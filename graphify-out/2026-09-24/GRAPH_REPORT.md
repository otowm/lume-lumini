# Graph Report - lume  (2026-09-23)

## Corpus Check
- 65 files · ~123,634 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1944 nodes · 4755 edges · 107 communities (92 shown, 15 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 507 edges (avg confidence: 0.51)
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

## God Nodes (most connected - your core abstractions)
1. `ConfigTests` - 120 edges
2. `ActionResult` - 97 edges
3. `connect()` - 92 edges
4. `VideoLoop` - 68 edges
5. `SystemdServiceManager` - 63 edges
6. `HudSnapshot` - 59 edges
7. `Monitor` - 54 edges
8. `Hud` - 52 edges
9. `Meter` - 52 edges
10. `WindowsCaptureBackend` - 48 edges

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

## Communities (107 total, 15 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.04
Nodes (12): ConfigTests, Path, O laço do Linux conta tempo pela mesma porta que o gravador do Windows., Uma queda no meio da partida não pode contar o tempo até agora., O alvo puxava as capturas por `Wants=`, habilitadas ou não., A média vem do tempo real medido, não do intervalo entre capturas., Sem amostra do tipo pendente, um palpite atrapalharia mais que ajudar., O ``-c:a copy`` só sobrevive se o contêiner aceitar o codec de origem. (+4 more)

### Community 1 - "src/api.ts"
Cohesion: 0.06
Nodes (32): ActivityFrame, AnalysisTrace, api, AudioEvent, DaySummary, EditingEntry, EditingResult, HourSummary (+24 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "LinuxCaptureBackend"
Cohesion: 0.06
Nodes (31): CaptureBackend, matched_sensitive_pattern(), ABC, Path, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Primeiro padrão sensível (regex, case-insensitive) que casa com a janela.      M, Contrato que Linux e Windows implementam., Nome estável para ``<título> | <executável>``.      Alguns jogos, especialmente (+23 more)

### Community 5 - "obs.py"
Cohesion: 0.06
Nodes (58): any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), _encode_field(), ensure_scene(), find_installation() (+50 more)

### Community 6 - "record"
Cohesion: 0.17
Nodes (10): ProcessLoopbackCapture, Loopback que inclui ou exclui a árvore de um processo do Windows., Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record() (+2 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.14
Nodes (20): audio_file(), _audio_streams(), capture_speaker_sample(), delete_voice_identity(), import_video(), process_file(), ProcessFileRequest, datetime (+12 more)

### Community 9 - "VideoSettings"
Cohesion: 0.29
Nodes (8): get_video_settings(), set_video_settings(), VideoSettings, Salvar as preferências não pode apagar chaves silenciosamente.      ``set_video_, Uma instalação antiga não pode ficar sem HUD nem quebrar ao salvar., VideoSettingsRoundTripTests, format_video_app_rule(), BackgroundTasks

### Community 10 - "Lume no Windows"
Cohesion: 0.06
Nodes (28): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, Atalho de gravação (F8), captura-dia (+20 more)

### Community 11 - "SilentTrackTests"
Cohesion: 0.11
Nodes (9): ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Pausar desabilita a unit: só parar valia até o próximo boot., LinuxIdlePauseTests, _pausable(), Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)., Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API. (+1 more)

### Community 12 - "test_services.py"
Cohesion: 0.12
Nodes (35): HudDisplayModeTests, HudEventContractTests, HudFrameRateTests, ImageDiffTests, LinuxAudioTrackTests, ObsWindowSpecTests, PrivacyTests, Testes das peças que tornam o app portável entre Linux e Windows.  Rodam nos doi (+27 more)

### Community 13 - "ActionResult"
Cohesion: 0.07
Nodes (46): connect(), row_dict(), _audio_channels(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_screen_sequence(), cancel_video_analysis() (+38 more)

### Community 14 - "WindowsServiceManager"
Cohesion: 0.18
Nodes (5): Supervisor: mantém os processos de captura vivos e agenda o processamento., Anota que a captura deve (ou não) voltar na próxima abertura do Lume., Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., _unknown(), WindowsServiceManager

### Community 15 - "game-video-loop"
Cohesion: 0.13
Nodes (33): game-video-loop script, active_monitor(), add_long_marker(), add_marker(), adopt_video(), begin_game_session(), cleanup(), collect_clips() (+25 more)

### Community 16 - "runtime_dir"
Cohesion: 0.23
Nodes (10): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows.  Centraliza as poucas, Diretório para arquivos efêmeros (locks, estado volátil).      Linux usa ``XDG_R, Arquivo que sinaliza "estou gravando vídeo agora".      É como o laço de vídeo p, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``.      Retorna ``True`` se conseg, runtime_dir() (+2 more)

### Community 18 - "RemapToSourceTests"
Cohesion: 0.33
Nodes (3): Voltar os tempos do bloco para o eixo do áudio original.      É a parte que, err, Fim antes do início quebraria a ordenação e a legenda., RemapToSourceTests

### Community 19 - "get"
Cohesion: 0.25
Nodes (11): capture_change_test_frames(), capture_frames(), compare_screen_change_test(), get_screen_settings(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver.      A mesma regra nos doi, Captura um conjunto de frames com a configuração atual., screen_change_percent() (+3 more)

### Community 20 - "main.py"
Cohesion: 0.06
Nodes (63): _apply_storage_runtime(), _apply_video_runtime(), atomic_write(), atomic_write_if_changed(), cancel_video_audio_track_jobs(), CleanupSettings, ContextUpdate, create_video_marker() (+55 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.10
Nodes (26): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+18 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "hud.py"
Cohesion: 0.32
Nodes (8): backfill_confirmed_voice_observations(), enroll_voice_identity(), _normalized_average(), Recalcula um perfil dando um único voto a cada gravação., rebuild_voice_identity(), SpeakerLabelUpdate, update_capture_speaker(), update_video_speaker()

### Community 27 - "WasapiError"
Cohesion: 0.25
Nodes (3): _ActivationHandler, GUID, Implementação mínima de IActivateAudioInterfaceCompletionHandler.

### Community 29 - "Path"
Cohesion: 0.07
Nodes (44): cancel_video_audio_track_job(), cancel_video_audio_tracks(), _delete_media_sidecars(), delete_video(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), migrate_legacy_cache_file() (+36 more)

### Community 30 - "editing.py"
Cohesion: 0.10
Nodes (39): available_name(), chapter_seconds(), clip_markers(), EditingError, entries(), folder(), frames_to_timecode(), inside_folder() (+31 more)

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
Nodes (24): _alert_sound(), _declare_dpi_aware(), _demo_sequence(), ease_in_cubic(), ease_out_cubic(), Hud, HudSettings, log() (+16 more)

### Community 35 - "_call"
Cohesion: 0.23
Nodes (18): _AudioClientActivationParams, _Blob, _call(), _check(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints() (+10 more)

### Community 37 - "_JobObject"
Cohesion: 0.22
Nodes (5): _JobObject, Amarra os processos filhos ao ciclo de vida da API.      É o que o systemd con, Return seconds since the last real keyboard or mouse input on Windows., Combine selective-video and user-idle pauses without racing them.          Aud, windows_idle_seconds()

### Community 38 - "run"
Cohesion: 0.15
Nodes (15): parse_video_app_rule(), Lista de expressões de um arquivo de padrões, ignorando comentários., Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., read_patterns(), _install_stop_handlers(), Atende todos os sinais de parada que o SO pode mandar.      No Windows o supervi, concat_videos(), looks_blank() (+7 more)

### Community 39 - "connect"
Cohesion: 0.17
Nodes (12): daemon_flag(), HotkeyDaemon, keyboard_devices(), log(), main(), parse_key(), Path, Atalho global que distingue **toque** de **segurada**, lendo o evdev.  O atalho (+4 more)

### Community 43 - "prompts.py"
Cohesion: 0.21
Nodes (17): get_prompts(), reset_prompt(), active_template(), listing(), _overrides(), payload(), PromptError, PromptSpec (+9 more)

### Community 45 - "winrecord.py"
Cohesion: 0.13
Nodes (15): dbfs(), default_endpoint_name(), Nome do endpoint padrão, ou ``None`` se não houver nenhum., Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), main(), _mix(), _multichannel() (+7 more)

### Community 46 - "SpeechRegionTests"
Cohesion: 0.36
Nodes (5): Trechos ``(início, fim)`` em segundos onde há som acima do limiar.      Função p, speech_regions(), Detecção dos trechos com som, sobre amostras sintéticas., A folga não pode gerar tempo negativo nem passar do fim do áudio., SpeechRegionTests

### Community 47 - ".snapshot"
Cohesion: 0.12
Nodes (17): _assert_topmost(), blend(), EventFrame, HudPanel, _make_overlay(), HWND real de um ``Toplevel`` do tkinter., Deixa a janela flutuando, sem foco, sem clique e fora do Alt+Tab., Reafirma o topo da pilha.      Um jogo entrando em tela cheia reordena o z-order (+9 more)

### Community 48 - "get_manager"
Cohesion: 0.18
Nodes (10): _as_bool(), _as_float(), _as_int(), main(), _parse_config(), Laço contínuo de captura de telas — porte de ``bin/capture-loop`` para Python., Lê o ``tela.conf`` (formato ``CHAVE=valor`` do shell)., Instantâneo do ``tela.conf``, relido quando o arquivo muda no disco. (+2 more)

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
Cohesion: 0.10
Nodes (61): _activity_batch_summary(), _activity_image(), adaptive_web_research(), analyze_screen_sequence(), analyze_video_chapter(), audio_channel_count(), audio_stream_count(), clear_call_metrics() (+53 more)

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
Cohesion: 0.14
Nodes (6): Não sei que janela é essa" não é "o usuário saiu do jogo".          ``GetForegro, ``jogo``, ``na-tela`` ou ``fora`` — a mesma pergunta do laço Linux.          Trê, Atualiza o prazo publicado para a HUD e informa se ele venceu., Grava uma sessão lógica, possivelmente dividida em segmentos., Mantém Replay Buffer ativo e salva somente quando F8 for pressionado., VideoLoop

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers.      M, Um fluxo de captura: microfone padrão ou loopback da saída padrão.      A saída, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio).          Um, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "trim_video"
Cohesion: 0.09
Nodes (23): get_cleanup_settings(), apply_exact_game_durations(), daily_narrative_target(), days_pending_consolidation(), drain_pending(), game_activity_rows(), generate_hourly_summaries(), generate_summary() (+15 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.17
Nodes (11): log(), Escreve o sinal de atividade lido pela HUD.          Fica separado de :meth:`_su, Registra um acontecimento pontual e publica na hora.          A sequência é o qu, Confirma uma ação aceita sem depender da interface estar em foco., Segurar: abre a gravação longa e, na segurada seguinte, a fecha., Anota o instante atual da gravação.          Os marcadores ficam em memória e só, Guarda o pré-roll e começa a gravar em paralelo ao Replay Buffer., Encerra a gravação longa e emenda o pré-roll na frente dela. (+3 more)

### Community 64 - "HudStateTests"
Cohesion: 0.19
Nodes (7): HudStateTests, As regras que decidem se a captura está saudável.      Rodam nos dois sistemas d, Segurou o atalho: já não é "armado", é gravando de verdade., Ficar calado é normal; confundir com falha destrói a confiança na HUD., evaluate(), Traduz um instantâneo em alertas e num veredito único.      Função pura: mesma e, worst_level()

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
Cohesion: 0.21
Nodes (3): log(), Medidores e engate lidos do OBS dedicado, estado lido do sinal de vídeo., WindowsHudCollector

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
Cohesion: 0.16
Nodes (9): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., ease_out_back(), event_animation(), Passa um pouco do alvo e volta.      É o que separa "apareceu" de "chegou": sem (+1 more)

### Community 78 - "multimodal_context"
Cohesion: 0.60
Nodes (4): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows.  Executado com ``pythonw.exe`` pe

### Community 79 - "Path"
Cohesion: 0.10
Nodes (18): LinuxCaptureModeTests, LinuxFocusVerdictTests, Path, Sair do jogo é uma coisa; o KWin mudar de ideia por um segundo é outra.      O l, Move o foco para ``window``, com o jogo continuando aberto atrás., O outro lado de segurar a sessão: o jogo fechar tem de acabar com ela., A correção não pode virar "grava para sempre".          Quem abre o navegador po, Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver. (+10 more)

### Community 81 - "winscreen.py"
Cohesion: 0.25
Nodes (7): _attached_source(), _pulse_sources(), Lê PCM cru do monitor de um bus e acumula o pico.          Taxa baixa e um canal, Mapa id -> nome das fontes do PipeWire/Pulse., Fonte à qual o ``parec`` de ``client`` está realmente ligado.      Existe porque, Converte multiplicador linear (0..1) para dBFS, com piso em silêncio., to_db()

### Community 82 - "context_overflow"
Cohesion: 0.67
Nodes (5): dateOf(), DayPicker(), fullLabel(), MemoryDay, monthLabel()

### Community 83 - "._start"
Cohesion: 0.36
Nodes (4): _Process, Path, Popen, Um processo filho supervisionado.

### Community 84 - "test_main.py"
Cohesion: 0.08
Nodes (18): Uma unit transitória coletada equivale a um job já parado., stop_target_is_already_gone(), merge_source_transcripts(), merge_transcript_sources(), monitor_key(), private_context_terms(), Pico de um WAV PCM 16 bits, em dBFS. ``-inf`` vira o piso -99., A faixa está muda o bastante para transcrevê-la ser desperdício?      Numa sessã (+10 more)

### Community 85 - "_video_pause_file"
Cohesion: 0.29
Nodes (3): Arquivo de estado que o laço de vídeo cria enquanto controla as capturas., (Re)inicia o swayidle apontando os eventos para o flag de idle., _video_pause_file()

### Community 86 - ".snapshot"
Cohesion: 0.17
Nodes (10): _app_label(), _elapsed(), _event_fields(), _focus_grace_remaining(), _long_elapsed(), Lê o sinal JSON que o ``winvideo`` reescreve a cada volta do laço.      Um arqui, Há quanto tempo a gravação longa corre, ou zero se não há nenhuma., Nome curto do app a partir de ``"<título> | <executável>"``. (+2 more)

### Community 87 - "filter_hallucinated_segments"
Cohesion: 0.11
Nodes (16): _count_markers(), get_collector(), HudCollector, LinuxHudCollector, ABC, Path, Coleta do estado que a HUD mostra, com um coletor por sistema.  Mesma divisão qu, Fonte do instantâneo da HUD. (+8 more)

### Community 88 - "hudsource.py"
Cohesion: 0.16
Nodes (10): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas., Devolve os tempos do áudio condensado para o eixo do áudio original.      Sem is, Transcreve um WAV mono 16 kHz, pulando os trechos sem som.      Cada trecho vira, _read_whisper_json(), remap_to_source(), _whisper_batch() (+2 more)

### Community 89 - "media_source_key"
Cohesion: 0.10
Nodes (29): initialize(), _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., captured_video_session(), delete_unkept_raw_media(), enqueue_unprocessed() (+21 more)

### Community 90 - "capture_frames"
Cohesion: 0.19
Nodes (9): Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg.  O laço de captura do Linux usa, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar., Diferença percentual entre dois arquivos de imagem. (+1 more)

### Community 91 - "WasapiError"
Cohesion: 0.40
Nodes (4): Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, WAVEFORMATEXTENSIBLE, OSError

### Community 92 - "context_overflow"
Cohesion: 0.67
Nodes (3): context_overflow(), O Ollama recusa o lote inteiro quando as imagens não cabem no ``num_ctx``., Exception

### Community 94 - "HoldDetectorTests"
Cohesion: 0.20
Nodes (3): HoldDetectorTests, Toque e segurada a partir dos eventos crus do teclado.      O atalho do KDE só c, O formato do ``input_event`` é contrato do kernel, não detalhe nosso.          E

### Community 97 - "_Growth"
Cohesion: 0.22
Nodes (4): _Growth, _MeterTracker, Contabilidade temporal de uma fonte de áudio.      Guarda desde quando a fonte n, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo).

### Community 98 - "services.py"
Cohesion: 0.16
Nodes (7): _pipeline(), _python(), Gerenciamento de serviços independente de sistema operacional.  No Linux o sys, Uma unit supervisionada.      ``simple`` roda enquanto o serviço estiver ligad, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef

### Community 99 - ".active"
Cohesion: 0.32
Nodes (5): _monitor_key(), Path, Identidade do monitor a partir do nome do arquivo (``..._mon1_DP-1.png``)., Motivo para não capturar agora, ou ``None`` se pode capturar., _thumbnail()

### Community 100 - "pipeline_queue"
Cohesion: 0.29
Nodes (7): capture_speed_stats(), pipeline_queue(), pipeline_summary_job(), queue_eta_seconds(), Média recente de análise por tipo, para estimar a duração da fila.      Só as úl, Estimativa da fila restante; a execução do worker é sequencial., Expose the worker's actual plan; older workers report only saved evidence.

### Community 101 - "LinuxAudioTapTests"
Cohesion: 0.47
Nodes (3): LinuxAudioTapTests, Um app com vários streams tem de entrar inteiro na faixa de sistema.      O ``pw, c1 e c2 não podem carregar a mesma voz, nem o mesmo som duas vezes.

### Community 102 - "_activity_groups"
Cohesion: 0.40
Nodes (4): _activity_app(), _activity_groups(), Prefere a identidade capturada da janela aos nomes variáveis da IA., Separa por aplicativo e continuidade; mudanças de título não quebram a sessão.

### Community 103 - "foreground_details"
Cohesion: 0.40
Nodes (3): foreground_details(), Título, classe e executável da janela em foco — o que o OBS precisa     para eng, Janela atual e resultado das regras usando campos separados.

### Community 106 - "Monitor"
Cohesion: 0.10
Nodes (9): Monitor, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Um monitor físico: rótulo estável + geometria em pixels do desktop., Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga.          Dois formatos d, Dispositivo dshow capaz de gravar a saída, se algum existir.          Só diagnós, argv do gravador WASAPI (ver :mod:`app.capture.winrecord`).          Não é ffmpe (+1 more)

## Knowledge Gaps
- **118 isolated node(s):** `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame`, `StorageCandidate`, `WebSource` (+113 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **15 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `SilentTrackTests` to `ConfigTests`, `VideoLoop`, `VideoSettings`, `test_services.py`, `ActionResult`, `WindowsServiceManager`, `RemapToSourceTests`, `get`, `main.py`, `hud.py`, `Path`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `ServiceManager`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `pad_to_segmentation_window`, `Path`, `LinuxAppRuleMatchTests`, `._start`, `test_main.py`, `HoldDetectorTests`, `services.py`, `LinuxAudioTapTests`?**
  _High betweenness centrality (0.131) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `SilentTrackTests` to `ConfigTests`, `VideoSettings`, `test_services.py`, `runtime_dir`, `RemapToSourceTests`, `main.py`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `ServiceManager`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `pad_to_segmentation_window`, `Path`, `LinuxAppRuleMatchTests`, `test_main.py`, `_video_pause_file`, `HoldDetectorTests`, `services.py`, `LinuxAudioTapTests`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `local_origin_only`, `VideoWindowTest`, `_activity_groups`, `VideoSettings`, `SilentTrackTests`, `test_main.py`, `audio_intelligence.py`, `hudsource.py`, `trim_video`, `ollama_json`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `VideoWindowTest`) actually correct?**
  _`ConfigTests` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 61 inferred relationships involving `ActionResult` (e.g. with `CleanupSettings` and `ContextUpdate`) actually correct?**
  _`ActionResult` has 61 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `VideoLoop` (e.g. with `HoldDetectorTests` and `HudDisplayModeTests`) actually correct?**
  _`VideoLoop` has 35 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` to the rest of the system?**
  _118 weakly-connected nodes found - possible documentation gaps or missing edges._