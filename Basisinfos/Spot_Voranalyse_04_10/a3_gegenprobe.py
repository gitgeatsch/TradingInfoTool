"""Gegenprobe Altcoin Fassung 3 (python Basisinfos/Spot_Voranalyse_04_10/a3_gegenprobe.py): je Ausstieg X4/X5/X6 fuenf A1-Ereignisse
mit eigener einfacher Schleife direkt aus SQL nachgerechnet und gegen a3_messung.handel3 verglichen; dazu die Ausstiegsgruende von X6."""
import os, sqlite3, sys, random
from datetime import date, timedelta
import numpy as np
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, "Basisinfos/Spot_Voranalyse_04_10")
import a3_messung as M
A = M.A
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)


def reihe(s, ab, n):
    r = c.execute("SELECT date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol=? AND date>=? ORDER BY date LIMIT ?", (s, ab, n + 1)).fetchall()
    out, d0 = [], date.fromisoformat(ab)
    for i, (d, x) in enumerate(r):
        if date.fromisoformat(d) != d0 + timedelta(days=i) or x is None: break
        out.append(x)
    return out


def eigen(s, ab, art, i0):
    n = {"X4": 120, "X5": 90, "X6": 1095}[art]
    v = reihe(s, ab, n); b = reihe("BTC", ab, n)[:len(v)]
    vk, rest, hoch, ziele, scharf, qh, grund = [], 1.0, v[0], [1.30, 1.60], False, -1.0, "Frist/Ende"
    for i in range(1, len(v)):
        hoch = max(hoch, v[i])
        if art == "X5":
            if v[i] >= 1.40 * v[0] or v[i] <= 0.75 * v[0]:
                vk.append((min(i + 1, len(v) - 1), 1.0)); rest = 0; break
        elif art == "X4":
            for f in list(ziele):
                if v[i] >= f * v[0] and rest > 1e-9:
                    teil = 0.5 if f == 1.30 else rest
                    vk.append((min(i + 1, len(v) - 1), teil)); rest -= teil; ziele.remove(f)
            if rest > 1e-9 and v[i] < 0.80 * hoch:
                vk.append((min(i + 1, len(v) - 1), rest)); rest = 0
            if rest <= 1e-9: break
        if art == "X6":
            pass
    if art == "X6":
        for i in range(0, len(v)):
            q, br = M.QV[i0 + i], M.BRV[i0 + i]
            if not np.isnan(q) and q >= 0.80: scharf = True
            if scharf and not np.isnan(q): qh = max(qh, q)
            k2 = scharf and not np.isnan(q) and q < qh - 0.10
            alt = (not np.isnan(br)) and br >= 0.75
            if k2 or alt:
                grund = "K2" if k2 else "Breite"
                vk.append((min(i + 1, len(v) - 1), 1.0)); rest = 0; break
    if rest > 1e-9:
        vk.append((len(v) - 1, rest))
    ec = sum(a * v[t] / v[0] * (1 - 0.0125) for t, a in vk) / 1.0125
    eb = sum(a * b[t] / b[0] * (1 - 0.004) for t, a in vk) / 1.004
    return ec / eb - 1, grund


random.seed(8)
ev = A.mit_ruhe(A.A1)
gleich = 0; n = 0
for art in ("X4", "X5", "X6"):
    for t, s in random.sample(ev, 5):
        i0 = A.POS[t] + 1
        if i0 >= len(A.IDX): continue
        h = M.handel3(s, i0, art)
        g, grund = eigen(s, A.IDX[i0].date().isoformat(), art, i0)
        ok = abs(h["vorteil"] - g) < 1e-9; gleich += ok; n += 1
        print("%s %-9s %s  Messung %+.4f  Gegenprobe %+.4f  %s%s" % (t.date(), s, art, h["vorteil"], g, "gleich" if ok else "ABWEICHUNG",
                                                                     ("  (" + grund + ")") if art == "X6" else ""))
print("\n%d von %d gleich" % (gleich, n))

print("\nX6 Ausstiegsgrund je Epoche (alle A1-Ereignisse H/M/S):")
zahl = {}
for t, s in ev:
    i0 = A.POS[t] + 1
    if i0 >= len(A.IDX) or np.isnan(A.K[s].values[i0]): continue
    _, grund = eigen(s, A.IDX[i0].date().isoformat(), "X6", i0)
    zahl.setdefault(A.epoche(t), {}).setdefault(grund, 0); zahl[A.epoche(t)][grund] += 1
for e in sorted(zahl):
    print("  %s  %s" % (e, "  ".join("%s %d" % kv for kv in sorted(zahl[e].items()))))
