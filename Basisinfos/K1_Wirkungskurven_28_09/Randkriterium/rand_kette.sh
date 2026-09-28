#!/bin/bash
cd "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool"
for m in unverzerrt:1 unverzerrt:2 unverzerrt:3 bestand; do
  mm=${m/:/_}
  for lauf in "voll|--gruppe voll" "termin|--gruppe termin" "teilung_eigen|--gruppe teilung --nur-eigen" "teilung_markt|--gruppe teilung --nur-markt --gemeinsam" "tt_eigen|--gruppe termin_teilung --nur-eigen" "tt_markt|--gruppe termin_teilung --nur-markt --gemeinsam"; do
    name=${lauf%%|*}; args=${lauf#*|}
    echo "$(date +%H:%M) START $name $m" >> data/_vergleich/rand_kette.log
    PYTHONIOENCODING=utf-8 python messe_k1_wirkungskurven.py --menge "$m" $args > "data/_vergleich/rand__${name}__${mm}.txt" 2>&1
    echo "$(date +%H:%M) ENDE  $name $m exit=$?" >> data/_vergleich/rand_kette.log
  done
done
echo "$(date +%H:%M) KETTE FERTIG" >> data/_vergleich/rand_kette.log
