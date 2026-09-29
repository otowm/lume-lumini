"""HUD de gravação: uma faixa sobre o jogo dizendo se a captura está saindo.

Roda como processo próprio, igual aos outros laços:

    python -m app.capture.hud

O problema que ela resolve é de tempo: hoje só se descobre que a gravação saiu
preta ou muda **depois**, quando o arquivo já foi perdido. A HUD antecipa isso
para o instante em que ainda dá para agir.

Sobre tela cheia
================
Não existe overlay garantido sobre fullscreen exclusivo sem injetar DLL no
processo do jogo — é o que Discord, Steam e RTSS fazem. Aqui isso está fora de
questão: há anti-cheat na lista de apps monitorados, e nenhum diagnóstico vale
esse risco. O que se faz sem injetar é uma janela ``TOPMOST`` que não recebe
foco nem clique. Ela aparece sobre a esmagadora maioria dos jogos no Windows 11,
que na prática apresentam em flip-model por causa do Fullscreen Optimizations, e
**some** em exclusivo de verdade.

Por isso a posição é configurável em vez de fixa: sobre o jogo quando funciona,
num segundo monitor quando é preciso garantia, ou nos dois. E por isso as falhas
também tocam um som — se a HUD não aparecer, o aviso ainda chega.

O detalhe que não pode ser esquecido é ``WS_EX_NOACTIVATE``. Sem ele a HUD
roubaria o foco ao aparecer, o ``winvideo`` concluiria que o jogo saiu de foco e
**pararia a gravação** que a HUD deveria estar vigiando.
"""

from __future__ import annotations

import argparse
import ctypes
import dataclasses
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass

from .base import Monitor, read_shell_config
from .hudstate import (SILENCE_DB, SOUND_FLOOR_DB, HudSnapshot, HudStatus, Meter,
                       evaluate, format_elapsed)
from .hudsource import VIDEO_CONFIG, get_collector

IS_WINDOWS = os.name == "nt"

# Redesenhar custa ~4 ms (o Canvas do tkinter recria os itens a cada volta), o
# que a 60 quadros por segundo daria uns 20% de um núcleo — caro demais para
# uma barra de estado rodando durante um jogo. Daí três cadências:
#
#: Enquanto uma confirmação anima. São 2 ou 3 segundos, e é justamente aqui que
#: a fluidez se nota.
ANIMATION_TICK_MS = 16
#: Com a HUD à vista, sem animação. Os medidores continuam vivos e legíveis.
TICK_MS = 66
#: Com a HUD escondida: não há o que desenhar, só o que observar.
IDLE_TICK_MS = 250

#: Silêncio mínimo entre dois avisos sonoros da mesma causa.
SOUND_COOLDOWN_SECONDS = 30.0

#: Queda da barra em dB por segundo. Sem isso o medidor pisca a cada sílaba;
#: com isso ele se comporta como um VU de verdade.
METER_FALL_DB_PER_SECOND = 90.0

BACKGROUND = "#0d1117"
BORDER = "#30363d"
TEXT = "#e6edf3"
MUTED = "#7d8590"
TRACK = "#21262d"
#: Cor tratada como transparente pelo Windows. Um valor improvável de aparecer
#: por acidente no desenho, senão o buraco apareceria no meio do painel.
CHROMA = "#010203"

LEVEL_COLORS = {"ok": "#3fb950", "info": "#58a6ff", "warn": "#d29922", "fail": "#f85149"}

#: Vermelho de gravação. Deliberadamente **não** é o vermelho de falha: o de
#: falha é chapado e grita; este é o ponto de REC de qualquer câmera, e é a
#: piscada — não a cor sozinha — que diz que ainda está rodando.
RECORD_RED = "#ff5c5c"

def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


@dataclass
class HudSettings:
    """Preferências da HUD, lidas de ``video.conf``."""

    enabled: bool = True
    #: ``game`` (monitor do jogo), ``second`` (outro monitor) ou ``both``.
    placement: str = "second"
    corner: str = "top-right"
    hotkey: str = "Ctrl+Shift+F8"
    sound: bool = True

    @classmethod
    def load(cls) -> "HudSettings":
        values = read_shell_config(VIDEO_CONFIG)
        placement = values.get("VIDEO_HUD_PLACEMENT", "second").lower()
        corner = values.get("VIDEO_HUD_CORNER", "top-right").lower()
        corners = {"top-left", "top-right", "bottom-left", "bottom-right"}
        return cls(
            enabled=values.get("VIDEO_HUD_ENABLED", "true").lower() == "true",
            placement=placement if placement in {"game", "second", "both"} else "second",
            corner=corner if corner in corners else "top-right",
            hotkey=values.get("VIDEO_HUD_HOTKEY", "Ctrl+Shift+F8"),
            sound=values.get("VIDEO_HUD_SOUND", "true").lower() == "true",
        )


# --- integração com o sistema de janelas ------------------------------------

def _declare_dpi_aware() -> None:
    """Coordenadas em pixels reais, antes de qualquer janela existir.

    Sem isto o Windows mente sobre a geometria dos monitores em qualquer escala
    diferente de 100%, e a HUD apareceria fora do canto pedido — ou fora da tela.
    """
    if not IS_WINDOWS:
        return
    try:
        # PER_MONITOR_AWARE_V2: cada monitor com a sua escala.
        ctypes.windll.user32.SetProcessDpiAwarenessContext(-4)
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except (AttributeError, OSError):
                pass


def _window_handle(window) -> int:
    """HWND real de um ``Toplevel`` do tkinter."""
    child = window.winfo_id()
    parent = ctypes.windll.user32.GetParent(child)
    return parent or child


def _make_overlay(window) -> None:
    """Deixa a janela flutuando, sem foco, sem clique e fora do Alt+Tab."""
    if not IS_WINDOWS:
        # No X11 o tipo ``dock`` pede ao gerenciador de janelas que a mantenha
        # acima e sem decoração. Não há equivalente barato para clique
        # atravessante em tkinter, então no Linux a HUD é uma janela comum
        # flutuando — a validar quando o sistema for trocado.
        try:
            window.attributes("-type", "dock")
        except Exception:
            pass
        return

    user32 = ctypes.windll.user32
    user32.GetWindowLongW.restype = ctypes.c_long
    user32.SetWindowLongW.restype = ctypes.c_long
    hwnd = _window_handle(window)

    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    WS_EX_TRANSPARENT = 0x00000020      # clique atravessa
    WS_EX_NOACTIVATE = 0x08000000       # nunca rouba o foco do jogo
    WS_EX_TOOLWINDOW = 0x00000080       # fora do Alt+Tab e da barra de tarefas
    style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    user32.SetWindowLongW(hwnd, GWL_EXSTYLE,
                          style | WS_EX_LAYERED | WS_EX_TRANSPARENT
                          | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW)


def _assert_topmost(window) -> None:
    """Reafirma o topo da pilha.

    Um jogo entrando em tela cheia reordena o z-order e passa na frente. Como
    isso acontece exatamente quando a HUD começa a importar, ela se reafirma a
    cada volta em vez de confiar no ``-topmost`` inicial.
    """
    if not IS_WINDOWS:
        return
    HWND_TOPMOST = -1
    SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x1, 0x2, 0x10
    ctypes.windll.user32.SetWindowPos(_window_handle(window), HWND_TOPMOST, 0, 0, 0, 0,
                                      SWP_NOSIZE | SWP_NOMOVE | SWP_NOACTIVATE)


def _alert_sound() -> None:
    """Aviso audível de falha, distinto do bipe de marcador.

    O marcador toca um par **ascendente** ao aceitar uma ação; aqui o par é
    **descendente**, para que os dois nunca sejam confundidos com o jogo tocando
    por cima.
    """
    if IS_WINDOWS:
        try:
            import winsound

            winsound.Beep(660, 120)
            winsound.Beep(440, 180)
        except (ImportError, RuntimeError, OSError):
            pass
        return
    try:
        subprocess.run(["canberra-gtk-play", "-i", "dialog-warning"],
                       check=False, capture_output=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass


# --- confirmações -----------------------------------------------------------

#: Cada acontecimento do laço de vídeo tem ícone, cor e um destino: ou ele
#: termina sozinho, ou fica esperando o desfecho. ``clip_saving`` é o segundo
#: caso — o OBS leva segundos para informar o arquivo, e a faixa some quando o
#: evento seguinte (salvo ou falhou) chegar.
EVENT_STYLES = {
    "marker":         ("◆", "#58a6ff", 2.4),
    "marker_queued":  ("◇", "#58a6ff", 2.4),
    "clip_saving":    ("●", "#d29922", 20.0),
    "clip_queued":    ("○", "#d29922", 2.4),
    "clip_saved":     ("✔", "#3fb950", 2.8),
    # Um atalho dentro da janela de replay não abre outro clipe: estende o que
    # acabou de ser salvo. A seta é o que diferencia "salvei" de "cresceu".
    "clip_merged":    ("⇥", "#3fb950", 2.8),
    "clip_failed":    ("✖", "#f85149", 5.0),
    "ignored":        ("–", "#7d8590", 2.0),
    # Gravação longa. O início é um instante curto — a partir dali quem informa
    # é o ponto vermelho permanente, não a faixa. Fechar, ao contrário, espera
    # o desfecho: emendar o pré-roll à gravação leva segundos.
    "long_started":   ("⏺", RECORD_RED, 2.4),
    "long_saving":    ("●", "#d29922", 60.0),
    "long_saved":     ("✔", "#3fb950", 3.2),
    "long_failed":    ("✖", "#f85149", 5.0),
}

#: Duração da entrada (desliza e acende) e da saída (recolhe).
EVENT_IN_SECONDS = 0.26
EVENT_OUT_SECONDS = 0.42
#: Deslocamento horizontal inicial da faixa expandida, em pixels.
EVENT_SLIDE_PX = 20.0
#: Altura da faixa de evento no painel expandido.
EVENT_BAND_PX = 28


def blend(base: str, other: str, amount: float) -> str:
    """Mistura duas cores ``#rrggbb``.

    O Canvas do tkinter não tem canal alfa por item, então "esmaecer" é
    literalmente caminhar em direção à cor do fundo.
    """
    amount = max(0.0, min(1.0, amount))
    a = tuple(int(base[i:i + 2], 16) for i in (1, 3, 5))
    b = tuple(int(other[i:i + 2], 16) for i in (1, 3, 5))
    return "#" + "".join(f"{round(x + (y - x) * amount):02x}" for x, y in zip(a, b))


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def ease_in_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t ** 3


def ease_out_back(t: float, overshoot: float = 1.6) -> float:
    """Passa um pouco do alvo e volta.

    É o que separa "apareceu" de "chegou": sem o exagero final o movimento
    parece uma transição de planilha. O excesso é pequeno de propósito — a
    faixa é informação, não enfeite.
    """
    t = max(0.0, min(1.0, t))
    c = overshoot + 1.0
    return 1.0 + c * (t - 1.0) ** 3 + overshoot * (t - 1.0) ** 2


@dataclass(frozen=True)
class EventFrame:
    """Um quadro da animação de confirmação.

    ``reveal`` é o quanto o evento tomou o lugar (0 = ausente, 1 = inteiro) e
    pode passar de 1 no repique da entrada. ``glow`` é o mesmo movimento sem
    exagero, para cor — uma cor que "passa do alvo" não existe.
    """

    reveal: float
    glow: float
    slide: float


def event_animation(kind: str, elapsed: float) -> EventFrame | None:
    """Estado da animação, ou ``None`` quando ela já acabou.

    Função pura: é o miolo do movimento e dá para verificar sem abrir janela.
    """
    style = EVENT_STYLES.get(kind)
    if style is None or elapsed < 0:
        return None
    total = style[2]
    if elapsed >= total:
        return None

    remaining = total - elapsed
    if elapsed < EVENT_IN_SECONDS:
        t = elapsed / EVENT_IN_SECONDS
        reveal, glow = ease_out_back(t), ease_out_cubic(t)
    elif remaining < EVENT_OUT_SECONDS:
        t = 1.0 - remaining / EVENT_OUT_SECONDS
        reveal = glow = 1.0 - ease_in_cubic(t)
    else:
        reveal = glow = 1.0
    return EventFrame(reveal=reveal, glow=max(0.0, min(1.0, glow)),
                      slide=EVENT_SLIDE_PX * (1.0 - min(1.0, reveal)))


# --- posicionamento ----------------------------------------------------------

def choose_monitors(placement: str, monitors: list[Monitor],
                    active: Monitor | None) -> list[Monitor]:
    """Monitores que devem receber um painel.

    Função pura para poder ser testada sem tela: recebe a lista de monitores e
    qual deles contém a janela em foco, devolve onde desenhar. Com um monitor
    só, qualquer escolha recai sobre ele — nunca devolve lista vazia quando há
    ao menos um monitor.
    """
    if not monitors:
        return []
    game = active or monitors[0]
    others = [monitor for monitor in monitors if monitor.index != game.index]
    if placement == "game" or not others:
        return [game]
    if placement == "both":
        return [game, others[0]]
    return [others[0]]


def corner_position(monitor: Monitor, corner: str, width: int, height: int,
                    margin: int = 24) -> tuple[int, int]:
    left = monitor.x + margin
    right = monitor.x + monitor.width - width - margin
    top = monitor.y + margin
    bottom = monitor.y + monitor.height - height - margin
    x = right if corner.endswith("right") else left
    y = bottom if corner.startswith("bottom") else top
    return x, y


# --- painel ------------------------------------------------------------------

class HudPanel:
    """Um painel desenhado num monitor."""

    COMPACT_SIZE = (232, 34)
    EXPANDED_WIDTH = 352

    def __init__(self, root, monitor: Monitor, corner: str) -> None:
        import tkinter as tk

        self.tk = tk
        self.monitor = monitor
        self.corner = corner
        self.window = tk.Toplevel(root)
        self.window.overrideredirect(True)
        self.window.attributes("-topmost", True)
        try:
            self.window.attributes("-alpha", 0.92)
        except Exception:
            pass
        try:
            self.window.attributes("-transparentcolor", CHROMA)
        except Exception:
            pass  # só existe no Windows; sem isso o fundo fica sólido
        self.window.configure(bg=CHROMA)
        self.canvas = tk.Canvas(self.window, highlightthickness=0, bd=0,
                                bg=CHROMA, width=self.COMPACT_SIZE[0],
                                height=self.COMPACT_SIZE[1])
        self.canvas.pack()
        self.window.withdraw()
        self._configured = False
        self._visible = False
        self._geometry = ""
        self._family = "Segoe UI" if IS_WINDOWS else "DejaVu Sans"
        self._fonts: dict[tuple[int, bool], object] = {}
        self._compact_key: tuple | None = None

    # --- ciclo de vida --------------------------------------------------
    def _ensure_overlay(self) -> None:
        # Os estilos estendidos só pegam depois de a janela existir de verdade
        # no sistema; antes do primeiro ``deiconify`` não há HWND para alterar.
        if not self._configured:
            self.window.update_idletasks()
            _make_overlay(self.window)
            self._configured = True

    def show(self) -> None:
        if not self._visible:
            self.window.deiconify()
            self._visible = True
            self._ensure_overlay()
        _assert_topmost(self.window)

    def hide(self) -> None:
        if self._visible:
            self.window.withdraw()
            self._visible = False

    def destroy(self) -> None:
        self.window.destroy()

    def move_to(self, monitor: Monitor) -> None:
        self.monitor = monitor

    def _resize(self, width: int, height: int) -> None:
        x, y = corner_position(self.monitor, self.corner, width, height)
        geometry = f"{width}x{height}+{x}+{y}"
        if geometry != self._geometry:
            self.window.geometry(geometry)
            self._geometry = geometry
        self.canvas.configure(width=width, height=height)

    # --- desenho ---------------------------------------------------------
    def render(self, snapshot: HudSnapshot, status: HudStatus,
               levels: dict[str, float], expanded: bool,
               event: tuple[str, str, EventFrame] | None = None) -> None:
        if expanded:
            self._compact_key = None
            self._render_expanded(snapshot, status, levels, event)
        else:
            self._render_compact(snapshot, status, event)

    def _panel(self, width: int, height: int, color: str) -> None:
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, width - 1, height - 1,
                                     fill=BACKGROUND, outline=BORDER)
        # Faixa de cor na borda esquerda: dá para ler o estado com o canto do
        # olho, sem parar de jogar para interpretar texto.
        self.canvas.create_rectangle(0, 0, 3, height - 1, fill=color, outline=color)

    def _font(self, size: int, bold: bool = False):
        import tkinter.font as tkfont

        key = (size, bold)
        if key not in self._fonts:
            self._fonts[key] = tkfont.Font(family=self._family, size=size,
                                           weight="bold" if bold else "normal")
        return self._fonts[key]

    def _fit(self, text: str, max_px: int, size: int, bold: bool = False) -> str:
        """Corta pela largura real do texto, não por contagem de caracteres.

        A HUD mistura duas fontes (uma por sistema) e nomes de jogo de tamanhos
        imprevisíveis; qualquer limite em caracteres ora sobra, ora estoura a
        borda — que foi o que aconteceu no primeiro desenho.
        """
        text = text.strip()
        font = self._font(size, bold)
        if font.measure(text) <= max_px:
            return text
        while text and font.measure(text + "…") > max_px:
            text = text[:-1]
        return text + "…"

    def _text(self, x: int, y: int, text: str, color: str = TEXT, size: int = 9,
              bold: bool = False, anchor: str = "w") -> None:
        self.canvas.create_text(x, y, text=text, fill=color, anchor=anchor,
                                font=self._font(size, bold))

    def _render_compact(self, snapshot: HudSnapshot, status: HudStatus,
                        event: tuple[str, str, EventFrame] | None = None) -> None:
        """Barra mínima. O evento entra por baixo empurrando o conteúdo normal.

        Não há espaço para uma faixa separada aqui, e crescer a barra seria a
        mesma expansão que se quis evitar. Então o compacto troca de conteúdo
        como um letreiro: a linha normal sobe, a do evento entra no lugar, e
        depois volta. O recorte é o próprio canvas, que tem o tamanho do painel.
        """
        width, height = self.COMPACT_SIZE
        color = LEVEL_COLORS.get(status.level, MUTED)
        accent = color
        blink = True
        if event is not None:
            accent = blend(color, EVENT_STYLES[event[0]][1], event[2].glow)
        label = status.headline if status.level == "fail" else (snapshot.app or status.headline)
        clock = format_elapsed(snapshot.elapsed_seconds) if snapshot.recording else ""
        # Numa gravação longa o relógio que importa é o dela, não o da sessão de
        # jogo: a pergunta na cabeça de quem segurou o atalho é "há quanto tempo
        # estou gravando isto", e o ponto passa a piscar em vermelho.
        if snapshot.long_recording:
            clock = format_elapsed(snapshot.long_elapsed_seconds)
            if status.level != "fail":
                label = f"REC · {snapshot.app}" if snapshot.app else "Gravando tudo"
            color = RECORD_RED
            if event is None:
                accent = RECORD_RED
            # Um segundo aceso, um apagado: a piscada nasce do próprio relógio,
            # sem redesenhar um quadro a mais do que a barra já desenha.
            blink = int(snapshot.long_elapsed_seconds) % 2 == 0

        # Parada, a barra compacta só muda quando o relógio vira — uma vez por
        # segundo. Redesenhá-la 15 vezes nesse intervalo seria puro desperdício
        # de CPU justamente durante o jogo, que é quando ela está na tela.
        key = (accent, color, label, clock, snapshot.long_recording and blink,
               None if event is None else (event[0], event[1], round(event[2].reveal, 3)))
        if key == self._compact_key:
            return
        self._compact_key = key

        self._resize(width, height)
        self._panel(width, height, accent)

        reveal = 0.0 if event is None else event[2].reveal
        middle = height / 2

        # Linha normal, deslocada para cima conforme o evento toma o lugar.
        y = middle - height * reveal
        if reveal < 1.2:
            dot = blend(BACKGROUND, color, 0.35) if snapshot.long_recording and not blink else color
            self.canvas.create_oval(14, y - 4, 22, y + 4, fill=dot, outline=dot)
            room = width - 32 - 12 - (self._font(9).measure(clock) + 10 if clock else 0)
            self._text(32, y, self._fit(label, room, 9, bold=True), TEXT, 9,
                       bold=True, anchor="w")
            if clock:
                self._text(width - 12, y, clock, MUTED, 9, anchor="e")

        if event is not None:
            kind, text, frame = event
            icon, tone, _duration = EVENT_STYLES[kind]
            y = middle + height * (1.0 - reveal)
            self._text(16, y, icon, tone, 9, bold=True)
            self._text(32, y, self._fit(text, width - 32 - 12, 9, bold=True),
                       blend(BACKGROUND, TEXT, frame.glow), 9, bold=True)

    def _render_expanded(self, snapshot: HudSnapshot, status: HudStatus,
                         levels: dict[str, float],
                         event: tuple[str, str, EventFrame] | None = None) -> None:
        width = self.EXPANDED_WIDTH
        color = LEVEL_COLORS.get(status.level, MUTED)
        meters = snapshot.meters
        alerts = [alert for alert in status.alerts if alert.level in {"fail", "warn"}]
        # A faixa cresce junto com a animação em vez de aparecer de uma vez: o
        # painel inteiro acompanha, sem o salto de altura que se notava antes.
        band = 0 if event is None else round(EVENT_BAND_PX * min(1.0, event[2].reveal))
        height = 46 + 18 * len(meters) + 16 * len(alerts) + 22 + band
        self._resize(width, height)
        # Durante o evento a barra lateral assume a cor dele: é o pulso que se
        # percebe pelo canto do olho, sem precisar ler nada.
        accent = color
        if event is not None:
            accent = blend(color, EVENT_STYLES[event[0]][1], event[2].glow)
        self._panel(width, height, accent)

        clock = (format_elapsed(snapshot.elapsed_seconds)
                 if snapshot.recording or snapshot.buffering else "")
        dot = color
        if snapshot.long_recording:
            clock = format_elapsed(snapshot.long_elapsed_seconds)
            if int(snapshot.long_elapsed_seconds) % 2 == 0 or status.level == "fail":
                dot = RECORD_RED
            else:
                dot = blend(BACKGROUND, RECORD_RED, 0.35)
        self.canvas.create_oval(14, 17, 22, 25, fill=dot, outline=dot)
        room = width - 32 - 14 - (self._font(10).measure(clock) + 10 if clock else 0)
        self._text(32, 21, self._fit(status.headline, room, 10, bold=True), TEXT, 10, bold=True)
        if clock:
            self._text(width - 14, 21, clock, MUTED, 10, anchor="e")

        subtitle = snapshot.app or "—"
        if snapshot.long_recording:
            subtitle += "  ·  gravando tudo (clipe + o que veio depois)"
        elif snapshot.mode == "clips":
            subtitle += "  ·  clipes"
        if snapshot.markers:
            subtitle += f"  ·  {snapshot.markers} marcador" + ("es" if snapshot.markers > 1 else "")
        self._text(14, 38, self._fit(subtitle, width - 28, 8), MUTED, 8)

        y = 56
        for meter in meters:
            self._render_meter(meter, levels.get(meter.label, SILENCE_DB), y, width)
            y += 18

        y += 4
        for alert in alerts:
            # O título já diz *qual* é a falha; repetir a mesma frase aqui só
            # gastaria a linha que devia explicar o que fazer a respeito.
            line = alert.detail if alert.text == status.headline else f"{alert.text} — {alert.detail}"
            self._text(14, y, "▲", LEVEL_COLORS.get(alert.level, MUTED), 8)
            self._text(28, y, self._fit(line, width - 28 - 14, 8),
                       LEVEL_COLORS.get(alert.level, MUTED), 8)
            y += 16

        if event is not None and band:
            self._render_event(event, height - band + 3, width, band)

    def _render_event(self, event: tuple[str, str, EventFrame], y: int, width: int,
                      band: int) -> None:
        """Faixa de confirmação: desliza da esquerda, acende e recolhe."""
        kind, label, frame = event
        icon, color, _duration = EVENT_STYLES[kind]
        left = 10 + frame.slide
        bottom = y + max(1, band - 6)
        fill = blend(BACKGROUND, color, 0.16 * frame.glow)
        edge = blend(BACKGROUND, color, 0.60 * frame.glow)
        self.canvas.create_rectangle(left, y, width - 10, bottom, fill=fill, outline=edge)
        middle = (y + bottom) / 2
        self._text(left + 11, middle, icon, blend(BACKGROUND, color, frame.glow), 9, bold=True)
        self._text(left + 28, middle,
                   self._fit(label, width - 10 - (left + 28) - 8, 9, bold=True),
                   blend(BACKGROUND, TEXT, frame.glow), 9, bold=True)

    def _render_meter(self, meter: Meter, display_db: float, y: int, width: int) -> None:
        bar_x, bar_width = 86, width - 86 - 58
        self._text(14, y, meter.label, MUTED, 8)
        self.canvas.create_rectangle(bar_x, y - 4, bar_x + bar_width, y + 4,
                                     fill=TRACK, outline="")
        if meter.muted:
            self._text(bar_x + 4, y, "mudo", LEVEL_COLORS["fail"], 8)
            return
        if not meter.present:
            self._text(bar_x + 4, y, "sem sinal", LEVEL_COLORS["warn"] if not meter.required
                       else LEVEL_COLORS["fail"], 8)
            return
        if meter.peak_db <= SOUND_FLOOR_DB and display_db <= SOUND_FLOOR_DB:
            # O trilho vazio continua delimitando onde a barra surgirá, mas o
            # texto torna inequívoco que não há áudio sendo capturado. Antes as
            # três linhas cinzas pareciam três barras ativas mesmo em -100 dB.
            self._text(bar_x + 4, y, "silêncio", MUTED, 8)
            self._text(width - 14, y, "−∞", MUTED, 8, anchor="e")
            return
        # Escala de -60 dB (piso audível) a 0 dB (saturação).
        filled = max(0.0, min(1.0, (display_db - SOUND_FLOOR_DB) / -SOUND_FLOOR_DB))
        color = LEVEL_COLORS["fail"] if display_db > -3 else LEVEL_COLORS["ok"]
        if filled > 0:
            self.canvas.create_rectangle(bar_x, y - 4, bar_x + bar_width * filled, y + 4,
                                         fill=color, outline="")
        reading = "—" if meter.peak_db <= SILENCE_DB else f"{meter.peak_db:.0f} dB"
        self._text(width - 14, y, reading, MUTED, 8, anchor="e")


# --- aplicação ---------------------------------------------------------------

class Hud:
    """Laço da interface: coleta, avalia, desenha e avisa."""

    DISPLAY_MODES = ("compact", "expanded", "hidden")

    def __init__(self, settings: HudSettings, collector=None, demo=None) -> None:
        self.settings = settings
        self.collector = collector
        self.demo = demo
        self.display_mode = "compact"
        self.stopping = False
        self._panels: list[HudPanel] = []
        self._targets: list[int] = []
        self._levels: dict[str, float] = {}
        self._last_draw = time.monotonic()
        self._signature: tuple | None = None
        self._sounded_at: dict[str, float] = {}
        self._placement_checked_at = 0.0
        self._event_seq = 0
        self._event_started = 0.0
        self._event: tuple[str, str] | None = None
        #: Avisos que o atalho mandou esconder. Enquanto só eles existirem, a
        #: HUD fica fora da tela, ainda que o modo escolhido a abrisse.
        self._dismissed: frozenset[str] | None = None
        self._alert_keys: frozenset[str] = frozenset()

    # --- estado -----------------------------------------------------------
    def _snapshot(self) -> HudSnapshot:
        if self.demo is not None:
            return self.demo()
        assert self.collector is not None
        return self.collector.snapshot()

    def _decay(self, snapshot: HudSnapshot) -> None:
        """Aplica queda suave às barras, para o medidor não piscar."""
        now = time.monotonic()
        step = METER_FALL_DB_PER_SECOND * (now - self._last_draw)
        self._last_draw = now
        for meter in snapshot.meters:
            current = self._levels.get(meter.label, SILENCE_DB)
            self._levels[meter.label] = max(meter.peak_db, current - step)

    @staticmethod
    def _signature_of(snapshot: HudSnapshot, status: HudStatus) -> tuple:
        """O que caracteriza uma mudança que precisa ser anunciada.

        De propósito não inclui os medidores nem o tempo: eles mudam sempre, e a
        HUD repetiria o mesmo aviso continuamente.
        """
        return (status.level, snapshot.recording, snapshot.buffering,
                snapshot.long_recording, snapshot.app,
                tuple(alert.key for alert in status.alerts))

    #: Acima desta idade o evento é história, não confirmação: a HUD que acaba
    #: de subir não deve reproduzir a animação de um marcador de minutos atrás.
    EVENT_MAX_AGE_SECONDS = 5.0

    def _observe_event(self, snapshot: HudSnapshot) -> None:
        """Reage a um acontecimento novo vindo do laço de vídeo."""
        if not snapshot.event_kind or snapshot.event_seq == self._event_seq:
            return
        self._event_seq = snapshot.event_seq
        if snapshot.event_age_seconds > self.EVENT_MAX_AGE_SECONDS:
            return
        # O relógio da animação é o desta máquina e começa agora: assim ela roda
        # inteira, em vez de já entrar pela metade por causa do atraso de leitura.
        self._event = (snapshot.event_kind, snapshot.event_label)
        self._event_started = time.monotonic()
        # A confirmação sonora do marcador é do laço de vídeo, que roda sempre;
        # tocá-la aqui também renderia dois bipes para o mesmo marcador.
        if snapshot.event_kind in {"clip_failed", "long_failed"} and self.settings.sound:
            _alert_sound()

    def _current_event(self) -> tuple[str, str, EventFrame] | None:
        if self._event is None:
            return None
        frame = event_animation(self._event[0], time.monotonic() - self._event_started)
        if frame is None:
            self._event = None
            return None
        return (self._event[0], self._event[1], frame)

    def _announce(self, status: HudStatus) -> None:
        if not self.settings.sound:
            return
        now = time.monotonic()
        for alert in status.failing:
            if now - self._sounded_at.get(alert.key, -1e9) < SOUND_COOLDOWN_SECONDS:
                continue
            self._sounded_at[alert.key] = now
            _alert_sound()
            log(f"[hud] {alert.text}: {alert.detail}")
            break  # um aviso por vez; uma sirene de falhas seria pior que nada

    def _note_alerts(self, status: HudStatus) -> None:
        """Guarda os avisos atuais e desfaz a dispensa quando eles mudam.

        A dispensa vale para *aqueles* avisos: um aviso novo é notícia e volta
        a abrir a HUD. Quando todos somem, ela também acaba — o próximo que
        aparecer precisa ser visto.
        """
        self._alert_keys = frozenset(alert.key for alert in status.alerts)
        if self._dismissed is not None and (
                not self._alert_keys or not self._alert_keys <= self._dismissed):
            self._dismissed = None

    @property
    def _forced_open(self) -> bool:
        """Os avisos estão abrindo a HUD além do que o modo escolhido pediria."""
        return bool(self._alert_keys) and self.display_mode != "expanded"

    def _should_show(self, snapshot: HudSnapshot, status: HudStatus,
                     event: tuple[str, str, EventFrame] | None) -> bool:
        if self._dismissed is not None:
            # No Linux a HUD não deixa o clique atravessar. Fora do jogo, com o
            # aviso da contagem aberto por cima, ela prendia o que estava atrás
            # até a folga vencer; dispensada, sai da frente de verdade.
            return False
        if self.display_mode == "hidden":
            # Oculto não significa surdo: qualquer aviso e toda confirmação
            # pontual ainda precisam atravessar o modo discreto.
            return bool(status.alerts) or event is not None
        return (snapshot.active or self.display_mode == "expanded"
                or bool(status.failing) or event is not None)

    def _should_expand(self, status: HudStatus) -> bool:
        return (self.display_mode == "expanded"
                or (self.display_mode in {"compact", "hidden"}
                    and bool(status.alerts)))

    # --- painéis ----------------------------------------------------------
    def _sync_panels(self, root) -> None:
        """Cria, move ou remove painéis conforme os monitores em jogo."""
        now = time.monotonic()
        if self._panels and now - self._placement_checked_at < 2.0:
            return
        self._placement_checked_at = now
        from . import get_backend

        backend = get_backend()
        try:
            monitors = backend.list_monitors()
            active = backend.active_monitor()
        except OSError:
            return
        targets = choose_monitors(self.settings.placement, monitors, active)
        indexes = [monitor.index for monitor in targets]
        if indexes == self._targets:
            for panel, monitor in zip(self._panels, targets):
                panel.move_to(monitor)
            return
        for panel in self._panels:
            panel.destroy()
        self._panels = [HudPanel(root, monitor, self.settings.corner) for monitor in targets]
        self._targets = indexes

    # --- laço -------------------------------------------------------------
    def _tick(self, root) -> None:
        if self.stopping:
            root.quit()
            return
        visible = True
        event = None
        try:
            snapshot = self._snapshot()
            status = evaluate(snapshot)
            self._note_alerts(status)
            self._decay(snapshot)
            self._observe_event(snapshot)
            event = self._current_event()

            signature = self._signature_of(snapshot, status)
            if signature != self._signature:
                self._signature = signature
                self._announce(status)

            visible = self._should_show(snapshot, status, event)
            if visible:
                self._sync_panels(root)
                # O evento **não** entra aqui de propósito: confirmar um
                # marcador não é motivo para abrir o painel inteiro por cima do
                # jogo. Ele aparece no formato que estiver valendo — no
                # compacto, trocando a linha; no expandido, na faixa de baixo.
                expanded = self._should_expand(status)
                for panel in self._panels:
                    panel.show()
                    panel.render(snapshot, status, self._levels, expanded, event)
            else:
                for panel in self._panels:
                    panel.hide()
        except Exception as exc:  # a HUD nunca pode derrubar a si mesma
            log(f"[hud] erro no desenho: {exc}")
        if not visible:
            delay = IDLE_TICK_MS
        else:
            delay = ANIMATION_TICK_MS if event is not None else TICK_MS
        root.after(delay, self._tick, root)

    def toggle(self) -> None:
        """Atalho da HUD: alterna o modo ou dispensa os avisos que a abriram.

        Com um aviso forçando a HUD aberta, girar o modo não mudaria nada na
        tela — o aviso a reabriria em qualquer um deles. Então o atalho a
        esconde até surgir um aviso diferente; apertado de novo, traz de volta.
        """
        if self._dismissed is not None:
            self._dismissed = None
            log("[hud] avisos à vista de novo")
            return
        if self._forced_open:
            self._dismissed = self._alert_keys
            log("[hud] avisos dispensados até surgir um novo")
            return
        current = self.DISPLAY_MODES.index(self.display_mode)
        self.display_mode = self.DISPLAY_MODES[(current + 1) % len(self.DISPLAY_MODES)]
        labels = {"compact": "compacto", "expanded": "expandido", "hidden": "oculto"}
        log(f"[hud] modo {labels[self.display_mode]}")

    def stop(self, _signum=None, _frame=None) -> None:
        self.stopping = True

    def run(self) -> int:
        import tkinter as tk

        _declare_dpi_aware()
        root = tk.Tk()
        root.withdraw()
        if self.collector is not None:
            self.collector.start()
        if IS_WINDOWS and self.settings.hotkey:
            from .winhotkey import MarkerHotkey

            MarkerHotkey(self.settings.hotkey, self.toggle).start()
        root.after(TICK_MS, self._tick, root)
        try:
            root.mainloop()
        finally:
            if self.collector is not None:
                self.collector.stop()
        return 0


# --- modos de teste ----------------------------------------------------------

#: Acontecimentos percorridos pelo ``--demo``, um de cada tipo.
_DEMO_EVENTS = [
    ("marker", "Marcador 3 · 12:04"),
    ("clip_saving", "Salvando clipe…"),
    ("clip_saved", "Clipe salvo · 60s"),
    ("clip_merged", "Clipe estendido · 1:35"),
    ("clip_failed", "O OBS não informou o arquivo"),
    ("ignored", "Nada sendo gravado"),
    ("marker_queued", "Marcador na próxima cena"),
    ("long_started", "Gravação longa iniciada"),
    ("long_saved", "Gravação longa salva · 2026-09-20_21-14-08_DP-1.mp4"),
]


def _demo_sequence():
    """Estados fabricados percorridos em laço, para ajustar a HUD sem jogo."""
    import math

    started = time.monotonic()

    def build() -> HudSnapshot:
        elapsed = time.monotonic() - started
        phase = int(elapsed // 8) % 4
        wave = (math.sin(elapsed * 3) + 1) / 2
        meters = [
            Meter("Microfone", peak_db=-55 + 45 * wave, present=True, required=True),
            Meter("Discord", peak_db=-40 + 20 * (1 - wave), present=True),
            Meter("Jogo", peak_db=-20 + 12 * wave, present=True),
        ]
        snapshot = HudSnapshot(
            backend="demo", available=True, enabled=True, recording=True,
            mode="continuous", app="Tabletop Simulator",
            elapsed_seconds=elapsed, output_bytes=int(elapsed * 900_000),
            video_hooked=True, capture_source="Captura de jogo",
            markers=int(elapsed // 20), meters=meters,
            disk_free_bytes=120 * 1024**3,
        )
        if phase == 1:  # captura não engatou
            snapshot.video_hooked = False
        elif phase == 2:  # microfone caiu
            meters[0].present = False
            meters[0].absent_seconds = 20.0
        elif phase == 3:  # modo clipes com uma gravação longa em curso
            snapshot.buffering = False
            snapshot.mode = "clips"
            snapshot.long_recording = True
            snapshot.long_elapsed_seconds = elapsed % 60

        # Um acontecimento a cada 4 s, percorrendo os tipos, para dar para ver a
        # animação sem precisar de um jogo aberto e do atalho na mão.
        beat = int(elapsed // 4)
        kind, label = _DEMO_EVENTS[beat % len(_DEMO_EVENTS)]
        snapshot.event_kind = kind
        snapshot.event_label = label
        snapshot.event_seq = beat
        snapshot.event_age_seconds = elapsed % 4
        return snapshot

    return build


def _probe(collector, seconds: float) -> int:
    """Imprime o estado lido, sem abrir janela. Diagnóstico puro."""
    collector.start()
    try:
        deadline = time.monotonic() + seconds
        snapshot = collector.snapshot()
        while time.monotonic() < deadline:
            time.sleep(0.25)
            snapshot = collector.snapshot()
    finally:
        collector.stop()
    status = evaluate(snapshot)
    print(json.dumps({
        "snapshot": dataclasses.asdict(snapshot),
        "status": dataclasses.asdict(status),
    }, ensure_ascii=False, indent=2, default=str))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="HUD de gravação: mostra sobre o jogo se a captura está saindo.")
    parser.add_argument("--probe", action="store_true",
                        help="imprime o estado coletado em JSON e sai, sem janela")
    parser.add_argument("--probe-seconds", type=float, default=3.0,
                        help="quanto tempo observar antes de imprimir (padrão: 3)")
    parser.add_argument("--demo", action="store_true",
                        help="abre a HUD com dados fabricados, para ajustar posição")
    parser.add_argument("--placement", choices=("game", "second", "both"),
                        help="sobrepõe a posição configurada")
    args = parser.parse_args(argv)

    settings = HudSettings.load()
    if args.placement:
        settings.placement = args.placement

    if args.probe:
        return _probe(get_collector(), args.probe_seconds)

    if args.demo:
        return Hud(settings, demo=_demo_sequence()).run()

    if not settings.enabled:
        log("[hud] desligada em video.conf; nada a fazer")
        return 0

    hud = Hud(settings, collector=get_collector())
    if IS_WINDOWS:
        from .winrecord import _install_stop_handlers

        _install_stop_handlers(hud.stop)
    else:
        import signal

        signal.signal(signal.SIGTERM, hud.stop)
        signal.signal(signal.SIGINT, hud.stop)
        signal.signal(signal.SIGUSR1, lambda _signum, _frame: hud.toggle())
    return hud.run()


if __name__ == "__main__":
    raise SystemExit(main())
