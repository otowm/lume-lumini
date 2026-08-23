from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.backend import database
from app.backend.main_paths import media_source_key


class PortableMediaPathTests(unittest.TestCase):
    def test_linux_and_windows_paths_have_the_same_key(self) -> None:
        linux = "/home/otowm/Mount/lume/video-buffer/game.mp4"
        windows = r"F:\lume\video-buffer\game.mp4"
        self.assertEqual(media_source_key(linux), "media:video-buffer/game.mp4")
        self.assertEqual(media_source_key(windows), "media:video-buffer/game.mp4")

    def test_migration_preserves_analyzed_video_and_relations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "lume.sqlite3"
            with patch.object(database, "DB_PATH", db_path):
                database.initialize()
                with database.connect() as db:
                    analyzed_id = db.execute(
                        """INSERT INTO video_segments(source_path,captured_at,status,title,description,transcript,session_id)
                           VALUES(?,?,'done','Analisado','Descrição completa','Transcrição',1)""",
                        ("/home/otowm/Mount/lume/video-buffer/game.mp4", "2026-08-01T12:00:00-03:00"),
                    ).lastrowid
                    duplicate_id = db.execute(
                        """INSERT INTO video_segments(source_path,captured_at,status)
                           VALUES(?,?,'pending')""",
                        (r"F:\lume\video-buffer\game.mp4", "2026-08-01T12:00:00-03:00"),
                    ).lastrowid
                    db.execute(
                        "INSERT INTO video_markers(video_id,offset_seconds,title) VALUES(?,?,?)",
                        (duplicate_id, 12.5, "Momento"),
                    )

                database.initialize()

                with database.connect() as db:
                    rows = db.execute("SELECT * FROM video_segments").fetchall()
                    self.assertEqual(len(rows), 1)
                    self.assertEqual(rows[0]["id"], analyzed_id)
                    self.assertEqual(rows[0]["source_path"], "media:video-buffer/game.mp4")
                    self.assertEqual(rows[0]["status"], "done")
                    self.assertEqual(rows[0]["description"], "Descrição completa")
                    marker = db.execute("SELECT video_id,title FROM video_markers").fetchone()
                    self.assertEqual(marker["video_id"], analyzed_id)
                    self.assertEqual(marker["title"], "Momento")


if __name__ == "__main__":
    unittest.main()
