"""Batch-Signal-Berechnung (2026-07-13, Nutzer-Wunsch) - siehe
Basisinfos/Regelwerksmanual.md fuer den vollen Kontext. Ausloeser: Die
Groq-basierte Signal-Berechnung ist bewusst manuell (jeder Lauf kostet einen
KI-Aufruf, siehe agent/krypto/analyst.py::call_groq_for_signal()), aber bei
54 Watchlist-Assets ohne Handy-App unpraktisch, wenn niemand 54x einzeln
klicken kann.

Gemessen statt geschaetzt (2026-07-13): eine echte Signal-Berechnung
verbraucht ~5.600-6.000 Tokens (System-Prompt ~12.072 Zeichen/~3.450 Tokens +
Fakten-JSON ~5.100-6.500 Zeichen + Antwort ~2.560 Zeichen). Bei Groq
Free-Tier (100.000 Tokens/Tag) sind das reale ~15-18 Berechnungen/Tag - NICHT
die 1.000 Requests/Tag, die der RPD-Wert allein suggerieren wuerde (TPD ist
die bindende Grenze).

Zweistufig wie Marktscan (agent/krypto/marktscan.py): eine guenstige Auswahl
(reine Staleness-Sortierung, kein Groq-Aufruf) laeuft ueber ALLE
Watchlist-Assets, die teure Groq-Analyse nur fuer eine budget-begrenzte
Teilmenge pro Lauf. Wird sowohl vom Scheduler-Job (taeglicher
Wochen-Sicherheitsnetz-Lauf) als auch vom manuellen UI-Button aufgerufen."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

import database.db as db
from agent.krypto.pipeline import generate_signal
from database.models import Signal

logger = logging.getLogger(__name__)

# Nur fuer die Statusanzeige/Meldung ("X Assets ueberfaellig") - KEIN Gate
# fuer die Auswahl selbst (siehe select_assets_due_for_signal()-Docstring):
# bei ~15-18 moeglichen Berechnungen/Tag und 54 Assets braucht ein reiner
# Rotations-Ansatz (aeltestes zuerst, jeden Tag erneut) nur ~4 Tage fuer
# einen kompletten Durchlauf - deutlich Puffer gegenueber 7 Tagen.
SIGNAL_STALE_THRESHOLD_DAYS = 7


@dataclass
class BatchResult:
    berechnet: list[Signal] = field(default_factory=list)
    fehlgeschlagen: list[str] = field(default_factory=list)
    verbleibend_ueberfaellig: int = 0
    budget_erschoepft: bool = False


def _tage_seit(created_at: str | None) -> float:
    """None (noch nie eine echte Analyse) -> unendlich, damit diese Assets
    in der Sortierung immer zuerst drankommen."""
    if created_at is None:
        return float("inf")
    then = datetime.fromisoformat(created_at)
    if then.tzinfo is None:
        then = then.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - then).total_seconds() / 86400


def select_assets_due_for_signal(conn, watchlist: list, max_count: int) -> list:
    """Sortiert alle Watchlist-Assets (aktiv UND watchlist-Status - Nutzer-
    Wunsch 2026-07-13: 'sonst macht es keinen Sinn') nach Tagen seit der
    letzten ECHTEN Groq-Analyse absteigend (nie berechnet zuerst), gibt die
    ersten `max_count` zurueck.

    Bewusst KEIN Gate auf SIGNAL_STALE_THRESHOLD_DAYS hier: das wuerde bei
    einer bereits "eingeschwungenen" Rotation (alles < 7 Tage alt) dazu
    fuehren, dass der taegliche Job/manuelle Klick zeitweise NICHTS tut und
    sich dann alle Assets gleichzeitig stauen, sobald sie die 7-Tage-Grenze
    reissen. Stattdessen: immer die global aeltesten zuerst, das ergibt eine
    gleichmaessige Rotation ohne Bursts. Die Schwelle dient nur der
    Ueberfaellig-Meldung (siehe run_signal_batch()).

    Stablecoins ausgeschlossen (A-1: bekommen strukturell nie ein echtes
    Signal - generate_signal() gibt sofort HALTEN zurueck, ohne Groq zu
    rufen - wuerden sonst wegen "nie berechnet" dauerhaft ganz oben in der
    Prioritaet stehen und echte Analysen verdraengen).

    Nicht-Krypto-Assets (Aktien/ETF/Rohstoffe) ebenfalls ausgeschlossen -
    agent/krypto/pipeline.py::generate_signal() ist Krypto-only (braucht
    asset.coingecko_id fuer die Kurshistorie, das Aktien/ETF/Rohstoffe nicht
    haben, siehe Spezifikation Kap. 11 "Zielarchitektur fuer Multi-Asset-
    Erweiterbarkeit"). Identisches Filtermuster wie
    ui/signals_view.py::SignalsView.__init__()."""
    latest_real = db.get_latest_real_signal_per_symbol(conn)
    candidates = [a for a in watchlist if a.assetklasse == "krypto" and a.typ != "stablecoin"]
    candidates.sort(
        key=lambda a: _tage_seit(latest_real[a.symbol].created_at if a.symbol in latest_real else None),
        reverse=True,
    )
    return candidates[:max_count]


def run_signal_batch(
    conn_factory,
    watchlist: list,
    groq_client,
    coingecko_client,
    kraken_client,
    fred_api_key: str | None,
    daily_budget: int,
    progress_callback: Callable[[int, int, str], None] | None = None,
    cerebras_client=None,
) -> BatchResult:
    """Nur noch vom manuellen UI-Button (ui/signals_view.py) aufgerufen - der
    urspruengliche taegliche Scheduler-Job (signal_batch_job) wurde in Phase 5
    entfernt, seitdem laeuft die automatische Spot-Rotation ausschliesslich
    ueber den Budget-Allocator (agent/krypto/budget_allocator.py, Tier 3).
    `progress_callback(done, total, symbol)` optional fuer eine
    UI-Fortschrittsanzeige.

    Groq-dann-Cerebras-Fallback (2026-07-14, nachgezogen nach echtem
    Notebook-Vorfall) - `cerebras_client` optional (P-8), ohne ihn bleibt der
    Batch reines Groq wie zuvor. Pro Asset EIGENE Fallback-Entscheidung
    (kein gemeinsamer "Groq ist heute tot"-Kurzschluss ueber den ganzen
    Batch) - konsistent mit dem Budget-Allocator/Hebel-Tab-Muster.

    Budget-Pruefung ueber db.count_real_signals_today() statt eines eigenen
    Zaehlers: da sowohl der Einzel-Klick-Button ("Signal berechnen") als auch
    der Budget-Allocator in dieselbe signals-Tabelle schreiben, ist das
    Tagesbudget automatisch ueber alle drei Ausloeser (Einzel-Klick,
    Batch-Button, Budget-Allocator) hinweg korrekt geteilt - kein
    zusaetzlicher Zaehler/Tabelle noetig.

    Bekannte Ungenauigkeit (P-10-Stil, dokumentiert statt versteckt): ein
    fehlgeschlagener Retry-Versuch (kaputtes JSON, siehe analyst.py::
    call_groq_for_signal()) verbraucht bei Groq echte Tokens, zaehlt hier
    aber nicht mit, da groq_raw_response dabei None bleibt - das Budget ist
    eine gute Naeherung, keine harte Garantie gegen Groqs eigenen
    Token-Zaehler.

    Einzelne Fehlschlaege (z.B. Netzwerk-Hickser bei einem Asset) brechen
    NICHT den ganzen Batch ab - geloggt, in `fehlgeschlagen` gesammelt,
    naechstes Asset wird trotzdem versucht (P-10)."""
    conn = conn_factory()
    try:
        bereits_heute = db.count_real_signals_today(conn)
        verbleibendes_budget = max(0, daily_budget - bereits_heute)
        faellige = select_assets_due_for_signal(conn, watchlist, max_count=verbleibendes_budget)
    finally:
        conn.close()

    def _attempt(asset, llm_client):
        conn = conn_factory()
        try:
            return generate_signal(
                asset, watchlist, conn, llm_client, coingecko_client, kraken_client,
                fred_api_key=fred_api_key,
            )
        finally:
            conn.close()

    result = BatchResult()
    for index, asset in enumerate(faellige):
        if progress_callback:
            progress_callback(index, len(faellige), asset.symbol)
        try:
            signal = _attempt(asset, groq_client)
            result.berechnet.append(signal)
        except Exception as exc:
            if cerebras_client is not None:
                try:
                    signal = _attempt(asset, cerebras_client)
                    result.berechnet.append(signal)
                    continue
                except Exception:
                    logger.exception("Batch-Signal-Berechnung für %s (Groq UND Cerebras) fehlgeschlagen", asset.symbol)
                    result.fehlgeschlagen.append(asset.symbol)
                    continue
            logger.exception("Batch-Signal-Berechnung für %s fehlgeschlagen (%s)", asset.symbol, exc)
            result.fehlgeschlagen.append(asset.symbol)

    conn = conn_factory()
    try:
        latest_real = db.get_latest_real_signal_per_symbol(conn)
        bereits_heute_danach = db.count_real_signals_today(conn)
    finally:
        conn.close()

    result.verbleibend_ueberfaellig = sum(
        1
        for a in watchlist
        if a.assetklasse == "krypto" and a.typ != "stablecoin"
        and _tage_seit(latest_real[a.symbol].created_at if a.symbol in latest_real else None)
        > SIGNAL_STALE_THRESHOLD_DAYS
    )
    result.budget_erschoepft = bereits_heute_danach >= daily_budget
    return result
