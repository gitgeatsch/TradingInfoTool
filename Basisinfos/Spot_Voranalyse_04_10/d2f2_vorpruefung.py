"""D2 Fassung 2, Vorpruefung (06.10.2026): NUR wann die Kipp-Ausloeser gegriffen haetten - Klima q (BTC) und Datum, KEINE Ertraege."""
import os
import pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
src = open("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py", encoding="utf-8").read().split("pb, mb = lade")[0]
g = {"__file__": os.path.abspath("Basisinfos/Spot_Voranalyse_04_10/k3_gewichten.py")}; exec(compile(src, "k3", "exec"), g)
pb, mb = g["lade"]("btc"); q = g["klima"](pb, mb, pd.Timestamp("2013-01-01")).dropna()
q = q[q.index >= "2015-01-01"]
for name, scharf, ab in (("K1: scharf ab q >= 0,90; Verkauf beim Fall unter 0,85 / 0,75 / 0,65", 0.90, (0.85, 0.75, 0.65)),
                         ("K2: scharf ab q >= 0,80; Verkauf beim Fall 0,10 / 0,20 / 0,30 unter das Zyklushoch von q", 0.80, None)):
    print(name)
    an, hoch, offen = False, 0.0, []
    for t, x in q.items():
        if x <= 0.20:
            an, hoch, offen = False, 0.0, []
        if x >= scharf and not an:
            an, hoch = True, x
            offen = list(ab) if ab else [0.10, 0.20, 0.30]
            print("  %s scharf (q %.2f)" % (t.date(), x))
        if an:
            hoch = max(hoch, x)
            for st in list(offen):
                grenze = st if ab else hoch - st
                if x < grenze:
                    offen.remove(st)
                    print("  %s VERKAUF Stufe %s (q %.2f, Zyklushoch %.2f)" % (t.date(), st, x, hoch))
