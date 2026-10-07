@echo off
rem N5 - Rueckspiel der Fassung 0.2 starten oder nach Neustart/Absturz FORTSETZEN (Schritt7 Par. 23.20). Wartet, bis N4 beendet ist.
rem Laeuft schon ein Laeufer, beendet sich der neue sofort. Das Fenster darf geschlossen werden: der Laeufer laeuft ohne Konsole weiter.
cd /d "%~dp0..\.."
start "" pythonw Basisinfos\Rechenkern_02_10\n5_rueckspiel.py lauf --warte-auf-n4
echo N5 gestartet bzw. fortgesetzt (wartet auf das Ende von N4). Stand: n5_stand.cmd - Protokoll: data\_n5\n4_lauf.log
timeout /t 5 >nul
