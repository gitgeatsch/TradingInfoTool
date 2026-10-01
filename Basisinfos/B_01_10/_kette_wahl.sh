#!/bin/sh
# B Teil B Wahl 2024 (Voranalyse_B_Kern_stabilisieren_01_10.md Abschnitt 2): R-R11 F0 ohne BTC = 2.699 W2, dann F0/F1/F2 in der REGEL0-Form mit BTC
cd /d/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool
echo "$(date +%H:%M:%S) start rr11" >> Basisinfos/B_01_10/_kette_wahl.log
python messe_losfahren.py --menge bestand --kern --ruhe 48 --junge --daempfung F0 > Basisinfos/B_01_10/wahl_rr11_F0_ohne_btc__bestand.txt 2>&1
echo "$(date +%H:%M:%S) rr11 exit=$?" >> Basisinfos/B_01_10/_kette_wahl.log
for F in F0 F1 F2; do
  python messe_losfahren.py --menge bestand --kern --ruhe 48 --junge --mit-btc --daempfung $F > Basisinfos/B_01_10/wahl_${F}__bestand.txt 2>&1
  echo "$(date +%H:%M:%S) $F exit=$?" >> Basisinfos/B_01_10/_kette_wahl.log
done
