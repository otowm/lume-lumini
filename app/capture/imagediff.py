"""Comparação visual entre dois frames, com ffmpeg.

O laço de captura do Linux usa ImageMagick (``magick ... -compose difference``).
No Windows não há ImageMagick, e exigir mais uma instalação por causa de uma
subtração de imagens seria desproporcional — o ffmpeg, que já é obrigatório,
resolve. O critério é o mesmo dos dois lados: reduzir para 320x180 em tons de
cinza, marcar os pixels que diferem acima de 8% e tirar a média.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

#: Resolução da miniatura comparada, igual à do ``bin/capture-loop``.
THUMB_WIDTH, THUMB_HEIGHT = 320, 180

#: Equivalente ao ``-threshold 8%`` do ImageMagick.
PIXEL_THRESHOLD = round(0.08 * 255)

_HIDDEN_PROCESS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


def thumbnail(image: Path, ffmpeg: str = "ffmpeg") -> bytes | None:
    """Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar."""
    result = subprocess.run(
        [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(image),
         "-vf", f"scale={THUMB_WIDTH}:{THUMB_HEIGHT},format=gray",
         "-frames:v", "1", "-f", "rawvideo", "-"],
        check=False, capture_output=True, timeout=30,
        creationflags=_HIDDEN_PROCESS,
    )
    expected = THUMB_WIDTH * THUMB_HEIGHT
    if result.returncode != 0 or len(result.stdout) < expected:
        return None
    return result.stdout[:expected]


def difference_percent(old: bytes, new: bytes) -> float:
    """Percentual de pixels que mudaram além do limiar."""
    if not new:
        return 0.0
    changed = sum(1 for a, b in zip(old, new) if abs(a - b) > PIXEL_THRESHOLD)
    return 100.0 * changed / len(new)


def compare_images(before: Path, after: Path, ffmpeg: str = "ffmpeg") -> float | None:
    """Diferença percentual entre dois arquivos de imagem."""
    first = thumbnail(before, ffmpeg)
    second = thumbnail(after, ffmpeg)
    if first is None or second is None:
        return None
    return round(difference_percent(first, second), 4)
