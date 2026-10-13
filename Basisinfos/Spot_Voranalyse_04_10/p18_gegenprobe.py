"""P18 GEGENPROBE (Spot §48) - die Zahlen der Voranalyse auf einem ZWEITEN Weg. Nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/p18_gegenprobe.py <Prod-Sicherung tradinginfotool.db>

  G1  Stichtage AUSSERHALB der Vormessung (2026-08-01, 2026-09-01, Fenster nicht abgeschlossen): Fuenftel ueber die Funktionen der MESSUNG
      (mk_messung.klassen_mw, as_messung.merkmale, wl_messung.wert, as_messung.pct_in_zelle) gegen den Nachbau p18_voranalyse.B4 - je Coin gleich?
  G2  Zuordnung Bestand -> Binance-Reihe (D5): Tagesschluss der Produktion (USD) gegen den Schluss der Messbasis am selben Tag; Faktor aus
      symbol_zuordnung.csv; Median-Verhaeltnis ausserhalb 0,97-1,03 = falsche Zuordnung
  G3  Teil 1 mit ANDERER Schnittlaenge (300 und 700 T statt 500): D3 + Fenster bleibt gleich der vollen Geschichte
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

PROD = os.path.abspath(sys.argv[1])
HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
sys.argv = ["x", PROD]
import p18_voranalyse as P  # noqa: E402

MK, M, W, D4 = P.MK, P.M, P.MK.W, P.D4
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-9s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


K, U = P.G["K"], P.G["U"]
ausschluss = set(P.G["SONDER"]) | {s for s in K.columns if s not in P.G["UNIV"]}
R = P.B4(K, U, ausschluss, MK.umlauf)

# G1
for t in (pd.Timestamp("2026-08-01"), pd.Timestamp("2026-09-01")):
    out, _, _ = MK.klassen_mw(t)
    D = pd.DataFrame([dict(t=t, sym=s, kl=k) for s, k in out.items() if not np.isnan(K[s].values[MK.POS[t]])])
    F = M.merkmale(D)
    Zl = W.Leicht(D)
    p = M.pct_in_zelle(Zl, W.wert(Zl, F, wahl=D4.OHNE_F9))
    q_mess = dict(zip(D.sym, D4.fuenftel(p)))
    z = R.fuenftel(t)
    q_nach = dict(zip(z.sym, z.q))
    gem = [s for s in q_mess if q_mess[s] == q_mess[s] or q_nach.get(s) == q_nach.get(s)]
    gl = sum((q_mess[s] == q_nach.get(s)) or (q_mess[s] != q_mess[s] and q_nach.get(s) != q_nach.get(s)) for s in gem)
    pruefe("G1", gl == len(gem) and set(q_mess) == set(q_nach), "%s Messfunktionen gegen Nachbau: %d von %d Coins gleiches Fuenftel · Mengen %s" % (
        t.date(), gl, len(gem), "gleich" if set(q_mess) == set(q_nach) else "VERSCHIEDEN"))

# G2
c = sqlite3.connect("file:%s?mode=ro" % PROD.replace("\\", "/"), uri=True)
import config as C  # noqa: E402
wl = {a.symbol: a for a in C.get_watchlist()}
zu = pd.read_csv("Basisinfos/symbol_zuordnung.csv", sep=";")
spot = {r.bitpanda: (r.binance, float(r.faktor)) for r in zu.itertuples() if r.markt == "spot"}
falsch, geprueft = [], []
for s, q, st in c.execute("SELECT symbol, quantity, staked_quantity FROM holdings"):
    a = wl.get(s)
    if not (float(q or 0) + float(st or 0) > 0 and a and a.assetklasse == "krypto" and not a.ist_cash_aequivalent and s not in P.KERN):
        continue
    b, f = spot.get(s, (s, 1.0))
    if b not in K.columns or K[b].loc["2026-09-01":].notna().sum() == 0:
        continue
    # ⚠️ KORREKTUR 13.10. (erster Lauf): price_cache haelt nur die letzten Tage - verglichen wurde dort ein Kurs vom 13.10. mit dem Schluss
    # vom 20.09. (AVAX 1,18, NEAR 1,20 - Kursbewegung, keine falsche Zuordnung). Jetzt: Tagesschluss der Produktion (price_history_ohlc,
    # USD) gegen den Schluss der Messbasis AM SELBEN TAG, Median des Verhaeltnisses ueber die letzten 60 gemeinsamen Tage
    d = pd.read_sql("SELECT date, close FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND COALESCE(quelle,'') != 'rekonstruiert'",
                    c, params=(s,), parse_dates=["date"])
    if d.empty:
        continue
    d["date"] = d.date.dt.normalize()
    pr = d.drop_duplicates("date", keep="last").set_index("date").close
    gm = pd.concat([pr * f, K[b]], axis=1, join="inner").dropna().iloc[-60:]
    if len(gm) < 20:
        continue
    v = float((gm.iloc[:, 0] / gm.iloc[:, 1]).median())
    geprueft.append("%s->%s %.3f" % (s, b, v))
    if not 0.97 <= v <= 1.03:
        falsch.append(s)
pruefe("G2", not falsch and len(geprueft) >= 15, "Zuordnung Bestand -> Binance (Kurs Prod / Schluss Messbasis): %d geprueft, falsch %s · %s" % (
    len(geprueft), falsch or "-", ", ".join(geprueft)))

# G3
X = R.X
for laenge in (300, 700):
    ab = n = 0
    for t in (pd.Timestamp("2026-05-01"), pd.Timestamp("2026-09-01")):
        RS = P.B4(K, U, ausschluss, MK.umlauf, stamm=P.stamm_bis(X, R.pos[t] - laenge))
        for s in R.klassen(t):
            a, b = R.merkmale(t, s), RS.merkmale(t, s)
            n += 1
            ab += not all((u == v) or (u != u and v != v) for u, v in zip(a, b))
    pruefe("G3", ab == 0, "D3 mit Schnitt t-%d: %d Coin-Stichtage, Abweichung %d" % (laenge, n, ab))
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
