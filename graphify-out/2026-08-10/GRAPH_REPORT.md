# Graph Report - lume  (2026-08-10)

## Corpus Check
- 48 files · ~68,476 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1087 nodes · 2527 edges · 67 communities (56 shown, 11 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 118 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- ConfigTests
- src/api.ts
- package.json
- compilerOptions
- AudioConfig
- obs.py
- record
- Handoff: Lume — app de memória de tela & áudio
- VideoLoop
- WindowsServiceManager
- Lume no Windows
- connect
- main_paths.py
- winscreen.py
- get
- game-video-loop
- _install_stop_handlers
- AGENTS.md
- post
- pipeline.py
- Path
- install-audio-intelligence
- audio_intelligence.py
- capture-frame
- run
- add-video-marker
- ActionResult
- install-captura-dia.sh
- Path
- test_services.py
- audio-bus.sh
- src-backup-2026-08-09/api.ts
- src-backup-2026-08-09/main.tsx
- main.py
- imagediff.py
- capture-loop
- capture_frames
- MarkerHotkey
- filter_hallucinated_segments
- grava-audio.sh
- install-lume.sh
- install-user.sh
- winrecord.py
- rebuild_voice_identity
- test_main.py
- services.py
- _call
- Path
- matched_sensitive_pattern
- winvideo.py
- wasapi.py
- src/main.tsx
- App
- videoTime
- Settings
- _BoxResampler
- videoTime
- _resolve
- App
- ._start
- WasapiCapture
- merge_transcript_sources
- _JobObject
- ScreenConfigTests

## God Nodes (most connected - your core abstractions)
1. `connect()` - 66 edges
2. `ActionResult` - 63 edges
3. `ConfigTests` - 59 edges
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

## Communities (67 total, 11 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.05
Nodes (11): speaker_profiles(), captured_video_session(), Lê a identidade portátil deixada pelo gravador seletivo. Vídeos antigos só têm…, daily_narrative_target(), multimodal_context(), Recupera JSON que o parser do Ollama classificou todo como thinking., Agrupa telas e áudios sobrepostos em momentos únicos para as sínteses., recover_json_from_thinking() (+3 more)

### Community 1 - "src/api.ts"
Cohesion: 0.07
Nodes (27): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+19 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "AudioConfig"
Cohesion: 0.05
Nodes (36): AudioConfig, CaptureBackend, Monitor, ABC, Interface comum de captura, independente de sistema operacional. Cada SO…, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco. Retorna ``None``…, Monitores habilitados, em ordem estável de índice. (+28 more)

### Community 5 - "obs.py"
Cohesion: 0.08
Nodes (50): any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), ensure_scene(), find_installation(), is_provisioned() (+42 more)

### Community 6 - "record"
Cohesion: 0.20
Nodes (8): Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record(), _SegmentWriter, _Source

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.15
Nodes (14): foreground_details(), log(), looks_blank(), main(), Path, Título, classe e executável da janela em foco — o que o OBS precisa para…, Amostra um quadro e diz se o vídeo saiu chapado (preto/estático). É a rede de…, Janela atual e resultado das regras usando campos separados. (+6 more)

### Community 9 - "WindowsServiceManager"
Cohesion: 0.17
Nodes (6): Supervisor: mantém os processos de captura vivos e agenda o processamento. Vive…, Anota que a captura deve (ou não) voltar na próxima abertura do Lume. No Linux…, Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., Suspende áudio e telas enquanto o gravador de vídeo estiver ativo. No Linux o…, _unknown(), WindowsServiceManager

### Community 10 - "Lume no Windows"
Cohesion: 0.08
Nodes (23): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+15 more)

### Community 11 - "connect"
Cohesion: 0.12
Nodes (29): connect(), backfill_video_session_durations(), cancel_entire_queue(), cancel_queue_item(), cancel_video_analysis(), cancel_video_session(), capture_days(), delete_capture() (+21 more)

### Community 12 - "main_paths.py"
Cohesion: 0.17
Nodes (10): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., _config_dir(), configured_storage_root(), Onde ficam ``tela.conf`` e a lista de janelas sensíveis. No Linux, o lugar de…, PortableMediaPathTests (+2 more)

### Community 13 - "winscreen.py"
Cohesion: 0.20
Nodes (10): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.…, read_shell_config(), _as_bool(), _as_float(), _as_int(), _parse_config(), Laço contínuo de captura de telas — porte de ``bin/capture-loop`` para Python.…, Lê o ``tela.conf`` (formato ``CHAVE=valor`` do shell). (+2 more)

### Community 14 - "get"
Cohesion: 0.12
Nodes (28): row_dict(), _audio_channels(), cancel_video_audio_track_jobs(), cancel_video_audio_tracks(), capture_payload(), capture_speaker_sample(), captures(), delete_unprocessed_files() (+20 more)

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "_install_stop_handlers"
Cohesion: 0.20
Nodes (9): _install_stop_handlers(), Atende todos os sinais de parada que o SO pode mandar. No Windows o supervisor…, main(), _monitor_key(), Path, Identidade do monitor a partir do nome do arquivo (``..._mon1_DP-1.png``). A…, Motivo para não capturar agora, ou ``None`` se pode capturar., ScreenLoop (+1 more)

### Community 18 - "post"
Cohesion: 0.19
Nodes (16): cancel_pipeline(), capture_action(), enqueue_unprocessed(), generate_hourly_now(), generate_summary_now(), pipeline_run(), preserve_video(), process_video() (+8 more)

### Community 19 - "pipeline.py"
Cohesion: 0.21
Nodes (29): initialize(), _activity_image(), adaptive_web_research(), analyze_video_chapter(), describe_long_video(), describe_video(), discover(), extract_adaptive_keyframes() (+21 more)

### Community 20 - "Path"
Cohesion: 0.11
Nodes (27): audio_file(), ensure_video_thumbnail(), get_storage_settings(), probe_video_audio_tracks(), process_file(), ProcessFileRequest, Path, Popen (+19 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.23
Nodes (21): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+13 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "run"
Cohesion: 0.19
Nodes (14): _audio_streams(), import_video(), local_origin_only(), datetime, run(), search(), test_audio(), unload_ollama_models() (+6 more)

### Community 27 - "ActionResult"
Cohesion: 0.18
Nodes (8): Uma unit transitória coletada equivale a um job já parado., stop_target_is_already_gone(), ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API., SystemdFallbackTests, VideoMarkerTransitionTests

### Community 29 - "Path"
Cohesion: 0.15
Nodes (5): PrivacyTests, Path, SupervisorTests, VideoReplayClipTests, VideoSettingsTests

### Community 30 - "test_services.py"
Cohesion: 0.21
Nodes (7): ObsWindowSpecTests, Testes das peças que tornam o app portável entre Linux e Windows. Rodam nos…, O identificador de janela do OBS é ``título:classe:executável``. Um título com…, parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., _encode_field(), Escapa um campo do identificador de janela do OBS. O identificador é…

### Community 31 - "audio-bus.sh"
Cohesion: 0.67
Nodes (6): load_loopback(), setup(), audio-bus.sh script, status(), unload_bus(), wait_pipewire()

### Community 32 - "src-backup-2026-08-09/api.ts"
Cohesion: 0.07
Nodes (26): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+18 more)

### Community 33 - "src-backup-2026-08-09/main.tsx"
Cohesion: 0.10
Nodes (5): EditableVideoSpeaker, icons, labels, Panel, View

### Community 34 - "main.py"
Cohesion: 0.12
Nodes (35): atomic_write(), ContextUpdate, create_video_marker(), create_video_session(), get_schedule(), get_sensitive_windows(), join_video_session(), list_voice_identities() (+27 more)

### Community 35 - "imagediff.py"
Cohesion: 0.24
Nodes (9): Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg. O laço de captura do Linux usa…, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar., Diferença percentual entre dois arquivos de imagem. (+1 more)

### Community 37 - "capture_frames"
Cohesion: 0.25
Nodes (11): capture_change_test_frames(), capture_frames(), compare_screen_change_test(), get_screen_settings(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver. A mesma regra nos dois…, Captura um conjunto de frames com a configuração atual., screen_change_percent() (+3 more)

### Community 38 - "MarkerHotkey"
Cohesion: 0.18
Nodes (6): ImageDiffTests, skipUnless, StereoAudioTests, VideoHotkeyTests, MarkerHotkey, Atalho global para marcar um momento durante a gravação. No Linux o atalho do…

### Community 39 - "filter_hallucinated_segments"
Cohesion: 0.40
Nodes (3): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas.

### Community 45 - "winrecord.py"
Cohesion: 0.15
Nodes (12): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _mix(), _multichannel(), array, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.…, Soma as fontes com saturação e converte para PCM s16le. (+4 more)

### Community 46 - "rebuild_voice_identity"
Cohesion: 0.24
Nodes (8): backfill_confirmed_voice_observations(), enroll_voice_identity(), _normalized_average(), Recalcula um perfil dando um único voto a cada gravação., rebuild_voice_identity(), SpeakerLabelUpdate, update_capture_speaker(), update_video_speaker()

### Community 47 - "test_main.py"
Cohesion: 0.12
Nodes (11): _activity_groups(), private_context_terms(), Memórias do dia, representando cada sessão de vídeo apenas uma vez., Valida referências da IA e protege os arquivos escolhidos., Falas do áudio que estava sendo gravado perto do instante de um print., Separa por aplicativo e continuidade; mudanças de título não quebram a sessão., safe_research_query(), short_video_analysis_prompt() (+3 more)

### Community 48 - "services.py"
Cohesion: 0.09
Nodes (14): _pipeline(), ABC, _python(), Gerenciamento de serviços independente de sistema operacional. No Linux o…, Chamado quando a API sobe., Chamado quando a API desce., Contrato que o ``main.py`` usa; systemd e supervisor implementam., Estado de uma unit, no mesmo formato que ``systemctl show`` produz. (+6 more)

### Community 49 - "_call"
Cohesion: 0.29
Nodes (14): _call(), _check(), default_endpoint_name(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints(), Invoca o método ``index`` da vtable de uma interface COM. (+6 more)

### Community 50 - "Path"
Cohesion: 0.18
Nodes (21): audio_channel_count(), audio_stream_count(), compact_processed_audio(), compact_saved_capture(), describe_screen(), known_voice_profiles(), monitor_key(), process_pending() (+13 more)

### Community 51 - "matched_sensitive_pattern"
Cohesion: 0.40
Nodes (5): matched_sensitive_pattern(), Path, Primeiro padrão sensível (regex, case-insensitive) que casa com a janela. Mesma…, Lista de expressões de um arquivo de padrões, ignorando comentários., read_patterns()

### Community 52 - "winvideo.py"
Cohesion: 0.19
Nodes (13): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows. Centraliza as poucas…, Diretório para arquivos efêmeros (locks, estado volátil). Linux usa…, Arquivo que sinaliza "estou gravando vídeo agora". É como o laço de vídeo pede…, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``. Retorna ``True`` se conseguiu…, runtime_dir() (+5 more)

### Community 53 - "wasapi.py"
Cohesion: 0.20
Nodes (10): _ActivationHandler, _AudioClientActivationParams, _Blob, PROPERTYKEY, PROPVARIANT, _PropVariantBlob, Captura de áudio WASAPI em ``ctypes`` puro (Windows). Existe porque o ffmpeg no…, Implementação mínima de IActivateAudioInterfaceCompletionHandler. (+2 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.08
Nodes (8): CapturaTab, dayViews, EditableVideoSpeaker, icons, labels, lensLabels, Panel, View

### Community 55 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 56 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 57 - "Settings"
Cohesion: 0.29
Nodes (3): Regras sem prefixo procuram somente no executável. Assim uma pasta chamada como…, Instantâneo de ``video.conf`` e da lista de apps., Settings

### Community 58 - "_BoxResampler"
Cohesion: 0.22
Nodes (6): Blocos que não caem em fronteira redonda não podem perder amostras., ResamplerTests, _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers. Média…, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio). Um fluxo…

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "_resolve"
Cohesion: 0.24
Nodes (5): Uma unit supervisionada. ``simple`` roda enquanto o serviço estiver ligado (e…, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef, UnitResolutionTests

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "._start"
Cohesion: 0.36
Nodes (4): _Process, Path, Popen, Um processo filho supervisionado.

### Community 64 - "WasapiCapture"
Cohesion: 0.14
Nodes (8): GUID, ProcessLoopbackCapture, Falha numa chamada COM do WASAPI, com o HRESULT preservado., Um fluxo de captura: microfone padrão ou loopback da saída padrão. A saída de…, Loopback que inclui ou exclui a árvore de um processo do Windows., WasapiCapture, WasapiError, OSError

## Knowledge Gaps
- **100 isolated node(s):** `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` (+95 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `ConfigTests`, `main.py`, `ScreenConfigTests`, `capture_frames`, `MarkerHotkey`, `WindowsServiceManager`, `rebuild_voice_identity`, `test_main.py`, `services.py`, `post`, `Path`, `_BoxResampler`, `_resolve`, `Path`, `test_services.py`, `._start`?**
  _High betweenness centrality (0.099) - this node is a cross-community bridge._
- **Why does `VideoLoop` connect `VideoLoop` to `ScreenConfigTests`, `MarkerHotkey`, `winvideo.py`, `_BoxResampler`, `ActionResult`, `_resolve`, `Path`, `test_services.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `AudioConfig` connect `AudioConfig` to `main.py`, `ScreenConfigTests`, `MarkerHotkey`, `run`, `_BoxResampler`, `ActionResult`, `_resolve`, `Path`, `test_services.py`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 33 inferred relationships involving `ActionResult` (e.g. with `ContextUpdate` and `MarkerCreate`) actually correct?**
  _`ActionResult` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ConfigTests` (e.g. with `ActionResult` and `SystemdServiceManager`) actually correct?**
  _`ConfigTests` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `VideoLoop` (e.g. with `ImageDiffTests` and `ObsWindowSpecTests`) actually correct?**
  _`VideoLoop` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem` to the rest of the system?**
  _100 weakly-connected nodes found - possible documentation gaps or missing edges._