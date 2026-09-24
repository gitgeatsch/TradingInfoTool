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

## ⚠️⚠️⚠️ DIE LAGENACHSE (24.09.2026, Befund 2.574, Umbauschritt A)

Das Gitter oben laesst **drei der vier Achsen** von `_gilt()` unberuehrt:
es uebergibt `klasse`, aber **nicht** `strategie`, `richtung`, `instrument`.
Beide Folgen sind belegt:

  1. Eine Aenderung an `strategien`/`richtungen`/`instrumente` eines
     Beitrags waere hier **nicht aufgefallen**. Genau das steht beim
     Hebelumbau an (`instrumente=("hebel",)`).
  2. Schlimmer: mit `strategie=""` gilt `"" not in ("einstieg",)`, also
     greifen die Beitraege mit `strategien=("einstieg",)` im ganzen
     Gitter **gar nicht**. Der Test friert eine Rechnung ein, in der die
     tragenden Beitraege stillgelegt sind.

Deshalb ein **zweites** Gitter, unter eigenem Schluesselpraefix `lage|`.

⚠️ DIE ALTEN SCHLUESSEL BLEIBEN UNVERAENDERT. Waeren sie umbenannt, waere
die aufgezeichnete Referenz von 432 Faellen wertlos - und mit ihr der
Massstab, wegen dem dieses Werkzeug existiert.

⚠️⚠️ DIE LAGEN WERDEN ABGELEITET, NICHT AUFGEZAEHLT (CLAUDE.md, Regel 4:
*„was aufgezaehlt wird, veraltet still"*). Quellen sind
`handelsauftrag.ERLAUBTE_PAARE` und die Deklarationen der Beitraege
selbst. Registriert jemand morgen einen Beitrag auf `richtungen=("short",)`,
waechst das Gitter **von allein** mit - ohne Aenderung an dieser Datei.
"""
import io
import json
import os
import sys

# ⚠️ NUR WENN ES GEHT (24.09.2026). Seit die Suite dieses Modul IMPORTIERT,
# statt es als Programm zu starten, steht in `sys.stdout` ihr Mitschnitt -
# und der kennt `reconfigure` nicht. Ohne diese Bedingung scheitert schon
# der Import, und die Suite meldet den Schutz als nicht ausfuehrbar.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from agent import wahrscheinlichkeit as WK

REFERENZ = "pruefwerte_wahrscheinlichkeit.json"
CRV = (1.5, 2.0, 2.6, 3.0)
STOP = (0.03, 0.05, 0.20)
KLASSEN = ("krypto", "aktien", "etf", "")
H = (True, False, None)
GEBUEHREN = (0.003, 0.015)


# Das REDUZIERTE Gitter fuer die Lagenachse. Die fuenf Achsen oben wirken
# auf die Lagenfrage nicht ein - `_gilt()` sieht von ihnen nur `klasse`.
# Zwei CRV, ein Stop, zwei Klassen, zwei H, eine Gebuehr = 8 je Lage.
L_CRV, L_STOP, L_KLASSEN, L_H, L_GEB = (2.0, 3.0), 0.05, ("krypto", ""), (True, None), 0.015


def _schluessel(crv, stop, klasse, h, geb):
    return "crv%s|stop%s|kl%s|h%s|geb%s" % (crv, stop, klasse or "-", h, geb)


def _ohne_text(fall: dict) -> dict:
    """Denselben Fall ohne die FORMULIERUNGEN - nur was gerechnet wurde.

    ⚠️ Fuer die Aufzeichnungssperre. Der Vergleich beim PRUEFEN bleibt
    vollstaendig: eine geaenderte Mailzeile soll dort auffallen. Nur die
    Frage *„darf ich ohne --auch-zahlen neu aufzeichnen?"* blendet Text aus.

    Text ist `zeilen` (aus `saetze()`) und `beitraege[*][3]` (`warum`).
    Name, Zustand und Punkte eines Beitrags bleiben drin - ein Sprung auf
    `zustand="nie"` ist eine Wirkungsaenderung, auch bei 0,0 Punkten.
    """
    rest = {k: v for k, v in fall.items()
            if k not in ("zeilen", "beitraege")}
    if "beitraege" in fall:
        rest["beitraege"] = [list(b[:3]) for b in fall["beitraege"]]
    return rest


def lagen() -> list:
    """Welche (instrument, strategie, richtung) muss der Test abdecken?

    ⚠️ ABGELEITET, NICHT AUFGEZAEHLT. Zwei Quellen, beide im Quelltext:

        handelsauftrag.ERLAUBTE_PAARE   was der Betrieb zulaesst
        WK.BEITRAEGE[*].instrumente     wo ein Beitrag registriert IST
                     .strategien
                     .richtungen

    Dazu die leere Lage ("", "", "") - das ist der Zustand, in dem das
    alte Gitter laeuft, und er muss mitgeprueft bleiben.
    """
    from agent import handelsauftrag as HA

    paare = {("", "")}
    for instrument, strategien in HA.ERLAUBTE_PAARE.items():
        for strategie in strategien:
            paare.add((instrument, strategie))
    # Ein Beitrag, der auf einer Lage registriert ist, die ERLAUBTE_PAARE
    # nicht kennt, muss trotzdem geprueft werden - sonst deckt der Test
    # genau die Registrierung nicht ab, um die es geht.
    for b in WK.BEITRAEGE:
        for instrument in (b.instrumente or ("",)):
            for strategie in (b.strategien or ("",)):
                paare.add((instrument, strategie))
    richtungen = {""}
    for b in WK.BEITRAEGE:
        richtungen.update(b.richtungen or ())
    return sorted((i, s, r) for (i, s) in paare for r in sorted(richtungen))


def erfassen_lagen() -> dict:
    """Das zweite Gitter: dieselbe Rechnung ueber alle Lagen."""
    aus = {}
    for instrument, strategie, richtung in lagen():
        vorne = "lage|i%s|s%s|r%s" % (instrument or "-", strategie or "-",
                                      richtung or "-")
        for crv in L_CRV:
            for klasse in L_KLASSEN:
                for h in L_H:
                    s = "%s|%s" % (vorne, _schluessel(crv, L_STOP, klasse,
                                                      h, L_GEB))
                    try:
                        r = WK.rechne(crv=crv, stop_relativ=L_STOP,
                                      klasse=klasse, h=h,
                                      gebuehr_je_seite=L_GEB,
                                      strategie=strategie, richtung=richtung,
                                      instrument=instrument)
                        aus[s] = {
                            "quote": round(r["quote"], 10),
                            "zuschlag": round(r["zuschlag_punkte"], 10),
                            # ⚠️ `zustand` UND `warum` gehoeren dazu: eine
                            # Lagenaenderung zeigt sich zuerst darin, dass
                            # ein Beitrag auf "nie" springt - die Punkte
                            # koennen dabei gleich bleiben (0,0 war schon
                            # vorher moeglich).
                            "beitraege": [
                                [b["name"], b["zustand"],
                                 round(b["punkte"], 10), b["warum"]]
                                for b in r["beitraege"]],
                        }
                    except WK.WahrscheinlichkeitUnbekannt as exc:
                        aus[s] = {"fehler": str(exc)}
    return aus


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
    jetzt.update(erfassen_lagen())
    if "--aufzeichnen" in sys.argv:
        # ⚠️⚠️⚠️ DIE SPERRE GEGEN DAS BEQUEME NEUAUFZEICHNEN (11.09.2026).
        #
        # DER ANLASS. Vier TEXTaenderungen an `saetze()` machten 144 der
        # 432 Faelle rot. Neu aufzeichnen war richtig - aber das ist ein
        # URTEIL, kein Handgriff, und beim naechsten Mal koennte
        # dieselbe Geste eine geaenderte ZAHL mitloeschen. Dann ist der
        # Massstab weg, und zwar genau dann, wenn er gebraucht wird.
        #
        # ⚠️⚠️⚠️ 24.09.2026: DIE TRENNUNG LAG AUF DER FALSCHEN EBENE, UND
        # DADURCH WAR DIE SPERRE STUMPF.
        #
        # Sie trennte nach SCHLUESSEL - `|saetze` gilt als Text, alles
        # andere als Zahl. Aber in einem `|geb<x>`-Schluessel steckt
        # `beitraege[*][3]`, der WARUM-Text, und der aendert sich mit
        # jedem Quellenverweis.
        #
        # GEMESSEN am 24.09.: die Referenz vom 11.09. war zu 100 % rot
        # (432 von 432). Davon waren ECHTE Zahlen: NULL. 144 Faelle
        # `saetze()`, 288 Faelle allein der `warum`-Text (504 Zeilen) -
        # nachgezogene Quellenangaben aus dem Nennerwechsel.
        #
        # Die Sperre hat also 288 TEXTaenderungen als Zahlaenderung
        # gemeldet und `--auch-zahlen` verlangt. Wer das tut, loescht
        # genau die Zahl mit, die sie schuetzen sollte - der Fall, den
        # ihr eigener Kommentar oben befuerchtet.
        #
        # DIE TRENNUNG LAEUFT JETZT NACH FELD: `warum` und `zeilen` sind
        # Text, alles andere ist Zahl.
        #
        #     TEXT aendert sich absichtlich - Formulierungen werden besser
        #     ZAHLEN aendern sich NIE, ohne dass eine Messung es verlangt
        #
        # Wer die Zahlen wirklich neu setzen will, nimmt `--auch-zahlen`
        # dazu - und schreibt den Grund ins Umbaudokument. Die Huerde ist
        # bewusst klein, aber sie zwingt zum Hinsehen.
        try:
            _alt = json.loads(io.open(REFERENZ, encoding="utf-8").read())
        except (OSError, ValueError):
            _alt = {}
        # ⚠️ 24.09.2026: EIN NEUER FALL IST KEINE GEAENDERTE ZAHL. Als die
        # Lagenachse dazukam, waren 64 Schluessel neu - die Sperre haette
        # sie als "64 Zahlen geaendert" gemeldet und damit `--auch-zahlen`
        # verlangt, obwohl sich keine einzige bestehende Zahl bewegt hat.
        # Das ist keine Aufweichung: was es vorher nicht gab, kann sich
        # nicht geaendert haben. Ein VERSCHWUNDENER Schluessel zaehlt
        # dagegen weiter mit - das waere ein Verlust an Abdeckung.
        _zahl = sorted(k for k in sorted(set(_alt) & set(jetzt))
                       if _ohne_text(_alt[k]) != _ohne_text(jetzt[k]))
        _neu = sorted(set(jetzt) - set(_alt))
        _weg = sorted(set(_alt) - set(jetzt))
        if _weg:
            # Ein verschwundener Fall ist Verlust an Abdeckung, nie Text.
            _zahl = sorted(set(_zahl) | set(_weg))
        if _zahl and "--auch-zahlen" not in sys.argv:
            print("=" * 66)
            print("⚠️⚠️⚠️ NICHT AUFGEZEICHNET - %d ZAHLEN haben sich "
                  "geaendert" % len(_zahl))
            print("=" * 66)
            for k in _zahl[:8]:
                print("   %s" % k)
            if len(_zahl) > 8:
                print("   ... und %d weitere" % (len(_zahl) - 8))
            print()
            print("Eine geaenderte TEXTzeile ist Absicht. Eine geaenderte")
            print("ZAHL ist ein Befund - sie gehoert gemessen, nicht")
            print("ueberschrieben. Ist die Aenderung gewollt UND begruendet:")
            print("   python %s --aufzeichnen --auch-zahlen"
                  % os.path.basename(__file__))
            return 1
        # Textaenderungen: abweichend, aber NICHT in der Rechnung.
        _text = sum(1 for k in sorted(set(_alt) & set(jetzt))
                    if _alt[k] != jetzt[k]
                    and _ohne_text(_alt[k]) == _ohne_text(jetzt[k]))
        io.open(REFERENZ, "w", encoding="utf-8").write(
            json.dumps(jetzt, ensure_ascii=False, indent=1, sort_keys=True))
        print("Aufgezeichnet: %d Faelle -> %s" % (len(jetzt), REFERENZ))
        print("   %d TEXTzeilen neu, %d Zahlen veraendert, %d Faelle NEU"
              % (_text, len(_zahl), len(_neu)))
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
