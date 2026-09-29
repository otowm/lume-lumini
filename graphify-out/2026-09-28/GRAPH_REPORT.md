# Graph Report - lume  (2026-09-28)

## Corpus Check
- 83 files · ~159,793 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2606 nodes · 6180 edges · 157 communities (127 shown, 30 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 628 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `5d5ee736`
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
- safe_research_query
- .active_monitor
- test_updater.py
- .read
- .test_a_summary_older_than_its_own_memories_is_redone
- UpdateNotice.tsx
- .test_nome_do_download_usa_o_jogo_do_sidecar_quando_a_ia_ainda_nao_titulou
- .test_nome_de_trecho_de_sessao_diz_qual_pedaco_e
- .test_nome_da_sessao_igual_ao_jogo_nao_entra_duas_vezes
- .test_clipe_sem_jogo_e_sem_titulo_mantem_o_nome_do_arquivo
- .test_nome_da_versao_leve_diz_o_teto
- .test_versao_leve_mantem_somente_a_faixa_de_mixagem
- .test_versao_leve_mais_antiga_que_o_original_e_descartada
- .test_upload_sem_confirmacao_explicita_e_recusado
- .test_link_fica_salvo_para_recopiar_depois
- .test_bash_loop_counts_game_time_through_the_shared_cli
- .test_capture_target_does_not_pull_a_disabled_capture
- .test_opus_stems_go_to_a_container_that_accepts_them
- .test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis
- .test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time
- .test_recording_keeps_the_mix_ahead_of_the_isolated_tracks
- .test_stale_game_session_is_closed_at_the_last_heartbeat
- .test_end_video_session_only_during_the_focus_countdown
- LightVersion
- _event_fields
- selftest.py
- forget_shared_link
- _kdotool_env
- .test_an_unreadable_foreground_window_neither_starts_nor_advances_the_countdown

## God Nodes (most connected - your core abstractions)
1. `ConfigTests` - 121 edges
2. `connect()` - 118 edges
3. `ActionResult` - 116 edges
4. `VideoLoop` - 80 edges
5. `SystemdServiceManager` - 74 edges
6. `HudSnapshot` - 67 edges
7. `Monitor` - 61 edges
8. `Hud` - 59 edges
9. `Meter` - 57 edges
10. `WindowsCaptureBackend` - 57 edges

## Surprising Connections (you probably didn't know these)
- `apply_pending()` --references--> `scripts`  [EXTRACTED]
  app/backend/updater.py → frontend/package.json
- `remove_alias()` --calls--> `connect()`  [EXTRACTED]
  app/backend/tags.py → app/backend/database.py
- `ScreenSettings` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `AudioSettings` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `SensitiveWindows` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py

## Import Cycles
- None detected.

## Communities (157 total, 30 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.04
Nodes (17): captured_video_session(), Lê a identidade portátil deixada pelo gravador seletivo.      Vídeos antigos só, Estado operacional do gravador, separado da mera configuração ativa., selective_video_status(), ConfigTests, Path, O laço do Linux conta tempo pela mesma porta que o gravador do Windows., Uma queda no meio da partida não pode contar o tempo até agora. (+9 more)

### Community 1 - "src/api.ts"
Cohesion: 0.05
Nodes (41): ActivityFrame, AnalysisTrace, AppMode, AudioEvent, ConfirmationSound, DaySummary, EditingEntry, EditingResult (+33 more)

### Community 2 - "package.json"
Cohesion: 0.12
Nodes (47): _activity_image(), analyze_screen_sequence(), analyze_video_chapter(), audio_channel_count(), audio_stream_count(), clear_call_metrics(), compact_processed_audio(), compact_saved_capture() (+39 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "LinuxCaptureBackend"
Cohesion: 0.08
Nodes (17): CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco.          Retorna ``N, Por que ``active_window`` falhou, numa frase para a interface., Monitores habilitados, em ordem estável de índice., Prepara o roteamento de áudio (no-op onde não for necessário). (+9 more)

### Community 5 - "obs.py"
Cohesion: 0.21
Nodes (16): any_fullscreen(), call(), ensure_scene(), Instância dedicada do OBS para a gravação de jogos no Windows.  No Linux a grava, Uma requisição ao OBS dedicado.      Cada chamada abre e fecha a conexão. É deli, Garante a cena com Game Capture, som do sistema e microfone.      Devolve ``True, Ativa uma das fontes visuais da cena sem recriá-la durante a sessão., Aponta o Game Capture para um app específico, casando pelo executável.      O mo (+8 more)

### Community 6 - "record"
Cohesion: 0.11
Nodes (19): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., main(), _mix(), _multichannel(), array, Path, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.  Gr (+11 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.12
Nodes (30): cached_file(), _download(), _fetch(), forget_missing(), _from_steam(), _from_steamgriddb(), _get(), _ico_to_png() (+22 more)

### Community 9 - "VideoSettings"
Cohesion: 0.33
Nodes (4): VideoSettings, Salvar as preferências não pode apagar chaves silenciosamente.      ``set_video_, Uma instalação antiga não pode ficar sem HUD nem quebrar ao salvar., VideoSettingsRoundTripTests

### Community 10 - "Lume no Windows"
Cohesion: 0.05
Nodes (40): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, Abrir de outro aparelho, As três faixas de áudio (+32 more)

### Community 11 - "SilentTrackTests"
Cohesion: 0.05
Nodes (23): LinuxCaptureModeTests, Path, O gravador de jogo não pode depender da captura de áudio estar de pé.          O, O VCE de uma RX 550 derrubou a GPU inteira ("ring vce0 timeout").          Em Po, Um gravador que morre ao subir não pode virar um laço invisível.          Era as, Clipar duas vezes seguidas descreve um trecho só, não dois.          Com clipes, Sem sobreposição não há o que mesclar: são duas jogadas distintas., Segurar o atalho: "isto vai ser longo, quero tudo".          O clipe de pré-roll (+15 more)

### Community 12 - "test_services.py"
Cohesion: 0.09
Nodes (47): ClipAudioTrackTests, HudDisplayModeTests, HudEventContractTests, ImageDiffTests, KdotoolSessionVersionTests, LinuxAudioTapTests, LinuxAudioTrackTests, LinuxFocusVerdictTests (+39 more)

### Community 13 - "ActionResult"
Cohesion: 0.12
Nodes (4): O vocabulário de tags: normalização, quarentena, fusão e promoção., Substitui o daemon: devolve uma escolha por estado, na ordem pedida., A quarentena governa o vocabulário, não a memória: nada se perde., TagVocabularyTests

### Community 14 - "WindowsServiceManager"
Cohesion: 0.18
Nodes (5): Return seconds since the last real keyboard or mouse input on Windows., Supervisor: mantém os processos de captura vivos e agenda o processamento., Combine selective-video and user-idle pauses without racing them.          Audio, windows_idle_seconds(), WindowsServiceManager

### Community 15 - "game-video-loop"
Cohesion: 0.10
Nodes (41): game-video-loop script, active_monitor(), add_long_marker(), add_marker(), adopt_video(), begin_game_session(), clean_mic_track(), cleanup() (+33 more)

### Community 16 - "runtime_dir"
Cohesion: 0.20
Nodes (12): end_video_session(), Encerra agora a sessão que já está contando para parar fora do jogo.      Quem s, Path, Helpers de runtime que funcionam igual em Linux e Windows.  Centraliza as poucas, Diretório para arquivos efêmeros (locks, estado volátil).      Linux usa ``XDG_R, Arquivo que sinaliza "estou gravando vídeo agora".      É como o laço de vídeo p, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Pedido da interface para encerrar já a sessão que está na contagem.      Só vale (+4 more)

### Community 18 - "RemapToSourceTests"
Cohesion: 0.27
Nodes (5): Devolve os tempos do áudio condensado para o eixo do áudio original.      Sem is, remap_to_source(), Voltar os tempos do bloco para o eixo do áudio original.      É a parte que, err, Fim antes do início quebraria a ordenação e a legenda., RemapToSourceTests

### Community 19 - "get"
Cohesion: 0.12
Nodes (29): active_vocabulary(), apply_tags(), canonicalize(), clean_label(), create(), _describe(), _enforce_cap(), listing() (+21 more)

### Community 20 - "main.py"
Cohesion: 0.04
Nodes (84): _apply_storage_runtime(), _apply_video_runtime(), atomic_write(), atomic_write_if_changed(), AudioSettings, cancel_update(), cancel_video_audio_track_jobs(), CleanupSettings (+76 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.08
Nodes (32): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+24 more)

### Community 24 - "capture-frame"
Cohesion: 0.27
Nodes (6): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), KDE_SESSION_VERSION, usage()

### Community 25 - "hud.py"
Cohesion: 0.09
Nodes (11): ModoLuminiTests, O Lumini é a mesma base instalada só como gravador.      Sem estes testes, a ins, Atualizar o Lume não pode desligar a análise de quem a tem., O modo precisa valer para todo processo da máquina.          São quatro que prec, Experimentar o Lumini não pode exigir editar a instalação., Um erro de digitação não pode mutilar a interface de ninguém., Sem isso a interface adivinha, e mostra botões de IA a quem não tem., Um prefixo desatento na tabela derrubaria a biblioteca de clipes. (+3 more)

### Community 27 - "WasapiError"
Cohesion: 0.19
Nodes (14): available(), Choice, choose(), LayaUnavailable, RuntimeError, Cliente do daemon do Laya — classificação de texto por vocabulário fechado.  O `, Uma pergunta de múltipla escolha para cada estado, num único lote.      ``criter, Onde o daemon escuta. No Windows não há socket UNIX — devolve vazio. (+6 more)

### Community 29 - "Path"
Cohesion: 0.17
Nodes (13): concat_videos(), cut_head(), media_duration(), Path, Duração em segundos, ou 0 quando o ffprobe não souber dizer., Guarda só os primeiros ``seconds`` do arquivo, copiando os streams.      Cortar, Emenda os pedaços num arquivo só, copiando os streams.      Os dois vêm do mesmo, Encerra a gravação longa e emenda o pré-roll na frente dela. (+5 more)

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
Cohesion: 0.19
Nodes (9): Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg.  O laço de captura do Linux usa, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar., Diferença percentual entre dois arquivos de imagem. (+1 more)

### Community 35 - "_call"
Cohesion: 0.18
Nodes (22): _AudioClientActivationParams, _Blob, _call(), _check(), default_endpoint_name(), _device_enumerator(), ensure_com(), _friendly_name() (+14 more)

### Community 37 - "_JobObject"
Cohesion: 0.15
Nodes (12): blend(), EventFrame, HudPanel, Mistura duas cores ``#rrggbb``.      O Canvas do tkinter não tem canal alfa por, Um quadro da animação de confirmação.      ``reveal`` é o quanto o evento tomou, Um painel desenhado num monitor., Corta pela largura real do texto, não por contagem de caracteres.          A HUD, Barra mínima. O evento entra por baixo empurrando o conteúdo normal.          Nã (+4 more)

### Community 38 - "run"
Cohesion: 0.10
Nodes (26): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., cancel_light_version(), cancel_upload(), join_video_session(), light_version_state() (+18 more)

### Community 39 - "connect"
Cohesion: 0.11
Nodes (16): daemon_flag(), HotkeyDaemon, keyboard_devices(), log(), main(), parse_key(), Path, Atalho global que distingue **toque** de **segurada**, lendo o evdev.  O atalho (+8 more)

### Community 43 - "prompts.py"
Cohesion: 0.07
Nodes (22): get_prompts(), reset_prompt(), active_template(), listing(), _overrides(), payload(), PromptError, PromptSpec (+14 more)

### Community 45 - "winrecord.py"
Cohesion: 0.19
Nodes (18): _clip_row(), download_filename(), host_catalog(), _link_dict(), links_for(), Path, Mandar um clipe para alguém: nome legível, versão leve e link público.  O gravad, ``2026-09-26 00-10 Sea of Thieves — trecho 02 de 05``, sem extensão.      Vale p (+10 more)

### Community 46 - "SpeechRegionTests"
Cohesion: 0.36
Nodes (5): Trechos ``(início, fim)`` em segundos onde há som acima do limiar.      Função p, speech_regions(), Detecção dos trechos com som, sobre amostras sintéticas., A folga não pode gerar tempo negativo nem passar do fim do áudio., SpeechRegionTests

### Community 47 - ".snapshot"
Cohesion: 0.05
Nodes (73): connect(), initialize(), row_dict(), _audio_channels(), backfill_video_session_durations(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item() (+65 more)

### Community 48 - "get_manager"
Cohesion: 0.18
Nodes (7): cancel_light_jobs(), Host, Interrompe recodificações — de um vídeo, ou de todos ao sair., Um lugar onde o arquivo pode ser publicado, sem conta e sem login., Sobe o arquivo fora da requisição HTTP, com progresso e cancelamento., remember_link(), _UploadJob

### Community 49 - "CallMetricsTests"
Cohesion: 0.27
Nodes (4): CallMetricsTests, Sem separar carga, leitura do prompt e geracao, encurtar prompt e chute., ollama_json repete a chamada para consertar JSON; isso custa tempo., Um audio nao passa pelo Ollama; herdar a medicao de uma tela mentiria.

### Community 50 - "resolve_media_source"
Cohesion: 0.18
Nodes (16): light_video_file(), Baixa a versão leve pronta; 409 enquanto ela não existir.      Não gera nada aqu, light_filename(), light_state(), normalized_limit(), Publica o clipe num host grátis, **só com confirmação explícita**.      A trava, O teto entra no nome: duas versões do mesmo clipe não se confundem., Bitrate que cabe no teto, e o tamanho de imagem que esse bitrate aguenta.      R (+8 more)

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
Cohesion: 0.04
Nodes (31): ConfirmationSounds, EditingFolder, HotkeyInput(), CAPTION_LABELS, CAPTION_ORDER, CapturaTab, ConfirmationSounds(), ContextMenuAction (+23 more)

### Community 55 - "App"
Cohesion: 0.11
Nodes (19): AudioSettings, Capture, CleanupSettings, PipelineQueue, ScreenSequenceResult, Status, uploadVideo(), VideoSettings (+11 more)

### Community 56 - "videoTime"
Cohesion: 0.13
Nodes (17): AudioAnalysis(), ChapterReader(), chapterStart(), clipClock(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SessionCard() (+9 more)

### Community 57 - "_video_pause_file"
Cohesion: 0.16
Nodes (8): foreground_details(), log(), Grava uma sessão lógica, possivelmente dividida em segmentos., Mantém Replay Buffer ativo e salva somente quando F8 for pressionado., Título, classe e executável da janela em foco — o que o OBS precisa     para eng, ``jogo``, ``na-tela`` ou ``fora`` — a mesma pergunta do laço Linux.          Trê, Atualiza o prazo publicado para a HUD e informa se ele venceu., VideoLoop

### Community 58 - "WasapiCapture"
Cohesion: 0.15
Nodes (8): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers.      M, Um fluxo de captura: microfone padrão ou loopback da saída padrão.      A saída, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio).          Um, WasapiCapture, WAVEFORMATEXTENSIBLE

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "trim_video"
Cohesion: 0.10
Nodes (26): audio_file(), _audio_streams(), capture_speaker_sample(), delete_capture(), delete_capture_file(), delete_file(), download_video(), game_icon_file() (+18 more)

### Community 61 - "ollama_json"
Cohesion: 0.19
Nodes (6): Escreve o sinal de atividade lido pela HUD.          Fica separado de :meth:`_su, Registra um acontecimento pontual e publica na hora.          A sequência é o qu, Confirma uma ação aceita sem depender da interface estar em foco., Segurar: abre a gravação longa e, na segurada seguinte, a fecha., Anota o instante atual da gravação.          Os marcadores ficam em memória e só, Guarda o pré-roll e começa a gravar em paralelo ao Replay Buffer.

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.21
Nodes (12): health(), install_update_now(), _do_arquivo(), e_lumini(), modo_atual(), Em qual modo esta instalação foi montada.  O Lume completo grava, transcreve, de, Lê ``LUME_MODE`` do ``lume.conf``, sem depender do resto do backend.      Parse, O modo em vigor. Sem cache, de propósito.      O arquivo tem uma linha, e ``/api (+4 more)

### Community 64 - "HudStateTests"
Cohesion: 0.14
Nodes (12): HudStateTests, As regras que decidem se a captura está saudável.      Rodam nos dois sistemas d, Segurou o atalho: já não é "armado", é gravando de verdade., Ficar calado é normal; confundir com falha destrói a confiança na HUD., _disk_alerts(), evaluate(), _meter_alerts(), Estado da HUD de gravação: instantâneo portátil e regras de saúde.  Este módulo (+4 more)

### Community 65 - "local_origin_only"
Cohesion: 0.22
Nodes (14): begin(), close_stale(), _ensure_schema(), finish(), heartbeat(), iso_time(), main(), Contagem de tempo por jogo, independente do que foi gravado.  O tempo de jogo é (+6 more)

### Community 67 - "VideoWindowTest"
Cohesion: 0.36
Nodes (4): VideoWindowTest, O teste de janela do Lume precisa responder o mesmo que o gravador.      Se ele, Adicionar um jogo usa a resolução do monitor dele, não 1920x1080 fixo., VideoWindowTestEndpointTests

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
Cohesion: 0.11
Nodes (9): HotkeyChordTests, WindowsBracketTests, log(), MarkerHotkey, MSG, Atalhos globais no Windows, registrados fora de qualquer janela.  No Linux o ata, Espera o desfecho da tecla e diz se foi toque ou segurada.          Bloquear a f, Descarta as repetições enfileiradas enquanto a tecla esteve abaixada. (+1 more)

### Community 72 - "capture_frames"
Cohesion: 0.20
Nodes (9): 1. Atividades por assunto, com agrupamento por aplicativo como apoio, 2. Contexto completo e verificável em resumos e vídeos, 3. Captura e fila: preservar o lugar de onde a pessoa veio, 4. Vídeos, áudio e busca: acesso consistente às evidências, 5. Ajustes, calendário e acessibilidade, Melhorias aplicadas nesta revisão, Revisão das demais áreas e prioridades, Revisão do Lume — experiência e contexto da IA (+1 more)

### Community 74 - "EditingFolderTests"
Cohesion: 0.11
Nodes (5): EditingFolderTests, A pasta de edicao troca garimpo de arquivo por nome legivel e EDL., 12,5 s a 60 fps sao 750 quadros depois do inicio da timeline., O hardlink segura os bytes, entao apagar por engano so confundiria., O segundo trecho comeca onde o primeiro acaba, e o EDL acompanha.

### Community 75 - "hudsource.py"
Cohesion: 0.19
Nodes (8): MultipartBody, RuntimeError, A resposta é a URL em texto puro — e o erro também vem como HTTP 200.          P, O envio foi interrompido a pedido de quem o começou., Corpo multipart que lê o arquivo em blocos e sabe o próprio tamanho.      O tama, Publica o arquivo e devolve a URL. **Só o job de upload chama isto.**      Nenhu, SharingCancelled, upload_file()

### Community 76 - "_Growth"
Cohesion: 0.38
Nodes (6): ActivitiesView(), ActivityCard(), Frame, searchable(), time(), ActivitySession

### Community 77 - "Path"
Cohesion: 0.15
Nodes (12): Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., Valores de ``tela.conf`` relevantes para a captura de um frame., ScreenConfig, Path, _as_bool(), _as_float(), _as_int(), _parse_config() (+4 more)

### Community 78 - "multimodal_context"
Cohesion: 0.40
Nodes (3): MediaFreshnessTests, As URLs de mídia têm de mudar quando o arquivo muda.      O corte reescreve o ví, Um clipe apagado entre a listagem e a montagem da URL não é erro 500.

### Community 79 - "Path"
Cohesion: 0.22
Nodes (9): Decision, _merge_ready(), As tags com alguma chance de serem a mesma coisa, e só elas.      Mandar o vocab, Pergunta ao Laya quais propostas são sinônimo de alguma tag ativa., Última checagem semântica antes de ativar: o vocabulário pode ter crescido., O caminho que uma string bruta percorreu até virar (ou não) uma tag., Resolution, _resolve_with_laya() (+1 more)

### Community 81 - "winscreen.py"
Cohesion: 0.22
Nodes (4): Regras sem prefixo procuram somente no executável.          Assim uma pasta cham, Janela atual e resultado das regras usando campos separados., Instantâneo de ``video.conf`` e da lista de apps., Settings

### Community 82 - "context_overflow"
Cohesion: 0.67
Nodes (5): dateOf(), DayPicker(), fullLabel(), MemoryDay, monthLabel()

### Community 83 - "._start"
Cohesion: 0.24
Nodes (6): _JobObject, _Process, Path, Popen, Amarra os processos filhos ao ciclo de vida da API.      É o que o systemd conse, Um processo filho supervisionado.

### Community 84 - "test_main.py"
Cohesion: 0.15
Nodes (9): matched_sensitive_pattern(), Primeiro padrão sensível (regex, case-insensitive) que casa com a janela.      M, main(), _monitor_key(), Path, Identidade do monitor a partir do nome do arquivo (``..._mon1_DP-1.png``)., Motivo para não capturar agora, ou ``None`` se pode capturar., ScreenLoop (+1 more)

### Community 85 - "get_backend"
Cohesion: 0.15
Nodes (18): capture_change_test_frames(), capture_frames(), delete_voice_identity(), get_screen_settings(), mic_level(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver.      A mesma regra nos doi, Captura um conjunto de frames com a configuração atual. (+10 more)

### Community 86 - ".snapshot"
Cohesion: 0.17
Nodes (14): _app_label(), _count_markers(), _elapsed(), _focus_grace_remaining(), _long_elapsed(), Path, Coleta do estado que a HUD mostra, com um coletor por sistema.  Mesma divisão qu, Segmento sendo escrito agora pelo ``gpu-screen-recorder``. (+6 more)

### Community 87 - "filter_hallucinated_segments"
Cohesion: 0.12
Nodes (9): ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Pausar desabilita a unit: só parar valia até o próximo boot., LinuxIdlePauseTests, _pausable(), Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)., Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API. (+1 more)

### Community 88 - "hudsource.py"
Cohesion: 0.17
Nodes (3): Um clipe no disco com o sidecar do gravador e a linha do banco., Recodificar um arquivo que já cabe só pioraria a imagem., ``GET`` que dispara meio minuto de ffmpeg viraria timeout no navegador.

### Community 89 - "media_source_key"
Cohesion: 0.08
Nodes (12): MonitorResolutionTests, O dshow corta nomes longos: casa pelo prefixo do nome do WASAPI., A resolução sugerida para um jogo novo é a física, não a lógica., Com ``dmSize`` errado o EnumDisplaySettingsW recusa a chamada.          No Windo, Monitor, Um monitor físico: rótulo estável + geometria em pixels do desktop., Resolução física, em pixels reais — a que o gravador de vídeo vê.          Arred, Path (+4 more)

### Community 90 - ".grab_frame"
Cohesion: 0.09
Nodes (31): _activity_batch_summary(), adaptive_web_research(), context_overflow(), daily_narrative_target(), describe_long_video(), describe_tag_candidates(), describe_video(), generate_hourly_summaries() (+23 more)

### Community 91 - "WasapiError"
Cohesion: 0.20
Nodes (6): ProcessLoopbackCapture, Falha numa chamada COM do WASAPI, com o HRESULT preservado., Loopback que inclui ou exclui a árvore de um processo do Windows., WasapiError, discord_process_id(), Retorna a raiz da árvore Discord.exe com mais processos descendentes.

### Community 92 - "context_overflow"
Cohesion: 0.26
Nodes (21): update_status(), exclusive_lock(), Trava exclusiva e não-bloqueante sobre ``path``.      Retorna ``True`` se conseg, apply_pending(), can_install_now(), cancel(), check(), check_compatible() (+13 more)

### Community 93 - "_LazyOle32"
Cohesion: 0.12
Nodes (12): api, TagDecision, TagEntry, TagPromotion, TagStatus, TagTestResult, TagVocabulary, OUTCOME (+4 more)

### Community 94 - "HoldDetectorTests"
Cohesion: 0.22
Nodes (14): diagnostics(), is_provisioned(), launch(), ObsError, port_open(), prepare(), RuntimeError, O OBS já aceita comandos de verdade?      A porta abrir não basta: o obs-websock (+6 more)

### Community 97 - "winscreen.py"
Cohesion: 0.13
Nodes (14): dependencies, react, react-dom, name, private, scripts, build, dev (+6 more)

### Community 98 - "services.py"
Cohesion: 0.20
Nodes (4): Uma unit supervisionada.      ``simple`` roda enquanto o serviço estiver ligado, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef

### Community 99 - ".active"
Cohesion: 0.13
Nodes (12): light_video_command(), _LightVersionJob, progress_percent(), prune_share_cache(), Popen, A receita que cabe no teto: quanto bitrate, em que tamanho de imagem., Recodificação que cabe no teto e serve para ser assistida por outra pessoa., Lê ``out_time_us=12500000`` do ``-progress`` e devolve 21 num clipe de 60s. (+4 more)

### Community 100 - "devDependencies"
Cohesion: 0.18
Nodes (11): devDependencies, playwright, @types/react, @types/react-dom, typescript, vite, playwright, @types/react (+3 more)

### Community 101 - "hudsource.py"
Cohesion: 0.26
Nodes (12): apply_preset(), clear_custom(), custom_sound(), default_sound(), play(), presets(), Path, Sons de confirmação do atalho de gravação, personalizáveis.  Cada ação aceita pe (+4 more)

### Community 102 - "_LazyOle32"
Cohesion: 0.28
Nodes (3): _chunks(), ConfirmationSoundTests, Sons do atalho: o arquivo enviado substitui o padrão, e remover o devolve.

### Community 103 - "HudCollector"
Cohesion: 0.20
Nodes (7): get_collector(), HudCollector, ABC, Fonte do instantâneo da HUD., Sobe threads de coleta (no-op quando não houver)., Estado atual, já normalizado., Coletor do SO atual, na mesma convenção de :func:`app.capture.get_backend`.

### Community 104 - ".feed"
Cohesion: 0.24
Nodes (8): Pico de um WAV PCM 16 bits, em dBFS. ``-inf`` vira o piso -99., A faixa está muda o bastante para transcrevê-la ser desperdício?      Numa sessã, track_is_silent(), track_peak_dbfs(), Faixas mudas não valem uma transcrição.      Numa sessão sem Discord a faixa del, -40 dBFS é fala baixa de verdade; pular isso perderia conversa., Na dúvida, transcreve: perder fala é pior que gastar tempo., SilentTrackTests

### Community 105 - "read_shell_config"
Cohesion: 0.29
Nodes (3): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas.

### Community 106 - ".test_an_unreadable_foreground_window_neither_starts_nor_advances_the_countdown"
Cohesion: 0.09
Nodes (25): apply_confirmation_sound_preset(), bounded_video_range(), _confirmation_sounds(), list_confirmation_sounds(), local_origin_only(), origin_allowed(), Se este caminho só faz sentido com o pipeline instalado., No Lumini, o que depende de IA responde 409 em vez de tentar.      Esconder os b (+17 more)

### Community 108 - "multimodal_context"
Cohesion: 0.27
Nodes (3): Anota que a captura deve (ou não) voltar na próxima abertura do Lume.          N, Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., _unknown()

### Community 110 - ".action"
Cohesion: 0.29
Nodes (3): Arquivo de estado que o laço de vídeo cria enquanto controla as capturas.      M, (Re)inicia o swayidle apontando os eventos para o flag de idle., _video_pause_file()

### Community 111 - "matched_sensitive_pattern"
Cohesion: 0.32
Nodes (8): backfill_confirmed_voice_observations(), enroll_voice_identity(), _normalized_average(), Recalcula um perfil dando um único voto a cada gravação., rebuild_voice_identity(), SpeakerLabelUpdate, update_capture_speaker(), update_video_speaker()

### Community 112 - "VideoActivityFlagTests"
Cohesion: 0.22
Nodes (4): _Growth, _MeterTracker, Contabilidade temporal de uma fonte de áudio.      Guarda desde quando a fonte n, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo).

### Community 113 - "rebuild_voice_identity"
Cohesion: 0.22
Nodes (10): batch(), _identify(), password(), Faz o *hello/identify* do obs-websocket v5 sobre um socket já aberto.      ``sub, Várias requisições numa conexão só., Mantém uma conexão viva com o OBS, entregando eventos e leituras.      Ao contrá, Senha do websocket da instância dedicada, criada na primeira vez., _session() (+2 more)

### Community 114 - "LinuxHudCollector"
Cohesion: 0.40
Nodes (4): _devmode_w(), _monitor_info_ex(), MONITORINFOEXW: o ``szDevice`` é o nome que o EnumDisplaySettings pede., DEVMODEW com a união de impressora/monitor como 16 bytes opacos.      Só ``dmPel

### Community 115 - "delete_voice_identity"
Cohesion: 0.07
Nodes (42): cancel_video_audio_track_job(), cancel_video_audio_tracks(), _delete_media_sidecars(), delete_video(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), media_url() (+34 more)

### Community 116 - "HudStatus"
Cohesion: 0.05
Nodes (38): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., _alert_sound(), _assert_topmost(), _declare_dpi_aware() (+30 more)

### Community 117 - ".feed"
Cohesion: 0.29
Nodes (3): _FakeResponse, O host recusa com HTTP 200 e um texto no corpo; engolir isso deixaria         a, Resposta de host de arquivo: corpo em texto puro, sem rede envolvida.

### Community 120 - "._partial_segment"
Cohesion: 0.15
Nodes (11): parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., _install_stop_handlers(), Atende todos os sinais de parada que o SO pode mandar.      No Windows o supervi, _consume_end_request(), looks_blank(), main(), Gravação seletiva de jogos no Windows — porte de ``bin/game-video-loop``.  Mesma (+3 more)

### Community 121 - "multimodal_context"
Cohesion: 0.27
Nodes (10): _copy_installation(), find_installation(), provision(), Path, Escreve o perfil e as preferências da instância dedicada., Garante a cópia portátil configurada; devolve a raiz dela., Onde o OBS do usuário está instalado, se estiver., Duplica a instalação do OBS. Usa robocopy, que é ordens de grandeza     mais ráp (+2 more)

### Community 122 - "_event_fields"
Cohesion: 0.50
Nodes (4): _parse_max_geometry(), Interpreta ``"1920x1080>"`` -> (1920, 1080, apenas_reduzir)., Dimensões finais respeitando ``MAX_GEOMETRY`` (mantém proporção)., _scaled_size()

### Community 125 - "stop_target_is_already_gone"
Cohesion: 0.33
Nodes (3): parse_json_response(), Recupera JSON que o parser do Ollama classificou todo como thinking., recover_json_from_thinking()

### Community 126 - "exige"
Cohesion: 1.00
Nodes (3): exige(), instalar-lumini.sh script, tem()

### Community 127 - "safe_research_query"
Cohesion: 0.22
Nodes (6): Path, Lista de expressões de um arquivo de padrões, ignorando comentários., Nome estável para ``<título> | <executável>``.      Alguns jogos, especialmente, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados.          ``, read_patterns(), stable_app_label()

### Community 128 - ".active_monitor"
Cohesion: 0.25
Nodes (8): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.      ``ut, read_shell_config(), apply_mic_filters(), mic_filter_requests(), mic_filter_settings(), (supressão ligada, limite em dB) de ``audio.conf``, com os padrões., Pedidos do obs-websocket que deixam o microfone com os filtros de agora.      Se, Aplica ao microfone do OBS a supressão de ruído e o volume mínimo.      Os filtr

### Community 129 - "test_updater.py"
Cohesion: 0.25
Nodes (3): LinuxHudCollector, Estado derivado do laço bash e medidores lidos dos buses do PipeWire.      O ``b, Janela em foco, com a mesma cadência do laço bash (2 s).          O sidecar ``.w

### Community 131 - ".test_a_summary_older_than_its_own_memories_is_redone"
Cohesion: 0.29
Nodes (7): capture_speed_stats(), pipeline_queue(), pipeline_summary_job(), queue_eta_seconds(), Média recente de análise por tipo, para estimar a duração da fila.      Só as úl, Estimativa da fila restante; a execução do worker é sequencial., Expose the worker's actual plan; older workers report only saved evidence.

### Community 132 - "UpdateNotice.tsx"
Cohesion: 0.67
Nodes (3): request(), UpdateNotice(), UpdateStatus

### Community 142 - ".test_bash_loop_counts_game_time_through_the_shared_cli"
Cohesion: 0.38
Nodes (7): _as_float(), _as_ratio(), probe_video_shape(), Duração, altura e fps num ``ffprobe`` só.      A duração do banco não serve aqui, ``60/1`` → 60.0; é assim que o ffprobe conta quadros por segundo., video_shape(), VideoShape

### Community 143 - ".test_capture_target_does_not_pull_a_disabled_capture"
Cohesion: 0.38
Nodes (4): ObsWindowSpecTests, O identificador de janela do OBS é ``título:classe:executável``.      Um título, _encode_field(), Escapa um campo do identificador de janela do OBS.      O identificador é ``títu

### Community 144 - ".test_opus_stems_go_to_a_container_that_accepts_them"
Cohesion: 0.33
Nodes (5): _activity_app(), _activity_groups(), Prefere a identidade capturada da janela aos nomes variáveis da IA., Separa por aplicativo e continuidade; mudanças de título não quebram a sessão., _screen_window()

### Community 145 - ".test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis"
Cohesion: 0.20
Nodes (8): apply_exact_game_durations(), game_activity_rows(), Sessões monitoradas recortadas ao dia local, inclusive ao cruzar meia-noite., Substitui estimativas da IA pelos intervalos medidos pelo contador da sidebar., Memórias do dia, representando cada sessão de vídeo apenas uma vez., Valida referências da IA e protege os arquivos escolhidos., summary_source_rows(), validate_relevant_media()

### Community 146 - ".test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time"
Cohesion: 0.33
Nodes (3): HudFrameRateTests, As três cadências existem por causa do custo de redesenhar.      Cada volta recr, Uma entrada de 0,26 s precisa de quadros suficientes para não escadear.

### Community 148 - ".test_stale_game_session_is_closed_at_the_last_heartbeat"
Cohesion: 0.40
Nodes (5): _attached_source(), _pulse_sources(), Lê PCM cru do monitor de um bus e acumula o pico.          Taxa baixa e um canal, Mapa id -> nome das fontes do PipeWire/Pulse., Fonte à qual o ``parec`` de ``client`` está realmente ligado.      Existe porque

### Community 149 - ".test_end_video_session_only_during_the_focus_countdown"
Cohesion: 0.33
Nodes (6): _process_path(), Caminho do executável de um processo, ou vazio se não der para consultar., PID da instância dedicada, distinguindo-a da do usuário pelo caminho.      Enume, Encerra a instância dedicada, pedindo com educação antes de forçar., running_pid(), stop()

### Community 151 - "LightVersion"
Cohesion: 0.40
Nodes (3): _ActivationHandler, GUID, Implementação mínima de IActivateAudioInterfaceCompletionHandler.

### Community 153 - "selftest.py"
Cohesion: 0.60
Nodes (4): main(), _measure_volume(), Path, Self-test de captura — rode isto ao trocar de sistema.      python -m app.captur

### Community 154 - "forget_shared_link"
Cohesion: 0.50
Nodes (4): forget_shared_link(), Tira o link da lista. O arquivo continua no ar — o host é que o apaga., forget_link(), Esquece o link. Não o despublica — e a interface diz isso em voz alta.

## Knowledge Gaps
- **144 isolated node(s):** `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame`, `StorageCandidate`, `WebSource` (+139 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `filter_hallucinated_segments` to `ConfigTests`, `VideoSettings`, `SilentTrackTests`, `test_services.py`, `ActionResult`, `WindowsServiceManager`, `.test_capture_target_does_not_pull_a_disabled_capture`, `RemapToSourceTests`, `.test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time`, `main.py`, `.test_recording_keeps_the_mix_ahead_of_the_isolated_tracks`, `audio_intelligence.py`, `hud.py`, `run`, `SpeechRegionTests`, `.snapshot`, `CallMetricsTests`, `RegionGroupingTests`, `Path`, `ServiceManager`, `trim_video`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `multimodal_context`, `LinuxAppRuleMatchTests`, `._start`, `media_source_key`, `services.py`, `_LazyOle32`, `.feed`, `multimodal_context`, `matched_sensitive_pattern`, `delete_voice_identity`, `HudStatus`, `.feed`, `LinuxAudioTapTests`, `stop_target_is_already_gone`?**
  _High betweenness centrality (0.134) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `package.json`, `VideoWindowTest`, `VideoSettings`, `read_shell_config`, `.test_an_unreadable_foreground_window_neither_starts_nor_advances_the_countdown`, `.test_opus_stems_go_to_a_container_that_accepts_them`, `.test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis`, `audio_intelligence.py`, `filter_hallucinated_segments`, `.grab_frame`, `stop_target_is_already_gone`, `stop_target_is_already_gone`?**
  _High betweenness centrality (0.100) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `filter_hallucinated_segments` to `ConfigTests`, `VideoSettings`, `SilentTrackTests`, `test_services.py`, `ActionResult`, `.test_capture_target_does_not_pull_a_disabled_capture`, `runtime_dir`, `RemapToSourceTests`, `.test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time`, `main.py`, `.test_recording_keeps_the_mix_ahead_of_the_isolated_tracks`, `audio_intelligence.py`, `hud.py`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `Path`, `ServiceManager`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `multimodal_context`, `LinuxAppRuleMatchTests`, `media_source_key`, `_LazyOle32`, `.feed`, `.action`, `HudStatus`, `.feed`, `LinuxAudioTapTests`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `VideoWindowTest`) actually correct?**
  _`ConfigTests` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 80 inferred relationships involving `ActionResult` (e.g. with `AudioSettings` and `CleanupSettings`) actually correct?**
  _`ActionResult` has 80 INFERRED edges - model-reasoned connections that need verification._
- **Are the 41 inferred relationships involving `VideoLoop` (e.g. with `ClipAudioTrackTests` and `HoldDetectorTests`) actually correct?**
  _`VideoLoop` has 41 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` to the rest of the system?**
  _144 weakly-connected nodes found - possible documentation gaps or missing edges._