"""Spot K-0, Messplan FASSUNG 1 (Voranalyse_Spot_Neubau_04_10.md §8.6, Commit 9a16c0d; E-61) - Klima und echte Bodenbildung, BTC.

    python Basisinfos/Spot_Voranalyse_04_10/k1_klima_studie.py

Nur lesend: data/_spot/coinmetrics.db (BTC PriceUSD, CapMVRVCur ab 2010) und data/messdaten.db (Breite aus allen Krypto-Reihen,
eingestellte eingeschlossen). Kein Netz, kein LLM, kein Betriebscode (T-2, T-5).

AUSLEGUNG von Fassung 1, festgelegt VOR dem ersten Lauf (im Plan nicht genau bestimmt):
  - Kurs = CoinMetrics PriceUSD (Tagesschluss); Tief und Ereignisse daraus (die Pruefung §8.4 lief auf Binance-Tagestiefs)
  - Zyklus fuer H4 = Fenster [Tief - 365 T, Tief + 365 T] um jedes echte Tief (Fenster duerfen sich ueberlappen)
  - eine B-Einschaltung = erster B-Tag nach mindestens 10 Tagen ohne B (H3)
  - Breite nur an Tagen mit mindestens 50 Reihen mit 50-Tage-Schnitt
"""
import os
import sqlite3

import numpy as np
import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RNG = np.random.default_rng(20261005)


def ro(p):
    return sqlite3.connect("file:%s?mode=ro" % p.replace("\\", "/"), uri=True)


c = ro("data/_spot/coinmetrics.db")
cm = pd.read_sql("SELECT tag, PriceUSD AS kurs, CapMVRVCur AS mvrv FROM tag WHERE asset='btc' ORDER BY tag", c, parse_dates=["tag"]).set_index("tag")
c.close()
p = cm["kurs"].asfreq("D").ffill()
mvrv = cm["mvrv"].asfreq("D").ffill()
AB = pd.Timestamp("2013-01-01")


def pct_wachsend(x):
    x = x[x.index >= AB]
    return x.expanding(min_periods=365).rank(pct=True).reindex(p.index)


# ---- A Zone ----
lr = np.log(p).diff()
dd = p / p.cummax() - 1
vol = lr.rolling(365, min_periods=300).std() * np.sqrt(365)
A1 = pct_wachsend(mvrv) <= 0.20
A2 = pct_wachsend(-dd / vol) >= 0.80
A3 = pct_wachsend(p / p.rolling(1400, min_periods=1400).mean()) <= 0.20
A = (A1.astype(int) + A2.astype(int) + A3.astype(int)) >= 2

# ---- B Wende ----
c = ro("data/messdaten.db")
k = pd.read_sql("SELECT symbol, date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD'", c, parse_dates=["date"])
c.close()
K = k.pivot(index="date", columns="symbol", values="close").sort_index().asfreq("D")
s50 = K.rolling(50, min_periods=40).mean()
gueltig = s50.notna().sum(axis=1)
breite = ((K > s50) & s50.notna()).sum(axis=1) / gueltig.where(gueltig >= 50)
breite = breite.reindex(p.index)
sprung = (breite >= 0.80) & (breite.rolling(20, min_periods=15).min() <= 0.30)
B1 = sprung.astype(float).rolling(60, min_periods=1).max().fillna(0) > 0
B1_da = breite.notna()
s200 = p.rolling(200, min_periods=200).mean()
B2 = (p > s200) & (s200 > s200.shift(20))
B3 = p.rolling(30).min() > p.shift(30).rolling(60).min()
B = B2 & B3 & (B1 | ~B1_da)

# ---- echte Boeden (K-4): >= 45 % unter dem Hoch, 180 T kein tieferes Tief, +50 % in 365 T ----
ende = p.index[-1]
ereignisse = []
for t in p.index[p.index >= "2017-01-01"]:
    if dd[t] > -0.45:
        continue
    vor = p[t - pd.Timedelta(days=180):t]
    nach = p[t:t + pd.Timedelta(days=180)]
    if p[t] > vor.min() or p[t] > nach.min():
        continue
    hoch = p[t:t + pd.Timedelta(days=365)].max()
    vollst = t + pd.Timedelta(days=180) <= ende
    if hoch / p[t] >= 1.5 or not vollst:
        if not ereignisse or (t - ereignisse[-1][0]).days > 180:
            ereignisse.append((t, vollst, hoch / p[t] - 1))
print("Spot K-0 Klima und Bodenbildung - Messplan Fassung 1 (Voranalyse_Spot §8.6), BTC, Daten bis %s" % ende.date())
print()
print("ECHTE BOEDEN (K-4, aus CoinMetrics-Tagesschluss):")
for t, vollst, hoch in ereignisse:
    print("  %s  Kurs %8.0f  Drawdown %+.0f %%  danach hoechstens %+.0f %% in 365 T%s" % (
        t.date(), p[t], 100 * dd[t], 100 * hoch, "" if vollst else "  [VORLAEUFIG: 180-Tage-Bedingung erst %s pruefbar]" % (t + pd.Timedelta(days=180)).date()))
print()

# ---- H1 Zone ----
print("H1 Zone - A an in +-30 Tagen um das Tief (gestuetzt: >= 3 von 4 Bestimmungszyklen):")
h1 = []
for t, vollst, _h in ereignisse:
    w = A[t - pd.Timedelta(days=30):t + pd.Timedelta(days=30)]
    an = bool(w.any())
    if t.year <= 2022:
        h1.append(an)
    print("  %s  A an: %s  (A1 MVRV %s · A2 Drawdown %s · A3 200-Wochen %s; MVRV am Tief %.2f)" % (
        t.date(), "JA" if an else "nein", "ja" if A1[t - pd.Timedelta(days=30):t + pd.Timedelta(days=30)].any() else "nein",
        "ja" if A2[t - pd.Timedelta(days=30):t + pd.Timedelta(days=30)].any() else "nein",
        "ja" if A3[t - pd.Timedelta(days=30):t + pd.Timedelta(days=30)].any() else "nein", mvrv[t]))
print("  -> Bestimmungszyklen %d von %d: %s" % (sum(h1), len(h1), "GESTUETZT" if sum(h1) >= 3 else "nicht gestuetzt"))
print()

# ---- H2 Wende ----
print("H2 Wende - B schaltet binnen 120 T nach dem Tief ein (gestuetzt: >= 3 von 4); Verzoegerung und verpasster Anstieg:")
h2 = []
for t, vollst, _h in ereignisse:
    w = B[t:t + pd.Timedelta(days=120)]
    erst = w[w].index.min() if w.any() else None
    if t.year <= 2022:
        h2.append(erst is not None)
    if erst is not None:
        print("  %s  B an am %s: nach %3d Tagen, Kurs %+.0f %% ueber dem Tief%s" % (
            t.date(), erst.date(), (erst - t).days, 100 * (p[erst] / p[t] - 1), "" if B1_da[erst] else "  (ohne Breite: vor 2020)"))
    else:
        print("  %s  B NICHT binnen 120 T" % t.date())
print("  -> Bestimmungszyklen %d von %d: %s" % (sum(h2), len(h2), "GESTUETZT" if sum(h2) >= 3 else "nicht gestuetzt"))
print()

# ---- H3 Fehlalarm ----
print("H3 Fehlalarm - Anteil der B-Einschaltungen mit einem Tief 20 % unter dem Einschaltkurs binnen 180 T (gestuetzt: <= 1/3):")
ein = [d for d in B.index[B & (B.rolling(11).sum() == 1)] if d >= pd.Timestamp("2017-08-01")]
fa, offen = [], []
for d in ein:
    if d + pd.Timedelta(days=180) > ende:
        offen.append(d)
        continue
    tief = p[d + pd.Timedelta(days=1):d + pd.Timedelta(days=180)].min()
    fa.append((d, tief < 0.8 * p[d], tief / p[d] - 1))
for d, f, x in fa:
    print("  %s  %s  (tiefstes binnen 180 T %+.0f %%)" % (d.date(), "FEHLALARM" if f else "ok", 100 * x))
n_fa = sum(1 for _d, f, _x in fa if f)
print("  -> %d von %d Einschaltungen Fehlalarm (%.0f %%), %d noch offen (%s): %s" % (
    n_fa, len(fa), 100 * n_fa / max(len(fa), 1), len(offen), ", ".join(str(d.date()) for d in offen) or "-",
    "GESTUETZT" if len(fa) and n_fa / len(fa) <= 1 / 3 else "nicht gestuetzt"))
print()

# ---- H4 Klima traegt ----
print("H4 Klima - 180-Tage-Folgeertrag an B-Tagen gegen alle Tage, je Zyklus [Tief -365 T, +365 T] (gestuetzt: >= 3 von 4):")
f180 = p.shift(-180) / p - 1
h4, auskunft = [], []


def vergleich(fw, zw):
    diff = fw[zw].mean() - fw.mean()
    null = []
    for _ in range(200):
        zv = np.roll(zw.values, int(RNG.integers(30, len(zw) - 30)))
        null.append(fw.values[zv].mean() - fw.mean())
    return diff, float(np.mean(np.array(null) < diff))



for t, vollst, _h in ereignisse:
    w = slice(t - pd.Timedelta(days=365), t + pd.Timedelta(days=365))
    fw, bw = f180[w], B[w]
    ok = fw.notna()
    fw, bw = fw[ok], bw[ok]
    if bw.sum() < 10:
        print("  %s  zu wenige B-Tage mit 180-Tage-Ertrag (%d)" % (t.date(), int(bw.sum())))
        continue
    diff, rang = vergleich(fw, bw)
    if t.year <= 2022:
        h4.append(diff > 0)
    nach_tief = int(bw[bw.index > t].sum())
    print("  %s  B-Tage %3d (davon nach dem Tief %3d): Folgeertrag %+.0f %% gegen alle Tage %+.0f %% (Unterschied %+.0f Pp) · Nullwelt-Rang %.2f (Auskunft)%s" % (
        t.date(), int(bw.sum()), nach_tief, 100 * fw[bw].mean(), 100 * fw.mean(), 100 * diff, rang,
        "" if vollst else "  [VORLAEUFIG: 180-Tage-Ertrag reicht nur bis %s - die Wende nach dem Tief ist noch nicht messbar]" % (ende - pd.Timedelta(days=180)).date()))
    aw = A[w][ok]
    if aw.sum() >= 10:
        da, ra = vergleich(fw, aw)
        auskunft.append("  %s  A-Tage %3d: Folgeertrag %+.0f %% gegen alle Tage %+.0f %% (Unterschied %+.0f Pp) · Nullwelt-Rang %.2f" % (
            t.date(), int(aw.sum()), 100 * fw[aw].mean(), 100 * fw.mean(), 100 * da, ra))
print("  -> Bestimmungszyklen %d von %d positiv: %s" % (sum(h4), len(h4), "GESTUETZT" if sum(h4) >= 3 else "nicht gestuetzt"))
print()
print("AUSKUNFT (KEINE Hypothese der Fassung 1, Gegenrichtung nach §8.6): derselbe Vergleich fuer A-Tage (Zone)")
for z in auskunft:
    print(z)
print()

# ---- Klima heute (Fakt) ----
d = p.index[-1]
mp = pct_wachsend(mvrv)
klima = ("Wende bestaetigt" if B[d] else "Bodenbildung laeuft" if A[d] and (B2[d] or B3[d]) else "Kapitulation" if A[d]
         else "ueberhitzt" if mp[d] >= 0.90 else "Aufwaertstrend" if B2[d] else "neutral / Abwaertstrend")
print("KLIMA HEUTE (%s, Fakt): %s · A1 %s A2 %s A3 %s · B1 %s B2 %s B3 %s · MVRV %.2f (Perzentil %.0f %%) · Breite ueber 50 T %s" % (
    d.date(), klima, *["an" if x[d] else "aus" for x in (A1, A2, A3, B1, B2, B3)], mvrv[d], 100 * mp[d],
    "%.0f %%" % (100 * breite[d]) if not np.isnan(breite[d]) else "- (messdaten.db endet %s, B1 aus dem 60-Tage-Nachlauf)" % breite.dropna().index[-1].date()))
erst_b = B[B & (B.index >= "2026-06-01")].index.min()
print("  B (Wende) an seit: %s" % (erst_b.date() if pd.notna(erst_b) else "-"))
