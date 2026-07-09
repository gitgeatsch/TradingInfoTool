"""Einmal-/Re-Import der Bestaende aus Basisinfos/Assets.xlsx (siehe Spezifikation B-5)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import openpyxl

import config
import database.db as db

XLSX_PATH = Path(__file__).resolve().parent.parent / "Basisinfos" / "Assets.xlsx"
SHEET_NAME = "Krypto"


@dataclass
class ImportResult:
    imported_count: int
    warnings: list[str] = field(default_factory=list)


def _parse_quantity(raw) -> float:
    if raw is None:
        return 0.0
    if isinstance(raw, str):
        raw = raw.strip().replace(",", ".")
        if not raw:
            return 0.0
        return float(raw)
    return float(raw)


def read_holdings_from_excel(path: Path = XLSX_PATH) -> dict[str, float]:
    workbook = openpyxl.load_workbook(path, data_only=True)
    sheet = workbook[SHEET_NAME]

    header = [cell.value for cell in next(sheet.iter_rows(min_row=1, max_row=1))]
    col_index = {name: idx for idx, name in enumerate(header)}
    coin_name_idx = col_index["Coin Name"]
    kurzzeichen_idx = col_index["Kurzzeichen"]
    anzahl_idx = col_index["Anzahl Coins"]

    holdings: dict[str, float] = {}
    for row in sheet.iter_rows(min_row=2):
        coin_name = row[coin_name_idx].value
        if coin_name is None:
            break
        raw_symbol = row[kurzzeichen_idx].value
        symbol = (raw_symbol or "").strip().upper()
        quantity = _parse_quantity(row[anzahl_idx].value)
        holdings[symbol] = quantity

    return holdings


def import_holdings(
    conn: sqlite3.Connection, path: Path = XLSX_PATH, source: str = "import"
) -> ImportResult:
    holdings = read_holdings_from_excel(path)
    watchlist_symbols = {asset.symbol for asset in config.get_watchlist()}
    # Konflikt-Check (Nutzer-Review 2026-07-09): holdings hat keine Historie, ein
    # Reimport ueberschreibt absolut. Wurde ein Bestand seither per Signal-
    # Rueckmeldung (ui/signals_view.py::UmsetzungDialog, source="signal_bestaetigung")
    # auf einen ANDEREN Wert gesetzt, geht dieser sonst kommentarlos verloren -
    # ueberschreibt weiterhin (Assets.xlsx bleibt die Quelle der Wahrheit), aber
    # sichtbar in der Warnliste statt still.
    existing_holdings = {h.symbol: h for h in db.get_all_holdings(conn)}

    warnings: list[str] = []
    for symbol, quantity in holdings.items():
        if symbol not in watchlist_symbols:
            warnings.append(
                f"Symbol '{symbol}' aus Assets.xlsx nicht in config.yaml watchlist gefunden."
            )
        existing = existing_holdings.get(symbol)
        if existing is not None and existing.source == "signal_bestaetigung" and existing.quantity != quantity:
            when = existing.updated_at[:16].replace("T", " ")
            warnings.append(
                f"Symbol '{symbol}': Bestand wurde zuletzt manuell per Signal-Rückmeldung auf "
                f"{existing.quantity} gesetzt (am {when}) und wird jetzt durch den Excel-Import auf "
                f"{quantity} überschrieben."
            )
        db.upsert_holding(conn, symbol, quantity, source=source)

    missing_in_xlsx = watchlist_symbols - set(holdings.keys())
    for symbol in sorted(missing_in_xlsx):
        warnings.append(f"Watchlist-Symbol '{symbol}' hat keinen Eintrag in Assets.xlsx.")

    db.mark_holdings_imported(conn)

    return ImportResult(imported_count=len(holdings), warnings=warnings)
