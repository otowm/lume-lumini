#!/usr/bin/env bash
# Grava três faixas isoladas (mic + Discord + demais sons do sistema) num único
# WAV de 3 canais PCM 16 kHz, pronto para o pipeline separar por fonte.
#   c0 = MicBus.monitor      (microfone)
#   c1 = DiscordBus.monitor  (voz do Discord, derivada via pw-link)
#   c2 = RecordBus.monitor   (mixagem das saídas do sistema)
#
# O ``map=`` do join é obrigatório: as três entradas são mono e, portanto, todas
# chamam seu único canal de FC. Sem o mapeamento explícito o ffmpeg resolve o
# conflito de nomes por conta própria e entrega os canais rotacionados — o mic
# saía em c2, o Discord em c0 e o sistema em c1, e o pipeline transcrevia cada
# faixa com o rótulo da outra.
# Depois do processamento bem-sucedido o pipeline compacta para mono.
set -euo pipefail

storage_config="${XDG_CONFIG_HOME:-$HOME/.config}/captura-dia/storage.conf"
STORAGE_ROOT="$HOME/captura-dia"
[[ -r "$storage_config" ]] && source "$storage_config"
OUTDIR="$STORAGE_ROOT/audio"
SEG_SECONDS="${SEG_SECONDS:-900}"

MIC_SRC="${MIC_SOURCE:-MicBus.monitor}"
DISCORD_SRC="${DISCORD_SOURCE:-DiscordBus.monitor}"
SYSTEM_SRC="${AUDIO_SOURCE:-RecordBus.monitor}"

# Tratamento do microfone (supressão de ruído + portão de volume mínimo, como
# a "sensibilidade de entrada" do Discord). Configurável em audio.conf; a
# interface do Lume escreve nele via /api/settings/audio.
audio_config="${XDG_CONFIG_HOME:-$HOME/.config}/captura-dia/audio.conf"
MIC_DENOISE_ENABLED=true
MIC_GATE_THRESHOLD_DB=-45
[[ -r "$audio_config" ]] && source "$audio_config"

# agate trabalha com amplitude linear (0-1), não dBFS: converte aqui para que
# o arquivo de configuração e a interface só falem em dB, que é o que se lê
# num medidor de volume.
mic_gate_linear="$(awk -v db="$MIC_GATE_THRESHOLD_DB" 'BEGIN{printf "%.6f", 10 ^ (db / 20)}')"
mic_filter="pan=mono|c0=c0"
[[ "$MIC_DENOISE_ENABLED" == "true" ]] && mic_filter+=",afftdn"
mic_filter+=",agate=threshold=${mic_gate_linear}:attack=5:release=250"

[[ "$SEG_SECONDS" =~ ^[1-9][0-9]*$ ]] || { echo "SEG_SECONDS inválido" >&2; exit 2; }
mkdir -p "$OUTDIR"

BUS_SCRIPT="$(dirname "$(readlink -f "$0")")/audio-bus.sh"

wait_source() {
  local src="$1" attempt=0
  until pactl list short sources 2>/dev/null | awk -v s="$src" '$2 == s { found=1 } END { exit !found }'; do
    ((attempt += 1))
    if (( attempt == 1 || attempt % 15 == 0 )); then
      echo "Aguardando $src (tentativa $attempt)..." >&2
    fi
    sleep 1
  done
}

wait_source "$MIC_SRC"
wait_source "$DISCORD_SRC"
wait_source "$SYSTEM_SRC"

# Mantém o tap do Discord vivo durante toda a gravação; morre junto com ela.
watch_pid=""
if [[ -x "$BUS_SCRIPT" ]]; then
  "$BUS_SCRIPT" watch &
  watch_pid=$!
  trap '[[ -n "$watch_pid" ]] && kill "$watch_pid" 2>/dev/null || true' EXIT INT TERM
fi

echo ">> Gravando 3 faixas (mic/Discord/sistema) -> $OUTDIR (blocos de ${SEG_SECONDS}s, 16 kHz)"
set +e
ffmpeg -hide_banner -loglevel warning -nostdin \
  -f pulse -thread_queue_size 1024 -i "$MIC_SRC" \
  -f pulse -thread_queue_size 1024 -i "$DISCORD_SRC" \
  -f pulse -thread_queue_size 1024 -i "$SYSTEM_SRC" \
  -filter_complex "[0:a]${mic_filter}[mic];[1:a]pan=mono|c0=c0[dis];[2:a]pan=mono|c0=0.5*c0+0.5*c1[sys];[mic][dis][sys]join=inputs=3:channel_layout=3.0:map=0.0-FL|1.0-FR|2.0-FC[out]" \
  -map "[out]" -ar 16000 -c:a pcm_s16le \
  -flush_packets 1 \
  -f segment -segment_time "$SEG_SECONDS" -reset_timestamps 1 -strftime 1 \
  "$OUTDIR/audio-%Y%m%d-%H%M%S.wav"
status=$?
set -e
# O watch morre pelo trap de EXIT registrado acima; matá-lo aqui de novo só
# mascararia um trap que tivesse deixado de ser registrado.
exit "$status"
