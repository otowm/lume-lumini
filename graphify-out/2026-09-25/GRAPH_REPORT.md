# Graph Report - lume  (2026-09-25)

## Corpus Check
- 68 files · ~132,639 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2081 nodes · 5048 edges · 129 communities (98 shown, 31 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 522 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e8a602ea`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- ConfigTests
- src/api.ts
- package.json
- compilerOptions
- LinuxCaptureBackend
- obs.py
- record
- Handoff: Lume — app de memória de tela & áudio
- VideoLoop
- VideoSettings
- Lume no Windows
- SilentTrackTests
- test_services.py
- ActionResult
- WindowsServiceManager
- game-video-loop
- runtime_dir
- AGENTS.md
- RemapToSourceTests
- get
- main.py
- install-audio-intelligence
- audio_intelligence.py
- capture-frame
- hud.py
- add-video-marker
- WasapiError
- install-captura-dia.sh
- Path
- editing.py
- audio-bus.sh
- src-backup-2026-08-09/api.ts
- src-backup-2026-08-09/main.tsx
- pipeline.py
- _call
- capture-loop
- _JobObject
- run
- connect
- grava-audio.sh
- install-lume.sh
- install-user.sh
- prompts.py
- winrecord.py
- SpeechRegionTests
- .snapshot
- get_manager
- CallMetricsTests
- resolve_media_source
- RegionGroupingTests
- Path
- ServiceManager
- src/main.tsx
- App
- videoTime
- _video_pause_file
- WasapiCapture
- videoTime
- trim_video
- ollama_json
- App
- HudPanel
- HudStateTests
- local_origin_only
- VideoWindowTest
- HudPlacementTests
- PromptSettingsTests
- WindowsHudCollector
- patch
- capture_frames
- EditingFolderTests
- hudsource.py
- _Growth
- pad_to_segmentation_window
- multimodal_context
- Path
- LinuxAppRuleMatchTests
- winscreen.py
- context_overflow
- ._start
- test_main.py
- _video_pause_file
- .snapshot
- filter_hallucinated_segments
- hudsource.py
- media_source_key
- capture_frames
- WasapiError
- context_overflow
- _LazyOle32
- HoldDetectorTests
- toggle-video-hud
- lume-audio-diag
- _Growth
- services.py
- .active
- pipeline_queue
- LinuxAudioTapTests
- _activity_groups
- foreground_details
- .feed
- read_shell_config
- Monitor
- matched_sensitive_pattern
- multimodal_context
- _event_fields
- ._dshow_loopback
- HudFrameRateTests
- speaker_profiles
- windows_startup.py
- captured_video_session
- delete_voice_identity
- stop_target_is_already_gone
- .feed
- .test_a_day_that_fails_to_consolidate_does_not_abort_the_whole_run
- .test_a_day_whose_media_is_done_but_has_no_summary_is_consolidated
- .test_a_summary_older_than_its_own_memories_is_redone
- .test_bash_loop_counts_game_time_through_the_shared_cli
- .test_capture_target_does_not_pull_a_disabled_capture
- .test_opus_stems_go_to_a_container_that_accepts_them
- .test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis
- .test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time
- .test_recording_keeps_the_mix_ahead_of_the_isolated_tracks
- .test_stale_game_session_is_closed_at_the_last_heartbeat
- .active

## God Nodes (most connected - your core abstractions)
1. `ConfigTests` - 120 edges
2. `connect()` - 109 edges
3. `ActionResult` - 102 edges
4. `VideoLoop` - 72 edges
5. `SystemdServiceManager` - 64 edges
6. `HudSnapshot` - 59 edges
7. `Monitor` - 54 edges
8. `Hud` - 52 edges
9. `Meter` - 52 edges
10. `WindowsCaptureBackend` - 48 edges

## Surprising Connections (you probably didn't know these)
- `remove_alias()` --calls--> `connect()`  [EXTRACTED]
  app/backend/tags.py → app/backend/database.py
- `ScreenSettings` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `SensitiveWindows` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `PipelineRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `ProcessFileRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py

## Import Cycles
- None detected.

## Communities (129 total, 31 thin omitted)

### Community 1 - "src/api.ts"
Cohesion: 0.06
Nodes (32): ActivityFrame, AnalysisTrace, AudioEvent, DaySummary, EditingEntry, EditingResult, HourSummary, LayaStatus (+24 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "LinuxCaptureBackend"
Cohesion: 0.05
Nodes (30): CaptureBackend, Monitor, ABC, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco.          Retorna ``N, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável. (+22 more)

### Community 5 - "obs.py"
Cohesion: 0.06
Nodes (58): any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), _encode_field(), ensure_scene(), find_installation() (+50 more)

### Community 6 - "record"
Cohesion: 0.20
Nodes (8): Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record(), _SegmentWriter, _Source

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.13
Nodes (22): audio_file(), _audio_streams(), capture_speaker_sample(), delete_capture(), delete_capture_file(), delete_file(), import_video(), process_file() (+14 more)

### Community 9 - "VideoSettings"
Cohesion: 0.31
Nodes (7): set_video_settings(), VideoSettings, Salvar as preferências não pode apagar chaves silenciosamente.      ``set_video_, Uma instalação antiga não pode ficar sem HUD nem quebrar ao salvar., VideoSettingsRoundTripTests, format_video_app_rule(), BackgroundTasks

### Community 10 - "Lume no Windows"
Cohesion: 0.06
Nodes (29): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, Atalho de gravação (F8), captura-dia (+21 more)

### Community 11 - "SilentTrackTests"
Cohesion: 0.12
Nodes (9): ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Pausar desabilita a unit: só parar valia até o próximo boot., LinuxIdlePauseTests, _pausable(), Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)., Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API. (+1 more)

### Community 12 - "test_services.py"
Cohesion: 0.12
Nodes (41): HudDisplayModeTests, HudEventContractTests, ImageDiffTests, LinuxAudioTapTests, LinuxAudioTrackTests, LinuxFocusVerdictTests, ObsWindowSpecTests, PrivacyTests (+33 more)

### Community 13 - "ActionResult"
Cohesion: 0.07
Nodes (49): connect(), row_dict(), _apply_video_runtime(), _audio_channels(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_screen_sequence() (+41 more)

### Community 14 - "WindowsServiceManager"
Cohesion: 0.18
Nodes (5): Supervisor: mantém os processos de captura vivos e agenda o processamento., Anota que a captura deve (ou não) voltar na próxima abertura do Lume., Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., Combine selective-video and user-idle pauses without racing them.          Aud, WindowsServiceManager

### Community 15 - "game-video-loop"
Cohesion: 0.11
Nodes (37): game-video-loop script, active_monitor(), add_long_marker(), add_marker(), adopt_video(), begin_game_session(), cleanup(), collect_clips() (+29 more)

### Community 16 - "runtime_dir"
Cohesion: 0.23
Nodes (10): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows.  Centraliza as poucas, Diretório para arquivos efêmeros (locks, estado volátil).      Linux usa ``XDG_R, Arquivo que sinaliza "estou gravando vídeo agora".      É como o laço de vídeo p, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``.      Retorna ``True`` se conseg, runtime_dir() (+2 more)

### Community 18 - "RemapToSourceTests"
Cohesion: 0.33
Nodes (3): Voltar os tempos do bloco para o eixo do áudio original.      É a parte que, err, Fim antes do início quebraria a ordenação e a legenda., RemapToSourceTests

### Community 19 - "get"
Cohesion: 0.06
Nodes (54): available(), Choice, choose(), LayaUnavailable, RuntimeError, Cliente do daemon do Laya — classificação de texto por vocabulário fechado.  O `, Uma pergunta de múltipla escolha para cada estado, num único lote.      ``criter, Onde o daemon escuta. No Windows não há socket UNIX — devolve vazio. (+46 more)

### Community 20 - "main.py"
Cohesion: 0.06
Nodes (54): _apply_storage_runtime(), atomic_write(), atomic_write_if_changed(), CleanupSettings, compare_screen_change_test(), ContextUpdate, create_tag(), create_video_marker() (+46 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.16
Nodes (21): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize_file() (+13 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "hud.py"
Cohesion: 0.20
Nodes (14): backfill_confirmed_voice_observations(), backfill_video_session_durations(), delete_video_session(), enroll_voice_identity(), list_video_sessions(), _normalized_average(), Resolve uma identidade portátil ou um caminho legado na raiz atual., resolve_media_source() (+6 more)

### Community 27 - "WasapiError"
Cohesion: 0.22
Nodes (5): _ActivationHandler, GUID, _LazyOle32, Resolve ``ole32`` só no primeiro uso.      ``ctypes.windll`` não existe fora do, Implementação mínima de IActivateAudioInterfaceCompletionHandler.

### Community 29 - "Path"
Cohesion: 0.08
Nodes (42): cancel_video_audio_track_job(), cancel_video_audio_tracks(), _delete_media_sidecars(), delete_video(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), migrate_legacy_cache_file() (+34 more)

### Community 30 - "editing.py"
Cohesion: 0.11
Nodes (34): available_name(), chapter_seconds(), clip_markers(), EditingError, entries(), folder(), frames_to_timecode(), inside_folder() (+26 more)

### Community 31 - "audio-bus.sh"
Cohesion: 0.26
Nodes (17): ensure(), link_ports(), make_null_sink(), selected_mic(), setup(), audio-bus.sh script, sink_exists(), source_exists() (+9 more)

### Community 32 - "src-backup-2026-08-09/api.ts"
Cohesion: 0.07
Nodes (26): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+18 more)

### Community 33 - "src-backup-2026-08-09/main.tsx"
Cohesion: 0.10
Nodes (5): EditableVideoSpeaker, icons, labels, Panel, View

### Community 34 - "pipeline.py"
Cohesion: 0.09
Nodes (21): _alert_sound(), _assert_topmost(), _declare_dpi_aware(), _demo_sequence(), HudSettings, log(), main(), _make_overlay() (+13 more)

### Community 35 - "_call"
Cohesion: 0.23
Nodes (18): _AudioClientActivationParams, _Blob, _call(), _check(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints() (+10 more)

### Community 37 - "_JobObject"
Cohesion: 0.22
Nodes (7): _JobObject, _pipeline(), _python(), Gerenciamento de serviços independente de sistema operacional.  No Linux o sys, Amarra os processos filhos ao ciclo de vida da API.      É o que o systemd con, Return seconds since the last real keyboard or mouse input on Windows., windows_idle_seconds()

### Community 38 - "run"
Cohesion: 0.17
Nodes (9): parse_video_app_rule(), Lista de expressões de um arquivo de padrões, ignorando comentários., Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., read_patterns(), looks_blank(), main(), Gravação seletiva de jogos no Windows — porte de ``bin/game-video-loop``.  Mesma, Amostra um quadro e diz se o vídeo saiu chapado (preto/estático).      É a rede (+1 more)

### Community 39 - "connect"
Cohesion: 0.17
Nodes (12): daemon_flag(), HotkeyDaemon, keyboard_devices(), log(), main(), parse_key(), Path, Atalho global que distingue **toque** de **segurada**, lendo o evdev.  O atalho (+4 more)

### Community 43 - "prompts.py"
Cohesion: 0.21
Nodes (17): get_prompts(), reset_prompt(), active_template(), listing(), _overrides(), payload(), PromptError, PromptSpec (+9 more)

### Community 45 - "winrecord.py"
Cohesion: 0.11
Nodes (17): dbfs(), default_endpoint_name(), Nome do endpoint padrão, ou ``None`` se não houver nenhum., Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _install_stop_handlers(), main(), _mix() (+9 more)

### Community 46 - "SpeechRegionTests"
Cohesion: 0.36
Nodes (5): Trechos ``(início, fim)`` em segundos onde há som acima do limiar.      Função p, speech_regions(), Detecção dos trechos com som, sobre amostras sintéticas., A folga não pode gerar tempo negativo nem passar do fim do áudio., SpeechRegionTests

### Community 47 - ".snapshot"
Cohesion: 0.16
Nodes (12): blend(), EventFrame, HudPanel, Mistura duas cores ``#rrggbb``.      O Canvas do tkinter não tem canal alfa por, Um quadro da animação de confirmação.      ``reveal`` é o quanto o evento tomou, Um painel desenhado num monitor., Corta pela largura real do texto, não por contagem de caracteres.          A HUD, Barra mínima. O evento entra por baixo empurrando o conteúdo normal.          Nã (+4 more)

### Community 48 - "get_manager"
Cohesion: 0.15
Nodes (11): Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.      ``ut, read_shell_config(), _as_bool(), _as_float(), _as_int(), _parse_config(), Laço contínuo de captura de telas — porte de ``bin/capture-loop`` para Python. (+3 more)

### Community 49 - "CallMetricsTests"
Cohesion: 0.27
Nodes (4): CallMetricsTests, Sem separar carga, leitura do prompt e geracao, encurtar prompt e chute., ollama_json repete a chamada para consertar JSON; isso custa tempo., Um audio nao passa pelo Ollama; herdar a medicao de uma tela mentiria.

### Community 50 - "resolve_media_source"
Cohesion: 0.13
Nodes (18): Path, Nome estável para ``<título> | <executável>``.      Alguns jogos, especialmente, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados.          ``, stable_app_label(), begin(), close_stale(), _ensure_schema(), finish() (+10 more)

### Community 51 - "RegionGroupingTests"
Cohesion: 0.31
Nodes (5): group_regions(), Agrupa trechos vizinhos em blocos que caibam numa janela do whisper.      Dois t, Blocos que enchem uma janela do whisper sem esticar o eixo do tempo.      O whis, É o teto que impede um erro de 1 s virar 20 s ao voltar ao original., RegionGroupingTests

### Community 52 - "Path"
Cohesion: 0.23
Nodes (24): analyze_video_chapter(), audio_channel_count(), audio_stream_count(), compact_processed_audio(), describe_long_video(), describe_screen(), describe_video(), extract_adaptive_keyframes() (+16 more)

### Community 53 - "ServiceManager"
Cohesion: 0.10
Nodes (12): ABC, Executa ``start``/``stop``/``restart``/``try-restart``/``enable``/``disable``., Horário configurado do processamento noturno e se está ativo., Reprograma o processamento noturno., Dispara um job avulso sob um nome de unit, para poder cancelá-lo depois., Reinicia a própria interface (usado ao trocar o local dos dados)., Chamado quando a API sobe., Chamado quando a API desce. (+4 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.06
Nodes (17): EditingFolder, CAPTION_LABELS, CAPTION_ORDER, CapturaTab, ContextMenuAction, dayViews, EditableVideoSpeaker, EditingFolderModal() (+9 more)

### Community 55 - "App"
Cohesion: 0.17
Nodes (13): Capture, CleanupSettings, PipelineQueue, ScreenSequenceResult, Status, uploadVideo(), VideoSettings, analysisAverage() (+5 more)

### Community 56 - "videoTime"
Cohesion: 0.14
Nodes (16): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SessionCard(), sessionDuration() (+8 more)

### Community 57 - "_video_pause_file"
Cohesion: 0.15
Nodes (7): Não sei que janela é essa" não é "o usuário saiu do jogo".          ``GetForegro, log(), Mantém Replay Buffer ativo e salva somente quando F8 for pressionado., ``jogo``, ``na-tela`` ou ``fora`` — a mesma pergunta do laço Linux.          Trê, Atualiza o prazo publicado para a HUD e informa se ele venceu., Grava uma sessão lógica, possivelmente dividida em segmentos., VideoLoop

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers.      M, Um fluxo de captura: microfone padrão ou loopback da saída padrão.      A saída, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio).          Um, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "trim_video"
Cohesion: 0.13
Nodes (26): initialize(), detach_video_from_session(), get_cleanup_settings(), Retira um trecho da sessão sem apagar o vídeo nem sua análise., describe_tag_candidates(), discover(), generate_hourly_summaries(), generate_summary() (+18 more)

### Community 61 - "ollama_json"
Cohesion: 0.12
Nodes (20): adaptive_web_research(), days_pending_consolidation(), ollama_chat(), parse_json_response(), private_context_terms(), publish_ai_live(), datetime, Dias com memória analisada cuja narrativa não cobre o que está lá.      Existe p (+12 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.21
Nodes (6): Escreve o sinal de atividade lido pela HUD.          Fica separado de :meth:`_su, Registra um acontecimento pontual e publica na hora.          A sequência é o qu, Segurar: abre a gravação longa e, na segurada seguinte, a fecha., Anota o instante atual da gravação.          Os marcadores ficam em memória e só, Guarda o pré-roll e começa a gravar em paralelo ao Replay Buffer., Pede o Replay Buffer ao OBS e devolve o arquivo que ele escreveu.          Separ

### Community 64 - "HudStateTests"
Cohesion: 0.15
Nodes (12): HudStateTests, As regras que decidem se a captura está saudável.      Rodam nos dois sistemas d, Segurou o atalho: já não é "armado", é gravando de verdade., Ficar calado é normal; confundir com falha destrói a confiança na HUD., _disk_alerts(), evaluate(), Meter, _meter_alerts() (+4 more)

### Community 65 - "local_origin_only"
Cohesion: 0.25
Nodes (8): bounded_video_range(), local_origin_only(), origin_allowed(), Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., remote_client_allowed(), video_file(), Request, StreamingResponse

### Community 67 - "VideoWindowTest"
Cohesion: 0.48
Nodes (4): test_video_window(), VideoWindowTest, O teste de janela do Lume precisa responder o mesmo que o gravador.      Se ele, VideoWindowTestEndpointTests

### Community 68 - "HudPlacementTests"
Cohesion: 0.23
Nodes (6): HudPlacementTests, Onde a HUD desenha, dado o arranjo de monitores., Com um monitor só, "no outro monitor" tem que recair sobre este., choose_monitors(), corner_position(), Monitores que devem receber um painel.      Função pura para poder ser testada s

### Community 69 - "PromptSettingsTests"
Cohesion: 0.13
Nodes (4): PromptSettingsTests, Os prompts sao editaveis, mas nao a ponto de quebrar a analise., Uma variavel esquecida na ficha sumiria do texto sem ninguem notar., Um JSON quebrado nao pode parar a fila inteira.

### Community 70 - "WindowsHudCollector"
Cohesion: 0.19
Nodes (5): log(), Medidores e engate lidos do OBS dedicado, estado lido do sinal de vídeo., WindowsHudCollector, Converte multiplicador linear (0..1) para dBFS, com piso em silêncio., to_db()

### Community 71 - "patch"
Cohesion: 0.18
Nodes (7): log(), MarkerHotkey, MSG, Atalhos globais no Windows, registrados fora de qualquer janela.  No Linux o ata, Espera o desfecho da tecla e diz se foi toque ou segurada.          Bloquear a f, Descarta as repetições enfileiradas enquanto a tecla esteve abaixada., Atalho global que distingue toque de segurada.      ``RegisterHotKey`` avisa qua

### Community 72 - "capture_frames"
Cohesion: 0.20
Nodes (9): 1. Atividades por assunto, com agrupamento por aplicativo como apoio, 2. Contexto completo e verificável em resumos e vídeos, 3. Captura e fila: preservar o lugar de onde a pessoa veio, 4. Vídeos, áudio e busca: acesso consistente às evidências, 5. Ajustes, calendário e acessibilidade, Melhorias aplicadas nesta revisão, Revisão das demais áreas e prioridades, Revisão do Lume — experiência e contexto da IA (+1 more)

### Community 74 - "EditingFolderTests"
Cohesion: 0.11
Nodes (5): EditingFolderTests, A pasta de edicao troca garimpo de arquivo por nome legivel e EDL., 12,5 s a 60 fps sao 750 quadros depois do inicio da timeline., O hardlink segura os bytes, entao apagar por engano so confundiria., O segundo trecho comeca onde o primeiro acaba, e o EDL acompanha.

### Community 75 - "hudsource.py"
Cohesion: 0.27
Nodes (3): Regras sem prefixo procuram somente no executável.          Assim uma pasta cham, Instantâneo de ``video.conf`` e da lista de apps., Settings

### Community 76 - "_Growth"
Cohesion: 0.38
Nodes (6): ActivitiesView(), ActivityCard(), Frame, searchable(), time(), ActivitySession

### Community 77 - "pad_to_segmentation_window"
Cohesion: 0.18
Nodes (11): cancel_video_audio_track_jobs(), get_schedule(), lifespan(), migrate_legacy_media_caches(), process_video_session_job(), Move caches antigos do perfil para a raiz de armazenamento selecionada., ScheduleSettings, set_schedule() (+3 more)

### Community 78 - "multimodal_context"
Cohesion: 0.12
Nodes (4): O vocabulário de tags: normalização, quarentena, fusão e promoção., Substitui o daemon: devolve uma escolha por estado, na ordem pedida., A quarentena governa o vocabulário, não a memória: nada se perde., TagVocabularyTests

### Community 79 - "Path"
Cohesion: 0.07
Nodes (20): LinuxCaptureModeTests, Path, Segurar o atalho: "isto vai ser longo, quero tudo".          O clipe de pré-roll, O tempo de jogo é um fato à parte do vídeo, igual ao gravador do Windows., c1 e c2 não podem carregar a mesma voz, nem o mesmo som duas vezes., Move o foco para ``window``, com o jogo continuando aberto atrás., O outro lado de segurar a sessão: o jogo fechar tem de acabar com ela., A correção não pode virar "grava para sempre".          Quem abre o navegador po (+12 more)

### Community 81 - "winscreen.py"
Cohesion: 0.40
Nodes (5): _attached_source(), _pulse_sources(), Lê PCM cru do monitor de um bus e acumula o pico.          Taxa baixa e um canal, Mapa id -> nome das fontes do PipeWire/Pulse., Fonte à qual o ``parec`` de ``client`` está realmente ligado.      Existe porque

### Community 82 - "context_overflow"
Cohesion: 0.67
Nodes (5): dateOf(), DayPicker(), fullLabel(), MemoryDay, monthLabel()

### Community 83 - "._start"
Cohesion: 0.36
Nodes (4): _Process, Path, Popen, Um processo filho supervisionado.

### Community 84 - "test_main.py"
Cohesion: 0.10
Nodes (25): apply_exact_game_durations(), clear_call_metrics(), compact_saved_capture(), daily_narrative_target(), drain_pending(), game_activity_rows(), known_voice_profiles(), last_call_metrics() (+17 more)

### Community 85 - "_video_pause_file"
Cohesion: 0.22
Nodes (4): Arquivo de estado que o laço de vídeo cria enquanto controla as capturas., (Re)inicia o swayidle apontando os eventos para o flag de idle., _unknown(), _video_pause_file()

### Community 86 - ".snapshot"
Cohesion: 0.17
Nodes (12): _app_label(), _count_markers(), _elapsed(), _event_fields(), _focus_grace_remaining(), _long_elapsed(), Coleta do estado que a HUD mostra, com um coletor por sistema.  Mesma divisão qu, Lê o sinal JSON que o ``winvideo`` reescreve a cada volta do laço.      Um arqui (+4 more)

### Community 87 - "filter_hallucinated_segments"
Cohesion: 0.20
Nodes (7): get_collector(), HudCollector, ABC, Fonte do instantâneo da HUD., Sobe threads de coleta (no-op quando não houver)., Estado atual, já normalizado., Coletor do SO atual, na mesma convenção de :func:`app.capture.get_backend`.

### Community 88 - "hudsource.py"
Cohesion: 0.29
Nodes (3): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas.

### Community 89 - "media_source_key"
Cohesion: 0.18
Nodes (14): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., _config_dir(), configured_storage_root(), media_source_key(), media_source_name() (+6 more)

### Community 90 - "capture_frames"
Cohesion: 0.19
Nodes (9): Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg.  O laço de captura do Linux usa, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar., Diferença percentual entre dois arquivos de imagem. (+1 more)

### Community 91 - "WasapiError"
Cohesion: 0.18
Nodes (6): ProcessLoopbackCapture, Falha numa chamada COM do WASAPI, com o HRESULT preservado., Loopback que inclui ou exclui a árvore de um processo do Windows., WasapiError, WAVEFORMATEXTENSIBLE, OSError

### Community 92 - "context_overflow"
Cohesion: 0.15
Nodes (7): LinuxHudCollector, Path, Estado derivado do laço bash e medidores lidos dos buses do PipeWire.      O ``b, Segmento sendo escrito agora pelo ``gpu-screen-recorder``., Janela em foco, com a mesma cadência do laço bash (2 s).          O sidecar ``.w, Há quanto tempo o segmento em curso começou.      Vem do nome do arquivo, não do, _segment_elapsed()

### Community 93 - "_LazyOle32"
Cohesion: 0.12
Nodes (12): api, TagDecision, TagEntry, TagPromotion, TagStatus, TagTestResult, TagVocabulary, OUTCOME (+4 more)

### Community 97 - "_Growth"
Cohesion: 0.22
Nodes (4): _Growth, _MeterTracker, Contabilidade temporal de uma fonte de áudio.      Guarda desde quando a fonte n, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo).

### Community 98 - "services.py"
Cohesion: 0.20
Nodes (4): Uma unit supervisionada.      ``simple`` roda enquanto o serviço estiver ligad, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef

### Community 99 - ".active"
Cohesion: 0.24
Nodes (7): main(), _monitor_key(), Path, Identidade do monitor a partir do nome do arquivo (``..._mon1_DP-1.png``)., Motivo para não capturar agora, ou ``None`` se pode capturar., ScreenLoop, _thumbnail()

### Community 100 - "pipeline_queue"
Cohesion: 0.29
Nodes (7): capture_speed_stats(), pipeline_queue(), pipeline_summary_job(), queue_eta_seconds(), Média recente de análise por tipo, para estimar a duração da fila.      Só as úl, Estimativa da fila restante; a execução do worker é sequencial., Expose the worker's actual plan; older workers report only saved evidence.

### Community 101 - "LinuxAudioTapTests"
Cohesion: 0.17
Nodes (13): concat_videos(), cut_head(), media_duration(), Path, Duração em segundos, ou 0 quando o ffprobe não souber dizer., Guarda só os primeiros ``seconds`` do arquivo, copiando os streams.      Cortar, Emenda os pedaços num arquivo só, copiando os streams.      Os dois vêm do mesmo, Confirma uma ação aceita sem depender da interface estar em foco. (+5 more)

### Community 102 - "_activity_groups"
Cohesion: 0.10
Nodes (26): _activity_app(), _activity_batch_summary(), _activity_groups(), _activity_image(), analyze_screen_sequence(), context_overflow(), generate_visual_activities(), _merge_activity_batches() (+18 more)

### Community 103 - "foreground_details"
Cohesion: 0.40
Nodes (3): foreground_details(), Título, classe e executável da janela em foco — o que o OBS precisa     para eng, Janela atual e resultado das regras usando campos separados.

### Community 104 - ".feed"
Cohesion: 0.29
Nodes (6): A faixa está muda o bastante para transcrevê-la ser desperdício?      Numa sessã, track_is_silent(), Faixas mudas não valem uma transcrição.      Numa sessão sem Discord a faixa del, -40 dBFS é fala baixa de verdade; pular isso perderia conversa., Na dúvida, transcreve: perder fala é pior que gastar tempo., SilentTrackTests

### Community 105 - "read_shell_config"
Cohesion: 0.13
Nodes (11): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., ease_in_cubic(), ease_out_back(), ease_out_cubic() (+3 more)

### Community 106 - "Monitor"
Cohesion: 0.16
Nodes (16): capture_change_test_frames(), capture_frames(), get_screen_settings(), get_video_settings(), parse_shell_config(), privacy_decision(), Estado operacional do gravador, separado da mera configuração ativa., Janela ativa e o motivo para não capturar, se houver.      A mesma regra nos doi (+8 more)

### Community 109 - "_event_fields"
Cohesion: 0.29
Nodes (4): diarize(), pad_to_segmentation_window(), Descarta o que a diarização inventou sobre o silêncio de completamento., turns_within_duration()

### Community 111 - "HudFrameRateTests"
Cohesion: 0.33
Nodes (3): HudFrameRateTests, As três cadências existem por causa do custo de redesenhar.      Cada volta recr, Uma entrada de 0,26 s precisa de quadros suficientes para não escadear.

### Community 113 - "windows_startup.py"
Cohesion: 0.60
Nodes (4): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows.  Executado com ``pythonw.exe`` pe

### Community 115 - "delete_voice_identity"
Cohesion: 0.50
Nodes (4): delete_voice_identity(), Volta uma amostra ao estado não identificado sem perder sua diarização., Remove um perfil incorreto e solta as amostras para nova classificação., _speaker_without_identity()

## Knowledge Gaps
- **122 isolated node(s):** `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame`, `StorageCandidate`, `WebSource` (+117 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **31 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `SilentTrackTests` to `ConfigTests`, `VideoLoop`, `VideoSettings`, `test_services.py`, `ActionResult`, `WindowsServiceManager`, `RemapToSourceTests`, `main.py`, `hud.py`, `Path`, `_JobObject`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `ServiceManager`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `pad_to_segmentation_window`, `multimodal_context`, `Path`, `LinuxAppRuleMatchTests`, `._start`, `test_main.py`, `HoldDetectorTests`, `services.py`, `.feed`, `read_shell_config`, `HudFrameRateTests`, `stop_target_is_already_gone`?**
  _High betweenness centrality (0.155) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `VideoSettings`, `SilentTrackTests`, `audio_intelligence.py`, `ollama_json`, `local_origin_only`, `VideoWindowTest`, `test_main.py`, `hudsource.py`, `multimodal_context`, `_event_fields`, `speaker_profiles`, `captured_video_session`, `stop_target_is_already_gone`, `.test_a_day_that_fails_to_consolidate_does_not_abort_the_whole_run`, `.test_a_day_whose_media_is_done_but_has_no_summary_is_consolidated`, `.test_a_summary_older_than_its_own_memories_is_redone`, `.test_bash_loop_counts_game_time_through_the_shared_cli`, `.test_capture_target_does_not_pull_a_disabled_capture`, `.test_opus_stems_go_to_a_container_that_accepts_them`, `.test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis`, `.test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time`, `.test_recording_keeps_the_mix_ahead_of_the_isolated_tracks`, `.test_stale_game_session_is_closed_at_the_last_heartbeat`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `SilentTrackTests` to `ConfigTests`, `VideoSettings`, `test_services.py`, `runtime_dir`, `RemapToSourceTests`, `_JobObject`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `ServiceManager`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `pad_to_segmentation_window`, `multimodal_context`, `Path`, `LinuxAppRuleMatchTests`, `test_main.py`, `_video_pause_file`, `HoldDetectorTests`, `.feed`, `read_shell_config`, `HudFrameRateTests`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `VideoWindowTest`) actually correct?**
  _`ConfigTests` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 66 inferred relationships involving `ActionResult` (e.g. with `CleanupSettings` and `ContextUpdate`) actually correct?**
  _`ActionResult` has 66 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `VideoLoop` (e.g. with `HoldDetectorTests` and `HudDisplayModeTests`) actually correct?**
  _`VideoLoop` has 35 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` to the rest of the system?**
  _122 weakly-connected nodes found - possible documentation gaps or missing edges._