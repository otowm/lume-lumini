"""Pasta de edição: liga a memória do Lume ao editor de vídeo.

O gravador nomeia os arquivos por data, então achar "aquele clipe" no
Explorer ou no Media Pool do Resolve é garimpo. Aqui cada clipe escolhido
ganha um nome legível numa pasta só — e um ``.edl`` ao lado, com marcadores
e capítulos já posicionados no timecode certo.

O arquivo original não se move nem é copiado: a pasta recebe um *hardlink*,
que no mesmo volume NTFS não custa byte nenhum. O preço disso é que apagar
o original não libera espaço enquanto o hardlink existir — por isso quem
manda um clipe para a edição também o marca como preservado.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import unicodedata
from pathlib import Path

from .database import connect
from .main_paths import EDIT_DIR, resolve_media_source, video_game_label

HIDDEN_PROCESS = getattr(subprocess, "CREATE_NO_WINDOW", 0)
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".webm", ".mov", ".avi", ".m4v"}
ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
TIMECODE = re.compile(r"^(\d{2}):([0-5]\d):([0-5]\d):(\d{2})$")
DEFAULT_START_TIMECODE = "01:00:00:00"

# O vermelho é o que você marcou com a tecla durante o jogo; o amarelo é o
# mesmo marcador depois que a IA deu um nome a ele; o azul são os capítulos.
COLOR_MANUAL = "ResolveColorRed"
COLOR_AI = "ResolveColorYellow"
COLOR_CHAPTER = "ResolveColorBlue"


class EditingError(RuntimeError):
    """Falha que o usuário precisa ler, não um defeito interno."""


def safe_component(value: str, limit: int = 70) -> str:
    """Um pedaço de nome de arquivo que o Windows aceita e você consegue ler."""
    text = unicodedata.normalize("NFC", str(value or "")).strip()
    text = ILLEGAL.sub("", text).replace("\n", " ")
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text[:limit].strip(" .")


def readable_name(captured_at: str, game: str, title: str, fallback: str) -> str:
    """``2026-08-28 17-29 Valorant — clutch no pós-plant``"""
    stamp = safe_component(str(captured_at or "")[:16].replace("T", " ").replace(":", "-"), 16)
    parts = [part for part in (stamp, safe_component(game, 40)) if part]
    subject = safe_component(title, 80) or safe_component(Path(fallback).stem, 80)
    head = " ".join(parts)
    if head and subject:
        return f"{head} — {subject}"
    return head or subject or "clipe"


def timecode_to_frames(value: str, fps: int) -> int:
    match = TIMECODE.match(str(value or "").strip())
    if not match:
        raise EditingError(f"Timecode inválido: {value!r}. Use HH:MM:SS:FF.")
    hours, minutes, seconds, frames = (int(part) for part in match.groups())
    if frames >= fps:
        raise EditingError(f"O timecode {value} tem mais quadros do que os {fps} fps da timeline.")
    return ((hours * 3600 + minutes * 60 + seconds) * fps) + frames


def frames_to_timecode(frames: int, fps: int) -> str:
    frames = max(0, int(frames))
    total_seconds, remainder = divmod(frames, fps)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours % 24:02d}:{minutes:02d}:{seconds:02d}:{remainder:02d}"


def probe_fps(path: Path, fallback: int = 30) -> int:
    """Quadros por segundo do arquivo, arredondados — o EDL é non-drop."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=20, creationflags=HIDDEN_PROCESS,
        )
        numerator, _, denominator = result.stdout.strip().partition("/")
        value = float(numerator) / float(denominator or 1)
    except (OSError, ValueError, ZeroDivisionError, subprocess.SubprocessError):
        return fallback
    return max(1, round(value)) if value > 0 else fallback


def marker_edl(title: str, markers: list[dict], fps: int, start_timecode: str = DEFAULT_START_TIMECODE) -> str:
    """EDL que o Resolve lê em Timelines › Import › Timeline Markers from EDL."""
    origin = timecode_to_frames(start_timecode, fps)
    lines = [f"TITLE: {safe_component(title, 120) or 'Lume'}", "FCM: NON-DROP FRAME", ""]
    for index, marker in enumerate(sorted(markers, key=lambda item: float(item["seconds"])), 1):
        frame = origin + max(0, round(float(marker["seconds"]) * fps))
        start = frames_to_timecode(frame, fps)
        end = frames_to_timecode(frame + 1, fps)
        # O pipe separa os campos do comentário, então ele não pode sobreviver
        # dentro do nome do marcador.
        name = re.sub(r"\s+", " ", str(marker.get("name") or "").replace("|", "/")).strip()[:100] or "Marcador"
        lines.append(f"{index:03d}  001      V     C        {start} {end} {start} {end}")
        lines.append(f" |C:{marker.get('color') or COLOR_MANUAL} |M:{name} |D:1")
        lines.append("")
    return "\n".join(lines)


def chapter_seconds(chapter: dict) -> float | None:
    value = chapter.get("start")
    if isinstance(value, (int, float)):
        return float(value)
    parts = str(chapter.get("time") or "").split(":")
    if not parts or not all(part.strip().isdigit() for part in parts):
        return None
    total = 0.0
    for part in parts:
        total = total * 60 + int(part)
    return total


def clip_markers(db, video_id: int, chapters_json: str, offset: float = 0.0) -> list[dict]:
    """Marcadores da tecla e capítulos da IA, já deslocados na timeline."""
    collected: list[dict] = []
    for row in db.execute(
        "SELECT offset_seconds,title,ai_generated FROM video_markers WHERE video_id=? ORDER BY offset_seconds",
        (video_id,),
    ):
        collected.append({
            "seconds": offset + float(row["offset_seconds"]),
            "name": row["title"] or "Marcador",
            "color": COLOR_AI if row["ai_generated"] else COLOR_MANUAL,
        })
    try:
        chapters = json.loads(chapters_json or "[]")
    except json.JSONDecodeError:
        chapters = []
    for chapter in chapters if isinstance(chapters, list) else []:
        if not isinstance(chapter, dict):
            continue
        seconds = chapter_seconds(chapter)
        if seconds is None:
            continue
        collected.append({
            "seconds": offset + seconds,
            "name": chapter.get("title") or "Capítulo",
            "color": COLOR_CHAPTER,
        })
    return collected


def available_name(stem: str, suffix: str, source: Path) -> Path:
    """Evita colidir com um arquivo homônimo que não seja o mesmo conteúdo."""
    candidate = EDIT_DIR / f"{stem}{suffix}"
    for attempt in range(2, 60):
        if not candidate.exists():
            return candidate
        if candidate.stat().st_ino and candidate.stat().st_ino == source.stat().st_ino:
            return candidate
        candidate = EDIT_DIR / f"{stem} ({attempt}){suffix}"
    raise EditingError(f"Já existem arquivos demais chamados {stem}.")


def link_clip(source: Path, stem: str) -> Path:
    destination = available_name(stem, source.suffix.lower(), source)
    if destination.exists():
        return destination
    try:
        os.link(source, destination)
    except OSError as exc:
        raise EditingError(
            "Não deu para criar o atalho na pasta de edição. Ela precisa estar no mesmo "
            f"disco dos vídeos para o hardlink funcionar ({exc})."
        ) from exc
    return destination


def write_edl(stem: str, title: str, markers: list[dict], fps: int, start_timecode: str) -> Path | None:
    if not markers:
        return None
    path = EDIT_DIR / f"{stem}.edl"
    path.write_text(marker_edl(title, markers, fps, start_timecode), encoding="utf-8")
    return path


def send_video(video_id: int, start_timecode: str = DEFAULT_START_TIMECODE, fps: int = 0) -> dict:
    EDIT_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        row = db.execute(
            "SELECT id,source_path,captured_at,title,app,chapters_json FROM video_segments WHERE id=?",
            (video_id,),
        ).fetchone()
        if not row:
            raise EditingError("Vídeo não encontrado.")
        source = resolve_media_source(row["source_path"])
        if not source.is_file():
            raise EditingError("O arquivo original não está mais no disco.")
        markers = clip_markers(db, row["id"], row["chapters_json"])
        db.execute("UPDATE video_segments SET preserved=1 WHERE id=?", (video_id,))
    timeline_fps = fps or probe_fps(source)
    game, _source = video_game_label(row["source_path"], row["app"])
    stem = readable_name(row["captured_at"], game, row["title"], source.name)
    linked = link_clip(source, stem)
    edl = write_edl(stem, stem, markers, timeline_fps, start_timecode)
    return {
        "ok": True, "name": linked.name, "path": str(linked), "fps": timeline_fps,
        "markers": len(markers), "edl": edl.name if edl else "", "clips": 1,
    }


def send_session(session_id: int, start_timecode: str = DEFAULT_START_TIMECODE, fps: int = 0) -> dict:
    """Os clipes viram 01., 02., 03.… e um único EDL cobre a sessão inteira.

    Os tempos são acumulados na ordem dos trechos, então o EDL só bate se os
    clipes forem colocados na timeline nessa ordem e sem intervalo entre eles.
    """
    EDIT_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        session = db.execute("SELECT id,name,created_at FROM video_sessions WHERE id=?", (session_id,)).fetchone()
        if not session:
            raise EditingError("Sessão não encontrada.")
        clips = db.execute(
            """SELECT id,source_path,captured_at,title,app,chapters_json,duration_seconds
               FROM video_segments WHERE session_id=? AND COALESCE(session_detached,0)=0
               ORDER BY sort_order,captured_at,id""",
            (session_id,),
        ).fetchall()
        usable = [(clip, resolve_media_source(clip["source_path"])) for clip in clips]
        usable = [(clip, path) for clip, path in usable if path.is_file()]
        if not usable:
            raise EditingError("Nenhum trecho desta sessão está no disco.")
        markers: list[dict] = []
        elapsed = 0.0
        for clip, path in usable:
            markers.extend(clip_markers(db, clip["id"], clip["chapters_json"], elapsed))
            elapsed += float(clip["duration_seconds"] or 0)
        db.execute("UPDATE video_sessions SET preserved=1 WHERE id=?", (session_id,))
        db.execute("UPDATE video_segments SET preserved=1 WHERE session_id=?", (session_id,))
    first = usable[0][0]
    timeline_fps = fps or probe_fps(usable[0][1])
    game, _source = video_game_label(first["source_path"], first["app"])
    base = readable_name(first["captured_at"] or session["created_at"], game,
                         session["name"], usable[0][1].name)
    linked = [link_clip(path, f"{base} — {index:02d}") for index, (_clip, path) in enumerate(usable, 1)]
    edl = write_edl(base, base, markers, timeline_fps, start_timecode)
    return {
        "ok": True, "name": base, "path": str(EDIT_DIR / base), "fps": timeline_fps,
        "markers": len(markers), "edl": edl.name if edl else "", "clips": len(linked),
    }


def entries() -> list[dict]:
    if not EDIT_DIR.is_dir():
        return []
    items = []
    for path in sorted(EDIT_DIR.iterdir(), key=lambda item: item.stat().st_mtime, reverse=True):
        if not path.is_file() or path.suffix.lower() not in VIDEO_EXTENSIONS:
            continue
        stats = path.stat()
        edl = path.with_suffix(".edl")
        # A sessão numera os trechos, e o EDL fica com o nome sem o número.
        if not edl.is_file():
            edl = EDIT_DIR / f"{re.sub(r' — \d{2}$', '', path.stem)}.edl"
        items.append({
            "name": path.name, "path": str(path), "bytes": stats.st_size,
            "modified_at": stats.st_mtime, "edl": edl.name if edl.is_file() else "",
        })
    return items


def folder() -> dict:
    items = entries()
    return {
        "root": str(EDIT_DIR),
        "exists": EDIT_DIR.is_dir(),
        "items": items,
        "bytes": sum(item["bytes"] for item in items),
    }


def inside_folder(name: str) -> Path:
    candidate = (EDIT_DIR / name).resolve()
    if candidate.parent != EDIT_DIR.resolve() or not candidate.is_file():
        raise EditingError("Arquivo fora da pasta de edição.")
    return candidate


def remove(name: str) -> dict:
    path = inside_folder(name)
    if path.suffix.lower() not in VIDEO_EXTENSIONS:
        raise EditingError("Só dá para tirar vídeos da pasta de edição.")
    path.unlink()
    companion = path.with_suffix(".edl")
    removed_edl = companion.is_file() and not any(
        other.suffix.lower() in VIDEO_EXTENSIONS and other.stem.startswith(companion.stem)
        for other in EDIT_DIR.iterdir()
    )
    if removed_edl:
        companion.unlink()
    return {"ok": True, "name": name, "edl_removed": removed_edl}
