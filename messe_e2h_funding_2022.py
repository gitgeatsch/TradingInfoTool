# -*- coding: utf-8 -*-
"""E2h: funding auf UNBERUEHRTEN Daten (2022) - und woher der alte gute Ruf kam.

**27.09.2026.** Nutzer: *"dann 2022 fuer funding pruefen"* und *"bisher war
angeblich funding ein guter Beitrag"*. E2f (2.665) hat die zwei
funding-Auswahlen auf 2023-01 bis 2026-08 GESUCHT; die Such-/Pruef-Trennung
fehlte. Und 2.663 zeigt auf +15 %/12 h noch Lift 4,45, E2f auf derselben
Frage (q15) nichts - der Unterschied liegt im BEZUG, und das ist messbar.

VORAB FESTGELEGT
    Schwellen   die Perzentile 5 und 95 von funding_vortag aus 2023-01 bis
                2026-08 (dem Suchzeitraum von E2f) - NICHT aus 2022
    Pruefzeit   2021-12 bis 2022-12 (vor dem Suchzeitraum; in 2.651/2.655
                breit mitgemessen, in der Suche von E2f nicht)
    Zielgroesse q5 (+5 vor -5 Prozent, 24 h) wie in E2f, dazu q15
    Bezug       STRENG (eigenes Asset im selben Monat) und daneben LOCKER
                (eigenes Asset ueber alle Zeit) und MARKT (alle Anker) -
                derselbe Satz Episoden, nur der Vergleich wechselt
    Pruefung    Nullwelt symboltreu im Monat, 40 Ziehungen, zweiseitig;
                je Monat; P2 (1 h aelter); P4 (Tausch in Symbol und Monat)
    HAELT       wenn auf q5 streng: z > 2 in der Richtung von E2f, die Mehrheit
                der Monate mit demselben Vorzeichen, P2 gleiches Vorzeichen,
                P4 |z| < 2
    ZUSATZ      die Form von 2.651: funding_vortag <= -0,0040 auf q15, in
                BEIDEN Zeitraeumen und allen drei Bezuegen

NUR LESEND (`mode=ro`). Kein Stop, kein Trailing, keine Gebuehren (Regel 2).
"""
from __future__ import annotations

import os
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402

B0 = datetime(2020, 1, 1)


def _h(d):
    return int((d - B0).total_seconds() // 3600)


SUCHE = (_h(datetime(2023, 1, 1)), _h(datetime(2026, 9, 1)))
PRUEF = (_h(datetime(2021, 12, 1)), _h(datetime(2023, 1, 1)))
ZIEHUNGEN, SAAT = 40, 20261004
ABSTAND_H = 24


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 110)
    print("E2h - funding auf UNBERUEHRTEN Daten (2021-12 bis 2022-12) und "
          "der Bezug als Erklaerung des alten Rufs")
    print("=" * 110)
    D = E2.lade(hmax=72, erste=(("up15", 1.15, True), ("dn15", 0.85, False)))
    SYM, STD = D["SYM"], D["STD"]
    FU = D["F"]["funding_vortag"]
    A5 = D["Z"][24]["auf5"].astype(np.int8)
    B5 = D["Z"][24]["ab5"].astype(np.int8)
    U15 = (D["T"]["up15"] <= 12).astype(np.int8)
    D15 = (D["T"]["dn15"] <= 12).astype(np.int8)
    del D
    n = len(SYM)
    MON = monat_von(STD)
    rng = np.random.default_rng(SAAT)
    suche = (STD >= SUCHE[0]) & (STD < SUCHE[1])
    pruef = (STD >= PRUEF[0]) & (STD < PRUEF[1])
    ok = np.isfinite(FU)
    sw5 = float(np.percentile(FU[suche & ok], 5))
    sw95 = float(np.percentile(FU[suche & ok], 95))
    print("  Schwellen aus dem SUCHzeitraum: P5 %.6f · P95 %.6f" % (sw5, sw95))
    print("  Anker: Suche %d · Pruefung %d (Symbole %d)" % (
        suche.sum(), pruef.sum(), len(np.unique(SYM[pruef]))))

    SM = SYM.astype(np.int64) * 1000 + (MON - MON.min())
    _u, sm_i = np.unique(SM, return_inverse=True)
    sm_anz = np.maximum(np.bincount(sm_i), 1)
    nsym = int(SYM.max()) + 1
    # lockerer Bezug je Zeitraum getrennt, damit er nicht aus dem anderen
    # Zeitraum lernt
    PAAR = {"q5": (A5, B5), "q15": (U15, D15)}

    def basen(zeit):
        aus = {}
        for z, (xa, xb) in PAAR.items():
            a_sm = np.bincount(sm_i, weights=xa * zeit) / np.maximum(
                np.bincount(sm_i, weights=zeit.astype(float)), 1)
            b_sm = np.bincount(sm_i, weights=xb * zeit) / np.maximum(
                np.bincount(sm_i, weights=zeit.astype(float)), 1)
            ns = np.maximum(np.bincount(SYM, weights=zeit.astype(float),
                                        minlength=nsym), 1)
            a_s = np.bincount(SYM, weights=xa * zeit, minlength=nsym) / ns
            b_s = np.bincount(SYM, weights=xb * zeit, minlength=nsym) / ns
            a_m, b_m = xa[zeit].mean(), xb[zeit].mean()
            aus[z] = (a_sm, b_sm, a_s, b_s, a_m, b_m)
        return aus

    BS = {"suche": basen(suche), "pruef": basen(pruef)}

    def q(a, b):
        return a / (a + b) if a + b > 0 else np.nan

    def dq(e, z, zeitname, bezug, perm=None):
        if e.sum() == 0:
            return np.nan
        xa, xb = PAAR[z]
        if perm is not None:
            xa, xb = xa[perm], xb[perm]
        a_sm, b_sm, a_s, b_s, a_m, b_m = BS[zeitname][z]
        w = q(xa[e].mean(), xb[e].mean())
        if bezug == "streng":
            return w - q(a_sm[sm_i[e]].mean(), b_sm[sm_i[e]].mean())
        if bezug == "locker":
            return w - q(a_s[SYM[e]].mean(), b_s[SYM[e]].mean())
        return w - q(a_m, b_m)

    ordnung = np.lexsort((STD, SYM))

    def entzerren(maske):
        idx = ordnung[maske[ordnung]]
        aus = np.zeros(n, bool)
        ls, lt = -1, -10 ** 9
        for i in idx:
            if SYM[i] != ls or STD[i] - lt >= ABSTAND_H:
                aus[i] = True
                ls, lt = SYM[i], STD[i]
        return aus

    o_sm = np.argsort(sm_i, kind="stable")
    sm_start = np.searchsorted(sm_i[o_sm], np.arange(len(_u)), "left")

    def ziehe(e):
        s = sm_i[e]
        r = (rng.random(len(s)) * sm_anz[s]).astype(np.int64)
        return o_sm[sm_start[s] + r]

    def z_streng(e, z, zeitname):
        w = dq(e, z, zeitname, "streng")
        nz = []
        for _ in range(ZIEHUNGEN):
            ee = np.zeros(n, bool); ee[ziehe(e)] = True
            nz.append(dq(ee, z, zeitname, "streng"))
        return w, (w - np.nanmean(nz)) / max(np.nanstd(nz, ddof=1), 1e-12)

    vor1 = np.full(n, -1, np.int64)
    gl = (SYM[ordnung][1:] == SYM[ordnung][:-1]) & (np.diff(STD[ordnung]) == 1)
    vor1[ordnung[1:][gl]] = ordnung[:-1][gl]
    FU1 = np.full(n, np.nan); FU1[vor1 >= 0] = FU[vor1[vor1 >= 0]]
    perm = np.arange(n)
    for s0 in range(len(_u)):
        a = o_sm[sm_start[s0]:sm_start[s0] + sm_anz[s0]]
        perm[a] = rng.permutation(a)

    AUSW = (("F5  funding <= P5", lambda v: v <= sw5, +1),
            ("F95 funding >= P95", lambda v: v >= sw95, -1),
            ("2.651-Form funding <= -0,0040", lambda v: v <= -0.0040, +1))
    for zeitname, zeit in (("suche", suche), ("pruef", pruef)):
        print()
        print("-" * 110)
        print("%s  (%s)" % ("SUCHZEITRAUM 2023-01 bis 2026-08" if zeitname == "suche"
                            else "PRUEFZEITRAUM 2021-12 bis 2022-12 - unberuehrt von E2f",
                            zeitname))
        print("  %-32s %-4s %6s | %7s %7s %7s | %6s | %7s %7s | %s" % (
            "Auswahl", "Ziel", "Epis.", "streng", "locker", "Markt", "z str",
            "P2 1h-", "P4 tau", "Monate gleiches Vorzeichen"))
        for name, f, erwartet in AUSW:
            fin = np.isfinite(FU)
            e = entzerren(zeit & fin & f(np.where(fin, FU, 0)))
            fin1 = np.isfinite(FU1)
            e1 = entzerren(zeit & fin1 & f(np.where(fin1, FU1, 0)))
            for z in ("q5", "q15"):
                w, zz = z_streng(e, z, zeitname)
                mon = [dq(e & (MON == mm), z, zeitname, "streng")
                       for mm in np.unique(MON[e]) if (e & (MON == mm)).sum() >= 20]
                gleich = sum(int(np.sign(x) == erwartet) for x in mon if np.isfinite(x))
                print("  %-32s %-4s %6d | %+7.3f %+7.3f %+7.3f | %+6.1f | %+7.3f %+7.3f | %d von %d"
                      % (name, z, int(e.sum()), w,
                         dq(e, z, zeitname, "locker"), dq(e, z, zeitname, "markt"),
                         zz, dq(e1, z, zeitname, "streng"),
                         dq(e, z, zeitname, "streng", perm), gleich, len(mon)))
    print()
    print("  streng = gegen das eigene Asset im selben Monat · locker = gegen das "
          "eigene Asset im ganzen Zeitraum · Markt = gegen alle Anker")
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
