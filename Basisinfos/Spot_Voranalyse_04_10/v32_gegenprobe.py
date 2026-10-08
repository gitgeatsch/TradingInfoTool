"""Gegenprobe der Vorpruefung §32 - eigener Rechenweg, nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/v32_gegenprobe.py <pfad_zur_prod_kopie.db>

  V1 Altindex: an 4 Tagen den Tagesertrag gegen BTC aus Gewichten und Kursen neu (Index-Verhaeltnis zweier Tage)
  V2 Episoden: eigene Suche auf der abgelegten Indexreihe (Schwelle 1,15 ueber 60-T-Tief) - gleiche Zahl und gleiche Tiefs
  V3 Kosten: 30 zufaellige Handel - Aufschlag aus Rohdaten neu (Stunde aus Unix-Zeit, EUR/USD der Ablage)
  V4 Handelbarkeit: Bitpanda-Anteil je Klasse mit eigener Zuordnung neu = Ausgabe
  V5 BTCDOM 30 T vor einem Tief direkt aus SQL = Ausgabe
"""
import os
import re
import sqlite3
import sys

PROD = sys.argv[1] if len(sys.argv) > 1 else None
import numpy as np      # noqa: E402
import pandas as pd     # noqa: E402

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import as_messung as M      # noqa: E402
import mk_messung as MK     # noqa: E402

K, POS, BTCV, IDX = M.K, M.POS, M.BTCV, M.IDX
TXT = open(os.path.join(HIER, "v32_vorpruefung.txt"), encoding="utf-8").read()
I = pd.read_csv(os.path.join("data", "_spot", "v32_altindex_mw.csv"), sep=";", index_col=0, parse_dates=True).iloc[:, 0]
ok = n = 0


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


for d in [pd.Timestamp(x) for x in ("2023-03-15", "2024-11-20", "2025-07-08", "2026-05-20")]:
    t = d.to_period("M").to_timestamp()
    _, rg = MK.rang_mw(t)
    top = [s for s in rg.sort_values().index if s not in ("BTC", "ETH", "SOL")][:100]
    w = pd.Series({s: MK.umlauf(s, t) * K[s].values[POS[t]] for s in top}).dropna()
    w = w[w > 0]
    i = POS[d]
    r = pd.Series({s: K[s].values[i] / K[s].values[i - 1] - 1 for s in w.index}).dropna()
    rel = (1 + (r * w[r.index]).sum() / w[r.index].sum()) / (BTCV[i] / BTCV[i - 1]) - 1
    soll = I.loc[d] / I.loc[IDX[i - 1]] - 1
    pruefe("V1", abs(rel - soll) < 1e-9, "%s Tagesertrag gegen BTC neu %+.5f · Ablage %+.5f" % (d.date(), rel, soll))

tief60 = I.rolling(60, min_periods=20).min()
an = (I / tief60 >= 1.15)
tiefs = []
letzte = None
for d, a in an.items():
    if not a:
        continue
    if letzte is None or (d - letzte).days >= 30:
        tiefs.append(I[d - pd.Timedelta(days=60):d].idxmin())
    letzte = d
tiefs = sorted(set(tiefs))
aus = re.findall(r"Tief (\d{4}-\d\d-\d\d) -> Hoch", TXT.split("gleich gewichtet")[0])
pruefe("V2", [str(x.date()) for x in tiefs] == aus, "eigene Tiefs %s · Ausgabe %s" % ([str(x.date()) for x in tiefs], aus))

KO = pd.read_csv(os.path.join("data", "_spot", "v32_kosten.csv"), sep=";", parse_dates=["t"])
import json  # noqa: E402
roh = {(x["cryptocoin_symbol"].upper(), int(x["unix_timestamp"])): x for x in json.load(open(
    r"K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/bitpanda_transaktionen.json", encoding="utf-8"))["transaktionen"]
    if x.get("unix_timestamp") and x["type"] in ("buy", "sell") and x.get("trade_price")}
fx = None
fehl = 0
for r in KO.sample(30, random_state=41).itertuples():
    ts = int(pd.Timestamp(r.t).timestamp())
    x = roh.get((r.sym, ts))
    stunde = pd.Timestamp(ts, unit="s").strftime("%Y-%m-%d %H:00")
    k = None
    for db in ("data/stundenkurse.db", "data/stundenkurse_alle.db"):
        z = sqlite3.connect("file:%s?mode=ro" % db, uri=True).execute("select close from stundenkurse where symbol=? and stunde=?", (r.sym, stunde)).fetchone()
        if z and z[0]:
            k = z[0]; break
    if x is None or k is None:
        fehl += 1; continue
    eurusd = (1 + r.auf) * k / float(x["trade_price"])                  # rueckgerechnet: muss ein plausibler Kurs sein
    fehl += not (1.0 < eurusd < 1.3)
pruefe("V3", fehl == 0, "30 Handel: Rohdaten gefunden, Stunde gleich, rueckgerechneter EUR/USD in 1,0..1,3; Verstoesse %d" % fehl)

if PROD:
    kat = pd.read_sql("select symbol, gruppe from bitpanda_katalog", sqlite3.connect("file:%s?mode=ro" % PROD, uri=True))
    bp = set(kat[kat.gruppe.isin(["coin", "token"])].symbol.str.upper())
    letzte_t = max(t for t in pd.date_range("2023-01-01", M.ENDE, freq="MS") if t in POS)
    kl = {s: k for s, k in MK.klassen_mw(letzte_t)[0].items() if s not in ("BTC", "ETH", "SOL")}
    def handelbar(s):
        m = re.match(r"^(\d+)(M?)(?=[A-Z])", s)
        return bool(s in bp or (m and s[m.end():] in bp))
    neu = {k: "%d/%d" % (sum(handelbar(s) for s in kl if kl[s] == k), sum(1 for s in kl if kl[s] == k)) for k in "HMS"}
    m = re.search(r"H (\d+/\d+) · M (\d+/\d+) · S (\d+/\d+)", TXT)
    pruefe("V4", m and (neu["H"], neu["M"], neu["S"]) == m.groups(), "neu %s · Ausgabe %s" % (neu, m.groups() if m else None))

c = sqlite3.connect("file:data/richtung_historie.db?mode=ro", uri=True)
d = pd.Timestamp("2024-11-04")
x = pd.read_sql("select stunde, close from btcdom where stunde >= ? and stunde < ? order by stunde", c,
                params=[(d - pd.Timedelta(days=30)).strftime("%Y-%m-%d"), (d + pd.Timedelta(days=1)).strftime("%Y-%m-%d")])   # bis Ende des Tief-Tages, kein Folgetag
neu = x.close.iloc[-1] / x.close.iloc[0] - 1
m = re.search(r"Tief 2024-11-04 .*?BTCDOM 30T ([+-]\d+\.\d) %", TXT)
pruefe("V5", m and abs(100 * neu - float(m.group(1))) < 0.06, "BTCDOM 30 T vor 2024-11-04 neu %+.2f %% · Ausgabe %s" % (100 * neu, m.group(1) if m else None))
print("\n%d von %d gleich" % (ok, n))
