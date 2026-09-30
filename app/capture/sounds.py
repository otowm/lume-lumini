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

# No Windows o ``winsound`` só toca WAV. Os outros formatos — inclusive os
# pacotes, que são OGG — são convertidos pelo ffmpeg na primeira vez que tocam
# e guardados aqui, já com o volume aplicado: o ``winsound`` também não tem
# controle de volume.
def wav_cache_dir() -> Path:
    return SOUNDS_DIR / ".wav"

_HIDDEN_PROCESS = getattr(subprocess, "CREATE_NO_WINDOW", 0)


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


def playable_wav(path: Path, volume: int) -> Path | None:
    """WAV pronto para o ``winsound``, convertido e guardado se preciso.

    O nome carrega a versão do arquivo e o volume: trocar o som ou mexer no
    volume gera outra conversão, e as antigas do mesmo slot são apagadas.
    """
    volume = max(1, min(100, volume))
    if path.suffix.lower() == ".wav" and volume == 100:
        return path
    try:
        stat = path.stat()
    except OSError:
        return None
    cache = wav_cache_dir()
    target = cache / f"{path.stem}@{stat.st_mtime_ns}-{stat.st_size}-{volume}.wav"
    if target.is_file():
        return target
    cache.mkdir(parents=True, exist_ok=True)
    for old in cache.glob(f"{path.stem}@*.wav"):
        old.unlink(missing_ok=True)
    partial = target.with_name(f".{target.name}")
    try:
        result = subprocess.run(
            ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(path),
             "-af", f"volume={volume / 100:.2f}", "-ar", "48000", "-c:a", "pcm_s16le",
             "-f", "wav", str(partial)],
            check=False, capture_output=True, timeout=30, creationflags=_HIDDEN_PROCESS)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not partial.is_file():
        partial.unlink(missing_ok=True)
        return None
    partial.replace(target)
    return target


def prepare(volume: int) -> None:
    """Converte de antemão tudo que o Windows vai precisar tocar.

    Chamado quando a pessoa salva no app — aplica um pacote, escolhe um
    arquivo, muda o volume —, para que o primeiro atalho da partida só toque
    o que já está pronto, sem ffmpeg nenhum rodando durante o jogo.
    """
    if os.name != "nt" or volume <= 0:
        return
    for slot in SLOTS:
        path = custom_sound(slot)
        if path is not None:
            playable_wav(path, volume)


def play(slot: str, volume: int = 100) -> bool:
    """Toca o som do slot sem esperar o fim. Devolve se conseguiu disparar.

    ``volume`` vai de 0 a 100. No Windows vale o arquivo escolhido na
    interface, convertido para WAV quando é outro formato — normalmente já
    por :func:`prepare`; sem ele, ou sem ffmpeg para converter, quem chamou
    segue com a melodia de bipes.
    """
    if volume <= 0:
        return True
    if os.name == "nt":
        path = custom_sound(slot)
        wav = playable_wav(path, volume) if path is not None else None
        if wav is None:
            return False
        try:
            import winsound

            winsound.PlaySound(str(wav), winsound.SND_FILENAME | winsound.SND_ASYNC)
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
