"""P82 VORANALYSE ROBUSTHEIT REGEL0 (24.10.2026, Nutzer: *"Voranalyse Robustheit starten"*, E-136) - nur MECHANISMUS und RAUSCHEN.

    python -X utf8 Basisinfos/Rechenkern_02_10/p82_robustheit_voranalyse.py

Keine neue Ertragsmessung je Variante (die kommt erst mit dem Messplan). Gerechnet wird:
 D1  Datenbeginn je Symbol: Messbasis (data/) gegen data/_hist - Gruppen (a) Start 2021-12 mit Historie davor, (b) spaeter gestartet,
     Binance hatte aber frueher Kurse (abgeschnitten), (c) ohne fruehere Kurse (Start = Listing)
 D2  je Monat 2023-01..2026-08, Referenz gegen lang: reife Assets in BASIS, Trainingsmenge des Monatsmodells (Anker / Treffer),
     Querschnitt der Schrumpfung (Assets im Vormonat), Marktmitte und tau2
 D3  Herkunft der Einstiege 2024-26: Anteil aus Assets, die in der Referenz zu dem Zeitpunkt NICHT reif waren (Gruppe b/a)
 R1  Rauschen der schon gemessenen Zahlen (E-136): Tagesblock-Bootstrap (7-Tage-Bloecke, 2.000 Ziehungen) fuer netto je Handel der
     Referenz, von Lauf A und der Differenz auf denselben Tagen
Liest nur (data/ und data/_hist/ mode=ro); schreibt nichts ausser der Ausgabe.
"""
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd

HIER = os.path.dirname(os.path.abspath(__file__))
WURZEL = os.path.dirname(os.path.dirname(HIER))
sys.path.insert(0, HIER)
sys.path.insert(0, WURZEL)
os.chdir(WURZEL)
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass
import agent.regel0_rechnung as R0  # noqa: E402
import p79_f1_fg_gier as P79  # noqa: E402

K2 = R0.K2
GRUPPE = os.path.join("data", "_vergleich", "kern48jbz_gruppe_bestand.csv")
REF = os.path.join("data", "_vergleich", "kern48jbz_einstiege_bestand.csv")


def lauf(ordner, zus):
    A = R0.anker(R0.lade_reihen(ordner, zus), zukunft_bekannt=True)
    R = R0.rechne(A, set(zus), K2.ROLL_MONATE)
    return A, R


def basis(R, zus):
    SYM, STD = R["SYM"], R["STD"]
    btc = R["syms"].index("BTC") if "BTC" in R["syms"] else -1
    grid = np.isin(STD % 24, K2.GITTER)
    return grid & np.isfinite(R["OFF"]) & R["REIF"] & (SYM != btc) & ~R["ZUS"]


def main():
    zus = R0.zusatz_aus_gruppe(GRUPPE)
    print("P82 VORANALYSE ROBUSTHEIT REGEL0 · %s\n" % datetime.now().strftime("%Y-%m-%d %H:%M"))
    Ar, Rr = lauf("data", zus)
    Al, Rl = lauf(os.path.join("data", "_hist"), zus)
    # ── D1 Datenbeginn ──────────────────────────────────────────────────────────────────────────────────────────────────
    st0r = {Rr["syms"][s]: int(Ar["STD"][Ar["SYM"] == s].min()) for s in np.unique(Ar["SYM"])}
    st0l = {Rl["syms"][s]: int(Al["STD"][Al["SYM"] == s].min()) for s in np.unique(Al["SYM"])}
    grp = {}
    for s in st0r:
        a, b = st0r[s], st0l.get(s, st0r[s])
        tr = R0._stunde_txt(a)[:7]
        grp[s] = "c" if b >= a - 24 * 30 else ("a" if tr == "2021-12" else "b")
    g = pd.Series(grp)
    print("D1 Datenbeginn je Symbol (Messbasis gegen lang): (a) Start 2021-12, Historie davor: %d · (b) spaeter gestartet, Binance hatte "
          "frueher Kurse: %d · (c) ohne fruehere Kurse: %d" % ((g == "a").sum(), (g == "b").sum(), (g == "c").sum()))
    b_ = sorted(s for s in g.index if g[s] == "b")
    print("    (b): " + ", ".join("%s %s->%s" % (s, R0._stunde_txt(st0r[s])[:7], R0._stunde_txt(st0l[s])[:7]) for s in b_[:40]))
    # ── D2 je Monat ─────────────────────────────────────────────────────────────────────────────────────────────────────
    Br, Bl = basis(Rr, zus), basis(Rl, zus)
    print("\nD2 je Monat: reife Assets in BASIS · Trainingsmenge des Monatsmodells (Anker/Treffer, ab 2023-01 bis Monat-24 h) · "
          "Schrumpfung Vormonat (Assets, Mitte, tau2)")
    print("    %-7s | %14s | %22s | %30s" % ("Monat", "reif ref/lang", "Training ref / lang", "Schrumpfung ref / lang"))
    ab = K2._h(datetime(2023, 1, 1))
    for (j, mo) in [(2023, m) for m in (1, 4, 7, 10)] + K2.ROLL_MONATE:
        mi = j * 12 + mo - 1
        start = K2._h(datetime(j, mo, 1))
        z = []
        for R, B in ((Rr, Br), (Rl, Bl)):
            reif = len(np.unique(R["SYM"][B & (R["MON"] == mi)]))
            hit = ((R["t_u"] <= 24) | (R["t_d"] <= 24))
            fen = B & (R["STD"] >= ab) & (R["MON"] < mi) & (R["STD"] < start - 24)
            us = len(np.unique(R["SYM"][B & (R["MON"] == mi - 1)]))
            lg = R["lage"].get(mi)
            z.append((reif, int(fen.sum()), int((fen & hit).sum()), us, lg))
        if (j, mo) in K2.ROLL_MONATE and mo not in (1, 4, 7, 10):
            continue
        f = lambda l: "-" if l is None else "%.3f/%.4f" % l   # noqa: E731
        print("    %d-%02d | %5d / %5d | %8d/%6d / %8d/%6d | %3d %s / %3d %s" % (
            j, mo, z[0][0], z[1][0], z[0][1], z[0][2], z[1][1], z[1][2], z[0][3], f(z[0][4]), z[1][3], f(z[1][4])))
    # ── D3 Herkunft der Einstiege ───────────────────────────────────────────────────────────────────────────────────────
    a = pd.read_csv(os.path.join("data", "_hist", "einstiege_A.csv"), sep=";")
    b = pd.read_csv(REF, sep=";")
    m = a.merge(b, on=["symbol", "stunde"], how="outer", indicator=True)
    reif_ref = {}
    for s in np.unique(Rr["SYM"]):
        ix = (Rr["SYM"] == s) & Rr["REIF"]
        reif_ref[Rr["syms"][s]] = int(Rr["STD"][ix].min()) if ix.any() else None
    m["gruppe"] = m.symbol.map(grp).fillna("zusatz")
    m["jung_in_ref"] = [(reif_ref.get(s) is None or st < reif_ref[s]) for s, st in zip(m.symbol, m.stunde)]
    print("\nD3 Herkunft der Einstiege 2024-26 (Anzahl; jung = in der Referenz zu dem Zeitpunkt noch nicht reif)")
    for k, n in (("both", "gemeinsam"), ("left_only", "nur lang"), ("right_only", "nur Referenz")):
        x = m[m._merge == k]
        print("    %-12s %6d · Gruppe a %5d / b %5d / c %5d / Zusatz %4d · jung in der Referenz %5d (%.0f %%)" % (
            n, len(x), (x.gruppe == "a").sum(), (x.gruppe == "b").sum(), (x.gruppe == "c").sum(), (x.gruppe == "zusatz").sum(),
            int(x.jung_in_ref.sum()), 100 * x.jung_in_ref.mean()))
    # ── R1 Rauschen ─────────────────────────────────────────────────────────────────────────────────────────────────────
    tage = pd.date_range("2024-01-01", "2026-08-31", freq="D")
    P79.TAGE = tage
    sr, nr, _ = P79.tagesreihe(b)
    sl, nl, _ = P79.tagesreihe(a)
    rng = np.random.default_rng(82)
    nb = len(tage) // 7
    z = np.empty((2000, 3))
    for i in range(2000):
        st = rng.integers(0, len(tage) - 7, nb)
        ix = (st[:, None] + np.arange(7)).ravel()
        r_, l_ = sr[ix].sum() / nr[ix].sum(), sl[ix].sum() / nl[ix].sum()
        z[i] = r_, l_, l_ - r_
    echt = (sr.sum() / nr.sum(), sl.sum() / nl.sum())
    print("\nR1 Rauschen (7-Tage-Bloecke, 2.000 Ziehungen, 2024-01..2026-08):")
    for name, w, k in (("Referenz", echt[0], 0), ("Lauf A (lang)", echt[1], 1), ("Differenz lang - Referenz", echt[1] - echt[0], 2)):
        lo, hi = np.percentile(z[:, k], [2.5, 97.5])
        print("    %-26s %+.3f %%  [%+.3f; %+.3f]  Anteil > 0: %.1f %%" % (name, 100 * w, 100 * lo, 100 * hi, 100 * np.mean(z[:, k] > 0)))
    for j in (2024, 2025, 2026):
        mk = tage.year == j
        print("    %d: Referenz %+.3f %% (%d) · lang %+.3f %% (%d)" % (j, 100 * sr[mk].sum() / nr[mk].sum(), nr[mk].sum(),
                                                                       100 * sl[mk].sum() / nl[mk].sum(), nl[mk].sum()))


if __name__ == "__main__":
    main()
