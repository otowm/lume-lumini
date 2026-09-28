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
from pathlib import Path

from . import gamesession, get_backend
from .base import parse_video_app_rule, read_patterns, read_shell_config
from .imagediff import thumbnail
from .winhotkey import DEFAULT_HOLD_SECONDS, MarkerHotkey
from . import obs
from ..backend.main_paths import CONFIG_DIR, VIDEO_DIR
from ..backend.database import initialize
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
        try:
            hold = float(values.get("VIDEO_HOTKEY_HOLD_SECONDS", DEFAULT_HOLD_SECONDS))
        except (TypeError, ValueError):
            hold = DEFAULT_HOLD_SECONDS
        self.hold_seconds = hold if hold > 0 else DEFAULT_HOLD_SECONDS
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


def media_duration(video: Path) -> float:
    """Duração em segundos, ou 0 quando o ffprobe não souber dizer."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(video)],
        check=False, capture_output=True, text=True, timeout=30,
        creationflags=_HIDDEN_PROCESS)
    try:
        return max(0.0, float(result.stdout.strip()))
    except (TypeError, ValueError):
        return 0.0


# Cópia de todos os streams. Sem ``-map 0`` o ffmpeg fica com uma faixa de
# áudio só, e recortar ou emendar um clipe perderia as faixas isoladas de
# microfone, Discord e sistema que o OBS gravou.
KEEP_ALL_STREAMS = ("-map", "0", "-c", "copy")


def cut_head(source: Path, destination: Path, seconds: float) -> bool:
    """Guarda só os primeiros ``seconds`` do arquivo, copiando os streams.

    Cortar pelo fim é exato com cópia de streams; cortar pelo começo cairia no
    quadro-chave anterior e repetiria segundos já vistos. É por isso que a
    mesclagem de dois clipes recorta o começo do que já existe em vez de
    recortar o começo do que acabou de chegar.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(source), "-t", f"{seconds:.3f}", *KEEP_ALL_STREAMS, str(destination)],
            check=False, capture_output=True, timeout=600,
            creationflags=_HIDDEN_PROCESS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        log(f"[clipe] falha ao recortar: {exc}")
        return False
    return result.returncode == 0 and destination.is_file()


def concat_videos(destination: Path, *parts: Path) -> bool:
    """Emenda os pedaços num arquivo só, copiando os streams.

    Os dois vêm do mesmo OBS, com o mesmo codec e as mesmas faixas, então não há
    o que recodificar — e recodificar uma partida inteira só para juntar dois
    pedaços custaria mais do que a gravação toda.
    """
    listing = destination.with_suffix(destination.suffix + ".concat.txt")
    try:
        listing.write_text(
            "".join(f"file '{part.as_posix()}'\n" for part in parts), encoding="utf-8")
        result = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-f", "concat", "-safe", "0", "-i", str(listing),
             *KEEP_ALL_STREAMS, str(destination)],
            check=False, capture_output=True, timeout=600,
            creationflags=_HIDDEN_PROCESS)
    except (OSError, subprocess.TimeoutExpired) as exc:
        log(f"[longa] falha ao emendar: {exc}")
        return False
    finally:
        listing.unlink(missing_ok=True)
    return result.returncode == 0 and destination.is_file()


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
        self.last_clip_name = ""
        # Dois atalhos dentro da mesma janela de replay descrevem um trecho só:
        # o segundo clipe começa antes do fim do primeiro, e publicar os dois
        # deixaria a mesma jogada em dois arquivos. Enquanto a janela pode
        # receber outro atalho o clipe espera fora do buffer que o Lume observa,
        # e é publicado já mesclado quando ela fecha.
        self.pending_clip: Path | None = None
        self.pending_clip_at = 0.0
        self.clips_saved = 0
        # Gravação longa: no modo clipes, segurar o atalho salva o pré-roll que
        # está no Replay Buffer e deixa o OBS gravando dali em diante, até a
        # próxima segurada. Os dois pedaços saem emendados num arquivo só.
        self.long_recording = False
        self.long_started_at = 0.0
        self.long_started = 0.0
        self.long_clip: Path | None = None
        self.long_markers: list[float] = []
        self.active_window = ""
        self.last_event: dict | None = None
        self.event_seq = 0
        self.active_capture_mode: str | None = None
        self.active_fps: int | None = None
        self.active_geometry: str | None = None
        self.active_capture_source: str | None = None
        self.focus_grace_deadline = 0.0
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

    #: Janelas que não são "o usuário foi fazer outra coisa": a barra de
    #: tarefas, o menu Iniciar, o alternador de tarefas e as notificações tomam
    #: o foco por alguns instantes sozinhas. Contá-las como saída era o que
    #: fazia a HUD anunciar "Fora do jogo" com o jogo na frente — o mesmo
    #: defeito que o laço do Linux tinha com o painel do Plasma.
    SHELL_WINDOW_CLASSES = frozenset({
        "Shell_TrayWnd", "Shell_SecondaryTrayWnd", "Windows.UI.Core.CoreWindow",
        "XamlExplorerHostIslandWindow", "MultitaskingViewFrame",
        "ForegroundStaging", "TaskSwitcherWnd", "TaskSwitcherOverlayWnd",
    })

    def _focus_state(self, window: str, mode: str) -> str:
        """``jogo``, ``na-tela`` ou ``fora`` — a mesma pergunta do laço Linux.

        Três respostas, e não duas, porque "não é o jogo" reunia coisas
        diferentes demais. ``GetForegroundWindow`` devolve 0 no meio de um
        Alt+Tab e durante transições da área de trabalho, e aí ``na-tela``
        significa "não sei": a contagem não começa nem anda. Quem sai do jogo
        de verdade continua caindo em ``fora``.
        """
        title, window_class, executable = foreground_details()
        current = f"{title} | {executable}" if title or executable else ""
        if not current:
            return "na-tela"
        rule = self.settings.capture_rule_for_details(title, window_class, executable)
        if rule and rule[0] == mode and self._same_app(window, current):
            return "jogo"
        if window_class in self.SHELL_WINDOW_CLASSES:
            return "na-tela"
        return "fora"

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
    def _begin_game_session(self, session_key: str, window: str, mode: str) -> None:
        self.game_session_key = session_key
        self._game_session_heartbeat = self.session_started_at
        try:
            gamesession.begin(session_key, window, mode, self.session_started_at)
        except sqlite3.Error as exc:
            log(f"[aviso] falha ao iniciar contagem persistente: {exc}")

    def _heartbeat_game_session(self) -> None:
        if not self.game_session_key:
            return
        now = time.time()
        if now - self._game_session_heartbeat < gamesession.HEARTBEAT_SECONDS:
            return
        gamesession.heartbeat(self.game_session_key, now)
        self._game_session_heartbeat = now

    def _finish_game_session(self) -> None:
        if not self.game_session_key or not self.session_started_at:
            return
        try:
            duration = gamesession.finish(self.game_session_key, self.session_started_at)
            log(f"[tempo] sessão de jogo registrada: {duration / 60:.1f} min")
        except sqlite3.Error as exc:
            log(f"[aviso] falha ao finalizar contagem persistente: {exc}")
        self.game_session_key = ""
        self._game_session_heartbeat = 0.0

    def _publish_activity(self) -> None:
        """Escreve o sinal de atividade lido pela HUD.

        Fica separado de :meth:`_suspend_others` porque tem duas cadências: a
        volta do laço (2 s) e, sempre que algo acontece, imediatamente. Uma
        confirmação de marcador que demorasse até dois segundos para aparecer
        não serviria como confirmação — a pessoa apertaria de novo.
        """
        # O sinal significa "há captura de vídeo em curso": o supervisor suspende
        # áudio e telas enquanto ele existir, e a API o lê como gravação ativa.
        # Escrevê-lo fora de uma sessão — por um F8 solto, por exemplo — pausaria
        # a captura do dia inteiro por engano.
        if not self.session_active:
            return
        try:
            self.activity_flag.parent.mkdir(parents=True, exist_ok=True)
            self.activity_flag.write_text(json.dumps({
                "window": self.active_window,
                "started_at": self.session_started_at or time.time(),
                "mode": self.active_capture_mode or self.settings.capture_mode,
                # A HUD usa a data de modificação deste arquivo como sinal de
                # vida: um sinal parado significa laço morto, não gravação em
                # curso.
                "markers": len(self.pending_markers),
                "clips": self.clips_saved,
                "last_clip": self.last_clip_name,
                "long_recording": self.long_recording,
                "long_started_at": self.long_started_at or None,
                "focus_grace_deadline": getattr(self, "focus_grace_deadline", 0.0) or None,
                "event": self.last_event,
            }, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    def _note_event(self, kind: str, label: str) -> None:
        """Registra um acontecimento pontual e publica na hora.

        A sequência é o que deixa a HUD distinguir *evento novo* de *mesmo
        evento relido*: contagens e nomes de arquivo se repetem (dois
        marcadores seguidos, um clipe salvo duas vezes no mesmo segundo), um
        contador que só cresce não.
        """
        self.event_seq += 1
        self.last_event = {"kind": kind, "label": label,
                           "seq": self.event_seq, "at": time.time()}
        self._publish_activity()

    def _suspend_others(self, window: str) -> None:
        self.active_window = window
        self._publish_activity()
        try:
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

    def _update_focus_grace(self, state: str, focus_lost_at: float) -> tuple[float, bool]:
        """Atualiza o prazo publicado para a HUD e informa se ele venceu."""
        now = time.monotonic()
        if state == "jogo":
            self.focus_grace_deadline = 0.0
            return -1.0, False
        if state == "na-tela":
            # Segura o que estiver valendo: uma contagem já em curso fica onde
            # está, empurrada volta a volta, em vez de correr enquanto o menu
            # Iniciar está aberto.
            if focus_lost_at >= 0:
                focus_lost_at = min(now, focus_lost_at + POLL_SECONDS)
                self.focus_grace_deadline = time.time() + max(
                    0.0, self.settings.focus_grace - (now - focus_lost_at))
            return focus_lost_at, False
        if focus_lost_at < 0:
            focus_lost_at = now
        self.focus_grace_deadline = time.time() + max(
            0.0, self.settings.focus_grace - (now - focus_lost_at))
        return focus_lost_at, now - focus_lost_at >= self.settings.focus_grace

    # --- marcadores -------------------------------------------------------
    #: Cada confirmação tem um desenho melódico próprio, porque quem está
    #: jogando escuta sem olhar: o aceite de sempre sobe uma quinta, a gravação
    #: longa abre com um arpejo subindo e fecha com o mesmo arpejo descendo.
    _SOUNDS = {
        "ok": ((1046, 80), (1318, 110)),
        "long_start": ((784, 70), (1046, 70), (1318, 150)),
        "long_stop": ((1318, 70), (1046, 70), (784, 150)),
    }

    @classmethod
    def _confirmation_sound(cls, variant: str = "ok") -> None:
        """Confirma uma ação aceita sem depender da interface estar em foco."""
        if sys.platform != "win32":
            return
        try:
            import winsound
            for frequency, duration in cls._SOUNDS.get(variant, cls._SOUNDS["ok"]):
                winsound.Beep(frequency, duration)
        except (ImportError, RuntimeError, OSError):
            pass

    def hotkey_pressed(self) -> None:
        # Durante uma gravação longa o toque volta a ser marcador: salvar um
        # clipe do que já está sendo gravado inteiro não diria nada.
        if self.long_recording:
            self.add_marker()
            return
        if (self.active_capture_mode or self.settings.capture_mode) == "clips":
            if self.clip_buffer_active:
                # Salvar leva segundos (o OBS só informa o arquivo depois de
                # gravá-lo), então avisamos antes e confirmamos depois — senão o
                # silêncio no meio pareceria que o atalho não pegou.
                self._note_event("clip_saving", "Salvando clipe…")
                self.save_replay_clip()
            elif self.session_active:
                self.clip_save_queued = True
                self._note_event("clip_queued", "Clipe na fila")
                log("[clipe] F8 recebido durante a preparação; salvamento enfileirado")
            else:
                self._note_event("ignored", "Nenhum jogo monitorado")
                log("[clipe] ignorado: nenhum jogo monitorado está ativo")
            return
        self.add_marker()

    def hotkey_held(self) -> None:
        """Segurar: abre a gravação longa e, na segurada seguinte, a fecha."""
        if (self.active_capture_mode or self.settings.capture_mode) != "clips":
            self._note_event("ignored", "Segurar só vale no modo clipes")
            return
        if self.long_recording:
            self.stop_long_recording()
        elif self.clip_buffer_active:
            self.start_long_recording()
        else:
            self._note_event("ignored", "Nenhum jogo monitorado")
            log("[longa] ignorado: nenhum buffer de clipes ativo")

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
                    self._note_event("marker_queued", "Marcador na próxima cena")
                    self._confirmation_sound()
                else:
                    log("[marcador] ignorado: nenhuma gravação em andamento")
                    self._note_event("ignored", "Nada sendo gravado")
                return
            offset = max(0.0, time.monotonic() - self.recording_started)
            self.pending_markers.append(offset)
            total = len(self.pending_markers)
        log(f"[marcador] {offset:.1f}s anotado")
        self._note_event("marker", f"Marcador {total} · {offset / 60:.0f}:{offset % 60:02.0f}")
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

    # --- gravação longa ---------------------------------------------------
    def start_long_recording(self) -> None:
        """Guarda o pré-roll e começa a gravar em paralelo ao Replay Buffer."""
        # A gravação longa tem pré-roll próprio: o clipe que esperava não é
        # estendido por ela, e ficar pendente só atrasaria a publicação dele.
        self.flush_pending_clip()
        self.long_started_at = time.time()
        self.long_started = time.monotonic()
        self.long_markers = []
        self.long_clip = None
        self._note_event("long_started", "Gravação longa iniciada")
        self._confirmation_sound("long_start")
        # A ordem importa: o pré-roll primeiro, senão o clipe sairia com o
        # começo da própria gravação dentro dele.
        self.long_clip = self._save_replay_file()
        if self.long_clip is None:
            log("[longa] o pré-roll não saiu; grava-se só do atalho em diante")
        try:
            obs.call("StartRecord")
        except (obs.ObsError, OSError) as exc:
            log(f"[longa] o OBS recusou iniciar a gravação: {exc}")
            self._note_event("long_failed", "O OBS recusou gravar")
            self.long_clip = None
            return
        self.long_recording = True
        # Sem evento: "gravando tudo" é estado permanente, e é o ponto vermelho
        # da HUD que o mostra. Como faixa, ele só roubaria o lugar do marcador.
        self._publish_activity()
        log("[longa] gravação longa iniciada com pré-roll de "
            f"{self.settings.replay_seconds}s")

    def stop_long_recording(self) -> Path | None:
        """Encerra a gravação longa e emenda o pré-roll na frente dela."""
        if not self.long_recording:
            return None
        self.long_recording = False
        self._note_event("long_saving", "Fechando gravação longa…")
        self._confirmation_sound("long_stop")
        try:
            result = obs.call("StopRecord")
        except (obs.ObsError, OSError) as exc:
            log(f"[longa] falha ao encerrar a gravação: {exc}")
            self._note_event("long_failed", "O OBS não encerrou a gravação")
            return None
        recorded = Path(result.get("outputPath", ""))
        clip, self.long_clip = self.long_clip, None
        markers, self.long_markers = self.long_markers, []
        if not recorded.is_file():
            log("[aviso] o OBS não devolveu arquivo da gravação longa")
            self._note_event("long_failed", "O OBS não devolveu arquivo")
            return None

        final, offset = recorded, 0.0
        if clip is not None and clip.is_file():
            joined = recorded.with_name(f"{recorded.stem}-completo{recorded.suffix}")
            if concat_videos(joined, clip, recorded):
                offset = media_duration(clip)
                clip.unlink(missing_ok=True)
                recorded.unlink(missing_ok=True)
                final = joined
            else:
                # Emendar falhou: os dois pedaços valem mais soltos do que
                # perdidos. O clipe entra como arquivo próprio da sessão.
                log("[longa] não consegui emendar o pré-roll; os dois ficam separados")
                self._write_sidecars(clip)
        self._write_sidecars(final, markers=[value + offset for value in markers])
        self.last_clip_name = final.name
        size_mb = final.stat().st_size / 1024 / 1024
        log(f"[longa] {final.name} ({size_mb:.1f} MB)")
        self._note_event("long_saved", f"Gravação longa salva · {final.name}")
        print(final, flush=True)
        return final

    def _write_sidecars(self, path: Path, markers: list[float] | None = None) -> None:
        """Janela, sessão e marcadores ao lado do arquivo, como nos segmentos."""
        try:
            path.with_suffix(path.suffix + ".window").write_text(
                self.clip_window, encoding="utf-8")
            path.with_suffix(path.suffix + ".session").write_text(
                f"{self.clip_session_key}\n{self.clip_window}\n", encoding="utf-8")
            if markers:
                path.with_suffix(path.suffix + ".markers").write_text(
                    "".join(f"{value:.1f}\n" for value in markers), encoding="utf-8")
        except OSError as exc:
            log(f"[aviso] falha ao escrever sidecars de {path.name}: {exc}")

    def _save_replay_file(self) -> Path | None:
        """Pede o Replay Buffer ao OBS e devolve o arquivo que ele escreveu.

        Separado de :meth:`save_replay_clip` porque a gravação longa também
        precisa do pré-roll, mas ele não é um clipe da sessão: vai virar o
        começo do arquivo emendado, e adotá-lo aqui o deixaria também solto no
        buffer, contado duas vezes.
        """
        with self._clip_lock:
            if not self.clip_buffer_active:
                log("[clipe] ignorado: Replay Buffer não está ativo")
                self._note_event("ignored", "Buffer de clipes inativo")
                return None
            try:
                previous = str(obs.call("GetLastReplayBufferReplay").get("savedReplayPath") or "")
            except (obs.ObsError, OSError):
                previous = ""
            try:
                obs.call("SaveReplayBuffer")
            except (obs.ObsError, OSError) as exc:
                log(f"[clipe] falha ao salvar Replay Buffer: {exc}")
                self._note_event("clip_failed", "O OBS recusou o pedido")
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
                log("[clipe] o OBS aceitou o atalho, mas não informou o arquivo salvo")
                self._note_event("clip_failed", "O OBS não informou o arquivo")
                return None
            return path

    def _pending_dir(self) -> Path:
        directory = VIDEO_DIR.parent / ".clipe-pendente"
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def save_replay_clip(self) -> Path | None:
        """Salva o Replay Buffer atual, estendendo o clipe anterior se houver.

        O arquivo não vai direto para o buffer do Lume: enquanto outro atalho
        ainda puder estendê-lo — a janela dura o mesmo tanto que o replay — ele
        espera fora dele, e é publicado já mesclado quando a janela fecha.
        """
        # O instante do atalho, e não o do arquivo: o clipe cobre os segundos
        # *anteriores* a ele, e é essa borda que decide se dois pedidos se
        # sobrepõem. O OBS leva segundos para informar o arquivo salvo.
        now = time.time()
        path = self._save_replay_file()
        if path is None:
            return None
        self.clip_save_queued = False
        merged = self._merge_pending_clip(path, now)
        if merged is not None:
            total = media_duration(merged)
            log(f"[clipe] atalho dentro da janela de replay; {merged.name} "
                f"estendido para {total:.0f}s")
            self._note_event("clip_merged",
                             f"Clipe estendido · {total / 60:.0f}:{total % 60:02.0f}")
            self._confirmation_sound()
            return merged
        # Sem sobreposição: o que esperava vira arquivo do buffer e o novo
        # assume a vez.
        self.flush_pending_clip()
        pending = self._pending_dir() / f"clipe{path.suffix}"
        try:
            pending.unlink(missing_ok=True)
            path.replace(pending)
        except OSError as exc:
            log(f"[clipe] falha ao guardar {path.name}: {exc}")
            self._write_sidecars(path)
            self.last_clip_name = path.name
            self._note_event("clip_saved", f"Clipe salvo · {self.settings.replay_seconds}s")
            self._confirmation_sound()
            return path
        self.pending_clip = pending
        self.pending_clip_at = now
        self.clips_saved += 1
        log(f"[clipe] últimos {self.settings.replay_seconds}s salvos; "
            f"aguardando a janela de mesclagem")
        self._note_event("clip_saved", f"Clipe salvo · {self.settings.replay_seconds}s")
        self._confirmation_sound()
        return pending

    def _rescue_stale_pending_clip(self) -> None:
        """Sobra de uma queda abrupta: um clipe salvo que não foi publicado.

        De que sessão ele era já não se sabe, e inventar isso o penduraria na
        partida errada — vai para o buffer sem sidecars, como vídeo solto, que
        ainda é melhor do que perdido.
        """
        directory = VIDEO_DIR.parent / ".clipe-pendente"
        if not directory.is_dir():
            return
        for leftover in sorted(directory.iterdir()):
            try:
                if not leftover.is_file():
                    continue
                # Pedaços de uma emenda interrompida no meio não servem a ninguém.
                if leftover.stem.endswith(("-inicio", "-uniao")):
                    leftover.unlink(missing_ok=True)
                    continue
                target = VIDEO_DIR / leftover.name
                counter = 1
                while target.exists():
                    target = VIDEO_DIR / f"{leftover.stem}-{counter}{leftover.suffix}"
                    counter += 1
                leftover.replace(target)
                log(f"[clipe] pendente de uma execução anterior publicado em {target.name}")
            except OSError as exc:
                log(f"[aviso] falha ao recuperar {leftover.name}: {exc}")

    def _merge_pending_clip(self, incoming: Path, now: float) -> Path | None:
        """Estende o clipe que espera, quando o pedido novo se sobrepõe a ele.

        O pendente termina no atalho anterior; o novo cobre os segundos
        anteriores a este. Se o começo do novo cai dentro do pendente, o trecho
        em comum não pode aparecer duas vezes — e o corte sai do *fim* do
        pendente, porque só esse lado é exato com cópia de streams.
        """
        pending = self.pending_clip
        if pending is None or not pending.is_file():
            return None
        pending_seconds = media_duration(pending)
        incoming_seconds = media_duration(incoming)
        delta = now - self.pending_clip_at
        if pending_seconds <= 0 or incoming_seconds <= 0 or delta >= incoming_seconds:
            return None
        head = pending_seconds + delta - incoming_seconds
        if head < 0.2:
            # O clipe novo contém o pendente inteiro: não há começo a preservar.
            try:
                pending.unlink(missing_ok=True)
                incoming.replace(pending)
            except OSError as exc:
                log(f"[clipe] falha ao substituir o clipe pendente: {exc}")
                return None
        else:
            start = pending.with_name(f"{pending.stem}-inicio{pending.suffix}")
            union = pending.with_name(f"{pending.stem}-uniao{pending.suffix}")
            if not (cut_head(pending, start, head)
                    and concat_videos(union, start, incoming)):
                # Emendar falhou: os dois pedaços valem mais soltos do que
                # perdidos, cada um como clipe próprio da sessão.
                log("[clipe] não consegui mesclar os clipes vizinhos; seguem separados")
                start.unlink(missing_ok=True)
                union.unlink(missing_ok=True)
                return None
            try:
                union.replace(pending)
            except OSError as exc:
                log(f"[clipe] falha ao adotar o clipe mesclado: {exc}")
                union.unlink(missing_ok=True)
                return None
            start.unlink(missing_ok=True)
            incoming.unlink(missing_ok=True)
        # O arquivo começa onde começava — só o fim andou —, então o nome segue
        # valendo; a espera reabre a partir deste atalho.
        self.pending_clip_at = now
        return pending

    def flush_pending_clip(self) -> Path | None:
        """Publica no buffer o clipe que esperava por uma mesclagem."""
        pending, self.pending_clip = self.pending_clip, None
        self.pending_clip_at = 0.0
        if pending is None or not pending.is_file():
            return None
        target = VIDEO_DIR / pending.name
        counter = 1
        while target.exists():
            target = VIDEO_DIR / f"{pending.stem}-{counter}{pending.suffix}"
            counter += 1
        try:
            VIDEO_DIR.mkdir(parents=True, exist_ok=True)
            pending.replace(target)
        except OSError as exc:
            log(f"[clipe] falha ao publicar {pending.name}: {exc}")
            return None
        self._write_sidecars(target)
        self.last_clip_name = target.name
        log(f"[clipe] {target.name} publicado no buffer")
        self._publish_activity()
        print(target, flush=True)
        return target

    # --- gravação ---------------------------------------------------------
    #: Tempo para o hook do Game Capture injetar antes de valer a pena gravar.
    #: Medido em ~2 s nesta máquina; a folga evita começar o arquivo no escuro.
    HOOK_WARMUP_SECONDS = 4.0

    def _apply_mic_filters(self) -> None:
        # Falhar aqui não pode impedir a gravação: sem o filtro, o microfone
        # sai cru, como antes — melhor que perder a partida.
        try:
            obs.apply_mic_filters()
        except (obs.ObsError, OSError) as exc:
            log(f"[aviso] filtros do microfone não aplicados: {exc}")

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
            self._apply_mic_filters()
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
            self._apply_mic_filters()
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
                    # Reescrever o sinal a cada volta mantém o marcador e o
                    # tempo visíveis para a HUD, e faz da data de modificação um
                    # batimento: sem segmentação (``VIDEO_SEGMENT_SECONDS=0``)
                    # isto aqui seria escrito uma única vez na sessão inteira.
                    elapsed = time.monotonic() - self.recording_started
                    if limit and elapsed >= limit:
                        break
                    focus_lost_at, grace_expired = self._update_focus_grace(
                        self._focus_state(window, "continuous"), focus_lost_at)
                    # Publica novamente depois de observar o foco, para que a
                    # HUD receba o prazo já nesta mesma volta.
                    self._suspend_others(window)
                    if grace_expired:
                        session_ended = True
                        break
                self._stop_recording(window, session_key)
                if session_ended or self.stopping or not limit:
                    break
                # Entre um segmento e outro vale o mesmo critério do laço: só
                # uma saída de verdade encerra. Uma leitura em branco aqui
                # cortava a sessão exatamente na virada do arquivo.
                if self._focus_state(window, "continuous") == "fora":
                    break
        finally:
            self._finish_game_session()
            self.session_started_at = 0.0
            self.focus_grace_deadline = 0.0
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
                # A janela de mesclagem fechou: o clipe que esperava vira
                # arquivo do buffer.
                if (self.pending_clip is not None
                        and time.time() - self.pending_clip_at >= self.settings.replay_seconds):
                    self.flush_pending_clip()
                focus_lost_at, grace_expired = self._update_focus_grace(
                    self._focus_state(window, "clips"), focus_lost_at)
                self._suspend_others(window)
                if grace_expired:
                    break
        finally:
            # A sessão acabou: não há próximo atalho para estender o clipe que
            # esperava. Antes do buffer cair, porque os sidecars dele saem da
            # sessão que está sendo encerrada.
            self.flush_pending_clip()
            # Antes de derrubar o buffer: parar o OBS com uma gravação longa em
            # curso deixaria o arquivo dela órfão, sem sidecar e sem emenda.
            self.stop_long_recording()
            self._stop_replay_buffer()
            self._release_others("buffer de clipes encerrado")
            self._finish_game_session()
            self.session_started_at = 0.0
            self.focus_grace_deadline = 0.0
            self.session_active = False
            self.clip_save_queued = False

    def run(self) -> int:
        from .winrecord import _install_stop_handlers

        _install_stop_handlers(self.stop)
        initialize()
        gamesession.close_stale()
        self._rescue_stale_pending_clip()
        self._release_others("limpeza inicial")

        hotkey = MarkerHotkey(self.settings.hotkey, self.hotkey_pressed,
                              on_hold=self.hotkey_held,
                              hold_seconds=self.settings.hold_seconds)
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
