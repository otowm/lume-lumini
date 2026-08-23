#!/usr/bin/env bash
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/otowm-recall"
lib_dir="$HOME/.local/lib/otowm-recall"
unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

install -d "$config_dir" "$lib_dir" "$unit_dir"
install -m 0755 "$root/bin/capture-frame" "$root/bin/capture-loop" "$lib_dir/"
install -m 0644 "$root/systemd/otowm-recall-capture.service" "$unit_dir/"
[[ -e "$config_dir/capture.conf" ]] || install -m 0644 "$root/config/capture.conf" "$config_dir/"
[[ -e "$config_dir/sensitive-windows.txt" ]] || install -m 0644 "$root/config/sensitive-windows.txt" "$config_dir/"
systemctl --user daemon-reload
echo "Instalado. Teste antes de ativar; veja README.md."

