# -*- coding: utf-8 -*-
"""N5 VORABTEST auf KUNSTDATEN - tun die Modi, was sie sollen? (06.09.2026)

Nutzervorgabe: *"wir werden nicht wieder alles an einer einzigen Messung
aufhaengen ... wenn etwas nicht traegt, ist zu pruefen, ob ein Fehler
vorliegt oder der Nutzen falsch angenommen wurde."*

  K1  DIE F-206-FALLE: sperrt `und` wirklich nur rund 4 % (0,2 x 0,2)?
      Waeren es 20 %, waere es gar kein UND, sondern eine lockerere
      Einzelschwelle - genau der Fehler vom 04.09.
  K2  ORDNUNG: und < einzeln < oder, im gesperrten Anteil
  K3  NUR EINE GROESSE TRAEGT -> die Kombination darf NICHT besser sein
  K4  BEIDE TRAGEN UNABHAENGIG -> die Kombination MUSS besser sein
"""
from __future__ import annotations
import sys
import numpy as np
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import messnorm_rand as R                                    # noqa: E402

MARKE = 2.0


def welt(rng, tage=1200, syms=80, eff1=0.0, eff2=0.0):
    """Zwei UNABHAENGIGE Kennzahlen; jede senkt das oberste Fuenftel."""
    je_tag, zweit = {}, {}
    g = int(round(syms * 0.80))
    for t in range(tage):
        k1 = [float(rng.random()) for _ in range(syms)]
        k2 = [float(rng.random()) for _ in range(syms)]
        o1 = sorted(range(syms), key=lambda i: k1[i])
        o2 = sorted(range(syms), key=lambda i: k2[i])
        rang1 = {i: p for p, i in enumerate(o1)}
        rang2 = {i: p for p, i in enumerate(o2)}
        tagname = "t%04d" % t
        z, d2 = [], {}
        for i in range(syms):
            y = float(rng.normal(0, 1.0))
            if rang1[i] >= g:
                y -= eff1
            if rang2[i] >= g:
                y -= eff2
            z.append({"sym": "S%02d" % i, "kennzahl": k1[i], "in_r": y})
            d2["S%02d" % i] = k2[i]
        je_tag[tagname] = z
        zweit[tagname] = d2
    return je_tag, zweit


def anteil_gesperrt(je_tag, zweit, modus):
    _d, anteil, _g, _u = R.wirkung_rand(je_tag, True, marke=MARKE,
                                        zweit=zweit, modus=modus)
    return float(np.mean(anteil)) if anteil else float("nan")


def wirkung(je_tag, zweit, modus):
    d, _a, _g, _u = R.wirkung_rand(je_tag, True, marke=MARKE,
                                   zweit=zweit, modus=modus)
    return float(np.mean(list(d.values()))) if d else float("nan")


def main() -> int:
    ok = True
    je, zw = welt(np.random.default_rng(1), eff1=0.0, eff2=0.0)

    print("=" * 84)
    print("K1/K2  DER GESPERRTE ANTEIL — sperrt `und` wirklich wie ein UND?")
    print("=" * 84)
    a = {m: anteil_gesperrt(je, zw, m)
         for m in ("einzeln", "und", "oder", "summe")}
    for m in ("einzeln", "und", "oder", "summe"):
        print("  %-9s %6.2f %%" % (m, 100 * a[m]))
    k1 = 0.02 <= a["und"] <= 0.07
    k2 = a["und"] < a["einzeln"] < a["oder"]
    ok &= k1 and k2
    print()
    print("  K1 `und` liegt bei rund 4 %% (0,2 x 0,2):  %s"
          % ("OK" if k1 else "⚠️ FEHLER - das ist kein UND (F-206-Falle)"))
    print("  K2 Ordnung und < einzeln < oder:          %s"
          % ("OK" if k2 else "⚠️ FEHLER"))

    print()
    print("=" * 84)
    print("K3  NUR DIE ERSTE GROESSE TRAEGT (0,20 R) — Kombination darf")
    print("    NICHT besser sein als `einzeln`")
    print("=" * 84)
    je3, zw3 = welt(np.random.default_rng(2), eff1=0.20, eff2=0.0)
    w3 = {m: wirkung(je3, zw3, m) for m in ("einzeln", "und", "oder", "summe")}
    for m, v in w3.items():
        print("  %-9s %+8.5f" % (m, v))
    k3 = w3["einzeln"] >= w3["und"] - 1e-9 and w3["einzeln"] >= w3["summe"] - 1e-9
    ok &= k3
    print("  K3: %s" % ("OK - die Kombination verwaessert, wie sie soll"
                        if k3 else "⚠️ FEHLER - Kombination schlaegt die "
                                   "einzige tragende Groesse"))

    print()
    print("=" * 84)
    print("K4  BEIDE TRAGEN UNABHAENGIG (je 0,15 R) — `oder` MUSS besser")
    print("    sein als `einzeln`")
    print("=" * 84)
    je4, zw4 = welt(np.random.default_rng(3), eff1=0.15, eff2=0.15)
    w4 = {m: wirkung(je4, zw4, m) for m in ("einzeln", "und", "oder", "summe")}
    for m, v in w4.items():
        print("  %-9s %+8.5f" % (m, v))
    k4 = w4["oder"] > w4["einzeln"]
    ok &= k4
    print("  K4: %s" % ("OK - beide Groessen werden genutzt" if k4
                        else "⚠️ FEHLER - die zweite Groesse wirkt nicht"))

    print()
    print("=" * 84)
    print("K5  SYMMETRIE — dieselbe UND/ODER-Auswahl von der anderen Seite")
    print("=" * 84)
    print("  ⚠️ Am 06.09. im ECHTLAUF aufgefallen, nicht hier: die erste")
    print("     Fassung rangte die Basisgroesse ueber alle Werte des Tages")
    print("     und die Zweitgroesse nur ueber die gemeinsamen. `UND` gab")
    print("     dann von der einen Seite +0,00117 und von der anderen")
    print("     +0,00086. Eine symmetrische Bedingung muss symmetrische")
    print("     Zahlen geben.")
    je5, zw5 = welt(np.random.default_rng(5), eff1=0.15, eff2=0.15)
    # dieselbe Welt, Rollen getauscht
    getauscht = {}
    for t, z in je5.items():
        getauscht[t] = [{"sym": x["sym"], "kennzahl": zw5[t][x["sym"]],
                         "in_r": x["in_r"]} for x in z]
    zw_getauscht = {t: {x["sym"]: x["kennzahl"] for x in z}
                    for t, z in je5.items()}
    k5 = True
    for m in ("und", "oder"):
        a1 = wirkung(je5, zw5, m)
        a2 = wirkung(getauscht, zw_getauscht, m)
        gl = abs(a1 - a2) < 1e-12
        k5 &= gl
        print("  %-5s  von A aus %+.6f · von B aus %+.6f   %s"
              % (m, a1, a2, "OK" if gl else "⚠️ ASYMMETRISCH"))
    ok &= k5

    print()
    print("=" * 84)
    print("VORABTEST %s" % ("BESTANDEN" if ok else "FEHLGESCHLAGEN"))
    print("=" * 84)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
