"""P101 Gegenprobe H-1 - ZWEITER RECHENWEG, ohne p101_h1_basis zu rechnen (nur dessen Tabelle wird gelesen und geprueft).

    python -X utf8 Basisinfos/Rechenkern_02_10/p101_h1_gegenprobe.py [--ergebnis]

G1  Stichprobe 300 Einstiege je Menge aus den ROHDATEN nachgerechnet (eigene SQL, eigene Schleifen): r6/r24/r72/r120, rF
    (nachgezogener Stop), Zustaende a/b/c (Vortag, eigene Schnitte), ext_mom/ext_rsi (eigene ATR, eigener RSI)
G4  Mutationen, die G1 erkennen MUSS: Zustand a mit dem Schluss DESSELBEN Tages (Vorgriff) · Stop-Linie mit dem Hoch der
    LAUFENDEN Stunde (Vorgriff) - weicht nichts ab, ist G1 blind
G2  (--ergebnis, erst nach der Messung) Tagesklammer je Hypothese und Menge mit reinen Python-Schleifen = Werkzeug (1e-12);
    Nullpunkt mit eigener Vertauschung (random.shuffle je Tag, 40 Ziehungen) innerhalb der Zufallsstreuung
Nur lesend (mode=ro).
"""
import math
import os
import random
import sqlite3
import sys
from datetime import datetime, timedelta

import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
DATA = os.path.join(WURZEL, "data")
B0 = datetime(2020, 1, 1)
MENGEN = ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3")
DATEIEN = ("stundenkurse.db", "stundenkurse_alle.db", "eingestellt_historie.db")
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass


def ro(name):
    return sqlite3.connect("file:%s?mode=ro" % os.path.join(DATA, name).replace("\\", "/"), uri=True)


CON = [ro(d) for d in DATEIEN if os.path.exists(os.path.join(DATA, d))]
MD = ro("messdaten.db")
_rk, _tk = {}, {}


def zeilen(sym):
    """Gespeicherte Stundenzeilen, erste Datei gewinnt: Liste (stunde_index, h, l, c), aufsteigend."""
    if sym not in _rk:
        d = {}
        for c in CON:
            for st, h, lo, cl in c.execute("SELECT stunde, high, low, close FROM stundenkurse WHERE symbol=?", (sym,)):
                if st not in d:
                    d[st] = (h, lo, cl)
        _rk[sym] = [(int((datetime.strptime(s, "%Y-%m-%d %H:%M") - B0).total_seconds() // 3600),) + d[s] for s in sorted(d)]
    return _rk[sym]


def tage(sym):
    if sym not in _tk:
        _tk[sym] = [(r[0], r[1]) for r in MD.execute(
            "SELECT date, close FROM price_history_ohlc WHERE symbol=? AND assetklasse='krypto' ORDER BY date", (sym,))]
    return _tk[sym]


def nachrechnen(sym, std, vorgriff=False):
    z = zeilen(sym)
    pos = {r[0]: i for i, r in enumerate(z)}
    i = pos[std]
    c0 = z[i][3]
    nach = {r[0]: r for r in z[i + 1:i + 200]}
    r = {"r%d" % h: nach[std + h][3] / c0 - 1 for h in (6, 24, 72, 120)}
    sp = [(x[1] - x[2]) / x[3] for x in z[i - 23:i + 1]]
    atr = sum(sp) / 24 * math.sqrt(24) if i >= 23 else float("nan")
    mx, rf = 1.0, nach[std + 120][3] / c0 - 1
    for s in range(1, 121):
        _st, h, lo, _c = nach[std + s]
        if vorgriff:
            mx = max(mx, h / c0)
        lin = mx - 1.5 * atr
        if lo / c0 <= lin:
            rf = lin - 1
            break
        mx = max(mx, h / c0)
    r["rF"] = rf
    vor = z[i - 6][3] if i >= 6 else float("nan")
    r["ext_mom"] = float((c0 / vor - 1) / max(atr, 1e-12) >= 0.8509) if i >= 23 else float("nan")
    diffs = [z[k][3] - z[k - 1][3] if k > 0 else 0.0 for k in range(i - 13, i + 1)]
    auf = sum(x for x in diffs if x > 0) / 14
    ab = sum(-x for x in diffs if x < 0) / 14
    rsi = 100 - 100 / (1 + auf / max(ab, 1e-12))
    r["ext_rsi"] = float(rsi >= 85.6631)
    # Tageszustaende, Stand Vortag (Mutation: derselbe Tag)
    tag = (B0 + timedelta(hours=std)).strftime("%Y-%m-%d")
    t = tage(sym)
    idx = [k for k, (d, _c) in enumerate(t) if (d <= tag if vorgriff else d < tag)]
    if idx:
        k = idx[-1]
        cl = [c for _d, c in t[:k + 1]]
        r["a"] = float(cl[-1] > sum(cl[-50:]) / 50) if len(cl) >= 50 else float("nan")
        r["b"] = float(cl[-1] > sum(cl[-200:]) / 200) if len(cl) >= 200 else float("nan")
        bt = dict(tage("BTC"))
        if len(cl) > 30 and t[k][0] in bt and t[k - 30][0] in bt:
            r["c"] = float((cl[-1] / cl[-31]) / (bt[t[k][0]] / bt[t[k - 30][0]]) - 1 > 0)
        else:
            r["c"] = float("nan")
    else:
        r["a"] = r["b"] = r["c"] = float("nan")
    return r


def gleich(x, y):
    if isinstance(x, float) and math.isnan(x):
        return isinstance(y, float) and math.isnan(y)
    return abs(x - y) < 1e-9


def g1(mutation=False):
    rng = random.Random(7)
    abw, n = {}, 0
    for menge in MENGEN:
        T = pd.read_csv(os.path.join(DATA, "_h1", "h1_%s.csv" % menge), sep=";")
        for zl in T.sample(300, random_state=rng.randint(0, 10 ** 6)).itertuples():
            ist = nachrechnen(zl.symbol, int(zl.stunde), vorgriff=mutation)
            n += 1
            for k, v in ist.items():
                w = float(getattr(zl, k))
                if not gleich(float(v), w):
                    abw.setdefault(k, []).append((menge, zl.symbol, int(zl.stunde), v, w))
    return n, abw


def je_tag_py(tag, z, d):
    g = {}
    for t, zi, di in zip(tag, z, d):
        if math.isnan(zi) or math.isnan(di):
            continue
        g.setdefault(t, ([], []))[0 if zi == 1 else 1].append(di)
    return [sum(a) / len(a) - sum(b) / len(b) for a, b in g.values() if a and b], g


def g2():
    sys.path.insert(0, HIER)
    import p101_h1_basis as B  # noqa: E402 - nur zum VERGLEICH der Werkzeugzahl
    import numpy as np
    rng = random.Random(11)
    fehl = 0
    for teil, hyps, zst in (("H-1b", B.H1B, "a"), ("H-1c", B.H1C, "extrem")):
        for name, lang, kurz in hyps:
            for menge in MENGEN:
                T = pd.read_csv(os.path.join(DATA, "_h1", "h1_%s.csv" % menge), sep=";")
                U = T[T.jahr >= 2025]
                d = (U[lang] - U[kurz]).tolist()
                z = U[zst].astype(float).tolist()
                dts, g = je_tag_py(U.tag.tolist(), z, d)
                eigen = sum(dts) / len(dts)
                werk = B.klammer(U.tag.to_numpy(), U[zst].to_numpy(float), B.delta(U, lang, kurz))
                nulls = []
                for _ in range(40):
                    w = []
                    for a, b in g.values():
                        alle = a + b
                        rng.shuffle(alle)
                        aa, bb = alle[:len(a)], alle[len(a):]
                        if aa and bb:
                            w.append(sum(aa) / len(aa) - sum(bb) / len(bb))
                    nulls.append(sum(w) / len(w))
                ok_t = len([1 for a, b in g.values() if a and b])
                ok = np.isclose(eigen, werk, atol=1e-12)
                wn = B.nullwelt(U.tag.to_numpy()[np.isfinite(U[zst].to_numpy(float)) & np.isfinite(B.delta(U, lang, kurz))],
                                U[zst].to_numpy(float)[np.isfinite(U[zst].to_numpy(float)) & np.isfinite(B.delta(U, lang, kurz))],
                                B.delta(U, lang, kurz)[np.isfinite(U[zst].to_numpy(float)) & np.isfinite(B.delta(U, lang, kurz))],
                                np.random.default_rng(5))[0]
                sd = float(np.std(nulls))
                okn = abs(sum(nulls) / 40 - wn) <= 4 * sd / math.sqrt(20) + 1e-12
                fehl += (not ok) + (not okn)
                print("   G2 %s %-5s %-13s Klammer eigen %+.6f %% / Werkzeug %+.6f %% %s · Tage %d · Nullpunkt eigen %+.4f / "
                      "Werkzeug %+.4f %% %s" % (teil, name, menge, 100 * eigen, 100 * werk, "✔" if ok else "✖", ok_t,
                                                100 * sum(nulls) / 40, 100 * wn, "✔" if okn else "✖"))
    return fehl


def main():
    print("P101 GEGENPROBE H-1 · zweiter Rechenweg aus den Rohdaten\n")
    n, abw = g1()
    print("G1 Stichprobe %d Einstiege: %s" % (n, "✔ alle Groessen gleich" if not abw else "✖ Abweichungen: %s" % {
        k: len(v) for k, v in abw.items()}))
    for k, v in abw.items():
        for x in v[:3]:
            print("      %s %s %s %d: eigen %r / Werkzeug %r" % (k, *x))
    _n, mut = g1(mutation=True)
    blind = [k for k in ("a", "rF") if k not in mut]
    print("G4 Mutationen (Vorgriff Tageszustand a, Stop-Linie mit laufendem Hoch): %s" % (
        "✔ erkannt: " + ", ".join("%s %d Abweichungen" % (k, len(mut[k])) for k in ("a", "rF")) if not blind
        else "✖ G1 BLIND fuer %s" % blind))
    fehl = len(abw) + len(blind)
    if "--ergebnis" in sys.argv:
        fehl += g2()
    print("\nGEGENPROBE: %s" % ("✔ BESTANDEN" if not fehl else "✖ %d Punkte offen" % fehl))
    return 1 if fehl else 0


if __name__ == "__main__":
    sys.exit(main())
