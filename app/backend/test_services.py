"""Testes das peças que tornam o app portável entre Linux e Windows.

Rodam nos dois sistemas: o que é específico do Windows é verificado pela via
que dá para exercitar em qualquer lugar (resolução de units, política de
reinício, formato do estado) e o resto é pulado explicitamente.
"""

import json
import os
import tempfile
import threading
import unittest
import unittest.mock
from types import SimpleNamespace
from array import array
from datetime import datetime
from pathlib import Path

from app.backend.services import ActionResult, SystemdServiceManager, _resolve
from app.capture.base import AudioConfig, Monitor, matched_sensitive_pattern
from app.capture.imagediff import THUMB_HEIGHT, THUMB_WIDTH, difference_percent, thumbnail
from app.capture.windows import WindowsCaptureBackend
from app.capture.wasapi import _BoxResampler
from app.capture.winrecord import _multichannel, _stereo
from app.capture.winscreen import _monitor_key, _parse_config

IS_WINDOWS = os.name == "nt"


class StereoAudioTests(unittest.TestCase):
    def test_microphone_and_system_are_written_to_distinct_channels(self):
        pcm = array("h")
        pcm.frombytes(_stereo(array("f", [0.25, -0.5]), array("f", [-0.75, 1.0])))
        self.assertEqual(list(pcm), [8191, -24575, -16383, 32767])

    def test_microphone_discord_and_other_audio_use_three_channels(self):
        pcm = array("h")
        pcm.frombytes(_multichannel([
            array("f", [0.25, -0.5]),
            array("f", [-0.75, 1.0]),
            array("f", [0.5, 0.0]),
        ]))
        self.assertEqual(list(pcm), [8191, -24575, 16383, -16383, 32767, 0])


class UnitResolutionTests(unittest.TestCase):
    def test_plain_unit(self):
        definition, arg = _resolve("captura-dia-audio.service")
        self.assertIsNotNone(definition)
        self.assertEqual(definition.kind, "simple")
        self.assertTrue(definition.restart)
        self.assertEqual(arg, "")

    def test_template_unit_carries_the_day(self):
        definition, arg = _resolve("lume-summary@2026-08-05.service")
        self.assertIsNotNone(definition)
        self.assertEqual(definition.kind, "oneshot")
        self.assertEqual(arg, "2026-08-05")
        self.assertIn("--summary-only", definition.argv(arg))
        self.assertIn("2026-08-05", definition.argv(arg))

    def test_unknown_unit(self):
        definition, _ = _resolve("nao-existe.service")
        self.assertIsNone(definition)

    def test_target_lists_the_two_captures(self):
        definition, _ = _resolve("captura-dia.target")
        self.assertEqual(
            set(definition.members),
            {"captura-dia-audio.service", "captura-dia-tela.service"},
        )


class SystemdFallbackTests(unittest.TestCase):
    def test_missing_systemctl_reports_unknown_instead_of_raising(self):
        """Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API."""
        manager = SystemdServiceManager()
        with unittest.mock.patch.object(
            SystemdServiceManager, "_run",
            return_value=ActionResult(127, "", "systemctl: comando indisponível")):
            state = manager.state("captura-dia-audio.service")
        self.assertFalse(state["active"])
        self.assertEqual(state["active_state"], "unknown")


@unittest.skipUnless(IS_WINDOWS, "supervisor só existe no Windows")
class SupervisorTests(unittest.TestCase):
    def _manager(self, tmp: Path):
        from app.backend import services

        with unittest.mock.patch.object(services, "STATE_FILE", tmp / "services.json"):
            manager = services.WindowsServiceManager()
            manager._save_state()
            return manager

    def test_start_marks_the_unit_to_return_next_time(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = self._manager(Path(directory))
            unit = "captura-dia-audio.service"
            with unittest.mock.patch.object(manager, "_start",
                                            return_value=ActionResult(0)):
                manager.action("start", [unit])
            self.assertIn(unit, manager._enabled)
            with unittest.mock.patch.object(manager, "_stop",
                                            return_value=ActionResult(0)):
                manager.action("stop", [unit])
            self.assertNotIn(unit, manager._enabled)

    def test_try_restart_leaves_a_stopped_unit_stopped(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = self._manager(Path(directory))
            with unittest.mock.patch.object(manager, "_start") as start:
                manager.action("try-restart", ["captura-dia-tela.service"])
            start.assert_not_called()

    def test_unknown_unit_fails_with_a_readable_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            manager = self._manager(Path(directory))
            result = manager.action("start", ["nao-existe.service"])
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("desconhecida", result.stderr)

    def test_idle_pauses_only_audio_and_screens(self):
        from app.backend import services

        with tempfile.TemporaryDirectory() as directory:
            manager = self._manager(Path(directory))
            manager._enabled.update((*manager._PAUSABLE, "captura-dia-video.service"))
            manager._capture_blocked = False
            manager._idle_seen = False
            manager._idle_pause_seconds = 300
            with unittest.mock.patch.object(services, "windows_idle_seconds", return_value=301), \
                 unittest.mock.patch.object(services, "video_recording_flag",
                                              return_value=Path(directory) / "no-video"), \
                 unittest.mock.patch.object(manager, "_stop",
                                              return_value=ActionResult(0)) as stop:
                manager._follow_capture_policy()

            self.assertTrue(manager._capture_blocked)
            self.assertTrue(manager.idle_state()["captures_paused"])
            self.assertEqual(
                {call.args[0] for call in stop.call_args_list}, set(manager._PAUSABLE))
            self.assertNotIn("captura-dia-video.service",
                             {call.args[0] for call in stop.call_args_list})

    def test_activity_does_not_resume_captures_while_video_is_recording(self):
        from app.backend import services

        with tempfile.TemporaryDirectory() as directory:
            manager = self._manager(Path(directory))
            manager._enabled.update(manager._PAUSABLE)
            manager._capture_blocked = True
            manager._idle_seen = True
            manager._idle_pause_seconds = 300
            video_flag = Path(directory) / "video-recording"
            video_flag.touch()
            with unittest.mock.patch.object(services, "windows_idle_seconds", return_value=0), \
                 unittest.mock.patch.object(services, "video_recording_flag",
                                              return_value=video_flag), \
                 unittest.mock.patch.object(manager, "_start") as start:
                manager._follow_capture_policy()
            start.assert_not_called()
            self.assertTrue(manager._capture_blocked)

            video_flag.unlink()
            with unittest.mock.patch.object(services, "windows_idle_seconds", return_value=0), \
                 unittest.mock.patch.object(services, "video_recording_flag",
                                              return_value=video_flag), \
                 unittest.mock.patch.object(manager, "_start",
                                              return_value=ActionResult(0)) as start:
                manager._follow_capture_policy()
            self.assertEqual(
                {call.args[0] for call in start.call_args_list}, set(manager._PAUSABLE))
            self.assertFalse(manager._capture_blocked)

    def test_video_unit_is_supported_and_runs_the_video_loop(self):
        definition, _ = _resolve("captura-dia-video.service")
        self.assertEqual(definition.kind, "simple")
        self.assertIn("app.capture.winvideo", definition.argv(""))

    def test_audio_argv_asks_for_the_shared_wav_format(self):
        from app.capture import get_backend

        argv = get_backend().audio_record_argv(
            AudioConfig(outdir=Path(tempfile.gettempdir()), segment_seconds=900,
                        duration_seconds=5))
        self.assertIn("app.capture.winrecord", argv)
        self.assertIn("--duration", argv)

    def test_future_schedule_saved_today_still_runs_today(self):
        from app.backend import services

        class Clock(datetime):
            current = datetime(2026, 8, 8, 1, 30)

            @classmethod
            def now(cls, tz=None):
                return cls.current

        with tempfile.TemporaryDirectory() as directory, \
             unittest.mock.patch.object(services, "STATE_FILE", Path(directory) / "services.json"), \
             unittest.mock.patch.object(services, "datetime", Clock):
            manager = services.WindowsServiceManager()
            manager.set_timer("01:42", True)
            self.assertEqual(manager._last_timer_run, "")

            Clock.current = datetime(2026, 8, 8, 1, 42)
            with unittest.mock.patch.object(manager, "_start", return_value=ActionResult(0)) as start:
                manager._check_timer()

            start.assert_called_once_with("lume-process.service")
            self.assertEqual(manager._last_timer_run, "2026-08-08")

    def test_past_schedule_saved_today_does_not_run_immediately(self):
        from app.backend import services

        class Clock(datetime):
            @classmethod
            def now(cls, tz=None):
                return datetime(2026, 8, 8, 1, 45)

        with tempfile.TemporaryDirectory() as directory, \
             unittest.mock.patch.object(services, "STATE_FILE", Path(directory) / "services.json"), \
             unittest.mock.patch.object(services, "datetime", Clock):
            manager = services.WindowsServiceManager()
            manager.set_timer("01:42", True)

            with unittest.mock.patch.object(manager, "_start", return_value=ActionResult(0)) as start:
                manager._check_timer()

            start.assert_not_called()
            self.assertEqual(manager._last_timer_run, "2026-08-08")


@unittest.skipUnless(IS_WINDOWS, "gravação de vídeo só existe no Windows")
class VideoHotkeyTests(unittest.TestCase):
    def test_parses_function_keys_and_modifiers(self):
        from app.capture.winvideo import MarkerHotkey

        self.assertEqual(MarkerHotkey._parse("F8"), (0, 0x77))
        self.assertEqual(MarkerHotkey._parse("F1"), (0, 0x70))
        # CTRL=2, SHIFT=4 -> 6
        self.assertEqual(MarkerHotkey._parse("CTRL+SHIFT+F9"), (6, 0x78))
        self.assertEqual(MarkerHotkey._parse("ALT+M"), (1, ord("M")))

    def test_rejects_nonsense_instead_of_registering_something_random(self):
        from app.capture.winvideo import MarkerHotkey

        self.assertIsNone(MarkerHotkey._parse(""))
        self.assertIsNone(MarkerHotkey._parse("CTRL+"))
        self.assertIsNone(MarkerHotkey._parse("F99"))


class VideoMarkerTransitionTests(unittest.TestCase):
    def test_marker_during_recording_warmup_is_applied_to_clip_start(self):
        from app.capture.winvideo import VideoLoop

        loop = object.__new__(VideoLoop)
        loop.recording_active = False
        loop.recording_started = 0.0
        loop.pending_markers = []
        loop.session_active = True
        loop.marker_queued_for_start = False
        loop._marker_lock = threading.Lock()

        with unittest.mock.patch.object(loop, "_confirmation_sound"), \
             unittest.mock.patch.object(loop, "_note_event"):
            loop.add_marker()
        self.assertTrue(loop.marker_queued_for_start)
        with unittest.mock.patch("app.capture.winvideo.time.monotonic", return_value=123.0):
            loop._activate_recording()

        self.assertTrue(loop.recording_active)
        self.assertFalse(loop.marker_queued_for_start)
        self.assertEqual(loop.pending_markers, [0.0])

    def test_marker_is_still_ignored_when_no_video_session_is_active(self):
        from app.capture.winvideo import VideoLoop

        loop = object.__new__(VideoLoop)
        loop.recording_active = False
        loop.recording_started = 0.0
        loop.pending_markers = []
        loop.session_active = False
        loop.marker_queued_for_start = False
        loop._marker_lock = threading.Lock()

        with unittest.mock.patch.object(loop, "_note_event"):
            loop.add_marker()
        self.assertFalse(loop.marker_queued_for_start)
        self.assertEqual(loop.pending_markers, [])


class VideoReplayClipTests(unittest.TestCase):
    def test_replay_buffer_signals_pause_and_releases_it_when_done(self):
        from app.capture.winvideo import VideoLoop

        loop = object.__new__(VideoLoop)
        loop.stopping = True
        loop.session_active = False
        loop.clip_save_queued = False
        with unittest.mock.patch.object(loop, "_suspend_others") as suspend, \
             unittest.mock.patch.object(loop, "_begin_game_session") as begin, \
             unittest.mock.patch.object(loop, "_finish_game_session") as finish, \
             unittest.mock.patch.object(loop, "_start_replay_buffer", return_value=True), \
             unittest.mock.patch.object(loop, "_stop_replay_buffer") as stop, \
             unittest.mock.patch.object(loop, "_release_others") as release:
            loop._record_clip_session("Meu Jogo")

        suspend.assert_called_once_with("Meu Jogo")
        begin.assert_called_once()
        finish.assert_called_once_with()
        stop.assert_called_once_with()
        release.assert_called_once_with("buffer de clipes encerrado")
        self.assertFalse(loop.session_active)

    def test_saved_replay_gets_session_sidecars_and_confirmation(self):
        from app.capture import winvideo

        with tempfile.TemporaryDirectory() as directory:
            replay = Path(directory) / "Replay 2026-08-08.mkv"
            replay.write_bytes(b"video")
            loop = object.__new__(winvideo.VideoLoop)
            loop.clip_buffer_active = True
            loop.clip_save_queued = False
            loop.clip_session_key = "sessao-jogo"
            loop.clip_window = "Meu Jogo | jogo.exe"
            loop._clip_lock = threading.Lock()
            loop.settings = unittest.mock.Mock(replay_seconds=60)

            responses = iter([
                {"savedReplayPath": "C:/antigo.mkv"},
                {},
                {"savedReplayPath": str(replay)},
            ])
            with unittest.mock.patch.object(winvideo.obs, "call", side_effect=lambda *_args, **_kwargs: next(responses)), \
                 unittest.mock.patch.object(loop, "_confirmation_sound") as sound, \
                 unittest.mock.patch.object(loop, "_note_event"):
                result = loop.save_replay_clip()

            self.assertEqual(result, replay)
            self.assertEqual(
                replay.with_suffix(".mkv.session").read_text(encoding="utf-8"),
                "sessao-jogo\nMeu Jogo | jogo.exe\n",
            )
            self.assertEqual(
                replay.with_suffix(".mkv.window").read_text(encoding="utf-8"),
                "Meu Jogo | jogo.exe",
            )
            sound.assert_called_once()

    def test_obs_replay_duration_is_independent_from_file_retention(self):
        from app.capture import obs

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with unittest.mock.patch.object(obs, "OBS_HOME", root / "obs"), \
                 unittest.mock.patch.object(obs, "OBS_CONFIG", root / "obs" / "config"), \
                 unittest.mock.patch.object(obs, "VIDEO_DIR", root / "video"), \
                 unittest.mock.patch.object(obs, "PASSWORD_FILE", root / "password"):
                obs.write_config(retention_minutes=1440, replay_seconds=60)
                basic = (root / "obs" / "config" / "basic" / "profiles" / obs.PROFILE / "basic.ini").read_text(encoding="utf-8")
            self.assertIn("RecRBTime=60", basic)
            self.assertNotIn("RecRBTime=86400", basic)
            self.assertIn("RecTracks=15", basic)
            self.assertIn("Track2Name=Microfone", basic)
            self.assertIn("Track3Name=Discord", basic)
            self.assertIn("Track4Name=Sistema", basic)


class ObsWindowSpecTests(unittest.TestCase):
    """O identificador de janela do OBS é ``título:classe:executável``.

    Um título com ``:`` — "Half-Life: Alyx" — quebraria a divisão dos campos e o
    OBS procuraria uma janela inexistente, sem sequer tentar o hook: gravação
    válida, porém preta.
    """

    def test_colon_in_the_title_is_escaped(self):
        from app.capture.obs import _encode_field

        self.assertEqual(_encode_field("Half-Life: Alyx"), "Half-Life#3A Alyx")
        self.assertEqual(_encode_field("testsrc2=size=1920x1080:rate=60"),
                         "testsrc2=size=1920x1080#3Arate=60")

    def test_hash_is_escaped_before_the_colon(self):
        from app.capture.obs import _encode_field

        # Se o '#' não fosse escapado primeiro, "#3A" viraria um dois-pontos
        # falso ao ser relido.
        self.assertEqual(_encode_field("Jogo #1: fase 2"), "Jogo #221#3A fase 2")

    def test_spec_keeps_three_fields(self):
        from app.capture.obs import _encode_field

        spec = ":".join(_encode_field(p) for p in
                        ("Half-Life: Alyx", "UnityWndClass", "hlvr.exe"))
        self.assertEqual(len(spec.split(":")), 3)
        self.assertTrue(spec.endswith(":hlvr.exe"))

    def test_roblox_legacy_rule_defaults_to_window_capture_but_can_be_disabled(self):
        from app.capture.base import parse_video_app_rule

        self.assertEqual(parse_video_app_rule("exe:^RobloxPlayerBeta\\.exe$")[-1], "window")
        self.assertEqual(parse_video_app_rule(
            "[continuous source=game] exe:^RobloxPlayerBeta\\.exe$")[-1], "game")
        self.assertEqual(parse_video_app_rule("exe:^Big Walk\\.exe$")[-1], "game")


@unittest.skipUnless(IS_WINDOWS, "gravação de vídeo só existe no Windows")
class VideoSettingsTests(unittest.TestCase):
    def test_app_patterns_match_the_window_text(self):
        from app.capture import winvideo

        with tempfile.TemporaryDirectory() as directory:
            conf = Path(directory) / "video.conf"
            apps = Path(directory) / "video-apps.txt"
            conf.write_text(
                "VIDEO_ENABLED=true\nVIDEO_FPS=60\nVIDEO_CAPTURE_MODE=clips\nVIDEO_REPLAY_SECONDS=75\n",
                encoding="utf-8",
            )
            apps.write_text("# jogos\ncs2\\.exe\nBig Walk\n", encoding="utf-8")
            with unittest.mock.patch.object(winvideo, "VIDEO_CONFIG", conf), \
                 unittest.mock.patch.object(winvideo, "VIDEO_APPS", apps):
                settings = winvideo.Settings()
            self.assertTrue(settings.enabled)
            self.assertEqual(settings.capture_mode, "clips")
            self.assertEqual(settings.replay_seconds, 75)
            self.assertEqual(settings.capture_mode_for_details("Counter-Strike 2", "", "cs2.exe"), "clips")
            self.assertTrue(settings.matches("Counter-Strike 2 | cs2.exe"))
            self.assertTrue(settings.matches("BIG WALK | Big Walk.exe"))
            self.assertFalse(settings.matches("Big Walk | explorer.exe"))
            self.assertFalse(settings.matches("Documento | notepad.exe"))

    def test_each_game_can_override_the_default_capture_mode(self):
        from app.capture import winvideo

        with tempfile.TemporaryDirectory() as directory:
            conf = Path(directory) / "video.conf"
            apps = Path(directory) / "video-apps.txt"
            conf.write_text("VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=continuous\n", encoding="utf-8")
            apps.write_text(
                "[continuous fps=60 geometry=1920x1080 source=game] exe:^Big Walk\\.exe$\n"
                "[clips fps=30 geometry=1280x720 source=window] exe:^VALORANT-Win64-Shipping\\.exe$\n"
                "[clips fps=60 geometry=1600x900] exe:^osu!\\.exe$\n",
                encoding="utf-8",
            )
            with unittest.mock.patch.object(winvideo, "VIDEO_CONFIG", conf), \
                 unittest.mock.patch.object(winvideo, "VIDEO_APPS", apps):
                settings = winvideo.Settings()
        self.assertEqual(settings.capture_mode_for_details("", "", "Big Walk.exe"), "continuous")
        self.assertEqual(settings.capture_mode_for_details("", "", "VALORANT-Win64-Shipping.exe"), "clips")
        self.assertEqual(settings.capture_mode_for_details("", "", "osu!.exe"), "clips")
        self.assertEqual(settings.capture_rule_for_details("", "", "Big Walk.exe"), ("continuous", 60, "1920x1080", "game"))
        self.assertEqual(settings.capture_rule_for_details("", "", "VALORANT-Win64-Shipping.exe"), ("clips", 30, "1280x720", "window"))
        self.assertEqual(settings.capture_rule_for_details("", "", "osu!.exe"), ("clips", 60, "1600x900", "game"))
        self.assertIsNone(settings.capture_mode_for_details("", "", "explorer.exe"))
        self.assertTrue(winvideo.VideoLoop._same_app("Big Walk | Big Walk.exe", "Outro título | Big Walk.exe"))
        self.assertFalse(winvideo.VideoLoop._same_app("Big Walk | Big Walk.exe", "VALORANT | VALORANT.exe"))

    def test_recording_prepares_obs_with_the_active_games_profile(self):
        from app.capture import winvideo

        loop = winvideo.VideoLoop.__new__(winvideo.VideoLoop)
        loop.active_fps = 30
        loop.active_geometry = "1280x720"
        loop.active_capture_source = "window"
        loop.settings = SimpleNamespace(
            fps=60, geometry="1920x1080", retention_minutes=60,
            replay_seconds=60, codec="hevc",
        )
        loop._needs_prepare = True
        loop._prepared_profile = None
        with unittest.mock.patch.object(winvideo, "foreground_details", return_value=("VALORANT", "", "VALORANT.exe")), \
             unittest.mock.patch.object(winvideo.obs, "prepare") as prepare, \
             unittest.mock.patch.object(winvideo.obs, "stop_recording_if_active", return_value=None), \
             unittest.mock.patch.object(winvideo.obs, "stop_replay_buffer_if_active", return_value=False), \
             unittest.mock.patch.object(winvideo.obs, "target_window", return_value="janela") as target_window, \
             unittest.mock.patch.object(winvideo.obs, "call", return_value={}), \
             unittest.mock.patch.object(winvideo.time, "sleep"), \
             unittest.mock.patch.object(loop, "_activate_recording"):
            self.assertTrue(loop._start_recording("VALORANT | VALORANT.exe"))
        prepare.assert_called_once_with(
            fps=30, geometry="1280x720", retention_minutes=60,
            replay_seconds=60, codec="hevc",
        )
        target_window.assert_called_once_with(
            "VALORANT", "", "VALORANT.exe", window_capture=True,
        )
        self.assertEqual(loop._prepared_profile, (30, "1280x720", 60, "hevc"))

    def test_title_rules_must_be_explicit(self):
        from app.capture import winvideo

        with tempfile.TemporaryDirectory() as directory:
            conf = Path(directory) / "video.conf"
            apps = Path(directory) / "video-apps.txt"
            conf.write_text("VIDEO_ENABLED=true\n", encoding="utf-8")
            apps.write_text("title:^Big Walk$\nexe:^Big Walk\\.exe$\n", encoding="utf-8")
            with unittest.mock.patch.object(winvideo, "VIDEO_CONFIG", conf), \
                 unittest.mock.patch.object(winvideo, "VIDEO_APPS", apps):
                settings = winvideo.Settings()
            self.assertTrue(settings.matches("Big Walk | explorer.exe"))
            self.assertTrue(settings.matches("Outro título | Big Walk.exe"))

    def test_hevc_selects_amd_hardware_encoder_without_changing_audio_tracks(self):
        from app.capture import obs

        with tempfile.TemporaryDirectory() as directory, \
             unittest.mock.patch.object(obs, "OBS_CONFIG", Path(directory)):
            obs.write_config(codec="hevc")
            profile = (Path(directory) / "basic" / "profiles" / obs.PROFILE / "basic.ini").read_text(encoding="utf-8")
            self.assertIn("RecEncoder=amd_hevc", profile)
            self.assertIn("RecTracks=15", profile)
            self.assertIn("Track4Name=Sistema", profile)

    def test_broken_pattern_does_not_disable_the_rest(self):
        from app.capture import winvideo

        with tempfile.TemporaryDirectory() as directory:
            conf = Path(directory) / "video.conf"
            apps = Path(directory) / "video-apps.txt"
            conf.write_text("VIDEO_ENABLED=true\n", encoding="utf-8")
            apps.write_text("[quebrada\ncs2\n", encoding="utf-8")
            with unittest.mock.patch.object(winvideo, "VIDEO_CONFIG", conf), \
                 unittest.mock.patch.object(winvideo, "VIDEO_APPS", apps):
                settings = winvideo.Settings()
            self.assertEqual(len(settings.patterns), 1)
            self.assertTrue(settings.matches("cs2.exe"))


class ScreenConfigTests(unittest.TestCase):
    def test_bom_does_not_break_the_first_key(self):
        """Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tela.conf"
            path.write_bytes("﻿CAPTURE_MODE=change\nINTERVAL_SECONDS=7\n".encode())
            parsed = _parse_config(path)
            self.assertEqual(parsed["CAPTURE_MODE"], "change")
            self.assertEqual(parsed["INTERVAL_SECONDS"], "7")

    def test_monitor_key_identifies_the_screen_not_the_position(self):
        self.assertEqual(_monitor_key(Path("2026-08-05_10-00-00_mon1_display1.png")), "1")
        self.assertEqual(_monitor_key(Path("2026-08-05_10-00-00_mon0_display0.png")), "0")


class PrivacyTests(unittest.TestCase):
    def test_same_rule_matches_case_insensitively(self):
        with tempfile.TemporaryDirectory() as directory:
            patterns = Path(directory) / "janelas-sensiveis.txt"
            patterns.write_text("# comentário\nbanco\nKeePass\n", encoding="utf-8")
            self.assertEqual(
                matched_sensitive_pattern("Meu BANCO online | firefox", patterns), "banco")
            self.assertIsNone(
                matched_sensitive_pattern("Terminal | konsole", patterns))

    def test_broken_regex_is_ignored_instead_of_blocking_everything(self):
        with tempfile.TemporaryDirectory() as directory:
            patterns = Path(directory) / "janelas-sensiveis.txt"
            patterns.write_text("[inválida\nsenha\n", encoding="utf-8")
            self.assertEqual(matched_sensitive_pattern("digite a senha", patterns), "senha")


class ImageDiffTests(unittest.TestCase):
    def test_periodic_ffmpeg_helpers_never_open_a_windows_console(self):
        completed = SimpleNamespace(returncode=0, stdout=bytes(THUMB_WIDTH * THUMB_HEIGHT), stderr="")
        with unittest.mock.patch("app.capture.imagediff.subprocess.run", return_value=completed) as run:
            self.assertIsNotNone(thumbnail(Path("frame.png")))
        self.assertEqual(run.call_args.kwargs["creationflags"], getattr(__import__("subprocess"), "CREATE_NO_WINDOW", 0))

        backend = WindowsCaptureBackend()
        with tempfile.TemporaryDirectory() as directory, \
             unittest.mock.patch("app.capture.windows.subprocess.run", return_value=completed) as run:
            backend._grab_region(Monitor(0, "display0", 0, 0, 1920, 1080), "1280x720>", Path(directory) / "frame.png")
        self.assertEqual(run.call_args.kwargs["creationflags"], getattr(__import__("subprocess"), "CREATE_NO_WINDOW", 0))

    def test_identical_frames_are_zero(self):
        frame = bytes([120]) * 1000
        self.assertEqual(difference_percent(frame, frame), 0.0)

    def test_full_inversion_is_one_hundred(self):
        self.assertEqual(difference_percent(bytes(1000), bytes([255]) * 1000), 100.0)

    def test_small_change_stays_below_the_threshold(self):
        """Variação de 5 níveis é ruído de compressão, não mudança de tela."""
        before = bytes([100]) * 1000
        after = bytes([105]) * 1000
        self.assertEqual(difference_percent(before, after), 0.0)


class ResamplerTests(unittest.TestCase):
    def test_48k_to_16k_keeps_the_duration(self):
        resampler = _BoxResampler(48000)
        out = resampler.feed(array("f", [0.5] * 48000))
        self.assertAlmostEqual(len(out), 16000, delta=2)

    def test_state_survives_between_buffers(self):
        """Blocos que não caem em fronteira redonda não podem perder amostras."""
        resampler = _BoxResampler(48000)
        total = sum(len(resampler.feed(array("f", [0.1] * 1000))) for _ in range(48))
        self.assertAlmostEqual(total, 16000, delta=2)

    def test_44100_is_handled_too(self):
        resampler = _BoxResampler(44100)
        out = resampler.feed(array("f", [0.2] * 44100))
        self.assertAlmostEqual(len(out), 16000, delta=2)


class LinuxIdlePauseTests(unittest.TestCase):
    """Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)."""

    def _manager(self):
        from app.backend import services

        manager = SystemdServiceManager()
        manager._idle_pause_seconds = 300
        self._active = {unit: True for unit in services.PAUSABLE_UNITS}
        self._calls = []

        def fake_state(unit):
            return {"active": self._active.get(unit, False)}

        def fake_action(verb, units, **kwargs):
            for unit in units:
                self._active[unit] = verb == "start"
                self._calls.append((verb, unit))
            return ActionResult(0)

        manager.state = fake_state
        manager.action = fake_action
        # Isola os flags deste teste do ambiente real.
        tmp = Path(tempfile.mkdtemp(prefix="lume-idle-test-"))
        manager._idle_flag = tmp / "idle"
        self._video_pause = tmp / "video-paused"
        self._patch = unittest.mock.patch.object(
            services, "_video_pause_file", lambda: self._video_pause)
        self._patch.start()
        self.addCleanup(self._patch.stop)
        return manager

    def test_idle_pauses_and_activity_resumes(self):
        manager = self._manager()
        manager._idle_flag.touch()
        manager._apply_idle_policy()
        self.assertEqual(manager._idle_suspended, set(_pausable()))
        self.assertTrue(all(v[0] == "stop" for v in self._calls))

        self._calls.clear()
        manager._idle_flag.unlink()
        manager._apply_idle_policy()
        self.assertEqual(manager._idle_suspended, set())
        self.assertTrue(all(v[0] == "start" for v in self._calls))
        self.assertTrue(all(self._active.values()))

    def test_video_pause_owns_the_captures(self):
        manager = self._manager()
        self._video_pause.touch()
        manager._idle_flag.touch()
        manager._apply_idle_policy()
        self.assertEqual(self._calls, [])
        self.assertEqual(manager._idle_suspended, set())

    def test_manual_pause_is_not_resumed_by_idle(self):
        manager = self._manager()
        for unit in _pausable():
            self._active[unit] = False  # usuário já pausou na interface
        manager._idle_flag.touch()
        manager._apply_idle_policy()
        self.assertEqual(manager._idle_suspended, set())
        self._calls.clear()
        manager._idle_flag.unlink()
        manager._apply_idle_policy()
        self.assertEqual(self._calls, [])

    def test_idle_state_flags_missing_swayidle(self):
        manager = SystemdServiceManager()
        manager._idle_pause_seconds = 300
        manager._swayidle_path = None
        state = manager.idle_state()
        self.assertFalse(state["supported"])
        self.assertIn("swayidle", state.get("hint", ""))


def _pausable():
    from app.backend.services import PAUSABLE_UNITS

    return PAUSABLE_UNITS


class LinuxAudioTrackTests(unittest.TestCase):
    """Gravação em faixas separadas (3 canais) no backend Linux."""

    def test_three_channel_argv_reads_the_three_buses(self):
        from app.capture.linux import LinuxCaptureBackend

        argv = LinuxCaptureBackend().audio_record_argv(
            AudioConfig(outdir=Path(tempfile.gettempdir()), channels=3, duration_seconds=5))
        self.assertEqual(argv.count("pulse"), 3)
        self.assertTrue(any("join=inputs=3" in token for token in argv))
        self.assertIn("MicBus.monitor", argv)
        self.assertIn("DiscordBus.monitor", argv)
        self.assertIn("RecordBus.monitor", argv)

    def test_mono_sample_keeps_single_source(self):
        from app.capture.linux import LinuxCaptureBackend

        argv = LinuxCaptureBackend().audio_record_argv(
            AudioConfig(outdir=Path(tempfile.gettempdir()), channels=1, duration_seconds=5))
        self.assertEqual(argv.count("pulse"), 1)
        self.assertNotIn("-filter_complex", argv)


class HudStateTests(unittest.TestCase):
    """As regras que decidem se a captura está saudável.

    Rodam nos dois sistemas de propósito: são a parte da HUD que não depende de
    OBS nem de PipeWire, e portanto a parte que dá para verificar sem um jogo
    aberto — inclusive no sistema que não está rodando.
    """

    @staticmethod
    def _recording(**overrides):
        from app.capture.hudstate import HudSnapshot

        base = dict(enabled=True, available=True, recording=True, elapsed_seconds=60.0,
                    video_hooked=True, disk_free_bytes=200 * 1024**3)
        base.update(overrides)
        return HudSnapshot(**base)

    def _keys(self, snapshot) -> set[str]:
        from app.capture.hudstate import evaluate

        return {alert.key for alert in evaluate(snapshot).alerts}

    def test_healthy_recording_raises_nothing(self):
        from app.capture.hudstate import evaluate

        status = evaluate(self._recording())
        self.assertEqual(status.level, "ok")
        self.assertEqual(status.headline, "Gravando")
        self.assertEqual(status.alerts, [])

    def test_capture_that_never_hooked_is_a_failure(self):
        self.assertIn("sem-imagem", self._keys(self._recording(video_hooked=False)))

    def test_hook_gets_a_grace_period_before_being_accused(self):
        # Logo após o StartRecord o hook ainda está injetando; acusar aqui seria
        # alarme falso em toda troca de segmento.
        self.assertNotIn("sem-imagem",
                         self._keys(self._recording(video_hooked=False, elapsed_seconds=2.0)))

    def test_linux_never_reports_a_hook_failure(self):
        # Lá se grava um monitor inteiro: não existe hook que possa falhar.
        self.assertNotIn("sem-imagem", self._keys(self._recording(video_hooked=None)))

    def test_stalled_file_is_a_failure(self):
        self.assertIn("travada", self._keys(self._recording(bytes_stalled_seconds=30.0)))

    def test_replay_buffer_is_not_expected_to_grow_a_file(self):
        # Em modo clipes o buffer vive em memória e não escreve nada até o F8.
        keys = self._keys(self._recording(recording=False, buffering=True,
                                          bytes_stalled_seconds=300.0))
        self.assertNotIn("travada", keys)

    def test_missing_microphone_is_a_failure(self):
        from app.capture.hudstate import Meter

        mic = Meter("Microfone", present=False, absent_seconds=20.0, required=True)
        self.assertIn("ausente:Microfone", self._keys(self._recording(meters=[mic])))

    def test_a_quiet_microphone_is_not_a_missing_one(self):
        """Ficar calado é normal; confundir com falha destrói a confiança na HUD."""
        from app.capture.hudstate import Meter

        mic = Meter("Microfone", peak_db=-90.0, present=True, silent_seconds=5.0, required=True)
        self.assertEqual(self._keys(self._recording(meters=[mic])), set())

    def test_a_long_silence_is_worth_a_gentle_warning(self):
        from app.capture.hudstate import Meter, evaluate

        mic = Meter("Microfone", peak_db=-90.0, present=True, silent_seconds=600.0, required=True)
        status = evaluate(self._recording(meters=[mic]))
        self.assertEqual([alert.level for alert in status.alerts], ["warn"])

    def test_silent_optional_sources_stay_quiet(self):
        # Discord fechado é o caso normal de quem joga sozinho.
        from app.capture.hudstate import Meter

        discord = Meter("Discord", present=False, absent_seconds=600.0)
        self.assertEqual(self._keys(self._recording(meters=[discord])), set())

    def test_muted_microphone_is_reported_even_while_present(self):
        from app.capture.hudstate import Meter

        mic = Meter("Microfone", present=False, muted=True, required=True)
        self.assertIn("mudo:Microfone", self._keys(self._recording(meters=[mic])))

    def test_disabled_video_reports_nothing_at_all(self):
        from app.capture.hudstate import evaluate

        status = evaluate(self._recording(enabled=False, video_hooked=False))
        self.assertEqual(status.alerts, [])

    def test_unknown_service_state_does_not_accuse_anyone(self):
        from app.capture.hudstate import evaluate

        idle = self._recording(recording=False, service_active=None)
        self.assertEqual(evaluate(idle).alerts, [])
        stopped = self._recording(recording=False, service_active=False)
        self.assertIn("servico", {alert.key for alert in evaluate(stopped).alerts})

    def test_decibel_conversion_floors_at_digital_silence(self):
        from app.capture.hudstate import SILENCE_DB, to_db

        self.assertEqual(to_db(0.0), SILENCE_DB)
        self.assertAlmostEqual(to_db(1.0), 0.0)
        self.assertAlmostEqual(to_db(0.5), -6.02, places=1)

    def test_elapsed_reads_like_a_stopwatch(self):
        from app.capture.hudstate import format_elapsed

        self.assertEqual(format_elapsed(95), "1:35")
        self.assertEqual(format_elapsed(3725), "1:02:05")


class HudPlacementTests(unittest.TestCase):
    """Onde a HUD desenha, dado o arranjo de monitores."""

    PRIMARY = Monitor(index=0, name="display0", x=0, y=0, width=1920, height=1080)
    SECOND = Monitor(index=1, name="display1", x=1920, y=0, width=1366, height=768)

    def test_game_placement_follows_the_focused_monitor(self):
        from app.capture.hud import choose_monitors

        chosen = choose_monitors("game", [self.PRIMARY, self.SECOND], self.SECOND)
        self.assertEqual([m.index for m in chosen], [1])

    def test_second_placement_avoids_the_game_monitor(self):
        from app.capture.hud import choose_monitors

        chosen = choose_monitors("second", [self.PRIMARY, self.SECOND], self.PRIMARY)
        self.assertEqual([m.index for m in chosen], [1])

    def test_both_covers_game_and_a_spare_monitor(self):
        from app.capture.hud import choose_monitors

        chosen = choose_monitors("both", [self.PRIMARY, self.SECOND], self.PRIMARY)
        self.assertEqual([m.index for m in chosen], [0, 1])

    def test_single_monitor_never_leaves_the_hud_homeless(self):
        """Com um monitor só, "no outro monitor" tem que recair sobre este."""
        from app.capture.hud import choose_monitors

        for placement in ("game", "second", "both"):
            chosen = choose_monitors(placement, [self.PRIMARY], self.PRIMARY)
            self.assertEqual([m.index for m in chosen], [0], placement)

    def test_no_monitors_is_handled_without_blowing_up(self):
        from app.capture.hud import choose_monitors

        self.assertEqual(choose_monitors("second", [], None), [])

    def test_corners_stay_inside_the_target_monitor(self):
        from app.capture.hud import corner_position

        for corner in ("top-left", "top-right", "bottom-left", "bottom-right"):
            x, y = corner_position(self.SECOND, corner, width=352, height=140)
            self.assertGreaterEqual(x, self.SECOND.x, corner)
            self.assertGreaterEqual(y, self.SECOND.y, corner)
            self.assertLessEqual(x + 352, self.SECOND.x + self.SECOND.width, corner)
            self.assertLessEqual(y + 140, self.SECOND.y + self.SECOND.height, corner)


class VideoActivityFlagTests(unittest.TestCase):
    """O sinal de atividade tem um significado só, e ele é caro de errar.

    Enquanto o arquivo existe, o supervisor mantém áudio e telas suspensos e a
    API relata gravação em curso. Publicá-lo fora de uma sessão — por um atalho
    apertado à toa, por exemplo — pausaria a captura do dia inteiro sem que
    nada estivesse sendo gravado.
    """

    def _loop(self, directory: Path, session_active: bool):
        from app.capture.winvideo import VideoLoop

        loop = object.__new__(VideoLoop)
        loop.activity_flag = directory / "lume-video-active"
        loop.session_active = session_active
        loop.session_started_at = 100.0
        loop.active_window = "Meu Jogo | jogo.exe"
        loop.active_capture_mode = "clips"
        loop.pending_markers = []
        loop.last_clip_name = ""
        loop.last_event = None
        loop.event_seq = 0
        loop.settings = unittest.mock.Mock(capture_mode="clips")
        return loop

    def test_an_event_outside_a_session_does_not_create_the_flag(self):
        with tempfile.TemporaryDirectory() as directory:
            loop = self._loop(Path(directory), session_active=False)
            loop._note_event("ignored", "Nada sendo gravado")
            self.assertFalse(loop.activity_flag.exists())

    def test_an_event_during_a_session_publishes_it_immediately(self):
        with tempfile.TemporaryDirectory() as directory:
            loop = self._loop(Path(directory), session_active=True)
            loop._note_event("marker", "Marcador 1 · 0:12")
            payload = json.loads(loop.activity_flag.read_text(encoding="utf-8"))
            self.assertEqual(payload["event"]["kind"], "marker")
            self.assertEqual(payload["event"]["label"], "Marcador 1 · 0:12")
            self.assertEqual(payload["event"]["seq"], 1)

    def test_the_sequence_distinguishes_two_identical_events(self):
        """Dois marcadores seguidos têm o mesmo rótulo; só a sequência os separa."""
        with tempfile.TemporaryDirectory() as directory:
            loop = self._loop(Path(directory), session_active=True)
            loop._note_event("marker", "Marcador 1")
            first = json.loads(loop.activity_flag.read_text(encoding="utf-8"))["event"]
            loop._note_event("marker", "Marcador 1")
            second = json.loads(loop.activity_flag.read_text(encoding="utf-8"))["event"]
            self.assertEqual(second["seq"], first["seq"] + 1)


class HudEventAnimationTests(unittest.TestCase):
    """A curva da animação de confirmação, sem abrir janela nenhuma."""

    def test_band_starts_hidden_and_settles_open(self):
        from app.capture.hud import EVENT_IN_SECONDS, EVENT_SLIDE_PX, event_animation

        start = event_animation("marker", 0.0)
        self.assertEqual((start.reveal, start.glow, start.slide), (0.0, 0.0, EVENT_SLIDE_PX))
        settled = event_animation("marker", EVENT_IN_SECONDS)
        self.assertEqual((settled.reveal, settled.glow, settled.slide), (1.0, 1.0, 0.0))

    def test_entry_overshoots_a_little_before_settling(self):
        """O repique é o que separa "apareceu" de "chegou"."""
        from app.capture.hud import EVENT_IN_SECONDS, event_animation

        peak = max(event_animation("marker", EVENT_IN_SECONDS * f).reveal
                   for f in (0.5, 0.6, 0.7, 0.8, 0.9))
        self.assertGreater(peak, 1.0)
        self.assertLess(peak, 1.2, "exagero demais vira enfeite")

    def test_colour_never_overshoots_even_when_movement_does(self):
        """Uma cor que passa do alvo não existe; um movimento que passa, sim."""
        from app.capture.hud import EVENT_IN_SECONDS, event_animation

        for f in (0.1, 0.5, 0.7, 0.9, 1.0):
            frame = event_animation("marker", EVENT_IN_SECONDS * f)
            self.assertLessEqual(frame.glow, 1.0)
            self.assertGreaterEqual(frame.glow, 0.0)

    def test_band_retracts_and_then_disappears(self):
        from app.capture.hud import EVENT_STYLES, event_animation

        total = EVENT_STYLES["marker"][2]
        fading = event_animation("marker", total - 0.1)
        self.assertIsNotNone(fading)
        self.assertLess(fading.reveal, 1.0)
        self.assertIsNone(event_animation("marker", total))

    def test_saving_a_clip_stays_up_much_longer_than_a_marker(self):
        """O OBS leva segundos para informar o arquivo; a faixa espera por ele."""
        from app.capture.hud import EVENT_STYLES

        self.assertGreater(EVENT_STYLES["clip_saving"][2], EVENT_STYLES["marker"][2] * 4)

    def test_unknown_event_draws_nothing_instead_of_crashing(self):
        from app.capture.hud import event_animation

        self.assertIsNone(event_animation("kind-que-nao-existe", 0.1))

    def test_blend_walks_between_the_two_colors(self):
        from app.capture.hud import blend

        self.assertEqual(blend("#000000", "#ffffff", 0.0), "#000000")
        self.assertEqual(blend("#000000", "#ffffff", 1.0), "#ffffff")
        self.assertEqual(blend("#000000", "#ffffff", 0.5), "#808080")


class HudFrameRateTests(unittest.TestCase):
    """As três cadências existem por causa do custo de redesenhar.

    Cada volta recria os itens do Canvas e custa alguns milissegundos; a 60
    quadros por segundo isso passaria de 20% de um núcleo, gasto justamente
    durante o jogo. A fluidez fica reservada ao que é curto e se nota.
    """

    def test_animation_is_the_fastest_cadence(self):
        from app.capture.hud import ANIMATION_TICK_MS, IDLE_TICK_MS, TICK_MS

        self.assertLess(ANIMATION_TICK_MS, TICK_MS)
        self.assertLess(TICK_MS, IDLE_TICK_MS)

    def test_animation_runs_near_sixty_frames_per_second(self):
        from app.capture.hud import ANIMATION_TICK_MS

        self.assertLessEqual(ANIMATION_TICK_MS, 20)

    def test_the_whole_entry_gets_many_frames(self):
        """Uma entrada de 0,26 s precisa de quadros suficientes para não escadear."""
        from app.capture.hud import ANIMATION_TICK_MS, EVENT_IN_SECONDS

        self.assertGreater(EVENT_IN_SECONDS * 1000 / ANIMATION_TICK_MS, 10)


class HudEventContractTests(unittest.TestCase):
    """O evento cruza dois processos por um arquivo; o formato é um contrato.

    O ``winvideo`` escreve e a HUD lê. Como são processos diferentes, nada além
    destes testes garante que os dois continuem falando a mesma língua.
    """

    def _flag(self, event):
        return {"window": "Jogo | jogo.exe", "started_at": 1.0, "mode": "clips",
                "markers": 2, "last_clip": "x.mkv", "event": event}

    def test_event_survives_the_trip_from_the_video_loop(self):
        import time as clock

        from app.capture.hudsource import _event_fields

        fields = _event_fields(self._flag(
            {"kind": "clip_saved", "label": "Clipe salvo · 60s", "seq": 7,
             "at": clock.time() - 1.5}))
        self.assertEqual(fields["event_kind"], "clip_saved")
        self.assertEqual(fields["event_label"], "Clipe salvo · 60s")
        self.assertEqual(fields["event_seq"], 7)
        self.assertAlmostEqual(fields["event_age_seconds"], 1.5, delta=0.5)

    def test_a_flag_without_an_event_reports_nothing(self):
        from app.capture.hudsource import _event_fields

        self.assertEqual(_event_fields(self._flag(None)), {})
        self.assertEqual(_event_fields({}), {})

    def test_every_kind_the_video_loop_emits_has_a_drawing_style(self):
        """Um tipo sem estilo seria um evento invisível — falha silenciosa."""
        import re as regex

        from app.capture.hud import EVENT_STYLES

        source = Path("app/capture/winvideo.py").read_text(encoding="utf-8")
        emitted = set(regex.findall(r'_note_event\("([a-z_]+)"', source))
        self.assertTrue(emitted, "nenhum evento encontrado em winvideo.py")
        self.assertEqual(emitted - set(EVENT_STYLES), set())


if __name__ == "__main__":
    unittest.main()
