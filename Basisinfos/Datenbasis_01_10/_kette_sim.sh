#!/bin/sh
# O11 N-5: Simulation REGEL0-Erfolgsmessung mit den neuen Assets, Gruppe NEU getrennt; R-R11 Konto der uebrigen = REGEL0-Referenz
cd /d/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool
for m in bestand unverzerrt:1 unverzerrt:2 unverzerrt:3; do
  f=$(echo $m | tr ':' '_')
  python messe_k6_hebelstufe.py --menge $m --kurs mark --mit-btc --zusatz --einstiege data/_vergleich/kern48jbz_einstiege_$f.csv --gruppe data/_vergleich/kern48jbz_gruppe_$f.csv --simulation 24,ohne,0.02 > Basisinfos/Datenbasis_01_10/sim_neu__$f.txt 2>&1
  echo "$(date +%H:%M:%S) sim $m exit=$?" >> Basisinfos/Datenbasis_01_10/_kette_sim.log
done
