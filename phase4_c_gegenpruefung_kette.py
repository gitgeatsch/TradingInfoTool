# -*- coding: utf-8 -*-
"""GEGENPRUEFUNG DER MESSKETTE - bevor irgendein Befund weiterverwendet wird.

⚠️⚠️ DIESE PRUEFUNG HAETTE AM ANFANG STEHEN MUESSEN. Alle Messungen vom
21.09.2026 speisen ihre Groessen ueber `art='turnover_markt'` ein - das
nimmt einen FERTIGEN Wert je Tag. Die registrierte Messung benutzt
`art='turnover'`, das `v[i] / menge` INTERN rechnet. Ob beide auf
IDENTISCHEN Eingaben dasselbe ergeben, war nie geprueft.

Stimmt es nicht, sitzt der ganze Tag auf einer anderen Groesse als
gedacht - und keiner der Befunde waere haltbar.

## Die vier Pruefungen

    1 BITGLEICHHEIT   `turnover_markt(V/S)` gegen `turnover(menge)` auf
                      DENSELBEN Daten. Muss Anker fuer Anker
                      uebereinstimmen
    2 ZUFALLSKONTROLLE eine Zufallsreihe durch DENSELBEN Pfad. Sie MUSS
                      stumm bleiben - traegt sie, ist der Pfad
                      kontaminiert (`zufallskontrolle-faengt-
                      kontamination`)
    3 ZERLEGUNG SUMMIERT  EIGENSCHAFT + LAGE muss den log-Umschlag
                      exakt wiedergeben. Eine Zerlegung, die nicht
                      summiert, ist keine
    4 FAMILIENFEHLER  wie viele Zellen wurden an diesem Tag gerechnet,
                      und wie hoch ist der familienweite Fehlalarm?
                      Ausweisen, nicht herausrechnen (`phase3_stufen.
                      familienfehler`)

⚠️ NUR LESEND.

    python phase4_c_gegenpruefung_kette.py
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import agent.marktrang as MR                               # noqa: E402
import messe_eigenschaft_beitrag as B                      # noqa: E402
import messe_kandidaten_als_regel as K                     # noqa: E402
import messnorm as N                                       # noqa: E402
import messnorm_auswahl as MA                              # noqa: E402
import phase3_stufen as ST                                 # noqa: E402
import phase4_c_hypothese_turnover as HY                   # noqa: E402
import phase4_c_kalibrierung_freefloat as C                # noqa: E402
from messe_beitrag_auf_auswahl import momentum250          # noqa: E402

SAAT = 20260921
# ⚠️ Gezaehlt, nicht geschaetzt: die Zellen dieses Tages.
ZELLEN_TAG = (("Kalibrierung 3 Arme x 3 H x 2 Zielgroessen", 18),
              ("Mengenleiter 5 x 3", 15),
              ("Stufentabelle 3 Arme x 3 H", 9),
              ("Zerlegung 4 Arme x 3 H", 12),
              ("Mitlaeufer 4 Zeilen x 3 H", 12),
              ("Normpfad 4 Arme x 3 H", 12))


def main() -> int:
    print("=" * 104)
    print("GEGENPRUEFUNG DER MESSKETTE")
    print("=" * 104)
    neu, _w, _g = C.menge_neu(C.MENGE_DB, True)
    datei, _sql = MR.MESSBASIS["schnitt"]
    log_u, ab = HY.reihen_umschlag(neu, datei)
    reihen = B.lade()

    # ---- 1  BITGLEICHHEIT -------------------------------------------
    print()
    print("-" * 104)
    print("  1) BITGLEICHHEIT - rechnet `turnover_markt(V/S)` dasselbe "
          "wie `turnover(menge)`?")
    print("-" * 104)
    # `turnover_markt` bekommt den fertigen Quotienten, NICHT den
    # Logarithmus - sonst waere es eine andere Groesse. Im Rang ist der
    # Logarithmus zwar aequivalent (monoton), aber das ist eine
    # BEHAUPTUNG und wird unten mitgeprueft.
    quot = {}
    for s, d in log_u.items():
        quot[s] = {t: math.exp(w) for t, w in d.items()}
    for H in (2, 3):
        a = K.baue(reihen, "turnover", neu, horizont=H)
        b = K.baue(reihen, "turnover_markt", quot, horizont=H)
        ta, tb = set(a), set(b)
        gemeinsam = sorted(ta & tb)
        n = abweich = 0
        groesste = 0.0
        for t in gemeinsam:
            ka = {x["sym"]: x["kennzahl"] for x in a[t]}
            kb = {x["sym"]: x["kennzahl"] for x in b[t]}
            for sym in set(ka) & set(kb):
                n += 1
                d = abs(ka[sym] - kb[sym]) / max(abs(ka[sym]), 1e-30)
                groesste = max(groesste, d)
                abweich += (d > 1e-9)
        print("     H%d: Tage %d gegen %d (gemeinsam %d) · %d Anker "
              "verglichen" % (H, len(ta), len(tb), len(gemeinsam), n))
        print("         Abweichungen ueber 1e-9: %d · groesste relative "
              "Abweichung %.3g  %s"
              % (abweich, groesste,
                 "✔ BITGLEICH" if abweich == 0 else "⚠️ NICHT GLEICH"))
        if ta != tb:
            print("         ⚠️ die TAGESMENGEN unterscheiden sich um %d "
                  "Tage - Ursache pruefen" % len(ta ^ tb))

    # ---- 1b  ist der LOGARITHMUS rangaequivalent? --------------------
    print()
    print("     1b) Der Logarithmus ist im RANG aequivalent - geprueft, "
          "nicht behauptet:")
    H = 3
    a = K.baue(reihen, "turnover_markt", quot, horizont=H)
    b = K.baue(reihen, "turnover_markt", log_u, horizont=H)
    import messe_regel_wirksamkeit as W
    schlecht = 0
    tage = sorted(set(a) & set(b))
    for t in tage:
        ka = [x["kennzahl"] for x in a[t]]
        kb = [x["kennzahl"] for x in b[t]]
        if len(ka) == len(kb):
            ra, rb = W.rang(ka), W.rang(kb)
            schlecht += int(np.max(np.abs(np.asarray(ra) -
                                          np.asarray(rb))) > 1e-12)
    print("         %d Tage geprueft · Tage mit abweichendem Rang: %d  %s"
          % (len(tage), schlecht,
             "✔ rangaequivalent" if schlecht == 0 else "⚠️ NICHT"))

    # ---- 2  ZUFALLSKONTROLLE ----------------------------------------
    print()
    print("-" * 104)
    print("  2) ZUFALLSKONTROLLE - eine Zufallsreihe durch DENSELBEN "
          "Pfad muss STUMM bleiben")
    print("-" * 104)
    rz = np.random.default_rng(SAAT + 4242)
    zufall = {s: {t: float(rz.random()) for t in d}
              for s, d in log_u.items()}
    mom = momentum250(reihen)
    lg = N.Lage(instrument="spot", strategie="einstieg")
    print("     %-14s %3s %6s %9s %20s %9s %7s  %s"
          % ("Reihe", "H", "Syms", "Wirkung", "Band", "Bezug", "Blöcke",
             "Urteil"))
    laut = 0
    for H in (2, 3, 5):
        je = C.beschneiden(
            K.baue(reihen, "turnover_markt", zufall, horizont=H), None, ab)
        if not je:
            continue
        try:
            bf = MA.pruefe_auswahl(
                "zufall", je, mom, lage=lg, menge="10%",
                rng=np.random.default_rng(SAAT), horizont=H,
                hypothese="Zufallskontrolle der Kette",
                verwendung="Beitrag", zielgroesse="bewegung_r")
        except Exception as exc:                           # noqa: BLE001
            print("     %-14s %3d -> %s" % ("zufall", H, str(exc)[:56]))
            continue
        still = bf.urteil.startswith("KEIN BEFUND") or not bf.traegt
        laut += (not still)
        print("     %-14s %3d %6d %+9.4f [%+.4f..%+.4f] %+9.4f %7d  %s"
              % ("zufall", H, bf.abdeckung_symbole, bf.wirkung, bf.unten,
                 bf.oben, bf.bezugswert, bf.n_bloecke, C.kurz(bf.urteil)))
    print("     ➤ %s" % ("✔ STUMM in allen Zellen - der Pfad ist nicht "
                         "kontaminiert" if not laut else
                         "⚠️⚠️ %d Zelle(n) TRAGEN - der Pfad ist "
                         "verdaechtig" % laut))

    # ---- 3  ZERLEGUNG SUMMIERT --------------------------------------
    print()
    print("-" * 104)
    print("  3) ZERLEGUNG - ergibt EIGENSCHAFT + LAGE wieder den "
          "log-Umschlag?")
    print("-" * 104)
    asset, lage = HY.zerlege(log_u, HY.RUECKBLICK)
    n = schlecht = 0
    groesste = 0.0
    for s in asset:
        for t, a_ in asset[s].items():
            l = lage.get(s, {}).get(t)
            o = log_u.get(s, {}).get(t)
            if l is None or o is None:
                continue
            n += 1
            d = abs((a_ + l) - o)
            groesste = max(groesste, d)
            schlecht += (d > 1e-10)
    print("     %d Punkte geprueft · Abweichungen ueber 1e-10: %d · "
          "groesste %.3g  %s"
          % (n, schlecht, groesste,
             "✔ die Zerlegung summiert exakt" if schlecht == 0
             else "⚠️ SIE SUMMIERT NICHT"))

    # ---- 4  FAMILIENFEHLER ------------------------------------------
    print()
    print("-" * 104)
    print("  4) FAMILIENFEHLER - wie viele Zellen wurden heute "
          "gerechnet?")
    print("-" * 104)
    ges = 0
    for name, n_ in ZELLEN_TAG:
        ges += n_
        print("     %-44s %4d" % (name, n_))
    print("     %-44s %4d" % ("SUMME (ohne Saat- und Mengenproben)", ges))
    print("     ➤ familienweiter Fehlalarm bei %d Zellen: %.0f %%"
          % (ges, 100 * ST.familienfehler(ges)))
    print("     ⚠️ AUSGEWIESEN, NICHT HERAUSGERECHNET. Genau deshalb "
          "wird nach FORM")
    print("        ueber benachbarte Horizonte geurteilt und nicht nach "
          "Einzelzellen -")
    print("        eine Einzelzelle ist bei dieser Zellenzahl praktisch "
          "wertlos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
