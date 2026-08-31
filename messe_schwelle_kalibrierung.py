# -*- coding: utf-8 -*-
"""Welche Potentialschwelle ist die richtige? (30.08.2026, U-1 Kalibrierung)

## Die Frage

Nutzervorgabe: *„JA - Schwelle muss ueber 0,000 liegen, wie hoch ist noch zu
messen."* Und: *„ich wuerde gerne erst detailliert simulieren und nicht
entscheiden - was ist die optimale Schwelle aktuell zur Kalibrierung."*

## Was hier simuliert wird

Fuer jeden Anker wird das Potential aus den REGISTRIERTEN Beitraegen
gerechnet - so, wie `wahrscheinlichkeit.rechne()` es tun wird:

    Potential = quote * CRV - (1 - quote)
    quote     = 1/(1+CRV) + Summe der Beitragspunkte / 100

Beitraege in dieser Simulation (die gemessenen, mit Wirksamkeitszahlen):

    Funding-Fuenftel   +0,81 / +0,85 / +0,25 / -0,52 / -1,39 Punkte
    Turnover-Fuenftel  dieselbe Form, aus der eigenen Messung

⚠️ VORFILTER H FEHLT hier. Er braucht die Marken-Rechnung, die auf diesen
Ankern nicht vorliegt. Die Simulation unterschaetzt das Potential also -
und die gefundene Schwelle ist damit eher zu niedrig als zu hoch. Das ist
die vorsichtige Richtung.

## Was eine Schwelle leisten muss - drei Groessen gegeneinander

    DURCHLASS   wieviele Signale bleiben uebrig
    ERTRAG      wie gut sind die Verbliebenen (Median in R)
    GEWINN      Ertrag mit Schwelle minus Ertrag ohne

⚠️ Die optimale Schwelle ist NICHT die mit dem hoechsten Ertrag - das waere
die schaerfste, und sie liesse fast nichts durch. Gesucht ist der Punkt, an
dem der Gewinn je verworfenem Signal am groessten ist: **wo kostet das
Verwerfen am wenigsten und bringt am meisten**.
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B
import messe_funding_niveau as F
import messe_kandidaten_als_regel as K
from agent import wahrscheinlichkeit as W

HORIZONT = 20
CRV = 2.0

# ⚠️ DIE STUFEN WERDEN GELESEN, NICHT KOPIERT (2e, 30.08.2026).
#
# Hier standen bis heute zwei Zahlenreihen von Hand - und die fuer Turnover
# war eine KOPIE der Funding-Reihe, mit dem Kommentar "dieselbe Form aus der
# eigenen Messung". Sie war es nicht: gemessen sind
# (+3,15 / +0,83 / +0,22 / -1,79 / -2,40), also eine mehr als doppelt so
# grosse Spanne. Eine Schwelle, die auf falschen Stufen kalibriert wird,
# ist falsch kalibriert - und der Fehler faellt nirgends auf, weil beide
# Seiten fuer sich plausibel aussehen.
#
# Seit 2e sind beide in `wahrscheinlichkeit.BEITRAEGE` registriert. Von dort
# werden sie gelesen. Wer die Beitraege aendert, aendert damit automatisch
# die Kalibrierung - und muss sie neu rechnen (R-R9).
def _stufen(merkmal):
    for b in W.BEITRAEGE:
        if b.merkmal == merkmal and b.stufen:
            return tuple(b.stufen)
    raise SystemExit("Beitrag %r ist nicht registriert - 2e unvollstaendig?"
                     % merkmal)


FUNDING_STUFEN = _stufen("funding_fuenftel")
TURNOVER_STUFEN = _stufen("turnover_fuenftel")
H_PUNKTE = next((b.punkte for b in W.BEITRAEGE
                 if b.merkmal == "h" and b.zustand == "traegt"), 0.0)
# H trifft auf rund 2,1 % der Anker zu (`messe_h_produktionsgeometrie.py`,
# 620.679 Anker, Produktions-Geometrie). Die Simulation kennt die Marken
# nicht; H wird deshalb mit dieser Haeufigkeit zufaellig aufgeschlagen.
H_HAEUFIGKEIT = 0.021
SCHWELLEN = (0.000, 0.001, 0.005, 0.010, 0.020, 0.030, 0.050, 0.080, 0.120)


def basisrate(crv=CRV):
    return 1.0 / (1.0 + crv)


def potential(punkte, crv=CRV):
    q = basisrate(crv) + punkte / 100.0
    return q * crv - (1.0 - q)


def fuenftel(werte):
    r = np.argsort(np.argsort(np.asarray(werte, float))) / max(len(werte) - 1, 1)
    return np.minimum((r * 5).astype(int), 4)


def baue():
    """Je Kalendertag: Potential und Ergebnis je Symbol."""
    reihen = B.lade()
    funding = F.lade_funding()
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    tu = K.baue(reihen, "turnover", menge)          # Turnover-Anker
    je_tag = {}
    for tag, zeilen in tu.items():
        eintraege = []
        for x in zeilen:
            f = funding.get(x["sym"].upper(), {}).get(tag)
            eintraege.append({"sym": x["sym"], "turnover": x["kennzahl"],
                              "funding": f, "in_r": x["in_r"]})
        if len(eintraege) >= 12:
            je_tag[tag] = eintraege
    return je_tag


def bewerte(je_tag, mit_h=True, saat=20260830):
    """Je Anker das Potential aus den registrierten Beitraegen.

    ⚠️ H WIRD MITGERECHNET (2e, 30.08.2026). Die fruehere Fassung liess ihn
    weg und vermerkte, die Schwelle falle dadurch "eher zu niedrig aus, also
    in die vorsichtige Richtung". Das war vor 2e richtig und ist es jetzt
    nicht mehr: H ist mit +4,50 Punkten der mit Abstand groesste Einzelwert.
    Wer ihn weglaesst, kalibriert gegen eine Verteilung, die es nicht gibt -
    und zwar in die UNvorsichtige Richtung, weil die Schwelle dann alles
    durchlaesst, was H trifft.
    """
    rng = np.random.default_rng(saat)
    for zeilen in je_tag.values():
        t5 = fuenftel([x["turnover"] for x in zeilen])
        mit_f = [x for x in zeilen if x["funding"] is not None]
        f5 = fuenftel([x["funding"] for x in mit_f]) if len(mit_f) >= 5 else None
        lage = {id(x): i for i, x in enumerate(mit_f)}
        for x, tstufe in zip(zeilen, t5):
            punkte = TURNOVER_STUFEN[tstufe]
            if f5 is not None and id(x) in lage:
                punkte += FUNDING_STUFEN[f5[lage[id(x)]]]
            x["h"] = bool(mit_h and rng.random() < H_HAEUFIGKEIT)
            if x["h"]:
                punkte += H_PUNKTE
            x["punkte"] = punkte
            x["potential"] = potential(punkte)
    return je_tag


def main():
    je_tag = bewerte(baue())
    alle = [x for z in je_tag.values() for x in z]
    n = len(alle)
    print("=" * 88)
    print("KALIBRIERUNG DER POTENTIALSCHWELLE")
    print("=" * 88)
    print("%d Anker, %d Kalendertage, Horizont %d, CRV %.1f"
          % (n, len(je_tag), HORIZONT, CRV))
    p = [x["potential"] for x in alle]
    print("Potential: Median %+.4f R   Spanne %+.4f .. %+.4f"
          % (st.median(p), min(p), max(p)))
    print("Beitragslage: Funding %s | Turnover %s | H %+.2f bei %.1f %% der Anker"
          % ("/".join("%+.2f" % x for x in FUNDING_STUFEN),
             "/".join("%+.2f" % x for x in TURNOVER_STUFEN),
             H_PUNKTE, 100 * H_HAEUFIGKEIT))
    print()
    basis = st.median([x["in_r"] for x in alle])
    print("  %-9s %10s %12s %12s %14s" % ("Schwelle", "Durchlass",
                                          "Ertrag", "gegen ohne", "je verworfenem"))
    for s in SCHWELLEN:
        bleibt = [x for x in alle if x["potential"] > s]
        if len(bleibt) < 100:
            print("  %-9.3f %9d   zu wenige" % (s, len(bleibt)))
            continue
        ertrag = st.median([x["in_r"] for x in bleibt])
        verworfen = n - len(bleibt)
        gewinn = ertrag - basis
        je = (gewinn / (verworfen / n)) if verworfen else float("nan")
        print("  %-9.3f %8.1f %% %+11.4f %+12.4f %+14.4f"
              % (s, 100 * len(bleibt) / n, ertrag, gewinn, je))
    print()
    print("  Lesehilfe: 'je verworfenem' = Gewinn geteilt durch den Anteil der")
    print("  gesperrten Signale. Hoch heisst: viel Wirkung fuer wenig Verzicht.")


if __name__ == "__main__":
    main()
