"""Setzt Rohstoff-Signalergebnisse zurueck, die gegen die FALSCHE Kursreihe
entschieden wurden (2026-08-06). Standardmaessig TROCKENLAUF.

WARUM DAS NOETIG IST. Bis zur Symboltrennung lag unter dem ETC-Symbol die
Futures-Historie. Ein OD7C-VERKAUFEN-Signal mit Entry 34,63 wurde deshalb gegen
eine Kupfer-Futures-Reihe bei 6,30 USD/lb bewertet: das Ziel galt sofort als
erreicht, und (34,63 - 6,30) / 1,37 ergab **+20,51 R**. Dieser eine Trade ist
die gesamte "Evidenz" der Assetklasse Rohstoffe.

Die Plausibilitaetsschranke in backward_tracking.simuliere_signal() verhindert
NEUE Fehlbewertungen. Sie korrigiert keine alten - der Wert steht als
Ergebnis in der DB und geht weiter in jede Systemguete ein.

WAS DIESES SKRIPT TUT. Es setzt die outcome_*-Felder betroffener Signale
zurueck auf "offen". Es erfindet KEIN Ergebnis: das Signal wird beim naechsten
Backward-Tracking-Lauf normal neu bewertet, dann gegen die rekonstruierte
ETC-Reihe auf der richtigen Skala. Kommt dabei kein Ergebnis zustande, bleibt
es offen - das ist der ehrliche Zustand, nicht ein schlechterer.

BETROFFEN sind Signale, die ALLE drei Bedingungen erfuellen:
  1. Assetklasse Rohstoffe (Symbol in SYMBOL_ZU_FUTURES_TICKER)
  2. ein gespeichertes outcome_realisiertes_crv
  3. entschieden VOR der Symboltrennung (Stichtag unten)

Aufruf:
    python korrigiere_rohstoff_outcome.py           # Trockenlauf, aendert nichts
    python korrigiere_rohstoff_outcome.py --anwenden
"""
import sys

import database.db as db
from agent.rohstoff.pipeline import SYMBOL_ZU_FUTURES_TICKER

# Tag der Symboltrennung. Alles, was davor entschieden wurde, lief gegen die
# falsch abgelegte Futures-Reihe.
STICHTAG = "2026-08-06"

FELDER = (
    "outcome_status", "outcome_geprueft_am", "outcome_entschieden_am",
    "outcome_realisiertes_crv", "outcome_datenquelle",
    "outcome_max_realisiertes_crv", "outcome_mindestziel_erreicht_am",
)


def main() -> int:
    anwenden = "--anwenden" in sys.argv
    conn = db.get_connection()
    db.init_db(conn)

    platzhalter = ",".join("?" for _ in SYMBOL_ZU_FUTURES_TICKER)
    zeilen = conn.execute(
        f"SELECT id, symbol, created_at, action, outcome_status, "
        f"outcome_realisiertes_crv, outcome_entschieden_am FROM signals "
        f"WHERE symbol IN ({platzhalter}) AND outcome_realisiertes_crv IS NOT NULL "
        f"AND (outcome_entschieden_am IS NULL OR outcome_entschieden_am < ?)",
        (*SYMBOL_ZU_FUTURES_TICKER, STICHTAG),
    ).fetchall()

    if not zeilen:
        print("Keine betroffenen Signale gefunden - nichts zu tun.")
        return 0

    print(f"{len(zeilen)} betroffene(s) Signal(e):\n")
    for r in zeilen:
        print(f"  #{r['id']}  {r['symbol']}  {str(r['created_at'])[:16]}  "
              f"{r['action']}  {r['outcome_status']}  "
              f"R={r['outcome_realisiertes_crv']:.2f}  "
              f"entschieden {str(r['outcome_entschieden_am'])[:10]}")

    if not anwenden:
        print("\nTROCKENLAUF - nichts geaendert. Zum Anwenden: "
              "python korrigiere_rohstoff_outcome.py --anwenden")
        return 0

    setz = ", ".join(f"{f} = NULL" for f in FELDER if f != "outcome_status")
    conn.execute(
        f"UPDATE signals SET outcome_status = 'offen', {setz} "
        f"WHERE id IN ({','.join('?' for _ in zeilen)})",
        tuple(r["id"] for r in zeilen),
    )
    conn.commit()
    print(f"\n{len(zeilen)} Signal(e) auf 'offen' zurueckgesetzt. Der naechste "
          f"Backward-Tracking-Lauf (taeglich 06:00) bewertet sie neu - dann "
          f"gegen die rekonstruierte ETC-Reihe auf der richtigen Skala.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
