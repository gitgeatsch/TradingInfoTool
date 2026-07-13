# Einmaliges Setup pro Geraet (2026-07-13, siehe Basisinfos/Regelwerksmanual.md
# Kap. 12): legt eine Desktop-Verknuepfung an, die monitor/watchdog.py per
# pythonw.exe startet (kein Konsolenfenster). Nicht Teil des USB-Sync-Workflows
# (der Desktop-Ordner wird bewusst nicht mitgenommen) - deshalb auf Desktop-PC
# UND Notebook je einmal manuell ausfuehren:
#   powershell -ExecutionPolicy Bypass -File monitor\create_shortcut.ps1
#
# WScript.Shell (eingebautes COM-Objekt) statt pywin32 - keine zusaetzliche
# Python-Abhaengigkeit fuer einen einmaligen Setup-Schritt.

$pythonw = (Get-Command pythonw -ErrorAction Stop).Source
$projectRoot = Split-Path -Parent $PSScriptRoot
$WshShell = New-Object -ComObject WScript.Shell

# Zwei Verknuepfungen (Desktop + Start-Menu) - identisches Ziel, damit der
# Nutzer waehlen kann, ob er per Desktop-Icon oder ueber "Start" bzw. per
# Rechtsklick->"An Taskleiste anheften" startet (letzteres ist eine native
# Windows-Funktion auf der Start-Menu-Verknuepfung, kein zusaetzlicher Code
# noetig).
$targets = @(
    "$env:USERPROFILE\Desktop\TradingInfoTool.lnk",
    "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\TradingInfoTool.lnk"
)

foreach ($path in $targets) {
    $Shortcut = $WshShell.CreateShortcut($path)
    $Shortcut.TargetPath = $pythonw
    $Shortcut.Arguments = "`"$projectRoot\monitor\watchdog.py`""
    $Shortcut.WorkingDirectory = $projectRoot
    $Shortcut.IconLocation = "$pythonw,0"
    $Shortcut.Save()
    Write-Host "Verknuepfung erstellt: $path"
}

Write-Host "Ziel: $pythonw $projectRoot\monitor\watchdog.py"
Write-Host ""
Write-Host "Tipp: Start-Menu-Verknuepfung suchen (Windows-Taste, 'TradingInfoTool'),"
Write-Host "dann per Rechtsklick 'An Taskleiste anheften' fuer einen dauerhaften Taskleisten-Eintrag."
