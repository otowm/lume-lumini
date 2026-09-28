// npm run test:settings (once: npx playwright install chromium)
import assert from 'node:assert/strict';
import {chromium} from 'playwright';
import {preview} from 'vite';
const server = process.env.SETTINGS_TEST_URL ? null : await preview({preview:{host:'127.0.0.1',port:0}});
const base = process.env.SETTINGS_TEST_URL || `http://127.0.0.1:${server.httpServer.address().port}`;
let browser;
try {
  browser = await chromium.launch({headless:true});
  for (const mode of ['lumini', 'completo']) {
    const page = await browser.newPage();
    page.on("pageerror", error => console.error(error.message));
    page.setDefaultTimeout(5000);
    const writes = [];
    let updates = {current:'a'.repeat(40),latest:'b'.repeat(40),title:'Correção de gravação',available:true,can_prepare:true,pending:'',download_url:'https://github.com/otowm/lume-lumini/archive/refs/heads/main.zip'};
    let prepareCalls = 0;
    const screen = {capture_mode:'interval',interval_seconds:30,change_poll_seconds:5,change_threshold_percent:5,change_max_interval_seconds:60,max_geometry:'1920x1080',split_monitors:false,active_monitor_only:true,privacy_fail_closed:true};
    let video = {enabled:true,codec:'hevc',capture_mode:'continuous',replay_seconds:60,fps:60,geometry:'1920x1080',segment_seconds:60,sample_frames:8,sample_geometry:'960x540',retention_minutes:60,delete_after_description:false,pause_other_captures:true,focus_grace_seconds:20,analysis_profile:'detailed',scan_interval_seconds:2,max_keyframes:80,patterns:[],pattern_modes:{},pattern_fps:{},pattern_geometry:{},pattern_sources:{},marker_hotkey:'F8',hotkey_hold_seconds:0.6,marker_preroll_seconds:8,hud_enabled:true,hud_placement:'second',hud_corner:'top-right',hud_hotkey:'Ctrl+Shift+F8',hud_sound:true,resolve_fps:0,resolve_start_timecode:'01:00:00:00'};
    let storage = {root:'/tmp/lumini-test',disk:{free:100000,total:200000},candidates:[],restart_required:false};
    let audio = {mic_denoise_enabled:true,mic_gate_threshold_db:-45};
    await page.addInitScript(mode=>{localStorage.setItem('lume-mode',mode);sessionStorage.setItem('lume-active-view','videos')},mode);
    await page.route('**/api/**', async route => {
      const request = route.request(), path = new URL(request.url()).pathname;
      if(path.startsWith('/api/updates')) {
        if(path.endsWith('/prepare')) {prepareCalls++;updates={...updates,pending:updates.latest}}
        if(path.endsWith('/cancel')) updates={...updates,pending:''};
        await route.fulfill({json:updates});return;
      }
      const put = request.method()==='PUT';
      if(put)writes.push({path,body:request.postDataJSON()});
      if(mode==='lumini' && /\/(schedule|prompts|ollama|pipeline|captures|days|summary|timeline|activities)(\/|$)/.test(path)) {
        await route.fulfill({status:409,json:{detail:'Indisponível no Lumini'}});return;
      }
      let data = {items:[],hours:[],source_hours:[],summary:null,counts:{},running:false,total:0};
      if(path==='/api/status')data={mode,settings:screen,capturing:false,audio:{active:false},screen:{active:false},video:{enabled:true,recording:false,mode:'clips'},files:{audio:{count:0,bytes:0},screen:{count:0,bytes:0}},storage:{bytes:0,disk_free:100000},idle:{supported:false}};
      if(path==='/api/settings/video'){if(put)video=request.postDataJSON();data=video}
      if(path==='/api/settings/storage'){if(put)storage={...storage,...request.postDataJSON()};data=storage}
      if(path==='/api/settings/audio'){if(put)audio=request.postDataJSON();data=audio}
      if(path==='/api/settings/audio/mic-level')data={ok:true,peak_db:-20,silent:false}
      if(path==='/api/settings/cleanup')data={enabled:false};
      if(path==='/api/game-icons/retry')data={ok:true,retrying:2};
      if(path==='/api/test/video-window')data={ok:true,window_id:'',title:'Jogo Novo',window_class:'jogonovo.exe',executable:'jogonovo.exe',monitor_resolution:'1366x768',info:'',matched:false,matched_pattern:''};
      if(path==='/api/settings/schedule')data={time:'03:00',enabled:false};
      if(path==='/api/ollama/models')data={online:false,models:[]};
      await route.fulfill({json:data});
    });
    await page.goto(base);
    await page.getByRole('button',{name:'Ajustes',exact:true}).click();
    await page.getByRole('radio',{name:/Clipes/}).check();
    await page.getByRole('button',{name:'Detectar atalho',exact:true}).click();
    await page.keyboard.press('Control+[');
    assert.equal(await page.getByLabel('Atalho',{exact:true}).inputValue(),'Ctrl+[');
    await page.getByLabel(/Onde aparecer/).selectOption('game');
    const save = page.getByRole('button',{name:'Salvar configurações',exact:true});
    assert.equal(await save.isEnabled(),true,`${mode}: Salvar deve estar habilitado após editar a HUD`);
    await save.click();
    await page.waitForFunction(()=>!document.querySelector('.settings-modal'));
    assert.equal(writes.find(item=>item.path==='/api/settings/video')?.body.hud_placement,'game');
    assert.equal(video.capture_mode,'clips');
    assert.equal(video.marker_hotkey,'Ctrl+[');
    assert.equal(video.marker_key_code,'BracketLeft');
    assert.equal(writes.some(item=>item.path==='/api/settings/schedule'),mode==='completo');
    await page.getByRole('button',{name:'Ajustes',exact:true}).click();
    assert.equal(await page.getByLabel(/Onde aparecer/).inputValue(),'game');
    assert.equal(await page.getByLabel('Atalho',{exact:true}).inputValue(),'Ctrl+[');
    await page.getByRole('button',{name:'Detectar atalho',exact:true}).click();
    await page.keyboard.press('Escape');
    assert.equal(await page.getByLabel('Atalho',{exact:true}).inputValue(),'Ctrl+[');
    await page.getByRole('button',{name:'Armazenamento',exact:true}).click();
    await page.getByLabel('Pasta-raiz',{exact:true}).fill('');
    assert.equal(await save.isDisabled(),true,'Pasta vazia deve bloquear o salvamento');
    await page.getByLabel('Pasta-raiz',{exact:true}).fill('/tmp/another-folder');
    await save.click();
    await page.waitForFunction(()=>!document.querySelector('.settings-modal'));
    assert.equal(storage.root,'/tmp/another-folder');
    if(mode==='lumini') {
      assert.equal(prepareCalls,0,'Checar versões nunca deve preparar uma atualização sozinho');
      await page.getByRole('button',{name:'Atualização disponível',exact:true}).click();
      await page.getByRole('button',{name:'Preparar atualização',exact:true}).click();
      await page.getByText('Reinicie o computador para instalar a versão preparada antes de ligar o gravador.').waitFor();
      assert.equal(prepareCalls,1);
      await page.getByRole('button',{name:'Cancelar atualização',exact:true}).click();
      await page.getByRole('button',{name:'Preparar atualização',exact:true}).waitFor();
      assert.equal(updates.pending,'');
    }
    console.log(`${mode}: edição de vídeo, reabertura, validação e armazenamento OK`);
    {
      // O microfone vale para os vídeos, então mora na aba Vídeo seletivo e
      // aparece também no Lumini, que não tem a aba Captura.
      await page.getByRole('button',{name:'Ajustes',exact:true}).click();
      await page.getByRole('button',{name:'Vídeo seletivo',exact:true}).click();
      // Nível ao vivo e limite dividem a mesma barra: o nível chega como
      // --level no trilho, e o texto mostra o valor lido.
      await page.getByText('Agora: -20 dB · gravando').waitFor();
      assert.equal(await page.locator('.mic-gate-track').evaluate(el=>el.style.getPropertyValue('--level')),'80%');
      await page.getByLabel(/Suprimir ruído de fundo/).uncheck();
      await page.locator('.mic-gate-track input[type=range]').evaluate(el=>{
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(el, '-30');
        el.dispatchEvent(new Event('input', {bubbles:true}));
      });
      await save.click();
      await page.waitForFunction(()=>!document.querySelector('.settings-modal'));
      assert.equal(audio.mic_denoise_enabled,false);
      assert.equal(audio.mic_gate_threshold_db,-30);
      console.log(`${mode}: microfone (ruído e portão de volume) salvo OK`);
    }
    if(mode==='lumini') {
      // Jogo novo entra na resolução do monitor dele, não no 1920x1080 padrão.
      await page.getByRole('button',{name:'Ajustes',exact:true}).click();
      await page.getByRole('button',{name:'+ Aplicativo aberto',exact:true}).click();
      await page.getByText('Monitor do jogo: 1366x768').waitFor({timeout:8000});
      await page.getByRole('button',{name:'Sim, adicionar',exact:true}).click();
      await save.click();
      await page.waitForFunction(()=>!document.querySelector('.settings-modal'));
      assert.equal(video.pattern_geometry['exe:^jogonovo\\.exe$'],'1366x768');
      console.log(`${mode}: app novo gravado na resolução do monitor OK`);
      await page.getByRole('button',{name:'Ajustes',exact:true}).click();
      await page.getByRole('button',{name:'Buscar de novo os que faltam',exact:true}).click();
      await page.getByText('Buscando de novo 2 jogos que estavam sem ícone.').waitFor();
      console.log(`${mode}: busca de ícones que faltam OK`);
    }
    await page.close();
  }
} finally {
  await browser?.close();
  if(server) await new Promise(resolve=>server.httpServer.close(resolve));
}
