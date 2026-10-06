"""Gegenprobe S3 Stufe 1 (python Basisinfos/Spot_Voranalyse_04_10/s3_gegenprobe.py): Klasse H am 01.03.2024 direkt aus SQL bestimmt
(90-T-Umsatz vor dem Tag, Top 30 an drei Monatsersten, >= 730 T Kurs) und ihr 180-T-Korb gegen BTC, verglichen mit s3_stufe1."""
import os, sqlite3, statistics
from datetime import date, timedelta
import pandas as pd
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
Q = " FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD'"
SONDER = {"AEUR", "AUD", "EUR", "EURI", "GBP", "PAXG", "WBTC", "WBETH", "BNSOL", "BFUSD", "BUSD", "FDUSD", "PAX", "TUSD", "USD1", "USDC", "USDP", "USDSOLD", "XUSD", "BTC", "ETH", "SOL"}
alle = [r[0] for r in c.execute("SELECT DISTINCT symbol" + Q)]
def stabil(s):
    rr = [r[0] for r in c.execute("SELECT close" + Q + " AND symbol=? ORDER BY date", (s,))]
    ch = [abs(rr[i] / rr[i - 1] - 1) for i in range(1, len(rr)) if rr[i - 1]]
    return bool(ch) and statistics.median(ch) < 0.002
univ = [s for s in alle if s not in SONDER and not stabil(s)]
def top30(m):
    da = {r[0] for r in c.execute("SELECT symbol" + Q + " AND date=?", (m.isoformat(),))}
    # dieselbe Regel wie s3_stufe1 (rolling 90, min_periods 30): ein Coin wird erst ab 30 Tagen Umsatz gerankt
    v = c.execute("SELECT symbol, AVG(close*volume), COUNT(close*volume)" + Q + " AND date BETWEEN ? AND ? GROUP BY symbol", ((m - timedelta(days=90)).isoformat(), (m - timedelta(days=1)).isoformat())).fetchall()
    v = sorted([(s, x) for s, x, n in v if s in univ and s in da and x is not None and n >= 30], key=lambda z: -z[1])
    return {s for s, _ in v[:30]}
m = date(2024, 3, 1)
kand = top30(m) & top30(date(2024, 2, 1)) & top30(date(2024, 1, 1))
erst = {s: c.execute("SELECT MIN(date)" + Q + " AND symbol=?", (s,)).fetchone()[0] for s in kand}
H = sorted(s for s in kand if (m - date.fromisoformat(erst[s])).days >= 730)
te = m + timedelta(days=180)
def kurs_bis(s, d):
    return c.execute("SELECT close" + Q + " AND symbol=? AND date<=? ORDER BY date DESC LIMIT 1", (s, d.isoformat())).fetchone()[0]
b = kurs_bis("BTC", te) / kurs_bis("BTC", m)
r = [kurs_bis(s, te) / kurs_bis(s, m) for s in H]
print("Gegenprobe H am %s: %d Coins %s" % (m, len(H), ",".join(H)))
print("Gegenprobe Korb 180 T gegen BTC: %+.4f" % (sum(r) / len(r) / b - 1))
Z = pd.read_pickle(os.path.join(os.environ.get("TEMP", "."), "s3_stufe1_z.pkl"))
x = Z[(Z["start"] == pd.Timestamp(m)) & (Z["h"] == 180) & (Z["klasse"] == "H")]
print("s3_stufe1  H am %s: %d Coins %s" % (m, len(x), ",".join(sorted(x["sym"]))))
print("s3_stufe1  Korb 180 T gegen BTC: %+.4f" % (x["r"].mean() / x["btc"].iloc[0] - 1))
