# -*- coding: utf-8 -*-
"""Wieviel lassen die Sperren ZUSAMMEN durch? (02.09.2026)

Das System hat seit N-14 eine Sperre (`oi_aenderung`, oberstes Fuenftel),
und N-13-1' waere die zweite (relativer Volumenanteil). Jede nimmt fuer
sich rund ein Fuenftel weg.

⚠️ WARUM DAS NICHT ADDIERT WERDEN DARF. Zwei Regeln, die je 20 % sperren,
sperren zusammen zwischen 20 % (deckungsgleich) und 36 % (unabhaengig).
Welcher Wert gilt, ist eine MESSFRAGE - und nur die gemessene Zahl sagt,
ob die Kette danach noch spricht.

## Was hier gerechnet wird

  1  die Ueberlappung: wieviel sperren sie zusammen, gegen die beiden
     Randfaelle
  2  die WIRKUNG zusammen gegen die Wirkung jeder einzelnen - auf
     DENSELBEN Ankern, sonst vergleicht man zwei Mengen
  3  die verbleibende Menge je Assetklasse-Naeherung: wieviele Werte je
     Tag kaemen ueberhaupt noch durch

⚠️ DIE GEMEINSAME MENGE IST KLEINER ALS BEIDE. `oi_aenderung` gibt es fuer
122 Symbole, den Volumenanteil fuer 578. Gerechnet wird auf dem Schnitt -
und das ist die ehrliche Grundlage, weil nur dort BEIDE Sperren greifen
koennen. Fuer die uebrigen 456 Werte greift nur die zweite.

    python rechne_sperren_zusammen.py
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as M
import messe_kandidaten_als_regel as K
import messe_regel_wirksamkeit as W
import messe_volumenanteil as V

HORIZONT = 20
BLOCK = max(90, HORIZONT * 3)


def main():
    print("Lade...", flush=True)
    reihen = V._reihen()
    # --- die beiden Kennzahlen je (Tag, Symbol) -------------------------
    va = V.anteile_relativ(V.anteile(reihen))
    tm = K.lade_terminmarkt()["oi_aenderung"]
    oi = {}
    for sym, je in tm.items():
        for tag, wert in je.items():
            if wert is not None:
                oi.setdefault(tag, {})[sym] = float(wert)

    # --- Anker mit BEIDEN Werten ----------------------------------------
    je_tag = {}
    for sym, roh in reihen.items():
        tage = [z[0] for z in roh]
        c = np.array([z[1] for z in roh])
        h = np.array([z[2] for z in roh])
        t_ = np.array([z[3] for z in roh])
        br = V.B.spanne(h, t_, c, V.B.SCHWANKUNG)
        S = sym.upper()
        for i in range(60, len(c) - HORIZONT):
            r = br[i]
            if not np.isfinite(r) or r <= 0:
                continue
            a = (va.get(tage[i]) or {}).get(sym)
            b = (oi.get(tage[i]) or {}).get(S)
            if a is None or b is None:
                continue
            je_tag.setdefault(tage[i], []).append(
                {"sym": sym, "va": float(a), "oi": float(b),
                 "in_r": float((c[i + HORIZONT] - c[i]) / r)})
    je_tag = {t: z for t, z in je_tag.items() if len(z) >= V.MIND_JE_TAG}
    n = sum(len(z) for z in je_tag.values())
    syms = len({x["sym"] for z in je_tag.values() for x in z})
    print("Gemeinsame Menge: %d Anker · %d Symbole · %d Kalendertage"
          % (n, syms, len(je_tag)))

    # --- Sperranteile und Wirkung ---------------------------------------
    rng = np.random.default_rng(20260902)
    d_oi, d_va, d_beide, d_eines = {}, {}, {}, {}
    a_oi, a_va, a_beide, a_eines = [], [], [], []
    for tag, z in je_tag.items():
        y = np.array([x["in_r"] for x in z], float)
        r_oi = W.rang([x["oi"] for x in z])
        r_va = W.rang([x["va"] for x in z])
        f_oi = r_oi < W.GRENZE
        f_va = r_va < W.GRENZE
        f_beide = f_oi & f_va                  # beide Sperren muessen frei
        f_eines = f_oi | f_va                  # nur zur Anschauung
        if f_beide.sum() < 3:
            continue
        m = float(np.median(y))
        d_oi[tag] = float(np.median(y[f_oi]) - m)
        d_va[tag] = float(np.median(y[f_va]) - m)
        d_beide[tag] = float(np.median(y[f_beide]) - m)
        d_eines[tag] = float(np.median(y[f_eines]) - m)
        a_oi.append(float((~f_oi).mean()))
        a_va.append(float((~f_va).mean()))
        a_beide.append(float((~f_beide).mean()))
        a_eines.append(float((~f_eines).mean()))

    print()
    print("=" * 88)
    print("1) WIEVIEL WIRD GESPERRT?")
    print("=" * 88)
    print("  nur OI-Sperre (N-14)                  %.1f %%" % (100 * st.mean(a_oi)))
    print("  nur Volumenanteil (N-13-1')           %.1f %%" % (100 * st.mean(a_va)))
    print("  BEIDE (gesperrt, wer in EINEM oben)   %.1f %%" % (100 * st.mean(a_beide)))
    print()
    p1, p2 = st.mean(a_oi), st.mean(a_va)
    print("  Zum Vergleich die beiden Randfaelle:")
    print("    deckungsgleich  %.1f %%   (dann brachte die zweite nichts Neues)"
          % (100 * max(p1, p2)))
    print("    unabhaengig     %.1f %%   (dann sperrt jede etwas anderes)"
          % (100 * (1 - (1 - p1) * (1 - p2))))
    ueber = ((100 * st.mean(a_beide)) - 100 * max(p1, p2)) / \
            max(1e-9, (100 * (1 - (1 - p1) * (1 - p2)) - 100 * max(p1, p2)))
    print("    gemessen liegt es bei %.0f %% des Wegs zur Unabhaengigkeit"
          % (100 * ueber))

    print()
    print("=" * 88)
    print("2) WAS BRINGT DAS ZUSAETZLICH? — dieselben Anker, dieselbe Klammer")
    print("=" * 88)
    M.urteil_tage("  nur OI", d_oi, rng, BLOCK)
    M.urteil_tage("  nur Volumenanteil", d_va, rng, BLOCK)
    M.urteil_tage("  BEIDE zusammen", d_beide, rng, BLOCK)

    print()
    print("=" * 88)
    print("3) WAS BLEIBT ÜBRIG?")
    print("=" * 88)
    je = [len(z) for z in je_tag.values()]
    print("  Werte je Tag in der gemeinsamen Menge: Median %d" % int(np.median(je)))
    print("  davon nach beiden Sperren:             Median %d"
          % int(np.median(je) * (1 - st.mean(a_beide))))
    print()
    print("  ⚠️ Das ist die MESSEBENE. Im laufenden Trichter stehen zwoelf")
    print("     Stufen davor - was DORT uebrig bleibt, sagt nur")
    print("     `simuliere_kette.py`.")


if __name__ == "__main__":
    main()
