from __future__ import annotations

import argparse
import base64
import math
import hashlib
import json
import re
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import wave
from datetime import datetime, timedelta
from pathlib import Path

import numpy

from ..capture.imagediff import compare_images
from .audio_intelligence import analyze_video_audio
from .database import connect, initialize
from .main_paths import AUDIO_DIR, CONFIG_DIR, SCREEN_DIR, VIDEO_DIR, media_source_key, resolve_media_source
from . import prompts
from .retention import cleanup_processed_capture_media, cleanup_settings, mark_capture_cleanup_ready
from . import tags as tag_vocabulary
from .runtime import exclusive_lock, pipeline_pause_flag, runtime_dir

DEFAULT_WHISPER_BIN = (
    Path.home() / "whisper.cpp" / "build" / "bin"
    / ("whisper-cli.exe" if os.name == "nt" else "whisper-cli")
)
WHISPER_BIN = Path(os.environ.get("WHISPER_BIN", DEFAULT_WHISPER_BIN))
WHISPER_MODEL = Path(os.environ.get("WHISPER_MODEL", Path.home() / "whisper.cpp/models/ggml-large-v3-turbo-q5_0.bin"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
DEFAULT_VISION_MODEL = "qwen3-vl-ctx:latest"
DEFAULT_TEXT_MODEL = "qwen3.5:9b"
LOCK_PATH = runtime_dir() / "lume-process.lock"
AI_LIVE_VIDEO_PATH: str | None = None
AI_LIVE_SESSION_ID: int | None = None
AI_LIVE_LAST_WRITE = 0.0
MAX_VISION_IMAGES_PER_REQUEST = 16
ACTIVITY_CONTEXT_FRAMES = 3
ACTIVITY_BATCH_FRAMES = MAX_VISION_IMAGES_PER_REQUEST - ACTIVITY_CONTEXT_FRAMES


def _run_hidden(*args, **kwargs):
    kwargs.setdefault("creationflags", getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if kwargs.get("text"):
        # O whisper imprime UTF-8; sem isto o Python decodifica pelo locale do
        # Windows (cp1252) e estoura em qualquer acento da transcrição.
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("errors", "replace")
    return subprocess.run(*args, **kwargs)


def publish_ai_live(thinking: str, content: str, metrics: dict | None = None, force: bool = False) -> None:
    global AI_LIVE_LAST_WRITE
    now = time.monotonic()
    if not force and now - AI_LIVE_LAST_WRITE < 0.5:
        return
    AI_LIVE_LAST_WRITE = now
    values = (thinking[-16000:], content[-10000:], json.dumps(metrics or {}, ensure_ascii=False))
    with connect() as db:
        if AI_LIVE_VIDEO_PATH:
            db.execute("UPDATE video_segments SET ai_live_thinking=?,ai_live_content=?,ai_metrics_json=? WHERE source_path=?", (*values, AI_LIVE_VIDEO_PATH))
        if AI_LIVE_SESSION_ID is not None:
            db.execute("UPDATE video_sessions SET ai_live_thinking=?,ai_live_content=?,ai_metrics_json=? WHERE id=?", (*values, AI_LIVE_SESSION_ID))


def update_video_progress(path: Path, stage: str, progress: int, event: dict | None = None) -> None:
    source_key = media_source_key(path)
    with connect() as db:
        row = db.execute("SELECT trace_json FROM video_segments WHERE source_path=?", (source_key,)).fetchone()
        trace = json.loads(row["trace_json"] or "[]") if row else []
        if event:
            trace.append({"time": datetime.now().astimezone().isoformat(), **event})
            trace = trace[-100:]
        db.execute(
            "UPDATE video_segments SET stage=?,progress=?,trace_json=? WHERE source_path=?",
            (stage, max(0, min(100, progress)), json.dumps(trace, ensure_ascii=False), source_key),
        )


def video_config() -> dict[str, str]:
    values: dict[str,str] = {}; path=CONFIG_DIR/"video.conf"
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.lstrip().startswith("#") and "=" in line:
                key,value=line.split("=",1);values[key.strip()]=value.strip().strip("\"'")
    return values


def vision_model() -> str:
    return os.environ.get("LUME_VISION_MODEL") or video_config().get("LUME_VISION_MODEL", DEFAULT_VISION_MODEL)


def text_model() -> str:
    return os.environ.get("LUME_TEXT_MODEL") or video_config().get("LUME_TEXT_MODEL", DEFAULT_TEXT_MODEL)


def timestamp_from_name(path: Path) -> datetime:
    match = re.search(r"(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})", path.name)
    if match:
        return datetime.strptime("_".join(match.groups()), "%Y-%m-%d_%H-%M-%S").astimezone()
    match = re.search(r"audio-(\d{8})-(\d{6})", path.name)
    if match:
        return datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S").astimezone()
    return datetime.fromtimestamp(path.stat().st_mtime).astimezone()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def discover(audio_recording: bool | None = None) -> dict[str, int]:
    initialize()
    audio_files = sorted(AUDIO_DIR.glob("*.wav"), key=lambda p: p.stat().st_mtime)
    # A API conhece o estado do gravador. No worker independente, preserve o
    # segmento recém-escrito, mas não deixe o último WAV parado fora do índice
    # para sempre depois de a captura encerrar.
    newest_audio = audio_files[-1] if audio_files else None
    active_audio = newest_audio if newest_audio and (
        audio_recording is True or
        (audio_recording is None and time.time() - newest_audio.stat().st_mtime < 30)
    ) else None
    counts = {"audio": 0, "screen": 0, "deferred_audio": int(active_audio is not None)}
    with connect() as db:
        for kind, files in (("audio", audio_files), ("screen", sorted(SCREEN_DIR.glob("*.png")))):
            for path in files:
                if kind == "audio" and path == active_audio:
                    continue
                captured = timestamp_from_name(path).isoformat()
                cursor = db.execute(
                    "INSERT OR IGNORE INTO captures(kind,source_path,captured_at,status) VALUES(?,?,?,'pending')",
                    (kind, media_source_key(path), captured),
                )
                counts[kind] += cursor.rowcount
    return counts


# O Ollama devolve, por chamada, quanto tempo foi carregar o modelo, quanto foi
# ler o prompt (que num modelo de visão inclui codificar a imagem) e quanto foi
# gerar a resposta. Sem essa divisão não dá para saber se encurtar um prompt
# adianta alguma coisa. O acumulador soma as chamadas de uma mesma análise --
# ``ollama_json`` pode repetir a chamada para consertar um JSON quebrado -- e o
# worker processa um item por vez, então um dicionário de módulo basta.
_CALL_METRICS: dict[str, object] = {}


def clear_call_metrics() -> None:
    _CALL_METRICS.clear()


def last_call_metrics() -> dict:
    return dict(_CALL_METRICS)


def _record_call_metrics(model: str, payload: dict) -> None:
    def milliseconds(key: str) -> int:
        return round(payload.get(key, 0) / 1_000_000)

    _CALL_METRICS["model"] = model
    _CALL_METRICS["calls"] = int(_CALL_METRICS.get("calls", 0)) + 1
    for key, source in (
        ("prompt_tokens", "prompt_eval_count"),
        ("generated_tokens", "eval_count"),
    ):
        _CALL_METRICS[key] = int(_CALL_METRICS.get(key, 0)) + int(payload.get(source, 0) or 0)
    for key, source in (
        ("load_ms", "load_duration"),
        ("prompt_ms", "prompt_eval_duration"),
        ("eval_ms", "eval_duration"),
        ("total_ms", "total_duration"),
    ):
        _CALL_METRICS[key] = int(_CALL_METRICS.get(key, 0)) + milliseconds(source)


def ollama_chat(model: str, messages: list[dict], timeout: int = 300, num_ctx: int = 16384, think: bool | None = None) -> str:
    thinking = video_config().get("AI_THINKING_ENABLED", "false") == "true" if think is None else think
    localized_messages = messages if any(message.get("role") == "system" for message in messages) else [{
        "role": "system",
        "content": "Responda sempre em português do Brasil. Escreva também em pt-BR todos os valores textuais de JSON, incluindo títulos, descrições, resumos, eventos, explicações e consultas. Preserve apenas nomes próprios, termos oficiais e trechos citados no idioma original.",
    }, *messages]
    body = json.dumps({
        "model": model, "stream": True, "think": thinking, "format": "json", "messages": localized_messages,
        "options": {"temperature": 0.05, "num_ctx": num_ctx, "num_predict": 8192},
    }).encode()
    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat", data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        thinking = ""; content = ""; final_payload = {}
        publish_ai_live("", "", {"model": model, "status": "generating"}, force=True)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            for raw_line in response:
                if not raw_line.strip():
                    continue
                payload = json.loads(raw_line)
                message = payload.get("message", {})
                thinking += message.get("thinking") or ""
                content += message.get("content") or ""
                if payload.get("done"):
                    final_payload = payload
                publish_ai_live(thinking, content, {"model": model, "status": "generating"})
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8", errors="replace").strip()
        except OSError:
            detail = ""
        message = f"Ollama recusou a requisição (HTTP {exc.code})"
        if detail:
            message += f": {detail[:2000]}"
        raise RuntimeError(message) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(f"Ollama indisponível: {exc}") from exc
    metrics = {"model": model, "status": "done", "prompt_tokens": final_payload.get("prompt_eval_count", 0), "generated_tokens": final_payload.get("eval_count", 0), "total_duration_ms": round(final_payload.get("total_duration", 0) / 1_000_000), "eval_duration_ms": round(final_payload.get("eval_duration", 0) / 1_000_000), "prompt_duration_ms": round(final_payload.get("prompt_eval_duration", 0) / 1_000_000), "load_duration_ms": round(final_payload.get("load_duration", 0) / 1_000_000)}
    _record_call_metrics(model, final_payload)
    publish_ai_live(thinking, content, metrics, force=True)
    had_content = bool(content.strip())
    content = recover_json_from_thinking(content, thinking)
    if content and not had_content:
        metrics["content_source"] = "thinking_fallback"
        publish_ai_live(thinking, content, metrics, force=True)
    if not content:
        raise RuntimeError("Ollama retornou conteúdo vazio")
    return content


def context_overflow(exc: Exception) -> bool:
    """O Ollama recusa o lote inteiro quando as imagens não cabem no ``num_ctx``."""
    return "exceed_context_size" in str(exc) or "exceeds the available context size" in str(exc)


def parse_json_response(text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.I | re.S)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start < 0 or end < start:
        raise ValueError("modelo não retornou JSON")
    return json.loads(cleaned[start:end + 1])


def recover_json_from_thinking(content: str, thinking: str) -> str:
    """Recupera JSON que o parser do Ollama classificou todo como thinking."""
    content = content.strip()
    if content:
        return content
    candidate = thinking.strip()
    if not candidate:
        return ""
    try:
        parse_json_response(candidate)
    except (json.JSONDecodeError, ValueError):
        return ""
    return candidate


def ollama_json(model: str, messages: list[dict], timeout: int = 300, num_ctx: int = 16384, think: bool | None = None) -> dict:
    response = ollama_chat(model, messages, timeout=timeout, num_ctx=num_ctx, think=think)
    for attempt in range(3):
        try:
            return parse_json_response(response)
        except (json.JSONDecodeError, ValueError):
            if attempt == 2:
                raise
            response = ollama_chat(model, [{
                "role": "user",
                "content": "Corrija a sintaxe deste JSON sem alterar os fatos. Responda apenas com o objeto JSON válido:\n" + response[:30000],
            }], timeout=timeout, num_ctx=num_ctx, think=False)
    raise ValueError("não foi possível obter JSON válido")


def searxng_search(base_url: str, query: str, limit: int = 5) -> list[dict]:
    url = base_url.rstrip("/") + "/search?" + urllib.parse.urlencode({"q": query, "format": "json", "language": "pt-BR", "safesearch": 1})
    request = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "Lume/0.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.load(response)
    return [{"title": str(item.get("title") or "")[:300], "url": str(item.get("url") or "")[:2000], "snippet": str(item.get("content") or "")[:1000], "query": query} for item in payload.get("results", [])[:limit] if item.get("url")]


def private_context_terms(context: str) -> set[str]:
    terms: set[str] = set()
    patterns = (
        r"(?:jogando|joguei|estava)\s+com\s+(?:o\s+|a\s+)?@?([\wÀ-ÿ.-]{2,})",
        r"(?:meu|minha)\s+(?:amigo|amiga|colega)\s+@?([\wÀ-ÿ.-]{2,})",
        r"(?:amigo|amiga|colega)\s+(?:chamado|chamada)?\s*@?([\wÀ-ÿ.-]{2,})",
    )
    for pattern in patterns:
        terms.update(match.casefold() for match in re.findall(pattern, context, flags=re.I))
    terms.update(match.casefold() for match in re.findall(r"@[\w.-]{2,}", context))
    return {term.lstrip("@") for term in terms if term not in {"ele", "ela", "eles", "elas"}}


def safe_research_query(query: str, private_terms: set[str]) -> bool:
    lowered = query.casefold()
    identity_intents = ("quem é", "who is", "instagram", "linkedin", "facebook", "twitter", "tiktok", "perfil", "profile", "biografia", "biography", "idade", "famos", "competitive status", "pro player", "estatísticas do jogador")
    if any(intent in lowered for intent in identity_intents):
        return False
    return not any(re.search(rf"(?<!\w){re.escape(term)}(?!\w)", lowered) for term in private_terms)


def adaptive_web_research(facts: str, user_context: str, config: dict[str, str], cache: dict[str, list[dict]], state: dict | None = None) -> dict:
    if config.get("VIDEO_WEB_SEARCH_ENABLED", "false") != "true":
        return {"findings": "", "sources": [], "queries": []}
    base_url = config.get("SEARXNG_URL", "http://127.0.0.1:8889")
    safety_limit = max(5, min(500, int(config.get("VIDEO_WEB_SEARCH_SAFETY_LIMIT", "50"))))
    state = state if state is not None else {"query_count": 0}
    private_terms = private_context_terms(user_context)
    safe_facts = facts
    for term in private_terms:
        safe_facts = re.sub(rf"(?i)(?<!\w){re.escape(term)}(?!\w)", "[pessoa mencionada]", safe_facts)
    sources: list[dict] = []; queries: list[str] = []; seen_urls: set[str] = set()
    while state.get("query_count", 0) < safety_limit:
        evidence = "\n".join(f"- {item['title']}: {item['snippet']}" for item in sources[-30:]) or "(nenhuma pesquisa feita)"
        plan = ollama_json(text_model(), [{"role": "user", "content": prompts.render(
            "web_research_plan",
            fatos=safe_facts[:12000],
            consultas_anteriores=json.dumps(queries, ensure_ascii=False),
            resultados=evidence[:16000],
        )}], timeout=180, num_ctx=16384, think=False)
        proposed = [str(item).strip() for item in plan.get("queries", []) if str(item).strip()]
        unique = [item for item in proposed if item.casefold() not in {old.casefold() for old in queries} and safe_research_query(item, private_terms)]
        if not plan.get("continue") or not unique:
            break
        sources_before = len(sources)
        for query in unique[:safety_limit-state.get("query_count", 0)]:
            queries.append(query)
            state["query_count"] = state.get("query_count", 0) + 1
            try:
                cache_key = query.casefold()
                if cache_key not in cache:
                    cache[cache_key] = searxng_search(base_url, query)
                results = cache[cache_key]
            except (urllib.error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
                results = []
            for item in results:
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"]);sources.append(item)
        if len(sources) == sources_before:
            break
    if not sources:
        return {"findings": "", "sources": [], "queries": queries}
    synthesis = ollama_json(text_model(), [{"role": "user", "content": prompts.render(
        "web_research_synthesis",
        fatos=safe_facts[:12000],
        resultados=json.dumps(sources, ensure_ascii=False)[:30000],
    )}], timeout=240, num_ctx=24576, think=False)
    useful = set(str(url) for url in synthesis.get("useful_urls", []))
    selected = [item for item in sources if not useful or item["url"] in useful]
    return {"findings": str(synthesis.get("findings") or ""), "sources": selected[:12], "queries": queries}


def normalized_transcript_text(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    folded = "".join(character for character in folded if not unicodedata.combining(character))
    return " ".join(re.findall(r"[a-z0-9]+", folded, re.UNICODE))


# Créditos de legendagem que o Whisper.cpp costuma emitir sobre silêncio e
# ruído ambiente. São assinaturas completas e estreitas de propósito: remover
# qualquer frase que apenas contenha a palavra "legenda" apagaria fala real.
_KNOWN_WHISPER_HALLUCINATIONS = {
    "legenda por sonia ruberti",
    "legendas por sonia ruberti",
    "legendas pela comunidade amara org",
    "subtitles by the amara org community",
}


def filter_hallucinated_segments(segments: list[dict]) -> list[dict]:
    """Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas."""
    if not segments:
        return []
    keys = [normalized_transcript_text(str(item.get("text") or "")) for item in segments]
    counts: dict[str, int] = {}
    for key in keys:
        if key:
            counts[key] = counts.get(key, 0) + 1
    pathological = {
        key for key, count in counts.items()
        if count >= 5 and count / max(1, len(segments)) >= 0.45
    }
    rejected: set[int] = set()
    start = 0
    while start < len(segments):
        end = start + 1
        while end < len(segments) and keys[end] == keys[start] and keys[start]:
            end += 1
        if end - start >= 3:
            rejected.update(range(start, end))
        start = end
    return [
        item for index, item in enumerate(segments)
        if (keys[index] and keys[index] not in _KNOWN_WHISPER_HALLUCINATIONS
            and keys[index] not in pathological and index not in rejected)
    ]


def audio_channel_count(path: Path) -> int:
    try:
        with wave.open(str(path), "rb") as source:
            return source.getnchannels()
    except (wave.Error, OSError):
        return 1


def audio_stream_count(path: Path) -> int:
    """Quantidade de streams de áudio em contêineres como MKV/MP4."""
    try:
        result = _run_hidden([
            "ffprobe", "-v", "error", "-select_streams", "a",
            "-show_entries", "stream=index", "-of", "csv=p=0", str(path),
        ], capture_output=True, text=True, timeout=30)
        return len([line for line in result.stdout.splitlines() if line.strip()])
    except (OSError, subprocess.SubprocessError):
        return 0


def compact_processed_audio(path: Path) -> bool:
    """Collapse a processed multichannel WAV to mono without risking the source.

    The temporary three-channel recording is kept until ffmpeg finishes and the
    replacement has been checked for format and duration.  ``os.replace`` is
    atomic on the same volume, so an interrupted conversion cannot leave a
    half-written capture at the original path.
    """
    channels = audio_channel_count(path)
    if channels < 2:
        return False
    try:
        with wave.open(str(path), "rb") as source:
            source_duration = source.getnframes() / max(1, source.getframerate())
    except (wave.Error, OSError) as exc:
        raise RuntimeError(f"não foi possível validar o áudio multifaixa: {exc}") from exc

    temporary = path.with_name(f".{path.stem}.mono-{os.getpid()}.wav")
    inputs = "+".join(f"c{index}" for index in range(channels))
    try:
        converted = _run_hidden([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path),
            "-af", f"pan=mono|c0={inputs},alimiter=limit=0.95",
            "-ar", "16000", "-c:a", "pcm_s16le", str(temporary),
        ], capture_output=True, text=True, timeout=1800)
        if converted.returncode != 0 or not temporary.is_file():
            raise RuntimeError((converted.stderr or "ffmpeg não gerou o áudio mono")[-2000:])
        with wave.open(str(temporary), "rb") as result:
            result_duration = result.getnframes() / max(1, result.getframerate())
            valid_format = result.getnchannels() == 1 and result.getframerate() == 16000
        duration_tolerance = max(0.25, source_duration * 0.01)
        if not valid_format or abs(result_duration - source_duration) > duration_tolerance:
            raise RuntimeError(
                f"áudio mono inválido (duração {result_duration:.3f}s; esperada {source_duration:.3f}s)"
            )
        os.replace(temporary, path)
        return True
    finally:
        temporary.unlink(missing_ok=True)


def compact_saved_capture(path: Path, capture_id: int) -> bool:
    """Compacta uma captura concluída e registra o novo hash ou um aviso."""
    try:
        compacted = compact_processed_audio(path)
        if compacted:
            with connect() as db:
                db.execute("UPDATE captures SET sha256=?,error='' WHERE id=?", (sha256(path), capture_id))
        return compacted
    except Exception as exc:
        # O processamento já terminou. Preserve o multicanal se a compactação
        # falhar, sem descartar a transcrição e a diarização recém-gravadas.
        with connect() as db:
            db.execute(
                "UPDATE captures SET error=? WHERE id=? AND status='done'",
                (f"processado; áudio multifaixa preservado porque a compactação falhou: {str(exc)[-1500:]}", capture_id),
            )
        return False


#: Pico abaixo disto: a faixa não tem nada para transcrever. Conservador de
#: propósito — fala baixa costuma passar de -40 dBFS, então só silêncio digital
#: e ruído inaudível caem aqui.
SILENT_TRACK_PEAK_DBFS = -55.0


def track_peak_dbfs(path: Path) -> float:
    """Pico de um WAV PCM 16 bits, em dBFS. ``-inf`` vira o piso -99."""
    try:
        with wave.open(str(path), "rb") as handle:
            if handle.getsampwidth() != 2:
                return 0.0  # formato inesperado: não arrisca pular a faixa
            frames = handle.readframes(handle.getnframes())
    except (wave.Error, OSError):
        return 0.0
    if not frames:
        return -99.0
    samples = numpy.frombuffer(frames, dtype="<i2")
    if not samples.size:
        return -99.0
    peak = int(numpy.abs(samples.astype(numpy.int32)).max())
    return 20 * math.log10(peak / 32768) if peak > 0 else -99.0


def track_is_silent(path: Path) -> bool:
    """A faixa está muda o bastante para transcrevê-la ser desperdício?

    Numa sessão sem Discord a faixa dele é zero absoluto do início ao fim, e
    ainda assim custa o mesmo tempo de whisper que uma faixa cheia de fala —
    cerca de um terço do custo do capítulo. Pior: sobre silêncio o whisper
    alucina, e o resultado precisa ser filtrado depois de gerado.
    """
    return track_peak_dbfs(path) < SILENT_TRACK_PEAK_DBFS


# --- transcrever só o que tem som ------------------------------------------
#
# Transcrever é a etapa mais cara da análise: o whisper roda a ~0,14x do tempo
# real e é chamado uma vez por faixa. Numa gravação de jogo a maior parte do
# tempo ninguém fala, e transcrever silêncio custa o mesmo que transcrever
# conversa — além de produzir alucinação, que depois precisa ser filtrada.
#
# A saída é condensar: encontrar os trechos com som, colá-los num único WAV,
# rodar o whisper **uma vez** sobre ele e devolver os tempos ao eixo original.
# Uma chamada por trecho seria pior que o problema — cada invocação paga ~20 s
# de carregamento do modelo.

#: RMS por quadro abaixo disto conta como silêncio. Conservador: fala baixa de
#: verdade fica bem acima, e perder fala é muito pior que economizar menos.
SPEECH_THRESHOLD_DBFS = -50.0
#: Janela de análise do envelope.
SPEECH_FRAME_SECONDS = 0.03
#: Folga antes e depois de cada trecho, para não cortar ataque nem cauda.
SPEECH_PAD_SECONDS = 0.4
#: Silêncio menor que isto não vale um corte: emenda os trechos vizinhos.
#: Generoso de propósito — trechos maiores dão ao whisper contexto suficiente
#: para acertar o tempo, e reduzem o número de arquivos por capítulo. A 4 s a
#: economia medida cai de 88% para 83%, o que é barato pela precisão.
SPEECH_MERGE_GAP_SECONDS = 4.0
#: Trecho isolado menor que isto é estalo, não fala.
SPEECH_MIN_REGION_SECONDS = 0.3
#: Acima desta fração de áudio audível, condensar não compensa o risco: manda
#: a faixa inteira, como antes.
SPEECH_MAX_COVERAGE = 0.85


def speech_regions(samples, rate: int, threshold_dbfs: float = SPEECH_THRESHOLD_DBFS,
                   frame_seconds: float = SPEECH_FRAME_SECONDS,
                   pad_seconds: float = SPEECH_PAD_SECONDS,
                   merge_gap_seconds: float = SPEECH_MERGE_GAP_SECONDS,
                   min_region_seconds: float = SPEECH_MIN_REGION_SECONDS) -> list[tuple[float, float]]:
    """Trechos ``(início, fim)`` em segundos onde há som acima do limiar.

    Função pura sobre as amostras: é o miolo da condensação e dá para verificar
    com áudio sintético, sem whisper nem arquivo.
    """
    if rate <= 0 or samples is None or len(samples) == 0:
        return []
    frame = max(1, int(rate * frame_seconds))
    usable = len(samples) // frame * frame
    if usable == 0:
        return []
    blocks = samples[:usable].astype(numpy.float32).reshape(-1, frame)
    rms = numpy.sqrt(numpy.square(blocks).mean(axis=1))
    loud = rms >= 32768 * (10 ** (threshold_dbfs / 20))
    duration = len(samples) / rate

    regions: list[list[float]] = []
    for index in numpy.flatnonzero(loud):
        start = index * frame / rate
        end = start + frame / rate
        if regions and start - regions[-1][1] <= merge_gap_seconds:
            regions[-1][1] = end
        else:
            regions.append([start, end])
    if not regions:
        return []

    padded: list[list[float]] = []
    for start, end in regions:
        start, end = max(0.0, start - pad_seconds), min(duration, end + pad_seconds)
        # A folga pode encostar um trecho no outro; emendar evita cortes de 20 ms.
        if padded and start <= padded[-1][1]:
            padded[-1][1] = max(padded[-1][1], end)
        else:
            padded.append([start, end])
    return [(start, end) for start, end in padded if end - start >= min_region_seconds]


def remap_to_source(segments: list[dict], regions: list[tuple[float, float]]) -> list[dict]:
    """Devolve os tempos do áudio condensado para o eixo do áudio original.

    Sem isto todo segmento sairia com o tempo errado — e errado em silêncio,
    porque o texto continuaria correto e nada acusaria a falha.
    """
    if not regions:
        return segments
    marks: list[tuple[float, float, float]] = []
    cursor = 0.0
    for start, end in regions:
        length = max(0.0, end - start)
        marks.append((cursor, cursor + length, start))
        cursor += length

    def locate(value: float) -> float:
        value = max(0.0, min(value, cursor))
        for condensed_start, condensed_end, source_start in marks:
            if value <= condensed_end:
                return source_start + (value - condensed_start)
        return marks[-1][2] + (marks[-1][1] - marks[-1][0])

    remapped = []
    for segment in segments:
        start = locate(float(segment.get("start", 0)))
        end = locate(float(segment.get("end", 0)))
        # Um segmento que o whisper tenha esticado por cima de um corte volta
        # com fim antes do início; manter a ordem importa mais que a duração.
        remapped.append({**segment, "start": start, "end": max(start, end)})
    return remapped


#: Arquivos por chamada do whisper. Ele aceita vários e carrega o modelo uma vez
#: só; o limite existe para a linha de comando não estourar no Windows.
WHISPER_BATCH_FILES = 48

#: O whisper processa em janelas de 30 s: um arquivo de 6 s custa quase o mesmo
#: que um de 30 s. Por isso trechos vizinhos são colados até encher uma janela —
#: senão a economia evapora em janelas quase vazias.
SPEECH_CHUNK_AUDIBLE_SECONDS = 25.0
#: Mas só trechos **vizinhos**: quanto mais tempo original um grupo cobre, mais
#: um erro de tempo do whisper é amplificado ao voltar para o eixo real. Este
#: teto segura a amplificação em poucas vezes.
SPEECH_CHUNK_SPAN_SECONDS = 75.0


def group_regions(regions: list[tuple[float, float]],
                  audible_limit: float = SPEECH_CHUNK_AUDIBLE_SECONDS,
                  span_limit: float = SPEECH_CHUNK_SPAN_SECONDS) -> list[list[tuple[float, float]]]:
    """Agrupa trechos vizinhos em blocos que caibam numa janela do whisper.

    Dois tetos: quanto de áudio audível cabe num bloco (para não desperdiçar
    janela) e quanto do eixo original ele pode cobrir (para o erro de tempo não
    ser amplificado na volta). Função pura, testável sem áudio.
    """
    groups: list[list[tuple[float, float]]] = []
    for region in regions:
        if groups:
            current = groups[-1]
            audible = sum(end - start for start, end in current) + (region[1] - region[0])
            span = region[1] - current[0][0]
            if audible <= audible_limit and span <= span_limit:
                current.append(region)
                continue
        groups.append([region])
    return groups


def _whisper_segments(path: Path, output: Path, language: str) -> list[dict]:
    """Transcreve um WAV mono 16 kHz, pulando os trechos sem som.

    Cada trecho vira um arquivo próprio e todos vão numa mesma invocação do
    whisper, que aceita vários e carrega o modelo uma vez. O caminho óbvio —
    colar os trechos num WAV só — foi tentado e **não funciona**: com o áudio
    comprimido 8x, um erro de tempo de 1,5 s do whisper vira 13 s no eixo
    original. Um arquivo por trecho mantém o erro dentro do trecho, porque o
    início dele é conhecido exatamente.
    """
    try:
        with wave.open(str(path), "rb") as handle:
            if handle.getnchannels() != 1 or handle.getsampwidth() != 2:
                return _whisper_run(path, output, language)
            rate = handle.getframerate()
            frames = handle.readframes(handle.getnframes())
    except (wave.Error, OSError):
        return _whisper_run(path, output, language)

    samples = numpy.frombuffer(frames, dtype="<i2")
    if not samples.size:
        return _whisper_run(path, output, language)
    duration = samples.size / rate
    regions = speech_regions(samples, rate)
    audible = sum(end - start for start, end in regions)
    if not regions or audible >= duration * SPEECH_MAX_COVERAGE:
        return _whisper_run(path, output, language)

    groups = group_regions(regions)
    directory = output.parent / f"{output.name}-falas"
    directory.mkdir(parents=True, exist_ok=True)
    blocks: list[tuple[Path, list[tuple[float, float]]]] = []
    try:
        for index, group in enumerate(groups):
            piece = directory / f"t{index:04d}.wav"
            with wave.open(str(piece), "wb") as out:
                out.setnchannels(1)
                out.setsampwidth(2)
                out.setframerate(rate)
                for start, end in group:
                    out.writeframes(samples[int(start * rate):int(end * rate)].tobytes())
            blocks.append((piece, group))
        segments: list[dict] = []
        for batch in range(0, len(blocks), WHISPER_BATCH_FILES):
            current = blocks[batch:batch + WHISPER_BATCH_FILES]
            _whisper_batch([piece for piece, _group in current], language)
            for piece, group in current:
                found = _read_whisper_json(piece.with_name(piece.name + ".json"))
                segments.extend(remap_to_source(found, group))
    finally:
        shutil.rmtree(directory, ignore_errors=True)
    segments.sort(key=lambda item: item["start"])
    return filter_hallucinated_segments(segments)


def _whisper_batch(files: list[Path], language: str) -> None:
    command = [str(WHISPER_BIN), "-m", str(WHISPER_MODEL), "-l", language, "-t", "4", "-oj",
               *[str(item) for item in files]]
    result = _run_hidden(command, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout)[-2000:])


def _read_whisper_json(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    segments = []
    payload = json.loads(path.read_text(encoding="utf-8"))
    for segment in payload.get("transcription", []):
        offsets = segment.get("offsets") or {}
        start_ms, end_ms = offsets.get("from"), offsets.get("to")
        if isinstance(start_ms, (int, float)) and isinstance(end_ms, (int, float)):
            segments.append({
                "start": float(start_ms) / 1000,
                "end": float(end_ms) / 1000,
                "text": str(segment.get("text") or "").strip(),
            })
    return segments


def _whisper_run(path: Path, output: Path, language: str) -> list[dict]:
    command = [
        str(WHISPER_BIN), "-m", str(WHISPER_MODEL), "-f", str(path),
        "-l", language, "-t", "4", "-otxt", "-oj", "-of", str(output),
    ]
    result = _run_hidden(command, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        raise RuntimeError((result.stderr or result.stdout)[-2000:])
    return filter_hallucinated_segments(_read_whisper_json(output.with_suffix(".json")))


def merge_source_transcripts(microphone: list[dict], system: list[dict]) -> list[dict]:
    return merge_transcript_sources({"microphone": microphone, "system": system})


def merge_transcript_sources(sources: dict[str, list[dict]]) -> list[dict]:
    order = {"microphone": 0, "discord": 1, "system": 2}
    accepted: dict[str, list[dict]] = {}
    higher: list[dict] = []
    # Quando duas faixas contêm a mesma fala, a fonte de maior prioridade
    # vence. Discord silencioso não bloqueia o voice chat presente no sistema.
    for source in ("microphone", "discord", "system"):
        kept = []
        for segment in sources.get(source, []):
            start, end = float(segment.get("start", 0)), float(segment.get("end", 0))
            duration = max(0.01, end - start)
            words = set(re.findall(r"[\wÀ-ÿ]+", str(segment.get("text", "")).lower()))
            duplicate_overlap = 0.0
            for item in higher:
                item_words = set(re.findall(r"[\wÀ-ÿ]+", str(item.get("text", "")).lower()))
                similarity = len(words & item_words) / max(1, len(words | item_words))
                if similarity >= 0.55:
                    duplicate_overlap = max(duplicate_overlap, max(0.0, min(end, float(item.get("end", 0))) - max(start, float(item.get("start", 0)))))
            if duplicate_overlap < min(0.35, duration * 0.4):
                kept.append(segment)
        accepted[source] = kept
        higher.extend(kept)
    merged = []
    for source, segments in accepted.items():
        for segment in segments:
            item = {**segment, "source": source}
            if source == "microphone":
                item["speaker"] = "self"
            merged.append(item)
    return sorted(merged, key=lambda item: (float(item.get("start", 0)), order.get(item["source"], 9)))


def transcribe(path: Path, language: str = "pt") -> dict:
    missing = []
    if not WHISPER_BIN.is_file():
        missing.append(f"executável não encontrado: {WHISPER_BIN}")
    if not WHISPER_MODEL.is_file():
        missing.append(f"modelo não encontrado: {WHISPER_MODEL}")
    if missing:
        raise RuntimeError("whisper.cpp indisponível; " + "; ".join(missing))
    with tempfile.TemporaryDirectory(prefix="lume-whisper-") as directory:
        root = Path(directory)
        channels = audio_channel_count(path)
        if channels >= 2:
            specifications = (
                (("microphone", "c0"), ("discord", "c1"), ("system", "c2"))
                if channels >= 3 else (("microphone", "c0"), ("system", "c1"))
            )
            tracks = {}
            for name, channel in specifications:
                track = root / f"{name}.wav"
                extracted = _run_hidden([
                    "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path),
                    "-af", f"pan=mono|c0={channel}", "-ar", "16000", "-c:a", "pcm_s16le", str(track),
                ], capture_output=True, text=True, timeout=300)
                if extracted.returncode != 0 or not track.is_file():
                    raise RuntimeError((extracted.stderr or f"não foi possível extrair o canal {name}")[-2000:])
                tracks[name] = _whisper_segments(track, root / f"transcricao-{name}", language)
            segments = merge_transcript_sources(tracks)
            labels = {"microphone": "Você", "discord": "Discord", "system": "Outros sons"}
            text = "\n".join(
                f"{labels[item['source']]}: {item['text']}"
                for item in segments
            ).strip()
        else:
            segments = _whisper_segments(path, root / "transcricao", language)
            text = "\n".join(item["text"] for item in segments).strip()
    probe = _run_hidden([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)
    ], capture_output=True, text=True, timeout=15)
    duration = float(probe.stdout.strip() or 0)
    return {"title": "Trecho de áudio", "text": text, "segments": segments, "app": "RecordBus", "tags": ["áudio"], "duration": duration, "separated_sources": audio_channel_count(path) >= 2}


def transcribe_video_audio(path: Path, duration: float, directory: Path) -> dict:
    streams = audio_stream_count(path)
    if streams >= 4:
        tracks: dict[str, list[dict]] = {}
        for source, stream_index in (("microphone", 1), ("discord", 2), ("system", 3)):
            audio = directory / f"audio-context-{source}.wav"
            result = _run_hidden([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path),
                "-map", f"0:a:{stream_index}", "-vn", "-ac", "1", "-ar", "16000",
                "-c:a", "pcm_s16le", str(audio),
            ], capture_output=True, text=True, timeout=1800)
            tracks[source] = []
            if result.returncode == 0 and audio.is_file() and audio.stat().st_size > 44:
                try:
                    tracks[source] = transcribe(audio, language="auto")["segments"]
                except RuntimeError:
                    pass
        segments = merge_transcript_sources(tracks)
        labels = {"microphone": "Você", "discord": "Discord", "system": "Áudio do sistema"}
        return {
            "text": "\n".join(f"{labels[item['source']]}: {item['text']}" for item in segments).strip(),
            "segments": segments,
            "separated_sources": True,
        }
    audio = directory / "audio-context.wav"
    command = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    if duration <= 1200:
        command += ["-i", str(path), "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio)]
        result = _run_hidden(command, capture_output=True, text=True, timeout=300)
    else:
        clips = []
        for index in range(6):
            start = max(0.0, duration * (index + 0.5) / 6 - 30)
            clip = directory / f"audio-{index:02d}.wav"
            result = _run_hidden([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}",
                "-i", str(path), "-t", "60", "-vn", "-ac", "1", "-ar", "16000",
                "-c:a", "pcm_s16le", str(clip),
            ], capture_output=True, text=True, timeout=90)
            if result.returncode == 0 and clip.stat().st_size > 44:
                clips.append(clip)
        if not clips:
            return {"text": "", "segments": []}
        concat = directory / "audio-list.txt"
        concat.write_text("\n".join(f"file '{clip.name}'" for clip in clips) + "\n", encoding="utf-8")
        result = _run_hidden([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-f", "concat", "-safe", "0",
            "-i", str(concat), "-c", "copy", str(audio),
        ], capture_output=True, text=True, timeout=120, cwd=directory)
    if result.returncode != 0 or not audio.is_file() or audio.stat().st_size <= 44:
        return {"text": "", "segments": []}
    try:
        result = transcribe(audio, language="auto")
        return {"text": result["text"], "segments": result["segments"]}
    except RuntimeError:
        return {"text": "", "segments": []}


def format_video_time(seconds: float) -> str:
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"


def extract_adaptive_keyframes(path: Path, start: float, end: float, interval: float, limit: int, geometry: str, directory: Path, index: int) -> list[str]:
    candidates: list[tuple[float, Path]] = []
    scene_pattern = directory / f"chapter-{index:02d}-scene-%012d.jpg"
    _run_hidden([
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}", "-i", str(path),
        "-t", f"{end-start:.3f}", "-vf",
        f"fps=1/{interval},select='gt(scene,0.018)',settb=1/1000,scale={geometry}:force_original_aspect_ratio=decrease",
        "-fps_mode", "vfr", "-frame_pts", "1", "-q:v", "3", str(scene_pattern),
    ], capture_output=True, text=True, timeout=max(120, int((end-start)/2)))
    for frame in directory.glob(f"chapter-{index:02d}-scene-*.jpg"):
        match = re.search(r"scene-(\d+)\.jpg$", frame.name)
        candidates.append((start + (float(match.group(1)) / 1000 if match else 0), frame))
    # Frames periódicos garantem cobertura mesmo quando HUD/menu muda pouco.
    baseline_count = min(6, max(4, limit // 2))
    for frame_index in range(baseline_count):
        timestamp = start + (end - start) * (frame_index + 0.5) / baseline_count
        frame = directory / f"chapter-{index:02d}-base-{int(timestamp*1000):012d}.jpg"
        result = _run_hidden([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", f"{timestamp:.3f}", "-i", str(path),
            "-frames:v", "1", "-vf", f"scale={geometry}:force_original_aspect_ratio=decrease", "-q:v", "3", str(frame),
        ], capture_output=True, text=True, timeout=60)
        if result.returncode == 0 and frame.is_file():
            candidates.append((timestamp, frame))
    candidates.sort(key=lambda item: item[0])
    if len(candidates) > limit:
        candidates = [candidates[round(i * (len(candidates) - 1) / (limit - 1))] for i in range(limit)]
    return [base64.b64encode(frame.read_bytes()).decode() for _, frame in candidates]


def marker_visual_title(
    path: Path,
    moment: float,
    duration: float,
    transcript_segments: list[dict],
    audio_events: list[dict],
    geometry: str,
    directory: Path,
    index: int,
) -> str:
    """Name a marker from the local 24-second audiovisual moment around it."""
    duration = max(0.0, float(duration))
    moment = min(max(0.0, float(moment)), duration)
    start = max(0.0, moment - 12.0)
    end = min(duration, moment + 12.0)
    if end <= start:
        return ""

    images = extract_adaptive_keyframes(path, start, end, 3.0, 6, geometry, directory, index)
    if len(images) < 2:
        return ""

    nearby_transcript = []
    for segment in transcript_segments:
        if float(segment.get("end", 0)) < start or float(segment.get("start", 0)) > end:
            continue
        source = str(segment.get("source") or segment.get("speaker") or "").strip()
        text = str(segment.get("text") or "").strip()
        if text:
            nearby_transcript.append(f"[{source}] {text}" if source else text)
    nearby_events = [
        event for event in audio_events
        if float(event.get("end", 0)) >= start and float(event.get("start", 0)) <= end
    ]
    prompt = prompts.render(
        "video_marker_title",
        instante=format_video_time(moment),
        inicio=format_video_time(start),
        fim=format_video_time(end),
        transcricao=" ".join(nearby_transcript)[:6000] or "(sem fala detectada)",
        eventos_sonoros=json.dumps(nearby_events, ensure_ascii=False)[:3000] or "[]",
    )
    data = ollama_json(
        vision_model(),
        [{"role": "user", "content": prompt, "images": images}],
        timeout=300,
        num_ctx=8192,
        think=False,
    )
    return str(data.get("title") or "").strip()[:200]


def analyze_video_chapter(path: Path, start: float, end: float, index: int, total: int, geometry: str, directory: Path, context: str = "", scan_interval: float = 2.0, keyframe_limit: int = 12, research_config: dict[str, str] | None = None, research_cache: dict[str, list[dict]] | None = None, research_state: dict | None = None) -> dict:
    base_progress = 5 + int(index / total * 80)
    update_video_progress(path, f"Capítulo {index+1}/{total}: extraindo frames", base_progress, {
        "kind": "chapter_start", "chapter": index + 1, "total": total,
        "detail": f"Intervalo {format_video_time(start)}–{format_video_time(end)}",
    })
    images = extract_adaptive_keyframes(path, start, end, scan_interval, keyframe_limit, geometry, directory, index)
    update_video_progress(path, f"Capítulo {index+1}/{total}: transcrevendo áudio", base_progress + 3)
    transcription = {"text": "", "segments": []}
    labels = {"microphone": "Você", "discord": "Discord", "system": "Áudio do sistema"}
    if audio_stream_count(path) >= 4:
        source_tracks: dict[str, list[dict]] = {}
        for source, stream_index in (("microphone", 1), ("discord", 2), ("system", 3)):
            audio = directory / f"chapter-{index:02d}-{source}.wav"
            extract = _run_hidden([
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}",
                "-i", str(path), "-t", f"{end-start:.3f}", "-map", f"0:a:{stream_index}",
                "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio),
            ], capture_output=True, text=True, timeout=300)
            source_tracks[source] = []
            if extract.returncode == 0 and audio.is_file() and audio.stat().st_size > 44:
                if track_is_silent(audio):
                    update_video_progress(
                        path, f"Capítulo {index+1}/{total}: faixa {labels[source]} está muda",
                        base_progress + 3)
                    continue
                # Sem isto o estágio fica parado em "transcrevendo áudio" por
                # vários minutos por faixa, o que se lê como travado.
                update_video_progress(
                    path, f"Capítulo {index+1}/{total}: transcrevendo {labels[source]}",
                    base_progress + 3)
                try:
                    source_tracks[source] = transcribe(audio, language="auto")["segments"]
                except RuntimeError:
                    pass
        transcription["segments"] = merge_transcript_sources(source_tracks)
        transcription["text"] = "\n".join(f"{labels[item['source']]}: {item['text']}" for item in transcription["segments"])
    else:
        audio = directory / f"chapter-{index:02d}.wav"
        extract = _run_hidden([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-ss", f"{start:.3f}", "-i", str(path),
            "-t", f"{end-start:.3f}", "-vn", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", str(audio),
        ], capture_output=True, text=True, timeout=180)
        if extract.returncode == 0 and audio.is_file() and audio.stat().st_size > 44:
            try:
                transcription = transcribe(audio, language="auto")
            except RuntimeError:
                pass
    prompt = prompts.render(
        "video_chapter",
        capitulo=index + 1,
        total=total,
        inicio=format_video_time(start),
        fim=format_video_time(end),
        transcricao=transcription["text"][:10000] or "(sem fala detectada)",
        contexto=context[:5000] or "(nenhum)",
    )
    if len(images) < 2:
        raise RuntimeError(f"não foi possível extrair frames do capítulo {index+1}")
    update_video_progress(path, f"Capítulo {index+1}/{total}: cruzando áudio e imagens", base_progress + 7)
    try:
        data = ollama_json(vision_model(), [{"role": "user", "content": prompt, "images": images}], timeout=600)
    except RuntimeError as exc:
        # O custo em tokens das imagens varia com o modelo. Se mesmo o limite
        # conservador ultrapassar o contexto, repete com uma amostra menor sem
        # refazer transcrição nem extração do capítulo.
        detail = str(exc).casefold()
        if len(images) <= 8 or not any(term in detail for term in ("context", "token", "tamanho disponível")):
            raise
        images = [images[round(i * (len(images) - 1) / 7)] for i in range(8)]
        update_video_progress(path, f"Capítulo {index+1}/{total}: reduzindo imagens para caber no contexto", base_progress + 7)
        data = ollama_json(vision_model(), [{"role": "user", "content": prompt, "images": images}], timeout=600)
    chapter = {
        "start": start, "end": end, "time": f"{format_video_time(start)}–{format_video_time(end)}",
        "title": str(data.get("title") or f"Capítulo {index+1}")[:200],
        "summary": str(data.get("summary") or "").strip(),
        "events": [str(event)[:500] for event in data.get("events", [])[:8]],
        "evidence": [str(item)[:500] for item in data.get("evidence", [])[:8]],
        "interpretation": str(data.get("interpretation") or "")[:1000],
        "app": str(data.get("app") or ""), "game": str(data.get("game") or ""),
        "tags": [str(tag)[:60] for tag in data.get("tags", [])[:6]], "transcript": transcription["text"],
        "transcript_segments": [
            {**segment, "start": start + segment["start"], "end": start + segment["end"]}
            for segment in transcription["segments"]
        ],
    }
    research = adaptive_web_research(
        f"{chapter['title']}\n{chapter['summary']}\n" + "\n".join(chapter["events"]),
        context, research_config or {}, research_cache if research_cache is not None else {}, research_state,
    )
    chapter["web_findings"] = research["findings"]
    chapter["web_sources"] = research["sources"]
    chapter["web_queries"] = research["queries"]
    if research["queries"]:
        update_video_progress(path, f"Capítulo {index+1}/{total}: pesquisa web concluída", base_progress + 9, {
            "kind": "web_research", "chapter": index + 1,
            "detail": f"{len(research['queries'])} consultas e {len(research['sources'])} fontes úteis",
            "evidence": research["queries"][:12],
        })
    update_video_progress(path, f"Capítulo {index+1}/{total} concluído", 5 + int((index + 1) / total * 80), {
        "kind": "chapter_done", "chapter": index + 1, "title": chapter["title"],
        "detail": f"{len(images)} keyframes selecionados. {chapter['summary']}", "evidence": chapter["evidence"],
        "interpretation": chapter["interpretation"],
    })
    return chapter


def describe_long_video(path: Path, duration: float, geometry: str, directory: Path, context: str = "", scan_interval: float = 2.0, max_keyframes: int = 80, research_config: dict[str, str] | None = None) -> dict:
    chapter_count = min(8, max(2, math.ceil(duration / 300)))
    chapter_duration = duration / chapter_count
    research_cache: dict[str, list[dict]] = {}
    research_state = {"query_count": 0}
    chapters = [
        analyze_video_chapter(
            path, index * chapter_duration, min(duration, (index + 1) * chapter_duration),
            index, chapter_count, geometry, directory, context, scan_interval,
            min(MAX_VISION_IMAGES_PER_REQUEST, max(6, max_keyframes // chapter_count)),
            research_config, research_cache, research_state,
        )
        for index in range(chapter_count)
    ]
    compact = [{key: chapter[key] for key in ("time", "title", "summary", "events", "evidence", "interpretation", "game", "tags", "web_findings")} for chapter in chapters]
    update_video_progress(path, "Sintetizando todos os capítulos", 90, {
        "kind": "synthesis", "detail": f"{chapter_count} capítulos concluídos; gerando memória final",
    })
    synthesis = ollama_json(text_model(), [{"role": "user", "content": prompts.render(
        "video_synthesis",
        capitulos=json.dumps(compact, ensure_ascii=False),
    )}], timeout=600, num_ctx=32768)
    description = str(synthesis.get("description") or "").strip()
    highlights = [str(item) for item in synthesis.get("highlights", [])[:10]]
    if highlights:
        description += "\n\nDestaques:\n" + "\n".join(f"• {item}" for item in highlights)
    transcript = "\n\n".join(
        f"[{chapter['time']}]\n{chapter['transcript']}" for chapter in chapters if chapter["transcript"]
    )
    transcript_segments = [segment for chapter in chapters for segment in chapter["transcript_segments"]]
    return {
        "title": str(synthesis.get("title") or chapters[0]["title"])[:300],
        "description": description, "transcript": transcript, "transcript_segments": transcript_segments,
        "app": str(synthesis.get("app") or chapters[0]["app"] or "Jogo")[:120],
        "duration": duration, "chapters": chapters, "metadata": synthesis,
    }


def synchronized_audio_context(captured_at: str, radius_seconds: float = 45) -> str:
    """Falas do áudio que estava sendo gravado perto do instante de um print."""
    with connect() as db:
        row = db.execute(
            """SELECT captured_at,duration_seconds,transcript_segments_json
               FROM captures
               WHERE kind='audio' AND status='done' AND duration_seconds>0
                 AND julianday(?) BETWEEN julianday(captured_at)
                                      AND julianday(captured_at)+(duration_seconds/86400.0)
               ORDER BY captured_at DESC LIMIT 1""",
            (captured_at,),
        ).fetchone()
    if not row:
        return ""
    try:
        moment = datetime.fromisoformat(captured_at)
        audio_start = datetime.fromisoformat(row["captured_at"])
        offset = (moment - audio_start).total_seconds()
        segments = json.loads(row["transcript_segments_json"] or "[]")
    except (TypeError, ValueError, json.JSONDecodeError):
        return ""
    nearby = [
        segment for segment in segments
        if float(segment.get("end", 0)) >= offset - radius_seconds
        and float(segment.get("start", 0)) <= offset + radius_seconds
        and str(segment.get("text") or "").strip()
    ]
    return "\n".join(
        f"[{float(segment.get('start', 0)) - offset:+.0f}s; "
        f"fonte={segment.get('source') or 'não identificada'}] {str(segment.get('text') or '').strip()}"
        for segment in nearby
    )[:4000]


def describe_screen(path: Path) -> dict:
    encoded = base64.b64encode(path.read_bytes()).decode()
    sidecar = path.with_suffix(path.suffix + ".window")
    window = sidecar.read_text(encoding="utf-8").strip() if sidecar.exists() else ""
    audio_context = synchronized_audio_context(timestamp_from_name(path).isoformat())
    prompt = prompts.render(
        "screen_description",
        janela=window or "(indisponível)",
        audio_proximo=audio_context or "(sem fala sincronizada)",
    )
    data = ollama_json(vision_model(), [{"role": "user", "content": prompt, "images": [encoded]}], timeout=300)
    title = str(data.get("title") or "Captura de tela")[:300]
    description = str(data.get("description") or "").strip()
    return {
        "title": title,
        "text": description,
        "app": str(data.get("app") or (window.split(" | ")[-1] if window else "Desktop"))[:120],
        "tags": tag_vocabulary.apply_tags(
            [str(tag) for tag in data.get("tags", [])[:5]],
            day=timestamp_from_name(path).date().isoformat(),
            context=f"{title}. {description}",
        ),
        "metadata": {"is_game": bool(data.get("is_game")), "game": data.get("game", ""), "event": data.get("event", "")},
    }


def _activity_image(path: Path, target: Path) -> str:
    """JPEG de trabalho: reduz custo visual sem alterar o print original."""
    result = _run_hidden([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path),
        "-vf", "scale=1280:720:force_original_aspect_ratio=decrease",
        "-frames:v", "1", "-q:v", "4", str(target),
    ], capture_output=True, timeout=90)
    source = target if result.returncode == 0 and target.is_file() else path
    return base64.b64encode(source.read_bytes()).decode()


def _screen_window(path: Path) -> str:
    try:
        return path.with_suffix(path.suffix + ".window").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        return ""


def _activity_app(row: dict) -> str:
    """Prefere a identidade capturada da janela aos nomes variáveis da IA."""
    source = row.get("source_path")
    if source:
        path = resolve_media_source(source)
        window = _screen_window(path)
        # O capturador grava «título | classe/processo». Só o sufixo é estável;
        # o título pode mudar a cada episódio ou aba do mesmo aplicativo.
        _, separator, app = window.rpartition(" | ")
        if separator and app.strip():
            return app.strip()
    return str(row.get("app") or "Aplicativo desconhecido").strip()


def _activity_groups(rows: list[dict], gap_seconds: float = 600) -> list[list[dict]]:
    """Separa por aplicativo e continuidade; mudanças de título não quebram a sessão."""
    groups: list[list[dict]] = []
    last_by_app: dict[str, list[dict]] = {}
    for row in sorted(rows, key=lambda item: item["captured_at"]):
        app = _activity_app(row)
        row = {**row, "app": app}
        moment = datetime.fromisoformat(row["captured_at"])
        current = last_by_app.get(app)
        if current:
            previous = datetime.fromisoformat(current[-1]["captured_at"])
            if (moment - previous).total_seconds() <= gap_seconds:
                current.append(row)
                continue
        current = [row]
        groups.append(current)
        last_by_app[app] = current
    return groups


def analyze_screen_sequence(paths: list[Path]) -> dict:
    """Analisa uma seleção manual de prints como uma única sequência temporal."""
    ordered = sorted(paths, key=timestamp_from_name)
    if len(ordered) < 2:
        raise ValueError("selecione pelo menos dois prints")
    if len(ordered) > 30:
        raise ValueError("selecione no máximo 30 prints por teste")

    source_keys = [media_source_key(path) for path in ordered]
    placeholders = ",".join("?" for _ in source_keys)
    with connect() as db:
        rows = db.execute(
            f"SELECT source_path,captured_at,app,text FROM captures WHERE source_path IN ({placeholders})",
            source_keys,
        ).fetchall()
    metadata = {row["source_path"]: dict(row) for row in rows}

    with tempfile.TemporaryDirectory(prefix="lume-sequence-test-") as directory:
        workdir = Path(directory)
        images = [
            _activity_image(path, workdir / f"frame-{index:02d}.jpg")
            for index, path in enumerate(ordered, 1)
        ]
        frame_context = []
        for index, path in enumerate(ordered, 1):
            item = metadata.get(media_source_key(path), {})
            captured_at = str(item.get("captured_at") or timestamp_from_name(path).isoformat())
            audio = synchronized_audio_context(captured_at)
            frame_context.append(
                f"FRAME {index} · [{captured_at[11:19]}] · aplicativo: {item.get('app') or '(desconhecido)'} · "
                f"descrição anterior: {item.get('text') or '(ainda sem descrição)'} · "
                f"áudio próximo: {(audio or '(nenhum)')[:800]}"
            )
        prompt = prompts.render(
            "screen_sequence",
            quantidade=len(ordered),
            frames="\n".join(frame_context),
        )
        data = ollama_json(
            vision_model(), [{"role": "user", "content": prompt, "images": images}], timeout=900, num_ctx=24576
        )
    return {
        "title": str(data.get("title") or "Sequência de telas")[:200],
        "narrative": str(data.get("narrative") or "").strip(),
        "events": string_list(data.get("events"), 40, 800),
        "tags": string_list(data.get("tags"), 8, 80),
        "key_frames": [value for value in data.get("key_frames", []) if isinstance(value, (int, str))],
        "frame_count": len(ordered),
        "model": vision_model(),
    }


def process_screen_sequence_job(job_id: int) -> dict:
    with connect() as db:
        row = db.execute("SELECT paths_json,status FROM screen_sequence_jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise RuntimeError("teste de sequência não encontrado")
        if row["status"] == "cancelled":
            return {"status": "cancelled", "id": job_id}
        db.execute(
            "UPDATE screen_sequence_jobs SET status='processing',stage='Preparando frames selecionados',progress=15,error='' WHERE id=?",
            (job_id,),
        )
    try:
        paths = [resolve_media_source(value) for value in json.loads(row["paths_json"])]
        with connect() as db:
            db.execute("UPDATE screen_sequence_jobs SET stage='Analisando o que aconteceu na sequência',progress=45 WHERE id=?", (job_id,))
        result = analyze_screen_sequence(paths)
        with connect() as db:
            current = db.execute("SELECT status FROM screen_sequence_jobs WHERE id=?", (job_id,)).fetchone()
            if current and current["status"] != "cancelled":
                db.execute(
                    """UPDATE screen_sequence_jobs SET status='done',stage='Concluído',progress=100,result_json=?,model=?,
                       error='',processed_at=CURRENT_TIMESTAMP WHERE id=?""",
                    (json.dumps(result, ensure_ascii=False), result["model"], job_id),
                )
        return {"status": "done", "id": job_id}
    except Exception as exc:
        with connect() as db:
            db.execute(
                """UPDATE screen_sequence_jobs SET status='error',stage='Falha na análise',error=?,
                   processed_at=CURRENT_TIMESTAMP WHERE id=? AND status!='cancelled'""",
                (str(exc)[-2000:], job_id),
            )
        raise


def _activity_batch_summary(data: dict, started_at: str, ended_at: str) -> dict:
    """Mantém cada lote legível e limitado, sem cortar o JSON da sequência."""
    result = {
        "started_at": started_at, "ended_at": ended_at,
        "title": str(data.get("title") or "")[:200],
        "narrative": str(data.get("narrative") or "")[:4000],
        "events": string_list(data.get("events"), 12, 300),
        "tags": string_list(data.get("tags"), 10, 80),
    }
    # Caracteres escapados podem multiplicar o tamanho serializado. Dois
    # resumos sempre devem caber juntos para cada nível realmente reduzir.
    while len(json.dumps(result, ensure_ascii=False)) > 10000:
        result["narrative"] = result["narrative"][:len(result["narrative"]) // 2]
        result["events"] = [event[:len(event) // 2] for event in result["events"]]
    return result


def _merge_activity_batches(analyses: list[dict]) -> dict:
    """Consolida em níveis: todos os períodos chegam à síntese final."""
    pending = analyses
    while len(pending) > 1:
        chunks: list[list[dict]] = [[]]
        size = 0
        for item in pending:
            item_size = len(json.dumps(item, ensure_ascii=False))
            if chunks[-1] and size + item_size > 24000:
                chunks.append([])
                size = 0
            chunks[-1].append(item)
            size += item_size
        merged = []
        for chunk in chunks:
            if len(chunk) == 1:
                merged.append(chunk[0])
                continue
            data = ollama_json(text_model(), [{"role": "user", "content": prompts.render(
                "activity_merge", lotes=json.dumps(chunk, ensure_ascii=False),
            )}], timeout=900, num_ctx=32768)
            merged.append(_activity_batch_summary(data, chunk[0]["started_at"], chunk[-1]["ended_at"]))
        pending = merged
    return pending[0]


def generate_visual_activities(day: str, force: bool = False, *, report=None) -> int:
    """Analisa sequências completas de prints em lotes sobrepostos e as consolida."""
    with connect() as db:
        raw_rows = db.execute(
            """SELECT id,source_path,captured_at,app,title,text,preserved
               FROM captures WHERE kind='screen' AND status='done'
                 AND substr(captured_at,1,10)=? ORDER BY captured_at""", (day,)
        ).fetchall()
    rows = [dict(row) for row in raw_rows if resolve_media_source(row["source_path"]).is_file()]
    groups = _activity_groups(rows)
    generated = 0
    active_keys: list[str] = []
    # O lote encolhe uma vez e vale para o dia inteiro: sem isso, cada grupo
    # grande repetiria a mesma chamada perdida antes de descobrir o limite.
    batch_frames = ACTIVITY_BATCH_FRAMES
    for group_index, group in enumerate(groups, 1):
        app = str(group[0].get("app") or "Aplicativo desconhecido")
        activity_key = hashlib.sha1(f"{day}|{app}|{group[0]['id']}".encode()).hexdigest()
        active_keys.append(activity_key)
        with connect() as db:
            cached = db.execute("SELECT source_count FROM activity_sessions WHERE activity_key=?", (activity_key,)).fetchone()
        if cached and cached["source_count"] == len(group) and not force:
            continue

        analyses: list[dict] = []
        key_capture_ids: list[int] = []
        with tempfile.TemporaryDirectory(prefix="lume-activity-") as directory:
            workdir = Path(directory)
            start = 0
            while start < len(group):
                if report:
                    report(f"Analisando imagens · grupo {group_index}/{len(groups)} · {app} · imagens {start + 1}–{min(len(group), start + batch_frames)}/{len(group)}")
                context_start = max(0, start - ACTIVITY_CONTEXT_FRAMES)
                frames = group[context_start:min(len(group), start + batch_frames)]
                context_count = start - context_start
                images = [
                    _activity_image(resolve_media_source(item["source_path"]), workdir / f"{start:04d}-{index:02d}.jpg")
                    for index, item in enumerate(frames)
                ]
                frame_context = []
                for index, item in enumerate(frames, 1):
                    audio = synchronized_audio_context(item["captured_at"])
                    window = _screen_window(resolve_media_source(item["source_path"]))
                    frame_context.append(
                        f"FRAME {index}{' (somente contexto anterior)' if index <= context_count else ''} · "
                        f"[{item['captured_at']}] · memória screen:{item['id']}\n"
                        + json.dumps({
                            "janela_capturada": window[:600] or "(indisponível)",
                            "titulo_anterior_da_ia": str(item.get("title") or "")[:300],
                            "descricao_anterior_da_ia": str(item.get("text") or "")[:1800],
                            "audio_proximo_transcrito": (audio or "(nenhum)")[:800],
                        }, ensure_ascii=False)
                    )
                prompt = prompts.render(
                    "activity_batch",
                    quantidade=len(frames),
                    aplicativo=app,
                    frames_de_contexto=context_count,
                    frames="\n".join(frame_context),
                )
                try:
                    data = ollama_json(vision_model(), [{"role": "user", "content": prompt, "images": images}], timeout=900, num_ctx=24576)
                except RuntimeError as exc:
                    if not context_overflow(exc) or batch_frames <= 1:
                        raise
                    batch_frames = max(1, batch_frames // 2)
                    print(f"[activity] lote visual reduzido para {batch_frames} frames: {exc}", file=sys.stderr)
                    continue
                analyses.append(_activity_batch_summary(
                    data, frames[context_count]["captured_at"], frames[-1]["captured_at"]
                ))
                for value in data.get("key_frames", []) if isinstance(data.get("key_frames"), list) else []:
                    try:
                        frame_index = int(value) - 1
                    except (TypeError, ValueError):
                        continue
                    if 0 <= frame_index < len(frames):
                        capture_id = int(frames[frame_index]["id"])
                        if capture_id not in key_capture_ids:
                            key_capture_ids.append(capture_id)
                start += batch_frames

        synthesis = _merge_activity_batches(analyses)
        events = string_list(synthesis.get("events"), 40, 800)
        tags = tag_vocabulary.apply_tags(
            string_list(synthesis.get("tags"), 10, 80), day=day,
            context=f"{synthesis.get('title') or app}. {str(synthesis.get('narrative') or '')[:400]}",
        )
        capture_ids = [int(item["id"]) for item in group]
        with connect() as db:
            db.execute(
                """INSERT INTO activity_sessions(activity_key,day,app,title,narrative,events_json,tags_json,
                     capture_ids_json,key_capture_ids_json,started_at,ended_at,source_count,model)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(activity_key) DO UPDATE SET app=excluded.app,title=excluded.title,narrative=excluded.narrative,
                     events_json=excluded.events_json,tags_json=excluded.tags_json,capture_ids_json=excluded.capture_ids_json,
                     key_capture_ids_json=excluded.key_capture_ids_json,started_at=excluded.started_at,ended_at=excluded.ended_at,
                     source_count=excluded.source_count,model=excluded.model,generated_at=CURRENT_TIMESTAMP""",
                (activity_key, day, app, str(synthesis.get("title") or app)[:200], str(synthesis.get("narrative") or ""),
                 json.dumps(events, ensure_ascii=False), json.dumps(tags, ensure_ascii=False), json.dumps(capture_ids),
                 json.dumps(key_capture_ids), group[0]["captured_at"], group[-1]["captured_at"], len(group), vision_model()),
            )
            db.executemany("UPDATE captures SET preserved=1 WHERE id=?", [(item_id,) for item_id in key_capture_ids])
        generated += 1
    # Só reconciliar após concluir todos os grupos. Uma execução interrompida
    # não pode remover a única análise disponível de uma captura.
    covered_ids = {row["id"] for row in rows}
    active_key_set = set(active_keys)
    with connect() as db:
        obsolete = db.execute(
            "SELECT id,activity_key,capture_ids_json FROM activity_sessions WHERE day=?", (day,)
        ).fetchall()
        for session in obsolete:
            if session["activity_key"] in active_key_set:
                continue
            ids = set(json.loads(session["capture_ids_json"] or "[]"))
            if ids and ids.issubset(covered_ids):
                db.execute("DELETE FROM activity_sessions WHERE id=?", (session["id"],))
    return generated


def multimodal_context(rows: list, char_limit: int) -> str:
    """Agrupa telas e áudios sobrepostos em momentos únicos para as sínteses."""
    items = [dict(row) for row in rows]
    screens = [item for item in items if item["kind"] == "screen"]
    assigned_screens: set[int] = set()
    blocks: list[tuple[datetime, str]] = []

    for audio in (item for item in items if item["kind"] == "audio"):
        start = datetime.fromisoformat(audio["captured_at"])
        duration = float(audio.get("duration_seconds") or 0)
        end = start + timedelta(seconds=duration)
        overlapping = []
        if duration > 0:
            for index, screen in enumerate(screens):
                moment = datetime.fromisoformat(screen["captured_at"])
                if start <= moment <= end and index not in assigned_screens:
                    assigned_screens.add(index)
                    overlapping.append(screen)
        if overlapping:
            screen_lines = "\n".join(
                f"- [screen:{screen.get('id','?')}] [{screen['captured_at'][11:19]}] {screen['app']} · {screen['title']}: {screen['text']}"
                for screen in overlapping[:40]
            )
            block = (
                f"[audio:{audio.get('id','?')}] [{audio['captured_at']}] MOMENTO MULTIMODAL\n"
                f"ÁUDIO durante o intervalo:\n{audio['text'] or '(sem fala transcrita)'}\n"
                f"TELAS capturadas durante o mesmo áudio:\n{screen_lines}"
            )
        else:
            block = f"[audio:{audio.get('id','?')}] [{audio['captured_at']}] audio · {audio['app']} · {audio['title']}\n{audio['text']}"
        blocks.append((start, block))

    for index, screen in enumerate(screens):
        if index not in assigned_screens:
            blocks.append((
                datetime.fromisoformat(screen["captured_at"]),
                f"[screen:{screen.get('id','?')}] [{screen['captured_at']}] screen · {screen['app']} · {screen['title']}\n{screen['text']}",
            ))

    for item in (item for item in items if item["kind"] in {"video", "session"}):
        label = "SESSÃO DE VÍDEO" if item["kind"] == "session" else "VÍDEO SELETIVO"
        duration = max(0.0, float(item.get("duration_seconds") or 0))
        duration_line = ""
        if duration > 0:
            rounded = int(round(duration))
            hours, remainder = divmod(rounded, 3600)
            minutes, seconds = divmod(remainder, 60)
            duration_line = (
                f"\nDURAÇÃO REGISTRADA DO VÍDEO: {hours:02d}:{minutes:02d}:{seconds:02d} "
                f"({duration:.1f} segundos)."
            )
        blocks.append((
            datetime.fromisoformat(item["captured_at"]),
            f"[{item['kind']}:{item['id']}] [{item['captured_at']}] {label} · {item['app']} · {item['title']}"
            f"{duration_line}\n{item['text']}",
        ))

    for item in (item for item in items if item["kind"] == "game_activity"):
        duration = max(0.0, float(item.get("duration_seconds") or 0))
        rounded = int(round(duration))
        hours, remainder = divmod(rounded, 3600)
        minutes, seconds = divmod(remainder, 60)
        blocks.append((
            datetime.fromisoformat(item["captured_at"]),
            f"[game_activity:{item['id']}] [{item['captured_at']}] SESSÃO DE JOGO CRONOMETRADA · {item['app']}\n"
            f"DURAÇÃO EXATA DO CONTADOR: {hours:02d}:{minutes:02d}:{seconds:02d} ({duration:.1f} segundos).\n"
            f"{item['text']}",
        ))

    ordered = [block for _moment, block in sorted(blocks, key=lambda item: item[0])]
    joined = "\n\n".join(ordered)
    if len(joined) <= char_limit:
        return joined
    if not ordered or char_limit <= 0:
        return ""

    # Um corte simples pelo limite favorecia o começo do dia e descartava todo
    # o restante. Mantemos amostras uniformes do período inteiro e damos mais
    # espaço aos blocos com áudio, que carregam fala e telas sincronizadas.
    max_blocks = max(1, char_limit // 240)
    if len(ordered) > max_blocks:
        if max_blocks == 1:
            ordered = [ordered[0]]
        else:
            indices = [round(index * (len(ordered) - 1) / (max_blocks - 1)) for index in range(max_blocks)]
            ordered = [ordered[index] for index in dict.fromkeys(indices)]
    separators = max(0, len(ordered) - 1) * 2
    available = max(0, char_limit - separators)
    minimum = min(120, available // max(1, len(ordered)))
    weights = [3 if ("MOMENTO MULTIMODAL" in block or " audio · " in block) else 1 for block in ordered]
    remaining = max(0, available - minimum * len(ordered))
    weight_total = max(1, sum(weights))
    budgets = [minimum + remaining * weight // weight_total for weight in weights]
    budgets[-1] += max(0, available - sum(budgets))

    fitted = []
    for block, budget in zip(ordered, budgets):
        if len(block) <= budget:
            fitted.append(block)
        elif budget >= 40:
            tail = max(12, budget // 3)
            head = budget - tail - 3
            fitted.append(f"{block[:head]}…\n{block[-tail:]}")
        else:
            fitted.append(block[:budget])
    return "\n\n".join(fitted)[:char_limit]


def daily_narrative_target(source_count: int) -> str:
    if source_count >= 150:
        return "6 a 10 parágrafos substanciais"
    if source_count >= 50:
        return "4 a 7 parágrafos substanciais"
    if source_count >= 15:
        return "3 a 5 parágrafos"
    return "2 a 4 parágrafos"


def game_activity_rows(day: str) -> list[dict]:
    """Sessões monitoradas recortadas ao dia local, inclusive ao cruzar meia-noite."""
    day_start = datetime.fromisoformat(f"{day}T00:00:00").astimezone()
    day_end = day_start + timedelta(days=1)
    with connect() as db:
        sessions = [dict(row) for row in db.execute(
            """SELECT id,session_key,app,window,capture_mode,started_at,last_seen_at,ended_at,duration_seconds
               FROM game_activity_sessions ORDER BY started_at"""
        )]
    rows = []
    for session in sessions:
        start = datetime.fromisoformat(session["started_at"])
        end = datetime.fromisoformat(session["ended_at"] or session["last_seen_at"])
        overlap_start = max(start, day_start)
        overlap_end = min(end, day_end)
        duration = max(0.0, (overlap_end - overlap_start).total_seconds())
        if duration <= 0:
            continue
        rows.append({
            "id": session["id"], "source_path": "", "captured_at": overlap_start.isoformat(),
            "kind": "game_activity", "app": session["app"],
            "title": "Sessão monitorada pelo gravador",
            "text": f"Jogo monitorado em modo {session['capture_mode']} durante todo este intervalo.",
            "duration_seconds": duration, "preserved": 1,
        })
    return rows


def apply_exact_game_durations(data: dict, rows: list[dict]) -> dict:
    """Substitui estimativas da IA pelos intervalos medidos pelo contador da sidebar."""
    def game_key(value: object) -> str:
        cleaned = re.sub(r"\.exe$", "", str(value or "").strip().casefold())
        return re.sub(r"[^\w]+", "", cleaned, flags=re.UNICODE)

    totals: dict[str, tuple[str, float]] = {}
    for row in rows:
        if row.get("kind") != "game_activity":
            continue
        app = str(row.get("app") or "Jogo").strip()
        key = game_key(app)
        label, seconds = totals.get(key, (app, 0.0))
        totals[key] = (label, seconds + float(row.get("duration_seconds") or 0))
    if not totals:
        return data

    games = [dict(item) for item in data.get("games", []) if isinstance(item, dict)]
    games_by_title = {game_key(item.get("title")): item for item in games}
    app_blocks = [dict(item) for item in data.get("app_blocks", []) if isinstance(item, dict)]
    blocks_by_app = {game_key(item.get("app")): item for item in app_blocks}
    for key, (label, seconds) in totals.items():
        minutes = max(1, round(seconds / 60))
        game = games_by_title.get(key)
        if game is None:
            game = {"title": label, "event": "Sessão monitorada pelo gravador"}
            games.append(game)
        game["minutes"] = minutes
        block = blocks_by_app.get(key)
        if block is None:
            block = {"app": label}
            app_blocks.append(block)
        block["minutes"] = minutes
    data["games"] = games
    data["app_blocks"] = app_blocks
    return data


def summary_source_rows(day: str) -> list[dict]:
    """Memórias do dia, representando cada sessão de vídeo apenas uma vez."""
    with connect() as db:
        captures = [dict(row) for row in db.execute(
            """SELECT id,source_path,captured_at,kind,app,title,text,duration_seconds,preserved
               FROM captures WHERE status='done' AND substr(captured_at,1,10)=?""", (day,)
        )]
        videos = [dict(row) for row in db.execute(
            """SELECT id,source_path,captured_at,'video' kind,app,title,description text,duration_seconds,preserved
               FROM video_segments WHERE status='done' AND session_id IS NULL
                 AND substr(captured_at,1,10)=?""", (day,)
        )]
        sessions = [dict(row) for row in db.execute(
            """SELECT s.id,min(v.source_path) source_path,min(v.captured_at) captured_at,'session' kind,
                      coalesce(nullif(max(v.app),''),'Vídeo') app,s.name title,s.summary text,
                      sum(v.duration_seconds) duration_seconds,s.preserved
               FROM video_sessions s JOIN video_segments v ON v.session_id=s.id
               WHERE s.status='done' AND substr(v.captured_at,1,10)=?
               GROUP BY s.id""", (day,)
        )]
    return sorted([*captures, *videos, *sessions, *game_activity_rows(day)], key=lambda row: row["captured_at"])


def validate_relevant_media(data: dict, rows: list[dict]) -> dict[str, list[dict]]:
    """Valida referências da IA e protege os arquivos escolhidos."""
    requested = data.get("relevant_media") if isinstance(data.get("relevant_media"), dict) else {}
    groups = {"screens": "screen", "audio": "audio", "videos": "video", "sessions": "session"}
    candidates = {(row["kind"], int(row["id"])): row for row in rows}
    validated: dict[str, list[dict]] = {name: [] for name in groups}

    # Alguns modelos citam corretamente [tipo:id] em tarefas/reuniões, mas ainda
    # devolvem todas as listas de relevant_media vazias. Nessa situação, as
    # próprias citações do resumo são a recuperação mais conservadora: não
    # escolhemos uma memória aleatória e continuamos limitados aos IDs do contexto.
    requested_values = requested if isinstance(requested, dict) else {}
    if not any(isinstance(requested_values.get(group), list) and requested_values[group] for group in groups):
        references: dict[str, list[dict]] = {name: [] for name in groups}

        def collect_strings(value: object):
            if isinstance(value, str):
                yield value
            elif isinstance(value, dict):
                for child in value.values():
                    yield from collect_strings(child)
            elif isinstance(value, list):
                for child in value:
                    yield from collect_strings(child)

        kind_to_group = {kind: group for group, kind in groups.items()}
        limits = {"screens": 6, "audio": 3, "videos": 3, "sessions": 3}
        seen_refs: set[tuple[str, int]] = set()
        for text_value in collect_strings({key: value for key, value in data.items() if key != "relevant_media"}):
            for kind, raw_id in re.findall(r"\[(screen|audio|video|session):(\d+)\]", text_value):
                item_id = int(raw_id)
                key = (kind, item_id)
                group = kind_to_group[kind]
                if key in candidates and key not in seen_refs and len(references[group]) < limits[group]:
                    seen_refs.add(key)
                    references[group].append({"id": item_id, "reason": "Citado diretamente no resumo do dia"})
        requested_values = references

    with connect() as db:
        for group, kind in groups.items():
            values = requested_values.get(group, [])
            if not isinstance(values, list):
                continue
            seen: set[int] = set()
            for value in values[:20]:
                if not isinstance(value, dict):
                    continue
                try:
                    item_id = int(value.get("id"))
                except (TypeError, ValueError):
                    continue
                row = candidates.get((kind, item_id))
                if not row or item_id in seen:
                    continue
                seen.add(item_id)
                item = {
                    "id": item_id, "kind": kind, "title": row.get("title") or "Sem título",
                    "captured_at": row["captured_at"], "app": row.get("app") or "",
                    "source_path": row.get("source_path") or "",
                    "reason": str(value.get("reason") or "Evidência relevante do resumo")[:500],
                    "preserved": True,
                }
                validated[group].append(item)
                if kind in {"screen", "audio"}:
                    db.execute("UPDATE captures SET preserved=1 WHERE id=?", (item_id,))
                elif kind == "video":
                    db.execute("UPDATE video_segments SET preserved=1 WHERE id=?", (item_id,))
                else:
                    db.execute("UPDATE video_sessions SET preserved=1 WHERE id=?", (item_id,))
                    db.execute("UPDATE video_segments SET preserved=1 WHERE session_id=?", (item_id,))
    return validated


def string_list(value: object, limit: int = 10, item_limit: int = 500) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip()[:item_limit] for item in value[:limit] if str(item).strip()]


def short_video_analysis_prompt(duration: float, window: str, transcript: str, context: str) -> str:
    return prompts.render(
        "video_short_analysis",
        duracao=f"{duration:.1f}",
        janela=window or "indisponível",
        transcricao=transcript[:16000] or "(sem fala detectada)",
        contexto=context[:5000] or "(nenhum)",
    )


def review_short_video_analysis(analysis: dict, context: str, research: dict) -> dict:
    evidence = {
        "clip_type": str(analysis.get("clip_type") or "")[:120],
        "main_action": str(analysis.get("main_action") or "")[:1000],
        "audio_visual_relation": str(analysis.get("audio_visual_relation") or "")[:1000],
        "interesting_moment": str(analysis.get("interesting_moment") or "")[:1000],
        "observed_facts": string_list(analysis.get("observed_facts"), 12),
        "user_context_facts": string_list(analysis.get("user_context_facts"), 12),
        "inferences": string_list(analysis.get("inferences"), 10),
        "uncertain": string_list(analysis.get("uncertain"), 10),
        "game_state": analysis.get("game_state") if isinstance(analysis.get("game_state"), dict) else {},
        "app": str(analysis.get("app") or "")[:120],
        "event": str(analysis.get("event") or "")[:1000],
        "tags": string_list(analysis.get("tags"), 5, 60),
        "clip_worthy": bool(analysis.get("clip_worthy")),
    }
    prompt = prompts.render(
        "video_short_review",
        contexto=context[:5000] or "(nenhum)",
        analise=json.dumps(evidence, ensure_ascii=False),
        contexto_externo=str(research.get("findings") or "")[:6000] or "(nenhum)",
    )
    reviewed = ollama_json(text_model(), [{"role": "user", "content": prompt}], timeout=300, num_ctx=16384)
    reviewed["observed_facts"] = string_list(reviewed.get("observed_facts") or evidence["observed_facts"], 12)
    reviewed["user_context_facts"] = string_list(reviewed.get("user_context_facts") or evidence["user_context_facts"], 12)
    reviewed["inferences"] = string_list(reviewed.get("inferences") or evidence["inferences"], 10)
    reviewed["uncertain"] = string_list(reviewed.get("uncertain") or evidence["uncertain"], 10)
    reviewed["game_state"] = evidence["game_state"]
    return reviewed


def describe_video(path: Path, frame_count: int = 6, geometry: str = "960x540", context: str = "") -> dict:
    probe = _run_hidden(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)], capture_output=True, text=True, timeout=20)
    duration = float(probe.stdout.strip() or 0)
    if duration <= 0: raise RuntimeError("vídeo sem duração válida")
    analysis_config = video_config()
    scan_interval = float(analysis_config.get("VIDEO_SCAN_INTERVAL_SECONDS", "2"))
    max_keyframes = int(analysis_config.get("VIDEO_MAX_KEYFRAMES", "80"))
    with tempfile.TemporaryDirectory(prefix="lume-video-") as directory:
        workdir = Path(directory)
        if duration > 300:
            return describe_long_video(path, duration, geometry, workdir, context, scan_interval, max_keyframes, analysis_config)
        update_video_progress(path, "Extraindo frames e áudio", 10, {
            "kind": "short_video", "detail": "Análise audiovisual do vídeo completo",
        })
        images = extract_adaptive_keyframes(path, 0, duration, scan_interval, min(16, max_keyframes), geometry, workdir, 0)
        transcription = transcribe_video_audio(path, duration, workdir)
        update_video_progress(path, "Cruzando transcrição e imagens", 65)
    if len(images) < 2: raise RuntimeError("não foi possível extrair frames suficientes")
    sidecar = path.with_suffix(path.suffix + ".window")
    window = sidecar.read_text(encoding="utf-8").strip() if sidecar.exists() else ""
    prompt = short_video_analysis_prompt(duration, window, transcription["text"], context)
    data = ollama_json(vision_model(), [{"role": "user", "content": prompt, "images": images}], timeout=600, num_ctx=16384)
    observed_for_research = "\n".join([
        *string_list(data.get("observed_facts"), 12),
        str((data.get("game_state") or {}).get("game") or "") if isinstance(data.get("game_state"), dict) else "",
        str(data.get("app") or ""),
    ])
    research = adaptive_web_research(observed_for_research, context, analysis_config, {})
    update_video_progress(path, "Revisando consistência e contexto", 88, {
        "kind": "fact_review", "detail": "Separando evidência visual, contexto informado e inferências",
    })
    reviewed = review_short_video_analysis(data, context, research)
    description = str(reviewed.get("description") or "").strip()
    if research["findings"]: description += "\n\nContexto pesquisado:\n" + research["findings"]
    observed = string_list(reviewed.get("observed_facts"), 12)
    user_facts = string_list(reviewed.get("user_context_facts"), 12)
    inferences = string_list(reviewed.get("inferences"), 10)
    uncertain = string_list(reviewed.get("uncertain"), 10)
    title = str(reviewed.get("title") or data.get("title") or "Trecho de vídeo")[:300]
    chapter = {
        "start": 0, "end": duration, "time": f"{format_video_time(0)}–{format_video_time(duration)}",
        "title": title, "summary": str(reviewed.get("description") or ""),
        "events": observed, "evidence": observed, "user_context_facts": user_facts,
        "interpretation": " ".join(inferences), "uncertain": uncertain,
        "transcript": transcription["text"], "web_findings": research["findings"],
        "web_sources": research["sources"], "web_queries": research["queries"],
    }
    metadata = {**data, **reviewed, "analysis_before_review": data}
    return {
        "title": title, "description": description, "transcript": transcription["text"],
        "transcript_segments": transcription["segments"],
        "app": str(reviewed.get("app") or data.get("app") or "Jogo")[:120],
        "duration": duration, "chapters": [chapter], "metadata": metadata,
    }


def process_video_specific(path: Path, extra_context: str = "") -> dict:
    global AI_LIVE_VIDEO_PATH, AI_LIVE_SESSION_ID
    initialize(); captured = timestamp_from_name(path).isoformat(); source_key = media_source_key(path)
    with connect() as db:
        db.execute("INSERT OR IGNORE INTO video_segments(source_path,captured_at,status) VALUES(?,?,'pending')", (source_key, captured))
        row = db.execute("SELECT * FROM video_segments WHERE source_path=?", (source_key,)).fetchone()
        db.execute("UPDATE video_segments SET status='processing',stage='Preparando análise',progress=1,trace_json='[]',error='',ai_live_thinking='',ai_live_content='',ai_metrics_json='{}' WHERE id=?", (row["id"],))
    AI_LIVE_VIDEO_PATH = source_key; AI_LIVE_SESSION_ID = row["session_id"]
    try:
        context = "\n".join(part for part in (row["context"] or "", extra_context) if part)
        config=video_config();result = describe_video(path,int(config.get("VIDEO_SAMPLE_FRAMES","6")),config.get("VIDEO_SAMPLE_GEOMETRY","960x540"),context)
        update_video_progress(path, "Identificando vozes e eventos acústicos", 96, {
            "kind": "audio_intelligence", "detail": "Separando locutores e detectando risadas, aplausos, choro, gritos, música e falas sobrepostas",
        })
        audio_intelligence = analyze_video_audio(path, result["transcript_segments"], known_voice_profiles())
        result["transcript_segments"] = audio_intelligence["segments"]
        result["speakers"] = audio_intelligence["speakers"]
        result["audio_events"] = audio_intelligence["events"]
        if result["audio_events"]:
            event_lines = [
                f"• {format_video_time(float(event['start']))} [{event['event']}]"
                for event in result["audio_events"][:80]
            ]
            result["description"] = result["description"].rstrip() + "\n\nEventos acústicos observados:\n" + "\n".join(event_lines)
            for chapter in result["chapters"]:
                chapter_start = float(chapter.get("start", 0))
                chapter_end = float(chapter.get("end", result["duration"]))
                chapter["audio_events"] = [
                    event for event in result["audio_events"]
                    if float(event["end"]) >= chapter_start and float(event["start"]) <= chapter_end
                ]
        with connect() as db:
            db.execute("""UPDATE video_segments SET status='done',stage='Concluído',progress=100,title=?,description=?,transcript=?,
                       transcript_segments_json=?,speakers_json=?,audio_events_json=?,chapters_json=?,app=?,duration_seconds=?,model=?,processed_at=CURRENT_TIMESTAMP
                       WHERE id=?""", (result["title"],result["description"],result["transcript"],json.dumps(result["transcript_segments"],ensure_ascii=False),json.dumps(result["speakers"],ensure_ascii=False),json.dumps(result["audio_events"],ensure_ascii=False),json.dumps(result["chapters"],ensure_ascii=False),result["app"],result["duration"],vision_model(),row["id"]))
            save_speaker_observations(db, "video", row["id"], audio_intelligence.get("speaker_embeddings", {}))
            untitled = db.execute("SELECT id,offset_seconds FROM video_markers WHERE video_id=? AND trim(title)='' ORDER BY offset_seconds", (row["id"],)).fetchall()
        if untitled:
            update_video_progress(path, "Nomeando marcadores pelo momento", 99, {
                "kind": "marker_naming",
                "detail": "Analisando 12 segundos antes e depois de cada marcador",
            })
            with tempfile.TemporaryDirectory(prefix="lume-markers-") as marker_directory:
                for index, marker in enumerate(untitled):
                    try:
                        title = marker_visual_title(
                            path,
                            float(marker["offset_seconds"]),
                            float(result["duration"]),
                            result["transcript_segments"],
                            result["audio_events"],
                            config.get("VIDEO_SAMPLE_GEOMETRY", "960x540"),
                            Path(marker_directory),
                            index,
                        )
                    except Exception as exc:
                        print(f"[markers] não foi possível nomear o marcador {marker['id']}: {exc}", file=sys.stderr)
                        continue
                    if title:
                        with connect() as db:
                            db.execute(
                                "UPDATE video_markers SET title=?,ai_generated=1 WHERE id=? AND trim(title)=''",
                                (title, int(marker["id"])),
                            )
            update_video_progress(path, "Concluído", 100)
        deleted=False
        with connect() as db: preserved=bool(db.execute("SELECT preserved FROM video_segments WHERE id=?",(row["id"],)).fetchone()["preserved"])
        if config.get("DELETE_AFTER_DESCRIPTION","false")=="true" and not preserved:
            path.unlink(missing_ok=True);path.with_suffix(path.suffix+".window").unlink(missing_ok=True);deleted=True
        return {"status":"done","id":row["id"],"title":result["title"],"deleted":deleted}
    except Exception as exc:
        with connect() as db: db.execute("UPDATE video_segments SET status='error',stage='Falha na análise',error=? WHERE id=?", (str(exc)[-2000:],row["id"]))
        raise


def monitor_key(path: Path) -> str:
    match = re.search(r"_(mon\d+_[^.]*)\.png$", path.name)
    return match.group(1) if match else "mon-all"


def visually_changed(old: Path, new: Path, threshold: float = 0.03) -> bool:
    if not old.is_file():
        return True
    difference = compare_images(old, new)
    # Falha aberta: se a comparação não puder ser feita, processar a tela é
    # mais seguro do que descartá-la. ``compare_images`` retorna porcentagem;
    # este limiar histórico é uma fração (0,03 == 3%).
    return difference is None or difference >= threshold * 100


def known_voice_profiles() -> list[dict]:
    with connect() as db:
        rows = db.execute("SELECT id,label,embedding_json FROM voice_identities").fetchall()
    return [{"id": row["id"], "label": row["label"], "embedding": json.loads(row["embedding_json"])} for row in rows]


def save_speaker_observations(db, source_kind: str, source_id: int, embeddings: dict[str, list[float]]) -> None:
    db.execute("DELETE FROM speaker_observations WHERE source_kind=? AND source_id=?", (source_kind, source_id))
    db.executemany(
        "INSERT INTO speaker_observations(source_kind,source_id,speaker_id,embedding_json) VALUES(?,?,?,?)",
        [(source_kind, source_id, speaker, json.dumps(vector)) for speaker, vector in embeddings.items()],
    )


def process_pending(kind: str, limit: int, *, capture_ids: list[int] | None = None) -> int:
    if limit <= 0 or capture_ids == []:
        return 0
    selected = "" if capture_ids is None else f" AND id IN ({','.join('?' for _ in capture_ids)})"
    with connect() as db:
        rows = db.execute(
            f"SELECT * FROM captures WHERE kind=? AND status IN ('pending','error'){selected} ORDER BY captured_at,id LIMIT ?",
            [kind, *(capture_ids or []), limit if kind == "audio" else max(limit * 20, limit)],
        ).fetchall()
    completed = 0
    for row in rows:
        if completed >= limit:
            break
        capture_id, path = row["id"], resolve_media_source(row["source_path"])
        with connect() as db:
            current = db.execute("SELECT status FROM captures WHERE id=?", (capture_id,)).fetchone()
        if not current or current["status"] not in ("pending", "error"):
            continue
        if not path.is_file():
            with connect() as db:
                db.execute(
                    """UPDATE captures SET status='skipped',error='arquivo bruto não existe mais',
                       processed_at=CURRENT_TIMESTAMP WHERE id=? AND status IN ('pending','error')""",
                    (capture_id,),
                )
            continue
        if kind == "screen":
            key = monitor_key(path)
            with connect() as db:
                previous = db.execute(
                    "SELECT source_path FROM captures WHERE kind='screen' AND status='done' AND source_path LIKE ? ORDER BY captured_at DESC LIMIT 1",
                    (f"%_{key}.png",),
                ).fetchone()
            if previous and not visually_changed(resolve_media_source(previous["source_path"]), path):
                with connect() as db:
                    db.execute("UPDATE captures SET status='skipped',error='visualmente semelhante',processed_at=CURRENT_TIMESTAMP WHERE id=?", (capture_id,))
                continue
        # Claim the item atomically.  A queue cancellation can happen between
        # loading the batch above and reaching this item.
        with connect() as db:
            claimed = db.execute(
                "UPDATE captures SET status='processing',error='' WHERE id=? AND status IN ('pending','error')",
                (capture_id,),
            ).rowcount
        if not claimed:
            continue
        try:
            # O tempo medido aqui alimenta a média por tipo mostrada na fila.
            started = time.monotonic()
            clear_call_metrics()
            result = transcribe(path) if kind == "audio" else describe_screen(path)
            if kind == "audio":
                intelligence = analyze_video_audio(path, result.get("segments", []), known_voice_profiles())
                result.update(segments=intelligence["segments"], speakers=intelligence["speakers"], audio_events=intelligence["events"])
            elapsed_ms = round((time.monotonic() - started) * 1000)
            call_metrics = json.dumps(last_call_metrics(), ensure_ascii=False)
            with connect() as db:
                saved = db.execute(
                    """UPDATE captures SET status='done',title=?,text=?,app=?,tags_json=?,duration_seconds=?,
                       model=?,sha256=?,transcript_segments_json=?,speakers_json=?,audio_events_json=?,error='',
                       process_ms=?,ai_metrics_json=?,processed_at=CURRENT_TIMESTAMP
                       WHERE id=? AND status='processing'""",
                    (result["title"], result["text"], result["app"], json.dumps(result.get("tags", []), ensure_ascii=False),
                     result.get("duration"), WHISPER_MODEL.name if kind == "audio" else vision_model(), sha256(path),
                     json.dumps(result.get("segments", []), ensure_ascii=False), json.dumps(result.get("speakers", []), ensure_ascii=False),
                     json.dumps(result.get("audio_events", []), ensure_ascii=False), elapsed_ms, call_metrics, capture_id),
                )
                if kind == "audio" and saved.rowcount:
                    save_speaker_observations(db, "audio", capture_id, intelligence.get("speaker_embeddings", {}))
            if kind == "audio" and saved.rowcount:
                compact_saved_capture(path, capture_id)
            completed += saved.rowcount
        except Exception as exc:
            with connect() as db:
                db.execute(
                    "UPDATE captures SET status='error',error=? WHERE id=? AND status='processing'",
                    (str(exc)[-2000:], capture_id),
                )
    return completed


def drain_pending(kind: str, batch_size: int, through_id: int) -> int:
    """Tenta cada item da fila inicial uma vez, em lotes, sem repetir erros."""
    if batch_size <= 0:
        return 0
    with connect() as db:
        ids = [row["id"] for row in db.execute(
            "SELECT id FROM captures WHERE kind=? AND status IN ('pending','error') AND id<=? ORDER BY captured_at,id",
            (kind, through_id),
        )]
    size = min(batch_size, 500)
    completed = 0
    for start in range(0, len(ids), size):
        if pipeline_pause_flag().is_file():
            break
        batch = ids[start:start + size]
        completed += process_pending(kind, len(batch), capture_ids=batch)
    return completed


def process_specific(path: Path) -> dict:
    initialize()
    kind = "screen" if path.suffix.lower() == ".png" else "audio"
    with connect() as db:
        db.execute(
            "INSERT OR IGNORE INTO captures(kind,source_path,captured_at,status) VALUES(?,?,?,'pending')",
            (kind, media_source_key(path), timestamp_from_name(path).isoformat()),
        )
        row = db.execute("SELECT * FROM captures WHERE source_path=?", (media_source_key(path),)).fetchone()
        if row["status"] == "done":
            return {"status": "already-done", "id": row["id"]}
        db.execute("UPDATE captures SET status='processing',error='' WHERE id=?", (row["id"],))
    try:
        started = time.monotonic()
        clear_call_metrics()
        result = transcribe(path) if kind == "audio" else describe_screen(path)
        if kind == "audio":
            intelligence = analyze_video_audio(path, result.get("segments", []), known_voice_profiles())
            result.update(segments=intelligence["segments"], speakers=intelligence["speakers"], audio_events=intelligence["events"])
        elapsed_ms = round((time.monotonic() - started) * 1000)
        call_metrics = json.dumps(last_call_metrics(), ensure_ascii=False)
        with connect() as db:
            db.execute(
                """UPDATE captures SET status='done',title=?,text=?,app=?,tags_json=?,duration_seconds=?,
                   model=?,sha256=?,transcript_segments_json=?,speakers_json=?,audio_events_json=?,error='',
                   process_ms=?,ai_metrics_json=?,processed_at=CURRENT_TIMESTAMP WHERE id=?""",
                (result["title"], result["text"], result["app"], json.dumps(result.get("tags", []), ensure_ascii=False),
                 result.get("duration"), WHISPER_MODEL.name if kind == "audio" else vision_model(), sha256(path),
                 json.dumps(result.get("segments", []), ensure_ascii=False), json.dumps(result.get("speakers", []), ensure_ascii=False),
                 json.dumps(result.get("audio_events", []), ensure_ascii=False), elapsed_ms, call_metrics, row["id"]),
            )
            if kind == "audio":
                save_speaker_observations(db, "audio", row["id"], intelligence.get("speaker_embeddings", {}))
        if kind == "audio":
            compact_saved_capture(path, row["id"])
        return {"status": "done", "id": row["id"], "kind": kind, "title": result["title"]}
    except Exception as exc:
        with connect() as db:
            db.execute("UPDATE captures SET status='error',error=? WHERE id=?", (str(exc)[-2000:], row["id"]))
        raise


def days_pending_consolidation() -> set[str]:
    """Dias com memória analisada cuja narrativa não cobre o que está lá.

    Existe porque "pendente" tinha dois sentidos que não se encontravam. O
    botão de processar pendentes enfileira *mídia* pendente; um dia cuja mídia
    foi analisada semanas atrás não tem nada pendente e, ainda assim, pode
    estar sem narrativa — e o worker só consolidava os dias que tocava na
    própria rodada. O resultado era um dia inteiro de memórias invisível: não
    aparecia como atrasado em lugar nenhum e nenhum clique o alcançava.

    São dois casos, e o segundo é o que trava a limpeza segura:

    * dia sem resumo nenhum;
    * dia cujo resumo é **anterior** à memória mais nova dele. Acontece quando
      mais capturas do mesmo dia são analisadas depois da consolidação: a
      narrativa passa a não cobrir tudo, e a limpeza — que compara a contagem
      registrada com a atual — recusa apagar a mídia bruta, corretamente.
      Reconsolidar é o que atualiza as duas coisas.

    A consulta é sobre o índice, não sobre o disco: a narrativa é montada a
    partir do texto já analisado, então um dia continua consolidável depois de
    a mídia bruta ter sido apagada pela retenção.
    """
    with connect() as db:
        rows = db.execute(
            """SELECT memoria.day FROM (
                   SELECT day, max(processado) processado FROM (
                       SELECT substr(captured_at,1,10) day,
                              coalesce(processed_at,created_at) processado
                       FROM captures WHERE status='done'
                       UNION ALL
                       SELECT substr(captured_at,1,10) day,
                              coalesce(processed_at,created_at) processado
                       FROM video_segments WHERE status='done'
                   ) WHERE day IS NOT NULL AND day <> '' GROUP BY day
               ) memoria
               LEFT JOIN summaries resumo ON resumo.day = memoria.day
               WHERE resumo.day IS NULL
                  OR julianday(resumo.generated_at) < julianday(memoria.processado)"""
        ).fetchall()
    return {row["day"] for row in rows}


def describe_tag_candidates(candidates: list[dict]) -> dict[str, dict]:
    """O Qwen batiza as candidatas que sobreviveram à quarentena.

    Uma tag nova precisa de um critério: é o texto que o Laya lê para reconhecer
    o assunto nas próximas análises. Sem ele a tag existe mas não é aplicável.
    """
    with connect() as db:
        vocabulary = [dict(row) for row in db.execute(
            "SELECT label,criterion FROM tags WHERE status='active' ORDER BY label"
        )]
    prompt = prompts.render(
        "tag_promotion",
        vocabulario="\n".join(f"- {item['label']}: {item['criterion']}" for item in vocabulary) or "(nenhuma ainda)",
        candidatas=json.dumps(candidates, ensure_ascii=False, indent=1),
    )
    data = ollama_json(text_model(), [{"role": "user", "content": prompt}], timeout=600, num_ctx=8192)
    described: dict[str, dict] = {}
    for item in data.get("tags", []) if isinstance(data, dict) else []:
        slug = str((item or {}).get("slug") or "").strip()
        if slug:
            described[slug] = {"label": str(item.get("label") or ""), "criterion": str(item.get("criterion") or "")}
    return described


def promote_day_tags(day: str) -> dict:
    """Fecha o vocabulário do dia: funde sinônimos e promove o que recorreu."""
    return tag_vocabulary.promote(day, describe=describe_tag_candidates)


def generate_summary(day: str) -> bool:
    rows = summary_source_rows(day)
    if not rows:
        return False
    # A síntese horária reduz centenas de capturas repetidas sem perder os
    # diferentes períodos. Horas já atuais são reutilizadas pelo source_count.
    # A análise visual e a síntese horária enriquecem o resumo, mas dados já
    # processados continuam suficientes para gerá-lo. Um timeout de uma etapa
    # auxiliar não deve impedir o resumo diário inteiro de ser atualizado.
    try:
        generate_visual_activities(day)
    except Exception as exc:
        print(f"[summary] análise visual indisponível para {day}: {exc}", file=sys.stderr)
    try:
        generate_hourly_summaries(day)
    except Exception as exc:
        print(f"[summary] síntese horária indisponível para {day}: {exc}", file=sys.stderr)
    # Depois das análises do dia: só aqui todas as propostas da jornada existem,
    # e a recorrência entre elas é o que separa assunto novo de ruído do modelo.
    try:
        promote_day_tags(day)
    except Exception as exc:
        print(f"[summary] promoção de tags indisponível para {day}: {exc}", file=sys.stderr)
    with connect() as db:
        hourly_rows = db.execute(
            "SELECT hour,title,narrative,activities_json,source_count FROM hourly_summaries WHERE substr(hour,1,10)=? ORDER BY hour",
            (day,),
        ).fetchall()
        activity_rows = db.execute(
            "SELECT started_at,ended_at,app,title,narrative,events_json,source_count FROM activity_sessions WHERE day=? ORDER BY started_at",
            (day,),
        ).fetchall()
    hourly_context = "\n\n".join(
        f"[{row['hour'][-2:]}:00] {row['title']} ({row['source_count']} memórias)\n"
        f"{row['narrative']}\nAtividades: {row['activities_json']}"
        for row in hourly_rows
    )
    raw_context = multimodal_context(rows, 42000)
    activity_context = "\n\n".join(
        f"[{row['started_at'][11:16]}–{row['ended_at'][11:16]}] SESSÃO VISUAL · {row['app']} · {row['title']} "
        f"({row['source_count']} prints)\n{row['narrative']}\nEventos: {row['events_json']}"
        for row in activity_rows
    )
    counts = {kind: sum(1 for row in rows if row["kind"] == kind) for kind in ("audio", "screen", "video", "session", "game_activity")}
    target = daily_narrative_target(len(rows))
    prompt = prompts.render(
        "daily_summary",
        memorias=len(rows),
        telas=counts["screen"],
        audios=counts["audio"],
        videos=counts["video"],
        sessoes=counts["session"],
        sessoes_de_jogo=counts["game_activity"],
        horas=len(hourly_rows),
        tamanho_da_narrativa=target,
        sintese_por_hora=hourly_context or "(indisponível)",
        sessoes_visuais=activity_context[:50000] or "(indisponível)",
        evidencias=raw_context,
    )
    data = ollama_json(text_model(), [{"role": "user", "content": prompt}], timeout=900, num_ctx=24576)
    data = apply_exact_game_durations(data, rows)
    data["relevant_media"] = validate_relevant_media(data, rows)
    narrative = str(data.get("narrative") or "")
    with connect() as db:
        db.execute(
            "INSERT INTO summaries(day,narrative,data_json,model) VALUES(?,?,?,?) ON CONFLICT(day) DO UPDATE SET narrative=excluded.narrative,data_json=excluded.data_json,model=excluded.model,generated_at=CURRENT_TIMESTAMP",
            (day, narrative, json.dumps(data, ensure_ascii=False), text_model()),
        )
    return True


def generate_hourly_summaries(day: str, force: bool = False, *, report=None) -> int:
    rows = summary_source_rows(day)
    hours: dict[str, list] = {}
    for row in rows:
        hours.setdefault(row["captured_at"][:13], []).append(row)
    generated = 0
    for hour_index, (hour, entries) in enumerate(sorted(hours.items()), 1):
        with connect() as db:
            cached = db.execute("SELECT source_count FROM hourly_summaries WHERE hour=?", (hour,)).fetchone()
        if cached and cached["source_count"] == len(entries) and not force:
            continue
        if report:
            report(f"Gerando resumo das {hour[-2:]}h · período {hour_index}/{len(hours)}")
        context = multimodal_context(entries, 30000)
        prompt = prompts.render("hourly_summary", contexto=context)
        data = ollama_json(text_model(), [{"role": "user", "content": prompt}], timeout=600, num_ctx=8192)
        hourly_tags = tag_vocabulary.apply_tags(
            [str(tag) for tag in data.get("tags", [])[:5]], day=hour[:10],
            context=f"{data.get('title') or ''}. {str(data.get('narrative') or '')[:400]}",
        )
        with connect() as db:
            db.execute(
                """INSERT INTO hourly_summaries(hour,title,narrative,tags_json,activities_json,source_count,model)
                   VALUES(?,?,?,?,?,?,?) ON CONFLICT(hour) DO UPDATE SET title=excluded.title,narrative=excluded.narrative,
                   tags_json=excluded.tags_json,activities_json=excluded.activities_json,source_count=excluded.source_count,
                   model=excluded.model,generated_at=CURRENT_TIMESTAMP""",
                (hour, str(data.get("title") or f"Atividades das {hour[-2:]}h")[:200], str(data.get("narrative") or ""),
                 json.dumps(hourly_tags, ensure_ascii=False), json.dumps(data.get("activities", [])[:12], ensure_ascii=False), len(entries), text_model()),
            )
        generated += 1
    return generated


def run_pipeline(limit_audio: int, limit_screen: int, summarize: bool, *, drain: bool = False) -> dict:
    initialize(); discovered = discover()
    with connect() as db:
        db.execute("UPDATE captures SET status='pending',error='interrompido; reagendado' WHERE status='processing'")
        db.execute("UPDATE pipeline_runs SET status='interrupted',finished_at=CURRENT_TIMESTAMP,error='execução anterior interrompida' WHERE status='running'")
        capture_days = {
            row["day"] for row in db.execute(
                """SELECT DISTINCT substr(captured_at,1,10) day FROM captures
                   WHERE status IN ('pending','error')"""
            ) if row["day"]
        }
        video_jobs = [dict(row) for row in db.execute(
            """SELECT 'session' kind,s.id id,min(v.captured_at) captured_at,'' source_path
               FROM video_sessions s JOIN video_segments v ON v.session_id=s.id
               WHERE s.status='queued' GROUP BY s.id
               UNION ALL
               SELECT 'video' kind,id,captured_at,source_path FROM video_segments
               WHERE session_id IS NULL AND status='queued'
               ORDER BY captured_at"""
        )]
        run_id = db.execute("INSERT INTO pipeline_runs(status) VALUES('running')").lastrowid
        through_id = db.execute("SELECT coalesce(max(id),0) FROM captures").fetchone()[0]
    try:
        videos = 0
        sessions = 0
        video_errors = 0
        video_days = {job["captured_at"][:10] for job in video_jobs if job.get("captured_at")}
        # Vídeos e sessões entram primeiro porque a consolidação diária os
        # consulta como fontes. O lock global garante uso sequencial da GPU.
        for job in video_jobs:
            try:
                if job["kind"] == "session":
                    process_video_session(int(job["id"]))
                    sessions += 1
                else:
                    process_video_specific(resolve_media_source(job["source_path"]))
                    videos += 1
            except Exception as exc:
                video_errors += 1
                print(f"[pipeline] falha em {job['kind']} {job['id']}: {exc}", file=sys.stderr)
        audio = drain_pending("audio", limit_audio, through_id) if drain else process_pending("audio", limit_audio)
        screen = drain_pending("screen", limit_screen, through_id) if drain else process_pending("screen", limit_screen)
        today = datetime.now().astimezone().date().isoformat()
        # Primeiro os dias desta rodada, em ordem cronológica; depois o
        # atrasado — dias com memória analisada e sem resumo —, do mais recente
        # para o mais antigo, que é a ordem em que alguém procura por eles.
        summary_days: list[str] = []
        if summarize and not pipeline_pause_flag().is_file():
            touched = sorted(capture_days | video_days | {today})
            summary_days = touched + sorted(days_pending_consolidation() - set(touched), reverse=True)
        activities = 0
        hourly = 0
        summary_errors = 0
        summarized_days = []
        # Um dia que a IA não consegue consolidar não pode derrubar a execução
        # inteira: os dias seguintes e a limpeza precisam acontecer mesmo assim.
        summary_queue = [{"day": day, "status": "pending", "stage": "Aguardando"} for day in summary_days]

        def save_progress(stage=None):
            if stage is not None:
                entry["stage"] = stage
            payload = {"days": summary_queue, "updated_at": datetime.now().astimezone().isoformat()}
            with connect() as db:
                db.execute("UPDATE pipeline_runs SET progress_json=? WHERE id=?",
                           (json.dumps(payload, ensure_ascii=False), run_id))

        save_progress()
        for entry in summary_queue:
            day = entry["day"]
            entry["status"] = "processing"
            try:
                save_progress("Preparando análise das imagens")
                activities += generate_visual_activities(day, report=save_progress)
                save_progress("Preparando resumos por hora")
                hourly += generate_hourly_summaries(day, report=save_progress)
                save_progress("Escrevendo resumo do dia")
                if generate_summary(day):
                    summarized_days.append(day)
                    mark_capture_cleanup_ready(day)
                    entry["stage"] = "Concluído"
                else:
                    entry["stage"] = "Sem registros para resumir"
                entry["status"] = "done"
                save_progress()
            except Exception as exc:
                entry.update(status="error", stage="Falha ao consolidar o dia", error=str(exc)[-2000:])
                save_progress()
                summary_errors += 1
                print(f"[pipeline] falha ao consolidar {day}: {exc}", file=sys.stderr)
        with connect() as db:
            db.execute("UPDATE pipeline_runs SET status='done',finished_at=CURRENT_TIMESTAMP,audio_count=?,screen_count=? WHERE id=?", (audio, screen, run_id))
        cleanup = None
        if cleanup_settings()["enabled"]:
            try:
                cleanup = cleanup_processed_capture_media()
            except Exception as exc:
                print(f"[cleanup] limpeza automática falhou sem afetar o processamento: {exc}", file=sys.stderr)
        return {"discovered": discovered, "audio": audio, "screen": screen, "videos": videos,
                "sessions": sessions, "video_errors": video_errors, "activities": activities,
                "hourly": hourly, "summary_errors": summary_errors, "summary": bool(summarized_days),
                "summarized_days": summarized_days, "cleanup": cleanup}
    except Exception as exc:
        with connect() as db:
            db.execute("UPDATE pipeline_runs SET status='error',finished_at=CURRENT_TIMESTAMP,error=? WHERE id=?", (str(exc)[-2000:], run_id))
        raise


def process_video_session(session_id: int) -> dict:
    global AI_LIVE_SESSION_ID
    initialize()
    with connect() as db:
        session = db.execute("SELECT * FROM video_sessions WHERE id=?", (session_id,)).fetchone()
        clips = db.execute(
            "SELECT * FROM video_segments WHERE session_id=? ORDER BY captured_at,id", (session_id,)
        ).fetchall()
        if not session or not clips:
            raise RuntimeError("sessão sem clipes")
        db.execute("UPDATE video_sessions SET status='processing',stage='Preparando clipes',progress=1,trace_json='[]',error='',ai_live_thinking='',ai_live_content='',ai_metrics_json='{}' WHERE id=?", (session_id,))
    AI_LIVE_SESSION_ID = session_id
    trace = []
    try:
        for index, clip in enumerate(clips):
            stage = f"Clipe {index+1}/{len(clips)}: {resolve_media_source(clip['source_path']).name}"
            progress = int(index / len(clips) * 85)
            with connect() as db:
                db.execute("UPDATE video_sessions SET stage=?,progress=? WHERE id=?", (stage, progress, session_id))
            if clip["status"] == "done" and (clip["title"] or clip["description"]):
                trace.append({"kind": "clip_reused", "chapter": index + 1, "title": clip["title"] or "", "detail": stage})
                with connect() as db:
                    db.execute("UPDATE video_sessions SET trace_json=? WHERE id=?", (json.dumps(trace, ensure_ascii=False), session_id))
                continue
            result = process_video_specific(resolve_media_source(clip["source_path"]), session["context"] or "")
            trace.append({"kind": "clip_done", "chapter": index + 1, "title": result.get("title", ""), "detail": stage})
            with connect() as db:
                db.execute("UPDATE video_sessions SET trace_json=? WHERE id=?", (json.dumps(trace, ensure_ascii=False), session_id))
        with connect() as db:
            rows = db.execute(
                "SELECT title,description,duration_seconds FROM video_segments WHERE session_id=? ORDER BY captured_at,id",
                (session_id,),
            ).fetchall()
            db.execute("UPDATE video_sessions SET stage='Criando síntese da gameplay',progress=90 WHERE id=?", (session_id,))
        context = "\n\n".join(
            f"CLIPE {index+1} · {row['duration_seconds']:.0f}s · {row['title']}\n{row['description']}"
            for index, row in enumerate(rows)
        )
        synthesis = ollama_json(text_model(), [{"role": "user", "content": prompts.render(
            "session_synthesis",
            contexto=session["context"] or "(nenhum)",
            clipes=context[:50000],
        )}], timeout=600, num_ctx=32768)
        summary = str(synthesis.get("summary") or "")
        highlights = synthesis.get("highlights") or []
        if highlights:
            summary += "\n\nDestaques:\n" + "\n".join(f"• {item}" for item in highlights[:12])
        with connect() as db:
            db.execute(
                "UPDATE video_sessions SET name=COALESCE(NULLIF(?,''),name),status='done',stage='Concluído',progress=100,summary=?,processed_at=CURRENT_TIMESTAMP WHERE id=?",
                (str(synthesis.get("title") or ""), summary, session_id),
            )
        return {"status": "done", "session_id": session_id, "clips": len(clips)}
    except Exception as exc:
        with connect() as db:
            db.execute("UPDATE video_sessions SET status='error',stage='Falha na sessão',error=? WHERE id=?", (str(exc)[-2000:], session_id))
        raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit-audio", type=int, default=100)
    parser.add_argument("--limit-screen", type=int, default=500)
    parser.add_argument("--no-summary", action="store_true")
    parser.add_argument("--single-batch", action="store_true", help="Executa somente um lote; por padrão esgota a fila inicial")
    parser.add_argument("--discover-only", action="store_true")
    parser.add_argument("--summary-only", metavar="DAY")
    parser.add_argument("--hourly-only", metavar="DAY")
    parser.add_argument("--file", type=Path)
    parser.add_argument("--video", type=Path)
    parser.add_argument("--video-session", type=int)
    parser.add_argument("--screen-sequence", type=int)
    parser.add_argument("--promote-tags", metavar="DAY", help="Funde e promove as tags candidatas do dia")
    parser.add_argument("--preview-tags", metavar="DAY", help="Mostra o que a promoção faria, sem gravar")
    args = parser.parse_args()
    with exclusive_lock(LOCK_PATH) as acquired:
        if not acquired:
            print(json.dumps({"status": "already-running"}))
            return
        if args.preview_tags:
            result = tag_vocabulary.promote(args.preview_tags, describe=describe_tag_candidates, commit=False)
        elif args.promote_tags:
            result = promote_day_tags(args.promote_tags)
        elif args.screen_sequence:
            result = process_screen_sequence_job(args.screen_sequence)
        elif args.video_session:
            result = process_video_session(args.video_session)
        elif args.video:
            result = process_video_specific(args.video.resolve())
        elif args.hourly_only:
            result = {"activities": generate_visual_activities(args.hourly_only, force=True), "hourly": generate_hourly_summaries(args.hourly_only, force=True), "day": args.hourly_only}
        elif args.summary_only:
            activities = generate_visual_activities(args.summary_only)
            hourly = generate_hourly_summaries(args.summary_only)
            summary = generate_summary(args.summary_only)
            if summary:
                mark_capture_cleanup_ready(args.summary_only)
            cleanup = cleanup_processed_capture_media() if summary and cleanup_settings()["enabled"] else None
            result = {"summary": summary, "activities": activities, "hourly": hourly,
                      "cleanup": cleanup, "day": args.summary_only}
        elif args.file:
            result = process_specific(args.file.resolve())
        else:
            result = discover() if args.discover_only else (
                {"status": "paused"} if pipeline_pause_flag().is_file()
                else run_pipeline(args.limit_audio, args.limit_screen, not args.no_summary, drain=not args.single_batch)
            )
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
