#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/captura-dia"
unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
applications_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
backup_dir="${XDG_STATE_HOME:-$HOME/.local/state}/captura-dia/backups/$(date +%Y%m%d-%H%M%S)"

install -d "$HOME/bin" "$HOME/captura-dia/audio" "$HOME/captura-dia/telas" \
  "$config_dir" "$unit_dir" "$applications_dir" "$backup_dir"

for old in \
  "$HOME/bin/audio-bus.sh" \
  "$HOME/bin/grava-audio.sh" \
  "$unit_dir/captura-audio.service" \
  "$unit_dir/otowm-recall-capture.service"; do
  [[ -e "$old" ]] && cp -a "$old" "$backup_dir/"
done

install -m 0755 "$root/bin/audio-bus.sh" "$HOME/bin/audio-bus.sh"
install -m 0755 "$root/bin/grava-audio.sh" "$HOME/bin/grava-audio.sh"
install -m 0755 "$root/bin/capture-frame" "$HOME/bin/captura-tela.sh"
install -m 0755 "$root/bin/capture-loop" "$HOME/bin/captura-tela-loop.sh"
install -m 0755 "$root/bin/game-video-loop" "$HOME/bin/captura-video-loop.sh"
install -m 0755 "$root/bin/add-video-marker" "$HOME/bin/lume-add-video-marker"
install -m 0755 "$root/bin/toggle-video-hud" "$HOME/bin/lume-toggle-video-hud"
install -m 0755 "$root/bin/lume-audio-diag" "$HOME/bin/lume-audio-diag"
sed "s|%h|$HOME|g" "$root/systemd/lume-marker.desktop" > "$applications_dir/lume-marker.desktop"
VIDEO_HUD_HOTKEY=Ctrl+Shift+F8
[[ -r "$config_dir/video.conf" ]] && source "$config_dir/video.conf"
sed -e "s|%h|$HOME|g" -e "s|@HOTKEY@|$VIDEO_HUD_HOTKEY|g" \
  "$root/systemd/lume-hud-toggle.desktop" > "$applications_dir/lume-hud-toggle.desktop"
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 --noincremental >/dev/null 2>&1 || true

if [[ ! -e "$config_dir/tela.conf" ]]; then
  install -m 0644 "$root/config/captura-dia/tela.conf" "$config_dir/tela.conf"
fi
if [[ ! -e "$config_dir/janelas-sensiveis.txt" ]]; then
  old_patterns="${XDG_CONFIG_HOME:-$HOME/.config}/otowm-recall/sensitive-windows.txt"
  if [[ -e "$old_patterns" ]]; then
    cp "$old_patterns" "$config_dir/janelas-sensiveis.txt"
  else
    install -m 0644 "$root/config/captura-dia/janelas-sensiveis.txt" "$config_dir/janelas-sensiveis.txt"
  fi
fi
if [[ ! -e "$config_dir/video.conf" ]]; then
  install -m 0644 "$root/config/captura-dia/video.conf" "$config_dir/video.conf"
elif grep -qxE 'VIDEO_AUDIO=(default_output|device:MicBus\.monitor,device:DiscordBus\.monitor,device:RecordBus\.monitor)' "$config_dir/video.conf"; then
  # Migra as configurações históricas: `default_output` produzia uma única faixa
  # no vídeo, e a lista sem a mixagem à frente deixava os players tocando apenas
  # a primeira faixa isolada — o microfone.
  sed -E "s%^VIDEO_AUDIO=(default_output|device:MicBus\.monitor,device:DiscordBus\.monitor,device:RecordBus\.monitor)$%VIDEO_AUDIO='device:MicBus.monitor|device:DiscordBus.monitor|device:RecordBus.monitor,device:MicBus.monitor,device:DiscordBus.monitor,device:RecordBus.monitor'%" \
    "$config_dir/video.conf" > "$config_dir/video.conf.new"
  install -m 0644 "$config_dir/video.conf.new" "$config_dir/video.conf"
  rm -f "$config_dir/video.conf.new"
fi
[[ -e "$config_dir/video-apps.txt" ]] || install -m 0644 "$root/config/captura-dia/video-apps.txt" "$config_dir/video-apps.txt"
if [[ ! -e "$config_dir/storage.conf" ]]; then
  printf "STORAGE_ROOT='%s/captura-dia'\n" "$HOME" > "$config_dir/storage.conf"
  chmod 0644 "$config_dir/storage.conf"
fi

install -m 0644 "$root/systemd/captura-dia-audio.service" "$unit_dir/"
install -m 0644 "$root/systemd/captura-dia-tela.service" "$unit_dir/"
install -m 0644 "$root/systemd/captura-dia.target" "$unit_dir/"
for unit in captura-dia-video captura-dia-hud captura-dia-hotkey; do
  sed -e "s|@LUME_ROOT@|$root|g" -e "s|@LUME_PYTHON@|$root/.venv/bin/python|g" \
    "$root/systemd/$unit.service" > "$unit_dir/$unit.service"
  chmod 0644 "$unit_dir/$unit.service"
done

systemctl --user disable --now captura-audio.service otowm-recall-capture.service 2>/dev/null || true
systemctl --user daemon-reload
# Instalar/atualizar nunca muda a escolha operacional atual do usuário. Em
# especial, capturas pausadas continuam pausadas e uma partida não é cortada.
# A pausa mora no estado de habilitação da unit, então reabilitar tudo às cegas
# retomaria a captura de quem a pausou de propósito: só entra quem ainda não
# tem uma escolha registrada.
systemctl --user enable captura-dia.target captura-dia-video.service \
  captura-dia-hud.service captura-dia-hotkey.service
for unit in captura-dia-audio.service captura-dia-tela.service; do
  state="$(systemctl --user is-enabled "$unit" 2>/dev/null || true)"
  [[ "$state" == disabled ]] || systemctl --user enable "$unit"
done

# Instalar não troca o que já está rodando: o bash lê o script na partida, e um
# serviço que subiu antes desta instalação segue com o código anterior. Quem
# acabou de corrigir um defeito fica olhando para ele intacto e conclui que a
# correção não funcionou. Reiniciar por conta própria também não serve — isso
# descartaria o buffer de clipes de uma partida em curso —, então o caminho é
# dizer, com o comando pronto.
stale_units=()
check_stale() {
  local unit="$1" started newest file
  shift
  systemctl --user is-active --quiet "$unit" || return 0
  started="$(systemctl --user show "$unit" -p ActiveEnterTimestamp --value)"
  [[ -n "$started" ]] || return 0
  started="$(date -d "$started" +%s 2>/dev/null)" || return 0
  newest=0
  for file in "$@"; do
    [[ -e "$file" ]] || continue
    (( $(stat -c %Y "$file") > newest )) && newest="$(stat -c %Y "$file")"
  done
  (( newest > started )) && stale_units+=("$unit")
  return 0
}
check_stale captura-dia-video.service "$HOME/bin/captura-video-loop.sh" "$HOME/bin/audio-bus.sh"
check_stale captura-dia-audio.service "$HOME/bin/grava-audio.sh" "$HOME/bin/audio-bus.sh"
check_stale captura-dia-tela.service "$HOME/bin/captura-tela-loop.sh" "$HOME/bin/captura-tela.sh"
check_stale captura-dia-hud.service "$root/app/capture/hud.py" "$root/app/capture/hudsource.py" \
  "$root/app/capture/hudstate.py"
check_stale captura-dia-hotkey.service "$root/app/capture/hotkeyd.py"
if ((${#stale_units[@]})); then
  echo
  echo "Estes serviços ainda rodam a versão anterior (o script foi lido quando subiram):"
  printf '    %s\n' "${stale_units[@]}"
  echo "Para aplicar o que acabou de ser instalado:"
  echo "    systemctl --user restart ${stale_units[*]}"
  case " ${stale_units[*]} " in
    *" captura-dia-video.service "*)
      echo "Atenção: reiniciar a captura de vídeo descarta o buffer de clipes em curso." ;;
  esac
fi

if ! id -nG | tr ' ' '\n' | grep -qx input; then
  echo "Aviso: $USER não está no grupo 'input'. Segurar o atalho para abrir uma"
  echo "gravação longa exige ler o teclado direto:"
  echo "    sudo usermod -aG input \"$USER\"   # e reabrir a sessão"
  echo "Até lá, o toque simples continua funcionando pelo atalho do KDE."
fi
echo "Captura consolidada instalada. Backup: $backup_dir"
