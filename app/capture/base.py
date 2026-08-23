"""Interface comum de captura, independente de sistema operacional.

Cada SO fornece um :class:`CaptureBackend` concreto. O resto do app conversa só
com esta interface e nunca chama ``pactl``, ``spectacle``, ``dshow`` etc.
diretamente. Assim, ao trocar de Linux para Windows, apenas a implementação
selecionada muda; a API, a UI e o pipeline continuam idênticos.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Monitor:
    """Um monitor físico: rótulo estável + geometria em pixels do desktop."""

    index: int
    name: str
    x: int
    y: int
    width: int
    height: int

    @property
    def geometry(self) -> str:
        return f"{self.width}x{self.height}+{self.x}+{self.y}"


@dataclass
class ScreenConfig:
    """Valores de ``tela.conf`` relevantes para a captura de um frame."""

    capture_root: Path
    max_geometry: str = "1920x1080>"
    split_monitors: bool = True
    active_monitor_only: bool = True
    privacy_fail_closed: bool = True


@dataclass
class AudioConfig:
    """Como gravar áudio: fontes e formato do WAV alvo do whisper."""

    outdir: Path
    segment_seconds: int = 900
    sample_rate: int = 16000
    channels: int = 1
    # Nomes de dispositivo específicos por SO; None = deixar o backend decidir.
    mic_device: str | None = None
    system_device: str | None = None
    latency_msec: int = 200
    # Para amostras curtas (self-test). ``None`` = grava até receber sinal, que
    # é o modo do serviço contínuo.
    duration_seconds: float | None = None
    extra_env: dict[str, str] = field(default_factory=dict)


def read_shell_config(path: Path) -> dict[str, str]:
    """Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.

    ``utf-8-sig`` porque no Windows editores e o PowerShell gravam UTF-8 com
    BOM, e o BOM grudaria na primeira chave.
    """
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key.strip()] = value.replace("$HOME", str(Path.home()))
    return values


def read_patterns(path: Path) -> list[str]:
    """Lista de expressões de um arquivo de padrões, ignorando comentários."""
    if not path.is_file():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8-sig").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def parse_video_app_rule(raw: str, default_mode: str = "continuous",
                         default_fps: int = 60,
                         default_geometry: str = "1920x1080") -> tuple[str, str, int, str, str]:
    """Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``."""
    source = raw.strip()
    match = re.match(r"^\[([^]]+)\]\s+(.+)$", source, re.IGNORECASE)
    metadata = match.group(1).split() if match else []
    if match:
        source = match.group(2).strip()
    mode = default_mode if default_mode in {"continuous", "clips"} else "continuous"
    fps = max(1, min(60, int(default_fps)))
    geometry = default_geometry if re.fullmatch(r"\d{2,4}x\d{2,4}", default_geometry) else "1920x1080"
    capture_source = "window" if "robloxplayerbeta" in source.casefold() else "game"
    if metadata:
        for token in metadata:
            lowered = token.lower()
            if lowered in {"continuous", "clips"}:
                mode = lowered
            elif lowered.startswith("fps="):
                try:
                    fps = max(1, min(60, int(lowered.split("=", 1)[1])))
                except ValueError:
                    pass
            elif lowered.startswith(("geometry=", "resolution=")):
                value = token.split("=", 1)[1]
                if re.fullmatch(r"\d{2,4}x\d{2,4}", value):
                    geometry = value
            elif lowered.startswith("source="):
                value = lowered.split("=", 1)[1]
                if value in {"game", "window"}:
                    capture_source = value
    return source, mode, fps, geometry, capture_source


def format_video_app_rule(pattern: str, mode: str, fps: int = 60,
                          geometry: str = "1920x1080",
                          capture_source: str = "game") -> str:
    selected = mode if mode in {"continuous", "clips"} else "continuous"
    selected_fps = max(1, min(60, int(fps)))
    selected_geometry = geometry if re.fullmatch(r"\d{2,4}x\d{2,4}", geometry) else "1920x1080"
    selected_source = capture_source if capture_source in {"game", "window"} else "game"
    return f"[{selected} fps={selected_fps} geometry={selected_geometry} source={selected_source}] {pattern.strip()}"


def matched_sensitive_pattern(window_text: str, patterns_file: Path) -> str | None:
    """Primeiro padrão sensível (regex, case-insensitive) que casa com a janela.

    Mesma regra nos dois SOs — a proteção de privacidade precisa ser idêntica.
    Retorna o padrão que casou, ou ``None`` se a janela é permitida.
    """
    if not patterns_file.is_file():
        return None
    for raw in patterns_file.read_text(encoding="utf-8-sig").splitlines():
        pattern = raw.strip()
        if not pattern or pattern.startswith("#"):
            continue
        try:
            if re.search(pattern, window_text, re.IGNORECASE):
                return pattern
        except re.error:
            continue
    return None


class CaptureBackend(ABC):
    """Contrato que Linux e Windows implementam."""

    #: Identificador curto ("linux", "windows") para logs e diagnóstico.
    name: str = "base"

    # --- Janela ativa / privacidade -------------------------------------
    @abstractmethod
    def active_window(self) -> str | None:
        """Texto ``"<título> | <classe/processo>"`` da janela em foco.

        Retorna ``None`` quando não é possível consultar — o chamador deve
        tratar isso como *fail closed* (não capturar) se a config exigir.
        """

    @abstractmethod
    def list_monitors(self) -> list[Monitor]:
        """Monitores habilitados, em ordem estável de índice."""

    @abstractmethod
    def active_monitor(self) -> Monitor | None:
        """Monitor que contém a janela em foco, se determinável."""

    # --- Tela ------------------------------------------------------------
    @abstractmethod
    def grab_frame(self, dest_dir: Path, stamp: str, cfg: ScreenConfig, window_text: str) -> list[Path]:
        """Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados.

        ``stamp`` é o prefixo de timestamp já formatado. A decisão de
        privacidade (janela sensível / indisponível) é feita antes por quem
        chama; aqui só se produz a imagem.
        """

    # --- Áudio -----------------------------------------------------------
    def audio_setup(self) -> None:
        """Prepara o roteamento de áudio (no-op onde não for necessário)."""

    def audio_teardown(self) -> None:
        """Desfaz o roteamento de áudio (no-op onde não for necessário)."""

    @abstractmethod
    def audio_record_argv(self, cfg: AudioConfig) -> list[str]:
        """argv do ``ffmpeg`` que grava mic + saída do sistema num único WAV.

        O comando deve segmentar em blocos de ``segment_seconds`` e escrever
        ``audio-%Y%m%d-%H%M%S.wav`` dentro de ``cfg.outdir``, em PCM s16le
        16 kHz. O Linux legado pode fornecer a mixagem mono do RecordBus; no
        Windows, mic, Discord e demais sons ocupam três canais temporários que
        são convertidos para mono depois do processamento bem-sucedido.
        """

    @abstractmethod
    def audio_diagnostics(self) -> dict[str, object]:
        """Info legível sobre quais dispositivos de áudio foram encontrados.

        Usado pelo self-test para revelar, antes de gravar, se a captura da
        saída do sistema é possível sem dependências extras.
        """
