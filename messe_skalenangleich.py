# -*- coding: utf-8 -*-
"""Laesst sich die Skala von Stufe D angleichen - und traegt sie dann?

**27.09.2026**, aus der Bewertungsfrage zur CoinGecko-Anbindung.

Vorabfestlegung: `Basisinfos/Vorabfestlegung_30_Skalenangleich_27_09.md`

═══════════════════════════════════════════════════════════════════════
 WARUM
═══════════════════════════════════════════════════════════════════════

Dieselbe Schwelle -1,2881 trifft bei Stufe A (echtes OHLC) 0,330 Prozent
der Anker, bei Stufe D (nur Schlusskurse) 8,515 Prozent - Faktor 25,8.
Die ATR-Ersatzgroesse ist etwa halb so gross, `W` wird doppelt so gross
im Betrag.

⭐ Die Rangkorrelation ist 0,9964: DIE ORDNUNG STIMMT, NUR DIE SKALA
NICHT.

═══════════════════════════════════════════════════════════════════════
 ⚠️⚠️ WOHER DER FAKTOR KOMMT - UND WOHER NICHT
═══════════════════════════════════════════════════════════════════════

    erlaubt    aus dem VERHAELTNIS DER ATR-GROESSEN - eine reine
               Skaleneigenschaft der Messgroesse
    ⛔ verboten aus dem ERTRAG oder der Trefferzahl - das waere
               Kurvenanpassung, und genau davor warnt 2.616 beim
               Wurzel-24-Faktor (*hergeleitet, nicht angepasst*)

⚠️ NUR LESEN.  python messe_skalenangleich.py [--symbole N]
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
SCHWELLE = -1.2881          # aus 2.632, gerechnete Kelly-Nullstelle
SAAT = 20260927


def atr_aus_schluessen(c: np.ndarray) -> np.ndarray:
    """Stufe D aus 2.616: OHNE High und Low.

    Mittlere absolute Stundenrendite ueber 24 h, mal Wurzel 24 auf
    Tagesmass. ⚠️ Der Wurzelfaktor ist HERGELEITET (Irrfahrt), nicht an
    ein Ergebnis angepasst - genau das ist der Punkt, und genau deshalb
    trifft er die Skala nicht."""
    r = np.zeros(len(c))
    r[1:] = np.abs(np.diff(c)) / np.maximum(c[:-1], 1e-12)
    m = np.convolve(r, np.ones(24) / 24, mode="full")[:len(c)]
    out = np.full(len(c), np.nan)
    out[24:] = m[23:-1]                     # kausal: ohne die laufende Stunde
    return out * np.sqrt(24.0)


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 104)
    print("LAESST SICH DIE SKALA VON STUFE D ANGLEICHEN?")
    print("=" * 104)
    print("  " + N.standardzeile())
    print("  Geometrie H%d / Stop %.2f ATR / Trailing %.1f / %.1f (2.628)"
          % (HZ, STOP, AUSL, ABST))
    print("  Schwelle %.4f aus 2.632" % SCHWELLE)
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}

    G, P, ZA, AA, AD, SY = [], [], [], [], [], []
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        gi = np.array([sid[x] for x in st], np.int64)
        aA = atr_tag_relativ(h, l, cc)
        aD = atr_aus_schluessen(cc)
        e = ema(cc, EMA_L)
        _r, p, _g = trailing_mit_ausloeser(h, l, cc, aA, STOP, AUSL, ABST, HZ)
        gu = (np.isfinite(aA) & (aA > 0) & np.isfinite(aD) & (aD > 0)
              & np.isfinite(e) & np.isfinite(p))
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - HZ):] = False
        s2 = np.flatnonzero(gu)
        if len(s2) < 500:
            continue
        G.append(gi[s2]); P.append(p[s2])
        ZA.append(cc[s2] - e[s2])           # Zaehler, in BEIDEN gleich
        AA.append(aA[s2] * cc[s2]); AD.append(aD[s2] * cc[s2])
        SY.append(np.full(len(s2), sym, object))
    G = np.concatenate(G); P = np.concatenate(P); ZA = np.concatenate(ZA)
    AA = np.concatenate(AA); AD = np.concatenate(AD); SY = np.concatenate(SY)
    tag = G // 24
    n = len(G)
    print("  %d Anker · %d Tage · %d Symbole"
          % (n, len(np.unique(tag)), len(set(SY))), flush=True)
    print()

    WA = ZA / np.maximum(AA, 1e-12)
    WD = ZA / np.maximum(AD, 1e-12)

    # ══ 1. DER FAKTOR - aus der ATR-Verteilung, NICHT aus dem Ertrag ══
    print("=" * 104)
    print("TEIL 1 - DER FAKTOR (aus dem ATR-Verhaeltnis, Falle 1)")
    print("  ⛔ Der Ertrag geht hier NICHT ein.")
    print()
    global_f = float(np.median(AA) / np.median(AD))
    print("  globaler Faktor = median(ATR_A)/median(ATR_D) = %.4f" % global_f)
    print("  (Kehrwert %.4f - die aus 2.616/2.618 bekannte "
          "Methodendifferenz 0,48x)" % (1 / global_f))
    print()
    je = {}
    for sy in sorted(set(SY)):
        m = SY == sy
        je[sy] = float(np.median(AA[m]) / np.median(AD[m]))
    w = np.array(list(je.values()))
    print("  JE SYMBOL (Falle 3 - ein globaler Faktor taugt nur, wenn er "
          "nicht davonlaeuft):")
    print("    Median %.4f · Mittel %.4f · Streuung %.4f"
          % (np.median(w), w.mean(), w.std()))
    print("    5. Perzentil %.4f · 95. Perzentil %.4f · Spanne %.4f bis %.4f"
          % (np.percentile(w, 5), np.percentile(w, 95), w.min(), w.max()))
    print("    Variationskoeffizient %.1f %%" % (100 * w.std() / w.mean()))
    aus = [(s, f) for s, f in je.items()
           if f < np.percentile(w, 2) or f > np.percentile(w, 98)]
    print("    Ausreisser: %s"
          % ", ".join("%s %.2f" % (s, f) for s, f in sorted(
              aus, key=lambda x: x[1])[:8]))

    # ══ 2. TRAEGT D KORRIGIERT BEI DERSELBEN SCHWELLE? ═══════════════
    rng = np.random.default_rng(SAAT)
    pool = {}
    for i_ in range(n):
        pool.setdefault(int(tag[i_]), []).append(i_)
    pool = {t: np.array(v) for t, v in pool.items()}

    def band(m):
        jed = {int(t): int(c) for t, c in
               zip(*np.unique(tag[m], return_counts=True))}
        o = []
        for _ in range(N.NULL_ZIEHUNGEN):
            a = []
            for t, c in jed.items():
                pl = pool.get(t)
                if pl is not None and len(pl):
                    a.append(rng.choice(pl, size=min(c, len(pl)),
                                        replace=False))
            if a:
                o.append(float(P[np.concatenate(a)].mean()))
        return 100 * float(np.percentile(np.array(o), N.NULL_PERZENTIL)) \
            if o else float("nan")

    WDg = WD / global_f                       # global korrigiert
    fje = np.array([je[s] for s in SY])
    WDj = WD / fje                            # je Symbol korrigiert

    print()
    print("=" * 104)
    print("TEIL 2 - TRAEGT ES BEI DERSELBEN SCHWELLE %.4f?" % SCHWELLE)
    print()
    print("  %-26s %10s %9s %12s %12s %10s  %s"
          % ("Variante", "Treffer", "Anteil", "Ertrag %", "Nullband",
             "Abstand", "Urteil"))
    for lab, W in (("A  echtes OHLC", WA),
                   ("D  unkorrigiert", WD),
                   ("D  global korrigiert", WDg),
                   ("D  je Symbol korrigiert", WDj)):
        m = W <= SCHWELLE
        if m.sum() < 100:
            print("  %-26s %10d  zu wenige" % (lab, int(m.sum()))); continue
        er = 100 * float(P[m].mean()); nb = band(m)
        print("  %-26s %10d %8.3f%% %+12.4f %+12.4f %+10.4f  %s"
              % (lab, int(m.sum()), 100 * m.mean(), er, nb, er - nb,
                 "✔" if er > nb else "⛔ im Band"), flush=True)

    # ══ 3. KONTROLLE: gleicher ANTEIL statt gleicher Schwelle ════════
    print()
    print("=" * 104)
    print("TEIL 3 - KONTROLLE bei gleichem ANTEIL (reproduziert 2.616)")
    print("  ⭐ Hier MUSS D tragen - sonst stimmt am Aufbau etwas nicht.")
    print()
    k = int((WA <= SCHWELLE).sum())
    print("  %-26s %10s %12s %12s %10s  %s"
          % ("Variante", "Treffer", "Ertrag %", "Nullband", "Abstand",
             "Urteil"))
    for lab, W in (("A  echtes OHLC", WA), ("D  nur Schlusskurse", WD)):
        o = np.argsort(W, kind="stable")[:k]
        m = np.zeros(n, bool); m[o] = True
        er = 100 * float(P[m].mean()); nb = band(m)
        print("  %-26s %10d %+12.4f %+12.4f %+10.4f  %s"
              % (lab, int(m.sum()), er, nb, er - nb,
                 "✔" if er > nb else "⛔ im Band"), flush=True)

    # ══ 4. OUT-OF-SAMPLE auf dem FAKTOR ══════════════════════════════
    print()
    print("=" * 104)
    print("TEIL 4 - OUT-OF-SAMPLE (Falle 2): Faktor aus der einen Haelfte")
    print()
    ut = np.unique(tag); mitte = ut[len(ut) // 2]
    print("  %-22s %10s %10s %12s %12s  %s"
          % ("Richtung", "Faktor", "Treffer", "Ertrag %", "Nullband",
             "Urteil"))
    for lab, mtr, mte in (("1. Haelfte -> 2.", tag < mitte, tag >= mitte),
                          ("2. Haelfte -> 1.", tag >= mitte, tag < mitte)):
        f = float(np.median(AA[mtr]) / np.median(AD[mtr]))
        m = mte & ((WD / f) <= SCHWELLE)
        if m.sum() < 100:
            print("  %-22s %10.4f  zu wenige (%d)" % (lab, f, int(m.sum())))
            continue
        er = 100 * float(P[m].mean()); nb = band(m)
        print("  %-22s %10.4f %10d %+12.4f %+12.4f  %s"
              % (lab, f, int(m.sum()), er, nb,
                 "✔" if er > nb else "⛔ im Band"), flush=True)

    print()
    print("  ⚠️ Gemessen auf Symbolen MIT OHLC - nur dort sind A und D")
    print("     vergleichbar. Fuer die 16 ohne ist es eine UEBERTRAGUNG.")
    print("  ⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet (Regel 2).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
