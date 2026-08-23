# Graph Report - lume  (2026-08-07)

## Corpus Check
- 45 files · ~48,545 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 836 nodes · 1855 edges · 44 communities (34 shown, 10 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 98 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- pipeline.py
- main.tsx
- package.json
- compilerOptions
- CaptureBackend
- obs.py
- wasapi.py
- Handoff: Lume — app de memória de tela & áudio
- winvideo.py
- WindowsServiceManager
- Lume no Windows
- winscreen.py
- media_source_key
- WindowsCaptureBackend
- main.py
- game-video-loop
- get_backend
- AGENTS.md
- connect
- Path
- LinuxCaptureBackend
- install-audio-intelligence
- .grab_frame
- capture-frame
- services.py
- add-video-marker
- ActionResult
- install-captura-dia.sh
- get
- test_services.py
- audio-bus.sh
- _install_stop_handlers
- post
- BaseModel
- Path
- capture-loop
- runtime.py
- capture_frames
- grava-audio.sh
- install-lume.sh
- install-user.sh

## God Nodes (most connected - your core abstractions)
1. `ActionResult` - 55 edges
2. `connect()` - 54 edges
3. `ConfigTests` - 32 edges
4. `AudioConfig` - 26 edges
5. `media_source_key()` - 25 edges
6. `SystemdServiceManager` - 25 edges
7. `WindowsServiceManager` - 25 edges
8. `resolve_media_source()` - 19 edges
9. `get_backend()` - 19 edges
10. `analyze_video_audio()` - 18 edges

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

## Communities (44 total, 10 thin omitted)

### Community 0 - "pipeline.py"
Cohesion: 0.07
Nodes (11): captured_video_session(), Uma unit transitória coletada equivale a um job já parado., Lê a identidade portátil deixada pelo gravador seletivo.      Vídeos antigos só, stop_target_is_already_gone(), filter_hallucinated_segments(), normalized_transcript_text(), parse_json_response(), Recupera JSON que o parser do Ollama classificou todo como thinking. (+3 more)

### Community 1 - "main.tsx"
Cohesion: 0.06
Nodes (40): AnalysisTrace, api, AudioEvent, Capture, DaySummary, HourSummary, OllamaModel, QueueItem (+32 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "CaptureBackend"
Cohesion: 0.12
Nodes (12): CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco.          Retorna ``N, Prepara o roteamento de áudio (no-op onde não for necessário)., Desfaz o roteamento de áudio (no-op onde não for necessário)., argv do ``ffmpeg`` que grava mic + saída do sistema num único WAV.          O co (+4 more)

### Community 5 - "obs.py"
Cohesion: 0.08
Nodes (46): any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), ensure_scene(), find_installation(), is_provisioned() (+38 more)

### Community 6 - "wasapi.py"
Cohesion: 0.06
Nodes (44): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, _call(), _check(), dbfs(), default_endpoint_name(), _device_enumerator(), ensure_com() (+36 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "winvideo.py"
Cohesion: 0.07
Nodes (31): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows.  Centraliza as poucas, Diretório para arquivos efêmeros (locks, estado volátil).      Linux usa ``XDG_R, Arquivo que sinaliza "estou gravando vídeo agora".      É como o laço de vídeo p, Trava exclusiva e não-bloqueante sobre ``path``.      Retorna ``True`` se conseg, runtime_dir(), video_recording_flag() (+23 more)

### Community 9 - "WindowsServiceManager"
Cohesion: 0.05
Nodes (28): _JobObject, _pipeline(), _Process, ABC, Path, _python(), Gerenciamento de serviços independente de sistema operacional.  No Linux o sys, Chamado quando a API sobe. (+20 more)

### Community 10 - "Lume no Windows"
Cohesion: 0.08
Nodes (23): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+15 more)

### Community 11 - "winscreen.py"
Cohesion: 0.20
Nodes (10): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.      ``ut, read_shell_config(), _as_bool(), _as_float(), _as_int(), _parse_config(), Laço contínuo de captura de telas — porte de ``bin/capture-loop`` para Python., Lê o ``tela.conf`` (formato ``CHAVE=valor`` do shell). (+2 more)

### Community 12 - "media_source_key"
Cohesion: 0.15
Nodes (18): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., delete_video(), list_video_sessions(), _config_dir(), configured_storage_root() (+10 more)

### Community 13 - "WindowsCaptureBackend"
Cohesion: 0.13
Nodes (9): Monitor, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Um monitor físico: rótulo estável + geometria em pixels do desktop., Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga.          Dois formatos d, Dispositivo dshow capaz de gravar a saída, se algum existir.          Só diagnós, argv do gravador WASAPI (ver :mod:`app.capture.winrecord`).          Não é ffmpe (+1 more)

### Community 14 - "main.py"
Cohesion: 0.13
Nodes (25): connect(), row_dict(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_video_analysis(), cancel_video_session(), capture_action() (+17 more)

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "get_backend"
Cohesion: 0.23
Nodes (10): Path, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados.          ``, Valores de ``tela.conf`` relevantes para a captura de um frame., ScreenConfig, get_backend(), Devolve o backend do SO atual (memorizado).      ``force`` (``"linux"``/``"windo, main(), _measure_volume() (+2 more)

### Community 18 - "connect"
Cohesion: 0.24
Nodes (28): initialize(), adaptive_web_research(), analyze_video_chapter(), describe_long_video(), describe_video(), discover(), extract_adaptive_keyframes(), format_video_time() (+20 more)

### Community 23 - ".grab_frame"
Cohesion: 0.25
Nodes (17): analyze_video_audio(), available(), consolidate_events(), detect_events(), diarize(), embedding_for_sample(), enrich_segments(), _event_name() (+9 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "services.py"
Cohesion: 0.16
Nodes (20): atomic_write(), audio_file(), delete_capture(), delete_capture_file(), delete_file(), get_storage_settings(), get_video_settings(), parse_shell_config() (+12 more)

### Community 27 - "ActionResult"
Cohesion: 0.07
Nodes (31): ActionResult, Encontra a definição da unit e o argumento de template (``@dia``)., Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., _resolve(), SystemdServiceManager, ImageDiffTests, ObsWindowSpecTests, PrivacyTests (+23 more)

### Community 29 - "get"
Cohesion: 0.16
Nodes (16): capture_speaker_sample(), import_video(), list_videos(), local_origin_only(), datetime, run(), search(), test_audio() (+8 more)

### Community 30 - "test_services.py"
Cohesion: 0.17
Nodes (15): capture_change_test_frames(), capture_frames(), compare_screen_change_test(), directory_stats(), get_screen_settings(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver.      A mesma regra nos doi, Captura um conjunto de frames com a configuração atual. (+7 more)

### Community 31 - "audio-bus.sh"
Cohesion: 0.67
Nodes (6): load_loopback(), setup(), audio-bus.sh script, status(), unload_bus(), wait_pipewire()

### Community 32 - "_install_stop_handlers"
Cohesion: 0.26
Nodes (10): describe_screen(), known_voice_profiles(), monitor_key(), process_pending(), process_specific(), save_speaker_observations(), sha256(), short_video_analysis_prompt() (+2 more)

### Community 33 - "post"
Cohesion: 0.20
Nodes (12): get_schedule(), join_video_session(), preserve_video(), process_video(), process_video_session_job(), safe_video_path(), ScheduleSettings, set_schedule() (+4 more)

### Community 34 - "BaseModel"
Cohesion: 0.14
Nodes (23): ContextUpdate, create_video_marker(), create_video_session(), get_sensitive_windows(), lifespan(), list_voice_identities(), MarkerCreate, MarkerUpdate (+15 more)

### Community 35 - "Path"
Cohesion: 0.24
Nodes (7): main(), _monitor_key(), Path, Identidade do monitor a partir do nome do arquivo (``..._mon1_DP-1.png``)., Motivo para não capturar agora, ou ``None`` se pode capturar., ScreenLoop, _thumbnail()

### Community 37 - "runtime.py"
Cohesion: 0.50
Nodes (4): _parse_max_geometry(), Interpreta ``"1920x1080>"`` -> (1920, 1080, apenas_reduzir)., Dimensões finais respeitando ``MAX_GEOMETRY`` (mantém proporção)., _scaled_size()

### Community 39 - "capture_frames"
Cohesion: 0.28
Nodes (8): backfill_confirmed_voice_observations(), enroll_voice_identity(), _normalized_average(), Recalcula um perfil dando um único voto a cada gravação., rebuild_voice_identity(), SpeakerLabelUpdate, update_capture_speaker(), update_video_speaker()

## Knowledge Gaps
- **79 isolated node(s):** `grava-audio.sh script`, `name`, `private`, `version`, `type` (+74 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **10 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `pipeline.py`, `post`, `BaseModel`, `_install_stop_handlers`, `capture_frames`, `WindowsServiceManager`, `main.py`, `services.py`, `get`, `test_services.py`?**
  _High betweenness centrality (0.095) - this node is a cross-community bridge._
- **Why does `get_backend()` connect `get_backend` to `BaseModel`, `CaptureBackend`, `winvideo.py`, `winscreen.py`, `WindowsCaptureBackend`, `LinuxCaptureBackend`, `.grab_frame`, `ActionResult`, `get`, `test_services.py`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `AudioConfig` connect `ActionResult` to `BaseModel`, `CaptureBackend`, `WindowsCaptureBackend`, `get_backend`, `LinuxCaptureBackend`, `get`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Are the 28 inferred relationships involving `ActionResult` (e.g. with `ContextUpdate` and `MarkerCreate`) actually correct?**
  _`ActionResult` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ConfigTests` (e.g. with `ActionResult` and `SystemdServiceManager`) actually correct?**
  _`ConfigTests` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `AudioConfig` (e.g. with `ImageDiffTests` and `ObsWindowSpecTests`) actually correct?**
  _`AudioConfig` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `grava-audio.sh script`, `name`, `private` to the rest of the system?**
  _79 weakly-connected nodes found - possible documentation gaps or missing edges._