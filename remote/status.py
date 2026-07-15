"""Status-Aggregator fuer die Remote-Steuer-Seite (2026-07-11, siehe
Basisinfos/Regelwerksmanual.md Kap. 12/13). Reine Datenbeschaffung, KEINE
Flask-Abhaengigkeit - eigenstaendig testbar, gleiches Trennungsprinzip wie
staleness.py (Domaenenlogik) vs. ui/formatting.py (Anzeige)."""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import config as config_module
import database.db as db
import scheduler.background as background
from staleness import is_price_stale

_TREFFER_EINSTUFUNGEN = {"kaufkandidat", "watchlist_wuerdig"}


@dataclass
class RemoteStatus:
    generated_at: str
    prices: list[dict] = field(default_factory=list)
    portfolio_value_eur: float | None = None
    cash_reserve_eur: float = 0.0
    cash_reserve_synced_at: str | None = None
    staked_value_eur: float = 0.0
    marktscan_last: dict | None = None
    recent_errors: list[str] = field(default_factory=list)
    jobs_running: dict[str, bool] = field(default_factory=dict)
    jobs_running_seit_minuten: dict[str, float | None] = field(default_factory=dict)
    budget_heute: dict | None = None
    provider_performance: dict | None = None
    api_health: dict | None = None

    def to_dict(self) -> dict:
        return {
            "generated_at": self.generated_at,
            "prices": self.prices,
            "portfolio_value_eur": self.portfolio_value_eur,
            "cash_reserve_eur": self.cash_reserve_eur,
            "cash_reserve_synced_at": self.cash_reserve_synced_at,
            "staked_value_eur": self.staked_value_eur,
            "marktscan_last": self.marktscan_last,
            "recent_errors": self.recent_errors,
            "jobs_running": self.jobs_running,
            "jobs_running_seit_minuten": self.jobs_running_seit_minuten,
            "budget_heute": self.budget_heute,
            "provider_performance": self.provider_performance,
            "api_health": self.api_health,
        }


def build_status(conn: sqlite3.Connection, watchlist: list, log_path: Path, error_tail_lines: int = 5) -> RemoteStatus:
    latest_prices = db.get_latest_prices(conn)
    active_symbols = {a.symbol for a in watchlist if a.status == "aktiv"}

    prices = []
    for symbol in sorted(active_symbols):
        snap = latest_prices.get(symbol)
        fetched_at = snap.fetched_at if snap else None
        prices.append(
            {
                "symbol": symbol,
                "price_eur": snap.price_eur if snap else None,
                "fetched_at": fetched_at,
                "stale": is_price_stale(fetched_at),
            }
        )

    holdings = db.get_all_holdings(conn)
    portfolio_value_eur = 0.0
    staked_value_eur = 0.0
    any_price = False
    for holding in holdings:
        snap = latest_prices.get(holding.symbol)
        if snap and snap.price_eur is not None:
            portfolio_value_eur += holding.quantity * snap.price_eur
            any_price = True
            # 2026-07-11, Nutzer-Fund: gestakte Menge ist ueber die normale Wallet-API
            # unsichtbar (importer/bitpanda_avg_cost.py::compute_staked_quantities()) -
            # additiv, echtes Vermoegen, nur voruebergehend nicht handelbar.
            if holding.staked_quantity:
                staked_value_eur += holding.staked_quantity * snap.price_eur
    portfolio_value_eur += staked_value_eur

    # RM-4/Konsistenz-Fix (2026-07-11): agent/krypto/risk_gate.py::pre_check()
    # zaehlt die Fiat-Cash-Reserve zum Portfoliowert dazu, diese Anzeige tat das
    # bisher nicht (gleicher Fund wie bei ui/portfolio.py::refresh()) - EUR ist
    # hier direkt (keine USD-Umrechnung noetig, die Remote-Seite zeigt nur EUR).
    fiat_cash_eur = db.get_cash_reserve_fiat_eur(conn)
    if fiat_cash_eur > 0:
        portfolio_value_eur += fiat_cash_eur
        any_price = True

    lock_status = background.get_lock_status()
    jobs_running = {name: info["locked"] for name, info in lock_status.items()}
    jobs_running_seit_minuten = {
        name: (info["running_since_seconds"] / 60 if info["running_since_seconds"] is not None else None)
        for name, info in lock_status.items()
    }

    return RemoteStatus(
        generated_at=datetime.now(timezone.utc).isoformat(),
        prices=prices,
        portfolio_value_eur=portfolio_value_eur if any_price else None,
        cash_reserve_eur=fiat_cash_eur,
        cash_reserve_synced_at=db.get_cash_reserve_synced_at(conn),
        staked_value_eur=staked_value_eur,
        marktscan_last=_get_marktscan_last(conn),
        recent_errors=_tail_log_errors(log_path, error_tail_lines),
        jobs_running=jobs_running,
        jobs_running_seit_minuten=jobs_running_seit_minuten,
        budget_heute=_get_budget_heute(conn),
        provider_performance=_get_provider_performance(conn),
        api_health=_get_api_health(conn),
    )


def _get_api_health(conn: sqlite3.Connection) -> dict:
    """Sichtbarkeit fuer das passive API-Gesundheits-Tracking (2026-07-15, siehe
    database/api_health.py::track_api_health()) - reiner Lesezugriff, keine neue
    Logik."""
    return db.get_api_health_status(conn)


def _get_provider_performance(conn: sqlite3.Connection) -> dict:
    """Sichtbarkeit fuer die Backward-Tracking-Provider-Performance (2026-07-15,
    siehe agent/krypto/backward_tracking.py::compute_provider_performance()) -
    reiner Lesezugriff, keine neue Logik. Erwartet aktuell noch leere/nahezu
    leere Ergebnisse (reine Infrastruktur, sammelt ab jetzt automatisch Daten)."""
    from agent.krypto.backward_tracking import compute_provider_performance

    return compute_provider_performance(conn)


def _get_budget_heute(conn: sqlite3.Connection) -> dict:
    """Budget-Sichtbarkeit fuer alle 3 Tiers des gemeinsamen Tagesbudgets
    (docs/budget_queue_design.md) - reiner Lesezugriff auf bereits vorhandene
    Zaehlfunktionen, keine neue Logik. taegliches_budget_gesamt ist EIN
    gemeinsamer Deckel ueber Hebel+Marktscan+Spot (kein Budget pro Tier)."""
    config_dict = config_module.load_config()
    gesamt = config_dict.get("budget_allocator", {}).get("taegliches_budget_gesamt", 15)
    hebel = db.count_real_hebel_signals_today(conn)
    marktscan = db.count_real_marktscan_writeups_today(conn)
    spot = db.count_real_signals_today(conn)
    return {
        "hebel": hebel,
        "marktscan": marktscan,
        "spot": spot,
        "verbraucht_gesamt": hebel + marktscan + spot,
        "gesamt": gesamt,
    }


def _get_marktscan_last(conn: sqlite3.Connection) -> dict | None:
    candidates = db.get_marktscan_candidates(conn, limit=500)
    if not candidates:
        return None
    latest_run_id = candidates[0].scan_run_id  # bereits DESC nach discovered_at sortiert
    latest_run = [c for c in candidates if c.scan_run_id == latest_run_id]
    treffer = [c for c in latest_run if c.einstufung in _TREFFER_EINSTUFUNGEN]
    return {
        "discovered_at": latest_run[0].discovered_at,
        "kandidaten": len(latest_run),
        "treffer": len(treffer),
    }


def _tail_log_errors(log_path: Path, max_lines: int, max_read_bytes: int = 200_000) -> list[str]:
    """Liest nur die letzten ~200 KB der Logdatei (Seek vom Ende), nicht die
    komplette Datei - die rotierende Logdatei kann bis zu 5 MB gross sein."""
    if not log_path.exists():
        return []
    try:
        with log_path.open("rb") as f:
            f.seek(0, 2)
            size = f.tell()
            f.seek(max(0, size - max_read_bytes))
            chunk = f.read().decode("utf-8", errors="replace")
    except OSError:
        return []

    error_lines = [line for line in chunk.splitlines() if " ERROR " in line or " CRITICAL " in line]
    return error_lines[-max_lines:]
