"""Gegenprobe S1 (python Basisinfos/Spot_Voranalyse_04_10/s1_gegenprobe.py): Korb-Rendite Januar 2021 und Altseason-Breite am 29.03.2021
direkt aus SQL nachgerechnet und gegen s1_messung verglichen."""
import os, sqlite3, statistics, sys
from datetime import date, timedelta
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
Q = "FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD'"
def kurs(s, d):
    r = c.execute("SELECT close " + Q + " AND symbol=? AND date=?", (s, d)).fetchone(); return r[0] if r else None
stabil = set()
for (s,) in c.execute("SELECT DISTINCT symbol " + Q):
    rr = [r[0] for r in c.execute("SELECT close " + Q + " AND symbol=? ORDER BY date", (s,))]
    ch = [abs(rr[i] / rr[i - 1] - 1) for i in range(1, len(rr)) if rr[i - 1]]
    if ch and statistics.median(ch) < 0.002: stabil.add(s)
def top50(m):
    v = c.execute("SELECT symbol, AVG(close*volume) " + Q + " AND date BETWEEN ? AND ? GROUP BY symbol", ((m - timedelta(days=30)).isoformat(), m.isoformat())).fetchall()
    v = [(s, x) for s, x in v if s not in stabil and s != "BTC" and x is not None]
    return [s for s, _ in sorted(v, key=lambda z: -z[1])[:50]]
top = top50(date(2021, 1, 1)); wert = 1.0
for i in range(31):
    d0, d1 = (date(2020, 12, 31) + timedelta(days=i)).isoformat(), (date(2021, 1, 1) + timedelta(days=i)).isoformat()
    rs = []
    for s in top:
        a, b = kurs(s, d0), kurs(s, d1)
        rs.append(b / a - 1 if a and b else 0.0)
    wert *= 1 + sum(rs) / len(rs)
print("Gegenprobe Korb-Rendite Januar 2021: %+.4f" % (wert - 1))
t, t90 = "2021-03-29", "2020-12-29"; top = top50(date(2021, 3, 1)); bt = kurs("BTC", t) / kurs("BTC", t90)
pa = [(kurs(s, t), kurs(s, t90)) for s in top]; pa = [a / b for a, b in pa if a and b]
print("Gegenprobe Breite am %s: %.3f (%d Coins mit beiden Kursen)" % (t, sum(x > bt for x in pa) / len(pa), len(pa)))
sys.path.insert(0, "Basisinfos/Spot_Voranalyse_04_10")
import s1_messung as S
d = S.baue()
k = d["korb"]; import pandas as pd
print("s1_messung  Korb-Rendite Januar 2021: %+.4f · Breite am %s: %.3f" % (k[pd.Timestamp("2021-01-31")] / k[pd.Timestamp("2020-12-31")] - 1, t, d["breite"][pd.Timestamp(t)]))
