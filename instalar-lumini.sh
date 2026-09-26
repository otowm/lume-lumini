#!/usr/bin/env bash
# Lumini: instala só o gravador de gameplay e a biblioteca de clipes.
#
# É o mesmo projeto do Lume, sem nada de análise: sem Ollama, sem whisper, sem
# modelos de áudio, sem os serviços de print e de áudio do dia. O que sobra é o
# que a pessoa abriu o app para fazer — gravar a jogada, achar o clipe, cortar e
# mandar no Discord.
#
# Feito para CachyOS/Arch com KDE Plasma em Wayland, que é onde o gravador foi
# testado: a janela em foco vem do `kdotool` e a geometria do monitor do
# `kscreen-doctor`, ambos do KDE, e nenhum dos dois tem substituto no código.
set -euo pipefail

# A interface responde na rede local por padrão: as faixas privadas da RFC 1918,
# e não a sub-rede detectada agora. É de propósito — trocar de Wi-Fi ou renovar o
# DHCP mudaria o endereço, e quem não é técnico ficaria com uma interface que
# parou de abrir sem nada ter mudado do lado dele.
#
# Abrir não é só trocar o endereço de escuta: o backend confere o IP de quem
# chega, então as duas coisas saem daqui juntas.
rede="10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
while (($#)); do
  case "$1" in
    --rede)
      if (($# < 2)) || [[ -z "$2" || "$2" == --* ]]; then
        echo "--rede exige uma faixa (ex.: 192.168.0.0/24)" >&2
        exit 2
      fi
      rede="$2"; shift 2 ;;
    --rede=*) rede="${1#*=}"; shift ;;
    --somente-local) rede=""; shift ;;
    -h|--help)
      echo "uso: instalar-lumini.sh [--rede FAIXA[,FAIXA...]] [--somente-local]"
      echo
      echo "  padrão:          a interface abre na sua rede local (faixas privadas)"
      echo "  --rede           limita a uma faixa sua (ex.: 192.168.0.0/24)"
      echo "  --somente-local  fecha em 127.0.0.1, só nesta máquina"
      exit 0 ;;
    *) echo "opção desconhecida: $1 (tente --help)" >&2; exit 2 ;;
  esac
done

root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
config_dir="${XDG_CONFIG_HOME:-$HOME/.config}/captura-dia"
unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
applications_dir="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
python_bin="$root/.venv/bin/python"

faltando=()
avisos=()

tem() { command -v "$1" >/dev/null 2>&1; }

exige() {
  local binario="$1" pacote="$2" motivo="$3"
  tem "$binario" && return 0
  faltando+=("$binario ($pacote) — $motivo")
}

echo "== Conferindo o que o gravador precisa =="
exige gpu-screen-recorder gpu-screen-recorder "é ele que grava a tela com a GPU"
exige kdotool kdotool "descobre qual jogo está em foco"
exige kscreen-doctor libkscreen "descobre em qual monitor o jogo está"
exige ffmpeg ffmpeg "emenda e corta os clipes"
exige ffprobe ffmpeg "lê a duração dos clipes"
exige pactl libpulse "fala com o PipeWire para criar as faixas de áudio"
exige python3 python "roda a interface e a HUD"

if ((${#faltando[@]})); then
  echo
  echo "Faltam programas para o Lumini funcionar:"
  printf '  - %s\n' "${faltando[@]}"
  echo
  echo "No CachyOS/Arch, normalmente:"
  echo "  sudo pacman -S --needed ffmpeg libpulse libkscreen python tk"
  echo "  paru -S gpu-screen-recorder kdotool     # ou o seu ajudante de AUR"
  exit 1
fi

# O banco do Lume usa FTS5. Sem ele, criar o esquema falha e nada funciona —
# melhor descobrir agora do que num erro no meio da primeira gravação. O Python
# de Arch traz FTS5; o da Microsoft Store, no Windows, às vezes não.
if ! python3 - <<'PY' >/dev/null 2>&1
import sqlite3
sqlite3.connect(":memory:").execute("CREATE VIRTUAL TABLE t USING fts5(x)")
PY
then
  echo "ERRO: este Python não tem SQLite com FTS5, e o banco do Lumini exige." >&2
  echo "      Instale o pacote 'python' do repositório oficial." >&2
  exit 1
fi

python3 -c "import tkinter" >/dev/null 2>&1 \
  || avisos+=("sem o pacote 'tk' a HUD não abre (sudo pacman -S tk); o resto funciona")
tem canberra-gtk-play \
  || avisos+=("sem 'libcanberra' não há som de confirmação ao salvar o clipe")
id -nG "$USER" | tr ' ' '\n' | grep -qx input \
  || avisos+=("você não está no grupo 'input': segurar o F8 não será percebido — 'sudo usermod -aG input $USER' e reabrir a sessão")

# --- ambiente Python ---------------------------------------------------------
# Só fastapi e uvicorn: nada de numpy nem sherpa-onnx, que existem apenas para a
# análise. `python -m pip` porque o atalho `pip` do venv guarda o caminho de
# criação e quebra se o diretório for movido.
if [[ ! -x "$python_bin" ]]; then
  echo "== Criando o ambiente Python em .venv =="
  python3 -m venv "$root/.venv"
fi
echo "== Instalando as dependências do gravador =="
"$python_bin" -m pip install --disable-pip-version-check -q --upgrade pip
"$python_bin" -m pip install --disable-pip-version-check -q -r "$root/requirements-lumini.txt"

if [[ ! -f "$root/frontend/dist/index.html" ]]; then
  echo "ERRO: falta frontend/dist — a interface não foi compilada neste clone." >&2
  echo "      Se você tem node instalado: cd frontend && npm install && npm run build" >&2
  exit 1
fi

# --- scripts, config e serviços ---------------------------------------------
install -d "$HOME/bin" "$config_dir" "$unit_dir" "$applications_dir"

install -m 0755 "$root/bin/audio-bus.sh" "$HOME/bin/audio-bus.sh"
install -m 0755 "$root/bin/game-video-loop" "$HOME/bin/captura-video-loop.sh"
install -m 0755 "$root/bin/add-video-marker" "$HOME/bin/lume-add-video-marker"
install -m 0755 "$root/bin/toggle-video-hud" "$HOME/bin/lume-toggle-video-hud"
install -m 0755 "$root/bin/lume-audio-diag" "$HOME/bin/lume-audio-diag"

# O modo é reescrito sempre: quem manda nele é a instalação, não um arquivo
# antigo que sobrou.
printf 'LUME_MODE=lumini\n' > "$config_dir/lume.conf"

# Preferências, só se ainda não existirem — reinstalar não pode apagar a lista
# de jogos de quem já usava.
[[ -e "$config_dir/video.conf" ]] || {
  sed 's/^VIDEO_ENABLED=false$/VIDEO_ENABLED=true/' \
    "$root/config/captura-dia/video.conf" > "$config_dir/video.conf"
}
[[ -e "$config_dir/video-apps.txt" ]] || \
  install -m 0644 "$root/config/captura-dia/video-apps.txt" "$config_dir/video-apps.txt"
[[ -e "$config_dir/storage.conf" ]] || \
  printf "STORAGE_ROOT='%s/lumini'\n" "$HOME" > "$config_dir/storage.conf"

VIDEO_HUD_HOTKEY=Ctrl+Shift+F8
[[ -r "$config_dir/video.conf" ]] && source "$config_dir/video.conf"
sed "s|%h|$HOME|g" "$root/systemd/lume-marker.desktop" > "$applications_dir/lume-marker.desktop"
sed -e "s|%h|$HOME|g" -e "s|@HOTKEY@|$VIDEO_HUD_HOTKEY|g" \
  "$root/systemd/lume-hud-toggle.desktop" > "$applications_dir/lume-hud-toggle.desktop"
tem kbuildsycoca6 && kbuildsycoca6 --noincremental >/dev/null 2>&1 || true

# Quatro units, e só estas: gravador, HUD, atalho e interface. O caminho do
# clone entra aqui, então o Lumini pode morar em qualquer pasta.
for unit in captura-dia-video captura-dia-hud captura-dia-hotkey lume; do
  sed -e "s|@LUME_ROOT@|$root|g" -e "s|@LUME_PYTHON@|$python_bin|g" \
    "$root/systemd/$unit.service" > "$unit_dir/$unit.service"
  chmod 0644 "$unit_dir/$unit.service"
done
# A interface do Lume espera pelo `captura-dia.target`, que é da captura do dia e
# não existe aqui. No Lumini ela espera pelo gravador.
sed -i -e 's|^After=captura-dia.target$|After=captura-dia-video.service|' \
       -e '/^Wants=captura-dia.target$/d' "$unit_dir/lume.service"

# Só instala versões preparadas pelo botão do app, antes de iniciar a captura.
sed -e "s|@LUME_ROOT@|$root|g" -e "s|@LUME_PYTHON@|$python_bin|g" \
  "$root/systemd/lumini-update.service" > "$unit_dir/lumini-update.service"
for unit in captura-dia-video captura-dia-hud captura-dia-hotkey lume; do
  install -d "$unit_dir/$unit.service.d"
  printf '[Unit]\nWants=lumini-update.service\nAfter=lumini-update.service\n' \
    > "$unit_dir/$unit.service.d/lumini-update.conf"
done

enderecos=""
if [[ -n "$rede" ]]; then
  # Substituir a linha que já existe, e não acrescentar no fim do arquivo: ali
  # cairia depois do `[Install]`, fora da seção `[Service]`, e o systemd
  # ignoraria. Não fixamos LUME_REMOTE_HOSTS: o backend aceita como `Host`
  # qualquer IP dentro destas faixas, então um endereço novo continua valendo.
  sed -i -e "s|^Environment=LUME_BIND_HOST=.*\$|Environment=LUME_BIND_HOST=0.0.0.0\nEnvironment=LUME_REMOTE_NETWORKS=$rede|" \
    "$unit_dir/lume.service"
  # Só as interfaces que são rede de casa: pontes de Docker, libvirt e afins têm
  # endereço privado também, e sugerir um deles mandaria a pessoa digitar um
  # endereço que não responde de fora.
  enderecos="$(ip -4 -o addr show scope global 2>/dev/null \
    | awk '$2 !~ /^(docker|br-|veth|virbr|vmnet|lo|tun|tap)/ {split($4,a,"/"); print a[1]}' \
    | paste -sd' ' -)"
  avisos+=("a interface responde na sua rede local, sem senha: quem estiver nela e abrir o endereço vê e baixa os seus clipes. Para fechar, rode com --somente-local")
fi

# `import-environment` porque as units sobem antes de o Plasma exportar a sessão
# gráfica, e sem WAYLAND_DISPLAY o kdotool não acha janela nenhuma.
systemctl --user import-environment WAYLAND_DISPLAY XDG_SESSION_TYPE XDG_CURRENT_DESKTOP DISPLAY 2>/dev/null || true
systemctl --user daemon-reload
systemctl --user enable --now captura-dia-video.service captura-dia-hud.service \
  captura-dia-hotkey.service lume.service

# --- áudio -------------------------------------------------------------------
echo "== Faixas de áudio =="
if timeout 20 "$HOME/bin/audio-bus.sh" ensure >/dev/null 2>&1 \
   && pactl list short sinks 2>/dev/null | grep -q MicBus; then
  echo "  buses de áudio no ar (microfone, Discord e jogo em faixas separadas)"
  "$HOME/bin/audio-bus.sh" discord || true
else
  avisos+=("não consegui criar os buses de áudio; o gravador vai recusar as fontes até 'audio-bus.sh ensure' funcionar")
fi

echo
if ((${#avisos[@]})); then
  echo "Anotações:"
  printf '  - %s\n' "${avisos[@]}"
  echo
fi
echo "Lumini instalado. Interface em http://127.0.0.1:8876"
for endereco in $enderecos; do
  echo "            também em http://$endereco:8876 (de outro aparelho da sua rede)"
done
echo "Abra um jogo da lista e toque F8 para salvar um clipe."
echo "Para atualizar depois:  git pull && ./instalar-lumini.sh"
