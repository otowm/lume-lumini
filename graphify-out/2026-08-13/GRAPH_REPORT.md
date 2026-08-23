# Graph Report - lume  (2026-08-13)

## Corpus Check
- 50 files · ~71,811 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1148 nodes · 2719 edges · 61 communities (52 shown, 9 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 149 edges (avg confidence: 0.54)
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
- BaseModel
- Lume no Windows
- test_main.py
- get_backend
- winscreen.py
- WindowsServiceManager
- game-video-loop
- ActionResult
- AGENTS.md
- WindowsCaptureBackend
- pipeline.py
- Path
- install-audio-intelligence
- audio_intelligence.py
- capture-frame
- run
- add-video-marker
- _ActivationHandler
- install-captura-dia.sh
- get
- Path
- audio-bus.sh
- src-backup-2026-08-09/api.ts
- src-backup-2026-08-09/main.tsx
- connect
- wasapi.py
- capture-loop
- main.py
- test_services.py
- winrecord.py
- grava-audio.sh
- install-lume.sh
- install-user.sh
- UnitResolutionTests
- get_manager
- import_video
- main_paths.py
- WasapiError
- media_source_key
- summary_source_rows
- matched_sensitive_pattern
- src/main.tsx
- App
- videoTime
- generate_visual_activities
- WasapiCapture
- videoTime
- App

## God Nodes (most connected - your core abstractions)
1. `ConfigTests` - 73 edges
2. `connect()` - 72 edges
3. `ActionResult` - 64 edges
4. `VideoLoop` - 38 edges
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

## Communities (61 total, 9 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.05
Nodes (12): speaker_profiles(), captured_video_session(), Uma unit transitória coletada equivale a um job já parado., Lê a identidade portátil deixada pelo gravador seletivo. Vídeos antigos só têm…, stop_target_is_already_gone(), daily_narrative_target(), Recupera JSON que o parser do Ollama classificou todo como thinking., recover_json_from_thinking() (+4 more)

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
Nodes (22): AudioConfig, CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional. Cada SO…, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco. Retorna ``None``…, Prepara o roteamento de áudio (no-op onde não for necessário)., Desfaz o roteamento de áudio (no-op onde não for necessário). (+14 more)

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
Cohesion: 0.08
Nodes (24): parse_video_app_rule(), Lista de expressões de um arquivo de padrões, ignorando comentários., Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., read_patterns(), _install_stop_handlers(), Atende todos os sinais de parada que o SO pode mandar. No Windows o supervisor…, foreground_details(), log() (+16 more)

### Community 9 - "BaseModel"
Cohesion: 0.09
Nodes (32): _apply_storage_runtime(), _apply_video_runtime(), atomic_write(), atomic_write_if_changed(), ContextUpdate, get_sensitive_windows(), get_storage_settings(), MarkerUpdate (+24 more)

### Community 10 - "Lume no Windows"
Cohesion: 0.08
Nodes (23): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+15 more)

### Community 11 - "test_main.py"
Cohesion: 0.09
Nodes (13): overlapping_sources(), _activity_groups(), filter_hallucinated_segments(), merge_source_transcripts(), merge_transcript_sources(), normalized_transcript_text(), private_context_terms(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas. (+5 more)

### Community 12 - "get_backend"
Cohesion: 0.24
Nodes (11): capture_frames(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver. A mesma regra nos dois…, Captura um conjunto de frames com a configuração atual., test_screen(), get_backend(), Devolve o backend do SO atual (memorizado). ``force``…, main() (+3 more)

### Community 13 - "winscreen.py"
Cohesion: 0.06
Nodes (36): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows. Centraliza as poucas…, Diretório para arquivos efêmeros (locks, estado volátil). Linux usa…, Arquivo que sinaliza "estou gravando vídeo agora". É como o laço de vídeo pede…, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``. Retorna ``True`` se conseguiu…, runtime_dir() (+28 more)

### Community 14 - "WindowsServiceManager"
Cohesion: 0.05
Nodes (28): _JobObject, _pipeline(), _Process, ABC, Path, Popen, _python(), Gerenciamento de serviços independente de sistema operacional. No Linux o… (+20 more)

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "ActionResult"
Cohesion: 0.26
Nodes (7): ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API., ResamplerTests, StereoAudioTests, SystemdFallbackTests

### Community 18 - "WindowsCaptureBackend"
Cohesion: 0.12
Nodes (10): ImageDiffTests, Monitor, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Um monitor físico: rótulo estável + geometria em pixels do desktop., Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga. Dois formatos de saída…, Dispositivo dshow capaz de gravar a saída, se algum existir. Só diagnóstico: a… (+2 more)

### Community 19 - "pipeline.py"
Cohesion: 0.15
Nodes (40): _activity_image(), adaptive_web_research(), analyze_video_chapter(), audio_channel_count(), audio_stream_count(), compact_processed_audio(), compact_saved_capture(), describe_long_video() (+32 more)

### Community 20 - "Path"
Cohesion: 0.11
Nodes (26): cancel_video_audio_track_job(), cancel_video_audio_tracks(), delete_video(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), migrate_legacy_cache_file(), probe_video_audio_tracks() (+18 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.19
Nodes (20): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+12 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "run"
Cohesion: 0.19
Nodes (15): audio_file(), _audio_streams(), capture_speaker_sample(), process_file(), ProcessFileRequest, run(), safe_audio_path(), safe_screen_path() (+7 more)

### Community 29 - "get"
Cohesion: 0.13
Nodes (21): backfill_confirmed_voice_observations(), capture_days(), enroll_voice_identity(), get_screen_settings(), get_video_settings(), health(), list_ollama_models(), _network_values() (+13 more)

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

### Community 34 - "connect"
Cohesion: 0.11
Nodes (35): connect(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_video_analysis(), cancel_video_session(), capture_action(), create_video_marker() (+27 more)

### Community 35 - "wasapi.py"
Cohesion: 0.19
Nodes (22): _AudioClientActivationParams, _Blob, _call(), _check(), default_endpoint_name(), _device_enumerator(), ensure_com(), _friendly_name() (+14 more)

### Community 37 - "main.py"
Cohesion: 0.19
Nodes (19): row_dict(), _audio_channels(), capture_change_test_frames(), capture_payload(), captures(), compare_screen_change_test(), hourly_timeline(), list_files() (+11 more)

### Community 38 - "test_services.py"
Cohesion: 0.12
Nodes (12): ObsWindowSpecTests, skipUnless, Testes das peças que tornam o app portável entre Linux e Windows. Rodam nos…, O identificador de janela do OBS é ``título:classe:executável``. Um título com…, Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., ScreenConfigTests, VideoHotkeyTests, VideoMarkerTransitionTests (+4 more)

### Community 39 - "winrecord.py"
Cohesion: 0.15
Nodes (12): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _mix(), _multichannel(), array, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.…, Soma as fontes com saturação e converte para PCM s16le. (+4 more)

### Community 45 - "UnitResolutionTests"
Cohesion: 0.36
Nodes (3): Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), UnitResolutionTests

### Community 46 - "get_manager"
Cohesion: 0.22
Nodes (10): cancel_video_audio_track_jobs(), get_schedule(), lifespan(), migrate_legacy_media_caches(), process_video_session_job(), Move caches antigos do perfil para a raiz de armazenamento selecionada., set_schedule(), get_manager() (+2 more)

### Community 47 - "import_video"
Cohesion: 0.18
Nodes (12): bounded_video_range(), import_video(), local_origin_only(), origin_allowed(), datetime, Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., remote_client_allowed(), video_file() (+4 more)

### Community 48 - "main_paths.py"
Cohesion: 0.13
Nodes (15): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., _config_dir(), configured_storage_root(), Path, Onde ficam ``tela.conf`` e a lista de janelas sensíveis. No Linux, o lugar de… (+7 more)

### Community 49 - "WasapiError"
Cohesion: 0.25
Nodes (4): GUID, Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, OSError

### Community 50 - "media_source_key"
Cohesion: 0.18
Nodes (17): backfill_video_session_durations(), join_video_session(), list_video_sessions(), list_videos(), media_source_key(), media_source_name(), Retorna uma identidade de mídia portátil entre Linux e Windows. Registros…, Resolve uma identidade portátil ou um caminho legado na raiz atual. (+9 more)

### Community 51 - "summary_source_rows"
Cohesion: 0.20
Nodes (8): apply_exact_game_durations(), game_activity_rows(), Sessões monitoradas recortadas ao dia local, inclusive ao cruzar meia-noite., Substitui estimativas da IA pelos intervalos medidos pelo contador da sidebar., Memórias do dia, representando cada sessão de vídeo apenas uma vez., Valida referências da IA e protege os arquivos escolhidos., summary_source_rows(), validate_relevant_media()

### Community 52 - "matched_sensitive_pattern"
Cohesion: 0.29
Nodes (5): PrivacyTests, matched_sensitive_pattern(), Path, Primeiro padrão sensível (regex, case-insensitive) que casa com a janela. Mesma…, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados. ``stamp``…

### Community 54 - "src/main.tsx"
Cohesion: 0.08
Nodes (9): CapturaTab, dayViews, EditableVideoSpeaker, gameCovers, icons, labels, lensLabels, Panel (+1 more)

### Community 55 - "App"
Cohesion: 0.20
Nodes (11): Capture, Status, uploadVideo(), VideoSettings, App(), canonicalGameName(), groupCaptures(), SessionCard() (+3 more)

### Community 56 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 57 - "generate_visual_activities"
Cohesion: 0.17
Nodes (14): initialize(), discover(), generate_hourly_summaries(), generate_summary(), generate_visual_activities(), main(), multimodal_context(), process_video_session() (+6 more)

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers. Média…, Um fluxo de captura: microfone padrão ou loopback da saída padrão. A saída de…, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio). Um fluxo…, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

## Knowledge Gaps
- **101 isolated node(s):** `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` (+96 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `ConfigTests`, `connect`, `main.py`, `test_services.py`, `BaseModel`, `test_main.py`, `UnitResolutionTests`, `WindowsServiceManager`, `media_source_key`, `WindowsCaptureBackend`, `Path`, `matched_sensitive_pattern`, `run`, `get`, `Path`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `test_main.py`, `import_video`, `ActionResult`, `summary_source_rows`, `pipeline.py`, `audio_intelligence.py`, `generate_visual_activities`, `get`?**
  _High betweenness centrality (0.087) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `ActionResult` to `ConfigTests`, `test_services.py`, `test_main.py`, `UnitResolutionTests`, `get_manager`, `WindowsServiceManager`, `WindowsCaptureBackend`, `matched_sensitive_pattern`, `Path`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `ConfigTests` (e.g. with `ActionResult` and `SystemdServiceManager`) actually correct?**
  _`ConfigTests` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 33 inferred relationships involving `ActionResult` (e.g. with `ContextUpdate` and `MarkerCreate`) actually correct?**
  _`ActionResult` has 33 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `VideoLoop` (e.g. with `ImageDiffTests` and `ObsWindowSpecTests`) actually correct?**
  _`VideoLoop` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem` to the rest of the system?**
  _101 weakly-connected nodes found - possible documentation gaps or missing edges._