"""Host invisível do backend no login do Windows.

Executado com ``pythonw.exe`` pelo atalho da pasta Inicializar. O console
oculto permite que o supervisor continue enviando CTRL_BREAK aos gravadores,
para que WAV/MKV sejam finalizados corretamente, sem exibir terminal.
"""

from __future__ import annotations

import ctypes
import os
import socket
import sys
from pathlib import Path

import uvicorn

from .main_paths import MEDIA_ROOT
from .mode import e_lumini


def _backend_is_running(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except OSError:
        return False


def _hide_console() -> None:
    if os.name != "nt":
        return
    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    if not kernel32.GetConsoleWindow():
        kernel32.AllocConsole()
    window = kernel32.GetConsoleWindow()
    if window:
        user32.ShowWindow(window, 0)


def main() -> None:
    probe_host = "127.0.0.1"
    host = os.environ.get("LUME_BIND_HOST") or os.environ.get("LUME_HOST", "0.0.0.0")
    port = int(os.environ.get("LUME_PORT", "8876"))
    if _backend_is_running(probe_host, port):
        return
    if e_lumini():
        # Outro processo aplica antes de subir captura/HUD; ao voltar, importa
        # a versão nova em um processo novo, sem misturar módulos antigos.
        from . import updater
        before = updater.read_state().get("pending")
        if before:
            import subprocess
            try:
                subprocess.run([sys.executable, "-m", "app.backend.updater", "--apply"],
                               cwd=Path(__file__).resolve().parents[2], timeout=240)
            except (OSError, subprocess.TimeoutExpired):
                # Uma falha de atualização não impede a captura de subir.
                pass
            if not updater.read_state().get("pending"):
                os.execv(sys.executable, [sys.executable, "-m", "app.backend.windows_startup"])
    # A aplicação valida também o IP de origem e o cabeçalho Host. Escutar em
    # todas as interfaces não concede acesso ao Wi-Fi/LAN comum.
    if e_lumini():
        os.environ.setdefault("LUME_REMOTE_NETWORKS", "10.0.0.0/8,172.16.0.0/12,192.168.0.0/16")
    else:
        os.environ.setdefault("LUME_REMOTE_NETWORKS", "172.27.0.0/16,10.28.4.0/24")
        os.environ.setdefault("LUME_REMOTE_HOSTS", "172.27.181.179,10.28.4.6")
    _hide_console()
    log_dir = MEDIA_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "lume-backend.log"
    with log_path.open("a", encoding="utf-8", buffering=1) as log:
        sys.stdout = log
        sys.stderr = log
        uvicorn.run("app.backend.main:app", host=host, port=port, log_level="info")


if __name__ == "__main__":
    main()
