# Graph Report - lume  (2026-09-29)

## Corpus Check
- 83 files · ~163,740 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2662 nodes · 6354 edges · 149 communities (120 shown, 29 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 662 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `c1d95dd7`
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
- get_backend
- .snapshot
- filter_hallucinated_segments
- hudsource.py
- media_source_key
- .grab_frame
- WasapiError
- context_overflow
- _LazyOle32
- HoldDetectorTests
- toggle-video-hud
- lume-audio-diag
- winscreen.py
- services.py
- .active
- devDependencies
- hudsource.py
- _LazyOle32
- HudCollector
- .feed
- read_shell_config
- .test_an_unreadable_foreground_window_neither_starts_nor_advances_the_countdown
- multimodal_context
- _Growth
- .action
- matched_sensitive_pattern
- VideoActivityFlagTests
- rebuild_voice_identity
- LinuxHudCollector
- delete_voice_identity
- HudStatus
- .feed
- LinuxAudioTapTests
- WindowsStartupTests
- ._partial_segment
- multimodal_context
- _event_fields
- stop_target_is_already_gone
- test_updater.py
- stop_target_is_already_gone
- exige
- devDependencies
- get_backend
- share_stem
- _activity_groups
- .test_a_summary_older_than_its_own_memories_is_redone
- UpdateNotice.tsx
- WindowsStartupTests
- GUID
- _devmode_w
- delete_voice_identity
- validate_relevant_media
- ValueError
- .active_monitor
- _scaled_size
- context_overflow
- test_updater.py
- .test_capture_target_does_not_pull_a_disabled_capture
- .test_o_teto_do_discord_preserva_os_sessenta_quadros
- .test_o_original_que_ja_cabe_nao_e_recodificado
- .test_original_que_cabe_com_volumes_copia_a_imagem_e_refaz_so_o_audio
- .test_consultar_o_estado_nunca_liga_o_ventilador

## God Nodes (most connected - your core abstractions)
1. `ConfigTests` - 122 edges
2. `connect()` - 121 edges
3. `ActionResult` - 120 edges
4. `VideoLoop` - 83 edges
5. `SystemdServiceManager` - 77 edges
6. `HudSnapshot` - 69 edges
7. `Monitor` - 63 edges
8. `Hud` - 61 edges
9. `Meter` - 59 edges
10. `WindowsCaptureBackend` - 59 edges

## Surprising Connections (you probably didn't know these)
- `apply_pending()` --references--> `scripts`  [EXTRACTED]
  app/backend/updater.py → frontend/package.json
- `delete_video_marker()` --calls--> `connect()`  [EXTRACTED]
  app/backend/main.py → app/backend/database.py
- `screen_sequence_result()` --calls--> `connect()`  [EXTRACTED]
  app/backend/main.py → app/backend/database.py
- `remove_alias()` --calls--> `connect()`  [EXTRACTED]
  app/backend/tags.py → app/backend/database.py
- `ScreenSettings` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py

## Import Cycles
- None detected.

## Communities (149 total, 29 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.03
Nodes (21): captured_video_session(), end_video_session(), Lê a identidade portátil deixada pelo gravador seletivo.      Vídeos antigos só, Estado operacional do gravador, separado da mera configuração ativa., Encerra agora a sessão que já está contando para parar fora do jogo.      Quem s, selective_video_status(), _activity_groups(), Separa por aplicativo e continuidade; mudanças de título não quebram a sessão. (+13 more)

### Community 1 - "src/api.ts"
Cohesion: 0.05
Nodes (41): ActivityFrame, AnalysisTrace, AppMode, AudioEvent, ConfirmationSound, DaySummary, EditingEntry, EditingResult (+33 more)

### Community 2 - "package.json"
Cohesion: 0.10
Nodes (54): _activity_app(), _activity_image(), analyze_video_chapter(), audio_channel_count(), audio_stream_count(), clear_call_metrics(), compact_processed_audio(), compact_saved_capture() (+46 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "LinuxCaptureBackend"
Cohesion: 0.04
Nodes (61): _config_dir(), configured_storage_root(), Onde ficam ``tela.conf`` e a lista de janelas sensíveis.      No Linux, o lugar, Testes das peças que tornam o app portável entre Linux e Windows.  Rodam nos doi, ScreenConfigTests, CaptureBackend, matched_sensitive_pattern(), ABC (+53 more)

### Community 5 - "obs.py"
Cohesion: 0.06
Nodes (63): any_fullscreen(), apply_mic_filters(), batch(), call(), _copy_installation(), diagnostics(), ensure_scene(), find_installation() (+55 more)

### Community 6 - "record"
Cohesion: 0.18
Nodes (10): Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record() (+2 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.14
Nodes (25): _download(), _fetch(), forget_missing(), _from_steam(), _from_steamgriddb(), _get(), _json(), lookup() (+17 more)

### Community 9 - "VideoSettings"
Cohesion: 0.33
Nodes (4): VideoSettings, Salvar as preferências não pode apagar chaves silenciosamente.      ``set_video_, Uma instalação antiga não pode ficar sem HUD nem quebrar ao salvar., VideoSettingsRoundTripTests

### Community 10 - "Lume no Windows"
Cohesion: 0.05
Nodes (40): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, Abrir de outro aparelho, As três faixas de áudio (+32 more)

### Community 11 - "SilentTrackTests"
Cohesion: 0.27
Nodes (4): O sinal de atividade tem um significado só, e ele é caro de errar.      Enquanto, Dois marcadores seguidos têm o mesmo rótulo; só a sequência os separa., O pedido da interface só encerra com a contagem já correndo., VideoActivityFlagTests

### Community 12 - "test_services.py"
Cohesion: 0.07
Nodes (20): ClipAudioTrackTests, HoldDetectorTests, HudDisplayModeTests, LinuxAudioTapTests, ObsMicFilterTests, Um app com vários streams tem de entrar inteiro na faixa de sistema.      O ``pw, c1 e c2 não podem carregar a mesma voz, nem o mesmo som duas vezes., Fora do jogo o aviso da contagem reabria a HUD em qualquer modo.          No Lin (+12 more)

### Community 13 - "ActionResult"
Cohesion: 0.12
Nodes (4): O vocabulário de tags: normalização, quarentena, fusão e promoção., Substitui o daemon: devolve uma escolha por estado, na ordem pedida., A quarentena governa o vocabulário, não a memória: nada se perde., TagVocabularyTests

### Community 14 - "WindowsServiceManager"
Cohesion: 0.17
Nodes (5): Supervisor: mantém os processos de captura vivos e agenda o processamento., Anota que a captura deve (ou não) voltar na próxima abertura do Lume.          N, Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., Combine selective-video and user-idle pauses without racing them.          Audio, WindowsServiceManager

### Community 15 - "game-video-loop"
Cohesion: 0.10
Nodes (42): game-video-loop script, absorb_pending_clip(), active_monitor(), add_long_marker(), add_marker(), adopt_video(), begin_game_session(), clean_mic_track() (+34 more)

### Community 16 - "runtime_dir"
Cohesion: 0.12
Nodes (19): Path, Helpers de runtime que funcionam igual em Linux e Windows.  Centraliza as poucas, Diretório para arquivos efêmeros (locks, estado volátil).      Linux usa ``XDG_R, Arquivo que sinaliza "estou gravando vídeo agora".      É como o laço de vídeo p, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Pedido da interface para encerrar já a sessão que está na contagem.      Só vale, runtime_dir(), video_activity_flag() (+11 more)

### Community 18 - "RemapToSourceTests"
Cohesion: 0.33
Nodes (3): Voltar os tempos do bloco para o eixo do áudio original.      É a parte que, err, Fim antes do início quebraria a ordenação e a legenda., RemapToSourceTests

### Community 19 - "get"
Cohesion: 0.11
Nodes (31): active_vocabulary(), apply_tags(), canonicalize(), clean_label(), create(), _describe(), _enforce_cap(), listing() (+23 more)

### Community 20 - "main.py"
Cohesion: 0.05
Nodes (71): atomic_write(), capture_action(), capture_days(), capture_speed_stats(), CleanupSettings, _confirmation_sounds(), ContextUpdate, create_tag() (+63 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.10
Nodes (26): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+18 more)

### Community 24 - "capture-frame"
Cohesion: 0.27
Nodes (6): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), KDE_SESSION_VERSION, usage()

### Community 25 - "hud.py"
Cohesion: 0.10
Nodes (10): ModoLuminiTests, O Lumini é a mesma base instalada só como gravador.      Sem estes testes, a ins, Atualizar o Lume não pode desligar a análise de quem a tem., O modo precisa valer para todo processo da máquina.          São quatro que prec, Experimentar o Lumini não pode exigir editar a instalação., Um erro de digitação não pode mutilar a interface de ninguém., Sem isso a interface adivinha, e mostra botões de IA a quem não tem., Um prefixo desatento na tabela derrubaria a biblioteca de clipes. (+2 more)

### Community 27 - "WasapiError"
Cohesion: 0.19
Nodes (14): available(), Choice, choose(), LayaUnavailable, RuntimeError, Cliente do daemon do Laya — classificação de texto por vocabulário fechado.  O `, Uma pergunta de múltipla escolha para cada estado, num único lote.      ``criter, Onde o daemon escuta. No Windows não há socket UNIX — devolve vazio. (+6 more)

### Community 29 - "Path"
Cohesion: 0.10
Nodes (30): apply_confirmation_sound_preset(), _apply_storage_runtime(), _apply_video_runtime(), atomic_write_if_changed(), AudioSettings, _config_int(), get_audio_settings(), get_storage_settings() (+22 more)

### Community 30 - "editing.py"
Cohesion: 0.11
Nodes (34): available_name(), chapter_seconds(), clip_markers(), EditingError, entries(), folder(), frames_to_timecode(), inside_folder() (+26 more)

### Community 31 - "audio-bus.sh"
Cohesion: 0.20
Nodes (20): discord(), ensure(), link_ports(), make_null_sink(), mic_feed(), selected_mic(), setup(), audio-bus.sh script (+12 more)

### Community 32 - "src-backup-2026-08-09/api.ts"
Cohesion: 0.07
Nodes (26): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+18 more)

### Community 33 - "src-backup-2026-08-09/main.tsx"
Cohesion: 0.10
Nodes (5): EditableVideoSpeaker, icons, labels, Panel, View

### Community 34 - "pipeline.py"
Cohesion: 0.13
Nodes (15): dbfs(), default_endpoint_name(), Nome do endpoint padrão, ou ``None`` se não houver nenhum., Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), main(), _mix(), _multichannel() (+7 more)

### Community 35 - "_call"
Cohesion: 0.18
Nodes (20): _AudioClientActivationParams, _Blob, _call(), _check(), _device_enumerator(), ensure_com(), _friendly_name(), _LazyOle32 (+12 more)

### Community 37 - "_JobObject"
Cohesion: 0.13
Nodes (9): HotkeyChordTests, WindowsBracketTests, log(), MarkerHotkey, MSG, Atalhos globais no Windows, registrados fora de qualquer janela.  No Linux o ata, Espera o desfecho da tecla e diz se foi toque ou segurada.          Bloquear a f, Descarta as repetições enfileiradas enquanto a tecla esteve abaixada. (+1 more)

### Community 38 - "run"
Cohesion: 0.06
Nodes (65): connect(), row_dict(), _audio_channels(), backfill_confirmed_voice_observations(), backfill_video_session_durations(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item() (+57 more)

### Community 39 - "connect"
Cohesion: 0.15
Nodes (10): HotkeyDaemon, keyboard_devices(), log(), main(), Consome um evento de tecla (0 solta, 1 pressiona, 2 repete)., Deixa a segurada vencer mesmo sem evento novo chegando., Teclados vistos pelo kernel, sem duplicar o mesmo ``eventN``.      ``by-path`` l, Reconhece a combinação inteira antes de iniciar um toque ou segurada. (+2 more)

### Community 43 - "prompts.py"
Cohesion: 0.07
Nodes (22): get_prompts(), reset_prompt(), active_template(), listing(), _overrides(), payload(), PromptError, PromptSpec (+14 more)

### Community 45 - "winrecord.py"
Cohesion: 0.24
Nodes (13): _as_float(), _as_ratio(), host_catalog(), _link_dict(), links_for(), probe_video_shape(), Mandar um clipe para alguém: nome legível, versão leve e link público.  O gravad, Andamento do envio deste clipe, mais os links que ele já ganhou. (+5 more)

### Community 46 - "SpeechRegionTests"
Cohesion: 0.36
Nodes (5): Trechos ``(início, fim)`` em segundos onde há som acima do limiar.      Função p, speech_regions(), Detecção dos trechos com som, sobre amostras sintéticas., A folga não pode gerar tempo negativo nem passar do fim do áudio., SpeechRegionTests

### Community 47 - ".snapshot"
Cohesion: 0.06
Nodes (38): Não sei que janela é essa" não é "o usuário saiu do jogo".          ``GetForegro, parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., concat_videos(), cut_head(), foreground_details(), log(), looks_blank() (+30 more)

### Community 48 - "get_manager"
Cohesion: 0.12
Nodes (13): Host, MultipartBody, RuntimeError, Sobe o arquivo fora da requisição HTTP, com progresso e cancelamento., O envio foi interrompido a pedido de quem o começou., Um lugar onde o arquivo pode ser publicado, sem conta e sem login., A resposta é a URL em texto puro — e o erro também vem como HTTP 200.          P, Corpo multipart que lê o arquivo em blocos e sabe o próprio tamanho.      O tama (+5 more)

### Community 49 - "CallMetricsTests"
Cohesion: 0.27
Nodes (4): CallMetricsTests, Sem separar carga, leitura do prompt e geracao, encurtar prompt e chute., ollama_json repete a chamada para consertar JSON; isso custa tempo., Um audio nao passa pelo Ollama; herdar a medicao de uma tela mentiria.

### Community 50 - "resolve_media_source"
Cohesion: 0.23
Nodes (14): audio_mix(), light_state(), load_audio_mix(), _mix_tag(), Path, Volumes salvos no player, por posição da faixa de áudio (``0:a:N``)., A mixagem a aplicar no envio, ou ``None`` quando nada foi mexido.      Tudo em 1, O teto e a receita ficam **fora** do hash, de propósito.      Assim a limpeza de (+6 more)

### Community 51 - "RegionGroupingTests"
Cohesion: 0.31
Nodes (5): group_regions(), Agrupa trechos vizinhos em blocos que caibam numa janela do whisper.      Dois t, Blocos que enchem uma janela do whisper sem esticar o eixo do tempo.      O whis, É o teto que impede um erro de 1 s virar 20 s ao voltar ao original., RegionGroupingTests

### Community 52 - "Path"
Cohesion: 0.11
Nodes (6): Achar o clipe e mandar para alguém.      O gravador nomeia por data, então o que, Pedir 63 Mbps de um vídeo gravado a 2,3 gastaria CPU para nada., O arquivo tem quatro faixas: mixagem, microfone, Discord e sistema.          Lev, Para sempre" é decisão de quem publica, não do código., Mandar arquivo para fora só acontece pelo caminho que pede confirmação., SharingTests

### Community 53 - "ServiceManager"
Cohesion: 0.10
Nodes (12): ABC, Executa ``start``/``stop``/``restart``/``try-restart``/``enable``/``disable``., Horário configurado do processamento noturno e se está ativo., Reprograma o processamento noturno., Dispara um job avulso sob um nome de unit, para poder cancelá-lo depois., Reinicia a própria interface (usado ao trocar o local dos dados)., Chamado quando a API sobe., Chamado quando a API desce. (+4 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.04
Nodes (31): ConfirmationSounds, EditingFolder, HotkeyInput(), CAPTION_LABELS, CAPTION_ORDER, CapturaTab, ConfirmationSounds(), ContextMenuAction (+23 more)

### Community 55 - "App"
Cohesion: 0.11
Nodes (19): AudioSettings, Capture, CleanupSettings, PipelineQueue, ScreenSequenceResult, Status, uploadVideo(), VideoSettings (+11 more)

### Community 56 - "videoTime"
Cohesion: 0.13
Nodes (17): AudioAnalysis(), ChapterReader(), chapterStart(), clipClock(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SessionCard() (+9 more)

### Community 57 - "_video_pause_file"
Cohesion: 0.14
Nodes (15): blend(), EventFrame, HudPanel, Mistura duas cores ``#rrggbb``.      O Canvas do tkinter não tem canal alfa por, Um quadro da animação de confirmação.      ``reveal`` é o quanto o evento tomou, Um painel desenhado num monitor., Corta pela largura real do texto, não por contagem de caracteres.          A HUD, Barra mínima. O evento entra por baixo empurrando o conteúdo normal.          Nã (+7 more)

### Community 58 - "WasapiCapture"
Cohesion: 0.16
Nodes (9): Blocos que não caem em fronteira redonda não podem perder amostras., ResamplerTests, _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers.      M, Um fluxo de captura: microfone padrão ou loopback da saída padrão.      A saída, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio).          Um, WasapiCapture (+1 more)

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "trim_video"
Cohesion: 0.13
Nodes (20): audio_file(), _audio_streams(), delete_voice_identity(), import_video(), mic_level(), promote_tags(), datetime, Pico do microfone cru (sem denoise/portão) numa janela curta.      A interface f (+12 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 64 - "HudStateTests"
Cohesion: 0.13
Nodes (14): HudStateTests, As regras que decidem se a captura está saudável.      Rodam nos dois sistemas d, Segurou o atalho: já não é "armado", é gravando de verdade., Ficar calado é normal; confundir com falha destrói a confiança na HUD., _disk_alerts(), evaluate(), Meter, _meter_alerts() (+6 more)

### Community 65 - "local_origin_only"
Cohesion: 0.22
Nodes (14): begin(), close_stale(), _ensure_schema(), finish(), heartbeat(), iso_time(), main(), Contagem de tempo por jogo, independente do que foi gravado.  O tempo de jogo é (+6 more)

### Community 67 - "VideoWindowTest"
Cohesion: 0.26
Nodes (6): test_video_window(), VideoWindowTest, AudioSettingsTests, O teste de janela do Lume precisa responder o mesmo que o gravador.      Se ele, Adicionar um jogo usa a resolução do monitor dele, não 1920x1080 fixo., VideoWindowTestEndpointTests

### Community 68 - "HudPlacementTests"
Cohesion: 0.23
Nodes (6): HudPlacementTests, Onde a HUD desenha, dado o arranjo de monitores., Com um monitor só, "no outro monitor" tem que recair sobre este., choose_monitors(), corner_position(), Monitores que devem receber um painel.      Função pura para poder ser testada s

### Community 69 - "PromptSettingsTests"
Cohesion: 0.13
Nodes (4): PromptSettingsTests, Os prompts sao editaveis, mas nao a ponto de quebrar a analise., Uma variavel esquecida na ficha sumiria do texto sem ninguem notar., Um JSON quebrado nao pode parar a fila inteira.

### Community 72 - "capture_frames"
Cohesion: 0.20
Nodes (9): 1. Atividades por assunto, com agrupamento por aplicativo como apoio, 2. Contexto completo e verificável em resumos e vídeos, 3. Captura e fila: preservar o lugar de onde a pessoa veio, 4. Vídeos, áudio e busca: acesso consistente às evidências, 5. Ajustes, calendário e acessibilidade, Melhorias aplicadas nesta revisão, Revisão das demais áreas e prioridades, Revisão do Lume — experiência e contexto da IA (+1 more)

### Community 74 - "EditingFolderTests"
Cohesion: 0.11
Nodes (5): EditingFolderTests, A pasta de edicao troca garimpo de arquivo por nome legivel e EDL., 12,5 s a 60 fps sao 750 quadros depois do inicio da timeline., O hardlink segura os bytes, entao apagar por engano so confundiria., O segundo trecho comeca onde o primeiro acaba, e o EDL acompanha.

### Community 75 - "hudsource.py"
Cohesion: 0.18
Nodes (4): LinuxIdlePauseTests, _pausable(), Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)., SupervisorTests

### Community 76 - "_Growth"
Cohesion: 0.38
Nodes (6): ActivitiesView(), ActivityCard(), Frame, searchable(), time(), ActivitySession

### Community 77 - "Path"
Cohesion: 0.25
Nodes (11): capture_change_test_frames(), capture_frames(), compare_screen_change_test(), get_screen_settings(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver.      A mesma regra nos doi, Captura um conjunto de frames com a configuração atual., screen_change_percent() (+3 more)

### Community 78 - "multimodal_context"
Cohesion: 0.08
Nodes (27): cancel_light_version(), cancel_update(), cancel_upload(), cancel_video_audio_track_jobs(), download_video(), game_icon_file(), get_video_audio_mix(), lifespan() (+19 more)

### Community 79 - "Path"
Cohesion: 0.28
Nodes (7): Decision, _merge_ready(), Pergunta ao Laya quais propostas são sinônimo de alguma tag ativa., Última checagem semântica antes de ativar: o vocabulário pode ter crescido., O caminho que uma string bruta percorreu até virar (ou não) uma tag., Resolution, _resolve_with_laya()

### Community 80 - "LinuxAppRuleMatchTests"
Cohesion: 0.07
Nodes (17): KdotoolSessionVersionTests, LinuxAudioTrackTests, PrivacyTests, Gravação em faixas separadas (3 canais) no backend Linux., Sem audio.conf, o microfone ainda ganha o tratamento padrão., A calibração precisa do sinal cru: filtrado, o silêncio de fundo         sempre, O dshow corta nomes longos: casa pelo prefixo do nome do WASAPI., O kdotool 0.3 sai com erro sem ``KDE_SESSION_VERSION=6``.      As units do syste (+9 more)

### Community 82 - "context_overflow"
Cohesion: 0.67
Nodes (5): dateOf(), DayPicker(), fullLabel(), MemoryDay, monthLabel()

### Community 83 - "._start"
Cohesion: 0.22
Nodes (7): _JobObject, _pipeline(), _python(), Gerenciamento de serviços independente de sistema operacional.  No Linux o syste, Amarra os processos filhos ao ciclo de vida da API.      É o que o systemd conse, Return seconds since the last real keyboard or mouse input on Windows., windows_idle_seconds()

### Community 84 - "test_main.py"
Cohesion: 0.22
Nodes (10): get_schedule(), process_video_session_job(), Conciliação sem gravar nada: mostra o caminho de cada string até a tag., ScheduleSettings, set_schedule(), status(), TagTestRequest, test_tags() (+2 more)

### Community 85 - "get_backend"
Cohesion: 0.29
Nodes (9): initialize(), _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., detach_video_from_session(), Retira um trecho da sessão sem apagar o vídeo nem sua análise., Connection (+1 more)

### Community 86 - ".snapshot"
Cohesion: 0.24
Nodes (8): _app_label(), _elapsed(), _focus_grace_remaining(), _long_elapsed(), Lê o sinal JSON que o ``winvideo`` reescreve a cada volta do laço.      Um arqui, Há quanto tempo a gravação longa corre, ou zero se não há nenhuma., Nome curto do app a partir de ``"<título> | <executável>"``., _read_video_flag()

### Community 87 - "filter_hallucinated_segments"
Cohesion: 0.16
Nodes (4): SystemdServiceManager, Pausar desabilita a unit: só parar valia até o próximo boot., Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API., SystemdFallbackTests

### Community 88 - "hudsource.py"
Cohesion: 0.14
Nodes (14): LinuxCaptureModeTests, LinuxFocusVerdictTests, O modo da regra vale no Linux, com o gravador de verdade rodando.      ``[clips], O gravador de jogo não pode depender da captura de áudio estar de pé.          O, O VCE de uma RX 550 derrubou a GPU inteira ("ring vce0 timeout").          Em Po, Um gravador que morre ao subir não pode virar um laço invisível.          Era as, Clipar duas vezes seguidas descreve um trecho só, não dois.          Com clipes, Sem sobreposição não há o que mesclar: são duas jogadas distintas. (+6 more)

### Community 89 - "media_source_key"
Cohesion: 0.06
Nodes (21): ImageDiffTests, MonitorResolutionTests, Variação de 5 níveis é ruído de compressão, não mudança de tela., A resolução sugerida para um jogo novo é a física, não a lógica., Com ``dmSize`` errado o EnumDisplaySettingsW recusa a chamada.          No Windo, Monitor, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável. (+13 more)

### Community 90 - ".grab_frame"
Cohesion: 0.09
Nodes (40): get_cleanup_settings(), _activity_batch_summary(), adaptive_web_research(), analyze_screen_sequence(), context_overflow(), days_pending_consolidation(), describe_tag_candidates(), discover() (+32 more)

### Community 91 - "WasapiError"
Cohesion: 0.18
Nodes (5): _ActivationHandler, GUID, ProcessLoopbackCapture, Implementação mínima de IActivateAudioInterfaceCompletionHandler., Loopback que inclui ou exclui a árvore de um processo do Windows.

### Community 92 - "context_overflow"
Cohesion: 0.26
Nodes (21): update_status(), exclusive_lock(), Trava exclusiva e não-bloqueante sobre ``path``.      Retorna ``True`` se conseg, apply_pending(), can_install_now(), cancel(), check(), check_compatible() (+13 more)

### Community 93 - "_LazyOle32"
Cohesion: 0.12
Nodes (12): api, TagDecision, TagEntry, TagPromotion, TagStatus, TagTestResult, TagVocabulary, OUTCOME (+4 more)

### Community 94 - "HoldDetectorTests"
Cohesion: 0.20
Nodes (6): Laço só com o estado que o caminho dos clipes usa., O clipe espera fora do buffer; ao ser publicado leva os sidecars.          Publi, Dois atalhos em menos de um clipe descrevem um trecho só.          Com clipes de, Clipe e gravação longa logo depois: um arquivo só, sem trecho repetido., Sem sobreposição não há o que mesclar: são duas jogadas distintas., VideoReplayClipTests

### Community 97 - "winscreen.py"
Cohesion: 0.40
Nodes (3): MediaFreshnessTests, As URLs de mídia têm de mudar quando o arquivo muda.      O corte reescreve o ví, Um clipe apagado entre a listagem e a montagem da URL não é erro 500.

### Community 98 - "services.py"
Cohesion: 0.27
Nodes (5): Uma unit supervisionada.      ``simple`` roda enquanto o serviço estiver ligado, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef, UnitResolutionTests

### Community 99 - ".active"
Cohesion: 0.18
Nodes (8): _LightVersionJob, progress_percent(), prune_share_cache(), Popen, Lê ``out_time_us=12500000`` do ``-progress`` e devolve 21 num clipe de 60s., Segura o tamanho do cache: são arquivos de dezenas de MB.      Nada no Lume apag, Recodifica fora da requisição HTTP, com progresso e cancelamento.      Mesmo mol, Lê o ``-progress`` numa thread só sua.          A leitura de pipe bloqueia, e o

### Community 100 - "devDependencies"
Cohesion: 0.13
Nodes (14): dependencies, react, react-dom, name, private, scripts, build, dev (+6 more)

### Community 101 - "hudsource.py"
Cohesion: 0.20
Nodes (17): apply_preset(), clear_custom(), custom_sound(), default_sound(), play(), playable_wav(), prepare(), presets() (+9 more)

### Community 102 - "_LazyOle32"
Cohesion: 0.20
Nodes (4): _chunks(), ConfirmationSoundTests, Sons do atalho: o arquivo enviado substitui o padrão, e remover o devolve., O winsound só toca WAV e não tem volume: a conversão cuida dos dois.

### Community 104 - ".feed"
Cohesion: 0.08
Nodes (21): apply_exact_game_durations(), daily_narrative_target(), game_activity_rows(), private_context_terms(), Sessões monitoradas recortadas ao dia local, inclusive ao cruzar meia-noite., Substitui estimativas da IA pelos intervalos medidos pelo contador da sidebar., Memórias do dia, representando cada sessão de vídeo apenas uma vez., Valida referências da IA e protege os arquivos escolhidos. (+13 more)

### Community 105 - "read_shell_config"
Cohesion: 0.21
Nodes (12): health(), install_update_now(), _do_arquivo(), e_lumini(), modo_atual(), Em qual modo esta instalação foi montada.  O Lume completo grava, transcreve, de, Lê ``LUME_MODE`` do ``lume.conf``, sem depender do resto do backend.      Parse, O modo em vigor. Sem cache, de propósito.      O arquivo tem uma linha, e ``/api (+4 more)

### Community 106 - ".test_an_unreadable_foreground_window_neither_starts_nor_advances_the_countdown"
Cohesion: 0.15
Nodes (14): bounded_video_range(), local_origin_only(), origin_allowed(), Se este caminho só faz sentido com o pipeline instalado., No Lumini, o que depende de IA responde 409 em vez de tentar.      Esconder os b, Se o ``Host`` (ou a origem) descreve este servidor.      Além dos nomes configur, Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., recusar_analise_no_lumini() (+6 more)

### Community 108 - "multimodal_context"
Cohesion: 0.20
Nodes (7): get_collector(), HudCollector, ABC, Fonte do instantâneo da HUD., Sobe threads de coleta (no-op quando não houver)., Estado atual, já normalizado., Coletor do SO atual, na mesma convenção de :func:`app.capture.get_backend`.

### Community 110 - ".action"
Cohesion: 0.14
Nodes (8): _Process, Path, Popen, Arquivo de estado que o laço de vídeo cria enquanto controla as capturas.      M, (Re)inicia o swayidle apontando os eventos para o flag de idle., Um processo filho supervisionado., _unknown(), _video_pause_file()

### Community 111 - "matched_sensitive_pattern"
Cohesion: 0.38
Nodes (7): enroll_voice_identity(), _normalized_average(), Recalcula um perfil dando um único voto a cada gravação., rebuild_voice_identity(), SpeakerLabelUpdate, update_capture_speaker(), update_video_speaker()

### Community 113 - "rebuild_voice_identity"
Cohesion: 0.27
Nodes (10): light_video_file(), Baixa a versão leve pronta; 409 enquanto ela não existir.      Não gera nada aqu, light_filename(), normalized_limit(), Publica o clipe num host grátis, **só com confirmação explícita**.      A trava, O teto entra no nome: duas versões do mesmo clipe não se confundem., Falha que o usuário precisa ler, não um defeito interno., resolve_host() (+2 more)

### Community 115 - "delete_voice_identity"
Cohesion: 0.07
Nodes (42): cancel_video_audio_track_job(), cancel_video_audio_tracks(), _delete_media_sidecars(), delete_video(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), media_url() (+34 more)

### Community 116 - "HudStatus"
Cohesion: 0.05
Nodes (38): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., _alert_sound(), _assert_topmost(), _declare_dpi_aware() (+30 more)

### Community 117 - ".feed"
Cohesion: 0.29
Nodes (3): _FakeResponse, O host recusa com HTTP 200 e um texto no corpo; engolir isso deixaria         a, Resposta de host de arquivo: corpo em texto puro, sem rede envolvida.

### Community 118 - "LinuxAudioTapTests"
Cohesion: 0.16
Nodes (6): LinuxCleanMicTests, Path, Supressão por IA antes do MicBus: liga, desliga e nunca deixa a faixa muda., Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., O formato do ``input_event`` é contrato do kernel, não detalhe nosso.          E, VideoSettingsTests

### Community 120 - "._partial_segment"
Cohesion: 0.22
Nodes (4): _Growth, _MeterTracker, Contabilidade temporal de uma fonte de áudio.      Guarda desde quando a fonte n, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo).

### Community 121 - "multimodal_context"
Cohesion: 0.31
Nodes (5): HudEventContractTests, O evento cruza dois processos por um arquivo; o formato é um contrato.      O ``, Um tipo sem estilo seria um evento invisível — falha silenciosa., _event_fields(), Extrai o acontecimento pontual publicado pelo laço de vídeo.      A idade vem do

### Community 124 - "test_updater.py"
Cohesion: 0.25
Nodes (6): light_video_command(), A receita que cabe no teto: quanto bitrate, em que tamanho de imagem., Bitrate que cabe no teto, e o tamanho de imagem que esse bitrate aguenta.      R, Recodificação que cabe no teto e serve para ser assistida por outra pessoa., share_plan(), SharePlan

### Community 125 - "stop_target_is_already_gone"
Cohesion: 0.29
Nodes (3): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas.

### Community 126 - "exige"
Cohesion: 1.00
Nodes (3): exige(), instalar-lumini.sh script, tem()

### Community 127 - "devDependencies"
Cohesion: 0.18
Nodes (11): devDependencies, playwright, @types/react, @types/react-dom, typescript, vite, playwright, @types/react (+3 more)

### Community 128 - "get_backend"
Cohesion: 0.25
Nodes (3): LinuxHudCollector, Estado derivado do laço bash e medidores lidos dos buses do PipeWire.      O ``b, Janela em foco, com a mesma cadência do laço bash (2 s).          O sidecar ``.w

### Community 129 - "share_stem"
Cohesion: 0.29
Nodes (7): _clip_row(), download_filename(), ``2026-09-26 00-10 Sea of Thieves — trecho 02 de 05``, sem extensão.      Vale p, Nome oferecido no download, com a extensão do arquivo original., Posição do trecho na sessão, na mesma ordem que a pasta de edição usa.      Uma, _session_position(), share_stem()

### Community 130 - "_activity_groups"
Cohesion: 0.38
Nodes (4): ObsWindowSpecTests, O identificador de janela do OBS é ``título:classe:executável``.      Um título, _encode_field(), Escapa um campo do identificador de janela do OBS.      O identificador é ``títu

### Community 131 - ".test_a_summary_older_than_its_own_memories_is_redone"
Cohesion: 0.33
Nodes (6): _attached_source(), log(), _pulse_sources(), Lê PCM cru do monitor de um bus e acumula o pico.          Taxa baixa e um canal, Mapa id -> nome das fontes do PipeWire/Pulse., Fonte à qual o ``parec`` de ``client`` está realmente ligado.      Existe porque

### Community 132 - "UpdateNotice.tsx"
Cohesion: 0.67
Nodes (3): request(), UpdateNotice(), UpdateStatus

### Community 134 - "GUID"
Cohesion: 0.33
Nodes (3): parse_json_response(), Recupera JSON que o parser do Ollama classificou todo como thinking., recover_json_from_thinking()

### Community 135 - "_devmode_w"
Cohesion: 0.40
Nodes (4): _devmode_w(), _monitor_info_ex(), MONITORINFOEXW: o ``szDevice`` é o nome que o EnumDisplaySettings pede., DEVMODEW com a união de impressora/monitor como 16 bytes opacos.      Só ``dmPel

### Community 136 - "delete_voice_identity"
Cohesion: 0.33
Nodes (3): HudFrameRateTests, As três cadências existem por causa do custo de redesenhar.      Cada volta recr, Uma entrada de 0,26 s precisa de quadros suficientes para não escadear.

### Community 138 - "ValueError"
Cohesion: 0.29
Nodes (7): cached_file(), _ico_to_png(), Path, Caminho de um ícone já baixado; só nomes gerados aqui são aceitos., Converte um ``.ico`` na sua maior imagem, em PNG.      Muitos jogos só têm ícone, set_status(), ValueError

### Community 139 - ".active_monitor"
Cohesion: 0.33
Nodes (5): _count_markers(), Path, Segmento sendo escrito agora pelo ``gpu-screen-recorder``., Há quanto tempo o segmento em curso começou.      Vem do nome do arquivo, não do, _segment_elapsed()

### Community 140 - "_scaled_size"
Cohesion: 0.50
Nodes (4): forget_shared_link(), Tira o link da lista. O arquivo continua no ar — o host é que o apaga., forget_link(), Esquece o link. Não o despublica — e a interface diz isso em voz alta.

### Community 141 - "context_overflow"
Cohesion: 0.50
Nodes (3): Oferecer "processar" numa máquina sem Ollama é oferecer uma falha., Nomes de unit que o supervisor do Windows oferece naquele modo.      Em subproce, _units_do_supervisor()

### Community 143 - ".test_capture_target_does_not_pull_a_disabled_capture"
Cohesion: 0.31
Nodes (4): O microfone dos vídeos recebe a supressão e o volume mínimo da interface.      N, Ligada, a supressão atenua um chiado constante que o portão deixaria passar., Vídeo que chega ao buffer sem passar pela limpeza sai com o mic cru., VideoMicCleanupTests

## Knowledge Gaps
- **144 isolated node(s):** `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame`, `StorageCandidate`, `WebSource` (+139 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `main.py` to `ConfigTests`, `_activity_groups`, `LinuxCaptureBackend`, `delete_voice_identity`, `VideoSettings`, `validate_relevant_media`, `SilentTrackTests`, `test_services.py`, `ActionResult`, `WindowsServiceManager`, `.test_capture_target_does_not_pull_a_disabled_capture`, `runtime_dir`, `RemapToSourceTests`, `hud.py`, `Path`, `run`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `Path`, `ServiceManager`, `WasapiCapture`, `HudPanel`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `hudsource.py`, `Path`, `multimodal_context`, `LinuxAppRuleMatchTests`, `._start`, `test_main.py`, `filter_hallucinated_segments`, `hudsource.py`, `media_source_key`, `HoldDetectorTests`, `winscreen.py`, `services.py`, `_LazyOle32`, `.feed`, `matched_sensitive_pattern`, `delete_voice_identity`, `HudStatus`, `.feed`, `LinuxAudioTapTests`, `multimodal_context`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `package.json`, `VideoWindowTest`, `GUID`, `patch`, `.feed`, `VideoSettings`, `.test_an_unreadable_foreground_window_neither_starts_nor_advances_the_countdown`, `main.py`, `audio_intelligence.py`, `filter_hallucinated_segments`, `.grab_frame`, `stop_target_is_already_gone`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `filter_hallucinated_segments` to `ConfigTests`, `_activity_groups`, `LinuxCaptureBackend`, `delete_voice_identity`, `VideoSettings`, `validate_relevant_media`, `SilentTrackTests`, `test_services.py`, `ActionResult`, `.test_capture_target_does_not_pull_a_disabled_capture`, `runtime_dir`, `RemapToSourceTests`, `hud.py`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `Path`, `ServiceManager`, `WasapiCapture`, `HudPanel`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `hudsource.py`, `LinuxAppRuleMatchTests`, `._start`, `test_main.py`, `hudsource.py`, `media_source_key`, `HoldDetectorTests`, `winscreen.py`, `services.py`, `_LazyOle32`, `.feed`, `.action`, `HudStatus`, `.feed`, `LinuxAudioTapTests`, `multimodal_context`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `VideoWindowTest`) actually correct?**
  _`ConfigTests` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 84 inferred relationships involving `ActionResult` (e.g. with `AudioSettings` and `CleanupSettings`) actually correct?**
  _`ActionResult` has 84 INFERRED edges - model-reasoned connections that need verification._
- **Are the 43 inferred relationships involving `VideoLoop` (e.g. with `ClipAudioTrackTests` and `HoldDetectorTests`) actually correct?**
  _`VideoLoop` has 43 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` to the rest of the system?**
  _144 weakly-connected nodes found - possible documentation gaps or missing edges._