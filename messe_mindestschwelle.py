# -*- coding: utf-8 -*-
"""Die MINDESTSCHWELLE auf der inversen Achse - traegt ein Signal fuer sich?

**26.09.2026**, Nutzerauftrag: *"Mindestschwelle zuerst messen, pruefen und
gegenpruefen, dann Simulation mit Rang und Schwelle"*.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_25_Mindestschwelle_26_09.md`

═══════════════════════════════════════════════════════════════════════
 WARUM SIE FEHLT
═══════════════════════════════════════════════════════════════════════

2.626 und 2.628 waehlen JE TAG die besten 2 Prozent - eine reine
RANGFOLGE. Das hat zwei Luecken:

    ⛔ Bei einem EINZELNEN Asset gibt es keinen Rang. Genau der
       Nutzereinwand: *das System muss auch bei nur EINEM Asset
       funktionieren und nicht besser oder schlechter durch die Watchlist
       werden*
    ⛔ An einem Tag ohne gute Lage kauft die Rangfolge TROTZDEM - der
       beste von 115 schlechten Werten ist immer noch schlecht

➤ Gesucht ist eine ABSOLUTE Schwelle, unterhalb derer ein Signal fuer
sich steht.

⚠️ NUR LESEN.  python messe_mindestschwelle.py [--symbole N]
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
from messe_inverse_achse import taeglich_beste                  # noqa: E402

# aus 2.628
HZ, STOP, AUSL, ABST = 24, 1.00, 1.5, 0.5
SCHWELLEN = (-1.5, -1.2, -1.0, -0.8, -0.6, -0.4, -0.2, 0.0)
SAAT = 20260926


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 108)
    print("DIE MINDESTSCHWELLE AUF DER INVERSEN ACHSE")
    print("=" * 108)
    print("  " + N.standardzeile())
    print("  Geometrie H%d / Stop %.2f ATR / Trailing %.1f / %.1f (2.628)"
          % (HZ, STOP, AUSL, ABST))
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    G, W, P = [], [], []
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w)
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - HZ):] = False
        sel = np.flatnonzero(gu)
        if not len(sel):
            continue
        _r, p, _g = trailing_mit_ausloeser(h, l, cc, atr, STOP, AUSL,
                                           ABST, HZ)
        G.append(np.array([sid[x] for x in st], np.int64)[sel])
        W.append(w[sel]); P.append(p[sel])
    G = np.concatenate(G); W = np.concatenate(W); P = np.concatenate(P)
    n = len(G); tag = G // 24
    ut, inv = np.unique(tag, return_inverse=True)
    mit = (np.bincount(inv, weights=P) /
           np.maximum(np.bincount(inv), 1))[inv]
    REL = P - mit
    tage_gesamt = len(ut)
    print("  %d Anker · %d Tage · %d Symbole" % (n, tage_gesamt, len(kurse)),
          flush=True)
    print()

    rng = np.random.default_rng(SAAT)
    frei = np.flatnonzero(np.isfinite(W))
    pool = {}
    for i_ in frei:
        pool.setdefault(int(tag[i_]), []).append(i_)
    pool = {t: np.array(v) for t, v in pool.items()}

    def nullband(maske):
        """Tagestreu: je Tag so viele zufaellige wie die echte Auswahl."""
        je = {int(t): int(c) for t, c in
              zip(*np.unique(tag[maske], return_counts=True))}
        aus = []
        for _ in range(N.NULL_ZIEHUNGEN):
            a = []
            for t, c in je.items():
                pl = pool.get(t)
                if pl is not None and len(pl):
                    a.append(rng.choice(pl, size=min(c, len(pl)),
                                        replace=False))
            if a:
                idx = np.concatenate(a)
                aus.append((float(P[idx].mean()), float(REL[idx].mean())))
        return np.array(aus) if aus else np.zeros((0, 2))

    # ══ TEIL 1: die Schwelle ALLEIN ══════════════════════════════════
    print("=" * 108)
    print("TEIL 1 - DIE SCHWELLE ALLEIN (ohne Rang)")
    print("  ⭐ Die ABDECKUNG gehoert dazu: eine Schwelle, die nur selten "
          "greift, ist etwas anderes")
    print()
    print("  %-9s %9s %9s %9s %11s %11s %11s  %s"
          % ("Schwelle", "Signale", "Sig/Tag", "Tage %", "absolut %",
             "Band abs.", "relativ %", "Urteil"))
    proben = []
    zeilen = []
    for sw in SCHWELLEN:
        m = np.isfinite(W) & (W <= sw)
        k = int(m.sum())
        if k < 200:
            print("  %-9.1f %9d  (zu duenn)" % (sw, k)); continue
        nb = nullband(m)
        if not len(nb):
            continue
        proben.append(nb[:, 0])
        b90 = 100 * float(np.percentile(nb[:, 0], N.NULL_PERZENTIL))
        abdeck = 100.0 * len(np.unique(tag[m])) / max(tage_gesamt, 1)
        ab = 100 * float(P[m].mean()); re = 100 * float(REL[m].mean())
        zeilen.append(dict(sw=sw, k=k, ab=ab, re=re, b90=b90,
                           abdeck=abdeck))
        print("  %-9.1f %9d %9.1f %8.1f%% %+11.4f %+11.4f %+11.4f  %s"
              % (sw, k, k / max(tage_gesamt, 1), abdeck, ab, b90, re,
                 "✔" if ab > b90 else "⛔ im Band"), flush=True)

    if proben:
        arr = np.array(proben) * 100
        b90m = float(np.percentile(arr.max(axis=0), N.NULL_PERZENTIL))
        gute = [z for z in zeilen if z["ab"] > b90m]
        print()
        print("  P5  MEHRFACHTESTEN ueber %d Schwellen · Bestes-von-%d-Band "
              "%+.4f %%" % (len(zeilen), len(zeilen), b90m))
        if gute:
            b = max(gute, key=lambda z: z["ab"])
            print("      strengste haltende Schwelle: %.1f "
                  "(%+.4f %%, Abdeckung %.1f %%)"
                  % (min(z["sw"] for z in gute),
                     [z for z in gute
                      if z["sw"] == min(g["sw"] for g in gute)][0]["ab"],
                     [z for z in gute
                      if z["sw"] == min(g["sw"] for g in gute)][0]["abdeck"]))
            print("      beste haltende Schwelle:     %.1f "
                  "(%+.4f %%, Abdeckung %.1f %%)"
                  % (b["sw"], b["ab"], b["abdeck"]))
        else:
            print("      ⛔ KEINE Schwelle haelt gegen das Mehrfachtesten")

    # ══ TEIL 2: RANG UND SCHWELLE ZUSAMMEN ═══════════════════════════
    print()
    print("=" * 108)
    print("TEIL 2 - RANG UND SCHWELLE ZUSAMMEN (ein Signal muss BEIDES "
          "erfuellen)")
    print()
    rang = taeglich_beste(W, tag, 0.02)
    print("  %-9s %9s %9s %9s %11s %11s  %s"
          % ("Schwelle", "Signale", "Sig/Tag", "Tage %", "absolut %",
             "Band abs.", "Urteil"))
    for sw in SCHWELLEN:
        m = rang & np.isfinite(W) & (W <= sw)
        k = int(m.sum())
        if k < 200:
            print("  %-9.1f %9d  (zu duenn)" % (sw, k)); continue
        nb = nullband(m)
        if not len(nb):
            continue
        b90 = 100 * float(np.percentile(nb[:, 0], N.NULL_PERZENTIL))
        abdeck = 100.0 * len(np.unique(tag[m])) / max(tage_gesamt, 1)
        ab = 100 * float(P[m].mean())
        print("  %-9.1f %9d %9.1f %8.1f%% %+11.4f %+11.4f  %s"
              % (sw, k, k / max(tage_gesamt, 1), abdeck, ab, b90,
                 "✔" if ab > b90 else "⛔ im Band"), flush=True)
    print()
    print("  ⭐ Der Vergleich zu TEIL 1 zeigt, ob der Rang ZUSAETZLICH "
          "etwas bringt.")
    print("  ⚠️ Gebuehren und Finanzierung sind nicht eingerechnet "
          "(Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
