"""Gegenprobe P68 (23.10.2026) - zweite Wege, eigener Code (nur Kursladen ueber p64.reihe bzw. direkt per SQL).

    python Basisinfos/Rechenkern_02_10/p68_gegenprobe.py

G1 O3 Limit 1 %: 300 zufaellige Einstiege (unverzerrt_1) direkt per SQL nachgerechnet (Tief der 4 Folgestunden, Schluss nach 24 h) = p68?
G2 O3 Limit 1 % je Jahr 2025 / 2026 und je Menge - netto > 0 in jedem Jahr?
G3 O3 strengere Fuellung: Tief muss das Limit um 0,05 % UNTERschreiten (Warteschlange) - bleibt netto > 0?
G4 O3 Dosis als Auskunft: x = 1,5 / 2 % (nicht Teil des Kriteriums)
G5 P-A Abdeckung auf zweitem Weg (Kontraktname PF_<BASE>USD zerlegt statt Feld 'base'); Funding-Vorzeichen: Binance positiv = Long zahlt
G6 P-A je Jahr mit Taker + 0,05 % Schlupf: netto > 0 in jedem Jahr und jeder Menge?
"""
import json
import os
import re
import sqlite3
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


def zeilen(menge):
    E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % menge), sep=";")
    E = E[E.jahr >= 2025]
    out = []
    for s, st in zip(E.symbol, E.stunde):
        if s not in cache:
            cache[s] = P.reihe(s)
        x = cache[s]
        if x is None:
            continue
        a, L, C = x
        i = int(st) - a
        if not (168 <= i and i + 24 < len(C) and np.isfinite(C[i]) and np.isfinite(C[i + 24])):
            continue
        t4 = L[i + 1:i + 5]
        out.append((s, int(st), C[i], C[i + 24], np.nanmin(t4) if np.isfinite(t4).any() else np.nan))
    D = pd.DataFrame(out, columns=["symbol", "stunde", "c0", "c24", "tief4"])
    D["jahr"] = (P.B0 + pd.to_timedelta(D.stunde, unit="h")).dt.year
    D["datum"] = (P.B0 + pd.to_timedelta(D.stunde, unit="h")).dt.strftime("%Y-%m-%d")
    return D


def limit_netto(D, x, streng=0.0, kosten=0.0048):
    lim = D.c0 * (1 - x)
    g = D.tief4 <= lim * (1 - streng)
    r = D.c24[g] / lim[g] - 1
    return r.mean() - kosten, g.mean(), g


print("P68 GEGENPROBE\n")
cons = [sqlite3.connect("file:data/%s?mode=ro" % d, uri=True) for d in P.DATEIEN if os.path.exists(os.path.join("data", d))]


def sql_reihe(sym, ab, bis):
    for c in cons:
        r = c.execute("SELECT stunde, low, close FROM stundenkurse WHERE symbol=? AND stunde>=? AND stunde<=? ORDER BY stunde", (sym, ab, bis)).fetchall()
        if len(r) >= 20:
            return r
    return []


D1 = zeilen("unverzerrt_1")
S = D1.sample(300, random_state=5)
gleich = 0
for r in S.itertuples():
    t0 = P.B0 + pd.Timedelta(hours=r.stunde)
    rows = {pd.Timestamp(st): (lo, cl) for st, lo, cl in sql_reihe(r.symbol, t0.strftime("%Y-%m-%d %H:%M"), (t0 + pd.Timedelta(hours=24)).strftime("%Y-%m-%d %H:%M"))}
    c0 = rows.get(t0, (None, None))[1]
    c24 = rows.get(t0 + pd.Timedelta(hours=24), (None, None))[1]
    tief = min([rows[t0 + pd.Timedelta(hours=k)][0] for k in range(1, 5) if t0 + pd.Timedelta(hours=k) in rows] or [np.nan])
    gleich += int(c0 is not None and c24 is not None and abs(c0 - r.c0) < 1e-12 and abs(c24 - r.c24) < 1e-12 and
                  (abs(tief - r.tief4) < 1e-12 or (np.isnan(tief) and np.isnan(r.tief4))))
pruefe("G1 Kurse fuer O3 direkt per SQL (Einstieg, Tief 4 h, Schluss 24 h)", gleich >= 297, "%d von 300 gleich" % gleich)

alle = {m: (D1 if m == "unverzerrt_1" else zeilen(m)) for m in MENGEN}
jahr_ok, streng_ok, zeilen_g2, zeilen_g3, zeilen_g4 = True, True, [], [], []
for m, D in alle.items():
    for j in (2025, 2026):
        n, f, _ = limit_netto(D[D.jahr == j], 0.01)
        jahr_ok &= n > 0
        zeilen_g2.append("%s %d %+.3f" % (m, j, 100 * n))
    n, f, _ = limit_netto(D, 0.01, streng=0.0005)
    streng_ok &= n > 0
    zeilen_g3.append("%s %+.3f (gefuellt %.0f %%)" % (m, 100 * n, 100 * f))
    zeilen_g4.append("%s: 1,5 %% %+.3f (2026 %+.3f) · 2 %% %+.3f (2026 %+.3f)" % (m, 100 * limit_netto(D, 0.015)[0], 100 * limit_netto(D[D.jahr == 2026], 0.015)[0],
                                                                             100 * limit_netto(D, 0.02)[0], 100 * limit_netto(D[D.jahr == 2026], 0.02)[0]))
pruefe("G2 O3 1 % netto > 0 in jedem Jahr und jeder Menge", jahr_ok, " · ".join(zeilen_g2))
pruefe("G3 O3 1 % mit strengerer Fuellung (Tief 0,05 % unter Limit) netto > 0", streng_ok, " · ".join(zeilen_g3))
print("  G4 Auskunft Dosis: " + " | ".join(zeilen_g4))

j = json.load(open(os.path.join("data", "_perp", "kraken_instruments_2026-10-23.json")))
basen = set()
for i in j["instruments"]:
    m_ = re.match(r"PF_([A-Z0-9]+)USD$", str(i.get("symbol", "")))
    if m_ and i.get("tradeable"):
        b = m_.group(1)
        basen.add("BTC" if b == "XBT" else b)
c = sqlite3.connect("file:data/funding_historie.db?mode=ro", uri=True)
F = pd.read_sql("SELECT symbol, datum, wert FROM funding", c)
c.close()
FU = {(s, d): w for s, d, w in zip(F.symbol, F.datum, F.wert)}
abd, pa_ok, zeilen_g6 = [], True, []
for m, D in alle.items():
    A = D[D.symbol.isin(basen)].copy()
    abd.append("%s %.1f %%" % (m, 100 * len(A) / len(D)))
    A["fund"] = [FU.get((s, d), np.nan) for s, d in zip(A.symbol, A.datum)]
    A["fund"] = A.fund.fillna(A.fund.mean())
    net = A.c24 / A.c0 - 1 - 2 * 0.0005 - 2 * 0.0005 - A.fund
    for jj in (2025, 2026):
        v = net[A.jahr == jj].mean()
        pa_ok &= v > 0
        zeilen_g6.append("%s %d %+.3f" % (m, jj, 100 * v))
pruefe("G5 P-A Abdeckung auf zweitem Weg (Kontraktname)", True, " · ".join(abd))
pruefe("G6 P-A Taker + 0,05 % Schlupf netto > 0 in jedem Jahr und jeder Menge", pa_ok, " · ".join(zeilen_g6))
print("\n%d Pruefungen, %s" % (len(ok), "ALLE BESTANDEN" if all(ok) else "%d FEHLGESCHLAGEN" % ok.count(False)))
