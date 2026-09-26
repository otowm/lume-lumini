@echo off
setlocal EnableExtensions

rem Lumini: o gravador de gameplay sem nada de IA.
rem
rem Nao duplica o lancador: ajusta o que muda e chama o Lume.bat, que ja sabe
rem criar o ambiente, conferir dependencias e subir a interface. Duplicar daria
rem dois lancadores para corrigir toda vez.
rem
rem Este arquivo e' so ASCII de proposito: o cmd.exe le o .bat por deslocamento
rem de bytes, e acento desalinha o parser.

rem So fastapi, uvicorn e websockets. Sem numpy e sem sherpa-onnx, que existem
rem para a analise e levariam centenas de MB para nada.
set "LUME_REQUIREMENTS=requirements-lumini.txt"
set "LUME_IMPORT_CHECK=import fastapi, uvicorn, websockets"

rem O modo tambem vive no lume.conf que o instalador escreve; aqui ele garante
rem que abrir por este atalho nunca acorde a interface completa.
set "LUME_MODE=lumini"

rem Responde na rede local, para abrir a biblioteca do celular ou de outro PC.
rem As faixas privadas inteiras, e nao o endereco de agora: trocar de Wi-Fi ou
rem renovar o DHCP nao pode fazer a interface parar de abrir. Na primeira vez o
rem Windows pergunta se libera na rede.
if not defined LUME_BIND_HOST set "LUME_BIND_HOST=0.0.0.0"
if not defined LUME_REMOTE_NETWORKS set "LUME_REMOTE_NETWORKS=10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"

title Lumini
call "%~dp0Lume.bat" %*
