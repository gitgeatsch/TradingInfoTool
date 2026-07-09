"""Marktscan Stufe A-D (Spezifikation Kap. 13) - Entdeckung neuer Assets ueber
CoinGecko Trending/Top-Gainers (MS-2), Filterung (Stufe A), Scoring (Stufe B),
Gewichtung (Stufe C, aus dem aktiven Regime-Profil) und Schwellenwerte (Stufe D).

Siehe C:\\Users\\Geatsch\\.claude\\plans\\deep-launching-zebra.md fuer den vollstaendigen
Scope-Plan. Drei bewusste, mit dem Nutzer abgestimmte Abweichungen vom Spec-Wortlaut
(MS-1, 2026-07-09):
1. KEIN automatisches Schreiben in config.yaml - Kandidaten werden hier nur bewertet
   und gespeichert (marktscan_candidates), der Nutzer entscheidet ueber die UI (U-10).
2. Vierte Scoring-Kategorie "Kontext/Makro" nutzt liquiditaets_regime/zyklus_risiko/
   btc_matrix_state aus agent/regime.py (dort bereits berechnet, kein Zusatz-Call).
3. Deterministisches Scoring hier komplett ohne Groq - die optionale P-5-Begruendung
   (hybrid: Klick ODER automatisch per Konfig-Schalter) ist eine separate Funktion.

Bekannte, dokumentierte Vereinfachungen (nicht stillschweigend, siehe Plan):
- Stablecoin-Erkennung ueber Preis nahe 1 $ (kein Categories-API-Call pro Kandidat).
- Alters-Schaetzung ueber `atl_date` (CoinGecko liefert kein echtes Listing-Datum) -
  fuer reine Trending-Funde (nicht auch in Top-Gainers) NICHT verfuegbar, da
  `/search/trending` kein atl_date liefert und der Ergaenzungs-Call (simple/price)
  ebenfalls keins hat - solche Kandidaten fallen durch den Alters-Filter, es sei denn
  sie sind auch ueber Top-Gainers gefunden worden.
- Narrativ-Abdeckung (A(MS)-5) nicht bewertet (bräuchte einen Zusatz-Call pro Kandidat)."""
from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

import numpy as np

import database.db as db
from agent.krypto.regime import RegimeResult
from agent.krypto.risk_gate import small_cap_budget_headroom
from api.coingecko import CoinGeckoClient, MarketCoin
from api.history import backfill_history
from config import WatchlistAsset
from database.models import MarktscanCandidate
from indicators.calculations import TechnicalSnapshot, build_technical_snapshot, latest_value

logger = logging.getLogger(__name__)

# Kategorie-Basiswerte je Tier (Stufe B Fundamental) - VORLAEUFIG.
_TIER_BASIS = {"tier1": 70.0, "tier2": 50.0, "tier3": 30.0}
# Bonus-/Malus-Tabellen fuer Kontext/Makro (Stufe B) - VORLAEUFIG, eigene, dokumentierte
# Einteilung (keine Nachbildung eines kommerziellen Modells).
_LIQUIDITAET_BONUS = {
    "expansiv": 20.0, "restriktiv": -20.0, "gemischt": 0.0,
    "widerspruechlich": 0.0, "unbekannt": 0.0,
}
_BTC_MATRIX_BONUS = {
    "altseason": 15.0, "btc_season": -10.0, "baer_flucht": -15.0,
    "unklar_defensiv": -5.0, "nicht_verfuegbar": 0.0,
}


def _is_probable_stablecoin(coin: MarketCoin) -> bool:
    """Grobe Naeherung ohne Zusatz-API-Call - Preis nahe 1 $ gilt als Verdacht.
    Dokumentierter Kompromiss, kein exakter Check (siehe Modul-Docstring)."""
    return coin.price_usd is not None and abs(coin.price_usd - 1.0) < 0.02


def _estimate_age_days(atl_date: str | None) -> int | None:
    """Alters-Naeherung ueber das Datum des Allzeittiefs - CoinGecko liefert kein
    echtes Listing-Datum (live geprueft 2026-07-09, siehe Plan). Untergrenze, kein
    exakter Wert."""
    if atl_date is None:
        return None
    try:
        atl = datetime.fromisoformat(atl_date.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (datetime.now(timezone.utc) - atl).days


def classify_tier(market_cap_usd: float | None, tiers_cfg: dict) -> str | None:
    if market_cap_usd is None:
        return None
    if market_cap_usd >= tiers_cfg["tier1_min_marktkap_usd"]:
        return "tier1"
    if market_cap_usd >= tiers_cfg["tier2_min_marktkap_usd"]:
        return "tier2"
    if market_cap_usd >= tiers_cfg["tier3_min_marktkap_usd"]:
        return "tier3"
    return None


@dataclass
class StufeAResult:
    bestanden: bool
    begruendung: str
    tier: str | None
    vol_marktkap_ratio: float | None
    alter_tage_geschaetzt: int | None


def apply_stufe_a_filters(coin: MarketCoin, marktscan_cfg: dict) -> StufeAResult:
    tier = classify_tier(coin.market_cap_usd, marktscan_cfg["tiers"])
    filter_cfg = marktscan_cfg["filter"]
    gruende: list[str] = []

    if tier is None:
        gruende.append(f"Marktkap. {coin.market_cap_usd} unter Tier-3-Untergrenze")
    if filter_cfg["stablecoins_ausschliessen"] and _is_probable_stablecoin(coin):
        gruende.append("vermutlich Stablecoin (Preis nahe 1 $)")
    if coin.volume_24h_usd is None or coin.volume_24h_usd < filter_cfg["min_volumen_24h_usd"]:
        gruende.append(
            f"24h-Volumen {coin.volume_24h_usd} unter Mindestwert {filter_cfg['min_volumen_24h_usd']}"
        )

    vol_mcap_ratio = None
    if coin.volume_24h_usd is not None and coin.market_cap_usd:
        vol_mcap_ratio = coin.volume_24h_usd / coin.market_cap_usd
        if not (filter_cfg["vol_marktkap_ratio_min"] <= vol_mcap_ratio <= filter_cfg["vol_marktkap_ratio_max"]):
            gruende.append(f"Volumen/Marktkap.-Verhältnis {vol_mcap_ratio:.4f} außerhalb der Bandbreite")

    alter_tage = _estimate_age_days(coin.atl_date)
    if alter_tage is None or alter_tage < filter_cfg["min_alter_tage"]:
        gruende.append(f"geschätztes Alter {alter_tage} Tage unter Mindestalter {filter_cfg['min_alter_tage']}")

    bestanden = len(gruende) == 0
    begruendung = "alle Stufe-A-Filter bestanden" if bestanden else "; ".join(gruende)
    return StufeAResult(bestanden, begruendung, tier, vol_mcap_ratio, alter_tage)


def score_technik(
    price_usd: float | None, change_24h_pct: float | None, snapshot: TechnicalSnapshot | None
) -> tuple[float | None, dict]:
    """0-100. 24h-Änderung ist immer da; RSI/EMA-20/MACD/Bollinger nur, falls ein
    gezielter Backfill genug Historie ergeben hat (siehe `_try_backfill_snapshot`).
    EMA-50/-200/Fibonacci/ATR bleiben für Neufunde praktisch immer unverfügbar."""
    signale: dict = {}
    bullish, total = 0.0, 0.0

    if change_24h_pct is not None:
        signale["change_24h_pct"] = change_24h_pct
        total += 1
        if change_24h_pct > 0:
            bullish += 1

    if snapshot is not None:
        rsi = latest_value(snapshot.rsi)
        if rsi is not None:
            signale["rsi_14"] = rsi
            total += 1
            if 30 < rsi < 70:
                bullish += 1

        ema20 = latest_value(snapshot.ema.get(20))
        if ema20 is not None and price_usd is not None:
            signale["ema_20"] = ema20
            total += 1
            if price_usd > ema20:
                bullish += 1

        if snapshot.macd.available:
            hist_arr = np.asarray(snapshot.macd.value["histogram"], dtype=float)
            valid = hist_arr[~np.isnan(hist_arr)]
            if len(valid):
                histogram = float(valid[-1])
                signale["macd_histogram"] = histogram
                total += 1
                if histogram > 0:
                    bullish += 1

    if total == 0:
        return None, signale
    return round(bullish / total * 100, 1), signale


def score_fundamental(stufe_a: StufeAResult, filter_cfg: dict) -> tuple[float | None, dict]:
    if stufe_a.tier is None:
        return None, {}
    tier_basis = _TIER_BASIS[stufe_a.tier]
    signale: dict = {"tier": stufe_a.tier, "tier_basis": tier_basis}

    alter_bonus = 0.0
    if stufe_a.alter_tage_geschaetzt is not None:
        alter_bonus = min(stufe_a.alter_tage_geschaetzt / 730 * 15, 15.0)
        signale["alter_bonus"] = round(alter_bonus, 1)

    ratio_bonus = 0.0
    if stufe_a.vol_marktkap_ratio is not None:
        band_min, band_max = filter_cfg["vol_marktkap_ratio_min"], filter_cfg["vol_marktkap_ratio_max"]
        band_mid = (band_min * band_max) ** 0.5
        distanz = abs(stufe_a.vol_marktkap_ratio - band_mid) / band_mid if band_mid else 1.0
        ratio_bonus = max(0.0, 15.0 * (1 - min(distanz, 1.0)))
        signale["ratio_bonus"] = round(ratio_bonus, 1)

    score = min(tier_basis + alter_bonus + ratio_bonus, 100.0)
    return round(score, 1), signale


def score_momentum(
    change_24h_pct: float | None, trending_rank: int | None
) -> tuple[float | None, dict]:
    if change_24h_pct is None:
        return None, {}
    signale: dict = {"change_24h_pct": change_24h_pct}
    change_score = 50.0 + max(min(change_24h_pct, 50.0), -50.0)
    signale["change_score"] = round(change_score, 1)

    rank_bonus = 0.0
    if trending_rank is not None:
        rank_bonus = max(0.0, 20.0 * (16 - trending_rank) / 15)
        signale["trending_rank"] = trending_rank
        signale["rank_bonus"] = round(rank_bonus, 1)

    return round(min(max(change_score + rank_bonus, 0.0), 100.0), 1), signale


def score_kontext_makro(regime_result: RegimeResult) -> tuple[float | None, dict]:
    """Einmal pro Scan-Lauf berechnet (regime_result ist BTC-/makro-weit, nicht
    asset-spezifisch) und fuer alle Kandidaten dieses Laufs identisch verwendet."""
    score = 50.0
    signale: dict = {}

    liq_bonus = _LIQUIDITAET_BONUS.get(regime_result.liquiditaets_regime, 0.0)
    score += liq_bonus
    signale["liquiditaets_regime"] = regime_result.liquiditaets_regime
    signale["liq_bonus"] = liq_bonus

    if regime_result.zyklus_risiko is not None:
        risiko_effekt = (0.5 - regime_result.zyklus_risiko) * 40
        score += risiko_effekt
        signale["zyklus_risiko"] = regime_result.zyklus_risiko
        signale["risiko_effekt"] = round(risiko_effekt, 1)

    matrix_bonus = _BTC_MATRIX_BONUS.get(regime_result.btc_matrix_state, 0.0)
    score += matrix_bonus
    signale["btc_matrix_state"] = regime_result.btc_matrix_state
    signale["matrix_bonus"] = matrix_bonus

    return round(min(max(score, 0.0), 100.0), 1), signale


def combine_scores(scores: dict[str, float | None], gewichte: dict) -> float | None:
    """Stufe C. Kategorien mit `None`-Score werden aus Zaehler UND Nenner
    ausgeschlossen (nicht als 0 gewertet) - eine fehlende Kategorie darf den Score
    nicht kuenstlich druecken."""
    zaehler, nenner = 0.0, 0.0
    for kategorie, score in scores.items():
        gewicht = gewichte.get(f"gewicht_{kategorie}", 0.0)
        if score is not None:
            zaehler += gewicht * score
            nenner += gewicht
    if nenner <= 0:
        return None
    return round(zaehler / nenner, 1)


def classify(score_gesamt: float | None, schwellen_cfg: dict) -> tuple[str, str]:
    """Stufe D. Schwellen sind VORLAEUFIG (config.yaml marktscan.schwellen)."""
    if score_gesamt is None:
        return "kein_treffer", "Gesamt-Score nicht berechenbar (keine Kategorie bewertbar)"
    kauf_ab = schwellen_cfg["score_kaufkandidat_ab"]
    watchlist_ab = schwellen_cfg["score_watchlist_wuerdig_ab"]
    if score_gesamt >= kauf_ab:
        return "kaufkandidat", f"Score {score_gesamt:.1f} >= {kauf_ab} (Kaufkandidat-Schwelle)"
    if score_gesamt >= watchlist_ab:
        return "watchlist_wuerdig", f"Score {score_gesamt:.1f} >= {watchlist_ab} (Watchlist-Schwelle)"
    return "kein_treffer", f"Score {score_gesamt:.1f} unter der Watchlist-Schwelle ({watchlist_ab})"


def _try_backfill_snapshot(
    coingecko_client: CoinGeckoClient, conn, coingecko_id: str, symbol: str
) -> TechnicalSnapshot | None:
    """Gezielter Backfill NUR fuer Stufe-A-Ueberlebende (Kosten sparen, siehe
    run_scan()). Nebeneffekt: die geladene Historie bleibt in price_history stehen -
    wird der Kandidat spaeter manuell in die echte Watchlist uebernommen, hat
    agent/pipeline.py::generate_signal() dafuer schon Vorlauf-Historie, kein
    Kaltstart. Kein WatchlistAsset-Objekt in der DB noetig, `backfill_history()` ist
    bereits rein duck-typed (`.coingecko_id`/`.symbol`)."""
    try:
        asset = WatchlistAsset(
            symbol=symbol, name=symbol, typ="taktisch", status="watchlist", coingecko_id=coingecko_id
        )
        backfill_history(coingecko_client, conn, asset)
        history = db.get_price_history(conn, coingecko_id)
        dates = np.array([p.date for p in history])
        closes = np.array([p.price_usd for p in history], dtype=float)
        valid = ~np.isnan(closes)
        dates, closes = dates[valid], closes[valid]
        if len(closes) < 15:  # RSI-14-Mindestanforderung als Untergrenze fuers Lohnen
            return None
        return build_technical_snapshot(closes, dates, [])
    except Exception as exc:
        logger.info("Backfill/Snapshot für Marktscan-Kandidat %s fehlgeschlagen: %s", symbol, exc)
        return None


def _duplicate_should_skip(conn, coingecko_id: str, watchlist) -> bool:
    """A(MS)-3 Duplikat-Check: nichts bereits auf der echten Watchlist oder bereits
    vom Nutzer entschiedenes (verworfen/uebernommen) erneut anzeigen."""
    if any(a.coingecko_id == coingecko_id for a in watchlist):
        return True
    status = db.get_latest_marktscan_status_by_coingecko_id(conn, coingecko_id)
    return status in ("nutzer_verworfen", "nutzer_behalten_manuell_uebernommen")


def _collect_raw_candidates(coingecko_client: CoinGeckoClient) -> dict[str, dict]:
    """Fasst Top-Gainers und Trending zusammen (MS-2). Ein Trending-Coin, der nicht
    auch unter den Top-Gainers ist, braucht einen Zusatz-Call fuer Marktdaten -
    hat dann aber kein atl_date (siehe Modul-Docstring)."""
    raw: dict[str, dict] = {}
    try:
        for coin in coingecko_client.fetch_top_gainers():
            raw[coin.coingecko_id] = {"coin": coin, "source": "top_gainers", "trending_rank": None}
    except Exception as exc:
        logger.warning("Top-Gainers-Abruf für Marktscan fehlgeschlagen: %s", exc)

    try:
        trending = coingecko_client.get_trending()
    except Exception as exc:
        trending = []
        logger.warning("Trending-Abruf für Marktscan fehlgeschlagen: %s", exc)

    for t in trending:
        if t.coingecko_id in raw:
            raw[t.coingecko_id]["trending_rank"] = t.trending_rank
            continue
        try:
            simple = coingecko_client.get_simple_prices([t.coingecko_id])
            data = simple.get(t.coingecko_id, {})
            coin = MarketCoin(
                coingecko_id=t.coingecko_id, symbol=t.symbol, name=t.name,
                price_usd=data.get("usd"), market_cap_usd=data.get("usd_market_cap"),
                volume_24h_usd=data.get("usd_24h_vol"), change_24h_pct=data.get("usd_24h_change"),
                atl_date=None,
            )
            raw[t.coingecko_id] = {"coin": coin, "source": "trending", "trending_rank": t.trending_rank}
        except Exception as exc:
            logger.info("Marktdaten für Trending-Coin %s nicht abrufbar: %s", t.coingecko_id, exc)
    return raw


def run_scan(
    coingecko_client: CoinGeckoClient,
    conn,
    watchlist,
    regime_result: RegimeResult,
    config_dict: dict,
    groq_client=None,
    kraken_client=None,
) -> list[MarktscanCandidate]:
    """Orchestriert Stufe A-D fuer einen kompletten Scan-Lauf. Speichert jeden
    Kandidaten (auch `kein_treffer`, Audit/Z-4) und gibt die Liste zurueck.
    `groq_client`/`kraken_client` sind optional (P-8) - ohne Groq-Client wird der
    automatische Kaufkandidat-Begruendungs-Zweig einfach uebersprungen, auch wenn
    `marktscan.groq_automatisch_kaufkandidaten` in config.yaml aktiviert ist."""
    marktscan_cfg = config_dict["marktscan"]
    scan_run_id = f"{datetime.now(timezone.utc).isoformat()}_{uuid.uuid4().hex[:8]}"
    raw = _collect_raw_candidates(coingecko_client)

    kontext_score, kontext_signale = score_kontext_makro(regime_result)
    gewichte = config_dict["regime"]["profile"].get(regime_result.regime, {})

    # Handelsboersen-Check (Nutzer-Wunsch 2026-07-09): einmal pro Scan-Lauf, nicht
    # pro Kandidat. Bewusst NUR Warnung, kein Stufe-A-Ausschluss - siehe
    # database/models.py::MarktscanCandidate.bitpanda_gelistet.
    try:
        from api.bitpanda import get_listed_assets
        from api.bitpanda import is_listed as bitpanda_is_listed

        bitpanda_assets = get_listed_assets()
    except Exception as exc:
        bitpanda_assets = None
        logger.info("Bitpanda-Listing-Abruf fehlgeschlagen: %s", exc)

    holdings = db.get_all_holdings(conn)
    latest_prices = db.get_latest_prices(conn)

    candidates: list[MarktscanCandidate] = []
    for coingecko_id, entry in raw.items():
        if _duplicate_should_skip(conn, coingecko_id, watchlist):
            continue
        coin: MarketCoin = entry["coin"]
        stufe_a = apply_stufe_a_filters(coin, marktscan_cfg)
        bitpanda_gelistet = (
            bitpanda_is_listed(coin.symbol, bitpanda_assets, name=coin.name)
            if bitpanda_assets is not None else None
        )

        snapshot = None
        if stufe_a.bestanden:
            snapshot = _try_backfill_snapshot(coingecko_client, conn, coingecko_id, coin.symbol)

        tech_score, tech_signale = score_technik(coin.price_usd, coin.change_24h_pct, snapshot)
        fund_score, fund_signale = score_fundamental(stufe_a, marktscan_cfg["filter"])
        mom_score, mom_signale = score_momentum(coin.change_24h_pct, entry["trending_rank"])

        scores = {
            "technik": tech_score, "fundamental": fund_score, "momentum": mom_score,
            "kontext_makro": kontext_score,
        }
        small_cap_budget_hinweis = None
        if stufe_a.bestanden:
            score_gesamt = combine_scores(scores, gewichte)
            einstufung, einstufung_begruendung = classify(score_gesamt, marktscan_cfg["schwellen"])
            # Stufe D + Small-Cap-Budget: ein Tier-3-Kaufkandidat ohne Budget-Headroom
            # wird auf watchlist_wuerdig heruntergestuft - sonst wuerde ein
            # "Kaufkandidat" angezeigt, den agent/risk_gate.py::pre_check() beim
            # Versuch sofort veto'en wuerde (R-5.10, siehe Plan).
            if einstufung == "kaufkandidat" and stufe_a.tier == "tier3":
                headroom = small_cap_budget_headroom(watchlist, holdings, latest_prices, regime_result, config_dict)
                if headroom <= 0:
                    small_cap_budget_hinweis = (
                        f"Score erreicht die Kaufkandidat-Schwelle, aber Small-Cap-Budget im "
                        f"Regime '{regime_result.regime}' bereits ausgeschöpft (Headroom {headroom:.1f} "
                        "Prozentpunkte) - auf watchlist_wuerdig heruntergestuft."
                    )
                    einstufung = "watchlist_wuerdig"
        else:
            score_gesamt = None
            einstufung, einstufung_begruendung = "kein_treffer", f"Stufe A nicht bestanden: {stufe_a.begruendung}"

        if bitpanda_gelistet is False and einstufung != "kein_treffer":
            einstufung_begruendung += " ⚠ NICHT bei Bitpanda gelistet - dort aktuell nicht kaufbar."

        candidate = MarktscanCandidate(
            coingecko_id=coingecko_id, symbol=coin.symbol, name=coin.name,
            discovered_at=datetime.now(timezone.utc).isoformat(), discovery_source=entry["source"],
            scan_run_id=scan_run_id, filter_a_bestanden=stufe_a.bestanden,
            tier=stufe_a.tier, market_cap_usd=coin.market_cap_usd, volume_24h_usd=coin.volume_24h_usd,
            vol_marktkap_ratio=stufe_a.vol_marktkap_ratio, alter_tage_geschaetzt=stufe_a.alter_tage_geschaetzt,
            alter_tage_quelle="atl_date_proxy" if coin.atl_date else None,
            filter_a_begruendung=stufe_a.begruendung,
            bitpanda_gelistet=bitpanda_gelistet,
            price_usd=coin.price_usd, change_24h_pct=coin.change_24h_pct,
            score_technik=tech_score, score_fundamental=fund_score, score_momentum=mom_score,
            score_kontext_makro=kontext_score,
            signale_technik_json=json.dumps(tech_signale, ensure_ascii=False),
            signale_fundamental_json=json.dumps(fund_signale, ensure_ascii=False),
            signale_momentum_json=json.dumps(mom_signale, ensure_ascii=False),
            signale_kontext_json=json.dumps(kontext_signale, ensure_ascii=False),
            score_gesamt=score_gesamt,
            gewichte_json=json.dumps(gewichte, ensure_ascii=False),
            regime_bei_scan=regime_result.regime,
            einstufung=einstufung, einstufung_begruendung=einstufung_begruendung,
            small_cap_budget_hinweis=small_cap_budget_hinweis,
        )
        candidate.id = db.upsert_marktscan_candidate(conn, candidate)
        candidates.append(candidate)

        # Hybrid Groq-Begruendung (Design-Entscheidung 3, siehe Plan): der manuelle
        # UI-Klick-Pfad ruft generate_candidate_writeup() direkt auf; hier nur der
        # AUTOMATISCHE Zweig, ausschliesslich wenn per config.yaml explizit
        # eingeschaltet UND ein Groq-Client vorhanden ist (P-8: nie hart von einem
        # KI-Key abhaengen).
        if (
            einstufung == "kaufkandidat"
            and groq_client is not None
            and marktscan_cfg.get("groq_automatisch_kaufkandidaten", False)
        ):
            try:
                parsed = generate_candidate_writeup(
                    candidate, regime_result, groq_client, kraken_client, conn, watchlist, config_dict
                )
                db.update_marktscan_candidate_groq_writeup(
                    conn, candidate.id, parsed.get("short_reasoning"),
                    json.dumps(parsed.get("long_reasoning") or {}, ensure_ascii=False),
                )
            except Exception as exc:
                logger.warning(
                    "Automatische Groq-Begründung für Marktscan-Kandidat %s fehlgeschlagen: %s",
                    candidate.symbol, exc,
                )

    return candidates


def generate_candidate_writeup(
    candidate: MarktscanCandidate,
    regime_result: RegimeResult,
    groq_client,
    kraken_client,
    conn,
    watchlist,
    config_dict: dict,
) -> dict:
    """Baut ein Facts-Objekt analog zu agent/analyst.py::build_facts() aus einem
    bereits gescorten Kandidaten und ruft call_groq_for_signal() UNVERAENDERT auf -
    kein zweites Prompt-Schema (Design-Entscheidung 3, siehe Plan). Zwei Aufrufpfade
    fuehren hierher: manueller UI-Klick (jederzeit, jeder Kandidat) und der
    automatische Zweig in run_scan() (nur kaufkandidat + Konfig-Schalter). Wirft
    AnalystResponseInvalid unveraendert weiter - der Aufrufer entscheidet, wie er
    damit umgeht (siehe agent/pipeline.py fuer das etablierte Muster)."""
    from agent.krypto.analyst import build_facts, call_groq_for_signal
    from agent.krypto.anticyclic import assess as assess_anticyclic
    from agent.krypto.pipeline import fetch_market_context
    from agent.krypto.risk_gate import pre_check
    from database.models import PriceSnapshot
    from indicators.calculations import summarize_confluence

    asset = WatchlistAsset(
        symbol=candidate.symbol, name=candidate.name, typ="taktisch", status="watchlist",
        coingecko_id=candidate.coingecko_id,
    )
    latest_price = PriceSnapshot(
        symbol=candidate.symbol, coingecko_id=candidate.coingecko_id, price_usd=candidate.price_usd,
        price_eur=candidate.price_eur, market_cap_usd=candidate.market_cap_usd,
        volume_24h_usd=candidate.volume_24h_usd, change_24h_pct=candidate.change_24h_pct,
        fetched_at=candidate.discovered_at,
    )

    history = db.get_price_history(conn, candidate.coingecko_id)
    dates = np.array([p.date for p in history])
    closes = np.array([p.price_usd for p in history], dtype=float)
    valid = ~np.isnan(closes)
    dates, closes = dates[valid], closes[valid]
    snapshot = build_technical_snapshot(closes, dates, [])

    latest_close = float(closes[-1]) if len(closes) else candidate.price_usd
    confluence = summarize_confluence(snapshot, latest_close)

    latest_prices = dict(db.get_latest_prices(conn))
    latest_prices[candidate.symbol] = latest_price
    risk_result = pre_check(asset, watchlist, conn, latest_prices, snapshot, regime_result, config_dict)
    anticyclic_context = assess_anticyclic(asset, kraken_client, closes)
    market_context = fetch_market_context()

    price_age_minutes = None
    try:
        fetched = datetime.fromisoformat(candidate.discovered_at)
        if fetched.tzinfo is None:
            fetched = fetched.replace(tzinfo=timezone.utc)
        price_age_minutes = (datetime.now(timezone.utc) - fetched).total_seconds() / 60
    except ValueError:
        pass

    strategien_aktiv = [s["name"] for s in config_dict["strategien"] if s["aktiv"]]
    regime_profile = config_dict["regime"]["profile"].get(regime_result.regime, {})

    facts = build_facts(
        asset, latest_price, None, snapshot, confluence, regime_result, regime_profile,
        risk_result, anticyclic_context, strategien_aktiv, price_age_minutes, market_context,
    )
    return call_groq_for_signal(groq_client, facts)
