"""Konzeptpruefung Spot (11.10.2026) - GEGENPROBE mit eigenem Rechenweg (nur lesend, Desktop).

    python Basisinfos/Spot_Voranalyse_04_10/kp_gegenprobe.py <NB-Sicherung tradinginfotool.db>

  G1 Dollar-Ertrag der 32 Upbit-Listings direkt aus SQL (eigene Zeitrechnung: Meldezeit + 4 h, Schluss der letzten Stunde <= +4 h + 168 h)
  G2 eingefrorene Uebernahmen: je Symbol mit Status 'uebernommen' das letzte Datum per SQL - alle vor dem Stichtag 01.09.2026?
  G3 CAT = 1000CAT: Kursverhaeltnis 1000CAT / CAT an gemeinsamen Tagen der Messbasis ~ 1000 (dasselbe Asset, nur das Buendel)
  G4 die 5 echt fehlenden: weder binance_mess noch uebernommen in der Messbasis; Laenge der Produktionsreihe an der NB-Sicherung
     (XDC >= 400 = nach der Uebernahmeregel aufnehmbar, die uebrigen < 400)
"""
import os
import sqlite3
import sys
from datetime import datetime, timedelta

import pandas as pd

os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
NB = sys.argv[1]
ERG = []


def pruefe(k, ok, text):
    ERG.append(bool(ok))
    print("%-3s %-10s %s" % (k, "gleich" if ok else "ABWEICHUNG", text))


# G1
D = pd.read_csv("data/_spot/c2_ereignisse.csv", sep=";", parse_dates=["zeit"])
Du = D[(D.art == "C2-b Upbit-Listing") & (D.zeit >= "2024-01-01")]
cs = [sqlite3.connect("file:data/%s?mode=ro" % f, uri=True) for f in ("stundenkurse.db", "stundenkurse_alle.db")]


def kurs(sym, von, bis):
    for c in cs:
        r = c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=? AND stunde >= ? AND stunde <= ? AND close > 0 ORDER BY stunde",
                      (sym, von, bis)).fetchall()
        if r:
            return r
    return []


werte = []
for r in Du.itertuples():
    t0 = r.zeit.to_pydatetime().replace(minute=0, second=0, microsecond=0, tzinfo=None)
    ein = t0 + timedelta(hours=4)
    aus = ein + timedelta(hours=168)
    f = "%Y-%m-%d %H:%M:%S"
    z = kurs(r.sym, ein.strftime(f)[:13], aus.strftime(f))
    a = [x for x in z if x[0][:13] == ein.strftime(f)[:13]]
    if a and z:
        werte.append((r.zeit, z[-1][1] / a[0][1] - 1))
W = pd.DataFrame(werte, columns=["zeit", "usd"])
korb = W.groupby(W.zeit.dt.to_period("M")).usd.mean().mean()
pruefe("G1", len(W) == 32 and abs(korb - (-0.0851)) < 0.005 and int((W.usd > 0).sum()) == 7,
       "%d Ereignisse, Dollar-Korb %+.2f %% (Skript -8,51 %%), steigt %d (Skript 7)" % (len(W), 100 * korb, int((W.usd > 0).sum())))

# G2
md = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
ue = md.execute("SELECT s.symbol, MAX(p.date) FROM messreihen_status s JOIN price_history_ohlc p ON p.symbol = s.symbol AND p.currency='USD' "
                "WHERE s.status='uebernommen' GROUP BY s.symbol").fetchall()
pruefe("G2", len(ue) == 10 and all(d < "2026-09-01" for _, d in ue), "uebernommen %d, letztes Datum: %s" % (len(ue), sorted({d[:10] for _, d in ue})))

# G3
q = md.execute("SELECT a.close / b.close FROM price_history_ohlc a JOIN price_history_ohlc b ON a.date = b.date AND b.symbol='CAT' AND b.currency='USD' "
               "WHERE a.symbol='1000CAT' AND a.currency='USD'").fetchall()
med = sorted(x[0] for x in q)[len(q) // 2] if q else None
pruefe("G3", med and 900 < med < 1100, "1000CAT/CAT an %d gemeinsamen Tagen, Median %.0f" % (len(q), med or 0))

# G4
nb = sqlite3.connect("file:%s?mode=ro" % NB.replace("\\", "/"), uri=True)
z = {}
for s in ("ASTER", "CANTON", "MON", "VSN", "XDC"):
    n_md = md.execute("SELECT COUNT(*) FROM price_history_ohlc WHERE symbol IN (?, 'CC') AND currency='USD'", (s,)).fetchone()[0]
    n_nb = nb.execute("SELECT COUNT(DISTINCT date) FROM price_history_ohlc WHERE symbol=? AND currency='USD' AND COALESCE(quelle,'') != 'rekonstruiert'",
                      (s,)).fetchone()[0]
    z[s] = (n_md, n_nb)
pruefe("G4", all(a == 0 for a, _ in z.values()) and z["XDC"][1] >= 400 and all(b < 400 for s, (_, b) in z.items() if s != "XDC"),
       "Messbasis/NB-Tage: %s" % z)
print("\n%d von %d gleich" % (sum(ERG), len(ERG)))
