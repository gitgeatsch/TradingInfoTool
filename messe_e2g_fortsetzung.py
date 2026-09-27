# -*- coding: utf-8 -*-
"""E2g: sind die Richtungstraeger aus E2f FORTSETZUNG - oder Lage VOR der Bewegung?

**27.09.2026.** E2f fand vier Auswahlen, die den Pflichtablauf halten
(Gegenprobe P5: 0 von 80 Zufallsauswahlen). Zwei davon messen womoeglich nur
*der Kurs ist schon gestiegen* - und das disqualifiziert als Einstieg
(Nutzerdefinition OPTIMUM: *"die Bewertung eines BEREITS GESTIEGENEN Assets
ist weder das Ziel noch ein Optimum - dazu brauche ich kein System"*).
Das ist eine Erklaerung, die man messen kann - also wird sie gemessen.

VORAB FESTGELEGT
    Auswahlen    genau die vier aus E2f, mit IHREN Schwellen (keine neue Suche):
        F5   funding_vortag <= P5    Ziel q5    (Richtung +)
        F95  funding_vortag >= P95   Ziel q5    (Sperre)
        K95  kaeufer_24h    >= P95   Ziel q15   (Richtung +)
        M95  momentum_kurz  >= P95   Ziel q15   (Richtung +)
    TEIL A  ALTERSACHSE: das Merkmal ist L Stunden alt (L = 0, 1, 3, 6, 12,
            24), der Ausgang zaehlt ab JETZT. Haltequote Dq(L) / Dq(0).
            Traegt ein altes Merkmal noch, war die Lage VORHER da.
    TEIL B  SCHICHTUNG nach der eigenen 24-h-Rendite (Fuenftel ueber alle
            Anker): in jeder Schicht q der Auswahl minus q ALLER Anker
            derselben Schicht. Bleibt ein Vorsprung bei GLEICHER
            Vorbewegung, ist das Merkmal mehr als *schon gestiegen*.
            Dazu die Rangkorrelation Merkmal gegen 24-h-Rendite.
    Bezug       Teil A wie E2f (eigenes Asset im Monat, Episoden); Teil B
                gegen die Schicht (Episoden)

NUR LESEND (`mode=ro`). Kein Stop, kein Trailing, keine Gebuehren (Regel 2).
"""
from __future__ import annotations

import os
import sqlite3
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messe_e2_beitraege as E2                                   # noqa: E402
from messe_e3_vorwaerts import monat_von                          # noqa: E402
from messe_e2f_richtungsdaten import (AB, BIS, RICHTUNG_DB,       # noqa: E402
                                      richtungsmerkmale)

AUSWAHLEN = (("F5", "funding_vortag", 5, "q5"),
             ("F95", "funding_vortag", 95, "q5"),
             ("K95", "kaeufer_24h", 95, "q15"),
             ("M95", "momentum_kurz", 95, "q15"))
ALTER = (0, 1, 3, 6, 12, 24)
ABSTAND_H = 24


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 110)
    print("E2g - FORTSETZUNG ODER LAGE VORHER? Altersachse und Schichtung "
          "nach der Vorbewegung")
    print("=" * 110)
    D = E2.lade(hmax=72, erste=(("up15", 1.15, True), ("dn15", 0.85, False)))
    im = (D["STD"] >= AB) & (D["STD"] < BIS)
    SYM, STD = D["SYM"][im], D["STD"][im]
    F = {"funding_vortag": D["F"]["funding_vortag"][im].astype(np.float32),
         "momentum_kurz": D["F"]["momentum_kurz"][im].astype(np.float32)}
    VOR24 = D["X"]["vor24"][im]
    A5 = D["Z"][24]["auf5"][im].astype(np.int8)
    B5 = D["Z"][24]["ab5"][im].astype(np.int8)
    U15 = (D["T"]["up15"][im] <= 12).astype(np.int8)
    D15 = (D["T"]["dn15"][im] <= 12).astype(np.int8)
    syms = D["syms"]
    del D
    n = len(SYM)
    MON = monat_von(STD)
    cr = sqlite3.connect("file:%s?mode=ro" % RICHTUNG_DB, uri=True)
    F["kaeufer_24h"] = np.full(n, np.nan, np.float32)
    for si in np.unique(SYM):
        r = richtungsmerkmale(syms[si], cr)
        if r is None:
            continue
        h0, M = r
        mk = SYM == si
        pos = STD[mk] - h0
        ok = (pos >= 0) & (pos < len(M["kaeufer_24h"]))
        w = np.full(mk.sum(), np.nan, np.float32)
        w[ok] = M["kaeufer_24h"][pos[ok]]
        F["kaeufer_24h"][mk] = w
    cr.close()
    print("  %d Anker · %d Symbole" % (n, len(np.unique(SYM))))

    SM = SYM.astype(np.int64) * 1000 + (MON - MON.min())
    _u, sm_i = np.unique(SM, return_inverse=True)
    sm_anz = np.maximum(np.bincount(sm_i), 1)

    def smb(x):
        return np.bincount(sm_i, weights=x.astype(float)) / sm_anz

    BASE = {"q5": (smb(A5), smb(B5), A5, B5),
            "q15": (smb(U15), smb(D15), U15, D15)}

    def q(e, z):
        _a0, _b0, xa, xb = BASE[z]
        a, b = xa[e].mean(), xb[e].mean()
        return a / (a + b) if a + b > 0 else np.nan

    def dq(e, z):
        if e.sum() == 0:
            return np.nan
        a0, b0, _xa, _xb = BASE[z]
        a = a0[sm_i[e]].mean(); b = b0[sm_i[e]].mean()
        return q(e, z) - (a / (a + b) if a + b > 0 else np.nan)

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

    # Zeiger: derselbe Symbolanker L Stunden frueher (nur lueckenlos)
    pos_in = np.empty(n, np.int64); pos_in[ordnung] = np.arange(n)
    s_o, t_o = SYM[ordnung], STD[ordnung]

    def frueher(L):
        z = np.full(n, -1, np.int64)
        if L == 0:
            return np.arange(n)
        ok = np.zeros(n, bool)
        ok[L:] = (s_o[L:] == s_o[:-L]) & (t_o[L:] - t_o[:-L] == L)
        z[ordnung[L:][ok[L:]]] = ordnung[:-L][ok[L:]]
        return z

    SW = {}
    for kurz, m, p, _z in AUSWAHLEN:
        v = F[m]
        SW[kurz] = float(np.percentile(v[np.isfinite(v)], p))

    print()
    print("TEIL A - ALTERSACHSE: Merkmal L Stunden alt, Ausgang ab jetzt · "
          "Dq gegen das eigene Asset im Monat, Episoden")
    print("  %-5s %-15s %9s | %s" % ("", "Merkmal", "Schwelle", "  ".join(
        "%12s" % ("L=%dh" % L) for L in ALTER)))
    for kurz, m, p, z in AUSWAHLEN:
        reihe = []
        for L in ALTER:
            zg = frueher(L)
            v = np.full(n, np.nan)
            ok = zg >= 0
            v[ok] = F[m][zg[ok]]
            sel = np.isfinite(v) & ((v <= SW[kurz]) if p < 50 else (v >= SW[kurz]))
            e = entzerren(sel)
            reihe.append((dq(e, z), int(e.sum())))
        d0 = reihe[0][0]
        print("  %-5s %-15s %9.4f | %s" % (kurz, m, SW[kurz], "  ".join(
            "%+6.3f (%3.0f%%)" % (d, 100 * d / d0 if d0 else float("nan"))
            for d, _k in reihe)))
    print("  (in Klammern: Haltequote gegen L = 0)")

    print()
    print("TEIL B - SCHICHTUNG nach der eigenen 24-h-Rendite (Fuenftel): "
          "q der Auswahl minus q ALLER Anker derselben Schicht")
    ok_v = np.isfinite(VOR24)
    gr = np.percentile(VOR24[ok_v], [20, 40, 60, 80])
    schicht = np.full(n, -1, np.int8)
    schicht[ok_v] = np.searchsorted(gr, VOR24[ok_v])
    print("  Schichtgrenzen 24-h-Rendite: %s" % " · ".join(
        "%+.2f%%" % (100 * g) for g in gr))
    for kurz, m, p, z in AUSWAHLEN:
        v = F[m]
        fin = np.isfinite(v) & ok_v
        rv = np.argsort(np.argsort(v[fin])); rr = np.argsort(np.argsort(VOR24[fin]))
        rho = np.corrcoef(rv, rr)[0, 1]
        sel = np.isfinite(v) & ((v <= SW[kurz]) if p < 50 else (v >= SW[kurz]))
        teile = []
        for s in range(5):
            e = entzerren(sel & (schicht == s))
            alle = entzerren(schicht == s)
            if e.sum() < 100:
                teile.append("S%d  zu duenn (%d)" % (s + 1, int(e.sum())))
                continue
            teile.append("S%d %+.3f (%d)" % (s + 1, q(e, z) - q(alle, z),
                                             int(e.sum())))
        anteil = [np.mean(schicht[sel] == s) for s in range(5)]
        print("  %-5s %-15s rho %+.2f | Anteil je Schicht %s" % (
            kurz, m, rho, " ".join("%.0f%%" % (100 * a) for a in anteil)))
        print("        %s" % " · ".join(teile))
    print()
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
