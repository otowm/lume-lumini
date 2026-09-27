"""Atualizações opt-in: baixar pelo botão, aplicar antes de iniciar o gravador.

Este módulo usa só a biblioteca padrão. Nunca troca o código de um backend em
execução: o serviço de login (ou lançador Windows) aplica uma versão preparada.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from .main_paths import CONFIG_DIR
from .mode import e_lumini
from .runtime import exclusive_lock

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = "https://github.com/otowm/lume-lumini.git"
COMMITS_URL = "https://api.github.com/repos/otowm/lume-lumini/commits/main"
DOWNLOAD_URL = "https://github.com/otowm/lume-lumini/archive/refs/heads/main.zip"
STATE = CONFIG_DIR / "updates.json"
SCRIPTS = {
    "audio-bus.sh": "audio-bus.sh", "game-video-loop": "captura-video-loop.sh",
    "add-video-marker": "lume-add-video-marker", "toggle-video-hud": "lume-toggle-video-hud",
    "lume-audio-diag": "lume-audio-diag",
}


class UpdateError(RuntimeError):
    pass


def git(*args: str, timeout: int = 30) -> str:
    result = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True,
                            text=True, timeout=timeout,
                            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
    if result.returncode:
        raise UpdateError("O Git não conseguiu concluir a atualização. Verifique a conexão e as alterações locais.")
    return result.stdout.strip()


def read_state() -> dict:
    try:
        state = json.loads(STATE.read_text(encoding="utf-8"))
        return state if isinstance(state, dict) else {}
    except (OSError, ValueError):
        return {}


def write_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    temporary.replace(STATE)


def installation() -> tuple[str, str]:
    if not (ROOT / ".git").exists() or not shutil.which("git"):
        return "", "Esta instalação veio de um ZIP ou não tem Git. Baixe a nova versão pelo botão abaixo."
    current = git("rev-parse", "HEAD")
    if git("branch", "--show-current") != "main":
        return current, "Atualização pelo app disponível apenas na branch main."
    remote = git("remote", "get-url", "origin").removesuffix(".git")
    if remote not in {REPOSITORY.removesuffix(".git"), "git@github.com:otowm/lume-lumini"}:
        return current, "O repositório desta instalação não é o oficial."
    if git("status", "--porcelain", "--untracked-files=no"):
        return current, "Há alterações locais no código. Elas serão preservadas; atualize manualmente."
    return current, ""


def check(force: bool = False) -> dict:
    with exclusive_lock(STATE.with_suffix(".lock")) as acquired:
        state = read_state()
        if acquired and (force or time.time() - state.get("checked_at", 0) > 21600):
            try:
                request = urllib.request.Request(COMMITS_URL, headers={"User-Agent": "Lumini-Updater", "Accept": "application/vnd.github+json"})
                with urllib.request.urlopen(request, timeout=8) as response:
                    latest = json.load(response)
                sha = latest["sha"]
                if not re.fullmatch(r"[0-9a-f]{40}", sha):
                    raise ValueError("versão inválida")
                state.update(latest=sha, title=latest["commit"]["message"].splitlines()[0], error="")
            except (OSError, ValueError, KeyError):
                state["error"] = "Não foi possível verificar agora. O gravador continua funcionando normalmente."
            state["checked_at"] = time.time()
            write_state(state)
    try:
        current, reason = installation()
    except (OSError, subprocess.SubprocessError, UpdateError):
        current, reason = "", "Não foi possível verificar a instalação local."
    return {**state, "current": current, "available": bool(state.get("latest") and state["latest"] != current),
            "can_prepare": bool(current and not reason), "can_install_now": can_install_now(),
            "reason": reason, "download_url": DOWNLOAD_URL}


def prepare(version: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{40}", version):
        raise UpdateError("Versão inválida.")
    with exclusive_lock(STATE.with_suffix(".lock")) as acquired:
        if not acquired:
            raise UpdateError("Já existe uma verificação ou atualização em andamento.")
        current, reason = installation()
        if reason:
            raise UpdateError(reason)
        state = read_state()
        if version != state.get("latest"):
            raise UpdateError("Verifique a versão disponível novamente antes de atualizar.")
        git("fetch", "--no-tags", REPOSITORY, "main", timeout=60)
        git("merge-base", "--is-ancestor", version, "FETCH_HEAD")
        git("merge-base", "--is-ancestor", current, version)
        if version == current:
            raise UpdateError("Esta versão já está instalada.")
        check_compatible(current, version)
        state.update(pending=version, prepared_from=current, error="", message="Atualização preparada. Reinicie o computador para instalar.")
        write_state(state)
        return state


def cancel() -> dict:
    with exclusive_lock(STATE.with_suffix(".lock")) as acquired:
        if not acquired:
            raise UpdateError("A atualização está em andamento. Aguarde.")
        state = read_state()
        state.update(pending="", message="Atualização cancelada.", error="")
        write_state(state)
        return state


def check_compatible(current: str, target: str) -> None:
    changed = git("diff", "--name-only", current, target).splitlines()
    if any(name.startswith(("systemd/", "requirements")) for name in changed):
        raise UpdateError("Esta versão muda serviços ou dependências. Atualize com git pull e rode o instalador uma vez.")


RUNTIME_UNITS = ("lume.service", "captura-dia-video.service", "captura-dia-hud.service",
                 "captura-dia-hotkey.service")
INSTALL_NOW_UNIT = "lumini-instalar-agora"


def can_install_now() -> bool:
    # No Windows quem aplica é o lançador do login; aqui, o systemd do usuário.
    return os.name != "nt" and shutil.which("systemd-run") is not None


def install_now() -> dict:
    """Aplica a versão preparada sem reiniciar o computador.

    O backend que atende o pedido é um dos serviços parados no caminho, então
    o trabalho roda numa unit transitória, fora do cgroup do ``lume.service``:
    para o gravador, roda o mesmo ``lumini-update.service`` do boot e religa
    só o que estava ligado — uma captura pausada continua pausada. O
    ``restart`` é necessário porque a unit de atualização fica ``active``
    (RemainAfterExit) desde o boot, e um ``start`` não faria nada.
    """
    if not can_install_now():
        raise UpdateError("Neste sistema a atualização é instalada na próxima inicialização.")
    if not read_state().get("pending"):
        raise UpdateError("Prepare a atualização antes de instalar.")
    result = subprocess.run(["systemctl", "--user", "is-active", *RUNTIME_UNITS],
                            capture_output=True, text=True, timeout=5)
    running = [unit for unit, state in zip(RUNTIME_UNITS, result.stdout.splitlines())
               if state in {"active", "activating", "reloading"}]
    units = " ".join(running)
    # A pausa inicial deixa a resposta HTTP chegar antes de o backend parar. O
    # religamento não depende da atualização dar certo: com falha, a versão
    # antiga volta e o erro fica no estado para a interface mostrar.
    script = (f"sleep 1; systemctl --user stop {units}; "
              "systemctl --user restart lumini-update.service; "
              f"systemctl --user start {units}")
    started = subprocess.run(
        ["systemd-run", "--user", "--collect", f"--unit={INSTALL_NOW_UNIT}",
         "--description=Lumini - instalar atualização agora", "/bin/sh", "-c", script],
        capture_output=True, text=True, timeout=15)
    if started.returncode:
        raise UpdateError("Não foi possível iniciar a instalação. Talvez ela já esteja em andamento.")
    state = read_state()
    state.update(message="Instalando a atualização. O Lumini volta em alguns segundos.", error="")
    write_state(state)
    return state


def runtime_active() -> bool:
    # Portas personalizadas também são verificadas; no Linux, as units cobrem
    # instalações que tenham escolhido outro endereço/porta por um drop-in.
    try:
        with socket.create_connection(("127.0.0.1", int(os.environ.get("LUME_PORT", "8876"))), timeout=.3):
            return True
    except OSError:
        pass
    if os.name != "nt":
        result = subprocess.run(["systemctl", "--user", "is-active", "lume.service",
                                 "captura-dia-video.service", "captura-dia-hud.service",
                                 "captura-dia-hotkey.service"], capture_output=True, text=True, timeout=5)
        states = result.stdout.splitlines()
        if not states:
            raise UpdateError("Não foi possível verificar se o gravador está parado. A atualização foi adiada.")
        return any(state in {"active", "reloading", "deactivating"} for state in states)
    return False


def apply_pending() -> bool:
    """Retorna True se trocou a versão. Falhas mantêm o pedido para nova tentativa."""
    if not e_lumini() or not read_state().get("pending"):
        return False
    with exclusive_lock(STATE.with_suffix(".lock")) as acquired:
        if not acquired or runtime_active():
            return False
        state = read_state()
        target = state.get("pending", "")
        if not re.fullmatch(r"[0-9a-f]{40}", target):
            raise UpdateError("Versão preparada inválida.")
        current, reason = installation()
        if current == target:
            state.update(pending="", error="", message="A versão preparada já está instalada.")
            write_state(state)
            return False
        if reason or current != state.get("prepared_from"):
            raise UpdateError(reason or "A instalação mudou desde o pedido. Verifique e prepare a atualização novamente.")
        git("merge-base", "--is-ancestor", current, target)
        # Mudanças de infraestrutura exigem reinstalação. Não executamos um
        # instalador que possa reabrir a rede ou reativar serviços desabilitados.
        check_compatible(current, target)
        bin_dir = Path.home() / "bin"
        originals = {name: ((bin_dir / name).read_bytes() if (bin_dir / name).exists() else None)
                     for name in SCRIPTS.values()} if os.name != "nt" else {}
        merged = False
        try:
            git("merge", "--ff-only", target)
            merged = True
            if os.name != "nt":
                bin_dir.mkdir(parents=True, exist_ok=True)
                for source, destination in SCRIPTS.items():
                    shutil.copyfile(ROOT / "bin" / source, bin_dir / destination)
                    (bin_dir / destination).chmod(0o755)
            state.update(pending="", current=target, error="", message="Atualização instalada com sucesso.")
            write_state(state)
            return True
        except Exception:
            if merged:
                git("reset", "--keep", current)
            for name, content in originals.items():
                path = bin_dir / name
                if content is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(content)
            raise


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.apply:
        try:
            apply_pending()
        except Exception as exc:
            state = read_state()
            state["error"] = str(exc) if isinstance(exc, UpdateError) else "A atualização não foi concluída. Consulte os logs antes de tentar novamente."
            write_state(state)
            print(state["error"], file=sys.stderr)


if __name__ == "__main__":
    main()
