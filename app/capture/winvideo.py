"""Gravação seletiva de jogos no Windows — porte de ``bin/game-video-loop``.

Mesma lógica do laço do Linux: observa a janela em foco, e quando ela casa com
a lista de apps começa a gravar; para quando o foco sai por tempo suficiente ou
o segmento estoura. A diferença é quem grava — lá é o ``gpu-screen-recorder``,
aqui é a instância dedicada do OBS (ver :mod:`app.capture.obs`), porque o Game
Capture é o caminho de menor custo para o jogo no Windows.

Roda como processo próprio, igual aos outros laços:

    python -m app.capture.winvideo
"""

from __future__ import annotations

import argparse
import ctypes
import json
import re
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

from . import get_backend
from .base import parse_video_app_rule, read_patterns, read_shell_config
from .imagediff import thumbnail
from . import obs
from ..backend.main_paths import CONFIG_DIR, VIDEO_DIR
from ..backend.database import connect, initialize
from ..backend.runtime import video_activity_flag, video_recording_flag

VIDEO_CONFIG = CONFIG_DIR / "video.conf"
VIDEO_APPS = CONFIG_DIR / "video-apps.txt"

#: Intervalo entre checagens de foco, igual ao do laço bash.
POLL_SECONDS = 2.0

#: Abaixo disto a imagem é considerada chapada (nada foi capturado).
MIN_LUMINANCE_SPREAD = 8

_HIDDEN_PROCESS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


class Settings:
    """Instantâneo de ``video.conf`` e da lista de apps."""

    def __init__(self) -> None:
        self._mtimes: tuple[float, float] = (0.0, 0.0)
        self.reload()

    @staticmethod
    def _mtime(path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    def reload(self) -> None:
        values = read_shell_config(VIDEO_CONFIG)
        self.enabled = values.get("VIDEO_ENABLED", "false").lower() == "true"
        self.fps = self._int(values, "VIDEO_FPS", 60)
        self.geometry = values.get("VIDEO_GEOMETRY", "1920x1080")
        codec = values.get("VIDEO_CODEC", "h264").lower()
        self.codec = "hevc" if codec in {"hevc", "h265"} else "h264"
        self.segment_seconds = self._int(values, "VIDEO_SEGMENT_SECONDS", 60, minimum=0)
        self.retention_minutes = self._int(values, "VIDEO_RETENTION_MINUTES", 60)
        self.pause_others = values.get("PAUSE_OTHER_CAPTURES", "true").lower() == "true"
        self.focus_grace = self._int(values, "VIDEO_FOCUS_GRACE_SECONDS", 20, minimum=0)
        self.capture_mode = values.get("VIDEO_CAPTURE_MODE", "continuous").lower()
        if self.capture_mode not in {"continuous", "clips"}:
            self.capture_mode = "continuous"
        self.replay_seconds = self._int(values, "VIDEO_REPLAY_SECONDS", 60)
        self.hotkey = values.get("VIDEO_MARKER_HOTKEY", "F8")
        self.patterns = [p for p in (self._compile(p, self.capture_mode, self.fps, self.geometry) for p in read_patterns(VIDEO_APPS)) if p]
        self._mtimes = (self._mtime(VIDEO_CONFIG), self._mtime(VIDEO_APPS))

    @staticmethod
    def _compile(pattern: str, default_mode: str = "continuous", default_fps: int = 60,
                 default_geometry: str = "1920x1080"):
        source, mode, fps, geometry, capture_source = parse_video_app_rule(
            pattern, default_mode, default_fps, default_geometry)
        field = "exe"
        for prefix in ("exe:", "title:", "class:"):
            if source.lower().startswith(prefix):
                field, source = prefix[:-1], source[len(prefix):].strip()
                break
        if not source:
            log(f"[aviso] regra de app vazia ignorada: {pattern!r}")
            return None
        try:
            return field, re.compile(source, re.IGNORECASE), source, mode, fps, geometry, capture_source
        except re.error:
            log(f"[aviso] expressão inválida ignorada: {pattern!r}")
            return None

    @staticmethod
    def _int(values: dict[str, str], key: str, default: int, minimum: int = 1) -> int:
        try:
            parsed = int(float(values.get(key, default)))
        except (TypeError, ValueError):
            return default
        return parsed if parsed >= minimum else default

    def refresh_if_changed(self) -> bool:
        current = (self._mtime(VIDEO_CONFIG), self._mtime(VIDEO_APPS))
        if current != self._mtimes:
            self.reload()
            return True
        return False

    def matches_details(self, title: str, window_class: str, executable: str) -> bool:
        return self.capture_rule_for_details(title, window_class, executable) is not None

    def capture_mode_for_details(self, title: str, window_class: str, executable: str) -> str | None:
        rule = self.capture_rule_for_details(title, window_class, executable)
        return rule[0] if rule else None

    def capture_rule_for_details(self, title: str, window_class: str,
                                 executable: str) -> tuple[str, int, str, str] | None:
        fields = {"title": title, "class": window_class, "exe": executable}
        for field, regex, _source, mode, fps, geometry, capture_source in self.patterns:
            if regex.search(fields[field] or ""):
                return mode, fps, geometry, capture_source
        return None

    def matches(self, window: str, window_class: str = "") -> bool:
        """Regras sem prefixo procuram somente no executável.

        Assim uma pasta chamada como o jogo, aberta pelo Explorer, não inicia
        uma captura. Título e classe exigem ``title:`` e ``class:`` explícitos.
        """
        title, separator, executable = (window or "").rpartition(" | ")
        if not separator:
            executable, title = window or "", ""
        return self.matches_details(title, window_class, executable)


class MarkerHotkey:
    """Atalho global para marcar um momento durante a gravação.

    No Linux o atalho do KDE manda ``USR1`` para o laço. O Windows não tem
    ``USR1``, então registramos um hotkey global e rodamos a fila de mensagens
    numa thread — é o equivalente mais próximo, e funciona com o jogo em foco.
    """

    _MODIFIERS = {"ALT": 0x1, "CTRL": 0x2, "CONTROL": 0x2, "SHIFT": 0x4, "WIN": 0x8}
    _WM_HOTKEY = 0x0312

    def __init__(self, spec: str, on_press) -> None:
        self.spec = spec
        self.on_press = on_press
        self._thread = None

    @classmethod
    def _parse(cls, spec: str) -> tuple[int, int] | None:
        modifiers = 0
        key = None
        for part in spec.replace("-", "+").split("+"):
            token = part.strip().upper()
            if not token:
                continue
            if token in cls._MODIFIERS:
                modifiers |= cls._MODIFIERS[token]
            else:
                key = token
        if not key:
            return None
        if re.fullmatch(r"F([1-9]|1[0-9]|2[0-4])", key):
            return modifiers, 0x70 + int(key[1:]) - 1
        if len(key) == 1 and (key.isalpha() or key.isdigit()):
            return modifiers, ord(key)
        return None

    def start(self) -> None:
        parsed = self._parse(self.spec)
        if parsed is None:
            log(f"[aviso] atalho de marcador inválido: {self.spec!r}")
            return
        import threading

        self._thread = threading.Thread(target=self._loop, args=parsed,
                                        name="lume-marker-hotkey", daemon=True)
        self._thread.start()

    def _loop(self, modifiers: int, vk: int) -> None:
        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, 1, modifiers, vk):
            log(f"[aviso] não foi possível registrar {self.spec!r} "
                f"(outro programa já usa esse atalho)")
            return
        log(f"[marcador] atalho {self.spec} registrado")

        class MSG(ctypes.Structure):
            _fields_ = [("hwnd", ctypes.c_void_p), ("message", ctypes.c_uint),
                        ("wParam", ctypes.c_void_p), ("lParam", ctypes.c_void_p),
                        ("time", ctypes.c_uint),
                        ("pt_x", ctypes.c_long), ("pt_y", ctypes.c_long)]

        message = MSG()
        try:
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == self._WM_HOTKEY:
                    try:
                        self.on_press()
                    except Exception as exc:  # nunca derrubar a thread do atalho
                        log(f"[marcador] falhou: {exc}")
        finally:
            user32.UnregisterHotKey(None, 1)


def foreground_details() -> tuple[str, str, str]:
    """Título, classe e executável da janela em foco — o que o OBS precisa
    para enganchar exatamente naquele app."""
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return "", "", ""

    length = user32.GetWindowTextLengthW(hwnd)
    title_buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, title_buf, length + 1)

    class_buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, class_buf, 256)

    pid = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    executable = ""
    handle = kernel32.OpenProcess(0x1000, False, pid.value)  # QUERY_LIMITED_INFORMATION
    if handle:
        try:
            size = ctypes.c_uint(260)
            path_buf = ctypes.create_unicode_buffer(size.value)
            if kernel32.QueryFullProcessImageNameW(handle, 0, path_buf, ctypes.byref(size)):
                executable = Path(path_buf.value).name
        finally:
            kernel32.CloseHandle(handle)
    return title_buf.value or "", class_buf.value or "", executable


def looks_blank(video: Path) -> bool:
    """Amostra um quadro e diz se o vídeo saiu chapado (preto/estático).

    É a rede de segurança contra gravar a coisa errada sem perceber: se o Game
    Capture não engatou, o arquivo sai válido mas sem imagem.
    """
    probe = video.with_suffix(video.suffix + ".probe.png")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", "2", "-i", str(video), "-frames:v", "1", str(probe)],
                   check=False, capture_output=True, timeout=60,
                   creationflags=_HIDDEN_PROCESS)
    if not probe.exists():
        return True
    thumb = thumbnail(probe)
    probe.unlink(missing_ok=True)
    if thumb is None:
        return True
    return (max(thumb) - min(thumb)) < MIN_LUMINANCE_SPREAD


class VideoLoop:
    def __init__(self, once: bool = False, max_wait: float | None = None) -> None:
        self.backend = get_backend()
        self.settings = Settings()
        self.once = once
        self.max_wait = max_wait
        self.stopping = False
        self.recording_active = False
        self.recording_started = 0.0
        self.pending_markers: list[float] = []
        self.session_active = False
        self.session_started_at = 0.0
        self.game_session_key = ""
        self._game_session_heartbeat = 0.0
        self.marker_queued_for_start = False
        self._marker_lock = threading.Lock()
        self.clip_buffer_active = False
        self.clip_save_queued = False
        self.clip_session_key = ""
        self.clip_window = ""
        self.active_capture_mode: str | None = None
        self.active_fps: int | None = None
        self.active_geometry: str | None = None
        self.active_capture_source: str | None = None
        self._clip_lock = threading.Lock()
        # Preparar (copiar, configurar, montar a cena) custa segundos; fazer
        # isso a cada gravação atrasaria o início e perderia jogada. Só na
        # primeira vez e quando a configuração muda.
        self._needs_prepare = True
        self._prepared_profile: tuple[int, str, int, str] | None = None
        self.flag = video_recording_flag()
        self.activity_flag = video_activity_flag()

    def stop(self, _signum=None, _frame=None) -> None:
        self.stopping = True

    def _focused_window(self) -> tuple[str, tuple[str, int, str] | None]:
        """Janela atual e resultado das regras usando campos separados."""
        title, window_class, executable = foreground_details()
        window = f"{title} | {executable}" if title or executable else ""
        return window, self.settings.capture_rule_for_details(title, window_class, executable)

    @staticmethod
    def _same_app(first: str, current: str) -> bool:
        first_title, first_separator, first_exe = first.rpartition(" | ")
        current_title, current_separator, current_exe = current.rpartition(" | ")
        if first_separator and current_separator and first_exe and current_exe:
            return first_exe.casefold() == current_exe.casefold()
        return (first_title or first).casefold() == (current_title or current).casefold()

    # --- sinalização para o supervisor -----------------------------------
    @staticmethod
    def _iso_time(timestamp: float) -> str:
        return datetime.fromtimestamp(timestamp).astimezone().isoformat()

    def _begin_game_session(self, session_key: str, window: str, mode: str) -> None:
        started = self._iso_time(self.session_started_at)
        app = window.split(" | ", 1)[0].strip() or window.rsplit(" | ", 1)[-1].strip() or "Jogo"
        self.game_session_key = session_key
        self._game_session_heartbeat = self.session_started_at
        try:
            with connect() as db:
                db.execute(
                    """INSERT INTO game_activity_sessions(
                           session_key,app,window,capture_mode,started_at,last_seen_at,ended_at,duration_seconds)
                       VALUES(?,?,?,?,?,?,NULL,0)
                       ON CONFLICT(session_key) DO UPDATE SET
                         app=excluded.app,window=excluded.window,capture_mode=excluded.capture_mode,
                         started_at=excluded.started_at,last_seen_at=excluded.last_seen_at,
                         ended_at=NULL,duration_seconds=0""",
                    (session_key, app[:200], window[:1000], mode, started, started),
                )
        except sqlite3.Error as exc:
            log(f"[aviso] falha ao iniciar contagem persistente: {exc}")

    def _heartbeat_game_session(self) -> None:
        if not self.game_session_key:
            return
        now = time.time()
        if now - self._game_session_heartbeat < 10:
            return
        with connect() as db:
            db.execute(
                """UPDATE game_activity_sessions
                   SET last_seen_at=?,
                       duration_seconds=MAX(0,(julianday(?)-julianday(started_at))*86400.0)
                   WHERE session_key=? AND ended_at IS NULL""",
                (self._iso_time(now), self._iso_time(now), self.game_session_key),
            )
        self._game_session_heartbeat = now

    def _finish_game_session(self) -> None:
        if not self.game_session_key or not self.session_started_at:
            return
        ended = time.time()
        duration = max(0.0, ended - self.session_started_at)
        try:
            with connect() as db:
                db.execute(
                    """UPDATE game_activity_sessions
                       SET last_seen_at=?,ended_at=?,duration_seconds=? WHERE session_key=?""",
                    (self._iso_time(ended), self._iso_time(ended), duration, self.game_session_key),
                )
            log(f"[tempo] sessão de jogo registrada: {duration / 60:.1f} min")
        except sqlite3.Error as exc:
            log(f"[aviso] falha ao finalizar contagem persistente: {exc}")
        self.game_session_key = ""
        self._game_session_heartbeat = 0.0

    def _suspend_others(self, window: str) -> None:
        try:
            self.activity_flag.parent.mkdir(parents=True, exist_ok=True)
            self.activity_flag.write_text(json.dumps({
                "window": window,
                "started_at": self.session_started_at or time.time(),
                "mode": self.active_capture_mode or self.settings.capture_mode,
            }, ensure_ascii=False), encoding="utf-8")
            if self.settings.pause_others:
                self.flag.write_text(window, encoding="utf-8")
        except OSError:
            pass
        try:
            self._heartbeat_game_session()
        except (OSError, sqlite3.Error) as exc:
            log(f"[aviso] falha ao atualizar tempo da sessão: {exc}")

    def _release_others(self, reason: str = "") -> None:
        existia = self.flag.exists() or self.activity_flag.exists()
        try:
            self.flag.unlink(missing_ok=True)
            self.activity_flag.unlink(missing_ok=True)
        except OSError:
            pass
        if existia:
            log(f"[sinal] liberado ({reason or 'sem motivo informado'})")

    # --- marcadores -------------------------------------------------------
    @staticmethod
    def _confirmation_sound() -> None:
        """Confirma uma ação aceita sem depender da interface estar em foco."""
        if sys.platform != "win32":
            return
        try:
            import winsound
            winsound.Beep(1046, 80)
            winsound.Beep(1318, 110)
        except (ImportError, RuntimeError, OSError):
            pass

    def hotkey_pressed(self) -> None:
        if (self.active_capture_mode or self.settings.capture_mode) == "clips":
            if self.clip_buffer_active:
                self.save_replay_clip()
            elif self.session_active:
                self.clip_save_queued = True
                log("[clipe] F8 recebido durante a preparação; salvamento enfileirado")
            else:
                log("[clipe] ignorado: nenhum jogo monitorado está ativo")
            return
        self.add_marker()

    def add_marker(self) -> None:
        """Anota o instante atual da gravação.

        Os marcadores ficam em memória e só vão para o disco no fim: o nome do
        arquivo definitivo só é conhecido quando o OBS encerra a gravação, e
        perguntar por ele durante a captura não é confiável — logo após o
        ``StartRecord`` a saída ainda nem consta como ativa.
        """
        with self._marker_lock:
            if not self.recording_active:
                if self.session_active:
                    self.marker_queued_for_start = True
                    log("[marcador] recebido durante a transição; será aplicado ao início do próximo clipe")
                    self._confirmation_sound()
                else:
                    log("[marcador] ignorado: nenhuma gravação em andamento")
                return
            offset = max(0.0, time.monotonic() - self.recording_started)
            self.pending_markers.append(offset)
        log(f"[marcador] {offset:.1f}s anotado")
        self._confirmation_sound()

    def _activate_recording(self) -> None:
        with self._marker_lock:
            self.recording_started = time.monotonic()
            self.recording_active = True
            self.pending_markers.clear()
            if self.marker_queued_for_start:
                self.pending_markers.append(0.0)
                self.marker_queued_for_start = False
                log("[marcador] transição aplicada em 0.0s")

    def save_replay_clip(self) -> Path | None:
        """Salva o Replay Buffer atual e vincula o arquivo à sessão do jogo."""
        with self._clip_lock:
            if not self.clip_buffer_active:
                log("[clipe] ignorado: Replay Buffer não está ativo")
                return None
            try:
                previous = str(obs.call("GetLastReplayBufferReplay").get("savedReplayPath") or "")
            except (obs.ObsError, OSError):
                previous = ""
            try:
                obs.call("SaveReplayBuffer")
            except (obs.ObsError, OSError) as exc:
                log(f"[clipe] falha ao salvar Replay Buffer: {exc}")
                return None

            path: Path | None = None
            deadline = time.monotonic() + 15
            while time.monotonic() < deadline:
                try:
                    current = str(obs.call("GetLastReplayBufferReplay").get("savedReplayPath") or "")
                except (obs.ObsError, OSError):
                    current = ""
                candidate = Path(current) if current else None
                if current and current != previous and candidate and candidate.is_file():
                    path = candidate
                    break
                time.sleep(0.15)
            if path is None:
                log("[clipe] o OBS aceitou o F8, mas não informou o arquivo salvo")
                return None

            path.with_suffix(path.suffix + ".window").write_text(self.clip_window, encoding="utf-8")
            path.with_suffix(path.suffix + ".session").write_text(
                f"{self.clip_session_key}\n{self.clip_window}\n", encoding="utf-8")
            self.clip_save_queued = False
            log(f"[clipe] últimos {self.settings.replay_seconds}s salvos em {path.name}")
            self._confirmation_sound()
            return path

    # --- gravação ---------------------------------------------------------
    #: Tempo para o hook do Game Capture injetar antes de valer a pena gravar.
    #: Medido em ~2 s nesta máquina; a folga evita começar o arquivo no escuro.
    HOOK_WARMUP_SECONDS = 4.0

    def _start_recording(self, window: str) -> bool:
        title, window_class, executable = foreground_details()
        fps = self.active_fps or self.settings.fps
        geometry = self.active_geometry or self.settings.geometry
        profile = (fps, geometry, self.settings.replay_seconds, self.settings.codec)
        try:
            if self._needs_prepare or self._prepared_profile != profile:
                obs.prepare(fps=fps, geometry=geometry,
                            retention_minutes=self.settings.retention_minutes,
                            replay_seconds=self.settings.replay_seconds,
                            codec=self.settings.codec)
                self._needs_prepare = False
                self._prepared_profile = profile
            else:
                # Barato quando já está de pé; recupera se o OBS tiver caído.
                obs.launch()
            # Sobra de um encerramento abrupto: o OBS pode ter ficado gravando.
            leftover = obs.stop_recording_if_active()
            if leftover:
                log(f"[aviso] havia uma gravação em aberto; encerrada em {leftover.name}")
            obs.stop_replay_buffer_if_active()
            capture_source = "tela cheia"
            if executable:
                capture_source = obs.target_window(
                    title, window_class, executable,
                    window_capture=self.active_capture_source == "window",
                )
            else:
                obs.any_fullscreen()
            time.sleep(self.HOOK_WARMUP_SECONDS)
            obs.call("StartRecord")
        except (obs.ObsError, OSError) as exc:
            log(f"[erro] não foi possível iniciar a gravação: {exc}")
            self._release_others("falha ao iniciar")
            return False
        self._activate_recording()
        log(f"[gravando] {window}" + (f"  ({capture_source} em {executable})" if executable else ""))
        return True

    def _start_replay_buffer(self, window: str, session_key: str) -> bool:
        title, window_class, executable = foreground_details()
        fps = self.active_fps or self.settings.fps
        geometry = self.active_geometry or self.settings.geometry
        profile = (fps, geometry, self.settings.replay_seconds, self.settings.codec)
        try:
            if self._needs_prepare or self._prepared_profile != profile:
                obs.prepare(fps=fps, geometry=geometry,
                            retention_minutes=self.settings.retention_minutes,
                            replay_seconds=self.settings.replay_seconds,
                            codec=self.settings.codec)
                self._needs_prepare = False
                self._prepared_profile = profile
            else:
                obs.launch()
            obs.stop_recording_if_active()
            obs.stop_replay_buffer_if_active()
            capture_source = "tela cheia"
            if executable:
                capture_source = obs.target_window(
                    title, window_class, executable,
                    window_capture=self.active_capture_source == "window",
                )
            else:
                obs.any_fullscreen()
            time.sleep(self.HOOK_WARMUP_SECONDS)
            obs.call("StartReplayBuffer")
        except (obs.ObsError, OSError) as exc:
            log(f"[erro] não foi possível iniciar o Replay Buffer: {exc}")
            return False
        with self._clip_lock:
            self.clip_session_key = session_key
            self.clip_window = window
            self.clip_buffer_active = True
        log(f"[clipes] buffer de {self.settings.replay_seconds}s ativo para {window}" +
            (f"  ({capture_source} em {executable})" if executable else ""))
        if self.clip_save_queued:
            self.save_replay_clip()
        return True

    def _stop_replay_buffer(self) -> None:
        with self._clip_lock:
            if self.clip_buffer_active:
                try:
                    obs.call("StopReplayBuffer")
                except (obs.ObsError, OSError) as exc:
                    log(f"[aviso] falha ao encerrar Replay Buffer: {exc}")
            self.clip_buffer_active = False
            self.clip_save_queued = False
            self.clip_session_key = ""
            self.clip_window = ""
        log("[clipes] Replay Buffer encerrado")

    def _stop_recording(self, window: str, session_key: str) -> None:
        try:
            result = obs.call("StopRecord")
        except (obs.ObsError, OSError) as exc:
            log(f"[erro] falha ao encerrar a gravação: {exc}")
            self._release_others("falha ao parar")
            with self._marker_lock:
                self.recording_active = False
            return
        with self._marker_lock:
            self.recording_active = False
            markers = list(self.pending_markers)
            self.pending_markers.clear()

        path = Path(result.get("outputPath", ""))
        self._release_others("gravação encerrada")
        if not path.is_file():
            log("[aviso] o OBS não devolveu arquivo")
            return

        size_mb = path.stat().st_size / 1024 / 1024
        path.with_suffix(path.suffix + ".window").write_text(window, encoding="utf-8")
        path.with_suffix(path.suffix + ".session").write_text(
            f"{session_key}\n{window}\n", encoding="utf-8")
        if markers:
            path.with_suffix(path.suffix + ".markers").write_text(
                "".join(f"{offset:.1f}\n" for offset in markers),
                encoding="utf-8")
            log(f"[marcador] {len(markers)} gravado(s) em {path.name}")
        if looks_blank(path):
            log(f"[aviso] {path.name} saiu sem imagem ({size_mb:.1f} MB). "
                f"O jogo pode não estar em tela cheia.")
            path.with_suffix(path.suffix + ".sem-imagem").write_text(
                "A captura não engatou no jogo.\n", encoding="utf-8")
        else:
            log(f"[pronto] {path.name} ({size_mb:.1f} MB)")
        print(path, flush=True)

    def _record_session(self, window: str) -> None:
        """Grava uma sessão lógica, possivelmente dividida em segmentos."""
        session_key = secrets.token_hex(16)
        self.session_started_at = time.time()
        limit = self.settings.segment_seconds
        self.session_active = True
        self._begin_game_session(session_key, window, "continuous")
        try:
            while not self.stopping:
                self._suspend_others(window)
                if not self._start_recording(window):
                    return
                focus_lost_at = -1.0
                session_ended = False
                while not self.stopping:
                    time.sleep(POLL_SECONDS)
                    elapsed = time.monotonic() - self.recording_started
                    if limit and elapsed >= limit:
                        break
                    current, rule = self._focused_window()
                    if rule and rule[0] == "continuous" and self._same_app(window, current):
                        focus_lost_at = -1.0
                    elif focus_lost_at < 0:
                        focus_lost_at = time.monotonic()
                    elif time.monotonic() - focus_lost_at >= self.settings.focus_grace:
                        session_ended = True
                        break
                self._stop_recording(window, session_key)
                if session_ended or self.stopping or not limit:
                    break
                current, rule = self._focused_window()
                if not rule or rule[0] != "continuous" or not self._same_app(window, current):
                    break
        finally:
            self._finish_game_session()
            self.session_started_at = 0.0
            with self._marker_lock:
                self.session_active = False
                if self.marker_queued_for_start:
                    log("[marcador] transição descartada porque a sessão terminou antes do próximo clipe")
                    self.marker_queued_for_start = False

    def _record_clip_session(self, window: str) -> None:
        """Mantém Replay Buffer ativo e salva somente quando F8 for pressionado."""
        session_key = secrets.token_hex(16)
        self.session_started_at = time.time()
        self.session_active = True
        self._begin_game_session(session_key, window, "clips")
        try:
            self._suspend_others(window)
            if not self._start_replay_buffer(window, session_key):
                return
            focus_lost_at = -1.0
            while not self.stopping:
                time.sleep(POLL_SECONDS)
                current, rule = self._focused_window()
                if rule and rule[0] == "clips" and self._same_app(window, current):
                    focus_lost_at = -1.0
                elif focus_lost_at < 0:
                    focus_lost_at = time.monotonic()
                elif time.monotonic() - focus_lost_at >= self.settings.focus_grace:
                    break
        finally:
            self._stop_replay_buffer()
            self._release_others("buffer de clipes encerrado")
            self._finish_game_session()
            self.session_started_at = 0.0
            self.session_active = False
            self.clip_save_queued = False

    def run(self) -> int:
        from .winrecord import _install_stop_handlers

        _install_stop_handlers(self.stop)
        initialize()
        with connect() as db:
            db.execute(
                """UPDATE game_activity_sessions
                   SET ended_at=last_seen_at,
                       duration_seconds=MAX(0,(julianday(last_seen_at)-julianday(started_at))*86400.0)
                   WHERE ended_at IS NULL"""
            )
        self._release_others("limpeza inicial")

        hotkey = MarkerHotkey(self.settings.hotkey, self.hotkey_pressed)
        hotkey.start()

        log(f"[video] apps monitorados: {len(self.settings.patterns)} | "
            f"destino: {VIDEO_DIR}")
        if not self.settings.enabled:
            log("[video] desligado em video.conf; aguardando ser habilitado")

        started = time.monotonic()
        recorded = False
        while not self.stopping:
            if self.settings.refresh_if_changed():
                # fps, resolução e retenção vivem no perfil do OBS.
                self._needs_prepare = True
                log(f"[video] configuração recarregada: "
                    f"{len(self.settings.patterns)} app(s), "
                    f"{'ligado' if self.settings.enabled else 'desligado'}")
            if self.settings.enabled and self.settings.patterns:
                window, capture_rule = self._focused_window()
                if capture_rule:
                    capture_mode, capture_fps, capture_geometry, capture_source = capture_rule
                    self.active_capture_mode = capture_mode
                    self.active_fps = capture_fps
                    self.active_geometry = capture_geometry
                    self.active_capture_source = capture_source
                    try:
                        if capture_mode == "clips":
                            self._record_clip_session(window)
                        else:
                            self._record_session(window)
                        recorded = True
                    finally:
                        self.active_capture_mode = None
                        self.active_fps = None
                        self.active_geometry = None
                        self.active_capture_source = None
            # `--once` grava uma sessão e sai; até um app casar, segue
            # esperando, senão o modo de teste sairia antes de ver qualquer
            # coisa em foco.
            if self.once and recorded:
                break
            if self.max_wait is not None and time.monotonic() - started >= self.max_wait:
                log("[video] tempo de espera esgotado sem nenhum app casar")
                break
            time.sleep(POLL_SECONDS)

        # Encerrar sem fechar a gravação deixaria o OBS gravando sozinho.
        try:
            pendente = obs.stop_recording_if_active()
            if pendente:
                log(f"[saindo] gravação encerrada em {pendente.name}")
            obs.stop_replay_buffer_if_active()
        except (obs.ObsError, OSError):
            pass
        self._release_others("saída do laço")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Gravação seletiva de jogos no Windows, via OBS dedicado.")
    parser.add_argument("--once", action="store_true",
                        help="espera um app casar, grava uma sessão e sai")
    parser.add_argument("--max-wait", type=float, default=None,
                        help="desiste depois de N segundos sem nenhum app em foco")
    parser.add_argument("--prepare", action="store_true",
                        help="só prepara a instância dedicada do OBS e sai")
    parser.add_argument("--diagnostics", action="store_true",
                        help="mostra o estado da instância dedicada e sai")
    args = parser.parse_args(argv)

    if args.diagnostics:
        import json

        print(json.dumps(obs.diagnostics(), ensure_ascii=False, indent=2))
        return 0

    if args.prepare:
        settings = Settings()
        obs.prepare(fps=settings.fps, geometry=settings.geometry,
                    retention_minutes=settings.retention_minutes,
                    replay_seconds=settings.replay_seconds, codec=settings.codec)
        print(f"instância dedicada pronta em {obs.OBS_HOME}")
        return 0

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return VideoLoop(once=args.once, max_wait=args.max_wait).run()


if __name__ == "__main__":
    raise SystemExit(main())
