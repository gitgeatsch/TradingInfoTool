# -*- coding: utf-8 -*-
"""KIPPT DAS URTEIL MIT DER SAAT? - Saatprobe auf den tragenden Zellen.

⚠️⚠️ WARUM SIE PFLICHT IST. Der Lauf vom 21.09.2026
(`phase4_c_kalibrierung_freefloat --alle-mengen`) fand SECHS tragende
Zellen fuer `umschlag_frei` auf `bewegung_r`. Die Abstaende zum Nullpunkt
sind winzig - bei H2/50 Prozent sind es 0,0009 R.

Genau diese Lage steht in 2.477-stabilitaet: dort fielen ZWEI
TRAEGT-Urteile mit Abstaenden von 0,0006 und 0,0003 R an der Saatprobe.
Ein Urteil, das mit der Saat kippt, ist kein Urteil.

## ⚠️⚠️⚠️ ZWEI ZUFALLSQUELLEN, UND NUR EINE IST OFFENSICHTLICH

    --saat       geht in den BOOTSTRAP (`urteil_tage` zieht damit)
    --nullsaat   geht in die 40 NULLWELTEN (`messnorm.SAAT`)

Bis zum 21.09. erreichte die uebliche Saatprobe nur die erste
(2.505-fenster-engpass). Eine Probe, die nur den Bootstrap dreht, laesst
den halben Zufall unberuehrt und sieht stabiler aus, als die Lage ist.
**Hier werden beide gedreht, getrennt ausgewiesen.**

## Vorab festgelegt

| Ergebnis je Zelle | Deutung |
|---|---|
| TRAEGT bei **allen** Saaten | ✔ stabil |
| TRAEGT bei **einigen** | ✖ **kippt** - das Urteil faellt |
| TRAEGT bei **keiner** ausser der Ausgangssaat | ✖ Artefakt der Saat |

⚠️ Die Zellen werden NICHT neu gesucht. Geprueft werden genau die sechs,
die der Hauptlauf gemeldet hat - alles andere waere Suchpreis.

⚠️ NUR LESEND, keine Netzabrufe, keine Standard-DB.
"""
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.chdir("D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")
sys.path.insert(0, "D:/CLAUDE_Projects/SoftwareProjekte/TradingInfoTool")

import numpy as np                                          # noqa: E402

import messe_eigenschaft_beitrag as B                       # noqa: E402
import messe_kandidaten_als_regel as K                      # noqa: E402
import messnorm as N                                        # noqa: E402
import messnorm_auswahl as MA                               # noqa: E402
import phase4_c_kalibrierung_freefloat as KF                # noqa: E402

# ⚠️ GENAU DIE ZELLEN AUS DEM HAUPTLAUF, nicht neu gesucht.
# ⚠️⚠️ UMGESTELLT AUF DIE NAEHERUNG (21.09.2026). Die
# Zellen stammen aus `phase4_c_naeherung_konstante_menge`: auf H5
# traegt sie auf ALLEN fuenf zulaessigen Mengen - genau das ist zu
# pruefen, denn dort ist die Vorabfestlegung erfuellt.
ZELLEN = ((5, "5%"), (5, "10%"), (5, "20%"),
          (5, "50%"), (5, "frei"))
NAEHERUNG = True
BOOT_SAATEN = (20260921, 1, 7, 99, 4242)
NULL_SAATEN = (20260921, 5, 77, 31415)
ZIEL = "bewegung_r"


def main() -> int:
    t0 = time.time()
    print("=" * 108)
    print("SAATPROBE AUF DEN TRAGENDEN ZELLEN - `umschlag_frei`, "
          "Zielgroesse %s" % ZIEL)
    print("=" * 108)
    print("  " + N.standardzeile())
    print()
    print("  ⚠️ Geprueft werden GENAU die %d Zellen aus dem Hauptlauf."
          % len(ZELLEN))
    print("     Neue zu suchen waere Suchpreis (2.208-n86).")
    print()

    if NAEHERUNG:
        import phase4_c_naeherung_konstante_menge as _NK
        _reihen0 = B.lade()
        _h, _r = _NK.mengen_heute()
        _um = _NK.umstellungen(_reihen0)
        neu = dict()
        for _s, _m in _h.items():
            if _s in _um:
                continue
            _z = _reihen0.get(_s)
            if _z:
                neu[_s] = dict((str(_x[0])[:10], _m) for _x in _z)
    else:
        neu, _weg, _ges = KF.menge_neu(KF.MENGE_DB, True)
    tage = sorted({t for d in neu.values() for t in d})
    import phase4_c_naeherung_konstante_menge as _NK2
    ab = _NK2.AB if NAEHERUNG else (tage[0] if tage else "2025-01-01")
    reihen = B.lade()
    mom = KF.momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")

    # ⚠️ Die Ankerdaten je Horizont EINMAL bauen - nicht je Saat.
    # Der Zufall steckt im Bootstrap und in den Nullwelten, nicht in
    # den Daten; sie neu zu bauen waere reine Rechenzeit.
    welten = {}
    for H in sorted({h for h, _m in ZELLEN}):
        KF._SPEICHER.clear()
        je0 = K.baue(reihen, "turnover", neu, horizont=H)
        welten[H] = KF.beschneiden(je0, None, ab)
        print("  H%-3d %5d Ankertage geladen" % (H, len(welten[H])))
    print()

    kopf = ("  %-12s %-10s %11s %22s %9s  %s"
            % ("Zelle", "Saatart", "Wirkung", "Band", "Bezug", "Urteil"))
    schlecht = []
    for H, menge in ZELLEN:
        print("-" * 108)
        print("  ZELLE H%d / %s" % (H, menge))
        print(kopf)
        traegt_boot, traegt_null = [], []
        for art, saaten in (("Bootstrap", BOOT_SAATEN),
                            ("Nullwelt", NULL_SAATEN)):
            for s in saaten:
                alt_saat = N.SAAT
                try:
                    if art == "Nullwelt":
                        N.SAAT = s
                        rng = np.random.default_rng(BOOT_SAATEN[0])
                    else:
                        rng = np.random.default_rng(s)
                    b = MA.pruefe_auswahl(
                        "turnover", welten[H], mom, lage=lage, menge=menge,
                        rng=rng, horizont=H,
                        hypothese="C Saatprobe Free Float",
                        verwendung="Beitrag", zielgroesse=ZIEL)
                finally:
                    N.SAAT = alt_saat
                (traegt_boot if art == "Bootstrap"
                 else traegt_null).append(bool(b.traegt))
                print("  %-12s %-10d %+11.4f [%+9.4f..%+9.4f] %+9.4f  %s"
                      % ("", s, b.wirkung, b.unten, b.oben, b.bezugswert,
                         KF.kurz(b.urteil)))
        nb, nn = sum(traegt_boot), sum(traegt_null)
        stabil = (nb == len(traegt_boot) and nn == len(traegt_null))
        if not stabil:
            schlecht.append((H, menge, nb, nn))
        print("  ➤ H%d/%-6s Bootstrap %d von %d · Nullwelt %d von %d   %s"
              % (H, menge, nb, len(traegt_boot), nn, len(traegt_null),
                 "✔ STABIL" if stabil else "⛔ KIPPT - das Urteil faellt"))
        print()

    print("=" * 108)
    if schlecht:
        print("  ⛔ %d von %d Zellen KIPPEN:" % (len(schlecht), len(ZELLEN)))
        for H, m, nb, nn in schlecht:
            print("     H%d/%-6s Bootstrap %d/%d, Nullwelt %d/%d"
                  % (H, m, nb, len(BOOT_SAATEN), nn, len(NULL_SAATEN)))
        print()
        print("  ⚠️ Ein Urteil, das mit der Saat kippt, ist kein Urteil")
        print("     (2.477-stabilitaet). Diese Zellen zaehlen NICHT.")
    else:
        print("  ✔✔ ALLE %d ZELLEN HALTEN ueber %d Bootstrap- und %d "
              "Nullwelt-Saaten" % (len(ZELLEN), len(BOOT_SAATEN),
                                   len(NULL_SAATEN)))
    print()
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60))
    return 1 if schlecht else 0


if __name__ == "__main__":
    sys.exit(main())
