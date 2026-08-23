"""Seleção automática do backend de captura conforme o sistema operacional.

Uso:

    from app.capture import get_backend
    backend = get_backend()          # LinuxCaptureBackend ou WindowsCaptureBackend

O resto do app nunca importa ``linux``/``windows`` diretamente — só chama
``get_backend()``. Trocar de SO passa a ser transparente.
"""

from __future__ import annotations

import os
import sys

from .base import AudioConfig, CaptureBackend, Monitor, ScreenConfig, matched_sensitive_pattern

__all__ = [
    "AudioConfig",
    "CaptureBackend",
    "Monitor",
    "ScreenConfig",
    "matched_sensitive_pattern",
    "get_backend",
]

_cached: CaptureBackend | None = None


def get_backend(force: str | None = None) -> CaptureBackend:
    """Devolve o backend do SO atual (memorizado).

    ``force`` (``"linux"``/``"windows"``) permite testar um backend específico;
    caso contrário decide por ``os.name``/``sys.platform``.
    """
    global _cached
    if force is None and _cached is not None:
        return _cached

    target = force or ("windows" if os.name == "nt" else "linux" if sys.platform.startswith("linux") else os.name)
    if target == "windows":
        from .windows import WindowsCaptureBackend

        backend: CaptureBackend = WindowsCaptureBackend()
    elif target == "linux":
        from .linux import LinuxCaptureBackend

        backend = LinuxCaptureBackend()
    else:
        raise RuntimeError(f"Sistema operacional sem backend de captura: {target!r}")

    if force is None:
        _cached = backend
    return backend
