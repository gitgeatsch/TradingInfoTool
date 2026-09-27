# -*- coding: utf-8 -*-
"""E2i: wie oft laeuft der Kurs so weit GEGEN eine Long-Position, dass 5x / 3x / 2x
liquidiert wuerden - getrennt nach der ATR zum Einstieg?

**27.09.2026.** Nutzer zu Punkt 3 (Einheit der Hebelhoehe): *"ohne Kontext
und konkreter Bewertung kann ich dazu noch nichts sagen."* Das hier ist der
Kontext - eine ERHEBUNG ohne Merkmalssuche (wie E1, 2.654), keine Messung
eines Beitrags.

    MAE        groesster Rueckgang unter den Einstiegskurs binnen 24 / 72 h
               (Tiefstkurs der Folgestunden, konservativ), Prozent
    Grenzen    12 / 27 / 45 Prozent - die ORIENTIERUNGSwerte des alten Codes
               fuer die Liquidation bei 5x / 3x / 2x (nicht nachgerechnet,
               nur Groessenordnung)
    Schichten  ATR zum Anker (Tagesmass, kausal) in Fuenfteln ueber alle Anker
    Zeitraum   alle Anker, und je Kalenderjahr zur Stabilitaet

NUR LESEND (`mode=ro`). Keine Gebuehren (Regel 2).
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402

GRENZEN = ((0.12, "5x"), (0.27, "3x"), (0.45, "2x"))
FENSTER = (24, 72)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 100)
    print("E2i - LIQUIDATIONSNAEHE: MAE einer Long-Position binnen 24 / 72 h "
          "nach der ATR zum Einstieg")
    print("=" * 100)
    cs = sqlite3.connect("file:%s?mode=ro" % E2.STUNDEN_DB, uri=True)
    syms = [r[0] for r in cs.execute(
        "SELECT symbol FROM stundenkurse GROUP BY symbol "
        "HAVING COUNT(*) > 2000 ORDER BY COUNT(*) DESC")]
    b0 = datetime(2020, 1, 1)
    ATR, JAHR = [], []
    MAE = {f: [] for f in FENSTER}
    for sym in syms:
        if sym.upper() == "BTC":
            continue
        rows = cs.execute("SELECT stunde, high, low, close FROM stundenkurse "
                          "WHERE symbol=? ORDER BY stunde", (sym,)).fetchall()
        if len(rows) < 500:
            continue
        st = [r[0] for r in rows]
        h = np.array([r[1] for r in rows], float)
        l = np.array([r[2] for r in rows], float)
        cc = np.array([r[3] for r in rows], float)
        std = np.array([int((datetime.strptime(x, "%Y-%m-%d %H:%M") - b0)
                            .total_seconds() // 3600) for x in st], np.int64)
        n = len(cc)
        idx = np.arange(n)
        atr = E2._atr(h, l, cc)
        gu = np.isfinite(atr) & (cc > 0)
        gu[:E2.VORLAUF] = False
        gu[max(0, n - max(FENSTER)):] = False
        nach = np.clip(idx + max(FENSTER), 0, n - 1)
        gu &= (std[nach] - std) == max(FENSTER)
        sel = np.flatnonzero(gu)
        if not len(sel):
            continue
        tief = np.full(n, np.inf)
        for s in range(1, max(FENSTER) + 1):
            tief = np.minimum(tief, l[np.minimum(idx + s, n - 1)])
            if s in FENSTER:
                MAE[s].append((1.0 - tief / cc)[sel])
        ATR.append(atr[sel])
        JAHR.append(np.array([int(st[i][:4]) for i in sel], np.int16))
    cs.close()
    ATR = np.concatenate(ATR); JAHR = np.concatenate(JAHR)
    MAE = {f: np.concatenate(v) for f, v in MAE.items()}
    q = np.percentile(ATR, [20, 40, 60, 80])
    sch = np.searchsorted(q, ATR)
    print("  %d Anker · ATR-Fuenftelgrenzen (Tagesmass): %s" % (
        len(ATR), " · ".join("%.1f%%" % (100 * x) for x in q)))
    for f in FENSTER:
        print()
        print("  FENSTER %d h - Anteil der Einstiege, bei denen der Kurs die "
              "Grenze unterschreitet" % f)
        print("  %-22s %10s | %s | %s" % ("ATR-Schicht", "MAE Median",
                                          "  ".join("%9s" % ("%s %d%%" % (nm, round(100 * g)))
                                                    for g, nm in GRENZEN),
                                          "MAE P95"))
        for s in range(5):
            m = sch == s
            lo = 0 if s == 0 else q[s - 1]
            hi = q[s] if s < 4 else ATR.max()
            print("  S%d ATR %4.1f-%5.1f%%     %9.2f%% | %s | %6.1f%%" % (
                s + 1, 100 * lo, 100 * hi, 100 * np.median(MAE[f][m]),
                "  ".join("%8.3f%%" % (100 * np.mean(MAE[f][m] >= g))
                          for g, _nm in GRENZEN),
                100 * np.percentile(MAE[f][m], 95)))
        print("  %-22s %9.2f%% | %s | %6.1f%%" % (
            "ALLE", 100 * np.median(MAE[f]),
            "  ".join("%8.3f%%" % (100 * np.mean(MAE[f] >= g)) for g, _nm in GRENZEN),
            100 * np.percentile(MAE[f], 95)))
        print("  je Jahr, Anteil MAE >= 12 %% (5x) in S1 / S5: %s" % " · ".join(
            "%d %.2f%% / %.2f%%" % (j, 100 * np.mean(MAE[f][(JAHR == j) & (sch == 0)] >= 0.12),
                                   100 * np.mean(MAE[f][(JAHR == j) & (sch == 4)] >= 0.12))
            for j in np.unique(JAHR) if ((JAHR == j) & (sch == 0)).sum() > 1000))
    print()
    print("  ⚠️ Die Liquidationsgrenzen sind Orientierung aus dem alten Code, "
          "keine nachgerechneten Boersenwerte.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
