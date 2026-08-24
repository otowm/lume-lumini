"""Instância dedicada do OBS para a gravação de jogos no Windows.

No Linux a gravação seletiva usa ``gpu-screen-recorder``. No Windows o
equivalente em desempenho é o *Game Capture* do OBS, que engancha na cadeia de
apresentação do jogo e copia o quadro na própria GPU. As alternativas medidas
nesta máquina não servem: ``gdigrab`` captura pela CPU e nem enxerga fullscreen
exclusivo, e o ``ddagrab`` só fechou com um retorno de cada quadro para a CPU —
meio gigabyte por segundo enquanto o jogo roda.

O OBS aqui é **uma cópia portátil, exclusiva do Lume**, em ``~/.lume-obs``. A
razão é isolamento: quem usa OBS para transmitir tem cenas montadas para live,
e mandar o Lume gravar a cena atual gravaria a câmera e o overlay em vez do
jogo. Em modo portátil a instância guarda a própria configuração dentro da
pasta, então as duas nunca dividem coleção, perfil ou ``global.ini`` — e a
instalação de live não é lida nem escrita em momento algum.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import os
import secrets
import shutil
import socket
import subprocess
import time
from pathlib import Path

_HIDDEN_PROCESS = getattr(subprocess, "CREATE_NO_WINDOW", 0)

from ..backend.main_paths import VIDEO_DIR

#: Cópia portátil do OBS usada só pelo Lume.
OBS_HOME = Path(os.environ.get("LUME_OBS_HOME", Path.home() / ".lume-obs"))
OBS_EXE = OBS_HOME / "bin" / "64bit" / "obs64.exe"
OBS_CONFIG = OBS_HOME / "config" / "obs-studio"
PASSWORD_FILE = OBS_HOME / "websocket-password.txt"

PROFILE = "Lume"
COLLECTION = "Lume"
SCENE = "Captura"
#: Cena e entrada dividem o mesmo espaço de nomes no OBS: não podem coincidir.
GAME_INPUT = "Jogo"
WINDOW_INPUT = "Janela (fallback)"
SYSTEM_AUDIO_INPUT = "Áudio do aplicativo"
FALLBACK_AUDIO_INPUT = "Som do sistema (fallback)"
DISCORD_AUDIO_INPUT = "Discord"
MIC_INPUT = "Microfone"
# Reforço moderado para compensar microfones cujo nível de entrada fica baixo
# no OBS dedicado. É reaplicado ao preparar a cena, sem afetar os outros stems.
MIC_VOLUME_DB = 6.0

#: Porta separada da instância do usuário (que usa 4455 por padrão).
DEFAULT_PORT = int(os.environ.get("LUME_OBS_PORT", "4466"))

_INSTALL_CANDIDATES = (
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "obs-studio",
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "obs-studio",
)


class ObsError(RuntimeError):
    """Falha ao falar com o OBS ou ao prepará-lo."""


# --- localização e provisionamento -----------------------------------------

def find_installation() -> Path | None:
    """Onde o OBS do usuário está instalado, se estiver."""
    for candidate in _INSTALL_CANDIDATES:
        if (candidate / "bin" / "64bit" / "obs64.exe").is_file():
            return candidate
    return None


def is_provisioned() -> bool:
    return OBS_EXE.is_file() and (OBS_HOME / "portable_mode.txt").is_file()


def password() -> str:
    """Senha do websocket da instância dedicada, criada na primeira vez."""
    if PASSWORD_FILE.is_file():
        existing = PASSWORD_FILE.read_text(encoding="utf-8").strip()
        if existing:
            return existing
    generated = secrets.token_urlsafe(18)
    PASSWORD_FILE.parent.mkdir(parents=True, exist_ok=True)
    PASSWORD_FILE.write_text(generated, encoding="utf-8")
    return generated


def _copy_installation(source: Path) -> None:
    """Duplica a instalação do OBS. Usa robocopy, que é ordens de grandeza
    mais rápido que copytree para ~475 MB, e cai no Python se não houver."""
    OBS_HOME.mkdir(parents=True, exist_ok=True)
    robocopy = shutil.which("robocopy")
    if robocopy:
        result = subprocess.run(
            [robocopy, str(source), str(OBS_HOME), "/E", "/NFL", "/NDL",
             "/NJH", "/NJS", "/NP", "/MT:8"],
            check=False, capture_output=True, timeout=900,
            creationflags=_HIDDEN_PROCESS)
        # robocopy usa 0-7 para sucesso; 8+ é falha real.
        if result.returncode < 8:
            return
    shutil.copytree(source, OBS_HOME, dirs_exist_ok=True)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_config(fps: int = 60, geometry: str = "1920x1080",
                 retention_minutes: int = 60, replay_seconds: int = 60,
                 codec: str = "h264") -> None:
    """Escreve o perfil e as preferências da instância dedicada."""
    width, _, height = geometry.partition("x")
    try:
        width_i, height_i = int(width), int(height)
    except ValueError:
        width_i, height_i = 1920, 1080
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)

    _write(OBS_HOME / "portable_mode.txt", "")

    _write(OBS_CONFIG / "global.ini", "\n".join([
        "[General]", "MaxLogs=5", "ProcessPriority=Normal",
        "EnableAutoUpdates=false", "BrowserHWAccel=true", "",
        "[Video]", "Renderer=Direct3D 11", "",
        "[Audio]", "DisableAudioDucking=true", "",
    ]))

    # FirstRun=true evita o assistente de configuração inicial, que abriria uma
    # janela modal e travaria a instância antes do websocket subir.
    _write(OBS_CONFIG / "user.ini", "\n".join([
        "[General]", "ConfirmOnExit=false", "FirstRun=true", "",
        "[BasicWindow]", "SysTrayEnabled=true", "SysTrayWhenStarted=true",
        "SysTrayMinimizeToTray=true", "WarnBeforeStoppingRecord=false", "",
        "[Basic]", f"Profile={PROFILE}", f"ProfileDir={PROFILE}",
        f"SceneCollection={COLLECTION}", f"SceneCollectionFile={COLLECTION}",
        "ConfigOnNewProfile=false", "",
    ]))

    recording_encoder = "amd_hevc" if codec.lower() in {"hevc", "h265"} else "amd"
    _write(OBS_CONFIG / "basic" / "profiles" / PROFILE / "basic.ini", "\n".join([
        "[General]", f"Name={PROFILE}", "",
        "[Output]", "Mode=Simple",
        "FilenameFormatting=%CCYY-%MM-%DD_%hh-%mm-%ss", "",
        "[SimpleOutput]",
        f"FilePath={VIDEO_DIR.as_posix()}",
        "RecFormat2=mkv", "RecQuality=Small",
        # HEVC/AVC via AMF usa o codificador da GPU. As faixas de áudio não
        # são misturadas nem convertidas para mono por esta configuração.
        f"RecEncoder={recording_encoder}", "RecAudioEncoder=aac",
        # Faixa 1 é a mixagem para reprodução comum. As faixas 2–4 preservam
        # os stems editáveis: microfone, Discord e aplicativo/sistema.
        "VBitrate=6000", "ABitrate=160", "RecTracks=15", "AMDPreset=balanced",
        "RecRB=true", f"RecRBTime={max(10, min(300, replay_seconds))}",
        "RecRBSize=1024", "RecRBPrefix=lume", "",
        "[Video]", f"BaseCX={width_i}", f"BaseCY={height_i}",
        f"OutputCX={width_i}", f"OutputCY={height_i}",
        "FPSType=0", f"FPSCommon={fps}", "ColorFormat=NV12",
        "ColorSpace=709", "ColorRange=Partial", "",
        "[Audio]", "SampleRate=48000", "ChannelSetup=Stereo", "",
        "[AdvOut]", "Track1Name=Mixagem", "Track2Name=Microfone",
        "Track3Name=Discord", "Track4Name=Sistema", "",
    ]))

    _write(OBS_CONFIG / "plugin_config" / "obs-websocket" / "config.json",
           json.dumps({"alerts_enabled": False, "auth_required": True,
                       "first_load": False, "server_enabled": True,
                       "server_password": password(),
                       "server_port": DEFAULT_PORT}, indent=2))


def provision(fps: int = 60, geometry: str = "1920x1080",
              retention_minutes: int = 60, replay_seconds: int = 60,
              codec: str = "h264") -> Path:
    """Garante a cópia portátil configurada; devolve a raiz dela."""
    if not OBS_EXE.is_file():
        source = find_installation()
        if source is None:
            raise ObsError(
                "OBS Studio não encontrado. Instale de https://obsproject.com "
                "— o Lume faz uma cópia própria e não mexe na sua configuração.")
        _copy_installation(source)
        if not OBS_EXE.is_file():
            raise ObsError(f"A cópia do OBS falhou (esperado {OBS_EXE}).")
    write_config(fps=fps, geometry=geometry, retention_minutes=retention_minutes,
                 replay_seconds=replay_seconds, codec=codec)
    return OBS_HOME


# --- ciclo de vida do processo ---------------------------------------------

def port_open(port: int = DEFAULT_PORT, timeout: float = 0.4) -> bool:
    with socket.socket() as probe:
        probe.settimeout(timeout)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def _process_path(pid: int) -> str:
    """Caminho do executável de um processo, ou vazio se não der para consultar."""
    import ctypes

    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED
    if not handle:
        return ""
    try:
        size = ctypes.c_uint(32768)
        buffer = ctypes.create_unicode_buffer(size.value)
        if ctypes.windll.kernel32.QueryFullProcessImageNameW(
                handle, 0, buffer, ctypes.byref(size)):
            return buffer.value
        return ""
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def running_pid() -> int | None:
    """PID da instância dedicada, distinguindo-a da do usuário pelo caminho.

    Enumera processos pela API do Windows em vez de chamar ``wmic``, que foi
    removido nas versões recentes do sistema, ou o PowerShell, que custa meio
    segundo por consulta.
    """
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD),
                    ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
                    ("szExeFile", ctypes.c_wchar * 260)]

    kernel32 = ctypes.windll.kernel32
    snapshot = kernel32.CreateToolhelp32Snapshot(0x2, 0)  # TH32CS_SNAPPROCESS
    if snapshot == -1:
        return None
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        root = str(OBS_HOME).lower()
        if not kernel32.Process32FirstW(snapshot, ctypes.byref(entry)):
            return None
        while True:
            if entry.szExeFile.lower() == "obs64.exe":
                pid = entry.th32ProcessID
                if _process_path(pid).lower().startswith(root):
                    return pid
            if not kernel32.Process32NextW(snapshot, ctypes.byref(entry)):
                return None
    finally:
        kernel32.CloseHandle(snapshot)


def ready(timeout: float = 3.0) -> bool:
    """O OBS já aceita comandos de verdade?

    A porta abrir não basta: o obs-websocket começa a atender antes de o OBS
    terminar de carregar, e nesse intervalo qualquer pedido volta com "OBS is
    not ready to perform the request".
    """
    try:
        call("GetVersion")
        return True
    except (ObsError, OSError):
        return False


def launch(wait_seconds: int = 60) -> None:
    """Sobe a instância dedicada e espera até ela aceitar comandos."""
    if port_open() and ready():
        return
    if not is_provisioned():
        raise ObsError("A instância dedicada do OBS ainda não foi preparada.")

    if port_open():
        # Já está subindo; só falta ficar pronta.
        _wait_until_ready(wait_seconds)
        return

    argv = [
        str(OBS_EXE), "--multi", "--minimize-to-tray", "--disable-shutdown-check",
        "--disable-updater", f"--collection={COLLECTION}", f"--profile={PROFILE}",
        f"--websocket_port={DEFAULT_PORT}", f"--websocket_password={password()}",
    ]
    # O OBS resolve `data/` e os plugins a partir do diretório do executável.
    subprocess.Popen(argv, cwd=str(OBS_EXE.parent),
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))

    _wait_until_ready(wait_seconds)


def _wait_until_ready(wait_seconds: float) -> None:
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        if port_open() and ready():
            return
        time.sleep(0.5)
    raise ObsError(
        f"O OBS dedicado não ficou pronto na porta {DEFAULT_PORT} "
        f"em {wait_seconds:.0f}s.")


def stop() -> None:
    """Encerra a instância dedicada, pedindo com educação antes de forçar."""
    pid = running_pid()
    if pid is None:
        return
    for forced in (False, True):
        argv = ["taskkill", "/PID", str(pid)] + (["/F"] if forced else [])
        try:
            subprocess.run(
                argv, check=False, capture_output=True, timeout=30,
                creationflags=_HIDDEN_PROCESS,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return
        deadline = time.monotonic() + (10 if not forced else 5)
        while time.monotonic() < deadline:
            if running_pid() is None:
                return
            time.sleep(0.5)


# --- cliente obs-websocket v5 ----------------------------------------------

async def _identify(ws, secret: str, subscriptions: int | None = None) -> None:
    """Faz o *hello/identify* do obs-websocket v5 sobre um socket já aberto.

    ``subscriptions`` é a máscara de eventos desejada. Omitir mantém o padrão do
    OBS (``All``), que de propósito **exclui** os eventos de alto volume — entre
    eles ``InputVolumeMeters``, que só chega quando pedido explicitamente.
    """
    hello = json.loads(await ws.recv())
    identify = {"op": 1, "d": {"rpcVersion": hello["d"]["rpcVersion"]}}
    if subscriptions is not None:
        identify["d"]["eventSubscriptions"] = subscriptions
    if "authentication" in hello["d"]:
        challenge = hello["d"]["authentication"]
        digest = base64.b64encode(hashlib.sha256(
            (secret + challenge["salt"]).encode()).digest()).decode()
        identify["d"]["authentication"] = base64.b64encode(hashlib.sha256(
            (digest + challenge["challenge"]).encode()).digest()).decode()
    await ws.send(json.dumps(identify))
    reply = json.loads(await ws.recv())
    if reply.get("op") != 2:
        raise ObsError(f"autenticação recusada pelo OBS: {reply}")


async def _session(requests: list[tuple[str, dict]], port: int,
                   secret: str) -> list[dict]:
    import websockets

    async with websockets.connect(f"ws://127.0.0.1:{port}", max_size=None) as ws:
        await _identify(ws, secret)

        results: list[dict] = []
        for index, (request_type, data) in enumerate(requests):
            rid = f"lume{index}"
            await ws.send(json.dumps({"op": 6, "d": {
                "requestType": request_type, "requestId": rid, "requestData": data}}))
            while True:
                message = json.loads(await ws.recv())
                if message.get("op") == 7 and message["d"]["requestId"] == rid:
                    status = message["d"]["requestStatus"]
                    if not status["result"]:
                        raise ObsError(
                            f"{request_type}: {status.get('comment') or status['code']}")
                    results.append(message["d"].get("responseData") or {})
                    break
        return results


def call(request_type: str, data: dict | None = None,
         port: int = DEFAULT_PORT) -> dict:
    """Uma requisição ao OBS dedicado.

    Cada chamada abre e fecha a conexão. É deliberado: as chamadas acontecem
    só nas transições (começou/parou de gravar), então o custo é irrelevante
    perto de manter um socket vivo e ter que tratá-lo quando o OBS reinicia.
    """
    return batch([(request_type, data or {})], port=port)[0]


def batch(requests: list[tuple[str, dict]], port: int = DEFAULT_PORT) -> list[dict]:
    """Várias requisições numa conexão só."""
    return asyncio.run(_session(requests, port, password()))


# --- conexão persistente (medidores da HUD) ---------------------------------
#
# Máscaras de evento do obs-websocket v5. As três primeiras cabem em ``All``;
# ``InputVolumeMeters`` e ``InputActiveStateChanged`` **não** — são classificadas
# como alto volume e só chegam se pedidas nominalmente no Identify.
EVENT_OUTPUTS = 1 << 6
EVENT_INPUT_VOLUME_METERS = 1 << 16
EVENT_INPUT_ACTIVE_STATE = 1 << 17

#: O que a HUD precisa: estado da gravação, medidores e engate das capturas.
HUD_SUBSCRIPTIONS = EVENT_OUTPUTS | EVENT_INPUT_VOLUME_METERS | EVENT_INPUT_ACTIVE_STATE


async def _stream_session(on_event, requests, on_results, subscriptions: int,
                          tick_seconds: float, should_stop, port: int,
                          secret: str) -> None:
    import websockets

    async with websockets.connect(f"ws://127.0.0.1:{port}", max_size=None) as ws:
        await _identify(ws, secret, subscriptions)
        loop = asyncio.get_running_loop()
        pending: dict[str, asyncio.Future] = {}
        counter = 0

        async def receive() -> None:
            # Termina sozinho quando o OBS fecha o socket — é assim que a queda
            # da instância vira reconexão lá em cima, sem precisar de timeout.
            async for raw in ws:
                message = json.loads(raw)
                if message.get("op") == 5:
                    on_event(message["d"].get("eventType", ""),
                             message["d"].get("eventData") or {})
                elif message.get("op") == 7:
                    waiting = pending.pop(message["d"].get("requestId", ""), None)
                    if waiting is not None and not waiting.done():
                        waiting.set_result(message["d"])

        async def ask(request_type: str, data: dict) -> dict | None:
            nonlocal counter
            counter += 1
            rid = f"lume-hud{counter}"
            waiting = loop.create_future()
            pending[rid] = waiting
            await ws.send(json.dumps({"op": 6, "d": {
                "requestType": request_type, "requestId": rid, "requestData": data}}))
            try:
                payload = await asyncio.wait_for(waiting, 5)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pending.pop(rid, None)
                return None
            if not (payload.get("requestStatus") or {}).get("result"):
                return None
            return payload.get("responseData") or {}

        async def tick() -> None:
            while True:
                results = [await ask(request_type, data or {})
                           for request_type, data in requests()]
                on_results(results)
                await asyncio.sleep(tick_seconds)

        async def watch_stop() -> None:
            while not should_stop():
                await asyncio.sleep(0.2)

        tasks = [asyncio.create_task(coro())
                 for coro in (receive, tick, watch_stop)]
        try:
            done, unfinished = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED)
        finally:
            for task in tasks:
                task.cancel()
            # Recolher o resultado das canceladas importa: quando o OBS fecha o
            # socket, a tarefa de leitura periódica morre com ``ConnectionClosed``
            # antes de ser cancelada, e sem isto o asyncio despeja um
            # "Task exception was never retrieved" a cada parada.
            await asyncio.gather(*tasks, return_exceptions=True)
        for task in done:
            # Propaga a exceção real (socket caiu, OBS recusou) para quem chamou
            # decidir se reconecta; parada pedida sai como retorno normal.
            task.result()


def stream(*, on_event, requests, on_results, should_stop,
           subscriptions: int = HUD_SUBSCRIPTIONS, tick_seconds: float = 1.0,
           port: int = DEFAULT_PORT) -> None:
    """Mantém uma conexão viva com o OBS, entregando eventos e leituras.

    Ao contrário de :func:`call`, que abre e fecha um socket por requisição,
    aqui a conexão persiste — os medidores de volume chegam a ~20 Hz e não
    sobreviveriam a um handshake por leitura.

    Os quatro callbacks são **síncronos** de propósito: quem consome isto é a
    HUD, que só precisa copiar números para dentro de uma estrutura protegida
    por lock. Manter asyncio confinado a este módulo evita contaminar o resto do
    app com corrotinas por causa de um detalhe de transporte.

    - ``on_event(tipo, dados)`` — cada evento assinado em ``subscriptions``.
    - ``requests()`` — devolve ``[(tipo, dados)]`` a cada ``tick_seconds``, para
      o que não chega por evento (o estado inicial, sobretudo).
    - ``on_results(resultados)`` — respostas na ordem pedida; ``None`` onde a
      requisição falhou.
    - ``should_stop()`` — consultado periodicamente para encerrar.

    Bloqueia até a parada ser pedida ou a conexão cair (aí propaga o erro).
    """
    asyncio.run(_stream_session(on_event, requests, on_results, subscriptions,
                                tick_seconds, should_stop, port, password()))


# --- cena de captura --------------------------------------------------------

def ensure_scene() -> bool:
    """Garante a cena com Game Capture, som do sistema e microfone.

    Devolve ``True`` se algo foi criado — nesse caso a instância **precisa ser
    reiniciada** antes de gravar: com as fontes recém-criadas o hook falha com
    ``init_pipe: failed to start pipe`` até o OBS subir de novo já com elas.
    """
    scenes = [s["sceneName"] for s in call("GetSceneList")["scenes"]]
    changed = False

    if SCENE not in scenes:
        call("CreateScene", {"sceneName": SCENE})
        scenes.append(SCENE)
        changed = True

    # Cenas sobrando atrapalham: uma cena com o nome de uma fonte impede a
    # criação da fonte, já que ambas dividem o espaço de nomes.
    for leftover in list(scenes):
        if leftover != SCENE and leftover in {"Cena", "Scene", GAME_INPUT}:
            if len(scenes) > 1:
                call("RemoveScene", {"sceneName": leftover})
                scenes.remove(leftover)
                changed = True

    call("SetCurrentProgramScene", {"sceneName": SCENE})

    existing = [i["inputName"] for i in call("GetInputList")["inputs"]]
    # Remove a fonte antiga, que misturava todo o desktop na faixa principal.
    if "Som do sistema" in existing and "Som do sistema" != SYSTEM_AUDIO_INPUT:
        call("RemoveInput", {"inputName": "Som do sistema"})
        existing.remove("Som do sistema")
        changed = True
    wanted = [
        (GAME_INPUT, "game_capture", {"capture_mode": "any_fullscreen",
                                      "capture_cursor": True,
                                      "allow_transparency": False,
                                      "limit_framerate": False}),
        (WINDOW_INPUT, "window_capture", {
            "window": ":WINDOWSCLIENT:__lume_pending__.exe",
            "method": 2,
            "priority": 2,
            "capture_cursor": True,
            "client_area": True,
        }),
        (SYSTEM_AUDIO_INPUT, "wasapi_process_output_capture", {
            "window": ":Chrome_WidgetWin_1:__lume_pending__.exe", "priority": 2,
        }),
        (FALLBACK_AUDIO_INPUT, "wasapi_output_capture", {"device_id": "default"}),
        (DISCORD_AUDIO_INPUT, "wasapi_process_output_capture", {
            "window": ":Chrome_WidgetWin_1:Discord.exe", "priority": 2,
        }),
        (MIC_INPUT, "wasapi_input_capture", {"device_id": "default"}),
    ]
    for name, kind, settings in wanted:
        if name in existing:
            continue
        call("CreateInput", {"sceneName": SCENE, "inputName": name,
                             "inputKind": kind, "inputSettings": settings})
        changed = True
    # A mixagem na faixa 1 mantém o player comum audível; 2–4 são stems para
    # edição e para a análise com prioridade de origem.
    routes = {
        MIC_INPUT: {"1": True, "2": True, "3": False, "4": False, "5": False, "6": False},
        DISCORD_AUDIO_INPUT: {"1": True, "2": False, "3": True, "4": False, "5": False, "6": False},
        SYSTEM_AUDIO_INPUT: {"1": True, "2": False, "3": False, "4": True, "5": False, "6": False},
        FALLBACK_AUDIO_INPUT: {"1": True, "2": False, "3": False, "4": True, "5": False, "6": False},
    }
    for name, tracks in routes.items():
        call("SetInputAudioTracks", {"inputName": name, "inputAudioTracks": tracks})
    call("SetInputVolume", {"inputName": MIC_INPUT, "inputVolumeDb": MIC_VOLUME_DB})
    call("SetInputMute", {"inputName": FALLBACK_AUDIO_INPUT, "inputMuted": True})
    _set_capture_input(WINDOW_INPUT, False)
    _set_capture_input(GAME_INPUT, True)
    return changed


def _encode_field(value: str) -> str:
    """Escapa um campo do identificador de janela do OBS.

    O identificador é ``título:classe:executável``, então um título que contenha
    ``:`` — coisa banal, "Jogo: Episódio 2" — quebraria a divisão dos campos e o
    OBS procuraria por uma janela que não existe, sem nem tentar o hook. É a
    mesma codificação que o OBS usa internamente.
    """
    return value.replace("#", "#22").replace(":", "#3A")


def _set_capture_input(input_name: str, enabled: bool) -> None:
    """Ativa uma das fontes visuais da cena sem recriá-la durante a sessão."""
    item = call("GetSceneItemId", {"sceneName": SCENE, "sourceName": input_name})
    call("SetSceneItemEnabled", {
        "sceneName": SCENE,
        "sceneItemId": item["sceneItemId"],
        "sceneItemEnabled": enabled,
    })


def target_window(title: str, window_class: str, executable: str,
                  window_capture: bool = False) -> str:
    """Aponta o Game Capture para um app específico, casando pelo executável.

    O modo "qualquer tela cheia" parece conveniente, mas desamarra duas coisas
    que precisam andar juntas: o Lume decide gravar porque *uma* janela entrou
    em foco, e o OBS gravaria o que quer que esteja em tela cheia — podendo ser
    outra. Casar por executável (``priority=2``) grava exatamente o app que
    disparou, e sobrevive a mudanças de título durante a partida.
    """
    spec = ":".join(_encode_field(part) for part in (title, window_class, executable))
    if window_capture:
        call("SetInputSettings", {"inputName": WINDOW_INPUT, "inputSettings": {
            "window": spec,
            "method": 2,  # Windows Graphics Capture
            "priority": 2,  # WINDOW_PRIORITY_EXE
            "capture_cursor": True,
            "client_area": True,
        }})
    else:
        call("SetInputSettings", {"inputName": GAME_INPUT, "inputSettings": {
            "capture_mode": "window",
            "window": spec,
            "priority": 2,  # WINDOW_PRIORITY_EXE
            "capture_cursor": True,
        }})
    _set_capture_input(WINDOW_INPUT, window_capture)
    _set_capture_input(GAME_INPUT, not window_capture)
    call("SetInputSettings", {"inputName": SYSTEM_AUDIO_INPUT, "inputSettings": {
        "window": ":".join(_encode_field(part) for part in (title, window_class, executable)),
        "priority": 2,
    }})
    call("SetInputMute", {"inputName": SYSTEM_AUDIO_INPUT, "inputMuted": False})
    call("SetInputMute", {"inputName": FALLBACK_AUDIO_INPUT, "inputMuted": True})
    return "janela" if window_capture else "hook"


def any_fullscreen() -> None:
    """Volta o Game Capture ao modo genérico de tela cheia."""
    call("SetInputSettings", {"inputName": GAME_INPUT, "inputSettings": {
        "capture_mode": "any_fullscreen", "window": "", "capture_cursor": True,
    }})
    _set_capture_input(WINDOW_INPUT, False)
    _set_capture_input(GAME_INPUT, True)
    call("SetInputMute", {"inputName": SYSTEM_AUDIO_INPUT, "inputMuted": True})
    call("SetInputMute", {"inputName": FALLBACK_AUDIO_INPUT, "inputMuted": False})


def recording() -> bool:
    try:
        return bool(call("GetRecordStatus").get("outputActive"))
    except (ObsError, OSError):
        return False


def stop_recording_if_active() -> Path | None:
    """Encerra uma gravação em andamento; devolve o arquivo, se houver.

    Existe porque um encerramento abrupto do laço (fim de tarefa, crash) deixa
    o OBS gravando indefinidamente — a próxima gravação falharia e o disco
    encheria em silêncio.
    """
    if not recording():
        return None
    try:
        result = call("StopRecord")
    except (ObsError, OSError):
        return None
    path = result.get("outputPath")
    return Path(path) if path else None


def replay_buffer_active() -> bool:
    try:
        return bool(call("GetReplayBufferStatus").get("outputActive"))
    except (ObsError, OSError):
        return False


def stop_replay_buffer_if_active() -> bool:
    if not replay_buffer_active():
        return False
    try:
        call("StopReplayBuffer")
        return True
    except (ObsError, OSError):
        return False


def prepare(fps: int = 60, geometry: str = "1920x1080",
            retention_minutes: int = 60, replay_seconds: int = 60,
            codec: str = "h264") -> None:
    """Deixa a instância dedicada pronta para gravar, do zero se preciso."""
    provision(fps=fps, geometry=geometry, retention_minutes=retention_minutes,
              replay_seconds=replay_seconds, codec=codec)
    # O perfil é lido apenas na inicialização do OBS. Quando o serviço reinicia
    # ou o usuário troca modo/duração, uma instância dedicada antiga precisa
    # recarregar basic.ini antes de iniciar o output.
    if port_open() or running_pid():
        stop()
    launch()
    if ensure_scene():
        # Reinício obrigatório para o hook de captura enxergar as fontes novas.
        stop()
        launch()


def diagnostics() -> dict[str, object]:
    """Estado legível da instância dedicada, para a interface e o self-test."""
    info: dict[str, object] = {
        "instalacao_origem": str(find_installation() or ""),
        "copia_dedicada": str(OBS_HOME),
        "preparada": is_provisioned(),
        "porta": DEFAULT_PORT,
        "no_ar": port_open(),
    }
    if not info["no_ar"]:
        return info
    try:
        version, record, scenes = batch([
            ("GetVersion", {}), ("GetRecordStatus", {}), ("GetSceneList", {})])
        info["obs"] = version.get("obsVersion")
        info["gravando"] = record.get("outputActive")
        info["cenas"] = [s["sceneName"] for s in scenes.get("scenes", [])]
    except (ObsError, OSError) as exc:
        info["erro"] = str(exc)
    return info
