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
from datetime import datetime, timedelta, timezone
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

# Fix (2026-07-15, echter Notebook-Vorfall - siehe Memory
# project_llm_budget_ueberlast_2026-07-15.md): Default-Cooldown fuer
# select_assets_due_for_signal(), siehe dortige Docstring-Erweiterung fuer
# den vollen Kontext. <24h, damit die Rotation nicht durch feste Tick-Zeiten
# schrittweise nach hinten driftet.
SPOT_COOLDOWN_STUNDEN = 20.0

# Zwei-Stufen-Cooldown (2026-07-16, Nutzer-Wunsch nach Gewichtungs-Analyse):
# `core`-Assets (RM-2-Kernallokation) UND aktuell gehaltene Assets bekommen
# einen kuerzeren Cooldown als reine taktische Watchlist-Kandidaten ohne
# Position - beide vertreten "echtes Geld/strategische Kernrolle" und
# verdienen haeufigere Neubewertung als ein x-beliebiger unbeobachteter
# Satellit. Reale Watchlist (2026-07-16): 13 core (100% davon gehalten) +
# 8 weitere gehaltene taktische Assets = 21 "Kern"-Symbole, 19 rein
# taktische Watchlist-Symbole ohne Position bleiben bei SPOT_COOLDOWN_STUNDEN.
# ~2x/Tag statt ~1x/Tag fuer diese 21 Symbole - moderater Mehrverbrauch
# (~13-21 zusaetzliche Calls/Tag ggue. reiner Gleichbehandlung), da nur ein
# Teil der 40 Assets betroffen ist, kein Rueckfall in die alte Burst-Problematik.
SPOT_COOLDOWN_STUNDEN_KERN = 10.0

# Dritte Cooldown-Stufe (Klassifikations-Redesign 2026-07-16, siehe Memory
# project_asset_klassifikation_redesign): `beobachtungsstatus == "ausgemustert"`
# bedeutet niedrigste Prioritaet, NICHT Ausschluss ("darf nicht sterben",
# Nutzer-Formulierung) - ein Tage- statt Stunden-Wert macht das spuerbar
# seltener, ohne auf null zu gehen. [OFFEN]/vorlaeufig wie die anderen
# Cooldown-Werte, noch nicht ueber echten Betrieb kalibriert.
SPOT_COOLDOWN_STUNDEN_AUSGEMUSTERT = 120.0  # 5 Tage


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


def select_assets_due_for_signal(
    conn, watchlist: list, max_count: int, cooldown_stunden: float | None = SPOT_COOLDOWN_STUNDEN,
    cooldown_stunden_kern: float | None = SPOT_COOLDOWN_STUNDEN_KERN,
    cooldown_stunden_ausgemustert: float | None = SPOT_COOLDOWN_STUNDEN_AUSGEMUSTERT,
) -> list:
    """Sortiert alle Watchlist-Assets (aktiv UND watchlist-Status - Nutzer-
    Wunsch 2026-07-13: 'sonst macht es keinen Sinn') nach Tagen seit der
    letzten ECHTEN Groq-Analyse absteigend (nie berechnet zuerst), gibt die
    ersten `max_count` zurueck.

    Ehemals KEIN Gate auf SIGNAL_STALE_THRESHOLD_DAYS: das wuerde bei einer
    bereits "eingeschwungenen" Rotation (alles < 7 Tage alt) dazu fuehren,
    dass der taegliche Job/manuelle Klick zeitweise NICHTS tut und sich dann
    alle Assets gleichzeitig stauen, sobald sie die 7-Tage-Grenze reissen.
    Stattdessen: immer die global aeltesten zuerst, das ergibt eine
    gleichmaessige Rotation ohne Bursts. Die Schwelle dient nur der
    Ueberfaellig-Meldung (siehe run_signal_batch()).

    Cooldown-Fix (2026-07-15, echter Notebook-Vorfall - siehe Memory
    project_llm_budget_ueberlast_2026-07-15.md): diese Begruendung stimmte
    fuer EINEN taeglichen Cron-Lauf, aber seit Phase 5 ruft der Budget-
    Allocator (budget_allocator.py) diese Funktion alle 15 Min auf - ohne
    Cooldown rotierte das System bei ~40 Krypto-Assets komplett innerhalb
    von ~40 Minuten durch (bestaetigt: 234 Spot-Signale an einem Tag fuer
    nur 40 distinkte Symbole). `cooldown_stunden` schliesst jetzt Assets mit
    einer echten Analyse INNERHALB des Cooldown-Fensters aus, bevor sortiert/
    gekappt wird - analog zum bereits bestehenden Hebel-/Marktscan-Cooldown
    in budget_allocator.py (dort war Tier 3 bisher die einzige Ausnahme ohne
    Gate). `cooldown_stunden=None` behaelt das alte, ungefilterte Verhalten
    bei (z.B. fuer Tests).

    Drei-Stufen-Cooldown (2026-07-16, Klassifikations-Redesign, siehe Memory
    project_asset_klassifikation_redesign): ein Asset gilt als "Kern"
    (kuerzester `cooldown_stunden_kern`), wenn `asset.rolle == "core"` ODER es
    aktuell gehalten wird (Spot-Bestand+gestakte Menge > 0, live per
    `db.get_all_holdings()` geprueft) ODER es eine offene Hebel-Position
    darauf gibt (live per `db.get_open_hebel_positions()` geprueft - echtes,
    gehebeltes Geld verdient dieselbe Prioritaet wie ein Spot-Bestand). Ist
    keine Kern-Bedingung erfuellt UND `asset.beobachtungsstatus ==
    "ausgemustert"`, gilt der laengste `cooldown_stunden_ausgemustert`
    (niedrigste Prioritaet, aber NIE Ausschluss - "darf nicht sterben",
    Nutzer-Formulierung, siehe Memory). Praezedenz: Kern schlaegt IMMER
    Ausgemustert (ein Asset mit echtem Engagement wird nie durch eine
    Beobachtungsabsicht ausgebremst). Sonst `cooldown_stunden` als Standard
    (Taktisch/Beobachtung). `cooldown_stunden_kern=None` UND
    `cooldown_stunden_ausgemustert=None` deaktivieren die Mehrstufigkeit
    (dann gilt `cooldown_stunden` fuer alle gleich, altes Verhalten).

    Cash-Aequivalente (Stablecoins) ausgeschlossen (A-1: bekommen
    strukturell nie ein echtes Signal - generate_signal() gibt sofort HALTEN
    zurueck, ohne Groq zu rufen - wuerden sonst wegen "nie berechnet"
    dauerhaft ganz oben in der Prioritaet stehen und echte Analysen
    verdraengen).

    Nicht-Krypto-Assets (Aktien/ETF/Rohstoffe) ebenfalls ausgeschlossen -
    agent/krypto/pipeline.py::generate_signal() ist Krypto-only (braucht
    asset.coingecko_id fuer die Kurshistorie, das Aktien/ETF/Rohstoffe nicht
    haben, siehe Spezifikation Kap. 11 "Zielarchitektur fuer Multi-Asset-
    Erweiterbarkeit"). Identisches Filtermuster wie
    ui/signals_view.py::SignalsView.__init__()."""
    latest_real = db.get_latest_real_signal_per_symbol(conn)
    candidates = [a for a in watchlist if a.assetklasse == "krypto" and not a.ist_cash_aequivalent]

    kern_symbole: set[str] = set()
    if cooldown_stunden_kern is not None:
        gehaltene_symbole = {
            h.symbol for h in db.get_all_holdings(conn)
            if (h.quantity or 0.0) + (h.staked_quantity or 0.0) > 0.0
        }
        offene_hebel_symbole = {p.symbol for p in db.get_open_hebel_positions(conn)}
        kern_symbole = {
            a.symbol for a in candidates
            if a.rolle == "core" or a.symbol in gehaltene_symbole or a.symbol in offene_hebel_symbole
        }

    ausgemusterte_symbole = {
        a.symbol for a in candidates
        if a.beobachtungsstatus == "ausgemustert" and a.symbol not in kern_symbole
    }

    def _cooldown_fuer(asset) -> float | None:
        if asset.symbol in kern_symbole:
            return cooldown_stunden_kern
        if asset.symbol in ausgemusterte_symbole:
            return cooldown_stunden_ausgemustert
        return cooldown_stunden

    if cooldown_stunden or cooldown_stunden_kern or cooldown_stunden_ausgemustert:
        now = datetime.now(timezone.utc)
        gefiltert = []
        for a in candidates:
            cd = _cooldown_fuer(a)
            if not cd:
                gefiltert.append(a)
                continue
            grenze = (now - timedelta(hours=cd)).isoformat()
            sig = latest_real.get(a.symbol)
            if sig is None or sig.created_at < grenze:
                gefiltert.append(a)
        candidates = gefiltert

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
    gemini_client=None,
) -> BatchResult:
    """Nur noch vom manuellen UI-Button (ui/signals_view.py) aufgerufen - der
    urspruengliche taegliche Scheduler-Job (signal_batch_job) wurde in Phase 5
    entfernt, seitdem laeuft die automatische Spot-Rotation ausschliesslich
    ueber den Budget-Allocator (agent/krypto/budget_allocator.py, Tier 3).
    `progress_callback(done, total, symbol)` optional fuer eine
    UI-Fortschrittsanzeige.

    Groq-dann-Cerebras-dann-Gemini-Fallback (2026-07-14, Gemini als dritte
    Stufe ergaenzt) - `cerebras_client`/`gemini_client` optional (P-8), ohne
    sie bleibt der Batch entsprechend kuerzer in der Kette. Pro Asset EIGENE
    Fallback-Entscheidung (kein gemeinsamer "Groq ist heute tot"-Kurzschluss
    ueber den ganzen Batch) - konsistent mit dem Budget-Allocator/Hebel-Tab-
    Muster.

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

    llm_clients = [c for c in (groq_client, cerebras_client, gemini_client) if c is not None]

    result = BatchResult()
    for index, asset in enumerate(faellige):
        if progress_callback:
            progress_callback(index, len(faellige), asset.symbol)
        signal, last_exc = None, None
        for llm_client in llm_clients:
            try:
                signal = _attempt(asset, llm_client)
                break
            except Exception as exc:
                last_exc = exc
        if signal is not None:
            result.berechnet.append(signal)
        else:
            logger.error(
                "Batch-Signal-Berechnung für %s fehlgeschlagen (%s)", asset.symbol, last_exc, exc_info=last_exc,
            )
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
        if a.assetklasse == "krypto" and not a.ist_cash_aequivalent
        and _tage_seit(latest_real[a.symbol].created_at if a.symbol in latest_real else None)
        > SIGNAL_STALE_THRESHOLD_DAYS
    )
    result.budget_erschoepft = bereits_heute_danach >= daily_budget
    return result
