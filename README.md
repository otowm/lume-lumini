# captura-dia

Captura local e contínua de áudio + telas para processamento noturno por
whisper.cpp/Vulkan, Qwen-VL/Ollama e o gerador de resumo.

Este documento descreve a instalação no Linux. O mesmo código roda no Windows —
ver [WINDOWS.md](WINDOWS.md).

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
