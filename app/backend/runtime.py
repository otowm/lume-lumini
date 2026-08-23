"""Helpers de runtime que funcionam igual em Linux e Windows.

Centraliza as poucas coisas que diferem entre sistemas operacionais: onde ficam
os arquivos efêmeros de execução e como travar um arquivo. O resto do app não
precisa saber em qual SO está rodando.
"""

from __future__ import annotations

import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

IS_WINDOWS = os.name == "nt"
IS_LINUX = sys.platform.startswith("linux")


def runtime_dir() -> Path:
    """Diretório para arquivos efêmeros (locks, estado volátil).

    Linux usa ``XDG_RUNTIME_DIR`` (tmpfs por usuário) quando disponível;
    Windows e o resto caem no diretório temporário do sistema.
    """
    if not IS_WINDOWS:
        xdg = os.environ.get("XDG_RUNTIME_DIR")
        if xdg and Path(xdg).is_dir():
            return Path(xdg)
    return Path(tempfile.gettempdir())


def video_recording_flag() -> Path:
    """Arquivo que sinaliza "estou gravando vídeo agora".

    É como o laço de vídeo pede ao supervisor que suspenda áudio e telas
    enquanto grava, sem precisar falar com a API: o supervisor observa este
    arquivo no mesmo laço em que vigia os processos. Se o gravador morrer, o
    arquivo some e as capturas voltam sozinhas.
    """
    return runtime_dir() / "lume-video-recording"


def video_activity_flag() -> Path:
    """Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo."""
    return runtime_dir() / "lume-video-active"


@contextmanager
def exclusive_lock(path: Path) -> Iterator[bool]:
    """Trava exclusiva e não-bloqueante sobre ``path``.

    Retorna ``True`` se conseguiu a trava, ``False`` se outro processo já a tem.
    Usa ``fcntl`` no POSIX e ``msvcrt`` no Windows, expondo a mesma semântica.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = path.open("w")
    acquired = False
    try:
        if IS_WINDOWS:
            import msvcrt

            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                acquired = True
            except OSError:
                acquired = False
        else:
            import fcntl

            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                acquired = True
            except OSError:
                acquired = False
        yield acquired
    finally:
        if acquired:
            if IS_WINDOWS:
                import msvcrt

                try:
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            else:
                import fcntl

                try:
                    fcntl.flock(handle, fcntl.LOCK_UN)
                except OSError:
                    pass
        handle.close()
