"""OHLC-Rueckfallquelle fuer Krypto-Assets ohne Kraken-Listing (2026-08-03).

DIE LUECKE, die das schliesst. price_history_ohlc wird ausschliesslich aus
Kraken befuellt (api/kraken_history.py), und zwar nur fuer Symbole aus der fest
gepflegten KRAKEN_PAIR_MAP (35 Eintraege). Steht ein Asset nicht darin, bekommt
es NULL Kursdaten - ohne Fehler, nur mit "kein Kraken-Listing" uebersprungen.
Das war als bekannte Deckungsluecke dokumentiert und als solche vertretbar,
solange die Naeherung aus indicators/calculations.py fuer die Anzeige reichte.

Fuer die MESSUNG reicht sie nicht. Am 03.08. an echten Daten aufgefallen:
elf Symbole ohne jede Kursreihe, darunter die haeufigsten Hebel-Kandidaten
ueberhaupt.

    Symbol    Hebel-Kandidaten   Hebel-Signale   Spot-Signale   Holding
    KAIA                 1070             126             67   ja
    KAITO                 344             121             35   nein
    CANTON                209               1             67   ja
    SUPRA                 117              28             67   ja
    IO                      4               0             29   ja
    XNO                     4               4             33   ja
    BRETT                   1               0             61   ja

KAIA allein stellt 17,2 % aller Screening-Kandidaten. Jede Auswertung des
Vorfilters lief damit auf einem knappen Viertel blind, und fuenf gehaltene
Positionen (~765 EUR) hatten weder Signale noch Tracking (#614).

WARUM COINGECKO. Der Client kann das seit dem 30.07. bereits - get_coin_ohlc()
ueber `/coins/{id}/ohlc`, gebaut fuer das Marktscan-Backward-Tracking mit der
ausdruecklichen Begruendung "deckt praktisch jeden CoinGecko-Coin ab, weil
Marktscan-Coins meist nicht Kraken-gelistet sind". Genau dieselbe Lage, nur
eine andere Stelle. Die Faehigkeit war da, sie war nur nicht angeschlossen.

NUR ALS RUECKFALL, nie parallel: Wo Kraken liefert, bleibt Kraken die Quelle.
Zwei Quellen fuer dasselbe Symbol wuerden sich in derselben Tabelle
ueberschreiben, und die Kerzen unterscheiden sich (Boersenkurs gegen
volumengewichteten Mehrboersen-Schnitt). price_history_ohlc fuehrt KEINE
Herkunftsspalte - sie ist auch nicht noetig, weil die Quelle deterministisch
ableitbar ist: `KRAKEN_PAIR_MAP.get(symbol) is None` heisst CoinGecko, sonst
Kraken. Wer das je Punkt braucht (etwa nach einem Wechsel der Paarliste),
muesste eine Spalte ergaenzen - heute waere sie redundant.

NUR KRYPTO. Wertpapiere (3QSS, DBPK, VSN) laufen ueber yfinance
(api/yfinance_history.py), Stablecoins (EURCV) brauchen keine Kerzen. Die
Unterscheidung laeuft ueber `assetklasse`, nicht ueber das Fehlen eines
Kraken-Paares - sonst wuerde diese Funktion Aktien bei CoinGecko suchen.

KOSTEN. Ein Abruf je Symbol und Lauf, taeglich, fuer rund sieben Symbole.
Gegen das CoinGecko-Kontingent (siehe api/coingecko.py) faellt das nicht ins
Gewicht; die Drossel des Clients gilt unveraendert.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import database.db as db
from api.kraken import KRAKEN_PAIR_MAP
from database.models import OhlcPoint

logger = logging.getLogger(__name__)

# CoinGecko liefert bei `days` <= 90 Tageskerzen; darueber werden es Vier-Tage-
# Kerzen. 90 ist damit der groesste Wert, der noch die benoetigte Aufloesung
# hat. Fuer den taeglichen Lauf waere weniger genug, aber der erste Lauf fuellt
# so gleich eine brauchbare Historie.
ABRUF_TAGE = 90
# Assetklassen, fuer die CoinGecko ueberhaupt die richtige Quelle ist.
KRYPTO_KLASSEN = ("krypto",)


@dataclass
class FallbackResult:
    symbol: str
    points_upserted: int
    skipped: bool = False
    reason: str | None = None


def braucht_fallback(asset) -> bool:
    """Krypto-Asset, kein Kraken-Paar, aber eine CoinGecko-ID vorhanden?

    Alle drei Bedingungen sind noetig: ohne Kraken-Paar waere sonst nichts zu
    tun, ohne Krypto-Klasse waere CoinGecko die falsche Quelle, und ohne ID
    laesst sich der Coin dort nicht adressieren."""
    if getattr(asset, "assetklasse", None) not in KRYPTO_KLASSEN:
        return False
    if KRAKEN_PAIR_MAP.get(asset.symbol) is not None:
        return False
    return bool(getattr(asset, "coingecko_id", None))


def _rohdaten_zu_tageskerzen(raw: list) -> list[dict]:
    """CoinGecko liefert [ts_ms, open, high, low, close] ohne Volumen.

    Mehrere Eintraege koennen auf denselben Kalendertag fallen; dann gilt der
    letzte (die Liste kommt chronologisch). Unvollstaendige Zeilen fliegen raus
    statt mit Nullen gefuellt zu werden - eine erfundene Null waere in der
    High/Low-Logik des Backward-Trackings ein stiller Treffer."""
    je_tag: dict[str, dict] = {}
    for zeile in raw or []:
        if not zeile or len(zeile) < 5:
            continue
        ts, o, h, l, c = zeile[0], zeile[1], zeile[2], zeile[3], zeile[4]
        if None in (ts, o, h, l, c):
            continue
        try:
            tag = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).date().isoformat()
        except (TypeError, ValueError, OSError):
            continue
        je_tag[tag] = {"date": tag, "open": float(o), "high": float(h),
                       "low": float(l), "close": float(c)}
    return [je_tag[t] for t in sorted(je_tag)]


def fuelle_ohlc_aus_coingecko(client, conn, asset,
                              currencies: tuple[str, ...] = ("USD",)) -> FallbackResult:
    """Holt Tageskerzen fuer EIN Asset und schreibt sie in price_history_ohlc.

    Bewusst nur USD als Default: die Auswertungen rechnen durchgehend in USD
    (lade_kursreihen() filtert darauf), und jede weitere Waehrung waere ein
    zusaetzlicher Abruf gegen dasselbe Kontingent."""
    if not braucht_fallback(asset):
        return FallbackResult(asset.symbol, 0, skipped=True,
                              reason="kein Fallback noetig (Kraken-Listing, "
                                     "keine Krypto-Klasse oder keine CoinGecko-ID)")
    fetched_at = datetime.now(timezone.utc).isoformat()
    gesamt = 0
    fehler: list[str] = []
    for currency in currencies:
        try:
            raw = client.get_coin_ohlc(asset.coingecko_id, vs_currency=currency.lower(),
                                       days=ABRUF_TAGE)
        except Exception as exc:
            fehler.append(f"{currency}: {exc}")
            logger.info("CoinGecko-OHLC-Fallback (%s) fuer %s fehlgeschlagen: %s",
                        currency, asset.symbol, exc)
            continue
        kerzen = _rohdaten_zu_tageskerzen(raw)
        if not kerzen:
            fehler.append(f"{currency}: keine verwertbaren Kerzen")
            continue
        db.upsert_ohlc_points(conn, [
            OhlcPoint(
                symbol=asset.symbol, currency=currency, date=k["date"],
                open=k["open"], high=k["high"], low=k["low"], close=k["close"],
                # CoinGecko liefert im OHLC-Endpunkt KEIN Volumen. 0.0 statt
                # None, weil die Spalte NOT NULL ist - der Wert wird von keiner
                # Auswertung gelesen, die Herkunft steht in datenquelle.
                volume=0.0, fetched_at=fetched_at,
            )
            for k in kerzen
        ])
        gesamt += len(kerzen)
    if gesamt == 0:
        return FallbackResult(asset.symbol, 0,
                              reason="; ".join(fehler) or "keine Kerzen erhalten")
    return FallbackResult(asset.symbol, gesamt,
                          reason="; ".join(fehler) if fehler else None)


def fuelle_alle_ohlc_luecken(client, conn, watchlist) -> list[FallbackResult]:
    """Alle Watchlist-Assets, die den Fallback brauchen. Reine Ergaenzung -
    Assets mit Kraken-Listing werden nicht angefasst."""
    ergebnisse = []
    for asset in watchlist or []:
        if not braucht_fallback(asset):
            continue
        ergebnis = fuelle_ohlc_aus_coingecko(client, conn, asset)
        ergebnisse.append(ergebnis)
        if ergebnis.reason and ergebnis.points_upserted == 0:
            logger.info("CoinGecko-OHLC-Fallback fuer %s ohne Ergebnis: %s",
                        ergebnis.symbol, ergebnis.reason)
    return ergebnisse
