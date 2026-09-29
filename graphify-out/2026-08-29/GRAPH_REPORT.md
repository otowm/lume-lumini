# Graph Report - lume  (2026-08-29)

## Corpus Check
- 57 files · ~96,720 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1612 nodes · 4054 edges · 87 communities (74 shown, 13 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 398 edges (avg confidence: 0.52)
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
- connect
- Lume no Windows
- test_main.py
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
- ._dshow_loopback
- add-video-marker
- WasapiError
- install-captura-dia.sh
- LinuxHudCollector
- SpeechRegionTests
- audio-bus.sh
- src-backup-2026-08-09/api.ts
- src-backup-2026-08-09/main.tsx
- get
- _call
- capture-loop
- main.py
- hud.py
- ._start
- grava-audio.sh
- install-lume.sh
- install-user.sh
- prompts.py
- winrecord.py
- VideoSettings
- WindowsHudCollector
- media_source_key
- run
- recover_json_from_thinking
- _event_fields
- resolve_media_source
- ServiceManager
- src/main.tsx
- App
- videoTime
- filter_hallucinated_segments
- WasapiCapture
- videoTime
- generate_summary
- pipeline.py
- App
- HudPanel
- HudStateTests
- local_origin_only
- wasapi.py
- HudPlacementTests
- PromptSettingsTests
- HudCollector
- thumbnail
- _Growth
- capture_frames
- services.py
- windows_startup.py
- _resolve
- ScreenLoop
- Path
- get_backend
- winscreen.py
- RegionGroupingTests
- RemapToSourceTests
- matched_sensitive_pattern
- HudStatus
- to_db

## God Nodes (most connected - your core abstractions)
1. `ConfigTests` - 90 edges
2. `ActionResult` - 88 edges
3. `connect()` - 86 edges
4. `SystemdServiceManager` - 54 edges
5. `HudSnapshot` - 54 edges
6. `VideoLoop` - 52 edges
7. `Monitor` - 49 edges
8. `Hud` - 47 edges
9. `Meter` - 47 edges
10. `WindowsCaptureBackend` - 43 edges

## Surprising Connections (you probably didn't know these)
- `ProcessFileRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `VideoProcessRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `VideoTrimRequest` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `SpeakerLabelUpdate` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py
- `VideoSettings` --uses--> `ActionResult`  [INFERRED]
  app/backend/main.py → app/backend/services.py

## Import Cycles
- None detected.

## Communities (87 total, 13 thin omitted)

### Community 0 - "ConfigTests"
Cohesion: 0.06
Nodes (8): captured_video_session(), Lê a identidade portátil deixada pelo gravador seletivo. Vídeos antigos só têm…, ConfigTests, Path, skipUnless, A média vem do tempo real medido, não do intervalo entre capturas., Sem amostra do tipo pendente, um palpite atrapalharia mais que ajudar., patch

### Community 1 - "src/api.ts"
Cohesion: 0.06
Nodes (31): ActivityFrame, ActivitySession, AnalysisTrace, api, AudioEvent, DaySummary, HourSummary, OllamaModel (+23 more)

### Community 2 - "package.json"
Cohesion: 0.09
Nodes (22): dependencies, react, react-dom, devDependencies, @types/react, @types/react-dom, typescript, vite (+14 more)

### Community 3 - "compilerOptions"
Cohesion: 0.09
Nodes (22): compilerOptions, allowJs, allowSyntheticDefaultImports, esModuleInterop, forceConsistentCasingInFileNames, isolatedModules, jsx, lib (+14 more)

### Community 4 - "base.py"
Cohesion: 0.09
Nodes (17): CaptureBackend, ABC, Interface comum de captura, independente de sistema operacional. Cada SO…, Contrato que Linux e Windows implementam., Texto ``"<título> | <classe/processo>"`` da janela em foco. Retorna ``None``…, Monitores habilitados, em ordem estável de índice., Monitor que contém a janela em foco, se determinável., Prepara o roteamento de áudio (no-op onde não for necessário). (+9 more)

### Community 5 - "obs.py"
Cohesion: 0.06
Nodes (57): any_fullscreen(), batch(), call(), _copy_installation(), diagnostics(), _encode_field(), ensure_scene(), find_installation() (+49 more)

### Community 6 - "record"
Cohesion: 0.17
Nodes (10): ProcessLoopbackCapture, Loopback que inclui ou exclui a árvore de um processo do Windows., Path, Uma fonte de áudio que se reabre sozinha quando o dispositivo cai., Puxa o que houver do dispositivo para o buffer interno., Retira ``count`` amostras, completando com silêncio se faltar., Escreve WAVs sequenciais com o mesmo nome que o Linux produz., record() (+2 more)

### Community 7 - "Handoff: Lume — app de memória de tela & áudio"
Cohesion: 0.12
Nodes (16): 1. Busca (tela principal / default), 2. Resumo do dia, 3. Jogos, 4. Linha do tempo, About the Design Files, Assets, Design Tokens (Nocturne), Fidelity (+8 more)

### Community 8 - "VideoLoop"
Cohesion: 0.06
Nodes (27): parse_video_app_rule(), Separa metadados de ``[modo fps=N geometry=WxH source=game|window] regex``., log(), MarkerHotkey, Atalhos globais no Windows, registrados fora de qualquer janela. No Linux o…, Atalho global que chama ``on_press`` a cada acionamento., foreground_details(), log() (+19 more)

### Community 9 - "connect"
Cohesion: 0.10
Nodes (44): connect(), initialize(), cancel_entire_queue(), cancel_pipeline(), cancel_queue_item(), cancel_screen_sequence(), cancel_video_analysis(), cancel_video_session() (+36 more)

### Community 10 - "Lume no Windows"
Cohesion: 0.07
Nodes (24): Como está dividido, Como validar, Convenções, Decisões que não são óbvias, Estado do port para Windows, O que falta, captura-dia, Estrutura instalada (+16 more)

### Community 11 - "test_main.py"
Cohesion: 0.10
Nodes (15): voice_identity_payloads(), _activity_groups(), merge_source_transcripts(), merge_transcript_sources(), private_context_terms(), Separa por aplicativo e continuidade; mudanças de título não quebram a sessão., Pico de um WAV PCM 16 bits, em dBFS. ``-inf`` vira o piso -99., A faixa está muda o bastante para transcrevê-la ser desperdício? Numa sessão… (+7 more)

### Community 12 - "test_services.py"
Cohesion: 0.08
Nodes (35): SystemdServiceManager, HudEventContractTests, HudFrameRateTests, ImageDiffTests, LinuxAudioTrackTests, ObsWindowSpecTests, PrivacyTests, Testes das peças que tornam o app portável entre Linux e Windows. Rodam nos… (+27 more)

### Community 13 - ".action"
Cohesion: 0.14
Nodes (4): Arquivo de estado que o laço de vídeo cria enquanto controla as capturas. Mesma…, (Re)inicia o swayidle apontando os eventos para o flag de idle., _unknown(), _video_pause_file()

### Community 14 - "WindowsServiceManager"
Cohesion: 0.17
Nodes (5): Supervisor: mantém os processos de captura vivos e agenda o processamento. Vive…, Anota que a captura deve (ou não) voltar na próxima abertura do Lume. No Linux…, Resolve a unit, incluindo os jobs avulsos registrados em tempo de execução., Combine selective-video and user-idle pauses without racing them. Audio and…, WindowsServiceManager

### Community 15 - "game-video-loop"
Cohesion: 0.26
Nodes (9): game-video-loop script, cleanup(), finish_segment(), graphical_session_ready(), is_selected_app(), log(), pause_background_captures(), refresh_graphical_environment() (+1 more)

### Community 16 - "runtime_dir"
Cohesion: 0.23
Nodes (10): exclusive_lock(), Path, Helpers de runtime que funcionam igual em Linux e Windows. Centraliza as poucas…, Diretório para arquivos efêmeros (locks, estado volátil). Linux usa…, Arquivo que sinaliza "estou gravando vídeo agora". É como o laço de vídeo pede…, Sinaliza que o OBS está gravando ou mantendo o Replay Buffer ativo., Trava exclusiva e não-bloqueante sobre ``path``. Retorna ``True`` se conseguiu…, runtime_dir() (+2 more)

### Community 18 - "HudSnapshot"
Cohesion: 0.10
Nodes (18): _alert_sound(), _demo_sequence(), Hud, HudSettings, log(), main(), _probe(), Aviso audível de falha, distinto do bipe de marcador. O marcador toca um par… (+10 more)

### Community 19 - "hudsource.py"
Cohesion: 0.14
Nodes (12): Nome estável para ``<título> | <executável>``. Alguns jogos, especialmente…, Lê um arquivo ``CHAVE=valor`` no formato que os scripts do Linux usam.…, read_shell_config(), stable_app_label(), _app_label(), _elapsed(), _focus_grace_remaining(), log() (+4 more)

### Community 20 - "Path"
Cohesion: 0.09
Nodes (36): cancel_video_audio_track_job(), cancel_video_audio_track_jobs(), cancel_video_audio_tracks(), _delete_media_sidecars(), delete_video(), delete_video_caches(), directory_stats(), ensure_video_thumbnail() (+28 more)

### Community 23 - "audio_intelligence.py"
Cohesion: 0.14
Nodes (22): analyze_video_audio(), audio_channel_count(), audio_stream_count(), available(), clean_speaker_turns(), consolidate_events(), detect_events(), diarize() (+14 more)

### Community 24 - "capture-frame"
Cohesion: 0.31
Nodes (5): capture-frame script, capture_grim_one(), capture_spectacle(), finish_image(), usage()

### Community 27 - "WasapiError"
Cohesion: 0.22
Nodes (4): GUID, Falha numa chamada COM do WASAPI, com o HRESULT preservado., WasapiError, OSError

### Community 29 - "LinuxHudCollector"
Cohesion: 0.22
Nodes (8): _count_markers(), LinuxHudCollector, Path, Estado derivado do laço bash e medidores lidos dos buses do PipeWire. O…, Segmento sendo escrito agora pelo ``gpu-screen-recorder``., Janela em foco, com a mesma cadência do laço bash (2 s). O sidecar ``.window``…, Há quanto tempo o segmento em curso começou. Vem do nome do arquivo, não do…, _segment_elapsed()

### Community 30 - "SpeechRegionTests"
Cohesion: 0.36
Nodes (5): Trechos ``(início, fim)`` em segundos onde há som acima do limiar. Função pura…, speech_regions(), Detecção dos trechos com som, sobre amostras sintéticas., A folga não pode gerar tempo negativo nem passar do fim do áudio., SpeechRegionTests

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
Cohesion: 0.09
Nodes (34): row_dict(), _audio_channels(), capture_days(), capture_payload(), capture_speed_stats(), captures(), delete_unprocessed_files(), delete_voice_identity() (+26 more)

### Community 35 - "_call"
Cohesion: 0.29
Nodes (14): _call(), _check(), default_endpoint_name(), _device_enumerator(), ensure_com(), _friendly_name(), list_endpoints(), Invoca o método ``index`` da vtable de uma interface COM. (+6 more)

### Community 37 - "main.py"
Cohesion: 0.10
Nodes (48): _apply_storage_runtime(), _apply_video_runtime(), atomic_write(), atomic_write_if_changed(), CleanupSettings, ContextUpdate, get_schedule(), get_sensitive_windows() (+40 more)

### Community 38 - "hud.py"
Cohesion: 0.08
Nodes (24): HudEventAnimationTests, A curva da animação de confirmação, sem abrir janela nenhuma., O repique é o que separa "apareceu" de "chegou"., Uma cor que passa do alvo não existe; um movimento que passa, sim., O OBS leva segundos para informar o arquivo; a faixa espera por ele., _assert_topmost(), _declare_dpi_aware(), ease_in_cubic() (+16 more)

### Community 39 - "._start"
Cohesion: 0.36
Nodes (4): _Process, Path, Popen, Um processo filho supervisionado.

### Community 43 - "prompts.py"
Cohesion: 0.21
Nodes (17): get_prompts(), reset_prompt(), active_template(), listing(), _overrides(), payload(), PromptError, PromptSpec (+9 more)

### Community 45 - "winrecord.py"
Cohesion: 0.15
Nodes (12): dbfs(), Pico linear (0..1) em dBFS; ``-inf`` para silêncio digital., discord_process_id(), _mix(), _multichannel(), array, Gravador de áudio contínuo do Windows — o equivalente ao RecordBus do Linux.…, Soma as fontes com saturação e converte para PCM s16le. (+4 more)

### Community 46 - "VideoSettings"
Cohesion: 0.17
Nodes (13): get_video_settings(), lifespan(), migrate_legacy_media_caches(), parse_shell_config(), Move caches antigos do perfil para a raiz de armazenamento selecionada., set_video_settings(), VideoSettings, Salvar as preferências não pode apagar chaves silenciosamente.… (+5 more)

### Community 48 - "media_source_key"
Cohesion: 0.12
Nodes (22): _merge_portable_paths(), migrate_media_paths(), _path_survivor(), Consolida identidades absolutas do Linux/Windows sem perder análises., _config_dir(), configured_storage_root(), media_source_key(), media_source_name() (+14 more)

### Community 49 - "run"
Cohesion: 0.16
Nodes (19): audio_file(), _audio_streams(), capture_speaker_sample(), delete_capture_file(), import_video(), process_file(), ProcessFileRequest, datetime (+11 more)

### Community 52 - "resolve_media_source"
Cohesion: 0.19
Nodes (15): backfill_confirmed_voice_observations(), backfill_video_session_durations(), enroll_voice_identity(), list_video_sessions(), _normalized_average(), Resolve uma identidade portátil ou um caminho legado na raiz atual., resolve_media_source(), Prefer the recorded window title over an AI-generated app guess. (+7 more)

### Community 53 - "ServiceManager"
Cohesion: 0.10
Nodes (12): ABC, Executa ``start``/``stop``/``restart``/``try-restart``/``enable``/``disable``., Horário configurado do processamento noturno e se está ativo., Reprograma o processamento noturno., Dispara um job avulso sob um nome de unit, para poder cancelá-lo depois. É o…, Reinicia a própria interface (usado ao trocar o local dos dados)., Chamado quando a API sobe., Chamado quando a API desce. (+4 more)

### Community 54 - "src/main.tsx"
Cohesion: 0.06
Nodes (15): CAPTION_LABELS, CAPTION_ORDER, CapturaTab, ContextMenuAction, dayViews, EditableVideoSpeaker, gameCovers, icons (+7 more)

### Community 55 - "App"
Cohesion: 0.17
Nodes (13): Capture, CleanupSettings, PipelineQueue, ScreenSequenceResult, Status, uploadVideo(), VideoSettings, analysisAverage() (+5 more)

### Community 56 - "videoTime"
Cohesion: 0.15
Nodes (15): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SessionCard(), sessionDuration() (+7 more)

### Community 57 - "filter_hallucinated_segments"
Cohesion: 0.16
Nodes (10): filter_hallucinated_segments(), normalized_transcript_text(), Remove loops típicos do Whisper em silêncio/ruído sem bloquear frases isoladas., Devolve os tempos do áudio condensado para o eixo do áudio original. Sem isto…, Transcreve um WAV mono 16 kHz, pulando os trechos sem som. Cada trecho vira um…, _read_whisper_json(), remap_to_source(), _whisper_batch() (+2 more)

### Community 58 - "WasapiCapture"
Cohesion: 0.17
Nodes (7): Blocos que não caem em fronteira redonda não podem perder amostras., _BoxResampler, array, Reamostra para 16 kHz por média de blocos, mantendo estado entre buffers. Média…, Um fluxo de captura: microfone padrão ou loopback da saída padrão. A saída de…, Drena os pacotes disponíveis e devolve mono 16 kHz (pode vir vazio). Um fluxo…, WasapiCapture

### Community 59 - "videoTime"
Cohesion: 0.20
Nodes (12): AudioAnalysis(), ChapterReader(), chapterStart(), CustomVideoPlayer(), playerTime(), sampleIsOverlapped(), SyncedAudioPlayer(), videoTime() (+4 more)

### Community 60 - "generate_summary"
Cohesion: 0.13
Nodes (14): apply_exact_game_durations(), daily_narrative_target(), game_activity_rows(), generate_hourly_summaries(), generate_summary(), multimodal_context(), Agrupa telas e áudios sobrepostos em momentos únicos para as sínteses., Sessões monitoradas recortadas ao dia local, inclusive ao cruzar meia-noite. (+6 more)

### Community 61 - "pipeline.py"
Cohesion: 0.11
Nodes (57): _activity_image(), adaptive_web_research(), analyze_screen_sequence(), analyze_video_chapter(), audio_channel_count(), audio_stream_count(), compact_processed_audio(), compact_saved_capture() (+49 more)

### Community 62 - "App"
Cohesion: 0.22
Nodes (9): Capture, Status, uploadVideo(), VideoSettings, App(), groupCaptures(), SessionCard(), sessionDuration() (+1 more)

### Community 63 - "HudPanel"
Cohesion: 0.15
Nodes (12): blend(), EventFrame, HudPanel, Mistura duas cores ``#rrggbb``. O Canvas do tkinter não tem canal alfa por…, Um quadro da animação de confirmação. ``reveal`` é o quanto o evento tomou o…, Um painel desenhado num monitor., Corta pela largura real do texto, não por contagem de caracteres. A HUD mistura…, Barra mínima. O evento entra por baixo empurrando o conteúdo normal. Não há… (+4 more)

### Community 64 - "HudStateTests"
Cohesion: 0.17
Nodes (9): HudStateTests, As regras que decidem se a captura está saudável. Rodam nos dois sistemas de…, Ficar calado é normal; confundir com falha destrói a confiança na HUD., _disk_alerts(), evaluate(), _meter_alerts(), Estado da HUD de gravação: instantâneo portátil e regras de saúde. Este módulo…, Traduz um instantâneo em alertas e num veredito único. Função pura: mesma… (+1 more)

### Community 65 - "local_origin_only"
Cohesion: 0.22
Nodes (9): bounded_video_range(), local_origin_only(), origin_allowed(), Converte um Range HTTP em um bloco limitado, evitando ler um vídeo inteiro., remote_client_allowed(), video_file(), middleware, Request (+1 more)

### Community 67 - "wasapi.py"
Cohesion: 0.15
Nodes (12): _ActivationHandler, _AudioClientActivationParams, _Blob, _LazyOle32, PROPERTYKEY, PROPVARIANT, _PropVariantBlob, Captura de áudio WASAPI em ``ctypes`` puro (Windows). Existe porque o ffmpeg no… (+4 more)

### Community 68 - "HudPlacementTests"
Cohesion: 0.23
Nodes (6): HudPlacementTests, Onde a HUD desenha, dado o arranjo de monitores., Com um monitor só, "no outro monitor" tem que recair sobre este., choose_monitors(), corner_position(), Monitores que devem receber um painel. Função pura para poder ser testada sem…

### Community 69 - "PromptSettingsTests"
Cohesion: 0.13
Nodes (4): PromptSettingsTests, Os prompts sao editaveis, mas nao a ponto de quebrar a analise., Uma variavel esquecida na ficha sumiria do texto sem ninguem notar., Um JSON quebrado nao pode parar a fila inteira.

### Community 70 - "HudCollector"
Cohesion: 0.25
Nodes (5): HudCollector, ABC, Fonte do instantâneo da HUD., Sobe threads de coleta (no-op quando não houver)., Estado atual, já normalizado.

### Community 71 - "thumbnail"
Cohesion: 0.19
Nodes (9): Variação de 5 níveis é ruído de compressão, não mudança de tela., compare_images(), difference_percent(), Path, Comparação visual entre dois frames, com ffmpeg. O laço de captura do Linux usa…, Miniatura em tons de cinza como bytes crus, ou ``None`` se falhar., Percentual de pixels que mudaram além do limiar., Diferença percentual entre dois arquivos de imagem. (+1 more)

### Community 72 - "_Growth"
Cohesion: 0.22
Nodes (4): _Growth, _MeterTracker, Detecta um valor que parou de crescer (bytes escritos, tamanho de arquivo)., Contabilidade temporal de uma fonte de áudio. Guarda desde quando a fonte não…

### Community 74 - "capture_frames"
Cohesion: 0.25
Nodes (11): capture_change_test_frames(), capture_frames(), compare_screen_change_test(), get_screen_settings(), privacy_decision(), Janela ativa e o motivo para não capturar, se houver. A mesma regra nos dois…, Captura um conjunto de frames com a configuração atual., screen_change_percent() (+3 more)

### Community 75 - "services.py"
Cohesion: 0.22
Nodes (7): _JobObject, _pipeline(), _python(), Gerenciamento de serviços independente de sistema operacional. No Linux o…, Amarra os processos filhos ao ciclo de vida da API. É o que o systemd consegue…, Return seconds since the last real keyboard or mouse input on Windows., windows_idle_seconds()

### Community 76 - "windows_startup.py"
Cohesion: 0.60
Nodes (4): _backend_is_running(), _hide_console(), main(), Host invisível do backend no login do Windows. Executado com ``pythonw.exe``…

### Community 77 - "_resolve"
Cohesion: 0.20
Nodes (4): Uma unit supervisionada. ``simple`` roda enquanto o serviço estiver ligado (e…, Encontra a definição da unit e o argumento de template (``@dia``)., _resolve(), _UnitDef

### Community 78 - "ScreenLoop"
Cohesion: 0.22
Nodes (7): main(), _monitor_key(), Path, Identidade do monitor a partir do nome do arquivo (``..._mon1_DP-1.png``). A…, Motivo para não capturar agora, ou ``None`` se pode capturar., ScreenLoop, _thumbnail()

### Community 79 - "Path"
Cohesion: 0.09
Nodes (12): LinuxIdlePauseTests, _pausable(), Path, skipUnless, Um tipo sem estilo seria um evento invisível — falha silenciosa., Editores do Windows gravam UTF-8 com BOM; a config precisa sobreviver., Política de pausa por inatividade do gerenciador systemd (roda em qualquer SO)., O sinal de atividade tem um significado só, e ele é caro de errar. Enquanto o… (+4 more)

### Community 80 - "get_backend"
Cohesion: 0.23
Nodes (10): Valores de ``tela.conf`` relevantes para a captura de um frame., ScreenConfig, get_backend(), Seleção automática do backend de captura conforme o sistema operacional. Uso:…, Devolve o backend do SO atual (memorizado). ``force``…, Path, main(), _measure_volume() (+2 more)

### Community 81 - "winscreen.py"
Cohesion: 0.23
Nodes (8): _as_bool(), _as_float(), _as_int(), _parse_config(), Laço contínuo de captura de telas — porte de ``bin/capture-loop`` para Python.…, Lê o ``tela.conf`` (formato ``CHAVE=valor`` do shell)., Instantâneo do ``tela.conf``, relido quando o arquivo muda no disco., _Settings

### Community 82 - "RegionGroupingTests"
Cohesion: 0.31
Nodes (5): group_regions(), Agrupa trechos vizinhos em blocos que caibam numa janela do whisper. Dois…, Blocos que enchem uma janela do whisper sem esticar o eixo do tempo. O whisper…, É o teto que impede um erro de 1 s virar 20 s ao voltar ao original., RegionGroupingTests

### Community 83 - "RemapToSourceTests"
Cohesion: 0.33
Nodes (3): Voltar os tempos do bloco para o eixo do áudio original. É a parte que, errada,…, Fim antes do início quebraria a ordenação e a legenda., RemapToSourceTests

### Community 84 - "matched_sensitive_pattern"
Cohesion: 0.22
Nodes (6): matched_sensitive_pattern(), Path, Lista de expressões de um arquivo de padrões, ignorando comentários., Primeiro padrão sensível (regex, case-insensitive) que casa com a janela. Mesma…, Captura e grava PNG(s) em ``dest_dir``; retorna os caminhos criados. ``stamp``…, read_patterns()

### Community 86 - "to_db"
Cohesion: 0.40
Nodes (3): Lê PCM cru do monitor de um bus e acumula o pico. Taxa baixa e um canal de…, Converte multiplicador linear (0..1) para dBFS, com piso em silêncio., to_db()

## Knowledge Gaps
- **107 isolated node(s):** `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem`, `AnalysisTrace`, `ActivityFrame` (+102 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ActionResult` connect `main.py` to `ConfigTests`, `connect`, `test_main.py`, `test_services.py`, `.action`, `WindowsServiceManager`, `Path`, `SpeechRegionTests`, `hud.py`, `._start`, `VideoSettings`, `run`, `resolve_media_source`, `ServiceManager`, `HudStateTests`, `HudPlacementTests`, `PromptSettingsTests`, `capture_frames`, `services.py`, `_resolve`, `Path`, `RegionGroupingTests`, `RemapToSourceTests`, `HudStatus`?**
  _High betweenness centrality (0.122) - this node is a cross-community bridge._
- **Why does `ConfigTests` connect `ConfigTests` to `local_origin_only`, `main.py`, `test_main.py`, `test_services.py`, `VideoSettings`, `recover_json_from_thinking`, `audio_intelligence.py`, `filter_hallucinated_segments`, `generate_summary`, `pipeline.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `SystemdServiceManager` connect `test_services.py` to `ConfigTests`, `HudStateTests`, `HudPlacementTests`, `PromptSettingsTests`, `hud.py`, `connect`, `services.py`, `test_main.py`, `.action`, `VideoSettings`, `Path`, `runtime_dir`, `RegionGroupingTests`, `RemapToSourceTests`, `ServiceManager`, `HudStatus`, `SpeechRegionTests`?**
  _High betweenness centrality (0.053) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `ConfigTests` (e.g. with `VideoSettings` and `ActionResult`) actually correct?**
  _`ConfigTests` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 53 inferred relationships involving `ActionResult` (e.g. with `CleanupSettings` and `ContextUpdate`) actually correct?**
  _`ActionResult` has 53 INFERRED edges - model-reasoned connections that need verification._
- **Are the 30 inferred relationships involving `SystemdServiceManager` (e.g. with `ConfigTests` and `PromptSettingsTests`) actually correct?**
  _`SystemdServiceManager` has 30 INFERRED edges - model-reasoned connections that need verification._
- **What connects `WAVEFORMATEXTENSIBLE`, `PROPERTYKEY`, `SummaryMediaItem` to the rest of the system?**
  _107 weakly-connected nodes found - possible documentation gaps or missing edges._