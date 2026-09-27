# -*- coding: utf-8 -*-
"""Welche Zielgroesse bildet "hoch und kurz" ab? - Phase 1a.

**27.09.2026**, Nutzervorgabe: *"Der Einstieg funktioniert ... zu einem
Zeitpunkt, wo der HORIZONT NICHT BEKANNT ist - was aber bekannt ist aus
der Historie: welche Lagen und Potential fuehrten zu einem HOHEN KURZEN
ANSTIEG."* Und: *"sei nur vorsichtig mit ERTRAG - u.U. nimmt man
Kursanstieg oder eine andere Groesse, die korrekter ist."*

Vorabfestlegung: `Basisinfos/Vorabfestlegung_33_Zielgroesse_hoch_und_kurz_27_09.md`

═══════════════════════════════════════════════════════════════════════
 ⚠️ WARUM NICHT "ERTRAG"
═══════════════════════════════════════════════════════════════════════

Der Ertrag ist das, was eine BESTIMMTE Handelsregel (Stop 1,00, Trailing
1,5 / 0,5) aus einer Lage macht. Wer die Regel optimiert UND den Massstab
daraus ableitet, schliesst einen Kreis.

➤ Die Bewertung misst das POTENTIAL DER LAGE - nicht, was eine Regel
daraus holt. Deshalb MFE und MAE in ATR:

    MFE in ATR     wie hoch geht es, in der eigenen Schwankungsbreite
    MAE in ATR     wie tief geht es vorher gegen mich
    MFE/MAE        die Asymmetrie - MFE ALLEIN TRENNT NICHT (2.606)
    Zeit bis MFE   "kurz"

⚠️ NICHT in R: R = Stopweite * ATR, und die Stopweite ist ein
Regelparameter. ATR ist eine Markteigenschaft.

⚠️ NUR LESEN.  python messe_zielgroesse.py [--symbole N]
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

FENSTER = (6, 12, 24, 48, 72, 120)
ANTEIL = 0.01
MAE_MIN = 0.05          # Untergrenze, sonst explodiert MFE/MAE (Falle 7)
SAAT = 20260927
# aus 2.628 - nur fuer den VERGLEICHSARM, nicht fuer die Zielgroessen
STOP, AUSL, ABST = 1.00, 1.5, 0.5


def mfe_mae_zeit(high, low, close, atr, H):
    """MFE, MAE und die ZEIT BIS MFE - in ATR, streng kausal, REGELFREI.

    ⚠️ Anders als `messe_selektion.mfe_mae` ohne Ziel und ohne Stop: hier
    soll KEIN Regelparameter hinein. Zurueck kommt, was der Markt getan
    hat, nicht was eine Regel daraus gemacht haette."""
    n = len(close)
    idx = np.arange(n)
    lauf_h = np.full(n, -np.inf)
    lauf_t = np.full(n, np.inf)
    zeit_h = np.zeros(n)
    for s in range(1, H + 1):
        j = np.minimum(idx + s, n - 1)
        besser = high[j] > lauf_h
        zeit_h = np.where(besser, s, zeit_h)
        lauf_h = np.maximum(lauf_h, high[j])
        lauf_t = np.minimum(lauf_t, low[j])
    with np.errstate(divide="ignore", invalid="ignore"):
        mfe = (lauf_h / np.maximum(close, 1e-12) - 1.0) / np.maximum(atr, 1e-9)
        mae = (lauf_t / np.maximum(close, 1e-12) - 1.0) / np.maximum(atr, 1e-9)
    return mfe, mae, zeit_h


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 110)
    print("WELCHE ZIELGROESSE BILDET \"HOCH UND KURZ\" AB?")
    print("=" * 110)
    print("  " + N.standardzeile())
    print("  ⚠️ NICHT der Ertrag: er enthaelt Stop und Trailing. MFE/MAE in")
    print("     ATR sind REGELFREI. Der Ertrag laeuft nur als Vergleichsarm.")
    print("  Fenster %s Stunden · Auswahlanteil %.1f %%"
          % ("/".join(str(x) for x in FENSTER), 100 * ANTEIL))
    print()

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    maxH = max(FENSTER)
    G, W = [], []
    ZG = {}                       # (name, H) -> Liste
    for sym, (st, h, l, cc, v) in kurse.items():
        if sym.upper() == "BTC":
            continue
        gi = np.array([sid[x] for x in st], np.int64)
        atr = atr_tag_relativ(h, l, cc)
        e = ema(cc, EMA_L)
        with np.errstate(divide="ignore", invalid="ignore"):
            w = (cc - e) / np.maximum(atr * cc, 1e-12)
        gu = np.isfinite(atr) & (atr > 0) & np.isfinite(w)
        gu[:VORLAUF] = False
        gu[max(0, len(cc) - maxH):] = False      # fuer ALLE Fenster gueltig
        sel = np.flatnonzero(gu)
        if len(sel) < 500:
            continue
        G.append(gi[sel]); W.append(w[sel])
        for H in FENSTER:
            mfe, mae, zeit = mfe_mae_zeit(h, l, cc, atr, H)
            _r, p, _g = trailing_mit_ausloeser(h, l, cc, atr, STOP, AUSL,
                                               ABST, H)
            maeb = np.minimum(mae, -MAE_MIN)     # Falle 7
            ZG.setdefault(("MFE", H), []).append(mfe[sel])
            ZG.setdefault(("MAE", H), []).append(mae[sel])
            ZG.setdefault(("MFE/MAE", H), []).append(mfe[sel] / np.abs(maeb[sel]))
            # Zeit ist umgekehrt gepolt (Falle 6) -> negativ, damit
            # "groesser ist besser" ueberall gilt
            ZG.setdefault(("-Zeit bis MFE", H), []).append(-zeit[sel])
            ZG.setdefault(("MFE je Stunde", H), []).append(
                mfe[sel] / np.maximum(zeit[sel], 1.0))
            ZG.setdefault(("Ertrag (Vergleich)", H), []).append(p[sel])
    G = np.concatenate(G); W = np.concatenate(W)
    ZG = {k: np.concatenate(v) for k, v in ZG.items()}
    tag = G // 24
    n = len(G)
    print("  %d Anker · %d Tage · %d Symbole  (fuer ALLE Fenster gueltig)"
          % (n, len(np.unique(tag)), len(kurse)), flush=True)
    print()

    rng = np.random.default_rng(SAAT)
    pool = {}
    for i_ in range(n):
        pool.setdefault(int(tag[i_]), []).append(i_)
    pool = {t: np.array(v) for t, v in pool.items()}

    k = max(50, int(round(ANTEIL * n)))
    o = np.argsort(W, kind="stable")[:k]        # invers: die niedrigsten
    maske = np.zeros(n, bool); maske[o] = True
    je = {int(t): int(c) for t, c in
          zip(*np.unique(tag[maske], return_counts=True))}
    # ⭐ EINE Ziehungsmenge fuer ALLE Zielgroessen - so ist der Vergleich
    # gepaart und die Unterschiede sind nicht Ziehungsrauschen.
    ziehungen = []
    for _ in range(N.NULL_ZIEHUNGEN):
        a = []
        for t, c in je.items():
            pl = pool.get(t)
            if pl is not None and len(pl):
                a.append(rng.choice(pl, size=min(c, len(pl)), replace=False))
        if a:
            ziehungen.append(np.concatenate(a))

    print("=" * 110)
    print("DER STANDARDISIERTE ABSTAND  (echt - Nullmittel) / Nullstreuung")
    print("  ⭐ Nur so sind Groessen mit verschiedenen Einheiten "
          "vergleichbar.")
    print()
    namen = ["MFE", "MAE", "MFE/MAE", "-Zeit bis MFE", "MFE je Stunde",
             "Ertrag (Vergleich)"]
    print("  %-20s %s" % ("Zielgroesse",
                          " ".join("%9s" % ("H%d" % H) for H in FENSTER)))
    tabelle = {}
    effekt = {}
    roh = {}
    for nm in namen:
        zell = []
        for H in FENSTER:
            x = ZG[(nm, H)]
            gut = np.isfinite(x)
            echt = float(x[maske & gut].mean())
            nb = np.array([float(x[idx][np.isfinite(x[idx])].mean())
                           for idx in ziehungen])
            sd = float(nb.std())
            z = (echt - float(nb.mean())) / max(sd, 1e-12)
            # ⚠️ Das EFFEKTMASS: gegen die Streuung der EINZELWERTE, nicht
            # der Ziehungsmittel. Bei 3 Mio Ankern ist z fast immer gross;
            # d sagt, ob der Unterschied auch GROSS ist.
            sd_einzel = float(x[gut].std())
            d = (echt - float(nb.mean())) / max(sd_einzel, 1e-12)
            zell.append(z)
            tabelle[(nm, H)] = z; effekt[(nm, H)] = d
            roh[(nm, H)] = (echt, float(nb.mean()))
        print("  %-20s %s" % (nm, " ".join("%+9.2f" % v for v in zell)))

    print()
    print("  DASSELBE ALS EFFEKTMASS (Cohens d - wie GROSS, nicht wie sicher)")
    print("  %-20s %s" % ("Zielgroesse",
                          " ".join("%9s" % ("H%d" % H) for H in FENSTER)))
    for nm in namen:
        print("  %-20s %s"
              % (nm, " ".join("%+9.3f" % effekt[(nm, H)] for H in FENSTER)))
    print()
    print("  Lesart: d unter 0,2 ist klein, 0,5 mittel, ab 0,8 gross.")
    print()
    print("  UND DIE ROHWERTE - damit sichtbar ist, worum es geht")
    print("  %-20s %s" % ("Zielgroesse (echt/null)",
                          " ".join("%17s" % ("H%d" % H) for H in FENSTER)))
    for nm in namen:
        print("  %-20s %s"
              % (nm, " ".join("%8.3f /%7.3f" % roh[(nm, H)]
                              for H in FENSTER)))

    print()
    print("=" * 110)
    print("P5 - MEHRFACHTESTEN ueber %d Zellen" % (len(namen) * len(FENSTER)))
    print("  ⚠️ Der standardisierte Abstand IST bereits ein z-Wert; das")
    print("     Mehrfachtesten verlangt eine strengere Grenze als 1,64.")
    from math import sqrt
    try:
        from scipy.stats import norm
        grenze_z = float(norm.ppf(1 - 0.05 / (len(namen) * len(FENSTER))))
    except Exception:
        grenze_z = 3.2
    print("  Bonferroni-Grenze bei %d Zellen: z > %.2f"
          % (len(namen) * len(FENSTER), grenze_z))
    halten = [(nm, H, v) for (nm, H), v in tabelle.items() if v > grenze_z]
    print("  Zellen darueber: %d von %d" % (len(halten), len(tabelle)))
    if halten:
        best = max(halten, key=lambda x: x[2])
        print("  staerkste: %s bei H%d mit z = %+.2f"
              % (best[0], best[1], best[2]))

    print()
    print("=" * 110)
    print("DIE FRAGE VON 2.626/2.628 - kurz oder lang?")
    print("  ⚠️ Falle 8: laengere Fenster haben MECHANISCH hoeheres MFE.")
    print("     Deshalb zaehlt die ORDNUNG (z), nicht der Rohwert.")
    print()
    print("  %-20s %10s %10s %10s %10s  %s"
          % ("Zielgroesse", "bestes H", "z dort", "bestes H", "d dort",
             "Richtung (d)"))
    print("  %-20s %10s %10s %10s %10s"
          % ("", "nach z", "", "nach d", ""))
    for nm in namen:
        bHz, bz = max(((H, tabelle[(nm, H)]) for H in FENSTER),
                      key=lambda x: x[1])
        bHd, bd = max(((H, effekt[(nm, H)]) for H in FENSTER),
                      key=lambda x: x[1])
        rich = ("kurz" if bHd <= 12 else ("mittel" if bHd <= 48 else "lang"))
        print("  %-20s %10s %+10.2f %10s %+10.3f  %s"
              % (nm, "H%d" % bHz, bz, "H%d" % bHd, bd, rich))
    print()
    print("  ⚠️ Weichen die beiden Spalten ab, entscheidet d - z waechst")
    print("     mit der Stichprobe, d nicht.")

    print()
    print("  ⚠️ Gebuehren und Finanzierung sind NICHT eingerechnet (Regel 2).")
    print("  ⚠️ Das Ergebnis fliesst NICHT als Schwelle in die Bewertung")
    print("     zurueck - das ist Ebene B (2.641).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
