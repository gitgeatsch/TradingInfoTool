"""Hebel-Screening (2026-07-14, siehe docs/hebel_positionsformel.md) - rein
deterministisches Zwei-Zweige-Scoring (Trendfolge + Kontra), KEIN Groq-Aufruf,
laeuft alle 15 Min ueber die komplette Watchlist. Liefert Kandidaten fuer den
kuenftigen Budget-Allocator (Tier 1), der dann die eigentliche Hebel-Empfehlung
per LLM generieren laesst - das ist NICHT Teil dieses Moduls.

Struktur analog agent/krypto/marktscan.py (Stufe-B-artiges gewichtetes Scoring,
combine_scores-Aequivalent), OI-Abruf analog agent/krypto/anticyclic.py::assess()
(dieselben Binance/Bybit/OKX-Endpunkte, dasselbe f"{symbol}USDT"-Muster), nur
dass hier zusaetzlich jeder Abruf in open_interest_snapshot persistiert wird -
anticyclic.py ruft live ab und speichert nichts, hier ist die Zeitreihe der Punkt.

Bekannte, dokumentierte Vereinfachung (P-10-Stil): "kursaenderung_pct_lookback"
nutzt CoinGecko's rollierenden 24h-Change (price_cache.change_24h_pct), NICHT
eine echte 4h-Fensteraenderung - eine eigene stuendliche Preis-Zeitreihe existiert
bisher nicht, nur die neue OI-Zeitreihe. Das ist eine praktikable Naeherung, kein
exaktes 4h-Fenster.

"Wende-Anzeichen" (Kontra-Zweig) ist eine einfache RSI-Extremzonen-Heuristik
(RSI > 70 oder < 30), KEINE echte Divergenz-Erkennung (Kurs macht neues Hoch/Tief,
RSI nicht) - letzteres braeuchte eine Vergleichsfenster-Logik, hier bewusst
vereinfacht, analog zu anticyclic.py's eigener "einfache Heuristik"-Kennzeichnung."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta, timezone

import database.db as db
from api.derivatives import (
    get_binance_long_short_ratio,
    get_binance_open_interest,
    get_bybit_open_interest,
    get_okx_open_interest,
)
from api.kraken import KRAKEN_FUTURES_SYMBOL_MAP
from database.models import HebelTrigger, OpenInterestSnapshot
from indicators.calculations import ConfluenceSummary, TechnicalSnapshot, latest_value

logger = logging.getLogger(__name__)

RICHTUNG_LONG = "LONG"
RICHTUNG_SHORT = "SHORT"
ZWEIG_TRENDFOLGE = "trendfolge"
ZWEIG_KONTRA = "kontra"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_and_store_oi_snapshot(conn, asset, kraken_client) -> bool:
    """Ruft OI (Binance/Bybit/OKX) + Long-Konten-Anteil (Binance) + Funding-Rate
    (Kraken) fuer ein Asset ab und speichert je Boerse einen Snapshot. Jede Quelle
    einzeln try/except (P-10-Isolation, identisches Muster wie anticyclic.py::
    assess()) - ein Fehlschlag bei einer Boerse blockiert die anderen nicht.

    Gibt zurueck, ob MINDESTENS eine der drei OI-Boersen (Binance/Bybit/OKX)
    erfolgreich war (2026-07-19, echter Notebook-Fund: KAS/KAIA/FLOKI/TURBO/
    CANTON scheiterten wiederholt bei ALLEN dreien - der Aufrufer nutzt das,
    um einen persistenten Fehlschlag-Zaehler je Symbol zu pflegen, siehe
    db.record_oi_abdeckung_ergebnis())."""
    binance_symbol = f"{asset.symbol}USDT"
    fetched_at = _now_iso()
    mindestens_eine_boerse_erfolgreich = False

    funding_rate = None
    futures_symbol = KRAKEN_FUTURES_SYMBOL_MAP.get(asset.symbol)
    if futures_symbol is not None:
        try:
            rates = kraken_client.get_funding_rates(futures_symbol)
            recent = rates[-24:] if len(rates) >= 24 else rates
            if recent:
                funding_rate = sum(r["relative_funding_rate"] for r in recent) / len(recent)
        except Exception as exc:
            logger.info("Kraken-Funding-Rate-Abruf fuer %s fehlgeschlagen: %s", asset.symbol, exc)

    long_account_pct = None
    try:
        lsr = get_binance_long_short_ratio(binance_symbol)
        long_account_pct = lsr.long_account_pct
    except Exception as exc:
        logger.info("Binance-Long-Short-Ratio-Abruf fuer %s fehlgeschlagen: %s", binance_symbol, exc)

    try:
        oi = get_binance_open_interest(binance_symbol)
        db.insert_oi_snapshot(conn, OpenInterestSnapshot(
            symbol=asset.symbol, exchange="binance", open_interest=oi.open_interest,
            open_interest_usd=oi.open_interest_usd, funding_rate=funding_rate,
            long_account_pct=long_account_pct, fetched_at=fetched_at,
        ))
        mindestens_eine_boerse_erfolgreich = True
    except Exception as exc:
        logger.info("Binance-Open-Interest-Abruf fuer %s fehlgeschlagen: %s", binance_symbol, exc)

    try:
        oi = get_bybit_open_interest(binance_symbol)
        db.insert_oi_snapshot(conn, OpenInterestSnapshot(
            symbol=asset.symbol, exchange="bybit", open_interest=oi.open_interest,
            open_interest_usd=oi.open_interest_usd, funding_rate=funding_rate,
            long_account_pct=long_account_pct, fetched_at=fetched_at,
        ))
        mindestens_eine_boerse_erfolgreich = True
    except Exception as exc:
        logger.info("Bybit-Open-Interest-Abruf fuer %s fehlgeschlagen: %s", binance_symbol, exc)

    try:
        oi = get_okx_open_interest(f"{asset.symbol}-USDT-SWAP")
        db.insert_oi_snapshot(conn, OpenInterestSnapshot(
            symbol=asset.symbol, exchange="okx", open_interest=oi.open_interest,
            open_interest_usd=oi.open_interest_usd, funding_rate=funding_rate,
            long_account_pct=long_account_pct, fetched_at=fetched_at,
        ))
        mindestens_eine_boerse_erfolgreich = True
    except Exception as exc:
        logger.info("OKX-Open-Interest-Abruf fuer %s fehlgeschlagen: %s", asset.symbol, exc)

    return mindestens_eine_boerse_erfolgreich


def compute_oi_change_pct(conn, symbol: str, exchange: str, lookback_hours: float) -> float | None:
    """%-Aenderung des Open Interest seit dem aeltesten Snapshot innerhalb des
    Lookback-Fensters. None, wenn weniger als 2 Snapshots im Fenster liegen (noch
    keine Vergleichsbasis) oder der aelteste Wert 0/None ist (Division waere
    undefiniert)."""
    min_fetched_at = (datetime.now(timezone.utc) - timedelta(hours=lookback_hours)).isoformat()
    history = db.get_oi_history(conn, symbol, exchange, min_fetched_at=min_fetched_at)
    if len(history) < 2:
        return None
    aeltester, neuester = history[0], history[-1]
    if not aeltester.open_interest:
        return None
    return (neuester.open_interest - aeltester.open_interest) / aeltester.open_interest * 100


def _combine(scores: dict[str, float | None], gewichte: dict) -> float | None:
    """Gewichteter Durchschnitt ueber verfuegbare Kategorien - fehlende Kategorie
    wird aus Zaehler UND Nenner ausgeschlossen (nicht als 0 gewertet), identisches
    Prinzip wie marktscan.py::combine_scores()."""
    zaehler, nenner = 0.0, 0.0
    for kategorie, score in scores.items():
        gewicht = gewichte.get(f"gewicht_{kategorie}", 0.0)
        if score is not None:
            zaehler += gewicht * score
            nenner += gewicht
    if nenner <= 0:
        return None
    return round(zaehler / nenner, 1)


def score_trendfolge(
    oi_change_pct: float | None,
    kursaenderung_pct: float | None,
    funding_rate: float | None,
    confluence: ConfluenceSummary | None,
    cfg: dict,
) -> tuple[float | None, dict]:
    """Bewertet Trendbestaetigung in Richtung des Vorzeichens von
    kursaenderung_pct (>=0 -> LONG-These, <0 -> SHORT-These). Score 0-100 je
    Teilkategorie: OI-Aenderung in dieselbe Richtung wie der Kurs = Bestaetigung,
    Funding-Rate NOCH NICHT extrem = "Luft nach oben" (besser), Konfluenz-Anteil
    in Trendrichtung."""
    scores: dict[str, float | None] = {}
    signale: dict = {}
    richtung_vorzeichen = 1 if (kursaenderung_pct or 0) >= 0 else -1
    schwelle_oi = cfg["oi_aenderung_schwelle_prozent"]
    schwelle_kurs = cfg["kursaenderung_schwelle_prozent"]
    schwelle_funding = cfg["funding_rate_noch_nicht_extrem"]

    if oi_change_pct is not None and schwelle_oi:
        gerichtete_oi_aenderung = oi_change_pct * richtung_vorzeichen
        scores["oi_aenderung"] = max(0.0, min(100.0, 50.0 + (gerichtete_oi_aenderung / schwelle_oi) * 50.0))
        signale["oi_change_pct"] = oi_change_pct

    if kursaenderung_pct is not None and schwelle_kurs:
        scores["kursaenderung"] = max(0.0, min(100.0, (abs(kursaenderung_pct) / schwelle_kurs) * 100.0))
        signale["kursaenderung_pct"] = kursaenderung_pct

    if funding_rate is not None and schwelle_funding:
        anteil_an_schwelle = abs(funding_rate) / schwelle_funding
        scores["funding_rate"] = max(0.0, min(100.0, 100.0 - anteil_an_schwelle * 100.0))
        signale["funding_rate_aktuell"] = funding_rate

    if confluence is not None:
        gesamt = confluence.bullish_count + confluence.bearish_count + confluence.neutral_count
        if gesamt > 0:
            passende_confluence = confluence.bullish_count if richtung_vorzeichen > 0 else confluence.bearish_count
            scores["konfluenz"] = (passende_confluence / gesamt) * 100.0
            signale["konfluenz_bias"] = confluence.overall_bias

    return _combine(scores, cfg.get("_gewichte", {})), signale


def _detect_wende_anzeichen(snapshot: TechnicalSnapshot | None) -> bool | None:
    if snapshot is None:
        return None
    rsi = latest_value(snapshot.rsi)
    if rsi is None:
        return None
    return bool(rsi > 70 or rsi < 30)


def score_kontra(
    funding_rate: float | None,
    long_account_pct: float | None,
    wende_anzeichen: bool | None,
    cfg: dict,
) -> tuple[float | None, dict]:
    """Bewertet eine Squeeze-Chance (Zweig 2): extreme Funding-Rate + einseitige
    Positionierung + Wende-Anzeichen. Die implizierte Richtung wird separat ueber
    _determine_kontra_richtung() bestimmt, nicht hier."""
    scores: dict[str, float | None] = {}
    signale: dict = {}
    schwelle_funding = cfg["funding_rate_extrem_schwelle"]
    oben = cfg["long_bias_extrem_oben_prozent"]

    if funding_rate is not None and schwelle_funding:
        scores["funding_rate_extrem"] = max(0.0, min(100.0, abs(funding_rate) / schwelle_funding * 100.0))
        signale["funding_rate_aktuell"] = funding_rate

    if long_account_pct is not None and oben > 50:
        abstand_von_mitte = abs(long_account_pct - 50.0)
        abstand_schwelle = oben - 50.0
        scores["long_bias_extrem"] = max(0.0, min(100.0, (abstand_von_mitte / abstand_schwelle) * 100.0))
        signale["long_konten_anteil_prozent"] = long_account_pct

    if wende_anzeichen is not None:
        scores["wende_anzeichen"] = 100.0 if wende_anzeichen else 0.0
        signale["wende_anzeichen"] = wende_anzeichen

    return _combine(scores, cfg.get("_gewichte", {})), signale


def _determine_kontra_richtung(funding_rate: float | None, long_account_pct: float | None, cfg: dict) -> str | None:
    """Extreme positive Funding-Rate / hoher Long-Konten-Anteil = ueberfuellter
    Long-Trade -> Kontra-These ist SHORT. Umgekehrt fuer LONG. None, wenn keines
    der beiden Signale eindeutig in eine Richtung zeigt (kein Kontra-Kandidat)."""
    schwelle_funding = cfg["funding_rate_extrem_schwelle"]
    oben, unten = cfg["long_bias_extrem_oben_prozent"], cfg["long_bias_extrem_unten_prozent"]

    ueberfuellt_long = (funding_rate is not None and schwelle_funding and funding_rate > schwelle_funding) or \
        (long_account_pct is not None and long_account_pct > oben)
    ueberfuellt_short = (funding_rate is not None and schwelle_funding and funding_rate < -schwelle_funding) or \
        (long_account_pct is not None and long_account_pct < unten)

    if ueberfuellt_long and not ueberfuellt_short:
        return RICHTUNG_SHORT
    if ueberfuellt_short and not ueberfuellt_long:
        return RICHTUNG_LONG
    return None


def run_hebel_screening(
    conn_factory, watchlist: list, kraken_client, coingecko_client, config_dict: dict,
) -> list[HebelTrigger]:
    """Orchestriert das Screening ueber die Krypto-Watchlist (Aktien/ETF/
    Rohstoffe ausgeschlossen, wie ueberall in der Krypto-Pipeline) MINUS
    Assets mit abgeschaltetem Hebel-Pruefung-Toggle (2026-07-18, siehe
    db.get_hebel_pruefung_erlaubt()). Fuer jedes verbleibende Asset:
    OI-Snapshot abrufen+speichern, dann bis zu zwei unabhaengige Kandidaten
    bewerten (Trendfolge- UND Kontra-These koennen gleichzeitig existieren, mit
    potenziell unterschiedlicher Richtung - siehe UNIQUE(symbol, richtung,
    screening_run_id) im Schema)."""
    from agent.krypto.pipeline import _load_closes_and_ohlc
    from indicators.calculations import build_technical_snapshot, summarize_confluence

    cfg = config_dict["hebel_screening"]
    screening_run_id = f"{_now_iso()}_{uuid.uuid4().hex[:8]}"
    triggers: list[HebelTrigger] = []

    conn = conn_factory()
    try:
        latest_prices = db.get_latest_prices(conn)
        krypto_assets = [a for a in watchlist if a.assetklasse == "krypto" and not a.ist_cash_aequivalent]
        # Hebel-Pruefung-Toggle (2026-07-18, Budget/Asset-Optimierung, siehe
        # ui/app.py Watchlist-Tab) - VOR dem teuren OI-Abruf gefiltert, spart
        # auch unnoetige Binance/Bybit/OKX-Calls fuer abgeschaltete Assets.
        # Beruehrt NUR die Neuentdeckung neuer Trigger - bereits offene Hebel-
        # Positionen (agent/krypto/budget_allocator.py::_offene_positionen_
        # als_kandidaten()) sind ein unabhaengiger Kandidatenpfad und bleiben
        # unabhaengig vom Toggle weiter risikoueberwacht.
        krypto_assets = [a for a in krypto_assets if db.get_hebel_pruefung_erlaubt(conn, a.symbol)]
        for asset in krypto_assets:
            erfolg = fetch_and_store_oi_snapshot(conn, asset, kraken_client)
            # OI-Abdeckungs-Tracking (2026-07-19, siehe db.record_oi_abdeckung_
            # ergebnis()-Docstring) - persistenter Zaehler je Symbol, unabhaengig
            # von diesem einzelnen Lauf, damit scheduler/background.py::
            # hebel_screening_job() spaeter erkennen kann, welche Symbole
            # dauerhaft (nicht nur diesen einen Lauf) betroffen sind.
            db.record_oi_abdeckung_ergebnis(conn, asset.symbol, erfolg)

        for asset in krypto_assets:
            oi_change_pct = compute_oi_change_pct(conn, asset.symbol, "binance", cfg["oi_lookback_stunden"])
            price_snap = latest_prices.get(asset.symbol)
            kursaenderung_pct = price_snap.change_24h_pct if price_snap else None
            oi_history = db.get_oi_history(conn, asset.symbol, "binance")
            funding_rate = oi_history[-1].funding_rate if oi_history else None
            long_account_pct = oi_history[-1].long_account_pct if oi_history else None

            snapshot = None
            try:
                dates, closes, ohlc_history, _ = _load_closes_and_ohlc(conn, asset.symbol, asset.coingecko_id)
                if len(closes) >= 15:
                    snapshot = build_technical_snapshot(closes, dates, ohlc_history)
            except Exception as exc:
                logger.info("Technische Analyse fuer Hebel-Screening %s fehlgeschlagen: %s", asset.symbol, exc)

            confluence = None
            if snapshot is not None and price_snap and price_snap.price_usd:
                confluence = summarize_confluence(snapshot, price_snap.price_usd)

            trendfolge_cfg = dict(cfg["trendfolge"], _gewichte=cfg["gewichte"]["trendfolge"])
            score_tf, details_tf = score_trendfolge(oi_change_pct, kursaenderung_pct, funding_rate, confluence, trendfolge_cfg)
            if score_tf is not None:
                richtung = RICHTUNG_LONG if (kursaenderung_pct or 0) >= 0 else RICHTUNG_SHORT
                triggers.append(HebelTrigger(
                    symbol=asset.symbol, richtung=richtung, screened_at=_now_iso(),
                    screening_run_id=screening_run_id, trigger_zweig=ZWEIG_TRENDFOLGE,
                    score_gesamt=score_tf, score_details_json=str(details_tf),
                    oi_change_pct_lookback=oi_change_pct, kursaenderung_pct_lookback=kursaenderung_pct,
                    funding_rate_aktuell=funding_rate, long_konten_anteil_prozent=long_account_pct,
                    ist_kandidat=score_tf >= cfg["score_schwelle_kandidat"],
                ))

            kontra_cfg = dict(cfg["kontra"], _gewichte=cfg["gewichte"]["kontra"])
            kontra_richtung = _determine_kontra_richtung(funding_rate, long_account_pct, cfg["kontra"])
            if kontra_richtung is not None:
                wende_anzeichen = _detect_wende_anzeichen(snapshot)
                score_k, details_k = score_kontra(funding_rate, long_account_pct, wende_anzeichen, kontra_cfg)
                if score_k is not None:
                    triggers.append(HebelTrigger(
                        symbol=asset.symbol, richtung=kontra_richtung, screened_at=_now_iso(),
                        screening_run_id=screening_run_id, trigger_zweig=ZWEIG_KONTRA,
                        score_gesamt=score_k, score_details_json=str(details_k),
                        oi_change_pct_lookback=oi_change_pct, kursaenderung_pct_lookback=kursaenderung_pct,
                        funding_rate_aktuell=funding_rate, long_konten_anteil_prozent=long_account_pct,
                        ist_kandidat=score_k >= cfg["score_schwelle_kandidat"],
                    ))

        for trigger in triggers:
            trigger.id = db.insert_hebel_trigger(conn, trigger)

        # Info-Leichen-Fix (2026-07-19, Nutzer-Fund): unanalysierte Kandidaten
        # verfallen nach cfg["hebel_kandidat_verfall_stunden"], siehe
        # db.expire_stale_hebel_candidates()-Docstring fuer die Begruendung.
        # BUGFIX (2026-07-21): prueft jetzt die WAHRE Wartezeit seit
        # Erstkandidatur statt des Alters der einzelnen (immer frischen)
        # Zeile - siehe db.get_hebel_wartezeit_stunden_je_paar()-Docstring.
        verfallen_anzahl = db.expire_stale_hebel_candidates(
            conn, cfg["hebel_kandidat_verfall_stunden"],
            cfg.get("hebel_wartezeit_lookback_tage_cap", 14.0),
            cfg.get("hebel_kandidat_luecken_toleranz_stunden", 1.5),
        )
        if verfallen_anzahl:
            logger.info(
                "Hebel-Screening: %d veraltete Kandidaten (status=neu, aelter als %.0fh) "
                "automatisch auf status=verfallen gesetzt.",
                verfallen_anzahl, cfg["hebel_kandidat_verfall_stunden"],
            )
    finally:
        conn.close()

    return triggers
