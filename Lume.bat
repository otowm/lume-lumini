@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Lume

rem Lancador do Lume no Windows. Duplo clique e pronto.
rem Batch puro, sem PowerShell: nao depende de politica de execucao.
rem Uso opcional:  Lume.bat [porta]
rem
rem Este arquivo e' deliberadamente so ASCII, sem acentos. O cmd.exe le o .bat
rem por deslocamento de bytes e reabre o arquivo a cada comando; caracteres
rem multibyte desalinham esse deslocamento e o parser passa a retomar no meio
rem das palavras. Mensagens sem acento sao o preco de um lancador confiavel.

set "PORT=8876"
if not "%~1"=="" set "PORT=%~1"
set "VENV=%~dp0.venv-win"
set "PY=%VENV%\Scripts\python.exe"
set "URL=http://127.0.0.1:%PORT%"

rem Ajustes de uma maquina especifica (caminho do banco, redes remotas) vivem
rem num arquivo proprio, fora do versionamento: um caminho `F:\lume` ou um IP de
rem VPN cravados aqui viajariam para quem clonasse o projeto.
rem Fechado por padrao; `lume-local.cmd` pode abrir para a rede.
if not defined LUME_BIND_HOST set "LUME_BIND_HOST=127.0.0.1"
if not defined LUME_REQUIREMENTS set "LUME_REQUIREMENTS=requirements.txt"
if not defined LUME_IMPORT_CHECK set "LUME_IMPORT_CHECK=import fastapi, uvicorn, numpy, sherpa_onnx"
if exist "%~dp0lume-local.cmd" call "%~dp0lume-local.cmd"

echo.
echo   Lume - captura local do dia
echo.

rem --- Pre-requisitos --------------------------------------------------------
where python >nul 2>&1
if errorlevel 1 (
    echo   [ERRO] Python nao encontrado no PATH.
    echo          Instale em https://www.python.org/downloads/
    echo          marcando "Add python.exe to PATH".
    echo.
    pause
    exit /b 1
)

where ffmpeg >nul 2>&1
if errorlevel 1 (
    echo   [AVISO] ffmpeg nao esta no PATH - a captura de telas depende dele.
    echo           Instale com: winget install Gyan.FFmpeg
    echo.
)

rem --- Ambiente Python -------------------------------------------------------
if not exist "%PY%" (
    echo   Criando o ambiente Python ^(so na primeira vez^)...
    python -m venv "%VENV%"
    if errorlevel 1 (
        echo   [ERRO] Falha ao criar o ambiente.
        pause
        exit /b 1
    )
)

rem Instala as dependencias so quando faltam, para a abertura ser rapida.
"%PY%" -c "%LUME_IMPORT_CHECK%" >nul 2>&1
if errorlevel 1 (
    echo   Instalando dependencias...
    "%PY%" -m pip install --disable-pip-version-check -q -r "%~dp0%LUME_REQUIREMENTS%"
    if errorlevel 1 (
        echo   [ERRO] Falha ao instalar as dependencias.
        pause
        exit /b 1
    )
)

rem --- Interface -------------------------------------------------------------
echo   Interface em %URL%
echo.

rem Se o backend invisivel do login ja estiver ativo, apenas abre a interface.
where curl.exe >nul 2>&1
if not errorlevel 1 (
    curl.exe -fsS "%URL%/api/health" >nul 2>&1
    if not errorlevel 1 (
        start "" "%URL%"
        exit /b 0
    )
)

echo   Feche esta janela ^(ou Ctrl+C^) para encerrar a captura.
echo.

rem Abre o navegador em paralelo, depois que o servidor tiver subido.
start "" /min cmd /c "timeout /t 3 /nobreak >nul&start %URL%"

"%PY%" -m uvicorn app.backend.main:app --host %LUME_BIND_HOST% --port %PORT%
set "CODE=%ERRORLEVEL%"

rem Ctrl+C encerra com 15 no cmd; nao e' falha, e' o usuario fechando.
if not "%CODE%"=="0" if not "%CODE%"=="15" (
    echo.
    echo   O Lume encerrou com erro ^(codigo %CODE%^).
    pause
)
exit /b %CODE%
