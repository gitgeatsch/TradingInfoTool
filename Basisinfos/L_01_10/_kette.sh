#!/bin/sh
# L (Voranalyse_L_Liquiditaet_01_10.md Abschnitt 9): L0/L1 in 4 Mengen (Wahl nur bestand), L2-Spur bestand, Auswertungen
cd /d/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool
for m in bestand unverzerrt:1 unverzerrt:2 unverzerrt:3; do
  f=$(echo $m | tr ':' '_')
  python messe_losfahren.py --menge $m --kern --ruhe 48 --junge --mit-btc --liq > Basisinfos/L_01_10/liq__$f.txt 2>&1
  echo "$(date +%H:%M:%S) liq $m exit=$?" >> Basisinfos/L_01_10/_kette.log
done
python messe_k6_hebelstufe.py --menge bestand --kurs mark --mit-btc --einstiege data/_vergleich/kern48jb_einstiege_bestand.csv --simulation 24,ohne,0.02 --spur-regel0 data/_vergleich/l2_spur_bestand.csv --spur-alle > Basisinfos/L_01_10/sim_l2__bestand.txt 2>&1
echo "$(date +%H:%M:%S) sim l2 exit=$?" >> Basisinfos/L_01_10/_kette.log
python messe_l2_liq_risiko.py data/_vergleich/l2_spur_bestand.csv data/_vergleich/l_liq_bestand.csv 2024 > Basisinfos/L_01_10/l2__bestand.txt 2>&1
echo "$(date +%H:%M:%S) l2 exit=$?" >> Basisinfos/L_01_10/_kette.log
