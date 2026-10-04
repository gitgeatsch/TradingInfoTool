"""V-2b der Spot-Voranalyse (O23): Kauft die Regel *unter dem 200-Tage-Schnitt* (UNTER_SMA / schnitt, das Akkumulationsmass)
in den Verlust nach - oder an einem Boden? Rueckspiel 2024 bis 2026 auf der Messbasis, ohne LLM, nur lesend.

Tageskurs = Schlusskurs der Stunde 23:00 UTC (data/stundenkurse.db, Messbasis, mode=ro).
Je Asset und Tag: abstand = Kurs / Schnitt200 - 1. Stufen: UNTER (abstand < 0), TIEF (< -30 %), SEHR TIEF (< -50 %).
Gemessen: Ertrag nach 30 und 90 Tagen roh, gegen den Median ALLER Assets am selben Tag (tagestreu), und die Lage im
Bereich 30 Tage davor bis 30 Tage danach (0 = Boden). Bezug ist jeder Asset-Tag (Zufallskauf).
Unabhaengig gezaehlt: Asset-Monate (ein Wert je Asset und Monat). Urteil je Jahr - das Regime ist das Hauptrisiko.
"""
import os
import sqlite3

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
c = sqlite3.connect("file:data/stundenkurse.db?mode=ro", uri=True)
d = pd.read_sql("select symbol, stunde, close from stundenkurse where substr(stunde, 12, 2) = '23'", c)
c.close()
d["tag"] = d["stunde"].str[:10]
K = d.pivot(index="tag", columns="symbol", values="close").sort_index()
K.index = pd.to_datetime(K.index)
K = K.asfreq("D")
sma = K.rolling(200, min_periods=200).mean()
AB = K / sma - 1
R = {h: K.shift(-h) / K - 1 for h in (30, 90)}
MED = {h: R[h].median(axis=1) for h in R}
# Rang am selben Tag (0 schlechtestes, 1 bestes Asset; Zufall 0,50) - unempfindlich gegen die rechte Schiefe. Das Mittel der
# Abstaende zum Tagesmedian war es nicht: schon JEDER Tag lag damit bei +3 bis +10 % (erste Fassung, verworfen)
U = {h: R[h].rank(axis=1, pct=True) for h in R}
tief = K.rolling(61, center=True, min_periods=61).min()
hoch = K.rolling(61, center=True, min_periods=61).max()
LAGE = (K - tief) / (hoch - tief)
print("V-2b Rueckspiel UNTER dem 200-Tage-Schnitt - Messbasis %d Assets, Tage %s bis %s" % (K.shape[1], K.index[0].date(), K.index[-1].date()))
print()


def zeile(maske, titel, jahr):
    sel = maske & (K.index.year == jahr)[:, None]
    out = "  %-22s" % titel
    n_ges = int(np.nansum(sel))
    out += " Asset-Tage %6d" % n_ges
    for h in (30, 90):
        r = R[h].where(sel).stack().dropna()
        u = U[h].where(sel).stack().dropna()
        if len(r) < 30:
            out += " | %2d T  -" % h
            continue
        # unabhaengig: Asset-Monate
        um = u.groupby([u.index.get_level_values(0).to_period("M"), u.index.get_level_values(1)]).mean()
        se = um.std(ddof=1) / np.sqrt(len(um))
        urt = "ueber" if um.mean() - 2 * se > 0 else ("UNTER" if um.mean() + 2 * se < 0 else "~null")
        urt = "besser" if um.mean() - 2 * se > 0.5 else ("SCHLECHTER" if um.mean() + 2 * se < 0.5 else "~Zufall")
        out += " | %2d T roh %+6.1f %% Minus %3.0f %% | Rang %.3f +- %.3f (AM %d, %s)" % (
            h, 100 * r.median(), 100 * (r < 0).mean(), um.mean(), se, len(um), urt)
    lg = LAGE.where(sel).stack().dropna()
    if len(lg) >= 30:
        out += " | Lage %.2f, Boden-Fuenftel %2.0f %%" % (lg.median(), 100 * (lg < 0.2).mean())
    print(out)


for jahr in (2024, 2025, 2026):
    print("== %d" % jahr)
    alle = AB.notna()
    zeile(alle, "JEDER Tag (Bezug)", jahr)
    zeile(AB < 0, "UNTER Schnitt", jahr)
    zeile(AB < -0.30, "TIEF (< -30 %)", jahr)
    zeile(AB < -0.50, "SEHR TIEF (< -50 %)", jahr)
    zeile(AB > 0.30, "WEIT DARUEBER (> +30 %)", jahr)
    print()
print("Lesart: *roh* = was ein Kauf gebracht haette (Median); *Rang* = Platz des Ertrags unter allen Assets desselben Tages,")
print("0,50 = Zufall, Mittel ueber Asset-Monate mit Standardfehler (Urteil bei 2 SE). *Minus* = Anteil, der nach h Tagen tiefer stand. Lage 0,5 = Zufall, < 0,2 = Boden.")
