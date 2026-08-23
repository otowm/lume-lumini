# Graph Report - lume  (2026-08-09)

## Corpus Check
- 45 files · ~60,960 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 996 nodes · 2372 edges · 57 communities (48 shown, 9 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 117 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- ConfigTests
- api.ts
- package.json
- compilerOptions
- base.py
- obs.py
- record
- Handoff: Lume — app de memória de tela & áudio
- VideoLoop
- WindowsServiceManager
- Lume no Windows
- connect
- media_source_key
- winscreen.py
- winrecord.py
- game-video-loop
- get_backend
- AGENTS.md
- WasapiCapture
- generate_visual_activities
- Path
- install-audio-intelligence
- analyze_video_audio
- capture-frame
- run
- add-video-marker
- ActionResult
- install-captura-dia.sh
- Path
- _BoxResampler
- audio-bus.sh
- ._start
- _call
- main.py
- ImageDiffTests
- capture-loop
- WindowsCaptureBackend
- test_services.py
- wasapi.py
- grava-audio.sh
- install-lume.sh
- install-user.sh
- process_pending
- get
- test_main.py
- services.py
- VideoHotkeyTests
- pipeline.py
- runtime.py
- filter_hallucinated_segments
- main.tsx
- App
- videoTime
- _resolve

## God Nodes (most connected - your core abstractions)
1. `connect()` - 66 edges
2. `ActionResult` - 62 edges
3. `ConfigTests` - 55 edges
4. `VideoLoop` - 34 edges
5. `AudioConfig` - 29 edges
6. `media_source_key()` - 28 edges
7. `SystemdServiceManager` - 28 edges
8. `WindowsServiceManager` - 25 edges
9. `resolve_media_source()` - 23 edges
10. `analyze_video_audio()` - 22 edges

## Surprising Connections (you probably didn't know these)
- `ScreenSettings` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `SensitiveWindows` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `PipelineRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `ProcessFileRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `VideoProcessRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py

## Import Cycles
- None detected.

## Communities (57 total, 9 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.06
Nodes (9): captured_video_session(), Lê a identidade portátil deixada pelo gravador seletivo. Vídeos antigos só têm…, daily_narrative_target(), merge_source_transcripts(), merge_transcript_sources(), Recupera JSON que o parser do Ollama classificou todo como thinking., recover_json_from_thinking(), ConfigTests (+1 more)

### Community 1 - "api.ts"
Cohesion: 0.07
Nodes (26): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+18 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "base.py"
Cohesion: 0.08
Nodes (20): CaptureBackend, ABC, Path, Interface comum de captura, independente de sistema operacional. Cada SO…, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco. Retorna ``None``…, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável. (+12 more)

### Community 5 - "obs.py"
Cohesion: 0.07
Nodes (54): ObsWindowSpecTests, O identificador de janela do OBS é ``título:classe:executável``. Um título com…, any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), _encode_field() (+46 more)

### Community 6 - "record"
Cohesion: 0.20
Nodes (8): Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record(), _SegmentWriter, _Source

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.09
Nodes (19): parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., foreground_details(), log(), looks_blank(), main(), Path, Regras sem prefixo procuram somente no executável. Assim uma pasta chamada como… (+11 more)

### Community 9 - "WindowsServiceManager"
Cohesion: 0.16
Nodes (6): Supervisor: mantém os processos de captura vivos e agenda o processamento. Vive…, Anota que a captura deve (ou não) voltar na próxima abertura do Lume. No Linux…, Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., Suspende áudio e telas enquanto o gravador de vídeo estiver ativo. No Linux o…, _unknown(), WindowsServiceManager

### Community 10 - "Lume no Windows"
Cohesion: 0.08
Nodes (23): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+15 more)

### Community 11 - "connect"
Cohesion: 0.10
Nodes (40): connect(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_video_analysis(), cancel_video_session(), capture_action(), capture_days() (+32 more)

### Community 12 - "media_source_key"
Cohesion: 0.17
Nodes (15): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., list_videos(), _config_dir(), configured_storage_root(), media_source_key() (+7 more)

### Community 13 - "winscreen.py"
Cohesion: 0.11
Nodes (19): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.…, read_shell_config(), _install_stop_handlers(), Atende todos os sinais de parada que o SO pode mandar. No Windows o supervisor…, _as_bool(), _as_float(), _as_int(), main() (+11 more)

### Community 14 - "winrecord.py"
Cohesion: 0.15
Nodes (12): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _mix(), _multichannel(), array, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.…, Soma as fontes com saturação e converte para PCM s16le. (+4 more)

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "get_backend"
Cohesion: 0.12
Nodes (17): capture_frames(), privacy_decision(), Captura um conjunto de frames com a configuração atual., Janela ativa e o motivo para não capturar, se houver. A mesma regra nos dois…, test_screen(), Valores de ``tela.conf`` relevantes para a captura de um frame., ScreenConfig, get_backend() (+9 more)

### Community 18 - "WasapiCapture"
Cohesion: 0.14
Nodes (8): GUID, ProcessLoopbackCapture, Falha numa chamada COM do WASAPI, com o HRESULT preservado., Um fluxo de captura: microfone padrão ou loopback da saída padrão. A saída de…, Loopback que inclui ou exclui a árvore de um processo do Windows., WasapiCapture, WasapiError, OSError

### Community 19 - "generate_visual_activities"
Cohesion: 0.21
Nodes (12): initialize(), _activity_image(), discover(), generate_hourly_summaries(), generate_summary(), generate_visual_activities(), main(), multimodal_context() (+4 more)

### Community 20 - "Path"
Cohesion: 0.17
Nodes (21): ensure_video_audio_tracks(), ensure_video_thumbnail(), get_storage_settings(), probe_video_audio_tracks(), Path, Extrai uma miniatura uma vez; chamadas simultâneas não disputam o HD., Lista os stems reproduzíveis, omitindo a mixagem geral do OBS., Remuxa todos os stems AAC em uma única leitura e mantém cache por arquivo. (+13 more)

### Community 23 - "analyze_video_audio"
Cohesion: 0.25
Nodes (20): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), consolidate_events(), detect_events(), diarize(), embedding_for_sample() (+12 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "run"
Cohesion: 0.13
Nodes (21): audio_file(), _audio_streams(), capture_speaker_sample(), import_video(), local_origin_only(), probe_video_duration(), process_file(), ProcessFileRequest (+13 more)

### Community 27 - "ActionResult"
Cohesion: 0.22
Nodes (7): Uma unit transitória coletada equivale a um job já parado., stop_target_is_already_gone(), ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API., SystemdFallbackTests

### Community 29 - "Path"
Cohesion: 0.17
Nodes (4): Path, SupervisorTests, VideoReplayClipTests, VideoSettingsTests

### Community 30 - "_BoxResampler"
Cohesion: 0.22
Nodes (6): Blocos que não caem em fronteira redonda não podem perder amostras., ResamplerTests, _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers. Média…, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio). Um fluxo…

### Community 31 - "audio-bus.sh"
Cohesion: 0.67
Nodes (6): load_loopback(), setup(), audio-bus.sh script, status(), unload_bus(), wait_pipewire()

### Community 32 - "._start"
Cohesion: 0.24
Nodes (6): _JobObject, _Process, Path, Amarra os processos filhos ao ciclo de vida da API. É o que o systemd consegue…, Um processo filho supervisionado., Popen

### Community 33 - "_call"
Cohesion: 0.29
Nodes (14): _call(), _check(), default_endpoint_name(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints(), Invoca o método ``index`` da vtable de uma interface COM. (+6 more)

### Community 34 - "main.py"
Cohesion: 0.09
Nodes (49): atomic_write(), capture_change_test_frames(), compare_screen_change_test(), ContextUpdate, create_video_marker(), create_video_session(), directory_stats(), get_schedule() (+41 more)

### Community 35 - "ImageDiffTests"
Cohesion: 0.20
Nodes (10): ImageDiffTests, Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg. O laço de captura do Linux usa…, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar. (+2 more)

### Community 37 - "WindowsCaptureBackend"
Cohesion: 0.16
Nodes (7): Monitor, Um monitor físico: rótulo estável + geometria em pixels do desktop., Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga. Dois formatos de saída…, Dispositivo dshow capaz de gravar a saída, se algum existir. Só diagnóstico: a…, argv do gravador WASAPI (ver :mod:`app.capture.winrecord`). Não é ffmpeg: no…, WindowsCaptureBackend

### Community 38 - "test_services.py"
Cohesion: 0.15
Nodes (13): PrivacyTests, Testes das peças que tornam o app portável entre Linux e Windows. Rodam nos…, Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., ScreenConfigTests, StereoAudioTests, VideoMarkerTransitionTests, AudioConfig, matched_sensitive_pattern() (+5 more)

### Community 39 - "wasapi.py"
Cohesion: 0.20
Nodes (10): _ActivationHandler, _AudioClientActivationParams, _Blob, PROPERTYKEY, PROPVARIANT, _PropVariantBlob, Captura de áudio WASAPI em ``ctypes`` puro (Windows). Existe porque o ffmpeg no…, Implementação mínima de IActivateAudioInterfaceCompletionHandler. (+2 more)

### Community 45 - "process_pending"
Cohesion: 0.16
Nodes (13): audio_channel_count(), compact_processed_audio(), compact_saved_capture(), known_voice_profiles(), process_pending(), process_specific(), Collapse a processed multichannel WAV to mono without risking the source. The…, Compact a completed capture and record either its new hash or a warning. (+5 more)

### Community 46 - "get"
Cohesion: 0.14
Nodes (23): row_dict(), _audio_channels(), backfill_confirmed_voice_observations(), backfill_video_session_durations(), capture_payload(), captures(), enroll_voice_identity(), health() (+15 more)

### Community 47 - "test_main.py"
Cohesion: 0.11
Nodes (12): _activity_groups(), monitor_key(), private_context_terms(), Memórias do dia, representando cada sessão de vídeo apenas uma vez., Valida referências da IA e protege os arquivos escolhidos., Falas do áudio que estava sendo gravado perto do instante de um print., Separa por aplicativo e continuidade; mudanças de título não quebram a sessão., safe_research_query() (+4 more)

### Community 48 - "services.py"
Cohesion: 0.09
Nodes (14): _pipeline(), ABC, _python(), Gerenciamento de serviços independente de sistema operacional. No Linux o…, Chamado quando a API sobe., Chamado quando a API desce., Contrato que o ``main.py`` usa; systemd e supervisor implementam., Estado de uma unit, no mesmo formato que ``systemctl show`` produz. (+6 more)

### Community 50 - "pipeline.py"
Cohesion: 0.23
Nodes (26): adaptive_web_research(), analyze_video_chapter(), audio_stream_count(), describe_long_video(), describe_screen(), describe_video(), extract_adaptive_keyframes(), format_video_time() (+18 more)

### Community 52 - "runtime.py"
Cohesion: 0.23
Nodes (10): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows. Centraliza as poucas…, Diretório para arquivos efêmeros (locks, estado volátil). Linux usa…, Arquivo que sinaliza "estou gravando vídeo agora". É como o laço de vídeo pede…, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``. Retorna ``True`` se conseguiu…, runtime_dir() (+2 more)

### Community 53 - "filter_hallucinated_segments"
Cohesion: 0.33
Nodes (4): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas., _whisper_segments()

### Community 54 - "main.tsx"
Cohesion: 0.09
Nodes (8): EditableVideoSpeaker, icons, labels, Panel, SessionCard(), sessionDuration(), SessionViewer(), View

### Community 55 - "App"
Cohesion: 0.25
Nodes (8): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), voiceGroups(), VoiceIdentityPanel()

### Community 56 - "videoTime"
Cohesion: 0.29
Nodes (8): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), SyncedAudioPlayer(), videoTime(), VideoViewer()

### Community 57 - "_resolve"
Cohesion: 0.24
Nodes (5): Uma unit supervisionada. ``simple`` roda enquanto o serviço estiver ligado (e…, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef, UnitResolutionTests

## Knowledge Gaps
- **84 isolated node(s):** `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `grava-audio.sh script`, `name`, `private` (+79 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `._start`, `ConfigTests`, `main.py`, `ImageDiffTests`, `obs.py`, `test_services.py`, `WindowsServiceManager`, `connect`, `get`, `test_main.py`, `services.py`, `VideoHotkeyTests`, `run`, `Path`, `_BoxResampler`, `_resolve`?**
  _High betweenness centrality (0.106) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `process_pending`, `get`, `test_main.py`, `pipeline.py`, `generate_visual_activities`, `filter_hallucinated_segments`, `ActionResult`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `AudioConfig` connect `test_services.py` to `main.py`, `ImageDiffTests`, `base.py`, `obs.py`, `WindowsCaptureBackend`, `get_backend`, `VideoHotkeyTests`, `run`, `ActionResult`, `Path`, `_BoxResampler`, `_resolve`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `ActionResult` (e.g. with `ContextUpdate` and `MarkerCreate`) actually correct?**
  _`ActionResult` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ConfigTests` (e.g. with `ActionResult` and `SystemdServiceManager`) actually correct?**
  _`ConfigTests` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `VideoLoop` (e.g. with `ImageDiffTests` and `ObsWindowSpecTests`) actually correct?**
  _`VideoLoop` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `grava-audio.sh script` to the rest of the system?**
  _84 weakly-connected nodes found - possible documentation gaps or missing edges._