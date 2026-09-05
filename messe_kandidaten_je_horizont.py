# -*- coding: utf-8 -*-
"""D1 / N-47: Auf welchem HORIZONT und welcher ZIELGROESSE gilt was? (05.09.2026)

## Warum diese Messung sein muss

In der Kette stehen drei verschiedene Horizonte nebeneinander, und niemand
hat sie je verglichen:

    60 Tage   `messe_zielregel.HORIZONT` - worauf ich am 05.09. ALLE
              Kandidaten gemessen habe, weil das Werkzeug das so hatte
    20 Tage   worauf `funding` und `turnover` als Beitraege gefittet wurden
     3-5 Tage worauf tatsaechlich gehandelt wird (Nutzervorgabe)

Dazu kommen ZWEI verschiedene Zielgroessen, die bisher vermischt wurden:

    RENDITE      mittlere Rendite in R nach H Tagen
                 -> darauf beruht der Funding-Befund (+0,137 R bei H20,
                    monoton, alle Gegenpruefungen bestanden)
    BARRIERE     Wahrscheinlichkeit, +CRV zu treffen BEVOR -1 kommt
                 -> das behauptet die Bewertung im Betrieb

⚠️ **Beides gleichzeitig zu verwechseln erzeugt genau die Scheinbefunde,
die heute dreimal aufgeflogen sind** (F-218, F-219, F-223). Deshalb wird
hier NICHTS zusammengefasst: jede Zelle nennt Horizont UND Zielgroesse.

## Der Aufbau

    Kandidaten   amihud · vola · schnitt50 · funding · turnover
    Kontrolle    zufall - muss in JEDER Zelle im Rauschen bleiben
    Klammer      IMMER Tag (Vorgabe 31.08.) - nie gepoolt
    Horizonte    5 · 20 · 60

⚠️ **Die echten Funktionen, keine Kopien.** Der Barrieren-Horizont wird
ueber `messe_zielregel.HORIZONT` gesetzt und `ergebnisse()` unveraendert
gerufen; die Rendite kommt aus `messe_kandidaten_als_regel.baue(horizont=H)`
als `in_r`.

## ⚠️ Die Zensur - vorab benannt, nicht nachtraeglich entschuldigt

Bei kurzem Horizont loesen sich WENIGER Anker auf: wer weder +CRV noch -1
erreicht, zaehlt bei der Barriere nicht. Die aufgeloeste Teilmenge ist dann
zu den grossen Bewegern verschoben. **Die Aufloesungsquote wird je Zelle
ausgewiesen** - eine Barrierenspanne bei 8 % Aufloesung ist etwas anderes
als eine bei 60 %.

Die RENDITE-Spalte hat dieses Problem nicht: dort zaehlt jeder Anker.

    python messe_kandidaten_je_horizont.py
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
# ⚠️ IMPORTIERT, NICHT NACHGEBAUT - dieselbe Klammer wie in N-46.
from messe_fuenftel_mit_tagesklammer import (               # noqa: E402
    je_tag_und_fuenftel, abweichung_je_fuenftel, _spanne)

ARTEN = ("amihud", "vola", "schnitt50", "funding", "turnover", "zufall")
HORIZONTE = (5, 20, 60)
CRV = 2.0
VARIANTE = "ZIEL 2,0"


def _monoton(w: list) -> bool:
    g = [x for x in w if x == x]
    if len(g) < 5:
        return False
    return (all(g[i] >= g[i + 1] for i in range(4))
            or all(g[i] <= g[i + 1] for i in range(4)))


def rendite_je_fuenftel(gebaut: dict, f5: dict) -> tuple[list, int, list]:
    """Mittlere `in_r` je Fuenftel, ABWEICHUNG von der Tagesrate.

    ⚠️ DIE FUENFTEL KOMMEN VON AUSSEN, aus `_fuenftel_je_tag` - sie werden
    hier NICHT noch einmal gebildet (05.09., eigener Fehler in der ersten
    Fassung).
    #
    Der Nachbau hatte einen anderen Nenner: die echte Funktion rechnet
    `n = len(sortiert) - 1`, mein Nachbau `n = len(paare)`. Die
    Fuenftelgrenzen lagen damit leicht verschoben - und die Zeilen
    BARRIERE und RENDITE haetten VERSCHIEDENE Fuenftel verglichen, ohne
    dass irgendetwas angeschlagen haette.
    #
    Ein Test muss die echte Funktion rufen, nie eine Kopie.
    """
    summe = [0.0] * 5
    gewicht = [0.0] * 5
    streu = []
    tage = 0
    for tag, liste in gebaut.items():
        je_sym = f5.get(tag)
        if not je_sym:
            continue
        paare = [(je_sym.get(e["sym"]), e.get("in_r")) for e in liste
                 if e.get("in_r") is not None and je_sym.get(e["sym"]) is not None]
        if len(paare) < 10:
            continue
        werte = [p[1] for p in paare]
        mittel_tag = float(np.mean(werte))
        streu.append(float(np.std(werte)))
        tage += 1
        for f, r in paare:
            summe[f] += r - mittel_tag
            gewicht[f] += 1.0
    aus = [summe[f] / gewicht[f] if gewicht[f] else float("nan")
           for f in range(5)]
    # ⚠️ Standardfehler aus der TAGESSTREUUNG - eine geratene Schwelle
    # waere hier derselbe Fehler wie dreimal zuvor an diesem Tag.
    sd = float(np.mean(streu)) if streu else float("nan")
    fehler = [sd / (gewicht[f] ** 0.5) if gewicht[f] else float("nan")
              for f in range(5)]
    return aus, tage, fehler


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    print("  %d Reihen" % len(reihen))

    print("  lade funding ...", flush=True)
    fu = F.lade_funding()
    print("  lade turnover ...", flush=True)
    tu = MB.reihe("data/onchain_historie.db", "splycur")
    quelle = {"funding": fu, "turnover": tu}

    urspruenglich = ZR.HORIZONT
    try:
        for h in HORIZONTE:
            # ⚠️ Der Modulwert wird gesetzt und die ECHTE Funktion gerufen -
            # keine Kopie der Barrierenschleife.
            ZR.HORIZONT = h
            print()
            print("Barrieren-Ausgaenge fuer Horizont %d ..." % h, flush=True)
            zeilen = ZR.ergebnisse(reihen)
            entschieden = sum(
                1 for z in zeilen
                if z.get(VARIANTE) is not None
                and (abs(z[VARIANTE] - CRV) < 1e-9 or abs(z[VARIANTE] + 1.0) < 1e-9))
            quote = 100.0 * entschieden / max(len(zeilen), 1)

            print("=" * 96)
            print("HORIZONT %d TAGE — %d Anker · %.1f %% aufgeloest"
                  % (h, len(zeilen), quote))
            print("=" * 96)
            print("  %-11s %-9s %-34s %8s %8s %s"
                  % ("Groesse", "Ziel", "Abweichung je Fuenftel", "Spanne",
                     "Rauschen", "monoton"))
            for art in ARTEN:
                gebaut = K.baue(reihen, art, quelle.get(art), horizont=h)
                f5 = _fuenftel_je_tag(gebaut)

                bq, n_tage, feh = abweichung_je_fuenftel(
                    je_tag_und_fuenftel(zeilen, tage_je_sym, f5))
                gr = 2.0 * max((x for x in feh if x == x), default=float("nan"))
                sp = _spanne(bq)
                print("  %-11s %-9s %-34s %7.2f %8.2f %5s%s"
                      % (art, "BARRIERE",
                         " ".join("%+5.2f" % x for x in bq), sp, gr,
                         "ja" if _monoton(bq) else "nein",
                         "" if sp > gr else "   <- im Rauschen"))

                rq, r_tage, rfeh = rendite_je_fuenftel(gebaut, f5)
                rgr = 2.0 * max((x for x in rfeh if x == x), default=float("nan"))
                rsp = _spanne(rq)
                print("  %-11s %-9s %-34s %7.3f %8.3f %5s%s"
                      % ("", "RENDITE",
                         " ".join("%+5.3f" % x for x in rq), rsp, rgr,
                         "ja" if _monoton(rq) else "nein",
                         "" if rsp > rgr else "   <- im Rauschen"))
    finally:
        ZR.HORIZONT = urspruenglich

    print()
    print("=" * 96)
    print("⚠️ LESEART")
    print("=" * 96)
    print("  BARRIERE in Prozentpunkten der Quote · RENDITE in R")
    print("  Die beiden Zeilen sind NICHT ineinander umrechenbar - genau")
    print("  diese Verwechslung hat F-218/F-219/F-223 erzeugt.")
    print()
    print("  `zufall` muss in JEDER Zelle im Rauschen liegen.")
    print("  Die Aufloesungsquote je Horizont steht in der Ueberschrift:")
    print("  eine Barrierenspanne bei niedriger Aufloesung gilt nur fuer")
    print("  die grossen Beweger, nicht fuer alle Anker.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
