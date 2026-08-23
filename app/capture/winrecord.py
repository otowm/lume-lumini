"""Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.

Grava temporariamente **microfone, Discord e demais sons em canais separados**
num único WAV (PCM s16le, três canais, 16 kHz). Depois da transcrição e da
diarização, o pipeline converte o arquivo para mono para economizar espaço.

Roda como processo próprio para que o supervisor precise apenas de um argv:

    python -m app.capture.winrecord --outdir ~/captura-dia/audio --segment 900

Cada fonte é um fluxo WASAPI independente (ver :mod:`app.capture.wasapi`), com
relógio próprio. A mixagem é guiada pelo relógio de parede: a cada volta o
gravador calcula quantas amostras já deveriam existir, completa com silêncio a
fonte que estiver atrasada e descarta o excesso da que estiver adiantada. Isso
mantém o arquivo com duração real mesmo quando o loopback fica mudo (sem nada
tocando, o WASAPI simplesmente não entrega pacote) ou quando o headset é
desligado no meio da gravação.
"""

from __future__ import annotations

import argparse
import ctypes
import signal
import sys
import time
import wave
from array import array
from datetime import datetime
from pathlib import Path

from .wasapi import (
    AUDCLNT_E_DEVICE_INVALIDATED,
    TARGET_RATE,
    E_CAPTURE,
    E_RENDER,
    WasapiCapture,
    WasapiError,
    ProcessLoopbackCapture,
    dbfs,
    default_endpoint_name,
)

#: Passo do laço de mixagem. Curto o bastante para não estourar o buffer do
#: endpoint (2 s), longo o bastante para o custo em CPU ser irrelevante.
_TICK_SECONDS = 0.01

# Mantém a escrita um pouco atrás do relógio real. Pacotes WASAPI chegam com
# jitter normal; sem esta margem, qualquer atraso virava silêncio digital e o
# áudio verdadeiro só entrava na volta seguinte, causando cortes perceptíveis.
_SYNC_DELAY_SECONDS = 0.25

#: Atraso tolerado por fonte antes de descartar o excesso e ressincronizar.
_MAX_LAG_SECONDS = 2.0

#: Espera antes de tentar reabrir uma fonte que caiu.
_REOPEN_BACKOFF_SECONDS = 3.0


def discord_process_id() -> int | None:
    """Retorna a raiz da árvore Discord.exe com mais processos descendentes."""
    if sys.platform != "win32":
        return None

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", ctypes.c_uint32), ("cntUsage", ctypes.c_uint32),
                    ("th32ProcessID", ctypes.c_uint32), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", ctypes.c_uint32), ("cntThreads", ctypes.c_uint32),
                    ("th32ParentProcessID", ctypes.c_uint32), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", ctypes.c_uint32), ("szExeFile", ctypes.c_wchar * 260)]

    kernel = ctypes.windll.kernel32
    kernel.CreateToolhelp32Snapshot.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
    kernel.CreateToolhelp32Snapshot.restype = ctypes.c_void_p
    kernel.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESSENTRY32W)]
    kernel.Process32FirstW.restype = ctypes.c_int
    kernel.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESSENTRY32W)]
    kernel.Process32NextW.restype = ctypes.c_int
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    kernel.CloseHandle.restype = ctypes.c_int
    snapshot = kernel.CreateToolhelp32Snapshot(0x2, 0)
    if snapshot in (0, -1, ctypes.c_void_p(-1).value):
        return None
    entries: dict[int, tuple[int, str]] = {}
    try:
        item = PROCESSENTRY32W()
        item.dwSize = ctypes.sizeof(item)
        ok = kernel.Process32FirstW(snapshot, ctypes.byref(item))
        while ok:
            entries[int(item.th32ProcessID)] = (int(item.th32ParentProcessID), item.szExeFile.casefold())
            ok = kernel.Process32NextW(snapshot, ctypes.byref(item))
    finally:
        kernel.CloseHandle(snapshot)
    discord = {pid for pid, (_parent, name) in entries.items() if name == "discord.exe"}
    if not discord:
        return None
    roots = [pid for pid in discord if entries[pid][0] not in discord] or list(discord)
    children: dict[int, list[int]] = {}
    for pid, (parent, _name) in entries.items():
        children.setdefault(parent, []).append(pid)

    def descendants(pid: int) -> int:
        pending, seen = [pid], set()
        while pending:
            current = pending.pop()
            if current in seen:
                continue
            seen.add(current)
            pending.extend(children.get(current, []))
        return len(seen)

    return max(roots, key=descendants)


def _install_stop_handlers(handler) -> None:
    """Atende todos os sinais de parada que o SO pode mandar.

    No Windows o supervisor pede a parada com ``CTRL_BREAK`` (o mais próximo de
    um SIGTERM por lá), e sem tratá-lo o processo morreria na hora — deixando o
    WAV em aberto, com o cabeçalho ainda dizendo zero bytes.
    """
    for name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        received = getattr(signal, name, None)
        if received is not None:
            try:
                signal.signal(received, handler)
            except (ValueError, OSError):
                pass


class _Source:
    """Uma fonte de áudio que se reabre sozinha quando o dispositivo cai."""

    def __init__(self, label: str, loopback: bool, enabled: bool = True,
                 process_mode: str | None = None) -> None:
        self.label = label
        self.loopback = loopback
        self.enabled = enabled
        self.process_mode = process_mode
        self.buffer = array("f")
        self.peak = 0.0
        self.samples_seen = 0
        self.failures = 0
        self._stream: WasapiCapture | None = None
        self._retry_at = 0.0
        self._process_id: int | None = None
        self._process_checked_at = 0.0

    @property
    def device_name(self) -> str | None:
        return self._stream.device_name if self._stream else None

    def ensure_open(self, now: float) -> None:
        if self.process_mode and now >= self._process_checked_at:
            self._process_checked_at = now + _REOPEN_BACKOFF_SECONDS
            process_id = discord_process_id()
            if process_id != self._process_id:
                self.close()
                self._process_id = process_id
                self._retry_at = 0.0
        if not self.enabled or self._stream is not None or now < self._retry_at:
            return
        if self.process_mode == "include" and self._process_id is None:
            return
        stream = (
            ProcessLoopbackCapture(self._process_id, include=self.process_mode == "include")
            if self.process_mode and self._process_id is not None
            else WasapiCapture(loopback=self.loopback)
        )
        try:
            stream.open()
        except (WasapiError, OSError) as exc:
            stream.close()
            self.failures += 1
            self._retry_at = now + _REOPEN_BACKOFF_SECONDS
            if self.failures == 1:
                print(f"[{self.label}] indisponível: {exc}", file=sys.stderr, flush=True)
            return
        self._stream = stream
        print(f"[{self.label}] {stream.device_name} "
              f"({stream.native_rate} Hz, {stream.native_channels} ch)",
              file=sys.stderr, flush=True)

    def drain(self, now: float) -> None:
        """Puxa o que houver do dispositivo para o buffer interno."""
        if self._stream is None:
            return
        try:
            chunk = self._stream.read()
        except WasapiError as exc:
            self._stream.close()
            self._stream = None
            self._retry_at = now + _REOPEN_BACKOFF_SECONDS
            reason = ("dispositivo trocado ou desligado"
                      if exc.hr == AUDCLNT_E_DEVICE_INVALIDATED else str(exc))
            print(f"[{self.label}] {reason}; reabrindo em "
                  f"{_REOPEN_BACKOFF_SECONDS:.0f}s", file=sys.stderr, flush=True)
            return
        if chunk:
            self.buffer.extend(chunk)
            self.samples_seen += len(chunk)

    def take(self, count: int) -> array:
        """Retira ``count`` amostras, completando com silêncio se faltar."""
        limit = count + int(_MAX_LAG_SECONDS * TARGET_RATE)
        if len(self.buffer) > limit:
            del self.buffer[:len(self.buffer) - limit]

        available = min(count, len(self.buffer))
        out = self.buffer[:available]
        del self.buffer[:available]
        for value in out:
            magnitude = abs(value)
            if magnitude > self.peak:
                self.peak = magnitude
        if available < count:
            out.extend([0.0] * (count - available))
        return out

    def close(self) -> None:
        if self._stream:
            self._stream.close()
            self._stream = None


class _SegmentWriter:
    """Escreve WAVs sequenciais com o mesmo nome que o Linux produz."""

    def __init__(self, outdir: Path, segment_seconds: int, prefix: str = "audio", channels: int = 2) -> None:
        self.outdir = outdir
        self.segment_samples = max(1, segment_seconds) * TARGET_RATE
        self.prefix = prefix
        self.channels = channels
        self._wav: wave.Wave_write | None = None
        self._path: Path | None = None
        self._written = 0

    def _open(self) -> None:
        self.outdir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self._path = self.outdir / f"{self.prefix}-{stamp}.wav"
        self._wav = wave.open(str(self._path), "wb")
        self._wav.setnchannels(self.channels)
        self._wav.setsampwidth(2)
        self._wav.setframerate(TARGET_RATE)
        self._written = 0
        print(f"[wav] {self._path}", file=sys.stderr, flush=True)

    def write(self, pcm: bytes, frames: int) -> None:
        if self._wav is None:
            self._open()
        assert self._wav is not None
        self._wav.writeframes(pcm)
        self._written += frames
        if self._written >= self.segment_samples:
            self.close()

    def close(self) -> None:
        if self._wav is not None:
            self._wav.close()
            self._wav = None
            self._path = None
            self._written = 0


def _mix(chunks: list[array]) -> bytes:
    """Soma as fontes com saturação e converte para PCM s16le."""
    if not chunks:
        return b""
    length = len(chunks[0])
    out = array("h", bytes(2 * length))
    for index in range(length):
        total = 0.0
        for chunk in chunks:
            total += chunk[index]
        if total > 1.0:
            total = 1.0
        elif total < -1.0:
            total = -1.0
        out[index] = int(total * 32767)
    if sys.byteorder == "big":  # pragma: no cover - Windows é little-endian
        out.byteswap()
    return out.tobytes()


def _stereo(microphone: array, system: array) -> bytes:
    """Intercala mic (esquerda) e sistema (direita) em PCM s16le."""
    length = min(len(microphone), len(system))
    out = array("h", bytes(4 * length))
    for index in range(length):
        out[index * 2] = int(max(-1.0, min(1.0, microphone[index])) * 32767)
        out[index * 2 + 1] = int(max(-1.0, min(1.0, system[index])) * 32767)
    if sys.byteorder == "big":  # pragma: no cover - Windows é little-endian
        out.byteswap()
    return out.tobytes()


def _multichannel(chunks: list[array]) -> bytes:
    """Intercala N fontes mono em canais PCM s16le independentes."""
    if not chunks:
        return b""
    length = min(len(chunk) for chunk in chunks)
    out = array("h", bytes(2 * length * len(chunks)))
    for frame in range(length):
        for channel, chunk in enumerate(chunks):
            out[frame * len(chunks) + channel] = int(max(-1.0, min(1.0, chunk[frame])) * 32767)
    if sys.byteorder == "big":  # pragma: no cover
        out.byteswap()
    return out.tobytes()


def record(outdir: Path, segment_seconds: int, duration: float | None,
           want_mic: bool, want_system: bool, prefix: str = "audio") -> int:
    sources = [
        _Source("mic", loopback=False, enabled=want_mic),
        _Source("discord", loopback=True, enabled=want_system, process_mode="include"),
        _Source("outros", loopback=True, enabled=want_system, process_mode="exclude"),
    ]
    separate_channels = want_mic and want_system
    writer = _SegmentWriter(outdir, segment_seconds, prefix, channels=3 if separate_channels else 1)

    stopping = False

    def _stop(_signum, _frame):
        nonlocal stopping
        stopping = True

    _install_stop_handlers(_stop)

    start = time.monotonic()
    written = 0
    try:
        while not stopping:
            now = time.monotonic()
            if duration is not None and now - start >= duration:
                break
            for source in sources:
                source.ensure_open(now)
                source.drain(now)

            # A margem absorve o jitter dos três endpoints sem alterar a
            # posição das amostras dentro do arquivo.
            target = max(0, int((time.monotonic() - start - _SYNC_DELAY_SECONDS) * TARGET_RATE))
            count = target - written
            microphone = sources[0]
            if microphone.enabled and microphone._stream is not None:
                # O microfone entrega pacotes continuamente e funciona como
                # relógio mestre. Nunca inventar amostras além do que ele já
                # entregou; se o timer acordar antes do pacote, aguardamos a
                # próxima volta em vez de gravar um buraco.
                count = min(count, len(microphone.buffer))
            if count <= 0:
                time.sleep(_TICK_SECONDS)
                continue

            chunks = {source.label: source.take(count) for source in sources if source.enabled}
            pcm = _multichannel([chunks["mic"], chunks["discord"], chunks["outros"]]) if separate_channels else _mix(list(chunks.values()))
            writer.write(pcm, count)
            written += count
            time.sleep(_TICK_SECONDS)
    finally:
        # Preserva os últimos 250 ms que ainda estavam aguardando no buffer.
        now = time.monotonic()
        for source in sources:
            source.drain(now)
        target = max(written, int((now - start) * TARGET_RATE))
        count = target - written
        microphone = sources[0]
        if microphone.enabled and microphone._stream is not None:
            count = min(count, len(microphone.buffer))
        if count > 0:
            chunks = {source.label: source.take(count) for source in sources if source.enabled}
            pcm = _multichannel([chunks["mic"], chunks["discord"], chunks["outros"]]) if separate_channels else _mix(list(chunks.values()))
            writer.write(pcm, count)
        writer.close()
        for source in sources:
            source.close()

    for source in sources:
        if source.enabled:
            print(f"[{source.label}] pico {dbfs(source.peak):.1f} dBFS "
                  f"({source.samples_seen} amostras)", file=sys.stderr, flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Grava microfone, Discord e outros sons em canais separados num WAV temporário 16 kHz.")
    parser.add_argument("--outdir", type=Path,
                        help="pasta dos WAVs (obrigatório, exceto com --list)")
    parser.add_argument("--segment", type=int, default=900,
                        help="duração de cada WAV em segundos (padrão: 900)")
    parser.add_argument("--duration", type=float, default=None,
                        help="para depois de N segundos (padrão: roda até receber sinal)")
    parser.add_argument("--prefix", default="audio")
    parser.add_argument("--no-mic", action="store_true")
    parser.add_argument("--no-system", action="store_true")
    parser.add_argument("--list", action="store_true",
                        help="lista os endpoints de áudio e sai")
    args = parser.parse_args(argv)

    if args.list:
        from .wasapi import list_endpoints

        print("Saída (loopback disponível em qualquer uma):")
        for name in list_endpoints(E_RENDER):
            print(f"  - {name}")
        print(f"  padrão: {default_endpoint_name(E_RENDER)}")
        print("Entrada:")
        for name in list_endpoints(E_CAPTURE):
            print(f"  - {name}")
        print(f"  padrão: {default_endpoint_name(E_CAPTURE)}")
        return 0

    if args.outdir is None:
        parser.error("--outdir é obrigatório para gravar")

    return record(args.outdir, args.segment, args.duration,
                  want_mic=not args.no_mic, want_system=not args.no_system,
                  prefix=args.prefix)


if __name__ == "__main__":
    raise SystemExit(main())
