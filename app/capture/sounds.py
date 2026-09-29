"""Sons de confirmação do atalho de gravação, personalizáveis.

Cada ação aceita pelo atalho tem uma confirmação audível, porque quem está
jogando escuta sem olhar. Antes elas vinham do tema de som do sistema, e isso
falhava de dois jeitos: temas como o ``ocean`` do KDE não têm esses sons, e
o ``canberra`` toca no canal de notificações — mudo nele, mudo no atalho, sem
erro nenhum. Aqui o arquivo é tocado direto, fora desse canal.

Cada ``slot`` aceita um arquivo escolhido pela pessoa, guardado em
``CONFIG_DIR/sons/<slot>.<ext>``, ou um pacote pronto que preenche todos de
uma vez. Sem arquivo, vale o som padrão do freedesktop (Linux) ou a melodia
de bipes do gravador (Windows).

O gravador do Linux é um script bash e repete esta mesma resolução em
``confirmation_sound``; os nomes de slot e de arquivo são o contrato entre os
dois.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from ..backend.main_paths import CONFIG_DIR

SOUNDS_DIR = CONFIG_DIR / "sons"

#: slot → (rótulo na interface, som padrão do freedesktop).
SLOTS: dict[str, tuple[str, str]] = {
    "clipe": ("Clipe salvo", "complete"),
    # Um toque dentro da janela de replay não abre outro clipe: estende o que
    # acabou de ser salvo. Soar diferente é o que diz isso sem olhar a HUD.
    "clipe-estendido": ("Clipe estendido", "complete"),
    "marcador": ("Marcador", "complete"),
    "longa-inicio": ("Início da gravação longa", "device-added"),
    "longa-fim": ("Fim da gravação longa", "device-removed"),
}

#: Pacotes prontos, um por tema do uisfx (CC0, https://uisfx.com), guardados
#: no próprio projeto. Cada slot recebe o som do tema com o nome ao lado.
PRESETS_DIR = Path(__file__).resolve().parent / "sons" / "uisfx"
PRESET_SOUNDS: dict[str, str] = {
    "clipe": "toggle-on",
    "clipe-estendido": "check",
    "marcador": "open",
    "longa-inicio": "double-click",
    "longa-fim": "deselect",
}

#: Formatos que o ``pw-play`` (libsndfile) e o ``paplay`` abrem.
EXTENSIONS = {".oga", ".ogg", ".opus", ".wav", ".flac", ".mp3"}

#: Um efeito sonoro é curto; o limite só impede que um vídeo vire "som".
MAX_BYTES = 5 * 1024 * 1024

_FREEDESKTOP = Path("/usr/share/sounds/freedesktop/stereo")


def custom_sound(slot: str) -> Path | None:
    """Arquivo escolhido pela pessoa para o slot, se houver."""
    for path in sorted(SOUNDS_DIR.glob(f"{slot}.*")):
        if path.suffix.lower() in EXTENSIONS and path.is_file():
            return path
    return None


def default_sound(slot: str) -> Path | None:
    path = _FREEDESKTOP / f"{SLOTS[slot][1]}.oga"
    return path if path.is_file() else None


def sound_file(slot: str) -> Path | None:
    return custom_sound(slot) or default_sound(slot)


def clear_custom(slot: str) -> None:
    for path in SOUNDS_DIR.glob(f"{slot}.*"):
        path.unlink(missing_ok=True)


def presets() -> list[str]:
    if not PRESETS_DIR.is_dir():
        return []
    return sorted(path.name for path in PRESETS_DIR.iterdir() if path.is_dir())


def apply_preset(theme: str) -> None:
    """Troca todos os slots pelos sons de um tema.

    Copia em vez de apontar: depois de aplicado, cada slot continua podendo
    ser trocado sozinho, como qualquer arquivo escolhido à mão.
    """
    if theme not in presets():
        raise ValueError(theme)
    SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
    for slot, name in PRESET_SOUNDS.items():
        source = PRESETS_DIR / theme / f"{name}.ogg"
        partial = SOUNDS_DIR / f".{slot}.ogg.upload"
        shutil.copyfile(source, partial)
        clear_custom(slot)
        partial.replace(SOUNDS_DIR / f"{slot}.ogg")


def play(slot: str, volume: int = 100) -> bool:
    """Toca o som do slot sem esperar o fim. Devolve se conseguiu disparar.

    ``volume`` vai de 0 a 100. No Windows só arquivos ``.wav`` tocam (é o que
    o ``winsound`` abre) e sem controle de volume; sem eles, quem chamou
    segue com a melodia de bipes.
    """
    if volume <= 0:
        return True
    if os.name == "nt":
        path = custom_sound(slot)
        if path is None or path.suffix.lower() != ".wav":
            return False
        try:
            import winsound

            winsound.PlaySound(str(path), winsound.SND_FILENAME | winsound.SND_ASYNC)
        except (ImportError, RuntimeError, OSError):
            return False
        return True

    path = sound_file(slot)
    if path is None:
        return False
    level = max(0, min(100, volume)) / 100
    commands = []
    if shutil.which("pw-play"):
        commands.append(["pw-play", "--volume", f"{level:.2f}", str(path)])
    if shutil.which("paplay"):
        commands.append(["paplay", f"--volume={round(65536 * level)}", str(path)])
    for command in commands:
        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             start_new_session=True)
        except OSError:
            continue
        return True
    return False
