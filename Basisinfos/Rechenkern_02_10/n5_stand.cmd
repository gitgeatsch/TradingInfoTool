@echo off
rem N5 - Fortschritt, Kontingent, Fehler (ohne Trennzahlen, kein Zwischenblick).
cd /d "%~dp0..\.."
set PYTHONIOENCODING=utf-8
python Basisinfos\Rechenkern_02_10\n5_rueckspiel.py stand
pause
