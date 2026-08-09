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


def stufe_1_kontingent(versuche: int = 3, abstand: float = 7.0) -> bool:
    """Kommt ueberhaupt ein Aufruf durch?

    Drei Aufrufe mit 7 s Abstand - unter der dokumentierten 10/min-Drossel und
    damit ein fairer Test. Am 09.08. abends kamen bei 8 s und 10 s Abstand
    NULL von acht durch; wenn hier auch nichts geht, ist der Tageswechsel
    nicht erfolgt und jede weitere Stufe waere Verschwendung."""
    import os

    import requests

    import config as config_module
    from api.gemini import BASE_URL, DEFAULT_MODEL
    config_module.load_env()
    schluessel = os.environ.get("GEMINI_API_KEY")
    if not schluessel:
        melde("ABBRUCH Stufe 1: GEMINI_API_KEY fehlt.")
        return False
    ok = 0
    for i in range(versuche):
        try:
            antwort = requests.post(
                BASE_URL,
                json={"model": DEFAULT_MODEL, "temperature": 0.1,
                      "messages": [{"role": "user", "content": "OK"}]},
                headers={"Authorization": f"Bearer {schluessel}"}, timeout=45)
        except Exception as exc:  # noqa: BLE001
            melde(f"  Probe {i + 1}: Netzwerkfehler {type(exc).__name__}")
            time.sleep(abstand)
            continue
        if antwort.status_code == 200:
            ok += 1
        else:
            melde(f"  Probe {i + 1}: HTTP {antwort.status_code} "
                  f"{antwort.text[:120]}")
        time.sleep(abstand)
    melde(f"Stufe 1: {ok} von {versuche} Probeaufrufen erfolgreich.")
    if ok < versuche:
        melde("ABBRUCH: das Kontingent traegt keinen Dauerlauf. Kein "
              "weiterer Versuch - das kostet nur, was morgen fehlt.")
        return False
    return True


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
    args = p.parse_args()

    melde("=" * 70)
    melde("WIRKUNGSMESSUNG - vier Stufen, jede ein Tor")
    melde("=" * 70)

    if not args.ohne_kontingentprobe and not stufe_1_kontingent():
        return 1

    melde("--- Stufe 2: Vorflug (2 Anker x 5 Arme)")
    ok, ausgabe = _lauf("Vorflug", [
        "messe_umbau_wirkung.py", "--anker", "2", "--je-symbol", "1",
        "--anbieter", "gemini", "--pause", "0.2", "--trotzdem-weiter",
        "--ausgabe", str(AUSGABE / "wirkung_vorflug.json")], zeitlimit=900)
    if not ok:
        melde(f"ABBRUCH Stufe 2: {ausgabe[-300:] if ausgabe else 'unbekannt'}")
        return 2
    if "[FEHLER]" in ausgabe:
        melde("ABBRUCH Stufe 2: eine Eingriffskontrolle ist fehlgeschlagen. "
              "Die Arme unterscheiden sich nicht wie beabsichtigt - ein "
              "Hauptlauf darauf waere sinnlos.")
        return 2
    melde("Stufe 2 bestanden: Prompt wird verarbeitet, Arme stimmen.")

    melde(f"--- Stufe 3: Hauptlauf ({args.anker} Anker x 5 Arme)")
    ok, ausgabe = _lauf("Hauptlauf", [
        "messe_umbau_wirkung.py", "--anker", str(args.anker),
        "--je-symbol", "5", "--anbieter", "gemini", "--pause", "0.2",
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
