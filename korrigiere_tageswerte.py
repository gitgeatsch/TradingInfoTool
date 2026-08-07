"""Entfernt Portfolio-Tageswerte, die auf zu wenigen Kursen beruhen.
Standardmaessig TROCKENLAUF.

WARUM. Der taegliche Job bewertete bis zum 07.08. den LAUFENDEN Tag, obwohl er
um 06:30 laeuft - da fehlen die meisten Tageskerzen noch. Beide Zeilen, die er
je geschrieben hat, sind dadurch unbrauchbar:

    2026-08-05   1.241,35 EUR   Abdeckung  3,0 %  ( 1 von 33 Symbolen)
    2026-08-06   6.180,00 EUR   Abdeckung 42,4 %  (14 von 33 Symbolen)

Zum Vergleich: die 88 nachtraeglich rekonstruierten Zeilen liegen bei 87-98 %.

Der Bezugstag ist inzwischen der Vortag, und eine Abdeckungswache verhindert
neue Faelle (agent/portfolio_historie.py). Dieses Skript raeumt die beiden
Altlasten weg - sie stehen sonst dauerhaft in jeder Anzeige, die `wert_eur`
liest, und verfaelschen die Gegenprobe auf der Uebersichtsseite.

Z-3 SELBST IST NICHT BETROFFEN: pruefe_z3() rechnet auf `index_wert`, nicht auf
`wert_eur`. Der Index ueberspringt Symbole ohne Kurs auf beiden Seiten und
blieb dadurch stabil. Der Schaden ist die EUR-Spalte und alles, was sie liest.

Aufruf:
    python korrigiere_tageswerte.py             # Trockenlauf
    python korrigiere_tageswerte.py --anwenden
"""
import sys

import database.db as db
from agent.portfolio_historie import MIN_ABDECKUNG_FUER_TAGESWERT


def main() -> int:
    anwenden = "--anwenden" in sys.argv
    conn = db.get_connection()
    db.init_db(conn)

    zeilen = conn.execute(
        "SELECT datum, wert_eur, symbole_gesamt, symbole_ohne_kurs, quelle, index_wert "
        "FROM portfolio_wert_historie WHERE symbole_gesamt > 0 ORDER BY datum"
    ).fetchall()
    betroffen = [
        r for r in zeilen
        if (r["symbole_gesamt"] - r["symbole_ohne_kurs"]) / r["symbole_gesamt"]
        < MIN_ABDECKUNG_FUER_TAGESWERT
    ]

    print(f"{len(zeilen)} Tageswerte insgesamt, Mindestabdeckung "
          f"{MIN_ABDECKUNG_FUER_TAGESWERT * 100:.0f} %\n")
    if not betroffen:
        print("Keine Zeile unter der Schwelle - nichts zu tun.")
        return 0

    print(f"{len(betroffen)} Zeile(n) unter der Schwelle:")
    for r in betroffen:
        abd = (r["symbole_gesamt"] - r["symbole_ohne_kurs"]) / r["symbole_gesamt"] * 100
        print(f"  {r['datum']}  {r['wert_eur']:>10,.2f} EUR  Abdeckung {abd:>5.1f} %  "
              f"({r['symbole_gesamt'] - r['symbole_ohne_kurs']}/{r['symbole_gesamt']})  "
              f"quelle={r['quelle']}")

    if not anwenden:
        print("\nTROCKENLAUF - nichts geaendert. Zum Anwenden: "
              "python korrigiere_tageswerte.py --anwenden")
        return 0

    conn.executemany("DELETE FROM portfolio_wert_historie WHERE datum = ?",
                     [(r["datum"],) for r in betroffen])
    conn.commit()
    print(f"\n{len(betroffen)} Zeile(n) entfernt. Der naechste Lauf (taeglich 06:30) "
          f"schreibt den Vortag neu - dann mit vollstaendigen Kursen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
