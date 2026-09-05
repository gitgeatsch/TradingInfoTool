# -*- coding: utf-8 -*-
"""N-41c: die pruefbare VORHERSAGE aus N-41b (05.09.2026)

N-41b ergab, gegen beide Nullpunkte eingeordnet:

    FUNDING   +0,330 - echt, aber unter der 1-Punkt-Pflanzung (+0,420)
    TURNOVER  +0,020 - waehrend 2 Punkte bei diesem n mit +0,347 sichtbar
                       waeren. Ein ECHTER Nullbefund, kein untermaechtiger.

⚠️ Ein Nullbefund allein ist noch kein Grund, etwas zu entfernen. Er wird
erst zu einem, wenn die daraus folgende VORHERSAGE eintritt:

    Traegt turnover nichts Stabiles, darf sein WEGFALL die
    Out-of-sample-Steigung nicht senken.

Faellt die Steigung doch, trug turnover etwas, das die Blockstabilitaet
nicht erfasst - dann ist nicht turnover das Problem, sondern mein Mass.

## Die vier Varianten

    A  registrierte Stufen                  N-37, der Ausgangspunkt   +0,056
    B  beide aus der Quote gefittet         N-41                      +0,138
    C  nur funding aus der Quote            turnover auf null
    D  nur turnover aus der Quote           die Gegenprobe zu C

⚠️ D ist die eigentliche Kontrolle: waere C besser, weil "weniger Beitraege
immer besser", muesste D ebenfalls ueber B liegen. Tut es das nicht,
liegt es an turnover und nicht an der Zahl der Beitraege.

    python pruefe_turnover_weglassen.py
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
from messe_bewertung_kalibrierung import (                  # noqa: E402
    _fuenftel_je_tag, _steigung, baue_gruppen, _mit_stufen)
from messe_stufen_aus_quote import (                        # noqa: E402
    quote_je_fuenftel, stufen_aus_quote, _basis_gemessen)
from agent import wahrscheinlichkeit as W                   # noqa: E402

SAAT = 20260905
NULL = [0.0] * 5


def main() -> int:
    print("Lade Reihen...", flush=True)
    reihen = B.lade()
    tage_je_sym = {s: [z[0] for z in roh] for s, roh in reihen.items()}
    zeilen = ZR.ergebnisse(reihen)
    print("  %d Anker · %d Reihen" % (len(zeilen), len(reihen)))

    quellen = {"funding": F.lade_funding(),
               "turnover": MB.reihe("data/onchain_historie.db", "splycur")}
    f5 = {a: _fuenftel_je_tag(K.baue(reihen, a, quellen[a], horizont=20))
          for a in ("funding", "turnover")}
    alle = sorted(set(f5["funding"]) | set(f5["turnover"]))
    mitte = alle[len(alle) // 2]
    erste = {t for t in alle if t < mitte}
    zweite = {t for t in alle if t >= mitte}
    print("  SPLIT bei %s  (gefittet auf erste, geprueft auf zweite)" % mitte)

    # ⚠️ BEIDE BASEN FITTEN (05.09.) - weil sich herausstellte, dass die
    # Wahl der Basis das Ergebnis halbiert (+0,138 gegen +0,067). Ein
    # konstanter Versatz aller fuenf Stufen darf eine Regressionssteigung
    # nicht aendern. Tut er es doch, wirkt die Quote irgendwo nichtlinear -
    # und dann ist nicht die Basis das Thema, sondern diese Nichtlinearitaet.
    fit, fit_th = {}, {}
    for art in ("funding", "turnover"):
        je = quote_je_fuenftel(zeilen, tage_je_sym, f5[art], erste)
        fit[art] = stufen_aus_quote(je, _basis_gemessen(je)) or list(NULL)
        fit_th[art] = stufen_aus_quote(je, 1.0 / 3.0) or list(NULL)
        if fit[art] and fit_th[art]:
            d = [round(a - b, 3) for a, b in zip(fit_th[art], fit[art])]
            print("  %-9s Versatz Theorie-gemessen: %s  (konstant: %s)"
                  % (art, d, "ja" if max(d) - min(d) < 0.01 else "NEIN"))

    reg = {}
    for art in ("funding", "turnover"):
        reg[art] = next((b.stufen for b in W.BEITRAEGE
                         if b.merkmal == "%s_fuenftel" % art and b.stufen), NULL)

    varianten = (
        ("A  registriert                ", reg["funding"], reg["turnover"]),
        ("B  Quote, gemessene Basis     ", fit["funding"], fit["turnover"]),
        ("B* Quote, THEORIE-Basis (N-41)", fit_th["funding"], fit_th["turnover"]),
        ("C  NUR funding, gemessen      ", fit["funding"], NULL),
        ("C* NUR funding, Theorie       ", fit_th["funding"], NULL),
        ("D  NUR turnover, gemessen     ", NULL, fit["turnover"]),
    )

    print()
    print("=" * 92)
    print("OUT-OF-SAMPLE-STEIGUNG je Variante  (perfekt waere +0,333)")
    print("=" * 92)
    alt = W.BEITRAEGE
    try:
        for name, sf, st in varianten:
            W.BEITRAEGE = _mit_stufen(list(sf), list(st))
            rng = np.random.default_rng(SAAT)
            g = baue_gruppen(zeilen, tage_je_sym, f5["funding"], f5["turnover"],
                             nur_tage=zweite)
            print()
            print("  %s  (%d Stufen)" % (name, len(g)))
            _steigung(g, rng)
    finally:
        W.BEITRAEGE = alt

    print()
    print("  ⚠️ LESEART")
    print("     C >= B   turnover ist Ballast - der Wegfall kostet nichts")
    print("     C <  B   turnover traegt etwas, das die Blockstabilitaet")
    print("              nicht erfasst -> das MASS pruefen, nicht turnover")
    print("     D nahe 0 bestaetigt C: es liegt an turnover, nicht an der")
    print("              blossen Zahl der Beitraege")
    return 0


if __name__ == "__main__":
    sys.exit(main())
