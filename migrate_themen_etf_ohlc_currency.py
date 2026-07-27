"""Einmaliges Migrationsskript (2026-07-27, Grundsatzfix Teil 2) - relabelt die
bereits gespeicherten price_history_ohlc-Zeilen der 5 Themen-ETF-Symbole von
currency='USD' auf 'EUR' (alle 5 sind Quotrix-/Xetra-/Berlin-gelistete
EUR-Instrumente, siehe agent/themen_etf/pipeline.py::_resolve_asset_currency()).

Kein Blocker: der ab jetzt korrekte Code wuerde die falsch beschrifteten
Zeilen ohnehin binnen der 5-Tage-Staleness-Schwelle selbst heilen (neuer
_ensure_ohlc_backfilled()-Aufruf schreibt dann direkt unter currency='EUR').
Dieses Skript sorgt nur fuer sofortige Korrektheit statt bis zu 5 Tage zu warten.

Sicher (kein Duplikat-/Verwaisungs-Risiko): PRIMARY KEY ist (symbol, currency,
date), fuer diese 5 Symbole existieren aktuell keine 'EUR'-Zeilen (nur die
faelschlich 'USD'-beschrifteten).

Nutzung (--apply zum tatsaechlichen Schreiben, sonst reiner Trockenlauf):
    python migrate_themen_etf_ohlc_currency.py [--apply]
"""
import argparse
import sqlite3

import database.db as db

_BETROFFENE_SYMBOLE = ["VVMX", "X136", "EXH3", "CEBS", "ISOC"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Aenderungen tatsaechlich schreiben (sonst Trockenlauf)")
    args = parser.parse_args()

    conn = db.get_connection()
    try:
        for symbol in _BETROFFENE_SYMBOLE:
            rows = conn.execute(
                "SELECT COUNT(*) AS n FROM price_history_ohlc WHERE symbol = ? AND currency = 'USD'",
                (symbol,),
            ).fetchone()
            anzahl = rows["n"]
            konflikt = conn.execute(
                "SELECT COUNT(*) AS n FROM price_history_ohlc WHERE symbol = ? AND currency = 'EUR'",
                (symbol,),
            ).fetchone()["n"]
            print(f"{symbol}: {anzahl} Zeilen mit currency='USD' gefunden"
                  + (f" (WARNUNG: {konflikt} 'EUR'-Zeilen existieren bereits - UPDATE wuerde Duplikate erzeugen, "
                     "diese Zeile wird uebersprungen)" if konflikt else ""))
            if anzahl == 0 or konflikt > 0 or not args.apply:
                continue
            conn.execute(
                "UPDATE price_history_ohlc SET currency = 'EUR' WHERE symbol = ? AND currency = 'USD'",
                (symbol,),
            )
            conn.commit()
            print(f"  -> {anzahl} Zeilen auf currency='EUR' umgestellt.")

        if not args.apply:
            print("\nTrockenlauf (kein --apply) - keine Aenderungen geschrieben.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
