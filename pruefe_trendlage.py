# -*- coding: utf-8 -*-
"""Prueft L3 (Trendlage) an echten Daten - Form, Kausalitaet, Unterscheidungskraft.

Vier Pruefungen, und die vierte ist die eigentliche:

    1  FORM         jede Aussage nennt ihr Fenster, traegt kein Werturteil
    2  KAUSALITAET  die Aussage zu Tag T aendert sich nicht, wenn man Tage
                    NACH T hinzufuegt oder wegnimmt
    3  BREITE       kommt sie fuer jede Assetklasse?
    4  KORREKTURFALL  gibt es Tage, an denen das lange Fenster steigt und das
                    kurze faellt - und wie beschreiben wir sie? Das ist der
                    Fall, den `_struktur()` "intakter Abwaertstrend" nannte

Lauf:  python pruefe_trendlage.py
"""
from __future__ import annotations

import sqlite3
import sys
from collections import defaultdict

sys.path.insert(0, ".")

from agent.marktlage import (BENCHMARK, TREND_KURZ, TREND_LANG,
                             beschreibe_trend, beschreibe_volatilitaet)
from database.models import OhlcPoint

DB = "data/tradinginfotool.db"


def lade(symbol: str) -> list[OhlcPoint]:
    """Eine Waehrung je Symbol - USD bevorzugt, sonst EUR (7.17)."""
    con = sqlite3.connect(DB)
    try:
        for w in ("USD", "EUR"):
            zeilen = con.execute(
                "SELECT date, open, high, low, close, volume FROM "
                "price_history_ohlc WHERE symbol=? AND currency=? "
                "ORDER BY date", (symbol, w)).fetchall()
            if zeilen:
                return [OhlcPoint(symbol=symbol, currency=w, date=z[0],
                                  open=z[1], high=z[2], low=z[3], close=z[4],
                                  volume=z[5], fetched_at="") for z in zeilen]
        return []
    finally:
        con.close()


def main() -> int:
    reihen = {s: lade(s) for s in set(BENCHMARK.values())}
    fehler = 0

    print("=== 3. BREITE - kommt die Aussage fuer jede Klasse? ===")
    for klasse in BENCHMARK:
        reihe = reihen.get(BENCHMARK[klasse]) or []
        if not reihe:
            print(f"   {klasse:<12} KEINE REIHE"); fehler += 1; continue
        datum = reihe[-1].date
        saetze = beschreibe_trend(reihen, klasse, datum)
        vola = beschreibe_volatilitaet(reihen, klasse, datum)
        print(f"\n   {klasse.upper()}   ({len(reihe)} Kerzen, Anker {datum})")
        for s in saetze + vola:
            print(f"      - {s}")
        if len(saetze) != 2:
            print(f"      !! {len(saetze)} statt 2 Trendaussagen"); fehler += 1

    print("\n=== 1. FORM - Fenster genannt, keine Werturteile ===")
    # Fuer PROSA ist `waechter_zuspitzung` zustaendig, nicht
    # `enthaelt_werturteile` - der prueft Feldnamen in einem dict.
    # Ueber die GANZE Historie, nicht nur ueber den letzten Anker: eine
    # Formulierung, die bei heutigen Zahlen sauber ist, kann bei anderen
    # kippen. Genau das war der Fehler bei `_struktur()` - an einem Beispiel
    # geprueft, auf 2,71 % der Tage falsch.
    from agent.waechter_zuspitzung import finde_grade
    alle = []
    for klasse in BENCHMARK:
        reihe = reihen.get(BENCHMARK[klasse]) or []
        for i in range(TREND_LANG, len(reihe), 53):
            alle += beschreibe_trend(reihen, klasse, reihe[i].date)
    schlimm = 0
    for s in alle:
        hart, weich = finde_grade(s)
        if hart or weich or "Handelstage" not in s:
            print(f"   !! {s}")
            print(f"      hart={hart} weich={weich}")
            schlimm += 1
    fehler += schlimm
    print(f"   {len(alle)} Aussagen ueber die ganze Historie geprueft, "
          f"{schlimm} beanstandet")

    print("\n=== 2. KAUSALITAET - haengt die Aussage an der Zukunft? ===")
    btc = reihen[BENCHMARK["krypto"]]
    abw = 0
    for i in range(TREND_LANG + 5, len(btc), 37):
        datum = btc[i].date
        soll = beschreibe_trend({BENCHMARK["krypto"]: btc}, "krypto", datum)
        for extra in (0, 1, 20, 200):
            gekuerzt = btc[:min(i + 1 + extra, len(btc))]
            ist = beschreibe_trend({BENCHMARK["krypto"]: gekuerzt}, "krypto",
                                   datum)
            if ist != soll:
                abw += 1
                print(f"   !! {datum} weicht ab bei +{extra} Tagen Zukunft")
    print(f"   {abw} Abweichungen")
    fehler += abw

    print("\n=== 4. KORREKTURFALL - langes Fenster hoch, kurzes runter ===")
    zaehler = defaultdict(int)
    beispiel = None
    for i in range(TREND_LANG, len(btc)):
        c = btc[i].close
        lang = c / btc[i - TREND_LANG].close - 1.0
        kurz = c / btc[i - TREND_KURZ].close - 1.0
        art = ("lang+ kurz+" if lang >= 0 and kurz >= 0 else
               "lang+ kurz-" if lang >= 0 else
               "lang- kurz+" if kurz >= 0 else "lang- kurz-")
        zaehler[art] += 1
        if art == "lang+ kurz-" and beispiel is None and kurz < -0.15:
            beispiel = btc[i].date
    n = sum(zaehler.values())
    for art in ("lang+ kurz+", "lang+ kurz-", "lang- kurz+", "lang- kurz-"):
        print(f"   {art:<14}{zaehler[art]:>5}  {100.0*zaehler[art]/n:>5.1f} %")
    if beispiel:
        print(f"\n   Beispiel {beispiel} - so lesen es die LLM heute:")
        for s in beschreibe_trend({BENCHMARK["krypto"]: btc}, "krypto",
                                  beispiel):
            print(f"      - {s}")
    else:
        print("   !! kein Korrekturfall in der Historie")

    print(f"\n{'BESTANDEN' if not fehler else str(fehler) + ' FEHLER'}")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
