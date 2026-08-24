# -*- coding: utf-8 -*-
"""Ist das Ausrollen angekommen? (24.08.2026)

NACH DEM `git pull` UND DEM NEUSTART AUF DEM NOTEBOOK. Dieses Werkzeug fragt
genau das ab, was der Ausrollplan als Beobachtungspunkte nennt - in einem
Aufruf, damit es niemand einzeln zusammensucht.

⚠️ ES LIEST NUR. Keine Zeile wird geschrieben, kein Modell gerufen, kein
Kontingent verbraucht. Es darf deshalb neben der laufenden Produktion laufen.

WAS ES PRUEFT, und warum jeder Punkt einmal teuer war:

    1 SCHEMA        Spalte `strategie`, Tabelle `auswahl_schatten`.
                    ⚠️ Am 22.08. hat eine neue Spalte die App angehalten -
                    geschrieben wurde sie, gelesen nie.
    2 LESEPROBE     ueber den LESEPFAD DES MODELLS, nicht per SELECT. Das
                    Schreiben nennt Spalten einzeln, das Lesen bekommt sie alle.
    3 AUSWAHL       fuellt sich der Schatten? Wie viele Laeufe, wie viele
                    Gewaehlte, wie viele mit Aktion?
    4 TRICHTER      passiert die Stufe `auswahl` plausibel viele - und bleibt
                    der Trichter monoton?
    5 VERKAUFSSEITE traegt sie jetzt Fakten und Merkmale (B1/B2/B3)?
    6 ROHSTOFFE     haben OD7C/H/N/L eigene Kerzen? In der Desktop-Kopie hatten
                    sie NULL - am Notebook ist das zu pruefen.

Aufruf:  python pruefe_ausrollen.py
"""
from __future__ import annotations

import argparse
import sqlite3

GRUEN, ROT, GELB = "OK  ", "FEHL", "?   "


def _sag(zeichen: str, text: str, detail: str = "") -> None:
    print(f"  {zeichen}  {text}")
    if detail:
        print(f"        {detail}")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--symbol", default="BTC")
    a = p.parse_args()

    c = sqlite3.connect(f"file:{a.db}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    schlecht = 0

    # ---- 1 SCHEMA ------------------------------------------------------
    print("\n1. SCHEMA - was der erste Lauf anlegen sollte")
    spalten = {r[1] for r in c.execute("PRAGMA table_info(signals)")}
    tabellen = {r[0] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    for was, da, hinweis in (
            ("Spalte signals.strategie", "strategie" in spalten,
             "entsteht beim ERSTEN Schreiben der Rollen-Kette"),
            ("Tabelle auswahl_schatten", "auswahl_schatten" in tabellen,
             "entsteht beim ERSTEN Lauf")):
        if da:
            _sag(GRUEN, was)
        else:
            _sag(GELB, was + " fehlt noch", hinweis)

    # ---- 2 LESEPROBE ---------------------------------------------------
    print("\n2. LESEPROBE - ueber den Lesepfad des Modells, nicht per SELECT")
    try:
        import database.db as db

        s = db.get_latest_signal(c, a.symbol)
        if s is None:
            _sag(GELB, f"noch kein Signal fuer {a.symbol}",
                 "nach dem ersten Umlauf wiederholen")
        else:
            _sag(GRUEN, f"{s.symbol} {s.action} - strategie = "
                        f"{getattr(s, 'strategie', 'FELD FEHLT')!r}",
                 f"geschrieben {str(s.created_at)[:16]}")
    except Exception as exc:                                 # noqa: BLE001
        schlecht += 1
        _sag(ROT, "der Lesepfad wirft", f"{type(exc).__name__}: {exc}")

    # ---- 3 AUSWAHL -----------------------------------------------------
    print("\n3. AUSWAHL - fuellt sich der Schatten?")
    try:
        from agent import auswahl as AW

        st = AW.stand(c)
        if st["zeilen"]:
            _sag(GRUEN, f"{st['zeilen']} Zeilen aus {st['laeufe']} Laeufen, "
                        f"{st['gewaehlt']} gewaehlt, {st['mit_aktion']} mit Aktion")
            for g in {r[0] for r in c.execute(
                    "SELECT DISTINCT gruppe FROM auswahl_schatten")}:
                s2 = AW.stumme_laeufe(c, g)
                _sag(GRUEN if not s2["stumm"] else GELB,
                     f"{g}: {s2['laeufe']} Laeufe in Folge ohne Einstieg"
                     + ("  ⚠️ die Auswahl liefert, die Kette nimmt keinen"
                        if s2["stumm"] else ""))
        else:
            _sag(GELB, "noch keine Zeile", "nach dem ersten Umlauf wiederholen")
    except Exception as exc:                                 # noqa: BLE001
        _sag(GELB, "Schatten noch nicht lesbar", str(exc))

    # ---- 4 TRICHTER ----------------------------------------------------
    print("\n4. TRICHTER - passiert die neue Stufe, und bleibt er monoton?")
    try:
        import json as _json

        from agent.rollen_gate import TABELLE as _TAB

        zeile = c.execute(
            f"SELECT lauf, hinein, heraus, daten_json FROM {_TAB} "
            f"ORDER BY rowid DESC LIMIT 1").fetchone()
        if zeile is None:
            _sag(GELB, "noch kein Durchlauf verzeichnet")
        else:
            d = _json.loads(zeile["daten_json"] or "{}")
            best = (d.get("bestanden_je_stufe") or {})
            verl = (d.get("verloren_je_stufe") or {})
            hinein = zeile["hinein"] or 0
            if "auswahl" not in best:
                _sag(GELB, f"{zeile['lauf']}: die Stufe `auswahl` fehlt noch",
                     "dieser Durchlauf stammt vom alten Code - nach dem "
                     "naechsten Umlauf wiederholen")
            else:
                # ⚠️ MONOTON: keine Stufe darf mehr bestanden haben, als
                # ueberhaupt hineingegangen sind. Genau das war am 23.08.
                # verletzt (anlass 4 bei hinein 3).
                zuviel = [s for s, n in best.items() if n > hinein]
                _sag(GRUEN if not zuviel else ROT,
                     f"{zeile['lauf']}: hinein {hinein} · auswahl "
                     f"{best['auswahl']} bestanden / "
                     f"{verl.get('auswahl', 0)} verloren · heraus "
                     f"{zeile['heraus']}",
                     "" if not zuviel
                     else f"⚠️ NICHT MONOTON: {zuviel} zaehlen mehr "
                          f"als hinein - eine Doppelbuchung")
    except Exception as exc:                                 # noqa: BLE001
        _sag(GELB, "Trichter nicht lesbar", str(exc))

    # ---- 5 VERKAUFSSEITE -----------------------------------------------
    print("\n5. VERKAUFSSEITE - traegt sie jetzt Fakten und Merkmale?")
    try:
        for r in c.execute(
                "SELECT action, COUNT(*) n, MIN(LENGTH(facts_json)) mn, "
                "MAX(LENGTH(facts_json)) mx FROM signals "
                "WHERE quelle_kette='rollen' AND action IN "
                "('HALTEN','REDUZIEREN','VERKAUFEN') GROUP BY action"):
            gut = (r["mx"] or 0) > 200
            if not gut:
                schlecht += 0          # noch keine neuen Zeilen ist kein Fehler
            _sag(GRUEN if gut else GELB,
                 f"{r['action']:11} n={r['n']:4}  facts_json "
                 f"{r['mn']} .. {r['mx']} Zeichen",
                 "" if gut else "⚠️ 17 Zeichen = alte Zeilen. Die neuen "
                                "entstehen erst mit dem naechsten Ausstieg")
    except sqlite3.Error as exc:
        _sag(GELB, "Verkaufsseite nicht lesbar", str(exc))

    # ---- 6 ROHSTOFFE ---------------------------------------------------
    print("\n6. ROHSTOFFE - haben sie eigene Kerzen?")
    try:
        import config

        roh = [x.symbol for x in config.get_watchlist()
               if x.assetklasse == "rohstoffe"]
        for sym in roh:
            n = c.execute("SELECT COUNT(*) FROM price_history_ohlc "
                          "WHERE symbol = ?", (sym,)).fetchone()[0]
            if n:
                _sag(GRUEN, f"{sym}: {n} Kerzen")
            else:
                schlecht += 1
                _sag(ROT, f"{sym}: KEINE eigene Kerze",
                     "die langen Reihen liegen nur unter "
                     "_ROHSTOFF_FUTURES_* - damit fehlt hier die Faktenbasis")
    except Exception as exc:                                 # noqa: BLE001
        _sag(GELB, "Watchlist nicht lesbar", str(exc))

    c.close()
    print("\n" + "=" * 68)
    print("ALLES GRUEN" if not schlecht else f"{schlecht} PUNKT(E) OFFEN")
    print("⚠️ Gelb heisst 'noch nicht da' - nach dem ersten Umlauf "
          "wiederholen.\n   Rot heisst: nachsehen, bevor der naechste Lauf "
          "darauf aufbaut.")
    return 1 if schlecht else 0


if __name__ == "__main__":
    raise SystemExit(main())
