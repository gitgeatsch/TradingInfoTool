"""Die Wirkungsmessung, unbeaufsichtigt und mit Abbruch bei jedem Defekt.

WOZU. Der Lauf startet automatisch nach dem Gemini-Tageswechsel, wenn niemand
zusieht. Er muss deshalb SELBST erkennen, wenn er nichts Brauchbares liefern
kann - und dann abbrechen, statt Stunden und Kontingent zu verbrennen. Genau
das ist am 09.08. dreimal passiert: ein Lauf mit dem falschen Anbieter, einer
mit zerstoerter LONG-Stichprobe, einer gegen ein erschoepftes Kontingent.

DIE VIER STUFEN, jede mit eigenem Abbruch:

    1 KONTINGENT   Drei Probeaufrufe mit korrektem Abstand. Kommt keiner
                   durch, ist der Tageswechsel nicht erfolgt oder das Budget
                   weiterhin leer - abbrechen, nichts weiter versuchen.
    2 VORFLUG      2 Anker x 5 Arme. Prueft die Eingriffskontrollen, dass das
                   Modell antwortet, dass die Antwort valide ist und dass die
                   Messfelder befuellt sind.
    3 HAUPTLAUF    60 Anker x 5 Arme. Der eingebaute Auswertbarkeits-Waechter
                   bricht nach wenigen Ankern ab, wenn die Zellen nicht
                   erreichbar werden.
    4 AUSWERTUNG   Verhalten, Ertrag und Zufallsvergleich, mit Rauschboden.

WAS ER NICHT TUT: eine Stufe ueberspringen, weil die vorige "fast" gereicht
hat. Jede Stufe ist ein Tor.

    python fahre_wirkungsmessung.py --anker 60
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import time

AUSGABE = pathlib.Path(
    "C:/Users/Geatsch/AppData/Local/Temp/claude/"
    "D--CLAUDE-Projects-SoftwareProjekte-TradingInfoTool/"
    "9e774fdd-5a46-48f6-9d20-e6614cad35af/scratchpad")


def melde(text: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {text}", flush=True)


def stufe_1_modellwahl(bedarf: int, festgelegt: str | None = None) -> str | None:
    """Welches Modell hat heute genug Budget fuer diesen Lauf?

    NEU AM 09.08., nachdem die Messung ergab, dass Google
    `...PerDayPerProjectPerModel...` begrenzt: 500 Aufrufe pro Tag, pro
    Projekt, pro MODELL. Drei Folgerungen stecken in dieser Funktion:

      je Modell   Ein erschoepftes Modell heisst nicht erschoepfter Zugang.
                  `gemini-3.5-flash-lite` war unberuehrt, waehrend unser
                  Produktionsmodell am Anschlag stand.
      am Schluessel  Das Budget haengt nicht am Geraet. Ein Messlauf am
                  Desktop nimmt der Produktion am Notebook direkt Kontingent
                  weg - deshalb steht das PRODUKTIONSMODELL hier hinten und
                  nicht vorn. Die Messung weicht aus, nicht die Produktion.
      vorher rechnen  `bedarf` wird gegen den Zaehler geprueft, BEVOR der
                  erste Aufruf faellt. Am 09.08. lief ein Lauf drei Stunden
                  gegen ein leeres Budget.

    Was hier bewusst NICHT steht: `gemini-flash-lite-latest`. Der Alias
    wechselt unangekuendigt das Modell (siehe api/gemini.py-Kommentar). In
    einem unbeaufsichtigten Lauf waere ein Modellwechsel mitten in der Messung
    ein stiller Bruch der Vergleichbarkeit - genau die Sorte Fehler, die diese
    Messung finden soll."""
    import os

    import requests

    import config as config_module
    from api.gemini import DEFAULT_MODEL, GeminiClient
    config_module.load_env()
    schluessel = os.environ.get("GEMINI_API_KEY")
    if not schluessel:
        melde("ABBRUCH Stufe 1: GEMINI_API_KEY fehlt.")
        return None

    client = GeminiClient(schluessel)
    # Ein festgelegtes Modell wird NICHT ungeprueft genommen - es durchlaeuft
    # dieselben zwei Tore (Zaehler und echter Probeaufruf). Festlegen heisst
    # "nimm dieses oder gar keins", nicht "frag nicht nach".
    kandidaten = ((festgelegt,) if festgelegt
                  else ("gemini-3.5-flash-lite", DEFAULT_MODEL))
    melde(f"Stufe 1: Bedarf {bedarf} Aufrufe."
          + (f" Modell festgelegt auf {festgelegt}." if festgelegt else ""))
    for modell in kandidaten:
        stand = client.budget_status(modell)
        rolle = "Produktionsmodell" if modell == DEFAULT_MODEL else "Ausweichmodell"
        melde(f"  {modell} ({rolle}): {stand['verbraucht']}/{stand['budget']} "
              f"verbraucht am {stand['tag_pazifik']}, "
              f"{stand['verfuegbar']} frei")
        if stand["verfuegbar"] < bedarf:
            melde("      zu wenig - naechster Kandidat.")
            continue
        # Der Zaehler kann zu niedrig stehen (Aufrufe von einem anderen Geraet
        # auf demselben Schluessel sieht er nicht). Deshalb zusaetzlich EIN
        # echter Aufruf gegen den nativen Endpunkt - der sagt im Fehlerfall
        # selbst, welches Kontingent gerissen ist.
        url = ("https://generativelanguage.googleapis.com/v1beta/models/"
               f"{modell}:generateContent")
        try:
            antwort = requests.post(
                url, headers={"x-goog-api-key": schluessel},
                json={"contents": [{"parts": [{"text": "hi"}]}],
                      "generationConfig": {"maxOutputTokens": 1}}, timeout=45)
        except Exception as exc:  # noqa: BLE001
            melde(f"      Netzwerkfehler {type(exc).__name__} - naechster.")
            continue
        if antwort.status_code == 200:
            melde(f"      Probeaufruf OK -> dieser Lauf nutzt {modell}.")
            return modell
        melde(f"      Probeaufruf HTTP {antwort.status_code} - "
              f"{antwort.text[:200]}")
        time.sleep(3)

    melde("ABBRUCH Stufe 1: kein Modell hat heute genug Budget. Kein "
          "weiterer Versuch - das kostet nur, was die Produktion braucht.")
    return None


def stufe_2b_groesse(vorflug: pathlib.Path, geplant: int,
                     min_zelle: int = 8) -> int | None:
    """Wie viele Anker braucht es, damit die SHORT-Kontrolle erreichbar ist?

    DER GRUND (10.08.). Die Messung hat zweimal ihr Ziel verfehlt, und beide
    Male an derselben Stelle: der Grundlinienarm waehlte zu selten SHORT, also
    entstand keine einzige gepaarte SHORT-Zelle, also war die
    Kontrollbedingung der vorab festgelegten Regel nicht pruefbar. Bemerkt
    wurde das jedes Mal ERST IM LAUF - nach 25 Ankern und 125 Aufrufen.

    Der Vorflug misst den SHORT-Anteil an acht Ankern. Daraus laesst sich
    ausrechnen, wie gross der Hauptlauf sein muss, BEVOR er startet.

    KONSERVATIV GERECHNET: verwendet wird nicht der beobachtete Anteil,
    sondern eine UNTERE Schranke davon (halber Anteil, mindestens aber die
    Dreierregel-Untergrenze). Ein zu klein geschaetzter Bedarf ist der
    teurere Fehler - er kostet einen ganzen Lauf.

    Gibt None zurueck, wenn sich nichts sagen laesst: bei NULL beobachteten
    SHORT-Faellen in acht Ankern ist der Anteil nach oben durch 3/8 begrenzt,
    nach unten aber durch nichts. Dann ist die Groesse nicht bestimmbar, und
    der Aufrufer erfaehrt das, statt eine erfundene Zahl zu bekommen."""
    import json
    try:
        daten = json.loads(vorflug.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        melde(f"Stufe 2b: Vorflugdatei nicht lesbar ({exc}) - Groesse bleibt "
              f"bei {geplant}.")
        return None
    a1 = (daten.get("zeilen") or {}).get("A1") or []
    if not a1:
        melde("Stufe 2b: keine Grundlinienzeilen im Vorflug - Groesse bleibt.")
        return None
    n_short = sum(1 for z in a1 if z.get("richtung") == "SHORT")
    anteil = n_short / len(a1)
    melde(f"Stufe 2b: Grundlinie waehlt SHORT in {n_short} von {len(a1)} "
          f"Vorflug-Ankern ({anteil * 100:.0f} %).")
    if n_short == 0:
        melde("      Bei null Faellen laesst sich die noetige Groesse NICHT "
              "berechnen - null Treffer in acht Versuchen schliessen nichts "
              "aus, taugen aber auch nicht als Schaetzung. Der Lauf geht mit "
              "der geplanten Groesse weiter; der Auswertbarkeits-Waechter "
              "entscheidet unterwegs.")
        return None
    sicher = max(anteil / 2.0, 1.0 / len(a1) / 2.0)
    import math
    return int(math.ceil(min_zelle / sicher))


def _lauf(name: str, argumente: list[str], zeitlimit: int) -> tuple[bool, str]:
    melde(f"{name} startet ...")
    try:
        ergebnis = subprocess.run(
            [sys.executable, "-u", *argumente], capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=zeitlimit)
    except subprocess.TimeoutExpired:
        return False, f"{name}: Zeitlimit von {zeitlimit} s ueberschritten"
    ausgabe = (ergebnis.stdout or "") + (ergebnis.stderr or "")
    print(ausgabe, flush=True)
    if ergebnis.returncode != 0:
        return False, f"{name}: Rueckgabecode {ergebnis.returncode}"
    return True, ausgabe


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anker", type=int, default=60)
    p.add_argument("--ohne-kontingentprobe", action="store_true")
    # Stufe 1 waehlt sonst das Ausweichmodell zuerst, um das Budget der
    # Produktion zu schonen. Steht die Produktion ohnehin still, ist das
    # PRODUKTIONSMODELL die bessere Wahl: dann entfaellt die Annahme, dass
    # sich ein Befund von einem Modell auf ein anderes uebertraegt.
    # Geprueft wird das gesetzte Modell trotzdem - Budget und Probeaufruf.
    p.add_argument("--modell", default=None,
                   help="Gemini-Modell festnageln statt es waehlen zu lassen")
    # NUR STUFE 1 UND 2 (10.08.). Die Frage, an der die Messung zweimal
    # gescheitert ist, laesst sich fuer 40 Aufrufe vorab beantworten: waehlt
    # der Grundlinienarm oft genug SHORT, damit die Kontrollbedingung
    # ueberhaupt erreichbar wird? Ohne diese Vorabklaerung startet der
    # Hauptlauf mit unbekannter Erfolgsaussicht - und 280 Aufrufe sind ein
    # teurer Weg, "nein" zu erfahren.
    p.add_argument("--nur-vorflug", action="store_true",
                   help="Stufe 1+2 fahren, Groesse berechnen, dann anhalten")
    args = p.parse_args()

    melde("=" * 70)
    melde("WIRKUNGSMESSUNG - vier Stufen, jede ein Tor")
    melde("=" * 70)

    # Bedarf = Anker x Arme, plus Vorflug (2 x 5) und ein wenig Luft fuer die
    # Wiederholung bei ungueltiger Antwort (gemessen ~1,3 Versuche je Fall).
    bedarf = int((args.anker + 8) * 5 * 1.35)
    modell = args.modell
    if not args.ohne_kontingentprobe:
        modell = stufe_1_modellwahl(bedarf, args.modell)
        if modell is None:
            return 1
    modell_argumente = ["--modell", modell] if modell else []
    from api.gemini import DEFAULT_MODEL as _PRODUKTIONSMODELL
    if modell and modell != _PRODUKTIONSMODELL:
        melde(f"HINWEIS: die Messung laeuft auf {modell}, nicht auf dem "
              f"Produktionsmodell - dessen Budget bleibt der Produktion. "
              f"Preis: der Befund gilt streng genommen fuer dieses Modell; "
              f"die Uebertragung ist eine Annahme. Der ARM-VERGLEICH bleibt "
              f"gueltig, weil alle Arme dasselbe Modell sehen.")

    melde("--- Stufe 2: Vorflug (8 Anker x 5 Arme)")
    # ACHT statt zwei (10.08.). Zwei Anker reichen, um zu pruefen, dass der
    # Prompt verarbeitet wird - aber nicht, um die Frage zu beantworten, an
    # der die Messung zweimal gescheitert ist: WIE OFT waehlt der
    # Grundlinienarm ueberhaupt SHORT? Davon haengt ab, wie viele Anker es
    # braucht, damit die Kontrollbedingung erreichbar ist. Acht Anker kosten
    # 40 Aufrufe und ersparen im Zweifel einen Lauf, der nach 25 abbricht.
    ok, ausgabe = _lauf("Vorflug", [
        "messe_umbau_wirkung.py", "--anker", "8", "--je-symbol", "2",
        "--anbieter", "gemini", "--pause", "0.2", "--trotzdem-weiter",
        *modell_argumente,
        "--ausgabe", str(AUSGABE / "wirkung_vorflug.json")], zeitlimit=1800)
    if not ok:
        melde(f"ABBRUCH Stufe 2: {ausgabe[-300:] if ausgabe else 'unbekannt'}")
        return 2
    if "[FEHLER]" in ausgabe:
        melde("ABBRUCH Stufe 2: eine Eingriffskontrolle ist fehlgeschlagen. "
              "Die Arme unterscheiden sich nicht wie beabsichtigt - ein "
              "Hauptlauf darauf waere sinnlos.")
        return 2
    melde("Stufe 2 bestanden: Prompt wird verarbeitet, Arme stimmen.")

    anker = args.anker
    noetig = stufe_2b_groesse(AUSGABE / "wirkung_vorflug.json", args.anker)
    if noetig is not None and noetig > args.anker:
        melde(f"Stufe 2b: {args.anker} Anker reichen fuer die "
              f"SHORT-Kontrolle NICHT - noetig waeren rund {noetig}.")
        # Mehr Anker heisst mehr Aufrufe. Passt das noch ins Budget?
        import os

        import config as config_module
        from api.gemini import GeminiClient
        config_module.load_env()
        frei = GeminiClient(os.environ["GEMINI_API_KEY"]).budget_status(
            modell or "gemini-3.1-flash-lite")["verfuegbar"]
        moeglich = int(frei / (5 * 1.35))
        if moeglich >= noetig:
            anker = noetig
            melde(f"      Budget traegt es ({frei} frei) - erhoeht auf "
                  f"{anker} Anker.")
        else:
            anker = max(args.anker, moeglich)
            melde(f"      Budget traegt nur {moeglich} Anker ({frei} frei). "
                  f"Der Lauf geht mit {anker} weiter, die SHORT-Kontrolle "
                  f"wird damit VORAUSSICHTLICH NICHT erreichbar sein - das "
                  f"ist vorab bekannt und kein Befund des Laufs.")

    melde(f"--- Stufe 3: Hauptlauf ({anker} Anker x 5 Arme)")
    ok, ausgabe = _lauf("Hauptlauf", [
        "messe_umbau_wirkung.py", "--anker", str(anker),
        "--je-symbol", "5", "--anbieter", "gemini", "--pause", "0.2",
        *modell_argumente,
        "--ausgabe", str(AUSGABE / "wirkung.json")],
        zeitlimit=60 * 90)
    if not ok:
        melde(f"ABBRUCH Stufe 3: {ausgabe[-300:] if ausgabe else 'unbekannt'}")
        return 3
    if "ABBRUCH - die Messung kann ihre Frage nicht beantworten" in ausgabe:
        melde("Stufe 3 hat SELBST abgebrochen - die Zellen werden nicht gross "
              "genug. Das ist ein Ergebnis, kein Fehler: die Frage ist mit "
              "dieser Stichprobe nicht beantwortbar.")
        return 3
    melde("Stufe 3 durchgelaufen.")

    melde("--- Stufe 4: Auswertung")
    ok, ausgabe = _lauf("Auswertung", [
        "werte_kettennaht_aus.py", "--datei", str(AUSGABE / "wirkung.json"),
        "--rauschboden", "0.83"], zeitlimit=600)
    if not ok:
        melde(f"ABBRUCH Stufe 4: {ausgabe[-300:] if ausgabe else 'unbekannt'}")
        return 4

    melde("=" * 70)
    melde("FERTIG. Ergebnis in wirkung.json, Auswertung oben.")
    melde("ZUR ERINNERUNG BEIM LESEN: die Entscheidungsregel steht vorab fest "
          "- wirksam ist der Umbau, wenn er die LONG-Konfidenz WENIGER "
          "drueckt als die Alt-Variante, ueber dem Rauschboden von 0,83, UND "
          "SHORT sich dabei nicht gegenlaeufig bewegt.")
    melde("Das offene Risiko: 'deutlich unter der Basislinie' koennte die "
          "Unterdrueckung VERSTAERKEN statt sie zu beheben.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
