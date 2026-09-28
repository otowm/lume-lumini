"""Backend de captura para Linux (PipeWire + KDE/Wayland).

Delega para os scripts já instalados em ``~/bin`` e para o ``ffmpeg -f pulse``,
preservando exatamente o comportamento atual. A intenção aqui não é reescrever a
captura do Linux, e sim expô-la pela mesma interface que o Windows implementa.
"""

from __future__ import annotations

import os
import json
import re
import shutil
import subprocess
from pathlib import Path

_ANSI = re.compile(r"\033\[[0-9;]*m")

from .base import AudioConfig, CaptureBackend, Monitor, ScreenConfig, read_shell_config
from ..backend.main_paths import AUDIO_CONFIG
from ..backend.runtime import video_activity_flag

HOME = Path.home()
SCREEN_BIN = Path(os.environ.get("CAPTURA_DIA_SCREEN_BIN", HOME / "bin/captura-tela.sh"))
AUDIO_BUS = Path(os.environ.get("CAPTURA_DIA_AUDIO_BUS", HOME / "bin/audio-bus.sh"))
#: Monitores dos três buses de captura, um por faixa (mic / Discord / sistema).
MIC_SOURCE = os.environ.get("MIC_SOURCE", "MicBus.monitor")
DISCORD_SOURCE = os.environ.get("DISCORD_SOURCE", "DiscordBus.monitor")
AUDIO_SOURCE = os.environ.get("AUDIO_SOURCE", "RecordBus.monitor")


def _mic_filter() -> str:
    """Filtro ffmpeg do canal do microfone: supressão de ruído + portão de
    volume mínimo, lidos de ``audio.conf`` (mesmo contrato do grava-audio.sh).

    O ``agate`` trabalha em amplitude linear (0-1), não dBFS; convertemos aqui
    para que o arquivo de configuração e a interface só falem em dB.
    """
    config = read_shell_config(AUDIO_CONFIG)
    denoise = config.get("MIC_DENOISE_ENABLED", "true").strip().lower() == "true"
    try:
        threshold_db = float(config.get("MIC_GATE_THRESHOLD_DB", "-45"))
    except ValueError:
        threshold_db = -45.0
    gate_linear = 10 ** (threshold_db / 20)
    filt = "pan=mono|c0=c0"
    if denoise:
        filt += ",afftdn"
    filt += f",agate=threshold={gate_linear:.6f}:attack=5:release=250"
    return filt


def _kdotool_env() -> dict[str, str]:
    """Ambiente do kdotool com ``KDE_SESSION_VERSION`` garantido.

    O kdotool 0.3 recusa rodar sem ``KDE_SESSION_VERSION=6`` ("Unsupported KDE
    version"). O terminal herda a variável do Plasma, mas as units do systemd
    podem subir antes de ela ser importada — e aí nenhuma janela era lida.
    """
    return {**os.environ, "KDE_SESSION_VERSION": os.environ.get("KDE_SESSION_VERSION") or "6"}


class LinuxCaptureBackend(CaptureBackend):
    name = "linux"

    # --- Janela ativa (kdotool) -----------------------------------------
    def active_window(self) -> str | None:
        wid = self._kdotool("getactivewindow")
        if wid is None:
            return None
        title = self._kdotool("getwindowname", wid) or ""
        klass = self._kdotool("getwindowclassname", wid) or ""
        return f"{title} | {klass}"

    def active_window_problem(self) -> str:
        # O kdotool só conversa com o KWin: em GNOME, Hyprland ou qualquer outro
        # compositor ele falha sem dizer por quê.
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "")
        if desktop and "kde" not in desktop.lower():
            return (f"A janela ativa só é lida no KDE Plasma, e esta sessão é {desktop}. "
                    "O Lumini no Linux depende do kdotool, que só funciona com o KWin.")
        if shutil.which("kdotool") is None:
            return "O kdotool não está instalado. Instale com: paru -S kdotool"
        try:
            result = subprocess.run(["kdotool", "getactivewindow"], check=False,
                                    capture_output=True, text=True, timeout=5,
                                    env=_kdotool_env())
        except subprocess.TimeoutExpired:
            return "O kdotool não respondeu em 5 segundos. O KWin está rodando?"
        detail = (result.stderr.strip().splitlines() or [""])[-1][:300]
        if result.returncode != 0 or not result.stdout.strip():
            return f"O kdotool falhou ao consultar o KWin: {detail or 'sem resposta'}"
        return ""

    @staticmethod
    def _kdotool(*args: str) -> str | None:
        try:
            result = subprocess.run(["kdotool", *args], check=False,
                                    capture_output=True, text=True, timeout=5,
                                    env=_kdotool_env())
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0:
            return None
        return result.stdout.strip()

    def list_monitors(self) -> list[Monitor]:
        monitors: list[Monitor] = []
        try:
            result = subprocess.run(["kscreen-doctor", "-o"], check=False,
                                    capture_output=True, text=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return monitors
        current_name: str | None = None
        current_enabled = False
        for raw in result.stdout.splitlines():
            line = _ANSI.sub("", raw).strip()
            if line.startswith("Output:"):
                parts = line.split()
                current_name = parts[2] if len(parts) > 2 else f"output{len(monitors)}"
                current_enabled = False
            elif line == "enabled" and current_name is not None:
                current_enabled = True
            elif line.startswith("Geometry:") and current_name is not None and current_enabled:
                match = re.search(r"Geometry:\s*(-?\d+),(-?\d+)\s+(\d+)x(\d+)", line)
                if match:
                    x, y, width, height = map(int, match.groups())
                    monitors.append(Monitor(index=len(monitors), name=current_name,
                                            x=x, y=y, width=width, height=height))
            elif line.startswith("Scale:") and monitors and monitors[-1].name == current_name:
                # Vem depois do Geometry, que no KWin é lógico: com escala de
                # 125% um monitor 1600x900 aparece como 1280x720.
                try:
                    monitors[-1].scale = float(line.split()[1])
                except (IndexError, ValueError):
                    pass
        return monitors

    def active_monitor(self) -> Monitor | None:
        monitors = self.list_monitors()
        try:
            payload = json.loads(video_activity_flag().read_text(encoding="utf-8"))
            recorded = str(payload.get("monitor") or "") if isinstance(payload, dict) else ""
        except (OSError, json.JSONDecodeError):
            recorded = ""
        if recorded:
            return next((monitor for monitor in monitors if monitor.name == recorded), None)

        wid = self._kdotool("getactivewindow")
        geometry = self._kdotool("getwindowgeometry", wid) if wid else None
        if not geometry:
            return None
        position = re.search(r"Position:\s*(-?\d+),(-?\d+)", geometry)
        size = re.search(r"Geometry:\s*(\d+)x(\d+)", geometry)
        if not position or not size:
            return None
        x, y = map(int, position.groups())
        width, height = map(int, size.groups())
        cx, cy = x + width // 2, y + height // 2
        return next((monitor for monitor in monitors
                     if monitor.x <= cx < monitor.x + monitor.width
                     and monitor.y <= cy < monitor.y + monitor.height), None)

    # --- Telas (delega ao script instalado, sem mudar comportamento) -----
    def grab_frame(self, dest_dir: Path, stamp: str, cfg: ScreenConfig, window_text: str) -> list[Path]:
        env = dict(os.environ)
        env["OTOWM_RECALL_IMAGE_ROOT"] = str(dest_dir)
        try:
            result = subprocess.run([str(SCREEN_BIN)], check=False,
                                    capture_output=True, text=True, timeout=60, env=env)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return []
        paths: list[Path] = []
        for line in result.stdout.splitlines():
            candidate = Path(line.strip())
            if candidate.is_file():
                paths.append(candidate)
        return paths

    # --- Áudio (PipeWire: RecordBus somando mic + saídas) ----------------
    def audio_setup(self) -> None:
        if AUDIO_BUS.exists():
            subprocess.run([str(AUDIO_BUS), "setup"], check=False, timeout=60)

    def audio_teardown(self) -> None:
        if AUDIO_BUS.exists():
            subprocess.run([str(AUDIO_BUS), "teardown"], check=False, timeout=30)

    def audio_record_argv(self, cfg: AudioConfig) -> list[str]:
        """argv do ffmpeg que grava mic + Discord + sistema num WAV de 3 canais.

        Mesmo contrato do Windows: ``c0`` = microfone, ``c1`` = Discord, ``c2``
        = demais sons. O pipeline transcreve cada canal e compacta para mono no
        fim. Os três monitores vêm dos buses do ``audio-bus.sh``. Se ``cfg``
        pedir explicitamente 1 canal (amostra mono do self-test), grava só o mix
        do sistema, preservando o modo antigo.
        """
        cfg.outdir.mkdir(parents=True, exist_ok=True)
        system = cfg.system_device or AUDIO_SOURCE
        limit = ["-t", str(cfg.duration_seconds)] if cfg.duration_seconds else []
        target = str(cfg.outdir / "audio-%Y%m%d-%H%M%S.wav")
        segment = [
            "-flush_packets", "1",
            "-f", "segment", "-segment_time", str(cfg.segment_seconds),
            "-reset_timestamps", "1", "-strftime", "1", target,
        ]
        if cfg.channels <= 1:
            return [
                "ffmpeg", "-hide_banner", "-loglevel", "warning", "-nostdin",
                "-f", "pulse", "-thread_queue_size", "1024", "-i", system, *limit,
                "-ac", "1", "-ar", str(cfg.sample_rate), "-c:a", "pcm_s16le", *segment,
            ]
        mic = cfg.mic_device or MIC_SOURCE
        discord = DISCORD_SOURCE
        # O ``map=`` é obrigatório: as três entradas são mono e todas chamam seu
        # único canal de FC. Sem ele o ffmpeg desempata sozinho e devolve os
        # canais rotacionados — mic em c2, Discord em c0, sistema em c1.
        filters = (
            f"[0:a]{_mic_filter()}[mic];[1:a]pan=mono|c0=c0[dis];"
            "[2:a]pan=mono|c0=0.5*c0+0.5*c1[sys];"
            "[mic][dis][sys]join=inputs=3:channel_layout=3.0"
            ":map=0.0-FL|1.0-FR|2.0-FC[out]"
        )
        return [
            "ffmpeg", "-hide_banner", "-loglevel", "warning", "-nostdin",
            "-f", "pulse", "-thread_queue_size", "1024", "-i", mic,
            "-f", "pulse", "-thread_queue_size", "1024", "-i", discord,
            "-f", "pulse", "-thread_queue_size", "1024", "-i", system, *limit,
            "-filter_complex", filters, "-map", "[out]",
            "-ar", str(cfg.sample_rate), "-c:a", "pcm_s16le", *segment,
        ]

    def mic_level_argv(self, seconds: float) -> list[str]:
        # ``-loglevel info`` é obrigatório: o volumedetect escreve o
        # ``max_volume`` em nível info, e com ``warning`` a leitura sairia
        # sempre vazia — o medidor mostraria silêncio mesmo com você falando.
        return [
            "ffmpeg", "-hide_banner", "-loglevel", "info", "-nostdin",
            "-f", "pulse", "-thread_queue_size", "1024", "-i", MIC_SOURCE,
            "-t", str(seconds), "-af", "volumedetect", "-f", "null", "-",
        ]

    def audio_diagnostics(self) -> dict[str, object]:
        sources: list[str] = []
        try:
            result = subprocess.run(["pactl", "list", "short", "sources"], check=False,
                                    capture_output=True, text=True, timeout=10)
            sources = [ln.split("\t")[1] for ln in result.stdout.splitlines() if "\t" in ln]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        buses = {"microphone": MIC_SOURCE, "discord": DISCORD_SOURCE, "system": AUDIO_SOURCE}
        present = {name: monitor in sources for name, monitor in buses.items()}
        has_bus = present["system"]
        missing = [monitor for monitor in buses.values() if monitor not in sources]
        return {
            "backend": self.name,
            "sources": sources,
            "record_bus": AUDIO_SOURCE,
            "track_buses": buses,
            "track_buses_present": present,
            "separated_sources": all(present.values()),
            "system_capture_ok": has_bus,
            "hint": None if not missing else
                    f"buses ausentes ({', '.join(missing)}); rode 'audio-bus.sh setup'.",
        }
