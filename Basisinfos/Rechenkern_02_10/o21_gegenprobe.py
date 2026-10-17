"""O21 GEGENPROBE (17.10.2026): Selbsttest der Befund-Regel - wie oft sagt der Messstand 'UNTER/ueber der Messung', wenn der Betrieb
GENAU wie die Messung laeuft? Zweiter Weg: Tage aus der Referenz 2025-26 ziehen (mit Zuruecklegen), Kennzahl und Befund wie im Modul.
Soll: Fehlalarm hoechstens 5 % (Befund auf dem 99-%-Band, MS.NIVEAU; mit 95 % lag er bei 10 T 12,5 %, Selbsttest 17.10.). Nur lesend, kein Netz.

    python Basisinfos/Rechenkern_02_10/o21_gegenprobe.py
"""
import os
import sqlite3
import sys
from datetime import datetime

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import agent.regel0_messstand as MS  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
B0 = datetime(2020, 1, 1)
E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
E = E[E.jahr >= 2025]
kz = {}
for datei in MS.KURSE:
    c = sqlite3.connect("file:data/%s?mode=ro" % datei, uri=True)
    for sym in E.symbol.unique():
        if sym not in kz:
            r = dict(c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol=?", (sym,)).fetchall())
            if r:
                kz[sym] = r
    c.close()
zeilen = []
for r in E.itertuples():
    a = (B0 + pd.Timedelta(hours=int(r.stunde))).strftime("%Y-%m-%d %H:%M")
    b = (B0 + pd.Timedelta(hours=int(r.stunde) + 24)).strftime("%Y-%m-%d %H:%M")
    if a in kz[r.symbol] and b in kz[r.symbol]:
        zeilen.append((int(r.stunde) // 24, kz[r.symbol][b] / kz[r.symbol][a] - 1, 0))
D = pd.DataFrame(zeilen, columns=["tag", "e24", "q"])
wahr = D.e24.mean()
print("O21 GEGENPROBE · Referenz %d Einstiege an %d Tagen, Mittel %+.3f %% (MS.REF_MITTEL %+.3f %%)" % (len(D), D.tag.nunique(), 100 * wahr, 100 * MS.REF_MITTEL))
gruppen = [g for _, g in D.groupby("tag")]
rng = np.random.default_rng(21)
ok = True
for N in (10, 12, 30, 90, 180):
    alarm = 0
    halb = []
    for _ in range(1000):
        ix = rng.integers(0, len(gruppen), N)
        rows = []
        for j, i in enumerate(ix):
            g = gruppen[i]
            rows += [("t%03d" % j, e, q) for e, q in zip(g.e24, g.q)]
        k = MS._kennzahl(rows)
        halb.append(k["halb"])
        alarm += int(not (k["mittel"] - k["halb"] <= wahr <= k["mittel"] + k["halb"]))
    q = alarm / 1000
    ok &= q <= 0.06
    print("   %3d Tage: Fehlalarm %.1f %% (Soll <= 5 %%) · Halbbreite im Mittel %.2f Pp" % (N, 100 * q, 100 * np.mean(halb)))
print("%s" % ("GLEICH (Fehlalarm im Rahmen)" if ok else "ABWEICHUNG (Fehlalarm zu hoch)"))
sys.exit(0 if ok else 1)
