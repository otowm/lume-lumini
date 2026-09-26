from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .main_paths import DB_PATH, media_source_key


SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS captures (
  id INTEGER PRIMARY KEY,
  kind TEXT NOT NULL CHECK(kind IN ('screen','audio')),
  source_path TEXT NOT NULL UNIQUE,
  captured_at TEXT NOT NULL,
  app TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL DEFAULT '',
  text TEXT NOT NULL DEFAULT '',
  transcript_segments_json TEXT NOT NULL DEFAULT '[]',
  speakers_json TEXT NOT NULL DEFAULT '[]',
  audio_events_json TEXT NOT NULL DEFAULT '[]',
  tags_json TEXT NOT NULL DEFAULT '[]',
  duration_seconds REAL,
  model TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending',
  stage TEXT NOT NULL DEFAULT '',
  progress INTEGER NOT NULL DEFAULT 0,
  trace_json TEXT NOT NULL DEFAULT '[]',
  job_unit TEXT NOT NULL DEFAULT '',
  error TEXT NOT NULL DEFAULT '',
  sha256 TEXT NOT NULL DEFAULT '',
  preserved INTEGER NOT NULL DEFAULT 0,
  process_ms INTEGER,
  ai_metrics_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  processed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_captures_time ON captures(captured_at DESC);
CREATE INDEX IF NOT EXISTS idx_captures_kind_status ON captures(kind,status);
CREATE VIRTUAL TABLE IF NOT EXISTS captures_fts USING fts5(
  title, text, app, tags_json, content='captures', content_rowid='id', tokenize='unicode61 remove_diacritics 2'
);
CREATE TRIGGER IF NOT EXISTS captures_ai AFTER INSERT ON captures BEGIN
  INSERT INTO captures_fts(rowid,title,text,app,tags_json) VALUES(new.id,new.title,new.text,new.app,new.tags_json);
END;
CREATE TRIGGER IF NOT EXISTS captures_ad AFTER DELETE ON captures BEGIN
  INSERT INTO captures_fts(captures_fts,rowid,title,text,app,tags_json) VALUES('delete',old.id,old.title,old.text,old.app,old.tags_json);
END;
CREATE TRIGGER IF NOT EXISTS captures_au AFTER UPDATE ON captures BEGIN
  INSERT INTO captures_fts(captures_fts,rowid,title,text,app,tags_json) VALUES('delete',old.id,old.title,old.text,old.app,old.tags_json);
  INSERT INTO captures_fts(rowid,title,text,app,tags_json) VALUES(new.id,new.title,new.text,new.app,new.tags_json);
END;
CREATE TABLE IF NOT EXISTS summaries (
  day TEXT PRIMARY KEY,
  narrative TEXT NOT NULL DEFAULT '',
  data_json TEXT NOT NULL DEFAULT '{}',
  model TEXT NOT NULL DEFAULT '',
  generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS hourly_summaries (
  hour TEXT PRIMARY KEY,
  title TEXT NOT NULL DEFAULT '',
  narrative TEXT NOT NULL DEFAULT '',
  tags_json TEXT NOT NULL DEFAULT '[]',
  activities_json TEXT NOT NULL DEFAULT '[]',
  source_count INTEGER NOT NULL DEFAULT 0,
  model TEXT NOT NULL DEFAULT '',
  generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS activity_sessions (
  id INTEGER PRIMARY KEY,
  activity_key TEXT NOT NULL UNIQUE,
  day TEXT NOT NULL,
  app TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL DEFAULT '',
  narrative TEXT NOT NULL DEFAULT '',
  events_json TEXT NOT NULL DEFAULT '[]',
  tags_json TEXT NOT NULL DEFAULT '[]',
  capture_ids_json TEXT NOT NULL DEFAULT '[]',
  key_capture_ids_json TEXT NOT NULL DEFAULT '[]',
  started_at TEXT NOT NULL,
  ended_at TEXT NOT NULL,
  source_count INTEGER NOT NULL DEFAULT 0,
  model TEXT NOT NULL DEFAULT '',
  generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_activity_sessions_day_time ON activity_sessions(day,started_at);
CREATE TABLE IF NOT EXISTS pipeline_runs (
  id INTEGER PRIMARY KEY,
  started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  finished_at TEXT,
  status TEXT NOT NULL DEFAULT 'running',
  audio_count INTEGER NOT NULL DEFAULT 0,
  screen_count INTEGER NOT NULL DEFAULT 0,
  error TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS capture_cleanup_ready (
  day TEXT PRIMARY KEY,
  capture_count INTEGER NOT NULL,
  latest_processed_at TEXT NOT NULL DEFAULT '',
  completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS screen_sequence_jobs (
  id INTEGER PRIMARY KEY,
  paths_json TEXT NOT NULL DEFAULT '[]',
  status TEXT NOT NULL DEFAULT 'queued',
  stage TEXT NOT NULL DEFAULT 'Aguardando início',
  progress INTEGER NOT NULL DEFAULT 0,
  result_json TEXT NOT NULL DEFAULT '{}',
  model TEXT NOT NULL DEFAULT '',
  job_unit TEXT NOT NULL DEFAULT '',
  error TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  processed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_screen_sequence_jobs_status ON screen_sequence_jobs(status,created_at);
CREATE TABLE IF NOT EXISTS video_segments (
  id INTEGER PRIMARY KEY,
  source_path TEXT NOT NULL UNIQUE,
  captured_at TEXT NOT NULL,
  app TEXT NOT NULL DEFAULT '',
  title TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  context TEXT NOT NULL DEFAULT '',
  transcript TEXT NOT NULL DEFAULT '',
  transcript_segments_json TEXT NOT NULL DEFAULT '[]',
  speakers_json TEXT NOT NULL DEFAULT '[]',
  audio_events_json TEXT NOT NULL DEFAULT '[]',
  chapters_json TEXT NOT NULL DEFAULT '[]',
  duration_seconds REAL NOT NULL DEFAULT 0,
  model TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending',
  error TEXT NOT NULL DEFAULT '',
  preserved INTEGER NOT NULL DEFAULT 0,
  session_detached INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  processed_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_video_segments_status ON video_segments(status,captured_at);
CREATE TABLE IF NOT EXISTS video_sessions (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  source_folder TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'pending',
  stage TEXT NOT NULL DEFAULT '',
  progress INTEGER NOT NULL DEFAULT 0,
  summary TEXT NOT NULL DEFAULT '',
  context TEXT NOT NULL DEFAULT '',
  trace_json TEXT NOT NULL DEFAULT '[]',
  job_unit TEXT NOT NULL DEFAULT '',
  error TEXT NOT NULL DEFAULT '',
  preserved INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  processed_at TEXT
);
CREATE TABLE IF NOT EXISTS video_markers (
  id INTEGER PRIMARY KEY,
  video_id INTEGER NOT NULL,
  offset_seconds REAL NOT NULL DEFAULT 0,
  title TEXT NOT NULL DEFAULT '',
  ai_generated INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(video_id) REFERENCES video_segments(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_video_markers_video ON video_markers(video_id,offset_seconds);
CREATE TABLE IF NOT EXISTS shared_links (
  id INTEGER PRIMARY KEY,
  source_path TEXT NOT NULL,
  host TEXT NOT NULL,
  url TEXT NOT NULL,
  bytes INTEGER NOT NULL DEFAULT 0,
  light INTEGER NOT NULL DEFAULT 0,
  limit_mb INTEGER NOT NULL DEFAULT 0,
  expires_at TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_shared_links_source ON shared_links(source_path,created_at);
CREATE TABLE IF NOT EXISTS game_activity_sessions (
  id INTEGER PRIMARY KEY,
  session_key TEXT NOT NULL UNIQUE,
  app TEXT NOT NULL DEFAULT '',
  window TEXT NOT NULL DEFAULT '',
  capture_mode TEXT NOT NULL DEFAULT '',
  started_at TEXT NOT NULL,
  last_seen_at TEXT NOT NULL,
  ended_at TEXT,
  duration_seconds REAL NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_game_activity_sessions_time ON game_activity_sessions(started_at,ended_at);
CREATE TABLE IF NOT EXISTS voice_identities (
  id INTEGER PRIMARY KEY,
  label TEXT NOT NULL UNIQUE COLLATE NOCASE,
  embedding_json TEXT NOT NULL,
  sample_count INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS speaker_observations (
  source_kind TEXT NOT NULL CHECK(source_kind IN ('audio','video')),
  source_id INTEGER NOT NULL,
  speaker_id TEXT NOT NULL,
  embedding_json TEXT NOT NULL,
  PRIMARY KEY(source_kind,source_id,speaker_id)
);
CREATE TABLE IF NOT EXISTS tags (
  slug TEXT PRIMARY KEY,
  label TEXT NOT NULL,
  criterion TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL DEFAULT 'candidate' CHECK(status IN ('candidate','active','dormant','rejected')),
  origin TEXT NOT NULL DEFAULT 'model' CHECK(origin IN ('model','user')),
  proposals INTEGER NOT NULL DEFAULT 0,
  proposal_days_json TEXT NOT NULL DEFAULT '[]',
  samples_json TEXT NOT NULL DEFAULT '[]',
  uses INTEGER NOT NULL DEFAULT 0,
  decided_by TEXT NOT NULL DEFAULT '',
  first_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  last_used TEXT,
  decided_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_tags_status ON tags(status,last_used);
CREATE TABLE IF NOT EXISTS tag_aliases (
  alias TEXT PRIMARY KEY,
  slug TEXT NOT NULL REFERENCES tags(slug) ON DELETE CASCADE,
  confidence REAL NOT NULL DEFAULT 0,
  decided_by TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_tag_aliases_slug ON tag_aliases(slug);
"""


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def _path_survivor(row: sqlite3.Row) -> tuple[int, int, int]:
    item = dict(row)
    analyzed = bool(
        item.get("status") == "done"
        or item.get("text")
        or item.get("description")
        or item.get("transcript")
    )
    return analyzed, item.get("status") == "done", -int(item["id"])


def _merge_portable_paths(db: sqlite3.Connection, table: str) -> None:
    rows = db.execute(f"SELECT * FROM {table} ORDER BY id").fetchall()
    groups: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        key = media_source_key(row["source_path"])
        if key != row["source_path"] or key.startswith("media:"):
            groups.setdefault(key, []).append(row)

    for key, matches in groups.items():
        winner = max(matches, key=_path_survivor)
        winner_id = int(winner["id"])
        losers = [row for row in matches if int(row["id"]) != winner_id]
        if table == "video_segments":
            for loser in losers:
                loser_id = int(loser["id"])
                db.execute("UPDATE video_markers SET video_id=? WHERE video_id=?", (winner_id, loser_id))
                db.execute(
                    """INSERT OR IGNORE INTO speaker_observations(source_kind,source_id,speaker_id,embedding_json)
                       SELECT source_kind,?,speaker_id,embedding_json FROM speaker_observations
                       WHERE source_kind='video' AND source_id=?""",
                    (winner_id, loser_id),
                )
                db.execute("DELETE FROM speaker_observations WHERE source_kind='video' AND source_id=?", (loser_id,))
                db.execute(
                    """UPDATE video_segments SET
                         session_id=coalesce(session_id,?),
                         context=CASE WHEN context='' THEN ? ELSE context END,
                         preserved=max(preserved,?)
                       WHERE id=?""",
                    (loser["session_id"], loser["context"], loser["preserved"], winner_id),
                )
        else:
            for loser in losers:
                loser_id = int(loser["id"])
                db.execute(
                    """INSERT OR IGNORE INTO speaker_observations(source_kind,source_id,speaker_id,embedding_json)
                       SELECT source_kind,?,speaker_id,embedding_json FROM speaker_observations
                       WHERE source_kind='audio' AND source_id=?""",
                    (winner_id, loser_id),
                )
                db.execute("DELETE FROM speaker_observations WHERE source_kind='audio' AND source_id=?", (loser_id,))
        if losers:
            placeholders = ",".join("?" for _ in losers)
            db.execute(f"DELETE FROM {table} WHERE id IN ({placeholders})", [int(row["id"]) for row in losers])
        if winner["source_path"] != key:
            db.execute(f"UPDATE {table} SET source_path=? WHERE id=?", (key, winner_id))


def migrate_media_paths(db: sqlite3.Connection) -> None:
    """Consolida identidades absolutas do Linux/Windows sem perder análises."""
    _merge_portable_paths(db, "captures")
    _merge_portable_paths(db, "video_segments")
    db.execute(
        """DELETE FROM video_sessions
           WHERE source_folder LIKE 'lume-capture:%'
             AND NOT EXISTS(SELECT 1 FROM video_segments WHERE session_id=video_sessions.id)"""
    )


def initialize() -> None:
    with connect() as db:
        db.executescript(SCHEMA)
        run_columns = {row["name"] for row in db.execute("PRAGMA table_info(pipeline_runs)")}
        if "progress_json" not in run_columns:
            db.execute("ALTER TABLE pipeline_runs ADD COLUMN progress_json TEXT NOT NULL DEFAULT '{}'")
        columns = {row["name"] for row in db.execute("PRAGMA table_info(hourly_summaries)")}
        if "activities_json" not in columns:
            db.execute("ALTER TABLE hourly_summaries ADD COLUMN activities_json TEXT NOT NULL DEFAULT '[]'")
        capture_columns = {row["name"] for row in db.execute("PRAGMA table_info(captures)")}
        if "preserved" not in capture_columns:
            db.execute("ALTER TABLE captures ADD COLUMN preserved INTEGER NOT NULL DEFAULT 0")
        if "process_ms" not in capture_columns:
            db.execute("ALTER TABLE captures ADD COLUMN process_ms INTEGER")
        if "ai_metrics_json" not in capture_columns:
            db.execute("ALTER TABLE captures ADD COLUMN ai_metrics_json TEXT NOT NULL DEFAULT '{}'")
        for name in ("transcript_segments_json", "speakers_json", "audio_events_json"):
            if name not in capture_columns:
                db.execute(f"ALTER TABLE captures ADD COLUMN {name} TEXT NOT NULL DEFAULT '[]'")
        video_columns = {row["name"] for row in db.execute("PRAGMA table_info(video_segments)")}
        if "transcript" not in video_columns:
            db.execute("ALTER TABLE video_segments ADD COLUMN transcript TEXT NOT NULL DEFAULT ''")
        if "chapters_json" not in video_columns:
            db.execute("ALTER TABLE video_segments ADD COLUMN chapters_json TEXT NOT NULL DEFAULT '[]'")
        if "transcript_segments_json" not in video_columns:
            db.execute("ALTER TABLE video_segments ADD COLUMN transcript_segments_json TEXT NOT NULL DEFAULT '[]'")
        if "speakers_json" not in video_columns:
            db.execute("ALTER TABLE video_segments ADD COLUMN speakers_json TEXT NOT NULL DEFAULT '[]'")
        if "audio_events_json" not in video_columns:
            db.execute("ALTER TABLE video_segments ADD COLUMN audio_events_json TEXT NOT NULL DEFAULT '[]'")
        for name, definition in (
            ("stage", "TEXT NOT NULL DEFAULT ''"),
            ("progress", "INTEGER NOT NULL DEFAULT 0"),
            ("trace_json", "TEXT NOT NULL DEFAULT '[]'"),
            ("job_unit", "TEXT NOT NULL DEFAULT ''"),
            ("ai_live_thinking", "TEXT NOT NULL DEFAULT ''"),
            ("ai_live_content", "TEXT NOT NULL DEFAULT ''"),
            ("ai_metrics_json", "TEXT NOT NULL DEFAULT '{}'")
        ):
            if name not in video_columns:
                db.execute(f"ALTER TABLE video_segments ADD COLUMN {name} {definition}")
        if "session_id" not in video_columns:
            db.execute("ALTER TABLE video_segments ADD COLUMN session_id INTEGER")
        if "sort_order" not in video_columns:
            db.execute("ALTER TABLE video_segments ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 0")
        if "context" not in video_columns:
            db.execute("ALTER TABLE video_segments ADD COLUMN context TEXT NOT NULL DEFAULT ''")
        if "session_detached" not in video_columns:
            db.execute("ALTER TABLE video_segments ADD COLUMN session_detached INTEGER NOT NULL DEFAULT 0")
        session_columns = {row["name"] for row in db.execute("PRAGMA table_info(video_sessions)")}
        if "preserved" not in session_columns:
            db.execute("ALTER TABLE video_sessions ADD COLUMN preserved INTEGER NOT NULL DEFAULT 0")
        if "context" not in session_columns:
            db.execute("ALTER TABLE video_sessions ADD COLUMN context TEXT NOT NULL DEFAULT ''")
        for name, definition in (
            ("ai_live_thinking", "TEXT NOT NULL DEFAULT ''"),
            ("ai_live_content", "TEXT NOT NULL DEFAULT ''"),
            ("ai_metrics_json", "TEXT NOT NULL DEFAULT '{}'")
        ):
            if name not in session_columns:
                db.execute(f"ALTER TABLE video_sessions ADD COLUMN {name} {definition}")
        migrate_media_paths(db)


def row_dict(row: sqlite3.Row) -> dict:
    item = dict(row)
    if "tags_json" in item:
        item["tags"] = json.loads(item.pop("tags_json") or "[]")
    if "data_json" in item:
        item["data"] = json.loads(item.pop("data_json") or "{}")
    if "activities_json" in item:
        item["activities"] = json.loads(item.pop("activities_json") or "[]")
    for source, target in (
        ("events_json", "events"),
        ("capture_ids_json", "capture_ids"),
        ("key_capture_ids_json", "key_capture_ids"),
        ("transcript_segments_json", "transcript_segments"),
        ("speakers_json", "speakers"),
        ("audio_events_json", "audio_events"),
    ):
        if source in item:
            item[target] = json.loads(item.pop(source) or "[]")
    return item
