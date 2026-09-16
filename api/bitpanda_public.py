# -*- coding: utf-8 -*-
"""LESENDER ZUGANG ZUR NEUEN BITPANDA-SCHNITTSTELLE (Schritt 61, Stufe 1.1).

⚠️⚠️ WARUM ES DIESES MODUL GIBT. `api/bitpanda.py` spricht die ALTE
Schnittstelle `api.bitpanda.com/v1` (abgekuendigt, Befund 2.455-cash-messbar).
Sie zeigt gestaktes Guthaben nicht, kennt gebundenes Cash nicht und zwingt zu
einer Rekonstruktion aus Transfer-Markierungen - die Quelle der Doppelzaehlung
(2.455-bitpanda-staking-ursache). Der Nachfolger `api.public.bitpanda.com/v1`
liefert beides direkt.

⚠️⚠️⚠️ DIESES MODUL SCHREIBT KEINEN BESTAND. Es liest, nichts weiter. Der
Umbau des Abgleichs ist Stufe 1.2 - bis dahin laeuft der Betrieb unveraendert
ueber die alte Anbindung. Einzige Ausnahme: der KATALOG wird in der Datenbank
gepuffert (`bitpanda_katalog`), weil ein Abruf 140 Seiten kostet.

DIE DREI EIGENHEITEN DER SCHNITTSTELLE, live gemessen am 15./16.09.2026:

  1  DER CURSOR DER BUCHUNGSLISTE IST DEFEKT. `/operations` liefert zwar
     `next_cursor`, ignoriert ihn aber - jede Folgeseite ist wieder Seite 1
     (`cursor`, `page_cursor`, `after`: alle wirkungslos). Vollstaendig wird
     die Liste nur ueber DATUMSFENSTER: `to` auf den aeltesten Zeitpunkt der
     letzten Seite setzen und weiterwandern. `from` funktioniert und begrenzt
     nach unten - damit laeuft der inkrementelle Abruf.
  2  DER KATALOG-CURSOR FUNKTIONIERT (`/assets`, `next_cursor` +
     `has_next_page`, 141 Seiten, 14.052 Eintraege).
  3  DER SCHLUESSEL STEHT IM HEADER (`X-Api-Key`), nicht in der URL. Ein
     falscher Schluessel gibt 401 mit ,Credentials / Access token wrong'.

MASKIERUNG. `geheimnisse.maskiere` entfernt Schluessel aus URL-PARAMETERN -
hier steht keiner in der URL, trotzdem geht JEDE Fehlermeldung zusaetzlich
durch `_ohne_schluessel()`: taucht der Schluesselwert je in einem Text auf
(fremde Fehlermeldung, Antwortkoerper), ist er weg, bevor er ins Log oder in
die Ampel geraet.

ZEITLIMIT UND AMPEL. Jede Anfrage hat ein eigenes Zeitlimit, der Buchungslauf
zusaetzlich eine Gesamtfrist - ein haengender Abruf darf keinen Job blockieren
(dieselbe Lehre wie bei yfinance). Jeder Netzabruf laeuft unter
`track_api_health("bitpanda_public")`, damit die Ampel ihn sieht.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import requests

from database.api_health import track_api_health
from geheimnisse import maskiere

logger = logging.getLogger(__name__)

BASIS_URL = "https://api.public.bitpanda.com/v1"
# Der EUR-Bezug fuer `/portfolio` (Bitpandas eigene Waehrungskennung, live geprueft).
EUR_WAEHRUNG_ID = "b88b8466-efe3-11eb-b56f-0691764446a7"
ZEITLIMIT_SEKUNDEN = 20
# Gesamtfrist fuer einen Buchungslauf. Die volle Historie (7.859 Vorgaenge,
# 79 Fenster) brauchte live rund 40 Sekunden; 300 lassen Luft fuer einen
# langsamen Tag, ohne einen Job festzuhalten.
GESAMTFRIST_BUCHUNGEN_SEKUNDEN = 300
SEITENGROESSE = 100
MAX_VERSUCHE = 5
# Notbremse gegen eine Endlosschleife, falls die Schnittstelle ein Fenster
# nicht respektiert: mehr Fenster als das kann eine Historie nicht brauchen.
MAX_FENSTER = 2000
KATALOG_MAX_SEITEN = 400
# Wie lange ein gepufferter Katalog gilt. Neue Werte kommen selten dazu,
# ein Abruf kostet 141 Seiten - einmal am Tag reicht.
KATALOG_HOECHSTALTER_STUNDEN = 24

# Wallet-Arten der Schnittstelle (`wallet_owner`), live gesehen.
WALLET_SPOT = "shared-default"
WALLET_STAKING = "staking-service"
WALLET_HEBEL = ("margin-trading", "margin-trading-credit")
WALLET_BOERSE = "stock-exchange"
WALLET_ADVANCED = "advanced-trading"


class BitpandaPublicFehler(RuntimeError):
    """Fehler beim Lesen - Text bereits maskiert."""


@dataclass(frozen=True)
class KatalogEintrag:
    asset_id: str
    symbol: str
    name: str
    gruppe: str
    isin: str | None = None


@dataclass(frozen=True)
class Position:
    """Eine Position aus `/portfolio` - Mengen, nicht Bewertungen.

    `menge_verfuegbar` ist der frei handelbare Teil, `menge_gesamt` alles
    zusammen; die Differenz liegt in Staking- oder Hebel-Wallets. WELCHE es
    sind, sagt erst die Wallet-Aufteilung aus den Buchungen (Stufe 1.2) -
    deshalb steht hier bewusst keine Zahl namens ,gestakt'."""
    asset_id: str
    symbol: str | None
    name: str | None
    gruppe: str | None
    menge_gesamt: float
    menge_verfuegbar: float
    wert_eur: float | None
    einstand_bp_eur: float | None
    investiert_bp_eur: float | None


def _ohne_schluessel(text, api_key: str | None) -> str:
    """Der Schluesselwert selbst raus, danach die uebliche URL-Maskierung."""
    t = str(text)
    if api_key:
        t = t.replace(api_key, "***")
    return maskiere(t)


def _zahl(wert) -> float | None:
    """`{"value": "1.23"}` oder "1.23" oder None -> float oder None."""
    if isinstance(wert, dict):
        wert = wert.get("value")
    if wert is None:
        return None
    try:
        return float(wert)
    except (TypeError, ValueError):
        return None


@track_api_health("bitpanda_public")
def _hole(pfad: str, api_key: str, params: dict | None = None) -> dict:
    """Ein Abruf mit Zeitlimit und 429-Geduld. Wirft `BitpandaPublicFehler`.

    ⚠️ 429 IST KEIN AUSFALL, sondern die Bitte zu warten - deshalb Wiederholung
    statt Fehler. `Retry-After` wird beachtet, wenn die Antwort ihn nennt."""
    letzter = ""
    for versuch in range(MAX_VERSUCHE):
        try:
            antwort = requests.get(BASIS_URL + pfad, headers={"X-Api-Key": api_key},
                                   params=params or {}, timeout=ZEITLIMIT_SEKUNDEN)
        except requests.RequestException as exc:
            letzter = _ohne_schluessel(exc, api_key)
            raise BitpandaPublicFehler("%s nicht erreichbar: %s" % (pfad, letzter)) from None
        if antwort.status_code == 429:
            warte = float(antwort.headers.get("Retry-After") or 5)
            logger.info("Bitpanda (neu) %s: Taktgrenze erreicht, warte %.0f s", pfad, warte)
            time.sleep(min(warte, 30.0))
            letzter = "429"
            continue
        if antwort.status_code == 401:
            # Eigener, eindeutiger Text: die Schluesselueberwachung (1.7) haengt daran.
            raise BitpandaPublicFehler(
                "Zugang abgelehnt (401) - der Bitpanda-Schluessel ist ungueltig oder abgelaufen")
        if antwort.status_code >= 400:
            raise BitpandaPublicFehler("%s antwortete %d: %s"
                                       % (pfad, antwort.status_code,
                                          _ohne_schluessel(antwort.text[:200], api_key)))
        try:
            return antwort.json()
        except ValueError:
            raise BitpandaPublicFehler("%s lieferte keine lesbare Antwort" % pfad) from None
    raise BitpandaPublicFehler("%s antwortet dauerhaft mit der Taktgrenze (%s)" % (pfad, letzter))


def hole_katalog(api_key: str) -> list[KatalogEintrag]:
    """Der volle Katalog ueber die Cursor-Seiten (141 Seiten, ~14.000 Eintraege).

    ⚠️ HIER FUNKTIONIERT DER CURSOR - anders als bei den Buchungen. Abbruch,
    sobald `has_next_page` falsch ist oder der Cursor stehenbleibt."""
    aus: dict[str, KatalogEintrag] = {}
    cursor = None
    for _ in range(KATALOG_MAX_SEITEN):
        params = {"page_size": SEITENGROESSE}
        if cursor:
            params["cursor"] = cursor
        js = _hole("/assets", api_key, params)
        for e in js.get("data") or []:
            if not e.get("id") or not e.get("symbol"):
                continue
            aus[e["id"]] = KatalogEintrag(asset_id=e["id"], symbol=e["symbol"],
                                          name=e.get("name") or "", gruppe=e.get("group") or "",
                                          isin=e.get("isin"))
        neuer = js.get("next_cursor")
        if not js.get("has_next_page") or not neuer or neuer == cursor:
            break
        cursor = neuer
    return list(aus.values())


def katalog(conn, api_key: str, jetzt: datetime | None = None,
            hoechstalter_stunden: float = KATALOG_HOECHSTALTER_STUNDEN) -> dict[str, KatalogEintrag]:
    """asset_id -> Eintrag, aus der Datenbank; aelter als einen Tag wird geholt.

    ⚠️ BEI EINEM FEHLSCHLAG GILT DER ALTE STAND WEITER (P-10): ein Katalog von
    gestern ist unendlich viel besser als keiner - er aendert sich kaum. Nur
    wenn GAR KEINER da ist, faellt der Fehler durch."""
    import database.db as db

    jetzt = jetzt or datetime.now(timezone.utc)
    gepuffert = db.lade_bitpanda_katalog(conn)
    stand = db.bitpanda_katalog_stand(conn)
    alt = True
    if stand:
        try:
            alt = (jetzt - datetime.fromisoformat(stand)).total_seconds() > hoechstalter_stunden * 3600
        except ValueError:
            alt = True
    if gepuffert and not alt:
        return gepuffert
    try:
        frisch = hole_katalog(api_key)
    except BitpandaPublicFehler as exc:
        if gepuffert:
            logger.warning("Bitpanda-Katalog nicht abrufbar (%s) - der Stand vom %s gilt weiter",
                           exc, stand)
            return gepuffert
        raise
    db.speichere_bitpanda_katalog(conn, frisch, jetzt.isoformat())
    logger.info("Bitpanda-Katalog (neu) geholt: %d Eintraege", len(frisch))
    return {e.asset_id: e for e in frisch}


def hole_portfolio(api_key: str, katalog_eintraege: dict[str, KatalogEintrag] | None = None) -> list[Position]:
    """Alle Positionen mit Menge gesamt und verfuegbar, EUR-Wert und Bitpandas
    eigenem Durchschnittspreis.

    ⚠️ `average_buy_price` IST KEIN EINSTAND in unserem Sinn: es ist rechnerisch
    `invested_amount / balance`, und `invested_amount` sinkt bei Verkauf oder
    Tausch nicht (Befund 2.455-einstand-veraltet). Deshalb heissen die Felder
    hier `..._bp_...` - sie taugen als Gegenprobe, nicht als Wahrheit."""
    js = _hole("/portfolio", api_key, {"equivalent_currency_id": EUR_WAEHRUNG_ID})
    kat = katalog_eintraege or {}
    aus = []
    for p in js.get("data") or []:
        aid = p.get("asset_id")
        if not aid:
            continue                       # Fiat-Zeilen tragen `currency_id`
        e = kat.get(aid)
        gesamt = _zahl(p.get("balance")) or 0.0
        aus.append(Position(
            asset_id=aid, symbol=e.symbol if e else None, name=e.name if e else None,
            gruppe=e.gruppe if e else None, menge_gesamt=gesamt,
            menge_verfuegbar=_zahl(p.get("available_balance")) or 0.0,
            wert_eur=_zahl(p.get("currency_balance")),
            einstand_bp_eur=_zahl(p.get("average_buy_price")),
            investiert_bp_eur=_zahl(p.get("invested_amount"))))
    return aus


def hole_fiat(api_key: str) -> dict:
    """Fiat-Zeilen aus `/portfolio`: {Waehrungskennung: (gesamt, verfuegbar)}.

    Die EUR-Zeile traegt `currency_id` statt `asset_id`; die Differenz zwischen
    gesamt und verfuegbar ist in offenen Orders gebunden (Befund
    2.455-cash-gesperrt: 3.000 von 3.667 EUR)."""
    js = _hole("/portfolio", api_key, {"equivalent_currency_id": EUR_WAEHRUNG_ID})
    aus = {}
    for p in js.get("data") or []:
        cid = p.get("currency_id")
        if cid and not p.get("asset_id"):
            aus[cid] = (_zahl(p.get("balance")) or 0.0, _zahl(p.get("available_balance")) or 0.0)
    return aus


def _aeltester_zeitpunkt(vorgaenge: list) -> str | None:
    zeiten = [t.get("credited_at") for o in vorgaenge for t in (o.get("transactions") or [])
              if t.get("credited_at")]
    return min(zeiten) if zeiten else None


def _eine_millisekunde_zurueck(zeitpunkt: str) -> str:
    z = datetime.fromisoformat(zeitpunkt.replace("Z", "+00:00")) - timedelta(milliseconds=1)
    return z.isoformat().replace("+00:00", "Z")


def hole_buchungen(api_key: str, seit: str | None = None, jetzt=None,
                   frist_sekunden: float = GESAMTFRIST_BUCHUNGEN_SEKUNDEN) -> list[dict]:
    """Alle Vorgaenge (neueste zuerst), notfalls ab `seit` (ISO-Zeitpunkt).

    ⚠️⚠️ UEBER DATUMSFENSTER, NICHT UEBER DEN CURSOR (Befund
    2.455-bitpanda-stufe0): `to` wandert auf den aeltesten Zeitpunkt der
    letzten Seite. Liefert ein Fenster nichts Neues (alle Vorgaenge tragen
    denselben Zeitpunkt), geht die Grenze eine Millisekunde zurueck - sonst
    stuende der Lauf.

    `seit` setzt zusaetzlich `from`; der inkrementelle Lauf holt damit nur
    Neues. Die Gesamtfrist bricht ab, bevor ein Job haengt - dann kommt, was
    da ist, und der Aufrufer sieht es an der Anzahl."""
    ende = (jetzt or time.monotonic) if callable(jetzt) else None
    start = (ende() if ende else time.monotonic())
    vorgaenge: dict[str, dict] = {}
    bis = None
    for _ in range(MAX_FENSTER):
        params = {"page_size": SEITENGROESSE}
        if seit:
            params["from"] = seit
        if bis:
            params["to"] = bis
        js = _hole("/operations", api_key, params)
        seite = js.get("data") or []
        neu = 0
        for o in seite:
            kennung = o.get("operation_id")
            if kennung and kennung not in vorgaenge:
                vorgaenge[kennung] = o
                neu += 1
        aeltest = _aeltester_zeitpunkt(seite)
        if not seite or not aeltest:
            break
        if neu == 0:
            # ⚠️ DIE EINE GRENZE DIESES VERFAHRENS, sichtbar statt still: traegt
            # eine VOLLE Seite denselben Zeitpunkt, springt die Grenze an ihm
            # vorbei - Vorgaenge dieser Millisekunde koennten fehlen. Live
            # gemessen (16.09.2026, volle Historie): 7.873 Vorgaenge, 7.873
            # verschiedene Zeitstempel, groesste Haeufung in einer SEKUNDE 17.
            # Der Fall ist also fern, aber er waere sonst nicht zu erkennen.
            if len(seite) >= SEITENGROESSE:
                logger.warning(
                    "Bitpanda-Buchungen: eine volle Seite traegt denselben Zeitpunkt (%s) - "
                    "beim Weiterwandern koennen Vorgaenge dieser Millisekunde fehlen", aeltest)
            aeltest = _eine_millisekunde_zurueck(aeltest)
        if aeltest == bis:
            break
        bis = aeltest
        jetzt_s = ende() if ende else time.monotonic()
        if jetzt_s - start > frist_sekunden:
            logger.warning("Bitpanda-Buchungen: Frist von %.0f s erreicht - %d Vorgaenge geladen, "
                           "aeltester Stand %s", frist_sekunden, len(vorgaenge), bis)
            break
    return sorted(vorgaenge.values(),
                  key=lambda o: _aeltester_zeitpunkt([o]) or "", reverse=True)
