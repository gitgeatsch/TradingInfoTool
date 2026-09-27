# -*- coding: utf-8 -*-
"""E2d: Pruefung der Squeeze-Familie aus E2c - "hohe Vola & wenige Longs", bestaetigt.

**27.09.2026.** Nutzerauftrag: *"Pruefung 1 bis 4 so angehen - die
Symbolkonzentration und der Drift ist normal und muss beruecksichtigt
werden - BTC fuehrt in den meisten Faellen und zieht den Markt, Alts
folgen."*

VORAB FESTGELEGT (nichts wird danach nachgestellt):
    Familie   die vier Lagen, die in E2c in der SUCHE (bis 2024) oben standen:
              L1 vola_kausal hoch P95 & top_konten_verh tief P1
              L2 vola_kausal hoch P95 & konten_verh tief P1
              L3 vola_kausal hoch P99 & konten_verh tief P5
              L4 volumenschub hoch P99 & top_konten_verh tief P1
    Varianten V0 Einstieg beim Erscheinen der Lage
              V1 / V3 Einstieg 1 bzw. 3 h spaeter, NUR wenn der Kurs seither
              gestiegen ist (Nutzeridee Bestaetigung)
    Ziel      binnen 120 h: +20 % zuerst -> +20 · -10 % zuerst -> -10 ·
              sonst der Kurs nach 120 h. Daraus der ERWARTUNGSWERT brutto.
    Trennung  Schwellen NUR aus 2021-2023. 2024 ist fuer die Bestaetigung
              UNBERUEHRT. 2025-2026 wird ausgewiesen, ist aber SCHON GESEHEN
              (E2c) und zaehlt nicht als Beleg.

PRUEFUNGEN
    1  UNABHAENGIGE EREIGNISSE: je Asset hoechstens ein Einstieg in 24 h;
       ausgewiesen: Einstiege, Tage, Symbole, Anteil der 5 haeufigsten
       Symbole. Konzentration und Drift sind NORMAL (Nutzer) - sie werden
       gezeigt, nicht bestraft.
    2  VOLLSTAENDIGER AUSGANG: EW je Einstieg gegen den EW DESSELBEN Assets
       zu Zufallszeiten im selben Zeitraum (symboltreu, 40 Ziehungen,
       Bestes-von-12-Band je Zeitraum).
    3  siehe Trennung
    4  RUECKGANG VOR DEM ZIEL: fuer die Treffer die Verteilung des tiefsten
       Kurses vor +20 %; fuer alle Einstiege der tiefste Kurs binnen 120 h.
    +  BTC-KONTEXT: getrennt nach BTC-Rendite der letzten 24 h > 0 oder <= 0.

Gleichstand in einer Stunde = -10 % zuerst (2.583). Kein Stop, kein
Trailing: +20 / -10 / 120 h sind die Messanordnung, nicht die Fuehrung.
Daten wie E2c (`messe_e2_beitraege.lade(hmax=120, ...)`). NUR LESEND.
Keine Gebuehren, keine Finanzierung (Regel 2). Ebene B (2.641).
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
SCHWELLEN_BIS = 2023
ZEITRAEUME = (("2021-2023 (Schwellen)", (2021, 2022, 2023)),
              ("2024 (unberuehrt)", (2024,)),
              ("2025-2026 (schon gesehen)", (2025, 2026)))
LAGEN = (("L1", (("vola_kausal", ">=", 95), ("top_konten_verh", "<=", 1))),
         ("L2", (("vola_kausal", ">=", 95), ("konten_verh", "<=", 1))),
         ("L3", (("vola_kausal", ">=", 99), ("konten_verh", "<=", 5))),
         ("L4", (("volumenschub", ">=", 99), ("top_konten_verh", "<=", 1))))
VARIANTEN = (("V0", 0), ("V1", 1), ("V3", 3))
ABSTAND_H = 24
ZIEHUNGEN, SAAT = 40, 20260930


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 124)
    print("E2d - PRUEFUNG DER SQUEEZE-FAMILIE (hohe Vola & wenige Longs), "
          "Ziel +20 %% / -10 %% / sonst Kurs nach %d h" % W)
    print("=" * 124)
    print("  Schwellen nur aus 2021-2023 · 2024 unberuehrt · 2025-26 schon "
          "gesehen · je Asset hoechstens ein Einstieg in %d h" % ABSTAND_H)
    print()
    D = E2.lade(hmax=W, erste=(("up20", 1.20, True), ("dn10", 0.90, False)))
    F, T = D["F"], D["T"]
    SYM, JAHR, STD, CC = D["SYM"], D["JAHR"], D["STD"], D["CC"]
    syms, n = D["syms"], D["n"]
    nsym = int(SYM.max()) + 1

    # Kurs nach 120 h und Pfade je Anker (aus den Stundenkursen, nur lesend)
    cs = sqlite3.connect("file:%s?mode=ro" % E2.STUNDEN_DB, uri=True)
    basis = datetime(2020, 1, 1)
    reihen = {}
    for si in np.unique(SYM):
        rows = cs.execute("SELECT stunde, high, low, close FROM stundenkurse "
                          "WHERE symbol=? ORDER BY stunde", (syms[si],)).fetchall()
        st = np.array([int((datetime.strptime(r[0], "%Y-%m-%d %H:%M") - basis)
                           .total_seconds() // 3600) for r in rows], np.int64)
        reihen[int(si)] = (st, np.array([r[1] for r in rows], float),
                           np.array([r[2] for r in rows], float),
                           np.array([r[3] for r in rows], float))
    cs.close()
    POS = np.zeros(n, np.int64)
    for si, (st, _h, _l, _c) in reihen.items():
        m = SYM == si
        POS[m] = np.searchsorted(st, STD[m])
    END = np.empty(n)
    for si, (st, _h, _l, cc) in reihen.items():
        m = SYM == si
        END[m] = cc[POS[m] + W] / cc[POS[m]] - 1.0
    g = (T["up20"] <= W) & (T["up20"] < T["dn10"])
    k = (T["dn10"] <= W) & (T["dn10"] <= T["up20"])
    EW = np.where(g, 20.0, np.where(k, -10.0, 100.0 * END))

    # BTC-Kontext
    B = btc_merkmale()
    btc24 = np.array([B.get(int(s), (np.nan,))[0] for s in STD])

    # Schwellen aus 2021-2023
    alt = JAHR <= SCHWELLEN_BIS
    schw = {}
    for _n, bed in LAGEN:
        for m, op, q in bed:
            schw[(m, q)] = float(np.nanpercentile(F[m][alt], q))

    # Nachfolger desselben Symbols k Stunden spaeter
    ordnung = np.lexsort((STD, SYM))
    vor1 = np.full(n, -1, np.int64)
    gl = (SYM[ordnung][1:] == SYM[ordnung][:-1]) & (np.diff(STD[ordnung]) == 1)
    vor1[ordnung[1:][gl]] = ordnung[:-1][gl]
    nach = {}
    for kk in (1, 3):
        o = ordnung
        gl2 = (SYM[o][kk:] == SYM[o][:-kk]) & (STD[o][kk:] - STD[o][:-kk] == kk)
        nach[kk] = (o[:-kk][gl2], o[kk:][gl2])

    def lage_maske(bed):
        mm = np.ones(n, bool)
        for m, op, q in bed:
            v = F[m]
            with np.errstate(invalid="ignore"):
                mm &= np.isfinite(v) & ((v >= schw[(m, q)]) if op == ">="
                                        else (v <= schw[(m, q)]))
        war = np.zeros(n, bool)
        ok = vor1 >= 0
        war[ok] = mm[vor1[ok]]
        return mm & ~war                         # Erscheinen der Lage

    def variante(beginn, kk):
        if kk == 0:
            return beginn
        fr, sp = nach[kk]
        mm = np.zeros(n, bool)
        mm[sp[beginn[fr] & (CC[sp] > CC[fr])]] = True
        return mm

    def entzerren(mm):
        """Je Asset hoechstens ein Einstieg in ABSTAND_H Stunden."""
        idx = np.flatnonzero(mm)
        idx = idx[np.lexsort((STD[idx], SYM[idx]))]
        behalten = []
        letzt_sym, letzt_std = -1, -10 ** 9
        for i in idx:
            if SYM[i] != letzt_sym or STD[i] - letzt_std >= ABSTAND_H:
                behalten.append(i)
                letzt_sym, letzt_std = SYM[i], STD[i]
        aus = np.zeros(n, bool)
        aus[np.array(behalten, np.int64)] = True
        return aus

    # symboltreue Nullwelt je Zeitraum
    rng = np.random.default_rng(SAAT)

    def pool(zr):
        ids = np.flatnonzero(zr)
        o = ids[np.argsort(SYM[ids], kind="stable")]
        so = SYM[o]
        st = np.searchsorted(so, np.arange(nsym), "left")
        la = np.searchsorted(so, np.arange(nsym), "right") - st
        return o, st, la

    POOL = {name: pool(np.isin(JAHR, jj)) for name, jj in ZEITRAEUME}

    def null_ew(mm, name):
        o, st, la = POOL[name]
        s = SYM[mm]
        werte = []
        for _ in range(ZIEHUNGEN):
            r = (rng.random(len(s)) * np.maximum(la[s], 1)).astype(np.int64)
            werte.append(EW[o[st[s] + r]].mean())
        return np.array(werte)

    # ══ TEIL 1+2: je Zeitraum, Lage, Variante ═══════════════════════
    ergebnisse = {}
    for name, jj in ZEITRAEUME:
        zr = np.isin(JAHR, jj)
        print("=" * 124)
        print("ZEITRAUM %s" % name)
        print("     %-6s %6s %5s %5s %6s | %6s %6s %6s %6s | %7s %7s %7s %6s | %8s"
              % ("Lage", "Einst.", "Tage", "Sym.", "Top5", "P+20", "P-10",
                 "offen", "q", "EW %", "EW Null", "Band90", "z", "Ende Med"))
        zeilen = []
        for lname, bed in LAGEN:
            beginn = lage_maske(bed)
            for vname, kk in VARIANTEN:
                mm = entzerren(variante(beginn, kk) & zr)
                ne = int(mm.sum())
                if ne < 20:
                    print("     %-6s %6d  (zu wenig)" % (lname + vname, ne))
                    continue
                nw = null_ew(mm, name)
                zeilen.append((lname + vname, mm, nw))
        # Bestes-von-N je Zeitraum
        if zeilen:
            mu = np.array([z[2].mean() for z in zeilen])
            sd = np.array([max(z[2].std(ddof=1), 1e-9) for z in zeilen])
            M = np.array([z[2] for z in zeilen])          # (N, ZIEHUNGEN)
            zmax = np.max((M - mu[:, None]) / sd[:, None], axis=0)
            zgr = float(np.percentile(zmax, 90))
        for i, (lv, mm, nw) in enumerate(zeilen):
            ne = int(mm.sum())
            tage = len(np.unique(STD[mm] // 24))
            cnt = np.bincount(SYM[mm], minlength=nsym)
            top5 = np.sort(cnt)[::-1][:5].sum() / max(ne, 1)
            pg, pk = g[mm].mean(), k[mm].mean()
            q = pg / max(pg + pk, 1e-12)
            ew = EW[mm].mean()
            z = (ew - mu[i]) / sd[i]
            ergebnisse[(name, lv)] = (mm, ew, mu[i], z, zgr)
            print("     %-6s %6d %5d %5d %5.0f%% | %5.1f%% %5.1f%% %5.1f%% %6.3f | %+7.2f %+7.2f %+7.2f %6.2f%s | %+7.2f%%"
                  % (lv, ne, tage, int((cnt > 0).sum()), 100 * top5, 100 * pg,
                     100 * pk, 100 * (1 - pg - pk), q, ew, mu[i],
                     float(np.percentile(nw, 90)), z,
                     "*" if z > zgr else " ", 100 * np.median(END[mm])))
        if zeilen:
            print("     * = ueber der Bestes-von-%d-Grenze (z %.2f)" % (len(zeilen), zgr))
        print()

    # ══ TEIL 4: RUECKGANG VOR DEM ZIEL ══════════════════════════════
    print("=" * 124)
    print("TEIL 4 - RUECKGANG: tiefster Kurs vor +20 %% (nur Treffer) und "
          "tiefster Kurs binnen %d h (alle Einstiege) - 2024 bis 2026" % W)
    print("     %-6s %6s | %8s %8s %8s | %8s %8s %8s %9s %9s"
          % ("Lage", "Treffer", "vor Ziel", "P75", "P90", "alle Med", "P75",
             "P90", ">12 %", ">27 %"))
    spaet = JAHR >= 2024
    for lname, bed in LAGEN:
        beginn = lage_maske(bed)
        for vname, kk in VARIANTEN:
            mm = entzerren(variante(beginn, kk) & spaet)
            idx = np.flatnonzero(mm)
            if len(idx) < 20:
                continue
            vor_ziel, alle = [], []
            for i in idx:
                st, hh, ll, cc = reihen[int(SYM[i])]
                p = POS[i]
                e = cc[p]
                lows = ll[p + 1:p + W + 1]
                alle.append(1.0 - lows.min() / e)
                if g[i]:
                    t = int(T["up20"][i])
                    vor_ziel.append(1.0 - ll[p + 1:p + t + 1].min() / e)
            vz = 100 * np.array(vor_ziel) if vor_ziel else np.array([np.nan])
            al = 100 * np.array(alle)
            print("     %-6s %6d | %7.1f%% %7.1f%% %7.1f%% | %7.1f%% %7.1f%% %7.1f%% %8.1f%% %8.1f%%"
                  % (lname + vname, len(vor_ziel), np.nanmedian(vz),
                     np.nanpercentile(vz, 75), np.nanpercentile(vz, 90),
                     np.median(al), np.percentile(al, 75), np.percentile(al, 90),
                     100 * np.mean(al > 12), 100 * np.mean(al > 27)))
    print("  ⚠️ 'vor Ziel' zaehlt die Stunde des Zieltreffers mit - der tiefste "
          "Kurs dieser Stunde kann nach dem Ziel liegen (konservativ).")
    print()

    # ══ BTC-KONTEXT ═════════════════════════════════════════════════
    print("=" * 124)
    print("BTC-KONTEXT - 2024 bis 2026, getrennt nach BTC-Rendite der letzten "
          "24 h beim Einstieg")
    print("     %-6s | %-28s | %-28s" % ("Lage", "BTC steigend (> 0)", "BTC fallend (<= 0)"))
    for lname, bed in LAGEN:
        beginn = lage_maske(bed)
        for vname, kk in VARIANTEN:
            mm = entzerren(variante(beginn, kk) & spaet)
            teile = []
            for bm in (btc24 > 0, btc24 <= 0):
                x = mm & bm
                if x.sum() < 15:
                    teile.append("%5d  (zu wenig)          " % int(x.sum()))
                    continue
                pg, pk = g[x].mean(), k[x].mean()
                teile.append("%5d q %.3f EW %+6.2f%%     "
                             % (int(x.sum()), pg / max(pg + pk, 1e-12), EW[x].mean()))
            print("     %-6s | %s | %s" % (lname + vname, teile[0], teile[1]))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
