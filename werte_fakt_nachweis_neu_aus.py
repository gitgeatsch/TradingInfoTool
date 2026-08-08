"""Wertet einen abgeschlossenen Fakt-Nachweis NEU aus - ohne einen einzigen Aufruf.

WOZU. `laufe_fakt_nachweis.py` speichert jede Rohantwort. Damit ist jede
Auswertungsfrage, die einem HINTERHER einfaellt, gratis beantwortbar:

  * anderer Horizont (7 statt 14, oder umgekehrt)
  * strengere Entscheidungsregel
  * eine Teilmenge - etwa ohne den einen Tag, der ein Drittel der Faelle stellt
  * ein spaeter gefundener Auswertungsfehler

Das ist die Nutzer-Vorgabe "damit wir nicht mehrmals testen muessen", zu Ende
gedacht: nicht nur den Lauf wiederverwenden, sondern die AUSWERTUNG davon
trennen. Ein Messlauf kostet 800 Aufrufe und anderthalb Stunden; eine
Neuauswertung kostet Sekunden.

DER KONKRETE ANLASS. `pruefe_nachweis_grundmenge.py` beanstandete am Lauf vom
09.08. zwei Punkte, und einer davon ist hier heilbar: die Stichprobe umfasst
zehn Tage, und der **31.07. allein stellt 34,8 %** - derselbe Tag, an dem der
Mistral-Verhaltensbruch dokumentiert ist. Mit `--deckel-je-tag` laesst sich das
glaetten und nachsehen, ob der Befund davon abhaengt. Haelt er, ist er
robuster; kippt er, war er ein Tagesartefakt.

    python werte_fakt_nachweis_neu_aus.py --db <kopie.db> \
        --protokoll fakt_nachweis_echt.json --fakt liquiditaetszonen \
        [--deckel-je-tag 20] [--ohne-tag 2026-07-31] [--horizont 7]
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sqlite3
import sys
from collections import Counter, defaultdict

import bewerte_fakt_wirkung as nw
from agent.krypto.backward_tracking import lade_kursreihen
from laufe_fakt_nachweis import _lade_faelle


def _antworten_je_arm(protokoll_pfad: str) -> dict:
    daten = json.loads(pathlib.Path(protokoll_pfad).read_text(encoding="utf-8"))
    je_arm: dict = {}
    for e in daten.get("rohantworten", []):
        if "antwort" not in e or e.get("fall_id") is None:
            continue
        je_arm.setdefault(e["arm"], {})[e["fall_id"]] = e["antwort"]
    return {"vorab": daten.get("vorab", {}), "antworten": je_arm}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True)
    p.add_argument("--protokoll", required=True)
    p.add_argument("--fakt", required=True)
    p.add_argument("--horizont", type=int, default=None,
                   help="abweichend vom Originallauf")
    p.add_argument("--deckel-je-tag", type=int, default=0,
                   help="hoechstens so viele Faelle je Kalendertag (0 = kein Deckel)")
    p.add_argument("--ohne-tag", action="append", default=[],
                   help="diesen Tag ganz weglassen, mehrfach angebbar")
    p.add_argument("--nur-richtung", choices=["LONG", "SHORT"])
    args = p.parse_args()

    gespeichert = _antworten_je_arm(args.protokoll)
    vorab = gespeichert["vorab"]
    antworten = gespeichert["antworten"]
    if not antworten:
        print("ABBRUCH: keine Rohantworten im Protokoll - stammt es aus einem "
              "Trockenlauf?")
        return 2

    horizont = args.horizont or vorab.get("horizont", 7)
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    reihen = lade_kursreihen(conn)
    faelle, _ = _lade_faelle(conn, reihen, vorab.get("horizont", 7), args.fakt,
                             vorab.get("deckel_je_symbol", 15))

    # --- Filter, in fester Reihenfolge -------------------------------------
    vorher = len(faelle)
    if args.ohne_tag:
        faelle = [f for f in faelle if f["created_at"] not in args.ohne_tag]
    if args.nur_richtung:
        faelle = [f for f in faelle if f["richtung"] == args.nur_richtung]
    if args.deckel_je_tag:
        je_tag: dict = defaultdict(list)
        for f in faelle:
            je_tag[f["created_at"]].append(f)
        gefiltert = []
        for tag in sorted(je_tag):
            eigene = je_tag[tag]
            if len(eigene) > args.deckel_je_tag:
                schritt = max(1, len(eigene) // args.deckel_je_tag)
                eigene = eigene[::schritt][:args.deckel_je_tag]
            gefiltert.extend(eigene)
        faelle = gefiltert

    # Nur Faelle, fuer die auch Antworten vorliegen.
    hat_alle = set.intersection(*(set(a) for a in antworten.values()))
    faelle = [f for f in faelle if f["id"] in hat_alle]

    tage = Counter(f["created_at"] for f in faelle)
    symbole = Counter(f["symbol"] for f in faelle)
    print(f"Originallauf: {vorab.get('faelle')} Faelle, Horizont "
          f"{vorab.get('horizont')}, Modus {vorab.get('modus')}")
    print(f"Neuauswertung: {len(faelle)} Faelle (von {vorher} nach Filtern), "
          f"Horizont {horizont}")
    if not faelle:
        print("ABBRUCH: nach den Filtern bleibt nichts uebrig.")
        return 2
    print(f"  Symbole {len(symbole)}, groesstes {max(symbole.values())/len(faelle):.1%}")
    print(f"  Tage {len(tage)}, groesster {max(tage.values())/len(faelle):.1%}")
    print()

    def provider_fuer(arm: str):
        tabelle = antworten[arm]

        def modell(fakten):
            return tabelle.get(fakten.get("_fall_id"), {"action": "HALTEN"})
        return modell

    # nachweisrahmen ruft die Arme in fester Reihenfolge A1, A2, B - der
    # Provider muss also wissen, der wievielte Aufruf er ist. Einfacher: die
    # drei Arme direkt bewerten und den Rahmen mit einem Provider fuettern,
    # der je Arm wechselt.
    reihenfolge = ["A1", "A2", "B"]
    zustand = {"i": 0, "gesehen": 0}

    def provider(fakten):
        arm = reihenfolge[min(zustand["i"], 2)]
        zustand["gesehen"] += 1
        if zustand["gesehen"] >= len(faelle):
            zustand["gesehen"] = 0
            zustand["i"] += 1
        tabelle = antworten.get(arm, {})
        return tabelle.get(fakten.get("_fall_id"), {"action": "HALTEN"})

    if set(reihenfolge) - set(antworten):
        print(f"HINWEIS: Protokoll enthaelt nur {sorted(antworten)} - "
              f"erwartet {reihenfolge}. Fehlende Arme antworten HALTEN.")

    n = nw.nachweisrahmen(provider, faelle, args.fakt, reihen, horizont=horizont)
    print(nw.bericht(n))
    print()
    print("Kein einziger LLM-Aufruf - alles aus dem gespeicherten Protokoll.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
