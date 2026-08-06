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

# DREI MESSARME, nicht einer (Korrektur 2026-08-06 nach dem ersten Lauf). Der
# erste Entwurf setzte nur `outcome_*` zurueck - und uebersah, dass dasselbe
# Signal in bis zu drei getrennten Armen bewertet wird:
#
#   outcome_*               das echte Ergebnis
#   veto_outcome_*          Schatten: was waere ohne das Veto passiert?
#   selbst_halten_outcome_* Schatten: was waere ohne das selbst gewaehlte HALTEN?
#
# Folge im Betrieb: der +20,51-R-Ausreisser verschwand aus dem realen Arm, und
# im Schattenarm stand danach -18,81 R - dasselbe Instrumenten-Missverstaendnis,
# nur mit umgekehrtem Vorzeichen. Eine Korrektur, die einen Arm saeubert und die
# anderen stehen laesst, verschiebt den Fehler, statt ihn zu beheben.
#
# ZWEITE LUECKE des ersten Entwurfs: die Bedingung verlangte ein gesetztes
# `outcome_realisiertes_crv`. Ein Signal, das nur ein MFE
# (`*_max_realisiertes_crv`) hat und noch offen ist, fiel durch - obwohl auch
# dieses MFE gegen die falsche Reihe gerechnet wurde.
ARME = {
    "outcome": (
        "outcome_status", "outcome_geprueft_am", "outcome_entschieden_am",
        "outcome_realisiertes_crv", "outcome_datenquelle",
        "outcome_max_realisiertes_crv", "outcome_mindestziel_erreicht_am",
    ),
    "veto_outcome": (
        "veto_outcome_status", "veto_outcome_geprueft_am", "veto_outcome_entschieden_am",
        "veto_outcome_realisiertes_crv", "veto_outcome_max_realisiertes_crv",
        "veto_outcome_mindestziel_erreicht_am",
    ),
    "selbst_halten_outcome": (
        "selbst_halten_outcome_status", "selbst_halten_outcome_geprueft_am",
        "selbst_halten_outcome_entschieden_am", "selbst_halten_outcome_realisiertes_crv",
        "selbst_halten_outcome_max_realisiertes_crv",
        "selbst_halten_outcome_mindestziel_erreicht_am",
    ),
}

# Zeitbezug ist `*_geprueft_am` - der Zeitpunkt der BEWERTUNG, nicht der der
# Entscheidung. Ein noch offenes Signal hat kein entschieden_am, sein MFE wurde
# aber trotzdem gegen die falsche Reihe gerechnet. Ausserdem macht es die
# Korrektur idempotent: nach dem Zuruecksetzen sind alle Wertfelder NULL, die
# Bedingung greift nicht mehr.
WERTFELDER = ("realisiertes_crv", "max_realisiertes_crv")


def main() -> int:
    anwenden = "--anwenden" in sys.argv
    conn = db.get_connection()
    db.init_db(conn)

    platzhalter = ",".join("?" for _ in SYMBOL_ZU_FUTURES_TICKER)
    gesamt = 0
    for arm, felder in ARME.items():
        werte_bedingung = " OR ".join(f"{arm}_{f} IS NOT NULL" for f in WERTFELDER)
        zeilen = conn.execute(
            f"SELECT id, symbol, created_at, action, {arm}_status AS status, "
            f"{arm}_realisiertes_crv AS r, {arm}_max_realisiertes_crv AS mfe, "
            f"{arm}_geprueft_am AS geprueft FROM signals "
            f"WHERE symbol IN ({platzhalter}) AND ({werte_bedingung}) "
            f"AND ({arm}_geprueft_am IS NULL OR {arm}_geprueft_am < ?)",
            (*SYMBOL_ZU_FUTURES_TICKER, STICHTAG),
        ).fetchall()
        if not zeilen:
            print(f"  {arm}: nichts zu korrigieren")
            continue
        print(f"  {arm}: {len(zeilen)} Signal(e)")
        for r in zeilen:
            wert = f"R={r['r']:.2f}" if r["r"] is not None else f"MFE={r['mfe']:.2f}"
            print(f"      #{r['id']}  {r['symbol']}  {str(r['created_at'])[:16]}  "
                  f"{r['action']}  {r['status']}  {wert}  "
                  f"geprueft {str(r['geprueft'])[:10]}")
        gesamt += len(zeilen)
        if anwenden:
            setz = ", ".join(f"{f} = NULL" for f in felder if not f.endswith("_status"))
            conn.execute(
                f"UPDATE signals SET {arm}_status = NULL, {setz} "
                f"WHERE id IN ({','.join('?' for _ in zeilen)})",
                tuple(r["id"] for r in zeilen),
            )
            conn.commit()

    if not gesamt:
        print("\nNichts zu tun - alle drei Messarme sind sauber.")
        return 0
    if not anwenden:
        print(f"\nTROCKENLAUF - {gesamt} Eintrag/Eintraege betroffen, nichts geaendert. "
              f"Zum Anwenden: python korrigiere_rohstoff_outcome.py --anwenden")
        return 0
    print(f"\n{gesamt} Eintrag/Eintraege zurueckgesetzt. Der naechste "
          f"Backward-Tracking-Lauf (taeglich 06:00) bewertet neu - dann gegen die "
          f"rekonstruierte ETC-Reihe auf der richtigen Skala.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
