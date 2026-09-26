<#
.SYNOPSIS
    Inicia o Lume no Windows (equivalente ao lume.service do Linux).

.DESCRIPTION
    Prepara o ambiente na primeira execução e sobe a interface local. Enquanto
    esta janela estiver aberta, a captura roda; ao fechá-la, tudo é encerrado
    junto — no Windows não há systemd para manter o serviço de pé, então a
    própria interface é o processo supervisor.

.PARAMETER NoBrowser
    Não abre o navegador automaticamente.

.PARAMETER Port
    Porta da interface (padrão 8876).
#>
[CmdletBinding()]
param(
    [switch]$NoBrowser,
    [int]$Port = 8876
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venv = Join-Path $root '.venv-win'
$python = Join-Path $venv 'Scripts\python.exe'

# O que é de uma máquina só — caminho do banco compartilhado com o Linux, redes
# da VPN, porta aberta para fora — mora em `lume-local.ps1`, fora do
# versionamento. Sem esse arquivo o Lume sobe fechado em 127.0.0.1, que é o que
# a máquina de outra pessoa deve fazer.
$env:LUME_REQUIREMENTS = 'requirements.txt'
$env:LUME_IMPORT_CHECK = 'import fastapi, uvicorn, numpy, sherpa_onnx'
$env:LUME_BIND_HOST = '127.0.0.1'
$local = Join-Path $root 'lume-local.ps1'
if (Test-Path $local) { . $local }

Write-Host "Lume — captura local do dia" -ForegroundColor Cyan
Write-Host ""

# --- Pré-requisitos ---------------------------------------------------------
$systemPython = Get-Command python -ErrorAction SilentlyContinue
if (-not $systemPython) {
    Write-Host "Python não encontrado no PATH." -ForegroundColor Red
    Write-Host "Instale em https://www.python.org/downloads/ marcando 'Add python.exe to PATH'."
    Read-Host "Enter para sair"
    exit 1
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "AVISO: ffmpeg não está no PATH." -ForegroundColor Yellow
    Write-Host "  A captura de telas depende dele. Instale com: winget install Gyan.FFmpeg"
    Write-Host ""
}

# --- Ambiente Python --------------------------------------------------------
if (-not (Test-Path $python)) {
    Write-Host "Criando o ambiente Python em .venv-win (só na primeira vez)..."
    & python -m venv $venv
    if ($LASTEXITCODE -ne 0) { Write-Host "Falha ao criar o ambiente." -ForegroundColor Red; Read-Host; exit 1 }
}

# Instala as dependências apenas quando faltam, para a abertura ser rápida.
& $python -c $env:LUME_IMPORT_CHECK 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Instalando dependências..."
    & $python -m pip install --disable-pip-version-check -q -r (Join-Path $root $env:LUME_REQUIREMENTS)
    if ($LASTEXITCODE -ne 0) { Write-Host "Falha ao instalar dependências." -ForegroundColor Red; Read-Host; exit 1 }
}

# --- Interface --------------------------------------------------------------
$url = "http://127.0.0.1:$Port"
Write-Host "Interface em $url" -ForegroundColor Green
if ($env:LUME_REMOTE_HOSTS) {
    foreach ($host_ in $env:LUME_REMOTE_HOSTS.Split(',')) {
        Write-Host "Tambem em http://$($host_.Trim()):$Port" -ForegroundColor DarkGreen
    }
}
Write-Host "Feche esta janela (ou Ctrl+C) para encerrar a captura."
Write-Host ""

if (-not $NoBrowser) {
    Start-Job -ScriptBlock { Start-Sleep -Seconds 3; Start-Process $using:url } | Out-Null
}

Set-Location $root
& $python -m uvicorn app.backend.main:app --host $env:LUME_BIND_HOST --port $Port
