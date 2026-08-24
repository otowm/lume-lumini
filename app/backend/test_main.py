import os
import json
import tempfile
import threading
import unittest
import wave
from array import array
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from app.backend import database, main as backend_main, pipeline
from app.backend.audio_intelligence import consolidate_events, enrich_segments, identify_profiles, overlapping_sources, speaker_profiles
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


class ConfigTests(unittest.TestCase):
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
             patch.object(pipeline, "discover", return_value={"audio": 1, "screen": 2}):
            database.initialize()
            with database.connect() as db:
                db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('audio','a.wav','2026-08-09','pending')")
                db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('screen','s.png','2026-08-09','error')")
            result = backend_main.enqueue_unprocessed()
        self.assertEqual(result["queued"], {"audio": 1, "screen": 1, "total": 2})
        self.assertEqual(result["discovered"], {"audio": 1, "screen": 2})
        start.assert_called_once_with("start", ["lume-process.service"], timeout=20, no_block=True)

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

    def test_activity_groups_follow_app_and_temporal_continuity(self):
        rows = [
            {"id": 1, "app": "Code", "captured_at": "2026-08-08T10:00:00-03:00"},
            {"id": 2, "app": "Code", "captured_at": "2026-08-08T10:08:00-03:00"},
            {"id": 3, "app": "Browser", "captured_at": "2026-08-08T10:09:00-03:00"},
            {"id": 4, "app": "Code", "captured_at": "2026-08-08T10:25:00-03:00"},
        ]
        self.assertEqual([[item["id"] for item in group] for group in _activity_groups(rows)], [[1, 2], [3], [4]])

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
            self.assertEqual(mocked.call_count, 3)
            with database.connect() as db:
                activity = db.execute("SELECT * FROM activity_sessions").fetchone()
            self.assertEqual(activity["source_count"], 35)
            self.assertEqual(len(json.loads(activity["capture_ids_json"])), 35)

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
            screen_dir, audio_dir, video_dir, clips_dir = (root / name for name in ("screen", "audio", "video", "clips"))
            for path in (screen_dir, audio_dir, video_dir, clips_dir):
                path.mkdir()
            kept = screen_dir / "kept.png"; kept.write_bytes(b"kept")
            removed = screen_dir / "removed.png"; removed.write_bytes(b"removed")
            video = video_dir / "removed.mkv"; video.write_bytes(b"video")
            with (
                patch.object(database, "DB_PATH", root / "lume.sqlite3"),
                patch.object(backend_main, "SCREEN_DIR", screen_dir),
                patch.object(backend_main, "AUDIO_DIR", audio_dir),
                patch.object(backend_main, "VIDEO_DIR", video_dir),
                patch.object(backend_main, "CLIPS_DIR", clips_dir),
                patch.object(backend_main, "unit_state", return_value={"active": False}),
            ):
                database.initialize()
                with database.connect() as db:
                    db.execute("INSERT INTO captures(kind,source_path,captured_at,status,preserved) VALUES('screen',?,'2026-08-08T10:00:00-03:00','done',1)", (backend_main.media_source_key(kept),))
                    removed_id = db.execute("INSERT INTO captures(kind,source_path,captured_at,status) VALUES('screen',?,'2026-08-08T10:01:00-03:00','done')", (backend_main.media_source_key(removed),)).lastrowid
                    video_id = db.execute("INSERT INTO video_segments(source_path,captured_at,status) VALUES(?,'2026-08-08T10:02:00-03:00','done')", (backend_main.media_source_key(video),)).lastrowid
                result = backend_main.delete_unkept_raw_media()
                self.assertTrue(kept.is_file())
                self.assertFalse(removed.exists())
                self.assertFalse(video.exists())
                self.assertEqual(result["deleted_total"], 2)
                with database.connect() as db:
                    self.assertIsNotNone(db.execute("SELECT id FROM captures WHERE id=?", (removed_id,)).fetchone())
                    self.assertIsNotNone(db.execute("SELECT id FROM video_segments WHERE id=?", (video_id,)).fetchone())
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


class VideoSettingsRoundTripTests(unittest.TestCase):
    """Salvar as preferências não pode apagar chaves silenciosamente.

    ``set_video_settings`` reescreve ``video.conf`` inteiro a partir de um
    template fixo, então toda chave nova precisa estar em três lugares — modelo,
    leitura e template. Esquecer o template não quebra nada na hora: a chave
    simplesmente desaparece no primeiro save, e o defeito só aparece depois.
    """

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

    def test_hud_preferences_survive_a_save(self):
        after = self._round_trip(
            "VIDEO_ENABLED=true\nVIDEO_FPS=60\nVIDEO_GEOMETRY=1920x1080\n"
            "VIDEO_HUD_ENABLED=true\nVIDEO_HUD_PLACEMENT=both\n"
            "VIDEO_HUD_CORNER=bottom-left\nVIDEO_HUD_HOTKEY=Ctrl+F9\n"
            "VIDEO_HUD_SOUND=false\n"
        )
        self.assertTrue(after["hud_enabled"])
        self.assertEqual(after["hud_placement"], "both")
        self.assertEqual(after["hud_corner"], "bottom-left")
        self.assertEqual(after["hud_hotkey"], "Ctrl+F9")
        self.assertFalse(after["hud_sound"])

    def test_config_without_hud_keys_gets_usable_defaults(self):
        """Uma instalação antiga não pode ficar sem HUD nem quebrar ao salvar."""
        after = self._round_trip("VIDEO_ENABLED=true\nVIDEO_FPS=60\nVIDEO_GEOMETRY=1920x1080\n")
        self.assertTrue(after["hud_enabled"])
        self.assertEqual(after["hud_placement"], "second")
        self.assertEqual(after["hud_hotkey"], "Ctrl+Shift+F8")


if __name__ == "__main__":
    unittest.main()
