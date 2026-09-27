# -*- coding: utf-8 -*-
"""E2e: GEGENPRUEFUNG der HOEHE aus 2.655 - nach dem Pflichtablauf.

**27.09.2026.** 2.655 meldet: *die Beitraege sagen die HOEHE der Bewegung
stark voraus* (vola_kausal, oi_je_umsatz, oi_aenderung, volumenschub). Das
ist die Grundlage fuer die HEBELHOEHE. Es fehlten: Vorwaertsrechnung,
Gegenpruefung, und - laut der eigenen Basis - Jahre, Weglassprobe und
Asset-Anteil fuer die Hoehe (sie waren nur fuer die Richtung gerechnet).
Nutzerauftrag: *alles bisherige pruefen und gegenpruefen, falls noch nicht
erfolgt - sauber und langsam, bis wir die Grundlagen haben.*

VORAB FESTGELEGT (vor dem ersten Lauf, nicht nachgestellt)
    Kandidaten   vola_kausal, oi_je_umsatz, oi_aenderung, volumenschub,
                 je Perzentil 1 / 5 / 95 / 99 - 16 Auswahlen, nur diese
    Zielgroessen mfe (groesster Anstieg) und maevp (Rueckgang vor dem Hoch),
                 Prozentpunkte, Lehrer-Fenster 24 h (6 / 72 h als Kontrolle)
    Schritt 0    REPRODUKTION (R-R11): Stunden, Bezug eigenes Symbol ueber
                 alle Zeit - genau die Rechnung von E2. Muss 2.655 ergeben.
    Bezug        STRENG: das eigene Asset im SELBEN MONAT. Vola haeuft sich
                 in der Zeit; wer gegen das ganze Leben des Assets misst,
                 misst den Monat mit. Der lockere Bezug laeuft daneben.
    Episoden     je Asset hoechstens ein Anker in 24 h (die Lage haelt
                 Stunden an - Stunden waeren abhaengige Wiederholungen)
    Nullwelt     symboltreu im selben Monat, 40 Ziehungen; Grenze
                 Bestes-von-16 je Zielgroesse, zweiseitig, 90. Perzentil
    Stabilitaet  je Kalenderjahr, Weglassprobe je Jahr, Anteil der Assets
                 (mind. 10 Episoden) mit gleichem Vorzeichen
    Vorwaerts    Pruefmonate 2024-01 bis 2026-08, Schwellen NUR aus den 12
                 Monaten davor; je Quartal und je BTC-Monatslage
    Gegenproben  P2 Merkmale 1 h aelter (muss halten), P3 1 h aus der
                 Zukunft (zeigt, ob die Anlage einen Vorgriff sieht),
                 P4 Ausgaenge innerhalb Symbol und Monat vertauscht (muss
                 in das Band fallen)
    TRAEGT       wenn ALLES gilt: jenseits der Grenze (streng, Episoden),
                 Jahre >= n-1, Weglass alle, Assets >= 60 %, vorwaerts in
                 >= 75 % der Monate und in JEDER BTC-Lage dasselbe
                 Vorzeichen, P2 dasselbe Vorzeichen mit >= halber Groesse,
                 P4 innerhalb des Bandes

NUR LESEND (`mode=ro`). Kein Stop, kein Trailing, keine Gebuehren (Regel 2).
Ebene B (2.641).
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402

KANDIDATEN = ("vola_kausal", "oi_je_umsatz", "oi_aenderung", "volumenschub")
PERZ = (1, 5, 95, 99)
ZIELE = ("mfe", "maevp")
H = 24
ABSTAND_H = 24
ZIEHUNGEN, SAAT = 40, 20261002
MIN_ASSET = 10
PRUEF_AB = 2024 * 12 + 0
PRUEF_BIS = 2026 * 12 + 7


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 120)
    print("E2e - GEGENPRUEFUNG DER HOEHE (2.655): Reproduktion, strenger "
          "Bezug, Episoden, Stabilitaet, vorwaerts, Gegenproben")
    print("=" * 120)
    D = E2.lade()
    F, Z, SYM, STD, JAHR = D["F"], D["Z"], D["SYM"], D["STD"], D["JAHR"]
    n = D["n"]
    nsym = int(SYM.max()) + 1
    MON = monat_von(STD)
    rng = np.random.default_rng(SAAT)
    print("  %d Anker · %d Symbole · Monate %d bis %d" % (
        n, len(np.unique(SYM)), MON.min(), MON.max()))

    # ── Bezug: eigenes Symbol (locker) und eigenes Symbol im Monat (streng)
    anz = np.maximum(np.bincount(SYM, minlength=nsym), 1)
    SM = SYM.astype(np.int64) * 1000 + (MON - MON.min())
    usm, sm_i = np.unique(SM, return_inverse=True)
    sm_anz = np.maximum(np.bincount(sm_i), 1)

    def basis(zw):
        return (np.bincount(SYM, weights=zw, minlength=nsym) / anz,
                np.bincount(sm_i, weights=zw) / sm_anz)

    B = {f: {z: basis(Z[f][z]) for z in ZIELE} for f in (6, 24, 72)}

    def diff(maske, z, f=H, streng=True, werte=None):
        x = Z[f][z] if werte is None else werte
        b = B[f][z][1][sm_i[maske]] if streng else B[f][z][0][SYM[maske]]
        return float(x[maske].mean() - b.mean()) if maske.any() else np.nan

    # ── Episoden: je Symbol hoechstens ein Anker in 24 h
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

    # symboltreue Ziehung im selben Monat
    o_sm = np.argsort(sm_i, kind="stable")
    s_sorted = sm_i[o_sm]
    sm_start = np.searchsorted(s_sorted, np.arange(len(usm)), "left")

    def ziehe(maske):
        s = sm_i[maske]
        r = (rng.random(len(s)) * sm_anz[s]).astype(np.int64)
        return o_sm[sm_start[s] + r]

    # ── Auswahlen (Schwellen ueber die ganze Menge - wie E2)
    AUS = []
    for m in KANDIDATEN:
        v = F[m]
        ok = np.isfinite(v)
        q = np.percentile(v[ok], PERZ)
        for p, sw in zip(PERZ, q):
            mk = ok & ((v <= sw) if p < 50 else (v >= sw))
            AUS.append((m, p, float(sw), mk))

    # ══ SCHRITT 0: REPRODUKTION ══════════════════════════════════════
    print()
    print("SCHRITT 0 - REPRODUKTION von 2.655 (Stunden, Bezug eigenes Symbol "
          "ueber alle Zeit, 24 h)")
    print("  2.655 meldet: vola_kausal hoch +6,5 / +2,1 · oi_je_umsatz tief "
          "+5,0 / +1,9 · oi_aenderung stark +4,7 / +1,3 · volumenschub hoch "
          "+3,6 / +1,4 (mfe / maevp)")
    print("  %-14s %4s %10s %9s | %8s %8s" % ("Merkmal", "Perz", "Schwelle",
                                             "Stunden", "mfe", "maevp"))
    for m, p, sw, mk in AUS:
        print("  %-14s P%-3d %10.4f %9d | %+8.2f %+8.2f" % (
            m, p, sw, int(mk.sum()), diff(mk, "mfe", streng=False),
            diff(mk, "maevp", streng=False)))

    # ══ SCHRITT 1: STRENG + EPISODEN, Nullwelt ═══════════════════════
    EP = [entzerren(mk) for _m, _p, _sw, mk in AUS]
    wert = {z: np.array([diff(e, z) for e in EP]) for z in ZIELE}
    null = {z: np.zeros((ZIEHUNGEN, len(AUS))) for z in ZIELE}
    for zi in range(ZIEHUNGEN):
        for ai, e in enumerate(EP):
            idx = ziehe(e)
            for z in ZIELE:
                null[z][zi, ai] = (Z[H][z][idx].mean()
                                   - B[H][z][1][sm_i[idx]].mean())
    band = {}
    for z in ZIELE:
        mu = null[z].mean(axis=0)
        sd = np.maximum(null[z].std(axis=0, ddof=1), 1e-12)
        band[z] = (mu, sd, float(np.percentile(
            np.max(np.abs((null[z] - mu) / sd), axis=1), 90)))

    def jenseits(z, ai, w):
        mu, sd, g = band[z]
        return abs((w - mu[ai]) / sd[ai]) > g

    # ══ SCHRITT 2: Gegenproben P2 / P3 / P4 ═════════════════════════
    vor1 = np.full(n, -1, np.int64)
    gl = (SYM[ordnung][1:] == SYM[ordnung][:-1]) & (np.diff(STD[ordnung]) == 1)
    vor1[ordnung[1:][gl]] = ordnung[:-1][gl]
    nach1 = np.full(n, -1, np.int64)
    nach1[ordnung[:-1][gl]] = ordnung[1:][gl]

    def verschoben(zeiger, m):
        v = np.full(n, np.nan)
        ok = zeiger >= 0
        v[ok] = F[m][zeiger[ok]]
        return v

    def auswahl_mit(v, p):
        ok = np.isfinite(v)
        sw = np.percentile(v[ok], p)
        return ok & ((v <= sw) if p < 50 else (v >= sw))

    P2, P3 = {}, {}
    for ai, (m, p, _sw, _mk) in enumerate(AUS):
        e2 = entzerren(auswahl_mit(verschoben(vor1, m), p))
        e3 = entzerren(auswahl_mit(verschoben(nach1, m), p))
        P2[ai] = {z: diff(e2, z) for z in ZIELE}
        P3[ai] = {z: diff(e3, z) for z in ZIELE}
    # P4: Ausgaenge innerhalb Symbol und Monat vertauschen
    perm = np.arange(n)
    for s0 in range(len(usm)):
        a = o_sm[sm_start[s0]:sm_start[s0] + sm_anz[s0]]
        perm[a] = rng.permutation(a)
    P4 = {ai: {z: diff(e, z, werte=Z[H][z][perm]) for z in ZIELE}
          for ai, e in enumerate(EP)}

    # ══ SCHRITT 3: Jahre, Weglass, Assets ═══════════════════════════
    def stabil(e, z, vz):
        jahre = [j for j in np.unique(JAHR[e]) if (e & (JAHR == j)).sum() >= 30]
        j_ok = sum(int(vz * diff(e & (JAHR == j), z) > 0) for j in jahre)
        w_ok = sum(int(vz * diff(e & (JAHR != j), z) > 0) for j in jahre)
        d = Z[H][z][e] - B[H][z][1][sm_i[e]]
        je = np.bincount(SYM[e], weights=d, minlength=nsym)
        jn = np.bincount(SYM[e], minlength=nsym)
        g = jn >= MIN_ASSET
        a = float(np.mean(vz * je[g] > 0)) if g.any() else np.nan
        return j_ok, len(jahre), w_ok, a, int(g.sum())

    # ══ SCHRITT 4: VORWAERTS ═══════════════════════════════════════
    cs = sqlite3.connect("file:%s?mode=ro" % E2.STUNDEN_DB, uri=True)
    rows = cs.execute("SELECT stunde, close FROM stundenkurse WHERE "
                      "symbol='BTC' ORDER BY stunde").fetchall()
    cs.close()
    b0 = datetime(2020, 1, 1)
    bstd = np.array([int((datetime.strptime(r[0], "%Y-%m-%d %H:%M") - b0)
                         .total_seconds() // 3600) for r in rows], np.int64)
    bcc = np.array([r[1] for r in rows], float)
    bmon = monat_von(bstd)
    btc_lage = {}
    for mm in np.unique(bmon):
        x = bcc[bmon == mm]
        r = x[-1] / x[0] - 1.0
        btc_lage[int(mm)] = ("steigend" if r > 0.05 else
                             "fallend" if r < -0.05 else "seitwaerts")
    monate = [mm for mm in range(PRUEF_AB, PRUEF_BIS + 1) if (MON == mm).any()]

    def vorwaerts(m, p, z):
        v = F[m]
        aus = {}
        for mm in monate:
            kal = (MON >= mm - 12) & (MON < mm) & np.isfinite(v)
            if kal.sum() < 1000:
                continue
            sw = np.percentile(v[kal], p)
            im = (MON == mm) & np.isfinite(v)
            mk = im & ((v <= sw) if p < 50 else (v >= sw))
            e = entzerren(mk)
            if e.sum() >= 20:
                aus[mm] = (diff(e, z), int(e.sum()))
        return aus

    # ══ AUSGABE ════════════════════════════════════════════════════
    print()
    print("=" * 120)
    print("SCHRITT 1 bis 4 - STRENG (eigenes Asset im selben Monat), "
          "EPISODEN (1 je Asset in 24 h), Lehrer 24 h")
    print("  Grenze Bestes-von-%d, z: %s" % (len(AUS), " · ".join(
        "%s %.2f" % (z, band[z][2]) for z in ZIELE)))
    print("  %-14s %4s %6s | %7s %7s | %7s %7s | %6s %6s %5s | %7s %7s %7s | %s" % (
        "Merkmal", "Perz", "Epis.", "mfe", "maevp", "6h mfe", "72h mfe",
        "Jahre", "Wegl", "Asset", "P2 1h-", "P3 1h+", "P4 tau", "Vorwaerts mfe"))
    urteile = []
    for ai, (m, p, sw, mk) in enumerate(AUS):
        e = EP[ai]
        w = {z: wert[z][ai] for z in ZIELE}
        st = {z: jenseits(z, ai, w[z]) for z in ZIELE}
        vz = 1.0 if w["mfe"] > 0 else -1.0
        j_ok, j_n, w_ok, a, a_n = stabil(e, "mfe", vz)
        vw = vorwaerts(m, p, "mfe")
        vm = [d for d, _k in vw.values()]
        vm_ok = sum(int(vz * d > 0) for d in vm)
        lagen = {}
        for mm, (d, _k) in vw.items():
            lagen.setdefault(btc_lage.get(mm, "?"), []).append(d)
        lage_ok = all(vz * np.mean(x) > 0 for x in lagen.values()) and lagen
        p2 = P2[ai]["mfe"]; p3 = P3[ai]["mfe"]; p4 = P4[ai]["mfe"]
        p4_im_band = not jenseits("mfe", ai, p4)
        traegt = (st["mfe"] and j_n >= 3 and j_ok >= j_n - 1 and w_ok == j_n
                  and a >= 0.6 and len(vm) >= 12 and vm_ok >= 0.75 * len(vm)
                  and lage_ok and vz * p2 > 0 and abs(p2) >= 0.5 * abs(w["mfe"])
                  and p4_im_band)
        urteile.append((m, p, traegt, w, vz, lagen, vm_ok, len(vm)))
        print("  %-14s P%-3d %6d | %+6.2f%s %+6.2f%s | %+7.2f %+7.2f | %2d/%-3d %2d/%-3d %4.0f%% | %+7.2f %+7.2f %+7.2f | %2d/%-2d %s" % (
            m, p, int(e.sum()),
            w["mfe"], "*" if st["mfe"] else " ",
            w["maevp"], "*" if st["maevp"] else " ",
            diff(e, "mfe", 6), diff(e, "mfe", 72),
            j_ok, j_n, w_ok, j_n, 100 * a if np.isfinite(a) else float("nan"),
            p2, p3, p4, vm_ok, len(vm),
            "✔ TRAEGT" if traegt else "· nein"))
    print()
    print("  VORWAERTS JE BTC-MONATSLAGE (mfe, Mittel der Monatswerte, "
          "Anzahl Monate):")
    for m, p, traegt, w, vz, lagen, vm_ok, vn in urteile:
        print("  %-14s P%-3d  %s" % (m, p, " · ".join(
            "%s %+.2f (%d)" % (k, np.mean(x), len(x))
            for k, x in sorted(lagen.items()))))
    print()
    print("  Grundlage des Marktes (24 h, alle Stunden): mfe %.2f %% · "
          "maevp %.2f %%" % (Z[H]["mfe"].mean(), Z[H]["maevp"].mean()))
    print("  * = jenseits der Grenze (Nullwelt symboltreu im Monat) · P2 muss "
          "halten, P4 muss ins Band fallen · P3 ist ein absichtlicher Vorgriff")
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
