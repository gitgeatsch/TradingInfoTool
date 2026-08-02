"""Altbewertungen fuer die neue Exit-Konvention zuruecksetzen (2026-08-02, Task #604).

Bis zum 02.08. nahm die Spot-Familie den Tages-Extremwert als Ausfuehrungspreis,
die Hebel-Seite den Schwellwert. Seither gilt fuer beide die Zonen-Grenze, bei
einem Gap der Eroeffnungskurs (Regelwerksmanual Kapitel 21). Alle vorher
aufgeloesten Bewertungen stehen damit nach einer anderen Konvention in der
Datenbank - ohne Bereinigung mischen sich zwei Massstaebe in Expectancy und SQN.

ANSATZ: keine zweite Berechnungslogik, sondern outcome_status der betroffenen
Zeilen auf NULL zuruecksetzen und anschliessend run_backward_tracking() /
run_hebel_backward_tracking() aufrufen - dieselben Funktionen wie im Scheduler.
Damit kann die Neuberechnung nicht von der Produktivlogik abweichen.

Sicher, weil:
- nur AUFGELOESTE Bewertungen betroffen sind (take_profit/stop_loss/liquidation).
  'ueberholt' und 'abgelaufen' tragen kein realisiertes CRV und bleiben unberuehrt.
- TP/SL vor dem Ueberholt-/Ablauf-Check geprueft werden: ein damals aufgeloestes
  Signal wird wieder aufgeloest, nur mit korrigiertem Preis.
- die Preishistorie waechst und nicht schrumpft - die Ausloesetage sind weiter da.

AUFRUF (am Notebook, wo die Produktiv-DB liegt):
    python neuberechnung_exit_konvention.py            # nur zaehlen, nichts aendern
    python neuberechnung_exit_konvention.py --schreiben
Der Schreibmodus bewertet direkt im Anschluss neu (dieselben Funktionen wie der
taegliche 06:00-Job) - danach ist ein Notebook-Export sinnvoll. Ohne diesen
Schritt stuende die DB bis 06:00 ohne Ergebnisse da.
"""
from __future__ import annotations

import sys

import config
import database.db as db
from agent.krypto.backward_tracking import (
    OUTCOME_LIQUIDATION,
    OUTCOME_STOP_LOSS,
    OUTCOME_TAKE_PROFIT,
    run_backward_tracking,
)
from agent.krypto.hebel_backward_tracking import run_hebel_backward_tracking

AUFGELOEST = (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS, OUTCOME_LIQUIDATION)

# (Tabelle, Status-Spalte, weitere Spalten die mit zurueckgesetzt werden)
ZWEIGE = [
    ("signals", "outcome", ["entschieden_am", "realisiertes_crv", "datenquelle"]),
    ("signals", "veto_outcome", ["entschieden_am", "realisiertes_crv"]),
    ("signals", "selbst_halten_outcome", ["entschieden_am", "realisiertes_crv"]),
    ("hebel_signals", "outcome", ["entschieden_am", "realisiertes_crv", "datenquelle"]),
    ("hebel_signals", "veto_outcome", ["entschieden_am", "realisiertes_crv"]),
    ("hebel_signals", "selbst_halten_outcome", ["entschieden_am", "realisiertes_crv"]),
]


def main() -> None:
    schreiben = "--schreiben" in sys.argv
    conn = db.get_connection()
    platzhalter = ", ".join("?" for _ in AUFGELOEST)
    gesamt = 0

    print(f"{'SCHREIBMODUS' if schreiben else 'TROCKENLAUF (nichts wird geaendert)'}\n")
    for tabelle, praefix, extra in ZWEIGE:
        status_spalte = f"{praefix}_status"
        spalten = {r[1] for r in conn.execute(f"PRAGMA table_info({tabelle})")}
        if status_spalte not in spalten:
            print(f"  {tabelle}.{status_spalte}: Spalte fehlt - uebersprungen")
            continue

        anzahl = conn.execute(
            f"SELECT COUNT(*) FROM {tabelle} WHERE {status_spalte} IN ({platzhalter})",
            AUFGELOEST,
        ).fetchone()[0]
        gesamt += anzahl
        print(f"  {tabelle}.{status_spalte}: {anzahl} aufgeloeste Bewertungen")

        if schreiben and anzahl:
            # geprueft_am bewusst NICHT zuruecksetzen - der Wert dokumentiert,
            # wann zuletzt geprueft wurde, und stoert die Neubewertung nicht.
            sets = [f"{status_spalte} = NULL"]
            sets += [f"{praefix}_{feld} = NULL" for feld in extra
                     if f"{praefix}_{feld}" in spalten]
            conn.execute(
                f"UPDATE {tabelle} SET {', '.join(sets)} "
                f"WHERE {status_spalte} IN ({platzhalter})",
                AUFGELOEST,
            )

    if not schreiben:
        print(f"\n{gesamt} Bewertungen waeren betroffen. "
              f"Zum Ausfuehren: --schreiben")
        conn.close()
        return

    conn.commit()
    print(f"\n{gesamt} Bewertungen zurueckgesetzt.")

    # Direkt neu bewerten statt auf den 06:00-Job zu warten: sonst stuende die
    # DB bis dahin ohne Ergebnisse da, und ein Export dazwischen waere leer.
    # Bewusst dieselben Funktionen wie im Scheduler - keine Sonderlogik.
    print("\nNeubewertung laeuft (dieselben Funktionen wie der taegliche Job)...")
    watchlist = config.get_watchlist()
    cfg = config.load_config()
    spot = run_backward_tracking(conn, watchlist, cfg)
    hebel = run_hebel_backward_tracking(conn, watchlist, cfg)
    print(f"  Spot : {spot.geprueft_count} geprueft, "
          f"{spot.resolved_take_profit} Take-Profit, {spot.resolved_stop_loss} Stop-Loss, "
          f"{spot.still_open} weiter offen")
    print(f"  Hebel: {hebel.geprueft_count} geprueft, "
          f"{hebel.resolved_take_profit} Take-Profit, {hebel.resolved_stop_loss} Stop-Loss, "
          f"{hebel.resolved_liquidation} Liquidation, {hebel.still_open} weiter offen")
    print("\nFertig - jetzt ist ein Notebook-Export sinnvoll.")
    conn.close()


if __name__ == "__main__":
    main()
