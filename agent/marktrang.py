# -*- coding: utf-8 -*-
"""Wo steht dieser Wert HEUTE im Markt? (30.08.2026, G-2' Schritt 1)

⚠️ DIESES MODUL SPERRT NICHTS. Es rechnet zwei Rangplaetze aus und gibt sie
zurueck. Kein Signal wird verhindert, keine Reihenfolge geaendert, kein Budget
umgelenkt - genau wie `vorfilter.py` es fuer H tut. Die Wirkung kommt erst mit
G-6, und das ist eine eigene Entscheidung.

## Die zwei Groessen, und warum genau diese

Beide sind am 30.08.2026 **als REGEL** gemessen worden, nicht als Merkmal
(Regelwerk R-R8, Methodik 2.87). Die Zahl in Klammern ist die Wirkung einer
Regel "kein Einstieg im obersten Fuenftel", gepaart auf denselben Ankern:

    FUNDING    was Long-Positionen taeglich kosten      (+0,0246 R)
               hoch = viele Longs = ueberhitzt = Warnsignal
               290 Symbole, 6,3 Jahre, beide Historienhaelften, beide
               Marktphasen, monoton ueber fuenf Fuenftel

    TURNOVER   Handelsvolumen / Umlaufmenge             (+0,0616 R)
               hoch = viel Aufmerksamkeit = eher ueberbewertet
               66 Symbole; traegt auch bei den schwaecheren 33 (+0,0471)

**Zusammen sind sie zu 92 % additiv** - zwei eigenstaendige Beitraege, kein
doppelt gezaehlter. Korrelation untereinander nur -0,158.

## ⚠️ DER RANGPLATZ IST EIN QUERSCHNITT - das ist keine Nebensache

Gemessen wurde: *welches Asset hat HEUTE, verglichen mit den anderen, das
niedrigste Funding.* Die Je-Reihe-Sicht ("ist dieses Asset guenstig fuer seine
eigenen Verhaeltnisse") wurde ebenfalls geprueft und traegt **nicht** - sie
war marktbereinigt -0,0755 R und damit reines Markt-Timing.

**Folge fuer die Bauform:** Der Rang wird IMMER ueber alle heute bewerteten
Symbole gebildet, nie gegen die eigene Historie. Faellt der Querschnitt weg,
faellt die Aussage weg - dann liefert dieses Modul `None`, nicht einen Wert
aus zwei Vergleichen.

## Datenquellen - je ein Aufruf fuer alle Symbole

    Funding    fapi.binance.com/fapi/v1/premiumIndex   885 Eintraege, 1 Call
    Turnover   api.coingecko.com/coins/markets         250 Coins,     1 Call

⚠️ CoinGecko kostet Kontingent (10.000/Monat, Grundverbrauch bereits ~230/Tag).
**Ein Aufruf je Lauf** ist eingeplant - 0,4 % des Monatskontingents.

⚠️ Die Umlaufmenge kommt hier von CoinGecko (`circulating_supply`), gemessen
wurde mit Coin Metrics (`SplyCur`). Die Definitionen unterscheiden sich
(Burns, gesperrte Bestaende - bei BNB 29 %). **Geprueft am 30.08.:
Rangkorrelation +0,967, und die Sperrentscheidung waere bei 33 von 33
Symbolen identisch.** Der Wechsel ist damit unkritisch.

## Was das Modul NICHT tut

- es sperrt nicht (siehe oben)
- es raet nicht: fehlt eine Groesse, steht dort `None` und nicht 0. Ein
  Merkmal, das man nicht kennt, darf nie aussehen wie eines, das man geprueft
  hat (dieselbe Regel wie bei H: `h = None`, nicht `h = False`)
- es rechnet keine Punkte: die Umsetzung in Prozentpunkte ist Sache von
  `wahrscheinlichkeit.py` (Schritt 3)
"""
from __future__ import annotations

import json
import logging
import urllib.request

logger = logging.getLogger(__name__)

PREMIUM_INDEX = "https://fapi.binance.com/fapi/v1/premiumIndex"
COINGECKO_MARKETS = ("https://api.coingecko.com/api/v3/coins/markets"
                     "?vs_currency=usd&order=market_cap_desc&per_page=250&page=1")
KOPF = {"User-Agent": "TradingInfoTool/1.0"}
ZEITSPERRE = 30

# Unter dieser Zahl bewerteter Symbole ist ein Fuenftel kein Fuenftel mehr.
# Bei 10 Werten enthaelt es zwei - eine Rangaussage waere Zufall.
MINDEST_QUERSCHNITT = 15

# ---------------------------------------------------------------------------
# ⚠️⚠️ DIE GRUNDGESAMTHEIT DES RANGS - die Frage, an der H gescheitert ist
# ---------------------------------------------------------------------------
#
# Drei Mengen kommen in Frage, und nur EINE ist richtig:
#
#   WATCHLIST   43 Werte (bei anderen Klassen 2-5). ✖ Der Platz haengt an
#               unserer Auswahl - "Fuenftel 2" bedeutete bei 43 Werten etwas
#               anderes als bei 5. Nutzervorgabe 31.08.: *"ein neutraler
#               Trade ist unabhaengig von der Anzahl der Assets zu
#               bewerten."* Bis heute stand genau das im Code.
#   MARKT       837 Perpetual-Paare bzw. 232 Coins. ✖ Gemessen wurde darauf
#               NIE. Geprueft am 31.08.: von 293 gemeinsamen Symbolen
#               bekommen nur 56 % dasselbe Fuenftel wie in der Messung,
#               Abweichung bis zu DREI Stufen. Das waere der H-Fehler in
#               neuer Form - Messung und Anwendung laufen auseinander.
#   MESSBASIS   die Symbole, auf denen die Beitragstabelle entstanden ist.
#               ✔ Nur hier gilt, was `rechne_funding_beitrag.py` und
#               `rechne_turnover_beitrag.py` ausgerechnet haben.
#
# Deshalb: der Marktabruf liefert alles, gerangt wird ueber die Schnittmenge
# mit der Messbasis, abgelesen wird fuer unsere Symbole.
#
# ⚠️ FEHLT DIE MESSBASIS, GIBT ES KEINEN RANG. Ein Rang ueber die falsche
# Menge saehe genauso aus wie ein richtiger - und niemand koennte ihm
# widersprechen.
# ---------------------------------------------------------------------------
# DER DRITTE BEITRAG: ABSTAND ZUM EIGENEN 200-SCHNITT (P2/P3, 31.08.2026)
# ---------------------------------------------------------------------------
#
# ⚠️ WARUM ER ANDERS GEBAUT IST ALS FUNDING UND TURNOVER. Beide kommen aus
# Fremdquellen und haben deshalb Luecken - nach dem Nachladen am 31.08.
# immer noch 7 von 43 Werten ohne jeden Beitrag. Binance und CoinGecko
# listen nicht jeden Wert, und daran aendert kein Abruf etwas.
#
# Der Schnittabstand braucht nur die KURSREIHE. Abdeckung: 523 von 523
# Messreihen, 40 von 43 Watchlist-Werten (drei ohne ausreichende Historie).
# Genau das war die Eigenschaft von Vorfilter H, und sie fehlte seinen
# Nachfolgern.
#
# ⚠️⚠️ DER RANG MUSS UEBER DIE MESSBASIS LAUFEN - gemessen am 31.08.:
#
#     Rang ueber alle 523:          +1,39/+1,16/+0,55/-1,06/-2,04  Spanne +3,43
#     Rang nur ueber die Watchlist: -0,03/-0,08/-3,11/+0,14/+3,07  Spanne -3,10
#
# Ueber die Watchlist gerangt DREHT DAS VORZEICHEN. Der Beitrag wuerde
# genau falsch herum wirken. Nur 54 % der Fuenftel stimmen ueberein.
#
# ⚠️ ZWEI QUELLEN, UND DAS IST BEGRUENDET:
#   Schnitt (200 Tage)  aus `messdaten.db` - er aendert sich langsam.
#                       Gemessen: ein 10 Tage alter Schnitt liefert bei
#                       aktuellem Kurs 93,5 % identische Fuenftel (5 Tage:
#                       96,6 %, 20 Tage: 87,9 %). Daher die Frischegrenze.
#   aktueller Kurs      aus EINEM Binance-Abruf. Der Kurs ist die Haelfte
#                       der Groesse und darf NICHT alt sein.
SCHNITT_TAGE = 200
SCHNITT_MESSDB = "data/messdaten.db"
SCHNITT_FRISCHE_TAGE = 10          # ab hier kein Rang mehr - siehe oben
BINANCE_PREISE = "https://api.binance.com/api/v3/ticker/price"
_SCHNITT_ZWISCHEN: dict = {}


def schnitte(hoechstalter: int = SCHNITT_FRISCHE_TAGE) -> dict:
    """Je Symbol der 200-Tage-Schnitt aus der Messbasis. Leer = zu alt.

    ⚠️ GIBT LIEBER NICHTS ALS EINEN ALTEN SCHNITT. Ein veralteter Wert
    saehe aus wie ein frischer, und niemand koennte ihm widersprechen.
    """
    import datetime as _dt
    import sqlite3
    if "werte" in _SCHNITT_ZWISCHEN:
        return _SCHNITT_ZWISCHEN["werte"]
    aus: dict = {}
    try:
        c = sqlite3.connect("file:%s?mode=ro" % SCHNITT_MESSDB, uri=True)
        letzte = c.execute(
            "SELECT MAX(date) FROM price_history_ohlc "
            "WHERE currency='USD'").fetchone()[0]
        alter = (_dt.date.today()
                 - _dt.date.fromisoformat(str(letzte)[:10])).days
        if alter > hoechstalter:
            logger.error("Schnittabstand: Messbasis ist %d Tage alt "
                         "(Grenze %d) - kein Rang. `lade_messreihen.py` "
                         "nachziehen.", alter, hoechstalter)
            c.close()
            _SCHNITT_ZWISCHEN["werte"] = {}
            return {}
        roh: dict = {}
        for sym, kurs in c.execute(
                "SELECT symbol, close FROM price_history_ohlc "
                "WHERE currency='USD' AND close IS NOT NULL AND close > 0 "
                "ORDER BY symbol, date"):
            roh.setdefault(str(sym).upper(), []).append(float(kurs))
        c.close()
        for sym, reihe in roh.items():
            if len(reihe) >= SCHNITT_TAGE:
                aus[sym] = sum(reihe[-SCHNITT_TAGE:]) / SCHNITT_TAGE
    except Exception:                                        # noqa: BLE001
        logger.exception("Schnittabstand: Messbasis nicht lesbar")
        aus = {}

    # ---- ERGAENZUNG AUS DER PRODUKTIONS-DB (31.08.2026) ----------------
    #
    # ⚠️ WARUM DAS ERLAUBT IST, obwohl zwei Quellen gemischt werden: der
    # Schnittabstand ist eine RELATIVE Groesse (`Kurs / Schnitt - 1`).
    # Waehrung und Boerse kuerzen sich heraus, solange Kurs und Schnitt
    # aus DERSELBEN Reihe stammen. Genau das wird hier eingehalten.
    #
    # Ohne diese Ergaenzung fehlten 14 von 43 Watchlist-Werten, weil die
    # Messbasis nur Binance-USDT-Spotpaare enthaelt - AIOZ, AKT, BRETT,
    # GRIFFAIN, HYPE, KAS und andere sind dort nicht gelistet. Mit ihr
    # sind es noch 2 (CANTON, VSN - beide ohne jede Kursreihe).
    try:
        c = sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True)
        je_sym: dict = {}
        for sym, waehrung, kurs, tag in c.execute(
                "SELECT symbol, currency, close, date FROM price_history_ohlc "
                "WHERE close IS NOT NULL AND close > 0 ORDER BY symbol, date"):
            je_sym.setdefault((str(sym).upper(), waehrung), []).append(
                (str(tag)[:10], float(kurs)))
        c.close()
        # je Symbol die LAENGSTE Reihe nehmen - nicht die erste beste
        beste: dict = {}
        for (sym, _w), reihe in je_sym.items():
            if sym in aus:
                continue
            if len(reihe) > len(beste.get(sym, ())):
                beste[sym] = reihe
        for sym, reihe in beste.items():
            if len(reihe) < SCHNITT_TAGE:
                continue
            # ⚠️ FRISCHE AM KURS, nicht am Schnitt. Der Schnitt darf alt
            # sein (gemessen: 10 Tage -> 93,5 % identische Fuenftel), der
            # Kurs nicht - er ist die Haelfte der Groesse.
            alter = (_dt.date.today()
                     - _dt.date.fromisoformat(reihe[-1][0])).days
            if alter > hoechstalter:
                logger.info("Schnittabstand: %s uebersprungen - Kurs %d "
                            "Tage alt", sym, alter)
                continue
            aus[sym] = sum(k for _t, k in reihe[-SCHNITT_TAGE:]) / SCHNITT_TAGE
            _SCHNITT_ZWISCHEN.setdefault("eigenkurs", {})[sym] = reihe[-1][1]
    except Exception:                                        # noqa: BLE001
        logger.exception("Schnittabstand: Produktions-DB nicht lesbar")

    # ---- DRITTE QUELLE: `price_history` ueber die coingecko_id ----------
    #
    # ⚠️ NUTZERHINWEIS 31.08.: *"es gibt bereits eine Abfrage ueber
    # Coingecko - wir fragen bereits Werte auf LAGER ab, schau in die Doku
    # wo das genau ist."* Er hatte recht, und ich hatte in der falschen
    # Tabelle gesucht:
    #
    #     price_history_ohlc   Schluessel `symbol`        (Kraken/Binance/Bybit)
    #     price_history        Schluessel `coingecko_id`  (CoinGecko, alle 15 Min)
    #
    # `refresh_prices_job` holt ueber `fetch_price_snapshots` fuer JEDEN
    # Watchlist-Wert mit `coingecko_id` einen Tagespreis. Damit haben auch
    # Werte OHNE Boersenlisting eine Reihe - CANTON 252 Tage, VSN 365,
    # AIOZ und SUPRA je 378. Genau die Werte, die vorher als "keine
    # Kursreihe" galten.
    #
    # ⚠️ NUR CLOSE, kein OHLC - fuer einen gleitenden Schnitt genuegt das.
    try:
        namen = _coingecko_namen()
        c = sqlite3.connect("file:data/tradinginfotool.db?mode=ro", uri=True)
        je_id: dict = {}
        for kid, tag, usd, eur in c.execute(
                "SELECT coingecko_id, date, price_usd, price_eur "
                "FROM price_history ORDER BY coingecko_id, date"):
            kurs = usd if usd else eur
            if kurs and float(kurs) > 0:
                je_id.setdefault(str(kid).lower(), []).append(
                    (str(tag)[:10], float(kurs)))
        c.close()
        for kid, reihe in je_id.items():
            sym = namen.get(kid)
            if not sym or sym in aus or len(reihe) < SCHNITT_TAGE:
                continue
            alter = (_dt.date.today()
                     - _dt.date.fromisoformat(reihe[-1][0])).days
            if alter > hoechstalter:
                logger.info("Schnittabstand: %s (price_history) "
                            "uebersprungen - Kurs %d Tage alt", sym, alter)
                continue
            aus[sym] = sum(k for _t, k in reihe[-SCHNITT_TAGE:]) / SCHNITT_TAGE
            _SCHNITT_ZWISCHEN.setdefault("eigenkurs", {})[sym] = reihe[-1][1]
    except Exception:                                        # noqa: BLE001
        logger.exception("Schnittabstand: price_history nicht lesbar")

    _SCHNITT_ZWISCHEN["werte"] = aus
    return aus


def schnitt_werte(symbole=None) -> dict:
    """Abstand zum eigenen 200-Schnitt, fuer die ganze Messbasis.

    ⚠️ Der Rang entsteht ueber die Messbasis; `symbole` filtert nur die
    Rueckgabe (siehe `raenge`). Ueber die Watchlist gerangt dreht das
    Vorzeichen - das ist gemessen, nicht befuerchtet.
    """
    schnitt = schnitte()
    if not schnitt:
        return {}
    preise = {}
    for e in _hole(BINANCE_PREISE):
        paar = str(e.get("symbol") or "")
        if paar.endswith("USDT") and "_" not in paar:
            try:
                preise[paar[:-4]] = float(e.get("price"))
            except (TypeError, ValueError):
                continue
    eigen = _SCHNITT_ZWISCHEN.get("eigenkurs") or {}
    aus = {}
    for sym, sch in schnitt.items():
        # ⚠️ BINANCE ZUERST (aktuellster Kurs), sonst der letzte Kurs
        # DERSELBEN Reihe, aus der auch der Schnitt stammt.
        k = preise.get(sym) or eigen.get(sym)
        if k and sch > 0:
            aus[sym] = k / sch - 1.0
    return aus


MESSBASIS = {"funding": ("data/funding_historie.db",
                         "SELECT DISTINCT symbol FROM funding"),
             # ⚠️ `splycur` ist die Umlaufmenge - die Turnover-Messung
             # brauchte sie als Nenner, und nur wo sie vorliegt, ist die
             # Kennzahl ueberhaupt entstanden.
             "turnover": ("data/onchain_historie.db",
                          "SELECT DISTINCT symbol FROM splycur"),
             # ⚠️ Der Schnittabstand kommt aus den KURSREIHEN selbst -
             # die Messbasis ist dieselbe Datei, aus der auch der
             # Schnitt stammt. Deshalb genuegt die Symbolliste.
             "schnitt": (SCHNITT_MESSDB,
                         "SELECT DISTINCT symbol FROM price_history_ohlc "
                         "WHERE currency='USD'")}
_MESSBASIS_ZWISCHEN: dict = {}


def messbasis(name: str) -> set:
    """Die Symbole, auf denen der Beitrag gemessen wurde. Leer = unbekannt."""
    import sqlite3
    if name in _MESSBASIS_ZWISCHEN:
        return _MESSBASIS_ZWISCHEN[name]
    datei, frage = MESSBASIS[name]
    aus: set = set()
    try:
        c = sqlite3.connect("file:%s?mode=ro" % datei, uri=True)
        aus = {str(r[0]).upper() for r in c.execute(frage) if r[0]}
        c.close()
    except Exception:                                        # noqa: BLE001
        logger.exception("Messbasis %s nicht lesbar (%s)", name, datei)
    _MESSBASIS_ZWISCHEN[name] = aus
    return aus


class MarktrangUnbekannt(RuntimeError):
    """Lieber keine Zahl als eine erfundene."""


def _hole(url: str, zeitsperre: int = ZEITSPERRE):
    r = urllib.request.Request(url, headers=KOPF)
    with urllib.request.urlopen(r, timeout=zeitsperre) as antwort:
        return json.loads(antwort.read().decode("utf-8"))


def _rang(werte: dict) -> dict:
    """{symbol: wert} -> {symbol: Rangplatz 0.0 bis 1.0}.

    0.0 ist der niedrigste Wert, 1.0 der hoechste. Bindungen bekommen
    aufsteigende Plaetze - bei stetigen Groessen praktisch nie relevant.
    """
    if len(werte) < 2:
        return {}
    sortiert = sorted(werte.items(), key=lambda x: x[1])
    n = len(sortiert) - 1
    return {sym: i / n for i, (sym, _w) in enumerate(sortiert)}


def _fuenftel(rang: float | None) -> int | None:
    """0 bis 4. `None` bleibt `None` - nie 0."""
    if rang is None:
        return None
    return min(int(rang * 5), 4)


def funding_werte(symbole=None) -> dict:
    """Aktuelle Funding-Rate JE MARKTSYMBOL, aus EINEM Aufruf.

    ⚠️ Nur PERPETUAL. Quartalskontrakte (`BTCUSDT_261225`) haben keine
    Funding-Rate; wer sie mitnimmt, verliert ausgerechnet BTC und ETH still
    (Fehler vom 30.08.2026).

    ⚠️⚠️ LIEFERT DEN GANZEN MARKT, NICHT UNSERE AUSWAHL (31.08.2026).
    Bis heute filterte diese Funktion auf die uebergebenen Symbole, und
    `raenge()` bildete den Rang IN DIESER MENGE. Das weicht von der
    Messung ab: `rechne_funding_beitrag.py` rangt je Kalendertag ueber
    ALLE verfuegbaren Symbole (bis zu 290). Ein Rang ueber 43 Watchlist-
    Werte ist eine andere Groesse als der gemessene - derselbe Fehlertyp,
    an dem H gescheitert ist (Messung und Anwendung liefen auseinander).

    Nutzervorgabe 31.08., die es entscheidet: *"ein neutraler Trade ist
    unabhaengig von der Wirtschaftlichkeit und Anzahl der Assets zu
    bewerten."* Ob ein Wert heute guenstiges Funding hat, haengt nicht
    davon ab, wie viele Werte wir beobachten.

    `symbole` wird nur noch als Filter fuer die RUECKGABE gebraucht - der
    Rang entsteht vorher, ueber den Markt.
    """
    aus = {}
    for e in _hole(PREMIUM_INDEX):
        paar = str(e.get("symbol") or "")
        if not paar.endswith("USDT") or "_" in paar:
            continue
        rate = e.get("lastFundingRate")
        if rate not in (None, ""):
            aus[paar[:-4]] = float(rate)
    return aus


def _coingecko_namen() -> dict:
    """{coingecko_id: unser Symbol} - fuer Werte mit abweichendem Kuerzel.

    ⚠️ CANTON WAR DER ANLASS (31.08.2026, vom Nutzer vermutet und
    bestaetigt): CoinGecko fuehrt `canton-network` unter dem Symbol
    **CC**, unsere Watchlist unter `CANTON`. Der Abgleich lief ueber das
    CoinGecko-Symbol - CANTON konnte deshalb NIE gefunden werden, und
    zwar lautlos.

    Die `coingecko_id` steht in der Watchlist und ist eindeutig. Ueber
    sie abzugleichen ist der richtige Weg; das Symbol ist nur ein Kuerzel
    und kollidiert (es gibt mehrere `CC`).
    """
    aus = {}
    try:
        import config as _config
        for a in _config.get_watchlist():
            kid = getattr(a, "coingecko_id", None)
            sym = getattr(a, "symbol", None)
            if kid and sym:
                aus[str(kid).lower()] = str(sym).upper()
    except Exception:                                        # noqa: BLE001
        logger.exception("Marktrang: Watchlist fuer den ID-Abgleich fehlt")
    return aus


def turnover_werte(symbole=None) -> dict:
    """Handelsvolumen je Umlaufmenge, fuer den GANZEN Markt.

    ⚠️ Wie `funding_werte`: der Rang gehoert ueber den Markt gebildet,
    nicht ueber unsere Auswahl (31.08.2026).
    """
    namen = _coingecko_namen()
    aus = {}
    for e in _hole(COINGECKO_MARKETS):
        # ⚠️ ERST UEBER DIE ID, dann ueber das Symbol - siehe CANTON.
        basis = namen.get(str(e.get("id") or "").lower())             or str(e.get("symbol") or "").upper()
        menge = e.get("circulating_supply")
        volumen = e.get("total_volume")
        preis = e.get("current_price")
        if basis and menge and volumen and preis and menge > 0 and preis > 0:
            aus[basis] = float(volumen) / float(preis) / float(menge)
    return aus


def raenge(symbole, *, mit_turnover: bool = True) -> dict:
    """Je Symbol der Querschnittsrang beider Groessen.

    Rueckgabe je Symbol:
        {"funding": Rohwert oder None, "funding_rang": 0..1 oder None,
         "funding_fuenftel": 0..4 oder None, ... dito turnover ...,
         "querschnitt": Zahl der Symbole, aus denen der Rang gebildet wurde}

    ⚠️ Wirft NICHT bei Netzwerkfehlern - eine fehlende Zahl ist `None`, und
    die Kette laeuft weiter. Eine Bewertung, die den ganzen Lauf abbricht,
    waere schlimmer als eine, die an diesem Tag schweigt.
    """
    symbole = [str(s).upper() for s in symbole]
    ergebnis = {s: {"funding": None, "funding_rang": None,
                    "funding_fuenftel": None, "turnover": None,
                    "turnover_rang": None, "turnover_fuenftel": None,
                    "querschnitt_funding": 0, "querschnitt_turnover": 0,
                    # ⚠️ NUR ANZEIGE, NIE BEWERTUNG - siehe unten.
                    "schnitt": None, "schnitt_rang": None,
                    "schnitt_fuenftel": None, "querschnitt_schnitt": 0,
                    "funding_platz": None, "turnover_platz": None,
                    "schnitt_platz": None, "platz_von": 0}
                for s in symbole}

    # ⚠️ FUENFTEL 0 IST BEI ALLEN DREI DAS "GUTE" ENDE - aber aus
    # verschiedenen Gruenden: wenig Funding = wenig Ueberhitzung, wenig
    # Umschlag = wenig Aufmerksamkeit, TIEF unter dem Schnitt = Rueckkehr
    # zum Mittel. `_rang` sortiert aufsteigend, das passt fuer alle drei.
    for name, holen, an in (("funding", funding_werte, True),
                            ("turnover", turnover_werte, mit_turnover),
                            ("schnitt", schnitt_werte, True)):
        if not an:
            continue
        try:
            roh = holen()            # der ganze Markt, aus EINEM Aufruf
        except Exception:                                    # noqa: BLE001
            logger.exception("Marktrang: %s nicht abrufbar", name)
            continue
        # ⚠️ AUF DIE MESSBASIS EINGRENZEN - siehe den Block bei MESSBASIS.
        basis = messbasis(name)
        if not basis:
            logger.error("Marktrang: %s uebersprungen - Messbasis nicht "
                         "lesbar. Ein Rang ueber die falsche Menge saehe "
                         "aus wie ein richtiger.", name)
            continue
        werte = {s_: w for s_, w in roh.items() if s_ in basis}
        if len(werte) < MINDEST_QUERSCHNITT:
            logger.info("Marktrang: %s uebersprungen - nur %d Werte, "
                        "Mindestquerschnitt %d", name, len(werte),
                        MINDEST_QUERSCHNITT)
            continue
        # ⚠️ DER RANG ENTSTEHT UEBER DEN MARKT, ABGELESEN WIRD ER FUER UNS.
        # Frueher stand hier der Rang INNERHALB der uebergebenen Symbole -
        # damit haette dieselbe Lage bei 43 Werten ein anderes Fuenftel
        # ergeben als bei 5, und bei 2 Werten gar keines.
        rang = _rang(werte)
        for sym in symbole:
            if sym not in werte:
                continue
            ergebnis[sym][name] = werte[sym]
            ergebnis[sym][name + "_rang"] = rang.get(sym)
            ergebnis[sym][name + "_fuenftel"] = _fuenftel(rang.get(sym))
        for sym in symbole:
            ergebnis[sym]["querschnitt_" + name] = len(werte)

        # ---- DER PLATZ IN DER EIGENEN LISTE - NUR ZUR ANZEIGE ----------
        #
        # Nutzerwunsch 31.08.: *"ein Ranking innerhalb meiner Watchlist ist
        # fuer mich hilfreich."*
        #
        # ⚠️⚠️ DIESER PLATZ DARF NIE IN DIE BEWERTUNG. Er haengt an der
        # Zahl der beobachteten Werte - bei 43 Symbolen bedeutet "Platz 3"
        # etwas anderes als bei 5, und bei 2 gar nichts. Genau deshalb
        # rangt die Bewertung ueber den MARKT (`*_fuenftel`, 837 bzw. 232
        # Werte). Der Platz hier beantwortet eine andere Frage: "welcher
        # MEINER Werte steht heute am guenstigsten" - eine Auskunft, keine
        # Groesse.
        #
        # Die Trennung ist die Lehre aus H: was gemessen wurde, muss auch
        # angewandt werden - und was NICHT gemessen wurde, darf nicht
        # aussehen, als waere es dasselbe.
        eigene = {s: werte[s] for s in symbole if s in werte}
        if len(eigene) >= 2:
            for platz, (sym, _w) in enumerate(
                    sorted(eigene.items(), key=lambda x: x[1]), start=1):
                ergebnis[sym][name + "_platz"] = platz
            for sym in symbole:
                ergebnis[sym]["platz_von"] = len(eigene)
    return ergebnis


def saetze(eintrag: dict | None) -> list[str]:
    """Zeilen fuer die Mail - Tatsache, keine Empfehlung.

    ⚠️ SAGT AUCH, WENN NICHTS VORLIEGT (31.08.2026). Die Kettensimulation
    zeigte einen Lauf, in dem das Signalsymbol (ASTER) in keiner Messbasis
    steht: kein Funding-Rang, kein Turnover-Rang - und die Mail schwieg
    dazu. Der Leser sah ein Signal, dessen Bewertung auf NULL gemessenen
    Beitraegen stand, ohne es erfahren zu koennen.

    Das ist dieselbe Unterscheidung wie bei `null` gegen `nie`: "geprueft
    und niedrig" und "gar nicht bestimmbar" sehen in einer schweigenden
    Mail gleich aus.
    """
    if not eintrag:
        return []
    zeilen = []
    if (eintrag.get("funding_fuenftel") is None
            and eintrag.get("turnover_fuenftel") is None
            and eintrag.get("schnitt_fuenftel") is None):
        return ["Marktvergleich: fuer diesen Wert liegt keiner vor - er "
                "gehoert weder zur Funding- noch zur Umschlag-Messbasis "
                "(%d bzw. %d Werte). Die beiden gemessenen Beitraege "
                "tragen hier also NICHTS bei; die Bewertung steht allein "
                "auf der Geometrie."
                % (eintrag.get("querschnitt_funding") or 0,
                   eintrag.get("querschnitt_turnover") or 0)]
    f = eintrag.get("funding_fuenftel")
    if f is not None:
        lage = {0: "das niedrigste", 1: "ein niedriges", 2: "ein mittleres",
                3: "ein erhoehtes", 4: "das hoechste"}[f]
        zeilen.append(
            "Finanzierung: %s Fuenftel im Marktvergleich (%d Werte). "
            "Hohe Finanzierungskosten zeigen viele Long-Positionen an; "
            "gemessen liefen solche Werte schlechter."
            % (lage, eintrag.get("querschnitt_funding") or 0))
    sc = eintrag.get("schnitt_fuenftel")
    if sc is not None:
        lage = {0: "am tiefsten", 1: "tief", 2: "mittig",
                3: "erhoeht", 4: "am hoechsten"}[sc]
        zeilen.append(
            "Abstand zum eigenen 200-Tage-Schnitt: %s im Marktvergleich "
            "(%d Werte). Gemessen liefen Werte tief unter ihrem Schnitt "
            "besser als solche weit darueber."
            % (lage, eintrag.get("querschnitt_schnitt") or 0))
    t = eintrag.get("turnover_fuenftel")
    if t is not None:
        lage = {0: "das niedrigste", 1: "ein niedriges", 2: "ein mittleres",
                3: "ein erhoehtes", 4: "das hoechste"}[t]
        zeilen.append(
            "Umschlag: %s Fuenftel im Marktvergleich (%d Werte). "
            "Viel Umschlag je Umlaufmenge bedeutet viel Aufmerksamkeit."
            % (lage, eintrag.get("querschnitt_turnover") or 0))

    # ---- DER PLATZ IN DER EIGENEN LISTE (Nutzerwunsch 31.08.) ----------
    #
    # ⚠️ ALS EIGENE ZEILE UND MIT EIGENEM WORT ("Platz", nicht "Fuenftel"),
    # damit beim Lesen nicht verschwimmt, was in die Bewertung eingeht.
    # Die Fuenftel oben stammen aus dem Marktvergleich und sind gemessen;
    # der Platz hier ist eine Auskunft ueber die eigene Liste.
    von = eintrag.get("platz_von") or 0
    # ⚠️ "guenstigste Finanzierung auf Platz 15" LAS SICH WIDERSPRUECHLICH.
    # Platz 1 ist der guenstigste; die Eigenschaft gehoert an die Reihung,
    # nicht an den Platz.
    plaetze = [("Finanzierung", eintrag.get("funding_platz")),
               ("Umschlag", eintrag.get("turnover_platz")),
               ("Abstand zum Schnitt", eintrag.get("schnitt_platz"))]
    teile = ["%s Platz %d" % (was, p) for was, p in plaetze if p]
    if teile and von >= 2:
        zeilen.append(
            "In deiner Liste (%d Werte, Platz 1 = am guenstigsten): %s. Das "
            "ist eine Auskunft, keine Bewertung - in die Zahl geht der "
            "Marktvergleich oben ein, nicht dieser Platz."
            % (von, ", ".join(teile)))
    return zeilen
