"""WIRKUNG der Buendelfaktor-Korrektur auf die Marktwert-Klassen und die Altseason-Breite (Spot §30.2) - nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/mk_buendel_wirkung.py

Befund 2.501-buendelpaare (21.09.): Binance handelt 1000SATS, 1MBABYDOGE ... als Buendel, CoinGecko fuehrt die Menge des Einzeltokens.
mk_messung.umlauf nahm die Menge OHNE Faktor -> Marktwert bis 10^6 zu hoch (1MBABYDOGE ab 2025 Rang 1).
Gemessen wird ALT (wie bis 08.10.) gegen NEU (Menge / hole_umlaufmenge_cg.vervielfacher), an allen Stichtagen ab 2019:
  W1 betroffene Symbole · W2 Coin-Stichtage mit anderer Klasse (je Epoche) · W3 Breite: Stichtage mit anderem Wert / gekipptem Tor (>= 50 %)
"""
import os
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
sys.path.insert(0, os.getcwd())
import hole_umlaufmenge_cg as HU  # noqa: E402
import mk_messung as MK     # noqa: E402
import ein_vorpruefung as EV  # noqa: E402

M, POS = MK.M, MK.POS
stich = [t for t in pd.date_range("2019-01-01", MK.ENDE, freq="MS") if t in POS]
betr = sorted(s for s in MK.K.columns if HU.vervielfacher(s)[0] > 1)
print("W1 Buendelsymbole in der Kursbasis: %s" % ", ".join("%s (x%g)" % (s, HU.vervielfacher(s)[0]) for s in betr))

NEU = lambda s, t: MK.umlauf_stufe(s, t, 2)          # Stufe 2: mit Buendelfaktor
ALT_F = lambda s, t: MK.umlauf_stufe(s, t, 1)        # Stufe 1: Stand bis 08.10. (ohne Faktor)


def lauf():
    MK._KLASSE.clear()
    kl = {t: MK.klassen_mw(t)[0] for t in stich}
    br = {t: EV.breite(t) for t in stich if POS[t] >= 90}
    return kl, br


MK.umlauf = ALT_F
k_alt, b_alt = lauf()
MK.umlauf = NEU
k_neu, b_neu = lauf()

zeilen = []
for t in stich:
    for s in set(k_alt[t]) | set(k_neu[t]):
        zeilen.append((t, M.A.epoche(t), s, k_alt[t].get(s), k_neu[t].get(s)))
X = pd.DataFrame(zeilen, columns=["t", "ep", "sym", "alt", "neu"])
X["anders"] = X.alt != X.neu
print("\nW2 Coin-Stichtage mit ANDERER Marktwert-Klasse:")
for ep, g in X.groupby("ep"):
    a = g[g.anders]
    print("  %s  %d von %d (%.2f %%) · davon Buendelsymbole selbst %d · Uebergaenge %s" % (
        ep, len(a), len(g), 100 * len(a) / len(g), a.sym.isin(betr).sum(),
        ", ".join("%s->%s %d" % (x, y, n) for (x, y), n in a.groupby(["alt", "neu"]).size().sort_values(ascending=False).head(6).items())))
ab24 = X[X.t >= "2024-01-01"]
print("  ab 2024: %d von %d (%.2f %%)" % (ab24.anders.sum(), len(ab24), 100 * ab24.anders.mean()))

print("\nW3 Altseason-Breite (Top 50 nach Marktwert ohne BTC):")
d = pd.DataFrame([(t, b_alt[t], b_neu[t]) for t in b_alt], columns=["t", "alt", "neu"])
d["diff"] = (d.neu - d.alt).abs()
kipp = d[(d.alt >= 0.5) != (d.neu >= 0.5)]
print("  Stichtage %d · mit anderem Wert %d · groesste Abweichung %.3f · Tor gekippt an %d: %s" % (
    len(d), int((d["diff"] > 1e-12).sum()), d["diff"].max(), len(kipp),
    ", ".join("%s %.2f->%.2f" % (r.t.date(), r.alt, r.neu) for r in kipp.itertuples()) or "-"))
MK.umlauf = lambda s, t: MK.umlauf_stufe(s, t, 3)
