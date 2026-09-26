# captura-dia

Captura local e contínua de áudio + telas para processamento noturno por
whisper.cpp/Vulkan, Qwen-VL/Ollama e o gerador de resumo.

Este documento descreve a instalação no Linux. O mesmo código roda no Windows —
ver [WINDOWS.md](WINDOWS.md).

## Dois modos da mesma base

O Lume completo grava, transcreve, descreve e resume o dia. O **Lumini** é este
mesmo projeto instalado só como gravador de gameplay: sem Ollama, sem whisper,
sem modelos de áudio, sem os serviços de print e de áudio do dia — e a interface
não mostra nada de análise.

Não é um fork: é uma linha em `~/.config/captura-dia/lume.conf`, escrita pelo
instalador.

| | Instala com | `LUME_MODE` |
|---|---|---|
| Lume | `install-captura-dia.sh` + `install-lume.sh` | `completo` (padrão) |
| Lumini | `instalar-lumini.sh` | `lumini` |

O Lumini precisa de `fastapi` e `uvicorn`, e nada mais de Python
(`requirements-lumini.txt`) — verificado por teste, que bloqueia `numpy` e
`sherpa-onnx` e importa a API inteira. As rotas de análise continuam existindo,
mas respondem **409** nessa instalação: esconder o botão não impediria um POST
manual de chamar um Ollama ausente.

Para experimentar o Lumini sem tocar na sua instalação:

```bash
LUME_MODE=lumini .venv/bin/python -m uvicorn app.backend.main:app --port 8877
```

Uma diferença deliberada: o Lumini abre a interface na **rede local** por padrão
(as faixas privadas da RFC 1918, não o endereço detectado na hora — trocar de
Wi-Fi não pode fazer a interface parar de abrir), para quem não é técnico
conseguir ver os clipes pelo celular sem editar nada. `--somente-local` fecha.
O Lume completo continua em `127.0.0.1`, com o que você já configurou por
`lume-local.*` ou pelo drop-in da unit.

O guia de quem só vai gravar está em [LUMINI.md](LUMINI.md).

## Estrutura instalada

```text
~/captura-dia/
├── audio/   # Windows: 3 canais temporários, convertidos para mono após análise
└── telas/   # um PNG por monitor, timestamp no nome

~/bin/
├── audio-bus.sh
├── grava-audio.sh
├── captura-tela.sh
└── captura-tela-loop.sh

~/.config/captura-dia/
├── tela.conf
└── janelas-sensiveis.txt
```

As units são `captura-dia-audio.service`, `captura-dia-tela.service` e o
agregador `captura-dia.target`. Ver tudo de uma vez:

```bash
systemctl --user status captura-dia.target captura-dia-audio.service captura-dia-tela.service
journalctl --user -u captura-dia-audio.service -u captura-dia-tela.service -f
```

## Áudio

O áudio é gravado em **três faixas separadas** num único WAV de 3 canais, igual
ao Windows: `c0` = microfone, `c1` = voz do Discord, `c2` = demais sons do
sistema. O pipeline transcreve cada canal isoladamente (a fonte de cada trecho
fica registrada) e, após o processamento bem-sucedido, compacta o arquivo para
mono.

Cada faixa vem de um bus efêmero recriado pelo serviço (`~/bin/audio-bus.sh`):

- **MicBus** ← o microfone disponível (aliases wireless/gaming do headset);
- **RecordBus** ← os monitores de saída (`headset`, `GameOut`, `spotify-sink`);
- **DiscordBus** ← a voz do Discord, **derivada** (tap) das saídas do nó
  `WEBRTC VoiceEngine` com `pw-link`, em paralelo ao que já toca no fone — sem
  reencaminhar, então não há latência extra na chamada. O modo `watch` do
  script mantém esse tap vivo enquanto o Discord entra e sai das chamadas.

Como o merge por prioridade deduplica falas repetidas, o Discord aparecer também
no mix do sistema (`c2`) não é problema. O setup aguarda `pipewire-pulse` sem
limite e o serviço usa 15 s de backoff caso o gravador termine. Para inspecionar:

```bash
~/bin/audio-bus.sh status
```

Teste isolado de 10 segundos (fale e reproduza algum som durante o teste):

```bash
mkdir -p /tmp/captura-dia-teste
ffmpeg -y -hide_banner -loglevel error \
  -f pulse -i RecordBus.monitor -t 10 -ac 1 -ar 16000 -c:a pcm_s16le \
  /tmp/captura-dia-teste/audio.wav

ffprobe -v error -show_entries stream=codec_name,sample_rate,channels,duration \
  -of default=noprint_wrappers=1 /tmp/captura-dia-teste/audio.wav

ffmpeg -hide_banner -i /tmp/captura-dia-teste/audio.wav \
  -af volumedetect -f null - 2>&1 | grep -E 'mean_volume|max_volume'
```

`max_volume: -inf dB` indica silêncio digital. Um número finito confirma sinal;
o teste feito na instalação mediu média de -34,2 dB e pico de -9,5 dB.

## Tela

No KDE/KWin, o backend automático usa `spectacle`; `grim` permanece disponível
para compositores compatíveis. Uma única captura do desktop virtual é recortada
pela geometria dinâmica de `kscreen-doctor`, produzindo arquivos como:

```text
2026-07-21_01-02-03_mon0_HDMI-A-1.png
2026-07-21_01-02-03_mon1_DP-1.png
```

Teste de um frame:

```bash
~/bin/captura-tela.sh
identify ~/captura-dia/telas/*.png | tail -2
```

Teste a decisão sem capturar:

```bash
~/bin/captura-tela.sh --print-window
~/bin/captura-tela.sh --dry-run
```

Edite as regexes sensíveis em
`~/.config/captura-dia/janelas-sensiveis.txt`. Para testar no próprio terminal,
adicione temporariamente `Konsole`; `--dry-run` deve imprimir
`SKIP sensitive-window` e retornar status 11. No fish, veja com `echo $status`.

A proteção é *fail closed*: se `kdotool` não conseguir consultar a janela ativa,
nenhuma imagem é criada.

### Intervalo ou mudança

Edite `~/.config/captura-dia/tela.conf` e reinicie a unit.

```bash
# Salvar sempre a cada 20 s
CAPTURE_MODE=interval
INTERVAL_SECONDS=20

# Ou amostrar a cada 5 s e salvar só mudanças relevantes
CAPTURE_MODE=change
CHANGE_POLL_SECONDS=5
CHANGE_THRESHOLD_PERCENT=3
CHANGE_MAX_INTERVAL_SECONDS=300
```

`MAX_GEOMETRY="1920x1080>"` limita cada monitor sem ampliar imagens menores.

```bash
systemctl --user restart captura-dia-tela.service
```

## Instalação e recuperação

O instalador salva versões anteriores sob
`~/.local/state/captura-dia/backups/AAAAmmdd-HHMMSS/` antes de substituir os
arquivos. Reinstale depois de editar o repositório com:

```bash
./install-captura-dia.sh
```

As units antigas `captura-audio.service` e `otowm-recall-capture.service` ficam
desativadas para impedir processos duplicados; não são apagadas.

## Interface Lume

A primeira versão operacional da interface está em `frontend/`, com API local
em `app/backend/`. Ela mostra o estado real das duas capturas e permite:

- pausar e retomar áudio + tela;
- alternar captura por intervalo/mudança e ajustar resolução;
- editar e validar a lista de janelas sensíveis;
- gravar uma amostra temporária e medir o volume;
- capturar e visualizar os dois monitores.

A API escuta somente em loopback, valida o `Host` e rejeita mutações originadas
por outros sites. Para reconstruir e instalar:

```bash
cd frontend && npm run build && cd ..
./install-lume.sh
```

Abra `http://127.0.0.1:8876`. Logs e estado:

```bash
systemctl --user status lume.service
journalctl --user -u lume.service -f
```

## Som dos apps na faixa de sistema (c2)

Cada app é derivado para o `RecordBus` **stream por stream**, em paralelo ao
que ele já toca no fone — e por **id de porta**, não por nome. Nome não é
identidade: um jogo costuma abrir vários nós com o mesmo nome (o Sea of
Thieves abre quatro, um por conjunto de sons), e o `pw-link`, ao encontrar um
par que já existe, desiste ali sem tentar os seguintes. Com um stream antigo já
ligado, nenhum dos novos entrava — o som do jogo sumia da HUD e da gravação
enquanto o navegador continuava saindo normalmente.

O `watch` refaz as derivações a cada `WATCH_INTERVAL` (3 s), então um app que
abre som depois da gravação começar entra sozinho. Para conferir o que está
ligado agora:

```bash
pw-link -I -l | grep -A5 RecordBus:playback
~/bin/audio-bus.sh tap      # refaz as derivações na hora
```

## Quando a gravação de jogo para

O `gpu-screen-recorder` grava um **monitor**, não uma janela, e é isso que
decide quando a sessão acaba. A cada dois segundos o laço classifica a janela
em foco em três respostas, não duas:

- **é o jogo** — a contagem de saída, se houver alguma, é cancelada;
- **não cobre o jogo** — o painel do Plasma, um OSD de volume, uma notificação,
  uma leitura que o KWin devolveu em branco, ou outro app **no outro monitor**.
  O jogo continua inteiro na tela que está sendo gravada, então nada muda: a
  contagem não começa, e uma que já estivesse correndo fica onde está;
- **cobre o jogo** — outra janela, no monitor gravado. Só isto inicia a
  contagem, e passados `VIDEO_FOCUS_GRACE_SECONDS` a sessão encerra.

Fechar o jogo encerra a sessão mesmo com a área de trabalho em foco: antes de
segurar, o laço confere se a janela que abriu a sessão ainda existe (ou outra
da mesma classe, para o jogo que troca de janela ao virar tela cheia).

As janelas tratadas como "ambiente" estão em `VIDEO_FOCUS_IGNORE_CLASSES` —
uma expressão regular com um padrão sensato embutido no script. Ela não vive no
`video.conf`, que a interface reescreve inteiro a cada gravada de ajustes; para
mudá-la, use um `Environment=` no `captura-dia-video.service`.

Enquanto a sessão estiver de pé, áudio e telas seguem pausados
(`PAUSE_OTHER_CAPTURES`) — inclusive durante a folga em que você está no outro
monitor.

## Atalho de gravação (F8)

No modo **Clipes**, o atalho tem duas intenções:

- **tocar** salva os últimos `VIDEO_REPLAY_SECONDS` que o `gpu-screen-recorder`
  mantém em RAM. Tocar de novo antes de a janela fechar — menos de
  `VIDEO_REPLAY_SECONDS` depois — **estende o mesmo clipe** em vez de abrir
  outro: os dois pedidos descrevem um trecho só, e salvá-los separados deixaria
  a mesma jogada em dois arquivos. Por isso o clipe aparece na biblioteca
  quando a janela fecha, não no instante do atalho;
- **segurar** por `VIDEO_HOTKEY_HOLD_SECONDS` (0,6s) abre uma **gravação
  longa** — o clipe de pré-roll é guardado e a gravação segue dali em diante,
  até você segurar de novo. Os dois pedaços saem emendados num arquivo só, e
  durante ela o toque volta a ser marcador.

A HUD mostra um ponto vermelho piscando com o tempo da gravação longa, e cada
ação tem um som próprio (aceite, abrir, fechar).

Quem percebe a segurada é o `captura-dia-hotkey.service`, que lê o teclado em
`/dev/input`. Isso exige o grupo `input`, uma vez só:

```bash
sudo usermod -aG input "$USER"   # e reabrir a sessão
```

Sem ele o serviço sai avisando no journal e o toque simples continua
funcionando pelo atalho do KDE — só a segurada não é percebida.

## Mandar um clipe pra alguém

O gravador nomeia por data, e a pasta acaba com centenas de arquivos que só se
distinguem pelo segundo. O botão **Enviar** — no card do vídeo, no player e em
cada trecho de uma sessão — resolve isso sem mexer no arquivo original:

- **Baixar** entrega o mesmo arquivo com um nome que você reconhece no seletor
  do Discord: `2026-09-26 00-10 Sea of Thieves — trecho 02 de 05.mp4`. O jogo sai
  do sidecar `.window`, então funciona no clipe recém-gravado, antes de a IA
  analisar qualquer coisa. Nada é copiado: quem renomeia é o cabeçalho HTTP.
- **Versão leve** recodifica para caber num teto (10, 20, 50 ou 500 MB). Um
  minuto de 1080p60 pesa ~57 MB e não entra como anexo; em 20 MB ele sai 720p60,
  porque numa jogada a fluidez lê melhor que a nitidez. Vai **uma faixa de
  áudio** só, a mixagem — as faixas isoladas do seu microfone e do Discord dos
  seus amigos não saem daqui. Se o original já cabe, o Lume diz isso em vez de
  recodificar à toa. A versão leve fica em `.lume-cache/video-share`, fora da
  biblioteca, e é apagada junto com os outros caches do vídeo.
- **Link público**, para o que não cabe nem comprimido: sobe para o
  `litterbox.catbox.moe` (temporário, 1h a 72h, até 1 GB) ou para o
  `catbox.moe` (permanente, até 200 MB). É a única parte do Lume que manda
  arquivo para fora, e por isso exige uma confirmação explícita a cada envio —
  a recusa vive no servidor, não só na tela. Os links ficam guardados para
  recopiar; tirar um da lista **não o despublica**, só o host faz isso.

## Pausa por inatividade

Depois de alguns minutos sem teclado ou mouse, o áudio e as telas são pausados
sozinhos e voltam assim que você retoma a atividade — o vídeo seletivo é exceção
e continua monitorando jogos. No KDE/Wayland o caminho X11 de idle não funciona,
então o Lume usa o **`swayidle`** (protocolo `ext-idle-notify` do KWin); a
política de pausar/retomar vive na própria API, coordenada com a pausa do vídeo.

```bash
sudo pacman -S swayidle
```

Sem ele a interface mostra a pausa como indisponível, e nada mais é afetado. O
limite é ajustável por `LUME_IDLE_PAUSE_SECONDS` (padrão 300; `0` desativa),
igual ao Windows.

## O que "pendente" quer dizer

São duas coisas, e elas não se encontravam sozinhas:

- **mídia pendente** — arquivos ainda não analisados. É o que o botão
  **Processar pendentes** enfileira, e o que o timer noturno drena;
- **dia sem consolidação** — um dia cuja mídia já foi analisada, mas que nunca
  ganhou resumo nem timeline. Não havia clique que o alcançasse: a mídia dele
  está `done`, então não é pendente, e o worker só consolidava os dias que
  tocava na própria rodada.

Um dia conta como **pendente de consolidação** quando não tem resumo nenhum
**ou** quando o resumo é anterior à memória mais nova dele — o que acontece
sempre que mais capturas do mesmo dia são analisadas depois da consolidação. O
segundo caso é o que trava a limpeza segura: ela compara a contagem de memórias
registrada na consolidação com a atual e, vendo que a narrativa não cobre tudo,
recusa apagar a mídia bruta. Como o dia *tem* resumo, nada o reconsolidava, e o
espaço ficava preso para sempre.

Agora o worker fecha os dois casos junto com o primeiro: ao fim de cada
execução ele consolida os dias desta rodada (em ordem cronológica) e, na
sequência, todo dia pendente de consolidação, do mais recente para o mais
antigo. A narrativa é montada a partir do texto já no índice, então um dia
continua consolidável mesmo depois de a retenção apagar a mídia bruta.

Para um dia específico, sem esperar a fila:

```bash
.venv/bin/python -m app.backend.pipeline --summary-only 2026-08-14
```

## Índice e processamento noturno

O índice fica em `~/captura-dia/lume.sqlite3` (SQLite WAL + FTS5). A ingestão é
incremental: cada caminho aparece uma vez e passa por `pending`, `processing`,
`done`, `skipped` ou `error`. O WAV mais recente é considerado aberto e nunca é
enviado ao Whisper até o segmento seguinte existir.

Screenshots passam por comparação visual 320×180 antes do Qwen-VL; quadros
semelhantes ao último descrito no mesmo monitor são marcados `skipped`. Isso
impede que intervalos curtos virem milhares de inferências redundantes.

Modelos padrão:

- áudio: `ggml-large-v3-turbo-q5_0.bin` pelo whisper.cpp/Vulkan;
- telas: `qwen3-vl-ctx:latest` no Ollama;
- resumo: `qwen3.5:9b` no Ollama.

O timer persistente roda às 03:30:

```bash
systemctl --user list-timers lume-process.timer
journalctl --user -u lume-process.service -f
```

Execução controlada manual:

```bash
.venv/bin/python -m app.backend.pipeline --limit-audio 1 --limit-screen 2 --no-summary
```

## Vocabulário de tags

O Qwen propõe tags livres em toda análise. Sem conciliação elas viram centenas
de strings quase iguais — `sea of thieves`, `Sea Of Thieves` e `sot` são três
assuntos diferentes para quem filtra. Cada string bruta passa por quatro
filtros, do mais barato ao mais caro:

1. **slug** — minúsculo, sem acento, hifenizado. Resolve a maioria de graça.
2. **apelido** — equivalências já decididas (`sot` → `sea-of-thieves`).
3. **Laya** — o daemon responde se a proposta significa o mesmo que alguma tag
   ativa. É o mesmo modelo que aplica o vocabulário e que guarda o crescimento
   dele.
4. **recorrência** — uma tag proposta uma única vez é ruído do modelo, não
   assunto novo. Só vira vocabulário depois de reaparecer em dias distintos.

O que não casa com nada fica em quarentena como candidata e **continua sendo
gravado na captura**: o vocabulário governa o índice, não a memória. Sem o
daemon no ar, valem só os dois primeiros filtros — nenhuma tag se perde, apenas
a fusão semântica espera.

A promoção roda sozinha ao fim do resumo diário: funde sinônimos, promove o que
recorreu e pede ao Qwen o nome final e o critério de cada tag nova. Tags sem uso
há 45 dias adormecem, e há teto de 72 ativas — um vocabulário sem teto deixa de
ser vocabulário.

Tudo isso tem tela própria em **Central de captura › Tags**: a bancada passa
strings pelo vocabulário sem gravar nada, a promoção de um dia roda em ensaio ou
valendo, e o vocabulário aceita criar, ativar, adormecer, rejeitar e fundir à
mão. Pela linha de comando:

```bash
.venv/bin/python -m app.backend.pipeline --preview-tags 2026-09-24   # ensaio
.venv/bin/python -m app.backend.pipeline --promote-tags 2026-09-24   # valendo
```

O daemon é o `laya-daemon.service` do usuário, que escuta em
`$XDG_RUNTIME_DIR/laya-daemon.sock` (ajustável por `LAYA_SOCKET`). O Lume nunca
carrega o modelo no próprio processo: o pipeline já divide GPU e memória com o
whisper e o Ollama.

```bash
systemctl --user status laya-daemon.service
```

Limiares por variável de ambiente: `LUME_TAG_CONFIDENCE` (0.6),
`LUME_TAG_MIN_PROPOSALS` (3), `LUME_TAG_MIN_DAYS` (2), `LUME_TAG_MAX_ACTIVE`
(72) e `LUME_TAG_DORMANT_DAYS` (45).

A pergunta enviada ao Laya cabe num orçamento de 192 tokens repartido entre
todas as opções, e o que elas não gastam é o que sobra para o enunciado. Por
isso o critério de cada tag é curto (palavras concretas, não frases) e o
vocabulário é recortado por proximidade lexical antes da pergunta: medindo neste
vocabulário, a confiança se sustenta até cerca de 33 opções e cai perto de 65.
