"""Laço contínuo de captura de telas — porte de ``bin/capture-loop`` para Python.

No Linux esse laço é bash chamando ``captura-tela.sh``. No Windows não há bash
nem ImageMagick, então a mesma lógica vive aqui: mesmos modos (``interval`` e
``change``), mesmo limiar de diferença sobre uma miniatura 320x180 e a mesma
regra de privacidade *fail closed*.

Roda como processo próprio, igual ao gravador de áudio, para o supervisor
precisar apenas de um argv:

    python -m app.capture.winscreen
"""

from __future__ import annotations

import argparse
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from . import ScreenConfig, get_backend, matched_sensitive_pattern
from .base import read_shell_config
from .imagediff import difference_percent as _difference_percent
from .imagediff import thumbnail as _thumbnail_of
from ..backend.main_paths import CONFIG_DIR, SCREEN_CONFIG, SCREEN_DIR, SENSITIVE_FILE
from ..backend.runtime import runtime_dir


def _parse_config(path: Path) -> dict[str, str]:
    """Lê o ``tela.conf`` (formato ``CHAVE=valor`` do shell)."""
    return read_shell_config(path)


def _as_int(values: dict[str, str], key: str, default: int, minimum: int = 1) -> int:
    try:
        parsed = int(values.get(key, default))
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= minimum else default


def _as_float(values: dict[str, str], key: str, default: float) -> float:
    try:
        return float(values.get(key, default))
    except (TypeError, ValueError):
        return default


def _as_bool(values: dict[str, str], key: str, default: bool) -> bool:
    return values.get(key, str(default)).strip().lower() in {"true", "1", "yes"}


class _Settings:
    """Instantâneo do ``tela.conf``, relido quando o arquivo muda no disco."""

    def __init__(self) -> None:
        self.mtime: float | None = None
        self.reload()

    def reload(self) -> None:
        values = _parse_config(SCREEN_CONFIG)
        self.mode = values.get("CAPTURE_MODE", "interval")
        if self.mode not in {"interval", "change"}:
            self.mode = "interval"
        self.interval_seconds = _as_int(values, "INTERVAL_SECONDS", 20)
        self.poll_seconds = _as_int(values, "CHANGE_POLL_SECONDS", 5)
        self.threshold_percent = _as_float(values, "CHANGE_THRESHOLD_PERCENT", 3.0)
        self.max_interval_seconds = _as_int(values, "CHANGE_MAX_INTERVAL_SECONDS", 300)
        self.capture = ScreenConfig(
            capture_root=SCREEN_DIR,
            max_geometry=values.get("MAX_GEOMETRY", "1920x1080>"),
            split_monitors=_as_bool(values, "SPLIT_MONITORS", True),
            active_monitor_only=_as_bool(values, "ACTIVE_MONITOR_ONLY", True),
            privacy_fail_closed=_as_bool(values, "PRIVACY_FAIL_CLOSED", True),
        )
        try:
            self.mtime = SCREEN_CONFIG.stat().st_mtime
        except OSError:
            self.mtime = None

    def refresh_if_changed(self) -> bool:
        try:
            current = SCREEN_CONFIG.stat().st_mtime
        except OSError:
            current = None
        if current != self.mtime:
            self.reload()
            return True
        return False

    @property
    def period(self) -> int:
        return self.poll_seconds if self.mode == "change" else self.interval_seconds


def _thumbnail(ffmpeg: str, image: Path) -> bytes | None:
    return _thumbnail_of(image, ffmpeg)


def _monitor_key(frame: Path) -> str:
    """Identidade do monitor a partir do nome do arquivo (``..._mon1_DP-1.png``).

    A comparação precisa ser por monitor, não por posição na lista: com
    ``ACTIVE_MONITOR_ONLY`` só o monitor em foco é capturado, então a posição 0
    passa a apontar para telas diferentes quando o foco muda — e cada troca de
    monitor pareceria uma mudança enorme.
    """
    match = re.search(r"_mon(\d+)_", frame.name)
    return match.group(1) if match else frame.name


class ScreenLoop:
    def __init__(self, ffmpeg: str = "ffmpeg", once: bool = False) -> None:
        self.backend = get_backend()
        self.settings = _Settings()
        self.ffmpeg = ffmpeg
        self.once = once
        self.state_dir = runtime_dir() / "captura-dia-tela"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.last_saved = 0.0
        self._thumbs: dict[str, bytes] = {}
        self.stopping = False

    def stop(self, _signum=None, _frame=None) -> None:
        self.stopping = True

    # --- privacidade ------------------------------------------------------
    def _privacy_skip(self) -> str | None:
        """Motivo para não capturar agora, ou ``None`` se pode capturar."""
        window = self.backend.active_window()
        if window is None:
            if self.settings.capture.privacy_fail_closed:
                return "janela ativa indisponível (fail closed)"
            return None
        pattern = matched_sensitive_pattern(window, SENSITIVE_FILE)
        if pattern:
            return f"janela sensível ({pattern})"
        return None

    # --- uma volta --------------------------------------------------------
    def tick(self) -> list[Path]:
        reason = self._privacy_skip()
        if reason:
            print(f"[skip] {reason}", file=sys.stderr, flush=True)
            return []

        window = self.backend.active_window() or ""
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        frames = self.backend.grab_frame(SCREEN_DIR, stamp, self.settings.capture, window)
        if not frames or self.settings.mode == "interval":
            for frame in frames:
                print(frame, flush=True)
            if frames:
                self.last_saved = time.time()
            return frames

        # Modo "change": só guarda o conjunto se algo mudou o bastante, ou se
        # já passou tempo demais desde a última gravação.
        keep = (time.time() - self.last_saved) >= self.settings.max_interval_seconds
        thumbs: dict[str, bytes] = {}
        for frame in frames:
            thumb = _thumbnail(self.ffmpeg, frame)
            if thumb is None:
                keep = True  # não deu para comparar: preserva por segurança
                continue
            key = _monitor_key(frame)
            thumbs[key] = thumb
            previous = self._thumbs.get(key)
            if previous is None:
                keep = True
            elif _difference_percent(previous, thumb) >= self.settings.threshold_percent:
                keep = True

        if not keep:
            for frame in frames:
                frame.unlink(missing_ok=True)
                frame.with_suffix(frame.suffix + ".window").unlink(missing_ok=True)
            return []

        self._thumbs.update(thumbs)
        self.last_saved = time.time()
        for frame in frames:
            print(frame, flush=True)
        return frames

    def run(self) -> int:
        from .winrecord import _install_stop_handlers

        _install_stop_handlers(self.stop)
        print(f"[tela] modo={self.settings.mode} período={self.settings.period}s "
              f"destino={SCREEN_DIR}", file=sys.stderr, flush=True)

        while not self.stopping:
            started = time.monotonic()
            try:
                self.tick()
            except Exception as exc:  # o laço não pode morrer por um frame ruim
                print(f"[erro] {exc}", file=sys.stderr, flush=True)
            if self.once:
                break
            if self.settings.refresh_if_changed():
                print(f"[tela] configuração recarregada: modo={self.settings.mode} "
                      f"período={self.settings.period}s", file=sys.stderr, flush=True)
            delay = max(1.0, self.settings.period - (time.monotonic() - started))
            # Dorme em fatias para responder rápido a um pedido de parada.
            while delay > 0 and not self.stopping:
                time.sleep(min(0.5, delay))
                delay -= 0.5
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Laço de captura de telas (Windows).")
    parser.add_argument("--once", action="store_true", help="captura uma vez e sai")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    args = parser.parse_args(argv)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return ScreenLoop(ffmpeg=args.ffmpeg, once=args.once).run()


if __name__ == "__main__":
    raise SystemExit(main())
