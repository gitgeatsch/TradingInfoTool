# -*- coding: utf-8 -*-
"""Gegenpruefung von E3 (2.659): rechnet die Messanlage fuenfmal unter Bedingungen,
deren Ausgang VORHER feststeht.

**27.09.2026.** Nutzerfrage: *"mach noch eine Gegenpruefung der letzten
Messungen - hast du das durchgefuehrt?"* - zum Teil. Hier der fehlende Teil.

    P1  SELBSTPROBE    dieselbe Rechnung wie E3 muss dieselben Zahlen liefern
    P2  MERKMALE 1 h AELTER  (Wert von t-1) - Ergebnisse muessen AEHNLICH
                       bleiben; sonst hing etwas am letzten Stundenwert
    P3  ABSICHTLICHER VORGRIFF (Wert von t+1) - Ergebnisse MUESSEN deutlich
                       steigen; sonst koennte die Anlage einen Vorgriff gar
                       nicht bemerken
    P4  ETIKETTENTAUSCH  Ausgaenge innerhalb Symbol und Monat vertauscht -
                       alles muss bei null liegen, nichts ueber dem Band
    P5  FEHLALARM      50 Zufallslagen mit der Monatsverteilung von R1V0 -
                       hoechstens rund 10 Prozent duerfen ueber dem Band liegen

Die Kernrechnung ist die aus `messe_e3_vorwaerts.py`, hier als Funktion.
P2/P3 verschieben nur die ASSET-Merkmale; der BTC-Kontext bleibt (er ist
nicht Gegenstand der Lage). NUR LESEND. Ebene B.
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
import messe_e3_vorwaerts as E3                                   # noqa: E402
from messe_e2c_grosse_bewegungen import btc_merkmale              # noqa: E402

W, ABSTAND_H, ZIEHUNGEN = E3.W, E3.ABSTAND_H, E3.ZIEHUNGEN
ZUFALL_N = 50


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 118)
    print("GEGENPRUEFUNG E3 (2.659) - fuenf Laeufe mit vorher bekanntem Ausgang")
    print("=" * 118)
    D = E2.lade(hmax=W, erste=(("up20", 1.20, True), ("dn10", 0.90, False)))
    F0, T = D["F"], D["T"]
    SYM, STD, CC, syms, n = D["SYM"], D["STD"], D["CC"], D["syms"], D["n"]
    MON = E3.monat_von(STD)
    cs = sqlite3.connect("file:%s?mode=ro" % E2.STUNDEN_DB, uri=True)
    basis = datetime(2020, 1, 1)
    END = np.empty(n)
    for si in np.unique(SYM):
        rows = cs.execute("SELECT stunde, close FROM stundenkurse WHERE "
                          "symbol=? ORDER BY stunde", (syms[si],)).fetchall()
        st = np.array([int((datetime.strptime(r[0], "%Y-%m-%d %H:%M") - basis)
                           .total_seconds() // 3600) for r in rows], np.int64)
        cc = np.array([r[1] for r in rows], float)
        m = SYM == si
        p = np.searchsorted(st, STD[m])
        END[m] = cc[p + W] / cc[p] - 1.0
    cs.close()
    G0 = (T["up20"] <= W) & (T["up20"] < T["dn10"])
    K0 = (T["dn10"] <= W) & (T["dn10"] <= T["up20"])
    EW0 = np.where(G0, 20.0, np.where(K0, -10.0, 100.0 * END))
    B = btc_merkmale()
    btc24 = np.array([B.get(int(s), (np.nan,))[0] for s in STD])

    ordnung = np.lexsort((STD, SYM))
    gl = (SYM[ordnung][1:] == SYM[ordnung][:-1]) & (np.diff(STD[ordnung]) == 1)
    vor1 = np.full(n, -1, np.int64)
    vor1[ordnung[1:][gl]] = ordnung[:-1][gl]
    nach1 = np.full(n, -1, np.int64)
    nach1[ordnung[:-1][gl]] = ordnung[1:][gl]
    pruefmonate = [j * 12 + m for j in (2024, 2025, 2026) for m in range(12)
                   if j * 12 + m <= 2026 * 12 + 7]
    sm = SYM.astype(np.int64) * 10000 + MON
    u, inv = np.unique(sm, return_inverse=True)
    o = np.argsort(sm, kind="stable")
    su = sm[o]
    anfang = np.searchsorted(su, u, "left")
    laenge = np.searchsorted(su, u, "right") - anfang

    def entzerren(mm):
        idx = np.flatnonzero(mm)
        idx = idx[np.lexsort((STD[idx], SYM[idx]))]
        behalten, ls, lt = [], -1, -10 ** 9
        for i in idx:
            if SYM[i] != ls or STD[i] - lt >= ABSTAND_H:
                behalten.append(i)
                ls, lt = SYM[i], STD[i]
        aus = np.zeros(n, bool)
        if behalten:
            aus[np.array(behalten, np.int64)] = True
        return aus

    def signale(F):
        ERG = {(kn, v): np.zeros(n, bool) for kn, _b, _x in E3.KANDIDATEN
               for v in ("V0", "V1")}
        for pm in pruefmonate:
            kal = (MON >= pm - 12) & (MON < pm)
            im = MON == pm
            schw = {}
            for kn, bed, nur_btc in E3.KANDIDATEN:
                mm = np.ones(n, bool)
                for m, op, q in bed:
                    if (m, q) not in schw:
                        schw[(m, q)] = float(np.nanpercentile(F[m][kal], q))
                    v = F[m]
                    with np.errstate(invalid="ignore"):
                        mm &= np.isfinite(v) & ((v >= schw[(m, q)]) if op == ">="
                                                else (v <= schw[(m, q)]))
                if nur_btc:
                    mm &= np.isfinite(btc24) & (btc24 <= 0)
                war = np.zeros(n, bool)
                ok = vor1 >= 0
                war[ok] = mm[vor1[ok]]
                beginn = mm & ~war & im
                ERG[(kn, "V0")] |= beginn
                v1 = np.zeros(n, bool)
                ok2 = beginn & (nach1 >= 0)
                ziel = nach1[ok2]
                steigt = CC[ziel] > CC[np.flatnonzero(ok2)]
                v1[ziel[steigt]] = True
                ERG[(kn, "V1")] |= v1 & im
        return {key: entzerren(mm) for key, mm in ERG.items()}

    def bewerte(ERG, EW, saat):
        grund = (np.bincount(inv, weights=EW) / np.maximum(np.bincount(inv), 1))[inv]
        rng = np.random.default_rng(saat)
        keys = list(ERG)
        null = np.zeros((ZIEHUNGEN, len(keys)))
        for zi in range(ZIEHUNGEN):
            for i, key in enumerate(keys):
                mm = ERG[key]
                if mm.sum() == 0:
                    continue
                ii = inv[mm]
                r = (rng.random(len(ii)) * laenge[ii]).astype(np.int64)
                idx = o[anfang[ii] + r]
                null[zi, i] = (EW[idx] - grund[idx]).mean()
        mu, sd = null.mean(axis=0), np.maximum(null.std(axis=0, ddof=1), 1e-9)
        zgr = float(np.percentile(np.max((null - mu) / sd, axis=1), 90))
        aus = {}
        for i, key in enumerate(keys):
            mm = ERG[key]
            vor = (EW[mm] - grund[mm]).mean() if mm.sum() else np.nan
            aus[key] = (int(mm.sum()), vor, (vor - mu[i]) / sd[i])
        return aus, zgr

    def verschoben(zeiger):
        F = {}
        for m, v in F0.items():
            w = np.full(n, np.nan)
            ok = zeiger >= 0
            w[ok] = v[zeiger[ok]]
            F[m] = w
        return F

    laeufe = {}
    print("  P1 Selbstprobe ...", flush=True)
    E_orig = signale(F0)
    laeufe["P1 Selbstprobe"] = bewerte(E_orig, EW0, E3.SAAT)
    print("  P2 Merkmale 1 h aelter ...", flush=True)
    laeufe["P2 1 h aelter"] = bewerte(signale(verschoben(vor1)), EW0, E3.SAAT)
    print("  P3 absichtlicher Vorgriff ...", flush=True)
    laeufe["P3 Vorgriff +1 h"] = bewerte(signale(verschoben(nach1)), EW0, E3.SAAT)
    print("  P4 Etikettentausch ...", flush=True)
    rng = np.random.default_rng(20261002)
    perm = np.arange(n)
    for a, l_ in zip(anfang, laenge):
        seg = o[a:a + l_]
        perm[seg] = rng.permutation(seg)
    laeufe["P4 Etiketten vertauscht"] = bewerte(E_orig, EW0[perm], E3.SAAT)

    keys = list(E_orig)
    print()
    print("=" * 118)
    print("VORSPRUNG je Kandidat (Prozentpunkte, * = ueber der Bestes-von-18-Grenze)")
    kopf = "     %-7s" % "Lage" + "".join("%24s" % name for name in laeufe)
    print(kopf)
    for key in keys:
        zeile = "     %-7s" % ("%s%s" % key)
        for name, (aus, zgr) in laeufe.items():
            ne, vor, z = aus[key]
            zeile += "%11d %+7.2f%s    " % (ne, vor, "*" if z > zgr else " ")
        print(zeile)
    print("     Grenzen: " + " · ".join("%s %.2f" % (name, zgr)
                                        for name, (_a, zgr) in laeufe.items()))
    print()
    ref = laeufe["P1 Selbstprobe"][0]
    e3 = {("S3b", "V1"): (128, 4.84), ("S1", "V1"): (77, 3.43),
          ("N1", "V0"): (674, -1.06), ("R1", "V0"): (1987, 0.12)}
    ok1 = all(ref[k_][0] == ne and abs(ref[k_][1] - v) < 0.006 for k_, (ne, v) in e3.items())
    print("  P1 gegen die E3-Ausgabe (4 Stichproben): %s" % ("✔ identisch" if ok1 else "⛔ ABWEICHUNG"))
    a3 = laeufe["P3 Vorgriff +1 h"][0]
    hoeher = sum(1 for k_ in keys if a3[k_][1] > ref[k_][1])
    print("  P3 Vorgriff hebt den Vorsprung bei %d von %d Kandidaten" % (hoeher, len(keys)))
    a4, z4 = laeufe["P4 Etiketten vertauscht"]
    ueber = sum(1 for k_ in keys if a4[k_][2] > z4)
    print("  P4 nach dem Tausch ueber dem Band: %d von %d · groesster |Vorsprung| %.2f"
          % (ueber, len(keys), max(abs(a4[k_][1]) for k_ in keys)))

    # P5 Fehlalarm: Zufallslagen mit der Monatsverteilung von R1V0
    print()
    print("  P5 Fehlalarm - %d Zufallslagen ..." % ZUFALL_N, flush=True)
    vorlage = E_orig[("R1", "V0")]
    je_monat = {int(pm): int((vorlage & (MON == pm)).sum()) for pm in pruefmonate}
    rng = np.random.default_rng(20261003)
    zufall = {}
    for zi in range(ZUFALL_N):
        mm = np.zeros(n, bool)
        for pm, c in je_monat.items():
            ids = np.flatnonzero(MON == pm)
            if c and len(ids):
                mm[rng.choice(ids, size=min(c, len(ids)), replace=False)] = True
        zufall[("Z%02d" % zi, "")] = entzerren(mm)
    az, zgz = bewerte(zufall, EW0, 20261004)
    zgr1 = laeufe["P1 Selbstprobe"][1]
    fa = sum(1 for k_ in az if az[k_][2] > zgr1)
    print("  P5 Zufallslagen ueber der E3-Grenze (%.2f): %d von %d (%.0f Prozent) · "
          "Vorsprung Mittel %+.2f, Spanne %+.2f bis %+.2f"
          % (zgr1, fa, ZUFALL_N, 100.0 * fa / ZUFALL_N,
             np.mean([v[1] for v in az.values()]),
             min(v[1] for v in az.values()), max(v[1] for v in az.values())))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
