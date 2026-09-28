# Graph Report - lume  (2026-08-30)

## Corpus Check
- 60 files · ~102,199 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1702 nodes · 4143 edges · 98 communities (78 shown, 20 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 406 edges (avg confidence: 0.51)
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
- base.py
- obs.py
- record
- Handoff: Lume — app de memória de tela & áudio
- VideoLoop
- post
- Lume no Windows
- track_is_silent
- test_services.py
- .action
- WindowsServiceManager
- game-video-loop
- runtime_dir
- AGENTS.md
- HudSnapshot
- hudsource.py
- Path
- install-audio-intelligence
- audio_intelligence.py
- capture-frame
- hud.py
- add-video-marker
- WasapiError
- install-captura-dia.sh
- LinuxHudCollector
- editing.py
- audio-bus.sh
- src-backup-2026-08-09/api.ts
- src-backup-2026-08-09/main.tsx
- get
- _call
- capture-loop
- main.py
- delete_voice_identity
- ._start
- grava-audio.sh
- install-lume.sh
- install-user.sh
- prompts.py
- winrecord.py
- trim_video
- WindowsHudCollector
- media_source_key
- run
- recover_json_from_thinking
- _event_fields
- connect
- ServiceManager
- src/main.tsx
- App
- videoTime
- filter_hallucinated_segments
- WasapiCapture
- videoTime
- generate_visual_activities
- pipeline.py
- App
- HudPanel
- HudStateTests
- safe_video_path
- .test_the_whole_entry_gets_many_frames
- HudPlacementTests
- PromptSettingsTests
- HudCollector
- thumbnail
- _Growth
- EditingFolderTests
- trim_video
- windows_startup.py
- _resolve
- .tick
- ActionResult
- get_backend
- winscreen.py
- VideoActivityFlagTests
- HudFrameRateTests
- ScreenLoop
- HudStatus
- game_activity_rows
- multimodal_context
- stop_target_is_already_gone
- hudsource.py
- _scaled_size
- .test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis
- .test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time
- _event_fields
- daily_narrative_target
- toggle-video-hud
- lume-audio-diag
- UnitResolutionTests

## God Nodes (most connected - your core abstractions)
1. `ActionResult` - 90 edges
2. `ConfigTests` - 90 edges
3. `connect()` - 89 edges
4. `VideoLoop` - 57 edges
5. `SystemdServiceManager` - 56 edges
6. `HudSnapshot` - 54 edges
7. `Monitor` - 49 edges
8. `Hud` - 47 edges
9. `Meter` - 47 edges
10. `WindowsCaptureBackend` - 43 edges

## Surprising Connections (you probably didn't know these)
- `delete_video_marker()` --calls--> `connect()`  [EXTRACTED]
  app/backend/main.py → app/backend/database.py
- `screen_sequence_result()` --calls--> `connect()`  [EXTRACTED]
  app/backend/main.py → app/backend/database.py
- `ScreenSettings` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `SensitiveWindows` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `PipelineRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py

## Import Cycles
- None detected.

## Communities (98 total, 20 thin omitted)

### Community 1 - "src/api.ts"
Cohesion: 0.06
Nodes (33): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, EditingEntry, EditingResult (+25 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "base.py"
Cohesion: 0.08
Nodes (19): CaptureBackend, format_video_app_rule(), ABC, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco.          Retorna ``N, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável. (+11 more)

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
Cohesion: 0.06
Nodes (29): parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., log(), MarkerHotkey, Atalhos globais no Windows, registrados fora de qualquer janela.  No Linux o ata, Atalho global que chama ``on_press`` a cada acionamento., _install_stop_handlers(), Atende todos os sinais de parada que o SO pode mandar.      No Windows o supervi (+21 more)

### Community 9 - "post"
Cohesion: 0.33
Nodes (7): get_video_settings(), set_video_settings(), VideoSettings, Salvar as preferências não pode apagar chaves silenciosamente.      ``set_video_, Uma instalação antiga não pode ficar sem HUD nem quebrar ao salvar., VideoSettingsRoundTripTests, BackgroundTasks

### Community 10 - "Lume no Windows"
Cohesion: 0.07
Nodes (24): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+16 more)

### Community 11 - "track_is_silent"
Cohesion: 0.29
Nodes (6): A faixa está muda o bastante para transcrevê-la ser desperdício?      Numa sessã, track_is_silent(), Faixas mudas não valem uma transcrição.      Numa sessão sem Discord a faixa del, -40 dBFS é fala baixa de verdade; pular isso perderia conversa., Na dúvida, transcreve: perder fala é pior que gastar tempo., SilentTrackTests

### Community 12 - "test_services.py"
Cohesion: 0.10
Nodes (34): HudDisplayModeTests, HudFrameRateTests, ImageDiffTests, LinuxAudioTrackTests, ObsWindowSpecTests, PrivacyTests, Testes das peças que tornam o app portável entre Linux e Windows.  Rodam nos doi, As três cadências existem por causa do custo de redesenhar.      Cada volta recr (+26 more)

### Community 13 - ".action"
Cohesion: 0.17
Nodes (6): Arquivo de estado que o laço de vídeo cria enquanto controla as capturas., (Re)inicia o swayidle apontando os eventos para o flag de idle., Anota que a captura deve (ou não) voltar na próxima abertura do Lume., Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., _unknown(), _video_pause_file()

### Community 14 - "WindowsServiceManager"
Cohesion: 0.21
Nodes (3): Supervisor: mantém os processos de captura vivos e agenda o processamento., Combine selective-video and user-idle pauses without racing them.          Aud, WindowsServiceManager

### Community 15 - "game-video-loop"
Cohesion: 0.23
Nodes (12): game-video-loop script, add_marker(), cleanup(), confirmation_sound(), finish_segment(), graphical_session_ready(), is_selected_app(), log() (+4 more)

### Community 16 - "runtime_dir"
Cohesion: 0.23
Nodes (10): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows.  Centraliza as poucas, Diretório para arquivos efêmeros (locks, estado volátil).      Linux usa ``XDG_R, Arquivo que sinaliza "estou gravando vídeo agora".      É como o laço de vídeo p, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``.      Retorna ``True`` se conseg, runtime_dir() (+2 more)

### Community 18 - "HudSnapshot"
Cohesion: 0.33
Nodes (3): Voltar os tempos do bloco para o eixo do áudio original.      É a parte que, err, Fim antes do início quebraria a ordenação e a legenda., RemapToSourceTests

### Community 19 - "hudsource.py"
Cohesion: 0.11
Nodes (22): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., delete_capture(), delete_capture_file(), delete_file(), delete_video() (+14 more)

### Community 20 - "Path"
Cohesion: 0.08
Nodes (36): capture_days(), CleanupSettings, ContextUpdate, create_video_session(), delete_video_marker(), get_cleanup_settings(), get_sensitive_windows(), list_voice_identities() (+28 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.17
Nodes (20): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+12 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "hud.py"
Cohesion: 0.07
Nodes (24): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., _alert_sound(), _declare_dpi_aware(), ease_in_cubic() (+16 more)

### Community 27 - "WasapiError"
Cohesion: 0.25
Nodes (3): _ActivationHandler, GUID, Implementação mínima de IActivateAudioInterfaceCompletionHandler.

### Community 29 - "LinuxHudCollector"
Cohesion: 0.14
Nodes (23): atomic_write(), atomic_write_if_changed(), _delete_media_sidecars(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), get_storage_settings(), migrate_legacy_cache_file() (+15 more)

### Community 30 - "editing.py"
Cohesion: 0.11
Nodes (34): available_name(), chapter_seconds(), clip_markers(), EditingError, entries(), folder(), frames_to_timecode(), inside_folder() (+26 more)

### Community 31 - "audio-bus.sh"
Cohesion: 0.30
Nodes (15): make_null_sink(), selected_mic(), setup(), audio-bus.sh script, sink_exists(), source_exists(), status(), system_stream_nodes() (+7 more)

### Community 32 - "src-backup-2026-08-09/api.ts"
Cohesion: 0.07
Nodes (26): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+18 more)

### Community 33 - "src-backup-2026-08-09/main.tsx"
Cohesion: 0.10
Nodes (5): EditableVideoSpeaker, icons, labels, Panel, View

### Community 34 - "get"
Cohesion: 0.12
Nodes (15): EventFrame, Um quadro da animação de confirmação.      ``reveal`` é o quanto o evento tomou, Aplica queda suave às barras, para o medidor não piscar., O que caracteriza uma mudança que precisa ser anunciada.          De propósito n, Reage a um acontecimento novo vindo do laço de vídeo., Estado atual, já normalizado., _disk_alerts(), evaluate() (+7 more)

### Community 35 - "_call"
Cohesion: 0.23
Nodes (18): _AudioClientActivationParams, _Blob, _call(), _check(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints() (+10 more)

### Community 37 - "main.py"
Cohesion: 0.11
Nodes (24): row_dict(), _audio_channels(), cancel_entire_queue(), capture_speed_stats(), delete_unprocessed_files(), generate_hourly_now(), generate_summary_now(), hourly_timeline() (+16 more)

### Community 38 - "delete_voice_identity"
Cohesion: 0.16
Nodes (18): audio_file(), _audio_streams(), capture_speaker_sample(), delete_voice_identity(), import_video(), datetime, Volta uma amostra ao estado não identificado sem perder sua diarização., Remove um perfil incorreto e solta as amostras para nova classificação. (+10 more)

### Community 39 - "._start"
Cohesion: 0.36
Nodes (4): _Process, Path, Popen, Um processo filho supervisionado.

### Community 43 - "prompts.py"
Cohesion: 0.21
Nodes (17): get_prompts(), reset_prompt(), active_template(), listing(), _overrides(), payload(), PromptError, PromptSpec (+9 more)

### Community 45 - "winrecord.py"
Cohesion: 0.13
Nodes (15): dbfs(), default_endpoint_name(), Nome do endpoint padrão, ou ``None`` se não houver nenhum., Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), main(), _mix(), _multichannel() (+7 more)

### Community 46 - "trim_video"
Cohesion: 0.36
Nodes (5): Trechos ``(início, fim)`` em segundos onde há som acima do limiar.      Função p, speech_regions(), Detecção dos trechos com som, sobre amostras sintéticas., A folga não pode gerar tempo negativo nem passar do fim do áudio., SpeechRegionTests

### Community 47 - "WindowsHudCollector"
Cohesion: 0.05
Nodes (36): Nome estável para ``<título> | <executável>``.      Alguns jogos, especialmente, stable_app_label(), _app_label(), _attached_source(), _count_markers(), _elapsed(), _focus_grace_remaining(), get_collector() (+28 more)

### Community 48 - "media_source_key"
Cohesion: 0.38
Nodes (7): backfill_confirmed_voice_observations(), enroll_voice_identity(), Recalcula um perfil dando um único voto a cada gravação., rebuild_voice_identity(), SpeakerLabelUpdate, update_capture_speaker(), update_video_speaker()

### Community 49 - "run"
Cohesion: 0.27
Nodes (4): CallMetricsTests, Sem separar carga, leitura do prompt e geracao, encurtar prompt e chute., ollama_json repete a chamada para consertar JSON; isso custa tempo., Um audio nao passa pelo Ollama; herdar a medicao de uma tela mentiria.

### Community 51 - "_event_fields"
Cohesion: 0.31
Nodes (5): group_regions(), Agrupa trechos vizinhos em blocos que caibam numa janela do whisper.      Dois t, Blocos que enchem uma janela do whisper sem esticar o eixo do tempo.      O whis, É o teto que impede um erro de 1 s virar 20 s ao voltar ao original., RegionGroupingTests

### Community 52 - "connect"
Cohesion: 0.10
Nodes (42): connect(), initialize(), backfill_video_session_durations(), capture_payload(), captures(), create_video_marker(), delete_unkept_raw_media(), delete_video_session() (+34 more)

### Community 53 - "ServiceManager"
Cohesion: 0.10
Nodes (12): ABC, Executa ``start``/``stop``/``restart``/``try-restart``/``enable``/``disable``., Horário configurado do processamento noturno e se está ativo., Reprograma o processamento noturno., Dispara um job avulso sob um nome de unit, para poder cancelá-lo depois., Reinicia a própria interface (usado ao trocar o local dos dados)., Chamado quando a API sobe., Chamado quando a API desce. (+4 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.05
Nodes (17): EditingFolder, CAPTION_LABELS, CAPTION_ORDER, CapturaTab, ContextMenuAction, dayViews, EditableVideoSpeaker, EditingFolderModal() (+9 more)

### Community 55 - "App"
Cohesion: 0.17
Nodes (13): Capture, CleanupSettings, PipelineQueue, ScreenSequenceResult, Status, uploadVideo(), VideoSettings, analysisAverage() (+5 more)

### Community 56 - "videoTime"
Cohesion: 0.14
Nodes (16): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SessionCard(), sessionDuration() (+8 more)

### Community 57 - "filter_hallucinated_segments"
Cohesion: 0.29
Nodes (3): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas.

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers.      M, Um fluxo de captura: microfone padrão ou loopback da saída padrão.      A saída, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio).          Um, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 61 - "pipeline.py"
Cohesion: 0.18
Nodes (29): analyze_video_chapter(), audio_channel_count(), audio_stream_count(), compact_processed_audio(), describe_long_video(), describe_video(), extract_adaptive_keyframes(), format_video_time() (+21 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.11
Nodes (14): _assert_topmost(), blend(), HudPanel, _make_overlay(), HWND real de um ``Toplevel`` do tkinter., Deixa a janela flutuando, sem foco, sem clique e fora do Alt+Tab., Reafirma o topo da pilha.      Um jogo entrando em tela cheia reordena o z-order, Mistura duas cores ``#rrggbb``.      O Canvas do tkinter não tem canal alfa por (+6 more)

### Community 64 - "HudStateTests"
Cohesion: 0.18
Nodes (7): HudStateTests, As regras que decidem se a captura está saudável.      Rodam nos dois sistemas d, Ficar calado é normal; confundir com falha destrói a confiança na HUD., _demo_sequence(), Estados fabricados percorridos em laço, para ajustar a HUD sem jogo., Meter, Uma fonte de áudio vista pela HUD.      ``present`` e ``peak_db`` respondem perg

### Community 65 - "safe_video_path"
Cohesion: 0.25
Nodes (8): bounded_video_range(), local_origin_only(), origin_allowed(), Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., remote_client_allowed(), video_file(), Request, StreamingResponse

### Community 67 - ".test_the_whole_entry_gets_many_frames"
Cohesion: 0.13
Nodes (20): _apply_storage_runtime(), _apply_video_runtime(), cancel_pipeline(), cancel_queue_item(), cancel_screen_sequence(), cancel_video_analysis(), cancel_video_session(), capture_action() (+12 more)

### Community 68 - "HudPlacementTests"
Cohesion: 0.25
Nodes (5): HudPlacementTests, Onde a HUD desenha, dado o arranjo de monitores., Com um monitor só, "no outro monitor" tem que recair sobre este., choose_monitors(), Monitores que devem receber um painel.      Função pura para poder ser testada s

### Community 69 - "PromptSettingsTests"
Cohesion: 0.13
Nodes (4): PromptSettingsTests, Os prompts sao editaveis, mas nao a ponto de quebrar a analise., Uma variavel esquecida na ficha sumiria do texto sem ninguem notar., Um JSON quebrado nao pode parar a fila inteira.

### Community 70 - "HudCollector"
Cohesion: 0.13
Nodes (16): open_editing_folder(), probe_video_audio_tracks(), process_video(), Popen, Lista os stems reproduzíveis, omitindo a mixagem geral do OBS., Remuxa stems fora da requisição HTTP e permite interromper a leitura pesada., Abre a pasta no gerenciador de arquivos da maquina que roda o Lume., safe_video_path() (+8 more)

### Community 71 - "thumbnail"
Cohesion: 0.19
Nodes (9): Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg.  O laço de captura do Linux usa, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar., Diferença percentual entre dois arquivos de imagem. (+1 more)

### Community 72 - "_Growth"
Cohesion: 0.25
Nodes (17): clear_call_metrics(), compact_saved_capture(), describe_screen(), known_voice_profiles(), last_call_metrics(), monitor_key(), ollama_chat(), process_pending() (+9 more)

### Community 74 - "EditingFolderTests"
Cohesion: 0.11
Nodes (5): EditingFolderTests, A pasta de edicao troca garimpo de arquivo por nome legivel e EDL., 12,5 s a 60 fps sao 750 quadros depois do inicio da timeline., O hardlink segura os bytes, entao apagar por engano so confundiria., O segundo trecho comeca onde o primeiro acaba, e o EDL acompanha.

### Community 75 - "trim_video"
Cohesion: 0.13
Nodes (14): cancel_video_audio_track_job(), cancel_video_audio_track_jobs(), cancel_video_audio_tracks(), lifespan(), migrate_legacy_media_caches(), probe_video_duration(), Substitui um clipe pelo intervalo escolhido e invalida a análise antiga., Lê a duração do contêiner localmente; não envolve modelos ou análise. (+6 more)

### Community 76 - "windows_startup.py"
Cohesion: 0.60
Nodes (4): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows.  Executado com ``pythonw.exe`` pe

### Community 77 - "_resolve"
Cohesion: 0.22
Nodes (7): _JobObject, _pipeline(), _python(), Gerenciamento de serviços independente de sistema operacional.  No Linux o sys, Amarra os processos filhos ao ciclo de vida da API.      É o que o systemd con, Return seconds since the last real keyboard or mouse input on Windows., windows_idle_seconds()

### Community 78 - ".tick"
Cohesion: 0.29
Nodes (5): matched_sensitive_pattern(), Path, Lista de expressões de um arquivo de padrões, ignorando comentários., Primeiro padrão sensível (regex, case-insensitive) que casa com a janela.      M, read_patterns()

### Community 79 - "ActionResult"
Cohesion: 0.08
Nodes (14): ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, LinuxIdlePauseTests, _pausable(), Path, Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO). (+6 more)

### Community 80 - "get_backend"
Cohesion: 0.31
Nodes (7): Janela em foco, com a mesma cadência do laço bash (2 s).          O sidecar ``.w, get_backend(), Devolve o backend do SO atual (memorizado).      ``force`` (``"linux"``/``"windo, main(), _measure_volume(), Path, Self-test de captura — rode isto ao trocar de sistema.      python -m app.captur

### Community 81 - "winscreen.py"
Cohesion: 0.20
Nodes (10): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.      ``ut, read_shell_config(), _as_bool(), _as_float(), _as_int(), _parse_config(), Laço contínuo de captura de telas — porte de ``bin/capture-loop`` para Python., Lê o ``tela.conf`` (formato ``CHAVE=valor`` do shell). (+2 more)

### Community 84 - "ScreenLoop"
Cohesion: 0.22
Nodes (7): main(), _monitor_key(), Path, Identidade do monitor a partir do nome do arquivo (``..._mon1_DP-1.png``)., Motivo para não capturar agora, ou ``None`` se pode capturar., ScreenLoop, _thumbnail()

### Community 85 - "HudStatus"
Cohesion: 0.40
Nodes (4): Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, WAVEFORMATEXTENSIBLE, OSError

### Community 89 - "hudsource.py"
Cohesion: 0.50
Nodes (4): _parse_max_geometry(), Interpreta ``"1920x1080>"`` -> (1920, 1080, apenas_reduzir)., Dimensões finais respeitando ``MAX_GEOMETRY`` (mantém proporção)., _scaled_size()

### Community 90 - "_scaled_size"
Cohesion: 0.13
Nodes (19): capture_change_test_frames(), capture_frames(), compare_screen_change_test(), get_screen_settings(), parse_shell_config(), privacy_decision(), Estado operacional do gravador, separado da mera configuração ativa., Janela ativa e o motivo para não capturar, se houver.      A mesma regra nos doi (+11 more)

### Community 93 - "_event_fields"
Cohesion: 0.31
Nodes (5): HudEventContractTests, O evento cruza dois processos por um arquivo; o formato é um contrato.      O ``, Um tipo sem estilo seria um evento invisível — falha silenciosa., _event_fields(), Extrai o acontecimento pontual publicado pelo laço de vídeo.      A idade vem do

### Community 94 - "daily_narrative_target"
Cohesion: 0.10
Nodes (28): _activity_groups(), _activity_image(), adaptive_web_research(), analyze_screen_sequence(), apply_exact_game_durations(), daily_narrative_target(), generate_visual_activities(), merge_source_transcripts() (+20 more)

### Community 98 - "UnitResolutionTests"
Cohesion: 0.20
Nodes (4): Uma unit supervisionada.      ``simple`` roda enquanto o serviço estiver ligad, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef

## Knowledge Gaps
- **106 isolated node(s):** `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame`, `StorageCandidate`, `WebSource` (+101 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **20 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `ConfigTests`, `post`, `track_is_silent`, `test_services.py`, `.action`, `WindowsServiceManager`, `HudSnapshot`, `Path`, `hud.py`, `LinuxHudCollector`, `._start`, `trim_video`, `media_source_key`, `run`, `_event_fields`, `ServiceManager`, `HudStateTests`, `.test_the_whole_entry_gets_many_frames`, `HudPlacementTests`, `PromptSettingsTests`, `HudCollector`, `EditingFolderTests`, `trim_video`, `_resolve`, `stop_target_is_already_gone`, `_scaled_size`, `_event_fields`, `daily_narrative_target`, `UnitResolutionTests`?**
  _High betweenness centrality (0.127) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `safe_video_path`, `post`, `ActionResult`, `recover_json_from_thinking`, `VideoActivityFlagTests`, `Path`, `game_activity_rows`, `audio_intelligence.py`, `stop_target_is_already_gone`, `multimodal_context`, `.test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis`, `.test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time`, `daily_narrative_target`, `filter_hallucinated_segments`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `ActionResult` to `ConfigTests`, `post`, `track_is_silent`, `test_services.py`, `.action`, `runtime_dir`, `HudSnapshot`, `hud.py`, `trim_video`, `run`, `_event_fields`, `ServiceManager`, `HudStateTests`, `.test_the_whole_entry_gets_many_frames`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `_resolve`, `_event_fields`, `daily_narrative_target`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 55 inferred relationships involving `ActionResult` (e.g. with `CleanupSettings` and `ContextUpdate`) actually correct?**
  _`ActionResult` has 55 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `ActionResult`) actually correct?**
  _`ConfigTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 29 inferred relationships involving `VideoLoop` (e.g. with `HudDisplayModeTests` and `HudEventAnimationTests`) actually correct?**
  _`VideoLoop` has 29 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` to the rest of the system?**
  _106 weakly-connected nodes found - possible documentation gaps or missing edges._