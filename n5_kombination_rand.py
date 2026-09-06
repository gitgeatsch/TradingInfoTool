# -*- coding: utf-8 -*-
"""N5 — TRAEGT DIE KOMBINATION `vola` UND `turnover` AM RAND? (06.09.2026)

## ⚠️ Nutzervorgabe, die den Zuschnitt bestimmt

*"wir werden nicht wieder alles an einer einzigen Messung aufhaengen, dazu
steht zu viel auf dem Spiel. Es muessen alle relevanten Aspekte bedacht
werden und ggf. Gegenmassnahmen getroffen werden - wenn etwas aus einem
bestimmten Grund nicht traegt, ist zu pruefen, ob ein Fehler vorliegt oder
der Nutzen falsch angenommen worden ist."*

Deshalb misst diese Datei **fuenf Formen mit zwei Erfolgsmassen und drei
Diagnosegroessen** - damit ein "traegt nicht" seine URSACHE mitliefert.

## Der Vorbefund (N1, 2.120)

    vola allein am Rand    +0,00327  TRAEGT
    turnover allein am Rand +0,00362  TRAEGT (H5 voll, 2.119)
    turnover erklaert 18 % von vola   (Rang 1 von 40, p = 0,025)
    -> 82 % von vola sind unabhaengig

## ⚠️ Der Nutzen ist geprueft, nicht angenommen

Vor dem Messen wurde nachgesehen, WOHIN ein Randbefund ueberhaupt gehen
koennte. Ergebnis:

    q      = basisrate + punkte / 100.0
    wert_r = q * CRV - (1 - q)

**Die Architektur rechnet in QUOTEN, nicht in R.** Die heutigen Stufen sind
R-Wirkungen, die ueber `d(quote) = d(Potential) / (1 + CRV)` mit einem
ANGENOMMENEN CRV von 2,0 umgerechnet wurden. Ein Randmass misst die
Quotenaenderung DIREKT - ohne diese Umrechnung.

⚠️ **Die verbleibende Luecke, benannt statt uebergangen:** die Quote der
Potentialformel ist eine BARRIEREN-Quote (Ziel vor Stop), unser Randmass
eine HORIZONT-Quote ohne Barriere. Verwandt, nicht identisch.

## Die fuenf Formen (vorab festgelegt, Suchpreis 2.49)

    vola      allein            Bezug
    turnover  allein            Bezug
    und       beide im obersten Fuenftel   -> sperrt rund 4 %
    oder      eine im obersten Fuenftel    -> sperrt rund 36 %
    summe     oberstes Fuenftel der Rangsumme -> sperrt 20 %

## Zwei Erfolgsmasse — sie koennen GEGENLAEUFIG zeigen (F-206)

    WIRKUNG    anteilgewichtet: wieviel hebt die Regel den Randanteil des
               Rests? Fuer eine MENGENfrage.
    REINHEIT   je gesperrtem Anker: wieviel schlechter sind die
               Gesperrten? Fuer eine WEGWAHLfrage.

⚠️ Eine enge Auswahl (`und`, 4 %) hat zwangslaeufig eine kleine WIRKUNG,
auch wenn die Gesperrten sehr schlecht sind. Wer nur die Wirkung liest,
verurteilt `und` fuer seine Enge statt fuer seine Qualitaet - der Fehler
aus F-206.

## Drei Diagnosegroessen — damit "traegt nicht" eine Ursache hat

    gesperrter Anteil   zu enge Auswahl?      -> Mengenproblem
    Trennschaerfe       zu breites Band?      -> Maechtigkeitsproblem
    Tage / Bloecke      zu wenig Daten?       -> Datenproblem

## Der Vorabtest ist durch (`pruefe_n5_modi.py`)

    K1 `und` sperrt 4,12 % - ein echtes UND, nicht die F-206-Falle
    K2 Ordnung und < einzeln < oder haelt
    K3 traegt nur EINE Groesse, verwaessert die Kombination - richtig
    K4 tragen BEIDE, nutzt `oder` beide - richtig

    python n5_kombination_rand.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                         # noqa: E402
import messnorm_rand as R                                    # noqa: E402
from messnorm import Lage                                    # noqa: E402

H, MARKE = 5, 2.0
STAERKEN = (0.02, 0.05, 0.10, 0.20, 0.40)


def main() -> int:
    t0 = time.time()
    L = Lage("spot", "einstieg")
    print("Lade Reihen ...", flush=True)
    reihen = B.lade()
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    vola = K.baue(reihen, "vola", None, horizont=H)
    turn = K.baue(reihen, "turnover", tu, horizont=H)
    z_turn = {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in turn.items()}
    z_vola = {t: {x["sym"]: x["kennzahl"] for x in z} for t, z in vola.items()}
    print("  vola %d Tage · turnover %d Tage" % (len(vola), len(turn)),
          flush=True)

    faelle = (
        ("vola allein", vola, None, "einzeln"),
        ("turnover allein", turn, None, "einzeln"),
        ("UND  (beide oben)", vola, z_turn, "und"),
        ("ODER (eine oben)", vola, z_turn, "oder"),
        ("SUMME der Raenge", vola, z_turn, "summe"),
        # Gegenprobe: dieselbe Kombination von der anderen Seite gebaut -
        # das Ergebnis MUSS gleich sein, sonst ist die Reihenfolge drin
        ("UND  (von turnover aus)", turn, z_vola, "und"),
    )

    print()
    print("=" * 118)
    print("N5 — FUENF FORMEN, ZWEI ERFOLGSMASSE, DREI DIAGNOSEGROESSEN "
          "(Rand > +%g R · H%d · volle Historie)" % (MARKE, H))
    print("=" * 118)
    print("  %-24s %9s %9s %8s %6s %5s  %s"
          % ("Form", "WIRKUNG", "Reinheit", "gesperrt", "Tage", "Blk",
             "Band · Trennschaerfe · Urteil"))

    for lab, basis, zweit, modus in faelle:
        # Diagnosegroessen aus demselben Aufruf, den die Norm benutzt
        d, anteil, gesperrt, uebrig = R.wirkung_rand(
            basis, True, marke=MARKE, zweit=zweit, modus=modus)
        if not d:
            print("  %-24s   keine verwertbaren Tage" % lab)
            continue
        ant = float(np.mean(anteil))
        # Reinheit: um wieviel schlechter sind die GESPERRTEN je Anker?
        rein = float(np.mean(uebrig)) - float(np.mean(gesperrt))
        rng = np.random.default_rng(N.SAAT)
        try:
            f = R.pruefe_rand(lab, basis, lage=L, menge="frei", rng=rng,
                              marke=MARKE, horizont=H, staerken=STAERKEN,
                              zweit=zweit, modus=modus)
        except Exception as e:                               # noqa: BLE001
            print("  %-24s   FEHLER: %s" % (lab, e))
            continue
        urteil = ("TRAEGT" if f.traegt else
                  "kein Befund" if f.trennschaerfe_in_r is None else
                  "nicht trennbar" if abs(f.wirkung) >= (f.trennschaerfe or 0)
                  else "traegt nicht")
        print("  %-24s %+9.5f %+9.5f %7.2f%% %6d %5d  [%+.5f..%+.5f] · %s · %s"
              % (lab, f.wirkung, rein, 100 * ant, f.n_tage, f.n_bloecke,
                 f.unten, f.oben,
                 ("%.2f R" % f.trennschaerfe_in_r)
                 if f.trennschaerfe_in_r else "KEINE", urteil), flush=True)
        print("        Null [%+.5f .. %+.5f] · Treffer %s · Block-AK %.4f %s"
              % (f.null_unten, f.null_oben, f.protokoll.positiv_treffer,
                 f.protokoll.block_ak,
                 "✔" if f.protokoll.block_ok else "⚠️ ZU KURZ"))

    print()
    print("=" * 118)
    print("WIE ZU LESEN — und was ein 'traegt nicht' bedeuten KANN")
    print("=" * 118)
    print("  WIRKUNG klein, REINHEIT gross    die Auswahl ist eng, aber gut")
    print("                                   -> Wegwahl, nicht Mengenregel")
    print("  WIRKUNG gross, REINHEIT klein    die Regel sperrt viel Mittelmass")
    print("  gesperrt < 5 %% und breites Band  MENGENproblem, kein Nullbefund")
    print("  Trennschaerfe fehlt              MAECHTIGKEITSproblem - die")
    print("                                   Messung haette nichts gefunden")
    print("  beide Bezugsgroessen tragen,     dann ist die FORM falsch, nicht")
    print("  keine Kombination                die Idee")
    print()
    print("  ⚠️ Die letzte Zeile ist die Gegenprobe: dieselbe UND-Auswahl")
    print("     von der anderen Seite gebaut. Weicht sie ab, steckt eine")
    print("     Reihenfolgeabhaengigkeit in der Konstruktion.")
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
