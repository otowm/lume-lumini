# Graph Report - lume  (2026-09-27)

## Corpus Check
- 82 files · ~156,668 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2537 nodes · 6034 edges · 142 communities (115 shown, 27 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 621 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6517e558`
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

## God Nodes (most connected - your core abstractions)
1. `ConfigTests` - 120 edges
2. `connect()` - 118 edges
3. `ActionResult` - 115 edges
4. `VideoLoop` - 78 edges
5. `SystemdServiceManager` - 73 edges
6. `HudSnapshot` - 64 edges
7. `Monitor` - 61 edges
8. `Hud` - 57 edges
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

## Communities (142 total, 27 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.04
Nodes (16): captured_video_session(), Lê a identidade portátil deixada pelo gravador seletivo.      Vídeos antigos só, _activity_groups(), Separa por aplicativo e continuidade; mudanças de título não quebram a sessão., ConfigTests, Path, O laço do Linux conta tempo pela mesma porta que o gravador do Windows., Uma queda no meio da partida não pode contar o tempo até agora. (+8 more)

### Community 1 - "src/api.ts"
Cohesion: 0.05
Nodes (37): ActivityFrame, AnalysisTrace, AppMode, AudioEvent, DaySummary, EditingEntry, EditingResult, GameIcon (+29 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (57): _activity_app(), _activity_batch_summary(), _activity_image(), adaptive_web_research(), analyze_screen_sequence(), analyze_video_chapter(), audio_channel_count(), audio_stream_count() (+49 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "LinuxCaptureBackend"
Cohesion: 0.08
Nodes (19): CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco.          Retorna ``N, Por que ``active_window`` falhou, numa frase para a interface., Monitores habilitados, em ordem estável de índice., Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados.          `` (+11 more)

### Community 5 - "obs.py"
Cohesion: 0.06
Nodes (64): any_fullscreen(), apply_mic_filters(), batch(), call(), _copy_installation(), diagnostics(), _encode_field(), ensure_scene() (+56 more)

### Community 6 - "record"
Cohesion: 0.11
Nodes (19): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., main(), _mix(), _multichannel(), array, Path, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.  Gr (+11 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.15
Nodes (24): cached_file(), _download(), _fetch(), _from_steam(), _from_steamgriddb(), _get(), _json(), lookup() (+16 more)

### Community 9 - "VideoSettings"
Cohesion: 0.36
Nodes (4): VideoSettings, Salvar as preferências não pode apagar chaves silenciosamente.      ``set_video_, Uma instalação antiga não pode ficar sem HUD nem quebrar ao salvar., VideoSettingsRoundTripTests

### Community 10 - "Lume no Windows"
Cohesion: 0.05
Nodes (40): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, Abrir de outro aparelho, As três faixas de áudio (+32 more)

### Community 11 - "SilentTrackTests"
Cohesion: 0.05
Nodes (23): LinuxCaptureModeTests, Path, O gravador de jogo não pode depender da captura de áudio estar de pé.          O, O VCE de uma RX 550 derrubou a GPU inteira ("ring vce0 timeout").          Em Po, Um gravador que morre ao subir não pode virar um laço invisível.          Era as, Clipar duas vezes seguidas descreve um trecho só, não dois.          Com clipes, Sem sobreposição não há o que mesclar: são duas jogadas distintas., Segurar o atalho: "isto vai ser longo, quero tudo".          O clipe de pré-roll (+15 more)

### Community 12 - "test_services.py"
Cohesion: 0.06
Nodes (48): ClipAudioTrackTests, HoldDetectorTests, HudEventContractTests, ImageDiffTests, KdotoolSessionVersionTests, LinuxAudioTapTests, LinuxAudioTrackTests, LinuxFocusVerdictTests (+40 more)

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
Cohesion: 0.31
Nodes (7): Path, Diretório para arquivos efêmeros (locks, estado volátil).      Linux usa ``XDG_R, Arquivo que sinaliza "estou gravando vídeo agora".      É como o laço de vídeo p, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., runtime_dir(), video_activity_flag(), video_recording_flag()

### Community 18 - "RemapToSourceTests"
Cohesion: 0.33
Nodes (3): Voltar os tempos do bloco para o eixo do áudio original.      É a parte que, err, Fim antes do início quebraria a ordenação e a legenda., RemapToSourceTests

### Community 19 - "get"
Cohesion: 0.14
Nodes (23): active_vocabulary(), apply_tags(), canonicalize(), clean_label(), create(), _describe(), _enforce_cap(), listing() (+15 more)

### Community 20 - "main.py"
Cohesion: 0.05
Nodes (75): atomic_write(), AudioSettings, capture_change_test_frames(), capture_frames(), CleanupSettings, compare_screen_change_test(), ContextUpdate, create_tag() (+67 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.09
Nodes (27): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+19 more)

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
Cohesion: 0.12
Nodes (17): concat_videos(), media_duration(), Path, Duração em segundos, ou 0 quando o ffprobe não souber dizer., Emenda os pedaços num arquivo só, copiando os streams.      Os dois vêm do mesmo, Escreve o sinal de atividade lido pela HUD.          Fica separado de :meth:`_su, Registra um acontecimento pontual e publica na hora.          A sequência é o qu, Confirma uma ação aceita sem depender da interface estar em foco. (+9 more)

### Community 30 - "editing.py"
Cohesion: 0.11
Nodes (36): available_name(), chapter_seconds(), clip_markers(), EditingError, entries(), folder(), frames_to_timecode(), inside_folder() (+28 more)

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
Cohesion: 0.08
Nodes (22): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., _assert_topmost(), _declare_dpi_aware(), ease_in_cubic() (+14 more)

### Community 38 - "run"
Cohesion: 0.06
Nodes (58): connect(), initialize(), _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., row_dict(), _audio_channels() (+50 more)

### Community 39 - "connect"
Cohesion: 0.11
Nodes (16): daemon_flag(), HotkeyDaemon, keyboard_devices(), log(), main(), parse_key(), Path, Atalho global que distingue **toque** de **segurada**, lendo o evdev.  O atalho (+8 more)

### Community 43 - "prompts.py"
Cohesion: 0.07
Nodes (21): get_prompts(), reset_prompt(), active_template(), listing(), _overrides(), payload(), PromptError, PromptSpec (+13 more)

### Community 45 - "winrecord.py"
Cohesion: 0.16
Nodes (18): _apply_storage_runtime(), _apply_video_runtime(), atomic_write_if_changed(), get_storage_settings(), Write a config only when its contents changed., _report_runtime_failure(), _restart_audio_runtime(), _restart_screen_runtime() (+10 more)

### Community 46 - "SpeechRegionTests"
Cohesion: 0.36
Nodes (5): Trechos ``(início, fim)`` em segundos onde há som acima do limiar.      Função p, speech_regions(), Detecção dos trechos com som, sobre amostras sintéticas., A folga não pode gerar tempo negativo nem passar do fim do áudio., SpeechRegionTests

### Community 47 - ".snapshot"
Cohesion: 0.15
Nodes (12): blend(), EventFrame, HudPanel, Mistura duas cores ``#rrggbb``.      O Canvas do tkinter não tem canal alfa por, Um quadro da animação de confirmação.      ``reveal`` é o quanto o evento tomou, Um painel desenhado num monitor., Corta pela largura real do texto, não por contagem de caracteres.          A HUD, Barra mínima. O evento entra por baixo empurrando o conteúdo normal.          Nã (+4 more)

### Community 48 - "get_manager"
Cohesion: 0.27
Nodes (3): Anota que a captura deve (ou não) voltar na próxima abertura do Lume.          N, Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., _unknown()

### Community 49 - "CallMetricsTests"
Cohesion: 0.27
Nodes (4): CallMetricsTests, Sem separar carga, leitura do prompt e geracao, encurtar prompt e chute., ollama_json repete a chamada para consertar JSON; isso custa tempo., Um audio nao passa pelo Ollama; herdar a medicao de uma tela mentiria.

### Community 50 - "resolve_media_source"
Cohesion: 0.10
Nodes (28): cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_screen_sequence(), cancel_video_analysis(), cancel_video_session(), capture_action(), capture_speed_stats() (+20 more)

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
Nodes (29): EditingFolder, LightVersion, ShareUpload, HotkeyInput(), CAPTION_LABELS, CAPTION_ORDER, CapturaTab, ContextMenuAction (+21 more)

### Community 55 - "App"
Cohesion: 0.11
Nodes (19): AudioSettings, Capture, CleanupSettings, PipelineQueue, ScreenSequenceResult, Status, uploadVideo(), VideoSettings (+11 more)

### Community 56 - "videoTime"
Cohesion: 0.13
Nodes (17): AudioAnalysis(), ChapterReader(), chapterStart(), clipClock(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SessionCard() (+9 more)

### Community 57 - "_video_pause_file"
Cohesion: 0.14
Nodes (9): Não sei que janela é essa" não é "o usuário saiu do jogo".          ``GetForegro, foreground_details(), log(), Grava uma sessão lógica, possivelmente dividida em segmentos., Mantém Replay Buffer ativo e salva somente quando F8 for pressionado., Título, classe e executável da janela em foco — o que o OBS precisa     para eng, ``jogo``, ``na-tela`` ou ``fora`` — a mesma pergunta do laço Linux.          Trê, Atualiza o prazo publicado para a HUD e informa se ele venceu. (+1 more)

### Community 58 - "WasapiCapture"
Cohesion: 0.15
Nodes (8): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers.      M, Um fluxo de captura: microfone padrão ou loopback da saída padrão.      A saída, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio).          Um, WasapiCapture, WAVEFORMATEXTENSIBLE

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "trim_video"
Cohesion: 0.33
Nodes (3): parse_json_response(), Recupera JSON que o parser do Ollama classificou todo como thinking., recover_json_from_thinking()

### Community 61 - "ollama_json"
Cohesion: 0.11
Nodes (24): audio_file(), _audio_streams(), capture_speaker_sample(), delete_capture(), delete_capture_file(), delete_file(), import_video(), mic_level() (+16 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.13
Nodes (14): dependencies, react, react-dom, name, private, scripts, build, dev (+6 more)

### Community 64 - "HudStateTests"
Cohesion: 0.14
Nodes (13): HudStateTests, As regras que decidem se a captura está saudável.      Rodam nos dois sistemas d, Segurou o atalho: já não é "armado", é gravando de verdade., Ficar calado é normal; confundir com falha destrói a confiança na HUD., Alert, _disk_alerts(), evaluate(), Meter (+5 more)

### Community 65 - "local_origin_only"
Cohesion: 0.08
Nodes (29): cancel_light_version(), cancel_update(), cancel_upload(), cancel_video_audio_track_jobs(), download_video(), game_icon_file(), lifespan(), light_version_state() (+21 more)

### Community 67 - "VideoWindowTest"
Cohesion: 0.33
Nodes (5): test_video_window(), VideoWindowTest, O teste de janela do Lume precisa responder o mesmo que o gravador.      Se ele, Adicionar um jogo usa a resolução do monitor dele, não 1920x1080 fixo., VideoWindowTestEndpointTests

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
Cohesion: 0.11
Nodes (9): HotkeyChordTests, WindowsBracketTests, log(), MarkerHotkey, MSG, Atalhos globais no Windows, registrados fora de qualquer janela.  No Linux o ata, Espera o desfecho da tecla e diz se foi toque ou segurada.          Bloquear a f, Descarta as repetições enfileiradas enquanto a tecla esteve abaixada. (+1 more)

### Community 72 - "capture_frames"
Cohesion: 0.20
Nodes (9): 1. Atividades por assunto, com agrupamento por aplicativo como apoio, 2. Contexto completo e verificável em resumos e vídeos, 3. Captura e fila: preservar o lugar de onde a pessoa veio, 4. Vídeos, áudio e busca: acesso consistente às evidências, 5. Ajustes, calendário e acessibilidade, Melhorias aplicadas nesta revisão, Revisão das demais áreas e prioridades, Revisão do Lume — experiência e contexto da IA (+1 more)

### Community 74 - "EditingFolderTests"
Cohesion: 0.11
Nodes (5): EditingFolderTests, A pasta de edicao troca garimpo de arquivo por nome legivel e EDL., 12,5 s a 60 fps sao 750 quadros depois do inicio da timeline., O hardlink segura os bytes, entao apagar por engano so confundiria., O segundo trecho comeca onde o primeiro acaba, e o EDL acompanha.

### Community 75 - "hudsource.py"
Cohesion: 0.23
Nodes (11): health(), _do_arquivo(), e_lumini(), modo_atual(), Em qual modo esta instalação foi montada.  O Lume completo grava, transcreve, de, Lê ``LUME_MODE`` do ``lume.conf``, sem depender do resto do backend.      Parse, O modo em vigor. Sem cache, de propósito.      O arquivo tem uma linha, e ``/api, _backend_is_running() (+3 more)

### Community 76 - "_Growth"
Cohesion: 0.38
Nodes (6): ActivitiesView(), ActivityCard(), Frame, searchable(), time(), ActivitySession

### Community 77 - "Path"
Cohesion: 0.18
Nodes (11): devDependencies, playwright, @types/react, @types/react-dom, typescript, vite, playwright, @types/react (+3 more)

### Community 78 - "multimodal_context"
Cohesion: 0.40
Nodes (3): MediaFreshnessTests, As URLs de mídia têm de mudar quando o arquivo muda.      O corte reescreve o ví, Um clipe apagado entre a listagem e a montagem da URL não é erro 500.

### Community 79 - "Path"
Cohesion: 0.18
Nodes (12): Decision, _merge_ready(), _note_use(), _persist(), Acumula a evidência da candidata: quantas vezes, em que dias, com que texto., Pergunta ao Laya quais propostas são sinônimo de alguma tag ativa., Última checagem semântica antes de ativar: o vocabulário pode ter crescido., O caminho que uma string bruta percorreu até virar (ou não) uma tag. (+4 more)

### Community 81 - "winscreen.py"
Cohesion: 0.20
Nodes (5): parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., Regras sem prefixo procuram somente no executável.          Assim uma pasta cham, Instantâneo de ``video.conf`` e da lista de apps., Settings

### Community 82 - "context_overflow"
Cohesion: 0.67
Nodes (5): dateOf(), DayPicker(), fullLabel(), MemoryDay, monthLabel()

### Community 83 - "._start"
Cohesion: 0.24
Nodes (6): _JobObject, _Process, Path, Popen, Amarra os processos filhos ao ciclo de vida da API.      É o que o systemd conse, Um processo filho supervisionado.

### Community 84 - "test_main.py"
Cohesion: 0.24
Nodes (7): main(), _monitor_key(), Path, Identidade do monitor a partir do nome do arquivo (``..._mon1_DP-1.png``)., Motivo para não capturar agora, ou ``None`` se pode capturar., ScreenLoop, _thumbnail()

### Community 85 - "get_backend"
Cohesion: 0.36
Nodes (6): get_backend(), Devolve o backend do SO atual (memorizado).      ``force`` (``"linux"``/``"windo, main(), _measure_volume(), Path, Self-test de captura — rode isto ao trocar de sistema.      python -m app.captur

### Community 86 - ".snapshot"
Cohesion: 0.24
Nodes (8): _app_label(), _elapsed(), _focus_grace_remaining(), _long_elapsed(), Lê o sinal JSON que o ``winvideo`` reescreve a cada volta do laço.      Um arqui, Há quanto tempo a gravação longa corre, ou zero se não há nenhuma., Nome curto do app a partir de ``"<título> | <executável>"``., _read_video_flag()

### Community 87 - "filter_hallucinated_segments"
Cohesion: 0.11
Nodes (10): ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Pausar desabilita a unit: só parar valia até o próximo boot., LinuxIdlePauseTests, _pausable(), Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)., Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API. (+2 more)

### Community 88 - "hudsource.py"
Cohesion: 0.17
Nodes (3): Um clipe no disco com o sidecar do gravador e a linha do banco., Recodificar um arquivo que já cabe só pioraria a imagem., ``GET`` que dispara meio minuto de ffmpeg viraria timeout no navegador.

### Community 90 - ".grab_frame"
Cohesion: 0.09
Nodes (28): get_cleanup_settings(), apply_exact_game_durations(), days_pending_consolidation(), describe_tag_candidates(), game_activity_rows(), generate_hourly_summaries(), generate_summary(), main() (+20 more)

### Community 91 - "WasapiError"
Cohesion: 0.20
Nodes (6): ProcessLoopbackCapture, Falha numa chamada COM do WASAPI, com o HRESULT preservado., Loopback que inclui ou exclui a árvore de um processo do Windows., WasapiError, discord_process_id(), Retorna a raiz da árvore Discord.exe com mais processos descendentes.

### Community 92 - "context_overflow"
Cohesion: 0.22
Nodes (22): update_status(), exclusive_lock(), Helpers de runtime que funcionam igual em Linux e Windows.  Centraliza as poucas, Trava exclusiva e não-bloqueante sobre ``path``.      Retorna ``True`` se conseg, apply_pending(), can_install_now(), cancel(), check() (+14 more)

### Community 93 - "_LazyOle32"
Cohesion: 0.12
Nodes (12): api, TagDecision, TagEntry, TagPromotion, TagStatus, TagTestResult, TagVocabulary, OUTCOME (+4 more)

### Community 94 - "HoldDetectorTests"
Cohesion: 0.28
Nodes (5): _parse_max_geometry(), Path, Interpreta ``"1920x1080>"`` -> (1920, 1080, apenas_reduzir)., Dimensões finais respeitando ``MAX_GEOMETRY`` (mantém proporção)., _scaled_size()

### Community 97 - "winscreen.py"
Cohesion: 0.17
Nodes (12): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.      ``ut, read_shell_config(), _mic_filter(), Filtro ffmpeg do canal do microfone: supressão de ruído + portão de     volume m, _as_bool(), _as_float(), _as_int(), _parse_config() (+4 more)

### Community 98 - "services.py"
Cohesion: 0.20
Nodes (4): Uma unit supervisionada.      ``simple`` roda enquanto o serviço estiver ligado, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef

### Community 99 - ".active"
Cohesion: 0.05
Nodes (59): _as_float(), _as_ratio(), _clip_row(), Host, host_catalog(), light_filename(), light_state(), light_video_command() (+51 more)

### Community 100 - "devDependencies"
Cohesion: 0.33
Nodes (3): HudFrameRateTests, As três cadências existem por causa do custo de redesenhar.      Cada volta recr, Uma entrada de 0,26 s precisa de quadros suficientes para não escadear.

### Community 101 - "hudsource.py"
Cohesion: 0.16
Nodes (16): Nome estável para ``<título> | <executável>``.      Alguns jogos, especialmente, stable_app_label(), begin(), close_stale(), _ensure_schema(), finish(), heartbeat(), iso_time() (+8 more)

### Community 102 - "_LazyOle32"
Cohesion: 0.33
Nodes (3): MonitorResolutionTests, A resolução sugerida para um jogo novo é a física, não a lógica., Com ``dmSize`` errado o EnumDisplaySettingsW recusa a chamada.          No Windo

### Community 103 - "HudCollector"
Cohesion: 0.25
Nodes (5): HudCollector, ABC, Fonte do instantâneo da HUD., Sobe threads de coleta (no-op quando não houver)., Estado atual, já normalizado.

### Community 104 - ".feed"
Cohesion: 0.24
Nodes (8): Pico de um WAV PCM 16 bits, em dBFS. ``-inf`` vira o piso -99., A faixa está muda o bastante para transcrevê-la ser desperdício?      Numa sessã, track_is_silent(), track_peak_dbfs(), Faixas mudas não valem uma transcrição.      Numa sessão sem Discord a faixa del, -40 dBFS é fala baixa de verdade; pular isso perderia conversa., Na dúvida, transcreve: perder fala é pior que gastar tempo., SilentTrackTests

### Community 105 - "read_shell_config"
Cohesion: 0.29
Nodes (3): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas.

### Community 106 - ".test_an_unreadable_foreground_window_neither_starts_nor_advances_the_countdown"
Cohesion: 0.15
Nodes (14): bounded_video_range(), local_origin_only(), origin_allowed(), Se este caminho só faz sentido com o pipeline instalado., No Lumini, o que depende de IA responde 409 em vez de tentar.      Esconder os b, Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., Se o ``Host`` (ou a origem) descreve este servidor.      Além dos nomes configur, recusar_analise_no_lumini() (+6 more)

### Community 109 - "_Growth"
Cohesion: 0.22
Nodes (4): _Growth, _MeterTracker, Contabilidade temporal de uma fonte de áudio.      Guarda desde quando a fonte n, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo).

### Community 110 - ".action"
Cohesion: 0.29
Nodes (3): Arquivo de estado que o laço de vídeo cria enquanto controla as capturas.      M, (Re)inicia o swayidle apontando os eventos para o flag de idle., _video_pause_file()

### Community 111 - "matched_sensitive_pattern"
Cohesion: 0.29
Nodes (5): matched_sensitive_pattern(), Path, Lista de expressões de um arquivo de padrões, ignorando comentários., Primeiro padrão sensível (regex, case-insensitive) que casa com a janela.      M, read_patterns()

### Community 113 - "rebuild_voice_identity"
Cohesion: 0.32
Nodes (8): backfill_confirmed_voice_observations(), enroll_voice_identity(), _normalized_average(), Recalcula um perfil dando um único voto a cada gravação., rebuild_voice_identity(), SpeakerLabelUpdate, update_capture_speaker(), update_video_speaker()

### Community 114 - "LinuxHudCollector"
Cohesion: 0.20
Nodes (4): LinuxHudCollector, Estado derivado do laço bash e medidores lidos dos buses do PipeWire.      O ``b, Segmento sendo escrito agora pelo ``gpu-screen-recorder``., Janela em foco, com a mesma cadência do laço bash (2 s).          O sidecar ``.w

### Community 115 - "delete_voice_identity"
Cohesion: 0.07
Nodes (41): cancel_video_audio_track_job(), cancel_video_audio_tracks(), _delete_media_sidecars(), delete_video(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), media_version() (+33 more)

### Community 116 - "HudStatus"
Cohesion: 0.10
Nodes (21): HudDisplayModeTests, ResamplerTests, _alert_sound(), _demo_sequence(), Hud, HudSettings, log(), main() (+13 more)

### Community 117 - ".feed"
Cohesion: 0.29
Nodes (3): _FakeResponse, O host recusa com HTTP 200 e um texto no corpo; engolir isso deixaria         a, Resposta de host de arquivo: corpo em texto puro, sem rede envolvida.

### Community 118 - "LinuxAudioTapTests"
Cohesion: 0.40
Nodes (5): _count_markers(), Path, Coleta do estado que a HUD mostra, com um coletor por sistema.  Mesma divisão qu, Há quanto tempo o segmento em curso começou.      Vem do nome do arquivo, não do, _segment_elapsed()

### Community 119 - "WindowsStartupTests"
Cohesion: 0.40
Nodes (5): _attached_source(), _pulse_sources(), Lê PCM cru do monitor de um bus e acumula o pico.          Taxa baixa e um canal, Mapa id -> nome das fontes do PipeWire/Pulse., Fonte à qual o ``parec`` de ``client`` está realmente ligado.      Existe porque

### Community 120 - "._partial_segment"
Cohesion: 0.18
Nodes (10): _install_stop_handlers(), Atende todos os sinais de parada que o SO pode mandar.      No Windows o supervi, cut_head(), looks_blank(), main(), Gravação seletiva de jogos no Windows — porte de ``bin/game-video-loop``.  Mesma, Amostra um quadro e diz se o vídeo saiu chapado (preto/estático).      É a rede, Guarda só os primeiros ``seconds`` do arquivo, copiando os streams.      Cortar (+2 more)

### Community 121 - "multimodal_context"
Cohesion: 0.40
Nodes (5): As tags com alguma chance de serem a mesma coisa, e só elas.      Mandar o vocab, Forma canônica: sem acento, minúscula, hifenizada.      Mesma normalização do FT, _shortlist(), slugify(), _words()

### Community 123 - "stop_target_is_already_gone"
Cohesion: 0.09
Nodes (24): Uma unit transitória coletada equivale a um job já parado., stop_target_is_already_gone(), clear_call_metrics(), compact_saved_capture(), daily_narrative_target(), drain_pending(), known_voice_profiles(), last_call_metrics() (+16 more)

### Community 124 - "test_updater.py"
Cohesion: 0.40
Nodes (3): _ActivationHandler, GUID, Implementação mínima de IActivateAudioInterfaceCompletionHandler.

### Community 125 - "stop_target_is_already_gone"
Cohesion: 0.40
Nodes (4): _devmode_w(), _monitor_info_ex(), MONITORINFOEXW: o ``szDevice`` é o nome que o EnumDisplaySettings pede., DEVMODEW com a união de impressora/monitor como 16 bytes opacos.      Só ``dmPel

### Community 126 - "exige"
Cohesion: 1.00
Nodes (3): exige(), instalar-lumini.sh script, tem()

### Community 127 - "safe_research_query"
Cohesion: 0.50
Nodes (4): delete_voice_identity(), Volta uma amostra ao estado não identificado sem perder sua diarização., Remove um perfil incorreto e solta as amostras para nova classificação., _speaker_without_identity()

### Community 132 - "UpdateNotice.tsx"
Cohesion: 0.67
Nodes (3): request(), UpdateNotice(), UpdateStatus

## Knowledge Gaps
- **143 isolated node(s):** `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame`, `StorageCandidate`, `WebSource` (+138 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **27 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `filter_hallucinated_segments` to `ConfigTests`, `VideoSettings`, `SilentTrackTests`, `test_services.py`, `ActionResult`, `WindowsServiceManager`, `RemapToSourceTests`, `main.py`, `hud.py`, `_JobObject`, `winrecord.py`, `SpeechRegionTests`, `get_manager`, `CallMetricsTests`, `resolve_media_source`, `RegionGroupingTests`, `Path`, `ServiceManager`, `ollama_json`, `HudStateTests`, `local_origin_only`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `multimodal_context`, `LinuxAppRuleMatchTests`, `._start`, `services.py`, `devDependencies`, `_LazyOle32`, `.feed`, `multimodal_context`, `rebuild_voice_identity`, `delete_voice_identity`, `HudStatus`, `.feed`, `stop_target_is_already_gone`?**
  _High betweenness centrality (0.129) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `package.json`, `VideoWindowTest`, `VideoSettings`, `read_shell_config`, `.test_an_unreadable_foreground_window_neither_starts_nor_advances_the_countdown`, `filter_hallucinated_segments`, `audio_intelligence.py`, `.grab_frame`, `stop_target_is_already_gone`, `trim_video`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `filter_hallucinated_segments` to `ConfigTests`, `VideoSettings`, `SilentTrackTests`, `test_services.py`, `ActionResult`, `runtime_dir`, `RemapToSourceTests`, `main.py`, `hud.py`, `_JobObject`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `Path`, `ServiceManager`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `multimodal_context`, `LinuxAppRuleMatchTests`, `devDependencies`, `_LazyOle32`, `.feed`, `multimodal_context`, `.action`, `HudStatus`, `.feed`, `stop_target_is_already_gone`?**
  _High betweenness centrality (0.081) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `VideoWindowTest`) actually correct?**
  _`ConfigTests` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 79 inferred relationships involving `ActionResult` (e.g. with `AudioSettings` and `CleanupSettings`) actually correct?**
  _`ActionResult` has 79 INFERRED edges - model-reasoned connections that need verification._
- **Are the 40 inferred relationships involving `VideoLoop` (e.g. with `ClipAudioTrackTests` and `HoldDetectorTests`) actually correct?**
  _`VideoLoop` has 40 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` to the rest of the system?**
  _143 weakly-connected nodes found - possible documentation gaps or missing edges._