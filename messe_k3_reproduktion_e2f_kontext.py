# -*- coding: utf-8 -*-
"""R-R11 zu K3: die Kontextzeile aus E2f (2.665) EXAKT reproduzieren, dann gegen die Zeitverschiebung halten.

**28.09.2026.** K3 (messe_k3_kontextflaeche.py) findet die Sperre *BTC 24 h
steigt UND Dominanz steigt* nicht (Drittel-Felder, Phase, Tagesanker). Um den
registrierten Wert (E2f: q5 Dq -0,020, z -6,9, Menge bestand) umzustossen, muss
er ZUERST reproduziert werden (R-R11). Hier dieselbe Rechnung wie E2f:
Menge bestand, dieselben Anker (E2.lade, 2023-01 bis 2026-08), dieselbe
Episodenregel (erster Anker je Asset in 24 h), derselbe Moment-Bezug, BTC aus
stundenkurse.db (damals erst ab 2023-09) - dann dieselbe Zahl gegen
(a) die E2f-Nullwelt (Episoden-Ziehung) und (b) die Zeitverschiebung.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import messe_e2_beitraege as E2                                   # noqa: E402
import messe_e2f_richtungsdaten as F                              # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402
from messe_e2c_grosse_bewegungen import btc_merkmale              # noqa: E402


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    E2.MENGE = "bestand"
    D = E2.lade(hmax=72, erste=(("up15", 1.15, True), ("dn15", 0.85, False)), ab=F.AB, bis=F.BIS)
    SYM, STD = D["SYM"], D["STD"]
    A5 = D["Z"][24]["auf5"].astype(np.int8); B5 = D["Z"][24]["ab5"].astype(np.int8)
    del D
    n = len(SYM); MON = monat_von(STD)
    SM = SYM.astype(np.int64) * 1000 + (MON - MON.min())
    _u, sm_i = np.unique(SM, return_inverse=True)
    sm_n = np.maximum(np.bincount(sm_i), 1)
    a0 = np.bincount(sm_i, weights=A5) / sm_n; b0 = np.bincount(sm_i, weights=B5) / sm_n
    ordnung = np.lexsort((STD, SYM))

    def entzerren(maske):
        idx = ordnung[maske[ordnung]]
        aus = np.zeros(n, bool); ls, lt = -1, -10 ** 9
        for i in idx:
            if SYM[i] != ls or STD[i] - lt >= 24:
                aus[i] = True; ls, lt = SYM[i], STD[i]
        return aus

    def dq(e):
        a, b = A5[e].mean(), B5[e].mean()
        return a / (a + b) - a0[sm_i[e]].mean() / (a0[sm_i[e]].mean() + b0[sm_i[e]].mean())

    # Kontext wie in E2f: btc24 aus btc_merkmale (stundenkurse.db), btcdom aus richtung_historie
    import sqlite3
    BM = btc_merkmale()
    btc24 = np.array([BM.get(int(s), (np.nan,))[0] for s in STD])
    dom = sqlite3.connect("file:%s?mode=ro" % F.RICHTUNG_DB, uri=True).execute(
        "SELECT stunde, close FROM btcdom ORDER BY stunde").fetchall()
    hd = F._stunden([x[0] for x in dom]); dc = np.full(hd.max() - hd.min() + 1, np.nan)
    dc[hd - hd.min()] = [x[1] for x in dom]
    vor = np.concatenate([np.full(24, np.nan), dc[:-24]])
    ae = dc / vor - 1.0
    p = STD - hd.min(); ok = (p >= 0) & (p < len(ae))
    dom24 = np.full(n, np.nan); dom24[ok] = ae[p[ok]]
    alle = np.isfinite(btc24) & np.isfinite(dom24)
    zeilen = (("BTC 24h > 0 UND Dominanz 24h > 0 (2.601-Sperre)", lambda b, d: (b > 0) & (d > 0), -0.020),
              ("BTC 24h > 0 UND Dominanz 24h < 0", lambda b, d: (b > 0) & (d < 0), -0.003))
    rng = np.random.default_rng(20261006)
    # Zeitverschiebung: die Kontextwerte je STUNDE gegen die Anker verschieben
    stunden = np.unique(STD[alle])
    pos = np.searchsorted(stunden, STD)
    b_h = np.full(len(stunden), np.nan); d_h = np.full(len(stunden), np.nan)
    b_h[pos[alle]] = btc24[alle]; d_h[pos[alle]] = dom24[alle]
    print("R-R11 - E2f-Kontextzeilen exakt nachgerechnet (Menge bestand, E2f-Anker und -Episoden)")
    for name, f, soll in zeilen:
        e = entzerren(alle & f(btc24, dom24))
        w = dq(e)
        null = []
        for _ in range(40):
            v = int(rng.integers(60 * 24, len(stunden) - 60 * 24))
            bs, ds = np.roll(b_h, v)[pos], np.roll(d_h, v)[pos]
            m = alle & np.isfinite(bs) & np.isfinite(ds) & f(bs, ds)
            null.append(dq(entzerren(m)))
        null = np.array(null)
        print("  %-48s Dq %+.4f (registriert %+.3f) · Episoden %d · Zeitverschiebung: Mittel %+.4f, "
              "Streuung %.4f, z %+.2f" % (name, w, soll, e.sum(), null.mean(), null.std(ddof=1),
                                          (w - null.mean()) / null.std(ddof=1)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
