# Graph Report - lume  (2026-09-21)

## Corpus Check
- 65 files · ~122,761 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1938 nodes · 4745 edges · 101 communities (87 shown, 14 thin omitted)
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
- HoldDetectorTests
- toggle-video-hud
- lume-audio-diag
- _Growth
- services.py
- LinuxHudCollector
- multimodal_context
- _event_fields
- Monitor

## God Nodes (most connected - your core abstractions)
1. `ConfigTests` - 117 edges
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

## Communities (101 total, 14 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.04
Nodes (15): Estado operacional do gravador, separado da mera configuração ativa., selective_video_status(), _activity_groups(), Separa por aplicativo e continuidade; mudanças de título não quebram a sessão., ConfigTests, Path, O laço do Linux conta tempo pela mesma porta que o gravador do Windows., Uma queda no meio da partida não pode contar o tempo até agora. (+7 more)

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
Cohesion: 0.09
Nodes (17): CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco.          Retorna ``N, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Prepara o roteamento de áudio (no-op onde não for necessário). (+9 more)

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
Cohesion: 0.12
Nodes (23): audio_file(), _audio_streams(), capture_speaker_sample(), delete_voice_identity(), import_video(), process_file(), ProcessFileRequest, datetime (+15 more)

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
Cohesion: 0.11
Nodes (38): HudDisplayModeTests, HudEventContractTests, HudFrameRateTests, ImageDiffTests, LinuxAudioTrackTests, ObsWindowSpecTests, PrivacyTests, Testes das peças que tornam o app portável entre Linux e Windows.  Rodam nos doi (+30 more)

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
Cohesion: 0.19
Nodes (9): Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg.  O laço de captura do Linux usa, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar., Diferença percentual entre dois arquivos de imagem. (+1 more)

### Community 20 - "main.py"
Cohesion: 0.06
Nodes (62): _apply_storage_runtime(), _apply_video_runtime(), capture_change_test_frames(), capture_frames(), CleanupSettings, compare_screen_change_test(), ContextUpdate, create_video_marker() (+54 more)

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
Cohesion: 0.22
Nodes (5): _ActivationHandler, GUID, _LazyOle32, Resolve ``ole32`` só no primeiro uso.      ``ctypes.windll`` não existe fora do, Implementação mínima de IActivateAudioInterfaceCompletionHandler.

### Community 29 - "Path"
Cohesion: 0.06
Nodes (52): atomic_write(), atomic_write_if_changed(), cancel_video_audio_track_job(), cancel_video_audio_track_jobs(), cancel_video_audio_tracks(), captured_video_session(), _delete_media_sidecars(), delete_video() (+44 more)

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
Cohesion: 0.06
Nodes (37): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., _alert_sound(), _assert_topmost(), _declare_dpi_aware() (+29 more)

### Community 35 - "_call"
Cohesion: 0.23
Nodes (18): _AudioClientActivationParams, _Blob, _call(), _check(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints() (+10 more)

### Community 37 - "_JobObject"
Cohesion: 0.22
Nodes (5): _JobObject, Amarra os processos filhos ao ciclo de vida da API.      É o que o systemd con, Return seconds since the last real keyboard or mouse input on Windows., Combine selective-video and user-idle pauses without racing them.          Aud, windows_idle_seconds()

### Community 38 - "run"
Cohesion: 0.18
Nodes (13): concat_videos(), foreground_details(), log(), looks_blank(), main(), media_duration(), Path, Gravação seletiva de jogos no Windows — porte de ``bin/game-video-loop``.  Mesma (+5 more)

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
Cohesion: 0.13
Nodes (11): blend(), corner_position(), HudPanel, Mistura duas cores ``#rrggbb``.      O Canvas do tkinter não tem canal alfa por, Um painel desenhado num monitor., Corta pela largura real do texto, não por contagem de caracteres.          A HUD, Barra mínima. O evento entra por baixo empurrando o conteúdo normal.          Nã, Faixa de confirmação: desliza da esquerda, acende e recolhe. (+3 more)

### Community 48 - "get_manager"
Cohesion: 0.14
Nodes (14): _as_bool(), _as_float(), _as_int(), main(), _monitor_key(), _parse_config(), Path, Laço contínuo de captura de telas — porte de ``bin/capture-loop`` para Python. (+6 more)

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
Nodes (33): audio_channel_count(), audio_stream_count(), clear_call_metrics(), compact_processed_audio(), compact_saved_capture(), describe_screen(), filter_hallucinated_segments(), known_voice_profiles() (+25 more)

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
Nodes (6): Não sei que janela é essa" não é "o usuário saiu do jogo".          ``GetForegro, ``jogo``, ``na-tela`` ou ``fora`` — a mesma pergunta do laço Linux.          Trê, Atualiza o prazo publicado para a HUD e informa se ele venceu., Grava uma sessão lógica, possivelmente dividida em segmentos., Mantém Replay Buffer ativo e salva somente quando F8 for pressionado., VideoLoop

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers.      M, Um fluxo de captura: microfone padrão ou loopback da saída padrão.      A saída, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio).          Um, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "trim_video"
Cohesion: 0.09
Nodes (57): get_cleanup_settings(), _activity_app(), _activity_batch_summary(), _activity_image(), adaptive_web_research(), analyze_screen_sequence(), analyze_video_chapter(), context_overflow() (+49 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.15
Nodes (10): Escreve o sinal de atividade lido pela HUD.          Fica separado de :meth:`_su, Registra um acontecimento pontual e publica na hora.          A sequência é o qu, Confirma uma ação aceita sem depender da interface estar em foco., Segurar: abre a gravação longa e, na segurada seguinte, a fecha., Anota o instante atual da gravação.          Os marcadores ficam em memória e só, Guarda o pré-roll e começa a gravar em paralelo ao Replay Buffer., Encerra a gravação longa e emenda o pré-roll na frente dela., Janela, sessão e marcadores ao lado do arquivo, como nos segmentos. (+2 more)

### Community 64 - "HudStateTests"
Cohesion: 0.19
Nodes (7): HudStateTests, As regras que decidem se a captura está saudável.      Rodam nos dois sistemas d, Segurou o atalho: já não é "armado", é gravando de verdade., Ficar calado é normal; confundir com falha destrói a confiança na HUD., evaluate(), Traduz um instantâneo em alertas e num veredito único.      Função pura: mesma e, worst_level()

### Community 65 - "local_origin_only"
Cohesion: 0.18
Nodes (12): bounded_video_range(), local_origin_only(), origin_allowed(), preserve_video(), process_video(), Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., remote_client_allowed(), safe_video_path() (+4 more)

### Community 67 - "VideoWindowTest"
Cohesion: 0.48
Nodes (4): test_video_window(), VideoWindowTest, O teste de janela do Lume precisa responder o mesmo que o gravador.      Se ele, VideoWindowTestEndpointTests

### Community 68 - "HudPlacementTests"
Cohesion: 0.29
Nodes (5): HudPlacementTests, Onde a HUD desenha, dado o arranjo de monitores., Com um monitor só, "no outro monitor" tem que recair sobre este., choose_monitors(), Monitores que devem receber um painel.      Função pura para poder ser testada s

### Community 69 - "PromptSettingsTests"
Cohesion: 0.13
Nodes (4): PromptSettingsTests, Os prompts sao editaveis, mas nao a ponto de quebrar a analise., Uma variavel esquecida na ficha sumiria do texto sem ninguem notar., Um JSON quebrado nao pode parar a fila inteira.

### Community 70 - "WindowsHudCollector"
Cohesion: 0.14
Nodes (10): _attached_source(), log(), _pulse_sources(), Medidores e engate lidos do OBS dedicado, estado lido do sinal de vídeo., Lê PCM cru do monitor de um bus e acumula o pico.          Taxa baixa e um canal, Mapa id -> nome das fontes do PipeWire/Pulse., Fonte à qual o ``parec`` de ``client`` está realmente ligado.      Existe porque, WindowsHudCollector (+2 more)

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
Cohesion: 0.20
Nodes (5): parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., Regras sem prefixo procuram somente no executável.          Assim uma pasta cham, Instantâneo de ``video.conf`` e da lista de apps., Settings

### Community 76 - "_Growth"
Cohesion: 0.38
Nodes (6): ActivitiesView(), ActivityCard(), Frame, searchable(), time(), ActivitySession

### Community 77 - "pad_to_segmentation_window"
Cohesion: 0.24
Nodes (8): Pico de um WAV PCM 16 bits, em dBFS. ``-inf`` vira o piso -99., A faixa está muda o bastante para transcrevê-la ser desperdício?      Numa sessã, track_is_silent(), track_peak_dbfs(), Faixas mudas não valem uma transcrição.      Numa sessão sem Discord a faixa del, -40 dBFS é fala baixa de verdade; pular isso perderia conversa., Na dúvida, transcreve: perder fala é pior que gastar tempo., SilentTrackTests

### Community 78 - "multimodal_context"
Cohesion: 0.60
Nodes (4): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows.  Executado com ``pythonw.exe`` pe

### Community 79 - "Path"
Cohesion: 0.12
Nodes (15): LinuxCaptureModeTests, LinuxFocusVerdictTests, Path, Sair do jogo é uma coisa; o KWin mudar de ideia por um segundo é outra.      O l, Move o foco para ``window``, com o jogo continuando aberto atrás., O outro lado de segurar a sessão: o jogo fechar tem de acabar com ela., A correção não pode virar "grava para sempre".          Quem abre o navegador po, Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver. (+7 more)

### Community 81 - "winscreen.py"
Cohesion: 0.22
Nodes (6): Path, Lista de expressões de um arquivo de padrões, ignorando comentários., Nome estável para ``<título> | <executável>``.      Alguns jogos, especialmente, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados.          ``, read_patterns(), stable_app_label()

### Community 82 - "context_overflow"
Cohesion: 0.67
Nodes (5): dateOf(), DayPicker(), fullLabel(), MemoryDay, monthLabel()

### Community 83 - "._start"
Cohesion: 0.36
Nodes (4): _Process, Path, Popen, Um processo filho supervisionado.

### Community 84 - "test_main.py"
Cohesion: 0.08
Nodes (17): Uma unit transitória coletada equivale a um job já parado., stop_target_is_already_gone(), apply_exact_game_durations(), daily_narrative_target(), game_activity_rows(), merge_source_transcripts(), merge_transcript_sources(), private_context_terms() (+9 more)

### Community 85 - "_video_pause_file"
Cohesion: 0.29
Nodes (3): Arquivo de estado que o laço de vídeo cria enquanto controla as capturas., (Re)inicia o swayidle apontando os eventos para o flag de idle., _video_pause_file()

### Community 86 - ".snapshot"
Cohesion: 0.19
Nodes (13): _app_label(), _count_markers(), _elapsed(), _focus_grace_remaining(), _long_elapsed(), Path, Coleta do estado que a HUD mostra, com um coletor por sistema.  Mesma divisão qu, Lê o sinal JSON que o ``winvideo`` reescreve a cada volta do laço.      Um arqui (+5 more)

### Community 87 - "filter_hallucinated_segments"
Cohesion: 0.43
Nodes (3): O sinal de atividade tem um significado só, e ele é caro de errar.      Enquanto, Dois marcadores seguidos têm o mesmo rótulo; só a sequência os separa., VideoActivityFlagTests

### Community 88 - "hudsource.py"
Cohesion: 0.12
Nodes (10): get_collector(), HudCollector, LinuxHudCollector, ABC, Fonte do instantâneo da HUD., Sobe threads de coleta (no-op quando não houver)., Estado atual, já normalizado., Estado derivado do laço bash e medidores lidos dos buses do PipeWire.      O ``b (+2 more)

### Community 89 - "media_source_key"
Cohesion: 0.10
Nodes (29): initialize(), _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., delete_unkept_raw_media(), detach_video_from_session(), enqueue_unprocessed() (+21 more)

### Community 90 - "capture_frames"
Cohesion: 0.33
Nodes (3): matched_sensitive_pattern(), Primeiro padrão sensível (regex, case-insensitive) que casa com a janela.      M, Motivo para não capturar agora, ou ``None`` se pode capturar.

### Community 91 - "WasapiError"
Cohesion: 0.18
Nodes (6): ProcessLoopbackCapture, Falha numa chamada COM do WASAPI, com o HRESULT preservado., Loopback que inclui ou exclui a árvore de um processo do Windows., WasapiError, WAVEFORMATEXTENSIBLE, OSError

### Community 94 - "HoldDetectorTests"
Cohesion: 0.20
Nodes (3): HoldDetectorTests, Toque e segurada a partir dos eventos crus do teclado.      O atalho do KDE só c, O formato do ``input_event`` é contrato do kernel, não detalhe nosso.          E

### Community 97 - "_Growth"
Cohesion: 0.22
Nodes (4): _Growth, _MeterTracker, Contabilidade temporal de uma fonte de áudio.      Guarda desde quando a fonte n, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo).

### Community 98 - "services.py"
Cohesion: 0.16
Nodes (7): _pipeline(), _python(), Gerenciamento de serviços independente de sistema operacional.  No Linux o sys, Uma unit supervisionada.      ``simple`` roda enquanto o serviço estiver ligad, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef

### Community 100 - "LinuxHudCollector"
Cohesion: 0.19
Nodes (11): Valores de ``tela.conf`` relevantes para a captura de um frame., ScreenConfig, Janela em foco, com a mesma cadência do laço bash (2 s).          O sidecar ``.w, get_backend(), Seleção automática do backend de captura conforme o sistema operacional.  Uso:, Devolve o backend do SO atual (memorizado).      ``force`` (``"linux"``/``"windo, Path, main() (+3 more)

### Community 106 - "Monitor"
Cohesion: 0.13
Nodes (10): LinuxAudioTapTests, Um app com vários streams tem de entrar inteiro na faixa de sistema.      O ``pw, c1 e c2 não podem carregar a mesma voz, nem o mesmo som duas vezes., Monitor, Um monitor físico: rótulo estável + geometria em pixels do desktop., Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga.          Dois formatos d, Dispositivo dshow capaz de gravar a saída, se algum existir.          Só diagnós (+2 more)

## Knowledge Gaps
- **118 isolated node(s):** `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame`, `StorageCandidate`, `WebSource` (+113 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **14 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `SilentTrackTests` to `ConfigTests`, `VideoLoop`, `VideoSettings`, `test_services.py`, `ActionResult`, `WindowsServiceManager`, `RemapToSourceTests`, `main.py`, `hud.py`, `Path`, `pipeline.py`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `ServiceManager`, `HudStateTests`, `local_origin_only`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `pad_to_segmentation_window`, `Path`, `LinuxAppRuleMatchTests`, `._start`, `test_main.py`, `filter_hallucinated_segments`, `HoldDetectorTests`, `services.py`, `Monitor`?**
  _High betweenness centrality (0.128) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `local_origin_only`, `VideoWindowTest`, `multimodal_context`, `VideoSettings`, `SilentTrackTests`, `test_main.py`, `Path`, `audio_intelligence.py`, `ollama_json`?**
  _High betweenness centrality (0.072) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `SilentTrackTests` to `ConfigTests`, `VideoSettings`, `test_services.py`, `runtime_dir`, `RemapToSourceTests`, `main.py`, `pipeline.py`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `ServiceManager`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `pad_to_segmentation_window`, `Path`, `LinuxAppRuleMatchTests`, `test_main.py`, `_video_pause_file`, `filter_hallucinated_segments`, `HoldDetectorTests`, `services.py`, `Monitor`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `VideoWindowTest`) actually correct?**
  _`ConfigTests` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 61 inferred relationships involving `ActionResult` (e.g. with `CleanupSettings` and `ContextUpdate`) actually correct?**
  _`ActionResult` has 61 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `VideoLoop` (e.g. with `HoldDetectorTests` and `HudDisplayModeTests`) actually correct?**
  _`VideoLoop` has 35 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` to the rest of the system?**
  _118 weakly-connected nodes found - possible documentation gaps or missing edges._