# -*- coding: utf-8 -*-
"""Positivkontrolle zu K-1: WIE GROSS muss ein Effekt sein, damit wir ihn finden?

## Warum diese Kontrolle vor der Deutung kommt

Kapitel 103 ist genau hier gescheitert - nicht am Befund, sondern an der
Trennschaerfe. Die dortige Positivkontrolle fand einen eingepflanzten Effekt
von +22,1 Punkten *gerade noch*. Woertlich: *"Alles darunter kann diese
Datenmenge nicht von Zufall unterscheiden."* Vorfilter H traegt +4,5.

    Ein Nullbefund aus einem Werkzeug, das den gesuchten Effekt nicht sehen
    kann, ist kein Nullbefund. Er ist keine Antwort.

Deshalb wird hier NICHT gefragt "traegt die Kombination", sondern:

    Welche Effektgroesse findet dieses Werkzeug auf 485 Reihen noch?

## Der Aufbau

In eine **vorab benannte, unauffaellige** Zelle wird ein echter Effekt
eingepflanzt - bewusst NICHT die beste Zelle des echten Laufs, damit die
Kontrolle nicht auf den Befund hin gebaut ist.

    gepflanzte Zelle:  schwankung=mitte / umschlag=mitte

Der Effekt wird in Stufen eingepflanzt (0,05 bis 0,60 R) und jedesmal gegen
die Maximum-Schwelle aus dem echten Lauf gehalten. Die kleinste Stufe, die
gefunden wird, IST die Trennschaerfe.
"""
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B
import messe_konjunktion as K

GEPFLANZT = ("schwankung", "mitte", "umschlag", "mitte")
STUFEN = (0.05, 0.10, 0.20, 0.30, 0.45, 0.60)
LAEUFE_SCHWELLE = 60


def pflanze(je_tag, staerke):
    """Kopie der Anker, in der die benannte Zelle um `staerke` R angehoben ist."""
    a = K.KANAELE.index(GEPFLANZT[0])
    b = K.KANAELE.index(GEPFLANZT[2])
    ta = K.TERZILE.index(GEPFLANZT[1])
    tb = K.TERZILE.index(GEPFLANZT[3])
    aus = {}
    for tag, z in je_tag.items():
        z = z.copy()
        ma = K.terzile(z[:, a])
        mb = K.terzile(z[:, b])
        treffer = (ma == ta) & (mb == tb)
        z[treffer, 5] += staerke
        aus[tag] = z
    return aus


def main():
    reihen = B.lade()
    je_tag = K.anker(reihen, 20)
    print("=" * 84)
    print("POSITIVKONTROLLE ZU K-1 — welche Effektgroesse findet das Werkzeug?")
    print("=" * 84)
    print("gepflanzte Zelle: %s=%s / %s=%s   (vorab benannt, nicht die beste)"
          % GEPFLANZT)
    print("523 Reihen · %d Anker · %d Kalendertage"
          % (sum(len(z) for z in je_tag.values()), len(je_tag)))

    # Die Schwelle: Maximum-Verteilung unter der Nullhypothese
    rng = np.random.default_rng(4711)
    maxima = []
    for _ in range(LAEUFE_SCHWELLE):
        p = K.zellen(je_tag, rng)
        if p:
            maxima.append(max(p.values()))
    schwelle = float(np.quantile(maxima, 0.95))
    print()
    print("Schwelle aus %d Placebo-Laeufen (95 %% des Maximums): %+.4f R"
          % (LAEUFE_SCHWELLE, schwelle))
    print()
    print("%-10s %14s %14s   %s" % ("gepflanzt", "gemessen dort", "bester Wert", "gefunden?"))
    kleinste = None
    for staerke in STUFEN:
        z = K.zellen(pflanze(je_tag, staerke))
        schluessel = (GEPFLANZT[0] + "/" + GEPFLANZT[2],
                      GEPFLANZT[1] + "/" + GEPFLANZT[3])
        dort = z.get(schluessel)
        bester = max(z.values())
        ist_sieger = max(z, key=z.get) == schluessel
        gefunden = dort is not None and dort > schwelle and ist_sieger
        if gefunden and kleinste is None:
            kleinste = staerke
        print("%+.2f R    %+13.4f %+14.4f   %s"
              % (staerke, dort if dort is not None else float("nan"), bester,
                 "JA" if gefunden else ("nur ueber Schwelle" if dort and dort > schwelle
                                        else "nein")))
    print()
    if kleinste is None:
        print("  -> WARNUNG: selbst %+.2f R wird nicht gefunden. Das Werkzeug ist"
              % STUFEN[-1])
        print("     fuer diese Frage zu stumpf - jeder Nullbefund waere bedeutungslos.")
    else:
        print("  -> TRENNSCHAERFE: ab %+.2f R wird ein Effekt gefunden." % kleinste)
        print("     Alles darunter kann dieses Werkzeug nicht von Zufall trennen.")
        print("     Zum Vergleich: Vorfilter H traegt +4,5 Punkte Trefferquote,")
        print("     das sind bei CRV 2,0 rund +0,135 R.")


if __name__ == "__main__":
    main()
