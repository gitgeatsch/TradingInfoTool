# -*- coding: utf-8 -*-
"""Erfolgsmessung fuer Marktscan-Kandidaten (2026-07-30, Teil 2 der Reifegrad-/
Erfolgsmessung-Runde, siehe Plan "Marktscan-Reifegrad + Erfolgsmessung").

Eigenes Modul statt Vermischung mit marktscan.py, analog zu
agent/krypto/hebel_backward_tracking.py. Wiederverwendet die Formel-Logik aus
agent/krypto/backward_tracking.py (mindestziel_preis(), schaetze_mindestziel_
zeitraum_tage()) - ABER mit CoinGecko-OHLC statt der Kraken-basierten
price_history_ohlc-Tabelle: Marktscan-Coins sind meist obskure Altcoins, die
kaum auf Kraken gelistet sind, waehrend price_history_ohlc nur fuer Watchlist-
Assets befuellt wird (siehe Modul-Recherche im Plan).

Granularitaets-Hinweis: CoinGecko liefert bei `/coins/{id}/ohlc` je nach
`days`-Parameter unterschiedlich grobe Kerzen (30 Min./4h/4 Tage, dynamisch
gewaehlt) - NICHT garantiert taeglich. Um trotzdem eine echte "Ø taegliche
High-Low-Spanne" zu berechnen (die Formel schaetze_mindestziel_zeitraum_tage()
labelt ihr Ergebnis explizit als Tage), werden die rohen Kerzen hier zuerst zu
echten Kalendertag-Balken aggregiert (_ohlc_rows_zu_tages_bars()), bevor die
Ø-Spannen-Berechnung darauf laeuft - unabhaengig von der tatsaechlich
gelieferten Rohgranularitaet."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone

import database.db as db
from agent.krypto.backward_tracking import (
    DEFAULT_ZEITRAUM_SCHAETZUNG_TAGE_FENSTER,
    mindestziel_preis,
    schaetze_mindestziel_zeitraum_tage,
)
from agent.krypto.llm_provider import llm_model_label
from agent.krypto.marktscan import generate_candidate_writeup
from agent.krypto.pipeline import compute_current_regime
from database.models import MarktscanCandidate

logger = logging.getLogger(__name__)

# CoinGecko-OHLC-Abrufzeitraum fuer starte_messung() - deckt das
# DEFAULT_ZEITRAUM_SCHAETZUNG_TAGE_FENSTER (14 Tage) plus Puffer ab, falls
# einzelne Kalendertage in der CoinGecko-Antwort fehlen sollten.
_OHLC_ABRUF_TAGE = 30


@dataclass
class _TagesBar:
    high: float
    low: float


def _ohlc_rows_zu_tages_bars(raw: list) -> list[_TagesBar]:
    """Aggregiert rohe CoinGecko-Kerzen (`[ts_ms, open, high, low, close]`,
    beliebige Granularitaet) zu einem `_TagesBar` je UTC-Kalendertag (High =
    Tagesmaximum, Low = Tagesminimum aller Kerzen dieses Tages) - siehe
    Modul-Docstring fuer die Begruendung. Chronologisch aufsteigend sortiert,
    wie von schaetze_mindestziel_zeitraum_tage()/_durchschnittliche_
    tagesspanne() erwartet."""
    by_day: dict[str, list[tuple[float, float]]] = {}
    for row in raw:
        if len(row) < 5:
            continue
        ts_ms, _open, high, low, _close = row[:5]
        if high is None or low is None:
            continue
        day = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        by_day.setdefault(day, []).append((high, low))
    bars = []
    for day in sorted(by_day.keys()):
        highs_lows = by_day[day]
        bars.append(_TagesBar(
            high=max(h for h, _ in highs_lows),
            low=min(l for _, l in highs_lows),
        ))
    return bars


def _durchschnittliche_tagesspanne_coingecko(
    tages_bars: list[_TagesBar], fenster_tage: int = DEFAULT_ZEITRAUM_SCHAETZUNG_TAGE_FENSTER,
) -> float | None:
    """Eigene, schlanke Kopie von backward_tracking.py::_durchschnittliche_
    tagesspanne() (die ist privat/Kraken-intern) - identische Ø-High-Low-Logik,
    andere Datenquelle. Wird HIER separat gebraucht (fuer risiko_distanz in
    mindestziel_preis()), obwohl schaetze_mindestziel_zeitraum_tage() dieselbe
    Spanne intern nochmal berechnet - kein Duplikat der Formel-DATEI, nur ein
    zweiter Aufruf derselben oeffentlichen Formel-FUNKTION unten."""
    relevante = tages_bars[-fenster_tage:]
    if len(relevante) < 2:
        return None
    spannen = [b.high - b.low for b in relevante]
    avg = sum(spannen) / len(spannen)
    return avg if avg > 0 else None


def starte_messung(conn, candidate: MarktscanCandidate, coingecko_client, config_dict: dict) -> dict | None:
    """Startet eine neue Erfolgsmessung fuer `candidate`: holt CoinGecko-OHLC,
    berechnet Mindestziel-Preis (CRV-basiert, marktscan-eigene Schwelle) und die
    geschaetzte Zeitspanne bis dahin, persistiert beides + outcome_status='offen'.
    Fehlschlag (kein OHLC verfuegbar/zu wenig Kalendertage) -> bleibt
    'nicht_anwendbar', KEIN Hard-Fail (Aufrufer laeuft mit dem naechsten
    Kandidaten weiter)."""
    erfolgsmessung_cfg = config_dict["marktscan"]["erfolgsmessung"]
    crv = erfolgsmessung_cfg["richtungstreffer_mindest_crv"]
    try:
        raw = coingecko_client.get_coin_ohlc(candidate.coingecko_id, days=_OHLC_ABRUF_TAGE)
    except Exception as exc:
        logger.info(
            "CoinGecko-OHLC-Abruf für Erfolgsmessung-Start (%s) fehlgeschlagen: %s",
            candidate.symbol, exc,
        )
        return None
    tages_bars = _ohlc_rows_zu_tages_bars(raw)
    avg_tagesspanne = _durchschnittliche_tagesspanne_coingecko(tages_bars)
    if avg_tagesspanne is None:
        return None
    ziel_preis = mindestziel_preis(candidate.price_usd, avg_tagesspanne, crv, ist_short=False)
    zeitraum_tage = schaetze_mindestziel_zeitraum_tage(ziel_preis, candidate.price_usd, tages_bars)
    if ziel_preis is None or zeitraum_tage is None:
        return None
    db.update_marktscan_outcome_start(conn, candidate.id, ziel_preis, zeitraum_tage)
    return {"mindestziel_usd": ziel_preis, "mindestziel_zeitraum_tage_geschaetzt": zeitraum_tage}


def pruefe_messung(conn, candidate: MarktscanCandidate, aktueller_preis: float, max_tage: float) -> dict:
    """Prueft eine laufende Messung (`candidate.outcome_status == 'offen'`) gegen
    den aktuellen Preis. `outcome_return_pct` wird IMMER aktualisiert (auch
    waehrend die Messung offen bleibt). Erfolg = aktueller Preis hat das bereits
    gespeicherte `mindestziel_usd` erreicht/uebertroffen (direkter Preisvergleich,
    kein erneutes CRV-Zurueckrechnen noetig - das Mindestziel IST bereits der
    CRV-Zielpreis). Kein Erfolg, wenn seit `outcome_gestartet_am` mindestens
    `max_tage` (config marktscan.erfolgsmessung.mindestziel_zeitraum_tage_cap)
    vergangen sind, ohne dass das Ziel erreicht wurde."""
    outcome_return_pct = (aktueller_preis - candidate.price_usd) / candidate.price_usd * 100

    gestartet = datetime.fromisoformat(candidate.outcome_gestartet_am)
    if gestartet.tzinfo is None:
        gestartet = gestartet.replace(tzinfo=timezone.utc)
    tage_seit_start = (datetime.now(timezone.utc) - gestartet).total_seconds() / 86400.0

    ziel_erreicht = aktueller_preis >= candidate.mindestziel_usd
    if ziel_erreicht:
        outcome_status = "erfolg"
        db.update_marktscan_outcome_ergebnis(
            conn, candidate.id, outcome_status, outcome_return_pct, geprueft_abschliessen=True,
        )
        return {
            "outcome_status": outcome_status, "outcome_return_pct": outcome_return_pct,
            "tatsaechliche_dauer_tage": tage_seit_start,
        }
    if tage_seit_start >= max_tage:
        outcome_status = "kein_erfolg"
        db.update_marktscan_outcome_ergebnis(
            conn, candidate.id, outcome_status, outcome_return_pct, geprueft_abschliessen=True,
        )
        return {
            "outcome_status": outcome_status, "outcome_return_pct": outcome_return_pct,
            "tatsaechliche_dauer_tage": tage_seit_start,
        }
    db.update_marktscan_outcome_ergebnis(conn, candidate.id, "offen", outcome_return_pct)
    return {"outcome_status": "offen", "outcome_return_pct": outcome_return_pct}


def _sichtung_position_aus_signale(candidate: MarktscanCandidate) -> int:
    """Liest `sichtung_position` aus `signale_momentum_json` (siehe
    marktscan.py::score_momentum()) - 0 falls nicht vorhanden (z.B. Sichtung 1-2,
    unter dem Streak-Malus-Schwellenwert, gar nicht erst im Dict)."""
    try:
        signale = json.loads(candidate.signale_momentum_json or "{}")
    except (TypeError, ValueError):
        return 0
    return signale.get("sichtung_position", 0) or 0


def run_marktscan_backward_tracking(
    conn_factory, coingecko_client, kraken_client, llm_client, watchlist, fred_api_key, config_dict: dict,
) -> dict:
    """Orchestriert die Erfolgsmessung in 2 Schritten (siehe Plan Abschnitt 3):
    1. Neue Messungen starten (Kaufkandidaten + "heisse" Watchlist-Kandidaten,
       sichtung_position >= 3), 2. laufende Messungen pruefen (EIN gebuendelter
       Preis-Check fuer alle offenen Coins). Sammelt Kandidaten mit
       ungewoehnlich schneller Aufloesung (Mail 3, siehe scheduler/
       background.py::_notify_marktscan_schnellerfolg()) - JEDER Erfolg wird
       trotzdem vollstaendig in der DB erfasst, nur die Sammel-Liste fuer die
       E-Mail ist selektiv."""
    erfolgsmessung_cfg = config_dict["marktscan"]["erfolgsmessung"]
    max_tage = erfolgsmessung_cfg["mindestziel_zeitraum_tage_cap"]
    schnellerfolg_anteil_max = erfolgsmessung_cfg["schnellerfolg_anteil_max"]

    conn = conn_factory()
    try:
        neue_messungen = 0
        kandidaten_fuer_start = db.get_marktscan_kandidaten_fuer_messstart(conn)
        for candidate in kandidaten_fuer_start:
            if candidate.einstufung == "watchlist_wuerdig" and _sichtung_position_aus_signale(candidate) < 3:
                continue
            if db.has_pending_marktscan_messung(conn, candidate.coingecko_id):
                continue
            if starte_messung(conn, candidate, coingecko_client, config_dict) is not None:
                neue_messungen += 1

        geprueft = 0
        erfolge = 0
        kein_erfolg = 0
        schnellerfolge = []
        offene = db.get_offene_marktscan_messungen(conn)
        preis_abruf_fehler = None
        if offene:
            coingecko_ids = sorted({c.coingecko_id for c in offene})
            # EIN gebuendelter Abruf fuer ALLE offenen Messungen - und genau
            # deshalb muss er fail-soft sein (2026-08-09, echter Vorfall):
            # CoinGecko lieferte ein "504 Gateway Timeout" auf eine Anfrage mit
            # 28 IDs, die Exception lief bis scheduler/background.py durch und
            # beendete die GESAMTE Erfolgsmessung - inklusive der oben bereits
            # gestarteten neuen Messungen.
            #
            # WARUM HIER UND NICHT IM CLIENT: api/zai.py haelt als bewusste
            # Entscheidung fest, dass Timeout/5xx/Verbindungsfehler NICHT
            # wiederholt werden - "P-8 (kein Hard-Fail, Aufrufer faengt die
            # Exception ab)". Die Annahme stimmte hier nicht: der Aufrufer fing
            # nichts ab. Repariert wird deshalb die Annahme, nicht der Client.
            #
            # FAIL-SOFT, ABER NICHT FAIL-SILENT: der Grund geht als Zaehler in
            # das Ergebnis und damit in die Log-Zeile des Jobs. Ein Ausfall, den
            # niemand sieht, ist von "es gab nichts zu pruefen" nicht zu
            # unterscheiden (Memory feedback_fail_soft_ist_fail_silent).
            # Unverarbeitete Messungen bleiben offen - der naechste Lauf prueft
            # sie erneut, kein Datenverlust (P-10).
            try:
                preise = coingecko_client.get_simple_prices(coingecko_ids, vs_currencies=("usd",))
            except Exception as exc:  # noqa: BLE001
                preis_abruf_fehler = f"{type(exc).__name__}: {str(exc)[:160]}"
                logger.warning(
                    "Marktscan-Erfolgsmessung: Preisabruf fuer %d offene Messung(en) "
                    "fehlgeschlagen (%s) - keine davon geprueft, sie bleiben offen und "
                    "werden im naechsten Lauf erneut versucht.",
                    len(coingecko_ids), preis_abruf_fehler,
                )
                preise = {}
            regime_result = None
            for candidate in offene:
                preis_daten = preise.get(candidate.coingecko_id)
                if preis_daten is None or preis_daten.get("usd") is None:
                    continue
                aktueller_preis = preis_daten["usd"]
                ergebnis = pruefe_messung(conn, candidate, aktueller_preis, max_tage)
                geprueft += 1
                if ergebnis["outcome_status"] != "erfolg":
                    if ergebnis["outcome_status"] == "kein_erfolg":
                        kein_erfolg += 1
                    continue
                erfolge += 1
                if not candidate.groq_kurzbegruendung and llm_client is not None:
                    try:
                        if regime_result is None:
                            regime_result = compute_current_regime(
                                conn, coingecko_client, watchlist, fred_api_key, config_dict,
                            )
                        parsed = generate_candidate_writeup(
                            candidate, regime_result, llm_client, kraken_client, conn, watchlist,
                            config_dict, fred_api_key,
                        )
                        db.update_marktscan_candidate_groq_writeup(
                            conn, candidate.id, parsed.get("short_reasoning"),
                            json.dumps(parsed.get("long_reasoning") or {}, ensure_ascii=False),
                            llm_model=llm_model_label(llm_client),
                        )
                    except Exception as exc:
                        logger.info(
                            "LLM-Kurzbegründung für Erfolgsmeldung (%s) fehlgeschlagen: %s",
                            candidate.symbol, exc,
                        )
                dauer = ergebnis["tatsaechliche_dauer_tage"]
                geschaetzt = candidate.mindestziel_zeitraum_tage_geschaetzt
                if geschaetzt and geschaetzt > 0 and dauer <= schnellerfolg_anteil_max * geschaetzt:
                    schnellerfolge.append({
                        "candidate": candidate,
                        "outcome_return_pct": ergebnis["outcome_return_pct"],
                        "tatsaechliche_dauer_tage": dauer,
                        "geschaetzte_dauer_tage": geschaetzt,
                    })
        return {
            "neue_messungen": neue_messungen, "geprueft": geprueft,
            "erfolge": erfolge, "kein_erfolg": kein_erfolg, "schnellerfolge": schnellerfolge,
            # None, solange der Preisabruf durchging - sonst der Grund. Steht in
            # der Log-Zeile des Jobs, damit ein stiller Ausfall nicht wie ein
            # ruhiger Lauf aussieht.
            "preis_abruf_fehler": preis_abruf_fehler,
        }
    finally:
        conn.close()


# Mindest-Stichprobe fuer eine belastbare Aussage - eigene, lokale Kopie
# desselben Werts wie backward_tracking.py::_MIN_SAMPLE_FUER_AUSSAGE (dort
# privat/modul-intern, siehe Modul-Docstring-Grundsatz "keine privaten
# Funktionen/Konstanten anderer Module importieren").
_MIN_SAMPLE_FUER_AUSSAGE = 15


def compute_marktscan_erfolgsquote(conn) -> dict | None:
    """Remote-Status-Karte (2026-07-30, analog backward_tracking.py::
    compute_richtungstreffer_quote()): Anteil der ABGESCHLOSSENEN Erfolgsmessungen
    (erfolg ODER kein_erfolg, 'offen' zaehlt nicht mit) die tatsaechlich
    erfolgreich waren. `None` falls noch keine einzige Messung abgeschlossen
    ist (frisches Feature, siehe Docstring-Grundsatz "reiner Lesezugriff, keine
    Seiteneffekte")."""
    rows = conn.execute(
        "SELECT outcome_status, outcome_gestartet_am, outcome_geprueft_am "
        "FROM marktscan_candidates WHERE outcome_status IN ('erfolg', 'kein_erfolg')"
    ).fetchall()
    total = len(rows)
    if total == 0:
        return None

    erfolge = sum(1 for r in rows if r["outcome_status"] == "erfolg")
    quote_pct = round(100.0 * erfolge / total, 1)

    offen_row = conn.execute(
        "SELECT COUNT(*) AS n FROM marktscan_candidates WHERE outcome_status = 'offen'"
    ).fetchone()
    offen = offen_row["n"] if offen_row else 0

    tage_liste = []
    for r in rows:
        if r["outcome_status"] != "erfolg" or not r["outcome_gestartet_am"] or not r["outcome_geprueft_am"]:
            continue
        try:
            gestartet = datetime.fromisoformat(r["outcome_gestartet_am"])
            geprueft = datetime.fromisoformat(r["outcome_geprueft_am"])
        except ValueError:
            continue
        tage_liste.append((geprueft - gestartet).total_seconds() / 86400.0)

    ausreichend_stichprobe = len(tage_liste) >= _MIN_SAMPLE_FUER_AUSSAGE
    avg_tage = round(sum(tage_liste) / len(tage_liste), 1) if tage_liste else None

    return {
        "anzahl_ausgewertet": total,
        "erfolge": erfolge,
        "erfolgsquote_pct": quote_pct,
        "offen": offen,
        "avg_tage_bis_erfolg": avg_tage if ausreichend_stichprobe else None,
        "avg_tage_bis_erfolg_stichprobe_n": len(tage_liste),
        "ausreichend_stichprobe": ausreichend_stichprobe,
    }
