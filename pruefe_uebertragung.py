"""Uebertragung der REGEL0-Datenbasis Desktop -> Notebook per USB pruefen (Schritt 7, S7-1; Voranalyse_Schritt7_Betrieb_02_10.md F3).

Nutzer 02.10.: *"rascher Einsatz am NB, wuerde eine fertige und gepruefte Datei auf das NB per USB kopieren"*. Gleichheit wird ueber eine
PRUEFSUMME (SHA-256) je Datei nachgewiesen, dazu Groesse, Symbolzahl und Zeilenzahl - so ist die Grundgesamtheit am Notebook dieselbe wie in
der Messung (CLAUDE.md: Grundgesamtheit ist keine Stellschraube).

    python pruefe_uebertragung.py --erstellen <ordner>     # am DESKTOP: kopiert die vier Dateien in <ordner> und schreibt manifest.json
    python pruefe_uebertragung.py --pruefen <ordner>       # an JEDEM Geraet: rechnet die Pruefsummen in <ordner> nach (nur lesen)

Die Dateien werden nur LESEND geoeffnet (Pruefsumme, mode=ro); das Kopieren am Desktop liest die Quelle nur.
Beruehrt nie data/tradinginfotool.db.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime

HIER = os.path.dirname(os.path.abspath(__file__))
DATEIEN = ("stundenkurse.db", "stundenkurse_alle.db", "markpreis_historie.db", "markpreis_alle.db")
TABELLE = {"stundenkurse.db": "stundenkurse", "stundenkurse_alle.db": "stundenkurse",
           "markpreis_historie.db": "markpreis", "markpreis_alle.db": "markpreis"}


def sha(pfad):
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def kennzahlen(pfad, tab):
    c = sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True)
    n, s, lo, hi = c.execute("SELECT COUNT(*), COUNT(DISTINCT symbol), MIN(stunde), MAX(stunde) FROM %s" % tab).fetchone()
    c.close()
    return {"zeilen": n, "symbole": s, "von": lo, "bis": hi}


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    if "--erstellen" in sys.argv:
        ziel = sys.argv[sys.argv.index("--erstellen") + 1]
        os.makedirs(ziel, exist_ok=True)
        man = {"erstellt": datetime.now().strftime("%Y-%m-%d %H:%M"), "dateien": {}}
        for d in DATEIEN:
            q = os.path.join(HIER, "data", d)
            z = os.path.join(ziel, d)
            print("  kopiere %s (%.0f MB) ..." % (d, os.path.getsize(q) / 1e6), flush=True)
            shutil.copy2(q, z)
            hq, hz = sha(q), sha(z)
            if hq != hz:
                print("  ⛔ %s: Kopie weicht von der Quelle ab" % d)
                return 1
            man["dateien"][d] = {"sha256": hq, "bytes": os.path.getsize(q), **kennzahlen(z, TABELLE[d])}
            print("    ✔ %s · %d Symbole · %s Zeilen · %s .. %s" % (hq[:16], man["dateien"][d]["symbole"],
                                                              f"{man['dateien'][d]['zeilen']:,}".replace(",", "."), man["dateien"][d]["von"], man["dateien"][d]["bis"]))
        with open(os.path.join(ziel, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(man, f, indent=1, ensure_ascii=False)
        print("FERTIG: %s (4 Dateien + manifest.json). Am Notebook nach data/ kopieren, dann:  python pruefe_uebertragung.py --pruefen data" % ziel)
        return 0
    if "--pruefen" in sys.argv:
        ordner = sys.argv[sys.argv.index("--pruefen") + 1]
        mf = os.path.join(ordner, "manifest.json")
        if not os.path.exists(mf):
            print("⛔ manifest.json fehlt in %s (mit den Dateien mitkopieren)" % ordner)
            return 1
        man = json.load(open(mf, encoding="utf-8"))
        fehler = 0
        print("PRUEFUNG der Uebertragung gegen manifest.json vom %s · Ordner %s" % (man["erstellt"], os.path.abspath(ordner)))
        for d, soll in man["dateien"].items():
            p = os.path.join(ordner, d)
            if not os.path.exists(p):
                print("  ⛔ %s fehlt" % d); fehler += 1; continue
            ist = sha(p)
            ok = ist == soll["sha256"] and os.path.getsize(p) == soll["bytes"]
            fehler += 0 if ok else 1
            print("  %s %s · Pruefsumme %s · %d Symbole · %s Zeilen" % ("✔" if ok else "⛔ ABWEICHUNG", d, ist[:16], soll["symbole"],
                                                                  f"{soll['zeilen']:,}".replace(",", ".")))
        print("SCHLUSS: %s" % ("✔ alle vier Dateien identisch" if not fehler else "⛔ %d Datei(en) weichen ab - nicht verwenden" % fehler))
        return 0 if not fehler else 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
