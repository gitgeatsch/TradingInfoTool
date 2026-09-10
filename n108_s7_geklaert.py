# -*- coding: utf-8 -*-
"""S-7 GEKLAERT — traegt `schnitt` in den Fenstern ab 2022? (10.09.2026)

## Der Befund, der `schnitt` widerspricht

Am 07.09. fiel `schnitt` mit dieser Tafel:

    |                    | ganz    | ab 2022 | ab 2023 | ab 2024 |
    | funding (Kontrolle)| +0,0446 ✔ | +0,0157 ✔ | +0,0170 ✔ | +0,0182 ✔ |
    | schnitt allein     | +0,1623 ✔ | +0,0414 ✖ | +0,0478 ✖ | +0,0855 ✖ |
    | schnitt in der Kette| +0,0397 ✔ | +0,0165 ✖ | +0,0216 ✖ | +0,0264 ✖ |

## ⚠️⚠️ Und S-7 sagt SELBST, dass es unentschieden ist

> *„,heute nicht nachweisbar' ist nicht ,traegt nicht'. Die
> Trennschaerfe liegt allein bei 0,10 R, in der Kette bei 0,05 R; die
> Werte liegen darunter. Es ist **unentschieden** - aber eine
> Bauentscheidung braucht einen Nachweis, keine offene Frage."*

**Das war am 07.09. richtig entschieden.** Inzwischen ist die Lage eine
andere: `schnitt` erfuellt alle vier Kriterien (2.319) und besteht N-73
besser als `funding`. Wer jetzt registriert, muss S-7 zuerst klaeren -
sonst ist es genau das Hin und Her, das abgestellt werden sollte.

## ⚠️⚠️⚠️ DIE ERSTE ANTWORT STEHT VOR JEDER MESSUNG

Die Blockregel verlangt 20 Bloecke; bei H20 ist ein Block 60 Tage, also
1.200 Tage:

    ab 2019   ~2.809 Tage   46,8 Bloecke   ✔
    ab 2022   ~1.713 Tage   28,6 Bloecke   ✔
    ab 2023   ~1.348 Tage   22,5 Bloecke   ✔
    ab 2024   ~  983 Tage   16,4 Bloecke   ⚠️ UNTER der Regel

> **S-7s Spalte ,ab 2024' ist unter dem heutigen Standard KEIN BEFUND,
> nicht ,traegt nicht'.** Sie war nie ein gueltiges Urteil.

## Was hier gemessen wird

    Fenster      ganz · ab 2022 · ab 2023 · ab 2024
    Kandidaten   `schnitt` (der Gegenstand) · `funding` (S-7s eigene
                 Kontrolle) · `zufall`
    Mengen       ALLE zulaessigen je Fenster (N-73) - nicht eine
    Norm         Band, Nullpunkt, Trennschaerfeleiter, Blockpruefung

⚠️ **R-R11:** S-7 stammt vom 07.09. - VOR dem Messstandard (08./09.09.)
und vor der Nullbezugsentscheidung. Reproduziert wird zuerst die
Groessenordnung seiner Zahlen; erst dann wird gedeutet.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    ganz         `schnitt` traegt - das war schon in S-7 so
    ab 2022      ⚠️ die eigentliche Frage. S-7 sagte +0,0414 bei einer
                 Trennschaerfe von 0,10 R - also UNTERMACHT, kein
                 Nullbefund. Unter dem Standard mit geeichtem Nullpunkt
                 koennte es entscheidbar sein
    ab 2023      wie ab 2022, mit weniger Bloecken
    ab 2024      ⚠️ KEIN BEFUND erwartet - die Blockregel greift

⚠️⚠️ **Faellt `schnitt` ab 2022 mit BEZIFFERTER Trennschaerfe durch, ist
S-7 bestaetigt und die Registrierung fällt.** Bleibt es Untermacht, ist
S-7 weder bestaetigt noch widerlegt - und dann ist es eine
Nutzerentscheidung, ob ein unentschiedener Widerspruch die
Registrierung blockiert.

    python n108_s7_geklaert.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                         # noqa: E402
import messe_kandidaten_als_regel as K                        # noqa: E402
import messmenge                                              # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                 # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen     # noqa: E402
from messe_beitrag_auf_auswahl import momentum250             # noqa: E402

KANDIDATEN = ("schnitt", "funding", "zufall")
FENSTER = (("ganz", ""), ("ab 2022", "2022-01-01"),
           ("ab 2023", "2023-01-01"), ("ab 2024", "2024-01-01"))
# ⚠️ S-7s eigene Zahlen - zur Reproduktionspruefung (R-R11), NICHT als
# Sollwert. Sie stammen aus einem Werkzeug von VOR dem Messstandard.
S7 = {("schnitt", "ganz"): 0.1623, ("schnitt", "ab 2022"): 0.0414,
      ("schnitt", "ab 2023"): 0.0478, ("schnitt", "ab 2024"): 0.0855,
      ("funding", "ganz"): 0.0446, ("funding", "ab 2022"): 0.0157,
      ("funding", "ab 2023"): 0.0170, ("funding", "ab 2024"): 0.0182}
SAAT = 20260910


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    lage = N.Lage(instrument="spot", strategie="einstieg")
    block = N._block(HORIZONT)

    print("=" * 116)
    print("S-7 GEKLAERT — traegt `schnitt` in den Fenstern ab 2022?")
    print("=" * 116)
    print("  %s" % messmenge.zeile())
    print("  %s" % N.standardzeile())
    print("  Block %d Tage · 20 Bloecke gefordert = %d Tage"
          % (block, 20 * block))
    print("  ⚠️ S-7 stammt vom 07.09. - VOR dem Messstandard. Seine "
          "Zahlen stehen als")
    print("     Reproduktionspruefung daneben, NICHT als Sollwert.")
    print("  ⚠️⚠️ Gemessen wird ueber ALLE zulaessigen Mengen je Fenster "
          "(N-73), nicht auf einer.")

    erg = {}
    for kand in KANDIDATEN:
        je0 = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        print()
        print("  %s" % kand.upper())
        print("     %-9s %-6s %9s %22s %9s %6s %9s  %s"
              % ("Fenster", "Menge", "Wirkung", "Band", "Nullpkt",
                 "Bloe.", "Trennsch", "Urteil"))
        for name, ab in FENSTER:
            je = ({t: z for t, z in je0.items() if str(t) >= ab}
                  if ab else je0)
            tage = len(je)
            if tage < 4 * block:
                print("     %-9s ⚠️ nur %d Tage (%.1f Bloecke) - unter der "
                      "Blockregel, KEIN BEFUND"
                      % (name, tage, tage / block))
                continue
            try:
                zul = MA.zulaessige_mengen(je, mom, horizont=HORIZONT)
            except Exception as exc:                          # noqa: BLE001
                print("     %-9s Mengenwahl: %s" % (name, str(exc)[:50]))
                continue
            traeger, geprueft = [], []
            for m in zul:
                try:
                    b = MA.pruefe_auswahl(
                        kand, je, mom, lage=lage, menge=m,
                        rng=np.random.default_rng(SAAT), horizont=HORIZONT,
                        hypothese="S-7 geklaert",
                        verwendung=("Markt" if m == "frei" else "Beitrag"))
                except Exception as exc:                      # noqa: BLE001
                    print("     %-9s %-6s nicht messbar: %s"
                          % (name, m, str(exc)[:40]))
                    continue
                ts = ("%.2f R" % b.trennschaerfe_in_r
                      if b.trennschaerfe_in_r else "KEINE")
                kb = b.urteil.upper().startswith("KEIN BEFUND")
                print("     %-9s %-6s %+9.4f [%+.4f .. %+.4f] %+9.4f %6d "
                      "%9s  %s"
                      % (name, m, b.wirkung, b.unten, b.oben,
                         b.nullpunkt, b.n_bloecke, ts,
                         b.urteil.split(" (")[0][:30]), flush=True)
                if m == "frei":
                    continue
                geprueft.append(m)
                if b.traegt and not kb:
                    traeger.append(m)
            if geprueft:
                erg[(kand, name)] = (len(traeger), len(geprueft))
                print("     %-9s -> traegt auf %d von %d Beitragsmengen"
                      % ("", len(traeger), len(geprueft)))

    # ---- Die Abnahme -----------------------------------------------------
    print()
    print("=" * 116)
    print("DIE ABNAHME — ist S-7 bestaetigt, widerlegt oder unentschieden?")
    print("=" * 116)
    print("     %-9s %-22s %-22s %s"
          % ("Fenster", "schnitt (N-73)", "funding (N-73)", "S-7 sagte"))
    for name, _ab in FENSTER:
        sc = erg.get(("schnitt", name))
        fu = erg.get(("funding", name))
        print("     %-9s %-22s %-22s schnitt %+.4f · funding %+.4f"
              % (name,
                 "%d von %d" % sc if sc else "KEIN BEFUND",
                 "%d von %d" % fu if fu else "KEIN BEFUND",
                 S7.get(("schnitt", name), float("nan")),
                 S7.get(("funding", name), float("nan"))))
    print()
    zf = [v for (k, _n), v in erg.items() if k == "zufall" and v[0]]
    if zf:
        print("  ⚠️⚠️⚠️ `zufall` traegt in einem Fenster - der Lauf gilt "
              "NICHT.")
    else:
        print("  ✔ `zufall` traegt in keinem Fenster auf keiner Menge.")
    print()
    print("  ⚠️ ENTSCHEIDEND ist die TRENNSCHAERFE in den Zeilen ab 2022:")
    print("     ist sie beziffert und `schnitt` traegt trotzdem nicht -> "
          "S-7 BESTAETIGT")
    print("     fehlt sie -> UNTERMACHT, S-7 weder bestaetigt noch "
          "widerlegt")
    print("     traegt er -> S-7 WIDERLEGT, aber nur mit Reproduktion "
          "(R-R11)")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
