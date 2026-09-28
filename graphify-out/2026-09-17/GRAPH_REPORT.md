# Graph Report - lume  (2026-09-03)

## Corpus Check
- 60 files · ~105,618 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1745 nodes · 4266 edges · 113 communities (89 shown, 24 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 443 edges (avg confidence: 0.51)
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
- ollama_json
- WasapiCapture
- videoTime
- generate_visual_activities
- Settings
- App
- HudPanel
- HudStateTests
- safe_video_path
- .test_the_whole_entry_gets_many_frames
- HudPlacementTests
- PromptSettingsTests
- HudCollector
- _install_stop_handlers
- get_backend
- EditingFolderTests
- trim_video
- windows_startup.py
- _resolve
- .tick
- ActionResult
- get_backend
- winscreen.py
- process_specific
- HudFrameRateTests
- ScreenLoop
- HudStatus
- matched_sensitive_pattern
- trim_video
- stop_target_is_already_gone
- hudsource.py
- _scaled_size
- filter_hallucinated_segments
- HudFrameRateTests
- _event_fields
- daily_narrative_target
- toggle-video-hud
- lume-audio-diag
- ._partial_segment
- UnitResolutionTests
- LinuxHudCollector
- summary_source_rows
- foreground_details
- speaker_profiles
- windows_startup.py
- captured_video_session
- _scaled_size
- ._dshow_loopback
- context_overflow
- .test_a_day_that_fails_to_consolidate_does_not_abort_the_whole_run
- .test_opus_stems_go_to_a_container_that_accepts_them
- .test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis
- .test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time
- .test_recording_keeps_the_mix_ahead_of_the_isolated_tracks

## God Nodes (most connected - your core abstractions)
1. `ConfigTests` - 97 edges
2. `ActionResult` - 93 edges
3. `connect()` - 89 edges
4. `SystemdServiceManager` - 59 edges
5. `VideoLoop` - 59 edges
6. `HudSnapshot` - 56 edges
7. `Monitor` - 51 edges
8. `Hud` - 49 edges
9. `Meter` - 49 edges
10. `WindowsCaptureBackend` - 45 edges

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

## Communities (113 total, 24 thin omitted)

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
Cohesion: 0.10
Nodes (14): CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco.          Retorna ``N, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Prepara o roteamento de áudio (no-op onde não for necessário). (+6 more)

### Community 5 - "obs.py"
Cohesion: 0.06
Nodes (59): any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), _encode_field(), ensure_scene(), find_installation() (+51 more)

### Community 6 - "record"
Cohesion: 0.17
Nodes (10): ProcessLoopbackCapture, Loopback que inclui ou exclui a árvore de um processo do Windows., Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record() (+2 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.17
Nodes (6): log(), Janela atual e resultado das regras usando campos separados., Escreve o sinal de atividade lido pela HUD.          Fica separado de :meth:`_su, Atualiza o prazo publicado para a HUD e informa se ele venceu., Grava uma sessão lógica, possivelmente dividida em segmentos., Mantém Replay Buffer ativo e salva somente quando F8 for pressionado.

### Community 9 - "post"
Cohesion: 0.43
Nodes (4): VideoSettings, Salvar as preferências não pode apagar chaves silenciosamente.      ``set_video_, Uma instalação antiga não pode ficar sem HUD nem quebrar ao salvar., VideoSettingsRoundTripTests

### Community 10 - "Lume no Windows"
Cohesion: 0.07
Nodes (24): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+16 more)

### Community 11 - "track_is_silent"
Cohesion: 0.24
Nodes (8): Pico de um WAV PCM 16 bits, em dBFS. ``-inf`` vira o piso -99., A faixa está muda o bastante para transcrevê-la ser desperdício?      Numa sessã, track_is_silent(), track_peak_dbfs(), Faixas mudas não valem uma transcrição.      Numa sessão sem Discord a faixa del, -40 dBFS é fala baixa de verdade; pular isso perderia conversa., Na dúvida, transcreve: perder fala é pior que gastar tempo., SilentTrackTests

### Community 12 - "test_services.py"
Cohesion: 0.10
Nodes (22): HudEventContractTests, ImageDiffTests, LinuxAudioTrackTests, ObsWindowSpecTests, PrivacyTests, Testes das peças que tornam o app portável entre Linux e Windows.  Rodam nos doi, O evento cruza dois processos por um arquivo; o formato é um contrato.      O ``, O identificador de janela do OBS é ``título:classe:executável``.      Um título (+14 more)

### Community 14 - "WindowsServiceManager"
Cohesion: 0.08
Nodes (19): _JobObject, _Process, Path, Popen, Arquivo de estado que o laço de vídeo cria enquanto controla as capturas., (Re)inicia o swayidle apontando os eventos para o flag de idle., Uma unit supervisionada.      ``simple`` roda enquanto o serviço estiver ligad, Amarra os processos filhos ao ciclo de vida da API.      É o que o systemd con (+11 more)

### Community 15 - "game-video-loop"
Cohesion: 0.20
Nodes (17): game-video-loop script, add_marker(), cleanup(), collect_clips(), confirmation_sound(), finish_clip_session(), finish_segment(), graphical_session_ready() (+9 more)

### Community 16 - "runtime_dir"
Cohesion: 0.16
Nodes (17): cancel_entire_queue(), pipeline_status(), exclusive_lock(), pipeline_pause_flag(), Path, Helpers de runtime que funcionam igual em Linux e Windows.  Centraliza as poucas, Diretório para arquivos efêmeros (locks, estado volátil).      Linux usa ``XDG_R, Arquivo que sinaliza "estou gravando vídeo agora".      É como o laço de vídeo p (+9 more)

### Community 18 - "HudSnapshot"
Cohesion: 0.33
Nodes (3): Voltar os tempos do bloco para o eixo do áudio original.      É a parte que, err, Fim antes do início quebraria a ordenação e a legenda., RemapToSourceTests

### Community 19 - "hudsource.py"
Cohesion: 0.24
Nodes (4): log(), MarkerHotkey, Atalhos globais no Windows, registrados fora de qualquer janela.  No Linux o ata, Atalho global que chama ``on_press`` a cada acionamento.

### Community 20 - "Path"
Cohesion: 0.09
Nodes (37): atomic_write(), CleanupSettings, ContextUpdate, create_video_marker(), create_video_session(), get_sensitive_windows(), list_voice_identities(), MarkerCreate (+29 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.17
Nodes (20): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+12 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "hud.py"
Cohesion: 0.09
Nodes (20): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., _assert_topmost(), _declare_dpi_aware(), ease_in_cubic() (+12 more)

### Community 27 - "WasapiError"
Cohesion: 0.25
Nodes (3): _ActivationHandler, GUID, Implementação mínima de IActivateAudioInterfaceCompletionHandler.

### Community 29 - "LinuxHudCollector"
Cohesion: 0.08
Nodes (41): atomic_write_if_changed(), _delete_media_sidecars(), delete_video(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), get_storage_settings(), migrate_legacy_cache_file() (+33 more)

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
Cohesion: 0.10
Nodes (22): HudDisplayModeTests, ResamplerTests, StableAppLabelTests, _alert_sound(), _demo_sequence(), Hud, HudSettings, log() (+14 more)

### Community 35 - "_call"
Cohesion: 0.23
Nodes (18): _AudioClientActivationParams, _Blob, _call(), _check(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints() (+10 more)

### Community 37 - "main.py"
Cohesion: 0.16
Nodes (16): _apply_storage_runtime(), _apply_video_runtime(), cancel_pipeline(), cancel_queue_item(), cancel_screen_sequence(), cancel_video_analysis(), cancel_video_session(), capture_action() (+8 more)

### Community 38 - "delete_voice_identity"
Cohesion: 0.14
Nodes (20): audio_file(), _audio_streams(), capture_speaker_sample(), delete_voice_identity(), import_video(), process_file(), ProcessFileRequest, datetime (+12 more)

### Community 39 - "._start"
Cohesion: 0.11
Nodes (24): enqueue_unprocessed(), generate_hourly_now(), generate_summary_now(), get_schedule(), get_video_settings(), lifespan(), list_videos(), migrate_legacy_media_caches() (+16 more)

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
Cohesion: 0.29
Nodes (6): _app_label(), _elapsed(), _focus_grace_remaining(), Lê o sinal JSON que o ``winvideo`` reescreve a cada volta do laço.      Um arqui, Nome curto do app a partir de ``"<título> | <executável>"``., _read_video_flag()

### Community 48 - "media_source_key"
Cohesion: 0.14
Nodes (12): Variação de 5 níveis é ruído de compressão, não mudança de tela., parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg.  O laço de captura do Linux usa, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar. (+4 more)

### Community 49 - "run"
Cohesion: 0.27
Nodes (4): CallMetricsTests, Sem separar carga, leitura do prompt e geracao, encurtar prompt e chute., ollama_json repete a chamada para consertar JSON; isso custa tempo., Um audio nao passa pelo Ollama; herdar a medicao de uma tela mentiria.

### Community 50 - "recover_json_from_thinking"
Cohesion: 0.18
Nodes (22): initialize(), detach_video_from_session(), get_cleanup_settings(), Retira um trecho da sessão sem apagar o vídeo nem sua análise., discover(), generate_hourly_summaries(), generate_summary(), generate_visual_activities() (+14 more)

### Community 51 - "_event_fields"
Cohesion: 0.31
Nodes (5): group_regions(), Agrupa trechos vizinhos em blocos que caibam numa janela do whisper.      Dois t, Blocos que enchem uma janela do whisper sem esticar o eixo do tempo.      O whis, É o teto que impede um erro de 1 s virar 20 s ao voltar ao original., RegionGroupingTests

### Community 52 - "connect"
Cohesion: 0.20
Nodes (26): analyze_video_chapter(), audio_channel_count(), audio_stream_count(), compact_processed_audio(), describe_long_video(), describe_video(), extract_adaptive_keyframes(), format_video_time() (+18 more)

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

### Community 57 - "ollama_json"
Cohesion: 0.21
Nodes (13): _activity_image(), analyze_screen_sequence(), describe_screen(), ollama_json(), parse_json_response(), process_screen_sequence_job(), datetime, Falas do áudio que estava sendo gravado perto do instante de um print. (+5 more)

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers.      M, Um fluxo de captura: microfone padrão ou loopback da saída padrão.      A saída, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio).          Um, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "generate_visual_activities"
Cohesion: 0.12
Nodes (27): connect(), row_dict(), _audio_channels(), capture_days(), capture_payload(), captures(), delete_capture(), delete_capture_file() (+19 more)

### Community 61 - "Settings"
Cohesion: 0.27
Nodes (3): Regras sem prefixo procuram somente no executável.          Assim uma pasta cham, Instantâneo de ``video.conf`` e da lista de apps., Settings

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.15
Nodes (12): blend(), EventFrame, HudPanel, Mistura duas cores ``#rrggbb``.      O Canvas do tkinter não tem canal alfa por, Um quadro da animação de confirmação.      ``reveal`` é o quanto o evento tomou, Um painel desenhado num monitor., Corta pela largura real do texto, não por contagem de caracteres.          A HUD, Barra mínima. O evento entra por baixo empurrando o conteúdo normal.          Nã (+4 more)

### Community 64 - "HudStateTests"
Cohesion: 0.15
Nodes (12): HudStateTests, Ficar calado é normal; confundir com falha destrói a confiança na HUD., As regras que decidem se a captura está saudável.      Rodam nos dois sistemas d, Alert, _disk_alerts(), evaluate(), Meter, _meter_alerts() (+4 more)

### Community 65 - "safe_video_path"
Cohesion: 0.25
Nodes (8): bounded_video_range(), local_origin_only(), origin_allowed(), Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., remote_client_allowed(), video_file(), Request, StreamingResponse

### Community 67 - ".test_the_whole_entry_gets_many_frames"
Cohesion: 0.48
Nodes (4): test_video_window(), VideoWindowTest, O teste de janela do Lume precisa responder o mesmo que o gravador.      Se ele, VideoWindowTestEndpointTests

### Community 68 - "HudPlacementTests"
Cohesion: 0.23
Nodes (6): HudPlacementTests, Onde a HUD desenha, dado o arranjo de monitores., Com um monitor só, "no outro monitor" tem que recair sobre este., choose_monitors(), corner_position(), Monitores que devem receber um painel.      Função pura para poder ser testada s

### Community 69 - "PromptSettingsTests"
Cohesion: 0.13
Nodes (4): PromptSettingsTests, Os prompts sao editaveis, mas nao a ponto de quebrar a analise., Uma variavel esquecida na ficha sumiria do texto sem ninguem notar., Um JSON quebrado nao pode parar a fila inteira.

### Community 70 - "HudCollector"
Cohesion: 0.26
Nodes (3): log(), Medidores e engate lidos do OBS dedicado, estado lido do sinal de vídeo., WindowsHudCollector

### Community 71 - "_install_stop_handlers"
Cohesion: 0.23
Nodes (8): _install_stop_handlers(), Atende todos os sinais de parada que o SO pode mandar.      No Windows o supervi, main(), _monitor_key(), Path, Identidade do monitor a partir do nome do arquivo (``..._mon1_DP-1.png``)., ScreenLoop, _thumbnail()

### Community 72 - "get_backend"
Cohesion: 0.23
Nodes (9): Valores de ``tela.conf`` relevantes para a captura de um frame., ScreenConfig, get_backend(), Devolve o backend do SO atual (memorizado).      ``force`` (``"linux"``/``"windo, Path, main(), _measure_volume(), Path (+1 more)

### Community 74 - "EditingFolderTests"
Cohesion: 0.11
Nodes (5): EditingFolderTests, A pasta de edicao troca garimpo de arquivo por nome legivel e EDL., 12,5 s a 60 fps sao 750 quadros depois do inicio da timeline., O hardlink segura os bytes, entao apagar por engano so confundiria., O segundo trecho comeca onde o primeiro acaba, e o EDL acompanha.

### Community 75 - "trim_video"
Cohesion: 0.20
Nodes (7): get_collector(), HudCollector, ABC, Fonte do instantâneo da HUD., Sobe threads de coleta (no-op quando não houver)., Estado atual, já normalizado., Coletor do SO atual, na mesma convenção de :func:`app.capture.get_backend`.

### Community 76 - "windows_startup.py"
Cohesion: 0.22
Nodes (4): _Growth, _MeterTracker, Contabilidade temporal de uma fonte de áudio.      Guarda desde quando a fonte n, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo).

### Community 77 - "_resolve"
Cohesion: 0.18
Nodes (11): backfill_video_session_durations(), capture_speed_stats(), list_video_sessions(), media_source_name(), pipeline_queue(), probe_video_duration(), queue_eta_seconds(), Média recente de análise por tipo, para estimar a duração da fila.      Só as úl (+3 more)

### Community 79 - "ActionResult"
Cohesion: 0.07
Nodes (17): ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, LinuxCaptureModeTests, LinuxIdlePauseTests, _pausable(), Path, O sinal de atividade tem um significado só, e ele é caro de errar.      Enquanto (+9 more)

### Community 81 - "winscreen.py"
Cohesion: 0.20
Nodes (10): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.      ``ut, read_shell_config(), _as_bool(), _as_float(), _as_int(), _parse_config(), Laço contínuo de captura de telas — porte de ``bin/capture-loop`` para Python., Lê o ``tela.conf`` (formato ``CHAVE=valor`` do shell). (+2 more)

### Community 82 - "process_specific"
Cohesion: 0.29
Nodes (11): clear_call_metrics(), compact_saved_capture(), known_voice_profiles(), last_call_metrics(), monitor_key(), process_pending(), process_specific(), Compacta uma captura concluída e registra o novo hash ou um aviso. (+3 more)

### Community 83 - "HudFrameRateTests"
Cohesion: 0.24
Nodes (8): _attached_source(), _pulse_sources(), Coleta do estado que a HUD mostra, com um coletor por sistema.  Mesma divisão qu, Lê PCM cru do monitor de um bus e acumula o pico.          Taxa baixa e um canal, Mapa id -> nome das fontes do PipeWire/Pulse., Fonte à qual o ``parec`` de ``client`` está realmente ligado.      Existe porque, Converte multiplicador linear (0..1) para dBFS, com piso em silêncio., to_db()

### Community 84 - "ScreenLoop"
Cohesion: 0.10
Nodes (24): _activity_groups(), adaptive_web_research(), apply_exact_game_durations(), daily_narrative_target(), game_activity_rows(), merge_source_transcripts(), ollama_chat(), private_context_terms() (+16 more)

### Community 85 - "HudStatus"
Cohesion: 0.40
Nodes (4): Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, WAVEFORMATEXTENSIBLE, OSError

### Community 86 - "matched_sensitive_pattern"
Cohesion: 0.18
Nodes (7): matched_sensitive_pattern(), Path, Lista de expressões de um arquivo de padrões, ignorando comentários., Primeiro padrão sensível (regex, case-insensitive) que casa com a janela.      M, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados.          ``, read_patterns(), Motivo para não capturar agora, ou ``None`` se pode capturar.

### Community 87 - "trim_video"
Cohesion: 0.22
Nodes (8): cancel_video_audio_track_job(), cancel_video_audio_track_jobs(), cancel_video_audio_tracks(), Substitui um clipe pelo intervalo escolhido e invalida a análise antiga., Monta uma conversão precisa e preserva todas as faixas de áudio., trim_video(), trim_video_command(), VideoTrimRequest

### Community 88 - "stop_target_is_already_gone"
Cohesion: 0.31
Nodes (4): Registra um acontecimento pontual e publica na hora.          A sequência é o qu, Confirma uma ação aceita sem depender da interface estar em foco., Anota o instante atual da gravação.          Os marcadores ficam em memória e só, Salva o Replay Buffer atual e vincula o arquivo à sessão do jogo.

### Community 89 - "hudsource.py"
Cohesion: 0.08
Nodes (29): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., backfill_confirmed_voice_observations(), delete_unkept_raw_media(), enroll_voice_identity(), _normalized_average() (+21 more)

### Community 90 - "_scaled_size"
Cohesion: 0.25
Nodes (11): capture_change_test_frames(), capture_frames(), compare_screen_change_test(), get_screen_settings(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver.      A mesma regra nos doi, Captura um conjunto de frames com a configuração atual., screen_change_percent() (+3 more)

### Community 91 - "filter_hallucinated_segments"
Cohesion: 0.29
Nodes (3): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas.

### Community 92 - "HudFrameRateTests"
Cohesion: 0.33
Nodes (3): HudFrameRateTests, As três cadências existem por causa do custo de redesenhar.      Cada volta recr, Uma entrada de 0,26 s precisa de quadros suficientes para não escadear.

### Community 97 - "._partial_segment"
Cohesion: 0.33
Nodes (5): _count_markers(), Path, Segmento sendo escrito agora pelo ``gpu-screen-recorder``., Há quanto tempo o segmento em curso começou.      Vem do nome do arquivo, não do, _segment_elapsed()

### Community 98 - "UnitResolutionTests"
Cohesion: 0.36
Nodes (3): Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), UnitResolutionTests

### Community 99 - "LinuxHudCollector"
Cohesion: 0.25
Nodes (3): LinuxHudCollector, Estado derivado do laço bash e medidores lidos dos buses do PipeWire.      O ``b, Janela em foco, com a mesma cadência do laço bash (2 s).          O sidecar ``.w

### Community 101 - "foreground_details"
Cohesion: 0.33
Nodes (5): foreground_details(), looks_blank(), Path, Título, classe e executável da janela em foco — o que o OBS precisa     para eng, Amostra um quadro e diz se o vídeo saiu chapado (preto/estático).      É a rede

### Community 103 - "windows_startup.py"
Cohesion: 0.60
Nodes (4): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows.  Executado com ``pythonw.exe`` pe

### Community 105 - "_scaled_size"
Cohesion: 0.50
Nodes (4): _parse_max_geometry(), Interpreta ``"1920x1080>"`` -> (1920, 1080, apenas_reduzir)., Dimensões finais respeitando ``MAX_GEOMETRY`` (mantém proporção)., _scaled_size()

### Community 106 - "._dshow_loopback"
Cohesion: 0.21
Nodes (5): Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga.          Dois formatos d, Dispositivo dshow capaz de gravar a saída, se algum existir.          Só diagnós, argv do gravador WASAPI (ver :mod:`app.capture.winrecord`).          Não é ffmpe, WindowsCaptureBackend

### Community 107 - "context_overflow"
Cohesion: 0.67
Nodes (3): context_overflow(), O Ollama recusa o lote inteiro quando as imagens não cabem no ``num_ctx``., Exception

## Knowledge Gaps
- **106 isolated node(s):** `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame`, `StorageCandidate`, `WebSource` (+101 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **24 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `ConfigTests`, `post`, `track_is_silent`, `test_services.py`, `.action`, `WindowsServiceManager`, `runtime_dir`, `HudSnapshot`, `Path`, `hud.py`, `LinuxHudCollector`, `get`, `main.py`, `delete_voice_identity`, `._start`, `trim_video`, `run`, `_event_fields`, `ServiceManager`, `generate_visual_activities`, `HudStateTests`, `.test_the_whole_entry_gets_many_frames`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `get_backend`, `ScreenLoop`, `trim_video`, `hudsource.py`, `_scaled_size`, `HudFrameRateTests`, `UnitResolutionTests`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `safe_video_path`, `.test_the_whole_entry_gets_many_frames`, `speaker_profiles`, `captured_video_session`, `post`, `.test_a_day_that_fails_to_consolidate_does_not_abort_the_whole_run`, `.action`, `.test_opus_stems_go_to_a_container_that_accepts_them`, `ActionResult`, `.test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis`, `.test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time`, `.test_recording_keeps_the_mix_ahead_of_the_isolated_tracks`, `ScreenLoop`, `audio_intelligence.py`, `filter_hallucinated_segments`, `daily_narrative_target`?**
  _High betweenness centrality (0.061) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `ActionResult` to `ConfigTests`, `post`, `track_is_silent`, `test_services.py`, `WindowsServiceManager`, `runtime_dir`, `HudSnapshot`, `hud.py`, `get`, `._start`, `trim_video`, `run`, `_event_fields`, `ServiceManager`, `HudStateTests`, `.test_the_whole_entry_gets_many_frames`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `get_backend`, `ScreenLoop`, `HudFrameRateTests`, `UnitResolutionTests`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `VideoWindowTest`) actually correct?**
  _`ConfigTests` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 58 inferred relationships involving `ActionResult` (e.g. with `CleanupSettings` and `ContextUpdate`) actually correct?**
  _`ActionResult` has 58 INFERRED edges - model-reasoned connections that need verification._
- **Are the 36 inferred relationships involving `SystemdServiceManager` (e.g. with `CallMetricsTests` and `ConfigTests`) actually correct?**
  _`SystemdServiceManager` has 36 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` to the rest of the system?**
  _106 weakly-connected nodes found - possible documentation gaps or missing edges._