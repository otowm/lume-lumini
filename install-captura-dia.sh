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
sed "s|%h|$HOME|g" "$root/systemd/lume-marker.desktop" > "$applications_dir/lume-marker.desktop"
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
[[ -e "$config_dir/video.conf" ]] || install -m 0644 "$root/config/captura-dia/video.conf" "$config_dir/video.conf"
[[ -e "$config_dir/video-apps.txt" ]] || install -m 0644 "$root/config/captura-dia/video-apps.txt" "$config_dir/video-apps.txt"
if [[ ! -e "$config_dir/storage.conf" ]]; then
  printf "STORAGE_ROOT='%s/captura-dia'\n" "$HOME" > "$config_dir/storage.conf"
  chmod 0644 "$config_dir/storage.conf"
fi

install -m 0644 "$root/systemd/captura-dia-audio.service" "$unit_dir/"
install -m 0644 "$root/systemd/captura-dia-tela.service" "$unit_dir/"
install -m 0644 "$root/systemd/captura-dia.target" "$unit_dir/"
install -m 0644 "$root/systemd/captura-dia-video.service" "$unit_dir/"

systemctl --user disable --now captura-audio.service otowm-recall-capture.service 2>/dev/null || true
systemctl --user daemon-reload
systemctl --user enable --now captura-dia.target

echo "Captura consolidada instalada. Backup: $backup_dir"
