# -*- coding: utf-8 -*-
"""E1: ERHEBUNG - welche Bewegungen gab es, und wie viel Rueckgang lag davor?

**27.09.2026.** Nutzerauftrag: *"Aufgabe ist, bei welchen BEWERTUNGEN ist in
der Vergangenheit ein 2x 3x oder 5x fuer ein Asset aufgetreten ... also
musst du zuerst feststellen, welche Lage brauchen die Assets POSITIV und
welche sind NEGATIV ... die meisten kurzen Bewegungen sind innerhalb eines
Tages, aber das musst du erheben."*

Dieses Werkzeug kennt KEIN Merkmal. Es beschreibt nur die VERLAEUFE nach
jedem Anker - damit feststeht, was "positiv" und "negativ" heisst, BEVOR
eine Lage dagegen gemessen wird (E2).

⚠️⚠️ UNABHAENGIG VOM ALTEN CODE (Nutzerhinweis 27.09.: *"Vorsicht, Code ist
alt - wir bauen NEU"*). Der zulaessige Rueckgang einer Hebelstufe ist ein
Fakt der BOERSE. Der alte Produktionscode schaetzt ihn
(`hebel_risk_gate.estimate_liquidation_price`, selbst als *"konservative
Schaetzung, Bitpanda veroeffentlicht keine exakte Formel"* bezeichnet, an
EINER Position am 16.07. kalibriert). Deshalb misst E1 ueber ein RASTER
zulaessiger Rueckgaenge; welche Zeile zu 5x / 3x / 2x gehoert, wird erst
zugeordnet, wenn der Wert an Bitpanda bestaetigt ist. Die alte Schaetzung
steht nur als Orientierung im Kopf der Ausgabe.

⚠️ Kein Stop, kein Trailing, kein Ziel - die Positionsfuehrung kommt
spaeter (Nutzervorgabe 27.09.). Gemessen wird nur, was der VERLAUF hergab.

GEMESSEN je Anker (alle Stunden mit 240 h Vorlauf, BTC ausgenommen wie in
2.631 - dieselbe Ankermenge fuer E2), ueber t+1 .. t+72 h:
    erste Stunde, in der +g erreicht ist (g = 2, 5, 10, 15, 20, 30 %)
    erste Stunde, in der -r erreicht ist (r = das Raster unten)
    ⚠️ Gleichstand in derselben Stunde zaehlt als RUECKGANG zuerst - ohne
    Minutendaten ist die Reihenfolge innerhalb der Stunde unbekannt, und die
    sichere Seite ist der Rueckgang (2.583).

AUSGABE
    TEIL A  Wie oft und WIE SCHNELL: Anteil der Anker mit +g binnen H, und
            die Zeit bis +g (Median, Anteil binnen 6 / 24 h)
    TEIL B  JE ZULAESSIGEM RUECKGANG r: Anteil mit +g VOR -r binnen H
            (positiv) und Anteil mit -r zuerst (negativ)
    TEIL C  Stabilitaet je Kalenderjahr (aus dem Datum) und je Asset

NUR LESEND (`mode=ro`), importiert nichts aus `agent/`. Keine Gebuehren
(Regel 2), keine Finanzierung. Ebene B (2.641).
"""
from __future__ import annotations

import os
import sqlite3
import sys

import numpy as np

STUNDEN_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "data", "stundenkurse.db")
VORLAUF, HMAX = 240, 72
HORIZONTE = (3, 6, 12, 24, 48, 72)
GEWINNE = (0.02, 0.05, 0.10, 0.15, 0.20, 0.30)
RUECKGAENGE = (0.05, 0.08, 0.10, 0.12, 0.15, 0.20, 0.27, 0.35, 0.45)
# NUR Orientierung, NICHT Grundlage: alte Schaetzung aus dem Produktionscode
ORIENTIERUNG_ALT = "5x ~12 % · 3x ~27 % · 2x ~45 % (alte Schaetzung, an Bitpanda zu bestaetigen)"
# fuer TEIL C: drei Rueckgaenge, die die Spanne abdecken
C_RUECKGAENGE = (0.05, 0.12, 0.27)


def lade_kurse():
    """Dieselbe Menge wie `messe_reverse_scharfe_anstiege.lade_kurse`."""
    c = sqlite3.connect("file:%s?mode=ro" % STUNDEN_DB, uri=True)
    syms = [r[0] for r in c.execute(
        "SELECT symbol FROM stundenkurse GROUP BY symbol "
        "HAVING COUNT(*) > 2000 ORDER BY COUNT(*) DESC")]
    aus = {}
    for s in syms:
        rows = c.execute(
            "SELECT stunde, high, low, close FROM stundenkurse "
            "WHERE symbol=? ORDER BY stunde", (s,)).fetchall()
        if len(rows) < 500:
            continue
        aus[s] = ([r[0] for r in rows],
                  np.array([r[1] for r in rows], float),
                  np.array([r[2] for r in rows], float),
                  np.array([r[3] for r in rows], float))
    c.close()
    return aus


def erste_treffer(high, low, close):
    """-> ({g: erste Stunde +g}, {r: erste Stunde -r}); 999 = nie binnen HMAX."""
    n = len(close)
    idx = np.arange(n)
    t_auf = {g: np.full(n, 999, np.int16) for g in GEWINNE}
    t_ab = {r: np.full(n, 999, np.int16) for r in RUECKGAENGE}
    for s in range(1, HMAX + 1):
        j = np.minimum(idx + s, n - 1)
        hj, lj = high[j], low[j]
        for g in GEWINNE:
            neu = (t_auf[g] == 999) & (hj >= close * (1.0 + g))
            t_auf[g][neu] = s
        for r in RUECKGAENGE:
            neu = (t_ab[r] == 999) & (lj <= close * (1.0 - r))
            t_ab[r][neu] = s
    return t_auf, t_ab


def pct(x):
    return "%d %%" % round(100 * x)


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    print("=" * 110)
    print("E1 - ERHEBUNG: WELCHE BEWEGUNGEN GAB ES, UND WIE VIEL RUECKGANG "
          "LAG DAVOR?")
    print("=" * 110)
    print("  KEIN Merkmal, kein Stop, kein Trailing - nur der Verlauf nach "
          "jedem Anker, t+1 bis t+%d h" % HMAX)
    print("  Zulaessiger Rueckgang als RASTER - Zuordnung zu den Hebelstufen "
          "erst nach Bestaetigung an Bitpanda")
    print("  Orientierung: %s" % ORIENTIERUNG_ALT)
    print("  ⚠️ Gleichstand in einer Stunde = Rueckgang zuerst · ohne "
          "Finanzierung und Gebuehren")
    print()

    kurse = lade_kurse()
    T_AUF = {g: [] for g in GEWINNE}
    T_AB = {r: [] for r in RUECKGAENGE}
    JAHR, SYM = [], []
    for si, (sym, (st, h, l, cc)) in enumerate(kurse.items()):
        if sym.upper() == "BTC":
            continue
        gu = np.isfinite(cc) & (cc > 0)
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - HMAX):] = False
        sel = np.flatnonzero(gu)
        if not len(sel):
            continue
        ta, tb = erste_treffer(h, l, cc)
        for g in GEWINNE:
            T_AUF[g].append(ta[g][sel])
        for r in RUECKGAENGE:
            T_AB[r].append(tb[r][sel])
        JAHR.append(np.array([int(st[i][:4]) for i in sel], np.int16))
        SYM.append(np.full(len(sel), si, np.int32))
    T_AUF = {g: np.concatenate(v) for g, v in T_AUF.items()}
    T_AB = {r: np.concatenate(v) for r, v in T_AB.items()}
    JAHR = np.concatenate(JAHR)
    SYM = np.concatenate(SYM)
    print("  %d Anker · %d Symbole · Jahre %d bis %d"
          % (len(JAHR), len(np.unique(SYM)), JAHR.min(), JAHR.max()))
    print()

    # ══ TEIL A ══════════════════════════════════════════════════════
    print("=" * 110)
    print("TEIL A - WIE OFT UND WIE SCHNELL: Anteil der Anker, bei denen +g "
          "binnen H Stunden erreicht wird")
    print("     %-6s" % "+g" + "".join("%9s" % ("H%d" % H) for H in HORIZONTE)
          + "   | Zeit bis +g (wenn binnen 72 h): Median · binnen 6 h · "
            "binnen 24 h")
    for g in GEWINNE:
        t = T_AUF[g]
        zellen = "".join("%8.2f%%" % (100 * np.mean(t <= H))
                         for H in HORIZONTE)
        hit = t[t <= HMAX]
        zusatz = ("   | %5.0f h · %5.1f %% · %5.1f %%"
                  % (np.median(hit), 100 * np.mean(hit <= 6),
                     100 * np.mean(hit <= 24)) if len(hit) else "   | -")
        print("     %-6s%s%s" % ("+" + pct(g), zellen, zusatz))
    print()
    print("     Rueckgang -r binnen H (ohne Bedingung):")
    for r in RUECKGAENGE:
        t = T_AB[r]
        print("     %-6s%s" % ("-" + pct(r), "".join(
            "%8.2f%%" % (100 * np.mean(t <= H)) for H in HORIZONTE)))
    print()

    # ══ TEIL B ══════════════════════════════════════════════════════
    print("=" * 110)
    print("TEIL B - +g erreicht, BEVOR der Rueckgang -r eintritt (positiv), "
          "binnen H · und -r zuerst binnen 72 h (negativ)")
    for r in RUECKGAENGE:
        tb = T_AB[r]
        print("  ── zulaessiger Rueckgang -%s" % pct(r))
        print("     %-6s" % "+g" + "".join("%9s" % ("H%d" % H)
                                          for H in HORIZONTE)
              + "   | -r zuerst (H72)")
        for g in GEWINNE:
            ta = T_AUF[g]
            pos = "".join("%8.2f%%" % (100 * np.mean((ta <= H) & (ta < tb)))
                          for H in HORIZONTE)
            neg = 100 * np.mean((tb <= HMAX) & (tb <= ta))
            print("     %-6s%s   | %6.2f %%" % ("+" + pct(g), pos, neg))
        print()

    # ══ TEIL C ══════════════════════════════════════════════════════
    print("=" * 110)
    print("TEIL C - STABILITAET: +10 %% vor -r binnen 24 h, fuer drei "
          "Rueckgaenge - je Kalenderjahr und je Asset")
    print("     %-6s %9s" % ("Jahr", "Anker") + "".join(
        "%16s" % ("+10%%/-%s/H24" % pct(r)) for r in C_RUECKGAENGE))
    for j in np.unique(JAHR):
        m = JAHR == j
        if m.sum() < 1000:
            continue
        werte = "".join("%15.2f%%" % (100 * np.mean(
            (T_AUF[0.10][m] <= 24) & (T_AUF[0.10][m] < T_AB[r][m])))
            for r in C_RUECKGAENGE)
        print("     %-6d %9d%s" % (j, int(m.sum()), werte))
    print()
    print("  JE ASSET (Anteil je Symbol, dann Verteilung ueber die Symbole):")
    anz = np.bincount(SYM)
    for r in C_RUECKGAENGE:
        treffer = ((T_AUF[0.10] <= 24) & (T_AUF[0.10] < T_AB[r])).astype(float)
        je = (np.bincount(SYM, weights=treffer) / np.maximum(anz, 1))[anz > 0]
        print("     +10 %%/-%s/H24  Median %5.2f %% · 10. Perz. %5.2f %% · "
              "90. Perz. %5.2f %% · Symbole %d"
              % (pct(r), 100 * np.median(je), 100 * np.percentile(je, 10),
                 100 * np.percentile(je, 90), len(je)))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
