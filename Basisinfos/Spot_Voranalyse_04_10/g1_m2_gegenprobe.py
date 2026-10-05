"""Gegenprobe G1-M2 (python Basisinfos/Spot_Voranalyse_04_10/g1_m2_gegenprobe.py): zwei Starts unabhaengig nachgerechnet (reine SQL-Abfrage
je Coin, ohne Pivot) und die groessten Ausreisser in E1 auf Sprunge pruefen (Token-Umstellungen, Befund Datenfehler messdaten)."""
import os, sqlite3, statistics
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
def kurs(s, t):
    r = c.execute("SELECT close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol=? AND date=?", (s, t)).fetchone()
    return r[0] if r else None
def letzter_bis(s, t):
    r = c.execute("SELECT close, date FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol=? AND date<=? ORDER BY date DESC LIMIT 1", (s, t)).fetchone()
    return r
stable = {"BFUSD", "BUSD", "EURI", "FDUSD", "PAX", "TUSD", "USD1", "USDC", "USDP", "USDSOLD", "XUSD"}
for start, ende in (("2022-01-01", "2023-01-01"), ("2024-02-01", "2025-01-31")):
    syms = [r[0] for r in c.execute("SELECT symbol FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND date=?", (start,))]
    b = kurs("BTC", ende) / kurs("BTC", start)
    rel = []
    for s in syms:
        if s == "BTC" or s in stable:
            continue
        pe = letzter_bis(s, ende)
        rel.append(pe[0] / kurs(s, start) / b - 1)
    print("Start %s, 365 T: %d Coins, Median %+.1f %%, vor BTC %.0f %%" % (start, len(rel), 100 * statistics.median(rel), 100 * sum(x > 0 for x in rel) / len(rel)))
# Ausreisser E1, 730 T: hoechste Endwerte und groesster Tagessprung in der Reihe
print("Groesste Gewinner E1 (Start 2019-01 bis 2020-12, 730 T) - Pruefung auf Kurs-Spruenge (Tageswechsel > x5 oder < /5):")
best = {}
for (start,) in c.execute("SELECT DISTINCT date FROM price_history_ohlc WHERE symbol='BTC' AND assetklasse='krypto' AND currency='USD' AND date BETWEEN '2019-01-01' AND '2020-12-31' AND substr(date,9,2)='01'").fetchall():
    pass
import pandas as pd
k = pd.read_sql("SELECT symbol, date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND date BETWEEN '2019-01-01' AND '2022-12-31'", c, parse_dates=["date"])
K = k.pivot(index="date", columns="symbol", values="close").sort_index()
r = {}
for t in pd.date_range("2019-01-01", "2020-12-01", freq="MS"):
    te = t + pd.Timedelta(days=730)
    if t not in K.index: continue
    for s in K.columns[K.loc[t].notna()]:
        if s in stable or s == "BTC": continue
        pe = K.loc[t:te, s].ffill().iloc[-1]
        r[s] = max(r.get(s, 0), pe / K.at[t, s])
top = sorted(r.items(), key=lambda x: -x[1])[:12]
for s, v in top:
    tr = K[s].pct_change(fill_method=None)
    print("  %-8s bis x%.0f   groesster Tagesanstieg %+.0f %%, groesster Tagesfall %+.0f %%" % (s, v, 100 * tr.max(), 100 * tr.min()))
# Abgleich mit dem Hauptskript (gleiche Starts) und Robustheit des Korbs in E1 ohne die Ausreisser mit Verdacht auf Token-Umstellung
src = open("Basisinfos/Spot_Voranalyse_04_10/g1_m2_grundrate_altcoins.py", encoding="utf-8").read().split("def epoche")[0]
import contextlib, io
g = {"__file__": os.path.abspath("Basisinfos/Spot_Voranalyse_04_10/g1_m2_grundrate_altcoins.py")}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "m2", "exec"), g)
Z = g["Z"]
for st in ("2022-01-01", "2024-02-01"):
    x = Z[(Z["start"] == pd.Timestamp(st)) & (Z["h"] == 365)]
    print("Hauptskript Start %s, 365 T: %d Coins, Median %+.1f %%, vor BTC %.0f %%" % (st, len(x), 100 * x["rel"].median(), 100 * (x["rel"] > 0).mean()))
e1 = Z[(Z["start"] <= "2020-12-31")]
for h in (365, 730):
    for name, sel in (("alle", e1), ("ohne COCOS, DREP, NPXS", e1[~e1["sym"].isin({"COCOS", "DREP", "NPXS"})]),
                      ("Korb mit Median statt Mittel", None)):
        x = (e1 if sel is None else sel)
        x = x[x["h"] == h]
        if sel is None:
            k = x.groupby("start").apply(lambda q: q["r"].median() / q["btc"].iloc[0] - 1, include_groups=False).median()
        else:
            k = x.groupby("start").apply(lambda q: q["r"].mean() / q["btc"].iloc[0] - 1, include_groups=False).median()
        print("E1 %d T, %-30s Korb-Median %+.1f %%" % (h, name, 100 * k))
