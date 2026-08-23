$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonw = Join-Path $root '.venv-win\Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw)) {
    throw 'Ambiente .venv-win não encontrado. Execute Lume.bat uma vez antes de instalar a inicialização.'
}
$startup = [Environment]::GetFolderPath('Startup')
$shortcutPath = Join-Path $startup 'Lume Backend.lnk'
$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = '-m app.backend.windows_startup'
$shortcut.WorkingDirectory = $root
$shortcut.WindowStyle = 7
$shortcut.Description = 'Inicia o backend do Lume sem janela de terminal'
$shortcut.Save()
Write-Output $shortcutPath
