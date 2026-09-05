# -*- coding: utf-8 -*-
"""GEGENPRUEFUNG zu F-215: sind die Beitragsstufen in der falschen Einheit?

## Der Verdacht

`rechne_*_beitrag.py` misst je Fuenftel den Median von `in_r` (Rendite in R
nach 20 Tagen) und rechnet ihn ueber `d(quote) = d(Potential)/(1+CRV)` in
Quote-Punkte um. Das unterstellt, die gemessene R-Differenz SEI eine
Potentialdifferenz.

Das Potential ist aber fuer ein BARRIERENSYSTEM definiert
(`quote = P(Ziel vor Stop)`). Rendite-nach-20-Tagen und Barrieren-Quote
sind verschiedene Groessen - genau der Formfehler aus Methodik 2.85.

**Wenn der Verdacht stimmt, ist der Kalibrierungsfaktor 0,168 aus F-215
teilweise ein Umrechnungsfehler und kein schwaches Signal.**

## Was hier gerechnet wird

Je Fuenftel DIREKT die realisierte Barrieren-Quote - ohne Umrechnung.
Daraus das Potential als `3q-1`. Das ist selbstkalibrierend: was
herauskommt, IST die Verschiebung.

Verglichen mit dem, was die registrierten Stufen behaupten.

⚠️ Barriere ueber die bestehende `messe_zielregel.ergebnisse()`, nur
ENTSCHIEDENE Anker - dieselbe Konvention wie N-37.
"""
import sys
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B
import messe_funding_niveau as F
import messe_kandidaten_als_regel as K
import messe_zielregel as ZR
from agent import wahrscheinlichkeit as W
from messe_bewertung_kalibrierung import _fuenftel_je_tag

CRV = 2.0
VARIANTE = "ZIEL 2,0"


def main():
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    print("Barrieren-Ausgaenge...", flush=True)
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker" % len(zeilen))

    quellen = {"funding": F.lade_funding(),
               "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    for art in ("funding", "turnover"):
        f5 = _fuenftel_je_tag(K.baue(reihen, art, quellen[art], horizont=20))
        je = defaultdict(lambda: [0, 0])          # fuenftel -> [treffer, n]
        for z in zeilen:
            tage = tage_je_sym.get(z["sym"])
            if not tage or z["i"] >= len(tage):
                continue
            f = (f5.get(tage[z["i"]]) or {}).get(z["sym"])
            if f is None:
                continue
            w = z.get(VARIANTE)
            if w is None:
                continue
            if abs(w - CRV) < 1e-9:
                je[f][0] += 1; je[f][1] += 1
            elif abs(w + 1.0) < 1e-9:
                je[f][1] += 1
        reg = next((b.stufen for b in W.BEITRAEGE
                    if b.merkmal == "%s_fuenftel" % art and b.stufen), None)
        print()
        print("=" * 84)
        print("%s — Barrieren-Quote je Fuenftel, DIREKT gemessen" % art.upper())
        print("=" * 84)
        print("  %-8s %9s %9s %11s %14s %12s"
              % ("Fuenftel", "entsch.", "Quote", "Potential", "Punkte direkt",
                 "registriert"))
        direkt = []
        for f in sorted(je):
            tr, n = je[f]
            if n < 200:
                continue
            q = tr / n
            pot = q * (1 + CRV) - 1
            pkt = 100 * pot / (1 + CRV)
            direkt.append(pkt)
            r = ("%+6.2f" % reg[f]) if reg and f < len(reg) else "   -"
            print("  %-8d %9d %8.1f%% %+10.3f %+13.2f %12s"
                  % (f, n, 100 * q, pot, pkt, r))
        if direkt and reg:
            sp_d = max(direkt) - min(direkt)
            sp_r = max(reg) - min(reg)
            print()
            print("  Spanne DIREKT gemessen: %+.2f Punkte" % sp_d)
            print("  Spanne REGISTRIERT:     %+.2f Punkte" % sp_r)
            print("  Verhaeltnis direkt/registriert: %.2f" % (sp_d / sp_r if sp_r else 0))
            print()
            if sp_d < sp_r * 0.5:
                print("  -> die registrierten Stufen sind ZU GROSS: der Faktor 0,168")
                print("     ist ueberwiegend ein Umrechnungsfehler, kein schwaches Signal")
            elif sp_d > sp_r * 1.5:
                print("  -> die registrierten Stufen sind ZU KLEIN - das Signal ist")
                print("     staerker als bisher angesetzt")
            else:
                print("  -> die Groessenordnung stimmt; der Faktor 0,168 kommt NICHT")
                print("     aus der Umrechnung, sondern aus schwacher Ordnung")
    return 0


if __name__ == "__main__":
    sys.exit(main())
