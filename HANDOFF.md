# Estado do port para Windows

Um app só, o mesmo código nos dois sistemas. O usuário troca de SO com
frequência e quer abrir o Lume nos dois e simplesmente funcionar.

O "cérebro" (FastAPI, UI, SQLite+FTS5, pipeline) sempre foi portável. O
acoplamento com Linux estava em duas camadas — **captura** e **orquestração** —
e as duas já foram portadas. Detalhes de uso estão em [WINDOWS.md](WINDOWS.md);
aqui fica só o que interessa a quem for mexer no código.

## Como está dividido

- `app/capture/` — captura por sistema, atrás de `CaptureBackend`
  (`base.py`). `get_backend()` escolhe pelo SO; ninguém fora daqui chama
  `pactl`, `spectacle`, `dshow` ou Win32.
  - `linux.py` delega aos scripts já instalados em `~/bin` — decisão
    deliberada de preservar o comportamento do Linux 1:1.
  - `windows.py` usa `ctypes` (janela ativa, monitores) e ffmpeg `gdigrab`
    (telas).
  - `wasapi.py` é o loopback da saída do sistema em `ctypes` puro; `winrecord.py`
    mixa mic + saída num WAV mono 16 kHz; `winscreen.py` é o porte de
    `bin/capture-loop`; `imagediff.py` é a comparação 320x180 com ffmpeg.
  - `obs.py` e `winvideo.py` são o porte de `bin/game-video-loop`: uma cópia
    portátil do OBS em `~/.lume-obs`, dirigida por obs-websocket.
  - `hudstate.py`, `hudsource.py` e `hud.py` são a HUD de gravação, na mesma
    divisão: as regras de saúde são puras e portáteis (`hudstate`), a coleta tem
    uma implementação por SO (`hudsource`) e a janela é única (`hud`).
  - `winhotkey.py` tem o `MarkerHotkey` (`RegisterHotKey` + fila de mensagens),
    usado tanto pela gravação quanto pela HUD, em processos separados.
- `app/backend/services.py` — `ServiceManager`: `systemctl --user` no Linux,
  supervisor de processos no Windows. `main.py` só fala com ele
  (`unit_state()`, `service_action()`, `get_manager()`), tratando nomes de unit
  como identificadores opacos.
- `app/backend/runtime.py` — `runtime_dir()` e `exclusive_lock()` (fcntl/msvcrt).
- `app/backend/main_paths.py` — caminhos por SO.

## Decisões que não são óbvias

- **Áudio no Windows não usa ffmpeg.** O ffmpeg só enxerga DirectShow, e a saída
  do sistema depende de "Stereo Mix", que muita placa não tem (a máquina de
  teste não tinha, nem desativado). WASAPI loopback resolve sem driver virtual.
- **`WAVEFORMATEX` precisa de `_pack_ = 1`.** O SDK declara essas structs sob
  `pshpack1.h`; sem isso o `SubFormat` sai deslocado e a detecção de float32
  falha silenciosamente.
- **Config em `~/captura-dia/config`, não em `%APPDATA%`.** O Python da Microsoft
  Store virtualiza `%APPDATA%`: o app enxergaria uma pasta privada dentro de
  `LocalCache\Roaming`, e config editada por fora sumiria sem erro.
- **Job Object.** Amarra os processos filhos à interface; sem isso um
  encerramento abrupto deixaria o gravador órfão segurando o microfone.
- **Iniciar/parar já valem como habilitar/desabilitar — só no Windows.** Lá não
  há integração com o boot, então o supervisor precisa lembrar o que estava
  ligado. No Linux isso continua sendo decisão do `systemctl enable`, feita na
  instalação: o `main.py` não mudou de comportamento.
- **Comparação de telas por ffmpeg** em vez de ImageMagick, com o mesmo critério
  (320x180, 8% por pixel). O laço bash do Linux continua usando `magick`.
- **O vídeo usa uma cópia portátil do OBS, não a instalação do usuário.** Quem
  transmite tem cenas de live montadas; gravar a cena atual gravaria câmera e
  overlay, e trocar de cena no meio de uma transmissão seria pior. Em modo
  portátil as duas instâncias não dividem coleção, perfil nem `global.ini`.
- **O Game Capture é apontado por executável (`priority=2`), não por "qualquer
  tela cheia".** Senão a decisão de gravar (janela em foco) e o que é gravado
  (o que estiver em tela cheia) podem divergir.
- **O identificador de janela do OBS precisa de escape.** É
  `título:classe:executável`; um título com `:` quebra a divisão e o OBS nem
  tenta o hook — o arquivo sai válido e preto.
- **Sem `CREATE_NO_WINDOW` nos filhos do supervisor.** Sem console, o
  `CTRL_BREAK` não chega e toda parada virava morte súbita depois de 10 s de
  espera — com WAV sem cabeçalho finalizado.
- **Marcadores ficam em memória** até a gravação fechar: o nome do arquivo só é
  conhecido no `StopRecord`, e logo após o `StartRecord` a saída ainda nem
  consta como ativa.
- **Sessões de vídeo são portáteis.** Cada segmento seletivo ganha um sidecar
  `.session`; todos os segmentos da mesma jogada usam a mesma chave. A API
  reconstrói `video_sessions` a partir dele, portanto Linux e Windows podem ter
  bancos SQLite locais sem perder o agrupamento visual. Vídeos seletivos antigos
  com apenas `.window` são tratados como sessões individuais.
- **A HUD precisa de `WS_EX_NOACTIVATE`.** Sem ele a janela rouba o foco ao
  aparecer, o `winvideo` conclui que o jogo saiu de foco e **para a gravação**
  que a HUD deveria estar vigiando. Junto vão `WS_EX_TRANSPARENT` (clique
  atravessa) e `WS_EX_TOOLWINDOW` (fora do Alt+Tab).
- **Não existe overlay sobre fullscreen exclusivo sem injetar DLL.** É o que
  Discord e RTSS fazem, e está descartado: há anti-cheat na lista de apps. A
  janela `TOPMOST` aparece na maioria dos jogos (Fullscreen Optimizations os põe
  em flip-model) e some no exclusivo de verdade — daí a posição configurável e o
  aviso sonoro, que chega mesmo quando a HUD não aparece.
- **Chave nova em `video.conf` mora em quatro lugares.** `ALLOWED_CONFIG`
  (senão `parse_shell_config` a descarta em silêncio na leitura), o modelo
  `VideoSettings`, `get_video_settings()` e o template de `set_video_settings()`,
  que reescreve o arquivo inteiro. Faltar em qualquer um deles some com a chave
  no primeiro save, sem erro. `VideoSettingsRoundTripTests` cobre isso.
- **O sinal `lume-video-active` é batimento, não só estado.** É reescrito a cada
  volta do laço (2 s) e a HUD trata um sinal velho como ausente — senão um laço
  morto seguraria para sempre a aparência de gravação em curso.
- **O sinal de atividade tem um significado só.** Enquanto `lume-video-active`
  existe, o supervisor mantém áudio e telas suspensos e a API relata gravação em
  curso. Por isso `_publish_activity()` só escreve dentro de uma sessão: publicar
  por um `F8` apertado à toa pausaria a captura do dia sem nada estar gravando.
  `VideoActivityFlagTests` fixa isso.
- **Evento é instante, saúde é estado.** As confirmações (marcador anotado,
  clipe salvo, atalho ignorado) ficam **fora** de `hudstate.evaluate()`. Se um
  clipe que falhou uma vez virasse alerta, a HUD ficaria vermelha para sempre.
- **A sequência do evento é o que o identifica**, não o rótulo. Dois marcadores
  seguidos têm o mesmo texto e o mesmo nome de arquivo; um contador que só
  cresce distingue *evento novo* de *mesmo evento relido a cada volta*.
- **Salvar clipe tem duas fases.** O OBS só informa o arquivo depois de gravá-lo
  (até 15 s), então o laço avisa `clip_saving` na hora e `clip_saved`/`clip_failed`
  no desfecho — sem isso o silêncio no meio pareceria atalho não registrado.
- **Redesenhar o Canvas custa ~4 ms**, porque o tkinter recria os itens a cada
  volta. A 60 quadros por segundo isso daria uns 20% de um núcleo, durante o
  jogo. Daí três cadências (`ANIMATION_TICK_MS`/`TICK_MS`/`IDLE_TICK_MS`) e o
  descarte de redesenho no modo compacto, que parado só muda quando o relógio
  vira: escondida a HUD custa 0%, compacta quase nada, expandida ~6%.
- **A confirmação não expande o painel.** Abrir a HUD inteira por cima do jogo
  para avisar de um marcador seria pior que o problema. No compacto o evento
  entra como letreiro — a linha normal sobe, a do evento toma o lugar e depois
  volta; o recorte é o próprio canvas. No expandido ele vira uma faixa cuja
  altura cresce junto com a animação, sem o salto de antes.
- **A HUD não é pausável.** Fica fora de `_PAUSABLE` e de `captura-dia.target`
  de propósito: ela existe para vigiar a gravação, então precisa continuar de pé
  exatamente quando as outras capturas são suspensas.

## O que falta

1. **Modelos no Windows** — Ollama sem os modelos baixados
   (`qwen3-vl-ctx:latest`, `qwen3.5:9b`) e whisper.cpp ausente. O pipeline roda e
   indexa; as etapas de IA falham com mensagem clara e podem ser reprocessadas.
2. **Início automático com o Windows** — hoje é um atalho manual em
   `shell:startup`.
3. **A gravação de jogos exige o OBS instalado** e só foi exercitada contra um
   app D3D em tela cheia (`ffplay`), não contra um jogo de verdade com
   anti-cheat. O hook pode ser bloqueado por alguns deles.
4. **A HUD no Linux não foi validada.** O coletor (`LinuxHudCollector`) lê o
   estado de `captura-dia-video-paused` mais o `*.partial.mp4` em curso, e os
   níveis dos buses do PipeWire com `parec`; a janela usa `-type dock`, sem
   equivalente barato para clique atravessante em tkinter. O comportamento na
   ausência de cada peça é degradar calado, nunca acusar falha inexistente.

## Como validar

Linux (nada pode quebrar):

```bash
.venv/bin/python -m app.backend.test_main
.venv/bin/python -m app.backend.test_services
.venv/bin/python -m app.capture.selftest --no-audio
```

`--no-audio` importa: `audio_setup()` chama `audio-bus.sh setup`, que
reconfigura o RecordBus ao vivo e atrapalha a captura em execução.

A HUD tem dois modos que dispensam abrir um jogo:

```bash
.venv/bin/python -m app.capture.hud --probe   # estado lido, em JSON, sem janela
.venv/bin/python -m app.capture.hud --demo    # janela com dados fabricados
```

O `--probe` é seguro com a captura rodando: só emite requisições de leitura.

Windows:

```powershell
.\.venv-win\Scripts\python.exe -m app.backend.test_main
.\.venv-win\Scripts\python.exe -m app.backend.test_services
.\.venv-win\Scripts\python.exe -m app.capture.selftest --seconds 10
```

## Convenções

- `AGENTS.md`: há um grafo em `graphify-out/`; use `graphify query "..."` antes
  de grep e rode `graphify update .` após alterar código.
- Idioma do projeto e dos comentários: português.
- Não use `Get-Content`/`Set-Content` do PowerShell 5.1 para editar arquivos
  fonte: ele lê UTF-8 como ANSI e devolve os acentos corrompidos.
