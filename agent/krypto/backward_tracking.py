"""Backward-Tracking (2026-07-10, Selbstverifikations-Vision Schritt 2 - siehe
Basisinfos/Regelwerksmanual.md Kap. 9 / Basisinfos/Spezifikation.md Kap. 16). Prueft
vergangene KAUFEN/NACHKAUFEN-Signale gegen die seit ihrer Erstellung tatsaechlich
eingetretene Kurshistorie: wurde die Take-Profit-Zone erreicht (Erfolg) oder die
Stop-Loss-Zone (Fehlschlag)? Rein beobachtend (P-7 Advisory-only) - liest nur
bereits vorhandene Preis-/OHLC-Daten, schreibt ausschliesslich einen Ergebnis-Status
je Signal zurueck. Keine neue Empfehlung, kein Veto, keine Positions-Aenderung.

Datengrundlage fuer die spaeteren Schritte 3+4 der Selbstverifikations-Vision
(KI-gestuetzte Regel-Trimm-Vorschlaege, manuelle Pruefzyklen) - ohne gespeicherte
Ist-Ergebnisse kann nichts verglichen werden."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import database.db as db
from agent.krypto.llm_provider import provider_from_label
from agent.krypto.risk_gate import KONFIDENZ_SCHWELLE_HOCH, KONFIDENZ_SCHWELLE_NIEDRIG

OUTCOME_OFFEN = "offen"
OUTCOME_TAKE_PROFIT = "take_profit_erreicht"
OUTCOME_STOP_LOSS = "stop_loss_erreicht"
OUTCOME_ABGELAUFEN = "abgelaufen_unentschieden"
OUTCOME_NICHT_ANWENDBAR = "nicht_anwendbar"
# Aktive Ueberholt-Erkennung (2026-07-16, Nutzer-Wunsch: "redundante bzw.
# gegensaetzliche Empfehlungen muessen rausfallen") - siehe _is_superseded().
# Rein deterministischer Datumsvergleich, KEIN LLM-Call.
OUTCOME_UEBERHOLT = "ueberholt_durch_neuere_analyse"
# Nur fuer hebel_signals relevant (siehe agent/krypto/hebel_backward_tracking.py),
# hier definiert statt dort, um einen Kreisimport zu vermeiden (hebel_backward_
# tracking.py importiert die OUTCOME_*-Konstanten bereits von hier).
OUTCOME_LIQUIDATION = "liquidation_wahrscheinlich"

# Trackbare Aktionen (2026-07-27, Nutzer-Wunsch "auch auf sinkende Short-Kurse
# tracken, damit es vollstaendig ist fuer alle Assets - fuer ZAI und Mistral"):
# VERKAUFEN/TAUSCHEN NACHTRAEGLICH ergaenzt - vorher nur KAUFEN/NACHKAUFEN, weil
# Entry/Stop-Loss/Take-Profit erst seit der gespiegelten Regel-3/Regel-16-
# Erweiterung (agent/krypto/analyst.py + 3 weitere Spot-family-Analysten,
# NICHT agent/hedge/analyst.py - siehe dortige Regel 9, Hedge hat bewusst KEINE
# CRV-Pflicht/Zonen-Richtungs-Garantie fuer irgendeine Richtung) zuverlaessig
# bearisch orientiert sind (Take-Profit UNTER, Stop-Loss UEBER dem Entry).
# HALTEN bleibt weiterhin nicht trackbar (keine Handlung, keine Zonen-These).
_TRACKABLE_ACTIONS = {"KAUFEN", "NACHKAUFEN", "VERKAUFEN", "TAUSCHEN"}

# Inhaltsbasierte Ablaufzeit (2026-07-19, Backtracking-Aussagekraft-Audit -
# Nutzer-Wunsch: "der zeitliche Faktor sollte durch den Inhalt bzw. Angabe -
# wann soll ein Zielwert erreicht werden - besser abschaetzbar sein"). Nutzt
# das vom Modell BEREITS zuverlaessig gefuellte halte_kriterium.bucket
# (Regel 17 in analyst.py, live verifiziert: 100% Abdeckung bei allen
# KAUFEN/NACHKAUFEN-Signalen, waehrend ziel_datum in der Praxis fast nie
# gesetzt wird) statt einer einzigen fixen Frist fuer JEDES Signal. Werte
# selbst [OFFEN]/vorlaeufig (noch nicht gegen echte Ergebnisse kalibriert,
# siehe Regelwerksmanual Kap. 15).
DEFAULT_ABGELAUFEN_TAGE_BUCKET = {"kurz": 14, "mittel": 45, "lang": 120}
DEFAULT_ABGELAUFEN_TAGE_FALLBACK = 90

# Mindestbeobachtung + Zonen-Reaffirmation (2026-07-22, Nutzer-Frage "funktioniert
# das System auf Glueck?" - siehe Plan-Datei "Ueberholt-Erkennung reparieren").
# Backtest gegen echte Notebook-Daten (backtest_ueberholt_erkennung.py) zeigte:
# 24 von 27 historisch ueberholten Hebel-Signalen (89%) haetten unter diesen
# beiden zusaetzlichen Gates weiter offen bleiben sollen - darunter mind. 4, die
# seither TATSAECHLICH Take-Profit/Stop-Loss erreicht haetten, aber durch die
# alte, zeit-/inhaltsblinde Ueberholt-Erkennung spurlos verschwanden. Deutlich
# unter den bestehenden Abgelaufen-Schwellen (14/45/120/90 Tage) - es bleibt
# immer ein Fenster, in dem ein Signal weder zu jung fuer eine Ueberholung noch
# bereits abgelaufen ist.
DEFAULT_MINDESTBEOBACHTUNG_TAGE_BUCKET = {"kurz": 2, "mittel": 5, "lang": 10}
DEFAULT_MINDESTBEOBACHTUNG_TAGE_FALLBACK = 3
DEFAULT_ZONEN_REAFFIRMATION_TOLERANZ_RELATIV = 0.03

# Mindestziel/MFE-Tracking (2026-07-27, Performance-Messung-Expertenanalyse - siehe
# project_performance_messung_backtracking_expertenanalyse.md). Unabhaengig vom
# finalen outcome_status (auch wenn spaeter Stop-Loss/Ueberholt/Abgelaufen folgt):
# wurde WENIGSTENS ZEITWEISE ein CRV von mindestens diesem Wert erreicht (Maximum
# Favorable Excursion, Van-Tharp-Konzept)? Bewusst NIEDRIGER als CRV_MINIMUM=2.0
# (risk_gate.py, die harte Take-Profit-Vorgabe) - Mindestziel ist ein separater,
# schwaecherer Maszstab ("war die Richtung ueberhaupt richtig"), kein Ersatz fuer
# die bestehende TP-Zone. Ueberschreibt/veraendert KEIN bestehendes Gate.
DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV = 1.0


@dataclass
class BackwardTrackingResult:
    geprueft_count: int = 0
    resolved_take_profit: int = 0
    resolved_stop_loss: int = 0
    expired: int = 0
    superseded: int = 0
    still_open: int = 0
    warnings: list[str] = field(default_factory=list)
    # Veto-Schatten-Tracking (2026-07-28, siehe check_signal_veto_shadow_outcome()
    # Docstring) - separater Zaehlerblock, damit dieser zweite Durchlauf nicht
    # mit der Statistik der echten/ausgefuehrten Signale vermischt wird.
    veto_schatten_geprueft_count: int = 0
    veto_schatten_take_profit: int = 0
    veto_schatten_stop_loss: int = 0
    veto_schatten_expired: int = 0
    veto_schatten_still_open: int = 0


def _threshold(von_value: float | None, point_value: float | None) -> float | None:
    """Von/Bis-Zone bevorzugt (neue Signale), Fallback auf den alten Punktwert
    (Bestandszeilen vor der Kurszonen-Slice, siehe Signal-Dataclass-Kommentar)."""
    return von_value if von_value is not None else point_value


def _entry_mid(signal) -> float | None:
    von = signal.entry_usd_von
    bis = signal.entry_usd_bis
    if von is not None and bis is not None:
        return (von + bis) / 2
    if von is not None:
        return von
    return signal.entry_usd


def _mittelwert(von: float | None, bis: float | None, punkt: float | None = None) -> float | None:
    """Generischer Zonen-Mittelwert (Von/Bis bevorzugt, optionaler Punktwert-
    Fallback fuer Alt-Signale ohne Zonen-Slice) - separat von _entry_mid()
    (nur fuer die TP/SL-Aufloesung genutzt), da HebelSignal keine Punktwert-
    Felder besitzt (wurde immer schon mit Zonen eingefuehrt)."""
    if von is not None and bis is not None:
        return (von + bis) / 2
    if von is not None:
        return von
    return punkt


def _zonen_mittel(signal) -> tuple[float | None, float | None, float | None]:
    """Entry-/Stop-Loss-/Take-Profit-Mittelwert (USD) - Grundlage fuer
    _ist_zonen_reaffirmation(). Nutzt getattr() mit None-Default statt
    direktem Attributzugriff, damit dieselbe Funktion unveraendert auch fuer
    HebelSignal-Objekte funktioniert (siehe hebel_backward_tracking.py)."""
    return (
        _mittelwert(
            getattr(signal, "entry_usd_von", None), getattr(signal, "entry_usd_bis", None),
            getattr(signal, "entry_usd", None),
        ),
        _mittelwert(
            getattr(signal, "stop_loss_usd_von", None), getattr(signal, "stop_loss_usd_bis", None),
            getattr(signal, "stop_loss_usd", None),
        ),
        _mittelwert(
            getattr(signal, "take_profit_usd_von", None), getattr(signal, "take_profit_usd_bis", None),
            getattr(signal, "take_profit_usd", None),
        ),
    )


def _ist_zonen_reaffirmation(signal, latest, toleranz_relativ: float) -> bool:
    """True, wenn Entry-, Stop-Loss- UND Take-Profit-Mittelwert von `latest`
    alle innerhalb der Toleranz um die Werte von `signal` liegen - dann ist
    `latest` inhaltlich eine Bestaetigung derselben These, keine neue
    Information (siehe Plan-Datei "Ueberholt-Erkennung reparieren", Gate 2).
    Konservativ: fehlt einer der drei Werte bei einem der beiden Signale,
    gilt das NICHT als Reaffirmation - die normale Ueberholung greift dann
    weiter, kein stiller Sonderfall."""
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
) -> bool:
    """Mindestbeobachtungsfenster (Untergrenze, spiegelbildlich zu
    _is_expired()'s Obergrenze) - ein Signal darf erst als ueberholt gelten,
    nachdem seit seiner Erstellung mindestens diese Zeit vergangen ist,
    abgeleitet aus derselben Content-Angabe (halte_kriterium_bucket) wie die
    Ablauf-Berechnung (siehe Plan-Datei "Ueberholt-Erkennung reparieren",
    Gate 1)."""
    bucket = getattr(signal, "halte_kriterium_bucket", None)
    mindest_tage = bucket_tage.get(bucket, fallback_tage) if bucket else fallback_tage
    alter = _parse_dt(latest.created_at) - _parse_dt(signal.created_at)
    return alter >= timedelta(days=mindest_tage)


def check_signal_outcome(
    conn, signal, watchlist, richtungstreffer_mindest_crv: float = DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
) -> tuple[str, dict]:
    """Prueft EIN Signal gegen die seit signal.created_at vorliegende Kurshistorie.
    Gibt (neuer_status, extra_felder) zurueck - schreibt selbst NICHTS in die DB
    (reiner Funktionskern, Testbarkeit ohne DB-Mocking der Schreibpfade). extra_felder
    ist ein dict mit optionalen Keys 'entschieden_am'/'realisiertes_crv'/'datenquelle'/
    'max_realisiertes_crv'/'mindestziel_erreicht_am', passend fuer
    db.update_signal_outcome(**extra_felder).

    Mindestziel/MFE-Tracking (2026-07-27, siehe DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV):
    laeuft PARALLEL zur bestehenden TP/SL-Aufloesung mit, veraendert deren Ergebnis
    NICHT - max_realisiertes_crv ist das hoechste an irgendeinem Tag erreichte
    guenstige CRV (Tages-High fuer LONG/Tages-Low fuer SHORT), unabhaengig davon,
    ob/wann das Signal spaeter per TP/SL/Ueberholt/Abgelaufen aufgeloest wird.
    mindestziel_erreicht_am ist das Datum des ERSTEN Tages, an dem die Schwelle
    erreicht wurde.

    Richtungsabhaengig (2026-07-27, Nutzer-Wunsch "auch auf sinkende Short-Kurse
    tracken"): VERKAUFEN/TAUSCHEN spiegeln TP/SL/MFE komplett - mirror von
    hebel_backward_tracking.py::check_hebel_signal_outcome()s ist_short-Zweig,
    hier ueber agent.krypto.gegenpruefung.richtung_aus_action() abgeleitet statt
    eines nativen richtung-Felds (Signal hat keins, siehe dortiger Docstring).
    Hedge-Invertierung (ist_hedge_invertiert) ist hier bewusst NICHT relevant -
    die Zonen beschreiben immer die Kursbewegung des Instruments SELBST, nicht
    die Gesamtmarkt-Interpretation."""
    if signal.action not in _TRACKABLE_ACTIONS:
        return OUTCOME_NICHT_ANWENDBAR, {}

    from agent.krypto.gegenpruefung import richtung_aus_action

    ist_short = richtung_aus_action(signal.action) == "SHORT"

    take_profit_threshold = _threshold(signal.take_profit_usd_von, signal.take_profit_usd)
    stop_loss_threshold = _threshold(signal.stop_loss_usd_von, signal.stop_loss_usd)
    if take_profit_threshold is None or stop_loss_threshold is None:
        return OUTCOME_NICHT_ANWENDBAR, {}

    asset = next((a for a in watchlist if a.symbol == signal.symbol), None)
    if asset is None:
        return OUTCOME_OFFEN, {}

    min_date = signal.created_at[:10]
    entry_mid = _entry_mid(signal)
    if entry_mid is not None:
        risiko_distanz = (
            (stop_loss_threshold - entry_mid) if ist_short else (entry_mid - stop_loss_threshold)
        )
        if risiko_distanz == 0:
            risiko_distanz = None
    else:
        risiko_distanz = None

    max_favorable_crv = None
    mindestziel_erreicht_am = None

    def _erfasse_mfe(guenstigster_preis: float, day_value: str) -> None:
        nonlocal max_favorable_crv, mindestziel_erreicht_am
        if risiko_distanz is None or risiko_distanz <= 0:
            return
        favorable_crv = (
            (entry_mid - guenstigster_preis) / risiko_distanz if ist_short
            else (guenstigster_preis - entry_mid) / risiko_distanz
        )
        if max_favorable_crv is None or favorable_crv > max_favorable_crv:
            max_favorable_crv = favorable_crv
        if mindestziel_erreicht_am is None and favorable_crv >= richtungstreffer_mindest_crv:
            mindestziel_erreicht_am = day_value

    def resolve(exit_price: float, hit_take: bool) -> tuple[str, dict]:
        status = OUTCOME_TAKE_PROFIT if hit_take else OUTCOME_STOP_LOSS
        realized_crv = None
        if entry_mid is not None and entry_mid != stop_loss_threshold:
            realized_crv = (
                (entry_mid - exit_price) / (stop_loss_threshold - entry_mid) if ist_short
                else (exit_price - entry_mid) / (entry_mid - stop_loss_threshold)
            )
        return status, {
            "entschieden_am": day,
            "realisiertes_crv": realized_crv,
            "datenquelle": datenquelle,
            "max_realisiertes_crv": max_favorable_crv,
            "mindestziel_erreicht_am": mindestziel_erreicht_am,
        }

    def _check_preis(high: float, low: float) -> tuple[bool, bool, float, float]:
        """Gibt (hit_take, hit_stop, exit_preis_bei_take, exit_preis_bei_stop) zurueck -
        SHORT spiegelt Take-Profit/Stop-Loss gegenueber LONG (Take-Profit unten,
        Stop-Loss oben)."""
        if ist_short:
            return (low <= take_profit_threshold, high >= stop_loss_threshold, low, high)
        return (high >= take_profit_threshold, low <= stop_loss_threshold, high, low)

    ohlc_rows = db.get_ohlc_history(conn, signal.symbol, "USD", min_date=min_date)
    if len(ohlc_rows) >= 1:
        datenquelle = "real"
        for row in ohlc_rows:
            day = row.date
            guenstigster_tagespreis = row.low if ist_short else row.high
            _erfasse_mfe(guenstigster_tagespreis, day)
            hit_take, hit_stop, exit_take, exit_stop = _check_preis(row.high, row.low)
            if hit_stop:
                # Konservativ (Z-1: Kapitalerhalt vor Gewinn): trifft ein Tag beide
                # Zonen, gewinnt Stop-Loss - keine Annahme ueber die Intraday-
                # Reihenfolge ohne Tick-Daten.
                return resolve(exit_stop, hit_take=False)
            if hit_take:
                return resolve(exit_take, hit_take=True)
    else:
        datenquelle = "proxy"
        price_rows = db.get_price_history(conn, asset.coingecko_id, min_date=min_date) if asset.coingecko_id else []
        for row in price_rows:
            if row.price_usd is None:
                continue
            day = row.date
            _erfasse_mfe(row.price_usd, day)
            hit_take, hit_stop, _, _ = _check_preis(row.price_usd, row.price_usd)
            if hit_stop:
                return resolve(row.price_usd, hit_take=False)
            if hit_take:
                return resolve(row.price_usd, hit_take=True)

    # Kein Treffer gefunden - offen oder abgelaufen, je nach Alter.
    return OUTCOME_OFFEN, {
        "max_realisiertes_crv": max_favorable_crv,
        "mindestziel_erreicht_am": mindestziel_erreicht_am,
    }


def _hat_veto_schatten_these(signal) -> bool:
    """Diskriminator fuer einen echten Veto-Schatten-Kandidaten (2026-07-28,
    siehe database/models.py::Signal.veto_outcome_status-Docstring fuer die
    volle Herleitung): `risk_veto=True` UND `action="HALTEN"` (das LLM wurde
    per Veto auf HALTEN zurueckgestuft) UND alle drei Preiszonen (Entry/
    Stop-Loss/Take-Profit) sind gesetzt - nur dann gibt es ueberhaupt eine
    hypothetische These, die sich nachverfolgen laesst. Ein regelkonformes,
    selbst gewaehltes HALTEN (kein Veto) hat KEINE Zonen und faellt hier
    automatisch durch."""
    if not (getattr(signal, "risk_veto", False) and signal.action == "HALTEN"):
        return False
    entry = _entry_mid(signal)
    stop = _threshold(signal.stop_loss_usd_von, signal.stop_loss_usd)
    take = _threshold(signal.take_profit_usd_von, signal.take_profit_usd)
    return entry is not None and stop is not None and take is not None


def _richtung_aus_veto_zonen(signal) -> str | None:
    """Bestimmt LONG/SHORT-Orientierung fuer einen Veto-Schatten-Kandidaten rein
    aus der relativen Zonen-Reihenfolge (Stop-Loss vs. Entry) - `action` ist
    durch den Veto bereits auf HALTEN ueberschrieben, richtung_aus_action()
    (agent/krypto/gegenpruefung.py) liefert also None und kann hier nicht
    genutzt werden. Spiegelt dieselbe implizite Logik, die risk_gate.py::
    post_check() fuer die CRV-Pflicht-Vetos bereits nutzt (_BUY_ACTIONS
    verlangt entry>stop_von, _SELL_ACTIONS verlangt stop_bis>entry): Stop-Loss
    UEBER dem Entry bedeutet SHORT-Orientierung (Stop-Loss oben, wie bei
    check_signal_outcome()s ist_short-Zweig), Stop-Loss UNTER dem Entry
    bedeutet LONG. None, wenn Entry/Stop-Loss fehlen oder identisch sind
    (keine eindeutige Richtung ableitbar)."""
    entry_mid = _entry_mid(signal)
    stop_loss_threshold = _threshold(signal.stop_loss_usd_von, signal.stop_loss_usd)
    if entry_mid is None or stop_loss_threshold is None or entry_mid == stop_loss_threshold:
        return None
    return "SHORT" if stop_loss_threshold > entry_mid else "LONG"


def check_signal_veto_shadow_outcome(
    conn, signal, watchlist, richtungstreffer_mindest_crv: float = DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
) -> tuple[str, dict]:
    """Wie check_signal_outcome(), aber fuer den Veto-Schatten-Zweig (2026-07-28,
    siehe _hat_veto_schatten_these()-Docstring fuer die volle Herleitung dieses
    Features): trackt Signale, deren Action durch einen Risk-Gate-Veto (CRV-
    Pflicht, Bitpanda/Cash-Veto, Regime-Mindestkonfidenz R-5.10, ...) auf HALTEN
    zurueckgestuft wurde, OBWOHL das LLM urspruenglich einen echten Trade
    vorgeschlagen hatte - ohne diesen zweiten Tracking-Zweig waeren diese
    hypothetischen Thesen (und Z.ais unabhaengiges Urteil dazu) fuer IMMER aus
    jeder Performance-Betrachtung verschwunden (siehe backward_tracking.py-
    Moduldocstring und database/db.py::_SIGNAL_VETO_SHADOW_NEW_COLUMNS).

    Identische TP/SL/MFE-Mechanik wie check_signal_outcome() (inkl. derselben
    konservativen Stop-Loss-vor-Take-Profit-Prioritaet bei Mehrfachtreffern am
    selben Tag) - einziger struktureller Unterschied: die Handelsrichtung kommt
    aus _richtung_aus_veto_zonen() statt richtung_aus_action(), weil `action`
    hier bereits auf HALTEN steht. Gibt (neuer_status, extra_felder) zurueck,
    extra_felder passend fuer db.update_signal_veto_shadow_outcome(**extra_felder)
    (bewusst OHNE 'datenquelle'-Key - dieses Feld wird im Schatten-Zweig nicht
    gespiegelt, siehe dortiger Docstring)."""
    if not _hat_veto_schatten_these(signal):
        return OUTCOME_NICHT_ANWENDBAR, {}

    ist_short = _richtung_aus_veto_zonen(signal) == "SHORT"

    take_profit_threshold = _threshold(signal.take_profit_usd_von, signal.take_profit_usd)
    stop_loss_threshold = _threshold(signal.stop_loss_usd_von, signal.stop_loss_usd)

    asset = next((a for a in watchlist if a.symbol == signal.symbol), None)
    if asset is None:
        return OUTCOME_OFFEN, {}

    min_date = signal.created_at[:10]
    entry_mid = _entry_mid(signal)
    risiko_distanz = (stop_loss_threshold - entry_mid) if ist_short else (entry_mid - stop_loss_threshold)
    if risiko_distanz == 0:
        risiko_distanz = None

    max_favorable_crv = None
    mindestziel_erreicht_am = None

    def _erfasse_mfe(guenstigster_preis: float, day_value: str) -> None:
        nonlocal max_favorable_crv, mindestziel_erreicht_am
        if risiko_distanz is None or risiko_distanz <= 0:
            return
        favorable_crv = (
            (entry_mid - guenstigster_preis) / risiko_distanz if ist_short
            else (guenstigster_preis - entry_mid) / risiko_distanz
        )
        if max_favorable_crv is None or favorable_crv > max_favorable_crv:
            max_favorable_crv = favorable_crv
        if mindestziel_erreicht_am is None and favorable_crv >= richtungstreffer_mindest_crv:
            mindestziel_erreicht_am = day_value

    def resolve(exit_price: float, hit_take: bool) -> tuple[str, dict]:
        status = OUTCOME_TAKE_PROFIT if hit_take else OUTCOME_STOP_LOSS
        realized_crv = None
        if entry_mid != stop_loss_threshold:
            realized_crv = (
                (entry_mid - exit_price) / (stop_loss_threshold - entry_mid) if ist_short
                else (exit_price - entry_mid) / (entry_mid - stop_loss_threshold)
            )
        return status, {
            "entschieden_am": day,
            "realisiertes_crv": realized_crv,
            "max_realisiertes_crv": max_favorable_crv,
            "mindestziel_erreicht_am": mindestziel_erreicht_am,
        }

    def _check_preis(high: float, low: float) -> tuple[bool, bool, float, float]:
        if ist_short:
            return (low <= take_profit_threshold, high >= stop_loss_threshold, low, high)
        return (high >= take_profit_threshold, low <= stop_loss_threshold, high, low)

    ohlc_rows = db.get_ohlc_history(conn, signal.symbol, "USD", min_date=min_date)
    if len(ohlc_rows) >= 1:
        for row in ohlc_rows:
            day = row.date
            guenstigster_tagespreis = row.low if ist_short else row.high
            _erfasse_mfe(guenstigster_tagespreis, day)
            hit_take, hit_stop, exit_take, exit_stop = _check_preis(row.high, row.low)
            if hit_stop:
                return resolve(exit_stop, hit_take=False)
            if hit_take:
                return resolve(exit_take, hit_take=True)
    else:
        price_rows = db.get_price_history(conn, asset.coingecko_id, min_date=min_date) if asset.coingecko_id else []
        for row in price_rows:
            if row.price_usd is None:
                continue
            day = row.date
            _erfasse_mfe(row.price_usd, day)
            hit_take, hit_stop, _, _ = _check_preis(row.price_usd, row.price_usd)
            if hit_stop:
                return resolve(row.price_usd, hit_take=False)
            if hit_take:
                return resolve(row.price_usd, hit_take=True)

    return OUTCOME_OFFEN, {
        "max_realisiertes_crv": max_favorable_crv,
        "mindestziel_erreicht_am": mindestziel_erreicht_am,
    }


_GEGENRICHTUNG_AKTIONEN = ("VERKAUFEN", "TAUSCHEN")


def _is_superseded(
    signal, latest_real: dict, mindestbeob_bucket: dict[str, int],
    mindestbeob_fallback: int, zonen_toleranz_relativ: float,
) -> bool:
    """2026-07-16 (Nutzer-Wunsch nach der Backward-Tracking-Diskussion:
    'redundante bzw. gegensaetzliche Empfehlungen muessen rausfallen, mit
    oder ohne Benachrichtigung'): ein noch offenes KAUFEN/NACHKAUFEN-Signal
    gilt als ueberholt, sobald fuer dasselbe Symbol bereits eine NEUERE
    echte Analyse mit einer tatsaechlich NEUEN Aktion vorliegt - entweder
    redundant (erneut KAUFEN/NACHKAUFEN) oder gegensaetzlich (VERKAUFEN/
    TAUSCHEN).

    NACHTRAG (2026-07-19, Backtracking-Aussagekraft-Audit): eine reine
    HALTEN-Bestaetigung ist KEINE der beiden Faelle - sie widerspricht der
    offenen Kauf-These nicht und bestaetigt sie auch nicht neu, sie sagt nur
    "keine Aenderung noetig". Live gegen den Notebook-Datenexport geprueft:
    unter der alten Regel wurden 100% der trackbaren Spot-Signale und 60%
    der Hebel-ERÖFFNEN-Signale innerhalb weniger Stunden ueberholt (Spot
    ⌀29h, Hebel ⌀11,7h) - lange bevor ein realistischer mehrtaegiger
    Kursverlauf Take-Profit/Stop-Loss ueberhaupt erreichen konnte, weil
    gehaltene/offene Positionen alle 3-24 Std. neu bewertet werden (siehe
    config.yaml hebel_position_cooldown_stunden/spot_cooldown_stunden_kern).
    Das hat die Ergebnisstatistik strukturell leergehalten (0 von 9 Spot-
    Signalen je real ausgewertet). HALTEN aus dem Ueberholt-Trigger
    auszuschliessen behebt das, ohne die urspruengliche Absicht (Duplikate/
    Widersprueche ausblenden) einzuschraenken.

    NACHTRAG 2 (2026-07-22, Nutzer-Frage "funktioniert das System auf
    Glueck?" - Backtest gegen echte Daten zeigte 89% (24/27) faelschlich
    ueberholte Hebel-Signale, siehe DEFAULT_MINDESTBEOBACHTUNG_*-Konstanten
    oben): ein erneutes KAUFEN/NACHKAUFEN (gleiche Richtung/Aktionskategorie
    wie das offene Signal) ueberholt jetzt NUR NOCH, wenn zwei zusaetzliche
    Gates erfuellt sind - (1) Mindestbeobachtung erreicht (das Signal hatte
    ueberhaupt Zeit, seine eigene These zu bestaetigen) UND (2) keine
    Zonen-Reaffirmation (die neue Analyse ist inhaltlich tatsaechlich eine
    andere These, nicht nur dieselbe mit fast identischen Zonen erneut
    bestaetigt). Eine echte Gegenrichtung (VERKAUFEN/TAUSCHEN nach KAUFEN)
    bleibt UNVERAENDERT sofort ueberholend - das war 2026-07-16 der
    urspruengliche, korrekte Zweck dieser Funktion und wird durch die
    beiden neuen Gates nicht angetastet.

    Rein deterministischer Datums-/ID-/Aktions-/Zonen-Vergleich gegen
    `db.get_latest_real_signal_per_symbol()` (bereits einmal pro Lauf
    geladen) - KEIN LLM-Call, erhoeht das Tagesbudget nicht."""
    latest = latest_real.get(signal.symbol)
    if latest is None or latest.id == signal.id or latest.created_at <= signal.created_at:
        return False
    if latest.action == "HALTEN":
        return False
    if latest.action in _GEGENRICHTUNG_AKTIONEN:
        return True
    if not _mindestbeobachtung_erreicht(signal, latest, mindestbeob_bucket, mindestbeob_fallback):
        return False
    if _ist_zonen_reaffirmation(signal, latest, zonen_toleranz_relativ):
        return False
    return True


def _is_expired(signal, bucket_tage: dict[str, int], fallback_tage: int) -> bool:
    """Inhaltsbasierte Ablaufzeit (siehe DEFAULT_ABGELAUFEN_TAGE_BUCKET oben):
    ein explizites `halte_kriterium_ziel_datum` (vom Modell gesetzt, aber in
    der Praxis selten) hat Vorrang; sonst der grobe `halte_kriterium_bucket`
    (kurz/mittel/lang, in der Praxis zuverlaessig gefuellt); sonst der
    Fallback-Wert (aeltere Signale ohne halte_kriterium-Daten)."""
    from datetime import datetime, timezone

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
            pass  # ungueltiges Datum vom Modell - auf bucket/Fallback zurueckfallen

    bucket = getattr(signal, "halte_kriterium_bucket", None)
    tage = bucket_tage.get(bucket, fallback_tage) if bucket else fallback_tage
    age_days = (now - created).days
    return age_days >= tage


def run_backward_tracking(conn, watchlist, config: dict) -> BackwardTrackingResult:
    """Holt alle Signale mit outcome_status IN (NULL, 'offen'), prueft jedes gegen
    die Kurshistorie, schreibt ein Ergebnis nur bei tatsaechlicher Statusaenderung
    (kein Write bei weiterhin 'offen' - reduziert unnoetige DB-Last bei jedem
    taeglichen Lauf).

    Ueberholt-Erkennung (2026-07-16, siehe _is_superseded()): `latest_real`
    einmal pro Lauf geladen (identisches Muster wie signal_batch.py), damit
    der Vergleich ohne N Zusatz-Queries auskommt."""
    result = BackwardTrackingResult()
    bt_cfg = config.get("backward_tracking", {})
    bucket_tage = bt_cfg.get("abgelaufen_nach_tagen_bucket", DEFAULT_ABGELAUFEN_TAGE_BUCKET)
    fallback_tage = bt_cfg.get("abgelaufen_nach_tagen_fallback", DEFAULT_ABGELAUFEN_TAGE_FALLBACK)
    mindestbeob_bucket = bt_cfg.get("mindestbeobachtung_tage_bucket", DEFAULT_MINDESTBEOBACHTUNG_TAGE_BUCKET)
    mindestbeob_fallback = bt_cfg.get("mindestbeobachtung_tage_fallback", DEFAULT_MINDESTBEOBACHTUNG_TAGE_FALLBACK)
    zonen_toleranz = bt_cfg.get(
        "zonen_reaffirmation_toleranz_relativ", DEFAULT_ZONEN_REAFFIRMATION_TOLERANZ_RELATIV,
    )
    richtungstreffer_mindest_crv = bt_cfg.get(
        "richtungstreffer_mindest_crv", DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    )
    latest_real = db.get_latest_real_signal_per_symbol(conn)

    rows = conn.execute(
        "SELECT id FROM signals WHERE outcome_status IS NULL OR outcome_status = ?",
        (OUTCOME_OFFEN,),
    ).fetchall()

    for row in rows:
        signal = db.get_signal_by_id(conn, row["id"])
        if signal is None:
            continue
        result.geprueft_count += 1

        status, extra = check_signal_outcome(conn, signal, watchlist, richtungstreffer_mindest_crv)

        if status == OUTCOME_NICHT_ANWENDBAR:
            db.update_signal_outcome(conn, signal.id, status)
            continue

        if status in (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS):
            db.update_signal_outcome(
                conn, signal.id, status,
                entschieden_am=extra.get("entschieden_am"),
                realisiertes_crv=extra.get("realisiertes_crv"),
                datenquelle=extra.get("datenquelle"),
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            if status == OUTCOME_TAKE_PROFIT:
                result.resolved_take_profit += 1
            else:
                result.resolved_stop_loss += 1
            continue

        # status == OUTCOME_OFFEN: erst Ueberholt-Check, dann Ablauf-Check.
        if _is_superseded(signal, latest_real, mindestbeob_bucket, mindestbeob_fallback, zonen_toleranz):
            db.update_signal_outcome(
                conn, signal.id, OUTCOME_UEBERHOLT,
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            result.superseded += 1
        elif _is_expired(signal, bucket_tage, fallback_tage):
            db.update_signal_outcome(
                conn, signal.id, OUTCOME_ABGELAUFEN,
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            result.expired += 1
        else:
            result.still_open += 1

    # Veto-Schatten-Zweig (2026-07-28, siehe check_signal_veto_shadow_outcome()-
    # Docstring): zweiter, unabhaengiger Durchlauf ueber Signale, deren Action per
    # Risk-Gate-Veto auf HALTEN zurueckgestuft wurde. Bewusst OHNE Ueberholt-Check
    # (_is_superseded()) - eine bereits hypothetische, nie ausgefuehrte These kann
    # durch eine neuere echte Analyse nicht im selben Sinn "ueberholt" werden wie
    # eine offene reale Position; Ablauf-Check (_is_expired()) bleibt sinnvoll,
    # da er nur von den signal-eigenen Feldern (created_at, halte_kriterium_*)
    # abhaengt, nicht von action.
    veto_shadow_rows = conn.execute(
        "SELECT id FROM signals WHERE risk_veto = 1 AND action = 'HALTEN' "
        "AND (veto_outcome_status IS NULL OR veto_outcome_status = ?)",
        (OUTCOME_OFFEN,),
    ).fetchall()

    for row in veto_shadow_rows:
        signal = db.get_signal_by_id(conn, row["id"])
        if signal is None:
            continue
        result.veto_schatten_geprueft_count += 1

        status, extra = check_signal_veto_shadow_outcome(conn, signal, watchlist, richtungstreffer_mindest_crv)

        if status == OUTCOME_NICHT_ANWENDBAR:
            db.update_signal_veto_shadow_outcome(conn, signal.id, status)
            continue

        if status in (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS):
            db.update_signal_veto_shadow_outcome(
                conn, signal.id, status,
                entschieden_am=extra.get("entschieden_am"),
                realisiertes_crv=extra.get("realisiertes_crv"),
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            if status == OUTCOME_TAKE_PROFIT:
                result.veto_schatten_take_profit += 1
            else:
                result.veto_schatten_stop_loss += 1
            continue

        if _is_expired(signal, bucket_tage, fallback_tage):
            db.update_signal_veto_shadow_outcome(
                conn, signal.id, OUTCOME_ABGELAUFEN,
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            result.veto_schatten_expired += 1
        else:
            result.veto_schatten_still_open += 1

    return result


_RESOLVED_OUTCOMES = (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS, OUTCOME_LIQUIDATION)


def _aggregate_resolved_signal_rows(
    conn, *, veto: bool, watchlist: list | None = None,
) -> dict[tuple[str, str], dict]:
    """Gemeinsamer, noch UNFORMATIERTER Aggregations-Kern fuer
    compute_provider_performance() und compute_veto_shadow_performance()
    (2026-07-28, extrahiert damit compute_gesamt_signalqualitaet() beide
    Quellen exakt zusammenfuehren kann - Rohzaehler statt einer nachtraeglichen
    Rueckrechnung aus zwei bereits gemittelten avg_realisiertes_crv-Werten, die
    bei fehlendem entry_mid in Einzelfaellen von der tatsaechlichen Crv-Anzahl
    abweichen wuerde). `veto=False` liest outcome_status/outcome_realisiertes_crv
    (echte/ausgefuehrte Signale), `veto=True` liest veto_outcome_status/
    veto_outcome_realisiertes_crv gefiltert auf risk_veto=1 AND action='HALTEN'
    (siehe check_signal_veto_shadow_outcome()-Docstring)."""
    status_col = "veto_outcome_status" if veto else "outcome_status"
    crv_col = "veto_outcome_realisiertes_crv" if veto else "outcome_realisiertes_crv"
    filter_clause = "risk_veto = 1 AND action = 'HALTEN' AND " if veto else ""

    gruppen: dict[tuple[str, str], dict] = {}
    assetklasse_by_symbol = {a.symbol: a.assetklasse for a in watchlist} if watchlist else {}

    def _stelle_sicher(tier: str, provider: str) -> dict:
        key = (tier, provider)
        if key not in gruppen:
            gruppen[key] = {
                "anzahl_resolved": 0,
                "take_profit_count": 0,
                "stop_loss_count": 0,
                "liquidation_count": 0,
                "_crv_summe": 0.0,
                "_crv_count": 0,
            }
        return gruppen[key]

    placeholders = ", ".join("?" for _ in _RESOLVED_OUTCOMES)
    spot_rows = conn.execute(
        f"SELECT symbol, groq_model AS llm_model, {status_col} AS status, {crv_col} AS crv "
        f"FROM signals WHERE {filter_clause}{status_col} IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in spot_rows:
        tier = assetklasse_by_symbol.get(row["symbol"], "unbekannt") if watchlist else "spot"
        eintrag = _stelle_sicher(tier, provider_from_label(row["llm_model"]))
        eintrag["anzahl_resolved"] += 1
        if row["status"] == OUTCOME_TAKE_PROFIT:
            eintrag["take_profit_count"] += 1
        elif row["status"] == OUTCOME_STOP_LOSS:
            eintrag["stop_loss_count"] += 1
        if row["crv"] is not None:
            eintrag["_crv_summe"] += row["crv"]
            eintrag["_crv_count"] += 1

    hebel_rows = conn.execute(
        f"SELECT llm_model, {status_col} AS status, {crv_col} AS crv "
        f"FROM hebel_signals WHERE {filter_clause}{status_col} IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in hebel_rows:
        eintrag = _stelle_sicher("hebel", provider_from_label(row["llm_model"]))
        eintrag["anzahl_resolved"] += 1
        if row["status"] == OUTCOME_TAKE_PROFIT:
            eintrag["take_profit_count"] += 1
        elif row["status"] == OUTCOME_STOP_LOSS:
            eintrag["stop_loss_count"] += 1
        elif row["status"] == OUTCOME_LIQUIDATION:
            eintrag["liquidation_count"] += 1
        if row["crv"] is not None:
            eintrag["_crv_summe"] += row["crv"]
            eintrag["_crv_count"] += 1

    return gruppen


def _format_performance_gruppen(gruppen: dict[tuple[str, str], dict], watchlist: list | None) -> dict:
    ergebnis: dict = {"hebel": {}} if watchlist else {"spot": {}, "hebel": {}}
    for (tier, provider), eintrag in gruppen.items():
        anzahl = eintrag["anzahl_resolved"]
        ergebnis.setdefault(tier, {})[provider] = {
            "anzahl_resolved": anzahl,
            "take_profit_count": eintrag["take_profit_count"],
            "stop_loss_count": eintrag["stop_loss_count"],
            "liquidation_count": eintrag["liquidation_count"],
            "win_rate": (eintrag["take_profit_count"] / anzahl) if anzahl > 0 else None,
            "avg_realisiertes_crv": (
                eintrag["_crv_summe"] / eintrag["_crv_count"] if eintrag["_crv_count"] > 0 else None
            ),
        }
    return ergebnis


def compute_provider_performance(conn, watchlist: list | None = None) -> dict:
    """Provider-Performance-Aggregation (2026-07-15, Nutzer-Wunsch: Groq/Cerebras/
    Gemini nach echter Trefferquote statt nur Kapazitaet vergleichen). Liest ALLE
    bereits aufgeloesten Signale (take_profit_erreicht/stop_loss_erreicht, bei
    Hebel zusaetzlich liquidation_wahrscheinlich) aus signals UND hebel_signals,
    gruppiert nach (tier, provider_from_label(...)). Spot und Hebel bleiben
    GETRENNT (unterschiedliche Risikoprofile - RM-1 2% vs. Hebel 1%
    Positionsgroesse, siehe Regelwerksmanual "Positionsgroesse bei Hebel" - eine
    gemeinsame Kennzahl waere irrefuehrend). Reine Lesefunktion, kein
    Seiteneffekt.

    Assetklassen-Aufschluesselung (2026-07-20, Nutzer-Frage "Wie ist der Status
    zum Thema Backtracking bei nicht Krypto?"): die `signals`-Tabelle enthaelt
    seit den Aktien-/Rohstoff-/Hedge-/Themen-ETF-Pipelines (alle nutzen
    dieselbe `insert_signal()`) laengst auch deren Signale, aber die Anzeige
    poolte bisher ALLES unter einem einzigen "spot"-Schluessel - Krypto und
    z.B. Rohstoffe waren in der Provider-Performance-Karte nicht mehr
    unterscheidbar. `watchlist` (optional, Default None = altes Verhalten mit
    nur "spot") erlaubt jetzt eine Aufschluesselung nach `asset.assetklasse`
    (krypto/aktien/rohstoffe/etf) statt einem einzigen Topf - bewusst FEINER
    als `compute_win_rate_fact()`s Pooling (das Krypto+Aktien fuer den
    Prompt-Fakt bewusst zusammenlegt, siehe dortiger Docstring), weil diese
    Anzeige-Karte fuer den Nutzer Sichtbarkeit PRO Assetklasse schaffen soll,
    nicht die Prompt-Kalibrierung eines Modells. Symbole, die nicht (mehr) in
    der Watchlist stehen, fallen unter "unbekannt" statt zu verschwinden.

    (2026-07-28: Aggregations-Kern nach _aggregate_resolved_signal_rows()
    ausgelagert, Verhalten/Rueckgabeform unveraendert - siehe dortiger
    Docstring fuer den Grund.)"""
    gruppen = _aggregate_resolved_signal_rows(conn, veto=False, watchlist=watchlist)
    return _format_performance_gruppen(gruppen, watchlist)


def compute_veto_shadow_performance(conn, watchlist: list | None = None) -> dict:
    """Wie compute_provider_performance(), aber fuer den Veto-Schatten-Zweig
    (2026-07-28, siehe check_signal_veto_shadow_outcome()/check_hebel_signal_
    veto_shadow_outcome()-Docstrings fuer die volle Herleitung): Provider-/
    Tier-Aufschluesselung ueber alle hypothetischen, NIE ausgefuehrten Trade-
    Vorschlaege, deren Action durch einen Risk-Gate-Veto auf HALTEN
    zurueckgestuft wurde. `llm_model`/`groq_model` bleiben vom Veto unberuehrt
    (nur action/risk_veto/risk_veto_reason werden ueberschrieben, siehe
    hebel_risk_gate.py::post_check_hebel()/risk_gate.py::post_check()) - die
    Provider-Zuordnung bleibt also korrekt. Gleiche Rueckgabeform wie
    compute_provider_performance(), bewusst als KOMPLETT SEPARATE Funktion
    (Option B) statt eines Parameters an compute_provider_performance() - ein
    Konsument, der nur echte Performance anzeigen will, kann diese Funktion
    schlicht nicht aufrufen, statt sich auf einen Flag-Default verlassen zu
    muessen."""
    gruppen = _aggregate_resolved_signal_rows(conn, veto=True, watchlist=watchlist)
    return _format_performance_gruppen(gruppen, watchlist)


def compute_gesamt_signalqualitaet(conn, watchlist: list | None = None) -> dict:
    """"Gesamt-Signalqualitaet, unabhaengig vom Risk-Gate" (2026-07-28, Nutzer-
    Einsicht bei der Konzeption dieses Features: "eigentlich die Veto-Schatten
    und die ausfuehrbaren Empfehlungen-Signale sind eigentlich die Gesamt- und
    Echtperformance/Trefferquote sind"). Summiert die Rohzaehler von
    compute_provider_performance() (echte/ausgefuehrte Signale) UND
    compute_veto_shadow_performance() (hypothetische, vetote Vorschlaege) je
    (tier, provider) und berechnet win_rate/avg_realisiertes_crv NEU aus den
    summierten Zaehlern - NICHT als Mittelwert der beiden bereits gerundeten
    Einzelquoten (waere bei unterschiedlichen Stichprobengroessen falsch).

    Rein additive Aggregation AUF DER ANZEIGE-/SERIALISIERUNGS-EBENE - beide
    Quellen bleiben in der DB/den einzelnen Storage-Funktionen komplett
    getrennt (Option B, siehe database/db.py::_SIGNAL_VETO_SHADOW_NEW_COLUMNS-
    Docstring); diese Funktion ist der EINZIGE Ort, an dem beide
    zusammengefuehrt werden."""
    real = _aggregate_resolved_signal_rows(conn, veto=False, watchlist=watchlist)
    schatten = _aggregate_resolved_signal_rows(conn, veto=True, watchlist=watchlist)
    merged: dict[tuple[str, str], dict] = {}
    for gruppen in (real, schatten):
        for key, werte in gruppen.items():
            ziel = merged.setdefault(key, {
                "anzahl_resolved": 0, "take_profit_count": 0, "stop_loss_count": 0,
                "liquidation_count": 0, "_crv_summe": 0.0, "_crv_count": 0,
            })
            for feld in (
                "anzahl_resolved", "take_profit_count", "stop_loss_count",
                "liquidation_count", "_crv_summe", "_crv_count",
            ):
                ziel[feld] += werte[feld]
    return _format_performance_gruppen(merged, watchlist)


def compute_provider_sendezaehler(conn, watchlist: list | None = None) -> dict:
    """Rohe, ergebnisUNABHAENGIGE Sendeanzahl je (tier, provider) (2026-07-28,
    Nutzer-Frage "wie oft hat Gemini ueberhaupt welche Signale gesendet?" -
    compute_provider_performance() zeigt einen Provider nur, sobald mindestens
    ein Signal RESOLVED ist (take_profit/stop_loss/liquidation); ein selten
    eingesetzter Provider wie Gemini kann so komplett unsichtbar bleiben, auch
    wenn er bereits mehrfach gerufen wurde, nur eben noch kein Signal
    aufgeloest ist). Zaehlt jede Zeile mit `groq_raw_response IS NOT NULL`
    (= echte LLM-Analyse fand statt, identisches Gate wie get_latest_real_
    signal_per_symbol()/get_latest_hebel_signal_per_symbol() - NICHT
    gate_passed, da der AnalystResponseInvalid-Fallback gate_passed=True setzt
    ohne echte Antwort), unabhaengig von outcome_status/action/risk_veto -
    rein informativ, keine Performance-Aussage."""
    zaehler: dict[tuple[str, str], int] = {}
    assetklasse_by_symbol = {a.symbol: a.assetklasse for a in watchlist} if watchlist else {}

    spot_rows = conn.execute(
        "SELECT symbol, groq_model AS llm_model FROM signals WHERE groq_raw_response IS NOT NULL",
    ).fetchall()
    for row in spot_rows:
        tier = assetklasse_by_symbol.get(row["symbol"], "unbekannt") if watchlist else "spot"
        key = (tier, provider_from_label(row["llm_model"]))
        zaehler[key] = zaehler.get(key, 0) + 1

    hebel_rows = conn.execute(
        "SELECT llm_model FROM hebel_signals WHERE groq_raw_response IS NOT NULL",
    ).fetchall()
    for row in hebel_rows:
        key = ("hebel", provider_from_label(row["llm_model"]))
        zaehler[key] = zaehler.get(key, 0) + 1

    ergebnis: dict = {"hebel": {}} if watchlist else {"spot": {}, "hebel": {}}
    for (tier, provider), anzahl in zaehler.items():
        ergebnis.setdefault(tier, {})[provider] = anzahl

    return ergebnis


# Rueckgabewerte von bewerte_zai_richtung() jenseits von "treffer"/"fehlschlag" -
# als benannte Konstanten statt Strings inline, damit compute_zai_richtung_
# performance() sie eindeutig in getrennte Zaehler einsortieren kann (siehe
# dortige Docstring-Erklaerung des Unterschieds).
ZAI_URTEIL_NEUTRAL = "neutral"
ZAI_URTEIL_KEINE_KLARE_BEWEGUNG = "keine_klare_marktbewegung"


def bewerte_zai_richtung(
    primaer_richtung: str, max_realisiertes_crv: float | None, zai_eigene_richtung: str | None,
    richtungstreffer_mindest_crv: float = DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
) -> str:
    """Vergleicht Z.ais UNABHAENGIGE Richtungs-Ableitung (Call 2,
    `zai_eigene_richtung` aus agent/krypto/gegenpruefung.py::leite_eigene_richtung())
    gegen die TATSAECHLICHE Marktrichtung - komplett unabhaengig davon, ob
    Z.ai mit dem primaeren Signal selbst uebereinstimmte (das misst bereits
    `zai_uebereinstimmung`, siehe Modul-Docstring von gegenpruefung.py).

    Nutzer-Wunsch (2026-07-27, nach der Feststellung, dass `hebel_richtung_modus`
    auf dem Notebook seit Einfuehrung der Long/Short-Funktion durchgehend
    "nur_long" ist - Mistrals extreme LONG-Bias in den bisherigen Auswertungen
    ist also ein strukturelles Konfigurations-Artefakt, keine organische
    Strategie): "ZAI unabhaengig mit seinen unterschiedlichen Entscheidungen
    und deren Erfolgsquote messen" - analog zu compute_provider_performance()/
    compute_win_rate_fact(), aber unabhaengig von Mistrals Bias.

    NACHTRAG (2026-07-27, Punkt 3 der Performance-Messung-Nachfrage): erste
    Version nutzte den binaeren `outcome_status` (TP/SL-Zone getroffen?) -
    Nutzer-Einwand zurecht: das "reizt die Take-Profit-Zone nicht aus", ein
    Signal, das nie TP/SL erreicht (spaeter ueberholt/abgelaufen) aber
    zwischenzeitlich klar in eine Richtung lief, wurde komplett ignoriert.
    Jetzt auf `outcome_max_realisiertes_crv` (Maximum Favorable Excursion,
    bereits fuer die bestehende Richtungstreffer-Quote berechnet, siehe
    compute_richtungstreffer_quote()) umgestellt - BREITER als der reine
    TP/SL-Fall, gleiche Philosophie: eine Bewegung zaehlt erst als
    "tatsaechliche Richtung", wenn sie mindestens `richtungstreffer_mindest_crv`
    CRV erreicht hat (Default 1.0, konfigurierbar, gleicher Wert wie
    compute_richtungstreffer_quote() verwendet).

    `max_realisiertes_crv` ist bereits relativ zu `primaer_richtung`s eigener
    Risiko-Distanz berechnet (siehe check_signal_outcome()/
    check_hebel_signal_outcome()): deutlich positiv (>= Schwelle) heisst
    "Markt bestaetigte primaer_richtung", deutlich negativ (<= -Schwelle)
    heisst "Markt lief klar in die GEGENRICHTUNG von primaer_richtung" (kein
    neuer Kursabruf noetig, reine Vorzeichen-/Schwellen-Auswertung eines
    bereits vorhandenen Werts). Dazwischen (keine der beiden Schwellen
    erreicht) -> `ZAI_URTEIL_KEINE_KLARE_BEWEGUNG` (eigener Zaehler, siehe
    compute_zai_richtung_performance() - nicht dasselbe wie NEUTRAL: hier hat
    der MARKT nicht klar entschieden, unabhaengig davon, was Z.ai sagte).

    `zai_eigene_richtung`=NEUTRAL (oder None/unbekannt) liefert
    `ZAI_URTEIL_NEUTRAL` (eigener Zaehler, weder Treffer noch Fehlschlag) -
    Nutzer-Entscheidung 2026-07-27: "wuerde ich neutral zaehlen eher nein -
    denn wir messen es auch nicht oder?" (analog dazu, dass HALTEN/Mistral-
    NEUTRAL ebenfalls nicht in die bestehenden Trefferquoten einfliesst).
    `max_realisiertes_crv is None` wird ebenso behandelt (kein MFE-Wert
    vorhanden, z.B. nie eine OHLC-Zeile gefunden)."""
    if max_realisiertes_crv is None or zai_eigene_richtung not in ("LONG", "SHORT"):
        return ZAI_URTEIL_NEUTRAL
    if max_realisiertes_crv >= richtungstreffer_mindest_crv:
        tatsaechliche_richtung = primaer_richtung
    elif max_realisiertes_crv <= -richtungstreffer_mindest_crv:
        tatsaechliche_richtung = "SHORT" if primaer_richtung == "LONG" else "LONG"
    else:
        return ZAI_URTEIL_KEINE_KLARE_BEWEGUNG
    return "treffer" if zai_eigene_richtung == tatsaechliche_richtung else "fehlschlag"


def compute_zai_richtung_performance(
    conn, watchlist: list | None = None,
    richtungstreffer_mindest_crv: float = DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
) -> dict:
    """Aggregiert bewerte_zai_richtung() ueber alle Signale mit gesetztem
    `zai_eigene_richtung` UND vorhandenem `outcome_max_realisiertes_crv` - aus
    hebel_signals (echtes `richtung`-Feld) UND signals (Spot-family,
    `primaer_richtung` via agent.krypto.gegenpruefung.richtung_aus_action()
    aus `action` abgeleitet, identisch zu der Ableitung, die bereits fuer
    `zai_uebereinstimmung` verwendet wird). Gleiche Tier-Aufschluesselung wie
    compute_provider_performance() (Hebel gesondert, Spot-family nach
    Assetklasse wenn `watchlist` uebergeben wird).

    Basis ist `outcome_max_realisiertes_crv` (Maximum Favorable Excursion),
    NICHT `outcome_status` - siehe bewerte_zai_richtung()-Docstring fuer die
    Begruendung (Punkt 3 der Performance-Messung-Nachfrage, 2026-07-27:
    "die Take-Profit-Zone nicht ausgereizt" haette mit dem binaeren
    outcome_status viele Faelle uebersehen). WHERE-Filter deshalb breiter als
    die erste Version: `outcome_max_realisiertes_crv IS NOT NULL` statt
    `outcome_status IN (_RESOLVED_OUTCOMES)` - identisch zum WHERE-Filter von
    compute_richtungstreffer_quote().

    Hedge-Instrumente (in agent.hedge.pipeline.SYMBOL_ZU_HEBEL_FAKTOR gelistet)
    bekommen `ist_hedge_invertiert=True` fuer richtung_aus_action() - siehe
    dortiger Docstring (KAUFEN = Hedge aufbauen = baerische Gesamtmarkt-
    erwartung -> SHORT).

    Wichtige Einschraenkung (2026-07-27, gilt weiterhin): signals._TRACKABLE_
    ACTIONS = nur KAUFEN/NACHKAUFEN bekommen je ein outcome_max_realisiertes_crv
    berechnet (siehe check_signal_outcome()) - VERKAUFEN/TAUSCHEN (die SHORT-
    Seite der Spot-family) tauchen hier also praktisch nicht auf, bis ein
    eigenes Sell-Side-Tracking existiert. Bei Hebel gilt diese Einschraenkung
    NICHT (check_hebel_signal_outcome() berechnet MFE fuer beide Richtungen).

    Rueckgabe je Tier: {"anzahl_bewertet" (nur treffer+fehlschlaege, siehe
    unten), "treffer", "fehlschlaege", "neutral" (Z.ai antwortete NEUTRAL),
    "keine_klare_marktbewegung" (Markt bewegte sich nicht entscheidend genug,
    unabhaengig von Z.ais Antwort), "trefferquote_pct"}. `anzahl_bewertet`
    zaehlt bewusst NUR Faelle mit eindeutigem Urteil (treffer+fehlschlaege) -
    die anderen beiden Kategorien waeren sonst faelschlich in der
    Trefferquote verwaesserend mitgezaehlt. Reine Lesefunktion, kein
    Seiteneffekt."""
    from agent.hedge.pipeline import SYMBOL_ZU_HEBEL_FAKTOR as _hedge_symbole
    from agent.krypto.gegenpruefung import richtung_aus_action

    assetklasse_by_symbol = {a.symbol: a.assetklasse for a in watchlist} if watchlist else {}
    ergebnis: dict = {}

    def _stelle_sicher(tier: str) -> dict:
        return ergebnis.setdefault(tier, {
            "anzahl_bewertet": 0, "treffer": 0, "fehlschlaege": 0,
            "neutral": 0, "keine_klare_marktbewegung": 0, "trefferquote_pct": None,
        })

    def _erfasse(tier: str, urteil: str) -> None:
        eintrag = _stelle_sicher(tier)
        if urteil == ZAI_URTEIL_NEUTRAL:
            eintrag["neutral"] += 1
        elif urteil == ZAI_URTEIL_KEINE_KLARE_BEWEGUNG:
            eintrag["keine_klare_marktbewegung"] += 1
        elif urteil == "treffer":
            eintrag["anzahl_bewertet"] += 1
            eintrag["treffer"] += 1
        else:
            eintrag["anzahl_bewertet"] += 1
            eintrag["fehlschlaege"] += 1

    hebel_rows = conn.execute(
        "SELECT richtung, outcome_max_realisiertes_crv, zai_eigene_richtung FROM hebel_signals "
        "WHERE outcome_max_realisiertes_crv IS NOT NULL AND zai_eigene_richtung IS NOT NULL",
    ).fetchall()
    for row in hebel_rows:
        urteil = bewerte_zai_richtung(
            row["richtung"], row["outcome_max_realisiertes_crv"], row["zai_eigene_richtung"],
            richtungstreffer_mindest_crv,
        )
        _erfasse("hebel", urteil)

    spot_rows = conn.execute(
        "SELECT symbol, action, outcome_max_realisiertes_crv, zai_eigene_richtung FROM signals "
        "WHERE outcome_max_realisiertes_crv IS NOT NULL AND zai_eigene_richtung IS NOT NULL",
    ).fetchall()
    for row in spot_rows:
        primaer_richtung = richtung_aus_action(
            row["action"], ist_hedge_invertiert=row["symbol"] in _hedge_symbole,
        )
        if primaer_richtung is None:
            continue
        tier = assetklasse_by_symbol.get(row["symbol"], "unbekannt") if watchlist else "spot"
        urteil = bewerte_zai_richtung(
            primaer_richtung, row["outcome_max_realisiertes_crv"], row["zai_eigene_richtung"],
            richtungstreffer_mindest_crv,
        )
        _erfasse(tier, urteil)

    for eintrag in ergebnis.values():
        n = eintrag["anzahl_bewertet"]
        eintrag["trefferquote_pct"] = round(100 * eintrag["treffer"] / n, 1) if n > 0 else None

    return ergebnis


def compute_zai_richtung_performance_schatten(
    conn, watchlist: list | None = None,
    richtungstreffer_mindest_crv: float = DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
) -> dict:
    """Wie compute_zai_richtung_performance(), aber fuer den Veto-Schatten-Zweig
    (2026-07-28, siehe check_signal_veto_shadow_outcome()-Docstring): misst
    Z.ais unabhaengiges Richtungsurteil (Call 2) gerade fuer die Faelle, in
    denen es am interessantesten waere - LLM1 wollte handeln, wurde aber per
    Risk-Gate-Veto auf HALTEN zurueckgestuft - und die sonst NIE bewertet
    wuerden (der Konsistenz-/Richtungs-Abgleich laeuft zwar trotzdem, siehe
    agent/krypto/gegenpruefung.py::fuehre_beide_calls_im_hintergrund(), aber
    OHNE diesen Zweig hier bliebe `zai_eigene_richtung` fuer solche Zeilen
    permanent unausgewertet).

    Direktions-Ableitung: Hebel nutzt weiterhin `signal.richtung` (vom Veto
    unveraendert), Spot-family nutzt _richtung_aus_veto_zonen() (Zonen-
    Reihenfolge) statt richtung_aus_action() - `action` steht hier bereits auf
    HALTEN, richtung_aus_action() wuerde also None liefern (siehe dortiger
    Docstring). Gleiche Tier-Aufschluesselung und Rueckgabeform wie
    compute_zai_richtung_performance(), bewusst als separate Funktion (Option
    B) statt eines Parameters."""
    assetklasse_by_symbol = {a.symbol: a.assetklasse for a in watchlist} if watchlist else {}
    ergebnis: dict = {}

    def _stelle_sicher(tier: str) -> dict:
        return ergebnis.setdefault(tier, {
            "anzahl_bewertet": 0, "treffer": 0, "fehlschlaege": 0,
            "neutral": 0, "keine_klare_marktbewegung": 0, "trefferquote_pct": None,
        })

    def _erfasse(tier: str, urteil: str) -> None:
        eintrag = _stelle_sicher(tier)
        if urteil == ZAI_URTEIL_NEUTRAL:
            eintrag["neutral"] += 1
        elif urteil == ZAI_URTEIL_KEINE_KLARE_BEWEGUNG:
            eintrag["keine_klare_marktbewegung"] += 1
        elif urteil == "treffer":
            eintrag["anzahl_bewertet"] += 1
            eintrag["treffer"] += 1
        else:
            eintrag["anzahl_bewertet"] += 1
            eintrag["fehlschlaege"] += 1

    hebel_rows = conn.execute(
        "SELECT richtung, veto_outcome_max_realisiertes_crv, zai_eigene_richtung FROM hebel_signals "
        "WHERE risk_veto = 1 AND action = 'HALTEN' "
        "AND veto_outcome_max_realisiertes_crv IS NOT NULL AND zai_eigene_richtung IS NOT NULL",
    ).fetchall()
    for row in hebel_rows:
        urteil = bewerte_zai_richtung(
            row["richtung"], row["veto_outcome_max_realisiertes_crv"], row["zai_eigene_richtung"],
            richtungstreffer_mindest_crv,
        )
        _erfasse("hebel", urteil)

    spot_ids = conn.execute(
        "SELECT id, symbol FROM signals WHERE risk_veto = 1 AND action = 'HALTEN' "
        "AND veto_outcome_max_realisiertes_crv IS NOT NULL AND zai_eigene_richtung IS NOT NULL",
    ).fetchall()
    for row in spot_ids:
        signal = db.get_signal_by_id(conn, row["id"])
        if signal is None:
            continue
        primaer_richtung = _richtung_aus_veto_zonen(signal)
        if primaer_richtung is None:
            continue
        tier = assetklasse_by_symbol.get(row["symbol"], "unbekannt") if watchlist else "spot"
        urteil = bewerte_zai_richtung(
            primaer_richtung, signal.veto_outcome_max_realisiertes_crv, signal.zai_eigene_richtung,
            richtungstreffer_mindest_crv,
        )
        _erfasse(tier, urteil)

    for eintrag in ergebnis.values():
        n = eintrag["anzahl_bewertet"]
        eintrag["trefferquote_pct"] = round(100 * eintrag["treffer"] / n, 1) if n > 0 else None

    return ergebnis


# Trackbare Hebel-Aktionen fuer die Offen-Uebersicht (2026-07-24) - identisch zu
# _TRACKABLE_HEBEL_ACTIONS in hebel_backward_tracking.py, hier bewusst dupliziert
# statt importiert: hebel_backward_tracking.py importiert bereits von diesem Modul
# (OUTCOME_*-Konstanten), ein Rueckimport wuerde einen Zirkelimport erzeugen.
_HEBEL_TRACKABLE_ACTIONS_FUER_UEBERSICHT = ("ERÖFFNEN", "NACHKAUFEN")


def compute_offene_signale_uebersicht(conn, watchlist: list | None = None) -> dict:
    """Ergaenzt compute_provider_performance() um Sichtbarkeit fuer noch NICHT
    aufgeloeste, aber bereits trackbare Signale (outcome_status IS NULL, echte
    Kauf-/Nachkauf-/Eroeffnen-Aktion) - Nutzer-Fund (2026-07-24, Remote-Seite
    zeigte bei 0 abgeschlossenen Spot-Signalen keinerlei Hinweis, ob ueberhaupt
    Fortschritt passiert oder das Tracking schlicht stillsteht). Gleiche
    Tier-Aufschluesselung wie compute_provider_performance() (Spot nach
    Assetklasse, Hebel gesondert), aber OHNE Provider-Aufschluesselung - ein
    offenes Signal hat noch kein Ergebnis, das waere irrefuehrend.

    Rueckgabe je Tier: {"anzahl": int, "aeltestes_erstellt_am": str | None}."""
    assetklasse_by_symbol = {a.symbol: a.assetklasse for a in watchlist} if watchlist else {}
    ergebnis: dict = {"hebel": {"anzahl": 0, "aeltestes_erstellt_am": None}}
    if not watchlist:
        ergebnis["spot"] = {"anzahl": 0, "aeltestes_erstellt_am": None}

    def _erfasse(tier: str, created_at: str) -> None:
        eintrag = ergebnis.setdefault(tier, {"anzahl": 0, "aeltestes_erstellt_am": None})
        eintrag["anzahl"] += 1
        if eintrag["aeltestes_erstellt_am"] is None or created_at < eintrag["aeltestes_erstellt_am"]:
            eintrag["aeltestes_erstellt_am"] = created_at

    placeholders = ", ".join("?" for _ in _TRACKABLE_ACTIONS)
    spot_rows = conn.execute(
        f"SELECT symbol, created_at FROM signals WHERE outcome_status IS NULL AND action IN ({placeholders})",
        tuple(_TRACKABLE_ACTIONS),
    ).fetchall()
    for row in spot_rows:
        tier = assetklasse_by_symbol.get(row["symbol"], "unbekannt") if watchlist else "spot"
        _erfasse(tier, row["created_at"])

    hebel_placeholders = ", ".join("?" for _ in _HEBEL_TRACKABLE_ACTIONS_FUER_UEBERSICHT)
    hebel_rows = conn.execute(
        f"SELECT created_at FROM hebel_signals WHERE outcome_status IS NULL AND action IN ({hebel_placeholders})",
        _HEBEL_TRACKABLE_ACTIONS_FUER_UEBERSICHT,
    ).fetchall()
    for row in hebel_rows:
        _erfasse("hebel", row["created_at"])

    return ergebnis


# Historische Trefferquote als Prompt-Fakt (2026-07-18, Item E der Konfidenz-
# Kalibrierungs-Runde, siehe Memory project_konfidenz_kalibrierung_regelwerk.md) -
# unter dieser Schwelle bekommt das Modell einen expliziten Ehrlichkeits-Hinweis,
# damit eine winzige Stichprobe nicht als starkes Signal fehlinterpretiert wird.
_MIN_SAMPLE_FUER_AUSSAGE = 15


def compute_win_rate_fact(conn, tier: str, erlaubte_symbole: set[str] | None = None) -> dict | None:
    """Grobe Gesamt-Trefferquote (2026-07-18, Item E) fuer `build_facts()`/
    `build_hebel_facts()` - liest bereits aufgeloeste Signale (take_profit_erreicht/
    stop_loss_erreicht, bei Hebel zusaetzlich liquidation_wahrscheinlich) aus
    signals ("spot") bzw. hebel_signals ("hebel"). BEWUSST nur eine einzige
    Gesamtzahl, kein Per-Regime-Split (Datenbasis dafuer noch zu duenn) - mit
    explizitem Ehrlichkeits-Hinweis bei kleiner Stichprobe. Reine Lesefunktion,
    kein Seiteneffekt. Gibt None zurueck, wenn noch gar keine ausgewerteten
    Signale (im gefilterten Symbol-Set) vorliegen (Prompt sollte den Fakt dann
    einfach weglassen).

    `erlaubte_symbole` (2026-07-18, Multi-Asset-Vollstaendigkeitspruefung):
    urspruenglich pool­te "spot" STILLSCHWEIGEND alle Symbole aus der signals-
    Tabelle, was nach Einfuehrung von Rohstoff-/Hedge-/Themen-ETF-Pipelines
    deren strukturell andersartige Signale (langsamer, andere Zyklen) OHNE
    bewusste Entscheidung in denselben Topf wie Krypto+Aktien warf. Krypto+
    Aktien bleiben bewusst gepoolt (fruehere, dokumentierte Entscheidung -
    aehnliches Momentum-/CRV-Profil), jede andere Assetklasse bekommt bei
    Uebergabe eines eigenen Symbol-Sets ihre EIGENE (anfangs meist leere,
    also None liefernde) Trefferquote statt einer fremden geliehenen Zahl.
    None (Default) = ungefiltert, wie bisher."""
    table = "signals" if tier == "spot" else "hebel_signals"
    placeholders = ", ".join("?" for _ in _RESOLVED_OUTCOMES)
    rows = conn.execute(
        f"SELECT symbol, outcome_status FROM {table} WHERE outcome_status IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    if erlaubte_symbole is not None:
        rows = [r for r in rows if r["symbol"] in erlaubte_symbole]
    total = len(rows)
    if total == 0:
        return None

    treffer = sum(1 for r in rows if r["outcome_status"] == OUTCOME_TAKE_PROFIT)
    fehlschlaege = total - treffer
    trefferquote_pct = round(100.0 * treffer / total, 1)

    if total < _MIN_SAMPLE_FUER_AUSSAGE:
        hinweis = (
            f"Basiert auf nur {total} bisher ausgewerteten Signalen - statistisch "
            "NICHT belastbar (Mindeststichprobe fuer eine verlaessliche Aussage: "
            f"{_MIN_SAMPLE_FUER_AUSSAGE}). Nur als sehr grobe Orientierung "
            "verwenden, keinesfalls die Konfidenz allein darauf stuetzen."
        )
    else:
        hinweis = f"Basiert auf {total} bisher ausgewerteten Signalen."

    return {
        "anzahl_ausgewertete_signale": total,
        "trefferquote_pct": trefferquote_pct,
        "treffer": treffer,
        "fehlschlaege": fehlschlaege,
        "hinweis": hinweis,
    }


def _konfidenz_bucket(confidence_pct: float) -> str:
    """Bucket-Grenzen bewusst identisch zu den bereits operativ genutzten
    Schwellen in risk_gate.py::post_check() (dort seit Item E fuer den
    "Konfidenz X%"-Risikofaktor in niedrig/mittel/hoch verwendet) - keine
    neu erfundenen Kalibrierungs-Baender, siehe Docstring von
    compute_konfidenz_kalibrierung()."""
    if confidence_pct < KONFIDENZ_SCHWELLE_NIEDRIG:
        return "niedrig"
    if confidence_pct >= KONFIDENZ_SCHWELLE_HOCH:
        return "hoch"
    return "mittel"


def compute_konfidenz_kalibrierung(conn, watchlist: list | None = None) -> dict:
    """Konfidenz-Kalibrierungskurve (2026-07-26, Punkt 3 des Regime-Persistenz-
    Folge-Vorschlags - siehe Memory project_regime_konflikt_makro_kennzahl.md).
    Beantwortet die Kernfrage der 2026er-LLM-Forecasting-Recherche dieser
    Session ("ist confidence_pct ueberhaupt kalibriert?") OHNE jede neue
    externe Datenquelle - nur bereits vorhandene, laengst gespeicherte Werte
    (confidence_pct zum Signalzeitpunkt + der spaeter tatsaechlich
    eingetretene Ausgang aus dem Backward-Tracking).

    Gruppiert alle bereits aufgeloesten Signale (_RESOLVED_OUTCOMES, wie
    compute_provider_performance()) nach (tier, konfidenz_bucket) und
    vergleicht je Bucket die durchschnittlich VORHERGESAGTE Konfidenz mit der
    tatsaechlichen Trefferquote (take_profit_count/anzahl - Liquidation zaehlt
    bei Hebel wie ueberall sonst im Projekt als Fehlschlag, nicht als Erfolg).
    Eine gute Kalibrierung zeigt sich darin, dass beide Werte je Bucket nahe
    beieinanderliegen (z. B. "hoch"-Bucket ~70-80% vorhergesagt UND ~70-80%
    tatsaechlich getroffen) - eine grosse `differenz_prozentpunkte` (vorher-
    gesagt minus tatsaechlich, positiv = Ueberschaetzung) waere ein Hinweis,
    dass die Prompt-Konfidenz nicht das haelt, was sie verspricht.

    Tier-Aufschluesselung identisch zu compute_provider_performance() (Spot
    optional nach Assetklasse via `watchlist`, Hebel immer gesondert - siehe
    dortiger Docstring fuer die Begruendung). Bucket-Grenzen siehe
    _konfidenz_bucket(). `ausreichend_stichprobe` je Bucket nutzt dieselbe
    _MIN_SAMPLE_FUER_AUSSAGE-Schwelle wie compute_win_rate_fact() - die
    Anzeige-Schicht soll Buckets darunter erkennbar als vorlaeufig markieren,
    nicht verschweigen (P-8: Transparenz statt stiller Fehlinterpretation).

    Reine Lesefunktion, kein Seiteneffekt."""
    gruppen: dict[tuple[str, str], dict] = {}
    assetklasse_by_symbol = {a.symbol: a.assetklasse for a in watchlist} if watchlist else {}

    def _stelle_sicher(tier: str, bucket: str) -> dict:
        key = (tier, bucket)
        if key not in gruppen:
            gruppen[key] = {"anzahl": 0, "take_profit_count": 0, "_konfidenz_summe": 0.0}
        return gruppen[key]

    placeholders = ", ".join("?" for _ in _RESOLVED_OUTCOMES)
    spot_rows = conn.execute(
        f"SELECT symbol, confidence_pct, outcome_status FROM signals "
        f"WHERE outcome_status IN ({placeholders}) AND confidence_pct IS NOT NULL",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in spot_rows:
        tier = assetklasse_by_symbol.get(row["symbol"], "unbekannt") if watchlist else "spot"
        eintrag = _stelle_sicher(tier, _konfidenz_bucket(row["confidence_pct"]))
        eintrag["anzahl"] += 1
        if row["outcome_status"] == OUTCOME_TAKE_PROFIT:
            eintrag["take_profit_count"] += 1
        eintrag["_konfidenz_summe"] += row["confidence_pct"]

    hebel_rows = conn.execute(
        f"SELECT confidence_pct, outcome_status FROM hebel_signals "
        f"WHERE outcome_status IN ({placeholders}) AND confidence_pct IS NOT NULL",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in hebel_rows:
        eintrag = _stelle_sicher("hebel", _konfidenz_bucket(row["confidence_pct"]))
        eintrag["anzahl"] += 1
        if row["outcome_status"] == OUTCOME_TAKE_PROFIT:
            eintrag["take_profit_count"] += 1
        eintrag["_konfidenz_summe"] += row["confidence_pct"]

    ergebnis: dict = {"hebel": {}} if watchlist else {"spot": {}, "hebel": {}}
    for (tier, bucket), eintrag in gruppen.items():
        anzahl = eintrag["anzahl"]
        avg_konfidenz = round(eintrag["_konfidenz_summe"] / anzahl, 1)
        tatsaechliche_trefferquote_pct = round(100.0 * eintrag["take_profit_count"] / anzahl, 1)
        ergebnis.setdefault(tier, {})[bucket] = {
            "anzahl": anzahl,
            "take_profit_count": eintrag["take_profit_count"],
            "avg_vorhergesagte_konfidenz_pct": avg_konfidenz,
            "tatsaechliche_trefferquote_pct": tatsaechliche_trefferquote_pct,
            "differenz_prozentpunkte": round(avg_konfidenz - tatsaechliche_trefferquote_pct, 1),
            "ausreichend_stichprobe": anzahl >= _MIN_SAMPLE_FUER_AUSSAGE,
        }

    return ergebnis


# Mindestziel-Preis/Zeitraum bei SIGNAL-ERSTELLUNG (2026-07-27, Nachtrag nach
# Nutzer-Rueckfrage "die Basiswerte muessten doch schon bei Signalerzeugung
# feststehen?"): anders als max_realisiertes_crv/mindestziel_erreicht_am oben
# (die koennen erst NACHTRAEGLICH per Backward-Tracking ermittelt werden - man
# kann nicht wissen, ob ein Ziel getroffen wurde, bevor Zeit vergangen ist) sind
# der Mindestziel-KURS und die Zeitschaetzung rein arithmetisch aus bereits beim
# Signal vorhandenen Werten (Entry/Stop-Loss, wie die bestehende Take-Profit-
# Zone) - stehen SOFORT fest und werden von der Pipeline direkt auf das Signal
# geschrieben (mindestziel_usd/mindestziel_zeitraum_tage_geschaetzt), damit GUI/
# E-Mail sie beim Erzeugen des Signals zusammen mit Entry/Stop-Loss/Take-Profit
# zeigen koennen - kein Warten auf das Backward-Tracking noetig.
DEFAULT_ZEITRAUM_SCHAETZUNG_TAGE_FENSTER = 14


def _durchschnittliche_tagesspanne(
    ohlc_rows, fenster_tage: int = DEFAULT_ZEITRAUM_SCHAETZUNG_TAGE_FENSTER,
) -> float | None:
    """Durchschnittliche Tages-High-Low-Spanne der letzten `fenster_tage` bereits
    vorliegenden OHLC-Zeilen (chronologisch aufsteigend erwartet, wie ueberall
    sonst in diesem Modul) - Grundlage der Random-Walk-Zeitschaetzung unten.
    Rein deskriptiv aus real vorliegenden Daten, keine Prognose."""
    relevante = [r for r in ohlc_rows if r.high is not None and r.low is not None][-fenster_tage:]
    if len(relevante) < 2:
        return None
    spannen = [r.high - r.low for r in relevante]
    avg = sum(spannen) / len(spannen)
    return avg if avg > 0 else None


def mindestziel_preis(
    entry_mid: float | None, risiko_distanz: float | None,
    richtungstreffer_mindest_crv: float = DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    ist_short: bool = False,
) -> float | None:
    """Mindestziel-Kurs (Min-Kurs bei LONG/Spot, entsprechend gespiegelt bei
    Hebel-SHORT) - dieselbe Distanz wie der Stop-Loss, nur in die guenstige
    Richtung (CRV=richtungstreffer_mindest_crv). Rein arithmetisch aus bereits
    vorhandenen Entry-/Stop-Loss-Werten - siehe Modul-Docstring-Nachtrag oben."""
    if entry_mid is None or risiko_distanz is None or risiko_distanz <= 0:
        return None
    if ist_short:
        return entry_mid - richtungstreffer_mindest_crv * risiko_distanz
    return entry_mid + richtungstreffer_mindest_crv * risiko_distanz


def schaetze_mindestziel_zeitraum_tage(
    ziel_preis: float | None, entry_mid: float | None, ohlc_rows,
) -> float | None:
    """Rechnerisch ANGENOMMENE Anzahl Tage bis zum Mindestziel - Kursdistanz zum
    Ziel geteilt durch die durchschnittliche Tagesspanne (High-Low) der letzten
    DEFAULT_ZEITRAUM_SCHAETZUNG_TAGE_FENSTER bereits gehandelten Tage vor
    Signal-Erstellung (Random-Walk-Annahme: erwartete Tage = Distanz / typische
    Tagesbewegung). KEIN Versprechen, kann verfehlt werden - GUI/E-Mail muessen
    das explizit als 'angenommen' kennzeichnen, solange keine belastbare
    empirische Ø-Tage-Zahl vorliegt (siehe compute_richtungstreffer_quote())."""
    if ziel_preis is None or entry_mid is None:
        return None
    distanz = abs(ziel_preis - entry_mid)
    if distanz == 0:
        return 0.0
    avg_tagesspanne = _durchschnittliche_tagesspanne(ohlc_rows)
    if avg_tagesspanne is None:
        return None
    return round(distanz / avg_tagesspanne, 1)


def compute_richtungstreffer_quote(
    conn, tier: str, richtungstreffer_mindest_crv: float = DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
    erlaubte_symbole: set[str] | None = None,
) -> dict | None:
    """Richtungstreffer-Quote (2026-07-27, Performance-Messung-Expertenanalyse -
    siehe project_performance_messung_backtracking_expertenanalyse.md): unabhaengig
    von der exakten TP/SL-Zonen-Ausfuehrung - wie oft war die Richtung wenigstens
    zeitweise (Maximum Favorable Excursion) mindestens richtungstreffer_mindest_crv
    wert? BREITER gefasst als compute_win_rate_fact() (_RESOLVED_OUTCOMES) - zaehlt
    JEDES Signal mit outcome_max_realisiertes_crv IS NOT NULL, also auch spaeter
    ueberholte/abgelaufene, die trotzdem eine Zeitlang in die richtige Richtung
    liefen. Ø-Tage-bis-Mindestziel nur bei n>=_MIN_SAMPLE_FUER_AUSSAGE als
    belastbar markiert - GUI/E-Mail sollen sonst den rechnerisch angenommenen Wert
    aus schaetze_mindestziel_zeitraum_tage() zeigen, nicht diesen. Reine
    Lesefunktion, kein Seiteneffekt."""
    table = "signals" if tier == "spot" else "hebel_signals"
    rows = conn.execute(
        f"SELECT symbol, created_at, outcome_max_realisiertes_crv, outcome_mindestziel_erreicht_am "
        f"FROM {table} WHERE outcome_max_realisiertes_crv IS NOT NULL",
    ).fetchall()
    if erlaubte_symbole is not None:
        rows = [r for r in rows if r["symbol"] in erlaubte_symbole]
    total = len(rows)
    if total == 0:
        return None

    treffer_rows = [r for r in rows if r["outcome_max_realisiertes_crv"] >= richtungstreffer_mindest_crv]
    treffer = len(treffer_rows)
    quote_pct = round(100.0 * treffer / total, 1)

    tage_liste = []
    for r in treffer_rows:
        if not r["outcome_mindestziel_erreicht_am"]:
            continue
        try:
            erstellt = _parse_dt(r["created_at"])
            erreicht = _parse_dt(r["outcome_mindestziel_erreicht_am"])
        except ValueError:
            continue
        tage_liste.append((erreicht - erstellt).total_seconds() / 86400)

    ausreichend_stichprobe = len(tage_liste) >= _MIN_SAMPLE_FUER_AUSSAGE
    avg_tage = round(sum(tage_liste) / len(tage_liste), 1) if tage_liste else None

    return {
        "anzahl_ausgewertet": total,
        "richtungstreffer": treffer,
        "richtungstreffer_quote_pct": quote_pct,
        "avg_tage_bis_mindestziel": avg_tage if ausreichend_stichprobe else None,
        "avg_tage_bis_mindestziel_stichprobe_n": len(tage_liste),
        "ausreichend_stichprobe": ausreichend_stichprobe,
    }
