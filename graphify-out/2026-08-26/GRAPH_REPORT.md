# Graph Report - lume  (2026-08-26)

## Corpus Check
- 56 files · ~92,194 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1516 nodes · 3738 edges · 93 communities (81 shown, 12 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 303 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `da259cb6`
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
- connect
- Lume no Windows
- track_is_silent
- post
- winscreen.py
- WindowsServiceManager
- game-video-loop
- ActionResult
- AGENTS.md
- LinuxCaptureBackend
- initialize
- Path
- install-audio-intelligence
- audio_intelligence.py
- capture-frame
- Monitor
- add-video-marker
- WasapiError
- install-captura-dia.sh
- set_video_settings
- RuntimeError
- audio-bus.sh
- src-backup-2026-08-09/api.ts
- src-backup-2026-08-09/main.tsx
- get
- _call
- capture-loop
- main.py
- test_services.py
- run
- grava-audio.sh
- install-lume.sh
- install-user.sh
- winrecord.py
- MarkerHotkey
- local_origin_only
- media_source_key
- HudEventAnimationTests
- get_manager
- hudsource.py
- Hud
- ServiceManager
- src/main.tsx
- App
- videoTime
- capture_frames
- WasapiCapture
- videoTime
- test_main.py
- pipeline.py
- App
- HudPanel
- HudStateTests
- thumbnail
- wasapi.py
- HudPlacementTests
- hud.py
- HudSnapshot
- VideoActivityFlagTests
- .tick
- runtime_dir
- .action
- windows_startup.py
- UnitResolutionTests
- VideoSettings
- Path
- HudEventContractTests
- services.py
- ._start
- patch
- matched_sensitive_pattern
- HudFrameRateTests
- get_backend
- analyze_screen_sequence
- VideoReplayClipTests
- LinuxIdlePauseTests
- speaker_profiles
- recover_json_from_thinking
- captured_video_session

## God Nodes (most connected - your core abstractions)
1. `connect()` - 83 edges
2. `ActionResult` - 82 edges
3. `ConfigTests` - 81 edges
4. `SystemdServiceManager` - 51 edges
5. `HudSnapshot` - 50 edges
6. `VideoLoop` - 49 edges
7. `Monitor` - 47 edges
8. `Meter` - 45 edges
9. `WindowsCaptureBackend` - 41 edges
10. `LinuxCaptureBackend` - 40 edges

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

## Communities (93 total, 12 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.06
Nodes (5): multimodal_context(), Agrupa telas e áudios sobrepostos em momentos únicos para as sínteses., ConfigTests, Path, skipUnless

### Community 1 - "src/api.ts"
Cohesion: 0.07
Nodes (28): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+20 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "base.py"
Cohesion: 0.09
Nodes (16): CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional. Cada SO…, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco. Retorna ``None``…, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Prepara o roteamento de áudio (no-op onde não for necessário). (+8 more)

### Community 5 - "obs.py"
Cohesion: 0.07
Nodes (55): any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), ensure_scene(), find_installation(), _identify() (+47 more)

### Community 6 - "record"
Cohesion: 0.17
Nodes (10): ProcessLoopbackCapture, Loopback que inclui ou exclui a árvore de um processo do Windows., Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record() (+2 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.08
Nodes (22): parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., foreground_details(), log(), looks_blank(), main(), Path, Gravação seletiva de jogos no Windows — porte de ``bin/game-video-loop``. Mesma… (+14 more)

### Community 9 - "connect"
Cohesion: 0.15
Nodes (26): connect(), row_dict(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_screen_sequence(), cancel_video_analysis(), cancel_video_session() (+18 more)

### Community 10 - "Lume no Windows"
Cohesion: 0.07
Nodes (24): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+16 more)

### Community 11 - "track_is_silent"
Cohesion: 0.29
Nodes (6): A faixa está muda o bastante para transcrevê-la ser desperdício? Numa sessão…, track_is_silent(), Faixas mudas não valem uma transcrição. Numa sessão sem Discord a faixa dele é…, -40 dBFS é fala baixa de verdade; pular isso perderia conversa., Na dúvida, transcreve: perder fala é pior que gastar tempo., SilentTrackTests

### Community 12 - "post"
Cohesion: 0.17
Nodes (16): cancel_video_audio_track_job(), cancel_video_audio_tracks(), capture_action(), generate_summary_now(), join_video_session(), preserve_video(), process_video(), Substitui um clipe pelo intervalo escolhido e invalida a análise antiga. (+8 more)

### Community 13 - "winscreen.py"
Cohesion: 0.16
Nodes (12): Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.…, read_shell_config(), _as_bool(), _as_float(), _as_int(), main(), _parse_config(), Laço contínuo de captura de telas — porte de ``bin/capture-loop`` para Python.… (+4 more)

### Community 14 - "WindowsServiceManager"
Cohesion: 0.21
Nodes (3): Supervisor: mantém os processos de captura vivos e agenda o processamento. Vive…, Combine selective-video and user-idle pauses without racing them. Audio and…, WindowsServiceManager

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "ActionResult"
Cohesion: 0.18
Nodes (7): Uma unit transitória coletada equivale a um job já parado., stop_target_is_already_gone(), ActionResult, Mesma forma de ``subprocess.CompletedProcess`` nos campos que importam., SystemdServiceManager, Sem systemd, o estado é 'unknown' — nunca uma exceção que derruba a API., SystemdFallbackTests

### Community 18 - "LinuxCaptureBackend"
Cohesion: 0.13
Nodes (9): LinuxAudioTrackTests, Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., Gravação em faixas separadas (3 canais) no backend Linux., ScreenConfigTests, AudioConfig, Como gravar áudio: fontes e formato do WAV alvo do whisper., LinuxCaptureBackend, argv do ffmpeg que grava mic + Discord + sistema num WAV de 3 canais. Mesmo… (+1 more)

### Community 19 - "initialize"
Cohesion: 0.14
Nodes (24): initialize(), _activity_groups(), apply_exact_game_durations(), daily_narrative_target(), discover(), game_activity_rows(), generate_hourly_summaries(), generate_summary() (+16 more)

### Community 20 - "Path"
Cohesion: 0.11
Nodes (26): _delete_media_sidecars(), delete_video_caches(), directory_stats(), ensure_video_thumbnail(), migrate_legacy_cache_file(), probe_video_audio_tracks(), probe_video_duration(), Path (+18 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.21
Nodes (20): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+12 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 25 - "Monitor"
Cohesion: 0.20
Nodes (7): ImageDiffTests, Monitor, Um monitor físico: rótulo estável + geometria em pixels do desktop., Path, Nomes de dispositivos de áudio que o ``dshow`` enxerga. Dois formatos de saída…, Dispositivo dshow capaz de gravar a saída, se algum existir. Só diagnóstico: a…, WindowsCaptureBackend

### Community 27 - "WasapiError"
Cohesion: 0.22
Nodes (4): GUID, Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, OSError

### Community 29 - "set_video_settings"
Cohesion: 0.21
Nodes (14): _apply_storage_runtime(), _apply_video_runtime(), atomic_write_if_changed(), get_storage_settings(), Write a config only when its contents changed., _report_runtime_failure(), _restart_screen_runtime(), set_storage_settings() (+6 more)

### Community 30 - "RuntimeError"
Cohesion: 0.19
Nodes (11): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas., Devolve os tempos do áudio condensado para o eixo do áudio original. Sem isto…, Transcreve um WAV mono 16 kHz, pulando os trechos sem som. Cada trecho vira um…, _read_whisper_json(), remap_to_source(), _whisper_batch() (+3 more)

### Community 31 - "audio-bus.sh"
Cohesion: 0.34
Nodes (13): load_loopback(), make_null_sink(), selected_mic(), setup(), audio-bus.sh script, sink_exists(), source_exists(), status() (+5 more)

### Community 32 - "src-backup-2026-08-09/api.ts"
Cohesion: 0.07
Nodes (26): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+18 more)

### Community 33 - "src-backup-2026-08-09/main.tsx"
Cohesion: 0.10
Nodes (5): EditableVideoSpeaker, icons, labels, Panel, View

### Community 34 - "get"
Cohesion: 0.11
Nodes (29): backfill_confirmed_voice_observations(), capture_days(), enqueue_unprocessed(), enroll_voice_identity(), generate_hourly_now(), get_cleanup_settings(), get_video_settings(), health() (+21 more)

### Community 35 - "_call"
Cohesion: 0.29
Nodes (14): _call(), _check(), default_endpoint_name(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints(), Invoca o método ``index`` da vtable de uma interface COM. (+6 more)

### Community 37 - "main.py"
Cohesion: 0.12
Nodes (33): atomic_write(), CleanupSettings, ContextUpdate, create_video_marker(), create_video_session(), get_sensitive_windows(), list_voice_identities(), MarkerCreate (+25 more)

### Community 38 - "test_services.py"
Cohesion: 0.16
Nodes (11): ObsWindowSpecTests, PrivacyTests, Testes das peças que tornam o app portável entre Linux e Windows. Rodam nos…, O identificador de janela do OBS é ``título:classe:executável``. Um título com…, ResamplerTests, StereoAudioTests, VideoMarkerTransitionTests, Meter (+3 more)

### Community 39 - "run"
Cohesion: 0.16
Nodes (18): _audio_channels(), audio_file(), _audio_streams(), capture_speaker_sample(), import_video(), list_files(), process_file(), ProcessFileRequest (+10 more)

### Community 45 - "winrecord.py"
Cohesion: 0.15
Nodes (12): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _mix(), _multichannel(), array, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.…, Soma as fontes com saturação e converte para PCM s16le. (+4 more)

### Community 46 - "MarkerHotkey"
Cohesion: 0.16
Nodes (6): HudSettings, Preferências da HUD, lidas de ``video.conf``., log(), MarkerHotkey, Atalhos globais no Windows, registrados fora de qualquer janela. No Linux o…, Atalho global que chama ``on_press`` a cada acionamento.

### Community 47 - "local_origin_only"
Cohesion: 0.22
Nodes (9): bounded_video_range(), local_origin_only(), origin_allowed(), Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., remote_client_allowed(), video_file(), middleware, Request (+1 more)

### Community 48 - "media_source_key"
Cohesion: 0.11
Nodes (27): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., backfill_video_session_durations(), list_video_sessions(), _config_dir(), configured_storage_root() (+19 more)

### Community 49 - "HudEventAnimationTests"
Cohesion: 0.17
Nodes (9): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., ease_out_back(), event_animation(), Passa um pouco do alvo e volta. É o que separa "apareceu" de "chegou": sem o… (+1 more)

### Community 50 - "get_manager"
Cohesion: 0.18
Nodes (11): cancel_video_audio_track_jobs(), get_schedule(), lifespan(), migrate_legacy_media_caches(), process_video_session_job(), Move caches antigos do perfil para a raiz de armazenamento selecionada., ScheduleSettings, set_schedule() (+3 more)

### Community 51 - "hudsource.py"
Cohesion: 0.05
Nodes (31): _app_label(), _count_markers(), _elapsed(), get_collector(), _Growth, HudCollector, LinuxHudCollector, log() (+23 more)

### Community 52 - "Hud"
Cohesion: 0.15
Nodes (11): _alert_sound(), Hud, log(), main(), _probe(), Aviso audível de falha, distinto do bipe de marcador. O marcador toca um par…, Laço da interface: coleta, avalia, desenha e avisa., Aplica queda suave às barras, para o medidor não piscar. (+3 more)

### Community 53 - "ServiceManager"
Cohesion: 0.10
Nodes (12): ABC, Executa ``start``/``stop``/``restart``/``try-restart``/``enable``/``disable``., Horário configurado do processamento noturno e se está ativo., Reprograma o processamento noturno., Dispara um job avulso sob um nome de unit, para poder cancelá-lo depois. É o…, Reinicia a própria interface (usado ao trocar o local dos dados)., Chamado quando a API sobe., Chamado quando a API desce. (+4 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.07
Nodes (12): CAPTION_LABELS, CAPTION_ORDER, CapturaTab, dayViews, EditableVideoSpeaker, gameCovers, icons, labels (+4 more)

### Community 55 - "App"
Cohesion: 0.20
Nodes (11): Capture, CleanupSettings, PipelineQueue, ScreenSequenceResult, Status, uploadVideo(), VideoSettings, App() (+3 more)

### Community 56 - "videoTime"
Cohesion: 0.15
Nodes (15): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SessionCard(), sessionDuration() (+7 more)

### Community 57 - "capture_frames"
Cohesion: 0.23
Nodes (12): capture_change_test_frames(), capture_frames(), compare_screen_change_test(), get_screen_settings(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver. A mesma regra nos dois…, Captura um conjunto de frames com a configuração atual., screen_change_percent() (+4 more)

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers. Média…, Um fluxo de captura: microfone padrão ou loopback da saída padrão. A saída de…, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio). Um fluxo…, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "test_main.py"
Cohesion: 0.20
Nodes (22): compact_processed_audio(), compact_saved_capture(), describe_screen(), known_voice_profiles(), marker_visual_title(), monitor_key(), process_pending(), process_specific() (+14 more)

### Community 61 - "pipeline.py"
Cohesion: 0.19
Nodes (26): adaptive_web_research(), analyze_video_chapter(), audio_channel_count(), audio_stream_count(), describe_long_video(), describe_video(), extract_adaptive_keyframes(), format_video_time() (+18 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.17
Nodes (11): blend(), EventFrame, HudPanel, Mistura duas cores ``#rrggbb``. O Canvas do tkinter não tem canal alfa por…, Um quadro da animação de confirmação. ``reveal`` é o quanto o evento tomou o…, Um painel desenhado num monitor., Corta pela largura real do texto, não por contagem de caracteres. A HUD mistura…, Barra mínima. O evento entra por baixo empurrando o conteúdo normal. Não há… (+3 more)

### Community 64 - "HudStateTests"
Cohesion: 0.25
Nodes (3): HudStateTests, As regras que decidem se a captura está saudável. Rodam nos dois sistemas de…, Ficar calado é normal; confundir com falha destrói a confiança na HUD.

### Community 65 - "thumbnail"
Cohesion: 0.19
Nodes (9): Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg. O laço de captura do Linux usa…, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar., Diferença percentual entre dois arquivos de imagem. (+1 more)

### Community 67 - "wasapi.py"
Cohesion: 0.15
Nodes (12): _ActivationHandler, _AudioClientActivationParams, _Blob, _LazyOle32, PROPERTYKEY, PROPVARIANT, _PropVariantBlob, Captura de áudio WASAPI em ``ctypes`` puro (Windows). Existe porque o ffmpeg no… (+4 more)

### Community 68 - "HudPlacementTests"
Cohesion: 0.23
Nodes (6): HudPlacementTests, Onde a HUD desenha, dado o arranjo de monitores., Com um monitor só, "no outro monitor" tem que recair sobre este., choose_monitors(), corner_position(), Monitores que devem receber um painel. Função pura para poder ser testada sem…

### Community 69 - "hud.py"
Cohesion: 0.11
Nodes (17): _assert_topmost(), _declare_dpi_aware(), _demo_sequence(), ease_in_cubic(), ease_out_cubic(), _make_overlay(), HUD de gravação: uma faixa sobre o jogo dizendo se a captura está saindo. Roda…, Coordenadas em pixels reais, antes de qualquer janela existir. Sem isto o… (+9 more)

### Community 70 - "HudSnapshot"
Cohesion: 0.26
Nodes (10): Alert, _disk_alerts(), evaluate(), HudSnapshot, _meter_alerts(), Estado da HUD de gravação: instantâneo portátil e regras de saúde. Este módulo…, Há captura de vídeo em curso, gravando ou em buffer de clipes., Traduz um instantâneo em alertas e num veredito único. Função pura: mesma… (+2 more)

### Community 71 - "VideoActivityFlagTests"
Cohesion: 0.43
Nodes (3): O sinal de atividade tem um significado só, e ele é caro de errar. Enquanto o…, Dois marcadores seguidos têm o mesmo rótulo; só a sequência os separa., VideoActivityFlagTests

### Community 72 - ".tick"
Cohesion: 0.47
Nodes (4): _monitor_key(), Path, Identidade do monitor a partir do nome do arquivo (``..._mon1_DP-1.png``). A…, _thumbnail()

### Community 74 - "runtime_dir"
Cohesion: 0.23
Nodes (10): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows. Centraliza as poucas…, Diretório para arquivos efêmeros (locks, estado volátil). Linux usa…, Arquivo que sinaliza "estou gravando vídeo agora". É como o laço de vídeo pede…, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``. Retorna ``True`` se conseguiu…, runtime_dir() (+2 more)

### Community 75 - ".action"
Cohesion: 0.23
Nodes (5): Arquivo de estado que o laço de vídeo cria enquanto controla as capturas. Mesma…, Anota que a captura deve (ou não) voltar na próxima abertura do Lume. No Linux…, Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., _unknown(), _video_pause_file()

### Community 76 - "windows_startup.py"
Cohesion: 0.60
Nodes (4): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows. Executado com ``pythonw.exe``…

### Community 77 - "UnitResolutionTests"
Cohesion: 0.36
Nodes (3): Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), UnitResolutionTests

### Community 78 - "VideoSettings"
Cohesion: 0.09
Nodes (17): VideoSettings, group_regions(), Trechos ``(início, fim)`` em segundos onde há som acima do limiar. Função pura…, Agrupa trechos vizinhos em blocos que caibam numa janela do whisper. Dois…, speech_regions(), Detecção dos trechos com som, sobre amostras sintéticas., A folga não pode gerar tempo negativo nem passar do fim do áudio., Blocos que enchem uma janela do whisper sem esticar o eixo do tempo. O whisper… (+9 more)

### Community 79 - "Path"
Cohesion: 0.18
Nodes (5): Path, skipUnless, SupervisorTests, VideoHotkeyTests, VideoSettingsTests

### Community 80 - "HudEventContractTests"
Cohesion: 0.31
Nodes (5): HudEventContractTests, O evento cruza dois processos por um arquivo; o formato é um contrato. O…, Um tipo sem estilo seria um evento invisível — falha silenciosa., _event_fields(), Extrai o acontecimento pontual publicado pelo laço de vídeo. A idade vem do…

### Community 81 - "services.py"
Cohesion: 0.22
Nodes (7): _JobObject, _pipeline(), _python(), Gerenciamento de serviços independente de sistema operacional. No Linux o…, Amarra os processos filhos ao ciclo de vida da API. É o que o systemd consegue…, Return seconds since the last real keyboard or mouse input on Windows., windows_idle_seconds()

### Community 82 - "._start"
Cohesion: 0.18
Nodes (7): _Process, Path, Popen, (Re)inicia o swayidle apontando os eventos para o flag de idle., Uma unit supervisionada. ``simple`` roda enquanto o serviço estiver ligado (e…, Um processo filho supervisionado., _UnitDef

### Community 84 - "matched_sensitive_pattern"
Cohesion: 0.18
Nodes (7): matched_sensitive_pattern(), Path, Primeiro padrão sensível (regex, case-insensitive) que casa com a janela. Mesma…, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados. ``stamp``…, Lista de expressões de um arquivo de padrões, ignorando comentários., read_patterns(), Motivo para não capturar agora, ou ``None`` se pode capturar.

### Community 85 - "HudFrameRateTests"
Cohesion: 0.33
Nodes (3): HudFrameRateTests, Uma entrada de 0,26 s precisa de quadros suficientes para não escadear., As três cadências existem por causa do custo de redesenhar. Cada volta recria…

### Community 86 - "get_backend"
Cohesion: 0.20
Nodes (11): Valores de ``tela.conf`` relevantes para a captura de um frame., ScreenConfig, get_backend(), Seleção automática do backend de captura conforme o sistema operacional. Uso:…, Devolve o backend do SO atual (memorizado). ``force``…, Path, Backend de captura para Linux (PipeWire + KDE/Wayland). Delega para os scripts…, main() (+3 more)

### Community 87 - "analyze_screen_sequence"
Cohesion: 0.40
Nodes (5): _activity_image(), analyze_screen_sequence(), process_screen_sequence_job(), JPEG de trabalho: reduz custo visual sem alterar o print original., Analisa uma seleção manual de prints como uma única sequência temporal.

### Community 89 - "LinuxIdlePauseTests"
Cohesion: 0.33
Nodes (3): LinuxIdlePauseTests, _pausable(), Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO).

### Community 91 - "recover_json_from_thinking"
Cohesion: 0.33
Nodes (3): parse_json_response(), Recupera JSON que o parser do Ollama classificou todo como thinking., recover_json_from_thinking()

## Knowledge Gaps
- **103 isolated node(s):** `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` (+98 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `ActionResult` to `ConfigTests`, `connect`, `track_is_silent`, `post`, `WindowsServiceManager`, `LinuxCaptureBackend`, `Path`, `Monitor`, `set_video_settings`, `get`, `main.py`, `test_services.py`, `run`, `HudEventAnimationTests`, `get_manager`, `ServiceManager`, `capture_frames`, `test_main.py`, `HudStateTests`, `HudPlacementTests`, `VideoActivityFlagTests`, `.action`, `UnitResolutionTests`, `VideoSettings`, `Path`, `HudEventContractTests`, `services.py`, `._start`, `HudFrameRateTests`, `VideoReplayClipTests`, `LinuxIdlePauseTests`?**
  _High betweenness centrality (0.108) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `VideoSettings`, `local_origin_only`, `ActionResult`, `patch`, `pipeline.py`, `audio_intelligence.py`, `speaker_profiles`, `recover_json_from_thinking`, `test_main.py`, `captured_video_session`, `RuntimeError`?**
  _High betweenness centrality (0.057) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `ActionResult` to `ConfigTests`, `track_is_silent`, `LinuxCaptureBackend`, `Monitor`, `test_services.py`, `HudEventAnimationTests`, `get_manager`, `ServiceManager`, `test_main.py`, `HudStateTests`, `HudPlacementTests`, `VideoActivityFlagTests`, `runtime_dir`, `.action`, `UnitResolutionTests`, `VideoSettings`, `Path`, `HudEventContractTests`, `services.py`, `._start`, `HudFrameRateTests`, `VideoReplayClipTests`, `LinuxIdlePauseTests`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Are the 49 inferred relationships involving `ActionResult` (e.g. with `CleanupSettings` and `ContextUpdate`) actually correct?**
  _`ActionResult` has 49 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `ActionResult`) actually correct?**
  _`ConfigTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 27 inferred relationships involving `SystemdServiceManager` (e.g. with `ConfigTests` and `RegionGroupingTests`) actually correct?**
  _`SystemdServiceManager` has 27 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `HudSnapshot` (e.g. with `HudEventAnimationTests` and `HudEventContractTests`) actually correct?**
  _`HudSnapshot` has 30 INFERRED edges - model-reasoned connections that need verification._