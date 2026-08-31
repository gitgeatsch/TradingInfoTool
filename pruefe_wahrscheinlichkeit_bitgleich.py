# -*- coding: utf-8 -*-
"""Bitgleichheitstest fuer wahrscheinlichkeit.py (30.08.2026, G-2' Schritt 2a).

## Wozu

Schritt 2 baut `Beitrag` um: heute kennt er EINEN Punktwert, kuenftig auch
STUFEN. Dabei muss H unveraendert weiterrechnen - jede Abweichung waere ein
stiller Fehler in einer Zahl, die in jeder Mail steht.

⚠️ **Dieser Test wird VOR dem Umbau gebaut und aufgezeichnet.** Er friert das
heutige Verhalten ein. Danach darf sich nichts aendern, was hier steht.

    python pruefe_wahrscheinlichkeit_bitgleich.py --aufzeichnen
    ... Umbau ...
    python pruefe_wahrscheinlichkeit_bitgleich.py        -> muss 0 FEHL sein

## Was abgedeckt wird

Alle Kombinationen, die im Betrieb vorkommen koennen:

    crv            1,5 / 2,0 / 2,6 / 3,0      die tatsaechlich benutzten
    stop_relativ   0,03 / 0,05 / 0,20         eng bis weit
    klasse         krypto / aktien / etf / "" die Beitraege sind klassenabhaengig
    h              True / False / None        ⚠️ alle drei, None ist eigen
    gebuehr        0,003 / 0,015              Referenz und Betrieb

Das sind 4 x 3 x 4 x 3 x 2 = 288 Faelle. Erfasst wird nicht nur die Quote,
sondern **jedes Feld** der Rueckgabe und **jede Zeile** von `saetze()` -
inklusive Reihenfolge und Text.
"""
import io
import json
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agent import wahrscheinlichkeit as WK

REFERENZ = "pruefwerte_wahrscheinlichkeit.json"
CRV = (1.5, 2.0, 2.6, 3.0)
STOP = (0.03, 0.05, 0.20)
KLASSEN = ("krypto", "aktien", "etf", "")
H = (True, False, None)
GEBUEHREN = (0.003, 0.015)


def _schluessel(crv, stop, klasse, h, geb):
    return "crv%s|stop%s|kl%s|h%s|geb%s" % (crv, stop, klasse or "-", h, geb)


def erfassen() -> dict:
    """Jeden Fall einmal rechnen und vollstaendig festhalten."""
    aus = {}
    for crv in CRV:
        for stop in STOP:
            for klasse in KLASSEN:
                for h in H:
                    for geb in GEBUEHREN:
                        s = _schluessel(crv, stop, klasse, h, geb)
                        try:
                            r = WK.rechne(crv=crv, stop_relativ=stop,
                                          klasse=klasse, h=h,
                                          gebuehr_je_seite=geb)
                            # Zahlen gerundet - Fliesskomma darf nicht am
                            # letzten Bit scheitern, aber 10 Stellen sind
                            # strenger als jede sichtbare Aenderung.
                            aus[s] = {
                                "quote": round(r["quote"], 10),
                                "basisrate": round(r["basisrate"], 10),
                                "zuschlag": round(r["zuschlag_punkte"], 10),
                                "breakeven": round(r["breakeven"], 10),
                                "abstand": round(r["abstand_punkte"], 10),
                                "ew_r": round(r["erwartungswert_r"], 10),
                                # ⚠️ LISTEN, keine Tupel. JSON kennt keine
                                # Tupel - beim Zurueckladen werden sie zu
                                # Listen, und der Vergleich schlaegt fehl,
                                # obwohl sich nichts geaendert hat.
                                "beitraege": [
                                    [b["name"], b["zustand"],
                                     round(b["punkte"], 10), b["warum"]]
                                    for b in r["beitraege"]],
                            }
                        except WK.WahrscheinlichkeitUnbekannt as exc:
                            aus[s] = {"fehler": str(exc)}
                    # saetze() nur je (crv, stop, klasse, h) - die Gebuehren
                    # stecken dort in `saetze_zum_berichten`
                    st = _schluessel(crv, stop, klasse, h, "saetze")
                    try:
                        aus[st] = {"zeilen": list(WK.saetze(
                            crv=crv, stop_relativ=stop, klasse=klasse, h=h))}
                    except Exception as exc:                 # noqa: BLE001
                        aus[st] = {"fehler": repr(exc)}
    return aus


def main() -> int:
    jetzt = erfassen()
    if "--aufzeichnen" in sys.argv:
        io.open(REFERENZ, "w", encoding="utf-8").write(
            json.dumps(jetzt, ensure_ascii=False, indent=1, sort_keys=True))
        print("Aufgezeichnet: %d Faelle -> %s" % (len(jetzt), REFERENZ))
        print("⚠️ Diese Datei ist der Massstab. Sie wird NUR neu geschrieben,")
        print("   wenn eine Aenderung ABSICHTLICH das Ergebnis verschiebt -")
        print("   und dann steht der Grund im Umbaudokument.")
        return 0

    try:
        soll = json.loads(io.open(REFERENZ, encoding="utf-8").read())
    except FileNotFoundError:
        print("FEHL: keine Referenz. Erst `--aufzeichnen` laufen lassen -")
        print("      und zwar VOR dem Umbau.")
        return 1

    fehl = 0
    for s in sorted(set(soll) | set(jetzt)):
        a, b = soll.get(s), jetzt.get(s)
        if a is None:
            print("  NEU (in der Referenz nicht vorhanden): %s" % s)
            fehl += 1
        elif b is None:
            print("  FEHLT jetzt: %s" % s)
            fehl += 1
        elif a != b:
            fehl += 1
            print("  ABWEICHUNG bei %s" % s)
            for feld in sorted(set(a) | set(b)):
                if a.get(feld) != b.get(feld):
                    print("      %-11s soll %s" % (feld, str(a.get(feld))[:90]))
                    print("      %-11s ist  %s" % ("", str(b.get(feld))[:90]))
    print()
    print("=" * 66)
    print("%d Faelle geprueft, %d FEHL" % (len(jetzt), fehl))
    return 1 if fehl else 0


if __name__ == "__main__":
    sys.exit(main())
