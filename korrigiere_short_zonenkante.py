"""Rechnet die gespeicherten SHORT-Ausgaenge auf die Gate-Zonenkante um.

WOZU. Bis zum 09.08. nahmen die Outcome-Tracker fuer BEIDE Handelsrichtungen die
`_von`-Kante einer Preiszone, waehrend `_zonen_absolut()` - die Quelle des CRV,
das ueber die Mindestgrenze entscheidet - bei SHORT auf `_bis` spiegelt. Ein
Trade wurde damit nach der einen Rechnung genehmigt und nach einer anderen
bewertet. Herleitung im Docstring von `backward_tracking._zonen_schwelle()`.

Der Code ist seit `_zonen_schwelle()` korrekt - das gilt aber nur fuer KUENFTIGE
Aufloesungen. Bereits gespeicherte Zeilen tragen weiterhin die alten Werte, und
aufgeloeste Zeilen sieht das taegliche Backward-Tracking nicht mehr an. Dieses
Skript holt sie nach.

WIE, UND WARUM NICHT ANDERS. Es ruft die PRODUKTIVEN Checker-Funktionen auf und
schreibt ueber die produktiven db.update_*-Funktionen. Kein Nachbau: zwei
Implementierungen derselben Aufloesung laufen garantiert auseinander, und genau
dieser Riss war ja der Defekt. Betroffene Zeilen werden dabei NICHT
zurueckgesetzt - sie werden neu bewertet und der neue Wert geschrieben.

ERWARTETE WIRKUNG (gemessen am 09.08. gegen eine Kopie der Produktions-DB, 128
auswertbare Zeilen): die Summe wandert von -44,69 R auf -59,91 R. Die alte
Konvention hat den Schatten-Arm geschmeichelt - erreichbare R-Werte lagen weit
ueber dem jeweiligen CRV (+9,43 bei CRV 1,79). Es geht hier NICHT um eine
Verbesserung der Zahlen, sondern um ihre Richtigkeit.

LONG-Zeilen werden nicht angefasst. Dort waren beide Konventionen schon immer
identisch, und ein unnoetiger Schreibvorgang koennte nur schaden.

BETRIEB. Standardmaessig ein Trockenlauf: er zeigt, was sich aendern wuerde, und
schreibt nichts. Erst `--anwenden` schreibt. Vorher ein Backup ziehen - das
Skript verlangt die Bestaetigung, dass eines existiert.

    python korrigiere_short_zonenkante.py --db <pfad>              # Trockenlauf
    python korrigiere_short_zonenkante.py --db <pfad> --anwenden --backup-vorhanden
"""
from __future__ import annotations

import argparse
import sqlite3
import sys

import database.db as db
from agent.krypto.backward_tracking import (
    OUTCOME_STOP_LOSS,
    OUTCOME_TAKE_PROFIT,
    _RESOLVED_OUTCOMES,
    _zonen_absolut,
    check_signal_outcome,
    check_signal_selbst_halten_outcome,
    check_signal_veto_shadow_outcome,
)
from agent.krypto.hebel_backward_tracking import (
    check_hebel_signal_outcome,
    check_hebel_signal_selbst_halten_outcome,
    check_hebel_signal_veto_shadow_outcome,
)

# (Tabelle, Spaltenpraefix, Checker, Schreiber, Lader)
_ARME = [
    ("signals", "outcome_", check_signal_outcome,
     db.update_signal_outcome, db.get_signal_by_id),
    ("signals", "veto_outcome_", check_signal_veto_shadow_outcome,
     db.update_signal_veto_shadow_outcome, db.get_signal_by_id),
    ("signals", "selbst_halten_outcome_", check_signal_selbst_halten_outcome,
     db.update_signal_selbst_halten_outcome, db.get_signal_by_id),
    ("hebel_signals", "outcome_", check_hebel_signal_outcome,
     db.update_hebel_signal_outcome, db.get_hebel_signal_by_id),
    ("hebel_signals", "veto_outcome_", check_hebel_signal_veto_shadow_outcome,
     db.update_hebel_signal_veto_shadow_outcome, db.get_hebel_signal_by_id),
    ("hebel_signals", "selbst_halten_outcome_", check_hebel_signal_selbst_halten_outcome,
     db.update_hebel_signal_selbst_halten_outcome, db.get_hebel_signal_by_id),
]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True)
    p.add_argument("--anwenden", action="store_true",
                   help="tatsaechlich schreiben (sonst nur Trockenlauf)")
    p.add_argument("--backup-vorhanden", action="store_true",
                   help="Bestaetigung, dass ein DB-Backup existiert")
    args = p.parse_args()

    if args.anwenden and not args.backup_vorhanden:
        print("ABBRUCH: --anwenden verlangt --backup-vorhanden. Erst ein Backup "
              "ziehen (extract_notebook_diagnose.py::_db_backup()), dann erneut.")
        return 2

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    from config import get_watchlist
    watchlist = get_watchlist()

    platzhalter = ",".join("?" for _ in _RESOLVED_OUTCOMES)
    geaendert = unveraendert = uebersprungen = 0
    summe_alt = summe_neu = 0.0
    zeilen: list[tuple] = []

    for tabelle, praefix, checker, schreiber, lader in _ARME:
        spalten = {r[1] for r in conn.execute(f"PRAGMA table_info({tabelle})")}
        if f"{praefix}status" not in spalten:
            continue
        rows = conn.execute(
            f"SELECT * FROM {tabelle} WHERE {praefix}status IN ({platzhalter})",
            _RESOLVED_OUTCOMES,
        ).fetchall()
        for row in rows:
            z = _zonen_absolut(row)
            if z is None or not z["ist_short"]:
                continue  # LONG und zonenlose Zeilen bleiben unberuehrt
            signal = lader(conn, row["id"])
            if signal is None:
                uebersprungen += 1
                continue
            try:
                status, extra = checker(conn, signal, watchlist)
            except Exception as exc:  # noqa: BLE001 - eine Zeile darf den Lauf nicht kippen
                print(f"  UEBERSPRUNGEN {tabelle} id={row['id']}: "
                      f"{type(exc).__name__}: {exc}")
                uebersprungen += 1
                continue
            if status not in (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS):
                # Mit der korrekten Kante loest die Zeile nicht mehr auf. Das
                # ist ein echtes Ergebnis (der Stop lag weiter weg), aber ein
                # Zurueckschreiben auf 'offen' waere ein anderer Eingriff als
                # der hier beauftragte - deshalb nur melden.
                print(f"  HINWEIS {tabelle}/{praefix} id={row['id']} {row['symbol']}: "
                      f"loest mit der Gate-Kante nicht mehr auf ({status}) - "
                      f"nicht geaendert")
                uebersprungen += 1
                continue

            alt_r = row[f"{praefix}realisiertes_crv"]
            neu_r = extra.get("realisiertes_crv")
            if alt_r is not None and neu_r is not None:
                summe_alt += alt_r
                summe_neu += neu_r
            if alt_r == neu_r and row[f"{praefix}status"] == status:
                unveraendert += 1
                continue
            geaendert += 1
            zeilen.append((tabelle, praefix, row["id"], row["symbol"],
                           row[f"{praefix}status"], alt_r, status, neu_r))
            if args.anwenden:
                schreiber(
                    conn, row["id"], status,
                    entschieden_am=extra.get("entschieden_am"),
                    realisiertes_crv=neu_r,
                    max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                    mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
                )

    if args.anwenden:
        conn.commit()

    print()
    print(f"{'Tabelle':14} {'Arm':24} {'id':>6} {'Symbol':8} "
          f"{'alt':>9} -> {'neu':>9}")
    for t, pre, i, sym, st_a, r_a, st_n, r_n in zeilen[:40]:
        ra = "None" if r_a is None else f"{r_a:+.2f}"
        rn = "None" if r_n is None else f"{r_n:+.2f}"
        marke = "  STATUS" if st_a != st_n else ""
        print(f"{t:14} {pre:24} {i:>6} {sym:8} {ra:>9} -> {rn:>9}{marke}")
    if len(zeilen) > 40:
        print(f"  ... und {len(zeilen) - 40} weitere")

    print()
    print(f"  geaendert:      {geaendert}")
    print(f"  unveraendert:   {unveraendert}")
    print(f"  uebersprungen:  {uebersprungen}")
    print(f"  Summe R alt:    {summe_alt:+.2f}")
    print(f"  Summe R neu:    {summe_neu:+.2f}   Differenz {summe_neu - summe_alt:+.2f}")
    print()
    print("GESCHRIEBEN." if args.anwenden else
          "TROCKENLAUF - nichts geschrieben. Mit --anwenden --backup-vorhanden ausfuehren.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
