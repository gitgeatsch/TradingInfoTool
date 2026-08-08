"""Haelt der Befund, wenn man an der Stichprobe ruettelt? Ohne neue Aufrufe.

WOZU. Ein einzelnes Urteil aus einem Messlauf sagt wenig. Die Regel des
Projekts lautet: *"Eine Tendenz zaehlt nur, wenn sie beim Vergroessern der
Stichprobe HAELT ODER WAECHST - nicht wenn sie schrumpft"* (Mappe Kapitel 9,
zweimal unabhaengig belegt). Dasselbe gilt fuer das Ruetteln in die andere
Richtung: haengt ein Befund an einem Tag, an einer Richtung oder an einem
Horizont, ist er keiner.

Dieses Skript faehrt dieselbe Auswertung ueber mehrere Schnitte und stellt die
Urteile nebeneinander. **Kein einziger LLM-Aufruf** - alles aus dem
gespeicherten Protokoll.

DIE SCHNITTE, und warum genau diese:

    vollstaendig        der Referenzlauf
    ohne 31.07.         dieser eine Tag stellt 34,8 % der Faelle, und er ist
                        der Tag, an dem die Vorschlagsrichtung kippte
    Tages-Deckel 15     glaettet die zeitliche Ballung insgesamt
    nur LONG            133 der 201 Faelle
    nur SHORT           68 der 201 - und davon 76,5 % aus EINEM Tag
    Horizont 5 / 14     haengt das Urteil an der Beobachtungsdauer?

LESEART. Stimmen alle Schnitte ueberein, ist der Befund robust. Kippt er bei
einem, gehoert genau dieser Schnitt in die Ergebnisdarstellung - nicht in eine
Fussnote. Das ist keine Statistik, sondern Buchfuehrung ueber die eigene
Unsicherheit.

    python pruefe_nachweis_robustheit.py --db <kopie.db> \
        --protokoll fakt_nachweis_echt.json --fakt liquiditaetszonen
"""
from __future__ import annotations

import argparse
import subprocess
import sys


SCHNITTE = [
    ("vollstaendig", []),
    ("ohne 31.07.", ["--ohne-tag", "2026-07-31"]),
    ("Tages-Deckel 15", ["--deckel-je-tag", "15"]),
    ("nur LONG", ["--nur-richtung", "LONG"]),
    ("nur SHORT", ["--nur-richtung", "SHORT"]),
    ("Horizont 5", ["--horizont", "5"]),
    ("Horizont 14", ["--horizont", "14"]),
]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True)
    p.add_argument("--protokoll", required=True)
    p.add_argument("--fakt", required=True)
    args = p.parse_args()

    print(f"ROBUSTHEIT: {args.fakt}")
    print(f"{'Schnitt':18} {'n':>5} {'Sym':>4} {'Wirkung':>9} {'Intervall':>20} "
          f"{'wild p':>7}  Urteil")
    print("-" * 100)

    urteile = []
    for name, zusatz in SCHNITTE:
        ergebnis = subprocess.run(
            [sys.executable, "werte_fakt_nachweis_neu_aus.py",
             "--db", args.db, "--protokoll", args.protokoll,
             "--fakt", args.fakt, *zusatz],
            capture_output=True, text=True, encoding="utf-8", errors="replace")
        zeilen = (ergebnis.stdout or "").splitlines()
        werte = {"n": "-", "sym": "-", "wirkung": "-", "ci": "-",
                 "wild": "-", "urteil": "?"}
        for z in zeilen:
            s = z.strip()
            if s.startswith("Wirkung (B gegen A):"):
                werte["wirkung"] = s.split(":")[1].strip().split(" R")[0]
                if "gepaart ueber" in s:
                    werte["n"] = s.split("gepaart ueber")[1].split()[0]
            elif s.startswith("Vertrauensbereich:"):
                werte["ci"] = s.split(":")[1].strip().split(")")[0].strip()
                if werte["ci"].startswith("["):
                    werte["ci"] = werte["ci"].split("]")[0] + "]"
            elif s.startswith("Wild-Cluster-Test:"):
                werte["wild"] = s.split("=")[1].strip().split()[0]
            elif s.startswith("Effektive Stichprobe:"):
                werte["sym"] = s.split(":")[1].strip().split()[0]
            elif s.startswith("URTEIL zum Fakt:"):
                werte["urteil"] = s.split(":", 1)[1].strip()
        if ergebnis.returncode != 0 and werte["urteil"] == "?":
            werte["urteil"] = f"(Lauf fehlgeschlagen, Code {ergebnis.returncode})"
        urteile.append(werte["urteil"])
        print(f"{name:18} {werte['n']:>5} {werte['sym']:>4} {werte['wirkung']:>9} "
              f"{werte['ci']:>20} {werte['wild']:>7}  {werte['urteil']}")

    print("-" * 100)
    eindeutig = {u.split(":")[0] for u in urteile if u not in ("?",)}
    if len(eindeutig) <= 1:
        print("ROBUST: alle Schnitte kommen zum selben Urteil.")
    else:
        print(f"NICHT ROBUST: {len(eindeutig)} verschiedene Urteile "
              f"({', '.join(sorted(eindeutig))}).")
        print("Der Befund haengt an der Stichprobenwahl. Welcher Schnitt ihn")
        print("kippt, gehoert in die Ergebnisdarstellung - nicht in eine Fussnote.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
