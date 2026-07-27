# -*- coding: utf-8 -*-
"""Korrektur-Skript (2026-07-27, echter HYPE-Fund - siehe Memory
project_hype_hebel_position_kredit_rueckzahlung_fix.md): behebt bereits
haengengebliebene "offene" hebel_positions-Zeilen, deren zugrundeliegende
margin-Position auf Bitpanda tatsaechlich schon VOLLSTAENDIG geschlossen wurde,
bevor der Fix in importer/bitpanda_margin_positions.py (Kredit-Rueckzahlung als
zusaetzliches Vollstaendig-Signal) live war - der normale inkrementelle Sync
(sync_hebel_positions()) wuerde die betroffene Close-Transaktion NICHT erneut
abrufen, weil `hebel_position_last_synced_unix` bereits daran vorbeigelaufen ist.

MUSS auf dem Geraet mit echtem BITPANDA_API_KEY + echter Produktiv-DB laufen
(Notebook, siehe feedback_desktop_kein_produktivstart.md - Desktop darf hier
NICHT ran). Zwei Phasen:

1. Diagnose (IMMER, keine DB-Schreibzugriffe): laedt die KOMPLETTE Bitpanda-
   Transaktionshistorie, rekonstruiert JEDE aktuell in der DB als "offen"
   gefuehrte Position komplett neu ab dem ersten margin-Ereignis (existing=None,
   volle Historie statt inkrementellem `existing`-Akkumulator - schliesst
   damit auch Drift-Fehler aus fruehen, jetzt uebersprungenen Ereignissen aus),
   und zeigt fuer jedes Symbol den vollstaendigen Ereignis-/Entscheidungs-
   Trace (debug_symbols) sowie einen Vergleich alt vs. neu.
2. Korrektur (NUR mit --apply): schreibt die neu berechneten Positionen fuer
   Symbole, bei denen sich das Ergebnis geaendert hat, in die DB
   (db.upsert_hebel_position() - selber Konflikt-Schluessel (symbol,
   eroeffnet_am) wie der normale Sync, deshalb sicher idempotent). Ruehrt
   `hebel_position_last_synced_unix` NICHT an - der naechste normale
   inkrementelle Sync laeuft unveraendert von dort weiter, wo er stehen
   geblieben ist; diese Korrektur ist ein einmaliger, symbolgebundener
   Nachtrag ueber die volle Historie, unabhaengig vom Watermark."""
from __future__ import annotations

import os
import sys

import config
import database.db as db
from api.bitpanda import get_wallet_transactions
from importer.bitpanda_margin_positions import reconstruct_margin_positions


def main() -> None:
    apply_changes = "--apply" in sys.argv

    config.load_env()
    api_key = os.environ.get("BITPANDA_API_KEY")
    if not api_key:
        print("BITPANDA_API_KEY nicht gesetzt - Abbruch (dieses Skript braucht das echte Notebook-.env).")
        return

    conn = db.get_connection()
    try:
        offene = db.get_open_hebel_positions(conn)
        if not offene:
            print("Keine aktuell offenen Hebel-Positionen in der DB - nichts zu pruefen.")
            return

        symbole = {p.symbol for p in offene}
        print(f"Aktuell offen laut DB: {sorted(symbole)}")

        print("\nLade komplette Bitpanda-Transaktionshistorie (read-only, keine DB-Schreibzugriffe bisher)...")
        transactions = get_wallet_transactions(api_key)
        print(f"{len(transactions)} Transaktionen geladen.")

        # existing=None: volle Neu-Rekonstruktion ab dem ersten margin-Ereignis
        # je Symbol, NICHT auf dem aktuell (moeglicherweise fehlerhaften)
        # DB-Zustand aufgesetzt - schliesst Drift aus.
        result = reconstruct_margin_positions(transactions, existing=None, debug_symbols=symbole)

        print("\n=== Vergleich DB (alt) vs. Neu-Rekonstruktion ===")
        alte_by_symbol = {p.symbol: p for p in offene}
        korrekturen = []
        for symbol in sorted(symbole):
            alt = alte_by_symbol[symbol]
            neu_offen = result.offene_positionen.get(symbol)
            neu_geschlossen = next(
                (p for p in result.neu_geschlossene_positionen if p.symbol == symbol), None
            )
            print(f"\n--- {symbol} ---")
            print(
                f"  ALT (DB):  status=offen eigenkapital={alt.eigenkapital_eur} "
                f"positionswert={alt.positionswert_eur} kredit={alt.kreditbetrag_eur}"
            )
            if neu_geschlossen is not None:
                print(
                    f"  NEU:       status={neu_geschlossen.status} "
                    f"eigenkapital={neu_geschlossen.eigenkapital_eur} geschlossen_am={neu_geschlossen.geschlossen_am}"
                )
                korrekturen.append(neu_geschlossen)
            elif neu_offen is not None:
                gleich = (
                    round(neu_offen.eigenkapital_eur or 0, 2) == round(alt.eigenkapital_eur or 0, 2)
                    and round(neu_offen.positionswert_eur or 0, 2) == round(alt.positionswert_eur or 0, 2)
                )
                print(
                    f"  NEU:       status=offen eigenkapital={neu_offen.eigenkapital_eur} "
                    f"positionswert={neu_offen.positionswert_eur} kredit={neu_offen.kreditbetrag_eur} "
                    f"{'(unveraendert)' if gleich else '(WEICHT AB)'}"
                )
                if not gleich:
                    korrekturen.append(neu_offen)
            else:
                print("  NEU:       keine Position gefunden (unerwartet, manuell pruefen)")

        if not korrekturen:
            print("\nKeine Abweichungen gefunden - keine Korrektur noetig.")
            return

        print(f"\n{len(korrekturen)} Position(en) mit Abweichung: {[p.symbol for p in korrekturen]}")
        if not apply_changes:
            print("\nNUR DIAGNOSE (Trockenlauf) - keine DB-Schreibzugriffe erfolgt.")
            print("Zum tatsaechlichen Schreiben erneut mit --apply aufrufen, NACHDEM die Ausgabe oben geprueft wurde.")
            return

        for pos in korrekturen:
            db.upsert_hebel_position(conn, pos)
            print(f"Korrigiert: {pos.symbol} -> status={pos.status}")
        print("\nKorrektur geschrieben.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
