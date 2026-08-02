"""Altbewertungen fuer die neue Exit-Konvention zuruecksetzen (2026-08-02, Task #604).

Bis zum 02.08. nahm die Spot-Familie den Tages-Extremwert als Ausfuehrungspreis,
die Hebel-Seite den Schwellwert. Seither gilt fuer beide die Zonen-Grenze, bei
einem Gap der Eroeffnungskurs (Regelwerksmanual Kapitel 21). Alle vorher
aufgeloesten Bewertungen stehen damit nach einer anderen Konvention in der
Datenbank - ohne Bereinigung mischen sich zwei Massstaebe in Expectancy und SQN.

ANSATZ: keine zweite Berechnungslogik, sondern outcome_status der betroffenen
Zeilen auf NULL zuruecksetzen. Der naechste regulaere backward_tracking_job
bewertet sie dann mit dem neuen Code und denselben Kursdaten neu. Damit kann
die Neuberechnung nicht von der Produktivlogik abweichen.

Sicher, weil:
- nur AUFGELOESTE Bewertungen betroffen sind (take_profit/stop_loss/liquidation).
  'ueberholt' und 'abgelaufen' tragen kein realisiertes CRV und bleiben unberuehrt.
- TP/SL vor dem Ueberholt-/Ablauf-Check geprueft werden: ein damals aufgeloestes
  Signal wird wieder aufgeloest, nur mit korrigiertem Preis.
- die Preishistorie waechst und nicht schrumpft - die Ausloesetage sind weiter da.

AUFRUF (am Notebook, wo die Produktiv-DB liegt):
    python neuberechnung_exit_konvention.py            # nur zaehlen, nichts aendern
    python neuberechnung_exit_konvention.py --schreiben
Danach den backward_tracking_job abwarten (taeglich 06:00) oder die App neu
starten - der Nachhol-Mechanismus holt den Termin nach.
"""
from __future__ import annotations

import sys

import database.db as db
from agent.krypto.backward_tracking import (
    OUTCOME_LIQUIDATION,
    OUTCOME_STOP_LOSS,
    OUTCOME_TAKE_PROFIT,
)

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

    if schreiben:
        conn.commit()
        print(f"\n{gesamt} Bewertungen zurueckgesetzt. Der naechste "
              f"backward_tracking_job bewertet sie mit der neuen Konvention neu.")
    else:
        print(f"\n{gesamt} Bewertungen waeren betroffen. "
              f"Zum Ausfuehren: --schreiben")
    conn.close()


if __name__ == "__main__":
    main()
