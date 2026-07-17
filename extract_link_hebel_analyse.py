# -*- coding: utf-8 -*-
"""Einmal-Extraktionsskript (2026-07-17): komplette Hebel-Historie fuer ein
Symbol (Signale + Positions-Lebenszyklus + Trigger + Preisverlauf), damit
Claude das Hebelverhalten am konkreten Beispiel nachvollziehen kann - z.B.
die Frage, ob eine Empfehlungsfolge (ERÖFFNEN -> HALTEN -> HEBEL_SENKEN)
praktisch sinnvoll/ausfuehrbar war und wie der Kurs sich danach entwickelt hat.

Aufruf am Notebook: python extract_link_hebel_analyse.py LINK
Schreibt nach K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/
"""
import json
import sqlite3
import sys
from pathlib import Path

import database.db as db

SYMBOL = sys.argv[1] if len(sys.argv) > 1 else "LINK"
ZIEL_ORDNER = Path(r"K:\My Drive\Claude_Austauschordner\Notebook_Analysedaten")


def row_to_dict(row: sqlite3.Row) -> dict:
    return {k: row[k] for k in row.keys()}


def main() -> None:
    conn = db.get_connection()
    try:
        signale = conn.execute(
            "SELECT * FROM hebel_signals WHERE symbol = ? ORDER BY created_at ASC", (SYMBOL,)
        ).fetchall()
        positionen = conn.execute(
            "SELECT * FROM hebel_positions WHERE symbol = ? ORDER BY eroeffnet_am ASC", (SYMBOL,)
        ).fetchall()
        trigger = conn.execute(
            "SELECT * FROM hebel_triggers WHERE symbol = ? ORDER BY screened_at ASC", (SYMBOL,)
        ).fetchall()

        # Preisverlauf: falls Signale vorhanden, Fenster ab erstem Signal bis
        # 48h nach dem letzten - genug Kontext fuer "was kam danach".
        preis_punkte = []
        if signale:
            von = signale[0]["created_at"]
            preis_punkte = conn.execute(
                "SELECT * FROM price_history_ohlc WHERE symbol = ? AND date >= ? "
                "ORDER BY date ASC",
                (SYMBOL, von[:10]),
            ).fetchall()
    finally:
        conn.close()

    payload = {
        "symbol": SYMBOL,
        "hebel_signals": [row_to_dict(r) for r in signale],
        "hebel_positions": [row_to_dict(r) for r in positionen],
        "hebel_triggers": [row_to_dict(r) for r in trigger],
        "price_history_ohlc": [row_to_dict(r) for r in preis_punkte],
    }

    ZIEL_ORDNER.mkdir(parents=True, exist_ok=True)
    ziel_datei = ZIEL_ORDNER / f"hebel_analyse_{SYMBOL}.json"
    ziel_datei.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    print(f"Geschrieben: {ziel_datei}")
    print(f"  {len(signale)} Hebel-Signale, {len(positionen)} Positions-Zeilen, "
          f"{len(trigger)} Trigger-Zeilen, {len(preis_punkte)} Preispunkte")


if __name__ == "__main__":
    main()
