"""Mandar um clipe para alguém: nome legível, versão leve e link público.

O gravador nomeia por data — ``2026-09-26_00-10-34_DP-1.mp4`` — e a pasta acaba
com centenas de arquivos que só se distinguem pelo segundo em que foram salvos.
Quando a pessoa quer anexar *aquele* clipe no Discord, o seletor de arquivos não
ajuda em nada. Aqui o arquivo continua onde está: o que muda é o nome oferecido
no download, que sai do jogo gravado no sidecar e do título que a IA deu ao
clipe.

Três coisas vivem neste módulo, na ordem em que a pessoa encosta nelas:

* o **nome legível** do download (nada é copiado; quem renomeia é o header);
* a **versão leve**, recodificada para caber num teto de tamanho — porque um
  minuto de 1080p60 pesa ~57 MB e o Discord sem Nitro não aceita isso;
* o **link público**, para o que não cabe nem comprimido.

O upload é a única parte deste projeto que manda dados para fora da máquina.
Ele nunca acontece como efeito colateral: exige confirmação explícita em cada
envio, e nenhum outro módulo do Lume o chama.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import secrets
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from . import editing
from .database import connect
from .main_paths import (MEDIA_CACHE_DIR, media_source_key, resolve_media_source,
                         unlink_with_retry, video_game_label)

HIDDEN_PROCESS = getattr(subprocess, "CREATE_NO_WINDOW", 0)

#: Onde as versões leves ficam. É cache, e não biblioteca: em ``video-buffer``
#: elas virariam sósias de cada clipe em ``/api/videos`` — exatamente o
#: amontoado de arquivos que este módulo existe para resolver.
SHARE_CACHE_DIR = MEDIA_CACHE_DIR / "video-share"

#: Muda quando a receita de recodificação muda, para que um arquivo gerado pela
#: receita antiga não seja servido como se fosse da nova.
RECIPE_VERSION = 1

#: Tetos oferecidos, em MB. 20 é o limite de anexo do Discord sem Nitro; 50, o
#: do Nitro Básico e dos servidores impulsionados; 500, o do Nitro.
SIZE_PRESETS = (10, 20, 50, 500)
DEFAULT_LIMIT_MB = 20

#: O controle de bitrate erra para cima, e o contêiner tem seu próprio custo.
#: Mirar no teto cheio entregaria arquivos alguns por cento acima dele.
SAFETY = 0.92

#: Abaixo disto não existe vídeo assistível; melhor recusar e dizer o motivo do
#: que gastar CPU para entregar um borrão.
MIN_VIDEO_BITRATE = 150_000


class SharingError(RuntimeError):
    """Falha que o usuário precisa ler, não um defeito interno."""


class SharingCancelled(RuntimeError):
    """O envio foi interrompido a pedido de quem o começou."""


# --- nome legível -----------------------------------------------------------

def _clip_row(db, source_key: str):
    return db.execute(
        """SELECT id,captured_at,app,title,session_id,COALESCE(session_detached,0) AS detached
           FROM video_segments WHERE source_path=?""",
        (source_key,),
    ).fetchone()


def _session_position(db, row) -> tuple[int, int, str] | None:
    """Posição do trecho na sessão, na mesma ordem que a pasta de edição usa.

    Uma sessão de um clipe só não ganha numeração: "trecho 01 de 01" não diz
    nada a quem recebe o arquivo.
    """
    if row is None or row["session_id"] is None or row["detached"]:
        return None
    session = db.execute("SELECT name FROM video_sessions WHERE id=?", (row["session_id"],)).fetchone()
    clips = db.execute(
        """SELECT id FROM video_segments WHERE session_id=? AND COALESCE(session_detached,0)=0
           ORDER BY sort_order,captured_at,id""",
        (row["session_id"],),
    ).fetchall()
    identifiers = [item["id"] for item in clips]
    if len(identifiers) < 2 or row["id"] not in identifiers:
        return None
    return identifiers.index(row["id"]) + 1, len(identifiers), (session["name"] if session else "")


def share_stem(raw_path: str | Path, source: Path) -> str:
    """``2026-09-26 00-10 Sea of Thieves — trecho 02 de 05``, sem extensão.

    Vale para o clipe recém-gravado, que é o caso que importa: ele entra no
    banco como ``pending``, sem ``app`` e sem ``title``, e o jogo só existe no
    sidecar ``.window`` — de onde ``video_game_label`` o tira.
    """
    key = media_source_key(raw_path)
    with connect() as db:
        row = _clip_row(db, key)
        position = _session_position(db, row)
    game, _origin = video_game_label(key, row["app"] if row else "")
    captured = row["captured_at"] if row else ""
    if not captured:
        captured = datetime.fromtimestamp(source.stat().st_mtime).isoformat()
    subject = (row["title"] if row else "") or ""
    # O nome da sessão automática é o próprio título da janela, igual ao jogo:
    # usá-lo aqui daria "Sea of Thieves — Sea of Thieves". Só entra quando a
    # pessoa renomeou a sessão para algo que o jogo já não diz.
    if position and not subject and position[2].casefold() != game.casefold():
        subject = position[2]
    # Sem jogo e sem título não há o que dizer além da data: aí o nome do
    # arquivo do gravador ainda é melhor do que um carimbo solto.
    fallback = "" if game else source.name
    stem = editing.readable_name(captured, game, subject, fallback)
    if position:
        stem = f"{stem} — trecho {position[0]:02d} de {position[1]:02d}"
    return stem


def download_filename(raw_path: str | Path, source: Path) -> str:
    """Nome oferecido no download, com a extensão do arquivo original."""
    return f"{share_stem(raw_path, source)}{source.suffix.lower()}"


def light_filename(raw_path: str | Path, source: Path, limit_mb: int) -> str:
    """O teto entra no nome: duas versões do mesmo clipe não se confundem."""
    return f"{share_stem(raw_path, source)} ({int(limit_mb)} MB).mp4"


# --- plano da versão leve ---------------------------------------------------

@dataclass(frozen=True)
class SharePlan:
    """A receita que cabe no teto: quanto bitrate, em que tamanho de imagem."""

    limit_bytes: int
    duration: float
    height: int
    fps: int
    video_bitrate: int
    audio_bitrate: int
    scale: bool
    resample: bool
    #: O original já cabe no teto e só o áudio muda (volumes salvos): a imagem
    #: é copiada como está, sem perder qualidade nem gastar CPU recodificando.
    copy_video: bool = False

    @property
    def estimated_bytes(self) -> int:
        return int((self.video_bitrate + self.audio_bitrate) * self.duration / 8)


#: Bitrate mínimo para cada degrau, escolhido por bits por pixel por quadro
#: (~0,04 em gameplay com libx264). A escada **preserva os 60 fps** enquanto o
#: bitrate aguentar: numa jogada, a fluidez lê melhor do que a nitidez — cair
#: para 30 fps em 1080p deixa o movimento picado justamente no momento que a
#: pessoa quer mostrar.
LADDER = (
    (4_500_000, 1080, 60),
    (2_200_000, 720, 60),
    (1_100_000, 720, 30),
    (600_000, 540, 30),
    (MIN_VIDEO_BITRATE, 480, 30),
)


def share_plan(limit_mb: int, duration: float, height: int = 1080, fps: float = 60.0,
               source_bitrate: int = 0) -> SharePlan:
    """Bitrate que cabe no teto, e o tamanho de imagem que esse bitrate aguenta.

    Recusa antes de gastar CPU quando não há receita possível: meia hora de
    gravação não entra em 20 MB nem em 240p, e descobrir isso depois de dez
    minutos de ffmpeg seria pior do que ouvir um "não" na hora.
    """
    limit_bytes = max(1, int(limit_mb)) * 1024 * 1024
    duration = max(0.5, float(duration or 0))
    budget_bits = limit_bytes * 8 * SAFETY
    audio_bitrate = 128_000
    total = budget_bits / duration
    # Num teto apertado, 32 kbps a menos de áudio valem mais do que 32 kbps a
    # menos de vídeo: a voz continua inteligível, a imagem não.
    if total - audio_bitrate < 400_000:
        audio_bitrate = 96_000
    budget_bitrate = int(total - audio_bitrate)
    video_bitrate = budget_bitrate
    if video_bitrate < MIN_VIDEO_BITRATE:
        minutes, seconds = divmod(int(duration), 60)
        raise SharingError(
            f"Um vídeo de {minutes}min{seconds:02d}s não cabe em {int(limit_mb)} MB "
            "nem na pior qualidade. Escolha um teto maior ou corte o trecho antes."
        )
    source_height = max(1, int(height or 1080))
    source_fps = max(1, int(round(fps or 60)))
    # A escada responde "quantos pixels este orçamento carrega?", então ela lê o
    # bitrate que o teto permite — não o que a origem por acaso gastou.
    target_height, target_fps = LADDER[-1][1], LADDER[-1][2]
    for floor, ladder_height, ladder_fps in LADDER:
        if budget_bitrate >= floor:
            target_height, target_fps = ladder_height, ladder_fps
            break
    # Já escolhida a imagem, um teto folgado não é licença para inflar: pedir
    # 63 Mbps de um vídeo gravado a 2,3 gastaria minutos de CPU para entregar um
    # arquivo maior que o original e idêntico a ele na tela.
    if source_bitrate > 0:
        video_bitrate = min(video_bitrate, int(source_bitrate * 0.95))
    # Nunca aumentar nada: recodificar 720p30 para 1080p60 gastaria bytes
    # inventando quadros e linhas que o original não tem.
    target_height = min(target_height, source_height)
    target_fps = min(target_fps, source_fps)
    return SharePlan(
        limit_bytes=limit_bytes, duration=duration, height=target_height, fps=target_fps,
        video_bitrate=video_bitrate, audio_bitrate=audio_bitrate,
        scale=target_height < source_height, resample=target_fps < source_fps,
    )


# --- volumes salvos ---------------------------------------------------------

def load_audio_mix(raw_path: str | Path) -> dict[int, float]:
    """Volumes salvos no player, por posição da faixa de áudio (``0:a:N``)."""
    with connect() as db:
        row = db.execute("SELECT volumes_json FROM video_audio_mix WHERE source_path=?",
                         (media_source_key(raw_path),)).fetchone()
    if row is None:
        return {}
    try:
        raw = json.loads(row["volumes_json"] or "{}")
        return {int(track): max(0.0, min(2.0, float(volume))) for track, volume in raw.items()}
    except (ValueError, TypeError, AttributeError):
        return {}


def save_audio_mix(raw_path: str | Path, volumes: dict[int, float]) -> None:
    key = media_source_key(raw_path)
    with connect() as db:
        if volumes:
            db.execute(
                """INSERT INTO video_audio_mix(source_path,volumes_json,updated_at)
                   VALUES(?,?,CURRENT_TIMESTAMP)
                   ON CONFLICT(source_path) DO UPDATE SET volumes_json=excluded.volumes_json,
                                                        updated_at=CURRENT_TIMESTAMP""",
                (key, json.dumps({str(track): volume for track, volume in sorted(volumes.items())})))
        else:
            db.execute("DELETE FROM video_audio_mix WHERE source_path=?", (key,))


def audio_mix(raw_path: str | Path) -> dict[int, float] | None:
    """A mixagem a aplicar no envio, ou ``None`` quando nada foi mexido.

    Tudo em 100% é o mesmo que a faixa de mixagem que o arquivo já tem: aí
    vale o caminho de sempre, e o original que cabe no teto segue intocado.
    """
    mix = load_audio_mix(raw_path)
    if not mix or all(abs(volume - 1.0) < 0.005 for volume in mix.values()):
        return None
    return mix


def _mix_tag(mix: dict[int, float] | None) -> str:
    if not mix:
        return ""
    identity = json.dumps(sorted((track, round(volume, 3)) for track, volume in mix.items()))
    return "-m" + hashlib.sha256(identity.encode()).hexdigest()[:10]


#: "Leia do banco": a maioria dos chamadores quer a mixagem salva agora; o
#: trabalho de recodificação fixa a dele ao nascer, para o arquivo bater com o
#: nome mesmo que alguém salve outros volumes no meio do caminho.
_CURRENT_MIX: dict = {}


def light_video_command(source: Path, destination: Path, plan: SharePlan,
                        preset: str = "fast", mix: dict[int, float] | None = None) -> list[str]:
    """Recodificação que cabe no teto e serve para ser assistida por outra pessoa.

    Três escolhas que não são detalhe:

    * ``-map 0:a:0`` e nunca ``0:a?`` — o arquivo tem quatro faixas (mixagem,
      microfone, Discord, sistema). Levar as quatro quadruplica o áudio, estoura
      o teto e publica o microfone da pessoa numa faixa separada.
    * bitrate médio de uma passada, com ``-maxrate``/``-bufsize`` de folga:
      cravar o teto no milímetro não vale dobrar o tempo de CPU, e um estouro
      pequeno é corrigido numa segunda tentativa.
    * mp4 com ``yuv420p`` e ``+faststart`` mesmo quando a origem é mkv — é o que
      o Discord e o navegador mostram sem baixar o arquivo inteiro primeiro.

    Com volumes salvos (``mix``), a faixa única deixa de ser a mixagem pronta e
    passa a ser microfone, Discord e sistema somados nos volumes escolhidos.
    """
    filters = []
    if plan.scale:
        # ``-2`` mantém a proporção e garante largura par, que o H.264 exige.
        filters.append(f"scale=-2:{plan.height}")
    if plan.resample:
        filters.append(f"fps={plan.fps}")
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
        "-progress", "pipe:1", "-nostats", "-i", str(source),
    ]
    if mix:
        tracks = sorted(mix)
        branches = "".join(
            f"[0:a:{track}]aformat=channel_layouts=stereo,volume={mix[track]:.3f}[t{track}];"
            for track in tracks)
        inputs = "".join(f"[t{track}]" for track in tracks)
        # Soma sem normalizar — é o que o player faz ao tocar as faixas juntas —
        # e um limitador só para os picos que a soma empurrar além do teto.
        command += ["-filter_complex",
                    f"{branches}{inputs}amix=inputs={len(tracks)}:normalize=0,"
                    f"alimiter=limit=0.95:level=0[mix]",
                    "-map", "0:v:0", "-map", "[mix]"]
    else:
        command += ["-map", "0:v:0", "-map", "0:a:0"]
    command += ["-map_metadata", "0", "-sn", "-dn"]
    if plan.copy_video:
        command += ["-c:v", "copy"]
    else:
        if filters:
            command += ["-vf", ",".join(filters)]
        command += [
            "-c:v", "libx264", "-preset", preset, "-pix_fmt", "yuv420p",
            "-b:v", str(plan.video_bitrate),
            "-maxrate", str(int(plan.video_bitrate * 1.07)),
            "-bufsize", str(plan.video_bitrate * 2),
        ]
    command += [
        "-c:a", "aac", "-b:a", str(plan.audio_bitrate), "-ac", "2", "-ar", "48000",
        "-movflags", "+faststart", str(destination),
    ]
    return command


_PROGRESS_TIME = re.compile(r"^out_time_us=(\d+)$")


def progress_percent(line: str, duration: float) -> int | None:
    """Lê ``out_time_us=12500000`` do ``-progress`` e devolve 21 num clipe de 60s.

    Função pura porque é o único sinal de andamento que a interface tem: sem
    ela, a recodificação seria uma barra parada em 0% por meio minuto.
    """
    match = _PROGRESS_TIME.match(line.strip())
    if not match or duration <= 0:
        return None
    seconds = int(match.group(1)) / 1_000_000
    return max(0, min(99, int(seconds / duration * 100)))


# --- cache ------------------------------------------------------------------

def share_digest(source: Path) -> str:
    identity = media_source_key(source).encode("utf-8", errors="surrogatepass")
    return hashlib.sha256(identity).hexdigest()


def share_cache_path(source: Path, limit_mb: int, mix: dict | None = _CURRENT_MIX) -> Path:
    """O teto e a receita ficam **fora** do hash, de propósito.

    Assim a limpeza de caches do vídeo acha todas as versões leves dele com um
    ``glob`` só, sem precisar saber quais tetos já foram pedidos. A mixagem
    entra no nome: mudar os volumes nunca serve a versão com os antigos.
    """
    if mix is _CURRENT_MIX:
        mix = audio_mix(source)
    return SHARE_CACHE_DIR / (f"{share_digest(source)}-{int(limit_mb)}mb{_mix_tag(mix)}"
                              f"-v{RECIPE_VERSION}.mp4")


def share_cache_glob(source: Path) -> str:
    return f"{share_digest(source)}-*.mp4"


def share_cached(source: Path, limit_mb: int, mix: dict | None = _CURRENT_MIX) -> Path | None:
    """Versão leve pronta e mais nova que o original, ou nada.

    O corte (``/api/videos/{id}/trim``) reescreve o arquivo no lugar mantendo o
    nome: sem comparar a data de modificação, a pessoa baixaria o trecho antigo.
    """
    destination = share_cache_path(source, limit_mb, mix)
    try:
        if destination.is_file() and destination.stat().st_mtime_ns >= source.stat().st_mtime_ns:
            return destination
    except OSError:
        return None
    return None


def prune_share_cache(max_age_days: int = 14, max_bytes: int = 4 * 1024 ** 3) -> int:
    """Segura o tamanho do cache: são arquivos de dezenas de MB.

    Nada no Lume apaga vídeo por idade, e estas cópias existem para um envio que
    já aconteceu — guardá-las para sempre seria cobrar disco por nada.
    """
    if not SHARE_CACHE_DIR.is_dir():
        return 0
    entries = []
    for path in SHARE_CACHE_DIR.glob("*.mp4"):
        try:
            stats = path.stat()
        except OSError:
            continue
        entries.append((stats.st_mtime, stats.st_size, path))
    entries.sort(reverse=True)
    cutoff = time.time() - max_age_days * 86400
    removed, kept_bytes = 0, 0
    for modified, size, path in entries:
        kept_bytes += size
        if modified >= cutoff and kept_bytes <= max_bytes:
            continue
        try:
            unlink_with_retry(path, attempts=5)
            removed += 1
            kept_bytes -= size
        except OSError:
            pass
    return removed


# --- leitura do original ----------------------------------------------------

@dataclass(frozen=True)
class VideoShape:
    duration: float
    height: int
    fps: float
    bitrate: int = 0


def probe_video_shape(source: Path) -> VideoShape:
    """Duração, altura e fps num ``ffprobe`` só.

    A duração do banco não serve aqui: um clipe recém-gravado ainda está
    ``pending`` e com ``duration_seconds`` zerado, e é justamente o clipe recém
    -gravado que a pessoa quer mandar.
    """
    try:
        result = subprocess.run([
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=height,r_frame_rate:format=duration,bit_rate",
            # Com as chaves, e não por posição: uma linha "N/A" a mais bastaria
            # para a duração ser lida como altura.
            "-of", "default=noprint_wrappers=1", str(source),
        ], capture_output=True, text=True, timeout=60, creationflags=HIDDEN_PROCESS)
    except (OSError, subprocess.SubprocessError) as exc:
        raise SharingError(f"Não deu para ler o vídeo: {exc}") from exc
    values: dict[str, str] = {}
    for line in result.stdout.splitlines():
        key, separator, value = line.strip().partition("=")
        if separator and value and value != "N/A":
            values.setdefault(key, value)
    duration = _as_float(values.get("duration"), 0.0)
    if duration <= 0:
        raise SharingError("Não foi possível ler a duração do vídeo.")
    return VideoShape(
        duration=duration,
        height=int(_as_float(values.get("height"), 1080.0)) or 1080,
        fps=_as_ratio(values.get("r_frame_rate"), 60.0),
        bitrate=int(_as_float(values.get("bit_rate"), 0.0)),
    )


def _as_float(raw: str | None, fallback: float) -> float:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return fallback
    return value if math.isfinite(value) and value > 0 else fallback


def _as_ratio(raw: str | None, fallback: float) -> float:
    """``60/1`` → 60.0; é assim que o ffprobe conta quadros por segundo."""
    numerator, separator, denominator = str(raw or "").partition("/")
    if not separator:
        return _as_float(raw, fallback)
    try:
        value = float(numerator) / float(denominator or 1)
    except (ValueError, ZeroDivisionError):
        return fallback
    return value if math.isfinite(value) and value > 0 else fallback


#: A forma do vídeo não muda enquanto o arquivo não muda, e a interface consulta
#: o estado a cada poucos segundos: sem memória, cada volta pagaria um ffprobe.
_SHAPES: dict[tuple[str, int], VideoShape] = {}
_SHAPES_LOCK = threading.Lock()


def video_shape(source: Path) -> VideoShape:
    key = (str(source), source.stat().st_mtime_ns)
    with _SHAPES_LOCK:
        cached = _SHAPES.get(key)
    if cached is not None:
        return cached
    shape = probe_video_shape(source)
    with _SHAPES_LOCK:
        if len(_SHAPES) > 64:
            _SHAPES.clear()
        _SHAPES[key] = shape
    return shape


# --- versão leve em segundo plano -------------------------------------------

#: Uma recodificação por vez. libx264 já usa todos os núcleos, e duas em
#: paralelo só fariam as duas demorarem o dobro — com o jogo rodando ao lado.
_ENCODE_LOCK = threading.Lock()
_LIGHT_JOBS: dict[tuple[str, int, str], "_LightVersionJob"] = {}
_LIGHT_JOBS_LOCK = threading.Lock()


class _LightVersionJob:
    """Recodifica fora da requisição HTTP, com progresso e cancelamento.

    Mesmo molde do ``_VideoAudioTrackJob``: um arquivo temporário que só vira
    cache no ``os.replace`` final, para que uma recodificação interrompida nunca
    seja servida como pronta.
    """

    def __init__(self, source: Path, limit_mb: int, plan: SharePlan,
                 mix: dict[int, float] | None = None) -> None:
        self.id = secrets.token_urlsafe(12)
        self.source = source
        self.limit_mb = int(limit_mb)
        self.plan = plan
        self.mix = mix
        self.status = "preparing"
        self.error = ""
        self.progress = 0
        self.bytes = 0
        self.cancelled = threading.Event()
        self._process_lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._thread = threading.Thread(target=self._run, name=f"video-light-{self.id}", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def cancel(self) -> None:
        self.cancelled.set()
        with self._process_lock:
            process = self._process
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass
        if threading.current_thread() is not self._thread:
            self._thread.join(timeout=5)

    @staticmethod
    def _stop_process(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        try:
            process.terminate()
            process.wait(timeout=2)
        except (OSError, subprocess.TimeoutExpired):
            try:
                process.kill()
                process.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                pass

    def _watch_progress(self, process: subprocess.Popen[str]) -> None:
        """Lê o ``-progress`` numa thread só sua.

        A leitura de pipe bloqueia, e o laço principal precisa continuar
        conferindo o cancelamento e o prazo: quem trava aqui é esta thread, que
        morre junto com o pipe.
        """
        stream = process.stdout
        if stream is None:
            return
        try:
            for line in stream:
                percent = progress_percent(line, self.plan.duration)
                if percent is not None:
                    self.progress = percent
        except (OSError, ValueError):
            pass

    def _encode(self, plan: SharePlan, destination: Path) -> bool:
        destination.unlink(missing_ok=True)
        command = light_video_command(self.source, destination, plan, mix=self.mix)
        process = subprocess.Popen(
            command, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            env=os.environ.copy(), creationflags=HIDDEN_PROCESS,
        )
        with self._process_lock:
            self._process = process
        threading.Thread(target=self._watch_progress, args=(process,),
                         name=f"video-light-progress-{self.id}", daemon=True).start()
        # Recodificar é mais caro que remuxar: o prazo acompanha a duração em vez
        # de ser um número fixo que estouraria numa sessão longa.
        deadline = time.monotonic() + max(600.0, min(21600.0, self.plan.duration * 6 + 300.0))
        try:
            while process.poll() is None and not self.cancelled.wait(0.2):
                if time.monotonic() >= deadline:
                    self.error = "Tempo esgotado ao gerar a versão leve"
                    self.cancelled.set()
            if self.cancelled.is_set():
                self._stop_process(process)
                return False
            process.wait()
            return process.returncode == 0 and destination.is_file() and destination.stat().st_size > 0
        finally:
            if process.poll() is None:
                self._stop_process(process)
            with self._process_lock:
                self._process = None

    def _run(self) -> None:
        destination = share_cache_path(self.source, self.limit_mb, self.mix)
        temporary = destination.with_name(f"{destination.stem}.{self.id}.tmp.mp4")
        acquired = False
        try:
            while not self.cancelled.is_set():
                acquired = _ENCODE_LOCK.acquire(timeout=0.2)
                if acquired:
                    break
            if not acquired or self.cancelled.is_set():
                self.status = "cancelled"
                return
            # Alguém pode ter gerado a mesma versão enquanto esperávamos a vez.
            if share_cached(self.source, self.limit_mb, self.mix) is not None:
                self.status = "ready"
                self.progress = 100
                return
            SHARE_CACHE_DIR.mkdir(parents=True, exist_ok=True)
            prune_share_cache()
            if not self._encode(self.plan, temporary):
                self.status = "cancelled" if not self.error else "error"
                if self.status == "error" and not self.error:
                    self.error = "O FFmpeg não conseguiu gerar a versão leve"
                return
            size = temporary.stat().st_size
            if size > self.plan.limit_bytes and not self.plan.copy_video:
                # O controle de bitrate erra para cima em cena muito movimentada.
                # Uma correção só, proporcional ao excesso: insistir mais seria
                # gastar CPU atrás de um teto que talvez não caiba.
                corrected = int(self.plan.video_bitrate * self.plan.limit_bytes * SAFETY / size)
                self.progress = 0
                if corrected >= MIN_VIDEO_BITRATE:
                    retry = replace(self.plan, video_bitrate=corrected)
                    if not self._encode(retry, temporary):
                        self.status = "cancelled" if not self.error else "error"
                        return
                    size = temporary.stat().st_size
            if size > self.plan.limit_bytes:
                self.bytes = size
                self.status = "too_big"
                self.error = (f"A versão leve chegou a {size / 1024 / 1024:.1f} MB e o teto é "
                              f"{self.limit_mb} MB. Tente um teto maior ou corte o trecho.")
                return
            os.replace(temporary, destination)
            self.bytes = size
            self.progress = 100
            self.status = "ready"
        except (OSError, subprocess.SubprocessError) as exc:
            self.error = str(exc)
            self.status = "error"
        finally:
            try:
                unlink_with_retry(temporary, attempts=5)
            except OSError:
                # Derivado sem valor: a próxima limpeza do cache o leva.
                pass
            if acquired:
                _ENCODE_LOCK.release()


def normalized_limit(limit_mb: int | None) -> int:
    limit = int(limit_mb or DEFAULT_LIMIT_MB)
    if limit < 1 or limit > 4096:
        raise SharingError("O teto de tamanho precisa estar entre 1 MB e 4096 MB.")
    return limit


def cancel_light_jobs(source: Path | None = None) -> int:
    """Interrompe recodificações — de um vídeo, ou de todos ao sair."""
    with _LIGHT_JOBS_LOCK:
        keys = [key for key in _LIGHT_JOBS if source is None or key[0] == str(source)]
        jobs = [_LIGHT_JOBS.pop(key) for key in keys]
    for job in jobs:
        job.cancel()
    return len(jobs)


def light_state(raw_path: str | Path, source: Path, limit_mb: int | None = None,
                start: bool = False) -> dict:
    """O que a interface precisa saber sobre a versão leve deste clipe.

    ``start`` separa consulta de ação: o ``GET`` nunca liga o ventilador, e é o
    ``POST`` que decide gastar CPU. (``/api/video-audio-tracks`` faz o contrário,
    e é por isso que abrir um player já disparava trabalho.)
    """
    limit = normalized_limit(limit_mb)
    limit_bytes = limit * 1024 * 1024
    size = source.stat().st_size
    mix = audio_mix(source)
    state = {
        "limit_mb": limit, "presets": list(SIZE_PRESETS), "source_bytes": size,
        "name": light_filename(raw_path, source, limit), "status": "absent",
        "progress": 0, "bytes": 0, "error": "", "plan": None, "mixed": mix is not None,
        # ``safe=""`` para a barra da chave ``media:video-buffer/…`` também virar
        # ``%2F``: a URL vai inteira dentro de um parâmetro de consulta.
        "url": (f"/api/video-light?path={urllib.parse.quote(media_source_key(raw_path), safe='')}"
                f"&limit_mb={limit}"),
    }
    if size <= limit_bytes and mix is None:
        # O original já cabe: recodificar só pioraria a imagem para chegar ao
        # mesmo lugar.
        state["status"] = "fits"
        return state
    try:
        shape = video_shape(source)
        if size <= limit_bytes:
            # Cabe, mas com volumes salvos: a imagem vai como está e só o áudio
            # é refeito. O arquivo só encolhe — sai uma faixa no lugar de quatro.
            plan = SharePlan(limit_bytes=limit_bytes, duration=max(0.5, shape.duration),
                             height=shape.height, fps=int(round(shape.fps)),
                             video_bitrate=int(size * 8 / max(0.5, shape.duration)),
                             audio_bitrate=160_000, scale=False, resample=False, copy_video=True)
        else:
            plan = share_plan(limit, shape.duration, shape.height, shape.fps, shape.bitrate)
    except SharingError as exc:
        state["status"] = "too_big"
        state["error"] = str(exc)
        return state
    state["plan"] = {
        "height": plan.height, "fps": plan.fps, "video_bitrate": plan.video_bitrate,
        "audio_bitrate": plan.audio_bitrate, "duration": round(plan.duration, 3),
        "estimated_bytes": plan.estimated_bytes, "copy_video": plan.copy_video,
    }
    ready = share_cached(source, limit, mix)
    key = (str(source), limit, _mix_tag(mix))
    started = None
    with _LIGHT_JOBS_LOCK:
        job = _LIGHT_JOBS.get(key)
        # Um trabalho terminado não é estado: ou virou cache, ou o pedido novo
        # merece uma tentativa limpa em vez de reler o erro da anterior.
        if job is not None and (job.status in {"ready", "cancelled"}
                                or (start and job.status in {"error", "too_big"})):
            _LIGHT_JOBS.pop(key, None)
            job = None
        if job is None and start and ready is None:
            job = started = _LightVersionJob(source, limit, plan, mix)
            _LIGHT_JOBS[key] = job
    if started is not None:
        started.start()
    if ready is not None and (job is None or job.status == "ready"):
        state["status"] = "ready"
        state["progress"] = 100
        state["bytes"] = ready.stat().st_size
        return state
    if job is not None:
        state["status"] = job.status if job.status != "cancelled" else "absent"
        state["progress"] = job.progress
        state["error"] = job.error
        state["job_id"] = job.id
        if job.bytes:
            state["bytes"] = job.bytes
    return state


# --- link público -----------------------------------------------------------

@dataclass(frozen=True)
class Host:
    """Um lugar onde o arquivo pode ser publicado, sem conta e sem login."""

    name: str
    label: str
    url: str
    field: str
    prefix: str
    max_bytes: int
    permanent: bool
    expiry_options: tuple[str, ...] = ()

    def fields(self, expires: str) -> dict[str, str]:
        values = {"reqtype": "fileupload"}
        if self.expiry_options:
            values["time"] = expires if expires in self.expiry_options else self.expiry_options[-1]
        return values

    def parse(self, body: str) -> str:
        """A resposta é a URL em texto puro — e o erro também vem como HTTP 200.

        Por isso a validação é pelo prefixo: qualquer outra coisa é a mensagem do
        host, e vale mais mostrada do que engolida.
        """
        text = (body or "").strip()
        if text.startswith(self.prefix):
            return text
        raise SharingError(f"O {self.label} recusou o envio: {text[:200] or 'resposta vazia'}")

    def expires_at(self, expires: str) -> str | None:
        if self.permanent or not self.expiry_options:
            return None
        hours = int(re.sub(r"\D", "", expires) or 72)
        return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


HOSTS: dict[str, Host] = {
    # Temporário por construção: o link do amigo morre em três dias em vez de
    # virar um vídeo seu permanentemente no ar.
    "litterbox": Host(
        name="litterbox", label="litterbox", field="fileToUpload",
        url="https://litterbox.catbox.moe/resources/internals/api.php",
        prefix="https://litter.catbox.moe/", max_bytes=1024 * 1024 * 1024,
        permanent=False, expiry_options=("1h", "12h", "24h", "72h"),
    ),
    # Permanente. Nunca é escolhido por padrão nem como alternativa automática:
    # "para sempre" é decisão de quem publica.
    "catbox": Host(
        name="catbox", label="catbox", field="fileToUpload",
        url="https://catbox.moe/user/api.php", prefix="https://files.catbox.moe/",
        max_bytes=200 * 1024 * 1024, permanent=True,
    ),
}
DEFAULT_HOST = "litterbox"
DEFAULT_EXPIRES = "72h"
UPLOAD_USER_AGENT = "Lume/0.1 (+https://github.com/otowm/lume)"


def host_catalog() -> list[dict]:
    return [{
        "name": host.name, "label": host.label, "max_bytes": host.max_bytes,
        "permanent": host.permanent, "expiry_options": list(host.expiry_options),
    } for host in HOSTS.values()]


def resolve_host(name: str | None) -> Host:
    host = HOSTS.get((name or DEFAULT_HOST).strip().lower())
    if host is None:
        raise SharingError(f"Host desconhecido: {name!r}.")
    return host


class MultipartBody:
    """Corpo multipart que lê o arquivo em blocos e sabe o próprio tamanho.

    O tamanho não é conveniência: o ``urllib`` só declara ``Content-Length``
    quando recebe ``bytes``, e com um objeto de leitura qualquer ele cai em
    ``Transfer-Encoding: chunked`` — que o PHP do catbox recusa. Carregar 60 MB
    na memória para contornar isso seria pior.
    """

    def __init__(self, fields: dict[str, str], field: str, path: Path, filename: str,
                 on_progress=None, should_stop=None, block: int = 65536) -> None:
        self.boundary = secrets.token_hex(16)
        self.block = block
        self._on_progress = on_progress
        self._should_stop = should_stop
        self._path = path
        self.total = path.stat().st_size
        self.sent = 0
        head = []
        for name, value in fields.items():
            head.append(f"--{self.boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n")
        head.append(
            f"--{self.boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; "
            f"filename=\"{filename}\"\r\nContent-Type: application/octet-stream\r\n\r\n"
        )
        self._head = "".join(head).encode("utf-8")
        self._tail = f"\r\n--{self.boundary}--\r\n".encode("utf-8")
        self.length = len(self._head) + self.total + len(self._tail)
        self._handle = None

    @property
    def content_type(self) -> str:
        return f"multipart/form-data; boundary={self.boundary}"

    def read(self, size: int = -1) -> bytes:
        size = self.block if size is None or size < 0 else min(size, self.block)
        if self._should_stop is not None and self._should_stop():
            raise SharingCancelled("Envio interrompido")
        if self._head:
            chunk, self._head = self._head[:size], self._head[size:]
            return chunk
        if self._handle is None and self.sent < self.total:
            self._handle = self._path.open("rb")
        if self._handle is not None:
            chunk = self._handle.read(size)
            if chunk:
                self.sent += len(chunk)
                if self._on_progress is not None:
                    self._on_progress(self.sent, self.total)
                return chunk
            self._handle.close()
            self._handle = None
        if self._tail:
            chunk, self._tail = self._tail[:size], self._tail[size:]
            return chunk
        return b""

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None


def upload_file(path: Path, filename: str, host: Host, expires: str = DEFAULT_EXPIRES,
                on_progress=None, should_stop=None, timeout: float = 120.0) -> str:
    """Publica o arquivo e devolve a URL. **Só o job de upload chama isto.**

    Nenhuma outra parte do Lume manda arquivo para fora, e é de propósito: o
    envio precisa de um "sim" explícito por vez, não de um efeito colateral.
    """
    size = path.stat().st_size
    if size <= 0:
        raise SharingError("O arquivo está vazio.")
    if size > host.max_bytes:
        # Antes de abrir socket: subir 900 MB para ouvir "não" no fim seria
        # gastar a banda da pessoa por nada.
        raise SharingError(
            f"O {host.label} aceita até {host.max_bytes / 1024 / 1024:.0f} MB, "
            f"e este arquivo tem {size / 1024 / 1024:.1f} MB."
        )
    body = MultipartBody(host.fields(expires), host.field, path, filename,
                         on_progress=on_progress, should_stop=should_stop)
    request = urllib.request.Request(host.url, data=body, method="POST", headers={
        "Content-Type": body.content_type,
        "Content-Length": str(body.length),
        "User-Agent": UPLOAD_USER_AGENT,
    })
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            answer = response.read(4096).decode("utf-8", errors="replace")
    except SharingCancelled:
        raise
    except urllib.error.HTTPError as exc:
        raise SharingError(f"O {host.label} respondeu {exc.code}.") from exc
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        raise SharingError(f"Não deu para falar com o {host.label}: {exc}") from exc
    finally:
        body.close()
    return host.parse(answer)


def remember_link(source_key: str, host: Host, url: str, size: int,
                  light: bool, limit_mb: int, expires: str) -> dict:
    with connect() as db:
        cursor = db.execute(
            """INSERT INTO shared_links(source_path,host,url,bytes,light,limit_mb,expires_at)
               VALUES(?,?,?,?,?,?,?)""",
            (source_key, host.name, url, int(size), 1 if light else 0,
             int(limit_mb or 0), host.expires_at(expires)),
        )
        row = db.execute("SELECT * FROM shared_links WHERE id=?", (cursor.lastrowid,)).fetchone()
    return _link_dict(row)


def _link_dict(row) -> dict:
    expires_at = row["expires_at"]
    expired = False
    if expires_at:
        try:
            expired = datetime.fromisoformat(expires_at) <= datetime.now(timezone.utc)
        except ValueError:
            expired = False
    return {
        "id": row["id"], "url": row["url"], "host": row["host"], "bytes": row["bytes"],
        "light": bool(row["light"]), "limit_mb": row["limit_mb"],
        "expires_at": expires_at, "expired": expired, "created_at": row["created_at"],
    }


def links_for(raw_path: str | Path) -> list[dict]:
    with connect() as db:
        rows = db.execute(
            "SELECT * FROM shared_links WHERE source_path=? ORDER BY created_at DESC,id DESC",
            (media_source_key(raw_path),),
        ).fetchall()
    return [_link_dict(row) for row in rows]


def forget_link(link_id: int) -> bool:
    """Esquece o link. Não o despublica — e a interface diz isso em voz alta."""
    with connect() as db:
        return db.execute("DELETE FROM shared_links WHERE id=?", (int(link_id),)).rowcount > 0


#: Um envio por vez: são dezenas de MB de subida, e duas em paralelo só fariam
#: as duas se arrastarem — com o jogo usando a mesma conexão.
_UPLOAD_LOCK = threading.Lock()
_UPLOAD_JOBS: dict[str, "_UploadJob"] = {}
_UPLOAD_JOBS_LOCK = threading.Lock()


class _UploadJob:
    """Sobe o arquivo fora da requisição HTTP, com progresso e cancelamento."""

    def __init__(self, source_key: str, path: Path, filename: str, host: Host,
                 expires: str, light: bool, limit_mb: int) -> None:
        self.id = secrets.token_urlsafe(12)
        self.source_key = source_key
        self.path = path
        self.filename = filename
        self.host = host
        self.expires = expires
        self.light = light
        self.limit_mb = int(limit_mb or 0)
        self.status = "sending"
        self.error = ""
        self.percent = 0
        self.sent_bytes = 0
        self.total_bytes = path.stat().st_size
        self.link: dict | None = None
        self.cancelled = threading.Event()
        self._thread = threading.Thread(target=self._run, name=f"share-upload-{self.id}", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def cancel(self) -> None:
        self.cancelled.set()
        if threading.current_thread() is not self._thread:
            self._thread.join(timeout=10)

    def _progress(self, sent: int, total: int) -> None:
        self.sent_bytes = sent
        self.total_bytes = total or self.total_bytes
        if self.total_bytes > 0:
            self.percent = max(0, min(99, int(sent / self.total_bytes * 100)))

    def _run(self) -> None:
        acquired = False
        try:
            while not self.cancelled.is_set():
                acquired = _UPLOAD_LOCK.acquire(timeout=0.2)
                if acquired:
                    break
            if not acquired or self.cancelled.is_set():
                self.status = "cancelled"
                return
            url = upload_file(self.path, self.filename, self.host, self.expires,
                              on_progress=self._progress,
                              should_stop=self.cancelled.is_set)
            self.link = remember_link(self.source_key, self.host, url, self.total_bytes,
                                      self.light, self.limit_mb, self.expires)
            self.percent = 100
            self.status = "done"
        except SharingCancelled:
            self.status = "cancelled"
        except SharingError as exc:
            self.error = str(exc)
            self.status = "error"
        except OSError as exc:
            self.error = f"Falha ao ler o arquivo: {exc}"
            self.status = "error"
        finally:
            if acquired:
                _UPLOAD_LOCK.release()


def cancel_uploads(raw_path: str | Path | None = None) -> int:
    key = media_source_key(raw_path) if raw_path is not None else None
    with _UPLOAD_JOBS_LOCK:
        keys = [item for item in _UPLOAD_JOBS if key is None or item == key]
        jobs = [_UPLOAD_JOBS.pop(item) for item in keys]
    for job in jobs:
        job.cancel()
    return len(jobs)


def upload_state(raw_path: str | Path) -> dict:
    """Andamento do envio deste clipe, mais os links que ele já ganhou."""
    key = media_source_key(raw_path)
    with _UPLOAD_JOBS_LOCK:
        job = _UPLOAD_JOBS.get(key)
    state = {
        "status": "absent", "percent": 0, "sent_bytes": 0, "total_bytes": 0,
        "error": "", "url": "", "host": "", "expires": "", "job_id": "",
        "hosts": host_catalog(), "default_host": DEFAULT_HOST,
        "default_expires": DEFAULT_EXPIRES, "links": links_for(key),
    }
    if job is None:
        return state
    state.update({
        "status": job.status, "percent": job.percent, "sent_bytes": job.sent_bytes,
        "total_bytes": job.total_bytes, "error": job.error, "job_id": job.id,
        "host": job.host.name, "expires": job.expires,
        "url": (job.link or {}).get("url", ""),
    })
    return state


def start_upload(raw_path: str | Path, source: Path, use_light: bool = True,
                 limit_mb: int | None = None, host_name: str | None = None,
                 expires: str = DEFAULT_EXPIRES, confirmed: bool = False) -> dict:
    """Publica o clipe num host grátis, **só com confirmação explícita**.

    A trava mora aqui, e não no modal: publicar por acidente é o tipo de erro
    que não dá para desfazer, e uma chamada direta à API não deveria conseguir
    fazer o que a interface pede confirmação para fazer.
    """
    if confirmed is not True:
        raise SharingError("Confirme que o link é público antes de enviar.")
    key = media_source_key(raw_path)
    host = resolve_host(host_name)
    limit = normalized_limit(limit_mb) if use_light else 0
    if use_light:
        ready = share_cached(source, limit)
        if ready is None:
            raise SharingError("Gere a versão leve antes de criar o link.")
        path, filename = ready, light_filename(raw_path, source, limit)
    else:
        path, filename = source, download_filename(raw_path, source)
    with _UPLOAD_JOBS_LOCK:
        current = _UPLOAD_JOBS.get(key)
        if current is not None and current.status == "sending":
            raise SharingError("Este clipe já está sendo enviado.")
        job = _UploadJob(key, path, filename, host, expires, use_light, limit)
        _UPLOAD_JOBS[key] = job
    job.start()
    return upload_state(key)
