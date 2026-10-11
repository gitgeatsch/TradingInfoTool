"""P14 Spot B1 - Teil 0 der Gegenprobe (R-R11): die BETRIEBSfunktion ``agent.spot_mitnahme.verkaufstag`` muss auf der Messbasis die
Uebertragbarkeit (Spot §39.6) bitgleich reproduzieren. Desktop, nur lesend.

    python Basisinfos/Rechenkern_02_10/p14_teil0.py

  T0a dieselben Ausloesungen: je Position Verkaufstag Messregel (fb_messung.l_regel "Z1 x3") == spot_mitnahme.verkaufstag
  T0b dieselben Zahlen: 7.819 Positionen, 7,1 % ausgeloest, Korb +4,87 Pp (sonst Abbruch - dann misst der Betrieb etwas anderes)
"""
import os
import sys

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
sys.path.insert(0, os.path.join(WURZEL, "Basisinfos", "Spot_Voranalyse_04_10"))
os.chdir(WURZEL)
import agent.spot_mitnahme as SM  # noqa: E402
import fb_messung as FB  # noqa: E402
import fb_uebertrag as FU  # noqa: E402

pf = FU.anker("alle")
alt = FB.l_auswerten(pf, "Z1 x3")
neu = FB.l_auswerten(pf, "Z1 x3", verkauf=lambda a: SM.verkaufstag(list(a["x"])))
gleich = (alt.tag.values == neu.tag.values).all() and (alt.d.values == neu.d.values).all()
k_alt, k_neu = FB.korb(alt, "d", "t").mean(), FB.korb(neu, "d", "t").mean()
print("T0a %s  Verkaufstag je Position gleich: %s (%d Positionen, Abweichungen %d)" % (
    "gleich" if gleich else "ABWEICHUNG", gleich, len(alt), int((alt.tag.values != neu.tag.values).sum())))
ok_b = len(neu) == 7819 and abs(100 * neu.aus.mean() - 7.1) < 0.05 and abs(100 * k_neu - 4.87) < 0.005
print("T0b %s  Positionen %d · ausgeloest %.2f %% · Korb %+.3f Pp (Messung %+.3f Pp)" % (
    "gleich" if ok_b else "ABWEICHUNG", len(neu), 100 * neu.aus.mean(), 100 * k_neu, 100 * k_alt))
print("\n%d von 2 gleich" % (int(gleich) + int(ok_b)))
