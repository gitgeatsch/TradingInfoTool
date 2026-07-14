"""Budget-Allocator (2026-07-14, Phase 5, siehe docs/budget_queue_design.md) -
zentrale Tagesbudget-Verteilung ueber die drei KI-Verbraucher (Hebel-
Kandidaten, Marktscan-Kaufkandidaten, Spot-Rotation), huckepack auf dem
15-Min-Takt (scheduler/background.py::hebel_screening_job). Ersetzt den
automatischen Groq-Zweig in marktscan.py::run_scan() und den fixen
05:00-Uhr-signal_batch_job-Cron - beide liefen bisher unabhaengig voneinander
ohne gemeinsame Budget-Kenntnis.

Verteilungsformel (1:1 aus docs/budget_queue_design.md):
    verfuegbar_1_2 = B - F
    tier1_verbraucht = min(anzahl_hebel_kandidaten, verfuegbar_1_2)
    rest_fuer_2 = verfuegbar_1_2 - tier1_verbraucht
    tier2_verbraucht = min(anzahl_marktscan_kandidaten, rest_fuer_2)
    rest_fuer_3 = B - tier1_verbraucht - tier2_verbraucht
    tier3_verbraucht = min(anzahl_faelliger_spot_assets, rest_fuer_3)

Cerebras-Overflow (additiv zu B - siehe 2026-07-14-Fund: Cerebras' echtes
Tageslimit liegt bei ~166 Calls, ~10x Groqs reale ~15-18/Tag): fuer jeden
ausgewaehlten Kandidaten wird ZUERST Groq versucht; schlaegt der Call fehl
(jede Exception - Netzwerk, HTTP-Fehler, Rate-Limit), wird SOFORT mit
Cerebras retryed, solange dessen eigener Tages-Deckel (config
cerebras_taegliches_budget) noch nicht erschoepft ist. Kandidaten, die auch
daran scheitern, bleiben unverarbeitet - kein Datenverlust (P-10), der
naechste 15-Min-Lauf bewertet sie automatisch neu."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import database.db as db
from agent.krypto.hebel_pipeline import generate_hebel_signal
from agent.krypto.marktscan import generate_candidate_writeup
from agent.krypto.pipeline import compute_current_regime, generate_signal
from agent.krypto.signal_batch import select_assets_due_for_signal
from database.models import HebelTrigger, MarktscanCandidate

logger = logging.getLogger(__name__)


@dataclass
class AllocationResult:
    hebel_verarbeitet: list[str] = field(default_factory=list)
    marktscan_verarbeitet: list[str] = field(default_factory=list)
    spot_verarbeitet: list[str] = field(default_factory=list)
    provider_je_call: dict[str, str] = field(default_factory=dict)
    fehlgeschlagen: list[str] = field(default_factory=list)
    uebersprungen_cooldown_hebel: int = 0
    uebersprungen_cooldown_marktscan: int = 0
    cerebras_calls_verbraucht: int = 0
    cerebras_budget_erschoepft: bool = False
    # 2026-07-14 (Empfehlungs-E-Mails): die echten Signal-/HebelSignal-Objekte
    # zu jedem schluessel aus hebel_verarbeitet/spot_verarbeitet - nur befuellt,
    # wenn provider_je_call[schluessel] ebenfalls gesetzt wurde (also ein
    # ECHTER LLM-Call stattfand, kein Gate-Skip). scheduler/background.py::
    # hebel_screening_job() liest das aus, um E-Mails bei handlungsrelevanten
    # Empfehlungen auszuloesen - budget_allocator.py selbst bleibt frei von
    # E-Mail-Logik (gleiche Trennung wie bei marktscan.py/_notify_marktscan_
    # kaufkandidaten()).
    ergebnis_objekt: dict[str, object] = field(default_factory=dict)


def _cooldown_grenze(cooldown_stunden: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=cooldown_stunden)).isoformat()


def _filter_hebel_cooldown(
    conn, candidates: list[HebelTrigger], cooldown_stunden: float
) -> tuple[list[HebelTrigger], int]:
    """Symbol+Richtung mit einem hebel_signals-Eintrag NACH der Cooldown-Grenze
    (echte Analyse, groq_raw_response gesetzt) ausschliessen - verhindert, dass
    ein dauerhaft ausloesendes Symbol (z.B. anhaltend extreme Funding-Rate)
    jeden 15-Min-Zyklus erneut analysiert wird und damit das Budget allein
    aufbraucht."""
    grenze = _cooldown_grenze(cooldown_stunden)
    latest = db.get_latest_hebel_signal_per_symbol(conn)
    gefiltert, uebersprungen = [], 0
    for c in candidates:
        sig = latest.get(c.symbol)
        if sig is not None and sig.richtung == c.richtung and sig.created_at >= grenze:
            uebersprungen += 1
            continue
        gefiltert.append(c)
    return gefiltert, uebersprungen


def _filter_marktscan_cooldown(
    conn, candidates: list[MarktscanCandidate], cooldown_stunden: float
) -> tuple[list[MarktscanCandidate], int]:
    """Analog _filter_hebel_cooldown() - get_pending_marktscan_kaufkandidaten()
    filtert nur auf `groq_generiert_am IS NULL` DER NEUESTEN Zeile, ein neuer
    Scan-Lauf legt aber immer eine neue Zeile an (UNIQUE(coingecko_id,
    scan_run_id)) - ohne diesen Zusatz-Check wuerde ein Coin, der vor 20 Min
    bereits eine Begruendung bekam, beim naechsten Scan erneut als "pending"
    erscheinen."""
    grenze = _cooldown_grenze(cooldown_stunden)
    gefiltert, uebersprungen = [], 0
    for c in candidates:
        letzter = db.get_latest_marktscan_writeup_at(conn, c.coingecko_id)
        if letzter is not None and letzter >= grenze:
            uebersprungen += 1
            continue
        gefiltert.append(c)
    return gefiltert, uebersprungen


def _verteile_budget(
    anzahl_hebel: int, anzahl_marktscan: int, anzahl_spot: int, budget_gesamt: int, spot_reserve: int
) -> tuple[int, int, int]:
    """Verteilungsformel 1:1 aus docs/budget_queue_design.md - reine Funktion,
    kein DB-/Netzwerk-Zugriff, damit sie isoliert gegen Grenzfaelle testbar
    ist (siehe Verifikation im Plan)."""
    verfuegbar_1_2 = budget_gesamt - spot_reserve
    tier1_verbraucht = min(anzahl_hebel, max(0, verfuegbar_1_2))
    rest_fuer_2 = verfuegbar_1_2 - tier1_verbraucht
    tier2_verbraucht = min(anzahl_marktscan, max(0, rest_fuer_2))
    rest_fuer_3 = budget_gesamt - tier1_verbraucht - tier2_verbraucht
    tier3_verbraucht = min(anzahl_spot, max(0, rest_fuer_3))
    return tier1_verbraucht, tier2_verbraucht, tier3_verbraucht


def run_budget_allocator(
    conn_factory,
    watchlist: list,
    groq_client,
    cerebras_client,
    coingecko_client,
    kraken_client,
    fred_api_key: str | None,
    config_dict: dict,
) -> AllocationResult:
    cfg = config_dict.get("budget_allocator", {})
    result = AllocationResult()
    if not cfg.get("aktiv", True):
        return result

    budget_gesamt = cfg.get("taegliches_budget_gesamt", 15)
    spot_reserve = cfg.get("spot_rotation_reserve", 5)
    cerebras_budget = cfg.get("cerebras_taegliches_budget", 60)
    cooldown_stunden = cfg.get("cooldown_stunden", 3.5)

    conn = conn_factory()
    try:
        hebel_kandidaten, result.uebersprungen_cooldown_hebel = _filter_hebel_cooldown(
            conn, db.get_pending_hebel_candidates(conn), cooldown_stunden,
        )
        marktscan_kandidaten, result.uebersprungen_cooldown_marktscan = _filter_marktscan_cooldown(
            conn, db.get_pending_marktscan_kaufkandidaten(conn), cooldown_stunden,
        )
        spot_kandidaten = select_assets_due_for_signal(conn, watchlist, max_count=budget_gesamt)
    finally:
        conn.close()

    tier1_n, tier2_n, tier3_n = _verteile_budget(
        len(hebel_kandidaten), len(marktscan_kandidaten), len(spot_kandidaten), budget_gesamt, spot_reserve,
    )
    logger.info(
        "Budget-Allocator: Hebel %d/%d, Marktscan %d/%d, Spot %d/%d ausgewaehlt (B=%d, F=%d), "
        "Cooldown uebersprungen: Hebel %d, Marktscan %d",
        tier1_n, len(hebel_kandidaten), tier2_n, len(marktscan_kandidaten), tier3_n, len(spot_kandidaten),
        budget_gesamt, spot_reserve, result.uebersprungen_cooldown_hebel, result.uebersprungen_cooldown_marktscan,
    )

    cerebras_verbraucht = 0

    def _mit_overflow(schluessel: str, groq_call, cerebras_call) -> bool:
        """Versucht groq_call(); bei JEDER Exception sofort cerebras_call()
        (solange dessen eigener Tages-Deckel nicht erschoepft ist). True bei
        Erfolg (egal welcher Anbieter), False wenn beide scheitern/Cerebras-
        Budget leer ist - Kandidat bleibt dann unverarbeitet.

        Wichtig: ein Datenqualitaets-Gate (Signal.gate_passed/HebelSignal.
        gate_passed == False, z.B. veralteter Preis) schlaegt VOR jedem echten
        LLM-Call fehl - kein Fehler, aber auch KEIN echter Groq-/Cerebras-Call.
        Ein Retry mit Cerebras waere hier sinnlos (identische zugrundeliegende
        Datenlage), UND `provider_je_call` darf keinen Anbieter zuschreiben,
        der nie tatsaechlich aufgerufen wurde (verfaelscht sonst das in
        docs/budget_queue_design.md geforderte Qualitaets-Tracking)."""
        nonlocal cerebras_verbraucht
        try:
            res = groq_call()
            if getattr(res, "gate_passed", True) is False:
                return True
            result.provider_je_call[schluessel] = "groq"
            result.ergebnis_objekt[schluessel] = res
            return True
        except Exception as exc:
            logger.info("Groq-Call für %s fehlgeschlagen (%s), versuche Cerebras", schluessel, exc)

        if cerebras_verbraucht >= cerebras_budget:
            result.cerebras_budget_erschoepft = True
            result.fehlgeschlagen.append(schluessel)
            return False
        try:
            res = cerebras_call()
            if getattr(res, "gate_passed", True) is False:
                return True
            cerebras_verbraucht += 1
            result.cerebras_calls_verbraucht = cerebras_verbraucht
            result.provider_je_call[schluessel] = "cerebras"
            result.ergebnis_objekt[schluessel] = res
            return True
        except Exception as exc:
            logger.warning("Cerebras-Call für %s ebenfalls fehlgeschlagen: %s", schluessel, exc)
            result.fehlgeschlagen.append(schluessel)
            return False

    def _mit_conn(fn):
        """Oeffnet/schliesst einen eigenen conn je Call - jeder LLM-Call ist
        potenziell langsam (Netzwerk), eine gemeinsame lang gehaltene
        Connection ueber alle Kandidaten waere unnoetig fehleranfaellig."""
        conn = conn_factory()
        try:
            return fn(conn)
        finally:
            conn.close()

    # --- Tier 1: Hebel ---
    for trigger in hebel_kandidaten[:tier1_n]:
        asset = next((a for a in watchlist if a.symbol == trigger.symbol), None)
        if asset is None:
            continue
        schluessel = f"hebel:{trigger.symbol}:{trigger.richtung}"
        ok = _mit_overflow(
            schluessel,
            lambda t=trigger, a=asset: _mit_conn(
                lambda c: generate_hebel_signal(t, a, watchlist, c, groq_client, coingecko_client, kraken_client, fred_api_key)
            ),
            lambda t=trigger, a=asset: _mit_conn(
                lambda c: generate_hebel_signal(t, a, watchlist, c, cerebras_client, coingecko_client, kraken_client, fred_api_key)
            ),
        )
        if ok:
            result.hebel_verarbeitet.append(schluessel)

    # --- Tier 2: Marktscan-Kaufkandidaten ---
    if tier2_n > 0:
        conn = conn_factory()
        try:
            regime_result = compute_current_regime(conn, coingecko_client, watchlist, fred_api_key, config_dict)
        finally:
            conn.close()

        def _writeup(candidate, llm_client):
            conn = conn_factory()
            try:
                parsed = generate_candidate_writeup(
                    candidate, regime_result, llm_client, kraken_client, conn, watchlist, config_dict,
                )
                db.update_marktscan_candidate_groq_writeup(
                    conn, candidate.id, parsed.get("short_reasoning"),
                    json.dumps(parsed.get("long_reasoning") or {}, ensure_ascii=False),
                )
            finally:
                conn.close()

        for candidate in marktscan_kandidaten[:tier2_n]:
            schluessel = f"marktscan:{candidate.coingecko_id}"
            ok = _mit_overflow(
                schluessel,
                lambda c=candidate: _writeup(c, groq_client),
                lambda c=candidate: _writeup(c, cerebras_client),
            )
            if ok:
                result.marktscan_verarbeitet.append(schluessel)

    # --- Tier 3: Spot-Rotation ---
    for asset in spot_kandidaten[:tier3_n]:
        schluessel = f"spot:{asset.symbol}"
        ok = _mit_overflow(
            schluessel,
            lambda a=asset: _mit_conn(
                lambda c: generate_signal(a, watchlist, c, groq_client, coingecko_client, kraken_client, fred_api_key)
            ),
            lambda a=asset: _mit_conn(
                lambda c: generate_signal(a, watchlist, c, cerebras_client, coingecko_client, kraken_client, fred_api_key)
            ),
        )
        if ok:
            result.spot_verarbeitet.append(schluessel)

    return result
