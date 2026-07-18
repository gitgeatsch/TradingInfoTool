"""Multi-Asset-Batch (2026-07-18) - automatischer Signal-Batch fuer Aktien/
Rohstoffe/Hedge/Themen-ETFs (VST/PLTR, OD7N/OD7H/OD7C/OD7L, DBPK/3QSS,
VVMX/X136/EXH3/CEBS/ISOC - 13 Assets). Bisher NUR ueber den manuellen "Signal
berechnen"-Klick in ui/signals_view.py erreichbar - im Gegensatz zu Krypto
(agent/krypto/budget_allocator.py, 15-Min-Takt) gab es dafuer KEINE
automatische Bewertung (Nutzer-Fund 2026-07-18: das letzte VST-Signal war 3
Tage alt, kein einziger automatischer Versuch seit Erstellung der Rohstoff/
Hedge-Pipelines).

Nachtrag (gleicher Tag, Multi-Asset-Vollstaendigkeitspruefung): die 5
Themen-ETFs standen zu diesem Zeitpunkt bereits als Watchlist-Eintraege in
config.yaml, aber OHNE jede Pipeline (weder manuell noch automatisch) -
agent/themen_etf/ + diese Erweiterung schliessen die Luecke.

Bewusst EIGENER, separater Job (nicht Tier 4 im bestehenden Budget-
Allocator, siehe Regelwerksmanual-Nachtrag fuer die volle Begruendung):
- Die dortige strikte 1>2>3-Kaskade (Hebel>Marktscan>Spot) wuerde ein
  Tier 4 an geschaeftigen Tagen nie erreichen - genau das Problem, das
  hier geloest werden soll.
- Aktien/Rohstoffe/Hedge bewegen sich strukturell langsamer (Boersenzeiten,
  Wochenenden, 5-Tage-OHLC-Staleness-Schwelle vs. Kryptos 2 Tage) - der
  15-Min-Krypto-Takt waere fuer diese Assetklassen verschwendet.
- Nutzt dasselbe gemeinsame LLM-Tagesbudget (count_real_llm_calls_today_by_
  provider zaehlt bereits assetklassen-uebergreifend ueber die signals-
  Tabelle) OHNE die gut getestete Krypto-Kaskade anzufassen (kein
  Regressionsrisiko fuer einen kritischen, funktionierenden Pfad).

Cooldown bewusst NUR 2-stufig (gehalten/beobachtet), kein drittes
"ausgemustert"-Level wie bei Krypto - alle 13 Assets sind aktuell
beobachtungsstatus="beobachtung", ein ausgemustertes Multi-Asset-Symbol
existiert noch nicht. "Gehalten" wird wie bei Krypto (signal_batch.py)
live aus der holdings-Tabelle abgeleitet, nicht aus einem statischen Feld.

Keine Marktscan-Aequivalent-Logik - feste, kleine Watchlist (13 Assets),
keine Discovery (Multi-Asset-Roadmap Phase 4, bewusst zurueckgestellt)."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

import database.db as db

logger = logging.getLogger(__name__)


@dataclass
class MultiAssetBatchResult:
    verarbeitet: list[str] = field(default_factory=list)
    fehlgeschlagen: list[str] = field(default_factory=list)
    uebersprungen_cooldown: int = 0
    provider_je_symbol: dict[str, str] = field(default_factory=dict)
    ergebnis_objekt: dict[str, object] = field(default_factory=dict)
    mistral_calls_verbraucht: int = 0
    gemini_calls_verbraucht: int = 0


def _kandidaten(watchlist: list) -> list:
    from agent.hedge.pipeline import SYMBOL_ZU_HEBEL_FAKTOR as _hedge_symbole

    return [
        a for a in watchlist
        if a.assetklasse in ("aktien", "rohstoffe") or a.symbol in _hedge_symbole
        # Themen-ETFs (2026-07-18, Multi-Asset-Vollstaendigkeitspruefung): restliche
        # assetklasse=="etf"-Assets, die KEINE Hedge-Instrumente sind (VVMX/X136/
        # EXH3/CEBS/ISOC) - standen bis hierher als einzige Watchlist-Assets ganz
        # ohne Pipeline da, siehe agent/themen_etf/pipeline.py Modul-Docstring.
        or (a.assetklasse == "etf" and a.symbol not in _hedge_symbole)
    ]


def _pipeline_fuer(asset):
    if asset.assetklasse == "aktien":
        from agent.aktien.pipeline import generate_signal
        return generate_signal
    if asset.assetklasse == "rohstoffe":
        from agent.rohstoff.pipeline import generate_signal
        return generate_signal
    from agent.hedge.pipeline import SYMBOL_ZU_HEBEL_FAKTOR as _hedge_symbole
    if asset.assetklasse == "etf" and asset.symbol not in _hedge_symbole:
        from agent.themen_etf.pipeline import generate_signal
        return generate_signal
    from agent.hedge.pipeline import generate_signal
    return generate_signal


def _ist_faellig(
    letztes_signal, gehalten: bool, cooldown_gehalten_stunden: float, cooldown_beobachtet_stunden: float,
) -> bool:
    if letztes_signal is None:
        return True
    letzter_zeitpunkt = datetime.fromisoformat(letztes_signal.created_at)
    if letzter_zeitpunkt.tzinfo is None:
        letzter_zeitpunkt = letzter_zeitpunkt.replace(tzinfo=timezone.utc)
    alter_stunden = (datetime.now(timezone.utc) - letzter_zeitpunkt).total_seconds() / 3600
    schwelle = cooldown_gehalten_stunden if gehalten else cooldown_beobachtet_stunden
    return alter_stunden >= schwelle


def run_multi_asset_batch(
    conn_factory,
    watchlist: list,
    groq_client,
    coingecko_client,
    config_dict: dict,
    gemini_client=None,
    mistral_client=None,
) -> MultiAssetBatchResult:
    result = MultiAssetBatchResult()
    cfg = config_dict.get("multi_asset_batch", {})
    if not cfg.get("aktiv", True):
        return result

    cooldown_gehalten = cfg.get("cooldown_stunden_gehalten", 24)
    cooldown_beobachtet = cfg.get("cooldown_stunden_beobachtet", 72)
    # Dieselben Budget-Werte wie der Krypto-Allocator (agent/krypto/
    # budget_allocator.py) - EIN gemeinsames Tagesbudget je Provider, kein
    # separater Deckel fuer Multi-Asset (die 8 Kandidaten sind eine kleine
    # Ergaenzung zum bestehenden Verbrauch, kein eigenes Kontingent noetig).
    ba_cfg = config_dict.get("budget_allocator", {})
    mistral_budget = ba_cfg.get("mistral_taegliches_budget", 150)
    gemini_budget = ba_cfg.get("gemini_taegliches_budget", 200)

    conn = conn_factory()
    try:
        gehaltene_symbole = {
            h.symbol for h in db.get_all_holdings(conn)
            if (h.quantity or 0.0) + (h.staked_quantity or 0.0) > 0.0
        }
        faellige = []
        for asset in _kandidaten(watchlist):
            gehalten = asset.symbol in gehaltene_symbole
            letztes = db.get_latest_signal(conn, asset.symbol)
            if _ist_faellig(letztes, gehalten, cooldown_gehalten, cooldown_beobachtet):
                faellige.append(asset)
            else:
                result.uebersprungen_cooldown += 1
        tages_verbraucht = {
            "mistral": db.count_real_llm_calls_today_by_provider(conn, "mistral:"),
            "gemini": db.count_real_llm_calls_today_by_provider(conn, "gemini:"),
        }
    finally:
        conn.close()
    tages_budget = {"mistral": mistral_budget, "gemini": gemini_budget}

    def _mit_conn(fn):
        """Eigene Connection je Call (gleiches Muster wie budget_allocator.py::
        _mit_conn()) - ein LLM-Call ist potenziell langsam, eine gemeinsame
        lang gehaltene Connection ueber alle Kandidaten waere unnoetig
        fehleranfaellig."""
        c = conn_factory()
        try:
            return fn(c)
        finally:
            c.close()

    for asset in faellige:
        pipeline_fn = _pipeline_fuer(asset)
        schluessel = asset.symbol
        calls = [
            ("groq", lambda a=asset, fn=pipeline_fn: _mit_conn(
                lambda c: fn(a, watchlist, c, groq_client, coingecko_client)
            )),
        ]
        if mistral_client is not None:
            calls.append(("mistral", lambda a=asset, fn=pipeline_fn: _mit_conn(
                lambda c: fn(a, watchlist, c, mistral_client, coingecko_client)
            )))
        if gemini_client is not None:
            calls.append(("gemini", lambda a=asset, fn=pipeline_fn: _mit_conn(
                lambda c: fn(a, watchlist, c, gemini_client, coingecko_client)
            )))

        ok = False
        last_exc: Exception | None = None
        for provider_name, call_fn in calls:
            if provider_name in tages_budget and tages_verbraucht[provider_name] >= tages_budget[provider_name]:
                continue
            try:
                res = call_fn()
                if getattr(res, "gate_passed", True) is False:
                    ok = True
                    break
                result.provider_je_symbol[schluessel] = provider_name
                result.ergebnis_objekt[schluessel] = res
                if provider_name in tages_verbraucht:
                    tages_verbraucht[provider_name] += 1
                    if provider_name == "mistral":
                        result.mistral_calls_verbraucht = tages_verbraucht["mistral"]
                    elif provider_name == "gemini":
                        result.gemini_calls_verbraucht = tages_verbraucht["gemini"]
                ok = True
                break
            except Exception as exc:
                last_exc = exc
                continue
        if ok:
            result.verarbeitet.append(schluessel)
        else:
            logger.warning("Multi-Asset-Batch: alle Provider fuer %s fehlgeschlagen (letzter Fehler: %s)", schluessel, last_exc)
            result.fehlgeschlagen.append(schluessel)

    return result
