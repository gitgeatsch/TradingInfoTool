"""PRUEFUNG der Umlaufmengen hinter den Marktwert-Klassen (Spot §30.2) - nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/mk_umlauf_pruefung.py

Anlass (08.10.): XVG mit 11 Mrd Marktwert unter den Top 15; fuer 342 von 384 Coins gilt der Umlauf von HEUTE auch fuer die Vergangenheit.
  U1  CoinMetrics SplyCur gegen CoinGecko (Profil heute) je Symbol: Verhaeltnis > 3 oder < 1/3 = Einheitenverdacht
  U2  Stichtage 2025-10 bis 2026-09 (dort gibt es die CoinGecko-Historie umlaufmenge_cg.db, Buendelfaktor schon angewandt):
      Klassen und Breite mit dem bisherigen Weg (mk_messung.umlauf) gegen Umlauf ZU t aus der Historie -> Klassenwechsel, Breite, Tor
  U3  Wachstum des Umlaufs in 12 Monaten (Historie erster gegen letzter Wert): Verteilung, groesste - Mass fuer den Fehler 'Umlauf heute' 2024
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import ein_vorpruefung as EV  # noqa: E402
import mk_messung as MK     # noqa: E402

POS = MK.POS
CG = pd.read_sql("SELECT symbol, datum, wert FROM umlaufmenge", sqlite3.connect("file:data/umlaufmenge_cg.db?mode=ro", uri=True), parse_dates=["datum"])
CGH = {s: g.set_index("datum")["wert"].sort_index() for s, g in CG.groupby("symbol")}

print("U1 CoinMetrics SplyCur (letzter Wert) gegen CoinGecko heute:")
aus = []
for s, r in MK.SPLY.items():
    h = MK.UMLAUF_HEUTE.get(s)
    if h and r.iloc[-1] > 0:
        aus.append((s, r.iloc[-1] / h, r.index[-1].date()))
U = pd.DataFrame(aus, columns=["sym", "verh", "stand"])
auff = U[(U.verh > 3) | (U.verh < 1 / 3)]
print("  %d Symbole mit beiden Quellen · Median-Verhaeltnis %.2f · auffaellig (>3 oder <1/3): %d -> %s" % (
    len(U), U.verh.median(), len(auff), ", ".join("%s x%.3g (bis %s)" % (r.sym, r.verh, r.stand) for r in auff.itertuples()) or "-"))

ALT = lambda s, t: MK.umlauf_stufe(s, t, 2)   # Stufe 2 (Faktor), ohne Historie und Riegel


def hist(s, t):                                   # = Stufe 3 ohne den CoinMetrics-Riegel (nur die Historie)
    r = CGH.get(s)
    if r is not None:
        x = r[:t]
        if len(x) and (t - x.index[-1]).days <= 7 and x.iloc[-1] > 0:
            return x.iloc[-1]
    return ALT(s, t)


stich = [t for t in pd.date_range("2025-10-01", MK.ENDE, freq="MS") if t in POS]


def lauf():
    MK._KLASSE.clear()
    return {t: MK.klassen_mw(t)[0] for t in stich}, {t: EV.breite(t) for t in stich}


MK.umlauf = ALT
k_alt, b_alt = lauf()
MK.umlauf = hist
k_neu, b_neu = lauf()
MK.umlauf = lambda s, t: MK.umlauf_stufe(s, t, 3)
n = an = 0
ueb = {}
for t in stich:
    for s in k_alt[t]:
        n += 1
        if k_alt[t][s] != k_neu[t].get(s):
            an += 1
            ueb[(k_alt[t][s], k_neu[t].get(s))] = ueb.get((k_alt[t][s], k_neu[t].get(s)), 0) + 1
print("\nU2 Stichtage %s bis %s (%d): Klasse anders bei %d von %d Coin-Stichtagen (%.1f %%) · %s" % (
    stich[0].date(), stich[-1].date(), len(stich), an, n, 100 * an / n, ", ".join("%s->%s %d" % (a, b, c) for (a, b), c in sorted(ueb.items(), key=lambda x: -x[1])[:6])))
print("  Breite bisher / mit Umlauf zu t: %s" % " · ".join("%s %.2f/%.2f%s" % (t.strftime("%Y-%m"), b_alt[t], b_neu[t], " KIPPT" if (b_alt[t] >= .5) != (b_neu[t] >= .5) else "") for t in stich))

print("\nU3 Wachstum des Umlaufs ueber die Historie (%s bis %s):" % (CG.datum.min().date(), CG.datum.max().date()))
w = pd.Series({s: r.iloc[-1] / r.iloc[0] - 1 for s, r in CGH.items() if len(r) > 300 and r.iloc[0] > 0})
print("  %d Symbole · Median %+.1f %% · Anteil > +10 %% %.0f %% · > +25 %% %.0f %% · > +50 %% %.0f %%" % (
    len(w), 100 * w.median(), 100 * (w > .1).mean(), 100 * (w > .25).mean(), 100 * (w > .5).mean()))
print("  groesste: %s" % " · ".join("%s %+.0f %%" % (s, 100 * v) for s, v in w.sort_values(ascending=False).head(12).items()))

print("\nU4 GESAMTWIRKUNG Stufe 2 -> Stufe 3 (Historie + CoinMetrics-Riegel), alle Stichtage ab 2019:")
for s in [x for x in MK.K.columns if MK.HU.vervielfacher(x)[0] > 1 and x in CGH]:
    print("  Einheit %s: Historie letzter Wert %.4g · CoinGecko heute / Faktor %.4g" % (s, CGH[s].iloc[-1], MK.UMLAUF_HEUTE.get(s, np.nan) / MK.HU.vervielfacher(s)[0]))
alle = [t for t in pd.date_range("2019-01-01", MK.ENDE, freq="MS") if t in POS]
erg = {}
for st in (2, 3):
    MK.umlauf = (lambda k: (lambda s, t: MK.umlauf_stufe(s, t, k)))(st)
    MK._KLASSE.clear()
    erg[st] = ({t: MK.klassen_mw(t)[0] for t in alle}, {t: EV.breite(t) for t in alle if POS[t] >= 90})
MK.umlauf = lambda s, t: MK.umlauf_stufe(s, t, 3)
X = pd.DataFrame([(t, MK.M.A.epoche(t), s, erg[2][0][t].get(s), erg[3][0][t].get(s)) for t in alle for s in erg[2][0][t]], columns=["t", "ep", "sym", "a", "b"])
for ep, g in X.groupby("ep"):
    d = g[g.a != g.b]
    print("  %s Klasse anders %d von %d (%.2f %%) · Symbole %s" % (ep, len(d), len(g), 100 * len(d) / len(g), ", ".join(d.sym.value_counts().head(8).index)))
kipp = [(t, erg[2][1][t], erg[3][1][t]) for t in erg[2][1] if (erg[2][1][t] >= .5) != (erg[3][1][t] >= .5)]
print("  Breite: Tor gekippt an %d Stichtagen: %s" % (len(kipp), ", ".join("%s %.2f->%.2f" % (t.date(), a, b) for t, a, b in kipp) or "-"))
