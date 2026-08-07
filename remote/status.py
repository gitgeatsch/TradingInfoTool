"""Status-Aggregator fuer die Remote-Steuer-Seite (2026-07-11, siehe
Basisinfos/Regelwerksmanual.md Kap. 12/13). Reine Datenbeschaffung, KEINE
Flask-Abhaengigkeit - eigenstaendig testbar, gleiches Trennungsprinzip wie
staleness.py (Domaenenlogik) vs. ui/formatting.py (Anzeige)."""
from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import config as config_module
import database.db as db
import scheduler.background as background
from staleness import is_price_stale

logger = logging.getLogger(__name__)

_TREFFER_EINSTUFUNGEN = {"kaufkandidat", "watchlist_wuerdig"}


# Entfernte LLM-Provider (2026-08-05, Nutzer-Vorgabe "alle groq und cerebras
# infos ausblenden bzw entfernen"). Beide sind laengst aus dem Betrieb
# genommen - Cerebras vollstaendig, Groq ebenso -, ihre historischen Zeilen
# stehen aber weiterhin in provider_performance, veto_schatten_performance,
# gesamt_signalqualitaet, provider_sendezaehler, llm_calls_heute und
# api_health. Auf einer Statusseite gelesen wirkt das wie ein aktiver
# Provider, der nichts liefert.
#
# NUR DIE ANZEIGE wird gefiltert. Die Daten bleiben in Datenbank und Export
# vollstaendig - dort gehoeren sie hin, weil alte Auswertungen sonst ihre
# Vergleichsgrundlage verlieren.
_ENTFERNTE_PROVIDER = ("groq", "cerebras")


def _ohne_entfernte_provider(daten):
    """Entfernt Eintraege entfernter Provider aus einer beliebig verschachtelten
    Status-Struktur.

    Rekursiv statt je Karte einzeln: die sechs betroffenen Bloecke haben
    unterschiedliche Formen ({tier: {provider: ...}}, {provider: zahl},
    Listen von Dicts). Eine gemeinsame Funktion kann nicht an einer Stelle
    vergessen werden, wenn eine siebte Karte dazukommt.

    Vergleich auf dem Praefix vor dem Doppelpunkt UND auf dem ganzen
    Schluessel: die Werte treten als "groq" ebenso auf wie als
    "groq:llama-3.3-70b-versatile"."""
    if isinstance(daten, dict):
        raus = {}
        for k, v in daten.items():
            name = str(k).split(":")[0].strip().lower()
            if name in _ENTFERNTE_PROVIDER:
                continue
            raus[k] = _ohne_entfernte_provider(v)
        return raus
    if isinstance(daten, list):
        return [_ohne_entfernte_provider(x) for x in daten]
    return daten


def _safe(fn, *args, **kwargs):
    """Fehlerisolierung je Karte (2026-07-31, Bug-Runde-Fund): build_status()
    reihte bisher alle _get_*()-Aufrufe direkt als Konstruktor-Argumente von
    RemoteStatus(...) auf - EIN Fehler in irgendeiner der ueber 15 Karten (z.B.
    der original_action-Rename-Vorfall vom selben Tag) riss die KOMPLETTE
    /api/status-Antwort mit, genau in dem Moment nach einem Deploy, in dem die
    Remote-Seite am dringendsten gebraucht wird (264 Fehlschlaege in ~9 Minuten
    im Log beobachtet, weil die Seite alle paar Sekunden pollt). Ab jetzt
    bleibt ein Fehler auf die eine betroffene Karte begrenzt (None statt
    Daten), der Rest der Seite funktioniert weiter."""
    try:
        return fn(*args, **kwargs)
    except Exception:
        logger.exception("Remote-Status-Karte '%s' fehlgeschlagen - Rest der Seite bleibt unbeeinflusst", fn.__name__)
        return None


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
    offene_signale: dict | None = None
    konfidenz_kalibrierung: dict | None = None
    api_health: dict | None = None
    regime_status: dict | None = None
    # Z-3 und die Gegenprobe der Bewertung (2026-08-06) - siehe
    # _get_z3_und_bewertung() fuer den Anlass.
    z3_und_bewertung: dict | None = None
    # Hedge-Wirksamkeit (2026-08-07, W1) - das zustaendige Erfolgsmass
    # fuer Absicherungen, siehe compute_hedge_wirksamkeit().
    hedge_wirksamkeit: dict | None = None
    parameter_overview: list[dict] | None = None
    richtungstreffer_quote: dict | None = None
    zai_richtung_performance: dict | None = None
    # Veto-Schatten-Tracking (2026-07-28, siehe agent/krypto/backward_tracking.py::
    # check_signal_veto_shadow_outcome()-Docstring) - 3-Gruppen-Anzeige-Redesign
    # (Nutzer-Wunsch: "sauber in eigene Bereiche aufteilen mit einem bestimmten
    # Zweck"). provider_sendezaehler ist bewusst UNABHAENGIG von der Veto-Schatten-
    # Frage (behebt einen separaten, aelteren Fund: ein selten eingesetzter
    # Provider wie Gemini kann in provider_performance komplett unsichtbar
    # bleiben, solange kein Signal von ihm aufgeloest ist).
    veto_schatten_performance: dict | None = None
    zai_richtung_performance_schatten: dict | None = None
    gesamt_signalqualitaet: dict | None = None
    provider_sendezaehler: dict | None = None
    # R-5.10-Konfidenzschwellen-Nachtrag (2026-07-30, siehe Memory
    # project_llm_optimierung_abdeckung_pruefung) - wie veto_schatten_
    # performance, aber nach (tier, veto_grund) statt (tier, provider)
    # gruppiert, damit kuenftige Schwellen-Entscheidungen ohne Ad-hoc-
    # Analyse moeglich sind.
    veto_schatten_performance_nach_grund: dict | None = None
    richtungsverteilung: dict | None = None
    # Selbst-gewaehltes-HALTEN-Schatten-Tracking (2026-07-31, siehe agent/
    # krypto/backward_tracking.py::compute_selbst_halten_performance()-
    # Docstring) - Gegenfall zum Veto-Schatten oben: kein Gate/Veto, das LLM
    # hat sich selbst gegen einen Trade entschieden, aber trotzdem eine
    # hypothetische Zone angegeben.
    systemguete: dict | None = None
    # Trailing-Stop-Empfehlungen fuer offene Signale (2026-08-04,
    # Punkt 3.2). Advisory-only: rechnet und meldet, greift nicht ein.
    ausstiegs_empfehlungen: dict | None = None
    selbst_gewaehltes_halten_performance: dict | None = None
    selbst_gewaehltes_halten_performance_nach_grund: dict | None = None
    # Marktscan-Erfolgsmessung (2026-07-30, siehe agent/krypto/
    # marktscan_backward_tracking.py::compute_marktscan_erfolgsquote()).
    marktscan_erfolgsquote: dict | None = None
    # CoinGecko-Monats-Kontingent (2026-07-31, echte 80%-Warnmail ausgeloest,
    # siehe scheduler/background.py::coingecko_quota_check_job()).
    coingecko_quota: dict | None = None
    # Wartende Themen-Vorschlaege (2026-08-07, S-3). Die Statusverteilung
    # "14 beobachtung" sagt nichts ueber den Vorlauf - diese Karte sagt, WANN
    # etwas reif wird und wie viele am selben Tag.
    wartende_themen: dict | None = None

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
            "offene_signale": self.offene_signale,
            "konfidenz_kalibrierung": self.konfidenz_kalibrierung,
            "api_health": self.api_health,
            "regime_status": self.regime_status,
            "z3_und_bewertung": self.z3_und_bewertung,
            "hedge_wirksamkeit": self.hedge_wirksamkeit,
            "parameter_overview": self.parameter_overview,
            "richtungstreffer_quote": self.richtungstreffer_quote,
            "zai_richtung_performance": self.zai_richtung_performance,
            "veto_schatten_performance": self.veto_schatten_performance,
            "zai_richtung_performance_schatten": self.zai_richtung_performance_schatten,
            "gesamt_signalqualitaet": self.gesamt_signalqualitaet,
            "provider_sendezaehler": self.provider_sendezaehler,
            "veto_schatten_performance_nach_grund": self.veto_schatten_performance_nach_grund,
            "richtungsverteilung": self.richtungsverteilung,
            "systemguete": self.systemguete,
            "ausstiegs_empfehlungen": self.ausstiegs_empfehlungen,
            "selbst_gewaehltes_halten_performance": self.selbst_gewaehltes_halten_performance,
            "selbst_gewaehltes_halten_performance_nach_grund": self.selbst_gewaehltes_halten_performance_nach_grund,
            "marktscan_erfolgsquote": self.marktscan_erfolgsquote,
            "coingecko_quota": self.coingecko_quota,
            "wartende_themen": self.wartende_themen,
        }


def build_status(conn: sqlite3.Connection, watchlist: list, log_path: Path, error_tail_lines: int = 5) -> RemoteStatus:
    latest_prices = db.get_latest_prices(conn)
    # Klassifikations-Redesign (2026-07-16): "gehalten" live aus den echten
    # Bestaenden (Spot) UND offenen Hebel-Positionen abgeleitet statt eines
    # gespeicherten Status-Felds - kann dadurch nie veralten (siehe config.py::
    # WatchlistAsset-Docstring).
    gehaltene_symbole = {
        h.symbol for h in db.get_all_holdings(conn)
        if (h.quantity or 0.0) + (h.staked_quantity or 0.0) > 0.0
    }
    offene_hebel_symbole = {p.symbol for p in db.get_open_hebel_positions(conn)}
    active_symbols = {
        a.symbol for a in watchlist
        if a.symbol in gehaltene_symbole or a.symbol in offene_hebel_symbole
    }

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
        marktscan_last=_safe(_get_marktscan_last, conn),
        recent_errors=_tail_log_errors(log_path, error_tail_lines),
        jobs_running=jobs_running,
        jobs_running_seit_minuten=jobs_running_seit_minuten,
        budget_heute=_safe(_get_budget_heute, conn),
        provider_performance=_safe(_get_provider_performance, conn, watchlist),
        offene_signale=_safe(_get_offene_signale_uebersicht, conn, watchlist),
        konfidenz_kalibrierung=_safe(_get_konfidenz_kalibrierung, conn, watchlist),
        api_health=_safe(_get_api_health, conn),
        regime_status=_safe(_get_regime_status, conn),
        z3_und_bewertung=_safe(_get_z3_und_bewertung, conn, portfolio_value_eur),
        hedge_wirksamkeit=_safe(_get_hedge_wirksamkeit, conn, watchlist),
        parameter_overview=_safe(_get_parameter_overview),
        richtungstreffer_quote=_safe(_get_richtungstreffer_quote, conn, watchlist),
        zai_richtung_performance=_safe(_get_zai_richtung_performance, conn, watchlist),
        veto_schatten_performance=_safe(_get_veto_schatten_performance, conn, watchlist),
        zai_richtung_performance_schatten=_safe(_get_zai_richtung_performance_schatten, conn, watchlist),
        gesamt_signalqualitaet=_safe(_get_gesamt_signalqualitaet, conn, watchlist),
        provider_sendezaehler=_safe(_get_provider_sendezaehler, conn, watchlist),
        veto_schatten_performance_nach_grund=_safe(_get_veto_schatten_performance_nach_grund, conn, watchlist),
        richtungsverteilung=_safe(_get_richtungsverteilung, conn, watchlist),
        systemguete=_safe(_get_systemguete, conn, watchlist),
        ausstiegs_empfehlungen=_safe(_get_ausstiegs_empfehlungen, conn, watchlist),
        selbst_gewaehltes_halten_performance=_safe(_get_selbst_gewaehltes_halten_performance, conn, watchlist),
        selbst_gewaehltes_halten_performance_nach_grund=_safe(
            _get_selbst_gewaehltes_halten_performance_nach_grund, conn, watchlist,
        ),
        marktscan_erfolgsquote=_safe(_get_marktscan_erfolgsquote, conn),
        coingecko_quota=_safe(_get_coingecko_quota, conn),
        wartende_themen=_safe(_get_wartende_themen, conn),
    )


def _get_api_health(conn: sqlite3.Connection) -> dict:
    """Sichtbarkeit fuer das passive API-Gesundheits-Tracking (2026-07-15, siehe
    database/api_health.py::track_api_health()) - reiner Lesezugriff, keine neue
    Logik.

    Auch hier der Filter fuer entfernte Provider (2026-08-05): das
    Gesundheits-Tracking ist passiv und schreibt fort, was einmal aufgerufen
    wurde - Groq und Cerebras stehen dort mit ihrem letzten Stand von vor der
    Entfernung und erschienen auf der Seite sonst als dauerhaft stille
    Quellen."""
    return _ohne_entfernte_provider(db.get_api_health_status(conn))


def _get_coingecko_quota(conn: sqlite3.Connection) -> dict | None:
    """CoinGecko-Monats-Kontingent-Sichtbarkeit (2026-07-31, echte 80%-
    Warnmail von CoinGecko ausgeloest, siehe scheduler/background.py::
    coingecko_quota_check_job()) - reiner Lesezugriff auf den Zaehler, keine
    neue Logik. None, wenn coingecko_quota.monatslimit in config.yaml (noch)
    nicht gesetzt ist."""
    config_dict = config_module.load_config()
    limit = config_dict.get("coingecko_quota", {}).get("monatslimit")
    if not limit:
        return None
    monat = db.aktueller_monat_utc()
    anzahl = db.get_api_call_counter(conn, "coingecko", monat)
    return {
        "monat": monat,
        "anzahl": anzahl,
        "limit": limit,
        "prozent": round((anzahl / limit) * 100, 1),
        # Tages-Granularitaet (2026-08-01, Nutzer-Nachfrage nach ungewoehnlich
        # hohem Verbrauch) - macht kuenftig sichtbar, an welchem Tag der
        # Verbrauch tatsaechlich anstieg, statt es im Nachhinein schaetzen zu
        # muessen.
        "anzahl_heute": db.get_api_call_counter_taeglich(conn, "coingecko"),
    }


def _get_provider_performance(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Sichtbarkeit fuer die Backward-Tracking-Provider-Performance (2026-07-15,
    siehe agent/krypto/backward_tracking.py::compute_provider_performance()) -
    reiner Lesezugriff, keine neue Logik.

    `watchlist` seit 2026-07-20 durchgereicht, damit die Spot-Seite nach
    Assetklasse (krypto/aktien/rohstoffe/etf) statt einem einzigen "spot"-Topf
    aufgeschluesselt wird - siehe compute_provider_performance()-Docstring."""
    from agent.krypto.backward_tracking import compute_provider_performance

    return _ohne_entfernte_provider(compute_provider_performance(conn, watchlist))


def _get_offene_signale_uebersicht(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Ergaenzt _get_provider_performance() um Sichtbarkeit fuer noch nicht
    aufgeloeste, aber bereits trackbare Signale (2026-07-24, Nutzer-Fund: die
    reine "0 abgeschlossen"-Anzeige zeigte keinen Fortschritt an) - reiner
    Lesezugriff, siehe agent/krypto/backward_tracking.py::
    compute_offene_signale_uebersicht()."""
    from agent.krypto.backward_tracking import compute_offene_signale_uebersicht

    return compute_offene_signale_uebersicht(conn, watchlist)


def _get_konfidenz_kalibrierung(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Konfidenz-Kalibrierungskurve (2026-07-26, Punkt 3 des Regime-Persistenz-
    Folge-Vorschlags) - reiner Lesezugriff, siehe agent/krypto/
    backward_tracking.py::compute_konfidenz_kalibrierung() fuer die Frage,
    die diese Karte beantwortet (haelt confidence_pct, was es verspricht?)."""
    from agent.krypto.backward_tracking import compute_konfidenz_kalibrierung

    return compute_konfidenz_kalibrierung(conn, watchlist)


def _get_richtungstreffer_quote(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Richtungstreffer-Quote-Karte (2026-07-27, Performance-Messung-
    Expertenanalyse, Nutzer-Wunsch "bitte nicht auf der Remoteseite vergessen")
    - reiner Lesezugriff auf agent/krypto/backward_tracking.py::
    compute_richtungstreffer_quote(). Anders als provider_performance/
    konfidenz_kalibrierung (die watchlist-basiert nach Assetklasse
    aufschluesseln) liefert compute_richtungstreffer_quote() nur EINEN Tier
    pro Aufruf - hier bewusst nur grob nach spot/hebel getrennt (wie
    compute_win_rate_fact()), keine feinere Assetklassen-Aufschluesselung noetig
    fuer diese Uebersichtskarte."""
    from agent.krypto.backward_tracking import DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV, compute_richtungstreffer_quote

    schwelle = config_module.load_config().get("backward_tracking", {}).get(
        "richtungstreffer_mindest_crv", DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    )
    return {
        "mindest_crv": schwelle,
        "spot": compute_richtungstreffer_quote(conn, "spot", schwelle),
        "hebel": compute_richtungstreffer_quote(conn, "hebel", schwelle),
    }


def _get_marktscan_erfolgsquote(conn: sqlite3.Connection) -> dict | None:
    """Marktscan-Erfolgsquote-Karte (2026-07-30, Erfolgsmessung Teil 2) - reiner
    Lesezugriff auf agent/krypto/marktscan_backward_tracking.py::
    compute_marktscan_erfolgsquote(). Anders als richtungstreffer_quote braucht
    diese Karte KEINE Watchlist (die Aggregation liest direkt aus
    marktscan_candidates, nicht ueber Assetklassen der Watchlist)."""
    from agent.krypto.marktscan_backward_tracking import compute_marktscan_erfolgsquote

    return compute_marktscan_erfolgsquote(conn)


def _get_zai_richtung_performance(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Z.ais UNABHAENGIGE Richtungs-Erfolgsquote (2026-07-27, Nutzer-Wunsch:
    "ZAI unabhaengig mit seinen unterschiedlichen Entscheidungen und deren
    Erfolgsquote messen"). Die urspruengliche Begruendung stuetzte sich auf den
    Nur-Long-Kandidatenfilter - der ist seit dem 05.08. entfernt, siehe
    compute_zai_richtung_performance()-Docstring, Abschnitt "URSPRUENGLICHE
    BEGRUENDUNG UEBERHOLT".
    - reiner Lesezugriff auf agent/krypto/backward_tracking.py::
    compute_zai_richtung_performance(). Anders als provider_performance
    (das Mistrals EIGENE Empfehlung bewertet) misst diese Karte, ob Z.ais
    Call-2-Richtungsableitung (`zai_eigene_richtung`) unabhaengig von Mistrals
    Bias mit der tatsaechlichen Marktrichtung uebereinstimmte.

    Seit Punkt 3 der Performance-Messung-Nachfrage (2026-07-27) auf derselben
    Basis wie richtungstreffer_quote (Maximum Favorable Excursion, nicht der
    binaere TP/SL-outcome_status) - dieselbe config-Schwelle wie dort
    verwenden, damit beide Karten konsistent dieselbe CRV-Schwelle nutzen."""
    from agent.krypto.backward_tracking import DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV, compute_zai_richtung_performance

    schwelle = config_module.load_config().get("backward_tracking", {}).get(
        "richtungstreffer_mindest_crv", DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    )
    return compute_zai_richtung_performance(conn, watchlist, schwelle)


def _get_veto_schatten_performance(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Gruppe C ("Veto-Schatten", 2026-07-28) - reiner Lesezugriff auf
    agent/krypto/backward_tracking.py::compute_veto_shadow_performance(). Wie
    _get_provider_performance(), aber fuer die hypothetischen, nie
    ausgefuehrten Trade-Vorschlaege, deren Action durch einen Risk-Gate-Veto
    auf HALTEN zurueckgestuft wurde - siehe check_signal_veto_shadow_outcome()-
    Docstring fuer die volle Herleitung dieses Features."""
    from agent.krypto.backward_tracking import compute_veto_shadow_performance

    return _ohne_entfernte_provider(compute_veto_shadow_performance(conn, watchlist))


def _get_richtungsverteilung(conn: sqlite3.Connection, watchlist: list) -> dict:
    """LONG gegen SHORT seit dem Nur-Long-Umbau (2026-08-05) - NEUE Karte.

    Bis zum Umbau war diese Frage nicht stellbar: SHORT-Kandidaten wurden vor
    dem LLM-Aufruf gefiltert, und was das Modell trotzdem als SHORT empfahl,
    drehte das Risk-Gate auf HALTEN. Seither laufen beide Richtungen normal
    durch - und werden gemessen, auch wenn SHORT weder gemailt noch im
    Hebel-Tab standardmaessig angezeigt wird.

    Reiner Lesezugriff auf backward_tracking.py::compute_richtungsverteilung()."""
    from agent.krypto.backward_tracking import compute_richtungsverteilung

    return compute_richtungsverteilung(conn, watchlist)


def _get_veto_schatten_performance_nach_grund(conn: sqlite3.Connection, watchlist: list) -> dict:
    """R-5.10-Konfidenzschwellen-Nachtrag (2026-07-30) - reiner Lesezugriff auf
    agent/krypto/backward_tracking.py::compute_veto_shadow_performance_nach_grund().
    Wie _get_veto_schatten_performance(), aber nach (tier, veto_grund) statt
    (tier, provider) aufgeschluesselt - beantwortet die fuer eine Schwellen-
    Entscheidung eigentliche Frage: schlagen sich Konfidenzschwellen-Vetos
    (R-5.10) anders als CRV<2.0-Vetos, je Assetklasse?"""
    from agent.krypto.backward_tracking import (
        VETO_GRUND_NUR_LONG, compute_veto_shadow_performance_nach_grund,
    )

    roh = compute_veto_shadow_performance_nach_grund(conn, watchlist)
    # HISTORISCHEN BESTAND AUSBLENDEN (2026-08-05, Nutzer-Vorgabe "Informationen
    # welche wir nicht mehr messen ... nicht mehr anzeigen"): der Nur-Long-Veto
    # ist entfernt, seine 313 Altfaelle wachsen nicht mehr. Als laufende
    # Kennzahl dargestellt liest man einen eingefrorenen Bestand als aktuelles
    # Systemverhalten - genau die Verwechslung, die beim 31.07.-Bruch Zeit
    # gekostet hat.
    #
    # Nur die ANZEIGE wird gefiltert. Die Daten bleiben in der Datenbank und im
    # Export vollstaendig erhalten; die neue Kategorie VETO_GRUND_NUR_LONG
    # macht sie dort gezielt auswertbar, statt sie wie bisher im Sammeltopf
    # "sonstige" zu verstecken.
    if not isinstance(roh, dict):
        return roh
    gefiltert = {}
    for tier, gruende in roh.items():
        if isinstance(gruende, dict):
            gefiltert[tier] = {g: v for g, v in gruende.items()
                               if g != VETO_GRUND_NUR_LONG}
        else:
            gefiltert[tier] = gruende
    return gefiltert


# Zwischenspeicher fuer die Systemguete (2026-08-03, HOTFIX).
# HINTERGRUND: die Remote-Seite ruft /api/status alle 2 Sekunden ab
# (setInterval(refreshStatus, 2000) in remote/server.py). Am 03.08. kamen
# Basislinien-Simulation und Bootstrap dazu, zusammen rund 1-1,5 s je Aufruf -
# damit ueberlappten sich die Anfragen, der Server kam nicht mehr hinterher und
# die Seite zeigte nur noch kurz Werte, bevor sie leer blieb (Nutzer-Fund).
# Die Zahlen aendern sich ohnehin nur beim taeglichen Backward-Tracking-Lauf,
# ein Zwischenspeicher kostet also keine Aktualitaet.
#
# NACHTRAG 03.08.: 300 Sekunden waren immer noch 60x haeufiger als noetig. Die
# Zahlen speisen sich ausschliesslich aus den outcome_*-Spalten, und die werden
# nur vom taeglichen 06:00-Backward-Tracking geschrieben - zwischen zwei Laeufen
# kann sich das Ergebnis gar nicht aendern. Auf dem Notebook (i5-4300U, zwei
# Kerne von 2013) kostet ein Durchlauf ein Vielfaches der 1,8 s vom Desktop,
# und die reine Python-Schleife des Bootstraps belegt dabei einen der beiden
# Kerne - der Nutzer sah nach einem Browser-Refresh 15-20 s lang keine
# aktualisierten Werte. Ein Stundentakt loest das an der Wurzel: der Wert ist
# hoechstens eine Stunde alt, die Berechnung laeuft statt 288x nur noch 24x
# am Tag.
_SYSTEMGUETE_CACHE: dict = {"stand": 0.0, "wert": None, "laeuft": False}
_SYSTEMGUETE_CACHE_SEKUNDEN = 3600


def _get_ausstiegs_empfehlungen(conn, watchlist: list) -> dict:
    """Offene Signale, deren Stop nachgezogen gehoert (2026-08-04).

    Reiner Lesezugriff auf backward_tracking.py::
    compute_ausstiegs_empfehlungen(). Advisory-only (P-7) - die
    Empfehlung wird angezeigt, nicht ausgefuehrt."""
    from agent.krypto.backward_tracking import compute_ausstiegs_empfehlungen
    import config as _config
    return compute_ausstiegs_empfehlungen(conn, watchlist, _config.load_config())


def _get_systemguete(conn: sqlite3.Connection, watchlist: list) -> dict:
    """SQN/Expectancy/Profit Factor je tier (2026-08-02) - reiner Lesezugriff
    auf agent/krypto/backward_tracking.py::compute_systemguete(). Zielwerte und
    Herleitung in Basisinfos/Zielgroessen_und_Erfolgsmasse.md; getrennt nach
    real ausgefuehrt und Veto-Schatten, weil beide verschiedene Fragen
    beantworten.

    Ergebnis wird zwischengespeichert und im HINTERGRUND erneuert - der
    Statusabruf wartet nie auf die Berechnung. Begruendung bei
    _SYSTEMGUETE_CACHE."""
    import threading
    import time

    jetzt = time.monotonic()
    frisch = (_SYSTEMGUETE_CACHE["wert"] is not None
              and jetzt - _SYSTEMGUETE_CACHE["stand"] < _SYSTEMGUETE_CACHE_SEKUNDEN)
    if not frisch and not _SYSTEMGUETE_CACHE["laeuft"]:
        _SYSTEMGUETE_CACHE["laeuft"] = True
        threading.Thread(target=_systemguete_neu_berechnen, args=(watchlist,),
                         daemon=True).start()
    # Bis die Berechnung fertig ist, kommt der vorige Wert zurueck (beim
    # allerersten Aufruf None - die Karte bleibt dann eine Runde leer und
    # fuellt sich beim naechsten Refresh zwei Sekunden spaeter).
    return _SYSTEMGUETE_CACHE["wert"]


def _systemguete_neu_berechnen(watchlist: list) -> None:
    """Laeuft in einem Hintergrund-Thread und OEFFNET EINE EIGENE
    DB-Verbindung - sqlite3-Verbindungen duerfen nicht ueber Threads hinweg
    benutzt werden, die Verbindung des Aufrufers ist hier also tabu."""
    import time

    import database.db as db
    from agent.krypto.backward_tracking import compute_systemguete

    try:
        eigene = db.get_connection()
        try:
            wert = compute_systemguete(eigene, watchlist)
        finally:
            eigene.close()
        _SYSTEMGUETE_CACHE["wert"] = wert
        _SYSTEMGUETE_CACHE["stand"] = time.monotonic()
    except Exception:
        # Nicht durchreichen: ein Fehler hier darf den Statusabruf nicht
        # beeinflussen. Beim naechsten Abruf wird es erneut versucht.
        logger.exception("Systemguete-Neuberechnung im Hintergrund fehlgeschlagen")
    finally:
        _SYSTEMGUETE_CACHE["laeuft"] = False


def _get_selbst_gewaehltes_halten_performance(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Gruppe C, Gegenfall zum Veto-Schatten (2026-07-31) - reiner Lesezugriff
    auf agent/krypto/backward_tracking.py::compute_selbst_halten_performance().
    Kein Gate/Veto, das LLM hat sich selbst gegen einen Trade entschieden,
    aber trotzdem eine hypothetische Zone angegeben - siehe check_signal_
    selbst_halten_outcome()-Docstring fuer die volle Herleitung."""
    from agent.krypto.backward_tracking import compute_selbst_halten_performance

    return compute_selbst_halten_performance(conn, watchlist)


def _get_selbst_gewaehltes_halten_performance_nach_grund(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Wie _get_selbst_gewaehltes_halten_performance(), aber nach (tier,
    top_grund_1_kategorie) statt (tier, provider) aufgeschluesselt (2026-07-31,
    mirror _get_veto_schatten_performance_nach_grund())."""
    from agent.krypto.backward_tracking import compute_selbst_halten_performance_nach_grund

    return compute_selbst_halten_performance_nach_grund(conn, watchlist)


def _get_zai_richtung_performance_schatten(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Gruppe C, Z.ai-Anteil (2026-07-28) - reiner Lesezugriff auf
    compute_zai_richtung_performance_schatten(). Misst Z.ais unabhaengiges
    Richtungsurteil gerade fuer die vetoten Signale - siehe dortiger
    Docstring."""
    from agent.krypto.backward_tracking import (
        DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
        compute_zai_richtung_performance_schatten,
    )

    schwelle = config_module.load_config().get("backward_tracking", {}).get(
        "richtungstreffer_mindest_crv", DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    )
    return compute_zai_richtung_performance_schatten(conn, watchlist, schwelle)


def _get_gesamt_signalqualitaet(conn: sqlite3.Connection, watchlist: list) -> dict:
    """"Gesamt-Signalqualitaet, unabhaengig vom Risk-Gate" (2026-07-28, Nutzer-
    Einsicht: Gruppe C ist eigentlich Real+Schatten zusammen) - reiner
    Lesezugriff auf compute_gesamt_signalqualitaet(), siehe dortiger Docstring
    fuer die additive Zusammenfuehrung."""
    from agent.krypto.backward_tracking import compute_gesamt_signalqualitaet

    return _ohne_entfernte_provider(compute_gesamt_signalqualitaet(conn, watchlist))


def _get_provider_sendezaehler(conn: sqlite3.Connection, watchlist: list) -> dict:
    """Rohe Sendeanzahl je Provider (2026-07-28, Nutzer-Frage "wie oft hat
    Gemini ueberhaupt welche Signale gesendet?") - reiner Lesezugriff auf
    compute_provider_sendezaehler(), macht selten eingesetzte Provider auch
    OHNE aufgeloestes Signal sichtbar (siehe dortiger Docstring)."""
    from agent.krypto.backward_tracking import compute_provider_sendezaehler

    return _ohne_entfernte_provider(compute_provider_sendezaehler(conn, watchlist))


def _get_regime_status(conn: sqlite3.Connection) -> dict | None:
    """Regime-Status-Karte (2026-07-17) - reiner Lesezugriff auf den zuletzt
    PERSISTIERTEN Regime-Stand, kein neuer Live-Recompute (siehe
    agent/krypto/regime.py::get_last_known_regime_status())."""
    from agent.krypto.regime import get_last_known_regime_status

    return get_last_known_regime_status(conn)


def _get_z3_und_bewertung(conn: sqlite3.Connection, portfolio_value_eur: float | None) -> dict | None:
    """Drawdown-Notbremse Z-3 - und die Gegenprobe, ob ihre Datenbasis stimmt.

    ZWEI LUECKEN, die dieser Block schliesst (2026-08-06):

    1. Z-3 stand ueberhaupt nicht auf der Uebersichtsseite. Die Notbremse loeste
       am 05. und 06.08. aus, sichtbar war das nur per E-Mail und im Log.

    2. WICHTIGER: die Seite rechnet den Portfoliowert aus den SNAPSHOT-Preisen
       (`price_cache`), Z-3 aus der KURSREIHE (`price_history_ohlc`). Beide
       beschreiben dasselbe Portfolio. Weichen sie voneinander ab, stimmt eine
       der beiden Datenquellen nicht - und man sieht es sofort, statt es zu
       suchen.

    Genau diese Abweichung lag am 06.08. bei ueber 100 Prozent, ohne dass es
    irgendwo auffiel: die Kursreihe fuehrte 19 gehaltene Symbole gar nicht (die
    FX-Ableitung wurde an 87 von 91 Tagen verworfen), und unter denen lag ein
    Symbol mit dem Kurs eines voellig anderen Instruments. Eine der beiden
    Zahlen war immer falsch - nur nebeneinander gestellt wurden sie nie.
    """
    try:
        from agent.portfolio_historie import pruefe_z3
        import config as config_module
        z3 = pruefe_z3(
            conn, schwelle_prozent=config_module.load_config()["ziele"]["max_drawdown_prozent"]
        )
    except Exception as exc:            # Nebenblock darf die Seite nie toeten
        logger.info("Z-3-Status fuer die Remote-Seite nicht ermittelbar: %s", exc)
        return None

    reihe = db.get_portfolio_wert_historie(conn)
    letzter = reihe[-1] if reihe else None
    reihen_wert = letzter["wert_eur"] if letzter and "wert_eur" in letzter.keys() else None
    abweichung = None
    if reihen_wert and portfolio_value_eur:
        abweichung = abs(reihen_wert - portfolio_value_eur) / portfolio_value_eur * 100.0
    return {
        **z3,
        "reihen_wert_eur": reihen_wert,
        "reihen_tag": letzter["datum"] if letzter and "datum" in letzter.keys() else None,
        "snapshot_wert_eur": portfolio_value_eur,
        "abweichung_prozent": abweichung,
        "symbole_ohne_kurs": (letzter["symbole_ohne_kurs"]
                              if letzter and "symbole_ohne_kurs" in letzter.keys() else None),
    }


def _get_hedge_wirksamkeit(conn: sqlite3.Connection, watchlist: list) -> dict | None:
    """Hat die Absicherung gewirkt? Siehe agent/portfolio_historie.py::
    compute_hedge_wirksamkeit() - SQN/Expectancy sind fuer diese Klasse die
    falsche Frage, deshalb eine eigene Karte statt einer Zeile in der
    Systemguete."""
    from datetime import date, timedelta

    from agent.portfolio_historie import compute_hedge_wirksamkeit

    ab = (date.today() - timedelta(days=90)).isoformat()
    return compute_hedge_wirksamkeit(conn, ab_datum=ab, watchlist=watchlist)


def _get_wartende_themen(conn: sqlite3.Connection) -> dict | None:
    """Welche Themen-Vorschlaege warten, und wann werden sie reif? (2026-08-07)

    Siehe agent/kategorie_vorschlaege.py::wartende_vorschlaege(). Auf die
    Uebersichtsseite gehoert davon vor allem EINE Zahl: wie viele Kandidaten am
    SELBEN Tag reif werden. Uebersteigt sie das freie Budget, entscheidet die
    Gleichzeitigkeits-Moderation - und das gehoert mit Wochen Vorlauf gesehen,
    nicht am Tag selbst."""
    from agent.kategorie_vorschlaege import wartende_vorschlaege

    return wartende_vorschlaege(conn)


def _get_parameter_overview() -> list[dict]:
    """Parameter-Übersicht-Karte (2026-07-17) - reiner Lesezugriff auf die
    Kap.-15-Kalibrierungsparameter aus config.yaml (siehe
    agent/krypto/regelwerk_parameter.py::build_parameter_overview())."""
    from agent.krypto.regelwerk_parameter import build_parameter_overview

    return build_parameter_overview(config_module.load_config())


def _get_budget_heute(conn: sqlite3.Connection) -> dict:
    """Budget-Sichtbarkeit fuer alle 3 Tiers des gemeinsamen Tagesbudgets
    (docs/budget_queue_design.md) - reiner Lesezugriff auf bereits vorhandene
    Zaehlfunktionen, keine neue Logik. taegliches_budget_gesamt ist EIN
    gemeinsamer Deckel ueber Hebel+Marktscan+Spot (kein Budget pro Tier) -
    war und ist Krypto-spezifisch kalibriert (Hebel/Marktscan haben ohnehin
    kein Nicht-Krypto-Aequivalent).

    LLM-Budget-Konsistenzpruefung (2026-07-18): `spot` zaehlte bisher
    STILLSCHWEIGEND auch die automatischen Multi-Asset-Batch-Signale
    (Aktien/Rohstoffe/Hedge/Themen-ETF) mit, da beide in dieselbe
    signals-Tabelle schreiben - verzerrte das angezeigte X/taegliches_budget_
    gesamt-Verhaeltnis nach oben, sobald der 12h-Multi-Asset-Batch lief.
    `spot` ist jetzt Krypto-only gefiltert, Multi-Asset-Verbrauch wird
    separat als `multi_asset_heute` ausgewiesen statt unsichtbar
    eingerechnet.

    `zai_gegenpruefung_heute` (2026-07-27, Nutzer-Fund): Z.ai ist seit dem
    Gegenpruefungs-Umbau (26.07.) NICHT mehr Teil von `verbraucht_gesamt`/
    `gesamt` (kein primaerer Analyst mehr, keine Ressourcen-Konkurrenz zum
    B-Tagesbudget) - laeuft aber weiterhin real im Hintergrund. Separat
    ausgewiesen statt in die Hauptzahl gemischt, aus demselben Grund wie
    `multi_asset_heute`."""
    config_dict = config_module.load_config()
    gesamt = config_dict.get("budget_allocator", {}).get("taegliches_budget_gesamt", 15)
    krypto_symbole = {a.symbol for a in config_module.get_watchlist() if a.assetklasse == "krypto"}
    hebel = db.count_real_hebel_signals_today(conn)
    marktscan = db.count_real_marktscan_writeups_today(conn)
    spot_gesamt = db.count_real_signals_today(conn)
    spot = db.count_real_signals_today(conn, erlaubte_symbole=krypto_symbole)
    return {
        "hebel": hebel,
        "marktscan": marktscan,
        "spot": spot,
        "verbraucht_gesamt": hebel + marktscan + spot,
        "gesamt": gesamt,
        "multi_asset_heute": spot_gesamt - spot,
        # Rein informativ (2026-07-27), KEIN Tagesdeckel - siehe
        # count_zai_gegenpruefung_calls_today()-Docstring.
        "zai_gegenpruefung_heute": db.count_zai_gegenpruefung_calls_today(conn),
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
