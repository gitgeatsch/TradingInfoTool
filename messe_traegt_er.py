# -*- coding: utf-8 -*-
"""Tragen die neun Richtungsmerkmale aus 2.603 auch `E[R]`?

**26.09.2026**, Nutzerauftrag: *"prüfe ob die neun Richtungsmerkmale E[R]
tragen - prüfen und gegenprüfen"*.

═══════════════════════════════════════════════════════════════════════
 WARUM DAS EINE EIGENE FRAGE IST
═══════════════════════════════════════════════════════════════════════

2.603 hat neun Merkmale mit belegter RICHTUNG gefunden (Lift auf das
Ziel-Ereignis, geeichte Schwelle 1,717). ⚠️ Das sagt NICHT, dass sie
`E[R]` tragen: ein hoher Lift auf *Ziel erreicht* ist mit HAEUFIGEREN
Stops vereinbar. Beides zugleich ist die Niveaufrage.

═══════════════════════════════════════════════════════════════════════
 ⭐⭐⭐ DAS FUENFTEL IST VORHERGESAGT, NICHT AUSGEWAEHLT
═══════════════════════════════════════════════════════════════════════

In `messe_a_faktoren.py` wurde je Merkmal das BESTE Fuenftel genommen -
das ist Rueckschau, und bei 5 Fuenfteln x 11 Merkmalen sind positive
Werte zu erwarten.

Hier steht das Fuenftel VORHER fest: es ist das, welches 2.603 als
Richtungstraeger ausgewiesen hat. Damit ist die Messung eine echte
VORHERSAGE und keine Auslese.

    F4   vola · ema_abstand_atr · ema_lage · bandenge · momentum_kurz
         rsi · ema_steigung · trendstruktur
    F0   rueckstand_beta        (dort war der Lift, siehe 2.603)

═══════════════════════════════════════════════════════════════════════
 DIE VIER PRUEFUNGEN
═══════════════════════════════════════════════════════════════════════

    P1  WERT       `E[R]` im vorhergesagten Fuenftel, mit TAGESGEBLOCKTEM
                   Fehler - die Anker eines Fuenftels stammen aus wenigen
                   Tagen und sind nicht unabhaengig
    P2  B6         erste gegen zweite Haelfte. Ein Wert, der nur in einer
                   Haelfte positiv ist, traegt nicht
    P3  ⭐ ZUFALLS-VERGLEICH
                   dieselbe Prozedur mit einem ZUFALLSmerkmal, 40
                   Ziehungen - wie hoch liegt ein zufaellig gewaehltes
                   Fuenftel? Das ist der Bezug, nicht die Null
    P4  KOMBINATION
                   die beiden staerksten Richtungstraeger geschnitten,
                   gegen die Schrumpfungs-Nullwelt

⚠️ NUR LESEN.  python messe_traegt_er.py [--symbole N]
"""
from __future__ import annotations

import os
import sqlite3
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import (                    # noqa: E402
    lade_kurse, lade_funding, merkmale_je_symbol)
from messe_hebel_dimension import _lade_terminmarkt             # noqa: E402
from messe_a_faktoren import a_faktoren                         # noqa: E402
import messe_hebel_geometrie_neutral as GG                      # noqa: E402
from messe_q_beide_seiten import (                              # noqa: E402
    fuenftel_je_stunde, MIND_JE_FUENFTEL)

LEITWERT = os.path.join("data", "btc_leitwert.db")
K = 1.0
ZELLEN = ((1.5, 6), (1.5, 24))
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
SAAT = 20260926

#: ⭐ die VORHERSAGE aus 2.603 - Merkmal -> Fuenftel mit dem Richtungslift
VORHERSAGE = (
    ("vola", 4), ("ema_abstand_atr", 4), ("ema_lage", 4), ("bandenge", 4),
    ("momentum_kurz", 4), ("rsi", 4), ("rueckstand_beta", 0),
    ("ema_steigung", 4), ("trendstruktur", 4),
)


def _tf(r, g):
    t = g // 24
    u = np.unique(t)
    if len(u) < 30:
        return float("nan")
    p = np.searchsorted(u, t)
    j = (np.bincount(p, weights=r, minlength=len(u))
         / np.maximum(np.bincount(p, minlength=len(u)), 1))
    return float(np.std(j, ddof=1) / np.sqrt(len(u)))


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 100)
    print("TRAGEN DIE NEUN RICHTUNGSMERKMALE AUCH `E[R]`?")
    print("=" * 100)
    print("  ⭐ Das Fuenftel ist VORHERGESAGT (aus 2.603), nicht ausgewaehlt")
    print("  ⚠️ *hat Richtung* ist nicht *traegt* - ein hoher Ziel-Lift")
    print("     vertraegt sich mit haeufigeren Stops.")

    kurse = lade_kurse(grenze)
    tm = _lade_terminmarkt(set(kurse))
    fund = lade_funding()
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}; T = len(sl)

    c = sqlite3.connect("file:%s?mode=ro" % LEITWERT, uri=True)
    btc = np.full(T, np.nan)
    for st, cl in c.execute("SELECT stunde, close FROM leitwert "
                            "WHERE symbol='BTC'"):
        i = sid.get(st)
        if i is not None:
            btc[i] = cl
    c.close()
    br = np.full(T, np.nan)
    br[6:] = btc[6:] / np.maximum(btc[:-6], 1e-12) - 1.0
    asum, anum = np.zeros(T), np.zeros(T)
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        ii = np.array([sid[x] for x in st], np.int64)
        rr = np.full(len(cc), np.nan)
        if len(cc) > 6:
            rr[6:] = cc[6:] / np.maximum(cc[:-6], 1e-12) - 1.0
        g = np.isfinite(rr)
        np.add.at(asum, ii[g], rr[g]); np.add.at(anum, ii[g], 1.0)
    with np.errstate(invalid="ignore"):
        am = np.where(anum >= 5, asum / np.maximum(anum, 1), np.nan)
    gesperrt = (br > 0.005) & ((br - am) > 0.0)
    print("  %d Symbole · Sperre aus 2.602 angewandt" % len(kurse),
          flush=True)

    rng = np.random.default_rng(SAAT)
    NAMEN = tuple(n for n, _f in VORHERSAGE)
    for crv, H in ZELLEN:
        G, R, MM = [], [], {k: [] for k in NAMEN}
        for sym, (st, h, l, cc, v) in kurse.items():
            if sym.upper() == "BTC":
                continue
            idx = np.array([sid[x] for x in st], np.int64)
            atr = GG.atr_tag_relativ(h, l, cc)
            stop = np.clip(K * atr, GG.STOP_MIN, GG.STOP_MAX)
            zz, ss, ro, gu, _g = GG.ausgaenge(h, l, cc, stop, crv * stop, H)
            mk = dict(a_faktoren(cc, atr))
            mr = merkmale_je_symbol(sym, st, h, l, cc, v, tm, fund)
            mk.update({k: val for k, val in mr.items() if k in NAMEN})
            a6 = np.full(len(cc), np.nan)
            if len(cc) > 6:
                a6[6:] = cc[6:] / np.maximum(cc[:-6], 1e-12) - 1.0
            mk["rueckstand_beta"] = br[idx] - a6
            gu = gu & ~np.nan_to_num(gesperrt[idx], nan=False)
            sel = np.flatnonzero(gu)
            if not len(sel):
                continue
            G.append(idx[sel])
            R.append(np.where(zz[sel], crv, np.where(ss[sel], -1.0,
                                                     np.nan_to_num(ro[sel]))))
            for k in NAMEN:
                MM[k].append(mk[k][sel] if k in mk
                             else np.full(len(sel), np.nan))
        G = np.concatenate(G); R = np.concatenate(R)
        MM = {k: np.concatenate(v) for k, v in MM.items()}
        er_alle = float(R.mean())
        mitte = int(np.median(G // 24))
        print()
        print("=" * 100)
        print("CRV %.1f · H%d · %d Anker · E[R]_alle %+.5f (±%.5f)"
              % (crv, H, len(G), er_alle, _tf(R, G)))

        # ── P3: wie hoch liegt ein ZUFAELLIG gewaehltes Fuenftel? ─────
        zw = []
        for _ in range(N_NULL):
            fz = fuenftel_je_stunde(G, rng.random(len(G)))
            if fz is None:
                continue
            i2, f2 = fz
            n2 = np.bincount(f2, minlength=5).astype(float)
            if (n2 < MIND_JE_FUENFTEL).any():
                continue
            e2 = np.bincount(f2, weights=R[i2], minlength=5) / n2
            zw.append(float(e2[int(rng.integers(0, 5))]))
        zg = float(np.percentile(np.array(zw), NULL_PERZ)) if zw else np.nan
        print("  P3 Zufallsfuenftel: Mittel %+.5f · %d. Perzentil %+.5f"
              % (float(np.mean(zw)) if zw else np.nan, int(NULL_PERZ), zg))
        print()
        print("  %-17s %4s %9s %9s %10s %10s  %s"
              % ("Merkmal", "F", "E[R]", "±Tagesf.", "Haelfte1", "Haelfte2",
                 "Urteil"))
        ergebnis = {}
        for name, f_soll in VORHERSAGE:
            fz = fuenftel_je_stunde(G, MM[name])
            if fz is None:
                continue
            i2, f2 = fz
            n5 = np.bincount(f2, minlength=5).astype(float)
            if (n5 < MIND_JE_FUENFTEL).any():
                continue
            m = np.zeros(len(G), bool)
            m[i2[f2 == f_soll]] = True
            w, se = float(R[m].mean()), _tf(R[m], G[m])
            h1 = m & (G // 24 <= mitte); h2 = m & (G // 24 > mitte)
            w1 = float(R[h1].mean()) if h1.sum() > 1000 else np.nan
            w2 = float(R[h2].mean()) if h2.sum() > 1000 else np.nan
            ergebnis[name] = (w, se, m)
            # ⚠️ TRAEGT nur, wenn alle drei halten: ueber dem
            # Zufallsfuenftel, von null verschieden, BEIDE Haelften positiv
            ok = (np.isfinite(zg) and w > zg and np.isfinite(se)
                  and w > 1.645 * se and w1 > 0 and w2 > 0)
            teil = (w > 0 and w1 > 0 and w2 > 0)
            print("  %-17s %4d %+9.5f %9.5f %+10.5f %+10.5f  %s"
                  % (name, f_soll, w, se, w1, w2,
                     "⭐⭐⭐ TRAEGT" if ok else
                     ("⚠️ positiv, aber nicht belegt" if teil else "⛔ nein")))

        # ── P4: die zwei staerksten geschnitten ──────────────────────
        top = sorted(ergebnis, key=lambda k: -ergebnis[k][0])[:2]
        if len(top) == 2:
            a, b = ergebnis[top[0]][2], ergebnis[top[1]][2]
            beide = a & b
            if beide.sum() >= MIND_JE_FUENFTEL:
                wa = float(R[a].mean()); wb = float(R[beide].mean())
                quote = beide.sum() / max(a.sum(), 1)
                nw = []
                for _ in range(N_NULL):
                    z = rng.random(len(G))
                    sw = np.quantile(z[a], quote)
                    mm = a & (z <= sw)
                    if mm.sum() >= MIND_JE_FUENFTEL:
                        nw.append(float(R[mm].mean()) - wa)
                g90 = float(np.percentile(np.array(nw), NULL_PERZ)) if nw \
                    else np.nan
                print("  P4 KOMBINATION  %s ∧ %s: %d Anker · E[R] %+.5f "
                      "(±%.5f)" % (top[0], top[1], int(beide.sum()), wb,
                                   _tf(R[beide], G[beide])))
                print("      Zugewinn %+.5f gegen Schrumpfungs-Band %+.5f · %s"
                      % (wb - wa, g90,
                         "✔ ueber dem Band" if wb - wa > g90
                         else "⛔ im Band - nur die Verkleinerung"))
    print()
    print("  ⚠️ TRAEGT verlangt DREI Dinge zugleich: ueber dem")
    print("     Zufallsfuenftel, von null verschieden (tagesgeblockt) UND")
    print("     in BEIDEN Haelften positiv.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
