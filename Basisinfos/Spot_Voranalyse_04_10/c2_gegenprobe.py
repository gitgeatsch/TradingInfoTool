"""Gegenprobe Messung C2 (Spot §38) - eigener Rechenweg, nur lesend.

    python Basisinfos/Spot_Voranalyse_04_10/c2_gegenprobe.py

  P1 Zuordnung: 20 Ereignisse - das Kuerzel steht im Titel (Futures: als XYZ/XYZUSDT vor 'Perpetual'; Upbit: in Klammern vor 신규 거래지원)
  P2 Ertrag gegen BTC an 30 Ereignissen direkt aus SQL (Stunde = Meldung abgerundet + 4 h, Ausstieg + 168 h; eingestellt -> letzter Kurs)
  P3 Korb je Art ab 2024 aus der Ablage neu = Ausgabe
  P4 'verpasst' (Stunde vor der Meldung bis Einstieg) an 10 Ereignissen neu
  P5 Klasse an 10 Ereignissen = mk_messung.klassen_mw des Monats
"""
import os
import re
import sqlite3
import sys

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HIER)
os.chdir(os.path.dirname(os.path.dirname(HIER)))
import mk_messung as MK     # noqa: E402

TXT = open(os.path.join(HIER, "c2_messung.txt"), encoding="utf-8").read()
D = pd.read_csv(os.path.join("data", "_spot", "c2_ereignisse.csv"), sep=";", parse_dates=["zeit"])
T0 = pd.Timestamp("2023-01-01")
ok = n = 0
C = [sqlite3.connect("file:%s?mode=ro" % db, uri=True) for db in ("data/stundenkurse.db", "data/stundenkurse_alle.db")]


def pruefe(name, gut, info):
    global ok, n
    n += 1; ok += bool(gut)
    print("%-3s %s  %s" % (name, "gleich" if gut else "ABWEICHUNG", info), flush=True)


def kurs(s, stunde):
    for c in C:
        z = c.execute("select close from stundenkurse where symbol=? and stunde=?", (s, stunde)).fetchone()
        if z and z[0]:
            return z[0]
    return None


def letzter(s, a, b):
    for c in C:
        z = c.execute("select close from stundenkurse where symbol=? and stunde between ? and ? and close is not null order by stunde desc limit 1", (s, a, b)).fetchone()
        if z:
            return z[0]
    return None


A = sqlite3.connect("file:data/_c2/ankuendigungen.db?mode=ro", uri=True)
titel = {}
for t, ms in A.execute("select titel, release_ms from binance"):
    titel.setdefault(pd.Timestamp(ms, unit="ms"), []).append(t)
for t, u in A.execute("select titel, utc from upbit"):
    titel.setdefault(pd.Timestamp(u), []).append(t)
fx = 0
for r in D.sample(20, random_state=51).itertuples():
    ts = titel.get(r.zeit, [])
    gut = False
    for t in ts:
        if r.art.startswith("C2-a"):
            vor = t.split("Perpetual")[0]
            gut |= bool(re.search(r"\b(1000|1000000|1M)?%s(USDT|USDC|BUSD)?\b" % re.escape(r.sym), vor))
        elif r.art.startswith("C2-b"):
            gut |= ("(%s)" % r.sym) in t.split("신규 거래지원")[0]
        else:
            gut |= ("(%s)" % r.sym) in t or ("(1000%s)" % r.sym) in t
    fx += not gut
pruefe("P1", fx == 0, "20 Ereignisse: Kuerzel im Titel der Meldung zur selben Zeit, Verstoesse %d" % fx)

fx = 0
for r in D.sample(30, random_state=52).itertuples():
    e = r.zeit.floor("h") + pd.Timedelta(hours=4)
    x = e + pd.Timedelta(hours=168)
    f = lambda t: t.strftime("%Y-%m-%d %H:00")
    k0, k1 = kurs(r.sym, f(e)), letzter(r.sym, f(e), f(x))
    b0, b1 = kurs("BTC", f(e)), kurs("BTC", f(x))
    neu = (k1 / k0) / (b1 / b0) - 1
    fx += abs(neu - r.ex) > 1e-9
pruefe("P2", fx == 0, "30 Ereignisse direkt aus SQL, Abweichungen %d" % fx)

for art in ("C2-a Futures-Start", "C2-b Upbit-Listing"):
    g = D[(D.art == art) & (D.zeit >= "2024-01-01")]
    k = g.groupby(g.zeit.dt.to_period("M")).ex.mean().mean()
    m = re.search(r"%s ab 2024: .*?Korb ([+-]\d+\.\d\d) Pp" % re.escape(art), TXT)
    pruefe("P3", m and abs(100 * k - float(m.group(1))) < 0.006, "%s Korb neu %+.3f · Ausgabe %s" % (art, 100 * k, m.group(1) if m else None))

fx = 0
for r in D[D.verpasst.notna()].sample(10, random_state=53).itertuples():
    e = r.zeit.floor("h") + pd.Timedelta(hours=4)
    v = r.zeit.floor("h") - pd.Timedelta(hours=1)
    f = lambda t: t.strftime("%Y-%m-%d %H:00")
    neu = (kurs(r.sym, f(e)) / kurs(r.sym, f(v))) / (kurs("BTC", f(e)) / kurs("BTC", f(v))) - 1
    fx += abs(neu - r.verpasst) > 1e-9
pruefe("P4", fx == 0, "verpasst an 10 Ereignissen, Abweichungen %d" % fx)

fx = 0
for r in D.sample(10, random_state=54).itertuples():
    m = r.zeit.to_period("M").to_timestamp()
    fx += MK.klassen_mw(m)[0].get(r.sym, "U") != r.kl
pruefe("P5", fx == 0, "Klasse an 10 Ereignissen, Abweichungen %d" % fx)
print("\n%d von %d gleich" % (ok, n))
