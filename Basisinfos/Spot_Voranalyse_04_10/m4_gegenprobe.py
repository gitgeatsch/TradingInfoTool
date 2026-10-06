"""Gegenprobe Fassung 4 (python Basisinfos/Spot_Voranalyse_04_10/m4_gegenprobe.py) - eigener Rechenweg direkt aus SQL, nur lesend.

  G1 M1/M2: vier Monatsportfolios (Rang, Auswahl, Ertrag) mit eigener Schleife; Klassen aus A.klassen (dieselbe Zuordnung, nicht Teil der Probe)
  G2 M3: sechs Trend-Handel mit eigener Schleife (Verhaeltnis Coin/BTC, 50-T-Schnitt, 28-T-Ertrag, Ausstieg)
"""
import math, os, random, sqlite3, sys
from datetime import date, timedelta
import numpy as np, pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, "Basisinfos/Spot_Voranalyse_04_10")
import m4_messung as M  # noqa: E402
A = M.A
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
_cache = {}


def kurse(s):
    if s not in _cache:
        _cache[s] = dict(c.execute("SELECT date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol=?", (s,)).fetchall())
    return _cache[s]


def tag(d, k):
    return (d + timedelta(days=k)).isoformat()


def halt(s, d1, n):
    """Kauf Schluss d1, Verkauf Schluss d1+n oder am letzten Kurs davor (eingestellt)."""
    p, b = kurse(s), kurse("BTC")
    if tag(d1, 0) not in p:
        return None
    last = 0
    for k in range(1, n + 1):
        if tag(d1, k) not in p or p[tag(d1, k)] is None:
            break
        last = k
    if last == 0:
        return None
    cc, bb = p[tag(d1, last)] / p[tag(d1, 0)], b[tag(d1, last)] / b[tag(d1, 0)]
    return cc * (1 - .0125) / 1.0125 / (bb * (1 - .004) / 1.004) - 1


gleich = n = 0
for t, kl, rueck in ((pd.Timestamp("2022-03-01"), "H", 28), (pd.Timestamp("2023-07-01"), "M", 84), (pd.Timestamp("2025-02-01"), "S", 28), (pd.Timestamp("2025-11-01"), "H", 84)):
    d = t.date()
    kand = []
    for s, k in A.klassen(t)[0].items():
        if k != kl:
            continue
        p = kurse(s)
        if tag(d, 0) not in p or tag(d, -rueck) not in p or p[tag(d, 0)] is None or p[tag(d, -rueck)] is None:
            continue
        h = halt(s, d + timedelta(days=1), 28)
        if h is None:
            continue
        rel = p[tag(d, 0)] / p[tag(d, -rueck)] / (kurse("BTC")[tag(d, 0)] / kurse("BTC")[tag(d, -rueck)])
        kand.append((rel, h, s))
    kand.sort(key=lambda z: -z[0])
    k = max(2, math.ceil(0.2 * len(kand)))
    eigen = float(np.mean([z[1] for z in kand[:k]]))
    mess = [r for r in M.querschnitt(kl, rueck, 28, [t])][0]["net"]
    ok = abs(eigen - mess) < 1e-9; gleich += ok; n += 1
    print("G1 %s %s Rueckblick %2d T · %d Kandidaten, Kauf %s | Messung %+.4f  Gegenprobe %+.4f  %s" % (
        d, kl, rueck, len(kand), ",".join(z[2] for z in kand[:k]), mess, eigen, "gleich" if ok else "ABWEICHUNG"))

D = M.m3_ereignisse()
random.seed(10)
for r in random.sample(list(D.itertuples()), 6):
    s, t = r.sym, r.t
    p, b = kurse(s), kurse("BTC")
    d0 = t.date()
    def ratio(d):
        x = p.get(d.isoformat()); y = b.get(d.isoformat())
        return None if x is None or y is None else x / y
    def schnitt50(d):
        w = [ratio(d - timedelta(days=k)) for k in range(50)]
        return None if any(v is None for v in w) else sum(w) / 50
    sig = ratio(d0) > schnitt50(d0) and ratio(d0) / ratio(d0 - timedelta(days=28)) - 1 > 0
    d1 = d0 + timedelta(days=1); verkauf = None
    for k in range(0, 366):
        dk = d1 + timedelta(days=k)
        if ratio(dk) is None:
            break
        m50 = schnitt50(dk)
        if m50 is not None and ratio(dk) < m50:
            verkauf = min(k + 1, 365); break
    if verkauf is None or ratio(d1 + timedelta(days=verkauf)) is None:
        letzte = max(k for k in range(0, 366) if ratio(d1 + timedelta(days=k)) is not None and all(ratio(d1 + timedelta(days=j)) is not None for j in range(k + 1)))
        verkauf = letzte if verkauf is None else min(verkauf, letzte)
    cc, bb = p[tag(d1, verkauf)] / p[tag(d1, 0)], b[tag(d1, verkauf)] / b[tag(d1, 0)]
    eigen = cc * (1 - .0125) / 1.0125 / (bb * (1 - .004) / 1.004) - 1
    ok = abs(eigen - r.vorteil) < 1e-9 and sig; gleich += ok; n += 1
    print("G2 %s %-9s %s Signal %s · Verkauf nach %3d T (Messung %3d) | Messung %+.4f  Gegenprobe %+.4f  %s" % (
        d0, s, r.kl, "ja" if sig else "NEIN", verkauf, r.tage, r.vorteil, eigen, "gleich" if ok else "ABWEICHUNG"))
print("\n%d von %d gleich" % (gleich, n))
