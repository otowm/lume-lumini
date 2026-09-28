"""Backend de captura para Windows.

Sem dependências Python extras: janela ativa e monitores via ``ctypes``
(Win32), telas e áudio via ``ffmpeg`` (``gdigrab`` e ``dshow``). O áudio junta
microfone + saída do sistema num único WAV, igual ao RecordBus do Linux.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from .base import AudioConfig, CaptureBackend, Monitor, ScreenConfig

# Nomes conhecidos de dispositivos dshow que capturam a saída do sistema
# (loopback). Mantidos apenas para diagnóstico: a gravação usa WASAPI, que não
# precisa de nenhum deles.
_LOOPBACK_HINTS = (
    "stereo mix",
    "mixagem estéreo",
    "what u hear",
    "what you hear",
    "wave out mix",
    "virtual-audio-capturer",
    "cable output",
    "voicemeeter out",
    "loopback",
)

_HIDDEN_PROCESS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def _parse_max_geometry(spec: str) -> tuple[int, int, bool] | None:
    """Interpreta ``"1920x1080>"`` -> (1920, 1080, apenas_reduzir)."""
    spec = spec.strip()
    if not spec:
        return None
    shrink_only = spec.endswith(">")
    core = spec.rstrip("<>").strip()
    match = re.fullmatch(r"(\d+)x(\d+)", core)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), shrink_only


def _scaled_size(w: int, h: int, cfg_max: str) -> tuple[int, int] | None:
    """Dimensões finais respeitando ``MAX_GEOMETRY`` (mantém proporção)."""
    parsed = _parse_max_geometry(cfg_max)
    if parsed is None:
        return None
    max_w, max_h, shrink_only = parsed
    if shrink_only and w <= max_w and h <= max_h:
        return None  # menor que o teto: não redimensiona
    ratio = min(max_w / w, max_h / h)
    return max(1, round(w * ratio)), max(1, round(h * ratio))


class WindowsCaptureBackend(CaptureBackend):
    name = "windows"

    def __init__(self, ffmpeg: str = "ffmpeg") -> None:
        self._ffmpeg = ffmpeg
        self._audio_devices: list[str] | None = None

    # --- Win32 via ctypes ------------------------------------------------
    def active_window(self) -> str | None:
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None

            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            title = buf.value or ""

            pid = wintypes.DWORD()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            proc_name = self._process_name(kernel32, pid.value)
            return f"{title} | {proc_name}"
        except Exception:
            return None

    @staticmethod
    def _process_name(kernel32, pid: int) -> str:
        import ctypes

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return ""
        try:
            size = ctypes.c_uint(260)
            buf = ctypes.create_unicode_buffer(size.value)
            if kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size)):
                return Path(buf.value).name
            return ""
        finally:
            kernel32.CloseHandle(handle)

    def list_monitors(self) -> list[Monitor]:
        import ctypes
        from ctypes import wintypes

        monitors: list[Monitor] = []

        class RECT(ctypes.Structure):
            _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                        ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
            ctypes.POINTER(RECT), ctypes.c_double)

        results: list[tuple[int, int, int, int]] = []

        def _cb(_hmon, _hdc, lprc, _data):
            r = lprc.contents
            results.append((r.left, r.top, r.right - r.left, r.bottom - r.top))
            return 1

        ctypes.windll.user32.EnumDisplayMonitors(0, 0, MonitorEnumProc(_cb), 0)
        # Ordem estável: da esquerda para a direita, de cima para baixo.
        results.sort(key=lambda t: (t[0], t[1]))
        for index, (x, y, w, h) in enumerate(results):
            monitors.append(Monitor(index=index, name=f"display{index}", x=x, y=y, width=w, height=h))
        return monitors

    def active_monitor(self) -> Monitor | None:
        try:
            import ctypes

            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd:
                return None

            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                            ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            rect = RECT()
            ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            cx = (rect.left + rect.right) // 2
            cy = (rect.top + rect.bottom) // 2
            for mon in self.list_monitors():
                if mon.x <= cx < mon.x + mon.width and mon.y <= cy < mon.y + mon.height:
                    return mon
        except Exception:
            return None
        return None

    def active_monitor_resolution(self) -> str | None:
        # O processo da API não é DPI-aware, então os retângulos de
        # EnumDisplayMonitors chegam divididos pela escala do Windows. O modo
        # de vídeo atual do monitor (EnumDisplaySettings) não passa por essa
        # virtualização: é a resolução que o OBS vai de fato capturar.
        try:
            import ctypes
            from ctypes import wintypes

            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return None
            user32.MonitorFromWindow.restype = wintypes.HMONITOR
            user32.MonitorFromWindow.argtypes = [wintypes.HWND, wintypes.DWORD]
            # Com argtypes declarados o handle viaja inteiro; sem eles o
            # ctypes o converteria para int de 32 bits.
            user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.c_void_p]
            user32.EnumDisplaySettingsW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
            monitor = user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
            info = _monitor_info_ex()()
            info.cbSize = ctypes.sizeof(info)
            if not monitor or not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
                return None
            mode = _devmode_w()()
            mode.dmSize = ctypes.sizeof(mode)
            if not user32.EnumDisplaySettingsW(info.szDevice, 0xFFFFFFFF, ctypes.byref(mode)):  # ENUM_CURRENT_SETTINGS
                return None
            width, height = int(mode.dmPelsWidth), int(mode.dmPelsHeight)
        except Exception:
            return super().active_monitor_resolution()
        if width <= 0 or height <= 0:
            return None
        return f"{width // 2 * 2}x{height // 2 * 2}"

    # --- Telas via gdigrab ----------------------------------------------
    def grab_frame(self, dest_dir: Path, stamp: str, cfg: ScreenConfig, window_text: str) -> list[Path]:
        dest_dir.mkdir(parents=True, exist_ok=True)
        targets: list[Monitor]
        if cfg.active_monitor_only:
            active = self.active_monitor()
            targets = [active] if active else self.list_monitors()[:1]
        elif cfg.split_monitors:
            targets = self.list_monitors()
        else:
            mons = self.list_monitors()
            targets = mons  # captura cada um; sem split real no Windows equivale ao conjunto

        saved: list[Path] = []
        for mon in targets:
            if mon is None:
                continue
            safe = re.sub(r"[^0-9A-Za-z_.-]", "_", mon.name)
            final = dest_dir / f"{stamp}_mon{mon.index}_{safe}.png"
            self._grab_region(mon, cfg.max_geometry, final)
            if final.exists():
                final.with_suffix(final.suffix + ".window").write_text(window_text, encoding="utf-8")
                saved.append(final)
        return saved

    def _grab_region(self, mon: Monitor, max_geometry: str, out: Path) -> None:
        argv = [
            self._ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
            "-f", "gdigrab",
            "-offset_x", str(mon.x), "-offset_y", str(mon.y),
            "-video_size", f"{mon.width}x{mon.height}",
            "-i", "desktop", "-frames:v", "1",
        ]
        scaled = _scaled_size(mon.width, mon.height, max_geometry)
        if scaled:
            argv += ["-vf", f"scale={scaled[0]}:{scaled[1]}:flags=lanczos"]
        argv.append(str(out))
        subprocess.run(
            argv, check=False, capture_output=True, timeout=30,
            creationflags=_HIDDEN_PROCESS,
        )

    # --- Áudio via dshow -------------------------------------------------
    def _list_audio_devices(self, refresh: bool = False) -> list[str]:
        """Nomes de dispositivos de áudio que o ``dshow`` enxerga.

        Dois formatos de saída do ffmpeg são aceitos: o antigo, com seções
        ``DirectShow audio devices``, e o atual (>= 7.x), que imprime uma lista
        única marcando cada linha com ``(audio)``/``(video)``.
        """
        if self._audio_devices is not None and not refresh:
            return self._audio_devices
        result = subprocess.run(
            [self._ffmpeg, "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"],
            check=False, capture_output=True, text=True, timeout=20,
            creationflags=_HIDDEN_PROCESS,
        )
        text = result.stderr or ""
        devices: list[str] = []
        section: str | None = None
        for line in text.splitlines():
            low = line.lower()
            if "audio devices" in low:
                section = "audio"
                continue
            if "video devices" in low:
                section = "video"
                continue
            if "alternative name" in low:
                continue
            match = re.search(r'"([^"]+)"', line)
            if not match:
                continue
            if low.rstrip().endswith("(audio)"):
                kind = "audio"
            elif low.rstrip().endswith("(video)"):
                kind = "video"
            else:
                kind = section
            if kind == "audio":
                devices.append(match.group(1))
        self._audio_devices = devices
        return devices

    def _dshow_loopback(self) -> str | None:
        """Dispositivo dshow capaz de gravar a saída, se algum existir.

        Só diagnóstico: a gravação usa WASAPI. Serve para mostrar se a máquina
        tem "Stereo Mix"/VB-Cable, que é o que a maioria dos tutoriais manda
        procurar.
        """
        for dev in self._list_audio_devices():
            low = dev.lower()
            if any(hint in low for hint in _LOOPBACK_HINTS):
                return dev
        return None

    def mic_level_argv(self, seconds: float) -> list[str] | None:
        # O microfone padrão pelo DirectShow, cru: é antes do volume da fonte
        # que o portão do OBS age, então é esse o sinal que se calibra. O
        # WASAPI dá o nome amigável; o dshow às vezes o corta, daí o prefixo.
        try:
            from . import wasapi
            name = wasapi.default_endpoint_name(wasapi.E_CAPTURE)
        except Exception:
            return None
        if not name:
            return None
        devices = self._list_audio_devices()
        device = next((d for d in devices if d == name), None) or next(
            (d for d in devices if name.startswith(d) or d.startswith(name)), None)
        if not device:
            return None
        return [
            self._ffmpeg, "-hide_banner", "-loglevel", "info", "-nostdin",
            "-f", "dshow", "-i", f"audio={device}",
            "-t", str(seconds), "-af", "volumedetect", "-f", "null", "-",
        ]

    def audio_record_argv(self, cfg: AudioConfig) -> list[str]:
        """argv do gravador WASAPI (ver :mod:`app.capture.winrecord`).

        Não é ffmpeg: no Windows o ffmpeg só enxerga DirectShow, e a saída do
        sistema costuma não estar lá. O gravador próprio mantém microfone,
        Discord e demais sons separados em um WAV temporário de três canais
        a 16 kHz; o pipeline o converte para mono depois da análise.
        """
        cfg.outdir.mkdir(parents=True, exist_ok=True)
        argv = [
            sys.executable, "-m", "app.capture.winrecord",
            "--outdir", str(cfg.outdir),
            "--segment", str(cfg.segment_seconds),
        ]
        if cfg.duration_seconds:
            argv += ["--duration", str(cfg.duration_seconds)]
        return argv

    def audio_diagnostics(self) -> dict[str, object]:
        from . import wasapi

        try:
            speakers = wasapi.default_endpoint_name(wasapi.E_RENDER)
            mic = wasapi.default_endpoint_name(wasapi.E_CAPTURE)
            outputs = wasapi.list_endpoints(wasapi.E_RENDER)
            inputs = wasapi.list_endpoints(wasapi.E_CAPTURE)
            error: str | None = None
        except OSError as exc:
            speakers = mic = None
            outputs = inputs = []
            error = str(exc)

        hint = None
        if error:
            hint = f"WASAPI indisponível ({error}); a captura de áudio não vai funcionar."
        elif speakers is None:
            hint = ("Nenhum dispositivo de saída padrão. Escolha um em "
                    "Configurações > Sistema > Som.")
        elif mic is None:
            hint = "Nenhum microfone padrão; só a saída do sistema será gravada."

        return {
            "backend": self.name,
            "method": "wasapi-loopback",
            "selected_system": speakers,
            "selected_mic": mic,
            "outputs": outputs,
            "inputs": inputs,
            # O loopback do WASAPI não depende de "Stereo Mix"; informamos só
            # para deixar claro que a ausência dele não é problema.
            "dshow_audio_devices": self._list_audio_devices(refresh=True),
            "dshow_loopback_device": self._dshow_loopback(),
            "system_capture_ok": speakers is not None and error is None,
            "hint": hint,
        }


# Tipos de largura fixa em vez de ``wintypes.DWORD``/``RECT``: no Windows são
# idênticos, e assim o layout também confere nos testes que rodam no Linux,
# onde ``c_ulong``/``c_long`` têm 8 bytes. Só o ``WCHAR`` fica do ``wintypes``,
# porque o ``szDevice`` precisa ser lido como texto.
def _monitor_info_ex():
    """MONITORINFOEXW: o ``szDevice`` é o nome que o EnumDisplaySettings pede."""
    import ctypes
    from ctypes import wintypes

    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_int32), ("top", ctypes.c_int32),
                    ("right", ctypes.c_int32), ("bottom", ctypes.c_int32)]

    class MONITORINFOEXW(ctypes.Structure):
        _fields_ = [("cbSize", ctypes.c_uint32), ("rcMonitor", RECT),
                    ("rcWork", RECT), ("dwFlags", ctypes.c_uint32),
                    ("szDevice", wintypes.WCHAR * 32)]
    return MONITORINFOEXW


def _devmode_w():
    """DEVMODEW com a união de impressora/monitor como 16 bytes opacos.

    Só ``dmPelsWidth``/``dmPelsHeight`` interessam, mas o ``dmSize`` precisa
    bater com o tamanho real (220 bytes) ou o Windows recusa a chamada.
    """
    import ctypes
    from ctypes import wintypes

    word, dword, short = ctypes.c_uint16, ctypes.c_uint32, ctypes.c_int16

    class DEVMODEW(ctypes.Structure):
        _fields_ = [("dmDeviceName", wintypes.WCHAR * 32), ("dmSpecVersion", word),
                    ("dmDriverVersion", word), ("dmSize", word),
                    ("dmDriverExtra", word), ("dmFields", dword),
                    ("dmUnion", ctypes.c_byte * 16), ("dmColor", short),
                    ("dmDuplex", short), ("dmYResolution", short),
                    ("dmTTOption", short), ("dmCollate", short),
                    ("dmFormName", wintypes.WCHAR * 32), ("dmLogPixels", word),
                    *((name, dword) for name in (
                        "dmBitsPerPel", "dmPelsWidth", "dmPelsHeight", "dmDisplayFlags",
                        "dmDisplayFrequency", "dmICMMethod", "dmICMIntent", "dmMediaType",
                        "dmDitherType", "dmReserved1", "dmReserved2", "dmPanningWidth",
                        "dmPanningHeight"))]
    return DEVMODEW
