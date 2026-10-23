"""Gegenprobe P70 E-A (23.10.2026) - eigener Code.

    python Basisinfos/Rechenkern_02_10/p70_gegenprobe.py

G1 Kaufvorteil (N 7 T, unverzerrt_1, 2025 und 2026, Altcoins) per eigener Schleife direkt aus den Einstiegen und p64.reihe = p70?
G2 Fairness der Nullwelt: mittlere Wartezeit bis zum Kauf (Stunden) REGEL0 gegen Nullwelt - gleich? (sonst erklaert die Drift den Rang)
G3 Selbsttest mit anderem Startwert: Zufallssignale ~0, Raenge nicht systematisch am Rand
G4 Auskunft: Kaufvorteil REGEL0 minus Nullwelt je Monat (unverzerrt_1, Altcoins) - Anteil Monate > 0 je Jahr
G5 Nullwelt 2 mit GLEICHER Wartezeit: Kaufstunde aus der Verteilung der REGEL0-Wartezeiten desselben Jahres gezogen - Rang je Jahr
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


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


print("P70 GEGENPROBE\n")
out = subprocess.run([sys.executable, "-X", "utf8", os.path.join("Basisinfos", "Rechenkern_02_10", "p70_ea_kaufzeitpunkt.py")],
                     capture_output=True, text=True, encoding="utf-8").stdout
E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_unverzerrt_1.csv"), sep=";")
KERN = {"BTC", "ETH", "SOL"}
N, fh = 7, 7 * 24
res = {2025: [], 2026: []}
warte = {2025: [], 2026: []}
warte_null = {2025: [], 2026: []}
monat = {}
rng = np.random.default_rng(31)
for s, grp in E.groupby("symbol"):
    if s in KERN:
        continue
    x = P.reihe(s)
    if x is None:
        continue
    a, L, C = x
    st = set(grp.stunde.astype(int))
    for m in pd.date_range("2025-01-01", "2026-08-01", freq="MS"):
        h0 = int((m - P.B0) / pd.Timedelta(hours=1))
        i0 = h0 - a
        if i0 < 0 or i0 + fh + 30 >= len(C):
            continue
        c0, cf, cT = C[i0], C[i0 + fh], C[i0 + fh + 24]
        if not (np.isfinite(c0) and np.isfinite(cf) and np.isfinite(cT)):
            continue
        sig = [k for k in range(fh) if (h0 + k) in st and np.isfinite(C[i0 + k])]
        kauf = C[i0 + sig[0]] if sig else cf
        v = cT / kauf - cT / c0
        res[m.year].append(v)
        if sig:
            warte[m.year].append(sig[0])
            gueltig = [k for k in range(fh) if np.isfinite(C[i0 + k])]
            z = np.array(gueltig)[rng.integers(0, len(gueltig), (200, len(sig)))].min(axis=1)
            warte_null[m.year].append(z.mean())
            nv = (cT / C[i0 + z] - cT / c0).mean()
        else:
            nv = v
        monat.setdefault(m, []).append(v - nv)
g1 = []
gleich = True
for j in (2025, 2026):
    mo = re.search(r"%d unverzerrt_1\s+Altcoins:\s+(\d+) Faelle .*?Kaufvorteil ([-+0-9.]+) %%" % j, out)
    v = 100 * np.mean(res[j])
    gleich &= bool(mo) and int(mo.group(1)) == len(res[j]) and abs(float(mo.group(2)) - v) < 0.002
    g1.append("%d %d Faelle %+.3f / %s" % (j, len(res[j]), v, mo.groups() if mo else "-"))
pruefe("G1 Kaufvorteil per eigener Schleife = p70", gleich, " · ".join(g1))
g2 = " · ".join("%d REGEL0 %.1f h gegen Nullwelt %.1f h" % (j, np.mean(warte[j]), np.mean(warte_null[j])) for j in (2025, 2026))
fair = all(abs(np.mean(warte[j]) - np.mean(warte_null[j])) < 6 for j in (2025, 2026))
pruefe("G2 Wartezeit REGEL0 gegen Nullwelt gleich (+-6 h)", fair, g2)

rng2 = np.random.default_rng(77)
n = 3000
z = rng2.standard_t(4, (n, fh + 25)) / np.sqrt(2) * 0.006
Cs = np.cumprod(1 + z, axis=1)
werte = []
for _ in range(3):
    e = []
    for c in Cs:
        k = rng2.poisson(1.0)
        s_ = sorted(rng2.integers(0, fh, k)) if k else []
        kauf = c[s_[0]] if s_ else c[fh]
        e.append(c[fh + 24] / kauf - c[fh + 24] / c[0])
    werte.append(np.mean(e))
pruefe("G3 Selbsttest anderer Startwert: Zufallssignale |Mittel| < 0,2 %", all(abs(w) < 0.002 for w in werte), " / ".join("%+.3f %%" % (100 * w) for w in werte))
anteil = {j: np.mean([np.mean(v) > 0 for m, v in monat.items() if m.year == j]) for j in (2025, 2026)}
print("  G4 Auskunft: Monate mit REGEL0 besser als Nullwelt: 2025 %.0f %% · 2026 %.0f %%" % (100 * anteil[2025], 100 * anteil[2026]))
faelle = {2025: [], 2026: []}
for s, grp in E.groupby("symbol"):
    if s in KERN:
        continue
    x = P.reihe(s)
    if x is None:
        continue
    a, L, C = x
    st = set(grp.stunde.astype(int))
    for m in pd.date_range("2025-01-01", "2026-08-01", freq="MS"):
        h0 = int((m - P.B0) / pd.Timedelta(hours=1))
        i0 = h0 - a
        if i0 < 0 or i0 + fh + 30 >= len(C) or not np.isfinite(C[[i0, i0 + fh, i0 + fh + 24]]).all():
            continue
        sig = [k for k in range(fh) if (h0 + k) in st and np.isfinite(C[i0 + k])]
        if sig:
            faelle[m.year].append((C[i0:i0 + fh], C[i0], C[i0 + fh + 24], sig[0]))
rng3 = np.random.default_rng(41)
g5 = []
for j in (2025, 2026):
    F = faelle[j]
    w = np.array([f[3] for f in F])
    echt = np.mean([f[2] / f[0][f[3]] - f[2] / f[1] for f in F])
    null = np.zeros(200)
    for c, c0, cT, _ in F:
        cz = c[rng3.choice(w, 200)]
        cz = np.where(np.isfinite(cz), cz, c0)
        null += cT / cz - cT / c0
    null /= len(F)
    g5.append("%d nur Faelle mit Signal: REGEL0 %+.3f %% · Nullwelt gleiche Wartezeit %+.3f %% · Rang %.2f" % (j, 100 * echt, 100 * null.mean(), np.mean(null < echt)))
print("  G5 " + " | ".join(g5))
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
