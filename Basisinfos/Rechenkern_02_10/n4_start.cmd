@echo off
rem N4 - Rueckspiel starten oder nach Neustart/Absturz FORTSETZEN (nichts geht verloren, Erledigtes wird nicht wiederholt).
rem Laeuft schon ein Laeufer, beendet sich der neue sofort. Das Fenster darf geschlossen werden: der Laeufer laeuft ohne Konsole weiter.
cd /d "%~dp0..\.."
start "" pythonw Basisinfos\Rechenkern_02_10\n4_rueckspiel.py lauf
echo N4 gestartet bzw. fortgesetzt. Stand: n4_stand.cmd - Protokoll: data\_n4\n4_lauf.log
timeout /t 5 >nul
