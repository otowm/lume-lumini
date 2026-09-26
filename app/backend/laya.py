"""Cliente do daemon do Laya — classificação de texto por vocabulário fechado.

O ``laya-daemon.service`` mantém o modelo quente e atende num socket UNIX, uma
linha JSON por pedido. O Lume nunca carrega o modelo dentro do próprio
processo: o pipeline já divide GPU e memória com o whisper e o Ollama, e um
segundo residente de alguns gigabytes dentro da fila tiraria exatamente o que
ele economiza. Sem daemon no ar, quem chama decide o que fazer — aqui a
ausência é informada, nunca contornada carregando o modelo.

Protocolo (o mesmo do ``laya_organiza``):

    --> {"op": "classificar", "states": [...], "questions": {...}}
    <-- {"results": [{"answers": {"chave": {"choice": ..., "confidence": ...}}}]}
"""

from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass

TIMEOUT_SECONDS = float(os.environ.get("LUME_LAYA_TIMEOUT", "120"))
NENHUMA = "nenhuma"


def socket_path() -> str:
    """Onde o daemon escuta. No Windows não há socket UNIX — devolve vazio."""
    configured = os.environ.get("LAYA_SOCKET", "").strip()
    if configured:
        return configured
    if not hasattr(os, "getuid") or not hasattr(socket, "AF_UNIX"):
        return ""
    return f"/run/user/{os.getuid()}/laya-daemon.sock"


class LayaUnavailable(RuntimeError):
    """O daemon não está no ar, recusou o pedido ou respondeu algo ininteligível."""


@dataclass(frozen=True)
class Choice:
    """Uma resposta do Laya: a opção escolhida e o quanto ele confia nela."""

    choice: str
    confidence: float

    @property
    def is_none(self) -> bool:
        return self.choice == NENHUMA


def _request(payload: dict, timeout: float) -> object:
    path = socket_path()
    if not path or not os.path.exists(path):
        raise LayaUnavailable(f"daemon do Laya não está escutando em {path or '(sem socket nesta plataforma)'}")
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(timeout)
            client.connect(path)
            client.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
            data = b""
            while not data.endswith(b"\n"):
                chunk = client.recv(1 << 20)
                if not chunk:
                    break
                data += chunk
    except OSError as exc:
        raise LayaUnavailable(f"falha ao falar com o daemon do Laya: {exc}") from exc
    try:
        response = json.loads(data.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise LayaUnavailable(f"resposta ilegível do daemon do Laya: {exc}") from exc
    if "error" in response:
        raise LayaUnavailable(f"daemon do Laya recusou o pedido: {response['error']}")
    return response.get("results")


def available() -> bool:
    path = socket_path()
    return bool(path) and os.path.exists(path)


def status() -> dict:
    """Estado do daemon para a tela de diagnóstico; nunca levanta exceção."""
    path = socket_path()
    if not path:
        return {"available": False, "socket": "", "detail": "sem socket UNIX nesta plataforma"}
    if not os.path.exists(path):
        return {"available": False, "socket": path, "detail": "o daemon não está escutando"}
    try:
        results = _request({"op": "status"}, timeout=10)
    except LayaUnavailable as exc:
        return {"available": False, "socket": path, "detail": str(exc)}
    info = results if isinstance(results, dict) else {}
    return {
        "available": True,
        "socket": path,
        "detail": "",
        "model": str(info.get("modelo") or ""),
        "loaded": bool(info.get("laya_carregado")),
    }


def choose(states: list[str], instructions: str, criteria: dict[str, str], *,
           timeout: float = TIMEOUT_SECONDS) -> list[Choice]:
    """Uma pergunta de múltipla escolha para cada estado, num único lote.

    ``criteria`` é o vocabulário fechado: o Laya só pode responder uma de suas
    chaves. Cabe a quem chama incluir uma saída de escape (``NENHUMA``) — sem
    ela o modelo é obrigado a escolher, e passa a inventar parentescos.
    """
    if not states:
        return []
    if not criteria:
        raise LayaUnavailable("pergunta sem critérios: não há vocabulário para escolher")
    question = {"escolha": {"type": "choice", "instructions": instructions, "criteria": criteria}}
    results = _request({"op": "classificar", "states": states, "questions": question}, timeout)
    if not isinstance(results, list) or len(results) != len(states):
        raise LayaUnavailable("daemon do Laya devolveu um número de respostas diferente do pedido")
    answers = []
    for item in results:
        try:
            answer = item["answers"]["escolha"]
            answers.append(Choice(str(answer["choice"]).strip(), float(answer["confidence"])))
        except (KeyError, TypeError, ValueError) as exc:
            raise LayaUnavailable(f"resposta do Laya fora do formato esperado: {exc}") from exc
    return answers
