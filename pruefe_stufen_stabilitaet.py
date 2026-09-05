# -*- coding: utf-8 -*-
"""N-41b: HAELT die Fuenftel-Ordnung? - gegen einen echten Nullpunkt (05.09.2026)

## Warum diese Gegenpruefung

N-41 fand out-of-sample:

    Steigung +0,138 statt +0,056  ->  der Umrechnungsfehler war real
    ABER: gleiche Rangplaetze 2 von 5 (funding) bzw. 1 von 5 (turnover)
          -> "die Ordnung haelt NICHT"

⚠️ **Diese zweite Aussage darf so nicht stehenbleiben - aus drei Gruenden:**

1 EINE ZIEHUNG IST KEIN NULLPUNKT. Ein einziger chronologischer Split bei
  2022-11-08 trennt zwei Marktregime. Ob die Ordnung "nicht haelt" oder ob
  das Regime gewechselt hat, kann eine Ziehung nicht unterscheiden.

2 DAS MASS WAR ZU GROB. "gleiche Rangplaetze" bei 5 Positionen hat den
  Erwartungswert 1,0 unter reinem Zufall. Turnover mit 1 von 5 lag damit
  exakt auf dem Zufallswert - aber Funding mit 2 von 5 auch nur knapp
  darueber. Das Mass kann Ordnung von Zufall gar nicht trennen.

3 KEIN NULLPUNKT VORHANDEN. Ohne zu wissen, wie stabil eine ECHTE Ordnung
  bei dieser Stichprobe waere und wie instabil reiner Zufall ist, ist
  "haelt nicht" keine Messung, sondern ein Eindruck.

## Was hier gemacht wird

    Rangkorrelation (Spearman) statt Rangplatzgleichheit
    MEHRERE Bloecke statt eines Splits, alle Paare
    ZUFALLSKONTROLLE  gemischte Fuenftel -> der untere Nullpunkt
    POSITIVKONTROLLE  gepflanzte feste Ordnung -> der obere Nullpunkt

Erst zwischen diesen beiden Punkten laesst sich der echte Wert einordnen.

    python pruefe_stufen_stabilitaet.py [--bloecke 6]
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from itertools import combinations

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
from messe_stufen_aus_quote import (                        # noqa: E402
    quote_je_fuenftel, stufen_aus_quote, _basis_gemessen, MIND_JE_FUENFTEL)

SAAT = 20260905


def spearman5(a: list, b: list) -> float:
    """Rangkorrelation ueber 5 Punkte. -1 = gedreht, +1 = identisch."""
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    return float(np.corrcoef(ra, rb)[0, 1])


def stufen_je_block(zeilen, tage_je_sym, f5, bloecke: list) -> list:
    """Je Block: die Stufen gegen die BLOCKEIGENE Basisrate.

    ⚠️ Blockeigene Basis, nicht global - sonst misst man das Regime-Niveau
    mit, nicht die Spreizung. Genau der Fehler, der in N-41 den Eindruck
    "haelt nicht" mit erzeugt haben kann.
    """
    aus = []
    for tage in bloecke:
        je = quote_je_fuenftel(zeilen, tage_je_sym, f5, tage)
        st = stufen_aus_quote(je, _basis_gemessen(je))
        n = min((je.get(f, (0, 0))[1] for f in range(5)), default=0)
        aus.append((st, n))
    return aus


def bewerte(name: str, je_block: list) -> float | None:
    gueltig = [(s, n) for s, n in je_block if s]
    if len(gueltig) < 2:
        print("  %-14s zu wenige gueltige Bloecke" % name)
        return None
    rs = [spearman5(a, b) for (a, _), (b, _) in combinations(gueltig, 2)]
    m = float(np.mean(rs))
    print("  %-14s %d Bloecke · n_min je Zelle %6d · Spearman Mittel %+.3f"
          "  [%+.2f .. %+.2f]"
          % (name, len(gueltig), min(n for _, n in gueltig), m, min(rs), max(rs)))
    return m


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--bloecke", type=int, default=6)
    a = p.parse_args()

    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    print("Barrieren-Ausgaenge...", flush=True)
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen" % (len(zeilen), len(reihen)))

    quellen = {"funding": F.lade_funding(),
               "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    f5 = {art: _fuenftel_je_tag(K.baue(reihen, art, quellen[art], horizont=20))
          for art in ("funding", "turnover")}

    alle = sorted(set(f5["funding"]) | set(f5["turnover"]))
    gr = len(alle) // a.bloecke
    bloecke = [set(alle[i * gr:(i + 1) * gr]) for i in range(a.bloecke)]
    print("  %d Bloecke a ~%d Tage · %s .. %s"
          % (a.bloecke, gr, alle[0], alle[-1]))
    print("  ⚠️ Mindestens %d entschiedene Anker je Fuenftel und Block noetig"
          % MIND_JE_FUENFTEL)

    rng = np.random.default_rng(SAAT)
    for art in ("funding", "turnover"):
        print()
        print("=" * 92)
        print("%s — haelt die Ordnung ueber die Bloecke?" % art.upper())
        print("=" * 92)

        echt = bewerte("ECHT", stufen_je_block(zeilen, tage_je_sym, f5[art], bloecke))

        # ---- UNTERER NULLPUNKT: Fuenftel je Tag gemischt -------------
        # ⚠️ Innerhalb des Tages mischen, nicht global - die Tagesklammer
        #    bleibt erhalten, nur die Zuordnung Symbol->Fuenftel faellt.
        misch = {}
        for tag, d in f5[art].items():
            syms = list(d)
            werte = list(d.values())
            rng.shuffle(werte)
            misch[tag] = dict(zip(syms, werte))
        zufall = bewerte("ZUFALL", stufen_je_block(zeilen, tage_je_sym, misch, bloecke))

        # ---- OBERER NULLPUNKT: feste Ordnung gepflanzt ---------------
        # ⚠️ Die Fuenftel bleiben, aber der AUSGANG wird an das Fuenftel
        #    gekoppelt - so sieht maximal stabile Ordnung bei DIESEM n aus.
        # ⚠️ SPANNENREIHE STATT EINER PFLANZUNG (05.09., eigener Mangel).
        #
        # Die erste Fassung pflanzte 10 Punkte Spanne - die ECHTEN Spannen
        # liegen bei 2-4. Damit prueft die Kontrolle nur, ob eine STARKE
        # Ordnung erkennbar ist, und beantwortet die eigentliche Frage
        # nicht: ist eine Ordnung von der GEMESSENEN Groesse ueberhaupt
        # ueber die Bloecke nachweisbar? Ohne das ist ein Nullbefund
        # nicht von Untermaechtigkeit zu unterscheiden (Methodik 2.88).
        positiv = None
        for spanne in (1.0, 2.0, 4.0, 10.0):
            h = spanne / 100.0 / 4.0
            wahr = {f: 1.0 / 3.0 + (2 - f) * h for f in range(5)}
            r2 = np.random.default_rng(SAAT + 1)
            gepflanzt = []
            for z in zeilen:
                tage = tage_je_sym.get(z["sym"])
                if not tage or z["i"] >= len(tage):
                    continue
                f = (f5[art].get(tage[z["i"]]) or {}).get(z["sym"])
                if f is None:
                    continue
                gepflanzt.append({"sym": z["sym"], "i": z["i"],
                                  "ZIEL 2,0": (2.0 if r2.random() < wahr[f] else -1.0)})
            w = bewerte("GEPFLANZT %4.1f Pkt" % spanne,
                        stufen_je_block(gepflanzt, tage_je_sym, f5[art], bloecke))
            if abs(spanne - 10.0) < 1e-9:
                positiv = w

        print()
        if echt is None or zufall is None or positiv is None:
            print("  -> nicht einordenbar")
            continue
        spanne = positiv - zufall
        anteil = (echt - zufall) / spanne if spanne > 0.05 else None
        print("  EINORDNUNG   Zufall %+.3f  <  ECHT %+.3f  <  gepflanzt %+.3f"
              % (zufall, echt, positiv))
        if anteil is None:
            print("  ⚠️ Die Kontrollen trennen nicht - das Mass taugt hier nicht")
        else:
            print("  -> die echte Ordnung erreicht %.0f %% der pflanzbaren Stabilitaet"
                  % (100 * anteil))
            print("  -> %s" % ("die Ordnung HAELT" if anteil > 0.5 else
                               "die Ordnung haelt TEILWEISE" if anteil > 0.2 else
                               "⚠️ die Ordnung haelt NICHT - nicht vom Zufall trennbar"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
