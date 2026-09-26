# Lumini no Windows: só o gravador de gameplay e a biblioteca de clipes.
#
# Diferente do Linux, aqui o gravador não é um serviço próprio: ele roda dentro
# do processo da interface (é ela que supervisiona `app.capture.winvideo`). Por
# isso o Lumini precisa subir junto com o Windows — senão é preciso lembrar de
# abrir o app antes de jogar, e a jogada que valia já passou.
#
# Uso:  powershell -ExecutionPolicy Bypass -File instalar-lumini.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "== Conferindo o que o gravador precisa ==" -ForegroundColor Cyan

$comando = Get-Command python -ErrorAction SilentlyContinue
if (-not $comando) {
    throw "Python nao encontrado. Instale de python.org (marque 'Add to PATH') e rode de novo."
}
$python = $comando.Source

# O banco exige SQLite com FTS5. O Python da Microsoft Store as vezes vem sem —
# e sem isso nada funciona, nem gravar.
& $python -c "import sqlite3;sqlite3.connect(':memory:').execute('CREATE VIRTUAL TABLE t USING fts5(x)')" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Este Python nao tem SQLite com FTS5. Instale o Python de python.org (nao o da Microsoft Store)."
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "  ffmpeg nao esta no PATH — sem ele o corte e a versao leve nao funcionam." -ForegroundColor Yellow
    Write-Host "  Instale com:  winget install Gyan.FFmpeg" -ForegroundColor Yellow
}

$obs = @("$env:ProgramFiles\obs-studio\bin\64bit\obs64.exe",
         "${env:ProgramFiles(x86)}\obs-studio\bin\64bit\obs64.exe") |
        Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $obs) {
    Write-Host "  OBS Studio nao encontrado. E' ele que grava no Windows." -ForegroundColor Yellow
    Write-Host "  Instale de https://obsproject.com e rode este script de novo." -ForegroundColor Yellow
} else {
    Write-Host ("  OBS encontrado. Na primeira gravacao o Lumini faz uma copia propria dele " +
                "(~475 MB) em ~\.lume-obs, e isso demora alguns minutos.")
    $unidade = Get-PSDrive -Name $HOME.Substring(0,1) -ErrorAction SilentlyContinue
    if ($unidade -and ($unidade.Free / 1GB) -lt 1.5) {
        Write-Host ("  Atencao: so {0:N1} GB livres em {1}." -f ($unidade.Free / 1GB), $unidade.Root) -ForegroundColor Yellow
    }
}

# --- ambiente Python ---------------------------------------------------------
$venv = Join-Path $root '.venv-win'
$venvPython = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "== Criando o ambiente Python ==" -ForegroundColor Cyan
    & $python -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw "Falha ao criar o ambiente Python." }
}
Write-Host "== Instalando as dependencias do gravador ==" -ForegroundColor Cyan
& $venvPython -m pip install --disable-pip-version-check -q --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Falha ao atualizar o pip." }
& $venvPython -m pip install --disable-pip-version-check -q -r (Join-Path $root 'requirements-lumini.txt')
if ($LASTEXITCODE -ne 0) { throw "Falha ao instalar as dependencias do gravador." }

if (-not (Test-Path -LiteralPath (Join-Path $root 'frontend\dist\index.html'))) {
    throw "Falta frontend\dist — a interface nao foi compilada neste clone."
}

# --- configuracao ------------------------------------------------------------
# No Windows o caminho da config é `~\captura-dia\config` (o %APPDATA% do Python
# da Store é virtualizado e some do resto do sistema).
$configDir = Join-Path $HOME 'captura-dia\config'
New-Item -ItemType Directory -Force -Path $configDir | Out-Null
Set-Content -LiteralPath (Join-Path $configDir 'lume.conf') -Value 'LUME_MODE=lumini' -Encoding ASCII

# Copia o template de video.conf: sem ele os padrões ficam só no código, e eles
# divergem do template (30 fps contra 60).
$videoConf = Join-Path $configDir 'video.conf'
if (-not (Test-Path -LiteralPath $videoConf)) {
    (Get-Content -LiteralPath (Join-Path $root 'config\captura-dia\video.conf')) `
        -replace '^VIDEO_ENABLED=false$', 'VIDEO_ENABLED=true' |
        Set-Content -LiteralPath $videoConf -Encoding UTF8
}
$appsConf = Join-Path $configDir 'video-apps.txt'
if (-not (Test-Path -LiteralPath $appsConf)) {
    Copy-Item (Join-Path $root 'config\captura-dia\video-apps.txt') $appsConf
}

# --- atalhos -----------------------------------------------------------------
$shell = New-Object -ComObject WScript.Shell

# Na inicializacao, sem janela: no Windows o gravador vive dentro da interface.
$startup = Join-Path ([Environment]::GetFolderPath('Startup')) 'Lumini.lnk'
$atalho = $shell.CreateShortcut($startup)
$atalho.TargetPath = Join-Path $venv 'Scripts\pythonw.exe'
$atalho.Arguments = '-m app.backend.windows_startup'
$atalho.WorkingDirectory = $root
$atalho.WindowStyle = 7
$atalho.Description = 'Lumini - gravador de gameplay'
$atalho.Save()

# E na Area de Trabalho, para abrir a biblioteca quando quiser.
$desktop = Join-Path ([Environment]::GetFolderPath('Desktop')) 'Lumini.lnk'
$mesa = $shell.CreateShortcut($desktop)
$mesa.TargetPath = Join-Path $root 'Lumini.bat'
$mesa.WorkingDirectory = $root
$mesa.Description = 'Abre o Lumini'
$mesa.Save()

Write-Host ""
Write-Host "Lumini instalado." -ForegroundColor Green
Write-Host "  Atalho na Area de Trabalho e inicializacao automatica com o Windows."
Write-Host "  Interface em http://127.0.0.1:8876"
Write-Host "  Abra um jogo da lista e toque F8 para salvar um clipe."
Write-Host "  Para atualizar depois:  git pull  e rodar este script de novo."
