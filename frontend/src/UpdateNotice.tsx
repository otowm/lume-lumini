import {useEffect, useState} from "react";

type UpdateStatus = {
  current: string; latest?: string; title?: string; available: boolean;
  can_prepare: boolean; reason?: string; error?: string; pending?: string;
  message?: string; download_url: string;
};

async function request(path: string, options?: RequestInit): Promise<UpdateStatus> {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || "Não foi possível concluir a atualização.");
  return body;
}

export function UpdateNotice({recording}: {recording: boolean}) {
  const [status, setStatus] = useState<UpdateStatus|null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [open, setOpen] = useState(false);
  useEffect(()=>{
    let disposed = false;
    const check = ()=>request('/api/updates').then(next=>{if(!disposed)setStatus(next)}).catch(()=>{});
    void check();
    const timer = setInterval(()=>void check(), 6*60*60*1000);
    return ()=>{disposed=true; clearInterval(timer)};
  },[]);
  const act = async (action: 'check'|'prepare'|'cancel')=>{
    setBusy(true); setError("");
    try {
      if(action==='check')setStatus(await request('/api/updates?force=true'));
      else {
        await request(`/api/updates/${action}`, {method:'POST',headers:{'Content-Type':'application/json'},
          body: action==='prepare'?JSON.stringify({version:status?.latest}):undefined});
        setStatus(await request('/api/updates'));
      }
    } catch(error) {setError(error instanceof Error?error.message:'Falha ao atualizar.');}
    finally {setBusy(false)}
  };
  return <section className="update-notice">
    <button className="ghost" aria-expanded={open} onClick={()=>setOpen(!open)}>
      {status?.pending?'Atualização preparada':status?.available?'Atualização disponível':'Atualizações'}
    </button>
    {open&&<div>
      {status?.title&&status.available&&<p>{status.title}</p>}
      {status?.pending?<>
        <p>Reinicie o computador para instalar a versão preparada antes de ligar o gravador.</p>
        <button disabled={busy} onClick={()=>void act('cancel')}>Cancelar atualização</button>
      </>:<>
        {status?.available&&status.can_prepare&&<>
          <p>A instalação acontece na próxima inicialização. Suas preferências e gravações serão mantidas.</p>
          <button className="primary" disabled={busy||recording} onClick={()=>void act('prepare')}>Preparar atualização</button>
          {recording&&<p>Saia do jogo e espere a gravação terminar para atualizar.</p>}
        </>}
        {status?.reason&&<p>{status.reason}</p>}
        {status?.available&&!status.can_prepare&&<a href={status.download_url}>Baixar nova versão</a>}
        {status&&!status.available&&!status.error&&<p>Você está na versão mais recente.</p>}
        <button className="ghost" disabled={busy} onClick={()=>void act('check')}>{busy?'Aguarde…':'Verificar atualizações'}</button>
      </>}
      {(error||status?.error)&&<p role="alert">{error||status?.error}</p>}
    </div>}
  </section>;
}
