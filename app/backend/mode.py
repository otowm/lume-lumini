"""Em qual modo esta instalação foi montada.

O Lume completo grava, transcreve, descreve e resume. O **Lumini** é o mesmo
projeto instalado só como gravador: nada de Ollama, de whisper, de modelos de
áudio — e, por consequência, nada de análise na interface.

O modo não é preferência do usuário, é fato da instalação: descreve o que o
script de instalação pôs na máquina. Por isso ele mora num arquivo escrito pelo
instalador, e não numa tela de ajustes — um botão "ligar a IA" numa máquina sem
Ollama só produziria erro.

Também não é detectado. O Lume já degrada quando o Ollama cai
(``/api/ollama/models`` devolve ``online: false``), e isso é temporário por
natureza; transformar uma queda de serviço em interface mutilada seria confundir
sintoma com decisão.

A variável de ambiente vence o arquivo para que dê para experimentar o Lumini
numa instalação completa sem tocar no que está instalado::

    LUME_MODE=lumini .venv/bin/python -m uvicorn app.backend.main:app --port 8877
"""

from __future__ import annotations

import os

from .main_paths import CONFIG_DIR

#: ``completo`` é o Lume inteiro; ``lumini``, só o gravador.
MODOS = ("completo", "lumini")
PADRAO = "completo"
LUMINI = "lumini"

#: Escrito pelo instalador, uma chave por linha, no formato dos outros `.conf`.
MODE_CONFIG = CONFIG_DIR / "lume.conf"


def _do_arquivo() -> str:
    """Lê ``LUME_MODE`` do ``lume.conf``, sem depender do resto do backend.

    Parse próprio, de seis linhas, em vez de importar o leitor de config do
    ``main`` (que importaria o mundo) ou o de ``app.capture.base`` (que escolhe
    um backend de captura ao ser importado).
    """
    try:
        texto = MODE_CONFIG.read_text(encoding="utf-8-sig")
    except OSError:
        return ""
    for linha in texto.splitlines():
        chave, separador, valor = linha.strip().partition("=")
        if separador and chave.strip() == "LUME_MODE":
            return valor.strip().strip("\"'")
    return ""


def modo_atual() -> str:
    """O modo em vigor. Sem cache, de propósito.

    O arquivo tem uma linha, e ``/api/status`` já relê o ``video.conf`` inteiro a
    cada chamada. Em troca, trocar o modo passa a valer sem reiniciar o serviço —
    e os testes mexem em ``os.environ`` sem precisar recarregar módulo.
    """
    declarado = (os.environ.get("LUME_MODE") or _do_arquivo()).strip().lower()
    # Um valor com erro de digitação não pode desligar a análise de quem a tem:
    # o que não é reconhecido cai no completo.
    return declarado if declarado in MODOS else PADRAO


def e_lumini() -> bool:
    return modo_atual() == LUMINI
