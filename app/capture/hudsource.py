"""Coleta do estado que a HUD mostra, com um coletor por sistema.

Mesma divisão que o resto de ``app/capture``: a interface é única e cada SO traz
a sua implementação. Quem consome (:mod:`app.capture.hud`) nunca sabe se os
números vieram do obs-websocket ou do PipeWire.

Os dois lados respondem às mesmas perguntas, mas por caminhos bem diferentes:

Windows
    Durante a gravação de jogo o ``winrecord`` está **parado** — o supervisor o
    suspende assim que o sinal de vídeo aparece — e quem captura mic, Discord e
    som do jogo é o OBS dedicado. Então os medidores vêm do próprio OBS, por uma
    conexão persistente. É a melhor fonte possível: é literalmente o nível que
    entra no arquivo, depois do ganho e do mute.

Linux
    O ``gpu-screen-recorder`` não expõe medidor nenhum, mas os buses do
    PipeWire (``MicBus``, ``DiscordBus``, ``RecordBus``) continuam de pé mesmo
    com o serviço de áudio pausado — pausar o gravador não desmonta o
    roteamento. Então lemos os monitores dos buses direto, com ``parec``.

A pergunta "a captura engatou no jogo?" só existe no Windows: lá o Game Capture
é um hook que pode falhar em silêncio e produzir um arquivo preto e válido. No
Linux se grava um monitor inteiro, não há o que engatar, e o campo fica ``None``.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from abc import ABC, abstractmethod
from array import array
from datetime import datetime
from pathlib import Path

from .base import read_shell_config, stable_app_label
from .hudstate import SILENCE_DB, SOUND_FLOOR_DB, HudSnapshot, Meter, to_db
from ..backend.main_paths import CONFIG_DIR, MEDIA_ROOT, VIDEO_DIR
from ..backend.runtime import VIDEO_ACTIVITY_FRESH_SECONDS, runtime_dir, video_activity_flag, video_recording_flag

VIDEO_CONFIG = CONFIG_DIR / "video.conf"

#: Acima disto o arquivo de estado do laço de vídeo é considerado velho. Ele é
#: reescrito a cada volta (2 s), então uma folga generosa distingue "o laço
#: morreu segurando o sinal" de "a volta demorou um pouco".
FLAG_FRESH_SECONDS = VIDEO_ACTIVITY_FRESH_SECONDS


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


#: De quanto em quanto tempo se confere que o ``parec`` ainda lê o bus pedido.
ATTACH_CHECK_SECONDS = 4.0


def _pulse_sources() -> dict[str, str]:
    """Mapa id -> nome das fontes do PipeWire/Pulse."""
    try:
        result = subprocess.run(["pactl", "list", "short", "sources"], check=False,
                                capture_output=True, text=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return {}
    sources: dict[str, str] = {}
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) >= 2:
            sources[fields[0]] = fields[1]
    return sources


def _attached_source(client: str) -> str | None:
    """Fonte à qual o ``parec`` de ``client`` está realmente ligado.

    Existe porque ``parec --device=X`` **não** falha quando X não existe: ele
    cai calado na fonte padrão. E um stream já ligado é *movido* pelo PipeWire
    quando o bus some — foi assim que os três medidores da HUD acabavam lendo o
    mesmo dispositivo, e qualquer som mexia as três barras.
    """
    try:
        result = subprocess.run(["pactl", "list", "source-outputs"], check=False,
                                capture_output=True, text=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    sources = _pulse_sources()
    source_id: str | None = None
    for line in result.stdout.splitlines():
        stripped = line.strip()
        if stripped.startswith("Source Output #"):
            source_id = None
        elif stripped.startswith("Source:"):
            source_id = stripped.split(":", 1)[1].strip()
        elif f'"{client}"' in stripped and source_id is not None:
            return sources.get(source_id)
    return None


#: Pico acima do qual o microfone cru está vivo (~3 LSB em s16). Um microfone
#: aberto sempre tem ruído próprio muito acima disto; o mudo entrega zero.
LIVENESS_DB = -80.0

#: De quanto em quanto tempo se procura o filtro da supressão por IA.
RAW_MIC_CHECK_SECONDS = 2.0


def _clean_mic_master() -> str | None:
    """Microfone cru por trás do filtro da supressão por IA, se ele existir."""
    from .linux import CLEAN_MIC_SOURCE

    try:
        result = subprocess.run(["pactl", "list", "short", "modules"], check=False,
                                capture_output=True, text=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None
    for line in result.stdout.splitlines():
        fields = line.split("\t")
        if len(fields) < 3 or fields[1] != "module-ladspa-source":
            continue
        args = fields[2].split()
        if f"source_name={CLEAN_MIC_SOURCE}" not in args:
            continue
        for arg in args:
            if arg.startswith("master="):
                return arg[len("master="):] or None
    return None


class _MeterTracker:
    """Contabilidade temporal de uma fonte de áudio.

    Guarda desde quando a fonte não entrega amostras e desde quando entrega em
    silêncio. Esses dois relógios são o que permite a :func:`hudstate.evaluate`
    permanecer pura — ela recebe durações prontas em vez de olhar o relógio.
    """

    def __init__(self, label: str, required: bool = False) -> None:
        now = time.monotonic()
        self.label = label
        self.required = required
        self.present = False
        self.muted = False
        self.peak_db = SILENCE_DB
        # Começa em graça: recém-aberta, a fonte ainda não teve chance de
        # entregar nada, e acusar ausência no primeiro segundo seria mentira.
        self._present_at = now
        self._sound_at = now
        #: Quem responde "há som?" é outra leitura, não o pico exibido. Com a
        #: supressão por IA o bus fica em zero sempre que não há fala; é o
        #: microfone cru, antes do filtro, que distingue calado de mudo.
        self.external_liveness = False

    def update(self, present: bool, peak_db: float, muted: bool = False) -> None:
        now = time.monotonic()
        self.present = present
        self.muted = muted
        self.peak_db = peak_db if present else SILENCE_DB
        if present:
            self._present_at = now
            if peak_db > SOUND_FLOOR_DB and not self.external_liveness:
                self._sound_at = now
        if muted:
            # Mudo é uma condição própria, não uma ausência acumulada: zerar o
            # relógio evita empilhar dois alertas para a mesma causa.
            self._present_at = now

    def alive(self) -> None:
        """O microfone por trás do filtro entregou sinal de verdade."""
        self._sound_at = time.monotonic()

    def build(self) -> Meter:
        now = time.monotonic()
        return Meter(
            label=self.label,
            peak_db=self.peak_db,
            present=self.present,
            muted=self.muted,
            absent_seconds=0.0 if self.present else now - self._present_at,
            silent_seconds=now - self._sound_at,
            required=self.required,
        )


class _Growth:
    """Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo)."""

    def __init__(self) -> None:
        self.value = 0
        self._changed_at = time.monotonic()

    def update(self, value: int) -> None:
        if value != self.value:
            self.value = value
            self._changed_at = time.monotonic()

    def reset(self) -> None:
        self.value = 0
        self._changed_at = time.monotonic()

    @property
    def stalled_seconds(self) -> float:
        return time.monotonic() - self._changed_at


class HudCollector(ABC):
    """Fonte do instantâneo da HUD."""

    name = "base"

    def start(self) -> None:
        """Sobe threads de coleta (no-op quando não houver)."""

    def stop(self) -> None:
        """Encerra a coleta."""

    @abstractmethod
    def snapshot(self) -> HudSnapshot:
        """Estado atual, já normalizado."""

    # --- partes iguais nos dois sistemas ---------------------------------
    @staticmethod
    def _settings() -> dict[str, str]:
        return read_shell_config(VIDEO_CONFIG)

    @staticmethod
    def _disk_free() -> int:
        root = MEDIA_ROOT if MEDIA_ROOT.exists() else Path.home()
        try:
            return shutil.disk_usage(root).free
        except OSError:
            return 0


# --- Windows ----------------------------------------------------------------

class WindowsHudCollector(HudCollector):
    """Medidores e engate lidos do OBS dedicado, estado lido do sinal de vídeo."""

    name = "windows"

    def __init__(self) -> None:
        from . import obs

        self._obs = obs
        self._lock = threading.Lock()
        self._stopping = threading.Event()
        self._thread: threading.Thread | None = None

        self._trackers = {
            obs.MIC_INPUT: _MeterTracker("Microfone", required=True),
            obs.DISCORD_AUDIO_INPUT: _MeterTracker("Discord"),
            obs.SYSTEM_AUDIO_INPUT: _MeterTracker("Jogo"),
            obs.FALLBACK_AUDIO_INPUT: _MeterTracker("Sistema"),
        }
        self._muted: dict[str, bool] = {}
        self._recording = False
        self._buffering = False
        self._hooked: bool | None = None
        self._capture_source = ""
        self._bytes = _Growth()
        self._connected = False
        self._reason = "OBS dedicado não está aberto"

    # --- ciclo de vida ----------------------------------------------------
    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="lume-hud-obs", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stopping.set()
        if self._thread is not None:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        while not self._stopping.is_set():
            if not self._obs.port_open(timeout=0.3):
                self._offline("OBS dedicado não está aberto")
                self._stopping.wait(3.0)
                continue
            try:
                self._obs.stream(
                    on_event=self._on_event,
                    requests=self._requests,
                    on_results=self._on_results,
                    should_stop=self._stopping.is_set,
                    tick_seconds=1.0,
                )
            except Exception as exc:  # o socket cai o tempo todo; reconectar é o normal
                self._offline(f"conexão com o OBS caiu: {exc}")
                self._stopping.wait(3.0)
            else:
                # Retorno sem exceção é parada pedida ou socket fechado pelo
                # OBS. Só o segundo caso é notícia: anunciar o encerramento
                # normal encheria o log de alarme a cada parada do serviço.
                if not self._stopping.is_set():
                    self._offline("OBS dedicado encerrou a conexão")

    def _offline(self, reason: str) -> None:
        with self._lock:
            if self._connected:
                log(f"[hud] {reason}")
            self._connected = False
            self._reason = reason
            self._recording = False
            self._buffering = False
            self._hooked = None
            self._bytes.reset()
            for tracker in self._trackers.values():
                tracker.update(present=False, peak_db=SILENCE_DB)

    # --- callbacks do obs-websocket (rodam na thread do socket) -----------
    def _on_event(self, event_type: str, data: dict) -> None:
        with self._lock:
            if event_type == "InputVolumeMeters":
                self._apply_meters(data.get("inputs") or [])
            elif event_type == "RecordStateChanged":
                self._recording = bool(data.get("outputActive"))
                if not self._recording:
                    self._bytes.reset()
            elif event_type == "ReplayBufferStateChanged":
                self._buffering = bool(data.get("outputActive"))
            elif event_type == "InputActiveStateChanged":
                if data.get("inputName") in (self._obs.GAME_INPUT, self._obs.WINDOW_INPUT):
                    self._hooked = bool(data.get("videoActive"))

    def _apply_meters(self, inputs: list[dict]) -> None:
        seen: set[str] = set()
        for item in inputs:
            name = str(item.get("inputName") or "")
            tracker = self._trackers.get(name)
            if tracker is None:
                continue
            seen.add(name)
            # ``inputLevelsMul`` traz [magnitude, pico, pico de entrada] por
            # canal, em multiplicador linear. Usamos o pico pós-fader: é o que
            # de fato vai para o arquivo. Lista vazia é o que o OBS manda quando
            # a entrada está mutada ou sem dispositivo — daí present=False.
            channels = item.get("inputLevelsMul") or []
            peak = 0.0
            for channel in channels:
                if not channel:
                    continue
                peak = max(peak, float(channel[1] if len(channel) > 1 else channel[0]))
            tracker.update(present=bool(channels), peak_db=to_db(peak),
                           muted=self._muted.get(name, False))
        for name, tracker in self._trackers.items():
            if name not in seen:
                tracker.update(present=False, peak_db=SILENCE_DB,
                               muted=self._muted.get(name, False))

    def _requests(self) -> list[tuple[str, dict]]:
        obs = self._obs
        return [
            ("GetRecordStatus", {}),
            ("GetReplayBufferStatus", {}),
            ("GetSourceActive", {"sourceName": obs.GAME_INPUT}),
            ("GetSourceActive", {"sourceName": obs.WINDOW_INPUT}),
            *[("GetInputMute", {"inputName": name}) for name in self._trackers],
        ]

    def _on_results(self, results: list[dict | None]) -> None:
        record, replay, game, window, *mutes = results
        with self._lock:
            self._connected = True
            self._reason = ""
            if record is not None:
                self._recording = bool(record.get("outputActive"))
                if self._recording:
                    self._bytes.update(int(record.get("outputBytes") or 0))
                else:
                    self._bytes.reset()
            if replay is not None:
                self._buffering = bool(replay.get("outputActive"))
            # Qual das duas capturas de vídeo está valendo depende da regra do
            # app (``source=game`` ou ``source=window``); a que estiver ativa na
            # cena é a que responde por ter engatado.
            game_active = bool((game or {}).get("videoActive"))
            window_active = bool((window or {}).get("videoActive"))
            if game is None and window is None:
                self._hooked = None
            elif window_active:
                self._hooked, self._capture_source = True, "Captura de janela"
            elif game_active:
                self._hooked, self._capture_source = True, "Captura de jogo"
            else:
                self._hooked = False
                self._capture_source = self._capture_source or "Captura de jogo"
            for name, result in zip(self._trackers, mutes):
                if result is not None:
                    self._muted[name] = bool(result.get("inputMuted"))

    # --- instantâneo ------------------------------------------------------
    def snapshot(self) -> HudSnapshot:
        settings = self._settings()
        flag = _read_video_flag()
        with self._lock:
            meters = [self._trackers[name].build() for name in (
                self._obs.MIC_INPUT, self._obs.DISCORD_AUDIO_INPUT, self._obs.SYSTEM_AUDIO_INPUT)]
            # Quando o áudio do app não engatou, o ``winvideo`` desmuta o som do
            # sistema inteiro no lugar dele. Mostrar o que está realmente
            # valendo evita um medidor "Jogo" morto ao lado de som audível.
            fallback = self._trackers[self._obs.FALLBACK_AUDIO_INPUT].build()
            if not meters[2].present and fallback.present:
                meters[2] = fallback
            recording, buffering = self._recording, self._buffering
            hooked, source = self._hooked, self._capture_source
            stalled, written = self._bytes.stalled_seconds, self._bytes.value
            connected, reason = self._connected, self._reason
        # Só é gravação longa se o OBS confirmar que há gravação: o sinal pode
        # estar velho de um laço que morreu no meio dela.
        long_recording = bool(flag.get("long_recording")) and recording

        return HudSnapshot(
            backend=self.name,
            available=connected,
            unavailable_reason=reason,
            enabled=settings.get("VIDEO_ENABLED", "false").lower() == "true",
            recording=recording,
            buffering=buffering and not recording,
            long_recording=long_recording,
            long_elapsed_seconds=_long_elapsed(flag),
            mode=flag.get("mode") or settings.get("VIDEO_CAPTURE_MODE", "continuous"),
            app=_app_label(flag.get("window", "")),
            window=flag.get("window", ""),
            elapsed_seconds=_elapsed(flag),
            focus_grace_remaining=_focus_grace_remaining(flag),
            output_bytes=written,
            bytes_stalled_seconds=stalled,
            video_hooked=hooked,
            capture_source=source,
            markers=int(flag.get("markers") or 0),
            last_clip_name=str(flag.get("last_clip") or ""),
            **_event_fields(flag),
            meters=meters,
            disk_free_bytes=self._disk_free(),
        )


# --- Linux ------------------------------------------------------------------

class LinuxHudCollector(HudCollector):
    """Estado derivado do laço bash e medidores lidos dos buses do PipeWire.

    O ``bin/game-video-loop`` publica o mesmo JSON que o ``winvideo`` — janela,
    modo, marcadores, clipes, eventos — e, no modo contínuo, escreve o segmento
    em curso como ``*.partial.mp4``. O arquivo parcial ainda importa: é dele que
    saem os bytes escritos e o alerta de captura travada, que o sinal não conta.
    Instalações antigas, sem o JSON, continuam legíveis pelo par
    ``captura-dia-video-paused`` + ``*.partial.mp4``.

    Ainda **não validado numa máquina Linux**; a estrutura está no lugar e o
    comportamento na ausência de cada peça é degradar em silêncio, nunca acusar
    falha que não existe.
    """

    name = "linux"

    #: Mesmo arquivo que ``bin/game-video-loop`` e o ``SystemdServiceManager``
    #: usam para combinar quem pausou as capturas.
    PAUSE_FILE = "captura-dia-video-paused"

    def __init__(self) -> None:
        from .linux import AUDIO_SOURCE, DISCORD_SOURCE, MIC_SOURCE

        self._sources = [
            (MIC_SOURCE, _MeterTracker("Microfone", required=True)),
            (DISCORD_SOURCE, _MeterTracker("Discord")),
            (AUDIO_SOURCE, _MeterTracker("Jogo")),
        ]
        self._lock = threading.Lock()
        self._stopping = threading.Event()
        self._threads: list[threading.Thread] = []
        self._readable = False
        self._reason = "medidores de áudio indisponíveis (parec ausente?)"
        self._growth = _Growth()
        self._service_checked_at = 0.0
        self._service_active: bool | None = None
        self._window_checked_at = 0.0
        self._window = ""

    def start(self) -> None:
        for device, tracker in self._sources:
            thread = threading.Thread(target=self._read_source, args=(device, tracker),
                                      name=f"lume-hud-{tracker.label}", daemon=True)
            thread.start()
            self._threads.append(thread)
        microphone = self._sources[0][1]
        thread = threading.Thread(target=self._watch_raw_mic, args=(microphone,),
                                  name="lume-hud-microfone-cru", daemon=True)
        thread.start()
        self._threads.append(thread)

    def stop(self) -> None:
        self._stopping.set()
        for thread in self._threads:
            thread.join(timeout=3)

    def _stream_peaks(self, device: str, on_peak, still_wanted=None, on_open=None) -> bool:
        """Roda um ``parec`` sobre ``device`` e entrega o pico de cada ~100 ms.

        Taxa baixa e um canal de propósito: só queremos saber se há som e o
        quão alto, não gravar nada. Volta quando o stream acaba, é arrastado
        para outra fonte ou ``still_wanted`` diz que não vale mais; ``False``
        quando nem abriu.
        """
        # Nome único por fonte: é ele que permite conferir, depois, se este
        # processo continua lendo o dispositivo certo.
        client = f"lume-hud-{device}"
        argv = ["parec", f"--device={device}", "--format=s16le", "--rate=8000",
                "--channels=1", "--latency-msec=100", f"--client-name={client}"]
        try:
            process = subprocess.Popen(argv, stdout=subprocess.PIPE,
                                       stderr=subprocess.DEVNULL)
        except (FileNotFoundError, OSError) as exc:
            with self._lock:
                self._reason = f"não foi possível ler {device}: {exc}"
            return False
        if on_open is not None:
            on_open()
        checked_at = time.monotonic()
        try:
            while not self._stopping.is_set():
                assert process.stdout is not None
                chunk = process.stdout.read(1600)  # ~100 ms
                if not chunk:
                    break
                samples = array("h")
                samples.frombytes(chunk[:len(chunk) - len(chunk) % 2])
                peak = max((abs(value) for value in samples), default=0) / 32768.0
                on_peak(to_db(peak))
                now = time.monotonic()
                if now - checked_at >= ATTACH_CHECK_SECONDS:
                    checked_at = now
                    attached = _attached_source(client)
                    if attached is not None and attached != device:
                        # A fonte foi recriada e o PipeWire arrastou este
                        # stream para outra. Reabrir é o que devolve cada
                        # barra ao seu próprio áudio.
                        log(f"[hud] {device}: stream movido para {attached}; reabrindo")
                        break
                    if still_wanted is not None and not still_wanted():
                        break
        finally:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
        return True

    def _read_source(self, device: str, tracker: _MeterTracker) -> None:
        """Lê PCM cru do monitor de um bus e acumula o pico."""
        def opened() -> None:
            with self._lock:
                self._readable = True
                self._reason = ""

        def peak(db: float) -> None:
            with self._lock:
                tracker.update(present=True, peak_db=db)

        while not self._stopping.is_set():
            if device not in _pulse_sources().values():
                # Abrir agora faria o parec cair na fonte padrão e reportar o
                # áudio errado como se fosse deste bus. Melhor não ter medidor.
                with self._lock:
                    tracker.update(present=False, peak_db=SILENCE_DB)
                    self._reason = f"{device} ainda não existe"
                self._stopping.wait(2.0)
                continue
            if not self._stream_peaks(device, peak, on_open=opened):
                self._stopping.wait(5.0)
                continue
            with self._lock:
                tracker.update(present=False, peak_db=SILENCE_DB)
            self._stopping.wait(3.0)

    def _watch_raw_mic(self, tracker: _MeterTracker) -> None:
        """Mantém "o microfone está vivo?" no microfone cru, com o filtro ativo.

        A barra continua mostrando o bus, que é o que vai para o arquivo. Mas
        com a supressão por IA ele fica em zero enquanto a pessoa joga calada,
        e o aviso de silêncio acusaria um microfone que está funcionando.
        """
        while not self._stopping.is_set():
            master = _clean_mic_master()
            if master is None or master not in _pulse_sources().values():
                with self._lock:
                    tracker.external_liveness = False
                self._stopping.wait(RAW_MIC_CHECK_SECONDS)
                continue
            with self._lock:
                tracker.external_liveness = True

            def heard(db: float) -> None:
                if db > LIVENESS_DB:
                    with self._lock:
                        tracker.alive()

            # Troca de headset ou supressão desligada: o filtro some ou muda de
            # microfone, e a leitura recomeça pelo novo estado.
            opened = self._stream_peaks(master, heard,
                                        still_wanted=lambda: _clean_mic_master() == master)
            if not opened:
                with self._lock:
                    tracker.external_liveness = False
            self._stopping.wait(1.0)

    def _partial_segment(self) -> Path | None:
        """Segmento sendo escrito agora pelo ``gpu-screen-recorder``."""
        try:
            partials = sorted(VIDEO_DIR.glob("*.partial.mp4"),
                              key=lambda item: item.stat().st_mtime)
        except OSError:
            return None
        return partials[-1] if partials else None

    def _active_window(self) -> str:
        """Janela em foco, com a mesma cadência do laço bash (2 s).

        O sidecar ``.window`` só é escrito quando o segmento **termina**, então
        durante a gravação não há de onde ler o app a não ser perguntando ao
        compositor — que é exatamente o que ``bin/game-video-loop`` faz.
        """
        now = time.monotonic()
        if now - self._window_checked_at < 2.0:
            return self._window
        self._window_checked_at = now
        from . import get_backend

        try:
            self._window = get_backend().active_window() or ""
        except OSError:
            self._window = ""
        return self._window

    def _service_state(self) -> bool | None:
        # Consultar o systemd custa um processo; uma vez a cada 5 s basta para
        # um alerta que só importa quando o laço morre de vez.
        now = time.monotonic()
        if now - self._service_checked_at < 5.0:
            return self._service_active
        self._service_checked_at = now
        try:
            result = subprocess.run(
                ["systemctl", "--user", "is-active", "captura-dia-video.service"],
                check=False, capture_output=True, text=True, timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
            self._service_active = None
        else:
            self._service_active = result.stdout.strip() == "active"
        return self._service_active

    def snapshot(self) -> HudSnapshot:
        settings = self._settings()
        flag = _read_video_flag()
        # O sinal padrão existe mesmo quando PAUSE_OTHER_CAPTURES=false. O
        # arquivo histórico fica como fallback durante upgrades sem restart.
        active = (bool(flag) or video_recording_flag().is_file()
                  or (runtime_dir() / self.PAUSE_FILE).is_file())
        mode = str(flag.get("mode") or settings.get("VIDEO_CAPTURE_MODE", "continuous"))
        # No modo clipes o replay fica em RAM e nada é escrito enquanto ninguém
        # aperta o atalho: "gravando" seria mentira, e não há segmento parcial
        # cujo crescimento vigiar.
        # Segurar o atalho abre uma gravação longa: em clipes o replay vive em
        # RAM, mas a partir daí há arquivo crescendo em disco de verdade — e
        # chamar isso de "armado" esconderia justamente o que está acontecendo.
        long_recording = active and bool(flag.get("long_recording"))
        buffering = active and mode == "clips" and not long_recording
        recording = active and not buffering
        partial = self._partial_segment() if recording else None
        elapsed = 0.0
        written = 0
        if partial is not None:
            try:
                written = partial.stat().st_size
            except OSError:
                partial = None
            else:
                elapsed = _segment_elapsed(partial)
        with self._lock:
            if recording and partial is not None:
                self._growth.update(written)
            else:
                self._growth.reset()
            meters = [tracker.build() for _device, tracker in self._sources]
            readable, reason = self._readable, self._reason
            stalled = self._growth.stalled_seconds

        return HudSnapshot(
            backend=self.name,
            # Sem os medidores ainda dá para mostrar o essencial (gravando, há
            # quanto tempo), então a leitura só é "indisponível" se nem o estado
            # de vídeo puder ser lido — o que aqui é sempre possível.
            available=True,
            unavailable_reason="" if readable else reason,
            enabled=settings.get("VIDEO_ENABLED", "false").lower() == "true",
            service_active=self._service_state(),
            recording=recording,
            buffering=buffering,
            long_recording=long_recording,
            long_elapsed_seconds=_long_elapsed(flag),
            mode=mode,
            app=_app_label(str(flag.get("window") or "")) if active else "",
            window=str(flag.get("window") or "") if active else "",
            elapsed_seconds=_elapsed(flag) if flag else elapsed,
            focus_grace_remaining=_focus_grace_remaining(flag),
            output_bytes=written,
            bytes_stalled_seconds=stalled,
            video_hooked=None,  # não existe hook a falhar: grava-se o monitor
            markers=int(flag.get("markers") or _count_markers(partial)),
            last_clip_name=str(flag.get("last_clip") or ""),
            **_event_fields(flag),
            meters=meters if readable else [],
            disk_free_bytes=self._disk_free(),
        )


# --- utilidades compartilhadas ---------------------------------------------

def _read_video_flag() -> dict:
    """Lê o sinal JSON que o ``winvideo`` reescreve a cada volta do laço.

    Um arquivo velho significa laço morto segurando o sinal; tratamos como
    ausente para não anunciar uma gravação que já acabou.
    """
    flag = video_activity_flag()
    try:
        stat = flag.stat()
        if time.time() - stat.st_mtime > FLAG_FRESH_SECONDS:
            return {}
        payload = json.loads(flag.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _elapsed(flag: dict) -> float:
    started = flag.get("started_at")
    if isinstance(started, (int, float)) and started > 0:
        return max(0.0, time.time() - float(started))
    return 0.0


def _long_elapsed(flag: dict) -> float:
    """Há quanto tempo a gravação longa corre, ou zero se não há nenhuma."""
    started = flag.get("long_started_at")
    if not flag.get("long_recording") or not isinstance(started, (int, float)) or started <= 0:
        return 0.0
    return max(0.0, time.time() - float(started))


def _app_label(window: str) -> str:
    """Nome curto do app a partir de ``"<título> | <executável>"``."""
    return stable_app_label(window)


def _focus_grace_remaining(flag: dict) -> float | None:
    deadline = flag.get("focus_grace_deadline")
    if not isinstance(deadline, (int, float)) or deadline <= 0:
        return None
    return max(0.0, float(deadline) - time.time())


#: Nome que ``bin/game-video-loop`` dá ao segmento: ``%F_%H-%M-%S_<monitor>.mp4``.
_SEGMENT_STAMP = re.compile(r"(\d{4}-\d{2}-\d{2})_(\d{2})-(\d{2})-(\d{2})_")


def _segment_elapsed(partial: Path) -> float:
    """Há quanto tempo o segmento em curso começou.

    Vem do nome do arquivo, não do ``stat``: num arquivo que cresce a cada
    quadro, ``st_ctime`` e ``st_mtime`` são ambos "agora" e não dizem nada sobre
    o início.
    """
    match = _SEGMENT_STAMP.match(partial.name)
    if match is None:
        return 0.0
    day, hour, minute, second = match.groups()
    try:
        started = datetime.strptime(f"{day} {hour}:{minute}:{second}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return 0.0
    return max(0.0, time.time() - started.timestamp())


def _count_markers(partial: Path | None) -> int:
    if partial is None:
        return 0
    # O laço bash anota em ``<final>.markers``, e ``final`` é o nome sem o
    # ``.partial.mp4`` que só existe enquanto o segmento está sendo escrito.
    final = partial.parent / partial.name.removesuffix(".partial.mp4")
    sidecar = final.with_suffix(final.suffix + ".markers")
    try:
        return len([line for line in sidecar.read_text(encoding="utf-8").splitlines() if line.strip()])
    except OSError:
        return 0


def get_collector(force: str | None = None) -> HudCollector:
    """Coletor do SO atual, na mesma convenção de :func:`app.capture.get_backend`."""
    target = force or ("windows" if os.name == "nt"
                       else "linux" if sys.platform.startswith("linux") else os.name)
    if target == "windows":
        return WindowsHudCollector()
    if target == "linux":
        return LinuxHudCollector()
    raise RuntimeError(f"Sistema operacional sem coletor de HUD: {target!r}")


def _event_fields(flag: dict) -> dict:
    """Extrai o acontecimento pontual publicado pelo laço de vídeo.

    A idade vem do relógio de parede porque o evento nasce noutro processo.
    Serve para a HUD não reproduzir a animação de um marcador antigo quando ela
    própria acaba de subir: o dado continua no sinal, mas já não é notícia.
    """
    event = flag.get("event")
    if not isinstance(event, dict):
        return {}
    at = event.get("at")
    age = max(0.0, time.time() - float(at)) if isinstance(at, (int, float)) else 0.0
    return {
        "event_kind": str(event.get("kind") or ""),
        "event_label": str(event.get("label") or ""),
        "event_seq": int(event.get("seq") or 0),
        "event_age_seconds": age,
    }
