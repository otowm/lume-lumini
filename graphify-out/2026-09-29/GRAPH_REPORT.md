# Graph Report - lume  (2026-09-29)

## Corpus Check
- 83 files · ~164,640 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2676 nodes · 6375 edges · 161 communities (107 shown, 54 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 662 edges (avg confidence: 0.51)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8b02e4ad`
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
- .test_bash_loop_counts_game_time_through_the_shared_cli
- test_updater.py
- .test_capture_target_does_not_pull_a_disabled_capture
- .test_o_teto_do_discord_preserva_os_sessenta_quadros
- .test_o_original_que_ja_cabe_nao_e_recodificado
- .test_original_que_cabe_com_volumes_copia_a_imagem_e_refaz_so_o_audio
- .test_consultar_o_estado_nunca_liga_o_ventilador
- .test_opus_stems_go_to_a_container_that_accepts_them
- .test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis
- .test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time
- .test_recording_keeps_the_mix_ahead_of_the_isolated_tracks
- .test_stale_game_session_is_closed_at_the_last_heartbeat
- .test_versao_leve_mantem_somente_a_faixa_de_mixagem
- .test_link_fica_salvo_para_recopiar_depois
- .test_nenhum_outro_modulo_chama_o_upload
- .test_windows_structs_match_the_win32_sizes
- .test_every_publish_path_cleans_the_mic
- .resolution
- .active

## God Nodes (most connected - your core abstractions)
1. `ConfigTests` - 123 edges
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
- `remove_alias()` --calls--> `connect()`  [EXTRACTED]
  app/backend/tags.py → app/backend/database.py
- `ScreenSettings` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `AudioSettings` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `SensitiveWindows` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `PipelineRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py

## Import Cycles
- None detected.

## Communities (161 total, 54 thin omitted)

### Community 1 - "src/api.ts"
Cohesion: 0.05
Nodes (41): ActivityFrame, AnalysisTrace, AppMode, AudioEvent, ConfirmationSound, DaySummary, EditingEntry, EditingResult (+33 more)

### Community 2 - "package.json"
Cohesion: 0.14
Nodes (46): _activity_image(), analyze_video_chapter(), audio_channel_count(), audio_stream_count(), clear_call_metrics(), compact_processed_audio(), compact_saved_capture(), describe_long_video() (+38 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "LinuxCaptureBackend"
Cohesion: 0.05
Nodes (33): CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional.  Cada SO fornec, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco.          Retorna ``N, Por que ``active_window`` falhou, numa frase para a interface., Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável. (+25 more)

### Community 5 - "obs.py"
Cohesion: 0.06
Nodes (65): any_fullscreen(), apply_mic_filters(), batch(), call(), _copy_installation(), diagnostics(), _encode_field(), ensure_scene() (+57 more)

### Community 6 - "record"
Cohesion: 0.20
Nodes (8): Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record(), _SegmentWriter, _Source

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.15
Nodes (23): _download(), _fetch(), forget_missing(), _from_steam(), _from_steamgriddb(), _get(), _json(), lookup() (+15 more)

### Community 9 - "VideoSettings"
Cohesion: 0.33
Nodes (4): VideoSettings, Salvar as preferências não pode apagar chaves silenciosamente.      ``set_video_, Uma instalação antiga não pode ficar sem HUD nem quebrar ao salvar., VideoSettingsRoundTripTests

### Community 10 - "Lume no Windows"
Cohesion: 0.05
Nodes (40): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, Abrir de outro aparelho, As três faixas de áudio (+32 more)

### Community 11 - "SilentTrackTests"
Cohesion: 0.09
Nodes (5): Path, c1 e c2 não podem carregar a mesma voz, nem o mesmo som duas vezes., Dois marcadores seguidos têm o mesmo rótulo; só a sequência os separa., Um tipo sem estilo seria um evento invisível — falha silenciosa., O formato do ``input_event`` é contrato do kernel, não detalhe nosso.          E

### Community 13 - "ActionResult"
Cohesion: 0.10
Nodes (23): row_dict(), _audio_channels(), capture_payload(), captures(), delete_capture(), delete_capture_file(), generate_hourly_now(), generate_summary_now() (+15 more)

### Community 14 - "WindowsServiceManager"
Cohesion: 0.09
Nodes (15): _JobObject, _Process, Path, Popen, Uma unit supervisionada.      ``simple`` roda enquanto o serviço estiver ligado, Amarra os processos filhos ao ciclo de vida da API.      É o que o systemd conse, Return seconds since the last real keyboard or mouse input on Windows., Um processo filho supervisionado. (+7 more)

### Community 15 - "game-video-loop"
Cohesion: 0.10
Nodes (42): game-video-loop script, absorb_pending_clip(), active_monitor(), add_long_marker(), add_marker(), adopt_video(), begin_game_session(), clean_mic_track() (+34 more)

### Community 16 - "runtime_dir"
Cohesion: 0.15
Nodes (18): Path, Helpers de runtime que funcionam igual em Linux e Windows.  Centraliza as poucas, Diretório para arquivos efêmeros (locks, estado volátil).      Linux usa ``XDG_R, Arquivo que sinaliza "estou gravando vídeo agora".      É como o laço de vídeo p, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Pedido da interface para encerrar já a sessão que está na contagem.      Só vale, runtime_dir(), video_activity_flag() (+10 more)

### Community 18 - "RemapToSourceTests"
Cohesion: 0.33
Nodes (3): Voltar os tempos do bloco para o eixo do áudio original.      É a parte que, err, Fim antes do início quebraria a ordenação e a legenda., RemapToSourceTests

### Community 19 - "get"
Cohesion: 0.13
Nodes (26): active_vocabulary(), apply_tags(), canonicalize(), clean_label(), create(), _describe(), _enforce_cap(), listing() (+18 more)

### Community 20 - "main.py"
Cohesion: 0.05
Nodes (57): atomic_write(), capture_days(), capture_speed_stats(), CleanupSettings, ContextUpdate, create_tag(), create_video_session(), enroll_voice_identity() (+49 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.13
Nodes (22): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize_file() (+14 more)

### Community 24 - "capture-frame"
Cohesion: 0.27
Nodes (6): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), KDE_SESSION_VERSION, usage()

### Community 25 - "hud.py"
Cohesion: 0.08
Nodes (13): ModoLuminiTests, O Lumini é a mesma base instalada só como gravador.      Sem estes testes, a ins, Atualizar o Lume não pode desligar a análise de quem a tem., O modo precisa valer para todo processo da máquina.          São quatro que prec, Experimentar o Lumini não pode exigir editar a instalação., Um erro de digitação não pode mutilar a interface de ninguém., Sem isso a interface adivinha, e mostra botões de IA a quem não tem., Um prefixo desatento na tabela derrubaria a biblioteca de clipes. (+5 more)

### Community 27 - "WasapiError"
Cohesion: 0.19
Nodes (14): available(), Choice, choose(), LayaUnavailable, RuntimeError, Cliente do daemon do Laya — classificação de texto por vocabulário fechado.  O `, Uma pergunta de múltipla escolha para cada estado, num único lote.      ``criter, Onde o daemon escuta. No Windows não há socket UNIX — devolve vazio. (+6 more)

### Community 29 - "Path"
Cohesion: 0.10
Nodes (30): apply_confirmation_sound_preset(), _apply_storage_runtime(), _apply_video_runtime(), atomic_write_if_changed(), AudioSettings, cancel_pipeline(), cancel_queue_item(), cancel_screen_sequence() (+22 more)

### Community 30 - "editing.py"
Cohesion: 0.12
Nodes (32): available_name(), chapter_seconds(), clip_markers(), EditingError, entries(), folder(), frames_to_timecode(), inside_folder() (+24 more)

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
Cohesion: 0.11
Nodes (17): dbfs(), default_endpoint_name(), Nome do endpoint padrão, ou ``None`` se não houver nenhum., Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _install_stop_handlers(), main(), _mix() (+9 more)

### Community 35 - "_call"
Cohesion: 0.17
Nodes (21): _ActivationHandler, _AudioClientActivationParams, _Blob, _call(), _check(), _device_enumerator(), ensure_com(), _friendly_name() (+13 more)

### Community 37 - "_JobObject"
Cohesion: 0.14
Nodes (11): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., ease_in_cubic(), ease_out_back(), ease_out_cubic() (+3 more)

### Community 38 - "run"
Cohesion: 0.07
Nodes (32): connect(), backfill_confirmed_voice_observations(), backfill_video_session_durations(), cancel_entire_queue(), delete_unkept_raw_media(), delete_video_marker(), delete_video_session(), list_video_sessions() (+24 more)

### Community 39 - "connect"
Cohesion: 0.06
Nodes (25): HotkeyChordTests, WindowsBracketTests, daemon_flag(), HotkeyDaemon, keyboard_devices(), log(), main(), parse_key() (+17 more)

### Community 43 - "prompts.py"
Cohesion: 0.07
Nodes (22): get_prompts(), reset_prompt(), active_template(), listing(), _overrides(), payload(), PromptError, PromptSpec (+14 more)

### Community 45 - "winrecord.py"
Cohesion: 0.17
Nodes (21): _as_float(), _as_ratio(), audio_mix(), host_catalog(), _link_dict(), links_for(), load_audio_mix(), probe_video_shape() (+13 more)

### Community 46 - "SpeechRegionTests"
Cohesion: 0.36
Nodes (5): Trechos ``(início, fim)`` em segundos onde há som acima do limiar.      Função p, speech_regions(), Detecção dos trechos com som, sobre amostras sintéticas., A folga não pode gerar tempo negativo nem passar do fim do áudio., SpeechRegionTests

### Community 47 - ".snapshot"
Cohesion: 0.07
Nodes (31): concat_videos(), cut_head(), foreground_details(), log(), looks_blank(), media_duration(), Path, Grava uma sessão lógica, possivelmente dividida em segmentos. (+23 more)

### Community 48 - "get_manager"
Cohesion: 0.15
Nodes (11): Host, MultipartBody, RuntimeError, O envio foi interrompido a pedido de quem o começou., Um lugar onde o arquivo pode ser publicado, sem conta e sem login., A resposta é a URL em texto puro — e o erro também vem como HTTP 200.          P, Corpo multipart que lê o arquivo em blocos e sabe o próprio tamanho.      O tama, Publica o arquivo e devolve a URL. **Só o job de upload chama isto.**      Nenhu (+3 more)

### Community 49 - "CallMetricsTests"
Cohesion: 0.27
Nodes (4): CallMetricsTests, Sem separar carga, leitura do prompt e geracao, encurtar prompt e chute., ollama_json repete a chamada para consertar JSON; isso custa tempo., Um audio nao passa pelo Ollama; herdar a medicao de uma tela mentiria.

### Community 50 - "resolve_media_source"
Cohesion: 0.29
Nodes (7): _mix_tag(), prune_share_cache(), O teto e a receita ficam **fora** do hash, de propósito.      Assim a limpeza de, Versão leve pronta e mais nova que o original, ou nada.      O corte (``/api/vid, Segura o tamanho do cache: são arquivos de dezenas de MB.      Nada no Lume apag, share_cache_path(), share_cached()

### Community 51 - "RegionGroupingTests"
Cohesion: 0.31
Nodes (5): group_regions(), Agrupa trechos vizinhos em blocos que caibam numa janela do whisper.      Dois t, Blocos que enchem uma janela do whisper sem esticar o eixo do tempo.      O whis, É o teto que impede um erro de 1 s virar 20 s ao voltar ao original., RegionGroupingTests

### Community 52 - "Path"
Cohesion: 0.12
Nodes (5): Achar o clipe e mandar para alguém.      O gravador nomeia por data, então o que, Numa jogada a fluidez lê melhor que a nitidez: 720p60, não 1080p30., Pedir 63 Mbps de um vídeo gravado a 2,3 gastaria CPU para nada., Para sempre" é decisão de quem publica, não do código., SharingTests

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
Cohesion: 0.17
Nodes (10): blend(), EventFrame, HudPanel, Mistura duas cores ``#rrggbb``.      O Canvas do tkinter não tem canal alfa por, Um quadro da animação de confirmação.      ``reveal`` é o quanto o evento tomou, Um painel desenhado num monitor., Corta pela largura real do texto, não por contagem de caracteres.          A HUD, Barra mínima. O evento entra por baixo empurrando o conteúdo normal.          Nã (+2 more)

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers.      M, Um fluxo de captura: microfone padrão ou loopback da saída padrão.      A saída, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio).          Um, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "trim_video"
Cohesion: 0.13
Nodes (22): audio_file(), _audio_streams(), capture_speaker_sample(), delete_voice_identity(), import_video(), mic_level(), process_file(), ProcessFileRequest (+14 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.22
Nodes (11): _config_int(), get_audio_settings(), get_video_settings(), parse_shell_config(), _prepare_confirmation_sounds(), FPS e timecode inicial da timeline, como configurados no Video seletivo., No Windows, deixa os WAVs prontos antes da partida (ver sounds.prepare)., resolve_timeline_options() (+3 more)

### Community 64 - "HudStateTests"
Cohesion: 0.16
Nodes (7): HudStateTests, As regras que decidem se a captura está saudável.      Rodam nos dois sistemas d, Segurou o atalho: já não é "armado", é gravando de verdade., Ficar calado é normal; confundir com falha destrói a confiança na HUD., A supressão zera o bus sem fala; o microfone cru diz que ele vive., evaluate(), Traduz um instantâneo em alertas e num veredito único.      Função pura: mesma e

### Community 65 - "local_origin_only"
Cohesion: 0.22
Nodes (14): begin(), close_stale(), _ensure_schema(), finish(), heartbeat(), iso_time(), main(), Contagem de tempo por jogo, independente do que foi gravado.  O tempo de jogo é (+6 more)

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
Cohesion: 0.07
Nodes (19): _attached_source(), _clean_mic_master(), _Growth, log(), _MeterTracker, _pulse_sources(), Microfone cru por trás do filtro da supressão por IA, se ele existir., Contabilidade temporal de uma fonte de áudio.      Guarda desde quando a fonte n (+11 more)

### Community 72 - "capture_frames"
Cohesion: 0.20
Nodes (9): 1. Atividades por assunto, com agrupamento por aplicativo como apoio, 2. Contexto completo e verificável em resumos e vídeos, 3. Captura e fila: preservar o lugar de onde a pessoa veio, 4. Vídeos, áudio e busca: acesso consistente às evidências, 5. Ajustes, calendário e acessibilidade, Melhorias aplicadas nesta revisão, Revisão das demais áreas e prioridades, Revisão do Lume — experiência e contexto da IA (+1 more)

### Community 74 - "EditingFolderTests"
Cohesion: 0.11
Nodes (5): EditingFolderTests, A pasta de edicao troca garimpo de arquivo por nome legivel e EDL., 12,5 s a 60 fps sao 750 quadros depois do inicio da timeline., O hardlink segura os bytes, entao apagar por engano so confundiria., O segundo trecho comeca onde o primeiro acaba, e o EDL acompanha.

### Community 75 - "hudsource.py"
Cohesion: 0.08
Nodes (13): ActionResult, (Re)inicia o swayidle apontando os eventos para o flag de idle., Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, _unknown(), _FakeResponse, Pausar desabilita a unit: só parar valia até o próximo boot., Resposta de host de arquivo: corpo em texto puro, sem rede envolvida. (+5 more)

### Community 76 - "_Growth"
Cohesion: 0.38
Nodes (6): ActivitiesView(), ActivityCard(), Frame, searchable(), time(), ActivitySession

### Community 77 - "Path"
Cohesion: 0.25
Nodes (11): capture_change_test_frames(), capture_frames(), compare_screen_change_test(), get_screen_settings(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver.      A mesma regra nos doi, Captura um conjunto de frames com a configuração atual., screen_change_percent() (+3 more)

### Community 78 - "multimodal_context"
Cohesion: 0.09
Nodes (25): cancel_light_version(), cancel_upload(), download_video(), game_icon_file(), get_video_audio_mix(), light_version_state(), preserve_video(), process_video() (+17 more)

### Community 79 - "Path"
Cohesion: 0.20
Nodes (10): Decision, _merge_ready(), As tags com alguma chance de serem a mesma coisa, e só elas.      Mandar o vocab, Pergunta ao Laya quais propostas são sinônimo de alguma tag ativa., Última checagem semântica antes de ativar: o vocabulário pode ter crescido., O caminho que uma string bruta percorreu até virar (ou não) uma tag., Resolution, _resolve_with_laya() (+2 more)

### Community 80 - "LinuxAppRuleMatchTests"
Cohesion: 0.10
Nodes (50): ClipAudioTrackTests, HudDisplayModeTests, HudEventContractTests, ImageDiffTests, KdotoolSessionVersionTests, LinuxAudioTapTests, LinuxCleanMicTests, LinuxFocusVerdictTests (+42 more)

### Community 82 - "context_overflow"
Cohesion: 0.67
Nodes (5): dateOf(), DayPicker(), fullLabel(), MemoryDay, monthLabel()

### Community 83 - "._start"
Cohesion: 0.18
Nodes (5): Laço só com o estado que o caminho dos clipes usa., O clipe espera fora do buffer; ao ser publicado leva os sidecars.          Publi, Dois atalhos em menos de um clipe descrevem um trecho só.          Com clipes de, Clipe e gravação longa logo depois: um arquivo só, sem trecho repetido., Sem sobreposição não há o que mesclar: são duas jogadas distintas.

### Community 84 - "test_main.py"
Cohesion: 0.17
Nodes (12): cancel_update(), cancel_video_audio_track_jobs(), get_schedule(), lifespan(), migrate_legacy_media_caches(), process_video_session_job(), Move caches antigos do perfil para a raiz de armazenamento selecionada., ScheduleSettings (+4 more)

### Community 85 - "get_backend"
Cohesion: 0.09
Nodes (30): initialize(), _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., create_video_marker(), delete_file(), delete_unprocessed_files() (+22 more)

### Community 86 - ".snapshot"
Cohesion: 0.08
Nodes (28): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.      ``ut, read_shell_config(), _app_label(), _count_markers(), _elapsed(), _event_fields(), _focus_grace_remaining(), get_collector() (+20 more)

### Community 87 - "filter_hallucinated_segments"
Cohesion: 0.20
Nodes (5): parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., Regras sem prefixo procuram somente no executável.          Assim uma pasta cham, Instantâneo de ``video.conf`` e da lista de apps., Settings

### Community 88 - "hudsource.py"
Cohesion: 0.19
Nodes (9): LinuxCaptureModeTests, O modo da regra vale no Linux, com o gravador de verdade rodando.      ``[clips], O gravador de jogo não pode depender da captura de áudio estar de pé.          O, O VCE de uma RX 550 derrubou a GPU inteira ("ring vce0 timeout").          Em Po, Um gravador que morre ao subir não pode virar um laço invisível.          Era as, Clipar duas vezes seguidas descreve um trecho só, não dois.          Com clipes, Sem sobreposição não há o que mesclar: são duas jogadas distintas., Segurar o atalho: "isto vai ser longo, quero tudo".          O clipe de pré-roll (+1 more)

### Community 89 - "media_source_key"
Cohesion: 0.22
Nodes (9): cached_file(), _ico_to_png(), Path, Caminho de um ícone já baixado; só nomes gerados aqui são aceitos., Converte um ``.ico`` na sua maior imagem, em PNG.      Muitos jogos só têm ícone, merge(), _record_alias(), set_status() (+1 more)

### Community 90 - ".grab_frame"
Cohesion: 0.12
Nodes (34): _activity_batch_summary(), adaptive_web_research(), analyze_screen_sequence(), describe_tag_candidates(), generate_hourly_summaries(), generate_summary(), generate_visual_activities(), main() (+26 more)

### Community 91 - "WasapiError"
Cohesion: 0.20
Nodes (5): ProcessLoopbackCapture, Falha numa chamada COM do WASAPI, com o HRESULT preservado., Loopback que inclui ou exclui a árvore de um processo do Windows., WasapiError, WAVEFORMATEXTENSIBLE

### Community 92 - "context_overflow"
Cohesion: 0.05
Nodes (59): health(), update_status(), _do_arquivo(), e_lumini(), modo_atual(), Em qual modo esta instalação foi montada.  O Lume completo grava, transcreve, de, Lê ``LUME_MODE`` do ``lume.conf``, sem depender do resto do backend.      Parse, O modo em vigor. Sem cache, de propósito.      O arquivo tem uma linha, e ``/api (+51 more)

### Community 93 - "_LazyOle32"
Cohesion: 0.12
Nodes (12): api, TagDecision, TagEntry, TagPromotion, TagStatus, TagTestResult, TagVocabulary, OUTCOME (+4 more)

### Community 94 - "HoldDetectorTests"
Cohesion: 0.22
Nodes (6): Path, Lista de expressões de um arquivo de padrões, ignorando comentários., Nome estável para ``<título> | <executável>``.      Alguns jogos, especialmente, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados.          ``, read_patterns(), stable_app_label()

### Community 97 - "winscreen.py"
Cohesion: 0.40
Nodes (3): MediaFreshnessTests, As URLs de mídia têm de mudar quando o arquivo muda.      O corte reescreve o ví, Um clipe apagado entre a listagem e a montagem da URL não é erro 500.

### Community 98 - "services.py"
Cohesion: 0.36
Nodes (3): Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), UnitResolutionTests

### Community 99 - ".active"
Cohesion: 0.13
Nodes (14): light_state(), light_video_command(), _LightVersionJob, progress_percent(), Popen, A receita que cabe no teto: quanto bitrate, em que tamanho de imagem., Bitrate que cabe no teto, e o tamanho de imagem que esse bitrate aguenta.      R, Recodificação que cabe no teto e serve para ser assistida por outra pessoa. (+6 more)

### Community 100 - "devDependencies"
Cohesion: 0.29
Nodes (3): Move o foco para ``window``, com o jogo continuando aberto atrás., O outro lado de segurar a sessão: o jogo fechar tem de acabar com ela., A correção não pode virar "grava para sempre".          Quem abre o navegador po

### Community 101 - "hudsource.py"
Cohesion: 0.20
Nodes (17): apply_preset(), clear_custom(), custom_sound(), default_sound(), play(), playable_wav(), prepare(), presets() (+9 more)

### Community 102 - "_LazyOle32"
Cohesion: 0.20
Nodes (4): _chunks(), ConfirmationSoundTests, Sons do atalho: o arquivo enviado substitui o padrão, e remover o devolve., O winsound só toca WAV e não tem volume: a conversão cuida dos dois.

### Community 104 - ".feed"
Cohesion: 0.10
Nodes (19): _activity_app(), _activity_groups(), apply_exact_game_durations(), daily_narrative_target(), game_activity_rows(), private_context_terms(), Prefere a identidade capturada da janela aos nomes variáveis da IA., Separa por aplicativo e continuidade; mudanças de título não quebram a sessão. (+11 more)

### Community 105 - "read_shell_config"
Cohesion: 0.22
Nodes (9): end_video_session(), install_update_now(), Estado operacional do gravador, separado da mera configuração ativa., Encerra agora a sessão que já está contando para parar fora do jogo.      Quem s, Conciliação sem gravar nada: mostra o caminho de cada string até a tag., selective_video_status(), status(), TagTestRequest (+1 more)

### Community 106 - ".test_an_unreadable_foreground_window_neither_starts_nor_advances_the_countdown"
Cohesion: 0.09
Nodes (23): bounded_video_range(), _confirmation_sounds(), list_confirmation_sounds(), local_origin_only(), origin_allowed(), Se este caminho só faz sentido com o pipeline instalado., No Lumini, o que depende de IA responde 409 em vez de tentar.      Esconder os b, Se o ``Host`` (ou a origem) descreve este servidor.      Além dos nomes configur (+15 more)

### Community 108 - "multimodal_context"
Cohesion: 0.24
Nodes (8): Pico de um WAV PCM 16 bits, em dBFS. ``-inf`` vira o piso -99., A faixa está muda o bastante para transcrevê-la ser desperdício?      Numa sessã, track_is_silent(), track_peak_dbfs(), Faixas mudas não valem uma transcrição.      Numa sessão sem Discord a faixa del, -40 dBFS é fala baixa de verdade; pular isso perderia conversa., Na dúvida, transcreve: perder fala é pior que gastar tempo., SilentTrackTests

### Community 110 - ".action"
Cohesion: 0.29
Nodes (4): diarize(), pad_to_segmentation_window(), Descarta o que a diarização inventou sobre o silêncio de completamento., turns_within_duration()

### Community 111 - "matched_sensitive_pattern"
Cohesion: 0.29
Nodes (3): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas.

### Community 113 - "rebuild_voice_identity"
Cohesion: 0.27
Nodes (10): light_video_file(), Baixa a versão leve pronta; 409 enquanto ela não existir.      Não gera nada aqu, light_filename(), normalized_limit(), Publica o clipe num host grátis, **só com confirmação explícita**.      A trava, O teto entra no nome: duas versões do mesmo clipe não se confundem., Falha que o usuário precisa ler, não um defeito interno., resolve_host() (+2 more)

### Community 115 - "delete_voice_identity"
Cohesion: 0.07
Nodes (43): cancel_video_audio_track_job(), cancel_video_audio_tracks(), _delete_media_sidecars(), delete_video(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), media_url() (+35 more)

### Community 116 - "HudStatus"
Cohesion: 0.06
Nodes (33): _alert_sound(), _assert_topmost(), _declare_dpi_aware(), _demo_sequence(), Hud, HudSettings, log(), main() (+25 more)

### Community 118 - "LinuxAudioTapTests"
Cohesion: 0.08
Nodes (25): Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg.  O laço de captura do Linux usa, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar. (+17 more)

### Community 120 - "._partial_segment"
Cohesion: 0.33
Nodes (3): cancel_uploads(), Sobe o arquivo fora da requisição HTTP, com progresso e cancelamento., _UploadJob

### Community 121 - "multimodal_context"
Cohesion: 0.33
Nodes (3): HudFrameRateTests, As três cadências existem por causa do custo de redesenhar.      Cada volta recr, Uma entrada de 0,26 s precisa de quadros suficientes para não escadear.

### Community 126 - "exige"
Cohesion: 1.00
Nodes (3): exige(), instalar-lumini.sh script, tem()

### Community 129 - "share_stem"
Cohesion: 0.29
Nodes (7): _clip_row(), download_filename(), ``2026-09-26 00-10 Sea of Thieves — trecho 02 de 05``, sem extensão.      Vale p, Nome oferecido no download, com a extensão do arquivo original., Posição do trecho na sessão, na mesma ordem que a pasta de edição usa.      Uma, _session_position(), share_stem()

### Community 132 - "UpdateNotice.tsx"
Cohesion: 0.67
Nodes (3): request(), UpdateNotice(), UpdateStatus

### Community 137 - "validate_relevant_media"
Cohesion: 0.07
Nodes (18): LinuxAppRuleMatchTests, LinuxAudioTrackTests, Gravação em faixas separadas (3 canais) no backend Linux., Sem audio.conf, o microfone ainda ganha o tratamento padrão., A calibração precisa do sinal cru: filtrado, o silêncio de fundo         sempre, O dshow corta nomes longos: casa pelo prefixo do nome do WASAPI., Regras do ``bin/game-video-loop``, pelo modo ``--match`` do próprio script., AudioConfig (+10 more)

### Community 138 - "ValueError"
Cohesion: 0.67
Nodes (3): context_overflow(), O Ollama recusa o lote inteiro quando as imagens não cabem no ``num_ctx``., Exception

## Knowledge Gaps
- **144 isolated node(s):** `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame`, `StorageCandidate`, `WebSource` (+139 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **54 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `hudsource.py` to `ConfigTests`, `_activity_groups`, `.test_a_summary_older_than_its_own_memories_is_redone`, `VideoSettings`, `validate_relevant_media`, `test_services.py`, `ActionResult`, `WindowsServiceManager`, `runtime_dir`, `RemapToSourceTests`, `main.py`, `hud.py`, `Path`, `_JobObject`, `run`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `Path`, `ServiceManager`, `trim_video`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `Path`, `multimodal_context`, `LinuxAppRuleMatchTests`, `test_main.py`, `hudsource.py`, `winscreen.py`, `services.py`, `_LazyOle32`, `.feed`, `read_shell_config`, `multimodal_context`, `delete_voice_identity`, `multimodal_context`, `test_updater.py`?**
  _High betweenness centrality (0.136) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `_activity_groups`, `WindowsStartupTests`, `GUID`, `_devmode_w`, `VideoSettings`, `_scaled_size`, `.test_bash_loop_counts_game_time_through_the_shared_cli`, `test_updater.py`, `.test_o_teto_do_discord_preserva_os_sessenta_quadros`, `.test_opus_stems_go_to_a_container_that_accepts_them`, `.test_queue_omits_the_estimate_while_a_kind_has_no_measured_analysis`, `main.py`, `audio_intelligence.py`, `.test_queue_reports_recent_average_per_kind_and_estimates_the_remaining_time`, `.test_recording_keeps_the_mix_ahead_of_the_isolated_tracks`, `.test_stale_game_session_is_closed_at_the_last_heartbeat`, `VideoWindowTest`, `patch`, `hudsource.py`, `.feed`, `.test_an_unreadable_foreground_window_neither_starts_nor_advances_the_countdown`, `.action`, `matched_sensitive_pattern`, `stop_target_is_already_gone`, `devDependencies`?**
  _High betweenness centrality (0.089) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `hudsource.py` to `ConfigTests`, `.test_a_summary_older_than_its_own_memories_is_redone`, `VideoSettings`, `validate_relevant_media`, `test_services.py`, `runtime_dir`, `RemapToSourceTests`, `hud.py`, `_JobObject`, `run`, `SpeechRegionTests`, `CallMetricsTests`, `RegionGroupingTests`, `Path`, `ServiceManager`, `HudStateTests`, `VideoWindowTest`, `HudPlacementTests`, `PromptSettingsTests`, `EditingFolderTests`, `LinuxAppRuleMatchTests`, `test_main.py`, `hudsource.py`, `winscreen.py`, `services.py`, `_LazyOle32`, `.feed`, `multimodal_context`, `multimodal_context`, `test_updater.py`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `VideoWindowTest`) actually correct?**
  _`ConfigTests` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 84 inferred relationships involving `ActionResult` (e.g. with `AudioSettings` and `CleanupSettings`) actually correct?**
  _`ActionResult` has 84 INFERRED edges - model-reasoned connections that need verification._
- **Are the 43 inferred relationships involving `VideoLoop` (e.g. with `ClipAudioTrackTests` and `HoldDetectorTests`) actually correct?**
  _`VideoLoop` has 43 INFERRED edges - model-reasoned connections that need verification._
- **What connects `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` to the rest of the system?**
  _144 weakly-connected nodes found - possible documentation gaps or missing edges._