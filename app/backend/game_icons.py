"""Ícones dos jogos da biblioteca, buscados na primeira vez e guardados em disco.

A fonte preferida é o SteamGridDB, que tem ícones quadrados de quase tudo —
inclusive o que não está na Steam, como Roblox e Minecraft — e responde igual
no Linux e no Windows. A API dele exige uma chave pessoal, que cada um cola nas
configurações; ela nunca volta para a interface, porque o Lume pode estar
aberto para a rede remota. Sem chave, a capa vertical da loja da Steam cobre os
jogos de lá. Só biblioteca padrão: o Lumini não instala mais nada.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

from .main_paths import CONFIG_DIR, MEDIA_CACHE_DIR

KEY_FILE = CONFIG_DIR / "steamgriddb.key"
CACHE_DIR = MEDIA_CACHE_DIR / "game-icons"
INDEX = CACHE_DIR / "index.json"

SGDB_API = "https://www.steamgriddb.com/api/v2"
STEAM_SEARCH = "https://store.steampowered.com/api/storesearch/"
STEAM_ASSETS = "https://shared.cloudflare.steamstatic.com/store_item_assets/steam/apps"

# Um jogo que não foi encontrado é perguntado de novo depois de uma semana:
# o nome pode ter sido corrigido, ou o jogo, chegado ao SteamGridDB.
MISSING_RETRY_SECONDS = 7 * 86400
MAX_IMAGE_BYTES = 5 * 1024 * 1024
TIMEOUT = 8
USER_AGENT = "Lume-GameIcons"
_HIDDEN_PROCESS = getattr(subprocess, "CREATE_NO_WINDOW", 0)

Kind = Literal["icon", "cover"]
_lock = threading.Lock()


# --- chave ------------------------------------------------------------------

def read_key() -> str:
    try:
        return KEY_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def save_key(key: str) -> None:
    """Grava a chave (ou a apaga, se vazia) e libera nova busca dos ausentes."""
    key = key.strip()
    if key:
        KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        KEY_FILE.write_text(key + "\n", encoding="utf-8")
        try:
            os.chmod(KEY_FILE, 0o600)
        except OSError:
            pass
    else:
        KEY_FILE.unlink(missing_ok=True)
    # Quem ficou sem ícone por falta de chave merece outra chance já.
    forget_missing()


def forget_missing() -> int:
    """Esquece os jogos marcados como "sem ícone", para buscá-los já.

    Sem isso, um jogo não encontrado só é perguntado de novo depois de
    ``MISSING_RETRY_SECONDS``. Devolve quantos voltam para a fila.
    """
    with _lock:
        index = _read_index()
        kept = {name: entry for name, entry in index.items() if entry.get("file")}
        _write_index(kept)
    return len(index) - len(kept)


def verify_key(key: str) -> bool | None:
    """``True``/``False`` se o SteamGridDB aceitou a chave; ``None`` sem rede."""
    try:
        _json(f"{SGDB_API}/search/autocomplete/minecraft", key.strip())
        return True
    except urllib.error.HTTPError as error:
        return False if error.code in {401, 403} else None
    except (OSError, ValueError):
        return None


# --- cache ------------------------------------------------------------------

def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", name.casefold()).strip()


def _read_index() -> dict[str, dict]:
    try:
        data = json.loads(INDEX.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_index(index: dict[str, dict]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    temporary = INDEX.with_suffix(".tmp")
    temporary.write_text(json.dumps(index, ensure_ascii=False, indent=1), encoding="utf-8")
    temporary.replace(INDEX)


def cached_file(file_name: str) -> Path | None:
    """Caminho de um ícone já baixado; só nomes gerados aqui são aceitos."""
    if not re.fullmatch(r"[0-9a-f]{24}\.(png|jpg|webp)", file_name):
        return None
    path = CACHE_DIR / file_name
    return path if path.is_file() else None


# --- rede -------------------------------------------------------------------

def _get(url: str, key: str = "") -> bytes:
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json, image/*"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        body = response.read(MAX_IMAGE_BYTES + 1)
    if len(body) > MAX_IMAGE_BYTES:
        raise ValueError("resposta grande demais")
    return body


def _json(url: str, key: str = "") -> dict:
    data = json.loads(_get(url, key))
    return data if isinstance(data, dict) else {}


def _from_steamgriddb(name: str, key: str) -> tuple[str, Kind] | None:
    found = _json(f"{SGDB_API}/search/autocomplete/{urllib.parse.quote(name, safe='')}", key)
    games = found.get("data") or []
    if not games:
        return None
    game_id = int(games[0]["id"])
    # Ícones primeiro; um grid quadrado serve quando o jogo não tem ícone.
    for path, kind in ((f"icons/game/{game_id}?types=static&nsfw=false", "icon"),
                       (f"grids/game/{game_id}?dimensions=512x512,1024x1024&types=static&nsfw=false", "cover")):
        images = _json(f"{SGDB_API}/{path}", key).get("data") or []
        if images and images[0].get("url"):
            return str(images[0]["url"]), kind  # type: ignore[return-value]
    return None


def _from_steam(name: str) -> tuple[str, Kind] | None:
    query = urllib.parse.urlencode({"term": name, "l": "english", "cc": "US"})
    items = _json(f"{STEAM_SEARCH}?{query}").get("items") or []
    wanted = _normalize(name)
    # A busca da loja devolve parecidos; só um nome equivalente conta, para não
    # pôr a capa de "Minecraft Dungeons" no Minecraft.
    match = next((item for item in items if _normalize(str(item.get("name", ""))) == wanted), None)
    if not match:
        return None
    return f"{STEAM_ASSETS}/{int(match['id'])}/library_600x900.jpg", "cover"


def _ico_to_png(body: bytes) -> bytes:
    """Converte um ``.ico`` na sua maior imagem, em PNG.

    Muitos jogos só têm ícone em ``.ico`` no SteamGridDB — Sea of Thieves, por
    exemplo —, e o navegador não mostra o formato de forma confiável. Recusá-lo
    deixava o jogo marcado como "sem ícone" por uma semana. O ffmpeg já está em
    qualquer instalação (é o gravador) e escolhe sozinho a maior resolução.
    """
    # Arquivo, não pipe: o demuxer de .ico pula pelo índice de imagens, e numa
    # entrada sem seek ele desiste em vários ícones reais ("Invalid data").
    with tempfile.TemporaryDirectory(prefix="lume-ico-") as directory:
        source = Path(directory) / "icone.ico"
        source.write_bytes(body)
        result = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-i", str(source),
             "-frames:v", "1", "-f", "image2pipe", "-c:v", "png", "pipe:1"],
            capture_output=True, timeout=20, creationflags=_HIDDEN_PROCESS)
    if result.returncode != 0 or not result.stdout.startswith(b"\x89PNG"):
        raise ValueError("não foi possível converter o .ico")
    return result.stdout


def _download(url: str, name: str) -> str:
    body = _get(url)
    if body.startswith(b"\x00\x00\x01\x00"):
        body = _ico_to_png(body)
    if body.startswith(b"\x89PNG"):
        suffix = "png"
    elif body.startswith(b"\xff\xd8"):
        suffix = "jpg"
    elif body[8:12] == b"WEBP":
        suffix = "webp"
    else:
        raise ValueError("não é uma imagem")
    file_name = f"{hashlib.sha256(_normalize(name).encode()).hexdigest()[:24]}.{suffix}"
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    (CACHE_DIR / file_name).write_bytes(body)
    return file_name


def _fetch(name: str, key: str) -> dict:
    sources = []
    if key:
        sources.append(lambda: _from_steamgriddb(name, key))
    sources.append(lambda: _from_steam(name))
    for source in sources:
        try:
            found = source()
            if found:
                url, kind = found
                return {"file": _download(url, name), "kind": kind, "fetched_at": time.time()}
        except (OSError, ValueError, KeyError, TypeError, urllib.error.URLError):
            # Uma fonte fora do ar não impede a próxima.
            continue
    return {"file": "", "fetched_at": time.time()}


# --- consulta ---------------------------------------------------------------

def lookup(names: list[str], fetch: bool = True) -> dict[str, dict | None]:
    """``{nome: {"file", "kind"}}`` para cada jogo; ``None`` quando não há ícone."""
    key = read_key()
    wanted = {name: _normalize(name) for name in names if _normalize(name)}
    with _lock:
        index = _read_index()
    now = time.time()
    stale = [name for name, normal in wanted.items()
             if normal not in index
             or (not index[normal].get("file")
                 and now - float(index[normal].get("fetched_at", 0)) > MISSING_RETRY_SECONDS)
             or (index[normal].get("file") and not cached_file(index[normal]["file"]))]
    if fetch and stale:
        with ThreadPoolExecutor(max_workers=4) as pool:
            fresh = dict(zip((wanted[name] for name in stale),
                             pool.map(lambda name: _fetch(name, key), stale)))
        with _lock:
            index = {**_read_index(), **fresh}
            _write_index(index)
    result: dict[str, dict | None] = {}
    for name, normal in wanted.items():
        entry = index.get(normal) or {}
        file_name = entry.get("file") or ""
        result[name] = {"file": file_name, "kind": entry.get("kind", "icon")} \
            if file_name and cached_file(file_name) else None
    return result
