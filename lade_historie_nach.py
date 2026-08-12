# -*- coding: utf-8 -*-
"""Faehlende Kurshistorie VOR dem vorhandenen Bestand nachladen (L6, 12.08.2026).

DER ANLASS. Beim Bau der Trendlage (Arbeitsstand 7.29) fiel auf, dass BTC in
unserer Datenbank nur bis zum 17.07.2024 zurueckreicht - 733 Kerzen. Damit
fehlen der Baerenmarkt 2022 und das Hoch 2021 vollstaendig. Was in frueheren
Messungen als "Baerenphase" simuliert wurde, war der Rueckgang seit Juli 2025:
ein Jahr, keine Marktphasen.

Der Grund ist die Quelle, nicht der Markt. Krakens OHLC-Endpunkt liefert rund
720 Kerzen und keine aelteren - er kennt kein Blaettern in die Vergangenheit.
Binance kennt es (`endTime`), und liefert je Abruf 1.000 Kerzen.

DIE NAHT, und warum sie vertretbar ist. Der Bestand kommt von Kraken, die
Ergaenzung von Binance. Das ist ein Bruch der Regel "genau EINE Quelle je
Symbol", die in `api/boersen_klines.py` steht - deshalb hier die Begruendung,
warum dieser Fall ein anderer ist:

    Die Regel richtet sich gegen VERSCHRAENKUNG - zwei Quellen, die denselben
    Zeitraum bedienen und einander zeilenweise ueberschreiben. Das ergibt eine
    Reihe, die es an keiner Boerse gab. Hier gibt es dagegen einen sauberen
    zeitlichen Schnitt: vor dem 17.07.2024 Binance, danach Kraken, kein Tag
    doppelt.

    Und die Naht ist gemessen, nicht geschaetzt. Ueber die 733 ueberlappenden
    Tage weichen beide Boersen im Median um 0,039 % voneinander ab, im 95.
    Perzentil um 0,143 %, maximal um 0,617 %. Das liegt unter dem, was zwei
    Abrufzeitpunkte an derselben Boerse auseinanderbringen.

    Trotzdem wird die Herkunft MARKIERT: die nachgeladenen Zeilen tragen
    `quelle='binance_historie'`. Eine Naht, die man in den Daten sieht, ist
    eine andere Sache als eine, die man spaeter suchen muss.

NUR USD. Binance fuehrt BTCEUR erst seit dem 17.11.2023 - dort waere nichts zu
holen. `lade_reihen_aus_db()` waehlt fuer BTC ohnehin USD (eine Waehrung je
Symbol, USD bevorzugt), die Rollen-Ebene bekommt also die volle Reihe.

BESTEHENDE ZEILEN WERDEN NIE ANGEFASST. `upsert_ohlc_points()` ueberschreibt
bei Konflikt - deshalb filtert dieses Skript selbst auf Tage VOR dem aeltesten
vorhandenen Datum. Ein Lauf kann den Bestand nicht verschlechtern.

    python lade_historie_nach.py BTC              # Trockenlauf, zeigt nur
    python lade_historie_nach.py BTC --schreiben  # schreibt
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from datetime import date, datetime, timezone

import requests

DB = "data/tradinginfotool.db"
URL = "https://api.binance.com/api/v3/klines"
MAX_KERZEN = 1000
MAX_RUNDEN = 20          # 20.000 Kerzen - mehr Historie hat keine Boerse


def _tag(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()


def hole_alles(paar: str, session: requests.Session) -> dict[str, list]:
    """Rueckwaerts blaettern, bis die Boerse nichts Aelteres mehr hat."""
    alle: dict[str, list] = {}
    ende = None
    for _ in range(MAX_RUNDEN):
        p = {"symbol": paar, "interval": "1d", "limit": MAX_KERZEN}
        if ende:
            p["endTime"] = ende
        r = session.get(URL, params=p, timeout=20)
        r.raise_for_status()
        z = r.json() or []
        if not z:
            break
        for k in z:
            alle[_tag(int(k[0]))] = k
        ende = int(z[0][0]) - 1
        if len(z) < MAX_KERZEN:
            break
        time.sleep(0.25)
    return alle


def pruefe_taeglich(tage: list[str]) -> tuple[int, int]:
    """Median- und Groesstabstand. Eine Reihe mit Loechern taugt nicht als
    Historie - jeder Fensterindikator zaehlt Zeilen, nicht Kalendertage."""
    d = [date.fromisoformat(t) for t in tage]
    ab = sorted((d[i + 1] - d[i]).days for i in range(len(d) - 1))
    return ab[len(ab) // 2], ab[-1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--waehrung", default="USD")
    ap.add_argument("--paar", default=None, help="Boersensymbol, sonst <SYM>USDT")
    ap.add_argument("--schreiben", action="store_true")
    ap.add_argument("--db", default=DB)
    a = ap.parse_args()
    paar = a.paar or f"{a.symbol}USDT"

    con = sqlite3.connect(a.db)
    n, aeltester, neuester = con.execute(
        "SELECT COUNT(*), MIN(date), MAX(date) FROM price_history_ohlc "
        "WHERE symbol=? AND currency=?", (a.symbol, a.waehrung)).fetchone()
    if not n:
        print(f"{a.symbol}/{a.waehrung} steht nicht in der Datenbank.")
        return 1
    print(f"Bestand  {a.symbol}/{a.waehrung}: {n} Zeilen  {aeltester} .. {neuester}")

    print(f"Abruf    {paar} bei Binance ...")
    alle = hole_alles(paar, requests.Session())
    if not alle:
        print("   nichts erhalten.")
        return 1
    tage = sorted(alle)
    median, groesste = pruefe_taeglich(tage)
    print(f"   {len(tage)} Kerzen  {tage[0]} .. {tage[-1]}  "
          f"Median-Abstand {median}, groesste Luecke {groesste}")
    if median != 1:
        print("   ABBRUCH: keine Tageskerzen.")
        return 1

    # Die Naht messen, bevor irgendetwas geschrieben wird
    bestand = dict(con.execute(
        "SELECT date, close FROM price_history_ohlc WHERE symbol=? AND currency=?",
        (a.symbol, a.waehrung)))
    gem = [(abs(float(alle[t][4]) - bestand[t]) / bestand[t] * 100.0)
           for t in tage if t in bestand and bestand[t]]
    if gem:
        gem.sort()
        print(f"   Naht ueber {len(gem)} ueberlappende Tage: Median "
              f"{gem[len(gem)//2]:.3f} %  p95 {gem[int(.95*len(gem))]:.3f} %  "
              f"max {gem[-1]:.3f} %")
    else:
        print("   KEINE Ueberlappung - die Naht ist ungeprueft. "
              "Das ist ein Grund innezuhalten, kein Grund weiterzumachen.")
        if a.schreiben:
            return 1

    # NUR was vor dem Bestand liegt. Bestehende Zeilen bleiben unberuehrt.
    neu = [t for t in tage if t < aeltester]
    print(f"\nNachzuladen: {len(neu)} Tage vor {aeltester}"
          + (f"  ({neu[0]} .. {neu[-1]})" if neu else ""))
    if not neu:
        print("   nichts zu tun.")
        return 0
    if not a.schreiben:
        print("\nTROCKENLAUF - nichts geschrieben. Mit --schreiben ausfuehren.")
        return 0

    sys.path.insert(0, ".")
    import database.db as db
    from database.models import OhlcPoint
    # `database.db` liest Spalten ueber den Namen (`r["name"]`) und setzt
    # deshalb eine Row-Factory voraus. Ohne sie scheitert schon die
    # Schema-Migration - vor jedem Schreibzugriff, weshalb der Fehlversuch
    # den Bestand nicht angefasst hat.
    con.row_factory = sqlite3.Row
    jetzt = datetime.now(timezone.utc).isoformat()
    punkte = [OhlcPoint(symbol=a.symbol, currency=a.waehrung, date=t,
                        open=float(alle[t][1]), high=float(alle[t][2]),
                        low=float(alle[t][3]), close=float(alle[t][4]),
                        volume=float(alle[t][5]), fetched_at=jetzt)
              for t in neu]
    db.upsert_ohlc_points(con, punkte, quelle="binance_historie")
    con.commit()
    n2, a2, b2 = con.execute(
        "SELECT COUNT(*), MIN(date), MAX(date) FROM price_history_ohlc "
        "WHERE symbol=? AND currency=?", (a.symbol, a.waehrung)).fetchone()
    print(f"\nGeschrieben. Bestand jetzt: {n2} Zeilen  {a2} .. {b2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
