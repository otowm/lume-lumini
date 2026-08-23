#!/usr/bin/env bash
# Grava três faixas isoladas (mic + Discord + demais sons do sistema) num único
# WAV de 3 canais PCM 16 kHz, pronto para o pipeline separar por fonte.
#   c0 = MicBus.monitor      (microfone)
#   c1 = DiscordBus.monitor  (voz do Discord, derivada via pw-link)
#   c2 = RecordBus.monitor   (mixagem das saídas do sistema)
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
exec ffmpeg -hide_banner -loglevel warning -nostdin \
  -f pulse -thread_queue_size 1024 -i "$MIC_SRC" \
  -f pulse -thread_queue_size 1024 -i "$DISCORD_SRC" \
  -f pulse -thread_queue_size 1024 -i "$SYSTEM_SRC" \
  -filter_complex "[0:a]pan=mono|c0=c0[mic];[1:a]pan=mono|c0=c0[dis];[2:a]pan=mono|c0=0.5*c0+0.5*c1[sys];[mic][dis][sys]join=inputs=3:channel_layout=3.0[out]" \
  -map "[out]" -ar 16000 -c:a pcm_s16le \
  -flush_packets 1 \
  -f segment -segment_time "$SEG_SECONDS" -reset_timestamps 1 -strftime 1 \
  "$OUTDIR/audio-%Y%m%d-%H%M%S.wav"
