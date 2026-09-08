# -*- coding: utf-8 -*-
"""N-63 — SCHALTER oder REGLER? Die Form der 200-Schnitt-Achse (07.09.2026)

## Der Befund, der beide Themen zusammenlegt

`schnitt` und das Akkumulationsmass sind **dieselbe Groesse**, in zwei
Formen und mit zwei Erfolgsmassen gemessen:

    schnitt      c[i] / mean(c[i-200:i]) - 1        REGLER    bewegung_r
                 (messe_kandidaten_als_regel.baue, N-59)      +0,1707 R

    UNTER_SMA    kurs < sma200                      SCHALTER  Verbilligung
                 (messe_akkumulation.anteil_der_regel)        +0,0292 Rang

⚠️ **Sie standen nie nebeneinander.** Der 28.08.-Befund zum
Akkumulationsmass kam nie ins Register; `schnitt` wurde am 31.08. auf
kontaminierter Basis verworfen (2.153). Dass es eine Groesse ist, fiel
erst am 07.09. auf.

## Die Frage, die vor jeder Registrierung steht

> **In welcher FORM traegt die Achse?** Als Schalter (unter/ueber) oder
> als Regler (wie weit darunter)?

Stehende Vorgabe: *"Die FORM der Groesse vor der Messung klaeren."* Und
ein Vorbefund sagt etwas dazu -
`project_schwelle_ist_ein_schalter_kein_regler`: an anderer Stelle war die
Schalterform die tragende. **Ob das hier auch gilt, ist offen.**

## ⚠️ Beide Formen auf DEMSELBEN Massstab

Damit der Vergleich zaehlt, laufen beide durch `pruefe_auswahl`:

    Menge        20 % (selektiert) - `frageart='beitrag'`, F-212
    Zielgroesse  bewegung_r, Horizont 20 wie in N-59
    Kontrolle    `zufall` - darf in keiner Form tragen

Der Schalter entsteht aus DERSELBEN Kandidatenwelt wie der Regler; nur die
Kennzahl wird auf 0/1 gesetzt. So kann kein Unterschied aus der Datenlage
stammen.

⚠️ **Gleichstand geht dabei NICHT verloren:** ein Schalter erzeugt an
jedem Tag zwei Gruppen statt einer Rangfolge. Wieviele Werte je Tag
ueberhaupt unterschieden werden, wird MITGEZAEHLT - sonst sieht Untermacht
wie ein Nullbefund aus.

    python n63_form_der_achse.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                          # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm_auswahl import pruefe_auswahl                  # noqa: E402

HORIZONT, MENGE = 20, "20%"


def als_schalter(je_tag: dict) -> dict:
    """Dieselbe Welt, Kennzahl auf 0/1 - unter dem Schnitt ist 1.

    ⚠️ VORZEICHEN. `schnitt` ist negativ, wenn der Kurs UNTER dem
    200-Schnitt liegt. `UNTER_SMA` soll dort feuern, also ist die
    Schalterkennzahl `1 wenn kennzahl < 0`. Waere es umgekehrt, maesse
    diese Datei das Gegenteil dessen, was sie behauptet.
    """
    aus = {}
    for t, zeilen in je_tag.items():
        aus[t] = [{**z, "kennzahl": 1.0 if z["kennzahl"] < 0.0 else 0.0}
                  for z in zeilen]
    return aus


def main() -> int:
    t0 = time.time()
    print("=" * 96)
    print("N-63 — SCHALTER oder REGLER? Die 200-Schnitt-Achse, ein Massstab")
    print("=" * 96)
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    print("  %d Krypto-Reihen · Menge %s · H%d" % (len(reihen), MENGE,
                                                   HORIZONT))

    regler = K.baue(reihen, "schnitt", horizont=HORIZONT)
    schalter = als_schalter(regler)
    zufall = K.baue(reihen, "zufall", horizont=HORIZONT)

    # ---- 1  UNTERSCHEIDET DER SCHALTER UEBERHAUPT? ---------------------
    print()
    print("  1  TRENNT DER SCHALTER? — vor der Deutung")
    je = [sum(1 for z in v if z["kennzahl"] < 0.0) for v in regler.values()]
    ges = [len(v) for v in regler.values()]
    eindeutig = sum(1 for a, b in zip(je, ges) if a == 0 or a == b)
    print("     %d Tage · im Mittel %.1f von %.1f Werten unter dem Schnitt"
          % (len(je), float(np.mean(je)), float(np.mean(ges))))
    print("     %d Tage (%.1f %%) haben ALLE Werte auf derselben Seite"
          % (eindeutig, 100.0 * eindeutig / max(1, len(je))))
    print("     %s"
          % ("⚠️ An diesen Tagen trennt der Schalter NICHTS - er kann dort "
             "keine Auswahl treffen." if eindeutig else
             "✔ Der Schalter trennt an jedem Tag."))

    # ---- 2  DIE MESSUNG ------------------------------------------------
    print()
    print("  2  BEIDE FORMEN, DERSELBE MASSSTAB")
    print("     %-22s %10s %24s  %s"
          % ("Form", "Wirkung", "Band", "Urteil"))
    erg = {}
    for lab, welt in (("REGLER (stetig)", regler),
                      ("SCHALTER (0/1)", schalter),
                      ("zufall (Kontrolle)", zufall)):
        rng = np.random.default_rng(20260907)
        try:
            b = pruefe_auswahl("schnitt" if welt is not zufall else "zufall",
                               welt, mom, lage=lage, menge=MENGE, rng=rng,
                               horizont=HORIZONT,
                               hypothese="Form der 200-Schnitt-Achse",
                               verwendung="Beitrag")
        except Exception as exc:                             # noqa: BLE001
            print("     %-22s -> %s" % (lab, exc))
            continue
        erg[lab] = b
        print("     %-22s %+9.4f R [%+.4f .. %+.4f]  %s"
              % (lab, b.wirkung, b.unten, b.oben, b.urteil[:44]), flush=True)

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 96)
    print("WAS DAS HEISST")
    print("=" * 96)
    z = erg.get("zufall (Kontrolle)")
    if z is not None and z.traegt:
        print("  ⚠️⚠️ `zufall` TRAEGT - der Aufbau ist kaputt.")
        return 1
    print("  ✔ `zufall` traegt nicht.")
    r, sc = erg.get("REGLER (stetig)"), erg.get("SCHALTER (0/1)")
    if r is None or sc is None:
        print("  ⚠️ Eine Form fehlt - kein Vergleich.")
        return 1
    print("  REGLER   %+.4f R [%+.4f .. %+.4f]  %s"
          % (r.wirkung, r.unten, r.oben, "traegt" if r.traegt else "nicht"))
    print("  SCHALTER %+.4f R [%+.4f .. %+.4f]  %s"
          % (sc.wirkung, sc.unten, sc.oben, "traegt" if sc.traegt else "nicht"))
    print()
    # ⚠️ UEBERLAPPEN DIE BAENDER? Zwei Punktschaetzer zu vergleichen waere
    # genau der Fehler, den die Messnorm verhindern soll.
    ueberlappt = not (r.unten > sc.oben or sc.unten > r.oben)
    if ueberlappt:
        print("  ⚠️ DIE BAENDER UEBERLAPPEN. Die Formen sind NICHT")
        print("     unterscheidbar - wer hier die groessere Zahl waehlt,")
        print("     waehlt Rauschen. Dann entscheidet die EINFACHERE Form,")
        print("     und das ist der Schalter (eine Grenze statt einer")
        print("     Kennlinie ueber neun Baender).")
    else:
        besser = "REGLER" if r.wirkung > sc.wirkung else "SCHALTER"
        print("  ✔✔ DIE FORMEN SIND UNTERSCHEIDBAR - %s traegt mehr."
              % besser)
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
