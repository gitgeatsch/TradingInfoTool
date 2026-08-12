# -*- coding: utf-8 -*-
"""Makro-Historie nachladen: Netto-Liquiditaet und Zinskurve (Paket 4, 12.08.2026).

DER ANLASS - und er ist derselbe wie bei Fear & Greed, nur groesser.

Der Thesen-Abgleich (`agent/kategorie_thesen.py`) rechnet mit Groessen, die
NICHT aus unseren Kursreihen stammen: Netto-Liquiditaet, Zinskurve,
Dollar-Index, COT-Positionierung. Genau das, was dem Lagebild fehlt - alle
bisherigen Fakten lesen dieselben Kerzen.

ABER ER LIEFERT HEUTE NICHTS. Gemessen am 12.08.:

    13 von 57 Assets tragen eine Hauptgruppe (alle Nicht-Krypto)
    die Tabelle `thesen` hat NULL Zeilen

`build_these_abgleich_fact()` gibt deshalb ueberall `None` zurueck. Der
Codepfad laeuft in vier Pipelines, Ausgabe erzeugt er keine. Meine fruehere
Aussage "laeuft in 4 von 6 Pipelines" beschrieb den Pfad, nicht das Ergebnis.

DIE AUFLOESUNG: die Daten sind thesenunabhaengig, nur das URTEIL nicht.
`_net_liquidity_trend()` und `macro.get_zinskurve()` brauchen keine These -
allein `_einschaetzung_aus_richtung(bullisch, these.richtung)` tut es. Also
holen wir die Daten und lassen das Urteil weg. Das ist ohnehin richtiger: eine
These des Nutzers als Fakt an das Modell zu geben waere ein Anker (Ankerindex
0,45, Experten-Anker am staerksten).

WARUM ERST NACHLADEN. Beide Groessen sind LIVE abrufbar und historisch NICHT
gespeichert - `macro_snapshot` traegt 0 Dollar-Index-Werte und 7 Zinswerte, alle
aus dem Juli 2026. Ein live geholter Makrowert in einem Anker von 2022 waere
kein Fakt, sondern ein Leck: er wuerde die Zukunft in die Vergangenheit tragen
und jede Messung zerstoeren.

    NETTO-LIQUIDITAET   FRED: WALCL - WTREGEN - RRPONTSYD
                        (Fed-Bilanz minus Treasury General Account minus
                        Reverse-Repo). WALCL/WTREGEN in Mio., RRP in Mrd. -
                        die Einheiten sind im Quellmodul verifiziert.
    ZINSKURVE           yfinance ^TNX (10 Jahre) und ^IRX (13 Wochen).
                        Der Spread ist das Standardmass fuer die Steilheit.

    python lade_makro_historie_nach.py              Trockenlauf
    python lade_makro_historie_nach.py --schreiben
"""
from __future__ import annotations

import argparse
import os
import sqlite3
from datetime import datetime, timezone

DB = "data/tradinginfotool.db"
START = "2017-01-01"

# Neue Spalten. Bewusst mit Einheit im Namen, wo sie nicht selbsterklaerend ist -
# der Einheitenfehler (Mio. gegen Mrd.) ist in diesem Projekt schon einmal
# teuer gewesen.
SPALTEN = {
    "netto_liquiditaet_mrd": "REAL",
    "rendite_10j_pct": "REAL",
    "rendite_kurz_pct": "REAL",
}


def _spalten_anlegen(con: sqlite3.Connection) -> list[str]:
    vorhanden = {r[1] for r in con.execute("PRAGMA table_info(macro_snapshot)")}
    neu = []
    for name, typ in SPALTEN.items():
        if name not in vorhanden:
            con.execute(f"ALTER TABLE macro_snapshot ADD COLUMN {name} {typ}")
            neu.append(name)
    con.commit()
    return neu


def hole_netto_liquiditaet(fred_key: str) -> dict[str, float]:
    """WALCL - TGA - RRP, je WALCL-Datum (woechentlich).

    RRP ist taeglich und wird auf das jeweilige WALCL-Datum bezogen: der
    letzte bekannte Wert am oder vor diesem Tag. Anders herum - den naechsten
    Wert NACH dem Datum zu nehmen - waere ein Blick in die Zukunft."""
    from api.macro import get_fred_history

    def reihe(kuerzel: str) -> dict[str, float]:
        # FRED liefert fuer Feiertage und Luecken eine Beobachtung OHNE Wert
        # (in der API ein "."). Sie muss raus, bevor gerechnet wird - der
        # Trockenlauf ist genau darueber gestolpert, und ein `None` in einer
        # Subtraktion waere im Schreiblauf ein Abbruch mitten im Schreiben
        # gewesen.
        return {o.date: float(o.value)
                for o in get_fred_history(kuerzel, fred_key, START)
                if o.value is not None}

    walcl, tga, rrp = reihe("WALCL"), reihe("WTREGEN"), reihe("RRPONTSYD")
    rrp_tage = sorted(rrp)
    aus = {}
    for tag in sorted(walcl):
        if tag not in tga:
            continue
        passend = [t for t in rrp_tage if t <= tag]
        if not passend:
            continue
        # WALCL und TGA in Mio., RRP in Mrd. - vor der Subtraktion angleichen.
        aus[tag] = round(
            (walcl[tag] - tga[tag]) / 1000.0 - rrp[passend[-1]], 1)
    return aus


def hole_zinsen() -> dict[str, tuple[float, float]]:
    """^TNX (10 Jahre) und ^IRX (13 Wochen), je Tag mit beiden Werten."""
    import warnings

    import yfinance as yf
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        tnx = yf.Ticker("^TNX").history(start=START, interval="1d")
        irx = yf.Ticker("^IRX").history(start=START, interval="1d")
    a = {str(i)[:10]: float(v) for i, v in tnx["Close"].items()}
    b = {str(i)[:10]: float(v) for i, v in irx["Close"].items()}
    return {t: (a[t], b[t]) for t in sorted(set(a) & set(b))}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--schreiben", action="store_true")
    ap.add_argument("--db", default=DB)
    a = ap.parse_args()

    import sys
    sys.path.insert(0, ".")
    import config as config_module
    config_module.load_env()
    fred = os.environ.get("FRED_API_KEY")
    if not fred:
        print("[FEHLER] FRED_API_KEY fehlt - ohne ihn keine Netto-Liquiditaet.")
        return 1

    print("Abruf   FRED (WALCL, WTREGEN, RRPONTSYD) ...")
    liq = hole_netto_liquiditaet(fred)
    print(f"   {len(liq)} Wochenwerte  {min(liq)} .. {max(liq)}"
          if liq else "   nichts erhalten")
    print("Abruf   yfinance (^TNX, ^IRX) ...")
    zins = hole_zinsen()
    print(f"   {len(zins)} Tageswerte  {min(zins)} .. {max(zins)}"
          if zins else "   nichts erhalten")
    if not liq or not zins:
        return 1

    con = sqlite3.connect(a.db)
    bestand = {t: r for t, *r in con.execute(
        "SELECT date, netto_liquiditaet_mrd, rendite_10j_pct FROM macro_snapshot"
    )} if "netto_liquiditaet_mrd" in {
        r[1] for r in con.execute("PRAGMA table_info(macro_snapshot)")} else {}
    print(f"\nBestand: {sum(1 for v in bestand.values() if v[0] is not None)} "
          f"Tage mit Netto-Liquiditaet")

    tage = sorted(set(liq) | set(zins))
    print(f"Zu schreiben: {len(tage)} Tage  {tage[0]} .. {tage[-1]}")
    print(f"   davon mit Liquiditaet {len(liq)}, mit Zinsen {len(zins)}")
    if not a.schreiben:
        print("\nTROCKENLAUF - nichts geschrieben. Mit --schreiben ausfuehren.")
        return 0

    neu = _spalten_anlegen(con)
    if neu:
        print(f"\nSpalten angelegt: {neu}")
    jetzt = datetime.now(timezone.utc).isoformat()
    con.executemany(
        "INSERT INTO macro_snapshot (date, netto_liquiditaet_mrd, "
        "rendite_10j_pct, rendite_kurz_pct, fetched_at) VALUES (?, ?, ?, ?, ?) "
        # COALESCE: nie ueberschreiben, nur fuellen - wie beim Fear-&-Greed-
        # Nachladen. Live geschriebene Werte bleiben die Referenz.
        "ON CONFLICT(date) DO UPDATE SET "
        "netto_liquiditaet_mrd = COALESCE(macro_snapshot.netto_liquiditaet_mrd, excluded.netto_liquiditaet_mrd), "
        "rendite_10j_pct = COALESCE(macro_snapshot.rendite_10j_pct, excluded.rendite_10j_pct), "
        "rendite_kurz_pct = COALESCE(macro_snapshot.rendite_kurz_pct, excluded.rendite_kurz_pct)",
        [(t, liq.get(t), (zins.get(t) or (None, None))[0],
          (zins.get(t) or (None, None))[1], jetzt) for t in tage])
    con.commit()
    for sp in SPALTEN:
        n, v, b = con.execute(
            f"SELECT COUNT({sp}), MIN(date), MAX(date) FROM macro_snapshot "
            f"WHERE {sp} IS NOT NULL").fetchone()
        print(f"   {sp:<26}{n:>6} Werte  {v} .. {b}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
