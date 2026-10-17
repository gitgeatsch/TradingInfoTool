"""P62 GEGENPROBE (18.10.2026), zweiter Weg: bestand 2025-26, H24 / H72 / H168 / S8_168 brutto und Tief <= -20 % binnen 168 h mit eigener
Schleife ueber ein Stunden-Woerterbuch (nicht die Arrays aus p62). Muss den p62-Werten gleichen. Nur lesend.

    python Basisinfos/Rechenkern_02_10/p62_gegenprobe.py
"""
import os
import sqlite3
import sys
from datetime import datetime, timedelta

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
import csv  # noqa: E402

B0 = datetime(2020, 1, 1)
kz = {}
cons = [sqlite3.connect("file:data/%s?mode=ro" % d, uri=True) for d in ("stundenkurse.db", "stundenkurse_alle.db", "eingestellt_historie.db")]
E = [r for r in csv.DictReader(open("data/_vergleich/kern48jbz_einstiege_bestand.csv", encoding="utf-8"), delimiter=";") if int(r["jahr"]) >= 2025]
for sym in sorted({r["symbol"] for r in E}):
    d = {}
    for c in cons:
        for st, h, lo, cl in c.execute("SELECT stunde, high, low, close FROM stundenkurse WHERE symbol=?", (sym,)):
            d.setdefault(st, (h, lo, cl))
    kz[sym] = d
summe = {"H24": 0.0, "H72": 0.0, "H168": 0.0, "S8_168": 0.0}
n = tief = 0
for r in E:
    k = kz[r["symbol"]]
    t0 = B0 + timedelta(hours=int(r["stunde"]))
    z = [k.get((t0 + timedelta(hours=s)).strftime("%Y-%m-%d %H:%M")) for s in range(0, 169)]
    if any(x is None or x[0] is None or x[1] is None or x[2] is None for x in z):
        continue
    c0 = z[0][2]
    n += 1
    for name, h in (("H24", 24), ("H72", 72), ("H168", 168)):
        summe[name] += z[h][2] / c0 - 1
    stop = next((s for s in range(1, 169) if z[s][1] <= c0 * 0.92), None)
    summe["S8_168"] += -0.08 if stop else z[168][2] / c0 - 1
    tief += int(min(x[1] for x in z[1:169]) / c0 - 1 <= -0.20)
print("P62 GEGENPROBE bestand 2025-26: n %d · %s · Tief <= -20 %% binnen 168 h %.1f %%" % (
    n, " · ".join("%s %+.3f %%" % (k_, 100 * v / n) for k_, v in summe.items()), 100 * tief / n))
print("Soll aus p62: n 8401 · H24 +0.545 % · H72 -0.373 % · H168 -0.870 % · S8_168 -0.923 % · Tief 11.9 %")
