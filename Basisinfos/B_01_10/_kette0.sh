#!/bin/sh
# B Teil 0 (Voranalyse_B_Kern_stabilisieren_01_10.md Abschnitt 1/7): REGEL0-Simulation mit Spur je Handel, 4 Mengen, dann Aufteilung
cd /d/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool
for m in bestand unverzerrt:1 unverzerrt:2 unverzerrt:3; do
  f=$(echo $m | tr ':' '_')
  echo "$(date +%H:%M:%S) start $m" >> Basisinfos/B_01_10/_kette0.log
  python messe_k6_hebelstufe.py --menge $m --kurs mark --mit-btc --einstiege data/_vergleich/kern48jb_einstiege_$f.csv --simulation 24,ohne,0.02 --spur-regel0 data/_vergleich/b0_spur_$f.csv > Basisinfos/B_01_10/sim0__$f.txt 2>&1
  echo "$(date +%H:%M:%S) sim $m exit=$?" >> Basisinfos/B_01_10/_kette0.log
  python messe_b0_verlustaufteilung.py data/_vergleich/b0_spur_$f.csv $m > Basisinfos/B_01_10/teil0__$f.txt 2>&1
  echo "$(date +%H:%M:%S) teil0 $m exit=$?" >> Basisinfos/B_01_10/_kette0.log
done
