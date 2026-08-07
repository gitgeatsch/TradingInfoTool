"""Signal-Pipeline fuer Rohstoff-ETCs (2026-07-18, Multi-Asset-Roadmap Phase 2) -
mirror des Kontrollflusses von agent/aktien/pipeline.py::generate_signal() (Gate ->
Regime -> Technik -> Risk-Gate -> Makro-Ueberlagerung+Positionierung -> Facts -> LLM
-> Post-Check -> Signal), siehe agent/rohstoff/analyst.py Modul-Docstring fuer die
Architektur-Begruendung.

Wiederverwendet direkt (kein Duplikat): dieselben Bausteine wie die Aktien-
Pipeline (risk_gate.pre_check()/post_check(), compute_current_regime(),
build_technical_snapshot()/summarize_confluence(), Bitpanda-Listing-Check)."""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone

import numpy as np

import agent.kategorie_thesen as kategorie_thesen
import config
import database.db as db
from agent.krypto.backward_tracking import compute_win_rate_fact
from agent.krypto.gegenpruefung import (
    baue_fakten as baue_zai_fakten,
    baue_objektive_fakten as baue_zai_objektive_fakten,
    fuehre_beide_calls_im_hintergrund,
    richtung_aus_action,
)
from agent.krypto.llm_provider import llm_model_label
from agent.krypto.makro_analog import get_cached_makro_analog_fact
from agent.krypto.pipeline import (
    MIN_GATE_INDICATORS_AVAILABLE, compute_current_regime, eur_aus_usd, log_eur_abweichungen,
)
from agent.krypto.risk_gate import post_check, pre_check
from agent.rohstoff.analyst import (
    AnalystResponseInvalid,
    build_facts,
    call_llm_for_signal,
)
from api.cftc_cot import get_cot_snapshot
from api.macro import get_fred_latest
from agent.rekonstruktion import QUELLE_REKONSTRUIERT, rekonstruiere
from api.yfinance_history import get_full_ohlc_history
from database.models import Signal
from indicators.calculations import build_technical_snapshot, latest_value, summarize_confluence
from staleness import is_price_stale

logger = logging.getLogger(__name__)

PIPELINE_VERSION = "1"

# Wie bei Aktien: Boersen-/Terminmarkt-Handelszeiten, kein 24/7-Handel wie Krypto.
_ROHSTOFF_HISTORY_STALE_THRESHOLD_TAGE = 5

# ETC-Symbol -> CFTC-COT-Rohstoff-Schluessel (api/cftc_cot.py::COT_MARKET_NAMES).
# Manuell gepflegt statt automatisch abgeleitet (Symbol/Name-Heuristik waere
# fragiler) - bei einem neuen Rohstoff-ETC hier ergaenzen.
SYMBOL_ZU_COT_ROHSTOFF = {
    "OD7N": "silber",
    "OD7H": "gold",
    "OD7C": "kupfer",
    "OD7L": "erdgas",
}

# Live-Fund (2026-07-18, Verifikation dieser Pipeline): yfinance liefert fuer die
# duenn gehandelten WisdomTree-ETC-Boersennotierungen selbst (asset.yfinance_symbol,
# z.B. "OD7H.SG") KEINE .history()-Daten - nur fast_info (aktueller Preis)
# funktioniert, exakt dieselbe Einschraenkung, die 2026-07-09 bereits fuer OD7N/3QSS
# dokumentiert wurde (siehe Memory project_multi_asset_yfinance_symbols.md). Fix:
# technische Analyse (EMA/MACD/RSI/Bollinger/ATR/Fibonacci/S&R) wird stattdessen aus
# dem liquiden, kontinuierlichen Futures-Kontrakt abgeleitet, den das ETC nachbildet -
# 25+ Jahre taegliche Historie live verifiziert (GC=F/SI=F/HG=F/NG=F). Der eigentliche
# EXECUTION-Preis (preis.usd/eur in den Facts, Positionsgroessen-Berechnung) bleibt
# UNVERAENDERT der echte ETC-Kurs aus price_cache (YFinanceClient.fast_info, laeuft
# bereits ueber den bestehenden Preis-Refresh-Job). Kleine Tracking-Differenzen
# (Rollkosten, Waehrungsabsicherung, Emittenten-Marge) zwischen Future und ETC sind
# dadurch moeglich - im Prompt-Disclaimer explizit benannt (siehe build_facts()).
SYMBOL_ZU_FUTURES_TICKER = {
    "OD7N": "SI=F",
    "OD7H": "GC=F",
    "OD7C": "HG=F",
    "OD7L": "NG=F",
}

# FRED-Serien fuer die Makro-Ueberlagerung (siehe agent/rohstoff/analyst.py Regel 9) -
# DTWEXBGS wird bereits fuer den Makro-Analog-Vergleich abgerufen (agent/krypto/
# makro_analog.py), hier separat und live (nicht aus dem Cache), da die Rohstoff-
# Pipeline (wie die Aktien-Pipeline) bislang nur bei manuellem Klick laeuft.
_FRED_SERIES_MAKRO_UEBERLAGERUNG = {
    "realrendite_10j_prozent": "DFII10",
    "dxy_proxy": "DTWEXBGS",
    "industrieproduktion_index": "INDPRO",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _fixed_signal(symbol: str, action: str, gate_passed: bool, gate_reason: str | None, facts: dict | None = None) -> Signal:
    return Signal(
        symbol=symbol,
        created_at=_now(),
        action=action,
        gate_passed=gate_passed,
        gate_reason=gate_reason,
        risk_veto=False,
        facts_json=json.dumps(facts or {}, ensure_ascii=False),
        pipeline_version=PIPELINE_VERSION,
    )


def _is_rohstoff_history_stale(last_date: str | None) -> bool:
    if last_date is None:
        return True
    last = datetime.fromisoformat(last_date).date()
    today = datetime.now(timezone.utc).date()
    return (today - last).days > _ROHSTOFF_HISTORY_STALE_THRESHOLD_TAGE



def _futures_symbol(symbol: str) -> str:
    """Eigenes Symbol fuer die Futures-Referenzreihe - siehe
    _ensure_ohlc_backfilled() fuer die Begruendung."""
    return f"_ROHSTOFF_FUTURES_{symbol}"


def _rekonstruiere_etc_reihe(conn, asset, referenz_punkte) -> None:
    """ETC-Reihe aus der Futures-Referenz und dem aktuellen Preis (2026-08-06).

    NOETIG, WEIL ES KEINE ANDERE GIBT. Der Abruf-Test vom 06.08. hat bestaetigt,
    was YFINANCE_HISTORY_UNRELIABLE_TICKERS seit dem 20.07. festhaelt: alle vier
    Rohstoff-ETCs liefern ueber yfinance KEINE Historie, nur einen aktuellen
    Preis. Ohne Reihe hat eine gehaltene Position keinen Tageswert und faellt
    aus der Portfolio-Bewertung.

    VERFAHREN: die Futures-Reihe liefert die Form, der aktuelle ETC-Preis die
    Hoehe. Gegen die echten Signal-Entries geprueft (06.08.) trifft die
    Rekonstruktion auf -3,3 % / -1,4 % / +0,2 %, wobei die Abweichung zum
    Ankertag hin schrumpft - das erwartete Roll- und Gebuehrendrift-Muster.
    Zum Vergleich: die vorherige Vermischung lag um den Faktor 5,49 daneben.

    GRENZE, die zu jeder Verwendung gehoert: Rollkosten und Gebuehren fehlen.
    Bei Gold und Silber ist das klein, bei ERDGAS (OD7L) notorisch gross. Die
    Reihe taugt fuer kurze Horizonte, nicht fuer Monate - deshalb wird sie als
    `quelle='rekonstruiert'` markiert und ist damit ausschliessbar.
    """
    try:
        snap = db.get_latest_prices(conn).get(asset.symbol)
        anker = getattr(snap, "price_usd", None) if snap else None
        if not anker or anker <= 0:
            logger.info("Keine ETC-Rekonstruktion fuer %s - kein aktueller Preis als Anker",
                        asset.symbol)
            return
        referenz = [{"date": p.date, "close": p.close, "high": p.high, "low": p.low}
                    for p in referenz_punkte]
        punkte = rekonstruiere(asset.symbol, "USD", referenz, anker_preis=anker)
        if not punkte:
            logger.warning("ETC-Rekonstruktion fuer %s ergab keine Punkte", asset.symbol)
            return
        db.upsert_ohlc_points(conn, punkte, quelle=QUELLE_REKONSTRUIERT)
        logger.info("ETC-Reihe fuer %s rekonstruiert: %d Punkte, Anker %.4f USD "
                    "(quelle=rekonstruiert, Rollkosten und Gebuehren NICHT enthalten)",
                    asset.symbol, len(punkte), anker)
    except Exception:
        logger.exception("ETC-Rekonstruktion fuer %s fehlgeschlagen - Signal laeuft "
                         "ohne eigene Reihe weiter", asset.symbol)


def _ensure_ohlc_backfilled(conn, asset) -> None:
    """Fetcht die OHLC-Historie ueber den liquiden Futures-Ticker (siehe
    SYMBOL_ZU_FUTURES_TICKER-Docstring), gespeichert unter asset.symbol -
    get_full_ohlc_history()s ticker/symbol-Trennung ist genau dafuer gedacht."""
    # Die Wache fragt die FUTURES-Reihe, nicht asset.symbol (2026-08-06). Unter
    # asset.symbol liegt seit der Trennung die REKONSTRUIERTE Reihe - und vor der
    # Trennung lag dort die alte, falsch beschriftete Futures-Historie. In beiden
    # Faellen haette eine Wache auf asset.symbol einen frischen Stand gemeldet und
    # den Abruf uebersprungen: die Futures-Reihe waere unter ihrem neuen Symbol nie
    # entstanden, und die technische Analyse waere dauerhaft auf den Rueckfallpfad
    # gelaufen. Genau die Umstellung, die der Fix bewirken soll, haette sich damit
    # selbst blockiert.
    futures_ticker = SYMBOL_ZU_FUTURES_TICKER.get(asset.symbol)
    if futures_ticker is None:
        logger.warning("Kein Futures-Ticker fuer %s hinterlegt - keine technische Historie moeglich", asset.symbol)
        return
    # Die Futures-Reihe bekommt ein EIGENES Symbol (2026-08-06) - dasselbe
    # Muster, das agent/themen_etf/pipeline.py fuer seinen SPY-Benchmark schon
    # nutzt (_THEMEN_ETF_BENCHMARK_SPY).
    #
    # WARUM DAS GEAENDERT WURDE. Bis heute landete die Futures-Historie unter
    # dem ETC-Symbol. Die Absicht war richtig - der Future hat die liquide,
    # lueckenlose Reihe fuer die technische Analyse -, die Ablage nicht: alles
    # Nachgelagerte hielt die Reihe fuer den ETC. Ein OD7C-Signal mit Entry
    # 34,63 wurde gegen eine Kupfer-Futures-Reihe bei 6,30 USD/lb bewertet, was
    # (34,63 - 6,30) / 1,37 = 20,7 R ergab - dieser eine Trade war die gesamte
    # Evidenz der Assetklasse Rohstoffe.
    #
    # ZWEI GETRENNTE FRISCHE-BEGRIFFE (Korrektur 2026-08-06, Betriebsfund). Die
    # Futures-Reihe und die rekonstruierte ETC-Reihe veralten NICHT nach
    # derselben Regel, und sie an denselben Guard zu haengen war der Fehler:
    #
    #   Futures : veraltet, wenn der letzte Handelstag zu lange her ist
    #   ETC     : haengt an einem ANKERPREIS, der sich JEDEN Tag bewegt
    #
    # Der erste Entwurf sprang bei frischer Futures-Reihe sofort heraus - und
    # uebersprang damit die Rekonstruktion gleich mit. Auf dem Entwicklungsstand
    # fiel das nicht auf, weil die Futures-Reihe dort veraltet war und der Abruf
    # ohnehin lief. Im Betrieb war sie frisch, der frueher Ausstieg griff, und
    # die vier ETC-Reihen entstanden NIE: im Export 91 von 91 Tagen ohne Kurs.
    #
    # Deshalb: der ABRUF haengt an der Futures-Frische, die REKONSTRUKTION
    # laeuft bei jedem Aufruf. Sie kostet keinen Netzwerkzugriff - die Referenz
    # steht bereits in der DB.
    last_date = db.get_last_ohlc_date(conn, _futures_symbol(asset.symbol), "USD")
    if last_date is None or _is_rohstoff_history_stale(last_date):
        ohlc_points = get_full_ohlc_history(futures_ticker, _futures_symbol(asset.symbol), "USD")
        if ohlc_points:
            db.upsert_ohlc_points(conn, ohlc_points)

    referenz = db.get_ohlc_history(conn, _futures_symbol(asset.symbol), "USD")
    if referenz:
        _rekonstruiere_etc_reihe(conn, asset, referenz)
    else:
        logger.warning("Keine Futures-Reihe fuer %s - ETC-Reihe kann nicht rekonstruiert "
                       "werden, die Position bleibt ohne Tageswert", asset.symbol)


def _load_ohlc(conn, symbol: str):
    ohlc_history = db.get_ohlc_history(conn, symbol, "USD")
    last_date = ohlc_history[-1].date if ohlc_history else None
    dates = np.array([o.date for o in ohlc_history])
    closes = np.array([o.close for o in ohlc_history], dtype=float)
    return dates, closes, ohlc_history, last_date


# JIT-Historie-Nachladen (2026-07-27, Grundsatzfix Teil 2, gleiches Muster wie
# agent/krypto/pipeline.py::jit_refresh_asset_historie()) - die Rohstoff-Pipeline
# hatte bisher GAR KEINEN Scheduler-Job, nur den lazy _ensure_ohlc_backfilled()-
# Aufruf oben (nur bei bereits >5 Tage veralteter Historie) - strukturell
# schlechter als das urspruengliche Krypto-Staleness-Problem. Kein CoinGecko-
# aehnliches Monatskontingent bei yfinance zu schonen - der Burst-Schutz dient
# nur dem Schutz gegen Mehrfachanfragen innerhalb eines Allocator-/Batch-Zyklus.
# Laedt bewusst vom Futures-Ticker (USD) - die Reskalierung auf die ETC-
# Preisebene (_rescale_ohlc_zum_etc_kurs()) UND das Zurueckschreiben (Commit 1,
# oben in generate_signal()) passieren erst NACH diesem Aufruf.
JIT_REFRESH_MIN_ABSTAND_MINUTEN = 60

_jit_letzter_versuch: dict[str, datetime] = {}
_jit_lock = threading.Lock()


def _jit_burst_schutz_pruefen(symbol: str) -> bool:
    now = datetime.now(timezone.utc)
    with _jit_lock:
        letzter = _jit_letzter_versuch.get(symbol)
        if (
            letzter is not None
            and (now - letzter).total_seconds() < JIT_REFRESH_MIN_ABSTAND_MINUTEN * 60
        ):
            return False
        _jit_letzter_versuch[symbol] = now
        return True


def jit_refresh_ohlc(conn, asset) -> None:
    """P-10: ein Fehlschlag darf die Signal-Erzeugung nicht kippen - es wird
    dann einfach mit der bereits gespeicherten (ggf. staleren) Futures-Historie
    weitergearbeitet."""
    cfg = config.load_config()
    if not cfg.get("datenquellen", {}).get("marktdaten_wertpapiere", {}).get(
        "jit_historie_refresh_aktiv", True
    ):
        return
    futures_ticker = SYMBOL_ZU_FUTURES_TICKER.get(asset.symbol)
    if futures_ticker is None or not _jit_burst_schutz_pruefen(asset.symbol):
        return
    try:
        ohlc_points = get_full_ohlc_history(futures_ticker, asset.symbol, "USD")
        if ohlc_points:
            db.upsert_ohlc_points(conn, ohlc_points)
    except Exception as exc:
        logger.info("JIT-Historie-Refresh (yfinance/Futures) für %s fehlgeschlagen: %s", asset.symbol, exc)


def _rescale_ohlc_zum_etc_kurs(closes: np.ndarray, ohlc_history: list, etc_preis_usd: float | None):
    """Die gespeicherte OHLC-Historie stammt vom Futures-Kontrakt (siehe
    SYMBOL_ZU_FUTURES_TICKER-Docstring), nicht vom ETC selbst - Futures- und ETC-
    Kurs liegen auf VOELLIG unterschiedlichen absoluten Preisskalen (z.B. Gold-
    Future ~4000 USD/Unze vs. ein Bruchteils-ETC bei ~18 USD). Ohne Korrektur
    waeren EMA/Bollinger/ATR/Support-Resistance/Fibonacci-Level absolute Preis-
    Level auf der FALSCHEN Skala - eine vom LLM daraus abgeleitete Stop-Loss-Zone
    waere um Groessenordnungen falsch. Fix: die GESAMTE Historie wird mit einem
    EINZIGEN, heute gueltigen Skalierungsfaktor (ETC-Kurs / letzter Futures-Kurs)
    multipliziert, bevor sie in build_technical_snapshot() geht - technische
    MUSTER (Trendrichtung, Support/Resistance-Abstaende in Prozent, Crossover-
    Zeitpunkte) bleiben dabei unveraendert, nur die absolute Preisachse wird auf
    die ETC-Groessenordnung gehoben. RSI ist ohnehin skaleninvariant (Verhaeltnis
    von Gewinn-/Verlust-Mittelwerten), MACD/EMA/Bollinger/ATR sind lineare
    Funktionen des Preises und werden durch eine konstante Multiplikation korrekt
    mitskaliert. Gibt (closes, ohlc_history) UNVERAENDERT zurueck, wenn
    etc_preis_usd fehlt oder die Historie leer ist (P-10 - dann bleibt die
    Skalen-Diskrepanz bestehen, aber der Aufrufer bekommt keinen stillen Fehler)."""
    if etc_preis_usd is None or len(closes) == 0 or closes[-1] <= 0:
        return closes, ohlc_history
    faktor = etc_preis_usd / closes[-1]
    skaliert_closes = closes * faktor
    skaliert_history = [
        type(o)(
            symbol=o.symbol, currency=o.currency, date=o.date,
            open=o.open * faktor, high=o.high * faktor, low=o.low * faktor, close=o.close * faktor,
            volume=o.volume, fetched_at=o.fetched_at,
        )
        for o in ohlc_history
    ]
    return skaliert_closes, skaliert_history


def _fetch_makro_ueberlagerung(fred_api_key: str | None) -> dict | None:
    """P-10: ein fehlgeschlagener Einzel-Call blockiert nicht die anderen - jede
    FRED-Serie wird separat versucht (mirror api/macro.py::get_all_fred_rates()).
    Gibt None zurueck, wenn KEIN FRED_API_KEY gesetzt ist (Fakt fehlt dann
    komplett statt einer leeren/irrefuehrenden Huelle)."""
    if not fred_api_key:
        return None
    werte: dict[str, float | None] = {}
    for feld, series_id in _FRED_SERIES_MAKRO_UEBERLAGERUNG.items():
        try:
            obs = get_fred_latest(series_id, fred_api_key)
            werte[feld] = obs.value
        except Exception as exc:
            logger.info("FRED-Abruf fuer %s (%s) fehlgeschlagen: %s", feld, series_id, exc)
            werte[feld] = None
    werte["hinweis"] = (
        "realrendite_10j_prozent: 10J-TIPS-Realrendite (historisch staerkster Gold-/"
        "Silber-Treiber, negativ korreliert). dxy_proxy: Dollar-Index (inverse "
        "Wirkung auf USD-notierte Rohstoffe). industrieproduktion_index: grober "
        "Industrienachfrage-Proxy, primaer fuer Kupfer relevant."
    )
    return werte


def _fetch_lagerbestaende(symbol: str, eia_api_key: str | None) -> dict | None:
    """EIA-Erdgas-Lagerbestandsdaten (2026-07-19, Datenquellen-Recherche-
    Nachfolger, siehe Regelwerksmanual-Nachtrag) - NUR fuer OD7L (Erdgas),
    da EIAs Weekly Natural Gas Storage Report kein Gold-/Silber-/Kupfer-
    Aequivalent hat. Optional (P-8, kein Key -> None statt Fehler)."""
    if symbol != "OD7L" or not eia_api_key:
        return None
    try:
        from api.eia import get_natural_gas_storage_history

        readings = get_natural_gas_storage_history(eia_api_key, n_weeks=8)
    except Exception as exc:
        logger.info("EIA-Erdgas-Lagerbestand-Abruf fehlgeschlagen: %s", exc)
        return None
    if not readings:
        return None
    letzter = readings[-1]
    return {
        "letzter_wert_bcf": letzter.value_bcf,
        "letztes_datum": letzter.date,
        "letzte_woechentliche_aenderung_bcf": letzter.net_change_bcf,
        "verlauf_8_wochen": [
            {"datum": r.date, "wert_bcf": r.value_bcf, "aenderung_bcf": r.net_change_bcf} for r in readings
        ],
        "hinweis": (
            "Lower-48-Erdgaslagerbestand (EIA Weekly Natural Gas Storage Report, "
            "Bcf = Milliarden Kubikfuss). Ein 'Build' (positive Aenderung) staerkt "
            "das Angebot (tendenziell preisdaempfend), ein 'Draw' (negative "
            "Aenderung) verknappt es (tendenziell preisstuetzend) - relevant NUR im "
            "Vergleich zur JAHRESZEITLICHEN Norm (Sommer/Winter-Heizbedarf), nicht "
            "als absoluter Wert. Kein historischer 5-Jahres-Durchschnitt verfuegbar "
            "(noch nicht implementiert) - formuliere entsprechend vorsichtig."
        ),
    }


def _fetch_positionierung(symbol: str) -> dict | None:
    """CFTC-COT-Positionierung (Managed Money) - siehe api/cftc_cot.py. Gibt None
    zurueck bei unbekanntem Symbol oder Abruf-Fehlschlag (P-10)."""
    rohstoff = SYMBOL_ZU_COT_ROHSTOFF.get(symbol)
    if rohstoff is None:
        return None
    try:
        snap = get_cot_snapshot(rohstoff)
    except Exception as exc:
        logger.info("CFTC-COT-Abruf fuer %s (%s) fehlgeschlagen: %s", symbol, rohstoff, exc)
        return None
    if snap is None:
        return None
    return {
        "rohstoff": snap.rohstoff,
        "report_datum": snap.report_datum,
        "open_interest": snap.open_interest,
        "managed_money_long": snap.managed_money_long,
        "managed_money_short": snap.managed_money_short,
        "managed_money_netto": snap.managed_money_netto,
        "managed_money_long_anteil_oi_prozent": snap.managed_money_long_anteil_oi_prozent,
        "hinweis": (
            "Managed Money = grosse spekulative Fonds/CTAs laut woechentlichem "
            "CFTC-Report (~3 Tage Verzug bis Veroeffentlichung). Grobes Sentiment-"
            "Indiz, siehe Regel 10 im SYSTEM_PROMPT - kein praezises Timing-Signal."
        ),
    }


def generate_signal(
    asset, watchlist, conn, llm_client, coingecko_client, zai_client=None,
    war_re_evaluierung_faellig: bool = False,
) -> Signal:
    """Analog zu agent/aktien/pipeline.py::generate_signal(). `watchlist` muss die
    VOLLSTAENDIGE Watchlist sein (inkl. BTC) - compute_current_regime() braucht
    zwingend ein BTC-Asset darin. Fuer pre_check()'s RM-2-Allokations-Berechnung
    wird intern auf die Rohstoff-Teilmenge gefiltert (eigenes Mini-Portfolio-
    Verhaeltnis, analog zur Aktien-Pipeline)."""
    if asset.assetklasse != "rohstoffe":
        raise ValueError(f"generate_signal() (agent/rohstoff) erwartet assetklasse=='rohstoffe', bekam {asset.assetklasse!r}")

    rohstoff_watchlist = [a for a in watchlist if a.assetklasse == "rohstoffe"]

    jit_refresh_ohlc(conn, asset)
    _ensure_ohlc_backfilled(conn, asset)
    # TECHNISCHE ANALYSE AUF DER FUTURES-REIHE (2026-08-06). Seit der Trennung
    # liegt unter `asset.symbol` die REKONSTRUIERTE ETC-Reihe - die traegt Roll-
    # und Gebuehrendrift und ist fuer Indikatoren die schlechtere Grundlage. Der
    # Future hat die liquide, lueckenlose Reihe; genau deshalb wurde er
    # urspruenglich gewaehlt. Die ETC-Reihe dient der BEWERTUNG (Portfolio-Wert,
    # Outcome), nicht der Analyse.
    #
    # Rueckfall auf die ETC-Reihe, falls die Futures-Reihe fehlt - dann ist eine
    # driftbehaftete Analyse besser als gar keine, und der Fall ist im Log
    # sichtbar.
    dates, closes, ohlc_history, last_date = _load_ohlc(conn, _futures_symbol(asset.symbol))
    if last_date is None:
        dates, closes, ohlc_history, last_date = _load_ohlc(conn, asset.symbol)
        if last_date is not None:
            logger.warning("Keine Futures-Reihe fuer %s - technische Analyse laeuft auf der "
                           "rekonstruierten ETC-Reihe (driftbehaftet)", asset.symbol)
    latest_prices = db.get_latest_prices(conn)
    price_snap = latest_prices.get(asset.symbol)
    # Deterministische EUR-Ableitung (2026-07-27, Grundsatzfix Teil 2) - gleiches
    # Muster wie agent/hedge/pipeline.py, siehe agent/krypto/pipeline.py::eur_aus_usd()
    # Docstring. Die Herkunftsrichtung von price_snap.price_usd (hier: abgeleitet aus
    # price_eur, siehe Gate-Kommentar oben) ist fuer die Ableitungsformel irrelevant,
    # solange derselbe Live-EURCV-Kurs fuer Anzeige UND Ableitung verwendet wird.
    eurcv_snap = latest_prices.get("EURCV")
    eur_usd_fx_rate = (
        eurcv_snap.price_usd / eurcv_snap.price_eur
        if eurcv_snap and eurcv_snap.price_usd and eurcv_snap.price_eur else None
    )

    if len(closes) == 0:
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=False, gate_reason="keine historischen Daten vorhanden")
        db.insert_signal(conn, signal)
        return signal

    # Gate-Check FUER price_usd VOR der Skalierung (nicht erst danach, siehe unten) -
    # diese ETCs handeln in EUR (Stuttgart/XETRA), price_usd wird erst nachtraeglich
    # aus price_eur * eur_usd_fx_rate abgeleitet (api/yfinance_client.py::_fetch_one())
    # und kann fehlen, wenn beim letzten Preisabruf kein aktueller FX-Kurs vorlag -
    # OHNE price_usd kann _rescale_ohlc_zum_etc_kurs() nicht korrekt skalieren, die
    # gesamte technische Analyse waere sonst still auf der falschen (Futures-)
    # Preisskala (P-10: das darf das Gate nicht durchlassen).
    gate_problems = []
    if price_snap is None or is_price_stale(price_snap.fetched_at):
        gate_problems.append("Preis veraltet oder nicht vorhanden")
    elif price_snap.price_usd is None:
        gate_problems.append("USD-Preis nicht verfuegbar (EUR/USD-Kurs fehlte beim letzten Preisabruf)")
    if _is_rohstoff_history_stale(last_date):
        gate_problems.append(f"Historie veraltet (letzter Tag: {last_date})")

    if gate_problems:
        gate_reason = "; ".join(gate_problems)
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=False, gate_reason=gate_reason)
        db.insert_signal(conn, signal)
        return signal

    # Skalierung Futures-Historie -> ETC-Preisniveau (siehe SYMBOL_ZU_FUTURES_TICKER-
    # Docstring) - MUSS vor build_technical_snapshot() passieren, sonst liegen
    # EMA/Bollinger/ATR/S&R/Fibonacci auf der falschen absoluten Preisskala.
    closes, ohlc_history = _rescale_ohlc_zum_etc_kurs(closes, ohlc_history, price_snap.price_usd)

    # Nachtrag (2026-07-27, Grundsatzfix Teil 2): die skalierte Reihe wurde bisher
    # NUR im Arbeitsspeicher verwendet, nie zurueckgeschrieben - price_history_ohlc
    # blieb dauerhaft auf der Futures-Preisskala (z.B. Gold ~4000 USD/Unze), waehrend
    # signal.take_profit_usd_von/stop_loss_usd_von auf der ETC-Skala (~18-20 USD)
    # liegen. agent/krypto/backward_tracking.py::check_signal_outcome() vergleicht
    # genau diese gespeicherte (unskalierte!) Reihe gegen die ETC-Skala-Schwellen -
    # ein Futures-High von ~4000 erfuellt "high >= take_profit_threshold(~20)" fast
    # immer sofort, was Rohstoff-Signale bislang vermutlich systematisch zu frueh als
    # take_profit_erreicht aufloeste (und damit auch historische_erfolgsquote
    # verzerrte). Fix: die skalierte Reihe wird jetzt persistiert. Bewusste
    # Verhaltensaenderung, keine reine Nebenwirkung: der Skalierungsfaktor (aktueller
    # ETC-Kurs / letzter Futures-Kurs) aendert sich von Lauf zu Lauf leicht, jeder
    # erneute Schreibvorgang ueberschreibt die GESAMTE historische Reihe mit dem
    # jeweils neuesten Verhaeltnis - erwuenscht (haelt die Reihe konsistent zum
    # aktuell bekannten Skalierungsfaktor), aber nicht zeilen-fuer-zeilen-idempotent.
    if ohlc_history:
        db.upsert_ohlc_points(conn, ohlc_history)

    snapshot = build_technical_snapshot(closes, dates, ohlc_history)

    for name in MIN_GATE_INDICATORS_AVAILABLE:
        result = getattr(snapshot, name)
        if not result.available:
            gate_problems.append(f"{name.upper()}: {result.reason}")

    if gate_problems:
        gate_reason = "; ".join(gate_problems)
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=False, gate_reason=gate_reason)
        db.insert_signal(conn, signal)
        return signal

    config_dict = config.load_config()
    regime_result = compute_current_regime(conn, coingecko_client, watchlist, None, config_dict)

    confluence = summarize_confluence(snapshot, closes[-1])

    try:
        from api.bitpanda import get_listed_non_crypto_assets
        from api.bitpanda import is_listed as bitpanda_is_listed

        bitpanda_assets = get_listed_non_crypto_assets()
        bitpanda_gelistet = bitpanda_is_listed(asset.symbol, bitpanda_assets, name=asset.name)
        # Bitpanda-Gelistet-Override (2026-07-20) - siehe database/db.py::
        # asset_bitpanda_override-Tabellendocstring.
        if not bitpanda_gelistet and db.get_bitpanda_gelistet_override(conn, asset.symbol):
            bitpanda_gelistet = True
    except Exception as exc:
        bitpanda_gelistet = None
        logger.info("Bitpanda-Listing-Abruf fuer %s fehlgeschlagen: %s", asset.symbol, exc)

    risk_result = pre_check(asset, rohstoff_watchlist, conn, latest_prices, snapshot, regime_result, config_dict, bitpanda_gelistet)

    fred_api_key = os.environ.get("FRED_API_KEY")
    makro_ueberlagerung = _fetch_makro_ueberlagerung(fred_api_key)
    positionierung = _fetch_positionierung(asset.symbol)
    eia_api_key = os.environ.get("EIA_API_KEY")
    lagerbestaende = _fetch_lagerbestaende(asset.symbol, eia_api_key)

    holdings = {h.symbol: h for h in db.get_all_holdings(conn)}
    price_age_minutes = None
    if price_snap is not None:
        fetched = datetime.fromisoformat(price_snap.fetched_at)
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        price_age_minutes = (datetime.now(timezone.utc) - fetched).total_seconds() / 60

    # Eigener Pool statt des Krypto+Aktien-"spot"-Pools (2026-07-18, Multi-Asset-
    # Vollstaendigkeitspruefung): Rohstoffe bewegen sich strukturell anders
    # (langsamer, andere Zyklen) - eine geliehene fremde Zahl waere irrefuehrend,
    # siehe compute_win_rate_fact()-Docstring.
    _rohstoff_symbole = {a.symbol for a in config.get_watchlist() if a.assetklasse == "rohstoffe"}
    historische_erfolgsquote = compute_win_rate_fact(conn, "spot", erlaubte_symbole=_rohstoff_symbole)
    historischer_makro_vergleich = get_cached_makro_analog_fact(conn)
    letztes_signal = db.get_latest_signal(conn, asset.symbol)
    these_abgleich = kategorie_thesen.build_these_abgleich_fact(conn, asset)

    # CRV-Erfolgsbaender fuer DIESE Assetklasse (2026-08-06, Kandidat A1).
    # Eigene Messung je Tier statt uebertragener Prozentwerte - der Vorbehalt
    # aus fde5bfe. Ohne belastbares Band gibt die Funktion None zurueck und der
    # Fakt entfaellt. Fail-soft: der Signallauf darf daran nicht kippen. Der
    # Aufruf hat intern einen Tages-Cache, er simuliert Kursreihen.
    try:
        from agent.krypto.backward_tracking import crv_baender_kontext_fuer_prompt
        fakt_crv_baender = crv_baender_kontext_fuer_prompt(
            conn, "rohstoffe", watchlist=watchlist)
    except Exception:
        logger.exception("CRV-Baender-Fakt fehlgeschlagen - Signal laeuft ohne")
        fakt_crv_baender = None
    facts = build_facts(
        asset, price_snap, holdings.get(asset.symbol), snapshot, confluence, regime_result,
        risk_result, makro_ueberlagerung, positionierung, price_age_minutes,
        crv_baender=fakt_crv_baender,
        historische_erfolgsquote=historische_erfolgsquote,
        historischer_makro_vergleich=historischer_makro_vergleich,
        letztes_signal=letztes_signal,
        lagerbestaende=lagerbestaende,
        these_abgleich=these_abgleich,
    )

    try:
        parsed = call_llm_for_signal(llm_client, facts)
    except AnalystResponseInvalid as exc:
        logger.warning("LLM-Antwort fuer %s ungueltig: %s", asset.symbol, exc)
        signal = _fixed_signal(asset.symbol, "HALTEN", gate_passed=True, gate_reason=f"Agent-Antwort ungültig: {exc}", facts=facts)
        db.insert_signal(conn, signal)
        return signal

    raw_response = parsed.pop("_raw_response", None)

    corrected = post_check(parsed, risk_result, regime_result, config_dict, confluence=confluence)
    risk_veto = corrected.pop("_risk_veto")
    risk_veto_reason = corrected.pop("_risk_veto_reason")
    cash_veto = corrected.pop("_cash_veto")
    cash_veto_reason = corrected.pop("_cash_veto_reason")
    risikofaktoren = corrected.pop("_risikofaktoren", None)
    fazit_konsistenz_hinweis = corrected.pop("_fazit_konsistenz_hinweis", None)
    # H-6 (2026-08-07): `_original_action` und `_ist_reines_llm_halten` werden
    # von post_check() seit dem 31.07. fuer ALLE Spot-Pipelines gesetzt - nur
    # abgeholt hat sie bisher ausschliesslich agent/krypto/pipeline.py. Ohne sie
    # laesst sich nicht unterscheiden, ob eine HALTEN-Empfehlung vom Modell kam
    # oder ob ein Gate sie ueberschrieben hat.
    #
    # Das war keine Messluecke, sondern eine Funktionsluecke: bei 201
    # Nicht-Krypto-Signalen war `original_action` durchgehend None, und die
    # Frage "wie viele HALTEN kommen vom Modell?" damit strukturell
    # unbeantwortbar (siehe Zwischenstand 8c/8d).
    ist_reines_llm_halten = corrected.pop("_ist_reines_llm_halten", False)
    original_action = corrected.pop("_original_action", None)
    eigene_einschaetzung = corrected.get("eigene_einschaetzung") or {}

    long_reasoning = corrected.get("long_reasoning", {})
    position_size = corrected.get("position_size", {})
    entry = corrected.get("entry", {})
    stop_loss = corrected.get("stop_loss", {})
    take_profit = corrected.get("take_profit", {})
    halte_kriterium = corrected.get("halte_kriterium", {})
    top_gruende_by_rang = {g.get("rang"): g for g in corrected.get("top_gruende", [])}
    forecast = corrected.get("forecast", {})

    top_grund_fields = {}
    for rang in range(1, 6):
        eintrag = top_gruende_by_rang.get(rang, {})
        top_grund_fields[f"top_grund_{rang}_kategorie"] = eintrag.get("kategorie")
        top_grund_fields[f"top_grund_{rang}_text"] = eintrag.get("text")

    log_eur_abweichungen(asset.symbol, {
        "position_size": (position_size.get("eur"), eur_aus_usd(position_size.get("usd"), eur_usd_fx_rate)),
        "entry_von": (entry.get("eur_von"), eur_aus_usd(entry.get("usd_von"), eur_usd_fx_rate)),
        "entry_bis": (entry.get("eur_bis"), eur_aus_usd(entry.get("usd_bis"), eur_usd_fx_rate)),
        "stop_loss_von": (stop_loss.get("eur_von"), eur_aus_usd(stop_loss.get("usd_von"), eur_usd_fx_rate)),
        "stop_loss_bis": (stop_loss.get("eur_bis"), eur_aus_usd(stop_loss.get("usd_bis"), eur_usd_fx_rate)),
        "take_profit_von": (take_profit.get("eur_von"), eur_aus_usd(take_profit.get("usd_von"), eur_usd_fx_rate)),
        "take_profit_bis": (take_profit.get("eur_bis"), eur_aus_usd(take_profit.get("usd_bis"), eur_usd_fx_rate)),
        "halte_kriterium_ziel_preis": (
            halte_kriterium.get("ziel_preis_eur"), eur_aus_usd(halte_kriterium.get("ziel_preis_usd"), eur_usd_fx_rate),
        ),
    })

    signal = Signal(
        symbol=asset.symbol,
        created_at=_now(),
        action=corrected["action"],
        gate_passed=True,
        gate_reason=None,
        risk_veto=risk_veto,
        risk_veto_reason=risk_veto_reason,
        war_re_evaluierung_faellig=war_re_evaluierung_faellig,
        cash_veto=cash_veto,
        cash_veto_reason=cash_veto_reason,
        risikofaktoren_json=json.dumps(risikofaktoren, ensure_ascii=False) if risikofaktoren else None,
        original_action=original_action,
        ist_reines_llm_halten=ist_reines_llm_halten,
        facts_json=json.dumps(facts, ensure_ascii=False),
        pipeline_version=PIPELINE_VERSION,
        confidence_pct=corrected.get("confidence_pct"),
        short_reasoning=corrected.get("short_reasoning"),
        long_reasoning_technisch=long_reasoning.get("technisch"),
        long_reasoning_fundamental=long_reasoning.get("fundamental"),
        long_reasoning_makro=long_reasoning.get("makro"),
        position_size_usd=position_size.get("usd"),
        position_size_eur=eur_aus_usd(position_size.get("usd"), eur_usd_fx_rate),
        position_size_note=position_size.get("note"),
        entry_usd_von=entry.get("usd_von"),
        entry_usd_bis=entry.get("usd_bis"),
        entry_eur_von=eur_aus_usd(entry.get("usd_von"), eur_usd_fx_rate),
        entry_eur_bis=eur_aus_usd(entry.get("usd_bis"), eur_usd_fx_rate),
        stop_loss_usd_von=stop_loss.get("usd_von"),
        stop_loss_usd_bis=stop_loss.get("usd_bis"),
        stop_loss_eur_von=eur_aus_usd(stop_loss.get("usd_von"), eur_usd_fx_rate),
        stop_loss_eur_bis=eur_aus_usd(stop_loss.get("usd_bis"), eur_usd_fx_rate),
        take_profit_usd_von=take_profit.get("usd_von"),
        take_profit_usd_bis=take_profit.get("usd_bis"),
        take_profit_eur_von=eur_aus_usd(take_profit.get("usd_von"), eur_usd_fx_rate),
        take_profit_eur_bis=eur_aus_usd(take_profit.get("usd_bis"), eur_usd_fx_rate),
        halte_kriterium_bucket=halte_kriterium.get("bucket"),
        halte_kriterium_ziel_preis_usd=halte_kriterium.get("ziel_preis_usd"),
        halte_kriterium_ziel_preis_eur=eur_aus_usd(halte_kriterium.get("ziel_preis_usd"), eur_usd_fx_rate),
        halte_kriterium_ziel_datum=halte_kriterium.get("ziel_datum"),
        halte_kriterium_bedingung_text=halte_kriterium.get("bedingung_text"),
        halte_kriterium_reasoning=halte_kriterium.get("reasoning"),
        key_risks_text="\n".join(corrected.get("key_risks", [])),
        regime=regime_result.regime,
        regime_source=regime_result.source,
        forecast_bull_text=forecast.get("bull", {}).get("scenario"),
        forecast_bull_prob_pct=forecast.get("bull", {}).get("probability_pct"),
        forecast_base_text=forecast.get("base", {}).get("scenario"),
        forecast_base_prob_pct=forecast.get("base", {}).get("probability_pct"),
        forecast_bear_text=forecast.get("bear", {}).get("scenario"),
        forecast_bear_prob_pct=forecast.get("bear", {}).get("probability_pct"),
        gegenargument=corrected.get("gegenargument"),
        fazit_folgen=eigene_einschaetzung.get("folgen"),
        fazit_kurzfazit=eigene_einschaetzung.get("kurzfazit"),
        fazit_konsistenz_hinweis=fazit_konsistenz_hinweis,
        groq_raw_response=raw_response,
        groq_model=llm_model_label(llm_client),
        **top_grund_fields,
    )
    new_id = db.insert_signal(conn, signal)
    signal.id = new_id

    # Z.ai-Gegenpruefung (Ausweitung auf Rohstoffe, siehe agent/krypto/
    # gegenpruefung.py Modul-Docstring "Vollstaendige Vereinheitlichung") -
    # rein beobachtend, laeuft asynchron NACH dem Insert. Kein funding_rate/
    # optionsmarkt-Fakt (Krypto-Perpetual/Deribit-exklusiv). richtung_aus_
    # action() leitet die fuer den Vergleich erwartete Richtung deterministisch
    # aus der Action ab (HALTEN -> kein Vergleich).
    if zai_client is not None:
        ema_ordnung_item = next(
            (item for item in confluence.items if item.indicator == "EMA-Ordnung"), None,
        )
        trend_label = ema_ordnung_item.detail if ema_ordnung_item else None
        rsi_wert = latest_value(snapshot.rsi)
        zai_fakten = baue_zai_fakten(
            symbol=asset.symbol,
            action=corrected.get("action"),
            confidence_pct=corrected.get("confidence_pct"),
            rsi=rsi_wert,
            trend_label=trend_label,
            regime=regime_result.regime,
            funding_rate_stunde=None,
            confluence_bullish=confluence.bullish_count,
            confluence_bearish=confluence.bearish_count,
            confluence_neutral=confluence.neutral_count,
            optionsmarkt_skew=None,
        )
        zai_objektive_fakten = baue_zai_objektive_fakten(
            symbol=asset.symbol,
            rsi=rsi_wert,
            trend_label=trend_label,
            regime=regime_result.regime,
            funding_rate_stunde=None,
            confluence_bullish=confluence.bullish_count,
            confluence_bearish=confluence.bearish_count,
            confluence_neutral=confluence.neutral_count,
            optionsmarkt_skew=None,
        )
        primaer_richtung_erwartet = richtung_aus_action(corrected.get("action"))
        threading.Thread(
            target=fuehre_beide_calls_im_hintergrund,
            args=(
                new_id, zai_fakten, corrected.get("short_reasoning"),
                zai_objektive_fakten, primaer_richtung_erwartet, zai_client,
                db.update_signal_zai_gegenpruefung,
            ),
            daemon=True,
        ).start()

    return signal
