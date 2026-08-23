from __future__ import annotations

import os
import shlex
from pathlib import Path, PurePosixPath

HOME = Path.home()
DATA_ROOT = Path(os.environ.get("CAPTURA_DIA_ROOT", HOME / "captura-dia"))


def _config_dir() -> Path:
    """Onde ficam ``tela.conf`` e a lista de janelas sensíveis.

    No Linux, o lugar de sempre: ``XDG_CONFIG_HOME`` (ou ``~/.config``).

    No Windows a escolha natural seria ``%APPDATA%``, mas ela é uma armadilha:
    o Python da Microsoft Store roda com virtualização de sistema de arquivos e
    enxerga um ``%APPDATA%`` privado, dentro de ``LocalCache\\Roaming`` do
    pacote. Config escrita por um editor de texto fica invisível para o app, e
    vice-versa — sem erro nenhum, só sumindo. Por isso a config fica junto dos
    dados, em ``~/captura-dia/config``, que não sofre redirecionamento.

    ``CAPTURA_DIA_CONFIG_DIR`` sobrepõe os dois.
    """
    override = os.environ.get("CAPTURA_DIA_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    if os.name == "nt":
        return DATA_ROOT / "config"
    return Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "captura-dia"


CONFIG_DIR = _config_dir()
STORAGE_CONFIG = CONFIG_DIR / "storage.conf"


def configured_storage_root() -> Path:
    root = DATA_ROOT
    if STORAGE_CONFIG.exists():
        for raw in STORAGE_CONFIG.read_text(encoding="utf-8").splitlines():
            if raw.startswith("STORAGE_ROOT="):
                try:
                    value = shlex.split(raw.split("=", 1)[1])
                except ValueError:
                    break
                if len(value) == 1:
                    root = Path(value[0]).expanduser()
                break
    return Path(os.environ.get("CAPTURA_DIA_STORAGE_ROOT", root)).resolve()


MEDIA_ROOT = configured_storage_root()
AUDIO_DIR = MEDIA_ROOT / "audio"
SCREEN_DIR = MEDIA_ROOT / "telas"
VIDEO_DIR = MEDIA_ROOT / "video-buffer"
CLIPS_DIR = MEDIA_ROOT / "clips"
DB_PATH = Path(os.environ.get("CAPTURA_DIA_DB_PATH", MEDIA_ROOT / "lume.sqlite3")).expanduser()
SCREEN_CONFIG = CONFIG_DIR / "tela.conf"
SENSITIVE_FILE = CONFIG_DIR / "janelas-sensiveis.txt"
SCREEN_BIN = Path(os.environ.get("CAPTURA_DIA_SCREEN_BIN", HOME / "bin/captura-tela.sh"))


MEDIA_PATH_PREFIX = "media:"
MEDIA_DIRECTORIES = {"audio", "telas", "video-buffer", "clips"}


def media_source_key(raw: str | Path) -> str:
    """Retorna uma identidade de mídia portátil entre Linux e Windows.

    Registros antigos guardavam caminhos absolutos, então o mesmo arquivo era
    ``/home/.../lume/video-buffer/x.mp4`` no Linux e
    ``F:\\lume\\video-buffer\\x.mp4`` no Windows.  A identidade persistida passa
    a ser ``media:video-buffer/x.mp4``; caminhos externos aos diretórios de
    mídia conhecidos continuam intactos para não interferir em testes e usos
    explícitos fora do armazenamento configurado.
    """
    value = str(raw).strip()
    normalized = value.replace("\\", "/")
    relative = normalized[len(MEDIA_PATH_PREFIX):].lstrip("/") if normalized.startswith(MEDIA_PATH_PREFIX) else ""
    if not relative:
        padded = "/" + normalized.lstrip("/")
        for directory in MEDIA_DIRECTORIES:
            marker = f"/{directory}/"
            index = padded.lower().rfind(marker)
            if index >= 0:
                relative = padded[index + 1:]
                break
    if relative:
        parts = PurePosixPath(relative).parts
        if parts and parts[0] in MEDIA_DIRECTORIES and all(part not in {"", ".", ".."} for part in parts):
            return MEDIA_PATH_PREFIX + PurePosixPath(*parts).as_posix()
    return value


def resolve_media_source(raw: str | Path) -> Path:
    """Resolve uma identidade portátil ou um caminho legado na raiz atual."""
    key = media_source_key(raw)
    if key.startswith(MEDIA_PATH_PREFIX):
        relative = PurePosixPath(key[len(MEDIA_PATH_PREFIX):])
        return MEDIA_ROOT.joinpath(*relative.parts).resolve()
    return Path(raw).expanduser().resolve()


def media_source_name(raw: str | Path) -> str:
    key = media_source_key(raw)
    if key.startswith(MEDIA_PATH_PREFIX):
        return PurePosixPath(key[len(MEDIA_PATH_PREFIX):]).name
    return Path(raw).name
