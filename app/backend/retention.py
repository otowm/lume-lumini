from __future__ import annotations

import json
from pathlib import Path

from .database import connect
from .main_paths import AUDIO_DIR, CLEANUP_CONFIG, SCREEN_DIR, media_source_key, resolve_media_source


def cleanup_settings() -> dict[str, bool]:
    enabled = False
    if CLEANUP_CONFIG.is_file():
        for raw in CLEANUP_CONFIG.read_text(encoding="utf-8", errors="replace").splitlines():
            key, separator, value = raw.partition("=")
            if separator and key.strip() == "AUTO_DELETE_PROCESSED_CAPTURES":
                enabled = value.strip().lower() == "true"
    return {"enabled": enabled}


def save_cleanup_settings(enabled: bool) -> dict[str, bool]:
    CLEANUP_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    temporary = CLEANUP_CONFIG.with_suffix(CLEANUP_CONFIG.suffix + ".tmp")
    temporary.write_text(
        f"AUTO_DELETE_PROCESSED_CAPTURES={'true' if enabled else 'false'}\n",
        encoding="utf-8",
    )
    temporary.replace(CLEANUP_CONFIG)
    return {"enabled": enabled}


def mark_capture_cleanup_ready(day: str) -> bool:
    """Registra que todos os consumidores das capturas concluíram este dia."""
    with connect() as db:
        summary = db.execute("SELECT 1 FROM summaries WHERE day=?", (day,)).fetchone()
        fingerprint = db.execute(
            """SELECT count(*) capture_count,coalesce(max(processed_at),'') latest_processed_at
               FROM captures WHERE status='done' AND substr(captured_at,1,10)=?""",
            (day,),
        ).fetchone()
        if not summary or not fingerprint or not fingerprint["capture_count"]:
            return False
        db.execute(
            """INSERT INTO capture_cleanup_ready(day,capture_count,latest_processed_at)
               VALUES(?,?,?) ON CONFLICT(day) DO UPDATE SET
               capture_count=excluded.capture_count,
               latest_processed_at=excluded.latest_processed_at,
               completed_at=CURRENT_TIMESTAMP""",
            (day, int(fingerprint["capture_count"]), fingerprint["latest_processed_at"]),
        )
    return True


def reconcile_cleanup_ready_days() -> int:
    """Reconhece consolidações antigas apenas quando todos os artefatos comprovam cobertura."""
    reconciled = 0
    with connect() as db:
        days = db.execute("SELECT day,generated_at FROM summaries").fetchall()
        for summary in days:
            day = summary["day"]
            captures = db.execute(
                """SELECT id,kind,substr(captured_at,1,13) hour,
                          coalesce(processed_at,created_at) processed_at
                   FROM captures WHERE status='done' AND substr(captured_at,1,10)=?""",
                (day,),
            ).fetchall()
            if not captures or db.execute(
                "SELECT 1 FROM captures WHERE status!='done' AND substr(captured_at,1,10)=? LIMIT 1",
                (day,),
            ).fetchone():
                continue
            if any(not db.execute(
                "SELECT coalesce(julianday(?)>=julianday(?),0)",
                (summary["generated_at"], row["processed_at"]),
            ).fetchone()[0] for row in captures):
                continue

            hourly = {
                row["hour"]: row for row in db.execute(
                    "SELECT hour,source_count,generated_at FROM hourly_summaries WHERE substr(hour,1,10)=?",
                    (day,),
                )
            }
            hours: dict[str, list] = {}
            for capture in captures:
                hours.setdefault(capture["hour"], []).append(capture)
            if any(
                hour not in hourly
                or int(hourly[hour]["source_count"]) < len(entries)
                or any(not db.execute(
                    "SELECT coalesce(julianday(?)>=julianday(?),0)",
                    (hourly[hour]["generated_at"], entry["processed_at"]),
                ).fetchone()[0] for entry in entries)
                for hour, entries in hours.items()
            ):
                continue

            screen_rows = [row for row in captures if row["kind"] == "screen"]
            activity_coverage: dict[int, list[str]] = {}
            for activity in db.execute(
                "SELECT capture_ids_json,generated_at FROM activity_sessions WHERE day=?", (day,)
            ):
                try:
                    capture_ids = json.loads(activity["capture_ids_json"] or "[]")
                except (TypeError, ValueError, json.JSONDecodeError):
                    continue
                for capture_id in capture_ids:
                    if isinstance(capture_id, int):
                        activity_coverage.setdefault(capture_id, []).append(activity["generated_at"])
            if any(
                row["id"] not in activity_coverage
                or not any(db.execute(
                    "SELECT coalesce(julianday(?)>=julianday(?),0)",
                    (generated_at, row["processed_at"]),
                ).fetchone()[0] for generated_at in activity_coverage[row["id"]])
                for row in screen_rows
            ):
                continue

            fingerprint = db.execute(
                """SELECT count(*) capture_count,coalesce(max(processed_at),'') latest_processed_at
                   FROM captures WHERE status='done' AND substr(captured_at,1,10)=?""",
                (day,),
            ).fetchone()
            cursor = db.execute(
                """INSERT OR IGNORE INTO capture_cleanup_ready(day,capture_count,latest_processed_at)
                   VALUES(?,?,?)""",
                (day, int(fingerprint["capture_count"]), fingerprint["latest_processed_at"]),
            )
            reconciled += cursor.rowcount
    return reconciled


def cleanup_ready_days() -> set[str]:
    """Retorna somente dias cuja versão consolidada ainda corresponde às capturas."""
    reconcile_cleanup_ready_days()
    with connect() as db:
        rows = db.execute(
            """SELECT ready.day FROM capture_cleanup_ready ready
               JOIN (
                 SELECT substr(captured_at,1,10) day,count(*) capture_count,
                        coalesce(max(processed_at),'') latest_processed_at
                 FROM captures WHERE status='done' GROUP BY substr(captured_at,1,10)
               ) current ON current.day=ready.day
               JOIN summaries summary ON summary.day=ready.day
               WHERE current.capture_count=ready.capture_count
                 AND current.latest_processed_at=ready.latest_processed_at"""
        ).fetchall()
    return {row["day"] for row in rows}


def cleanup_processed_capture_media() -> dict:
    """Apaga apenas PNG/WAV consolidados, nunca vídeos, sessões ou análises."""
    ready_days = cleanup_ready_days()
    deleted = {"screen": 0, "audio": 0}
    deleted_bytes = 0
    skipped = {"preserved": 0, "not_ready": 0, "active": 0, "missing": 0}
    with connect() as db:
        active_paths: set[str] = set()
        for row in db.execute(
            "SELECT paths_json FROM screen_sequence_jobs WHERE status IN ('queued','processing')"
        ):
            try:
                active_paths.update(str(value) for value in json.loads(row["paths_json"] or "[]"))
            except (TypeError, ValueError, json.JSONDecodeError):
                continue
        rows = db.execute(
            """SELECT id,kind,source_path,captured_at,preserved FROM captures
               WHERE status='done' ORDER BY captured_at"""
        ).fetchall()

    for row in rows:
        path = resolve_media_source(row["source_path"])
        if row["preserved"]:
            skipped["preserved"] += int(path.is_file())
            continue
        if row["captured_at"][:10] not in ready_days:
            skipped["not_ready"] += int(path.is_file())
            continue
        if row["source_path"] in active_paths or media_source_key(path) in active_paths:
            skipped["active"] += 1
            continue
        expected_dir, suffix = (SCREEN_DIR, ".png") if row["kind"] == "screen" else (AUDIO_DIR, ".wav")
        if path.suffix.lower() != suffix or path.resolve().parent != expected_dir.resolve():
            skipped["not_ready"] += int(path.is_file())
            continue
        if not path.is_file():
            skipped["missing"] += 1
            continue
        size = path.stat().st_size
        path.unlink()
        if row["kind"] == "screen":
            path.with_suffix(path.suffix + ".window").unlink(missing_ok=True)
        deleted[row["kind"]] += 1
        deleted_bytes += size
    return {
        "ok": True,
        "deleted": deleted,
        "deleted_total": sum(deleted.values()),
        "deleted_bytes": deleted_bytes,
        "ready_days": sorted(ready_days),
        "skipped": skipped,
    }
