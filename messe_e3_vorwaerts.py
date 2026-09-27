# -*- coding: utf-8 -*-
"""E3: VORWAERTS rechnen - rollierend kalibriert, Monat fuer Monat geprueft.

**27.09.2026.** Nutzervorgaben: *"2021 und 2022 waren Krypto-Anfang mit sehr
vielen Extremen - haette fuer unseren Massstab eher 2024 bis heute 2026
gesehen, auch was die Kalibrierung und Kontrolle betrifft. Wenn wir gut nach
vorne rechnen oder simulieren koennen, gerne."* Und: *"das System soll auf
Basis unserer Bewertung in JEDEM Regime funktionieren - wenn nicht, dann
reden wir."*

VORAB FESTGELEGT
    Pruefmonate   2024-01 bis 2026-08 (Terminmarkt und Funding enden
                  Anfang September 2026)
    Kalibrierung  fuer jeden Pruefmonat NUR die 12 Monate davor: daraus die
                  Schwellen (Perzentile). Der Pruefmonat ist fuer seine
                  Kalibrierung unberuehrt.
    Kandidaten    klein und vorab (keine Suche in diesem Werkzeug):
        R1  ema_abstand_atr hoch P95 & funding_vortag tief P10   (E2b)
        R2  konten_verh tief P5                                  (E2)
        R3  rsi hoch P99                                         (E2)
        S1  vola_kausal hoch P95 & top_konten_verh tief P1       (E2c/E2d)
        S2  vola_kausal hoch P95 & konten_verh tief P1
        S3  vola_kausal hoch P99 & konten_verh tief P5
        S2b / S3b  wie S2 / S3, NUR wenn BTC in den letzten 24 h gefallen ist
                   (offene Hypothese aus 2.657)
        N1  konten_verh hoch P99 - GEGENPROBE, muss negativ sein (2.655)
        je V0 (beim Erscheinen) und V1 (1 h spaeter, Kurs seither gestiegen)
    Ausgang       binnen 120 h: +20 % zuerst -> +20, -10 % zuerst -> -10,
                  sonst Kurs nach 120 h (wie E2d). Je Asset hoechstens ein
                  Einstieg in 24 h. Gleichstand in einer Stunde = -10 % zuerst.
    Bezug         das EIGENE Asset im SELBEN Monat: Vorsprung = EW der
                  Einstiege minus EW desselben Symbols ueber alle Stunden des
                  Monats. Der Monat traegt sein Regime mit.
    Nullwelt      symboltreu im selben Monat, 40 Ziehungen, Bestes-von-N
                  ueber alle Kandidaten und Varianten.
    REGIME        je Quartal, und nach BTC-Monatsrendite (steigend > +5 %,
                  fallend < -5 %, sonst seitwaerts).

NUR LESEND. Kein Stop, kein Trailing. Keine Gebuehren, keine Finanzierung
(Regel 2). Ebene B (2.641).
"""
from __future__ import annotations

import os
import sqlite3
import sys
from datetime import datetime

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
from messe_e2c_grosse_bewegungen import btc_merkmale              # noqa: E402

W = 120
ABSTAND_H = 24
ZIEHUNGEN, SAAT = 40, 20261001
KANDIDATEN = (
    ("R1", (("ema_abstand_atr", ">=", 95), ("funding_vortag", "<=", 10)), False),
    ("R2", (("konten_verh", "<=", 5),), False),
    ("R3", (("rsi", ">=", 99),), False),
    ("S1", (("vola_kausal", ">=", 95), ("top_konten_verh", "<=", 1)), False),
    ("S2", (("vola_kausal", ">=", 95), ("konten_verh", "<=", 1)), False),
    ("S3", (("vola_kausal", ">=", 99), ("konten_verh", "<=", 5)), False),
    ("S2b", (("vola_kausal", ">=", 95), ("konten_verh", "<=", 1)), True),
    ("S3b", (("vola_kausal", ">=", 99), ("konten_verh", "<=", 5)), True),
    ("N1", (("konten_verh", ">=", 99),), False),
)


def monat_von(std):
    """Stunden seit 2020-01-01 -> Monatsindex (Jahr*12 + Monat-1)."""
    basis = np.datetime64("2020-01-01T00")
    t = basis + std.astype("timedelta64[h]")
    j = t.astype("datetime64[Y]").astype(int) + 1970
    m = t.astype("datetime64[M]").astype(int) % 12
    return j * 12 + m


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 124)
    print("E3 - VORWAERTS: rollierend kalibriert (12 Monate davor), Monat "
          "fuer Monat geprueft, 2024-01 bis 2026-08")
    print("=" * 124)
    print("  Ausgang +20 / -10 / sonst Kurs nach %d h · Bezug: eigenes Asset "
          "im selben Monat · je Asset ein Einstieg in %d h" % (W, ABSTAND_H))
    print()
    D = E2.lade(hmax=W, erste=(("up20", 1.20, True), ("dn10", 0.90, False)))
    F, T = D["F"], D["T"]
    SYM, STD, CC, syms, n = D["SYM"], D["STD"], D["CC"], D["syms"], D["n"]
    nsym = int(SYM.max()) + 1
    MON = monat_von(STD)

    # Kurs nach W Stunden
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
    g = (T["up20"] <= W) & (T["up20"] < T["dn10"])
    k = (T["dn10"] <= W) & (T["dn10"] <= T["up20"])
    EW = np.where(g, 20.0, np.where(k, -10.0, 100.0 * END))

    B = btc_merkmale()
    btc24 = np.array([B.get(int(s), (np.nan,))[0] for s in STD])

    # BTC-Monatsrendite fuer die Regime-Einteilung
    c = sqlite3.connect("file:%s?mode=ro" % E2.STUNDEN_DB, uri=True)
    rows = c.execute("SELECT stunde, close FROM stundenkurse WHERE symbol='BTC' "
                     "ORDER BY stunde").fetchall()
    c.close()
    bstd = np.array([int((datetime.strptime(r[0], "%Y-%m-%d %H:%M") - basis)
                         .total_seconds() // 3600) for r in rows], np.int64)
    bcc = np.array([r[1] for r in rows], float)
    bmon = monat_von(bstd)
    btc_monat = {}
    for mm in np.unique(bmon):
        x = bcc[bmon == mm]
        btc_monat[int(mm)] = x[-1] / x[0] - 1.0

    # Hilfen: Vorgaenger, Nachfolger, Entzerrung
    ordnung = np.lexsort((STD, SYM))
    vor1 = np.full(n, -1, np.int64)
    gl = (SYM[ordnung][1:] == SYM[ordnung][:-1]) & (np.diff(STD[ordnung]) == 1)
    vor1[ordnung[1:][gl]] = ordnung[:-1][gl]
    nach1 = np.full(n, -1, np.int64)
    nach1[ordnung[:-1][gl]] = ordnung[1:][gl]

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

    pruefmonate = [j * 12 + m for j in (2024, 2025, 2026) for m in range(12)
                   if j * 12 + m <= 2026 * 12 + 7]

    # je Pruefmonat die Signale aller Kandidaten (Schwellen aus 12 Monaten davor)
    ERG = {(kn, v): np.zeros(n, bool) for kn, _b, _btc in KANDIDATEN for v in ("V0", "V1")}
    for pm in pruefmonate:
        kal = (MON >= pm - 12) & (MON < pm)
        im = MON == pm
        schw = {}
        for kn, bed, nur_btc in KANDIDATEN:
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
    ERG = {key: entzerren(mm) for key, mm in ERG.items()}

    # Grund-EW je Symbol und Monat (alle Stunden des Monats)
    sm = SYM.astype(np.int64) * 10000 + MON
    u, inv = np.unique(sm, return_inverse=True)
    grund = (np.bincount(inv, weights=EW) / np.maximum(np.bincount(inv), 1))[inv]

    # symboltreue Nullwelt im selben Monat
    rng = np.random.default_rng(SAAT)
    o = np.argsort(sm, kind="stable")
    su = sm[o]
    anfang = np.searchsorted(su, u, "left")
    laenge = np.searchsorted(su, u, "right") - anfang

    def ziehe(mm):
        ii = inv[mm]
        r = (rng.random(len(ii)) * laenge[ii]).astype(np.int64)
        return o[anfang[ii] + r]

    schluessel = list(ERG)
    null = np.zeros((ZIEHUNGEN, len(schluessel)))
    for zi in range(ZIEHUNGEN):
        for i, key in enumerate(schluessel):
            mm = ERG[key]
            if mm.sum() == 0:
                continue
            idx = ziehe(mm)
            null[zi, i] = (EW[idx] - grund[idx]).mean()
    mu, sd = null.mean(axis=0), np.maximum(null.std(axis=0, ddof=1), 1e-9)
    zgr = float(np.percentile(np.max((null - mu) / sd, axis=1), 90))

    # ══ GESAMT ══════════════════════════════════════════════════════
    print("=" * 124)
    print("GESAMT ueber alle Pruefmonate (jeder Monat gegen seine eigene "
          "Kalibrierung) · z-Grenze Bestes-von-%d: %.2f" % (len(schluessel), zgr))
    print("     %-7s %6s %5s %5s | %6s %6s %6s | %7s %7s %8s %6s | %s"
          % ("Lage", "Einst.", "Mon.", "Sym.", "P+20", "P-10", "q", "EW %",
             "Grund", "Vorspr.", "z", "Quartale mit Vorsprung > 0"))
    quartale = sorted({(pm // 12, (pm % 12) // 3) for pm in pruefmonate})
    for i, key in enumerate(schluessel):
        mm = ERG[key]
        ne = int(mm.sum())
        if ne < 10:
            print("     %-7s %6d  (zu wenig)" % ("%s%s" % key, ne))
            continue
        pg, pk = g[mm].mean(), k[mm].mean()
        vor = (EW[mm] - grund[mm]).mean()
        z = (vor - mu[i]) / sd[i]
        q_ok, q_n = 0, 0
        for jq in quartale:
            mq = mm & (MON // 12 == jq[0]) & ((MON % 12) // 3 == jq[1])
            if mq.sum() >= 5:
                q_n += 1
                q_ok += int((EW[mq] - grund[mq]).mean() > 0)
        print("     %-7s %6d %5d %5d | %5.1f%% %5.1f%% %6.3f | %+7.2f %+7.2f %+8.2f %6.2f%s | %d von %d"
              % ("%s%s" % key, ne, len(np.unique(MON[mm])), len(np.unique(SYM[mm])),
                 100 * pg, 100 * pk, pg / max(pg + pk, 1e-12), EW[mm].mean(),
                 grund[mm].mean(), vor, z, "*" if z > zgr else " ", q_ok, q_n))
    print("     * = ueber der Bestes-von-%d-Grenze · N1 ist die Gegenprobe und "
          "muss NEGATIV sein" % len(schluessel))
    print()

    # ══ REGIME ══════════════════════════════════════════════════════
    print("=" * 124)
    print("REGIME - Vorsprung (EW minus Grund) nach BTC-Monatslage des "
          "Einstiegsmonats")
    lage = np.array([("steigend" if btc_monat.get(int(x), 0) > 0.05 else
                      "fallend" if btc_monat.get(int(x), 0) < -0.05 else
                      "seitwaerts") for x in MON])
    zaehl = {r: sum(1 for pm in pruefmonate if
                    (btc_monat.get(pm, 0) > 0.05 and r == "steigend") or
                    (btc_monat.get(pm, 0) < -0.05 and r == "fallend") or
                    (-0.05 <= btc_monat.get(pm, 0) <= 0.05 and r == "seitwaerts"))
             for r in ("steigend", "seitwaerts", "fallend")}
    print("     Pruefmonate je Lage: " + " · ".join("%s %d" % kv for kv in zaehl.items()))
    print("     %-7s | %-24s | %-24s | %-24s" % ("Lage", "BTC steigend", "BTC seitwaerts", "BTC fallend"))
    for key in schluessel:
        mm = ERG[key]
        teile = []
        for r in ("steigend", "seitwaerts", "fallend"):
            x = mm & (lage == r)
            if x.sum() < 10:
                teile.append("%4d  (zu wenig)         " % int(x.sum()))
            else:
                pg, pk = g[x].mean(), k[x].mean()
                teile.append("%4d q %.2f Vorspr %+5.2f" % (int(x.sum()), pg / max(pg + pk, 1e-12),
                                                          (EW[x] - grund[x]).mean()))
        print("     %-7s | %s | %s | %s" % ("%s%s" % key, teile[0], teile[1], teile[2]))
    print()

    # ══ QUARTALE ════════════════════════════════════════════════════
    print("=" * 124)
    print("QUARTALE - Vorsprung je Quartal (Einstiege in Klammern)")
    print("     %-7s " % "Lage" + " ".join("%11s" % ("%d/Q%d" % (j, q + 1)) for j, q in quartale))
    for key in schluessel:
        mm = ERG[key]
        zellen = []
        for jq in quartale:
            mq = mm & (MON // 12 == jq[0]) & ((MON % 12) // 3 == jq[1])
            zellen.append("%+5.1f(%3d)" % ((EW[mq] - grund[mq]).mean(), int(mq.sum()))
                          if mq.sum() >= 5 else "    -      ")
        print("     %-7s " % ("%s%s" % key) + " ".join("%11s" % z for z in zellen))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
