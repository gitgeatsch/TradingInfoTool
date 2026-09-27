# -*- coding: utf-8 -*-
"""Was kostet ein VERALTETER Merkmalswert?

**27.09.2026**, aus der Machbarkeitspruefung fuer die Stundendaten.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_29_Altersabschlag_27_09.md`

═══════════════════════════════════════════════════════════════════════
 WARUM
═══════════════════════════════════════════════════════════════════════

Das CoinGecko-Kontingent erlaubt die 16 Symbole ohne Binance-Daten NICHT
stuendlich: gemessen im echten Betrieb (NB-Diagnose 23.09.) liegt die
Nutzung bei 195 Anfragen je Tag, das Demo-Tier bei 10.000 je Monat.

    stuendlich   +384/Tag  ->  17.370/Monat   ⛔
    alle 2 h     +192/Tag  ->  11.610/Monat   ⛔
    alle 4 h      +96/Tag  ->   8.730/Monat   ✔
    alle 6 h      +64/Tag  ->   7.770/Monat   ✔

➤ Ab 4 Stunden passt es. Was dieser Takt KOSTET, soll gemessen werden -
nicht gesetzt. Dieselbe Frage wie bei der Fenstergroesse, wo 7 Tage und
100 Prozent Auswahlgleichheit herauskamen.

⚠️ Der Anker bleibt unveraendert - gehandelt wird zum Zeitpunkt t, nur
das MERKMAL stammt aus t-N. Genau der Betriebsfall.

⚠️ NUR LESEN.  python messe_altersabschlag.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402
from messe_trailing_und_betrieb import ema                      # noqa: E402
from messe_hebel_neudimension import (                          # noqa: E402
    trailing_mit_ausloeser, EMA_L, VORLAUF)

HZ, STOP, AUSL, ABST = 24, 1.00, 1.5, 0.5
ALTER = (0, 1, 2, 4, 6, 12, 24)        # Stunden
ANTEIL = 0.01
SAAT = 20260927


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 100)
    print("WAS KOSTET EIN VERALTETER MERKMALSWERT?")
    print("=" * 100)
    print("  " + N.standardzeile())
    print("  Geometrie H%d / Stop %.2f ATR / Trailing %.1f / %.1f (2.628)"
          % (HZ, STOP, AUSL, ABST))
    print("  Anker unveraendert, nur das MERKMAL stammt aus t-N.")
    print("  Auswahlanteil %.1f %% bei JEDER Verzoegerung (Falle 1)"
          % (100 * ANTEIL))
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}

    G, P = [], []
    W = {a: [] for a in ALTER}
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        gi = np.array([sid[x] for x in st], np.int64)
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        _r, p, _g = trailing_mit_ausloeser(h, l, cc, atr, STOP, AUSL,
                                           ABST, HZ)
        gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w) & np.isfinite(p)
        gu[:VORLAUF + max(ALTER)] = False
        gu[max(0, len(cc) - HZ):] = False
        sel = np.flatnonzero(gu)
        if not len(sel):
            continue
        # ⚠️ Alle Verzoegerungen brauchen dieselbe Ankermenge, sonst
        # vergleicht man verschiedene Mengen (Falle 1).
        ok = np.ones(len(sel), bool)
        for a in ALTER:
            ok &= np.isfinite(w[sel - a])
        sel = sel[ok]
        if not len(sel):
            continue
        G.append(gi[sel]); P.append(p[sel])
        for a in ALTER:
            W[a].append(w[sel - a])

    G = np.concatenate(G); P = np.concatenate(P)
    W = {a: np.concatenate(W[a]) for a in ALTER}
    tag = G // 24
    n = len(G)
    print("  %d Anker · %d Tage · %d Symbole  (identische Menge fuer ALLE "
          "Verzoegerungen)" % (n, len(np.unique(tag)), len(kurse)), flush=True)
    print()

    rng = np.random.default_rng(SAAT)
    pool = {}
    for i_ in range(n):
        pool.setdefault(int(tag[i_]), []).append(i_)
    pool = {t: np.array(v) for t, v in pool.items()}

    def auswahl(a):
        k = max(50, int(round(ANTEIL * n)))
        o = np.argsort(W[a], kind="stable")[:k]
        m = np.zeros(n, bool); m[o] = True
        return m

    def nullband(m):
        je = {int(t): int(c) for t, c in
              zip(*np.unique(tag[m], return_counts=True))}
        aus = []
        for _ in range(N.NULL_ZIEHUNGEN):
            b = []
            for t, c in je.items():
                pl = pool.get(t)
                if pl is not None and len(pl):
                    b.append(rng.choice(pl, size=min(c, len(pl)),
                                        replace=False))
            if b:
                aus.append(float(P[np.concatenate(b)].mean()))
        return np.array(aus) if aus else np.zeros(1)

    m0 = auswahl(0)
    s0 = set(np.flatnonzero(m0))

    print("=" * 100)
    print("DER ALTERSABSCHLAG")
    print()
    print("  %-12s %10s %13s %13s %11s %14s  %s"
          % ("Alter", "Auswahl", "Ertrag %", "Nullband", "Abstand",
             "gleiche Wahl", "Urteil"))
    proben = []
    zeilen = []
    for a in ALTER:
        m = auswahl(a)
        nb = nullband(m)
        proben.append(100 * nb)
        er = 100 * float(P[m].mean())
        band = 100 * float(np.percentile(nb, N.NULL_PERZENTIL))
        gl = 100.0 * len(s0 & set(np.flatnonzero(m))) / max(m.sum(), 1)
        zeilen.append((a, er, band, gl))
        print("  %-12s %10d %+13.4f %+13.4f %+11.4f %13.1f %%  %s"
              % ("%d h" % a, int(m.sum()), er, band, er - band, gl,
                 "✔" if er > band else "⛔ im Band"), flush=True)

    print()
    print("=" * 100)
    print("P5 - MEHRFACHTESTEN ueber %d Verzoegerungen" % len(ALTER))
    arr = np.array(proben)
    b5 = float(np.percentile(arr.max(axis=0), N.NULL_PERZENTIL))
    print("  Bestes-von-%d-Band: %+.4f %%" % (len(ALTER), b5))
    halten = [z for z in zeilen if z[1] > b5]
    if halten:
        print("  haltende Verzoegerungen: %s"
              % ", ".join("%d h" % z[0] for z in halten))
        print("  laengste haltende:       %d h" % max(z[0] for z in halten))
    else:
        print("  ⛔ KEINE haelt gegen das Mehrfachtesten")

    # ── Die eingebaute Selbstprobe ───────────────────────────────────
    print()
    print("  SELBSTPROBE: N=0 ist die bekannte Referenz und MUSS tragen.")
    z0 = [z for z in zeilen if z[0] == 0][0]
    print("  ➤ %s" % ("✔ N=0 traegt (%+.4f gegen %+.4f) - der Aufbau stimmt"
                      % (z0[1], z0[2]) if z0[1] > z0[2]
                      else "⛔ N=0 TRAEGT NICHT - am Aufbau stimmt etwas "
                           "nicht, die uebrigen Zeilen sind wertlos"))

    print()
    print("  ⚠️ Gemessen auf den Symbolen MIT Binance-Stundendaten -")
    print("     betroffen sind die 16 OHNE. Die Wirkung einer Verzoegerung")
    print("     ist eine Eigenschaft der ACHSE, nicht des Symbols; das ist")
    print("     vertretbar, aber es ist eine UEBERTRAGUNG.")
    print("  ⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
