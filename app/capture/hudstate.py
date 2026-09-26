"""Estado da HUD de gravação: instantâneo portátil e regras de saúde.

Este módulo é deliberadamente cego para o sistema operacional. Não sabe o que é
OBS, WASAPI ou PipeWire — quem coleta é :mod:`app.capture.hudsource`. Aqui só se
descreve *o que* foi coletado e se decide *o que aquilo significa*.

A separação existe por um motivo prático: as regras abaixo são a parte que
importa (são elas que dizem "a gravação está saindo preta" ou "o microfone
caiu") e são também a parte que dá para testar em qualquer máquina, inclusive no
sistema que não está rodando no momento. O coletor, que precisa de um jogo aberto
para exercitar, fica isolado do lado de fora.

Convenção de níveis, do mais grave para o mais brando:

``fail``
    Algo que compromete a gravação agora. É o único nível que dispara som.
``warn``
    Merece atenção mas não invalida o arquivo (disco baixo, ninguém falando).
``info``
    Só informação (gravando, marcador anotado).
``ok``
    Tudo certo.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

#: Piso em dBFS usado no lugar de ``-inf`` para silêncio digital absoluto.
#: Um float finito evita ter que tratar ``-inf`` em toda comparação e em toda
#: serialização JSON, que não representa infinito.
SILENCE_DB = -100.0

#: Acima disto consideramos que há som de verdade, não ruído de fundo.
SOUND_FLOOR_DB = -60.0

#: Folga antes de cobrar que a captura de vídeo tenha engatado. O ``winvideo``
#: já espera ``HOOK_WARMUP_SECONDS`` antes de mandar gravar; esta folga é a
#: margem por cima disso, para não acusar durante a troca de segmento.
HOOK_GRACE_SECONDS = 8.0

#: Tempo sem o arquivo crescer que caracteriza gravação travada.
STALL_SECONDS = 8.0

#: Tempo sem a fonte entregar nenhuma amostra que caracteriza dispositivo
#: caído ou mudo. Curto de propósito: é uma falha, e falha tem que aparecer.
SOURCE_ABSENT_SECONDS = 5.0

#: Tempo entregando amostras, porém em silêncio, antes de comentar. Longo de
#: propósito: ficar quieto não é defeito, e alarme falso destrói a confiança na
#: HUD inteira.
SOURCE_SILENT_SECONDS = 45.0

#: Abaixo disto o disco vira aviso. Uma gravação de jogo come alguns GB por
#: hora, então o piso é generoso.
LOW_DISK_BYTES = 5 * 1024**3


def to_db(multiplier: float) -> float:
    """Converte multiplicador linear (0..1) para dBFS, com piso em silêncio."""
    if multiplier <= 0:
        return SILENCE_DB
    value = 20.0 * math.log10(multiplier)
    return SILENCE_DB if value < SILENCE_DB else min(value, 0.0)


@dataclass
class Meter:
    """Uma fonte de áudio vista pela HUD.

    ``present`` e ``peak_db`` respondem perguntas diferentes, e essa distinção é
    o coração da regra de áudio: uma fonte *presente em silêncio* é você calado,
    o que é normal; uma fonte *ausente* é o dispositivo caído ou mudo, o que é
    falha. Confundir as duas transforma a HUD num alarme que ninguém escuta.
    """

    label: str
    peak_db: float = SILENCE_DB
    present: bool = False
    muted: bool = False
    #: Há quanto tempo não chega nenhuma amostra desta fonte.
    absent_seconds: float = 0.0
    #: Há quanto tempo chegam amostras, porém abaixo de :data:`SOUND_FLOOR_DB`.
    silent_seconds: float = 0.0
    #: Fontes obrigatórias geram falha quando somem; as opcionais, nada. O
    #: Discord não estar tocando é o caso normal de quem joga sozinho.
    required: bool = False

    @property
    def audible(self) -> bool:
        return self.present and self.peak_db > SOUND_FLOOR_DB


@dataclass
class HudSnapshot:
    """Tudo que a HUD sabe num instante, já normalizado entre os sistemas."""

    backend: str = ""
    #: O coletor conseguiu conversar com a fonte de verdade (OBS, PipeWire)?
    available: bool = False
    unavailable_reason: str = ""

    enabled: bool = False
    #: ``None`` quando não dá para saber baratinho se o laço de vídeo está de
    #: pé. Só ``False`` — certeza de que caiu — vira alerta; desconhecido cala.
    service_active: bool | None = None

    recording: bool = False
    #: Modo clipes com o Replay Buffer de pé, sem gravar em arquivo ainda.
    buffering: bool = False
    #: Gravação longa em curso: no modo clipes, alguém segurou o atalho e pediu
    #: para gravar tudo dali em diante — o clipe de pré-roll já está guardado e
    #: o arquivo cresce até a próxima segurada.
    long_recording: bool = False
    #: Há quanto tempo essa gravação longa começou. Separado de
    #: ``elapsed_seconds``, que conta a sessão de jogo inteira: são duas
    #: perguntas distintas, e a segunda não responde "quanto já gravei".
    long_elapsed_seconds: float = 0.0
    mode: str = "continuous"
    app: str = ""
    window: str = ""
    elapsed_seconds: float = 0.0
    #: Tempo restante depois de sair do jogo antes de encerrar a captura.
    focus_grace_remaining: float | None = None

    output_bytes: int = 0
    #: Há quanto tempo ``output_bytes`` não cresce.
    bytes_stalled_seconds: float = 0.0

    #: A captura de vídeo engatou no jogo? ``None`` onde a pergunta não se
    #: aplica — no Linux o ``gpu-screen-recorder`` grava um monitor inteiro, não
    #: existe hook que possa falhar em silêncio.
    video_hooked: bool | None = None
    capture_source: str = ""

    markers: int = 0
    last_clip_name: str = ""

    #: Acontecimento pontual vindo do laço de vídeo — marcador anotado, clipe
    #: salvo, atalho ignorado. De propósito **fora** de :func:`evaluate`: um
    #: evento é um instante, e saúde é um estado. Misturá-los deixaria a HUD
    #: vermelha para sempre por causa de um clipe que falhou uma vez.
    event_kind: str = ""
    event_label: str = ""
    event_seq: int = 0
    event_age_seconds: float = 0.0

    meters: list[Meter] = field(default_factory=list)
    disk_free_bytes: int = 0

    @property
    def active(self) -> bool:
        """Há captura de vídeo em curso, gravando ou em buffer de clipes."""
        return self.recording or self.buffering


@dataclass(frozen=True)
class Alert:
    key: str
    level: str
    text: str
    detail: str = ""


#: Ordem de gravidade, usada para escolher o pior alerta e a cor da HUD.
_ORDER = {"ok": 0, "info": 1, "warn": 2, "fail": 3}


@dataclass
class HudStatus:
    level: str
    headline: str
    alerts: list[Alert] = field(default_factory=list)

    @property
    def failing(self) -> list[Alert]:
        return [alert for alert in self.alerts if alert.level == "fail"]


def worst_level(levels: list[str]) -> str:
    return max(levels, key=lambda level: _ORDER.get(level, 0)) if levels else "ok"


def evaluate(snapshot: HudSnapshot) -> HudStatus:
    """Traduz um instantâneo em alertas e num veredito único.

    Função pura: mesma entrada, mesma saída, sem relógio nem I/O. Todo o
    acúmulo temporal (há quantos segundos a fonte sumiu, há quanto tempo o
    arquivo não cresce) já vem contado no instantâneo, justamente para que esta
    decisão continue testável.
    """
    alerts: list[Alert] = []

    if not snapshot.enabled:
        return HudStatus(level="ok", headline="Vídeo seletivo desligado")

    if not snapshot.available:
        reason = snapshot.unavailable_reason or "fonte de estado indisponível"
        return HudStatus(level="warn", headline="Sem leitura da captura",
                         alerts=[Alert("indisponivel", "warn", "Sem leitura da captura", reason)])

    if not snapshot.active:
        headline = "Aguardando um jogo monitorado"
        if snapshot.service_active is False:
            alerts.append(Alert("servico", "warn", "Serviço de vídeo parado",
                                "A gravação seletiva está habilitada, mas o processo não está de pé."))
            headline = "Serviço de vídeo parado"
        alerts.extend(_disk_alerts(snapshot))
        return HudStatus(level=worst_level([alert.level for alert in alerts]), headline=headline,
                         alerts=alerts)

    # --- daqui para baixo há captura em curso -------------------------------
    if snapshot.video_hooked is False and snapshot.elapsed_seconds >= HOOK_GRACE_SECONDS:
        alerts.append(Alert(
            "sem-imagem", "fail", "Captura sem imagem",
            f"{snapshot.capture_source or 'A captura'} não engatou. Sai preto."))

    # Só cobra crescimento de quem está de fato escrevendo em disco. Em modo
    # clipes o Replay Buffer vive em memória e não move byte nenhum até o F8.
    if snapshot.recording and snapshot.bytes_stalled_seconds >= STALL_SECONDS:
        alerts.append(Alert(
            "travada", "fail", "Gravação travada",
            f"O arquivo não cresce há {snapshot.bytes_stalled_seconds:.0f}s."))

    if snapshot.focus_grace_remaining is not None:
        remaining = max(0, math.ceil(snapshot.focus_grace_remaining))
        alerts.append(Alert(
            "fora-do-jogo", "warn", f"Fora do jogo · para em {remaining}s",
            "Volte ao jogo para manter a gravação ativa."))

    for meter in snapshot.meters:
        alerts.extend(_meter_alerts(meter))

    alerts.extend(_disk_alerts(snapshot))

    level = worst_level([alert.level for alert in alerts])
    if level == "fail":
        headline = alerts[0].text
    elif snapshot.focus_grace_remaining is not None:
        headline = f"Fora do jogo · para em {max(0, math.ceil(snapshot.focus_grace_remaining))}s"
    elif snapshot.long_recording:
        headline = "Gravando tudo"
    elif snapshot.buffering:
        headline = "Clipes armados"
    else:
        headline = "Gravando"
    return HudStatus(level=level, headline=headline, alerts=alerts)


def _meter_alerts(meter: Meter) -> list[Alert]:
    if meter.muted:
        level = "fail" if meter.required else "warn"
        return [Alert(f"mudo:{meter.label}", level, f"{meter.label} mudo",
                      "Silenciado na mixagem; não entra no arquivo.")]
    if not meter.present and meter.absent_seconds >= SOURCE_ABSENT_SECONDS:
        if not meter.required:
            # Discord fechado, jogo sem som: silêncio esperado, não é notícia.
            return []
        return [Alert(f"ausente:{meter.label}", "fail", f"{meter.label} sem sinal",
                      f"Sem amostras há {meter.absent_seconds:.0f}s. O aparelho caiu?")]
    if meter.required and meter.present and meter.silent_seconds >= SOURCE_SILENT_SECONDS:
        return [Alert(f"silencio:{meter.label}", "warn", f"{meter.label} em silêncio",
                      f"Capturando, mas sem som há {meter.silent_seconds / 60:.0f} min.")]
    return []


def _disk_alerts(snapshot: HudSnapshot) -> list[Alert]:
    if 0 < snapshot.disk_free_bytes < LOW_DISK_BYTES:
        return [Alert("disco", "warn", "Disco quase cheio",
                      f"{snapshot.disk_free_bytes / 1024**3:.1f} GB livres.")]
    return []


def format_elapsed(seconds: float) -> str:
    """``h:mm:ss`` acima de uma hora, ``m:ss`` abaixo — como um cronômetro."""
    total = max(0, int(seconds))
    hours, rest = divmod(total, 3600)
    minutes, secs = divmod(rest, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
