import { useState } from "react";
import type { ActivitySession } from "./api";
import "./activity-sessions.css";

type Frame = ActivitySession["key_frames"][number];
const time = (value: string) => new Date(value).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
const searchable = (value: string) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("pt-BR");

function ActivityCard({ item, onOpen }: { item: ActivitySession; onOpen: (frame: Frame) => void }) {
  const [expanded, setExpanded] = useState(false);
  const [allFrames, setAllFrames] = useState(false);
  const paragraphs = item.narrative.split(/\n+/).filter(Boolean);
  const first = paragraphs[0] || "Sem descrição disponível para esta sessão.";
  const preview = first.length > 320 ? `${first.slice(0, 320).trimEnd()}…` : first;
  const hasMore = paragraphs.length > 1 || first.length > 320;
  const frames = allFrames ? item.key_frames : item.key_frames.slice(0, 4);
  return <article className="visual-activity">
    <header><div className="activity-app-icon" aria-hidden="true">{item.app.slice(0, 1).toUpperCase()}</div><div className="activity-card-heading"><span>{item.app}</span><h2>{item.title}</h2><small><time>{time(item.started_at)}</time>{item.ended_at !== item.started_at && <>–<time>{time(item.ended_at)}</time></>} · {item.source_count} capturas <span title="O intervalo entre capturas não mede o tempo contínuo de uso.">· intervalo observado</span></small></div></header>
    <div className="activity-story">{(expanded ? paragraphs : [preview]).map((paragraph, index) => <p key={index}>{paragraph}</p>)}{hasMore && <button className="activity-read-more" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>{expanded ? "Recolher descrição" : "Ler descrição completa"}</button>}</div>
    {!!frames.length && <><div className="activity-filmstrip" aria-label={`Capturas de ${item.title}`}>{frames.map(frame => <button key={frame.id} onClick={() => onOpen(frame)} aria-label={`Abrir captura das ${time(frame.captured_at)}: ${frame.title || item.title}`}>{frame.url ? <img src={frame.url} alt={frame.title || "Captura da atividade"} loading="lazy"/> : <span>Imagem removida<br/>Análise disponível</span>}<time>{time(frame.captured_at)}</time>{frame.preserved && <b title="Captura preservada" aria-label="Captura preservada">◆</b>}</button>)}</div>{item.key_frames.length > 4 && <button className="activity-more-frames" aria-expanded={allFrames} onClick={() => setAllFrames(!allFrames)}>{allFrames ? "Mostrar menos capturas" : `Ver todas as ${item.key_frames.length} capturas selecionadas`}</button>}</>}
    {!!item.events.length && <details><summary>Acontecimentos · {item.events.length}</summary><ol>{item.events.map((event, index) => <li key={index}>{event}</li>)}</ol></details>}
    <div className="tags">{item.tags.map(tag => <span key={tag}>{tag}</span>)}</div>
  </article>;
}

export function ActivitiesView({ items, running, onGenerate, onOpen, onShowQueue }: { items: ActivitySession[]; running: boolean; onGenerate: () => void; onOpen: (frame: Frame) => void; onShowQueue: () => void }) {
  const [query, setQuery] = useState("");
  const [app, setApp] = useState("");
  const [order, setOrder] = useState("chronological");
  const apps = [...new Set(items.map(item => item.app))].sort((a, b) => a.localeCompare(b, "pt-BR"));
  const visible = items.filter(item => (!app || item.app === app) && searchable([item.title, item.app, item.narrative, ...item.tags, ...item.events].join(" ")).includes(searchable(query.trim())))
    .sort((a, b) => (Date.parse(a.started_at) - Date.parse(b.started_at)) * (order === "chronological" ? 1 : -1));
  return <div className="visual-activities">
    <div className="activity-overview"><div><strong>{items.length} sessões do dia</strong><span>{items.reduce((total, item) => total + item.source_count, 0)} capturas analisadas · agrupadas por aplicativo</span></div><button className="primary" disabled={running} onClick={onGenerate}>{running ? "Analisando atividades…" : items.length ? "Reanalisar atividades" : "Analisar atividades"}</button></div>
    {running && <p className="activity-progress" role="status">A análise está em andamento. As sessões aparecerão aqui quando estiverem prontas. <button className="activity-read-more" onClick={onShowQueue}>Ver processamento</button></p>}
    {!!items.length && <><div className="activity-filters"><label><span>Encontrar atividade</span><input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Série, assunto ou aplicativo…"/></label><label><span>Aplicativo</span><select value={app} onChange={event => setApp(event.target.value)}><option value="">Todos os aplicativos</option>{apps.map(name => <option key={name}>{name}</option>)}</select></label><label><span>Ordem</span><select value={order} onChange={event => setOrder(event.target.value)}><option value="chronological">Início do dia primeiro</option><option value="recent">Mais recentes primeiro</option></select></label></div><p className="activity-result-count" role="status">{visible.length} de {items.length} sessões{(query || app) && <button className="activity-read-more" onClick={() => { setQuery(""); setApp(""); }}>Limpar filtros</button>}</p></>}
    {visible.map(item => <ActivityCard key={item.id} item={item} onOpen={onOpen}/>)}
    {!!items.length && !visible.length && <div className="result">Nenhuma atividade corresponde aos filtros. Tente outro assunto ou aplicativo.</div>}
    {!items.length && !running && <div className="activity-empty"><strong>Veja o que aconteceu ao longo do dia</strong><p>Analise as capturas para reunir assuntos, acontecimentos e imagens importantes em sessões.</p><button className="secondary" onClick={onGenerate}>Analisar atividades</button></div>}
  </div>;
}
