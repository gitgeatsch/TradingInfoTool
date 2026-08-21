# -*- coding: utf-8 -*-
"""Haengt der Baermarkt-Befund am Index oder am Markt? (Umbauplan 107.4)

⚠️ Der Phasenindex normiert jede Reihe auf ihre eigene erste Kerze und mittelt
ueber die, die es an dem Tag schon gibt - von 2 Reihen (2017) bis 347 (2026).
Die Zusammensetzung wandert also, und genau daran ist Kapitel 93 A2 schon
einmal fast gescheitert ("es war die Zusammensetzung, nicht die Zeit").

Wenn der Baermarkt-Befund echt ist, muss er auch mit den Etiketten des ALTEN,
schmalen Index stehen. Die beiden stimmen zu 82,1 % ueberein - die restlichen
18 % entscheiden hier."""
import sys
sys.path.insert(0, ".")
from simuliere_bremse import _marktphase, _reihen_roh          # noqa: E402
from simuliere_bremse import klassen_aus_db                    # noqa: E402
from messe_marken import laufe                                 # noqa: E402
from messe_struktur_bereinigt import (_bandgrenzen, _reif,     # noqa: E402
                                      bereinigter_vorsprung)

f = _reif(laufe("data/messdaten.db", "krypto", roh_pruefen=False), 250)
eng = _marktphase(_reihen_roh("data/tradinginfotool.db", "krypto"))
grenzen = _bandgrenzen(f)
print(f"{len(f)} reife Anker\n")
print(f"  {'Phase':14}{'Index breit':>26}{'Index schmal':>26}")
print(f"  {'':14}{'H-Faelle':>12}{'Vorsprung':>14}"
      f"{'H-Faelle':>12}{'Vorsprung':>14}")
for ph in ("bulle", "seitwaerts", "baer"):
    zeile = f"  {ph:14}"
    for etikett in (None, eng):
        teil = [x for x in f
                if (x["phase"] if etikett is None
                    else etikett.get(x["datum"], "unbekannt")) == ph]
        v, _z = bereinigter_vorsprung(teil, grenzen)
        nh = sum(1 for x in teil if x["frei"] and x["gedeckt"])
        zeile += f"{nh:12}" + (f"{100 * v:+13.1f}" if v == v
                               else f"{'zu wenige':>13}")
    print(zeile)
