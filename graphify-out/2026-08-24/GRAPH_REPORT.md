# Graph Report - lume  (2026-08-24)

## Corpus Check
- 55 files · ~90,201 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1494 nodes · 3664 edges · 90 communities (79 shown, 11 thin omitted)
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
- get_backend
- obs.py
- record
- Handoff: Lume — app de memória de tela & áudio
- VideoLoop
- run
- Lume no Windows
- test_main.py
- test_services.py
- winscreen.py
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
- get
- ._start
- audio-bus.sh
- src-backup-2026-08-09/api.ts
- src-backup-2026-08-09/main.tsx
- post
- _call
- capture-loop
- main.py
- LinuxCaptureBackend
- winrecord.py
- grava-audio.sh
- install-lume.sh
- install-user.sh
- set_video_settings
- MarkerHotkey
- local_origin_only
- media_source_key
- selective_video_status
- recover_json_from_thinking
- WindowsHudCollector
- Hud
- ServiceManager
- src/main.tsx
- App
- videoTime
- connect
- WasapiCapture
- videoTime
- runtime_dir
- filter_hallucinated_segments
- App
- HudPanel
- HudStateTests
- evaluate
- wasapi.py
- HudPlacementTests
- hud.py
- sessionDuration
- LinuxHudCollector
- capture_frames
- .action
- services.py
- windows_startup.py
- UnitResolutionTests
- SpeechRegionTests
- Path
- HudEventContractTests
- .snapshot
- _Growth
- RegionGroupingTests
- RemapToSourceTests
- HudFrameRateTests
- merge_transcript_sources
- PrivacyTests
- format_elapsed
- _UnitDef

## God Nodes (most connected - your core abstractions)
1. `ActionResult` - 81 edges
2. `connect()` - 78 edges
3. `ConfigTests` - 76 edges
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

## Communities (90 total, 11 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.07
Nodes (9): captured_video_session(), Lê a identidade portátil deixada pelo gravador seletivo. Vídeos antigos só têm…, daily_narrative_target(), multimodal_context(), Agrupa telas e áudios sobrepostos em momentos únicos para as sínteses., ConfigTests, Path, skipUnless (+1 more)

### Community 1 - "src/api.ts"
Cohesion: 0.07
Nodes (27): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+19 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "get_backend"
Cohesion: 0.08
Nodes (27): CaptureBackend, ABC, Path, Interface comum de captura, independente de sistema operacional. Cada SO…, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco. Retorna ``None``…, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados. ``stamp``…, Prepara o roteamento de áudio (no-op onde não for necessário). (+19 more)

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
Cohesion: 0.08
Nodes (22): parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., foreground_details(), log(), looks_blank(), main(), Path, Gravação seletiva de jogos no Windows — porte de ``bin/game-video-loop``. Mesma… (+14 more)

### Community 9 - "run"
Cohesion: 0.18
Nodes (16): audio_file(), _audio_streams(), capture_speaker_sample(), import_video(), datetime, run(), safe_audio_path(), search() (+8 more)

### Community 10 - "Lume no Windows"
Cohesion: 0.07
Nodes (24): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+16 more)

### Community 11 - "test_main.py"
Cohesion: 0.08
Nodes (20): cancel_video_analysis(), Uma unit transitória coletada equivale a um job já parado., stop_target_is_already_gone(), _activity_groups(), apply_exact_game_durations(), private_context_terms(), Separa por aplicativo e continuidade; mudanças de título não quebram a sessão., Substitui estimativas da IA pelos intervalos medidos pelo contador da sidebar. (+12 more)

### Community 12 - "test_services.py"
Cohesion: 0.09
Nodes (19): HudEventAnimationTests, ObsWindowSpecTests, skipUnless, Testes das peças que tornam o app portável entre Linux e Windows. Rodam nos…, O identificador de janela do OBS é ``título:classe:executável``. Um título com…, Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., A curva da animação de confirmação, sem abrir janela nenhuma., O OBS leva segundos para informar o arquivo; a faixa espera por ele. (+11 more)

### Community 13 - "winscreen.py"
Cohesion: 0.08
Nodes (24): Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg. O laço de captura do Linux usa…, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar., Diferença percentual entre dois arquivos de imagem. (+16 more)

### Community 14 - "WindowsServiceManager"
Cohesion: 0.21
Nodes (3): Supervisor: mantém os processos de captura vivos e agenda o processamento. Vive…, Combine selective-video and user-idle pauses without racing them. Audio and…, WindowsServiceManager

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "ActionResult"
Cohesion: 0.20
Nodes (7): ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API., ResamplerTests, StereoAudioTests, SystemdFallbackTests

### Community 18 - "Monitor"
Cohesion: 0.15
Nodes (9): ImageDiffTests, Monitor, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Um monitor físico: rótulo estável + geometria em pixels do desktop., Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga. Dois formatos de saída…, Dispositivo dshow capaz de gravar a saída, se algum existir. Só diagnóstico: a… (+1 more)

### Community 19 - "pipeline.py"
Cohesion: 0.14
Nodes (48): _activity_image(), adaptive_web_research(), analyze_screen_sequence(), analyze_video_chapter(), audio_channel_count(), audio_stream_count(), compact_processed_audio(), compact_saved_capture() (+40 more)

### Community 20 - "Path"
Cohesion: 0.09
Nodes (34): delete_video(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), get_storage_settings(), migrate_legacy_cache_file(), probe_video_audio_tracks(), probe_video_duration() (+26 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.14
Nodes (22): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+14 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "hudsource.py"
Cohesion: 0.16
Nodes (10): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.…, read_shell_config(), get_collector(), HudCollector, ABC, Coleta do estado que a HUD mostra, com um coletor por sistema. Mesma divisão…, Fonte do instantâneo da HUD., Sobe threads de coleta (no-op quando não houver). (+2 more)

### Community 27 - "WasapiError"
Cohesion: 0.22
Nodes (4): GUID, Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, OSError

### Community 29 - "get"
Cohesion: 0.09
Nodes (31): row_dict(), _audio_channels(), backfill_confirmed_voice_observations(), capture_days(), capture_payload(), captures(), delete_unprocessed_files(), enroll_voice_identity() (+23 more)

### Community 30 - "._start"
Cohesion: 0.24
Nodes (5): _Process, Path, Popen, (Re)inicia o swayidle apontando os eventos para o flag de idle., Um processo filho supervisionado.

### Community 31 - "audio-bus.sh"
Cohesion: 0.34
Nodes (13): load_loopback(), make_null_sink(), selected_mic(), setup(), audio-bus.sh script, sink_exists(), source_exists(), status() (+5 more)

### Community 32 - "src-backup-2026-08-09/api.ts"
Cohesion: 0.07
Nodes (26): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+18 more)

### Community 33 - "src-backup-2026-08-09/main.tsx"
Cohesion: 0.10
Nodes (5): EditableVideoSpeaker, icons, labels, Panel, View

### Community 34 - "post"
Cohesion: 0.15
Nodes (24): _apply_storage_runtime(), cancel_pipeline(), capture_action(), enqueue_unprocessed(), generate_hourly_now(), generate_summary_now(), pipeline_run(), preserve_video() (+16 more)

### Community 35 - "_call"
Cohesion: 0.29
Nodes (14): _call(), _check(), default_endpoint_name(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints(), Invoca o método ``index`` da vtable de uma interface COM. (+6 more)

### Community 37 - "main.py"
Cohesion: 0.09
Nodes (42): atomic_write(), cancel_entire_queue(), cancel_queue_item(), cancel_screen_sequence(), cancel_video_audio_track_job(), cancel_video_audio_tracks(), cancel_video_session(), ContextUpdate (+34 more)

### Community 38 - "LinuxCaptureBackend"
Cohesion: 0.12
Nodes (9): LinuxAudioTrackTests, Gravação em faixas separadas (3 canais) no backend Linux., AudioConfig, argv do ``ffmpeg`` que grava mic + saída do sistema num único WAV. O comando…, Como gravar áudio: fontes e formato do WAV alvo do whisper., LinuxCaptureBackend, Path, argv do ffmpeg que grava mic + Discord + sistema num WAV de 3 canais. Mesmo… (+1 more)

### Community 39 - "winrecord.py"
Cohesion: 0.13
Nodes (14): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _install_stop_handlers(), _mix(), _multichannel(), array, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.… (+6 more)

### Community 45 - "set_video_settings"
Cohesion: 0.18
Nodes (14): _apply_video_runtime(), atomic_write_if_changed(), get_video_settings(), Write a config only when its contents changed., _report_runtime_failure(), _restart_screen_runtime(), set_video_settings(), update_screen_settings() (+6 more)

### Community 46 - "MarkerHotkey"
Cohesion: 0.16
Nodes (6): HudSettings, Preferências da HUD, lidas de ``video.conf``., log(), MarkerHotkey, Atalhos globais no Windows, registrados fora de qualquer janela. No Linux o…, Atalho global que chama ``on_press`` a cada acionamento.

### Community 47 - "local_origin_only"
Cohesion: 0.22
Nodes (9): bounded_video_range(), local_origin_only(), origin_allowed(), Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., remote_client_allowed(), video_file(), middleware, Request (+1 more)

### Community 48 - "media_source_key"
Cohesion: 0.14
Nodes (21): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., backfill_video_session_durations(), list_video_sessions(), list_videos(), _config_dir() (+13 more)

### Community 49 - "selective_video_status"
Cohesion: 0.22
Nodes (8): cancel_video_audio_track_jobs(), lifespan(), migrate_legacy_media_caches(), parse_shell_config(), Estado operacional do gravador, separado da mera configuração ativa., Move caches antigos do perfil para a raiz de armazenamento selecionada., selective_video_status(), FastAPI

### Community 50 - "recover_json_from_thinking"
Cohesion: 0.25
Nodes (5): ollama_chat(), parse_json_response(), publish_ai_live(), Recupera JSON que o parser do Ollama classificou todo como thinking., recover_json_from_thinking()

### Community 51 - "WindowsHudCollector"
Cohesion: 0.15
Nodes (6): log(), Medidores e engate lidos do OBS dedicado, estado lido do sinal de vídeo., Lê PCM cru do monitor de um bus e acumula o pico. Taxa baixa e um canal de…, WindowsHudCollector, Converte multiplicador linear (0..1) para dBFS, com piso em silêncio., to_db()

### Community 52 - "Hud"
Cohesion: 0.15
Nodes (11): _alert_sound(), Hud, log(), main(), _probe(), Aviso audível de falha, distinto do bipe de marcador. O marcador toca um par…, Laço da interface: coleta, avalia, desenha e avisa., Aplica queda suave às barras, para o medidor não piscar. (+3 more)

### Community 53 - "ServiceManager"
Cohesion: 0.10
Nodes (12): ABC, Executa ``start``/``stop``/``restart``/``try-restart``/``enable``/``disable``., Horário configurado do processamento noturno e se está ativo., Reprograma o processamento noturno., Dispara um job avulso sob um nome de unit, para poder cancelá-lo depois. É o…, Reinicia a própria interface (usado ao trocar o local dos dados)., Chamado quando a API sobe., Chamado quando a API desce. (+4 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.07
Nodes (12): CAPTION_LABELS, CAPTION_ORDER, CapturaTab, dayViews, EditableVideoSpeaker, gameCovers, icons, labels (+4 more)

### Community 55 - "App"
Cohesion: 0.25
Nodes (9): Capture, ScreenSequenceResult, Status, uploadVideo(), VideoSettings, App(), canonicalGameName(), groupCaptures() (+1 more)

### Community 56 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 57 - "connect"
Cohesion: 0.20
Nodes (20): connect(), initialize(), create_video_marker(), join_video_session(), discover(), game_activity_rows(), generate_hourly_summaries(), generate_summary() (+12 more)

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers. Média…, Um fluxo de captura: microfone padrão ou loopback da saída padrão. A saída de…, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio). Um fluxo…, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "runtime_dir"
Cohesion: 0.23
Nodes (10): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows. Centraliza as poucas…, Diretório para arquivos efêmeros (locks, estado volátil). Linux usa…, Arquivo que sinaliza "estou gravando vídeo agora". É como o laço de vídeo pede…, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``. Retorna ``True`` se conseguiu…, runtime_dir() (+2 more)

### Community 61 - "filter_hallucinated_segments"
Cohesion: 0.40
Nodes (3): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas.

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.17
Nodes (10): blend(), EventFrame, HudPanel, Mistura duas cores ``#rrggbb``. O Canvas do tkinter não tem canal alfa por…, Um quadro da animação de confirmação. ``reveal`` é o quanto o evento tomou o…, Um painel desenhado num monitor., Corta pela largura real do texto, não por contagem de caracteres. A HUD mistura…, Barra mínima. O evento entra por baixo empurrando o conteúdo normal. Não há… (+2 more)

### Community 64 - "HudStateTests"
Cohesion: 0.25
Nodes (3): HudStateTests, As regras que decidem se a captura está saudável. Rodam nos dois sistemas de…, Ficar calado é normal; confundir com falha destrói a confiança na HUD.

### Community 65 - "evaluate"
Cohesion: 0.38
Nodes (8): Alert, _disk_alerts(), evaluate(), HudStatus, _meter_alerts(), Estado da HUD de gravação: instantâneo portátil e regras de saúde. Este módulo…, Traduz um instantâneo em alertas e num veredito único. Função pura: mesma…, worst_level()

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

### Community 71 - "LinuxHudCollector"
Cohesion: 0.22
Nodes (8): _count_markers(), LinuxHudCollector, Path, Estado derivado do laço bash e medidores lidos dos buses do PipeWire. O…, Segmento sendo escrito agora pelo ``gpu-screen-recorder``., Janela em foco, com a mesma cadência do laço bash (2 s). O sidecar ``.window``…, Há quanto tempo o segmento em curso começou. Vem do nome do arquivo, não do…, _segment_elapsed()

### Community 72 - "capture_frames"
Cohesion: 0.23
Nodes (12): capture_change_test_frames(), capture_frames(), compare_screen_change_test(), get_screen_settings(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver. A mesma regra nos dois…, Captura um conjunto de frames com a configuração atual., screen_change_percent() (+4 more)

### Community 74 - ".action"
Cohesion: 0.23
Nodes (5): Arquivo de estado que o laço de vídeo cria enquanto controla as capturas. Mesma…, Anota que a captura deve (ou não) voltar na próxima abertura do Lume. No Linux…, Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., _unknown(), _video_pause_file()

### Community 75 - "services.py"
Cohesion: 0.22
Nodes (7): _JobObject, _pipeline(), _python(), Gerenciamento de serviços independente de sistema operacional. No Linux o…, Amarra os processos filhos ao ciclo de vida da API. É o que o systemd consegue…, Return seconds since the last real keyboard or mouse input on Windows., windows_idle_seconds()

### Community 76 - "windows_startup.py"
Cohesion: 0.60
Nodes (4): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows. Executado com ``pythonw.exe``…

### Community 77 - "UnitResolutionTests"
Cohesion: 0.36
Nodes (3): Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), UnitResolutionTests

### Community 78 - "SpeechRegionTests"
Cohesion: 0.36
Nodes (5): Trechos ``(início, fim)`` em segundos onde há som acima do limiar. Função pura…, speech_regions(), Detecção dos trechos com som, sobre amostras sintéticas., A folga não pode gerar tempo negativo nem passar do fim do áudio., SpeechRegionTests

### Community 79 - "Path"
Cohesion: 0.11
Nodes (9): LinuxIdlePauseTests, _pausable(), Path, Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)., O sinal de atividade tem um significado só, e ele é caro de errar. Enquanto o…, Dois marcadores seguidos têm o mesmo rótulo; só a sequência os separa., SupervisorTests, VideoActivityFlagTests (+1 more)

### Community 80 - "HudEventContractTests"
Cohesion: 0.31
Nodes (5): HudEventContractTests, O evento cruza dois processos por um arquivo; o formato é um contrato. O…, Um tipo sem estilo seria um evento invisível — falha silenciosa., _event_fields(), Extrai o acontecimento pontual publicado pelo laço de vídeo. A idade vem do…

### Community 81 - ".snapshot"
Cohesion: 0.20
Nodes (7): _demo_sequence(), Estados fabricados percorridos em laço, para ajustar a HUD sem jogo., _app_label(), _elapsed(), Lê o sinal JSON que o ``winvideo`` reescreve a cada volta do laço. Um arquivo…, Nome curto do app a partir de ``"<título> | <executável>"``., _read_video_flag()

### Community 82 - "_Growth"
Cohesion: 0.22
Nodes (4): _Growth, _MeterTracker, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo)., Contabilidade temporal de uma fonte de áudio. Guarda desde quando a fonte não…

### Community 83 - "RegionGroupingTests"
Cohesion: 0.31
Nodes (5): group_regions(), Agrupa trechos vizinhos em blocos que caibam numa janela do whisper. Dois…, Blocos que enchem uma janela do whisper sem esticar o eixo do tempo. O whisper…, É o teto que impede um erro de 1 s virar 20 s ao voltar ao original., RegionGroupingTests

### Community 84 - "RemapToSourceTests"
Cohesion: 0.33
Nodes (3): Voltar os tempos do bloco para o eixo do áudio original. É a parte que, errada,…, Fim antes do início quebraria a ordenação e a legenda., RemapToSourceTests

### Community 85 - "HudFrameRateTests"
Cohesion: 0.33
Nodes (3): HudFrameRateTests, Uma entrada de 0,26 s precisa de quadros suficientes para não escadear., As três cadências existem por causa do custo de redesenhar. Cada volta recria…

### Community 87 - "PrivacyTests"
Cohesion: 0.50
Nodes (3): PrivacyTests, matched_sensitive_pattern(), Primeiro padrão sensível (regex, case-insensitive) que casa com a janela. Mesma…

## Knowledge Gaps
- **104 isolated node(s):** `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` (+99 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **11 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `ConfigTests`, `run`, `test_main.py`, `test_services.py`, `WindowsServiceManager`, `Monitor`, `Path`, `get`, `._start`, `post`, `main.py`, `LinuxCaptureBackend`, `set_video_settings`, `ServiceManager`, `HudStateTests`, `HudPlacementTests`, `capture_frames`, `.action`, `services.py`, `UnitResolutionTests`, `SpeechRegionTests`, `Path`, `HudEventContractTests`, `RegionGroupingTests`, `RemapToSourceTests`, `HudFrameRateTests`, `PrivacyTests`, `_UnitDef`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `main.py`, `test_main.py`, `set_video_settings`, `local_origin_only`, `ActionResult`, `recover_json_from_thinking`, `merge_transcript_sources`, `audio_intelligence.py`, `connect`, `filter_hallucinated_segments`?**
  _High betweenness centrality (0.067) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `ActionResult` to `ConfigTests`, `test_main.py`, `test_services.py`, `Monitor`, `._start`, `post`, `LinuxCaptureBackend`, `set_video_settings`, `ServiceManager`, `runtime_dir`, `HudStateTests`, `HudPlacementTests`, `.action`, `services.py`, `UnitResolutionTests`, `SpeechRegionTests`, `Path`, `HudEventContractTests`, `RegionGroupingTests`, `RemapToSourceTests`, `HudFrameRateTests`, `PrivacyTests`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 48 inferred relationships involving `ActionResult` (e.g. with `ContextUpdate` and `MarkerCreate`) actually correct?**
  _`ActionResult` has 48 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `ActionResult`) actually correct?**
  _`ConfigTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `SystemdServiceManager` (e.g. with `ConfigTests` and `RegionGroupingTests`) actually correct?**
  _`SystemdServiceManager` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `HudSnapshot` (e.g. with `HudEventAnimationTests` and `HudEventContractTests`) actually correct?**
  _`HudSnapshot` has 30 INFERRED edges - model-reasoned connections that need verification._