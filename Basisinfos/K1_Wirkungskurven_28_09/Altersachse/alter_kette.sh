cd "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool"
for m in bestand unverzerrt:1 unverzerrt:2 unverzerrt:3; do
  f=data/_vergleich/alter__${m/:/_}.txt
  echo "$(date +%H:%M) START $m" >> data/_vergleich/alter_kette.log
  PYTHONIOENCODING=utf-8 python messe_k1_wirkungskurven.py --menge $m --gruppe altersachse > $f 2>&1
  echo "$(date +%H:%M) ENDE  $m exit=$?" >> data/_vergleich/alter_kette.log
done
echo "$(date +%H:%M) KETTE FERTIG" >> data/_vergleich/alter_kette.log