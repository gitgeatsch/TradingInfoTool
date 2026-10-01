#!/bin/sh
# A Bestaetigung 2025-26 (Voranalyse_A_Positionsfuehrung_01_10.md Abschnitt 5/6), 4 Mengen nacheinander
cd /d/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool
for m in bestand unverzerrt:1 unverzerrt:2 unverzerrt:3; do
  f=$(echo $m | tr ':' '_')
  echo "$(date +%H:%M:%S) start $m" >> Basisinfos/A_01_10/_kette.log
  python messe_k6_hebelstufe.py --menge $m --kurs mark --mit-btc --einstiege data/_vergleich/kern48jb_einstiege_$f.csv --stop 72,1.5,1 > Basisinfos/A_01_10/best__$f.txt 2>&1
  echo "$(date +%H:%M:%S) ende $m exit=$?" >> Basisinfos/A_01_10/_kette.log
done
