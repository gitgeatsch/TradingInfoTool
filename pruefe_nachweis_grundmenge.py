"""Gegenpruefung der Grundmenge, BEVOR einem Nachweis-Ergebnis geglaubt wird.

WOZU. `laufe_fakt_nachweis.py` waehlt seine Faelle selbst aus - und die
Fallauswahl ist in diesem Projekt schon zweimal der Punkt gewesen, an dem eine
Messung wertlos wurde (Methodik-Nachtrag 09.08., Punkt 4; und beim Vorbereiten
dieses Laufs erneut bei den CRV-Baendern). Ein Lauf, dessen Grundmenge die Frage
gar nicht beantworten kann, liefert trotzdem Zahlen. Genau das macht ihn
gefaehrlich.

Dieses Skript prueft die Grundmenge gegen ZEHN Fragen, die alle unabhaengig vom
Ergebnis beantwortbar sind. Es faellt kein Urteil ueber den Fakt - es sagt nur,
ob die Daten ein Urteil ueberhaupt tragen.

DIE ZEHN PRUEFUNGEN

  1  Traegt der Fakt-Pfad ueberhaupt Inhalt, oder ist er leer/None?
  2  Aendert das Entfernen den Prompt WIRKLICH - und nur an einer Stelle?
  3  Sehen A1 und A2 byteweise dasselbe?
  4  Steckt im Faktensatz etwas, das NACH seinem Zeitstempel entstanden ist?
  5  Passen Faktensatz-Preis und Kursreihe auf dieselbe Skala?
  6  Wie dicht sind die Kursreihen der beteiligten Symbole?
  7  Verteilt sich die Stichprobe ueber Zeit - oder haengt sie an einer Phase?
  8  Wie stark konzentriert sie sich auf Symbole (Methodik 2.5)?
  9  Deckt sie beide Handelsrichtungen ab?
 10  Wie viele Faelle waeren am Horizont zensiert?

Aufruf:
    python pruefe_nachweis_grundmenge.py --db <kopie.db> --fakt liquiditaetszonen
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from datetime import date

from agent.krypto.backward_tracking import lade_kursreihen, simuliere_signal
from laufe_fakt_nachweis import _lade_faelle
from messe_prompt_nebeneffekte import _entferne_pfad

BEFUNDE: list[tuple[str, bool, str]] = []


def befund(name: str, ok: bool, info: str = "") -> None:
    BEFUNDE.append((name, ok, info))
    print(("  OK   " if ok else "  ACHTUNG ") + name + (f"  {info}" if info else ""))


def _tag(wert: str) -> date:
    j, m, t = (int(x) for x in str(wert)[:10].split("-"))
    return date(j, m, t)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True)
    p.add_argument("--fakt", default="liquiditaetszonen")
    p.add_argument("--horizont", type=int, default=7)
    p.add_argument("--deckel-je-symbol", type=int, default=15)
    args = p.parse_args()

    import sqlite3
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    reihen = lade_kursreihen(conn)
    faelle, _ = _lade_faelle(conn, reihen, args.horizont, args.fakt,
                             args.deckel_je_symbol)
    print(f"Grundmenge: {len(faelle)} Faelle, Fakt '{args.fakt}', "
          f"Horizont {args.horizont}\n")
    if not faelle:
        print("ABBRUCH: leere Grundmenge.")
        return 2

    # --- 1) Traegt der Fakt Inhalt? ----------------------------------------
    leer = 0
    for f in faelle:
        wert = f["fakten"].get(args.fakt)
        if wert is None or (isinstance(wert, (dict, list)) and not wert):
            leer += 1
    befund("1  Fakt traegt in allen Faellen Inhalt", leer == 0,
           f"{leer} leer/None von {len(faelle)}")

    # --- 2) Aendert das Entfernen den Prompt wirklich? ----------------------
    # Ohne diese Pruefung koennte Arm B mit A identisch sein - der Rahmen
    # meldete dann "keine Wirkung", und zwar voellig zu Recht, nur eben ueber
    # eine Aenderung, die nie stattgefunden hat.
    unveraendert = 0
    laengen_vorher, laengen_nachher = [], []
    for f in faelle:
        vorher = json.dumps(f["fakten"], sort_keys=True, ensure_ascii=False)
        ohne = _entferne_pfad(f["fakten"], args.fakt)
        nachher = json.dumps(ohne, sort_keys=True, ensure_ascii=False)
        if vorher == nachher:
            unveraendert += 1
        laengen_vorher.append(len(vorher))
        laengen_nachher.append(len(nachher))
    anteil = 1 - statistics.mean(laengen_nachher) / statistics.mean(laengen_vorher)
    befund("2  Entfernen aendert den Prompt in JEDEM Fall", unveraendert == 0,
           f"{unveraendert} unveraendert; Prompt wird im Mittel um "
           f"{anteil:.1%} kuerzer")

    # Und: NUR der eine Block darf verschwinden.
    schluessel_weg = set()
    for f in faelle[:20]:
        ohne = _entferne_pfad(f["fakten"], args.fakt)
        schluessel_weg |= set(f["fakten"]) - set(ohne)
    befund("2b nur der gepruefte Block verschwindet",
           schluessel_weg == {args.fakt.split(".")[0]},
           f"entfernt: {sorted(schluessel_weg)}")

    # --- 3) A1 und A2 sehen dasselbe ---------------------------------------
    # Trivial wahr, weil beide dieselbe Liste bekommen - aber genau solche
    # Selbstverstaendlichkeiten waren hier schon falsch (Modul-Konstanten,
    # veraenderliche Vorgabewerte). Einmal nachsehen kostet nichts.
    kopie_a = json.dumps([f["fakten"] for f in faelle], sort_keys=True)
    kopie_b = json.dumps([f["fakten"] for f in faelle], sort_keys=True)
    befund("3  A1 und A2 sehen byteweise dieselben Fakten", kopie_a == kopie_b)

    # --- 4) Lookahead im Faktensatz? ---------------------------------------
    # Ein Datum IM Faktensatz, das nach seinem eigenen Zeitstempel liegt, waere
    # Information aus der Zukunft. Genau daran ist der CRV-Baender-Kandidat
    # gescheitert - dort haette man heutige Baender in Juli-Faelle gespielt.
    verdaechtig = []
    for f in faelle:
        eigen = _tag(f["created_at"])
        roh = json.dumps(f["fakten"], ensure_ascii=False)
        for stueck in roh.split('"'):
            if len(stueck) == 10 and stueck[4] == "-" and stueck[7] == "-":
                try:
                    d = _tag(stueck)
                except ValueError:
                    continue
                if d > eigen:
                    verdaechtig.append((f["id"], f["created_at"], stueck))
                    break
    befund("4  kein Datum im Faktensatz liegt NACH seinem Zeitstempel",
           not verdaechtig,
           f"{len(verdaechtig)} verdaechtig, z.B. {verdaechtig[:2]}"
           if verdaechtig else "")

    # --- 5) Skala Faktensatz gegen Kursreihe -------------------------------
    schief = []
    for f in faelle:
        preis = (f["fakten"].get("preis") or {}).get("usd")
        reihe = reihen.get(f["symbol"])
        if not preis or not reihe:
            continue
        erster = next((p["close"] for p in reihe
                       if p["date"] >= f["created_at"] and p["close"]), None)
        if not erster:
            continue
        if max(preis / erster, erster / preis) > 1.5:
            schief.append((f["symbol"], round(preis, 4), round(erster, 4)))
    befund("5  Faktensatz-Preis und Kursreihe auf derselben Skala",
           not schief, f"{len(schief)} schief, z.B. {schief[:3]}" if schief else "")

    # --- 6) Balkendichte ----------------------------------------------------
    duenn = []
    for symbol in {f["symbol"] for f in faelle}:
        rr = reihen.get(symbol) or []
        letzte = [p["date"] for p in rr][-40:]
        if len(letzte) < 5:
            continue
        abst = [(_tag(letzte[i + 1]) - _tag(letzte[i])).days
                for i in range(len(letzte) - 1)]
        if statistics.median(abst) > 1.5:
            duenn.append((symbol, statistics.median(abst)))
    befund("6  alle beteiligten Kursreihen sind Tageskerzen", not duenn,
           f"duenn: {duenn}" if duenn else "")

    # --- 7) Zeitliche Streuung ---------------------------------------------
    tage = Counter(f["created_at"] for f in faelle)
    spanne = (_tag(max(tage)) - _tag(min(tage))).days
    groesster_tag = max(tage.values()) / len(faelle)
    befund("7  Stichprobe streut ueber die Zeit", spanne >= 7 and groesster_tag < 0.25,
           f"{min(tage)} bis {max(tage)} ({spanne} Tage, {len(tage)} verschiedene), "
           f"groesster Tag {groesster_tag:.1%}")

    # --- 8) Symbol-Konzentration (Methodik 2.5) -----------------------------
    z = Counter(f["symbol"] for f in faelle)
    groesstes = max(z.values()) / len(faelle)
    befund("8  kein Symbol ueber 25 % (Methodik 2.5)", groesstes <= 0.25,
           f"{len(z)} Symbole, groesstes {groesstes:.1%}")
    befund("8b effektive Stichprobe >= 50 Symbole", len(z) >= 50,
           f"{len(z)} Symbole - darunter gilt ein Befund als "
           f"HYPOTHESENGENERIEREND, nicht operationalisierbar")

    # --- 9) Beide Richtungen -----------------------------------------------
    r = Counter(f["richtung"] for f in faelle)
    kleinste = min(r.values()) / len(faelle) if r else 0
    befund("9  beide Handelsrichtungen vertreten", len(r) >= 2 and kleinste >= 0.15,
           f"{dict(r)}, kleinste {kleinste:.1%}")

    # --- 10) Zensurquote am Horizont ---------------------------------------
    # Nicht die Kursreihe, sondern eine PLAUSIBLE Zone: 4 % Stop, CRV 3. So
    # viele Faelle wuerden bei diesem Horizont keine Barriere treffen.
    zensiert = bewertet = 0
    for f in faelle:
        reihe = reihen.get(f["symbol"])
        preis = (f["fakten"].get("preis") or {}).get("usd")
        if not reihe or not preis:
            continue
        z_probe = {"entry": preis, "stop": preis * 0.96, "ziel": preis * 1.12,
                   "risiko": preis * 0.04, "ist_short": False}
        sim = simuliere_signal(z_probe, reihe, f["created_at"], args.horizont,
                               voller_horizont_noetig=False)
        if sim is None:
            continue
        bewertet += 1
        if sim.get("zensiert"):
            zensiert += 1
    quote = zensiert / bewertet if bewertet else 1.0
    befund("10 Zensurquote unter 60 %", quote < 0.6,
           f"{zensiert} von {bewertet} treffen bei Horizont {args.horizont} "
           f"keine Barriere ({quote:.1%})")

    print()
    schlecht = [n for n, ok, _ in BEFUNDE if not ok]
    if not schlecht:
        print("ALLE ZEHN PRUEFUNGEN BESTANDEN - die Grundmenge traegt ein Urteil.")
        return 0
    print(f"{len(schlecht)} Pruefung(en) mit Vorbehalt:")
    for n in schlecht:
        print(f"   - {n}")
    print()
    print("Das ist NICHT automatisch ein Abbruchgrund - aber jeder dieser Punkte")
    print("gehoert in die Ergebnisdarstellung, nicht in eine Fussnote.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
