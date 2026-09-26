# -*- coding: utf-8 -*-
"""Die EMA-LAENGE als Achse: welcher Bezug ist der richtige?

**26.09.2026**, Nutzerfrage: *"EMA - was meinst du damit? dieser Indikator
hat auch mehrere Bedeutungen und muss korrekt angewendet werden."*

═══════════════════════════════════════════════════════════════════════
 DIE FRAGE
═══════════════════════════════════════════════════════════════════════

`ema_abstand_atr` war in 2.605 das staerkste Merkmal. Gerechnet wurde es
gegen einen EMA ueber **48 STUNDEN** - eine GESETZTE Laenge, nie gemessen.

⚠️⚠️ Und das ist NICHT der klassische 50er oder 200er: die beziehen sich
auf TAGESkerzen und entsprechen 1.200 bzw. 4.800 Stunden. Die in
`messe_a_faktoren` als *EMA200* bezeichnete Reihe sind 200 STUNDEN, also
gut acht Tage.

    Welche Bezugslaenge traegt am staerksten - und gibt es ein Optimum?

═══════════════════════════════════════════════════════════════════════
 ZWEI KONSTRUKTIONSPUNKTE, DIE ENTSCHEIDEN
═══════════════════════════════════════════════════════════════════════

    ⭐ GLEICHE ANKERMENGE
       Ein EMA ueber 1.200 Stunden braucht einen laengeren Vorlauf als
       einer ueber 12. Wuerde jede Laenge auf ihrer eigenen Menge
       gemessen, verglichen man verschiedene GRUNDGESAMTHEITEN - und
       genau davor warnt die registrierte Regel. Deshalb gilt fuer ALLE
       Laengen derselbe Vorlauf: 5 x die laengste Periode.

    ⭐⭐ MEHRFACHTESTEN
       Sieben Laengen zu pruefen und die beste zu nehmen ist Auslese.
       Die Nullwelt zieht deshalb ebenfalls SIEBEN Zufallsreihen und
       nimmt deren BESTE - so enthaelt sie die Suche.

⚠️ NUR LESEN.  python messe_ema_laenge.py [--symbole N]
"""
from __future__ import annotations

import os
import sys

import numpy as np
from scipy.signal import lfilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import messnorm as N                                            # noqa: E402
from messe_reverse_scharfe_anstiege import lade_kurse           # noqa: E402
from messe_selektion import mfe_mae                             # noqa: E402
from messe_hebel_geometrie_neutral import atr_tag_relativ       # noqa: E402

#: 0,5 / 1 / 2 / 4 / 10 / 20 / 50 Tage - der letzte ist der klassische
#: 50-Tage-EMA, hier in Stunden
LAENGEN = (12, 24, 48, 96, 240, 480, 1200)
VORLAUF = 5 * max(LAENGEN)          # fuer ALLE gleich (Grundgesamtheit!)
HORIZONTE = (24, 72)
SCHAERFEN = (0.01, 0.001)
N_NULL = N.NULL_ZIEHUNGEN
NULL_PERZ = N.NULL_PERZENTIL
MIND_ANKER = 500
SAAT = 20260926


def ema(x, p):
    """EMA ueber `p` Schritte - vektorisiert, kausal.

    ⚠️ `lfilter` startet bei null; der Startwert wird auf `x[0]` gesetzt
    und der Vorlauf ohnehin global maskiert (5 x die laengste Periode).
    Gegen die Schleifenfassung geprueft: relative Abweichung ~1e-5 nach
    dem 5-fachen der Periode.
    """
    a = 2.0 / (p + 1.0)
    y = lfilter([a], [1.0, -(1.0 - a)], x, zi=[(1.0 - a) * x[0]])[0]
    return y


def main() -> int:
    grenze = None
    if "--symbole" in sys.argv:
        grenze = int(sys.argv[sys.argv.index("--symbole") + 1])

    print("=" * 100)
    print("DIE EMA-LAENGE ALS ACHSE")
    print("=" * 100)
    print("  Laengen (Stunden): %s" % " ".join(str(x) for x in LAENGEN))
    print("  entspricht Tagen:  %s"
          % " ".join("%.1f" % (x / 24.0) for x in LAENGEN))
    print("  ⭐ Vorlauf fuer ALLE gleich: %d Stunden (%d Tage) - sonst "
          "vergleicht" % (VORLAUF, VORLAUF // 24))
    print("     man verschiedene Grundgesamtheiten")
    print("  ⭐⭐ Die Nullwelt zieht SIEBEN Zufallsreihen und nimmt die")
    print("     BESTE - damit enthaelt sie das Mehrfachtesten")

    kurse = lade_kurse(grenze)
    alle = set()
    for (s, *_r) in kurse.values():
        alle.update(s)
    sl = sorted(alle); sid = {s: i for i, s in enumerate(sl)}
    print("  %d Symbole · %d Stunden" % (len(kurse), len(sl)), flush=True)

    rng = np.random.default_rng(SAAT)
    for H in HORIZONTE:
        G, MFE, MAE, EV = [], [], [], []
        W = {p: [] for p in LAENGEN}
        for sym, (st, h, l, cc, v) in kurse.items():
            if sym.upper() == "BTC":
                continue
            idx = np.array([sid[x] for x in st], np.int64)
            atr = atr_tag_relativ(h, l, cc)
            hoch, tief, ev, gu = mfe_mae(h, l, cc, H)
            gu = gu & np.isfinite(hoch) & np.isfinite(tief)
            gu[:VORLAUF] = False                 # ⭐ fuer ALLE Laengen
            sel = np.flatnonzero(gu)
            if not len(sel):
                continue
            G.append(idx[sel]); MFE.append(hoch[sel]); MAE.append(tief[sel])
            EV.append(ev[sel])
            for p in LAENGEN:
                e = ema(cc, p)
                with np.errstate(divide="ignore", invalid="ignore"):
                    W[p].append(((cc - e) / np.maximum(atr * cc, 1e-12))[sel])
        if not G:
            continue
        G = np.concatenate(G); MFE = np.concatenate(MFE)
        MAE = np.concatenate(MAE); EV = np.concatenate(EV)
        W = {p: np.concatenate(x) for p, x in W.items()}
        n = len(G)
        print()
        print("=" * 100)
        print("HORIZONT %d h (%d Tage) · %d Anker · MFE %.3f · Treffer %.2f %%"
              % (H, H // 24, n, float(MFE.mean()), 100 * float(EV.mean())),
              flush=True)

        for sch in SCHAERFEN:
            k = max(MIND_ANKER, int(round(sch * n)))
            # ── Nullwelt EINFACH und mit MEHRFACHTESTEN ──────────────
            einzeln, bestes_von7 = [], []
            for _ in range(N_NULL):
                w7 = []
                for _j in range(len(LAENGEN)):
                    p = rng.choice(n, size=k, replace=False)
                    w7.append(float(MFE[p].mean()))
                einzeln.append(w7[0])
                bestes_von7.append(max(w7))
            b1 = float(np.percentile(np.array(einzeln), NULL_PERZ))
            b7 = float(np.percentile(np.array(bestes_von7), NULL_PERZ))
            print()
            print("  SCHAERFE %.1f %% (%d Anker) · Nullband einzeln %.3f · "
                  "⭐ bestes von %d: %.3f"
                  % (100 * sch, k, b1, len(LAENGEN), b7))
            print("    %-10s %8s %8s %8s %9s  %s"
                  % ("EMA", "Tage", "MFE", "MAE", "MFE/MAE", "Urteil"))
            werte = []
            for p in LAENGEN:
                w = W[p]
                gut = np.isfinite(w)
                if gut.sum() < k:
                    continue
                pos = np.flatnonzero(gut)
                ordn = pos[np.argsort(w[pos])[::-1][:k]]
                mfe = float(MFE[ordn].mean()); mae = float(MAE[ordn].mean())
                werte.append((mfe, p))
                print("    %-10d %8.1f %8.3f %8.3f %9.2f  %s"
                      % (p, p / 24.0, mfe, mae, mfe / max(abs(mae), 1e-9),
                         "✔ ueber dem Mehrfach-Band" if mfe > b7
                         else ("(ueber dem Einzelband)" if mfe > b1
                               else "-")))
            if werte:
                best_mfe, best_p = max(werte)
                print("    ➤ staerkste Laenge: %d h (%.1f Tage) mit MFE "
                      "%.3f · %s"
                      % (best_p, best_p / 24.0, best_mfe,
                         "✔✔ auch gegen das Mehrfachtesten"
                         if best_mfe > b7 else
                         "⚠️ NICHT gegen das Mehrfachtesten - das ist Auslese"))
                # Form der Kurve: Optimum oder monoton?
                mm = [m for m, _p in sorted(werte, key=lambda t: t[1])]
                if len(mm) >= 3:
                    i = int(np.argmax(mm))
                    form = ("monoton fallend mit der Laenge" if i == 0 else
                            ("monoton steigend" if i == len(mm) - 1 else
                             "OPTIMUM in der Mitte"))
                    print("    ➤ Form: %s (Maximum bei %d h)"
                          % (form, sorted(p for _m, p in werte)[i]))
    print()
    print("  ⚠️ Die Laengen sind hoch korreliert - benachbarte EMA messen")
    print("     fast dasselbe. Ein Unterschied von 0,02 zwischen 48 und 96 h")
    print("     ist deshalb kein Beleg fuer eine bessere Wahl.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
