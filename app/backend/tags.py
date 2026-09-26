"""Vocabulário de tags: fechado para consultar, aberto para crescer.

O Qwen já devolve tags livres em toda análise. Sem conciliação elas viram
centenas de strings quase iguais — "sea of thieves", "Sea Of Thieves" e "sot"
são três assuntos diferentes para quem filtra. Aqui cada string bruta passa por
quatro filtros, do mais barato ao mais caro:

1. **slug** — minúsculo, sem acento, hifenizado. Resolve a maioria de graça.
2. **alias** — apelidos já decididos ("sot" -> "sea-of-thieves").
3. **Laya** — pergunta ao daemon se a proposta significa o mesmo que alguma tag
   ativa. É o mesmo modelo que aplica o vocabulário e que guarda o crescimento
   dele.
4. **recorrência** — uma tag proposta uma única vez é ruído do modelo, não
   assunto novo. Só vira vocabulário depois de reaparecer em dias distintos.

O que não casa com nada fica em quarentena como ``candidate`` e continua sendo
gravado na captura: o vocabulário governa o índice, não a memória. Nenhuma
observação é perdida por ainda não ter nome canônico.
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass, field

from . import laya
from .database import connect

MIN_CONFIDENCE = float(os.environ.get("LUME_TAG_CONFIDENCE", "0.6"))
MIN_PROPOSALS = int(os.environ.get("LUME_TAG_MIN_PROPOSALS", "3"))
MIN_PROPOSAL_DAYS = int(os.environ.get("LUME_TAG_MIN_DAYS", "2"))
MAX_ACTIVE = int(os.environ.get("LUME_TAG_MAX_ACTIVE", "72"))
DORMANT_DAYS = int(os.environ.get("LUME_TAG_DORMANT_DAYS", "45"))

MAX_LABEL = 60
MAX_SAMPLES = 5
MAX_SAMPLE_LENGTH = 240
MAX_PROPOSAL_DAYS = 30
APPLIED = ("known", "alias", "merged", "reactivated", "proposed")

# O Laya monta a pergunta como [CLS] instruções [SEP] opção0 opção1 ... [SEP] estado,
# e as opções inteiras dividem um orçamento de 192 tokens (``head_max_len``) — o que
# elas não gastam é o que sobra para as instruções, com piso de 8 tokens. Critério
# comprido, portanto, não enriquece a pergunta: ele engole o enunciado dela. Medido
# neste vocabulário: critério de uma frase curta acerta onde o rótulo puro erra, e a
# confiança se sustenta até ~33 opções, caindo perto de 65. Daí o teto e o recorte.
MAX_CRITERION = 120
LAYA_CRITERION_CHARS = 90
LAYA_MAX_OPTIONS = 24

DEDUP_INSTRUCTIONS = "Qual destas tags significa o mesmo que a tag proposta?"
NO_MATCH = "assunto distinto de todos acima"


# ---------------------------------------------------------------- normalização

def slugify(value: str) -> str:
    """Forma canônica: sem acento, minúscula, hifenizada.

    Mesma normalização do FTS das capturas (``remove_diacritics``), para que
    buscar e etiquetar concordem sobre o que é a mesma palavra.
    """
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(character for character in text if unicodedata.category(character) != "Mn")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:MAX_LABEL]


def clean_label(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()[:MAX_LABEL]


@dataclass(frozen=True)
class Decision:
    """O caminho que uma string bruta percorreu até virar (ou não) uma tag."""

    raw: str
    slug: str
    label: str
    outcome: str
    confidence: float = 0.0
    detail: str = ""

    @property
    def applied(self) -> bool:
        return self.outcome in APPLIED


@dataclass
class Resolution:
    tags: list[str] = field(default_factory=list)
    decisions: list[Decision] = field(default_factory=list)
    laya_error: str = ""

    def as_dict(self) -> dict:
        return {
            "tags": self.tags,
            "laya_error": self.laya_error,
            "decisions": [
                {"raw": item.raw, "slug": item.slug, "label": item.label, "outcome": item.outcome,
                 "confidence": round(item.confidence, 3), "detail": item.detail, "applied": item.applied}
                for item in self.decisions
            ],
        }


@contextmanager
def _session(db):
    """Reaproveita a conexão de quem chama, ou abre uma própria."""
    if db is not None:
        yield db
    else:
        with connect() as owned:
            yield owned


# ---------------------------------------------------------------- leitura

def active_vocabulary(db) -> list[dict]:
    return [dict(row) for row in db.execute(
        "SELECT slug,label,criterion FROM tags WHERE status='active' ORDER BY slug"
    )]


def _lookup(db, slug: str) -> dict | None:
    row = db.execute("SELECT slug,label,status FROM tags WHERE slug=?", (slug,)).fetchone()
    if row:
        return dict(row)
    alias = db.execute(
        """SELECT tags.slug slug,tags.label label,tags.status status FROM tag_aliases
           JOIN tags ON tags.slug=tag_aliases.slug WHERE tag_aliases.alias=?""", (slug,)
    ).fetchone()
    return dict(alias) | {"via_alias": True} if alias else None


# ---------------------------------------------------------------- escrita

def _note_use(db, slugs: list[str]) -> None:
    if slugs:
        db.executemany(
            "UPDATE tags SET uses=uses+1,last_used=CURRENT_TIMESTAMP WHERE slug=?",
            [(slug,) for slug in slugs],
        )


def _record_proposal(db, slug: str, label: str, day: str, context: str) -> None:
    """Acumula a evidência da candidata: quantas vezes, em que dias, com que texto."""
    row = db.execute("SELECT proposal_days_json,samples_json FROM tags WHERE slug=?", (slug,)).fetchone()
    if row is None:
        db.execute(
            """INSERT INTO tags(slug,label,status,origin,proposals,proposal_days_json,samples_json)
               VALUES(?,?,'candidate','model',1,?,?)""",
            (slug, label, json.dumps([day] if day else []),
             json.dumps([context[:MAX_SAMPLE_LENGTH]] if context else [], ensure_ascii=False)),
        )
        return
    days = json.loads(row["proposal_days_json"] or "[]")
    if day and day not in days:
        days = (days + [day])[-MAX_PROPOSAL_DAYS:]
    samples = json.loads(row["samples_json"] or "[]")
    if context and len(samples) < MAX_SAMPLES:
        samples.append(context[:MAX_SAMPLE_LENGTH])
    db.execute(
        """UPDATE tags SET proposals=proposals+1,proposal_days_json=?,samples_json=?,
           last_used=CURRENT_TIMESTAMP WHERE slug=?""",
        (json.dumps(days), json.dumps(samples, ensure_ascii=False), slug),
    )


def _record_alias(db, alias: str, slug: str, confidence: float, decided_by: str) -> None:
    db.execute(
        """INSERT INTO tag_aliases(alias,slug,confidence,decided_by) VALUES(?,?,?,?)
           ON CONFLICT(alias) DO UPDATE SET slug=excluded.slug,confidence=excluded.confidence,
           decided_by=excluded.decided_by""",
        (alias, slug, float(confidence), decided_by),
    )


# ---------------------------------------------------------------- canonicalização

def canonicalize(raw_tags: list[str], *, day: str = "", context: str = "",
                 db=None, use_laya: bool = True, commit: bool = True) -> Resolution:
    """Resolve as tags brutas de uma análise contra o vocabulário.

    ``commit=False`` responde o que aconteceria sem gravar nada — é o que a tela
    de testes usa para experimentar um limiar antes de deixá-lo valer.
    """
    resolution = Resolution()
    seen: set[str] = set()
    pending: list[Decision] = []

    with _session(db) as connection:
        for raw in raw_tags:
            label = clean_label(raw)
            slug = slugify(label)
            if not slug or len(slug) < 2 or slug in seen:
                if slug and slug in seen:
                    continue
                resolution.decisions.append(Decision(str(raw), slug, label, "discarded",
                                                     detail="vazia ou curta demais"))
                continue
            seen.add(slug)
            known = _lookup(connection, slug)
            if known is None:
                # Só o que é inteiramente novo custa uma pergunta ao Laya; uma
                # candidata já conhecida apenas reaparece, e a fusão semântica
                # dela é reavaliada uma vez só, na promoção.
                pending.append(Decision(str(raw), slug, label, "proposed"))
            elif known["status"] == "rejected":
                resolution.decisions.append(Decision(str(raw), slug, known["label"], "discarded",
                                                     detail="tag rejeitada anteriormente"))
            elif known.get("via_alias"):
                resolution.decisions.append(Decision(str(raw), known["slug"], known["label"], "alias",
                                                     detail=f"apelido de {known['slug']}"))
            elif known["status"] == "candidate":
                resolution.decisions.append(Decision(str(raw), slug, known["label"], "proposed",
                                                     detail="candidata em quarentena, aguardando recorrência"))
            elif known["status"] == "dormant":
                resolution.decisions.append(Decision(str(raw), slug, known["label"], "reactivated",
                                                     detail="tag dormente voltou a ser usada"))
            else:
                resolution.decisions.append(Decision(str(raw), slug, known["label"], "known"))

        if pending and use_laya:
            vocabulary = active_vocabulary(connection)
            if vocabulary:
                pending = _resolve_with_laya(pending, vocabulary, resolution, context)

        resolution.decisions.extend(pending)
        order = {str(raw): index for index, raw in enumerate(raw_tags)}
        resolution.decisions.sort(key=lambda item: order.get(item.raw, len(order)))
        resolution.tags = [item.label for item in resolution.decisions if item.applied]

        if commit:
            _persist(connection, resolution, day, context)
    return resolution


def _words(value: str) -> set[str]:
    return {part for part in slugify(value).split("-") if len(part) > 2}


def _shortlist(vocabulary: list[dict], proposal: str, context: str) -> list[dict]:
    """As tags com alguma chance de serem a mesma coisa, e só elas.

    Mandar o vocabulário inteiro não é só caro: passando de algumas dezenas de
    opções a confiança do Laya despenca. Quem não compartilha nenhuma palavra
    com a proposta nem com o contexto raramente é o sinônimo procurado, então o
    recorte lexical vem primeiro e o modelo decide entre os finalistas.
    """
    if len(vocabulary) <= LAYA_MAX_OPTIONS:
        return vocabulary
    terms = _words(proposal) | _words(context)
    ranked = sorted(
        vocabulary,
        key=lambda item: (-len(terms & (_words(item["label"]) | _words(item["criterion"]))), item["slug"]),
    )
    return ranked[:LAYA_MAX_OPTIONS]


def _resolve_with_laya(pending: list[Decision], vocabulary: list[dict],
                       resolution: Resolution, context: str) -> list[Decision]:
    """Pergunta ao Laya quais propostas são sinônimo de alguma tag ativa."""
    options = _shortlist(vocabulary, " ".join(item.label for item in pending), context)
    criteria = {item["slug"]: (item["criterion"] or item["label"])[:LAYA_CRITERION_CHARS] for item in options}
    criteria[laya.NENHUMA] = NO_MATCH
    labels = {item["slug"]: item["label"] for item in options}
    states = [f"Tag proposta: {item.label}. Contexto: {context[:400] or 'nenhum'}" for item in pending]
    try:
        answers = laya.choose(states, DEDUP_INSTRUCTIONS, criteria)
    except laya.LayaUnavailable as exc:
        # Sem o Laya a proposta segue para a quarentena: a recorrência ainda a
        # segura, e nenhuma tag é perdida. Só a fusão semântica fica para depois.
        resolution.laya_error = str(exc)
        return pending

    remaining = []
    for item, answer in zip(pending, answers):
        if answer.is_none or answer.choice not in labels or answer.confidence < MIN_CONFIDENCE:
            detail = "" if answer.is_none else (
                f"o Laya viu '{answer.choice}' com confiança {answer.confidence:.2f}, "
                f"abaixo de {MIN_CONFIDENCE:.2f}"
            )
            remaining.append(Decision(item.raw, item.slug, item.label, "proposed", answer.confidence, detail))
            continue
        resolution.decisions.append(Decision(
            item.raw, answer.choice, labels[answer.choice], "merged", answer.confidence,
            detail=f"o Laya reconheceu '{item.label}' como a mesma coisa que '{labels[answer.choice]}'",
        ))
    return remaining


def _persist(db, resolution: Resolution, day: str, context: str) -> None:
    used = [item.slug for item in resolution.decisions if item.outcome in ("known", "alias", "merged", "reactivated")]
    _note_use(db, used)
    for item in resolution.decisions:
        if item.outcome == "reactivated":
            db.execute("UPDATE tags SET status='active' WHERE slug=? AND status='dormant'", (item.slug,))
        elif item.outcome == "merged":
            _record_alias(db, slugify(item.raw), item.slug, item.confidence, "laya")
        elif item.outcome == "proposed":
            _record_proposal(db, item.slug, item.label, day, context)


def apply_tags(raw_tags: list[str], *, day: str = "", context: str = "") -> list[str]:
    """Atalho para o pipeline: devolve só as tags já conciliadas."""
    try:
        return canonicalize(list(raw_tags or []), day=day, context=context).tags
    except Exception as exc:  # o vocabulário nunca pode derrubar uma análise
        print(f"[tags] conciliação indisponível: {exc}")
        return [clean_label(tag) for tag in (raw_tags or []) if clean_label(tag)]


# ---------------------------------------------------------------- promoção

def _recurrent(row: dict) -> bool:
    days = json.loads(row["proposal_days_json"] or "[]")
    return row["proposals"] >= MIN_PROPOSALS and len(days) >= MIN_PROPOSAL_DAYS


def promote(day: str = "", *, describe=None, commit: bool = True, db=None) -> dict:
    """Decide quais candidatas viram vocabulário — o passo de fim de dia.

    ``describe`` recebe as sobreviventes e devolve ``{slug: {label, criterion}}``;
    é o Qwen escrevendo o texto que o Laya vai ler daí em diante. Sem ele a tag
    é ativada com um critério derivado do que já se observou, que funciona mas é
    mais pobre.
    """
    report = {"day": day, "promoted": [], "merged": [], "waiting": [], "dormant": [],
              "retired": [], "laya_error": "", "committed": commit}
    with _session(db) as connection:
        if commit:
            _sweep_dormant(connection, report)
        candidates = [dict(row) for row in connection.execute(
            "SELECT * FROM tags WHERE status='candidate' ORDER BY proposals DESC,slug"
        )]
        ready, waiting = [], []
        for row in candidates:
            (ready if _recurrent(row) else waiting).append(row)
        report["waiting"] = [
            {"slug": row["slug"], "label": row["label"], "proposals": row["proposals"],
             "days": len(json.loads(row["proposal_days_json"] or "[]"))}
            for row in waiting
        ]
        if not ready:
            return report

        vocabulary = active_vocabulary(connection)
        if vocabulary:
            ready = _merge_ready(connection, ready, vocabulary, report, commit)
        if not ready:
            return report

        described = _describe(ready, describe)
        for row in ready:
            detail = described.get(row["slug"], {})
            label = clean_label(detail.get("label") or row["label"])
            criterion = re.sub(r"\s+", " ", str(detail.get("criterion") or "")).strip()[:MAX_CRITERION]
            if not criterion:
                criterion = f"conteúdo que as análises descreveram como '{label}'"
            report["promoted"].append({"slug": row["slug"], "label": label, "criterion": criterion,
                                       "proposals": row["proposals"]})
            if commit:
                connection.execute(
                    """UPDATE tags SET label=?,criterion=?,status='active',
                       decided_by='recurrence',decided_at=CURRENT_TIMESTAMP WHERE slug=?""",
                    (label, criterion, row["slug"]),
                )
        if commit:
            _enforce_cap(connection, report)
    return report


def _merge_ready(db, ready: list[dict], vocabulary: list[dict], report: dict, commit: bool) -> list[dict]:
    """Última checagem semântica antes de ativar: o vocabulário pode ter crescido."""
    resolution = Resolution()
    pending = [Decision(row["slug"], row["slug"], row["label"], "proposed") for row in ready]
    by_slug = {row["slug"]: row for row in ready}
    context = "; ".join(
        sample for row in ready for sample in json.loads(row["samples_json"] or "[]")[:1]
    )
    remaining = _resolve_with_laya(pending, vocabulary, resolution, context)
    report["laya_error"] = resolution.laya_error
    for merged in resolution.decisions:
        candidate = by_slug[merged.raw]
        report["merged"].append({"slug": candidate["slug"], "label": candidate["label"],
                                 "into": merged.slug, "into_label": merged.label,
                                 "confidence": round(merged.confidence, 3)})
        if commit:
            # A candidata deixa de existir como tag e passa a apelido da canônica:
            # o alias referencia tags(slug), então os dois não podem coexistir.
            db.execute("DELETE FROM tags WHERE slug=?", (candidate["slug"],))
            _record_alias(db, candidate["slug"], merged.slug, merged.confidence, "laya")
    return [by_slug[item.slug] for item in remaining]


def _describe(ready: list[dict], describe) -> dict[str, dict]:
    if not describe:
        return {}
    payload = [
        {"slug": row["slug"], "label": row["label"],
         "samples": json.loads(row["samples_json"] or "[]"), "proposals": row["proposals"]}
        for row in ready
    ]
    try:
        described = describe(payload)
    except Exception as exc:  # um texto melhor não vale travar a promoção
        print(f"[tags] descrição das candidatas indisponível: {exc}")
        return {}
    return described if isinstance(described, dict) else {}


def _sweep_dormant(db, report: dict) -> None:
    stale = db.execute(
        """SELECT slug,label FROM tags WHERE status='active'
           AND date(coalesce(last_used,first_seen)) < date('now',?)""",
        (f"-{DORMANT_DAYS} days",),
    ).fetchall()
    for row in stale:
        report["dormant"].append({"slug": row["slug"], "label": row["label"]})
        db.execute("UPDATE tags SET status='dormant' WHERE slug=?", (row["slug"],))


def _enforce_cap(db, report: dict) -> None:
    """Um vocabulário sem teto deixa de ser vocabulário — e encarece cada lote."""
    total = db.execute("SELECT count(*) total FROM tags WHERE status='active'").fetchone()["total"]
    excess = int(total) - MAX_ACTIVE
    if excess <= 0:
        return
    victims = db.execute(
        """SELECT slug,label FROM tags WHERE status='active' AND origin='model'
           ORDER BY uses,coalesce(last_used,first_seen) LIMIT ?""", (excess,),
    ).fetchall()
    for row in victims:
        report["retired"].append({"slug": row["slug"], "label": row["label"]})
        db.execute("UPDATE tags SET status='dormant' WHERE slug=?", (row["slug"],))


# ---------------------------------------------------------------- operações manuais

def listing() -> dict:
    with connect() as db:
        rows = [dict(row) for row in db.execute(
            "SELECT * FROM tags ORDER BY status,coalesce(last_used,first_seen) DESC,slug"
        )]
        aliases: dict[str, list[str]] = {}
        for row in db.execute("SELECT alias,slug,confidence,decided_by FROM tag_aliases ORDER BY alias"):
            aliases.setdefault(row["slug"], []).append(row["alias"])
        active_total = sum(1 for row in rows if row["status"] == "active")
    items = []
    for row in rows:
        days = json.loads(row["proposal_days_json"] or "[]")
        items.append({
            "slug": row["slug"], "label": row["label"], "criterion": row["criterion"],
            "status": row["status"], "origin": row["origin"], "proposals": row["proposals"],
            "proposal_days": len(days), "samples": json.loads(row["samples_json"] or "[]"),
            "uses": row["uses"], "decided_by": row["decided_by"], "last_used": row["last_used"],
            "first_seen": row["first_seen"], "aliases": aliases.get(row["slug"], []),
            "ready": row["status"] == "candidate" and _recurrent(row),
        })
    return {
        "items": items,
        "laya": laya.status(),
        "settings": {
            "min_confidence": MIN_CONFIDENCE, "min_proposals": MIN_PROPOSALS,
            "min_proposal_days": MIN_PROPOSAL_DAYS, "max_active": MAX_ACTIVE,
            "dormant_days": DORMANT_DAYS,
        },
        "counts": {
            "active": active_total,
            "candidate": sum(1 for row in rows if row["status"] == "candidate"),
            "dormant": sum(1 for row in rows if row["status"] == "dormant"),
            "rejected": sum(1 for row in rows if row["status"] == "rejected"),
        },
    }


def set_status(slug: str, status: str) -> dict:
    if status not in ("candidate", "active", "dormant", "rejected"):
        raise ValueError(f"situação desconhecida: {status}")
    with connect() as db:
        row = db.execute("SELECT label,criterion FROM tags WHERE slug=?", (slug,)).fetchone()
        if not row:
            raise LookupError(f"tag não encontrada: {slug}")
        criterion = row["criterion"] or f"conteúdo que as análises descreveram como '{row['label']}'"
        db.execute(
            """UPDATE tags SET status=?,criterion=?,decided_by='user',decided_at=CURRENT_TIMESTAMP
               WHERE slug=?""", (status, criterion, slug),
        )
    return {"slug": slug, "status": status}


def merge(slug: str, into: str) -> dict:
    if slug == into:
        raise ValueError("uma tag não pode ser apelido de si mesma")
    with connect() as db:
        target = db.execute("SELECT label FROM tags WHERE slug=?", (into,)).fetchone()
        if not target:
            raise LookupError(f"tag de destino não encontrada: {into}")
        if not db.execute("SELECT 1 FROM tags WHERE slug=?", (slug,)).fetchone():
            raise LookupError(f"tag não encontrada: {slug}")
        # Os apelidos da absorvida passam a apontar para o destino antes de
        # apagá-la, senão o ON DELETE CASCADE os levaria junto.
        db.execute("UPDATE tag_aliases SET slug=? WHERE slug=?", (into, slug))
        db.execute("DELETE FROM tags WHERE slug=?", (slug,))
        _record_alias(db, slug, into, 1.0, "user")
    return {"slug": slug, "into": into, "label": target["label"]}


def create(label: str, criterion: str = "") -> dict:
    clean = clean_label(label)
    slug = slugify(clean)
    if not slug or len(slug) < 2:
        raise ValueError("a tag precisa de pelo menos dois caracteres utilizáveis")
    text = re.sub(r"\s+", " ", criterion or "").strip()[:MAX_CRITERION] or \
        f"conteúdo que as análises descreveram como '{clean}'"
    with connect() as db:
        if db.execute("SELECT 1 FROM tag_aliases WHERE alias=?", (slug,)).fetchone():
            raise ValueError(f"'{slug}' já é apelido de outra tag")
        db.execute(
            """INSERT INTO tags(slug,label,criterion,status,origin,decided_by,decided_at)
               VALUES(?,?,?,'active','user','user',CURRENT_TIMESTAMP)
               ON CONFLICT(slug) DO UPDATE SET label=excluded.label,criterion=excluded.criterion,
               status='active',decided_by='user',decided_at=CURRENT_TIMESTAMP""",
            (slug, clean, text),
        )
    return {"slug": slug, "label": clean, "criterion": text}


def remove_alias(alias: str) -> dict:
    with connect() as db:
        removed = db.execute("DELETE FROM tag_aliases WHERE alias=?", (alias,)).rowcount
    if not removed:
        raise LookupError(f"apelido não encontrado: {alias}")
    return {"alias": alias}
