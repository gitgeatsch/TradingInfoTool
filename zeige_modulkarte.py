# -*- coding: utf-8 -*-
"""Was kann dieses System? - die Landkarte aus den Modulkoepfen (27.08.2026).

DER ANLASS IST EIN NUTZERBEFUND, woertlich: *"das ist ein problem des
projektes dass du immer nur die haelfte der infos bei der ausarbeitung kennst
dann bleibt immer etwas liegen"*.

Er ist belegt. In EINER Sitzung wurde sechsmal als fehlend gemeldet, was
gebaut war:

    "Staking bei VERKAUFEN ungeprueft"   -> verkaufsrechnung zieht es ab
    "REDUZIEREN nennt keinen Anteil"     -> TEIL_ANTEIL = 1/3
    "keine Position mit These"           -> Verkaufsseite hat Einstand + G/V
    "Strategie je Asset fehlt"           -> `rolle: core`, 13 Assets
    "welche sind Kern?"                  -> GUI-Schalter nennt BTC/ETH/SOL
    "Begruendung als Wahrscheinlichkeit" -> wahrscheinlichkeit.py

DIE URSACHE IST NICHT NACHLAESSIGKEIT, SONDERN DIE SUCHFORM. Wer `grep` nach
einer Vermutung absetzt, findet die Vermutung - nie das, wonach er nicht
gesucht hat. Bei ueber zweihundert Modulen ist das systematisch.

WARUM GENERIERT UND NICHT GESCHRIEBEN. Ein handgepflegtes Verzeichnis ist am
Tag seiner Anlage richtig und danach nie wieder - dieselbe Falle wie ein
ueberholtes Bestandsdokument. Dieses hier liest die ERSTE ZEILE jedes
Modul-Docstrings; sie ist im Projekt durchgaengig eine Aussage darueber, was
das Modul tut. Veraltet der Kopf, veraltet der Code mit ihm.

    python zeige_modulkarte.py                 alles, nach Ordner
    python zeige_modulkarte.py --suche verkauf  nur Treffer
    python zeige_modulkarte.py --tot            nur Module OHNE Aufrufer
"""
from __future__ import annotations

import argparse
import ast
import io
import os
import sys

# Wo Produktionscode liegt. Messwerkzeuge im Wurzelverzeichnis stehen
# bewusst NICHT hier - sie haben ihren eigenen Werkzeugkasten.
ORDNER = ("agent", "api", "database", "scheduler", "importer", "ui",
          "indicators", "remote")


def _kopfzeile(pfad: str) -> str:
    """Die erste Zeile des Modul-Docstrings, oder ein Hinweis."""
    try:
        quelle = io.open(pfad, encoding="utf-8").read()
    except (OSError, UnicodeDecodeError):
        return "(nicht lesbar)"
    try:
        baum = ast.parse(quelle)
    except SyntaxError:
        return "(Syntaxfehler)"
    doc = ast.get_docstring(baum)
    if not doc:
        return "(ohne Modulkopf)"
    return doc.strip().splitlines()[0].strip()


def _module() -> list[tuple[str, str, str]]:
    """(Ordner, Dateiname, Kopfzeile) fuer jedes Modul."""
    aus = []
    for ordner in ORDNER:
        if not os.path.isdir(ordner):
            continue
        for wurzel, _dirs, dateien in os.walk(ordner):
            if "__pycache__" in wurzel:
                continue
            for name in sorted(dateien):
                if not name.endswith(".py") or name == "__init__.py":
                    continue
                pfad = os.path.join(wurzel, name)
                aus.append((wurzel.replace("\\", "/"), name, _kopfzeile(pfad)))
    return sorted(aus)


def _hat_aufrufer(ordner: str, name: str, alle: list) -> bool:
    """Wird das Modul irgendwo importiert? Grobe, aber ehrliche Naeherung.

    ⚠️ SIE IRRT IN BEIDE RICHTUNGEN: ein Modul kann dynamisch geladen werden
    (dann sieht es tot aus, ist es aber nicht), und ein Import in einer toten
    Datei zaehlt hier als Aufrufer. Deshalb "Verdacht", nicht "Befund"."""
    stamm = name[:-3]
    muster = (f"import {stamm}", f"from {ordner.replace('/', '.')} import",
              f".{stamm} import", f"import {ordner.replace('/', '.')}.{stamm}")
    for o, n, _k in alle:
        if o == ordner and n == name:
            continue
        try:
            q = io.open(os.path.join(o, n), encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        if any(m in q for m in muster) and stamm in q:
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suche", default=None,
                    help="nur Module, deren Name oder Kopf das enthaelt")
    ap.add_argument("--tot", action="store_true",
                    help="nur Module ohne erkennbaren Aufrufer")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    alle = _module()
    if a.suche:
        s = a.suche.lower()
        alle = [x for x in alle if s in x[1].lower() or s in x[2].lower()]

    if a.tot:
        alle = [x for x in alle if not _hat_aufrufer(x[0], x[1], _module())]
        print("=" * 78)
        print("MODULE OHNE ERKENNBAREN AUFRUFER - Verdacht, kein Befund")
        print("=" * 78)
    else:
        print("=" * 78)
        print(f"MODULKARTE - {len(alle)} Module"
              + (f", Suche '{a.suche}'" if a.suche else ""))
        print("=" * 78)

    letzter = None
    for ordner, name, kopf in alle:
        if ordner != letzter:
            print(f"\n{ordner}/")
            letzter = ordner
        if len(kopf) > 88:
            kopf = kopf[:85] + "..."
        print(f"   {name[:-3]:28s} {kopf}")

    if not alle:
        print("\n   nichts gefunden")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
