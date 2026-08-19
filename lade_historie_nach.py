"""Mehr Kryptohistorie - rueckwaerts geblaettert (Umbauplan 93 B, Punkt 2)

DAS PROBLEM. 25 unserer Kryptoreihen enden an DERSELBEN Wand: 733 Kerzen ab
dem 17.07.2024. Das ist kein Zufall und kein Fehler, sondern Krakens
OHLC-Endpunkt - er gibt hoechstens 720 Punkte heraus. Fuer die Driftmessung
(93 B) heisst das: zwei Jahre, EIN Regime, und an einem Termin oft nur 20
vergleichbare Symbole. Bei 20 Symbolen besteht ein Fuenftel aus vier Werten.

DIE LOESUNG IST KEINE NEUE QUELLE, SONDERN EIN ZWEITER GRIFF IN DIE ALTE.
`api/boersen_klines.py` holt bei Binance/Bybit die letzten 1.000 Kerzen -
ohne `startTime`. Binance kennt den Parameter aber, man kann also
zurueckblaettern. Live geprueft am 20.08.2026:

    BTC     ab 2017-08-17 (paginiert)      SUI  ab 2023-05-03 statt 2024-07-17
    XNO     ab 2022-01-28, DB hatte NULL   IO   ab 2024-06-11, DB hatte NULL

⚠️ UND EIN GEGENBEISPIEL, DAS DIE GANZE VORSICHT BEGRUENDET: fuer MORPHO
liefert Binance erst ab 2025-10-03, waehrend die Datenbank bis 2024-11-21
zurueckreicht. Wer hier "aktualisiert", verschlechtert. Deshalb wird NIE
ueberschrieben, sondern ausschliesslich Fehlendes ergaenzt.

⚠️ DIE FALLE, DIE DIESES PROJEKT SCHON EINMAL ERWISCHT HAT. Der abgeloeste
yfinance-Rueckfall riet Ticker nach dem Muster `<SYM>-USD`; drei von acht
gehoerten einem anderen, toten Asset - bei IO waren es 269 % Abweichung. Hier
wird deshalb JEDE Reihe gegengeprueft, bevor eine Zeile geschrieben wird:

    Reihe schon da    Ueberlappung mit den vorhandenen Kerzen: mindestens 30
                      gemeinsame Tage, Median der Abweichung hoechstens 2 %.
                      Sonst ist es ein anderes Asset oder eine andere
                      Preisbasis - und beides gehoert nicht in dieselbe Reihe.
    Reihe leer        keine Ueberlappung moeglich, also gegen den aktuellen
                      Preis von CoinGecko: hoechstens 5 % Abstand. Ohne
                      Vergleichspreis wird NICHT geschrieben.

⚠️ DER VERGLEICHSPREIS MUSS FRISCHER SEIN ALS DAS GEPRUEFTE. Die erste
Fassung nahm ihn aus der eigenen Datenbank und lehnte vier Symbole ab - KAIA
mit "30 % Abweichung, das ist ein anderes Asset". Der Preis stammte vom
19.07., ueber einen Monat alt, weil die Produktion auf dem Notebook laeuft.
Mit einem frisch geholten Preis betraegt die Abweichung 0,4 %. Die Ablehnung
mass das Alter der eigenen Datenbank, nicht das Asset.

⚠️ EINE NAHT BLEIBT EINE NAHT. Aeltere Kerzen kommen von Binance, juengere
von Kraken. Die Ueberlappungspruefung sagt, dass die beiden am selben Tag
dasselbe meinen - sie macht sie nicht identisch. `quelle` haelt fest, woher
jede Zeile stammt.

    python lade_historie_nach.py                 # nur berichten
    python lade_historie_nach.py --schreiben     # nach Sicherung eintragen
"""
from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, ".")

BINANCE = "https://api.binance.com/api/v3/klines"
BYBIT = "https://api.bybit.com/v5/market/kline"
MAX_KERZEN = 1000
# Binance beginnt 2017; frueher gibt es dort nichts, und ein frueherer
# Startpunkt kostet nur einen leeren Abruf.
START_MS = 1483228800000  # 2017-01-01
ABSTAND_S = 0.25

# Die Gegenprobe. Zwei Prozent sind mehr als der Unterschied zweier Boersen
# am selben Tag und weniger als jede Verwechslung, die dieses Projekt je
# gesehen hat (IO: 269 %).
MAX_ABWEICHUNG_REIHE = 0.02
MAX_ABWEICHUNG_PREIS = 0.05
MIN_UEBERLAPPUNG = 30


def _tag(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).date().isoformat()


def hole_binance_alles(symbol: str, sitzung) -> list[tuple]:
    """Alle Tageskerzen, vorwaerts geblaettert. (datum, o, h, l, c, v)."""
    aus, start = [], START_MS
    while True:
        r = sitzung.get(BINANCE, params={
            "symbol": f"{symbol}USDT", "interval": "1d",
            "limit": MAX_KERZEN, "startTime": start}, timeout=25)
        if r.status_code == 400:
            # Das Paar gibt es dort nicht - eine Auskunft, kein Ausfall.
            return []
        r.raise_for_status()
        d = r.json() or []
        if not d:
            break
        aus += [(_tag(int(z[0])), float(z[1]), float(z[2]), float(z[3]),
                 float(z[4]), float(z[5])) for z in d]
        if len(d) < MAX_KERZEN:
            break
        start = int(d[-1][0]) + 86_400_000
        time.sleep(ABSTAND_S)
    return aus


def hole_bybit_alles(symbol: str, sitzung) -> list[tuple]:
    """Bybit als Rueckfall. Liefert absteigend und paginiert ueber `end`."""
    aus, ende = [], None
    while True:
        p = {"category": "spot", "symbol": f"{symbol}USDT", "interval": "D",
             "limit": MAX_KERZEN}
        if ende is not None:
            p["end"] = ende
        r = sitzung.get(BYBIT, params=p, timeout=25)
        r.raise_for_status()
        liste = ((r.json().get("result") or {}).get("list")) or []
        if not liste:
            break
        aus += [(_tag(int(z[0])), float(z[1]), float(z[2]), float(z[3]),
                 float(z[4]), float(z[5])) for z in liste]
        if len(liste) < MAX_KERZEN:
            break
        ende = int(liste[-1][0]) - 1
        time.sleep(ABSTAND_S)
    return sorted(set(aus))


def _vorhanden(conn, symbol: str) -> dict:
    return {r[0]: float(r[1]) for r in conn.execute(
        "SELECT date, close FROM price_history_ohlc WHERE symbol = ? "
        "AND currency = 'USD'", (symbol,))}


def preise_frisch(ids: list[str], sitzung) -> dict:
    """Aktuelle Preise von CoinGecko - EIN Abruf fuer alle.

    ⚠️ WARUM NICHT AUS `price_cache` (Fund vom 20.08.2026). Genau das war die
    erste Fassung, und sie hat vier Symbole zu Unrecht abgelehnt: KAIA mit
    "30 % Abweichung - das ist ein anderes Asset". Der Vergleichspreis auf
    dem Entwicklungsrechner stammte vom 19.07. - ueber einen Monat alt, weil
    die Produktion auf dem Notebook laeuft. Dreissig Prozent in einem Monat
    sind bei einem Kleinwert normal.

    Die Ablehnung mass nicht das Asset, sondern das Alter der eigenen
    Datenbank. Dazu kam ein zweiter Fehler: die Abfrage hatte kein ORDER BY
    und nahm damit eine BELIEBIGE der 31 gespeicherten Zeilen.

    Ein Vergleichsmassstab muss frischer sein als das, was er pruefen soll."""
    if not ids:
        return {}
    try:
        r = sitzung.get("https://api.coingecko.com/api/v3/simple/price",
                        params={"ids": ",".join(sorted(set(ids))),
                                "vs_currencies": "usd"}, timeout=30)
        if r.status_code != 200:
            return {}
        return {k: float(v.get("usd")) for k, v in (r.json() or {}).items()
                if v.get("usd")}
    except Exception:                                        # noqa: BLE001
        return {}


def pruefe(neu: list[tuple], alt: dict, preis) -> tuple[bool, str]:
    """Darf diese Reihe zu unserer dazu? DEFAULT IST NEIN."""
    if not neu:
        return False, "keine Kerzen von der Boerse"
    gemeinsam = [(alt[d], c) for d, _o, _h, _l, c, _v in neu if d in alt]
    if alt:
        if len(gemeinsam) < MIN_UEBERLAPPUNG:
            return False, (f"nur {len(gemeinsam)} gemeinsame Tage - zu wenig "
                           f"fuer eine Gegenprobe")
        ab = sorted(abs(a - b) / a for a, b in gemeinsam if a > 0)
        med = ab[len(ab) // 2] if ab else 1.0
        if med > MAX_ABWEICHUNG_REIHE:
            return False, (f"Median der Abweichung {100 * med:.1f} % auf "
                           f"{len(gemeinsam)} gemeinsamen Tagen - anderes "
                           f"Asset oder andere Preisbasis")
        return True, f"Ueberlappung {len(gemeinsam)} Tage, {100 * med:.2f} %"
    # Leere Reihe: die einzige Gegenprobe ist der aktuelle Preis.
    if not preis or preis <= 0:
        return False, "Reihe leer UND kein Vergleichspreis - nicht pruefbar"
    letzte = neu[-1][4]
    ab = abs(letzte - preis) / preis
    if ab > MAX_ABWEICHUNG_PREIS:
        return False, (f"letzte Kerze {letzte:.6g} gegen Preis {preis:.6g} = "
                       f"{100 * ab:.0f} % - das ist ein anderes Asset")
    return True, f"Preisprobe {100 * ab:.1f} %"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--db", default="data/tradinginfotool.db")
    p.add_argument("--schreiben", action="store_true",
                   help="ohne dieses Wort wird NUR berichtet")
    p.add_argument("--nur", default="", help="Symbole, kommagetrennt")
    p.add_argument("--datei", default="messwerte_historie.json")
    a = p.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    import requests

    import config as C

    wl = [x for x in C.get_watchlist()
          if str(getattr(x, "assetklasse", "") or "").lower() == "krypto"
          and not getattr(x, "ist_cash_aequivalent", False)]
    if a.nur:
        wunsch = {s.strip().upper() for s in a.nur.split(",")}
        wl = [x for x in wl if x.symbol.upper() in wunsch]

    print("=" * 78)
    print("MEHR KRYPTOHISTORIE - rueckwaerts geblaettert (93 B, Punkt 2)")
    print("=" * 78)
    print(f"  {len(wl)} Kryptowerte   Datenbank: {a.db}")
    if a.schreiben:
        sicherung = f"{a.db}.vor_historie_{datetime.now(timezone.utc):%Y%m%d}"
        if not os.path.exists(sicherung):
            with sqlite3.connect(a.db) as q, sqlite3.connect(sicherung) as z:
                q.backup(z)
            print(f"  Sicherung angelegt: {os.path.basename(sicherung)}")
        print("  SCHREIBMODUS - es wird NIE ueberschrieben, nur ergaenzt")
    else:
        print("  Nur Bericht. Zum Eintragen: --schreiben")
    print("")

    conn = sqlite3.connect(a.db)
    sitzung = requests.Session()
    # Nur fuer Symbole OHNE eigene Reihe - dort ist der Preis die einzige
    # moegliche Gegenprobe. Wo Kerzen liegen, prueft die Ueberlappung.
    _leer = [x for x in wl if not _vorhanden(conn, x.symbol.upper())]
    frisch = preise_frisch([getattr(x, "coingecko_id", None) for x in _leer
                            if getattr(x, "coingecko_id", None)], sitzung)
    if _leer:
        print(f"  Vergleichspreise fuer {len(_leer)} Reihen ohne Historie: "
              f"{len(frisch)} von CoinGecko geholt (frisch, nicht aus der "
              f"eigenen Datenbank)\n")
    jetzt = datetime.now(timezone.utc).isoformat()
    bericht, gewachsen, abgelehnt = [], 0, 0
    for i, asset in enumerate(wl, 1):
        sym = asset.symbol.upper()
        alt = _vorhanden(conn, sym)
        neu, quelle = [], "binance"
        try:
            neu = hole_binance_alles(sym, sitzung)
            if not neu:
                quelle = "bybit"
                neu = hole_bybit_alles(sym, sitzung)
        except Exception as exc:                             # noqa: BLE001
            print(f"  {i:3d}/{len(wl)} {sym:9} FEHLER {type(exc).__name__} - "
                  f"nicht erfahren, kein Nein")
            bericht.append({"symbol": sym, "zustand": "fehler"})
            continue
        ok, grund = pruefe(neu, alt,
                           frisch.get(getattr(asset, "coingecko_id", None)))
        fehlend = [z for z in neu if z[0] not in alt]
        if not ok:
            print(f"  {i:3d}/{len(wl)} {sym:9} ABGELEHNT - {grund}")
            bericht.append({"symbol": sym, "zustand": "abgelehnt",
                            "grund": grund})
            abgelehnt += 1
            continue
        aeltester_alt = min(alt) if alt else None
        aeltester_neu = min(z[0] for z in neu)
        print(f"  {i:3d}/{len(wl)} {sym:9} {len(alt):5} -> "
              f"{len(alt) + len(fehlend):5} Kerzen  (+{len(fehlend):4})  "
              f"ab {aeltester_alt or '-'} -> {min(aeltester_neu, aeltester_alt or aeltester_neu)}"
              f"   [{quelle}, {grund}]")
        bericht.append({"symbol": sym, "zustand": "ok", "quelle": quelle,
                        "vorher": len(alt), "dazu": len(fehlend),
                        "ab_neu": aeltester_neu, "grund": grund})
        gewachsen += len(fehlend)
        if a.schreiben and fehlend:
            # ⚠️ INSERT OR IGNORE - eine vorhandene Kerze bleibt, wie sie
            # ist. MORPHO ist der Beleg, warum: dort waere "aktualisieren"
            # eine Verschlechterung gewesen.
            conn.executemany(
                "INSERT OR IGNORE INTO price_history_ohlc (symbol, currency, "
                "date, open, high, low, close, volume, fetched_at, quelle) "
                "VALUES (?, 'USD', ?, ?, ?, ?, ?, ?, ?, ?)",
                [(sym, d, o, h, l, c, v, jetzt, quelle)
                 for d, o, h, l, c, v in fehlend])
            conn.commit()

    print("\n" + "=" * 78)
    print(f"  {gewachsen} Kerzen "
          + ("eingetragen" if a.schreiben else "waeren einzutragen")
          + f", {abgelehnt} Symbole abgelehnt")
    if not a.schreiben:
        print("  Nichts geschrieben. Mit --schreiben eintragen.")
    print("=" * 78)
    if a.datei:
        io.open(a.datei, "w", encoding="utf-8").write(
            json.dumps(bericht, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
