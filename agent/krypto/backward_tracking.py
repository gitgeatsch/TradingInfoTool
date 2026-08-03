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

import logging
import math
import random
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import database.db as db
from agent.krypto.llm_provider import provider_from_label
from agent.krypto.statistik import beitrags_konzentration, wilson_intervall
from agent.krypto.risk_gate import CRV_MINIMUM, KONFIDENZ_SCHWELLE_HOCH, KONFIDENZ_SCHWELLE_NIEDRIG

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

logger = logging.getLogger(__name__)

# --- Tier-Schluessel der Aggregationen (2026-08-02, Task #561) --------------
# Alle compute_*-Aggregationen gruppieren nach (tier, provider|grund). Spot-
# family-Signale werden dabei nach asset.assetklasse aufgeschluesselt, Hebel-
# Signale bilden einen eigenen Topf. Bis heute stand die Zuordnungslogik als
# identischer Einzeiler an ZEHN Stellen - eine Aenderung haette an neun davon
# vergessen werden koennen.
TIER_HEBEL = "hebel"
# Sammel-Topf, wenn keine Watchlist vorliegt: dann ist keine Aufschluesselung
# moeglich und alle Spot-family-Signale landen zusammen. Der Schluessel heisst
# bewusst weiterhin "spot" - remote/server.py::SPOT_ASSETKLASSEN rendert ihn
# nicht, wodurch der Ausfall in der Anzeige als leere Karte sichtbar wird
# statt als falsch beschriftete Zahl.
TIER_SPOT_SAMMEL = "spot"
# Symbol ist (nicht mehr) in der Watchlist - typischerweise nach Ausmusterung.
TIER_UNBEKANNT = "unbekannt"


def _tier_geruest(watchlist: list | None) -> dict:
    """Leeres Ergebnis-Geruest der Aggregationen.

    Der Hebel-Topf existiert immer. Der Spot-Sammel-Topf wird nur vorangelegt,
    wenn KEINE Watchlist vorliegt - mit Watchlist entstehen stattdessen die
    einzelnen Assetklassen-Toepfe erst beim Befuellen, damit eine leere
    Assetklasse nicht als "0 Signale" erscheint, wo remote/server.py sie
    ohnehin aus seiner festen Liste rendert."""
    if watchlist:
        return {TIER_HEBEL: {}}
    return {TIER_SPOT_SAMMEL: {}, TIER_HEBEL: {}}


def _tabelle_fuer_tier(tier: str, funktionsname: str) -> str:
    """Signal-Tabelle zu einem tier - strikt, ohne Auffang-Zweig.

    Bis 2026-08-02 stand an fuenf Stellen `"signals" if tier == "spot" else
    "hebel_signals"`. Damit las JEDER andere Wert die Hebel-Tabelle: "krypto",
    "aktien", ein Tippfehler, None. Das ist deshalb heikel, weil die
    Aggregationen desselben Moduls genau solche tiers erzeugen
    (Assetklassen-Aufschluesselung seit 2026-07-20) - wer sie hier einsetzt,
    bekaeme lautlos Hebel-Zahlen unter Spot-Beschriftung, dazu die nur fuer
    Hebel gedachten CRV-Break-even- und Regime-Vergleiche.

    Bewusst ValueError statt Warnung+Fallback: ein Absturz beim Entwickeln ist
    harmlos, eine falsche Zahl in einer Auswertung nicht (Projektpraeferenz
    "harte Garantie statt Soft-Boost"). Alle heutigen Aufrufer uebergeben
    String-Literale, koennen also nicht versehentlich hineinlaufen."""
    if tier == TIER_SPOT_SAMMEL:
        return "signals"
    if tier == TIER_HEBEL:
        return "hebel_signals"
    raise ValueError(
        f"{funktionsname}: unbekanntes tier {tier!r}. Erlaubt sind nur "
        f"{TIER_SPOT_SAMMEL!r} (Tabelle signals) und {TIER_HEBEL!r} "
        f"(hebel_signals). Assetklassen-Schluessel wie 'krypto'/'aktien' aus "
        f"den compute_*-Aggregationen sind hier NICHT gueltig - fuer eine "
        f"Einschraenkung auf einzelne Assetklassen den Parameter "
        f"erlaubte_symbole verwenden."
    )


def _assetklasse_index(watchlist: list | None, kontext: str) -> dict[str, str]:
    """Symbol -> assetklasse. Meldet LAUT, wenn die Watchlist fehlt.

    Warum diese Warnung existiert: am 2026-07-29 wurden sieben dieser
    Aggregationen im Notebook-Export ohne `watchlist` aufgerufen. Die Folge war
    kein Fehler, sondern ein plausibel aussehendes Ergebnis - saemtliche
    Spot-family-Signale (Krypto/Aktien/Rohstoffe/ETF) in einem einzigen Topf,
    wodurch bei einer Muster-Analyse nicht mehr unterscheidbar war, ob ein
    Befund krypto-spezifisch war oder alle Assetklassen betraf. Der Aufruf
    wurde damals korrigiert (siehe Kopfkommentar in
    extract_notebook_diagnose.py), die Konstruktion aber nicht: der Parameter
    ist weiterhin optional und degradiert still. Diese Warnung macht einen
    Rueckfall hoerbar, statt ihn erst Wochen spaeter in einer Auswertung
    auffallen zu lassen."""
    if not watchlist:
        logger.warning(
            "%s ohne watchlist aufgerufen - keine Assetklassen-Aufschluesselung "
            "moeglich, alle Spot-family-Signale landen im Sammel-Topf '%s'. "
            "Zahlen aus dieser Auswertung NICHT als krypto-spezifisch lesen.",
            kontext,
            TIER_SPOT_SAMMEL,
        )
        return {}
    return {a.symbol: a.assetklasse for a in watchlist}


def _tier_fuer_spot_symbol(symbol: str, assetklasse_by_symbol: dict[str, str]) -> str:
    """Tier-Schluessel eines Spot-family-Signals (Hebel hat seinen eigenen).

    Drei Faelle, alle bewusst unterschieden statt in einen Default zu fallen:
    leerer Index (keine Watchlist - siehe _assetklasse_index()), Symbol nicht
    gefunden (ausgemustert), und der Normalfall."""
    if not assetklasse_by_symbol:
        return TIER_SPOT_SAMMEL
    klasse = assetklasse_by_symbol.get(symbol)
    if not klasse:
        return TIER_UNBEKANNT
    if klasse == TIER_HEBEL:
        # Kollisionsschutz: eine Assetklasse namens "hebel" wuerde sonst
        # lautlos mit dem Hebel-Topf derselben Aggregation verschmelzen und
        # Spot-Zahlen in die Hebel-Auswertung mischen. Aktuell existiert keine
        # solche Assetklasse (krypto|aktien|etf|rohstoffe) - der Zweig kostet
        # nichts und schliesst einen sehr schwer auffindbaren Fehler aus.
        return f"spot_{klasse}"
    return klasse


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
    # Selbst-gewaehltes-HALTEN-Schatten-Tracking (2026-07-31, siehe
    # _hat_selbst_halten_these()-Docstring) - Gegenfall zum Veto-Schatten
    # oben: kein Gate/Veto, das LLM hat sich selbst gegen einen Trade
    # entschieden, aber trotzdem eine hypothetische Zone angegeben.
    selbst_halten_geprueft_count: int = 0
    selbst_halten_take_profit: int = 0
    selbst_halten_stop_loss: int = 0
    selbst_halten_expired: int = 0
    selbst_halten_still_open: int = 0


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

    def _check_preis(high: float, low: float) -> tuple[bool, bool]:
        """Gibt (hit_take, hit_stop) zurueck - SHORT spiegelt Take-Profit/Stop-Loss
        gegenueber LONG (Take-Profit unten, Stop-Loss oben). Der Ausfuehrungspreis
        kommt seit dem 02.08. aus gap_bewusster_fill(), nicht mehr aus dem
        Tages-Extremwert (Begruendung dort)."""
        if ist_short:
            return low <= take_profit_threshold, high >= stop_loss_threshold
        return high >= take_profit_threshold, low <= stop_loss_threshold

    ohlc_rows = db.get_ohlc_history(conn, signal.symbol, "USD", min_date=min_date)
    if len(ohlc_rows) >= 1:
        datenquelle = "real"
        for row in ohlc_rows:
            day = row.date
            guenstigster_tagespreis = row.low if ist_short else row.high
            _erfasse_mfe(guenstigster_tagespreis, day)
            hit_take, hit_stop = _check_preis(row.high, row.low)
            if hit_stop:
                # Konservativ (Z-1: Kapitalerhalt vor Gewinn): trifft ein Tag beide
                # Zonen, gewinnt Stop-Loss - keine Annahme ueber die Intraday-
                # Reihenfolge ohne Tick-Daten.
                return resolve(gap_bewusster_fill(
                    stop_loss_threshold, row.open, ist_stop=True, ist_short=ist_short,
                ), hit_take=False)
            if hit_take:
                return resolve(gap_bewusster_fill(
                    take_profit_threshold, row.open, ist_stop=False, ist_short=ist_short,
                ), hit_take=True)
    else:
        datenquelle = "proxy"
        price_rows = db.get_price_history(conn, asset.coingecko_id, min_date=min_date) if asset.coingecko_id else []
        for row in price_rows:
            if row.price_usd is None:
                continue
            day = row.date
            _erfasse_mfe(row.price_usd, day)
            hit_take, hit_stop = _check_preis(row.price_usd, row.price_usd)
            if hit_stop:
                return resolve(stop_loss_threshold, hit_take=False)
            if hit_take:
                return resolve(take_profit_threshold, hit_take=True)

    # Kein Treffer gefunden - offen oder abgelaufen, je nach Alter.
    return OUTCOME_OFFEN, {
        "max_realisiertes_crv": max_favorable_crv,
        "mindestziel_erreicht_am": mindestziel_erreicht_am,
    }


def gap_bewusster_fill(schwelle: float, open_preis: float | None,
                       ist_stop: bool, ist_short: bool) -> float:
    """Ausfuehrungspreis beim Treffen einer Zonen-Schwelle (2026-08-02, Task #604).

    Grundregel ist der Schwellwert selbst: eine Stop- oder Limit-Order fuellt
    dort, nicht am Tagesextrem. Ausnahme ist ein Gap - eroeffnet der Tag bereits
    jenseits der Schwelle, kommt die Order erst zum Eroeffnungskurs zum Zug.
    Bei einem Stop ist das schlechter als geplant, bei einem Take-Profit besser.

    Vorgeschichte: bis zum 02.08. nahm die Spot-Seite den tatsaechlichen
    Tages-Extremwert (Hoch bei Take, Tief bei Stop), die Hebel-Seite den
    Schwellwert. Die Spot-Variante entsprach der Doku vom 10.07. ("mit dem
    tatsaechlich erreichten Kurs statt der Zonen-Grenze"), war aber in sich
    widerspruechlich: Stop zum Tagestief ist pessimistisch, Take zum Tageshoch
    optimistisch - die Kombination blaeht genau die Streuung auf, die der SQN
    bestraft. Gemessen am Export vom 02.08. lagen Spot-Verluste dadurch bei
    -1,19 R im Mittel statt -1,00 R (n=7), Hebel exakt bei -1,000 R (n=70).

    Die Absicht hinter der alten Konvention - abbilden, wie weit der Markt
    tatsaechlich gelaufen ist - stammt vom 10.07. und damit 17 Tage VOR dem
    MFE-Feld (max_realisiertes_crv, 27.07.). Diese Rolle hat heute ein eigenes
    Feld; realisiertes_crv soll das Ausfuehrungsergebnis abbilden.

    Gap-Haeufigkeit in den eigenen Daten (Export 02.08.): 1 von 49 pruefbaren
    Hebel-Stops (Gap 2,0%), 2 von 11 Take-Profits, bei Spot 0 von 6. Selten,
    aber nicht null - und fuer Aktien/Themen-ETFs mit echten Wochenendluecken
    strukturell haeufiger als bei durchgehend gehandelten Kryptowerten.

    `open_preis=None` (Proxy-Zweig ohne OHLC, nur Tagesschlusskurs) faellt auf
    den Schwellwert zurueck - ohne Eroeffnungskurs ist ein Gap nicht erkennbar.
    """
    if open_preis is None or open_preis <= 0:
        return schwelle
    # Unguenstige Richtung: LONG-Stop und SHORT-Take liegen unterhalb,
    # LONG-Take und SHORT-Stop oberhalb der Schwelle.
    if ist_stop != ist_short:
        return min(schwelle, open_preis)
    return max(schwelle, open_preis)


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


def _hat_selbst_halten_these(signal) -> bool:
    """Diskriminator fuer einen echten Selbst-Halten-Schatten-Kandidaten
    (2026-07-31, Ergaenzung zu _hat_veto_schatten_these() oben - siehe
    dortigen Docstring fuer den Gegenfall): `ist_reines_llm_halten == True`
    (bereits deterministisch bei der Generierung berechnet, siehe
    risk_gate.py::post_check()) UND alle drei Preiszonen (Entry/Stop-Loss/
    Take-Profit) gesetzt."""
    if not getattr(signal, "ist_reines_llm_halten", False):
        return False
    entry = _entry_mid(signal)
    stop = _threshold(signal.stop_loss_usd_von, signal.stop_loss_usd)
    take = _threshold(signal.take_profit_usd_von, signal.take_profit_usd)
    return entry is not None and stop is not None and take is not None


def _richtung_aus_zonen(signal) -> str | None:
    """Bestimmt LONG/SHORT-Orientierung rein aus der relativen Zonen-
    Reihenfolge (Stop-Loss vs. Entry) - fuer Veto-Schatten- UND Selbst-
    Halten-Schatten-Kandidaten gleichermassen nutzbar, da `action` in beiden
    Faellen bereits auf HALTEN steht und richtung_aus_action() (agent/krypto/
    gegenpruefung.py) daher None liefern wuerde. Spiegelt dieselbe implizite
    Logik, die risk_gate.py::post_check() fuer die CRV-Pflicht-Vetos bereits
    nutzt (_BUY_ACTIONS verlangt entry>stop_von, _SELL_ACTIONS verlangt
    stop_bis>entry): Stop-Loss UEBER dem Entry bedeutet SHORT-Orientierung
    (Stop-Loss oben, wie bei check_signal_outcome()s ist_short-Zweig),
    Stop-Loss UNTER dem Entry bedeutet LONG. None, wenn Entry/Stop-Loss
    fehlen oder identisch sind (keine eindeutige Richtung ableitbar)."""
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
    aus _richtung_aus_zonen() statt richtung_aus_action(), weil `action`
    hier bereits auf HALTEN steht. Gibt (neuer_status, extra_felder) zurueck,
    extra_felder passend fuer db.update_signal_veto_shadow_outcome(**extra_felder)
    (bewusst OHNE 'datenquelle'-Key - dieses Feld wird im Schatten-Zweig nicht
    gespiegelt, siehe dortiger Docstring)."""
    if not _hat_veto_schatten_these(signal):
        return OUTCOME_NICHT_ANWENDBAR, {}

    ist_short = _richtung_aus_zonen(signal) == "SHORT"

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

    def _check_preis(high: float, low: float) -> tuple[bool, bool]:
        if ist_short:
            return low <= take_profit_threshold, high >= stop_loss_threshold
        return high >= take_profit_threshold, low <= stop_loss_threshold

    ohlc_rows = db.get_ohlc_history(conn, signal.symbol, "USD", min_date=min_date)
    if len(ohlc_rows) >= 1:
        for row in ohlc_rows:
            day = row.date
            guenstigster_tagespreis = row.low if ist_short else row.high
            _erfasse_mfe(guenstigster_tagespreis, day)
            hit_take, hit_stop = _check_preis(row.high, row.low)
            if hit_stop:
                return resolve(gap_bewusster_fill(
                    stop_loss_threshold, row.open, ist_stop=True, ist_short=ist_short,
                ), hit_take=False)
            if hit_take:
                return resolve(gap_bewusster_fill(
                    take_profit_threshold, row.open, ist_stop=False, ist_short=ist_short,
                ), hit_take=True)
    else:
        price_rows = db.get_price_history(conn, asset.coingecko_id, min_date=min_date) if asset.coingecko_id else []
        for row in price_rows:
            if row.price_usd is None:
                continue
            day = row.date
            _erfasse_mfe(row.price_usd, day)
            hit_take, hit_stop = _check_preis(row.price_usd, row.price_usd)
            if hit_stop:
                return resolve(stop_loss_threshold, hit_take=False)
            if hit_take:
                return resolve(take_profit_threshold, hit_take=True)

    return OUTCOME_OFFEN, {
        "max_realisiertes_crv": max_favorable_crv,
        "mindestziel_erreicht_am": mindestziel_erreicht_am,
    }


def check_signal_selbst_halten_outcome(
    conn, signal, watchlist, richtungstreffer_mindest_crv: float = DEFAULT_RICHTUNGSTREFFER_MINDEST_CRV,
) -> tuple[str, dict]:
    """Wie check_signal_veto_shadow_outcome(), aber fuer den Zweig "selbst
    gewaehltes HALTEN" (2026-07-31, siehe _hat_selbst_halten_these()-
    Docstring): trackt Signale, bei denen das LLM sich OHNE Gate/Veto von
    sich aus gegen einen Trade entschieden hat, aber trotzdem eine
    hypothetische Zone angegeben hat - beantwortet die Frage "war die eigene
    Zurueckhaltung im Nachhinein richtig?", getrennt vom Veto-Schatten-Zweig
    (dort hat das Gate entschieden, hier das LLM selbst).

    Identische TP/SL/MFE-Mechanik wie check_signal_veto_shadow_outcome(),
    inkl. Richtungsableitung ueber _richtung_aus_zonen() (auch hier steht
    `action` bereits auf HALTEN). Gibt (neuer_status, extra_felder) zurueck,
    passend fuer db.update_signal_selbst_halten_outcome(**extra_felder)."""
    if not _hat_selbst_halten_these(signal):
        return OUTCOME_NICHT_ANWENDBAR, {}

    ist_short = _richtung_aus_zonen(signal) == "SHORT"

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

    def _check_preis(high: float, low: float) -> tuple[bool, bool]:
        if ist_short:
            return low <= take_profit_threshold, high >= stop_loss_threshold
        return high >= take_profit_threshold, low <= stop_loss_threshold

    ohlc_rows = db.get_ohlc_history(conn, signal.symbol, "USD", min_date=min_date)
    if len(ohlc_rows) >= 1:
        for row in ohlc_rows:
            day = row.date
            guenstigster_tagespreis = row.low if ist_short else row.high
            _erfasse_mfe(guenstigster_tagespreis, day)
            hit_take, hit_stop = _check_preis(row.high, row.low)
            if hit_stop:
                return resolve(gap_bewusster_fill(
                    stop_loss_threshold, row.open, ist_stop=True, ist_short=ist_short,
                ), hit_take=False)
            if hit_take:
                return resolve(gap_bewusster_fill(
                    take_profit_threshold, row.open, ist_stop=False, ist_short=ist_short,
                ), hit_take=True)
    else:
        price_rows = db.get_price_history(conn, asset.coingecko_id, min_date=min_date) if asset.coingecko_id else []
        for row in price_rows:
            if row.price_usd is None:
                continue
            day = row.date
            _erfasse_mfe(row.price_usd, day)
            hit_take, hit_stop = _check_preis(row.price_usd, row.price_usd)
            if hit_stop:
                return resolve(stop_loss_threshold, hit_take=False)
            if hit_take:
                return resolve(take_profit_threshold, hit_take=True)

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


def persistiere_offenes_mfe(conn, signal_id: int, extra: dict,
                           gespeichertes_mfe: float | None, update_fn) -> None:
    """MFE auch bei noch OFFENEM Signal festhalten (2026-08-02, Task #602).

    check_*_outcome() berechnet den Maximum-Favorable-Excursion-Wert bei jedem
    Lauf neu ueber die volle Historie seit created_at - bisher wurde er nur
    dann geschrieben, wenn zugleich ein Endstatus feststand (aufgeloest,
    ueberholt, abgelaufen). Folge: MFE existierte ausschliesslich fuer
    abgeschlossene Faelle - also genau fuer die selektierte Teilmenge, gegen
    deren Survivorship-Verzerrung die Kennzahl eigentlich helfen soll.

    Gemessen am Export vom 02.08.: 52 von 881 Hebel-Signalen mit Zonen hatten
    einen MFE-Wert, gegenueber 382 aufgeloesten. Die Kennzahl war duenner als
    das Problem, das sie loesen sollte.

    Schreibt nur bei tatsaechlicher Aenderung: MFE ist ein Maximum und bewegt
    sich selten: ein bedingungsloses UPDATE je Lauf waere ein Schreibsturm
    ueber mehrere tausend offene Signale (update_*_outcome() committet einzeln).

    Der Status bleibt bewusst OUTCOME_OFFEN - die Zeile bleibt damit in der
    Selektion des naechsten Laufs (`... IS NULL OR ... = 'offen'`)."""
    neuer_mfe = extra.get("max_realisiertes_crv")
    if neuer_mfe is None or neuer_mfe == gespeichertes_mfe:
        return
    update_fn(
        conn, signal_id, OUTCOME_OFFEN,
        max_realisiertes_crv=neuer_mfe,
        mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
    )


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
            persistiere_offenes_mfe(
                conn, signal.id, extra, signal.outcome_max_realisiertes_crv,
                db.update_signal_outcome,
            )
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
            persistiere_offenes_mfe(
                conn, signal.id, extra, signal.veto_outcome_max_realisiertes_crv,
                db.update_signal_veto_shadow_outcome,
            )
            result.veto_schatten_still_open += 1

    # Selbst-gewaehltes-HALTEN-Zweig (2026-07-31, Gegenfall zum Veto-Schatten-
    # Zweig oben - siehe check_signal_selbst_halten_outcome()-Docstring).
    # Bewusst OHNE Ueberholt-Check, gleiche Begruendung wie beim Veto-
    # Schatten-Zweig: eine hypothetische, nie ausgefuehrte These kann durch
    # eine neuere echte Analyse nicht im selben Sinn "ueberholt" werden.
    selbst_halten_rows = conn.execute(
        "SELECT id FROM signals WHERE ist_reines_llm_halten = 1 "
        "AND (selbst_halten_outcome_status IS NULL OR selbst_halten_outcome_status = ?)",
        (OUTCOME_OFFEN,),
    ).fetchall()

    for row in selbst_halten_rows:
        signal = db.get_signal_by_id(conn, row["id"])
        if signal is None:
            continue
        result.selbst_halten_geprueft_count += 1

        status, extra = check_signal_selbst_halten_outcome(conn, signal, watchlist, richtungstreffer_mindest_crv)

        if status == OUTCOME_NICHT_ANWENDBAR:
            db.update_signal_selbst_halten_outcome(conn, signal.id, status)
            continue

        if status in (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS):
            db.update_signal_selbst_halten_outcome(
                conn, signal.id, status,
                entschieden_am=extra.get("entschieden_am"),
                realisiertes_crv=extra.get("realisiertes_crv"),
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            if status == OUTCOME_TAKE_PROFIT:
                result.selbst_halten_take_profit += 1
            else:
                result.selbst_halten_stop_loss += 1
            continue

        if _is_expired(signal, bucket_tage, fallback_tage):
            db.update_signal_selbst_halten_outcome(
                conn, signal.id, OUTCOME_ABGELAUFEN,
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
            )
            result.selbst_halten_expired += 1
        else:
            persistiere_offenes_mfe(
                conn, signal.id, extra, signal.selbst_halten_outcome_max_realisiertes_crv,
                db.update_signal_selbst_halten_outcome,
            )
            result.selbst_halten_still_open += 1

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
    assetklasse_by_symbol = _assetklasse_index(watchlist, "_aggregate_resolved_signal_rows()")

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
                # Einzelwerte zusaetzlich zur Summe: der Mittelwert allein
                # verraet nicht, ob er an wenigen Ausreissern haengt
                # (Methodik 2.5.5). Fuer den Beitrags-Check gebraucht.
                "_crv_werte": [],
            }
        return gruppen[key]

    placeholders = ", ".join("?" for _ in _RESOLVED_OUTCOMES)
    spot_rows = conn.execute(
        f"SELECT symbol, groq_model AS llm_model, {status_col} AS status, {crv_col} AS crv "
        f"FROM signals WHERE {filter_clause}{status_col} IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in spot_rows:
        tier = _tier_fuer_spot_symbol(row["symbol"], assetklasse_by_symbol)
        eintrag = _stelle_sicher(tier, provider_from_label(row["llm_model"]))
        eintrag["anzahl_resolved"] += 1
        if row["status"] == OUTCOME_TAKE_PROFIT:
            eintrag["take_profit_count"] += 1
        elif row["status"] == OUTCOME_STOP_LOSS:
            eintrag["stop_loss_count"] += 1
        if row["crv"] is not None:
            eintrag["_crv_summe"] += row["crv"]
            eintrag["_crv_count"] += 1
            eintrag["_crv_werte"].append(row["crv"])

    hebel_rows = conn.execute(
        f"SELECT llm_model, {status_col} AS status, {crv_col} AS crv "
        f"FROM hebel_signals WHERE {filter_clause}{status_col} IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in hebel_rows:
        eintrag = _stelle_sicher(TIER_HEBEL, provider_from_label(row["llm_model"]))
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
            eintrag["_crv_werte"].append(row["crv"])

    return gruppen


def _kennzahlen_mit_pruefung(eintrag: dict) -> dict:
    """Kennzahlen einer Gruppe - mit den beiden Pruefungen direkt daneben.

    Bis 2026-08-02 lieferten die Aggregationen nur `win_rate` und
    `avg_realisiertes_crv`. Beide Zahlen wurden dadurch regelmaessig
    ueberinterpretiert: eine Trefferquote von 40% bei n=10 sah aus wie eine
    von 40% bei n=200, und ein positiver Mittelwert sagte nichts darueber,
    ob er an drei Ausreissern hing. An genau diesen zwei Luecken sind an
    jenem Tag fuenf von sieben Befunden gescheitert - die Pruefungen dafuer
    standen bis dahin nur als Text in der Methodik und mussten jedes Mal von
    Hand nachgezogen werden. Jetzt laufen sie automatisch mit.

    Zwei Zusatzfelder:
    - `win_rate_ci_95`: Wilson-Intervall. Macht den Unterschied zwischen
      "40% aus 10 Faellen" und "40% aus 200 Faellen" sofort sichtbar.
    - `crv_konzentration`: Beitrags-Check (Methodik 2.5.5). Entscheidend
      darin ist `vorzeichen_kippt` - faellt der Mittelwert ohne die fuenf
      groessten Werte auf die andere Seite der Null, ist die Kennzahl NICHT
      belastbar, egal wie gut die Anzahl-Verteilung aussieht.
    """
    anzahl = eintrag["anzahl_resolved"]
    crv_werte = eintrag.get("_crv_werte") or []
    return {
        "anzahl_resolved": anzahl,
        "take_profit_count": eintrag["take_profit_count"],
        "stop_loss_count": eintrag["stop_loss_count"],
        "liquidation_count": eintrag["liquidation_count"],
        "win_rate": (eintrag["take_profit_count"] / anzahl) if anzahl > 0 else None,
        "win_rate_ci_95": (
            wilson_intervall(eintrag["take_profit_count"], anzahl) if anzahl > 0 else None
        ),
        "avg_realisiertes_crv": (
            eintrag["_crv_summe"] / eintrag["_crv_count"] if eintrag["_crv_count"] > 0 else None
        ),
        # Unter 6 Werten ist ein Top-5-Beitrag keine Aussage, sondern fast
        # die ganze Stichprobe - dann bleibt das Feld bewusst leer.
        "crv_konzentration": (
            beitrags_konzentration(crv_werte) if len(crv_werte) >= 6 else None
        ),
    }


def _format_performance_gruppen(gruppen: dict[tuple[str, str], dict], watchlist: list | None) -> dict:
    ergebnis: dict = _tier_geruest(watchlist)
    for (tier, provider), eintrag in gruppen.items():
        ergebnis.setdefault(tier, {})[provider] = _kennzahlen_mit_pruefung(eintrag)
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


VETO_GRUND_KONFIDENZSCHWELLE = "konfidenzschwelle_r510"
VETO_GRUND_CRV = "crv_unter_minimum"
VETO_GRUND_SONSTIGE = "sonstige"


def _kategorisiere_veto_grund(reason: str | None) -> str:
    """Klassifiziert `risk_veto_reason`/hebel-Pendant in eine von drei groben
    Kategorien (2026-07-30, R-5.10-Konfidenzschwellen-Nachtrag - siehe Memory
    project_llm_optimierung_abdeckung_pruefung). Textbasiert statt eines
    eigenen Enum-Felds, da der Veto-Grund bisher NUR als Freitext gespeichert
    wird (risk_gate.py::post_check()/hebel_risk_gate.py::post_check_hebel()) -
    beide Texte enthalten die charakteristischen Substrings zuverlaessig
    ("Regime-Mindestschwelle...% (R-5.10)" bzw. "CRV ... unter Minimum").
    Mehrere Veto-Gruende koennen im selben Feld aneinandergehaengt sein
    (siehe post_check(): `f"{risk_veto_reason}; {reason}"`) - hier wird
    bewusst NUR der ERSTE erkannte Grund gewertet (Prioritaet: Konfidenz vor
    CRV), da eine doppelte Zaehlung in mehreren Kategorien die Aggregation
    verfaelschen wuerde."""
    if not reason:
        return VETO_GRUND_SONSTIGE
    if "Regime-Mindestschwelle" in reason:
        return VETO_GRUND_KONFIDENZSCHWELLE
    if "CRV" in reason:
        return VETO_GRUND_CRV
    return VETO_GRUND_SONSTIGE


def compute_veto_shadow_performance_nach_grund(conn, watchlist: list | None = None) -> dict:
    """Wie compute_veto_shadow_performance(), aber gruppiert nach (tier,
    veto_grund) statt (tier, provider) (2026-07-30, R-5.10-Konfidenzschwellen-
    Nachtrag - siehe Memory project_llm_optimierung_abdeckung_pruefung fuer
    die volle Herleitung). Der Provider ist fuer eine Schwellen-Entscheidung
    nicht die relevante Dimension - der Veto-GRUND ist es: schlagen sich
    Konfidenzschwellen-Vetos (R-5.10) anders als CRV<2.0-Vetos, und
    unterscheidet sich das je Assetklasse? Bewusst eine KOMPLETT SEPARATE
    Funktion (Option B, wie im gesamten Modul ueblich) statt eines
    Parameters an compute_veto_shadow_performance() - dieselbe Begruendung
    wie dort (ein Konsument, der nur die Provider-Sicht braucht, muss sich
    nicht mit der Veto-Grund-Dimension befassen).

    Ergebnis war die direkte Grundlage fuer die config.yaml::regime.
    min_konfidenz_prozent_krypto_spot_override-Entscheidung: Krypto-Spot
    hatte bei Konfidenzschwellen-Vetos eine belastbare Stichprobe (n>=50)
    mit leicht positivem Ø realisiertem CRV, Aktien/Rohstoffe/Themen-ETF
    hatten keine ausreichende Stichprobe."""
    gruppen: dict[tuple[str, str], dict] = {}
    assetklasse_by_symbol = _assetklasse_index(watchlist, "compute_veto_shadow_performance_nach_grund()")

    def _stelle_sicher(tier: str, grund: str) -> dict:
        key = (tier, grund)
        if key not in gruppen:
            gruppen[key] = {
                "anzahl_resolved": 0,
                "take_profit_count": 0,
                "stop_loss_count": 0,
                "liquidation_count": 0,
                "_crv_summe": 0.0,
                "_crv_count": 0,
                # Einzelwerte zusaetzlich zur Summe: der Mittelwert allein
                # verraet nicht, ob er an wenigen Ausreissern haengt
                # (Methodik 2.5.5). Fuer den Beitrags-Check gebraucht.
                "_crv_werte": [],
            }
        return gruppen[key]

    placeholders = ", ".join("?" for _ in _RESOLVED_OUTCOMES)
    spot_rows = conn.execute(
        f"SELECT symbol, risk_veto_reason, veto_outcome_status AS status, "
        f"veto_outcome_realisiertes_crv AS crv FROM signals WHERE risk_veto = 1 "
        f"AND action = 'HALTEN' AND veto_outcome_status IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in spot_rows:
        tier = _tier_fuer_spot_symbol(row["symbol"], assetklasse_by_symbol)
        grund = _kategorisiere_veto_grund(row["risk_veto_reason"])
        eintrag = _stelle_sicher(tier, grund)
        eintrag["anzahl_resolved"] += 1
        if row["status"] == OUTCOME_TAKE_PROFIT:
            eintrag["take_profit_count"] += 1
        elif row["status"] == OUTCOME_STOP_LOSS:
            eintrag["stop_loss_count"] += 1
        if row["crv"] is not None:
            eintrag["_crv_summe"] += row["crv"]
            eintrag["_crv_count"] += 1
            eintrag["_crv_werte"].append(row["crv"])

    hebel_rows = conn.execute(
        f"SELECT risk_veto_reason, veto_outcome_status AS status, "
        f"veto_outcome_realisiertes_crv AS crv FROM hebel_signals WHERE risk_veto = 1 "
        f"AND action = 'HALTEN' AND veto_outcome_status IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in hebel_rows:
        grund = _kategorisiere_veto_grund(row["risk_veto_reason"])
        eintrag = _stelle_sicher(TIER_HEBEL, grund)
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
            eintrag["_crv_werte"].append(row["crv"])

    ergebnis: dict = _tier_geruest(watchlist)
    for (tier, grund), eintrag in gruppen.items():
        ergebnis.setdefault(tier, {})[grund] = _kennzahlen_mit_pruefung(eintrag)
    return ergebnis


def _aggregate_resolved_selbst_halten_signal_rows(
    conn, *, watchlist: list | None = None,
) -> dict[tuple[str, str], dict]:
    """Eigenstaendige Kopie von _aggregate_resolved_signal_rows() (2026-07-31,
    Option-B-Konvention dieses Moduls - siehe compute_veto_shadow_performance_
    nach_grund()s Docstring fuer den bereits etablierten Praezedenzfall einer
    vollstaendig separaten Kopie statt eines dritten `veto`-Parameterwerts)
    fuer den Zweig "selbst gewaehltes HALTEN": filtert auf `ist_reines_llm_
    halten = 1` statt `risk_veto = 1 AND action = 'HALTEN'`, liest
    selbst_halten_outcome_status/selbst_halten_outcome_realisiertes_crv statt
    veto_outcome_*."""
    gruppen: dict[tuple[str, str], dict] = {}
    assetklasse_by_symbol = _assetklasse_index(watchlist, "_aggregate_resolved_selbst_halten_signal_rows()")

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
                # Einzelwerte zusaetzlich zur Summe: der Mittelwert allein
                # verraet nicht, ob er an wenigen Ausreissern haengt
                # (Methodik 2.5.5). Fuer den Beitrags-Check gebraucht.
                "_crv_werte": [],
            }
        return gruppen[key]

    placeholders = ", ".join("?" for _ in _RESOLVED_OUTCOMES)
    spot_rows = conn.execute(
        f"SELECT symbol, groq_model AS llm_model, selbst_halten_outcome_status AS status, "
        f"selbst_halten_outcome_realisiertes_crv AS crv FROM signals WHERE ist_reines_llm_halten = 1 "
        f"AND selbst_halten_outcome_status IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in spot_rows:
        tier = _tier_fuer_spot_symbol(row["symbol"], assetklasse_by_symbol)
        eintrag = _stelle_sicher(tier, provider_from_label(row["llm_model"]))
        eintrag["anzahl_resolved"] += 1
        if row["status"] == OUTCOME_TAKE_PROFIT:
            eintrag["take_profit_count"] += 1
        elif row["status"] == OUTCOME_STOP_LOSS:
            eintrag["stop_loss_count"] += 1
        if row["crv"] is not None:
            eintrag["_crv_summe"] += row["crv"]
            eintrag["_crv_count"] += 1
            eintrag["_crv_werte"].append(row["crv"])

    hebel_rows = conn.execute(
        f"SELECT llm_model, selbst_halten_outcome_status AS status, "
        f"selbst_halten_outcome_realisiertes_crv AS crv FROM hebel_signals WHERE ist_reines_llm_halten = 1 "
        f"AND selbst_halten_outcome_status IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in hebel_rows:
        eintrag = _stelle_sicher(TIER_HEBEL, provider_from_label(row["llm_model"]))
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
            eintrag["_crv_werte"].append(row["crv"])

    return gruppen


def compute_selbst_halten_performance(conn, watchlist: list | None = None) -> dict:
    """Wie compute_veto_shadow_performance(), aber fuer den Zweig "selbst
    gewaehltes HALTEN" (2026-07-31, siehe check_signal_selbst_halten_outcome()/
    check_hebel_signal_selbst_halten_outcome()-Docstrings): Provider-/Tier-
    Aufschluesselung ueber alle Faelle, in denen das LLM sich OHNE Gate/Veto
    von sich aus gegen einen Trade entschieden, aber trotzdem eine
    hypothetische Zone angegeben hat. Beantwortet eine strukturell ANDERE
    Frage als compute_veto_shadow_performance() ("war die eigene
    Zurueckhaltung richtig" statt "war das Gate richtig") - bewusst NICHT in
    compute_gesamt_signalqualitaet() eingemischt, siehe dortiger Docstring."""
    gruppen = _aggregate_resolved_selbst_halten_signal_rows(conn, watchlist=watchlist)
    return _format_performance_gruppen(gruppen, watchlist)


def compute_selbst_halten_performance_nach_grund(conn, watchlist: list | None = None) -> dict:
    """Wie compute_selbst_halten_performance(), aber gruppiert nach (tier,
    top_grund_1_kategorie) statt (tier, provider) (2026-07-31, mirror
    compute_veto_shadow_performance_nach_grund()). Anders als dort ist hier
    KEIN Freitext-Klassifikator noetig - `top_grund_1_kategorie` ist bereits
    ein kleines, sauberes Enum (siehe hebel_analyst.py/analyst.py TOP_GRUENDE_
    KATEGORIEN), direkt aus der Zeile gelesen."""
    gruppen: dict[tuple[str, str], dict] = {}
    assetklasse_by_symbol = _assetklasse_index(watchlist, "compute_selbst_halten_performance_nach_grund()")

    def _stelle_sicher(tier: str, grund: str) -> dict:
        key = (tier, grund)
        if key not in gruppen:
            gruppen[key] = {
                "anzahl_resolved": 0,
                "take_profit_count": 0,
                "stop_loss_count": 0,
                "liquidation_count": 0,
                "_crv_summe": 0.0,
                "_crv_count": 0,
                # Einzelwerte zusaetzlich zur Summe: der Mittelwert allein
                # verraet nicht, ob er an wenigen Ausreissern haengt
                # (Methodik 2.5.5). Fuer den Beitrags-Check gebraucht.
                "_crv_werte": [],
            }
        return gruppen[key]

    placeholders = ", ".join("?" for _ in _RESOLVED_OUTCOMES)
    spot_rows = conn.execute(
        f"SELECT symbol, top_grund_1_kategorie, selbst_halten_outcome_status AS status, "
        f"selbst_halten_outcome_realisiertes_crv AS crv FROM signals WHERE ist_reines_llm_halten = 1 "
        f"AND selbst_halten_outcome_status IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in spot_rows:
        tier = _tier_fuer_spot_symbol(row["symbol"], assetklasse_by_symbol)
        grund = row["top_grund_1_kategorie"] or "unbekannt"
        eintrag = _stelle_sicher(tier, grund)
        eintrag["anzahl_resolved"] += 1
        if row["status"] == OUTCOME_TAKE_PROFIT:
            eintrag["take_profit_count"] += 1
        elif row["status"] == OUTCOME_STOP_LOSS:
            eintrag["stop_loss_count"] += 1
        if row["crv"] is not None:
            eintrag["_crv_summe"] += row["crv"]
            eintrag["_crv_count"] += 1
            eintrag["_crv_werte"].append(row["crv"])

    hebel_rows = conn.execute(
        f"SELECT top_grund_1_kategorie, selbst_halten_outcome_status AS status, "
        f"selbst_halten_outcome_realisiertes_crv AS crv FROM hebel_signals WHERE ist_reines_llm_halten = 1 "
        f"AND selbst_halten_outcome_status IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in hebel_rows:
        grund = row["top_grund_1_kategorie"] or "unbekannt"
        eintrag = _stelle_sicher(TIER_HEBEL, grund)
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
            eintrag["_crv_werte"].append(row["crv"])

    ergebnis: dict = _tier_geruest(watchlist)
    for (tier, grund), eintrag in gruppen.items():
        ergebnis.setdefault(tier, {})[grund] = _kennzahlen_mit_pruefung(eintrag)
    return ergebnis


# Van-Tharp-Skala fuer den System Quality Number (Definitive Guide to Position
# Sizing, 2008). Grenzen bewusst als Konstante statt als Magic Numbers im Code -
# sie sind uebernommene Fremdwerte, keine eigene Kalibrierung (Methodik 2.5.6).
_SQN_SKALA = (
    (1.5, "kaum handelbar"),
    (2.0, "durchschnittlich"),
    (3.0, "gut"),
    (5.0, "exzellent"),
    (7.0, "super"),
)
# Unter dieser Zahl ist der SQN durch den sqrt(n)-Faktor mehr Stichproben-
# artefakt als Systemeigenschaft - dann wird er zwar berechnet, aber mit
# ausdruecklichem Vorbehalt ausgewiesen.
_SQN_MIN_N_FUER_AUSSAGE = 30


def _sqn_einordnung(sqn: float | None) -> str | None:
    if sqn is None:
        return None
    for grenze, label in _SQN_SKALA:
        if sqn < grenze:
            return label
    return "ausserhalb der Skala"


# Bootstrap-Parameter. 1000 Ziehungen sind der in der Literatur uebliche
# Mindestwert fuer stabile Perzentile; darunter schwanken die Intervallgrenzen
# selbst spuerbar.
_BOOTSTRAP_ZIEHUNGEN = 1000
# Fester Seed: die Kennzahl wird bei jedem Seitenabruf neu berechnet. Ohne
# Seed sprangen die Intervallgrenzen zwischen zwei Aufrufen, was wie eine
# Datenaenderung aussieht und Vertrauen kostet. Der Zufall soll die
# Stichprobenunsicherheit abbilden, nicht die Anzeige unruhig machen.
_BOOTSTRAP_SEED = 20260803


def bootstrap_unsicherheit(r_multiples: list[float],
                           ziehungen: int = _BOOTSTRAP_ZIEHUNGEN) -> dict:
    """Konfidenzintervalle fuer Expectancy und SQN per Bootstrap (2026-08-03).

    PROBLEM. Die Kennzahlen stehen als Punktwerte da - "EW -0,299 R, SQN -1,72"
    liest sich exakt, beruht aber auf 86 Trades. Wie sicher der Wert ist, sagt
    die Zahl nicht. Van Tharp selbst empfiehlt 100+ Trades fuer eine
    Live-Bewertung und nennt 30 als Untergrenze fuer eine vorlaeufige Lesung -
    wir liegen dazwischen.

    VERFAHREN. Aus den vorhandenen R-Multiples wird `ziehungen` mal eine
    gleich grosse Stichprobe MIT ZURUECKLEGEN gezogen und jeweils Expectancy
    und SQN neu berechnet. Die 2,5%- und 97,5%-Perzentile der so entstehenden
    Verteilung bilden das 95%-Intervall. Das setzt keine Normalverteilung
    voraus - bei R-Multiples mit ihrer Haeufung bei genau -1,0 waere die
    Annahme auch falsch.

    `anteil_positiv` ist der praktisch wichtigste Wert: der Anteil der
    Ziehungen mit positiver Expectancy, also grob die Wahrscheinlichkeit, dass
    der wahre Erwartungswert ueber null liegt. Bei 0,5 ist die Datenlage
    schlicht unentschieden, egal wie der Punktwert aussieht.

    Gibt None-Felder zurueck, wenn zu wenige Werte fuer eine Streuung
    vorliegen (n < 2)."""
    n = len(r_multiples)
    if n < 2:
        return {"expectancy_ci_unten": None, "expectancy_ci_oben": None,
                "sqn_ci_unten": None, "sqn_ci_oben": None,
                "anteil_positiv": None, "bootstrap_ziehungen": 0}
    rng = random.Random(_BOOTSTRAP_SEED)
    ews: list[float] = []
    sqns: list[float] = []
    for _ in range(ziehungen):
        probe = [r_multiples[rng.randrange(n)] for _ in range(n)]
        mittel = statistics.fmean(probe)
        ews.append(mittel)
        streuung = statistics.stdev(probe)
        if streuung:
            sqns.append(mittel / streuung * math.sqrt(n))

    def _perzentil(werte: list[float], p: float) -> float | None:
        if not werte:
            return None
        sortiert = sorted(werte)
        # Nearest-Rank: robust und ohne Interpolationsannahme.
        idx = min(len(sortiert) - 1, max(0, int(round(p * (len(sortiert) - 1)))))
        return sortiert[idx]

    return {
        "expectancy_ci_unten": _perzentil(ews, 0.025),
        "expectancy_ci_oben": _perzentil(ews, 0.975),
        "sqn_ci_unten": _perzentil(sqns, 0.025),
        "sqn_ci_oben": _perzentil(sqns, 0.975),
        "anteil_positiv": sum(1 for x in ews if x > 0) / len(ews),
        "bootstrap_ziehungen": ziehungen,
    }


def _guete_kennzahlen(r_multiples: list[float], anzahl_offen: int) -> dict:
    """SQN, Expectancy und Profit Factor aus einer Liste von R-Multiples.

    R-Multiple = Ergebnis geteilt durch das anfangs riskierte Kapital. In
    diesem Projekt ist `outcome_realisiertes_crv` bereits genau das (bei
    Stop-Loss-Treffer -1,0, bei Take-Profit das erreichte Chance-Risiko-
    Verhaeltnis), es muss also nichts umgerechnet werden.

    - Expectancy = Mittelwert der R-Multiples. Positiv heisst: der Ansatz
      traegt sich rechnerisch. Notwendige, nicht hinreichende Bedingung.
    - SQN = Mittelwert / Standardabweichung * sqrt(n) (Van Tharp). Bestraft
      Streuung: zwei Systeme mit gleichem Mittelwert, aber unterschiedlicher
      Schwankung, bekommen verschiedene Werte - und genau das unterscheidet
      ein handelbares von einem bloss rechnerisch profitablen System.
    - Profit Factor = Summe der Gewinne / Betrag der Summe der Verluste.

    `anzahl_offen` (Signale mit Zonen, aber ohne Ergebnis) geht in keine
    Kennzahl ein, wird aber mitgefuehrt: die Aufloesungsquote ist seit dem
    02.08. Pflichtangabe, weil Gruppen mit weiten Stops kaum aufgeloest werden
    und ihre Trefferquote dadurch selektiert ist (siehe
    Basisinfos/Zielgroessen_und_Erfolgsmasse.md, Abschnitt 4)."""
    n = len(r_multiples)
    gesamt = n + anzahl_offen
    basis = {
        "anzahl_bewertet": n,
        "anzahl_offen": anzahl_offen,
        "aufloesungsquote": (n / gesamt) if gesamt > 0 else None,
    }
    if n == 0:
        return {**basis, "expectancy_r": None, "sqn": None, "sqn_einordnung": None,
                "sqn_belastbar": False, "profit_factor": None, "standardabweichung_r": None,
                **bootstrap_unsicherheit([])}
    mittel = statistics.fmean(r_multiples)
    streuung = statistics.stdev(r_multiples) if n >= 2 else None
    sqn = (mittel / streuung * math.sqrt(n)) if streuung else None
    gewinne = sum(r for r in r_multiples if r > 0)
    verluste = abs(sum(r for r in r_multiples if r < 0))
    return {
        **basis,
        "expectancy_r": mittel,
        "standardabweichung_r": streuung,
        "sqn": sqn,
        "sqn_einordnung": _sqn_einordnung(sqn),
        "sqn_belastbar": n >= _SQN_MIN_N_FUER_AUSSAGE,
        "profit_factor": (gewinne / verluste) if verluste > 0 else None,
        # Wie sicher sind diese Punktwerte? Siehe bootstrap_unsicherheit().
        **bootstrap_unsicherheit(r_multiples),
    }


# Horizont der Basislinien-Simulation. Bewusst derselbe Wert wie
# DEFAULT_ABGELAUFEN_TAGE_FALLBACK im Backward-Tracking: die Basislinie soll
# dasselbe Zeitfenster abbilden wie die Bewertung der echten Signale.
_BASISLINIE_HORIZONT_TAGE = 14
# Unter dieser Zahl simulierter Einstiege wird keine Basislinie ausgewiesen -
# ein Vergleichsmassstab aus wenigen Punkten ist schlechter als keiner.
_BASISLINIE_MIN_EINSTIEGE = 200
# Zieht die Basislinie ihre Zufallseinstiege nur aus dem Zeitraum, in dem die
# bewerteten Signale tatsaechlich liefen? Siehe basislinie_erwartungswert().
# RUECKSCHRITT: diesen Wert auf False setzen stellt exakt das Verhalten vor dem
# 03.08. wieder her (Ziehungen aus der gesamten Kurshistorie). Kein weiterer
# Eingriff noetig - die Kennzahlen aendern sich dann zurueck, nicht der Code.
_BASISLINIE_NUR_SIGNALFENSTER = True


def _zonen_kennzahlen(row) -> tuple[float, float, bool] | None:
    """(Stop-Abstand relativ, CRV, ist_short) einer Signalzeile nach Z-2.

    Die Richtung kommt aus den Zonen selbst (Ziel unter Entry = bearisch) statt
    aus einem richtung-Feld - so funktioniert es fuer Hebel UND die
    Spot-Familie, die kein solches Feld hat.

    Kantenwahl richtungsabhaengig wie im Risk-Gate: bei bullischer These
    stop_von/take_von, bei bearischer die gespiegelten _bis. Gibt None zurueck,
    wenn die Zonen unvollstaendig oder unplausibel sind."""
    def _f(name):
        try:
            return row[name]
        except (IndexError, KeyError):
            return None

    e_von, e_bis = _f("entry_usd_von"), _f("entry_usd_bis")
    if e_von is None:
        e_von = e_bis = _f("entry_usd")
    s_von, s_bis = _f("stop_loss_usd_von"), _f("stop_loss_usd_bis")
    t_von, t_bis = _f("take_profit_usd_von"), _f("take_profit_usd_bis")
    if s_von is None:
        s_von = s_bis = _f("stop_loss_usd")
    if t_von is None:
        t_von = t_bis = _f("take_profit_usd")
    if None in (e_von, s_von, t_von):
        return None
    e = (e_von + (e_bis or e_von)) / 2
    ist_short = t_von < e
    if ist_short:
        if s_bis is None or t_bis is None:
            return None
        stop, ziel = s_bis, t_bis
    else:
        stop, ziel = s_von, t_von
    risiko = (stop - e) if ist_short else (e - stop)
    chance = (e - ziel) if ist_short else (ziel - e)
    if risiko <= 0 or chance <= 0 or e <= 0:
        return None
    return risiko / e, chance / risiko, ist_short


def lade_kursreihen(conn) -> dict[str, list]:
    """Alle USD-Tageskerzen nach Symbol gruppiert - einmal laden, mehrfach
    nutzen. Ohne das laedt jede Basislinien-Berechnung die vollen rund 64000
    Zeilen erneut (bei acht Gruppen achtmal)."""
    reihen: dict[str, list] = {}
    for r in conn.execute(
        "SELECT symbol, date, open, high, low, close FROM price_history_ohlc "
        "WHERE currency = 'USD' ORDER BY symbol, date"
    ):
        reihen.setdefault(r["symbol"], []).append(r)
    return reihen


def _reihen_im_fenster(reihen: dict, ab_datum: str | None,
                       bis_datum: str | None) -> dict:
    """Beschneidet die Kursreihen auf [ab_datum, bis_datum] (ISO, inklusiv).

    Beide Grenzen optional - None laesst die jeweilige Seite offen. Reihen, die
    danach leer sind, fallen raus; die Zaehlung der Ziehungen in
    basislinie_erwartungswert() bleibt dadurch automatisch korrekt."""
    if ab_datum is None and bis_datum is None:
        return reihen
    geschnitten: dict[str, list] = {}
    for symbol, rows in reihen.items():
        gefiltert = [
            r for r in rows
            if (ab_datum is None or r["date"] >= ab_datum)
            and (bis_datum is None or r["date"] <= bis_datum)
        ]
        if gefiltert:
            geschnitten[symbol] = gefiltert
    return geschnitten


def basislinie_erwartungswert(conn, stop_rel: float, crv: float, ist_short: bool,
                              horizont: int = _BASISLINIE_HORIZONT_TAGE,
                              reihen: dict | None = None,
                              ab_datum: str | None = None,
                              bis_datum: str | None = None) -> dict:
    """Mechanische Basislinie: Zufallseinstieg an jedem Tagesbalken aller
    Symbole mit exakt diesen Stop-/Ziel-Abstaenden, beschraenkt auf das
    Zeitfenster der bewerteten Signale (2026-08-03).

    WARUM DAS NOETIG IST. Ohne Bezugspunkt haelt man ein funktionierendes
    System in einer schlechten Phase fuer kaputt - und steuert in die falsche
    Richtung nach. Der SIGNALBEITRAG (Expectancy minus Basislinie) ist die
    belastbarere Groesse, solange nur ein Regime beobachtet ist
    (Test_und_Verifikationsmethodik 2.5.7, Zielgroessen_und_Erfolgsmasse 4).

    DAS ZEITFENSTER IST DER GANZE PUNKT - und war bis heute falsch gesetzt.
    Zieht die Basislinie aus der gesamten Kurshistorie, mittelt sie ueber rund
    zwei Jahre Marktgeschichte, waehrend unsere bewerteten Signale aus wenigen
    Wochen stammen. Sie kontrolliert dann nicht die Marktphase, sondern ersetzt
    sie durch "Durchschnittsmarkt" - also genau das, wogegen sie gebaut wurde.
    Gemessen am 03.08. mit identischem Code und identischen Parametern
    (stop_rel 0,0394, CRV 2,698, LONG, Horizont 14):

        Signalfenster 2026-05-08..2026-08-03 (88 Tage):   -0,224 R  (n=2817)
        volle Historie 2024-07-17..2026-08-03 (~2 Jahre): +0,081 R  (n=60010)

    Das Vorzeichen kippt, Differenz 0,30 R. Der Signalbeitrag hebel/real geht
    dadurch von -0,379 R auf rund -0,075 R zurueck.

    KORREKTUR DER KORREKTUR (03.08.): Ein frueherer Docstring begruendete die
    Konstruktion mit "Zufallseinstieg verliert systematisch, -0,11 bis -0,26 R
    je nach Parametersatz". Commit b8d7cac erklaerte diese Zahl fuer nicht
    reproduzierbar und vermutete sie bei einer bereinigten Nebenrechnung. Beides
    war falsch: sie stammt aus der Basislinie von analyse_crv_gate_
    survivorship.py, deren Werte ueber alle Gruppen und beide Horizonte exakt
    zwischen -0,114 und -0,265 R liegen. Jenes Skript zieht bereits aus dem
    Signalfenster - die alte Zahl war also richtig, nur diese Funktion war es
    nicht. Beide Rechnungen sind mit dem Parameter unten jetzt deckungsgleich.

    RUECKSCHRITT: `_BASISLINIE_NUR_SIGNALFENSTER = False` (oben im Modul) stellt
    das alte Verhalten vollstaendig wieder her, ohne Code-Aenderung. Die Zahlen
    oben sind die beiden Erwartungswerte, zwischen denen dieser Schalter wechselt.

    VERBLEIBENDER VORBEHALT - Aufloesungs-Asymmetrie (#617, unveraendert offen).
    Trifft eine Ziehung weder Stop noch Ziel, wird sie unten zum Schlusskurs
    bewertet und ZAEHLT MIT. Echte Signale bekommen in derselben Lage
    'abgelaufen_unentschieden' und GAR KEINEN R-Wert. Der Topf ist gross und
    strukturell positiv (Barrieren-Konditionierung: was den Stop nicht trifft,
    ist nach oben selektiert - in BEIDEN Richtungen). An der Produktionszelle
    rund 31 % der Ziehungen, Verzerrung etwa +0,13 R. Das ist der kleinere der
    beiden Posten und bleibt bewusst offen: ihn zu beheben hiesse, entweder die
    Basislinie zu kuerzen oder unsere unaufgelosten Signale mitzubewerten - und
    Letzteres aendert die SQN-Basis aller bisherigen Auswertungen.

    Verwendet ansonsten dieselbe Abbruch- und Fill-Logik wie das
    Backward-Tracking: Stop schlaegt Ziel am selben Tag, Ausfuehrung zur
    Zonen-Grenze bzw. bei einem Gap zum Eroeffnungskurs (gap_bewusster_fill).

    `ab_datum`/`bis_datum`: ISO-Tagesdaten, inklusiv, beide optional. Werden sie
    weggelassen, zieht die Funktion aus der gesamten uebergebenen Historie -
    Aufrufer, die einen fairen Vergleich wollen, MUESSEN sie setzen.

    ZWEI FOLGEN DES FENSTERS, beide gewollt, beide sichtbar in `anzahl`:
    1. Eine Ziehung braucht `horizont`+1 Folgetage INNERHALB des Fensters. Das
       effektive Einstiegsfenster endet also rund einen Horizont vor
       `bis_datum` - deshalb setzt compute_systemguete() dort bewusst
       "letztes Signal + Horizont" und nicht das Datum des letzten Signals.
       Reicht die Kurshistorie nicht bis dorthin, deckt die Basislinie den
       juengsten Teil des Signalzeitraums nicht ab.
    2. Junge Gruppen fallen unter _BASISLINIE_MIN_EINSTIEGE und bekommen GAR
       KEINE Basislinie (erwartungswert_r None) statt einer aus wenigen
       Punkten. Am 03.08. traf das hebel/schatten (140 Ziehungen); hebel/real
       lag mit 210 knapp darueber. Das loest sich mit wachsender Historie von
       selbst - bis dahin ist "kein Massstab" die ehrlichere Anzeige als einer,
       der auf wenigen, stark korrelierten Ziehungen beruht.

    Kosten rund 0,06 s je Aufruf bei 64000 Kursreihen-Zeilen, mit Fenster
    entsprechend weniger - guenstig genug fuer den Betrieb, deshalb kein
    Caching."""
    if stop_rel <= 0 or crv <= 0:
        return {"anzahl": 0, "erwartungswert_r": None}
    if reihen is None:
        reihen = lade_kursreihen(conn)
    reihen = _reihen_im_fenster(reihen, ab_datum, bis_datum)

    werte: list[float] = []
    for rr in reihen.values():
        for i in range(len(rr) - horizont - 1):
            e = rr[i]["close"]
            if not e or e <= 0:
                continue
            risiko = e * stop_rel
            stop = e + risiko if ist_short else e - risiko
            ziel = e - risiko * crv if ist_short else e + risiko * crv
            fenster = rr[i + 1:i + 2 + horizont]
            ergebnis = None
            for p in fenster:
                hoch, tief, auf = p["high"], p["low"], p["open"]
                if hoch is None or tief is None:
                    continue
                hit_stop = (hoch >= stop) if ist_short else (tief <= stop)
                hit_ziel = (tief <= ziel) if ist_short else (hoch >= ziel)
                if hit_stop:
                    fill = gap_bewusster_fill(stop, auf, ist_stop=True, ist_short=ist_short)
                    ergebnis = ((e - fill) if ist_short else (fill - e)) / risiko
                    break
                if hit_ziel:
                    fill = gap_bewusster_fill(ziel, auf, ist_stop=False, ist_short=ist_short)
                    ergebnis = ((e - fill) if ist_short else (fill - e)) / risiko
                    break
            if ergebnis is None and fenster and fenster[-1]["close"]:
                schluss = fenster[-1]["close"]
                ergebnis = ((e - schluss) if ist_short else (schluss - e)) / risiko
            if ergebnis is not None:
                werte.append(ergebnis)

    # Fenster mit zurueckgeben: ohne diese Angabe ist ein Basislinienwert nicht
    # nachvollziehbar - derselbe Parametersatz liefert je nach Zeitraum
    # entgegengesetzte Vorzeichen (siehe Docstring).
    fenster = {"basislinie_ab_datum": ab_datum, "basislinie_bis_datum": bis_datum}
    if len(werte) < _BASISLINIE_MIN_EINSTIEGE:
        return {"anzahl": len(werte), "erwartungswert_r": None, **fenster}
    return {"anzahl": len(werte), "erwartungswert_r": statistics.fmean(werte), **fenster}


def compute_systemguete(conn, watchlist: list | None = None,
                        mit_basislinie: bool = True) -> dict:
    """System Quality Number + Expectancy + Profit Factor je tier (2026-08-02).

    Antwort auf eine Nutzer-Kritik nach einem Tag mit neun revidierten
    Befunden: ohne definierte Zielgroesse ist jede Kalibrierung beliebig, weil
    sich immer eine Zahl findet, die sich verbessern laesst. Herleitung und
    Zielwerte in `Basisinfos/Zielgroessen_und_Erfolgsmasse.md`.

    Bewusst GETRENNT nach `real` (tatsaechlich gesendete Signale) und
    `schatten` (vom Gate zurueckgestufte Vorschlaege, hypothetisch): am
    02.08. waren 468 von 560 ausgewerteten Faellen hypothetisch - ein
    Zusammenwurf haette die Systemguete zu 84% aus nie ausgefuehrten Trades
    berechnet. Die beiden Zahlen beantworten verschiedene Fragen ("wie gut ist
    das, was wir tun" vs. "wie gut waere das, was wir verhindern").

    SEIT 03.08. MIT BASISLINIE. Zusaetzlich wird je Gruppe eine mechanische
    Basislinie mitgerechnet (Zufallseinstieg mit denselben Median-Parametern,
    siehe basislinie_erwartungswert()) und daraus der SIGNALBEITRAG gebildet.
    Grund: die Basislinie ist im beobachteten Zeitraum durchgehend negativ, ein
    absolut gelesener SQN alarmiert dadurch strukturell falsch. `mit_basislinie
    =False` schaltet das ab, falls ein Aufrufer nur die reinen Kennzahlen will.

    ZEITFENSTER JE GRUPPE (03.08.): Die Basislinie zieht nur noch aus dem
    Zeitraum, in dem die bewerteten Signale DIESER Gruppe liefen - vom ersten
    bis zum letzten `created_at` plus Horizont. Vorher lief sie ueber die
    gesamte Kurshistorie und verglich damit zwei Jahre Durchschnittsmarkt mit
    wenigen Wochen Signalen; das drehte das Vorzeichen der Basislinie und
    ueberzeichnete den Signalbeitrag um rund 0,30 R. Herleitung, Messwerte und
    der Rueckschritt-Schalter stehen in basislinie_erwartungswert().

    Jede Gruppe bekommt ihr EIGENES Fenster, nicht ein gemeinsames: real und
    schatten, Hebel und Spot laufen ueber verschiedene Zeitraeume, und ein
    gemeinsames Fenster waere fuer jede einzelne Gruppe das falsche.

    Reine Lesefunktion. Gibt je tier ein dict mit den Schluesseln `real` und
    `schatten` zurueck, jeweils mit den Feldern aus _guete_kennzahlen() plus
    basislinie_erwartungswert_r / basislinie_anzahl / basislinie_stop_rel /
    basislinie_crv / basislinie_anteil_short / basislinie_ab_datum /
    basislinie_bis_datum / signalbeitrag_r."""
    assetklasse_by_symbol = _assetklasse_index(watchlist, "compute_systemguete()")
    r_werte: dict[tuple[str, str], list[float]] = {}
    offen: dict[tuple[str, str], int] = {}

    zonen: dict[tuple[str, str], list[tuple[float, float]]] = {}
    # Entstehungszeitpunkte der BEWERTETEN Faelle - daraus das Zeitfenster der
    # Basislinie. Ohne das mittelt sie ueber die ganze Kurshistorie und misst
    # eine andere Marktphase als die, die sie einordnen soll.
    zeitpunkte: dict[tuple[str, str], list[str]] = {}

    def _erfasse(tier: str, art: str, crv, ist_offen: bool, zonen_werte=None,
                 created_at=None) -> None:
        key = (tier, art)
        r_werte.setdefault(key, [])
        offen.setdefault(key, 0)
        if ist_offen:
            offen[key] += 1
            return
        if crv is not None:
            r_werte[key].append(crv)
        # Zonen nur von den BEWERTETEN Faellen sammeln - die Basislinie soll die
        # Parameter genau der Trades abbilden, deren Ergebnis sie einordnet.
        if zonen_werte is not None:
            zonen.setdefault(key, []).append(zonen_werte)
        if created_at:
            zeitpunkte.setdefault(key, []).append(str(created_at)[:10])

    for tabelle, ist_hebel in (("signals", False), ("hebel_signals", True)):
        # Die Veto-Schatten-Spalten kamen erst am 28.07. dazu. Aeltere
        # Datenbestaende (z.B. eine nie migrierte Zweitkopie) haben sie nicht -
        # dann wird der Schatten-Zweig einfach weggelassen statt die ganze
        # Auswertung mit einem OperationalError abzubrechen.
        spalten = {r[1] for r in conn.execute(f"PRAGMA table_info({tabelle})")}
        hat_schatten = {"veto_outcome_status", "veto_outcome_realisiertes_crv"} <= spalten
        felder = "symbol, outcome_status, outcome_realisiertes_crv, risk_veto, created_at"
        # Zonen mitlesen: daraus kommen die Parameter der Basislinie (Median
        # Stop-Abstand und CRV je Gruppe). Nur die Spalten, die es in der
        # jeweiligen Tabelle wirklich gibt - Spot fuehrt zusaetzlich
        # Einzelwert-Felder ohne _von/_bis, Hebel nicht.
        zonen_spalten = [c for c in (
            "entry_usd_von", "entry_usd_bis", "entry_usd",
            "stop_loss_usd_von", "stop_loss_usd_bis", "stop_loss_usd",
            "take_profit_usd_von", "take_profit_usd_bis", "take_profit_usd",
        ) if c in spalten]
        felder += "".join(f", {c}" for c in zonen_spalten)
        if hat_schatten:
            felder += ", veto_outcome_status, veto_outcome_realisiertes_crv"
        rows = conn.execute(
            f"SELECT {felder} FROM {tabelle} WHERE take_profit_usd_von IS NOT NULL"
        ).fetchall()
        for row in rows:
            tier = TIER_HEBEL if ist_hebel else _tier_fuer_spot_symbol(
                row["symbol"], assetklasse_by_symbol
            )
            z = _zonen_kennzahlen(row)
            if row["risk_veto"]:
                if not hat_schatten:
                    continue
                st = row["veto_outcome_status"]
                _erfasse(tier, "schatten", row["veto_outcome_realisiertes_crv"],
                         st not in _RESOLVED_OUTCOMES, z, row["created_at"])
            else:
                st = row["outcome_status"]
                _erfasse(tier, "real", row["outcome_realisiertes_crv"],
                         st not in _RESOLVED_OUTCOMES, z, row["created_at"])

    ergebnis: dict = {}
    # Einmal laden statt je Gruppe - siehe lade_kursreihen().
    reihen = lade_kursreihen(conn) if mit_basislinie else None
    for (tier, art) in sorted(set(r_werte) | set(offen)):
        k = _guete_kennzahlen(r_werte.get((tier, art), []), offen.get((tier, art), 0))
        z = [x for x in zonen.get((tier, art), []) if x]
        if mit_basislinie and z and k["expectancy_r"] is not None:
            stop_rel = statistics.median(x[0] for x in z)
            crv = statistics.median(x[1] for x in z)
            # Richtung nach Mehrheit der Gruppe: bei Hebel gibt es SHORT-Signale,
            # deren Basislinie spiegelverkehrt laeuft. Eine pauschale
            # LONG-Annahme waere dort schlicht die falsche Vergleichsgroesse.
            anteil_short = sum(1 for x in z if x[2]) / len(z)
            # Zeitfenster der Gruppe: vom ersten bewerteten Signal bis zum
            # letzten PLUS Horizont - so lange konnte das letzte Signal noch
            # laufen. Fehlen die Zeitstempel (Altbestand), bleibt das Fenster
            # offen und die Basislinie verhaelt sich wie vor dem 03.08.
            tage = sorted(zeitpunkte.get((tier, art), []))
            ab_datum = bis_datum = None
            if tage and _BASISLINIE_NUR_SIGNALFENSTER:
                ab_datum = tage[0]
                bis_datum = (datetime.fromisoformat(tage[-1])
                             + timedelta(days=_BASISLINIE_HORIZONT_TAGE)).date().isoformat()
            bl = basislinie_erwartungswert(conn, stop_rel, crv,
                                           ist_short=anteil_short > 0.5,
                                           reihen=reihen,
                                           ab_datum=ab_datum, bis_datum=bis_datum)
            k["basislinie_erwartungswert_r"] = bl["erwartungswert_r"]
            k["basislinie_anzahl"] = bl["anzahl"]
            k["basislinie_stop_rel"] = stop_rel
            k["basislinie_crv"] = crv
            k["basislinie_anteil_short"] = anteil_short
            k["basislinie_ab_datum"] = bl["basislinie_ab_datum"]
            k["basislinie_bis_datum"] = bl["basislinie_bis_datum"]
            k["signalbeitrag_r"] = (
                None if bl["erwartungswert_r"] is None
                else k["expectancy_r"] - bl["erwartungswert_r"]
            )
        else:
            k["basislinie_erwartungswert_r"] = None
            k["basislinie_anzahl"] = 0
            k["basislinie_stop_rel"] = None
            k["basislinie_crv"] = None
            k["basislinie_anteil_short"] = None
            k["basislinie_ab_datum"] = None
            k["basislinie_bis_datum"] = None
            k["signalbeitrag_r"] = None
        ergebnis.setdefault(tier, {})[art] = k
    return ergebnis


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
    assetklasse_by_symbol = _assetklasse_index(watchlist, "compute_provider_sendezaehler()")

    spot_rows = conn.execute(
        "SELECT symbol, groq_model AS llm_model FROM signals WHERE groq_raw_response IS NOT NULL",
    ).fetchall()
    for row in spot_rows:
        tier = _tier_fuer_spot_symbol(row["symbol"], assetklasse_by_symbol)
        key = (tier, provider_from_label(row["llm_model"]))
        zaehler[key] = zaehler.get(key, 0) + 1

    hebel_rows = conn.execute(
        "SELECT llm_model FROM hebel_signals WHERE groq_raw_response IS NOT NULL",
    ).fetchall()
    for row in hebel_rows:
        key = (TIER_HEBEL, provider_from_label(row["llm_model"]))
        zaehler[key] = zaehler.get(key, 0) + 1

    ergebnis: dict = _tier_geruest(watchlist)
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

    assetklasse_by_symbol = _assetklasse_index(watchlist, "compute_zai_richtung_performance()")
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
        _erfasse(TIER_HEBEL, urteil)

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
        tier = _tier_fuer_spot_symbol(row["symbol"], assetklasse_by_symbol)
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
    unveraendert), Spot-family nutzt _richtung_aus_zonen() (Zonen-
    Reihenfolge) statt richtung_aus_action() - `action` steht hier bereits auf
    HALTEN, richtung_aus_action() wuerde also None liefern (siehe dortiger
    Docstring). Gleiche Tier-Aufschluesselung und Rueckgabeform wie
    compute_zai_richtung_performance(), bewusst als separate Funktion (Option
    B) statt eines Parameters."""
    assetklasse_by_symbol = _assetklasse_index(watchlist, "compute_zai_richtung_performance_schatten()")
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
        _erfasse(TIER_HEBEL, urteil)

    spot_ids = conn.execute(
        "SELECT id, symbol FROM signals WHERE risk_veto = 1 AND action = 'HALTEN' "
        "AND veto_outcome_max_realisiertes_crv IS NOT NULL AND zai_eigene_richtung IS NOT NULL",
    ).fetchall()
    for row in spot_ids:
        signal = db.get_signal_by_id(conn, row["id"])
        if signal is None:
            continue
        primaer_richtung = _richtung_aus_zonen(signal)
        if primaer_richtung is None:
            continue
        tier = _tier_fuer_spot_symbol(row["symbol"], assetklasse_by_symbol)
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
    aufgeloeste, aber bereits trackbare Signale (outcome_status offen oder
    NULL, echte Kauf-/Nachkauf-/Eroeffnen-Aktion) - Nutzer-Fund (2026-07-24,
    Remote-Seite
    zeigte bei 0 abgeschlossenen Spot-Signalen keinerlei Hinweis, ob ueberhaupt
    Fortschritt passiert oder das Tracking schlicht stillsteht). Gleiche
    Tier-Aufschluesselung wie compute_provider_performance() (Spot nach
    Assetklasse, Hebel gesondert), aber OHNE Provider-Aufschluesselung - ein
    offenes Signal hat noch kein Ergebnis, das waere irrefuehrend.

    Rueckgabe je Tier: {"anzahl": int, "aeltestes_erstellt_am": str | None}."""
    assetklasse_by_symbol = _assetklasse_index(watchlist, "compute_offene_signale_uebersicht()")
    ergebnis: dict = {TIER_HEBEL: {"anzahl": 0, "aeltestes_erstellt_am": None}}
    if not watchlist:
        ergebnis[TIER_SPOT_SAMMEL] = {"anzahl": 0, "aeltestes_erstellt_am": None}

    def _erfasse(tier: str, created_at: str) -> None:
        eintrag = ergebnis.setdefault(tier, {"anzahl": 0, "aeltestes_erstellt_am": None})
        eintrag["anzahl"] += 1
        if eintrag["aeltestes_erstellt_am"] is None or created_at < eintrag["aeltestes_erstellt_am"]:
            eintrag["aeltestes_erstellt_am"] = created_at

    placeholders = ", ".join("?" for _ in _TRACKABLE_ACTIONS)
    spot_rows = conn.execute(
        f"SELECT symbol, created_at FROM signals WHERE (outcome_status IS NULL OR outcome_status = 'offen') AND action IN ({placeholders})",
        tuple(_TRACKABLE_ACTIONS),
    ).fetchall()
    for row in spot_rows:
        tier = _tier_fuer_spot_symbol(row["symbol"], assetklasse_by_symbol)
        _erfasse(tier, row["created_at"])

    hebel_placeholders = ", ".join("?" for _ in _HEBEL_TRACKABLE_ACTIONS_FUER_UEBERSICHT)
    hebel_rows = conn.execute(
        f"SELECT created_at FROM hebel_signals WHERE (outcome_status IS NULL OR outcome_status = 'offen') AND action IN ({hebel_placeholders})",
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
    table = _tabelle_fuer_tier(tier, "compute_win_rate_fact()")
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


def _binomialtest_zweiseitig_p_wert(erfolge: int, n: int, p: float = 0.5) -> float | None:
    """Exakter zweiseitiger Binomialtest (2026-07-29, Regelwerk-Audit Stufe 2 -
    siehe project_regelwerk_audit_29_07.md, "Kein Baseline-Vergleichsmechanismus
    existiert irgendwo im Code"): beantwortet "ist die beobachtete Trefferquote
    ueberhaupt signifikant von einer Zufalls-/Baseline-Quote `p` verschieden,
    oder ist der Unterschied bei dieser Stichprobengroesse durch Zufall
    erklaerbar?" - Ergaenzung zur reinen Prozentzahl, die bei kleinem n leicht
    ueberinterpretiert wird.

    Bewusst OHNE scipy (nicht in requirements.txt, nirgends sonst im Projekt
    verwendet - keine neue harte Abhaengigkeit fuer einen einzelnen Test):
    reine Standardbibliothek (`math.comb`), Summe aller Ausgaenge, die
    mindestens so unwahrscheinlich sind wie das beobachtete Ergebnis (Methode
    identisch zu scipy.stats.binomtest(..., alternative="two-sided")). Fuer die
    hier relevanten Stichprobengroessen (deutlich unter 1000) ist das schnell
    genug ohne Naeherung.

    Gibt None zurueck bei n=0 (kein Test moeglich) - Aufrufer soll das dann
    z.B. als "n/a" statt als falsche 1.0/0.0 anzeigen."""
    if n == 0:
        return None
    if not 0.0 < p < 1.0:
        raise ValueError("p muss zwischen 0 und 1 liegen (exklusive)")

    def _pmf(k: int) -> float:
        return math.comb(n, k) * (p ** k) * ((1 - p) ** (n - k))

    beobachtete_wahrscheinlichkeit = _pmf(erfolge)
    # Toleranz gegen Gleitkomma-Rundungsfehler bei "mindestens so unwahrscheinlich".
    p_wert = sum(
        wahrscheinlichkeit
        for k in range(n + 1)
        if (wahrscheinlichkeit := _pmf(k)) <= beobachtete_wahrscheinlichkeit * (1 + 1e-9)
    )
    return min(1.0, p_wert)


def compute_baseline_vergleich(
    conn, tier: str, erlaubte_symbole: set[str] | None = None,
    crv_minimum: float = CRV_MINIMUM,
) -> dict | None:
    """Konsolidierte Baseline-Vergleichs-Funktion (2026-07-29, Regelwerk-Audit
    Stufe 2 - siehe project_regelwerk_audit_29_07.md). Alle drei Audit-Agenten
    (Gate/Mistral/Z.ai) fanden unabhaengig voneinander denselben Mangel: es
    gibt nirgends eine Antwort auf "ist diese Trefferquote ueberhaupt besser
    als [Muenzwurf/CRV-Pflichtgrenze/regimenaiver Trendfolge-Trade]?" - diese
    Funktion buendelt die drei vorgeschlagenen Vergleiche zu EINER
    Funktionsfamilie statt drei getrennter (Nutzer-Vorgabe), ergaenzt um einen
    Signifikanztest, damit ein kleiner Prozentpunkt-Unterschied bei kleiner
    Stichprobe nicht als belastbarer Befund missverstanden wird.

    `tier`: "spot" liest die `signals`-Tabelle, alles andere (z.B. "hebel")
    liest `hebel_signals` - identisch zu compute_win_rate_fact(). Gleiche
    _RESOLVED_OUTCOMES-Basis (take_profit/stop_loss/liquidation), Liquidation
    zaehlt wie ueberall im Projekt als Fehlschlag.

    `erlaubte_symbole`: siehe compute_win_rate_fact()-Docstring (Multi-Asset-
    Vollstaendigkeitspruefung) - identisches Verhalten.

    Rueckgabe (None bei 0 ausgewerteten Signalen, wie compute_win_rate_fact()):
    - `anzahl_ausgewertete_signale`, `trefferquote_pct` (wie compute_win_rate_fact()).
    - `muenzwurf_vergleich`: Vergleich gegen p=0,5 (die vom Nutzer selbst
      aufgeworfene "kann ich nicht einfach eine Muenze werfen"-Frage) -
      `baseline_pct`, `differenz_prozentpunkte`, `binomialtest_p_wert`,
      `statistisch_signifikant_5pct`.
    - `crv_breakeven_vergleich`: NUR wenn `tier != "spot"` (CRV-Pflicht gilt nur
      fuer Hebel/gehebelte Trades) - Vergleich gegen die aus `crv_minimum`
      implizierte Break-even-Trefferquote (`1/(1+crv_minimum)`, siehe
      project_regelwerk_audit_29_07.md Kernerkenntnis 3: bei CRV_MINIMUM=2.0
      liegt Break-even bei 33,3%). Bewusst der FESTE Konfig-Mindestwert, nicht
      das tatsaechliche CRV je Signal - Letzteres ist noch kein eigenes
      DB-Feld (Audit-Fund "Wichtig" #4, separat, nicht Teil dieser Stufe).
    - `regime_naiv_vergleich`: NUR wenn `tier != "spot"` UND `trigger_zweig`
      gespeichert ist (Hebel-only-Feld) - Trefferquote des `trigger_zweig ==
      "trendfolge"`-Teilsatzes als regimenaive Referenz (Audit-Fund "Wichtig"
      #9: dieser Zweig IST bereits ein simpler Momentum-Baseline-Trade, LONG
      wenn 24h-Change>=0, wird aber nirgends separat ausgewertet). `None`, wenn
      dieser Teilsatz selbst 0 Eintraege hat.
    - `hinweis`: identischer Kleine-Stichprobe-Text wie compute_win_rate_fact().

    Reine Lesefunktion, kein Seiteneffekt."""
    table = _tabelle_fuer_tier(tier, "compute_baseline_vergleich()")
    spalten = ("symbol, outcome_status" if tier == TIER_SPOT_SAMMEL
               else "symbol, outcome_status, trigger_zweig")
    placeholders = ", ".join("?" for _ in _RESOLVED_OUTCOMES)
    rows = conn.execute(
        f"SELECT {spalten} FROM {table} WHERE outcome_status IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    if erlaubte_symbole is not None:
        rows = [r for r in rows if r["symbol"] in erlaubte_symbole]
    total = len(rows)
    if total == 0:
        return None

    def _trefferquote(teilmenge: list) -> tuple[int, int, float]:
        n = len(teilmenge)
        treffer = sum(1 for r in teilmenge if r["outcome_status"] == OUTCOME_TAKE_PROFIT)
        quote = round(100.0 * treffer / n, 1) if n > 0 else None
        return treffer, n, quote

    treffer, total, trefferquote_pct = _trefferquote(rows)

    muenzwurf_p_wert = _binomialtest_zweiseitig_p_wert(treffer, total, p=0.5)
    muenzwurf_vergleich = {
        "baseline_pct": 50.0,
        "differenz_prozentpunkte": round(trefferquote_pct - 50.0, 1),
        "binomialtest_p_wert": muenzwurf_p_wert,
        "statistisch_signifikant_5pct": (muenzwurf_p_wert is not None and muenzwurf_p_wert < 0.05),
    }

    crv_breakeven_vergleich = None
    if tier != TIER_SPOT_SAMMEL:
        breakeven_pct = round(100.0 / (1.0 + crv_minimum), 1)
        crv_p_wert = _binomialtest_zweiseitig_p_wert(treffer, total, p=breakeven_pct / 100.0)
        crv_breakeven_vergleich = {
            "crv_minimum": crv_minimum,
            "breakeven_pct": breakeven_pct,
            "differenz_prozentpunkte": round(trefferquote_pct - breakeven_pct, 1),
            "binomialtest_p_wert": crv_p_wert,
            "statistisch_signifikant_5pct": (crv_p_wert is not None and crv_p_wert < 0.05),
        }

    regime_naiv_vergleich = None
    if tier != TIER_SPOT_SAMMEL:
        trendfolge_rows = [r for r in rows if r["trigger_zweig"] == "trendfolge"]
        if trendfolge_rows:
            tf_treffer, tf_n, tf_quote = _trefferquote(trendfolge_rows)
            regime_naiv_vergleich = {
                "beschreibung": (
                    "Trefferquote des trigger_zweig='trendfolge'-Teilsatzes "
                    "(simpler Momentum-Trade: LONG wenn 24h-Aenderung>=0) als "
                    "regimenaive Referenz, OHNE LLM-Analyse."
                ),
                "anzahl": tf_n,
                "trefferquote_pct": tf_quote,
                "differenz_zur_gesamtquote_prozentpunkte": round(trefferquote_pct - tf_quote, 1),
            }

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
        "muenzwurf_vergleich": muenzwurf_vergleich,
        "crv_breakeven_vergleich": crv_breakeven_vergleich,
        "regime_naiv_vergleich": regime_naiv_vergleich,
        "hinweis": hinweis,
    }


_ZAI_ZUFALLS_BASELINE_PCT = 100.0 / 3.0  # Z.ai's zai_eigene_richtung ist LONG/SHORT/NEUTRAL;
# bei rein zufaelliger Wahl unter diesen 3 Optionen stimmt genau 1 davon mit der
# (binaeren LONG/SHORT-) Primaer-Richtung ueberein -> 1/3 Zufalls-Trefferquote.


def compute_zai_uebereinstimmung_baseline(conn, watchlist: list | None = None) -> dict:
    """Baseline-Vergleich fuer `zai_uebereinstimmung` (2026-07-29, Regelwerk-
    Audit Stufe 2, Z.ai-Audit-Fund "Kein Baseline-Vergleich fuer die
    4,8%-Uebereinstimmungsquote"): bislang wurde die Uebereinstimmungsquote
    zwischen der primaeren LLM-Empfehlung und Z.ais unabhaengiger Richtungs-
    Ableitung (`zai_eigene_richtung`, siehe gegenpruefung.py::leite_eigene_
    richtung()) nur ad-hoc waehrend Analysen berechnet (siehe
    extract_notebook_diagnose.py), nie als aufrufbare Funktion mit
    Referenzgroesse. `zai_eigene_richtung` kann LONG/SHORT/NEUTRAL sein, die
    Primaer-Richtung ist immer binaer (LONG/SHORT) - eine rein zufaellige
    3-Weg-Wahl traefe die Primaer-Richtung daher im Schnitt in 1/3 der Faelle
    (`_ZAI_ZUFALLS_BASELINE_PCT`), nicht in der Haelfte.

    Gleiche Tier-Aufschluesselung wie compute_provider_performance() (Hebel
    gesondert, Spot-family nach Assetklasse wenn `watchlist` uebergeben wird).
    Zaehlt NUR Zeilen mit gesetztem `zai_uebereinstimmung` ('ja'/'nein') -
    Zeilen ohne Z.ai-Ergebnis (Call fehlgeschlagen/nicht konfiguriert) fliessen
    nicht ein. Reine Lesefunktion, kein Seiteneffekt."""
    assetklasse_by_symbol = _assetklasse_index(watchlist, "compute_zai_uebereinstimmung_baseline()")
    gruppen: dict[str, dict] = {}

    def _stelle_sicher(tier: str) -> dict:
        return gruppen.setdefault(tier, {"anzahl_bewertet": 0, "anzahl_uebereinstimmung": 0})

    hebel_rows = conn.execute(
        "SELECT zai_uebereinstimmung FROM hebel_signals WHERE zai_uebereinstimmung IN ('ja', 'nein')",
    ).fetchall()
    for row in hebel_rows:
        eintrag = _stelle_sicher(TIER_HEBEL)
        eintrag["anzahl_bewertet"] += 1
        if row["zai_uebereinstimmung"] == "ja":
            eintrag["anzahl_uebereinstimmung"] += 1

    spot_rows = conn.execute(
        "SELECT symbol, zai_uebereinstimmung FROM signals WHERE zai_uebereinstimmung IN ('ja', 'nein')",
    ).fetchall()
    for row in spot_rows:
        tier = _tier_fuer_spot_symbol(row["symbol"], assetklasse_by_symbol)
        eintrag = _stelle_sicher(tier)
        eintrag["anzahl_bewertet"] += 1
        if row["zai_uebereinstimmung"] == "ja":
            eintrag["anzahl_uebereinstimmung"] += 1

    ergebnis: dict = {}
    for tier, eintrag in gruppen.items():
        n = eintrag["anzahl_bewertet"]
        uebereinstimmung = eintrag["anzahl_uebereinstimmung"]
        quote_pct = round(100.0 * uebereinstimmung / n, 1) if n > 0 else None
        p_wert = _binomialtest_zweiseitig_p_wert(uebereinstimmung, n, p=_ZAI_ZUFALLS_BASELINE_PCT / 100.0)
        ergebnis[tier] = {
            "anzahl_bewertet": n,
            "anzahl_uebereinstimmung": uebereinstimmung,
            "uebereinstimmungsquote_pct": quote_pct,
            "zufalls_baseline_pct": round(_ZAI_ZUFALLS_BASELINE_PCT, 1),
            "differenz_prozentpunkte": (
                round(quote_pct - _ZAI_ZUFALLS_BASELINE_PCT, 1) if quote_pct is not None else None
            ),
            "binomialtest_p_wert": p_wert,
            "statistisch_signifikant_5pct": (p_wert is not None and p_wert < 0.05),
        }
    return ergebnis


def compute_sl_mfe_analyse(conn, tier: str, erlaubte_symbole: set[str] | None = None) -> dict | None:
    """Trennt bei Stop-Loss-Faellen "Richtung war falsch" von "Richtung war
    zwischenzeitlich richtig, aber zu eng gestoppt" (2026-07-30, Nutzer-Frage
    "wie pruefen wir Erfolgsquoten auf mehreren Ebenen" - Anschluss an den
    Enge-Stop-Loss-Fund vom 28.07., siehe project_enge_stop_loss_backtest_
    und_massnahmen.md). Nutzt AUSSCHLIESSLICH bereits vorhandene Felder
    (`outcome_max_realisiertes_crv`/MFE, `outcome_mindestziel_erreicht_am`) -
    keine neue Datenerhebung noetig, nur eine neue Verschneidung.

    Fuer alle Signale mit `outcome_status == OUTCOME_STOP_LOSS`: wie viele
    haben trotzdem einen POSITIVEN `outcome_max_realisiertes_crv` (der Kurs
    lief zwischenzeitlich profitabel in die signalisierte Richtung, bevor er
    zurueckdrehte und den Stop ausloeste) bzw. haben sogar das Mindestziel
    (`outcome_mindestziel_erreicht_am`) VOR dem Stop erreicht. Eine hohe Quote
    deutet auf "richtige Richtung, aber Stop zu eng/Positionsfuehrung
    verbesserungswuerdig" hin statt auf grundsaetzlich falsche Signale -
    genau die Unterscheidung, die eine reine Win/Loss-Quote nicht liefert.

    `tier`: "spot" liest `signals`, alles andere liest `hebel_signals" -
    identisch zu compute_win_rate_fact()/compute_baseline_vergleich().

    Rueckgabe (None bei 0 Stop-Loss-Faellen):
    - `anzahl_sl_gesamt`: alle SL-Faelle (auch ohne MFE-Daten).
    - `anzahl_mit_mfe_daten`: davon mit gesetztem `outcome_max_realisiertes_crv`.
    - `anzahl_mit_positivem_mfe`/`quote_positiver_mfe_trotz_stop_pct`: Kern-
      Kennzahl dieser Funktion.
    - `anzahl_mindestziel_vor_stop_erreicht`: strengere Teilmenge (Mindestziel
      TATSAECHLICH erreicht, nicht nur MFE>0).
    - `anzahl_distinkte_symbole_bei_positivem_mfe`/`haeufigstes_symbol_anteil_
      pct`: Symbol-Konzentrations-Check (Test_und_Verifikationsmethodik.md
      Abschnitt 2.5) - IMMER mit ausweisen, da diese Funktion typischerweise
      auf kleinen Stichproben laeuft.
    - `hinweis`: Kleine-Stichprobe-Text (analog compute_win_rate_fact()) UND
      Konzentrations-Warnung, wenn ein einzelnes Symbol >20-25% der
      positiven Faelle stellt (`_MIN_SAMPLE_FUER_AUSSAGE`-Schwelle bewusst
      NICHT wiederverwendet - Nutzer-Vorgabe 2.5: > 20-25% Anteil EINES
      Symbols zaehlt separat, unabhaengig vom Gesamt-n).

    Reine Lesefunktion, kein Seiteneffekt."""
    table = _tabelle_fuer_tier(tier, "compute_sl_mfe_analyse()")
    rows = conn.execute(
        f"SELECT symbol, outcome_max_realisiertes_crv, outcome_mindestziel_erreicht_am "
        f"FROM {table} WHERE outcome_status = ?",
        (OUTCOME_STOP_LOSS,),
    ).fetchall()
    if erlaubte_symbole is not None:
        rows = [r for r in rows if r["symbol"] in erlaubte_symbole]
    anzahl_sl_gesamt = len(rows)
    if anzahl_sl_gesamt == 0:
        return None

    mit_mfe = [r for r in rows if r["outcome_max_realisiertes_crv"] is not None]
    anzahl_mit_mfe = len(mit_mfe)
    positiv_mfe = [r for r in mit_mfe if r["outcome_max_realisiertes_crv"] > 0]
    anzahl_mindestziel_vor_stop = sum(1 for r in rows if r["outcome_mindestziel_erreicht_am"])

    quote_pct = round(100.0 * len(positiv_mfe) / anzahl_mit_mfe, 1) if anzahl_mit_mfe > 0 else None

    symbol_counts: dict[str, int] = {}
    for r in positiv_mfe:
        symbol_counts[r["symbol"]] = symbol_counts.get(r["symbol"], 0) + 1
    anzahl_distinkte_symbole = len(symbol_counts)
    haeufigstes_symbol_anteil_pct = (
        round(100.0 * max(symbol_counts.values()) / len(positiv_mfe), 1)
        if symbol_counts else None
    )

    hinweise = []
    if anzahl_mit_mfe < _MIN_SAMPLE_FUER_AUSSAGE:
        hinweise.append(
            f"Nur {anzahl_mit_mfe} SL-Faelle mit MFE-Daten - statistisch NICHT belastbar "
            f"(Mindeststichprobe: {_MIN_SAMPLE_FUER_AUSSAGE})."
        )
    if haeufigstes_symbol_anteil_pct is not None and haeufigstes_symbol_anteil_pct > 20:
        hinweise.append(
            f"Ein einzelnes Symbol stellt {haeufigstes_symbol_anteil_pct}% der Faelle mit "
            "positivem MFE - Konzentrationsrisiko, siehe Test_und_Verifikationsmethodik.md 2.5."
        )
    hinweis = " ".join(hinweise) if hinweise else f"Basiert auf {anzahl_mit_mfe} Faellen mit MFE-Daten."

    return {
        "anzahl_sl_gesamt": anzahl_sl_gesamt,
        "anzahl_mit_mfe_daten": anzahl_mit_mfe,
        "anzahl_mit_positivem_mfe": len(positiv_mfe),
        "quote_positiver_mfe_trotz_stop_pct": quote_pct,
        "anzahl_mindestziel_vor_stop_erreicht": anzahl_mindestziel_vor_stop,
        "anzahl_distinkte_symbole_bei_positivem_mfe": anzahl_distinkte_symbole,
        "haeufigstes_symbol_anteil_pct": haeufigstes_symbol_anteil_pct,
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
    assetklasse_by_symbol = _assetklasse_index(watchlist, "compute_konfidenz_kalibrierung()")

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
        tier = _tier_fuer_spot_symbol(row["symbol"], assetklasse_by_symbol)
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
        eintrag = _stelle_sicher(TIER_HEBEL, _konfidenz_bucket(row["confidence_pct"]))
        eintrag["anzahl"] += 1
        if row["outcome_status"] == OUTCOME_TAKE_PROFIT:
            eintrag["take_profit_count"] += 1
        eintrag["_konfidenz_summe"] += row["confidence_pct"]

    ergebnis: dict = _tier_geruest(watchlist)
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
    table = _tabelle_fuer_tier(tier, "compute_richtungstreffer_quote()")
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
