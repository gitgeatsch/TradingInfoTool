# -*- coding: utf-8 -*-
"""N-17a: die Schwelle GEMEINSAM mit den H2-Beitraegen neu kalibrieren
(04.09.2026).

## Warum diese Datei nicht `messe_schwelle_kalibrierung.py` erweitert

Jenes Werkzeug liest die Stufen bewusst aus der LIVEN `wahrscheinlichkeit.
BEITRAEGE` ("die Stufen werden gelesen, nicht kopiert") - richtig fuer
eine Kalibrierung GEGEN den aktuellen Registrierungsstand. Die H2-Stufen
sind zum Zeitpunkt dieser Messung noch NICHT registriert (das waere die
Reihenfolge verkehrt: erst pruefen, ob eine Schwelle ueberhaupt eine
sinnvolle Selektivitaet ergibt, DANN registrieren - nicht umgekehrt).
Diese Datei nimmt die H2-Stufen deshalb als explizite Konstanten, mit
Quellenangabe, und bleibt bestehen, falls spaeter ein drittes Mal
kalibriert werden muss.

## Vorabfestlegung

    Frage      Welche Schwelle gehoert zu den H2-Beitraegen, damit die
               Kette nicht - wie F-189 fuer eine naive H2-Umskalierung
               zeigte - alles sperrt, aber weiterhin eine echte
               Selektivitaet hat (nicht 0 %, nicht 100 % Durchlass)?
    Massstab   Dieselbe Groesse wie bei der urspruenglichen H20-
               Kalibrierung (`messe_schwelle_kalibrierung.py`, 30./
               31.08.2026): Gewinn je verworfenem Signal - nicht der
               hoechste Ertrag (das waere die schaerfste Schwelle, sie
               liesse fast nichts durch).
    Datenlage  Dieselbe Ankerbasis wie immer (`messe_eigenschaft_beitrag.
               lade()`, Turnover/Funding-Kreuzung), aber mit Horizont 2
               statt 20 gebaut - `in_r` misst also den Ertrag ueber 2
               Handelstage, nicht 20.

## Die H2-Stufen - gemessen, nicht angenommen

    python rechne_funding_beitrag.py --horizont 2
    python rechne_turnover_beitrag.py --horizont 2

Ergebnis (04.09.2026, an den lokalen Historiendatenbanken gemessen):

    Funding H2   +0.01 / +0.18 / +0.01 / -0.08 / -0.12   Spanne 0.13
    Turnover H2  +0.34 / +0.08 / +0.15 / -0.25 / -0.32    Spanne 0.66

⚠️⚠️ WEDER STUFENREIHE IST STRENG MONOTON. Funding hat einen Ausschlag bei
Fuenftel 1 (+0.18, hoeher als Fuenftel 0) - dieselbe Form wie die LIVE
registrierte H20-Fassung (+0.82/+1.30/...), dort ebenfalls am selben Platz
akzeptiert. Turnover hat den Ausschlag an ANDERER Stelle (Fuenftel 2,
+0.15 gegen +0.08 bei Fuenftel 1) als seine eigene, sauber monotone
H20-Fassung - das ist neu und nicht durch Praezedenz gedeckt. **Diese
Datei bewertet das nicht selbst als bestanden/durchgefallen - sie legt
die Zahlen und die Schwellen-Rechnung vor, die Einordnung ("nutzbar?")
gehoert vor die Registrierung, nicht in dieses Skript.**

## Was diese Messung NICHT ersetzt

Die Spannen sind winzig gegen H20 (0.13/0.66 gegen 2.28/5.92 Punkte) -
konsistent mit dem seit dem 31.08. bekannten Faktor 6-10. Eine Schwelle,
die auf dieser Spanne kalibriert wird, wird deshalb selbst SEHR fein sein
- und ebenso empfindlich gegen genau die Unsicherheiten, die F-171 fuer
den Turnover-Beitrag schon benannt hat (ein um 0,9 % verschobenes
Sample bewegt die H20-Wirkung um 22 %; bei einer zehnmal kleineren
Spanne ist nichts, was das besser macht).
"""
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB
import messe_eigenschaft_beitrag as B
import messe_funding_niveau as F
import messe_kandidaten_als_regel as K

HORIZONT = 2
CRV = 2.0

# ⚠️ QUELLE: rechne_funding_beitrag.py / rechne_turnover_beitrag.py
# --horizont 2, gemessen 04.09.2026 - siehe Modulkopf.
FUNDING_STUFEN = (0.01, 0.18, 0.01, -0.08, -0.12)
TURNOVER_STUFEN = (0.34, 0.08, 0.15, -0.25, -0.32)

# Feiner und tiefer als bei H20 (0,000 .. 0,120) - die Spanne der
# H2-Beitraege ist selbst rund zehnmal kleiner.
SCHWELLEN = (0.000, 0.0005, 0.001, 0.002, 0.003, 0.005, 0.008, 0.010,
             0.015, 0.020)


def basisrate(crv=CRV):
    return 1.0 / (1.0 + crv)


def potential(punkte, crv=CRV):
    q = basisrate(crv) + punkte / 100.0
    return q * crv - (1.0 - q)


def fuenftel(werte):
    r = np.argsort(np.argsort(np.asarray(werte, float))) / max(len(werte) - 1, 1)
    return np.minimum((r * 5).astype(int), 4)


def baue():
    """Je Kalendertag: Potential und Ergebnis je Symbol - auf HORIZONT 2,
    nicht 20. Dieselbe Ankerkreuzung (Turnover x Funding) wie die
    H20-Kalibrierung, nur mit dem Horizont-Parameter durchgereicht."""
    reihen = B.lade()
    funding = F.lade_funding()
    menge = MB.reihe("data/onchain_historie.db", "splycur")
    tu = K.baue(reihen, "turnover", menge, horizont=HORIZONT)
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


def bewerte(je_tag):
    """Je Anker das Potential aus den H2-Stufen - OHNE H (H ist auch in
    der live registrierten Beitragslage `zustand='null'`, traegt also
    unabhaengig vom Horizont nichts bei - dieselbe Lage wie bei H20)."""
    for zeilen in je_tag.values():
        t5 = fuenftel([x["turnover"] for x in zeilen])
        mit_f = [x for x in zeilen if x["funding"] is not None]
        f5 = fuenftel([x["funding"] for x in mit_f]) if len(mit_f) >= 5 else None
        lage = {id(x): i for i, x in enumerate(mit_f)}
        for x, tstufe in zip(zeilen, t5):
            punkte = TURNOVER_STUFEN[tstufe]
            if f5 is not None and id(x) in lage:
                punkte += FUNDING_STUFEN[f5[lage[id(x)]]]
            x["punkte"] = punkte
            x["potential"] = potential(punkte)
    return je_tag


def main():
    je_tag = bewerte(baue())
    alle = [x for z in je_tag.values() for x in z]
    n = len(alle)
    print("=" * 88)
    print("N-17a: SCHWELLE GEMEINSAM MIT DEN H2-BEITRAEGEN KALIBRIERT")
    print("=" * 88)
    print("%d Anker, %d Kalendertage, Horizont %d, CRV %.1f"
          % (n, len(je_tag), HORIZONT, CRV))
    p = [x["potential"] for x in alle]
    print("Potential: Median %+.5f R   Spanne %+.5f .. %+.5f"
          % (st.median(p), min(p), max(p)))
    print("Beitragslage: Funding %s | Turnover %s"
          % ("/".join("%+.2f" % x for x in FUNDING_STUFEN),
             "/".join("%+.2f" % x for x in TURNOVER_STUFEN)))
    print()
    basis = st.median([x["in_r"] for x in alle])
    print("Referenz (Ertrag ohne jede Schwelle, Horizont 2): %+.4f R"
          % basis)
    print()
    print("  %-9s %10s %12s %12s %14s" % ("Schwelle", "Durchlass",
                                          "Ertrag", "gegen ohne", "je verworfenem"))
    bestes = None
    for s in SCHWELLEN:
        bleibt = [x for x in alle if x["potential"] > s]
        if len(bleibt) < 100:
            print("  %-9.4f %9d   zu wenige" % (s, len(bleibt)))
            continue
        ertrag = st.median([x["in_r"] for x in bleibt])
        verworfen = n - len(bleibt)
        gewinn = ertrag - basis
        je = (gewinn / (verworfen / n)) if verworfen else float("nan")
        print("  %-9.4f %8.1f %% %+11.4f %+12.4f %+14.4f"
              % (s, 100 * len(bleibt) / n, ertrag, gewinn, je))
        if verworfen and (bestes is None or je > bestes[1]):
            bestes = (s, je, 100 * len(bleibt) / n)
    print()
    if bestes:
        print("  Groesstes 'je verworfenem': Schwelle %.4f (Durchlass %.1f %%)"
              % (bestes[0], bestes[2]))
    print("  Lesehilfe: 'je verworfenem' = Gewinn geteilt durch den Anteil der")
    print("  gesperrten Signale. Hoch heisst: viel Wirkung fuer wenig Verzicht.")


if __name__ == "__main__":
    main()
