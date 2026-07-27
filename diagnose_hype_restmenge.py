# -*- coding: utf-8 -*-
"""Diagnose (2026-07-27, Fortsetzung HYPE-Fund): sucht die KOMPLETTE (nicht nur
margin-getaggte) Transaktionshistorie fuer HYPE rund um den bekannten Close-
Zeitpunkt (2026-07-26 16:22 UTC), um zu pruefen, ob die verbleibenden ~3,89
HYPE (11,59 Open minus 7,70 verkauft) ueber eine Transaktion OHNE "margin"-Tag
aus der Margin-Wallet abgeflossen sind (z.B. interner Transfer in die normale
Wallet) - reconstruct_margin_positions() filtert am Anfang alles ohne
"margin"-Tag heraus und wuerde so ein Ereignis nie sehen.

Rein lesend, KEINE DB-Schreibzugriffe. Muss auf dem Notebook laufen (echter
BITPANDA_API_KEY)."""
from __future__ import annotations

import os
from datetime import datetime, timezone

import config
from api.bitpanda import get_wallet_transactions

CLOSE_TS = 1785082937  # 2026-07-26T16:22:17Z, bekannter margin_close-Zeitpunkt fuer HYPE
FENSTER_SEKUNDEN = 3600  # +/- 1 Stunde


def _iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def main() -> None:
    config.load_env()
    api_key = os.environ.get("BITPANDA_API_KEY")
    if not api_key:
        print("BITPANDA_API_KEY nicht gesetzt - Abbruch.")
        return

    print("Lade komplette Bitpanda-Transaktionshistorie (read-only)...")
    transactions = get_wallet_transactions(api_key)
    print(f"{len(transactions)} Transaktionen geladen.\n")

    print(f"=== ALLE HYPE-Transaktionen im Fenster {_iso(CLOSE_TS - FENSTER_SEKUNDEN)} bis {_iso(CLOSE_TS + FENSTER_SEKUNDEN)} (OHNE margin-Filter) ===\n")
    treffer = [
        t for t in transactions
        if t.cryptocoin_symbol == "HYPE"
        and CLOSE_TS - FENSTER_SEKUNDEN <= t.unix_timestamp <= CLOSE_TS + FENSTER_SEKUNDEN
    ]
    if not treffer:
        print("Keine HYPE-Transaktionen in diesem Fenster gefunden (unerwartet).")
        return

    for t in sorted(treffer, key=lambda x: x.unix_timestamp):
        print(
            f"{_iso(t.unix_timestamp)}  type={t.type} in_or_out={t.in_or_out} "
            f"amount_wallet={t.amount_cryptocoin_wallet} trade_qty={t.trade_amount_cryptocoin} "
            f"trade_fiat={t.trade_amount_fiat} tags={t.tags}"
        )

    print("\n=== ALLE HYPE-Transaktionen insgesamt (komplette Historie, OHNE margin-Filter) ===\n")
    alle_hype = [t for t in transactions if t.cryptocoin_symbol == "HYPE"]
    for t in sorted(alle_hype, key=lambda x: x.unix_timestamp):
        print(
            f"{_iso(t.unix_timestamp)}  type={t.type} in_or_out={t.in_or_out} "
            f"amount_wallet={t.amount_cryptocoin_wallet} trade_qty={t.trade_amount_cryptocoin} "
            f"trade_fiat={t.trade_amount_fiat} tags={t.tags}"
        )


if __name__ == "__main__":
    main()
