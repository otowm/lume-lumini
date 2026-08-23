#!/usr/bin/env bash
# Mantém os três buses de captura que separam as fontes de áudio em faixas:
#   MicBus     -> microfone            (canal c0 do WAV)
#   DiscordBus -> voz do Discord       (canal c1 do WAV)
#   RecordBus  -> demais sons do sistema, monitores de saída (canal c2 do WAV)
#
# O gravador (grava-audio.sh) lê os três monitores e os junta num WAV de 3
# canais; o pipeline transcreve cada canal separadamente e, no fim, compacta
# para mono. Espelha o que o Windows faz com o loopback por processo.
#
# O Discord é "derivado" (tap) com pw-link em paralelo ao que já toca no fone:
# assim a voz continua sem latência extra e ainda aparece isolada em DiscordBus.
#
# Uso: audio-bus.sh {setup|teardown|status|wait|watch|tap}
set -euo pipefail

MIC_WIRELESS="alsa_input.usb-XiiSound_Technology_Corporation_H510-PRO_Wireless_headset-00.mono-fallback"
MIC_GAMING="alsa_input.usb-XiiSound_Technology_Corporation_H510-PRO_USB_Gaming_Headset-00.mono-fallback"
HEADSET="alsa_output.usb-XiiSound_Technology_Corporation_H510-PRO_Wireless_headset-00.analog-stereo"

MICS=("$MIC_WIRELESS" "$MIC_GAMING")
SINK_MONITORS=("${HEADSET}.monitor" "GameOut.monitor" "spotify-sink.monitor")
LAT_MSEC="${LAT_MSEC:-200}"

# Nós do PipeWire cujas saídas são derivadas para o DiscordBus. O Discord usa
# o WebRTC, que no PipeWire aparece como "WEBRTC VoiceEngine".
DISCORD_NODE_PATTERN="${DISCORD_NODE_PATTERN:-WEBRTC VoiceEngine}"
#: De quanto em quanto tempo o modo watch reestabelece o tap do Discord.
WATCH_INTERVAL="${WATCH_INTERVAL:-3}"

wait_pipewire() {
  local attempt=0
  until pactl info >/dev/null 2>&1; do
    ((attempt += 1))
    if (( attempt == 1 || attempt % 15 == 0 )); then
      echo "Aguardando pipewire-pulse ficar disponível (tentativa $attempt)..." >&2
    fi
    sleep 1
  done
}

# Descarrega todos os módulos (null-sink e loopback) que referenciam um bus.
unload_bus() {
  local bus="$1" ids=() id
  mapfile -t ids < <(
    pactl list short modules 2>/dev/null |
      awk -v b="$bus" '$0 ~ ("(^|[[:space:]])(sink|sink_name)=" b "([[:space:]]|$)") {print $1}' || true
  )
  for id in "${ids[@]}"; do
    pactl unload-module "$id" >/dev/null 2>&1 || true
  done
}

unload_all() {
  unload_bus RecordBus
  unload_bus DiscordBus
  unload_bus MicBus
}

sink_exists() {
  pactl list short sinks | awk -v s="$1" '$2 == s { found=1 } END { exit !found }'
}

source_exists() {
  pactl list short sources | awk -v s="$1" '$2 == s { found=1 } END { exit !found }'
}

make_null_sink() {
  local name="$1" channels="$2"
  pactl load-module module-null-sink \
    sink_name="$name" rate=48000 channels="$channels" \
    sink_properties="device.description=$name" >/dev/null
}

load_loopback() {
  local source="$1" sink="$2"
  if ! pactl load-module module-loopback \
      source="$source" sink="$sink" latency_msec="$LAT_MSEC" \
      source_dont_move=true sink_dont_move=true >/dev/null 2>&1; then
    echo "AVISO: loopback aguardando/indisponível para: $source -> $sink" >&2
  fi
}

selected_mic() {
  local source
  for source in "${MICS[@]}"; do
    if source_exists "$source"; then
      echo "$source"
      return 0
    fi
  done
  return 1
}

# Deriva as saídas do Discord para o DiscordBus, em paralelo (sem reencaminhar).
# pw-link falha de forma inofensiva quando o link já existe.
tap_discord() {
  sink_exists DiscordBus || return 0
  local port chan
  while IFS= read -r port; do
    chan="${port##*_}"
    case "$chan" in
      FL|FR|MONO) pw-link "$port" "DiscordBus:playback_MONO" 2>/dev/null || true ;;
    esac
  done < <(pw-link -o 2>/dev/null | awk -v p="$DISCORD_NODE_PATTERN" 'index($0, p) == 1 && $0 ~ /:output_/')
}

setup() {
  wait_pipewire
  unload_all

  make_null_sink MicBus 1
  make_null_sink DiscordBus 1
  make_null_sink RecordBus 2

  local mic
  if mic="$(selected_mic)"; then
    load_loopback "$mic" MicBus
    echo "Microfone selecionado: $mic"
  else
    echo "AVISO: nenhum alias de microfone disponível; MicBus ficará em silêncio." >&2
  fi

  local monitor
  for monitor in "${SINK_MONITORS[@]}"; do load_loopback "$monitor" RecordBus; done

  tap_discord

  local bus
  for bus in MicBus DiscordBus RecordBus; do
    if ! sink_exists "$bus"; then
      echo "ERRO: null-sink $bus não apareceu." >&2
      exit 1
    fi
  done
  echo "Buses prontos: MicBus (c0) + DiscordBus (c1) + RecordBus (c2)."
}

# Mantém o tap do Discord vivo enquanto a gravação roda (o Discord entra/sai da
# chamada a todo momento; os loopbacks de mic/saída são persistentes e não
# precisam disso).
watch() {
  while sleep "$WATCH_INTERVAL"; do
    tap_discord
  done
}

status() {
  wait_pipewire
  local bus
  for bus in MicBus DiscordBus RecordBus; do
    echo "== $bus =="
    pactl list short sinks | awk -v s="$bus" '$2 == s' || true
    if ! sink_exists "$bus"; then echo "  $bus AUSENTE"; fi
  done
  echo "== Tap do Discord =="
  pw-link -l 2>/dev/null | grep -A1 "DiscordBus" || echo "  (nenhum link para DiscordBus)"
}

case "${1:-setup}" in
  setup) setup ;;
  teardown) unload_all; echo "Buses removidos." ;;
  status) status ;;
  wait) wait_pipewire ;;
  watch) watch ;;
  tap) wait_pipewire; tap_discord ;;
  *) echo "uso: audio-bus.sh {setup|teardown|status|wait|watch|tap}" >&2; exit 2 ;;
esac
