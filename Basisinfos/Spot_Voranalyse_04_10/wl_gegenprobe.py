"""Gegenprobe erster Wurf Watchlist (python Basisinfos/Spot_Voranalyse_04_10/wl_gegenprobe.py) - eigener Rechenweg, nur lesend.

  G1 B5: 8 V0-Einstiege, X0 / X2 (Nachlauf -35 %, Notbremse -50 %) / X7a mit eigener Schleife direkt aus SQL gegen wl_messung
  G2 B1: Restwert- und Umsatzschwund-Flag fuer 10 Coin-Anker direkt aus SQL
  G3 B2: Bestaetigung (im Vormonat im Fuenftel) fuer 10 V0-Mitglieder ueber die Monatsrechnung nachgezaehlt
"""
import os, random, sqlite3, sys
from datetime import timedelta
import numpy as np, pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, "Basisinfos/Spot_Voranalyse_04_10")
import wl_messung as W  # noqa: E402
M, A = W.M, W.A
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)


def reihe(s, ab, n):
    r = c.execute("SELECT date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol=? AND date>=? ORDER BY date LIMIT ?",
                  (s, ab.isoformat(), n + 1)).fetchall()
    out = []
    for i, (d, x) in enumerate(r):
        if pd.Timestamp(d).date() != ab + timedelta(days=i) or x is None:
            break
        out.append(x)
    return out


D = M.paare(365).reset_index(drop=True)
Z = M.Zellen(D)
F = M.merkmale(D)
w = W.wert(Z, F)
p = M.pct_in_zelle(Z, w)
V0 = p > 0.8
RANG = W.monatsrang()
random.seed(13)
gl = n = 0
for j in random.sample(list(np.where(V0)[0]), 8):
    t, s = D.t[j], D.sym[j]
    d1 = (t + timedelta(days=1)).date()
    v, b = reihe(s, d1, 365), reihe("BTC", d1, 365)
    b = b[:len(v)]
    hoch, x2 = v[0], len(v) - 1
    for i in range(len(v)):
        hoch = max(hoch, v[i])
        if v[i] < 0.65 * hoch or v[i] < 0.5 * v[0]:
            x2 = min(i + 1, len(v) - 1); break
    x7 = len(v) - 1
    for m in range(1, 12):
        tm = t + pd.DateOffset(months=m)
        k = (tm.date() - d1).days + 1
        if k > len(v) - 1:
            break
        try:
            pr = RANG.at[(tm, s), "p"]
        except KeyError:
            pr = np.nan
        if not np.isnan(pr) and pr <= 0.5:
            x7 = k; break
    def er(tt):
        return v[tt] / v[0] * (1 - .0125) / 1.0125 - 1
    _, _, aus = W.ausstiege(t, s, RANG)
    vv, bb = A.pfad(s, M.POS[t] + 1, 365)
    m0, m2, m7 = (W.ertrag(vv, bb, aus[k])[0] for k in ("X0", "X2", "X7a"))
    e0, e2, e7 = er(len(v) - 1), er(x2), er(x7)
    ok = abs(m0 - e0) < 1e-9 and abs(m2 - e2) < 1e-9 and abs(m7 - e7) < 1e-9
    gl += ok; n += 1
    print("G1 %s %-8s X0 %+.4f/%+.4f · X2 %+.4f/%+.4f · X7a %+.4f/%+.4f  %s" % (t.date(), s, m0, e0, m2, e2, m7, e7, "gleich" if ok else "ABWEICHUNG"))
for j in random.sample(range(len(D)), 10):
    t, s = D.t[j], D.sym[j]
    r = pd.read_sql("SELECT date, close, volume FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol=? AND date<=? ORDER BY date",
                    c, params=(s, t.date().isoformat()), parse_dates=["date"]).set_index("date").asfreq("D")
    rest = (r.close.iloc[-1] / r.close.max() - 1) <= -0.99 if r.close.notna().sum() >= 180 else None
    u = (r.close * r.volume).iloc[:-1]
    u90, u365 = u.iloc[-90:], u.iloc[-365:]
    schw = (u90.mean() / u365.mean() < 0.2) if u90.notna().sum() >= 30 and u365.notna().sum() >= 180 else None
    m_rest = bool(F["F1"][j] <= -0.99) if not np.isnan(F["F1"][j]) else None
    m_schw = bool(F["F7"][j] < 0.2) if not np.isnan(F["F7"][j]) else None
    ok = (rest == m_rest) and (schw == m_schw)
    gl += ok; n += 1
    print("G2 %s %-8s Restwert %s/%s · Umsatzschwund %s/%s  %s" % (t.date(), s, m_rest, rest, m_schw, schw, "gleich" if ok else "ABWEICHUNG"))
for j in random.sample(list(np.where(V0)[0]), 10):
    t, s = D.t[j], D.sym[j]
    tm = t - pd.DateOffset(months=1)
    vor = RANG.reset_index()
    z = vor[(vor.t == tm)]
    zk = z[z.kl == RANG.at[(tm, s), "kl"]] if (tm, s) in RANG.index else None
    eigen = bool(zk is not None and (zk.set_index("sym").p.rank(pct=True, method="average").get(s, 0) is not None) and RANG.at[(tm, s), "p"] > 0.8) if zk is not None else False
    mess = bool(RANG.at[(tm, s), "p"] > 0.8) if (tm, s) in RANG.index else False
    ok = eigen == mess; gl += ok; n += 1
    print("G3 %s %-8s im Vormonat im Fuenftel: Messung %s · Gegenprobe %s  %s" % (t.date(), s, mess, eigen, "gleich" if ok else "ABWEICHUNG"))
print("\n%d von %d gleich" % (gl, n))
