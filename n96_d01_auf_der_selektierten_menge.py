# -*- coding: utf-8 -*-
"""N-96 — d01 auf der SELEKTIERTEN Menge, wie der Code es verlangt

## ⚠️⚠️⚠️ Warum dieser Lauf sein MUSS

`agent/wahrscheinlichkeit.py` traegt direkt neben der Funding-Tabelle
eine ausdrueckliche Warnung, gesetzt nach einem Fehler:

> ⚠️⚠️⚠️ TABELLE AM 07.09.2026 GEAENDERT UND AM SELBEN TAG
> ZURUECKGENOMMEN. Der Vorgang steht hier, weil er die naechste
> Aenderung an dieser Stelle verhindern soll. [...]
> **WER DIESE TABELLE AENDERN WILL, MUSS AUF DER SELEKTIERTEN MENGE
> MESSEN.** Alles andere misst eine Menge, in der die Beitraege gar
> nicht wirken - und bekommt zuverlaessig einen Nullbefund.

**N-92, N-93 und N-95 liefen alle auf `frei`.** Damit ist der Vorschlag,
Stufe 0 und 1 zusammenzulegen, nach dieser Vorgabe NICHT gedeckt - egal
wie sauber die Messung sonst war.

## ⚠️ Und N-91 deutet in die andere Richtung

Auf der 20-%-Menge waren `funding`s Haelften GEGENLAEUFIG und BEIDE
TRENNBAR (+0,0541 [+0,022..+0,088] und -0,0268 [-0,049..-0,004]). Wenn
der Knick dort real ist, sind die Stufen **richtig so** - und
Zusammenlegen waere ein Rueckbau.

## ⚠️⚠️ Der Widerspruch, der dabei offen bleibt (2.228)

Die Stufen wurden auf `frei` ABGELEITET (`rechne_funding_beitrag.py`
bildet keine Auswahl - an der Quelle geprueft), duerfen aber nur auf der
SELEKTIERTEN Menge GEAENDERT werden. Beides zugleich kann nicht richtig
sein. **Dieser Lauf entscheidet den Widerspruch nicht - er befolgt die
Vorgabe.**

## ⚠️⚠️⚠️ KORRIGIERT NACH DEM ERSTEN LAUF (09.09.2026)

Der erste Lauf hat **zuerst verengt und dann gerangt**. Damit entstanden
Fuenftel INNERHALB der Momentum-Kohorte - ein Merkmal, das weder
`agent/marktrang.raenge` noch `messe_beitrag_auf_auswahl.sammle`
berechnet. Beide rangen ueber die MESSBASIS und lesen den Rang danach nur
ab:

    # ⚠️ DER RANG ENTSTEHT UEBER DEN MARKT, ABGELESEN WIRD ER FUER UNS.
    rang = _rang(werte)          # agent/marktrang.py

⚠️ Befund 2.229 hat genau dafuer die Zahl: ueber die enge Menge gerangt
dreht `funding` das Vorzeichen (+3,43 gegen -3,10, nur 54 % identische
Fuenftel). Die Ergebnisse des ersten Laufs auf 5 %, 10 % und 20 % sind
damit UNGUELTIG; nur die Zeile `frei` war unberuehrt, weil dort nichts
maskiert wird.

## Was gemessen wird

    d01 = Stufe 1 - Stufe 0    je Kalendertag, auf 5 % / 10 % / 20 %
    d34 = Stufe 3 - Stufe 4    als Pruefstein, ob die Maschinerie traegt
    Nullpunkt                  40 Ziehungen mit gemischten Raengen
    Kontrolle                  `zufall` auf denselben Mengen

⚠️ F-212 nennt als selektierte Menge die **obersten 5 % je Tag nach
250-Tage-Momentum**. Die ist die massgebliche; 10 % und 20 % laufen mit,
weil die Datenlage bei 5 % duenn wird.

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

    d01 trennbar positiv      -> der Knick ist REAL, die Stufen bleiben,
                                 mein Vorschlag faellt
    d01 nicht trennbar        -> der Nullbefund gilt auch dort, und die
                                 Zusammenlegung waere gedeckt
    d34 nicht trennbar        -> untermaechtig, dann sagt d01 nichts

⚠️ Faellt mein Vorschlag, ist das das richtige Ergebnis - die Warnung im
Code hat dann getan, wofuer sie dasteht.

    python n96_d01_auf_der_selektierten_menge.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_beitrag_auf_auswahl as A                        # noqa: E402
import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messmenge                                              # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402
from messnorm import _block                                   # noqa: E402
from messnorm_auswahl import MENGEN                           # noqa: E402
from n91_rangkorrelation_form import band                     # noqa: E402

NULL_ZIEH = 40
SAAT = 20260909
MENGEN_PRUEFEN = ("5%", "10%", "20%", "frei")


def paar_je_tag(je_tag, mom, anteil, a, b, mische=None):
    """median(Fuenftel a) - median(Fuenftel b), NACH der Auswahl.

    ⚠️ Die Fuenftel entstehen aus dem Rang INNERHALB der Gewaehlten -
    genau wie `rechne_funding_beitrag` es auf seiner Menge tut. Wer den
    Marktrang nimmt und dann verengt, bekommt die Ungleichbesetzung aus
    N-64 (1,5 gegen 29,7 Anker).
    """
    aus, bes = {}, {k: [] for k in (a, b)}
    for tag, zeilen in je_tag.items():
        if len(zeilen) < 15:
            continue
        w = np.array([x["kennzahl"] for x in zeilen], float)
        y = np.array([x["in_r"] for x in zeilen], float)
        # ⚠️⚠️⚠️ ERST RANGEN, DANN VERENGEN - und das ist keine
        # Geschmacksfrage. `agent/marktrang.raenge` bildet den Rang ueber
        # die MESSBASIS und liest ihn fuer unsere Symbole nur ab; `sammle`
        # haelt es genauso ("NACH dem Rang verengen, nie davor"). Wer
        # zuerst verengt, erzeugt ein Fuenftel, das die Anlage nie
        # berechnet - und bei `funding` dreht das laut 2.229 das
        # Vorzeichen (+3,43 gegen -3,10).
        r = np.argsort(np.argsort(w)) / max(len(w) - 1, 1)
        if mische is not None:
            r = mische.permutation(r)
        m0 = A._auswahl_maske(zeilen, mom.get(tag) or {}, anteil, None)
        if m0 is None or m0.sum() < 12:
            continue

        def f(k):
            m = (r >= k / 5) & ((r < (k + 1) / 5) if k < 4 else (r <= 1.0))
            m = m & m0
            bes[k].append(int(m.sum()))
            return float(np.median(y[m])) if m.sum() >= 2 else None
        va, vb = f(a), f(b)
        if va is not None and vb is not None:
            aus[tag] = va - vb
    return aus, {k: (float(np.mean(v)) if v else 0.0) for k, v in bes.items()}


def nullpunkt(je_tag, mom, anteil, a, b, block):
    w = []
    for z in range(NULL_ZIEH):
        r, _ = paar_je_tag(je_tag, mom, anteil, a, b,
                           np.random.default_rng(SAAT + z))
        bb = band(r, block, zieh=300, saat=SAAT + z)
        if bb:
            w.append(bb[0])
    return float(np.mean(w)) if w else float("nan")


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    zus = zusatzquellen()
    block = _block(HORIZONT)

    print("=" * 104)
    print("N-96 — d01 auf der SELEKTIERTEN Menge, wie der Code es verlangt")
    print("=" * 104)
    print("  %s" % messmenge.zeile())
    print("  ⚠️ `wahrscheinlichkeit.py`: 'WER DIESE TABELLE AENDERN WILL, "
          "MUSS AUF DER")
    print("     SELEKTIERTEN MENGE MESSEN.' N-92/93/95 liefen auf `frei` "
          "- also nicht gedeckt.")
    print("  ⚠️ F-212 nennt die obersten 5 %% je Tag nach 250-Tage-"
          "Momentum als die massgebliche.")

    for kand in ("funding", "zufall"):
        je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        print()
        print("  %s" % kand.upper())
        print("     %-6s %-5s %10s %22s %10s %11s  %s"
              % ("Menge", "Paar", "Wert", "Band", "Nullpunkt", "Besetzung",
                 "Urteil"))
        for menge in MENGEN_PRUEFEN:
            for name, (a, b) in (("d01", (1, 0)), ("d34", (3, 4))):
                reihe, bes = paar_je_tag(je, mom, MENGEN[menge], a, b)
                if not reihe:
                    print("     %-6s %-5s nicht messbar" % (menge, name))
                    continue
                bb = band(reihe, block)
                if bb is None:
                    print("     %-6s %-5s zu wenige Bloecke (%d Tage)"
                          % (menge, name, len(reihe)))
                    continue
                n0 = nullpunkt(je, mom, MENGEN[menge], a, b, block)
                traegt = bb[1] > max(0.0, n0) or bb[2] < min(0.0, n0)
                print("     %-6s %-5s %+10.4f [%+.4f .. %+.4f] %+10.4f "
                      "%5.1f/%-5.1f  %s"
                      % (menge, name, bb[0], bb[1], bb[2], n0,
                         bes[a], bes[b],
                         "⚠️ TRENNBAR" if traegt else "nicht trennbar"),
                      flush=True)
            print()

    print("=" * 104)
    print("WAS DAS HEISST")
    print("=" * 104)
    print("  ⚠️ Ist d01 auf der selektierten Menge TRENNBAR POSITIV, ist "
          "der Knick REAL -")
    print("     die Stufen bleiben, und mein Vorschlag (Zusammenlegen) "
          "faellt.")
    print("  ⚠️ Ist er auch dort nicht trennbar, waere die Zusammenlegung "
          "gedeckt -")
    print("     aber nur, wenn d34 zeigt, dass die Maschinerie dort "
          "ueberhaupt traegt.")
    print("  ⚠️⚠️ Und der Widerspruch aus 2.228 bleibt offen: die Stufen "
          "wurden auf `frei`")
    print("     ABGELEITET, duerfen aber nur auf der selektierten Menge "
          "GEAENDERT werden.")
    print("     Dieser Lauf entscheidet ihn nicht - er befolgt die "
          "Vorgabe.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
