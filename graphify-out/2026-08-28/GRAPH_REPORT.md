# Graph Report - lume  (2026-08-28)

## Corpus Check
- 56 files · ~92,829 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1530 nodes · 3864 edges · 81 communities (71 shown, 10 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 378 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `da259cb6`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ConfigTests
- src/api.ts
- package.json
- compilerOptions
- winvideo.py
- obs.py
- record
- Handoff: Lume — app de memória de tela & áudio
- VideoLoop
- connect
- Lume no Windows
- test_main.py
- RegionGroupingTests
- winscreen.py
- WindowsServiceManager
- game-video-loop
- ActionResult
- AGENTS.md
- LinuxCaptureBackend
- initialize
- Path
- install-audio-intelligence
- audio_intelligence.py
- capture-frame
- Monitor
- add-video-marker
- WasapiError
- install-captura-dia.sh
- post
- RemapToSourceTests
- audio-bus.sh
- src-backup-2026-08-09/api.ts
- src-backup-2026-08-09/main.tsx
- get
- _call
- capture-loop
- main.py
- test_services.py
- run
- grava-audio.sh
- install-lume.sh
- install-user.sh
- winrecord.py
- ImageDiffTests
- LinuxHudCollector
- media_source_key
- _Growth
- capture_frames
- hudsource.py
- Hud
- ServiceManager
- src/main.tsx
- App
- videoTime
- filter_hallucinated_segments
- WasapiCapture
- videoTime
- merge_transcript_sources
- pipeline.py
- App
- HudPanel
- HudStateTests
- wasapi.py
- HudPlacementTests
- WindowsHudCollector
- runtime_dir
- .action
- windows_startup.py
- _resolve
- SpeechRegionTests
- Path
- _event_fields
- services.py
- ._start
- HudFrameRateTests
- recover_json_from_thinking

## God Nodes (most connected - your core abstractions)
1. `ActionResult` - 85 edges
2. `connect()` - 84 edges
3. `ConfigTests` - 83 edges
4. `HudSnapshot` - 53 edges
5. `SystemdServiceManager` - 52 edges
6. `VideoLoop` - 50 edges
7. `Monitor` - 48 edges
8. `Hud` - 46 edges
9. `Meter` - 46 edges
10. `WindowsCaptureBackend` - 42 edges

## Surprising Connections (you probably didn't know these)
- `ScreenSettings` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `SensitiveWindows` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `PipelineRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `ProcessFileRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `ScreenSequenceTestRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py

## Import Cycles
- None detected.

## Communities (81 total, 10 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.06
Nodes (9): captured_video_session(), Lê a identidade portátil deixada pelo gravador seletivo. Vídeos antigos só têm…, daily_narrative_target(), Valida referências da IA e protege os arquivos escolhidos., validate_relevant_media(), ConfigTests, Path, skipUnless (+1 more)

### Community 1 - "src/api.ts"
Cohesion: 0.07
Nodes (28): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+20 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "winvideo.py"
Cohesion: 0.07
Nodes (33): PrivacyTests, CaptureBackend, matched_sensitive_pattern(), parse_video_app_rule(), ABC, Path, Interface comum de captura, independente de sistema operacional. Cada SO…, Primeiro padrão sensível (regex, case-insensitive) que casa com a janela. Mesma… (+25 more)

### Community 5 - "obs.py"
Cohesion: 0.06
Nodes (57): any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), _encode_field(), ensure_scene(), find_installation() (+49 more)

### Community 6 - "record"
Cohesion: 0.17
Nodes (10): ProcessLoopbackCapture, Loopback que inclui ou exclui a árvore de um processo do Windows., Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record() (+2 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.07
Nodes (23): log(), MarkerHotkey, Atalhos globais no Windows, registrados fora de qualquer janela. No Linux o…, Atalho global que chama ``on_press`` a cada acionamento., foreground_details(), log(), looks_blank(), main() (+15 more)

### Community 9 - "connect"
Cohesion: 0.09
Nodes (45): connect(), row_dict(), _audio_channels(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_screen_sequence(), cancel_video_analysis() (+37 more)

### Community 10 - "Lume no Windows"
Cohesion: 0.07
Nodes (24): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+16 more)

### Community 11 - "test_main.py"
Cohesion: 0.10
Nodes (17): Uma unit transitória coletada equivale a um job já parado., stop_target_is_already_gone(), VideoSettings, private_context_terms(), Pico de um WAV PCM 16 bits, em dBFS. ``-inf`` vira o piso -99., A faixa está muda o bastante para transcrevê-la ser desperdício? Numa sessão…, safe_research_query(), short_video_analysis_prompt() (+9 more)

### Community 12 - "RegionGroupingTests"
Cohesion: 0.31
Nodes (5): group_regions(), Agrupa trechos vizinhos em blocos que caibam numa janela do whisper. Dois…, Blocos que enchem uma janela do whisper sem esticar o eixo do tempo. O whisper…, É o teto que impede um erro de 1 s virar 20 s ao voltar ao original., RegionGroupingTests

### Community 13 - "winscreen.py"
Cohesion: 0.12
Nodes (16): Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., _as_bool(), _as_float(), _as_int(), main(), _monitor_key(), _parse_config(), Path (+8 more)

### Community 14 - "WindowsServiceManager"
Cohesion: 0.18
Nodes (5): Supervisor: mantém os processos de captura vivos e agenda o processamento. Vive…, Anota que a captura deve (ou não) voltar na próxima abertura do Lume. No Linux…, Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., Combine selective-video and user-idle pauses without racing them. Audio and…, WindowsServiceManager

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "ActionResult"
Cohesion: 0.16
Nodes (6): ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API., SystemdFallbackTests, VideoReplayClipTests

### Community 18 - "LinuxCaptureBackend"
Cohesion: 0.12
Nodes (9): LinuxAudioTrackTests, Gravação em faixas separadas (3 canais) no backend Linux., AudioConfig, argv do ``ffmpeg`` que grava mic + saída do sistema num único WAV. O comando…, Como gravar áudio: fontes e formato do WAV alvo do whisper., LinuxCaptureBackend, Path, argv do ffmpeg que grava mic + Discord + sistema num WAV de 3 canais. Mesmo… (+1 more)

### Community 19 - "initialize"
Cohesion: 0.11
Nodes (24): initialize(), _activity_groups(), apply_exact_game_durations(), discover(), game_activity_rows(), generate_hourly_summaries(), generate_summary(), generate_visual_activities() (+16 more)

### Community 20 - "Path"
Cohesion: 0.11
Nodes (27): _delete_media_sidecars(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), migrate_legacy_cache_file(), probe_video_audio_tracks(), probe_video_duration(), Path (+19 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.14
Nodes (22): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+14 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "Monitor"
Cohesion: 0.16
Nodes (8): Monitor, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Um monitor físico: rótulo estável + geometria em pixels do desktop., Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga. Dois formatos de saída…, Dispositivo dshow capaz de gravar a saída, se algum existir. Só diagnóstico: a…, WindowsCaptureBackend

### Community 27 - "WasapiError"
Cohesion: 0.22
Nodes (4): GUID, Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, OSError

### Community 29 - "post"
Cohesion: 0.09
Nodes (34): cancel_video_audio_track_job(), cancel_video_audio_tracks(), capture_action(), compare_screen_change_test(), create_video_marker(), create_video_session(), get_schedule(), join_video_session() (+26 more)

### Community 30 - "RemapToSourceTests"
Cohesion: 0.33
Nodes (3): Voltar os tempos do bloco para o eixo do áudio original. É a parte que, errada,…, Fim antes do início quebraria a ordenação e a legenda., RemapToSourceTests

### Community 31 - "audio-bus.sh"
Cohesion: 0.34
Nodes (13): load_loopback(), make_null_sink(), selected_mic(), setup(), audio-bus.sh script, sink_exists(), source_exists(), status() (+5 more)

### Community 32 - "src-backup-2026-08-09/api.ts"
Cohesion: 0.07
Nodes (26): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+18 more)

### Community 33 - "src-backup-2026-08-09/main.tsx"
Cohesion: 0.10
Nodes (5): EditableVideoSpeaker, icons, labels, Panel, View

### Community 34 - "get"
Cohesion: 0.10
Nodes (25): backfill_confirmed_voice_observations(), bounded_video_range(), capture_days(), enroll_voice_identity(), get_cleanup_settings(), health(), list_ollama_models(), local_origin_only() (+17 more)

### Community 35 - "_call"
Cohesion: 0.29
Nodes (14): _call(), _check(), default_endpoint_name(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints(), Invoca o método ``index`` da vtable de uma interface COM. (+6 more)

### Community 37 - "main.py"
Cohesion: 0.12
Nodes (35): _apply_storage_runtime(), _apply_video_runtime(), atomic_write(), atomic_write_if_changed(), CleanupSettings, ContextUpdate, get_sensitive_windows(), get_storage_settings() (+27 more)

### Community 38 - "test_services.py"
Cohesion: 0.14
Nodes (27): HudDisplayModeTests, HudEventContractTests, ObsWindowSpecTests, Testes das peças que tornam o app portável entre Linux e Windows. Rodam nos…, O evento cruza dois processos por um arquivo; o formato é um contrato. O…, O identificador de janela do OBS é ``título:classe:executável``. Um título com…, ResamplerTests, ScreenConfigTests (+19 more)

### Community 39 - "run"
Cohesion: 0.16
Nodes (19): audio_file(), _audio_streams(), capture_speaker_sample(), import_video(), process_file(), ProcessFileRequest, datetime, run() (+11 more)

### Community 45 - "winrecord.py"
Cohesion: 0.13
Nodes (14): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _install_stop_handlers(), _mix(), _multichannel(), array, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.… (+6 more)

### Community 46 - "ImageDiffTests"
Cohesion: 0.19
Nodes (10): ImageDiffTests, Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg. O laço de captura do Linux usa…, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar. (+2 more)

### Community 47 - "LinuxHudCollector"
Cohesion: 0.22
Nodes (8): _count_markers(), LinuxHudCollector, Path, Estado derivado do laço bash e medidores lidos dos buses do PipeWire. O…, Segmento sendo escrito agora pelo ``gpu-screen-recorder``., Janela em foco, com a mesma cadência do laço bash (2 s). O sidecar ``.window``…, Há quanto tempo o segmento em curso começou. Vem do nome do arquivo, não do…, _segment_elapsed()

### Community 48 - "media_source_key"
Cohesion: 0.12
Nodes (25): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., backfill_video_session_durations(), delete_video(), list_video_sessions(), list_videos() (+17 more)

### Community 49 - "_Growth"
Cohesion: 0.22
Nodes (4): _Growth, _MeterTracker, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo)., Contabilidade temporal de uma fonte de áudio. Guarda desde quando a fonte não…

### Community 50 - "capture_frames"
Cohesion: 0.16
Nodes (14): cancel_video_audio_track_jobs(), capture_change_test_frames(), capture_frames(), get_screen_settings(), get_video_settings(), lifespan(), migrate_legacy_media_caches(), parse_shell_config() (+6 more)

### Community 51 - "hudsource.py"
Cohesion: 0.12
Nodes (15): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.…, read_shell_config(), _app_label(), _elapsed(), get_collector(), HudCollector, ABC, Coleta do estado que a HUD mostra, com um coletor por sistema. Mesma divisão… (+7 more)

### Community 52 - "Hud"
Cohesion: 0.07
Nodes (27): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., _alert_sound(), _declare_dpi_aware(), ease_in_cubic() (+19 more)

### Community 53 - "ServiceManager"
Cohesion: 0.10
Nodes (12): ABC, Executa ``start``/``stop``/``restart``/``try-restart``/``enable``/``disable``., Horário configurado do processamento noturno e se está ativo., Reprograma o processamento noturno., Dispara um job avulso sob um nome de unit, para poder cancelá-lo depois. É o…, Reinicia a própria interface (usado ao trocar o local dos dados)., Chamado quando a API sobe., Chamado quando a API desce. (+4 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.07
Nodes (12): CAPTION_LABELS, CAPTION_ORDER, CapturaTab, dayViews, EditableVideoSpeaker, gameCovers, icons, labels (+4 more)

### Community 55 - "App"
Cohesion: 0.20
Nodes (11): Capture, CleanupSettings, PipelineQueue, ScreenSequenceResult, Status, uploadVideo(), VideoSettings, App() (+3 more)

### Community 56 - "videoTime"
Cohesion: 0.15
Nodes (15): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SessionCard(), sessionDuration() (+7 more)

### Community 57 - "filter_hallucinated_segments"
Cohesion: 0.40
Nodes (3): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas.

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers. Média…, Um fluxo de captura: microfone padrão ou loopback da saída padrão. A saída de…, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio). Um fluxo…, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 61 - "pipeline.py"
Cohesion: 0.12
Nodes (54): _activity_image(), adaptive_web_research(), analyze_screen_sequence(), analyze_video_chapter(), audio_channel_count(), audio_stream_count(), compact_processed_audio(), compact_saved_capture() (+46 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.10
Nodes (18): _assert_topmost(), blend(), EventFrame, HudPanel, _make_overlay(), HWND real de um ``Toplevel`` do tkinter., Deixa a janela flutuando, sem foco, sem clique e fora do Alt+Tab., Reafirma o topo da pilha. Um jogo entrando em tela cheia reordena o z-order e… (+10 more)

### Community 64 - "HudStateTests"
Cohesion: 0.25
Nodes (3): HudStateTests, As regras que decidem se a captura está saudável. Rodam nos dois sistemas de…, Ficar calado é normal; confundir com falha destrói a confiança na HUD.

### Community 67 - "wasapi.py"
Cohesion: 0.15
Nodes (12): _ActivationHandler, _AudioClientActivationParams, _Blob, _LazyOle32, PROPERTYKEY, PROPVARIANT, _PropVariantBlob, Captura de áudio WASAPI em ``ctypes`` puro (Windows). Existe porque o ffmpeg no… (+4 more)

### Community 68 - "HudPlacementTests"
Cohesion: 0.23
Nodes (6): HudPlacementTests, Onde a HUD desenha, dado o arranjo de monitores., Com um monitor só, "no outro monitor" tem que recair sobre este., choose_monitors(), corner_position(), Monitores que devem receber um painel. Função pura para poder ser testada sem…

### Community 70 - "WindowsHudCollector"
Cohesion: 0.15
Nodes (6): log(), Medidores e engate lidos do OBS dedicado, estado lido do sinal de vídeo., Lê PCM cru do monitor de um bus e acumula o pico. Taxa baixa e um canal de…, WindowsHudCollector, Converte multiplicador linear (0..1) para dBFS, com piso em silêncio., to_db()

### Community 74 - "runtime_dir"
Cohesion: 0.23
Nodes (11): Estado operacional do gravador, separado da mera configuração ativa., selective_video_status(), status(), Path, Helpers de runtime que funcionam igual em Linux e Windows. Centraliza as poucas…, Diretório para arquivos efêmeros (locks, estado volátil). Linux usa…, Arquivo que sinaliza "estou gravando vídeo agora". É como o laço de vídeo pede…, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo. (+3 more)

### Community 75 - ".action"
Cohesion: 0.22
Nodes (4): Arquivo de estado que o laço de vídeo cria enquanto controla as capturas. Mesma…, (Re)inicia o swayidle apontando os eventos para o flag de idle., _unknown(), _video_pause_file()

### Community 76 - "windows_startup.py"
Cohesion: 0.60
Nodes (4): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows. Executado com ``pythonw.exe``…

### Community 77 - "_resolve"
Cohesion: 0.20
Nodes (4): Uma unit supervisionada. ``simple`` roda enquanto o serviço estiver ligado (e…, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef

### Community 78 - "SpeechRegionTests"
Cohesion: 0.36
Nodes (5): Trechos ``(início, fim)`` em segundos onde há som acima do limiar. Função pura…, speech_regions(), Detecção dos trechos com som, sobre amostras sintéticas., A folga não pode gerar tempo negativo nem passar do fim do áudio., SpeechRegionTests

### Community 79 - "Path"
Cohesion: 0.10
Nodes (11): LinuxIdlePauseTests, _pausable(), Path, skipUnless, Um tipo sem estilo seria um evento invisível — falha silenciosa., Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)., O sinal de atividade tem um significado só, e ele é caro de errar. Enquanto o…, Dois marcadores seguidos têm o mesmo rótulo; só a sequência os separa. (+3 more)

### Community 81 - "services.py"
Cohesion: 0.22
Nodes (7): _JobObject, _pipeline(), _python(), Gerenciamento de serviços independente de sistema operacional. No Linux o…, Amarra os processos filhos ao ciclo de vida da API. É o que o systemd consegue…, Return seconds since the last real keyboard or mouse input on Windows., windows_idle_seconds()

### Community 82 - "._start"
Cohesion: 0.36
Nodes (4): _Process, Path, Popen, Um processo filho supervisionado.

### Community 85 - "HudFrameRateTests"
Cohesion: 0.33
Nodes (3): HudFrameRateTests, As três cadências existem por causa do custo de redesenhar. Cada volta recria…, Uma entrada de 0,26 s precisa de quadros suficientes para não escadear.

### Community 91 - "recover_json_from_thinking"
Cohesion: 0.33
Nodes (3): parse_json_response(), Recupera JSON que o parser do Ollama classificou todo como thinking., recover_json_from_thinking()

## Knowledge Gaps
- **103 isolated node(s):** `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` (+98 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `ConfigTests`, `winvideo.py`, `connect`, `test_main.py`, `RegionGroupingTests`, `WindowsServiceManager`, `LinuxCaptureBackend`, `Path`, `post`, `RemapToSourceTests`, `get`, `main.py`, `test_services.py`, `run`, `ImageDiffTests`, `Hud`, `ServiceManager`, `HudStateTests`, `HudPlacementTests`, `.action`, `_resolve`, `SpeechRegionTests`, `Path`, `services.py`, `._start`, `HudFrameRateTests`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `ActionResult` to `ConfigTests`, `HudStateTests`, `HudPlacementTests`, `winvideo.py`, `test_services.py`, `test_main.py`, `.action`, `RegionGroupingTests`, `SpeechRegionTests`, `ImageDiffTests`, `Path`, `services.py`, `LinuxCaptureBackend`, `Hud`, `ServiceManager`, `HudFrameRateTests`, `post`, `RemapToSourceTests`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `get`, `test_main.py`, `ActionResult`, `initialize`, `audio_intelligence.py`, `filter_hallucinated_segments`, `recover_json_from_thinking`, `merge_transcript_sources`, `pipeline.py`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 50 inferred relationships involving `ActionResult` (e.g. with `CleanupSettings` and `ContextUpdate`) actually correct?**
  _`ActionResult` has 50 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `ActionResult`) actually correct?**
  _`ConfigTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 31 inferred relationships involving `HudSnapshot` (e.g. with `HudDisplayModeTests` and `HudEventAnimationTests`) actually correct?**
  _`HudSnapshot` has 31 INFERRED edges - model-reasoned connections that need verification._
- **Are the 28 inferred relationships involving `SystemdServiceManager` (e.g. with `ConfigTests` and `RegionGroupingTests`) actually correct?**
  _`SystemdServiceManager` has 28 INFERRED edges - model-reasoned connections that need verification._