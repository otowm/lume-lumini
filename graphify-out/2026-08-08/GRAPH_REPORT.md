# Graph Report - lume  (2026-08-08)

## Corpus Check
- 45 files · ~57,565 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 957 nodes · 2271 edges · 58 communities (45 shown, 13 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 117 edges (avg confidence: 0.54)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- ConfigTests
- main.tsx
- package.json
- compilerOptions
- CaptureBackend
- obs.py
- record
- Handoff: Lume — app de memória de tela & áudio
- VideoLoop
- WindowsServiceManager
- Lume no Windows
- get
- main_paths.py
- winscreen.py
- connect
- game-video-loop
- winrecord.py
- AGENTS.md
- Path
- generate_visual_activities
- LinuxCaptureBackend
- install-audio-intelligence
- analyze_video_audio
- capture-frame
- Path
- add-video-marker
- test_services.py
- install-captura-dia.sh
- ActionResult
- WasapiCapture
- audio-bus.sh
- post
- wasapi.py
- main.py
- read_patterns
- capture-loop
- WindowsCaptureBackend
- get_backend
- test_main.py
- grava-audio.sh
- install-lume.sh
- install-user.sh
- process_pending
- resolve_media_source
- join_video_session
- WasapiError
- _ActivationHandler
- pipeline.py
- _scaled_size
- _resolve
- Settings
- ObsWindowSpecTests
- ._dshow_loopback
- runtime.py
- .list_monitors

## God Nodes (most connected - your core abstractions)
1. `connect()` - 65 edges
2. `ActionResult` - 61 edges
3. `ConfigTests` - 52 edges
4. `VideoLoop` - 32 edges
5. `AudioConfig` - 29 edges
6. `SystemdServiceManager` - 28 edges
7. `media_source_key()` - 26 edges
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

## Communities (58 total, 13 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.06
Nodes (11): captured_video_session(), Lê a identidade portátil deixada pelo gravador seletivo. Vídeos antigos só têm…, daily_narrative_target(), merge_source_transcripts(), merge_transcript_sources(), Recupera JSON que o parser do Ollama classificou todo como thinking., recover_json_from_thinking(), visually_changed() (+3 more)

### Community 1 - "main.tsx"
Cohesion: 0.05
Nodes (46): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, Capture, DaySummary, HourSummary (+38 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "CaptureBackend"
Cohesion: 0.12
Nodes (12): CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional. Cada SO…, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco. Retorna ``None``…, Prepara o roteamento de áudio (no-op onde não for necessário)., Desfaz o roteamento de áudio (no-op onde não for necessário)., argv do ``ffmpeg`` que grava mic + saída do sistema num único WAV. O comando… (+4 more)

### Community 5 - "obs.py"
Cohesion: 0.08
Nodes (49): any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), ensure_scene(), find_installation(), is_provisioned() (+41 more)

### Community 6 - "record"
Cohesion: 0.17
Nodes (10): ProcessLoopbackCapture, Loopback que inclui ou exclui a árvore de um processo do Windows., Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record() (+2 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.17
Nodes (10): foreground_details(), log(), Path, Título, classe e executável da janela em foco — o que o OBS precisa para…, Confirma uma ação aceita sem depender da interface estar em foco., Anota o instante atual da gravação. Os marcadores ficam em memória e só vão…, Salva o Replay Buffer atual e vincula o arquivo à sessão do jogo., Grava uma sessão lógica, possivelmente dividida em segmentos. (+2 more)

### Community 9 - "WindowsServiceManager"
Cohesion: 0.05
Nodes (28): _JobObject, _pipeline(), _Process, ABC, Path, _python(), Gerenciamento de serviços independente de sistema operacional. No Linux o…, Chamado quando a API sobe. (+20 more)

### Community 10 - "Lume no Windows"
Cohesion: 0.08
Nodes (23): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+15 more)

### Community 11 - "get"
Cohesion: 0.12
Nodes (31): row_dict(), _delete_media_sidecars(), delete_unkept_raw_media(), delete_unprocessed_files(), directory_stats(), get_video_settings(), health(), hourly_timeline() (+23 more)

### Community 12 - "main_paths.py"
Cohesion: 0.17
Nodes (11): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., _config_dir(), configured_storage_root(), Path, Onde ficam ``tela.conf`` e a lista de janelas sensíveis. No Linux, o lugar de… (+3 more)

### Community 13 - "winscreen.py"
Cohesion: 0.06
Nodes (38): Path, Diretório para arquivos efêmeros (locks, estado volátil). Linux usa…, Arquivo que sinaliza "estou gravando vídeo agora". É como o laço de vídeo pede…, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., runtime_dir(), video_activity_flag(), video_recording_flag(), Variação de 5 níveis é ruído de compressão, não mudança de tela. (+30 more)

### Community 14 - "connect"
Cohesion: 0.21
Nodes (16): connect(), cancel_entire_queue(), cancel_queue_item(), cancel_video_analysis(), cancel_video_session(), capture_days(), capture_payload(), captures() (+8 more)

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "winrecord.py"
Cohesion: 0.15
Nodes (12): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _mix(), _multichannel(), array, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.…, Soma as fontes com saturação e converte para PCM s16le. (+4 more)

### Community 18 - "Path"
Cohesion: 0.18
Nodes (6): Path, skipUnless, Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., SupervisorTests, VideoReplayClipTests, VideoSettingsTests

### Community 19 - "generate_visual_activities"
Cohesion: 0.15
Nodes (16): initialize(), _activity_image(), discover(), generate_hourly_summaries(), generate_summary(), generate_visual_activities(), main(), multimodal_context() (+8 more)

### Community 23 - "analyze_video_audio"
Cohesion: 0.26
Nodes (19): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), consolidate_events(), detect_events(), diarize(), embedding_for_sample() (+11 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "Path"
Cohesion: 0.14
Nodes (25): atomic_write(), _audio_channels(), audio_file(), _audio_streams(), capture_speaker_sample(), get_storage_settings(), import_video(), local_origin_only() (+17 more)

### Community 27 - "test_services.py"
Cohesion: 0.15
Nodes (14): ImageDiffTests, PrivacyTests, Testes das peças que tornam o app portável entre Linux e Windows. Rodam nos…, ResamplerTests, ScreenConfigTests, StereoAudioTests, VideoHotkeyTests, VideoMarkerTransitionTests (+6 more)

### Community 29 - "ActionResult"
Cohesion: 0.22
Nodes (7): Uma unit transitória coletada equivale a um job já parado., stop_target_is_already_gone(), ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API., SystemdFallbackTests

### Community 30 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers. Média…, Um fluxo de captura: microfone padrão ou loopback da saída padrão. A saída de…, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio). Um fluxo…, WasapiCapture

### Community 31 - "audio-bus.sh"
Cohesion: 0.67
Nodes (6): load_loopback(), setup(), audio-bus.sh script, status(), unload_bus(), wait_pipewire()

### Community 32 - "post"
Cohesion: 0.17
Nodes (16): cancel_pipeline(), capture_action(), generate_hourly_now(), generate_summary_now(), pipeline_run(), PipelineRequest, process_video_session_job(), Executa uma ação sobre units, seja qual for o sistema. (+8 more)

### Community 33 - "wasapi.py"
Cohesion: 0.19
Nodes (22): _AudioClientActivationParams, _Blob, _call(), _check(), default_endpoint_name(), _device_enumerator(), ensure_com(), _friendly_name() (+14 more)

### Community 34 - "main.py"
Cohesion: 0.11
Nodes (39): capture_change_test_frames(), capture_frames(), compare_screen_change_test(), ContextUpdate, create_video_marker(), create_video_session(), get_schedule(), get_screen_settings() (+31 more)

### Community 35 - "read_patterns"
Cohesion: 0.40
Nodes (4): Path, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados. ``stamp``…, Lista de expressões de um arquivo de padrões, ignorando comentários., read_patterns()

### Community 37 - "WindowsCaptureBackend"
Cohesion: 0.21
Nodes (6): Monitor, Monitor que contém a janela em foco, se determinável., Um monitor físico: rótulo estável + geometria em pixels do desktop., Path, argv do gravador WASAPI (ver :mod:`app.capture.winrecord`). Não é ffmpeg: no…, WindowsCaptureBackend

### Community 38 - "get_backend"
Cohesion: 0.33
Nodes (8): Valores de ``tela.conf`` relevantes para a captura de um frame., ScreenConfig, get_backend(), Devolve o backend do SO atual (memorizado). ``force``…, main(), _measure_volume(), Path, Self-test de captura — rode isto ao trocar de sistema. python -m…

### Community 39 - "test_main.py"
Cohesion: 0.10
Nodes (12): identify_profiles(), _activity_groups(), filter_hallucinated_segments(), normalized_transcript_text(), private_context_terms(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas., Falas do áudio que estava sendo gravado perto do instante de um print., Separa por aplicativo e continuidade; mudanças de título não quebram a sessão. (+4 more)

### Community 45 - "process_pending"
Cohesion: 0.21
Nodes (12): audio_channel_count(), compact_processed_audio(), compact_saved_capture(), known_voice_profiles(), monitor_key(), process_pending(), process_specific(), Collapse a processed multichannel WAV to mono without risking the source. The… (+4 more)

### Community 46 - "resolve_media_source"
Cohesion: 0.18
Nodes (13): backfill_confirmed_voice_observations(), backfill_video_session_durations(), enroll_voice_identity(), list_video_sessions(), _normalized_average(), Resolve uma identidade portátil ou um caminho legado na raiz atual., resolve_media_source(), Recalcula um perfil dando um único voto a cada gravação. (+5 more)

### Community 47 - "join_video_session"
Cohesion: 0.22
Nodes (9): join_video_session(), preserve_video(), safe_screen_path(), safe_video_path(), screenshot(), video_file(), VideoJoinRequest, VideoProcessRequest (+1 more)

### Community 48 - "WasapiError"
Cohesion: 0.25
Nodes (4): GUID, Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, OSError

### Community 50 - "pipeline.py"
Cohesion: 0.23
Nodes (26): adaptive_web_research(), analyze_video_chapter(), audio_stream_count(), describe_long_video(), describe_screen(), describe_video(), extract_adaptive_keyframes(), format_video_time() (+18 more)

### Community 51 - "_scaled_size"
Cohesion: 0.50
Nodes (4): _parse_max_geometry(), Interpreta ``"1920x1080>"`` -> (1920, 1080, apenas_reduzir)., Dimensões finais respeitando ``MAX_GEOMETRY`` (mantém proporção)., _scaled_size()

### Community 52 - "_resolve"
Cohesion: 0.36
Nodes (3): Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), UnitResolutionTests

### Community 54 - "ObsWindowSpecTests"
Cohesion: 0.38
Nodes (4): ObsWindowSpecTests, O identificador de janela do OBS é ``título:classe:executável``. Um título com…, _encode_field(), Escapa um campo do identificador de janela do OBS. O identificador é…

### Community 56 - "runtime.py"
Cohesion: 0.50
Nodes (3): exclusive_lock(), Helpers de runtime que funcionam igual em Linux e Windows. Centraliza as poucas…, Trava exclusiva e não-bloqueante sobre ``path``. Retorna ``True`` se conseguiu…

## Knowledge Gaps
- **83 isolated node(s):** `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `grava-audio.sh script`, `name`, `private` (+78 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `post`, `ConfigTests`, `main.py`, `test_main.py`, `WindowsServiceManager`, `resolve_media_source`, `join_video_session`, `Path`, `_resolve`, `ObsWindowSpecTests`, `test_services.py`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `test_main.py`, `process_pending`, `resolve_media_source`, `pipeline.py`, `generate_visual_activities`, `ActionResult`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `AudioConfig` connect `test_services.py` to `post`, `main.py`, `CaptureBackend`, `WindowsCaptureBackend`, `get_backend`, `Path`, `_resolve`, `LinuxCaptureBackend`, `ObsWindowSpecTests`, `ActionResult`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 32 inferred relationships involving `ActionResult` (e.g. with `ContextUpdate` and `MarkerCreate`) actually correct?**
  _`ActionResult` has 32 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `ConfigTests` (e.g. with `ActionResult` and `SystemdServiceManager`) actually correct?**
  _`ConfigTests` has 2 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `VideoLoop` (e.g. with `ImageDiffTests` and `ObsWindowSpecTests`) actually correct?**
  _`VideoLoop` has 13 INFERRED edges - model-reasoned connections that need verification._
- **What connects `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `grava-audio.sh script` to the rest of the system?**
  _83 weakly-connected nodes found - possible documentation gaps or missing edges._