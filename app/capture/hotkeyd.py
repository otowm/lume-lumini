"""Atalho global que distingue **toque** de **segurada**, lendo o evdev.

O atalho de gravação sempre veio do KDE: um ``.desktop`` com
``X-KDE-Shortcuts`` dispara ``lume-add-video-marker``, que manda ``USR1`` para o
laço de vídeo. Esse caminho só conhece *um* acontecimento — a tecla foi
pressionada. Não existe "soltou", e sem isso não há como saber que a tecla
continua abaixada; uma segurada e um toque chegam idênticos.

Daí este daemon. Ele lê ``/dev/input/event*`` direto, onde cada tecla tem
pressionar (1), repetir (2) e soltar (0), e traduz para as duas intenções que o
gravador entende:

``USR1`` (toque)
    O de sempre: salva o clipe no modo clipes, anota marcador no contínuo — e,
    durante uma gravação longa, anota marcador também.
``USR2`` (segurada)
    Inicia a gravação longa; segurando de novo, encerra.

Ler o teclado cru exige o grupo ``input``:

    sudo usermod -aG input "$USER"   # e reabrir a sessão

Sem isso o daemon sai avisando, e o atalho do KDE continua valendo como antes —
toque apenas. É de propósito: a gravação nunca depende deste processo existir.
"""

from __future__ import annotations

import argparse
import glob
import os
import select
import signal
import struct
import subprocess
import sys
import time
from pathlib import Path

from .base import read_shell_config
from ..backend.main_paths import CONFIG_DIR
from ..backend.runtime import runtime_dir

VIDEO_CONFIG = CONFIG_DIR / "video.conf"

#: ``struct input_event`` em 64 bits: dois ``timeval`` (Q,Q), tipo, código e
#: valor. O tamanho é fixo, então a leitura pode ser feita em blocos.
_EVENT_FORMAT = "llHHi"
_EVENT_SIZE = struct.calcsize(_EVENT_FORMAT)
_EV_KEY = 0x01

#: Tempo com a tecla abaixada que separa um toque de uma segurada. Curto
#: demais transformaria qualquer apertada nervosa em gravação longa; longo
#: demais faria a pessoa duvidar se o atalho pegou.
DEFAULT_HOLD_SECONDS = 0.6

#: Intervalo entre releituras de ``/dev/input/by-path``: teclado sem fio que
#: dorme e volta troca de ``eventN``.
RESCAN_SECONDS = 5.0

#: Nomes de tecla que o Lume aceita, traduzidos para o código do kernel
#: (``include/uapi/linux/input-event-codes.h``). A mesma grafia que o Windows
#: usa em :class:`app.capture.winhotkey.MarkerHotkey`.
KEY_CODES: dict[str, int] = {
    **{f"F{n}": code for n, code in zip(range(1, 11), range(59, 69))},
    "F11": 87, "F12": 88,
    **{letter: code for letter, code in zip("QWERTYUIOP", range(16, 26))},
    **{letter: code for letter, code in zip("ASDFGHJKL", range(30, 39))},
    **{letter: code for letter, code in zip("ZXCVBNM", range(44, 51))},
    **{digit: code for digit, code in zip("1234567890", range(2, 12))},
}


def log(message: str) -> None:
    print(f"lume-hotkeyd: {message}", file=sys.stderr, flush=True)


def daemon_flag() -> Path:
    """Arquivo que diz "estou de pé, o atalho do KDE pode ficar quieto".

    Sem ele, quem segurasse a tecla receberia os dois caminhos ao mesmo tempo —
    o KDE mandando um toque no instante do pressionar e o daemon mandando a
    segurada logo depois — e o gravador salvaria um clipe solto junto da
    gravação longa.
    """
    return runtime_dir() / "lume-hotkey-daemon"


def parse_key(spec: str) -> int | None:
    """Código evdev da tecla de um atalho como ``F8``.

    Modificadores são ignorados de propósito: o atalho de gravação é uma tecla
    só, e aceitar ``Ctrl+F8`` aqui daria a impressão falsa de que a combinação
    inteira está sendo observada.
    """
    key = ""
    for part in (spec or "").replace("-", "+").split("+"):
        token = part.strip().upper()
        if token and token not in {"ALT", "CTRL", "CONTROL", "SHIFT", "WIN", "META", "SUPER"}:
            key = token
    return KEY_CODES.get(key)


class HoldDetector:
    """Máquina de estados que separa toque de segurada.

    Pura de propósito — recebe o relógio de fora e devolve a intenção — porque é
    a parte que dá para testar sem teclado nenhum.

    O toque só sai ao **soltar**: enquanto a tecla está abaixada ainda pode
    virar segurada, e disparar na descida faria todo início de gravação longa
    salvar um clipe indesejado antes. A segurada, ao contrário, sai no instante
    em que o limite vence, ainda com a tecla abaixada — é ela que confirma para
    a pessoa que já pode soltar.
    """

    def __init__(self, hold_seconds: float = DEFAULT_HOLD_SECONDS) -> None:
        self.hold_seconds = hold_seconds
        self._pressed_at: float | None = None
        self._fired = False

    def feed(self, value: int, now: float) -> str | None:
        """Consome um evento de tecla (0 solta, 1 pressiona, 2 repete)."""
        if value == 1:
            self._pressed_at = now
            self._fired = False
            return None
        if value == 2:
            # Autorrepetição do kernel: a tecla continua abaixada, e é o
            # ``tick`` quem decide a hora da segurada.
            return self.tick(now)
        if value == 0:
            pressed_at, fired = self._pressed_at, self._fired
            self._pressed_at = None
            self._fired = False
            if pressed_at is None or fired:
                return None
            return "tap"
        return None

    def tick(self, now: float) -> str | None:
        """Deixa a segurada vencer mesmo sem evento novo chegando."""
        if self._pressed_at is None or self._fired:
            return None
        if now - self._pressed_at < self.hold_seconds:
            return None
        self._fired = True
        return "hold"


def keyboard_devices() -> list[str]:
    """Teclados vistos pelo kernel, sem duplicar o mesmo ``eventN``.

    ``by-path`` lista cada teclado duas vezes (``usb-`` e ``usbv2-``) e o alvo
    real é o mesmo arquivo; abrir os dois só gastaria descritores para receber
    cada tecla em dobro.
    """
    seen: dict[str, str] = {}
    for link in sorted(glob.glob("/dev/input/by-path/*-event-kbd")):
        try:
            target = os.path.realpath(link)
        except OSError:
            continue
        seen.setdefault(target, link)
    return sorted(seen)


class HotkeyDaemon:
    def __init__(self, hold_seconds: float | None = None, key_spec: str | None = None) -> None:
        values = read_shell_config(VIDEO_CONFIG)
        self.key_spec = key_spec or values.get("VIDEO_MARKER_HOTKEY", "F8")
        if hold_seconds is None:
            try:
                hold_seconds = float(values.get("VIDEO_HOTKEY_HOLD_SECONDS", DEFAULT_HOLD_SECONDS))
            except (TypeError, ValueError):
                hold_seconds = DEFAULT_HOLD_SECONDS
        self.hold_seconds = hold_seconds if hold_seconds > 0 else DEFAULT_HOLD_SECONDS
        self.detector = HoldDetector(self.hold_seconds)
        self.stopping = False
        self._handles: dict[int, tuple[str, object]] = {}
        self._pid: int | None = None
        self._pid_checked_at = 0.0

    def stop(self, _signum=None, _frame=None) -> None:
        self.stopping = True

    # --- destino dos sinais ----------------------------------------------
    def _video_pid(self) -> int | None:
        """PID do laço de vídeo, relido de tempos em tempos.

        O laço reinicia (``Restart=on-failure``) e o PID muda; guardar o
        primeiro para sempre faria o atalho morrer em silêncio depois de uma
        queda.
        """
        now = time.monotonic()
        if self._pid is not None and now - self._pid_checked_at < 5.0:
            return self._pid
        self._pid_checked_at = now
        try:
            result = subprocess.run(
                ["systemctl", "--user", "show", "captura-dia-video.service",
                 "--property=MainPID", "--value"],
                check=False, capture_output=True, text=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            self._pid = None
            return None
        value = result.stdout.strip()
        self._pid = int(value) if value.isdigit() and int(value) > 0 else None
        return self._pid

    def _deliver(self, action: str) -> None:
        pid = self._video_pid()
        if pid is None:
            log(f"{action} ignorado: o gravador de vídeo não está ativo")
            return
        try:
            os.kill(pid, signal.SIGUSR1 if action == "tap" else signal.SIGUSR2)
        except OSError as exc:
            self._pid = None
            log(f"não consegui entregar {action} ao gravador: {exc}")
            return
        log(f"{action} entregue ao gravador ({self.key_spec})")

    # --- teclado ----------------------------------------------------------
    def _open_devices(self) -> None:
        wanted = keyboard_devices()
        for fd, (path, handle) in list(self._handles.items()):
            if path not in wanted:
                handle.close()  # type: ignore[union-attr]
                del self._handles[fd]
        open_paths = {path for path, _handle in self._handles.values()}
        for path in wanted:
            if path in open_paths:
                continue
            try:
                handle = open(path, "rb", buffering=0)
            except OSError:
                # Um teclado a que não temos acesso não é motivo para desistir
                # dos outros: basta um deles entregar a tecla.
                continue
            os.set_blocking(handle.fileno(), False)
            self._handles[handle.fileno()] = (path, handle)

    def _read(self, fd: int, code: int) -> None:
        path, handle = self._handles[fd]
        try:
            data = handle.read(_EVENT_SIZE * 64)  # type: ignore[union-attr]
        except OSError:
            handle.close()  # type: ignore[union-attr]
            del self._handles[fd]
            return
        if not data:
            return
        for offset in range(0, len(data) - _EVENT_SIZE + 1, _EVENT_SIZE):
            _sec, _usec, kind, key, value = struct.unpack_from(_EVENT_FORMAT, data, offset)
            if kind != _EV_KEY or key != code:
                continue
            action = self.detector.feed(value, time.monotonic())
            if action:
                self._deliver(action)

    def run(self) -> int:
        signal.signal(signal.SIGTERM, self.stop)
        signal.signal(signal.SIGINT, self.stop)

        code = parse_key(self.key_spec)
        if code is None:
            log(f"atalho sem tecla reconhecida: {self.key_spec!r}")
            return 2

        self._open_devices()
        if not self._handles:
            log("nenhum teclado legível em /dev/input — o toque continua pelo "
                "atalho do KDE, mas segurar a tecla não será percebido. "
                "Para habilitar: sudo usermod -aG input \"$USER\" e reabrir a sessão.")
            return 1

        flag = daemon_flag()
        try:
            flag.write_text(f"{os.getpid()}\n", encoding="utf-8")
        except OSError:
            pass
        log(f"observando {self.key_spec} em {len(self._handles)} teclado(s); "
            f"segurada a partir de {self.hold_seconds:.2f}s")

        next_scan = time.monotonic() + RESCAN_SECONDS
        try:
            while not self.stopping:
                try:
                    ready, _w, _x = select.select(list(self._handles), [], [], 0.05)
                except (OSError, ValueError):
                    ready = []
                for fd in ready:
                    if fd in self._handles:
                        self._read(fd, code)
                action = self.detector.tick(time.monotonic())
                if action:
                    self._deliver(action)
                if time.monotonic() >= next_scan:
                    next_scan = time.monotonic() + RESCAN_SECONDS
                    self._open_devices()
        finally:
            for _path, handle in self._handles.values():
                handle.close()  # type: ignore[union-attr]
            try:
                if flag.read_text(encoding="utf-8").strip() == str(os.getpid()):
                    flag.unlink(missing_ok=True)
            except OSError:
                pass
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Atalho global de gravação com toque e segurada (Linux).")
    parser.add_argument("--hold-seconds", type=float, default=None,
                        help="tempo abaixado que caracteriza uma segurada")
    parser.add_argument("--key", default=None, help="tecla observada (padrão: a de video.conf)")
    args = parser.parse_args(argv)
    return HotkeyDaemon(hold_seconds=args.hold_seconds, key_spec=args.key).run()


if __name__ == "__main__":
    raise SystemExit(main())
