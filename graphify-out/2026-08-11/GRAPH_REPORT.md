# Graph Report - lume  (2026-08-11)

## Corpus Check
- 50 files · ~70,185 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1118 nodes · 2629 edges · 64 communities (55 shown, 9 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 145 edges (avg confidence: 0.54)
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
- pipeline.py
- Lume no Windows
- connect
- media_source_key
- winscreen.py
- get
- game-video-loop
- ActionResult
- AGENTS.md
- WindowsCaptureBackend
- Path
- Path
- install-audio-intelligence
- audio_intelligence.py
- capture-frame
- run
- add-video-marker
- _ActivationHandler
- install-captura-dia.sh
- test_services.py
- Path
- audio-bus.sh
- src-backup-2026-08-09/api.ts
- src-backup-2026-08-09/main.tsx
- main.py
- wasapi.py
- capture-loop
- selective_video_status
- winvideo.py
- winrecord.py
- grava-audio.sh
- install-lume.sh
- install-user.sh
- UnitResolutionTests
- test_main.py
- video_file
- WindowsServiceManager
- WasapiError
- process_pending
- Settings
- matched_sensitive_pattern
- runtime.py
- src/main.tsx
- App
- videoTime
- ObsWindowSpecTests
- WasapiCapture
- videoTime
- windows_startup.py
- _scaled_size
- App

## God Nodes (most connected - your core abstractions)
1. `ConfigTests` - 70 edges
2. `connect()` - 66 edges
3. `ActionResult` - 63 edges
4. `VideoLoop` - 34 edges
5. `WindowsCaptureBackend` - 33 edges
6. `Monitor` - 30 edges
7. `AudioConfig` - 29 edges
8. `media_source_key()` - 28 edges
9. `SystemdServiceManager` - 28 edges
10. `WindowsServiceManager` - 25 edges

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

## Communities (64 total, 9 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.05
Nodes (10): speaker_profiles(), captured_video_session(), Lê a identidade portátil deixada pelo gravador seletivo. Vídeos antigos só têm…, daily_narrative_target(), multimodal_context(), Recupera JSON que o parser do Ollama classificou todo como thinking., Agrupa telas e áudios sobrepostos em momentos únicos para as sínteses., recover_json_from_thinking() (+2 more)

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
Cohesion: 0.08
Nodes (24): AudioConfig, CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional. Cada SO…, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco. Retorna ``None``…, Prepara o roteamento de áudio (no-op onde não for necessário)., Desfaz o roteamento de áudio (no-op onde não for necessário). (+16 more)

### Community 5 - "obs.py"
Cohesion: 0.08
Nodes (50): any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), ensure_scene(), find_installation(), is_provisioned() (+42 more)

### Community 6 - "record"
Cohesion: 0.17
Nodes (10): ProcessLoopbackCapture, Loopback que inclui ou exclui a árvore de um processo do Windows., Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record() (+2 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.15
Nodes (12): foreground_details(), log(), main(), Path, Título, classe e executável da janela em foco — o que o OBS precisa para…, Janela atual e resultado das regras usando campos separados., Confirma uma ação aceita sem depender da interface estar em foco., Anota o instante atual da gravação. Os marcadores ficam em memória e só vão… (+4 more)

### Community 9 - "pipeline.py"
Cohesion: 0.15
Nodes (26): initialize(), _activity_image(), adaptive_web_research(), discover(), generate_hourly_summaries(), generate_summary(), generate_visual_activities(), main() (+18 more)

### Community 10 - "Lume no Windows"
Cohesion: 0.08
Nodes (23): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+15 more)

### Community 11 - "connect"
Cohesion: 0.12
Nodes (34): connect(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_video_analysis(), cancel_video_session(), capture_action(), delete_capture() (+26 more)

### Community 12 - "media_source_key"
Cohesion: 0.17
Nodes (15): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., list_videos(), _config_dir(), configured_storage_root(), media_source_key() (+7 more)

### Community 13 - "winscreen.py"
Cohesion: 0.11
Nodes (19): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.…, read_shell_config(), _install_stop_handlers(), Atende todos os sinais de parada que o SO pode mandar. No Windows o supervisor…, _as_bool(), _as_float(), _as_int(), main() (+11 more)

### Community 14 - "get"
Cohesion: 0.12
Nodes (25): row_dict(), backfill_confirmed_voice_observations(), backfill_video_session_durations(), capture_days(), enroll_voice_identity(), health(), hourly_timeline(), list_ollama_models() (+17 more)

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "ActionResult"
Cohesion: 0.18
Nodes (7): Uma unit transitória coletada equivale a um job já parado., stop_target_is_already_gone(), ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API., SystemdFallbackTests

### Community 18 - "WindowsCaptureBackend"
Cohesion: 0.13
Nodes (10): ImageDiffTests, Monitor, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Um monitor físico: rótulo estável + geometria em pixels do desktop., Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga. Dois formatos de saída…, Dispositivo dshow capaz de gravar a saída, se algum existir. Só diagnóstico: a… (+2 more)

### Community 19 - "Path"
Cohesion: 0.20
Nodes (24): analyze_video_chapter(), audio_channel_count(), audio_stream_count(), compact_processed_audio(), describe_long_video(), describe_screen(), describe_video(), extract_adaptive_keyframes() (+16 more)

### Community 20 - "Path"
Cohesion: 0.12
Nodes (26): cancel_video_audio_track_job(), cancel_video_audio_track_jobs(), cancel_video_audio_tracks(), delete_video(), delete_video_caches(), ensure_video_thumbnail(), migrate_legacy_cache_file(), probe_video_audio_tracks() (+18 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.23
Nodes (21): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+13 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "run"
Cohesion: 0.22
Nodes (14): audio_file(), _audio_streams(), capture_speaker_sample(), import_video(), process_file(), ProcessFileRequest, datetime, run() (+6 more)

### Community 29 - "test_services.py"
Cohesion: 0.16
Nodes (10): skipUnless, Testes das peças que tornam o app portável entre Linux e Windows. Rodam nos…, Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., ResamplerTests, ScreenConfigTests, StereoAudioTests, VideoHotkeyTests, VideoMarkerTransitionTests (+2 more)

### Community 30 - "Path"
Cohesion: 0.17
Nodes (4): Path, SupervisorTests, VideoReplayClipTests, VideoSettingsTests

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
Cohesion: 0.09
Nodes (46): atomic_write(), _audio_channels(), capture_payload(), captures(), ContextUpdate, create_video_marker(), create_video_session(), get_schedule() (+38 more)

### Community 35 - "wasapi.py"
Cohesion: 0.19
Nodes (22): _AudioClientActivationParams, _Blob, _call(), _check(), default_endpoint_name(), _device_enumerator(), ensure_com(), _friendly_name() (+14 more)

### Community 37 - "selective_video_status"
Cohesion: 0.12
Nodes (21): capture_change_test_frames(), capture_frames(), compare_screen_change_test(), directory_stats(), get_screen_settings(), get_video_settings(), lifespan(), migrate_legacy_media_caches() (+13 more)

### Community 38 - "winvideo.py"
Cohesion: 0.15
Nodes (12): Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg. O laço de captura do Linux usa…, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar., Diferença percentual entre dois arquivos de imagem. (+4 more)

### Community 39 - "winrecord.py"
Cohesion: 0.15
Nodes (12): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _mix(), _multichannel(), array, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.…, Soma as fontes com saturação e converte para PCM s16le. (+4 more)

### Community 45 - "UnitResolutionTests"
Cohesion: 0.36
Nodes (3): Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), UnitResolutionTests

### Community 46 - "test_main.py"
Cohesion: 0.10
Nodes (11): _activity_groups(), filter_hallucinated_segments(), merge_source_transcripts(), merge_transcript_sources(), monitor_key(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas., Falas do áudio que estava sendo gravado perto do instante de um print. (+3 more)

### Community 47 - "video_file"
Cohesion: 0.29
Nodes (7): bounded_video_range(), local_origin_only(), Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., video_file(), middleware, Request, StreamingResponse

### Community 48 - "WindowsServiceManager"
Cohesion: 0.06
Nodes (28): _JobObject, _pipeline(), _Process, ABC, Path, Popen, _python(), Gerenciamento de serviços independente de sistema operacional. No Linux o… (+20 more)

### Community 49 - "WasapiError"
Cohesion: 0.25
Nodes (4): GUID, Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, OSError

### Community 50 - "process_pending"
Cohesion: 0.19
Nodes (9): compact_saved_capture(), known_voice_profiles(), process_pending(), process_specific(), Compact a completed capture and record either its new hash or a warning., save_speaker_observations(), sha256(), visually_changed() (+1 more)

### Community 51 - "Settings"
Cohesion: 0.22
Nodes (5): Lista de expressões de um arquivo de padrões, ignorando comentários., read_patterns(), Regras sem prefixo procuram somente no executável. Assim uma pasta chamada como…, Instantâneo de ``video.conf`` e da lista de apps., Settings

### Community 52 - "matched_sensitive_pattern"
Cohesion: 0.29
Nodes (5): PrivacyTests, matched_sensitive_pattern(), Path, Primeiro padrão sensível (regex, case-insensitive) que casa com a janela. Mesma…, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados. ``stamp``…

### Community 53 - "runtime.py"
Cohesion: 0.23
Nodes (10): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows. Centraliza as poucas…, Diretório para arquivos efêmeros (locks, estado volátil). Linux usa…, Arquivo que sinaliza "estou gravando vídeo agora". É como o laço de vídeo pede…, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``. Retorna ``True`` se conseguiu…, runtime_dir() (+2 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.08
Nodes (8): CapturaTab, dayViews, EditableVideoSpeaker, icons, labels, lensLabels, Panel, View

### Community 55 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 56 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 57 - "ObsWindowSpecTests"
Cohesion: 0.24
Nodes (6): ObsWindowSpecTests, O identificador de janela do OBS é ``título:classe:executável``. Um título com…, parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., _encode_field(), Escapa um campo do identificador de janela do OBS. O identificador é…

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers. Média…, Um fluxo de captura: microfone padrão ou loopback da saída padrão. A saída de…, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio). Um fluxo…, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "windows_startup.py"
Cohesion: 0.60
Nodes (4): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows. Executado com ``pythonw.exe``…

### Community 61 - "_scaled_size"
Cohesion: 0.50
Nodes (4): _parse_max_geometry(), Interpreta ``"1920x1080>"`` -> (1920, 1080, apenas_reduzir)., Dimensões finais respeitando ``MAX_GEOMETRY`` (mantém proporção)., _scaled_size()

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

## Knowledge Gaps
- **100 isolated node(s):** `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` (+95 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `ConfigTests`, `main.py`, `selective_video_status`, `connect`, `UnitResolutionTests`, `get`, `test_main.py`, `WindowsServiceManager`, `WindowsCaptureBackend`, `Path`, `matched_sensitive_pattern`, `run`, `test_services.py`, `Path`, `ObsWindowSpecTests`?**
  _High betweenness centrality (0.115) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `pipeline.py`, `test_main.py`, `get`, `ActionResult`, `process_pending`, `Path`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `AudioConfig` connect `AudioConfig` to `main.py`, `UnitResolutionTests`, `ActionResult`, `WindowsCaptureBackend`, `matched_sensitive_pattern`, `ObsWindowSpecTests`, `test_services.py`, `Path`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `ConfigTests` (e.g. with `ActionResult` and `SystemdServiceManager`) actually correct?**
  _`ConfigTests` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `ActionResult` (e.g. with `ContextUpdate` and `MarkerCreate`) actually correct?**
  _`ActionResult` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `VideoLoop` (e.g. with `ImageDiffTests` and `ObsWindowSpecTests`) actually correct?**
  _`VideoLoop` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem` to the rest of the system?**
  _100 weakly-connected nodes found - possible documentation gaps or missing edges._