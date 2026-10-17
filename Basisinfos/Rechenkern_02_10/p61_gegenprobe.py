"""P61 GEGENPROBE (17.10.2026) zur O21-Vorpruefung, zweiter Weg. Nur lesend, kein Netz.

  G1  die SCHLEIFEN-Rechnung aus Teil 2 (eigener Code, nicht E2.ergebnisse) auf der Referenz 2026: t_u / t_d / Q gleich der CSV?
  G2  Aussagekraft mit der geschlossenen, cluster-robusten Formel (Varianz des Mittels ueber Tagessummen) statt Bootstrap
"""
import os
import sqlite3
import sys
from datetime import datetime

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
B0 = datetime(2020, 1, 1)
E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv"), sep=";")
reihen = {}
for datei in ("stundenkurse.db", "stundenkurse_alle.db"):
    c = sqlite3.connect("file:data/%s?mode=ro" % datei, uri=True)
    for sym in sorted(E.symbol.unique()):
        if sym not in reihen:
            rows = c.execute("SELECT stunde, high, low, close FROM stundenkurse WHERE symbol=? ORDER BY stunde", (sym,)).fetchall()
            if rows:
                reihen[sym] = {int((datetime.strptime(r[0], "%Y-%m-%d %H:%M") - B0).total_seconds() // 3600): r[1:] for r in rows}
    c.close()
G = E[E.jahr == 2026]
gl, n, e24 = 0, 0, []
for r in G.itertuples():
    kz = reihen[r.symbol]
    cc = kz[r.stunde][2]
    tu = next((s for s in range(1, 73) if (r.stunde + s) in kz and kz[r.stunde + s][0] >= 1.05 * cc), 999)
    td = next((s for s in range(1, 73) if (r.stunde + s) in kz and kz[r.stunde + s][1] <= 0.95 * cc), 999)
    n += 1
    gl += int(str(tu) == str(r.t_u) and str(td) == str(r.t_d))
print("G1  Schleife (Teil 2) gegen die Referenz 2026: %d von %d Einstiegen t_u und t_d gleich -> %s" % (gl, n, "GLEICH" if gl == n else "ABWEICHUNG"))
R = E[E.jahr >= 2025].copy()
R["e24"] = [(reihen[r.symbol].get(r.stunde + 24, (0, 0, np.nan))[2] / reihen[r.symbol][r.stunde][2] - 1) for r in R.itertuples()]
R = R.dropna(subset=["e24"])
R["tag"] = R.stunde // 24
m = R.e24.mean()
g = R.groupby("tag").e24.agg(["sum", "count"])
var = ((g["sum"] - m * g["count"]) ** 2).sum() / g["count"].sum() ** 2
print("G2  cluster-robust: Mittel %+.3f %%, Halbbreite 95 %% %.2f Pp ueber %d Tage (Bootstrap in p61: 0,49) · hochgerechnet auf 365 Tage %.2f Pp"
      % (100 * m, 100 * 1.96 * np.sqrt(var), len(g), 100 * 1.96 * np.sqrt(var) * np.sqrt(len(g) / 365)))
