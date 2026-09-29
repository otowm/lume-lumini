from __future__ import annotations

import os
import hashlib
import ipaddress
import json
import math
import mimetypes
import re
import secrets
import shlex
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import wave
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query
from fastapi import Request
from fastapi.responses import FileResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field

from ..capture import AudioConfig, ScreenConfig, get_backend, matched_sensitive_pattern
from ..capture.base import format_video_app_rule, parse_video_app_rule
from ..capture.imagediff import compare_images
from .database import connect, initialize, row_dict
from .audio_intelligence import embedding_for_sample
from .main_paths import AUDIO_CONFIG, AUDIO_DIR, CLIPS_DIR, CONFIG_DIR, DATA_ROOT, DB_PATH, EDIT_DIR, MEDIA_CACHE_DIR, MEDIA_ROOT, video_game_label, SCREEN_CONFIG, SCREEN_DIR, SENSITIVE_FILE, STORAGE_CONFIG, VIDEO_DIR, media_source_key, media_source_name, resolve_media_source, unlink_with_retry
from .runtime import VIDEO_ACTIVITY_FRESH_SECONDS, pipeline_pause_flag, video_activity_flag, video_end_request_flag, video_recording_flag
from .retention import cleanup_processed_capture_media, cleanup_ready_days, cleanup_settings, save_cleanup_settings
from . import editing, game_icons, mode, prompts, sharing, tags as tag_vocabulary
from .services import ActionResult, get_manager


HOME = Path.home()
_HIDDEN_PROCESS = getattr(subprocess, "CREATE_NO_WINDOW", 0)

ALLOWED_CONFIG = {
    "CAPTURE_MODE",
    "INTERVAL_SECONDS",
    "CHANGE_POLL_SECONDS",
    "CHANGE_THRESHOLD_PERCENT",
    "CHANGE_MAX_INTERVAL_SECONDS",
    "CAPTURE_ROOT",
    "BACKEND",
    "MAX_GEOMETRY",
    "OUTPUTS",
    "SPLIT_MONITORS",
    "ACTIVE_MONITOR_ONLY",
    "PRIVACY_FAIL_CLOSED",
    "VIDEO_ENABLED","VIDEO_FPS","VIDEO_GEOMETRY","VIDEO_SEGMENT_SECONDS","VIDEO_CAPTURE_MODE","VIDEO_REPLAY_SECONDS","VIDEO_CODEC","VIDEO_ENCODER","VIDEO_QUALITY","VIDEO_AUDIO",
    "VIDEO_SAMPLE_FRAMES","VIDEO_SAMPLE_GEOMETRY","VIDEO_RETENTION_MINUTES","DELETE_AFTER_DESCRIPTION","PAUSE_OTHER_CAPTURES",
    "VIDEO_ANALYSIS_PROFILE","VIDEO_SCAN_INTERVAL_SECONDS","VIDEO_MAX_KEYFRAMES","VIDEO_FOCUS_GRACE_SECONDS",
    "VIDEO_WEB_SEARCH_ENABLED","SEARXNG_URL","VIDEO_WEB_SEARCH_SAFETY_LIMIT","AI_THINKING_ENABLED",
    "LUME_VISION_MODEL","LUME_TEXT_MODEL","VIDEO_MARKER_HOTKEY","VIDEO_MARKER_KEY_CODE","VIDEO_HOTKEY_HOLD_SECONDS","VIDEO_MARKER_PREROLL_SECONDS",
    "VIDEO_HUD_ENABLED","VIDEO_HUD_PLACEMENT","VIDEO_HUD_CORNER","VIDEO_HUD_HOTKEY","VIDEO_HUD_SOUND","VIDEO_SOUND_VOLUME",
    "VIDEO_RESOLVE_FPS","VIDEO_RESOLVE_START_TIMECODE",
    "MIC_DENOISE_ENABLED","MIC_GATE_THRESHOLD_DB",
}
VIDEO_CONFIG = CONFIG_DIR / "video.conf"
VIDEO_APPS = CONFIG_DIR / "video-apps.txt"
VIDEO_THUMBNAIL_DIR = MEDIA_CACHE_DIR / "video-thumbnails"
VIDEO_AUDIO_TRACK_DIR = MEDIA_CACHE_DIR / "video-audio-tracks"
LEGACY_VIDEO_THUMBNAIL_DIR = CONFIG_DIR / "video-thumbnails"
LEGACY_VIDEO_AUDIO_TRACK_DIR = CONFIG_DIR / "video-audio-tracks"
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v"}
_VIDEO_THUMBNAIL_LOCK = threading.Lock()
_VIDEO_AUDIO_TRACK_LOCK = threading.Lock()
_VIDEO_AUDIO_TRACK_JOBS_LOCK = threading.Lock()
_VIDEO_AUDIO_TRACK_JOBS: dict[str, "_VideoAudioTrackJob"] = {}

@asynccontextmanager
async def lifespan(_app: FastAPI):
    migrate_legacy_media_caches()
    initialize()
    # No Windows o supervisor vive aqui dentro: sobe a captura marcada como
    # habilitada e cuida do agendamento enquanto a interface estiver aberta.
    manager = get_manager()
    manager.startup()
    if os.name == "nt":
        # ``video.conf`` é a preferência do usuário; services.json é apenas o
        # estado operacional do supervisor e pode ficar vazio após migração ou
        # encerramento inesperado.  Reconciliar os dois evita mostrar vídeo
        # habilitado na interface enquanto o gravador permanece parado.
        video_config = parse_shell_config(VIDEO_CONFIG)
        video_enabled = video_config.get("VIDEO_ENABLED", "false") == "true"
        manager.action(
            "enable" if video_enabled else "disable",
            ["captura-dia-video.service"], now=True,
        )
        # A HUD segue a mesma reconciliação: sem isto ela só subiria depois de o
        # usuário mexer nas preferências uma vez, porque services.json não sabe
        # de uma unit que nunca foi habilitada.
        hud_enabled = video_enabled and video_config.get("VIDEO_HUD_ENABLED", "true") == "true"
        manager.action(
            "enable" if hud_enabled else "disable",
            ["captura-dia-hud.service"], now=True,
        )
    try:
        yield
    finally:
        cancel_video_audio_track_jobs()
        sharing.cancel_light_jobs()
        sharing.cancel_uploads()
        manager.shutdown()


app = FastAPI(title="Lume local API", version="0.1.0", lifespan=lifespan)


def _network_values(name: str) -> list[str]:
    return [value.strip() for value in os.environ.get(name, "").split(",") if value.strip()]


REMOTE_NETWORKS = tuple(ipaddress.ip_network(value, strict=False) for value in _network_values("LUME_REMOTE_NETWORKS"))
REMOTE_HOSTS = tuple(_network_values("LUME_REMOTE_HOSTS"))
ALLOWED_SERVER_HOSTS = {"127.0.0.1", "localhost", "::1", "testserver", *REMOTE_HOSTS}
# `["*"]` aqui, e a validação de verdade em `server_host_allowed`: a lista fixa
# do TrustedHost não sabe aceitar "qualquer IP desta rede", e é justamente isso
# que a instalação de quem não é técnico precisa — o endereço da máquina na LAN
# muda de casa para casa e de aluguel de DHCP para o próximo.
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

#: Rotas que só existem com a análise instalada. Uma tabela num lugar só, em vez
#: de um `Depends` em quarenta assinaturas: dá para auditar de relance e os
#: testes conseguem percorrê-la — inclusive para cobrar que toda rota nova seja
#: classificada de um lado ou do outro.
_PREFIXOS_IA = (
    "/api/search", "/api/summary", "/api/days", "/api/timeline", "/api/activities",
    "/api/captures", "/api/pipeline", "/api/tags", "/api/ollama",
    "/api/voice-identities", "/api/settings/prompts", "/api/settings/schedule",
)
#: As de vídeo não têm prefixo comum: a mesma família de caminhos serve para
#: gravar e para analisar, e só o sufixo distingue.
_SUFIXOS_IA = (
    re.compile(r"^/api/videos/process$"),
    re.compile(r"^/api/videos/\d+/(analysis|context)$"),
    re.compile(r"^/api/videos/\d+/speakers(/|$)"),
    re.compile(r"^/api/video-sessions/\d+/(process|analysis|context)$"),
    re.compile(r"^/api/test/screen-sequence"),
    re.compile(r"^/api/videos/\d+/markers/ai$"),
)


def rota_de_ia(caminho: str) -> bool:
    """Se este caminho só faz sentido com o pipeline instalado."""
    if caminho.startswith(_PREFIXOS_IA):
        return True
    return any(padrao.match(caminho) for padrao in _SUFIXOS_IA)


@app.middleware("http")
async def recusar_analise_no_lumini(request: Request, call_next):
    """No Lumini, o que depende de IA responde 409 em vez de tentar.

    Esconder os botões na interface não basta: um POST feito na mão chamaria um
    Ollama que não existe naquela máquina, e o erro sairia como falha de rede no
    meio de um traceback. 409 porque a rota existe — o que não comporta é o
    estado da instalação.
    """
    if mode.e_lumini() and rota_de_ia(request.url.path):
        return JSONResponse(status_code=409, content={
            "detail": "Esta instalação é o Lumini: a análise por IA não foi instalada.",
        })
    return await call_next(request)


def remote_client_allowed(host: str) -> bool:
    if host == "testclient":
        return True
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return False
    return address.is_loopback or any(address in network for network in REMOTE_NETWORKS)


def server_host_allowed(host: str) -> bool:
    """Se o ``Host`` (ou a origem) descreve este servidor.

    Além dos nomes configurados, aceita **qualquer IP literal dentro das redes
    autorizadas**. Sem isso, abrir a interface para a rede exigiria fixar o
    endereço da máquina — que muda ao trocar de Wi-Fi ou ao renovar o DHCP — e a
    interface passaria a recusar sozinha, com um 400 que ninguém liga à causa.

    Isso não afrouxa a proteção contra DNS rebinding, que é o motivo de conferir
    o ``Host``: um ataque desses chega com um *domínio* no cabeçalho, nunca com
    um IP literal da rede local.
    """
    name = (host or "").strip()
    if not name:
        return True
    # Tira a porta e os colchetes de IPv6 antes de comparar.
    if name.startswith("["):
        name = name[1:].partition("]")[0]
    elif name.count(":") == 1:
        name = name.partition(":")[0]
    name = name.lower()
    if name in ALLOWED_SERVER_HOSTS:
        return True
    try:
        address = ipaddress.ip_address(name)
    except ValueError:
        return False
    return address.is_loopback or any(address in network for network in REMOTE_NETWORKS)


def origin_allowed(origin: str) -> bool:
    try:
        parsed = urllib.parse.urlsplit(origin)
    except ValueError:
        return False
    return parsed.scheme in {"http", "https"} and server_host_allowed(parsed.netloc)


@app.middleware("http")
async def local_origin_only(request: Request, call_next):
    client_host = request.client.host if request.client else ""
    if not remote_client_allowed(client_host):
        return JSONResponse(status_code=403, content={"detail": "Cliente fora da rede autorizada"})
    if not server_host_allowed(request.headers.get("host", "")):
        return JSONResponse(status_code=400, content={"detail": "Cabeçalho Host não autorizado"})
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin and not origin_allowed(origin):
            return JSONResponse(status_code=403, content={"detail": "Origem não autorizada"})
    return await call_next(request)


class ScreenSettings(BaseModel):
    capture_mode: Literal["interval", "change"]
    interval_seconds: int = Field(ge=1, le=3600)
    change_poll_seconds: int = Field(ge=1, le=3600)
    change_threshold_percent: float = Field(ge=0.1, le=100)
    change_max_interval_seconds: int = Field(ge=1, le=86400)
    max_geometry: str = Field(max_length=32)
    split_monitors: bool
    active_monitor_only: bool
    privacy_fail_closed: bool


class AudioSettings(BaseModel):
    mic_denoise_enabled: bool
    mic_gate_threshold_db: float = Field(ge=-60, le=-10)


class SensitiveWindows(BaseModel):
    patterns: list[str] = Field(max_length=200)


class PipelineRequest(BaseModel):
    limit_audio: int = Field(default=10, ge=0, le=500)
    limit_screen: int = Field(default=100, ge=0, le=5000)
    summarize: bool = True


class ProcessFileRequest(BaseModel):
    kind: Literal["screen", "audio"]
    path: str = Field(max_length=4096)


class ScreenSequenceTestRequest(BaseModel):
    paths: list[str] = Field(min_length=2, max_length=30)


class TagCreate(BaseModel):
    label: str = Field(min_length=1, max_length=60)
    criterion: str = Field(default="", max_length=400)


class TagStatusUpdate(BaseModel):
    status: Literal["candidate", "active", "dormant", "rejected"]


class TagMergeRequest(BaseModel):
    into: str = Field(min_length=1, max_length=60)


class TagTestRequest(BaseModel):
    tags: list[str] = Field(min_length=1, max_length=20)
    context: str = Field(default="", max_length=2000)
    use_laya: bool = True


class VideoProcessRequest(BaseModel):
    path: str = Field(max_length=4096)


class VideoSessionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    source_folder: str = Field(default="", max_length=1000)


class ContextUpdate(BaseModel):
    context: str = Field(default="", max_length=10000)

class VideoJoinRequest(BaseModel):
    video_ids: list[int] = Field(default_factory=list, max_length=200)
    video_paths: list[str] = Field(default_factory=list, max_length=200)
    session_ids: list[int] = Field(default_factory=list, max_length=100)
    name: str = Field(min_length=1, max_length=200)

class MarkerCreate(BaseModel):
    offset_seconds: float = Field(ge=0, le=86400)
    title: str = Field(default="", max_length=200)

class MarkerUpdate(BaseModel):
    title: str = Field(default="", max_length=200)

class VideoDateUpdate(BaseModel):
    captured_at: datetime


class ShareUploadRequest(BaseModel):
    path: str = Field(min_length=1, max_length=1024)
    use_light: bool = True
    limit_mb: int | None = Field(default=None, ge=1, le=4096)
    host: str = Field(default="", max_length=40)
    expires: str = Field(default="", max_length=8)
    # Sem valor padrão: publicar um vídeo é decisão de quem publica, e um campo
    # que já vem marcado não é decisão nenhuma.
    confirm_public_upload: bool = False


class VideoTrimRequest(BaseModel):
    start_seconds: float = Field(ge=0, le=86400)
    end_seconds: float = Field(gt=0, le=86400)


class SpeakerLabelUpdate(BaseModel):
    label: str = Field(min_length=1, max_length=80)


class RetentionUpdate(BaseModel):
    preserved: bool


class CleanupSettings(BaseModel):
    enabled: bool


class PromptUpdate(BaseModel):
    text: str


def enroll_voice_identity(db, source_kind: str, source_id: int, speaker: dict, label: str, source: Path) -> dict:
    observation = db.execute(
        "SELECT embedding_json FROM speaker_observations WHERE source_kind=? AND source_id=? AND speaker_id=?",
        (source_kind, source_id, speaker["id"]),
    ).fetchone()
    vector = json.loads(observation["embedding_json"]) if observation else embedding_for_sample(
        source, float(speaker.get("sample_start", 0)), float(speaker.get("sample_end", 0)),
    )
    if not observation:
        db.execute(
            "INSERT OR REPLACE INTO speaker_observations(source_kind,source_id,speaker_id,embedding_json) VALUES(?,?,?,?)",
            (source_kind, source_id, speaker["id"], json.dumps(vector)),
        )
    existing = db.execute("SELECT * FROM voice_identities WHERE label=? COLLATE NOCASE", (label,)).fetchone()
    if existing:
        identity_id = existing["id"]
    else:
        identity_id = db.execute(
            "INSERT INTO voice_identities(label,embedding_json) VALUES(?,?)", (label, json.dumps(vector)),
        ).lastrowid
    speaker.update(label=label, identity_id=identity_id, confidence=1.0, identified=True, confirmed=True)
    return speaker


def _normalized_average(vectors: list[list[float]]) -> list[float]:
    if not vectors:
        return []
    size = len(vectors[0])
    valid = [vector for vector in vectors if len(vector) == size]
    averaged = [sum(float(vector[index]) for vector in valid) / len(valid) for index in range(size)]
    norm = math.sqrt(sum(value * value for value in averaged)) or 1
    return [value / norm for value in averaged]


def rebuild_voice_identity(db, identity_id: int) -> int:
    """Recalcula um perfil dando um único voto a cada gravação."""
    source_vectors: list[list[float]] = []
    for source_kind, table in (("audio", "captures"), ("video", "video_segments")):
        rows = db.execute(f"SELECT id,speakers_json FROM {table} WHERE speakers_json!='[]'").fetchall()
        for row in rows:
            speaker_ids = [
                item.get("id") for item in json.loads(row["speakers_json"] or "[]")
                if item.get("identity_id") == identity_id and item.get("confirmed")
            ]
            if not speaker_ids:
                continue
            observations = db.execute(
                f"SELECT embedding_json FROM speaker_observations WHERE source_kind=? AND source_id=? AND speaker_id IN ({','.join('?' for _ in speaker_ids)})",
                (source_kind, row["id"], *speaker_ids),
            ).fetchall()
            within_source = _normalized_average([json.loads(item["embedding_json"]) for item in observations])
            if within_source:
                source_vectors.append(within_source)
    rebuilt = _normalized_average(source_vectors)
    if rebuilt:
        db.execute(
            "UPDATE voice_identities SET embedding_json=?,sample_count=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (json.dumps(rebuilt), len(source_vectors), identity_id),
        )
    else:
        # Uma correção pode mover a última amostra de um nome errado para
        # outro perfil. Não deixe esse perfil vazio continuar identificando
        # vozes futuras com um embedding antigo.
        db.execute("DELETE FROM voice_identities WHERE id=?", (identity_id,))
    return len(source_vectors)


def backfill_confirmed_voice_observations() -> dict[int, int]:
    missing: list[tuple[str, int, str, Path, float, float, int]] = []
    with connect() as db:
        for source_kind, table in (("audio", "captures"), ("video", "video_segments")):
            for row in db.execute(f"SELECT id,source_path,speakers_json FROM {table} WHERE speakers_json!='[]'"):
                for speaker in json.loads(row["speakers_json"] or "[]"):
                    identity_id = speaker.get("identity_id")
                    if not identity_id or not speaker.get("confirmed"):
                        continue
                    exists = db.execute(
                        "SELECT 1 FROM speaker_observations WHERE source_kind=? AND source_id=? AND speaker_id=?",
                        (source_kind, row["id"], speaker["id"]),
                    ).fetchone()
                    source = resolve_media_source(row["source_path"])
                    if not exists and source.is_file():
                        missing.append((source_kind, row["id"], speaker["id"], source, float(speaker["sample_start"]), float(speaker["sample_end"]), int(identity_id)))
    computed = []
    for source_kind, source_id, speaker_id, source, start, end, identity_id in missing:
        computed.append((source_kind, source_id, speaker_id, embedding_for_sample(source, start, end), identity_id))
    with connect() as db:
        for source_kind, source_id, speaker_id, vector, _ in computed:
            db.execute(
                "INSERT OR REPLACE INTO speaker_observations(source_kind,source_id,speaker_id,embedding_json) VALUES(?,?,?,?)",
                (source_kind, source_id, speaker_id, json.dumps(vector)),
            )
        identities = [row["id"] for row in db.execute("SELECT id FROM voice_identities")]
        return {identity_id: rebuild_voice_identity(db, identity_id) for identity_id in identities}


def voice_identity_payloads(rows) -> list[dict]:
    identities = [{**dict(row), "embedding": json.loads(row["embedding_json"])} for row in rows]
    result = []
    for identity in identities:
        duplicates = []
        for other in identities:
            if other["id"] == identity["id"] or len(other["embedding"]) != len(identity["embedding"]):
                continue
            similarity = sum(float(a) * float(b) for a, b in zip(identity["embedding"], other["embedding"]))
            if similarity >= .72:
                duplicates.append({"id": other["id"], "label": other["label"], "similarity": round(similarity, 3)})
        result.append({
            "id": identity["id"], "label": identity["label"], "sample_count": identity["sample_count"],
            "created_at": identity["created_at"], "updated_at": identity["updated_at"],
            "possible_duplicates": sorted(duplicates, key=lambda item: item["similarity"], reverse=True),
        })
    return result


class VideoSettings(BaseModel):
    enabled: bool
    codec: Literal["h264", "hevc"] = "hevc"
    # `auto` deixa o game-video-loop escolher: o VCE das Radeon Polaris (RX
    # 460–590) trava a GPU inteira com o gpu-screen-recorder, então lá o vídeo
    # é codificado pela CPU. Só vale no Linux; no Windows quem codifica é o OBS.
    encoder: Literal["auto", "gpu", "cpu"] = "auto"
    capture_mode: Literal["continuous", "clips"] = "continuous"
    replay_seconds: int = Field(default=60, ge=10, le=300)
    fps: int = Field(ge=1,le=60)
    geometry: str = Field(pattern=r"^\d{2,4}x\d{2,4}$")
    segment_seconds: int = Field(ge=0,le=14400)
    sample_frames: int = Field(ge=2,le=16)
    sample_geometry: str = Field(pattern=r"^\d{2,4}x\d{2,4}$")
    retention_minutes: int = Field(ge=5,le=1440)
    delete_after_description: bool
    pause_other_captures: bool = True
    focus_grace_seconds: int = Field(default=20, ge=0, le=3600)
    analysis_profile: Literal["fast", "balanced", "detailed", "custom"] = "detailed"
    scan_interval_seconds: float = Field(default=2.0, ge=0.5, le=30)
    max_keyframes: int = Field(default=80, ge=8, le=160)
    web_search_enabled: bool = False
    searxng_url: str = Field(default="http://127.0.0.1:8889", max_length=500)
    web_search_safety_limit: int = Field(default=50, ge=5, le=500)
    thinking_enabled: bool = False
    vision_model: str = Field(default="qwen3-vl-ctx:latest", pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,200}$")
    text_model: str = Field(default="qwen3.5:9b", pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,200}$")
    marker_hotkey: str = Field(default="F8", pattern=r"^[A-Za-z0-9+_\[\]-]{1,40}$")
    marker_key_code: str = Field(default="", pattern=r"^(Key[A-Z]|Digit[0-9]|F([1-9]|1[0-2])|BracketLeft|BracketRight)?$")
    # Tempo com o atalho abaixado que abre uma gravação longa no modo clipes.
    # Abaixo de 0,2s qualquer toque viraria gravação; acima de 3s ninguém
    # segura tanto sem achar que o atalho não pegou.
    hotkey_hold_seconds: float = Field(default=0.6, ge=0.2, le=3.0)
    marker_preroll_seconds: int = Field(default=8, ge=0, le=120)
    hud_enabled: bool = True
    hud_placement: Literal["game", "second", "both"] = "second"
    hud_corner: Literal["top-left", "top-right", "bottom-left", "bottom-right"] = "top-right"
    hud_hotkey: str = Field(default="Ctrl+Shift+F8", pattern=r"^[A-Za-z0-9+_-]{1,40}$")
    hud_sound: bool = True
    # Volume dos sons de confirmação do atalho; 0 os desliga.
    sound_volume: int = Field(default=100, ge=0, le=100)
    resolve_fps: int = Field(default=0, ge=0, le=120)
    resolve_start_timecode: str = Field(default="01:00:00:00", pattern=r"^\d{2}:[0-5]\d:[0-5]\d:\d{2}$")
    patterns: list[str] = Field(max_length=100)
    pattern_modes: dict[str, Literal["continuous", "clips"]] = Field(default_factory=dict, max_length=100)
    pattern_fps: dict[str, int] = Field(default_factory=dict, max_length=100)
    pattern_geometry: dict[str, str] = Field(default_factory=dict, max_length=100)
    pattern_sources: dict[str, Literal["game", "window"]] = Field(default_factory=dict, max_length=100)


class VideoWindowTest(BaseModel):
    patterns: list[str] = Field(max_length=100)


class ScreenChangeTest(BaseModel):
    token: str = Field(default="", max_length=100)
    threshold_percent: float = Field(ge=0.1, le=100)


class ScheduleSettings(BaseModel):
    time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    enabled: bool = True


class StorageSettings(BaseModel):
    root: str = Field(min_length=1, max_length=4096)


def run(command: list[str], timeout: int = 15, check: bool = False, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=check,
            env=env or os.environ.copy(),
            creationflags=_HIDDEN_PROCESS,
        )
    except FileNotFoundError:
        # O executável não existe neste sistema — `systemctl` no Windows, por
        # exemplo. Degradar para "comando falhou" deixa as leituras de estado
        # responderem "unknown" em vez de derrubar a API inteira com um 500.
        return subprocess.CompletedProcess(
            command, returncode=127, stdout="",
            stderr=f"{command[0]}: comando indisponível neste sistema",
        )
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
        detail = getattr(exc, "stderr", "") or getattr(exc, "stdout", "") or str(exc)
        raise HTTPException(status_code=503, detail=detail.strip()) from exc


def unit_state(unit: str) -> dict[str, str | bool]:
    """Estado de uma unit — systemd no Linux, supervisor próprio no Windows."""
    return get_manager().state(unit)


def service_action(verb: str, units: list[str], timeout: int = 30,
                   now: bool = False, no_block: bool = False) -> ActionResult:
    """Executa uma ação sobre units, seja qual for o sistema."""
    return get_manager().action(verb, units, timeout=timeout, now=now, no_block=no_block)


def stop_target_is_already_gone(result: ActionResult) -> bool:
    """Uma unit transitória coletada equivale a um job já parado."""
    detail = f"{result.stderr}\n{result.stdout}".casefold()
    return any(message in detail for message in (
        "not loaded",
        "could not be found",
        "unit not found",
        "unit desconhecida",
    ))


@app.get("/api/settings/schedule")
def get_schedule() -> dict:
    return get_manager().timer_state()


@app.put("/api/settings/schedule")
def set_schedule(settings: ScheduleSettings) -> dict:
    current = get_schedule()
    if current.get("time") == settings.time and bool(current.get("enabled")) == settings.enabled:
        return current
    result = get_manager().set_timer(settings.time, settings.enabled)
    if result.returncode != 0:
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao atualizar agendamento")
    return get_schedule()


def parse_shell_config(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    # utf-8-sig porque no Windows é comum o arquivo vir com BOM.
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in ALLOWED_CONFIG:
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            values[key] = value.replace("$HOME", str(HOME))
    return values


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_write_if_changed(path: Path, content: str) -> bool:
    """Write a config only when its contents changed."""
    try:
        if path.read_text(encoding="utf-8") == content:
            return False
    except (OSError, UnicodeError):
        pass
    atomic_write(path, content)
    return True


def _report_runtime_failure(label: str, result: ActionResult) -> None:
    if result.returncode != 0:
        print(f"[settings] {label}: {result.stderr.strip() or 'falha sem detalhes'}", file=sys.stderr)


def _apply_storage_runtime() -> None:
    for unit in ("captura-dia-audio.service", "captura-dia-tela.service", "captura-dia-video.service"):
        _report_runtime_failure(unit, service_action("try-restart", [unit], timeout=30))
    _report_runtime_failure("reinício do Lume", get_manager().restart_self())


def _apply_video_runtime(enabled: bool, refresh_shortcuts: bool, hud_enabled: bool = True) -> None:
    if refresh_shortcuts and shutil.which("kbuildsycoca6"):
        run(["kbuildsycoca6", "--noincremental"], timeout=30)
    verb = "enable" if enabled else "disable"
    result = service_action(verb, ["captura-dia-video.service"], timeout=30, now=True)
    _report_runtime_failure("gravador de vídeo", result)
    # O laço Linux relê video.conf antes de cada sessão; reiniciá-lo aqui
    # cortava a partida atual, zerava o timer e podia separar o marcador do
    # vídeo. No Windows o supervisor aplica Settings em memória por outro fluxo.
    if enabled and result.returncode == 0 and os.name == "nt":
        _report_runtime_failure("reinício do gravador de vídeo",
                                service_action("restart", ["captura-dia-video.service"], timeout=20))
    # A HUD lê a configuração só ao subir; qualquer mudança de posição, canto ou
    # atalho exige religá-la. Ela também não tem o que mostrar com o vídeo
    # seletivo desligado, então segue o estado dele.
    hud_verb = "enable" if (enabled and hud_enabled) else "disable"
    _report_runtime_failure("HUD de gravação",
                            service_action(hud_verb, ["captura-dia-hud.service"], timeout=30, now=True))
    if enabled and hud_enabled:
        _report_runtime_failure("reinício da HUD",
                                service_action("restart", ["captura-dia-hud.service"], timeout=20))
    # O daemon do atalho lê a tecla e o tempo da segurada uma vez, ao subir:
    # trocar F8 por outra tecla na interface só vale depois de reiniciá-lo. No
    # Windows quem observa o teclado é o próprio gravador, e não há unit.
    if os.name != "nt":
        hotkey_verb = "enable" if enabled else "disable"
        _report_runtime_failure(
            "atalho de gravação",
            service_action(hotkey_verb, ["captura-dia-hotkey.service"], timeout=30, now=True))
        if enabled:
            _report_runtime_failure(
                "reinício do atalho de gravação",
                service_action("restart", ["captura-dia-hotkey.service"], timeout=20))


def _restart_screen_runtime() -> None:
    _report_runtime_failure("captura de tela", service_action("try-restart", ["captura-dia-tela.service"], timeout=20))


def _restart_audio_runtime() -> None:
    # grava-audio.sh só lê audio.conf ao subir; sem religar o filtro do
    # microfone continuaria com o valor antigo até a próxima sessão.
    _report_runtime_failure("captura de áudio", service_action("try-restart", ["captura-dia-audio.service"], timeout=20))


def storage_payload(root: Path) -> dict:
    existing = root
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    usage = shutil.disk_usage(existing)
    return {
        "root": str(root),
        "directories": {
            "screen": str(root / "telas"),
            "audio": str(root / "audio"),
            "video": str(root / "video-buffer"),
            "clips": str(root / "clips"),
        },
        "disk": {"total": usage.total, "used": usage.used, "free": usage.free},
    }


def storage_candidates() -> list[dict]:
    roots = {MEDIA_ROOT, HOME / "captura-dia"}
    for parent in (Path("/mnt"), Path("/media") / HOME.name, Path("/run/media") / HOME.name):
        if parent.is_dir():
            roots.update(path for path in parent.iterdir() if path.is_dir() and path.is_mount())
    candidates = []
    for root in sorted(roots, key=str):
        try:
            candidates.append(storage_payload(root))
        except OSError:
            continue
    return candidates


@app.get("/api/settings/storage")
def get_storage_settings() -> dict:
    return {**storage_payload(MEDIA_ROOT), "candidates": storage_candidates()}


@app.put("/api/settings/storage")
def set_storage_settings(settings: StorageSettings, background_tasks: BackgroundTasks) -> dict:
    root = Path(settings.root).expanduser()
    if not root.is_absolute():
        raise HTTPException(status_code=422, detail="Escolha um caminho absoluto")
    root = root.resolve()
    if root == Path("/"):
        raise HTTPException(status_code=422, detail="A raiz do sistema não pode ser usada diretamente")
    try:
        for child in ("audio", "telas", "video-buffer", "clips"):
            (root / child).mkdir(parents=True, exist_ok=True)
        probe = root / ".lume-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        raise HTTPException(status_code=422, detail=f"Não foi possível gravar nesse local: {exc}") from exc
    restart_required = root != MEDIA_ROOT
    if restart_required:
        atomic_write_if_changed(STORAGE_CONFIG, f"STORAGE_ROOT={shlex.quote(str(root))}\n")
        background_tasks.add_task(_apply_storage_runtime)
    return {**storage_payload(root), "candidates": storage_candidates(), "restart_required": restart_required}


@app.get("/api/settings/video")
def get_video_settings() -> dict:
    config=parse_shell_config(VIDEO_CONFIG)
    default_mode=config.get("VIDEO_CAPTURE_MODE","continuous")
    raw_rules=[line.strip() for line in VIDEO_APPS.read_text(encoding="utf-8").splitlines() if line.strip() and not line.lstrip().startswith("#")] if VIDEO_APPS.exists() else []
    default_fps=int(config.get("VIDEO_FPS","30"));default_geometry=config.get("VIDEO_GEOMETRY","1920x1080")
    parsed_rules=[parse_video_app_rule(line,default_mode,default_fps,default_geometry) for line in raw_rules]
    patterns=[pattern for pattern,_mode,_fps,_geometry,_source in parsed_rules]
    pattern_modes={pattern:mode for pattern,mode,_fps,_geometry,_source in parsed_rules}
    pattern_fps={pattern:fps for pattern,_mode,fps,_geometry,_source in parsed_rules}
    pattern_geometry={pattern:geometry for pattern,_mode,_fps,geometry,_source in parsed_rules}
    pattern_sources={pattern:source for pattern,_mode,_fps,_geometry,source in parsed_rules}
    return {"enabled":config.get("VIDEO_ENABLED","false")=="true","codec":"hevc" if config.get("VIDEO_CODEC","h264").lower() in {"hevc","h265"} else "h264","encoder":config.get("VIDEO_ENCODER","auto") if config.get("VIDEO_ENCODER","auto") in {"auto","gpu","cpu"} else "auto","capture_mode":default_mode,"replay_seconds":int(config.get("VIDEO_REPLAY_SECONDS","60")),"fps":default_fps,"geometry":default_geometry,"segment_seconds":int(config.get("VIDEO_SEGMENT_SECONDS","60")),"sample_frames":int(config.get("VIDEO_SAMPLE_FRAMES","6")),"sample_geometry":config.get("VIDEO_SAMPLE_GEOMETRY","960x540"),"retention_minutes":int(config.get("VIDEO_RETENTION_MINUTES","60")),"delete_after_description":config.get("DELETE_AFTER_DESCRIPTION","false")=="true","pause_other_captures":config.get("PAUSE_OTHER_CAPTURES","true")=="true","focus_grace_seconds":int(config.get("VIDEO_FOCUS_GRACE_SECONDS","20")),"analysis_profile":config.get("VIDEO_ANALYSIS_PROFILE","detailed"),"scan_interval_seconds":float(config.get("VIDEO_SCAN_INTERVAL_SECONDS","2")),"max_keyframes":int(config.get("VIDEO_MAX_KEYFRAMES","80")),"web_search_enabled":config.get("VIDEO_WEB_SEARCH_ENABLED","false")=="true","searxng_url":config.get("SEARXNG_URL","http://127.0.0.1:8889"),"web_search_safety_limit":int(config.get("VIDEO_WEB_SEARCH_SAFETY_LIMIT","50")),"thinking_enabled":config.get("AI_THINKING_ENABLED","false")=="true","vision_model":os.environ.get("LUME_VISION_MODEL") or config.get("LUME_VISION_MODEL","qwen3-vl-ctx:latest"),"text_model":os.environ.get("LUME_TEXT_MODEL") or config.get("LUME_TEXT_MODEL","qwen3.5:9b"),"marker_hotkey":config.get("VIDEO_MARKER_HOTKEY","F8"),"marker_key_code":config.get("VIDEO_MARKER_KEY_CODE",""),"hotkey_hold_seconds":float(config.get("VIDEO_HOTKEY_HOLD_SECONDS","0.6")),"marker_preroll_seconds":int(config.get("VIDEO_MARKER_PREROLL_SECONDS","8")),"hud_enabled":config.get("VIDEO_HUD_ENABLED","true")=="true","hud_placement":config.get("VIDEO_HUD_PLACEMENT","second"),"hud_corner":config.get("VIDEO_HUD_CORNER","top-right"),"hud_hotkey":config.get("VIDEO_HUD_HOTKEY","Ctrl+Shift+F8"),"hud_sound":config.get("VIDEO_HUD_SOUND","true")=="true","sound_volume":_config_int(config,"VIDEO_SOUND_VOLUME",100,0,100),"resolve_fps":int(config.get("VIDEO_RESOLVE_FPS","0")),"resolve_start_timecode":config.get("VIDEO_RESOLVE_START_TIMECODE","01:00:00:00"),"patterns":patterns,"pattern_modes":pattern_modes,"pattern_fps":pattern_fps,"pattern_geometry":pattern_geometry,"pattern_sources":pattern_sources,"service":unit_state("captura-dia-video.service")}


def _config_int(config: dict, key: str, default: int, minimum: int, maximum: int) -> int:
    try:
        return max(minimum, min(maximum, int(config.get(key, default))))
    except (TypeError, ValueError):
        return default


def _confirmation_sounds() -> dict:
    from ..capture import sounds

    return {"items": [{"slot": slot, "label": label,
                       "custom": (path := sounds.custom_sound(slot)) is not None,
                       "name": path.name if path else ""}
                      for slot, (label, _default) in sounds.SLOTS.items()],
            "presets": sounds.presets()}


def _sound_slot(slot: str):
    from ..capture import sounds

    if slot not in sounds.SLOTS:
        raise HTTPException(status_code=404, detail="Som desconhecido")
    return sounds


@app.get("/api/settings/video/sounds")
def list_confirmation_sounds() -> dict:
    """Os três sons de confirmação do atalho e se cada um foi personalizado."""
    return _confirmation_sounds()


@app.post("/api/settings/video/sounds/preset/{theme}")
def apply_confirmation_sound_preset(theme: str) -> dict:
    """Preenche todos os sons com um pacote pronto do uisfx."""
    from ..capture import sounds

    try:
        sounds.apply_preset(theme)
    except ValueError:
        raise HTTPException(status_code=404, detail="Pacote de sons desconhecido")
    return _confirmation_sounds()


@app.put("/api/settings/video/sounds/{slot}")
async def upload_confirmation_sound(slot: str, request: Request,
                                    name: str = Query(min_length=1, max_length=255)) -> dict:
    """Troca o som de um slot pelo arquivo enviado.

    O gravador procura ``sons/<slot>.*`` a cada toque, então vale no próximo
    atalho, sem reiniciar nada.
    """
    sounds = _sound_slot(slot)
    extension = Path(name).suffix.lower()
    if extension not in sounds.EXTENSIONS:
        raise HTTPException(status_code=422,
                            detail=f"Formato não aceito. Use: {', '.join(sorted(sounds.EXTENSIONS))}")
    data = bytearray()
    async for chunk in request.stream():
        data.extend(chunk)
        if len(data) > sounds.MAX_BYTES:
            raise HTTPException(status_code=413, detail="Som grande demais; o limite é 5 MB")
    if not data:
        raise HTTPException(status_code=422, detail="Arquivo vazio")
    sounds.SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    partial = sounds.SOUNDS_DIR / f".{slot}{extension}.upload"
    partial.write_bytes(bytes(data))
    sounds.clear_custom(slot)
    partial.replace(sounds.SOUNDS_DIR / f"{slot}{extension}")
    return _confirmation_sounds()


@app.delete("/api/settings/video/sounds/{slot}")
def reset_confirmation_sound(slot: str) -> dict:
    _sound_slot(slot).clear_custom(slot)
    return _confirmation_sounds()


@app.post("/api/settings/video/sounds/{slot}/test")
def test_confirmation_sound(slot: str, volume: int = Query(default=100, ge=0, le=100)) -> dict:
    """Toca o som nesta máquina, com o volume ainda não salvo da interface."""
    if not _sound_slot(slot).play(slot, volume):
        raise HTTPException(status_code=503, detail="Não consegui tocar o som (pw-play/paplay ausentes?)")
    return {"ok": True}


@app.get("/api/ollama/models")
def list_ollama_models() -> dict:
    base = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
    try:
        with urllib.request.urlopen(f"{base}/api/tags", timeout=5) as response:
            payload = json.loads(response.read())
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
        return {"online": False, "models": [], "error": str(exc)}
    models = []
    for item in payload.get("models", []):
        name = str(item.get("name") or item.get("model") or "").strip()
        if not name:
            continue
        capabilities: list[str] = []
        try:
            request = urllib.request.Request(
                f"{base}/api/show", data=json.dumps({"model": name}).encode(),
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                capabilities = [str(value) for value in json.loads(response.read()).get("capabilities", [])]
        except (OSError, urllib.error.URLError, json.JSONDecodeError):
            pass
        models.append({
            "name": name, "size": int(item.get("size") or 0),
            "modified_at": item.get("modified_at") or "", "capabilities": capabilities,
        })
    return {"online": True, "models": sorted(models, key=lambda item: item["name"].casefold())}


@app.put("/api/settings/video")
def set_video_settings(settings: VideoSettings, background_tasks: BackgroundTasks) -> dict:
    for pattern in settings.patterns:
        try: re.compile(pattern)
        except re.error as exc: raise HTTPException(status_code=422,detail=f"Regex inválida: {pattern}: {exc}") from exc
    content=f"""VIDEO_ENABLED={'true' if settings.enabled else 'false'}
VIDEO_CAPTURE_MODE={settings.capture_mode}
VIDEO_REPLAY_SECONDS={settings.replay_seconds}
VIDEO_FPS={settings.fps}
VIDEO_GEOMETRY={settings.geometry}
VIDEO_SEGMENT_SECONDS={settings.segment_seconds}
VIDEO_CODEC={settings.codec}
VIDEO_ENCODER={settings.encoder}
VIDEO_QUALITY=high
VIDEO_AUDIO='device:MicBus.monitor|device:DiscordBus.monitor|device:RecordBus.monitor,device:MicBus.monitor,device:DiscordBus.monitor,device:RecordBus.monitor'
VIDEO_SAMPLE_FRAMES={settings.sample_frames}
VIDEO_SAMPLE_GEOMETRY={settings.sample_geometry}
VIDEO_RETENTION_MINUTES={settings.retention_minutes}
DELETE_AFTER_DESCRIPTION={'true' if settings.delete_after_description else 'false'}
PAUSE_OTHER_CAPTURES={'true' if settings.pause_other_captures else 'false'}
VIDEO_FOCUS_GRACE_SECONDS={settings.focus_grace_seconds}
VIDEO_ANALYSIS_PROFILE={settings.analysis_profile}
VIDEO_SCAN_INTERVAL_SECONDS={settings.scan_interval_seconds}
VIDEO_MAX_KEYFRAMES={settings.max_keyframes}
VIDEO_WEB_SEARCH_ENABLED={'true' if settings.web_search_enabled else 'false'}
SEARXNG_URL={shlex.quote(settings.searxng_url.rstrip('/'))}
VIDEO_WEB_SEARCH_SAFETY_LIMIT={settings.web_search_safety_limit}
AI_THINKING_ENABLED={'true' if settings.thinking_enabled else 'false'}
LUME_VISION_MODEL={shlex.quote(settings.vision_model)}
LUME_TEXT_MODEL={shlex.quote(settings.text_model)}
VIDEO_MARKER_HOTKEY={shlex.quote(settings.marker_hotkey)}
VIDEO_MARKER_KEY_CODE={shlex.quote(settings.marker_key_code)}
VIDEO_HOTKEY_HOLD_SECONDS={settings.hotkey_hold_seconds}
VIDEO_MARKER_PREROLL_SECONDS={settings.marker_preroll_seconds}
VIDEO_HUD_ENABLED={'true' if settings.hud_enabled else 'false'}
VIDEO_HUD_PLACEMENT={settings.hud_placement}
VIDEO_HUD_CORNER={settings.hud_corner}
VIDEO_HUD_HOTKEY={shlex.quote(settings.hud_hotkey)}
VIDEO_HUD_SOUND={'true' if settings.hud_sound else 'false'}
VIDEO_SOUND_VOLUME={settings.sound_volume}
VIDEO_RESOLVE_FPS={settings.resolve_fps}
VIDEO_RESOLVE_START_TIMECODE={settings.resolve_start_timecode}
"""
    for pattern,fps in settings.pattern_fps.items():
        if pattern in settings.patterns and not 1 <= fps <= 60:
            raise HTTPException(status_code=422,detail=f"FPS inválido para {pattern}")
    for pattern,geometry in settings.pattern_geometry.items():
        if pattern in settings.patterns and not re.fullmatch(r"\d{2,4}x\d{2,4}",geometry):
            raise HTTPException(status_code=422,detail=f"Resolução inválida para {pattern}")
    app_rules=[format_video_app_rule(pattern,settings.pattern_modes.get(pattern,settings.capture_mode),settings.pattern_fps.get(pattern,settings.fps),settings.pattern_geometry.get(pattern,settings.geometry),settings.pattern_sources.get(pattern,"game")) for pattern in settings.patterns if pattern.strip()]
    config_changed = atomic_write_if_changed(VIDEO_CONFIG, content)
    rules_changed = atomic_write_if_changed(VIDEO_APPS, "# Gerenciado pelo Lume\n"+"\n".join(app_rules)+"\n")
    shortcut_file = Path(os.environ.get("XDG_DATA_HOME", str(Path.home()/".local/share"))) / "applications/lume-marker.desktop"
    shortcut_file.parent.mkdir(parents=True,exist_ok=True)
    shortcut_changed = atomic_write_if_changed(shortcut_file, f"""[Desktop Entry]
Type=Application
Name=Lume — adicionar destaque
Exec={Path.home()}/bin/lume-add-video-marker
Icon=bookmark-new
NoDisplay=true
X-KDE-Shortcuts={settings.marker_hotkey}
""")
    hud_shortcut_file = shortcut_file.with_name("lume-hud-toggle.desktop")
    hud_shortcut_changed = atomic_write_if_changed(hud_shortcut_file, f"""[Desktop Entry]
Type=Application
Name=Lume — alternar HUD
Exec={Path.home()}/bin/lume-toggle-video-hud
Icon=video-display
NoDisplay=true
X-KDE-Shortcuts={settings.hud_hotkey}
""")
    if config_changed or rules_changed or shortcut_changed or hud_shortcut_changed:
        background_tasks.add_task(_apply_video_runtime, settings.enabled,
                                  shortcut_changed or hud_shortcut_changed,
                                  settings.hud_enabled)
    return get_video_settings()


_DIRECTORY_STATS_CACHE: dict[tuple[str, str], tuple[float, dict[str, int | str | None]]] = {}
_DIRECTORY_STATS_REFRESHING: set[tuple[str, str]] = set()
_DIRECTORY_STATS_LOCK = threading.Lock()


def _scan_directory_stats(path: Path, suffix: str) -> dict[str, int | str | None]:
    count = 0
    total = 0
    latest_path: str | None = None
    latest_mtime = -1.0
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if not entry.name.endswith(suffix) or not entry.is_file():
                    continue
                try:
                    stat = entry.stat()
                except OSError:
                    continue
                count += 1
                total += stat.st_size
                if stat.st_mtime > latest_mtime:
                    latest_mtime = stat.st_mtime
                    latest_path = entry.path
    except OSError:
        pass
    return {"count": count, "bytes": total, "latest": latest_path}


def _refresh_directory_stats(key: tuple[str, str], path: Path, suffix: str) -> None:
    try:
        stats = _scan_directory_stats(path, suffix)
        with _DIRECTORY_STATS_LOCK:
            _DIRECTORY_STATS_CACHE[key] = (time.monotonic(), stats)
    finally:
        with _DIRECTORY_STATS_LOCK:
            _DIRECTORY_STATS_REFRESHING.discard(key)


def directory_stats(path: Path, suffix: str, max_age: float = 3.0) -> dict[str, int | str | None]:
    """Retorna contagens sem fazer o endpoint de status esperar pelo disco.

    Depois da primeira leitura, valores vencidos são atualizados em segundo
    plano. O estado operacional dos serviços continua sendo consultado em toda
    chamada; somente os totais de arquivos podem ficar alguns segundos atrás.
    """
    key = (str(path), suffix)
    now = time.monotonic()
    with _DIRECTORY_STATS_LOCK:
        cached = _DIRECTORY_STATS_CACHE.get(key)
        if cached and now - cached[0] < max_age:
            return dict(cached[1])
        if cached:
            if key not in _DIRECTORY_STATS_REFRESHING:
                _DIRECTORY_STATS_REFRESHING.add(key)
                threading.Thread(
                    target=_refresh_directory_stats,
                    args=(key, path, suffix),
                    daemon=True,
                    name=f"lume-stats-{path.name}",
                ).start()
            return dict(cached[1])
    stats = _scan_directory_stats(path, suffix)
    with _DIRECTORY_STATS_LOCK:
        _DIRECTORY_STATS_CACHE[key] = (now, stats)
    return dict(stats)

def video_recorded_at(path: Path, fallback: datetime | None = None) -> datetime:
    probe = run(["ffprobe","-v","error","-show_entries","format_tags=creation_time:stream_tags=creation_time","-of","json",str(path)],timeout=60)
    if probe.returncode == 0:
        try:
            data=json.loads(probe.stdout or "{}")
            values=[stream.get("tags",{}).get("creation_time") for stream in data.get("streams",[])]
            values.append(data.get("format",{}).get("tags",{}).get("creation_time"))
            for value in values:
                if value:
                    return datetime.fromisoformat(str(value).replace("Z","+00:00")).astimezone()
        except (ValueError,TypeError,json.JSONDecodeError): pass
    date_name=path.name.split("_importado_",1)[-1]
    match=re.search(r"(\d{4})[.-](\d{2})[.-](\d{2})[-_ ](\d{2})[.-](\d{2})(?:[.-](\d{2}))?",date_name)
    if match:
        parts=[int(value) if value else 0 for value in match.groups()]
        return datetime(*parts[:5],parts[5]).astimezone()
    match=re.search(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})",date_name)
    if match: return datetime.strptime("_".join(match.groups()),"%Y-%m-%d_%H-%M-%S").astimezone()
    return fallback or datetime.fromtimestamp(path.stat().st_mtime).astimezone()


def probe_video_duration(path: Path) -> float:
    """Lê a duração do contêiner localmente; não envolve modelos ou análise."""
    probe = run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=nk=1:nw=1", str(path),
    ], timeout=30)
    if probe.returncode != 0:
        return 0.0
    try:
        duration = float(probe.stdout.strip())
    except (TypeError, ValueError):
        return 0.0
    return duration if math.isfinite(duration) and duration > 0 else 0.0


def trim_video_command(source: Path, destination: Path, start: float, length: float) -> list[str]:
    """Monta uma conversão precisa e preserva todas as faixas de áudio."""
    webm = source.suffix.lower() == ".webm"
    video_codec = ["-c:v", "libvpx-vp9", "-crf", "24", "-b:v", "0"] if webm else [
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
    ]
    audio_codec = ["-c:a", "libopus", "-b:a", "160k"] if webm else ["-c:a", "aac", "-b:a", "192k"]
    return [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-ss", f"{start:.3f}", "-i", str(source), "-t", f"{length:.3f}",
        "-map", "0:v:0", "-map", "0:a?", "-map_metadata", "0",
        *video_codec, *audio_codec, "-avoid_negative_ts", "make_zero", str(destination),
    ]


def backfill_video_session_durations() -> int:
    """Preenche durações ausentes das sessões usando somente metadados dos arquivos."""
    with connect() as db:
        rows = db.execute(
            """SELECT id,source_path FROM video_segments
               WHERE session_id IS NOT NULL AND coalesce(duration_seconds,0)<=0"""
        ).fetchall()
    pending = [(row["id"], resolve_media_source(row["source_path"])) for row in rows]
    pending = [(video_id, path) for video_id, path in pending if path.is_file()]
    if not pending:
        return 0
    workers = min(4, len(pending))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        durations = list(pool.map(lambda item: probe_video_duration(item[1]), pending))
    updates = [(duration, item[0]) for item, duration in zip(pending, durations) if duration > 0]
    if updates:
        with connect() as db:
            db.executemany("UPDATE video_segments SET duration_seconds=? WHERE id=?", updates)
    return len(updates)


AUTO_VIDEO_SESSION_PREFIX = "lume-capture:"


def captured_video_session(path: Path) -> tuple[str, str] | None:
    """Lê a identidade portátil deixada pelo gravador seletivo.

    Vídeos antigos só têm ``.window``; eles viram sessões individuais para não
    continuarem aparecendo como vídeos avulsos. Os gravadores novos reutilizam
    a mesma chave em todos os segmentos de uma sessão de jogo.
    """
    window_file = path.with_suffix(path.suffix + ".window")
    session_file = path.with_suffix(path.suffix + ".session")
    window = ""
    if window_file.is_file():
        window = window_file.read_text(encoding="utf-8-sig").strip()
    if session_file.is_file():
        lines = session_file.read_text(encoding="utf-8-sig").splitlines()
        key = lines[0].strip() if lines else ""
        if len(lines) > 1 and not window:
            window = lines[1].strip()
        if not re.fullmatch(r"[A-Za-z0-9._-]{1,200}", key):
            return None
    elif window:
        key = f"legacy-{path.name}"
    else:
        return None
    name = window.split(" | ", 1)[0].strip() or "Sessão de jogo"
    return key, name[:200]


def safe_screen_path(raw: str) -> Path:
    candidate = resolve_media_source(raw)
    root = SCREEN_DIR.resolve()
    if candidate.parent != root or candidate.suffix.lower() != ".png":
        raise HTTPException(status_code=403, detail="Arquivo fora da pasta de telas")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Screenshot não encontrado")
    return candidate


def safe_audio_path(raw: str) -> Path:
    candidate = resolve_media_source(raw)
    root = AUDIO_DIR.resolve()
    if candidate.parent != root or candidate.suffix.lower() != ".wav":
        raise HTTPException(status_code=403, detail="Arquivo fora da pasta de áudio")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Áudio não encontrado")
    return candidate


def _audio_channels(path: Path) -> int:
    try:
        with wave.open(str(path), "rb") as source:
            return source.getnchannels()
    except (wave.Error, OSError):
        return 1


def _audio_streams(path: Path) -> int:
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=index", "-of", "csv=p=0", str(path),
        ], capture_output=True, text=True, timeout=30, creationflags=_HIDDEN_PROCESS)
        return len([line for line in result.stdout.splitlines() if line.strip()])
    except (OSError, subprocess.SubprocessError):
        return 0


def safe_video_path(raw: str) -> Path:
    candidate = resolve_media_source(raw)
    if candidate.parent not in {VIDEO_DIR.resolve(), CLIPS_DIR.resolve()} or candidate.suffix.lower() not in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=403, detail="Arquivo fora das pastas de vídeo")
    if not candidate.is_file(): raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    return candidate


def media_version(source: Path) -> str:
    """Carimbo que muda quando o arquivo muda.

    As URLs de mídia carregam o caminho, que o corte não altera — ele reescreve
    o arquivo no lugar. Sem este carimbo o navegador continua servindo do cache
    as faixas de bytes do vídeo *antigo* por uma hora, e o player cola pedaços
    de duas codificações diferentes: a imagem nova com o áudio velho.
    """
    try:
        stats = source.stat()
    except OSError:
        return "0"
    return f"{stats.st_mtime_ns}-{stats.st_size}"


def media_url(source_key: str, source: Path, endpoint: str = "video", **extra) -> str:
    query = "".join(f"&{name}={value}" for name, value in extra.items())
    return (f"/api/{endpoint}?path={urllib.parse.quote(source_key, safe='')}"
            f"{query}&v={media_version(source)}")


def video_thumbnail_cache_path(source: Path) -> Path:
    identity = media_source_key(source).encode("utf-8", errors="surrogatepass")
    return VIDEO_THUMBNAIL_DIR / f"{hashlib.sha256(identity).hexdigest()}.jpg"


def migrate_legacy_cache_file(destination: Path, legacy_directory: Path) -> None:
    legacy = legacy_directory / destination.name
    if destination.exists() or not legacy.is_file():
        return
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(legacy), str(destination))
    except OSError:
        pass


def migrate_legacy_media_caches() -> None:
    """Move caches antigos do perfil para a raiz de armazenamento selecionada."""
    for legacy, destination in (
        (LEGACY_VIDEO_THUMBNAIL_DIR, VIDEO_THUMBNAIL_DIR),
        (LEGACY_VIDEO_AUDIO_TRACK_DIR, VIDEO_AUDIO_TRACK_DIR),
    ):
        if not legacy.is_dir() or legacy.resolve() == destination.resolve():
            continue
        destination.mkdir(parents=True, exist_ok=True)
        for source in legacy.iterdir():
            if not source.is_file():
                continue
            target = destination / source.name
            try:
                if target.exists():
                    source.unlink()
                else:
                    shutil.move(str(source), str(target))
            except OSError:
                continue
        try:
            legacy.rmdir()
        except OSError:
            pass


def ensure_video_thumbnail(source: Path) -> Path:
    """Extrai uma miniatura uma vez; chamadas simultâneas não disputam o HD."""
    destination = video_thumbnail_cache_path(source)
    migrate_legacy_cache_file(destination, LEGACY_VIDEO_THUMBNAIL_DIR)
    if destination.is_file() and destination.stat().st_mtime_ns >= source.stat().st_mtime_ns:
        return destination
    with _VIDEO_THUMBNAIL_LOCK:
        if destination.is_file() and destination.stat().st_mtime_ns >= source.stat().st_mtime_ns:
            return destination
        VIDEO_THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(".tmp.jpg")
        temporary.unlink(missing_ok=True)
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", "1",
            "-i", str(source), "-frames:v", "1",
            "-vf", "scale=640:-2:force_original_aspect_ratio=decrease",
            "-q:v", "4", "-y", str(temporary),
        ]
        result = run(command, timeout=60)
        if result.returncode != 0 or not temporary.is_file() or temporary.stat().st_size == 0:
            temporary.unlink(missing_ok=True)
            command[4:6] = []  # vídeos muito curtos podem não chegar a 1 segundo
            result = run(command, timeout=60)
        if result.returncode != 0 or not temporary.is_file() or temporary.stat().st_size == 0:
            temporary.unlink(missing_ok=True)
            raise HTTPException(status_code=503, detail="Não foi possível gerar a miniatura")
        os.replace(temporary, destination)
    return destination


def probe_video_audio_tracks(source: Path) -> list[dict]:
    """Lista os stems reproduzíveis, omitindo a mixagem geral do OBS."""
    result = run([
        "ffprobe", "-v", "error", "-select_streams", "a",
        "-show_entries", "stream=index,codec_name,channels", "-of", "json", str(source),
    ], timeout=30)
    if result.returncode != 0:
        return []
    try:
        streams = json.loads(result.stdout or "{}").get("streams", [])
    except json.JSONDecodeError:
        return []
    # O perfil do Lume grava 1=Mixagem, 2=Microfone, 3=Discord, 4=Sistema.
    # Arquivos importados com exatamente três faixas também podem ser mixados.
    if len(streams) >= 4:
        selected = list(enumerate(streams))[1:4]
        labels = ["Microfone", "Discord", "Sistema"]
    elif len(streams) == 3:
        selected = list(enumerate(streams))
        labels = ["Microfone", "Discord", "Sistema"]
    elif len(streams) > 1:
        selected = list(enumerate(streams))
        labels = [f"Faixa {index + 1}" for index in range(len(selected))]
    else:
        return []
    return [
        {
            "track": position,
            "stream_index": int(stream.get("index", position)),
            "label": labels[index],
            "codec": str(stream.get("codec_name", "")),
            "channels": int(stream.get("channels", 0) or 0),
        }
        for index, (position, stream) in enumerate(selected)
    ]


#: Contêiner do cache por codec de áudio. A extração usa ``-c:a copy`` para não
#: reencodar horas de gravação, e por isso o contêiner precisa aceitar o codec
#: de origem: a extensão ``.m4a`` seleciona o muxer ipod, que recusa Opus — o
#: padrão do gpu-screen-recorder em mp4/mkv. Com a extensão errada o ffmpeg nem
#: escrevia o cabeçalho, o job terminava em erro e o botão "Preparar faixas
#: independentes" não produzia nada.
VIDEO_AUDIO_TRACK_DEFAULT_CONTAINER = (".m4a", "audio/mp4")
VIDEO_AUDIO_TRACK_CONTAINERS = {
    "opus": (".opus", "audio/ogg"),
    "vorbis": (".ogg", "audio/ogg"),
    "flac": (".flac", "audio/flac"),
}
VIDEO_AUDIO_TRACK_SUFFIXES = (
    VIDEO_AUDIO_TRACK_DEFAULT_CONTAINER, *VIDEO_AUDIO_TRACK_CONTAINERS.values(),
)


def video_audio_track_container(codec: str) -> tuple[str, str]:
    """Extensão e mimetype que aceitam ``codec`` sem reencodar."""
    return VIDEO_AUDIO_TRACK_CONTAINERS.get(
        str(codec or "").strip().lower(), VIDEO_AUDIO_TRACK_DEFAULT_CONTAINER)


def video_audio_track_cache_path(source: Path, track: int, suffix: str = ".m4a") -> Path:
    identity = f"{media_source_key(source)}\0{track}".encode("utf-8", errors="surrogatepass")
    return VIDEO_AUDIO_TRACK_DIR / f"{hashlib.sha256(identity).hexdigest()}{suffix}"


def video_audio_track_destination(source: Path, item: dict) -> Path:
    suffix, _ = video_audio_track_container(item.get("codec", ""))
    return video_audio_track_cache_path(source, int(item["track"]), suffix)


def resolve_video_audio_track_cache(source: Path, track: int) -> tuple[Path, str] | None:
    """Acha o stem já preparado sem reabrir o vídeo só para descobrir o codec."""
    for suffix, media_type in VIDEO_AUDIO_TRACK_SUFFIXES:
        destination = video_audio_track_cache_path(source, track, suffix)
        if suffix == VIDEO_AUDIO_TRACK_DEFAULT_CONTAINER[0]:
            migrate_legacy_cache_file(destination, LEGACY_VIDEO_AUDIO_TRACK_DIR)
        if destination.is_file():
            return destination, media_type
    return None


def video_audio_tracks_cached(source: Path, tracks: list[dict]) -> bool:
    destinations = [video_audio_track_destination(source, item) for item in tracks]
    for destination in destinations:
        migrate_legacy_cache_file(destination, LEGACY_VIDEO_AUDIO_TRACK_DIR)
    return bool(destinations) and all(
        path.is_file() and path.stat().st_mtime_ns >= source.stat().st_mtime_ns
        for path in destinations
    )


class _VideoAudioTrackJob:
    """Remuxa stems fora da requisição HTTP e permite interromper a leitura pesada."""

    def __init__(self, source: Path, tracks: list[dict], duration: float = 0.0):
        self.id = secrets.token_urlsafe(12)
        self.source = source
        self.tracks = tracks
        self.duration = duration
        self.status = "preparing"
        self.error = ""
        self.cancelled = threading.Event()
        self._process_lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._thread = threading.Thread(target=self._run, name=f"video-audio-{self.id}", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def cancel(self) -> None:
        self.cancelled.set()
        with self._process_lock:
            process = self._process
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
        if threading.current_thread() is not self._thread:
            self._thread.join(timeout=5)

    @staticmethod
    def _stop_process(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
                process.wait(timeout=2)
            except OSError:
                pass
            except subprocess.TimeoutExpired:
                pass

    def _run(self) -> None:
        destinations = [video_audio_track_destination(self.source, item) for item in self.tracks]
        temporary = [path.with_name(f"{path.stem}.{self.id}.tmp{path.suffix}") for path in destinations]
        acquired = False
        process: subprocess.Popen[str] | None = None
        try:
            while not self.cancelled.is_set():
                acquired = _VIDEO_AUDIO_TRACK_LOCK.acquire(timeout=0.2)
                if acquired:
                    break
            if not acquired or self.cancelled.is_set():
                self.status = "cancelled"
                return
            if video_audio_tracks_cached(self.source, self.tracks):
                self.status = "ready"
                return
            VIDEO_AUDIO_TRACK_DIR.mkdir(parents=True, exist_ok=True)
            for path in temporary:
                path.unlink(missing_ok=True)
            command = ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y", "-i", str(self.source)]
            for item, path in zip(self.tracks, temporary):
                command += ["-map", f"0:a:{int(item['track'])}", "-vn", "-c:a", "copy"]
                if path.suffix == VIDEO_AUDIO_TRACK_DEFAULT_CONTAINER[0]:
                    command += ["-movflags", "+faststart"]
                command.append(str(path))
            process = subprocess.Popen(
                command, text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                env=os.environ.copy(), creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            with self._process_lock:
                self._process = process
            timeout_seconds = max(300.0, min(21600.0, self.duration + 300.0))
            deadline = time.monotonic() + timeout_seconds
            while process.poll() is None and not self.cancelled.wait(0.1):
                if time.monotonic() >= deadline:
                    self.error = "Tempo esgotado ao preparar as faixas de áudio"
                    self.cancelled.set()
                    break
            if self.cancelled.is_set():
                self._stop_process(process)
                self.status = "cancelled" if not self.error else "error"
                return
            process.wait()
            if process.returncode != 0 or any(not path.is_file() or path.stat().st_size == 0 for path in temporary):
                self.error = "Não foi possível preparar as faixas de áudio"
                self.status = "error"
                return
            for source_path, destination in zip(temporary, destinations):
                os.replace(source_path, destination)
            self.status = "ready"
        except (OSError, subprocess.SubprocessError) as exc:
            self.error = str(exc)
            self.status = "error"
        finally:
            if process is not None and process.poll() is None:
                self._stop_process(process)
            with self._process_lock:
                self._process = None
            for path in temporary:
                try:
                    unlink_with_retry(path)
                except OSError:
                    # Um antivírus pode reter o temporário por mais alguns segundos.
                    # Ele não é reutilizado e será removido pela limpeza do cache.
                    pass
            if acquired:
                _VIDEO_AUDIO_TRACK_LOCK.release()


def cancel_video_audio_track_jobs() -> None:
    with _VIDEO_AUDIO_TRACK_JOBS_LOCK:
        jobs = list(_VIDEO_AUDIO_TRACK_JOBS.values())
        _VIDEO_AUDIO_TRACK_JOBS.clear()
    for job in jobs:
        job.cancel()


def cancel_video_audio_track_job(source: Path) -> bool:
    key = str(source)
    with _VIDEO_AUDIO_TRACK_JOBS_LOCK:
        job = _VIDEO_AUDIO_TRACK_JOBS.pop(key, None)
    if job is None:
        return False
    job.cancel()
    return True


def delete_video_caches(source: Path) -> None:
    paths = [
        video_thumbnail_cache_path(source),
        LEGACY_VIDEO_THUMBNAIL_DIR / video_thumbnail_cache_path(source).name,
    ]
    # Todas as versões leves deste vídeo, em qualquer teto: depois de um corte, a
    # que já existe mostra o trecho antigo com o nome do novo.
    paths.extend(sharing.SHARE_CACHE_DIR.glob(sharing.share_cache_glob(source)))
    for track in range(32):
        for suffix, _ in VIDEO_AUDIO_TRACK_SUFFIXES:
            destination = video_audio_track_cache_path(source, track, suffix)
            paths.extend((destination, LEGACY_VIDEO_AUDIO_TRACK_DIR / destination.name))
            paths.extend(destination.parent.glob(f"{destination.stem}.*.tmp{suffix}"))
    for path in paths:
        try:
            unlink_with_retry(path, attempts=5)
        except PermissionError:
            # Cache derivado: se ainda estiver aberto pelo navegador, pode sobrar
            # até uma limpeza futura sem impedir a exclusão do vídeo/análise.
            pass


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": mode.modo_atual(),
            "time": datetime.now().astimezone().isoformat()}


@app.get("/api/updates")
def update_status(force: bool = False) -> dict:
    from . import updater
    return updater.check(force)


class UpdateRequest(BaseModel):
    version: str = Field(pattern=r"^[0-9a-f]{40}$")


@app.post("/api/updates/prepare")
def prepare_update(settings: UpdateRequest) -> dict:
    from . import updater
    if not mode.e_lumini():
        raise HTTPException(status_code=409, detail="A atualização pelo app está disponível no Lumini.")
    if selective_video_status().get("recording"):
        raise HTTPException(status_code=409, detail="Saia do jogo e espere a gravação terminar antes de atualizar.")
    try:
        return updater.prepare(settings.version)
    except (updater.UpdateError, OSError, subprocess.SubprocessError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/updates/install")
def install_update_now() -> dict:
    from . import updater
    if not mode.e_lumini():
        raise HTTPException(status_code=409, detail="A atualização pelo app está disponível no Lumini.")
    if selective_video_status().get("recording"):
        raise HTTPException(status_code=409, detail="Saia do jogo e espere a gravação terminar antes de atualizar.")
    try:
        return updater.install_now()
    except (updater.UpdateError, OSError, subprocess.SubprocessError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/updates/cancel")
def cancel_update() -> dict:
    from . import updater
    try:
        return updater.cancel()
    except updater.UpdateError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.get("/api/status")
def status() -> dict:
    idle = get_manager().idle_state()
    audio = unit_state("captura-dia-audio.service")
    screen = unit_state("captura-dia-tela.service")
    target = unit_state("captura-dia.target")
    video = selective_video_status()
    audio_files = directory_stats(AUDIO_DIR, ".wav")
    screen_files = directory_stats(SCREEN_DIR, ".png")
    usage = shutil.disk_usage(MEDIA_ROOT if MEDIA_ROOT.exists() else HOME)
    return {
        "mode": mode.modo_atual(),
        "capturing": bool(audio["active"] and screen["active"]),
        "target": target,
        "audio": audio,
        "screen": screen,
        "video": video,
        "idle": idle,
        "capture_paused_by_idle": bool(idle["captures_paused"]),
        "capture_paused_by_video": bool(video["pausing_captures"]),
        "files": {"audio": audio_files, "screen": screen_files},
        "storage": {
            "bytes": int(audio_files["bytes"]) + int(screen_files["bytes"]),
            "disk_free": usage.free,
        },
        "settings": get_screen_settings(),
    }


def selective_video_status() -> dict:
    """Estado operacional do gravador, separado da mera configuração ativa."""
    config = parse_shell_config(VIDEO_CONFIG)
    service = unit_state("captura-dia-video.service")
    flag = video_activity_flag()
    pause_flag = video_recording_flag()
    try:
        recording = time.time() - flag.stat().st_mtime <= VIDEO_ACTIVITY_FRESH_SECONDS
    except OSError:
        recording = False
    window = ""
    started_at: float | None = None
    focus_grace_remaining: float | None = None
    mode = config.get("VIDEO_CAPTURE_MODE", "continuous").lower()
    if recording:
        try:
            raw = flag.read_text(encoding="utf-8").strip()
            try:
                activity = json.loads(raw)
            except json.JSONDecodeError:
                activity = None
            if isinstance(activity, dict):
                window = str(activity.get("window") or "")
                active_mode = str(activity.get("mode") or "").lower()
                if active_mode in {"continuous", "clips"}:
                    mode = active_mode
                value = activity.get("started_at")
                if isinstance(value, (int, float)) and value > 0:
                    started_at = float(value)
                deadline = activity.get("focus_grace_deadline")
                if isinstance(deadline, (int, float)) and deadline > 0:
                    focus_grace_remaining = max(0.0, float(deadline) - time.time())
            else:
                window = raw
                started_at = flag.stat().st_mtime
        except OSError:
            recording = False
    if mode not in {"continuous", "clips"}:
        mode = "continuous"
    return {
        "enabled": config.get("VIDEO_ENABLED", "false").lower() == "true",
        "service_active": bool(service.get("active")),
        "active_state": str(service.get("active_state", "unknown")),
        "recording": recording,
        "mode": mode,
        "window": window,
        "started_at": started_at,
        # Segundos até a sessão encerrar por falta de foco; ``None`` com o jogo
        # em foco. É a janela em que a interface oferece "Forçar encerramento".
        "focus_grace_remaining": focus_grace_remaining,
        "pausing_captures": recording and pause_flag.is_file(),
        "pause_other_captures": config.get("PAUSE_OTHER_CAPTURES", "true").lower() == "true",
    }


@app.post("/api/video/end-session")
def end_video_session() -> dict:
    """Encerra agora a sessão que já está contando para parar fora do jogo.

    Quem sai do jogo e quer as capturas de volta não precisa esperar a folga
    inteira. O pedido vira um arquivo que o laço de vídeo consome na volta
    seguinte — o mesmo caminho do encerramento por prazo vencido, com o arquivo
    finalizado do mesmo jeito.
    """
    video = selective_video_status()
    if not video["recording"] or video["focus_grace_remaining"] is None:
        raise HTTPException(status_code=409,
                            detail="Só dá para forçar o encerramento durante a contagem fora do jogo")
    flag = video_end_request_flag()
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.touch()
    return video


@app.post("/api/capture/{action}")
def capture_action(action: Literal["pause", "resume"]) -> dict:
    """Pausar e retomar a captura, de um jeito que sobreviva ao reboot.

    Só parar a unit valia até o próximo login: ela continuava habilitada e o
    systemd a subia de novo no boot seguinte, como se a pausa nunca tivesse
    existido. Quem guarda essa escolha é o estado de habilitação — é o mesmo
    que o supervisor do Windows já persistia em ``_remember``. O ``--now``
    mantém o efeito imediato de antes.
    """
    verb = "disable" if action == "pause" else "enable"
    units = ["captura-dia-audio.service", "captura-dia-tela.service"]
    result = service_action(verb, units, timeout=30, now=True)
    if result.returncode != 0:
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao controlar a captura")
    return {"ok": True, "action": action}


@app.get("/api/settings/screen", response_model=ScreenSettings)
def get_screen_settings() -> ScreenSettings:
    config = parse_shell_config(SCREEN_CONFIG)
    return ScreenSettings(
        capture_mode=config.get("CAPTURE_MODE", "interval"),
        interval_seconds=int(config.get("INTERVAL_SECONDS", "20")),
        change_poll_seconds=int(config.get("CHANGE_POLL_SECONDS", "5")),
        change_threshold_percent=float(config.get("CHANGE_THRESHOLD_PERCENT", "3")),
        change_max_interval_seconds=int(config.get("CHANGE_MAX_INTERVAL_SECONDS", "300")),
        max_geometry=config.get("MAX_GEOMETRY", "1920x1080>"),
        split_monitors=config.get("SPLIT_MONITORS", "true").lower() == "true",
        active_monitor_only=config.get("ACTIVE_MONITOR_ONLY", "true").lower() == "true",
        privacy_fail_closed=config.get("PRIVACY_FAIL_CLOSED", "true").lower() == "true",
    )


@app.put("/api/settings/screen")
def update_screen_settings(settings: ScreenSettings, background_tasks: BackgroundTasks) -> dict:
    if settings.max_geometry and not re.fullmatch(r"\d{2,5}x\d{2,5}>?", settings.max_geometry):
        raise HTTPException(status_code=422, detail="Resolução deve usar o formato 1920x1080>")
    content = f'''# Gerenciado pela interface Lume.
CAPTURE_MODE={settings.capture_mode}
INTERVAL_SECONDS={settings.interval_seconds}
CHANGE_POLL_SECONDS={settings.change_poll_seconds}
CHANGE_THRESHOLD_PERCENT={settings.change_threshold_percent:g}
CHANGE_MAX_INTERVAL_SECONDS={settings.change_max_interval_seconds}
CAPTURE_ROOT="$HOME/captura-dia/telas"
BACKEND=auto
MAX_GEOMETRY="{settings.max_geometry}"
OUTPUTS=""
SPLIT_MONITORS={'true' if settings.split_monitors else 'false'}
ACTIVE_MONITOR_ONLY={'true' if settings.active_monitor_only else 'false'}
PRIVACY_FAIL_CLOSED={'true' if settings.privacy_fail_closed else 'false'}
'''
    changed = atomic_write_if_changed(SCREEN_CONFIG, content)
    if changed:
        background_tasks.add_task(_restart_screen_runtime)
    return {"ok": True, "settings": settings, "restart_pending": changed}


@app.get("/api/settings/audio", response_model=AudioSettings)
def get_audio_settings() -> AudioSettings:
    config = parse_shell_config(AUDIO_CONFIG)
    return AudioSettings(
        mic_denoise_enabled=config.get("MIC_DENOISE_ENABLED", "true").lower() == "true",
        mic_gate_threshold_db=float(config.get("MIC_GATE_THRESHOLD_DB", "-45")),
    )


@app.put("/api/settings/audio")
def update_audio_settings(settings: AudioSettings, background_tasks: BackgroundTasks) -> dict:
    content = f'''# Gerenciado pela interface Lume.
MIC_DENOISE_ENABLED={'true' if settings.mic_denoise_enabled else 'false'}
MIC_GATE_THRESHOLD_DB={settings.mic_gate_threshold_db:g}
'''
    changed = atomic_write_if_changed(AUDIO_CONFIG, content)
    if changed:
        background_tasks.add_task(_restart_audio_runtime)
    return {"ok": True, "settings": settings, "restart_pending": changed}


@app.get("/api/settings/sensitive", response_model=SensitiveWindows)
def get_sensitive_windows() -> SensitiveWindows:
    patterns = []
    if SENSITIVE_FILE.exists():
        patterns = [
            line.strip()
            for line in SENSITIVE_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
    return SensitiveWindows(patterns=patterns)


@app.put("/api/settings/sensitive")
def update_sensitive_windows(payload: SensitiveWindows) -> dict:
    clean: list[str] = []
    for pattern in payload.patterns:
        value = pattern.strip()
        if not value:
            continue
        if len(value) > 200:
            raise HTTPException(status_code=422, detail="Uma expressão excede 200 caracteres")
        try:
            re.compile(value, re.IGNORECASE)
        except re.error as exc:
            raise HTTPException(status_code=422, detail=f"Regex inválida: {value}: {exc}") from exc
        clean.append(value)
    atomic_write(SENSITIVE_FILE, "# Gerenciado pela interface Lume.\n" + "\n".join(clean) + "\n")
    return {"ok": True, "patterns": clean}


def privacy_decision() -> tuple[str, str | None]:
    """Janela ativa e o motivo para não capturar, se houver.

    A mesma regra nos dois sistemas: janela impossível de consultar com
    ``PRIVACY_FAIL_CLOSED`` significa não capturar, e uma janela que casa com a
    lista de sensíveis também.
    """
    backend = get_backend()
    window = backend.active_window()
    if window is None:
        if get_screen_settings().privacy_fail_closed:
            return "", "janela ativa indisponível (fail closed)"
        return "", None
    pattern = matched_sensitive_pattern(window, SENSITIVE_FILE)
    return window, f"janela sensível ({pattern})" if pattern else None


def capture_frames(dest_dir: Path) -> list[Path]:
    """Captura um conjunto de frames com a configuração atual."""
    settings = get_screen_settings()
    config = ScreenConfig(
        capture_root=dest_dir,
        max_geometry=settings.max_geometry,
        split_monitors=settings.split_monitors,
        active_monitor_only=settings.active_monitor_only,
        privacy_fail_closed=settings.privacy_fail_closed,
    )
    window, _ = privacy_decision()
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return get_backend().grab_frame(dest_dir, stamp, config, window)


@app.post("/api/test/screen")
def test_screen(save: bool = Query(default=True)) -> dict:
    _window, skip = privacy_decision()
    if skip:
        return {"ok": True, "captured": False, "privacy_skip": True, "message": skip}
    if not save:
        return {"ok": True, "captured": False, "privacy_skip": False, "paths": []}
    paths = capture_frames(SCREEN_DIR)
    if not paths:
        raise HTTPException(status_code=503, detail="Captura falhou")
    return {"ok": True, "captured": True, "privacy_skip": False, "paths": [str(p) for p in paths]}


SCREEN_CHANGE_TEST_ROOT = Path(tempfile.gettempdir()) / "lume-screen-change-tests"


def capture_change_test_frames(directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    _window, skip = privacy_decision()
    if skip:
        raise HTTPException(status_code=409, detail=f"Captura bloqueada pela privacidade: {skip}")
    frames = capture_frames(directory)
    if not frames:
        raise HTTPException(status_code=503, detail="A captura de teste não produziu imagens")
    return frames


def screen_change_percent(before: Path, after: Path) -> float:
    percent = compare_images(before, after)
    if percent is None:
        raise HTTPException(status_code=503, detail="Falha ao comparar as capturas")
    return percent


@app.post("/api/test/screen-change/start")
def start_screen_change_test(payload: ScreenChangeTest) -> dict:
    token = secrets.token_urlsafe(18)
    directory = SCREEN_CHANGE_TEST_ROOT / token
    frames = capture_change_test_frames(directory / "before")
    return {"ok": True, "token": token, "frames": len(frames), "threshold_percent": payload.threshold_percent}


@app.post("/api/test/screen-change/compare")
def compare_screen_change_test(payload: ScreenChangeTest) -> dict:
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,100}", payload.token):
        raise HTTPException(status_code=422, detail="Teste inválido ou expirado")
    directory = SCREEN_CHANGE_TEST_ROOT / payload.token
    before = sorted((directory / "before").glob("*.png"))
    if not before:
        raise HTTPException(status_code=404, detail="Referência do teste não encontrada; inicie um novo teste")
    try:
        after = capture_change_test_frames(directory / "after")
        changes = [screen_change_percent(old, new) for old, new in zip(before, after)]
        if len(before) != len(after):
            changes.append(100.0)
        measured = max(changes, default=100.0)
        return {
            "ok": True, "change_percent": measured, "threshold_percent": payload.threshold_percent,
            "would_capture": measured >= payload.threshold_percent,
            "monitors": [{"index": index, "change_percent": value} for index, value in enumerate(changes)],
        }
    finally:
        shutil.rmtree(directory, ignore_errors=True)


@app.post("/api/test/video-window")
def test_video_window(payload: VideoWindowTest) -> dict:
    compiled: list[tuple[str, str, re.Pattern[str]]] = []
    for value in payload.patterns:
        pattern = value.strip()
        if not pattern:
            continue
        field = "exe"
        expression = pattern
        for prefix in ("exe:", "title:", "class:"):
            if pattern.lower().startswith(prefix):
                field, expression = prefix[:-1], pattern[len(prefix):].strip()
                break
        try:
            compiled.append((pattern, field, re.compile(expression, re.IGNORECASE)))
        except re.error as exc:
            raise HTTPException(status_code=422, detail=f"Regex inválida: {pattern}: {exc}") from exc
    backend = get_backend()
    info = backend.active_window()
    if not info:
        problem = backend.active_window_problem()
        raise HTTPException(status_code=503, detail=f"Não foi possível consultar a janela ativa. {problem}".strip())
    # O segundo campo é o executável no Windows e a classe da janela no Linux —
    # nos dois é a identidade estável do app, e é nela que uma regra sem prefixo
    # procura, igual ao gravador real. A separação é pelo último " | " porque o
    # título pode conter a sequência: "mrekk | osu! ... - YouTube | firefox" é
    # um vídeo no navegador, não o jogo.
    title, separator, identity = info.rpartition(" | ")
    if not separator:
        title, identity = "", info
    title, identity = title.strip(), identity.strip()
    window_class = identity if backend.name != "windows" else ""
    fields = {"title": title, "exe": identity, "class": window_class}
    matched_pattern = next((source for source, field, regex in compiled if regex.search(fields[field])), "")
    try:
        monitor_resolution = backend.active_monitor_resolution()
    except Exception:
        monitor_resolution = None
    return {
        "ok": True, "window_id": "", "title": title, "window_class": identity,
        "executable": identity, "monitor_resolution": monitor_resolution,
        "info": info, "matched": bool(matched_pattern), "matched_pattern": matched_pattern,
    }


@app.post("/api/test/audio")
def test_audio(seconds: int = Query(default=5, ge=2, le=15)) -> dict:
    with tempfile.TemporaryDirectory(prefix="lume-audio-") as directory:
        outdir = Path(directory)
        # Mesma fonte que a gravação contínua usa, seja RecordBus ou WASAPI.
        config = AudioConfig(outdir=outdir, segment_seconds=max(seconds, 60),
                             duration_seconds=seconds)
        capture = run(get_backend().audio_record_argv(config), timeout=seconds + 30)
        samples = sorted(outdir.glob("audio-*.wav"))
        if not samples:
            raise HTTPException(status_code=503, detail=capture.stderr.strip() or "Gravação de teste falhou")
        sample = samples[0]
        probe = run([
            "ffprobe", "-v", "error", "-show_entries", "stream=codec_name,sample_rate,channels,duration",
            "-of", "default=noprint_wrappers=1", str(sample),
        ])
        volume = run([
            "ffmpeg", "-hide_banner", "-nostdin", "-i", str(sample),
            "-af", "volumedetect", "-f", "null", "-",
        ])
        values = dict(line.split("=", 1) for line in probe.stdout.splitlines() if "=" in line)
        mean = re.search(r"mean_volume:\s*([^\s]+) dB", volume.stderr)
        maximum = re.search(r"max_volume:\s*([^\s]+) dB", volume.stderr)
        return {
            "ok": True,
            "format": values,
            "mean_db": mean.group(1) if mean else None,
            "max_db": maximum.group(1) if maximum else None,
            "silent": not maximum or maximum.group(1) == "-inf",
        }


@app.get("/api/settings/audio/mic-level")
def mic_level(ms: int = Query(default=300, ge=100, le=1500)) -> dict:
    """Pico do microfone cru (sem denoise/portão) numa janela curta.

    A interface faz polling nisto enquanto o teste de calibração está aberto,
    para desenhar a barra ao vivo ao lado do controle de volume mínimo.
    """
    seconds = ms / 1000
    argv = get_backend().mic_level_argv(seconds)
    if argv is None:
        raise HTTPException(status_code=501, detail="Medição ao vivo do microfone ainda não é suportada neste sistema.")
    result = run(argv, timeout=seconds + 10)
    maximum = re.search(r"max_volume:\s*([^\s]+) dB", result.stderr)
    silent = not maximum or maximum.group(1) == "-inf"
    return {"ok": True, "peak_db": None if silent else float(maximum.group(1)), "silent": silent}


@app.get("/api/screenshot")
def screenshot(path: str) -> FileResponse:
    return FileResponse(safe_screen_path(path), media_type="image/png")


@app.get("/api/audio")
def audio_file(path: str, track: Literal["mix", "microphone", "discord", "system", "original"] = "mix") -> Response:
    source = safe_audio_path(path)
    try:
        with wave.open(str(source), "rb") as wav:
            channels = wav.getnchannels()
    except (wave.Error, OSError):
        channels = 1
    if channels < 2 or track == "original":
        return FileResponse(source, media_type="audio/wav", filename=Path(path).name)
    expressions = {
        2: {"mix": "pan=mono|c0=0.5*c0+0.5*c1", "microphone": "pan=mono|c0=c0", "system": "pan=mono|c0=c1"},
        3: {"mix": "pan=mono|c0=0.333*c0+0.333*c1+0.333*c2", "microphone": "pan=mono|c0=c0", "discord": "pan=mono|c0=c1", "system": "pan=mono|c0=c2"},
    }
    expression = expressions.get(channels, expressions[2]).get(track)
    if not expression:
        raise HTTPException(status_code=422, detail="Faixa indisponível neste áudio")
    result = subprocess.run([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(source),
        "-af", expression, "-ar", "16000", "-c:a", "pcm_s16le", "-f", "wav", "pipe:1",
    ], capture_output=True, timeout=180, creationflags=_HIDDEN_PROCESS)
    if result.returncode != 0 or not result.stdout:
        raise HTTPException(status_code=503, detail="Não foi possível preparar a faixa de áudio")
    return Response(content=result.stdout, media_type="audio/wav", headers={"Cache-Control": "private, max-age=3600"})


VIDEO_STREAM_CHUNK_BYTES = 8 * 1024 * 1024


def bounded_video_range(range_header: str, size: int, limit: int = VIDEO_STREAM_CHUNK_BYTES) -> tuple[int, int]:
    """Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro."""
    match = re.fullmatch(r"bytes=(\d*)-(\d*)", range_header.strip(), flags=re.I) if range_header else None
    if not match:
        return 0, min(size - 1, limit - 1)
    first, last = match.groups()
    if not first and last:
        length = min(int(last), size, limit)
        return max(0, size - length), size - 1
    start = int(first or 0)
    requested_end = int(last) if last else size - 1
    return start, min(requested_end, size - 1, start + limit - 1)


@app.get("/api/video")
def video_file(request: Request, path: str) -> StreamingResponse:
    source = safe_video_path(path)
    size = source.stat().st_size
    if size <= 0:
        raise HTTPException(status_code=404, detail="Vídeo vazio")
    start, end = bounded_video_range(request.headers.get("range", ""), size)
    if start < 0 or start >= size or end < start:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{size}"})

    def body():
        remaining = end - start + 1
        with source.open("rb") as handle:
            handle.seek(start)
            while remaining > 0:
                chunk = handle.read(min(256 * 1024, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    media_type = mimetypes.guess_type(source.name)[0] or "application/octet-stream"
    return StreamingResponse(body(), status_code=206, media_type=media_type, headers={
        "Accept-Ranges": "bytes",
        "Content-Range": f"bytes {start}-{end}/{size}",
        "Content-Length": str(end - start + 1),
        "Cache-Control": "private, max-age=3600",
        "Content-Disposition": f'inline; filename="{source.name.replace(chr(34), "")}"',
    })


@app.get("/api/video-download")
def download_video(path: str) -> FileResponse:
    """O mesmo arquivo, com o nome que a pessoa reconhece no seletor do Discord.

    Rota própria, e não um ``?download=1`` em ``/api/video``: aquela existe para
    o ``<video>`` e por isso corta todo Range em 8 MB, responde sempre 206 e
    guarda uma hora de cache. Download quer o oposto — o arquivo inteiro, de uma
    vez, e sem cache sobre um nome que muda quando a IA titula o clipe.

    O ``FileResponse`` monta o ``Content-Disposition`` (inclusive o
    ``filename*=utf-8''`` de nomes com acento) e trata Range sozinho; escrever
    esse header à mão só acrescentaria uma forma nova de errá-lo.
    """
    source = safe_video_path(path)
    return FileResponse(
        source, filename=sharing.download_filename(path, source),
        media_type=mimetypes.guess_type(source.name)[0] or "application/octet-stream",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/share/light")
def light_version_state(path: str, limit_mb: int | None = None) -> dict:
    """Consulta pura: diz se a versão leve existe, está saindo ou não cabe."""
    source = safe_video_path(path)
    try:
        return sharing.light_state(path, source, limit_mb)
    except sharing.SharingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/share/light")
def start_light_version(path: str, limit_mb: int | None = None) -> dict:
    source = safe_video_path(path)
    try:
        return sharing.light_state(path, source, limit_mb, start=True)
    except sharing.SharingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete("/api/share/light")
def cancel_light_version(path: str) -> dict:
    source = safe_video_path(path)
    return {"ok": True, "cancelled": sharing.cancel_light_jobs(source)}


@app.get("/api/video-light")
def light_video_file(path: str, limit_mb: int | None = None) -> FileResponse:
    """Baixa a versão leve pronta; 409 enquanto ela não existir.

    Não gera nada aqui: um GET que dispara meio minuto de ffmpeg viraria
    timeout no navegador, e é o ``POST`` que existe para isso.
    """
    source = safe_video_path(path)
    try:
        limit = sharing.normalized_limit(limit_mb)
        ready = sharing.share_cached(source, limit)
    except sharing.SharingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if ready is None:
        raise HTTPException(status_code=409, detail="A versão leve ainda não está pronta")
    return FileResponse(
        ready, filename=sharing.light_filename(path, source, limit),
        media_type="video/mp4", headers={"Cache-Control": "no-store"},
    )


@app.get("/api/share/upload")
def upload_state(path: str) -> dict:
    """Andamento do envio e os links que este clipe já ganhou."""
    safe_video_path(path)
    initialize()
    return sharing.upload_state(path)


@app.post("/api/share/upload")
def start_upload(payload: ShareUploadRequest) -> dict:
    """Publica o clipe num host grátis. Exige confirmação explícita."""
    source = safe_video_path(payload.path)
    initialize()
    try:
        return sharing.start_upload(
            payload.path, source, use_light=payload.use_light, limit_mb=payload.limit_mb,
            host_name=payload.host or None, expires=payload.expires or sharing.DEFAULT_EXPIRES,
            confirmed=payload.confirm_public_upload,
        )
    except sharing.SharingError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete("/api/share/upload")
def cancel_upload(path: str) -> dict:
    safe_video_path(path)
    return {"ok": True, "cancelled": sharing.cancel_uploads(path)}


@app.delete("/api/share/links/{link_id}")
def forget_shared_link(link_id: int) -> dict:
    """Tira o link da lista. O arquivo continua no ar — o host é que o apaga."""
    initialize()
    if not sharing.forget_link(link_id):
        raise HTTPException(status_code=404, detail="Link não encontrado")
    return {"ok": True, "id": link_id, "unpublished": False}


@app.get("/api/video-audio-tracks")
def video_audio_tracks(path: str, prepare: bool = False) -> dict:
    source = safe_video_path(path)
    key = str(source)
    with _VIDEO_AUDIO_TRACK_JOBS_LOCK:
        job = _VIDEO_AUDIO_TRACK_JOBS.get(key)
    tracks = job.tracks if job is not None else probe_video_audio_tracks(source)
    if not tracks:
        return {"items": [], "status": "ready", "duration": 0.0}
    duration = job.duration if job is not None else probe_video_duration(source)
    if video_audio_tracks_cached(source, tracks):
        if job is not None:
            with _VIDEO_AUDIO_TRACK_JOBS_LOCK:
                if _VIDEO_AUDIO_TRACK_JOBS.get(key) is job:
                    _VIDEO_AUDIO_TRACK_JOBS.pop(key, None)
        return {
            "status": "ready",
            "duration": duration,
            "items": [
                {
                    **item,
                    "url": media_url(path, source, "video-audio-track", track=item["track"]),
                }
                for item in tracks
            ],
        }
    if job is None and duration >= 3600 and not prepare:
        return {"items": [], "status": "manual", "duration": duration}
    if job is None:
        job = _VideoAudioTrackJob(source, tracks, duration)
        with _VIDEO_AUDIO_TRACK_JOBS_LOCK:
            existing = _VIDEO_AUDIO_TRACK_JOBS.setdefault(key, job)
        if existing is job:
            job.start()
        else:
            job = existing
    return {
        "items": [],
        "status": "error" if job.status == "error" else "preparing",
        "job_id": job.id,
        "error": job.error,
        "duration": duration,
    }


@app.delete("/api/video-audio-tracks")
def cancel_video_audio_tracks(path: str, job_id: str) -> dict:
    source = safe_video_path(path)
    key = str(source)
    with _VIDEO_AUDIO_TRACK_JOBS_LOCK:
        job = _VIDEO_AUDIO_TRACK_JOBS.get(key)
    if job is None or job.id != job_id:
        return {"ok": True, "cancelled": False}
    return {"ok": True, "cancelled": cancel_video_audio_track_job(source)}


@app.get("/api/video-audio-track")
def video_audio_track(path: str, track: int = Query(ge=0, le=31)) -> FileResponse:
    source = safe_video_path(path)
    resolved = resolve_video_audio_track_cache(source, track)
    if resolved is None or resolved[0].stat().st_mtime_ns < source.stat().st_mtime_ns:
        raise HTTPException(status_code=409, detail="Faixas de áudio ainda estão sendo preparadas")
    destination, media_type = resolved
    return FileResponse(
        destination, media_type=media_type,
        headers={"Cache-Control": "private, max-age=86400"},
    )


class SteamGridDbKey(BaseModel):
    key: str = Field(default="", pattern=r"^[A-Za-z0-9]{0,128}$")


@app.get("/api/settings/steamgriddb")
def get_steamgriddb_settings() -> dict:
    # A chave nunca volta para a interface: o Lume pode estar aberto na rede.
    return {"configured": bool(game_icons.read_key())}


@app.put("/api/settings/steamgriddb")
def set_steamgriddb_settings(settings: SteamGridDbKey) -> dict:
    if settings.key and game_icons.verify_key(settings.key) is False:
        raise HTTPException(status_code=422, detail="O SteamGridDB recusou esta chave. Confira se ela foi copiada inteira.")
    game_icons.save_key(settings.key)
    return get_steamgriddb_settings()


@app.get("/api/game-icons")
def game_icon_lookup(names: list[str] = Query(default=[], max_length=100)) -> dict:
    found = game_icons.lookup([name[:120] for name in names])
    return {name: {"url": f"/api/game-icons/{entry['file']}", "kind": entry["kind"]} if entry else None
            for name, entry in found.items()}


@app.post("/api/game-icons/retry")
def game_icon_retry() -> dict:
    """Busca de novo, já, os jogos que ficaram sem ícone."""
    return {"ok": True, "retrying": game_icons.forget_missing()}


@app.get("/api/game-icons/{file_name}")
def game_icon_file(file_name: str) -> FileResponse:
    path = game_icons.cached_file(file_name)
    if path is None:
        raise HTTPException(status_code=404, detail="Ícone não encontrado")
    return FileResponse(path, headers={"Cache-Control": "private, max-age=604800"})


@app.get("/api/video-thumbnail")
def video_thumbnail(path: str) -> FileResponse:
    thumbnail = ensure_video_thumbnail(safe_video_path(path))
    return FileResponse(
        thumbnail, media_type="image/jpeg",
        headers={"Cache-Control": "private, max-age=86400"},
    )


@app.get("/api/videos")
def list_videos() -> dict:
    VIDEO_DIR.mkdir(parents=True, exist_ok=True); initialize()
    paths = sorted(
        (path for path in VIDEO_DIR.iterdir()
         if path.is_file() and path.suffix.lower() in VIDEO_EXTENSIONS
         and not path.name.endswith(".partial.mp4")),
        key=lambda item:item.stat().st_mtime, reverse=True,
    )
    with connect() as db:
        # Versões antigas chegaram a indexar o arquivo temporário enquanto o
        # gravador ainda escrevia. Ele nunca é mídia do usuário nem deve virar
        # uma entrada fantasma depois do rename para o nome final.
        db.execute("DELETE FROM video_segments WHERE source_path LIKE '%.partial.mp4'")
        known_paths={row["source_path"] for row in db.execute("SELECT source_path FROM video_segments")}
    for path in paths:
        source_key = media_source_key(path)
        if source_key not in known_paths:
            captured = video_recorded_at(path).isoformat()
            with connect() as db:
                db.execute("INSERT OR IGNORE INTO video_segments(source_path,captured_at,status) VALUES(?,?,'pending')", (source_key,captured))
    with connect() as db:
        affected_sessions: set[int] = set()
        for path in paths:
            video = db.execute(
                "SELECT id,session_id,session_detached FROM video_segments WHERE source_path=?",
                (media_source_key(path),),
            ).fetchone()
            video_id = video["id"]
            marker_file = path.with_suffix(path.suffix+".markers")
            if marker_file.is_file():
                existing = {round(float(row["offset_seconds"]),3) for row in db.execute("SELECT offset_seconds FROM video_markers WHERE video_id=?",(video_id,))}
                for raw in marker_file.read_text(encoding="utf-8").splitlines():
                    try: offset=max(0.0,float(raw.strip()))
                    except ValueError: continue
                    if round(offset,3) not in existing:
                        db.execute("INSERT INTO video_markers(video_id,offset_seconds) VALUES(?,?)",(video_id,offset));existing.add(round(offset,3))
            captured_session = captured_video_session(path)
            if captured_session and video["session_id"] is None and not video["session_detached"]:
                key, name = captured_session
                source = AUTO_VIDEO_SESSION_PREFIX + key
                session = db.execute("SELECT id FROM video_sessions WHERE source_folder=?", (source,)).fetchone()
                if session is None:
                    db.execute(
                        """INSERT INTO video_sessions(name,source_folder)
                           SELECT ?,? WHERE NOT EXISTS(
                             SELECT 1 FROM video_sessions WHERE source_folder=?
                           )""", (name, source, source))
                    session = db.execute(
                        "SELECT id FROM video_sessions WHERE source_folder=?", (source,)).fetchone()
                session_id = session["id"]
                db.execute("UPDATE video_segments SET session_id=? WHERE id=?", (session_id, video_id))
                affected_sessions.add(session_id)
        for session_id in affected_sessions:
            ordered = db.execute(
                "SELECT id FROM video_segments WHERE session_id=? ORDER BY captured_at,id", (session_id,)
            ).fetchall()
            for order, row in enumerate(ordered):
                db.execute("UPDATE video_segments SET sort_order=? WHERE id=?", (order, row["id"]))
        states={row["source_path"]:dict(row) for row in db.execute("SELECT * FROM video_segments")}
        markers_by_video: dict[int, list[dict]] = {}
        for marker in db.execute("SELECT * FROM video_markers ORDER BY offset_seconds,id"):
            markers_by_video.setdefault(marker["video_id"], []).append(dict(marker))
    items=[]
    available_sources: set[str] = set()
    for path in paths:
        source_key=media_source_key(path);state=states.get(source_key,{})
        available_sources.add(source_key)
        sidecar=path.with_suffix(path.suffix+".window")
        window=sidecar.read_text(encoding="utf-8").strip() if sidecar.exists() else ""
        game, game_source = video_game_label(source_key, state.get("app", ""))
        items.append({"id":state.get("id"),"session_id":state.get("session_id"),"name":path.name,"path":source_key,"bytes":path.stat().st_size,"modified_at":datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(),"captured_at":state.get("captured_at") or datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat(),"status":state.get("status","unindexed"),"stage":state.get("stage",""),"progress":state.get("progress",0),"trace":json.loads(state.get("trace_json","[]") or "[]"),"title":state.get("title","") ,"game":game,"game_source":game_source,"description":state.get("description",""),"context":state.get("context",""),"transcript":state.get("transcript",""),"transcript_segments":json.loads(state.get("transcript_segments_json","[]") or "[]"),"chapters":json.loads(state.get("chapters_json","[]") or "[]"),"markers":markers_by_video.get(state.get("id"), []),"error":state.get("error","") ,"preserved":bool(state.get("preserved",0)),"available":True,"url":media_url(source_key,path),"thumbnail_url":media_url(source_key,path,"video-thumbnail")})
        items[-1]["speakers"] = json.loads(state.get("speakers_json", "[]") or "[]")
        items[-1]["audio_events"] = json.loads(state.get("audio_events_json", "[]") or "[]")
    for source_key, state in states.items():
        if source_key in available_sources:
            continue
        items.append({
            "id": state.get("id"), "session_id": state.get("session_id"),
            "name": media_source_name(source_key), "path": source_key, "bytes": 0,
            "modified_at": state.get("processed_at") or state.get("created_at") or state.get("captured_at"),
            "captured_at": state.get("captured_at"), "status": state.get("status", "missing"),
            "stage": state.get("stage", ""), "progress": state.get("progress", 0),
            "trace": json.loads(state.get("trace_json", "[]") or "[]"),
            "title": state.get("title", ""), "game": state.get("app", ""), "game_source": "analysis",
            "description": state.get("description", ""), "context": state.get("context", ""),
            "transcript": state.get("transcript", ""),
            "transcript_segments": json.loads(state.get("transcript_segments_json", "[]") or "[]"),
            "speakers": json.loads(state.get("speakers_json", "[]") or "[]"),
            "audio_events": json.loads(state.get("audio_events_json", "[]") or "[]"),
            "chapters": json.loads(state.get("chapters_json", "[]") or "[]"),
            "markers": markers_by_video.get(state.get("id"), []), "error": state.get("error", ""),
            "preserved": bool(state.get("preserved", 0)),
            "available": False, "url": "",
        })
    return {"items":items,"total":len(items),"service":unit_state("captura-dia-video.service")}


@app.post("/api/videos/import")
async def import_video(request: Request, name: str = Query(min_length=1, max_length=255), session_id: int | None = None, sort_order: int = 0, client_modified_at: datetime | None = None) -> dict:
    extension = Path(name).suffix.lower()
    if extension not in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=422, detail=f"Formato não aceito. Use: {', '.join(sorted(VIDEO_EXTENSIONS))}")
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    clean_stem = re.sub(r"[^A-Za-z0-9À-ÿ._-]+", "_", Path(name).stem).strip("._")[:120] or "video"
    stamp = datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")
    destination = VIDEO_DIR / f"{stamp}_importado_{clean_stem}{extension}"
    counter = 1
    while destination.exists():
        destination = VIDEO_DIR / f"{stamp}_importado_{clean_stem}_{counter}{extension}"
        counter += 1
    partial = destination.with_name(f".{destination.name}.upload")
    free = shutil.disk_usage(VIDEO_DIR).free
    maximum = max(0, free - 1024 ** 3)
    written = 0
    try:
        with partial.open("xb") as handle:
            async for chunk in request.stream():
                written += len(chunk)
                if written > maximum:
                    raise HTTPException(status_code=507, detail="Espaço insuficiente; o Lume preserva 1 GB livre no disco")
                handle.write(chunk)
        if written == 0:
            raise HTTPException(status_code=422, detail="O arquivo enviado está vazio")
        probe = run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=codec_name", "-of", "default=nk=1:nw=1", str(partial),
        ], timeout=60)
        if probe.returncode != 0 or not probe.stdout.strip():
            raise HTTPException(status_code=422, detail="O arquivo não contém um vídeo válido")
        captured = video_recorded_at(partial, client_modified_at.astimezone() if client_modified_at else None).isoformat()
        partial.replace(destination)
        with connect() as db:
            db.execute(
                "INSERT INTO video_segments(source_path,captured_at,status,title,session_id,sort_order) VALUES(?,?,?,?,?,?)",
                (media_source_key(destination), captured, "pending", Path(name).stem[:300], session_id, sort_order),
            )
            if session_id is not None:
                ordered=db.execute("SELECT id FROM video_segments WHERE session_id=? ORDER BY captured_at,id",(session_id,)).fetchall()
                for order,row in enumerate(ordered): db.execute("UPDATE video_segments SET sort_order=? WHERE id=?",(order,row["id"]))
        return {"ok": True, "name": destination.name, "path": str(destination), "bytes": written, "captured_at": captured}
    finally:
        partial.unlink(missing_ok=True)


@app.post("/api/video-sessions")
def create_video_session(payload: VideoSessionCreate) -> dict:
    with connect() as db:
        cursor = db.execute(
            "INSERT INTO video_sessions(name,source_folder) VALUES(?,?)",
            (payload.name.strip(), payload.source_folder.strip()),
        )
    return {"ok": True, "id": cursor.lastrowid, "name": payload.name.strip()}

@app.post("/api/video-sessions/join")
def join_video_session(payload: VideoJoinRequest) -> dict:
    initialize()
    unique_ids = list(dict.fromkeys(payload.video_ids))
    session_ids = list(dict.fromkeys(payload.session_ids))
    with connect() as db:
        for raw_path in dict.fromkeys(payload.video_paths):
            path = safe_video_path(raw_path)
            source_key = media_source_key(path)
            db.execute("INSERT OR IGNORE INTO video_segments(source_path,captured_at,status) VALUES(?,?,'pending')", (source_key,datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat()))
            unique_ids.append(db.execute("SELECT id FROM video_segments WHERE source_path=?",(source_key,)).fetchone()["id"])
        unique_ids = list(dict.fromkeys(unique_ids))
        if len(unique_ids) + len(session_ids) < 2:
            raise HTTPException(status_code=422, detail="Selecione pelo menos dois vídeos ou sessões")

        sessions = []
        if session_ids:
            sessions = db.execute(
                f"SELECT * FROM video_sessions WHERE id IN ({','.join('?' for _ in session_ids)})",
                session_ids,
            ).fetchall()
            if len(sessions) != len(session_ids):
                raise HTTPException(status_code=404, detail="Uma ou mais sessões não foram encontradas")
            if any(row["status"] in ("queued", "processing") for row in sessions):
                raise HTTPException(status_code=409, detail="Uma das sessões está sendo analisada; cancele ou aguarde antes de unir")

        rows = []
        if unique_ids:
            rows = db.execute(
                f"SELECT id,session_id,captured_at,status FROM video_segments WHERE id IN ({','.join('?' for _ in unique_ids)})",
                unique_ids,
            ).fetchall()
            if len(rows) != len(unique_ids):
                raise HTTPException(status_code=404, detail="Um ou mais vídeos não foram encontrados")
            if any(row["session_id"] is not None and row["session_id"] not in session_ids for row in rows):
                raise HTTPException(status_code=409, detail="Um dos vídeos já pertence a uma sessão não selecionada")

        session_clips = []
        if session_ids:
            session_clips = db.execute(
                f"SELECT id,session_id,captured_at,status FROM video_segments WHERE session_id IN ({','.join('?' for _ in session_ids)})",
                session_ids,
            ).fetchall()
        clips_by_id = {row["id"]: row for row in [*rows, *session_clips]}
        if any(row["status"] in ("queued", "processing") for row in clips_by_id.values()):
            raise HTTPException(status_code=409, detail="Um dos clipes está sendo analisado; cancele ou aguarde antes de unir")
        if not clips_by_id:
            raise HTTPException(status_code=422, detail="As sessões selecionadas não possuem clipes")

        inherited_context = "\n\n".join(
            f"Contexto herdado de “{row['name']}”:\n{row['context'].strip()}"
            for row in sessions if row["context"].strip()
        )
        previous_summaries = "\n\n".join(
            f"Resumo anterior de “{row['name']}”:\n{row['summary'].strip()}"
            for row in sessions if row["summary"].strip()
        )
        source_folders = {row["source_folder"] for row in sessions if row["source_folder"]}
        source_folder = next(iter(source_folders)) if len(source_folders) == 1 else ""
        cursor = db.execute(
            "INSERT INTO video_sessions(name,source_folder,status,stage,summary,context) VALUES(?,?,'pending','Aguardando análise',?,?)",
            (payload.name.strip(), source_folder, previous_summaries, inherited_context),
        )
        session_id = cursor.lastrowid
        ordered_ids = [row["id"] for row in sorted(clips_by_id.values(),key=lambda row:(row["captured_at"],row["id"]))]
        for order, video_id in enumerate(ordered_ids):
            db.execute(
                "UPDATE video_segments SET session_id=?,sort_order=?,session_detached=0 WHERE id=?",
                (session_id, order, video_id),
            )
        if session_ids:
            db.execute(
                f"DELETE FROM video_sessions WHERE id IN ({','.join('?' for _ in session_ids)})",
                session_ids,
            )
    return {
        "ok": True, "id": session_id, "name": payload.name.strip(),
        "clips": len(ordered_ids), "merged_sessions": len(session_ids),
    }


@app.delete("/api/video-sessions/{session_id}/clips/{video_id}")
def detach_video_from_session(session_id: int, video_id: int) -> dict:
    """Retira um trecho da sessão sem apagar o vídeo nem sua análise."""
    initialize()
    with connect() as db:
        session = db.execute(
            "SELECT id,status FROM video_sessions WHERE id=?", (session_id,)
        ).fetchone()
        clip = db.execute(
            "SELECT id,status,session_id FROM video_segments WHERE id=?", (video_id,)
        ).fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        if not clip or clip["session_id"] != session_id:
            raise HTTPException(status_code=404, detail="Vídeo não pertence a esta sessão")
        if session["status"] in ("queued", "processing") or clip["status"] in ("queued", "processing"):
            raise HTTPException(
                status_code=409,
                detail="A sessão está sendo analisada; cancele ou aguarde antes de retirar o vídeo",
            )

        db.execute(
            "UPDATE video_segments SET session_id=NULL,sort_order=0,session_detached=1 WHERE id=?",
            (video_id,),
        )
        remaining = db.execute(
            "SELECT id FROM video_segments WHERE session_id=? ORDER BY captured_at,id",
            (session_id,),
        ).fetchall()
        for order, row in enumerate(remaining):
            db.execute("UPDATE video_segments SET sort_order=? WHERE id=?", (order, row["id"]))

        session_deleted = not remaining
        if session_deleted:
            db.execute("DELETE FROM video_sessions WHERE id=?", (session_id,))
        else:
            db.execute(
                """UPDATE video_sessions
                   SET status='pending',stage='Análise desatualizada após retirar trecho',progress=0,
                       summary='',trace_json='[]',job_unit='',error='',processed_at=NULL,
                       ai_live_thinking='',ai_live_content='',ai_metrics_json='{}'
                   WHERE id=?""",
                (session_id,),
            )
    return {
        "ok": True,
        "session_id": session_id,
        "video_id": video_id,
        "remaining_clips": len(remaining),
        "session_deleted": session_deleted,
    }

@app.post("/api/videos/{video_id}/markers")
def create_video_marker(video_id: int, payload: MarkerCreate) -> dict:
    initialize()
    with connect() as db:
        if not db.execute("SELECT id FROM video_segments WHERE id=?", (video_id,)).fetchone():
            raise HTTPException(status_code=404, detail="Vídeo não encontrado")
        cursor = db.execute("INSERT INTO video_markers(video_id,offset_seconds,title) VALUES(?,?,?)", (video_id,payload.offset_seconds,payload.title.strip()))
    return {"ok": True, "id": cursor.lastrowid, "video_id": video_id, "offset_seconds": payload.offset_seconds, "title": payload.title.strip(), "ai_generated": 0}

@app.put("/api/videos/{video_id}/captured-at")
def update_video_date(video_id: int, payload: VideoDateUpdate) -> dict:
    captured=payload.captured_at.astimezone().isoformat()
    with connect() as db:
        row=db.execute("SELECT session_id FROM video_segments WHERE id=?",(video_id,)).fetchone()
        if not row: raise HTTPException(status_code=404,detail="Vídeo não encontrado")
        db.execute("UPDATE video_segments SET captured_at=? WHERE id=?",(captured,video_id))
        if row["session_id"] is not None:
            ordered=db.execute("SELECT id FROM video_segments WHERE session_id=? ORDER BY captured_at,id",(row["session_id"],)).fetchall()
            for order,item in enumerate(ordered): db.execute("UPDATE video_segments SET sort_order=? WHERE id=?",(order,item["id"]))
    return {"ok":True,"id":video_id,"captured_at":captured}


@app.post("/api/videos/{video_id}/trim")
def trim_video(video_id: int, payload: VideoTrimRequest) -> dict:
    """Substitui um clipe pelo intervalo escolhido e invalida a análise antiga."""
    initialize()
    with connect() as db:
        row = db.execute(
            "SELECT source_path,captured_at,status,session_id,preserved FROM video_segments WHERE id=?",
            (video_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    if row["status"] in ("queued", "processing"):
        raise HTTPException(status_code=409, detail="Interrompa ou aguarde a análise antes de cortar")

    source = safe_video_path(row["source_path"])
    total = probe_video_duration(source)
    start = float(payload.start_seconds)
    end = min(float(payload.end_seconds), total)
    if total <= 0:
        raise HTTPException(status_code=422, detail="Não foi possível ler a duração do vídeo")
    if end - start < 0.25:
        raise HTTPException(status_code=422, detail="O corte precisa ter pelo menos 0,25 segundo")
    if start >= total or (start <= 0.05 and end >= total - 0.05):
        raise HTTPException(status_code=422, detail="Escolha um intervalo menor que o vídeo original")

    temporary = source.with_name(f".{source.stem}.lume-trim-{secrets.token_hex(5)}{source.suffix}")
    cancel_video_audio_track_job(source)
    sharing.cancel_light_jobs(source)
    try:
        result = run(trim_video_command(source, temporary, start, end - start), timeout=3600)
        if result.returncode != 0 or not temporary.is_file() or temporary.stat().st_size <= 0:
            raise HTTPException(status_code=500, detail=result.stderr.strip() or "O FFmpeg não conseguiu salvar o corte")
        delete_video_caches(source)
        os.replace(temporary, source)
        preserved_copy = CLIPS_DIR.resolve() / source.name
        if bool(row["preserved"]) and source.parent != CLIPS_DIR.resolve() and preserved_copy.is_file():
            shutil.copy2(source, preserved_copy)
    finally:
        if temporary.exists():
            temporary.unlink(missing_ok=True)

    captured = row["captured_at"]
    try:
        captured = (datetime.fromisoformat(captured) + timedelta(seconds=start)).isoformat()
    except (TypeError, ValueError):
        pass
    with connect() as db:
        db.execute("DELETE FROM video_markers WHERE video_id=? AND (offset_seconds<? OR offset_seconds>=?)", (video_id, start, end))
        db.execute("UPDATE video_markers SET offset_seconds=offset_seconds-? WHERE video_id=?", (start, video_id))
        db.execute(
            """UPDATE video_segments SET captured_at=?,duration_seconds=?,description='',transcript='',
                      transcript_segments_json='[]',speakers_json='[]',audio_events_json='[]',chapters_json='[]',
                      model='',status='pending',stage='Aguardando análise',progress=0,trace_json='[]',job_unit='',
                      error='',processed_at=NULL,ai_live_thinking='',ai_live_content='',ai_metrics_json='{}'
               WHERE id=?""",
            (captured, end - start, video_id),
        )
        if row["session_id"] is not None:
            db.execute(
                """UPDATE video_sessions SET status='pending',stage='Análise desatualizada após corte',progress=0,
                          summary='',trace_json='[]',job_unit='',error='',processed_at=NULL,
                          ai_live_thinking='',ai_live_content='',ai_metrics_json='{}' WHERE id=?""",
                (row["session_id"],),
            )
    return {
        "ok": True, "id": video_id, "start_seconds": start, "end_seconds": end,
        "duration_seconds": end - start, "captured_at": captured, "analysis_reset": True,
    }

@app.put("/api/video-markers/{marker_id}")
def update_video_marker(marker_id: int, payload: MarkerUpdate) -> dict:
    with connect() as db:
        updated = db.execute("UPDATE video_markers SET title=?,ai_generated=0 WHERE id=?", (payload.title.strip(),marker_id)).rowcount
    if not updated: raise HTTPException(status_code=404, detail="Marcador não encontrado")
    return {"ok": True, "id": marker_id, "title": payload.title.strip()}

@app.delete("/api/video-markers/{marker_id}")
def delete_video_marker(marker_id: int) -> dict:
    with connect() as db: updated=db.execute("DELETE FROM video_markers WHERE id=?",(marker_id,)).rowcount
    if not updated: raise HTTPException(status_code=404, detail="Marcador não encontrado")
    return {"ok": True, "id": marker_id}


@app.get("/api/video-sessions")
def list_video_sessions() -> dict:
    backfill_video_session_durations()
    with connect() as db:
        sessions = db.execute(
            """SELECT s.*,count(v.id) clip_count,coalesce(sum(v.duration_seconds),0) duration_seconds,coalesce(min(v.captured_at),s.created_at) captured_at
               FROM video_sessions s LEFT JOIN video_segments v ON v.session_id=s.id
               GROUP BY s.id ORDER BY captured_at DESC"""
        ).fetchall()
        clips = db.execute(
            """SELECT id,session_id,source_path,app,title,description,duration_seconds,status,error,preserved,sort_order,captured_at,
                      transcript,transcript_segments_json,speakers_json,audio_events_json,chapters_json
               FROM video_segments WHERE session_id IS NOT NULL ORDER BY session_id,captured_at,id"""
        ).fetchall()
    clips_by_session: dict[int, list[dict]] = {}
    with connect() as db:
        session_markers = db.execute("SELECT m.* FROM video_markers m JOIN video_segments v ON v.id=m.video_id WHERE v.session_id IS NOT NULL ORDER BY m.offset_seconds,m.id").fetchall()
    markers_by_video: dict[int,list[dict]] = {}
    for marker in session_markers: markers_by_video.setdefault(marker["video_id"],[]).append(dict(marker))
    for row in clips:
        source = resolve_media_source(row["source_path"])
        available = source.is_file()
        game, game_source = video_game_label(row["source_path"], row["app"])
        clips_by_session.setdefault(row["session_id"], []).append({
            "id": row["id"],
            "name": media_source_name(row["source_path"]),
            "title": row["title"],
            "game": game,
            "game_source": game_source,
            "description": row["description"],
            "duration_seconds": row["duration_seconds"],
            "status": row["status"],
            "error": row["error"],
            "preserved": bool(row["preserved"]),
            "sort_order": row["sort_order"],
            "captured_at": row["captured_at"],
            "transcript": row["transcript"],
            "transcript_segments": json.loads(row["transcript_segments_json"] or "[]"),
            "speakers": json.loads(row["speakers_json"] or "[]"),
            "audio_events": json.loads(row["audio_events_json"] or "[]"),
            "chapters": json.loads(row["chapters_json"] or "[]"),
            "markers": markers_by_video.get(row["id"], []),
            "bytes": source.stat().st_size if available else 0,
            "available": available,
            "path": row["source_path"],
            "url": media_url(row["source_path"], source) if available else "",
            "thumbnail_url": media_url(row["source_path"], source, "video-thumbnail") if available else "",
        })
    items = []
    for row in sessions:
        session_clips = clips_by_session.get(row["id"], [])
        items.append({
            **dict(row),
            "bytes": sum(clip["bytes"] for clip in session_clips),
            "trace": json.loads(row["trace_json"] or "[]"),
            "clips": session_clips,
        })
    return {"items": items}


@app.post("/api/video-sessions/{session_id}/process")
def process_video_session_job(session_id: int) -> dict:
    with connect() as db:
        row = db.execute("SELECT id,status FROM video_sessions WHERE id=?", (session_id,)).fetchone()
        active = db.execute("SELECT id FROM video_sessions WHERE status IN ('queued','processing') AND id<>?", (session_id,)).fetchone()
        active_video = db.execute("SELECT id FROM video_segments WHERE status IN ('queued','processing')").fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        if active or active_video:
            raise HTTPException(status_code=409, detail="Outro vídeo ou sessão já está sendo analisado")
        unit = f"lume-video-session-{session_id}"
        db.execute("UPDATE video_sessions SET status='queued',stage='Aguardando início',progress=0,trace_json='[]',job_unit=?,error='' WHERE id=?", (unit, session_id))
    result = get_manager().run_transient(
        unit, [sys.executable, "-m", "app.backend.pipeline", "--video-session", str(session_id)],
        timeout_property="12h", timeout=20)
    if result.returncode != 0:
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao iniciar sessão")
    return {"ok": True, "id": session_id, "status": "queued"}


@app.delete("/api/video-sessions/{session_id}/analysis")
def cancel_video_session(session_id: int) -> dict:
    with connect() as db:
        row = db.execute("SELECT status,job_unit FROM video_sessions WHERE id=?", (session_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    if row["job_unit"] == "lume-process.service":
        result = cancel_pipeline(None)
        return {**result, "id": session_id}
    if row["job_unit"]:
        service_action("stop", [row["job_unit"]], timeout=30)
    with connect() as db:
        db.execute("UPDATE video_sessions SET status='cancelled',stage='Cancelada pelo usuário',error='cancelada manualmente',ai_live_thinking='',ai_live_content='',ai_metrics_json='{}' WHERE id=?", (session_id,))
        db.execute("UPDATE video_segments SET status='cancelled',stage='Cancelado com a sessão' WHERE session_id=? AND status IN ('queued','processing')", (session_id,))
    return {"ok": True, "id": session_id}


@app.delete("/api/video-sessions/{session_id}")
def delete_video_session(session_id: int) -> dict:
    with connect() as db:
        session = db.execute("SELECT status FROM video_sessions WHERE id=?", (session_id,)).fetchone()
        if not session:
            raise HTTPException(status_code=404, detail="Sessão não encontrada")
        clips = db.execute(
            "SELECT source_path,status FROM video_segments WHERE session_id=?", (session_id,)
        ).fetchall()
        if session["status"] in ("queued", "processing") or any(
            clip["status"] in ("queued", "processing") for clip in clips
        ):
            raise HTTPException(status_code=409, detail="A sessão está sendo analisada; cancele a análise antes de excluir")

        deleted_files = 0
        for clip in clips:
            source = resolve_media_source(clip["source_path"])
            if source.parent != VIDEO_DIR.resolve():
                continue
            if source.exists():
                source.unlink()
                deleted_files += 1
            source.with_suffix(source.suffix + ".window").unlink(missing_ok=True)
            source.with_suffix(source.suffix + ".markers").unlink(missing_ok=True)
            source.with_suffix(source.suffix + ".session").unlink(missing_ok=True)

        db.execute("DELETE FROM video_markers WHERE video_id IN (SELECT id FROM video_segments WHERE session_id=?)", (session_id,))
        db.execute("DELETE FROM video_segments WHERE session_id=?", (session_id,))
        db.execute("DELETE FROM video_sessions WHERE id=?", (session_id,))
    return {"ok": True, "id": session_id, "clips": len(clips), "deleted_files": deleted_files}


@app.put("/api/video-sessions/{session_id}/context")
def update_video_session_context(session_id: int, payload: ContextUpdate) -> dict:
    with connect() as db:
        updated = db.execute("UPDATE video_sessions SET context=? WHERE id=?", (payload.context.strip(), session_id)).rowcount
    if not updated:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    return {"ok": True, "id": session_id, "context": payload.context.strip()}


@app.post("/api/videos/process")
def process_video(payload: VideoProcessRequest) -> dict:
    path = safe_video_path(payload.path)
    source_key = media_source_key(path)
    today = datetime.now().astimezone().date().isoformat()
    busy_units = ("lume-process.service", f"lume-summary@{today}.service", f"lume-hourly@{today}.service")
    if any(unit_state(unit)["active"] for unit in busy_units):
        raise HTTPException(status_code=409, detail="A GPU está ocupada com outro processamento")
    with connect() as db:
        active = db.execute("SELECT id FROM video_segments WHERE status IN ('queued','processing') AND source_path<>?", (source_key,)).fetchone()
        if active:
            raise HTTPException(status_code=409, detail="Outro vídeo já está na fila de análise")
        db.execute(
            "INSERT OR IGNORE INTO video_segments(source_path,captured_at,status) VALUES(?,?,'pending')",
            (source_key, datetime.fromtimestamp(path.stat().st_mtime).astimezone().isoformat()),
        )
        row = db.execute("SELECT id FROM video_segments WHERE source_path=?", (source_key,)).fetchone()
        unit = f"lume-video-{row['id']}"
        db.execute(
            "UPDATE video_segments SET status='queued',stage='Aguardando início',progress=0,trace_json='[]',job_unit=?,error='' WHERE id=?",
            (unit, row["id"]),
        )
    result = get_manager().run_transient(
        unit, [sys.executable, "-m", "app.backend.pipeline", "--video", str(path)],
        timeout_property="6h", timeout=20)
    if result.returncode != 0:
        with connect() as db:
            db.execute("UPDATE video_segments SET status='error',stage='Falha ao iniciar',error=? WHERE id=?", (result.stderr[-2000:], row["id"]))
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao iniciar análise")
    return {"ok": True, "status": "queued", "id": row["id"], "unit": unit}


@app.put("/api/videos/{video_id}/context")
def update_video_context(video_id: int, payload: ContextUpdate) -> dict:
    with connect() as db:
        updated = db.execute("UPDATE video_segments SET context=? WHERE id=?", (payload.context.strip(), video_id)).rowcount
    if not updated:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    return {"ok": True, "id": video_id, "context": payload.context.strip()}


@app.put("/api/videos/{video_id}/speakers/{speaker_id}")
def update_video_speaker(video_id: int, speaker_id: str, payload: SpeakerLabelUpdate) -> dict:
    if not re.fullmatch(r"(?:speaker|discord|system)_\d+", speaker_id):
        raise HTTPException(status_code=422, detail="Locutor inválido")
    with connect() as db:
        row = db.execute("SELECT source_path,speakers_json FROM video_segments WHERE id=?", (video_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Vídeo não encontrado")
        speakers = json.loads(row["speakers_json"] or "[]")
        speaker = next((item for item in speakers if item.get("id") == speaker_id), None)
        if not speaker:
            raise HTTPException(status_code=404, detail="Locutor não encontrado")
        previous_identity_id = speaker.get("identity_id")
        speaker = enroll_voice_identity(db, "video", video_id, speaker, payload.label.strip(), resolve_media_source(row["source_path"]))
        db.execute("UPDATE video_segments SET speakers_json=? WHERE id=?", (json.dumps(speakers, ensure_ascii=False), video_id))
        if previous_identity_id and previous_identity_id != speaker["identity_id"]:
            rebuild_voice_identity(db, int(previous_identity_id))
        rebuild_voice_identity(db, int(speaker["identity_id"]))
    return {"ok": True, "video_id": video_id, "speaker": speaker}


@app.get("/api/videos/{video_id}/speakers/{speaker_id}/sample")
def video_speaker_sample(video_id: int, speaker_id: str) -> Response:
    if not re.fullmatch(r"(?:speaker|discord|system)_\d+", speaker_id):
        raise HTTPException(status_code=422, detail="Locutor inválido")
    with connect() as db:
        row = db.execute("SELECT source_path,speakers_json FROM video_segments WHERE id=?", (video_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    source = resolve_media_source(row["source_path"])
    if source.parent not in {VIDEO_DIR.resolve(), CLIPS_DIR.resolve()} or not source.is_file():
        raise HTTPException(status_code=404, detail="Arquivo de vídeo indisponível")
    speaker = next((item for item in json.loads(row["speakers_json"] or "[]") if item.get("id") == speaker_id), None)
    if not speaker:
        raise HTTPException(status_code=404, detail="Amostra de locutor não encontrada")
    start = max(0, float(speaker.get("sample_start", 0)))
    duration = max(0.5, min(10, float(speaker.get("sample_end", start + 5)) - start))
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}", "-i", str(source),
    ]
    if _audio_streams(source) >= 4 and speaker.get("source") in {"discord", "system"}:
        command += ["-map", f"0:a:{2 if speaker.get('source') == 'discord' else 3}"]
    command += ["-t", f"{duration:.3f}", "-vn", "-ac", "1", "-ar", "16000", "-f", "wav", "pipe:1"]
    result = subprocess.run(command, capture_output=True, timeout=60, creationflags=_HIDDEN_PROCESS)
    if result.returncode != 0 or not result.stdout:
        raise HTTPException(status_code=503, detail="Não foi possível gerar a amostra de voz")
    return Response(content=result.stdout, media_type="audio/wav", headers={"Cache-Control": "private, max-age=3600"})


@app.delete("/api/videos/{video_id}/analysis")
def cancel_video_analysis(video_id: int) -> dict:
    with connect() as db:
        row = db.execute("SELECT status,job_unit FROM video_segments WHERE id=?", (video_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    if row["status"] not in ("queued", "processing"):
        raise HTTPException(status_code=409, detail="A análise não está em andamento")
    if row["job_unit"] == "lume-process.service":
        result = cancel_pipeline(None)
        return {**result, "id": video_id}
    if row["job_unit"]:
        result = service_action("stop", [row["job_unit"]], timeout=30)
        if result.returncode != 0 and not stop_target_is_already_gone(result):
            raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao cancelar análise")
    with connect() as db:
        db.execute(
            "UPDATE video_segments SET status='cancelled',stage='Cancelado pelo usuário',error='análise cancelada manualmente',ai_live_thinking='',ai_live_content='',ai_metrics_json='{}' WHERE id=?",
            (video_id,),
        )
    return {"ok": True, "id": video_id}


@app.post("/api/videos/preserve")
def preserve_video(payload: VideoProcessRequest) -> dict:
    source=safe_video_path(payload.path);CLIPS_DIR.mkdir(parents=True,exist_ok=True)
    destination=CLIPS_DIR/source.name
    if source.parent==VIDEO_DIR.resolve(): shutil.copy2(source,destination)
    with connect() as db: db.execute("UPDATE video_segments SET preserved=1 WHERE source_path=?",(media_source_key(source),))
    return {"ok":True,"path":str(destination)}


@app.delete("/api/videos")
def delete_video(path: str) -> dict:
    source = resolve_media_source(path)
    if source.parent not in {VIDEO_DIR.resolve(), CLIPS_DIR.resolve()} or source.suffix.lower() not in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=403, detail="Arquivo fora das pastas de vídeo")
    source_key = media_source_key(source)
    if source.parent != VIDEO_DIR.resolve():
        raise HTTPException(status_code=403, detail="Clipes preservados não são apagados por esta ação")
    cancel_video_audio_track_job(source)
    with connect() as db:
        state = db.execute("SELECT status FROM video_segments WHERE source_path=?", (source_key,)).fetchone()
    if not state and not source.is_file():
        raise HTTPException(status_code=404, detail="Vídeo e análise não encontrados")
    if state and state["status"] in ("queued", "processing"):
        raise HTTPException(status_code=409, detail="O vídeo está sendo analisado; aguarde ou interrompa o processamento")
    try:
        unlink_with_retry(source)
    except PermissionError as exc:
        raise HTTPException(
            status_code=409,
            detail="O vídeo ainda está sendo liberado pelo player ou FFmpeg. Feche o player e tente novamente em alguns segundos.",
        ) from exc
    for sidecar in (".window", ".markers", ".session"):
        try:
            unlink_with_retry(source.with_suffix(source.suffix + sidecar), attempts=5)
        except PermissionError:
            pass
    delete_video_caches(source)
    with connect() as db:
        db.execute("DELETE FROM video_markers WHERE video_id IN (SELECT id FROM video_segments WHERE source_path=?)", (source_key,))
        db.execute("DELETE FROM video_segments WHERE source_path=?", (source_key,))
    return {"ok": True, "path": str(source)}


@app.get("/api/files")
def list_files(
    kind: Literal["screen", "audio"],
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict:
    directory, suffix = (SCREEN_DIR, ".png") if kind == "screen" else (AUDIO_DIR, ".wav")
    all_paths = sorted(directory.glob(f"*{suffix}"), key=lambda item: item.stat().st_mtime, reverse=True)
    newest_audio = all_paths[0] if kind == "audio" and all_paths else None
    paths = all_paths[offset:offset + limit]
    audio_recording = kind == "audio" and unit_state("captura-dia-audio.service")["active"]
    with connect() as db:
        states = {row["source_path"]: row_dict(row) for row in db.execute(
            "SELECT id,source_path,status,title,text,app,model,error,preserved,transcript_segments_json,speakers_json,audio_events_json FROM captures WHERE kind=?", (kind,)
        )}
    items = []
    for path in paths:
        stat = path.stat()
        source_key = media_source_key(path)
        indexed = states.get(source_key, {})
        if kind == "audio" and indexed.get("transcript_segments"):
            # Registros produzidos antes do filtro novo também deixam de exibir
            # créditos fantasmas, sem exigir uma transcrição cara novamente.
            from .pipeline import filter_hallucinated_segments

            original_segments = indexed["transcript_segments"]
            clean_segments = filter_hallucinated_segments(original_segments)
            if len(clean_segments) != len(original_segments):
                indexed["transcript_segments"] = clean_segments
                labels = {"microphone": "Você", "discord": "Discord", "system": "Outros sons"}
                indexed["text"] = "\n".join(
                    f"{labels.get(str(segment.get('source') or ''), 'Falante')}: {segment.get('text', '')}"
                    for segment in clean_segments
                ).strip()
        items.append({
            "name": path.name, "path": source_key, "kind": kind, "bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(),
            "open": bool(path == newest_audio and audio_recording),
            "status": "recording" if path == newest_audio and audio_recording else indexed.get("status", "unindexed"),
            "capture_id": indexed.get("id"), "title": indexed.get("title", ""), "text": indexed.get("text", ""),
            "app": indexed.get("app", ""), "model": indexed.get("model", ""), "error": indexed.get("error", ""),
            "preserved": bool(indexed.get("preserved", 0)),
            "transcript_segments": indexed.get("transcript_segments", []), "speakers": indexed.get("speakers", []),
            "audio_events": indexed.get("audio_events", []),
            "audio_channels": _audio_channels(path) if kind == "audio" else 0,
            "url": f"/api/{'screenshot' if kind == 'screen' else 'audio'}?path={source_key}",
        })
    return {"items": items, "kind": kind, "total": len(all_paths), "offset": offset, "has_more": offset + len(items) < len(all_paths)}


def delete_capture_file(kind: str, raw_path: str) -> bool:
    path = safe_screen_path(raw_path) if kind == "screen" else safe_audio_path(raw_path)
    if kind == "audio":
        newest = max(AUDIO_DIR.glob("*.wav"), key=lambda item: item.stat().st_mtime, default=None)
        if newest == path and unit_state("captura-dia-audio.service")["active"]:
            raise HTTPException(status_code=409, detail="O áudio ainda está sendo gravado e não pode ser excluído")
    path.unlink()
    if kind == "screen":
        path.with_suffix(path.suffix + ".window").unlink(missing_ok=True)
    return True


@app.delete("/api/files")
def delete_file(kind: Literal["screen", "audio"], path: str) -> dict:
    with connect() as db:
        row = db.execute("SELECT id,kind,source_path FROM captures WHERE source_path=?", (media_source_key(path),)).fetchone()
        if row:
            delete_capture_file(row["kind"], row["source_path"])
            db.execute("DELETE FROM captures WHERE id=?", (row["id"],))
            return {"ok": True, "id": row["id"], "file_deleted": True}
    delete_capture_file(kind, path)
    return {"ok": True, "id": None, "file_deleted": True}


@app.delete("/api/files/unprocessed/all")
def delete_unprocessed_files() -> dict:
    """Apaga mídia local ainda não processada, sem tocar em trabalhos ativos."""
    deleted = {"screen": 0, "audio": 0}
    skipped = {"done": 0, "processing": 0, "recording": 0}
    audio_paths = list(AUDIO_DIR.glob("*.wav"))
    newest_audio = max(audio_paths, key=lambda item: item.stat().st_mtime, default=None)
    audio_recording = unit_state("captura-dia-audio.service")["active"]

    with connect() as db:
        states = {
            row["source_path"]: row_dict(row)
            for row in db.execute("SELECT id,kind,source_path,status FROM captures")
        }
        for kind, paths in (("screen", SCREEN_DIR.glob("*.png")), ("audio", iter(audio_paths))):
            for path in list(paths):
                source_key = media_source_key(path)
                state = states.get(source_key)
                status = state["status"] if state else "unindexed"
                if status == "done":
                    skipped["done"] += 1
                    continue
                if status == "processing":
                    skipped["processing"] += 1
                    continue
                if kind == "audio" and path == newest_audio and audio_recording:
                    skipped["recording"] += 1
                    continue
                path.unlink(missing_ok=True)
                if kind == "screen":
                    path.with_suffix(path.suffix + ".window").unlink(missing_ok=True)
                if state:
                    db.execute("DELETE FROM captures WHERE id=?", (state["id"],))
                deleted[kind] += 1
    return {"ok": True, "deleted": deleted, "deleted_total": sum(deleted.values()), "skipped": skipped}


@app.put("/api/retention/{kind}/{item_id}")
def set_retention(kind: Literal["screen", "audio", "video", "session"], item_id: int, payload: RetentionUpdate) -> dict:
    value = int(payload.preserved)
    with connect() as db:
        if kind in {"screen", "audio"}:
            updated = db.execute(
                "UPDATE captures SET preserved=? WHERE id=? AND kind=?", (value, item_id, kind)
            ).rowcount
        elif kind == "video":
            updated = db.execute("UPDATE video_segments SET preserved=? WHERE id=?", (value, item_id)).rowcount
        else:
            updated = db.execute("UPDATE video_sessions SET preserved=? WHERE id=?", (value, item_id)).rowcount
            if updated and payload.preserved:
                db.execute("UPDATE video_segments SET preserved=1 WHERE session_id=?", (item_id,))
    if not updated:
        raise HTTPException(status_code=404, detail="Mídia não encontrada")
    return {"ok": True, "kind": kind, "id": item_id, "preserved": payload.preserved}


def _delete_media_sidecars(path: Path) -> None:
    for suffix in (".window", ".markers", ".session", ".sem-imagem"):
        path.with_suffix(path.suffix + suffix).unlink(missing_ok=True)


@app.get("/api/settings/cleanup")
def get_cleanup_settings() -> dict:
    return cleanup_settings()


@app.put("/api/settings/cleanup")
def set_cleanup_settings(settings: CleanupSettings) -> dict:
    return save_cleanup_settings(settings.enabled)


def resolve_timeline_options() -> tuple[int, str]:
    """FPS e timecode inicial da timeline, como configurados no Video seletivo."""
    config = parse_shell_config(VIDEO_CONFIG)
    try:
        fps = int(config.get("VIDEO_RESOLVE_FPS", "0"))
    except ValueError:
        fps = 0
    return max(0, fps), config.get("VIDEO_RESOLVE_START_TIMECODE", editing.DEFAULT_START_TIMECODE)


@app.get("/api/editing")
def get_editing_folder() -> dict:
    return editing.folder()


@app.post("/api/editing/video/{video_id}")
def send_video_to_editing(video_id: int) -> dict:
    fps, start = resolve_timeline_options()
    try:
        return editing.send_video(video_id, start_timecode=start, fps=fps)
    except editing.EditingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.post("/api/editing/session/{session_id}")
def send_session_to_editing(session_id: int) -> dict:
    fps, start = resolve_timeline_options()
    try:
        return editing.send_session(session_id, start_timecode=start, fps=fps)
    except editing.EditingError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc


@app.delete("/api/editing/{name}")
def remove_from_editing(name: str) -> dict:
    """Some com o atalho; o video original continua onde sempre esteve."""
    try:
        return editing.remove(name)
    except editing.EditingError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=409, detail=f"Nao deu para remover: {exc}") from exc


@app.post("/api/editing/open")
def open_editing_folder() -> dict:
    """Abre a pasta no gerenciador de arquivos da maquina que roda o Lume."""
    EDIT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        if os.name == "nt":
            os.startfile(EDIT_DIR)
        else:
            subprocess.Popen(["xdg-open", str(EDIT_DIR)])
    except OSError as exc:
        raise HTTPException(status_code=503, detail=f"Nao deu para abrir a pasta: {exc}") from exc
    return {"ok": True, "root": str(EDIT_DIR)}


@app.get("/api/settings/prompts")
def get_prompts() -> dict:
    return {"items": prompts.listing()}


@app.put("/api/settings/prompts/{key}")
def set_prompt(key: str, update: PromptUpdate) -> dict:
    """Guarda o texto do usuario; um prompt igual ao padrao volta a seguir o Lume."""
    try:
        return prompts.save(key, update.text)
    except prompts.PromptError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete("/api/settings/prompts/{key}")
def reset_prompt(key: str) -> dict:
    try:
        return prompts.reset(key)
    except prompts.PromptError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/media/raw/unkept")
def delete_unkept_raw_media() -> dict:
    """Executa manualmente a limpeza segura apenas de prints e áudios consolidados."""
    if unit_state("lume-process.service")["active"]:
        raise HTTPException(status_code=409, detail="Aguarde o processamento e os resumos terminarem antes da limpeza")
    ready_days = cleanup_ready_days()
    if any(
        unit_state(f"lume-summary@{day}.service")["active"]
        or unit_state(f"lume-hourly@{day}.service")["active"]
        for day in ready_days
    ):
        raise HTTPException(status_code=409, detail="Um resumo ainda está utilizando as capturas; aguarde a conclusão")
    with connect() as db:
        sequence_active = db.execute(
            "SELECT 1 FROM screen_sequence_jobs WHERE status IN ('queued','processing') LIMIT 1"
        ).fetchone()
    if sequence_active:
        raise HTTPException(status_code=409, detail="Uma análise de sequência ainda está utilizando os prints")
    return cleanup_processed_capture_media()


@app.post("/api/pipeline/process-file")
def process_file(payload: ProcessFileRequest) -> dict:
    if unit_state("lume-process.service")["active"]:
        raise HTTPException(status_code=409, detail="O pipeline automático está usando a GPU (pode estar gerando o resumo); pare-o na tela Fila ou aguarde")
    path = safe_screen_path(payload.path) if payload.kind == "screen" else safe_audio_path(payload.path)
    if payload.kind == "audio":
        newest = max(AUDIO_DIR.glob("*.wav"), key=lambda item: item.stat().st_mtime, default=None)
        if newest == path and unit_state("captura-dia-audio.service")["active"]:
            raise HTTPException(status_code=409, detail="O WAV ainda está sendo gravado; aguarde o próximo segmento")
        with connect() as db:
            db.execute(
                """UPDATE captures SET status='pending',error='',transcript_segments_json='[]',
                   speakers_json='[]',audio_events_json='[]' WHERE source_path=?""", (media_source_key(path),)
            )
    result = run(
        [sys.executable, "-m", "app.backend.pipeline", "--file", str(path)], timeout=1800
    )
    if result.returncode != 0:
        raise HTTPException(status_code=503, detail=result.stderr.strip() or result.stdout.strip() or "Processamento falhou")


@app.post("/api/test/screen-sequence")
def test_screen_sequence(payload: ScreenSequenceTestRequest) -> dict:
    if unit_state("lume-process.service")["active"]:
        raise HTTPException(status_code=409, detail="O pipeline automático está usando a GPU; pare-o na tela Fila ou aguarde")
    if len(set(payload.paths)) != len(payload.paths):
        raise HTTPException(status_code=422, detail="A seleção contém prints repetidos")
    paths = [safe_screen_path(value) for value in payload.paths]
    with connect() as db:
        active = db.execute("SELECT id FROM screen_sequence_jobs WHERE status IN ('queued','processing') LIMIT 1").fetchone()
        video_busy = db.execute("SELECT id FROM video_segments WHERE status IN ('queued','processing') LIMIT 1").fetchone()
        session_busy = db.execute("SELECT id FROM video_sessions WHERE status IN ('queued','processing') LIMIT 1").fetchone()
        if active or video_busy or session_busy:
            raise HTTPException(status_code=409, detail="Outra análise já está usando ou aguardando a GPU")
        cursor = db.execute(
            "INSERT INTO screen_sequence_jobs(paths_json,status,stage,progress) VALUES(?,'queued','Aguardando início',0)",
            (json.dumps([media_source_key(path) for path in paths]),),
        )
        job_id = int(cursor.lastrowid)
        unit = f"lume-screen-sequence-{job_id}"
        db.execute("UPDATE screen_sequence_jobs SET job_unit=? WHERE id=?", (unit, job_id))
    result = get_manager().run_transient(
        unit, [sys.executable, "-m", "app.backend.pipeline", "--screen-sequence", str(job_id)],
        timeout_property="30m", timeout=20,
    )
    if result.returncode != 0:
        with connect() as db:
            db.execute("UPDATE screen_sequence_jobs SET status='error',stage='Falha ao iniciar',error=? WHERE id=?", (result.stderr[-2000:], job_id))
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao iniciar análise")
    return {"ok": True, "status": "queued", "id": job_id}


@app.get("/api/test/screen-sequence/{job_id}")
def screen_sequence_result(job_id: int) -> dict:
    with connect() as db:
        row = db.execute("SELECT * FROM screen_sequence_jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Teste de sequência não encontrado")
    return {**dict(row), "result": json.loads(row["result_json"] or "{}")}


@app.get("/api/tags")
def list_tags() -> dict:
    return tag_vocabulary.listing()


@app.post("/api/tags")
def create_tag(payload: TagCreate) -> dict:
    try:
        return tag_vocabulary.create(payload.label, payload.criterion)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/api/tags/test")
def test_tags(payload: TagTestRequest) -> dict:
    """Conciliação sem gravar nada: mostra o caminho de cada string até a tag."""
    resolution = tag_vocabulary.canonicalize(
        payload.tags, context=payload.context, use_laya=payload.use_laya, commit=False
    )
    return {**resolution.as_dict(), "laya": tag_vocabulary.laya.status()}


@app.post("/api/tags/promote")
def promote_tags(day: str = Query(pattern=r"^\d{4}-\d{2}-\d{2}$"), commit: bool = False) -> dict:
    """Roda a promoção de um dia — em ensaio por padrão, gravando só quando pedido."""
    if unit_state("lume-process.service")["active"]:
        raise HTTPException(status_code=409, detail="O pipeline automático está usando a GPU; pare-o na tela Fila ou aguarde")
    flag = "--promote-tags" if commit else "--preview-tags"
    result = run([sys.executable, "-m", "app.backend.pipeline", flag, day], timeout=900)
    if result.returncode != 0:
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao promover as tags")
    try:
        return json.loads(result.stdout)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail="O pipeline não devolveu um relatório legível") from exc


@app.put("/api/tags/{slug}/status")
def update_tag_status(slug: str, payload: TagStatusUpdate) -> dict:
    try:
        return tag_vocabulary.set_status(slug, payload.status)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/api/tags/{slug}/merge")
def merge_tag(slug: str, payload: TagMergeRequest) -> dict:
    try:
        return tag_vocabulary.merge(slug, payload.into)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.delete("/api/tags/aliases/{alias}")
def delete_tag_alias(alias: str) -> dict:
    try:
        return tag_vocabulary.remove_alias(alias)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.delete("/api/test/screen-sequence/{job_id}")
def cancel_screen_sequence(job_id: int) -> dict:
    with connect() as db:
        row = db.execute("SELECT status,job_unit FROM screen_sequence_jobs WHERE id=?", (job_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Teste de sequência não encontrado")
    if row["job_unit"]:
        service_action("stop", [row["job_unit"]], timeout=30)
    with connect() as db:
        db.execute("UPDATE screen_sequence_jobs SET status='cancelled',stage='Cancelado pelo usuário',error='análise cancelada manualmente' WHERE id=?", (job_id,))
    return {"ok": True, "id": job_id}
    try:
        payload_result = json.loads(result.stdout)
        if payload_result.get("status") == "already-running":
            raise HTTPException(status_code=409, detail="Já existe um processamento usando a GPU; aguarde a conclusão")
        return payload_result
    except json.JSONDecodeError:
        return {"ok": True, "output": result.stdout.strip()}


def capture_payload(row) -> dict:
    item = row_dict(row)
    item["source_available"] = resolve_media_source(item["source_path"]).is_file()
    item["image_url"] = f"/api/screenshot?path={item['source_path']}" if item["kind"] == "screen" and item["source_available"] else None
    item["paired_image_url"] = None
    item["paired_image_text"] = ""
    if item["kind"] == "audio":
        item["audio_channels"] = _audio_channels(resolve_media_source(item["source_path"])) if item["source_available"] else 0
        with connect() as db:
            paired = db.execute(
                """SELECT source_path, text FROM captures
                   WHERE kind='screen'
                     AND abs(julianday(captured_at)-julianday(?)) <= (2.0/1440.0)
                   ORDER BY abs(julianday(captured_at)-julianday(?)) LIMIT 1""",
                (item["captured_at"], item["captured_at"]),
            ).fetchone()
        if paired:
            if resolve_media_source(paired["source_path"]).is_file():
                item["paired_image_url"] = f"/api/screenshot?path={paired['source_path']}"
            item["paired_image_text"] = paired["text"] or ""
    return item


@app.put("/api/captures/{capture_id}/speakers/{speaker_id}")
def update_capture_speaker(capture_id: int, speaker_id: str, payload: SpeakerLabelUpdate) -> dict:
    if not re.fullmatch(r"(?:speaker|discord|system)_\d+", speaker_id):
        raise HTTPException(status_code=422, detail="Locutor inválido")
    with connect() as db:
        row = db.execute("SELECT kind,source_path,speakers_json FROM captures WHERE id=?", (capture_id,)).fetchone()
        if not row or row["kind"] != "audio":
            raise HTTPException(status_code=404, detail="Áudio não encontrado")
        speakers = json.loads(row["speakers_json"] or "[]")
        speaker = next((item for item in speakers if item.get("id") == speaker_id), None)
        if not speaker:
            raise HTTPException(status_code=404, detail="Locutor não encontrado")
        previous_identity_id = speaker.get("identity_id")
        speaker = enroll_voice_identity(db, "audio", capture_id, speaker, payload.label.strip(), resolve_media_source(row["source_path"]))
        db.execute("UPDATE captures SET speakers_json=? WHERE id=?", (json.dumps(speakers, ensure_ascii=False), capture_id))
        if previous_identity_id and previous_identity_id != speaker["identity_id"]:
            rebuild_voice_identity(db, int(previous_identity_id))
        rebuild_voice_identity(db, int(speaker["identity_id"]))
    return {"ok": True, "capture_id": capture_id, "speaker": speaker}


@app.get("/api/voice-identities")
def list_voice_identities() -> dict:
    with connect() as db:
        rows = db.execute(
            "SELECT id,label,embedding_json,sample_count,created_at,updated_at FROM voice_identities ORDER BY label COLLATE NOCASE"
        ).fetchall()
    return {"items": voice_identity_payloads(rows)}


def _speaker_without_identity(speaker: dict) -> dict:
    """Volta uma amostra ao estado não identificado sem perder sua diarização."""
    cleaned = dict(speaker)
    for key in ("identity_id", "confidence", "identified", "confirmed"):
        cleaned.pop(key, None)
    source = str(cleaned.get("source") or "")
    suffix = re.search(r"(\d+)$", str(cleaned.get("id") or ""))
    cleaned["label"] = (
        "Você" if source == "microphone" else
        "Voz do Discord" if source == "discord" else
        "Voz de outro conteúdo" if source == "system" else
        f"Pessoa {suffix.group(1)}" if suffix else "Voz não identificada"
    )
    return cleaned


@app.delete("/api/voice-identities/{identity_id}")
def delete_voice_identity(identity_id: int) -> dict:
    """Remove um perfil incorreto e solta as amostras para nova classificação."""
    updated = {"audio": 0, "video": 0}
    with connect() as db:
        identity = db.execute("SELECT id,label FROM voice_identities WHERE id=?", (identity_id,)).fetchone()
        if not identity:
            raise HTTPException(status_code=404, detail="Perfil de voz não encontrado")
        for source_kind, table in (("audio", "captures"), ("video", "video_segments")):
            rows = db.execute(
                f"SELECT id,speakers_json FROM {table} WHERE speakers_json!='[]'"
            ).fetchall()
            for row in rows:
                speakers = json.loads(row["speakers_json"] or "[]")
                changed = False
                for index, speaker in enumerate(speakers):
                    if speaker.get("identity_id") == identity_id:
                        speakers[index] = _speaker_without_identity(speaker)
                        changed = True
                if changed:
                    db.execute(
                        f"UPDATE {table} SET speakers_json=? WHERE id=?",
                        (json.dumps(speakers, ensure_ascii=False), row["id"]),
                    )
                    updated[source_kind] += 1
        db.execute("DELETE FROM voice_identities WHERE id=?", (identity_id,))
    return {"ok": True, "id": identity_id, "label": identity["label"], "updated": updated}


@app.get("/api/captures/{capture_id}/speakers/{speaker_id}/sample")
def capture_speaker_sample(capture_id: int, speaker_id: str) -> Response:
    if not re.fullmatch(r"(?:speaker|discord|system)_\d+", speaker_id):
        raise HTTPException(status_code=422, detail="Locutor inválido")
    with connect() as db:
        row = db.execute("SELECT kind,source_path,speakers_json FROM captures WHERE id=?", (capture_id,)).fetchone()
    if not row or row["kind"] != "audio":
        raise HTTPException(status_code=404, detail="Áudio não encontrado")
    source = safe_audio_path(row["source_path"])
    speaker = next((item for item in json.loads(row["speakers_json"] or "[]") if item.get("id") == speaker_id), None)
    if not speaker:
        raise HTTPException(status_code=404, detail="Amostra de locutor não encontrada")
    start = max(0, float(speaker.get("sample_start", 0)))
    duration = max(0.5, min(10, float(speaker.get("sample_end", start + 5)) - start))
    command = [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}", "-i", str(source),
        "-t", f"{duration:.3f}",
    ]
    channels = _audio_channels(source)
    if channels > 1 and speaker.get("source") in {"discord", "system"}:
        channel = "c2" if speaker.get("source") == "system" and channels >= 3 else "c1"
        command += ["-af", f"pan=mono|c0={channel}"]
    command += ["-ac", "1", "-ar", "16000", "-f", "wav", "pipe:1"]
    result = subprocess.run(command, capture_output=True, timeout=60, creationflags=_HIDDEN_PROCESS)
    if result.returncode != 0 or not result.stdout:
        raise HTTPException(status_code=503, detail="Não foi possível gerar a amostra de voz")
    return Response(content=result.stdout, media_type="audio/wav", headers={"Cache-Control": "private, max-age=3600"})


@app.get("/api/captures")
def captures(
    kind: Literal["all", "screen", "audio"] = "all",
    day: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    clauses = ["status='done'"]
    params: list[object] = []
    if kind != "all": clauses.append("kind=?"); params.append(kind)
    if day: clauses.append("substr(captured_at,1,10)=?"); params.append(day)
    params.append(limit)
    with connect() as db:
        rows = db.execute(
            f"SELECT * FROM captures WHERE {' AND '.join(clauses)} ORDER BY captured_at DESC LIMIT ?", params
        ).fetchall()
    return {"items": [capture_payload(row) for row in rows]}


@app.delete("/api/captures/{capture_id}")
def delete_capture(capture_id: int) -> dict:
    with connect() as db:
        row = db.execute("SELECT id,kind,source_path FROM captures WHERE id=?", (capture_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Item não encontrado")
        deleted = delete_capture_file(row["kind"], row["source_path"])
        db.execute("DELETE FROM captures WHERE id=?", (capture_id,))
    return {"ok": True, "id": capture_id, "file_deleted": deleted}


@app.get("/api/search")
def search(
    q: str = Query(default="", max_length=300),
    kind: Literal["all", "screen", "audio"] = "all",
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    terms = [term for term in re.findall(r"[\wÀ-ÿ]+", q, re.UNICODE) if term]
    with connect() as db:
        if not terms:
            clauses = ["status='done'"]; params: list[object] = []
            if kind != "all": clauses.append("kind=?"); params.append(kind)
            params.append(limit)
            rows = db.execute(f"SELECT * FROM captures WHERE {' AND '.join(clauses)} ORDER BY captured_at DESC LIMIT ?", params).fetchall()
        else:
            fts = " AND ".join(f'"{term.replace(chr(34), chr(34)*2)}"*' for term in terms)
            kind_sql = "" if kind == "all" else " AND c.kind=?"
            params = [fts] + ([] if kind == "all" else [kind]) + [limit]
            try:
                rows = db.execute(
                    f"SELECT c.* FROM captures_fts f JOIN captures c ON c.id=f.rowid WHERE captures_fts MATCH ? AND c.status='done'{kind_sql} ORDER BY bm25(captures_fts),c.captured_at DESC LIMIT ?",
                    params,
                ).fetchall()
            except sqlite3.OperationalError as exc:
                raise HTTPException(status_code=422, detail=f"Busca inválida: {exc}") from exc
    return {"items": [capture_payload(row) for row in rows], "query": q}


@app.get("/api/summary/{day}")
def summary(day: str) -> dict:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise HTTPException(status_code=422, detail="Data inválida")
    with connect() as db:
        row = db.execute("SELECT * FROM summaries WHERE day=?", (day,)).fetchone()
    if not row:
        return {"summary": None}
    payload = row_dict(row)
    relevant = payload.get("data", {}).get("relevant_media", {})
    for group, items in relevant.items() if isinstance(relevant, dict) else []:
        if not isinstance(items, list):
            continue
        for item in items:
            source = resolve_media_source(str(item.get("source_path") or ""))
            item["available"] = source.is_file()
            if item.get("kind") == "screen" and source.is_file():
                item["url"] = f"/api/screenshot?path={item['source_path']}"
            elif item.get("kind") == "audio" and source.is_file():
                item["url"] = f"/api/audio?path={item['source_path']}"
            elif item.get("kind") in {"video", "session"} and source.is_file():
                item["url"] = f"/api/video?path={item['source_path']}"
            else:
                item["url"] = ""
    return {"summary": payload}


@app.get("/api/days")
def capture_days() -> dict:
    """Dias que possuem memórias processadas, do mais recente ao mais antigo."""
    with connect() as db:
        rows = db.execute(
            """SELECT day,count(*) count FROM (
                 SELECT substr(captured_at,1,10) day FROM captures WHERE status='done'
                 UNION ALL
                 SELECT substr(captured_at,1,10) day FROM video_segments
                   WHERE status='done' AND session_id IS NULL
                 UNION ALL
                 SELECT substr(min(v.captured_at),1,10) day
                   FROM video_sessions s JOIN video_segments v ON v.session_id=s.id
                   WHERE s.status='done' GROUP BY s.id
                 UNION ALL
                 SELECT substr(started_at,1,10) day FROM game_activity_sessions
                   WHERE duration_seconds>0
               ) GROUP BY day ORDER BY day DESC"""
        ).fetchall()
    return {"items": [dict(row) for row in rows]}


@app.get("/api/timeline/{day}")
def hourly_timeline(day: str) -> dict:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise HTTPException(status_code=422, detail="Data inválida")
    with connect() as db:
        rows = db.execute("SELECT * FROM hourly_summaries WHERE substr(hour,1,10)=? ORDER BY hour DESC", (day,)).fetchall()
        source_hours = db.execute(
            """SELECT hour,count(*) count FROM (
                 SELECT substr(captured_at,1,13) hour FROM captures
                   WHERE status='done' AND substr(captured_at,1,10)=?
                 UNION ALL
                 SELECT substr(captured_at,1,13) hour FROM video_segments
                   WHERE status='done' AND session_id IS NULL AND substr(captured_at,1,10)=?
                 UNION ALL
                 SELECT substr(min(v.captured_at),1,13) hour
                   FROM video_sessions s JOIN video_segments v ON v.session_id=s.id
                   WHERE s.status='done' AND substr(v.captured_at,1,10)=? GROUP BY s.id
                 UNION ALL
                 SELECT substr(started_at,1,13) hour FROM game_activity_sessions
                   WHERE duration_seconds>0 AND substr(started_at,1,10)=?
               ) GROUP BY hour""", (day, day, day, day),
        ).fetchall()
    unit = f"lume-hourly@{day}.service"
    return {"hours": [row_dict(row) for row in rows], "source_hours": [dict(row) for row in source_hours], "running": unit_state(unit)["active"]}


@app.get("/api/activities/{day}")
def visual_activities(day: str) -> dict:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise HTTPException(status_code=422, detail="Data inválida")
    with connect() as db:
        sessions = [row_dict(row) for row in db.execute(
            "SELECT * FROM activity_sessions WHERE day=? ORDER BY started_at DESC", (day,)
        ).fetchall()]
        capture_rows = {row["id"]: dict(row) for row in db.execute(
            "SELECT id,source_path,captured_at,title,text,preserved FROM captures WHERE kind='screen' AND substr(captured_at,1,10)=?",
            (day,),
        )}
    for session in sessions:
        frames = []
        for capture_id in session.get("key_capture_ids", []):
            capture = capture_rows.get(capture_id)
            if not capture:
                continue
            source = resolve_media_source(capture["source_path"])
            frames.append({
                "id": capture_id, "captured_at": capture["captured_at"], "title": capture["title"],
                "text": capture["text"], "preserved": bool(capture["preserved"]),
                "available": source.is_file(),
                "url": f"/api/screenshot?path={capture['source_path']}" if source.is_file() else "",
            })
        session["key_frames"] = frames
    return {"items": sessions, "day": day, "running": unit_state(f"lume-hourly@{day}.service")["active"]}


@app.post("/api/timeline/{day}/generate")
def generate_hourly_now(day: str) -> dict:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise HTTPException(status_code=422, detail="Data inválida")
    if unit_state("lume-process.service")["active"]:
        raise HTTPException(status_code=409, detail="O pipeline automático já está usando a GPU")
    result = service_action("start", [f"lume-hourly@{day}.service"], timeout=20, no_block=True)
    if result.returncode != 0:
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao iniciar resumos horários")
    return {"ok": True, "day": day}


@app.get("/api/pipeline/status")
def pipeline_status() -> dict:
    with connect() as db:
        counts = {row["status"]: row["count"] for row in db.execute("SELECT status,count(*) count FROM captures GROUP BY status")}
        last = db.execute("SELECT * FROM pipeline_runs ORDER BY id DESC LIMIT 1").fetchone()
    state = unit_state("lume-process.service")
    return {
        "counts": counts, "last_run": dict(last) if last else None,
        "running": state["active"], "paused": pipeline_pause_flag().is_file(),
    }


@app.post("/api/ollama/unload")
def unload_ollama_models() -> dict:
    listing = run(["ollama", "ps"], timeout=15)
    if listing.returncode != 0:
        raise HTTPException(status_code=503, detail=listing.stderr.strip() or "Não foi possível consultar o Ollama")
    models = []
    for line in listing.stdout.splitlines()[1:]:
        columns = line.split()
        if columns:
            models.append(columns[0])
    failures = []
    for model in models:
        result = run(["ollama", "stop", model], timeout=30)
        if result.returncode != 0:
            failures.append({"model": model, "error": result.stderr.strip() or result.stdout.strip()})
    if failures:
        raise HTTPException(status_code=503, detail=f"Falha ao descarregar: {', '.join(item['model'] for item in failures)}")
    return {"ok": True, "models": models, "unloaded": len(models)}


def capture_speed_stats(db, sample_size: int = 40) -> dict[str, dict[str, int]]:
    """Média recente de análise por tipo, para estimar a duração da fila.

    Só as últimas capturas entram na conta: o tempo depende do modelo e da
    GPU em uso, então uma média histórica completa envelheceria rápido.
    """
    stats: dict[str, dict[str, int]] = {}
    for kind in ("screen", "audio"):
        row = db.execute(
            """SELECT AVG(process_ms) average, COUNT(*) samples FROM (
                 SELECT process_ms FROM captures
                 WHERE kind=? AND status='done' AND process_ms IS NOT NULL AND process_ms>0
                 ORDER BY processed_at DESC, id DESC LIMIT ?)""",
            (kind, sample_size),
        ).fetchone()
        samples = int(row["samples"] or 0)
        stats[kind] = {"avg_ms": round(row["average"]) if samples else 0, "samples": samples}
    return stats


def queue_eta_seconds(counts: dict[str, int], speed: dict[str, dict[str, int]]) -> int | None:
    """Estimativa da fila restante; a execução do worker é sequencial."""
    total = 0.0
    for kind in ("audio", "screen"):
        remaining = counts.get(kind, 0)
        if not remaining:
            continue
        average = speed.get(kind, {}).get("avg_ms", 0)
        if not average:
            return None
        total += remaining * average / 1000
    return round(total) or None


def pipeline_summary_job(db) -> dict:
    """Expose the worker's actual plan; older workers report only saved evidence."""
    job = {"id": "pipeline-summary", "kind": "summary", "title": "Consolidação dos dias", "stage": "Finalizando o processamento"}
    run = db.execute("SELECT * FROM pipeline_runs ORDER BY id DESC LIMIT 1").fetchone()
    if not run or run["status"] != "running":
        return job
    payload = json.loads(dict(run).get("progress_json") or "{}")
    days = payload.get("days", [])
    if days:
        finished = sum(item["status"] in ("done", "error") for item in days)
        errors = sum(item["status"] == "error" for item in days)
        current = next((item for item in days if item["status"] == "processing"), None)
        job.update(days=days, progress=round(finished / len(days) * 100),
                   detail=f"{finished}/{len(days)} dias finalizados · {errors} com falha",
                   updated_at=payload.get("updated_at"))
        if current:
            date = current["day"]
            job.update(title=f"Resumo de {date[8:10]}/{date[5:7]}/{date[:4]}", stage=current["stage"])
        else:
            job["stage"] = "Finalizando lote e limpeza"
        return job
    latest = db.execute(
        """SELECT day,generated_at,stage FROM (
             SELECT day,generated_at,'Análise de imagens salva' stage FROM activity_sessions
             UNION ALL SELECT substr(hour,1,10),generated_at,'Resumo por hora salvo' FROM hourly_summaries
             UNION ALL SELECT day,generated_at,'Resumo do dia salvo' FROM summaries
           ) WHERE julianday(generated_at)>=julianday(?) ORDER BY generated_at DESC LIMIT 1""",
        (run["started_at"],),
    ).fetchone()
    if latest:
        date = latest["day"]
        job.update(stage=f"Último resultado: {latest['stage']} · {date[8:10]}/{date[5:7]}/{date[:4]}",
                   updated_at=latest["generated_at"].replace(" ", "T") + "Z",
                   detail="Lote iniciado antes do acompanhamento detalhado; exibindo o último resultado salvo.")
    else:
        job["stage"] = "Preparando consolidação; aguardando o primeiro resultado"
    return job


@app.get("/api/pipeline/queue")
def pipeline_queue(
    limit: int = Query(default=200, ge=1, le=1000),
    day: str | None = Query(default=None),
) -> dict:
    today = datetime.now().astimezone().date().isoformat()
    tracked_day = day or today
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", tracked_day):
        raise HTTPException(status_code=422, detail="Data inválida")
    process_running = unit_state("lume-process.service")["active"]
    paused = pipeline_pause_flag().is_file()
    daily_state = unit_state(f"lume-summary@{tracked_day}.service")
    hourly_state = unit_state(f"lume-hourly@{tracked_day}.service")
    daily_running = daily_state["active"]
    hourly_running = hourly_state["active"]
    with connect() as db:
        video_rows = db.execute(
            """SELECT id,title,source_path,status,stage,progress,trace_json,error,job_unit,ai_live_thinking,ai_live_content,ai_metrics_json
               FROM video_segments WHERE status IN ('queued','processing','error')
               ORDER BY captured_at"""
        ).fetchall()
        session_rows = db.execute(
            "SELECT id,name,status,stage,progress,trace_json,error,ai_live_thinking,ai_live_content,ai_metrics_json FROM video_sessions WHERE status IN ('queued','processing','error') ORDER BY created_at"
        ).fetchall()
        sequence_rows = db.execute(
            "SELECT id,status,stage,progress,error FROM screen_sequence_jobs WHERE status IN ('queued','processing','error') ORDER BY created_at"
        ).fetchall()
    video_running = any(row["status"] in ("queued", "processing") for row in video_rows) or any(row["status"] in ("queued","processing") for row in session_rows)
    sequence_running = any(row["status"] in ("queued", "processing") for row in sequence_rows)
    running = process_running or daily_running or hourly_running or video_running or sequence_running
    with connect() as db:
        count_rows = db.execute(
            """SELECT kind,status,COUNT(*) total FROM captures
               WHERE status IN ('processing','pending','error')
               GROUP BY kind,status"""
        ).fetchall()
        rows = db.execute(
            """SELECT id,kind,source_path,captured_at,status,error FROM captures
               WHERE status IN ('processing','pending','error')
               ORDER BY CASE status WHEN 'processing' THEN 0 ELSE 1 END,
                        CASE kind WHEN 'audio' THEN 0 ELSE 1 END,
                        captured_at, id LIMIT ?""",
            (limit,),
        ).fetchall()
        speed = capture_speed_stats(db)
    counts = {"audio": 0, "screen": 0, "processing": 0, "pending": 0, "error": 0, "total": 0}
    for row in count_rows:
        amount = int(row["total"])
        counts[row["kind"]] += amount
        counts[row["status"]] += amount
        counts["total"] += amount
    speed_payload = {**speed, "eta_seconds": queue_eta_seconds(counts, speed)}
    items = []
    for position, row in enumerate(rows, 1):
        item = dict(row)
        item["name"] = media_source_name(item["source_path"])
        item["url"] = f"/api/{'screenshot' if item['kind'] == 'screen' else 'audio'}?path={item['source_path']}"
        item["position"] = position
        item["stage"] = (("Transcrevendo áudio com Whisper" if item["kind"] == "audio" else "Analisando imagem com Qwen-VL") if running else "Execução interrompida; será recolocado na fila") if item["status"] == "processing" else ("Falhou; aguardando nova tentativa" if item["status"] == "error" else ("Pausado; aguardando retomada" if paused else "Aguardando processamento"))
        items.append(item)
    jobs = []
    if daily_running:
        jobs.append({"id": f"daily-summary-{tracked_day}", "stage": f"Resumindo períodos e consolidando o dia {tracked_day[8:10]}/{tracked_day[5:7]}/{tracked_day[:4]} com Qwen", "kind": "summary"})
    if hourly_running:
        jobs.append({"id": f"hourly-summary-{tracked_day}", "stage": f"Gerando resumos por hora de {tracked_day[8:10]}/{tracked_day[5:7]}/{tracked_day[:4]} com Qwen", "kind": "hourly"})
    elif hourly_state["active_state"] == "failed":
        jobs.append({"id": f"hourly-summary-error-{tracked_day}", "stage": f"Falha ao gerar resumos horários de {tracked_day[8:10]}/{tracked_day[5:7]}; tente atualizar novamente", "kind": "hourly", "status": "error"})
    if not daily_running and daily_state["active_state"] == "failed":
        jobs.append({"id": f"daily-summary-error-{tracked_day}", "stage": f"Falha ao gerar o resumo de {tracked_day[8:10]}/{tracked_day[5:7]}; tente novamente", "kind": "summary", "status": "error"})
    if process_running and not items and not video_running:
        with connect() as db:
            jobs.append(pipeline_summary_job(db))
    for row in video_rows:
        jobs.append({
            "id": f"video-{row['id']}", "video_id": row["id"], "kind": "video",
            "stage": row["stage"] or ("Falha na análise" if row["status"] == "error" else "Preparando vídeo"),
            "title": row["title"] or media_source_name(row["source_path"]),
            "progress": row["progress"], "trace": json.loads(row["trace_json"] or "[]"),
            "status": "error" if row["status"] == "error" else "processing",
            "error": row["error"],
            "ai_thinking": row["ai_live_thinking"], "ai_content": row["ai_live_content"],
            "ai_metrics": json.loads(row["ai_metrics_json"] or "{}"),
        })
    for row in session_rows:
        jobs.append({
            "id": f"session-{row['id']}", "session_id": row["id"], "kind": "video",
            "stage": row["stage"], "title": row["name"], "progress": row["progress"],
            "trace": json.loads(row["trace_json"] or "[]"),
            "status": "error" if row["status"] == "error" else "processing", "error": row["error"],
            "ai_thinking": row["ai_live_thinking"], "ai_content": row["ai_live_content"],
            "ai_metrics": json.loads(row["ai_metrics_json"] or "{}"),
        })
    for row in sequence_rows:
        jobs.append({
            "id": f"screen-sequence-{row['id']}", "sequence_id": row["id"], "kind": "screen_sequence",
            "stage": row["stage"], "title": "Análise de sequência de telas", "progress": row["progress"],
            "status": "error" if row["status"] == "error" else "processing", "error": row["error"],
        })
    phase = "processing" if process_running and items and any(item["status"] == "processing" for item in items) else ("summarizing" if jobs else "idle")
    return {
        "items": items, "jobs": jobs, "total": counts["total"], "shown": len(items), "counts": counts,
        "speed": speed_payload, "running": running, "worker_running": process_running, "paused": paused,
        "phase": phase, "day": tracked_day,
    }


@app.post("/api/pipeline/pause")
def pause_pipeline() -> dict:
    """Interrompe o worker, mas preserva e reagenda tudo para retomada."""
    flag = pipeline_pause_flag()
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.write_text("paused\n", encoding="utf-8")
    if unit_state("lume-process.service")["active"]:
        result = service_action("stop", ["lume-process.service"], timeout=30)
        if result.returncode != 0:
            flag.unlink(missing_ok=True)
            raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao pausar processamento")
    with connect() as db:
        captures = db.execute(
            "UPDATE captures SET status='pending',error='pausado; aguardando retomada' WHERE status='processing'"
        ).rowcount
        videos = db.execute(
            """UPDATE video_segments SET status='queued',stage='Pausado; aguardando retomada',
               error='' WHERE status='processing' AND job_unit='lume-process.service'"""
        ).rowcount
        sessions = db.execute(
            """UPDATE video_sessions SET status='queued',stage='Pausada; aguardando retomada',
               error='' WHERE status='processing' AND job_unit='lume-process.service'"""
        ).rowcount
        db.execute(
            """UPDATE pipeline_runs SET status='paused',finished_at=CURRENT_TIMESTAMP,
               error='pausado manualmente' WHERE status='running'"""
        )
    return {"ok": True, "paused": True, "requeued": captures + videos + sessions}


@app.post("/api/pipeline/resume")
def resume_pipeline() -> dict:
    """Remove a pausa persistente e continua usando a mesma fila."""
    flag = pipeline_pause_flag()
    flag.unlink(missing_ok=True)
    if unit_state("lume-process.service")["active"]:
        return {"ok": True, "paused": False, "already_running": True}
    result = service_action("start", ["lume-process.service"], timeout=20, no_block=True)
    if result.returncode != 0:
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.write_text("paused\n", encoding="utf-8")
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao retomar processamento")
    return {"ok": True, "paused": False, "already_running": False}


@app.post("/api/pipeline/cancel")
def cancel_pipeline(day: str | None = Query(default=None)) -> dict:
    today = datetime.now().astimezone().date().isoformat()
    tracked_day = day or today
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", tracked_day):
        raise HTTPException(status_code=422, detail="Data inválida")
    with connect() as db:
        video_units = [row["job_unit"] for row in db.execute("SELECT job_unit FROM video_segments WHERE status IN ('queued','processing') AND job_unit<>''")]
        session_units = [row["job_unit"] for row in db.execute("SELECT job_unit FROM video_sessions WHERE status IN ('queued','processing') AND job_unit<>''")]
        sequence_units = [row["job_unit"] for row in db.execute("SELECT job_unit FROM screen_sequence_jobs WHERE status IN ('queued','processing') AND job_unit<>''")]
    result = service_action("stop", ["lume-process.service", f"lume-summary@{tracked_day}.service", f"lume-hourly@{tracked_day}.service", *video_units, *session_units, *sequence_units], timeout=30)
    if result.returncode != 0:
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao parar processamento")
    with connect() as db:
        resumed = db.execute(
            "UPDATE captures SET status='pending',error='processamento cancelado; aguardando retomada' WHERE status='processing'"
        ).rowcount
        db.execute("UPDATE pipeline_runs SET status='cancelled',finished_at=CURRENT_TIMESTAMP,error='cancelado manualmente' WHERE status='running'")
        db.execute("UPDATE video_segments SET status='cancelled',stage='Cancelado pelo usuário',error='análise cancelada manualmente' WHERE status IN ('queued','processing')")
        db.execute("UPDATE video_sessions SET status='cancelled',stage='Cancelada pelo usuário',error='sessão cancelada manualmente' WHERE status IN ('queued','processing')")
        db.execute("UPDATE screen_sequence_jobs SET status='cancelled',stage='Cancelado pelo usuário',error='análise cancelada manualmente' WHERE status IN ('queued','processing')")
    return {"ok": True, "resumed": resumed}


@app.delete("/api/pipeline/queue")
def cancel_entire_queue() -> dict:
    today = datetime.now().astimezone().date().isoformat()
    with connect() as db:
        sequence_units = [row["job_unit"] for row in db.execute("SELECT job_unit FROM screen_sequence_jobs WHERE status IN ('queued','processing') AND job_unit<>''")]
        video_units = [row["job_unit"] for row in db.execute("SELECT job_unit FROM video_segments WHERE status IN ('queued','processing') AND job_unit<>''")]
        session_units = [row["job_unit"] for row in db.execute("SELECT job_unit FROM video_sessions WHERE status IN ('queued','processing') AND job_unit<>''")]
    result = service_action("stop", ["lume-process.service", f"lume-summary@{today}.service", f"lume-hourly@{today}.service", *video_units, *session_units, *sequence_units], timeout=30)
    if result.returncode != 0:
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao parar processamento")
    with connect() as db:
        cancelled = db.execute(
            """UPDATE captures SET status='skipped',error='fila cancelada manualmente',processed_at=CURRENT_TIMESTAMP
               WHERE status IN ('pending','processing','error')"""
        ).rowcount
        db.execute("UPDATE pipeline_runs SET status='cancelled',finished_at=CURRENT_TIMESTAMP,error='fila cancelada manualmente' WHERE status='running'")
        cancelled += db.execute("UPDATE video_segments SET status='cancelled',stage='Cancelado pelo usuário',error='fila cancelada manualmente' WHERE status IN ('queued','processing','error')").rowcount
        cancelled += db.execute("UPDATE video_sessions SET status='cancelled',stage='Cancelada pelo usuário',error='fila cancelada manualmente' WHERE status IN ('queued','processing','error')").rowcount
        cancelled += db.execute("UPDATE screen_sequence_jobs SET status='cancelled',stage='Cancelado pelo usuário',error='fila cancelada manualmente' WHERE status IN ('queued','processing','error')").rowcount
    pipeline_pause_flag().unlink(missing_ok=True)
    return {"ok": True, "cancelled": cancelled}


@app.delete("/api/pipeline/queue/{capture_id}")
def cancel_queue_item(capture_id: int) -> dict:
    with connect() as db:
        row = db.execute("SELECT id,status FROM captures WHERE id=?", (capture_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    if row["status"] == "processing":
        result = service_action("stop", ["lume-process.service"], timeout=30)
        if result.returncode != 0:
            raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao parar item ativo")
    with connect() as db:
        db.execute(
            "UPDATE captures SET status='skipped',error='removido manualmente da fila',processed_at=CURRENT_TIMESTAMP WHERE id=? AND status IN ('pending','processing','error')",
            (capture_id,),
        )
        if row["status"] == "processing":
            db.execute("UPDATE captures SET status='pending',error='reagendado após cancelamento de outro item' WHERE status='processing' AND id<>?", (capture_id,))
    return {"ok": True, "id": capture_id}


@app.post("/api/pipeline/run")
def pipeline_run(payload: PipelineRequest) -> dict:
    result = service_action("start", ["lume-process.service"], timeout=20, no_block=True)
    if result.returncode != 0:
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao iniciar processamento")
    return {"ok": True, "note": "Limites são definidos na unit noturna", "requested": payload}


@app.post("/api/pipeline/enqueue-unprocessed")
def enqueue_unprocessed() -> dict:
    """Enfileira toda mídia ainda não analisada e inicia o worker único."""
    if pipeline_pause_flag().is_file():
        raise HTTPException(status_code=409, detail="O worker está pausado; use Retomar worker para continuar a fila existente")
    if unit_state("lume-process.service")["active"]:
        raise HTTPException(status_code=409, detail="O processamento automático já está em execução")
    with connect() as db:
        video_busy = db.execute(
            "SELECT 1 FROM video_segments WHERE status IN ('queued','processing') LIMIT 1"
        ).fetchone() or db.execute(
            "SELECT 1 FROM video_sessions WHERE status IN ('queued','processing') LIMIT 1"
        ).fetchone()
    if video_busy:
        raise HTTPException(status_code=409, detail="A IA está analisando um vídeo; aguarde para processar telas e áudios")

    # Import local evita carregar o pipeline pesado durante a inicialização
    # da API. A descoberta só registra arquivos; o worker faz a análise.
    from .pipeline import discover
    discovered = discover(audio_recording=bool(unit_state("captura-dia-audio.service")["active"]))
    # A listagem também registra vídeos novos e associa automaticamente os
    # clipes gravados às suas sessões. O retorno volumoso não é necessário aqui.
    list_videos()
    with connect() as db:
        # ``discover`` usa INSERT OR IGNORE, portanto uma captura removida ou
        # cancelada anteriormente continua como ``skipped``. Recupere registros
        # de qualquer data somente quando a mídia bruta ainda existir; entradas
        # órfãs não devem ocupar a fila nem virar um erro do worker.
        candidates = db.execute(
            """SELECT id,status,source_path FROM captures
               WHERE status NOT IN ('done','processing')"""
        ).fetchall()
        existing = [row for row in candidates if resolve_media_source(row["source_path"]).is_file()]
        missing = [row for row in candidates if not resolve_media_source(row["source_path"]).is_file()]
        requeued = sum(row["status"] not in ("pending", "error") for row in existing)
        db.executemany(
            "UPDATE captures SET status='pending',error='',processed_at=NULL WHERE id=?",
            [(row["id"],) for row in existing],
        )
        db.executemany(
            """UPDATE captures SET status='skipped',error='arquivo bruto não existe mais',
               processed_at=CURRENT_TIMESTAMP WHERE id=?""",
            [(row["id"],) for row in missing],
        )
        session_candidates = db.execute(
            """SELECT s.id FROM video_sessions s
               WHERE s.status NOT IN ('done','processing','queued')
                 AND EXISTS(SELECT 1 FROM video_segments v WHERE v.session_id=s.id)"""
        ).fetchall()
        session_clips = db.execute(
            """SELECT session_id,status,source_path FROM video_segments
               WHERE session_id IN (SELECT id FROM video_sessions
                 WHERE status NOT IN ('done','processing','queued'))"""
        ).fetchall()
        missing_session_ids = {
            row["session_id"] for row in session_clips
            if row["status"] != "done" and not resolve_media_source(row["source_path"]).is_file()
        }
        session_rows = [row for row in session_candidates if row["id"] not in missing_session_ids]
        missing_sessions = [row for row in session_candidates if row["id"] in missing_session_ids]
        video_rows = db.execute(
            """SELECT id,source_path FROM video_segments
               WHERE session_id IS NULL AND status NOT IN ('done','processing','queued')"""
        ).fetchall()
        available_videos = [row for row in video_rows if resolve_media_source(row["source_path"]).is_file()]
        missing_videos = [row for row in video_rows if not resolve_media_source(row["source_path"]).is_file()]
        db.executemany(
            """UPDATE video_sessions SET status='queued',stage='Aguardando processamento geral',progress=0,
               trace_json='[]',job_unit='lume-process.service',error='' WHERE id=?""",
            [(row["id"],) for row in session_rows],
        )
        db.executemany(
            """UPDATE video_sessions SET status='cancelled',stage='Clipe indisponível',
               error='um ou mais arquivos brutos não existem mais' WHERE id=?""",
            [(row["id"],) for row in missing_sessions],
        )
        db.executemany(
            """UPDATE video_segments SET status='queued',stage='Aguardando processamento geral',progress=0,
               trace_json='[]',job_unit='lume-process.service',error='' WHERE id=?""",
            [(row["id"],) for row in available_videos],
        )
        db.executemany(
            """UPDATE video_segments SET status='cancelled',stage='Arquivo indisponível',
               error='arquivo bruto não existe mais' WHERE id=?""",
            [(row["id"],) for row in missing_videos],
        )
        queued = {
            row["kind"]: row["count"]
            for row in db.execute(
                """SELECT kind,count(*) count FROM captures
                   WHERE status IN ('pending','error') GROUP BY kind"""
            )
        }
    result = service_action("start", ["lume-process.service"], timeout=20, no_block=True)
    if result.returncode != 0:
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao iniciar processamento")
    audio = int(queued.get("audio", 0))
    screen = int(queued.get("screen", 0))
    videos = len(available_videos)
    sessions = len(session_rows)
    return {
        "ok": True,
        "discovered": discovered,
        "requeued": requeued,
        "missing": len(missing) + len(missing_videos) + len(missing_sessions),
        "queued": {"audio": audio, "screen": screen, "video": videos, "session": sessions,
                   "total": audio + screen + videos + sessions},
        "note": "Todos os arquivos não processados foram adicionados; processamento iniciado em segundo plano",
    }


@app.post("/api/summary/{day}/generate")
def generate_summary_now(day: str) -> dict:
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
        raise HTTPException(status_code=422, detail="Data inválida")
    with connect() as db:
        source_count = db.execute(
            "SELECT count(*) FROM captures WHERE status='done' AND substr(captured_at,1,10)=?",
            (day,),
        ).fetchone()[0]
    if not source_count:
        formatted = datetime.strptime(day, "%Y-%m-%d").strftime("%d/%m/%Y")
        raise HTTPException(
            status_code=422,
            detail=f"Não há capturas processadas em {formatted}. Selecione um dia com dados.",
        )
    if unit_state("lume-process.service")["active"]:
        raise HTTPException(status_code=409, detail="A GPU está processando a fila; gere o resumo quando ela terminar")
    result = service_action("start", [f"lume-summary@{day}.service"], timeout=20, no_block=True)
    if result.returncode != 0:
        raise HTTPException(status_code=503, detail=result.stderr.strip() or "Falha ao iniciar resumo")
    return {"ok": True, "day": day, "note": "Resumo iniciado em segundo plano"}


FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
