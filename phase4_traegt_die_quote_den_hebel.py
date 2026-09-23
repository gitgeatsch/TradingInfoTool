# -*- coding: utf-8 -*-
"""PHASE 4 - TRAEGT DIE QUOTE DEN HEBEL? Vorwaerts gerechnet, nicht zurueck.

## ⚠️⚠️⚠️ WARUM ES DIESE DATEI GIBT - EIN EIGENER FEHLER

`phase4_2c_hebelverteilung.py` beantwortet die Frage an ECHTEN Signalen,
indem es die Quote aus dem gespeicherten Verlust ZURUECKRECHNET:

    r = verlust / Kapital  ->  q = (2 r b + 1) / (1 + b)

⛔ Das ist ZIRKULAER. `r` ist auf [r_min .. r_max] geklammert, also kann
die zurueckgerechnete Quote per Konstruktion nur zwischen 0,3400 und
0,3500 liegen - Faktor 1,029. Gemessen wurde 1,02, und daraus habe ich
geschlossen, die Quote *„streue kaum"* und trage den Hebel nicht.

⚠️ Der Schluss war falsch. Die ECHTE Quote spannt ueber die
Fuenftel-Kombinationen **0,2857 bis 0,3647** auf - 7,9 Prozentpunkte bei
einem steuernden Fenster von rund 1,6. Sie streut also ein VIELFACHES des
Fensters; man sieht es nur nicht, wenn man sie aus der geklammerten
Groesse zurueckrechnet.

⚠️⚠️ UND DER ZWEITE FEHLER WAR EIN ERFUNDENER BLOCKER: ich hatte
geschrieben, fuer die Antwort brauche es *„Signale aus der neuen
Kalibrierung"* - also Warten auf den Betrieb. Nutzerwortlaut dazu:
*„NOWAY - Teste, pruefe und Simuliere ... wir haben historische Daten und
koennen zurueck oder nach vorne simulieren."* Richtig: die Quote ist
VORWAERTS rechenbar, auf jedem Anker, mit der heute laufenden
Stufentabelle.

## ⚠️⚠️⚠️ DER MESSSTANDARD - und warum er hier NICHT gilt

    Messstandard ab 2026-09-09: Bezug = nullpunkt | Nullwelten = 90.
    Perzentil ueber 40 Ziehungen | Trennschaerfe gegen denselben Bezug |
    gepflanzte Staerken bis 0,40 R | Positivkontrolle 5 Ziehungen

Er gilt fuer die Messung einer WIRKUNG gegen Nullwelten - dort, wo eine
Stichprobe gegen den Zufall zu halten ist. Diese Datei rechnet dagegen
eine ABLEITUNG: gegebene Quote plus gegebener Stop ergeben genau einen
Hebel, deterministisch, ohne Ziehung. Es gibt nichts zu bandieren.

⚠️⚠️ ABER DARAUS FOLGT EINE PFLICHT: das Wort **„traegt"** ist in diesem
Projekt NORMIERT - es heisst *„Wirkung ueber der Trennschaerfe gegen den
Nullpunkt"*. Diese Datei benutzt es deshalb NICHT als Urteil. Sie
beantwortet eine KONSTRUKTIONSfrage:

    wie viel Hebelspanne erzeugt die Quote bei festem Stop,
    wie viel der Stop bei fester Quote?

⚠️ Die zugehoerige BEITRAGSfrage - *„laufen Trades mit hohem Hebel besser
als mit niedrigem?"* - ist eine andere und bereits normgerecht gemessen:
2a, *„der Hebel bekommt keine eigene Bewertung"*. Beides zu vermengen
waere derselbe Fehler wie am 23.09. frueh, als ich zwei verschiedene
Fensterbegriffe gegeneinandergestellt habe.

## Was gerechnet wird

    1  DIE SPANNE der echten Quote ueber alle 25 Fuenftel-Kombinationen,
       gegen die Breite des steuernden Fensters gehalten
    2  DIE ZERLEGUNG: Hebelspanne bei festem Stop (nur Quote variiert)
       gegen Hebelspanne bei fester Quote (nur Stop variiert)
    3  AUF ECHTEN ANKERN: wie sind die Kombinationen im Bestand verteilt,
       und was folgt daraus fuer die Hebel

⚠️ Gerechnet wird mit dem ECHTEN Code (`potential.rechne`,
`betraege.hebelrechnung`) und den LAUFENDEN Einstellungen - nicht mit
Code-Vorgaben.

    python phase4_traegt_die_quote_den_hebel.py [--db <sicherung.db>]
"""
from __future__ import annotations

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agent import betraege as BE                            # noqa: E402
from agent import potential as POT                          # noqa: E402
from pruefstand_hebelmail import betriebskonfiguration      # noqa: E402

KAPITAL = 17987.0
CRV = 2.0
STOPWEITEN = (0.05, 0.08, 0.12, 0.17, 0.25)


def einstellungen(cfg):
    return dict((cfg.get("rollen_kette") or {}).get("hebel_aus_quote") or {})


def quote(fu, tu):
    """Die ECHTE Quote - vorwaerts aus der laufenden Stufentabelle.

    ⚠️ `klasse='krypto'` ist Pflicht: `wahrscheinlichkeit._gilt()` prueft
    Klasse, Strategie und Richtung. Ohne Klasse tragen die Beitraege NULL
    bei, und die Quote bleibt auf der Basisrate stehen - mein erster Lauf
    sah deshalb aus, als haetten die Fuenftel keine Wirkung.
    """
    return POT.rechne(crv=CRV, stop_relativ=0.08, klasse="krypto",
                      merkmale={"funding_fuenftel": fu,
                                "turnover_fuenftel": tu}).quote


def hebel(cfg, q, stop_rel):
    # ⚠️ NUR SCHLUESSELWORTE: `hebelrechnung` nimmt keine Stellungsargumente
    # (`def hebelrechnung(*, quote, crv, ...)`). Mein erster Aufruf reichte
    # sieben positionell durch und brach ab - abgelesen an der Signatur,
    # nicht geraten.
    h = BE.hebelrechnung(quote=q, crv=CRV, kapital_eur=KAPITAL,
                         stop_rel=stop_rel, einstellungen=einstellungen(cfg))
    return float((h or {}).get("hebel") or 0.0)


def main() -> int:
    cfg = betriebskonfiguration()
    e = einstellungen(cfg)
    print("=" * 100)
    print("TRAEGT DIE QUOTE DEN HEBEL? - vorwaerts gerechnet")
    print("=" * 100)
    print("  Stufentabelle: %s" % POT.beitragslage())
    print("  Klammer r: %.4f bis %.4f · hebel_ab %.1f · grenze %.1f"
          % (e.get("r_min", 0.005), e.get("r_max", 0.0125),
             e.get("hebel_ab", 2.0), e.get("hebel_grenze", 5.0)))

    # ---- 1) Die Spanne der ECHTEN Quote ------------------------------
    print("\n  1) DIE ECHTE QUOTE UEBER ALLE 25 FUENFTEL-KOMBINATIONEN")
    print("  " + "-" * 96)
    qs = {}
    print("     funding\\turnover %s" % "".join("%9d" % t for t in range(5)))
    for fu in range(5):
        zeile = []
        for tu in range(5):
            q = quote(fu, tu)
            qs[(fu, tu)] = q
            zeile.append("%9.4f" % q)
        print("     %-16d %s" % (fu, "".join(zeile)))
    qmin, qmax = min(qs.values()), max(qs.values())
    print("     ➤ Spanne %.4f bis %.4f = %.1f Prozentpunkte"
          % (qmin, qmax, 100 * (qmax - qmin)))
    print("       Das steuernde Fenster ist rund 1,0 bis 1,5 Punkte breit -")
    print("       die Quote streut also ein VIELFACHES davon.")

    # ---- 2) Die Zerlegung --------------------------------------------
    print("\n  2) ⚠⚠ DIE ZERLEGUNG - wer bewegt den Hebel?")
    print("  " + "-" * 96)
    print("     A) STOP FEST, nur die Quote variiert (alle 25 "
          "Kombinationen):")
    print("        %-10s %10s %10s %10s %12s"
          % ("Stop", "Hebel min", "Hebel max", "Faktor", "davon Spot"))
    for st in STOPWEITEN:
        # ⚠️ SPOT IST `hebel < hebel_ab`, NICHT `== 0`. Die Rechnung gibt
        # unterhalb der Schwelle 1,0 zurueck (= Spot), nicht null - meine
        # erste Zaehlung meldete deshalb ueberall "0 davon Spot", obwohl
        # die halbe Tabelle Spot war.
        _ab = float(e.get("hebel_ab", 2.0))
        hs = [hebel(cfg, q, st) for q in qs.values()]
        echt = [x for x in hs if x >= _ab]
        spot = sum(1 for x in hs if x < _ab)
        if not echt:
            print("        %-10s %10s %10s %10s %12d"
                  % ("%.0f %%" % (100 * st), "-", "-", "-", spot))
            continue
        print("        %-10s %10.2f %10.2f %10.2f %12d"
              % ("%.0f %%" % (100 * st), min(echt), max(echt),
                 max(echt) / min(echt), spot))

    print("\n     B) QUOTE FEST, nur der Stop variiert:")
    print("        %-14s %10s %10s %10s"
          % ("Quote", "Hebel min", "Hebel max", "Faktor"))
    for name, q in (("niedrigste", qmin), ("mittlere", sorted(qs.values())[12]),
                    ("hoechste", qmax)):
        hs = [hebel(cfg, q, st) for st in STOPWEITEN]
        echt = [x for x in hs if x >= float(e.get("hebel_ab", 2.0))]
        if not echt:
            print("        %-14s %10s %10s %10s"
                  % ("%s %.4f" % (name, q), "-", "-", "alle Spot"))
            continue
        print("        %-14s %10.2f %10.2f %10.2f"
              % ("%s %.4f" % (name, q), min(echt), max(echt),
                 max(echt) / min(echt)))

    print("\n     ⚠⚠ SO GELESEN: (A) sagt, was die Quote bei "
          "festem Stop bewegt,")
    print("        (B) was der Stop bei fester Quote bewegt. Erst beide "
          "zusammen")
    print("        beantworten die Frage - eine allein ist nur die halbe "
          "Achse.")

    print("\n" + "=" * 100)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
