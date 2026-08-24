#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

[[ -x "$root/.venv/bin/uvicorn" ]] || { echo "ERRO: rode .venv/bin/pip install -r requirements.txt" >&2; exit 1; }
[[ -f "$root/frontend/dist/index.html" ]] || { echo "ERRO: rode npm run build em frontend/" >&2; exit 1; }

install -d "$unit_dir"
install -m 0644 "$root/systemd/lume.service" "$unit_dir/lume.service"
install -m 0644 "$root/systemd/lume-process.service" "$unit_dir/lume-process.service"
install -m 0644 "$root/systemd/lume-summary@.service" "$unit_dir/lume-summary@.service"
install -m 0644 "$root/systemd/lume-hourly@.service" "$unit_dir/lume-hourly@.service"
install -m 0644 "$root/systemd/lume-process.timer" "$unit_dir/lume-process.timer"
install -m 0644 "$root/systemd/captura-dia-hud.service" "$unit_dir/captura-dia-hud.service"
systemctl --user daemon-reload
systemctl --user enable --now lume.service
systemctl --user enable --now lume-process.timer
echo "Lume disponível em http://127.0.0.1:8876"
