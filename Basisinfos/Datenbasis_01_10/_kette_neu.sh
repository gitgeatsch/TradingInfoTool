#!/bin/sh
# O11 Nachweis NEU (Voranalyse_Datenbasis_alle_Assets_01_10.md Abschnitt 8): N-1..N-3 je Menge, dann Export mit --zusatz
cd /d/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool
for m in bestand unverzerrt:1 unverzerrt:2 unverzerrt:3; do
  f=$(echo $m | tr ':' '_')
  python messe_losfahren.py --menge $m --kern --ruhe 48 --junge --mit-btc --zusatz > Basisinfos/Datenbasis_01_10/neu__$f.txt 2>&1
  echo "$(date +%H:%M:%S) neu $m exit=$?" >> Basisinfos/Datenbasis_01_10/_kette_neu.log
  python messe_losfahren.py --menge $m --kern --ruhe 48 --junge --mit-btc --zusatz --export 0.035 > Basisinfos/Datenbasis_01_10/export_zusatz__$f.txt 2>&1
  echo "$(date +%H:%M:%S) export $m exit=$?" >> Basisinfos/Datenbasis_01_10/_kette_neu.log
done
