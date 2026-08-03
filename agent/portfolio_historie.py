"""Portfolio-Wert je Tag - Rekonstruktion und laufende Fortschreibung.
(2026-08-04, Task #612)

Grundlage fuer Z-3/RM-7 (Drawdown-Notbremse), die im Regelwerksmanual seit
jeher als "OFFEN - fehlt noch eine Portfolio-Wert-Historie" steht, und fuer die
Drawdown-Anzeige in U-1.

WARUM ES DIESES MODUL BRAUCHT
`holdings` ist eine Zustandstabelle (symbol als PRIMARY KEY) - jeder
Bitpanda-Sync ueberschreibt sie, der Verlauf ging bisher jedes Mal verloren.
Es gibt auch keine Transaktionstabelle in der DB. Die Kurse dagegen liegen
vollstaendig vor. Rekonstruierbar ist der Portfoliowert also ueber
Bestand x Kurs - die Frage ist nur, welchen Bestand man fuer die Vergangenheit
ansetzt.

ZWEI STUFEN, BEWUSST GETRENNT
Stufe 1 (dieses Modul, jetzt): Stichtags-Bestaende. Der heutige Bestand wird
rueckwaerts fortgeschrieben. Das ist exakt, solange sich nichts geaendert hat,
und wird mit jedem zurueckliegenden Handel ungenauer. Deshalb gibt
`rekonstruiere_stichtag()` ein `gueltig_ab`-Datum mit zurueck, das der Aufrufer
setzen muss - eine stillschweigende Ausdehnung auf beliebig lange Zeitraeume
waere genau der stille Falschwert, den P-10 verbietet.

Stufe 2 (spaeter): echte Bestandsverlaeufe aus
`api/bitpanda.py::get_wallet_transactions()`. Teurer (~9500 Transaktionen) und
mit einem bekannten Fallstrick - siehe `importer/bitpanda_avg_cost.py`:
holdings.quantity enthaelt Einheiten, die NIE ueber einen bepreisten Trade
liefen (Staking-Gutschriften, externe Einzahlungen). Wer Stufe 2 baut, muss
ALLE Bewegungsarten einbeziehen, nicht nur buy/sell.

WAS `wert_eur` BEDEUTET - UND WARUM CASH NICHT DRIN IST
`wert_eur` ist der Wert der GEHALTENEN ASSETS, ohne Cash. Das ist eine bewusste
Entscheidung, keine Vereinfachung:

Der Cash-Bestand der Vergangenheit ist nicht rekonstruierbar - er steht nur als
aktueller Wert in der DB. Wuerde man den heutigen Cash-Betrag konstant ueber
alle Tage mitfuehren, waere er ein gleichbleibender Summand. Ein konstanter
Summand DAEMPFT jeden prozentualen Rueckschlag: bei 10.000 EUR Assets und
5.000 EUR Cash wird aus einem 15%-Assetverlust ein 10%-Gesamtverlust. Z-3
wuerde also spaeter ausloesen, als es soll - und zwar umso spaeter, je mehr
Cash heute zufaellig herumliegt. Ein Messfehler, der sich nach dem
Kontostand des Erstellungstags richtet.

`cash_eur` wird deshalb getrennt gefuehrt: bei laufenden Werten mit dem echten
Betrag, bei rekonstruierten mit 0. Z-3 rechnet auf `wert_eur`, und das ist ueber
beide Quellen hinweg dasselbe Mass.
"""
from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone

import config
import database.db as db

logger = logging.getLogger(__name__)

QUELLE_REKONSTRUIERT = "rekonstruiert"
QUELLE_LAUFEND = "laufend"

# Ein Tages-FX-Kurs gilt nur, wenn ihn genug Symbole unabhaengig bestaetigen.
# Bei EINEM Symbol waere ein einzelner kaputter Kurs (falsches Waehrungslabel,
# Skalierungsfehler - beides ist in diesem Projekt schon vorgekommen, siehe
# Rohstoff-OHLC-Skalierungsbug 27.07.) nicht von einem echten Wechselkurs zu
# unterscheiden. Ab drei Symbolen faengt der Median einen Ausreisser ab.
MIN_SYMBOLE_FUER_FX = 3

# Wie weit duerfen die aus verschiedenen Symbolen abgeleiteten FX-Kurse eines
# Tages auseinanderliegen, bevor der Tag als unbrauchbar gilt? EUR/USD bewegt
# sich intraday im Promillebereich; 2% Spannweite bedeutet, dass mindestens
# eine der beiden Kursreihen nicht stimmt.
MAX_FX_SPANNWEITE_RELATIV = 0.02


@dataclass
class SymbolDiagnose:
    """Wie gut ist EIN Symbol ueber den Zeitraum abgedeckt?

    Nutzer-Vorgabe 04.08.: mit Unschaerfen ist zu rechnen - nicht ueberall
    Exaktheit erzwingen, sondern die Problemfaelle selektiv identifizieren und
    glaetten. Dafuer muss zuerst je Symbol sichtbar sein, WO es klemmt."""

    symbol: str
    menge: float
    tage_direkt_eur: int = 0
    tage_ueber_fx: int = 0
    tage_ohne_kurs: int = 0
    letzter_kurs_eur: float | None = None

    @property
    def tage_gesamt(self) -> int:
        return self.tage_direkt_eur + self.tage_ueber_fx + self.tage_ohne_kurs

    @property
    def ist_problemfall(self) -> bool:
        """Problemfall = mehr als ein Zehntel der Tage ohne Kurs. Solche
        Symbole gehoeren einzeln angesehen, nicht stillschweigend als 0
        mitgerechnet."""
        if self.tage_gesamt == 0:
            return True
        return self.tage_ohne_kurs / self.tage_gesamt > 0.10


@dataclass
class RekonstruktionsErgebnis:
    tageswerte: list[tuple[str, float, int, int]] = field(default_factory=list)
    symbol_diagnosen: list[SymbolDiagnose] = field(default_factory=list)
    fx_tage_verworfen: list[str] = field(default_factory=list)

    @property
    def problemfaelle(self) -> list[SymbolDiagnose]:
        return [d for d in self.symbol_diagnosen if d.ist_problemfall]


def _heute_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def tages_fx_kurse(conn: sqlite3.Connection) -> tuple[dict[str, float], list[str]]:
    """EUR-pro-USD je Tag, abgeleitet aus Symbolen mit BEIDEN Waehrungen.

    Wir haben keine historische Wechselkursreihe - aber 35 Symbole fuehren
    dieselbe Kursreihe in EUR und in USD. Deren Quotient IST der Wechselkurs.
    Das braucht keine neue Datenquelle und keinen API-Aufruf.

    Rueckgabe: (kurse_je_datum, verworfene_tage). Verworfen wird ein Tag, wenn
    zu wenige Symbole ihn stuetzen oder die Symbole einander widersprechen -
    lieber eine Luecke, die als Luecke sichtbar ist, als ein plausibel
    aussehender Falschkurs."""
    rows = conn.execute(
        "SELECT e.date AS datum, e.close AS eur, u.close AS usd "
        "FROM price_history_ohlc e "
        "JOIN price_history_ohlc u ON u.symbol = e.symbol AND u.date = e.date "
        "WHERE e.currency = 'EUR' AND u.currency = 'USD' "
        "AND e.close > 0 AND u.close > 0"
    ).fetchall()

    je_tag: dict[str, list[float]] = {}
    for row in rows:
        je_tag.setdefault(row["datum"], []).append(row["eur"] / row["usd"])

    kurse: dict[str, float] = {}
    verworfen: list[str] = []
    for datum, werte in je_tag.items():
        if len(werte) < MIN_SYMBOLE_FUER_FX:
            verworfen.append(datum)
            continue
        werte.sort()
        spannweite = (werte[-1] - werte[0]) / werte[len(werte) // 2]
        if spannweite > MAX_FX_SPANNWEITE_RELATIV:
            logger.warning(
                "FX-Ableitung %s verworfen: %d Symbole, Spannweite %.1f%% "
                "(Grenze %.0f%%) - mindestens eine Kursreihe ist fehlerhaft",
                datum, len(werte), spannweite * 100, MAX_FX_SPANNWEITE_RELATIV * 100,
            )
            verworfen.append(datum)
            continue
        kurse[datum] = werte[len(werte) // 2]

    return kurse, sorted(verworfen)


def _eur_kurse_je_symbol(
    conn: sqlite3.Connection,
    symbole: set[str],
    ab_datum: str,
    coingecko_ids: dict[str, str],
) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    """EUR-Kurse je Symbol und Tag, getrennt nach Herkunft.

    ZWEI QUELLEN, und das ist kein Detail: `price_history_ohlc` ist ueber
    `symbol` verschluesselt, `price_history` ueber `coingecko_id`. Ein
    Krypto-Asset kann in der einen Tabelle stehen und in der anderen fehlen.
    Ein erster Entwurf dieses Moduls las nur die OHLC-Tabelle - damit waeren
    mehrere gehaltene Coins stillschweigend mit 0 in den Portfoliowert
    eingegangen (gefunden 04.08. bei der Auswertung der 33 gehaltenen
    Symbole).

    Reihenfolge: OHLC zuerst, `price_history` fuellt nur Luecken. Beide Quellen
    speisen sich aus demselben CoinGecko-Abruf; wo beide etwas haben, ist die
    OHLC-Reihe die spezifischere (Tages-Schlusskurs statt Momentaufnahme).

    Rueckgabe: (direkt_eur, usd_roh). Die Trennung ist Absicht - der Aufrufer
    soll je Symbol ausweisen koennen, wieviel direkt vorlag und wieviel erst
    ueber den Wechselkurs entstand. Umgerechnete Werte tragen die Unsicherheit
    der FX-Ableitung mit; das darf nicht unsichtbar werden."""
    direkt: dict[str, dict[str, float]] = {}
    usd: dict[str, dict[str, float]] = {}
    if not symbole:
        return direkt, usd

    platzhalter = ",".join("?" for _ in symbole)
    for row in conn.execute(
        f"SELECT symbol, currency, date, close FROM price_history_ohlc "
        f"WHERE symbol IN ({platzhalter}) AND date >= ? "
        f"AND currency IN ('EUR', 'USD') AND close > 0",
        (*symbole, ab_datum),
    ).fetchall():
        ziel = direkt if row["currency"] == "EUR" else usd
        ziel.setdefault(row["symbol"], {})[row["date"]] = row["close"]

    # Zweite Quelle nur fuer Symbole mit coingecko_id (= Krypto). setdefault
    # statt Zuweisung: vorhandene OHLC-Werte bleiben unangetastet.
    je_id = {cg: sym for sym, cg in coingecko_ids.items() if sym in symbole}
    if je_id:
        platzhalter_id = ",".join("?" for _ in je_id)
        for row in conn.execute(
            f"SELECT coingecko_id, date, price_eur, price_usd FROM price_history "
            f"WHERE coingecko_id IN ({platzhalter_id}) AND date >= ?",
            (*je_id, ab_datum),
        ).fetchall():
            symbol = je_id[row["coingecko_id"]]
            if row["price_eur"] and row["price_eur"] > 0:
                direkt.setdefault(symbol, {}).setdefault(row["date"], row["price_eur"])
            elif row["price_usd"] and row["price_usd"] > 0:
                usd.setdefault(symbol, {}).setdefault(row["date"], row["price_usd"])

    return direkt, usd


def rekonstruiere_stichtag(
    conn: sqlite3.Connection,
    *,
    ab_datum: str,
    bis_datum: str | None = None,
    watchlist: list | None = None,
) -> RekonstruktionsErgebnis:
    """Portfoliowert je Tag aus den HEUTIGEN Bestaenden und der Kurshistorie.

    `ab_datum` ist Pflicht und ohne Vorbelegung - der Aufrufer muss sich
    festlegen, wie weit zurueck die heutigen Bestaende noch gelten. Je weiter
    zurueck, desto mehr zwischenzeitliche Kaeufe/Verkaeufe verfaelschen das
    Ergebnis. Ein Standardwert wuerde diese Entscheidung verstecken.

    Fehlt ein Kurs, wird das Symbol an diesem Tag NICHT mit 0 bewertet, sondern
    uebersprungen und in `symbole_ohne_kurs` gezaehlt. Sonst saehe eine
    Datenluecke wie ein Kurssturz aus - und Z-3 wuerde auf eine Luecke
    ausloesen."""
    bis = bis_datum or _heute_utc()
    holdings = [h for h in db.get_all_holdings(conn) if h.quantity > 0]
    if not holdings:
        logger.warning("Portfolio-Rekonstruktion: keine Bestaende vorhanden")
        return RekonstruktionsErgebnis()

    watchlist = watchlist if watchlist is not None else config.get_watchlist()
    coingecko_ids = {a.symbol: a.coingecko_id for a in watchlist if a.coingecko_id}
    # Cash-Aequivalente haben per Definition den Kurs 1,00 EUR und brauchen
    # deshalb GAR KEINE Kurshistorie. Ohne diesen Zweig fielen sie in die
    # "kein Kurs"-Luecke und gingen mit 0 in den Portfoliowert ein - bei einem
    # Bestand von ueber 1200 EUR (Stand 04.08., EURCV) ein Fehler, der jeden
    # Drawdown-Wert unbrauchbar macht. Das Feld existiert bereits in der
    # Watchlist, es musste nur benutzt werden.
    cash_aequivalente = {a.symbol for a in watchlist if a.ist_cash_aequivalent}

    symbole = {h.symbol for h in holdings}
    mengen = {h.symbol: h.quantity for h in holdings}
    direkt, usd_roh = _eur_kurse_je_symbol(
        conn, symbole - cash_aequivalente, ab_datum, coingecko_ids
    )
    fx, fx_verworfen = tages_fx_kurse(conn)

    # Handelstage aus den vorhandenen Kursen ableiten statt einen Kalender zu
    # erzeugen: an Tagen ohne jeden Kurs gab es auch keinen bewertbaren Stand
    # (Wochenenden bei Aktien/ETFs). Ein kuenstlich erzeugter Kalendertag
    # brächte nur eine Zeile mit lauter Luecken.
    tage = sorted(
        {d for reihe in direkt.values() for d in reihe if ab_datum <= d <= bis}
        | {d for reihe in usd_roh.values() for d in reihe if ab_datum <= d <= bis}
    )

    diagnosen = {s: SymbolDiagnose(symbol=s, menge=mengen[s]) for s in symbole}
    ergebnis = RekonstruktionsErgebnis(fx_tage_verworfen=fx_verworfen)

    for tag in tage:
        wert = 0.0
        ohne_kurs = 0
        for symbol in symbole:
            diag = diagnosen[symbol]
            if symbol in cash_aequivalente:
                wert += mengen[symbol] * 1.0
                diag.tage_direkt_eur += 1
                diag.letzter_kurs_eur = 1.0
                continue
            kurs_eur = direkt.get(symbol, {}).get(tag)
            if kurs_eur is not None:
                diag.tage_direkt_eur += 1
            else:
                kurs_usd = usd_roh.get(symbol, {}).get(tag)
                tages_fx = fx.get(tag)
                if kurs_usd is not None and tages_fx is not None:
                    kurs_eur = kurs_usd * tages_fx
                    diag.tage_ueber_fx += 1
                else:
                    diag.tage_ohne_kurs += 1
                    ohne_kurs += 1
                    continue
            wert += mengen[symbol] * kurs_eur
            diag.letzter_kurs_eur = kurs_eur

        ergebnis.tageswerte.append((tag, wert, len(symbole), ohne_kurs))

    ergebnis.symbol_diagnosen = sorted(
        diagnosen.values(), key=lambda d: (-d.tage_ohne_kurs, d.symbol)
    )
    return ergebnis


def schreibe_rekonstruktion(
    conn: sqlite3.Connection, ergebnis: RekonstruktionsErgebnis
) -> int:
    """Tageswerte persistieren. Ein Commit am Ende statt einem je Tag."""
    for datum, wert, gesamt, ohne_kurs in ergebnis.tageswerte:
        db.upsert_portfolio_wert(
            conn,
            datum,
            wert,
            cash_eur=0.0,  # historisch nicht rekonstruierbar, siehe Modul-Docstring
            symbole_gesamt=gesamt,
            symbole_ohne_kurs=ohne_kurs,
            quelle=QUELLE_REKONSTRUIERT,
            commit=False,
        )
    conn.commit()
    return len(ergebnis.tageswerte)
