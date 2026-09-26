# Graph Report - lume  (2026-09-26)

## Corpus Check
- 74 files · ~146,807 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2331 nodes · 5542 edges · 132 communities (97 shown, 35 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 539 edges (avg confidence: 0.51)
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
- Path
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
- WasapiError
- context_overflow
- _LazyOle32
- HoldDetectorTests
- toggle-video-hud
- lume-audio-diag
- _Growth
- services.py
- .active
- LinuxAudioTapTests
- .feed
- read_shell_config
- multimodal_context
- .action
- HudCollector
- pad_to_segmentation_window
- delete_voice_identity
- .feed
- captured_video_session
- stop_target_is_already_gone
- exige
- .test_a_day_that_fails_to_consolidate_does_not_abort_the_whole_run
- .read
- _event_fields
- .test_nome_do_download_usa_o_jogo_do_sidecar_quando_a_ia_ainda_nao_titulou
- .test_nome_de_trecho_de_sessao_diz_qual_pedaco_e
- .test_nome_da_sessao_igual_ao_jogo_nao_entra_duas_vezes
- .test_clipe_sem_jogo_e_sem_titulo_mantem_o_nome_do_arquivo
- .test_nome_da_versao_leve_diz_o_teto
- .test_versao_leve_mantem_somente_a_faixa_de_mixagem
- .test_versao_leve_mais_antiga_que_o_original_e_descartada
- .test_upload_sem_confirmacao_explicita_e_recusado
- .test_link_fica_salvo_para_recopiar_depois
- .test_a_summary_older_than_its_own_memories_is_redone
- .test_bash_loop_counts_game_time_through_the_shared_cli
- .test_capture_target_does_not_pull_a_disabled_capture
- .test_opus_stems_go_to_a_container_that_accepts_them
- .test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis
- .test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time
- .test_recording_keeps_the_mix_ahead_of_the_isolated_tracks
- .test_stale_game_session_is_closed_at_the_last_heartbeat

## God Nodes (most connected - your core abstractions)
1. `ConfigTests` - 120 edges
2. `connect()` - 118 edges
3. `ActionResult` - 107 edges
4. `VideoLoop` - 72 edges
5. `SystemdServiceManager` - 68 edges
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

## Communities (132 total, 35 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.04
Nodes (4): multimodal_context(), Agrupa telas e áudios sobrepostos em momentos únicos para as sínteses., ConfigTests, Path

### Community 1 - "src/api.ts"
Cohesion: 0.05
Nodes (36): ActivityFrame, AnalysisTrace, AppMode, AudioEvent, DaySummary, EditingEntry, EditingResult, HourSummary (+28 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "LinuxCaptureBackend"
Cohesion: 0.05
Nodes (39): CaptureBackend, matched_sensitive_pattern(), Monitor, ABC, Path, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Primeiro padrão sensível (regex, case-insensitive) que casa com a janela.      M, Contrato que Linux e Windows implementam. (+31 more)

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
Nodes (12): light_video_command(), _LightVersionJob, progress_percent(), Popen, A receita que cabe no teto: quanto bitrate, em que tamanho de imagem., Bitrate que cabe no teto, e o tamanho de imagem que esse bitrate aguenta.      R, Recodificação que cabe no teto e serve para ser assistida por outra pessoa., Lê ``out_time_us=12500000`` do ``-progress`` e devolve 21 num clipe de 60s. (+4 more)

### Community 9 - "VideoSettings"
Cohesion: 0.31
Nodes (7): set_video_settings(), VideoSettings, Salvar as preferências não pode apagar chaves silenciosamente.      ``set_video_, Uma instalação antiga não pode ficar sem HUD nem quebrar ao salvar., VideoSettingsRoundTripTests, format_video_app_rule(), BackgroundTasks

### Community 10 - "Lume no Windows"
Cohesion: 0.05
Nodes (39): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, Abrir de outro aparelho, As três faixas de áudio (+31 more)

### Community 11 - "SilentTrackTests"
Cohesion: 0.08
Nodes (24): LinuxCaptureModeTests, LinuxFocusVerdictTests, Path, Segurar o atalho: "isto vai ser longo, quero tudo".          O clipe de pré-roll, O tempo de jogo é um fato à parte do vídeo, igual ao gravador do Windows., Sair do jogo é uma coisa; o KWin mudar de ideia por um segundo é outra.      O l, Move o foco para ``window``, com o jogo continuando aberto atrás., O outro lado de segurar a sessão: o jogo fechar tem de acabar com ela. (+16 more)

### Community 12 - "test_services.py"
Cohesion: 0.11
Nodes (36): HudDisplayModeTests, HudEventContractTests, HudFrameRateTests, ImageDiffTests, LinuxAudioTrackTests, ObsWindowSpecTests, PrivacyTests, Testes das peças que tornam o app portável entre Linux e Windows.  Rodam nos doi (+28 more)

### Community 13 - "ActionResult"
Cohesion: 0.12
Nodes (4): O vocabulário de tags: normalização, quarentena, fusão e promoção., Substitui o daemon: devolve uma escolha por estado, na ordem pedida., A quarentena governa o vocabulário, não a memória: nada se perde., TagVocabularyTests

### Community 14 - "WindowsServiceManager"
Cohesion: 0.18
Nodes (5): Return seconds since the last real keyboard or mouse input on Windows., Supervisor: mantém os processos de captura vivos e agenda o processamento., Combine selective-video and user-idle pauses without racing them.          Audio, windows_idle_seconds(), WindowsServiceManager

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
Nodes (52): available(), Choice, choose(), LayaUnavailable, RuntimeError, Cliente do daemon do Laya — classificação de texto por vocabulário fechado.  O `, Uma pergunta de múltipla escolha para cada estado, num único lote.      ``criter, Onde o daemon escuta. No Windows não há socket UNIX — devolve vazio. (+44 more)

### Community 20 - "main.py"
Cohesion: 0.04
Nodes (111): _apply_storage_runtime(), _apply_video_runtime(), atomic_write(), atomic_write_if_changed(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_screen_sequence() (+103 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.13
Nodes (22): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize_file() (+14 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "hud.py"
Cohesion: 0.08
Nodes (13): ModoLuminiTests, O Lumini é a mesma base instalada só como gravador.      Sem estes testes, a ins, Atualizar o Lume não pode desligar a análise de quem a tem., O modo precisa valer para todo processo da máquina.          São quatro que prec, Experimentar o Lumini não pode exigir editar a instalação., Um erro de digitação não pode mutilar a interface de ninguém., Sem isso a interface adivinha, e mostra botões de IA a quem não tem., Um prefixo desatento na tabela derrubaria a biblioteca de clipes. (+5 more)

### Community 27 - "WasapiError"
Cohesion: 0.22
Nodes (5): _ActivationHandler, GUID, _LazyOle32, Resolve ``ole32`` só no primeiro uso.      ``ctypes.windll`` não existe fora do, Implementação mínima de IActivateAudioInterfaceCompletionHandler.

### Community 29 - "Path"
Cohesion: 0.14
Nodes (11): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., ease_in_cubic(), ease_out_back(), ease_out_cubic() (+3 more)

### Community 30 - "editing.py"
Cohesion: 0.10
Nodes (38): available_name(), chapter_seconds(), clip_markers(), EditingError, entries(), folder(), frames_to_timecode(), inside_folder() (+30 more)

### Community 31 - "audio-bus.sh"
Cohesion: 0.26
Nodes (18): discord(), ensure(), link_ports(), make_null_sink(), selected_mic(), setup(), audio-bus.sh script, sink_exists() (+10 more)

### Community 32 - "src-backup-2026-08-09/api.ts"
Cohesion: 0.07
Nodes (26): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+18 more)

### Community 33 - "src-backup-2026-08-09/main.tsx"
Cohesion: 0.10
Nodes (5): EditableVideoSpeaker, icons, labels, Panel, View

### Community 34 - "pipeline.py"
Cohesion: 0.14
Nodes (6): LinuxAudioTapTests, Um app com vários streams tem de entrar inteiro na faixa de sistema.      O ``pw, c1 e c2 não podem carregar a mesma voz, nem o mesmo som duas vezes., LinuxCaptureBackend, Path, argv do ffmpeg que grava mic + Discord + sistema num WAV de 3 canais.          M

### Community 35 - "_call"
Cohesion: 0.23
Nodes (18): _AudioClientActivationParams, _Blob, _call(), _check(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints() (+10 more)

### Community 37 - "_JobObject"
Cohesion: 0.24
Nodes (7): MultipartBody, RuntimeError, O envio foi interrompido a pedido de quem o começou., Corpo multipart que lê o arquivo em blocos e sabe o próprio tamanho.      O tama, Publica o arquivo e devolve a URL. **Só o job de upload chama isto.**      Nenhu, SharingCancelled, upload_file()

### Community 38 - "run"
Cohesion: 0.22
Nodes (4): _Growth, _MeterTracker, Contabilidade temporal de uma fonte de áudio.      Guarda desde quando a fonte n, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo).

### Community 39 - "connect"
Cohesion: 0.12
Nodes (16): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.      ``ut, read_shell_config(), daemon_flag(), HotkeyDaemon, keyboard_devices(), log(), main(), parse_key() (+8 more)

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
Cohesion: 0.12
Nodes (16): _assert_topmost(), blend(), EventFrame, HudPanel, _make_overlay(), HWND real de um ``Toplevel`` do tkinter., Deixa a janela flutuando, sem foco, sem clique e fora do Alt+Tab., Reafirma o topo da pilha.      Um jogo entrando em tela cheia reordena o z-order (+8 more)

### Community 48 - "get_manager"
Cohesion: 0.08
Nodes (24): Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg.  O laço de captura do Linux usa, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar., Diferença percentual entre dois arquivos de imagem. (+16 more)

### Community 49 - "CallMetricsTests"
Cohesion: 0.27
Nodes (4): CallMetricsTests, Sem separar carga, leitura do prompt e geracao, encurtar prompt e chute., ollama_json repete a chamada para consertar JSON; isso custa tempo., Um audio nao passa pelo Ollama; herdar a medicao de uma tela mentiria.

### Community 50 - "resolve_media_source"
Cohesion: 0.22
Nodes (14): begin(), close_stale(), _ensure_schema(), finish(), heartbeat(), iso_time(), main(), Contagem de tempo por jogo, independente do que foi gravado.  O tempo de jogo é (+6 more)

### Community 51 - "RegionGroupingTests"
Cohesion: 0.31
Nodes (5): group_regions(), Agrupa trechos vizinhos em blocos que caibam numa janela do whisper.      Dois t, Blocos que enchem uma janela do whisper sem esticar o eixo do tempo.      O whis, É o teto que impede um erro de 1 s virar 20 s ao voltar ao original., RegionGroupingTests

### Community 52 - "Path"
Cohesion: 0.11
Nodes (6): Achar o clipe e mandar para alguém.      O gravador nomeia por data, então o que, Numa jogada a fluidez lê melhor que a nitidez: 720p60, não 1080p30., Pedir 63 Mbps de um vídeo gravado a 2,3 gastaria CPU para nada., Para sempre" é decisão de quem publica, não do código., Mandar arquivo para fora só acontece pelo caminho que pede confirmação., SharingTests

### Community 53 - "ServiceManager"
Cohesion: 0.08
Nodes (15): _pipeline(), ABC, _python(), Gerenciamento de serviços independente de sistema operacional.  No Linux o syste, Executa ``start``/``stop``/``restart``/``try-restart``/``enable``/``disable``., Horário configurado do processamento noturno e se está ativo., Reprograma o processamento noturno., Dispara um job avulso sob um nome de unit, para poder cancelá-lo depois. (+7 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.05
Nodes (26): EditingFolder, LightVersion, ShareUpload, CAPTION_LABELS, CAPTION_ORDER, CapturaTab, clipClock(), ContextMenuAction (+18 more)

### Community 55 - "App"
Cohesion: 0.12
Nodes (18): Capture, CleanupSettings, PipelineQueue, ScreenSequenceResult, Status, uploadVideo(), VideoSettings, ABAS_DE_AJUSTES_DA_ANALISE (+10 more)

### Community 56 - "videoTime"
Cohesion: 0.18
Nodes (13): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), TIMELINE_ZOOM_LEVELS (+5 more)

### Community 57 - "_video_pause_file"
Cohesion: 0.05
Nodes (41): Não sei que janela é essa" não é "o usuário saiu do jogo".          ``GetForegro, parse_video_app_rule(), Lista de expressões de um arquivo de padrões, ignorando comentários., Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., read_patterns(), concat_videos(), cut_head(), foreground_details() (+33 more)

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers.      M, Um fluxo de captura: microfone padrão ou loopback da saída padrão.      A saída, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio).          Um, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "trim_video"
Cohesion: 0.06
Nodes (108): initialize(), get_cleanup_settings(), _activity_app(), _activity_batch_summary(), _activity_groups(), _activity_image(), adaptive_web_research(), analyze_screen_sequence() (+100 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.32
Nodes (7): normalized_limit(), Publica o clipe num host grátis, **só com confirmação explícita**.      A trava, Falha que o usuário precisa ler, não um defeito interno., A resposta é a URL em texto puro — e o erro também vem como HTTP 200.          P, resolve_host(), SharingError, start_upload()

### Community 64 - "HudStateTests"
Cohesion: 0.07
Nodes (31): HudStateTests, As regras que decidem se a captura está saudável.      Rodam nos dois sistemas d, Segurou o atalho: já não é "armado", é gravando de verdade., Ficar calado é normal; confundir com falha destrói a confiança na HUD., _alert_sound(), _declare_dpi_aware(), _demo_sequence(), HudSettings (+23 more)

### Community 65 - "local_origin_only"
Cohesion: 0.08
Nodes (31): cancel_light_version(), cancel_upload(), cancel_video_audio_track_job(), cancel_video_audio_track_jobs(), cancel_video_audio_tracks(), download_video(), lifespan(), light_version_state() (+23 more)

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
Cohesion: 0.26
Nodes (3): log(), Medidores e engate lidos do OBS dedicado, estado lido do sinal de vídeo., WindowsHudCollector

### Community 71 - "patch"
Cohesion: 0.18
Nodes (5): log(), MSG, Atalhos globais no Windows, registrados fora de qualquer janela.  No Linux o ata, Espera o desfecho da tecla e diz se foi toque ou segurada.          Bloquear a f, Descarta as repetições enfileiradas enquanto a tecla esteve abaixada.

### Community 72 - "capture_frames"
Cohesion: 0.20
Nodes (9): 1. Atividades por assunto, com agrupamento por aplicativo como apoio, 2. Contexto completo e verificável em resumos e vídeos, 3. Captura e fila: preservar o lugar de onde a pessoa veio, 4. Vídeos, áudio e busca: acesso consistente às evidências, 5. Ajustes, calendário e acessibilidade, Melhorias aplicadas nesta revisão, Revisão das demais áreas e prioridades, Revisão do Lume — experiência e contexto da IA (+1 more)

### Community 74 - "EditingFolderTests"
Cohesion: 0.11
Nodes (5): EditingFolderTests, A pasta de edicao troca garimpo de arquivo por nome legivel e EDL., 12,5 s a 60 fps sao 750 quadros depois do inicio da timeline., O hardlink segura os bytes, entao apagar por engano so confundiria., O segundo trecho comeca onde o primeiro acaba, e o EDL acompanha.

### Community 75 - "hudsource.py"
Cohesion: 0.29
Nodes (7): _clip_row(), download_filename(), ``2026-09-26 00-10 Sea of Thieves — trecho 02 de 05``, sem extensão.      Vale p, Nome oferecido no download, com a extensão do arquivo original., Posição do trecho na sessão, na mesma ordem que a pasta de edição usa.      Uma, _session_position(), share_stem()

### Community 76 - "_Growth"
Cohesion: 0.38
Nodes (6): ActivitiesView(), ActivityCard(), Frame, searchable(), time(), ActivitySession

### Community 77 - "Path"
Cohesion: 0.40
Nodes (5): _attached_source(), _pulse_sources(), Lê PCM cru do monitor de um bus e acumula o pico.          Taxa baixa e um canal, Mapa id -> nome das fontes do PipeWire/Pulse., Fonte à qual o ``parec`` de ``client`` está realmente ligado.      Existe porque

### Community 78 - "multimodal_context"
Cohesion: 0.07
Nodes (45): connect(), row_dict(), _audio_channels(), backfill_confirmed_voice_observations(), backfill_video_session_durations(), capture_days(), capture_payload(), captures() (+37 more)

### Community 79 - "Path"
Cohesion: 0.22
Nodes (13): light_video_file(), Baixa a versão leve pronta; 409 enquanto ela não existir.      Não gera nada aqu, light_filename(), light_state(), Path, O teto entra no nome: duas versões do mesmo clipe não se confundem., O teto e a receita ficam **fora** do hash, de propósito.      Assim a limpeza de, Versão leve pronta e mais nova que o original, ou nada.      O corte (``/api/vid (+5 more)

### Community 81 - "winscreen.py"
Cohesion: 0.50
Nodes (4): delete_voice_identity(), Volta uma amostra ao estado não identificado sem perder sua diarização., Remove um perfil incorreto e solta as amostras para nova classificação., _speaker_without_identity()

### Community 82 - "context_overflow"
Cohesion: 0.67
Nodes (5): dateOf(), DayPicker(), fullLabel(), MemoryDay, monthLabel()

### Community 83 - "._start"
Cohesion: 0.24
Nodes (6): _JobObject, _Process, Path, Popen, Amarra os processos filhos ao ciclo de vida da API.      É o que o systemd conse, Um processo filho supervisionado.

### Community 84 - "test_main.py"
Cohesion: 0.20
Nodes (15): _as_float(), _as_ratio(), host_catalog(), _link_dict(), links_for(), probe_video_shape(), prune_share_cache(), Mandar um clipe para alguém: nome legível, versão leve e link público.  O gravad (+7 more)

### Community 85 - "_video_pause_file"
Cohesion: 0.29
Nodes (3): Arquivo de estado que o laço de vídeo cria enquanto controla as capturas.      M, (Re)inicia o swayidle apontando os eventos para o flag de idle., _video_pause_file()

### Community 86 - ".snapshot"
Cohesion: 0.19
Nodes (13): _app_label(), _count_markers(), _elapsed(), _focus_grace_remaining(), _long_elapsed(), Path, Coleta do estado que a HUD mostra, com um coletor por sistema.  Mesma divisão qu, Lê o sinal JSON que o ``winvideo`` reescreve a cada volta do laço.      Um arqui (+5 more)

### Community 87 - "filter_hallucinated_segments"
Cohesion: 0.11
Nodes (9): ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Pausar desabilita a unit: só parar valia até o próximo boot., LinuxIdlePauseTests, _pausable(), Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)., Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API. (+1 more)

### Community 88 - "hudsource.py"
Cohesion: 0.17
Nodes (3): Um clipe no disco com o sidecar do gravador e a linha do banco., Recodificar um arquivo que já cabe só pioraria a imagem., ``GET`` que dispara meio minuto de ffmpeg viraria timeout no navegador.

### Community 89 - "media_source_key"
Cohesion: 0.14
Nodes (19): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., delete_video(), delete_video_caches(), list_videos(), _config_dir() (+11 more)

### Community 91 - "WasapiError"
Cohesion: 0.18
Nodes (6): ProcessLoopbackCapture, Falha numa chamada COM do WASAPI, com o HRESULT preservado., Loopback que inclui ou exclui a árvore de um processo do Windows., WasapiError, WAVEFORMATEXTENSIBLE, OSError

### Community 92 - "context_overflow"
Cohesion: 0.08
Nodes (26): bounded_video_range(), health(), local_origin_only(), origin_allowed(), Se este caminho só faz sentido com o pipeline instalado., No Lumini, o que depende de IA responde 409 em vez de tentar.      Esconder os b, Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., Se o ``Host`` (ou a origem) descreve este servidor.      Além dos nomes configur (+18 more)

### Community 93 - "_LazyOle32"
Cohesion: 0.12
Nodes (12): api, TagDecision, TagEntry, TagPromotion, TagStatus, TagTestResult, TagVocabulary, OUTCOME (+4 more)

### Community 94 - "HoldDetectorTests"
Cohesion: 0.20
Nodes (3): HoldDetectorTests, Toque e segurada a partir dos eventos crus do teclado.      O atalho do KDE só c, O formato do ``input_event`` é contrato do kernel, não detalhe nosso.          E

### Community 98 - "services.py"
Cohesion: 0.20
Nodes (4): Uma unit supervisionada.      ``simple`` roda enquanto o serviço estiver ligado, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef

### Community 99 - ".active"
Cohesion: 0.24
Nodes (5): Host, Um lugar onde o arquivo pode ser publicado, sem conta e sem login., Sobe o arquivo fora da requisição HTTP, com progresso e cancelamento., remember_link(), _UploadJob

### Community 101 - "LinuxAudioTapTests"
Cohesion: 0.50
Nodes (4): forget_shared_link(), Tira o link da lista. O arquivo continua no ar — o host é que o apaga., forget_link(), Esquece o link. Não o despublica — e a interface diz isso em voz alta.

### Community 104 - ".feed"
Cohesion: 0.24
Nodes (8): Pico de um WAV PCM 16 bits, em dBFS. ``-inf`` vira o piso -99., A faixa está muda o bastante para transcrevê-la ser desperdício?      Numa sessã, track_is_silent(), track_peak_dbfs(), Faixas mudas não valem uma transcrição.      Numa sessão sem Discord a faixa del, -40 dBFS é fala baixa de verdade; pular isso perderia conversa., Na dúvida, transcreve: perder fala é pior que gastar tempo., SilentTrackTests

### Community 105 - "read_shell_config"
Cohesion: 0.29
Nodes (3): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas.

### Community 108 - "multimodal_context"
Cohesion: 0.40
Nodes (3): MediaFreshnessTests, As URLs de mídia têm de mudar quando o arquivo muda.      O corte reescreve o ví, Um clipe apagado entre a listagem e a montagem da URL não é erro 500.

### Community 110 - ".action"
Cohesion: 0.27
Nodes (3): Anota que a captura deve (ou não) voltar na próxima abertura do Lume.          N, Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., _unknown()

### Community 111 - "HudCollector"
Cohesion: 0.11
Nodes (11): get_collector(), HudCollector, LinuxHudCollector, ABC, Fonte do instantâneo da HUD., Sobe threads de coleta (no-op quando não houver)., Estado atual, já normalizado., Estado derivado do laço bash e medidores lidos dos buses do PipeWire.      O ``b (+3 more)

### Community 114 - "pad_to_segmentation_window"
Cohesion: 0.29
Nodes (4): diarize(), pad_to_segmentation_window(), Descarta o que a diarização inventou sobre o silêncio de completamento., turns_within_duration()

### Community 115 - "delete_voice_identity"
Cohesion: 0.07
Nodes (48): audio_file(), _audio_streams(), capture_speaker_sample(), _delete_media_sidecars(), directory_stats(), ensure_video_thumbnail(), import_video(), media_url() (+40 more)

### Community 117 - ".feed"
Cohesion: 0.29
Nodes (3): _FakeResponse, O host recusa com HTTP 200 e um texto no corpo; engolir isso deixaria         a, Resposta de host de arquivo: corpo em texto puro, sem rede envolvida.

### Community 126 - "exige"
Cohesion: 1.00
Nodes (3): exige(), instalar-lumini.sh script, tem()

## Knowledge Gaps
- **137 isolated node(s):** `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame`, `StorageCandidate`, `WebSource` (+132 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **35 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `filter_hallucinated_segments` to `ConfigTests`, `VideoSettings`, `SilentTrackTests`, `test_services.py`, `ActionResult`, `WindowsServiceManager`, `RemapToSourceTests`, `main.py`, `hud.py`, `Path`, `pipeline.py`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `Path`, `ServiceManager`, `trim_video`, `HudStateTests`, `local_origin_only`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `multimodal_context`, `LinuxAppRuleMatchTests`, `._start`, `HoldDetectorTests`, `services.py`, `.feed`, `multimodal_context`, `.action`, `delete_voice_identity`, `.feed`, `stop_target_is_already_gone`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `filter_hallucinated_segments` to `ConfigTests`, `VideoSettings`, `SilentTrackTests`, `test_services.py`, `ActionResult`, `runtime_dir`, `RemapToSourceTests`, `main.py`, `hud.py`, `Path`, `pipeline.py`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `Path`, `ServiceManager`, `trim_video`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `LinuxAppRuleMatchTests`, `_video_pause_file`, `HoldDetectorTests`, `.feed`, `multimodal_context`, `.feed`?**
  _High betweenness centrality (0.076) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `.test_a_day_that_fails_to_consolidate_does_not_abort_the_whole_run`, `_event_fields`, `VideoSettings`, `.test_a_summary_older_than_its_own_memories_is_redone`, `.test_bash_loop_counts_game_time_through_the_shared_cli`, `.test_capture_target_does_not_pull_a_disabled_capture`, `.test_opus_stems_go_to_a_container_that_accepts_them`, `.test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis`, `.test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time`, `.test_recording_keeps_the_mix_ahead_of_the_isolated_tracks`, `.test_stale_game_session_is_closed_at_the_last_heartbeat`, `audio_intelligence.py`, `trim_video`, `ollama_json`, `VideoWindowTest`, `filter_hallucinated_segments`, `context_overflow`, `read_shell_config`, `pad_to_segmentation_window`, `captured_video_session`, `stop_target_is_already_gone`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `VideoWindowTest`) actually correct?**
  _`ConfigTests` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 71 inferred relationships involving `ActionResult` (e.g. with `CleanupSettings` and `ContextUpdate`) actually correct?**
  _`ActionResult` has 71 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `VideoLoop` (e.g. with `HoldDetectorTests` and `HudDisplayModeTests`) actually correct?**
  _`VideoLoop` has 35 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` to the rest of the system?**
  _137 weakly-connected nodes found - possible documentation gaps or missing edges._