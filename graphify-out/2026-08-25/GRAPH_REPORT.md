# Graph Report - lume  (2026-08-25)

## Corpus Check
- 56 files · ~91,588 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1510 nodes · 3723 edges · 77 communities (68 shown, 9 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 303 edges (avg confidence: 0.52)
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
- base.py
- obs.py
- record
- Handoff: Lume — app de memória de tela & áudio
- VideoLoop
- connect
- Lume no Windows
- track_is_silent
- ObsWindowSpecTests
- winvideo.py
- WindowsServiceManager
- game-video-loop
- ActionResult
- AGENTS.md
- Monitor
- pipeline.py
- Path
- install-audio-intelligence
- audio_intelligence.py
- capture-frame
- hudsource.py
- add-video-marker
- WasapiError
- install-captura-dia.sh
- post
- test_main.py
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
- MarkerHotkey
- safe_video_path
- main_paths.py
- multimodal_context
- lifespan
- WindowsHudCollector
- Hud
- ServiceManager
- src/main.tsx
- App
- videoTime
- capture_frames
- WasapiCapture
- videoTime
- Path
- App
- HudPanel
- HudStateTests
- HudSnapshot
- wasapi.py
- HudPlacementTests
- hud.py
- sessionDuration
- windows_startup.py
- UnitResolutionTests
- VideoSettings
- Path
- HudEventContractTests
- HudFrameRateTests

## God Nodes (most connected - your core abstractions)
1. `connect()` - 82 edges
2. `ActionResult` - 82 edges
3. `ConfigTests` - 79 edges
4. `SystemdServiceManager` - 51 edges
5. `HudSnapshot` - 50 edges
6. `VideoLoop` - 49 edges
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

## Communities (77 total, 9 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.06
Nodes (11): captured_video_session(), Lê a identidade portátil deixada pelo gravador seletivo. Vídeos antigos só têm…, daily_narrative_target(), Valida referências da IA e protege os arquivos escolhidos., Recupera JSON que o parser do Ollama classificou todo como thinking., recover_json_from_thinking(), validate_relevant_media(), ConfigTests (+3 more)

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
Cohesion: 0.07
Nodes (28): PrivacyTests, CaptureBackend, matched_sensitive_pattern(), ABC, Path, Interface comum de captura, independente de sistema operacional. Cada SO…, Primeiro padrão sensível (regex, case-insensitive) que casa com a janela. Mesma…, Contrato que Linux e Windows implementam. (+20 more)

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
Cohesion: 0.09
Nodes (19): foreground_details(), log(), looks_blank(), main(), Path, Regras sem prefixo procuram somente no executável. Assim uma pasta chamada como…, Título, classe e executável da janela em foco — o que o OBS precisa para…, Amostra um quadro e diz se o vídeo saiu chapado (preto/estático). É a rede de… (+11 more)

### Community 9 - "connect"
Cohesion: 0.12
Nodes (33): connect(), backfill_video_session_durations(), cancel_entire_queue(), cancel_queue_item(), cancel_screen_sequence(), delete_capture(), delete_capture_file(), delete_file() (+25 more)

### Community 10 - "Lume no Windows"
Cohesion: 0.07
Nodes (24): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+16 more)

### Community 11 - "track_is_silent"
Cohesion: 0.24
Nodes (8): Pico de um WAV PCM 16 bits, em dBFS. ``-inf`` vira o piso -99., A faixa está muda o bastante para transcrevê-la ser desperdício? Numa sessão…, track_is_silent(), track_peak_dbfs(), Faixas mudas não valem uma transcrição. Numa sessão sem Discord a faixa dele é…, -40 dBFS é fala baixa de verdade; pular isso perderia conversa., Na dúvida, transcreve: perder fala é pior que gastar tempo., SilentTrackTests

### Community 12 - "ObsWindowSpecTests"
Cohesion: 0.24
Nodes (6): ObsWindowSpecTests, O identificador de janela do OBS é ``título:classe:executável``. Um título com…, parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., _encode_field(), Escapa um campo do identificador de janela do OBS. O identificador é…

### Community 13 - "winvideo.py"
Cohesion: 0.06
Nodes (41): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows. Centraliza as poucas…, Diretório para arquivos efêmeros (locks, estado volátil). Linux usa…, Arquivo que sinaliza "estou gravando vídeo agora". É como o laço de vídeo pede…, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``. Retorna ``True`` se conseguiu…, runtime_dir() (+33 more)

### Community 14 - "WindowsServiceManager"
Cohesion: 0.09
Nodes (15): _JobObject, _Process, Path, Popen, Uma unit supervisionada. ``simple`` roda enquanto o serviço estiver ligado (e…, Amarra os processos filhos ao ciclo de vida da API. É o que o systemd consegue…, Return seconds since the last real keyboard or mouse input on Windows., Um processo filho supervisionado. (+7 more)

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "ActionResult"
Cohesion: 0.12
Nodes (12): ActionResult, _pipeline(), _python(), Gerenciamento de serviços independente de sistema operacional. No Linux o…, Arquivo de estado que o laço de vídeo cria enquanto controla as capturas. Mesma…, (Re)inicia o swayidle apontando os eventos para o flag de idle., Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager (+4 more)

### Community 18 - "Monitor"
Cohesion: 0.13
Nodes (10): ImageDiffTests, Monitor, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Um monitor físico: rótulo estável + geometria em pixels do desktop., Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga. Dois formatos de saída…, Dispositivo dshow capaz de gravar a saída, se algum existir. Só diagnóstico: a… (+2 more)

### Community 19 - "pipeline.py"
Cohesion: 0.14
Nodes (45): initialize(), adaptive_web_research(), analyze_screen_sequence(), analyze_video_chapter(), describe_long_video(), describe_screen(), describe_video(), discover() (+37 more)

### Community 20 - "Path"
Cohesion: 0.10
Nodes (30): _delete_media_sidecars(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), migrate_legacy_cache_file(), probe_video_audio_tracks(), probe_video_duration(), Path (+22 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.14
Nodes (22): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+14 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "hudsource.py"
Cohesion: 0.10
Nodes (20): _app_label(), _count_markers(), _elapsed(), get_collector(), HudCollector, LinuxHudCollector, ABC, Path (+12 more)

### Community 27 - "WasapiError"
Cohesion: 0.22
Nodes (4): GUID, Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, OSError

### Community 29 - "post"
Cohesion: 0.12
Nodes (26): _apply_storage_runtime(), _apply_video_runtime(), atomic_write_if_changed(), cancel_pipeline(), cancel_video_analysis(), cancel_video_session(), capture_action(), generate_hourly_now() (+18 more)

### Community 30 - "test_main.py"
Cohesion: 0.10
Nodes (14): Uma unit transitória coletada equivale a um job já parado., stop_target_is_already_gone(), _activity_groups(), apply_exact_game_durations(), game_activity_rows(), merge_source_transcripts(), merge_transcript_sources(), monitor_key() (+6 more)

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
Nodes (33): row_dict(), _audio_channels(), backfill_confirmed_voice_observations(), capture_days(), capture_payload(), captures(), enroll_voice_identity(), get_cleanup_settings() (+25 more)

### Community 35 - "_call"
Cohesion: 0.29
Nodes (14): _call(), _check(), default_endpoint_name(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints(), Invoca o método ``index`` da vtable de uma interface COM. (+6 more)

### Community 37 - "main.py"
Cohesion: 0.10
Nodes (40): atomic_write(), CleanupSettings, compare_screen_change_test(), ContextUpdate, create_video_marker(), create_video_session(), get_schedule(), get_sensitive_windows() (+32 more)

### Community 38 - "test_services.py"
Cohesion: 0.08
Nodes (22): HudEventAnimationTests, LinuxAudioTrackTests, skipUnless, Testes das peças que tornam o app portável entre Linux e Windows. Rodam nos…, Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., Gravação em faixas separadas (3 canais) no backend Linux., A curva da animação de confirmação, sem abrir janela nenhuma., O OBS leva segundos para informar o arquivo; a faixa espera por ele. (+14 more)

### Community 39 - "run"
Cohesion: 0.16
Nodes (19): audio_file(), _audio_streams(), capture_speaker_sample(), import_video(), process_file(), ProcessFileRequest, datetime, run() (+11 more)

### Community 45 - "winrecord.py"
Cohesion: 0.15
Nodes (12): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _mix(), _multichannel(), array, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.…, Soma as fontes com saturação e converte para PCM s16le. (+4 more)

### Community 46 - "MarkerHotkey"
Cohesion: 0.24
Nodes (4): log(), MarkerHotkey, Atalhos globais no Windows, registrados fora de qualquer janela. No Linux o…, Atalho global que chama ``on_press`` a cada acionamento.

### Community 47 - "safe_video_path"
Cohesion: 0.16
Nodes (13): bounded_video_range(), local_origin_only(), origin_allowed(), preserve_video(), process_video(), Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., remote_client_allowed(), safe_video_path() (+5 more)

### Community 48 - "main_paths.py"
Cohesion: 0.14
Nodes (12): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., _config_dir(), configured_storage_root(), Onde ficam ``tela.conf`` e a lista de janelas sensíveis. No Linux, o lugar de…, mark_capture_cleanup_ready() (+4 more)

### Community 50 - "lifespan"
Cohesion: 0.25
Nodes (7): cancel_video_audio_track_job(), cancel_video_audio_track_jobs(), cancel_video_audio_tracks(), lifespan(), migrate_legacy_media_caches(), Move caches antigos do perfil para a raiz de armazenamento selecionada., FastAPI

### Community 51 - "WindowsHudCollector"
Cohesion: 0.08
Nodes (12): _demo_sequence(), Estados fabricados percorridos em laço, para ajustar a HUD sem jogo., _Growth, log(), _MeterTracker, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo)., Medidores e engate lidos do OBS dedicado, estado lido do sinal de vídeo., Lê PCM cru do monitor de um bus e acumula o pico. Taxa baixa e um canal de… (+4 more)

### Community 52 - "Hud"
Cohesion: 0.13
Nodes (12): _alert_sound(), Hud, HudSettings, log(), main(), _probe(), Aviso audível de falha, distinto do bipe de marcador. O marcador toca um par…, Laço da interface: coleta, avalia, desenha e avisa. (+4 more)

### Community 53 - "ServiceManager"
Cohesion: 0.10
Nodes (12): ABC, Executa ``start``/``stop``/``restart``/``try-restart``/``enable``/``disable``., Horário configurado do processamento noturno e se está ativo., Reprograma o processamento noturno., Dispara um job avulso sob um nome de unit, para poder cancelá-lo depois. É o…, Reinicia a própria interface (usado ao trocar o local dos dados)., Chamado quando a API sobe., Chamado quando a API desce. (+4 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.07
Nodes (12): CAPTION_LABELS, CAPTION_ORDER, CapturaTab, dayViews, EditableVideoSpeaker, gameCovers, icons, labels (+4 more)

### Community 55 - "App"
Cohesion: 0.22
Nodes (10): Capture, CleanupSettings, ScreenSequenceResult, Status, uploadVideo(), VideoSettings, App(), canonicalGameName() (+2 more)

### Community 56 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 57 - "capture_frames"
Cohesion: 0.36
Nodes (8): capture_change_test_frames(), capture_frames(), get_screen_settings(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver. A mesma regra nos dois…, Captura um conjunto de frames com a configuração atual., ScreenSettings, test_screen()

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers. Média…, Um fluxo de captura: microfone padrão ou loopback da saída padrão. A saída de…, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio). Um fluxo…, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 61 - "Path"
Cohesion: 0.13
Nodes (24): _activity_image(), audio_channel_count(), audio_stream_count(), compact_processed_audio(), compact_saved_capture(), filter_hallucinated_segments(), normalized_transcript_text(), Path (+16 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.15
Nodes (13): blend(), EventFrame, HudPanel, Mistura duas cores ``#rrggbb``. O Canvas do tkinter não tem canal alfa por…, Um quadro da animação de confirmação. ``reveal`` é o quanto o evento tomou o…, Um painel desenhado num monitor., Corta pela largura real do texto, não por contagem de caracteres. A HUD mistura…, Barra mínima. O evento entra por baixo empurrando o conteúdo normal. Não há… (+5 more)

### Community 64 - "HudStateTests"
Cohesion: 0.25
Nodes (3): HudStateTests, As regras que decidem se a captura está saudável. Rodam nos dois sistemas de…, Ficar calado é normal; confundir com falha destrói a confiança na HUD.

### Community 65 - "HudSnapshot"
Cohesion: 0.18
Nodes (12): O que caracteriza uma *mudança de estado* digna de expandir a HUD. De propósito…, Estado atual, já normalizado., Alert, _disk_alerts(), evaluate(), HudSnapshot, _meter_alerts(), Estado da HUD de gravação: instantâneo portátil e regras de saúde. Este módulo… (+4 more)

### Community 67 - "wasapi.py"
Cohesion: 0.15
Nodes (12): _ActivationHandler, _AudioClientActivationParams, _Blob, _LazyOle32, PROPERTYKEY, PROPVARIANT, _PropVariantBlob, Captura de áudio WASAPI em ``ctypes`` puro (Windows). Existe porque o ffmpeg no… (+4 more)

### Community 68 - "HudPlacementTests"
Cohesion: 0.23
Nodes (6): HudPlacementTests, Onde a HUD desenha, dado o arranjo de monitores., Com um monitor só, "no outro monitor" tem que recair sobre este., choose_monitors(), corner_position(), Monitores que devem receber um painel. Função pura para poder ser testada sem…

### Community 69 - "hud.py"
Cohesion: 0.10
Nodes (17): O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., _assert_topmost(), _declare_dpi_aware(), ease_in_cubic(), ease_out_back(), ease_out_cubic(), event_animation() (+9 more)

### Community 70 - "sessionDuration"
Cohesion: 0.67
Nodes (3): SessionCard(), sessionDuration(), SessionViewer()

### Community 76 - "windows_startup.py"
Cohesion: 0.60
Nodes (4): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows. Executado com ``pythonw.exe``…

### Community 77 - "UnitResolutionTests"
Cohesion: 0.36
Nodes (3): Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), UnitResolutionTests

### Community 78 - "VideoSettings"
Cohesion: 0.09
Nodes (17): VideoSettings, group_regions(), Trechos ``(início, fim)`` em segundos onde há som acima do limiar. Função pura…, Agrupa trechos vizinhos em blocos que caibam numa janela do whisper. Dois…, speech_regions(), Detecção dos trechos com som, sobre amostras sintéticas., A folga não pode gerar tempo negativo nem passar do fim do áudio., Blocos que enchem uma janela do whisper sem esticar o eixo do tempo. O whisper… (+9 more)

### Community 79 - "Path"
Cohesion: 0.11
Nodes (9): LinuxIdlePauseTests, _pausable(), Path, Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)., O sinal de atividade tem um significado só, e ele é caro de errar. Enquanto o…, Dois marcadores seguidos têm o mesmo rótulo; só a sequência os separa., SupervisorTests, VideoActivityFlagTests (+1 more)

### Community 80 - "HudEventContractTests"
Cohesion: 0.31
Nodes (5): HudEventContractTests, O evento cruza dois processos por um arquivo; o formato é um contrato. O…, Um tipo sem estilo seria um evento invisível — falha silenciosa., _event_fields(), Extrai o acontecimento pontual publicado pelo laço de vídeo. A idade vem do…

### Community 85 - "HudFrameRateTests"
Cohesion: 0.33
Nodes (3): HudFrameRateTests, Uma entrada de 0,26 s precisa de quadros suficientes para não escadear., As três cadências existem por causa do custo de redesenhar. Cada volta recria…

## Knowledge Gaps
- **104 isolated node(s):** `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` (+99 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **9 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `ConfigTests`, `base.py`, `track_is_silent`, `ObsWindowSpecTests`, `WindowsServiceManager`, `Monitor`, `Path`, `post`, `test_main.py`, `get`, `main.py`, `test_services.py`, `run`, `safe_video_path`, `ServiceManager`, `capture_frames`, `HudStateTests`, `HudPlacementTests`, `UnitResolutionTests`, `VideoSettings`, `Path`, `HudEventContractTests`, `HudFrameRateTests`?**
  _High betweenness centrality (0.105) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `VideoSettings`, `safe_video_path`, `ActionResult`, `multimodal_context`, `audio_intelligence.py`, `Path`, `test_main.py`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `ActionResult` to `ConfigTests`, `HudStateTests`, `HudPlacementTests`, `base.py`, `test_services.py`, `track_is_silent`, `ObsWindowSpecTests`, `winvideo.py`, `VideoSettings`, `Path`, `HudEventContractTests`, `UnitResolutionTests`, `Monitor`, `ServiceManager`, `HudFrameRateTests`, `post`, `test_main.py`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `ActionResult` (e.g. with `CleanupSettings` and `ContextUpdate`) actually correct?**
  _`ActionResult` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `ActionResult`) actually correct?**
  _`ConfigTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `SystemdServiceManager` (e.g. with `ConfigTests` and `RegionGroupingTests`) actually correct?**
  _`SystemdServiceManager` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `HudSnapshot` (e.g. with `HudEventAnimationTests` and `HudEventContractTests`) actually correct?**
  _`HudSnapshot` has 30 INFERRED edges - model-reasoned connections that need verification._