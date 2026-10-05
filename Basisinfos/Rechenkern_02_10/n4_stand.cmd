@echo off
rem N4 - Fortschritt, Kontingent, Fehler (ohne Trennzahlen, kein Zwischenblick).
cd /d "%~dp0..\.."
set PYTHONIOENCODING=utf-8
python Basisinfos\Rechenkern_02_10\n4_rueckspiel.py stand
pause
