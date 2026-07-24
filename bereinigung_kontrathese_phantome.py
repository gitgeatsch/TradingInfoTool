# -*- coding: utf-8 -*-
"""Einmaliges Bereinigungs-Skript (2026-07-24): markiert die vor der
Kontrathese-Uebersetzung entstandenen NEAR/HYPE-SHORT-ERÖFFNEN-Phantom-
Signale als OUTCOME_NICHT_ANWENDBAR - nimmt sie aus dem "offen"-Pool und aus
der Provider-Performance-Statistik (Win-Rate/CRV) heraus, OHNE irgendetwas
zu loeschen (facts_json/Zonen/alle anderen Felder bleiben unveraendert, volle
Audit-Spur erhalten).

Kriterium: symbol IN ('NEAR','HYPE') AND richtung='SHORT' AND action='ERÖFFNEN'
AND outcome_status IS NULL. Beide Symbole hatten im gesamten fraglichen
Zeitraum durchgehend eine offene LONG-Position - jedes SHORT-ERÖFFNEN fuer
diese zwei Symbole in diesem Zeitraum ist per Definition ein Kontrathese-
Phantom (siehe Session-Analyse 2026-07-24), keine echte, je ausfuehrbare
These.

WICHTIG: Standardmaessig NUR Dry-Run (zeigt betroffene Zeilen, aendert
nichts). Erst mit --apply werden die Aenderungen tatsaechlich geschrieben.
Auf dem Notebook ausfuehren (dort liegt die echte Produktions-DB), NICHT auf
dem Desktop gegen eine veraltete Kopie. Vor dem Ausfuehren: git pull, damit
die Kontrathese-Uebersetzung selbst schon aktiv ist (sonst wuerden ab dem
naechsten Zyklus sofort wieder neue Phantome entstehen)."""
from __future__ import annotations

import sys

import database.db as db
from agent.krypto.backward_tracking import OUTCOME_NICHT_ANWENDBAR

BETROFFENE_SYMBOLE = ("NEAR", "HYPE")


def main() -> None:
    apply = "--apply" in sys.argv
    conn = db.get_connection()  # nutzt die produktive DB_PATH aus database/db.py

    placeholders = ", ".join("?" for _ in BETROFFENE_SYMBOLE)
    rows = conn.execute(
        f"""
        SELECT id, symbol, created_at, confidence_pct, llm_model
        FROM hebel_signals
        WHERE symbol IN ({placeholders})
          AND richtung = 'SHORT'
          AND action = 'ERÖFFNEN'
          AND outcome_status IS NULL
        ORDER BY created_at
        """,
        BETROFFENE_SYMBOLE,
    ).fetchall()

    print(f"{len(rows)} betroffene Kontrathese-Phantom-Signale gefunden:\n")
    for r in rows:
        print(f"  id={r['id']:<6} {r['created_at']}  {r['symbol']:5s}  conf={r['confidence_pct']}  llm={r['llm_model']}")

    if not rows:
        print("\nNichts zu tun.")
        return

    if not apply:
        print("\nDRY-RUN - keine Aenderung geschrieben. Zum Anwenden erneut mit '--apply' aufrufen.")
        return

    for r in rows:
        db.update_hebel_signal_outcome(
            conn, r["id"], OUTCOME_NICHT_ANWENDBAR,
            datenquelle="kontrathese_phantom_bereinigung_2026-07-24",
        )
    print(f"\n{len(rows)} Signale auf outcome_status='{OUTCOME_NICHT_ANWENDBAR}' gesetzt.")


if __name__ == "__main__":
    main()
