cd "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool"
L=data/_vergleich/k1s2_kette.log
for m in bestand unverzerrt:1 unverzerrt:2 unverzerrt:3; do
  f=data/_vergleich/k1s2__${m/:/_}.txt
  echo "$(date +%H:%M) START $m" >> $L
  PYTHONIOENCODING=utf-8 python messe_k1_schritt2_kombination.py --menge $m > $f 2>&1
  rc=$?
  if grep -q "SCHLUSS: vollstaendig" $f && ! grep -q "Traceback" $f; then ok=vollstaendig; else ok=UNVOLLSTAENDIG; fi
  echo "$(date +%H:%M) ENDE  $m exit=$rc $ok" >> $L
done
echo "$(date +%H:%M) KETTE FERTIG" >> $L