"""Hebel-Backward-Tracking (2026-07-15) - mirror von agent/krypto/backward_tracking.py
(Selbstverifikations-Vision Schritt 2), aber fuer hebel_signals statt signals. Prueft
vergangene ERÖFFNEN/NACHKAUFEN-Hebel-Empfehlungen gegen die seit ihrer Erstellung
tatsaechlich eingetretene Kurshistorie - richtungsabhaengig (LONG/SHORT), da bei SHORT
Take-Profit unterhalb und Stop-Loss oberhalb des Einstiegs liegt (umgekehrt zu LONG/Spot).

Zusaetzlich zu take_profit_erreicht/stop_loss_erreicht gibt es hier
OUTCOME_LIQUIDATION: der Liquidationspreis liegt naeher am Kurs als der Stop-Loss
(Sicherheitsmarge 15-20%, siehe Regelwerksmanual) - wird deshalb VOR dem Stop-Loss
geprueft (konservativste Annahme zuerst, gleiches Prinzip wie "trifft ein Tag beide
Zonen, gewinnt Stop-Loss" in backward_tracking.py). Rein beobachtend (P-7 Advisory-only)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import database.db as db
from agent.krypto.backward_tracking import (
    DEFAULT_ABGELAUFEN_TAGE_BUCKET,
    DEFAULT_ABGELAUFEN_TAGE_FALLBACK,
    DEFAULT_MINDESTBEOBACHTUNG_TAGE_BUCKET,
    DEFAULT_MINDESTBEOBACHTUNG_TAGE_FALLBACK,
    DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    DEFAULT_ZONEN_REAFFIRMATION_TOLERANZ_RELATIV,
    OUTCOME_ABGELAUFEN,
    OUTCOME_LIQUIDATION,
    OUTCOME_NICHT_ANWENDBAR,
    OUTCOME_OFFEN,
    OUTCOME_STOP_LOSS,
    OUTCOME_TAKE_PROFIT,
    OUTCOME_UEBERHOLT,
    _zonen_schwelle,
    gap_bewusster_fill,
    persistiere_offenes_mfe,
)

# Hebel-spezifischer Override (2026-07-22, siehe Plan-Datei "Ueberholt-
# Erkennung reparieren"): trade_thesis_typ ist ein praeziseres Signal fuer
# die erwartete Haltedauer als der generische halte_kriterium_bucket -
# existiert nur bei Hebel (hebel_analyst.py, Werte einmal_trade/
# swing_strategie). 'einmal_trade' (kurzlebige Squeeze-Gegenbewegung)
# bekommt eine kuerzere Stunden-Schwelle statt der Tage-Bucket-Logik -
# deutlich ueber dem Hebel-Cooldown (3,5-7h), aber kurz genug fuer eine
# wirklich kurzlebige Gegenbewegungs-These. 'swing_strategie' faellt auf die
# normale Bucket-Logik zurueck (gleiche Werte wie Spot). Default, ueber
# config.yaml::backward_tracking.hebel_mindestbeobachtung_stunden_einmal_trade
# ueberschreibbar.
DEFAULT_HEBEL_MINDESTBEOBACHTUNG_STUNDEN_EINMAL_TRADE = 18

# ERÖFFNEN/NACHKAUFEN sind die einzigen Aktionen mit Entry/Stop-Pflicht + CRV>=2.0-
# Vorgabe (siehe hebel_analyst.py:25-28,67) - HEBEL_ERHÖHEN/HEBEL_SENKEN/TEILVERKAUF/
# SCHLIESSEN/HALTEN haben keine trackbare Entry-vs-Kurs-Semantik.
_TRACKABLE_HEBEL_ACTIONS = {"ERÖFFNEN", "NACHKAUFEN"}


@dataclass
class HebelBackwardTrackingResult:
    geprueft_count: int = 0
    resolved_take_profit: int = 0
    resolved_stop_loss: int = 0
    resolved_liquidation: int = 0
    expired: int = 0
    superseded: int = 0
    still_open: int = 0
    warnings: list[str] = field(default_factory=list)
    # Veto-Schatten-Tracking (2026-07-28, mirror backward_tracking.py::
    # BackwardTrackingResult - siehe check_hebel_signal_veto_shadow_outcome()).
    veto_schatten_geprueft_count: int = 0
    veto_schatten_take_profit: int = 0
    veto_schatten_stop_loss: int = 0
    veto_schatten_liquidation: int = 0
    veto_schatten_expired: int = 0
    veto_schatten_still_open: int = 0
    # Selbst-gewaehltes-HALTEN-Schatten-Tracking (2026-07-31, siehe
    # _hat_hebel_selbst_halten_these()-Docstring) - Gegenfall zum Veto-
    # Schatten oben: kein Gate/Veto, das LLM hat sich selbst gegen einen
    # Trade entschieden, aber trotzdem eine hypothetische Zone angegeben.
    selbst_halten_geprueft_count: int = 0
    selbst_halten_take_profit: int = 0
    selbst_halten_stop_loss: int = 0
    selbst_halten_liquidation: int = 0
    selbst_halten_expired: int = 0
    selbst_halten_still_open: int = 0


def _entry_mid(signal) -> float | None:
    von = signal.entry_usd_von
    bis = signal.entry_usd_bis
    if von is not None and bis is not None:
        return (von + bis) / 2
    return von


def _mittelwert(von: float | None, bis: float | None) -> float | None:
    """Mirror backward_tracking.py::_mittelwert() - HebelSignal hat keine
    Punktwert-Felder (immer mit Zonen eingefuehrt), deshalb kein Punktwert-
    Fallback-Parameter noetig."""
    if von is not None and bis is not None:
        return (von + bis) / 2
    return von


def _zonen_mittel(signal) -> tuple[float | None, float | None, float | None]:
    """Mirror backward_tracking.py::_zonen_mittel() - Grundlage fuer
    _ist_zonen_reaffirmation()."""
    return (
        _entry_mid(signal),
        _mittelwert(signal.stop_loss_usd_von, signal.stop_loss_usd_bis),
        _mittelwert(signal.take_profit_usd_von, signal.take_profit_usd_bis),
    )


def _ist_zonen_reaffirmation(signal, latest, toleranz_relativ: float) -> bool:
    """Mirror backward_tracking.py::_ist_zonen_reaffirmation() - siehe dort
    fuer die vollstaendige Begruendung. Konservativ: fehlt einer der drei
    Werte, gilt das NICHT als Reaffirmation."""
    paare = list(zip(_zonen_mittel(signal), _zonen_mittel(latest)))
    if any(a is None or b is None for a, b in paare):
        return False
    return all(abs(a - b) <= toleranz_relativ * abs(a) for a, b in paare if a)


def _parse_dt(ts: str) -> datetime:
    dt = datetime.fromisoformat(ts)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _mindestbeobachtung_erreicht(
    signal, latest, bucket_tage: dict[str, int], fallback_tage: int,
    einmal_trade_stunden: float = DEFAULT_HEBEL_MINDESTBEOBACHTUNG_STUNDEN_EINMAL_TRADE,
) -> bool:
    """Mirror backward_tracking.py::_mindestbeobachtung_erreicht(), PLUS
    Hebel-spezifischer Override: trade_thesis_typ == 'einmal_trade' nutzt
    `einmal_trade_stunden` statt der Tage-Bucket-Logik (siehe Konstanten-
    Docstring oben)."""
    alter = _parse_dt(latest.created_at) - _parse_dt(signal.created_at)
    if signal.trade_thesis_typ == "einmal_trade":
        return alter >= timedelta(hours=einmal_trade_stunden)
    bucket = signal.halte_kriterium_bucket
    mindest_tage = bucket_tage.get(bucket, fallback_tage) if bucket else fallback_tage
    return alter >= timedelta(days=mindest_tage)


def check_hebel_signal_outcome(
    conn, signal, watchlist, richtungstreffer_mindest_crv: float = DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
) -> tuple[str, dict]:
    """Prueft EIN Hebel-Signal gegen die seit signal.created_at vorliegende
    Kurshistorie - mirror check_signal_outcome() (backward_tracking.py:57-118),
    richtungsabhaengig. Gibt (neuer_status, extra_felder) zurueck, schreibt selbst
    nichts (Testbarkeit ohne DB-Mocking der Schreibpfade).

    Mindestziel/MFE-Tracking (2026-07-27, siehe backward_tracking.py::
    check_signal_outcome() Docstring fuer die volle Begruendung): laeuft
    richtungsabhaengig PARALLEL zur bestehenden TP/SL/Liquidation-Aufloesung mit -
    LONG: guenstigster Preis ist das Tages-High, SHORT: das Tages-Low."""
    if signal.action not in _TRACKABLE_HEBEL_ACTIONS:
        return OUTCOME_NICHT_ANWENDBAR, {}

    # Richtung ZUERST - die Zonenkante haengt daran (2026-08-09). Vorher standen
    # die beiden Schwellen oberhalb dieser Zeile und nahmen fuer BEIDE
    # Richtungen die `_von`-Kante. Bei SHORT ist das die falsche: der Stop liegt
    # ueber dem Einstieg, konservativ ist dort `_bis`. Das Gate rechnet seit
    # jeher mit `_bis` (_zonen_absolut), der Tracker rechnete mit `_von` -
    # dieselbe Position wurde also nach zwei verschiedenen Massstaeben
    # genehmigt und bewertet. Herleitung und Messwerte im Docstring von
    # backward_tracking._zonen_schwelle().
    #
    # Diese Datei traegt die Hauptlast des Defekts: 134 der 167 aufgeloesten
    # SHORT-Zeilen stehen in hebel_signals.
    ist_short = signal.richtung == "SHORT"

    take_profit_threshold = _zonen_schwelle(
        signal.take_profit_usd_von, signal.take_profit_usd_bis, None, ist_short)
    stop_loss_threshold = _zonen_schwelle(
        signal.stop_loss_usd_von, signal.stop_loss_usd_bis, None, ist_short)
    if take_profit_threshold is None or stop_loss_threshold is None:
        return OUTCOME_NICHT_ANWENDBAR, {}

    liquidation_threshold = signal.liquidationspreis_geschaetzt_usd

    asset = next((a for a in watchlist if a.symbol == signal.symbol), None)
    if asset is None:
        return OUTCOME_OFFEN, {}

    min_date = signal.created_at[:10]
    entry_mid = _entry_mid(signal)
    if entry_mid is not None:
        risiko_distanz = (stop_loss_threshold - entry_mid) if ist_short else (entry_mid - stop_loss_threshold)
    else:
        risiko_distanz = None

    max_favorable_crv = None
    mindestziel_erreicht_am = None

    def _erfasse_mfe(high: float, low: float, day_value: str) -> None:
        nonlocal max_favorable_crv, mindestziel_erreicht_am
        if risiko_distanz is None or risiko_distanz <= 0:
            return
        guenstigster_preis = low if ist_short else high
        favorable_crv = (
            (entry_mid - guenstigster_preis) / risiko_distanz if ist_short
            else (guenstigster_preis - entry_mid) / risiko_distanz
        )
        if max_favorable_crv is None or favorable_crv > max_favorable_crv:
            max_favorable_crv = favorable_crv
        if mindestziel_erreicht_am is None and favorable_crv >= richtungstreffer_mindest_crv:
            mindestziel_erreicht_am = day_value

    def resolve(exit_price: float, status: str) -> tuple[str, dict]:
        realized_crv = None
        if entry_mid is not None:
            if ist_short:
                risiko_distanz_lokal = stop_loss_threshold - entry_mid
                if risiko_distanz_lokal != 0:
                    realized_crv = (entry_mid - exit_price) / risiko_distanz_lokal
            else:
                risiko_distanz_lokal = entry_mid - stop_loss_threshold
                if risiko_distanz_lokal != 0:
                    realized_crv = (exit_price - entry_mid) / risiko_distanz_lokal
        return status, {
            "entschieden_am": day,
            "realisiertes_crv": realized_crv,
            "datenquelle": datenquelle,
            "max_realisiertes_crv": max_favorable_crv,
            "mindestziel_erreicht_am": mindestziel_erreicht_am,
        }

    def _check_day(high: float, low: float, day_value: str,
                   open_preis: float | None = None) -> tuple[str, dict] | None:
        nonlocal day
        day = day_value
        _erfasse_mfe(high, low, day_value)
        if ist_short:
            hit_liquidation = liquidation_threshold is not None and high >= liquidation_threshold
            hit_stop = high >= stop_loss_threshold
            hit_take = low <= take_profit_threshold
        else:
            hit_liquidation = liquidation_threshold is not None and low <= liquidation_threshold
            hit_stop = low <= stop_loss_threshold
            hit_take = high >= take_profit_threshold

        # Konservativste Annahme zuerst: Liquidation vor Stop-Loss vor Take-Profit.
        if hit_liquidation:
            return resolve(gap_bewusster_fill(
                liquidation_threshold, open_preis, ist_stop=True, ist_short=ist_short,
            ), OUTCOME_LIQUIDATION)
        if hit_stop:
            return resolve(gap_bewusster_fill(
                stop_loss_threshold, open_preis, ist_stop=True, ist_short=ist_short,
            ), OUTCOME_STOP_LOSS)
        if hit_take:
            return resolve(gap_bewusster_fill(
                take_profit_threshold, open_preis, ist_stop=False, ist_short=ist_short,
            ), OUTCOME_TAKE_PROFIT)
        return None

    day = None
    ohlc_rows = db.get_ohlc_history(conn, signal.symbol, "USD", min_date=min_date)
    if len(ohlc_rows) >= 1:
        datenquelle = "real"
        for row in ohlc_rows:
            result = _check_day(row.high, row.low, row.date, row.open)
            if result is not None:
                return result
    else:
        datenquelle = "proxy"
        price_rows = db.get_price_history(conn, asset.coingecko_id, min_date=min_date) if asset.coingecko_id else []
        for row in price_rows:
            if row.price_usd is None:
                continue
            result = _check_day(row.price_usd, row.price_usd, row.date)
            if result is not None:
                return result

    return OUTCOME_OFFEN, {
        "max_realisiertes_crv": max_favorable_crv,
        "mindestziel_erreicht_am": mindestziel_erreicht_am,
    }


def _hat_hebel_veto_schatten_these(signal) -> bool:
    """Diskriminator fuer einen echten Hebel-Veto-Schatten-Kandidaten (2026-07-28,
    mirror backward_tracking.py::_hat_veto_schatten_these()): `risk_veto=True`
    UND `action="HALTEN"` (per Veto zurueckgestuft, z.B. Nur-Long-Deckel, CRV-
    Veto, Regime-Konflikt-Deckel, Retail-Konsens-Deckel - siehe hebel_risk_gate.py::
    post_check_hebel()) UND alle drei Preiszonen gesetzt. Ein regelkonformes,
    selbst gewaehltes HALTEN OHNE Zonen faellt automatisch durch.

    Nachtrag 2026-07-31 (Kontrapruefung nach der Selbst-Halten-Schatten-
    Erweiterung, echter Fund): zusaetzlich `original_action != "HALTEN"`
    verlangt. Grund: `post_check_hebel()`s AZ-7/krise_extrem-Deckel
    (`if not pre_result.hebel_erlaubt:`) ist UNBEDINGT - setzt `risk_veto=True`
    unabhaengig davon, was das LLM urspruenglich entschied. War die Aktion
    schon VORHER selbst gewaehltes HALTEN (das dank Regel 28 jetzt ebenfalls
    hypothetische Zonen traegt), landete dieser Fall bisher faelschlich hier
    im Veto-Schatten-Topf, obwohl nie ein Trade vorgeschlagen wurde. Alte
    Zeilen ohne `original_action` (vor dieser Migration) bleiben unveraendert
    erfasst (`None != "HALTEN"` ist True) - keine rueckwirkende Aenderung
    bereits aufgeloester Faelle."""
    if not (getattr(signal, "risk_veto", False) and signal.action == "HALTEN"):
        return False
    if getattr(signal, "original_action", None) == "HALTEN":
        return False
    return (
        signal.entry_usd_von is not None
        and signal.stop_loss_usd_von is not None
        and signal.take_profit_usd_von is not None
    )


def _hat_hebel_selbst_halten_these(signal) -> bool:
    """Diskriminator fuer einen echten Hebel-Selbst-Halten-Schatten-
    Kandidaten (2026-07-31, Ergaenzung zu _hat_hebel_veto_schatten_these()
    oben - siehe dortigen Docstring fuer den Gegenfall): `ist_reines_llm_
    halten == True` (bereits deterministisch bei der Generierung berechnet,
    siehe hebel_risk_gate.py::post_check_hebel()) UND alle drei Preiszonen
    gesetzt. Bewusst KEIN Ruecklesen von risk_veto/action hier - das Flag
    existiert genau deshalb, um den Kontrathese-Uebersetzungs-Fallstrick zu
    vermeiden (siehe HebelSignal.ist_reines_llm_halten-Docstring)."""
    if not getattr(signal, "ist_reines_llm_halten", False):
        return False
    return (
        signal.entry_usd_von is not None
        and signal.stop_loss_usd_von is not None
        and signal.take_profit_usd_von is not None
    )


def check_hebel_signal_selbst_halten_outcome(
    conn, signal, watchlist, richtungstreffer_mindest_crv: float = DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
) -> tuple[str, dict]:
    """Wie check_hebel_signal_veto_shadow_outcome(), aber fuer den Zweig
    "selbst gewaehltes HALTEN" (2026-07-31) - identische TP/SL/Liquidation/
    MFE-Mechanik, liest/schreibt nur die selbst_halten_outcome_*-Spalten
    statt veto_outcome_*. `signal.richtung` bleibt bei einem genuinen self-
    chosen HALTEN vom LLM unveraendert gesetzt - keine Zonen-Richtungs-
    Ableitung noetig (wie beim Veto-Schatten-Zweig).

    Gibt (neuer_status, extra_felder) zurueck, extra_felder passend fuer
    db.update_hebel_signal_selbst_halten_outcome(**extra_felder)."""
    if not _hat_hebel_selbst_halten_these(signal):
        return OUTCOME_NICHT_ANWENDBAR, {}

    # Richtung zuerst, dann die Kante - siehe check_hebel_signal_outcome()
    # und backward_tracking._zonen_schwelle().
    ist_short = signal.richtung == "SHORT"
    take_profit_threshold = _zonen_schwelle(
        signal.take_profit_usd_von, signal.take_profit_usd_bis, None, ist_short)
    stop_loss_threshold = _zonen_schwelle(
        signal.stop_loss_usd_von, signal.stop_loss_usd_bis, None, ist_short)
    liquidation_threshold = signal.liquidationspreis_geschaetzt_usd

    asset = next((a for a in watchlist if a.symbol == signal.symbol), None)
    if asset is None:
        return OUTCOME_OFFEN, {}

    min_date = signal.created_at[:10]
    entry_mid = _entry_mid(signal)
    if entry_mid is not None:
        risiko_distanz = (stop_loss_threshold - entry_mid) if ist_short else (entry_mid - stop_loss_threshold)
    else:
        risiko_distanz = None

    max_favorable_crv = None
    mindestziel_erreicht_am = None

    def _erfasse_mfe(high: float, low: float, day_value: str) -> None:
        nonlocal max_favorable_crv, mindestziel_erreicht_am
        if risiko_distanz is None or risiko_distanz <= 0:
            return
        guenstigster_preis = low if ist_short else high
        favorable_crv = (
            (entry_mid - guenstigster_preis) / risiko_distanz if ist_short
            else (guenstigster_preis - entry_mid) / risiko_distanz
        )
        if max_favorable_crv is None or favorable_crv > max_favorable_crv:
            max_favorable_crv = favorable_crv
        if mindestziel_erreicht_am is None and favorable_crv >= richtungstreffer_mindest_crv:
            mindestziel_erreicht_am = day_value

    def resolve(exit_price: float, status: str) -> tuple[str, dict]:
        realized_crv = None
        if entry_mid is not None:
            if ist_short:
                risiko_distanz_lokal = stop_loss_threshold - entry_mid
                if risiko_distanz_lokal != 0:
                    realized_crv = (entry_mid - exit_price) / risiko_distanz_lokal
            else:
                risiko_distanz_lokal = entry_mid - stop_loss_threshold
                if risiko_distanz_lokal != 0:
                    realized_crv = (exit_price - entry_mid) / risiko_distanz_lokal
        return status, {
            "entschieden_am": day,
            "realisiertes_crv": realized_crv,
            "max_realisiertes_crv": max_favorable_crv,
            "mindestziel_erreicht_am": mindestziel_erreicht_am,
        }

    def _check_day(high: float, low: float, day_value: str,
                   open_preis: float | None = None) -> tuple[str, dict] | None:
        nonlocal day
        day = day_value
        _erfasse_mfe(high, low, day_value)
        if ist_short:
            hit_liquidation = liquidation_threshold is not None and high >= liquidation_threshold
            hit_stop = high >= stop_loss_threshold
            hit_take = low <= take_profit_threshold
        else:
            hit_liquidation = liquidation_threshold is not None and low <= liquidation_threshold
            hit_stop = low <= stop_loss_threshold
            hit_take = high >= take_profit_threshold

        if hit_liquidation:
            return resolve(gap_bewusster_fill(
                liquidation_threshold, open_preis, ist_stop=True, ist_short=ist_short,
            ), OUTCOME_LIQUIDATION)
        if hit_stop:
            return resolve(gap_bewusster_fill(
                stop_loss_threshold, open_preis, ist_stop=True, ist_short=ist_short,
            ), OUTCOME_STOP_LOSS)
        if hit_take:
            return resolve(gap_bewusster_fill(
                take_profit_threshold, open_preis, ist_stop=False, ist_short=ist_short,
            ), OUTCOME_TAKE_PROFIT)
        return None

    day = None
    ohlc_rows = db.get_ohlc_history(conn, signal.symbol, "USD", min_date=min_date)
    if len(ohlc_rows) >= 1:
        for row in ohlc_rows:
            result = _check_day(row.high, row.low, row.date, row.open)
            if result is not None:
                return result
    else:
        price_rows = db.get_price_history(conn, asset.coingecko_id, min_date=min_date) if asset.coingecko_id else []
        for row in price_rows:
            if row.price_usd is None:
                continue
            result = _check_day(row.price_usd, row.price_usd, row.date)
            if result is not None:
                return result

    return OUTCOME_OFFEN, {
        "max_realisiertes_crv": max_favorable_crv,
        "mindestziel_erreicht_am": mindestziel_erreicht_am,
    }


def check_hebel_signal_veto_shadow_outcome(
    conn, signal, watchlist, richtungstreffer_mindest_crv: float = DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
) -> tuple[str, dict]:
    """Wie check_hebel_signal_outcome(), aber fuer den Veto-Schatten-Zweig
    (2026-07-28, mirror backward_tracking.py::check_signal_veto_shadow_outcome()
    - siehe dort fuer die volle Herleitung dieses Features). Trackt Hebel-
    Signale, deren Action durch einen Risk-Gate-Veto auf HALTEN zurueckgestuft
    wurde, OBWOHL das LLM urspruenglich ERÖFFNEN/NACHKAUFEN vorgeschlagen hatte.

    Anders als beim Spot-Pendant (dort muss die Richtung aus der Zonen-
    Reihenfolge abgeleitet werden) bleibt `signal.richtung` (LONG/SHORT) hier
    vom Veto unberuehrt - nur `action`/`risk_veto`/`risk_veto_reason` werden
    ueberschrieben (siehe hebel_risk_gate.py::post_check_hebel()) - deshalb
    exakt dieselbe ist_short-Ableitung wie im Nicht-Schatten-Zweig.

    Liquidationspreis-Pruefung bewusst BEIBEHALTEN (nicht weggelassen): auch
    fuer eine nie eroeffnete Position ist informativ, ob der geschaetzte
    Liquidationspreis vor Stop-Loss/Take-Profit erreicht worden waere - zeigt,
    wie riskant der vetote Vorschlag tatsaechlich war.

    Gibt (neuer_status, extra_felder) zurueck, extra_felder passend fuer
    db.update_hebel_signal_veto_shadow_outcome(**extra_felder) (bewusst OHNE
    'datenquelle'-Key, siehe database/db.py::_HEBEL_SIGNAL_VETO_SHADOW_NEW_
    COLUMNS-Docstring)."""
    if not _hat_hebel_veto_schatten_these(signal):
        return OUTCOME_NICHT_ANWENDBAR, {}

    # Richtung zuerst, dann die Kante - siehe check_hebel_signal_outcome()
    # und backward_tracking._zonen_schwelle().
    ist_short = signal.richtung == "SHORT"
    take_profit_threshold = _zonen_schwelle(
        signal.take_profit_usd_von, signal.take_profit_usd_bis, None, ist_short)
    stop_loss_threshold = _zonen_schwelle(
        signal.stop_loss_usd_von, signal.stop_loss_usd_bis, None, ist_short)
    liquidation_threshold = signal.liquidationspreis_geschaetzt_usd

    asset = next((a for a in watchlist if a.symbol == signal.symbol), None)
    if asset is None:
        return OUTCOME_OFFEN, {}

    min_date = signal.created_at[:10]
    entry_mid = _entry_mid(signal)
    if entry_mid is not None:
        risiko_distanz = (stop_loss_threshold - entry_mid) if ist_short else (entry_mid - stop_loss_threshold)
    else:
        risiko_distanz = None

    max_favorable_crv = None
    mindestziel_erreicht_am = None

    def _erfasse_mfe(high: float, low: float, day_value: str) -> None:
        nonlocal max_favorable_crv, mindestziel_erreicht_am
        if risiko_distanz is None or risiko_distanz <= 0:
            return
        guenstigster_preis = low if ist_short else high
        favorable_crv = (
            (entry_mid - guenstigster_preis) / risiko_distanz if ist_short
            else (guenstigster_preis - entry_mid) / risiko_distanz
        )
        if max_favorable_crv is None or favorable_crv > max_favorable_crv:
            max_favorable_crv = favorable_crv
        if mindestziel_erreicht_am is None and favorable_crv >= richtungstreffer_mindest_crv:
            mindestziel_erreicht_am = day_value

    def resolve(exit_price: float, status: str) -> tuple[str, dict]:
        realized_crv = None
        if entry_mid is not None:
            if ist_short:
                risiko_distanz_lokal = stop_loss_threshold - entry_mid
                if risiko_distanz_lokal != 0:
                    realized_crv = (entry_mid - exit_price) / risiko_distanz_lokal
            else:
                risiko_distanz_lokal = entry_mid - stop_loss_threshold
                if risiko_distanz_lokal != 0:
                    realized_crv = (exit_price - entry_mid) / risiko_distanz_lokal
        return status, {
            "entschieden_am": day,
            "realisiertes_crv": realized_crv,
            "max_realisiertes_crv": max_favorable_crv,
            "mindestziel_erreicht_am": mindestziel_erreicht_am,
        }

    def _check_day(high: float, low: float, day_value: str,
                   open_preis: float | None = None) -> tuple[str, dict] | None:
        nonlocal day
        day = day_value
        _erfasse_mfe(high, low, day_value)
        if ist_short:
            hit_liquidation = liquidation_threshold is not None and high >= liquidation_threshold
            hit_stop = high >= stop_loss_threshold
            hit_take = low <= take_profit_threshold
        else:
            hit_liquidation = liquidation_threshold is not None and low <= liquidation_threshold
            hit_stop = low <= stop_loss_threshold
            hit_take = high >= take_profit_threshold

        if hit_liquidation:
            return resolve(gap_bewusster_fill(
                liquidation_threshold, open_preis, ist_stop=True, ist_short=ist_short,
            ), OUTCOME_LIQUIDATION)
        if hit_stop:
            return resolve(gap_bewusster_fill(
                stop_loss_threshold, open_preis, ist_stop=True, ist_short=ist_short,
            ), OUTCOME_STOP_LOSS)
        if hit_take:
            return resolve(gap_bewusster_fill(
                take_profit_threshold, open_preis, ist_stop=False, ist_short=ist_short,
            ), OUTCOME_TAKE_PROFIT)
        return None

    day = None
    ohlc_rows = db.get_ohlc_history(conn, signal.symbol, "USD", min_date=min_date)
    if len(ohlc_rows) >= 1:
        for row in ohlc_rows:
            result = _check_day(row.high, row.low, row.date, row.open)
            if result is not None:
                return result
    else:
        price_rows = db.get_price_history(conn, asset.coingecko_id, min_date=min_date) if asset.coingecko_id else []
        for row in price_rows:
            if row.price_usd is None:
                continue
            result = _check_day(row.price_usd, row.price_usd, row.date)
            if result is not None:
                return result

    return OUTCOME_OFFEN, {
        "max_realisiertes_crv": max_favorable_crv,
        "mindestziel_erreicht_am": mindestziel_erreicht_am,
    }


def _is_superseded(
    signal, latest_real: dict, mindestbeob_bucket: dict[str, int],
    mindestbeob_fallback: int, zonen_toleranz_relativ: float,
    einmal_trade_stunden: float = DEFAULT_HEBEL_MINDESTBEOBACHTUNG_STUNDEN_EINMAL_TRADE,
) -> bool:
    """Mirror backward_tracking.py::_is_superseded(), aber nach (symbol,
    richtung) geschluesselt - ein LONG- und ein SHORT-Signal fuer denselben
    Coin sind unabhaengige Thesen, eines ueberholt das andere nicht (das
    heisst: JEDE Ueberholung hier ist strukturell bereits ein "gleiche
    Richtung, neue/erneute These"-Fall - eine echte Gegenrichtung wie bei
    Spot VERKAUFEN/TAUSCHEN gibt es unter diesem Schluessel nicht, sie liefe
    ueber den jeweils anderen (symbol, richtung)-Schluessel).

    NACHTRAG (2026-07-19, Backtracking-Aussagekraft-Audit, siehe dortiger
    Docstring): eine reine HALTEN-Bestaetigung ueberholt die offene
    ERÖFFNEN-These nicht mehr - live geprueft, dass 60% der offenen Hebel-
    Signale unter der alten Regel nach durchschnittlich 11,7 Std. ueberholt
    wurden (hebel_position_cooldown_stunden=3), bevor der Kurs ueberhaupt
    eine faire Chance hatte, Take-Profit/Stop-Loss zu erreichen.

    NACHTRAG 2 (2026-07-22, siehe backward_tracking.py::_is_superseded()
    NACHTRAG 2 fuer die vollstaendige Begruendung/Backtest-Zahlen): ein
    erneutes ERÖFFNEN ueberholt jetzt nur noch, wenn zwei zusaetzliche Gates
    erfuellt sind - Mindestbeobachtung erreicht (inkl. trade_thesis_typ-
    Override) UND keine Zonen-Reaffirmation. Backtest gegen echte Notebook-
    Daten: 24 von 27 (89%) historisch ueberholten Hebel-Signalen waeren
    unter diesen Gates gerettet worden, darunter mind. 4 mit einem echten
    TP/SL-Ergebnis statt spurlosem Verschwinden.

    NACHTRAG 3 (2026-07-24, Nutzer-Nachfrage "wirkt sich die Kontrathese-
    Uebersetzung negativ auf das Backward-Tracking aus?"): ist `latest`
    ein `kontrathese_zu_position`-Signal (SCHLIESSEN/TEILVERKAUF, siehe
    hebel_risk_gate.py::post_check_hebel()), wird das Zonen-Reaffirmation-
    Gate bewusst UEBERSPRUNGEN - seine Entry-/Stop-Loss-/Take-Profit-Felder
    stammen unveraendert aus dem ORIGINAL-LLM-Vorschlag fuer die (nie
    ausgefuehrte) Gegenrichtung, nicht aus der bestehenden Position, und
    sind deshalb mit `signal`s echten Zonen nicht sinnvoll vergleichbar -
    ein zufaelliger Zahlenabgleich waere weder eine echte Reaffirmation
    noch ein echter Widerspruch, sondern bedeutungslos. Ein bestaetigtes
    SCHLIESSEN/TEILVERKAUF ist inhaltlich immer eine echte neue Information
    ueber die bestehende Position - das Mindestbeobachtung-Gate bleibt
    trotzdem in Kraft (schuetzt weiterhin vor einer zu fruehen Ueberholung
    eines gerade erst eroeffneten Signals).

    Rein deterministischer Datums-/ID-/Aktions-/Zonen-Vergleich, KEIN
    LLM-Call."""
    latest = latest_real.get((signal.symbol, signal.richtung))
    if latest is None or latest.id == signal.id or latest.created_at <= signal.created_at:
        return False
    if latest.action == "HALTEN":
        return False
    if not _mindestbeobachtung_erreicht(
        signal, latest, mindestbeob_bucket, mindestbeob_fallback, einmal_trade_stunden,
    ):
        return False
    if not getattr(latest, "kontrathese_zu_position", False) and _ist_zonen_reaffirmation(
        signal, latest, zonen_toleranz_relativ,
    ):
        return False
    return True


def _is_expired(signal, bucket_tage: dict[str, int], fallback_tage: int) -> bool:
    """Mirror backward_tracking.py::_is_expired() - inhaltsbasierte Ablaufzeit
    aus halte_kriterium statt einer fixen Frist fuer alle Hebel-Signale."""
    created = datetime.fromisoformat(signal.created_at)
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)

    ziel_datum = getattr(signal, "halte_kriterium_ziel_datum", None)
    if ziel_datum:
        try:
            deadline = datetime.fromisoformat(ziel_datum)
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=timezone.utc)
            return now > deadline
        except ValueError:
            pass

    bucket = getattr(signal, "halte_kriterium_bucket", None)
    tage = bucket_tage.get(bucket, fallback_tage) if bucket else fallback_tage
    age_days = (now - created).days
    return age_days >= tage


def run_hebel_backward_tracking(conn, watchlist, config: dict) -> HebelBackwardTrackingResult:
    """Mirror run_backward_tracking() (backward_tracking.py:131-178) - holt alle
    hebel_signals mit outcome_status IN (NULL, 'offen'), prueft jedes, schreibt nur
    bei tatsaechlicher Statusaenderung. Nutzt dieselbe abgelaufen_nach_tagen-
    Konfiguration wie Spot (config['backward_tracking']) - kein separater Wert noetig,
    gleiche Ablauf-Logik."""
    result = HebelBackwardTrackingResult()
    bt_cfg = config.get("backward_tracking", {})
    bucket_tage = bt_cfg.get("abgelaufen_nach_tagen_bucket", DEFAULT_ABGELAUFEN_TAGE_BUCKET)
    fallback_tage = bt_cfg.get("abgelaufen_nach_tagen_fallback", DEFAULT_ABGELAUFEN_TAGE_FALLBACK)
    mindestbeob_bucket = bt_cfg.get("mindestbeobachtung_tage_bucket", DEFAULT_MINDESTBEOBACHTUNG_TAGE_BUCKET)
    mindestbeob_fallback = bt_cfg.get("mindestbeobachtung_tage_fallback", DEFAULT_MINDESTBEOBACHTUNG_TAGE_FALLBACK)
    zonen_toleranz = bt_cfg.get(
        "zonen_reaffirmation_toleranz_relativ", DEFAULT_ZONEN_REAFFIRMATION_TOLERANZ_RELATIV,
    )
    einmal_trade_stunden = bt_cfg.get(
        "hebel_mindestbeobachtung_stunden_einmal_trade", DEFAULT_HEBEL_MINDESTBEOBACHTUNG_STUNDEN_EINMAL_TRADE,
    )
    richtungstreffer_mindest_crv = bt_cfg.get(
        "richtungstreffer_mindest_crv", DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    )
    latest_real = db.get_latest_hebel_signal_per_symbol_and_richtung(conn)

    rows = conn.execute(
        "SELECT id FROM hebel_signals WHERE outcome_status IS NULL OR outcome_status = ?",
        (OUTCOME_OFFEN,),
    ).fetchall()

    for row in rows:
        signal = db.get_hebel_signal_by_id(conn, row["id"])
        if signal is None:
            continue
        result.geprueft_count += 1

        status, extra = check_hebel_signal_outcome(conn, signal, watchlist, richtungstreffer_mindest_crv)

        if status == OUTCOME_NICHT_ANWENDBAR:
            db.update_hebel_signal_outcome(conn, signal.id, status)
            continue

        if status in (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS, OUTCOME_LIQUIDATION):
            db.update_hebel_signal_outcome(
                conn, signal.id, status,
                entschieden_am=extra.get("entschieden_am"),
                realisiertes_crv=extra.get("realisiertes_crv"),
                datenquelle=extra.get("datenquelle"),
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            if status == OUTCOME_TAKE_PROFIT:
                result.resolved_take_profit += 1
            elif status == OUTCOME_STOP_LOSS:
                result.resolved_stop_loss += 1
            else:
                result.resolved_liquidation += 1
            continue

        # status == OUTCOME_OFFEN: erst Ueberholt-Check, dann Ablauf-Check.
        if _is_superseded(
            signal, latest_real, mindestbeob_bucket, mindestbeob_fallback, zonen_toleranz, einmal_trade_stunden,
        ):
            db.update_hebel_signal_outcome(
                conn, signal.id, OUTCOME_UEBERHOLT,
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            result.superseded += 1
        elif _is_expired(signal, bucket_tage, fallback_tage):
            db.update_hebel_signal_outcome(
                conn, signal.id, OUTCOME_ABGELAUFEN,
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            result.expired += 1
        else:
            persistiere_offenes_mfe(
                conn, signal.id, extra, signal.outcome_max_realisiertes_crv,
                db.update_hebel_signal_outcome,
            )
            result.still_open += 1

    # Veto-Schatten-Zweig (2026-07-28, mirror backward_tracking.py::
    # run_backward_tracking() - siehe check_hebel_signal_veto_shadow_outcome()-
    # Docstring). Bewusst OHNE Ueberholt-Check, gleiche Begruendung wie beim
    # Spot-Pendant: eine hypothetische, nie eroeffnete Position kann durch eine
    # neuere echte Analyse nicht im selben Sinn "ueberholt" werden.
    veto_shadow_rows = conn.execute(
        "SELECT id FROM hebel_signals WHERE risk_veto = 1 AND action = 'HALTEN' "
        "AND (veto_outcome_status IS NULL OR veto_outcome_status = ?)",
        (OUTCOME_OFFEN,),
    ).fetchall()

    for row in veto_shadow_rows:
        signal = db.get_hebel_signal_by_id(conn, row["id"])
        if signal is None:
            continue
        result.veto_schatten_geprueft_count += 1

        status, extra = check_hebel_signal_veto_shadow_outcome(conn, signal, watchlist, richtungstreffer_mindest_crv)

        if status == OUTCOME_NICHT_ANWENDBAR:
            db.update_hebel_signal_veto_shadow_outcome(conn, signal.id, status)
            continue

        if status in (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS, OUTCOME_LIQUIDATION):
            db.update_hebel_signal_veto_shadow_outcome(
                conn, signal.id, status,
                entschieden_am=extra.get("entschieden_am"),
                realisiertes_crv=extra.get("realisiertes_crv"),
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            if status == OUTCOME_TAKE_PROFIT:
                result.veto_schatten_take_profit += 1
            elif status == OUTCOME_STOP_LOSS:
                result.veto_schatten_stop_loss += 1
            else:
                result.veto_schatten_liquidation += 1
            continue

        if _is_expired(signal, bucket_tage, fallback_tage):
            db.update_hebel_signal_veto_shadow_outcome(
                conn, signal.id, OUTCOME_ABGELAUFEN,
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            result.veto_schatten_expired += 1
        else:
            persistiere_offenes_mfe(
                conn, signal.id, extra, signal.veto_outcome_max_realisiertes_crv,
                db.update_hebel_signal_veto_shadow_outcome,
            )
            result.veto_schatten_still_open += 1

    # Selbst-gewaehltes-HALTEN-Zweig (2026-07-31, Gegenfall zum Veto-Schatten-
    # Zweig oben - siehe check_hebel_signal_selbst_halten_outcome()-Docstring).
    # Bewusst OHNE Ueberholt-Check, gleiche Begruendung wie beim Veto-Schatten-
    # Zweig: eine hypothetische, nie eroeffnete Position kann durch eine
    # neuere echte Analyse nicht im selben Sinn "ueberholt" werden.
    selbst_halten_rows = conn.execute(
        "SELECT id FROM hebel_signals WHERE ist_reines_llm_halten = 1 "
        "AND (selbst_halten_outcome_status IS NULL OR selbst_halten_outcome_status = ?)",
        (OUTCOME_OFFEN,),
    ).fetchall()

    for row in selbst_halten_rows:
        signal = db.get_hebel_signal_by_id(conn, row["id"])
        if signal is None:
            continue
        result.selbst_halten_geprueft_count += 1

        status, extra = check_hebel_signal_selbst_halten_outcome(conn, signal, watchlist, richtungstreffer_mindest_crv)

        if status == OUTCOME_NICHT_ANWENDBAR:
            db.update_hebel_signal_selbst_halten_outcome(conn, signal.id, status)
            continue

        if status in (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS, OUTCOME_LIQUIDATION):
            db.update_hebel_signal_selbst_halten_outcome(
                conn, signal.id, status,
                entschieden_am=extra.get("entschieden_am"),
                realisiertes_crv=extra.get("realisiertes_crv"),
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            if status == OUTCOME_TAKE_PROFIT:
                result.selbst_halten_take_profit += 1
            elif status == OUTCOME_STOP_LOSS:
                result.selbst_halten_stop_loss += 1
            else:
                result.selbst_halten_liquidation += 1
            continue

        if _is_expired(signal, bucket_tage, fallback_tage):
            db.update_hebel_signal_selbst_halten_outcome(
                conn, signal.id, OUTCOME_ABGELAUFEN,
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            result.selbst_halten_expired += 1
        else:
            persistiere_offenes_mfe(
                conn, signal.id, extra, signal.selbst_halten_outcome_max_realisiertes_crv,
                db.update_hebel_signal_selbst_halten_outcome,
            )
            result.selbst_halten_still_open += 1

    return result
