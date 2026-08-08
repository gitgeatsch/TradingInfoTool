#!/bin/sh
# Nachtlauf 08.08. - alles Lange hintereinander, jede Stufe in eine eigene
# Logdatei (unbuffered), damit ein Abbruch nie die ganze Messung kostet.
cd "C:/Users/Geatsch/AppData/Local/Temp/claude/D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool/a51e0ce8-8568-4daa-bcd2-9c2b6bc3aec7/scratchpad"

# 1) auf das laufende Screening + den Schema-Test warten
until [ -f schema.log ] && grep -q "=> B" schema.log 2>/dev/null; do sleep 30; done
echo "[$(date +%H:%M)] Screening + Schema fertig"

# 2) laguna-xs auf 20 Faelle - sonst stehen 3 Faelle gegen nemotrons 20
sleep 60
python -u haertetest.py 20 poolside/laguna-xs-2.1:free > laguna20.log 2>&1
echo "[$(date +%H:%M)] laguna-xs 20er fertig"

# 3) historischer Ruecktest gegen Mistrals -27,38 R
#    Format kommt aus dem gemessenen Schema-Ergebnis, nicht aus einer Annahme
sleep 60
FMT=$(python entscheide_format.py 2>format_entscheidung.txt)
echo "[$(date +%H:%M)] Rueckspiel-Format: ${FMT:-json_object}"
python -u rueckspiel.py $FMT > rueckspiel.log 2>&1
echo "[$(date +%H:%M)] Rueckspiel fertig"
