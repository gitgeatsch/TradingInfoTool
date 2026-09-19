# -*- coding: utf-8 -*-
"""V3a: GELTEN DIE BEITRAEGE FUER DIE HALTEFRAGE? (19.09.2026, Paket V)

⚠️⚠️ WARUM DAS NICHT SELBSTVERSTAENDLICH IST - ES IST SCHON EINMAL GEKIPPT.

Befund **2.287** (gilt): `funding` und `oi_aenderung` wirken FUER DIE
AKKUMULATION UMGEKEHRT - ihr ,gutes` Fuenftel ist systematisch der
SCHLECHTERE Kauftag (-0,0230 und -0,0178, beide p 0,000). Beide sind live
als `strategien=('einstieg',)` deklariert und greifen deshalb dort nicht;
der Befund nennt das woertlich *ein Glueck, kein Zufall*.

Und **2.220-haltefrage** (gilt) haelt fest: saemtliche Beitraege sind fuer
die Lage `spot x einstieg` gemessen. Ob sie fuer die HALTEFRAGE gelten, ist
nie geprueft worden - obwohl `agent/auswahl.py` selbst in die Mail
schreibt, dass bei einer gehaltenen Position die Frage ,halten oder
verkaufen` lautet.

➔ DIESE MESSUNG BEANTWORTET GENAU DAS. Sie ist die Voraussetzung dafuer,
dass V3b eine Verkaufsbewertung auf diese Beitraege stellen darf.

## Der Aufbau

    Menge       DIE HALTEMENGE als Stellvertreter: je Tag die Symbole, die
                in den letzten %d Tagen mindestens einmal in den obersten
                20 %% nach 250-Tage-Momentum standen - also die, die man
                gekauft haette und daher halten wuerde.
    Selektion   `menge="frei"` - die Haltemenge IST die Selektion; ein
                zweites Momentum-Sieb darueber waere die Auswahlfrage,
                nicht die Haltefrage.
    Urteil      `messnorm_auswahl.pruefe_auswahl` - Band, Nullpunkt,
                Trennschaerfe, Positivkontrolle, Tagesklammer.

⚠️⚠️ DER ECHTE BESTAND IST HISTORISCH UNBEKANNT. Was der Nutzer 2023
gehalten hat, steht nirgends; die Haltemenge ist deshalb ein
STELLVERTRETER und wird als solcher ausgewiesen. Sie ist bewusst weit
gefasst - wer einmal gut genug war, bleibt %d Tage drin.

⚠️ Vergleichsmassstab sind die Einstiegsurteile aus 2.460-norm (ab 2023):
oi_aenderung TRAEGT, funding und turnover tragen nicht bis 0,04 bzw 0,09 R.

⚠️ Nur lesend, kein LLM.
"""
from __future__ import annotations

import sys
import time

import numpy as np

import messnorm
import messnorm_auswahl as MA
import messmenge
import phase3_reproduktion as R
from messe_beitrag_auf_auswahl import momentum250

AB_2023 = "2023-01-01"
HALTE_FENSTER = 60        # wie lange ein Wert nach der Auswahl als gehalten gilt
ANTEIL_KAUF = 0.20        # womit er ueberhaupt hineinkommt
LAGE = messnorm.Lage("spot", "halten")
VORBEHALT = ("Haltemenge ist ein STELLVERTRETER - der echte Bestand ist "
             "historisch unbekannt; gilt auf der Stellvertretermenge, NICHT "
             "auf der Live-Menge (N3 b)")

__doc__ = __doc__ % (HALTE_FENSTER, HALTE_FENSTER)


def haltemenge(mom: dict) -> dict:
    """tag -> Menge der Symbole, die man an diesem Tag halten wuerde.

    ⚠️ ROLLIEREND, NICHT AM STICHTAG: wer heute nicht mehr unter den besten
    20 % ist, wird nicht sofort verkauft - genau darum geht ja die Frage.
    Deshalb ein Fenster von HALTE_FENSTER Tagen."""
    tage = sorted(mom)
    gewaehlt = {}
    for t in tage:
        werte = mom.get(t) or {}
        if len(werte) < 5:
            gewaehlt[t] = set()
            continue
        k = max(1, int(round(len(werte) * ANTEIL_KAUF)))
        gewaehlt[t] = {s for s, _ in sorted(werte.items(),
                                            key=lambda x: -x[1])[:k]}
    aus = {}
    for i, t in enumerate(tage):
        fenster = tage[max(0, i - HALTE_FENSTER + 1):i + 1]
        menge = set()
        for f in fenster:
            menge |= gewaehlt[f]
        aus[t] = menge
    return aus


def main() -> int:
    t0 = time.time()
    nur_arten = sys.argv[1:] or ["funding", "turnover", "oi_aenderung"]
    print("=" * 100)
    print("V3a - GELTEN DIE BEITRAEGE FUER DIE HALTEFRAGE?")
    print("=" * 100)
    print("  " + messmenge.zeile())
    print("  " + messnorm.standardzeile().replace("\n", "\n  "))
    print("  Lage: %s x %s · Fenster ab %s · Horizont H%d"
          % (LAGE.instrument, LAGE.strategie, AB_2023, R.HORIZONT))
    print("  ⚠️ %s" % VORBEHALT)
    print("\n  Kursreihen laden ...")
    reihen = R.B.lade("krypto", "V1")
    mom = momentum250(reihen)
    halte = haltemenge(mom)
    groessen = [len(v) for v in halte.values() if v]
    print("  %d Reihen · %d Tage mit Haltemenge · im Mittel %.0f Werte je Tag"
          % (len(reihen), len(groessen), float(np.mean(groessen))))

    # ⚠️ DER VERGLEICHSMASSSTAB steht hier, nicht im Kopf der Ausgabe -
    # ein Urteil ohne den Einstiegsstand daneben ist nicht einzuordnen.
    einstieg = {"funding": "traegt nicht bis 0,0401 R",
                "turnover": "traegt nicht bis 0,0857 R",
                "oi_aenderung": "TRAEGT (+0,0433 R)"}

    for art in nur_arten:
        t1 = time.time()
        je_tag = R._ab(R.K.baue(reihen, art, R._zusatz(art),
                                horizont=R.HORIZONT), AB_2023)
        print("\n" + "-" * 100)
        print("  %s - %d Tage ab %s" % (art.upper(), len(je_tag), AB_2023))
        print("  Einstieg (2.460-norm): %s" % einstieg.get(art, "?"))
        try:
            b = MA.pruefe_auswahl(art, je_tag, mom, lage=LAGE, menge="frei",
                                  rng=np.random.default_rng(messnorm.SAAT),
                                  horizont=R.HORIZONT, nur=halte,
                                  zielgroesse="bewegung_r")
        except ValueError as x:
            print("   ⚠️ von der Norm zurueckgewiesen: %s" % x)
            continue
        print("   " + b.zeile())
        if getattr(b, "urteil", None) is not None:
            print("   Urteil (HALTEN): %s" % b.urteil)
        print("   ⚠️ %s" % VORBEHALT)
        print("   (%.0f s)" % (time.time() - t1))

    print("\n" + "=" * 100)
    print("  LESEART: ein Beitrag ,traegt` hier, wenn sein oberstes Fuenftel")
    print("  innerhalb der HALTEMENGE die schlechteren Folgeperioden trennt -")
    print("  dann waere er als Verkaufsgrund brauchbar. ⚠️ Ein UMGEKEHRTES")
    print("  Vorzeichen ist kein Nullbefund, sondern ein Befund (2.287).")
    print("  (%.0f s gesamt)" % (time.time() - t0))
    print("=" * 100)
    return 0


if __name__ == "__main__":
    sys.exit(main())
