"""Findet gespeicherte Ergebnisse, die zur eigenen Kursreihe nicht passen.

DER ANLASS. `OD7C` #2361 traegt seit dem 06.08. **+20,37 R** - der einzige
nennenswerte Wert der Assetklasse Rohstoffe, und er ist falsch: die Bewertung
lief gegen die Kupfer-Futures-Reihe (~6,30 USD/lb), die damals unter dem
ETC-Symbol lag, waehrend das Signal bei 34,63 einstieg.

WARUM DAS BIS HEUTE DRINSTAND, obwohl es zwei Reparaturen gab:

  1. Die Plausibilitaetsschranke vom 06.08. sitzt in `simuliere_signal()` - im
     SIMULATIONS-Pfad. Der Live-Tracker (`check_signal_outcome()`) hat keine.
  2. `korrigiere_rohstoff_outcome.py` traf die Zeile nicht mehr: sein Kriterium
     ist ein STICHTAG (`geprueft_am < 2026-08-06`), und `geprueft_am` steht
     inzwischen auf dem 08.08.

Beide Reparaturen waren richtig und beide greifen hier nicht. Das Muster
dahinter: **ein Kriterium, das auf einem Datum beruht, veraltet mit dem Datum.**

DAS KRITERIUM HIER PRUEFT SICH SELBST. Aus dem gespeicherten R-Wert laesst sich
der Ausstiegspreis zurueckrechnen, den die Bewertung unterstellt hat:

    LONG:   exit = entry + R * risiko
    SHORT:  exit = entry - R * risiko

Liegt dieser Preis weit ausserhalb der Spanne, die die Kursreihe des Symbols im
fraglichen Zeitraum ueberhaupt hergibt, dann hat die Bewertung eine ANDERE
Reihe gesehen als die, die heute dasteht. Bei #2361 ergibt die Rueckrechnung
6,72 - die Reihe lief in diesen Tagen zwischen 33,3 und 34,9.

Das gilt unabhaengig von Datum, Symbol und Assetklasse und findet damit auch
den naechsten Fall dieser Familie, nicht nur den bekannten.

BEWUSST KEIN NEUES ERGEBNIS. Betroffene Zeilen werden auf `offen`
zurueckgesetzt, nicht neu berechnet. Das naechste Backward-Tracking bewertet sie
regulaer gegen die richtige Reihe - und kommt dabei keins zustande, bleiben sie
offen. Das ist der ehrliche Zustand, nicht der schlechtere.

    python pruefe_outcome_plausibilitaet.py --db <pfad>                 # Trockenlauf
    python pruefe_outcome_plausibilitaet.py --db <pfad> --anwenden --backup-vorhanden
"""
from __future__ import annotations

import argparse
import sqlite3
import sys

from agent.krypto.backward_tracking import _RESOLVED_OUTCOMES, _zonen_absolut

# Wie weit darf der zurueckgerechnete Ausstieg ueber die beobachtete Spanne
# hinausragen, bevor er als "andere Reihe" gilt? Gaps, Zonen-Grenzen und der
# gap_bewusste Fill koennen den Ausstieg legitim knapp ausserhalb des
# Hoch/Tief-Bandes legen - Faktor 1,5 laesst das durch und faengt erst die
# Groessenordnungs-Verwechslung. Bewusst weit: lieber ein Fall zu wenig
# gemeldet als eine gesunde Zeile zurueckgesetzt.
_TOLERANZ = 1.5

_ARME = ("outcome", "veto_outcome", "selbst_halten_outcome")


def _spanne(conn, symbol: str, ab: str, bis: str | None) -> tuple[float, float] | None:
    if bis:
        row = conn.execute(
            "SELECT MIN(low) lo, MAX(high) hi FROM price_history_ohlc "
            "WHERE symbol = ? AND date >= ? AND date <= ?",
            (symbol, ab, bis),
        ).fetchone()
        if row and row["lo"] is not None:
            return row["lo"], row["hi"]
    # Kein Entscheidungsdatum oder kein Treffer im Fenster: die ganze Reihe ab
    # dem Signaltag. Grosszuegiger, also konservativer.
    row = conn.execute(
        "SELECT MIN(low) lo, MAX(high) hi FROM price_history_ohlc "
        "WHERE symbol = ? AND date >= ?",
        (symbol, ab),
    ).fetchone()
    if row and row["lo"] is not None:
        return row["lo"], row["hi"]
    return None


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--db", required=True)
    p.add_argument("--anwenden", action="store_true")
    p.add_argument("--backup-vorhanden", action="store_true")
    args = p.parse_args()

    if args.anwenden and not args.backup_vorhanden:
        print("ABBRUCH: --anwenden verlangt --backup-vorhanden.")
        return 2

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    platzhalter = ",".join("?" for _ in _RESOLVED_OUTCOMES)
    treffer: list[dict] = []
    geprueft = ohne_reihe = 0

    for tabelle in ("signals", "hebel_signals"):
        spalten = {r[1] for r in conn.execute(f"PRAGMA table_info({tabelle})")}
        for arm in _ARME:
            if f"{arm}_status" not in spalten:
                continue
            rows = conn.execute(
                f"SELECT * FROM {tabelle} WHERE {arm}_status IN ({platzhalter}) "
                f"AND {arm}_realisiertes_crv IS NOT NULL",
                _RESOLVED_OUTCOMES,
            ).fetchall()
            for row in rows:
                z = _zonen_absolut(row)
                if z is None:
                    continue
                geprueft += 1
                r_wert = row[f"{arm}_realisiertes_crv"]
                exit_preis = (z["entry"] - r_wert * z["risiko"]) if z["ist_short"] \
                    else (z["entry"] + r_wert * z["risiko"])
                sp = _spanne(conn, row["symbol"], str(row["created_at"])[:10],
                             str(row[f"{arm}_entschieden_am"] or "")[:10] or None)
                if sp is None:
                    ohne_reihe += 1
                    continue
                lo, hi = sp
                spannweite = hi - lo
                if exit_preis < lo - _TOLERANZ * spannweite or \
                   exit_preis > hi + _TOLERANZ * spannweite:
                    treffer.append({
                        "tabelle": tabelle, "arm": arm, "id": row["id"],
                        "symbol": row["symbol"], "r": r_wert,
                        "exit": exit_preis, "lo": lo, "hi": hi,
                        "entry": z["entry"], "crv": z["crv"],
                    })

    print(f"Geprueft: {geprueft} aufgeloeste Zeilen mit R-Wert und Zonen")
    print(f"Ohne Kursreihe (nicht beurteilbar): {ohne_reihe}")
    print()
    if not treffer:
        print("Kein unplausibler Ausgang gefunden - alle Ausstiege liegen in der "
              "Spanne, die die jeweilige Kursreihe hergibt.")
        conn.close()
        return 0

    print(f"UNPLAUSIBEL: {len(treffer)} Zeile(n). Der zurueckgerechnete Ausstieg "
          f"liegt ausserhalb dessen, was die Kursreihe hergibt:")
    print()
    print(f"  {'Tabelle':14} {'Arm':22} {'id':>6} {'Symbol':7} {'R':>8} "
          f"{'Entry':>9} {'-> Exit':>10} {'Reihe von..bis':>22}")
    for t in treffer:
        print(f"  {t['tabelle']:14} {t['arm']:22} {t['id']:>6} {t['symbol']:7} "
              f"{t['r']:>+8.2f} {t['entry']:>9.3f} {t['exit']:>10.3f} "
              f"{t['lo']:>10.3f}..{t['hi']:<10.3f}")

    if args.anwenden:
        for t in treffer:
            spalten = {r[1] for r in conn.execute(f"PRAGMA table_info({t['tabelle']})")}
            felder = [c for c in spalten if c.startswith(f"{t['arm']}_")
                      and c != f"{t['arm']}_status"]
            setz = ", ".join(f"{f} = NULL" for f in felder)
            conn.execute(
                f"UPDATE {t['tabelle']} SET {t['arm']}_status = 'offen', {setz} "
                f"WHERE id = ?", (t["id"],),
            )
        conn.commit()
        print()
        print(f"ZURUECKGESETZT: {len(treffer)} Zeile(n) stehen auf 'offen'. Das "
              f"naechste Backward-Tracking bewertet sie gegen die richtige Reihe.")
    else:
        print()
        print("TROCKENLAUF - nichts geschrieben.")
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
