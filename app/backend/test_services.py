"""Testes das peças que tornam o app portável entre Linux e Windows.

Rodam nos dois sistemas: o que é específico do Windows é verificado pela via
que dá para exercitar em qualquer lugar (resolução de units, política de
reinício, formato do estado) e o resto é pulado explicitamente.
"""

import json
import os
import shutil
import signal
import subprocess
import tempfile
import threading
import time
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


@unittest.skipIf(IS_WINDOWS, "o daemon de teclado é o caminho do Linux")
class HoldDetectorTests(unittest.TestCase):
    """Toque e segurada a partir dos eventos crus do teclado.

    O atalho do KDE só conhece "a tecla desceu"; é esta máquina de estados que
    transforma descer, repetir e soltar nas duas intenções do gravador.
    """

    def setUp(self):
        from app.capture.hotkeyd import HoldDetector

        self.detector = HoldDetector(hold_seconds=0.6)

    def test_a_quick_press_is_a_tap_and_only_on_release(self):
        # Disparar na descida faria toda gravação longa salvar um clipe solto
        # antes de começar: até soltar, um toque ainda pode virar segurada.
        self.assertIsNone(self.detector.feed(1, 0.0))
        self.assertEqual(self.detector.feed(0, 0.2), "tap")

    def test_holding_fires_while_the_key_is_still_down(self):
        # A segurada sai no instante em que o limite vence: é ela que confirma
        # à pessoa que já pode soltar.
        self.assertIsNone(self.detector.feed(1, 0.0))
        self.assertIsNone(self.detector.tick(0.3))
        self.assertEqual(self.detector.tick(0.7), "hold")

    def test_a_hold_does_not_also_produce_a_tap_when_released(self):
        self.detector.feed(1, 0.0)
        self.assertEqual(self.detector.tick(0.7), "hold")
        self.assertIsNone(self.detector.feed(0, 2.0))

    def test_autorepeat_counts_as_still_holding_not_as_new_presses(self):
        self.detector.feed(1, 0.0)
        self.assertIsNone(self.detector.feed(2, 0.4))
        self.assertEqual(self.detector.feed(2, 0.8), "hold")
        self.assertIsNone(self.detector.feed(2, 1.2))

    def test_key_that_was_never_pressed_releases_nothing(self):
        self.assertIsNone(self.detector.feed(0, 1.0))

    def test_raw_kernel_events_become_a_tap_and_a_hold(self):
        """O formato do ``input_event`` é contrato do kernel, não detalhe nosso.

        Errar o desempacotamento não quebra nada visível: o daemon simplesmente
        nunca reconheceria a tecla, e o atalho ficaria mudo.
        """
        import struct

        from app.capture import hotkeyd

        daemon = object.__new__(hotkeyd.HotkeyDaemon)
        daemon.detector = hotkeyd.ShortcutDetector("F8", hold_seconds=0.0)
        delivered = []
        daemon._deliver = delivered.append

        with tempfile.TemporaryDirectory() as directory:
            events = Path(directory) / "event-fake"
            def pack(code, value):
                return struct.pack(hotkeyd._EVENT_FORMAT, 0, 0, hotkeyd._EV_KEY, code, value)
            events.write_bytes(
                pack(66, 1) + pack(66, 0)          # F8: toque
                + pack(30, 1) + pack(30, 0)        # outra tecla: ignorada
                + pack(66, 1) + pack(66, 2))       # F8 segurado (limite zero)
            with events.open("rb", buffering=0) as handle:
                daemon._handles = {handle.fileno(): (str(events), handle)}
                daemon._read(handle.fileno(), 66)

        self.assertEqual(delivered, ["tap", "hold"])

    def test_shortcut_spec_keeps_only_the_key(self):
        from app.capture.hotkeyd import parse_key

        self.assertEqual(parse_key("F8"), 66)
        self.assertEqual(parse_key("Ctrl+Shift+F8"), 66)
        self.assertIsNone(parse_key("Ctrl"))
        self.assertIsNone(parse_key("Pause"))


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
        loop.long_recording = False
        loop.pending_clip = None
        loop.pending_clip_at = 0.0
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

    @staticmethod
    def _clip_loop(winvideo, replay_seconds: int = 60):
        """Laço só com o estado que o caminho dos clipes usa."""
        loop = object.__new__(winvideo.VideoLoop)
        loop.clip_buffer_active = True
        loop.clip_save_queued = False
        loop.clip_session_key = "sessao-jogo"
        loop.clip_window = "Meu Jogo | jogo.exe"
        loop._clip_lock = threading.Lock()
        loop.pending_clip = None
        loop.pending_clip_at = 0.0
        loop.clips_saved = 0
        loop.last_clip_name = ""
        loop.settings = unittest.mock.Mock(replay_seconds=replay_seconds)
        return loop

    def test_saved_replay_gets_session_sidecars_and_confirmation(self):
        """O clipe espera fora do buffer; ao ser publicado leva os sidecars.

        Publicá-lo de imediato é o que impediria a mesclagem: o Lume já teria
        indexado metade do trecho quando o segundo atalho chegasse.
        """
        from app.capture import winvideo

        with tempfile.TemporaryDirectory() as directory:
            buffer_dir = Path(directory) / "video-buffer"
            buffer_dir.mkdir()
            replay = buffer_dir / "Replay 2026-08-08.mkv"
            replay.write_bytes(b"video")
            loop = self._clip_loop(winvideo)

            responses = iter([
                {"savedReplayPath": "C:/antigo.mkv"},
                {},
                {"savedReplayPath": str(replay)},
            ])
            with unittest.mock.patch.object(winvideo, "VIDEO_DIR", buffer_dir), \
                 unittest.mock.patch.object(winvideo.obs, "call", side_effect=lambda *_args, **_kwargs: next(responses)), \
                 unittest.mock.patch.object(loop, "_confirmation_sound") as sound, \
                 unittest.mock.patch.object(loop, "_note_event"), \
                 unittest.mock.patch.object(loop, "_publish_activity"):
                pending = loop.save_replay_clip()
                self.assertEqual(pending, loop.pending_clip)
                self.assertEqual(list(buffer_dir.glob("*.mkv")), [],
                                 "o clipe entrou no buffer antes da janela fechar")
                published = loop.flush_pending_clip()

            self.assertIsNotNone(published)
            self.assertEqual(published.parent, buffer_dir)
            self.assertEqual(loop.last_clip_name, published.name)
            self.assertEqual(loop.clips_saved, 1)
            self.assertEqual(
                published.with_suffix(".mkv.session").read_text(encoding="utf-8"),
                "sessao-jogo\nMeu Jogo | jogo.exe\n",
            )
            self.assertEqual(
                published.with_suffix(".mkv.window").read_text(encoding="utf-8"),
                "Meu Jogo | jogo.exe",
            )
            sound.assert_called_once()

    def test_a_second_hotkey_inside_the_replay_window_extends_the_same_clip(self):
        """Dois atalhos em menos de um clipe descrevem um trecho só.

        Com clipes de um minuto, um segundo atalho vinte segundos depois salva
        de novo quarenta segundos que já estão no arquivo anterior: a mesma
        jogada em dois vídeos, o dobro de disco e o dobro de análise. Só o que
        o segundo pedido acrescenta é emendado — e o corte sai do fim do que já
        existe, que é o lado exato quando se copia os streams.
        """
        from app.capture import winvideo

        with tempfile.TemporaryDirectory() as directory:
            pending = Path(directory) / "clipe.mkv"
            pending.write_bytes(b"pendente")
            incoming = Path(directory) / "Replay 2.mkv"
            incoming.write_bytes(b"novo")
            loop = self._clip_loop(winvideo)
            loop.pending_clip = pending
            loop.pending_clip_at = 1000.0

            def concat(destination, *parts):
                destination.write_bytes(b"emendado")
                return True

            with unittest.mock.patch.object(winvideo, "media_duration", return_value=60.0), \
                 unittest.mock.patch.object(winvideo, "cut_head", return_value=True) as cut, \
                 unittest.mock.patch.object(winvideo, "concat_videos", side_effect=concat) as join:
                merged = loop._merge_pending_clip(incoming, 1020.0)

            self.assertEqual(merged, pending, "a mesclagem trocou o arquivo de nome")
            # 60s pendentes + 20s de intervalo − 60s do novo = 20s de começo.
            self.assertAlmostEqual(cut.call_args.args[2], 20.0, places=3)
            self.assertEqual(join.call_args.args[2], incoming)
            self.assertEqual(loop.pending_clip_at, 1020.0,
                             "a espera não reabriu a partir do segundo atalho")
            self.assertFalse(incoming.exists(), "o clipe novo ficou solto além da emenda")
            self.assertEqual(loop.clips_saved, 0, "mesclar contou um clipe a mais")

    def test_a_hotkey_after_the_replay_window_opens_another_clip(self):
        """Sem sobreposição não há o que mesclar: são duas jogadas distintas."""
        from app.capture import winvideo

        with tempfile.TemporaryDirectory() as directory:
            pending = Path(directory) / "clipe.mkv"
            pending.write_bytes(b"pendente")
            incoming = Path(directory) / "Replay 2.mkv"
            incoming.write_bytes(b"novo")
            loop = self._clip_loop(winvideo)
            loop.pending_clip = pending
            loop.pending_clip_at = 1000.0

            with unittest.mock.patch.object(winvideo, "media_duration", return_value=60.0), \
                 unittest.mock.patch.object(winvideo, "cut_head") as cut:
                self.assertIsNone(loop._merge_pending_clip(incoming, 1070.0))
            cut.assert_not_called()
            self.assertTrue(incoming.is_file())

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


@unittest.skipIf(IS_WINDOWS, "o gravador do Linux é um script bash")
class LinuxAppRuleMatchTests(unittest.TestCase):
    """Regras do ``bin/game-video-loop``, pelo modo ``--match`` do próprio script.

    O gravador do Linux é bash, então a única verificação honesta é rodá-lo. O
    caso que motivou o campo padrão: um vídeo no navegador chamado
    "mrekk | osu! ..." tem o nome do jogo no título e ligava a gravação.
    """

    SCRIPT = Path(__file__).resolve().parents[2] / "bin" / "game-video-loop"

    def _match(self, window: str, rules: str, enabled: bool = True) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / "config" / "captura-dia"
            config.mkdir(parents=True)
            (config / "video.conf").write_text(
                f"VIDEO_ENABLED={'true' if enabled else 'false'}\n", encoding="utf-8")
            (config / "video-apps.txt").write_text(rules, encoding="utf-8")
            result = subprocess.run(
                ["bash", str(self.SCRIPT), "--match", window],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, "HOME": str(home), "XDG_CONFIG_HOME": str(home / "config")})
            return result.returncode, result.stdout.strip()

    def test_game_name_in_the_title_does_not_start_a_recording(self):
        rules = "[clips fps=60 geometry=1920x1080 source=game] osu!\n"
        code, output = self._match("osu! | osu!", rules)
        self.assertEqual(code, 0, output)
        self.assertEqual(output.split("\t")[0], "grava")
        for browser in ("mrekk | osu! - YouTube | brave-browser",
                        "osu! no Google | firefox"):
            with self.subTest(window=browser):
                code, output = self._match(browser, rules)
                self.assertEqual(code, 1)
                self.assertEqual(output.split("\t")[0], "ignora")

    def test_prefixes_choose_the_field(self):
        code, output = self._match("Big Walk | dolphin", "title:^Big Walk$\n")
        self.assertEqual(code, 0, output)
        self.assertEqual(output.split("\t")[2], "title:^Big Walk$")
        # `exe:` é o nome que as mesmas regras usam no Windows; aqui vale a classe.
        self.assertEqual(self._match("Counter-Strike 2 | steam_app_730",
                                     "exe:^steam_app_[0-9]+$\n")[0], 0)
        self.assertEqual(self._match("steam_app_730 | dolphin",
                                     "class:^steam_app_[0-9]+$\n")[0], 1)

    def test_disabled_recorder_never_matches(self):
        code, output = self._match("osu! | osu!", "osu!\n", enabled=False)
        self.assertEqual(code, 1)
        self.assertEqual(output.split("\t")[0], "desativado")


#: Dublê do ``gpu-screen-recorder``. Em Python de propósito: o laço inicia o
#: gravador em segundo plano, e um shell não-interativo entrega SIGINT/SIGQUIT
#: já ignorados a um job assíncrono — um ``trap ... INT`` num dublê em bash nem
#: chegaria a ser instalado. O gsr de verdade é C e registra o próprio tratador,
#: que é o que este arquivo reproduz.
_GSR_STUB = """#!/usr/bin/env python3
import os, pathlib, signal, sys, time

args = sys.argv[1:]
with pathlib.Path(os.environ["GSR_LOG"]).open("a") as handle:
    handle.write(" ".join(args) + "\\n")
output = replay = recording_dir = ""
index = 0
while index < len(args):
    if args[index] == "-o":
        output = args[index + 1]; index += 2
    elif args[index] == "-r":
        replay = args[index + 1]; index += 2
    elif args[index] == "-ro":
        recording_dir = args[index + 1]; index += 2
    else:
        index += 1
# Mesmo contrato do gsr de verdade: em replay o -o é o diretório de saída, e
# sem ele o gravador recusa e sai na hora.
if replay and not output:
    sys.stderr.write("gsr error: Option -o is required when using option -r\\n")
    sys.exit(1)
saved = 0
recording = False

def video(destination, seconds):
    # Um mp4 de verdade, curto: e o que permite conferir a emenda depois.
    import subprocess
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-f", "lavfi", "-i",
                    f"testsrc=duration={seconds}:size=320x240:rate=10",
                    "-pix_fmt", "yuv420p", str(destination)], check=False)

def save(*_):
    global saved
    saved += 1
    video(pathlib.Path(output, f"Replay_{saved}.mp4"), 3)

def toggle(*_):
    # SIGRTMIN: liga e desliga a gravacao normal durante o replay.
    global recording
    recording = not recording
    if not recording:
        video(pathlib.Path(recording_dir, f"Gravacao_{saved}.mp4"), 2)

signal.signal(signal.SIGINT, lambda *_: sys.exit(0))
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
if replay:
    signal.signal(signal.SIGUSR1, save)
    signal.signal(signal.SIGRTMIN, toggle)
else:
    pathlib.Path(output).write_text("video")
while True:
    time.sleep(0.2)
"""

#: Dublê do ``kdotool`` com uma mesa de janelas, não só a ativa. O laço
#: pergunta pelas duas coisas — quem está em foco e se a janela que abriu a
#: sessão ainda existe — e um dublê que só conhecesse a ativa responderia "o
#: jogo sumiu" toda vez que o foco mudasse.
#:
#: Cada linha do ``WINDOW_FILE`` é uma janela aberta, ``<título> | <classe>``,
#: com ``@<x>,<y>`` opcional para dizer em que monitor ela está e ``*`` na
#: frente para marcar a que está em foco (sem marca nenhuma, é a primeira). A
#: linha ``VAZIO`` reproduz a leitura em branco que o KWin às vezes devolve,
#: sem fechar janela nenhuma. O id de uma janela é a classe dela, para que
#: continue sendo a mesma janela quando o foco muda ou outra some da lista.
_KDOTOOL_STUB = """#!/usr/bin/env bash
mapfile -t windows < "$WINDOW_FILE"
spec='' pos=''

# Preenche spec/pos com a janela de id $1 ("ativa" para a que está em foco).
janela() {
  local alvo="$1" raw entry active='' first='' found='' marcada='' marcou=false
  for raw in "${windows[@]}"; do
    [[ -z "$raw" ]] && continue
    entry="${raw#\\*}"
    [[ "$raw" == \\** ]] && { marcou=true; marcada="$entry"; }
    [[ "$entry" == VAZIO ]] && continue
    [[ -z "$first" ]] && first="$entry"
    [[ "${entry%%@*}" == *" | $alvo" ]] && found="$entry"
  done
  if [[ "$marcou" == true ]]; then
    [[ "$marcada" == VAZIO ]] || active="$marcada"
  elif [[ "${windows[0]:-}" != VAZIO ]]; then
    active="$first"
  fi
  entry="$found"
  [[ "$alvo" == ativa ]] && entry="$active"
  spec="${entry%%@*}" pos="10,10"
  [[ "$entry" == *@* ]] && pos="${entry##*@}"
  [[ -n "$spec" ]]
}

case "$1" in
  getactivewindow) janela ativa && printf '%s\\n' "${spec##* | }" ;;
  getwindowname) janela "${2:-ativa}" && printf '%s\\n' "${spec% | *}" ;;
  getwindowclassname) janela "${2:-ativa}" && printf '%s\\n' "${spec##* | }" ;;
  getwindowgeometry)
    janela "${2:-ativa}" \\
      && printf 'Window %s\\n  Position: %s\\n  Geometry: 800x600\\n' "$2" "$pos" ;;
  search)
    for raw in "${windows[@]}"; do
      raw="${raw#\\*}"; raw="${raw%%@*}"
      [[ -z "$raw" || "$raw" == VAZIO ]] && continue
      grep -Eiq -- "${@: -1}" <<<"${raw##* | }" && printf '%s\\n' "${raw##* | }"
    done ;;
esac
exit 0
"""

#: Duas telas, como a máquina que motivou a regra: o jogo em tela cheia na
#: primeira e o resto da vida na segunda.
_KSCREEN_STUB = """#!/usr/bin/env bash
printf 'Output: 1 DP-1\\n        enabled\\n        Geometry: 0,0 1920x1080\\n'
printf 'Output: 2 HDMI-A-1\\n        enabled\\n        Geometry: 1920,0 1366x768\\n'
"""


@unittest.skipIf(IS_WINDOWS, "o gravador do Linux é um script bash")
class LinuxCaptureModeTests(unittest.TestCase):
    """O modo da regra vale no Linux, com o gravador de verdade rodando.

    ``[clips]`` era lido só para ser descartado: o laço sempre chamava o
    ``gpu-screen-recorder`` em gravação contínua, e um jogo configurado como
    "somente clipes" gravava a sessão inteira.
    """

    SCRIPT = Path(__file__).resolve().parents[2] / "bin" / "game-video-loop"

    def _fixture(self, directory: Path, config: str, rules: str) -> dict[str, str]:
        stubs = directory / "stubs"
        stubs.mkdir()
        for name, body in (("gpu-screen-recorder", _GSR_STUB), ("kdotool", _KDOTOOL_STUB),
                           ("kscreen-doctor", _KSCREEN_STUB)):
            stub = stubs / name
            stub.write_text(body, encoding="utf-8")
            stub.chmod(0o755)
        config_dir = directory / "config" / "captura-dia"
        config_dir.mkdir(parents=True)
        (config_dir / "video.conf").write_text(config, encoding="utf-8")
        (config_dir / "video-apps.txt").write_text(rules, encoding="utf-8")
        (config_dir / "storage.conf").write_text(f"STORAGE_ROOT='{directory}/media'\n", encoding="utf-8")
        (directory / "window.txt").write_text("osu! | osu!\n", encoding="utf-8")
        (directory / "run").mkdir()
        return {
            **os.environ, "HOME": str(directory), "XDG_CONFIG_HOME": str(directory / "config"),
            "XDG_RUNTIME_DIR": str(directory / "run"), "DISPLAY": ":0",
            "GSR_LOG": str(directory / "gsr.log"), "WINDOW_FILE": str(directory / "window.txt"),
            "PATH": f"{stubs}:{os.environ['PATH']}",
        }

    @staticmethod
    def _wait_for(predicate, timeout: float = 15.0):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            value = predicate()
            if value:
                return value
            time.sleep(0.1)
        return None

    def _run_loop(self, directory: Path, env: dict[str, str], capture_stderr: bool = False):
        env.pop("WAYLAND_DISPLAY", None)
        return subprocess.Popen(
            ["bash", str(self.SCRIPT)], env=env, stdout=subprocess.DEVNULL, text=True,
            stderr=subprocess.PIPE if capture_stderr else subprocess.DEVNULL)

    def test_lumini_records_without_background_capture_units(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            env = self._fixture(directory,
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=clips\nPAUSE_OTHER_CAPTURES=true\n",
                "[clips] osu!\n")
            systemctl = directory / "stubs" / "systemctl"
            systemctl.write_text("#!/usr/bin/env bash\n"
                "case \"$2\" in\n"
                "  is-active) exit 4 ;;\n"
                "  stop) echo 'Unit captura-dia-audio.service not loaded.' >&2; exit 5 ;;\n"
                "esac\nexit 0\n")
            systemctl.chmod(0o755)
            loop = self._run_loop(directory, env, capture_stderr=True)
            try:
                log = directory / "gsr.log"
                self._wait_for(lambda: log.exists() or loop.poll() is not None)
                started = log.exists()
            finally:
                if loop.poll() is None: loop.terminate()
                error = loop.communicate(timeout=15)[1]
            self.assertTrue(started, f"Lumini não chegou ao gravador: {error}")

    def test_audio_buses_are_ensured_before_the_recorder_starts(self):
        """O gravador de jogo não pode depender da captura de áudio estar de pé.

        Os buses nascem no ``ExecStartPre`` da captura de áudio. Com ela pausada
        eles não existem depois do boot, o gsr recusa as fontes
        ("is not a valid audio device") e morre antes do primeiro quadro.
        """
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            env = self._fixture(
                directory,
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=clips\nVIDEO_REPLAY_SECONDS=30\n"
                "PAUSE_OTHER_CAPTURES=false\nVIDEO_FOCUS_GRACE_SECONDS=0\n",
                "[clips] osu!\n")
            bus_log = directory / "audio-bus.log"
            bus = directory / "stubs" / "audio-bus.sh"
            bus.write_text(f'#!/usr/bin/env bash\nprintf "%s\\n" "$1" >> {bus_log}\n'
                           '[[ "$1" == watch ]] && sleep 60\nexit 0\n', encoding="utf-8")
            bus.chmod(0o755)
            env["CAPTURA_DIA_AUDIO_BUS"] = str(bus)

            loop = self._run_loop(directory, env)
            try:
                self.assertIsNotNone(
                    self._wait_for(lambda: (directory / "gsr.log").is_file()),
                    "o gravador não foi iniciado")
                calls = bus_log.read_text(encoding="utf-8").split()
            finally:
                loop.terminate()
                loop.wait(timeout=15)

        self.assertIn("ensure", calls)

    def test_a_recorder_that_fails_to_start_is_not_retried_every_two_seconds(self):
        """Um gravador que morre ao subir não pode virar um laço invisível.

        Era assim que o modo clipes falhava calado: o gsr recusava os
        argumentos, o laço tentava de novo dois segundos depois e a HUD zerava o
        tempo a cada volta, como se estivesse tudo certo.
        """
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            env = self._fixture(
                directory,
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=clips\nVIDEO_REPLAY_SECONDS=30\n"
                "PAUSE_OTHER_CAPTURES=false\nVIDEO_FOCUS_GRACE_SECONDS=0\n",
                "[clips] osu!\n")
            broken = directory / "stubs" / "gpu-screen-recorder"
            broken.write_text('#!/usr/bin/env bash\nprintf \'%s\\n\' "$*" >> "$GSR_LOG"\n'
                              "echo 'gsr error: recusado' >&2\nexit 1\n", encoding="utf-8")
            broken.chmod(0o755)
            log = directory / "gsr.log"

            loop = self._run_loop(directory, env, capture_stderr=True)
            try:
                self.assertIsNotNone(self._wait_for(log.is_file), "o gravador nem chegou a ser chamado")
                time.sleep(4)
                attempts = len(log.read_text(encoding="utf-8").strip().splitlines())
            finally:
                loop.terminate()
                complaint = loop.communicate(timeout=15)[1]

        self.assertEqual(attempts, 1, "o laço reiniciou de imediato o gravador que acabara de falhar")
        self.assertIn("o gravador saiu em", complaint)

    def test_clips_rule_arms_the_replay_buffer_and_the_hotkey_saves_one_clip(self):
        # A janela de replay é curta de propósito: ela é também a espera pela
        # mesclagem, e o clipe só entra no buffer depois que ela fecha.
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            env = self._fixture(
                directory,
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=clips\nVIDEO_REPLAY_SECONDS=3\n"
                "PAUSE_OTHER_CAPTURES=false\nVIDEO_FOCUS_GRACE_SECONDS=0\n",
                "[clips fps=45 geometry=1280x720 source=game] osu!\n")
            buffer_dir = directory / "media" / "video-buffer"
            flag = directory / "run" / "lume-video-active"
            loop = self._run_loop(directory, env)
            try:
                argv = self._wait_for(lambda: (directory / "gsr.log").read_text(encoding="utf-8")
                                      if (directory / "gsr.log").is_file() else "")
                self.assertIsNotNone(argv, "o gravador não foi iniciado")
                # Replay armado com o diretório em `-o`, que é o que o gsr exige
                # com `-r`; e o fps/geometria da regra valendo sobre o global.
                self.assertIn(f"-r 3 -o {directory}/media/.clipes-parciais", argv)
                # `-ro` é outra coisa: a gravação normal *durante* o replay, que
                # só começa quando alguém segura o atalho. Trocar um pelo outro
                # fazia o gravador morrer a cada tentativa.
                self.assertIn(f"-ro {directory}/media/.gravacoes-longas", argv)
                self.assertIn("-f 45 -s 1280x720", argv)
                self.assertEqual(json.loads(flag.read_text(encoding="utf-8"))["mode"], "clips")

                loop.send_signal(signal.SIGUSR1)
                clip = self._wait_for(lambda: next(iter(sorted(buffer_dir.glob("*_DP-1.mp4"))), None))
                self.assertIsNotNone(clip, "o clipe não chegou ao buffer")
                self.assertRegex(clip.name, r"^\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_DP-1\.mp4$")
                window = clip.with_suffix(clip.suffix + ".window").read_text(encoding="utf-8").strip()
                session = clip.with_suffix(clip.suffix + ".session").read_text(encoding="utf-8").splitlines()
                self.assertEqual(window, "osu! | osu!")
                self.assertEqual(session[1], "osu! | osu!")
                state = self._wait_for(lambda: (lambda p: p if p.get("clips") else None)(
                    json.loads(flag.read_text(encoding="utf-8"))))
                self.assertIsNotNone(state, "o clipe salvo não foi publicado para a HUD")
                self.assertEqual(state["last_clip"], clip.name)
                self.assertEqual(state["event"]["kind"], "clip_saved")

                # Sair do jogo encerra a sessão sem deixar sinal de gravação.
                (directory / "window.txt").write_text("Lume | Helium\n", encoding="utf-8")
                self.assertTrue(self._wait_for(lambda: not flag.exists()), "o sinal de atividade ficou para trás")
            finally:
                loop.terminate()
                loop.wait(timeout=15)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "mesclar dois clipes vizinhos usa ffmpeg/ffprobe")
    def test_two_clips_inside_the_same_replay_window_become_a_single_file(self):
        """Clipar duas vezes seguidas descreve um trecho só, não dois.

        Com clipes de um minuto, um segundo atalho meio minuto depois do
        primeiro salvaria de novo tudo o que já estava no arquivo anterior: a
        mesma jogada em dois vídeos, o dobro de disco e o dobro de análise. O
        segundo pedido estende o clipe que ainda espera.
        """
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            env = self._fixture(
                directory,
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=clips\nVIDEO_REPLAY_SECONDS=30\n"
                "PAUSE_OTHER_CAPTURES=false\nVIDEO_FOCUS_GRACE_SECONDS=0\n",
                "[clips] osu!\n")
            buffer_dir = directory / "media" / "video-buffer"
            flag = directory / "run" / "lume-video-active"

            def event(kind):
                return self._wait_for(lambda: (lambda p: p if (p.get("event") or {}).get(
                    "kind") == kind else None)(
                        json.loads(flag.read_text(encoding="utf-8"))))

            loop = self._run_loop(directory, env)
            try:
                self.assertIsNotNone(
                    self._wait_for(lambda: (directory / "gsr.log").is_file()),
                    "o gravador não foi iniciado")

                loop.send_signal(signal.SIGUSR1)
                self.assertIsNotNone(event("clip_saved"), "o primeiro clipe não saiu")
                # O clipe fica fora do buffer enquanto outro atalho puder
                # estendê-lo: publicá-lo já seria publicar metade do trecho.
                self.assertEqual(list(buffer_dir.glob("*.mp4")), [])

                loop.send_signal(signal.SIGUSR1)
                merged = event("clip_merged")
                self.assertIsNotNone(merged, "o segundo atalho não estendeu o clipe")
                self.assertEqual(merged["clips"], 1, "o segundo atalho abriu outro clipe")

                # Sair do jogo fecha a janela: o clipe único vai para o buffer.
                (directory / "window.txt").write_text("Lume | Helium\n", encoding="utf-8")
                clip = self._wait_for(lambda: next(iter(buffer_dir.glob("*_DP-1.mp4")), None))
                self.assertIsNotNone(clip, "o clipe mesclado não chegou ao buffer")
            finally:
                loop.terminate()
                loop.wait(timeout=15)

            self.assertEqual(len(list(buffer_dir.glob("*.mp4"))), 1,
                             "os dois atalhos deixaram dois arquivos")
            # Cada clipe do gravador de teste tem 3s: o mesclado tem o primeiro
            # mais o que o segundo atalho acrescentou, sem repetir o meio.
            duration = float(subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(clip)],
                capture_output=True, text=True, check=True).stdout.strip())
            self.assertGreater(duration, 3.3, "o clipe não cresceu com o segundo atalho")
            self.assertLess(duration, 6.0, "o trecho em comum entrou duas vezes")
            self.assertEqual(clip.with_suffix(clip.suffix + ".window").read_text(
                encoding="utf-8").strip(), "osu! | osu!")

    def test_clips_pedidos_fora_da_janela_seguem_em_arquivos_separados(self):
        """Sem sobreposição não há o que mesclar: são duas jogadas distintas."""
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            # A janela de replay do gravador de teste dura 3s de vídeo; o
            # segundo atalho vem depois disso e não alcança o primeiro clipe.
            env = self._fixture(
                directory,
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=clips\nVIDEO_REPLAY_SECONDS=30\n"
                "PAUSE_OTHER_CAPTURES=false\nVIDEO_FOCUS_GRACE_SECONDS=0\n",
                "[clips] osu!\n")
            buffer_dir = directory / "media" / "video-buffer"
            flag = directory / "run" / "lume-video-active"
            loop = self._run_loop(directory, env)
            try:
                self.assertIsNotNone(
                    self._wait_for(lambda: (directory / "gsr.log").is_file()),
                    "o gravador não foi iniciado")
                loop.send_signal(signal.SIGUSR1)
                self.assertIsNotNone(
                    self._wait_for(lambda: (lambda p: p if p.get("clips") == 1 else None)(
                        json.loads(flag.read_text(encoding="utf-8")))),
                    "o primeiro clipe não saiu")
                time.sleep(4)
                loop.send_signal(signal.SIGUSR1)
                self.assertIsNotNone(
                    self._wait_for(lambda: (lambda p: p if p.get("clips") == 2 else None)(
                        json.loads(flag.read_text(encoding="utf-8")))),
                    "o segundo clipe foi mesclado no primeiro")
                (directory / "window.txt").write_text("Lume | Helium\n", encoding="utf-8")
                self.assertIsNotNone(
                    self._wait_for(lambda: len(list(buffer_dir.glob("*.mp4"))) == 2),
                    "os dois clipes não chegaram ao buffer")
            finally:
                loop.terminate()
                loop.wait(timeout=15)

    @unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                         "a emenda do clipe com a gravação usa ffmpeg/ffprobe")
    def test_holding_the_hotkey_records_the_clip_plus_everything_after(self):
        """Segurar o atalho: "isto vai ser longo, quero tudo".

        O clipe de pré-roll sozinho não serve para uma jogada que ainda vai
        acontecer, e começar a gravar do zero perderia o que levou até ela. As
        duas coisas saem num arquivo só, e o toque volta a ser marcador
        enquanto a gravação longa corre.
        """
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            env = self._fixture(
                directory,
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=clips\nVIDEO_REPLAY_SECONDS=30\n"
                "PAUSE_OTHER_CAPTURES=false\nVIDEO_FOCUS_GRACE_SECONDS=0\n",
                "[clips] osu!\n")
            buffer_dir = directory / "media" / "video-buffer"
            flag = directory / "run" / "lume-video-active"
            loop = self._run_loop(directory, env)
            try:
                self.assertIsNotNone(
                    self._wait_for(lambda: (directory / "gsr.log").is_file()),
                    "o gravador não foi iniciado")

                loop.send_signal(signal.SIGUSR2)
                state = self._wait_for(lambda: (lambda p: p if p.get("long_recording") else None)(
                    json.loads(flag.read_text(encoding="utf-8"))))
                self.assertIsNotNone(state, "a gravação longa não foi publicada para a HUD")
                self.assertGreater(state["long_started_at"], 0)

                # Durante a gravação longa o toque não salva outro clipe: marca.
                loop.send_signal(signal.SIGUSR1)
                marked = self._wait_for(lambda: (lambda p: p if p.get("markers") else None)(
                    json.loads(flag.read_text(encoding="utf-8"))))
                self.assertIsNotNone(marked, "o marcador da gravação longa não saiu")
                self.assertEqual(marked["event"]["kind"], "marker")

                loop.send_signal(signal.SIGUSR2)
                final = self._wait_for(lambda: next(iter(buffer_dir.glob("*_DP-1.mp4")), None))
                self.assertIsNotNone(final, "a gravação longa não chegou ao buffer")
                done = self._wait_for(lambda: (lambda p: p if p.get("event", {}).get("kind") == "long_saved" else None)(
                    json.loads(flag.read_text(encoding="utf-8"))))
                self.assertIsNotNone(done, "o desfecho da gravação longa não foi anunciado")
                self.assertFalse(done["long_recording"])
            finally:
                loop.terminate()
                loop.wait(timeout=15)

            # Um arquivo só, com os dois pedaços dentro: 3s de pré-roll + 2s
            # gravados.
            self.assertEqual(len(list(buffer_dir.glob("*.mp4"))), 1)
            duration = float(subprocess.run(
                ["ffprobe", "-v", "error", "-show_entries", "format=duration",
                 "-of", "csv=p=0", str(final)],
                capture_output=True, text=True, check=True).stdout.strip())
            self.assertGreater(duration, 4.0, "a gravação saiu sem o pré-roll emendado")
            self.assertEqual(final.with_suffix(final.suffix + ".window").read_text(
                encoding="utf-8").strip(), "osu! | osu!")
            # O marcador foi anotado durante a gravação, mas o arquivo começa
            # antes dela: sem o deslocamento do pré-roll ele apontaria cedo.
            offsets = [int(line) for line in final.with_suffix(
                final.suffix + ".markers").read_text(encoding="utf-8").split()]
            self.assertTrue(offsets and offsets[0] >= 3,
                            f"marcador sem o pré-roll somado: {offsets}")

    def test_session_time_is_counted_even_without_a_single_clip(self):
        """O tempo de jogo é um fato à parte do vídeo, igual ao gravador do Windows.

        Em modo clipes, sem apertar o atalho, nada vai para o disco — e mesmo
        assim o dia precisa saber que o jogo esteve aberto e por quanto tempo.
        """
        import sqlite3

        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            env = self._fixture(
                directory,
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=clips\nVIDEO_REPLAY_SECONDS=30\n"
                "PAUSE_OTHER_CAPTURES=false\nVIDEO_FOCUS_GRACE_SECONDS=0\n",
                "[clips] osu!\n")
            database_path = directory / "media" / "lume.sqlite3"
            buffer_dir = directory / "media" / "video-buffer"

            def session_row():
                if not database_path.is_file():
                    return None
                with sqlite3.connect(database_path) as db:
                    db.row_factory = sqlite3.Row
                    return db.execute(
                        "SELECT app,capture_mode,ended_at,duration_seconds FROM game_activity_sessions"
                    ).fetchone()

            loop = self._run_loop(directory, env)
            try:
                self.assertIsNotNone(
                    self._wait_for(lambda: (directory / "gsr.log").is_file()),
                    "o gravador não foi iniciado")
                self.assertIsNotNone(self._wait_for(session_row), "a sessão não foi contada")
                # Sair do jogo fecha a contagem, ainda que nenhum clipe exista.
                (directory / "window.txt").write_text("Lume | Helium\n", encoding="utf-8")
                closed = self._wait_for(lambda: (lambda row: row if row and row["ended_at"] else None)(session_row()))
            finally:
                loop.terminate()
                loop.wait(timeout=15)

            self.assertIsNotNone(closed, "a sessão ficou aberta depois do jogo sair")
            self.assertEqual(closed["app"], "osu!")
            self.assertEqual(closed["capture_mode"], "clips")
            self.assertGreaterEqual(closed["duration_seconds"], 0)
            self.assertEqual(list(buffer_dir.glob("*.mp4")), [])

    def test_continuous_rule_still_writes_a_segment_and_takes_markers(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            env = self._fixture(
                directory,
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=continuous\nVIDEO_SEGMENT_SECONDS=0\n"
                "PAUSE_OTHER_CAPTURES=false\nVIDEO_FOCUS_GRACE_SECONDS=0\n",
                "[continuous fps=60 geometry=1920x1080 source=game] osu!\n")
            buffer_dir = directory / "media" / "video-buffer"
            flag = directory / "run" / "lume-video-active"
            loop = self._run_loop(directory, env)
            try:
                partial = self._wait_for(lambda: next(iter(buffer_dir.glob("*.partial.mp4")), None))
                self.assertIsNotNone(partial, "nenhum segmento foi aberto")
                loop.send_signal(signal.SIGUSR1)
                # O marcador confirma na hora: um `sleep` comum seguraria o sinal
                # até o fim da volta de dois segundos.
                state = self._wait_for(lambda: (lambda p: p if p.get("markers") else None)(
                    json.loads(flag.read_text(encoding="utf-8"))), timeout=1.5)
                self.assertIsNotNone(state, "o marcador não foi confirmado a tempo")
                self.assertEqual(state["mode"], "continuous")
                self.assertEqual(state["event"]["kind"], "marker")

                (directory / "window.txt").write_text("Lume | Helium\n", encoding="utf-8")
                final = self._wait_for(lambda: next(iter(buffer_dir.glob("*_DP-1.mp4")), None))
                self.assertIsNotNone(final, "o segmento não foi finalizado")
                self.assertEqual(final.with_suffix(final.suffix + ".markers").read_text(
                    encoding="utf-8").strip().count("\n"), 0)
            finally:
                loop.terminate()
                loop.wait(timeout=15)


#: Dublê do ``pw-link``, com as duas interfaces que o de verdade tem: sem
#: ``-I`` ele lista só nomes, com ``-I`` lista id e nome. E, ao ligar por
#: nome, expande o nome para todas as portas que casam — abortando com
#: "Arquivo existe" no primeiro par que já existe, sem tentar os seguintes.
#: São esses dois detalhes, juntos, que apagavam o som do jogo: o grafo tem
#: vários nós com o mesmo nome, e um par antigo já ligado barrava o resto.
#: O ``LINK_LOG`` guarda o que foi efetivamente ligado.
_PW_LINK_STUB = """#!/usr/bin/env bash
saidas='11 jogo:output_FL
12 jogo:output_FR
21 jogo:output_FL
22 jogo:output_FR
31 WEBRTC VoiceEngine:output_FL
41 output.loopback-1:output_FL'
entradas='90 RecordBus:playback_FL
91 RecordBus:playback_FR
92 DiscordBus:playback_MONO'

com_id=false modo=lista
argumentos=()
for arg in "$@"; do
  case "$arg" in
    -I|--id) com_id=true ;;
    -o|--output) modo=saidas ;;
    -i|--input) modo=entradas ;;
    -l|--links) modo=links ;;
    -d|--disconnect) modo=desligar ;;
    -*) ;;
    *) argumentos+=("$arg") ;;
  esac
done

listar() {
  local tabela="$1"
  if [[ "$com_id" == true ]]; then
    printf '%s\\n' "$tabela" | sed 's/^/  /'
  else
    printf '%s\\n' "$tabela" | cut -d' ' -f2-
  fi
}

case "$modo" in
  saidas) listar "$saidas"; exit 0 ;;
  entradas) listar "$entradas"; exit 0 ;;
  links|desligar) exit 0 ;;
esac
[[ ${#argumentos[@]} -eq 2 ]] || exit 0

# Um argumento é um id ou o nome de uma porta; o nome pode casar com várias.
resolver() {
  local alvo="$1" tabela="$2" id nome
  while read -r id nome; do
    [[ "$alvo" == "$id" || "$alvo" == "$nome" ]] && printf '%s\\n' "$id"
  done <<< "$tabela"
}

while read -r origem; do
  [[ -n "$origem" ]] || continue
  while read -r destino; do
    [[ -n "$destino" ]] || continue
    if [[ "$origem" == 11 && "$destino" == 90 ]]; then
      # O par que já existia. O pw-link de verdade desiste aqui.
      echo "failed to link ports: Arquivo existe" >&2
      exit 255
    fi
    printf '%s %s\\n' "$origem" "$destino" >> "$LINK_LOG"
  done < <(resolver "${argumentos[1]}" "$entradas")
done < <(resolver "${argumentos[0]}" "$saidas")
"""

#: Dublê do ``pactl``: um jogo com dois streams tocando no fone, mais o
#: Discord e um loopback que não devem entrar na faixa de sistema.
_PACTL_STUB = """#!/usr/bin/env bash
case "$1 $2 $3" in
  "info  "|"info ") exit 0 ;;
  "list short sinks") printf '7\\tRecordBus\\tPipeWire\\n8\\tDiscordBus\\tPipeWire\\n9\\tMicBus\\tPipeWire\\n'; exit 0 ;;
esac
if [[ "$1 $2" == "list sink-inputs" ]]; then
  cat <<'FIM'
Sink Input #1
	Sink: 68
		node.name = "jogo"
Sink Input #2
	Sink: 68
		node.name = "jogo"
Sink Input #3
	Sink: 68
		node.name = "WEBRTC VoiceEngine"
Sink Input #4
	Sink: 68
		node.name = "output.loopback-1"
FIM
fi
exit 0
"""


@unittest.skipIf(IS_WINDOWS, "os buses de áudio do Linux são um script bash")
class LinuxAudioTapTests(unittest.TestCase):
    """Um app com vários streams tem de entrar inteiro na faixa de sistema.

    O ``pw-link`` liga portas por nome, e nome não é identidade: o Sea of
    Thieves abre quatro nós chamados ``microsoft.seaofthieves``. Pior, ao
    encontrar um par que já existe ele desiste ali sem tentar os seguintes.
    Com um stream antigo já ligado, nenhum dos novos entrava — o som do jogo
    sumia da HUD e da gravação enquanto o navegador continuava saindo.
    """

    SCRIPT = Path(__file__).resolve().parents[2] / "bin" / "audio-bus.sh"

    def _tap(self, directory: Path) -> list[str]:
        stubs = directory / "stubs"
        stubs.mkdir()
        for name, body in (("pw-link", _PW_LINK_STUB), ("pactl", _PACTL_STUB)):
            stub = stubs / name
            stub.write_text(body, encoding="utf-8")
            stub.chmod(0o755)
        log = directory / "links.log"
        result = subprocess.run(
            ["bash", str(self.SCRIPT), "tap"], capture_output=True, text=True, timeout=30,
            env={**os.environ, "PATH": f"{stubs}:{os.environ['PATH']}",
                 "LINK_LOG": str(log), "HOME": str(directory)})
        self.assertEqual(result.returncode, 0, result.stderr)
        return log.read_text(encoding="utf-8").split("\n") if log.is_file() else []

    def test_every_stream_of_the_same_app_reaches_the_record_bus(self):
        with tempfile.TemporaryDirectory() as raw:
            links = self._tap(Path(raw))

        # O segundo nó do jogo é o que faltava: ele vem depois do par que já
        # existia, exatamente onde o pw-link desistia.
        self.assertIn("21 90", links, "o segundo stream do jogo ficou fora da faixa")
        self.assertIn("22 91", links, "o segundo stream do jogo ficou fora da faixa")
        self.assertIn("12 91", links, "o primeiro stream do jogo perdeu o canal direito")

    def test_discord_and_loopbacks_stay_out_of_the_system_track(self):
        """c1 e c2 não podem carregar a mesma voz, nem o mesmo som duas vezes."""
        with tempfile.TemporaryDirectory() as raw:
            links = self._tap(Path(raw))

        self.assertNotIn("31 90", links, "o Discord entrou na faixa de sistema")
        self.assertNotIn("41 90", links, "um loopback entrou na faixa de sistema")
        # O Discord continua indo para o bus dele, e por id.
        self.assertIn("31 92", links)


@unittest.skipIf(IS_WINDOWS, "o gravador do Linux é um script bash")
class LinuxFocusVerdictTests(LinuxCaptureModeTests):
    """Sair do jogo é uma coisa; o KWin mudar de ideia por um segundo é outra.

    O laço perguntava só "a janela ativa casa com uma regra?" e tratava
    qualquer outra resposta como saída. Três situações comuns caíam aí sem
    ninguém ter largado o jogo: o ``kdotool`` devolvendo vazio (1,3% das
    leituras numa amostragem de 4 min com o jogo em primeiro plano), o
    ``plasmashell`` segurando a ativação depois de um clique no painel ou de um
    OSD de volume (27 s seguidos, na mesma amostragem) e — o caso que mais
    dói — clicar no navegador do segundo monitor, com o jogo inteiro ainda na
    tela que está sendo gravada.

    Cada um desses fazia a HUD anunciar "Fora do jogo · para em Ns" e, se
    durasse a folga inteira, levava junto o buffer de clipes da partida.
    """

    def _state(self, directory: Path) -> dict:
        flag = directory / "run" / "lume-video-active"
        if not flag.is_file():
            return {}
        try:
            return json.loads(flag.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    #: A janela do jogo continua aberta em todos estes casos — é justamente a
    #: diferença entre "o foco foi para outro lugar" e "o jogo foi embora".
    GAME = "osu! | osu!"

    def _look_at(self, directory: Path, window: str) -> None:
        """Move o foco para ``window``, com o jogo continuando aberto atrás."""
        (directory / "window.txt").write_text(
            f"{self.GAME}\n*{window}\n", encoding="utf-8")

    def test_what_does_not_cover_the_game_does_not_end_the_session(self):
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            env = self._fixture(
                directory,
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=clips\nVIDEO_REPLAY_SECONDS=30\n"
                "PAUSE_OTHER_CAPTURES=false\nVIDEO_FOCUS_GRACE_SECONDS=30\n",
                "[clips] osu!\n")
            loop = self._run_loop(directory, env)
            try:
                started = self._wait_for(lambda: self._state(directory).get("started_at"))
                self.assertIsNotNone(started, "a sessão não começou")
                for label, window in (
                    ("leitura em branco", "VAZIO"),
                    ("painel do Plasma", "plasmashell | org.kde.plasmashell@10,10"),
                    ("navegador no segundo monitor", "Lume | Helium@1930,10"),
                ):
                    with self.subTest(situacao=label):
                        self._look_at(directory, window)
                        time.sleep(4.5)
                        state = self._state(directory)
                        self.assertEqual(state.get("started_at"), started,
                                         "a sessão foi reiniciada")
                        self.assertIsNone(state.get("focus_grace_deadline"),
                                          "a contagem de saída começou à toa")
            finally:
                loop.terminate()
                loop.wait(timeout=15)

    def test_closing_the_game_ends_the_session_even_with_the_desktop_focused(self):
        """O outro lado de segurar a sessão: o jogo fechar tem de acabar com ela.

        Fechar um jogo em tela cheia costuma devolver o foco para a área de
        trabalho — que é justamente uma das janelas que o laço aprendeu a
        ignorar. Sem perguntar se a janela do jogo ainda existe, "segura"
        viraria "grava a área de trabalho até o disco encher".
        """
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            env = self._fixture(
                directory,
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=clips\nVIDEO_REPLAY_SECONDS=30\n"
                "PAUSE_OTHER_CAPTURES=false\nVIDEO_FOCUS_GRACE_SECONDS=4\n",
                "[clips] osu!\n")
            loop = self._run_loop(directory, env, capture_stderr=True)
            try:
                self.assertIsNotNone(
                    self._wait_for(lambda: self._state(directory).get("started_at")),
                    "a sessão não começou")
                # Só a área de trabalho: o jogo não está mais na lista.
                (directory / "window.txt").write_text(
                    "plasmashell | org.kde.plasmashell@10,10\n", encoding="utf-8")
                self.assertIsNotNone(
                    self._wait_for(
                        lambda: not (directory / "run" / "lume-video-active").exists(),
                        timeout=15),
                    "a sessão sobreviveu ao jogo que fechou")
            finally:
                loop.terminate()
                complaint = loop.communicate(timeout=15)[1]

        self.assertIn("a janela do jogo sumiu", complaint)

    def test_another_window_over_the_recorded_monitor_still_ends_the_session(self):
        """A correção não pode virar "grava para sempre".

        Quem abre o navegador por cima do jogo, no monitor que está sendo
        gravado, continua sendo gravado — e é justamente o que a folga existe
        para interromper.
        """
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            env = self._fixture(
                directory,
                "VIDEO_ENABLED=true\nVIDEO_CAPTURE_MODE=clips\nVIDEO_REPLAY_SECONDS=30\n"
                "PAUSE_OTHER_CAPTURES=false\nVIDEO_FOCUS_GRACE_SECONDS=4\n",
                "[clips] osu!\n")
            loop = self._run_loop(directory, env, capture_stderr=True)
            try:
                self.assertIsNotNone(
                    self._wait_for(lambda: self._state(directory).get("started_at")),
                    "a sessão não começou")
                self._look_at(directory, "Lume | Helium@10,10")
                counting = self._wait_for(
                    lambda: self._state(directory).get("focus_grace_deadline"), timeout=8)
                self.assertIsNotNone(counting, "a contagem de saída não começou")
                self.assertIsNotNone(
                    self._wait_for(
                        lambda: not (directory / "run" / "lume-video-active").exists(),
                        timeout=15),
                    "a sessão não encerrou depois da folga")
            finally:
                loop.terminate()
                complaint = loop.communicate(timeout=15)[1]

        self.assertIn("fora do jogo", complaint)


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

    def test_long_recording_says_so_instead_of_clips_armed(self):
        """Segurou o atalho: já não é "armado", é gravando de verdade."""
        from app.capture.hudstate import evaluate

        status = evaluate(self._recording(recording=True, buffering=False,
                                          long_recording=True,
                                          long_elapsed_seconds=42.0))
        self.assertEqual(status.headline, "Gravando tudo")
        self.assertEqual(status.alerts, [])

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

    def test_alt_tab_countdown_is_a_visible_warning(self):
        from app.capture.hudstate import evaluate

        status = evaluate(self._recording(focus_grace_remaining=12.2))
        self.assertEqual(status.level, "warn")
        self.assertEqual(status.headline, "Fora do jogo · para em 13s")
        self.assertIn("fora-do-jogo", {alert.key for alert in status.alerts})

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


class HudDisplayModeTests(unittest.TestCase):
    def _hud(self):
        from app.capture.hud import Hud

        return Hud(SimpleNamespace(sound=False), demo=lambda: None)

    def test_hotkey_cycles_compact_expanded_hidden(self):
        hud = self._hud()
        self.assertEqual(hud.display_mode, "compact")
        hud.toggle()
        self.assertEqual(hud.display_mode, "expanded")
        hud.toggle()
        self.assertEqual(hud.display_mode, "hidden")
        hud.toggle()
        self.assertEqual(hud.display_mode, "compact")

    def test_hidden_mode_only_surfaces_alerts_and_events(self):
        from app.capture.hudstate import Alert, HudSnapshot, HudStatus

        hud = self._hud()
        hud.display_mode = "hidden"
        snapshot = HudSnapshot(recording=True)
        healthy = HudStatus("ok", "Gravando")
        warning = HudStatus("warn", "Gravando", [Alert("mic", "warn", "Microfone")])
        event = ("marker", "Marcador", SimpleNamespace())

        self.assertFalse(hud._should_show(snapshot, healthy, None))
        self.assertTrue(hud._should_show(snapshot, warning, None))
        self.assertTrue(hud._should_show(snapshot, healthy, event))
        self.assertTrue(hud._should_expand(warning))

    def test_compact_mode_stays_compact_without_an_alert(self):
        from app.capture.hudstate import HudStatus

        hud = self._hud()
        self.assertFalse(hud._should_expand(HudStatus("ok", "Clipes armados")))

    def test_compact_mode_expands_only_while_an_alert_exists(self):
        from app.capture.hudstate import Alert, HudStatus

        hud = self._hud()
        warning = HudStatus("warn", "Microfone sem sinal",
                            [Alert("mic", "warn", "Microfone sem sinal")])

        self.assertTrue(hud._should_expand(warning))
        self.assertFalse(hud._should_expand(HudStatus("ok", "Clipes armados")))


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
        loop.clips_saved = 0
        loop.last_clip_name = ""
        loop.long_recording = False
        loop.long_started_at = 0.0
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

    def test_focus_loss_publishes_a_deadline_and_focus_cancels_it(self):
        from app.capture.winvideo import VideoLoop

        loop = object.__new__(VideoLoop)
        loop.settings = SimpleNamespace(focus_grace=20)
        loop.focus_grace_deadline = 0.0
        with unittest.mock.patch("app.capture.winvideo.time.monotonic", side_effect=[100.0, 105.0]), \
             unittest.mock.patch("app.capture.winvideo.time.time", return_value=1_000.0):
            lost_at, expired = loop._update_focus_grace("fora", -1.0)
            self.assertFalse(expired)
            self.assertEqual(loop.focus_grace_deadline, 1020.0)
            _lost_at, expired = loop._update_focus_grace("fora", lost_at)
            self.assertFalse(expired)
        reset_at, expired = loop._update_focus_grace("jogo", lost_at)
        self.assertEqual(reset_at, -1.0)
        self.assertFalse(expired)
        self.assertEqual(loop.focus_grace_deadline, 0.0)

    def test_an_unreadable_foreground_window_neither_starts_nor_advances_the_countdown(self):
        """"Não sei que janela é essa" não é "o usuário saiu do jogo".

        ``GetForegroundWindow`` devolve 0 no meio de um Alt+Tab e em transições
        da área de trabalho, e a barra de tarefas toma o foco sozinha. Contar
        isso como saída anunciava "Fora do jogo" com o jogo na frente e, se
        durasse a folga inteira, encerrava a sessão.
        """
        from app.capture.winvideo import VideoLoop

        loop = object.__new__(VideoLoop)
        loop.settings = SimpleNamespace(focus_grace=20)
        loop.focus_grace_deadline = 0.0

        # Sem contagem em curso, segurar não inventa prazo nenhum.
        with unittest.mock.patch("app.capture.winvideo.time.monotonic", return_value=100.0):
            lost_at, expired = loop._update_focus_grace("na-tela", -1.0)
        self.assertEqual(lost_at, -1.0)
        self.assertFalse(expired)
        self.assertEqual(loop.focus_grace_deadline, 0.0)

        # Com uma saída de verdade em curso, o prazo restante não encolhe
        # enquanto a janela em foco não diz nada — e vence quando ela volta a
        # dizer que o usuário está fora.
        with unittest.mock.patch("app.capture.winvideo.time.monotonic", return_value=100.0), \
             unittest.mock.patch("app.capture.winvideo.time.time", return_value=1_000.0):
            lost_at, _ = loop._update_focus_grace("fora", -1.0)
        with unittest.mock.patch("app.capture.winvideo.time.monotonic", return_value=102.0), \
             unittest.mock.patch("app.capture.winvideo.time.time", return_value=1_002.0):
            held_at, expired = loop._update_focus_grace("na-tela", lost_at)
        self.assertFalse(expired)
        self.assertEqual(held_at, 102.0, "a contagem andou enquanto ninguém sabia da janela")
        self.assertEqual(loop.focus_grace_deadline, 1022.0)
        with unittest.mock.patch("app.capture.winvideo.time.monotonic", return_value=130.0), \
             unittest.mock.patch("app.capture.winvideo.time.time", return_value=1_030.0):
            _held_at, expired = loop._update_focus_grace("fora", held_at)
        self.assertTrue(expired)


class StableAppLabelTests(unittest.TestCase):
    def test_osu_song_title_collapses_to_executable_name(self):
        from app.capture.base import stable_app_label

        self.assertEqual(
            stable_app_label("osu! - dj TAKA - quaver [Reform's Extra] | osu!.exe"),
            "osu!",
        )

    def test_friendly_title_survives_when_it_differs_from_executable(self):
        from app.capture.base import stable_app_label

        self.assertEqual(
            stable_app_label("Counter-Strike 2 | cs2.exe"),
            "Counter-Strike 2",
        )


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
