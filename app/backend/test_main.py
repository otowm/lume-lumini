import asyncio
import dataclasses
import os
import json
import re
import subprocess
import sys
import tempfile
import threading
import unittest
import wave
from array import array
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.backend import database, editing, main as backend_main, main_paths, mode, pipeline, prompts, retention, sharing
from app.backend import tags as tag_vocabulary
from app.backend.database import connect
from app.backend.audio_intelligence import (
    SEGMENTATION_WINDOW_SECONDS, consolidate_events, enrich_segments, identify_profiles,
    overlapping_sources, pad_to_segmentation_window, speaker_profiles, turns_within_duration,
)
from app.backend.main import atomic_write, captured_video_session, origin_allowed, parse_shell_config, rebuild_voice_identity, remote_client_allowed, selective_video_status, stop_target_is_already_gone, voice_identity_payloads
from app.backend.services import ActionResult, SystemdServiceManager
from app.backend.pipeline import (
    DEFAULT_WHISPER_BIN,
    compact_processed_audio,
    daily_narrative_target,
    apply_exact_game_durations,
    game_activity_rows,
    MAX_VISION_IMAGES_PER_REQUEST,
    marker_visual_title,
    monitor_key,
    merge_source_transcripts,
    merge_transcript_sources,
    multimodal_context,
    filter_hallucinated_segments,
    process_pending,
    process_specific,
    private_context_terms,
    recover_json_from_thinking,
    review_short_video_analysis,
    safe_research_query,
    short_video_analysis_prompt,
    summary_source_rows,
    synchronized_audio_context,
    text_model,
    visually_changed,
    vision_model,
    validate_relevant_media,
    _activity_groups,
    generate_visual_activities,
)


#: Isolamento dos sinais de runtime — ver :func:`setUpModule`.
_RUNTIME_DIR: tempfile.TemporaryDirectory | None = None
_RUNTIME_ENV: str | None = None


def setUpModule() -> None:
    """Nenhum teste enxerga (nem apaga) os sinais de runtime da máquina.

    ``runtime_dir()`` aponta para ``XDG_RUNTIME_DIR``, onde vivem os arquivos
    ``lume-process-paused``, ``lume-video-recording`` e afins. Sem isolar,
    ``enqueue_unprocessed`` respondia 409 na máquina de quem tinha o worker
    pausado de verdade, e um teste de "retomar worker" apagaria a pausa real.
    """
    global _RUNTIME_DIR, _RUNTIME_ENV
    _RUNTIME_DIR = tempfile.TemporaryDirectory(prefix="lume-runtime-")
    _RUNTIME_ENV = os.environ.get("XDG_RUNTIME_DIR")
    os.environ["XDG_RUNTIME_DIR"] = _RUNTIME_DIR.name
    # No Windows ``runtime_dir()`` usa o diretório temporário do sistema, e
    # ``tempfile`` guarda esse valor em cache; trocar só a variável não bastaria.
    tempfile.tempdir = _RUNTIME_DIR.name


def tearDownModule() -> None:
    global _RUNTIME_DIR, _RUNTIME_ENV
    tempfile.tempdir = None
    if _RUNTIME_ENV is None:
        os.environ.pop("XDG_RUNTIME_DIR", None)
    else:
        os.environ["XDG_RUNTIME_DIR"] = _RUNTIME_ENV
    if _RUNTIME_DIR is not None:
        _RUNTIME_DIR.cleanup()
    _RUNTIME_DIR = _RUNTIME_ENV = None



class ConfigTests(unittest.TestCase):
    def test_discovery_includes_the_last_finished_audio(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"), \
             patch.object(pipeline, "AUDIO_DIR", Path(directory)), \
             patch.object(pipeline, "SCREEN_DIR", Path(directory)):
            path = Path(directory) / "audio-20260917-200000.wav"
            with wave.open(str(path), "wb") as audio:
                audio.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
                audio.writeframes(b"\0\0" * 16000)
            os.utime(path, (1_700_000_000, 1_700_000_000))
            self.assertEqual(pipeline.discover()["audio"], 1)

    def test_discovery_defers_recording_audio_but_accepts_recent_closed_audio(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"), \
             patch.object(pipeline, "AUDIO_DIR", Path(directory)), \
             patch.object(pipeline, "SCREEN_DIR", Path(directory)):
            path = Path(directory) / "audio-20260917-200000.wav"
            path.write_bytes(b"recording")
            self.assertEqual(pipeline.discover(audio_recording=True)["audio"], 0)
            self.assertEqual(pipeline.discover()["deferred_audio"], 1)
            self.assertEqual(pipeline.discover(audio_recording=False)["audio"], 1)

    def test_drain_attempts_errors_once_and_continues_after_skips(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"), \
             patch.object(pipeline, "visually_changed", return_value=True):
            database.initialize()
            with database.connect() as db:
                for index in range(4):
                    path = Path(directory) / f"screen-{index}.png"
                    if index != 1:
                        path.write_bytes(b"png")
                    db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('screen',?,?,'pending')", (str(path), f"2026-09-17T20:00:0{index}"))
            attempts = []
            def describe(path):
                attempts.append(path.name)
                if path.name == "screen-0.png":
                    raise RuntimeError("falha de teste")
                return {"title": "Tela", "text": "Descrição", "app": "Browser"}
            with patch.object(pipeline, "describe_screen", side_effect=describe):
                self.assertEqual(pipeline.drain_pending("screen", 1, 3), 1)
            self.assertEqual(attempts, ["screen-0.png", "screen-2.png"])
            with database.connect() as db:
                states = [row[0] for row in db.execute("SELECT status FROM captures ORDER BY id")]
            self.assertEqual(states, ["error", "skipped", "done", "pending"])

    def test_drain_respects_pause_and_zero_batch(self):
        with patch.object(pipeline, "process_pending") as process:
            self.assertEqual(pipeline.drain_pending("screen", 0, 50), 0)
            process.assert_not_called()
        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with database.connect() as db:
                db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('screen','test.png','2026-09-17','pending')")
            flag = Path(directory) / "paused"
            flag.touch()
            with patch.object(pipeline, "pipeline_pause_flag", return_value=flag), patch.object(pipeline, "process_pending") as process:
                self.assertEqual(pipeline.drain_pending("screen", 1, 50), 0)
                process.assert_not_called()

    def test_automatic_worker_finishes_more_than_one_capture_batch(self):
        import shlex
        from contextlib import nullcontext
        unit = (Path(__file__).resolve().parents[2] / "systemd/lume-process.service").read_text()
        arguments = shlex.split(next(line for line in unit.splitlines() if line.startswith("ExecStart=")).split("app.backend.pipeline", 1)[1])
        arguments[arguments.index("--limit-screen") + 1] = "2"
        arguments[arguments.index("--limit-audio") + 1] = "0"
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"), \
             patch.object(pipeline, "discover", return_value={"audio": 0, "screen": 0}), \
             patch.object(pipeline, "exclusive_lock", return_value=nullcontext(True)), \
             patch.object(pipeline, "visually_changed", return_value=True), \
             patch.object(pipeline, "describe_screen", return_value={"title": "Tela", "text": "Descrição", "app": "Browser"}), \
             patch.object(pipeline, "cleanup_settings", return_value={"enabled": False}), \
             patch.object(pipeline.sys, "argv", ["pipeline", *arguments, "--no-summary"]):
            database.initialize()
            with database.connect() as db:
                for index in range(3):
                    path = Path(directory) / f"2026-09-17_20-00-0{index}_mon1.png"
                    path.write_bytes(b"png")
                    db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('screen',?,?,'pending')", (str(path), f"2026-09-17T20:00:0{index}"))
            pipeline.main()
            with database.connect() as db:
                remaining = db.execute("SELECT count(*) FROM captures WHERE status='pending'").fetchone()[0]
            self.assertEqual(remaining, 0, "O worker encerrou deixando capturas que já estavam na fila")

    def test_remote_access_accepts_only_configured_zerotier_networks_and_hosts(self):
        networks = (__import__("ipaddress").ip_network("10.28.4.0/24"),)
        with patch.object(backend_main, "REMOTE_NETWORKS", networks), \
             patch.object(backend_main, "ALLOWED_SERVER_HOSTS", {"127.0.0.1", "localhost", "10.28.4.6"}):
            self.assertTrue(remote_client_allowed("127.0.0.1"))
            self.assertTrue(remote_client_allowed("10.28.4.42"))
            self.assertFalse(remote_client_allowed("192.168.15.20"))
            self.assertTrue(origin_allowed("http://10.28.4.6:8876"))
            self.assertFalse(origin_allowed("http://192.168.15.19:8876"))

    def test_video_ranges_are_capped_even_when_browser_requests_to_eof(self):
        limit = backend_main.VIDEO_STREAM_CHUNK_BYTES
        size = limit * 10
        self.assertEqual(backend_main.bounded_video_range("", size), (0, limit - 1))
        self.assertEqual(backend_main.bounded_video_range("bytes=100-", size), (100, 100 + limit - 1))
        self.assertEqual(backend_main.bounded_video_range("bytes=200-299", size), (200, 299))

    def test_video_suffix_range_is_also_capped(self):
        limit = backend_main.VIDEO_STREAM_CHUNK_BYTES
        size = limit * 10
        self.assertEqual(backend_main.bounded_video_range(f"bytes=-{limit * 2}", size), (size - limit, size - 1))

    def test_trim_command_reencodes_video_and_keeps_all_audio_tracks(self):
        command = backend_main.trim_video_command(Path("clip.mkv"), Path("cut.mkv"), 4.25, 18.5)
        self.assertIn("libx264", command)
        self.assertEqual(command[command.index("-ss") + 1], "4.250")
        self.assertEqual(command[command.index("-t") + 1], "18.500")
        self.assertIn("0:a?", command)

    def test_trim_video_replaces_file_shifts_markers_and_resets_stale_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "clip.mkv"
            source.write_bytes(b"original")
            clips = root / "clips"
            clips.mkdir()
            db_path = root / "lume.sqlite3"
            with patch.object(database, "DB_PATH", db_path):
                database.initialize()
                with database.connect() as db:
                    session_id = db.execute("INSERT INTO video_sessions(name,status,summary) VALUES('Jogo','done','antigo')").lastrowid
                    video_id = db.execute(
                        """INSERT INTO video_segments(source_path,captured_at,status,description,transcript,chapters_json,duration_seconds,session_id)
                           VALUES(?,'2026-08-23T10:00:00-03:00','done','antiga','fala','[{}]',60,?)""",
                        (str(source), session_id),
                    ).lastrowid
                    db.executemany(
                        "INSERT INTO video_markers(video_id,offset_seconds,title) VALUES(?,?,?)",
                        [(video_id, 2, "fora"), (video_id, 12, "dentro"), (video_id, 50, "fora")],
                    )

                def fake_run(command, timeout=0):
                    Path(command[-1]).write_bytes(b"trimmed")
                    return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

                with patch.object(backend_main, "safe_video_path", return_value=source), \
                     patch.object(backend_main, "probe_video_duration", return_value=60), \
                     patch.object(backend_main, "run", side_effect=fake_run), \
                     patch.object(backend_main, "CLIPS_DIR", clips), \
                     patch.object(backend_main, "delete_video_caches"):
                    result = backend_main.trim_video(video_id, backend_main.VideoTrimRequest(start_seconds=10, end_seconds=40))

                with database.connect() as db:
                    video = db.execute("SELECT * FROM video_segments WHERE id=?", (video_id,)).fetchone()
                    markers = db.execute("SELECT offset_seconds,title FROM video_markers WHERE video_id=?", (video_id,)).fetchall()
                    session = db.execute("SELECT status,summary FROM video_sessions WHERE id=?", (session_id,)).fetchone()
            self.assertEqual(source.read_bytes(), b"trimmed")
            self.assertEqual(result["duration_seconds"], 30)
            self.assertEqual([(row["offset_seconds"], row["title"]) for row in markers], [(2, "dentro")])
            self.assertEqual(video["duration_seconds"], 30)
            self.assertEqual(video["status"], "pending")
            self.assertEqual(video["description"], "")
            self.assertEqual(video["captured_at"], "2026-08-23T10:00:10-03:00")
            self.assertEqual((session["status"], session["summary"]), ("pending", ""))

    def test_trim_to_new_file_keeps_the_original_and_its_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "clip.mkv"
            source.write_bytes(b"original")
            db_path = root / "lume.sqlite3"
            with patch.object(database, "DB_PATH", db_path):
                database.initialize()
                with database.connect() as db:
                    session_id = db.execute("INSERT INTO video_sessions(name,status,summary) VALUES('Jogo','done','resumo')").lastrowid
                    video_id = db.execute(
                        """INSERT INTO video_segments(source_path,captured_at,status,description,app,title,duration_seconds,session_id)
                           VALUES(?,'2026-08-23T10:00:00-03:00','done','antiga','osu!','Partida',120,?)""",
                        (str(source), session_id),
                    ).lastrowid
                    db.executemany(
                        "INSERT INTO video_markers(video_id,offset_seconds,title) VALUES(?,?,?)",
                        [(video_id, 2, "fora"), (video_id, 72, "dentro"), (video_id, 100, "fora")],
                    )

                def fake_run(command, timeout=0):
                    Path(command[-1]).write_bytes(b"trimmed")
                    return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

                with patch.object(backend_main, "safe_video_path", return_value=source), \
                     patch.object(backend_main, "probe_video_duration", return_value=120), \
                     patch.object(backend_main, "run", side_effect=fake_run), \
                     patch.object(backend_main, "media_source_key", side_effect=str), \
                     patch.object(backend_main, "delete_video_caches") as caches:
                    result = backend_main.trim_video(video_id, backend_main.VideoTrimRequest(
                        start_seconds=70, end_seconds=95, as_new_file=True))

                with database.connect() as db:
                    original = db.execute("SELECT * FROM video_segments WHERE id=?", (video_id,)).fetchone()
                    copy = db.execute("SELECT * FROM video_segments WHERE id=?", (result["id"],)).fetchone()
                    original_markers = db.execute("SELECT COUNT(*) FROM video_markers WHERE video_id=?", (video_id,)).fetchone()[0]
                    markers = db.execute("SELECT offset_seconds,title FROM video_markers WHERE video_id=?", (result["id"],)).fetchall()
                    session = db.execute("SELECT status FROM video_sessions WHERE id=?", (session_id,)).fetchone()
            target = root / "clip_corte_1m10s-1m35s.mkv"
            caches.assert_not_called()
            self.assertEqual(source.read_bytes(), b"original")
            self.assertEqual(target.read_bytes(), b"trimmed")
            self.assertEqual(result["name"], target.name)
            self.assertNotEqual(result["id"], video_id)
            self.assertEqual((original["status"], original["description"], original["duration_seconds"]), ("done", "antiga", 120))
            self.assertEqual(original_markers, 3)
            self.assertEqual(session["status"], "done")
            self.assertEqual(copy["source_path"], str(target))
            self.assertEqual((copy["title"], copy["app"], copy["status"]), ("Partida · corte", "osu!", "pending"))
            self.assertEqual(copy["duration_seconds"], 25)
            self.assertEqual(copy["captured_at"], "2026-08-23T10:01:10-03:00")
            self.assertEqual([(row["offset_seconds"], row["title"]) for row in markers], [(2, "dentro")])

    def test_video_audio_cache_lives_under_selected_media_root(self):
        self.assertEqual(backend_main.VIDEO_AUDIO_TRACK_DIR.parent.parent, backend_main.MEDIA_ROOT)
        self.assertEqual(backend_main.VIDEO_THUMBNAIL_DIR.parent.parent, backend_main.MEDIA_ROOT)

    def test_legacy_media_cache_is_moved_to_selected_storage(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            old_audio = root / "old-audio"
            old_thumbnail = root / "old-thumbnail"
            new_audio = root / "selected" / "audio"
            new_thumbnail = root / "selected" / "thumbnail"
            old_audio.mkdir()
            old_thumbnail.mkdir()
            (old_audio / "track.m4a").write_bytes(b"audio")
            (old_thumbnail / "thumb.jpg").write_bytes(b"image")
            with patch.object(backend_main, "LEGACY_VIDEO_AUDIO_TRACK_DIR", old_audio), \
                 patch.object(backend_main, "LEGACY_VIDEO_THUMBNAIL_DIR", old_thumbnail), \
                 patch.object(backend_main, "VIDEO_AUDIO_TRACK_DIR", new_audio), \
                 patch.object(backend_main, "VIDEO_THUMBNAIL_DIR", new_thumbnail):
                backend_main.migrate_legacy_media_caches()
            self.assertEqual((new_audio / "track.m4a").read_bytes(), b"audio")
            self.assertEqual((new_thumbnail / "thumb.jpg").read_bytes(), b"image")
            self.assertFalse(old_audio.exists())
            self.assertFalse(old_thumbnail.exists())

    def test_marker_title_uses_frames_and_audio_from_twelve_second_window(self):
        segments = [
            {"start": 1, "end": 3, "source": "microphone", "text": "olha essa jogada"},
            {"start": 16, "end": 17, "source": "discord", "text": "boa"},
            {"start": 30, "end": 31, "text": "fala distante"},
        ]
        events = [
            {"start": 10, "end": 11, "event": "risada"},
            {"start": 35, "end": 36, "event": "evento distante"},
        ]
        with tempfile.TemporaryDirectory() as directory, \
             patch("app.backend.pipeline.extract_adaptive_keyframes", return_value=["frame-1", "frame-2"]) as extract, \
             patch("app.backend.pipeline.vision_model", return_value="vision-test"), \
             patch("app.backend.pipeline.ollama_json", return_value={"title": "Jogada seguida de risada"}) as analyze:
            title = marker_visual_title(
                Path(directory) / "video.mkv", 5, 40, segments, events,
                "960x540", Path(directory), 7,
            )

        self.assertEqual(title, "Jogada seguida de risada")
        extract.assert_called_once_with(
            Path(directory) / "video.mkv", 0.0, 17.0, 3.0, 6,
            "960x540", Path(directory), 7,
        )
        messages = analyze.call_args.args[1]
        self.assertEqual(messages[0]["images"], ["frame-1", "frame-2"])
        self.assertIn("olha essa jogada", messages[0]["content"])
        self.assertIn("risada", messages[0]["content"])
        self.assertNotIn("fala distante", messages[0]["content"])
        self.assertNotIn("evento distante", messages[0]["content"])

    def test_marker_title_does_not_call_vision_without_enough_frames(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch("app.backend.pipeline.extract_adaptive_keyframes", return_value=["frame-1"]), \
             patch("app.backend.pipeline.ollama_json") as analyze:
            title = marker_visual_title(
                Path(directory) / "video.mkv", 20, 60, [], [],
                "960x540", Path(directory), 0,
            )
        self.assertEqual(title, "")
        analyze.assert_not_called()

    def test_hour_long_video_requires_manual_audio_track_preparation(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(backend_main, "_VIDEO_AUDIO_TRACK_JOBS", {}), \
             patch.object(backend_main, "safe_video_path", return_value=Path(directory) / "video.mkv"), \
             patch.object(backend_main, "probe_video_audio_tracks", return_value=[{"track": 0}]), \
             patch.object(backend_main, "probe_video_duration", return_value=3600), \
             patch.object(backend_main, "video_audio_tracks_cached", return_value=False), \
             patch.object(backend_main._VideoAudioTrackJob, "start") as start:
            result = backend_main.video_audio_tracks("media:video-buffer/video.mkv")
        self.assertEqual(result["status"], "manual")
        start.assert_not_called()

    def test_video_under_one_hour_starts_audio_track_preparation(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(backend_main, "_VIDEO_AUDIO_TRACK_JOBS", {}), \
             patch.object(backend_main, "safe_video_path", return_value=Path(directory) / "video.mkv"), \
             patch.object(backend_main, "probe_video_audio_tracks", return_value=[{"track": 0}]), \
             patch.object(backend_main, "probe_video_duration", return_value=3599), \
             patch.object(backend_main, "video_audio_tracks_cached", return_value=False), \
             patch.object(backend_main._VideoAudioTrackJob, "start") as start:
            result = backend_main.video_audio_tracks("media:video-buffer/video.mkv")
        self.assertEqual(result["status"], "preparing")
        start.assert_called_once()

    def test_manual_request_starts_audio_tracks_for_long_video(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(backend_main, "_VIDEO_AUDIO_TRACK_JOBS", {}), \
             patch.object(backend_main, "safe_video_path", return_value=Path(directory) / "video.mkv"), \
             patch.object(backend_main, "probe_video_audio_tracks", return_value=[{"track": 0}]), \
             patch.object(backend_main, "probe_video_duration", return_value=18000), \
             patch.object(backend_main, "video_audio_tracks_cached", return_value=False), \
             patch.object(backend_main._VideoAudioTrackJob, "start") as start:
            result = backend_main.video_audio_tracks("media:video-buffer/video.mkv", prepare=True)
        self.assertEqual(result["status"], "preparing")
        start.assert_called_once()

    def test_opus_stems_go_to_a_container_that_accepts_them(self):
        """O ``-c:a copy`` só sobrevive se o contêiner aceitar o codec de origem.

        O gpu-screen-recorder grava Opus por padrão em mp4/mkv, e o muxer ipond
        de ``.m4a`` recusa Opus: o ffmpeg nem chegava a escrever o cabeçalho e a
        preparação inteira falhava sem faixa nenhuma.
        """
        commands = []

        def fake_popen(command, *_args, **_kwargs):
            commands.append(command)
            raise OSError("não executa de verdade")

        with tempfile.TemporaryDirectory() as directory, \
             patch.object(backend_main, "VIDEO_AUDIO_TRACK_DIR", Path(directory) / "tracks"), \
             patch.object(backend_main.subprocess, "Popen", side_effect=fake_popen):
            source = Path(directory) / "video.mp4"
            source.write_bytes(b"video")
            job = backend_main._VideoAudioTrackJob(
                source, [{"track": 0, "codec": "opus"}, {"track": 1, "codec": "aac"}])
            job.start()
            job._thread.join(5)

        self.assertEqual(len(commands), 1)
        command = commands[0]
        outputs = [argument for argument in command if argument.endswith((".m4a", ".opus"))]
        self.assertEqual([Path(output).suffix for output in outputs], [".opus", ".m4a"])
        # ``-movflags`` é opção privada do muxer mp4; no Ogg aborta o ffmpeg.
        self.assertEqual(command.count("-movflags"), 1)
        self.assertGreater(command.index("-movflags"), command.index(outputs[0]))

    def test_prepared_opus_stem_is_served_as_ogg(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(backend_main, "VIDEO_AUDIO_TRACK_DIR", Path(directory) / "tracks"):
            source = Path(directory) / "video.mp4"
            source.write_bytes(b"video")
            with patch.object(backend_main, "safe_video_path", return_value=source):
                cached = backend_main.video_audio_track_cache_path(source, 0, ".opus")
                cached.parent.mkdir(parents=True, exist_ok=True)
                cached.write_bytes(b"OggS")
                os.utime(cached, (source.stat().st_mtime + 1, source.stat().st_mtime + 1))
                response = backend_main.video_audio_track("media:video-buffer/video.mp4", 0)

        self.assertEqual(response.media_type, "audio/ogg")
        self.assertEqual(Path(response.path).suffix, ".opus")

    def test_recording_keeps_the_mix_ahead_of_the_isolated_tracks(self):
        """Players tocam só a primeira faixa, e o resto do Lume conta a partir dela.

        Sem a mixagem à frente ouvia-se apenas o microfone e a transcrição por
        fonte caía no caminho de faixa única, que espera 0=mixagem, 1=microfone,
        2=Discord, 3=sistema.
        """
        root = Path(__file__).resolve().parents[2]
        sources = {}
        for relative in ("config/captura-dia/video.conf", "bin/game-video-loop"):
            for line in (root / relative).read_text(encoding="utf-8").splitlines():
                if line.startswith("VIDEO_AUDIO="):
                    sources[relative] = line.split("=", 1)[1].strip("'\"").split(",")
                    break
        sources["set_video_settings"] = next(
            line.split("=", 1)[1].strip("'\"").split(",")
            for line in (root / "app/backend/main.py").read_text(encoding="utf-8").splitlines()
            if line.startswith("VIDEO_AUDIO=")
        )

        self.assertEqual(len(sources), 3)
        for origin, entries in sources.items():
            with self.subTest(origin=origin):
                self.assertEqual(entries[1:], [
                    "device:MicBus.monitor", "device:DiscordBus.monitor", "device:RecordBus.monitor",
                ])
                self.assertEqual(entries[0].split("|"), entries[1:])

    def test_video_audio_track_job_terminates_ffmpeg_when_cancelled(self):
        started = threading.Event()
        stopped = threading.Event()

        class FakeProcess:
            returncode = None

            def poll(self):
                return self.returncode

            def terminate(self):
                self.returncode = -15
                stopped.set()

            def wait(self, timeout=None):
                if self.returncode is None and not stopped.wait(timeout):
                    raise backend_main.subprocess.TimeoutExpired("ffmpeg", timeout)
                return self.returncode

            def kill(self):
                self.terminate()

        def fake_popen(*_args, **_kwargs):
            started.set()
            return FakeProcess()

        with tempfile.TemporaryDirectory() as directory, \
             patch.object(backend_main, "VIDEO_AUDIO_TRACK_DIR", Path(directory) / "tracks"), \
             patch.object(backend_main.subprocess, "Popen", side_effect=fake_popen):
            source = Path(directory) / "video.mkv"
            source.write_bytes(b"video")
            job = backend_main._VideoAudioTrackJob(source, [{"track": 0}])
            job.start()
            self.assertTrue(started.wait(1))
            job.cancel()
            job._thread.join(2)

        self.assertTrue(stopped.is_set())
        self.assertFalse(job._thread.is_alive())
        self.assertEqual(job.status, "cancelled")

    def test_unlink_retries_while_windows_handle_is_being_released(self):
        path = Path("temporarily-locked.m4a")
        with patch.object(Path, "unlink", side_effect=[PermissionError("locked"), PermissionError("locked"), None]) as unlink, \
             patch.object(backend_main.time, "sleep") as sleep:
            self.assertTrue(backend_main.unlink_with_retry(path, attempts=3, delay=0.01))
        self.assertEqual(unlink.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    def test_enqueue_unprocessed_discovers_counts_and_starts_automatic_worker(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"), \
             patch.object(backend_main, "unit_state", return_value={"active": False}), \
             patch.object(backend_main, "service_action", return_value=ActionResult(0)) as start, \
             patch.object(backend_main, "list_videos", return_value={"items": [], "total": 0}), \
             patch.object(pipeline, "discover", return_value={"audio": 1, "screen": 2}):
            database.initialize()
            pending_path = Path(directory) / "a.wav"
            error_path = Path(directory) / "s.png"
            old_path = Path(directory) / "old.wav"
            video_path = Path(directory) / "video.mp4"
            clip_path = Path(directory) / "clip.mp4"
            for path in (pending_path, error_path, old_path, video_path, clip_path):
                path.write_bytes(b"media")
            with database.connect() as db:
                db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('audio',?,'2026-08-09','pending')", (str(pending_path),))
                db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('screen',?,'2026-08-09','error')", (str(error_path),))
                db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('audio',?,'2026-08-01','skipped')", (str(old_path),))
                db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('audio','missing.wav','2026-07-30','error')")
                db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('screen','done.png','2026-07-31','done')")
                session_id = db.execute(
                    "INSERT INTO video_sessions(name,status) VALUES('Sessão antiga','pending')"
                ).lastrowid
                db.execute(
                    "INSERT INTO video_segments(source_path,captured_at,status,session_id) VALUES(?,'2026-08-02','pending',?)",
                    (str(clip_path), session_id),
                )
                db.execute(
                    "INSERT INTO video_segments(source_path,captured_at,status) VALUES(?,'2026-08-03','pending')",
                    (str(video_path),),
                )
            result = backend_main.enqueue_unprocessed()
            with database.connect() as db:
                statuses = {
                    row["source_path"]: row["status"]
                    for row in db.execute("SELECT source_path,status FROM captures")
                }
                session_status = db.execute("SELECT status FROM video_sessions WHERE id=?", (session_id,)).fetchone()[0]
                video_status = db.execute("SELECT status FROM video_segments WHERE source_path=?", (str(video_path),)).fetchone()[0]
        self.assertEqual(result["queued"], {"audio": 2, "screen": 1, "video": 1, "session": 1, "total": 5})
        self.assertEqual(result["discovered"], {"audio": 1, "screen": 2})
        self.assertEqual(result["requeued"], 1)
        self.assertEqual(result["missing"], 1)
        self.assertEqual(statuses[str(old_path)], "pending")
        self.assertEqual(statuses["missing.wav"], "skipped")
        self.assertEqual(statuses["done.png"], "done")
        self.assertEqual(session_status, "queued")
        self.assertEqual(video_status, "queued")
        start.assert_called_once_with("start", ["lume-process.service"], timeout=20, no_block=True)

    def test_pipeline_processes_queued_videos_and_sessions_before_daily_summaries(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"), \
             patch.object(pipeline, "discover", return_value={"audio": 0, "screen": 0}), \
             patch.object(pipeline, "process_video_session", return_value={"status": "done"}) as process_session, \
             patch.object(pipeline, "process_video_specific", return_value={"status": "done"}) as process_video, \
             patch.object(pipeline, "process_pending", side_effect=[0, 0]), \
             patch.object(pipeline, "generate_visual_activities", return_value=0), \
             patch.object(pipeline, "generate_hourly_summaries", return_value=0), \
             patch.object(pipeline, "cleanup_settings", return_value={"enabled": True}), \
             patch.object(pipeline, "mark_capture_cleanup_ready") as mark_cleanup_ready, \
             patch.object(pipeline, "cleanup_processed_capture_media", return_value={"deleted_total": 2}) as cleanup_media, \
             patch.object(pipeline, "generate_summary", return_value=True) as generate_summary:
            database.initialize()
            video_path = Path(directory) / "standalone.mp4"
            clip_path = Path(directory) / "session-clip.mp4"
            video_path.write_bytes(b"video")
            clip_path.write_bytes(b"clip")
            with database.connect() as db:
                session_id = db.execute(
                    "INSERT INTO video_sessions(name,status) VALUES('Sessão','queued')"
                ).lastrowid
                db.execute(
                    "INSERT INTO video_segments(source_path,captured_at,status,session_id) VALUES(?,'2026-08-01T10:00:00-03:00','pending',?)",
                    (str(clip_path), session_id),
                )
                db.execute(
                    "INSERT INTO video_segments(source_path,captured_at,status) VALUES(?,'2026-08-02T10:00:00-03:00','queued')",
                    (str(video_path),),
                )
            result = pipeline.run_pipeline(10, 100, True)

        process_session.assert_called_once_with(session_id)
        process_video.assert_called_once_with(video_path)
        summarized = {call.args[0] for call in generate_summary.call_args_list}
        self.assertIn("2026-08-01", summarized)
        self.assertIn("2026-08-02", summarized)
        marked = {call.args[0] for call in mark_cleanup_ready.call_args_list}
        self.assertIn("2026-08-01", marked)
        self.assertIn("2026-08-02", marked)
        cleanup_media.assert_called_once_with()
        self.assertEqual(result["sessions"], 1)
        self.assertEqual(result["videos"], 1)
        self.assertEqual(result["video_errors"], 0)
        self.assertEqual(result["cleanup"], {"deleted_total": 2})

    def test_a_day_whose_media_is_done_but_has_no_summary_is_consolidated(self):
        """"Pendente" tinha dois sentidos, e um deles não tinha como ser alcançado.

        O botão enfileira mídia pendente; um dia analisado semanas atrás não
        tem mídia pendente nenhuma e mesmo assim pode nunca ter ganhado
        narrativa. Como o worker só consolidava os dias que tocava na rodada,
        esse dia ficava sem resumo para sempre — com centenas de memórias
        dentro dele e nenhum lugar acusando o atraso.
        """
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"), \
             patch.object(pipeline, "discover", return_value={"audio": 0, "screen": 0}), \
             patch.object(pipeline, "process_pending", side_effect=[0, 0]), \
             patch.object(pipeline, "generate_visual_activities", return_value=0), \
             patch.object(pipeline, "generate_hourly_summaries", return_value=0), \
             patch.object(pipeline, "cleanup_settings", return_value={"enabled": False}), \
             patch.object(pipeline, "mark_capture_cleanup_ready"), \
             patch.object(pipeline, "generate_summary", return_value=True) as generate_summary:
            database.initialize()
            with database.connect() as db:
                # Dois dias antigos já analisados: um consolidado, outro não.
                for day in ("2026-07-30", "2026-08-14"):
                    db.execute(
                        """INSERT INTO captures(kind,source_path,captured_at,status,processed_at)
                           VALUES('screen',?,?,'done',?)""",
                        (f"media:telas/{day}.png", f"{day}T10:00:00-03:00", f"{day} 13:00:00"),
                    )
                db.execute(
                    """INSERT INTO summaries(day,narrative,model,generated_at)
                       VALUES('2026-07-30','já resumido','qwen','2026-07-31 03:00:00')""")
                # E um dia com mídia pendente de verdade, o caso de sempre.
                db.execute(
                    """INSERT INTO captures(kind,source_path,captured_at,status)
                       VALUES('screen','media:telas/hoje.png','2026-09-20T10:00:00-03:00','pending')""")
            pipeline.run_pipeline(10, 100, True)

        consolidados = [call.args[0] for call in generate_summary.call_args_list]
        self.assertIn("2026-08-14", consolidados, "o dia sem resumo continuou sem resumo")
        self.assertIn("2026-09-20", consolidados)
        self.assertNotIn("2026-07-30", consolidados, "um dia já consolidado foi refeito à toa")
        # O atrasado entra depois do que esta rodada tocou: primeiro o que a
        # pessoa acabou de capturar, e o arquivo morto na sequência.
        self.assertLess(consolidados.index("2026-09-20"), consolidados.index("2026-08-14"))

    def test_a_summary_older_than_its_own_memories_is_redone(self):
        """Um resumo que não cobre o próprio dia trava a limpeza segura, com razão.

        Quando mais capturas do mesmo dia são analisadas depois da
        consolidação, a narrativa passa a descrever só parte do dia e a
        contagem registrada para a limpeza fica velha. A limpeza então recusa
        apagar a mídia bruta — e, como o dia *tem* resumo, nada o reconsolidava:
        o espaço ficava preso para sempre.
        """
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"), \
             patch.object(pipeline, "discover", return_value={"audio": 0, "screen": 0}), \
             patch.object(pipeline, "process_pending", side_effect=[0, 0]), \
             patch.object(pipeline, "generate_visual_activities", return_value=0), \
             patch.object(pipeline, "generate_hourly_summaries", return_value=0), \
             patch.object(pipeline, "cleanup_settings", return_value={"enabled": False}), \
             patch.object(pipeline, "mark_capture_cleanup_ready"), \
             patch.object(pipeline, "generate_summary", return_value=True) as generate_summary:
            database.initialize()
            with database.connect() as db:
                db.execute(
                    """INSERT INTO captures(kind,source_path,captured_at,status,processed_at)
                       VALUES('screen','media:telas/a.png','2026-09-01T10:00:00-03:00','done',
                              '2026-09-08 16:00:00')""")
                db.execute(
                    """INSERT INTO summaries(day,narrative,model,generated_at)
                       VALUES('2026-09-01','narrativa parcial','qwen','2026-09-08 16:09:19')""")
                # A memória que chegou depois do resumo: é ela que deixa a
                # narrativa incompleta e a limpeza bloqueada.
                db.execute(
                    """INSERT INTO captures(kind,source_path,captured_at,status,processed_at)
                       VALUES('screen','media:telas/b.png','2026-09-01T11:00:00-03:00','done',
                              '2026-09-09 08:40:28')""")
            pipeline.run_pipeline(10, 100, True)

        consolidados = [call.args[0] for call in generate_summary.call_args_list]
        self.assertIn("2026-09-01", consolidados,
                      "o dia com resumo defasado não foi reconsolidado")

    def test_a_day_that_fails_to_consolidate_does_not_abort_the_whole_run(self):
        """Um 400 do Ollama num dia deixava toda a fila parada até a próxima tentativa."""
        def failing_activities(day, force=False, **kwargs):
            if day == "2026-08-01":
                raise RuntimeError(
                    'Ollama recusou a requisição (HTTP 400): {"error":"exceed_context_size_error"}'
                )
            return 1

        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"), \
             patch.object(pipeline, "discover", return_value={"audio": 0, "screen": 0}), \
             patch.object(pipeline, "process_pending", side_effect=[0, 0]), \
             patch.object(pipeline, "generate_visual_activities", side_effect=failing_activities), \
             patch.object(pipeline, "generate_hourly_summaries", return_value=0), \
             patch.object(pipeline, "cleanup_settings", return_value={"enabled": False}), \
             patch.object(pipeline, "mark_capture_cleanup_ready"), \
             patch.object(pipeline, "generate_summary", return_value=True) as generate_summary:
            database.initialize()
            with database.connect() as db:
                for day in ("2026-08-01", "2026-08-02"):
                    db.execute(
                        """INSERT INTO captures(kind,source_path,captured_at,status)
                           VALUES('screen',?,?,'pending')""",
                        (f"media:telas/{day}.png", f"{day}T10:00:00-03:00"),
                    )
            result = pipeline.run_pipeline(10, 100, True)
            with database.connect() as db:
                run_status = db.execute(
                    "SELECT status FROM pipeline_runs ORDER BY id DESC LIMIT 1"
                ).fetchone()["status"]

        summarized = {call.args[0] for call in generate_summary.call_args_list}
        self.assertNotIn("2026-08-01", summarized)
        self.assertIn("2026-08-02", summarized)
        self.assertEqual(result["summary_errors"], 1)
        self.assertEqual(run_status, "done")

    def test_summary_queue_reports_the_active_day_and_preserves_failed_days(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"), \
             patch.object(pipeline, "discover", return_value={}), \
             patch.object(pipeline, "process_pending", return_value=0), \
             patch.object(pipeline, "days_pending_consolidation", return_value={"2026-08-21", "2026-08-22"}), \
             patch.object(pipeline, "generate_hourly_summaries", return_value=0), \
             patch.object(pipeline, "generate_summary", return_value=True), \
             patch.object(pipeline, "mark_capture_cleanup_ready"), \
             patch.object(pipeline, "cleanup_settings", return_value={"enabled": False}):
            seen = []

            def activities(day, *, report):
                report("Analisando imagens · grupo 2/8")
                with database.connect() as db:
                    job = backend_main.pipeline_summary_job(db)
                seen.append(job)
                self.assertIn(day, [entry["day"] for entry in job["days"]])
                self.assertEqual(job["stage"], "Analisando imagens · grupo 2/8")
                if day == "2026-08-22":
                    raise RuntimeError("resposta inválida")
                return 0

            with patch.object(pipeline, "generate_visual_activities", side_effect=activities):
                pipeline.run_pipeline(10, 100, True)
            final = seen[-1]
            self.assertEqual(final["title"], "Resumo de 21/08/2026")
            self.assertEqual(final["days"][1]["status"], "error")
            self.assertIn("1 com falha", final["detail"])

    def test_older_worker_shows_saved_evidence_without_claiming_current_stage(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with database.connect() as db:
                db.execute("INSERT INTO pipeline_runs(status,started_at) VALUES('running','2026-09-23 20:30:00')")
                db.execute("INSERT INTO summaries(day,generated_at) VALUES('2026-08-22','2026-09-23 23:54:00')")
                job = backend_main.pipeline_summary_job(db)
            self.assertIn("Último resultado", job["stage"])
            self.assertIn("22/08/2026", job["stage"])
            self.assertEqual(job["updated_at"], "2026-09-23T23:54:00Z")
            self.assertNotIn("progress", job)

    def test_selective_video_status_distinguishes_service_from_recording(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "video.conf"
            flag = root / "lume-video-recording"
            pause_flag = root / "lume-video-pausing"
            config.write_text(
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=clips\nPAUSE_OTHER_CAPTURES=true\n",
                encoding="utf-8",
            )
            with (
                patch.object(backend_main, "VIDEO_CONFIG", config),
                patch.object(backend_main, "video_activity_flag", return_value=flag),
                patch.object(backend_main, "video_recording_flag", return_value=pause_flag),
                patch.object(backend_main, "unit_state", return_value={"active": True, "active_state": "active"}),
            ):
                waiting = selective_video_status()
                self.assertTrue(waiting["service_active"])
                self.assertFalse(waiting["recording"])
                flag.write_text(json.dumps({"window": "Discord — chamada", "started_at": 1786200000.0}), encoding="utf-8")
                recording = selective_video_status()
            self.assertTrue(recording["recording"])
            self.assertEqual(recording["mode"], "clips")
            self.assertEqual(recording["window"], "Discord — chamada")
            self.assertEqual(recording["started_at"], 1786200000.0)
            self.assertFalse(recording["pausing_captures"])
            self.assertTrue(recording["pause_other_captures"])

    def test_end_video_session_only_during_the_focus_countdown(self):
        """"Forçar encerramento" só existe enquanto a folga fora do jogo corre."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            flag = root / "lume-video-active"
            request = root / "lume-video-end-session"
            now = 1_800_000_000.0
            flag.write_text(json.dumps({"window": "Jogo", "started_at": now - 60,
                                        "focus_grace_deadline": None}), encoding="utf-8")
            with (
                patch.object(backend_main, "VIDEO_CONFIG", root / "missing.conf"),
                patch.object(backend_main, "video_activity_flag", return_value=flag),
                patch.object(backend_main, "video_recording_flag", return_value=root / "pausing"),
                patch.object(backend_main, "video_end_request_flag", return_value=request),
                patch.object(backend_main.time, "time", return_value=now),
                patch.object(backend_main, "unit_state", return_value={"active": True}),
            ):
                os.utime(flag, (now, now))
                self.assertIsNone(selective_video_status()["focus_grace_remaining"])
                with self.assertRaises(backend_main.HTTPException) as failure:
                    backend_main.end_video_session()
                self.assertEqual(failure.exception.status_code, 409)
                self.assertFalse(request.exists())

                flag.write_text(json.dumps({"window": "Jogo", "started_at": now - 60,
                                            "focus_grace_deadline": now + 42}), encoding="utf-8")
                os.utime(flag, (now, now))
                result = backend_main.end_video_session()
            self.assertEqual(result["focus_grace_remaining"], 42.0)
            self.assertTrue(request.exists())

    def test_selective_video_status_expires_abandoned_activity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            flag = root / "lume-video-active"
            pause_flag = root / "lume-video-recording"
            now = 1_800_000_000.0
            started = now - (452 * 3600 + 17 * 60 + 57)
            flag.write_text(json.dumps({"window": "Tabletop Simulator", "started_at": started}), encoding="utf-8")
            pause_flag.touch()
            with (
                patch.object(backend_main, "VIDEO_CONFIG", root / "missing.conf"),
                patch.object(backend_main, "video_activity_flag", return_value=flag),
                patch.object(backend_main, "video_recording_flag", return_value=pause_flag),
                patch.object(backend_main.time, "time", return_value=now),
                patch.object(backend_main, "unit_state", return_value={"active": True}),
            ):
                os.utime(flag, (started, started))
                expired = selective_video_status()
                self.assertTrue(expired["service_active"])
                self.assertFalse(expired["recording"])
                self.assertIsNone(expired["started_at"])
                self.assertEqual(expired["window"], "")
                self.assertFalse(expired["pausing_captures"])

                # A long session is valid when the recorder still updates it.
                os.utime(flag, (now - 2, now - 2))
                live = selective_video_status()
                self.assertTrue(live["recording"])
                self.assertEqual(live["started_at"], started)
                self.assertTrue(live["pausing_captures"])

                os.utime(flag, (now - 16, now - 16))
                self.assertFalse(selective_video_status()["recording"])

    def test_activity_groups_follow_app_and_temporal_continuity(self):
        rows = [
            {"id": 1, "app": "Code", "captured_at": "2026-08-08T10:00:00-03:00"},
            {"id": 2, "app": "Code", "captured_at": "2026-08-08T10:08:00-03:00"},
            {"id": 3, "app": "Browser", "captured_at": "2026-08-08T10:09:00-03:00"},
            {"id": 4, "app": "Code", "captured_at": "2026-08-08T10:25:00-03:00"},
        ]
        self.assertEqual([[item["id"] for item in group] for group in _activity_groups(rows)], [[1, 2], [3], [4]])

    def test_activity_groups_use_window_app_despite_ai_label_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = []
            for index, label in enumerate(("Crunchyroll | Brave Browser", "Crunchyroll (pt-BR)", "Brave | brave-browser")):
                path = Path(directory) / f"frame-{index}.png"
                path.with_suffix(".png.window").write_text(
                    f"Yomi no Tsugai - Episódio {index + 1} - Brave | brave-browser", encoding="utf-8"
                )
                rows.append({"id": index, "app": label, "source_path": str(path),
                             "captured_at": f"2026-09-17T20:17:{index * 10:02d}-03:00"})
            groups = _activity_groups(rows)
            self.assertEqual([[row["id"] for row in group] for group in groups], [[0, 1, 2]])
            self.assertEqual(groups[0][0]["app"], "brave-browser")
            self.assertEqual(rows[0]["app"], "Crunchyroll | Brave Browser")

    def test_activity_window_identity_keeps_apps_and_long_breaks_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            rows = []
            for index, (app, minute) in enumerate((("brave-browser", "00"), ("org.kde.dolphin", "01"), ("brave-browser", "20"))):
                path = Path(directory) / f"frame-{index}.png"
                path.with_suffix(".png.window").write_text(f"Título | {app}", encoding="utf-8")
                rows.append({"id": index, "app": "Mesmo rótulo da IA", "source_path": str(path),
                             "captured_at": f"2026-09-17T20:{minute}:00-03:00"})
            self.assertEqual([[row["id"] for row in group] for group in _activity_groups(rows)], [[0], [1], [2]])

    def test_visual_activity_batch_fits_the_vision_image_ceiling(self):
        self.assertLessEqual(
            pipeline.ACTIVITY_BATCH_FRAMES + pipeline.ACTIVITY_CONTEXT_FRAMES,
            pipeline.MAX_VISION_IMAGES_PER_REQUEST,
        )

    def test_visual_activity_shrinks_the_batch_when_the_context_overflows(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            root = Path(directory)
            database.initialize()
            with database.connect() as db:
                for index in range(20):
                    image = root / f"screen-{index}.png"
                    image.write_bytes(b"png")
                    db.execute(
                        """INSERT INTO captures(kind,source_path,captured_at,status,app,title,text)
                           VALUES('screen',?,?,'done','Code',?,?)""",
                        (str(image), f"2026-08-08T10:{index:02d}:00-03:00", f"Tela {index}", f"Descrição {index}"),
                    )
            sizes = []

            def fake_ollama(_model, messages, **_kwargs):
                if not messages[0].get("images"):
                    return {"title": "Sessão completa", "narrative": "Consolidada", "events": [], "tags": []}
                sizes.append(len(messages[0]["images"]))
                if len(sizes) == 1:
                    raise RuntimeError(
                        'Ollama recusou a requisição (HTTP 400): {"error":"exceed_context_size_error"}'
                    )
                return {"title": "Lote", "narrative": "Mudanças", "events": [], "tags": [], "key_frames": [1]}

            with patch.object(pipeline, "_activity_image", return_value="aW1hZ2U="), \
                 patch.object(pipeline, "synchronized_audio_context", return_value=""), \
                 patch.object(pipeline, "ollama_json", side_effect=fake_ollama):
                self.assertEqual(generate_visual_activities("2026-08-08", force=True), 1)
            self.assertEqual(sizes[0], pipeline.ACTIVITY_BATCH_FRAMES)
            self.assertLess(sizes[1], sizes[0])  # o estouro reduz o lote em vez de derrubar o dia
            with database.connect() as db:
                activity = db.execute("SELECT * FROM activity_sessions").fetchone()
            self.assertEqual(activity["source_count"], 20)

    def test_visual_activity_uses_all_frames_across_overlapping_batches(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            root = Path(directory)
            database.initialize()
            with database.connect() as db:
                for index in range(35):
                    image = root / f"screen-{index}.png"
                    image.write_bytes(b"png")
                    db.execute(
                        """INSERT INTO captures(kind,source_path,captured_at,status,app,title,text)
                           VALUES('screen',?,?,'done','Code',?,?)""",
                        (str(image), f"2026-08-08T10:{index:02d}:00-03:00", f"Tela {index}", f"Descrição {index}"),
                    )
            def fake_ollama(_model, messages, **_kwargs):
                if messages[0].get("images"):
                    return {"title": "Lote", "narrative": "Mudanças do lote", "events": ["edição"], "tags": ["código"], "key_frames": [1]}
                return {"title": "Sessão completa", "narrative": "Narrativa consolidada", "events": ["início", "fim"], "tags": ["código"]}
            with patch.object(pipeline, "_activity_image", return_value="aW1hZ2U="), patch.object(pipeline, "synchronized_audio_context", return_value=""), patch.object(pipeline, "ollama_json", side_effect=fake_ollama) as mocked:
                self.assertEqual(generate_visual_activities("2026-08-08", force=True), 1)
            batches = -(-35 // pipeline.ACTIVITY_BATCH_FRAMES)
            self.assertEqual(mocked.call_count, batches + 1)  # lotes visuais + síntese
            with database.connect() as db:
                activity = db.execute("SELECT * FROM activity_sessions").fetchone()
            self.assertEqual(activity["source_count"], 35)
            self.assertEqual(len(json.loads(activity["capture_ids_json"])), 35)

    def test_visual_activity_sends_original_window_and_separates_ai_context(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            root = Path(directory)
            database.initialize()
            image = root / "screen.png"
            image.write_bytes(b"png")
            image.with_suffix(".png.window").write_text("Yomi no Tsugai - Episódio 21 | brave-browser", encoding="utf-8")
            with database.connect() as db:
                db.execute("""INSERT INTO captures(kind,source_path,captured_at,status,app,title,text)
                              VALUES('screen',?,'2026-09-17T20:17:00-03:00','done','Aplicativo inferido','Título inferido','Descrição incerta')""", (str(image),))
            with patch.object(pipeline, "_activity_image", return_value="aW1hZ2U="), \
                 patch.object(pipeline, "synchronized_audio_context", return_value="[+0s; fonte=system] fala do episódio"), \
                 patch.object(pipeline, "ollama_json", return_value={"title": "Assistindo a Yomi no Tsugai"}) as call:
                generate_visual_activities("2026-09-17", force=True)
            prompt = call.call_args.args[1][0]["content"]
            self.assertIn('"janela_capturada": "Yomi no Tsugai - Episódio 21 | brave-browser"', prompt)
            self.assertIn('"descricao_anterior_da_ia": "Descrição incerta"', prompt)
            self.assertIn("2026-09-17T20:17:00-03:00", prompt)
            self.assertIn("fonte=system", prompt)

    def test_large_activity_merge_keeps_every_batch_and_valid_json(self):
        batches = [pipeline._activity_batch_summary(
            {"title": f"Lote {index}", "narrative": "x" * 4000, "events": [f"evento-{index}"]},
            f"2026-09-17T{index // 60:02d}:{index % 60:02d}:00-03:00",
            f"2026-09-17T{index // 60:02d}:{index % 60:02d}:30-03:00",
        ) for index in range(20)]
        received = []

        def fake_merge(_model, messages, **kwargs):
            payload = messages[0]["content"].split("\n", 1)[1]
            self.assertLessEqual(len(payload), 24100)
            chunk = json.loads(payload)
            received.extend(item["title"] for item in chunk)
            return {"title": "União", "narrative": "Síntese", "events": []}

        with patch.object(pipeline, "ollama_json", side_effect=fake_merge) as call:
            result = pipeline._merge_activity_batches(batches)
        self.assertGreater(call.call_count, 1)
        self.assertTrue(all(f"Lote {index}" in received for index in range(20)))
        self.assertEqual(result["started_at"], batches[0]["started_at"])
        self.assertEqual(result["ended_at"], batches[-1]["ended_at"])

    def test_activity_batch_serialization_handles_escaped_text(self):
        batch = pipeline._activity_batch_summary({"narrative": "\x00" * 4000, "events": ["\x00" * 300] * 12}, "start", "end")
        self.assertLessEqual(len(json.dumps(batch, ensure_ascii=False)), 10000)

    def test_activity_refresh_removes_replaced_groups_but_keeps_missing_media_analysis(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            root = Path(directory)
            database.initialize()
            day = "2026-09-17"
            with database.connect() as db:
                for index in range(1, 4):
                    path = root / f"{index}.png"
                    if index < 3:
                        path.write_bytes(b"png")
                    db.execute("""INSERT INTO captures(id,kind,source_path,captured_at,status,app)
                                  VALUES(?,'screen',?,?,'done','Browser')""", (index, str(path), f"{day}T20:00:0{index}-03:00"))
                current_key = pipeline.hashlib.sha1(f"{day}|Browser|1".encode()).hexdigest()
                for key, ids in ((current_key, [1, 2]), ("old-fragment", [1]), ("missing-image", [3]), ("partly-covered", [2, 3])):
                    db.execute("""INSERT INTO activity_sessions(activity_key,day,app,started_at,ended_at,source_count,capture_ids_json)
                                  VALUES(?,?,'Browser',?,?,?,?)""", (key, day, f"{day}T20:00:01-03:00", f"{day}T20:00:03-03:00", len(ids), json.dumps(ids)))
            with patch.object(pipeline, "ollama_json") as model:
                self.assertEqual(generate_visual_activities(day), 0)
                model.assert_not_called()
            with database.connect() as db:
                remaining = {row["activity_key"] for row in db.execute("SELECT activity_key FROM activity_sessions")}
            self.assertEqual(remaining, {current_key, "missing-image", "partly-covered"})

    def test_audio_priority_only_removes_duplicate_lower_track(self):
        segments = merge_transcript_sources({
            "microphone": [{"start": 1, "end": 3, "text": "vamos pela esquerda"}],
            "discord": [{"start": 1.1, "end": 3.1, "text": "vamos pela esquerda"}],
            "system": [{"start": 1.2, "end": 3.2, "text": "inimigo no objetivo"}],
        })
        self.assertEqual([item["source"] for item in segments], ["microphone", "system"])

    def test_three_audio_tracks_keep_their_origin(self):
        segments = merge_transcript_sources({
            "microphone": [{"start": 2, "end": 3, "text": "eu"}],
            "discord": [{"start": 1, "end": 2, "text": "pessoa na call"}],
            "system": [{"start": 1.5, "end": 2.5, "text": "vídeo"}],
        })
        self.assertEqual([item["source"] for item in segments], ["discord", "system", "microphone"])
        self.assertEqual(segments[-1]["speaker"], "self")

    def test_processed_three_channel_audio_is_atomically_compacted_to_mono(self):
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "capture.wav"
            samples = array("h")
            for index in range(16000):
                samples.extend((1000 if index % 2 else -1000, 500, -250))
            with wave.open(str(audio), "wb") as target:
                target.setnchannels(3)
                target.setsampwidth(2)
                target.setframerate(16000)
                target.writeframes(samples.tobytes())
            self.assertTrue(compact_processed_audio(audio))
            with wave.open(str(audio), "rb") as result:
                self.assertEqual(result.getnchannels(), 1)
                self.assertEqual(result.getframerate(), 16000)
                self.assertAlmostEqual(result.getnframes() / result.getframerate(), 1.0, places=2)
            self.assertEqual(list(Path(directory).glob(".*.mono-*.wav")), [])

    def test_separated_audio_tracks_keep_origin_and_timeline(self):
        segments = merge_source_transcripts(
            [{"start": 2, "end": 4, "text": "minha fala"}],
            [{"start": 1, "end": 3, "text": "fala da call"}],
        )
        self.assertEqual([item["source"] for item in segments], ["system", "microphone"])
        self.assertEqual(segments[1]["speaker"], "self")
        overlaps = overlapping_sources(segments[1:], segments[:1])
        self.assertEqual(overlaps[0]["event"], "fala sobreposta")
        self.assertEqual((overlaps[0]["start"], overlaps[0]["end"]), (2.0, 3.0))

    def test_screen_receives_only_nearby_speech_from_overlapping_audio(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with database.connect() as db:
                db.execute(
                    """INSERT INTO captures(kind,source_path,captured_at,status,duration_seconds,transcript_segments_json)
                       VALUES('audio','/audio.wav','2026-08-08T10:00:00-03:00','done',900,?)""",
                    ('[{"start":110,"end":125,"text":"contexto próximo"},'
                     '{"start":500,"end":510,"text":"fala distante"}]',),
                )
            context = synchronized_audio_context("2026-08-08T10:02:00-03:00", radius_seconds=30)
            self.assertIn("contexto próximo", context)
            self.assertNotIn("fala distante", context)

    def test_summary_groups_overlapping_audio_and_screens_as_one_moment(self):
        rows = [
            {"captured_at": "2026-08-08T10:00:00-03:00", "kind": "audio", "app": "RecordBus",
             "title": "Conversa", "text": "Falamos sobre o deploy", "duration_seconds": 900},
            {"captured_at": "2026-08-08T10:05:00-03:00", "kind": "screen", "app": "Terminal",
             "title": "Publicação", "text": "Comando de deploy em execução", "duration_seconds": None},
        ]
        context = multimodal_context(rows, 10000)
        self.assertEqual(context.count("MOMENTO MULTIMODAL"), 1)
        self.assertIn("Falamos sobre o deploy", context)
        self.assertIn("Comando de deploy em execução", context)

    def test_summary_context_includes_exact_recorded_video_duration(self):
        rows = [{
            "id": 7,
            "captured_at": "2026-08-08T20:00:00-03:00",
            "kind": "video",
            "app": "Beat Saber",
            "title": "Sessão completa",
            "text": "Gameplay analisada",
            "duration_seconds": 7384.6,
        }]
        context = multimodal_context(rows, 10000)
        self.assertIn("DURAÇÃO REGISTRADA DO VÍDEO: 02:03:05", context)
        self.assertIn("7384.6 segundos", context)

    def test_game_counter_duration_is_split_at_midnight_and_overrides_ai_estimate(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with database.connect() as db:
                db.execute(
                    """INSERT INTO game_activity_sessions(
                           session_key,app,window,capture_mode,started_at,last_seen_at,ended_at,duration_seconds)
                       VALUES('session-1','osu!','osu! | osu!.exe','clips',?,?,?,5400)""",
                    ("2026-08-08T23:30:00-03:00", "2026-08-09T01:00:00-03:00", "2026-08-09T01:00:00-03:00"),
                )
            first_day = game_activity_rows("2026-08-08")
            second_day = game_activity_rows("2026-08-09")

        self.assertEqual(first_day[0]["duration_seconds"], 1800)
        self.assertEqual(second_day[0]["duration_seconds"], 3600)
        data = apply_exact_game_durations({
            "games": [{"title": "osu", "minutes": 5, "event": "Partida"}],
            "app_blocks": [{"app": "osu!.exe", "minutes": 8}],
        }, first_day)
        self.assertEqual(data["games"][0]["minutes"], 30)
        self.assertEqual(data["app_blocks"][0]["minutes"], 30)

    def test_video_loop_persists_the_sidebar_counter(self):
        from app.capture import winvideo

        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            loop = object.__new__(winvideo.VideoLoop)
            loop.session_started_at = datetime.fromisoformat("2026-08-08T20:00:00-03:00").timestamp()
            loop.game_session_key = ""
            loop._game_session_heartbeat = 0.0
            loop._begin_game_session("counter-session", "Beat Saber | Beat Saber.exe", "clips")
            with patch("app.capture.winvideo.time.time", return_value=loop.session_started_at + 615):
                loop._finish_game_session()
            with database.connect() as db:
                saved = db.execute(
                    "SELECT app,capture_mode,duration_seconds,ended_at FROM game_activity_sessions WHERE session_key='counter-session'"
                ).fetchone()

        self.assertEqual(saved["app"], "Beat Saber")
        self.assertEqual(saved["capture_mode"], "clips")
        self.assertAlmostEqual(saved["duration_seconds"], 615)
        self.assertTrue(saved["ended_at"])

    def test_bash_loop_counts_game_time_through_the_shared_cli(self):
        """O laço do Linux conta tempo pela mesma porta que o gravador do Windows."""
        from app.capture import gamesession

        started = datetime.fromisoformat("2026-08-08T20:00:00-03:00").timestamp()
        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            gamesession.main(["begin", "--key", "bash-session", "--window", "osu! | osu!",
                              "--mode", "clips", "--started", str(started)])
            gamesession.main(["heartbeat", "--key", "bash-session"])
            with database.connect() as db:
                partial = db.execute(
                    "SELECT ended_at,duration_seconds FROM game_activity_sessions WHERE session_key='bash-session'"
                ).fetchone()
            gamesession.main(["finish", "--key", "bash-session", "--started", str(started + 300)])
            with database.connect() as db:
                saved = db.execute(
                    "SELECT app,capture_mode,duration_seconds,ended_at FROM game_activity_sessions WHERE session_key='bash-session'"
                ).fetchone()

        self.assertIsNone(partial["ended_at"])
        self.assertGreater(partial["duration_seconds"], 0)
        self.assertEqual(saved["app"], "osu!")
        self.assertEqual(saved["capture_mode"], "clips")
        self.assertTrue(saved["ended_at"])

    def test_stale_game_session_is_closed_at_the_last_heartbeat(self):
        """Uma queda no meio da partida não pode contar o tempo até agora."""
        from app.capture import gamesession

        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with database.connect() as db:
                db.execute(
                    """INSERT INTO game_activity_sessions(
                           session_key,app,window,capture_mode,started_at,last_seen_at,ended_at,duration_seconds)
                       VALUES('queda','osu!','osu! | osu!','clips',?,?,NULL,0)""",
                    ("2026-08-08T20:00:00-03:00", "2026-08-08T21:00:00-03:00"),
                )
            gamesession.close_stale()
            with database.connect() as db:
                saved = db.execute(
                    "SELECT ended_at,duration_seconds FROM game_activity_sessions WHERE session_key='queda'"
                ).fetchone()

        self.assertEqual(saved["ended_at"], "2026-08-08T21:00:00-03:00")
        self.assertAlmostEqual(saved["duration_seconds"], 3600, places=1)

    def test_large_summary_context_represents_the_whole_day(self):
        rows = [
            {"captured_at": f"2026-08-07T{10 + index // 6:02d}:{(index % 6) * 10:02d}:00-03:00", "kind": "screen",
             "app": "App", "title": f"Momento {index}", "text": (f"evidência {index} " * 40), "duration_seconds": None}
            for index in range(30)
        ]
        context = multimodal_context(rows, 2400)
        self.assertLessEqual(len(context), 2400)
        self.assertIn("Momento 0", context)
        self.assertIn("Momento 29", context)

    def test_daily_narrative_depth_scales_with_memory_count(self):
        self.assertEqual(daily_narrative_target(256), "6 a 10 parágrafos substanciais")

    def test_long_video_image_budget_stays_below_vision_context_limit(self):
        self.assertEqual(min(MAX_VISION_IMAGES_PER_REQUEST, max(6, 80 // 2)), 16)
        self.assertEqual(min(MAX_VISION_IMAGES_PER_REQUEST, max(6, 80 // 8)), 10)

    def test_summary_includes_standalone_video_and_session_once_and_preserves_relevant(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with database.connect() as db:
                screen = db.execute("INSERT INTO captures(kind,source_path,captured_at,status,title) VALUES('screen','screen.png','2026-08-08T10:00:00-03:00','done','Print')").lastrowid
                video = db.execute("INSERT INTO video_segments(source_path,captured_at,status,title) VALUES('video.mkv','2026-08-08T11:00:00-03:00','done','Vídeo')").lastrowid
                session = db.execute("INSERT INTO video_sessions(name,status,summary) VALUES('Sessão','done','Resumo da sessão')").lastrowid
                db.execute("INSERT INTO video_segments(source_path,captured_at,status,title,session_id) VALUES('clip1.mkv','2026-08-08T12:00:00-03:00','done','Clipe 1',?)", (session,))
                db.execute("INSERT INTO video_segments(source_path,captured_at,status,title,session_id) VALUES('clip2.mkv','2026-08-08T12:05:00-03:00','done','Clipe 2',?)", (session,))
            rows = summary_source_rows("2026-08-08")
            self.assertEqual([row["kind"] for row in rows], ["screen", "video", "session"])
            relevant = validate_relevant_media({"relevant_media": {
                "screens": [{"id": screen, "reason": "estado importante"}],
                "videos": [{"id": video, "reason": "editar"}],
                "sessions": [{"id": session, "reason": "sessão marcante"}],
            }}, rows)
            self.assertEqual(len(relevant["sessions"]), 1)
            with database.connect() as db:
                self.assertEqual(db.execute("SELECT preserved FROM captures WHERE id=?", (screen,)).fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT preserved FROM video_segments WHERE id=?", (video,)).fetchone()[0], 1)
                self.assertTrue(all(row[0] for row in db.execute("SELECT preserved FROM video_segments WHERE session_id=?", (session,))))

    def test_relevant_media_recovers_ids_cited_by_summary_when_model_returns_empty_lists(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with database.connect() as db:
                screen = db.execute(
                    "INSERT INTO captures(kind,source_path,captured_at,status,title) VALUES('screen','screen.png','2026-08-08T10:00:00-03:00','done','Print citado')"
                ).lastrowid
                audio = db.execute(
                    "INSERT INTO captures(kind,source_path,captured_at,status,title) VALUES('audio','audio.wav','2026-08-08T10:01:00-03:00','done','Áudio citado')"
                ).lastrowid
            rows = summary_source_rows("2026-08-08")
            data = {
                "tasks": [{"text": "Revisar o momento", "source": f"[screen:{screen}] e [audio:{audio}]"}],
                "relevant_media": {"screens": [], "audio": [], "videos": [], "sessions": []},
            }
            relevant = validate_relevant_media(data, rows)
            self.assertEqual([item["id"] for item in relevant["screens"]], [screen])
            self.assertEqual([item["id"] for item in relevant["audio"]], [audio])
            with database.connect() as db:
                self.assertEqual(db.execute("SELECT preserved FROM captures WHERE id=?", (screen,)).fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT preserved FROM captures WHERE id=?", (audio,)).fetchone()[0], 1)

    def test_raw_cleanup_keeps_marked_files_and_processed_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            screen_dir, audio_dir, video_dir, clips_dir = (root / name for name in ("screen", "sounds", "video", "clips-test"))
            for path in (screen_dir, audio_dir, video_dir, clips_dir):
                path.mkdir()
            kept = screen_dir / "kept.png"; kept.write_bytes(b"kept")
            removed = screen_dir / "removed.png"; removed.write_bytes(b"removed")
            audio = audio_dir / "removed.wav"; audio.write_bytes(b"audio")
            video = video_dir / "removed.mkv"; video.write_bytes(b"video")
            with (
                patch.object(database, "DB_PATH", root / "lume.sqlite3"),
                patch.object(retention, "SCREEN_DIR", screen_dir),
                patch.object(retention, "AUDIO_DIR", audio_dir),
                patch.object(backend_main, "unit_state", return_value={"active": False}),
            ):
                database.initialize()
                with database.connect() as db:
                    db.execute("INSERT INTO captures(kind,source_path,captured_at,status,preserved) VALUES('screen',?,'2026-08-08T10:00:00-03:00','done',1)", (backend_main.media_source_key(kept),))
                    removed_id = db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('screen',?,'2026-08-08T10:01:00-03:00','done')", (backend_main.media_source_key(removed),)).lastrowid
                    db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('audio',?,'2026-08-08T10:02:00-03:00','done')", (backend_main.media_source_key(audio),))
                    video_id = db.execute("INSERT INTO video_segments(source_path,captured_at,status) VALUES(?,'2026-08-08T10:02:00-03:00','done')", (backend_main.media_source_key(video),)).lastrowid
                    db.execute("INSERT INTO summaries(day,narrative) VALUES('2026-08-08','Resumo pronto')")
                self.assertTrue(retention.mark_capture_cleanup_ready("2026-08-08"))
                result = backend_main.delete_unkept_raw_media()
                self.assertTrue(kept.is_file())
                self.assertFalse(removed.exists())
                self.assertFalse(audio.exists(), result)
                self.assertTrue(video.exists())
                self.assertEqual(result["deleted_total"], 2)
                with database.connect() as db:
                    self.assertIsNotNone(db.execute("SELECT id FROM captures WHERE id=?", (removed_id,)).fetchone())
                    self.assertIsNotNone(db.execute("SELECT id FROM video_segments WHERE id=?", (video_id,)).fetchone())

    def test_raw_cleanup_waits_when_a_day_changed_after_its_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            screen_dir, audio_dir = root / "screen", root / "audio"
            screen_dir.mkdir(); audio_dir.mkdir()
            first = screen_dir / "first.png"; first.write_bytes(b"first")
            later = screen_dir / "later.png"; later.write_bytes(b"later")
            with patch.object(database, "DB_PATH", root / "lume.sqlite3"), \
                 patch.object(retention, "SCREEN_DIR", screen_dir), \
                 patch.object(retention, "AUDIO_DIR", audio_dir):
                database.initialize()
                with database.connect() as db:
                    db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('screen',?,'2026-08-08T10:00:00-03:00','done')", (str(first),))
                    db.execute("INSERT INTO summaries(day,narrative) VALUES('2026-08-08','Resumo')")
                self.assertTrue(retention.mark_capture_cleanup_ready("2026-08-08"))
                with database.connect() as db:
                    db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('screen',?,'2026-08-08T11:00:00-03:00','done')", (str(later),))
                result = retention.cleanup_processed_capture_media()
            self.assertEqual(result["deleted_total"], 0)
            self.assertEqual(result["skipped"]["not_ready"], 2)
            self.assertTrue(first.exists())
            self.assertTrue(later.exists())

    def test_cleanup_setting_can_be_enabled_and_disabled(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(retention, "CLEANUP_CONFIG", Path(directory) / "cleanup.conf"):
            self.assertEqual(retention.cleanup_settings(), {"enabled": False})
            self.assertEqual(retention.save_cleanup_settings(True), {"enabled": True})
            self.assertEqual(retention.cleanup_settings(), {"enabled": True})
            self.assertEqual(retention.save_cleanup_settings(False), {"enabled": False})
            self.assertEqual(retention.cleanup_settings(), {"enabled": False})

    def test_cleanup_reconciles_a_legacy_audio_day_with_complete_summaries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            screen_dir, audio_dir = root / "screen", root / "sounds"
            screen_dir.mkdir(); audio_dir.mkdir()
            audio = audio_dir / "complete.wav"; audio.write_bytes(b"audio")
            with patch.object(database, "DB_PATH", root / "lume.sqlite3"), \
                 patch.object(retention, "SCREEN_DIR", screen_dir), \
                 patch.object(retention, "AUDIO_DIR", audio_dir):
                database.initialize()
                with database.connect() as db:
                    db.execute("INSERT INTO captures(kind,source_path,captured_at,status,processed_at) VALUES('audio',?,'2026-08-08T10:00:00-03:00','done','2026-08-09 10:00:00')", (str(audio),))
                    db.execute("INSERT INTO hourly_summaries(hour,title,narrative,source_count,generated_at) VALUES('2026-08-08T10','Hora','Pronta',1,'2026-08-09 11:00:00')")
                    db.execute("INSERT INTO summaries(day,narrative,generated_at) VALUES('2026-08-08','Resumo','2026-08-09 12:00:00')")
                result = retention.cleanup_processed_capture_media()
            self.assertEqual(result["ready_days"], ["2026-08-08"])
            self.assertEqual(result["deleted"], {"screen": 0, "audio": 1})
            self.assertFalse(audio.exists())
        self.assertEqual(daily_narrative_target(10), "2 a 4 parágrafos")

    def test_summary_generation_rejects_a_day_without_processed_sources(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with self.assertRaisesRegex(Exception, "Não há capturas processadas"):
                backend_main.generate_summary_now("2026-08-08")

    def test_capture_days_lists_only_processed_days_newest_first(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with database.connect() as db:
                db.executemany(
                    "INSERT INTO captures(kind,source_path,captured_at,status) VALUES('screen',?,?,?)",
                    [
                        ("/old.png", "2026-08-06T10:00:00-03:00", "done"),
                        ("/new.png", "2026-08-07T10:00:00-03:00", "done"),
                        ("/pending.png", "2026-08-08T10:00:00-03:00", "pending"),
                    ],
                )
            self.assertEqual(
                backend_main.capture_days()["items"],
                [{"day": "2026-08-07", "count": 1}, {"day": "2026-08-06", "count": 1}],
            )

    def test_queue_tracks_summary_for_requested_past_day(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()

            def state(unit):
                active = unit == "lume-summary@2026-08-07.service"
                return {
                    "active": active,
                    "active_state": "activating" if active else "inactive",
                }

            with patch.object(backend_main, "unit_state", side_effect=state):
                result = backend_main.pipeline_queue(limit=300, day="2026-08-07")
            self.assertTrue(result["running"])
            self.assertEqual(result["day"], "2026-08-07")
            self.assertEqual(result["jobs"][0]["id"], "daily-summary-2026-08-07")
            self.assertIn("07/08/2026", result["jobs"][0]["stage"])

    @unittest.skipUnless(os.name == "nt", "sufixo .exe é específico do Windows")
    def test_default_whisper_binary_uses_windows_executable_suffix(self):
        self.assertEqual(DEFAULT_WHISPER_BIN.name, "whisper-cli.exe")

    def test_models_come_from_video_config(self):
        from app.backend import pipeline

        with tempfile.TemporaryDirectory() as directory, \
             patch.object(pipeline, "CONFIG_DIR", Path(directory)), \
             patch.dict("os.environ", {}, clear=False):
            with patch.dict("os.environ", {"LUME_VISION_MODEL": "", "LUME_TEXT_MODEL": ""}):
                (Path(directory) / "video.conf").write_text(
                    "LUME_VISION_MODEL=qwen3-vl:4b\nLUME_TEXT_MODEL=qwen3.5:9b\n",
                    encoding="utf-8",
                )
                self.assertEqual(vision_model(), "qwen3-vl:4b")
                self.assertEqual(text_model(), "qwen3.5:9b")

    def test_screen_change_comparison_uses_portable_ffmpeg_helper(self):
        with tempfile.TemporaryDirectory() as directory:
            old = Path(directory) / "old.png"
            new = Path(directory) / "new.png"
            old.write_bytes(b"old")
            new.write_bytes(b"new")
            with patch("app.backend.pipeline.compare_images", return_value=2.9):
                self.assertFalse(visually_changed(old, new))
            with patch("app.backend.pipeline.compare_images", return_value=3.0):
                self.assertTrue(visually_changed(old, new))
            with patch("app.backend.pipeline.compare_images", return_value=None):
                self.assertTrue(visually_changed(old, new))

    def test_voice_identity_list_flags_similar_profiles_without_embedding(self):
        rows = [
            {"id": 1, "label": "Laura", "embedding_json": "[1,0]", "sample_count": 2, "created_at": "a", "updated_at": "b"},
            {"id": 2, "label": "Lara", "embedding_json": "[0.9,0.1]", "sample_count": 1, "created_at": "a", "updated_at": "b"},
            {"id": 3, "label": "Eu", "embedding_json": "[0,1]", "sample_count": 1, "created_at": "a", "updated_at": "b"},
        ]
        result = voice_identity_payloads(rows)
        self.assertEqual(result[0]["possible_duplicates"][0]["label"], "Lara")
        self.assertNotIn("embedding", result[0])
        self.assertEqual(result[2]["possible_duplicates"], [])

    def test_voice_profile_counts_one_vote_per_recording(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with database.connect() as db:
                identity_id = db.execute(
                    "INSERT INTO voice_identities(label,embedding_json) VALUES('Laura','[1,0]')"
                ).lastrowid
                first = db.execute(
                    "INSERT INTO captures(kind,source_path,captured_at,speakers_json) VALUES('audio','/a.wav','2026-01-01','[{\"id\":\"speaker_1\",\"identity_id\":1,\"confirmed\":true},{\"id\":\"speaker_2\",\"identity_id\":1,\"confirmed\":true}]')"
                ).lastrowid
                second = db.execute(
                    "INSERT INTO captures(kind,source_path,captured_at,speakers_json) VALUES('audio','/b.wav','2026-01-02','[{\"id\":\"speaker_1\",\"identity_id\":1,\"confirmed\":true}]')"
                ).lastrowid
                db.executemany(
                    "INSERT INTO speaker_observations VALUES('audio',?,?,?)",
                    [(first, "speaker_1", "[1,0]"), (first, "speaker_2", "[0.8,0.2]"), (second, "speaker_1", "[0,1]")],
                )
                self.assertEqual(rebuild_voice_identity(db, identity_id), 2)
                profile = db.execute("SELECT sample_count FROM voice_identities WHERE id=?", (identity_id,)).fetchone()
            self.assertEqual(profile["sample_count"], 2)

    def test_empty_voice_profile_is_removed_after_name_correction(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with database.connect() as db:
                identity_id = db.execute(
                    "INSERT INTO voice_identities(label,embedding_json,sample_count) VALUES('Nome errado','[1,0]',1)"
                ).lastrowid
                self.assertEqual(rebuild_voice_identity(db, identity_id), 0)
                profile = db.execute("SELECT id FROM voice_identities WHERE id=?", (identity_id,)).fetchone()
            self.assertIsNone(profile)

    def test_deleting_voice_profile_unlinks_samples_without_deleting_observations(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with database.connect() as db:
                identity_id = db.execute(
                    "INSERT INTO voice_identities(label,embedding_json) VALUES('Eu e Laura','[1,0]')"
                ).lastrowid
                capture_id = db.execute(
                    "INSERT INTO captures(kind,source_path,captured_at,speakers_json) VALUES('audio','/a.wav','2026-01-01',?)",
                    (json.dumps([{"id": "discord_1", "label": "Eu e Laura", "source": "discord", "identity_id": identity_id, "identified": True, "confirmed": True}]),),
                ).lastrowid
                db.execute(
                    "INSERT INTO speaker_observations VALUES('audio',?,?,?)",
                    (capture_id, "discord_1", "[1,0]"),
                )

            result = backend_main.delete_voice_identity(identity_id)

            with database.connect() as db:
                profile = db.execute("SELECT id FROM voice_identities WHERE id=?", (identity_id,)).fetchone()
                row = db.execute("SELECT speakers_json FROM captures WHERE id=?", (capture_id,)).fetchone()
                observation = db.execute(
                    "SELECT 1 FROM speaker_observations WHERE source_kind='audio' AND source_id=? AND speaker_id='discord_1'",
                    (capture_id,),
                ).fetchone()
            speaker = json.loads(row["speakers_json"])[0]
            self.assertTrue(result["ok"])
            self.assertIsNone(profile)
            self.assertEqual(speaker["label"], "Voz do Discord")
            self.assertNotIn("identity_id", speaker)
            self.assertIsNotNone(observation)

    def test_known_voice_is_only_applied_above_safe_threshold(self):
        profiles = [{"id": "speaker_1", "label": "Pessoa 1"}, {"id": "speaker_2", "label": "Pessoa 2"}]
        embeddings = {"speaker_1": [1.0, 0.0], "speaker_2": [0.6, 0.8]}
        known = [{"id": 7, "label": "Otávio", "embedding": [1.0, 0.0]}]
        identify_profiles(profiles, embeddings, known, threshold=.72)
        self.assertEqual(profiles[0]["label"], "Otávio")
        self.assertTrue(profiles[0]["identified"])
        self.assertEqual(profiles[1]["label"], "Pessoa 2")
        self.assertNotIn("identified", profiles[1])

    def test_whisper_repetition_loop_is_removed(self):
        segments = [
            {"start": index * 2, "end": index * 2 + 2, "text": "A CIDADE NO BRASIL"}
            for index in range(8)
        ] + [{"start": 16, "end": 17, "text": "Uma fala real"}]
        self.assertEqual(filter_hallucinated_segments(segments), [segments[-1]])

    def test_legitimate_repeated_reply_is_preserved(self):
        segments = [
            {"start": 0, "end": 1, "text": "sim"},
            {"start": 3, "end": 4, "text": "outra fala"},
            {"start": 5, "end": 6, "text": "sim"},
        ]
        self.assertEqual(filter_hallucinated_segments(segments), segments)

    def test_sonia_subtitle_credit_is_removed_even_when_it_only_appears_twice(self):
        segments = [
            {"start": 0, "end": 1, "text": "Legenda por Sônia Ruberti"},
            {"start": 30, "end": 31, "text": "Legenda por Sonia Ruberti."},
            {"start": 32, "end": 34, "text": "Esta fala é real"},
        ]
        self.assertEqual(filter_hallucinated_segments(segments), [segments[-1]])

    def test_real_sentence_about_subtitles_is_preserved(self):
        segment = {"start": 0, "end": 2, "text": "Eu ativei a legenda por causa do barulho"}
        self.assertEqual(filter_hallucinated_segments([segment]), [segment])

    def test_common_audio_persists_timestamps_speakers_and_events(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "2026-08-06_10-00-00.wav"
            audio.write_bytes(b"audio")
            transcription = {
                "title": "Trecho de áudio", "text": "Olá", "segments": [{"start": 1, "end": 2, "text": "Olá"}],
                "app": "RecordBus", "tags": ["áudio"], "duration": 3,
            }
            intelligence = {
                "segments": [{"start": 1, "end": 2, "text": "Olá", "speaker": "speaker_1", "events": ["risada"]}],
                "speakers": [{"id": "speaker_1", "label": "Pessoa 1", "sample_start": 1, "sample_end": 2, "duration": 1}],
                "events": [{"start": 1, "end": 2, "event": "risada", "confidence": .9}],
            }
            with (
                patch.object(database, "DB_PATH", root / "lume.sqlite3"),
                patch("app.backend.pipeline.transcribe", return_value=transcription),
                patch("app.backend.pipeline.analyze_video_audio", return_value=intelligence),
            ):
                result = process_specific(audio)
                with database.connect() as db:
                    row = database.row_dict(db.execute("SELECT * FROM captures WHERE id=?", (result["id"],)).fetchone())
            self.assertEqual(row["transcript_segments"][0]["start"], 1)
            self.assertEqual(row["transcript_segments"][0]["speaker"], "speaker_1")
            self.assertEqual(row["speakers"][0]["label"], "Pessoa 1")
            self.assertEqual(row["audio_events"][0]["event"], "risada")

    def test_partial_segmentation_window_is_padded_with_silence(self):
        import numpy as np

        samples = np.zeros(int(6.5 * 16000), dtype=np.float32)
        padded = pad_to_segmentation_window(samples)
        self.assertEqual(len(padded) % (SEGMENTATION_WINDOW_SECONDS * 16000), 0)
        self.assertEqual(len(padded), SEGMENTATION_WINDOW_SECONDS * 16000)

    def test_whole_segmentation_window_is_left_untouched(self):
        import numpy as np

        samples = np.zeros(SEGMENTATION_WINDOW_SECONDS * 16000 * 2, dtype=np.float32)
        self.assertIs(pad_to_segmentation_window(samples), samples)

    def test_turns_over_padded_silence_are_dropped_and_clipped(self):
        turns = turns_within_duration([
            {"start": 1.0, "end": 3.0, "speaker": "speaker_1"},
            {"start": 8.2, "end": 9.5, "speaker": "speaker_1"},
            {"start": 8.5, "end": 8.5, "speaker": "speaker_2"},
        ], 8.401)
        self.assertEqual([(item["start"], item["end"]) for item in turns], [(1.0, 3.0), (8.2, 8.401)])

    def test_audio_intelligence_assigns_speaker_and_event_by_overlap(self):
        segments = [{"start": 1.0, "end": 3.0, "text": "Olá"}]
        turns = [{"start": 0.5, "end": 2.8, "speaker": "speaker_1"}]
        events = [{"start": 2.0, "end": 3.5, "event": "risada", "confidence": .9}]
        result = enrich_segments(segments, turns, events)
        self.assertEqual(result[0]["speaker"], "speaker_1")
        self.assertEqual(result[0]["events"], ["risada"])

    def test_adjacent_audio_events_are_consolidated(self):
        result = consolidate_events([
            {"start": 0, "end": 5, "event": "risada", "confidence": .7},
            {"start": 4, "end": 9, "event": "risada", "confidence": .9},
        ])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["end"], 9)
        self.assertEqual(result[0]["confidence"], .9)

    def test_speaker_sample_uses_longest_clean_turn(self):
        profiles = speaker_profiles([
            {"start": 0, "end": 2, "speaker": "speaker_1"},
            {"start": 10, "end": 22, "speaker": "speaker_1"},
        ])
        self.assertEqual(profiles[0]["label"], "Pessoa 1")
        self.assertEqual(profiles[0]["sample_start"], 10)
        self.assertEqual(profiles[0]["sample_end"], 18)

    def test_speaker_sample_removes_overlapped_part_of_longest_turn(self):
        profiles = speaker_profiles([
            {"start": 0, "end": 10, "speaker": "speaker_1"},
            {"start": 20, "end": 24, "speaker": "speaker_1"},
        ], [{"start": 2, "end": 9, "event": "fala sobreposta", "confidence": 1}])
        self.assertEqual(profiles[0]["sample_start"], 20)
        self.assertEqual(profiles[0]["sample_end"], 24)
        self.assertFalse(profiles[0]["sample_overlapped"])

    def test_speaker_sample_is_flagged_when_no_clean_second_exists(self):
        profiles = speaker_profiles([
            {"start": 0, "end": 4, "speaker": "speaker_1"},
        ], [{"start": 0, "end": 4, "event": "fala sobreposta", "confidence": 1}])
        self.assertTrue(profiles[0]["sample_overlapped"])

    def test_short_clean_sample_is_not_called_overlapped(self):
        profiles = speaker_profiles([
            {"start": 0, "end": .8, "speaker": "speaker_1"},
        ], [{"start": 10, "end": 12, "event": "fala sobreposta", "confidence": 1}])
        self.assertFalse(profiles[0]["sample_overlapped"])

    def test_valid_json_misclassified_as_thinking_is_recovered(self):
        thinking = '{"title":"Capítulo 1","events":["Exploração"]}'
        self.assertEqual(recover_json_from_thinking("", thinking), thinking)

    def test_free_form_thinking_is_not_used_as_content(self):
        self.assertEqual(recover_json_from_thinking("", "Preciso analisar os frames primeiro."), "")

    def test_real_content_takes_precedence_over_thinking(self):
        content = '{"title":"Resposta final"}'
        self.assertEqual(recover_json_from_thinking(content, '{"title":"Rascunho"}'), content)

    def test_paused_capture_stays_paused_after_a_reboot(self):
        """Pausar desabilita a unit: só parar valia até o próximo boot."""
        manager = SystemdServiceManager()
        with (
            patch.object(backend_main, "get_manager", return_value=manager),
            patch.object(manager, "_run", return_value=ActionResult(0)) as mocked_run,
        ):
            backend_main.capture_action("pause")
            paused = mocked_run.call_args.args[0]
            backend_main.capture_action("resume")
            resumed = mocked_run.call_args.args[0]

        self.assertEqual(paused[:4], ["systemctl", "--user", "disable", "--now"])
        self.assertEqual(resumed[:4], ["systemctl", "--user", "enable", "--now"])
        for command in (paused, resumed):
            self.assertIn("captura-dia-audio.service", command)
            self.assertIn("captura-dia-tela.service", command)

    def test_capture_target_does_not_pull_a_disabled_capture(self):
        """O alvo puxava as capturas por `Wants=`, habilitadas ou não."""
        unit = Path(__file__).resolve().parents[2] / "systemd" / "captura-dia.target"
        body = unit.read_text(encoding="utf-8")
        directives = [line for line in body.splitlines() if not line.lstrip().startswith("#")]
        self.assertFalse([line for line in directives if line.startswith(("Wants=", "Requires="))])

    def test_transient_job_inherits_lume_data_paths(self):
        manager = SystemdServiceManager()
        with (
            patch.dict("os.environ", {
                "CAPTURA_DIA_ROOT": "/dados/lume",
                "CAPTURA_DIA_STORAGE_ROOT": "/midia/lume",
            }, clear=False),
            patch.object(manager, "_run", return_value=ActionResult(0)) as mocked_run,
        ):
            manager.run_transient("lume-video-1", ["python", "worker.py"])
        command = mocked_run.call_args.args[0]
        self.assertIn("--setenv=CAPTURA_DIA_ROOT=/dados/lume", command)
        self.assertIn("--setenv=CAPTURA_DIA_STORAGE_ROOT=/midia/lume", command)

    def test_collected_transient_unit_counts_as_already_stopped(self):
        result = ActionResult(5, stderr="Failed to stop lume-video-74.service: Unit lume-video-74.service not loaded.")
        self.assertTrue(stop_target_is_already_gone(result))

    def test_real_stop_error_is_not_ignored(self):
        result = ActionResult(1, stderr="Access denied")
        self.assertFalse(stop_target_is_already_gone(result))

    def test_cancelled_active_capture_is_not_restored_by_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            audio = root / "2026-08-06_10-00-00.wav"
            audio.write_bytes(b"audio")
            db_path = root / "lume.sqlite3"
            with patch.object(database, "DB_PATH", db_path):
                database.initialize()
                with database.connect() as db:
                    capture_id = db.execute(
                        "INSERT INTO captures(kind,source_path,captured_at,status) VALUES('audio',?,?,'pending')",
                        (str(audio), "2026-08-06T10:00:00-03:00"),
                    ).lastrowid

                def cancel_while_transcribing(_path):
                    with database.connect() as db:
                        db.execute(
                            "UPDATE captures SET status='skipped',error='removido manualmente da fila' WHERE id=?",
                            (capture_id,),
                        )
                    return {"title": "Áudio", "text": "texto", "app": "", "tags": [], "duration": 1}

                with patch("app.backend.pipeline.transcribe", side_effect=cancel_while_transcribing):
                    process_pending("audio", 1)
                with database.connect() as db:
                    row = db.execute("SELECT status,error FROM captures WHERE id=?", (capture_id,)).fetchone()
            self.assertEqual(row["status"], "skipped")
            self.assertEqual(row["error"], "removido manualmente da fila")

    def test_pipeline_queue_matches_audio_first_processing_order_and_reports_full_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "lume.sqlite3"
            stopped = {"active": False, "active_state": "inactive", "sub_state": "dead", "enabled_state": "disabled", "pid": "0"}
            with patch.object(database, "DB_PATH", db_path), patch.object(backend_main, "unit_state", return_value=stopped):
                database.initialize()
                with database.connect() as db:
                    db.executemany(
                        "INSERT INTO captures(kind,source_path,captured_at,status) VALUES(?,?,?,?)",
                        [
                            ("screen", "media:telas/older.png", "2026-08-07T10:00:00-03:00", "pending"),
                            ("audio", "media:audio/newer.wav", "2026-08-24T10:00:00-03:00", "pending"),
                            ("audio", "media:audio/retry.wav", "2026-08-25T10:00:00-03:00", "error"),
                        ],
                    )
                result = backend_main.pipeline_queue(limit=2, day="2026-08-26")
            self.assertEqual([item["kind"] for item in result["items"]], ["audio", "audio"])
            self.assertEqual(result["total"], 3)
            self.assertEqual(result["shown"], 2)
            self.assertEqual(result["counts"]["audio"], 2)
            self.assertEqual(result["counts"]["screen"], 1)
            self.assertEqual(result["counts"]["error"], 1)

    def test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time(self):
        """A média vem do tempo real medido, não do intervalo entre capturas."""
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "lume.sqlite3"
            stopped = {"active": False, "active_state": "inactive", "sub_state": "dead", "enabled_state": "disabled", "pid": "0"}
            with patch.object(database, "DB_PATH", db_path), patch.object(backend_main, "unit_state", return_value=stopped):
                database.initialize()
                with database.connect() as db:
                    db.executemany(
                        "INSERT INTO captures(kind,source_path,captured_at,status,process_ms,processed_at) VALUES(?,?,?,?,?,?)",
                        [
                            ("screen", "media:telas/a.png", "2026-08-26T10:00:00-03:00", "done", 20000, "2026-08-26T10:01:00"),
                            ("screen", "media:telas/b.png", "2026-08-26T10:02:00-03:00", "done", 16000, "2026-08-26T10:03:00"),
                            ("audio", "media:audio/a.wav", "2026-08-26T10:04:00-03:00", "done", 4000, "2026-08-26T10:05:00"),
                            ("screen", "media:telas/c.png", "2026-08-26T10:06:00-03:00", "pending", None, None),
                            ("screen", "media:telas/d.png", "2026-08-26T10:07:00-03:00", "pending", None, None),
                            ("audio", "media:audio/b.wav", "2026-08-26T10:08:00-03:00", "pending", None, None),
                        ],
                    )
                result = backend_main.pipeline_queue(limit=10, day="2026-08-26")
            self.assertEqual(result["speed"]["screen"], {"avg_ms": 18000, "samples": 2})
            self.assertEqual(result["speed"]["audio"], {"avg_ms": 4000, "samples": 1})
            self.assertEqual(result["speed"]["eta_seconds"], 40)

    def test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis(self):
        """Sem amostra do tipo pendente, um palpite atrapalharia mais que ajudar."""
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "lume.sqlite3"
            stopped = {"active": False, "active_state": "inactive", "sub_state": "dead", "enabled_state": "disabled", "pid": "0"}
            with patch.object(database, "DB_PATH", db_path), patch.object(backend_main, "unit_state", return_value=stopped):
                database.initialize()
                with database.connect() as db:
                    db.executemany(
                        "INSERT INTO captures(kind,source_path,captured_at,status,process_ms,processed_at) VALUES(?,?,?,?,?,?)",
                        [
                            ("audio", "media:audio/a.wav", "2026-08-26T10:00:00-03:00", "done", 4000, "2026-08-26T10:01:00"),
                            ("screen", "media:telas/c.png", "2026-08-26T10:02:00-03:00", "pending", None, None),
                        ],
                    )
                result = backend_main.pipeline_queue(limit=10, day="2026-08-26")
            self.assertEqual(result["speed"]["screen"], {"avg_ms": 0, "samples": 0})
            self.assertIsNone(result["speed"]["eta_seconds"])

    def test_pause_pipeline_stops_worker_and_preserves_active_item_for_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "lume.sqlite3"
            pause_flag = root / "paused"
            active = {"active": True, "active_state": "active", "sub_state": "running", "enabled_state": "enabled", "pid": "1"}
            with patch.object(database, "DB_PATH", db_path), \
                 patch.object(backend_main, "pipeline_pause_flag", return_value=pause_flag), \
                 patch.object(backend_main, "unit_state", return_value=active), \
                 patch.object(backend_main, "service_action", return_value=ActionResult(0)) as action:
                database.initialize()
                with database.connect() as db:
                    capture_id = db.execute(
                        "INSERT INTO captures(kind,source_path,captured_at,status) VALUES('audio','media:audio/a.wav','2026-08-26','processing')"
                    ).lastrowid
                    run_id = db.execute("INSERT INTO pipeline_runs(status) VALUES('running')").lastrowid
                result = backend_main.pause_pipeline()
                with database.connect() as db:
                    capture = db.execute("SELECT status,error FROM captures WHERE id=?", (capture_id,)).fetchone()
                    run = db.execute("SELECT status,error FROM pipeline_runs WHERE id=?", (run_id,)).fetchone()
            self.assertTrue(result["paused"])
            self.assertTrue(pause_flag.is_file())
            self.assertEqual(capture["status"], "pending")
            self.assertIn("retomada", capture["error"])
            self.assertEqual(run["status"], "paused")
            action.assert_called_once_with("stop", ["lume-process.service"], timeout=30)

    def test_resume_pipeline_clears_pause_and_restarts_same_worker(self):
        with tempfile.TemporaryDirectory() as directory:
            pause_flag = Path(directory) / "paused"
            pause_flag.write_text("paused\n", encoding="utf-8")
            inactive = {"active": False, "active_state": "inactive", "sub_state": "dead", "enabled_state": "enabled", "pid": "0"}
            with patch.object(backend_main, "pipeline_pause_flag", return_value=pause_flag), \
                 patch.object(backend_main, "unit_state", return_value=inactive), \
                 patch.object(backend_main, "service_action", return_value=ActionResult(0)) as action:
                result = backend_main.resume_pipeline()
            self.assertFalse(result["paused"])
            self.assertFalse(pause_flag.exists())
            action.assert_called_once_with("start", ["lume-process.service"], timeout=20, no_block=True)

    def test_parse_only_known_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tela.conf"
            path.write_text('CAPTURE_MODE=change\nEVIL=$(touch /tmp/no)\nMAX_GEOMETRY="1280x720>"\n')
            parsed = parse_shell_config(path)
            self.assertEqual(parsed["CAPTURE_MODE"], "change")
            self.assertEqual(parsed["MAX_GEOMETRY"], "1280x720>")
            self.assertNotIn("EVIL", parsed)

    def test_atomic_write(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.txt"
            atomic_write(path, "hello\n")
            self.assertEqual(path.read_text(), "hello\n")

    def test_bulk_delete_preserves_processed_processing_and_recording_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            screens, audio = root / "telas", root / "audio"
            screens.mkdir(); audio.mkdir()
            done_screen = screens / "done.png"
            pending_screen = screens / "pending.png"
            unindexed_screen = screens / "unindexed.png"
            old_audio = audio / "old.wav"
            processing_audio = audio / "processing.wav"
            recording_audio = audio / "recording.wav"
            for path in (done_screen, pending_screen, unindexed_screen, old_audio, processing_audio, recording_audio):
                path.write_bytes(b"media")
            pending_screen.with_suffix(".png.window").write_text("janela", encoding="utf-8")
            for index, path in enumerate((old_audio, processing_audio, recording_audio), start=1):
                os.utime(path, (index, index))

            with (
                patch.object(database, "DB_PATH", root / "lume.sqlite3"),
                patch.object(backend_main, "SCREEN_DIR", screens),
                patch.object(backend_main, "AUDIO_DIR", audio),
                patch.object(backend_main, "unit_state", return_value={"active": True}),
            ):
                database.initialize()
                with database.connect() as db:
                    db.executemany(
                        "INSERT INTO captures(kind,source_path,captured_at,status) VALUES(?,?,?,?)",
                        [
                            ("screen", backend_main.media_source_key(done_screen), "2026-01-01", "done"),
                            ("screen", backend_main.media_source_key(pending_screen), "2026-01-01", "pending"),
                            ("audio", backend_main.media_source_key(old_audio), "2026-01-01", "error"),
                            ("audio", backend_main.media_source_key(processing_audio), "2026-01-01", "processing"),
                            ("audio", backend_main.media_source_key(recording_audio), "2026-01-01", "pending"),
                        ],
                    )
                result = backend_main.delete_unprocessed_files()
                with database.connect() as db:
                    remaining = {row["status"] for row in db.execute("SELECT status FROM captures")}

            self.assertEqual(result["deleted"], {"screen": 2, "audio": 1})
            self.assertEqual(result["skipped"], {"done": 1, "processing": 1, "recording": 1})
            self.assertTrue(done_screen.exists())
            self.assertTrue(processing_audio.exists())
            self.assertTrue(recording_audio.exists())
            self.assertFalse(pending_screen.exists())
            self.assertFalse(pending_screen.with_suffix(".png.window").exists())
            self.assertFalse(unindexed_screen.exists())
            self.assertFalse(old_audio.exists())
            self.assertEqual(remaining, {"done", "processing", "pending"})

    def test_capture_session_sidecar(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "segmento.mp4"
            video.write_bytes(b"video")
            video.with_suffix(".mp4.session").write_text(
                "sessao-123\nHades II | hades2.exe\n", encoding="utf-8")
            self.assertEqual(captured_video_session(video), ("sessao-123", "Hades II"))

    def test_legacy_selective_video_becomes_a_session(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "2026-08-06_10-00-00.mp4"
            video.write_bytes(b"video")
            video.with_suffix(".mp4.window").write_text(
                "Hades II | hades2.exe\n", encoding="utf-8")
            self.assertEqual(
                captured_video_session(video),
                ("legacy-2026-08-06_10-00-00.mp4", "Hades II"),
            )

    def test_segments_with_same_capture_key_are_grouped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ("parte-1.mp4", "parte-2.mp4"):
                video = root / name
                video.write_bytes(b"video")
                video.with_suffix(".mp4.window").write_text(
                    "Hades II | hades2.exe\n", encoding="utf-8")
                video.with_suffix(".mp4.session").write_text(
                    "sessao-compartilhada\nHades II | hades2.exe\n", encoding="utf-8")
            db_path = root / "lume.sqlite3"
            recorded_at = datetime.fromisoformat("2026-08-06T10:00:00-03:00")
            with (
                patch.object(backend_main, "VIDEO_DIR", root),
                patch.object(database, "DB_PATH", db_path),
                patch.object(backend_main, "video_recorded_at", return_value=recorded_at),
                patch.object(backend_main, "probe_video_duration", return_value=62.5) as duration_probe,
                patch.object(backend_main, "unit_state", return_value={"active": False}),
            ):
                backend_main.list_videos()
                sessions = backend_main.list_video_sessions()["items"]
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0]["name"], "Hades II")
            self.assertEqual(sessions[0]["clip_count"], 2)
            self.assertEqual(sessions[0]["duration_seconds"], 125)
            self.assertEqual(sessions[0]["bytes"], 10)
            self.assertEqual(duration_probe.call_count, 2)

    def test_same_game_name_with_distinct_capture_keys_creates_distinct_sessions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index, key in enumerate(("sessao-a", "sessao-b"), start=1):
                video = root / f"parte-{index}.mp4"
                video.write_bytes(b"video")
                video.with_suffix(".mp4.window").write_text(
                    "Hades II | hades2.exe\n", encoding="utf-8")
                video.with_suffix(".mp4.session").write_text(
                    f"{key}\nHades II | hades2.exe\n", encoding="utf-8")
            db_path = root / "lume.sqlite3"
            with (
                patch.object(backend_main, "VIDEO_DIR", root),
                patch.object(database, "DB_PATH", db_path),
                patch.object(backend_main, "probe_video_duration", return_value=10),
                patch.object(backend_main, "unit_state", return_value={"active": False}),
            ):
                backend_main.list_videos()
                sessions = backend_main.list_video_sessions()["items"]

            self.assertEqual(len(sessions), 2)
            self.assertEqual({session["name"] for session in sessions}, {"Hades II"})
            self.assertEqual({session["clip_count"] for session in sessions}, {1})

    def test_detached_clip_stays_loose_and_keeps_its_analysis(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video = root / "trecho.mp4"
            video.write_bytes(b"video")
            video.with_suffix(".mp4.window").write_text(
                "Hades II | hades2.exe\n", encoding="utf-8")
            video.with_suffix(".mp4.session").write_text(
                "sessao-original\nHades II | hades2.exe\n", encoding="utf-8")
            db_path = root / "lume.sqlite3"
            with (
                patch.object(backend_main, "VIDEO_DIR", root),
                patch.object(database, "DB_PATH", db_path),
                patch.object(backend_main, "probe_video_duration", return_value=10),
                patch.object(backend_main, "unit_state", return_value={"active": False}),
            ):
                backend_main.list_videos()
                with database.connect() as db:
                    clip = db.execute("SELECT id,session_id FROM video_segments").fetchone()
                    db.execute(
                        "UPDATE video_segments SET title='Vitória',description='Análise preservada' WHERE id=?",
                        (clip["id"],),
                    )
                result = backend_main.detach_video_from_session(clip["session_id"], clip["id"])
                # Uma nova leitura encontra o sidecar antigo, mas respeita a
                # decisão manual e não agrupa o vídeo novamente.
                backend_main.list_videos()
                with database.connect() as db:
                    detached = db.execute(
                        "SELECT session_id,session_detached,title,description FROM video_segments WHERE id=?",
                        (clip["id"],),
                    ).fetchone()

            self.assertTrue(result["session_deleted"])
            self.assertIsNone(detached["session_id"])
            self.assertEqual(detached["session_detached"], 1)
            self.assertEqual((detached["title"], detached["description"]),
                             ("Vitória", "Análise preservada"))

    def test_existing_sessions_and_loose_video_can_be_merged_without_losing_clip_analysis(self):
        with tempfile.TemporaryDirectory() as directory, \
             patch.object(database, "DB_PATH", Path(directory) / "lume.sqlite3"):
            database.initialize()
            with database.connect() as db:
                first = db.execute(
                    "INSERT INTO video_sessions(name,status,summary,context) VALUES('Parte 1','done','Resumo um','Contexto um')"
                ).lastrowid
                second = db.execute(
                    "INSERT INTO video_sessions(name,status,summary,context) VALUES('Parte 2','done','Resumo dois','Contexto dois')"
                ).lastrowid
                clip_one = db.execute(
                    """INSERT INTO video_segments(source_path,captured_at,status,title,description,session_id)
                       VALUES('video-buffer/um.mp4','2026-08-08T10:00:00-03:00','done','Um','Análise um',?)""",
                    (first,),
                ).lastrowid
                clip_two = db.execute(
                    """INSERT INTO video_segments(source_path,captured_at,status,title,description,session_id)
                       VALUES('video-buffer/dois.mp4','2026-08-08T11:00:00-03:00','done','Dois','Análise dois',?)""",
                    (second,),
                ).lastrowid
                loose = db.execute(
                    """INSERT INTO video_segments(source_path,captured_at,status,title,description)
                       VALUES('video-buffer/tres.mp4','2026-08-08T12:00:00-03:00','done','Três','Análise três')"""
                ).lastrowid
                marker = db.execute(
                    "INSERT INTO video_markers(video_id,offset_seconds,title) VALUES(?,12,'Chefe')",
                    (clip_one,),
                ).lastrowid

            result = backend_main.join_video_session(backend_main.VideoJoinRequest(
                video_ids=[loose], session_ids=[first, second], name="Gameplay completa",
            ))

            with database.connect() as db:
                merged = db.execute("SELECT * FROM video_sessions WHERE id=?", (result["id"],)).fetchone()
                old_sessions = db.execute(
                    "SELECT count(*) total FROM video_sessions WHERE id IN (?,?)", (first, second)
                ).fetchone()["total"]
                clips = db.execute(
                    "SELECT id,session_id,sort_order,description FROM video_segments ORDER BY sort_order"
                ).fetchall()
                kept_marker = db.execute("SELECT video_id,title FROM video_markers WHERE id=?", (marker,)).fetchone()
            self.assertEqual(result["clips"], 3)
            self.assertEqual(result["merged_sessions"], 2)
            self.assertEqual(old_sessions, 0)
            self.assertEqual(merged["status"], "pending")
            self.assertIn("Contexto um", merged["context"])
            self.assertIn("Contexto dois", merged["context"])
            self.assertIn("Resumo um", merged["summary"])
            self.assertEqual([row["session_id"] for row in clips], [result["id"]] * 3)
            self.assertEqual([row["sort_order"] for row in clips], [0, 1, 2])
            self.assertEqual({row["description"] for row in clips}, {"Análise um", "Análise dois", "Análise três"})
            self.assertEqual((kept_marker["video_id"], kept_marker["title"]), (clip_one, "Chefe"))

    def test_monitor_key(self):
        self.assertEqual(monitor_key(Path("2026-07-21_01-02-03_mon1_DP-1.png")), "mon1_DP-1")

    def test_video_library_keeps_analysis_when_original_file_is_missing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            video_dir = root / "video-buffer"
            video_dir.mkdir()
            present = video_dir / "present.mp4"
            present.write_bytes(b"video")
            db_path = root / "lume.sqlite3"
            with (
                patch.object(backend_main, "VIDEO_DIR", video_dir),
                patch.object(database, "DB_PATH", db_path),
                patch.object(backend_main, "unit_state", return_value={"active": False}),
            ):
                database.initialize()
                with database.connect() as db:
                    db.execute(
                        "INSERT INTO video_segments(source_path,captured_at,status,title,description) VALUES(?,?,?,?,?)",
                        ("media:video-buffer/present.mp4", "2026-08-07T01:00:00-03:00", "done", "Presente", "Análise presente"),
                    )
                    db.execute(
                        "INSERT INTO video_segments(source_path,captured_at,status,title,description) VALUES(?,?,?,?,?)",
                        ("media:video-buffer/missing.mp4", "2026-08-07T02:00:00-03:00", "done", "Removido", "Análise preservada"),
                    )
                result = backend_main.list_videos()
            items = {item["name"]: item for item in result["items"]}
            self.assertTrue(items["present.mp4"]["available"])
            self.assertTrue(items["present.mp4"]["url"])
            self.assertFalse(items["missing.mp4"]["available"])
            self.assertEqual(items["missing.mp4"]["url"], "")
            self.assertEqual(items["missing.mp4"]["description"], "Análise preservada")

    def test_friend_name_is_private_for_web_research(self):
        terms = private_context_terms("Eu estava jogando com Dendena no CS2")
        self.assertIn("dendena", terms)
        self.assertFalse(safe_research_query("Dendena CS2 jogador famoso", terms))
        self.assertTrue(safe_research_query("CS2 Overpass mecânica da água", terms))

    def test_identity_search_is_always_blocked(self):
        self.assertFalse(safe_research_query("quem é o jogador Dendena", set()))
        self.assertFalse(safe_research_query("Dendena instagram profile", set()))

    def test_short_video_prompt_separates_context_from_visual_evidence(self):
        prompt = short_video_analysis_prompt(60, "Counter-Strike 2", "", "foi um clutch")
        self.assertIn("fatos visíveis ou audíveis", prompt)
        self.assertIn("afirmações fornecidas pelo usuário", prompt)
        self.assertIn("não deve ser apresentado como evidência visual", prompt)
        self.assertIn("nem plantar/proteger uma bomba com desarmá-la", prompt)
        self.assertIn("Primeiro reconstrua o acontecimento principal ENTRE os frames", prompt)
        self.assertIn("Não presuma que todo clipe de jogo é tático", prompt)
        self.assertIn("Use o HUD apenas como evidência secundária", prompt)
        self.assertIn("contraste entre fala e imagem", prompt)
        self.assertIn("clip_type, main_action, audio_visual_relation, interesting_moment", prompt)

    @patch("app.backend.pipeline.ollama_json")
    def test_review_preserves_fact_sources_and_checks_post_plant(self, mocked_ollama_json):
        mocked_ollama_json.return_value = {
            "title": "Clutch no pós-plant",
            "description": "No ataque, o jogador protegeu a bomba plantada.",
            "app": "Counter-Strike 2",
        }
        result = review_short_video_analysis({
            "clip_type": "humor",
            "main_action": "Tentativa de eliminar um adversário com a faca",
            "audio_visual_relation": "A fala prepara a tentativa mostrada nos frames",
            "interesting_moment": "Um aliado finaliza o adversário antes da facada",
            "observed_facts": ["Jogador no lado TR", "Vitória com 1 HP"],
            "user_context_facts": ["Foi um clutch", "A equipe plantou a bomba"],
            "inferences": ["Defesa do pós-plant"],
            "uncertain": ["Quem fez o plant"],
            "game_state": {"player_side": "TR", "objective_state": "bomba plantada"},
        }, "Foi um clutch; estávamos no ataque e meu time plantou.", {"findings": ""})
        sent_prompt = mocked_ollama_json.call_args.args[1][0]["content"]
        self.assertIn("descreva defesa do pós-plant, não desarme", sent_prompt)
        self.assertIn("não converta automaticamente gameplay em análise tática", sent_prompt)
        self.assertIn('"clip_type": "humor"', sent_prompt)
        self.assertIn("A fala prepara a tentativa mostrada nos frames", sent_prompt)
        self.assertEqual(result["observed_facts"], ["Jogador no lado TR", "Vitória com 1 HP"])
        self.assertEqual(result["user_context_facts"], ["Foi um clutch", "A equipe plantou a bomba"])
        self.assertEqual(result["game_state"]["player_side"], "TR")


class SilentTrackTests(unittest.TestCase):
    """Faixas mudas não valem uma transcrição.

    Numa sessão sem Discord a faixa dele é zero absoluto do início ao fim e
    ainda assim custava o mesmo whisper que uma faixa cheia de fala — cerca de
    um terço do tempo de cada capítulo. O limiar é conservador de propósito:
    fala baixa passa longe dele.
    """

    def _wav(self, directory: Path, amplitude: int, name: str = "t.wav") -> Path:
        import wave
        from array import array

        path = Path(directory) / name
        with wave.open(str(path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(16000)
            samples = array("h", [amplitude if index % 2 else -amplitude for index in range(16000)])
            handle.writeframes(samples.tobytes())
        return path

    def test_digital_silence_is_skipped(self):
        from app.backend.pipeline import track_is_silent

        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(track_is_silent(self._wav(Path(directory), 0)))

    def test_quiet_speech_is_still_transcribed(self):
        """-40 dBFS é fala baixa de verdade; pular isso perderia conversa."""
        from app.backend.pipeline import track_is_silent, track_peak_dbfs

        with tempfile.TemporaryDirectory() as directory:
            path = self._wav(Path(directory), 328)  # ~-40 dBFS
            self.assertAlmostEqual(track_peak_dbfs(path), -40, delta=1.5)
            self.assertFalse(track_is_silent(path))

    def test_inaudible_noise_is_skipped(self):
        from app.backend.pipeline import track_is_silent

        with tempfile.TemporaryDirectory() as directory:
            self.assertTrue(track_is_silent(self._wav(Path(directory), 20)))  # ~-64 dBFS

    def test_an_unreadable_file_is_never_assumed_silent(self):
        """Na dúvida, transcreve: perder fala é pior que gastar tempo."""
        from app.backend.pipeline import track_is_silent

        with tempfile.TemporaryDirectory() as directory:
            broken = Path(directory) / "quebrado.wav"
            broken.write_bytes(b"nao sou um wav")
            self.assertFalse(track_is_silent(broken))


class SpeechRegionTests(unittest.TestCase):
    """Detecção dos trechos com som, sobre amostras sintéticas."""

    def _samples(self, plano: list[tuple[float, int]], rate: int = 16000):
        import numpy

        partes = [numpy.full(int(rate * segundos), valor, dtype="<i2") for segundos, valor in plano]
        return numpy.concatenate(partes) if partes else numpy.zeros(0, dtype="<i2")

    def test_finds_the_loud_stretch_between_silences(self):
        from app.backend.pipeline import speech_regions

        samples = self._samples([(2.0, 0), (1.0, 8000), (2.0, 0)])
        regions = speech_regions(samples, 16000, pad_seconds=0.0, min_region_seconds=0.1)
        self.assertEqual(len(regions), 1)
        start, end = regions[0]
        self.assertAlmostEqual(start, 2.0, delta=0.1)
        self.assertAlmostEqual(end, 3.0, delta=0.1)

    def test_silence_yields_no_regions(self):
        from app.backend.pipeline import speech_regions

        self.assertEqual(speech_regions(self._samples([(3.0, 0)]), 16000), [])

    def test_padding_widens_the_region_without_leaving_the_track(self):
        """A folga não pode gerar tempo negativo nem passar do fim do áudio."""
        from app.backend.pipeline import speech_regions

        samples = self._samples([(0.2, 8000), (1.0, 0), (0.2, 8000)])
        for start, end in speech_regions(samples, 16000, pad_seconds=0.5, min_region_seconds=0.05):
            self.assertGreaterEqual(start, 0.0)
            self.assertLessEqual(end, samples.size / 16000 + 1e-6)

    def test_short_gaps_are_merged_into_one_region(self):
        from app.backend.pipeline import speech_regions

        samples = self._samples([(1.0, 8000), (0.5, 0), (1.0, 8000)])
        regions = speech_regions(samples, 16000, merge_gap_seconds=2.0,
                                 pad_seconds=0.0, min_region_seconds=0.1)
        self.assertEqual(len(regions), 1)


class RegionGroupingTests(unittest.TestCase):
    """Blocos que enchem uma janela do whisper sem esticar o eixo do tempo.

    O whisper processa em janelas de 30 s, então trechos curtos isolados
    desperdiçam janela; mas agrupar trechos distantes amplifica qualquer erro de
    tempo na volta ao eixo original. Os dois tetos existem por isso.
    """

    def test_neighbours_are_packed_together(self):
        from app.backend.pipeline import group_regions

        groups = group_regions([(0, 2), (3, 5), (6, 8)], audible_limit=25, span_limit=75)
        self.assertEqual(len(groups), 1)

    def test_audible_limit_starts_a_new_block(self):
        from app.backend.pipeline import group_regions

        # Dois trechos de 6 s cabem em 15 s; o terceiro passaria de 18 s.
        groups = group_regions([(0, 6), (7, 13), (14, 20)], audible_limit=15, span_limit=999)
        self.assertEqual([len(group) for group in groups], [2, 1])

    def test_distant_regions_never_share_a_block(self):
        """É o teto que impede um erro de 1 s virar 20 s ao voltar ao original."""
        from app.backend.pipeline import group_regions

        groups = group_regions([(0, 2), (500, 502)], audible_limit=25, span_limit=75)
        self.assertEqual(len(groups), 2)

    def test_every_region_survives_the_grouping(self):
        from app.backend.pipeline import group_regions

        regions = [(index * 7.0, index * 7.0 + 3.0) for index in range(20)]
        grouped = [region for group in group_regions(regions) for region in group]
        self.assertEqual(grouped, regions)


class RemapToSourceTests(unittest.TestCase):
    """Voltar os tempos do bloco para o eixo do áudio original.

    É a parte que, errada, corrompe tudo em silêncio: o texto continuaria certo
    e só o tempo estaria fora do lugar, sem nada acusar.
    """

    REGIONS = [(10.0, 12.0), (50.0, 53.0)]

    def _remap(self, start: float, end: float) -> tuple[float, float]:
        from app.backend.pipeline import remap_to_source

        item = remap_to_source([{"start": start, "end": end, "text": "x"}], self.REGIONS)[0]
        return item["start"], item["end"]

    def test_first_region_maps_to_its_own_offset(self):
        self.assertEqual(self._remap(0.0, 1.0), (10.0, 11.0))

    def test_second_region_continues_after_the_first(self):
        # 2 s de áudio no bloco já foram gastos pelo primeiro trecho.
        self.assertEqual(self._remap(2.5, 3.0), (50.5, 51.0))

    def test_time_past_the_end_is_clamped_to_the_last_region(self):
        start, end = self._remap(99.0, 99.0)
        self.assertLessEqual(end, 53.0)
        self.assertGreaterEqual(start, 50.0)

    def test_a_segment_stretched_over_a_cut_keeps_its_order(self):
        """Fim antes do início quebraria a ordenação e a legenda."""
        start, end = self._remap(1.9, 2.2)
        self.assertLessEqual(start, end)

    def test_without_regions_the_times_are_left_alone(self):
        from app.backend.pipeline import remap_to_source

        original = [{"start": 3.0, "end": 4.0, "text": "x"}]
        self.assertEqual(remap_to_source(original, []), original)


class VideoWindowTestEndpointTests(unittest.TestCase):
    """O teste de janela do Lume precisa responder o mesmo que o gravador.

    Se ele dissesse "gravaria" para um vídeo de navegador com o nome do jogo no
    título, o diagnóstico confirmaria justamente o defeito que ele existe para
    encontrar.
    """

    def _test(self, window: str, patterns: list[str], backend_name: str = "linux", **extra) -> dict:
        from app.backend.main import VideoWindowTest, test_video_window

        backend = SimpleNamespace(name=backend_name, active_window=lambda: window, **extra)
        with patch.object(backend_main, "get_backend", return_value=backend):
            return test_video_window(VideoWindowTest(patterns=patterns))

    def test_game_name_in_the_title_would_not_record(self):
        # O último " | " separa: o título do vídeo tem a mesma sequência.
        result = self._test("mrekk | osu! - YouTube | brave-browser", ["osu!"])
        self.assertFalse(result["matched"])
        self.assertEqual(result["title"], "mrekk | osu! - YouTube")
        self.assertEqual(result["window_class"], "brave-browser")
        self.assertTrue(self._test("osu! | osu!", ["osu!"])["matched"])

    def test_prefixes_pick_the_field(self):
        self.assertTrue(self._test("Big Walk | dolphin", ["title:^Big Walk$"])["matched"])
        self.assertFalse(self._test("Big Walk | dolphin", ["class:^Big Walk$"])["matched"])
        # No Linux a classe também atende `exe:`, que é como a regra se escreve
        # no Windows; lá não há classe para consultar.
        self.assertTrue(self._test("Counter-Strike 2 | steam_app_730",
                                   ["exe:^steam_app_[0-9]+$"])["matched"])
        self.assertFalse(self._test("Counter-Strike 2 | cs2.exe",
                                    ["class:cs2"], backend_name="windows")["matched"])


    def test_reports_the_game_monitor_resolution(self):
        """Adicionar um jogo usa a resolução do monitor dele, não 1920x1080 fixo."""
        result = self._test("Jogo | jogo.exe", [], backend_name="windows",
                            active_monitor_resolution=lambda: "1600x900")
        self.assertEqual(result["monitor_resolution"], "1600x900")

    def test_monitor_resolution_failure_does_not_break_the_window_test(self):
        def broken():
            raise OSError("sem monitor")
        result = self._test("Jogo | jogo.exe", [], active_monitor_resolution=broken)
        self.assertIsNone(result["monitor_resolution"])
        self.assertEqual(result["executable"], "jogo.exe")


class VideoSettingsRoundTripTests(unittest.TestCase):
    """Salvar as preferências não pode apagar chaves silenciosamente.

    ``set_video_settings`` reescreve ``video.conf`` inteiro a partir de um
    template fixo, então toda chave nova precisa estar em três lugares — modelo,
    leitura e template. Esquecer o template não quebra nada na hora: a chave
    simplesmente desaparece no primeiro save, e o defeito só aparece depois.
    """

    def test_detected_control_bracket_survives_saving(self):
        saved = self._round_trip("VIDEO_MARKER_HOTKEY='Ctrl+['\nVIDEO_MARKER_KEY_CODE=BracketRight\n")
        self.assertEqual(saved["marker_hotkey"], "Ctrl+[")
        self.assertEqual(saved["marker_key_code"], "BracketRight")

    def _round_trip(self, initial: str) -> dict:
        from fastapi import BackgroundTasks

        from app.backend.main import VideoSettings, get_video_settings, set_video_settings

        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "video.conf"
            apps = Path(directory) / "video-apps.txt"
            config.write_text(initial, encoding="utf-8")
            apps.write_text("# Gerenciado pelo Lume\nexe:^jogo\\.exe$\n", encoding="utf-8")
            shortcut = Path(directory) / "share"
            with patch.object(backend_main, "VIDEO_CONFIG", config), \
                 patch.object(backend_main, "VIDEO_APPS", apps), \
                 patch.dict(os.environ, {"XDG_DATA_HOME": str(shortcut)}, clear=False):
                before = get_video_settings()
                set_video_settings(VideoSettings(**before), BackgroundTasks())
                return get_video_settings()

    def test_cpu_encoder_survives_a_save(self):
        self.assertEqual(self._round_trip("VIDEO_ENCODER=cpu\n")["encoder"], "cpu")

    def test_hud_preferences_survive_a_save(self):
        after = self._round_trip(
            "VIDEO_ENABLED=true\nVIDEO_FPS=60\nVIDEO_GEOMETRY=1920x1080\n"
            "VIDEO_HUD_ENABLED=true\nVIDEO_HUD_PLACEMENT=both\n"
            "VIDEO_HUD_CORNER=bottom-left\nVIDEO_HUD_HOTKEY=Ctrl+F9\n"
            "VIDEO_HUD_SOUND=false\nVIDEO_FOCUS_GRACE_SECONDS=45\n"
        )
        self.assertTrue(after["hud_enabled"])
        self.assertEqual(after["hud_placement"], "both")
        self.assertEqual(after["hud_corner"], "bottom-left")
        self.assertEqual(after["hud_hotkey"], "Ctrl+F9")
        self.assertFalse(after["hud_sound"])
        self.assertEqual(after["focus_grace_seconds"], 45)

    def test_config_without_hud_keys_gets_usable_defaults(self):
        """Uma instalação antiga não pode ficar sem HUD nem quebrar ao salvar."""
        after = self._round_trip("VIDEO_ENABLED=true\nVIDEO_FPS=60\nVIDEO_GEOMETRY=1920x1080\n")
        self.assertTrue(after["hud_enabled"])
        self.assertEqual(after["hud_placement"], "second")
        self.assertEqual(after["hud_hotkey"], "Ctrl+Shift+F8")
        self.assertEqual(after["focus_grace_seconds"], 20)
        self.assertEqual(after["sound_volume"], 100)

    def test_sound_volume_survives_a_save(self):
        self.assertEqual(self._round_trip("VIDEO_SOUND_VOLUME=35\n")["sound_volume"], 35)


class AudioSettingsTests(unittest.TestCase):
    def test_ai_denoise_is_on_by_default_and_survives_a_save(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "audio.conf"
            with patch.object(backend_main, "AUDIO_CONFIG", config), \
                 patch.object(backend_main, "rnnoise_plugin_installed", return_value=True):
                before = backend_main.get_audio_settings()
                self.assertTrue(before.mic_ai_denoise_enabled)
                self.assertEqual(before.mic_vad_threshold, 80)
                self.assertTrue(before.mic_ai_denoise_available)
                changed = before.model_copy(update={"mic_ai_denoise_enabled": False, "mic_vad_threshold": 91})
                backend_main.update_audio_settings(changed, backend_main.BackgroundTasks())
                after = backend_main.get_audio_settings()
            self.assertFalse(after.mic_ai_denoise_enabled)
            self.assertEqual(after.mic_vad_threshold, 91)
            self.assertIn("MIC_AI_DENOISE_ENABLED=false", config.read_text(encoding="utf-8"))


class ConfirmationSoundTests(unittest.TestCase):
    """Sons do atalho: o arquivo enviado substitui o padrão, e remover o devolve."""

    def setUp(self):
        from app.capture import sounds

        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        patcher = patch.object(sounds, "SOUNDS_DIR", Path(self.directory.name) / "sons")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.sounds = sounds

    def _upload(self, slot: str, name: str, data: bytes):
        request = SimpleNamespace(stream=lambda: _chunks(data))
        return asyncio.run(backend_main.upload_confirmation_sound(slot, request, name=name))

    def test_upload_replaces_the_previous_file_and_reset_restores_default(self):
        self._upload("marcador", "plim.wav", b"RIFF1")
        result = self._upload("marcador", "ding.ogg", b"OggS2")
        item = next(item for item in result["items"] if item["slot"] == "marcador")
        self.assertEqual(item, {"slot": "marcador", "label": "Marcador",
                                "custom": True, "name": "marcador.ogg"})
        self.assertEqual(sorted(p.name for p in self.sounds.SOUNDS_DIR.iterdir()), ["marcador.ogg"])

        backend_main.reset_confirmation_sound("marcador")
        self.assertIsNone(self.sounds.custom_sound("marcador"))

    def test_preset_fills_every_slot_with_the_theme_sounds(self):
        result = backend_main.apply_confirmation_sound_preset("minimal")
        self.assertIn("minimal", result["presets"])
        self.assertTrue(all(item["custom"] for item in result["items"]))
        preset = self.sounds.PRESETS_DIR / "minimal"
        self.assertEqual(self.sounds.custom_sound("clipe").read_bytes(),
                         (preset / "toggle-on.ogg").read_bytes())
        self.assertEqual(self.sounds.custom_sound("clipe-estendido").read_bytes(),
                         (preset / "check.ogg").read_bytes())
        self.assertEqual(self.sounds.custom_sound("longa-inicio").read_bytes(),
                         (preset / "double-click.ogg").read_bytes())
        self.assertEqual(self.sounds.custom_sound("longa-fim").read_bytes(),
                         (preset / "deselect.ogg").read_bytes())
        with self.assertRaises(backend_main.HTTPException) as failure:
            backend_main.apply_confirmation_sound_preset("../../etc")
        self.assertEqual(failure.exception.status_code, 404)

    def test_every_preset_has_all_its_sounds(self):
        for theme in self.sounds.presets():
            for name in set(self.sounds.PRESET_SOUNDS.values()):
                self.assertTrue((self.sounds.PRESETS_DIR / theme / f"{name}.ogg").is_file(),
                                f"{theme}/{name}.ogg")

    def test_rejects_unknown_slots_and_formats(self):
        with self.assertRaises(backend_main.HTTPException) as failure:
            self._upload("marcador", "virus.exe", b"MZ")
        self.assertEqual(failure.exception.status_code, 422)
        with self.assertRaises(backend_main.HTTPException) as failure:
            self._upload("../video", "plim.wav", b"RIFF")
        self.assertEqual(failure.exception.status_code, 404)


async def _chunks(data: bytes):
    yield data


class PromptSettingsTests(unittest.TestCase):
    """Os prompts sao editaveis, mas nao a ponto de quebrar a analise."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.config = Path(self.directory.name) / "prompts.json"
        patcher = patch.object(prompts, "PROMPTS_CONFIG", self.config)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_every_prompt_declares_the_variables_that_it_uses(self):
        """Uma variavel esquecida na ficha sumiria do texto sem ninguem notar."""
        for definition in prompts.SPECS:
            used = set(prompts.PLACEHOLDER.findall(definition.template))
            self.assertEqual(used, set(definition.names), definition.key)

    def test_saved_text_replaces_the_default_when_the_prompt_is_rendered(self):
        prompts.save("hourly_summary", "Resuma a hora em uma frase.\n{{contexto}}")
        rendered = prompts.render("hourly_summary", contexto="MEMORIAS")
        self.assertEqual(rendered, "Resuma a hora em uma frase.\nMEMORIAS")

    def test_untouched_prompts_keep_following_the_code(self):
        prompts.save("hourly_summary", "Resuma a hora em uma frase.\n{{contexto}}")
        self.assertEqual(prompts.active_template("daily_summary"), prompts.spec("daily_summary").template)
        self.assertEqual(json.loads(self.config.read_text(encoding="utf-8")).keys(), {"hourly_summary"}.union())

    def test_dropping_a_required_variable_is_refused(self):
        with self.assertRaises(prompts.PromptError) as failure:
            prompts.save("screen_description", "Descreva o print e responda em JSON.")
        self.assertIn("{{janela}}", str(failure.exception))
        self.assertFalse(self.config.exists())

    def test_an_invented_variable_is_refused(self):
        with self.assertRaises(prompts.PromptError) as failure:
            prompts.save("hourly_summary", "{{contexto}} e tambem {{clima}}")
        self.assertIn("{{clima}}", str(failure.exception))

    def test_an_empty_prompt_is_refused(self):
        with self.assertRaises(prompts.PromptError):
            prompts.save("hourly_summary", "   ")

    def test_text_equal_to_the_default_stops_being_stored(self):
        prompts.save("hourly_summary", "Resuma a hora em uma frase.\n{{contexto}}")
        saved = prompts.save("hourly_summary", prompts.spec("hourly_summary").template)
        self.assertFalse(saved["customized"])
        self.assertEqual(json.loads(self.config.read_text(encoding="utf-8")), {})

    def test_reset_brings_the_default_back(self):
        prompts.save("hourly_summary", "Resuma a hora em uma frase.\n{{contexto}}")
        restored = prompts.reset("hourly_summary")
        self.assertFalse(restored["customized"])
        self.assertEqual(restored["text"], prompts.spec("hourly_summary").template)

    def test_a_corrupt_file_falls_back_to_the_defaults(self):
        """Um JSON quebrado nao pode parar a fila inteira."""
        self.config.write_text("{ isto nao e json", encoding="utf-8")
        self.assertEqual(prompts.active_template("hourly_summary"), prompts.spec("hourly_summary").template)

    def test_the_endpoint_reports_the_refusal_as_422(self):
        with self.assertRaises(backend_main.HTTPException) as failure:
            backend_main.set_prompt("screen_description", backend_main.PromptUpdate(text="Descreva o print."))
        self.assertEqual(failure.exception.status_code, 422)


class EditingFolderTests(unittest.TestCase):
    """A pasta de edicao troca garimpo de arquivo por nome legivel e EDL."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.edit = self.root / "edicao"
        self.db_path = self.root / "lume.sqlite3"
        for target, name in ((editing, "EDIT_DIR"), (backend_main, "EDIT_DIR")):
            patcher = patch.object(target, name, self.edit)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(database, "DB_PATH", self.db_path)
        patcher.start()
        self.addCleanup(patcher.stop)
        patcher = patch.object(editing, "probe_fps", lambda path, fallback=30: 60)
        patcher.start()
        self.addCleanup(patcher.stop)
        database.initialize()

    def add_clip(self, name="2026-08-28_17-29-12.mkv", title="Clutch no pós-plant", game="Valorant",
                 chapters="[]", session_id=None, sort_order=0, duration=0.0):
        source = self.root / name
        source.write_bytes(b"video")
        if game:
            source.with_suffix(source.suffix + ".window").write_text(f"{game} | jogo.exe", encoding="utf-8")
        with database.connect() as db:
            cursor = db.execute(
                """INSERT INTO video_segments(source_path,captured_at,status,title,app,chapters_json,
                   session_id,sort_order,duration_seconds) VALUES(?,?,'done',?,'',?,?,?,?)""",
                (str(source), "2026-08-28T17:29:12-03:00", title, chapters, session_id, sort_order, duration),
            )
            return cursor.lastrowid, source

    def add_marker(self, video_id, seconds, title, ai=0):
        with database.connect() as db:
            db.execute(
                "INSERT INTO video_markers(video_id,offset_seconds,title,ai_generated) VALUES(?,?,?,?)",
                (video_id, seconds, title, ai),
            )

    def test_the_name_says_when_what_game_and_what_happened(self):
        name = editing.readable_name("2026-08-28T17:29:12-03:00", "Valorant", "Clutch no pós-plant: 1v3", "x.mkv")
        self.assertEqual(name, "2026-08-28 17-29 Valorant — Clutch no pós-plant 1v3")

    def test_characters_windows_refuses_never_reach_the_filename(self):
        name = editing.readable_name("", "", 'a/b\\c:d*e?f"g<h>i|j', "x.mkv")
        self.assertNotRegex(name, r'[<>:"/\\|?*]')

    def test_a_marker_lands_on_the_frame_its_second_points_to(self):
        """12,5 s a 60 fps sao 750 quadros depois do inicio da timeline."""
        edl = editing.marker_edl("t", [{"seconds": 12.5, "name": "Tiro", "color": editing.COLOR_MANUAL}], 60)
        self.assertIn("01:00:12:30 01:00:12:31", edl)
        self.assertIn("|C:ResolveColorRed |M:Tiro |D:1", edl)

    def test_the_same_second_moves_with_the_timeline_frame_rate(self):
        thirty = editing.marker_edl("t", [{"seconds": 10.0, "name": "x"}], 30)
        sixty = editing.marker_edl("t", [{"seconds": 10.0, "name": "x"}], 60)
        self.assertIn("01:00:10:00", thirty)
        self.assertIn("01:00:10:00", sixty)

    def test_a_timeline_starting_at_zero_is_respected(self):
        edl = editing.marker_edl("t", [{"seconds": 1.0, "name": "x"}], 30, "00:00:00:00")
        self.assertIn("00:00:01:00", edl)

    def test_markers_come_out_in_chronological_order(self):
        edl = editing.marker_edl("t", [{"seconds": 9.0, "name": "depois"}, {"seconds": 1.0, "name": "antes"}], 30)
        self.assertLess(edl.index("antes"), edl.index("depois"))

    def test_a_pipe_in_the_title_cannot_break_the_comment_line(self):
        edl = editing.marker_edl("t", [{"seconds": 1.0, "name": "kill | ace"}], 30)
        self.assertIn("|M:kill / ace |D:1", edl)

    def test_a_broken_timecode_is_refused_with_a_readable_reason(self):
        with self.assertRaises(editing.EditingError):
            editing.marker_edl("t", [{"seconds": 1.0, "name": "x"}], 30, "1:00:00")
        with self.assertRaises(editing.EditingError):
            editing.marker_edl("t", [{"seconds": 1.0, "name": "x"}], 30, "01:00:00:45")

    def test_chapters_are_read_from_seconds_or_from_the_clock(self):
        self.assertEqual(editing.chapter_seconds({"start": 12.5}), 12.5)
        self.assertEqual(editing.chapter_seconds({"time": "01:30"}), 90)
        self.assertEqual(editing.chapter_seconds({"time": "1:00:30"}), 3630)
        self.assertIsNone(editing.chapter_seconds({"time": "abc"}))

    def test_sending_a_video_links_it_and_writes_the_markers_beside_it(self):
        video_id, source = self.add_clip(chapters='[{"start": 30, "title": "Segundo round"}]')
        self.add_marker(video_id, 12.5, "Clutch", ai=1)
        result = editing.send_video(video_id)
        linked = self.edit / result["name"]
        self.assertEqual(result["name"], "2026-08-28 17-29 Valorant — Clutch no pós-plant.mkv")
        self.assertTrue(linked.is_file())
        self.assertEqual(linked.stat().st_ino, source.stat().st_ino)
        self.assertEqual(result["markers"], 2)
        edl = (self.edit / result["edl"]).read_text(encoding="utf-8")
        self.assertIn("|C:ResolveColorYellow |M:Clutch |D:1", edl)
        self.assertIn("|C:ResolveColorBlue |M:Segundo round |D:1", edl)

    def test_sending_a_video_protects_it_from_the_cleanup(self):
        """O hardlink segura os bytes, entao apagar por engano so confundiria."""
        video_id, _source = self.add_clip()
        editing.send_video(video_id)
        with database.connect() as db:
            preserved = db.execute("SELECT preserved FROM video_segments WHERE id=?", (video_id,)).fetchone()
        self.assertEqual(preserved["preserved"], 1)

    def test_sending_the_same_video_twice_does_not_duplicate_it(self):
        video_id, _source = self.add_clip()
        first = editing.send_video(video_id)
        second = editing.send_video(video_id)
        self.assertEqual(first["name"], second["name"])
        self.assertEqual(len(editing.entries()), 1)

    def test_a_video_without_markers_gets_no_edl(self):
        video_id, _source = self.add_clip()
        result = editing.send_video(video_id)
        self.assertEqual(result["edl"], "")
        self.assertFalse(any(item.suffix == ".edl" for item in self.edit.iterdir()))

    def test_a_session_stacks_the_clips_along_one_timeline(self):
        """O segundo trecho comeca onde o primeiro acaba, e o EDL acompanha."""
        with database.connect() as db:
            session_id = db.execute(
                "INSERT INTO video_sessions(name,status) VALUES('Ranked de terça','done')"
            ).lastrowid
        first, _ = self.add_clip("a.mkv", "Primeiro", session_id=session_id, sort_order=0, duration=60.0)
        second, _ = self.add_clip("b.mkv", "Segundo", session_id=session_id, sort_order=1, duration=30.0)
        self.add_marker(first, 10.0, "No primeiro")
        self.add_marker(second, 5.0, "No segundo")
        result = editing.send_session(session_id)
        self.assertEqual(result["clips"], 2)
        self.assertEqual(result["markers"], 2)
        edl = (self.edit / result["edl"]).read_text(encoding="utf-8")
        self.assertIn("01:00:10:00", edl)
        self.assertIn("01:01:05:00", edl)
        self.assertEqual(len([item for item in self.edit.iterdir() if item.suffix == ".mkv"]), 2)

    def test_removing_takes_the_shortcut_and_keeps_the_original(self):
        video_id, source = self.add_clip()
        self.add_marker(video_id, 1.0, "x")
        result = editing.send_video(video_id)
        editing.remove(result["name"])
        self.assertFalse((self.edit / result["name"]).exists())
        self.assertFalse((self.edit / result["edl"]).exists())
        self.assertTrue(source.is_file())

    def test_removing_a_session_clip_keeps_the_edl_while_others_remain(self):
        with database.connect() as db:
            session_id = db.execute("INSERT INTO video_sessions(name,status) VALUES('S','done')").lastrowid
        first, _ = self.add_clip("a.mkv", "Primeiro", session_id=session_id, sort_order=0, duration=10.0)
        self.add_clip("b.mkv", "Segundo", session_id=session_id, sort_order=1, duration=10.0)
        self.add_marker(first, 1.0, "x")
        result = editing.send_session(session_id)
        names = [item["name"] for item in editing.entries()]
        editing.remove(names[0])
        self.assertTrue((self.edit / result["edl"]).is_file())

    def test_a_path_outside_the_folder_is_refused(self):
        with self.assertRaises(editing.EditingError):
            editing.remove("../lume.sqlite3")

    def test_a_missing_original_is_reported_not_crashed(self):
        video_id, source = self.add_clip()
        source.unlink()
        with self.assertRaises(editing.EditingError):
            editing.send_video(video_id)


class CallMetricsTests(unittest.TestCase):
    """Sem separar carga, leitura do prompt e geracao, encurtar prompt e chute."""

    def setUp(self):
        pipeline.clear_call_metrics()
        self.addCleanup(pipeline.clear_call_metrics)

    def sample(self, **overrides):
        payload = {
            "prompt_eval_count": 900, "eval_count": 120,
            "load_duration": 0, "prompt_eval_duration": 40_000_000_000,
            "eval_duration": 9_000_000_000, "total_duration": 49_000_000_000,
        }
        payload.update(overrides)
        return payload

    def test_nanoseconds_from_ollama_become_milliseconds(self):
        pipeline._record_call_metrics("qwen", self.sample())
        metrics = pipeline.last_call_metrics()
        self.assertEqual(metrics["prompt_ms"], 40000)
        self.assertEqual(metrics["eval_ms"], 9000)
        self.assertEqual(metrics["total_ms"], 49000)
        self.assertEqual(metrics["calls"], 1)

    def test_a_repair_call_is_added_not_forgotten(self):
        """ollama_json repete a chamada para consertar JSON; isso custa tempo."""
        pipeline._record_call_metrics("qwen", self.sample())
        pipeline._record_call_metrics("qwen", self.sample(
            prompt_eval_count=200, eval_count=40, prompt_eval_duration=3_000_000_000,
            eval_duration=2_000_000_000, total_duration=5_000_000_000))
        metrics = pipeline.last_call_metrics()
        self.assertEqual(metrics["calls"], 2)
        self.assertEqual(metrics["prompt_tokens"], 1100)
        self.assertEqual(metrics["prompt_ms"], 43000)
        self.assertEqual(metrics["total_ms"], 54000)

    def test_clearing_stops_one_analysis_from_inheriting_the_previous(self):
        """Um audio nao passa pelo Ollama; herdar a medicao de uma tela mentiria."""
        pipeline._record_call_metrics("qwen", self.sample())
        pipeline.clear_call_metrics()
        self.assertEqual(pipeline.last_call_metrics(), {})

    def test_a_screen_capture_keeps_its_measurement_in_the_row(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "lume.sqlite3"
            image = root / "2026-08-28_17-29-12_mon0_display0.png"
            image.write_bytes(b"png")

            def fake_describe(path):
                pipeline._record_call_metrics("qwen3-vl", self.sample())
                return {"title": "Tela", "text": "descricao", "app": "App", "tags": [], "duration": None}

            with patch.object(database, "DB_PATH", db_path), \
                 patch.object(pipeline, "describe_screen", fake_describe), \
                 patch.object(pipeline, "sha256", lambda value: "abc"):
                result = pipeline.process_specific(image)
                with database.connect() as db:
                    row = db.execute(
                        "SELECT process_ms,ai_metrics_json FROM captures WHERE id=?", (result["id"],)
                    ).fetchone()
            metrics = json.loads(row["ai_metrics_json"])
            self.assertEqual(metrics["prompt_ms"], 40000)
            self.assertEqual(metrics["eval_ms"], 9000)
            self.assertEqual(metrics["generated_tokens"], 120)
            self.assertIsNotNone(row["process_ms"])


if __name__ == "__main__":
    unittest.main()


class TagVocabularyTests(unittest.TestCase):
    """O vocabulário de tags: normalização, quarentena, fusão e promoção."""

    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        patcher = patch.object(database, "DB_PATH", Path(self._directory.name) / "lume.sqlite3")
        patcher.start()
        self.addCleanup(patcher.stop)
        database.initialize()

    @staticmethod
    def _laya(answers):
        """Substitui o daemon: devolve uma escolha por estado, na ordem pedida."""
        def choose(states, instructions, criteria):
            return [tag_vocabulary.laya.Choice(*answers[index]) for index in range(len(states))]
        return choose

    def test_slug_ignores_case_accent_and_punctuation(self):
        self.assertEqual(tag_vocabulary.slugify("  Sea of Thieves!! "), "sea-of-thieves")
        self.assertEqual(tag_vocabulary.slugify("Programação"), "programacao")
        self.assertEqual(tag_vocabulary.slugify("ação/aventura"), "acao-aventura")

    def test_known_tag_and_alias_do_not_reach_the_model(self):
        tag_vocabulary.create("culinária", "receita, comida, cozinha")
        with connect() as db:
            db.execute("INSERT INTO tag_aliases(alias,slug) VALUES('cozinhar','culinaria')")
        with patch.object(tag_vocabulary.laya, "choose", side_effect=AssertionError("não deveria perguntar")):
            resolution = tag_vocabulary.canonicalize(["CULINÁRIA", "cozinhar"], day="2026-09-24")
        self.assertEqual([item.outcome for item in resolution.decisions], ["known", "alias"])
        self.assertEqual(resolution.tags, ["culinária", "culinária"])

    def test_confident_synonym_becomes_an_alias_and_a_weak_one_waits(self):
        tag_vocabulary.create("culinária", "receita, comida, cozinha")
        with patch.object(tag_vocabulary.laya, "choose", self._laya([("culinaria", 0.95)])):
            resolution = tag_vocabulary.canonicalize(["receita de pão"], day="2026-09-24")
        self.assertEqual(resolution.decisions[0].outcome, "merged")
        self.assertEqual(resolution.tags, ["culinária"])
        with connect() as db:
            self.assertEqual(db.execute("SELECT slug FROM tag_aliases WHERE alias='receita-de-pao'").fetchone()["slug"], "culinaria")

        with patch.object(tag_vocabulary.laya, "choose", self._laya([("culinaria", 0.4)])):
            weak = tag_vocabulary.canonicalize(["finanças"], day="2026-09-24")
        self.assertEqual(weak.decisions[0].outcome, "proposed")
        with connect() as db:
            self.assertEqual(db.execute("SELECT status FROM tags WHERE slug='financas'").fetchone()["status"], "candidate")

    def test_a_proposal_is_still_written_to_the_capture(self):
        """A quarentena governa o vocabulário, não a memória: nada se perde."""
        with patch.object(tag_vocabulary.laya, "choose", side_effect=tag_vocabulary.laya.LayaUnavailable("daemon fora")):
            resolution = tag_vocabulary.canonicalize(["assunto novo"], day="2026-09-24")
        self.assertEqual(resolution.tags, ["assunto novo"])
        self.assertTrue(resolution.decisions[0].applied)

    def test_the_daemon_being_down_never_breaks_an_analysis(self):
        tag_vocabulary.create("culinária", "receita, comida, cozinha")
        with patch.object(tag_vocabulary.laya, "choose", side_effect=tag_vocabulary.laya.LayaUnavailable("daemon fora")):
            resolution = tag_vocabulary.canonicalize(["receita de pão"], day="2026-09-24")
        self.assertIn("daemon fora", resolution.laya_error)
        self.assertEqual(resolution.decisions[0].outcome, "proposed")

    def test_recurrence_holds_a_candidate_until_it_returns_on_another_day(self):
        with patch.object(tag_vocabulary.laya, "choose", side_effect=tag_vocabulary.laya.LayaUnavailable("sem daemon")):
            tag_vocabulary.canonicalize(["finanças"], day="2026-09-24")
            report = tag_vocabulary.promote("2026-09-24")
            self.assertEqual(report["promoted"], [])
            self.assertEqual(report["waiting"][0]["slug"], "financas")

            tag_vocabulary.canonicalize(["finanças"], day="2026-09-25")
            tag_vocabulary.canonicalize(["finanças"], day="2026-09-26")
            report = tag_vocabulary.promote("2026-09-26")
        self.assertEqual([item["slug"] for item in report["promoted"]], ["financas"])
        with connect() as db:
            self.assertEqual(db.execute("SELECT status FROM tags WHERE slug='financas'").fetchone()["status"], "active")

    def test_a_dry_run_reports_without_writing(self):
        with patch.object(tag_vocabulary.laya, "choose", side_effect=tag_vocabulary.laya.LayaUnavailable("sem daemon")):
            for day in ("2026-09-24", "2026-09-25", "2026-09-26"):
                tag_vocabulary.canonicalize(["finanças"], day=day)
            report = tag_vocabulary.promote("2026-09-26", commit=False)
        self.assertEqual([item["slug"] for item in report["promoted"]], ["financas"])
        with connect() as db:
            self.assertEqual(db.execute("SELECT status FROM tags WHERE slug='financas'").fetchone()["status"], "candidate")

    def test_promotion_merges_a_candidate_that_the_vocabulary_grew_to_cover(self):
        tag_vocabulary.create("culinária", "receita, comida, cozinha")
        with patch.object(tag_vocabulary.laya, "choose", side_effect=tag_vocabulary.laya.LayaUnavailable("sem daemon")):
            for day in ("2026-09-24", "2026-09-25", "2026-09-26"):
                tag_vocabulary.canonicalize(["receita de pão"], day=day)
        with patch.object(tag_vocabulary.laya, "choose", self._laya([("culinaria", 0.92)])):
            report = tag_vocabulary.promote("2026-09-26")
        self.assertEqual(report["promoted"], [])
        self.assertEqual(report["merged"][0]["into"], "culinaria")
        with connect() as db:
            self.assertIsNone(db.execute("SELECT 1 FROM tags WHERE slug='receita-de-pao'").fetchone())
            self.assertEqual(db.execute("SELECT slug FROM tag_aliases WHERE alias='receita-de-pao'").fetchone()["slug"], "culinaria")

    def test_a_rejected_tag_is_never_applied_again(self):
        tag_vocabulary.create("culinária", "receita, comida, cozinha")
        tag_vocabulary.set_status("culinaria", "rejected")
        with patch.object(tag_vocabulary.laya, "choose", side_effect=AssertionError("não deveria perguntar")):
            resolution = tag_vocabulary.canonicalize(["culinária"], day="2026-09-24")
        self.assertEqual(resolution.tags, [])
        self.assertEqual(resolution.decisions[0].outcome, "discarded")

    def test_manual_merge_carries_the_aliases_of_the_absorbed_tag(self):
        tag_vocabulary.create("culinária", "receita, comida")
        tag_vocabulary.create("comida", "prato, refeição")
        with connect() as db:
            db.execute("INSERT INTO tag_aliases(alias,slug) VALUES('rango','comida')")
        tag_vocabulary.merge("comida", "culinaria")
        with connect() as db:
            self.assertIsNone(db.execute("SELECT 1 FROM tags WHERE slug='comida'").fetchone())
            aliases = {row["alias"]: row["slug"] for row in db.execute("SELECT alias,slug FROM tag_aliases")}
        self.assertEqual(aliases, {"rango": "culinaria", "comida": "culinaria"})

    def test_the_cap_retires_the_least_used_tags_proposed_by_the_model(self):
        with connect() as db:
            for index in range(4):
                db.execute(
                    """INSERT INTO tags(slug,label,criterion,status,origin,uses,last_used)
                       VALUES(?,?,'x','active','model',?,'2026-09-24 10:00:00')""",
                    (f"tag-{index}", f"tag {index}", index),
                )
        with patch.object(tag_vocabulary, "MAX_ACTIVE", 2):
            report = {"retired": []}
            with connect() as db:
                tag_vocabulary._enforce_cap(db, report)
        self.assertEqual([item["slug"] for item in report["retired"]], ["tag-0", "tag-1"])
        with connect() as db:
            dormant = {row["slug"] for row in db.execute("SELECT slug FROM tags WHERE status='dormant'")}
        self.assertEqual(dormant, {"tag-0", "tag-1"})

    def test_a_user_tag_survives_the_cap(self):
        with connect() as db:
            db.execute("""INSERT INTO tags(slug,label,criterion,status,origin,uses)
                          VALUES('minha','minha','x','active','user',0)""")
            db.execute("""INSERT INTO tags(slug,label,criterion,status,origin,uses)
                          VALUES('dela','dela','x','active','model',9)""")
        with patch.object(tag_vocabulary, "MAX_ACTIVE", 1):
            report = {"retired": []}
            with connect() as db:
                tag_vocabulary._enforce_cap(db, report)
        self.assertEqual([item["slug"] for item in report["retired"]], ["dela"])


class MediaFreshnessTests(unittest.TestCase):
    """As URLs de mídia têm de mudar quando o arquivo muda.

    O corte reescreve o vídeo no lugar e mantém o caminho. Com a URL igual, o
    navegador reaproveita o que guardou: as faixas do mixer vêm com
    ``max-age=86400``, então o áudio de 61s continuava tocando por cima do
    vídeo de 9s recém-cortado — "o áudio ficou errado".
    """

    def test_a_url_da_midia_muda_quando_o_arquivo_muda(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "clipe.mp4"
            path.write_bytes(b"antes")
            antes = [backend_main.media_url("media:video-buffer/clipe.mp4", path),
                     backend_main.media_url("media:video-buffer/clipe.mp4", path, "video-thumbnail"),
                     backend_main.media_url("media:video-buffer/clipe.mp4", path, "video-audio-track", track=1)]
            path.write_bytes(b"depois do corte")
            os.utime(path, (1, 1))
            depois = [backend_main.media_url("media:video-buffer/clipe.mp4", path),
                      backend_main.media_url("media:video-buffer/clipe.mp4", path, "video-thumbnail"),
                      backend_main.media_url("media:video-buffer/clipe.mp4", path, "video-audio-track", track=1)]
        for primeiro, segundo in zip(antes, depois):
            self.assertNotEqual(primeiro, segundo, f"{primeiro} não mudou com o arquivo")
        self.assertIn("track=1", depois[2])
        # O caminho vai inteiro dentro do parâmetro, barras incluídas.
        self.assertIn("path=media%3Avideo-buffer%2Fclipe.mp4", depois[0])

    def test_arquivo_ausente_nao_derruba_a_url(self):
        """Um clipe apagado entre a listagem e a montagem da URL não é erro 500."""
        url = backend_main.media_url("media:video-buffer/sumiu.mp4", Path("/nao/existe.mp4"))
        self.assertIn("v=0", url)


class SharingTests(unittest.TestCase):
    """Achar o clipe e mandar para alguém.

    O gravador nomeia por data, então o que chega ao Discord precisa ganhar um
    nome legível na saída — e caber no limite de anexo sem levar as quatro
    faixas de áudio da gravação.
    """

    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        root = Path(self._temporary.name)
        self.buffer = root / "video-buffer"
        self.buffer.mkdir()
        self.cache = root / "video-share"
        # A raiz de mídia inteira vai para o temporário: sem isto, `media:` se
        # resolve na pasta real da máquina e o teste lê o sidecar de um clipe de
        # verdade — passando por motivo errado.
        self._patches = [
            patch.object(database, "DB_PATH", root / "lume.sqlite3"),
            patch.object(main_paths, "MEDIA_ROOT", root),
            patch.object(sharing, "SHARE_CACHE_DIR", self.cache),
        ]
        for item in self._patches:
            item.start()
        database.initialize()
        self.addCleanup(self._temporary.cleanup)
        self.addCleanup(lambda: [item.stop() for item in self._patches])

    def _clip(self, name="2026-09-26_00-10-34_DP-1.mp4", window="Sea of Thieves | steam_app_1172620",
              **columns):
        """Um clipe no disco com o sidecar do gravador e a linha do banco."""
        path = self.buffer / name
        path.write_bytes(b"0" * columns.pop("bytes", 1024))
        if window:
            path.with_suffix(path.suffix + ".window").write_text(window, encoding="utf-8")
        key = f"media:video-buffer/{name}"
        values = {"captured_at": "2026-09-26T00:10:34", "app": "", "title": "",
                  "status": "pending", "session_id": None, "sort_order": 0}
        values.update(columns)
        with connect() as db:
            db.execute(
                """INSERT INTO video_segments(source_path,captured_at,app,title,status,session_id,sort_order)
                   VALUES(?,?,?,?,?,?,?)""",
                (key, values["captured_at"], values["app"], values["title"],
                 values["status"], values["session_id"], values["sort_order"]),
            )
        return key, path

    # --- nome legível ------------------------------------------------------

    def test_nome_do_download_usa_o_jogo_do_sidecar_quando_a_ia_ainda_nao_titulou(self):
        """O clipe que acabou de sair é justamente o que a pessoa quer mandar.

        Ele entra no banco como ``pending``, sem ``app`` e sem ``title``: se o
        nome dependesse da análise, o anexo sairia como
        ``2026-09-26_00-10-34_DP-1.mp4`` — o amontoado de novo.
        """
        key, path = self._clip()
        name = sharing.download_filename(key, path)
        self.assertEqual(name, "2026-09-26 00-10 Sea of Thieves.mp4")

    def test_nome_do_download_usa_o_titulo_da_ia_quando_existe(self):
        key, path = self._clip(title="kraken no crepúsculo", status="done")
        name = sharing.download_filename(key, path)
        self.assertEqual(name, "2026-09-26 00-10 Sea of Thieves — kraken no crepúsculo.mp4")

    def test_nome_de_trecho_de_sessao_diz_qual_pedaco_e(self):
        """Cinco clipes da mesma partida não podem virar cinco anexos iguais."""
        with connect() as db:
            db.execute("INSERT INTO video_sessions(id,name) VALUES(7,'Sea of Thieves')")
        first_key, first = self._clip("2026-09-26_00-05-00_DP-1.mp4", session_id=7, sort_order=1,
                                      captured_at="2026-09-26T00:05:00")
        second_key, second = self._clip("2026-09-26_00-10-34_DP-1.mp4", session_id=7, sort_order=2)
        name = sharing.download_filename(second_key, second)
        self.assertEqual(name, "2026-09-26 00-10 Sea of Thieves — trecho 02 de 02.mp4")

    def test_sessao_com_um_clipe_so_nao_ganha_numeracao(self):
        with connect() as db:
            db.execute("INSERT INTO video_sessions(id,name) VALUES(8,'Sea of Thieves')")
        key, path = self._clip(session_id=8, sort_order=1)
        self.assertEqual(sharing.download_filename(key, path),
                         "2026-09-26 00-10 Sea of Thieves.mp4")

    def test_nome_da_sessao_igual_ao_jogo_nao_entra_duas_vezes(self):
        """A sessão automática se chama como a janela; repetir daria
        "Sea of Thieves — Sea of Thieves"."""
        with connect() as db:
            db.execute("INSERT INTO video_sessions(id,name) VALUES(9,'Sea of Thieves')")
        self._clip("2026-09-26_00-05-00_DP-1.mp4", session_id=9, sort_order=1,
                   captured_at="2026-09-26T00:05:00")
        key, path = self._clip(session_id=9, sort_order=2)
        self.assertNotIn("Sea of Thieves — Sea of Thieves",
                         sharing.download_filename(key, path))

    def test_clipe_sem_jogo_e_sem_titulo_mantem_o_nome_do_arquivo(self):
        """Sem sidecar e sem análise, um carimbo de data sozinho não identifica nada."""
        key, path = self._clip("2026-09-26_00-10-34_DP-1.mp4", window="")
        self.assertIn("2026-09-26_00-10-34_DP-1", sharing.download_filename(key, path))

    def test_nome_da_versao_leve_diz_o_teto(self):
        """Duas versões do mesmo clipe na pasta de downloads precisam se distinguir."""
        key, path = self._clip()
        self.assertEqual(sharing.light_filename(key, path, 20),
                         "2026-09-26 00-10 Sea of Thieves (20 MB).mp4")

    # --- plano da versão leve ---------------------------------------------

    def test_bitrate_alvo_reserva_margem_e_desconta_o_audio(self):
        plan = sharing.share_plan(20, 60.0, 1080, 60)
        budget = 20 * 1024 * 1024 * 8 * sharing.SAFETY / 60.0
        self.assertEqual(plan.video_bitrate, int(budget - plan.audio_bitrate))
        self.assertLess(plan.estimated_bytes, plan.limit_bytes)

    def test_clipe_de_um_minuto_em_dez_megas_cai_para_720p30(self):
        plan = sharing.share_plan(10, 60.0, 1080, 60)
        self.assertEqual((plan.height, plan.fps), (720, 30))

    def test_o_teto_do_discord_preserva_os_sessenta_quadros(self):
        """Numa jogada a fluidez lê melhor que a nitidez: 720p60, não 1080p30."""
        plan = sharing.share_plan(20, 60.0, 1080, 60)
        self.assertEqual((plan.height, plan.fps), (720, 60))

    def test_plano_nunca_aumenta_resolucao_nem_fps_do_original(self):
        plan = sharing.share_plan(500, 60.0, 720, 30)
        self.assertEqual((plan.height, plan.fps), (720, 30))
        self.assertFalse(plan.scale)
        self.assertFalse(plan.resample)

    def test_teto_folgado_nao_infla_o_bitrate_acima_do_original(self):
        """Pedir 63 Mbps de um vídeo gravado a 2,3 gastaria CPU para nada."""
        plan = sharing.share_plan(500, 60.0, 1080, 60, source_bitrate=2_300_000)
        self.assertLessEqual(plan.video_bitrate, 2_300_000)
        self.assertEqual((plan.height, plan.fps), (1080, 60))

    def test_video_longo_demais_para_o_teto_recusa_antes_de_gastar_cpu(self):
        with self.assertRaises(sharing.SharingError) as erro:
            sharing.share_plan(20, 3600.0, 1080, 60)
        self.assertIn("20 MB", str(erro.exception))

    def test_versao_leve_mantem_somente_a_faixa_de_mixagem(self):
        """O arquivo tem quatro faixas: mixagem, microfone, Discord e sistema.

        Levar as quatro estoura o teto e publica o microfone da pessoa numa
        faixa separada, para qualquer um baixar e isolar.
        """
        plan = sharing.share_plan(20, 60.0, 1080, 60)
        command = sharing.light_video_command(Path("a.mp4"), Path("b.mp4"), plan)
        self.assertIn("0:a:0", command)
        self.assertNotIn("0:a?", command)
        self.assertEqual(command.count("-map"), 2, "uma faixa de vídeo e uma de áudio, nada mais")

    def test_comando_leve_sempre_gera_mp4_com_faststart_e_yuv420p(self):
        plan = sharing.share_plan(20, 60.0, 1080, 60)
        command = sharing.light_video_command(Path("a.mkv"), Path("b.mp4"), plan)
        self.assertIn("+faststart", command)
        self.assertIn("yuv420p", command)
        self.assertEqual(command[-1], "b.mp4")

    def test_comando_leve_nao_reescala_o_que_ja_esta_no_tamanho(self):
        plan = sharing.share_plan(50, 60.0, 720, 30)
        self.assertNotIn("-vf", sharing.light_video_command(Path("a.mp4"), Path("b.mp4"), plan))

    def test_progresso_vem_do_out_time_do_ffmpeg(self):
        self.assertEqual(sharing.progress_percent("out_time_us=30000000", 60.0), 50)
        self.assertIsNone(sharing.progress_percent("frame=120", 60.0))
        # 100% só depois do arquivo trocado de lugar: antes disso não está pronto.
        self.assertEqual(sharing.progress_percent("out_time_us=60000000", 60.0), 99)

    # --- cache -------------------------------------------------------------

    def test_versao_leve_mais_antiga_que_o_original_e_descartada(self):
        """O corte reescreve o arquivo no lugar e mantém o nome: sem comparar a
        data, a pessoa baixaria o trecho que ela acabou de cortar fora."""
        _key, path = self._clip()
        self.cache.mkdir(parents=True)
        destination = sharing.share_cache_path(path, 20)
        destination.write_bytes(b"antigo")
        os.utime(destination, (0, 0))
        self.assertIsNone(sharing.share_cached(path, 20))
        os.utime(destination, None)
        self.assertEqual(sharing.share_cached(path, 20), destination)

    def test_limpeza_de_caches_do_video_remove_tambem_as_versoes_leves(self):
        _key, path = self._clip()
        self.cache.mkdir(parents=True)
        leves = [sharing.share_cache_path(path, limit) for limit in (10, 20)]
        for item in leves:
            item.write_bytes(b"x")
        with patch.object(backend_main, "VIDEO_THUMBNAIL_DIR", self.cache / "thumbs"), \
             patch.object(backend_main, "VIDEO_AUDIO_TRACK_DIR", self.cache / "tracks"):
            backend_main.delete_video_caches(path)
        self.assertEqual([item for item in leves if item.exists()], [])

    def test_o_original_que_ja_cabe_nao_e_recodificado(self):
        """Recodificar um arquivo que já cabe só pioraria a imagem."""
        key, path = self._clip(bytes=2048)
        with patch.object(sharing, "video_shape") as shape:
            state = sharing.light_state(key, path, 20, start=True)
        self.assertEqual(state["status"], "fits")
        shape.assert_not_called()

    def test_consultar_o_estado_nunca_liga_o_ventilador(self):
        """``GET`` que dispara meio minuto de ffmpeg viraria timeout no navegador."""
        key, path = self._clip(bytes=32 * 1024 * 1024)
        shape = sharing.VideoShape(duration=60.0, height=1080, fps=60.0, bitrate=4_000_000)
        with patch.object(sharing, "video_shape", return_value=shape), \
             patch.object(sharing._LightVersionJob, "start") as start:
            state = sharing.light_state(key, path, 20)
            self.assertEqual(state["status"], "absent")
            start.assert_not_called()
            self.assertEqual(sharing.light_state(key, path, 20, start=True)["status"], "preparing")
            start.assert_called_once()

    # --- upload ------------------------------------------------------------

    def test_corpo_multipart_declara_content_length_exato(self):
        """Sem o tamanho, o urllib manda ``chunked`` e o catbox recusa o envio."""
        _key, path = self._clip(bytes=4096)
        body = sharing.MultipartBody({"reqtype": "fileupload", "time": "72h"},
                                     "fileToUpload", path, "clipe.mp4")
        drained = b""
        while True:
            chunk = body.read(1024)
            if not chunk:
                break
            drained += chunk
        self.assertEqual(body.length, len(drained))
        self.assertIn(b'name="time"', drained)
        self.assertIn(b'filename="clipe.mp4"', drained)

    def test_corpo_multipart_nao_le_o_arquivo_inteiro_na_memoria(self):
        _key, path = self._clip(bytes=1024 * 1024)
        body = sharing.MultipartBody({}, "fileToUpload", path, "clipe.mp4", block=8192)
        maior = max(len(body.read(1 << 30)) for _ in range(20))
        self.assertLessEqual(maior, 8192)

    def test_upload_manda_reqtype_e_tempo_esperados_pelo_litterbox(self):
        _key, path = self._clip(bytes=2048)
        enviado = {}

        def fake_urlopen(request, timeout=0):
            enviado["headers"] = dict(request.headers)
            enviado["url"] = request.full_url
            enviado["corpo"] = b"".join(iter(lambda: request.data.read(4096), b""))
            return _FakeResponse(b"https://litter.catbox.moe/abc123.mp4\n")

        with patch.object(sharing.urllib.request, "urlopen", fake_urlopen):
            url = sharing.upload_file(path, "clipe.mp4", sharing.HOSTS["litterbox"], "72h")
        self.assertEqual(url, "https://litter.catbox.moe/abc123.mp4")
        self.assertIn("litterbox.catbox.moe", enviado["url"])
        self.assertIn(b'name="reqtype"', enviado["corpo"])
        self.assertIn(b"fileupload", enviado["corpo"])
        self.assertIn(b"72h", enviado["corpo"])
        self.assertEqual(enviado["headers"]["Content-length"], str(len(enviado["corpo"])))
        self.assertIn("Lume", enviado["headers"]["User-agent"])

    def test_resposta_que_nao_e_url_vira_erro_legivel(self):
        """O host recusa com HTTP 200 e um texto no corpo; engolir isso deixaria
        a pessoa olhando um link vazio sem saber por quê."""
        _key, path = self._clip(bytes=2048)
        with patch.object(sharing.urllib.request, "urlopen",
                          lambda *a, **k: _FakeResponse(b"File too large")):
            with self.assertRaises(sharing.SharingError) as erro:
                sharing.upload_file(path, "clipe.mp4", sharing.HOSTS["litterbox"])
        self.assertIn("File too large", str(erro.exception))

    def test_arquivo_maior_que_o_limite_do_host_falha_antes_de_abrir_socket(self):
        _key, path = self._clip(bytes=4096)
        apertado = dataclasses.replace(sharing.HOSTS["catbox"], max_bytes=1024)
        with patch.object(sharing.urllib.request, "urlopen") as urlopen:
            with self.assertRaises(sharing.SharingError) as erro:
                sharing.upload_file(path, "clipe.mp4", apertado)
        urlopen.assert_not_called()
        self.assertIn("aceita até", str(erro.exception))

    def test_cancelar_o_upload_interrompe_a_leitura_do_arquivo(self):
        _key, path = self._clip(bytes=64 * 1024)
        body = sharing.MultipartBody({}, "fileToUpload", path, "clipe.mp4",
                                     should_stop=lambda: True)
        with self.assertRaises(sharing.SharingCancelled):
            body.read(1024)

    def test_upload_sem_confirmacao_explicita_e_recusado(self):
        """A trava mora no servidor: publicar não pode ser efeito colateral de
        uma chamada de API, nem de um campo que já vem marcado."""
        key, path = self._clip(bytes=2048)
        with self.assertRaises(sharing.SharingError) as erro:
            sharing.start_upload(key, path, use_light=False, confirmed=False)
        self.assertIn("Confirme", str(erro.exception))

    def test_link_publico_exige_a_versao_leve_pronta_quando_pedida(self):
        key, path = self._clip(bytes=2048)
        with self.assertRaises(sharing.SharingError) as erro:
            sharing.start_upload(key, path, use_light=True, limit_mb=20, confirmed=True)
        self.assertIn("versão leve", str(erro.exception))

    def test_link_fica_salvo_para_recopiar_depois(self):
        """O mesmo clipe pode ir duas vezes, e o link expira: é lista, não campo."""
        key, path = self._clip()
        sharing.remember_link(key, sharing.HOSTS["litterbox"],
                              "https://litter.catbox.moe/a.mp4", 1024, True, 20, "72h")
        sharing.remember_link(key, sharing.HOSTS["catbox"],
                              "https://files.catbox.moe/b.mp4", 2048, False, 0, "")
        links = sharing.links_for(key)
        self.assertEqual({item["host"] for item in links}, {"litterbox", "catbox"})
        temporario = next(item for item in links if item["host"] == "litterbox")
        permanente = next(item for item in links if item["host"] == "catbox")
        self.assertTrue(temporario["expires_at"])
        self.assertFalse(temporario["expired"])
        self.assertIsNone(permanente["expires_at"])
        self.assertTrue(sharing.forget_link(temporario["id"]))
        self.assertEqual(len(sharing.links_for(key)), 1)

    def test_o_host_permanente_nunca_e_o_padrao(self):
        """"Para sempre" é decisão de quem publica, não do código."""
        self.assertFalse(sharing.resolve_host(None).permanent)
        self.assertEqual(sharing.DEFAULT_HOST, "litterbox")

    def test_nenhum_outro_modulo_chama_o_upload(self):
        """Mandar arquivo para fora só acontece pelo caminho que pede confirmação."""
        raiz = Path(__file__).resolve().parent
        for nome in ("main.py", "pipeline.py", "editing.py", "retention.py"):
            fonte = (raiz / nome).read_text(encoding="utf-8")
            self.assertNotIn("upload_file", fonte, f"{nome} chama o upload direto")
        fonte = (raiz / "sharing.py").read_text(encoding="utf-8")
        chamadas = [linha for linha in fonte.splitlines()
                    if "upload_file(" in linha and not linha.lstrip().startswith("def ")]
        self.assertEqual(len(chamadas), 1, f"upload_file chamado em mais de um lugar: {chamadas}")


class _FakeResponse:
    """Resposta de host de arquivo: corpo em texto puro, sem rede envolvida."""

    def __init__(self, body: bytes, status: int = 200) -> None:
        self._body = body
        self.status = status

    def read(self, size: int = -1) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *_exception) -> bool:
        return False


class ModoLuminiTests(unittest.TestCase):
    """O Lumini é a mesma base instalada só como gravador.

    Sem estes testes, a instalação dos amigos apodrece em silêncio: um `import
    numpy` novo no topo de um módulo, ou uma rota de análise sem classificação,
    só aparecem na máquina de quem não tem o pipeline.
    """

    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.config = Path(self._temporary.name) / "lume.conf"
        patches = [
            patch.object(mode, "MODE_CONFIG", self.config),
            patch.dict(os.environ, {}, clear=False),
        ]
        for item in patches:
            item.start()
        os.environ.pop("LUME_MODE", None)
        self.addCleanup(self._temporary.cleanup)
        self.addCleanup(lambda: [item.stop() for item in patches])

    def test_modo_padrao_e_completo_quando_nada_declara(self):
        """Atualizar o Lume não pode desligar a análise de quem a tem."""
        self.assertEqual(mode.modo_atual(), "completo")
        self.assertFalse(mode.e_lumini())

    def test_arquivo_de_configuracao_declara_o_modo(self):
        """O modo precisa valer para todo processo da máquina.

        São quatro que precisam concordar — a interface, a HUD, o daemon do
        atalho e o duplo clique no lançador. Variável de ambiente numa unit
        cobriria a unit e mentiria para os outros três.
        """
        self.config.write_text("LUME_MODE=lumini\n", encoding="utf-8")
        self.assertTrue(mode.e_lumini())

    def test_variavel_de_ambiente_vence_o_arquivo(self):
        """Experimentar o Lumini não pode exigir editar a instalação."""
        self.config.write_text("LUME_MODE=completo\n", encoding="utf-8")
        with patch.dict(os.environ, {"LUME_MODE": "lumini"}):
            self.assertTrue(mode.e_lumini())

    def test_valor_desconhecido_cai_no_completo(self):
        """Um erro de digitação não pode mutilar a interface de ninguém."""
        self.config.write_text("LUME_MODE=gravadorr\n", encoding="utf-8")
        self.assertEqual(mode.modo_atual(), "completo")

    def test_health_e_status_publicam_o_modo(self):
        """Sem isso a interface adivinha, e mostra botões de IA a quem não tem."""
        self.assertEqual(backend_main.health()["mode"], "completo")
        with patch.dict(os.environ, {"LUME_MODE": "lumini"}):
            self.assertEqual(backend_main.health()["mode"], "lumini")

    # --- a tabela de rotas -------------------------------------------------

    def test_rotas_de_analise_estao_classificadas_como_ia(self):
        for caminho in ("/api/search", "/api/summary/2026-09-26", "/api/timeline/2026-09-26",
                        "/api/activities/2026-09-26", "/api/captures", "/api/pipeline/queue",
                        "/api/tags", "/api/ollama/models", "/api/voice-identities",
                        "/api/settings/prompts", "/api/videos/process",
                        "/api/videos/12/analysis", "/api/videos/12/context",
                        "/api/videos/12/speakers/spk1", "/api/video-sessions/3/process"):
            self.assertTrue(backend_main.rota_de_ia(caminho), caminho)

    def test_rotas_de_gravacao_nao_sao_confundidas_com_analise(self):
        """Um prefixo desatento na tabela derrubaria a biblioteca de clipes."""
        for caminho in ("/api/videos", "/api/video", "/api/video-download", "/api/video-light",
                        "/api/video-thumbnail", "/api/video-audio-tracks", "/api/share/light",
                        "/api/share/upload", "/api/video-sessions", "/api/videos/12/markers",
                        "/api/videos/12/trim", "/api/videos/12/captured-at",
                        "/api/videos/preserve", "/api/settings/video", "/api/settings/storage",
                        "/api/settings/audio",
                        "/api/editing", "/api/status", "/api/health", "/api/files"):
            self.assertFalse(backend_main.rota_de_ia(caminho), caminho)

    def test_toda_rota_da_api_esta_classificada(self):
        """Rota nova obriga uma decisão: é análise ou é gravação?

        É este teste que impede o Lumini de apodrecer. Sem ele, uma rota de IA
        acrescentada daqui a seis meses passaria a chamar Ollama na máquina de
        quem não o tem, e ninguém perceberia até o amigo reclamar.
        """
        # Cada rota de gravação conhecida, com o método que a usa. Acrescentar
        # uma rota nova aqui é a forma de dizer "esta não depende de IA".
        gravacao = {
            "/api/updates", "/api/updates/prepare", "/api/updates/cancel", "/api/updates/install",
            "/api/health", "/api/status", "/api/capture/{action}", "/api/settings/screen",
            "/api/settings/audio", "/api/settings/audio/mic-level",
            "/api/settings/sensitive", "/api/settings/storage", "/api/settings/video",
            "/api/settings/cleanup", "/api/test/screen", "/api/test/screen-change/start",
            "/api/test/screen-change/compare", "/api/test/video-window", "/api/test/audio",
            "/api/screenshot", "/api/audio", "/api/video", "/api/video-download",
            "/api/video-thumbnail", "/api/video-audio-tracks", "/api/video-audio-track", "/api/video/end-session",
            "/api/share/light", "/api/video-light", "/api/share/upload",
            "/api/share/links/{link_id}", "/api/videos", "/api/videos/import",
            "/api/video-sessions", "/api/video-sessions/join", "/api/video-sessions/{session_id}",
            "/api/video-sessions/{session_id}/clips/{video_id}", "/api/videos/{video_id}/markers",
            "/api/video-markers/{marker_id}", "/api/videos/{video_id}/trim",
            "/api/videos/{video_id}/captured-at", "/api/videos/preserve", "/api/files",
            "/api/files/unprocessed/all", "/api/retention/{kind}/{item_id}",
            "/api/media/raw/unkept", "/api/editing", "/api/editing/video/{video_id}",
            "/api/editing/session/{session_id}", "/api/editing/{name}", "/api/editing/open",
            "/api/settings/steamgriddb", "/api/settings/video/sounds", "/api/settings/video/sounds/{slot}",
            "/api/settings/video/sounds/{slot}/test", "/api/settings/video/sounds/preset/{theme}", "/api/game-icons", "/api/game-icons/retry", "/api/game-icons/{file_name}",
        }
        sem_classificacao = []
        for rota in backend_main.app.routes:
            caminho = getattr(rota, "path", "")
            if not caminho.startswith("/api/") or caminho in gravacao:
                continue
            # O caminho com `{}` não casa os regex de sufixo; troca-se por um id
            # qualquer para perguntar à tabela o que ela diria em execução.
            concreto = re.sub(r"\{[^}]+\}", "7", caminho)
            if not backend_main.rota_de_ia(concreto):
                sem_classificacao.append(caminho)
        self.assertEqual(sem_classificacao, [], "rotas sem classificação de modo")

    def test_supervisor_do_windows_nao_oferece_as_units_da_analise(self):
        """Oferecer "processar" numa máquina sem Ollama é oferecer uma falha."""
        completo = _units_do_supervisor("completo")
        lumini = _units_do_supervisor("lumini")
        self.assertIn("lume-process.service", completo)
        self.assertNotIn("lume-process.service", lumini)
        self.assertNotIn("captura-dia-audio.service", lumini)
        self.assertIn("captura-dia-video.service", lumini)
        self.assertIn("captura-dia-hud.service", lumini)

    def test_a_api_sobe_sem_numpy_e_sem_sherpa(self):
        """O Lumini não instala as dependências da análise.

        Um `import numpy` no topo de qualquer módulo do caminho quente tornaria a
        instalação dos amigos impossível — e o erro apareceria só na máquina
        deles. Em subprocesso porque bloquear import no processo de teste
        contaminaria o resto da suíte.
        """
        programa = (
            "import sys, importlib.abc\n"
            "class Bloqueio(importlib.abc.MetaPathFinder):\n"
            "    def find_spec(self, name, path=None, target=None):\n"
            "        if name.split('.')[0] in {'numpy', 'sherpa_onnx'}:\n"
            "            raise ImportError(name)\n"
            "        return None\n"
            "sys.meta_path.insert(0, Bloqueio())\n"
            "import app.backend.main as m\n"
            "import app.capture.winvideo, app.capture.hud, app.capture.gamesession\n"
            "assert len(m.app.routes) > 50, len(m.app.routes)\n"
        )
        resultado = subprocess.run([sys.executable, "-c", programa],
                                   cwd=Path(__file__).resolve().parents[2],
                                   capture_output=True, text=True, timeout=120)
        self.assertEqual(resultado.returncode, 0, resultado.stderr[-2000:])


def _units_do_supervisor(modo: str) -> list[str]:
    """Nomes de unit que o supervisor do Windows oferece naquele modo.

    Em subprocesso porque a poda acontece na importação do módulo: recarregá-lo
    no processo de teste deixaria a tabela furada para os outros testes.
    """
    programa = ("import json;from app.backend import services;"
                "print(json.dumps(sorted(services._UNITS)))")
    resultado = subprocess.run(
        [sys.executable, "-c", programa], cwd=Path(__file__).resolve().parents[2],
        capture_output=True, text=True, timeout=60,
        env={**os.environ, "LUME_MODE": modo},
    )
    if resultado.returncode != 0:
        raise AssertionError(resultado.stderr[-2000:])
    return json.loads(resultado.stdout)
