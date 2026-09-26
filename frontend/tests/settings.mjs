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
    const screen = {capture_mode:'interval',interval_seconds:30,change_poll_seconds:5,change_threshold_percent:5,change_max_interval_seconds:60,max_geometry:'1920x1080',split_monitors:false,active_monitor_only:true,privacy_fail_closed:true};
    let video = {enabled:true,codec:'hevc',capture_mode:'continuous',replay_seconds:60,fps:60,geometry:'1920x1080',segment_seconds:60,sample_frames:8,sample_geometry:'960x540',retention_minutes:60,delete_after_description:false,pause_other_captures:true,focus_grace_seconds:20,analysis_profile:'detailed',scan_interval_seconds:2,max_keyframes:80,patterns:[],pattern_modes:{},pattern_fps:{},pattern_geometry:{},pattern_sources:{},marker_hotkey:'F8',hotkey_hold_seconds:0.6,marker_preroll_seconds:8,hud_enabled:true,hud_placement:'second',hud_corner:'top-right',hud_hotkey:'Ctrl+Shift+F8',hud_sound:true,resolve_fps:0,resolve_start_timecode:'01:00:00:00'};
    let storage = {root:'/tmp/lumini-test',disk:{free:100000,total:200000},candidates:[],restart_required:false};
    await page.addInitScript(mode=>{localStorage.setItem('lume-mode',mode);sessionStorage.setItem('lume-active-view','videos')},mode);
    await page.route('**/api/**', async route => {
      const request = route.request(), path = new URL(request.url()).pathname;
      const put = request.method()==='PUT';
      if(put)writes.push({path,body:request.postDataJSON()});
      if(mode==='lumini' && /\/(schedule|prompts|ollama|pipeline|captures|days|summary|timeline|activities)(\/|$)/.test(path)) {
        await route.fulfill({status:409,json:{detail:'Indisponível no Lumini'}});return;
      }
      let data = {items:[],hours:[],source_hours:[],summary:null,counts:{},running:false,total:0};
      if(path==='/api/status')data={mode,settings:screen,capturing:false,audio:{active:false},screen:{active:false},video:{enabled:true,recording:false,mode:'clips'},files:{audio:{count:0,bytes:0},screen:{count:0,bytes:0}},storage:{bytes:0,disk_free:100000},idle:{supported:false}};
      if(path==='/api/settings/video'){if(put)video=request.postDataJSON();data=video}
      if(path==='/api/settings/storage'){if(put)storage={...storage,...request.postDataJSON()};data=storage}
      if(path==='/api/settings/cleanup')data={enabled:false};
      if(path==='/api/settings/schedule')data={time:'03:00',enabled:false};
      if(path==='/api/ollama/models')data={online:false,models:[]};
      await route.fulfill({json:data});
    });
    await page.goto(base);
    await page.getByRole('button',{name:'Ajustes',exact:true}).click();
    await page.getByLabel(/Modo de captura/).selectOption('clips');
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
    console.log(`${mode}: edição de vídeo, reabertura, validação e armazenamento OK`);
    await page.close();
  }
} finally {
  await browser?.close();
  if(server) await new Promise(resolve=>server.httpServer.close(resolve));
}
