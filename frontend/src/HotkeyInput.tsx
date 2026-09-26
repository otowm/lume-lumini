import {useRef, useState} from "react";
import type {KeyboardEvent} from "react";

export function HotkeyInput({value, onChange}: {
  value: string;
  onChange: (value: string, physicalCode: string) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [listening, setListening] = useState(false);
  const [message, setMessage] = useState("");

  const capture = (event: KeyboardEvent<HTMLInputElement>) => {
    if (!listening) return;
    event.stopPropagation();
    if (event.key === "Tab") {setListening(false); return;}
    event.preventDefault();
    if (event.key === "Escape") {setListening(false); setMessage(""); return;}
    if (["Control", "Shift", "Alt", "Meta"].includes(event.key)) return;
    if (event.repeat) return;
    if (!/^(F([1-9]|1[0-2])|[a-zA-Z0-9\[\]])$/.test(event.key) || event.getModifierState("AltGraph")) {
      setMessage("Use F1–F12, letras, números ou [ e ], com Ctrl, Alt, Shift ou Super.");
      return;
    }
    const modifiers = [event.ctrlKey && "Ctrl", event.altKey && "Alt",
      event.shiftKey && "Shift", event.metaKey && "Win"].filter(Boolean);
    const code = /^(Key[A-Z]|Digit[0-9]|F([1-9]|1[0-2])|BracketLeft|BracketRight)$/.test(event.code) ? event.code : "";
    onChange([...modifiers, event.key.toUpperCase()].join("+"), code);
    setListening(false);
    setMessage("");
  };

  return <div className="hotkey-field">
    <label><span>Atalho</span><input ref={input} value={listening ? "Pressione o atalho…" : value}
      readOnly={listening} onKeyDown={capture} onBlur={()=>setListening(false)}
      onChange={event=>onChange(event.target.value.replace(/\s/g, ""), "")}/></label>
    <button type="button" className="secondary" onClick={()=>{
      setListening(true); setMessage(""); input.current?.focus();
    }}>Detectar atalho</button>
    <small aria-live="polite">{message || (listening ? "Pressione a combinação desejada. Esc cancela." : "Clique em Detectar atalho e pressione as teclas juntas.")}</small>
  </div>;
}
