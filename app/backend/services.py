"""Gerenciamento de serviços independente de sistema operacional.

No Linux o systemd faz tudo: mantém a captura viva, reinicia o que morre e
dispara o processamento noturno. No Windows não existe equivalente, então este
módulo traz um supervisor próprio que roda dentro do processo da API e oferece
exatamente a mesma interface.

O resto do app trata nomes de unit (``captura-dia-audio.service``) como
identificadores opacos e nunca chama ``systemctl`` direto — assim os dois
sistemas seguem o mesmo caminho de código.
"""

from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Sequence

import shutil

from .main_paths import AUDIO_DIR, CONFIG_DIR, MEDIA_ROOT
from .runtime import IS_WINDOWS, runtime_dir, video_recording_flag

#: Raiz do repositório — os subprocessos rodam a partir dela para que
#: ``python -m app.…`` resolva.
REPO_ROOT = Path(__file__).resolve().parents[2]

LOG_DIR = MEDIA_ROOT / "logs"
STATE_FILE = CONFIG_DIR / "services.json"

#: Igual ao ``RestartSec=15`` das units.
RESTART_DELAY_SECONDS = 15

#: Quanto esperar por uma parada limpa antes de matar o processo.
STOP_GRACE_SECONDS = 10

DEFAULT_SCHEDULE = "03:30"
DEFAULT_IDLE_PAUSE_SECONDS = 300


def windows_idle_seconds() -> float:
    """Return seconds since the last real keyboard or mouse input on Windows."""
    if not IS_WINDOWS:
        return 0.0
    try:
        import ctypes
        from ctypes import wintypes

        class _LASTINPUTINFO(ctypes.Structure):
            _fields_ = [("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD)]

        info = _LASTINPUTINFO()
        info.cbSize = ctypes.sizeof(info)
        if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(info)):
            return 0.0
        now = int(ctypes.windll.kernel32.GetTickCount())
        return ((now - int(info.dwTime)) & 0xFFFFFFFF) / 1000.0
    except (OSError, AttributeError, ValueError):
        # Unknown idle state must never stop a capture.
        return 0.0


@dataclass
class ActionResult:
    """Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam."""

    returncode: int
    stdout: str = ""
    stderr: str = ""


def _unknown(unit: str) -> dict[str, str | bool]:
    return {
        "unit": unit,
        "active": False,
        "active_state": "unknown",
        "sub_state": "unknown",
        "enabled_state": "unknown",
        "pid": "0",
    }


class ServiceManager(ABC):
    """Contrato que o ``main.py`` usa; systemd e supervisor implementam."""

    @abstractmethod
    def state(self, unit: str) -> dict[str, str | bool]:
        """Estado de uma unit, no mesmo formato que ``systemctl show`` produz."""

    @abstractmethod
    def action(self, verb: str, units: Sequence[str], timeout: int = 30,
               now: bool = False, no_block: bool = False) -> ActionResult:
        """Executa ``start``/``stop``/``restart``/``try-restart``/``enable``/``disable``."""

    @abstractmethod
    def timer_state(self) -> dict[str, object]:
        """Horário configurado do processamento noturno e se está ativo."""

    @abstractmethod
    def set_timer(self, time_hhmm: str, enabled: bool) -> ActionResult:
        """Reprograma o processamento noturno."""

    @abstractmethod
    def run_transient(self, unit: str, argv: list[str], timeout_property: str = "",
                      timeout: int = 20) -> ActionResult:
        """Dispara um job avulso sob um nome de unit, para poder cancelá-lo depois.

        É o que os jobs de vídeo usam: cada análise vira uma unit própria
        (``lume-video-7``) que a UI acompanha e pode parar.
        """

    def restart_self(self) -> ActionResult:
        """Reinicia a própria interface (usado ao trocar o local dos dados)."""
        return ActionResult(0)

    def startup(self) -> None:
        """Chamado quando a API sobe."""

    def shutdown(self) -> None:
        """Chamado quando a API desce."""

    def idle_state(self) -> dict[str, object]:
        """Politica de pausa por inatividade, quando suportada."""
        return {"supported": False, "enabled": False, "idle_seconds": 0,
                "threshold_seconds": 0, "captures_paused": False}


# ---------------------------------------------------------------------------
# Linux — delega ao systemd, comportamento idêntico ao de antes
# ---------------------------------------------------------------------------

SCHEDULE_DROPIN = (
    Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    / "systemd/user/lume-process.timer.d/schedule.conf"
)


#: Units suspensas durante uma pausa por inatividade (áudio e telas).
PAUSABLE_UNITS = ("captura-dia-audio.service", "captura-dia-tela.service")


def _video_pause_file() -> Path:
    """Arquivo de estado que o laço de vídeo cria enquanto controla as capturas.

    Mesma convenção de ``bin/game-video-loop``: quando ele existe, o vídeo
    seletivo já pausou áudio/telas e o idle não deve mexer nelas.
    """
    return runtime_dir() / "captura-dia-video-paused"


class SystemdServiceManager(ServiceManager):
    name = "systemd"

    def __init__(self) -> None:
        try:
            self._idle_pause_seconds = max(
                0, int(os.environ.get("LUME_IDLE_PAUSE_SECONDS",
                                      str(DEFAULT_IDLE_PAUSE_SECONDS))))
        except ValueError:
            self._idle_pause_seconds = DEFAULT_IDLE_PAUSE_SECONDS
        # swayidle traduz o protocolo ext-idle-notify do KWin em eventos; aqui
        # ele só cria/remove este flag, e a política (o que pausar) fica neste
        # processo, espelhando o supervisor do Windows.
        self._idle_flag = runtime_dir() / "lume-idle-active"
        self._swayidle: subprocess.Popen | None = None
        self._idle_thread: threading.Thread | None = None
        self._idle_stop = threading.Event()
        self._idle_lock = threading.RLock()
        self._idle_suspended: set[str] = set()
        self._idle_since: float | None = None
        self._swayidle_path = shutil.which("swayidle")

    @staticmethod
    def _run(command: list[str], timeout: int) -> ActionResult:
        try:
            done = subprocess.run(command, text=True, capture_output=True,
                                  timeout=timeout, env=os.environ.copy())
        except FileNotFoundError:
            return ActionResult(127, "", f"{command[0]}: comando indisponível")
        except subprocess.TimeoutExpired as exc:
            return ActionResult(124, "", str(exc))
        return ActionResult(done.returncode, done.stdout or "", done.stderr or "")

    def state(self, unit: str) -> dict[str, str | bool]:
        result = self._run(
            ["systemctl", "--user", "show", unit,
             "--property=ActiveState,SubState,UnitFileState,MainPID"], timeout=5)
        values: dict[str, str] = {}
        for line in result.stdout.splitlines():
            key, _, value = line.partition("=")
            values[key] = value
        if not values:
            return _unknown(unit)
        return {
            "unit": unit,
            "active": values.get("ActiveState") in {"active", "activating"},
            "active_state": values.get("ActiveState", "unknown"),
            "sub_state": values.get("SubState", "unknown"),
            "enabled_state": values.get("UnitFileState", "unknown"),
            "pid": values.get("MainPID", "0"),
        }

    def action(self, verb: str, units: Sequence[str], timeout: int = 30,
               now: bool = False, no_block: bool = False) -> ActionResult:
        command = ["systemctl", "--user", verb]
        if now:
            command.append("--now")
        if no_block:
            command.append("--no-block")
        command.extend(units)
        return self._run(command, timeout)

    def timer_state(self) -> dict[str, object]:
        configured = DEFAULT_SCHEDULE
        if SCHEDULE_DROPIN.exists():
            match = re.search(r"OnCalendar=\*-\*-\*\s+(\d{2}:\d{2}):\d{2}",
                              SCHEDULE_DROPIN.read_text(encoding="utf-8"))
            if match:
                configured = match.group(1)
        result = self._run(
            ["systemctl", "--user", "show", "lume-process.timer",
             "--property=ActiveState,NextElapseUSecRealtime"], timeout=5)
        values = dict(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line)
        return {
            "time": configured,
            "enabled": values.get("ActiveState") == "active",
            "next_run": values.get("NextElapseUSecRealtime", ""),
        }

    def set_timer(self, time_hhmm: str, enabled: bool) -> ActionResult:
        SCHEDULE_DROPIN.parent.mkdir(parents=True, exist_ok=True)
        SCHEDULE_DROPIN.write_text(
            f"[Timer]\nOnCalendar=\nOnCalendar=*-*-* {time_hhmm}:00\nRandomizedDelaySec=0\n",
            encoding="utf-8")
        reload_result = self._run(["systemctl", "--user", "daemon-reload"], timeout=15)
        if reload_result.returncode != 0:
            return reload_result
        verb = "enable" if enabled else "disable"
        result = self.action(verb, ["lume-process.timer"], timeout=20, now=True)
        if result.returncode != 0:
            return result
        if enabled:
            self.action("restart", ["lume-process.timer"], timeout=20)
        return ActionResult(0)

    def run_transient(self, unit: str, argv: list[str], timeout_property: str = "",
                      timeout: int = 20) -> ActionResult:
        command = ["systemd-run", "--user", "--collect", f"--unit={unit}",
                   f"--property=WorkingDirectory={REPO_ROOT}"]
        # systemd-run parte do ambiente do gerenciador do usuário, não do
        # serviço Lume que o chamou. Sem repassar estes overrides, o worker
        # pode usar outro banco e outro armazenamento enquanto a API continua
        # mostrando o job parado em 0%.
        command.extend(
            f"--setenv={name}={value}"
            for name, value in sorted(os.environ.items())
            if name.startswith("CAPTURA_DIA_")
        )
        if timeout_property:
            command.append(f"--property=TimeoutStartSec={timeout_property}")
        command.extend(argv)
        return self._run(command, timeout)

    def restart_self(self) -> ActionResult:
        unit_name = f"lume-storage-restart-{datetime.now().strftime('%H%M%S%f')}"
        return self._run([
            "systemd-run", "--user", f"--unit={unit_name}", "--on-active=2s",
            "systemctl", "--user", "restart", "lume.service",
        ], timeout=15)

    # --- Pausa por inatividade (swayidle + política neste processo) -------
    def _idle_available(self) -> bool:
        return self._idle_pause_seconds > 0 and self._swayidle_path is not None

    def startup(self) -> None:
        if not self._idle_available():
            return
        self._idle_flag.unlink(missing_ok=True)
        if self._idle_thread is None:
            self._idle_stop.clear()
            self._idle_thread = threading.Thread(
                target=self._idle_loop, name="lume-idle", daemon=True)
            self._idle_thread.start()

    def shutdown(self) -> None:
        self._idle_stop.set()
        if self._swayidle is not None:
            try:
                self._swayidle.terminate()
            except OSError:
                pass
            self._swayidle = None
        # Não deixe capturas presas em pausa se a API cair enquanto ocioso.
        with self._idle_lock:
            stuck = sorted(self._idle_suspended)
            self._idle_suspended.clear()
        for unit in stuck:
            if not _video_pause_file().exists():
                self.action("start", [unit], timeout=20)
        self._idle_flag.unlink(missing_ok=True)

    def _spawn_swayidle(self) -> None:
        """(Re)inicia o swayidle apontando os eventos para o flag de idle."""
        flag = str(self._idle_flag)
        argv = [
            self._swayidle_path, "-w",
            "timeout", str(self._idle_pause_seconds),
            f"touch -- {flag!r}",
            "resume", f"rm -f -- {flag!r}",
        ]
        try:
            self._swayidle = subprocess.Popen(
                argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, env=os.environ.copy())
        except OSError:
            self._swayidle = None

    def _idle_loop(self) -> None:
        backoff = 0.0
        while not self._idle_stop.wait(1.0):
            try:
                if self._swayidle is None or self._swayidle.poll() is not None:
                    # Respawn com pequeno backoff (ex.: reinício do compositor).
                    if backoff <= 0:
                        self._spawn_swayidle()
                        backoff = 15.0 if self._swayidle is None else 0.0
                    else:
                        backoff = max(0.0, backoff - 1.0)
                    continue
                self._apply_idle_policy()
            except Exception:
                # O laço de idle nunca pode derrubar a API.
                pass

    def _apply_idle_policy(self) -> None:
        idle = self._idle_flag.exists()
        video_owns = _video_pause_file().exists()
        with self._idle_lock:
            if idle and not self._idle_suspended:
                # Só suspende o que está realmente de pé e ainda não foi pausado
                # pelo vídeo seletivo; assim o retorno restaura exatamente isto.
                to_pause = [
                    unit for unit in PAUSABLE_UNITS
                    if not video_owns and self.state(unit)["active"]
                ]
                for unit in to_pause:
                    self.action("stop", [unit], timeout=20)
                if to_pause:
                    self._idle_suspended = set(to_pause)
                    self._idle_since = time.time()
            elif not idle and self._idle_suspended:
                to_resume = sorted(self._idle_suspended)
                self._idle_suspended.clear()
                self._idle_since = None
                for unit in to_resume:
                    # Se o vídeo assumiu no meio-tempo, deixe-o restaurar.
                    if not _video_pause_file().exists():
                        self.action("start", [unit], timeout=20)

    def idle_state(self) -> dict[str, object]:
        if self._idle_pause_seconds <= 0:
            return {"supported": True, "enabled": False, "idle_seconds": 0,
                    "threshold_seconds": 0, "captures_paused": False,
                    "detector": "swayidle"}
        if self._swayidle_path is None:
            return {"supported": False, "enabled": False, "idle_seconds": 0,
                    "threshold_seconds": self._idle_pause_seconds,
                    "captures_paused": False, "detector": "swayidle",
                    "hint": "swayidle ausente; instale com 'sudo pacman -S swayidle'."}
        with self._idle_lock:
            paused = bool(self._idle_suspended)
            since = self._idle_since
        idle_seconds = 0
        if since is not None:
            idle_seconds = round(self._idle_pause_seconds + (time.time() - since))
        return {
            "supported": True,
            "enabled": True,
            "idle_seconds": idle_seconds,
            "threshold_seconds": self._idle_pause_seconds,
            "captures_paused": paused,
            "detector": "swayidle",
        }


# ---------------------------------------------------------------------------
# Windows — supervisor de processos dentro da própria API
# ---------------------------------------------------------------------------

@dataclass
class _UnitDef:
    """Uma unit supervisionada.

    ``simple`` roda enquanto o serviço estiver ligado (e volta sozinha se cair);
    ``oneshot`` executa uma vez e termina; ``target`` só agrupa outras units.
    """

    kind: str  # "simple" | "oneshot" | "target" | "unsupported" | "external"
    argv: Callable[[str], list[str]] | None = None
    restart: bool = False
    members: tuple[str, ...] = ()
    description: str = ""


def _python() -> str:
    return sys.executable or "python"


def _pipeline(*extra: str) -> list[str]:
    return [_python(), "-m", "app.backend.pipeline", *extra]


_UNITS: dict[str, _UnitDef] = {
    "captura-dia-audio.service": _UnitDef(
        kind="simple", restart=True, description="gravação de áudio",
        argv=lambda _arg: [_python(), "-m", "app.capture.winrecord",
                           "--outdir", str(AUDIO_DIR), "--segment", "900"],
    ),
    "captura-dia-tela.service": _UnitDef(
        kind="simple", restart=True, description="captura de telas",
        argv=lambda _arg: [_python(), "-m", "app.capture.winscreen"],
    ),
    "captura-dia.target": _UnitDef(
        kind="target", description="captura do dia",
        members=("captura-dia-audio.service", "captura-dia-tela.service"),
    ),
    "lume-process.service": _UnitDef(
        kind="oneshot", description="processamento",
        argv=lambda _arg: _pipeline("--limit-audio", "500", "--limit-screen", "5000"),
    ),
    "lume-summary@": _UnitDef(
        kind="oneshot", description="resumo do dia",
        argv=lambda arg: _pipeline("--summary-only", arg),
    ),
    "lume-hourly@": _UnitDef(
        kind="oneshot", description="resumos horários",
        argv=lambda arg: _pipeline("--hourly-only", arg),
    ),
    "captura-dia-video.service": _UnitDef(
        kind="simple", restart=True, description="gravação seletiva de vídeo",
        argv=lambda _arg: [_python(), "-m", "app.capture.winvideo"],
    ),
    # Fora de ``_PAUSABLE`` e de ``captura-dia.target`` de propósito: a HUD
    # existe justamente para vigiar a gravação, então precisa continuar de pé
    # exatamente quando as outras capturas são suspensas.
    "captura-dia-hud.service": _UnitDef(
        kind="simple", restart=True, description="HUD de gravação",
        argv=lambda _arg: [_python(), "-m", "app.capture.hud"],
    ),
    "lume.service": _UnitDef(kind="external", description="interface Lume"),
}


def _resolve(unit: str) -> tuple[_UnitDef | None, str]:
    """Encontra a definição da unit e o argumento de template (``@dia``)."""
    if unit in _UNITS:
        return _UNITS[unit], ""
    match = re.fullmatch(r"([A-Za-z0-9._-]+)@([^.]*)\.service", unit)
    if match:
        template = _UNITS.get(f"{match.group(1)}@")
        if template:
            return template, match.group(2)
    return None, ""


class _JobObject:
    """Amarra os processos filhos ao ciclo de vida da API.

    É o que o systemd consegue de graça com cgroups: quando o serviço morre,
    tudo que ele criou morre junto. No Windows, sem isso, um encerramento
    abrupto da interface (fim de tarefa, crash, logoff) deixaria o gravador
    rodando, segurando o microfone — e na abertura seguinte haveria dois
    gravadores gravando o mesmo áudio.

    ``KILL_ON_JOB_CLOSE`` resolve: o handle só existe enquanto este processo
    existir, e ao ser fechado o Windows encerra todo o grupo.
    """

    _LIMIT_KILL_ON_JOB_CLOSE = 0x2000
    _EXTENDED_LIMIT_INFORMATION = 9

    def __init__(self) -> None:
        self.handle = None
        if not IS_WINDOWS:
            return
        try:
            import ctypes
            from ctypes import wintypes

            class _BASIC(ctypes.Structure):
                _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64),
                            ("PerJobUserTimeLimit", ctypes.c_int64),
                            ("LimitFlags", wintypes.DWORD),
                            ("MinimumWorkingSetSize", ctypes.c_size_t),
                            ("MaximumWorkingSetSize", ctypes.c_size_t),
                            ("ActiveProcessLimit", wintypes.DWORD),
                            ("Affinity", ctypes.c_size_t),
                            ("PriorityClass", wintypes.DWORD),
                            ("SchedulingClass", wintypes.DWORD)]

            class _IO(ctypes.Structure):
                _fields_ = [("ReadOperationCount", ctypes.c_uint64),
                            ("WriteOperationCount", ctypes.c_uint64),
                            ("OtherOperationCount", ctypes.c_uint64),
                            ("ReadTransferCount", ctypes.c_uint64),
                            ("WriteTransferCount", ctypes.c_uint64),
                            ("OtherTransferCount", ctypes.c_uint64)]

            class _EXTENDED(ctypes.Structure):
                _fields_ = [("BasicLimitInformation", _BASIC), ("IoInfo", _IO),
                            ("ProcessMemoryLimit", ctypes.c_size_t),
                            ("JobMemoryLimit", ctypes.c_size_t),
                            ("PeakProcessMemoryUsed", ctypes.c_size_t),
                            ("PeakJobMemoryUsed", ctypes.c_size_t)]

            self._kernel32 = ctypes.windll.kernel32
            handle = self._kernel32.CreateJobObjectW(None, None)
            if not handle:
                return
            info = _EXTENDED()
            info.BasicLimitInformation.LimitFlags = self._LIMIT_KILL_ON_JOB_CLOSE
            if not self._kernel32.SetInformationJobObject(
                    handle, self._EXTENDED_LIMIT_INFORMATION,
                    ctypes.byref(info), ctypes.sizeof(info)):
                self._kernel32.CloseHandle(handle)
                return
            self.handle = handle
        except (OSError, AttributeError):
            self.handle = None

    def adopt(self, popen: subprocess.Popen) -> None:
        if self.handle is None:
            return
        try:
            self._kernel32.AssignProcessToJobObject(self.handle, int(popen._handle))
        except (OSError, AttributeError, ValueError):
            pass


class _Process:
    """Um processo filho supervisionado."""

    def __init__(self, unit: str, popen: subprocess.Popen, log: Path) -> None:
        self.unit = unit
        self.popen = popen
        self.log = log
        self.started_at = time.time()
        self.exit_code: int | None = None
        self.finished_at: float | None = None


class WindowsServiceManager(ServiceManager):
    """Supervisor: mantém os processos de captura vivos e agenda o processamento.

    Vive dentro do processo da API — no Windows ela é iniciada silenciosamente
    no login e permanece como o processo de vida longa do Lume, mesmo sem uma
    aba do navegador aberta.
    """

    name = "supervisor"

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._job = _JobObject()
        self._dynamic: dict[str, _UnitDef] = {}   # jobs criados por run_transient
        self._running: dict[str, _Process] = {}
        self._last_exit: dict[str, tuple[int, float]] = {}
        self._wanted: set[str] = set()          # units que devem estar de pé
        self._restart_at: dict[str, float] = {}
        self._enabled: set[str] = set()         # equivalente a `systemctl enable`
        self._video_flag_seen = False
        try:
            self._idle_pause_seconds = max(
                0, int(os.environ.get("LUME_IDLE_PAUSE_SECONDS",
                                      str(DEFAULT_IDLE_PAUSE_SECONDS))))
        except ValueError:
            self._idle_pause_seconds = DEFAULT_IDLE_PAUSE_SECONDS
        self._idle_seconds = windows_idle_seconds()
        self._idle_seen = self._idle_pause_seconds > 0 and (
            self._idle_seconds >= self._idle_pause_seconds)
        self._capture_blocked = self._idle_seen or video_recording_flag().exists()
        self._schedule_time = DEFAULT_SCHEDULE
        self._schedule_enabled = False
        self._last_timer_run: str = ""
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._load_state()

    def _remember(self, unit: str, wanted: bool) -> None:
        """Anota que a captura deve (ou não) voltar na próxima abertura do Lume.

        No Linux quem guarda isso é o ``systemctl enable``. No Windows o host
        oculto volta no login, lê este estado e restaura apenas as capturas que
        continuavam habilitadas.
        """
        definition, _ = self._definition(unit)
        if definition is None or definition.kind not in {"simple", "target"}:
            return
        members = definition.members if definition.kind == "target" else (unit,)
        for name in members:
            if wanted:
                self._enabled.add(name)
            else:
                self._enabled.discard(name)
        self._save_state()

    def _definition(self, unit: str) -> tuple[_UnitDef | None, str]:
        """Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução."""
        dynamic = self._dynamic.get(unit)
        if dynamic is not None:
            return dynamic, ""
        return _resolve(unit)

    def run_transient(self, unit: str, argv: list[str], timeout_property: str = "",
                      timeout: int = 20) -> ActionResult:
        with self._lock:
            self._dynamic[unit] = _UnitDef(kind="oneshot", argv=lambda _arg: list(argv),
                                           description=f"job {unit}")
            return self._start(unit)

    # --- persistência ----------------------------------------------------
    def _load_state(self) -> None:
        try:
            data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        self._enabled = set(data.get("enabled", []))
        self._schedule_time = data.get("schedule_time", DEFAULT_SCHEDULE)
        self._schedule_enabled = bool(data.get("schedule_enabled", False))
        self._last_timer_run = data.get("last_timer_run", "")

    def _save_state(self) -> None:
        payload = {
            "enabled": sorted(self._enabled),
            "schedule_time": self._schedule_time,
            "schedule_enabled": self._schedule_enabled,
            "last_timer_run": self._last_timer_run,
        }
        try:
            STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            STATE_FILE.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except OSError:
            pass

    # --- ciclo de vida ---------------------------------------------------
    def startup(self) -> None:
        with self._lock:
            for unit in sorted(self._enabled):
                definition, _ = self._definition(unit)
                if definition and definition.kind == "simple":
                    self._start(unit)
        if self._thread is None:
            self._thread = threading.Thread(target=self._supervise, name="lume-supervisor",
                                            daemon=True)
            self._thread.start()

    def shutdown(self) -> None:
        self._stop_event.set()
        with self._lock:
            self._wanted.clear()
            for unit in list(self._running):
                self._stop(unit)

    # --- processos --------------------------------------------------------
    def _log_path(self, unit: str) -> Path:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        safe = re.sub(r"[^0-9A-Za-z@._-]", "_", unit)
        path = LOG_DIR / f"{safe}.log"
        try:
            if path.exists() and path.stat().st_size > 5_000_000:
                path.replace(path.with_suffix(".log.1"))
        except OSError:
            pass
        return path

    def _start(self, unit: str) -> ActionResult:
        definition, arg = self._definition(unit)
        if definition is None:
            return ActionResult(5, "", f"Unit desconhecida: {unit}")
        if definition.kind == "unsupported":
            return ActionResult(1, "", f"{definition.description} ainda não existe no Windows")
        if definition.kind == "external":
            return ActionResult(0)
        if definition.kind == "target":
            failures = []
            for member in definition.members:
                result = self._start(member)
                if result.returncode != 0:
                    failures.append(result.stderr)
            return ActionResult(1, "", "; ".join(failures)) if failures else ActionResult(0)

        # Audio and screenshots remain enabled, but do not start while an
        # automatic pause is active. Selective video is deliberately excluded.
        if unit in self._PAUSABLE and self._capture_blocked:
            return ActionResult(0)

        existing = self._running.get(unit)
        if existing and existing.popen.poll() is None:
            return ActionResult(0)  # já está de pé, como o systemd faria

        assert definition.argv is not None
        argv = definition.argv(arg)
        log = self._log_path(unit)
        try:
            handle = log.open("ab")
            handle.write(f"\n=== {datetime.now().isoformat(timespec='seconds')} "
                         f"start {unit}: {' '.join(argv)}\n".encode())
            handle.flush()
            popen = subprocess.Popen(
                argv, cwd=str(REPO_ROOT), stdout=handle, stderr=handle,
                stdin=subprocess.DEVNULL,
                # Grupo próprio para que o CTRL_BREAK atinja só este filho.
                #
                # Sem CREATE_NO_WINDOW de propósito: ele deixaria o filho sem
                # console nenhum, e `GenerateConsoleCtrlEvent` só alcança
                # processos ligados ao console de quem chama. Com a flag, todo
                # pedido de parada expirava em 10 s e terminava em morte súbita
                # — o gravador de áudio nem chegava a fechar o WAV. Herdando o
                # console (que fica oculto quando o Lume é aberto pelo .bat) o
                # sinal chega e a parada é limpa; a saída dos filhos já vai
                # para os arquivos de log, então nada polui a janela.
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        except OSError as exc:
            return ActionResult(1, "", f"Falha ao iniciar {unit}: {exc}")

        self._job.adopt(popen)
        self._running[unit] = _Process(unit, popen, log)
        self._restart_at.pop(unit, None)
        if definition.kind == "simple":
            self._wanted.add(unit)
        return ActionResult(0)

    def _stop(self, unit: str) -> ActionResult:
        definition, _ = self._definition(unit)
        if definition and definition.kind == "target":
            for member in definition.members:
                self._stop(member)
            return ActionResult(0)

        self._wanted.discard(unit)
        self._restart_at.pop(unit, None)
        process = self._running.get(unit)
        if process is None or process.popen.poll() is not None:
            self._running.pop(unit, None)
            return ActionResult(0)

        popen = process.popen
        # CTRL_BREAK é o que mais se aproxima do SIGTERM aqui: os gravadores o
        # tratam para fechar o WAV com o cabeçalho correto antes de sair.
        try:
            popen.send_signal(signal.CTRL_BREAK_EVENT)
        except (OSError, ValueError, AttributeError):
            popen.terminate()
        try:
            popen.wait(timeout=STOP_GRACE_SECONDS)
        except subprocess.TimeoutExpired:
            popen.kill()
            try:
                popen.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        self._last_exit[unit] = (popen.returncode or 0, time.time())
        self._running.pop(unit, None)
        return ActionResult(0)

    # --- laço de supervisão ----------------------------------------------
    def _supervise(self) -> None:
        while not self._stop_event.wait(1.0):
            try:
                with self._lock:
                    self._reap()
                    self._apply_restarts()
                    self._check_timer()
                    self._follow_capture_policy()
            except Exception:  # o supervisor nunca pode morrer
                pass

    def _reap(self) -> None:
        for unit, process in list(self._running.items()):
            code = process.popen.poll()
            if code is None:
                continue
            self._last_exit[unit] = (code, time.time())
            self._running.pop(unit, None)
            definition, _ = self._definition(unit)
            if definition and definition.restart and unit in self._wanted:
                self._restart_at[unit] = time.time() + RESTART_DELAY_SECONDS

    def _apply_restarts(self) -> None:
        now = time.time()
        for unit, when in list(self._restart_at.items()):
            if now >= when:
                self._restart_at.pop(unit, None)
                if unit in self._wanted:
                    self._start(unit)

    #: Units suspensas enquanto um vídeo está sendo gravado.
    _PAUSABLE = ("captura-dia-audio.service", "captura-dia-tela.service")

    def _follow_capture_policy(self) -> None:
        """Combine selective-video and user-idle pauses without racing them.

        Audio and screenshots only return after every automatic pause reason
        disappears. Selective video itself is never a pausable unit.
        """
        recording = video_recording_flag().exists()
        if recording != self._video_flag_seen:
            self._video_flag_seen = recording
            print(f"[supervisor] sinal de vídeo {'presente' if recording else 'ausente'} "
                  f"({video_recording_flag()})", flush=True)

        self._idle_seconds = windows_idle_seconds()
        idle = self._idle_pause_seconds > 0 and self._idle_seconds >= self._idle_pause_seconds
        if idle != self._idle_seen:
            self._idle_seen = idle
            print(f"[supervisor] usuário {'inativo' if idle else 'ativo'} "
                  f"({self._idle_seconds:.0f}s sem entrada)", flush=True)

        blocked = recording or idle
        if blocked and not self._capture_blocked:
            self._capture_blocked = True
            suspended = [unit for unit in self._PAUSABLE if unit in self._enabled]
            for unit in suspended:
                self._stop(unit)
            if suspended:
                reason = "vídeo seletivo" if recording else "inatividade"
                print(f"[supervisor] capturas comuns suspensas por {reason}", flush=True)
        elif not blocked and self._capture_blocked:
            self._capture_blocked = False
            # A manual pause removes the unit from _enabled and still wins.
            restored = [unit for unit in self._PAUSABLE if unit in self._enabled]
            for unit in restored:
                self._start(unit)
            if restored:
                print("[supervisor] atividade retomada; capturas comuns reiniciadas", flush=True)

    def idle_state(self) -> dict[str, object]:
        with self._lock:
            return {
                "supported": True,
                "enabled": self._idle_pause_seconds > 0,
                "idle_seconds": round(self._idle_seconds),
                "threshold_seconds": self._idle_pause_seconds,
                "captures_paused": self._idle_seen,
            }

    def _check_timer(self) -> None:
        if not self._schedule_enabled:
            return
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        if self._last_timer_run == today:
            return
        try:
            hour, minute = (int(part) for part in self._schedule_time.split(":"))
        except ValueError:
            return
        due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if now < due:
            return
        # Só dispara se ainda estivermos perto do horário; assim o app não roda
        # o processamento de madrugada só porque foi aberto às 15h.
        if now - due > timedelta(hours=1):
            self._last_timer_run = today
            self._save_state()
            return
        self._last_timer_run = today
        self._save_state()
        self._start("lume-process.service")

    # --- interface pública -------------------------------------------------
    def state(self, unit: str) -> dict[str, str | bool]:
        definition, _ = self._definition(unit)
        if definition is None:
            return _unknown(unit)

        with self._lock:
            if definition.kind == "target":
                members = [self.state(name) for name in definition.members]
                active = bool(members) and all(m["active"] for m in members)
                return {
                    "unit": unit,
                    "active": active,
                    "active_state": "active" if active else "inactive",
                    "sub_state": "running" if active else "dead",
                    "enabled_state": "enabled" if unit in self._enabled else "disabled",
                    "pid": "0",
                }
            if definition.kind == "external":
                # A própria API: se este código está rodando, ela está de pé.
                return {
                    "unit": unit, "active": True, "active_state": "active",
                    "sub_state": "running", "enabled_state": "enabled",
                    "pid": str(os.getpid()),
                }
            if definition.kind == "unsupported":
                return _unknown(unit)

            enabled_state = "enabled" if unit in self._enabled else "disabled"
            process = self._running.get(unit)
            if process is not None and process.popen.poll() is None:
                oneshot = definition.kind == "oneshot"
                return {
                    "unit": unit,
                    "active": True,
                    "active_state": "activating" if oneshot else "active",
                    "sub_state": "start" if oneshot else "running",
                    "enabled_state": enabled_state,
                    "pid": str(process.popen.pid),
                }
            if unit in self._restart_at:
                return {
                    "unit": unit, "active": True, "active_state": "activating",
                    "sub_state": "auto-restart", "enabled_state": enabled_state, "pid": "0",
                }
            code, _when = self._last_exit.get(unit, (None, 0.0))
            failed = code is not None and code not in (0, 1) and unit in self._wanted
            return {
                "unit": unit,
                "active": False,
                "active_state": "failed" if failed else "inactive",
                "sub_state": "failed" if failed else "dead",
                "enabled_state": enabled_state,
                "pid": "0",
            }

    def action(self, verb: str, units: Sequence[str], timeout: int = 30,
               now: bool = False, no_block: bool = False) -> ActionResult:
        errors: list[str] = []
        with self._lock:
            for unit in units:
                definition, _ = self._definition(unit)
                if definition is None:
                    errors.append(f"Unit desconhecida: {unit}")
                    continue

                if verb == "start":
                    result = self._start(unit)
                    self._remember(unit, wanted=True)
                elif verb == "stop":
                    result = self._stop(unit)
                    self._remember(unit, wanted=False)
                elif verb in {"restart", "try-restart"}:
                    was_running = self.state(unit)["active"]
                    if verb == "try-restart" and not was_running:
                        continue  # o systemd não inicia o que estava parado
                    self._stop(unit)
                    result = self._start(unit)
                elif verb in {"enable", "disable"}:
                    if verb == "enable":
                        self._enabled.add(unit)
                    else:
                        self._enabled.discard(unit)
                    self._save_state()
                    result = ActionResult(0)
                    if now:
                        result = self._start(unit) if verb == "enable" else self._stop(unit)
                else:
                    result = ActionResult(2, "", f"Verbo não suportado: {verb}")

                if result.returncode != 0 and result.stderr:
                    errors.append(result.stderr)
        return ActionResult(1, "", "; ".join(errors)) if errors else ActionResult(0)

    def timer_state(self) -> dict[str, object]:
        with self._lock:
            next_run = ""
            if self._schedule_enabled:
                try:
                    hour, minute = (int(p) for p in self._schedule_time.split(":"))
                    now = datetime.now()
                    due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if due <= now:
                        due += timedelta(days=1)
                    next_run = due.strftime("%a %Y-%m-%d %H:%M:%S")
                except ValueError:
                    next_run = ""
            return {
                "time": self._schedule_time,
                "enabled": self._schedule_enabled,
                "next_run": next_run,
            }

    def set_timer(self, time_hhmm: str, enabled: bool) -> ActionResult:
        with self._lock:
            self._schedule_time = time_hhmm
            self._schedule_enabled = enabled
            # Se o novo horário ainda está por vir, ele precisa poder rodar
            # hoje. Antes marcávamos o dia atual incondicionalmente e, com isso,
            # salvar 01:42 às 01:30 fazia o supervisor acreditar que a execução
            # de 01:42 já tinha acontecido. Horários que já passaram continuam
            # marcados para evitar um disparo imediato ao salvar a configuração.
            if enabled:
                now = datetime.now()
                try:
                    hour, minute = (int(part) for part in time_hhmm.split(":"))
                    due = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    self._last_timer_run = "" if now < due else now.strftime("%Y-%m-%d")
                except ValueError:
                    self._last_timer_run = now.strftime("%Y-%m-%d")
            self._save_state()
        return ActionResult(0)

    def restart_self(self) -> ActionResult:
        return ActionResult(
            1, "", "Reinicie o Lume manualmente para o novo local passar a valer.")


_manager: ServiceManager | None = None
_manager_lock = threading.Lock()


def get_manager() -> ServiceManager:
    """Gerenciador do sistema atual (memorizado)."""
    global _manager
    if _manager is None:
        with _manager_lock:
            if _manager is None:
                _manager = WindowsServiceManager() if IS_WINDOWS else SystemdServiceManager()
    return _manager
