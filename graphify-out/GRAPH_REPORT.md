# Graph Report - lume  (2026-08-20)

## Corpus Check
- 50 files · ~75,585 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1191 nodes · 2789 edges · 66 communities (56 shown, 10 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 199 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- ConfigTests
- src/api.ts
- package.json
- compilerOptions
- Monitor
- obs.py
- record
- Handoff: Lume — app de memória de tela & áudio
- VideoLoop
- main.py
- Lume no Windows
- test_main.py
- capture_frames
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
- rebuild_voice_identity
- Path
- audio-bus.sh
- src-backup-2026-08-09/api.ts
- src-backup-2026-08-09/main.tsx
- connect
- wasapi.py
- capture-loop
- get
- test_services.py
- winrecord.py
- grava-audio.sh
- install-lume.sh
- install-user.sh
- UnitResolutionTests
- lifespan
- local_origin_only
- main_paths.py
- WasapiError
- media_source_key
- summary_source_rows
- matched_sensitive_pattern
- services.py
- src/main.tsx
- App
- videoTime
- generate_visual_activities
- WasapiCapture
- videoTime
- ._follow_capture_policy
- ._start
- App
- ObsWindowSpecTests
- _LazyOle32

## God Nodes (most connected - your core abstractions)
1. `connect()` - 77 edges
2. `ConfigTests` - 73 edges
3. `ActionResult` - 69 edges
4. `VideoLoop` - 43 edges
5. `SystemdServiceManager` - 40 edges
6. `WindowsCaptureBackend` - 35 edges
7. `LinuxCaptureBackend` - 34 edges
8. `AudioConfig` - 33 edges
9. `Monitor` - 32 edges
10. `media_source_key()` - 30 edges

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

## Communities (66 total, 10 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.04
Nodes (11): speaker_profiles(), captured_video_session(), Uma unit transitória coletada equivale a um job já parado., Lê a identidade portátil deixada pelo gravador seletivo.      Vídeos antigos só, stop_target_is_already_gone(), daily_narrative_target(), multimodal_context(), Agrupa telas e áudios sobrepostos em momentos únicos para as sínteses. (+3 more)

### Community 1 - "src/api.ts"
Cohesion: 0.07
Nodes (27): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+19 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "Monitor"
Cohesion: 0.08
Nodes (29): CaptureBackend, parse_video_app_rule(), ABC, Path, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco.          Retorna ``N, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados.          `` (+21 more)

### Community 5 - "obs.py"
Cohesion: 0.07
Nodes (52): any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), _encode_field(), ensure_scene(), find_installation() (+44 more)

### Community 6 - "record"
Cohesion: 0.17
Nodes (10): ProcessLoopbackCapture, Loopback que inclui ou exclui a árvore de um processo do Windows., Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record() (+2 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.08
Nodes (21): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows.  Executado com ``pythonw.exe`` pe, foreground_details(), log(), looks_blank(), main() (+13 more)

### Community 9 - "main.py"
Cohesion: 0.07
Nodes (49): atomic_write(), cancel_video_audio_track_jobs(), compare_screen_change_test(), ContextUpdate, create_video_marker(), create_video_session(), delete_capture(), delete_capture_file() (+41 more)

### Community 10 - "Lume no Windows"
Cohesion: 0.07
Nodes (24): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+16 more)

### Community 11 - "test_main.py"
Cohesion: 0.09
Nodes (17): overlapping_sources(), _activity_groups(), apply_exact_game_durations(), filter_hallucinated_segments(), game_activity_rows(), merge_source_transcripts(), merge_transcript_sources(), normalized_transcript_text() (+9 more)

### Community 12 - "capture_frames"
Cohesion: 0.23
Nodes (12): capture_change_test_frames(), capture_frames(), get_screen_settings(), get_video_settings(), parse_shell_config(), privacy_decision(), Estado operacional do gravador, separado da mera configuração ativa., Janela ativa e o motivo para não capturar, se houver.      A mesma regra nos doi (+4 more)

### Community 13 - "winscreen.py"
Cohesion: 0.09
Nodes (20): Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., matched_sensitive_pattern(), Primeiro padrão sensível (regex, case-insensitive) que casa com a janela.      M, _install_stop_handlers(), Atende todos os sinais de parada que o SO pode mandar.      No Windows o supervi, _as_bool(), _as_float(), _as_int() (+12 more)

### Community 14 - "WindowsServiceManager"
Cohesion: 0.21
Nodes (3): Supervisor: mantém os processos de captura vivos e agenda o processamento., Combine selective-video and user-idle pauses without racing them.          Aud, WindowsServiceManager

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "ActionResult"
Cohesion: 0.13
Nodes (22): ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, ObsWindowSpecTests, PrivacyTests, Testes das peças que tornam o app portável entre Linux e Windows.  Rodam nos doi, O identificador de janela do OBS é ``título:classe:executável``.      Um título, Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API. (+14 more)

### Community 18 - "WindowsCaptureBackend"
Cohesion: 0.12
Nodes (9): Monitor, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Um monitor físico: rótulo estável + geometria em pixels do desktop., _parse_max_geometry(), Path, Interpreta ``"1920x1080>"`` -> (1920, 1080, apenas_reduzir)., Dimensões finais respeitando ``MAX_GEOMETRY`` (mantém proporção). (+1 more)

### Community 19 - "pipeline.py"
Cohesion: 0.19
Nodes (21): analyze_video_chapter(), audio_channel_count(), audio_stream_count(), compact_processed_audio(), describe_long_video(), describe_video(), extract_adaptive_keyframes(), format_video_time() (+13 more)

### Community 20 - "Path"
Cohesion: 0.11
Nodes (29): cancel_video_audio_track_job(), cancel_video_audio_tracks(), delete_video(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), migrate_legacy_cache_file(), probe_video_audio_tracks() (+21 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.19
Nodes (20): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+12 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "run"
Cohesion: 0.19
Nodes (15): audio_file(), _audio_streams(), import_video(), process_file(), ProcessFileRequest, datetime, run(), safe_audio_path() (+7 more)

### Community 27 - "_ActivationHandler"
Cohesion: 0.25
Nodes (3): _ActivationHandler, GUID, Implementação mínima de IActivateAudioInterfaceCompletionHandler.

### Community 29 - "rebuild_voice_identity"
Cohesion: 0.15
Nodes (16): backfill_confirmed_voice_observations(), backfill_video_session_durations(), delete_video_session(), enroll_voice_identity(), list_video_sessions(), _normalized_average(), Resolve uma identidade portátil ou um caminho legado na raiz atual., resolve_media_source() (+8 more)

### Community 30 - "Path"
Cohesion: 0.13
Nodes (6): LinuxIdlePauseTests, _pausable(), Path, Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)., SupervisorTests, VideoSettingsTests

### Community 31 - "audio-bus.sh"
Cohesion: 0.34
Nodes (13): load_loopback(), make_null_sink(), selected_mic(), setup(), audio-bus.sh script, sink_exists(), source_exists(), status() (+5 more)

### Community 32 - "src-backup-2026-08-09/api.ts"
Cohesion: 0.07
Nodes (26): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+18 more)

### Community 33 - "src-backup-2026-08-09/main.tsx"
Cohesion: 0.10
Nodes (5): EditableVideoSpeaker, icons, labels, Panel, View

### Community 34 - "connect"
Cohesion: 0.09
Nodes (38): connect(), row_dict(), _audio_channels(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_screen_sequence(), cancel_video_analysis() (+30 more)

### Community 35 - "wasapi.py"
Cohesion: 0.23
Nodes (18): _AudioClientActivationParams, _Blob, _call(), _check(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints() (+10 more)

### Community 37 - "get"
Cohesion: 0.16
Nodes (17): _apply_storage_runtime(), _apply_video_runtime(), atomic_write_if_changed(), get_storage_settings(), Write a config only when its contents changed., _report_runtime_failure(), _restart_screen_runtime(), ScreenSettings (+9 more)

### Community 38 - "test_services.py"
Cohesion: 0.18
Nodes (5): LinuxAudioTrackTests, Gravação em faixas separadas (3 canais) no backend Linux., LinuxCaptureBackend, Path, argv do ffmpeg que grava mic + Discord + sistema num WAV de 3 canais.          M

### Community 39 - "winrecord.py"
Cohesion: 0.13
Nodes (15): dbfs(), default_endpoint_name(), Nome do endpoint padrão, ou ``None`` se não houver nenhum., Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), main(), _mix(), _multichannel() (+7 more)

### Community 45 - "UnitResolutionTests"
Cohesion: 0.20
Nodes (4): Uma unit supervisionada.      ``simple`` roda enquanto o serviço estiver ligad, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef

### Community 46 - "lifespan"
Cohesion: 0.23
Nodes (10): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows.  Centraliza as poucas, Diretório para arquivos efêmeros (locks, estado volátil).      Linux usa ``XDG_R, Arquivo que sinaliza "estou gravando vídeo agora".      É como o laço de vídeo p, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``.      Retorna ``True`` se conseg, runtime_dir() (+2 more)

### Community 47 - "local_origin_only"
Cohesion: 0.25
Nodes (8): bounded_video_range(), local_origin_only(), origin_allowed(), Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., remote_client_allowed(), video_file(), Request, StreamingResponse

### Community 48 - "main_paths.py"
Cohesion: 0.16
Nodes (17): initialize(), _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., join_video_session(), list_videos(), _config_dir() (+9 more)

### Community 49 - "WasapiError"
Cohesion: 0.40
Nodes (4): Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, WAVEFORMATEXTENSIBLE, OSError

### Community 50 - "media_source_key"
Cohesion: 0.17
Nodes (6): Arquivo de estado que o laço de vídeo cria enquanto controla as capturas., (Re)inicia o swayidle apontando os eventos para o flag de idle., Anota que a captura deve (ou não) voltar na próxima abertura do Lume., Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., _unknown(), _video_pause_file()

### Community 51 - "summary_source_rows"
Cohesion: 0.19
Nodes (10): ImageDiffTests, Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg.  O laço de captura do Linux usa, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar. (+2 more)

### Community 52 - "matched_sensitive_pattern"
Cohesion: 0.21
Nodes (9): compact_saved_capture(), known_voice_profiles(), monitor_key(), process_pending(), process_specific(), Compacta uma captura concluída e registra o novo hash ou um aviso., save_speaker_observations(), sha256() (+1 more)

### Community 53 - "services.py"
Cohesion: 0.10
Nodes (12): ABC, Executa ``start``/``stop``/``restart``/``try-restart``/``enable``/``disable``., Horário configurado do processamento noturno e se está ativo., Reprograma o processamento noturno., Dispara um job avulso sob um nome de unit, para poder cancelá-lo depois., Reinicia a própria interface (usado ao trocar o local dos dados)., Chamado quando a API sobe., Chamado quando a API desce. (+4 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.07
Nodes (12): CapturaTab, dayViews, EditableVideoSpeaker, gameCovers, icons, labels, lensLabels, Panel (+4 more)

### Community 55 - "App"
Cohesion: 0.25
Nodes (9): Capture, ScreenSequenceResult, Status, uploadVideo(), VideoSettings, App(), canonicalGameName(), groupCaptures() (+1 more)

### Community 56 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 57 - "generate_visual_activities"
Cohesion: 0.16
Nodes (28): _activity_image(), adaptive_web_research(), analyze_screen_sequence(), describe_screen(), generate_hourly_summaries(), generate_summary(), generate_visual_activities(), main() (+20 more)

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers.      M, Um fluxo de captura: microfone padrão ou loopback da saída padrão.      A saída, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio).          Um, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "._follow_capture_policy"
Cohesion: 0.22
Nodes (7): _JobObject, _pipeline(), _python(), Gerenciamento de serviços independente de sistema operacional.  No Linux o sys, Amarra os processos filhos ao ciclo de vida da API.      É o que o systemd con, Return seconds since the last real keyboard or mouse input on Windows., windows_idle_seconds()

### Community 61 - "._start"
Cohesion: 0.36
Nodes (4): _Process, Path, Popen, Um processo filho supervisionado.

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

## Knowledge Gaps
- **99 isolated node(s):** `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame`, `StorageCandidate`, `WebSource` (+94 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `ConfigTests`, `connect`, `get`, `test_services.py`, `main.py`, `test_main.py`, `UnitResolutionTests`, `WindowsServiceManager`, `main_paths.py`, `media_source_key`, `._start`, `Path`, `services.py`, `summary_source_rows`, `run`, `._follow_capture_policy`, `rebuild_voice_identity`, `Path`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `test_main.py`, `local_origin_only`, `ActionResult`, `pipeline.py`, `matched_sensitive_pattern`, `audio_intelligence.py`, `generate_visual_activities`, `rebuild_voice_identity`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `ActionResult` to `ConfigTests`, `test_services.py`, `main.py`, `test_main.py`, `lifespan`, `media_source_key`, `summary_source_rows`, `services.py`, `._follow_capture_policy`, `Path`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `ConfigTests` (e.g. with `ActionResult` and `SystemdServiceManager`) actually correct?**
  _`ConfigTests` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `ActionResult` (e.g. with `ContextUpdate` and `MarkerCreate`) actually correct?**
  _`ActionResult` has 36 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `VideoLoop` (e.g. with `ImageDiffTests` and `LinuxAudioTrackTests`) actually correct?**
  _`VideoLoop` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `SystemdServiceManager` (e.g. with `ConfigTests` and `ImageDiffTests`) actually correct?**
  _`SystemdServiceManager` has 17 INFERRED edges - model-reasoned connections that need verification._