# -*- coding: utf-8 -*-
"""Was passiert im SYSTEM, wenn H sich aendert? (30.08.2026, H-1/H-2)

Nutzervorgabe: *"vor der Fertigstellung eine detaillierte Simulation"*.

## Was hier simuliert wird - und was nicht

Nicht die Frage "traegt H" (die ist gemessen), sondern: **was aendert sich
am Trichter**, wenn H auf einen anderen Wert gesetzt wird. Gerechnet mit
der PRODUKTIONSFUNKTION `potential.rechne()`, nicht mit einer Kopie.

Je Anker wird das Potential aus allen drei registrierten Beitraegen
gebildet und gegen die Schwelle gehalten - genau wie Stufe 11 es tut.

## Die Varianten

    A  H = 4,5    heute. Gemessen: der Wert stammt aus einer gepoolten
                  Messung, deren Vorsprung zu +10,18 Komposition und
                  -7,14 Leistung zerfaellt
    B  H = 0,0    H wird `zustand="null"`, die Mailzeile bleibt
    C  H = 2,25   halbiert - die vorsichtige Zwischenstufe
    D  H = -2,0   negativ angesetzt (nur zur Anschauung, NICHT empfohlen:
                  die Blockwerte schwanken zwischen -0,026 und -0,069,
                  das traegt keine Kalibrierung)

## Die Kennzahlen je Variante

    DURCHLASS   wieviele Anker kaemen durch Stufe 11
    ERTRAG      Median der Bewegung in R unter den Durchgelassenen
    GEWINN      Ertrag mit Schwelle minus Ertrag ohne jede Schwelle
    JE VERWORFEN  Gewinn geteilt durch die Sperrquote

⚠️ H IST HIER ECHT, NICHT GERATEN. Die Anker stammen aus
`anker_h_neu_2026_08_30.json`, wo `h_alt` je Anker gerechnet ist. Die
Funding- und Turnover-Raenge liegen fuer diese Anker NICHT vor (andere
Datenquelle); sie werden deshalb je Kalendertag aus einer Ersatzgroesse
gebildet, die dieselbe Randverteilung hat - siehe `_raenge_ersatz`.

    python simuliere_h_varianten.py
"""
import io
import json
import statistics as st
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from agent import potential as PT                                # noqa: E402
from agent import wahrscheinlichkeit as WK                       # noqa: E402

CACHE = "anker_h_neu_2026_08_30.json"
MIND_JE_TAG = 15
CRV = 2.0
STOP_REL = 0.05
VARIANTEN = (("A  H = 4,5  (heute)", 4.5),
             ("B  H = 0,0  (null)", 0.0),
             ("C  H = 2,25 (halbiert)", 2.25),
             ("D  H = -2,0 (nur Anschauung)", -2.0))


def _raenge_ersatz(anker, rng):
    """Fuenftel fuer Funding und Turnover - je Kalendertag, zufaellig.

    ⚠️ DAS IST EINE ERSATZGROESSE UND WIRD ALS SOLCHE BEHANDELT. Die echten
    Raenge liegen fuer diese Ankermenge nicht vor. Was hier gebraucht wird,
    ist nicht ihre Vorhersagekraft, sondern ihre VERTEILUNG: jeder Tag
    verteilt seine Anker gleichmaessig auf fuenf Fuenftel, genau wie
    `marktrang._rang` es tut. Damit stimmt die Punkteverteilung, gegen die
    die Schwelle greift - und nur die ist hier die Frage.

    Ein Ersatz mit VORHERSAGEKRAFT waere hier falsch: er wuerde den
    Ertragsunterschied zwischen den Varianten verwaessern, weil dann ein
    Teil der Auswahl von ihm statt von H kaeme.
    """
    je_tag = {}
    for a in anker:
        je_tag.setdefault(a["datum"], []).append(a)
    for tag, z in je_tag.items():
        if len(z) < MIND_JE_TAG:
            for x in z:
                x["f5"] = x["t5"] = None
            continue
        for feld in ("f5", "t5"):
            r = rng.permutation(len(z))
            for x, i in zip(z, r):
                x[feld] = min(int(i / len(z) * 5), 4)
    return anker


def setze_h(punkte):
    """H's Punktwert in der REGISTRIERUNG ersetzen - befristet."""
    neu = []
    for b in WK.BEITRAEGE:
        if b.merkmal == "h":
            neu.append(WK.Beitrag(
                name=b.name,
                zustand=("traegt" if punkte else "null"),
                punkte=float(punkte), merkmal="h", quelle=b.quelle,
                warum=b.warum, klassen=b.klassen))
        else:
            neu.append(b)
    WK.BEITRAEGE = tuple(neu)


def main():
    anker = json.loads(io.open(CACHE, encoding="utf-8").read())
    anker = [a for a in anker if a.get("in_r") is not None]
    rng = np.random.default_rng(20260830)
    anker = _raenge_ersatz(anker, rng)
    anker = [a for a in anker if a.get("f5") is not None]
    n = len(anker)
    n_h = sum(1 for a in anker if a["h_alt"])
    basis_ertrag = st.median([a["in_r"] for a in anker])
    original = WK.BEITRAEGE

    print("=" * 100)
    print("SIMULATION — WAS AENDERT SICH AM TRICHTER, WENN H SICH AENDERT?")
    print("=" * 100)
    print("%d Anker, davon %d mit H (%.2f %%), %d Kalendertage"
          % (n, n_h, 100 * n_h / n, len({a["datum"] for a in anker})))
    print("Schwelle %.3f R, CRV %.1f, Stop %.0f %%   (Produktionsfunktion)"
          % (PT.schwelle(), CRV, 100 * STOP_REL))
    print("Ertrag ohne jede Schwelle: %+.4f R" % basis_ertrag)
    print()
    print("  %-30s %10s %11s %12s %14s"
          % ("Variante", "Durchlass", "Ertrag", "gegen ohne", "je verworfenem"))

    ergebnisse = {}
    try:
        for klar, punkte in VARIANTEN:
            setze_h(punkte)
            # Die 3x5x5 moeglichen Lagen einmal vorrechnen - 620.000 Aufrufe
            # der Produktionsfunktion waeren sonst der ganze Lauf.
            tabelle = {}
            for h in (True, False):
                for f in range(5):
                    for t in range(5):
                        tabelle[(h, f, t)] = PT.rechne(
                            crv=CRV, stop_relativ=STOP_REL, klasse="krypto",
                            instrument="spot", strategie="einstieg", h=h,
                            merkmale={"funding_fuenftel": f,
                                      "turnover_fuenftel": t}).wert_r
            durch = [a for a in anker
                     if PT.traegt(tabelle[(bool(a["h_alt"]), a["f5"], a["t5"])])]
            if not durch:
                print("  %-30s %9s" % (klar, "0 %"))
                continue
            ertrag = st.median([a["in_r"] for a in durch])
            quote = len(durch) / n
            gewinn = ertrag - basis_ertrag
            je = gewinn / (1 - quote) if quote < 1 else float("nan")
            ergebnisse[klar] = (quote, ertrag, gewinn, je, durch)
            print("  %-30s %8.1f %% %+11.4f %+12.4f %+14.4f"
                  % (klar, 100 * quote, ertrag, gewinn, je))
    finally:
        WK.BEITRAEGE = original

    print()
    print("=" * 100)
    print("WAS DIE VARIANTEN AN DEN H-ANKERN SELBST TUN")
    print("=" * 100)
    print("  %-30s %12s %12s %14s"
          % ("Variante", "H-Anker durch", "davon Ertrag", "Nicht-H Ertrag"))
    for klar, (quote, _e, _g, _j, durch) in ergebnisse.items():
        mit = [a["in_r"] for a in durch if a["h_alt"]]
        ohne = [a["in_r"] for a in durch if not a["h_alt"]]
        print("  %-30s %11d %+12.4f %+14.4f"
              % (klar, len(mit),
                 st.median(mit) if mit else float("nan"),
                 st.median(ohne) if ohne else float("nan")))

    print()
    print("=" * 100)
    print("⚠️ DIE ENTSCHEIDENDE ZEILE — was kostet oder bringt H's Wegfall?")
    print("=" * 100)
    a = ergebnisse.get("A  H = 4,5  (heute)")
    b = ergebnisse.get("B  H = 0,0  (null)")
    if a and b:
        print("  Durchlass   %6.1f %%  ->  %6.1f %%   (%+.1f Punkte)"
              % (100 * a[0], 100 * b[0], 100 * (b[0] - a[0])))
        print("  Ertrag      %+.4f R  ->  %+.4f R   (%+.4f R)"
              % (a[1], b[1], b[1] - a[1]))
        print()
        nur_h = [x for x in a[4] if x["h_alt"]
                 and x not in b[4]] if len(a[4]) < 200000 else None
        print("  Anker, die NUR wegen H durchkommen: %d (%.2f %% aller Anker)"
              % (len(a[4]) - len(b[4]), 100 * (len(a[4]) - len(b[4])) / n))
        raus = set(id(x) for x in b[4])
        verloren = [x for x in a[4] if id(x) not in raus]
        if verloren:
            print("  ihr Ertrag: %+.4f R   (Gesamtfeld %+.4f R)"
                  % (st.median([x["in_r"] for x in verloren]), basis_ertrag))
            print()
            print("  ⚠️ LESART: liegt ihr Ertrag UNTER dem Gesamtfeld, dann")
            print("     laesst H genau die schlechteren Anker durch - dann ist")
            print("     sein Wegfall kein Verlust, sondern eine Verbesserung.")


if __name__ == "__main__":
    main()
