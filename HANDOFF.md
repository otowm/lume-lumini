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

## O que falta

1. **Modelos no Windows** — Ollama sem os modelos baixados
   (`qwen3-vl-ctx:latest`, `qwen3.5:9b`) e whisper.cpp ausente. O pipeline roda e
   indexa; as etapas de IA falham com mensagem clara e podem ser reprocessadas.
2. **Início automático com o Windows** — hoje é um atalho manual em
   `shell:startup`.
3. **A gravação de jogos exige o OBS instalado** e só foi exercitada contra um
   app D3D em tela cheia (`ffplay`), não contra um jogo de verdade com
   anti-cheat. O hook pode ser bloqueado por alguns deles.

## Como validar

Linux (nada pode quebrar):

```bash
.venv/bin/python -m app.backend.test_main
.venv/bin/python -m app.backend.test_services
.venv/bin/python -m app.capture.selftest --no-audio
```

`--no-audio` importa: `audio_setup()` chama `audio-bus.sh setup`, que
reconfigura o RecordBus ao vivo e atrapalha a captura em execução.

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
