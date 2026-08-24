# Graph Report - lume  (2026-08-23)

## Corpus Check
- 55 files · ~87,668 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1444 nodes · 3511 edges · 84 communities (76 shown, 8 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 290 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5f189fba`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ConfigTests
- src/api.ts
- package.json
- compilerOptions
- base.py
- obs.py
- record
- Handoff: Lume — app de memória de tela & áudio
- VideoLoop
- post
- Lume no Windows
- test_main.py
- thumbnail
- winscreen.py
- WindowsServiceManager
- game-video-loop
- ActionResult
- AGENTS.md
- WindowsCaptureBackend
- Path
- Path
- install-audio-intelligence
- audio_intelligence.py
- capture-frame
- read_shell_config
- add-video-marker
- WasapiError
- install-captura-dia.sh
- get
- HudSnapshot
- audio-bus.sh
- src-backup-2026-08-09/api.ts
- src-backup-2026-08-09/main.tsx
- connect
- _call
- capture-loop
- main.py
- LinuxCaptureBackend
- winrecord.py
- grava-audio.sh
- install-lume.sh
- install-user.sh
- ObsWindowSpecTests
- runtime_dir
- safe_video_path
- media_source_key
- LinuxHudCollector
- hudsource.py
- WindowsHudCollector
- Hud
- services.py
- src/main.tsx
- App
- videoTime
- pipeline.py
- WasapiCapture
- videoTime
- video_recording_flag
- filter_hallucinated_segments
- App
- HudPanel
- HudStateTests
- evaluate
- wasapi.py
- test_services.py
- hud.py
- matched_sensitive_pattern
- .tick
- _Growth
- HudCollector
- windows_startup.py
- UnitResolutionTests
- Meter
- Path
- HudEventContractTests
- .snapshot
- ._start
- get_backend
- HudFrameRateTests

## God Nodes (most connected - your core abstractions)
1. `connect()` - 78 edges
2. `ActionResult` - 77 edges
3. `ConfigTests` - 76 edges
4. `HudSnapshot` - 50 edges
5. `VideoLoop` - 49 edges
6. `SystemdServiceManager` - 47 edges
7. `Monitor` - 47 edges
8. `Meter` - 45 edges
9. `WindowsCaptureBackend` - 41 edges
10. `LinuxCaptureBackend` - 40 edges

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

## Communities (84 total, 8 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.04
Nodes (13): speaker_profiles(), captured_video_session(), Uma unit transitória coletada equivale a um job já parado., Lê a identidade portátil deixada pelo gravador seletivo. Vídeos antigos só têm…, stop_target_is_already_gone(), multimodal_context(), Agrupa telas e áudios sobrepostos em momentos únicos para as sínteses., Recupera JSON que o parser do Ollama classificou todo como thinking. (+5 more)

### Community 1 - "src/api.ts"
Cohesion: 0.07
Nodes (27): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+19 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "base.py"
Cohesion: 0.09
Nodes (17): CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional. Cada SO…, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco. Retorna ``None``…, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Prepara o roteamento de áudio (no-op onde não for necessário). (+9 more)

### Community 5 - "obs.py"
Cohesion: 0.07
Nodes (55): any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), ensure_scene(), find_installation(), _identify() (+47 more)

### Community 6 - "record"
Cohesion: 0.17
Nodes (10): ProcessLoopbackCapture, Loopback que inclui ou exclui a árvore de um processo do Windows., Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record() (+2 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.06
Nodes (28): parse_video_app_rule(), Lista de expressões de um arquivo de padrões, ignorando comentários., Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., read_patterns(), log(), MarkerHotkey, Atalhos globais no Windows, registrados fora de qualquer janela. No Linux o…, Atalho global que chama ``on_press`` a cada acionamento. (+20 more)

### Community 9 - "post"
Cohesion: 0.15
Nodes (14): capture_action(), create_video_marker(), create_video_session(), generate_hourly_now(), MarkerCreate, pipeline_run(), PipelineRequest, search() (+6 more)

### Community 10 - "Lume no Windows"
Cohesion: 0.07
Nodes (24): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+16 more)

### Community 11 - "test_main.py"
Cohesion: 0.08
Nodes (18): VideoSettings, _activity_groups(), apply_exact_game_durations(), daily_narrative_target(), game_activity_rows(), merge_source_transcripts(), monitor_key(), Sessões monitoradas recortadas ao dia local, inclusive ao cruzar meia-noite. (+10 more)

### Community 12 - "thumbnail"
Cohesion: 0.19
Nodes (9): Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg. O laço de captura do Linux usa…, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar., Diferença percentual entre dois arquivos de imagem. (+1 more)

### Community 13 - "winscreen.py"
Cohesion: 0.20
Nodes (8): _as_bool(), _as_float(), _as_int(), main(), Laço contínuo de captura de telas — porte de ``bin/capture-loop`` para Python.…, Instantâneo do ``tela.conf``, relido quando o arquivo muda no disco., ScreenLoop, _Settings

### Community 14 - "WindowsServiceManager"
Cohesion: 0.18
Nodes (4): Supervisor: mantém os processos de captura vivos e agenda o processamento. Vive…, Anota que a captura deve (ou não) voltar na próxima abertura do Lume. No Linux…, Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., WindowsServiceManager

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "ActionResult"
Cohesion: 0.13
Nodes (11): ActionResult, Arquivo de estado que o laço de vídeo cria enquanto controla as capturas. Mesma…, (Re)inicia o swayidle apontando os eventos para o flag de idle., Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, _unknown(), _video_pause_file(), PrivacyTests (+3 more)

### Community 18 - "WindowsCaptureBackend"
Cohesion: 0.21
Nodes (5): Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga. Dois formatos de saída…, Dispositivo dshow capaz de gravar a saída, se algum existir. Só diagnóstico: a…, argv do gravador WASAPI (ver :mod:`app.capture.winrecord`). Não é ffmpeg: no…, WindowsCaptureBackend

### Community 19 - "Path"
Cohesion: 0.17
Nodes (31): analyze_video_chapter(), audio_channel_count(), audio_stream_count(), compact_processed_audio(), compact_saved_capture(), describe_screen(), describe_video(), extract_adaptive_keyframes() (+23 more)

### Community 20 - "Path"
Cohesion: 0.09
Nodes (39): audio_file(), _audio_streams(), capture_speaker_sample(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), import_video(), migrate_legacy_cache_file() (+31 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.23
Nodes (21): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+13 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "read_shell_config"
Cohesion: 0.29
Nodes (6): Path, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados. ``stamp``…, Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.…, read_shell_config(), _parse_config(), Lê o ``tela.conf`` (formato ``CHAVE=valor`` do shell).

### Community 27 - "WasapiError"
Cohesion: 0.22
Nodes (4): GUID, Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, OSError

### Community 29 - "get"
Cohesion: 0.14
Nodes (18): backfill_confirmed_voice_observations(), capture_days(), enroll_voice_identity(), health(), list_ollama_models(), _network_values(), _normalized_average(), Estado operacional do gravador, separado da mera configuração ativa. (+10 more)

### Community 30 - "HudSnapshot"
Cohesion: 0.24
Nodes (6): O sinal de atividade tem um significado só, e ele é caro de errar. Enquanto o…, Dois marcadores seguidos têm o mesmo rótulo; só a sequência os separa., VideoActivityFlagTests, HudSnapshot, Há captura de vídeo em curso, gravando ou em buffer de clipes., Tudo que a HUD sabe num instante, já normalizado entre os sistemas.

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
Cohesion: 0.11
Nodes (36): connect(), row_dict(), _audio_channels(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_screen_sequence(), cancel_video_analysis() (+28 more)

### Community 35 - "_call"
Cohesion: 0.29
Nodes (14): _call(), _check(), default_endpoint_name(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints(), Invoca o método ``index`` da vtable de uma interface COM. (+6 more)

### Community 37 - "main.py"
Cohesion: 0.07
Nodes (61): _apply_storage_runtime(), _apply_video_runtime(), atomic_write(), atomic_write_if_changed(), cancel_video_audio_track_jobs(), capture_change_test_frames(), capture_frames(), compare_screen_change_test() (+53 more)

### Community 38 - "LinuxCaptureBackend"
Cohesion: 0.15
Nodes (9): LinuxAudioTrackTests, skipUnless, Gravação em faixas separadas (3 canais) no backend Linux., VideoHotkeyTests, VideoMarkerTransitionTests, AudioConfig, Como gravar áudio: fontes e formato do WAV alvo do whisper., LinuxCaptureBackend (+1 more)

### Community 39 - "winrecord.py"
Cohesion: 0.13
Nodes (14): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _install_stop_handlers(), _mix(), _multichannel(), array, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.… (+6 more)

### Community 45 - "ObsWindowSpecTests"
Cohesion: 0.38
Nodes (4): ObsWindowSpecTests, O identificador de janela do OBS é ``título:classe:executável``. Um título com…, _encode_field(), Escapa um campo do identificador de janela do OBS. O identificador é…

### Community 46 - "runtime_dir"
Cohesion: 0.19
Nodes (10): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows. Centraliza as poucas…, Diretório para arquivos efêmeros (locks, estado volátil). Linux usa…, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``. Retorna ``True`` se conseguiu…, runtime_dir(), video_activity_flag() (+2 more)

### Community 47 - "safe_video_path"
Cohesion: 0.10
Nodes (20): bounded_video_range(), cancel_video_audio_track_job(), cancel_video_audio_tracks(), local_origin_only(), origin_allowed(), preserve_video(), process_video(), Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro. (+12 more)

### Community 48 - "media_source_key"
Cohesion: 0.12
Nodes (24): initialize(), _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., backfill_video_session_durations(), join_video_session(), list_video_sessions() (+16 more)

### Community 49 - "LinuxHudCollector"
Cohesion: 0.20
Nodes (4): LinuxHudCollector, Estado derivado do laço bash e medidores lidos dos buses do PipeWire. O…, Segmento sendo escrito agora pelo ``gpu-screen-recorder``., Janela em foco, com a mesma cadência do laço bash (2 s). O sidecar ``.window``…

### Community 50 - "hudsource.py"
Cohesion: 0.33
Nodes (6): _count_markers(), _elapsed(), Path, Coleta do estado que a HUD mostra, com um coletor por sistema. Mesma divisão…, Há quanto tempo o segmento em curso começou. Vem do nome do arquivo, não do…, _segment_elapsed()

### Community 51 - "WindowsHudCollector"
Cohesion: 0.17
Nodes (6): log(), Medidores e engate lidos do OBS dedicado, estado lido do sinal de vídeo., Lê PCM cru do monitor de um bus e acumula o pico. Taxa baixa e um canal de…, WindowsHudCollector, Converte multiplicador linear (0..1) para dBFS, com piso em silêncio., to_db()

### Community 52 - "Hud"
Cohesion: 0.12
Nodes (13): _alert_sound(), Hud, HudSettings, log(), main(), _probe(), Aviso audível de falha, distinto do bipe de marcador. O marcador toca um par…, Laço da interface: coleta, avalia, desenha e avisa. (+5 more)

### Community 53 - "services.py"
Cohesion: 0.09
Nodes (15): _pipeline(), ABC, _python(), Gerenciamento de serviços independente de sistema operacional. No Linux o…, Executa ``start``/``stop``/``restart``/``try-restart``/``enable``/``disable``., Horário configurado do processamento noturno e se está ativo., Reprograma o processamento noturno., Dispara um job avulso sob um nome de unit, para poder cancelá-lo depois. É o… (+7 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.07
Nodes (13): CapturaTab, dayViews, EditableVideoSpeaker, gameCovers, icons, labels, lensLabels, Panel (+5 more)

### Community 55 - "App"
Cohesion: 0.25
Nodes (9): Capture, ScreenSequenceResult, Status, uploadVideo(), VideoSettings, App(), canonicalGameName(), groupCaptures() (+1 more)

### Community 56 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 57 - "pipeline.py"
Cohesion: 0.16
Nodes (27): _activity_image(), adaptive_web_research(), analyze_screen_sequence(), describe_long_video(), discover(), generate_hourly_summaries(), generate_summary(), generate_visual_activities() (+19 more)

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers. Média…, Um fluxo de captura: microfone padrão ou loopback da saída padrão. A saída de…, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio). Um fluxo…, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "video_recording_flag"
Cohesion: 0.20
Nodes (7): Arquivo que sinaliza "estou gravando vídeo agora". É como o laço de vídeo pede…, video_recording_flag(), _JobObject, Amarra os processos filhos ao ciclo de vida da API. É o que o systemd consegue…, Return seconds since the last real keyboard or mouse input on Windows., Combine selective-video and user-idle pauses without racing them. Audio and…, windows_idle_seconds()

### Community 61 - "filter_hallucinated_segments"
Cohesion: 0.40
Nodes (3): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas.

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.15
Nodes (11): blend(), EventFrame, HudPanel, Mistura duas cores ``#rrggbb``. O Canvas do tkinter não tem canal alfa por…, Um quadro da animação de confirmação. ``reveal`` é o quanto o evento tomou o…, Um painel desenhado num monitor., Corta pela largura real do texto, não por contagem de caracteres. A HUD mistura…, Barra mínima. O evento entra por baixo empurrando o conteúdo normal. Não há… (+3 more)

### Community 64 - "HudStateTests"
Cohesion: 0.25
Nodes (3): HudStateTests, As regras que decidem se a captura está saudável. Rodam nos dois sistemas de…, Ficar calado é normal; confundir com falha destrói a confiança na HUD.

### Community 65 - "evaluate"
Cohesion: 0.26
Nodes (9): Alert, _disk_alerts(), evaluate(), format_elapsed(), _meter_alerts(), Estado da HUD de gravação: instantâneo portátil e regras de saúde. Este módulo…, Traduz um instantâneo em alertas e num veredito único. Função pura: mesma…, ``h:mm:ss`` acima de uma hora, ``m:ss`` abaixo — como um cronômetro. (+1 more)

### Community 67 - "wasapi.py"
Cohesion: 0.15
Nodes (12): _ActivationHandler, _AudioClientActivationParams, _Blob, _LazyOle32, PROPERTYKEY, PROPVARIANT, _PropVariantBlob, Captura de áudio WASAPI em ``ctypes`` puro (Windows). Existe porque o ffmpeg no… (+4 more)

### Community 68 - "test_services.py"
Cohesion: 0.15
Nodes (11): HudPlacementTests, ImageDiffTests, Testes das peças que tornam o app portável entre Linux e Windows. Rodam nos…, Onde a HUD desenha, dado o arranjo de monitores., Com um monitor só, "no outro monitor" tem que recair sobre este., ResamplerTests, Monitor, Um monitor físico: rótulo estável + geometria em pixels do desktop. (+3 more)

### Community 69 - "hud.py"
Cohesion: 0.11
Nodes (17): O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., _assert_topmost(), _declare_dpi_aware(), ease_in_cubic(), ease_out_back(), ease_out_cubic(), event_animation() (+9 more)

### Community 70 - "matched_sensitive_pattern"
Cohesion: 0.33
Nodes (3): matched_sensitive_pattern(), Primeiro padrão sensível (regex, case-insensitive) que casa com a janela. Mesma…, Motivo para não capturar agora, ou ``None`` se pode capturar.

### Community 72 - ".tick"
Cohesion: 0.47
Nodes (4): _monitor_key(), Path, Identidade do monitor a partir do nome do arquivo (``..._mon1_DP-1.png``). A…, _thumbnail()

### Community 74 - "_Growth"
Cohesion: 0.22
Nodes (4): _Growth, _MeterTracker, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo)., Contabilidade temporal de uma fonte de áudio. Guarda desde quando a fonte não…

### Community 75 - "HudCollector"
Cohesion: 0.20
Nodes (7): get_collector(), HudCollector, ABC, Fonte do instantâneo da HUD., Sobe threads de coleta (no-op quando não houver)., Estado atual, já normalizado., Coletor do SO atual, na mesma convenção de :func:`app.capture.get_backend`.

### Community 76 - "windows_startup.py"
Cohesion: 0.60
Nodes (4): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows. Executado com ``pythonw.exe``…

### Community 77 - "UnitResolutionTests"
Cohesion: 0.36
Nodes (3): Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), UnitResolutionTests

### Community 78 - "Meter"
Cohesion: 0.14
Nodes (8): HudEventAnimationTests, Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., A curva da animação de confirmação, sem abrir janela nenhuma., O OBS leva segundos para informar o arquivo; a faixa espera por ele., ScreenConfigTests, VideoReplayClipTests, Meter, Uma fonte de áudio vista pela HUD. ``present`` e ``peak_db`` respondem…

### Community 79 - "Path"
Cohesion: 0.14
Nodes (6): LinuxIdlePauseTests, _pausable(), Path, Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)., SupervisorTests, VideoSettingsTests

### Community 80 - "HudEventContractTests"
Cohesion: 0.31
Nodes (5): HudEventContractTests, O evento cruza dois processos por um arquivo; o formato é um contrato. O…, Um tipo sem estilo seria um evento invisível — falha silenciosa., _event_fields(), Extrai o acontecimento pontual publicado pelo laço de vídeo. A idade vem do…

### Community 82 - ".snapshot"
Cohesion: 0.31
Nodes (4): _demo_sequence(), Estados fabricados percorridos em laço, para ajustar a HUD sem jogo., _app_label(), Nome curto do app a partir de ``"<título> | <executável>"``.

### Community 83 - "._start"
Cohesion: 0.24
Nodes (6): _Process, Path, Popen, Uma unit supervisionada. ``simple`` roda enquanto o serviço estiver ligado (e…, Um processo filho supervisionado., _UnitDef

### Community 84 - "get_backend"
Cohesion: 0.23
Nodes (10): Valores de ``tela.conf`` relevantes para a captura de um frame., ScreenConfig, get_backend(), Seleção automática do backend de captura conforme o sistema operacional. Uso:…, Devolve o backend do SO atual (memorizado). ``force``…, Path, main(), _measure_volume() (+2 more)

### Community 85 - "HudFrameRateTests"
Cohesion: 0.33
Nodes (3): HudFrameRateTests, Uma entrada de 0,26 s precisa de quadros suficientes para não escadear., As três cadências existem por causa do custo de redesenhar. Cada volta recria…

## Knowledge Gaps
- **102 isolated node(s):** `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` (+97 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `ConfigTests`, `post`, `test_main.py`, `WindowsServiceManager`, `Path`, `get`, `HudSnapshot`, `connect`, `main.py`, `LinuxCaptureBackend`, `ObsWindowSpecTests`, `safe_video_path`, `services.py`, `HudStateTests`, `test_services.py`, `UnitResolutionTests`, `Meter`, `Path`, `HudEventContractTests`, `._start`, `HudFrameRateTests`?**
  _High betweenness centrality (0.094) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `test_main.py`, `safe_video_path`, `ActionResult`, `filter_hallucinated_segments`, `Path`, `pipeline.py`, `get`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `ActionResult` to `ConfigTests`, `HudStateTests`, `test_services.py`, `main.py`, `LinuxCaptureBackend`, `test_main.py`, `ObsWindowSpecTests`, `runtime_dir`, `Meter`, `HudEventContractTests`, `Path`, `UnitResolutionTests`, `services.py`, `HudFrameRateTests`, `HudSnapshot`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Are the 44 inferred relationships involving `ActionResult` (e.g. with `ContextUpdate` and `MarkerCreate`) actually correct?**
  _`ActionResult` has 44 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `ActionResult`) actually correct?**
  _`ConfigTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `HudSnapshot` (e.g. with `HudEventAnimationTests` and `HudEventContractTests`) actually correct?**
  _`HudSnapshot` has 30 INFERRED edges - model-reasoned connections that need verification._
- **Are the 22 inferred relationships involving `VideoLoop` (e.g. with `HudEventAnimationTests` and `HudEventContractTests`) actually correct?**
  _`VideoLoop` has 22 INFERRED edges - model-reasoned connections that need verification._