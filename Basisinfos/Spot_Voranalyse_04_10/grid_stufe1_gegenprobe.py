"""Gegenprobe GRID STUFE 1 (§9) - zweite Wege und Selbsttest der Anlage.

    python Basisinfos/Spot_Voranalyse_04_10/grid_stufe1_gegenprobe.py

G1 eigene Gitterschleife (reines Python, je Stunde, Stufe fuer Stufe): BTC g 1 % echt, Summe ueber 36 Monate = grid_stufe1?
G2 Nullwelt behaelt je Monat Anfang und Ende (Summe der Renditen) - sonst waere der Vergleich unfair
G3 SELBSTTEST mit bekannter Wahrheit (kuenstliche Reihen mit der BTC-Schwankung): Rueckkehr zur Mitte (Renditen negativ autokorreliert)
   -> Rang >= 0,95; Trend (positiv autokorreliert) -> Rang <= 0,05; unabhaengige Renditen -> Rang dazwischen
G4 zweiter Weg zur Richtung: Varianz-Ratio VR(q) der Stundenrenditen (q = 6, 24, 168) mit heteroskedastie-robustem z (Lo/MacKinlay 1988).
   VR > 1 heisst Trend, VR < 1 Rueckkehr - gleiche Richtung wie das Gitter?
"""
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import grid_stufe1 as G  # noqa: E402  (nur Datenladen und die vektorisierte Fassung fuer G3; G1 rechnet eigenstaendig)

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
ok = []


def pruefe(name, bed, info=""):
    ok.append(bool(bed))
    print("  %s  %s%s" % ("OK  " if bed else "FEHL", name, ("  (%s)" % info) if info else ""))


def gitter_einfach(preise, g):
    """Stufe fuer Stufe: Bezug = erster Preis; Verkauf eine Stufe ueber der zuletzt gehandelten, Kauf eine darunter, zum Stufenpreis."""
    q = 1.0 + g
    p0 = preise[0]
    ell, menge, geld, nenn = 0, 0.0, 0.0, 0.0
    for p in preise[1:]:
        while p >= p0 * q ** (ell + 1) * (1 - 1e-12):
            ell += 1
            menge -= 1.0 / (p0 * q ** ell)
            geld += 1.0
            nenn += 1.0
        while p <= p0 * q ** (ell - 1) * (1 + 1e-12):
            ell -= 1
            menge += 1.0 / (p0 * q ** ell)
            geld -= 1.0
            nenn += 1.0
    wert = menge * preise[-1]
    return geld + wert, nenn + abs(wert)


print("GRID STUFE 1 - GEGENPROBE\n")
P, _ = G.stunden("BTC")
monate = sorted(set(P.index.to_period("M")))
s_e = s_n = 0.0
for mo in monate:
    e, n = gitter_einfach(P[P.index.to_period("M") == mo].values, 0.01)
    s_e += e
    s_n += n
out = subprocess.run([sys.executable, "-X", "utf8", os.path.join("Basisinfos", "Spot_Voranalyse_04_10", "grid_stufe1.py")],
                     capture_output=True, text=True, encoding="utf-8").stdout
m = re.search(r"BTC  g 1\.0 %: Ausfuehrungen\s+(\d+) · echt\s+([-+0-9.]+)", out)
pruefe("G1 eigene Gitterschleife BTC 1 % = grid_stufe1", m and abs(float(m.group(2)) - s_e) < 0.006 and abs(float(m.group(1)) - s_n) < 1.0,
       "hier %.2f / %.0f · dort %s" % (s_e, s_n, m.groups() if m else "-"))

rng = np.random.default_rng(1)
lp = np.log(P[P.index.to_period("M") == monate[5]].values)
r = np.diff(lp)
perm = rng.permuted(np.tile(r, (50, 1)), axis=1)
pruefe("G2 Nullwelt behaelt das Monatsende", np.allclose(perm.sum(axis=1), r.sum(), atol=1e-9), "Abweichung max %.1e" % np.abs(perm.sum(axis=1) - r.sum()).max())

# G3 Selbsttest: kuenstliche Monate mit der Stundenschwankung von BTC, Renditen r_t = phi * r_{t-1} + e_t
sig = np.std(np.diff(np.log(P.values)))


def welt(phi, n_mon=36, n=720, saat=0):
    rr = np.random.default_rng(saat)
    aus = []
    for _ in range(n_mon):
        e = rr.normal(0, sig * np.sqrt(1 - phi ** 2), n - 1)
        x = np.empty(n - 1)
        x[0] = e[0]
        for t in range(1, n - 1):
            x[t] = phi * x[t - 1] + e[t]
        aus.append(x)
    return aus


def rang_welt(monatsrenditen, g=0.01, D=200, saat=5):
    rr = np.random.default_rng(saat)
    echt_s, null_s = 0.0, np.zeros(D)
    for x in monatsrenditen:
        e, _ = G.gitter(np.concatenate([[0.0], np.cumsum(x)])[None, :], g)
        pm = rr.permuted(np.tile(x, (D, 1)), axis=1)
        nn, _ = G.gitter(np.concatenate([np.zeros((D, 1)), np.cumsum(pm, axis=1)], axis=1), g)
        echt_s += e[0]
        null_s += nn
    return float(np.mean(null_s < echt_s))


r_rueck, r_trend, r_null = rang_welt(welt(-0.10)), rang_welt(welt(+0.10)), rang_welt(welt(0.0))
pruefe("G3 Selbsttest: Rueckkehr (phi -0,10) Rang >= 0,95 · Trend (+0,10) Rang <= 0,05 · unabhaengig dazwischen",
       r_rueck >= 0.95 and r_trend <= 0.05 and 0.05 < r_null < 0.95, "Rueckkehr %.3f · Trend %.3f · unabhaengig %.3f" % (r_rueck, r_trend, r_null))


def vr(x, q):
    x = x - x.mean()
    n = len(x)
    s1 = np.mean(x ** 2)
    xq = np.convolve(x, np.ones(q), "valid")
    vq = np.sum(xq ** 2) / (n * q)
    v = vq / s1
    d = np.array([np.sum((x[j:] ** 2) * (x[:-j] ** 2)) / (np.sum(x ** 2) ** 2) * n for j in range(1, q)])
    th = np.sum([(2 * (q - j) / q) ** 2 * d[j - 1] for j in range(1, q)]) / n
    return v, (v - 1) / np.sqrt(th)


zeilen, richtung_gleich = [], True
for sym in ("BTC", "ETH", "SOL", "LINK"):
    x = np.diff(np.log(G.stunden(sym)[0].values))
    teile = []
    for q in (6, 24, 168):
        v, z = vr(x, q)
        teile.append("VR(%d) %.3f z %+.1f" % (q, v, z))
        if q == 24:
            richtung_gleich &= v > 1
    zeilen.append("%s: %s" % (sym, " · ".join(teile)))
print("  G4 Varianz-Ratio der Stundenrenditen 2023-09..2026-08:")
for z in zeilen:
    print("     " + z)
pruefe("G4 zweiter Weg: VR(24) > 1 (Trend) bei allen vier - gleiche Richtung wie das Gitter (umgekehrt)", richtung_gleich)
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
