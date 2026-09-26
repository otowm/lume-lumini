"""Atalhos globais no Windows, registrados fora de qualquer janela.

No Linux o atalho é do KDE e chega ao processo como ``USR1``. O Windows não tem
``USR1``, e um atalho que só funcione com a janela em foco não serviria para
nada quando o objetivo é justamente agir com o **jogo** em foco. A saída é
``RegisterHotKey`` com janela nula, que entrega ``WM_HOTKEY`` na fila de
mensagens da thread — daí o laço próprio numa thread dedicada.

Vive num módulo separado porque tanto a gravação (marcador) quanto a HUD
(mostrar/esconder) precisam do mesmo mecanismo, em processos diferentes, e não
faria sentido a HUD arrastar o laço de vídeo inteiro só por causa disto.
"""

from __future__ import annotations

import ctypes
import re
import sys
import threading
import time


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


#: Tempo com a tecla abaixada que separa um toque de uma segurada. O mesmo
#: valor do daemon do Linux (:mod:`app.capture.hotkeyd`), para que o atalho
#: tenha o mesmo tato nos dois sistemas.
DEFAULT_HOLD_SECONDS = 0.6

#: Cadência com que se pergunta ao Windows se a tecla continua abaixada.
_POLL_SECONDS = 0.025


class MSG(ctypes.Structure):
    _fields_ = [("hwnd", ctypes.c_void_p), ("message", ctypes.c_uint),
                ("wParam", ctypes.c_void_p), ("lParam", ctypes.c_void_p),
                ("time", ctypes.c_uint),
                ("pt_x", ctypes.c_long), ("pt_y", ctypes.c_long)]


class MarkerHotkey:
    """Atalho global que distingue toque de segurada.

    ``RegisterHotKey`` avisa quando a tecla desce e nada mais — nem soltar, nem
    "continua abaixada". Quem responde isso é ``GetAsyncKeyState``, perguntado
    em intervalos curtos logo depois do aviso. O toque só sai ao soltar, porque
    até lá ele ainda pode virar segurada; a segurada sai assim que o limite
    vence, ainda com a tecla abaixada, que é o que confirma à pessoa que já
    pode soltar.
    """

    _MODIFIERS = {"ALT": 0x1, "CTRL": 0x2, "CONTROL": 0x2, "SHIFT": 0x4, "WIN": 0x8}
    _WM_HOTKEY = 0x0312

    #: Cada thread registra num espaço próprio, mas dois atalhos na mesma
    #: thread precisam de identificadores distintos.
    _next_id = 1

    def __init__(self, spec: str, on_press, on_hold=None,
                 hold_seconds: float = DEFAULT_HOLD_SECONDS) -> None:
        self.spec = spec
        self.on_press = on_press
        self.on_hold = on_hold
        self.hold_seconds = hold_seconds if hold_seconds > 0 else DEFAULT_HOLD_SECONDS
        self._thread = None

    @classmethod
    def _parse(cls, spec: str) -> tuple[int, int] | None:
        modifiers = 0
        key = None
        for part in spec.replace("-", "+").split("+"):
            token = part.strip().upper()
            if not token:
                continue
            if token in cls._MODIFIERS:
                modifiers |= cls._MODIFIERS[token]
            else:
                key = token
        if not key:
            return None
        if re.fullmatch(r"F([1-9]|1[0-9]|2[0-4])", key):
            return modifiers, 0x70 + int(key[1:]) - 1
        if len(key) == 1 and (key.isalpha() or key.isdigit()):
            return modifiers, ord(key)
        if key in {"[", "]"}:
            # VkKeyScan usa o layout ativo (inclusive ABNT2), não a posição US.
            scan = ctypes.windll.user32.VkKeyScanW(ord(key))
            if scan & 0xffff == 0xffff:
                return None
            layout_modifiers = (scan >> 8) & 0xff
            modifiers |= ((0x4 if layout_modifiers & 1 else 0)
                          | (0x2 if layout_modifiers & 2 else 0)
                          | (0x1 if layout_modifiers & 4 else 0))
            return modifiers, scan & 0xff
        return None

    def start(self) -> None:
        parsed = self._parse(self.spec)
        if parsed is None:
            log(f"[aviso] atalho de marcador inválido: {self.spec!r}")
            return
        self._thread = threading.Thread(target=self._loop, args=parsed,
                                        name="lume-marker-hotkey", daemon=True)
        self._thread.start()

    def _loop(self, modifiers: int, vk: int) -> None:
        user32 = ctypes.windll.user32
        hotkey_id = MarkerHotkey._next_id
        MarkerHotkey._next_id += 1
        if not user32.RegisterHotKey(None, hotkey_id, modifiers, vk):
            log(f"[aviso] não foi possível registrar {self.spec!r} "
                f"(outro programa já usa esse atalho)")
            return
        log(f"[marcador] atalho {self.spec} registrado")

        message = MSG()
        try:
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == self._WM_HOTKEY:
                    action = self._resolve(user32, vk)
                    callback = self.on_hold if action == "hold" else self.on_press
                    if callback is None:
                        continue
                    try:
                        callback()
                    except Exception as exc:  # nunca derrubar a thread do atalho
                        log(f"[marcador] falhou: {exc}")
                    if action == "hold":
                        # A ação já saiu; o que a tecla ainda abaixada produzir
                        # até soltar é repetição, e repetição não é atalho novo.
                        self._drain(user32, vk)
        finally:
            user32.UnregisterHotKey(None, hotkey_id)

    def _resolve(self, user32, vk: int) -> str:
        """Espera o desfecho da tecla e diz se foi toque ou segurada.

        Bloquear a fila de mensagens aqui é de propósito: enquanto a tecla está
        abaixada o Windows repete o ``WM_HOTKEY``, e cada repetição contaria
        como um atalho novo. Presas na fila, elas são descartadas junto com a
        pressionada que já foi resolvida.
        """
        if self.on_hold is None:
            return "tap"
        deadline = time.monotonic() + self.hold_seconds
        while time.monotonic() < deadline:
            if not user32.GetAsyncKeyState(vk) & 0x8000:
                return "tap"
            time.sleep(_POLL_SECONDS)
        return "hold"

    def _drain(self, user32, vk: int) -> None:
        """Descarta as repetições enfileiradas enquanto a tecla esteve abaixada."""
        while user32.GetAsyncKeyState(vk) & 0x8000:
            time.sleep(_POLL_SECONDS)
        pending = MSG()
        while user32.PeekMessageW(ctypes.byref(pending), None,
                                  self._WM_HOTKEY, self._WM_HOTKEY, 0x0001):
            pass
