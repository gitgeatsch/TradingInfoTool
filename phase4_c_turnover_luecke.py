# -*- coding: utf-8 -*-
"""Phase 4, Punkt C — WAS KOSTET DIE `turnover`-LUECKE AM HEBEL?

## ⚠️⚠️ Was hier NICHT gefragt wird

**Nicht**, ob es eine bessere Quelle gibt. Das ist entschieden: neun
Anbieter geprueft (2.417 bis 2.417-naeherung), freie historische
Umlaufmenge gibt es nicht; `turnover` bleibt auf 66 von 536 Symbolen,
*„mit freien Mitteln nicht aufloesbar, und das gehoert so gesagt"*.

## Die Frage, die offen ist

`turnover_fuenftel` traegt die GROESSTEN Stufen der ganzen Bewertung
(+3,15 bis -2,40 Prozentpunkte), und bei einem fehlenden Wert setzt
`wahrscheinlichkeit.rechne` `punkte = 0.0` und markiert `luecke=True`.
Die SCHWELLE wird je Datenlage ausgeglichen - die QUOTE nicht, und
damit auch der HEBEL nicht.

⚠️ Der Code sagt das Problem selbst (N-15a, 03.09.2026): *„eine
Bewertung, der ein tragender Beitrag fehlt, ist nicht mit einer
vollstaendigen vergleichbar - ihre Skala haengt dann an der Datenlage."*

## ⚠️⚠️⚠️ Und WARUM eine Luecke nicht neutral ist

Ein fehlender Beitrag zaehlt 0,0 Punkte. Das entspricht **nicht** dem
Durchschnitt der Stufen, sondern liegt zwischen Fuenftel 2 (+0,22) und
Fuenftel 3 (-1,79). Ein Wert, der eigentlich Fuenftel 0 haette, verliert
**3,15 Punkte**; einer mit Fuenftel 4 wird um **2,40 Punkte geschont**.
Die Luecke wirkt also **einseitig zugunsten schlechter Werte**.

## Was gemessen wird - und was nicht gemessen werden KANN

Fuer die Werte ohne `turnover`-Reihe ist der wahre Rang **unbekannt**.
Messbar ist deshalb nicht die Verzerrung, sondern ihre **SPANNWEITE**:
welcher Hebel kaeme heraus, wenn der fehlende Wert im besten bzw.
schlechtesten Fuenftel laege. Das Ergebnis ist ein INTERVALL, in dem der
richtige Hebel liegt.

⚠️ Das ist keine Fehlerschaetzung, sondern eine Schranke - der wahre Wert
liegt irgendwo darin, und wo, weiss niemand.

⚠️ NUR LESEND, gegen eine SICHERUNG.

    python phase4_c_turnover_luecke.py --db <sicherung.db>
"""
from __future__ import annotations

import os
import sqlite3
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agent import betraege as B                            # noqa: E402
from agent import wahrscheinlichkeit as WK                 # noqa: E402

CRV = 2.0
KAPITAL_EUR = 17987.0          # wie in 2c, aus einem echten Signal geprueft
EINST = {"aktiv": True, "r_min": 0.005, "r_max": 0.0125,
         "hebelnenner_eur": 500.0, "hebel_ab": 2.0, "hebel_grenze": 5.0}


def _pfad(flagge: str, vorgabe: str) -> str:
    a = sys.argv[1:]
    return a[a.index(flagge) + 1] if flagge in a else vorgabe


def _turnover_symbole() -> set:
    """Die Symbole, fuer die `turnover` im BETRIEB einen Wert bekommt.

    ⚠️⚠️ BERICHTIGT AM 21.09.2026 (Befund 2.510) - UND DAS HAT DAS
    ERGEBNIS DIESES WERKZEUGS GEAENDERT.

    Hier stand `MR.MESSBASIS["turnover"]`, also die SYMBOLLISTE der
    Messdatei. Die kennt die FRISCHEGRENZE nicht. BNB steht darin, sein
    letzter Wert bei Coin Metrics ist aber vom 22.04.2019 - 2.709 Tage
    alt. Der Betrieb verwirft ihn (`umlaufmengen`, Grenze 21 Tage),
    dieses Werkzeug zaehlte ihn mit.

        gemeldet   3 von 16 Hebelsignalen mit turnover-Wert  (19 %)
        richtig    1 von 16                                  ( 6 %)

    ⚠️ Der Fehler ging in EINE Richtung: er liess die Luecke KLEINER
    aussehen, als sie ist - also genau die Richtung, die eine
    Entscheidung gegen den Hebel erschwert haette.

    ⚠️⚠️ Die Bedingung steht jetzt im HELFER `marktrang.
    turnover_verfuegbar`, nicht mehr hier - sonst laeuft sie beim
    naechsten Werkzeug wieder auseinander.
    """
    import agent.marktrang as MR
    return MR.turnover_verfuegbar()


def _hebel(zuschlag_punkte: float, stop: float) -> tuple:
    q = WK.basisrate(CRV) + zuschlag_punkte / 100.0
    if not 0.0 < q < 1.0:
        return None, None
    a = B.hebelrechnung(quote=q, crv=CRV, kapital_eur=KAPITAL_EUR,
                        stop_rel=stop, einstellungen=EINST)
    return (a["hebel"] if a["ist_hebel"] else None), a


def main() -> int:
    db = _pfad("--db", "")
    if not db or not os.path.exists(db):
        raise SystemExit("Sicherung nicht gefunden - mit --db "
                         "<sicherung.db> setzen (NIE die Standard-DB)")
    stufen = next(b.stufen for b in WK.BEITRAEGE
                  if b.merkmal == "turnover_fuenftel")
    basis = WK.basisrate(CRV)
    mit = _turnover_symbole()

    print("=" * 108)
    print("PHASE 4 · PUNKT C - WAS KOSTET DIE `turnover`-LUECKE AM HEBEL?")
    print("=" * 108)
    print("  `turnover_fuenftel` Stufen: %s Prozentpunkte" % (stufen,))
    print("  Eine LUECKE zaehlt 0,0 - das liegt zwischen Fuenftel 2 (%+.2f) "
          "und 3 (%+.2f)." % (stufen[2], stufen[3]))
    print("  ⚠️ Sie wirkt EINSEITIG: bestes Fuenftel verliert %.2f Punkte, "
          "schlechtestes wird" % stufen[0])
    print("     um %.2f Punkte geschont." % abs(stufen[4]))
    print("  Symbole mit `turnover`-Reihe: %d" % len(mit))
    print()

    c = sqlite3.connect("file:%s?mode=ro" % db.replace("\\", "/"), uri=True)
    zeilen = list(c.execute(
        "SELECT symbol, substr(created_at,1,10), hebel, position_size_eur, "
        "       verlust_am_stop_eur FROM signals "
        " WHERE instrument='hebel' AND hebel IS NOT NULL "
        "   AND verlust_am_stop_eur IS NOT NULL ORDER BY created_at"))
    print("-" * 108)
    print("  %-8s %-11s %5s %7s %8s   %s"
          % ("Symbol", "Tag", "turn", "Stop", "Hebel", "moegliche Spanne "
             "ohne die Luecke (Fuenftel 0 .. 4)"))
    print("-" * 108)
    ohne = betroffen = 0
    abstand = []
    for sym, tag, heb, pos, verl in zeilen:
        if not (heb and pos and verl):
            continue
        stop = verl / (pos * heb)
        z_heute = 100.0 * ((verl / KAPITAL_EUR) * 2.0 * CRV) / (1.0 + CRV)
        hat = sym.upper() in mit
        if hat:
            print("  %-8s %-11s %5s %6.1f%% %8.2f   (Wert liegt vor - keine "
                  "Luecke)" % (sym, tag, "ja", 100 * stop, heb))
            continue
        ohne += 1
        werte = []
        for p in stufen:
            h, _ = _hebel(z_heute + p, stop)
            werte.append(h)
        gueltig = [x for x in werte if x]
        spanne = ("%.2f .. %.2f" % (min(gueltig), max(gueltig))
                  if gueltig else "-")
        anzahl_spot = sum(1 for x in werte if x is None)
        # ⚠️ NICHT die BREITE der Spanne zaehlen - die sagt nur, wie
        # unterschiedlich die Faelle untereinander sind. Gefragt ist der
        # Abstand des HEUTIGEN Wertes zur Spanne: liegt er darunter, ist
        # der Hebel in JEDEM Fall zu niedrig angesetzt.
        if gueltig and min(gueltig) > heb + 1e-9:
            betroffen += 1
            abstand.append(min(gueltig) - heb)
        print("  %-8s %-11s %5s %6.1f%% %8.2f   %-16s %s"
              % (sym, tag, "NEIN", 100 * stop, heb, spanne,
                 ("%d von 5 Faellen waeren SPOT" % anzahl_spot)
                 if anzahl_spot else ""))
    print()
    print("  ➤ %d von %d Hebelsignalen entstanden OHNE `turnover`-Wert."
          % (ohne, len([z for z in zeilen if z[2] and z[3] and z[4]])))
    print("     Bei %d von %d liegt der HEUTIGE Hebel UNTERHALB der "
          "gesamten Spanne - in jedem" % (betroffen, ohne))
    print("     Fall, in dem ueberhaupt ein Hebel entstuende, waere er "
          "HOEHER.")
    if abstand:
        abstand.sort()
        print("     Abstand zum naechsten moeglichen Wert: Median %.2f, "
              "Spanne %.2f bis %.2f Stufen"
              % (abstand[len(abstand) // 2], abstand[0], abstand[-1]))
    print()
    print("  ⚠️⚠️ UND DIE ANDERE RICHTUNG IST DIE WICHTIGERE: bei den "
          "Fuenfteln 3 und 4 entstuende")
    print("     GAR KEIN HEBEL (2 von 5 Raengen, also 40 Prozent der "
          "Moeglichkeiten). Die Luecke")
    print("     laesst damit Hebelgeschaefte zu, die eine vollstaendige "
          "Bewertung moeglicherweise")
    print("     nicht zugelassen haette - und setzt den Hebel zu niedrig "
          "an, wenn sie zulaesst.")
    print()
    print("  ⚠️ Das ist eine SCHRANKE, keine Fehlerschaetzung: der wahre Rang "
          "ist unbekannt, und")
    print("     wo in der Spanne er liegt, weiss niemand. Die Spanne sagt, "
          "wie viel auf dem Spiel")
    print("     steht - nicht, wie falsch die Zahl ist.")
    print()
    print("  ⚠️ Kapital %s EUR angenommen (wie in 2c); die Quote ist nicht "
          "gespeichert und wird" % ("%.0f" % KAPITAL_EUR))
    print("     aus Hebel, Einsatz und Verlust am Stop zurueckgerechnet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
