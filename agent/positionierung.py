# -*- coding: utf-8 -*-
"""Die Fakten, die der Trader NICHT sieht - Grundlage der Rolle G (16.08.2026).

WOZU. Die zweite Stufe bekam bisher denselben Faktentext wie Rolle BC und
beantwortete dieselbe Frage. Nach der Literatur ist das der Fehlerfall
(*Homogeneous Debate*): teilen zwei Pruefer Modell und Informationsgrenze,
sinkt die epistemische Vielfalt, und das zweite Modell rationalisiert
nachtraeglich statt unabhaengig zu pruefen.

    Gemessen an unseren eigenen Daten: 17x LONG in 2.469 Pruefungen.
    SHORT 1.246, NEUTRAL 1.206. Ein Merkmal, das fast immer denselben Wert
    hat, kann nichts unterscheiden (R-T6).

DIE KONSTRUKTIONSBEDINGUNG. Ein Parameter gehoert zu GENAU EINEM Modell. Was
hier steht, darf NICHT in den Faktentext von BC - sonst ist die zweite Stufe
wieder das, was sie war.

    LLM1 (Rolle BC)  was aus Kursreihe und Depot folgt
    LLM2 (Rolle G)   was AUSSERHALB davon liegt - Positionierung

WAS HIER STEHT UND WAS NICHT. Positionierung heisst: wie sind die anderen
aufgestellt. Open Interest, Finanzierungsrate als Extremwert, Anteil der
Long-Konten. Das ist keine zweite Lesart des Charts - es ist eine Information,
die im Chart nicht steht.

NICHT hier: Nachrichten und Termine. Sie gehoeren ebenfalls zu Rolle G, sind
aber eine eigene Quelle und ein eigenes Vorhaben (Phase IV).

ALLE SAETZE MIT BEZUG, KEINE NACKTE ZAHL. Dieselbe Regel wie in
`lagebeschreibung.py`, und aus demselben Grund: eine Zahl ohne Massstab wird
zertokenisiert und traegt nicht. Die Bestandserhebung vom 16.08. hat fuer die
bestehenden Bloecke 41 Saetze geprueft - keiner trug eine nackte Zahl. Dieser
Block haelt denselben Stand.
"""
from __future__ import annotations

import logging
import sqlite3
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Wie weit zurueck der Open-Interest-Vergleich reicht. Dieselbe Groesse, die
# `hebel_screening.cfg["oi_lookback_stunden"]` benutzt - dort steht sie als
# Konfiguration, hier als Vorgabe, falls sie nicht lesbar ist.
OI_RUECKBLICK_STUNDEN = 8.0

# Ab wann eine Finanzierungsrate als extrem gilt. NICHT frei gesetzt: es ist
# das Perzentil der EIGENEN Historie, und 90/10 ist die uebliche Grenze fuer
# "aussergewoehnlich" - dieselbe, die `atr_percentile` im Projekt verwendet.
EXTREM_OBEN, EXTREM_UNTEN = 90, 10


def _reihe(conn, symbol: str, spalte: str, grenze: int = 400,
           boerse: str = "binance") -> list:
    try:
        return [r[0] for r in conn.execute(
            f"SELECT {spalte} FROM open_interest_snapshot "
            "WHERE symbol = ? AND exchange = ? "
            f"AND {spalte} IS NOT NULL "
            "ORDER BY fetched_at DESC LIMIT ?", (symbol, boerse, grenze))]
    except sqlite3.Error as exc:
        logger.info("Positionierung %s/%s nicht lesbar: %s", symbol, spalte, exc)
        return []


# --- DIE BOERSEN LAUFEN AUSEINANDER (16.08.2026) ---------------------------
#
# WARUM DAS UEBERHAUPT EIN FAKT IST. Bis heute las diese Datei nur Binance -
# `exchange = 'binance'` stand fest in der Abfrage. In derselben Tabelle liegen
# bybit (40.177 Zeilen) und okx (36.681), seit Monaten, kostenlos, vom
# Hebel-Screening mitgeschrieben.
#
# ⚠️ ABER NUR BEIM OPEN INTEREST IST ES EINE ZWEITE ERHEBUNG. Nachgezaehlt am
# Produktionsbestand:
#
#     long_account_pct   41.547 gemeinsame Zeitpunkte, davon 0 verschieden
#     funding_rate       40.033 gemeinsame Zeitpunkte, davon 0 verschieden
#     open_interest      41.551 gemeinsame Zeitpunkte, davon ALLE verschieden
#
# `hebel_screening._hole_und_speichere` holt die Finanzierungsrate EINMAL bei
# Kraken und den Long-Anteil EINMAL bei Binance, schreibt aber beide in alle
# drei Boersenzeilen. Zwei von drei Feldern sind Kopien unter fremdem Etikett.
# Deshalb wird hier AUSSCHLIESSLICH das Open Interest boersenweise gelesen.
#
# UND DIE STUFE HAT SICH GELOHNT: gemessen ueber 8.087 gepaarte Zeitpunkte und
# 22 Symbole betraegt die Spanne der 8-Stunden-Aenderung im Median 3,0
# Prozentpunkte, im 90. Perzentil 10,9. In 85 % der Faelle ist sie groesser als
# ein Punkt. Ein konstantes Feld (R-T6) ist das nicht.
#
# NUR AENDERUNGEN, NIE NIVEAUS. Binance fuehrt ein Vielfaches der Kontrakte von
# OKX; die absoluten Staende zu vergleichen hiesse, Boersengroessen zu messen
# statt Verhalten. Erst die prozentuale Veraenderung ueber dasselbe Fenster ist
# vergleichbar - R-T5 in seiner urspruenglichen Form.
BOERSEN = ("binance", "bybit", "okx")

# AUF MODULEBENE, NICHT IM SATZBAU. Eine Zuordnung, die in der Funktion
# entsteht, ist genau die Stelle, an der dieses Projekt schon dreimal einen
# freien Namen erzeugt hat - zuletzt `assetklasse`, zwei Vormittage.
_BOERSENNAME = {"binance": "Binance", "bybit": "Bybit", "okx": "OKX"}

# Wie viele gemeinsame Zeitpunkte mindestens vorliegen muessen, damit die
# Spanne ein Perzentil bekommt. Unter dieser Grenze steht eine Zahl ohne
# Massstab - und die traegt nach R-T1 nicht.
MINDEST_HISTORIE_DIVERGENZ = 40


def _oi_je_boerse(conn, symbol: str, grenze: int = 400) -> dict:
    """{boerse: {zeitpunkt: open_interest}} - nur Boersen mit genug Reihe."""
    aus: dict = {}
    for b in BOERSEN:
        try:
            zeilen = conn.execute(
                "SELECT fetched_at, open_interest FROM open_interest_snapshot "
                "WHERE symbol = ? AND exchange = ? AND open_interest IS NOT NULL "
                "ORDER BY fetched_at DESC LIMIT ?", (symbol, b, grenze)).fetchall()
        except sqlite3.Error as exc:
            logger.info("Positionierung %s/%s nicht lesbar: %s", symbol, b, exc)
            continue
        if len(zeilen) > MINDEST_HISTORIE_DIVERGENZ:
            aus[b] = {str(t): float(v) for t, v in zeilen}
    return aus


def _divergenz(conn, symbol: str) -> dict | None:
    """Wie weit laufen die Boersen beim Open Interest auseinander?

    GEPAART AUF DENSELBEN ZEITPUNKTEN. Das Screening schreibt alle drei
    Boersen mit demselben `fetched_at`, ein Schnitt der Zeitschluessel ist
    also verlustarm - und er verhindert, dass ein verpasster Abruf als
    Meinungsunterschied erscheint."""
    reihen = _oi_je_boerse(conn, symbol)
    if len(reihen) < 2:
        return None
    zeiten = sorted(set.intersection(*(set(d) for d in reihen.values())),
                    reverse=True)
    schritte = int(OI_RUECKBLICK_STUNDEN * 4)
    if len(zeiten) <= schritte + MINDEST_HISTORIE_DIVERGENZ:
        return None

    spannen: list[float] = []
    jetzt: dict = {}
    for i in range(len(zeiten) - schritte):
        aend = {}
        for b, d in reihen.items():
            alt = d[zeiten[i + schritte]]
            if alt:
                aend[b] = 100.0 * (d[zeiten[i]] - alt) / alt
        if len(aend) < 2:
            continue
        spannen.append(max(aend.values()) - min(aend.values()))
        if not jetzt:                       # i == 0 ist der aktuelle Stand
            jetzt = aend
    if not jetzt or len(spannen) < MINDEST_HISTORIE_DIVERGENZ:
        return None

    hoch = max(jetzt, key=jetzt.get)
    tief = min(jetzt, key=jetzt.get)
    return {"hoch_boerse": hoch, "hoch_pct": round(jetzt[hoch], 1),
            "tief_boerse": tief, "tief_pct": round(jetzt[tief], 1),
            "spanne_pp": round(jetzt[hoch] - jetzt[tief], 1),
            "spanne_perzentil": _perzentil(spannen, spannen[0]),
            "n_boersen": len(jetzt), "n_historie": len(spannen),
            "fenster_stunden": round(schritte / 4.0, 1)}


def _perzentil(werte: list, wert: float) -> int | None:
    """Wo steht dieser Wert in seiner eigenen Geschichte?"""
    if not werte or wert is None:
        return None
    kleiner = sum(1 for w in werte if w < wert)
    return int(round(100.0 * kleiner / len(werte)))


# --- DIE ZWEITE INFORMATIONSART (16.08.2026, Schritt 2) --------------------
#
# WARUM UEBERHAUPT. Rolle G hatte bis heute EINE Quellenart: den Terminmarkt.
# Drei Boersen daraus zu machen (Schritt 1) hat den Fakt verbessert, aber die
# Art nicht vermehrt - offene Kontrakte bleiben offene Kontrakte. R-R3 verlangt
# zwei UNABHAENGIGE Quellen, und unabhaengig heisst: andere Erhebung, andere
# Frage. Boersenzu- und -abfluesse sind gezaehlte Muenzbewegungen auf der Kette,
# kein Positionsstand an einem Terminmarkt.
#
# WARUM DER FLUSS UND NICHT MVRV. Gemessen am 16.08. ueber das letzte Jahr,
# Perzentil im 730-Tage-Fenster:
#
#     Netto-Boersenfluss   Median 47, Streuung 0..99, 97 verschiedene Werte
#     MVRV                 Median  5, Streuung 0..74, 68 % Extremtage
#
# MVRV liegt seit einem Jahr fast durchgehend im untersten Dezil - der Satz
# hiesse fast immer "aussergewoehnlich niedrig". Das ist ein konstantes Feld
# (R-T6), und zwar gemessen statt vermutet. Dazu kommt P3: `regime.py` haelt
# ausdruecklich fest, dass MVRV, Log-Regressions-Risiko und Fear & Greed
# DIESELBE Frage beantworten - und Fear & Greed sieht Rolle A bereits.
#
# ⚠️ ES IST BTC-WEIT, NICHT SYMBOLSPEZIFISCH. Fuer ein SEI-Signal beschreibt es
# den Rahmen, nicht den Wert - dieselbe Begruendung, unter der auch das Regime
# hier steht. G2 (symbolspezifisch) traegt weiterhin der Terminmarkt; dieser
# Fakt erfuellt G1 (zweite Art), nicht G2. Wer beides aus einer Quelle zaehlt,
# taeuscht sich selbst.
#
# WIE LANG DAS FENSTER. 730 Tage - zwei Marktjahre. Kuerzer waere anfaellig fuer
# eine einzelne Phase, laenger wuerde die Halving-Zyklen mischen.
FLUSS_FENSTER_TAGE = 730
FLUSS_MINDESTREIHE = 120

# EIN ABRUF JE TAG, NICHT JE SYMBOL. Rolle G laeuft fuer jedes Signal; der Wert
# gilt fuer den ganzen Kryptomarkt. Ohne diesen Zwischenspeicher holte ein Lauf
# mit zwanzig Signalen zwanzigmal dieselben 800 Zeilen - an einer Schnittstelle
# mit 10 Anfragen je 6 Sekunden.
#
# BEWUSST IM PROZESS UND NICHT IN DER DATENBANK: eine neue Tabelle mitten in
# einer laufenden Messkampagne ist ein Schemaeingriff in die Produktion. Der
# Cache faellt beim Neustart weg, und dann wird einmal neu geholt - das ist
# tragbar. Persistenz steht als offener Punkt im Umbauplan.
_fluss_cache: dict[str, list] = {}

# --- WOHER EINE EXTERNE REIHE KOMMT (16.08.2026, Schritt 3) ----------------
#
# ⚠️ ROLLE G DARF NICHT SCHREIBEN. `zweite_meinung.rolle_g` oeffnet die
# Datenbank mit `mode=ro` - ein Schreibversuch von hier aus scheitert immer.
# Persistenz gehoert deshalb in einen Job (`scheduler/background.py::
# externe_reihen_job`), genau wie `open_interest_snapshot` vom Screening
# geschrieben und hier nur gelesen wird.
#
# DREI STUFEN, IN DIESER REIHENFOLGE:
#   1. DATENBANK - was der Job hinterlegt hat. Der Normalfall im Betrieb.
#   2. PROZESSSPEICHER - fuer Laeufe ohne Job: Simulation, Messskripte, der
#      erste Start nach dem Einspielen.
#   3. NETZ - hoechstens einmal je Prozess und Kalendertag.
#
# OHNE STUFE 1 HAENGT JEDES URTEIL AM NETZ; ohne Stufe 2 holt ein Lauf mit
# zwanzig Signalen zwanzigmal dieselbe Reihe. Stufe 3 ohne die anderen beiden
# waere der Zustand von Schritt 2, den dieser Schritt aufloest.
HOECHSTALTER_REIHE_STUNDEN = 30.0


def _gepflegte_reihe(conn, quelle: str, schluessel: str, holen) -> list:
    """Die Reihe aus der Datenbank, sonst aus dem Speicher, sonst aus dem Netz."""
    from database import db as DB

    if conn is not None:
        alter = DB.alter_externe_reihe(conn, quelle, schluessel)
        if alter is not None and alter <= HOECHSTALTER_REIHE_STUNDEN:
            aus_db = DB.lies_externe_reihe(conn, quelle, schluessel)
            if aus_db:
                return aus_db

    tagesschluessel = f"{quelle}/{schluessel}/{datetime.now(timezone.utc).date()}"
    if tagesschluessel in _fluss_cache:
        return _fluss_cache[tagesschluessel]
    try:
        reihe = holen()
    except Exception as exc:                                  # noqa: BLE001
        # GEZAEHLT, NICHT VERSCHLUCKT - und der leere Eintrag verhindert, dass
        # ein Lauf mit zwanzig Signalen zwanzigmal in denselben Fehler laeuft.
        logger.info("Reihe %s/%s nicht abrufbar: %s", quelle, schluessel, exc)
        reihe = []
    _fluss_cache.clear()                     # nur der heutige Tag bleibt
    _fluss_cache[tagesschluessel] = reihe
    return reihe


def _boersenfluss(conn=None) -> dict | None:
    """Wo steht der heutige Netto-Zufluss in seiner eigenen Geschichte?"""
    from api.onchain import get_btc_exchange_flow_history

    reihe = _gepflegte_reihe(
        conn, "coinmetrics", "btc_netto_boersenfluss",
        lambda: get_btc_exchange_flow_history(tage=FLUSS_FENSTER_TAGE + 70))
    if len(reihe) < FLUSS_MINDESTREIHE:
        return None
    fenster = [w for _, w in reihe[-FLUSS_FENSTER_TAGE:]]
    datum, jetzt = reihe[-1]
    return {"datum": datum, "netto": jetzt, "n": len(fenster),
            "perzentil": _perzentil(fenster, jetzt)}


# --- DIE ROHSTOFFSEITE (16.08.2026, Schritt 3) ------------------------------
#
# WAS COT IST: die US-Aufsicht veroeffentlicht woechentlich, wie die grossen
# Marktteilnehmer im Terminmarkt aufgestellt sind. "Managed Money" sind die
# grossen spekulativen Fonds - naeher an "Stimmung der Profis" als die alte
# Kategorie "Non-Commercial".
#
# WARUM ES FUER ROLLE G TAUGT: es ist eine Erhebung einer Behoerde ueber
# fremde Positionen. Weder aus unserer Kursreihe abgeleitet noch fuer Rolle BC
# sichtbar - die Informationsgrenze, die R-R2 verlangt.
#
# ⚠️ ES BESCHREIBT DEN FUTURE, NICHT UNSER ZERTIFIKAT. Wir halten
# WisdomTree-ETCs; COT misst den Gold-Future an der COMEX. Das ist der
# BASISWERT unseres Papiers, also nah genug, um etwas zu sagen - aber es ist
# nicht dasselbe Instrument, und der Satz sagt das auch.
#
# FENSTER 156 WOCHEN. Drei Jahre decken einen Rohstoffzyklus, und alle vier
# Maerkte tragen es (Kupfer und Erdgas haben 236 Berichte). Die Fensterlaenge
# aendert die Extremhaeufigkeit kaum - gemessen 104/156/208 Wochen: Gold
# 35/50/44 %, Silber 20/15/13 %, Kupfer 7/4/6 %, Erdgas 33/35/38 %.
COT_FENSTER_WOCHEN = 156
COT_MINDESTREIHE = 60


def _cot(conn, symbol: str) -> dict | None:
    """Die COT-Positionierung zum BASISWERT dieses Zertifikats."""
    from agent.rohstoff.pipeline import SYMBOL_ZU_COT_ROHSTOFF
    from api.cftc_cot import get_cot_long_anteil_history

    # DIE ZUORDNUNG WIRD GELIEHEN, NICHT NACHGEBAUT. Sie steht seit dem 18.07.
    # in der Rohstoff-Pipeline; eine zweite Fassung hier waere die naechste
    # Stelle zum Auseinanderlaufen - dieselbe Ueberlegung wie bei `geteilt()`.
    stoff = SYMBOL_ZU_COT_ROHSTOFF.get(str(symbol or "").upper())
    if not stoff:
        return None
    reihe = _gepflegte_reihe(conn, "cftc_cot", stoff,
                             lambda: get_cot_long_anteil_history(stoff))
    if len(reihe) < COT_MINDESTREIHE:
        return None
    fenster = [w for _, w in reihe[-COT_FENSTER_WOCHEN:]]
    datum, jetzt = reihe[-1]
    return {"rohstoff": stoff, "datum": datum, "anteil": jetzt,
            "n": len(fenster), "perzentil": _perzentil(fenster, jetzt)}


def lage(conn, symbol: str, assetklasse: str | None = None) -> dict:
    """Die Positionierungslage - oder ein leeres dict, wenn nichts vorliegt.

    `assetklasse` entscheidet ueber den Boersenfluss und nichts sonst. Fehlt
    sie, bleibt er WEG - fail-closed. Ein Satz ueber Bitcoin-Bewegungen in der
    Beurteilung einer Aktie waere kein fehlender Fakt, sondern ein falscher,
    und P1 (Auftrag) schliesst ihn aus.

    FAIL-SOFT MIT VERMERK: was fehlt, steht unter `fehlt` und wird im Satzbau
    BENANNT. Ein stiller Ausfall waere hier besonders teuer, weil die ganze
    Rolle G auf diesen Zahlen steht - eine leere Antwort saehe aus wie
    'kein Einwand'."""
    sym = str(symbol or "").strip().upper()
    aus: dict = {"symbol": sym, "fehlt": []}

    oi = _reihe(conn, sym, "open_interest")
    fund = _reihe(conn, sym, "funding_rate")
    lang = _reihe(conn, sym, "long_account_pct")

    if oi:
        aus["oi_jetzt"] = oi[0]
        # Der Rueckblick in SCHRITTEN, nicht in Stunden: die Snapshots kommen
        # im 15-Minuten-Takt des Screenings, acht Stunden sind also rund 32.
        n = min(len(oi) - 1, int(OI_RUECKBLICK_STUNDEN * 4))
        if n > 0 and oi[n]:
            aus["oi_aenderung_pct"] = round(100.0 * (oi[0] - oi[n]) / oi[n], 2)
            aus["oi_fenster_stunden"] = round(n / 4.0, 1)
    else:
        aus["fehlt"].append("Open Interest")

    if fund:
        aus["funding_jetzt"] = fund[0]
        aus["funding_perzentil"] = _perzentil(fund, fund[0])
        aus["funding_n"] = len(fund)
    else:
        aus["fehlt"].append("Finanzierungsrate")

    if lang:
        aus["long_anteil_pct"] = round(float(lang[0]), 1)
        aus["long_perzentil"] = _perzentil(lang, lang[0])
        aus["long_n"] = len(lang)
    else:
        aus["fehlt"].append("Anteil der Long-Konten")

    # KEIN `fehlt`-VERMERK, WENN SIE AUSBLEIBT. Die Divergenz braucht zwei
    # Boersen mit langer Reihe; bei den meisten Symbolen gibt es sie, bei
    # jungen und kleinen nicht. Sie hier zu vermissen hiesse, bei jedem
    # duennen Wert einen Mangel zu melden, der keiner ist - dieselbe
    # Ueberlegung wie bei den CSTI-Luecken in `mindestkriterien.PFLICHT_BC`.
    div = _divergenz(conn, sym)
    if div:
        aus["divergenz"] = div

    # NUR FUER KRYPTO, und die Liste ist bewusst eng. "krypto" und "coin"
    # decken die Gruppenvokabeln ab, die die Kette fuehrt; alles andere - auch
    # ein unbekannter Wert - faellt heraus. Genau die Vokabelverwirrung
    # (`etf` gegen `themen_etf`) hat am 16.08. zwei Fakten stillgelegt.
    # ROHSTOFFE: die Positionierung im Basiswert. Anders als der Boersenfluss
    # ist sie SYMBOLSPEZIFISCH - Gold, Silber, Kupfer und Erdgas haben je einen
    # eigenen Bericht. Damit deckt sie G1 UND G2.
    if str(assetklasse or "").lower() in ("rohstoffe", "rohstoff"):
        c = _cot(conn, sym)
        if c:
            aus["cot"] = c
            aus["cot_perzentil"] = c["perzentil"]
        else:
            aus["fehlt_rahmen"] = (aus.get("fehlt_rahmen") or []) + [
                "Positionierung der grossen Fonds im Basiswert"]

    if str(assetklasse or "").lower() in ("krypto", "coin", "crypto"):
        fluss = _boersenfluss(conn)
        if fluss:
            aus["boersenfluss"] = fluss
        else:
            # ⚠️ EIGENER SCHLUESSEL, NICHT `fehlt` - und das ist kein Stil,
            # sondern ein Fehler, den diese Zeile verhindert.
            #
            # `zweite_meinung.rolle_g` bricht ab, wenn `len(fehlt) >= 3` ist
            # (G5: ueber nichts wird nicht gefragt). Haenge ich den Fluss dort
            # an, kann eine ZUSAETZLICHE Quelle die Rolle STILLLEGEN, sobald
            # sie ausfaellt - genau verkehrt herum. Gefunden beim Nachlesen der
            # Aufrufstelle, nicht vom Test: die Simulation lief gruen.
            #
            # UND DER WORTLAUT WAERE FALSCH GEWESEN. `fehlt` erzeugt den Satz
            # "Zu diesem Wert liegt keine Angabe vor" - der Boersenfluss sagt
            # aber nichts ueber diesen Wert, er beschreibt den Rahmen.
            aus.setdefault("fehlt_rahmen", []).append(
                "Boersenzu- und -abfluesse")

    # DAS REGIME MIT SEINER DAUER (16.08.2026). Es ist gerechnet und stand
    # bisher in keinem Prompt. Fuer Rolle G gehoert es hierher und NICHT zu
    # Rolle BC: es beschreibt nicht diesen Wert, sondern den Rahmen, in dem
    # jedes Urteil steht - und die Trennung der Informationsgrenzen ist die
    # Konstruktionsbedingung der zweiten Stufe.
    #
    # DIE DAUER IST DER EIGENTLICHE PUNKT. "baer" allein ist ueber alle
    # Signale eines Tages identisch und damit ein konstantes Feld (R-T6);
    # "seit 27 Tagen" macht daraus eine Aussage, die sich bewegt.
    # NICHT AUS EINER TABELLE - es gibt keine. Das Regime steht auf der
    # juengsten Signalzeile, die Dauer rechnet `regime.regime_persistenz_tage()`.
    # Meine erste Fassung fragte `regime_status` ab; die Tabelle existiert
    # nicht, und der Fail-soft haette das stillschweigend als "keine Angabe"
    # gemeldet - richtig gefangen, aber dauerhaft leer.
    try:
        r = conn.execute(
            "SELECT regime FROM signals WHERE regime IS NOT NULL "
            "ORDER BY created_at DESC LIMIT 1").fetchone()
        if r and r[0]:
            aus["regime"] = str(r[0])
            # DIE DAUER SEPARAT - faellt sie aus, ist das Regime trotzdem da.
            # Erste Fassung fing beides gemeinsam: die Zeile "Regime baer" UND
            # "keine Angabe zum Marktregime" standen nebeneinander in derselben
            # Ausgabe. Ein Widerspruch, den der Leser nicht aufloesen kann.
            #
            # ⚠️ DIE DAUER KAM IM BETRIEB NIE AN (gefunden 16.08. abends beim
            # Rendern fuer die Parameteruebersicht). `regime_persistenz_tage`
            # liest ueber `get_hebel_regime_tageshistorie()`, und die greift
            # mit `row["tag"]` auf die Spalten zu - das setzt
            # `conn.row_factory = sqlite3.Row` voraus. `rolle_g` oeffnet aber
            # eine gewoehnliche Verbindung. Ergebnis: TypeError, vom breiten
            # `except` verschluckt, und in JEDER Ausgabe stand nur "Regime
            # 'baer'" ohne Dauer.
            #
            # DAS WAR GENAU DER SCHADEN, gegen den die Dauer eingebaut wurde:
            # das Regime allein ist ueber alle Signale eines Tages identisch -
            # ein konstantes Feld (R-T6). Erst "seit 27 Tagen" bewegt sich.
            # Fail-soft ist fail-silent, hier in seiner teuersten Form.
            #
            # DIE ZEILENFABRIK WIRD GELIEHEN, NICHT UEBERNOMMEN. `conn` kann
            # dem Aufrufer gehoeren; sie bleibt hinterher, wie sie war.
            try:
                from agent.krypto.regime import regime_persistenz_tage

                _alt = conn.row_factory
                try:
                    conn.row_factory = sqlite3.Row
                    aus["regime_tage"] = regime_persistenz_tage(conn, str(r[0]))
                finally:
                    conn.row_factory = _alt
            except Exception as exc:                         # noqa: BLE001
                # GEZAEHLT STATT VERSCHLUCKT. Ohne diese Zeile war der Ausfall
                # nur daran zu sehen, dass ein Halbsatz fehlte.
                logger.info("Regime-Dauer fuer %s nicht ermittelbar: %s",
                            sym, exc)
        else:
            aus["fehlt"].append("Marktregime")
    except Exception as exc:                                 # noqa: BLE001
        logger.info("Regime nicht lesbar: %s", exc)
        aus["fehlt"].append("Marktregime")
    return aus


def saetze(e: dict) -> list[str]:
    """Die Positionierung als Aussagen - fuer Rolle G.

    JEDE ZAHL MIT IHREM MASSSTAB. "Die Finanzierungsrate liegt im 96.
    Perzentil der letzten 400 Messungen" traegt; "0.0312 %" traegt nicht."""
    if not e:
        return []
    z: list[str] = []

    if e.get("oi_aenderung_pct") is not None:
        richtung = "gestiegen" if e["oi_aenderung_pct"] > 0 else "gefallen"
        # DIE BOERSE WIRD SEIT 16.08. GENANNT. Solange nur eine Zahl dastand,
        # war "der Terminmarkt" eine zulaessige Verkuerzung. Jetzt folgt ein
        # Satz, der Boersen beim Namen nennt - und eine unbeschriftete Zahl
        # daneben laesst offen, welche der drei gemeint ist. Genau die Sorte
        # Mehrdeutigkeit, die R-T1 mit "das Fenster nennen" ausschliesst.
        z.append(
            f"Die offenen Kontrakte am Terminmarkt sind auf Binance in den "
            f"letzten {e['oi_fenster_stunden']:.0f} Stunden um "
            f"{abs(e['oi_aenderung_pct']):.1f} % {richtung}.")

    # DIE BOERSEN NEBENEINANDER - OHNE DEUTUNG (16.08.2026).
    #
    # HIER STEHT BEWUSST KEIN HINWEIS, WAS EINE GROSSE SPANNE BEDEUTET. Beim
    # Funding gibt es einen (Extremwerte gehen Umkehrungen voraus), und er ist
    # durch die Praxisliteratur gedeckt. Fuer die Boersendivergenz ist er das
    # NICHT: die Literatur fuehrt die Spanne zwischen Boersen als
    # Arbitrage-Groesse, nicht als Richtungssignal. Eine Deutung waere hier
    # meine Vermutung - Rang 3 der Eignungsleiter (P2) und damit nicht
    # aufnahmefaehig. Der Fakt steht, die Schlussfolgerung zieht das Modell.
    d = e.get("divergenz")
    if d and d.get("spanne_perzentil") is not None:
        hoch = _BOERSENNAME.get(d["hoch_boerse"], d["hoch_boerse"])
        tief = _BOERSENNAME.get(d["tief_boerse"], d["tief_boerse"])
        # QUALITATIV, NICHT ARITHMETISCH (Nutzerhinweis 16.08.). Meine erste
        # Fassung nannte beide Einzelwerte UND die Spanne - also drei Zahlen,
        # von denen die dritte die Differenz der ersten beiden ist. Das ist
        # eine Rechenaufgabe an ein Modell, das nicht rechnen soll, und obendrein
        # redundant. Die Richtung traegt die Aussage, das Perzentil den Massstab.
        # GLEICHLAUF IST AUCH EINE AUSSAGE - und "uneinheitlich" waere dann
        # schlicht falsch. Die Werte sind auf eine Stelle gerundet; zwei
        # Boersen koennen danach denselben Wert tragen.
        if abs(d["spanne_pp"]) < 0.1:
            z.append("Die Boersen entwickeln sich dabei gleichlaeufig.")
        else:
            if d["hoch_pct"] > 0 > d["tief_pct"]:
                lage_ = f"auf {hoch} nehmen sie zu, auf {tief} gleichzeitig ab"
            elif d["tief_pct"] >= 0:
                lage_ = f"auf {hoch} nehmen sie staerker zu als auf {tief}"
            else:
                lage_ = f"auf {tief} nehmen sie staerker ab als auf {hoch}"
            z.append(
                f"Die Boersen entwickeln sich dabei uneinheitlich: {lage_}.")
        # DIE EINORDNUNG GEHOERT DAZU, NICHT INS MODELL. Ein blosses "26.
        # Perzentil" verlangt vom Leser die Frage, ob das viel ist - also
        # genau die Rechenleistung, die ein Sprachmodell nicht erbringen soll.
        # Der Funding-Satz zwei Absaetze weiter unten macht es seit jeher
        # richtig ("im gewohnten Bereich"); hier fehlte es. Dieselben Grenzen,
        # damit nicht zwei Massstaebe nebeneinanderstehen.
        pd_ = d["spanne_perzentil"]
        wie = ("weiter auseinander als gewohnt" if pd_ >= EXTREM_OBEN else
               "enger beieinander als gewohnt" if pd_ <= EXTREM_UNTEN else
               "im gewohnten Bereich")
        z.append(
            f"Wie weit sie auseinanderliegen, steht im {pd_}. Perzentil der "
            f"letzten {d['n_historie']} Messungen dieses Werts - {wie}.")

    p = e.get("funding_perzentil")
    if p is not None:
        n = e.get("funding_n", 0)
        wo = ("aussergewoehnlich hoch" if p >= EXTREM_OBEN else
              "aussergewoehnlich niedrig" if p <= EXTREM_UNTEN else
              "im gewohnten Bereich")
        z.append(
            f"Die Finanzierungsrate steht im {p}. Perzentil der letzten {n} "
            f"Messungen dieses Werts - {wo}.")
        # DER HINWEIS AUF DIE UMKEHR, und zwar NUR bei einem Extremwert.
        # Die Praxisliteratur ist hier eindeutig: extremes Funding geht
        # scharfen Umkehrungen oft voraus. Bei einem gewoehnlichen Wert waere
        # derselbe Satz ein konstantes Feld (R-T6) und damit schaedlich.
        if p >= EXTREM_OBEN:
            z.append("Bei so hohen Raten zahlen die Long-Positionen an die "
                     "Short-Positionen; historisch gingen solche Extremwerte "
                     "haeufig scharfen Rueckschlaegen voraus.")
        elif p <= EXTREM_UNTEN:
            z.append("Bei so niedrigen Raten zahlen die Short-Positionen an "
                     "die Long-Positionen; historisch gingen solche "
                     "Extremwerte haeufig scharfen Erholungen voraus.")

    if e.get("long_anteil_pct") is not None:
        lp = e.get("long_perzentil")
        satz = f"{e['long_anteil_pct']:.0f} % der Konten stehen long"
        if lp is not None:
            # ⚠️ ZWEI MAENGEL, GEFUNDEN AM 16.08. von
            # `pruefe_zahlen_in_prompts.py` - beide aelter als der Fund.
            #
            # ERSTENS ohne Einordnung: "das 92. Perzentil" verlangte vom
            # Modell die Entscheidung, ob das viel ist. Der Funding-Satz
            # darueber macht es seit jeher richtig; hier fehlte es, und zwar
            # in 37 von 37 gerenderten Faellen.
            #
            # ZWEITENS ohne Fenster: "der eigenen Historie" nennt nicht, wie
            # lang diese Historie ist - R-T1 verlangt genau das, und der
            # Nachbarsatz nennt es ("der letzten 400 Messungen").
            wie = ("aussergewoehnlich viele" if lp >= EXTREM_OBEN else
                   "aussergewoehnlich wenige" if lp <= EXTREM_UNTEN else
                   "im gewohnten Bereich")
            satz += (f"; das ist das {lp}. Perzentil der letzten "
                     f"{e.get('long_n', 0)} Messungen - {wie}")
        z.append(satz + ".")

    # DIE ZWEITE INFORMATIONSART. Kein Wort ueber Richtung oder Folgen: dass
    # Zufluesse Verkaufsdruck ANKUENDIGEN, ist eine gaengige Lesart und in
    # unseren Daten nie gemessen - also P2 Rang 3 und nicht aufnahmefaehig.
    # `onchain.py` nennt sie im Feldkommentar "potenziell Verkaufsdruck"; genau
    # dieses "potenziell" gehoert nicht in einen Faktensatz.
    # DIE ROHSTOFFSEITE. Der Satz nennt ausdruecklich den BASISWERT und nicht
    # das gehaltene Papier: wir halten ein WisdomTree-Zertifikat, die Behoerde
    # misst den Future an der COMEX. Wer das verschweigt, laesst das Modell
    # glauben, es lese eine Aussage ueber unser Instrument.
    ct = e.get("cot")
    if ct and ct.get("perzentil") is not None:
        pc = ct["perzentil"]
        wie = ("aussergewoehnlich stark" if pc >= EXTREM_OBEN else
               "aussergewoehnlich schwach" if pc <= EXTREM_UNTEN else
               "im gewohnten Bereich")
        z.append(
            "Die US-Aufsicht meldet woechentlich, wie stark die grossen "
            "spekulativen Fonds auf der Kaufseite stehen - im Terminmarkt des "
            "Basiswerts, nicht in diesem Zertifikat.")
        z.append(
            f"Im Bericht vom {ct['datum']} steht dieser Anteil im {pc}. "
            f"Perzentil der letzten {ct['n']} Wochenberichte - {wie}.")

    f = e.get("boersenfluss")
    if f and f.get("perzentil") is not None:
        pf = f["perzentil"]
        richtung = ("flossen mehr Bitcoin auf die Boersen als von ihnen herunter"
                    if f["netto"] > 0 else
                    "flossen mehr Bitcoin von den Boersen herunter als auf sie")
        wie = ("aussergewoehnlich viel" if pf >= EXTREM_OBEN else
               "aussergewoehnlich wenig" if pf <= EXTREM_UNTEN else
               "im gewohnten Bereich")
        z.append(f"Am {f['datum']} {richtung}.")
        z.append(f"Gemessen an den letzten {f['n']} Tagen steht diese Bewegung "
                 f"im {pf}. Perzentil - {wie}.")

    if e.get("regime"):
        satz = f"Der Gesamtmarkt steht im Regime {e['regime']!r}"
        if e.get("regime_tage") is not None:
            satz += f", seit {e['regime_tage']} Tagen ununterbrochen"
        z.append(satz + ".")

    for f in (e.get("fehlt_rahmen") or []):
        # ANDERER WORTLAUT ALS BEI `fehlt`: es fehlt nichts ZU DIESEM WERT,
        # sondern eine Angabe ueber den Markt. Verschwiegen wird trotzdem
        # nichts - "fail-soft ist fail-silent".
        z.append(f"Zum Gesamtmarkt liegt keine Angabe vor: {f}.")

    for f in (e.get("fehlt") or []):
        # BENANNT, NICHT VERSCHWIEGEN. Ohne diesen Satz liest das Modell die
        # Abwesenheit als "unauffaellig" - derselbe Fehler, den die
        # Bestandserhebung am 16.08. bei acht Assets gefunden hat.
        z.append(f"Zu diesem Wert liegt keine Angabe vor: {f}.")
    return z
