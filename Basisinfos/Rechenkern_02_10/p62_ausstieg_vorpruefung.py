"""P62 Punkt 2 - Ausstieg und Haltedauer auf den REGEL0-Einstiegen (18.10.2026). VORAB FESTGELEGT in Schritt7 §23.68. Nur lesend.

    python Basisinfos/Rechenkern_02_10/p62_ausstieg_vorpruefung.py

Einstieg = Schluss der Einstiegsstunde (Referenz-Spalte ``stunde``). Kurse: stundenkurse.db, stundenkurse_alle.db, eingestellt_historie.db
(die erste Datei gewinnt). Nur Einstiege mit lueckenlosen 168 h danach - in jeder Zelle dieselbe Menge.
  Zellen   H24 H48 H72 H120 H168 (ohne Stop) · S5_24 S8_24 (Stop -5 / -8 % ueber 24 h) · S8_168 (Stop -8 %, hoechstens 7 Tage)
  Kosten   0,30 % + 0,18 % je Tag auf den Positionswert
  Haupt    gepaart netto: Zelle - H24; Tagesblock cluster-robust 99 % (agent.regel0_messstand._kennzahl)
  Urteil   besser / schlechter: Intervall > 0 bzw. < 0 in 2025 UND 2026 und in >= 3 von 4 Mengen; sonst nicht unterscheidbar
  Auskunft Tief binnen Haltedauer <= -20 % / -33 % (Liquidationsnaehe 5x / 3x); 2024
"""
import os
import sqlite3
import sys

import numpy as np
import pandas as pd

WURZEL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
import agent.regel0_messstand as MS  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
DATEIEN = ("stundenkurse.db", "stundenkurse_alle.db", "eingestellt_historie.db")
MENGEN = ("bestand", "unverzerrt_1", "unverzerrt_2", "unverzerrt_3")
H_MAX = 168
ZELLEN = (("H24", 24, None), ("H48", 48, None), ("H72", 72, None), ("H120", 120, None), ("H168", 168, None),
          ("S5_24", 24, 0.05), ("S8_24", 24, 0.08), ("S8_168", 168, 0.08))
KOSTEN_FIX, KOSTEN_TAG = 0.0030, 0.0018
B0 = pd.Timestamp("2020-01-01")
_cache = {}
_con = {d: sqlite3.connect("file:data/%s?mode=ro" % d, uri=True) for d in DATEIEN if os.path.exists(os.path.join("data", d))}


def reihe(sym):
    """-> (stunde_ab, high, low, close) als Arrays je Stunde seit B0 (Luecken NaN), aus allen Dateien, die erste gewinnt."""
    if sym in _cache:
        return _cache[sym]
    d = {}
    for name, c in _con.items():
        for st, h, lo, cl in c.execute("SELECT stunde, high, low, close FROM stundenkurse WHERE symbol=?", (sym,)):
            d.setdefault(st, (h, lo, cl))
    if not d:
        _cache[sym] = None
        return None
    hs = ((pd.to_datetime(list(d.keys())) - B0) / pd.Timedelta(hours=1)).astype(int).to_numpy()
    a = hs.min()
    n = hs.max() - a + 1
    H, L, C = (np.full(n, np.nan) for _ in range(3))
    v = np.array(list(d.values()), float)
    H[hs - a], L[hs - a], C[hs - a] = v[:, 0], v[:, 1], v[:, 2]
    _cache[sym] = (a, H, L, C)
    return _cache[sym]


def zellen_fuer(e):
    """Je Einstieg: brutto je Zelle und Tief-Kennzahlen, oder None ohne lueckenlose 168 h."""
    r = reihe(e.symbol)
    if r is None:
        return None
    a, H, L, C = r
    i = int(e.stunde) - a
    if i < 0 or i + H_MAX >= len(C):
        return None
    c0 = C[i]
    hh, ll, cc = H[i + 1:i + H_MAX + 1], L[i + 1:i + H_MAX + 1], C[i + 1:i + H_MAX + 1]
    if not np.isfinite(c0) or c0 <= 0 or not (np.isfinite(hh).all() and np.isfinite(ll).all() and np.isfinite(cc).all()):
        return None
    aus = {}
    for name, h, s in ZELLEN:
        if s is None:
            aus[name] = (cc[h - 1] / c0 - 1, h)
        else:
            treffer = np.flatnonzero(ll[:h] <= c0 * (1 - s))
            aus[name] = ((-s, int(treffer[0]) + 1) if len(treffer) else (cc[h - 1] / c0 - 1, h))
    tief = {h: float(ll[:h].min() / c0 - 1) for h in (24, 168)}
    return aus, tief


def netto(brutto, stunden):
    return brutto - KOSTEN_FIX - KOSTEN_TAG * stunden / 24.0


print("P62 PUNKT 2 · Ausstieg und Haltedauer auf den REGEL0-Einstiegen · vorab §23.68 · Kosten 0,30 %% + 0,18 %%/Tag · Band %.0f %%\n"
      % (100 * MS.NIVEAU))
urteil = {name: [] for name, _h, _s in ZELLEN if name != "H24"}
for menge in MENGEN:
    E = pd.read_csv(os.path.join("data", "_vergleich", "kern48jbz_einstiege_%s.csv" % menge), sep=";")
    zeilen = []
    for e in E.itertuples():
        z = zellen_fuer(e)
        if z is None:
            continue
        aus, tief = z
        zeilen.append(dict(jahr=e.jahr, tag=int(e.stunde) // 24, **{n_: v[0] for n_, v in aus.items()},
                           **{n_ + "_h": v[1] for n_, v in aus.items()}, tief24=tief[24], tief168=tief[168]))
    D = pd.DataFrame(zeilen)
    U = D[D.jahr >= 2025]
    print("=" * 118)
    print("%s: %d Einstiege mit 168 h (von %d), Urteil 2025-26 %d an %d Tagen" % (menge, len(D), len(E), len(U), U.tag.nunique()))
    print("   %-7s %10s %10s   %-34s %-26s %-26s %s" % ("Zelle", "brutto", "netto", "gepaart netto - H24 (2025-26, 99 %)", "2025", "2026", "Urteil"))
    for name, h, s in ZELLEN:
        bru = U[name].mean()
        net_ = netto(U[name], U[name + "_h"]).mean()
        if name == "H24":
            print("   %-7s %+9.3f%% %+9.3f%%   (Bezug)" % (name, 100 * bru, 100 * net_))
            continue
        diff = netto(U[name], U[name + "_h"]) - netto(U["H24"], U["H24_h"])
        kz = {j: MS._kennzahl(list(zip(U.tag[U.jahr == j], diff[U.jahr == j], [0] * int((U.jahr == j).sum())))) for j in (2025, 2026)}
        kg = MS._kennzahl(list(zip(U.tag, diff, [0] * len(U))))
        txt = lambda k: "%+.2f [%+.2f; %+.2f]" % (100 * k["mittel"], 100 * (k["mittel"] - k["halb"]), 100 * (k["mittel"] + k["halb"]))  # noqa: E731
        bes = all(k["mittel"] - k["halb"] > 0 for k in kz.values())
        sch = all(k["mittel"] + k["halb"] < 0 for k in kz.values())
        u = "besser" if bes else ("schlechter" if sch else "nicht unterscheidbar")
        urteil[name].append(u)
        print("   %-7s %+9.3f%% %+9.3f%%   %-34s %-26s %-26s %s" % (name, 100 * bru, 100 * net_, txt(kg), txt(kz[2025]), txt(kz[2026]), u))
    lq = "   Auskunft Tief <= -20 %% / -33 %%: binnen 24 h %.1f / %.1f %% der Einstiege · binnen 168 h %.1f / %.1f %%" % (
        100 * (U.tief24 <= -0.20).mean(), 100 * (U.tief24 <= -0.33).mean(), 100 * (U.tief168 <= -0.20).mean(), 100 * (U.tief168 <= -0.33).mean())
    print(lq)
    steig = [netto(U[n_], U[n_ + "_h"]).mean() for n_ in ("H24", "H48", "H72", "H120", "H168")]
    print("   netto je Haltedauer 24/48/72/120/168 h: %s  -> je weiterem Tag im Mittel %+.3f %% (24 -> 168 h)" % (
        " / ".join("%+.3f %%" % (100 * x) for x in steig), 100 * (steig[-1] - steig[0]) / 6))
    if menge == "bestand":
        print("   R-R11 H24 brutto 2025-26 %+.3f %% (p61: +0,545 %% auf allen Einstiegen mit 24 h; hier nur mit 168 h)" % (100 * U.H24.mean()))
    V = D[D.jahr == 2024]
    print("   Auskunft 2024: brutto H24 %+.3f %% · H168 %+.3f %% · S8_168 %+.3f %% · netto H24 %+.3f %% · H168 %+.3f %%" % (
        100 * V.H24.mean(), 100 * V.H168.mean(), 100 * V.S8_168.mean(), 100 * netto(V.H24, V.H24_h).mean(), 100 * netto(V.H168, V.H168_h).mean()))
print("\nURTEIL JE ZELLE ueber die vier Mengen (vorab: >= 3 von 4):")
for name, us in urteil.items():
    b = us.count("besser")
    s = us.count("schlechter")
    print("   %-7s %s -> %s" % (name, " · ".join(us), "BESSER als 24 h" if b >= 3 else ("SCHLECHTER als 24 h" if s >= 3 else "nicht unterscheidbar")))
