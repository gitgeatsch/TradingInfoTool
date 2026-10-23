"""Gegenprobe P69 M-L (23.10.2026) - eigener Code, Schleife je Einstieg (ohne die vektorisierten Felder aus p69).

    python Basisinfos/Rechenkern_02_10/p69_gegenprobe.py

G1 Basis H, Tiefe 0,5 %: netto je gefuelltem Handel 2025/2026 je Menge per Einzelschleife = p69 (+-0,005 Pp)
G2 Wahl 2024 auf zweitem Weg: Gesamtertrag je Signal je Tiefe (Basis H) - waehlt dieselbe Tiefe?
G3 Nullwelt plausibel: 24-h-Mittel zufaelliger Stunden derselben Coins je Jahr (ohne Limit) = Marktdrift dieser Coins (negativ 2025/26?)
G4 Auskunft Gueltigkeit 2 / 8 h bei Tiefe 0,5 % und 1 % (Basis H, unverzerrt_1, 2025 und 2026)
"""
import os
import re
import subprocess
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import p64_lc_voranalyse as P  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []
MENGEN = ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3")


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


cache = {}


def roh(menge):
    E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % menge), sep=";")
    out = []
    for s, st, j in zip(E.symbol, E.stunde, E.jahr):
        if s not in cache:
            cache[s] = P.reihe(s)
        x = cache[s]
        if x is None:
            continue
        a, L, C = x
        i = int(st) - a
        if i < 0 or i + 24 >= len(C):
            continue
        if not (np.isfinite(C[i]) and np.isfinite(C[i + 24]) and np.isfinite(L[i + 1:i + 9]).all()):
            continue
        out.append((int(j), C[i], C[i + 24], L[i + 1:i + 9].copy()))
    return out


def netto(z, x, w, kosten, jahr=None):
    s = n = 0
    for j, c0, c24, L in z:
        if jahr is not None and j != jahr:
            continue
        lim = c0 * (1 - x)
        if L[:w].min() <= lim:
            s += c24 / lim - 1 - kosten
            n += 1
    return s, n


print("P69 GEGENPROBE\n")
out = subprocess.run([sys.executable, "-X", "utf8", os.path.join("Basisinfos", "Rechenkern_02_10", "p69_ml_limit.py")],
                     capture_output=True, text=True, encoding="utf-8").stdout
blk = out.split("=== Basis H (Kosten")[1].split("=== Basis H+Schlupf")[0]
Z = {m: roh(m) for m in MENGEN}
g1 = []
gleich = True
for m in MENGEN:
    for j in (2025, 2026):
        s, n = netto(Z[m], 0.005, 4, 0.0048, j)
        mo = re.search(r"%d %s\s+netto je gefuelltem Handel ([-+0-9.]+) %%" % (j, m), blk)
        v = 100 * s / n
        gleich &= bool(mo) and abs(float(mo.group(1)) - v) < 0.006
        g1.append("%s %d %+.3f/%s" % (m, j, v, mo.group(1) if mo else "-"))
pruefe("G1 netto je gefuelltem Handel (Basis H, 0,5 %) per Einzelschleife", gleich, " · ".join(g1))

ges = {}
for x in (0.005, 0.01, 0.015, 0.02):
    ges[x] = np.mean([netto(Z[m], x, 4, 0.0048, 2024)[0] / sum(1 for z in Z[m] if z[0] == 2024) for m in MENGEN])
wahl = max(ges, key=ges.get)
pruefe("G2 Wahl 2024 auf zweitem Weg waehlt dieselbe Tiefe (0,5 %)", wahl == 0.005, " · ".join("%.1f %% %+.3f" % (100 * k, 100 * v) for k, v in ges.items()))

rng = np.random.default_rng(9)
zeilen = []
for j in (2025, 2026):
    r = []
    for s in list(cache)[:400]:
        x = cache[s]
        if x is None:
            continue
        a, L, C = x
        jahr = (P.B0 + pd.to_timedelta(np.arange(len(C)) + a, unit="h")).year
        kand = np.flatnonzero((jahr == j) & np.isfinite(C) & np.isfinite(np.roll(C, -24)))
        kand = kand[kand + 24 < len(C)]
        if len(kand) > 50:
            idx = rng.choice(kand, 50)
            r.extend(C[idx + 24] / C[idx] - 1)
    zeilen.append("%d: %+.3f %%" % (j, 100 * np.nanmean(r)))
pruefe("G3 Nullwelt plausibel: Zufallsstunden ohne Limit (24 h, ohne Kosten) zeigen die Marktdrift dieser Coins", True, " · ".join(zeilen))

zz = []
for x in (0.005, 0.01):
    for w in (2, 4, 8):
        t = []
        for j in (2025, 2026):
            s, n = netto(Z["unverzerrt_1"], x, w, 0.0048, j)
            t.append("%d %+.3f (%.0f %%)" % (j, 100 * s / n, 100 * n / sum(1 for z in Z["unverzerrt_1"] if z[0] == j)))
        zz.append("%.1f %% / %d h: %s" % (100 * x, w, " ".join(t)))
print("  G4 Auskunft Gueltigkeit (Basis H, unverzerrt_1): " + " | ".join(zz))
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
