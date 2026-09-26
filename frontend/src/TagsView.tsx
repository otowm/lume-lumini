import { useEffect, useState } from "react";
import { api, type TagDecision, type TagEntry, type TagPromotion, type TagStatus, type TagTestResult, type TagVocabulary } from "./api";
import "./tags.css";

const OUTCOME: Record<TagDecision["outcome"], { label: string; hint: string }> = {
  known: { label: "já existia", hint: "casou pelo slug com uma tag ativa, sem custo de modelo" },
  alias: { label: "apelido", hint: "casou com um apelido já decidido" },
  merged: { label: "fundida", hint: "o Laya reconheceu como sinônimo de uma tag ativa" },
  reactivated: { label: "reativada", hint: "tag dormente voltou a ser usada" },
  proposed: { label: "proposta", hint: "foi para a quarentena; é aplicada na captura, mas ainda não é vocabulário" },
  discarded: { label: "descartada", hint: "curta demais ou rejeitada anteriormente" },
};

const STATUS: Record<TagStatus, string> = {
  active: "ativa", candidate: "candidata", dormant: "dormente", rejected: "rejeitada",
};

const today = () => new Date().toISOString().slice(0, 10);

function DecisionRow({ decision }: { decision: TagDecision }) {
  const outcome = OUTCOME[decision.outcome];
  return <tr className={decision.applied ? "" : "muted-row"}>
    <td><code>{decision.raw}</code></td>
    <td><span className={`outcome ${decision.outcome}`} title={outcome.hint}>{outcome.label}</span></td>
    <td>{decision.outcome === "discarded" ? "—" : decision.label}</td>
    <td className="numeric">{decision.confidence ? decision.confidence.toFixed(2) : "—"}</td>
    <td className="detail">{decision.detail}</td>
  </tr>;
}

function Bench({ onBusy }: { onBusy: (busy: boolean) => void }) {
  const [raw, setRaw] = useState("");
  const [context, setContext] = useState("");
  const [useLaya, setUseLaya] = useState(true);
  const [result, setResult] = useState<TagTestResult | null>(null);
  const [error, setError] = useState("");

  const parsed = raw.split(/[,\n]/).map(value => value.trim()).filter(Boolean);
  const run = async () => {
    setError(""); onBusy(true);
    try {
      setResult(await api.testTags(parsed, context, useLaya));
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : String(exception));
    } finally {
      onBusy(false);
    }
  };

  return <section className="tag-panel">
    <header><h3>Bancada</h3><small>Passa strings pelo vocabulário sem gravar nada. É o mesmo caminho que uma análise percorre.</small></header>
    <div className="tag-bench">
      <label><span>Tags brutas (uma por linha ou separadas por vírgula)</span>
        <textarea value={raw} onChange={event => setRaw(event.target.value)} placeholder={"sot\nreceita de pão\nfinanças pessoais"} rows={3}/></label>
      <label><span>Contexto — o texto da análise em que elas apareceriam</span>
        <textarea value={context} onChange={event => setContext(event.target.value)} placeholder="Planilha de orçamento aberta no navegador, conferindo faturas do cartão" rows={3}/></label>
    </div>
    <div className="tag-actions">
      <label className="tag-toggle"><input type="checkbox" checked={useLaya} onChange={event => setUseLaya(event.target.checked)}/>Consultar o Laya</label>
      <small>Sem o Laya só valem slug e apelido — serve para ver o que a normalização resolve sozinha.</small>
      <button className="primary" disabled={!parsed.length} onClick={run}>Testar {parsed.length || ""}</button>
    </div>
    {error && <p className="tag-error">{error}</p>}
    {result && <>
      {result.laya_error && <p className="tag-error">Laya indisponível: {result.laya_error}. As propostas ficaram na quarentena.</p>}
      <table className="tag-table">
        <thead><tr><th>bruta</th><th>caminho</th><th>vira</th><th>confiança</th><th>por quê</th></tr></thead>
        <tbody>{result.decisions.map(decision => <DecisionRow key={decision.raw} decision={decision}/>)}</tbody>
      </table>
      <p className="tag-outcome">Gravaria na captura: {result.tags.length ? result.tags.map(tag => <span key={tag} className="tag-chip">{tag}</span>) : "nenhuma tag"}</p>
    </>}
  </section>;
}

function Promotion({ onBusy, onChanged }: { onBusy: (busy: boolean) => void; onChanged: () => void }) {
  const [day, setDay] = useState(today);
  const [report, setReport] = useState<TagPromotion | null>(null);
  const [error, setError] = useState("");

  const run = async (commit: boolean) => {
    setError(""); onBusy(true);
    try {
      setReport(await api.promoteTags(day, commit));
      if (commit) onChanged();
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : String(exception));
    } finally {
      onBusy(false);
    }
  };

  return <section className="tag-panel">
    <header><h3>Promoção de um dia</h3><small>Funde sinônimos e promove o que reapareceu o bastante. Roda sozinha no fim do resumo diário; aqui você a executa à mão.</small></header>
    <div className="tag-actions">
      <label className="tag-day"><span>Dia</span><input type="date" value={day} onChange={event => setDay(event.target.value)}/></label>
      <button className="secondary" onClick={() => run(false)}>Ensaiar</button>
      <button className="primary" onClick={() => run(true)}>Aplicar</button>
      <small>O ensaio usa os mesmos modelos e mostra o relatório inteiro, mas não grava.</small>
    </div>
    {error && <p className="tag-error">{error}</p>}
    {report && <div className="tag-report">
      <p className={report.committed ? "tag-committed" : "tag-dry"}>{report.committed ? "Aplicado." : "Ensaio — nada foi gravado."}</p>
      {report.laya_error && <p className="tag-error">Laya indisponível: {report.laya_error}. Nenhuma fusão semântica foi avaliada.</p>}
      <ReportList title="Promovidas a vocabulário" empty="nenhuma candidata atingiu a recorrência mínima"
        items={report.promoted.map(item => ({ key: item.slug, head: item.label, body: `${item.criterion} · ${item.proposals} propostas` }))}/>
      <ReportList title="Fundidas com tags existentes" empty="nenhum sinônimo encontrado"
        items={report.merged.map(item => ({ key: item.slug, head: `${item.label} → ${item.into_label}`, body: `confiança ${item.confidence.toFixed(2)}` }))}/>
      <ReportList title="Ainda em quarentena" empty="nenhuma candidata esperando"
        items={report.waiting.map(item => ({ key: item.slug, head: item.label, body: `${item.proposals} propostas em ${item.days} dia(s)` }))}/>
      <ReportList title="Passaram a dormentes" empty="nenhuma tag envelheceu"
        items={[...report.dormant, ...report.retired].map(item => ({ key: item.slug, head: item.label, body: "" }))}/>
    </div>}
  </section>;
}

function ReportList({ title, items, empty }: { title: string; items: { key: string; head: string; body: string }[]; empty: string }) {
  return <div className="tag-report-group">
    <h4>{title} · {items.length}</h4>
    {items.length ? <ul>{items.map(item => <li key={item.key}><strong>{item.head}</strong>{item.body && <small>{item.body}</small>}</li>)}</ul>
      : <p className="tag-empty">{empty}</p>}
  </div>;
}

function TagRow({ tag, actives, onAct }: { tag: TagEntry; actives: TagEntry[]; onAct: (action: () => Promise<unknown>) => void }) {
  const [mergeInto, setMergeInto] = useState("");
  return <article className={`tag-entry ${tag.status}`}>
    <header>
      <div><strong>{tag.label}</strong><code>{tag.slug}</code></div>
      <span className={`tag-status ${tag.status}`}>{STATUS[tag.status]}{tag.ready && tag.status === "candidate" ? " · pronta" : ""}</span>
    </header>
    <p className="tag-criterion">{tag.criterion || <em>sem critério — o Laya não consegue aplicá-la</em>}</p>
    <small className="tag-meta">
      {tag.uses} usos · {tag.proposals} propostas em {tag.proposal_days} dia(s) · {tag.origin === "user" ? "criada por você" : "proposta pelo modelo"}
      {tag.last_used && ` · último uso ${tag.last_used.slice(0, 10)}`}
    </small>
    {!!tag.aliases.length && <div className="tag-aliases">{tag.aliases.map(alias =>
      <button key={alias} title="Remover este apelido" onClick={() => onAct(() => api.deleteTagAlias(alias))}>{alias} ✕</button>)}</div>}
    {!!tag.samples.length && <details><summary>Onde apareceu · {tag.samples.length}</summary>
      <ul>{tag.samples.map((sample, index) => <li key={index}>{sample}</li>)}</ul></details>}
    <div className="tag-entry-actions">
      {tag.status !== "active" && <button className="secondary" onClick={() => onAct(() => api.setTagStatus(tag.slug, "active"))}>Ativar</button>}
      {tag.status === "active" && <button className="ghost" onClick={() => onAct(() => api.setTagStatus(tag.slug, "dormant"))}>Adormecer</button>}
      {tag.status !== "rejected" && <button className="danger" onClick={() => onAct(() => api.setTagStatus(tag.slug, "rejected"))}>Rejeitar</button>}
      <select value={mergeInto} onChange={event => setMergeInto(event.target.value)}>
        <option value="">Fundir com…</option>
        {actives.filter(other => other.slug !== tag.slug).map(other => <option key={other.slug} value={other.slug}>{other.label}</option>)}
      </select>
      {mergeInto && <button className="secondary" onClick={() => onAct(() => api.mergeTag(tag.slug, mergeInto))}>Confirmar fusão</button>}
    </div>
  </article>;
}

export function TagsView() {
  const [data, setData] = useState<TagVocabulary | null>(null);
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState<TagStatus | "all">("candidate");
  const [label, setLabel] = useState("");
  const [criterion, setCriterion] = useState("");
  const [error, setError] = useState("");

  const load = async () => {
    try {
      setData(await api.tags());
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : String(exception));
    }
  };
  useEffect(() => { void load(); }, []);

  const act = async (action: () => Promise<unknown>) => {
    setError(""); setBusy(true);
    try {
      await action();
      await load();
    } catch (exception) {
      setError(exception instanceof Error ? exception.message : String(exception));
    } finally {
      setBusy(false);
    }
  };

  if (!data) return <div className="result">{error || "Carregando o vocabulário…"}</div>;
  const actives = data.items.filter(item => item.status === "active");
  const visible = filter === "all" ? data.items : data.items.filter(item => item.status === filter);
  const { settings, laya } = data;

  return <div className={`tags-view ${busy ? "busy" : ""}`}>
    <div className={`tag-daemon ${laya.available ? "up" : "down"}`}>
      <strong>{laya.available ? "Laya no ar" : "Laya fora do ar"}</strong>
      <small>{laya.available ? `${laya.model || "modelo carregado"} · ${laya.socket}` : laya.detail}</small>
      <span>{settings.min_proposals} propostas em {settings.min_proposal_days} dias para promover · confiança mínima {settings.min_confidence.toFixed(2)} · teto de {settings.max_active} ativas · dormência em {settings.dormant_days} dias</span>
    </div>
    {!laya.available && <p className="tag-error">Sem o daemon, só a normalização e os apelidos valem: nenhuma fusão semântica acontece e tudo que é novo espera na quarentena. Nada se perde — as tags continuam sendo gravadas nas capturas.</p>}
    {error && <p className="tag-error">{error}</p>}

    <Bench onBusy={setBusy}/>
    <Promotion onBusy={setBusy} onChanged={load}/>

    <section className="tag-panel">
      <header><h3>Vocabulário</h3><small>{data.counts.active} ativas · {data.counts.candidate} candidatas · {data.counts.dormant} dormentes · {data.counts.rejected} rejeitadas</small></header>
      <div className="tag-actions">
        <div className="segmented">
          {(["candidate", "active", "dormant", "rejected", "all"] as const).map(key =>
            <button key={key} className={filter === key ? "active" : ""} onClick={() => setFilter(key)}>
              {key === "all" ? "todas" : STATUS[key]}
            </button>)}
        </div>
      </div>
      <div className="tag-create">
        <input value={label} onChange={event => setLabel(event.target.value)} placeholder="Nome de uma tag nova"/>
        <input value={criterion} onChange={event => setCriterion(event.target.value)} placeholder="Palavras que caracterizam o assunto: receita, comida, cozinha"/>
        <button className="secondary" disabled={!label.trim()} onClick={() => act(async () => {
          await api.createTag(label.trim(), criterion.trim()); setLabel(""); setCriterion("");
        })}>Criar já ativa</button>
      </div>
      {visible.length ? visible.map(tag => <TagRow key={tag.slug} tag={tag} actives={actives} onAct={act}/>)
        : <p className="tag-empty">Nenhuma tag nesta situação.</p>}
    </section>
  </div>;
}
