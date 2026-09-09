# -*- coding: utf-8 -*-
"""K-1b — Tragen die Beiträge auf einer UNSELEKTIERTEN Menge? (09.09.2026)

## Die Frage, und warum sie zaehlt

Die Kette beurteilt je Lauf rund 27 von 43 Krypto-Werten. Davon passieren
**25 die Auswahl, WEIL der Nutzer sie haelt** - nach nichts selektiert.
Nur 2 kommen von A1 (top-k nach Jahresentwicklung).

Alle Beitraege sind aber auf den Mengen 5/10/20/50 % belegt - **alle nach
MOMENTUM verengt**. Und der groesste Signalposten der Kette,
`NACHKAUFEN` mit 51,7 Mails am Tag, hat per Definition Bestand.

> **Die Beitraege werden auf einer Menge angewandt, auf der sie nie
> geprueft wurden.** (Befund 2.220)

## ⚠️⚠️ Warum ein STELLVERTRETER noetig ist

Eine Bestands-Historie gibt es nicht: `holdings` hat 55 Zeilen ohne
Zeitachse, `portfolio_wert_historie` ist leer. Die echte historische
Bestandsmenge ist **nicht rekonstruierbar**.

Der Stellvertreter ist eine Menge **gleicher Groesse, aber ZUFAELLIG
gewaehlt** statt nach Momentum. Alles andere bleibt gleich - der Rang
kommt weiter aus dem vollen Tagesquerschnitt, wie `marktrang` in der
Produktion.

    traegt auf der Zufallsmenge     -> uebertraegt sich auf den Bestand
    traegt NUR auf der Momentumspitze -> der Beleg haengt an einer Auswahl,
                                       die der Bestand nicht durchlaeuft

⚠️ **Die Grenze des Stellvertreters gehoert dazu:** der echte Bestand ist
vom Nutzer gewaehlt, also nicht neutral - aber auch nicht gegen den
Beitrag gerichtet. Er ist damit eine Aussage ueber die Uebertragbarkeit,
kein Abbild des Bestands.

## ⚠️ EINE Zufallsauswahl ist kein Beleg

Dieselbe Regel wie beim Nullpunkt. Es laufen **fuenf** Ziehungen.

## ⚠️⚠️ DIE KONTROLLREGEL WAR ERST FALSCH — und der Fehler war lehrreich

Die erste Fassung verlangte, dass `zufall` in KEINER Variante traegt, und
erklaerte den Lauf sonst fuer wertlos. Genau das passierte (1 von 6).

**Die Regel war falsch.** Kriterium B hat eine gemessene Fehlalarmquote
von 2,7 % - das ist gewollt und gemessen. Bei sechs Ziehungen liegt die
Wahrscheinlichkeit, mindestens einen Fehlalarm zu sehen, bei **15 %**.
Eine Kontrolle, die nie feuern darf, verlangt implizit **0 %** - also
genau das Kriterium `null_oben`, das am selben Tag als ueberstreng
verworfen wurde.

⚠️ Und mit fuenf Ziehungen laesst sich eine QUOTE ohnehin nicht schaetzen.
Verglichen wird deshalb die **WIRKUNG** des Kandidaten gegen die des
Zufalls auf derselben Art Menge.

## Der Aufbau

    Kandidaten   funding · turnover · oi_aenderung · schnitt · zufall
    Menge        je die REGISTRIERTE (funding 10 %, turnover 50 %,
                 oi_aenderung 20 %, schnitt 20 %) - dort ist der Beleg
    Fenster      ab 2022 fuer die drei registrierten (ihre eigene Basis)
    Vergleich    Momentum-Auswahl gegen 5 Zufallsauswahlen gleicher Groesse
    Kontrolle    `zufall` auf denselben Zufallsmengen - verglichen wird
                 seine WIRKUNG, nicht seine Quote (siehe unten)

## Die Vorhersage, VOR dem Lauf (Methodik 2.80)

Die Beitraege sind **Marktraenge** - der Rang entsteht im vollen
Querschnitt, unabhaengig davon, auf welcher Teilmenge gemessen wird.

    Erwartung   sie tragen auch auf der Zufallsmenge, mit etwas
                breiteren Baendern (eine Zufallsmenge ist heterogener)
    Gegenthese  der Effekt sitzt in den Momentum-Spitzenwerten; dann
                bricht er auf der Zufallsmenge ein

⚠️ **Bricht er ein, ist das ein schwerer Befund** - dann gilt der Beitrag
fuer den groessten Teil der Kettensignale nicht.

    python k1b_beitrag_auf_bestandsmenge.py
"""
from __future__ import annotations

import sys
import time

import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import messe_eigenschaft_beitrag as B                        # noqa: E402
import messe_kandidaten_als_regel as K                       # noqa: E402
import messnorm as N                                          # noqa: E402
import messnorm_auswahl as MA                                # noqa: E402
from messe_alle_kandidaten import HORIZONT, zusatzquellen    # noqa: E402
from messe_beitrag_auf_auswahl import momentum250            # noqa: E402

ZIEHUNGEN = 5
SAATEN = (81001, 81002, 81003, 81004, 81005)
# (Kandidat, registrierte Menge, Fenster)
FAELLE = (("funding", "10%", "2022-01-01"),
          ("turnover", "50%", "2022-01-01"),
          ("oi_aenderung", "20%", "2022-01-01"),
          ("schnitt", "20%", None),
          ("zufall", "20%", None))


def kurz(u: str) -> str:
    return u.split(" (")[0].split(" - ")[0][:24]


def main() -> int:
    t0 = time.time()
    reihen = B.lade()
    mom = momentum250(reihen)
    lage = N.Lage(instrument="spot", strategie="einstieg")
    zus = zusatzquellen()

    print("=" * 108)
    print("K-1b — tragen die Beitraege auf einer UNSELEKTIERTEN Menge?")
    print("=" * 108)
    print("  %s" % N.standardzeile())
    print("  Vergleich: Momentum-Auswahl gegen %d ZUFALLSauswahlen "
          "gleicher Groesse." % ZIEHUNGEN)
    print("  ⚠️ Stellvertreter - eine Bestands-Historie gibt es nicht.")

    erg = {}
    for kand, menge, ab in FAELLE:
        je = K.baue(reihen, kand, zus.get(kand), horizont=HORIZONT)
        if ab:
            je = {t: z for t, z in je.items() if str(t) >= ab}
        print()
        print("  %s auf %s%s" % (kand.upper(), menge,
                                 (" ab %s" % ab) if ab else ""))
        print("     %-14s %9s %20s %9s %8s  %s"
              % ("Auswahl", "Wirkung", "Band", "Bezug", "traegt", "Urteil"))
        reihe = []
        for name, saat in [("Momentum", None)] + \
                          [("Zufall %d" % (i + 1), s)
                           for i, s in enumerate(SAATEN[:ZIEHUNGEN])]:
            try:
                b = MA.pruefe_auswahl(
                    kand, je, mom, lage=lage, menge=menge,
                    rng=np.random.default_rng(20260909), horizont=HORIZONT,
                    hypothese="K-1b Bestandsmenge", verwendung="Beitrag",
                    auswahl_saat=saat)
            except Exception as exc:                         # noqa: BLE001
                print("     %-14s -> %s" % (name, str(exc)[:60]))
                continue
            reihe.append((name, b))
            print("     %-14s %+9.4f [%+.4f..%+.4f] %+9.4f %8s  %s"
                  % (name, b.wirkung, b.unten, b.oben, b.bezugswert,
                     b.traegt, kurz(b.urteil)), flush=True)
        erg[kand] = reihe

    # ---- Urteil ---------------------------------------------------------
    print()
    print("=" * 108)
    print("UEBERTRAEGT SICH DER BELEG AUF EINE UNSELEKTIERTE MENGE?")
    print("=" * 108)
    # ⚠️⚠️ DIE KONTROLLREGEL WAR ERST FALSCH (korrigiert 09.09.2026).
    #
    # Sie verlangte, dass `zufall` in KEINER Variante traegt. Das ist
    # dieselbe Ueberstrenge, die am selben Tag als Fehler 6 erkannt wurde:
    # Kriterium B hat eine gemessene Fehlalarmquote von 2,7 % - das ist
    # gewollt. Bei sechs Ziehungen liegt die Wahrscheinlichkeit, MINDESTENS
    # einen Fehlalarm zu sehen, bei 15 %. Eine Kontrolle, die nie feuern
    # darf, verlangt implizit 0 % - also genau das verworfene Kriterium A.
    #
    # ⚠️ Und mit fuenf Ziehungen laesst sich eine QUOTE ohnehin nicht
    # schaetzen. Die tragfaehige Frage ist deshalb nicht "wie oft traegt
    # der Zufall", sondern: **ist die WIRKUNG des Kandidaten von der des
    # Zufalls unterscheidbar?**
    zf = erg.get("zufall") or []
    zuf_z = [b.wirkung for n, b in zf if n.startswith("Zufall")]
    zuf_tr = sum(1 for n, b in zf if n.startswith("Zufall") and b.traegt)
    zuf_mittel = float(np.mean(zuf_z)) if zuf_z else float("nan")
    zuf_max = max(zuf_z) if zuf_z else float("nan")
    print("  Kontrolle `zufall` auf Zufallsmengen: %d von %d tragen · "
          "Wirkung Mittel %+.4f, groesste %+.4f"
          % (zuf_tr, len(zuf_z), zuf_mittel, zuf_max))
    if len(zuf_z) < 20:
        print("  ⚠️ %d Ziehungen erlauben KEINE Quotenschaetzung (bei "
              "wahren 2,7 %% waeren 0 bis 1 Treffer normal). Verglichen "
              "wird deshalb die WIRKUNG, nicht die Quote." % len(zuf_z))
    print()
    print("  %-14s %8s    %8s  %s %6s  %s"
          % ("Kandidat", "Momentum", "Zufall", "n/N", "x Kontr.", "Urteil"))
    for kand, _m, _ab in FAELLE:
        if kand == "zufall" or kand not in erg:
            continue
        reihe = erg[kand]
        mo = next((b for n, b in reihe if n == "Momentum"), None)
        zu = [b for n, b in reihe if n.startswith("Zufall")]
        n_tr = sum(1 for b in zu if b.traegt)
        if mo is None or not zu:
            continue
        w_zu = float(np.mean([b.wirkung for b in zu]))
        # ⚠️ Der Massstab ist die KONTROLLE auf derselben Art Menge, nicht
        # eine gesetzte Zahl. Faktor 2 gegen den Zufall ist der Punkt, ab
        # dem die Wirkung nicht mehr durch ihn erklaerbar ist.
        vielfaches = (w_zu / zuf_mittel) if zuf_mittel and zuf_mittel > 0             else float("nan")
        if not mo.traegt:
            urteil = "⚠️ traegt schon auf der Momentummenge nicht"
        elif n_tr >= 4 and vielfaches >= 2.0:
            urteil = "✔ UEBERTRAEGT SICH - deutlich ueber der Kontrolle"
        elif n_tr >= 4:
            urteil = ("⚠️ traegt zwar, aber nur %.1f-fach ueber der "
                      "Kontrolle" % vielfaches)
        elif n_tr <= 2:
            urteil = ("⚠️⚠️ BRICHT EIN - vom Zufall kaum zu unterscheiden "
                      "(%.1f-fach)" % vielfaches)
        else:
            urteil = "⚠️ UNEINHEITLICH - %d von %d" % (n_tr, len(zu))
        print("  %-14s %+8.4f -> %+8.4f  %d/%d  %5.1fx  %s"
              % (kand, mo.wirkung, w_zu, n_tr, len(zu), vielfaches, urteil))
    print()
    print("  ⚠️ Ein Zufallsausschnitt ist ein STELLVERTRETER fuer den "
          "Bestand,")
    print("     kein Abbild - eine Bestands-Historie gibt es nicht.")
    print("  Dauer %.1f Minuten" % ((time.time() - t0) / 60.0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
