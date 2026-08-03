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

WOHER DIE BESTAENDE KOMMEN (Stand 04.08., Tasks #612+#613)
`bestandsverlauf()` rechnet den Verlauf VORWAERTS aus zwei Bitpanda-Quellen:
  * `get_wallet_transactions()` - alle Krypto-Bewegungen, auch die ohne
    bepreisten Trade (Staking-Gutschriften, Boni, externe Einzahlungen). Der
    Fallstrick dazu steht in `importer/bitpanda_avg_cost.py`.
  * `get_trades()` - Kaeufe/Verkaeufe ALLER Assetklassen; deckt Aktien/ETF/ETC
    ab, die in `/wallets/transactions` gar nicht vorkommen.
Beide zusammen treffen `holdings.quantity` fuer alle 33 gehaltenen Symbole.

`rekonstruiere_stichtag()` (heutiger Bestand rueckwaerts fortgeschrieben) bleibt
als Baustein erhalten, ist aber NICHT mehr der Hauptweg: das Fenster
unveraenderter Bestaende betrug am 04.08. zwei Tage. Wer sie benutzt, muss
`ab_datum` bewusst setzen - eine stillschweigende Ausdehnung auf lange
Zeitraeume waere genau der stille Falschwert, den P-10 verbietet.

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

import json
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


# --- Bestandsverlauf aus Transaktionen (Stufe 2) ----------------------------
# Regeln am 04.08. an den echten Daten hergeleitet, nicht ausgedacht: erst die
# naive Annahme (incoming +, outgoing -) gegen den Bestands-Schnappschuss
# gerechnet, dann die Abweichungen einzeln angesehen. 92 von 146 Symbolen
# stimmten sofort; von den 54 Abweichungen waren zwei Drittel gar keine
# Datenprobleme (Nicht-Krypto, Symbol-Override, Fliesskomma-Reste).


def normal_wallet_delta(tx: dict) -> float | None:
    """Wirkung EINER Buchung auf das normale Wallet. None = beruehrt es nicht.

    Der Margin-Teil ist der eigentliche Inhalt dieser Funktion. Ohne ihn stimmt
    der ENDSTAND trotzdem - ueber eine abgeschlossene Position heben sich
    Eroeffnung und Schliessung exakt auf, das Episoden-Netto ist 0. Fuer einen
    Tag MITTENDRIN gilt das nicht: eine offene Margin-Position wuerde dem
    normalen Bestand zugeschlagen.

    Gemessen an einer vollstaendigen NEAR-Episode (22.-27.07.2026): naiv lagen
    am 24.07. 355,33 NEAR im Bestand, tatsaechlich 0 - bei ~1,60 EUR gut
    570 EUR Scheinvermoegen. Ein Fehler, der jeden Endstands-Test besteht.

    Die Buchungsmechanik dahinter, am Beispiel einer 3x-Eroeffnung ueber 600 EUR:
      EURCV sell  outgoing 600  margin_trading.open    -> aus dem normalen Wallet
      EURCV transfer in  400    margin_trading.borrow  -> geliehen, ins normale
      NEAR  buy   incoming 355  margin_trading.open    -> ins MARGIN-Wallet
    Netto normal: -200 EUR, also genau das Eigenkapital. Beim Schliessen kommt
    `margin_trading.close` als PAAR aus incoming und outgoing mit identischem
    Betrag - das ist der Uebertrag margin -> normal, zaehlen darf nur eine Seite.
    """
    tags = set(tx.get("tags") or ())
    menge = tx["amount_cryptocoin_wallet"]
    eingehend = tx["in_or_out"] == "incoming"

    if "margin_trading.open" in tags:
        return None if eingehend else -menge
    if "margin_trading.repay" in tags or "margin_trading.fee" in tags:
        return None  # beides aus dem Margin-Wallet
    if "margin_trading.close" in tags:
        return menge if eingehend else None  # nur der Eingang ins normale Wallet
    return menge if eingehend else -menge


def bestandsverlauf(
    transaktionen: list[dict],
    *,
    symbol_overrides: dict[str, str] | None = None,
    trades: list[dict] | None = None,
) -> dict[str, dict[str, float]]:
    """Bestand je Symbol am ENDE jedes Tages, an dem sich etwas bewegt hat.

    Bewusst nur Bewegungstage: dazwischen aendert sich nichts, und der Aufrufer
    kann jeden Tag der Kursreihe auf den letzten Bewegungstag davor
    zurueckfuehren. Das haelt das Ergebnis klein und macht es lesbar.

    `symbol_overrides` bildet Bitpanda-Symbole auf die internen ab (z.B.
    "CC" -> "CANTON", "VST-US" -> "VST", "IS0C" -> "ISOC"). Ohne diese Abbildung
    landen 868,97 CANTON unter einem Symbol, das die Watchlist nicht kennt - im
    ersten Lauf genau so passiert.

    `trades` (GET /trades, alle Assetklassen) ERGAENZT die Wallet-Transaktionen
    fuer Aktien/ETF/ETC. `/wallets/transactions` fuehrt nur Krypto-Wallets, und
    `/asset-wallets/transactions` existiert nicht (siehe api/bitpanda.py::
    get_trades()).

    ERGAENZT, NICHT ERSETZT - und das ist hier mechanisch erzwungen: ein Trade
    wird nur beruecksichtigt, wenn das Symbol in den Transaktionen UEBERHAUPT
    NICHT vorkommt. Wuerde man beide Quellen fuer dasselbe Symbol mischen,
    zaehlte jeder Krypto-Kauf doppelt (er steht in beiden). Wuerde man umgekehrt
    fuer Krypto auf `/trades` umstellen, verlaere man 1468 `instant_trade_bonus`-
    sowie alle `stake`/`unstake`/`reward`-Buchungen - `/trades` enthaelt nur
    Trades.

    Verifiziert am 04.08. gegen den echten Account: alle 13 Nicht-Krypto-Werte
    treffen `holdings.quantity` auf sechs Nachkommastellen. Fuer diese
    Assetklassen gibt es also keine Mengenaenderungen ausserhalb von Trades
    (keine Splits, keine Fusionen im betrachteten Zeitraum).
    """
    overrides = symbol_overrides or {}
    ereignisse: list[tuple[int, str, str, float]] = []

    krypto_symbole: set[str] = set()
    for tx in transaktionen:
        delta = normal_wallet_delta(tx)
        if delta is None:
            continue
        roh = tx["cryptocoin_symbol"]
        symbol = overrides.get(roh, roh)
        krypto_symbole.add(symbol)
        ereignisse.append((tx["unix_timestamp"], tx["datum_utc"], symbol, delta))

    for tr in trades or []:
        if tr.get("status") and tr["status"] != "finished":
            continue  # nur abgeschlossene Trades aendern den Bestand
        symbol = overrides.get(tr["symbol"], tr["symbol"])
        if symbol in krypto_symbole:
            continue  # schon ueber die Wallet-Transaktionen abgedeckt
        menge = tr["amount_cryptocoin"]
        ereignisse.append((
            tr["unix_timestamp"], tr["datum_utc"], symbol,
            menge if tr["type"] == "buy" else -menge,
        ))

    laufend: dict[str, float] = {}
    verlauf: dict[str, dict[str, float]] = {}
    for _, datum, symbol, delta in sorted(ereignisse, key=lambda e: e[0]):
        laufend[symbol] = laufend.get(symbol, 0.0) + delta
        verlauf[datum] = dict(laufend)
    return verlauf


def pruefe_gegen_holdings(
    verlauf: dict[str, dict[str, float]],
    holdings: dict[str, float],
    *,
    toleranz_relativ: float = 0.01,
    epsilon: float = 1e-6,
) -> dict[str, list]:
    """Der Pruefstein: der rekonstruierte Endstand MUSS holdings.quantity treffen.

    Er hat nur dann Aussagekraft, wenn der Verlauf VORWAERTS von null gerechnet
    wurde. Rueckwaerts vom heutigen Bestand waere er per Konstruktion erfuellt
    und wuerde jede falsche Regel bestehen.

    Drei getrennte Toepfe statt einer Abweichungsliste, weil sie
    unterschiedliches bedeuten:
      `treffer`        - stimmt
      `glatt_aufgeloest` - beide praktisch null; vollstaendig verkaufte
                         Positionen hinterlassen Fliesskomma-Reste. Ein
                         relativer Vergleich meldet hier 100% Abweichung,
                         weil er durch ~1e-12 teilt - das ist ein Fehler der
                         Pruefung, nicht der Daten.
      `nicht_im_verlauf` - im Bestand, aber ohne jede Buchung. Aktien/ETF/ETC
                         stehen nicht in /wallets/transactions (13 Symbole,
                         Stand 04.08.) - eine bekannte Luecke, keine Abweichung.
      `abweichungen`   - alles andere. DAS sind die Faelle zum Ansehen.
    """
    endstand = verlauf[max(verlauf)] if verlauf else {}
    ergebnis: dict[str, list] = {
        "treffer": [], "glatt_aufgeloest": [], "nicht_im_verlauf": [], "abweichungen": [],
    }
    for symbol in sorted(set(endstand) | set(holdings)):
        soll = holdings.get(symbol, 0.0)
        ist = endstand.get(symbol, 0.0)
        if symbol not in endstand and soll > epsilon:
            ergebnis["nicht_im_verlauf"].append(symbol)
            continue
        abstand = abs(ist - soll)
        if abstand < epsilon and abs(soll) < epsilon:
            ergebnis["glatt_aufgeloest"].append(symbol)
        elif abstand / max(abs(soll), abs(ist), epsilon) < toleranz_relativ:
            ergebnis["treffer"].append(symbol)
        else:
            ergebnis["abweichungen"].append((symbol, soll, ist))
    return ergebnis


def verketteter_index(
    tage: list[str],
    mengen_am: "callable",
    kurs_am: "callable",
    *,
    startwert: float = 100.0,
) -> list[tuple[str, float, int]]:
    """Mengenkonstanter Index - die Grundlage, auf der Z-3 rechnen muss.

    WARUM NICHT DER ROHE PORTFOLIOWERT
    Ein Zukauf hebt den Portfoliowert, ist aber kein Gewinn; ein Verkauf senkt
    ihn, ist aber kein Verlust. Eine Drawdown-Notbremse auf der rohen Wertreihe
    wuerde also auf Handelsaktivitaet reagieren statt auf Marktbewegung - und
    zwar in beide Richtungen falsch: ein grosser Verkauf koennte Z-3 grundlos
    ausloesen, ein grosser Zukauf einen echten Einbruch verdecken.

    Das ist keine graue Theorie: am 12.07. gab es eine Einzahlung ueber 2.500
    EUR, dazu laufende Sparplan-Kaeufe. Der Fiat-Zufluss selbst steht nicht im
    Krypto-Export, aber sobald er zu einem Kauf wird, hebt er die Mengen - und
    damit den rohen Wert.

    DIE FORMEL
    Fuer jeden Tag wird die Rendite mit den Mengen des VORTAGS gerechnet:

        r_t = (Summe q_{t-1} * p_t) / (Summe q_{t-1} * p_{t-1}) - 1

    Weil in Zaehler und Nenner dieselben Mengen stehen, faellt jede
    zwischenzeitliche Mengenaenderung heraus - uebrig bleibt reine
    Kursbewegung. Die Tagesrenditen werden dann verkettet
    (I_t = I_{t-1} * (1 + r_t)). Das ist die zeitgewichtete Rendite, der
    uebliche Weg, Performance von Ein- und Auszahlungen zu trennen.

    `mengen_am(tag) -> dict[symbol, menge]` und
    `kurs_am(symbol, tag) -> float | None` werden hereingereicht, damit diese
    Funktion rein rechnerisch bleibt und ohne Datenbank testbar ist.

    Rueckgabe je Tag: (datum, indexwert, anzahl_bewerteter_symbole). Die dritte
    Zahl ist kein Beiwerk - faellt sie ploetzlich, beruht die Tagesrendite auf
    weniger Positionen und ist entsprechend weniger belastbar.

    Ein Symbol geht nur in die Rendite ein, wenn es an BEIDEN Tagen einen Kurs
    hat. Sonst waere der Vergleich schief: ein Symbol nur im Zaehler wirkt wie
    ein Kurssprung aus dem Nichts, nur im Nenner wie ein Totalverlust.
    """
    index = startwert
    reihe: list[tuple[str, float, int]] = []
    for i, tag in enumerate(tage):
        if i == 0:
            reihe.append((tag, index, 0))
            continue
        vortag = tage[i - 1]
        basis = mengen_am(vortag)
        alt = neu = 0.0
        bewertet = 0
        for symbol, menge in basis.items():
            if menge <= 0:
                continue
            p_alt, p_neu = kurs_am(symbol, vortag), kurs_am(symbol, tag)
            if p_alt is None or p_neu is None:
                continue
            alt += menge * p_alt
            neu += menge * p_neu
            bewertet += 1
        if alt > 0:
            index *= neu / alt
        reihe.append((tag, index, bewertet))
    return reihe


def groesster_rueckschlag(reihe: list[tuple[str, float, int]]) -> dict:
    """Groesster Rueckgang vom laufenden Hoechststand - die Zahl, gegen die
    Z-3/RM-7 seine Schwelle (`ziele.max_drawdown_prozent`, 15) prueft.

    Zusaetzlich `aktuell_prozent`: der Abstand zum Hoechststand HEUTE. Fuer die
    Notbremse ist das der eigentlich relevante Wert - der historisch groesste
    Rueckschlag ist Kontext, ausgeloest wird auf dem aktuellen."""
    if not reihe:
        return {"max_prozent": 0.0, "aktuell_prozent": 0.0, "hoch_am": None, "tief_am": None}
    hoch = reihe[0][1]
    hoch_am = tief_am = reihe[0][0]
    schlimmster_hoch_am = reihe[0][0]
    max_rueckschlag = 0.0
    for tag, wert, _ in reihe:
        if wert > hoch:
            hoch, hoch_am = wert, tag
        rueckschlag = (hoch - wert) / hoch * 100 if hoch > 0 else 0.0
        if rueckschlag > max_rueckschlag:
            max_rueckschlag, tief_am, schlimmster_hoch_am = rueckschlag, tag, hoch_am
    letzter = reihe[-1][1]
    return {
        "max_prozent": max_rueckschlag,
        "aktuell_prozent": (hoch - letzter) / hoch * 100 if hoch > 0 else 0.0,
        "hoch_am": schlimmster_hoch_am,
        "tief_am": tief_am,
    }


def _kurs_lookup(
    conn: sqlite3.Connection,
    symbole: set[str],
    ab_datum: str,
    coingecko_ids: dict[str, str],
    cash_aequivalente: set[str],
) -> tuple["callable", dict[str, str]]:
    """Baut eine `kurs_am(symbol, tag) -> float | None`-Funktion und meldet je
    Symbol, woher die Kurse kamen ('eur', 'fx', 'cash', 'keine').

    Einmal alle Kurse laden statt je Abfrage in die DB: bei 88 Tagen x 33
    Symbolen waeren das sonst knapp 3000 Einzelabfragen."""
    direkt, usd_roh = _eur_kurse_je_symbol(
        conn, symbole - cash_aequivalente, ab_datum, coingecko_ids
    )
    fx, _ = tages_fx_kurse(conn)

    herkunft: dict[str, str] = {}
    for symbol in symbole:
        if symbol in cash_aequivalente:
            herkunft[symbol] = "cash"
        elif direkt.get(symbol):
            herkunft[symbol] = "eur"
        elif usd_roh.get(symbol):
            herkunft[symbol] = "fx"
        else:
            herkunft[symbol] = "keine"

    def kurs_am(symbol: str, tag: str) -> float | None:
        if symbol in cash_aequivalente:
            return 1.0
        kurs = direkt.get(symbol, {}).get(tag)
        if kurs is not None:
            return kurs
        usd = usd_roh.get(symbol, {}).get(tag)
        tages_fx = fx.get(tag)
        return usd * tages_fx if usd is not None and tages_fx is not None else None

    return kurs_am, herkunft


def rekonstruiere_aus_transaktionen(
    conn: sqlite3.Connection,
    transaktionen: list[dict],
    holdings: dict[str, float],
    *,
    ab_datum: str,
    watchlist: list | None = None,
    symbol_overrides: dict[str, str] | None = None,
    nur_symbole: set[str] | None = None,
    trades: list[dict] | None = None,
) -> tuple[list[tuple[str, float, int, int]], dict]:
    """Alle drei Schichten zusammen: Buchungen -> Mengen je Tag -> EUR-Wert
    je Tag -> mengenkonstanter Index.

    NAEHERUNG FUER NICHT-KRYPTO (Nutzer-Entscheidung 04.08.)
    Aktien, ETFs und ETCs stehen nicht in `/wallets/transactions` - fuer sie
    gibt es keinen Bestandsverlauf. Ihre HEUTIGE Menge wird deshalb konstant
    ueber den ganzen Zeitraum angesetzt. Das ist genau dann richtig, wenn in
    diesen Werten nicht gehandelt wurde, und wird mit jedem zurueckliegenden
    Kauf/Verkauf ungenauer.

    Die Naeherung wird NICHT stillschweigend angewandt: jedes betroffene Symbol
    steht namentlich in `diagnose["naeherung_konstante_menge"]`, und wer die
    Zahlen liest, soll die Liste sehen. Fuer den Drawdown ist der Effekt
    ausserdem gedaempft - der Index rechnet mit den Mengen des Vortags, und
    eine konstante Menge ist ueber zwei aufeinanderfolgende Tage per Definition
    unveraendert. Falsch wird nur das GEWICHT dieser Werte im Index, nicht ihre
    Kursbewegung.

    Rueckgabe: (reihe, diagnose). Reihe je Tag:
    (datum, wert_eur, index, anzahl_bewerteter_symbole).
    """
    watchlist = watchlist if watchlist is not None else config.get_watchlist()
    coingecko_ids = {a.symbol: a.coingecko_id for a in watchlist if a.coingecko_id}
    cash_aequivalente = {a.symbol for a in watchlist if a.ist_cash_aequivalent}

    verlauf = bestandsverlauf(transaktionen, symbol_overrides=symbol_overrides, trades=trades)
    bewegungstage = sorted(verlauf)
    ohne_verlauf = {
        s: menge for s, menge in holdings.items()
        if menge > 0 and (not bewegungstage or s not in verlauf[bewegungstage[-1]])
    }
    if nur_symbole is not None:
        verlauf = {t: {s: m for s, m in stand.items() if s in nur_symbole}
                   for t, stand in verlauf.items()}
        ohne_verlauf = {s: m for s, m in ohne_verlauf.items() if s in nur_symbole}

    def mengen_am(tag: str) -> dict[str, float]:
        """Bestand am Ende von `tag`: der letzte Bewegungstag davor, ergaenzt um
        die konstant gehaltenen Nicht-Krypto-Werte."""
        stand: dict[str, float] = {}
        for bewegungstag in bewegungstage:
            if bewegungstag > tag:
                break
            stand = verlauf[bewegungstag]
        return {**stand, **ohne_verlauf}

    alle_symbole = set(ohne_verlauf) | {
        s for tagesstand in verlauf.values() for s in tagesstand
    }
    kurs_am, herkunft = _kurs_lookup(
        conn, alle_symbole, ab_datum, coingecko_ids, cash_aequivalente
    )

    # Handelstage aus den Kursen ableiten, nicht aus einem Kalender: an Tagen
    # ohne jeden Kurs gab es keinen bewertbaren Stand.
    tage = sorted({
        r["date"] for r in conn.execute(
            "SELECT DISTINCT date FROM price_history_ohlc WHERE date >= ?", (ab_datum,)
        ).fetchall()
    } | {
        r["date"] for r in conn.execute(
            "SELECT DISTINCT date FROM price_history WHERE date >= ?", (ab_datum,)
        ).fetchall()
    })

    index_reihe = verketteter_index(tage, mengen_am, kurs_am)
    reihe: list[tuple[str, float, int, int]] = []
    for (tag, index, bewertet) in index_reihe:
        stand = mengen_am(tag)
        wert = 0.0
        ohne_kurs = 0
        for symbol, menge in stand.items():
            if menge <= 0:
                continue
            kurs = kurs_am(symbol, tag)
            if kurs is None:
                ohne_kurs += 1
            else:
                wert += menge * kurs
        reihe.append((tag, wert, index, ohne_kurs))
        del bewertet

    diagnose = {
        "naeherung_konstante_menge": sorted(ohne_verlauf),
        "kursherkunft": herkunft,
        "ohne_jeden_kurs": sorted(s for s, h in herkunft.items() if h == "keine"),
        "bewegungstage_gesamt": len(bewegungstage),
        "bewegungstage_im_fenster": sum(1 for t in bewegungstage if t >= ab_datum),
    }
    return reihe, diagnose


def reihen_je_kategorie(
    conn: sqlite3.Connection,
    transaktionen: list[dict],
    holdings: dict[str, float],
    *,
    ab_datum: str,
    watchlist: list | None = None,
    symbol_overrides: dict[str, str] | None = None,
    trades: list[dict] | None = None,
) -> dict[str, tuple[list, dict]]:
    """Dieselbe Reihe zusaetzlich je Assetklasse - als DIAGNOSE, nicht als
    zweiter Ausloeser.

    ROLLENVERTEILUNG (Nutzer-Entscheidung 04.08., nach eigenem Vorschlag)
    Ausgeloest wird Z-3/RM-7 weiterhin auf dem GESAMTwert. Das ist keine
    Bequemlichkeit, sondern folgt aus dem Zweck der Regel: Z-3 schuetzt
    Kapital, und Diversifikation ist genau dafuer da. Faellt Krypto um 20%
    waehrend Aktien halten, liegt der Gesamtrueckschlag vielleicht bei 12% -
    das Portfolio ist intakt, ein kategoriebezogener Alarm waere ein
    Fehlsignal. Ausserdem ist `ziele.max_drawdown_prozent` eine
    Portfolio-Groesse, und RG-6 stellt Z-3 unter Aenderungsschutz; ein zweiter
    Ausloeser waere eine neue Regel, keine Anpassung.

    WOFUER DIE AUFSCHLUESSELUNG DANN DA IST
    Sie beantwortet die Frage, die nach jedem Alarm sofort kommt: woher kommt
    der Rueckschlag? Gedacht fuers Dashboard, die Alert-Mail und perspektivisch
    als Fakt fuer die Analysten.

    UND EIN QUALITAETSARGUMENT, das nicht untergehen soll: die Krypto-Reihe
    kommt OHNE Naeherung aus. Jede Mengenaenderung ist dort durch eine Buchung
    belegt, lueckenlos ueber zwei Jahre. Die konstant gehaltenen Mengen
    betreffen ausschliesslich Aktien/ETF/ETC. Wer beide Reihen nebeneinander
    liest, sollte wissen, dass die eine gemessen und die andere teilweise
    angenommen ist - `diagnose["naeherung_konstante_menge"]` sagt es je Reihe.

    Rueckgabe: {"gesamt": (reihe, diagnose), "krypto": (...), ...}
    """
    watchlist = watchlist if watchlist is not None else config.get_watchlist()
    je_klasse: dict[str, set[str]] = {}
    for asset in watchlist:
        klasse = getattr(asset, "assetklasse", None) or "unbekannt"
        je_klasse.setdefault(klasse, set()).add(asset.symbol)

    ergebnis: dict[str, tuple[list, dict]] = {
        "gesamt": rekonstruiere_aus_transaktionen(
            conn, transaktionen, holdings, ab_datum=ab_datum,
            watchlist=watchlist, symbol_overrides=symbol_overrides, trades=trades,
        )
    }
    for klasse, symbole in sorted(je_klasse.items()):
        # Leere Kategorien ueberspringen statt eine Reihe aus Nullen zu bauen -
        # eine flache Linie bei 100 saehe aus wie "keine Bewegung" statt wie
        # "keine Daten".
        if not (symbole & set(holdings)):
            continue
        ergebnis[klasse] = rekonstruiere_aus_transaktionen(
            conn, transaktionen, holdings, ab_datum=ab_datum,
            watchlist=watchlist, symbol_overrides=symbol_overrides,
            nur_symbole=symbole, trades=trades,
        )
    return ergebnis


def schreibe_tageswert(
    conn: sqlite3.Connection,
    *,
    datum: str | None = None,
    watchlist: list | None = None,
) -> dict:
    """Den heutigen Portfoliowert fortschreiben - der taegliche Betriebsteil.

    Setzt den Index dort fort, wo die letzte Zeile aufgehoert hat: die
    Tagesrendite wird mit den Mengen des VORTAGS gerechnet (aus `mengen_json`,
    nicht aus `holdings` - letzteres ist zum Zeitpunkt des Laufs schon der
    heutige Stand und wuerde den Zukauf mitzaehlen, den der Index gerade
    herausrechnen soll).

    Gibt es noch keine Vorzeile, startet der Index bei 100 - dann ist der
    Rueckschlag naturgemaess 0, bis genug Historie da ist.

    WORAUF ZU ACHTEN IST: `symbole_ohne_kurs` in der geschriebenen Zeile. Steigt
    diese Zahl, fehlen Kurse, und der Tageswert ist zu niedrig - das saehe wie
    ein Kursrutsch aus. Deshalb wird sie mitgeschrieben und nicht nur geloggt.
    """
    tag = datum or _heute_utc()
    watchlist = watchlist if watchlist is not None else config.get_watchlist()
    coingecko_ids = {a.symbol: a.coingecko_id for a in watchlist if a.coingecko_id}
    cash_aequivalente = {a.symbol for a in watchlist if a.ist_cash_aequivalent}

    holdings = {h.symbol: h.quantity for h in db.get_all_holdings(conn) if h.quantity > 0}
    vorzeilen = [z for z in db.get_portfolio_wert_historie(conn) if z["datum"] < tag]
    vorzeile = vorzeilen[-1] if vorzeilen else None

    ab = vorzeile["datum"] if vorzeile else tag
    kurs_am, _ = _kurs_lookup(
        conn, set(holdings) | set(json.loads(vorzeile["mengen_json"] or "{}") if vorzeile else ()),
        ab, coingecko_ids, cash_aequivalente,
    )

    wert = 0.0
    ohne_kurs = 0
    for symbol, menge in holdings.items():
        kurs = kurs_am(symbol, tag)
        if kurs is None:
            ohne_kurs += 1
        else:
            wert += menge * kurs

    index = 100.0
    if vorzeile and vorzeile["index_wert"] and vorzeile["mengen_json"]:
        basis = json.loads(vorzeile["mengen_json"])
        alt = neu = 0.0
        for symbol, menge in basis.items():
            p_alt, p_neu = kurs_am(symbol, vorzeile["datum"]), kurs_am(symbol, tag)
            if p_alt is None or p_neu is None or menge <= 0:
                continue
            alt += menge * p_alt
            neu += menge * p_neu
        index = vorzeile["index_wert"] * (neu / alt) if alt > 0 else vorzeile["index_wert"]

    db.upsert_portfolio_wert(
        conn, tag, wert,
        cash_eur=db.get_cash_reserve_fiat_eur(conn),
        symbole_gesamt=len(holdings),
        symbole_ohne_kurs=ohne_kurs,
        quelle=QUELLE_LAUFEND,
        index_wert=index,
        mengen_json=json.dumps(holdings),
    )
    return {"datum": tag, "wert_eur": wert, "index": index, "symbole_ohne_kurs": ohne_kurs}


def pruefe_z3(conn: sqlite3.Connection, *, schwelle_prozent: float) -> dict:
    """Z-3 / RM-7 - Drawdown-Notbremse.

    HART UND NICHT UEBERSCHREIBBAR (RG-6: "Weder Nutzer noch KI duerfen RM-1,
    RM-5 oder Z-3 per Override..."). Diese Funktion nimmt deshalb bewusst
    KEINEN Override-Parameter entgegen - was es nicht gibt, kann auch nicht
    versehentlich verdrahtet werden.

    Wirkt laut Spezifikation als DRINGENDER ALERT, nicht als Automatik: das
    System kann ohnehin keine Order ausloesen (keine Handels-API bei Bitpanda).
    `ausgeloest` heisst also "melden und Kapitalschutz-Modus S-5 erwaegen",
    nicht "verkaufen".

    Gerechnet wird auf `index_wert`, NICHT auf `wert_eur` - sonst loeste ein
    grosser Verkauf die Notbremse aus und ein grosser Zukauf verdeckte einen
    echten Einbruch.

    `datenbasis_duenn` ist der Ehrlichkeitsteil: mit wenigen Tagen Historie ist
    ein Hoechststand kein Hoechststand. Wer den Alert liest, soll sehen, worauf
    er beruht - eine Notbremse, die am dritten Tag ausloest, sagt mehr ueber
    die Datenlage als ueber den Markt.
    """
    reihe = [
        (z["datum"], z["index_wert"], 0)
        for z in db.get_portfolio_wert_historie(conn)
        if z["index_wert"] is not None
    ]
    rueckschlag = groesster_rueckschlag(reihe)
    return {
        **rueckschlag,
        "schwelle_prozent": schwelle_prozent,
        "ausgeloest": rueckschlag["aktuell_prozent"] >= schwelle_prozent,
        "tage_historie": len(reihe),
        "datenbasis_duenn": len(reihe) < 30,
    }


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
