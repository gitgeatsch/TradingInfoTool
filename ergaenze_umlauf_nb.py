# -*- coding: utf-8 -*-
"""NOTEBOOK: die aelteren Tage der Umlaufmenge EINMAL in die Betriebskopie einfuegen (P22, 15.10.2026; Spot §54.8).

    python ergaenze_umlauf_nb.py --nur-pruefen     # ZUERST: findet die Datei, prueft sie und das Ziel - schreibt NICHTS
    python ergaenze_umlauf_nb.py [Pfad zu umlauf_ergaenzung.db]

Ohne Pfad: die Datei im Google-Drive-Austauschordner (G:/K:, "My Drive"/"Meine Ablage"), sonst ``data/umlauf_ergaenzung.db``.

WAS GESCHIEHT - und was NICHT:
  1. Ziel ist NUR ``data/umlaufmenge_cg.db`` MIT der Marke ``_nur_betrieb`` (die NB-Betriebskopie). Ohne Marke bricht es ab: am Desktop
     liegt dort die volle Messbasis, die wird nie veraendert. ``tradinginfotool.db`` (Produktion) wird NICHT geoeffnet.
  2. Pruefsumme der Ergaenzung pruefen.
  3. SICHERUNG der Mengendatei (SQLite-Backup, sicher auch bei laufender App) nach ``data/umlaufmenge_cg.vor_ergaenzung_<Zeit>.db``.
  4. In EINER Transaktion: nur Zeilen mit Datum VOR dem ersten NB-Tag, ``INSERT OR IGNORE`` - kein NB-Tag wird beruehrt.
  5. Nachweis: die NB-Tage haben dieselbe Pruefsumme wie vorher, Zahl der neuen Zeilen, Marke vorhanden, integrity_check ok.
  6. Vermerk in ``_ergaenzung_eingespielt`` (zweiter Lauf: 0 neue Zeilen, "schon eingespielt").
Kein Neustart noetig: die Verwaesserung liest die Datei bei jedem Lauf neu.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import os
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WURZEL = Path(__file__).resolve().parent
ZIEL_VORGABE = WURZEL / "data" / "umlaufmenge_cg.db"
NAME = "umlauf_ergaenzung.db"


def _pruefsumme(zeilen) -> str:
    h = hashlib.sha256()
    for s, d, w in zeilen:
        h.update(("%s|%s|%.12g\n" % (s, d, w)).encode("utf-8"))
    return h.hexdigest()


def finde_quelle() -> Path | None:
    for b in ("G", "K", "H", "E", "F"):
        for n in ("My Drive", "Meine Ablage"):
            p = Path("%s:/%s/Claude_Austauschordner/%s" % (b, n, NAME))
            if p.exists():
                return p
    p = WURZEL / "data" / NAME
    return p if p.exists() else None


def pruefen(quelle: Path, ziel: Path = ZIEL_VORGABE) -> dict:
    """Trockenlauf (Nutzer 15.10.: *"pruefen wir, wie kommen die Daten auf das NB?"*): liest beide Dateien NUR (mode=ro) und sagt, was
    ein Einspielen taete - Fundort, Groesse, Pruefsumme, Marke, erster NB-Tag, Zahl der Zeilen, die neu waeren."""
    aus = {"quelle": str(quelle), "quelle_mb": round(quelle.stat().st_size / 1024 ** 2, 1), "ziel": str(ziel)}
    q = sqlite3.connect("file:%s?mode=ro" % quelle.as_posix(), uri=True)
    try:
        info = q.execute("SELECT bis_exklusiv, zeilen, pruefsumme, von FROM _ergaenzung").fetchone()
        zeilen = q.execute("SELECT symbol, datum, wert FROM umlaufmenge ORDER BY symbol, datum").fetchall()
    finally:
        q.close()
    aus.update(von=info[3], bis_exklusiv=info[0], zeilen=len(zeilen), pruefsumme_ok=(len(zeilen) == info[1] and _pruefsumme(zeilen) == info[2]))
    if not ziel.exists():
        aus.update(ziel_ok=False, grund="Ziel fehlt")
        return aus
    c = sqlite3.connect("file:%s?mode=ro" % ziel.as_posix(), uri=True)
    try:
        marke = bool(c.execute("SELECT name FROM sqlite_master WHERE name='_nur_betrieb'").fetchone())
        erster, letzter, n = c.execute("SELECT MIN(datum), MAX(datum), COUNT(*) FROM umlaufmenge").fetchone()
        schon = c.execute("SELECT name FROM sqlite_master WHERE name='_ergaenzung_eingespielt'").fetchone()
    finally:
        c.close()
    erster = str(erster)[:10] if erster else "9999-12-31"
    aus.update(ziel_ok=marke and ziel.name != "tradinginfotool.db", marke=marke, erster_nb=erster, letzter_nb=str(letzter)[:10], zeilen_nb=n,
               schon_eingespielt=bool(schon), wuerde_einfuegen=sum(1 for z in zeilen if str(z[1])[:10] < erster))
    return aus


def einspielen(quelle: Path, ziel: Path = ZIEL_VORGABE, jetzt: dt.datetime | None = None) -> dict:
    jetzt = jetzt or dt.datetime.now(dt.timezone.utc)
    if not ziel.exists():
        raise SystemExit("⛔ %s fehlt" % ziel)
    if ziel.name == "tradinginfotool.db":
        raise SystemExit("⛔ Ziel ist die Produktion - abgebrochen")
    q = sqlite3.connect("file:%s?mode=ro" % quelle.as_posix(), uri=True)
    try:
        info = q.execute("SELECT bis_exklusiv, zeilen, pruefsumme FROM _ergaenzung").fetchone()
        if not info:
            raise SystemExit("⛔ %s ist keine Ergaenzungsdatei (Tabelle _ergaenzung fehlt)" % quelle)
        zeilen = q.execute("SELECT symbol, datum, wert FROM umlaufmenge ORDER BY symbol, datum").fetchall()
    finally:
        q.close()
    if len(zeilen) != info[1] or _pruefsumme(zeilen) != info[2]:
        raise SystemExit("⛔ Pruefsumme der Ergaenzung stimmt nicht (Datei beschaedigt oder unvollstaendig) - nichts eingespielt")
    c = sqlite3.connect(str(ziel), timeout=60)
    try:
        if not c.execute("SELECT name FROM sqlite_master WHERE name='_nur_betrieb'").fetchone():
            raise SystemExit("⛔ %s traegt keine Marke _nur_betrieb - das ist keine NB-Betriebskopie (am Desktop: die Messbasis). "
                             "Abgebrochen, nichts veraendert" % ziel)
        erster_nb = c.execute("SELECT MIN(datum) FROM umlaufmenge").fetchone()[0]
        erster_nb = str(erster_nb)[:10] if erster_nb else "9999-12-31"
        # NB-Tage vorher (fuer den Nachweis, dass keiner beruehrt wird)
        nb_vor = c.execute("SELECT symbol, datum, wert FROM umlaufmenge WHERE datum >= ? ORDER BY symbol, datum", (erster_nb,)).fetchall()
        n_vor = c.execute("SELECT COUNT(*) FROM umlaufmenge").fetchone()[0]
        # Sicherung (Backup-API: auch bei laufender App konsistent)
        sich = ziel.with_name("umlaufmenge_cg.vor_ergaenzung_%s.db" % jetzt.strftime("%Y%m%d_%H%M%S"))
        b = sqlite3.connect(str(sich))
        try:
            c.backup(b)
        finally:
            b.close()
        neu = [z for z in zeilen if str(z[1])[:10] < erster_nb]
        c.execute("BEGIN")
        vorher_total = c.total_changes
        c.executemany("INSERT OR IGNORE INTO umlaufmenge VALUES (?,?,?)", neu)
        eingefuegt = c.total_changes - vorher_total
        c.execute("CREATE TABLE IF NOT EXISTS _ergaenzung_eingespielt (am TEXT, quelle TEXT, bis_exklusiv TEXT, angeboten INTEGER, "
                  "eingefuegt INTEGER, sicherung TEXT)")
        c.execute("INSERT INTO _ergaenzung_eingespielt VALUES (?,?,?,?,?,?)",
                  (jetzt.isoformat(), str(quelle), info[0], len(neu), eingefuegt, sich.name))
        c.commit()
        nb_nach = c.execute("SELECT symbol, datum, wert FROM umlaufmenge WHERE datum >= ? ORDER BY symbol, datum", (erster_nb,)).fetchall()
        n_nach = c.execute("SELECT COUNT(*) FROM umlaufmenge").fetchone()[0]
        marke = bool(c.execute("SELECT name FROM sqlite_master WHERE name='_nur_betrieb'").fetchone())
        integ = c.execute("PRAGMA integrity_check").fetchone()[0]
        frueh = c.execute("SELECT MIN(datum) FROM umlaufmenge").fetchone()[0]
    finally:
        c.close()
    erg = {"erster_nb": erster_nb, "angeboten": len(neu), "eingefuegt": eingefuegt, "zeilen_vor": n_vor, "zeilen_nach": n_nach,
           "nb_tage_unveraendert": _pruefsumme(nb_vor) == _pruefsumme(nb_nach), "marke": marke, "integritaet": integ,
           "fruehester_tag": str(frueh)[:10], "sicherung": str(sich)}
    erg["ok"] = erg["nb_tage_unveraendert"] and marke and integ == "ok" and n_nach == n_vor + eingefuegt
    return erg


def main() -> int:
    nur = "--nur-pruefen" in sys.argv
    pfade = [a for a in sys.argv[1:] if not a.startswith("--")]
    quelle = Path(pfade[0]) if pfade else finde_quelle()
    if not quelle or not quelle.exists():
        print("⛔ %s nicht gefunden (Austauschordner oder data/) - bitte den Pfad angeben" % NAME)
        return 2
    if nur:
        p = pruefen(quelle)
        print("=" * 78)
        print("TROCKENLAUF - es wird NICHTS geschrieben")
        print("=" * 78)
        print("  Datei gefunden    %s (%.1f MB)" % (p["quelle"], p["quelle_mb"]))
        print("  Inhalt            %d Zeilen, %s bis vor %s · Pruefsumme %s" % (p["zeilen"], p["von"], p["bis_exklusiv"],
                                                                                "OK" if p["pruefsumme_ok"] else "FALSCH (Datei unvollstaendig?)"))
        if p.get("grund"):
            print("  Ziel              %s" % p["grund"])
        else:
            print("  Ziel              %s · Marke _nur_betrieb %s · NB-Reihe %s bis %s (%d Zeilen)%s" % (
                p["ziel"], "ja" if p["marke"] else "NEIN", p["erster_nb"], p["letzter_nb"], p["zeilen_nb"],
                " · schon einmal eingespielt" if p["schon_eingespielt"] else ""))
            print("  wuerde einfuegen  %d Zeilen (nur Tage vor %s)" % (p["wuerde_einfuegen"], p["erster_nb"]))
        ok = p["pruefsumme_ok"] and p.get("ziel_ok")
        print("  => %s" % ("BEREIT - jetzt ohne --nur-pruefen ausfuehren" if ok else "⛔ NICHT bereit - bitte melden"))
        return 0 if ok else 1
    e = einspielen(quelle)
    print("=" * 78)
    print("UMLAUFMENGE AM NB ERGAENZT" if e["eingefuegt"] else "UMLAUFMENGE: NICHTS NEU (schon eingespielt)")
    print("=" * 78)
    print("  Quelle            %s" % quelle)
    print("  erster NB-Tag     %s · neu eingefuegt %d von %d angebotenen Zeilen" % (e["erster_nb"], e["eingefuegt"], e["angeboten"]))
    print("  Zeilen            %d -> %d · fruehester Tag jetzt %s" % (e["zeilen_vor"], e["zeilen_nach"], e["fruehester_tag"]))
    print("  NB-Tage unberuehrt %s · Marke _nur_betrieb %s · integrity_check %s" % (e["nb_tage_unveraendert"], e["marke"], e["integritaet"]))
    print("  Sicherung         %s" % e["sicherung"])
    print("  => %s" % ("IN ORDNUNG - kein Neustart noetig" if e["ok"] else "⛔ NACHWEIS FEHLGESCHLAGEN - Sicherung zurueckkopieren"))
    return 0 if e["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
