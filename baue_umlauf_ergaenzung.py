# -*- coding: utf-8 -*-
"""DESKTOP: die Ergaenzungsdatei der Umlaufmenge fuer das Notebook bauen (P22, 15.10.2026; Spot §54.7/§54.8).

    python baue_umlauf_ergaenzung.py [--bis JJJJ-MM-TT] [--ziel ORDNER]

Nutzer 15.10.: *"Ja, USB-Ergaenzung bauen"*.

WARUM: Die Mengendatei am NB (``data/umlaufmenge_cg.db``, Betriebskopie mit Marke ``_nur_betrieb``) beginnt am 08.09.2026 und wird dort
taeglich fortgeschrieben. Fuer die Verwaesserung 90 T (P22) fehlen ihr die Tage DAVOR - die hat nur der Desktop (Vollabruf ab
21.09.2025). Diese Datei traegt GENAU diese aelteren Zeilen, sonst nichts: keine Zuordnung, keine NB-Tage, keine Marke.

WIE ES AM NB ANKOMMT: ``ergaenze_umlauf_nb.py`` fuegt sie EINMAL ein (nur Tage vor dem NB-Beginn, INSERT OR IGNORE, vorher Sicherung) -
keine Datei wird ersetzt. Weg: Google-Drive-Austauschordner (Vorgabe; die Daten sind oeffentliche CoinGecko-Mengen, keine Geheimnisse)
oder USB (``--ziel``).

Dieselbe Groesse auf beiden Seiten: Vollabruf = Marktwert/Preis (market_chart), Tagesjob = circulating_supply (/coins/markets); an 119
Symbolen Median-Abweichung 0,000 % (``hole_umlaufmenge_cg.taeglich``). Der Buendelfaktor ist in beiden angewandt (Befund 2.522).
NUR LESEND auf der Quelle.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import os
import sqlite3
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
WURZEL = Path(__file__).resolve().parent
QUELLE = WURZEL / "data" / "umlaufmenge_cg.db"
NAME = "umlauf_ergaenzung.db"
NB_BEGINN_VORGABE = "2026-09-08"          # erster Tag der NB-Reihe (USB-Kopie 22.09.2026, 14 T; Spot §54.3)


def pruefsumme(zeilen) -> str:
    h = hashlib.sha256()
    for s, d, w in zeilen:
        h.update(("%s|%s|%.12g\n" % (s, d, w)).encode("utf-8"))
    return h.hexdigest()


def _drive() -> Path | None:
    for b in ("K", "G", "H", "E", "F"):
        for n in ("My Drive", "Meine Ablage"):
            p = Path("%s:/%s" % (b, n))
            if p.exists():
                return p
    return None


def nb_beginn_aus_kopie() -> str:
    """Erster Tag der NB-Reihe aus der USB-Kopie im Austauschordner (sonst die Vorgabe)."""
    d = _drive()
    p = d / "Claude_Austauschordner" / "umlaufmenge_cg.db" if d else None
    if p and p.exists():
        c = sqlite3.connect("file:%s?mode=ro" % p.as_posix(), uri=True)
        try:
            return str(c.execute("SELECT MIN(datum) FROM umlaufmenge").fetchone()[0])[:10]
        finally:
            c.close()
    return NB_BEGINN_VORGABE


def baue(ziel_ordner: Path, bis: str, quelle: Path = QUELLE) -> dict:
    q = sqlite3.connect("file:%s?mode=ro" % quelle.as_posix(), uri=True)
    try:
        if q.execute("SELECT name FROM sqlite_master WHERE name='_nur_betrieb'").fetchone():
            raise SystemExit("⛔ Die Quelle ist selbst eine Betriebskopie (_nur_betrieb) - die Ergaenzung kommt aus der VOLLEN Desktop-Reihe")
        zeilen = q.execute("SELECT symbol, datum, wert FROM umlaufmenge WHERE datum < ? ORDER BY symbol, datum", (bis,)).fetchall()
        quelle_info = q.execute("SELECT hinweis, groesse, tage, gebaut_am, buendelfaktor FROM _quelle").fetchone()
    finally:
        q.close()
    ziel_ordner.mkdir(parents=True, exist_ok=True)
    ziel = ziel_ordner / NAME
    if ziel.exists():
        ziel.unlink()
    z = sqlite3.connect(str(ziel))
    try:
        z.executescript("""
        CREATE TABLE umlaufmenge (symbol TEXT NOT NULL, datum TEXT NOT NULL, wert REAL NOT NULL, PRIMARY KEY (symbol, datum));
        CREATE TABLE _ergaenzung (hinweis TEXT, bis_exklusiv TEXT, von TEXT, zeilen INTEGER, symbole INTEGER, pruefsumme TEXT,
                                  buendelfaktor TEXT, gebaut_am TEXT);
        """)
        z.executemany("INSERT INTO umlaufmenge VALUES (?,?,?)", zeilen)
        von = min(d for _, d, _ in zeilen) if zeilen else None
        info = dict(hinweis="ERGAENZUNG fuer die NB-Betriebskopie: nur Tage VOR %s. Einspielen mit ergaenze_umlauf_nb.py - nie als "
                            "Mengendatei ablegen, nie messen" % bis, bis_exklusiv=bis, von=str(von)[:10] if von else None, zeilen=len(zeilen),
                    symbole=len({s for s, _, _ in zeilen}), pruefsumme=pruefsumme(zeilen),
                    buendelfaktor=quelle_info[4] if quelle_info else None, gebaut_am=dt.datetime.now(dt.timezone.utc).isoformat())
        z.execute("INSERT INTO _ergaenzung VALUES (?,?,?,?,?,?,?,?)", tuple(info.values()))
        z.commit()
    finally:
        z.close()
    info["datei"] = str(ziel)
    info["mb"] = round(ziel.stat().st_size / 1024 ** 2, 1)
    return info


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bis", help="erster Tag der NB-Reihe (exklusiv); Vorgabe: aus der USB-Kopie im Austauschordner")
    ap.add_argument("--ziel", help="Zielordner (Vorgabe: Google-Drive-Austauschordner)")
    a = ap.parse_args()
    bis = a.bis or nb_beginn_aus_kopie()
    if a.ziel:
        ziel = Path(a.ziel)
    else:
        d = _drive()
        if not d:
            print("⛔ Kein Google-Drive-Ordner gefunden - bitte --ziel angeben (z. B. USB)")
            return 2
        ziel = d / "Claude_Austauschordner"
    info = baue(ziel, bis)
    print("=" * 78)
    print("ERGAENZUNG DER UMLAUFMENGE FUER DAS NOTEBOOK")
    print("=" * 78)
    print("  Zeilen     %d · %d Symbole · %s bis vor %s" % (info["zeilen"], info["symbole"], info["von"], bis))
    print("  Datei      %s (%.1f MB)" % (info["datei"], info["mb"]))
    print("  Pruefsumme %s" % info["pruefsumme"][:16])
    print()
    print("  AM NOTEBOOK (nach dem Pull):  python ergaenze_umlauf_nb.py")
    print("  (findet die Datei im Austauschordner selbst; bei USB: python ergaenze_umlauf_nb.py <Pfad zur Datei>)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
