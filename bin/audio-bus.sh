#!/usr/bin/env bash
# Mantém os três buses de captura que separam as fontes de áudio em faixas:
#   MicBus     -> microfone            (canal c0 do WAV)
#   DiscordBus -> voz do Discord       (canal c1 do WAV)
#   RecordBus  -> demais sons do sistema, app por app (canal c2 do WAV)
#
# O gravador (grava-audio.sh) lê os três monitores e os junta num WAV de 3
# canais; o pipeline transcreve cada canal separadamente e, no fim, compacta
# para mono. Espelha o que o Windows faz com o loopback por processo.
#
# Tanto o Discord quanto os demais apps são "derivados" (tap) com pw-link, em
# paralelo ao que já tocam no fone: o áudio continua sem latência extra e cada
# fonte aparece isolada no seu bus. Nenhum monitor de saída física entra no
# RecordBus — o fone reproduz também o Discord, e monitorá-lo poria a mesma voz
# em c1 e c2, inutilizando a separação para edição.
#
# Uso: audio-bus.sh {setup|ensure|teardown|status|wait|watch|tap}
set -euo pipefail

MIC_WIRELESS="alsa_input.usb-XiiSound_Technology_Corporation_H510-PRO_Wireless_headset-00.mono-fallback"
MIC_GAMING="alsa_input.usb-XiiSound_Technology_Corporation_H510-PRO_USB_Gaming_Headset-00.mono-fallback"

MICS=("$MIC_WIRELESS" "$MIC_GAMING")

# Nós do PipeWire cujas saídas são derivadas para o DiscordBus. O Discord usa
# o WebRTC, que no PipeWire aparece como "WEBRTC VoiceEngine".
DISCORD_NODE_PATTERN="${DISCORD_NODE_PATTERN:-WEBRTC VoiceEngine}"
#: O WEBRTC carrega só a *voz*. Os sons de interface do Discord (entrar, sair,
#: notificação) saem por um nó transitório com outro nome, que precisa ficar
#: igualmente fora da faixa de sistema.
DISCORD_APP_PATTERN="${DISCORD_APP_PATTERN:-[Dd]iscord}"

#: Apps que não devem entrar na faixa de sistema, além do Discord. Regex ERE
#: casada contra o nome do nó. Útil quando um app carrega áudio que pertence a
#: outra faixa — um navegador com o Discord web aberto, por exemplo, entrega a
#: mesma voz que já está em c1 e não há como separar aba a aba dentro dele.
#: Definível em ~/.config/captura-dia/video.conf como C2_EXCLUDE.
_c2_config="${XDG_CONFIG_HOME:-$HOME/.config}/captura-dia/video.conf"
if [[ -z "${C2_EXCLUDE:-}" && -r "$_c2_config" ]]; then
  C2_EXCLUDE="$(awk -F= '$1 == "C2_EXCLUDE" {v=$2; gsub(/^["'"'"']|["'"'"']$/, "", v); print v}' "$_c2_config")"
fi
C2_EXCLUDE="${C2_EXCLUDE:-}"
#: De quanto em quanto tempo o modo watch refaz os taps (Discord e apps).
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
      awk -v b="$bus" '$0 ~ ("(^|[[:space:]])(source|sink|sink_name)=" b "([.]monitor)?([[:space:]]|$)") {print $1}' || true
  )
  for id in "${ids[@]}"; do
    pactl unload-module "$id" >/dev/null 2>&1 || true
  done
}

unload_all() {
  unload_bus RecordBus
  unload_bus DiscordBus
  unload_bus MicBus
  unload_bus LumeGameOut
  # Nome virtual usado pelas versões anteriores; remove apenas loopbacks que o
  # referenciam, sem tentar destruir o filtro externo que o criou.
  unload_bus GameOut
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
    sink_properties="device.description=$name node.virtual=true" >/dev/null
}

# Qual microfone alimenta o c0. A escolha do sistema vem primeiro: trocar de
# headset no Plasma passa a valer aqui, e a ordem fixa da lista punha a voz num
# dongle mudo — o wireless sem bateria continua *existindo* como fonte enquanto
# o receptor estiver plugado, então ele vencia mesmo com o USB em uso. A lista
# fica de reserva para quando o padrão não for um microfone.
selected_mic() {
  local default source
  default="$(pactl get-default-source 2>/dev/null || true)"
  if [[ -n "$default" && "$default" != *.monitor ]] && source_exists "$default"; then
    echo "$default"
    return 0
  fi
  for source in "${MICS[@]}"; do
    if source_exists "$source"; then
      echo "$source"
      return 0
    fi
  done
  return 1
}

#: Sinks criados pelo próprio Lume. Um stream que já toca num deles nunca é
#: derivado de volta para o RecordBus (seria realimentação, ou som duplicado).
LUME_SINKS=(MicBus DiscordBus RecordBus LumeGameOut)

# Sinks do Lume, por id, para casar com o campo ``Sink:`` dos sink-inputs.
lume_sink_ids() {
  local name
  for name in "${LUME_SINKS[@]}"; do
    pactl list short sinks | awk -v s="$name" '$2 == s {print $1}'
  done
}

# Nomes dos nós de reprodução que devem compor a faixa de sistema (c2).
#
# Deriva-se stream por stream, e não o monitor da saída física, porque o fone
# também toca o Discord: monitorá-lo poria a mesma voz em c1 e c2. Ficam de
# fora, além do Discord:
#   - streams que já tocam num bus do Lume (realimentação);
#   - nós ``output.*``, criados por module-loopback e combine-stream para
#     reencaminhar áudio que já é capturado na origem. Um jogo mandado para o
#     GameOut, por exemplo, aparece como stream dele *e* como saída do combine
#     no fone; derivar os dois poria o mesmo som duas vezes na faixa.
system_stream_nodes() {
  local ids
  ids="$(lume_sink_ids | paste -sd' ' -)"
  pactl list sink-inputs 2>/dev/null | awk -v ids=" $ids " \
      -v discord="$DISCORD_NODE_PATTERN" -v app="$DISCORD_APP_PATTERN" \
      -v skip="$C2_EXCLUDE" '
    /^Sink Input #/ { sink=""; node=""; next }
    /^[[:space:]]*Sink:/ { sink=$2; next }
    /node\.name = / {
      node=$0
      sub(/^.*node\.name = "/, "", node)
      sub(/"$/, "", node)
      if (index(ids, " " sink " ") > 0) next
      if (index(node, discord) == 1) next
      if (node ~ app) next
      if (skip != "" && node ~ skip) next
      if (index(node, "output.") == 1) next
      print node
    }
  ' | sort -u
}

# --- ligação por id -------------------------------------------------------
#
# O `pw-link` liga portas por nome, e nome não é identidade: um app pode ter
# vários nós chamados igual — o Sea of Thieves abre quatro — e o padrão casa
# com todos. Pior, ao encontrar um par que já existe o pw-link desiste ali
# ("Arquivo existe") sem tentar os seguintes. Junte as duas coisas e basta um
# stream antigo já ligado para nenhum dos novos entrar na faixa: era assim que
# o som do jogo sumia da HUD e da gravação enquanto o navegador continuava
# saindo normalmente. Ligar porta a porta, por id, resolve os dois.

# "<id>\t<nó>:<porta>" de cada porta de saída cujo nó começa com o prefixo.
output_port_ids() {
  pw-link -I -o 2>/dev/null | awk -v n="$1" '{
    id = $1
    name = $0
    sub(/^[[:space:]]*[0-9]+[[:space:]]+/, "", name)
    if (index(name, n) == 1 && name ~ /:output_/) printf "%s\t%s\n", id, name
  }'
}

# Id da porta de entrada de um bus. Os buses são únicos, mas o id evita
# depender disso e deixa o pw-link com um par exato para ligar.
bus_port_id() {
  pw-link -I -i 2>/dev/null | awk -v n="$1" '{
    id = $1
    name = $0
    sub(/^[[:space:]]*[0-9]+[[:space:]]+/, "", name)
    if (name == n) { print id; exit }
  }'
}

link_ports() {
  [[ -n "$1" && -n "$2" ]] || return 0
  pw-link "$1" "$2" 2>/dev/null || true
}

# Deriva o microfone para o MicBus. Usa pw-link, e não module-loopback, para
# que as três faixas percorram caminhos de latência equivalente: com o loopback
# de 200 ms só o mic chegava atrasado, e o WAV de 3 canais saía desalinhado.
# Refazer isto no watch também cobre a troca de fone no meio da sessão.
tap_mic() {
  sink_exists MicBus || return 0
  local mic port linked
  mic="$(selected_mic)" || return 0
  # Trocar de headset no meio da sessão deixaria o anterior ligado, porque o
  # watch só acrescenta links: o c0 ganharia duas fontes, uma delas muda. Solta
  # o que não for do mic escolhido antes de ligar o que for.
  while IFS= read -r linked; do
    [[ "$linked" == "$mic:"* ]] && continue
    pw-link -d "$linked" "MicBus:playback_MONO" 2>/dev/null || true
  done < <(pw-link -l 2>/dev/null | awk '
    $0 == "MicBus:playback_MONO" { inside = 1; next }
    /^[^[:space:]]/ { inside = 0 }
    inside && /\|<-/ { print $2 }')
  while IFS= read -r port; do
    pw-link "$port" "MicBus:playback_MONO" 2>/dev/null || true
  done < <(pw-link -o 2>/dev/null | awk -v n="$mic:" 'index($0, n) == 1 && $0 ~ /:capture_/')
}

# Deriva as saídas dos apps para o RecordBus, em paralelo ao que já tocam no
# fone. Como o tap do Discord, pw-link falha sem efeito se o link já existe.
tap_system() {
  sink_exists RecordBus || return 0
  local left right node id port chan
  left="$(bus_port_id "RecordBus:playback_FL")"
  right="$(bus_port_id "RecordBus:playback_FR")"
  [[ -n "$left" && -n "$right" ]] || return 0
  while IFS= read -r node; do
    [[ -n "$node" ]] || continue
    while IFS=$'\t' read -r id port; do
      chan="${port##*_}"
      case "$chan" in
        FL|FC|SL) link_ports "$id" "$left" ;;
        FR|SR)    link_ports "$id" "$right" ;;
        MONO)     link_ports "$id" "$left"; link_ports "$id" "$right" ;;
      esac
    done < <(output_port_ids "$node")
  done < <(system_stream_nodes)
}

# Deriva as saídas do Discord para o DiscordBus, em paralelo (sem reencaminhar).
# pw-link falha de forma inofensiva quando o link já existe.
tap_discord() {
  sink_exists DiscordBus || return 0
  local target id port chan
  target="$(bus_port_id "DiscordBus:playback_MONO")"
  [[ -n "$target" ]] || return 0
  while IFS=$'\t' read -r id port; do
    chan="${port##*_}"
    case "$chan" in
      FL|FR|MONO) link_ports "$id" "$target" ;;
    esac
  done < <(output_port_ids "$DISCORD_NODE_PATTERN")
}

setup() {
  wait_pipewire
  unload_all

  make_null_sink MicBus 1
  make_null_sink DiscordBus 1
  make_null_sink RecordBus 2

  local mic
  if mic="$(selected_mic)"; then
    tap_mic
    echo "Microfone selecionado: $mic"
  else
    echo "AVISO: nenhum alias de microfone disponível; MicBus ficará em silêncio." >&2
  fi

  # c2 é composta stream a stream por tap_system (ver ali o porquê), e não
  # pelo monitor da saída física: assim a voz do Discord fica só em c1.
  tap_system

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
    # Apps entram e saem o tempo todo — um jogo que abre depois da gravação
    # começar só entra na faixa c2 aqui. Por isso os dois taps são refeitos
    # juntos a cada volta, e não uma única vez no setup.
    tap_mic
    tap_discord
    tap_system
  done
}

# Garante os buses sem derrubar o que já está de pé. O `setup` começa por um
# `unload_all`, então refazê-lo à toa cortaria uma gravação de áudio em curso:
# só reconstrói quando algum bus falta. É o caso de uma sessão de jogo iniciada
# com a captura de áudio pausada — ninguém rodou o `setup` do ExecStartPre, e o
# gravador de vídeo recusaria as fontes e morreria.
ensure() {
  wait_pipewire
  local bus
  for bus in MicBus DiscordBus RecordBus; do
    sink_exists "$bus" || { setup; return; }
  done
  tap_mic
  tap_discord
  tap_system
}

status() {
  wait_pipewire
  local bus
  for bus in MicBus DiscordBus RecordBus; do
    echo "== $bus =="
    pactl list short sinks | awk -v s="$bus" '$2 == s' || true
    if ! sink_exists "$bus"; then echo "  $bus AUSENTE"; fi
  done
  echo "== Streams na faixa de sistema (c2) =="
  system_stream_nodes | sed 's/^/  /' || true
  if [[ -z "$(system_stream_nodes)" ]]; then echo "  (nenhum app tocando)"; fi
  echo "== Tap do Discord =="
  pw-link -l 2>/dev/null | grep -A1 "DiscordBus" || echo "  (nenhum link para DiscordBus)"
}

# Liga o Discord na faixa 2 e **diz** se conseguiu.
#
# É o passo em que quem instala trava: o `tap_discord` casa o nó por nome
# (`WEBRTC VoiceEngine`, do cliente oficial), e um Vesktop ou um Discord no
# navegador aparecem com outro nome — aí nada é ligado, em silêncio, e a faixa do
# Discord sai muda sem explicação. Quando não acha, aqui a gente lista o que
# existe tocando, que é o que permite corrigir o padrão em vez de adivinhar.
discord() {
  wait_pipewire
  sink_exists DiscordBus || { echo "DiscordBus não existe; rode 'audio-bus.sh ensure' antes." >&2; return 1; }
  tap_discord
  if pw-link -l 2>/dev/null | grep -q "DiscordBus"; then
    echo "áudio do Discord ligado na faixa 2"
    return 0
  fi
  echo "não achei o Discord tocando (procurei por \"$DISCORD_NODE_PATTERN\")." >&2
  echo "Abra o Discord, entre numa chamada e rode de novo:  ~/bin/audio-bus.sh discord" >&2
  local vistos
  vistos="$(pw-link -o 2>/dev/null | sed 's/:output_.*//' | sort -u | sed 's/^/  /')"
  if [[ -n "$vistos" ]]; then
    echo "Saídas de áudio que eu vejo agora:" >&2
    printf '%s\n' "$vistos" >&2
    echo "Se o Discord estiver nessa lista com outro nome, ponha-o no video.conf:" >&2
    echo "  DISCORD_NODE_PATTERN='<o nome que aparece acima>'" >&2
  fi
  return 1
}

case "${1:-setup}" in
  setup) setup ;;
  ensure) ensure ;;
  teardown) unload_all; echo "Buses removidos." ;;
  status) status ;;
  wait) wait_pipewire ;;
  watch) watch ;;
  tap) wait_pipewire; tap_discord; tap_system ;;
  discord) discord ;;
  *) echo "uso: audio-bus.sh {setup|ensure|teardown|status|wait|watch|tap|discord}" >&2; exit 2 ;;
esac
