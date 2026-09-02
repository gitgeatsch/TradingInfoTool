# -*- coding: utf-8 -*-
"""Was braucht der neue Code, das auf dem Notebook NICHT ankommt?
(02.09.2026)

## Der Anlass

Nutzerfrage vor dem Scharfschalten: *„Du musst vorher prüfen, ob wir alle
wichtigen Punkte und Knoten haben — z. B. was ist mit der neuen Datenbank,
wie kommt die auf das NB?"*

⚠️ **`*.db` steht in `.gitignore`.** Ein `git pull` bringt Code, keine
Daten. Jede Datei, die der neue Code liest und die es auf dem Notebook
nicht gibt, ist ein **stiller** Ausfall — die Module sind fail-soft
gebaut, sie stürzen nicht ab, sie schweigen.

## Was hier geprüft wird

  1  welche Datendateien liest der PRODUKTIONScode (nicht die
     Messwerkzeuge)?
  2  welche davon sind neu oder haben sich geaendert?
  3  was passiert, wenn eine fehlt - Ausfall oder stilles Schweigen?
  4  welche Schema-Migrationen laufen beim Start?
  5  welche config-Schluessel sind neu?

    python pruefe_ausrollbarkeit.py
"""
import ast
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PRODUKTION = ("main.py", "agent", "scheduler", "ui", "database", "api",
              "indicators")


def _dateien():
    aus = []
    for p in PRODUKTION:
        if os.path.isfile(p):
            aus.append(p)
        elif os.path.isdir(p):
            for wurzel, _d, dateien in os.walk(p):
                aus += [os.path.join(wurzel, f) for f in dateien
                        if f.endswith(".py")]
    return aus


def main():
    print("=" * 88)
    print("1) WELCHE DATENDATEIEN LIEST DER PRODUKTIONSCODE?")
    print("=" * 88)
    treffer = {}
    for f in _dateien():
        try:
            text = open(f, encoding="utf-8").read()
        except Exception:                                    # noqa: BLE001
            continue
        # ⚠️ NUR DER AKTIVE CODE - Kommentare fliegen raus. Dieses Projekt
        # haelt Entferntes ausfuehrlich im Kommentar fest; ein `grep` faende
        # die geloeschte Zeile in ihrer eigenen Grabinschrift wieder.
        aktiv = "\n".join(z for z in text.splitlines()
                          if not z.lstrip().startswith("#"))
        for m in re.findall(r"[\"']((?:data/)?[\w/]+\.db)[\"']", aktiv):
            treffer.setdefault(m, set()).add(f)
    for datei in sorted(treffer):
        da = os.path.exists(datei)
        groesse = (os.path.getsize(datei) / 1e6) if da else 0
        print("  %-34s %-10s %6.0f MB   %s"
              % (datei, "vorhanden" if da else "FEHLT", groesse,
                 ", ".join(sorted(treffer[datei])[:2])))

    print()
    print("=" * 88)
    print("2) WELCHE SIND NEU ODER GEAENDERT SEIT origin/main?")
    print("=" * 88)
    try:
        alt = subprocess.run(["git", "show", "origin/main:agent/marktrang.py"],
                             capture_output=True, text=True).stdout
    except Exception:                                        # noqa: BLE001
        alt = ""
    for datei in sorted(treffer):
        neu_im_code = datei not in alt and any(
            "marktrang" in f for f in treffer[datei])
        if neu_im_code:
            print("  ⚠️ %-32s NEU im Produktionscode seit origin/main" % datei)

    print()
    print("=" * 88)
    print("3) WAS PASSIERT, WENN EINE FEHLT?")
    print("=" * 88)
    from agent import marktrang as MR
    for name in sorted(MR.MESSBASIS):
        pfad = MR.MESSBASIS[name][0]
        da = os.path.exists(pfad)
        MR._MESSBASIS_ZWISCHEN.pop(name, None)
        menge = MR.messbasis(name) if da else set()
        print("  %-10s -> %-34s %s, Messbasis %d Symbole"
              % (name, pfad, "da" if da else "FEHLT", len(menge)))
    print()
    print("  ⚠️ Fehlt eine Datei, liefert `messbasis()` eine LEERE Menge.")
    print("     `raenge()` ueberspringt die Groesse dann mit einem")
    print("     logger.error - der Lauf bricht NICHT ab. Fuer N-14 heisst")
    print("     das: die Stufe steht, bekommt nie einen Rang und notiert")
    print("     nur 'kein OI-Rang'. Sie waere gebaut und wirkungslos.")

    print()
    print("=" * 88)
    print("4) SCHEMA-MIGRATIONEN BEIM START")
    print("=" * 88)
    quelle = open("database/db.py", encoding="utf-8").read()
    baum = ast.parse(quelle)
    migr = [n.name for n in ast.walk(baum)
            if isinstance(n, ast.FunctionDef) and n.name.startswith("_migrate")]
    print("  %d Migrationsfunktionen in database/db.py" % len(migr))
    neu = [m for m in migr if m not in subprocess.run(
        ["git", "show", "origin/main:database/db.py"],
        capture_output=True, text=True).stdout]
    print("  davon NEU seit origin/main: %s" % (neu or "keine"))

    print()
    print("=" * 88)
    print("5) NEUE CONFIG-SCHLUESSEL")
    print("=" * 88)
    try:
        import config as CFG
        cfg = CFG.load_config()
    except Exception as exc:                                 # noqa: BLE001
        print("  config nicht lesbar: %s" % exc)
        return
    alt_cfg = subprocess.run(["git", "show", "origin/main:config.yaml"],
                             capture_output=True, text=True).stdout
    if not alt_cfg:
        print("  ⚠️ `config.yaml` liegt NICHT im Repo (steht in .gitignore).")
        print("     Neue Schluessel muessen von Hand aufs Notebook - oder")
        print("     der Code muss ohne sie auskommen. Gepruefte Vorgaben:")
        from agent import wiederholung as WH
        print("       wiederholung.VORGABE_STUNDEN = %s" % WH.VORGABE_STUNDEN)
        from agent import potential as PT
        for name in dir(PT):
            if name.isupper() and "SCHWELLE" in name:
                print("       potential.%s = %s" % (name, getattr(PT, name)))


if __name__ == "__main__":
    main()
