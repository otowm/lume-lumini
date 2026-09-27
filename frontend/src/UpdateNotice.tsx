import {useEffect, useState} from "react";

type UpdateStatus = {
  current: string; latest?: string; title?: string; available: boolean;
  can_prepare: boolean; can_install_now?: boolean; reason?: string; error?: string; pending?: string;
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
  const [installing, setInstalling] = useState(false);
  useEffect(()=>{
    let disposed = false;
    const check = ()=>request('/api/updates').then(next=>{if(!disposed)setStatus(next)}).catch(()=>{});
    void check();
    const timer = setInterval(()=>void check(), 6*60*60*1000);
    return ()=>{disposed=true; clearInterval(timer)};
  },[]);
  // O backend cai durante a instalação. Espera ele voltar já na versão
  // preparada e recarrega a página, que também mudou.
  const waitForNewVersion = async (target: string)=>{
    const deadline = Date.now() + 4*60*1000;
    let wentDown = false;
    while (Date.now() < deadline) {
      await new Promise(resolve=>setTimeout(resolve, 2000));
      try {
        const next = await request('/api/updates');
        if (next.current === target) { window.location.reload(); return; }
        // Voltou na versão antiga: a instalação falhou e o erro está no estado.
        if (wentDown) {
          setStatus(next); setInstalling(false);
          setError(next.error || "A atualização não foi instalada. Reinicie o computador para tentar de novo.");
          return;
        }
      } catch { wentDown = true; }
    }
    setInstalling(false);
    setError("A instalação está demorando. Recarregue a página em instantes; se o erro continuar, reinicie o computador.");
  };
  const installNow = async ()=>{
    setBusy(true); setError("");
    try {
      const target = status?.pending || status?.latest || "";
      if (!status?.pending) await request('/api/updates/prepare', {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({version:target})});
      await request('/api/updates/install', {method:'POST'});
      setInstalling(true);
      await waitForNewVersion(target);
    } catch(error) {
      setError(error instanceof Error?error.message:'Falha ao atualizar.');
      setStatus(await request('/api/updates').catch(()=>status));
    } finally {setBusy(false)}
  };
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
      {installing?<p role="status">Instalando… o gravador para por alguns segundos e a página recarrega sozinha.</p>:status?.pending?<>
        <p>{status.can_install_now?'Instale agora ou reinicie o computador: a versão preparada entra antes de o gravador ligar.':'Reinicie o computador para instalar a versão preparada antes de ligar o gravador.'}</p>
        {status.can_install_now&&<button className="primary" disabled={busy||recording} onClick={()=>void installNow()}>Instalar agora</button>}
        <button disabled={busy} onClick={()=>void act('cancel')}>Cancelar atualização</button>
        {recording&&<p>Saia do jogo e espere a gravação terminar para atualizar.</p>}
      </>:<>
        {status?.available&&status.can_prepare&&<>
          <p>{status.can_install_now?'O gravador para por alguns segundos durante a instalação.':'A instalação acontece na próxima inicialização.'} Suas preferências e gravações serão mantidas.</p>
          {status.can_install_now&&<button className="primary" disabled={busy||recording} onClick={()=>void installNow()}>Instalar agora</button>}
          <button className={status.can_install_now?'ghost':'primary'} disabled={busy||recording} onClick={()=>void act('prepare')}>{status.can_install_now?'Instalar na próxima inicialização':'Preparar atualização'}</button>
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
