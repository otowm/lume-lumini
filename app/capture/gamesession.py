"""Contagem de tempo por jogo, independente do que foi gravado.

O tempo de jogo é um fato separado do vídeo: uma partida sem nenhum clipe nem
segmento salvo ainda precisa aparecer no dia, e é daqui que
``apply_exact_game_durations`` tira o número exato que substitui a estimativa da
IA. Por isso a sessão vive em ``game_activity_sessions``, e não nos sidecars dos
arquivos de mídia — que só existem quando algo foi para o disco.

Os dois gravadores usam as mesmas funções, para que a semântica não divirja: o
do Windows (:mod:`app.capture.winvideo`) importa direto; o laço bash do Linux
(``bin/game-video-loop``) chama a CLI:

    python -m app.capture.gamesession begin --key K --window "W" --mode clips
    python -m app.capture.gamesession heartbeat --key K
    python -m app.capture.gamesession finish --key K --started EPOCH
    python -m app.capture.gamesession close-stale
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime

from .base import stable_app_label
from ..backend.database import connect, initialize

#: Intervalo mínimo entre batimentos. Um travamento do gravador perde no máximo
#: isto do tempo contado, porque ``close_stale`` fecha pelo último batimento.
HEARTBEAT_SECONDS = 10.0


def iso_time(timestamp: float) -> str:
    """Horário local com fuso explícito, no formato que a tabela guarda."""
    return datetime.fromtimestamp(timestamp).astimezone().isoformat()


def _ensure_schema() -> None:
    """Cria o esquema só quando a tabela ainda não existe.

    O gravador pode ser o primeiro a tocar no banco numa máquina nova. Chamar
    ``initialize`` direto seria caro no começo de cada partida — ela também roda
    as migrações de caminho de mídia —, então o teste barato vem antes.
    """
    with connect() as db:
        found = db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='game_activity_sessions'"
        ).fetchone()
    if not found:
        initialize()


def begin(session_key: str, window: str, mode: str, started_at: float) -> None:
    """Abre (ou reabre) a contagem de uma sessão.

    O ``ON CONFLICT`` existe porque a chave pode voltar depois de um
    ``close_stale``: quem reabre manda no início, na duração e no ``ended_at``.
    """
    started = iso_time(started_at)
    app = stable_app_label(window) or "Jogo"
    _ensure_schema()
    with connect() as db:
        db.execute(
            """INSERT INTO game_activity_sessions(
                   session_key,app,window,capture_mode,started_at,last_seen_at,ended_at,duration_seconds)
               VALUES(?,?,?,?,?,?,NULL,0)
               ON CONFLICT(session_key) DO UPDATE SET
                 app=excluded.app,window=excluded.window,capture_mode=excluded.capture_mode,
                 started_at=excluded.started_at,last_seen_at=excluded.last_seen_at,
                 ended_at=NULL,duration_seconds=0""",
            (session_key, app[:200], window[:1000], mode, started, started),
        )


def heartbeat(session_key: str, now: float | None = None) -> None:
    """Marca que a sessão continua viva e atualiza a duração parcial."""
    stamp = iso_time(now if now is not None else time.time())
    with connect() as db:
        db.execute(
            """UPDATE game_activity_sessions
               SET last_seen_at=?,
                   duration_seconds=MAX(0,(julianday(?)-julianday(started_at))*86400.0)
               WHERE session_key=? AND ended_at IS NULL""",
            (stamp, stamp, session_key),
        )


def finish(session_key: str, started_at: float, ended_at: float | None = None) -> float:
    """Fecha a sessão e devolve a duração final em segundos."""
    ended = ended_at if ended_at is not None else time.time()
    duration = max(0.0, ended - started_at)
    with connect() as db:
        db.execute(
            """UPDATE game_activity_sessions
               SET last_seen_at=?,ended_at=?,duration_seconds=? WHERE session_key=?""",
            (iso_time(ended), iso_time(ended), duration, session_key),
        )
    return duration


def close_stale() -> None:
    """Fecha sessões deixadas abertas por um desligamento abrupto.

    Sem isto uma queda de energia no meio da partida deixaria uma sessão sem
    ``ended_at`` para sempre, e o dia contaria o intervalo até agora. O último
    batimento é o instante mais recente em que sabemos que o jogo estava ali.
    """
    _ensure_schema()
    with connect() as db:
        db.execute(
            """UPDATE game_activity_sessions
               SET ended_at=last_seen_at,
                   duration_seconds=MAX(0,(julianday(last_seen_at)-julianday(started_at))*86400.0)
               WHERE ended_at IS NULL"""
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    opener = commands.add_parser("begin", help="abre a contagem de uma sessão")
    opener.add_argument("--key", required=True)
    opener.add_argument("--window", default="")
    opener.add_argument("--mode", default="continuous")
    opener.add_argument("--started", type=float, default=None,
                        help="epoch do início; o padrão é agora")

    beat = commands.add_parser("heartbeat", help="atualiza a duração parcial")
    beat.add_argument("--key", required=True)

    closer = commands.add_parser("finish", help="fecha a contagem de uma sessão")
    closer.add_argument("--key", required=True)
    closer.add_argument("--started", type=float, required=True)

    commands.add_parser("close-stale", help="fecha sessões abertas por uma queda")

    args = parser.parse_args(argv)
    if args.command == "begin":
        begin(args.key, args.window, args.mode,
              args.started if args.started is not None else time.time())
    elif args.command == "heartbeat":
        heartbeat(args.key)
    elif args.command == "finish":
        print(f"{finish(args.key, args.started) / 60:.1f}", file=sys.stderr)
    else:
        close_stale()
    return 0


if __name__ == "__main__":  # pragma: no cover - entrada de linha de comando
    raise SystemExit(main())
