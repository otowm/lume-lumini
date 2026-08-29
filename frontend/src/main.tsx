import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { api, uploadVideo, type ActivitySession, type Capture, type CleanupSettings, type DaySummary, type HourSummary, type OllamaModel, type PipelineQueue, type QueueCounts, type QueueItem, type QueueJob, type QueueSpeed, type RawFile, type ScheduleSettings, type ScreenSequenceResult, type ScreenSettings, type Status, type StorageSettings, type SummaryMediaItem, type VideoAudioTrack, type VideoChapter, type VideoFile, type VideoMarker, type VideoSession, type VideoSettings, type VideoSpeaker, type VideoTranscriptSegment, type VoiceIdentity } from "./api";
import "./styles.css";
import "./markers.css";
import "./selection.css";
import "./playback-performance.css";
import "./retention.css";
import "./activity-sessions.css";

type View = "busca" | "resumo" | "atividades" | "jogos" | "videos" | "timeline" | "captura";
type Panel = "settings" | "privacy" | null;
type CapturaTab = "fila" | "arquivos" | "diagnostico";
//: Prioridade e rótulo de cada faixa nas legendas simultâneas.
const CAPTION_ORDER:Record<string,number>={microphone:0,discord:1,system:2};
const CAPTION_LABELS:Record<string,string>={microphone:"MIC",discord:"DISCORD",system:"JOGO"};
const dayViews: View[] = ["resumo", "timeline", "atividades", "jogos"];

const icons: Record<View, string> = {
  busca: "⌕",
  resumo: "▤",
  atividades: "◎",
  jogos: "♢",
  videos: "▸",
  timeline: "◷",
  captura: "◍",
};

const labels: Record<View, [string, string]> = {
  busca: ["Busca na memória", "Capturas processadas e indexadas localmente"],
  resumo: ["Resumo", "Narrativa, tarefas e mídia relevante do dia"],
  atividades: ["Atividades", "Apps, sites e assuntos identificados ao longo do dia"],
  jogos: ["Jogos", "Progresso e tempo detectados automaticamente"],
  videos: ["Vídeos & sessões", "Buffer de gameplay e análise temporal"],
  timeline: ["Linha do tempo", "Tudo que aconteceu, em ordem"],
  captura: ["Central de captura", "Sensores, fila de processamento e arquivos brutos"],
};

const lensLabels: [View, string][] = [["resumo", "Resumo"], ["timeline", "Linha do tempo"], ["atividades", "Atividades"], ["jogos", "Jogos"]];

function bytes(value = 0) {
  if (value < 1024 ** 2) return `${(value / 1024).toFixed(0)} KB`;
  if (value < 1024 ** 3) return `${(value / 1024 ** 2).toFixed(1)} MB`;
  return `${(value / 1024 ** 3).toFixed(2)} GB`;
}

const gameCovers: Record<string,string> = {
  // Ícones quadrados selecionados na seção Icons do SteamGridDB.
  "Big Walk": "https://cdn2.steamgriddb.com/icon/c7dfe95373bfe4bca2cfa4a1f7383fda.png",
  "Counter-Strike 2": "https://cdn2.steamgriddb.com/icon/b5b51ea98a0fe3ba71787a570deee800.png",
  "Lockdown Protocol": "https://cdn2.steamgriddb.com/icon/7000f8f47b5964d197184084f20707ee/32/256x256.png",
  "Minecraft": "https://cdn2.steamgriddb.com/icon/5698620bc382e43590e89eefc3097d3e.png",
  "osu!": "https://cdn2.steamgriddb.com/icon/01741e5669e3f7622b92810ab0449276.png",
  "Persona 5 Royal": "https://cdn2.steamgriddb.com/icon/bbba677a7830a14343512ae9637e3879.png",
  "Pavlov VR": "https://cdn2.steamgriddb.com/icon/dbda8f25d0b2e3b1d3712ac08963fadb/32/256x256.png",
  "Roblox": "https://cdn2.steamgriddb.com/icon/177db6acfe388526a4c7bff88e1feb15.png",
  "Tabletop Simulator": "https://cdn2.steamgriddb.com/icon/4eb03dd1fe19a0c7441794a10bf4e2f0.png",
  "VALORANT": "https://cdn2.steamgriddb.com/icon/191c62d342811d1a0d3d0528ec35cd2d/32/256x256.png",
};

function canonicalGameName(value = "", acceptRecordedTitle = false) {
  const raw=value.trim();
  const key=raw.toLocaleLowerCase("pt-BR").replace(/\.exe$/," ").replace(/[^a-z0-9!]+/g," ").trim();
  if(!key)return "";
  if(key.includes("big walk"))return "Big Walk";
  if(key==="cs2"||key.includes("counter strike"))return "Counter-Strike 2";
  if(key.includes("osu! ")||key.endsWith("osu!")||key==="osu")return "osu!";
  if(key.includes("tabletop simulator"))return "Tabletop Simulator";
  if(key.includes("roblox")||key==="sober")return "Roblox";
  if(key.includes("pavlov"))return "Pavlov VR";
  if(key.includes("minecraft"))return "Minecraft";
  if(key.includes("valorant"))return "VALORANT";
  if(key.includes("persona 5")||key==="p5r")return "Persona 5 Royal";
  if(key.includes("lockdown protocol"))return "Lockdown Protocol";
  if(acceptRecordedTitle){
    const title=raw.split(" | ",1)[0].replace(/\.exe$/i,"").trim();
    if(title&&!/^(jogo|game|sessão de jogo)$/i.test(title))return title.slice(0,80);
  }
  return "";
}

function sessionGameName(session: VideoSession) {
  const evidence=`${session.name} ${session.summary} ${session.clips.map(clip=>clip.game).join(" ")}`.toLocaleLowerCase("pt-BR");
  if(/pizzushi|employees lose|employees win/.test(evidence))return "Lockdown Protocol";
  const reliable=session.clips.filter(clip=>clip.game_source==="window").map(clip=>canonicalGameName(clip.game,true)).filter(Boolean);
  const candidates=reliable.length?reliable:session.clips.map(clip=>canonicalGameName(clip.game)).filter(Boolean);
  if(!candidates.length)return canonicalGameName(`${session.name} ${session.summary}`);
  const counts=new Map<string,number>();
  candidates.forEach(game=>counts.set(game,(counts.get(game)||0)+1));
  return [...counts].sort((a,b)=>b[1]-a[1]||a[0].localeCompare(b[0],"pt-BR"))[0][0];
}

function GameCover({game}:{game:string}) {
  const [failed,setFailed]=useState(false);
  const initials=game.split(/\s+/).map(part=>part[0]).join("").slice(0,2).toUpperCase();
  return <span className="game-option-cover" aria-hidden="true">{!failed&&gameCovers[game]?<img src={gameCovers[game]} alt="" onError={()=>setFailed(true)}/>:<b>{initials}</b>}</span>;
}

function analysisAverage(milliseconds: number) {
  if (!milliseconds) return "—";
  if (milliseconds < 60000) return `${(milliseconds / 1000).toFixed(milliseconds < 10000 ? 1 : 0).replace(".", ",")}s`;
  const total = Math.round(milliseconds / 1000);
  return `${Math.floor(total / 60)}min ${String(total % 60).padStart(2, "0")}s`;
}

function queueEta(totalSeconds: number) {
  if (totalSeconds < 60) return `${Math.round(totalSeconds)}s`;
  const minutes = Math.round(totalSeconds / 60);
  if (minutes < 60) return `${minutes}min`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return minutes % 60 ? `${hours}h ${minutes % 60}min` : `${hours}h`;
  return hours % 24 ? `${Math.floor(hours / 24)}d ${hours % 24}h` : `${Math.floor(hours / 24)}d`;
}

function sessionDuration(totalSeconds: number) {
  const total=Math.max(0,Math.floor(totalSeconds));
  const hours=Math.floor(total/3600);const minutes=Math.floor(total%3600/60);const seconds=total%60;
  return hours?`${hours}:${String(minutes).padStart(2,"0")}:${String(seconds).padStart(2,"0")}`:`${minutes}:${String(seconds).padStart(2,"0")}`;
}

function EmptyView({ view }: { view: View }) {
  const copy = {
    busca: ["A busca será ativada com o índice", "As capturas já estão sendo coletadas. O próximo estágio conecta transcrições, descrições e SQLite FTS5."],
    resumo: ["Nenhum resumo processado ainda", "Quando o lote noturno produzir o primeiro resumo, ele aparecerá aqui com tarefas, reuniões e momentos-chave."],
    atividades: ["Nenhuma atividade identificada", "Gere os resumos horários para extrair apps, sites, pesquisas e assuntos."],
    jogos: ["Detecção de jogos ainda não indexada", "As sessões e conquistas serão derivadas das descrições de tela e dos títulos de janela."],
    videos: ["Nenhum segmento gravado", "Ative o gravador e abra um app correspondente à lista configurada."],
    timeline: ["A linha do tempo aguarda o índice", "Áudios e screenshots existentes serão organizados aqui depois do primeiro processamento."],
    captura: ["Nada por aqui ainda", "O estado dos sensores e a fila de processamento aparecerão nesta central."],
  }[view];
  return <div className="empty"><div className="empty-icon">{icons[view]}</div><h2>{copy[0]}</h2><p>{copy[1]}</p></div>;
}

function groupCaptures(captures: Capture[]) {
  const groups = new Map<string, Capture[]>();
  for (const capture of captures) {
    const key = capture.captured_at.slice(0, 19);
    groups.set(key, [...(groups.get(key) || []), capture]);
  }
  return [...groups.values()].map(group => {
    const primary = group.find(item => item.kind === "audio") || group[0];
    const image = group.find(item => item.image_url)?.image_url || primary.paired_image_url;
    const screenTexts = group.filter(item => item.kind === "screen").map(item => item.text);
    const pairedTexts = group.map(item => item.paired_image_text);
    const audioTexts = group.filter(item => item.kind === "audio").map(item => item.text);
    const orderedTexts = [...screenTexts, ...pairedTexts, ...audioTexts].filter(Boolean);
    return {...primary,
      title: [...new Set(group.map(item => item.title).filter(Boolean))].join(" + "),
      text: [...new Set(orderedTexts)].join("\n\n"),
      tags: [...new Set(group.flatMap(item => item.tags))], image_url: image || null,
      capture_ids: group.map(item => item.id)};
  });
}

function CaptureCard({ item, onOpen, onDelete, disabled=false }: { item: Capture; onOpen: (url:string|null,name:string,text:string,model:string,kind:Capture["kind"],capture:Capture)=>void; onDelete:(item:Capture)=>void; disabled?:boolean }) {
  const time = new Date(item.captured_at).toLocaleTimeString("pt-BR", {hour:"2-digit",minute:"2-digit"});
  const open=()=>onOpen(item.image_url || item.paired_image_url,item.source_path.split("/").pop()||item.title,item.text,item.model,item.kind,item);
  return <article className="memory-card" role="button" tabIndex={0} onClick={open} onKeyDown={event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();open()}}}>
    <div className={`memory-thumb ${item.kind}`}>{item.image_url ? <img src={item.image_url}/> : <span>{item.kind==="screen"&&!item.source_available?"Imagem indisponível":"▮▮"}</span>}</div>
    <div className="memory-body"><div className="memory-meta"><span className={`tag ${item.kind}`}>{item.kind === "screen" ? "Tela" : "Áudio"}</span><span>{time} · {item.app || "Local"}</span></div>
      <h3>{item.title}</h3><p>{item.text}</p>{item.text.length>180&&<span className="expand-description">Clique no bloco para ler tudo</span>}<div className="tags">{item.tags.map(tag => <span key={tag}>{tag}</span>)}</div>
    </div>
    <button className="item-delete" disabled={disabled} title="Excluir este item" aria-label="Excluir este item" onClick={event=>{event.stopPropagation();onDelete(item)}}>×</button>
  </article>;
}

function AudioPlayer({src}:{src:string}){
  const ref=useRef<HTMLAudioElement>(null); const lastClock=useRef(0); const [playing,setPlaying]=useState(false); const [current,setCurrent]=useState(0); const [duration,setDuration]=useState(0);
  const updateClock=(value:number)=>{const now=performance.now();if(now-lastClock.current>=200){lastClock.current=now;setCurrent(value)}};
  const fmt=(seconds:number)=>`${Math.floor(seconds/60)}:${Math.floor(seconds%60).toString().padStart(2,"0")}`;
  return <div className="lume-player"><audio ref={ref} src={src} preload="none" onTimeUpdate={e=>updateClock(e.currentTarget.currentTime)} onLoadedMetadata={e=>setDuration(e.currentTarget.duration)} onEnded={()=>{setPlaying(false);setCurrent(duration)}}/>
    <button onClick={()=>{const audio=ref.current!; if(audio.paused){audio.play();setPlaying(true)}else{audio.pause();setPlaying(false)}}}>{playing?"❚❚":"▶"}</button>
    <span>{fmt(current)}</span><input type="range" min="0" max={duration||0} step="0.1" value={current} onChange={e=>{ref.current!.currentTime=+e.target.value;setCurrent(+e.target.value)}}/><span>{fmt(duration||0)}</span>
  </div>
}

type SourceTrack="microphone"|"discord"|"system";
type TranscriptTrackFilter="all"|SourceTrack;

function SyncedAudioPlayer({capture,onIdentify}:{capture:Capture;onIdentify?:(speaker:VideoSpeaker)=>void}){
  const audioRef=useRef<HTMLAudioElement>(null);const trackRefs=useRef(new Map<SourceTrack,HTMLAudioElement>());const activeRef=useRef<HTMLDivElement>(null);const lastClock=useRef(0);
  const [playing,setPlaying]=useState(false);const [current,setCurrent]=useState(0);const [duration,setDuration]=useState(capture.duration_seconds||0);const [volume,setVolume]=useState(1);const [rate,setRate]=useState(1);const [trackFilter,setTrackFilter]=useState<TranscriptTrackFilter>("all");
  const [trackVolumes,setTrackVolumes]=useState<Record<SourceTrack,number>>(()=>{try{return {...{microphone:1,discord:1,system:1},...JSON.parse(localStorage.getItem("lume-audio-track-volumes")||"{}")} as Record<SourceTrack,number>}catch{return {microphone:1,discord:1,system:1}}});
  const segments=capture.transcript_segments||[];
  const separatedSources=segments.some(segment=>!!segment.source)&&(capture.audio_channels||1)>1;
  const trackChoices=(capture.audio_channels||1)>=3?([['microphone','Meu microfone'],['discord','Discord'],['system','Outros sons']] as const):([['microphone','Meu microfone'],['system','Call / conteúdo']] as const);
  const visibleSegments=trackFilter==="all"?segments:segments.filter(segment=>segment.source===trackFilter);
  const activeIndexes=visibleSegments.map((segment,index)=>({segment,index})).filter(({segment})=>current>=segment.start&&current<segment.end).map(({index})=>index);
  const activeSet=new Set(activeIndexes);const activeIndex=activeIndexes[0]??-1;
  const activeItems=activeIndexes.map(index=>{const segment=visibleSegments[index];const itemSpeaker=segment.speaker?(capture.speakers||[]).find(item=>item.id===segment.speaker):null;return {segment,speaker:itemSpeaker}});
  const currentIsNamingSample=activeItems.some(item=>!!item.speaker&&current>=item.speaker.sample_start&&current<=item.speaker.sample_end);
  const syncTracks=(value:number,shouldPlay:boolean,force=false)=>trackRefs.current.forEach(node=>{if(node.readyState<1)return;if(force||Math.abs(node.currentTime-value)>.18)node.currentTime=Math.min(value,node.duration||value);node.playbackRate=rate;if(shouldPlay)void node.play().catch(()=>{});else node.pause()});
  const updateClock=(value:number)=>{const now=performance.now();if(now-lastClock.current>=200){lastClock.current=now;setCurrent(value);if(separatedSources)syncTracks(value,!(audioRef.current?.paused??true))}};
  useEffect(()=>{localStorage.setItem("lume-audio-track-volumes",JSON.stringify(trackVolumes));trackRefs.current.forEach((node,track)=>node.volume=trackVolumes[track])},[trackVolumes]);
  useEffect(()=>{if(playing&&activeRef.current)activeRef.current.scrollIntoView({block:"nearest",behavior:"auto"})},[activeIndexes.join(","),playing]);
  const seek=(value:number)=>{const audio=audioRef.current;if(audio){audio.currentTime=value;syncTracks(value,!audio.paused,true);setCurrent(value)}};
  const toggle=()=>{const audio=audioRef.current;if(!audio)return;if(audio.paused){void audio.play();setPlaying(true)}else{audio.pause();setPlaying(false)}};
  const changeRate=()=>{const next=rate===1?1.25:rate===1.25?1.5:rate===1.5?2:.75;setRate(next);if(audioRef.current)audioRef.current.playbackRate=next;trackRefs.current.forEach(node=>node.playbackRate=next)};
  return <section className="synced-audio-player">
    <audio ref={audioRef} src={`/api/audio?path=${encodeURIComponent(capture.source_path)}&track=${separatedSources?"original":"mix"}`} muted={separatedSources} preload="metadata" onLoadedMetadata={event=>{setDuration(event.currentTarget.duration);event.currentTarget.currentTime=Math.min(current,event.currentTarget.duration||current);syncTracks(event.currentTarget.currentTime,false,true)}} onTimeUpdate={event=>updateClock(event.currentTarget.currentTime)} onPlay={event=>{setPlaying(true);syncTracks(event.currentTarget.currentTime,true,true)}} onPause={()=>{setPlaying(false);syncTracks(current,false)}} onEnded={()=>{setPlaying(false);syncTracks(duration,false);setCurrent(duration)}}/>
    {separatedSources&&<div className="audio-track-mixer"><header><strong>Faixas de áudio</strong><span>Volumes independentes</span></header>{trackChoices.map(([track,label])=><label key={track}><audio ref={node=>{if(node)trackRefs.current.set(track,node);else trackRefs.current.delete(track)}} src={`/api/audio?path=${encodeURIComponent(capture.source_path)}&track=${track}`} preload="metadata" onLoadedMetadata={event=>{event.currentTarget.currentTime=Math.min(current,event.currentTarget.duration||current);event.currentTarget.volume=trackVolumes[track];event.currentTarget.playbackRate=rate;if(playing)void event.currentTarget.play().catch(()=>{})}}/><span>{label}</span><input aria-label={`Volume de ${label}`} type="range" min="0" max="1" step="0.01" value={trackVolumes[track]} onChange={event=>{const next=+event.target.value;const node=trackRefs.current.get(track);if(node)node.volume=next;setTrackVolumes(values=>({...values,[track]:next}))}}/><output>{Math.round(trackVolumes[track]*100)}%</output></label>)}</div>}
    {separatedSources&&<div className="transcript-track-filter"><label><span>Mostrar falas da faixa</span><select value={trackFilter} onChange={event=>setTrackFilter(event.target.value as TranscriptTrackFilter)}><option value="all">Todas as faixas</option>{trackChoices.map(([track,label])=><option value={track} key={track}>{label}</option>)}</select></label><small>{visibleSegments.length} de {segments.length} falas</small></div>}
    <div className={`audio-now ${currentIsNamingSample?"naming-sample":""}`}><span className={`audio-speaker-dot ${activeItems.some(item=>!!item.speaker)?"known":""}`}/><div className="audio-now-stack"><small>{currentIsNamingSample?"Amostra que definiu o nome":activeItems.length>1?`${activeItems.length} faixas falando agora`:"Falando agora"}</small>{activeItems.length?activeItems.map(({segment,speaker:itemSpeaker},index)=>{const itemLabel=itemSpeaker?.identified?itemSpeaker.label:itemSpeaker?.label||(segment.source==="microphone"?"Você":segment.source==="discord"?"Voz do Discord":segment.source==="system"?"Voz de outro conteúdo":"Voz não identificada");return <section key={`${segment.source||"mix"}-${segment.start}-${segment.end}-${index}`}><strong>{itemLabel}{segment.source&&<em className={`source-badge ${segment.source}`}>{segment.source==="microphone"?"MEU MICROFONE":segment.source==="discord"?"DISCORD":"OUTROS SONS"}</em>}</strong><p>{segment.text}</p>{itemSpeaker&&!itemSpeaker.fixed&&onIdentify&&<button className="now-rename" onClick={()=>onIdentify(itemSpeaker)}>Corrigir nome</button>}</section>}):<p>Sem fala neste momento</p>}</div></div>
    <div className="audio-controls"><button className="audio-play" onClick={toggle} aria-label={playing?"Pausar":"Reproduzir"}>{playing?"❚❚":"▶"}</button><time>{videoTime(current)}</time><input className="audio-progress" type="range" min="0" max={duration||0} step="0.05" value={current} style={{"--progress":`${duration?current/duration*100:0}%`} as React.CSSProperties} onChange={event=>seek(+event.target.value)}/><time>{videoTime(duration)}</time>{!separatedSources&&<><button className="audio-volume" onClick={()=>{const next=volume?0:1;setVolume(next);if(audioRef.current)audioRef.current.volume=next}}>{volume?"🔊":"🔇"}</button><input className="volume-range" type="range" min="0" max="1" step="0.05" value={volume} onChange={event=>{const next=+event.target.value;setVolume(next);if(audioRef.current)audioRef.current.volume=next}}/></>}<button className="audio-rate" onClick={changeRate}>{rate}×</button></div>
    {visibleSegments.length?<div className="synced-transcript">{visibleSegments.map((segment,index)=>{const itemSpeaker=segment.speaker?(capture.speakers||[]).find(item=>item.id===segment.speaker):null;const namingSample=!!itemSpeaker&&!itemSpeaker.fixed&&segment.end>=itemSpeaker.sample_start&&segment.start<=itemSpeaker.sample_end;const sourceLabel=segment.source==="microphone"?"MEU MICROFONE":segment.source==="discord"?"DISCORD":segment.source==="system"?"OUTROS SONS":"";return <div ref={index===activeIndex?activeRef:null} className={activeSet.has(index)?"active":""} key={`${segment.source||"mix"}-${segment.start}-${segment.end}-${index}`}><button className="transcript-seek" onClick={()=>seek(segment.start)}><time>{videoTime(segment.start)}</time><span><strong>{itemSpeaker?.label||(segment.source==="discord"?"Voz do Discord":segment.source==="system"?"Voz de outro conteúdo":"Voz não identificada")}{sourceLabel&&<small className={`source-badge ${segment.source}`}>{sourceLabel}</small>}{namingSample&&<small>◆ amostra usada para este nome</small>}</strong><em>{segment.text}</em></span></button>{itemSpeaker&&!itemSpeaker.fixed&&onIdentify&&<button className="segment-rename" onClick={()=>onIdentify(itemSpeaker)}>Corrigir</button>}</div>})}</div>:<p className="transcript-fallback">{segments.length?"Nenhuma fala nesta faixa.":capture.text}</p>}
  </section>
}

function voiceGroups(capture:Capture){
  const groups=new Map<string,VideoSpeaker[]>();
  for(const speaker of capture.speakers||[]){if(speaker.fixed)continue;const key=speaker.identity_id?`identity:${speaker.identity_id}`:`speaker:${speaker.id}`;groups.set(key,[...(groups.get(key)||[]),speaker])}
  return [...groups.entries()].map(([key,speakers])=>({key,speakers,label:speakers[0].label,identified:!!speakers[0].identity_id,representative:[...speakers].sort((a,b)=>b.duration-a.duration)[0]}));
}

function sampleIsOverlapped(capture:Pick<Capture,"audio_events">,speaker:VideoSpeaker){
  if(speaker.sample_overlapped)return true;
  return (capture.audio_events||[]).some(event=>event.event==="fala sobreposta"&&Math.min(speaker.sample_end,event.end)-Math.max(speaker.sample_start,event.start)>=.2);
}

function VoiceSampleTranscript({capture,speaker}:{capture:Pick<Capture,"transcript_segments"|"speakers"|"audio_events">;speaker:VideoSpeaker}){
  const segments=(capture.transcript_segments||[]).filter(segment=>Math.min(speaker.sample_end,segment.end)-Math.max(speaker.sample_start,segment.start)>0);
  const overlapped=sampleIsOverlapped(capture,speaker);
  const label=(segment:VideoTranscriptSegment)=>{
    if(segment.speaker===speaker.id)return speaker.label;
    const known=(capture.speakers||[]).find(item=>item.id===segment.speaker)?.label;
    return known||(segment.source==="microphone"?"Meu microfone":segment.source==="discord"?"Voz do Discord":segment.source==="system"?"Outros sons":"Voz não identificada");
  };
  return <div className={`voice-sample-transcript ${overlapped?"overlapped":""}`}><header><strong>Transcrição desta amostra</strong>{overlapped&&<span>⚠ fala sobreposta</span>}</header>{segments.length?segments.map((segment,index)=><p className={segment.speaker===speaker.id?"target":""} key={`${segment.start}-${index}`}><time>{videoTime(segment.start)}</time><span><b>{label(segment)}:</b> {segment.text}</span></p>):<small>Não há transcrição neste intervalo.</small>}{overlapped&&<small>Esta amostra não deve ser usada para criar ou corrigir uma identidade vocal.</small>}</div>;
}

function VoiceIdentitySelector({speaker,profiles,disabled,onIdentify}:{speaker:VideoSpeaker;profiles:VoiceIdentity[];disabled:boolean;onIdentify:(speaker:VideoSpeaker,label:string)=>Promise<void>}){
  const current=speaker.identity_id?`identity:${speaker.identity_id}`:"";
  const [choice,setChoice]=useState(current);const [other,setOther]=useState("");const [saving,setSaving]=useState(false);
  useEffect(()=>setChoice(current),[current]);
  const save=async(label:string)=>{const clean=label.trim();if(!clean)return;setSaving(true);try{await onIdentify(speaker,clean);setOther("")}finally{setSaving(false)}};
  const choose=(value:string)=>{setChoice(value);if(value.startsWith("identity:")){const id=+value.slice(9);const profile=profiles.find(item=>item.id===id);if(profile)void save(profile.label)}};
  return <div className="voice-identity-select"><select aria-label={`Identificar ${speaker.label}`} disabled={disabled||saving} value={choice} onChange={event=>choose(event.target.value)}><option value="">Selecionar pessoa…</option>{profiles.map(profile=><option value={`identity:${profile.id}`} key={profile.id}>{profile.label}</option>)}<option value="other">Outro nome…</option></select>{choice==="other"&&<div><input autoFocus value={other} maxLength={80} placeholder="Nome da pessoa" onChange={event=>setOther(event.target.value)} onKeyDown={event=>{if(event.key==="Enter")void save(other)}}/><button className="ghost" disabled={!other.trim()||saving} onClick={()=>void save(other)}>{saving?"Salvando…":"Salvar"}</button></div>}</div>;
}

function VoiceIdentityPanel({capture,onIdentify}:{capture:Capture;onIdentify:(speaker:VideoSpeaker,label:string)=>Promise<void>}){
  const [profiles,setProfiles]=useState<VoiceIdentity[]>([]);const [trackFilter,setTrackFilter]=useState<TranscriptTrackFilter>("all");
  const refreshProfiles=async()=>{const result=await api.voiceIdentities();setProfiles(result.items)};
  useEffect(()=>{let active=true;void api.voiceIdentities().then(result=>{if(active)setProfiles(result.items)}).catch(()=>{});return()=>{active=false}},[]);
  const identify=async(speaker:VideoSpeaker,label:string)=>{await onIdentify(speaker,label);await refreshProfiles()};
  const groups=voiceGroups(capture);const visibleGroups=trackFilter==="all"?groups:groups.filter(group=>group.speakers.some(speaker=>speaker.source===trackFilter));
  const availableTracks=([['microphone','Meu microfone'],['discord','Discord'],['system','Outros sons']] as const).filter(([track])=>groups.some(group=>group.speakers.some(speaker=>speaker.source===track)));
  return <aside className="lightbox-voices"><header><div><strong>Identificar vozes</strong><small>A faixa de tempo e a transcrição mostram exatamente qual amostra sustenta cada nome.</small></div>{availableTracks.length>1&&<label><span>Faixa</span><select value={trackFilter} onChange={event=>setTrackFilter(event.target.value as TranscriptTrackFilter)}><option value="all">Todas</option>{availableTracks.map(([track,label])=><option value={track} key={track}>{label}</option>)}</select></label>}</header><div className="voice-scroll">{visibleGroups.map(group=>{const blocked=sampleIsOverlapped(capture,group.representative);return <article className="voice-group" key={group.key}><div className="voice-group-title"><strong>{group.identified?`${group.label} ✓`:group.label}</strong><small>Amostra principal · {videoTime(group.representative.sample_start)}–{videoTime(group.representative.sample_end)} · {group.representative.duration.toFixed(1)}s</small><small>{group.speakers.length} {group.speakers.length===1?"grupo de voz":"grupos de voz"} nesta gravação</small></div><AudioPlayer src={`/api/captures/${capture.id}/speakers/${group.representative.id}/sample`}/><VoiceIdentitySelector speaker={group.representative} profiles={profiles} disabled={blocked} onIdentify={identify}/><VoiceSampleTranscript capture={capture} speaker={group.representative}/>{group.speakers.length>1&&<details><summary>Revisar {group.speakers.length} amostras</summary><div>{group.speakers.map((speaker,index)=>{const sampleBlocked=sampleIsOverlapped(capture,speaker);return <section key={speaker.id}><span>Amostra {index+1} · {videoTime(speaker.sample_start)}–{videoTime(speaker.sample_end)} · {speaker.duration.toFixed(1)}s</span><AudioPlayer src={`/api/captures/${capture.id}/speakers/${speaker.id}/sample`}/><VoiceIdentitySelector speaker={speaker} profiles={profiles} disabled={sampleBlocked} onIdentify={identify}/><VoiceSampleTranscript capture={capture} speaker={speaker}/></section>})}</div></details>}</article>})}{!visibleGroups.length&&<p>Nenhuma voz encontrada nesta faixa.</p>}</div></aside>
}

function SavedVoiceProfiles({profiles,onDelete,onClose}:{profiles:VoiceIdentity[];onDelete:(profile:VoiceIdentity)=>Promise<void>;onClose:()=>void}){
  const duplicatePairs=profiles.reduce((total,item)=>total+item.possible_duplicates.filter(other=>item.id<other.id).length,0);
  return <aside className="saved-voice-profiles"><header><div><strong>Perfis de voz salvos</strong><small>{profiles.length} pessoas · {duplicatePairs?`${duplicatePairs} possível duplicidade${duplicatePairs>1?"s":""}`:"nenhuma duplicidade provável"}</small></div><button onClick={onClose}>×</button></header><div>{profiles.map(profile=><article className={profile.possible_duplicates.length?"possible-duplicate":""} key={profile.id}><span className="profile-avatar">{profile.label.slice(0,1).toUpperCase()}</span><div><strong>{profile.label}</strong><small>{profile.sample_count} {profile.sample_count===1?"gravação confirmada":"gravações confirmadas"} · atualizado em {new Date(profile.updated_at.replace(" ","T")+"Z").toLocaleDateString("pt-BR")}</small>{profile.possible_duplicates.map(other=><em key={other.id}>Possível duplicidade com {other.label} · {Math.round(other.similarity*100)}%</em>)}</div><button className="profile-delete" onClick={()=>void onDelete(profile)}>Remover</button></article>)}</div>{!profiles.length&&<p>Nenhum perfil identificado ainda.</p>}</aside>
}

function AudioAnalysis({file,onChanged}:{file:RawFile;onChanged:()=>void}){
  const audioRef=useRef<HTMLAudioElement|null>(null);
  const labels=new Map((file.speakers||[]).map(item=>[item.id,item.label]));
  const seek=(seconds:number)=>{const audio=document.querySelector<HTMLAudioElement>(`audio[data-capture="${file.capture_id}"]`);if(audio){audio.currentTime=seconds;audio.play()}};
  const rename=async(speaker:VideoSpeaker)=>{if(!file.capture_id)return;const label=window.prompt("Nome desta voz",speaker.label)?.trim();if(!label||label===speaker.label)return;await api.renameCaptureSpeaker(file.capture_id,speaker.id,label);onChanged()};
  return <details className="audio-analysis" open><summary>Análise detalhada · {file.transcript_segments.length} trechos · {file.speakers.length} vozes · {file.audio_events.length} eventos</summary>
    <audio ref={audioRef} data-capture={file.capture_id} src={file.url} preload="metadata"/>
    {!!file.speakers?.length&&<section className="speaker-panel"><h3>Vozes identificadas</h3><div>{file.speakers.map(speaker=><article key={speaker.id}><strong>{speaker.label}{speaker.source&&<small className={`source-badge ${speaker.source}`}>{speaker.source==="microphone"?"MEU MICROFONE":speaker.source==="discord"?"DISCORD":"OUTROS SONS"}</small>}</strong>{file.capture_id&&!speaker.fixed&&<AudioPlayer src={`/api/captures/${file.capture_id}/speakers/${speaker.id}/sample`}/>} {!speaker.fixed&&<button className="ghost" onClick={()=>rename(speaker)}>Renomear</button>}</article>)}</div></section>}
    {!!file.audio_events?.length&&<section className="audio-events"><h3>Eventos acústicos</h3><div>{file.audio_events.map((event,index)=><button key={`${event.start}-${event.event}-${index}`} onClick={()=>seek(event.start)}><time>{videoTime(event.start)}</time><strong>[{event.event}]</strong><span>{Math.round(event.confidence*100)}%</span></button>)}</div></section>}
    <div className="transcript-segments">{(file.transcript_segments||[]).map((segment,index)=><button key={`${segment.start}-${index}`} onClick={()=>seek(segment.start)}><time>{videoTime(segment.start)}</time><span><strong>{(segment.speaker&&labels.get(segment.speaker))||(segment.source==="microphone"?"Você":segment.source==="discord"?"Discord":segment.source==="system"?"Outros sons":"Voz")}: </strong>{segment.text} {(segment.events||[]).map(event=><em key={event}>[{event}]</em>)}</span></button>)}</div>
  </details>
}

function videoTime(seconds:number){return `${Math.floor(seconds/60)}:${Math.floor(seconds%60).toString().padStart(2,"0")}`}
function playerTime(seconds:number){
  const total=Math.max(0,Math.floor(seconds));
  if(total<3600)return videoTime(total);
  return `${Math.floor(total/3600)}:${String(Math.floor(total%3600/60)).padStart(2,"0")}:${String(total%60).padStart(2,"0")}`;
}
const TIMELINE_ZOOM_LEVELS=[1,2,4,8,16,32];
function chapterStart(chapter:VideoChapter){if(typeof chapter.start==="number")return chapter.start;const first=chapter.time.split(/[–-]/)[0].trim().split(":").map(Number);return first.reduce((total,value)=>total*60+value,0)}

type EditableVideoSpeaker = VideoSpeaker & {videoId:number;clipLabel?:string};

function ChapterReader({chapter,speakers=[],onPlay,onRename,onClose}:{chapter:VideoChapter;speakers?:EditableVideoSpeaker[];onPlay:()=>void;onRename:(speaker:EditableVideoSpeaker)=>void;onClose:()=>void}){
  useEffect(()=>{const close=(event:KeyboardEvent)=>{if(event.key==="Escape")onClose()};window.addEventListener("keydown",close);return()=>window.removeEventListener("keydown",close)},[onClose]);
  const context=[chapter.app&&`Aplicativo: ${chapter.app}`,chapter.game&&`Jogo: ${chapter.game}`].filter(Boolean);
  return <div className="chapter-reader-overlay" onMouseDown={onClose}>
    <article className="chapter-reader" onMouseDown={event=>event.stopPropagation()}>
      <header><div><span className="eyebrow">Resultados do capítulo · {chapter.time}</span><h2>{chapter.title}</h2></div><button className="icon-button" title="Fechar" onClick={onClose}>×</button></header>
      <div className="chapter-reader-body">
        <div className="chapter-reader-actions"><button onClick={onPlay}>▶ Reproduzir deste ponto</button>{context.map(item=><span key={item}>{item}</span>)}</div>
        {chapter.summary&&<section><h3>Resumo</h3><p>{chapter.summary}</p></section>}
        {!!chapter.events?.length&&<section><h3>O que aconteceu</h3><ul>{chapter.events.map((event,index)=><li key={`${event}-${index}`}>{event}</li>)}</ul></section>}
        {!!chapter.evidence?.length&&<section><h3>Evidências observadas</h3><ul>{chapter.evidence.map((item,index)=><li key={`${item}-${index}`}>{item}</li>)}</ul></section>}
        {chapter.interpretation&&<section><h3>Interpretação</h3><p>{chapter.interpretation}</p></section>}
        {!!speakers.length&&<section className="chapter-speakers"><h3>Pessoas na sessão</h3><p>Ouça a amostra usada pela diarização e corrija o nome. A identificação fica salva para análises futuras.</p><div>{speakers.map(speaker=><article key={`${speaker.videoId}-${speaker.id}`}><div><strong>{speaker.label}</strong><small>{speaker.clipLabel}{speaker.source&&<span className={`source-badge ${speaker.source}`}>{speaker.source==="microphone"?"MEU MICROFONE":speaker.source==="discord"?"DISCORD":"ÁUDIO DO SISTEMA"}</span>}</small></div><AudioPlayer src={`/api/videos/${speaker.videoId}/speakers/${speaker.id}/sample`}/><button className="ghost" onClick={()=>onRename(speaker)}>Definir pessoa</button></article>)}</div></section>}
        {!!chapter.audio_events?.length&&<details className="chapter-reader-collapsible"><summary><span>Eventos de áudio</span><small>{chapter.audio_events.length} {chapter.audio_events.length===1?"evento":"eventos"}</small></summary><div><ul>{chapter.audio_events.map((event,index)=><li key={`${event.start}-${event.event}-${index}`}><time>{videoTime(event.start)}</time> [{event.event}]</li>)}</ul></div></details>}
        {chapter.transcript&&<details className="chapter-reader-collapsible"><summary><span>Transcrição do capítulo</span><small>Expandir texto completo</small></summary><div><p className="chapter-reader-transcript">{chapter.transcript}</p></div></details>}
        {chapter.web_findings&&<section><h3>Pesquisa complementar</h3><p>{chapter.web_findings}</p></section>}
        {!!chapter.web_sources?.length&&<section><h3>Fontes</h3><div className="chapter-reader-sources">{chapter.web_sources.map(source=><a href={source.url} target="_blank" rel="noreferrer" key={source.url}><strong>{source.title||source.url}</strong>{source.snippet&&<span>{source.snippet}</span>}</a>)}</div></section>}
        {!!chapter.tags?.length&&<div className="chapter-reader-tags">{chapter.tags.map(tag=><span key={tag}>{tag}</span>)}</div>}
      </div>
    </article>
  </div>
}

function CustomVideoPlayer({src,mediaPath,title,chapters=[],segments=[],speakers=[],editableSpeakers,markers=[],videoId,preroll=8,hotkey="F8",onMarkersChanged,onEnded,autoPlay=false}:{src:string;mediaPath?:string;title:string;chapters?:VideoChapter[];segments?:VideoTranscriptSegment[];speakers?:VideoSpeaker[];editableSpeakers?:EditableVideoSpeaker[];markers?:VideoMarker[];videoId?:number;preroll?:number;hotkey?:string;onMarkersChanged?:()=>void;onEnded?:()=>void;autoPlay?:boolean}){
  const video=useRef<HTMLVideoElement>(null);const stage=useRef<HTMLDivElement>(null);const lastClock=useRef(0);const audioNodes=useRef(new Map<number,HTMLAudioElement>());const scrubbing=useRef(false);const [playing,setPlaying]=useState(false);const [current,setCurrent]=useState(0);const [scrubTime,setScrubTime]=useState<number|null>(null);const [duration,setDuration]=useState(0);const [captions,setCaptions]=useState(true);const [fullscreen,setFullscreen]=useState(false);const [timelineZoom,setTimelineZoom]=useState(1);const [timelineWindowStart,setTimelineWindowStart]=useState(0);const [readingChapter,setReadingChapter]=useState<number|null>(null);const [audioTracks,setAudioTracks]=useState<VideoAudioTrack[]>([]);const [audioTracksPreparing,setAudioTracksPreparing]=useState(false);const [audioTracksManual,setAudioTracksManual]=useState(false);const [audioTrackJobId,setAudioTrackJobId]=useState<string>();const [manualAudioPath,setManualAudioPath]=useState<string|null>(null);const [cancelledAudioPath,setCancelledAudioPath]=useState<string|null>(null);const [trackVolumes,setTrackVolumes]=useState<Record<number,number>>({});const [trimOpen,setTrimOpen]=useState(false);const [trimStart,setTrimStart]=useState(0);const [trimEnd,setTrimEnd]=useState(0);const [trimming,setTrimming]=useState(false);const [trimMessage,setTrimMessage]=useState("");const [mediaRevision,setMediaRevision]=useState(0);
  // Todas as faixas que falam ao mesmo tempo, não só a primeira: microfone,
  // Discord e jogo costumam se sobrepor, e `find` devolvia quem tivesse
  // começado antes — não quem importa mais. A ordem é a de prioridade da fonte.
  const activeCaptions=captions?segments
    .filter(segment=>current>=segment.start&&current<=segment.end)
    .sort((a,b)=>(CAPTION_ORDER[a.source||""]??9)-(CAPTION_ORDER[b.source||""]??9))
    .slice(0,3):[];
  const syncTrackAudio=(seconds=video.current?.currentTime||0,force=false)=>{audioNodes.current.forEach(node=>{if(node.readyState>=1&&(force||Math.abs(node.currentTime-seconds)>.35))node.currentTime=seconds})};
  const playTrackAudio=()=>{const seconds=video.current?.currentTime||0;audioNodes.current.forEach((node,track)=>{if(node.readyState<1)return;if(Math.abs(node.currentTime-seconds)>.2)node.currentTime=seconds;node.volume=trackVolumes[track]??1;void node.play().catch(()=>{})})};
  const pauseTrackAudio=()=>audioNodes.current.forEach(node=>node.pause());
  const seek=(seconds:number)=>{if(video.current){video.current.currentTime=seconds;syncTrackAudio(seconds,true);setCurrent(seconds);video.current.play();setPlaying(true)}};
  const commitTimelineSeek=(seconds:number)=>{if(!video.current)return;video.current.currentTime=seconds;syncTrackAudio(seconds,true);setCurrent(seconds)};
  const addMarker=async()=>{if(!videoId||!video.current)return;await api.createVideoMarker(videoId,video.current.currentTime);onMarkersChanged?.()};
  const chapterSpeakers=editableSpeakers||(videoId?speakers.filter(speaker=>!speaker.fixed).map(speaker=>({...speaker,videoId})):[]);
  const renameSpeaker=async(speaker:EditableVideoSpeaker)=>{const next=prompt("Nome desta pessoa",speaker.label);if(next?.trim()){await api.renameVideoSpeaker(speaker.videoId,speaker.id,next.trim());onMarkersChanged?.()}};
  const updateClock=(value:number)=>{const now=performance.now();if(now-lastClock.current>=200){lastClock.current=now;setCurrent(value)}};
  useEffect(()=>{let active=true;let timer:number|undefined;let jobId:string|undefined;const wantsPreparation=manualAudioPath===mediaPath;setAudioTracks([]);setAudioTracksPreparing(false);setAudioTracksManual(false);setAudioTrackJobId(undefined);setTrackVolumes({});const cancelJob=(id:string)=>{if(mediaPath)void api.cancelVideoAudioTracks(mediaPath,id).catch(()=>{})};if(cancelledAudioPath===mediaPath&&!wantsPreparation){setAudioTracksManual(true);return()=>{active=false;pauseTrackAudio();audioNodes.current.clear()}}const load=async()=>{if(!mediaPath)return;try{const result=await api.videoAudioTracks(mediaPath,wantsPreparation);if(!active){if(result.job_id)cancelJob(result.job_id);return}jobId=result.job_id||jobId;setAudioTrackJobId(jobId);if(result.status==="preparing"){setAudioTracksPreparing(true);timer=window.setTimeout(load,750);return}setAudioTracksPreparing(false);if(result.status==="manual"||result.status==="error"){setAudioTracksManual(true);return}if(result.status==="ready"){setAudioTracksManual(false);setAudioTracks(result.items);setTrackVolumes(Object.fromEntries(result.items.map(item=>[item.track,1])))}}catch{if(active){setAudioTracksPreparing(false);setAudioTracksManual(true)}}};void load();return()=>{active=false;if(timer!==undefined)window.clearTimeout(timer);if(jobId)cancelJob(jobId);pauseTrackAudio();audioNodes.current.clear()}},[mediaPath,manualAudioPath,cancelledAudioPath]);
  useEffect(()=>{const player=video.current;return()=>{player?.pause();player?.removeAttribute("src");player?.load();audioNodes.current.forEach(node=>{node.pause();node.removeAttribute("src");node.load()});audioNodes.current.clear()}},[src,mediaRevision]);
  useEffect(()=>{if(autoPlay)video.current?.play().catch(()=>{})},[src,autoPlay]);
  useEffect(()=>{if(audioTracks.length&&video.current&&!video.current.paused)playTrackAudio()},[audioTracks]);
  useEffect(()=>{const changed=()=>setFullscreen(document.fullscreenElement===stage.current);document.addEventListener("fullscreenchange",changed);return()=>document.removeEventListener("fullscreenchange",changed)},[]);
  useEffect(()=>{if(timelineZoom===1){if(timelineWindowStart)setTimelineWindowStart(0);return}if(!playing||!duration)return;const windowSize=duration/timelineZoom;const end=timelineWindowStart+windowSize;if(current<timelineWindowStart||current>end)setTimelineWindowStart(Math.max(0,Math.min(duration-windowSize,current-windowSize*.15)))},[current,duration,playing,timelineZoom,timelineWindowStart]);
  useEffect(()=>{const listener=(event:KeyboardEvent)=>{if(event.key.toLowerCase()===hotkey.toLowerCase()&&videoId){event.preventDefault();addMarker()}};window.addEventListener("keydown",listener);return()=>window.removeEventListener("keydown",listener)},[videoId,hotkey]);
  const timelineWindow=timelineZoom>1?duration/timelineZoom:duration;const timelineMaxStart=Math.max(0,duration-timelineWindow);const timelineStart=Math.min(timelineWindowStart,timelineMaxStart);const timelineEnd=Math.min(duration,timelineStart+timelineWindow);const timelineValue=Math.max(timelineStart,Math.min(timelineEnd,scrubTime??current));const visibleMarkers=markers.filter(marker=>marker.offset_seconds>=timelineStart&&marker.offset_seconds<=timelineEnd);const changeTimelineZoom=(direction:number)=>{const index=TIMELINE_ZOOM_LEVELS.indexOf(timelineZoom);const next=TIMELINE_ZOOM_LEVELS[Math.max(0,Math.min(TIMELINE_ZOOM_LEVELS.length-1,index+direction))];const windowSize=next>1?duration/next:duration;setTimelineZoom(next);setTimelineWindowStart(next===1?0:Math.max(0,Math.min(duration-windowSize,current-windowSize/2)))};const panTimeline=(direction:number)=>setTimelineWindowStart(Math.max(0,Math.min(timelineMaxStart,timelineStart+direction*timelineWindow*.8)));
  const openTrim=()=>{setTrimStart(0);setTrimEnd(duration);setTrimMessage("");setTrimOpen(true)};
  const saveTrim=async()=>{if(!videoId||trimEnd-trimStart<.25)return;if(!window.confirm(`Manter somente ${playerTime(trimStart)} até ${playerTime(trimEnd)} (${playerTime(trimEnd-trimStart)})? O arquivo original será substituído.`))return;video.current?.pause();setTrimming(true);setTrimMessage("");try{const result=await api.trimVideo(videoId,trimStart,trimEnd);setDuration(result.duration_seconds);setCurrent(0);setTrimOpen(false);setMediaRevision(Date.now());setTrimMessage("Corte salvo. A análise anterior foi limpa para evitar resultados incorretos.");onMarkersChanged?.()}catch(error){setTrimMessage(error instanceof Error?error.message:"Não foi possível salvar o corte")}finally{setTrimming(false)}};
  const mediaSrc=`${src}${src.includes("?")?"&":"?"}v=${mediaRevision}`;
  return <div className="custom-video-player">
    <div className="custom-video-stage" ref={stage}>
      <video ref={video} src={mediaSrc} muted={audioTracks.length>0} preload="metadata" onLoadedMetadata={event=>{setDuration(event.currentTarget.duration);if(!trimEnd)setTrimEnd(event.currentTarget.duration)}} onTimeUpdate={event=>{if(!scrubbing.current)updateClock(event.currentTarget.currentTime);syncTrackAudio(event.currentTarget.currentTime)}} onPlay={()=>{setPlaying(true);playTrackAudio()}} onPlaying={playTrackAudio} onPause={()=>{setPlaying(false);pauseTrackAudio()}} onWaiting={pauseTrackAudio} onSeeked={event=>{if(!event.currentTarget.paused)playTrackAudio()}} onEnded={()=>{setPlaying(false);pauseTrackAudio();setCurrent(duration);onEnded?.()}} onClick={()=>{const player=video.current!;player.paused?player.play():player.pause()}}/>
      {!!activeCaptions.length&&<div className="custom-caption">{activeCaptions.map((segment,index)=>{
        const who=segment.speaker?speakers.find(speaker=>speaker.id===segment.speaker)?.label:"";
        const events=(segment.events||[]).map(event=>`[${event}]`).join(" ");
        return <p key={`${segment.source||"mix"}-${segment.start}-${index}`} className={`caption-line ${segment.source||"mix"}`}>
          {CAPTION_LABELS[segment.source||""]&&<b className={`source-badge ${segment.source}`}>{CAPTION_LABELS[segment.source||""]}</b>}
          <span>{who&&<i>{who}: </i>}{segment.text}{events&&` ${events}`}</span>
        </p>;
      })}</div>}
      <div className="playback-hud">
        <button onClick={()=>{const player=video.current!;player.paused?player.play():player.pause()}}>{playing?"❚❚":"▶"}</button>
        <span>{playerTime(current)}</span>
        {timelineZoom>1&&<button className="timeline-pan" title="Trecho anterior da timeline" onClick={()=>panTimeline(-1)}>‹</button>}
        <div className="playback-timeline">
          <input aria-label={`Posição do vídeo · zoom ${timelineZoom}× · trecho ${playerTime(timelineStart)} a ${playerTime(timelineEnd)}`} type="range" min={timelineStart} max={timelineEnd||0} step="0.1" value={timelineValue} onPointerDown={event=>{event.currentTarget.setPointerCapture(event.pointerId);scrubbing.current=true;setScrubTime(timelineValue)}} onChange={event=>{const value=+event.target.value;if(scrubbing.current)setScrubTime(value);else commitTimelineSeek(value)}} onPointerUp={event=>{const value=+event.currentTarget.value;scrubbing.current=false;setScrubTime(null);commitTimelineSeek(value)}} onPointerCancel={()=>{scrubbing.current=false;setScrubTime(null)}}/>
          {trimOpen&&timelineWindow>0&&trimEnd>=timelineStart&&trimStart<=timelineEnd&&<span className="trim-selection" style={{left:`${Math.max(0,(Math.max(trimStart,timelineStart)-timelineStart)/timelineWindow*100)}%`,width:`${Math.max(0,Math.min(trimEnd,timelineEnd)-Math.max(trimStart,timelineStart))/timelineWindow*100}%`}}/>}
          {visibleMarkers.map(marker=><button key={marker.id} className="timeline-marker" title={`${playerTime(marker.offset_seconds)} · ${marker.title||"Destaque sem título"}`} style={{left:`${timelineWindow?Math.min(100,(marker.offset_seconds-timelineStart)/timelineWindow*100):0}%`}} onClick={()=>seek(Math.max(0,marker.offset_seconds-preroll))}>◆</button>)}
        </div>
        {timelineZoom>1&&<button className="timeline-pan" title="Próximo trecho da timeline" onClick={()=>panTimeline(1)}>›</button>}
        <span>{playerTime(duration)}</span>
        <div className="timeline-zoom" aria-label="Zoom da timeline"><button disabled={timelineZoom===1} title="Reduzir zoom da timeline" onClick={()=>changeTimelineZoom(-1)}>−</button><span>{timelineZoom}×</span><button disabled={timelineZoom===TIMELINE_ZOOM_LEVELS[TIMELINE_ZOOM_LEVELS.length-1]} title="Ampliar timeline" onClick={()=>changeTimelineZoom(1)}>+</button></div>
        {videoId&&<button title="Adicionar destaque (F8)" onClick={addMarker}>◆</button>}
        {videoId&&<button className={trimOpen?"active":""} title="Cortar este clipe" onClick={()=>trimOpen?setTrimOpen(false):openTrim()}>✂</button>}
        <button className={captions?"active":""} disabled={!segments.length} title="Ativar ou desativar legendas" onClick={()=>setCaptions(value=>!value)}>CC</button>
        <button className={fullscreen?"active":""} title={fullscreen?"Sair da tela cheia":"Tela cheia"} aria-label={fullscreen?"Sair da tela cheia":"Tela cheia"} onClick={()=>fullscreen?document.exitFullscreen():stage.current?.requestFullscreen()}>{fullscreen?"⤢":"⛶"}</button>
      </div>
    </div>
    {trimOpen&&<section className="video-trimmer"><header><div><strong>Cortar clipe</strong><span>Arraste as bordas ou use o tempo atual para definir o trecho final.</span></div><output>{playerTime(trimStart)} — {playerTime(trimEnd)} · {playerTime(Math.max(0,trimEnd-trimStart))}</output></header><div className="trim-range"><label><span>Início · {playerTime(trimStart)}</span><input aria-label="Início do corte" type="range" min="0" max={Math.max(0,trimEnd-.25)} step=".05" value={trimStart} onChange={event=>{const value=+event.target.value;setTrimStart(value);commitTimelineSeek(value)}}/></label><label><span>Fim · {playerTime(trimEnd)}</span><input aria-label="Fim do corte" type="range" min={Math.min(duration,trimStart+.25)} max={duration} step=".05" value={trimEnd} onChange={event=>{const value=+event.target.value;setTrimEnd(value);commitTimelineSeek(value)}}/></label></div><footer><button onClick={()=>setTrimStart(Math.min(current,trimEnd-.25))}>Início no tempo atual</button><button onClick={()=>setTrimEnd(Math.max(current,trimStart+.25))}>Fim no tempo atual</button><button className="ghost" disabled={trimming} onClick={()=>setTrimOpen(false)}>Cancelar</button><button className="primary" disabled={trimming||trimEnd-trimStart<.25||(trimStart<=.05&&trimEnd>=duration-.05)} onClick={saveTrim}>{trimming?"Salvando corte…":"Salvar corte"}</button></footer></section>}
    {trimMessage&&<div className="trim-message">{trimMessage}</div>}
    {(audioTracksPreparing||audioTracksManual)&&<div className="video-audio-mixer video-audio-status"><div><strong>Faixas de áudio</strong><span>{audioTracksPreparing?"Preparando em segundo plano · reproduzindo a mixagem original":"Faixas ainda não preparadas · usando a mixagem original"}</span></div>{audioTracksPreparing?<button onClick={()=>{if(mediaPath&&audioTrackJobId)void api.cancelVideoAudioTracks(mediaPath,audioTrackJobId).catch(()=>{});setCancelledAudioPath(mediaPath||null);setManualAudioPath(null);setAudioTracksPreparing(false);setAudioTracksManual(true)}}>Abortar preparação</button>:<button onClick={()=>{setCancelledAudioPath(null);setManualAudioPath(mediaPath||null)}}>Preparar faixas independentes</button>}</div>}
    {!!audioTracks.length&&<div className="video-audio-mixer"><div><strong>Faixas de áudio</strong><span>Volumes independentes</span></div>{audioTracks.map(track=><label key={track.track}><audio ref={node=>{if(node)audioNodes.current.set(track.track,node);else audioNodes.current.delete(track.track)}} src={track.url} preload="metadata" onLoadedMetadata={event=>{const node=event.currentTarget;const seconds=video.current?.currentTime||0;node.currentTime=seconds;node.volume=trackVolumes[track.track]??1;if(video.current&&!video.current.paused)void node.play().catch(()=>{})}} onError={()=>setAudioTracks([])}/><span>{track.label}</span><input aria-label={`Volume de ${track.label}`} type="range" min="0" max="1" step="0.01" value={trackVolumes[track.track]??1} onChange={event=>{const value=+event.target.value;const node=audioNodes.current.get(track.track);if(node)node.volume=value;setTrackVolumes(volumes=>({...volumes,[track.track]:value}))}}/><output>{Math.round((trackVolumes[track.track]??1)*100)}%</output></label>)}</div>}
    {!!markers.length&&<div className="marker-list"><strong>Destaques</strong>{markers.map(marker=><div key={marker.id}><button onClick={()=>seek(Math.max(0,marker.offset_seconds-preroll))}><time>{videoTime(marker.offset_seconds)}</time><span>{marker.title||"Sem título · a IA nomeará na análise"}{marker.ai_generated?" ✦":""}</span></button><button title="Editar título" onClick={async()=>{const title=prompt("Título do destaque",marker.title);if(title!==null){await api.updateVideoMarker(marker.id,title);onMarkersChanged?.()}}}>✎</button><button title="Excluir" onClick={async()=>{await api.deleteVideoMarker(marker.id);onMarkersChanged?.()}}>×</button></div>)}</div>}
    {!!chapters.length&&<div className="chapter-strip"><div><strong>Capítulos</strong><span>Reproduza o trecho ou abra a leitura completa</span></div>{chapters.map((chapter,index)=><article key={`${chapter.time}-${index}`} className={current>=chapterStart(chapter)&&(index===chapters.length-1||current<chapterStart(chapters[index+1]))?"active":""}><button className="chapter-seek" title="Reproduzir a partir deste capítulo" onClick={()=>seek(chapterStart(chapter))}><time>{chapter.time}</time><strong>{chapter.title}</strong><span>{chapter.summary}</span></button><button className="chapter-read" onClick={()=>setReadingChapter(index)}>Ler capítulo</button></article>)}</div>}
    {!chapters.length&&<div className="chapter-strip empty-chapters">A análise ainda não gerou capítulos para este vídeo.</div>}
    {readingChapter!==null&&chapters[readingChapter]&&<ChapterReader chapter={chapters[readingChapter]} speakers={chapterSpeakers} onRename={renameSpeaker} onClose={()=>setReadingChapter(null)} onPlay={()=>{seek(chapterStart(chapters[readingChapter]));setReadingChapter(null)}}/>}
    {chapters.some(chapter=>chapter.web_sources?.length)&&<details className="web-sources"><summary>Fontes pesquisadas na internet</summary>{chapters.flatMap(chapter=>chapter.web_sources||[]).filter((source,index,all)=>all.findIndex(item=>item.url===source.url)===index).map(source=><a href={source.url} target="_blank" rel="noreferrer" key={source.url}><strong>{source.title||source.url}</strong><span>{source.snippet}</span></a>)}</details>}
  </div>
}

function VideoViewer({file,preroll,hotkey,onRefresh,onClose}:{file:VideoFile;preroll:number;hotkey:string;onRefresh:()=>void;onClose:()=>void}){
  const label=(speaker?:string)=>file.speakers?.find(item=>item.id===speaker)?.label||"";
  const rename=async(speaker:{id:string;label:string})=>{if(!file.id)return;const next=prompt("Nome deste locutor",speaker.label);if(next?.trim()){await api.renameVideoSpeaker(file.id,speaker.id,next.trim());onRefresh()}};
  return <div className="overlay video-viewer" onMouseDown={onClose}><section onMouseDown={event=>event.stopPropagation()}><header><div><span className="eyebrow">{file.available?"Playback analisado":"Análise preservada"}</span><h2>{file.title||file.name}</h2></div><button className="icon-button" onClick={onClose}>×</button></header><div className="video-viewer-body">{file.available?<CustomVideoPlayer src={file.url} mediaPath={file.path} title={file.title||file.name} chapters={file.chapters} segments={file.transcript_segments} speakers={file.speakers} markers={file.markers} videoId={file.id} preroll={preroll} hotkey={hotkey} onMarkersChanged={onRefresh}/>:<div className="missing-video viewer-missing">Arquivo removido — a análise continua disponível.</div>}{file.available&&!!file.speakers?.length&&<section className="speaker-panel"><h3>Vozes identificadas</h3><p>Ouça uma amostra e atribua nomes manualmente.</p><div>{file.speakers.map(speaker=><article key={speaker.id}><strong>{speaker.label}</strong>{file.id&&<AudioPlayer src={`/api/videos/${file.id}/speakers/${speaker.id}/sample`}/>}<button className="ghost" onClick={()=>rename(speaker)}>Renomear</button></article>)}</div></section>}{!!file.audio_events?.length&&<section className="audio-events"><h3>Eventos acústicos</h3><div>{file.audio_events.map((event,index)=><button disabled={!file.available} key={`${event.start}-${event.event}-${index}`} onClick={()=>{const target=document.querySelector<HTMLVideoElement>(".video-viewer video");if(target){target.currentTime=event.start;target.play()}}}><time>{videoTime(event.start)}</time><strong>[{event.event}]</strong><span>{Math.round(event.confidence*100)}%</span></button>)}</div></section>}{file.description&&<section className="viewer-description"><h3>Análise da IA</h3><p>{file.description}</p></section>}{file.transcript&&<details className="video-transcript"><summary>Transcrição por locutor</summary>{file.transcript_segments?.length?<div className="transcript-segments">{file.transcript_segments.map((segment,index)=><button disabled={!file.available} key={`${segment.start}-${index}`} onClick={()=>{const target=document.querySelector<HTMLVideoElement>(".video-viewer video");if(target){target.currentTime=segment.start;target.play()}}}><time>{videoTime(segment.start)}</time><span>{label(segment.speaker)&&<strong>{label(segment.speaker)}: </strong>}{segment.text} {(segment.events||[]).map(event=><em key={event}>[{event}]</em>)}</span></button>)}</div>:<p>{file.transcript}</p>}</details>}</div></section></div>
}

function VideoSettingsTab({tab,settings,patterns,models,ollamaOnline,busy,advanced=false,onSettings,onPatterns}:{tab:"ai"|"video";settings:VideoSettings;patterns:string;models:OllamaModel[];ollamaOnline:boolean;busy:boolean;advanced?:boolean;onSettings:(settings:VideoSettings)=>void;onPatterns:(value:string)=>void}){
  const profile=(value:VideoSettings["analysis_profile"])=>{const values={fast:[10,24],balanced:[5,48],detailed:[2,80],custom:[settings.scan_interval_seconds,settings.max_keyframes]}[value];onSettings({...settings,analysis_profile:value,scan_interval_seconds:values[0],max_keyframes:values[1]})};
  const choices=(current:string,visionOnly=false)=>{const available=models.filter(model=>!visionOnly||!model.capabilities.length||model.capabilities.includes("vision"));return available.some(model=>model.name===current)?available:[{name:current,size:0,modified_at:"",capabilities:[]},...available]};
  const modelLabel=(model:OllamaModel)=>`${model.name}${model.size?` · ${(model.size/1024**3).toFixed(1)} GB`:" · não encontrado"}`;
  const [testingWindow,setTestingWindow]=useState(false);
  const [windowTest,setWindowTest]=useState<{title?:string;window_class?:string;matched?:boolean;matched_pattern?:string;message?:string}|null>(null);
  const testWindow=async()=>{setTestingWindow(true);setWindowTest({message:"Troque para o jogo ou aplicativo que deseja testar…"});await new Promise(resolve=>setTimeout(resolve,3000));try{setWindowTest(await api.testVideoWindow(patterns.split("\n").map(value=>value.trim()).filter(Boolean)))}catch(error){setWindowTest({message:error instanceof Error?error.message:"Falha ao testar a janela"})}finally{setTestingWindow(false)}};
  if(tab==="ai")return <section className="ai-settings settings-tab-card"><h3>Modelos e recursos de IA</h3><div className="form-grid ai-model-selectors"><label><span>IA visual · telas e vídeo</span><select value={settings.vision_model} onChange={event=>onSettings({...settings,vision_model:event.target.value})}>{choices(settings.vision_model,true).map(model=><option key={model.name} value={model.name}>{modelLabel(model)}</option>)}</select></label><label><span>IA de texto · sínteses e resumos</span><select value={settings.text_model} onChange={event=>onSettings({...settings,text_model:event.target.value})}>{choices(settings.text_model).map(model=><option key={model.name} value={model.name}>{modelLabel(model)}</option>)}</select></label></div><small className={`ollama-status ${ollamaOnline?"online":"offline"}`}>{ollamaOnline?`${models.length} modelos instalados no Ollama`:"Ollama indisponível; mantendo os modelos já configurados"}</small><label className="check"><input type="checkbox" checked={settings.thinking_enabled} onChange={event=>onSettings({...settings,thinking_enabled:event.target.checked})}/><span><strong>Raciocínio do modelo</strong><small>Permite análise interna mais longa; aumenta o tempo e o uso de memória.</small></span></label><label className="check"><input type="checkbox" checked={settings.web_search_enabled} onChange={event=>onSettings({...settings,web_search_enabled:event.target.checked})}/><span><strong>Pesquisa adaptativa na internet</strong><small>Pesquisa jogos, missões, itens e mecânicas quando houver dúvidas.</small></span></label>{settings.web_search_enabled&&<div className="form-grid"><label><span>Endereço do SearXNG</span><input value={settings.searxng_url} onChange={event=>onSettings({...settings,searxng_url:event.target.value})}/></label><label><span>Teto de segurança por vídeo</span><input type="number" min="5" max="500" value={settings.web_search_safety_limit} onChange={event=>onSettings({...settings,web_search_safety_limit:+event.target.value})}/></label></div>}</section>;
  return <><section className="settings-group"><div className="settings-group-title"><span className="eyebrow">Gravação seletiva</span><h3>Captura e análise de vídeo</h3></div><div className="form-grid"><label><span>Gravador</span><select value={settings.enabled?"on":"off"} onChange={event=>onSettings({...settings,enabled:event.target.value==="on"})}><option value="on">Ativado</option><option value="off">Desativado</option></select></label><label><span>Modo de captura</span><select value={settings.capture_mode} onChange={event=>onSettings({...settings,capture_mode:event.target.value as VideoSettings["capture_mode"]})}><option value="continuous">Gravação contínua</option><option value="clips">Clipes · Replay Buffer</option></select></label><label><span>FPS</span><input type="number" min="1" max="60" value={settings.fps} onChange={event=>onSettings({...settings,fps:+event.target.value})}/></label><label><span>Parar após sair do jogo (s)</span><input type="number" min="0" max="3600" value={settings.focus_grace_seconds} onChange={event=>onSettings({...settings,focus_grace_seconds:+event.target.value})}/></label>{settings.capture_mode==="continuous"?<><label><span>Modo de arquivo</span><select value={settings.segment_seconds===0?"session":"segments"} onChange={event=>onSettings({...settings,segment_seconds:event.target.value==="session"?0:60})}><option value="session">Um arquivo por sessão</option><option value="segments">Dividir em segmentos</option></select></label><label><span>Segmento (segundos)</span><input type="number" min="10" disabled={settings.segment_seconds===0} value={settings.segment_seconds||60} onChange={event=>onSettings({...settings,segment_seconds:+event.target.value})}/></label></>:<label><span>Duração do clipe (segundos)</span><input type="number" min="10" max="300" value={settings.replay_seconds} onChange={event=>onSettings({...settings,replay_seconds:+event.target.value})}/></label>}<label><span>Frames básicos para IA</span><input type="number" min="2" max="16" value={settings.sample_frames} onChange={event=>onSettings({...settings,sample_frames:+event.target.value})}/></label><label><span>Perfil da análise</span><select value={settings.analysis_profile} onChange={event=>profile(event.target.value as VideoSettings["analysis_profile"])}><option value="fast">Rápida · 10s</option><option value="balanced">Equilibrada · 5s</option><option value="detailed">Detalhada · 2s</option><option value="custom">Personalizada</option></select></label><label><span>Intervalo da IA (s)</span><input type="number" min=".5" max="30" step=".5" disabled={settings.analysis_profile!=="custom"} value={settings.scan_interval_seconds} onChange={event=>onSettings({...settings,scan_interval_seconds:+event.target.value})}/></label><label><span>Máximo de keyframes</span><input type="number" min="8" max="160" disabled={settings.analysis_profile!=="custom"} value={settings.max_keyframes} onChange={event=>onSettings({...settings,max_keyframes:+event.target.value})}/></label></div>{settings.capture_mode==="continuous"&&<label className="check"><input type="checkbox" checked={settings.pause_other_captures} onChange={event=>onSettings({...settings,pause_other_captures:event.target.checked})}/><span>Pausar prints e áudio durante a gravação</span></label>}<label className="check"><input type="checkbox" checked={settings.delete_after_description} onChange={event=>onSettings({...settings,delete_after_description:event.target.checked})}/><span>Excluir o original depois da análise, exceto clips preservados</span></label></section><section className="marker-settings"><h3>{settings.capture_mode==="clips"?"Salvar clipe":"Destaques da gameplay"}</h3><div className="form-grid"><label><span>Atalho</span><input value={settings.marker_hotkey} onChange={event=>onSettings({...settings,marker_hotkey:event.target.value})}/></label>{settings.capture_mode==="continuous"&&<label><span>Voltar antes do evento (s)</span><input type="number" min="0" max="120" value={settings.marker_preroll_seconds} onChange={event=>onSettings({...settings,marker_preroll_seconds:+event.target.value})}/></label>}</div><p>{settings.capture_mode==="clips"?`Ao pressionar ${settings.marker_hotkey||"F8"}, o OBS salva os últimos ${settings.replay_seconds}s e toca uma confirmação. Os clipes são agrupados por sessão.`:"O atalho adiciona um marcador e toca uma confirmação. O player usa o pré-roll configurado."}</p></section><section className="marker-settings"><h3>HUD de gravação</h3><label className="check"><input type="checkbox" checked={settings.hud_enabled} onChange={event=>onSettings({...settings,hud_enabled:event.target.checked})}/><span><strong>Mostrar a HUD durante a gravação</strong><small>Uma faixa com o tempo, os medidores de microfone e Discord, e avisos quando a captura não engata.</small></span></label>{settings.hud_enabled&&<><div className="form-grid"><label><span>Onde aparecer</span><select value={settings.hud_placement} onChange={event=>onSettings({...settings,hud_placement:event.target.value as VideoSettings["hud_placement"]})}><option value="second">No outro monitor</option><option value="game">Sobre o jogo</option><option value="both">Nos dois</option></select></label><label><span>Canto</span><select value={settings.hud_corner} onChange={event=>onSettings({...settings,hud_corner:event.target.value as VideoSettings["hud_corner"]})}><option value="top-right">Superior direito</option><option value="top-left">Superior esquerdo</option><option value="bottom-right">Inferior direito</option><option value="bottom-left">Inferior esquerdo</option></select></label><label><span>Atalho para alternar modo</span><input value={settings.hud_hotkey} onChange={event=>onSettings({...settings,hud_hotkey:event.target.value})}/></label></div><label className="check"><input type="checkbox" checked={settings.hud_sound} onChange={event=>onSettings({...settings,hud_sound:event.target.checked})}/><span>Avisar com som quando a captura falhar</span></label><p>{settings.hud_placement==="game"?"Jogos em tela cheia exclusiva podem esconder a HUD — é limitação do Windows, não do Lume. Se ela sumir, use “No outro monitor”; o aviso sonoro chega de qualquer jeito.":"O atalho alterna entre Compacto, Expandido e Oculto. No modo Oculto, avisos e animações de clip ou marcador continuam aparecendo."}</p></>}</section>{advanced&&<div className="video-advanced-panel"><label className="video-pattern-field"><span>Apps e jogos monitorados · um por linha</span><textarea value={patterns} onChange={event=>onPatterns(event.target.value)} placeholder={'steam_app_[0-9]+\ngamescope\nNome do jogo'}/></label><section className={`window-test ${windowTest?.matched?"matched":windowTest?"unmatched":""}`}><div><strong>Testar detecção da janela</strong><span>Clique e troque para o jogo em até 3 segundos. Nenhuma gravação será iniciada.</span></div><button className="secondary" disabled={testingWindow||busy} onClick={testWindow}>{testingWindow?"Aguardando…":"Testar janela"}</button>{windowTest&&<p>{windowTest.message||(windowTest.matched?`Gravaria · regra: ${windowTest.matched_pattern}`:"Não gravaria · nenhuma regra correspondeu")} {windowTest.title&&<small>{windowTest.title} · {windowTest.window_class}</small>}</p>}</section></div>}</>;
}

function AppCaptureRules({settings,patterns,advanced,onAdvanced,onSettings,onPatterns}:{settings:VideoSettings;patterns:string;advanced:boolean;onAdvanced:(value:boolean)=>void;onSettings:(settings:VideoSettings)=>void;onPatterns:(patterns:string)=>void}){
  const [adding,setAdding]=useState(false);const [message,setMessage]=useState("");
  const [candidate,setCandidate]=useState<{executable:string;pattern:string;title?:string;windowClass?:string}|null>(null);
  const rules=patterns.split("\n").map(value=>value.trim()).filter(Boolean);
  const update=(pattern:string,field:"mode"|"fps"|"geometry"|"source",value:string|number)=>{
    if(field==="mode")onSettings({...settings,pattern_modes:{...(settings.pattern_modes||{}),[pattern]:value as "continuous"|"clips"}});
    if(field==="fps")onSettings({...settings,pattern_fps:{...(settings.pattern_fps||{}),[pattern]:Math.max(1,Math.min(60,+value))}});
    if(field==="geometry")onSettings({...settings,pattern_geometry:{...(settings.pattern_geometry||{}),[pattern]:String(value)}});
    if(field==="source")onSettings({...settings,pattern_sources:{...(settings.pattern_sources||{}),[pattern]:value as "game"|"window"}});
  };
  const remove=(pattern:string)=>{const next={...settings,pattern_modes:{...(settings.pattern_modes||{})},pattern_fps:{...(settings.pattern_fps||{})},pattern_geometry:{...(settings.pattern_geometry||{})},pattern_sources:{...(settings.pattern_sources||{})}};delete next.pattern_modes[pattern];delete next.pattern_fps[pattern];delete next.pattern_geometry[pattern];delete next.pattern_sources[pattern];onSettings(next);onPatterns(rules.filter(item=>item!==pattern).join("\n"))};
  const addCurrent=async()=>{setAdding(true);setMessage("Troque para o jogo que deseja adicionar…");await new Promise(resolve=>setTimeout(resolve,3000));try{const found=await api.testVideoWindow([]);const executable=found.executable||found.window_class;if(!executable)throw new Error("Não foi possível descobrir o executável");const escaped=executable.replace(/[.*+?^${}()|[\]\\]/g,"\\$&");const pattern=`exe:^${escaped}$`;if(rules.includes(pattern)){setMessage(`${executable} já está na lista`);return}setMessage("");setCandidate({executable,pattern,title:found.title,windowClass:found.window_class})}catch(error){setMessage(error instanceof Error?error.message:"Falha ao detectar aplicativo")}finally{setAdding(false)}};
  const confirmCandidate=()=>{if(!candidate)return;const {executable,pattern}=candidate;onPatterns([...rules,pattern].join("\n"));onSettings({...settings,pattern_modes:{...(settings.pattern_modes||{}),[pattern]:settings.capture_mode},pattern_fps:{...(settings.pattern_fps||{}),[pattern]:settings.fps},pattern_geometry:{...(settings.pattern_geometry||{}),[pattern]:settings.geometry},pattern_sources:{...(settings.pattern_sources||{}),[pattern]:executable.toLowerCase()==="robloxplayerbeta.exe"?"window":"game"}});setCandidate(null);setMessage(`${executable} adicionado. Escolha o perfil abaixo.`)};
  const nameOf=(pattern:string)=>pattern.replace(/^exe:\^?/i,"").replace(/\\([.!+])/g,"$1").replace(/\$$/,"")||pattern;
  const resolutions=Array.from(new Set([settings.geometry,"2560x1440","1920x1080","1600x900","1280x720"]));
  return <>
    <div className="video-advanced-toggle"><button type="button" className="ghost" aria-pressed={advanced} onClick={()=>onAdvanced(!advanced)}>{advanced?"Ocultar modo avançado":"⚙ Modo avançado"}</button></div>
    <section className="app-capture-rules settings-group">
      <div className="settings-group-title"><div><span className="eyebrow">Comportamento por jogo</span><h3>Aplicativos monitorados</h3><p>Adicione a janela aberta e escolha o modo, a qualidade e o método de captura.</p></div><button className="secondary" disabled={adding} onClick={addCurrent}>{adding?"Troque para o jogo…":"+ Aplicativo aberto"}</button></div>
      {message&&<p className="app-rule-message">{message}</p>}
      {rules.length?<div className="app-rule-list">{rules.map(pattern=>{
        const mode=settings.pattern_modes?.[pattern]||settings.capture_mode;
        const fps=settings.pattern_fps?.[pattern]||settings.fps;
        const geometry=settings.pattern_geometry?.[pattern]||settings.geometry;
        const source=settings.pattern_sources?.[pattern]||(pattern.toLowerCase().includes("robloxplayerbeta")?"window":"game");
        return <article key={pattern}>
          <div className="app-rule-name"><strong>{nameOf(pattern)}</strong><code>{pattern}</code></div>
          <label><span>Captura</span><select value={mode} onChange={event=>update(pattern,"mode",event.target.value)}><option value="continuous">Vídeo completo</option><option value="clips">Somente clipes · F8</option></select></label>
          <label><span>Resolução</span><select value={geometry} onChange={event=>update(pattern,"geometry",event.target.value)}>{resolutions.map(value=><option value={value} key={value}>{value}</option>)}</select></label>
          <label><span>FPS</span><input type="number" min="1" max="60" value={fps} onChange={event=>update(pattern,"fps",event.target.value)}/></label>
          <button type="button" className={`capture-fallback ${source==="window"?"active":""}`} aria-pressed={source==="window"} title="Use se a Captura de jogo do OBS produzir vídeo preto" onClick={()=>update(pattern,"source",source==="window"?"game":"window")}><b>{source==="window"?"✓":""}</b><span>Fallback janela</span></button>
          <button className="delete-video" title="Remover aplicativo" onClick={()=>remove(pattern)}>Remover</button>
        </article>
      })}</div>:<p className="help">Nenhum aplicativo monitorado. Abra um jogo e use “Aplicativo aberto”.</p>}
    </section>
    {candidate&&<Modal title="É este aplicativo que você quer adicionar?" className="app-confirm-modal" onClose={()=>setCandidate(null)}><div className="app-confirm-candidate"><span>{candidate.executable.slice(0,1).toUpperCase()}</span><div><strong>{candidate.title||candidate.executable}</strong><code>{candidate.executable}</code>{candidate.windowClass&&candidate.windowClass!==candidate.executable&&<small>{candidate.windowClass}</small>}</div></div><p className="help">A gravação será ativada somente quando este executável estiver em foco. Depois você poderá ativar o fallback de janela se a Captura de jogo produzir vídeo preto.</p><footer><button className="ghost" onClick={()=>setCandidate(null)}>Não, cancelar</button><button className="primary" onClick={confirmCandidate}>Sim, adicionar</button></footer></Modal>}
  </>
}

function AIInspector({job}:{job:QueueJob}){
  const metrics=job.ai_metrics||{};
  return <details className="ai-inspector" open={!!job.ai_thinking}><summary><span className="ai-live-dot"/>Inspetor da IA <em>{metrics.model||"aguardando modelo"}</em></summary><div className="ai-inspector-meta">{metrics.status==="generating"?"Gerando agora…":"Última geração concluída"}{!!metrics.generated_tokens&&` · ${metrics.generated_tokens} tokens gerados`}{!!metrics.total_duration_ms&&` · ${(metrics.total_duration_ms/1000).toFixed(1)}s`}</div>{job.ai_thinking?<section><h4>Raciocínio</h4><pre>{job.ai_thinking}</pre></section>:<section className="ai-inspector-empty">O raciocínio aparecerá aqui quando o modelo começar a gerar e a opção estiver ativada.</section>}{job.ai_content&&<section><h4>Resposta estruturada em andamento</h4><pre>{job.ai_content}</pre></section>}</details>
}

function SummaryView({ summary, onOpenMedia }: { summary: DaySummary|null; onOpenMedia:(item:SummaryMediaItem)=>void }) {
  if (!summary) return <EmptyView view="resumo"/>;
  const data = summary.data || {};
  const maxMinutes = Math.max(1, ...(data.app_blocks || []).map(x => x.minutes));
  const mediaGroups=[
    ["screens","Prints relevantes"],["videos","Vídeos relevantes"],["sessions","Sessões relevantes"],["audio","Trechos de áudio relevantes"],
  ] as const;
  return <div className="summary-view"><section><h2>✦ O que você fez</h2><div className="narrative">{summary.narrative.split(/\n+/).map((p,i)=><p key={i}>{p}</p>)}</div></section>
    {!!data.app_blocks?.length && <section><h2>Blocos por app</h2><div className="app-bars">{data.app_blocks.map(block => <div key={block.app}><span>{block.app}</span><i><b style={{width:`${Math.min(100,block.minutes/maxMinutes*100)}%`}}/></i><em>{block.minutes}m</em></div>)}</div></section>}
    {!!data.tasks?.length && <section><h2>Tarefas detectadas</h2><div className="tasks">{data.tasks.map((task,i)=><div key={i}><b>{task.done?"✓":""}</b><span>{task.text}</span><small>{task.source}</small></div>)}</div></section>}
    {!!data.meetings?.length && <section><h2>Reuniões transcritas</h2><div className="meeting-grid">{data.meetings.map((meeting,i)=><article key={i}><span className="tag audio">Áudio</span><small>{meeting.time}</small><h3>{meeting.title}</h3><p>{meeting.snippet}</p></article>)}</div></section>}
    {mediaGroups.map(([key,label])=>!!data.relevant_media?.[key]?.length&&<section className="summary-media-section" key={key}><h2>{label}</h2><div className="summary-media-grid">{data.relevant_media[key].map(item=>{const openable=item.kind==="video"||item.kind==="session";return <article key={`${item.kind}-${item.id}`} className={openable?"summary-media-openable":undefined} role={openable?"button":undefined} tabIndex={openable?0:undefined} onClick={openable?()=>onOpenMedia(item):undefined} onKeyDown={openable?event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();onOpenMedia(item)}}:undefined}>{item.url&&item.kind==="screen"?<img src={item.url} loading="lazy"/>:item.url&&item.kind==="video"?<video src={item.url} preload="none"/>:<div className={`summary-media-icon ${item.kind}`}>{item.kind==="audio"?"▮▮":item.kind==="session"?"▣":"●"}</div>}<div><span className="kept-badge">◆ Manter</span><time>{new Date(item.captured_at).toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"})}</time><h3>{item.title}</h3><p>{item.reason}</p><small>{item.available?item.app||"Mídia local":"Arquivo bruto removido · análise preservada"}</small>{openable&&<span className="summary-media-open">{item.available?"Abrir player ▸":"Abrir análise ▸"}</span>}</div></article>})}</div></section>)}
  </div>;
}

function ActivitiesView({items,running,onGenerate,onOpen}:{items:ActivitySession[];running:boolean;onGenerate:()=>void;onOpen:(frame:ActivitySession["key_frames"][number])=>void}){
  return <div className="visual-activities"><div className="activity-overview"><div><strong>{items.length} sessões visuais</strong><span>{items.reduce((total,item)=>total+item.source_count,0)} prints analisados em sequência</span></div><button className="primary" disabled={running} onClick={onGenerate}>{running?"Analisando sequências…":items.length?"Reanalisar atividades":"Analisar atividades"}</button></div>{items.map(item=>{const start=new Date(item.started_at);const end=new Date(item.ended_at);const minutes=Math.max(0,Math.round((end.getTime()-start.getTime())/60000));return <article className="visual-activity" key={item.id}><header><div className="activity-app-icon">{item.app.slice(0,1).toUpperCase()}</div><div><span>{item.app}</span><h2>{item.title}</h2><small>{start.toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"})}–{end.toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"})} · {item.source_count} prints{minutes?` · cerca de ${minutes} min`:""}</small></div></header>{item.key_frames.length>0&&<div className="activity-filmstrip">{item.key_frames.map(frame=><button key={frame.id} onClick={()=>onOpen(frame)}>{frame.url?<img src={frame.url} loading="lazy"/>:<span>Imagem removida</span>}<time>{new Date(frame.captured_at).toLocaleTimeString("pt-BR",{hour:"2-digit",minute:"2-digit"})}</time>{frame.preserved&&<b>◆</b>}</button>)}</div>}<div className="activity-story">{item.narrative.split(/\n+/).filter(Boolean).map((paragraph,index)=><p key={index}>{paragraph}</p>)}</div>{item.events.length>0&&<details><summary>Linha de acontecimentos · {item.events.length}</summary><ol>{item.events.map((event,index)=><li key={index}>{event}</li>)}</ol></details>}<div className="tags">{item.tags.map(tag=><span key={tag}>{tag}</span>)}</div></article>})}{!items.length&&!running&&<div className="result">Gere a análise para transformar os prints do dia em sessões contínuas por aplicativo.</div>}</div>
}

function Modal({ title, onClose, children, className="" }: { title: string; onClose: () => void; children: React.ReactNode; className?:string }) {
  return <div className="overlay" onMouseDown={onClose}><section className={`modal ${className}`} onMouseDown={e => e.stopPropagation()}>
    <header><div><span className="eyebrow">Configuração local</span><h2>{title}</h2></div><button className="icon-button" onClick={onClose}>×</button></header>
    {children}
  </section></div>;
}

function VideoThumbnail({path,title,onOpen}:{path:string;title:string;onOpen:()=>void}){
  const [failed,setFailed]=useState(false);
  return <button type="button" className="video-thumbnail" onClick={onOpen} aria-label={`Abrir player: ${title}`}>
    <span><b>▶</b><small>Abrir player</small></span>
    {!failed&&<img src={`/api/video-thumbnail?path=${encodeURIComponent(path)}`} alt="" loading="lazy" onError={()=>setFailed(true)}/>}
  </button>
}

function SessionCard({session,busy,selecting=false,selected=false,onToggle=()=>{},onOpen,onAnalyze,onDelete,onContext}:{session:VideoSession;busy:boolean;selecting?:boolean;selected?:boolean;onToggle?:()=>void;onOpen:(session:VideoSession)=>void;onAnalyze:(session:VideoSession)=>void;onDelete:(session:VideoSession)=>void;onContext:(session:VideoSession)=>void}){
  const preview=session.clips.find(clip=>clip.available);
  const running=["queued","processing"].includes(session.status);
  const selectable=!running&&session.clip_count>0;
  return <article className={`session-card ${selecting?"video-selectable":""} ${selected?"video-selected":""}`}>
    {selecting&&selectable&&<button type="button" className="video-selection-hitbox" aria-pressed={selected} aria-label={`${selected?"Remover":"Selecionar"} sessão ${session.name}`} onClick={onToggle}/>} 
    {selecting&&<div className="video-selection-indicator"><b>{selectable&&selected?"✓":""}</b><span>{selectable?(selected?"Selecionada":"Selecionar sessão"):running?"Em processamento":"Sem clipes"}</span></div>}
    {preview?<VideoThumbnail path={preview.path} title={session.name} onOpen={()=>onOpen(session)}/>:<div className={`session-cover${session.clip_count?" session-cover-openable":""}`} role={session.clip_count?"button":undefined} tabIndex={session.clip_count?0:undefined} onClick={session.clip_count&&!selecting?()=>onOpen(session):undefined} onKeyDown={session.clip_count&&!selecting?event=>{if(event.key==="Enter"||event.key===" "){event.preventDefault();onOpen(session)}}:undefined}><b>{session.clip_count}</b><span>{session.clip_count?"clipes · análise preservada":"clipes na sessão"}</span></div>}
    <span className="session-badge">Sessão completa</span>
    <h3>{session.name}</h3>
    <small>{new Date(session.captured_at).toLocaleString("pt-BR")} · {session.clip_count} clipes · {session.duration_seconds>0?`duração total ${sessionDuration(session.duration_seconds)}`:"duração indisponível"} · {bytes(session.bytes)} · {session.status}</small>
    {session.summary&&<p className="session-summary-preview">{session.summary}</p>}
    {!selecting&&<div className="session-actions"><button className="open-video" disabled={!session.clip_count} onClick={()=>onOpen(session)}>{preview?"Abrir sessão":"Abrir análise"}</button><button className="ghost" onClick={()=>onContext(session)}>Contexto</button><button className="secondary" disabled={busy||running||!session.clip_count} onClick={()=>onAnalyze(session)}>{running?`${session.stage} · ${session.progress}%`:"Analisar sessão completa"}</button><button className="delete-video" disabled={busy||running} onClick={()=>onDelete(session)}>Excluir</button></div>}
  </article>
}

function VideoCard({file,busy,selecting,selected,onToggle,onContext,onDate,onOpen,onAnalyze,onPreserve,onDelete,onVideoRef,onSeek}:{file:VideoFile;busy:boolean;selecting:boolean;selected:boolean;onToggle:()=>void;onContext:()=>void;onDate:()=>void;onOpen:()=>void;onAnalyze:()=>void;onPreserve:()=>void;onDelete:()=>void;onVideoRef:(element:HTMLVideoElement|null)=>void;onSeek:(seconds:number)=>void}){
  return <article className={`${selecting?"video-selectable":""} ${selected?"video-selected":""}`}>
    {selecting&&file.available&&<button type="button" className="video-selection-hitbox" aria-pressed={selected} aria-label={`${selected?"Remover":"Selecionar"} ${file.title||file.name}`} onClick={onToggle}/>} 
    {selecting&&<div className="video-selection-indicator"><b>{file.available&&selected?"✓":""}</b><span>{file.available?(selected?"Selecionado":"Selecionar"):"Indisponível"}</span></div>}
    {file.available?<VideoThumbnail path={file.path} title={file.title||file.name} onOpen={onOpen}/>:<div className="missing-video standalone-missing"><strong>Arquivo removido</strong><span>A análise foi preservada</span></div>}
    <h3>{file.title||file.name}</h3>
    <small>{new Date(file.captured_at||file.modified_at).toLocaleString("pt-BR")} · {bytes(file.bytes)} · {file.status}</small>
    {file.game&&<div className="video-tags"><span className="tag game">▣ {file.game}</span></div>}
    {file.description&&<p className="video-description">{file.description}</p>}
    {!!file.chapters?.length&&<details className="video-chapters"><summary>{file.chapters.length} capítulos analisados</summary>{file.chapters.map(chapter=><section key={chapter.time}><time>{chapter.time}</time><h4>{chapter.title}</h4><p>{chapter.summary}</p>{!!chapter.events?.length&&<ul>{chapter.events.map((event,index)=><li key={index}>{event}</li>)}</ul>}</section>)}</details>}
    {file.transcript&&<details className="video-transcript"><summary>Transcrição sincronizada</summary>{file.transcript_segments?.length?<div className="transcript-segments">{file.transcript_segments.map((segment,index)=><button disabled={!file.available} key={`${segment.start}-${index}`} onClick={()=>onSeek(segment.start)}><time>{`${Math.floor(segment.start/60)}:${Math.floor(segment.start%60).toString().padStart(2,"0")}`}</time><span>{segment.text}</span></button>)}</div>:<p>{file.transcript}</p>}</details>}
    {file.error&&<p className="video-error">{file.error}</p>}
    {!selecting&&<div><button className="open-video" onClick={onOpen}>{file.available?"Abrir player":"Abrir análise"}</button><button className="ghost" onClick={onContext}>Contexto</button><button className="ghost" onClick={onDate}>Data</button><button className="secondary" disabled={!file.available||busy||["queued","processing"].includes(file.status)} onClick={onAnalyze}>{["queued","processing"].includes(file.status)?`${file.stage||"Analisando"} · ${file.progress||0}%`:"Analisar áudio + vídeo"}</button><button className="ghost" disabled={!file.available||busy} onClick={onPreserve}>Preservar clip</button><button className="delete-video" disabled={busy||["queued","processing"].includes(file.status)} onClick={onDelete}>{file.available?"Excluir":"Excluir análise"}</button></div>}
  </article>
}

function SessionViewer({session,preroll,hotkey,onRefresh,onEditDate,onClose}:{session:VideoSession;preroll:number;hotkey:string;onRefresh:()=>void;onEditDate:(clip:VideoSession["clips"][number])=>void;onClose:()=>void}){
  const [active,setActive]=useState(0);const clip=session.clips[active];
  const sessionSpeakers:EditableVideoSpeaker[]=session.clips.flatMap((item,index)=>item.speakers.filter(speaker=>!speaker.fixed).map(speaker=>({...speaker,videoId:item.id,clipLabel:`Trecho ${index+1} · ${item.title||item.name}`})));
  return <div className="overlay session-viewer" onMouseDown={onClose}><section onMouseDown={event=>event.stopPropagation()}>
    <header><div><span className="session-badge">Sessão completa</span><h2>{session.name}</h2><p>{session.clip_count} clipes · {session.duration_seconds>0?`duração total ${sessionDuration(session.duration_seconds)}`:"duração indisponível"} · {bytes(session.bytes)} · {session.status}</p></div><button className="icon-button" onClick={onClose} aria-label="Fechar">×</button></header>
    <div className="session-viewer-body">
      <section className="session-analysis"><h3>Análise conjunta da IA</h3>{session.summary?<p>{session.summary}</p>:<p className="session-empty">A sessão ainda não possui uma síntese conjunta.</p>}{session.context&&<><h3>Contexto informado</h3><p>{session.context}</p></>}</section>
      {clip&&<div className="continuous-session"><div className="session-continuous-head"><strong>Reprodução contínua · trecho {active+1} de {session.clips.length}</strong><span>{new Date(clip.captured_at).toLocaleString("pt-BR")} · <button className="edit-clip-date" onClick={()=>onEditDate(clip)}>Corrigir data</button></span></div>{clip.available?<CustomVideoPlayer key={clip.id} src={clip.url} mediaPath={clip.path} title={clip.title||clip.name} chapters={clip.chapters} segments={clip.transcript_segments} speakers={clip.speakers} editableSpeakers={sessionSpeakers} markers={clip.markers} videoId={clip.id} preroll={preroll} hotkey={hotkey} onMarkersChanged={onRefresh} autoPlay={active>0} onEnded={()=>setActive(value=>Math.min(session.clips.length-1,value+1))}/>:<div className="missing-video">Arquivo removido — análise preservada abaixo.</div>}{!clip.available&&<div className="clip-preserved-analysis">{clip.description&&<><h4>Análise da IA</h4><p>{clip.description}</p></>}{!!clip.chapters?.length&&<details className="video-chapters" open><summary>{clip.chapters.length} capítulos analisados</summary>{clip.chapters.map(chapter=><section key={chapter.time}><time>{chapter.time}</time><h4>{chapter.title}</h4><p>{chapter.summary}</p>{!!chapter.events?.length&&<ul>{chapter.events.map((event,index)=><li key={index}>{event}</li>)}</ul>}</section>)}</details>}{clip.transcript&&<details className="video-transcript"><summary>Transcrição por locutor</summary>{clip.transcript_segments?.length?<div className="transcript-segments">{clip.transcript_segments.map((segment,index)=><div key={`${segment.start}-${index}`}><time>{videoTime(segment.start)}</time><span>{segment.text}</span></div>)}</div>:<p>{clip.transcript}</p>}</details>}{!clip.description&&!clip.chapters?.length&&!clip.transcript&&<p className="session-empty">Este trecho não chegou a ser analisado antes de ser removido.</p>}</div>}<div className="session-piece-tabs">{session.clips.map((item,index)=><button className={index===active?"active":""} onClick={()=>setActive(index)} key={item.id}>{index+1}. {item.title||item.name}</button>)}</div></div>}
    </div>
  </section></div>
}

function JoinVideosModal({files,selected,onSelected,busy,onJoin,onClose}:{files:VideoFile[];selected:number[];onSelected:(ids:number[])=>void;busy:boolean;onJoin:(name:string)=>Promise<void>;onClose:()=>void}){
  const [query,setQuery]=useState("");const [name,setName]=useState(`Sessão ${new Date().toLocaleDateString("pt-BR")}`);
  const visible=files.filter(file=>!query.trim()||`${file.title} ${file.name} ${file.game}`.toLowerCase().includes(query.toLowerCase()));
  const toggle=(id:number)=>onSelected(selected.includes(id)?selected.filter(item=>item!==id):[...selected,id]);
  return <div className="overlay" onMouseDown={onClose}><section className="modal media-picker-modal" onMouseDown={event=>event.stopPropagation()}><header><div><span className="eyebrow">Organizar gameplay</span><h2>Unir vídeos em uma sessão</h2></div><button className="icon-button" onClick={onClose}>×</button></header><p className="help">Selecione os trechos na ordem em que aconteceram. A reprodução será contínua e os arquivos originais serão preservados.</p><div className="picker-fields"><label><span>Nome da sessão</span><input value={name} onChange={event=>setName(event.target.value)}/></label><label><span>Buscar vídeos</span><input autoFocus value={query} onChange={event=>setQuery(event.target.value)} placeholder="Jogo, título ou arquivo…"/></label></div><div className="media-picker-list">{visible.map(file=><button key={file.id} className={selected.includes(file.id!)?"selected":""} onClick={()=>toggle(file.id!)}><b>{selected.indexOf(file.id!)+1||""}</b><span><strong>{file.title||file.name}</strong><small>{file.game||new Date(file.modified_at).toLocaleString("pt-BR")}</small></span><em>{selected.includes(file.id!)?"Selecionado":"Selecionar"}</em></button>)}</div><footer><span className="picker-count">{selected.length} selecionado{selected.length===1?"":"s"}</span><button className="ghost" onClick={onClose}>Cancelar</button><button className="primary" disabled={busy||selected.length<2||!name.trim()} onClick={()=>onJoin(name.trim())}>Criar sessão</button></footer></section></div>
}

function ContextPickerModal({sessions,files,target,draft,busy,onTarget,onDraft,onSave,onClose}:{sessions:VideoSession[];files:VideoFile[];target:string;draft:string;busy:boolean;onTarget:(value:string)=>void;onDraft:(value:string)=>void;onSave:()=>Promise<void>;onClose:()=>void}){
  const [query,setQuery]=useState("");const choices=[...sessions.map(item=>({key:`session:${item.id}`,kind:"Sessão",title:item.name,detail:`${item.clip_count} trechos`,context:item.context})),...files.filter(item=>item.id&&!item.session_id).map(item=>({key:`video:${item.id}`,kind:"Vídeo",title:item.title||item.name,detail:item.game||new Date(item.modified_at).toLocaleString("pt-BR"),context:item.context}))];const visible=choices.filter(item=>!query.trim()||`${item.title} ${item.detail}`.toLowerCase().includes(query.toLowerCase()));const chosen=choices.find(item=>item.key===target);
  return <div className="overlay" onMouseDown={onClose}><section className="modal context-picker-modal" onMouseDown={event=>event.stopPropagation()}><header><div><span className="eyebrow">Informações para a IA</span><h2>Contexto da gameplay</h2></div><button className="icon-button" onClick={onClose}>×</button></header>{!chosen?<><p className="help">Escolha diretamente a sessão ou vídeo que deseja contextualizar.</p><input className="picker-search" autoFocus value={query} onChange={event=>setQuery(event.target.value)} placeholder="Buscar sessão, jogo ou vídeo…"/><div className="context-choice-list">{visible.map(item=><button key={item.key} onClick={()=>onTarget(item.key)}><span className="tag">{item.kind}</span><div><strong>{item.title}</strong><small>{item.detail}{item.context?" · contexto já preenchido":""}</small></div><b>›</b></button>)}</div></>:<><button className="back-target" onClick={()=>onTarget("")}>‹ Escolher outro vídeo ou sessão</button><div className="context-target-title"><span className="tag">{chosen.kind}</span><strong>{chosen.title}</strong></div><textarea className="context-draft" autoFocus value={draft} onChange={event=>onDraft(event.target.value)} placeholder="Ex.: Eu estava jogando com… Nosso objetivo era…"/><p className="help">Este texto será usado pela IA na análise de áudio e vídeo.</p><footer><button className="ghost" onClick={onClose}>Cancelar</button><button className="primary" disabled={busy} onClick={async()=>{await onSave();onClose()}}>Salvar contexto</button></footer></>}</section></div>
}

function App() {
  const [view, setView] = useState<View>(()=>{
    const saved=sessionStorage.getItem("lume-active-view");
    return saved&&saved in labels?saved as View:"busca";
  });
  const [panel, setPanel] = useState<Panel>(null);
  const [mobileNavOpen,setMobileNavOpen]=useState(false);
  const [capturaTab, setCapturaTab] = useState<CapturaTab>("fila");
  const [palette, setPalette] = useState(false);
  const [paletteQuery, setPaletteQuery] = useState("");
  const [paletteItems, setPaletteItems] = useState<Capture[]>([]);
  const [status, setStatus] = useState<Status | null>(null);
  const [statusClock,setStatusClock]=useState(()=>Date.now());
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [savingSettings,setSavingSettings]=useState(false);
  const [pendingVideoActions,setPendingVideoActions]=useState<Set<string>>(()=>new Set());
  const [refreshing,setRefreshing]=useState(false);
  const [settings, setSettings] = useState<ScreenSettings | null>(null);
  const [cleanupSettings,setCleanupSettings]=useState<CleanupSettings|null>(null);
  const [patterns, setPatterns] = useState("");
  const [testResult, setTestResult] = useState<string>("");
  const [shots, setShots] = useState<string[]>([]);
  const [items, setItems] = useState<Capture[]>([]);
  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<"all"|"screen"|"audio">("all");
  const [summary, setSummary] = useState<DaySummary|null>(null);
  const [selectedDay,setSelectedDay]=useState(()=>new Date().toLocaleDateString("sv-SE"));
  const [memoryDays,setMemoryDays]=useState<{day:string;count:number}[]>([]);
  const [pipeline, setPipeline] = useState<{counts:Record<string,number>;running:boolean}|null>(null);
  const [rawFiles, setRawFiles] = useState<RawFile[]>([]);
  const [fileKind, setFileKind] = useState<"screen"|"audio">("screen");
  const [selectedScreenPaths,setSelectedScreenPaths]=useState<string[]>([]);
  const [screenSequenceResult,setScreenSequenceResult]=useState<ScreenSequenceResult|null>(null);
  const [activeScreenSequenceJob,setActiveScreenSequenceJob]=useState<number|null>(null);
  const [lightbox, setLightbox] = useState<{url:string|null;name:string;text:string;model:string;kind?:Capture["kind"];capture?:Capture}|null>(null);
  const [showLightboxVoices,setShowLightboxVoices]=useState(false);
  const [voiceProfiles,setVoiceProfiles]=useState<VoiceIdentity[]|null>(null);
  const [fileTotal, setFileTotal] = useState(0);
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [queueCounts,setQueueCounts]=useState<QueueCounts|null>(null);
  const [queueSpeed,setQueueSpeed]=useState<QueueSpeed|null>(null);
  const [queueRunning, setQueueRunning] = useState(false);
  const [queueWorkerRunning,setQueueWorkerRunning]=useState(false);
  const [queuePaused,setQueuePaused]=useState(false);
  const [queueJobs, setQueueJobs] = useState<QueueJob[]>([]);
  const [hours, setHours] = useState<HourSummary[]>([]);
  const [activities,setActivities]=useState<ActivitySession[]>([]);
  const [hourSources, setHourSources] = useState<{hour:string;count:number}[]>([]);
  const [hourlyRunning, setHourlyRunning] = useState(false);
  const [selectedHour, setSelectedHour] = useState<{summary:HourSummary|null;key:string;items:Capture[]}|null>(null);
  const [schedule, setSchedule] = useState<ScheduleSettings|null>(null);
  const [storage,setStorage]=useState<StorageSettings|null>(null);
  const [storageRoot,setStorageRoot]=useState("");
  const [videoSettings,setVideoSettings]=useState<VideoSettings|null>(null);
  const [ollamaModels,setOllamaModels]=useState<OllamaModel[]>([]);
  const [ollamaOnline,setOllamaOnline]=useState(false);
  const [videoFiles,setVideoFiles]=useState<VideoFile[]>([]);
  const [videoGame,setVideoGame]=useState("");
  const [videoSessions,setVideoSessions]=useState<VideoSession[]>([]);
  const [openSessionId,setOpenSessionId]=useState<number|null>(null);
  const [openVideoPath,setOpenVideoPath]=useState<string|null>(null);
  const [settingsTab,setSettingsTab]=useState<"capture"|"storage"|"ai"|"video">("capture");
  const [videoAdvanced,setVideoAdvanced]=useState(false);
  const [videoPatterns,setVideoPatterns]=useState("");
  const [uploadProgress,setUploadProgress]=useState<number|null>(null);
  const [dragActive,setDragActive]=useState(false);
  const [contextTarget,setContextTarget]=useState("");
  const [contextDraft,setContextDraft]=useState("");
  const [selectedVideoPaths,setSelectedVideoPaths]=useState<string[]>([]);
  const [selectedSessionIds,setSelectedSessionIds]=useState<number[]>([]);
  const [videoSort,setVideoSort]=useState<"newest"|"oldest">("newest");
  const [joinMode,setJoinMode]=useState(false);
  const [contextModalOpen,setContextModalOpen]=useState(false);
  const [screenChangeTest,setScreenChangeTest]=useState<{token?:string;change_percent?:number;threshold_percent?:number;would_capture?:boolean;message?:string}|null>(null);
  const videoUploadRef=useRef<HTMLInputElement>(null);
  const folderUploadRef=useRef<HTMLInputElement>(null);
  const screenSelectionAnchor=useRef<string|null>(null);
  const mediaPlaybackOpen=openVideoPath!==null||openSessionId!==null||lightbox?.kind==="audio";
  const isDayView=dayViews.includes(view);
  const lastLensRef=useRef<View>("resumo");
  if(isDayView)lastLensRef.current=view;
  const navigate=(next:View)=>{setView(next);setMobileNavOpen(false)};
  const queueCount=(pipeline?.counts.pending||0)+(pipeline?.counts.processing||0)+queueJobs.filter(job=>job.status!=="error").length;
  const dayIndex=memoryDays.findIndex(item=>item.day===selectedDay);
  const stepDay=(direction:1|-1)=>{const next=memoryDays[dayIndex+direction];if(next)setSelectedDay(next.day)};
  const openQueuePanel=()=>{setView("captura");setCapturaTab("fila")};
  const openDiagnostics=()=>{setView("captura");setCapturaTab("diagnostico");setMobileNavOpen(false)};
  const dateValue=(value?:string)=>new Date(value||0).getTime()||0;
  const looseVideos=videoFiles.filter(file=>!file.session_id).map(item=>({item,game:canonicalGameName(item.game,item.game_source==="window")}));
  const groupedSessions=videoSessions.map(item=>({item,game:sessionGameName(item)}));
  const gameStats=[...looseVideos.map(({item,game})=>({game,clips:1,bytes:item.bytes})),...groupedSessions.map(({item,game})=>({game,clips:item.clip_count,bytes:item.bytes}))]
    .filter(item=>item.game)
    .reduce((stats,item)=>{const found=stats.find(entry=>entry.game===item.game);if(found){found.clips+=item.clips;found.bytes+=item.bytes}else stats.push({...item});return stats},[] as {game:string;clips:number;bytes:number}[])
    .sort((a,b)=>a.game.localeCompare(b.game,"pt-BR"));
  const visibleVideoFiles=looseVideos.filter(({game})=>!videoGame||game===videoGame).map(({item})=>item).sort((a,b)=>(dateValue(b.captured_at)-dateValue(a.captured_at))*(videoSort==="newest"?1:-1));
  const visibleVideoSessions=groupedSessions.filter(({game})=>joinMode||!videoGame||game===videoGame).map(({item})=>item);
  const videoLibraryItems=[...visibleVideoFiles.map(file=>({kind:"video" as const,date:file.captured_at,item:file})),...visibleVideoSessions.map(session=>({kind:"session" as const,date:session.captured_at,item:session}))].sort((a,b)=>(dateValue(b.date)-dateValue(a.date))*(videoSort==="newest"?1:-1));
  const videoRefs=useRef<Record<string,HTMLVideoElement|null>>({});
  const queueWasRunning=useRef(false);
  const statusRefreshInFlight=useRef<Promise<void>|null>(null);
  const dragDepth=useRef(0);
  const applyQueueResult=(result:PipelineQueue)=>{
    setQueue(result.items);setQueueJobs(result.jobs);setQueueRunning(result.running);
    setQueueWorkerRunning(result.worker_running===true);setQueuePaused(result.paused===true);
    setQueueCounts(result.counts||null);setQueueSpeed(result.speed||null);
  };
  const refreshVideos=()=>Promise.all([api.videos(),api.videoSessions()]).then(([files,sessions])=>{setVideoFiles(files.items);setVideoSessions(sessions.items)}).catch(err=>setError((err as Error).message));
  const openSummaryMedia=(item:SummaryMediaItem)=>{
    if(item.kind==="session"){
      if(videoSessions.some(session=>session.id===item.id))setOpenSessionId(item.id);
      else setError("A sessão de vídeo não está mais na biblioteca.");
      return;
    }
    if(item.kind==="video"){
      const match=videoFiles.find(file=>file.id===item.id)||videoFiles.find(file=>file.path===item.source_path);
      if(match)setOpenVideoPath(match.path);
      else setError("A análise deste vídeo não está mais na biblioteca.");
    }
  };
  const withVideoAction=async(key:string,action:()=>Promise<void>)=>{
    if(pendingVideoActions.has(key))return;
    setPendingVideoActions(current=>new Set(current).add(key));
    try{await action()}finally{setPendingVideoActions(current=>{const next=new Set(current);next.delete(key);return next})}
  };

  const refresh = () => {
    if(statusRefreshInFlight.current)return statusRefreshInFlight.current;
    const request=api.status().then(next=>{
      setStatus(next); setSettings(current=>current||next.settings); setError("");
    }).catch(err=>setError((err as Error).message)).finally(()=>{
      if(statusRefreshInFlight.current===request)statusRefreshInFlight.current=null;
    });
    statusRefreshInFlight.current=request;
    return request;
  };

  const refreshMemory = async () => {
    try {
      const [found, job] = await Promise.all([
        query.trim() ? api.search(query, kind) : api.captures(kind),
        api.pipelineStatus(),
      ]);
      const fallbackDays=[...new Set(found.items.map(item=>item.captured_at.slice(0,10)).filter(Boolean))]
        .sort((a,b)=>b.localeCompare(a)).map(day=>({day,count:found.items.filter(item=>item.captured_at.startsWith(day)).length}));
      const available=await api.days().catch(()=>({items:fallbackDays}));
      const dayKey=available.items.some(item=>item.day===selectedDay)?selectedDay:(available.items[0]?.day||selectedDay);
      const [day,timeline,activityResult]=await Promise.all([api.summary(dayKey),api.timeline(dayKey),api.activities(dayKey)]);
      setMemoryDays(available.items);if(dayKey!==selectedDay)setSelectedDay(dayKey);
      setItems(groupCaptures(found.items)); setSummary(day.summary); setPipeline(job);setHours(timeline.hours);setHourSources(timeline.source_hours);setHourlyRunning(timeline.running||activityResult.running);setActivities(activityResult.items);
    } catch (err) { setError((err as Error).message); }
  };

  const refreshCurrentView=async()=>{
    setRefreshing(true);
    try{
      if(view==="videos"){
        const [nextStatus,files,sessions,nextVideoSettings,ollama]=await Promise.all([
          api.status(),api.videos(),api.videoSessions(),api.videoSettings(),api.ollamaModels(),
        ]);
        setStatus(nextStatus);setSettings(current=>current||nextStatus.settings);
        setVideoFiles(files.items);setVideoSessions(sessions.items);setVideoSettings(nextVideoSettings);
        setVideoPatterns(nextVideoSettings.patterns.join("\n"));setOllamaModels(ollama.models);setOllamaOnline(ollama.online);
        setError("");
      }else{
        await Promise.all([refresh(),refreshMemory()]);
      }
    }catch(err){setError((err as Error).message)}finally{setRefreshing(false)}
  };

  useEffect(()=>{sessionStorage.setItem("lume-active-view",view)},[view]);
  useEffect(() => {
    void refresh();
    const timer=setInterval(()=>void refresh(),1000);
    const refreshNow=()=>void refresh();
    window.addEventListener("focus",refreshNow);
    document.addEventListener("visibilitychange",refreshNow);
    return()=>{clearInterval(timer);window.removeEventListener("focus",refreshNow);document.removeEventListener("visibilitychange",refreshNow)};
  },[]);
  useEffect(()=>{if(!status?.video.recording)return;setStatusClock(Date.now());const timer=setInterval(()=>setStatusClock(Date.now()),1000);return()=>clearInterval(timer)},[status?.video.recording,status?.video.started_at]);
  useEffect(() => { const timer=setTimeout(refreshMemory,250); return()=>clearTimeout(timer); }, [query,kind,selectedDay]);
  useEffect(() => {
    if (view!=="captura"||capturaTab!=="fila") return;
    const load=()=>api.pipelineQueue(selectedDay).then(result=>{if(queueWasRunning.current&&!result.running)void refreshMemory();queueWasRunning.current=result.running;applyQueueResult(result)}).catch(err=>setError((err as Error).message));
    load(); const timer=setInterval(load,2000); return()=>clearInterval(timer);
  }, [view,capturaTab,selectedDay]);
  useEffect(()=>{
    const handler=(event:KeyboardEvent)=>{
      if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==="k"){event.preventDefault();setPalette(open=>!open)}
      if(event.key==="Escape")setPalette(false);
    };
    window.addEventListener("keydown",handler);
    return()=>window.removeEventListener("keydown",handler);
  },[]);
  useEffect(()=>{
    if(!palette)return;
    const term=paletteQuery.trim();
    if(!term){setPaletteItems([]);return}
    const timer=setTimeout(()=>{api.search(term,"all").then(result=>setPaletteItems(groupCaptures(result.items).slice(0,6))).catch(()=>{})},200);
    return()=>clearTimeout(timer);
  },[palette,paletteQuery]);
  useEffect(() => {
    if (view!=="timeline"||!hourlyRunning) return;
    const timer=setInterval(()=>api.timeline(selectedDay).then(result=>{setHours(result.hours);setHourSources(result.source_hours);setHourlyRunning(result.running)}).catch(()=>{}),3000);
    return()=>clearInterval(timer);
  },[view,hourlyRunning,selectedDay]);
  useEffect(()=>{if(view!=="videos")return;Promise.all([api.videoSettings(),api.ollamaModels()]).then(([settings,ollama])=>{setVideoSettings(settings);setVideoPatterns(settings.patterns.join("\n"));setOllamaModels(ollama.models);setOllamaOnline(ollama.online)}).catch(err=>setError((err as Error).message))},[view]);
  useEffect(()=>{if(view!=="videos"||mediaPlaybackOpen)return;let active=true;const load=()=>Promise.all([api.videos(),api.videoSessions()]).then(([files,sessions])=>{if(active){setVideoFiles(files.items);setVideoSessions(sessions.items)}}).catch(err=>{if(active)setError((err as Error).message)});load();const timer=setInterval(load,3000);return()=>{active=false;clearInterval(timer)}},[view,mediaPlaybackOpen]);
  useEffect(()=>{folderUploadRef.current?.setAttribute("webkitdirectory","")},[]);
  useEffect(()=>{if(view!=="videos")return;const prevent=(event:DragEvent)=>event.preventDefault();window.addEventListener("dragover",prevent);window.addEventListener("drop",prevent);return()=>{window.removeEventListener("dragover",prevent);window.removeEventListener("drop",prevent)}},[view]);

  const toggleCapture = async () => {
    if (!status) return;
    setBusy(true);
    try { await api.capture(status.capturing ? "pause" : "resume"); await refresh(); }
    catch (err) { setError((err as Error).message); }
    finally { setBusy(false); }
  };

  const openPrivacy = async () => {
    setMobileNavOpen(false);
    setPanel("privacy");
    try { const data = await api.sensitive(); setPatterns(data.patterns.join("\n")); }
    catch (err) { setError((err as Error).message); }
  };

  const openSettings = async () => {
    setMobileNavOpen(false);
    setSettingsTab(view==="videos"?"video":"capture");
    setPanel("settings");
    try {
      const [nextSchedule,nextStorage,nextVideo,nextCleanup,ollama]=await Promise.all([api.schedule(),api.storage(),api.videoSettings(),api.cleanupSettings(),api.ollamaModels()]);
      setSchedule(nextSchedule);setStorage(nextStorage);setStorageRoot(nextStorage.root);setVideoSettings(nextVideo);setCleanupSettings(nextCleanup);setVideoPatterns(nextVideo.patterns.join("\n"));setOllamaModels(ollama.models);setOllamaOnline(ollama.online);
    } catch(err){setError((err as Error).message)}
  };

  const saveAllSettings = async () => {
    if (!settings||!schedule||!storage||!videoSettings||!cleanupSettings||savingSettings) return;setSavingSettings(true);
    try {
      const [,savedSchedule,savedVideo,savedCleanup]=await Promise.all([
        api.saveSettings(settings),
        api.saveSchedule({time:schedule.time,enabled:schedule.enabled}),
        api.saveVideoSettings({...videoSettings,patterns:videoPatterns.split("\n").map(value=>value.trim()).filter(Boolean)}),
        api.saveCleanupSettings(cleanupSettings),
      ]);
      setSchedule(savedSchedule);setVideoSettings(savedVideo);setCleanupSettings(savedCleanup);
      const savedStorage=await api.saveStorage(storageRoot);setStorage(savedStorage);
      setTestResult(savedStorage.restart_required?"Local salvo. O Lume está reiniciando para usar o novo disco.":"Configurações salvas");
      setPanel(null);if(!savedStorage.restart_required)void refresh();
    }
    catch(err){setError((err as Error).message)} finally{setSavingSettings(false)}
  };

  const saveCaptureMode = async (capture_mode:VideoSettings["capture_mode"]) => {
    if(!videoSettings)return;setBusy(true);
    try{
      const saved=await api.saveVideoSettings({...videoSettings,capture_mode,patterns:videoPatterns.split("\n").map(value=>value.trim()).filter(Boolean)});
      setVideoSettings(saved);setTestResult(capture_mode==="clips"?`Modo clipes ativado · F8 salva os últimos ${saved.replay_seconds}s`:"Gravação contínua ativada");
    }catch(err){setError((err as Error).message)}finally{setBusy(false)}
  };

  const startScreenChangeTest = async () => {
    if(!settings)return;setBusy(true);
    try{const result=await api.startScreenChangeTest(settings.change_threshold_percent);setScreenChangeTest({token:result.token,threshold_percent:result.threshold_percent,message:"Referência guardada. Faça uma mudança na tela e compare."})}
    catch(err){setScreenChangeTest({message:(err as Error).message})}finally{setBusy(false)}
  };

  const compareScreenChangeTest = async () => {
    if(!settings||!screenChangeTest?.token)return;setBusy(true);
    try{const result=await api.compareScreenChangeTest(screenChangeTest.token,settings.change_threshold_percent);setScreenChangeTest(result)}
    catch(err){setScreenChangeTest({message:(err as Error).message})}finally{setBusy(false)}
  };

  const savePrivacy = async () => {
    setBusy(true);
    try { await api.saveSensitive(patterns.split("\n")); setPanel(null); }
    catch (err) { setError((err as Error).message); }
    finally { setBusy(false); }
  };

  const testAudio = async () => {
    setBusy(true); setTestResult("Gravando 5 segundos…");
    try { const r = await api.testAudio(); setTestResult(`Áudio válido · ${r.format.sample_rate} Hz · mono · média ${r.mean_db} dB · pico ${r.max_db} dB${r.silent ? " · SILÊNCIO" : ""}`); }
    catch (err) { setTestResult(`Falhou: ${(err as Error).message}`); }
    finally { setBusy(false); }
  };

  const testScreen = async () => {
    setBusy(true); setTestResult("Capturando e validando privacidade…"); setShots([]);
    try {
      const r = await api.testScreen();
      if (r.privacy_skip) setTestResult(`Captura bloqueada corretamente · ${r.message || "janela sensível"}`);
      else { setTestResult(`${r.paths?.length || 0} monitores capturados`); setShots(r.paths || []); }
    } catch (err) { setTestResult(`Falhou: ${(err as Error).message}`); }
    finally { setBusy(false); }
  };

  const captureLabel = status?.settings.capture_mode === "change"
    ? `mudança · ${status.settings.change_poll_seconds}s`
    : `a cada ${status?.settings.interval_seconds || 20}s`;
  const automaticCapturePause = !!status && (status.capture_paused_by_video || status.capture_paused_by_idle);
  const automaticPauseTitle = status?.capture_paused_by_video ? "Pausada pelo vídeo" : "Pausada por inatividade";
  const automaticPauseNote = status?.capture_paused_by_video
    ? "Áudio e telas retomam automaticamente quando o gravador seletivo encerrar."
    : `Áudio e telas retomam ao detectar atividade. O vídeo seletivo continua disponível.`;

  const runPipeline = async () => {
    setBusy(true);
    try { const result=await api.enqueueUnprocessed(); const queueResult=await api.pipelineQueue(selectedDay);applyQueueResult(queueResult);queueWasRunning.current=true;const restored=result.requeued?` · ${result.requeued} anteriormente removidos restaurados`:"";const videos=result.queued.video+result.queued.session?` · ${result.queued.video} vídeos e ${result.queued.session} sessões`:"";const missing=result.missing?` · ${result.missing} registros sem arquivo ignorados`:"";setTestResult(`${result.queued.total} pendentes de todos os dias na fila · ${result.discovered.audio+result.discovered.screen} arquivos novos encontrados${videos}${restored}${missing}`);openQueuePanel();setTimeout(refreshMemory,1000); }
    catch(err){setError((err as Error).message)} finally{setBusy(false)}
  };

  const forceSummary = async () => {
    setBusy(true);
    try { await api.generateSummary(selectedDay);queueWasRunning.current=true;setQueueJobs([{id:`daily-summary-${selectedDay}`,kind:"summary",stage:`Resumindo períodos e consolidando ${new Date(`${selectedDay}T12:00:00`).toLocaleDateString("pt-BR")} com Qwen`}]);setQueueRunning(true);setTestResult("Resumo detalhado iniciado em segundo plano");openQueuePanel(); }
    catch(err){setError((err as Error).message)} finally{setBusy(false)}
  };

  const deleteUnkeptRawMedia = async () => {
    if(!window.confirm("Executar agora a limpeza segura? Somente prints e áudios já processados, consolidados nos resumos e não marcados como Manter serão apagados. Vídeos e sessões não serão alterados."))return;
    setBusy(true);
    try{
      const result=await api.deleteUnkeptRawMedia();
      await refresh();
      setTestResult(`${result.deleted_total} arquivo${result.deleted_total===1?" removido":"s removidos"} (${result.deleted.screen} prints, ${result.deleted.audio} áudios) · ${bytes(result.deleted_bytes)} liberados · ${result.skipped.preserved} protegidos · ${result.skipped.not_ready} aguardando consolidação`);
    }catch(err){setError((err as Error).message)}finally{setBusy(false)}
  };

  const stopPipeline = async () => {
    setBusy(true);
    try { await api.cancelPipeline(selectedDay); const result=await api.pipelineQueue(selectedDay);applyQueueResult(result);await refreshMemory(); }
    catch(err){setError((err as Error).message)} finally{setBusy(false)}
  };

  const pausePipeline = async () => {
    setBusy(true);
    try { const paused=await api.pausePipeline();const result=await api.pipelineQueue(selectedDay);applyQueueResult(result);setTestResult(`${paused.requeued} item${paused.requeued===1?"":"s"} preservado${paused.requeued===1?"":"s"} para retomada`);await refreshMemory(); }
    catch(err){setError((err as Error).message)} finally{setBusy(false)}
  };

  const resumePipeline = async () => {
    setBusy(true);
    try { await api.resumePipeline();const result=await api.pipelineQueue(selectedDay);applyQueueResult(result);queueWasRunning.current=true;setTestResult("Processamento retomado do ponto seguro da fila"); }
    catch(err){setError((err as Error).message)} finally{setBusy(false)}
  };

  const removeQueueItem = async (item:QueueItem) => {
    setBusy(true);
    try { await api.cancelQueueItem(item.id); const result=await api.pipelineQueue(selectedDay);applyQueueResult(result);await refreshMemory(); }
    catch(err){setError((err as Error).message)} finally{setBusy(false)}
  };

  const deleteMemoryItem = async (item:Capture) => {
    const ids=item.capture_ids?.length?item.capture_ids:[item.id];
    const label=ids.length>1?`este item e seus ${ids.length} arquivos associados`:"este item";
    if(!window.confirm(`Excluir permanentemente ${label}? Essa ação apaga o arquivo original do disco.`)) return;
    setBusy(true);
    try {
      for(const id of ids) await api.deleteCapture(id);
      setItems(current=>current.filter(candidate=>candidate.id!==item.id));
      setSelectedHour(current=>current?{...current,items:current.items.filter(candidate=>candidate.id!==item.id)}:current);
      setLightbox(null);
      await Promise.all([refreshMemory(),refresh()]);
    } catch(err){setError((err as Error).message)}
    finally{setBusy(false)}
  };

  const clearQueue = async () => {
    if (!window.confirm("Cancelar todos os itens da fila? Os arquivos originais serão preservados.")) return;
    setBusy(true);
    try { const result=await api.cancelEntireQueue();setQueue([]);setQueueJobs([]);setQueueCounts({audio:0,screen:0,processing:0,pending:0,error:0,total:0});setQueueSpeed(current=>current&&{...current,eta_seconds:null});setQueueRunning(false);setQueueWorkerRunning(false);setQueuePaused(false);setTestResult(`${result.cancelled} itens removidos da fila`);await refreshMemory(); }
    catch(err){setError((err as Error).message)} finally{setBusy(false)}
  };
  const unloadOllama=async()=>{
    if(!window.confirm("Forçar o descarregamento de todos os modelos do Ollama? Uma análise em andamento pode falhar e precisar ser retomada."))return;
    setBusy(true);
    try{const result=await api.unloadOllama();setTestResult(result.unloaded?`${result.unloaded} modelo${result.unloaded===1?"":"s"} descarregado${result.unloaded===1?"":"s"}: ${result.models.join(", ")}`:"Nenhum modelo estava carregado")}
    catch(err){setError((err as Error).message)}finally{setBusy(false)}
  };

  const generateHours = async () => {
    setBusy(true);
    try { await api.generateTimeline(selectedDay);queueWasRunning.current=true;setQueueJobs([{id:`hourly-summary-${selectedDay}`,kind:"hourly",stage:`Analisando sequências visuais e resumos por hora de ${new Date(`${selectedDay}T12:00:00`).toLocaleDateString("pt-BR")} com Qwen`}]);setQueueRunning(true);setHourlyRunning(true);setTestResult("Análise de atividades e horas iniciada");openQueuePanel(); }
    catch(err){setError((err as Error).message)} finally{setBusy(false)}
  };

  const openHour = async (key:string, summary:HourSummary|null) => {
    setBusy(true);
    try { const found=await api.captures("all",key.slice(0,10));setSelectedHour({key,summary,items:groupCaptures(found.items).filter(item=>item.captured_at.slice(0,13)===key)}); }
    catch(err){setError((err as Error).message)} finally{setBusy(false)}
  };

  const timelineHours = hourSources.map(source=>({source,summary:hours.find(hour=>hour.hour===source.hour)||null}));

  const setAnalysisProfile=(profile:VideoSettings["analysis_profile"])=>{if(!videoSettings)return;const values={fast:[10,24],balanced:[5,48],detailed:[2,80],custom:[videoSettings.scan_interval_seconds,videoSettings.max_keyframes]}[profile];setVideoSettings({...videoSettings,analysis_profile:profile,scan_interval_seconds:values[0],max_keyframes:values[1]})};
  const analyzeVideo=async(file:VideoFile)=>withVideoAction(`video:${file.path}`,async()=>{setVideoFiles(current=>current.map(item=>item.path===file.path?{...item,status:"queued",stage:"Enfileirando",progress:0}:item));setTestResult(`Enfileirando ${file.name}…`);try{await api.processVideo(file.path);const [files,queueResult]=await Promise.all([api.videos(),api.pipelineQueue()]);setVideoFiles(files.items);applyQueueResult(queueResult);setTestResult("Análise adicionada à fila");openQueuePanel()}catch(err){void refreshVideos();setTestResult(`Falhou: ${(err as Error).message}`)}});
  const preserveVideo=async(file:VideoFile)=>{try{const result=await api.preserveVideo(file.path);setTestResult(`Clip preservado em ${result.path}`)}catch(err){setError((err as Error).message)}};
  const editVideoDate=async(file:VideoFile)=>{if(!file.id)return;const current=new Date(file.captured_at||file.modified_at);const local=new Date(current.getTime()-current.getTimezoneOffset()*60000).toISOString().slice(0,16);const value=prompt("Data e hora em que o vídeo foi gravado (AAAA-MM-DDTHH:MM)",local)?.trim();if(!value)return;const parsed=new Date(value);if(Number.isNaN(parsed.getTime())){setError("Data inválida");return}setBusy(true);try{await api.saveVideoDate(file.id,parsed.toISOString());await refreshVideos();setTestResult("Data do vídeo atualizada e sessão reordenada")}catch(err){setError((err as Error).message)}finally{setBusy(false)}};
  const editSessionClipDate=async(clip:VideoSession["clips"][number])=>{const current=new Date(clip.captured_at);const local=new Date(current.getTime()-current.getTimezoneOffset()*60000).toISOString().slice(0,16);const value=prompt("Data e hora em que este trecho foi gravado (AAAA-MM-DDTHH:MM)",local)?.trim();if(!value)return;const parsed=new Date(value);if(Number.isNaN(parsed.getTime())){setError("Data inválida");return}setBusy(true);try{await api.saveVideoDate(clip.id,parsed.toISOString());await refreshVideos();setTestResult("Data atualizada; os trechos foram reordenados cronologicamente")}catch(err){setError((err as Error).message)}finally{setBusy(false)}};
  const deleteVideo=async(file:VideoFile)=>{
    const warning=file.available?`O arquivo será apagado do disco${file.status==="done"?", junto com a análise":""}.`:"O arquivo já foi removido; somente a análise salva será excluída.";
    if(!window.confirm(`Excluir permanentemente “${file.title||file.name}”? ${warning}`))return;
    await withVideoAction(`video:${file.path}`,async()=>{try{await api.deleteVideo(file.path);setVideoFiles(current=>current.filter(item=>item.path!==file.path));setTestResult("Vídeo excluído")}
    catch(err){setError((err as Error).message)}})
  };
  const cancelVideoJob=async(job:QueueJob)=>{
    if(!job.video_id&&!job.session_id)return;setBusy(true);
    try{if(job.session_id)await api.cancelVideoSession(job.session_id);else await api.cancelVideoAnalysis(job.video_id!);const result=await api.pipelineQueue();setQueueJobs(result.jobs);setQueueRunning(result.running);setTestResult("Análise cancelada");const [files,sessions]=await Promise.all([api.videos(),api.videoSessions()]);setVideoFiles(files.items);setVideoSessions(sessions.items)}
    catch(err){setError((err as Error).message)}finally{setBusy(false)}
  };
  const importVideos=async(files:FileList|File[]|null)=>{
    if(!files?.length)return;const selected=Array.from(files).filter(file=>file.type.startsWith("video/")||/\.(mp4|mkv|webm|mov|avi|m4v)$/i.test(file.name));if(!selected.length){setError("Solte arquivos de vídeo compatíveis");return}setBusy(true);
    try{
      for(let index=0;index<selected.length;index++){
        const file=selected[index];setTestResult(`Enviando ${file.name} (${index+1} de ${selected.length})…`);setUploadProgress(0);
        await uploadVideo(file,setUploadProgress);
      }
      const refreshed=await api.videos();setVideoFiles(refreshed.items);setTestResult(`${selected.length} arquivo${selected.length===1?" importado":"s importados"} com sucesso`);
    }catch(err){setError((err as Error).message)}
    finally{setBusy(false);setUploadProgress(null);if(videoUploadRef.current)videoUploadRef.current.value=""}
  };
  const dragEnter=(event:React.DragEvent)=>{if(view!=="videos"||!event.dataTransfer.types.includes("Files"))return;event.preventDefault();dragDepth.current+=1;setDragActive(true)};
  const dragOver=(event:React.DragEvent)=>{if(view!=="videos")return;event.preventDefault();event.dataTransfer.dropEffect="copy"};
  const dragLeave=(event:React.DragEvent)=>{if(view!=="videos")return;event.preventDefault();dragDepth.current=Math.max(0,dragDepth.current-1);if(!dragDepth.current)setDragActive(false)};
  const dropVideos=(event:React.DragEvent)=>{if(view!=="videos")return;event.preventDefault();dragDepth.current=0;setDragActive(false);importVideos(Array.from(event.dataTransfer.files))};
  const importVideoFolder=async(files:FileList|null)=>{
    if(!files?.length)return;
    const ordered=Array.from(files).filter(file=>file.type.startsWith("video/")||/\.(mp4|mkv|webm|mov|avi|m4v)$/i.test(file.name)).sort((a,b)=>a.webkitRelativePath.localeCompare(b.webkitRelativePath,undefined,{numeric:true}));
    if(!ordered.length){setError("A pasta não contém vídeos compatíveis");return}
    const folder=ordered[0].webkitRelativePath.split("/")[0]||"Gameplay";
    const name=window.prompt("Nome desta sessão de gameplay:",folder)?.trim();if(!name)return;
    setBusy(true);
    try{
      const session=await api.createVideoSession(name,folder);
      for(let index=0;index<ordered.length;index++){setTestResult(`Importando clipe ${index+1} de ${ordered.length}…`);await uploadVideo(ordered[index],percent=>setUploadProgress(Math.round((index+percent/100)/ordered.length*100)),session.id,index)}
      const [videos,sessions]=await Promise.all([api.videos(),api.videoSessions()]);setVideoFiles(videos.items);setVideoSessions(sessions.items);setTestResult(`${ordered.length} clipes agrupados em “${name}”`);
    }catch(err){setError((err as Error).message)}finally{setBusy(false);setUploadProgress(null);if(folderUploadRef.current)folderUploadRef.current.value=""}
  };
  const analyzeSession=async(session:VideoSession)=>withVideoAction(`session:${session.id}`,async()=>{setVideoSessions(current=>current.map(item=>item.id===session.id?{...item,status:"queued",stage:"Enfileirando",progress:0}:item));try{await api.processVideoSession(session.id);const result=await api.pipelineQueue();setQueueJobs(result.jobs);setQueueRunning(result.running);openQueuePanel()}catch(err){void refreshVideos();setError((err as Error).message)}});
  const joinSelectedVideos=async(name?:string)=>{const itemCount=selectedVideoPaths.length+selectedSessionIds.length;if(itemCount<2)return;const sessionName=name?.trim()||prompt("Nome da sessão unida",`Sessão ${new Date().toLocaleString("pt-BR")}`)?.trim();if(!sessionName)return;setBusy(true);try{const result=await api.joinVideoSession(selectedVideoPaths,selectedSessionIds,sessionName);setSelectedVideoPaths([]);setSelectedSessionIds([]);setJoinMode(false);if(openSessionId!==null&&selectedSessionIds.includes(openSessionId))setOpenSessionId(null);await refreshVideos();setTestResult(`${itemCount} itens unidos em “${sessionName}” · ${result.clips} clipes preservados`)}catch(err){setError((err as Error).message)}finally{setBusy(false)}};
  const openContextFor=(target:string)=>{selectContextTarget(target);setContextModalOpen(true)};
  const deleteSession=async(session:VideoSession)=>{
    const clipText=session.clip_count?` e ${session.clip_count} clipe${session.clip_count===1?"":"s"} ainda existente${session.clip_count===1?"":"s"}`:"";
    if(!window.confirm(`Excluir permanentemente a sessão “${session.name}”${clipText}?`))return;
    await withVideoAction(`session:${session.id}`,async()=>{try{const result=await api.deleteVideoSession(session.id);setVideoSessions(current=>current.filter(item=>item.id!==session.id));setVideoFiles(current=>current.filter(item=>item.session_id!==session.id));if(contextTarget===`session:${session.id}`){setContextTarget("");setContextDraft("")}setTestResult(result.deleted_files?`Sessão e ${result.deleted_files} clipe${result.deleted_files===1?"":"s"} excluído${result.deleted_files===1?"":"s"}`:"Sessão excluída")}
    catch(err){setError((err as Error).message)}})
  };
  const selectContextTarget=(value:string)=>{
    setContextTarget(value);const [kind,id]=value.split(":");
    setContextDraft(kind==="session"?(videoSessions.find(item=>item.id===+id)?.context||""):(videoFiles.find(item=>item.id===+id)?.context||""));
  };
  const saveManualContext=async()=>{
    if(!contextTarget)return;const [kind,id]=contextTarget.split(":");setBusy(true);
    try{if(kind==="session")await api.saveVideoSessionContext(+id,contextDraft);else await api.saveVideoContext(+id,contextDraft);const [videos,sessions]=await Promise.all([api.videos(),api.videoSessions()]);setVideoFiles(videos.items);setVideoSessions(sessions.items);setTestResult("Informações extras salvas")}
    catch(err){setError((err as Error).message)}finally{setBusy(false)}
  };
  const seekVideo=(file:VideoFile,seconds:number)=>{
    const player=videoRefs.current[file.path];if(!player)return;
    player.currentTime=seconds;player.play().catch(()=>{});player.scrollIntoView({behavior:"smooth",block:"center"});
  };

  const openFiles = async (nextKind: "screen"|"audio") => {
    setMobileNavOpen(false);
    setSelectedScreenPaths([]);screenSelectionAnchor.current=null;setScreenSequenceResult(null);
    setFileKind(nextKind); setView("captura"); setCapturaTab("arquivos"); setBusy(true);
    try { const result=await api.files(nextKind); setRawFiles(result.items); setFileTotal(result.total); }
    catch(err){setError((err as Error).message)} finally{setBusy(false)}
  };

  const switchFiles = async (nextKind: "screen"|"audio") => {
    setSelectedScreenPaths([]);screenSelectionAnchor.current=null;setScreenSequenceResult(null);
    setFileKind(nextKind); setBusy(true);
    try { const result=await api.files(nextKind); setRawFiles(result.items); setFileTotal(result.total); }
    catch(err){setError((err as Error).message)} finally{setBusy(false)}
  };

  const loadMoreFiles = async () => {
    setBusy(true);
    try { const result=await api.files(fileKind,rawFiles.length); setRawFiles(current=>[...current,...result.items]); setFileTotal(result.total); }
    catch(err){setError((err as Error).message)} finally{setBusy(false)}
  };

  const manualProcess = async (file:RawFile) => {
    setBusy(true); setTestResult(`${file.kind==="screen"?"Descrevendo":"Transcrevendo"} ${file.name}…`);
    try { const result=await api.processFile(file); setTestResult(`Concluído: ${result.title||file.name}`); const refreshed=await api.files(fileKind); setRawFiles(refreshed.items); setFileTotal(refreshed.total); await refreshMemory(); }
    catch(err){setTestResult(`Falhou: ${(err as Error).message}`)} finally{setBusy(false)}
  };

  const testScreenSequence = async () => {
    if(selectedScreenPaths.length<2||selectedScreenPaths.length>30)return;
    setBusy(true);setScreenSequenceResult(null);setTestResult(`Analisando ${selectedScreenPaths.length} prints em sequência…`);
    try{const result=await api.testScreenSequence(selectedScreenPaths);setActiveScreenSequenceJob(result.id);queueWasRunning.current=true;const queueResult=await api.pipelineQueue(selectedDay);applyQueueResult(queueResult);setTestResult("Análise de sequência adicionada à fila");openQueuePanel()}
    catch(err){setTestResult(`Falhou: ${(err as Error).message}`)}finally{setBusy(false)}
  };

  useEffect(()=>{if(activeScreenSequenceJob===null)return;let active=true;let timer:number|undefined;const load=async()=>{try{const job=await api.screenSequenceResult(activeScreenSequenceJob);if(!active)return;if(job.status==="done"){setScreenSequenceResult(job.result);setActiveScreenSequenceJob(null);setTestResult("Análise da sequência concluída · resultado disponível em Arquivos brutos");return}if(job.status==="error"||job.status==="cancelled"){setActiveScreenSequenceJob(null);setTestResult(job.status==="cancelled"?"Análise da sequência cancelada":`Falhou: ${job.error}`);return}timer=window.setTimeout(load,1000)}catch(err){if(active){setActiveScreenSequenceJob(null);setTestResult(`Falhou: ${(err as Error).message}`)}}};void load();return()=>{active=false;if(timer!==undefined)window.clearTimeout(timer)}},[activeScreenSequenceJob]);

  const cancelScreenSequenceJob=async(job:QueueJob)=>{if(!job.sequence_id)return;setBusy(true);try{await api.cancelScreenSequence(job.sequence_id);setActiveScreenSequenceJob(current=>current===job.sequence_id?null:current);const result=await api.pipelineQueue(selectedDay);setQueueJobs(result.jobs);setQueueRunning(result.running);setTestResult("Análise da sequência cancelada")}catch(err){setError((err as Error).message)}finally{setBusy(false)}};

  const toggleScreenSelection=(path:string,shiftKey:boolean)=>{
    setScreenSequenceResult(null);
    setSelectedScreenPaths(current=>{
      if(shiftKey&&screenSelectionAnchor.current){
        const anchorIndex=rawFiles.findIndex(file=>file.path===screenSelectionAnchor.current);
        const targetIndex=rawFiles.findIndex(file=>file.path===path);
        if(anchorIndex>=0&&targetIndex>=0){
          const [start,end]=anchorIndex<targetIndex?[anchorIndex,targetIndex]:[targetIndex,anchorIndex];
          return Array.from(new Set([...current,...rawFiles.slice(start,end+1).map(file=>file.path)]));
        }
      }
      screenSelectionAnchor.current=path;
      return current.includes(path)?current.filter(value=>value!==path):[...current,path];
    });
  };

  const deleteSelectedScreens=async()=>{
    const selected=rawFiles.filter(file=>selectedScreenPaths.includes(file.path));
    if(!selected.length)return;
    if(!window.confirm(`Excluir permanentemente ${selected.length} print${selected.length===1?"":"s"} selecionado${selected.length===1?"":"s"}? Os arquivos serão apagados do disco.`))return;
    setBusy(true);
    try{const deleted:string[]=[];const failures:string[]=[];
      for(const file of selected){try{await api.deleteFile(file);deleted.push(file.path)}catch{failures.push(file.name)}}
      setRawFiles(current=>current.filter(file=>!deleted.includes(file.path)));
      setSelectedScreenPaths(current=>current.filter(path=>!deleted.includes(path)));
      screenSelectionAnchor.current=null;setFileTotal(current=>Math.max(0,current-deleted.length));setLightbox(null);
      setTestResult(`${deleted.length} print${deleted.length===1?" excluído":"s excluídos"}${failures.length?` · ${failures.length} não puderam ser excluídos`:""}`);
      await Promise.all([refreshMemory(),refresh()]);
    }catch(err){setError((err as Error).message)}finally{setBusy(false)}
  };

  const deleteRawFile = async (file:RawFile) => {
    if(!window.confirm(`Excluir permanentemente “${file.name}”? O arquivo será apagado do disco.`)) return;
    setBusy(true);
    try {
      await api.deleteFile(file);
      setRawFiles(current=>current.filter(candidate=>candidate.path!==file.path));
      setSelectedScreenPaths(current=>current.filter(path=>path!==file.path));
      setFileTotal(current=>Math.max(0,current-1));
      setLightbox(null);
      await Promise.all([refreshMemory(),refresh()]);
    } catch(err){setError((err as Error).message)}
    finally{setBusy(false)}
  };

  const deleteAllUnprocessedFiles = async () => {
    if(!window.confirm("Excluir permanentemente todos os áudios e telas locais que ainda não foram processados? Arquivos processados e gravações em andamento serão preservados.")) return;
    setBusy(true);
    try {
      const result=await api.deleteUnprocessedFiles();
      const refreshed=await api.files(fileKind);
      setRawFiles(refreshed.items);setFileTotal(refreshed.total);setLightbox(null);
      setTestResult(`${result.deleted_total} arquivo${result.deleted_total===1?" excluído":"s excluídos"} (${result.deleted.screen} tela${result.deleted.screen===1?"":"s"} e ${result.deleted.audio} áudio${result.deleted.audio===1?"":"s"}).`);
      await Promise.all([refreshMemory(),refresh()]);
    } catch(err){setError((err as Error).message)}
    finally{setBusy(false)}
  };

  const identifyLightboxVoice=async(speaker:VideoSpeaker,selectedLabel?:string)=>{
    const capture=lightbox?.capture;if(!capture)return;
    const label=(selectedLabel??window.prompt("Quem é esta pessoa?",speaker.identified?speaker.label:"")??"").trim();
    if(!label)return;
    try{
      await api.renameCaptureSpeaker(capture.id,speaker.id,label);
      const found=await api.captures("all");const updated=found.items.find(item=>item.id===capture.id);
      if(updated)setLightbox(current=>current?{...current,capture:updated,text:updated.text}:current);
      await refreshMemory();
    }catch(err){setError((err as Error).message)}
  };
  const openVoiceProfiles=async()=>{try{const result=await api.voiceIdentities();setVoiceProfiles(result.items);setShowLightboxVoices(false)}catch(err){setError((err as Error).message)}};
  const removeVoiceProfile=async(profile:VoiceIdentity)=>{
    if(!window.confirm(`Remover o perfil “${profile.label}”? As falas serão mantidas e voltarão a ficar sem identificação.`))return;
    try{
      const result=await api.deleteVoiceIdentity(profile.id);
      const refreshed=await api.voiceIdentities();setVoiceProfiles(refreshed.items);
      const capture=lightbox?.capture;
      if(capture){const found=await api.captures("all");const updated=found.items.find(item=>item.id===capture.id);if(updated)setLightbox(current=>current?{...current,capture:updated,text:updated.text}:current)}
      await refreshMemory();setTestResult(`Perfil “${result.label}” removido; ${result.updated.audio+result.updated.video} gravação(ões) foram desvinculadas.`);
    }catch(err){setError((err as Error).message)}
  };

  return <div className={`app-shell ${mediaPlaybackOpen?"media-playback-open":""} ${mobileNavOpen?"mobile-nav-open":""}`}>
    {mobileNavOpen&&<button className="mobile-nav-backdrop" aria-label="Fechar menu" onClick={()=>setMobileNavOpen(false)}/>}
    <aside className={`sidebar ${mobileNavOpen?"open":""}`} aria-label="Navegação principal">
      <div className="brand"><div className="brand-mark"><i /></div><span>Lume</span><em>local</em><button className="mobile-menu-close" aria-label="Fechar menu" onClick={()=>setMobileNavOpen(false)}>×</button></div>
      <div className="side-group">
        <span className="eyebrow">Memória</span>
        <nav>
          <button className={isDayView ? "active" : ""} onClick={() => navigate(lastLensRef.current)}><b>◉</b>Meu dia</button>
          <button className={view === "busca" ? "active" : ""} onClick={() => navigate("busca")}><b>⌕</b>Busca<kbd className="kbd-hint">Ctrl K</kbd></button>
        </nav>
      </div>
      <div className="side-group">
        <span className="eyebrow">Gravações</span>
        <nav>
          <button className={view === "videos" ? "active" : ""} onClick={() => navigate("videos")}><b>{icons.videos}</b>Vídeos &amp; sessões</button>
        </nav>
      </div>
      <div className="side-group">
        <span className="eyebrow">Sistema</span>
        <nav>
          <button className={view === "captura" ? "active" : ""} onClick={() => navigate("captura")}><b>{icons.captura}</b>Central de captura{queueCount>0&&<span className={`nav-count ${pipeline?.running||queueRunning?"hot":""}`}>{queueCount}</span>}</button>
        </nav>
        <button className="sensor-row" onClick={() => openFiles("audio")}><i className={`dot ${status?.audio.active ? "ok" : ""}`}/>Áudio<small>{status?.files.audio.count || 0}</small></button>
        <button className="sensor-row" onClick={() => openFiles("screen")}><i className={`dot ${status?.screen.active ? "ok" : ""}`}/>Telas<small>{status?.files.screen.count || 0}</small></button>
        <div className="sensor-row" title={status?.video.window||undefined}><i className={`dot ${status?.video.recording?"rec":status?.video.service_active?"warn":""}`}/>Vídeo<small>{status?.video.recording?`${status.video.mode==="clips"?"buffer":"gravando"} · ${sessionDuration(status.video.started_at?statusClock/1000-status.video.started_at:0)}`:status?.video.service_active?"aguardando":"desligado"}</small></div>
      </div>
      <div className="capture-card">
        <div className="capture-title"><i className={automaticCapturePause?"video":status?.capturing?"pulse":"off"}/><strong>{automaticCapturePause?automaticPauseTitle:status?.capturing?"Capturando":"Captura pausada"}</strong></div>
        {automaticCapturePause?<p className="video-pause-note">{automaticPauseNote}</p>:<div className="capture-meta"><span>{bytes(status?.storage.bytes)}</span><span>{status?.capturing ? captureLabel : "em pausa"}</span></div>}
        <button className="secondary block" disabled={busy || !status || automaticCapturePause} onClick={toggleCapture}>{automaticCapturePause?"Retomada automática":status?.capturing?"Pausar captura":"Retomar captura"}</button>
      </div>
      <div className="privacy-links"><button onClick={openDiagnostics}>Diagnóstico</button><button onClick={openPrivacy}>Privacidade</button><button onClick={openSettings}>Ajustes</button></div>
    </aside>

    <main>
      <header className="topbar"><button className="mobile-menu-button" aria-label="Abrir menu" aria-expanded={mobileNavOpen} onClick={()=>setMobileNavOpen(true)}>☰</button><div className="topbar-title"><h1>{isDayView?"Meu dia":labels[view][0]}</h1>{!isDayView&&<p>{labels[view][1]}</p>}</div>
        {isDayView&&<div className="day-nav">
          <button className="day-step" disabled={dayIndex<0||dayIndex>=memoryDays.length-1} onClick={()=>stepDay(1)} aria-label="Dia anterior">‹</button>
          <label className="day-chip"><select value={selectedDay} disabled={!memoryDays.length} onChange={event=>setSelectedDay(event.target.value)}>{memoryDays.map(item=><option value={item.day} key={item.day}>{new Date(`${item.day}T12:00:00`).toLocaleDateString("pt-BR",{weekday:"short",day:"numeric",month:"short"})} · {item.count}</option>)}</select></label>
          <button className="day-step" disabled={dayIndex<=0} onClick={()=>stepDay(-1)} aria-label="Próximo dia">›</button>
        </div>}
        {isDayView&&<div className="segmented lens-switch">{lensLabels.map(([key,label])=><button key={key} className={view===key?"active":""} onClick={()=>setView(key)}>{label}</button>)}</div>}
        <div className="topbar-actions">
          <button className="omni-button" onClick={()=>{setPaletteQuery("");setPaletteItems([]);setPalette(true)}} title="Buscar memórias e ações em qualquer tela"><span aria-hidden="true">⌕</span>Buscar<kbd>Ctrl K</kbd></button>
          <button className={`refresh-button ${refreshing?"refreshing":""}`} disabled={refreshing} onClick={refreshCurrentView} title="Atualizar os dados desta tela"><span aria-hidden="true">↻</span>Atualizar</button>
        </div>
      </header>
      <div className={`content ${dragActive?"drag-active":""}`} onDragEnter={dragEnter} onDragOver={dragOver} onDragLeave={dragLeave} onDrop={dropVideos}>
        {dragActive&&<div className="drop-overlay"><div><b>Solte para importar</b><span>MP4, MKV, WebM, MOV, AVI ou M4V</span></div></div>}
        {view==="videos"&&<div className="media-toolbar"><div><h2>Biblioteca de vídeos</h2><p>{joinMode?"Selecione vídeos avulsos e/ou sessões para formar uma sessão maior":videoGame?`${videoLibraryItems.length} item${videoLibraryItems.length===1?"":"s"} de ${videoGame}`:"Vídeos avulsos e sessões analisadas"}</p></div>{joinMode?<><button className="ghost" onClick={()=>{setJoinMode(false);setSelectedVideoPaths([]);setSelectedSessionIds([])}}>Cancelar</button><button className="primary" disabled={selectedVideoPaths.length+selectedSessionIds.length<2||busy} onClick={()=>joinSelectedVideos()}>Concluir · {selectedVideoPaths.length+selectedSessionIds.length} itens</button></>:<><button className="secondary" disabled={videoFiles.filter(file=>!file.session_id&&file.available).length+videoSessions.filter(session=>session.clip_count>0&&!['queued','processing'].includes(session.status)).length<2} onClick={()=>{setVideoGame("");setJoinMode(true)}}>Unir vídeos/sessões</button><button className="secondary" onClick={()=>videoUploadRef.current?.click()}>+ Vídeos</button><button className="secondary" onClick={()=>folderUploadRef.current?.click()}>+ Sessão</button></>}</div>}
        {view==="videos"&&!joinMode&&!!gameStats.length&&<section className="game-selector" aria-label="Filtrar biblioteca por jogo"><header><div><span className="eyebrow">Filtrar por jogo</span><p>Escolha um jogo para ver somente seus clipes e sessões.</p></div>{videoGame&&<button className="ghost" onClick={()=>setVideoGame("")}>Mostrar todos</button>}</header><div className="game-selector-grid">{gameStats.map(game=><button key={game.game} className={videoGame===game.game?"active":""} aria-pressed={videoGame===game.game} onClick={()=>setVideoGame(current=>current===game.game?"":game.game)}><GameCover game={game.game}/><strong>{game.game}</strong><small>{game.clips} clipe{game.clips===1?"":"s"} · {bytes(game.bytes)}</small></button>)}</div></section>}
        {view==="videos"&&videoSettings&&<details className="video-prefs"><summary><b aria-hidden="true">⚙</b><span>Preferências de gravação e análise</span><em>{(videoSettings.capture_mode==="clips"?`clipes F8 · ${videoSettings.replay_seconds}s`:"gravação contínua")+" · varredura "+({fast:"rápida",balanced:"equilibrada",detailed:"detalhada",custom:"personalizada"}[videoSettings.analysis_profile])+" · "+(videoSettings.delete_after_description?"exclui após descrição":"retenção segura")}</em><i aria-hidden="true">›</i></summary><div className="video-prefs-body"><div className="video-retention"><label className="check"><input type="checkbox" checked={videoSettings.delete_after_description} onChange={e=>setVideoSettings({...videoSettings,delete_after_description:e.target.checked})}/><span>Excluir segmento original depois de uma descrição bem-sucedida, exceto clips preservados</span></label><small>Desativado é o modo seguro recomendado durante os testes.</small></div>
        <div className="game-capture-behavior"><label><span>Modo do gravador</span><select disabled={busy} value={videoSettings.capture_mode} onChange={e=>void saveCaptureMode(e.target.value as VideoSettings["capture_mode"])}><option value="continuous">Gravação contínua</option><option value="clips">Clipes pelo F8</option></select></label>{videoSettings.capture_mode==="continuous"&&<label className="check"><input type="checkbox" checked={videoSettings.segment_seconds===0} onChange={e=>setVideoSettings({...videoSettings,segment_seconds:e.target.checked?0:60})}/><span>Um único arquivo por sessão de jogo</span></label>}<small>{videoSettings.capture_mode==="clips"?`F8 salva os últimos ${videoSettings.replay_seconds}s; os clipes serão agrupados por sessão.`:videoSettings.segment_seconds===0?"Grava até você sair do jogo ou trocar de aplicativo.":`Divide o vídeo a cada ${videoSettings.segment_seconds}s.`}</small></div>
        <div className="analysis-profile"><label><span>Varredura da IA</span><select value={videoSettings.analysis_profile} onChange={e=>setAnalysisProfile(e.target.value as VideoSettings["analysis_profile"])}><option value="fast">Rápida · 10s</option><option value="balanced">Equilibrada · 5s</option><option value="detailed">Detalhada · 2s</option><option value="custom">Personalizada</option></select></label><label><span>Intervalo (s)</span><input type="number" min=".5" max="30" step=".5" disabled={videoSettings.analysis_profile!=="custom"} value={videoSettings.scan_interval_seconds} onChange={e=>setVideoSettings({...videoSettings,scan_interval_seconds:+e.target.value})}/></label><label><span>Máximo de keyframes</span><input type="number" min="8" max="160" disabled={videoSettings.analysis_profile!=="custom"} value={videoSettings.max_keyframes} onChange={e=>setVideoSettings({...videoSettings,max_keyframes:+e.target.value})}/></label><p>Detecta mudanças visuais e mantém frames periódicos para acompanhar progresso sem enviar o vídeo inteiro ao modelo.</p></div></div></details>}
        {view==="videos"&&!joinMode&&<div className="video-sort-bar"><span>Ordenar pela data de gravação</span><select value={videoSort} onChange={event=>setVideoSort(event.target.value as "newest"|"oldest")}><option value="newest">Mais recentes primeiro</option><option value="oldest">Mais antigos primeiro</option></select></div>}
        {error && <div className="error-banner"><strong>Backend indisponível</strong><span>{error}</span><button onClick={refresh}>Tentar novamente</button></div>}
        {view === "busca" && <><div className="search"><span>⌕</span><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar em tudo que você viu e ouviu…" /></div>
          <div className="memory-toolbar"><div className="segmented">{[["all","Tudo"],["screen","Telas"],["audio","Áudio"]].map(([key,label])=><button key={key} className={kind===key?"active":""} onClick={()=>setKind(key as typeof kind)}>{label}</button>)}</div><span>{items.length} resultados</span></div>
          <div className="memory-feed">{items.map(item=><CaptureCard item={item} onOpen={(url,name,text,model,itemKind,capture)=>{setShowLightboxVoices(false);setVoiceProfiles(null);setLightbox({url,name,text,model,kind:itemKind,capture})}} onDelete={deleteMemoryItem} disabled={busy} key={item.id}/>)}</div>{!items.length&&<EmptyView view="busca"/>}</>}
        {view === "resumo" && <><div className="summary-actions"><button className="primary" disabled={busy||!memoryDays.length} onClick={forceSummary}>{summary?"Regerar resumo":"Gerar resumo agora"}</button><button className="danger" disabled={busy||pipeline?.running||queueRunning} onClick={deleteUnkeptRawMedia}>Limpar prints e áudios processados</button>{testResult&&<span>{testResult}</span>}</div><SummaryView summary={summary} onOpenMedia={openSummaryMedia}/></>}
        {view === "atividades" && <div className="activities-view"><div className="activity-day-bar"><p>Todos os prints com mudança relevante são analisados por aplicativo e continuidade temporal.</p></div><ActivitiesView items={activities} running={hourlyRunning} onGenerate={generateHours} onOpen={frame=>setLightbox({url:frame.url||null,name:frame.title,text:frame.text,model:"",kind:"screen"})}/></div>}
        {view === "videos" && <div className="video-view"><input ref={videoUploadRef} type="file" accept="video/mp4,video/x-matroska,video/webm,video/quicktime,video/x-msvideo,.m4v" multiple onChange={event=>importVideos(event.target.files)} hidden/><input ref={folderUploadRef} type="file" multiple hidden onChange={event=>importVideoFolder(event.target.files)}/>{testResult&&<div className="result video-result">{testResult}</div>}<div className={`video-grid ${joinMode?"joining":""}`}>{videoLibraryItems.map(entry=>entry.kind==="video"?<VideoCard key={entry.item.path} file={entry.item} busy={busy} selecting={joinMode} selected={selectedVideoPaths.includes(entry.item.path)} onToggle={()=>setSelectedVideoPaths(current=>current.includes(entry.item.path)?current.filter(path=>path!==entry.item.path):[...current,entry.item.path])} onContext={()=>entry.item.id&&openContextFor(`video:${entry.item.id}`)} onDate={()=>editVideoDate(entry.item)} onOpen={()=>setOpenVideoPath(entry.item.path)} onAnalyze={()=>analyzeVideo(entry.item)} onPreserve={()=>preserveVideo(entry.item)} onDelete={()=>deleteVideo(entry.item)} onVideoRef={element=>{videoRefs.current[entry.item.path]=element}} onSeek={seconds=>seekVideo(entry.item,seconds)}/>:<SessionCard key={`session-${entry.item.id}`} session={entry.item} busy={busy} selecting={joinMode} selected={selectedSessionIds.includes(entry.item.id)} onToggle={()=>setSelectedSessionIds(current=>current.includes(entry.item.id)?current.filter(id=>id!==entry.item.id):[...current,entry.item.id])} onOpen={item=>setOpenSessionId(item.id)} onAnalyze={analyzeSession} onDelete={deleteSession} onContext={item=>openContextFor(`session:${item.id}`)}/>)}</div>{!videoLibraryItems.length&&<EmptyView view="videos"/>}</div>}
        {view === "timeline" && <div className="hourly-view"><div className="hourly-actions"><span>{hourlyRunning?"Qwen está resumindo as horas…":`${timelineHours.length} horas com atividade`}</span><button className="primary" disabled={busy||hourlyRunning||!timelineHours.length} onClick={generateHours}>{hours.length?"Atualizar resumos":"Gerar resumos horários"}</button></div>{timelineHours.length?<div className="hour-grid">{timelineHours.map(({source,summary})=><button key={source.hour} onClick={()=>openHour(source.hour,summary)}><time>{source.hour.slice(11)}:00</time><div><h3>{summary?.title||"Resumo ainda não gerado"}</h3><p>{summary?.narrative||`${source.count} registros disponíveis para esta hora.`}</p><span>{summary?.tags.map(tag=>`#${tag}`).join("  ")||"Clique para ver os detalhes"}</span></div><b>›</b></button>)}</div>:<EmptyView view="timeline"/>}</div>}
        {view === "jogos" && (summary?.data.games?.length ? <div className="games-grid">{summary.data.games.map((game,i)=><article key={i}><div className="game-cover">{game.title.split(" ").map(x=>x[0]).join("").slice(0,2)}</div><h2>{game.title}</h2><p>{game.minutes} minutos detectados</p><small>{game.event}</small></article>)}</div>:<EmptyView view="jogos"/>)}
        {view==="captura"&&<div className="captura-view">
          <div className="sensor-tiles">
            <button className="tile" onClick={()=>openFiles("audio")}><header><i className={`dot ${status?.audio.active?"ok":""}`}/>Áudio</header><b>{status?.files.audio.count||0}</b><small>{bytes(status?.files.audio.bytes)} · {status?.audio.active?"captura ativa":"inativo"}</small></button>
            <button className="tile" onClick={()=>openFiles("screen")}><header><i className={`dot ${status?.screen.active?"ok":""}`}/>Telas</header><b>{status?.files.screen.count||0}</b><small>{bytes(status?.files.screen.bytes)} · {captureLabel}</small></button>
            <div className="tile"><header><i className={`dot ${status?.video.recording?"rec":status?.video.service_active?"warn":""}`}/>Vídeo seletivo</header><b>{status?.video.recording?(status.video.mode==="clips"?"buffer ativo":"gravando"):status?.video.service_active?"aguardando":"desligado"}</b><small>{status?.video.recording?sessionDuration(status.video.started_at?statusClock/1000-status.video.started_at:0):status?.video.window||"nenhum app da lista aberto"}</small></div>
          </div>
          <nav className="subtabs">
            <button className={capturaTab==="fila"?"active":""} onClick={()=>setCapturaTab("fila")}>Fila{queueCount>0&&<span>{queueCount}</span>}</button>
            <button className={capturaTab==="arquivos"?"active":""} onClick={()=>{setCapturaTab("arquivos");if(!rawFiles.length)void switchFiles(fileKind)}}>Arquivos brutos</button>
            <button className={capturaTab==="diagnostico"?"active":""} onClick={()=>setCapturaTab("diagnostico")}>Diagnóstico</button>
          </nav>
          {capturaTab==="fila"&&<><div className="queue-head">
            <div className="queue-summary">
              <span>{queueCounts?<><b>{queueCounts.audio.toLocaleString("pt-BR")}</b> áudios · <b>{queueCounts.screen.toLocaleString("pt-BR")}</b> telas · {queue.length.toLocaleString("pt-BR")} de {queueCounts.total.toLocaleString("pt-BR")} exibidos</>:<>{queue.length.toLocaleString("pt-BR")} itens exibidos</>}</span>
              <div className="queue-speed">
                <span title={queueSpeed?.screen.samples?`Média ${queueSpeed.screen.samples===1?"da última imagem analisada":`das últimas ${queueSpeed.screen.samples} imagens analisadas`}`:"Ainda não há imagens analisadas para calcular a média"}><i aria-hidden="true">▣</i>Imagem <b>{analysisAverage(queueSpeed?.screen.avg_ms||0)}</b></span>
                <span title={queueSpeed?.audio.samples?`Média ${queueSpeed.audio.samples===1?"do último áudio analisado":`dos últimos ${queueSpeed.audio.samples} áudios analisados`}`:"Ainda não há áudios analisados para calcular a média"}><i aria-hidden="true">▮▮</i>Áudio <b>{analysisAverage(queueSpeed?.audio.avg_ms||0)}</b></span>
                {!!queueSpeed?.eta_seconds&&<span className="queue-eta" title="Estimativa para esvaziar a fila com as médias atuais, considerando a execução sequencial">Fila <b>~{queueEta(queueSpeed.eta_seconds)}</b></span>}
              </div>
            </div>
            <div className="queue-actions">
              <div className="queue-tools">
                <button className="queue-tool" disabled={busy} onClick={unloadOllama} title="Descarrega os modelos da GPU e libera a memória de vídeo">Liberar VRAM</button>
                {queueWorkerRunning&&!queuePaused&&<button className="queue-tool" disabled={busy} onClick={pausePipeline} title="Interrompe o worker preservando a fila para retomada">Pausar worker</button>}
                <span className="queue-tool-sep" aria-hidden="true"/>
                {queueWorkerRunning&&<button className="queue-tool danger" disabled={busy} onClick={stopPipeline} title="Para o processamento e devolve o item atual para a fila">Parar processamento</button>}
                <button className="queue-tool danger" disabled={busy||(!queue.length&&!queueJobs.length)} onClick={clearQueue} title="Remove todos os itens pendentes da fila">Cancelar toda a fila</button>
              </div>
              {queuePaused
                ?<button className="primary" disabled={busy} onClick={resumePipeline}>Retomar worker</button>
                :<button className="primary" disabled={busy||queueRunning} onClick={runPipeline}>{queueRunning?"Processando…":"Processar pendentes"}</button>}
            </div>
          </div>
      <p className="help">A execução é sequencial: vídeos e sessões primeiro, depois todos os áudios e, por fim, as telas. {videoSettings?.thinking_enabled?"O raciocínio interno do Qwen está ativado; as etapas verificáveis e o resultado final aparecem aqui.":"A fila mostra transcrição, capítulos, pesquisas, síntese e possíveis erros."}</p>
      <div className="queue-list">{queueJobs.map(job=>job.kind==="video"?<article className={`${job.status||"processing"} video-job`} key={job.id}><b>▶</b><div><strong>{job.title||"Análise de vídeo"}</strong><span>{job.stage}</span><div className="job-progress"><i style={{width:`${job.progress||0}%`}}/><em>{job.progress||0}%</em></div><AIInspector job={job}/>{!!job.trace?.length&&<details className="job-trace"><summary>Acompanhar evidências e decisões</summary>{job.trace.map((event,index)=><section key={`${event.time}-${index}`}><time>{event.chapter?`Capítulo ${event.chapter}`:"Síntese"}</time>{event.title&&<strong>{event.title}</strong>}<p>{event.detail}</p>{!!event.evidence?.length&&<ul>{event.evidence.map((item,i)=><li key={i}>{item}</li>)}</ul>}{event.interpretation&&<small>Interpretação: {event.interpretation}</small>}</section>)}</details>}{job.error&&<small>{job.error}</small>}</div><em>Áudio + vídeo</em>{job.status!=="error"&&<button className="queue-remove" disabled={busy} onClick={()=>cancelVideoJob(job)}>Cancelar</button>}</article>:job.kind==="screen_sequence"?<article className={`${job.status||"processing"} video-job`} key={job.id}><b>▣</b><div><strong>{job.title}</strong><span>{job.stage}</span><div className="job-progress"><i style={{width:`${job.progress||0}%`}}/><em>{job.progress||0}%</em></div>{job.error&&<small>{job.error}</small>}</div><em>Vários frames</em>{job.status!=="error"&&<button className="queue-remove" disabled={busy} onClick={()=>cancelScreenSequenceJob(job)}>Cancelar</button>}</article>:<article className={`${job.status||"processing"} summary-job`} key={job.id}><b>{job.status==="error"?"!":"✦"}</b><div><strong>{job.kind==="hourly"?"Timeline por hora":"Resumo do dia"}</strong><span>{job.stage}</span></div><em>Qwen</em></article>)}{queue.map(item=><article className={item.status} key={item.id}><b>{item.status==="processing"?"●":`#${item.position}`}</b>{item.kind==="screen"?<button className="queue-preview" onClick={()=>setLightbox({url:item.url,name:item.name,text:"Ainda não processada",model:""})}><img src={item.url} loading="lazy"/></button>:<AudioPlayer src={item.url}/>}<div><strong>{item.name}</strong><span>{item.stage}</span>{item.error&&<small>{item.error}</small>}</div><em>{item.kind==="screen"?"Tela":"Áudio"}</em><button className="queue-remove" disabled={busy} onClick={()=>removeQueueItem(item)}>Remover da fila</button></article>)}</div>
      {!queue.length&&!queueJobs.length&&<div className="result">A fila está vazia.</div>}</>}
          {capturaTab==="arquivos"&&<><div className="file-toolbar"><div className="segmented"><button className={fileKind==="screen"?"active":""} onClick={()=>switchFiles("screen")}>Telas</button><button className={fileKind==="audio"?"active":""} onClick={()=>switchFiles("audio")}>Áudio</button></div><span>{rawFiles.length} de {fileTotal} arquivos</span>{fileKind==="screen"&&<><button className="secondary" title={selectedScreenPaths.length>30?"A análise aceita no máximo 30 frames":""} disabled={busy||selectedScreenPaths.length<2||selectedScreenPaths.length>30} onClick={testScreenSequence}>Analisar sequência · {selectedScreenPaths.length}</button>{selectedScreenPaths.length>0&&<button className="danger" disabled={busy||activeScreenSequenceJob!==null} onClick={deleteSelectedScreens}>Excluir selecionados · {selectedScreenPaths.length}</button>}{selectedScreenPaths.length>0&&<button className="ghost" disabled={busy} onClick={()=>{setSelectedScreenPaths([]);screenSelectionAnchor.current=null;setScreenSequenceResult(null)}}>Limpar seleção</button>}</>}<button className="danger clear-unprocessed" disabled={busy} onClick={deleteAllUnprocessedFiles}>Limpar não processados</button></div>
      {busy && <div className="result">Carregando arquivos…</div>}
      {!busy && fileKind === "screen" && <div className="file-gallery">{rawFiles.map(file=>{const selected=selectedScreenPaths.includes(file.path);return <article className={selected?"selected":""} key={file.path}><label className="screen-select" onClick={event=>{event.preventDefault();toggleScreenSelection(file.path,event.shiftKey)}}><input type="checkbox" checked={selected} readOnly/><span>{selected?"Selecionado":"Selecionar"}</span></label><button className="file-preview" onClick={()=>setLightbox({url:file.url,name:file.name,text:file.text,model:file.model})}><img src={file.url} loading="lazy"/></button><span>{file.name}</span><small>{new Date(file.modified_at).toLocaleString("pt-BR")} · {bytes(file.bytes)} · {file.status}</small>{file.text&&<details><summary>Ler descrição da IA</summary><p>{file.text}</p><em>{file.model}</em></details>}<div className="file-actions">{file.status!=="done"&&<button className="process-one" disabled={busy} onClick={()=>manualProcess(file)}>Descrever com Qwen-VL</button>}<button className="delete-file" disabled={busy} onClick={()=>deleteRawFile(file)}>Excluir</button></div></article>})}</div>}
      {!busy && fileKind === "audio" && <div className="audio-files">{rawFiles.map(file=><article key={file.path}><div className="audio-file-meta"><strong>{file.name}</strong><small>{new Date(file.modified_at).toLocaleString("pt-BR")} · {bytes(file.bytes)} · {file.open?"gravando agora":file.status}</small>{file.text&&<><details><summary>Ler transcrição completa</summary><p>{file.text}</p><em>{file.model}</em></details>{file.status==="done"&&<AudioAnalysis file={file} onChanged={()=>switchFiles("audio")}/>}</>}</div>{file.open?<span className="recording-badge">● aberto</span>:<><AudioPlayer src={file.url}/><button className="process-one" disabled={busy} onClick={()=>manualProcess(file)}>{file.status==="done"?"Reanalisar":"Analisar"}</button><button className="delete-file" disabled={busy} onClick={()=>deleteRawFile(file)}>Excluir</button></>}</article>)}</div>}
      {screenSequenceResult&&<section className="sequence-result"><span className="eyebrow">Teste com {screenSequenceResult.frame_count} frames · {screenSequenceResult.model}</span><h3>{screenSequenceResult.title}</h3><div>{screenSequenceResult.narrative.split(/\n+/).filter(Boolean).map((paragraph,index)=><p key={index}>{paragraph}</p>)}</div>{screenSequenceResult.events.length>0&&<details open><summary>Linha de acontecimentos</summary><ol>{screenSequenceResult.events.map((event,index)=><li key={index}>{event}</li>)}</ol></details>}<div className="tags">{screenSequenceResult.tags.map(tag=><span key={tag}>{tag}</span>)}</div></section>}
      {testResult && <div className="result">{testResult}</div>}
      {rawFiles.length < fileTotal && <button className="secondary load-more" disabled={busy} onClick={loadMoreFiles}>Carregar mais 100</button>}</>}
          {capturaTab==="diagnostico"&&<><div className="test-grid"><button className="test-card" disabled={busy} onClick={testAudio}><b>▮▮</b><span><strong>Testar áudio</strong><small>Grava 5 segundos e mede o volume</small></span></button>
      <button className="test-card" disabled={busy} onClick={testScreen}><b>▣</b><span><strong>Testar telas</strong><small>Valida privacidade e os dois monitores</small></span></button></div>
      {testResult && <div className="result">{testResult}</div>}
      {shots.length > 0 && <div className="previews">{shots.map(path => <figure key={path}><img src={`/api/screenshot?path=${encodeURIComponent(path)}`}/><figcaption>{path.split("/").pop()}</figcaption></figure>)}</div>}</>}
        </div>}
      </div>
    </main>

    <nav className="mobile-bottom-nav" aria-label="Navegação móvel">
      <button className={isDayView?"active":""} onClick={()=>navigate(lastLensRef.current)}><b>◉</b><span>Meu dia</span></button>
      <button className={view==="busca"?"active":""} onClick={()=>navigate("busca")}><b>⌕</b><span>Busca</span></button>
      <button className={view==="videos"?"active":""} onClick={()=>navigate("videos")}><b>{icons.videos}</b><span>Vídeos</span></button>
      <button className={view==="captura"?"active":""} onClick={()=>navigate("captura")}><b>{icons.captura}</b><span>Captura</span>{queueCount>0&&<em>{queueCount}</em>}</button>
      <button className={mobileNavOpen?"active":""} aria-expanded={mobileNavOpen} onClick={()=>setMobileNavOpen(open=>!open)}><b>☰</b><span>Menu</span></button>
    </nav>

    {contextModalOpen&&<ContextPickerModal sessions={videoSessions} files={videoFiles} target={contextTarget} draft={contextDraft} busy={busy} onTarget={selectContextTarget} onDraft={setContextDraft} onSave={saveManualContext} onClose={()=>{setContextModalOpen(false);setContextTarget("");setContextDraft("")}}/>}
    {openVideoPath&&videoFiles.find(file=>file.path===openVideoPath)&&<VideoViewer file={videoFiles.find(file=>file.path===openVideoPath)!} preroll={videoSettings?.marker_preroll_seconds||8} hotkey={videoSettings?.marker_hotkey||"F8"} onRefresh={refreshVideos} onClose={()=>setOpenVideoPath(null)}/>} 
    {openSessionId!==null&&videoSessions.find(session=>session.id===openSessionId)&&<SessionViewer session={videoSessions.find(session=>session.id===openSessionId)!} preroll={videoSettings?.marker_preroll_seconds||8} hotkey={videoSettings?.marker_hotkey||"F8"} onRefresh={refreshVideos} onEditDate={editSessionClipDate} onClose={()=>setOpenSessionId(null)}/>} 

    {panel === "settings" && settings && <Modal title="Configurações" className="settings-modal" onClose={() => setPanel(null)}>
      <nav className="settings-tabs">{([['capture','Captura'],['storage','Armazenamento'],['ai','Inteligência artificial'],['video','Vídeo seletivo']] as const).map(([key,label])=><button key={key} className={settingsTab===key?"active":""} onClick={()=>setSettingsTab(key)}>{label}</button>)}</nav>
      <div className="settings-tab-content">
      {settingsTab==="storage"&&storage&&<section className="storage-settings settings-tab-card"><div className="storage-heading"><div><span className="eyebrow">Armazenamento</span><h3>Armazenamento de mídia</h3><p>Prints, áudios, vídeos e clips novos serão gravados dentro desta pasta.</p></div><span>{bytes(storage.disk.free)} livres</span></div>
        <label><span>Pasta-raiz</span><input list="storage-candidates" value={storageRoot} onChange={e=>setStorageRoot(e.target.value)} placeholder="/mnt/meu-hd/lume"/><datalist id="storage-candidates">{storage.candidates.map(candidate=><option key={candidate.root} value={candidate.root}>{bytes(candidate.disk.free)} livres de {bytes(candidate.disk.total)}</option>)}</datalist></label>
        <div className="storage-paths"><span>Prints: <code>{storageRoot}/telas</code></span><span>Áudio: <code>{storageRoot}/audio</code></span><span>Gravações: <code>{storageRoot}/video-buffer</code></span></div>
        <small>Os arquivos existentes permanecem na pasta atual. A pasta escolhida precisa estar montada e permitir gravação.</small>
      </section>}
      {settingsTab==="storage"&&cleanupSettings&&<section className="settings-group"><div className="settings-group-title"><div><span className="eyebrow">Retenção segura</span><h3>Limpeza de prints e áudios processados</h3><p>Apaga o arquivo bruto somente depois que atividades, timeline e resumo do dia terminarem. Transcrições, descrições e índice permanecem; vídeos e sessões nunca são alterados.</p></div></div><label className="switch-row"><input type="checkbox" checked={cleanupSettings.enabled} onChange={event=>setCleanupSettings({enabled:event.target.checked})}/><span>{cleanupSettings.enabled?"Limpeza automática ativada":"Limpeza automática desativada"}</span></label><button className="secondary" type="button" disabled={busy||pipeline?.running||queueRunning} onClick={deleteUnkeptRawMedia}>Executar limpeza segura agora</button><small>Capturas marcadas como Manter e dias ainda não consolidados são sempre preservados.</small></section>}
      {settingsTab==="capture"&&<><section className="settings-group"><div className="settings-group-title"><div><span className="eyebrow">Captura de tela</span><h3>Quando salvar uma captura?</h3></div></div><div className="form-grid"><label><span>Modo</span><select value={settings.capture_mode} onChange={e => setSettings({...settings, capture_mode: e.target.value as "interval"|"change"})}><option value="interval">Em intervalo fixo</option><option value="change">Quando a tela mudar</option></select></label>{settings.capture_mode==="interval"?<label><span>Intervalo entre capturas (s)</span><input type="number" min="1" value={settings.interval_seconds} onChange={e => setSettings({...settings, interval_seconds: +e.target.value})}/></label>:<><label><span>Verificar mudanças a cada (s)</span><input type="number" min="1" value={settings.change_poll_seconds} onChange={e => setSettings({...settings, change_poll_seconds: +e.target.value})}/></label><label><span>Mudança mínima para capturar (%)</span><input type="number" min="0.1" step="0.1" value={settings.change_threshold_percent} onChange={e => setSettings({...settings, change_threshold_percent: +e.target.value})}/></label><label><span>Capturar mesmo sem mudança após (s)</span><input type="number" min="1" value={settings.change_max_interval_seconds} onChange={e => setSettings({...settings, change_max_interval_seconds: +e.target.value})}/></label></>}</div></section>
      <details className="settings-group advanced-settings"><summary>Opções avançadas de tela e privacidade</summary><div className="form-grid"><label><span>Resolução máxima</span><input value={settings.max_geometry} onChange={e => setSettings({...settings, max_geometry: e.target.value})}/></label></div><label className="check"><input type="checkbox" checked={settings.split_monitors} onChange={e => setSettings({...settings, split_monitors: e.target.checked})}/><span>Salvar cada monitor separadamente</span></label><label className="check"><input type="checkbox" checked={settings.active_monitor_only} onChange={e => setSettings({...settings, active_monitor_only: e.target.checked})}/><span>Capturar somente o monitor da janela ativa</span></label><label className="check"><input type="checkbox" checked={settings.privacy_fail_closed} onChange={e => setSettings({...settings, privacy_fail_closed: e.target.checked})}/><span>Bloquear captura se a janela ativa não puder ser identificada</span></label></details>
      {schedule&&<section className="settings-group schedule-settings"><div><span className="eyebrow">Automação diária</span><h3>Processamento automático</h3><p>Processa áudio, telas, timeline e resumo.</p></div><label className="switch-row"><input type="checkbox" checked={schedule.enabled} onChange={e=>setSchedule({...schedule,enabled:e.target.checked})}/><span>{schedule.enabled?"Ativada":"Desativada"}</span></label>{schedule.enabled&&<div className="schedule-time"><label><span>Executar às</span><input type="time" value={schedule.time} onChange={e=>setSchedule({...schedule,time:e.target.value})}/></label>{schedule.next_run&&<small>Próxima execução: {schedule.next_run}</small>}</div>}</section>}
      {settings.capture_mode==="change"&&<section className="settings-group change-test"><div className="settings-group-title"><div><span className="eyebrow">Teste prático</span><h3>Esta mudança seria capturada?</h3><p>Guarde a tela atual, faça uma mudança e compare usando o mesmo cálculo da captura real.</p></div></div><div className="change-test-actions"><button className="secondary" disabled={busy} onClick={startScreenChangeTest}>{screenChangeTest?.token?"Recomeçar teste":"Guardar referência"}</button><button className="primary" disabled={busy||!screenChangeTest?.token} onClick={compareScreenChangeTest}>Comparar agora</button></div>{screenChangeTest&&<div className={`change-test-result ${screenChangeTest.would_capture===true?"capture":screenChangeTest.would_capture===false?"skip":"waiting"}`}>{screenChangeTest.change_percent!==undefined?<><strong>{screenChangeTest.change_percent.toFixed(2)}% de mudança</strong><span>Limite atual: {settings.change_threshold_percent}% · {screenChangeTest.would_capture?"Capturaria":"Não capturaria"}</span><i><b style={{width:Math.min(100,screenChangeTest.change_percent/Math.max(settings.change_threshold_percent,0.1)*100)+"%"}}/></i></>:<span>{screenChangeTest.message}</span>}</div>}</section>}</>}
      {(settingsTab==="ai"||settingsTab==="video")&&videoSettings&&<VideoSettingsTab tab={settingsTab} settings={videoSettings} patterns={videoPatterns} models={ollamaModels} ollamaOnline={ollamaOnline} busy={busy} advanced={videoAdvanced} onSettings={setVideoSettings} onPatterns={setVideoPatterns}/>} 
      {settingsTab==="video"&&videoSettings&&<AppCaptureRules settings={videoSettings} patterns={videoPatterns} advanced={videoAdvanced} onAdvanced={setVideoAdvanced} onSettings={setVideoSettings} onPatterns={setVideoPatterns}/>} 
      </div>
      <footer><button className="ghost" disabled={savingSettings} onClick={() => setPanel(null)}>Cancelar</button><button className="primary" disabled={savingSettings||!schedule||!storage||!videoSettings||!cleanupSettings||!storageRoot.trim()} onClick={saveAllSettings}>{savingSettings?"Salvando…":"Salvar configurações"}</button></footer>
    </Modal>}

    {panel === "privacy" && <Modal title="Janelas sensíveis" onClose={() => setPanel(null)}>
      <p className="help">Uma expressão por linha. A captura é descartada quando o título ou a classe da janela ativa corresponder.</p>
      <textarea className="patterns" value={patterns} onChange={e => setPatterns(e.target.value)} spellCheck={false}/>
      <footer><button className="ghost" onClick={() => setPanel(null)}>Cancelar</button><button className="primary" disabled={busy} onClick={savePrivacy}>Salvar lista</button></footer>
    </Modal>}

    
    
    
    {selectedHour&&<Modal title={`${selectedHour.key.slice(11)}:00 — detalhes da hora`} onClose={()=>setSelectedHour(null)}>{selectedHour.summary&&<div className="hour-detail-summary"><h3>{selectedHour.summary.title}</h3><p>{selectedHour.summary.narrative}</p><small>Resumido por {selectedHour.summary.model}</small></div>}<div className="hour-detail-list">{selectedHour.items.map(item=><CaptureCard key={item.id} item={item} onOpen={(url,name,text,model,itemKind,capture)=>{setShowLightboxVoices(false);setVoiceProfiles(null);setLightbox({url,name,text,model,kind:itemKind,capture})}} onDelete={deleteMemoryItem} disabled={busy}/>)}</div>{!selectedHour.items.length&&<div className="result">Nenhum registro detalhado encontrado.</div>}</Modal>}

    {palette&&<div className="palette-overlay" onClick={()=>setPalette(false)}>
      <div className="palette" onClick={event=>event.stopPropagation()}>
        <input autoFocus value={paletteQuery} placeholder="Buscar memórias ou executar uma ação…" onChange={event=>setPaletteQuery(event.target.value)} onKeyDown={event=>{if(event.key==="Enter"&&paletteQuery.trim()){setQuery(paletteQuery);setView("busca");setPalette(false)}}}/>
        {!!paletteItems.length&&<div className="palette-section"><span className="palette-label">Memórias</span>
          {paletteItems.map(item=><button className="palette-item" key={item.id} onClick={()=>{setPalette(false);setShowLightboxVoices(false);setVoiceProfiles(null);setLightbox({url:item.image_url||item.paired_image_url,name:item.source_path.split("/").pop()||item.title,text:item.text,model:item.model,kind:item.kind,capture:item})}}><b>{item.kind==="screen"?"▣":"♪"}</b><span>{item.title}</span><small>{new Date(item.captured_at).toLocaleString("pt-BR",{day:"2-digit",month:"2-digit",hour:"2-digit",minute:"2-digit"})}</small></button>)}
          <button className="palette-item see-all" onClick={()=>{setQuery(paletteQuery);setView("busca");setPalette(false)}}><b>⌕</b><span>Ver todos os resultados na Busca</span><small>Enter</small></button>
        </div>}
        <div className="palette-section"><span className="palette-label">Ações</span>
          <button className="palette-item" disabled={busy||!memoryDays.length} onClick={()=>{setPalette(false);void forceSummary()}}><b>✦</b><span>Gerar resumo de {new Date(`${selectedDay}T12:00:00`).toLocaleDateString("pt-BR")}</span></button>
          <button className="palette-item" disabled={busy} onClick={()=>{setPalette(false);void generateHours()}}><b>◷</b><span>Gerar linha do tempo e atividades</span></button>
          <button className="palette-item" disabled={busy||!status||automaticCapturePause} onClick={()=>{setPalette(false);void toggleCapture()}}><b>{status?.capturing?"❚❚":"▶"}</b><span>{automaticCapturePause?"Retomada automática":status?.capturing?"Pausar captura":"Retomar captura"}</span></button>
          <button className="palette-item" onClick={()=>{setPalette(false);openQueuePanel()}}><b>◍</b><span>Abrir fila de processamento</span>{queueCount>0&&<small>{queueCount} na fila</small>}</button>
        </div>
      </div>
    </div>}

    {lightbox && <div className="lightbox" onClick={()=>setLightbox(null)}><button onClick={()=>setLightbox(null)}>×</button><div className={`lightbox-content ${lightbox.url?"":"text-only"} ${lightbox.kind==="audio"?"audio-view":""}`} onClick={e=>e.stopPropagation()}>{lightbox.url&&<img src={lightbox.url}/>}<div className="lightbox-caption"><strong>{lightbox.name}</strong>{lightbox.kind==="audio"&&lightbox.capture&&<div className="voice-corner-actions"><button className="profile-list-button" onClick={openVoiceProfiles}>Perfis salvos</button>{!!lightbox.capture.speakers?.length&&<button className={`voice-corner-button ${showLightboxVoices?"active":""}`} onClick={()=>{setVoiceProfiles(null);setShowLightboxVoices(value=>!value)}}>Pessoas · {voiceGroups(lightbox.capture).length}</button>}</div>}{voiceProfiles&&<SavedVoiceProfiles profiles={voiceProfiles} onDelete={removeVoiceProfile} onClose={()=>setVoiceProfiles(null)}/>} {showLightboxVoices&&lightbox.capture&&<VoiceIdentityPanel capture={lightbox.capture} onIdentify={identifyLightboxVoice}/>} {lightbox.kind==="audio"&&lightbox.capture?<SyncedAudioPlayer capture={lightbox.capture} onIdentify={identifyLightboxVoice}/>:lightbox.text&&<p>{lightbox.text}</p>}{lightbox.model&&<small>Processado por {lightbox.model}</small>}</div></div></div>}
  </div>;
}

createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
