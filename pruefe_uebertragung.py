"""Uebertragung der REGEL0-Datenbasis Desktop -> Notebook per USB pruefen (Schritt 7, S7-1; Voranalyse_Schritt7_Betrieb_02_10.md F3).

Nutzer 02.10.: *"rascher Einsatz am NB, wuerde eine fertige und gepruefte Datei auf das NB per USB kopieren"*. Gleichheit wird ueber eine
PRUEFSUMME (SHA-256) je Datei nachgewiesen, dazu Groesse, Symbolzahl und Zeilenzahl - so ist die Grundgesamtheit am Notebook dieselbe wie in
der Messung (CLAUDE.md: Grundgesamtheit ist keine Stellschraube).

    python pruefe_uebertragung.py --erstellen <ordner>     # am DESKTOP: kopiert die vier Dateien in <ordner> und schreibt manifest.json
    python pruefe_uebertragung.py --pruefen <ordner>       # an JEDEM Geraet: rechnet die Pruefsummen in <ordner> nach (nur lesen)
    python pruefe_uebertragung.py --abgleich               # am DESKTOP: data/ gegen die Referenz im Repo (REFERENZ), nur lesen

ABGLEICH (G17, 03.11.2026): am Desktop schreibt NIEMAND in diese vier Dateien (der Stundenjob nur am NB, S7-1b) - sie muessen also
bitgleich zum Stand vom 02.10. sein. Am 03.11. waren sie es nicht: EIN gekipptes Bit im Windows-Dateicache (Arbeitsspeicher), auf der
SSD stand das richtige Byte. R-R11-1 fiel dadurch auf 10.735 statt 10.732 Einstiege, und erst ein halber Tag Suche fand die Ursache.
Der Abgleich sagt es in Sekunden. Weicht eine Datei ab, prueft `struktur` (PRAGMA integrity_check), WELCHER Fall vorliegt:
    Struktur DEFEKT  -> Datei oder Cache beschaedigt (so am 03.11.); NICHT ueberschreiben, erst ungepuffert lesen (Voranalyse G14 Par. 7)
    Struktur ok      -> der Inhalt ist ein anderer: gewollt geaendert (dann neue Referenz) oder ein Bit in einem WERT
Eine neue Referenz entsteht nur bewusst: --erstellen, dann deren manifest.json nach REFERENZ kopieren (R-R11: dieselbe Basis wie die Messung).

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
REFERENZ = os.path.join(HIER, "Basisinfos", "Rechenkern_02_10", "kursdateien_manifest_02_10.json")   # im Repo, nicht nur in data/
from agent.regel0_nachlader import DATEIEN, betrieb_erlaubt   # eine Liste fuer Uebertragung, Nachlader und Abgleich
TABELLE = {"stundenkurse.db": "stundenkurse", "stundenkurse_alle.db": "stundenkurse",
           "markpreis_historie.db": "markpreis", "markpreis_alle.db": "markpreis"}


def sha(pfad):
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def struktur(pfad) -> str:
    """PRAGMA integrity_check, nur lesend: "ok", "gesperrt: ..." oder die ersten Meldungen. Eine Datei, die SQLite gar nicht oeffnen
    kann oder deren Groesse nicht zur Seitenzahl passt (auch 0 Byte - SQLite nimmt eine leere Datei als gueltig), ist defekt.
    Gesperrt ist KEIN Defekt: dann schreibt gerade jemand (am NB der Stundenjob) - timeout=1, damit die Pruefung ihn nicht aufhaelt."""
    try:
        c = sqlite3.connect("file:%s?mode=ro" % pfad.replace("\\", "/"), uri=True, timeout=1)
        try:
            z = [r[0] for r in c.execute("PRAGMA integrity_check(5)")]
            seiten, groesse = c.execute("PRAGMA page_count").fetchone()[0], c.execute("PRAGMA page_size").fetchone()[0]
        finally:
            c.close()
    except sqlite3.OperationalError as ex:
        if "locked" in str(ex).lower() or "busy" in str(ex).lower():
            return "gesperrt: %s" % ex
        return "nicht lesbar: %s" % ex
    except sqlite3.DatabaseError as ex:
        return "nicht lesbar: %s" % ex
    if not seiten or seiten * groesse != os.path.getsize(pfad):
        z = [m for m in z if m != "ok"] + ["Groesse %d Byte passt nicht zu %d Seiten x %d" % (os.path.getsize(pfad), seiten, groesse)]
    return "ok" if z == ["ok"] else " | ".join(z)


def abgleich_erlaubt(ordner) -> tuple:
    """Bitgleichheit gilt nur, wo NIEMAND schreibt: nicht am Betriebsgeraet, dort schreibt der Stundenjob die Dateien fort
    (`regel0_nachlader.betrieb_erlaubt`, S7-1b). Die Bedingung steht hier, damit Kommandozeile und Suite dieselbe benutzen."""
    nb, grund = betrieb_erlaubt(ordner)
    return (False, "Betriebsgeraet - die Dateien wachsen dort stuendlich (%s)" % grund) if nb else (True, grund)


def abgleich(ordner, man, mit_struktur=True) -> list:
    """Jede Datei des Manifests in <ordner> gegen ihre Pruefsumme, nur lesend. Urteil je Datei: gleich / fehlt /
    abweichend, Struktur ok / abweichend, Struktur DEFEKT - die Struktur wird nur bei Abweichung geprueft (bei gleicher
    Pruefsumme ist sie die der Referenz). `mit_struktur=False` laesst integrity_check weg (am Betriebsgeraet: keine Lesesperre
    neben dem Stundenjob)."""
    aus = []
    for d, soll in man["dateien"].items():
        p = os.path.join(ordner, d)
        z = {"datei": d, "soll": soll["sha256"]}
        if not os.path.exists(p):
            z["urteil"] = "fehlt"
            aus.append(z)
            continue
        z["ist"], z["bytes"] = sha(p), os.path.getsize(p)
        if z["ist"] == soll["sha256"] and z["bytes"] == soll["bytes"]:
            z["urteil"] = "gleich"
        elif not mit_struktur:
            z["urteil"] = "abweichend"
        else:
            z["struktur"] = struktur(p)
            z["urteil"] = ("abweichend, Struktur ok" if z["struktur"] == "ok" else
                           "abweichend, Struktur nicht pruefbar (gesperrt)" if z["struktur"].startswith("gesperrt") else
                           "abweichend, Struktur DEFEKT")
        aus.append(z)
    return aus


def _zeige(ordner, man) -> int:
    fehler = 0
    for z in abgleich(ordner, man, mit_struktur=abgleich_erlaubt(ordner)[0]):
        soll = man["dateien"][z["datei"]]
        ok = z["urteil"] == "gleich"
        fehler += 0 if ok else 1
        print("  %s %s · Pruefsumme %s · %d Symbole · %s Zeilen%s" % (
            "✔" if ok else "⛔ %s" % z["urteil"].upper(), z["datei"], z.get("ist", "-")[:16], soll["symbole"],
            f"{soll['zeilen']:,}".replace(",", "."), "" if ok or "struktur" not in z else " · Struktur: %s" % z["struktur"]))
    return fehler


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
        print("PRUEFUNG der Uebertragung gegen manifest.json vom %s · Ordner %s" % (man["erstellt"], os.path.abspath(ordner)))
        fehler = _zeige(ordner, man)
        print("SCHLUSS: %s" % ("✔ alle vier Dateien identisch" if not fehler else "⛔ %d Datei(en) weichen ab - nicht verwenden" % fehler))
        return 0 if not fehler else 1
    if "--abgleich" in sys.argv:
        man = json.load(open(REFERENZ, encoding="utf-8"))
        ordner = os.path.join(HIER, "data")
        erlaubt, grund = abgleich_erlaubt(ordner)
        if not erlaubt:
            print("ABGLEICH entfaellt an diesem Geraet: %s" % grund)
            return 0
        print("ABGLEICH der Kursdateien in %s gegen die Referenz vom %s (%s)" % (ordner, man["erstellt"], os.path.relpath(REFERENZ, HIER)))
        fehler = _zeige(ordner, man)
        print("SCHLUSS: %s" % ("✔ alle Dateien bitgleich zur Referenz" if not fehler else
                               "⛔ %d Datei(en) weichen ab - NICHT ueberschreiben, erst ungepuffert lesen (Voranalyse G14 Par. 7)" % fehler))
        return 0 if not fehler else 1
    print(__doc__)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
