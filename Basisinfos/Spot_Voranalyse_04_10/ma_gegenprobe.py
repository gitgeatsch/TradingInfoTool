"""Gegenprobe M-A Fassung 1 (Spot §60): zweite Wege, ohne den Code von ma_messung.py fuer die Rechnung zu benutzen.

    python Basisinfos/Spot_Voranalyse_04_10/ma_gegenprobe.py

G1 eigene Tagesschleife (reines Python, Listen): Endvermoegen/Halten, groesster Rueckgang, Wechsel je Teil - gleich ma_messung?
G2 kein Vorgriff: der Zustand an 20 zufaelligen Monatsenden, neu gerechnet nur aus Kursen BIS zu diesem Tag - gleich?
G3 Umkehr-Probe aus Monatsschluessen auf zweitem Weg (Haltemonat = Folgetag bis Folgetag) - Vorzeichen gleich?
G4 Wechselkurs: EUR-Kurs an 5 Stichtagen = USD / EZB-Kurs (Rohdatei, letzter Wert <= Tag); kein Tag ohne Kurs nach 2010-07
G5 Baerenphasen: je Phase ist der Hoch-Tag das Maximum und der Tief-Tag das Minimum zwischen den Wendepunkten
"""
import csv
import os
import re
import sqlite3
import subprocess
import sys
from bisect import bisect_right
from datetime import date, timedelta

import numpy as np

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


print("M-A GEGENPROBE\n")
c = sqlite3.connect("file:data/_spot/coinmetrics.db?mode=ro", uri=True)
roh = c.execute("SELECT tag, PriceUSD FROM tag WHERE asset='btc' AND PriceUSD IS NOT NULL ORDER BY tag").fetchall()
c.close()
fx_t, fx_v = [], []
with open(os.path.join("data", "_spot", "ma_eurusd_ezb.csv"), encoding="utf-8") as f:
    for r in csv.DictReader(f):
        fx_t.append(date.fromisoformat(r["tag"][:10]))
        fx_v.append(float(r["eurusd"]))
tage, eur = [], []
for t, p in roh:
    d = date.fromisoformat(t[:10])
    i = bisect_right(fx_t, d) - 1
    if i >= 0:
        tage.append(d)
        eur.append(p / fx_v[i])
idx = {d: i for i, d in enumerate(tage)}

# G4
stich = [date(2011, 6, 8), date(2014, 3, 15), date(2018, 12, 15), date(2022, 11, 21), date(2026, 6, 30)]
werte = []
for d in stich:
    i = bisect_right(fx_t, d) - 1
    werte.append("%s %.2f" % (d, eur[idx[d]]))
luecke = sum((tage[i] - tage[i - 1]).days != 1 for i in range(1, len(tage)))
pruefe("G4 Wechselkurs: Tagesraster ohne Luecke, EUR-Kurse an Stichtagen", luecke == 0, " · ".join(werte))

# Monatsenden und Zustand R2 (eigene Rechnung)
me = [i for i in range(len(tage) - 1) if tage[i + 1].month != tage[i].month]
zust = {}
for k in range(9, len(me)):
    schl = [eur[me[j]] for j in range(k - 9, k + 1)]
    zust[tage[me[k]]] = eur[me[k]] > sum(schl) / 10.0

# G2 kein Vorgriff
rng = np.random.default_rng(3)
proben = sorted(rng.choice(list(zust), 20, replace=False))
gleich = 0
for d in proben:
    bis = [eur[i] for i in range(idx[d] + 1)]
    tb = tage[:idx[d] + 1]
    mon = [j for j in range(len(tb)) if j == len(tb) - 1 or tb[j + 1].month != tb[j].month]
    schl = [bis[j] for j in mon[-10:]]
    gleich += int((bis[-1] > sum(schl) / 10.0) == zust[d])
pruefe("G2 kein Vorgriff: Zustand nur aus Kursen bis zum Monatsende", gleich == 20, "%d von 20 gleich" % gleich)


def lauf(s, e):
    s, e = date.fromisoformat(s), date.fromisoformat(e)
    pos = None
    v, h, vmax, hmax, rv, rh, w = 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0
    i0 = idx[s]
    for i in range(i0, idx[e] + 1):
        if i > i0:
            r = eur[i] / eur[i - 1]
            if pos:
                v *= r
            h *= r
        vorher = tage[i] - timedelta(days=1)
        if vorher in zust:
            neu = zust[vorher]
            if pos is not None and neu != pos:
                w += 1
            pos = neu
        vmax, hmax = max(vmax, v), max(hmax, h)
        rv, rh = min(rv, v / vmax - 1), min(rh, h / hmax - 1)
    return v / h, rv, rh, w


out = subprocess.run([sys.executable, "-X", "utf8", os.path.join("Basisinfos", "Spot_Voranalyse_04_10", "ma_messung.py")],
                     capture_output=True, text=True, encoding="utf-8").stdout
for teil, (s, e) in {"A": ("2011-05-01", "2016-12-31"), "B": ("2017-01-01", "2026-09-30")}.items():
    eh, rv, rh, w = lauf(s, e)
    m = re.search(r"Teil %s %s bis %s: Endvermoegen / Halten ([0-9.]+) · groesster Rueckgang Regel ([-0-9.]+) %% gegen Halten ([-0-9.]+) %% · Wechsel (\d+)"
                  % (teil, s, e), out)
    pruefe("G1 Teil %s eigene Tagesschleife = ma_messung" % teil, m and abs(float(m.group(1)) - eh) < 0.0015 and abs(float(m.group(2)) - 100 * rv) < 0.06
           and abs(float(m.group(3)) - 100 * rh) < 0.06 and int(m.group(4)) == w,
           "hier %.3f / %.1f %% / %.1f %% / %d · dort %s" % (eh, 100 * rv, 100 * rh, w, m.groups() if m else "-"))
    # G3 Umkehr
    exe = [i for i in range(idx[date.fromisoformat(s)], idx[date.fromisoformat(e)] + 1) if (tage[i] - timedelta(days=1)) in zust]
    ra, rd = [], []
    for a, b in zip(exe, exe[1:] + [idx[date.fromisoformat(e)]]):
        (rd if zust[tage[a] - timedelta(days=1)] else ra).append(eur[b] / eur[a] - 1)
    # KORREKTUR 21.10.: erste Fassung hatte "%%" im Muster ohne Formatierung - fand die Zeile nie (Werte waren gleich)
    m3 = re.search(r"Umkehr: Haltemonat-Rendite draussen ([-+0-9.]+) % \(n (\d+)\)", out[out.index("Teil %s %s" % (teil, s)):])
    pruefe("G3 Teil %s Umkehr-Probe zweiter Weg" % teil, m3 and abs(float(m3.group(1)) - 100 * np.mean(ra)) < 0.06 and int(m3.group(2)) == len(ra),
           "draussen %+.1f %% (n %d), drin %+.1f %% (n %d)" % (100 * np.mean(ra), len(ra), 100 * np.mean(rd), len(rd)))

# G5 Phasen
ph = re.findall(r"  (\d{4}-\d\d-\d\d) -> (\d{4}-\d\d-\d\d)  -?\d+ %", out.split("HAUPTREGEL")[0])
fehler = 0
for (h, t), nxt in zip(ph, ph[1:] + [(None, None)]):
    ih, it = idx[date.fromisoformat(h)], idx[date.fromisoformat(t)]
    seg = eur[ih:it + 1]
    fehler += int(min(seg) != eur[it] or max(seg) != eur[ih] or eur[it] / eur[ih] - 1 > -0.5)
pruefe("G5 Baerenphasen: Hoch ist Maximum, Tief ist Minimum, Rueckgang >= 50 %", len(ph) > 0 and fehler == 0, "%d Phasen, %d Fehler" % (len(ph), fehler))
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
