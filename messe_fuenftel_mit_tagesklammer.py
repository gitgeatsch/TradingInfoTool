# -*- coding: utf-8 -*-
"""N-46: die Fuenftel MIT TAGESKLAMMER - die Regel, die es laengst gibt (05.09.2026)

## ⚠️ Der Anlass ist ein eigener Fehler, zum DRITTEN Mal

Die stehende Vorgabe (31.08.) lautet: **ein Beitrag muss je KALENDERTAG
gemessen werden, nicht gepoolt.** Bei Vorfilter H waren das 4,6 Punkte
Unterschied - gepoolt +3,57, je Kalendertag -1,02 und nicht trennbar. Die
Memory dazu vermerkt ausdruecklich: *"Mir zweimal passiert: H und B."*

`quote_je_fuenftel` - das Werkzeug, auf dem heute JEDE gemessene Spanne
beruht (F-217, F-221, F-222) - **poolt ueber die ganze Historie.**

## Warum es die LAENGS-Form zerlegt und die QUER-Form kaum beruehrt

    QUER    Fuenftel je TAG ueber Symbole
            -> jeder Tag liefert per Konstruktion gleich viele Anker je
               Fuenftel. Die Tageszusammensetzung ist ausgeglichen, und
               Poolen ist weitgehend harmlos.

    LAENGS  Fuenftel je SYMBOL ueber seine eigene Zeit
            -> ein einzelner Tag kann fast ALLE Symbole im selben Fuenftel
               haben (ruhige Marktphase = viele Symbole in ihrem eigenen
               niedrigen Fuenftel). Poolen vermengt die Fuenftel-Aussage
               dann mit der TAGESRATE.

Genau das erklaert den Befund aus N-45b: bei `amihud` laengs lieferte die
Tagesmischung als Kontrolle **+0,620** gegen einen echten Wert von +0,713.
Die Mischung innerhalb des Tages laesst die Tagesrate stehen - unter der
Tagesklammer faellt sie weg.

## Die Klammer

    abweichung(fuenftel) = Mittel ueber Tage von
                           [ rate(fuenftel, tag) - rate(alle, tag) ]
                           gewichtet mit der Ankerzahl

Ein Tag mit nur einem besetzten Fuenftel traegt 0 bei - richtig, denn er
sagt nichts darueber, welcher Wert an DIESEM Tag besser war.

⚠️ **Das ist keine Kopie von `quote_je_fuenftel`, sondern eine andere
Klammer** - `gepoolt` gegen `tag`. Beide werden nebeneinander berichtet,
damit der Unterschied sichtbar ist statt stillschweigend ersetzt.

## Was hier gemessen wird

Fuer jede Groesse, in BEIDEN Formen, unter BEIDEN Klammern:

    gepoolt    wie bisher - "an welchen Tagen tritt es auf"
    tag        die gueltige Klammer - "welcher Wert ist HEUTE besser"

⚠️ Erwartung vorab festgehalten: bei QUER sollten sich beide kaum
unterscheiden, bei LAENGS deutlich. Trifft das nicht zu, stimmt die
Diagnose oben nicht - und dann gilt die Erklaerung fuer N-45b nicht.

    python messe_fuenftel_mit_tagesklammer.py
"""
from __future__ import annotations

import sys
from collections import defaultdict

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import argparse                                             # noqa: E402
import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
from messe_stufen_aus_quote import quote_je_fuenftel        # noqa: E402
from pruefe_vola_zeitpunkt_oder_asset import (              # noqa: E402
    laengs_fuenftel, _als_reihen)

CRV = 2.0
VARIANTE = "ZIEL 2,0"
ARTEN = ("vola", "schnitt50", "amihud", "zufall")
MIND_TAGE = 200


def je_tag_und_fuenftel(zeilen, tage_je_sym, f5) -> dict:
    """{tag: {fuenftel: [treffer, n]}} - nur ENTSCHIEDENE Anker."""
    aus: dict = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for z in zeilen:
        tage = tage_je_sym.get(z["sym"])
        if not tage or z["i"] >= len(tage):
            continue
        tag = tage[z["i"]]
        f = (f5.get(tag) or {}).get(z["sym"])
        if f is None:
            continue
        w = z.get(VARIANTE)
        if w is None:
            continue
        if abs(w - CRV) < 1e-9:
            aus[tag][f][0] += 1
            aus[tag][f][1] += 1
        elif abs(w + 1.0) < 1e-9:
            aus[tag][f][1] += 1
    return aus


def abweichung_je_fuenftel(je_tag: dict) -> tuple[list, int, list]:
    """(abweichung, verwertbare Tage, standardfehler) - in Prozentpunkten.

    ⚠️ Ein Tag mit nur einem besetzten Fuenftel traegt 0 bei - er sagt
    nichts darueber, welcher Wert an DIESEM Tag besser war.
    """
    summe = [0.0] * 5
    gewicht = [0.0] * 5
    tage_gezaehlt = 0
    for _tag, je_f in je_tag.items():
        besetzt = [f for f in je_f if je_f[f][1] > 0]
        if len(besetzt) < 2:
            continue
        tr = sum(je_f[f][0] for f in besetzt)
        nn = sum(je_f[f][1] for f in besetzt)
        if nn <= 0:
            continue
        rate_tag = tr / nn
        tage_gezaehlt += 1
        for f in besetzt:
            n_f = je_f[f][1]
            summe[f] += n_f * (je_f[f][0] / n_f - rate_tag)
            gewicht[f] += n_f
    aus = [100.0 * summe[f] / gewicht[f] if gewicht[f] else float("nan")
           for f in range(5)]
    # ⚠️ DAS WERKZEUG WEIST SEINE EIGENE GENAUIGKEIT AUS (05.09.).
    #
    # Zweimal an einem Tag habe ich eine Annahmeschwelle GERATEN statt sie
    # herzuleiten - und beide Male fiel ein funktionierendes Verfahren
    # durch. Der Standardfehler einer Quote ist sqrt(q(1-q)/N), in Punkten
    # mal 100; N ist hier das Gewicht je Fuenftel. Wer die Spanne deuten
    # will, braucht diese Zahl daneben.
    fehler = [100.0 * (0.33 * 0.67 / gewicht[f]) ** 0.5 if gewicht[f] else
              float("nan") for f in range(5)]
    return aus, tage_gezaehlt, fehler


def _gepoolt(zeilen, tage_je_sym, f5) -> list:
    je = quote_je_fuenftel(zeilen, tage_je_sym, f5)
    if not je or any(je.get(f, (0, 0))[1] < 1 for f in range(5)):
        return [float("nan")] * 5
    ges_tr = sum(v[0] for v in je.values())
    ges_n = sum(v[1] for v in je.values())
    basis = ges_tr / ges_n
    return [100.0 * (je[f][0] / je[f][1] - basis) for f in range(5)]


def _spanne(w: list) -> float:
    g = [x for x in w if x == x]
    return max(g) - min(g) if len(g) == 5 else float("nan")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--arten", default=None)
    p.add_argument("--nur", default=None,
                   help="QUER oder LAENGS - Vorgabe: beide")
    a = p.parse_args()
    arten = ([x.strip() for x in a.arten.split(",")] if a.arten
             else list(ARTEN))
    if "zufall" not in arten:
        arten.append("zufall")
    formen = ((a.nur.upper(),) if a.nur else ("QUER", "LAENGS"))
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen" % (len(zeilen), len(reihen)))

    # ⚠️ Quellen nur laden, wo sie gebraucht werden.
    quellen = {}
    if any(x in ("funding", "funding_extrem") for x in arten):
        print("  lade funding ...", flush=True)
        fu = F.lade_funding()
        quellen["funding"] = fu
        quellen["funding_extrem"] = fu
    if "turnover" in arten:
        print("  lade turnover ...", flush=True)
        quellen["turnover"] = MB.reihe("data/onchain_historie.db", "splycur")
    gebaut = {}
    for art in arten:
        print("  baue %s ..." % art, flush=True)
        gebaut[art] = K.baue(reihen, art, quellen.get(art), horizont=20)

    for form in formen:
        print()
        print("=" * 92)
        print("%s — gepoolt gegen Tagesklammer" % form)
        print("=" * 92)
        print("  %-11s %-9s %-34s %8s" % ("Groesse", "Klammer",
                                          "Abweichung je Fuenftel (Punkte)",
                                          "Spanne"))
        for art in arten:
            if form == "QUER":
                f5 = _fuenftel_je_tag(gebaut[art])
            else:
                f5 = laengs_fuenftel(_als_reihen(gebaut[art], tage_je_sym),
                                     tage_je_sym)
            gp = _gepoolt(zeilen, tage_je_sym, f5)
            je_tag = je_tag_und_fuenftel(zeilen, tage_je_sym, f5)
            tg, n_tage, tg_fehler = abweichung_je_fuenftel(je_tag)
            if n_tage < MIND_TAGE:
                print("  %-11s zu wenige verwertbare Tage (%d)" % (art, n_tage))
                continue
            print("  %-11s %-9s %-34s %7.2f"
                  % (art, "gepoolt",
                     " ".join("%+5.2f" % x for x in gp), _spanne(gp)))
            gr = 2.0 * max(x for x in tg_fehler if x == x)
            print("  %-11s %-9s %-34s %7.2f   (%d Tage · Rauschen bis %.2f)"
                  % ("", "TAG",
                     " ".join("%+5.2f" % x for x in tg), _spanne(tg),
                     n_tage, gr))
            if _spanne(tg) <= gr:
                print("  %-11s %-9s -> Spanne im Rauschen, kein Befund"
                      % ("", ""))
        print()

    print("=" * 92)
    print("⚠️ LESEART — die Erwartung stand VOR dem Lauf im Kopf dieser Datei")
    print("=" * 92)
    print("  QUER   beide Klammern aehnlich   -> Diagnose bestaetigt, die")
    print("         Quer-Befunde aus F-217/F-221/F-222 bleiben gueltig")
    print("  LAENGS Tagesklammer deutlich kleiner -> die Laengs-Spannen")
    print("         (5,37 / 5,06 / 4,05) waren ein LAGE-Effekt, keine")
    print("         Aussage darueber, welcher Wert heute besser ist")
    print()
    print("  ⚠️ `zufall` muss unter BEIDEN Klammern bei null liegen.")
    print("     Tut es das nicht, misst das Verfahren einen Artefakt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
