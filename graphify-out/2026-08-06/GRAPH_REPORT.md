# Graph Report - lume  (2026-08-06)

## Corpus Check
- 44 files · ~45,832 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 805 nodes · 1754 edges · 38 communities (30 shown, 8 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 97 edges (avg confidence: 0.55)
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
- WindowsCaptureBackend
- matched_sensitive_pattern
- main.py
- game-video-loop
- AGENTS.md
- connect
- Settings
- install-audio-intelligence
- capture-frame
- add-video-marker
- ActionResult
- install-captura-dia.sh
- run
- audio-bus.sh
- WindowsCaptureBackend
- get_manager
- LinuxCaptureBackend
- capture-loop
- get_backend
- grava-audio.sh
- install-lume.sh
- install-user.sh
- set_video_settings

## God Nodes (most connected - your core abstractions)
1. `ActionResult` - 55 edges
2. `connect()` - 52 edges
3. `ConfigTests` - 28 edges
4. `AudioConfig` - 26 edges
5. `SystemdServiceManager` - 25 edges
6. `WindowsServiceManager` - 25 edges
7. `get_backend()` - 19 edges
8. `analyze_video_audio()` - 18 edges
9. `WindowsCaptureBackend` - 18 edges
10. `MarkerHotkey` - 18 edges

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

## Communities (38 total, 8 thin omitted)

### Community 0 - "pipeline.py"
Cohesion: 0.06
Nodes (68): analyze_video_audio(), available(), consolidate_events(), detect_events(), diarize(), embedding_for_sample(), enrich_segments(), _event_name() (+60 more)

### Community 1 - "main.tsx"
Cohesion: 0.06
Nodes (38): AnalysisTrace, api, AudioEvent, Capture, DaySummary, HourSummary, QueueItem, QueueJob (+30 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "CaptureBackend"
Cohesion: 0.10
Nodes (16): CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco.          Retorna ``N, Prepara o roteamento de áudio (no-op onde não for necessário)., Desfaz o roteamento de áudio (no-op onde não for necessário)., argv do ``ffmpeg`` que grava mic + saída do sistema num único WAV.          O co (+8 more)

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
Nodes (29): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows.  Centraliza as poucas, Arquivo que sinaliza "estou gravando vídeo agora".      É como o laço de vídeo p, Trava exclusiva e não-bloqueante sobre ``path``.      Retorna ``True`` se conseg, video_recording_flag(), Lista de expressões de um arquivo de padrões, ignorando comentários., read_patterns() (+21 more)

### Community 9 - "WindowsServiceManager"
Cohesion: 0.05
Nodes (28): _JobObject, _pipeline(), _Process, ABC, Path, _python(), Gerenciamento de serviços independente de sistema operacional.  No Linux o sys, Chamado quando a API sobe. (+20 more)

### Community 10 - "Lume no Windows"
Cohesion: 0.08
Nodes (23): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+15 more)

### Community 11 - "winscreen.py"
Cohesion: 0.11
Nodes (19): Diretório para arquivos efêmeros (locks, estado volátil).      Linux usa ``XDG_R, runtime_dir(), Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.      ``ut, read_shell_config(), _as_bool(), _as_float(), _as_int(), main() (+11 more)

### Community 12 - "WindowsCaptureBackend"
Cohesion: 0.22
Nodes (11): audio_file(), delete_capture(), delete_capture_file(), delete_file(), process_file(), ProcessFileRequest, safe_audio_path(), safe_screen_path() (+3 more)

### Community 13 - "matched_sensitive_pattern"
Cohesion: 0.29
Nodes (4): matched_sensitive_pattern(), Path, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados.          ``, Primeiro padrão sensível (regex, case-insensitive) que casa com a janela.      M

### Community 14 - "main.py"
Cohesion: 0.12
Nodes (30): capture_change_test_frames(), compare_screen_change_test(), ContextUpdate, create_video_marker(), create_video_session(), delete_video(), get_sensitive_windows(), join_video_session() (+22 more)

### Community 15 - "game-video-loop"
Cohesion: 0.31
Nodes (6): game-video-loop script, cleanup(), finish_segment(), is_selected_app(), pause_background_captures(), resume_background_captures()

### Community 18 - "connect"
Cohesion: 0.14
Nodes (23): connect(), row_dict(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_video_analysis(), cancel_video_session(), capture_action() (+15 more)

### Community 19 - "Settings"
Cohesion: 0.22
Nodes (15): backfill_confirmed_voice_observations(), delete_video_session(), enroll_voice_identity(), get_storage_settings(), list_video_sessions(), _normalized_average(), Path, Recalcula um perfil dando um único voto a cada gravação. (+7 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 27 - "ActionResult"
Cohesion: 0.07
Nodes (31): Uma unit transitória coletada equivale a um job já parado., stop_target_is_already_gone(), ActionResult, Encontra a definição da unit e o argumento de template (``@dia``)., Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., _resolve(), SystemdServiceManager, ImageDiffTests (+23 more)

### Community 29 - "run"
Cohesion: 0.16
Nodes (16): capture_speaker_sample(), import_video(), list_videos(), local_origin_only(), datetime, run(), search(), test_audio() (+8 more)

### Community 31 - "audio-bus.sh"
Cohesion: 0.67
Nodes (6): load_loopback(), setup(), audio-bus.sh script, status(), unload_bus(), wait_pipewire()

### Community 32 - "WindowsCaptureBackend"
Cohesion: 0.21
Nodes (5): Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga.          Dois formatos d, Dispositivo dshow capaz de gravar a saída, se algum existir.          Só diagnós, argv do gravador WASAPI (ver :mod:`app.capture.winrecord`).          Não é ffmpe, WindowsCaptureBackend

### Community 33 - "get_manager"
Cohesion: 0.29
Nodes (8): get_schedule(), lifespan(), process_video_session_job(), ScheduleSettings, set_schedule(), get_manager(), Gerenciador do sistema atual (memorizado)., FastAPI

### Community 35 - "LinuxCaptureBackend"
Cohesion: 0.13
Nodes (6): Monitor, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Um monitor físico: rótulo estável + geometria em pixels do desktop., LinuxCaptureBackend, Path

### Community 39 - "get_backend"
Cohesion: 0.22
Nodes (13): capture_frames(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver.      A mesma regra nos doi, Captura um conjunto de frames com a configuração atual., test_screen(), Valores de ``tela.conf`` relevantes para a captura de um frame., ScreenConfig, get_backend() (+5 more)

### Community 45 - "set_video_settings"
Cohesion: 0.22
Nodes (10): atomic_write(), directory_stats(), get_screen_settings(), get_video_settings(), parse_shell_config(), ScreenSettings, set_video_settings(), status() (+2 more)

## Knowledge Gaps
- **79 isolated node(s):** `grava-audio.sh script`, `name`, `private`, `version`, `type` (+74 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `pipeline.py`, `get_manager`, `WindowsServiceManager`, `WindowsCaptureBackend`, `set_video_settings`, `main.py`, `connect`, `Settings`, `run`?**
  _High betweenness centrality (0.096) - this node is a cross-community bridge._
- **Why does `get_backend()` connect `get_backend` to `WindowsCaptureBackend`, `pipeline.py`, `LinuxCaptureBackend`, `CaptureBackend`, `winvideo.py`, `winscreen.py`, `main.py`, `ActionResult`, `run`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Why does `AudioConfig` connect `ActionResult` to `WindowsCaptureBackend`, `LinuxCaptureBackend`, `CaptureBackend`, `get_backend`, `main.py`, `run`?**
  _High betweenness centrality (0.042) - this node is a cross-community bridge._
- **Are the 28 inferred relationships involving `ActionResult` (e.g. with `ContextUpdate` and `MarkerCreate`) actually correct?**
  _`ActionResult` has 28 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ConfigTests` (e.g. with `ActionResult` and `SystemdServiceManager`) actually correct?**
  _`ConfigTests` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `AudioConfig` (e.g. with `ImageDiffTests` and `ObsWindowSpecTests`) actually correct?**
  _`AudioConfig` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `grava-audio.sh script`, `name`, `private` to the rest of the system?**
  _79 weakly-connected nodes found - possible documentation gaps or missing edges._