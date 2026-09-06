# -*- coding: utf-8 -*-
# ⛔⛔ UEBERHOLT AM 06.09.2026 — NICHT MEHR BENUTZEN
#
# Dieses Werkzeug misst auf der ZIELGROESSE "Ziel vor Stop" und/oder auf der
# FREIEN statt der SELEKTIERTEN Menge. Beides ist als falsch nachgewiesen:
#
#   Zielgroesse  `Konzept_Bewertungsstufe_29_08.md` Abschnitt 1, seit 23.08.:
#                "Wer 'Ziel vor Stop' misst, misst die eigene Zielregel
#                zurueck. Nicht der Markt war leer - das Mass war blind."
#
#   Menge        F-212 vom 04.09.: die Beitraege wirken auf 1,5 % der Anker.
#                Auf der selektierten Menge traegt funding DREIMAL staerker;
#                auf der freien liegt es bei -0,0003 R, also bei null.
#
# ⚠️ DIE RECHNUNGEN SIND KORREKT. Sie beantworten eine Frage, die laut
# eigener Dokumentation nichts ueber das Potential sagt. Wer sie erneut
# laufen laesst, bekommt wieder plausible Zahlen - und wieder die falschen.
#
# ERSATZ: `messnorm.py` (Methodik 2.110). Sie erzwingt Zielgroesse, Menge,
# Klammer, Kosten, Bootstrap und BEIDE Kontrollen - und lehnt sechs bekannte
# Irrwege ab, statt sie zu dokumentieren.
#
# Aufgehoben statt geloescht, weil die Herleitungen in den Docstrings die
# Fehler beschreiben, die dabei gefunden wurden (F-217 bis F-231).
#
"""N-50: Sind die beiden VERAENDERUNGSFORMEN unabhaengig? (05.09.2026)

## Warum das der naechste Schritt ist

N-49 hat zwei Formen gefunden, die ueber den MOMENT sprechen und damit den
Hebel treiben duerfen:

    amihud VERAENDERUNG      3,76 Punkte · 6,4x ueber dem Nullpunkt
    schnitt50 VERAENDERUNG   2,66 Punkte · 5,7x

⚠️ **Zwei Formen, die einzeln tragen, koennen zusammen EINE sein.** Im
NIVEAU waren amihud und schnitt50 unabhaengig (-0,08) - das sagt aber
nichts ueber ihre VERAENDERUNGEN. Eine Illiquiditaetsaenderung und eine
Schnittabstandsaenderung koennen dieselbe Kursbewegung abbilden.

⚠️ **Und eine zweite Kopplung ist zu pruefen, die im Niveau gar nicht
auftreten kann:** haengt die VERAENDERUNG von amihud an seinem eigenen
NIVEAU? Waere das so, zaehlte die Bewertung dasselbe Urteil zweimal - und
das Niveau ist die Groesse, die laut F-227 gerade NICHT den Hebel treiben
soll.

## Drei Messungen

    1  UEBERLAPPUNG   Korrelation der Fuenftel, paarweise, als Matrix

    2  BEDINGT        Ordnet amihud-VERAENDERUNG die Barrierenquote noch
                      INNERHALB eines festen schnitt50-VERAENDERUNGS-
                      Fuenftels? Und innerhalb eines festen amihud-NIVEAU-
                      Fuenftels?

    3  DER NULLPUNKT DAZU
                      ⚠️ Bedingen verkleinert n, also WAECHST der
                      Nullpunkt. Die Kunstgroesse laeuft durch dieselbe
                      Bedingung - sonst waere jede bedingte Spanne
                      gegen eine zu freundliche Grenze gelesen.

## Die Leseart

    amihud-VER traegt bedingt auf beides    -> zwei eigenstaendige Beitraege
    bricht bei schnitt50-VER ein            -> eine Familie, EINE waehlen
    bricht bei amihud-NIVEAU ein            -> die Veraenderung ist nur eine
                                               Faerbung des Niveaus und
                                               taugt nicht fuer den Hebel

    python pruefe_veraenderungsformen_unabhaengig.py
"""
from __future__ import annotations

import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_funding_niveau as F                            # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messe_zielregel as ZR                                # noqa: E402
from messe_bewertung_kalibrierung import _fuenftel_je_tag   # noqa: E402
# ⚠️ ALLES IMPORTIERT, NICHTS NACHGEBAUT.
from messe_fuenftel_mit_tagesklammer import (               # noqa: E402
    je_tag_und_fuenftel, abweichung_je_fuenftel, _spanne)
from messe_form_und_nullpunktkurve import (                 # noqa: E402
    veraenderung_quer, DIFFERENZ_TAGE)
from pruefe_persistenz_und_nullpunkt import (               # noqa: E402
    persistenz, kunst_fuenftel)

ZIEHUNGEN = 5


def _spanne_von(zeilen, tage_je_sym, f5) -> float:
    tg, _n, _f = abweichung_je_fuenftel(
        je_tag_und_fuenftel(zeilen, tage_je_sym, f5))
    return _spanne(tg)


def bedingt(f5_ziel: dict, f5_bed: dict, g: int) -> dict:
    """Nur die Anker, die im bedingenden Fuenftel `g` liegen."""
    aus = {}
    for tag, d in f5_ziel.items():
        db = f5_bed.get(tag) or {}
        treffer = {s: v for s, v in d.items() if db.get(s) == g}
        if len(treffer) >= 5:
            aus[tag] = treffer
    return aus


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen" % (len(zeilen), len(reihen)))
    print("  lade funding ...", flush=True)
    fu = F.lade_funding()

    roh = {}
    for art in ("amihud", "schnitt50", "vola"):
        print("  baue %s ..." % art, flush=True)
        roh[art] = K.baue(reihen, art, None, horizont=20)
    roh["funding"] = K.baue(reihen, "funding", fu, horizont=20)

    formen = {
        "amihud VER": veraenderung_quer(roh["amihud"], tage_je_sym, DIFFERENZ_TAGE),
        "schn50 VER": veraenderung_quer(roh["schnitt50"], tage_je_sym, DIFFERENZ_TAGE),
        "vola VER": veraenderung_quer(roh["vola"], tage_je_sym, DIFFERENZ_TAGE),
        "amihud NIV": _fuenftel_je_tag(roh["amihud"]),
        "funding NIV": _fuenftel_je_tag(roh["funding"]),
    }

    # ---- 1. Ueberlappungsmatrix -------------------------------------
    namen = list(formen)
    print()
    print("=" * 96)
    print("1. UEBERLAPPUNG der Fuenftel")
    print("=" * 96)
    print("  %-12s %s" % ("", " ".join("%11s" % n for n in namen)))
    for a in namen:
        zeile = []
        for b in namen:
            if a == b:
                zeile.append("          -")
                continue
            xs, ys = [], []
            for tag, da in formen[a].items():
                db = formen[b].get(tag)
                if not db:
                    continue
                for sym, v in da.items():
                    w = db.get(sym)
                    if w is not None:
                        xs.append(v)
                        ys.append(w)
            zeile.append("          ." if len(xs) < 1000 else
                         "%11.3f" % float(np.corrcoef(np.array(xs, float),
                                                      np.array(ys, float))[0, 1]))
        print("  %-12s %s" % (a, " ".join(zeile)))
    print()
    print("  ⚠️ |r| ueber 0,35 heisst: die beiden messen weitgehend dasselbe.")

    # ---- 2./3. Bedingt, mit passendem Nullpunkt ---------------------
    # ⚠️ JEDE VERAENDERUNG GEGEN IHR EIGENES NIVEAU (05.09., nachgezogen).
    #
    # Der erste Lauf prueft nur amihud VER gegen amihud NIV - und dort fiel
    # sie durch (0,7x). Genau diese Pruefung fehlte fuer schnitt50 und vola:
    # ohne sie waere "schnitt50 VER traegt" auf demselben Weg falsch, auf dem
    # "amihud VER traegt" falsch war.
    paare = [("amihud VER", "schn50 VER"),
             ("amihud VER", "amihud NIV"),
             ("schn50 VER", "schn50 NIV"),
             ("vola VER", "vola NIV")]
    formen["schn50 NIV"] = _fuenftel_je_tag(roh["schnitt50"])
    formen["vola NIV"] = _fuenftel_je_tag(roh["vola"])
    for ziel, bed in paare:
        print()
        print("=" * 96)
        print("2. BEDINGT — traegt %s noch INNERHALB eines festen %s-Fuenftels?"
              % (ziel, bed))
        print("=" * 96)
        echte, kunst = [], []
        for g in range(5):
            fz = bedingt(formen[ziel], formen[bed], g)
            if len(fz) < 200:
                print("    Fuenftel %d: zu wenige Tage (%d)" % (g, len(fz)))
                continue
            sp = _spanne_von(zeilen, tage_je_sym, fz)
            echte.append(sp)
            # ⚠️ DER NULLPUNKT DURCHLAEUFT DIESELBE BEDINGUNG.
            # Bedingen verkleinert n, also waechst der Nullpunkt. Die
            # Kunstgroesse bekommt dieselbe Blocklaenge wie die Persistenz
            # der Zielform und wird genauso bedingt.
            kk = []
            for z in range(ZIEHUNGEN):
                kf = kunst_fuenftel(roh["amihud"], 5, salz=z)
                kb = bedingt(kf, formen[bed], g)
                if len(kb) >= 200:
                    kk.append(_spanne_von(zeilen, tage_je_sym, kb))
            null = float(np.max(kk)) if kk else float("nan")
            kunst.append(null)
            print("    %s-Fuenftel %d: Spanne %5.2f · Nullpunkt %5.2f · %4.1fx"
                  % (bed, g, sp, null, sp / null if null > 0 else float("nan")))
        if echte and kunst:
            m, n0 = float(np.mean(echte)), float(np.mean(kunst))
            print()
            print("    Mittel: Spanne %.2f gegen Nullpunkt %.2f  ->  %.1fx  %s"
                  % (m, n0, m / n0 if n0 > 0 else float("nan"),
                     "traegt bedingt" if n0 > 0 and m / n0 > 2.0
                     else "⚠️ traegt bedingt NICHT"))

    print()
    print("  Persistenz zur Einordnung:")
    for n in namen:
        print("    %-12s %5.1f %%" % (n, 100 * persistenz(formen[n], tage_je_sym)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
