# -*- coding: utf-8 -*-
"""ARCHIV - Messbasen, Rohdaten und Messlaeufe auffindbar und nachvollziehbar aufbewahren (29.09.2026).

Nutzer 29.09.: *„Wir haben kein Platzproblem - ich wuerde nur jene loeschen, welche nur
temporaer Sinn machen. Ein Archiv oder eine Sicherung macht nur Sinn, wenn man wieder
etwas findet und es nachvollziehbar ist."*

WO     Y:\\TradingInfoTool_Archiv  (Laufwerk BACKUP_DATA, eine ANDERE physische Platte als
       das Projekt auf D:) - der Index liegt dort UND im Projekt:
       Basisinfos/ARCHIV_INDEX.md (in Git, damit er mit dem Code gefunden wird)
AUFBAU
    messbasen/<JJJJ-MM-TT>/          Kopien von data/*.db + manifest.json (SHA-256, Groesse,
                                     Tabellen und Zeilen je Tabelle)
    rohdaten/<JJJJ-MM-TT>_<name>/    Rohabrufe (Teildateien der Lader u. a.) + manifest.json
    laeufe/<JJJJ-MM-TT_HHMM>_<kurz>_<menge>/
                                     ausgabe.txt + meta.json (Werkzeug, Commit des Werkzeugs,
                                     Menge, Befund, Urteilszeilen, Stand der Messbasen)
                                     [+ schaetzungen.npz, wenn ein Werkzeug sie liefert]
    INDEX.md, index.csv              erzeugt aus den meta.json - nie von Hand aendern
EINSATZ  erst beim ABSCHLUSS einer grossen Phase bzw. M1 (Nutzer 29.09.: *„ich dachte, wir
         starten damit, wenn wir M1 bzw. grosse Phasen abgeschlossen haben - sonst liegen diese
         nicht besser“*). Bis dahin bleibt alles, wo es ist. Die Laeufe sind reproduzierbar
         (Werkzeug vorab committet, R-R11), fehlende Schaetzungen lassen sich neu rechnen.
REGELN
    - es wird NICHTS geloescht: `verschiebe` kopiert, prueft die SHA-256 und entfernt erst
      dann die Quelle
    - die Liste der Messbasen wird aus data/*.db ABGELEITET, nicht aufgezaehlt; ausgenommen
      sind die Betriebsdateien (tradinginfotool.db, trading.db)
    - jeder Eintrag traegt den Commit des Werkzeugs -> `git show <commit>:<werkzeug>`

    python archiv.py messbasen [--mit-altstaenden]
    python archiv.py verschiebe data/_teile --name lader_teile
    python archiv.py lauf data/_vergleich/k5__bestand.txt [--befund 2.681] [--npz x.npz]
    python archiv.py nachtragen            # vorhandene Ausgaben einsammeln
    python archiv.py index
    python archiv.py suche K6 mark
"""
from __future__ import annotations

import argparse
import csv
import glob
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime

HIER = os.path.dirname(os.path.abspath(__file__))
ARCHIV = os.environ.get("TIT_ARCHIV", r"Y:\TradingInfoTool_Archiv")
INDEX_PROJEKT = os.path.join(HIER, "Basisinfos", "ARCHIV_INDEX.md")
BETRIEB = {"tradinginfotool.db", "trading.db"}
ALTSTAND = re.compile(r"_vor_", re.I)
# Werkzeug aus dem Dateinamen der Ausgabe - die LAENGEREN Vorsilben zuerst
WERKZEUG = [
    ("k5f", "messe_k5_folge.py"), ("k5_", "messe_k5_lage_vorlauf.py"),
    ("k6_", "messe_k6_hebelstufe.py"), ("k7_", "messe_k7_abgleich.py"),
    ("k1s2c", "messe_k1_schritt2c_beitrag.py"), ("mp_", "hole_markpreis.py"),
    ("K1_Wirkungskurven", "messe_k1_wirkungskurven.py"), ("K1_Schritt2c", "messe_k1_schritt2c_beitrag.py"),
    ("K1_Schritt2b", "messe_k1_schritt2b_kombination.py"), ("K1_Schritt2_", "messe_k1_schritt2_kombination.py"),
    ("K3_Kontextflaeche", "messe_k3_kontextflaeche.py"), ("K6_Hebelstufe", "messe_k6_hebelstufe.py"),
    ("K7_Abgleich", "messe_k7_abgleich.py"),
]
URTEIL = re.compile(r"(TOR:|R-R11|^\s*(T\d|S\d|J\d|P\d|V\d|Z\d)\b|✔|⛔|SCHLUSS)")


def sha256(pfad: str) -> str:
    h = hashlib.sha256()
    with open(pfad, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def git(*a) -> str:
    try:
        return subprocess.run(["git", *a], cwd=HIER, capture_output=True, text=True, check=True).stdout.strip()
    except Exception:                                         # noqa: BLE001
        return ""


def tabellen(pfad: str) -> dict:
    try:
        c = sqlite3.connect("file:%s?mode=ro" % pfad, uri=True)
        aus = {}
        for (t,) in c.execute("SELECT name FROM sqlite_master WHERE type='table'"):
            try:
                aus[t] = c.execute('SELECT COUNT(*) FROM "%s"' % t).fetchone()[0]
            except Exception:                                 # noqa: BLE001
                aus[t] = None
        c.close()
        return aus
    except Exception as exc:                                  # noqa: BLE001
        return {"_fehler": str(exc)[:80]}


def messbasen_stand() -> dict:
    """Groesse und Zeitstempel jeder Messbasis - der Stand, auf dem ein Lauf gerechnet hat."""
    return {os.path.basename(p): [os.path.getsize(p), datetime.fromtimestamp(os.path.getmtime(p)).isoformat(timespec="seconds")]
            for p in sorted(glob.glob(os.path.join(HIER, "data", "*.db")))
            if os.path.basename(p).lower() not in BETRIEB and not ALTSTAND.search(os.path.basename(p))}


def kopiere_mit_manifest(quellen: list, ziel: str, art: str, notiz: str = "") -> dict:
    os.makedirs(ziel, exist_ok=True)
    eintraege = []
    for q in quellen:
        z = os.path.join(ziel, os.path.basename(q))
        sq = sha256(q)
        if not (os.path.exists(z) and sha256(z) == sq):
            shutil.copy2(q, z)
        sz = sha256(z)
        if sz != sq:
            raise SystemExit("⛔ Pruefsumme weicht ab: %s" % q)
        e = dict(datei=os.path.basename(q), quelle=os.path.abspath(q), groesse=os.path.getsize(q), sha256=sq,
                 geaendert=datetime.fromtimestamp(os.path.getmtime(q)).isoformat(timespec="seconds"))
        if q.lower().endswith(".db"):
            e["tabellen"] = tabellen(z)
        eintraege.append(e)
        print("  ✔ %-45s %8.1f MB  sha256 %s…" % (e["datei"], e["groesse"] / 1048576, sq[:12]))
    m = dict(art=art, angelegt=datetime.now().isoformat(timespec="seconds"), notiz=notiz,
             projekt_commit=git("rev-parse", "--short", "HEAD"), dateien=eintraege)
    with open(os.path.join(ziel, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(m, f, ensure_ascii=False, indent=1)
    return m


def cmd_messbasen(a) -> int:
    alle = sorted(glob.glob(os.path.join(HIER, "data", "*.db")))
    q = [p for p in alle if os.path.basename(p).lower() not in BETRIEB
         and (a.mit_altstaenden or not ALTSTAND.search(os.path.basename(p)))]
    ziel = os.path.join(ARCHIV, "messbasen", datetime.now().strftime("%Y-%m-%d"))
    print("MESSBASEN -> %s (%d Dateien, %.1f GB)" % (ziel, len(q), sum(os.path.getsize(p) for p in q) / 2 ** 30))
    kopiere_mit_manifest(q, ziel, "messbasen", "Stand der Messbasen; Altstaende %s" % ("mit" if a.mit_altstaenden else "ohne"))
    cmd_index(a)
    return 0


def cmd_verschiebe(a) -> int:
    quelle = os.path.abspath(a.pfad)
    dateien = sorted(p for p in glob.glob(os.path.join(quelle, "**", "*"), recursive=True) if os.path.isfile(p)) \
        if os.path.isdir(quelle) else [quelle]
    ziel = os.path.join(ARCHIV, "rohdaten", "%s_%s" % (datetime.now().strftime("%Y-%m-%d"), a.name))
    print("VERSCHIEBE %d Dateien -> %s" % (len(dateien), ziel))
    kopiere_mit_manifest(dateien, ziel, "rohdaten", a.notiz or "verschoben aus %s" % quelle)
    for p in dateien:                                         # erst nach geprueftem Manifest
        os.remove(p)
    if os.path.isdir(quelle) and not os.listdir(quelle):
        os.rmdir(quelle)
    print("  ✔ Quelle entfernt, nachdem alle Pruefsummen gleich waren")
    cmd_index(a)
    return 0


def werkzeug_von(name: str) -> str:
    for vor, w in WERKZEUG:
        if name.startswith(vor) or ("/" + vor) in name.replace("\\", "/"):
            return w
    return "-"


def menge_von(name: str) -> str:
    m = re.search(r"(bestand|unverzerrt_\d)", name)
    return m.group(1).replace("_", ":") if m else "-"


def cmd_lauf(a, datei=None, befund=None, npz=None, still=False) -> str:
    datei = datei or a.datei
    befund = befund if befund is not None else getattr(a, "befund", None)
    npz = npz if npz is not None else getattr(a, "npz", None)
    name = os.path.basename(datei)
    rel = os.path.relpath(datei, HIER).replace("\\", "/")
    werk = werkzeug_von(rel if rel.startswith("Basisinfos/") else name)
    zeit = datetime.fromtimestamp(os.path.getmtime(datei))
    kommit = git("log", "-1", "--format=%h", "--before=%s" % zeit.isoformat(), "--", werk) if werk != "-" else ""
    sq = sha256(datei)
    for m in glob.glob(os.path.join(ARCHIV, "laeufe", "*", "meta.json")):
        if json.load(open(m, encoding="utf-8")).get("sha256") == sq:
            if not still:
                print("  = schon archiviert: %s" % os.path.dirname(m))
            return os.path.dirname(m)
    text = open(datei, encoding="utf-8", errors="replace").read()
    urteil = [z.strip() for z in text.splitlines() if URTEIL.search(z)][:60]
    kurz = re.sub(r"[^A-Za-z0-9]+", "_", os.path.splitext(name)[0])[:40]
    ordner = os.path.join(ARCHIV, "laeufe", "%s_%s" % (zeit.strftime("%Y-%m-%d_%H%M"), kurz))
    os.makedirs(ordner, exist_ok=True)
    shutil.copy2(datei, os.path.join(ordner, "ausgabe.txt"))
    if npz:
        shutil.copy2(npz, os.path.join(ordner, "schaetzungen.npz"))
    meta = dict(art="lauf", datei=name, quelle=rel, sha256=sq, ende=zeit.isoformat(timespec="seconds"),
                werkzeug=werk, werkzeug_commit=kommit, menge=menge_von(name), befund=befund or "",
                schaetzungen=bool(npz), urteil=urteil, messbasen_stand=messbasen_stand(),
                hinweis=("Messbasen-Stand zum ARCHIVzeitpunkt, nicht zum Laufzeitpunkt"
                         if (datetime.now() - zeit).total_seconds() > 3600 else ""))
    with open(os.path.join(ordner, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    if not still:
        print("  ✔ %s -> %s" % (rel, ordner))
    return ordner


def cmd_nachtragen(a) -> int:
    kand = sorted(glob.glob(os.path.join(HIER, "data", "_vergleich", "*.txt"))
                  + glob.glob(os.path.join(HIER, "data", "_vergleich", "*.log"))
                  + glob.glob(os.path.join(HIER, "Basisinfos", "K*_*_[0-9][0-9]_[0-9][0-9]", "*.txt"))
                  + glob.glob(os.path.join(HIER, "Basisinfos", "Ergebnis_*.txt")))
    neu, jetzt = 0, datetime.now().timestamp()
    for p in kand:
        # was gerade noch geschrieben wird, gehoert nicht ins Archiv
        if jetzt - os.path.getmtime(p) < 900 or os.path.getsize(p) == 0:
            print("  · ausgelassen (laeuft noch oder leer): %s" % os.path.relpath(p, HIER))
            continue
        if p.endswith("_kette.log") and "KETTE FERTIG" not in open(p, encoding="utf-8", errors="replace").read():
            print("  · ausgelassen (Kette nicht fertig): %s" % os.path.relpath(p, HIER))
            continue
        vorher = len(glob.glob(os.path.join(ARCHIV, "laeufe", "*")))
        cmd_lauf(a, datei=p, befund="", npz=None, still=True)
        neu += len(glob.glob(os.path.join(ARCHIV, "laeufe", "*"))) - vorher
    print("NACHTRAGEN: %d Dateien geprueft, %d neu archiviert" % (len(kand), neu))
    cmd_index(a)
    return 0


def cmd_index(a) -> int:
    zeilen = []
    for m in sorted(glob.glob(os.path.join(ARCHIV, "*", "*", "*.json"))):
        if not m.endswith(("meta.json", "manifest.json")):
            continue
        d = json.load(open(m, encoding="utf-8"))
        ordner = os.path.relpath(os.path.dirname(m), ARCHIV).replace("\\", "/")
        if d.get("art") == "lauf":
            kern = [u for u in d.get("urteil", []) if re.search(r"TOR:|->|R-R11|J6|S1|T2", u)][:3]
            zeilen.append(dict(art="lauf", datum=d["ende"][:16].replace("T", " "), werkzeug=d["werkzeug"],
                               commit=d.get("werkzeug_commit", ""), menge=d.get("menge", ""), befund=d.get("befund", ""),
                               ordner=ordner, quelle=d.get("quelle", ""), kurz=" | ".join(k[:110] for k in kern)))
        else:
            zeilen.append(dict(art=d.get("art", ""), datum=d["angelegt"][:16].replace("T", " "), werkzeug="",
                               commit=d.get("projekt_commit", ""), menge="", befund="", ordner=ordner,
                               quelle="%d Dateien, %.1f GB" % (len(d["dateien"]), sum(x["groesse"] for x in d["dateien"]) / 2 ** 30),
                               kurz=d.get("notiz", "")))
    zeilen.sort(key=lambda z: (z["art"] != "lauf", z["datum"]), reverse=False)
    os.makedirs(ARCHIV, exist_ok=True)
    with open(os.path.join(ARCHIV, "index.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(zeilen[0].keys()) if zeilen else ["art"], delimiter=";")
        w.writeheader(); w.writerows(zeilen)
    kopf = ("# Archiv-Index TradingInfoTool\n\n"
            "**Erzeugt von `python archiv.py index` — nie von Hand ändern.** Archiv: `%s` "
            "(Laufwerk BACKUP_DATA, andere Platte als das Projekt). Stand %s.\n\n"
            "> Finden: `python archiv.py suche <Wort>` · ein Werkzeug im archivierten Stand: "
            "`git show <commit>:<werkzeug>` · Regeln: `archiv.py` (Kopf) und `%s/LIESMICH.md`.\n\n"
            % (ARCHIV, datetime.now().strftime("%d.%m.%Y %H:%M"), ARCHIV))
    teile = [kopf, "## Messbasen und Rohdaten\n\n| Datum | Art | Umfang | Ordner | Notiz |\n|---|---|---|---|---|\n"]
    for z in zeilen:
        if z["art"] != "lauf":
            teile.append("| %s | %s | %s | `%s` | %s |\n" % (z["datum"], z["art"], z["quelle"], z["ordner"], z["kurz"]))
    teile.append("\n## Messläufe (neueste zuerst)\n\n| Ende | Werkzeug | Commit | Menge | Befund | Ordner | Kern |\n|---|---|---|---|---|---|---|\n")
    for z in sorted((x for x in zeilen if x["art"] == "lauf"), key=lambda x: x["datum"], reverse=True):
        teile.append("| %s | %s | %s | %s | %s | `%s` | %s |\n" % (
            z["datum"], z["werkzeug"], z["commit"], z["menge"], z["befund"], z["ordner"], z["kurz"].replace("|", "/")))
    text = "".join(teile)
    for ziel in (os.path.join(ARCHIV, "INDEX.md"), INDEX_PROJEKT):
        with open(ziel, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
    liesmich = os.path.join(ARCHIV, "LIESMICH.md")
    if not os.path.exists(liesmich):
        with open(liesmich, "w", encoding="utf-8", newline="\n") as f:
            f.write((__doc__ or "").strip() + "\n")
    print("INDEX: %d Eintraege -> %s und %s" % (len(zeilen), os.path.join(ARCHIV, "INDEX.md"), INDEX_PROJEKT))
    return 0


def cmd_suche(a) -> int:
    worte = [w.lower() for w in a.worte]
    for m in sorted(glob.glob(os.path.join(ARCHIV, "*", "*", "*.json"))):
        d = json.load(open(m, encoding="utf-8"))
        text = json.dumps(d, ensure_ascii=False).lower()
        if all(w in text for w in worte):
            print("%s  %s  %s  %s" % (os.path.relpath(os.path.dirname(m), ARCHIV), d.get("werkzeug", d.get("art")),
                                      d.get("menge", ""), d.get("befund", "")))
    return 0


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:                                         # noqa: BLE001
        pass
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("messbasen"); p.add_argument("--mit-altstaenden", action="store_true")
    p = sp.add_parser("verschiebe"); p.add_argument("pfad"); p.add_argument("--name", required=True); p.add_argument("--notiz", default="")
    p = sp.add_parser("lauf"); p.add_argument("datei"); p.add_argument("--befund"); p.add_argument("--npz")
    sp.add_parser("nachtragen"); sp.add_parser("index")
    p = sp.add_parser("suche"); p.add_argument("worte", nargs="+")
    a = ap.parse_args()
    if not os.path.isdir(os.path.splitdrive(ARCHIV)[0] + os.sep):
        raise SystemExit("⛔ Archivlaufwerk %s nicht erreichbar" % ARCHIV)
    return {"messbasen": cmd_messbasen, "verschiebe": cmd_verschiebe, "lauf": cmd_lauf,
            "nachtragen": cmd_nachtragen, "index": cmd_index, "suche": cmd_suche}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())
