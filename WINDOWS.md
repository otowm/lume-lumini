# Lume no Windows

O Lume roda no Windows com o **mesmo código** do Linux. A captura (áudio, telas,
janela ativa) e a orquestração (o que no Linux é o systemd) têm implementações
próprias para cada sistema, atrás de uma interface só — o resto do app não sabe
em qual sistema está.

O que **funciona** hoje: captura contínua de áudio e telas, gravação seletiva de
jogos, a interface inteira, o controle de pausar/retomar, as janelas sensíveis, o
índice SQLite e o agendamento do processamento noturno.

O que **falta**: os modelos (Ollama e whisper.cpp). Ver a seção 8.

---

## 1. Pré-requisitos

- **Python 3.10+** — <https://www.python.org/downloads/>, marcando
  **"Add python.exe to PATH"**.
- **ffmpeg** no `PATH` — `winget install Gyan.FFmpeg` (recomendado).

Confirme:

```powershell
python --version
ffmpeg -version
```

Nada mais precisa ser instalado para capturar. Em especial, **não** é preciso
"Stereo Mix", VB-Cable, VoiceMeeter nem ImageMagick.

---

## 2. Abrir o Lume

Duplo clique em **`Lume.bat`**. Ele aceita uma porta como argumento
(`Lume.bat 8877`) e não depende de política de execução do PowerShell.

Ajustes que valem só nesta máquina — caminho de um banco compartilhado, abrir a
interface para a VPN — vivem em `lume-local.cmd` (ou `lume-local.ps1`), que o
git ignora. Sem esse arquivo, o Lume sobe fechado em `127.0.0.1`.

Para instalar apenas o gravador, sem nada de IA, é `instalar-lumini.ps1` e o
atalho **`Lumini.bat`** — ver [LUMINI.md](LUMINI.md). Nessa instalação o
supervisor deixa de oferecer as units de processamento e de captura do dia.

Se preferir o PowerShell, `lume.ps1` faz o mesmo e aceita `-NoBrowser` e
`-Port`:

```powershell
.\lume.ps1 -NoBrowser
```

Na primeira execução ele cria o ambiente Python em `.venv-win` e instala as
dependências; depois disso a abertura é imediata. A interface sobe em
<http://127.0.0.1:8876> e o navegador abre sozinho.

> A pasta `.venv` (do Linux) e `.venv-win` (do Windows) convivem no mesmo
> diretório, então dá para usar a mesma cópia do projeto nos dois sistemas.

Depois de executar `install-windows-startup.ps1`, o backend inicia de forma
invisível em cada login do Windows e continua ativo sem aba do navegador ou
terminal aberto. `Lume.bat` detecta essa instância e apenas abre a interface,
sem iniciar um segundo servidor. Os processos de captura são amarrados ao
backend por um *Job Object*, evitando gravadores órfãos.

Para começar a capturar, use o botão de retomar na interface. A escolha fica
guardada: da próxima vez que abrir o Lume, a captura volta sozinha.

---

## 3. Áudio: como a saída do sistema é capturada

O Lume grava temporariamente **microfone + Discord + demais sons em três canais
de um único WAV**. Na análise, cada canal passa separadamente pelo Whisper e
pela diarização. Quando tudo foi salvo com sucesso, o arquivo é validado e
substituído atomicamente por uma versão mono; a origem de cada trecho continua
registrada na transcrição, embora as faixas isoladas deixem de estar disponíveis
para reprodução depois da compactação.

No Windows o caminho óbvio seria o ffmpeg com DirectShow, mas ele só enxerga
dispositivos de *entrada*: a saída do sistema depende de um "Stereo Mix", que
placas modernas — sobretudo headsets USB — muitas vezes nem oferecem (foi o caso
da máquina onde isto foi testado: nenhum dispositivo de loopback existia, nem
desativado).

Por isso o Lume usa **WASAPI loopback** diretamente, via `ctypes`
(`app/capture/wasapi.py`), sem driver virtual e sem dependência Python extra.
Ele grava sempre pelos dispositivos **padrão** de entrada e saída do Windows —
os mesmos que você escolhe em Configurações > Sistema > Som — a 16 kHz, usando
loopback por processo para isolar o Discord (`app/capture/winrecord.py`).

Consequências práticas:

- trocar de saída no Windows (headset → caixas) muda o que é gravado, sem
  configurar nada;
- se o headset desligar no meio, a fonte é reaberta sozinha alguns segundos
  depois e a gravação continua, preenchida com silêncio no intervalo;
- quando nada está tocando, o WASAPI não entrega pacote nenhum — o gravador
  completa com silêncio pelo relógio, então o WAV sempre tem a duração real.
- se o Discord fechar ou reiniciar, o gravador procura novamente o processo e
  reabre as faixas sem interromper o bloco atual.

Para ver os dispositivos que ele enxerga:

```powershell
.\.venv-win\Scripts\python.exe -m app.capture.winrecord --list
```

---

## 4. Self-test

Verifica áudio, telas, monitores e janela ativa sem depender da interface:

```powershell
.\.venv-win\Scripts\python.exe -m app.capture.selftest --seconds 10
```

Durante a gravação, **fale ao microfone e deixe algum som tocando**. No fim:

```
Volume: mean_volume: -21.6 dB / max_volume: -7.2 dB
```

Um número finito confirma sinal. `max_volume: -inf dB` é silêncio digital.
O bloco `== Áudio ==` também mostra `system_capture_ok`, que deve ser `true`.

Opções: `--no-audio`, `--no-screen`, `--seconds N`.

---

## 5. Onde ficam os arquivos

Arquivos de mídia, banco, caches e logs ficam na raiz de armazenamento escolhida
na interface. A configuração que aponta para essa raiz continua em
`%USERPROFILE%\captura-dia\config`, pois precisa ser encontrada antes da raiz
selecionada ser conhecida.

A configuração fica em `captura-dia\config`, e **não** em `%APPDATA%`, de
propósito: o Python instalado pela Microsoft Store roda com virtualização de
sistema de arquivos e enxerga um `%APPDATA%` privado, dentro de
`LocalCache\Roaming` do pacote. Config escrita por um editor de texto ficaria
invisível para o app — e vice-versa — sem erro nenhum. Manter tudo sob
`captura-dia` evita isso e deixa os dados num lugar só.

Para mudar o local, use a interface, ou a variável `CAPTURA_DIA_ROOT`.

---

## 6. Orquestração: o que substitui o systemd

`app/backend/services.py` expõe a mesma interface nos dois sistemas. No Linux
delega ao `systemctl --user`. No Windows há um supervisor dentro do processo da
interface que trata os nomes de unit como identificadores:

| unit | no Windows |
|---|---|
| `captura-dia-audio.service` | gravador WASAPI (`app.capture.winrecord`) |
| `captura-dia-tela.service` | laço de telas (`app.capture.winscreen`) |
| `captura-dia.target` | os dois acima |
| `lume-process.service` | `python -m app.backend.pipeline` |
| `lume-summary@DIA` / `lume-hourly@DIA` | pipeline com `--summary-only` / `--hourly-only` |
| `lume-process.timer` | agendador interno (checa o horário a cada minuto) |
| `captura-dia-video.service` | gravação de jogos (`app.capture.winvideo`, ver seção 7) |

O supervisor reproduz o que as units faziam: reinicia o que cai depois de 15 s
(`Restart=always`), para os processos com `CTRL_BREAK` para o WAV fechar com o
cabeçalho correto, e guarda em `config\services.json` o que deve subir na
próxima inicialização oculta.

Após 5 minutos sem entrada de teclado ou mouse, o supervisor pausa
automaticamente o áudio e as capturas de tela. Elas voltam assim que o usuário
retoma a atividade. O vídeo seletivo é uma exceção e continua monitorando e
gravando jogos durante a inatividade. O limite pode ser alterado pela variável
`LUME_IDLE_PAUSE_SECONDS`; use `0` para desativar essa política.

O laço de telas (`app/capture/winscreen.py`) é o porte de `bin/capture-loop`:
mesmos modos `interval` e `change`, mesmo limiar sobre uma miniatura 320x180 e a
mesma regra de privacidade *fail closed*. A comparação usa ffmpeg em vez de
ImageMagick (`app/capture/imagediff.py`), com o mesmo critério de 8% por pixel.

---

## 7. Vídeo seletivo: gravação de jogos

Grava automaticamente quando um app da sua lista entra em foco. Como é para
jogos, o desempenho manda no desenho.

**Requisito:** ter o **OBS Studio** instalado (<https://obsproject.com>). O Lume
não usa a sua instalação diretamente — na primeira vez ele faz uma **cópia
portátil** em `~/.lume-obs` (cerca de 475 MB) com configuração própria.

Isso não é capricho. Quem transmite tem cenas montadas para live: câmera,
overlay, chat. Mandar o Lume gravar a cena atual gravaria justamente isso em vez
do jogo — e trocar a cena no meio de uma transmissão seria pior ainda. Em modo
portátil a instância do Lume tem coleção, perfil e configuração próprios, então
as duas nunca se cruzam: a sua instalação não é lida nem escrita, e as duas
podem rodar ao mesmo tempo.

Por que OBS e não ffmpeg: o *Game Capture* engancha na cadeia de apresentação do
jogo e copia o quadro na própria GPU, que é o caminho de menor custo no Windows.
As alternativas foram medidas e descartadas — `gdigrab` captura pela CPU e nem
enxerga fullscreen exclusivo, e `ddagrab` só fechou com um retorno de cada quadro
para a CPU, meio gigabyte por segundo enquanto o jogo roda.

O que acontece a cada gravação:

1. o app em foco casa com a lista (aba **Vídeo seletivo** > **Apps excluídos**);
2. áudio e telas são suspensos, se `PAUSE_OTHER_CAPTURES` estiver ligado;
3. o OBS dedicado sobe (se ainda não estiver de pé) e o Game Capture é apontado
   para **aquele executável** — e não para "qualquer tela cheia", que poderia
   pegar outra janela;
4. grava até o segmento estourar ou o foco **sair para outro app** por mais
   que `VIDEO_FOCUS_GRACE_SECONDS`. Sair do jogo e o sistema mexer no foco são
   coisas diferentes: a barra de tarefas, o menu Iniciar, o alternador de
   tarefas e as notificações tomam o foco sozinhos, e o
   `GetForegroundWindow` devolve 0 no meio de um Alt+Tab. Nesses instantes o
   gravador segura a contagem em vez de começá-la — era isso que anunciava
   "Fora do jogo" com o jogo na frente;
5. o arquivo é conferido: se sair preto ou estático, você é avisado e um
   `.sem-imagem` fica ao lado, em vez de acumular gravação inútil em silêncio;
6. áudio e telas voltam.

Cada vídeo ganha um `.window` com o app que o originou, um `.session` que mantém
os segmentos da mesma sessão agrupados na interface e, se você usar o atalho,
um `.markers` com os instantes marcados. O atalho padrão é **F8**
(`VIDEO_MARKER_HOTKEY`), registrado globalmente — funciona com o jogo em foco.
No modo contínuo, o F8 adiciona um marcador; no modo **Clipes**, ele salva os
últimos 60 segundos do Replay Buffer do OBS. Tocar de novo antes de a janela
fechar — menos de `VIDEO_REPLAY_SECONDS` depois do último toque — **estende o
mesmo clipe** em vez de abrir outro: os dois pedidos cobrem um trecho só, e
salvá-los separados deixaria a mesma jogada em dois arquivos. Por isso o clipe
aparece na biblioteca quando a janela fecha, não no instante do atalho.

**Segurar** o F8 por `VIDEO_HOTKEY_HOLD_SECONDS` (0,6s por padrão) no modo
Clipes abre uma **gravação longa**, para quando dá para ver que a jogada vai
demorar e você quer tudo: o Lume salva o pré-roll que já está no buffer e deixa
o OBS gravando dali em diante. Segurar de novo encerra, e os dois pedaços saem
emendados num arquivo só — clipe + conteúdo gravado. Enquanto ela corre, um
toque simples volta a ser marcador, e a HUD mostra um ponto vermelho piscando
com o tempo da gravação.

Cada ação tem um som próprio: o aceite de sempre para marcador e clipe, um
arpejo subindo ao abrir a gravação longa e o mesmo arpejo descendo ao fechá-la.
Nos três casos o som confirma somente ações aceitas. Clipes feitos enquanto o mesmo jogo permanece
ativo recebem a mesma sessão e aparecem agrupados automaticamente.

Na Biblioteca de vídeos, **Unir vídeos/sessões** aceita tanto clipes avulsos
quanto sessões já existentes. Os clipes, análises e marcadores são preservados
em ordem cronológica; a síntese global deve ser gerada novamente para descrever
corretamente a sessão resultante.

Para preparar ou inspecionar a instância dedicada sem abrir o Lume:

```powershell
.\.venv-win\Scripts\python.exe -m app.capture.winvideo --diagnostics
.\.venv-win\Scripts\python.exe -m app.capture.winvideo --prepare
```

Se quiser desfazer tudo, basta apagar a pasta `~/.lume-obs`.

---

## 8. O que ainda não funciona

**Os modelos.** O pipeline roda e indexa normalmente, mas as etapas de IA
precisam de:

- **Ollama** com os modelos `qwen3-vl-ctx:latest` (telas) e `qwen3.5:9b`
  (resumo). O Ollama pode já estar instalado e rodando sem estar no `PATH` —
  confira em <http://127.0.0.1:11434/api/tags>. Baixar os modelos:
  `ollama pull qwen3-vl-ctx` e `ollama pull qwen3.5:9b` (vários GB).
- **whisper.cpp** com `ggml-large-v3-turbo-q5_0.bin`, esperado em
  `%USERPROFILE%\whisper.cpp\build\bin\whisper-cli`. Os caminhos podem ser
  redefinidos por `WHISPER_BIN` e `WHISPER_MODEL`.

Sem eles as capturas ficam com status `error` e mensagem explicando o que falta;
nada quebra, e elas podem ser reprocessadas depois pela interface.

**Iniciar junto com o Windows** não está configurado. Se quiser, crie um atalho
para `Lume.bat` em `shell:startup` (Win+R → `shell:startup`).
