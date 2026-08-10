# -*- coding: utf-8 -*-
"""Traegt die Analogie? - auf Tausenden von Faellen statt auf 32.

WARUM ES DIESE ZWEITE DATEI GIBT. Der erste Anlauf hat die Analogie auf denselben
80 Ankern gemessen wie den Sprachmodell-Lauf. Das klang nach Sorgfalt - dieselben
Faelle, fairer Vergleich - war aber ein Denkfehler: fuer die Frage "taugt die
Analogie" braucht es die Sprachmodell-Anker ueberhaupt nicht. Uebrig blieben nach
der Kausalitaetsbedingung 32 Faelle, und der Cluster-Bootstrap sagte klar, was
davon zu halten ist: 95 %-Bereich [-0,296 .. +0,034], die Null mittendrin.

Die Anker braucht man NUR fuer den Vergleich MIT dem Sprachmodell. Die Frage, ob
die Analogie ueberhaupt etwas kann, beantwortet man an der ganzen Historie - hier
rund 15.000 auswertbare Punkte, die nichts kosten ausser Rechenzeit.

VEKTORISIERT, weil es sonst nicht laeuft: 2.000 Testfaelle gegen 15.000 Kandidaten
sind 30 Millionen Abstandsberechnungen. Als Schleife in Python waere das eine
Kaffeepause, als Matrixoperation sind es Sekunden.

    python pruefe_analogie_gross.py --k 10 --testfaelle 2000
"""
from __future__ import annotations

import argparse
import random
import statistics
import sys
from collections import defaultdict

import numpy as np

from agent.szenario_fakten import AUSGAENGE
from backtest_llm1_historisch import lade_reihen
from pruefe_analogie import MERKMALE, _merkmalstabelle

SCHLUESSEL = tuple(f"{a}_zuerst_pct" if a != "keines" else "keines_pct"
                   for a in AUSGAENGE)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--k", type=int, default=10)
    p.add_argument("--testfaelle", type=int, default=2000)
    p.add_argument("--mindestabstand-tage", type=int, default=0)
    p.add_argument("--seed", type=int, default=20260810)
    args = p.parse_args()

    reihen = lade_reihen()
    tab = []
    for sym, r in reihen.items():
        tab.extend(_merkmalstabelle(r, sym))
    if len(tab) < 1000:
        print("[FEHLER] zu wenige Faelle")
        return 2

    # --- Alles in Arrays, einmal ------------------------------------------
    M = np.array([[z[m] for m in MERKMALE] for z in tab], dtype=float)
    M = (M - M.mean(axis=0)) / (M.std(axis=0) + 1e-12)
    datum = np.array([z["datum"] for z in tab])
    bekannt = np.array([z["bekannt_ab"] for z in tab])
    symbol = np.array([z["symbol"] for z in tab])
    richtung = np.array([z["richtung"] for z in tab])
    ausgang = np.array([z["ausgang"] for z in tab])
    ist_ziel = (ausgang == "ziel").astype(float)
    ist_stop = (ausgang == "stop").astype(float)
    ist_kein = (ausgang == "keines").astype(float)

    print(f"{len(tab)} Faelle ueber {len(set(symbol))} Symbole, "
          f"{min(datum)} bis {max(datum)}")

    # Basisrate ueber die TESTFAELLE, nicht ueber alle - sonst vergleicht man
    # gegen eine Haeufigkeit, die die Testmenge gar nicht hat.
    rng = random.Random(args.seed)
    idx = sorted(rng.sample(range(len(tab)), min(args.testfaelle, len(tab))))
    basis = {s: 100.0 * float(v[idx].mean())
             for s, v in zip(SCHLUESSEL, (ist_ziel, ist_stop, ist_kein))}
    print(f"Testfaelle: {len(idx)}   Basisrate "
          + "  ".join(f"{s.split('_')[0]}={basis[s]:.1f} %" for s in SCHLUESSEL))

    b_ana, b_bas, je_symbol, ohne = [], [], defaultdict(list), 0
    for t in idx:
        grenze = datum[t]
        if args.mindestabstand_tage:
            import datetime
            grenze = str(datetime.date.fromisoformat(str(datum[t]))
                         - datetime.timedelta(days=args.mindestabstand_tage))
        # KAUSAL: Ausgang muss feststehen; anderes Symbol; gleiche Richtung.
        maske = (bekannt < grenze) & (symbol != symbol[t]) & (richtung == richtung[t])
        n = int(maske.sum())
        if n < args.k:
            ohne += 1
            continue
        kand = np.nonzero(maske)[0]
        dist = ((M[kand] - M[t]) ** 2).sum(axis=1)
        nah = kand[np.argpartition(dist, args.k - 1)[:args.k]]
        # Laplace-Glaettung wie im kleinen Lauf
        v = {s: 100.0 * (float(arr[nah].sum()) + 1) / (args.k + 3)
             for s, arr in zip(SCHLUESSEL, (ist_ziel, ist_stop, ist_kein))}
        wahr = {SCHLUESSEL[0]: ist_ziel[t], SCHLUESSEL[1]: ist_stop[t],
                SCHLUESSEL[2]: ist_kein[t]}
        ba = sum((v[s] / 100.0 - wahr[s]) ** 2 for s in SCHLUESSEL)
        bb = sum((basis[s] / 100.0 - wahr[s]) ** 2 for s in SCHLUESSEL)
        b_ana.append(ba)
        b_bas.append(bb)
        je_symbol[str(symbol[t])].append(ba - bb)

    if not b_ana:
        print("[FEHLER] keine auswertbaren Testfaelle")
        return 1

    print(f"\n{'=' * 62}")
    print(f"k={args.k}, Mindestabstand {args.mindestabstand_tage} Tage")
    print(f"{'=' * 62}")
    print(f"  Analogie   Brier {statistics.fmean(b_ana):.4f}")
    print(f"  Basisrate  Brier {statistics.fmean(b_bas):.4f}")
    print(f"  n={len(b_ana)}  (ohne genug Nachbarn: {ohne})")

    # Cluster-Bootstrap ueber Symbole - dieselbe Methodik wie im kleinen Lauf,
    # nur mit einer Stichprobe, die das Ergebnis auch tragen kann.
    syms = list(je_symbol)
    r2 = random.Random(args.seed)
    diffs = []
    for _ in range(3000):
        g = [x for s in r2.choices(syms, k=len(syms)) for x in je_symbol[s]]
        if g:
            diffs.append(statistics.fmean(g))
    diffs.sort()
    u, o = diffs[int(0.025 * len(diffs))], diffs[int(0.975 * len(diffs))]
    pkt = statistics.fmean([a - b for a, b in zip(b_ana, b_bas)])
    print(f"\n  Analogie minus Basisrate: {pkt:+.4f}")
    print(f"  95 % Cluster-Bootstrap ueber {len(syms)} Symbole: [{u:+.4f} .. {o:+.4f}]")
    # Die Differenz ist Analogie MINUS Basisrate, also ist NEGATIV gut. Drei
    # Faelle, nicht zwei - der erste Anlauf pruefte nur `o < 0` und haette ein
    # gesichert SCHLECHTERES Ergebnis als "kein Befund" ausgegeben.
    if o < 0:
        urteil = "JA, die Analogie traegt - gesichert besser als die Basisrate"
    elif u > 0:
        urteil = ("NEIN. Die Analogie ist gesichert SCHLECHTER als die "
                  "Basisrate - der ganze Bereich liegt ueber null")
    else:
        urteil = "KEIN gesicherter Befund - die Null liegt im Bereich"
    print(f"\n  -> {urteil}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
