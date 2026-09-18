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

⚠️ NICHT HIER, UND AUCH NICHT IN ROLLE G: Nachrichten und Termine.

Hier stand bis zum 16.08.2026 abends, sie gehoerten "ebenfalls zu Rolle G".
Das stammt aus einem Entwurf, in dem die Positionierung zu
DETERMINISTISCHEN Regeln werden sollte und die zweite Stufe nur noch
Nachrichten gelesen haette (Umbauplan Kapitel 39). Diese Gabelung wurde
NICHT genommen - gebaut wurde das Gegenteil: Rolle G ist die
Positionierungsrolle mit eigenen Quellen (Kapitel 55-60).

WOHIN SIE GEHOEREN: zu Rolle BC. Eine Nachricht ist der KATALYSATOR -
der Grund, warum ein Setup JETZT handelbar ist, also Teil des Einstiegs
und nicht seiner Pruefung. Rolle G kann nur einwenden, nie befuerworten;
ein Katalysator, der ausschliesslich vetieren kann, ist keiner. Eine gute
Quartalszahl koennte dort nichts bewirken, eine schlechte alles.

Begruendung und Gegenrede: Umbauplan Kapitel 63, Regel R-R6.

ALLE SAETZE MIT BEZUG, KEINE NACKTE ZAHL. Dieselbe Regel wie in
`lagebeschreibung.py`, und aus demselben Grund: eine Zahl ohne Massstab wird
zertokenisiert und traegt nicht. Die Bestandserhebung vom 16.08. hat fuer die
bestehenden Bloecke 41 Saetze geprueft - keiner trug eine nackte Zahl. Dieser
Block haelt denselben Stand.
"""
from __future__ import annotations

from agent import schreibweise as S

import logging
import sqlite3
from bisect import bisect_left
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

# Wie weit zurueck der Open-Interest-Vergleich reicht - 8 Stunden.
# ⚠️ Richtigstellung 14.09. (Review): hier stand ,dieselbe Groesse wie
# `hebel_screening.oi_lookback_stunden`' - dort stehen aber 4 Stunden, und
# gelesen wird die Konfiguration nicht. Es sind zwei verschiedene Fenster.
OI_RUECKBLICK_STUNDEN = 8.0

# ⚠️⚠️⚠️ DIE TERMINMARKT-ZAHLEN WERDEN NACH DER UHR GELESEN, NICHT NACH ZEILEN
# (Schritt 54, 14.09.2026 - Befund 2.452, Nutzerentscheidungen vom selben Tag).
#
# BIS HIERHER las `_reihe` die letzten 400 Zeilen, egal wie alt, und das
# ,8-Stunden'-Fenster war die 32. Zeile. Als das Hebel-Screening am 12.09.
# abgeschaltet wurde, schrieb niemand mehr - und Rolle BC und Rolle G bekamen
# weiter ,in den letzten 8 Stunden praktisch unveraendert', bei 13 Werten mit
# Zahlen aus dem Juli. Das Modell hat damit Urteile begruendet.
#
#   LESEGRENZE 2 h     ist der juengste Wert aelter, gibt es KEINE Zahl, sondern
#                      einen Satz, dass keine aktuelle Angabe vorliegt. Gemessen
#                      (01.08.-12.09.): zwischen 90 und 120 Minuten liegt fast
#                      keine Luecke - kurze Aussetzer bleiben darunter, echte
#                      Ausfaelle weit darueber.
#   VERGLEICH 100 h    wo eine Zahl ,ungewoehnlich hoch' genannt wird, ist der
#                      Vergleich die eigene Geschichte der letzten 100 Stunden -
#                      so viel, wie 400 Zeilen im 15-Minuten-Takt immer sein
#                      sollten. Nach einer Luecke wuerde sonst mit Wochen alten
#                      Werten verglichen.
#   TOLERANZ 30 min    der Vergleichsstand ,vor 8 Stunden' darf so weit
#                      daneben liegen - zwei ausgefallene Takte.
LESEGRENZE_STUNDEN = 2.0
VERGLEICHSZEITRAUM_STUNDEN = 100.0
FENSTER_TOLERANZ_MINUTEN = 30.0

# Ab wann eine Finanzierungsrate als extrem gilt. NICHT frei gesetzt: es ist
# das Perzentil der EIGENEN Historie, und 90/10 ist die uebliche Grenze fuer
# "aussergewoehnlich" - dieselbe, die `atr_percentile` im Projekt verwendet.
EXTREM_OBEN, EXTREM_UNTEN = 90, 10


def _zeit(text) -> datetime | None:
    """ISO-Zeitstempel -> Zeitpunkt mit Zeitzone (ohne Angabe: UTC)."""
    try:
        t = datetime.fromisoformat(str(text))
    except (TypeError, ValueError):
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def _jetzt(jetzt: datetime | None) -> datetime:
    if jetzt is None:
        return datetime.now(timezone.utc)
    return jetzt if jetzt.tzinfo else jetzt.replace(tzinfo=timezone.utc)


def _stunden(von: datetime, bis: datetime) -> float:
    return (bis - von).total_seconds() / 3600.0


def _zeitreihe(conn, symbol: str, spalte: str, jetzt: datetime,
               boerse: str = "binance") -> list:
    """[(zeitpunkt, wert)] der letzten 100 Stunden bis `jetzt`, juengste zuerst.

    ⚠️ ERSETZT `_reihe` (letzte 400 Zeilen ohne Alter) - Befund 2.452.
    `bis = jetzt` gilt auch fuer Nachspielungen an einer Sicherung: kein Wert
    aus der ,Zukunft' des Stichzeitpunkts."""
    seit = (jetzt - timedelta(hours=VERGLEICHSZEITRAUM_STUNDEN)).isoformat()
    try:
        zeilen = conn.execute(
            f"SELECT fetched_at, {spalte} FROM open_interest_snapshot "
            "WHERE symbol = ? AND exchange = ? "
            f"AND {spalte} IS NOT NULL AND fetched_at >= ? AND fetched_at <= ? "
            "ORDER BY fetched_at DESC", (symbol, boerse, seit,
                                         jetzt.isoformat())).fetchall()
    except sqlite3.Error as exc:
        logger.info("Positionierung %s/%s nicht lesbar: %s", symbol, spalte, exc)
        return []
    aus = []
    for t, v in zeilen:
        z = _zeit(t)
        if z is not None and v is not None:
            aus.append((z, float(v)))
    return aus


def _letzter_stand(conn, symbol: str, spalte: str, jetzt: datetime,
                   boerse: str | tuple = "binance") -> datetime | None:
    """Der juengste Zeitpunkt ueberhaupt - auch ausserhalb der 100 Stunden.

    Nur fuer den Satz ,letzter Stand vor X': ob eine Groesse VERALTET ist oder
    NIE da war, sind zwei verschiedene Aussagen."""
    boersen = (boerse,) if isinstance(boerse, str) else tuple(boerse)
    try:
        t = conn.execute(
            f"SELECT MAX(fetched_at) FROM open_interest_snapshot "
            f"WHERE symbol = ? AND exchange IN ({','.join('?' * len(boersen))}) "
            f"AND {spalte} IS NOT NULL AND fetched_at <= ?",
            (symbol, *boersen, jetzt.isoformat())).fetchone()
    except sqlite3.Error:
        return None
    return _zeit(t[0]) if t and t[0] else None


def _vergleichsstand(reihe: list, ziel: datetime):
    """Der Eintrag, der `ziel` am naechsten liegt - innerhalb der Toleranz.

    `reihe` ist [(zeitpunkt, wert)] juengste zuerst."""
    bester, abstand = None, None
    for t, v in reihe:
        d = abs((t - ziel).total_seconds())
        if abstand is None or d < abstand:
            bester, abstand = (t, v), d
        elif t < ziel:
            break
    if bester is None or abstand > FENSTER_TOLERANZ_MINUTEN * 60:
        return None
    return bester


BOERSEN = ("binance", "bybit", "okx")

_BOERSENNAME = {"binance": "Binance", "bybit": "Bybit", "okx": "OKX"}

# Wie viele Vergleichswerte die Divergenz mindestens braucht.
MINDEST_HISTORIE_DIVERGENZ = 40


def _oi_je_boerse(conn, symbol: str, jetzt: datetime) -> dict:
    """{boerse: {zeitpunkt: open_interest}} - nur Boersen mit genug Reihe.

    Seit Schritt 54 ueber die letzten 100 Stunden, nicht ueber 400 Zeilen."""
    aus: dict = {}
    for b in BOERSEN:
        reihe = _zeitreihe(conn, symbol, "open_interest", jetzt, boerse=b)
        if len(reihe) > MINDEST_HISTORIE_DIVERGENZ:
            aus[b] = {t: v for t, v in reihe}
    return aus


def _divergenz(conn, symbol: str, jetzt: datetime | None = None) -> dict | None:
    """Wie weit laufen die Boersen beim Open Interest auseinander?

    GEPAART AUF DENSELBEN ZEITPUNKTEN. Die Sammlung schreibt alle drei
    Boersen mit demselben `fetched_at`, ein Schnitt der Zeitschluessel ist
    also verlustarm - und er verhindert, dass ein verpasster Abruf als
    Meinungsunterschied erscheint.

    ⚠️ SEIT SCHRITT 54 NACH DER UHR: der Vergleichsstand ist der Zeitpunkt
    rund 8 Stunden vorher (Toleranz 30 min), nicht die 32. Zeile - eine Luecke
    in der Reihe machte aus ,8 Stunden' sonst beliebig viele. Und der juengste
    gemeinsame Zeitpunkt muss innerhalb der Lesegrenze liegen."""
    jetzt = _jetzt(jetzt)
    reihen = _oi_je_boerse(conn, symbol, jetzt)
    if len(reihen) < 2:
        return None
    zeiten = sorted(set.intersection(*(set(d) for d in reihen.values())))
    if not zeiten or _stunden(zeiten[-1], jetzt) > LESEGRENZE_STUNDEN:
        return None
    toleranz = FENSTER_TOLERANZ_MINUTEN * 60

    spannen: list[float] = []
    aktuell: dict = {}
    for t in reversed(zeiten):
        ziel = t - timedelta(hours=OI_RUECKBLICK_STUNDEN)
        i = bisect_left(zeiten, ziel)
        partner = [zeiten[k] for k in (i - 1, i) if 0 <= k < len(zeiten)]
        partner = [p for p in partner
                   if abs((p - ziel).total_seconds()) <= toleranz]
        if not partner:
            continue
        alt_t = min(partner, key=lambda p: abs((p - ziel).total_seconds()))
        aend = {}
        for b, d in reihen.items():
            alt = d[alt_t]
            if alt:
                aend[b] = 100.0 * (d[t] - alt) / alt
        if len(aend) < 2:
            continue
        spannen.append(max(aend.values()) - min(aend.values()))
        if not aktuell:
            if t != zeiten[-1]:
                # Der juengste Zeitpunkt hat keinen Vergleichsstand - dann
                # gibt es KEINE aktuelle Divergenz, und eine aeltere als
                # aktuelle auszugeben waere derselbe Fehler wie 2.452.
                return None
            aktuell = aend
    if not aktuell or len(spannen) < MINDEST_HISTORIE_DIVERGENZ:
        return None

    hoch = max(aktuell, key=aktuell.get)
    tief = min(aktuell, key=aktuell.get)
    return {"hoch_boerse": hoch, "hoch_pct": round(aktuell[hoch], 1),
            "tief_boerse": tief, "tief_pct": round(aktuell[tief], 1),
            "spanne_pp": round(aktuell[hoch] - aktuell[tief], 1),
            "spanne_perzentil": _perzentil(spannen, spannen[0]),
            "n_boersen": len(aktuell), "n_historie": len(spannen),
            "fenster_stunden": OI_RUECKBLICK_STUNDEN}


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

# ⚠️ EIN PERZENTIL AUS ZWEI WERTEN IST KEINE EINORDNUNG (20.08.2026).
#
# In einer echten Mail stand: "Der Anteil der Konten auf der Kaufseite steht
# im 0. Perzentil der letzten 2 MESSUNGEN - aussergewoehnlich wenige." Das
# klingt nach einem Befund und ist eine Muenze: bei zwei Werten gibt es nur
# 0 oder 100, und beide heissen "aussergewoehnlich".
#
# Nutzerrueckmeldung 20.08.: die Perzentile seien "zum Teil nicht oder
# schwierig einzuordnen". Dieser Fall war nicht schwierig einzuordnen,
# sondern gar nicht - und er sah trotzdem aus wie eine Aussage.
#
# Dreissig ist die Zahl, unter der ein einzelner Wert mehr als drei
# Prozentpunkte verschiebt. Die Nachbarn dieses Moduls liegen bei 40 bis 120;
# hier gilt der niedrigste Wert, der noch traegt, weil die Reihe je Symbol
# erst aufgebaut wird.
PERZENTIL_MINDESTREIHE = 30

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
# externe_reihen_job`), genau wie `open_interest_snapshot` vom eigenen Job
# `terminmarkt_job` geschrieben (seit 14.09., vorher vom Screening) und hier
# nur gelesen wird.
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


def _gepflegte_reihe(conn, quelle: str, schluessel: str, holen,
                     grenze: int = 400) -> list:
    """Die Reihe aus der Datenbank, sonst aus dem Speicher, sonst aus dem Netz.

    ⚠️ `grenze` MUSS ZUM FENSTER DES AUFRUFERS PASSEN (17.08.2026).
    `lies_externe_reihe` liest ohne Angabe 400 Punkte. Der Boersenfluss
    rechnet aber ueber 730 Tage - und lieferte deshalb still ein
    400-Tage-Perzentil. Der Satz sagte es ehrlich ("die letzten 400 Tage"),
    aber es war nicht das entworfene Fenster.

    GEFUNDEN AM GERENDERTEN SATZ, nicht im Code: solange die Reihe aus dem
    Netz kam, stimmte es; erst der Umzug in die Datenbank hat das Fenster
    beschnitten."""
    from database import db as DB

    if conn is not None:
        alter = DB.alter_externe_reihe(conn, quelle, schluessel)
        if alter is not None and alter <= HOECHSTALTER_REIHE_STUNDEN:
            aus_db = DB.lies_externe_reihe(conn, quelle, schluessel, grenze)
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
        lambda: get_btc_exchange_flow_history(tage=FLUSS_FENSTER_TAGE + 70),
        grenze=FLUSS_FENSTER_TAGE + 70)
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


# --- WIE VIEL METALL TATSAECHLICH HINTERLEGT IST (17.08.2026) ---------
#
# ⚠️ DIE VERAENDERUNG IST DIE AUSSAGE, NICHT DER STAND. Ein Perzentil auf
# den Stueckzahl-STAND waere wertlos: die Reihe waechst oder faellt
# langsam, und der juengste Wert laege fast immer im 0. oder 100.
# Perzentil - ein konstantes Feld in Zeitlupe (R-T6).
#
# Gemessen wird deshalb die Veraenderung ueber ein Fenster, und ihr
# Perzentil gegen die eigene Geschichte. Dieselbe Form wie beim
# Boersenfluss - und aus demselben Grund.
#
# WARTEZEIT: 90 Punkte bei taeglichem Takt, also rund drei Monate. Der
# Satz entsteht von selbst, sobald sie da sind.
ETF_BESTAND_MINDESTREIHE = 90
ETF_BESTAND_FENSTER_TAGE = 20
ETF_BESTAND_PERZENTILBASIS = 250


def _etf_bestand(conn, symbol: str) -> dict | None:
    """Wie hat sich die hinterlegte Menge veraendert - und wie ungewoehnlich?

    NUR FUER ROHSTOFFE MIT ETF. Kupfer fehlt, weil CPER keine Stueckzahl
    ausweist; fuer OD7C entsteht deshalb kein Satz."""
    from agent.rohstoff.pipeline import SYMBOL_ZU_COT_ROHSTOFF
    from database import db as DB

    stoff = SYMBOL_ZU_COT_ROHSTOFF.get(str(symbol or "").upper())
    if not stoff or conn is None:
        return None
    reihe = DB.lies_externe_reihe(conn, "etf_bestand", f"{stoff}_stueckzahl",
                                  ETF_BESTAND_PERZENTILBASIS
                                  + ETF_BESTAND_FENSTER_TAGE + 20)
    if len(reihe) < ETF_BESTAND_MINDESTREIHE:
        return None
    werte = [w for _, w in reihe]
    f = ETF_BESTAND_FENSTER_TAGE
    aend = [100.0 * (werte[i] - werte[i - f]) / werte[i - f]
            for i in range(f, len(werte)) if werte[i - f]]
    if len(aend) < 30:
        return None
    jetzt = aend[-1]
    return {"stoff": stoff, "datum": reihe[-1][0], "aenderung_pct": jetzt,
            "n": len(aend), "fenster": f,
            "perzentil": _perzentil(aend, jetzt)}


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
                             lambda: get_cot_long_anteil_history(stoff),
                             grenze=COT_FENSTER_WOCHEN + 40)
    if len(reihe) < COT_MINDESTREIHE:
        return None
    fenster = [w for _, w in reihe[-COT_FENSTER_WOCHEN:]]
    datum, jetzt = reihe[-1]
    return {"rohstoff": stoff, "datum": datum, "anteil": jetzt,
            "n": len(fenster), "perzentil": _perzentil(fenster, jetzt)}


# --- DIE AKTIENSEITE (16.08.2026, Schritt 4) --------------------------------
#
# ZWEI QUELLEN, ZWEI SEHR VERSCHIEDENE QUALITAETEN - und der Unterschied ist
# gemessen, nicht geschaetzt.
#
# EINDECKUNGSDAUER (FINRA): stark. PLTR traegt 140 Meldeperioden ab 2020,
# VST 207 ab 2017, `days_to_cover` fehlt in KEINER. Der Wert ist bereits
# normiert - Leerverkaufsposition geteilt durch Tagesumsatz -, also genau die
# Form, die R-T5 verlangt. Ein Abruf je Symbol.
#
# INSIDERGESCHAEFTE (SEC Form 4): schwach als Perzentil, brauchbar als Zaehlung.
# Gemessen ueber 730 Tage: PLTR 572 Transaktionen, davon **3 Kaeufe**; VST
# 9 Transaktionen, davon **0 Kaeufe**. Ein Satz ueber Insiderkaeufe hiesse fast
# immer "keine" - ein konstantes Feld (R-T6), dieselbe Absage wie an MVRV.
#
#     Was BLEIBT, ist die Zaehlung: wie viele Insider verkauft haben und ob
#     ueberhaupt jemand gekauft hat. Das schwankt (PLTR acht Personen, VST
#     sechs) und steht in keiner Kursreihe.
#
# WARUM KEIN VOLUMEN-PERZENTIL. Es waere die bessere Groesse - das monatliche
# Verkaufsvolumen von PLTR schwankt um das 13,2-fache. Aber es gibt nur
# 18 Monatspunkte, und dafuer muessten je Symbol rund 120 Filings einzeln
# geholt werden. Beides spricht dagegen; vermerkt als offener Punkt.
SHORT_FENSTER_PERIODEN = 104          # rund vier Jahre bei halbmonatlicher Meldung
SHORT_MINDESTREIHE = 40
INSIDER_FENSTER_TAGE = 90


def _short_interest(conn, symbol: str) -> dict | None:
    """Wo steht die Eindeckungsdauer in ihrer eigenen Geschichte?"""
    from api.finra import get_days_to_cover_history

    sym = str(symbol or "").upper()
    reihe = _gepflegte_reihe(conn, "finra", f"{sym}_days_to_cover",
                             lambda: get_days_to_cover_history(sym),
                             grenze=SHORT_FENSTER_PERIODEN + 40)
    if len(reihe) < SHORT_MINDESTREIHE:
        return None
    fenster = [w for _, w in reihe[-SHORT_FENSTER_PERIODEN:]]
    datum, jetzt = reihe[-1]
    return {"datum": datum, "tage": jetzt, "n": len(fenster),
            "perzentil": _perzentil(fenster, jetzt)}


def _insider(conn, symbol: str) -> dict | None:
    """Wer hat in den letzten Monaten gekauft, wer verkauft?

    LIEST NUR, HOLT NIE. Anders als die uebrigen Quellen geht hier KEIN
    Netzabruf ab - `externe_reihen_job` legt beide Zahlen taeglich ab. Grund
    ist die Drosselung: ein Form-4-Abruf sind mehrere Anfragen je Symbol, und
    bei einer Sperre gaebe es keine leere, sondern eine FALSCHE Antwort."""
    from database import db as DB

    sym = str(symbol or "").upper()
    # ⚠️ GESCHAEFTE, NICHT PERSONEN. `summarize_insider_activity` zaehlt
    # Transaktionen; die erste Fassung nannte den Schluessel "kaeufer" und
    # den Satz "55 verkauft" - beides haette Personen behauptet. Bei PLTR
    # waren es 55 Geschaefte von acht Personen.
    kauf = DB.lies_externe_reihe(conn, "sec_edgar", f"{sym}_insider_kaeufe", 1)
    verkauf = DB.lies_externe_reihe(conn, "sec_edgar", f"{sym}_insider_verkaeufe", 1)
    if not verkauf and not kauf:
        return None
    datum = (verkauf or kauf)[-1][0]
    return {"datum": datum,
            "kaeufe": int(kauf[-1][1]) if kauf else 0,
            "verkaeufe": int(verkauf[-1][1]) if verkauf else 0}


# --- ZWEI QUELLEN, DIE SICH SELBST EINSCHALTEN (17.08.2026) ----------------
#
# NUTZERFRAGE: *"sind diese alle dokumentiert und im Plan, bzw. hast du diese
# bereits fertig umgesetzt und wir warten nur?"*
#
# ⚠️ BEIM STABLECOIN-ANGEBOT WAR DIE ANTWORT: NEIN. Ich hatte nur das SAMMELN
# gebaut. In drei Monaten haette sich jemand erinnern muessen, dass da eine
# Reihe waechst, fuer die noch kein Satz existiert - und genau so gehen Dinge
# verloren.
#
# BEIDE WEGE STEHEN JETZT VOLLSTAENDIG. Der Satz entsteht, sobald die Reihe
# lang genug ist; bis dahin entsteht keiner. Es gibt nichts zu merken und
# nichts nachzubauen - die Zeit allein schaltet sie ein.
#
#     Stablecoin-Angebot   ab   90 Punkten   (taeglich -> rund drei Monate)
#     DVOL / Skew          ab   60 Punkten   (taeglich -> rund zwei Monate)
#
# WARUM SIE ZU ROLLE G GEHOEREN (Prinzip aus Kapitel 66.3b): beide beschreiben,
# wie DIE ANDEREN aufgestellt sind - das verfuegbare, noch nicht investierte
# Kapital und das, was der Optionsmarkt fuer die naechsten Wochen einpreist.
# Keine davon ist eine Eigenschaft MEINES Trades.
STABLECOIN_MINDESTREIHE = 90
STABLECOIN_FENSTER = 365
OPTIONEN_MINDESTREIHE = 60
OPTIONEN_FENSTER = 365
DERIBIT_WAEHRUNGEN = ("BTC", "ETH")


def _aus_reihe(conn, quelle: str, schluessel: str, mindest: int,
               fenster: int) -> dict | None:
    """Juengster Wert und sein Perzentil - oder None, solange es zu wenige gibt."""
    from database import db as DB

    if conn is None:
        return None
    reihe = DB.lies_externe_reihe(conn, quelle, schluessel, fenster + 40)
    if len(reihe) < mindest:
        return None
    werte = [w for _, w in reihe[-fenster:]]
    datum, jetzt = reihe[-1]
    return {"datum": datum, "wert": jetzt, "n": len(werte),
            "perzentil": _perzentil(werte, jetzt)}


def _stablecoin(conn) -> dict | None:
    """Das \"Trockenpulver\" - Kapital, das im Kryptomarkt liegt, aber nicht
    investiert ist."""
    return _aus_reihe(conn, "defillama", "stablecoin_angebot_usd",
                      STABLECOIN_MINDESTREIHE, STABLECOIN_FENSTER)


def _optionsmarkt(conn, symbol: str) -> dict | None:
    """Erwartete Schwankung und Schieflage der Absicherungskosten.

    NUR BTC UND ETH - Deribit fuehrt nur fuer diese beiden einen liquiden
    Optionsmarkt (live geprueft: SOL liefert nichts)."""
    sym = str(symbol or "").upper()
    if sym not in DERIBIT_WAEHRUNGEN:
        return None
    dvol = _aus_reihe(conn, "deribit", f"{sym}_dvol",
                      OPTIONEN_MINDESTREIHE, OPTIONEN_FENSTER)
    skew = _aus_reihe(conn, "deribit", f"{sym}_skew",
                      OPTIONEN_MINDESTREIHE, OPTIONEN_FENSTER)
    if not dvol and not skew:
        return None
    return {"dvol": dvol, "skew": skew}


# WELCHE GROESSEN ES IN WELCHER ASSETKLASSE UEBERHAUPT GIBT (17.08.2026).
#
# DER FUND: Rolle G meldete bei JEDER Assetklasse drei Luecken -
#
#     aktien/PLTR:  Zu diesem Wert liegt keine Angabe vor: Finanzierungsrate.
#                   Zu diesem Wert liegt keine Angabe vor: Open Interest.
#                   Zu diesem Wert liegt keine Angabe vor: Anteil der Long-Konten.
#
# Eine Aktie hat keine Finanzierungsrate. Das ist keine Luecke, sondern
# eine Groesse, die es dort nicht gibt - und bei Aktien und Rohstoffen
# waren das DREI VON SECHS Saetzen, bei Themen-ETF alle drei.
#
# ⚠️ DIE RICHTIGE BEHANDLUNG STAND SCHON IM SELBEN CODE, zwei Zeilen
# weiter unten, nur je INSTRUMENT statt je ASSETKLASSE:
#
#     "NUR MELDEN, WENN SIE HIER HINGEHOERT. Beim Hebel ist ihre
#      Abwesenheit Absicht, kein Mangel - keine Angabe waere gelogen."
#
# Genau dieselbe Ueberlegung, eine Ebene hoeher.
#
# `open_interest_snapshot` wird ausschliesslich von `terminmarkt_job`
# (bis 12.09. vom `hebel_screening`) fuer Krypto gefuellt - fuer alles andere gibt es diese drei Zahlen
# nicht, und es wird sie auch nicht geben.
TERMINMARKT_GROESSEN = ("Open Interest", "Finanzierungsrate",
                        "Anteil der Long-Konten")
TERMINMARKT_KLASSEN = ("krypto", "kryptowaehrung")


def _luecke_melden(name: str, assetklasse: str | None) -> bool:
    """Gehoert diese Groesse in diese Assetklasse - fehlt sie also wirklich?

    ⚠️ FUER DIESE DREI IST DAS FAIL-CLOSED, UND ZWAR BEWUSST. Meine
    erste Fassung hatte "fail-open" in den Kommentar geschrieben und
    fail-closed gebaut; die Paketpruefung hat den Widerspruch gefunden.

    Richtig ist fail-closed: Open Interest, Finanzierungsrate und
    Long-Anteil stehen ausschliesslich in `open_interest_snapshot`, und
    die fuellt `terminmarkt_job` (bis 12.09. `hebel_screening`) NUR fuer
    Krypto. Eine neue Assetklasse
    bekaeme diese Zahlen also nicht dadurch, dass wir ihre Abwesenheit
    melden - die Meldung waere in jedem Fall Rauschen.

    FEHLT DIE KLASSE GANZ (None oder leer), wird gemeldet: dann ist
    unklar, worueber wir reden, und eine Luecke zu viel ist besser als
    eine verschwiegene."""
    if name not in TERMINMARKT_GROESSEN:
        return True
    kl = str(assetklasse or "").strip().lower()
    return (not kl) or kl in TERMINMARKT_KLASSEN


def lage(conn, symbol: str, assetklasse: str | None = None,
         instrument: str | None = None,
         jetzt: datetime | None = None) -> dict:
    """Die Positionierungslage - oder ein leeres dict, wenn nichts vorliegt.

    `assetklasse` entscheidet ueber den Boersenfluss und nichts sonst. Fehlt
    sie, bleibt er WEG - fail-closed. Ein Satz ueber Bitcoin-Bewegungen in der
    Beurteilung einer Aktie waere kein fehlender Fakt, sondern ein falscher,
    und P1 (Auftrag) schliesst ihn aus.

    FAIL-SOFT MIT VERMERK: was fehlt, steht unter `fehlt` und wird im Satzbau
    BENANNT. Ein stiller Ausfall waere hier besonders teuer, weil die ganze
    Rolle G auf diesen Zahlen steht - eine leere Antwort saehe aus wie
    'kein Einwand'.

    ⚠️⚠️ `jetzt` UND DIE LESEGRENZE (Schritt 54, 14.09.2026, Befund 2.452).
    Ist der juengste Terminmarkt-Wert aelter als 2 Stunden, steht er unter
    `veraltet` (mit letztem Stand) statt als Zahl in der Lage. `jetzt` ist fuer
    Nachspielungen an einer Sicherung; im Betrieb bleibt es leer."""
    sym = str(symbol or "").strip().upper()
    aus: dict = {"symbol": sym, "fehlt": []}
    jetzt = _jetzt(jetzt)

    def _melde(name: str) -> None:
        """Eine Luecke nur melden, wenn es die Groesse hier ueberhaupt
        gibt - siehe `_luecke_melden`."""
        if _luecke_melden(name, assetklasse):
            aus["fehlt"].append(name)

    def _frisch(name: str, reihe: list, spalte: str, boersen) -> list:
        """Die Reihe, wenn ihr juengster Wert innerhalb der Lesegrenze liegt.

        Sonst: leer, und die Groesse steht unter `veraltet` (hatte Daten) oder
        unter `fehlt` (nie Daten) - zwei verschiedene Saetze."""
        if reihe and _stunden(reihe[0][0], jetzt) <= LESEGRENZE_STUNDEN:
            return reihe
        stand = reihe[0][0] if reihe else _letzter_stand(
            conn, sym, spalte, jetzt, boersen)
        if stand is None:
            _melde(name)
        elif _luecke_melden(name, assetklasse):
            aus.setdefault("veraltet", []).append(
                {"groesse": name, "stand": stand.isoformat(),
                 "stunden": round(_stunden(stand, jetzt), 1)})
        return []

    oi = _frisch("Open Interest",
                 _zeitreihe(conn, sym, "open_interest", jetzt),
                 "open_interest", "binance")
    # ⚠️ NICHT MEHR ueber `_reihe`: die Finanzierungsrate stammt von KRAKEN
    # und stand bis zum 16.08. unter allen drei Boersenetiketten. Seit die
    # Etiketten stimmen, weiss genau eine Stelle, wo sie liegt - und sie
    # deckt den Uebergang von den Altzeilen mit ab.
    #
    # ⚠️ UND BEIM HEBEL GAR NICHT (17.08.2026, R-R2 je Instrument).
    #
    # Dieselbe Kraken-Zahl stand bis heute in BEIDEN Rollen: hier als
    # Perzentil und in `lagebeschreibung._finanzierung` als Anteil
    # positiver Perioden. Die Gegenpruefung pruefte damit mit etwas, das
    # der Gepruefte schon wusste - genau der Zustand, gegen den die zweite
    # Stufe gebaut wurde (17x LONG in 2.469 Pruefungen).
    #
    # ⚠️ DAS WAR KEINE ENTSCHEIDUNG, SONDERN EIN NEBENPRODUKT. Der Plan
    # (Kapitel 36.1, Schritt 2) sagt "Funding aus dem SPOT-Prompt
    # entfernen" und schweigt zum Hebel; der Modulkopf von
    # `_finanzierung` haelt fest, bei Spot gehoere es "jetzt zu GENAU
    # EINEM Modell" - ueber den Hebel steht dort nichts.
    #
    # WARUM G VERZICHTET UND NICHT BC: beim Hebel ist das Funding der
    # EINZIGE Fakt der entscheidenden Rolle, der nicht aus der Kerzenreihe
    # stammt. Naehme man es dort weg, stuende BC bei 100 % Chart - und
    # genau diese Unterernaehrung ist der gemessene Grundbefund (nur das
    # Momentum trennt Einstieg von Halten). G behaelt vier Groessen.
    #
    # BEI SPOT BLEIBT ES UMGEKEHRT: dort wurde Funding im August bewusst
    # aus BC entfernt, weil es in 63 % der Spot-Urteile zitiert wurde,
    # obwohl ein Spot-Kaeufer keine Finanzierung zahlt. Das war richtig.
    from database import db as _DB

    fund = [] if str(instrument or "") == "hebel" else [
        (z, float(v)) for z, v in (
            (_zeit(t), v) for t, v in _DB.lies_funding_reihe(
                conn, sym, seit=(jetzt - timedelta(
                    hours=VERGLEICHSZEITRAUM_STUNDEN)).isoformat(),
                bis=jetzt.isoformat(), mit_zeit=True))
        if z is not None and v is not None]
    if str(instrument or "") != "hebel":
        fund = _frisch("Finanzierungsrate", fund, "funding_rate",
                       ("kraken", "binance"))
    lang = _frisch("Anteil der Long-Konten",
                   _zeitreihe(conn, sym, "long_account_pct", jetzt),
                   "long_account_pct", "binance")

    if oi:
        aus["oi_jetzt"] = oi[0][1]
        # DER VERGLEICHSSTAND NACH DER UHR (Schritt 54): der Wert rund acht
        # Stunden vor dem juengsten, nicht die 32. Zeile. Fehlt er (nach einem
        # Ausfall, nach dem Neustart), wird das gesagt statt verschwiegen.
        ziel = oi[0][0] - timedelta(hours=OI_RUECKBLICK_STUNDEN)
        vergleich = _vergleichsstand(oi, ziel)
        if vergleich and vergleich[1]:
            aus["oi_aenderung_pct"] = round(
                100.0 * (oi[0][1] - vergleich[1]) / vergleich[1], 2)
            aus["oi_fenster_stunden"] = round(
                _stunden(vergleich[0], oi[0][0]), 1)
        else:
            aus["oi_ohne_vergleich"] = True

    if fund:
        werte = [v for _, v in fund]
        aus["funding_jetzt"] = werte[0]
        aus["funding_n"] = len(werte)
        # Dieselbe Mindestreihe wie beim Kontenanteil - der Fehler war dort
        # sichtbar, das Muster ist hier dasselbe.
        if len(werte) >= PERZENTIL_MINDESTREIHE:
            aus["funding_perzentil"] = _perzentil(werte, werte[0])

    if lang:
        werte = [v for _, v in lang]
        aus["long_anteil_pct"] = round(float(werte[0]), 1)
        aus["long_n"] = len(werte)
        if len(werte) >= PERZENTIL_MINDESTREIHE:
            aus["long_perzentil"] = _perzentil(werte, werte[0])

    div = _divergenz(conn, sym, jetzt) if oi else None
    if div:
        aus["divergenz"] = div

    # NUR FUER KRYPTO, und die Liste ist bewusst eng. "krypto" und "coin"
    # decken die Gruppenvokabeln ab, die die Kette fuehrt; alles andere - auch
    # ein unbekannter Wert - faellt heraus. Genau die Vokabelverwirrung
    # (`etf` gegen `themen_etf`) hat am 16.08. zwei Fakten stillgelegt.
    # AKTIEN: Leerverkaeufer und Insider. Beide sind SYMBOLSPEZIFISCH und
    # zaehlen als zwei verschiedene Arten - die eine misst, wer gegen den Wert
    # steht, die andere, was die Leute im Haus tun. Damit deckt die
    # Aktiengruppe als einzige G1 aus zwei symbolspezifischen Quellen.
    if str(assetklasse or "").lower() in ("aktien", "aktie"):
        si = _short_interest(conn, sym)
        if si:
            aus["short_interest"] = si
            aus["short_interest_perzentil"] = si["perzentil"]
        else:
            aus["fehlt"].append("Leerverkaufsposition")
        ins = _insider(conn, sym)
        if ins:
            aus["insider"] = ins
            # DER SCHLUESSEL, DEN `mindestkriterien` SUCHT. Auch eine Null ist
            # eine Angabe: "niemand hat gekauft" ist ein Fakt, kein Ausfall.
            aus["insider_kaeufe_90d"] = ins["kaeufe"]
        else:
            aus["fehlt"].append("Insidergeschaefte")

    # ROHSTOFFE: die Positionierung im Basiswert. Anders als der Boersenfluss
    # ist sie SYMBOLSPEZIFISCH - Gold, Silber, Kupfer und Erdgas haben je einen
    # eigenen Bericht. Damit deckt sie G1 UND G2.
    if str(assetklasse or "").lower() in ("rohstoffe", "rohstoff"):
        c = _cot(conn, sym)
        if c:
            aus["cot"] = c
            aus["cot_perzentil"] = c["perzentil"]
        eb = _etf_bestand(conn, sym)
        if eb:
            aus["etf_bestand"] = eb
        else:
            aus["fehlt_rahmen"] = (aus.get("fehlt_rahmen") or []) + [
                "Positionierung der grossen Fonds im Basiswert"]

    if str(assetklasse or "").lower() in ("krypto", "coin", "crypto"):
        fluss = _boersenfluss(conn)
        if fluss:
            aus["boersenfluss"] = fluss
        st = _stablecoin(conn)
        if st:
            aus["stablecoin"] = st
        op = _optionsmarkt(conn, sym)
        if op:
            aus["optionsmarkt"] = op
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

    # ⚠️ HIER STAND DAS MARKTREGIME - HERAUSGENOMMEN AM 16.08.2026 ABENDS.
    #
    # DER NUTZER HAT ES AN EINER ECHTEN MAIL GESEHEN, nicht an einer Messung:
    #
    #     EINWAND - die Positionierung spricht dagegen: Der Gesamtmarkt
    #     steht im Regime 'baer', seit 27 Tagen ununterbrochen.
    #
    # Das Modell griff aus sechs Faktensaetzen genau den EINEN heraus, der ein
    # Urteil enthaelt, und gab ihn als Begruendung zurueck - waehrend jeder
    # echte Positionierungsfakt daneben "im gewohnten Bereich" sagte. Die
    # Gegenpruefung stand damit nicht auf der Positionierung, sondern auf einem
    # Etikett, das wir selbst gerechnet und selbst hineingelegt hatten.
    #
    # NACHGEZAEHLT AM PRODUKTIONSBESTAND: `regime` ist in 2.549 von 2.549
    # `signals` und 1.819 von 1.819 `hebel_signals` gleich "baer". Ein Wert,
    # der sich nie aendert, kann nichts unterscheiden - er kann nur schieben.
    #
    # VIER EIGENE REGELN AUF EINMAL:
    #     R-T2  ein Etikett statt eines beschriebenen Sachverhalts
    #     R-T3  ein Werturteil, dem Pruefer fertig hingelegt
    #     R-T6  ein konstantes Feld
    #     P3    aus BTC-Kurs und Fear & Greed gerechnet - beides sieht Rolle A
    #           bereits, es ist UNSERE Ableitung und keine fremde Information
    #
    # UND DER FEHLER IST AKTENKUNDIG. `szenario_fakten.finde_konstanten` traegt
    # ihn seit Wochen im Docstring: *"`regime` war auf allen 1.022 Faellen
    # 'baer' - der Gegenpruefer las eine Konstante mit Richtungsaussage und kam
    # deshalb 1 von 1.022 Mal auf LONG."* Derselbe Feldname, dieselbe Wirkung.
    #
    # WARUM DER WAECHTER NICHT ANSCHLUG: `enthaelt_werturteile` und
    # `finde_konstanten` pruefen FELDNAMEN in einem dict. Rolle G bekommt
    # SAETZE. Der Waechter konnte es strukturell nicht sehen - dieselbe Luecke
    # wie zwischen `pruefe_fakten_bezugsgroessen` und
    # `pruefe_zahlen_in_prompts`. Deshalb prueft letzteres jetzt auch auf
    # Etiketten (N4) und auf ueber alle Symbole identische Saetze (N5).
    #
    # DIE URSPRUENGLICHE BEGRUENDUNG IST ENTFALLEN. Sie stand hier woertlich:
    # das Regime sei noetig, "weil sie sonst nur eine Quelle haette". Seit
    # heute hat Krypto Terminmarkt UND On-Chain, Aktien Leerverkaeufer UND
    # Insider. Der Grund war weg, das Feld war geblieben.
    return aus


def saetze(e: dict, nur_eigen: bool = False) -> list[str]:
    """Die Positionierung als Aussagen - fuer Rolle G.

    ⚠️ `nur_eigen=True` LAESST DEN RAHMEN WEG (Schritt 5, 01.09.2026).

    Dieses Modul mischt zwei Dinge, und es sagt das selbst: `fehlt` nennt,
    was diesem ASSET fehlt, `fehlt_rahmen` nennt, was dem UMFELD fehlt. Der
    Boersenfluss ist Rahmen - er misst Bitcoin-Zu- und -Abfluesse und gilt
    fuer den ganzen Markt.

    Fuer Rolle G ist das richtig: sie beurteilt die Lage. Fuer die
    FAKTENLAGE EINES ASSETS ist es falsch - dort stuende dann bei LINK und
    TAO woertlich *„Am 2026-08-31 flossen mehr Bitcoin auf die Boersen"*.
    Genau diesen Zustand meldet `simuliere_kette` seit dem 31.08. als
    bekannten Punkt G2: *„Rolle G urteilt auf BTC-weiter Grundlage."*

    ⚠️ Ihn beim Einspeisen mitzunehmen, haette einen bekannten Defekt in
    einen zweiten Kanal getragen. Deshalb dieser Schalter - und deshalb
    bleibt G unveraendert: der Rahmen gehoert dort hin, nur nicht hierher.

    JEDE ZAHL MIT IHREM MASSSTAB. "Die Finanzierungsrate liegt im 96.
    Perzentil der letzten 400 Messungen" traegt; "0.0312 %" traegt nicht."""
    if not e:
        return []
    z: list[str] = []

    if e.get("oi_aenderung_pct") is not None:
        # ⚠️ "UM 0.0 % GEFALLEN" STAND SO IN DER MAIL VOM 16.08. Bei einer
        # gerundeten Null gibt es keine Richtung; sie zu behaupten ist eine
        # Aussage, die die Zahl nicht hergibt.
        richtung = ("gestiegen" if e["oi_aenderung_pct"] > 0.05 else
                    "gefallen" if e["oi_aenderung_pct"] < -0.05 else "")
        # DIE BOERSE WIRD SEIT 16.08. GENANNT. Solange nur eine Zahl dastand,
        # war "der Terminmarkt" eine zulaessige Verkuerzung. Jetzt folgt ein
        # Satz, der Boersen beim Namen nennt - und eine unbeschriftete Zahl
        # daneben laesst offen, welche der drei gemeint ist. Genau die Sorte
        # Mehrdeutigkeit, die R-T1 mit "das Fenster nennen" ausschliesst.
        if nur_eigen:
            # ⚠️⚠️ GROEBER FUER DIE FAKTENLAGE - UND DAS IST GEMESSEN,
            # NICHT GESCHAETZT (Schritt 5, 01.09.2026).
            #
            # `anlass.fingerabdruecke` bildet den Abdruck ueber den
            # Faktentext. Steht dort eine Prozentzahl auf eine
            # Nachkommastelle, wechselt sie fast bei jedem Lauf - und
            # damit waere JEDE Frage eine neue. Genau davor warnt der Kopf
            # von `anlass.py` beim Lagebild: *„naehme man es mit, waere
            # fast jede Frage neu und der Filter wirkungslos."*
            #
            # Gemessen an 2.988 Messpunkten je Symbol aus
            # `open_interest_snapshot` (NB-Stand 29.08.), Wechselrate des
            # Satzes zwischen aufeinanderfolgenden Messungen:
            #
            #     Auflösung            BTC     ETH    LINK     TAO
            #     0,1 % (fein)        68,2 %  71,1 %  74,3 %  73,7 %   <- unbrauchbar
            #     Stufen 1/3/8 %       5,0 %   7,5 %   7,3 %   6,7 %   <- gewaehlt
            #     nur 3 % (grob)       0,2 %   0,4 %   0,6 %   0,6 %   <- fast nie
            #
            # Mit den Stufen wird etwa jeder fuenfzehnte Lauf durch den
            # Terminmarkt zu einer neuen Frage. Das ist ein Anlass; 70 %
            # waeren Rauschen und 0,4 % waere kein Melder.
            #
            # ⚠️ ROLLE G BEHAELT DIE FEINE ZAHL. Sie beurteilt die Lage und
            # bildet keinen Fingerabdruck; ihre Messreihe bliebe sonst
            # ohne Not gebrochen.
            _a = abs(e["oi_aenderung_pct"])
            _n = ("praktisch unveraendert" if _a < 1.0
                  else "leicht " + richtung if _a < 3.0
                  else "deutlich " + richtung if _a < 8.0
                  else "stark " + richtung)
            z.append(
                f"Die offenen Kontrakte am Terminmarkt sind auf Binance in "
                f"den letzten {S.de(e['oi_fenster_stunden'], 0)} Stunden "
                f"{_n}.")
        elif richtung:
            z.append(
                f"Die offenen Kontrakte am Terminmarkt sind auf Binance in "
                f"den letzten {S.de(e['oi_fenster_stunden'], 0)} Stunden um "
                f"{S.de(abs(e['oi_aenderung_pct']), 1)} % {richtung}.")
        else:
            z.append(
                f"Die offenen Kontrakte am Terminmarkt sind auf Binance in "
                f"den letzten {S.de(e['oi_fenster_stunden'], 0)} Stunden "
                "praktisch unveraendert geblieben.")

    # DIE BOERSEN NEBENEINANDER - OHNE DEUTUNG (16.08.2026).
    #
    # HIER STEHT BEWUSST KEIN HINWEIS, WAS EINE GROSSE SPANNE BEDEUTET. Beim
    # Funding gibt es einen (Extremwerte gehen Umkehrungen voraus), und er ist
    # durch die Praxisliteratur gedeckt. Fuer die Boersendivergenz ist er das
    # NICHT: die Literatur fuehrt die Spanne zwischen Boersen als
    # Arbitrage-Groesse, nicht als Richtungssignal. Eine Deutung waere hier
    # meine Vermutung - Rang 3 der Eignungsleiter (P2) und damit nicht
    # aufnahmefaehig. Der Fakt steht, die Schlussfolgerung zieht das Modell.
    elif e.get("oi_ohne_vergleich"):
        # SCHRITT 54: der juengste Wert ist frisch, aber der Stand von vor acht
        # Stunden fehlt (nach einem Ausfall, in den ersten Stunden nach dem
        # Neustart). Schweigen saehe aus wie ,keine Bewegung'.
        z.append(
            f"Wie sich die offenen Kontrakte am Terminmarkt in den letzten "
            f"{S.de(OI_RUECKBLICK_STUNDEN, 0)} Stunden veraendert haben, laesst "
            f"sich noch nicht sagen - es fehlt der Vergleichsstand.")

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
        # ⚠️ "UNEINHEITLICH" BEI EINER SPANNE IM 7. PERZENTIL stand am
        # 16.08. in der Mail - also "ungewoehnlich EINIG" laut Messwert und
        # "uneinheitlich" laut Wortwahl. Das Wort richtet sich jetzt nach dem
        # Perzentil, nicht nach dem blossen Vorhandensein einer Differenz.
        if abs(d["spanne_pp"]) < 0.1 or d["spanne_perzentil"] <= EXTREM_UNTEN:
            z.append("Die Boersen entwickeln sich dabei weitgehend "
                     "gleichlaeufig.")
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

    elif e.get("funding_n") and e.get("funding_jetzt") is not None:
        # SCHRITT 54: nach einem Ausfall laeuft die Reihe neu an. Beim
        # Kontenanteil stand dafuer schon immer ein Satz; hier fiel die
        # Finanzierungsrate bis zur 30. Messung kommentarlos weg - dieselbe
        # Stille, die 2.452 unsichtbar gemacht hat.
        z.append(
            f"Die Finanzierungsrate laesst sich noch nicht einordnen - die "
            f"eigene Reihe hat erst {e.get('funding_n', 0)} von "
            f"{PERZENTIL_MINDESTREIHE} noetigen Messungen.")

    if e.get("long_anteil_pct") is not None:
        lp = e.get("long_perzentil")
        # ⚠️ "67 % DER KONTEN STEHEN LONG; DAS IST DAS 0. PERZENTIL -
        # AUSSERGEWOEHNLICH WENIGE" stand am 16.08. in der Mail. Rechnerisch
        # richtig und trotzdem unlesbar: die rohe Zahl klingt nach viel, die
        # Einordnung sagt wenig, und beides steht in einem Satz. Das Perzentil
        # traegt die Aussage - die rohe Zahl ist genau die nackte Zahl, gegen
        # die R-T5 geschrieben wurde.
        satz = "Der Anteil der Konten auf der Kaufseite"
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
            satz += (f" steht im {lp}. Perzentil der letzten "
                     f"{e.get('long_n', 0)} Messungen - {wie}")
        else:
            # ⚠️ DEN GRUND NENNEN, nicht nur das Fehlen. "Laesst sich nicht
            # einordnen" liest sich wie ein Datenausfall; hier ist es eine
            # zu kurze eigene Reihe, und das ist etwas anderes.
            satz += (f" laesst sich noch nicht einordnen - die eigene Reihe "
                     f"hat erst {e.get('long_n', 0)} von "
                     f"{PERZENTIL_MINDESTREIHE} noetigen Messungen")
        z.append(satz + ".")

    # DIE ZWEITE INFORMATIONSART. Kein Wort ueber Richtung oder Folgen: dass
    # Zufluesse Verkaufsdruck ANKUENDIGEN, ist eine gaengige Lesart und in
    # unseren Daten nie gemessen - also P2 Rang 3 und nicht aufnahmefaehig.
    # `onchain.py` nennt sie im Feldkommentar "potenziell Verkaufsdruck"; genau
    # dieses "potenziell" gehoert nicht in einen Faktensatz.
    si = e.get("short_interest")
    if si and si.get("perzentil") is not None:
        ps = si["perzentil"]
        wie = ("aussergewoehnlich lang" if ps >= EXTREM_OBEN else
               "aussergewoehnlich kurz" if ps <= EXTREM_UNTEN else
               "im gewohnten Bereich")
        z.append(
            "Die Eindeckungsdauer sagt, wie viele Handelstage die "
            "Leerverkaeufer braeuchten, um ihre Positionen zurueckzukaufen.")
        z.append(
            f"Zum Stichtag {si['datum']} steht sie im {ps}. Perzentil der "
            f"letzten {si['n']} Meldeperioden - {wie}.")

    ins = e.get("insider")
    if ins:
        # KEINE DEUTUNG (R-T3, P2). Dass Insiderverkaeufe ein schlechtes
        # Zeichen seien, ist die gaengige Lesart - und falsch verkuerzt:
        # Fuehrungskraefte bekommen Aktien als Verguetung und verkaufen sie
        # planmaessig. Der Modulkopf von `sec_edgar.py` sagt das ausdruecklich.
        # Gezaehlt wird, gedeutet nicht.
        # BEIDE SEITEN IMMER NENNEN. Die erste Fassung liess die Kaufseite
        # weg, wenn sie null war - und genau die NULL ist die Aussage:
        # gemessen ueber 730 Tage kaufte bei PLTR dreimal jemand und bei
        # VST keinmal. "55 Verkaeufe" allein liest sich wie eine Haelfte,
        # deren andere jemand vergessen hat.
        # DIE MEHRZAHL WIRD UEBERGEBEN, NICHT GEBILDET. Ein angehaengtes "e"
        # machte aus "Kauf" ein "Kaufe" und aus "Verkauf" ein "Verkaufe";
        # dazu hiess es "kein Kauf" statt "keinen Kauf". Ein Faktensatz, der
        # holpert, liest sich wie ein Fehler - und genau das soll er nicht.
        def _seite(anzahl: int, einzahl: str, mehrzahl: str) -> str:
            if anzahl == 0:
                return f"keinen {einzahl}"
            return f"{anzahl} {einzahl}" if anzahl == 1 else f"{anzahl} {mehrzahl}"

        z.append(
            f"Insider meldeten in den letzten {INSIDER_FENSTER_TAGE} Tagen "
            f"{_seite(ins['kaeufe'], 'Kauf', 'Kaeufe')} und "
            f"{_seite(ins['verkaeufe'], 'Verkauf', 'Verkaeufe')} am offenen "
            "Markt - Zuteilungen und Optionsausuebungen zaehlen nicht mit.")

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

    # ⚠️ RAHMEN, NICHT ASSET: der Boersenfluss misst Bitcoin fuer den ganzen
    # Markt. Bei `nur_eigen` faellt er weg - siehe Kopf.
    f = None if nur_eigen else e.get("boersenfluss")
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

    eb = e.get("etf_bestand")
    if eb:
        p_ = eb["perzentil"]
        wie = ("aussergewoehnlich stark" if p_ >= EXTREM_OBEN else
               "aussergewoehnlich schwach" if p_ <= EXTREM_UNTEN else
               "im gewohnten Bereich")
        richtung = ("aufgebaut" if eb["aenderung_pct"] > 0 else "abgebaut")
        # KEINE DEUTUNG. Dass ein Bestandsaufbau steigende Preise
        # ankuendigt, ist gaengige Lesart und bei uns nie gemessen.
        z.append(
            f"Die in boersengehandelten Fonds physisch hinterlegte Menge "
            f"dieses Rohstoffs wurde in den letzten {eb['fenster']} Tagen "
            f"{richtung}.")
        z.append(
            f"Wie stark, steht im {p_}. Perzentil der letzten {eb['n']} "
            f"Messungen - {wie}.")

    # ⚠️⚠️ RAHMEN, NICHT ASSET - und UNGEMESSEN (18.09.2026, 2.459-ungemessen).
    #
    # Der Kommentar in `rollen_lauf` sagt, an Rolle BC gingen ,NUR DIE
    # ASSET-EIGENEN SAETZE`. Dieser hier und der Optionsmarkt-Satz unten sind
    # aber durchgerutscht (2.457-n2). Heute faellt das nicht auf, weil beide
    # Reihen zu kurz sind und gar kein Satz entsteht - ab etwa Mitte Oktober
    # (2.453-alterlos) waeren sie ploetzlich im BC-Prompt, ohne Commit, ohne
    # neuen Prompt-Stand und ohne Entscheidung.
    #
    # ⚠️ KEINE STILLLEGUNG, SONDERN DIE REGEL: eine Groesse, die nie gegen
    # eine Folgebewegung gemessen wurde, gehoert nicht in die Modelleingabe
    # (R-R4/P1: Verfuegbarkeit ist kein Aufnahmegrund; R-T9: was dasteht,
    # wiegt). Beide sind jetzt im Kandidatenblatt registriert und werden in
    # Phase 3 gemessen; traegt eine, kommt sie in Schritt 33 bewusst hinein.
    #
    # ROLLE G BLEIBT UNVERAENDERT - sie beurteilt die LAGE und braucht den
    # Rahmen. Nur die Faktenlage eines einzelnen Assets braucht ihn nicht.
    st = None if nur_eigen else e.get("stablecoin")
    if st:
        p_ = st["perzentil"]
        wie = ("aussergewoehnlich viel" if p_ >= EXTREM_OBEN else
               "aussergewoehnlich wenig" if p_ <= EXTREM_UNTEN else
               "im gewohnten Bereich")
        # KEINE DEUTUNG. Dass viel Stablecoin-Kapital "Kaufkraft" sei, ist
        # eine gaengige Lesart und bei uns nie gemessen (P2 Rang 3).
        z.append(
            "Das insgesamt im Kryptomarkt liegende Stablecoin-Kapital "
            f"steht im {p_}. Perzentil der letzten {st['n']} Messungen "
            f"- {wie}.")

    op = ({} if nur_eigen else e.get("optionsmarkt")) or {}
    dvol = op.get("dvol")
    if dvol:
        p_ = dvol["perzentil"]
        wie = ("aussergewoehnlich hoch" if p_ >= EXTREM_OBEN else
               "aussergewoehnlich niedrig" if p_ <= EXTREM_UNTEN else
               "im gewohnten Bereich")
        z.append(
            "Am Optionsmarkt preisen die Haendler die Schwankung der "
            f"naechsten Wochen im {p_}. Perzentil der letzten "
            f"{dvol['n']} Messungen ein - {wie}.")
    skew = op.get("skew")
    if skew:
        p_ = skew["perzentil"]
        # DIE RICHTUNG QUALITATIV (R-T10): ein negativer Skew heisst,
        # Absicherung nach unten kostet mehr als Spekulation nach oben.
        seite = ("Absicherung nach unten" if skew["wert"] < 0
                 else "Spekulation nach oben")
        wie = ("aussergewoehnlich ausgepraegt" if p_ >= EXTREM_OBEN else
               "aussergewoehnlich schwach" if p_ <= EXTREM_UNTEN else
               "im gewohnten Bereich")
        z.append(
            f"Dabei ist {seite} die teurere Seite; wie deutlich, steht im "
            f"{p_}. Perzentil der letzten {skew['n']} Messungen - {wie}.")

    # ⚠️ AUCH DIE LUECKENMELDUNG ZUM RAHMEN faellt bei `nur_eigen` weg -
    # sie sagt etwas ueber den MARKT, nicht ueber dieses Asset. Sie stehen
    # zu lassen waere dieselbe Vermischung in kleiner Form.
    for f in ([] if nur_eigen else (e.get("fehlt_rahmen") or [])):
        # ANDERER WORTLAUT ALS BEI `fehlt`: es fehlt nichts ZU DIESEM WERT,
        # sondern eine Angabe ueber den Markt. Verschwiegen wird trotzdem
        # nichts - "fail-soft ist fail-silent".
        z.append(f"Zum Gesamtmarkt liegt keine Angabe vor: {f}.")

    # ⚠️⚠️ VERALTET IST NICHT DASSELBE WIE FEHLT (Schritt 54, Befund 2.452).
    # Bis zum 14.09. gab es diesen Fall nicht - ein alter Wert wurde als
    # aktueller ausgegeben. Jetzt steht er als eigener Satz da, mit dem Alter,
    # damit das Modell weder eine alte Zahl glaubt noch ,keine Angabe' fuer
    # ,nie vorhanden' haelt. Gleicher Stand = ein Satz.
    _veraltet: dict = {}
    for v in (e.get("veraltet") or []):
        _veraltet.setdefault((v.get("stand") or "")[:16], []).append(v)
    for _stand, _gruppe in _veraltet.items():
        _h = max(float(v.get("stunden") or 0) for v in _gruppe)
        _alter = (f"{int(_h // 24)} Tage" if _h >= 48 else
                  f"{int(_h)} Stunden" if _h >= 2 else "rund 2 Stunden")
        _namen = [v["groesse"] for v in _gruppe]
        _liste = (_namen[0] if len(_namen) == 1 else
                  ", ".join(_namen[:-1]) + " und " + _namen[-1])
        z.append(f"Zu diesem Wert liegt keine aktuelle Angabe vor: {_liste} - "
                 f"der letzte Stand ist {_alter} alt.")

    for f in (e.get("fehlt") or []):
        # BENANNT, NICHT VERSCHWIEGEN. Ohne diesen Satz liest das Modell die
        # Abwesenheit als "unauffaellig" - derselbe Fehler, den die
        # Bestandserhebung am 16.08. bei acht Assets gefunden hat.
        z.append(f"Zu diesem Wert liegt keine Angabe vor: {f}.")
    return z
