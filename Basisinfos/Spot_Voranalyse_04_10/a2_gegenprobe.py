"""Gegenprobe Altcoin Fassung 2 (python Basisinfos/Spot_Voranalyse_04_10/a2_gegenprobe.py): fuenf A1-Ereignisse je Ausstieg X1/X2/X3
mit eigener einfacher Schleife direkt aus SQL nachgerechnet und gegen a2_messung.handel verglichen."""
import os, sqlite3, sys, random
from datetime import date, timedelta
os.chdir(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, "Basisinfos/Spot_Voranalyse_04_10")
import a2_messung as A
c = sqlite3.connect("file:data/messdaten.db?mode=ro", uri=True)
def reihe(s, ab, n):
    r = c.execute("SELECT date, close FROM price_history_ohlc WHERE assetklasse='krypto' AND currency='USD' AND symbol=? AND date>=? ORDER BY date LIMIT ?", (s, ab, n + 1)).fetchall()
    out, d0 = [], date.fromisoformat(ab)
    for i, (d, x) in enumerate(r):
        if date.fromisoformat(d) != d0 + timedelta(days=i): break       # Luecke = Ende der Reihe
        out.append(x)
    return out
def eigen(s, t_ein, art):
    n = 365 if art == "X3" else 730
    v, b = reihe(s, t_ein, n), reihe("BTC", t_ein, n)
    b = b[:len(v)]
    if art == "X3":
        vk = [(min(365, len(v) - 1), 1.0)]
    else:
        hoch, vk, rest, tp = v[0], [], 1.0, [2.0, 3.0]
        for i in range(len(v)):
            hoch = max(hoch, v[i])
            if art == "X1":
                for f in list(tp):
                    if v[i] >= f * v[0] and i + 1 < len(v):
                        vk.append((i + 1, 1 / 3)); rest -= 1 / 3; tp.remove(f)
            if (v[i] < 0.65 * hoch or (art == "X2" and v[i] < 0.5 * v[0])):
                vk.append((min(i + 1, len(v) - 1), rest)); rest = 0; break
        if rest > 1e-9:
            vk.append((len(v) - 1, rest))
    ec = sum(a * v[t] / v[0] * (1 - 0.0125) for t, a in vk) / 1.0125
    eb = sum(a * b[t] / b[0] * (1 - 0.004) for t, a in vk) / 1.004
    return ec / eb - 1
random.seed(7)
ev = [e for e in A.mit_ruhe(A.A1) if e[0] < A.ENDE - timedelta(days=800)]
for t, s in random.sample(ev, 5):
    i0 = A.POS[t] + 1
    for art in ("X1", "X2", "X3"):
        h = A.handel(s, i0, art)
        print("%s %-8s %s  Messung %+.4f  Gegenprobe %+.4f" % (t.date(), s, art, h["vorteil"], eigen(s, A.IDX[i0].date().isoformat(), art)))
