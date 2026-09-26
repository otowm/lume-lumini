#!/usr/bin/env bash
set -euo pipefail

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"

[[ -x "$root/.venv/bin/uvicorn" ]] || { echo "ERRO: rode .venv/bin/pip install -r requirements.txt" >&2; exit 1; }
[[ -f "$root/frontend/dist/index.html" ]] || { echo "ERRO: rode npm run build em frontend/" >&2; exit 1; }

install -d "$unit_dir" "${XDG_CONFIG_HOME:-$HOME/.config}/captura-dia"
# Declara o modo: sem isto, uma máquina que já teve o Lumini instalado
# continuaria escondendo a análise que este instalador acabou de pôr no ar.
printf 'LUME_MODE=completo\n' > "${XDG_CONFIG_HOME:-$HOME/.config}/captura-dia/lume.conf"
install -m 0644 "$root/systemd/lume-process.timer" "$unit_dir/lume-process.timer"
# O caminho do checkout entra aqui, e não fica escrito na unit: antes elas
# traziam `~/Documentos/lume` cravado, e um clone em qualquer outro lugar não
# subia — sem erro visível, só um serviço que não começa.
for unit in lume lume-process lume-summary@ lume-hourly@ captura-dia-hud; do
  sed -e "s|@LUME_ROOT@|$root|g" -e "s|@LUME_PYTHON@|$root/.venv/bin/python|g" \
    "$root/systemd/$unit.service" > "$unit_dir/$unit.service"
  chmod 0644 "$unit_dir/$unit.service"
done
systemctl --user daemon-reload
systemctl --user enable --now lume.service
systemctl --user enable --now lume-process.timer
echo "Lume disponível em http://127.0.0.1:8876"
