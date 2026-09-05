# -*- coding: utf-8 -*-
"""N-51b: das Blockraster fuellen und die Nullpunkte neu ziehen (06.09.2026)

## Der Fehler, den die Vorabkriterien gefunden haben

Vor N-51 stand als viertes Kriterium: *„`funding` und `turnover` muessen
einen GROESSEREN Nullpunkt bekommen als die kursbasierten"* — sie sind
duenner gedeckt, also verrauschter. Gemessen:

    turnover   65 Symbole   Nullpunkt 1.85   ✔ deutlich groesser
    funding   287 Symbole   Nullpunkt 0.31   ✖ KLEINER als die 0.46
                                               der breiten Arten

## Die Ursache: das Blockraster ist in der Mitte zu grob

Die Persistenz einer Kunstgroesse mit Blocklaenge b ist rechnerisch

    p(b) = 1 - (4/5) / b

    b=1 -> 20 %    b=5  -> 84 %    b=20 -> 96 %
    b=2 -> 60 %    b=3  -> 73 %

Zwischen b=1 und b=5 klafft eine Luecke von **64 Punkten**, und beide
duenn gedeckten Groessen fallen hinein:

    funding   47,9 %  -> auf b=1 (20 %) geschnappt   Nullpunkt ZU KLEIN
    turnover  65,9 %  -> auf b=5 (84 %) geschnappt   Nullpunkt ZU GROSS

Sie landen an entgegengesetzten Enden derselben Luecke.

## Zwei Korrekturen

    1  RASTER FUELLEN   b=2 und b=3 ergaenzen -> 60 % und 73 %
    2  INTERPOLIEREN    statt auf den naechsten Block zu schnappen, wird
                        zwischen den beiden Nachbarn linear interpoliert

⚠️ **Die Spannen werden NICHT neu gemessen** - sie stehen aus N-51 und
haengen nicht vom Nullpunkt ab. Neu gezogen wird nur die Nulllinie. Das
spart den teuren Teil und aendert am Zaehler nichts.

    python rechne_nullpunkte_feiner.py
"""
from __future__ import annotations

import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_bewertungskennzahl as MB                       # noqa: E402
import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
from messe_fuenftel_mit_tagesklammer import (               # noqa: E402
    je_tag_und_fuenftel, abweichung_je_fuenftel, _spanne)
from messe_form_und_nullpunktkurve import (                 # noqa: E402
    veraenderung_quer, DIFFERENZ_TAGE)
from pruefe_persistenz_und_nullpunkt import (               # noqa: E402
    persistenz, kunst_fuenftel)

ZIEHUNGEN = 5
BLOECKE = (1, 2, 3, 5, 20, 60, 250, None)

# Die SPANNEN aus N-51 - gemessen, unabhaengig vom Nullpunkt.
SPANNEN = {
    ("amihud", "NIVEAU"): 6.51, ("amihud", "VERAEND"): 3.76,
    ("vola", "NIVEAU"): 3.77, ("vola", "VERAEND"): 1.12,
    ("schnitt", "NIVEAU"): 4.56, ("schnitt", "VERAEND"): 3.14,
    ("schnitt50", "NIVEAU"): 4.20, ("schnitt50", "VERAEND"): 2.66,
    ("rsi", "NIVEAU"): 2.81, ("rsi", "VERAEND"): 1.92,
    ("momentum", "NIVEAU"): 2.36, ("momentum", "VERAEND"): 2.66,
    ("momentum_kurz", "NIVEAU"): 2.71, ("momentum_kurz", "VERAEND"): 2.39,
    ("zufall", "NIVEAU"): 0.19, ("zufall", "VERAEND"): 0.22,
    ("funding", "NIVEAU"): 1.08, ("funding", "VERAEND"): 0.41,
    ("funding_extrem", "NIVEAU"): 0.87, ("funding_extrem", "VERAEND"): 0.21,
    ("turnover", "NIVEAU"): 2.83, ("turnover", "VERAEND"): 0.80,
    ("oi_aenderung", "NIVEAU"): 1.18, ("oi_aenderung", "VERAEND"): 1.16,
    ("long_bias", "NIVEAU"): 0.92, ("long_bias", "VERAEND"): 1.28,
    ("top_bias", "NIVEAU"): 0.76, ("top_bias", "VERAEND"): 1.32,
    ("taker_bias", "NIVEAU"): 0.89, ("taker_bias", "VERAEND"): 0.78,
}

AUS_KURSDATEN = ("amihud", "vola", "schnitt", "schnitt50", "rsi",
                 "momentum", "momentum_kurz", "zufall")
AUS_TERMIN = ("oi_aenderung", "long_bias", "top_bias", "taker_bias")


def kurve_fuer(gebaut, zeilen, tage_je_sym) -> list:
    """[(persistenz, nullpunkt)] auf DIESER Struktur, feines Raster."""
    aus = []
    for b in BLOECKE:
        sp, pe = [], []
        for z in range(ZIEHUNGEN):
            kf = kunst_fuenftel(gebaut, b, salz=z)
            if not kf:
                continue
            pe.append(persistenz(kf, tage_je_sym))
            tg, _n, _f = abweichung_je_fuenftel(
                je_tag_und_fuenftel(zeilen, tage_je_sym, kf))
            s = _spanne(tg)
            if s == s:
                sp.append(s)
        if sp:
            aus.append((float(np.mean(pe)), float(np.max(sp))))
    aus.sort()
    return aus


def interpoliere(kurve: list, p: float) -> float:
    """Linear zwischen den beiden Nachbarn - nicht auf den naechsten
    Block schnappen.

    ⚠️ Genau das Schnappen hat funding auf b=1 (20 %) und turnover auf
    b=5 (84 %) geworfen, obwohl beide bei 48 % bzw. 66 % liegen.
    """
    if not kurve:
        return float("nan")
    if p <= kurve[0][0]:
        return kurve[0][1]
    if p >= kurve[-1][0]:
        return kurve[-1][1]
    for (p0, n0), (p1, n1) in zip(kurve, kurve[1:]):
        if p0 <= p <= p1:
            if p1 - p0 < 1e-9:
                return max(n0, n1)
            t = (p - p0) / (p1 - p0)
            return n0 + t * (n1 - n0)
    return kurve[-1][1]


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen" % (len(zeilen), len(reihen)), flush=True)

    quelle = {}
    print("  lade funding ...", flush=True)
    fu = F.lade_funding()
    quelle["funding"] = quelle["funding_extrem"] = fu
    print("  lade turnover ...", flush=True)
    quelle["turnover"] = MB.reihe("data/onchain_historie.db", "splycur")
    print("  lade terminmarkt ...", flush=True)
    tm = K.lade_terminmarkt()
    for a in AUS_TERMIN:
        if a in tm:
            quelle[a] = tm[a]

    arten = list(AUS_KURSDATEN) + ["funding", "funding_extrem", "turnover"] \
        + [a for a in AUS_TERMIN if a in quelle]

    print()
    print("=" * 104)
    print("NULLPUNKTE NEU — feines Raster, interpoliert, je EIGENER Struktur")
    print("=" * 104)
    print("  %-15s %-8s %6s %7s %7s %8s %8s %s"
          % ("Groesse", "Form", "Spanne", "Pers.", "Null neu", "alt", "Verh.", ""))

    # ⚠️ EINE KURVE JE STRUKTUR, NICHT JE ART (06.09., vor dem Lauf).
    #
    # Acht Bloecke x fuenf Ziehungen x fuenfzehn Arten waeren 600
    # Barrierendurchlaeufe - Stunden. Die acht kursbasierten Arten teilen
    # sich aber DIESELBE Struktur (516 Symbole, dieselben Tage); dort ist
    # die Kurve identisch. Geschluesselt wird nach (Symbolzahl, Tagezahl),
    # grob gerundet, damit nahe beieinander liegende Arten sich eine Kurve
    # teilen.
    kurven, gebaut_je_art = {}, {}
    for art in arten:
        gebaut_je_art[art] = K.baue(reihen, art, quelle.get(art), horizont=20)
    for art in arten:
        g = gebaut_je_art[art]
        syms = len({e["sym"] for liste in g.values() for e in liste})
        schluessel = (round(syms / 25.0), round(len(g) / 100.0))
        if schluessel not in kurven:
            print("  ziehe Kurve fuer %d Symbole / %d Tage (%s) ..."
                  % (syms, len(g), art), flush=True)
            kurven[schluessel] = kurve_fuer(g, zeilen, tage_je_sym)
        kurven[art] = kurven[schluessel]

    for art in arten:
        gebaut = gebaut_je_art[art]
        kurve = kurven[art]
        for form, f5 in (("NIVEAU", _fuenftel_je_tag(gebaut)),
                         ("VERAEND", veraenderung_quer(gebaut, tage_je_sym,
                                                       DIFFERENZ_TAGE))):
            if not f5 or (art, form) not in SPANNEN:
                continue
            p = persistenz(f5, tage_je_sym)
            sp = SPANNEN[(art, form)]
            null = interpoliere(kurve, p)
            v = sp / null if null > 0 else float("nan")
            print("  %-15s %-8s %6.2f %6.1f%% %7.2f %8s %7.1fx %s"
                  % (art, form, sp, 100 * p, null, "-", v,
                     "" if v > 2.5 else "<- traegt nicht"))
        print("    Kurve: %s" % " ".join(
            "%.0f%%:%.2f" % (100 * a, b) for a, b in kurve))
    print()
    print("  ⚠️ Die SPANNEN stammen unveraendert aus N-51 - nur die")
    print("     Nulllinie wurde neu gezogen. Der Zaehler ist derselbe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
