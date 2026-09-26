import { useEffect, useId, useRef, useState } from "react";
import "./day-picker.css";

type MemoryDay = { day: string; count: number };
const dateOf = (day: string) => new Date(`${day}T12:00:00`);
const monthLabel = (month: string) => dateOf(`${month}-01`).toLocaleDateString("pt-BR", { month: "long", year: "numeric" });
const fullLabel = (day: string) => dateOf(day).toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long", year: "numeric" });

export function DayPicker({ days, value, onChange }: { days: MemoryDay[]; value: string; onChange: (day: string) => void }) {
  const [open, setOpen] = useState(false);
  const [month, setMonth] = useState(value.slice(0, 7));
  const root = useRef<HTMLDivElement>(null);
  const trigger = useRef<HTMLButtonElement>(null);
  const panel = useRef<HTMLDivElement>(null);
  const id = useId();
  const today = new Date().toLocaleDateString("sv-SE");
  const available = new Map(days.map(day => [day.day, day.count]));
  const ordered = [...available.keys()].sort();
  const months = [...new Set(ordered.map(day => day.slice(0, 7)))];
  const monthIndex = months.indexOf(month);
  const dayIndex = ordered.indexOf(value);
  const first = dateOf(`${month}-01`);
  const length = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
  const close = (restoreFocus = false) => { setOpen(false); if (restoreFocus) trigger.current?.focus(); };
  const choose = (day: string) => { onChange(day); close(true); };

  useEffect(() => {
    if (!open) return;
    panel.current?.querySelector<HTMLButtonElement>('button[aria-pressed="true"]')?.focus();
    const dismiss = (event: PointerEvent) => {
      if (event.target instanceof Node && !root.current?.contains(event.target)) setOpen(false);
    };
    document.addEventListener("pointerdown", dismiss);
    return () => document.removeEventListener("pointerdown", dismiss);
  }, [open]);

  return <div className="memory-date-picker" ref={root} onBlur={event => {
    if (event.relatedTarget instanceof Node && !event.currentTarget.contains(event.relatedTarget)) close();
  }} onKeyDown={event => {
    if (event.key === "Escape" && open) { event.preventDefault(); event.stopPropagation(); close(true); }
  }}>
    <button className="day-step" disabled={dayIndex <= 0} onClick={() => choose(ordered[dayIndex - 1])} aria-label="Dia anterior com registros">‹</button>
    <button className="memory-date-trigger" ref={trigger} disabled={!days.length} aria-haspopup="dialog" aria-expanded={open} aria-controls={id}
      onClick={() => { setMonth(value.slice(0, 7)); setOpen(!open); }}>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M7 3v4m10-4v4M3 11h18"/></svg>
      <span>{dateOf(value).toLocaleDateString("pt-BR", { day: "numeric", month: "short", year: "numeric" })}<small>{days.length ? `${dateOf(value).toLocaleDateString("pt-BR", { weekday: "long" })} · ${available.get(value) ?? 0} registros` : "Nenhum dia com registros"}</small></span>
      <span aria-hidden="true">⌄</span>
    </button>
    <button className="day-step" disabled={dayIndex < 0 || dayIndex >= ordered.length - 1} onClick={() => choose(ordered[dayIndex + 1])} aria-label="Próximo dia com registros">›</button>
    {open && <div className="memory-calendar" ref={panel} id={id} role="dialog" aria-label="Escolher dia">
      <div className="memory-calendar-heading"><div><strong>Escolher dia</strong><p>Revisite suas memórias</p></div><button className="day-step" aria-label="Fechar calendário" onClick={() => close(true)}>×</button></div>
      <div className="memory-calendar-month">
        <button className="day-step" aria-label="Mês anterior com registros" disabled={monthIndex <= 0} onClick={() => setMonth(months[monthIndex - 1])}>‹</button>
        <select aria-label="Mês e ano" value={month} onChange={event => setMonth(event.target.value)}>{months.map(item => <option value={item} key={item}>{monthLabel(item)}</option>)}</select>
        <button className="day-step" aria-label="Próximo mês com registros" disabled={monthIndex < 0 || monthIndex >= months.length - 1} onClick={() => setMonth(months[monthIndex + 1])}>›</button>
      </div>
      <div className="memory-calendar-week" aria-hidden="true">{["D", "S", "T", "Q", "Q", "S", "S"].map((label, index) => <span key={index}>{label}</span>)}</div>
      <div className="memory-calendar-days">
        {Array.from({ length: first.getDay() }, (_, index) => <span key={`blank-${index}`}/>)}
        {Array.from({ length }, (_, index) => {
          const day = `${month}-${String(index + 1).padStart(2, "0")}`;
          const count = available.get(day);
          return <button key={day} disabled={count === undefined} aria-pressed={day === value} aria-current={day === today ? "date" : undefined}
            aria-label={`${fullLabel(day)} · ${count === undefined ? "sem registros" : `${count} registros`}`} title={count === undefined ? "Sem registros" : `${count} registros`}
            onClick={() => choose(day)}><span>{index + 1}</span>{count !== undefined && <i aria-hidden="true"/>}</button>;
        })}
      </div>
      <div className="memory-calendar-legend"><i/> Dias com registros <span>Contorno: hoje</span></div>
      <div className="memory-calendar-shortcuts"><button disabled={!available.has(today)} onClick={() => choose(today)}>Hoje</button><button disabled={!ordered.length} onClick={() => choose(ordered[ordered.length - 1])}>Mais recente</button></div>
    </div>}
  </div>;
}
