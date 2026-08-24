"""Atalhos globais no Windows, registrados fora de qualquer janela.

No Linux o atalho é do KDE e chega ao processo como ``USR1``. O Windows não tem
``USR1``, e um atalho que só funcione com a janela em foco não serviria para
nada quando o objetivo é justamente agir com o **jogo** em foco. A saída é
``RegisterHotKey`` com janela nula, que entrega ``WM_HOTKEY`` na fila de
mensagens da thread — daí o laço próprio numa thread dedicada.

Vive num módulo separado porque tanto a gravação (marcador) quanto a HUD
(mostrar/esconder) precisam do mesmo mecanismo, em processos diferentes, e não
faria sentido a HUD arrastar o laço de vídeo inteiro só por causa disto.
"""

from __future__ import annotations

import ctypes
import re
import sys
import threading


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


class MarkerHotkey:
    """Atalho global que chama ``on_press`` a cada acionamento."""

    _MODIFIERS = {"ALT": 0x1, "CTRL": 0x2, "CONTROL": 0x2, "SHIFT": 0x4, "WIN": 0x8}
    _WM_HOTKEY = 0x0312

    #: Cada thread registra num espaço próprio, mas dois atalhos na mesma
    #: thread precisam de identificadores distintos.
    _next_id = 1

    def __init__(self, spec: str, on_press) -> None:
        self.spec = spec
        self.on_press = on_press
        self._thread = None

    @classmethod
    def _parse(cls, spec: str) -> tuple[int, int] | None:
        modifiers = 0
        key = None
        for part in spec.replace("-", "+").split("+"):
            token = part.strip().upper()
            if not token:
                continue
            if token in cls._MODIFIERS:
                modifiers |= cls._MODIFIERS[token]
            else:
                key = token
        if not key:
            return None
        if re.fullmatch(r"F([1-9]|1[0-9]|2[0-4])", key):
            return modifiers, 0x70 + int(key[1:]) - 1
        if len(key) == 1 and (key.isalpha() or key.isdigit()):
            return modifiers, ord(key)
        return None

    def start(self) -> None:
        parsed = self._parse(self.spec)
        if parsed is None:
            log(f"[aviso] atalho de marcador inválido: {self.spec!r}")
            return
        self._thread = threading.Thread(target=self._loop, args=parsed,
                                        name="lume-marker-hotkey", daemon=True)
        self._thread.start()

    def _loop(self, modifiers: int, vk: int) -> None:
        user32 = ctypes.windll.user32
        hotkey_id = MarkerHotkey._next_id
        MarkerHotkey._next_id += 1
        if not user32.RegisterHotKey(None, hotkey_id, modifiers, vk):
            log(f"[aviso] não foi possível registrar {self.spec!r} "
                f"(outro programa já usa esse atalho)")
            return
        log(f"[marcador] atalho {self.spec} registrado")

        class MSG(ctypes.Structure):
            _fields_ = [("hwnd", ctypes.c_void_p), ("message", ctypes.c_uint),
                        ("wParam", ctypes.c_void_p), ("lParam", ctypes.c_void_p),
                        ("time", ctypes.c_uint),
                        ("pt_x", ctypes.c_long), ("pt_y", ctypes.c_long)]

        message = MSG()
        try:
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == self._WM_HOTKEY:
                    try:
                        self.on_press()
                    except Exception as exc:  # nunca derrubar a thread do atalho
                        log(f"[marcador] falhou: {exc}")
        finally:
            user32.UnregisterHotKey(None, hotkey_id)
