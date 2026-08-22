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
from agent.krypto.ausstiegsregel import (
    parameter_aus_config, stopempfehlung_aus_mfe,
)
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

# E1 (22.08.2026, Umbauplan 128): der Einstieg wurde nie erreicht.
#
# ⚠️ WARUM DAS EIN EIGENER STATUS IST UND KEIN "nicht_anwendbar". Der Trade
# war anwendbar - er ist nur nie zustande gekommen. Ihn unter
# `nicht_anwendbar` zu buchen wuerde ihn mit HALTEN in einen Topf werfen; ihn
# als `abgelaufen_unentschieden` zu fuehren wuerde behaupten, er habe
# gelaufen und sich nicht entschieden. Beides waere falsch.
OUTCOME_EINSTIEG_NIE = "einstieg_nie_erreicht"

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
# Eigener Tier fuer Absicherungs-Instrumente (2026-08-07) - siehe
# _assetklasse_index() fuer die Begruendung.
TIER_HEDGE = "hedge"
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
    # HEDGE BEKOMMT EINEN EIGENEN TIER (2026-08-07, W1). Bis hierher landeten
    # DBPK und 3QSS in "etf" - zusammen mit den fuenf Themen-ETFs, weil sie in
    # der Watchlist dieselbe assetklasse tragen. Das ist fuer die Datenversorgung
    # richtig und fuer die MESSUNG falsch:
    #
    #   Ein Themen-ETF soll steigen. Ein Hedge soll fallen, wenn das Portfolio
    #   steigt - das ist seine Aufgabe, nicht sein Versagen.
    #
    # In einem gemeinsamen Topf heben sich zwei gegenlaeufige Logiken
    # gegenseitig auf, und die entstehende Zahl beschreibt nichts. Noch ist kein
    # Schaden entstanden (etf: real n=0), aber der erste aufgeloeste Hedge-Trade
    # haette ihn angerichtet - lautlos, weil eine Mischzahl immer plausibel
    # aussieht.
    #
    # Wirkt auf ALLE zwoelf Aggregationen, die diesen Index nutzen. Das ist
    # Absicht: die Trennung gilt ueberall oder nirgends.
    from agent.hedge.pipeline import ist_hedge_instrument

    return {
        a.symbol: (TIER_HEDGE if ist_hedge_instrument(a) else a.assetklasse)
        for a in watchlist
    }


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
    # E1 (22.08.2026): Signale, deren Einstiegszone nie beruehrt wurde.
    # ⚠️ EIGENER ZAEHLER, ausdruecklich NICHT in take_profit/stop_loss. Der
    # Trade ist nicht zustande gekommen - ihn in eine der beiden Quoten zu
    # buchen war der Defekt, den E1 behebt (Umbauplan 127: 21,1 %).
    einstieg_nie_erreicht: int = 0
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
    (Bestandszeilen vor der Kurszonen-Slice, siehe Signal-Dataclass-Kommentar).

    NUR NOCH FUER ANWESENHEITSPRUEFUNGEN und die Richtungsableitung. Wer eine
    Schwelle zum AUSLOESEN braucht, nimmt _zonen_schwelle() - siehe dort."""
    return von_value if von_value is not None else point_value


def _zonen_schwelle(von_value: float | None, bis_value: float | None,
                    point_value: float | None, ist_short: bool) -> float | None:
    """Ausloese-Schwelle einer Preiszone, RICHTUNGSABHAENGIG (2026-08-09).

    DER DEFEKT, DEN DAS BEHEBT. Eine Zone hat zwei Kanten. Bei LONG liegt die
    konservative jeweils bei `_von` (Stop darunter, Ziel darueber) - da fielen
    beide Konventionen zusammen und niemandem fiel etwas auf. Bei SHORT ist es
    gespiegelt: der Stop liegt UEBER dem Einstieg, das Ziel darunter, und
    konservativ ist dann `_bis` auf beiden Seiten.

    `_zonen_absolut()` spiegelt seit jeher korrekt - daraus entsteht das CRV,
    das ueber die Mindestgrenze 2,0 entscheidet. Die Outcome-Tracker nahmen
    dagegen ueber `_threshold()` fuer BEIDE Richtungen die `_von`-Kante. Damit
    genehmigte das System einen Trade nach der einen Rechnung und bewertete ihn
    nach einer anderen.

    WAS DABEI HERAUSKAM, an einem echten Fall (NEAR, hebel_signals id=407):

        entry 1,91   stop_von 1,96 / stop_bis 2,09   ziel_von 1,61 / ziel_bis 1,78

        Z-2 (Gate):     risiko 0,18   chance 0,13   ->  CRV   0,72
        Tracker (alt):  risiko 0,05   chance 0,30   ->  R    +6,00

    Bei einem CRV von 0,72 sind +6,00 R nicht erreichbar - die Zahl war ein
    Artefakt zweier Konventionen. Auf sechs Nachkommastellen reproduziert, ebenso
    bei HYPE id=598 (+9,4348) und XLM id=691 (+8,1606).

    GEMESSEN: 144 von 167 aufgeloesten SHORT-Zeilen (86,2 %) tragen abweichende
    Kanten, R ueberhoeht um Median 1,29x, maximal 3,78x. Bei LONG aendert sich
    nichts - dort waren beide Konventionen schon immer identisch.

    Der zweite, schwerere Teil betrifft nicht die Zahl, sondern den Handel: mit
    der nahen Kante loeste der Stop eines SHORT frueher aus als das Risiko, das
    bei der Positionsgroesse eingeplant war. Genau deshalb faellt die
    Entscheidung auf die Gate-Konvention und nicht umgekehrt (Nutzer-
    Entscheidung 09.08., "Variante A").

    Fallback-Kette wie bei _threshold(): fehlt die richtungsrichtige Kante,
    greift die andere, dann der alte Punktwert. Anwesenheitspruefungen bleiben
    dadurch gueltig."""
    if ist_short:
        erste, zweite = bis_value, von_value
    else:
        erste, zweite = von_value, bis_value
    if erste is not None:
        return erste
    if zweite is not None:
        return zweite
    return point_value


def lade_ohlc_auf_signal_skala(conn, symbol: str, entry: float | None,
                               min_date: str) -> list:
    """OHLC-Historie eines Symbols - aber nur, wenn sie zum Signal PASST.

    DIE LUECKE, DIE DAS SCHLIESST (2026-08-09). Am 06.08. bekam
    `simuliere_signal()` eine Plausibilitaetsschranke gegen den
    Instrumenten-Verwechsler: liegt der Einstieg um mehr als Faktor 3 neben der
    Kursreihe, wird nicht bewertet. Sie sitzt aber im SIMULATIONS-Pfad. Der
    LIVE-Tracker hatte keine - und der schreibt die Ergebnisse, die in jeder
    Systemguete landen.

    Wie teuer das war: `OD7C` #2361 stieg bei 34,63 ein und wurde gegen die
    Kupfer-Futures-Reihe bei ~6,30 USD/lb bewertet. Ergebnis **+20,37 R** - der
    einzige nennenswerte Wert der Assetklasse Rohstoffe, und er hat die
    Kennzahl monatelang getragen. Die Reihe ist laengst korrigiert, das
    gespeicherte Ergebnis blieb.

    ZWEI REPARATUREN GAB ES BEREITS, und beide greifen hier nicht:
    die Schranke von 06.08. (falscher Pfad) und
    `korrigiere_rohstoff_outcome.py` (Kriterium ist ein Stichtag, und
    `geprueft_am` ist inzwischen juenger). Ein Kriterium, das auf einem Datum
    beruht, veraltet mit dem Datum.

    Leere Liste, wenn die Skalen nicht zusammenpassen. Der Aufrufer faellt
    dadurch in seinen bestehenden Zweig fuer "keine OHLC-Daten" - er bewertet
    also nicht falsch, sondern gar nicht. Lieber kein Ergebnis als ein
    erfundenes; dieselbe Abwaegung wie bei der Schranke von 06.08.

    Grenze bewusst weit (Faktor 3): echte Gaps, Splits und Waehrungswechsel
    bleiben auswertbar, nur die Groessenordnungs-Verwechslung faellt heraus."""
    rows = db.get_ohlc_history(conn, symbol, "USD", min_date=min_date)
    if not rows or not entry or entry <= 0:
        return rows
    erster = next((r.close for r in rows if getattr(r, "close", None)), None)
    if not erster or erster <= 0:
        return rows
    verhaeltnis = max(entry / erster, erster / entry)
    if verhaeltnis > 3.0:
        logger.warning(
            "%s: Signal-Einstieg %.4f und Kursreihe %.4f liegen auf "
            "verschiedenen Skalen (Faktor %.2f) - NICHT bewertet. Typische "
            "Ursache: die Historie wurde ueber einen Proxy-Ticker geholt und "
            "unter dem echten Symbol abgelegt.",
            symbol, entry, erster, verhaeltnis,
        )
        return []
    return rows


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

    take_profit_threshold = _zonen_schwelle(
        signal.take_profit_usd_von, signal.take_profit_usd_bis,
        signal.take_profit_usd, ist_short)
    stop_loss_threshold = _zonen_schwelle(
        signal.stop_loss_usd_von, signal.stop_loss_usd_bis,
        signal.stop_loss_usd, ist_short)
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

    def resolve(exit_price: float, hit_take: bool,
                einstieg_am: str | None = None) -> tuple[str, dict]:
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
            # E1: 1 = die Zone wurde beruehrt, None = es gab keine Zone.
            "einstieg_erreicht": 1 if einstieg_am is not None else None,
            "einstieg_am": einstieg_am,
        }

    def _check_preis(high: float, low: float) -> tuple[bool, bool]:
        """Gibt (hit_take, hit_stop) zurueck - SHORT spiegelt Take-Profit/Stop-Loss
        gegenueber LONG (Take-Profit unten, Stop-Loss oben). Der Ausfuehrungspreis
        kommt seit dem 02.08. aus gap_bewusster_fill(), nicht mehr aus dem
        Tages-Extremwert (Begruendung dort)."""
        if ist_short:
            return low <= take_profit_threshold, high >= stop_loss_threshold
        return high >= take_profit_threshold, low <= stop_loss_threshold

    # ---- E1: ERST DER EINSTIEG, DANN DAS ERGEBNIS (22.08.2026) --------
    #
    # ⚠️ DER DEFEKT, DEN DAS BEHEBT (Umbauplan 127, an 114 echten Signalen
    # gemessen): diese Funktion begann bei `entry_mid` und wartete auf Ziel
    # oder Stop - AUCH WENN DER KURS DIE EINSTIEGSZONE NIE BERUEHRT HAT.
    #
    # 24 von 114 aufgeloesten Signalen (21,1 %) hatten nie einen Einstieg und
    # standen trotzdem als aufgeloest in der Datenbank. Bei NACHKAUFEN, wo
    # die Zone typisch UNTER dem Markt liegt, meldete der Tracker 90 %
    # Trefferquote: der Kurs stieg, das Ziel galt als erreicht, gekauft
    # wurde nie.
    #
    # `mindestziel_erreicht_am` und `max_realisiertes_crv` werden weiterhin
    # AB DEM ERSTEN TAG erfasst - sie beschreiben die Bewegung des Wertes,
    # nicht die eines Trades, und werden anderswo so gelesen.
    zone = einstiegszone(signal)
    eingestiegen = False
    einstieg_am = None

    ohlc_rows = lade_ohlc_auf_signal_skala(
        conn, signal.symbol, entry_mid, min_date)
    if len(ohlc_rows) >= 1:
        datenquelle = "real"
        for row in ohlc_rows:
            day = row.date
            guenstigster_tagespreis = row.low if ist_short else row.high
            _erfasse_mfe(guenstigster_tagespreis, day)
            if not eingestiegen:
                if not einstieg_beruehrt(row.high, row.low, zone):
                    continue
                eingestiegen = True
                # ⚠️ NUR MIT ZONE IST DAS EINE AUSSAGE (Testfund 22.08.):
                # ohne Zone laeuft die Aufloesung weiter wie bisher, aber
                # `einstieg_erreicht` bleibt None statt 1.
                einstieg_am = day if zone is not None else None
            hit_take, hit_stop = _check_preis(row.high, row.low)
            if hit_stop:
                # Konservativ (Z-1: Kapitalerhalt vor Gewinn): trifft ein Tag beide
                # Zonen, gewinnt Stop-Loss - keine Annahme ueber die Intraday-
                # Reihenfolge ohne Tick-Daten.
                return resolve(gap_bewusster_fill(
                    stop_loss_threshold, row.open, ist_stop=True, ist_short=ist_short,
                ), hit_take=False, einstieg_am=einstieg_am)
            if hit_take:
                return resolve(gap_bewusster_fill(
                    take_profit_threshold, row.open, ist_stop=False, ist_short=ist_short,
                ), hit_take=True, einstieg_am=einstieg_am)
    else:
        datenquelle = "proxy"
        price_rows = db.get_price_history(conn, asset.coingecko_id, min_date=min_date) if asset.coingecko_id else []
        for row in price_rows:
            if row.price_usd is None:
                continue
            day = row.date
            _erfasse_mfe(row.price_usd, day)
            if not eingestiegen:
                if not einstieg_beruehrt(row.price_usd, row.price_usd, zone):
                    continue
                eingestiegen = True
                einstieg_am = day if zone is not None else None
            hit_take, hit_stop = _check_preis(row.price_usd, row.price_usd)
            if hit_stop:
                return resolve(stop_loss_threshold, hit_take=False,
                               einstieg_am=einstieg_am)
            if hit_take:
                return resolve(take_profit_threshold, hit_take=True,
                               einstieg_am=einstieg_am)

    # ⚠️ NIE EINGESTIEGEN IST EIN ENDZUSTAND, KEIN OFFEN. Ein Signal, dessen
    # Zone nach der ganzen vorliegenden Historie nie beruehrt wurde, wartet
    # nicht mehr - es ist nicht zustande gekommen. Es weiter als `offen` zu
    # fuehren hiesse, es bei jedem Lauf erneut zu pruefen und am Ende doch
    # als "abgelaufen_unentschieden" zu buchen, also als Fehlschlag eines
    # Trades, den es nie gab.
    if zone is not None and not eingestiegen and (
            len(ohlc_rows) >= 1 or datenquelle == "proxy"):
        return OUTCOME_EINSTIEG_NIE, {
            "max_realisiertes_crv": max_favorable_crv,
            "mindestziel_erreicht_am": mindestziel_erreicht_am,
            "einstieg_erreicht": 0,
        }

    # Kein Treffer gefunden - offen oder abgelaufen, je nach Alter.
    return OUTCOME_OFFEN, {
        "max_realisiertes_crv": max_favorable_crv,
        "mindestziel_erreicht_am": mindestziel_erreicht_am,
        "einstieg_erreicht": (1 if (eingestiegen and zone is not None)
                              else None),
    }


def einstiegszone(signal) -> tuple | None:
    """(von, bis) der Einstiegszone in USD - oder None, wenn es sie nicht gibt.

    EINE STELLE FUER ALLE VIER AUFLOESER. Die Lehre vom 18.08.2026: vier
    Kopien derselben Stopzeile haben zwei Vormittage gekostet."""
    von, bis = signal.entry_usd_von, signal.entry_usd_bis
    if von is None and bis is None:
        punkt = getattr(signal, "entry_usd", None)
        return (float(punkt), float(punkt)) if punkt else None
    von = float(von if von is not None else bis)
    bis = float(bis if bis is not None else von)
    return (min(von, bis), max(von, bis))


def einstieg_beruehrt(hoch: float, tief: float, zone: tuple | None) -> bool:
    """Schneidet die Tagesspanne die Einstiegszone?

    ⚠️ GROSSZUEGIG ZUGUNSTEN DES BETRIEBS. Eine Beruehrung genuegt; es wird
    nicht verlangt, dass der Kurs in der Zone schliesst. Eine strengere
    Lesart wuerde den Befund aus Kapitel 127 nur verstaerken, und bei einem
    Eingriff in die Produktion ist die mildere die richtige.

    Ohne Zone gilt der Einstieg als erreicht - fehlende Daten duerfen kein
    Ergebnis erfinden, in keine der beiden Richtungen."""
    if zone is None:
        return True
    return float(tief) <= zone[1] and float(hoch) >= zone[0]


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

    take_profit_threshold = _zonen_schwelle(
        signal.take_profit_usd_von, signal.take_profit_usd_bis,
        signal.take_profit_usd, ist_short)
    stop_loss_threshold = _zonen_schwelle(
        signal.stop_loss_usd_von, signal.stop_loss_usd_bis,
        signal.stop_loss_usd, ist_short)

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

    ohlc_rows = lade_ohlc_auf_signal_skala(
        conn, signal.symbol, entry_mid, min_date)
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

    take_profit_threshold = _zonen_schwelle(
        signal.take_profit_usd_von, signal.take_profit_usd_bis,
        signal.take_profit_usd, ist_short)
    stop_loss_threshold = _zonen_schwelle(
        signal.stop_loss_usd_von, signal.stop_loss_usd_bis,
        signal.stop_loss_usd, ist_short)

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

    ohlc_rows = lade_ohlc_auf_signal_skala(
        conn, signal.symbol, entry_mid, min_date)
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


# Zeithorizont-DECKEL je Assetklasse (2026-08-07, H-2).
#
# DAS PROBLEM. Der `halte_kriterium_bucket` kommt vom LLM je Signal. Gemessen am
# Export vom 07.08.: **1.117 von 1.703 Hebel-Signalen tragen "mittel" = 45
# Tage** - bei einer Handelspraxis von 1-5, maximal 14 Tagen. Umgekehrt tragen
# 59 von 89 Themen-ETF-Signalen denselben Bucket, obwohl dort Monate gemeint
# sind. **Zwei voellig verschiedene Praxen, derselbe Horizont.**
#
# DER DECKEL IST EIN MAXIMUM, KEIN MINDESTWERT - und das ist der Kern.
# Nutzer-Hinweis vom 07.08.: *"auch bei laengerfristigen Positionen kann es zu
# sehr hoher Volatilitaet und ggf. kuerzeren Trades kommen, auch wenn diese
# urspruenglich laengerfristig geplant sind."* Genau deshalb wird nur nach oben
# begrenzt: ein Signal, das nach drei Tagen seine Zone trifft, loest nach drei
# Tagen auf - der Bucket steuert ausschliesslich, ab wann ein NICHT
# aufgeloestes Signal als abgelaufen gilt. Ein Deckel verkuerzt also nie einen
# Trade, er verhindert nur, dass ein Hebel-Signal 45 Tage lang als "noch offen"
# gefuehrt wird, obwohl die Praxis es laengst beendet haette.
#
# Kein Eintrag = kein Deckel. Die Spot-Klassen duerfen weiterhin bis "lang".
_HORIZONT_DECKEL_JE_TIER = {
    TIER_HEBEL: "kurz",
}
# Reihenfolge von kurz nach lang - fuer den Vergleich beim Deckeln.
_BUCKET_REIHENFOLGE = ("kurz", "mittel", "lang")


def gedeckelter_bucket(bucket: str | None, tier: str) -> str | None:
    """Begrenzt den vom LLM gewaehlten Zeithorizont auf das Maximum der Klasse.

    Gibt den Bucket unveraendert zurueck, wenn die Klasse keinen Deckel hat oder
    der gewaehlte Wert bereits darunter liegt. Siehe _HORIZONT_DECKEL_JE_TIER
    fuer die Begruendung - und dafuer, warum nur nach oben begrenzt wird.
    """
    deckel = _HORIZONT_DECKEL_JE_TIER.get(tier)
    if not deckel or not bucket:
        return bucket
    if bucket not in _BUCKET_REIHENFOLGE or deckel not in _BUCKET_REIHENFOLGE:
        return bucket
    if _BUCKET_REIHENFOLGE.index(bucket) <= _BUCKET_REIHENFOLGE.index(deckel):
        return bucket
    return deckel


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

        # E1 (22.08.2026): der Einstieg wurde nie erreicht - ENDZUSTAND.
        #
        # ⚠️ WEDER TREFFER NOCH FEHLSCHLAG. Der Trade ist nicht zustande
        # gekommen; ihn in eine der beiden Quoten zu buchen war genau der
        # Defekt aus Umbauplan 127 (21,1 % der aufgeloesten Signale).
        #
        # ⚠️ UND AUCH KEIN `offen`. Ohne diesen Zweig fiele der Status in
        # die Ueberholt-/Ablaufpruefung darunter und landete am Ende als
        # "abgelaufen_unentschieden" - also als Fehlschlag eines Trades, den
        # es nie gab. (Genau das ist beim Bauen zuerst passiert und von der
        # Paketpruefung gefangen worden.)
        if status == OUTCOME_EINSTIEG_NIE:
            db.update_signal_outcome(
                conn, signal.id, status,
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
                einstieg_erreicht=0,
            )
            result.einstieg_nie_erreicht += 1
            continue

        if status in (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS):
            db.update_signal_outcome(
                conn, signal.id, status,
                entschieden_am=extra.get("entschieden_am"),
                realisiertes_crv=extra.get("realisiertes_crv"),
                datenquelle=extra.get("datenquelle"),
                max_realisiertes_crv=extra.get("max_realisiertes_crv"),
                mindestziel_erreicht_am=extra.get("mindestziel_erreicht_am"),
                # E1: festhalten, DASS der Einstieg beruehrt wurde - sonst
                # laesst sich spaeter nicht unterscheiden, ob eine Zeile
                # nach der neuen oder der alten Regel entstand.
                einstieg_erreicht=extra.get("einstieg_erreicht"),
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
    # HISTORISCHE NUR-LONG-VETOS AUSSCHLIESSEN (2026-08-05). Der Veto, der
    # SHORT-Vorschlaege auf HALTEN drehte, ist entfernt - seine 313 Altfaelle
    # wachsen nicht mehr, wuerden hier aber dauerhaft in den Provider-Zahlen
    # mitlaufen und einen eingefrorenen Bestand wie laufendes Systemverhalten
    # aussehen lassen. Anders als bei der Aufschluesselung nach GRUND sind sie
    # in dieser Provider-Gruppierung nicht nachtraeglich trennbar - deshalb
    # hier in der Abfrage.
    #
    # Die Zeilen bleiben in der Datenbank und im Export vollstaendig erhalten;
    # ueber VETO_GRUND_NUR_LONG sind sie gezielt auswertbar. Gefiltert wird nur
    # die laufende Kennzahl.
    filter_clause = (
        "risk_veto = 1 AND action = 'HALTEN' "
        "AND (risk_veto_reason IS NULL OR risk_veto_reason NOT LIKE '%Nur Long%') AND "
    ) if veto else ""

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
    Gemini nach echter Trefferquote statt nur Kapazitaet vergleichen).

    ACHTUNG - DIESE TABELLE IST KEIN ANBIETERVERGLEICH (gemessen 2026-08-09). Die
    Anbieter loesen einander in der Kette AB, sie laufen nicht parallel - ihre
    Zeitraeume ueberlappen sich deshalb nicht einen einzigen Tag:

        cerebras   n= 9   14.07 .. 17.07   +0,523 R
        groq       n= 1   14.07 .. 14.07   +3,841 R
        mistral    n=82   17.07 .. 05.08   -0,491 R

    Was hier als "Anbieter-Unterschied" erscheint, ist ueberwiegend ein
    KALENDER-Unterschied. Die Gegenprobe INNERHALB von Mistral (Anbieter also
    konstant) zeigt denselben Verfall: -0,010 R in der Woche ab dem 15.07.
    gegen -0,601 R ab dem 22.07.

    Zweiter Vorbehalt, gleicher Messtag: die 92 aufgeloesten Signale liegen auf
    nur 23 Symbolen, und FUENF davon (KAIA/NEAR/BTC/XLM/HYPE, 32 Signale,
    ausnahmslos Verluste) tragen 102 % des Gesamtminus. Auf Symbolebene liegt
    der Mittelwert bei -0,136 R statt -0,344 R - die Differenz ist reine
    Wiederholung ueber Cooldown-Re-Signale, kein Urteilsunterschied.

    Fuer einen echten Anbietervergleich braeuchte es entweder ueberlappende
    Zeitraeume (zwei Anbieter gleichzeitig auf denselben Kandidaten) oder einen
    Ruecktest auf identischen Faktensaetzen. Bis dahin: als Betriebsuebersicht
    lesen, nicht als Qualitaetsurteil.

    Liest ALLE
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
# HISTORISCH, entsteht seit dem 05.08. nicht mehr (2026-08-05, Nur-Long-Umbau).
# Der Veto, der SHORT-Vorschlaege auf HALTEN drehte, ist entfernt - die
# Bitpanda-Beschraenkung wirkt jetzt nur noch auf E-Mail und Anzeige. Die 313
# Altfaelle bleiben in der Datenbank und bleiben auswertbar; sie duerfen aber
# nicht mehr als laufende Messgroesse dargestellt werden, sonst liest man einen
# eingefrorenen Bestand als aktuelles Systemverhalten.
#
# EIGENE KATEGORIE statt "sonstige": vorher fielen sie in den Sammeltopf und
# waren dort nicht von echten Restfaellen zu trennen. Genau diese Vermischung
# hat bei der Ursachensuche zum 31.07.-Bruch Zeit gekostet.
VETO_GRUND_NUR_LONG = "nur_long_historisch"


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
    # Nur-Long ZUERST (2026-08-05): diese Faelle fielen bisher in "sonstige"
    # und waren dort nicht von echten Restfaellen zu trennen. Sie entstehen
    # seit dem Nur-Long-Umbau nicht mehr neu - eine eigene Kategorie macht den
    # eingefrorenen Bestand sichtbar, statt ihn in einer laufenden Kennzahl zu
    # verstecken. Der Text stammt aus dem entfernten Veto in
    # hebel_risk_gate.py und ist in Altzeilen unveraendert erhalten.
    if "Nur Long" in reason:
        return VETO_GRUND_NUR_LONG
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
# Population A (compute_systemguete): zaehlen nur Zeilen mit, deren action
# tatsaechlich handelbar war? 'nicht_anwendbar' bedeutet HALTEN oder fehlende
# Zonen - nie eine Position. RUECKSCHRITT: False zaehlt sie wieder als "offen"
# mit und stellt die alte, zu niedrige Aufloesungsquote wieder her.
_SYSTEMGUETE_NUR_ECHTE_TRADES = True
# Bekommen noch laufende und ueberholte Trades einen R-Wert zum Schlusskurs?
# Das loest die Aufloesungs-Asymmetrie aus #617: die Basislinie tut es seit
# jeher, unsere Signale bisher nicht. RUECKSCHRITT: False laesst sie wieder aus
# allen Kennzahlen fallen - dann gilt die SQN-Basis von vor dem 03.08.
_SYSTEMGUETE_MARK_TO_MARKET = True


def _zonen_absolut(row) -> dict | None:
    """Absolute Zonenwerte einer Signalzeile nach Z-2: Entry-Mitte, Stop, Ziel.

    Eine Quelle fuer beides - _zonen_kennzahlen() leitet seine relativen Werte
    hieraus ab. Vorher lag dieselbe Logik zusaetzlich in
    analyse_crv_gate_survivorship.py::zonen(); zwei Fassungen derselben Formel
    driften auseinander, sobald eine angepasst wird."""
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
    # Kantenwahl richtungsabhaengig wie im Risk-Gate: bei bullischer These
    # stop_von/take_von, bei bearischer die gespiegelten _bis.
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
    return {"entry": e, "stop": stop, "ziel": ziel, "risiko": risiko,
            "stop_rel": risiko / e, "crv": chance / risiko, "ist_short": ist_short}


def _zonen_kennzahlen(row) -> tuple[float, float, bool] | None:
    """(Stop-Abstand relativ, CRV, ist_short) einer Signalzeile nach Z-2.

    Die Richtung kommt aus den Zonen selbst (Ziel unter Entry = bearisch) statt
    aus einem richtung-Feld - so funktioniert es fuer Hebel UND die
    Spot-Familie, die kein solches Feld hat.

    Duennes Tupel-Sichtfenster auf _zonen_absolut() - die Formel steht dort ein
    einziges Mal. Gibt None zurueck, wenn die Zonen unvollstaendig oder
    unplausibel sind."""
    z = _zonen_absolut(row)
    if z is None:
        return None
    return z["stop_rel"], z["crv"], z["ist_short"]


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
    # Haltedauer je Ziehung (04.08., Phase 0.2). Die Basislinie muss dieselben
    # Gebuehren tragen wie die Signale, gegen die sie steht - sonst vergleicht
    # der Signalbeitrag einen Netto-Wert mit einem Brutto-Wert. Sie traegt sie
    # aber zu IHRER eigenen Dauer: eine Zufallsziehung loest im Mittel anders
    # schnell auf als ein Signal, und die Kosten haengen linear an der Dauer.
    dauern: list[int] = []
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
            dauer = None
            for j, p in enumerate(fenster):
                hoch, tief, auf = p["high"], p["low"], p["open"]
                if hoch is None or tief is None:
                    continue
                hit_stop = (hoch >= stop) if ist_short else (tief <= stop)
                hit_ziel = (tief <= ziel) if ist_short else (hoch >= ziel)
                if hit_stop:
                    fill = gap_bewusster_fill(stop, auf, ist_stop=True, ist_short=ist_short)
                    ergebnis = ((e - fill) if ist_short else (fill - e)) / risiko
                    # Einstieg ist der Schlusskurs von Tag i, `fenster` beginnt
                    # bei i+1 - der erste Fenstertag ist also ein Haltetag.
                    dauer = j + 1
                    break
                if hit_ziel:
                    fill = gap_bewusster_fill(ziel, auf, ist_stop=False, ist_short=ist_short)
                    ergebnis = ((e - fill) if ist_short else (fill - e)) / risiko
                    dauer = j + 1
                    break
            if ergebnis is None and fenster and fenster[-1]["close"]:
                schluss = fenster[-1]["close"]
                ergebnis = ((e - schluss) if ist_short else (schluss - e)) / risiko
                dauer = len(fenster)
            if ergebnis is not None:
                werte.append(ergebnis)
                if dauer is not None:
                    dauern.append(dauer)

    # Fenster mit zurueckgeben: ohne diese Angabe ist ein Basislinienwert nicht
    # nachvollziehbar - derselbe Parametersatz liefert je nach Zeitraum
    # entgegengesetzte Vorzeichen (siehe Docstring).
    fenster = {"basislinie_ab_datum": ab_datum, "basislinie_bis_datum": bis_datum,
               "median_haltedauer_tage": (statistics.median(dauern) if dauern else None)}
    if len(werte) < _BASISLINIE_MIN_EINSTIEGE:
        return {"anzahl": len(werte), "erwartungswert_r": None, **fenster}
    return {"anzahl": len(werte), "erwartungswert_r": statistics.fmean(werte), **fenster}


# --- Kostenmodell (2026-08-04, Phase 0.2) ----------------------------------
# WOFUER. Bis heute enthielt KEINE Kennzahl dieses Moduls eine Gebuehr. Alle
# R-Multiples entstehen aus Zonen, also aus reiner Preisbewegung. Der
# ausgewiesene Erwartungswert war damit durchgehend BRUTTO, und die Frage
# "traegt sich das System?" wurde gegen eine Null-Kosten-Welt beantwortet.
#
# Herleitung, Quellen und die Gegenrechnung an echten Buchungen stehen in
# Basisinfos/Zielgroessen_und_Erfolgsmasse.md Abschnitt 6.7. Kurzfassung fuer
# den Hebel (Bitpanda Margin Trading, Kostentransparenz Version 4.0.0 vom
# 08.07.2026): Kauf 0 % - Schliessung 0,3 % - Tagesgebuehr 0,18 % -
# Liquidation 1 % zusaetzlich.
#
# BEMESSUNGSGRUNDLAGE IST DAS GELIEHENE KAPITAL. Das ist nicht aus dem
# Produkttext geschlossen, sondern an 104 eigenen geschlossenen Positionen
# nachgerechnet. Je Position gibt es genau EINE margin_trading.fee-Buchung
# (315 Buchungen zu 315 repay- und 315 close-Paaren), die den Fixanteil und
# die aufgelaufene Tagesgebuehr zusammen abrechnet - genau das Modell, das die
# Regression `Gebuehr / Bezugsgroesse = a + b x Haltetage` unterstellt. Auf
# Kreditbasis trifft der geschaetzte Fixanteil den offiziellen Satz
# (1,081 % gegen 1,00 % nach altem Tarif), auf Nominalbasis nicht (0,624 %).
_KOSTEN_AKTIV = True
_KOSTEN_HEBEL_SCHLIESSUNG = 0.003
_KOSTEN_HEBEL_LIQUIDATION = 0.01
# Staffelung der Tagesgebuehr: (bis einschliesslich Tag, Satz je Tag). Der
# letzte Eintrag mit Grenze None gilt darueber hinaus. Fuer die heutigen
# Horizonte (7/14 Tage) greift nur die erste Stufe - hinterlegt, weil die
# Ablauffrist bis 120 Tage reicht und die Staffel dort den Unterschied macht.
_KOSTEN_HEBEL_STAFFEL = ((60, 0.0018), (100, 0.0012), (180, 0.0006), (None, 0.000312))
# Fallback, wenn die Zeile keinen Hebel fuehrt: hebel_final ist nur bei 158 von
# 941 Hebel-Signalen gesetzt, hebel_vorschlag bei 894 - der Median beider ist
# 3,0, die Verteilung fast durchgehend 3x mit einem 5x-Anteil.
_KOSTEN_HEBEL_FALLBACK = 3.0

# SPOT IST NICHT BELEGT - bewusst als Annahme gefuehrt, nicht als Messwert.
# Im Bitpanda-Transaktionsexport tragen nur 348 von 3578 Spot-Trades eine
# explizite Gebuehrenbuchung (Tag vsn_fee, Median 1,03 % je Seite), und die
# auch nur in einem begrenzten Zeitfenster. Bei den uebrigen steckt die
# Gebuehr im Spread, also im ausgefuehrten Preis selbst, und ist ohne
# Marktmitte zum Ausfuehrungszeitpunkt nicht messbar. Der Satz unten ist die
# vorsichtige Fortschreibung des Messbaren; jede darauf gestuetzte Zahl traegt
# `kosten_belegt=False` und darf NICHT wie ein gemessener Wert zitiert werden.
_KOSTEN_SPOT_JE_SEITE = 0.01

# --- Kostenstruktur je Assetklasse (2026-08-07, recherchiert) --------------
#
# DER FEHLER, DEN DAS BEHEBT. Bis hierher galt EIN Satz fuer die gesamte
# Spot-Familie: 1 % je Seite, 2 % Roundtrip - bei einem 5-%-Stop also 0,40 R.
# Das ist fuer Bitpanda-Krypto plausibel (der Spread dort ist weit) und fuer
# Boersen-Aktien um eine Groessenordnung zu hoch.
#
# Recherchiert (Handelsblatt, Finanzfuchs, Stand 08/2026):
#
#   Krypto        0,99 % (BTC) bis 2,49 % (Altcoins), IM KURS enthalten
#   Aktien/ETF    1 EUR FIX je Trade + Spread bis 0,5 %
#   Sparplaene    kommissionsfrei
#   Edelmetalle   asymmetrischer Aufschlag je Metall (Gold 0,50/1,00 %)
#   Depot         0
#
# DAS STRUKTURELLE PROBLEM: eine FIXE Gebuehr bricht die Eigenschaft, auf der
# die ganze R-Rechnung beruht - der Einsatz kuerzt sich nicht mehr heraus. Bei
# 5 % Stop kostet dieselbe Gebuehr:
#
#     300 EUR Position  ->  15 EUR Risiko  ->  2 EUR  ->  0,133 R
#   2.000 EUR Position  -> 100 EUR Risiko  ->  2 EUR  ->  0,020 R
#
# Deshalb zwei Kostenarten statt einer, und deshalb geht die Positionsgroesse
# in die Rechnung ein.
#
# WICHTIGE ABGRENZUNG: die Rohstoff-ETCs (OD7N/OD7H/OD7C/OD7L) sind
# BOERSENGEHANDELTE ETCs, nicht Bitpanda Metals. Die Metals-Aufschlaege
# (Silber 2,5 % Kauf / 2,0 % Verkauf) gelten fuer sie NICHT - wer das
# verwechselt, rechnet mit dem Dreifachen.
_KOSTEN_ART_JE_TIER = {
    "krypto": "prozentual",
    "aktien": "fix_plus_spread",
    "etf": "fix_plus_spread",
    "rohstoffe": "fix_plus_spread",
    TIER_HEDGE: "fix_plus_spread",
}
# Krypto ueber Bitpanda: 0,99 % (BTC) bis 2,49 % (Altcoins). 1,5 % je Seite ist
# die konservative Mitte - bewusst EIN Satz je Klasse statt je Symbol, sonst
# wird die Pflege unhandhabbar (Nutzer-Einwand 07.08.).
_KOSTEN_KRYPTO_JE_SEITE = 0.015
# Boerse ueber Bitpanda: 1 EUR fix je Trade plus Spread.
_KOSTEN_BOERSE_FIX_EUR = 1.0
_KOSTEN_BOERSE_SPREAD_JE_SEITE = 0.0025
# Referenz-Positionsgroesse, wenn das Signal keine mitbringt. Nutzer-Angabe
# 07.08.: aktuell 300-500 EUR, kuenftig eher 500-1.000. 400 EUR ist der
# konservative (= teurere) Ausgangspunkt innerhalb der heutigen Praxis.
_KOSTEN_REFERENZ_POSITION_EUR = 400.0
# Laufende Gebuehr gehebelter ETPs (3QSS/DBPK). GESCHAETZT, nicht belegt -
# WisdomTree/Xtrackers liegen bei rund 0,6-1,0 % p.a. Fliesst nur bei Hedge ein
# und macht die dortige Haltedauer erstmals kostenwirksam; ohne sie erscheint
# eine ueber Monate gehaltene Absicherung billiger als sie ist.
_KOSTEN_HEDGE_TER_P_A = 0.008


def _tagesgebuehr_rel(tage: float) -> float:
    """Aufgelaufene Tagesgebuehr ueber `tage`, ueber die Staffel integriert."""
    rest, summe, vorher = max(0.0, float(tage)), 0.0, 0
    for grenze, satz in _KOSTEN_HEBEL_STAFFEL:
        spanne = math.inf if grenze is None else grenze - vorher
        genommen = min(rest, spanne)
        summe += genommen * satz
        rest -= genommen
        if rest <= 0:
            break
        vorher = grenze
    return summe


def kosten_in_r(stop_rel: float | None, tier: str, tage: float,
                hebel: float | None = None,
                ist_liquidation: bool = False,
                position_eur: float | None = None) -> dict:
    """Handelskosten eines Trades, ausgedrueckt in R (Vielfachen des Risikos).

    HERLEITUNG. Einsatz E, Hebel L, damit Nominal N = E x L und geliehenes
    Kapital K = E x (L-1). Das Risiko der Position ist N x stop_rel und
    definiert 1 R. Die Gebuehren fallen auf K an:

        Kosten      = K x (schliessung + tagesgebuehr(tage))
        Kosten in R = Kosten / (N x stop_rel)
                    = (L-1)/L x (schliessung + tagesgebuehr(tage)) / stop_rel

    DER EINSATZ KUERZT SICH HERAUS. Die Kostenlast in R haengt nur an Hebel,
    Haltedauer und Stop-Abstand - nicht an der Positionsgroesse. Das ist der
    Grund, warum sie ueberhaupt in eine R-Rechnung passt.

    Zwei Folgerungen fallen direkt aus der Formel:

    1. ENGE STOPS SIND DOPPELT TEUER. stop_rel steht im Nenner: ein enger Stop
       wird nicht nur haeufiger getroffen, er traegt auch je R eine hoehere
       Kostenlast. Das stuetzt RM-1b/RM-1c nachtraeglich mit einer zweiten,
       von der Trefferquote unabhaengigen Begruendung.
    2. HOEHERER HEBEL KOSTET MEHR JE R, nicht gleich viel. (L-1)/L waechst von
       0,50 (2x) ueber 0,67 (3x) auf 0,90 (10x), waehrend das Risikobudget
       gleich bleibt. Bei Bemessung auf das Nominal waere der Hebel neutral -
       genau deshalb ist die Bemessungsgrundlage oben keine Nebensache.

    Fuer die Spot-Familie gibt es keinen Kredit und keine Finanzierung; dort
    zaehlen Kauf und Verkauf je einmal (_KOSTEN_SPOT_JE_SEITE), unabhaengig
    von der Haltedauer, und `belegt` ist False.

    Gibt ein dict zurueck statt einer nackten Zahl, damit jede abgeleitete
    Kennzahl ihre Annahmen mitfuehren kann: `belegt` trennt gemessene von
    gesetzten Saetzen, `hebel`/`tage` machen die Rechnung nachvollziehbar.
    `kosten_r` ist None, wenn der Stop-Abstand fehlt oder unplausibel ist -
    dann wird bewusst NICHT geraten."""
    if not stop_rel or stop_rel <= 0:
        return {"kosten_r": None, "kosten_rel": None, "hebel": hebel,
                "tage": tage, "belegt": False, "basis": "kein Stop-Abstand"}

    groesse = None
    if tier == TIER_HEBEL:
        L = float(hebel) if hebel and hebel > 1 else _KOSTEN_HEBEL_FALLBACK
        satz = _KOSTEN_HEBEL_SCHLIESSUNG + _tagesgebuehr_rel(tage)
        if ist_liquidation:
            satz += _KOSTEN_HEBEL_LIQUIDATION
        kosten_rel = (L - 1.0) / L * satz
        belegt, basis = True, "geliehenes Kapital, an 104 Positionen belegt"
    elif _KOSTEN_ART_JE_TIER.get(tier) == "fix_plus_spread":
        # BOERSE: 1 EUR fix je Trade plus Spread. Die Fixgebuehr macht die
        # Kosten in R positionsgroessen-ABHAENGIG - der Einsatz kuerzt sich
        # hier NICHT heraus (siehe _KOSTEN_ART_JE_TIER fuer die Herleitung).
        L = None
        groesse = float(position_eur) if position_eur and position_eur > 0 else _KOSTEN_REFERENZ_POSITION_EUR
        fix_rel = (2.0 * _KOSTEN_BOERSE_FIX_EUR) / groesse
        kosten_rel = fix_rel + 2.0 * _KOSTEN_BOERSE_SPREAD_JE_SEITE
        if tier == TIER_HEDGE and tage:
            # Laufende ETP-Gebuehr, anteilig fuer die Haltedauer. Nur hier -
            # ein gewoehnlicher Spot-Kauf traegt keine.
            kosten_rel += _KOSTEN_HEDGE_TER_P_A * (float(tage) / 365.0)
        belegt = False
        basis = (f"Boerse: {_KOSTEN_BOERSE_FIX_EUR:.0f} EUR fix je Seite auf "
                 f"{groesse:.0f} EUR Position + {_KOSTEN_BOERSE_SPREAD_JE_SEITE * 100:.2f} % Spread"
                 + (", plus laufende ETP-Gebuehr" if tier == TIER_HEDGE else "")
                 + ("" if position_eur else " (Referenzgroesse, Signal ohne Positionsangabe)"))
    else:
        # KRYPTO ueber Bitpanda: prozentual, im Kurs enthalten.
        L = None
        kosten_rel = 2.0 * _KOSTEN_KRYPTO_JE_SEITE
        belegt = False
        basis = "Bitpanda-Krypto: 1,5 % je Seite (Mitte 0,99-2,49 %), im Kurs enthalten"

    return {"kosten_r": kosten_rel / stop_rel, "kosten_rel": kosten_rel,
            "hebel": L, "tage": tage, "belegt": belegt, "basis": basis,
            # NUR melden, wo die Groesse tatsaechlich in die Rechnung eingeht.
            # Bei Krypto und Hebel waere ein Wert hier irrefuehrend - dort
            # kuerzt sich der Einsatz heraus, die Zahl haette keine Bedeutung.
            "position_eur": (groesse if _KOSTEN_ART_JE_TIER.get(tier) == "fix_plus_spread"
                             else None)}


def _feld(row, name: str, default=None):
    """Spaltenzugriff, der fehlende Spalten vertraegt.

    sqlite3.Row wirft IndexError statt None zu liefern. Aeltere Datenbestaende
    fuehren einzelne Spalten nicht (siehe hat_schatten weiter unten) - ohne das
    braeche die ganze Auswertung an einer Nebengroesse ab."""
    try:
        return row[name]
    except (IndexError, KeyError):
        return default


def _haltedauer_tage(row, art: str) -> float | None:
    """Tatsaechliche Haltedauer aus den Zeitstempeln der Zeile.

    Nur fuer aufgeloeste Faelle gesetzt und selbst dort duenn: am 04.08. trug
    nur ein Zehntel der Hebel-Signale ein outcome_entschieden_am. Wo sie fehlt,
    faellt compute_systemguete() auf die simulierte Dauer zurueck."""
    ende = _feld(row, "veto_outcome_entschieden_am" if art == "schatten"
                 else "outcome_entschieden_am")
    start = _feld(row, "created_at")
    if not ende or not start:
        return None
    try:
        d = (_parse_dt(str(ende)) - _parse_dt(str(start))).total_seconds() / 86400.0
    except Exception:
        return None
    # Negative Differenzen und absurde Laufzeiten deuten auf Datenfehler -
    # lieber keine Dauer als eine falsche, die in die Kosten durchschlaegt.
    return d if 0.0 <= d <= 400.0 else None


def _hebel_der_zeile(row) -> float | None:
    """hebel_final vor hebel_vorschlag - der finale Wert ist der gehandelte."""
    for spalte in ("hebel_final", "hebel_vorschlag"):
        v = _feld(row, spalte)
        if v:
            return float(v)
    return None


def _position_eur_aus(row) -> float | None:
    """Positionsgroesse einer Signalzeile in EUR, oder None (2026-08-07).

    Spot fuehrt `position_size_eur`, Hebel `position_size_eur` bzw. den
    Eigenkapitaleinsatz. sqlite3.Row kennt kein .get() - deshalb ueber keys(),
    dieselbe Falle wie am 06.08. bei der Plausibilitaetsschranke."""
    try:
        felder = set(row.keys())
    except AttributeError:
        felder = set(row) if isinstance(row, dict) else set()
    for name in ("position_size_eur", "einsatz_eur", "position_eur"):
        if name in felder:
            wert = row[name]
            if wert and float(wert) > 0:
                return float(wert)
    return None


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

    POPULATION A (03.08.) - diese Funktion beantwortet ausschliesslich "wie gut
    ist, was wir TUN?". Die Schwesterfrage "haette das Gate richtig gefiltert?"
    hat mit compute_crv_breakeven_baender() eine eigene Funktion und eine eigene
    Grundgesamtheit. Zwei Aenderungen machen das hier scharf:

    1. NIE EIN TRADE FLIEGT RAUS. Zeilen mit outcome_status 'nicht_anwendbar'
       (action war HALTEN oder Zonen fehlten) tragen zwar Zonen, waren aber nie
       eine Position. Sie standen bisher im Offen-Topf und druckten die
       Aufloesungsquote: bei spot/real 240 von 271 Zeilen - ausgewiesen wurden
       3 % statt der ehrlichen 26 %. Bei hebel/real 94 von 242 (36 % statt
       58 %).
    2. MARK-TO-MARKET STATT WEGWERFEN. Noch laufende und ueberholte Trades
       bekommen einen R-Wert zum Schlusskurs nach _BASISLINIE_HORIZONT_TAGE,
       simuliert mit derselben Fill-Logik. Das loest die Aufloesungs-Asymmetrie
       aus #617: die Basislinie bewertet ihre unaufgeloesten Ziehungen seit
       jeher so, unsere Signale bekamen gar keinen R-Wert und fielen aus der
       SQN. Jetzt behandeln beide Seiten denselben Fall gleich. Signale, deren
       Horizont die Kurshistorie noch nicht abdeckt, bleiben 'offen' und gehen
       in keine Kennzahl ein - gleiche Beobachtungsdauer auf beiden Seiten.

    AUFGELOESTE BEHALTEN IHR DB-ERGEBNIS. Bewusst nicht ebenfalls simuliert:
    'liquidation_wahrscheinlich' haengt vom Hebel ab und laesst sich aus Zonen
    allein nicht rekonstruieren. Die Konvention ist dieselbe (gap_bewusster_
    fill, Stop schlaegt Ziel), nur der Rechenweg unterscheidet sich.

    DAS AENDERT DIE SQN-BASIS aller Auswertungen vor dem 03.08. Bewusster
    Schnitt, keine Nebenwirkung. RUECKSCHRITT ohne Code-Aenderung ueber
    _SYSTEMGUETE_NUR_ECHTE_TRADES / _SYSTEMGUETE_MARK_TO_MARKET (oben im Modul),
    einzeln oder zusammen.

    SEIT 04.08. MIT KOSTENMODELL (Phase 0.2). Bis dahin enthielt keine Zahl
    dieser Funktion eine Gebuehr - die R-Multiples entstehen aus Zonen, also
    aus reiner Preisbewegung. Jeder ausgewiesene Erwartungswert war damit
    BRUTTO, und "traegt sich das System?" wurde gegen eine Null-Kosten-Welt
    beantwortet. Formel und belegte Saetze in kosten_in_r().

    DIE BRUTTOZAHLEN BLEIBEN UNVERAENDERT. expectancy_r und sqn behalten ihre
    Bedeutung, die Nettowerte stehen als eigene Felder daneben. Grund: die
    Spot-Kostenannahme ist ausdruecklich nicht belegt (kosten_belegt=False),
    und ein still korrigierter Wert liesse sich hinterher nicht nachrechnen.

    DIE BASISLINIE TRAEGT DIESELBEN SAETZE, aber zu IHRER eigenen Haltedauer.
    Sie ist ein alternativer Trade, kein Nulltarif; sie brutto gegen ein
    Netto-Signal zu stellen rechnete dem Signal die Gebuehren doppelt an.
    Daraus folgt der eigentliche Befund der Umstellung: weil beide Seiten
    zahlen, kuerzen sich die Kosten im SIGNALBEITRAG weitgehend heraus.
    Kosten kippen die ABSOLUTE Frage ("traegt sich das System?"), nicht die
    RELATIVE ("ist die Auswahl besser als Zufall?"). Alle Selektionsbefunde
    aus den Vortagen bleiben damit gueltig; die Break-even-Aussagen nicht.

    HALTEDAUER: bevorzugt aus outcome_entschieden_am, sonst aus der Simulation
    (siehe _simuliere_zeile()). Wie viele Faelle welchen Weg gingen, steht in
    kosten_dauer_aus_zeitstempel / kosten_dauer_anzahl - ohne diese Angabe
    waere die Kostenzahl nicht einzuordnen.

    Reine Lesefunktion. Gibt je tier ein dict mit den Schluesseln `real` und
    `schatten` zurueck, jeweils mit den Feldern aus _guete_kennzahlen() plus
    basislinie_erwartungswert_r / basislinie_anzahl / basislinie_stop_rel /
    basislinie_crv / basislinie_anteil_short / basislinie_ab_datum /
    basislinie_bis_datum / signalbeitrag_r / anzahl_nie_ein_trade /
    anzahl_mark_to_market sowie den Kostenfeldern kosten_r / kosten_belegt /
    kosten_basis / kosten_hebel / kosten_median_haltedauer_tage /
    kosten_dauer_anzahl / kosten_dauer_aus_zeitstempel / expectancy_r_netto /
    sqn_netto / basislinie_kosten_r / basislinie_erwartungswert_r_netto /
    basislinie_median_haltedauer_tage / signalbeitrag_r_netto.

    HEDGE STEHT HIER, GEHOERT ABER NICHT HIERHER (2026-08-07). Seit dem
    Tier-Split taucht "hedge" als eigener Topf auf - das ist ein Fortschritt
    gegenueber der Vermischung mit den Themen-ETFs, aber die Kennzahl selbst
    bleibt fuer diese Klasse die FALSCHE FRAGE. SQN und Expectancy messen "wie
    gut verdient das?"; eine Absicherung soll aber Rueckschlaege daempfen und
    kostet dafuer Rendite. Nach Expectancy gemessen ist ihr Ergebnis
    konstruktionsbedingt negativ und sagt nichts ueber ihre Guete.

    Das richtige Mass steht in agent/portfolio_historie.py::
    compute_hedge_wirksamkeit() - Rueckschlag mit gegen ohne Absicherung, plus
    die gezahlte Praemie. Der hedge-Topf hier traegt deshalb ein
    `nicht_als_guete_lesen`-Flag und einen Verweis; er wird bewusst NICHT
    unterdrueckt, weil eine fehlende Zahl die Frage aufwirft, ob ueberhaupt
    gemessen wurde.
    """
    assetklasse_by_symbol = _assetklasse_index(watchlist, "compute_systemguete()")
    # Vor der Zeilenschleife laden: das Mark-to-Market unaufgeloester Trades
    # braucht die Kursreihen bereits dort, nicht erst bei der Basislinie.
    reihen = lade_kursreihen(conn)
    r_werte: dict[tuple[str, str], list[float]] = {}
    offen: dict[tuple[str, str], int] = {}

    zonen: dict[tuple[str, str], list[tuple[float, float]]] = {}
    # Entstehungszeitpunkte der BEWERTETEN Faelle - daraus das Zeitfenster der
    # Basislinie. Ohne das mittelt sie ueber die ganze Kurshistorie und misst
    # eine andere Marktphase als die, die sie einordnen soll.
    zeitpunkte: dict[tuple[str, str], list[str]] = {}

    # Zaehler fuer die beiden neuen Toepfe (03.08.), damit die Umstellung
    # nachvollziehbar bleibt statt nur die Kennzahlen zu verschieben.
    nie_trade: dict[tuple[str, str], int] = {}
    mtm: dict[tuple[str, str], int] = {}

    # Kostenmodell (04.08., Phase 0.2): Haltedauer und Hebel je bewertetem Fall.
    # Beide gehen NUR in die Kosten ein, nie in den R-Wert selbst - die
    # Bruttozahlen bleiben unveraendert, siehe kosten_in_r().
    dauern: dict[tuple[str, str], list[float]] = {}
    hebel_werte: dict[tuple[str, str], list[float]] = {}
    # POSITIONSGROESSE je bewertetem Fall (2026-08-07). Bei den boersengehandelten
    # Klassen faellt eine FIXE Gebuehr an (1 EUR je Trade), damit haengen die
    # Kosten in R an der Ordergroesse - der Einsatz kuerzt sich dort nicht
    # heraus. Siehe _KOSTEN_ART_JE_TIER.
    positionen: dict[tuple[str, str], list[float]] = {}
    # Woher die Dauer kam: echte Zeitstempel oder Simulation. Ohne diese
    # Aufschluesselung liesse sich hinterher nicht sagen, wie belastbar die
    # Kostenzahl ist - am 04.08. trug nur ein Zehntel der Zeilen ein Enddatum.
    dauer_echt: dict[tuple[str, str], int] = {}

    def _erfasse(tier: str, art: str, crv, ist_offen: bool, zonen_werte=None,
                 created_at=None, dauer=None, hebel=None,
                 dauer_aus_zeitstempel: bool = False, position_eur=None) -> None:
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
        if dauer is not None:
            dauern.setdefault(key, []).append(float(dauer))
            if dauer_aus_zeitstempel:
                dauer_echt[key] = dauer_echt.get(key, 0) + 1
        if hebel:
            hebel_werte.setdefault(key, []).append(float(hebel))
        if position_eur:
            positionen.setdefault(key, []).append(float(position_eur))

    def _simuliere_zeile(row, reihen_: dict) -> dict | None:
        """Simulationsergebnis einer Signalzeile, oder None.

        Zwei Verwendungen mit unterschiedlichem Anspruch:

        - MARK-TO-MARKET fuer noch nicht aufgeloeste, aber echte Trades. Dann
          zaehlt `r`. Simuliert ueber DENSELBEN Horizont wie die Basislinie und
          bewertet am Fensterende zum Schlusskurs - dadurch behandeln beide
          Seiten des Vergleichs Unaufgeloeste gleich. Gibt None zurueck, wenn
          die Kurshistorie den Horizont noch nicht abdeckt; solche Faelle
          bleiben 'offen' und gehen in keine Kennzahl ein (gleiche
          Beobachtungsdauer auf beiden Seiten).
        - HALTEDAUER fuer das Kostenmodell, auch bei aufgeloesten Zeilen. Dann
          zaehlt `tag`. Das ist ein Ersatzmass: der R-Wert kommt bei diesen
          Zeilen aus der DB, die Dauer aber aus der Nachbildung. Die Mechanik
          ist dieselbe (gap_bewusster_fill, Stop schlaegt Ziel), die
          Ausfuehrungszeitpunkte koennen dennoch abweichen. Verwendet wird es
          nur, wo outcome_entschieden_am fehlt - der Anteil steht als
          `kosten_dauer_aus_zeitstempel` im Ergebnis."""
        za = _zonen_absolut(row)
        if za is None or row["symbol"] not in reihen_:
            return None
        return simuliere_signal(za, reihen_[row["symbol"]],
                                str(row["created_at"])[:10], _BASISLINIE_HORIZONT_TAGE)

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
        # Nur fuer das Kostenmodell (04.08.): Enddatum fuer die echte
        # Haltedauer, Hebel fuer den Kreditanteil. Beide optional - die
        # Spot-Tabelle fuehrt keinen Hebel, aeltere Bestaende kein Enddatum.
        kosten_spalten = [c for c in (
            "outcome_entschieden_am", "veto_outcome_entschieden_am",
            "hebel_final", "hebel_vorschlag",
        ) if c in spalten]
        felder += "".join(f", {c}" for c in kosten_spalten)
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
                art, st = "schatten", row["veto_outcome_status"]
                crv = row["veto_outcome_realisiertes_crv"]
            else:
                art, st = "real", row["outcome_status"]
                crv = row["outcome_realisiertes_crv"]

            # POPULATION A (03.08.): war das ueberhaupt ein Trade? 'nicht_
            # anwendbar' setzt das Backward-Tracking, wenn die action nicht
            # handelbar war (HALTEN) oder Zonen fehlten. Solche Zeilen tragen
            # zwar Zonen, waren aber nie eine Position - sie gehoeren weder in
            # den Zaehler noch in den Nenner. Vorher landeten sie im
            # Offen-Topf und drueckten die Aufloesungsquote: bei spot/real
            # 240 von 271 Zeilen, ausgewiesen wurden 3 % statt 26 %.
            if _SYSTEMGUETE_NUR_ECHTE_TRADES and (st is None or st == OUTCOME_NICHT_ANWENDBAR):
                nie_trade[(tier, art)] = nie_trade.get((tier, art), 0) + 1
                continue

            hebel = _hebel_der_zeile(row)

            if st in _RESOLVED_OUTCOMES:
                # Haltedauer fuer die Kosten: echte Zeitstempel bevorzugt, sonst
                # die simulierte Dauer. Der R-Wert bleibt in JEDEM Fall der aus
                # der DB - simuliert wird hier nur die Dauer.
                dauer = _haltedauer_tage(row, art)
                echt = dauer is not None
                if dauer is None:
                    sim = _simuliere_zeile(row, reihen)
                    dauer = None if sim is None else sim["tag"] + 1
                _erfasse(tier, art, crv, False, z, row["created_at"],
                         dauer=dauer, hebel=hebel, dauer_aus_zeitstempel=echt,
                         position_eur=_position_eur_aus(row))
                continue

            # Noch laufend oder ueberholt: Mark-to-Market statt Wegwerfen -
            # das ist die Aufloesungs-Asymmetrie aus #617. Die Basislinie
            # bewertet ihre unaufgeloesten Ziehungen seit jeher zum
            # Schlusskurs; unsere Signale bekamen gar keinen R-Wert. Jetzt
            # behandeln beide Seiten denselben Fall gleich.
            sim = _simuliere_zeile(row, reihen) if _SYSTEMGUETE_MARK_TO_MARKET else None
            if sim is None:
                _erfasse(tier, art, None, True, z, row["created_at"])
            else:
                mtm[(tier, art)] = mtm.get((tier, art), 0) + 1
                _erfasse(tier, art, sim["r"], False, z, row["created_at"],
                         dauer=sim["tag"] + 1, hebel=hebel,
                         position_eur=_position_eur_aus(row))

    ergebnis: dict = {}
    # `reihen` ist schon oben geladen (Mark-to-Market braucht sie fruehe) -
    # einmal fuer alles, siehe lade_kursreihen().
    for (tier, art) in sorted(set(r_werte) | set(offen)):
        k = _guete_kennzahlen(r_werte.get((tier, art), []), offen.get((tier, art), 0))
        # Nachvollziehbarkeit der Umstellung: wie viele Faelle waren nie ein
        # Trade, wie viele sind per Mark-to-Market statt DB-Ergebnis bewertet?
        k["anzahl_nie_ein_trade"] = nie_trade.get((tier, art), 0)
        k["anzahl_mark_to_market"] = mtm.get((tier, art), 0)
        z = [x for x in zonen.get((tier, art), []) if x]

        # --- Kosten (04.08., Phase 0.2) ------------------------------------
        # BRUTTO BLEIBT BRUTTO. expectancy_r und sqn werden NICHT
        # ueberschrieben, die Nettowerte stehen daneben. Ein still korrigierter
        # Wert liesse sich hinterher nicht mehr nachrechnen, und die
        # Spot-Kostenannahme ist ausdruecklich nicht belegt (kosten_belegt).
        d_liste = dauern.get((tier, art), [])
        h_liste = hebel_werte.get((tier, art), [])
        p_liste = positionen.get((tier, art), [])
        kosten = kosten_in_r(
            statistics.median(x[0] for x in z) if z else None, tier,
            statistics.median(d_liste) if d_liste else _BASISLINIE_HORIZONT_TAGE,
            hebel=statistics.median(h_liste) if h_liste else None,
            position_eur=statistics.median(p_liste) if p_liste else None,
        ) if _KOSTEN_AKTIV else {"kosten_r": None, "kosten_rel": None, "hebel": None,
                                 "tage": None, "belegt": False, "basis": "abgeschaltet",
                                 "position_eur": None}
        k["kosten_r"] = kosten["kosten_r"]
        k["kosten_belegt"] = kosten["belegt"]
        k["kosten_basis"] = kosten["basis"]
        k["kosten_hebel"] = kosten["hebel"]
        k["kosten_median_haltedauer_tage"] = kosten["tage"]
        # Woraus die Kosten gerechnet wurden - bei den boersengehandelten
        # Klassen entscheidet die Ordergroesse ueber die Kostenlast in R.
        k["kosten_position_eur"] = kosten.get("position_eur")
        k["kosten_position_anzahl"] = len(p_liste)
        # Belastbarkeit der Dauer: wie viele Faelle trugen ein echtes Enddatum,
        # wie viele mussten simuliert werden?
        k["kosten_dauer_anzahl"] = len(d_liste)
        k["kosten_dauer_aus_zeitstempel"] = dauer_echt.get((tier, art), 0)
        k["expectancy_r_netto"] = (
            None if k["expectancy_r"] is None or kosten["kosten_r"] is None
            else k["expectancy_r"] - kosten["kosten_r"])
        # Kosten verschieben den Mittelwert, nicht die Streuung - der Abzug ist
        # fuer jeden Trade derselbe. Deshalb genuegt der verschobene Zaehler.
        k["sqn_netto"] = (
            None if k["expectancy_r_netto"] is None or not k["standardabweichung_r"]
            else k["expectancy_r_netto"] / k["standardabweichung_r"]
            * math.sqrt(k["anzahl_bewertet"]))

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
                # Fensterende ebenfalls am Gruppenhorizont (H-3) - so lange
                # konnte das letzte Signal DIESER Gruppe noch laufen.
                _fenster_horizont = (int(round(statistics.median(d_liste)))
                                     if d_liste else _BASISLINIE_HORIZONT_TAGE)
                bis_datum = (datetime.fromisoformat(tage[-1])
                             + timedelta(days=max(1, _fenster_horizont))).date().isoformat()
            # H-3 (2026-08-07): DER BASISLINIEN-HORIZONT FOLGT DER GRUPPE.
            # Bis hierher rechnete die Basislinie fuer JEDE Klasse fest 14 Tage
            # - eine Position mit 120 Tagen Frist wurde also gegen einen
            # 14-Tage-Zufallseinstieg gestellt, und der Signalbeitrag der
            # langfristigen Klassen war damit systematisch falsch.
            #
            # Genommen wird die GEMESSENE mediane Haltedauer der Gruppe, nicht
            # der konfigurierte Bucket. Das ist der empirisch richtige
            # Vergleich und erledigt zugleich den Nutzer-Hinweis, dass auch
            # langfristig geplante Positionen bei hoher Volatilitaet kurz
            # ausfallen koennen: schliessen die Signale einer Gruppe
            # tatsaechlich nach vier Tagen, misst die Basislinie vier Tage -
            # unabhaengig davon, was geplant war.
            bl_horizont = int(round(statistics.median(d_liste))) if d_liste else _BASISLINIE_HORIZONT_TAGE
            bl_horizont = max(1, bl_horizont)
            bl = basislinie_erwartungswert(conn, stop_rel, crv,
                                           ist_short=anteil_short > 0.5,
                                           horizont=bl_horizont,
                                           reihen=reihen,
                                           ab_datum=ab_datum, bis_datum=bis_datum)
            k["basislinie_horizont_tage"] = bl_horizont
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
            # DIE BASISLINIE TRAEGT DIESELBEN KOSTEN. Sie ist ein alternativer
            # Trade, kein Nulltarif - wer sie brutto gegen ein Netto-Signal
            # stellt, rechnet dem Signal die Gebuehren doppelt an. Aber zu
            # IHRER Dauer: Zufallsziehungen loesen anders schnell auf als
            # Signale, und die Kosten haengen linear an der Haltedauer.
            k["basislinie_median_haltedauer_tage"] = bl.get("median_haltedauer_tage")
            bl_kosten = kosten_in_r(
                stop_rel, tier,
                bl.get("median_haltedauer_tage") or _BASISLINIE_HORIZONT_TAGE,
                hebel=kosten["hebel"],
                # DIESELBE Positionsgroesse wie die Signale - sonst traegt die
                # Basislinie eine andere Kostenlast und der Vergleich waere
                # schief (die Fixgebuehr haengt an der Ordergroesse).
                position_eur=kosten.get("position_eur"),
            ) if _KOSTEN_AKTIV else {"kosten_r": None}
            k["basislinie_kosten_r"] = bl_kosten["kosten_r"]
            k["basislinie_erwartungswert_r_netto"] = (
                None if bl["erwartungswert_r"] is None or bl_kosten["kosten_r"] is None
                else bl["erwartungswert_r"] - bl_kosten["kosten_r"])
            # Netto-Signalbeitrag. Weil beide Seiten dieselben Saetze tragen,
            # verschiebt er sich NICHT um die vollen Kosten, sondern genau um
            # die Kostendifferenz beider Seiten. Das ist der eigentliche
            # Befund dieser Umstellung: Kosten kippen die ABSOLUTE Frage
            # ("traegt sich das System?"), nicht die RELATIVE ("ist die
            # Auswahl besser als Zufall?").
            #
            # ACHTUNG BEIM LESEN: die Differenz ist nicht klein und faellt
            # tendenziell zu unseren Gunsten aus. Ein Zufallseinstieg trifft
            # seltener eine Barriere und laeuft haeufiger bis zum Horizont -
            # er zahlt also laenger. Ein Signalbeitrag, der sich durch die
            # Kostenrechnung VERBESSERT, ist deshalb zu pruefen, bevor er
            # zitiert wird: er kann echt sein (schnellere Aufloesung ist ein
            # realer Vorteil) oder ein Artefakt der Horizontwahl.
            k["signalbeitrag_r_netto"] = (
                None if k["expectancy_r_netto"] is None
                or k["basislinie_erwartungswert_r_netto"] is None
                else k["expectancy_r_netto"] - k["basislinie_erwartungswert_r_netto"])
        else:
            k["basislinie_erwartungswert_r"] = None
            k["basislinie_anzahl"] = 0
            k["basislinie_stop_rel"] = None
            k["basislinie_crv"] = None
            k["basislinie_anteil_short"] = None
            k["basislinie_ab_datum"] = None
            k["basislinie_bis_datum"] = None
            k["signalbeitrag_r"] = None
            k["basislinie_median_haltedauer_tage"] = None
            k["basislinie_kosten_r"] = None
            k["basislinie_erwartungswert_r_netto"] = None
            k["signalbeitrag_r_netto"] = None
        # HEDGE: die Zahlen entstehen, werden aber ausdruecklich als
        # ungeeignetes Guetemass markiert (2026-08-07, siehe Docstring). Ein
        # Flag am Datum statt einer Unterdrueckung: eine fehlende Zahl wirft die
        # Frage auf, ob ueberhaupt gemessen wurde - eine gekennzeichnete nicht.
        if tier == TIER_HEDGE:
            k["nicht_als_guete_lesen"] = True
            k["hinweis"] = (
                "SQN/Expectancy sind fuer eine Absicherung die falsche Frage - "
                "ein Hedge soll Rueckschlaege daempfen und kostet dafuer "
                "Rendite, sein Erwartungswert ist konstruktionsbedingt negativ. "
                "Das zustaendige Mass ist agent/portfolio_historie.py::"
                "compute_hedge_wirksamkeit() (Rueckschlag mit gegen ohne "
                "Absicherung, plus gezahlte Praemie)."
            )
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

    Nutzer-Wunsch (2026-07-27): "ZAI unabhaengig mit seinen unterschiedlichen
    Entscheidungen und deren Erfolgsquote messen" - analog zu
    compute_provider_performance()/compute_win_rate_fact(), aber unabhaengig
    von Mistrals Neigung.

    URSPRUENGLICHE BEGRUENDUNG UEBERHOLT (2026-08-05). Sie lautete: der
    Kandidatenfilter halte `hebel_richtung_modus="nur_long"` durchgehend
    aktiv, Mistrals LONG-Uebergewicht sei damit ein strukturelles
    Konfigurations-Artefakt und keine organische Strategie.

    Dieser Filter ist seit dem 05.08. entfernt (budget_allocator.py, und der
    nachgelagerte Veto in hebel_risk_gate.py::post_check_hebel() ebenfalls -
    siehe dortigen Docstring). SHORT-Kandidaten erreichen das LLM jetzt, und
    SHORT-Empfehlungen laufen normal durch. Ein LONG-Uebergewicht in
    kuenftigen Auswertungen ist deshalb NICHT mehr automatisch ein Artefakt -
    es kann eine echte Modellneigung sein, und genau das macht diese Messung
    ab jetzt aussagekraeftiger als vorher.

    Die Messung selbst bleibt unveraendert richtig: `leite_eigene_richtung()`
    bekommt bewusst KEINE richtung/action/confidence_pct und leitet
    LONG/SHORT/NEUTRAL allein aus den objektiven Fakten ab - sie war nie vom
    Filter abhaengig, nur ihre Begruendung war es.

    ZEITVERGLEICHE: der 05.08. ist eine Bruchstelle (Testmethodik 2.1b).
    Vorher-Werte stammen aus einer Population ohne SHORT-Kandidaten.

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
    from agent.hedge.pipeline import ist_hedge_instrument
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
            row["action"], ist_hedge_invertiert=ist_hedge_instrument(row["symbol"]),
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


# Wie viele Beobachtungen die NEUTRALE Annahme wiegt (2026-08-09, Nutzer-
# Vorschlag: "eine neutrale Ausgangsposition die sich ohnehin selbst durch den
# Betrieb kalibriert"). 50 ist das untere Ende dessen, was die Literatur je
# Setup fuer eine belastbare Erwartungswert-Aussage verlangt (50-100); unsere
# 94 Signale gelten fuer den GESAMTEN Track-Record ueber alle Symbole, die
# SHORT-Seite hat davon nur 20.
PSEUDO_STICHPROBE = 50

# Die CRV-Pflichtgrenze - Quelle fuer den Breakeven, wenn noch keine eigenen
# Signale vorliegen. Bewusst hier gespiegelt statt importiert: risk_gate.py
# importiert dieses Modul, ein Rueckimport waere zirkulaer. Der Wert wird in
# `teste_trefferquote_bezug.py` gegen die Quelle geprueft, damit er nicht
# auseinanderlaeuft.
_CRV_MINIMUM = 2.0

# Ab wie vielen ausgewerteten Trades die Systemguete OHNE Gewichtung lesbar
# ist. War bis 09.08. die Schwelle, unter der der Fakt GAR NICHT geliefert
# wurde; seither wird er auch darunter geliefert - mit Gewicht und dem
# ausdruecklichen Vermerk `belastbar: false`.
_MIN_N_SYSTEMGUETE_BELASTBAR = 30


def _spalte(row, name: str):
    """Spaltenwert oder None - `sqlite3.Row` wirft sonst IndexError.

    Noetig, weil `compute_win_rate_fact()` fuer Hebel UND Spot laeuft und die
    Spot-Tabelle keine `richtung`-Spalte hat. Ein `try/except` an jeder
    Aufrufstelle waere dieselbe Logik dreimal."""
    try:
        return row[name]
    except (IndexError, KeyError):
        return None


def einordnung_gegen(wert: float | None, referenz: float | None,
                     toleranz: float) -> str | None:
    """Die KATEGORIALE Zwillingsform zu einer Zahl.

    WARUM ZUSAETZLICH ZUR ZAHL, nicht statt ihr. Dieses Projekt haelt an drei
    Stellen dasselbe fest: *"ein Modell, das rechnen soll, rechnet falsch;
    eines, das nachschlagen soll, schlaegt nach"* - daher Baender statt Kurve
    (Regel 32/36), Tabelle statt Formel (Kosten-Fakt) und beim
    `btc_zu_ema50`-Fakt ausdruecklich "zwei Formen mit Absicht: Prozentwert
    UND kategoriale Einordnung". Extern gestuetzt: Modelle sind beim
    Schliessen ueber stetige Groessen schwach, kategoriale Labels tragen
    zuverlaessiger; und schon bei zwei Zahlen ist ihre Arithmetik nicht
    verlaesslich.

    Die Trefferquote und die Systemguete hatten diese Zwillingsform bisher
    nicht - das Modell musste den Vergleich selbst ziehen. Genau der Vergleich
    ist die Aussage."""
    if wert is None or referenz is None:
        return None
    abstand = wert - referenz
    if abs(abstand) <= toleranz:
        return "auf Hoehe der Basislinie"
    if abstand > 0:
        return ("deutlich ueber der Basislinie" if abstand > 3 * toleranz
                else "ueber der Basislinie")
    return ("deutlich unter der Basislinie" if abstand < -3 * toleranz
            else "unter der Basislinie")


def schrumpfe_zu_neutral(gemessen: float | None, n: int | None,
                         neutral: float | None,
                         k: float = PSEUDO_STICHPROBE) -> dict | None:
    """Gewichteter Uebergang vom neutralen Anker zum Messwert.

        gewichtet = n/(n+k) * gemessen + k/(n+k) * neutral

    WOZU. Eine Kennzahl aus wenigen Beobachtungen tritt mit voller Autoritaet
    auf, obwohl sie sie nicht hat. Genau das ist bei uns der Fall: 94 Signale
    gesamt, davon 20 SHORT - und die Literatur verlangt 50-100 JE SETUP. Der
    Fakt "Trefferquote 16 %" liest sich fuer das Modell wie eine Tatsache und
    hat am 09.08. gemessen die LONG-Konfidenz um bis zu 33 Punkte gedrueckt,
    die SHORT-Konfidenz um null.

    Die Schrumpfung macht die Unsicherheit EXPLIZIT statt sie dem Leser zu
    ueberlassen: bei wenig Daten sagt der Fakt fast nichts, mit jedem
    aufgeloesten Signal wandert er zum Messwert. Kein Schwellwert, keine
    Klippe - dieselbe Bewegung, die dieses Projekt beim CRV schon vollzogen
    hat ("ein glatter Verlauf verlangt glatte Behandlung").

    ZWINGEND DAZU (sonst ist es Beschoenigung statt Kalibrierung): der Aufrufer
    gibt IMMER beide Zahlen weiter, die rohe und die gewichtete, plus das
    Gewicht. Der `systemguete`-Docstring warnt zu Recht davor, eine
    unerfreuliche Zahl weicher zu machen - hier wird nichts ersetzt, es kommt
    nur die Einordnung dazu.

    Rueckgabe: dict mit `roh`, `gewichtet`, `gewicht`, `neutral`, `n`, `k` -
    oder None, wenn eine Eingabe fehlt. Bewusst kein Ersatzwert.
    """
    if gemessen is None or neutral is None or n is None or n < 0 or k <= 0:
        return None
    gewicht = n / (n + k)
    return {
        "roh": round(float(gemessen), 4),
        "gewichtet": round(gewicht * gemessen + (1 - gewicht) * neutral, 4),
        "gewicht": round(gewicht, 3),
        "neutral": round(float(neutral), 4),
        "n": int(n),
        "k": k,
    }


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
        # `*` statt zweier Spalten (2026-08-09): fuer die Bezugsgroesse unten
        # wird das CRV je Zeile gebraucht, und das kommt aus den Zonenspalten
        # ueber `_zonen_absolut()` - dieselbe Quelle wie ueberall sonst, damit
        # keine zweite Zonenformel entsteht.
        f"SELECT * FROM {table} WHERE outcome_status IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    if erlaubte_symbole is not None:
        rows = [r for r in rows if r["symbol"] in erlaubte_symbole]
    total = len(rows)
    if total == 0:
        # AUSGANGSWERT STATT NICHTS (2026-08-09, Nutzer-Vorgabe: *"ein
        # Ausgangswert kann unabhaengig von der Assetklasse sein - die Regel
        # gilt hier nicht mehr mit der Schrumpfung"*).
        #
        # DIE ALTE REGEL UND WARUM SIE HIER NICHT MEHR GREIFT. Am 18.07. wurde
        # festgelegt: "jede andere Assetklasse bekommt ihre EIGENE
        # Trefferquote statt einer fremden geliehenen Zahl." Das war richtig -
        # gegen eine geliehene Zahl MIT VOLLER AUTORITAET. Der Einwand galt
        # der Autoritaet, nicht der Existenz. Ein Ausgangswert mit GEWICHT 0
        # behauptet nichts; er nennt nur die Latte und weicht der eigenen
        # Messung, sobald es eine gibt.
        #
        # DIE LATTE BRAUCHT KEINE DATEN. Sie folgt aus unserer eigenen
        # CRV-Pflichtgrenze - einer Regel, nicht einer Beobachtung. Damit
        # bekommen auch Aktien, Themen-ETF und Hedge ab dem ersten Tag einen
        # lesbaren Bezugsrahmen statt gar nichts. Vorher fiel der Bezugsrahmen
        # mit der Zahl weg, obwohl er von ihr unabhaengig ist.
        breakeven_ohne_daten = round(100.0 / (1.0 + _CRV_MINIMUM), 1)
        return {
            "anzahl_ausgewertete_signale": 0,
            "trefferquote_pct": None,
            "treffer": 0,
            "fehlschlaege": 0,
            "crv_median": None,
            "breakeven_trefferquote_pct": breakeven_ohne_daten,
            # STATT NULL EIN AUSGANGSWERT. Die neutrale Annahme fuer "wie
            # weit ueber der Latte" ist NULL PROZENTPUNKTE - derselbe Anker
            # wie beim Signalbeitrag der Systemguete, und aus demselben
            # Grund: ohne Information nimmt man an, man liegt weder darueber
            # noch darunter. Ein `None` waere hier kein ehrliches "unbekannt",
            # sondern eine Luecke, aus der das Modell nichts schliessen kann.
            "vorsprung_vor_breakeven_pp": 0.0,
            "trefferquote_gewichtet": breakeven_ohne_daten,
            "gewicht": 0.0,
            # Die kategoriale Zwillingsform sagt AUSDRUECKLICH, dass hier
            # nichts gemessen wurde - statt gar nichts zu sagen.
            "einordnung": "noch keine eigene Messung - Ausgangswert",
            "je_richtung": None,
            "nicht_enthalten_ueberholt": 0,
            "belastbar": False,
            "hinweis": (
                f"NOCH KEINE eigenen ausgewerteten Signale in dieser "
                f"Assetklasse. Der genannte Wert ist der neutrale "
                f"Ausgangswert, KEINE Messung: bei der Pflichtgrenze CRV "
                f"{_CRV_MINIMUM:.1f} liegt der Breakeven bei "
                f"{breakeven_ohne_daten:.1f} % - die Latte, gegen die eine "
                f"kuenftige Trefferquote gehoert, weder gut noch schlecht. "
                f"Gewicht 0: er sagt ueber die bisherige Leistung nichts aus "
                f"und weicht jedem ausgewerteten Signal."),
        }

    treffer = sum(1 for r in rows if r["outcome_status"] == OUTCOME_TAKE_PROFIT)
    fehlschlaege = total - treffer
    trefferquote_pct = round(100.0 * treffer / total, 1)

    # --- BEZUGSGROESSE (2026-08-09) -------------------------------------
    #
    # WARUM. Eine Trefferquote ohne Bezug ist bedeutungslos: sie faellt mit
    # steigendem CRV ZWANGSLAEUFIG, weil das Ziel CRV-mal weiter liegt als der
    # Stop. Genau deshalb haelt crv_baender_kontext_fuer_prompt() seit dem
    # 06.08. fest: "NUR DER ABSTAND ZUR BASISLINIE GEHT IN DEN FAKT, NIE DIE
    # ABSOLUTE QUOTE." Diese Funktion war die letzte Stelle, die den Grundsatz
    # noch verletzte - sie lieferte die nackte Quote (16,0 %) ohne die Latte,
    # gegen die sie gehoert (bei CRV 2,0 sind das 33,3 %).
    #
    # GEMESSEN am 09.08. (Gemini, 36 Anker, gepaart, Rauschboden 0,83 Punkte):
    # die nackte Quote druckt die LONG-Konfidenz um bis zu 33 Punkte und die
    # SHORT-Konfidenz um NULL - eine gerichtete Wirkung ohne sachliche
    # Grundlage (LONG-Trefferquote 16,2 % gegen SHORT 15,0 %). Mit Bezugsrahmen
    # schrumpft die Wirkung um rund 5 Punkte, und die Selbstzustimmung
    # ueberlebt (4,3 % statt 0,0 %).
    #
    # Die Zahlen selbst bleiben unveraendert - es wird nichts beschoenigt,
    # sondern nur der Massstab danebengelegt. "Kontext liefern, Urteil
    # offenlassen."
    crvs = []
    for r in rows:
        z = _zonen_absolut(r)
        if z and z.get("crv"):
            crvs.append(z["crv"])
    crv_median = statistics.median(crvs) if crvs else None
    breakeven_pct = round(100.0 / (1.0 + crv_median), 1) if crv_median else None
    vorsprung_pp = (round(trefferquote_pct - breakeven_pct, 1)
                    if breakeven_pct is not None else None)

    # Wie viele Signale sind aus der Rechnung GEFALLEN, weil sie durch eine
    # neuere Analyse ersetzt wurden? Sie sind weder Treffer noch Fehlschlag -
    # das gehoert dazugesagt, sonst liest sich die Quote vollstaendiger als
    # sie ist. (30,3 % der abgeschlossenen Hebel-Signale, Stand 09.08.)
    ueberholt = conn.execute(
        f"SELECT symbol FROM {table} WHERE outcome_status = ?",
        (OUTCOME_UEBERHOLT,),
    ).fetchall()
    if erlaubte_symbole is not None:
        ueberholt = [r for r in ueberholt if r["symbol"] in erlaubte_symbole]

    teile = []
    if total < _MIN_SAMPLE_FUER_AUSSAGE:
        teile.append(
            f"Basiert auf nur {total} bisher ausgewerteten Signalen - statistisch "
            "NICHT belastbar (Mindeststichprobe fuer eine verlaessliche Aussage: "
            f"{_MIN_SAMPLE_FUER_AUSSAGE}). Nur als sehr grobe Orientierung "
            "verwenden, keinesfalls die Konfidenz allein darauf stuetzen."
        )
    else:
        teile.append(f"Basiert auf {total} bisher ausgewerteten Signalen.")
    if breakeven_pct is not None:
        teile.append(
            f"Zur Einordnung: diese Quote ist NICHT mit 50 % zu vergleichen, "
            f"sondern mit dem Breakeven der eigenen Zielsetzung. Bei einem "
            f"Median-CRV von {crv_median:.2f} liegt er bei {breakeven_pct:.1f} % "
            f"(1/(1+CRV)). Der Abstand betraegt damit {vorsprung_pp:+.1f} "
            f"Prozentpunkte. Eine niedrige absolute Quote bei hohem CRV ist "
            f"rechnerisch normal und fuer sich genommen kein Qualitaetsurteil."
        )
    if ueberholt:
        teile.append(
            f"{len(ueberholt)} Signale sind NICHT enthalten, weil sie vor dem "
            f"Erreichen einer Zone durch eine neuere Analyse ersetzt wurden - "
            f"sie zaehlen weder als Treffer noch als Fehlschlag."
        )

    # --- JE RICHTUNG, MIT SCHRUMPFUNG (2026-08-09) ----------------------
    #
    # WARUM JE RICHTUNG. Der gepoolte Wert ist ein globales negatives Urteil
    # ohne Zuordnung - und das Modell legt es einseitig auf LONG. Gemessen am
    # 09.08.: die Trefferquote druckt die LONG-Konfidenz um bis zu 33 Punkte
    # und die SHORT-Konfidenz um NULL, obwohl LONG mit 16,2 % Trefferquote
    # sogar leicht BESSER liegt als SHORT mit 15,0 %. Wer beide Zahlen zeigt,
    # nimmt dem Modell die Grundlage zum Raten.
    #
    # WARUM MIT SCHRUMPFUNG. Genau hier wird die Stichprobe duenn: SHORT hat
    # rund 20 aufgeloeste Signale. Eine ungeschrumpfte 15-%-Quote aus 20
    # Faellen traete mit derselben Autoritaet auf wie eine aus 200. Die
    # Schrumpfung zum jeweiligen Breakeven macht die Unsicherheit explizit und
    # kalibriert sich mit jedem weiteren Signal von selbst.
    # ALS TABELLE, nicht als Dict von Dicts. Ein Dict je Richtung ergibt drei
    # Verschachtelungsebenen; eine LISTE gleichfoermiger flacher Saetze ist
    # zwei - und sie ist genau die Form, die dieses Projekt an anderer Stelle
    # schon bevorzugt ("Tabelle statt Formel", Kosten-Fakt). Die Richtung wird
    # zum Feld, statt Schluessel zu sein.
    je_richtung = []
    for ri in ("LONG", "SHORT"):
        teil = [r for r in rows if (_spalte(r, "richtung") or "").upper() == ri]
        if not teil:
            continue
        t_treffer = sum(1 for r in teil
                        if r["outcome_status"] == OUTCOME_TAKE_PROFIT)
        t_quote = round(100.0 * t_treffer / len(teil), 1)
        t_crvs = [z["crv"] for z in (_zonen_absolut(r) for r in teil)
                  if z and z.get("crv")]
        t_crv = statistics.median(t_crvs) if t_crvs else None
        t_break = round(100.0 / (1.0 + t_crv), 1) if t_crv else None
        # FLACH und je Richtung SELBSTERKLAEREND: Wert, Latte, Abstand,
        # gewichteter Wert und Gewicht stehen nebeneinander. Vorher lag der
        # gewichtete Wert eine Ebene tiefer in einem `geschrumpft`-Dict, das
        # zusaetzlich `roh`/`neutral`/`n` doppelte - drei Ebenen tief und
        # viermal dieselbe Zahl. Benchmarks skalieren ihre Schwierigkeit an
        # genau dieser Verschachtelungstiefe.
        t_g = schrumpfe_zu_neutral(t_quote, len(teil), t_break)
        je_richtung.append({
            "richtung": ri,
            "anzahl": len(teil),
            "trefferquote_pct": t_quote,
            "crv_median": round(t_crv, 2) if t_crv else None,
            "breakeven_trefferquote_pct": t_break,
            "vorsprung_vor_breakeven_pp": (round(t_quote - t_break, 1)
                                           if t_break is not None else None),
            "trefferquote_gewichtet": t_g["gewichtet"] if t_g else None,
            "gewicht": t_g["gewicht"] if t_g else None,
            "einordnung": einordnung_gegen(t_quote, t_break, 3.0),
        })
    if len(je_richtung) > 1:
        teile.append(
            "Je Richtung getrennt ausgewiesen - ein Gesamtwert ohne "
            "Richtungszuordnung laedt dazu ein, ihn einer Richtung zuzuschlagen. "
            "Die Werte unter `geschrumpft` sind zum jeweiligen Breakeven hin "
            "gewichtet: bei wenigen Signalen zaehlt der Messwert wenig, mit "
            "jedem weiteren mehr (`gewicht` sagt wie viel). Die rohen Zahlen "
            "stehen unveraendert daneben - es wird nichts ersetzt, nur "
            "eingeordnet."
        )

    return {
        "anzahl_ausgewertete_signale": total,
        "trefferquote_pct": trefferquote_pct,
        "treffer": treffer,
        "fehlschlaege": fehlschlaege,
        # Die neuen Felder sind der eigentliche Fakt - die absolute Quote
        # bleibt nur stehen, weil sie eine Tatsache ist, nicht weil sie taugt.
        "crv_median": round(crv_median, 2) if crv_median else None,
        "breakeven_trefferquote_pct": breakeven_pct,
        "vorsprung_vor_breakeven_pp": vorsprung_pp,
        "trefferquote_gewichtet": (_g["gewichtet"] if
                                   (_g := schrumpfe_zu_neutral(
                                       trefferquote_pct, total, breakeven_pct))
                                   else None),
        "gewicht": _g["gewicht"] if _g else None,
        # Die KATEGORIALE Zwillingsform - siehe einordnung_gegen().
        "einordnung": einordnung_gegen(trefferquote_pct, breakeven_pct, 3.0),
        # In BEIDEN Zweigen vorhanden (n=0 und normal). Ein Feld, das mal da
        # ist und mal nicht, ist schlimmer als keines: das Modell kann aus
        # seinem Fehlen nichts schliessen.
        "belastbar": total >= _MIN_SAMPLE_FUER_AUSSAGE,
        "je_richtung": je_richtung or None,
        "nicht_enthalten_ueberholt": len(ueberholt),
        "hinweis": " ".join(teile),
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


# --- CRV-Breakeven-Baender (Population B) ------------------------------------
# ZWEI GRUNDGESAMTHEITEN, bewusst nicht vermischt (Nutzer-Vorgabe 03.08.):
#
#   A "Wie gut ist, was wir TUN?"          -> compute_systemguete()
#     Nur Signale, deren action handelbar war. Ergebnis aus der DB.
#     Bei Hebel real: 148 Faelle (242 mit Zonen minus 94, die nie ein Trade
#     waren, weil die action HALTEN lautete).
#
#   B "Haette das Gate richtig GEFILTERT?" -> diese Funktion
#     ALLE Signale mit Zonen, einheitlich ab created_at neu simuliert - auch
#     vetote und (je nach `mit_halten`) auch nicht gehandelte. Das geplante CRV
#     ist eine Eigenschaft der ZONEN, nicht der Handelsentscheidung.
#
# Wer beides in einen Topf wirft, beantwortet keine der beiden Fragen. Genau
# diese Vermischung hat am 02.08. einen CRV-Befund gekippt.
_CRV_BAENDER = ((0.0, 2.0), (2.0, 2.5), (2.5, 3.0), (3.0, 4.0), (4.0, None))
# Erfolgskriterium ist "Ziel erreicht", NICHT "MFE >= 1R". Gemessen laufen die
# beiden GEGENLAEUFIG: bei CRV >= 4,0 beruehren 51 % einmal 1R, aber nur 7,7 %
# erreichen ihr Ziel - je hoeher das CRV, desto weiter das Ziel. Nur "Ziel
# erreicht" darf gegen den Breakeven 1/(1+CRV) gestellt werden; MFE-Quoten
# wuerden das Band bevorzugen, das sein Ziel am seltensten erreicht.
_BAND_ERFOLGSKRITERIUM = "ziel_erreicht"


def _balkenabstand_median(tage: list) -> float | None:
    """Median-Abstand zwischen zwei Balken der gepruefen Reihe, in Tagen.

    WOZU (2026-08-09, Abnahmelauf zu Mappe Kapitel 9 Stufe 1). Der Bewerter
    nimmt implizit TAGESKERZEN an: die Reihenfolge innerhalb eines Balkens ist
    unbekannt, deshalb gilt "Stop schlaegt Ziel am selben Tag" als konservative
    Konvention. Bei einem Tagesbalken ist das eine milde Annahme. Bei einem
    Balken, der VIER Tage zusammenfasst, ist es ein Muenzwurf.

    Gemessen am 09.08. gegen die 106 bekannten Ausgaenge: der Bewerter
    reproduziert 97 von 100 auswertbaren Faellen. ALLE DREI Fehlschlaege liegen
    auf Reihen mit Median-Balkenabstand 4,0 Tage, alle 97 Treffer auf 1,0.
    Betroffen sind neun Symbole mit je 23 Punkten (BRETT, CANTON, EURCV, IO,
    KAIA, KAITO, SUPRA, VSN, XNO) - darunter KAIA, das verlustreichste Symbol
    ueberhaupt.

    KENNZEICHNEN STATT AUSSCHLIESSEN (Nutzer-Entscheidung 09.08.). Eine Schranke
    analog zur Skalen-Plausibilitaet haette 16,8 % der unaufgeloesten
    Hebel-Signale aus Stufe 2 entfernt - also genau die Faelle, wegen derer die
    Stichprobe verbreitert wird. Stattdessen traegt jedes Ergebnis seine eigene
    Balkendichte, und die auswertende Stelle berichtet getrennt.

    Produktiv aendert das heute nichts: `_simuliere_zeile()` verlangt den vollen
    Horizont, den eine 23-Punkte-Reihe nie erfuellt - 0 von 50 laufenden
    Mark-to-Market-Faellen liegt auf einer duennen Reihe.

    None bei weniger als zwei Balken."""
    if len(tage) < 2:
        return None
    from datetime import date

    def _tag(wert: str) -> date:
        j, m, t = (int(x) for x in str(wert)[:10].split("-"))
        return date(j, m, t)

    try:
        tage_sortiert = [_tag(p["date"]) for p in tage]
    except (ValueError, TypeError, KeyError, IndexError):
        return None
    abstaende = [(tage_sortiert[i + 1] - tage_sortiert[i]).days
                 for i in range(len(tage_sortiert) - 1)]
    if not abstaende:
        return None
    return statistics.median(abstaende)


def simuliere_signal(z: dict, reihe: list, ab_datum: str, horizont: int,
                     voller_horizont_noetig: bool = True) -> dict | None:
    """Ein Signal Tag fuer Tag gegen die Kurshistorie, ab `ab_datum`.

    `voller_horizont_noetig=True` (Default) haelt die alte Bedingung GLEICHE
    BEOBACHTUNGSDAUER (Kontrolle 1 aus Task #602): Signale, deren Reihe den
    Horizont nicht abdeckt, geben None. Das ist richtig, solange die Auswertung
    Ergebnisse einfach mittelt - laenger beobachtete Signale haetten sonst mehr
    Gelegenheit, ihren Stop zu treffen.

    `voller_horizont_noetig=False` gibt sie stattdessen ZENSIERT zurueck
    (`zensiert=True`, `tag` = letzter beobachteter Tag). Nur fuer Auswerter, die
    mit Rechtszensierung umgehen koennen - siehe kumulative_inzidenz(). Dort
    ist das Wegwerfen der teilbeobachteten Faelle nicht noetig, sondern
    schaedlich: bei Horizont 7 fielen dadurch 304 von 759 Hebel-Signalen weg,
    bei Horizont 14 sogar 606.

    Identische Abbruch- und Fill-Logik wie das Backward-Tracking: Stop schlaegt
    Ziel am selben Tag, Ausfuehrung zur Zonen-Grenze bzw. bei einem Gap zum
    Eroeffnungskurs (gap_bewusster_fill). Trifft nichts, wird zum Schlusskurs
    des letzten Tages bewertet - dieselbe Konvention wie in der Basislinie,
    dadurch sind beide Seiten symmetrisch.

    Rueckgabe: `r` (R-Multiple), `ausgang` ('ziel'/'stop'/'offen'), `tag`
    (0-basierter Tagesindex des Ereignisses), `zensiert` (True, wenn bis zum
    letzten beobachteten Tag keine Barriere getroffen wurde) und
    `balkenabstand_median` - die Balkendichte der gepruefen Reihe in Tagen.
    Letzteres ist ein GUETEHINWEIS auf das Ergebnis selbst, kein Nebenwert:
    oberhalb von etwa 1,5 Tagen wird die Konvention "Stop schlaegt Ziel"
    unzuverlaessig, siehe _balkenabstand_median()."""
    tage = [p for p in reihe if p["date"] >= ab_datum][:horizont + 1]
    if voller_horizont_noetig and len(tage) < horizont + 1:
        return None
    if not tage:
        return None
    e, risiko, ist_short = z["entry"], z["risiko"], z["ist_short"]

    # PLAUSIBILITAETSSCHRANKE (2026-08-06): liegen Zonen und Kursreihe
    # ueberhaupt auf derselben Skala?
    #
    # DER FALL, DER DAS AUSLOESTE. OD7C ("WisdomTree Copper", ein ETC) wird bei
    # ~34,63 gehandelt; seine OHLC-Historie holt agent/rohstoff/pipeline.py
    # aber ueber den KUPFER-FUTURES-Ticker HG=F bei ~6,30 USD/lb - und legt sie
    # unter demselben Symbol ab. Ein VERKAUFEN-Signal mit Entry 34,63, Stop
    # 36,00 und Ziel 31,50 wurde dann gegen eine Reihe bei 6,30 bewertet: das
    # Ziel gilt sofort als erreicht, und (34,63 - 6,30) / 1,37 ergibt +20,7 R.
    # Genau dieser eine Trade war die gesamte Evidenz der Assetklasse Rohstoffe.
    #
    # Das ist KEIN Skalierungsfaktor, den man herausrechnen koennte: OD7C liegt
    # bei Faktor 5,49, OD7L bei 1,53, OD7N bei 0,74 - es sind verschiedene
    # Instrumente in verschiedenen Einheiten (lb, MMBtu, Feinunze).
    #
    # Diese Schranke behebt die Ursache NICHT, sie verhindert nur, dass daraus
    # Kennzahlen entstehen. Lieber kein Ergebnis als ein erfundenes. Die
    # Grenze ist bewusst weit (Faktor 3): echte Gaps und Splits bleiben
    # auswertbar, nur ein Instrumenten-Verwechsler faellt heraus.
    # ACHTUNG bei der Zugriffsform: `tage` enthaelt je nach Aufrufer dicts ODER
    # sqlite3.Row. Row kennt kein .get() - ein erster Entwurf dieser Schranke
    # benutzte es und riss die Systemguete-Neuberechnung mit einem
    # AttributeError ab (gefunden im Betrieb, 06.08. 13:19). Indexzugriff
    # funktioniert bei beiden, genau wie in der Schleife darunter.
    erster = next((p["close"] for p in tage if p["close"] is not None), None)
    if erster and e > 0:
        verhaeltnis = max(e / erster, erster / e)
        if verhaeltnis > 3.0:
            logger.warning(
                "Signal-Zonen und Kursreihe liegen auf verschiedenen Skalen "
                "(Entry %.4f gegen Kurs %.4f, Faktor %.2f) - nicht bewertet. "
                "Typische Ursache: die Historie wurde ueber einen Proxy-Ticker "
                "geholt und unter dem echten Symbol abgelegt.",
                e, erster, verhaeltnis,
            )
            return None
    balken = _balkenabstand_median(tage)
    for i, p in enumerate(tage):
        hoch, tief, auf = p["high"], p["low"], p["open"]
        if hoch is None or tief is None:
            continue
        hit_stop = (hoch >= z["stop"]) if ist_short else (tief <= z["stop"])
        hit_ziel = (tief <= z["ziel"]) if ist_short else (hoch >= z["ziel"])
        if hit_stop:
            fill = gap_bewusster_fill(z["stop"], auf, ist_stop=True, ist_short=ist_short)
            return {"r": ((e - fill) if ist_short else (fill - e)) / risiko,
                    "ausgang": "stop", "tag": i, "zensiert": False,
                    "balkenabstand_median": balken}
        if hit_ziel:
            fill = gap_bewusster_fill(z["ziel"], auf, ist_stop=False, ist_short=ist_short)
            return {"r": ((e - fill) if ist_short else (fill - e)) / risiko,
                    "ausgang": "ziel", "tag": i, "zensiert": False,
                    "balkenabstand_median": balken}
    schluss = tage[-1]["close"]
    if not schluss:
        return None
    return {"r": ((e - schluss) if ist_short else (schluss - e)) / risiko,
            "ausgang": "offen", "tag": len(tage) - 1, "zensiert": True,
            "balkenabstand_median": balken}


def spot_symbole_je_tier(watchlist: list | None) -> dict[str, set[str]]:
    """{tier: Symbolmenge} fuer die Spot-Familie, aus der Watchlist.

    WOFUER. Die Tabelle `signals` fuehrt Krypto, Aktien, Rohstoffe und
    Themen-ETF gemeinsam. Wer sie ohne Symbolfilter auswertet, bekommt einen
    Mischtopf und kann hinterher nicht sagen, ob ein Befund krypto-spezifisch
    war - genau der Fehler vom 29.07., gegen den _assetklasse_index() seither
    laut warnt, und genau der Grund, warum Regel 36 bewusst nur fuer
    Krypto-Spot gilt.

    Leere Watchlist -> leeres dict; der Aufrufer faellt dann sichtbar auf den
    Sammel-Topf zurueck, statt still zu mischen."""
    index = _assetklasse_index(watchlist, "spot_symbole_je_tier()")
    je_tier: dict[str, set[str]] = {}
    for symbol in index:
        je_tier.setdefault(_tier_fuer_spot_symbol(symbol, index), set()).add(symbol)
    return je_tier


def kumulative_inzidenz(ereignisse: list[tuple[int, str, str]], horizont: int) -> dict:
    """Aalen-Johansen-Schaetzer fuer zwei konkurrierende Ereignisse (2026-08-03).

    WARUM NICHT EINFACH ZAEHLEN. Unser Aufbau ist die Triple-Barrier-Methode
    (Lopez de Prado): obere Barriere Take-Profit, untere Stop-Loss, vertikale
    das Zeitlimit. Statistisch sind Ziel und Stop KONKURRIERENDE EREIGNISSE mit
    Rechtszensierung am Horizont. Die beiden naheliegenden Abkuerzungen sind
    beide bekannt-falsche Schaetzer:

      Ziel / ALLE Signale      - zaehlt Zensierte als Misserfolg, UNTERSCHAETZT
                                 systematisch. Bei Horizont 7 sind 39 % der
                                 Signale unentschieden - die wurden bisher wie
                                 Verlierer behandelt.
      Ziel / AUFGELOESTE       - Complete-Case-Analyse, verzerrt sobald die
                                 Zensierung informativ ist. Sie ist es: ob ein
                                 Trade aufloest, haengt vom Stop-Abstand ab.
                                 Genau daran brach der Befund vom 02.08.

    Die beiden nebeneinanderzustellen mittelt nicht zwei Wahrheiten, sondern
    zwei Fehler. Der Standardschaetzer fuer diese Lage ist die kumulative
    Inzidenzfunktion.

    DER EIGENTLICHE GEWINN ist aber ein anderer: der Schaetzer braucht KEIN
    vollstaendiges Beobachtungsfenster. Ein Signal mit 3 von 7 Tagen traegt zum
    Risikoset dieser 3 Tage bei und scheidet dann aus, statt weggeworfen zu
    werden. Bei Horizont 14 nutzt das 759 statt 153 Hebel-Signale.

    `ereignisse`: (tag, art, symbol) je Signal, art in 'ziel'/'stop'/'zensiert'.
    Das Symbol wird hier nicht gebraucht, aber durchgereicht - der Bootstrap
    darueber braucht es (siehe _block_bootstrap_ziel_anteil()).

    Rueckgabe: cif_ziel / cif_stop (Wahrscheinlichkeit, die jeweilige Barriere
    BIS zum Horizont zu treffen), `ziel_anteil` = cif_ziel/(cif_ziel+cif_stop) -
    das ist der Wert, der gegen 1/(1+CRV) gehoert, weil beide Seiten des
    Bruchs gleich stark von der Zensierung betroffen sind - und
    `aufloesungsquote` = cif_ziel+cif_stop als Pflicht-Vorbehalt."""
    ziel_je_tag: dict[int, int] = {}
    stop_je_tag: dict[int, int] = {}
    zens_je_tag: dict[int, int] = {}
    for tag, art, _symbol in ereignisse:
        eimer = {"ziel": ziel_je_tag, "stop": stop_je_tag}.get(art, zens_je_tag)
        eimer[tag] = eimer.get(tag, 0) + 1

    n_risiko = len(ereignisse)
    ueberleben = 1.0        # Anteil, der bis hierher KEINE Barriere getroffen hat
    cif_ziel = cif_stop = 0.0
    for tag in range(horizont + 1):
        if n_risiko <= 0:
            break
        z, s = ziel_je_tag.get(tag, 0), stop_je_tag.get(tag, 0)
        if z or s:
            h_ziel, h_stop = z / n_risiko, s / n_risiko
            cif_ziel += ueberleben * h_ziel
            cif_stop += ueberleben * h_stop
            ueberleben *= (1.0 - h_ziel - h_stop)
        # Zensierte scheiden NACH den Ereignissen desselben Tages aus - sie
        # waren an diesem Tag noch unter Risiko.
        n_risiko -= z + s + zens_je_tag.get(tag, 0)

    aufloesung = cif_ziel + cif_stop
    return {
        "cif_ziel": cif_ziel,
        "cif_stop": cif_stop,
        "aufloesungsquote": aufloesung,
        "ziel_anteil": (cif_ziel / aufloesung) if aufloesung > 0 else None,
        "anzahl": len(ereignisse),
        "anzahl_zensiert": sum(zens_je_tag.values()),
    }


def basislinie_ziel_anteil(reihen: dict, stop_rel: float, crv: float, ist_short: bool,
                           horizont: int, ab_datum: str | None = None,
                           bis_datum: str | None = None) -> dict:
    """Wie oft trifft ein ZUFALLSEINSTIEG mit diesen Zonen sein Ziel vor dem Stop?

    DER GRUND, WARUM ES DIESE FUNKTION GEBEN MUSS - nachgewiesen an synthetischen
    Daten mit bekannter Wahrheit (03.08.): Der Vergleich einer bei Horizont H
    abgeschnittenen Trefferquote gegen die arithmetische Formel 1/(1+CRV) ist
    NICHT nur ungenau, er DREHT AB CRV 2,5 DAS VORZEICHEN. Ursache ist die
    Horizont-Trunkierung: das Ziel liegt CRV-mal weiter weg als der Stop und
    wird deshalb systematisch spaeter erreicht. Wer frueh abschneidet,
    uebersamplet Stops - und zwar umso staerker, je hoeher das CRV.

    Gemessen an reinen Zufallseinstiegen, Horizont 7, driftfrei:

        CRV    wahre Quote    gemessen bei H=7    erfasster Anteil
        1,5        39,9 %              32,6 %              82 %
        2,5        28,4 %               7,0 %              25 %
        4,0        20,4 %               0,0 %               0 %

    Bei CRV 4,0 misst ein Zufallseinstieg exakt NULL - ein 4R-Ziel ist in sieben
    Tagen mechanisch kaum erreichbar. Jede Aussage der Form "Band X verfehlt
    seinen Breakeven" ist bei kurzem Horizont also zuerst eine Aussage ueber die
    Erreichbarkeit, nicht ueber die Signalqualitaet.

    DIE LOESUNG ist der Vergleich gegen einen Zufallseinstieg mit DENSELBEN
    Parametern, DEMSELBEN Horizont und DEMSELBEN Zeitfenster: beide Seiten
    tragen denselben Trunkierungsfehler, er kuerzt sich weitgehend heraus. An
    synthetischen Signalen mit echter Kante (+0,3 % Drift) geprueft:

        CRV    wahre Kante    gegen Basislinie    gegen 1/(1+CRV)
        2,0        +24,3 pp           +22,7 pp           +11,7 pp
        2,5        +26,7 pp           +16,7 pp            -1,0 pp
        3,0        +27,5 pp            +8,0 pp           -10,8 pp
        4,0        +31,3 pp            +0,5 pp           -18,4 pp

    Der Basislinien-Vergleich behaelt bei JEDEM CRV das richtige Vorzeichen.
    RESTFEHLER, der bleibt: er unterschaetzt die Staerke mit steigendem CRV
    zunehmend - bei CRV 4,0 und Horizont 7 ist praktisch nichts mehr messbar.
    Das ist eine Grenze der Datenlage, keine des Verfahrens.

    Damit erfuellt diese Funktion die Pflichtangabe aus
    Test_und_Verifikationsmethodik 2.5.7 ("Basislinie je Bucket ist PFLICHT")
    auf der Ebene der Trefferquote - basislinie_erwartungswert() tut dasselbe
    fuer den Erwartungswert."""
    if stop_rel <= 0 or crv <= 0:
        return {"ziel_anteil": None, "anzahl": 0}
    geschnitten = _reihen_im_fenster(reihen, ab_datum, bis_datum)
    ereignisse: list[tuple[int, str, str]] = []
    for symbol, rows in geschnitten.items():
        for i in range(len(rows) - horizont - 1):
            e = rows[i]["close"]
            if not e or e <= 0:
                continue
            risiko = e * stop_rel
            z = {
                "entry": e,
                "stop": e + risiko if ist_short else e - risiko,
                "ziel": e - risiko * crv if ist_short else e + risiko * crv,
                "risiko": risiko,
                "ist_short": ist_short,
            }
            # AB i+1, NICHT ab i: der Einstieg ist der SCHLUSSKURS von Tag i,
            # dessen Hoch und Tief liegen zeitlich davor. Simuliert man Tag i
            # mit, treffen Ziehungen systematisch den naeheren Stop und NIE das
            # weiter entfernte Ziel - an 2000 Kandidaten gemessen: 249 Treffer
            # am Tag 0, davon 249 Stop und 0 Ziel. basislinie_erwartungswert()
            # macht es seit jeher richtig (rr[i+1:...]); hier fehlte der Versatz.
            sim = simuliere_signal(z, rows[i + 1:], rows[i + 1]["date"], horizont,
                                   voller_horizont_noetig=False)
            if sim is None:
                continue
            ereignisse.append((sim["tag"],
                               "zensiert" if sim["zensiert"] else sim["ausgang"],
                               symbol))
    if len(ereignisse) < _BASISLINIE_MIN_EINSTIEGE:
        return {"ziel_anteil": None, "anzahl": len(ereignisse)}
    ki = kumulative_inzidenz(ereignisse, horizont)
    return {"ziel_anteil": ki["ziel_anteil"], "anzahl": len(ereignisse),
            "aufloesungsquote": ki["aufloesungsquote"]}


def _block_bootstrap_ziel_anteil(ereignisse: list[tuple[int, str, str]], horizont: int,
                                 ziehungen: int = _BOOTSTRAP_ZIEHUNGEN) -> tuple:
    """95%-Intervall fuer `ziel_anteil`, gezogen ueber SYMBOLE statt Signale.

    Ein gewoehnliches Wilson-Intervall unterstellt unabhaengige Beobachtungen.
    Unsere sind es nicht: einzelne Symbole stellen bis zu einem Drittel eines
    Bandes (VIRTUAL 33 %, HYPE 27 %), dazu ueberlappen sich die Zeitfenster.
    Wilson faellt dadurch zu ENG aus, und ein Band gilt zu leicht als belastbar.

    Deshalb Block-Bootstrap: gezogen werden ganze Symbole mit Zuruecklegen,
    nicht einzelne Signale. Damit bleibt die Abhaengigkeit innerhalb eines
    Symbols erhalten und schlaegt sich in der Intervallbreite nieder."""
    je_symbol: dict[str, list] = {}
    for e in ereignisse:
        je_symbol.setdefault(e[2], []).append(e)
    symbole = list(je_symbol)
    if len(symbole) < 2:
        return (None, None)
    rng = random.Random(_BOOTSTRAP_SEED)
    werte: list[float] = []
    for _ in range(ziehungen):
        probe: list[tuple[int, str, str]] = []
        for _ in range(len(symbole)):
            probe.extend(je_symbol[symbole[rng.randrange(len(symbole))]])
        anteil = kumulative_inzidenz(probe, horizont)["ziel_anteil"]
        if anteil is not None:
            werte.append(anteil)
    if len(werte) < 20:
        return (None, None)
    werte.sort()
    unten = werte[max(0, int(0.025 * len(werte)) - 1)]
    oben = werte[min(len(werte) - 1, int(0.975 * len(werte)))]
    return (unten, oben)


def compute_crv_breakeven_baender(
    conn, tier: str, horizont: int = 7, mit_halten: bool = True,
    erlaubte_symbole: set[str] | None = None, reihen: dict | None = None,
) -> dict | None:
    """Trefferquote je CRV-Band gegen den Breakeven 1/(1+CRV) - Population B.

    DIE LEITGROESSE. Expectancy = q*CRV - (1-q) > 0 ist gleichbedeutend mit
    q > 1/(1+CRV). "Expectancy-Gate" und "Abstand zum CRV-Breakeven" sind
    dieselbe Formel unter zwei Namen. Anders als ein reiner Erwartungswert
    laesst sich der Breakeven-Abstand NICHT durch weniger Handeln verbessern -
    er steigt nur, wenn mehr gute Signale kommen. Und weil die Schwelle mit
    steigendem CRV faellt (2,0 -> 33,3 %; 4,0 -> 20,0 %), ist er zugleich das
    gleitende Gate, das die starre 2,0-Grenze einmal ersetzen kann.

    SURVIVORSHIP-FREI: bewertet wird jedes Signal mit Zonen durch Neusimulation,
    nicht der DB-Status. Ob ein Signal aufloest, haengt vom Stop-Abstand ab -
    wer nur aufgeloeste Faelle vergleicht, vergleicht Selektionsgrade. Genau
    daran brach die Messung vom 02.08.

    `mit_halten`: nimmt Signale mit nicht handelbarer action (HALTEN) mit auf.
    Dafuer spricht, dass das CRV eine Eigenschaft der Zonen ist und die Menge
    deutlich groesser wird; dagegen, dass das Modell dort nichts riskieren
    wollte und seine Zonen weniger sorgfaeltig gesetzt haben koennte. BEWUSST
    NICHT vorab entschieden - beide Varianten werden gerechnet und
    gegeneinander geprueft (Schritt 2b, walk-forward).

    `belastbar` je Band heisst: mindestens _MIN_SAMPLE_FUER_AUSSAGE Faelle UND
    das Konfidenzintervall schliesst den Breakeven nicht ein. Nur dann taugt
    das Band fuer eine SCHWELLE. Als informierender Fakt fuer das LLM ist auch
    ein nicht belastbares Band brauchbar, solange die Unsicherheit mitgeliefert
    wird - das ist der Unterschied zwischen "informieren" und "blockieren".

    Reine Lesefunktion. None, wenn keine Kursreihen oder keine Signale."""
    table = _tabelle_fuer_tier(tier, "compute_crv_breakeven_baender()")
    if reihen is None:
        reihen = lade_kursreihen(conn)
    if not reihen:
        return None
    # _HEBEL_TRACKABLE_ACTIONS_FUER_UEBERSICHT statt des Originals aus
    # hebel_backward_tracking.py - dieses Modul kann von dort nicht importieren
    # (Kreisimport), siehe Kommentar an der Konstanten.
    trackable = (_HEBEL_TRACKABLE_ACTIONS_FUER_UEBERSICHT if table == "hebel_signals"
                 else _TRACKABLE_ACTIONS)
    rows = conn.execute(
        f"SELECT * FROM {table} WHERE take_profit_usd_von IS NOT NULL"
    ).fetchall()

    faelle: list[dict] = []
    ohne_kursreihe = 0
    action_mix: dict[str, int] = {}
    for row in rows:
        if erlaubte_symbole is not None and row["symbol"] not in erlaubte_symbole:
            continue
        handelbar = row["action"] in trackable
        if not handelbar and not mit_halten:
            continue
        z = _zonen_absolut(row)
        if z is None or row["symbol"] not in reihen:
            continue
        # voller_horizont_noetig=False: teilbeobachtete Signale werden ZENSIERT
        # mitgezaehlt statt weggeworfen - der ganze Punkt des Schaetzers.
        sim = simuliere_signal(z, reihen[row["symbol"]], str(row["created_at"])[:10],
                               horizont, voller_horizont_noetig=False)
        if sim is None:
            ohne_kursreihe += 1
            continue
        action_mix[str(row["action"])] = action_mix.get(str(row["action"]), 0) + 1
        faelle.append({"crv": z["crv"], "stop_rel": z["stop_rel"],
                       "ist_short": z["ist_short"], "r": sim["r"],
                       "ausgang": sim["ausgang"], "tag": sim["tag"],
                       "zensiert": sim["zensiert"], "symbol": row["symbol"],
                       "datum": str(row["created_at"])[:10]})
    if not faelle:
        return None

    baender = []
    for von, bis in _CRV_BAENDER:
        teil = [f for f in faelle if f["crv"] >= von and (bis is None or f["crv"] < bis)]
        n = len(teil)
        if n == 0:
            continue
        crv_median = statistics.median(f["crv"] for f in teil)
        breakeven = 1.0 / (1.0 + crv_median)
        # Der Schaetzer: konkurrierende Ereignisse mit Rechtszensierung.
        ereignisse = [(f["tag"], "zensiert" if f["zensiert"] else f["ausgang"], f["symbol"])
                      for f in teil]
        ki = kumulative_inzidenz(ereignisse, horizont)
        anteil = ki["ziel_anteil"]
        ki_unten, ki_oben = _block_bootstrap_ziel_anteil(ereignisse, horizont)
        # LEITGROESSE: Abstand zu einem Zufallseinstieg mit denselben Zonen,
        # demselben Horizont und demselben Zeitfenster. Nur so kuerzt sich die
        # Horizont-Trunkierung heraus - der Vergleich gegen 1/(1+CRV) dreht ab
        # CRV 2,5 das Vorzeichen (siehe basislinie_ziel_anteil()).
        tage_band = sorted(f["datum"] for f in teil)
        bis_band = (datetime.fromisoformat(tage_band[-1])
                    + timedelta(days=horizont)).date().isoformat()
        bl = basislinie_ziel_anteil(
            reihen, statistics.median(f["stop_rel"] for f in teil), crv_median,
            ist_short=sum(1 for f in teil if f["ist_short"]) / n > 0.5,
            horizont=horizont, ab_datum=tage_band[0], bis_datum=bis_band,
        )
        bl_anteil = bl["ziel_anteil"]
        abstand_basislinie = (None if (anteil is None or bl_anteil is None)
                              else round((anteil - bl_anteil) * 100, 1))
        # Die beiden bekannt-falschen Abkuerzungen bleiben als Kontrolle
        # sichtbar - weichen sie stark vom Schaetzer ab, lohnt ein Blick.
        ziel_roh = sum(1 for f in teil if f["ausgang"] == "ziel")
        stop_roh = sum(1 for f in teil if f["ausgang"] == "stop")
        aufgeloest_roh = ziel_roh + stop_roh
        zaehler: dict[str, int] = {}
        for f in teil:
            zaehler[f["symbol"]] = zaehler.get(f["symbol"], 0) + 1
        top_symbol, top_n = max(zaehler.items(), key=lambda x: x[1])
        baender.append({
            "crv_von": von,
            "crv_bis": bis,
            "anzahl": n,
            "anzahl_zensiert": ki["anzahl_zensiert"],
            "crv_median": round(crv_median, 2),
            # Zensierungsbereinigter Anteil Ziel-vor-Stop BIS zum Horizont.
            # Absolut NICHT interpretierbar - nur im Vergleich zur Basislinie.
            "ziel_anteil_pct": None if anteil is None else round(anteil * 100, 1),
            # LEITGROESSE.
            "basislinie_ziel_anteil_pct": (None if bl_anteil is None
                                           else round(bl_anteil * 100, 1)),
            "basislinie_anzahl": bl["anzahl"],
            "abstand_zur_basislinie_pp": abstand_basislinie,
            # NACHRANGIG, bewusst nicht mehr die Leitgroesse: der Vergleich gegen
            # die arithmetische Formel unterstellt einen abgeschlossenen Trade.
            # Bei unseren Horizonten dreht er ab CRV 2,5 das Vorzeichen - nur
            # als Kontext lesen, nie als Urteil.
            "breakeven_formel_pct": round(breakeven * 100, 1),
            "abstand_zur_formel_pp": (None if anteil is None
                                      else round((anteil - breakeven) * 100, 1)),
            "ki_unten_pct": None if ki_unten is None else round(ki_unten * 100, 1),
            "ki_oben_pct": None if ki_oben is None else round(ki_oben * 100, 1),
            # Anteil, der bis zum Horizont ueberhaupt eine Barriere trifft -
            # Pflichtangabe: je niedriger, desto mehr steckt der Punktwert in
            # der Hochrechnung statt in beobachteten Faellen.
            "aufloesungsquote_pct": round(ki["aufloesungsquote"] * 100, 1),
            # Fuer eine SCHWELLE reicht der Punktwert nicht - das Intervall muss
            # die BASISLINIE verfehlen (nicht die Formel, siehe oben). Das
            # Intervall stammt aus dem Block-Bootstrap ueber Symbole, nicht aus
            # Wilson: einzelne Symbole stellen bis zu einem Drittel eines Bandes.
            # ENTARTETE INTERVALLE ZAEHLEN NICHT (Fund 04.08. am Notebook-Export):
            # Erreicht in einem Band kein einziger Fall sein Ziel, liefert der
            # Bootstrap in jeder Ziehung 0,0 - das Intervall [0,0 .. 0,0] verfehlt
            # die Basislinie dann rein rechnerisch und galt als "belastbar".
            # Beobachtet bei krypto >= 4,0: n=20, davon 6 aufgeloest, alle Stop.
            # Ein Intervall ohne Breite ist keine Signifikanz, sondern ein
            # Randfall - deshalb zusaetzlich eine Mindestbreite verlangen.
            "belastbar": bool(
                n >= _MIN_SAMPLE_FUER_AUSSAGE and anteil is not None
                and ki_unten is not None and bl_anteil is not None
                and (ki_oben - ki_unten) > 1e-9
                and (ki_unten > bl_anteil or ki_oben < bl_anteil)
            ),
            "erwartungswert_r": round(statistics.fmean(f["r"] for f in teil), 4),
            # Kontrollwerte, bewusst mitgefuehrt (siehe kumulative_inzidenz()):
            "kontrolle_ziel_durch_alle_pct": round(ziel_roh / n * 100, 1),
            "kontrolle_ziel_durch_aufgeloeste_pct": (
                None if aufgeloest_roh == 0 else round(ziel_roh / aufgeloest_roh * 100, 1)),
            "groesstes_symbol": top_symbol,
            "groesstes_symbol_anteil_pct": round(top_n / n * 100, 1),
        })

    belastbare = sum(1 for b in baender if b["belastbar"])
    return {
        "tier": tier,
        "horizont_tage": horizont,
        "messgroesse": _BAND_ERFOLGSKRITERIUM,
        "mit_halten_signalen": mit_halten,
        "anzahl_signale": len(faelle),
        "anzahl_ohne_kursreihe": ohne_kursreihe,
        "schaetzer": "kumulative_inzidenz_aalen_johansen",
        "action_mix": action_mix,
        "baender": baender,
        "hinweis": (
            f"{len(faelle)} Signale mit Zonen, neu simuliert ueber {horizont} Tage. "
            "LESEART: Nur `abstand_zur_basislinie_pp` ist interpretierbar - der "
            "Vergleich mit einem Zufallseinstieg gleicher Zonen, gleichen "
            "Horizonts und gleichen Zeitfensters. Der absolute `ziel_anteil_pct` "
            "ist es NICHT: bei kurzem Horizont wird ein weit entferntes Ziel "
            "seltener erreicht, unabhaengig von der Signalqualitaet - bei CRV 4,0 "
            "und Horizont 7 misst selbst ein Zufallseinstieg 0,0 %. Aus demselben "
            "Grund ist `abstand_zur_formel_pp` (gegen 1/(1+CRV)) nur Kontext: er "
            "dreht ab CRV 2,5 das Vorzeichen. "
            "Geschaetzt wird per kumulativer Inzidenz mit Rechtszensierung - "
            "teilbeobachtete Signale zaehlen bis zu ihrem Zensierungszeitpunkt "
            "mit, statt weggeworfen zu werden. Erfolgskriterium ist ZIEL "
            "ERREICHT, nicht 'MFE >= 1R'. Konfidenzintervalle per Block-Bootstrap "
            f"ueber Symbole. {belastbare} von {len(baender)} Baendern trennen "
            "sich belastbar von ihrer Basislinie; die uebrigen sind eine "
            "Groessenordnung. aufloesungsquote_pct mitlesen: je niedriger, desto "
            "mehr steckt der Wert in der Hochrechnung."
        ),
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


def _eur_je_usd(schnappschuss) -> float | None:
    """Aus derselben Cache-Zeile, nicht aus einer zweiten Quelle."""
    try:
        if schnappschuss and schnappschuss.price_usd and schnappschuss.price_eur:
            return float(schnappschuss.price_eur) / float(schnappschuss.price_usd)
    except Exception:
        pass
    return None


_AR_SCHLIESSEN = "SCHLIESSEN"
_AR_NACHZIEHEN = "STOP NACHZIEHEN"


def compute_ausstiegs_empfehlungen(conn, watchlist: list | None = None,
                                   config: dict | None = None,
                                   seit_tag: str | None = None) -> dict:
    """Offene Signale, bei denen der Trailing-Stop nachgezogen gehoert.

    ADVISORY-ONLY (P-7). Rechnet und meldet, greift nicht ein - der Nutzer
    entscheidet und fuehrt aus. Kein Gate, kein Veto, keine Positions-
    aenderung.

    DER BEFUND DAHINTER (04.08.): 50 % der Signale standen einmal bei +1R,
    nur 17,6 % kamen am Ziel an. Positionen geben Gewinne zurueck. Der
    Trailing-Stop ab +1R hebt den Erwartungswert von -0,176 auf -0,084 R
    (495 echte Signale), symbolgeblocktes Intervall [+0,051; +0,131],
    haelt im Split-Sample und ueber alle drei Marktphasen. Herleitung und
    Abgrenzung zum verworfenen Breakeven-Lock in ausstiegsregel.py.

    KEINE NEUE BERECHNUNG NOETIG. `outcome_max_realisiertes_crv` wird seit
    dem 02.08. bei jedem Backward-Tracking-Lauf fortgeschrieben, auch fuer
    OFFENE Signale - das ist bereits der hoechste erreichte Buchgewinn in R
    und damit exakt die Eingabe der Regel. Ohne diese Vorarbeit braeuchte es
    hier eine eigene Kursreihen-Auswertung.

    Reine Lesefunktion. Gibt {'empfehlungen': [...], 'geprueft': n,
    'parameter': {...}} zurueck, absteigend nach MFE - der groesste
    ungesicherte Buchgewinn zuerst."""
    ausloese, abstand, aktiv = parameter_aus_config(config or {})
    # Nachlese-Fenster fuer erreichte Ziele: standardmaessig die letzten zwei
    # Tage. Ein Tag waere zu knapp - faellt ein Lauf aus, bliebe der Verkauf
    # ungemeldet, und genau das soll die Nachlese verhindern.
    if seit_tag is None:
        from datetime import date, timedelta
        seit_tag = (date.today() - timedelta(days=2)).isoformat()
    ergebnis: dict = {"empfehlungen": [], "alle": [], "geprueft": 0,
                      "parameter": {"ausloese_r": ausloese, "abstand_r": abstand,
                                    "aktiv": aktiv}}
    if not aktiv:
        ergebnis["hinweis"] = "ueber config abgeschaltet (ausstieg_trailing_*)"
        return ergebnis

    assetklasse_by_symbol = _assetklasse_index(
        watchlist, "compute_ausstiegs_empfehlungen()")
    # Der aktuelle Kurs wird fuer den Widerlegungspreis gebraucht - der
    # Trailing-Stop allein kommt ohne ihn aus.
    try:
        preise = db.get_latest_prices(conn)
    except Exception:
        logger.exception("Kurse fuer die Ausstiegspruefung nicht ladbar")
        preise = {}
    # ECHTER BESTAND GEGEN BLOSSE SIGNALVERFOLGUNG (Nutzerfund 13.08.):
    # *"Diese Aktionen sind teilweise fiktiv."* Richtig - `signals` enthaelt
    # EMPFEHLUNGEN, nicht Positionen. Von 45 Signal-Symbolen lagen 28 gar nicht
    # im Bestand; dort waere "SCHLIESSEN" eine Anweisung fuer etwas, das es
    # nicht gibt. Was gehalten wird, steht in `holdings` und `hebel_positions`.
    # ⚠️ GESTAKTES IST GEHALTEN (17.08.2026). `quantity` ist der FREIE
    # Wallet-Bestand - Bitpanda bucht einen Stake als Abgang aus der Wallet,
    # das Gestakte kommt additiv in `staked_quantity` dazu (live verifiziert,
    # siehe `importer/bitpanda_avg_cost.compute_staked_quantities`). Ein
    # vollstaendig gestakter Wert stand hier deshalb als NICHT gehalten, und
    # seine Ausstiegsfuehrung galt als blosse Signalverfolgung. Der Nutzer
    # haelt SOL seit Langem; im Export haben 23 von 56 Zeilen die Menge 0.
    #
    # ⚠️ UND JE INSTRUMENT GETRENNT (17.08.2026, Nutzerfund an einer
    # BTC-Hebelmail). Beide Mengen standen bis heute in EINEM `gehalten`:
    #
    #     Abschnitt 1:  In BTC besteht keine offene Hebelposition.
    #     Abschnitt 2:  Bestehende Position: Empfehlung HALTEN
    #
    # BTC liegt im SPOT-Bestand - damit galt `ist_bestand` auch im
    # HEBEL-Lauf, und die Mail widersprach sich zwanzig Zeilen weiter.
    # Es ist derselbe Fehler wie am 15.08. beim Bestandsblock ("meinte
    # den SPOT-Bestand"), nur an der Kennzeichnung statt an den Fakten.
    try:
        gehalten_spot = {r[0] for r in conn.execute(
            "SELECT symbol FROM holdings WHERE "
            "COALESCE(quantity, 0) + COALESCE(staked_quantity, 0) > 0")}
    except Exception:
        gehalten_spot = set()
    try:
        gehalten_hebel = {r[0] for r in conn.execute(
            "SELECT symbol FROM hebel_positions WHERE status = 'offen'")}
    except Exception:
        gehalten_hebel = set()
    for tabelle, ist_hebel in (("signals", False), ("hebel_signals", True)):
        spalten = {r[1] for r in conn.execute(f"PRAGMA table_info({tabelle})")}
        if "outcome_max_realisiertes_crv" not in spalten:
            continue
        zonen_spalten = [c for c in (
            "entry_usd_von", "entry_usd_bis", "entry_usd",
            "stop_loss_usd_von", "stop_loss_usd_bis", "stop_loss_usd",
            "take_profit_usd_von", "take_profit_usd_bis", "take_profit_usd",
        ) if c in spalten]
        # DIE ID MUSS MIT (14.08.2026). Ohne sie kann die Ausstiegsmail nicht
        # sagen, WELCHES Signal meldet - und mehrere offene Signale je Symbol
        # sind der Normalfall, nicht die Ausnahme: am 14.08. hatten DBPK und
        # OD7L je fuenf, 3QSS vier, MON und OD7C drei.
        #
        # DAS IST SO GEWOLLT. `_is_superseded()` raeumt aeltere Signale ab,
        # aber erst nach der Mindestbeobachtung - sonst waere ein Signal tot,
        # bevor es messbar wird. Solange beide offen sind, muss der Leser sie
        # auseinanderhalten koennen.
        felder = ("id, symbol, created_at, action, outcome_status, "
                  "outcome_max_realisiertes_crv"
                  + "".join(f", {c}" for c in zonen_spalten)
                  + "".join(f", {c}" for c in
                            ("umgeworfen_preis_eur", "umgeworfen_bis",
                             "umgeworfen_durch") if c in spalten))
        rows = conn.execute(
            f"SELECT {felder} FROM {tabelle} "
            f"WHERE outcome_status = ? AND outcome_max_realisiertes_crv IS NOT NULL "
            f"AND take_profit_usd_von IS NOT NULL",
            (OUTCOME_OFFEN,),
        ).fetchall()
        for row in rows:
            ergebnis["geprueft"] += 1
            z = _zonen_absolut(row)
            if z is None:
                continue
            # VOLLE AUSSTIEGSPRUEFUNG FUER JEDE OFFENE POSITION (13.08.2026).
            #
            # Bisher stand hier nur der Trailing-Stop, und darunter ein
            # `continue` fuer alles, was ihn nicht ausgeloest hat. Damit wurde
            # eine Position unter +1 R NIE geprueft - auch nicht darauf, ob der
            # Kurs den Preis erreicht hat, bei dem das Modell seine eigene
            # Begruendung fuer widerlegt erklaerte. Genau dort ist die Pruefung
            # aber am wichtigsten: eine Position im Minus hat den Trailing-Stop
            # per Definition nicht ausgeloest.
            #
            # WAEHRUNG: die Zonen stehen in USD (`entry_usd_*`), die Mail
            # spricht EUR. Umgerechnet wird HIER, mit demselben Kurs fuer alle
            # Werte einer Zeile - zwei Waehrungen nebeneinander sind der
            # dokumentierte Fehler aus Umbauplan 12.5.
            from agent import ausstiegsrechnung as _AR

            kurs_usd = (preise.get(row["symbol"]).price_usd
                        if preise.get(row["symbol"]) else None)
            # ⚠️ DER WIDERLEGUNGSPREIS STEHT IN EUR - ALLES ANDERE HIER IN USD
            # (gefunden 20.08.2026, Kapitel 94).
            #
            # `bewerte()` vergleicht ihn direkt mit `kurs_aktuell`, und der ist
            # USD. Die Spalte `umgeworfen_preis_eur` kommt dagegen aus der
            # Modellantwort, und dort ist sie EUR: `entscheidungsrechnung`
            # prueft denselben Wert gegen den EUR-Kurs. Beide Enden
            # nachverfolgt, nicht geraten.
            #
            # Die Folge war KEIN Anzeigefehler, sondern eine falsche
            # Entscheidung: EUR liegt rund 14 % unter USD, also loeste die
            # Widerlegung bei LONG zu spaet aus und bei SHORT zu frueh - und
            # sie fuehrt zur Empfehlung SCHLIESSEN.
            _fx = _eur_je_usd(preise.get(row["symbol"]))
            _umg_eur = (row["umgeworfen_preis_eur"]
                        if "umgeworfen_preis_eur" in spalten else None)
            # Ohne Faktor lieber KEINE Widerlegungspruefung als eine in der
            # falschen Waehrung - dieselbe Regel wie in `_in_eur`.
            _umg_usd = (float(_umg_eur) / float(_fx)
                        if _umg_eur and _fx else None)
            voll = _AR.bewerte(
                einstieg=z["entry"], stop_original=z["stop"],
                kurs_aktuell=kurs_usd, ziel=z.get("ziel"),
                mfe_r=row["outcome_max_realisiertes_crv"],
                ist_short=z["ist_short"],
                umgeworfen_preis=_umg_usd,
                umgeworfen_bis=(row["umgeworfen_bis"]
                                if "umgeworfen_bis" in spalten else None),
                umgeworfen_durch=(row["umgeworfen_durch"]
                                  if "umgeworfen_durch" in spalten else None),
                ausloese_r=ausloese, abstand_r=abstand)
            if voll:
                ergebnis["alle"].append({
                    "symbol": row["symbol"], "seit": str(row["created_at"])[:10],
                "signal_id": row["id"], "ist_hebel": ist_hebel,
                "ur_aktion": row["action"],
                    "richtung": "SHORT" if z["ist_short"] else "LONG",
                    "tier": TIER_HEBEL if ist_hebel else _tier_fuer_spot_symbol(
                        row["symbol"], assetklasse_by_symbol),
                    "kurs_usd": kurs_usd,
                    # EUR ist die Waehrung des Nutzers. Der Faktor kommt aus
                    # DERSELBEN Zeile des Preis-Caches (price_eur/price_usd) -
                    # eine zweite Umrechnungsquelle waere eine zweite Wahrheit.
                    "eur_je_usd": _eur_je_usd(preise.get(row["symbol"])),
                    # DAS EIGENE INSTRUMENT entscheidet, ob es eine
                    # Position ist. Die andere Seite wird BENANNT statt
                    # verschwiegen - sie gehoert dem Leser, nur eben
                    # nicht unter dieser Ueberschrift.
                    "ist_bestand": row["symbol"] in (
                        gehalten_hebel if ist_hebel else gehalten_spot),
                    "ist_bestand_gegenseite": row["symbol"] in (
                        gehalten_spot if ist_hebel else gehalten_hebel),
                    **voll})

            e = stopempfehlung_aus_mfe(
                z["entry"], z["stop"], row["outcome_max_realisiertes_crv"],
                ist_short=z["ist_short"], ausloese_r=ausloese, abstand_r=abstand)
            if e is None or not e.aktiv:
                continue
            ergebnis["empfehlungen"].append({
                "tier": TIER_HEBEL if ist_hebel else _tier_fuer_spot_symbol(
                    row["symbol"], assetklasse_by_symbol),
                "symbol": row["symbol"],
                "signal_id": row["id"], "ist_hebel": ist_hebel,
                "ur_aktion": row["action"],
                "seit": str(row["created_at"])[:10],
                "richtung": "SHORT" if z["ist_short"] else "LONG",
                "mfe_r": round(e.mfe_r, 3),
                "entry": z["entry"],
                "stop_bisher": z["stop"],
                "stop_empfohlen": e.stop_empfohlen,
                "sichert_r": round(e.gesicherte_r, 3),
                "begruendung": e.begruendung,
            })
    # ---- ZIEL ERREICHT, ABER NOCH IM BESTAND (Nutzerfund 13.08.) ----
    #
    # DIE LUECKE: *"Take-Profit steht nicht mehr hier, wenn im Bestand - ok,
    # aber zuvor sollte ich doch informiert werden, dass eine Aktion - Verkauf
    # - ansteht, oder?"* Genau. Bisher passierte beim Zielerreichen dies:
    #
    #     logger.info("Backward-Tracking: %d Take-Profit, ...")
    #
    # Ein Logeintrag. Keine Nachricht. Das Tracking verbucht "gewonnen" - und
    # der Wert liegt weiter im Depot, waehrend der Kurs zurueckkommen kann.
    # Das ist dieselbe Luecke wie die 50/17,6-Prozent-Zahl, nur an ihrem
    # oberen Ende: dort geben Positionen Gewinne zurueck, hier wird der
    # Gewinn nicht einmal gemeldet.
    #
    # DAS TRACKING LAEUFT UM 6:00, DIESER JOB UM 7:15 - zum Zeitpunkt der Mail
    # ist das Signal also nicht mehr `offen` und faellt aus der Schleife oben
    # heraus. Deshalb wird hier ein zweites Mal nachgesehen, nach Ausgang
    # statt nach Zustand.
    ergebnis["ziel_erreicht"] = []
    for tabelle, ist_hebel in (("signals", False), ("hebel_signals", True)):
        spalten = {r[1] for r in conn.execute(f"PRAGMA table_info({tabelle})")}
        if not {"outcome_status", "outcome_entschieden_am"} <= spalten:
            continue
        try:
            rows = conn.execute(
                f"SELECT symbol, outcome_entschieden_am, outcome_realisiertes_crv "
                f"FROM {tabelle} WHERE outcome_status = ? "
                f"AND outcome_entschieden_am >= ?",
                (OUTCOME_TAKE_PROFIT, seit_tag)).fetchall()
        except Exception:
            logger.exception("Take-Profit-Nachlese fuer %s fehlgeschlagen", tabelle)
            continue
        for row in rows:
            # NUR WAS WIRKLICH IM DEPOT LIEGT. Ein erreichtes Ziel auf einem
            # nie gekauften Signal ist ein Messpunkt, kein Verkaufsauftrag.
            #
            # ⚠️ UND ZWAR IM PASSENDEN INSTRUMENT (17.08.2026). Hier stand
            # das verschmolzene `gehalten` - ein Spot-Bestand haette einen
            # Verkaufshinweis fuer eine Hebelposition erzeugt, die es nicht
            # gibt. `finde_freie_namen.py` hat diese Zeile gefunden,
            # nachdem die Menge oben aufgeteilt war; ohne das Werkzeug waere
            # sie ein NameError hinter einem breiten Fang gewesen.
            if row["symbol"] not in (gehalten_hebel if ist_hebel
                                     else gehalten_spot):
                continue
            ergebnis["ziel_erreicht"].append({
                "symbol": row["symbol"],
                "tier": TIER_HEBEL if ist_hebel else _tier_fuer_spot_symbol(
                    row["symbol"], assetklasse_by_symbol),
                "am": str(row["outcome_entschieden_am"])[:10],
                "crv": row["outcome_realisiertes_crv"],
                "ist_bestand": True})

    ergebnis["empfehlungen"].sort(key=lambda x: -x["mfe_r"])
    # Dringlichstes zuerst: SCHLIESSEN, dann STOP NACHZIEHEN, dann der Rest -
    # nicht nach Buchgewinn. Der groesste ungesicherte Gewinn ist nicht
    # automatisch der dringendste Fall.
    _rang = {_AR_SCHLIESSEN: 0, _AR_NACHZIEHEN: 1}
    ergebnis["alle"].sort(key=lambda x: (
        _rang.get(x["empfehlung"].split(" · ")[0], 2), -(x.get("mfe_r") or 0)))
    return ergebnis


# Datum des Nur-Long-Umbaus. Ab hier erreichen SHORT-Kandidaten das LLM und
# SHORT-Empfehlungen laufen normal durch - davor wurden sie vorgefiltert oder
# vom Risk-Gate auf HALTEN gedreht. Jede Auswertung ueber diese Grenze hinweg
# mischt zwei Populationen (Testmethodik 2.1b, Bruchstellen-Tabelle).
UMBAU_NUR_LONG_AB = "2026-08-05"


def compute_richtungsverteilung(conn, watchlist: list | None = None,
                                ab_datum: str = UMBAU_NUR_LONG_AB) -> dict:
    """LONG gegen SHORT seit dem Nur-Long-Umbau (2026-08-05).

    WOFUER. Bis zum 05.08. war diese Frage nicht sinnvoll zu stellen: SHORT-
    Kandidaten wurden vor dem LLM-Aufruf weggefiltert, und was das Modell
    trotzdem als SHORT empfahl, drehte das Risk-Gate auf HALTEN. Die 313
    Altfaelle liegen deshalb als "HALTEN" in der Datenbank und haben bei der
    Ursachensuche zum 31.07.-Bruch wiederholt Populationen vermischt.

    Seit dem Umbau laufen beide Richtungen normal durch - erst dadurch wird
    messbar, ob das Modell in eine Richtung besser liegt.

    WAS DIE ZAHLEN NOCH NICHT SAGEN. Direkt nach dem Umbau ist n klein, und
    ein frueher Blick auf eine kleine Stichprobe verleitet zu Schluessen, die
    beim naechsten Dutzend Signale kippen. Deshalb wird `belastbar` erst ab 30
    aufgeloesten Faellen je Richtung gesetzt - darunter ist die Karte eine
    Bestandsanzeige, keine Aussage.

    Zur Einordnung, was bereits GEMESSEN ist (05.08., zwei Regime, dieselbe
    Faktenquelle): die Richtungswahl des Modells ist eine Regime-Wette, keine
    Kante - im steigenden Markt LONG minus SHORT +1,744 R, im fallenden
    -0,133 R mit einem Intervall, das null einschliesst. Diese Karte prueft,
    ob sich das im Betrieb bestaetigt."""
    _ = watchlist  # Signatur wie die uebrigen compute_*-Funktionen
    placeholders = ", ".join("?" for _ in _RESOLVED_OUTCOMES)
    rows = conn.execute(
        f"SELECT richtung, action, outcome_status AS status, "
        f"outcome_realisiertes_crv AS crv FROM hebel_signals "
        f"WHERE date(created_at) >= ? AND richtung IN ('LONG','SHORT')",
        (ab_datum,),
    ).fetchall()
    aufgeloest = conn.execute(
        f"SELECT richtung, outcome_status AS status, "
        f"outcome_realisiertes_crv AS crv FROM hebel_signals "
        f"WHERE date(created_at) >= ? AND richtung IN ('LONG','SHORT') "
        f"AND outcome_status IN ({placeholders})",
        (ab_datum, *_RESOLVED_OUTCOMES),
    ).fetchall()

    ergebnis = {"ab_datum": ab_datum, "richtungen": {}}
    for richtung in ("LONG", "SHORT"):
        alle = [r for r in rows if r["richtung"] == richtung]
        auf = [r for r in aufgeloest if r["richtung"] == richtung]
        tp = sum(1 for r in auf if r["status"] == OUTCOME_TAKE_PROFIT)
        crvs = [r["crv"] for r in auf if r["crv"] is not None]
        ergebnis["richtungen"][richtung] = {
            "signale": len(alle),
            "eroeffnen": sum(1 for r in alle if str(r["action"] or "") == "ERÖFFNEN"),
            "aufgeloest": len(auf),
            "take_profit": tp,
            "trefferquote_pct": round(tp / len(auf) * 100, 1) if auf else None,
            "erwartungswert_r": round(sum(crvs) / len(crvs), 3) if crvs else None,
            "belastbar": len(auf) >= 30,
        }
    gesamt = sum(v["signale"] for v in ergebnis["richtungen"].values())
    ergebnis["short_anteil_pct"] = (
        round(ergebnis["richtungen"]["SHORT"]["signale"] / gesamt * 100, 1)
        if gesamt else None)
    ergebnis["hinweis"] = (
        "Seit dem Nur-Long-Umbau am 05.08. laufen beide Richtungen normal durch. "
        "SHORT wird nicht gemailt und im Hebel-Tab standardmaessig ausgeblendet - "
        "gemessen wird es trotzdem. `belastbar` erst ab 30 aufgeloesten Faellen "
        "je Richtung.")
    return ergebnis


def kosten_kontext_fuer_prompt(hebel: float | None = None) -> dict:
    """Kostentabelle als FAKT fuer den Hebel-Prompt (2026-08-05).

    DIE LUECKE. Zielgroessen-Doku, Abschnitt "Was im System dazu fehlt":
    "Das LLM kennt die Kostenstruktur nicht und kann sie beim Setzen von Stop
    und Ziel nicht beruecksichtigen - der Faktor existiert jetzt
    deterministisch, die Weitergabe in den Prompt fehlt." Genau die schliesst
    diese Funktion.

    WARUM EINE TABELLE UND NICHT DIE FORMEL. Die Kostenlast in R lautet
    (L-1)/L x (Schliessung + Tagesgebuehr x Tage) / Stop-Abstand. Das Modell
    muesste sie fuer seinen eigenen Zonenvorschlag selbst ausrechnen - ein
    fehleranfaelliger Rechenschritt. Denselben Fehler hat das Projekt bei ATR
    schon einmal gemacht und am 28.07. korrigiert, indem `atr.relativ_prozent`
    deterministisch mitgeliefert wurde statt nur `atr.wert`. Die Tabelle ist
    die gleiche Loesung: das Modell liest ab, statt zu rechnen.

    WARUM KONTEXT UND KEIN GATE (Fakten-Entscheidungsmappe, 3+1-Raster):
      Frage 1 - immer dieselbe richtige Reaktion? NEIN. Eine harte Schwelle
        braeuchte die erwartete Trefferquote je Signal (kostenbereinigter
        Breakeven q > (1+Kosten)/(1+CRV)), und die ist je Signal unbekannt.
        Der Nutzer hat harte Vetos zudem wiederholt abgelehnt ("keine Signale
        unnoetig wegschmeissen").
      Frage 2 - kontextabhaengiges Abwaegen? JA. Das Modell waegt den
        Stop-Abstand gegen Struktur ab (Support, Fibonacci, ATR); die Kosten
        sind ein weiterer Eingang in dieselbe Abwaegung, keine Vorgabe.
      Frage 3 - bekommt es heute eine Einordnung? NEIN, gar nichts.
      Frage 4 - passt es zum Zeithorizont? JA, und darum traegt die Tabelle
        die Haltedauer als eigene Achse: bei Hebel loest ein Signal im Median
        nach 2,6 Tagen auf, gehandelt wird nach 0,3 Tagen.

    ZWEI FOLGERUNGEN, die aus der Formel fallen und die das Modell kennen
    sollte, weil sie seine Zonenwahl betreffen:
      - ENGE STOPS SIND DOPPELT TEUER: der Stop-Abstand steht im Nenner. Ein
        enger Stop wird nicht nur haeufiger getroffen, er traegt je R auch
        mehr Kosten.
      - HOEHERER HEBEL KOSTET MEHR JE R: (L-1)/L waechst von 0,50 (2x) ueber
        0,67 (3x) auf 0,90 (10x), waehrend das Risikobudget gleich bleibt.

    KEINE ERFUNDENEN ZAHLEN: die Saetze stammen aus der Bitpanda-
    Kostentransparenz (siehe _KOSTEN_HEBEL_*-Konstanten). Fuer Spot ist
    `belegt` False - dort steckt die Gebuehr groesstenteils im Spread und ist
    ohne Marktmitte nicht messbar."""
    L = float(hebel) if hebel and hebel > 1 else _KOSTEN_HEBEL_FALLBACK
    stop_stufen = (0.02, 0.03, 0.05, 0.08, 0.12)
    tage_stufen = (1, 3, 5)
    tabelle = []
    for stop_rel in stop_stufen:
        zeile = {"stop_abstand_prozent": round(stop_rel * 100, 1)}
        for tage in tage_stufen:
            wert = kosten_in_r(stop_rel, "hebel", float(tage), hebel=L).get("kosten_r")
            zeile[f"kosten_r_nach_{tage}_tagen"] = (
                round(wert, 3) if wert is not None else None)
        tabelle.append(zeile)
    return {
        "gilt_fuer_hebel": round(L, 1),
        "kosten_in_r_tabelle": tabelle,
        "lesehilfe": (
            "Kosten in R = Anteil deines Risikobudgets, den Schliessungsgebuehr und "
            "Finanzierung auffressen, BEVOR der Trade etwas verdient. 0,40 bedeutet: "
            "40 % des Risikos gehen an Gebuehren."
        ),
        "zwei_folgerungen": [
            "Enge Stops sind doppelt teuer: sie werden haeufiger getroffen UND "
            "tragen je R eine hoehere Kostenlast (der Stop-Abstand steht im Nenner).",
            "Hoeherer Hebel kostet mehr je R, nicht gleich viel - das Risikobudget "
            "bleibt gleich, der Kreditanteil waechst.",
        ],
        "typische_haltedauer_tage": {
            "median_bis_zur_aufloesung": 2.6,
            "hinweis": "gemessen an aufgeloesten Hebel-Signalen; der Rahmen sind 0 bis max. 5 Tage",
        },
        "belegt": True,
        "quelle": "Bitpanda-Kostentransparenz, Schliessung 0,3 % + gestaffelte Tagesgebuehr",
    }


def ausstiegsregel_kontext_fuer_prompt(config: dict | None = None) -> dict | None:
    """Die aktive Ausstiegsregel als FAKT (2026-08-05).

    DIE LUECKE: seit heute wird der Stop automatisch nachgezogen, sobald eine
    Position einmal bei `ausloese_r` im Plus stand. Das Modell setzt aber
    Take-Profit-Zonen, OHNE davon zu wissen - es plant gegen eine Regel, die es
    nicht kennt.

    WARUM DAS DIE ZONENWAHL BETRIFFT, und zwar in beide Richtungen: wer weiss,
    dass ab +1R abgesichert wird, kann ein WEITER entferntes Ziel wagen (der
    Rueckfall ist nach oben hin begrenzt) - oder ein naeheres waehlen, weil der
    Trailing-Stop ohnehin frueher greift. Welche der beiden Ueberlegungen
    richtig ist, haengt vom Einzelfall ab. Genau deshalb Kontext und keine
    Vorgabe (Fakten-Entscheidungsmappe, Frage 2).

    3+1-RASTER:
      Frage 1 (immer dieselbe Reaktion -> Gate?): NEIN. Die Regel selbst IST
        schon deterministisch; hier geht es darum, ob das Modell seine Zonen
        anders legt, wenn es sie kennt - das ist eine Abwaegung.
      Frage 2 (kontextabhaengig?): JA, siehe oben.
      Frage 3 (bekommt es heute etwas?): NEIN.
      Frage 4 (passt es zum Zeithorizont?): JA - der Trailing greift innerhalb
        derselben 0-bis-5-Tage-Spanne, in der die Zonen liegen.

    Gibt None zurueck, wenn die Regel abgeschaltet ist (ausloese_r <= 0) - dann
    darf sie auch nicht als Fakt behauptet werden."""
    from agent.krypto.ausstiegsregel import parameter_aus_config

    ausloese, abstand, aktiv = parameter_aus_config(config or {})
    if not aktiv:
        return None
    return {
        "aktiv": True,
        "ausloese_r": ausloese,
        "abstand_r": abstand,
        "so_funktioniert_es": (
            f"Sobald die Position einmal {ausloese:.1f} R im Plus stand, wird der "
            f"Stop auf 'hoechster Buchgewinn minus {abstand:.1f} R' nachgezogen und "
            f"NIE wieder zurueckgenommen. Bei LONG zaehlt das bisherige Hoch, bei "
            f"SHORT das bisherige Tief."
        ),
        "was_das_fuer_deine_zonen_heisst": (
            "Der Rueckfall aus einem Gewinn ist dadurch nach unten begrenzt, sobald "
            f"{ausloese:.1f} R erreicht war. Ob daraus ein weiter entferntes Ziel "
            "folgt (mehr Raum, begrenztes Rueckfallrisiko) oder ein naeheres (der "
            "Trailing greift ohnehin frueher), entscheidest du am Einzelfall."
        ),
        "kein_breakeven_lock": (
            "Ausdruecklich KEIN Breakeven-Lock - der wurde am 01.08. gemessen und "
            "verworfen, weil er 63 % der Gewinner kostet: der Kurs laeuft nach dem "
            f"ersten Antippen von {ausloese:.1f} R regelmaessig noch einmal unter "
            "den Einstand, bevor er das Ziel nimmt."
        ),
        "belegt": True,
        "quelle": "gemessen an 495 aufgeloesten Signalen, EW -0,176 -> -0,084 R",
    }


def systemguete_kontext_fuer_prompt(conn, watchlist: list | None = None,
                                    tier: str = "hebel") -> dict | None:
    """Die eigene, gemessene Systemguete als FAKT (2026-08-05).

    DIE LUECKE: Erwartungswert, SQN und Profitfaktor werden berechnet,
    exportiert und auf der Remote-Seite angezeigt - erreichen das Modell aber
    nie. Es beurteilt jedes Signal, ohne zu wissen, wie die bisherigen
    ausgegangen sind.

    ABSICHTLICH OHNE HANDLUNGSANWEISUNG. Die Zahl ist derzeit unerfreulich
    (Erwartungswert negativ, SQN "kaum handelbar"). Die naheliegende
    Formulierung waere "sei deshalb vorsichtiger" - und genau die waere ein
    Fehler: derselbe Mechanismus liess beim Ausfuehrbarkeits-Hinweis die
    EROEFFNEN-Quote von 93 % auf 3 % einbrechen. Ein Modell, das aus einer
    schlechten Bilanz schliesst, gar nichts mehr vorzuschlagen, loest das
    Problem nicht, es versteckt es.

    Deshalb: die Zahl mit ihrer Bedeutung, die Schlussfolgerung offen - genau
    die Linie der Fakten-Entscheidungsmappe ("Kontext liefern, Urteil
    offenlassen").

    RISIKO, das dazugehoert: sollte die Messung zeigen, dass dieser Fakt die
    EROEFFNEN-Quote senkt, gehoert er wieder entfernt. Die Quote ist deshalb
    Pflicht-Messgroesse jedes Tests dieses Fakts, nicht nur die Zonenqualitaet.

    Gibt None zurueck, wenn keine belastbare Zahl vorliegt - eine Systemguete
    aus fuenf Signalen waere irrefuehrender als gar keine."""
    try:
        guete = compute_systemguete(conn, watchlist)
    except Exception:
        return None
    real = ((guete or {}).get(tier) or {}).get("real") or {}
    n = real.get("anzahl_bewertet")
    # AUSGANGSWERT STATT WEGLASSEN (2026-08-09, Nutzer-Vorgabe: *"es soll einen
    # Ausgangswert geben und dann kalibrieren"*).
    #
    # Vorher: `n < 30 -> None`. Damit bekam die Spot-Familie mit 23
    # ausgewerteten Trades GAR NICHTS - und bei 30 auf einen Schlag eine Zahl
    # in voller Autoritaet. Eine harte Schwelle auf einer glatten Groesse, also
    # dieselbe Klippe, die beim Regime schon als Konstruktionsfehler erkannt
    # wurde ("ein glatter Verlauf verlangt glatte Behandlung").
    #
    # DIE URSPRUENGLICHE BEGRUENDUNG WAR RICHTIG - damals. Der alte Docstring
    # sagte: "eine Systemguete aus fuenf Signalen waere irrefuehrender als gar
    # keine." Das galt, SOLANGE ES KEINE SCHRUMPFUNG GAB. Jetzt begrenzt sich
    # eine duenne Zahl selbst: bei n=5 liegt das Gewicht bei 0,09, der
    # gewichtete Wert also praktisch auf der Basislinie, und `gewicht` steht
    # ausdruecklich im Fakt.
    #
    # Die alte Schwelle bleibt als `belastbar`-Kennzeichen erhalten - sie ist
    # weiter die Grenze, ab der man die Zahl OHNE Gewichtung lesen darf.
    # Vor dem Waechter definiert, weil auch der n=0-Zweig ihn braucht.
    def _z(name, stellen=3):
        wert = real.get(name)
        return round(wert, stellen) if isinstance(wert, (int, float)) else None

    # `None` heisst hier dasselbe wie 0: die Assetklasse taucht in der
    # Auswertung gar nicht auf, weil nie ein Signal bewertet wurde. Vorher
    # fiel sie damit durch `isinstance(n, int)` und bekam GAR KEINEN Fakt -
    # Aktien und Themen-ETF blieben so ohne Ausgangswert, obwohl genau fuer
    # sie einer gebaut wurde.
    if n is None:
        n = 0
    if not isinstance(n, int) or n < 0:
        return None
    if n == 0:
        # AUSGANGSWERT STATT NICHTS, wie bei der Trefferquote. Ohne eigene
        # Trades gibt es keinen Messwert - aber die neutrale Annahme laesst
        # sich benennen, und sie ist lesbarer als ein fehlender Block.
        return {
            "anzahl_ausgewerteter_trades": 0,
            "erwartungswert_r": None,
            "sqn": None, "sqn_einordnung": None, "profit_factor": None,
            "basislinie_erwartungswert_r": _z("basislinie_erwartungswert_r"),
            "signalbeitrag_r": None,
            "basislinie_anzahl": real.get("basislinie_anzahl"),
            "erwartungswert_anker": (
                "basislinie" if _z("basislinie_erwartungswert_r") is not None
                else "null_kein_vorteil"),
            "erwartungswert_gewichtet": (
                _z("basislinie_erwartungswert_r")
                if _z("basislinie_erwartungswert_r") is not None else 0.0),
            "signalbeitrag_gewichtet": 0.0,
            "gewicht": 0.0,
            "einordnung": "noch keine eigene Messung - Ausgangswert",
            "ci_enthaelt_null": None,
            "erwartungswert_ci": None,
            "aufloesungsquote": None,
            "belastbar": False,
            "vorlaeufig_hinweis": (
                "NOCH KEINE eigenen ausgewerteten Trades in dieser "
                "Assetklasse. Die genannten Werte sind der neutrale "
                "Ausgangspunkt, KEINE Messung - Gewicht 0. Sie sagen ueber "
                "die bisherige Leistung nichts aus und weichen jedem "
                "ausgewerteten Trade."),
            "lesehilfe": None,
            "belegt": False,
        }
    belastbar = n >= _MIN_N_SYSTEMGUETE_BELASTBAR
    ew = real.get("expectancy_r")
    # --- BASISLINIE UND UNSICHERHEIT DURCHREICHEN (2026-08-09) ----------
    #
    # DER FUND: `compute_systemguete()` rechnet beides laengst - und diese
    # Funktion warf es weg. Das Modell las "Erwartungswert -0,149 R" als
    # blanke Tatsache, ohne zu erfahren, dass
    #   (a) ein MECHANISCHER Einstieg im selben Zeitraum -0,094 R verloren
    #       haette, unser eigener Beitrag also -0,055 R betraegt, und
    #   (b) das Vertrauensintervall der Schaetzung die NULL enthaelt
    #       ([-0,407; +0,147]) - die Zahl ist statistisch nicht von "kein
    #       Effekt" zu unterscheiden.
    #
    # Damit gilt hier derselbe Grundsatz wie bei den CRV-Baendern und der
    # Trefferquote: NUR DER ABSTAND ZUR BASISLINIE IST DIE AUSSAGE. Eine
    # absolute Zahl ohne Basislinie laedt dazu ein, den Markt dem System
    # anzulasten.
    #
    # GEMESSEN am 09.08.: der Fakt in seiner alten Form druckte die
    # LONG-Konfidenz um 4,9 bis 30,0 Punkte und die SHORT-Konfidenz um NULL -
    # eine gerichtete Wirkung, fuer die die Zahl selbst keine Grundlage gibt.
    # Nichts davon wird hier beschoenigt: die rohe Zahl bleibt an erster
    # Stelle stehen. Es kommt nur dazu, was zu ihrer Einordnung gehoert.
    return {
        "anzahl_ausgewerteter_trades": n,
        "erwartungswert_r": round(ew, 3) if isinstance(ew, (int, float)) else None,
        "sqn": round(real["sqn"], 2) if isinstance(real.get("sqn"), (int, float)) else None,
        "sqn_einordnung": real.get("sqn_einordnung"),
        "profit_factor": (round(real["profit_factor"], 2)
                          if isinstance(real.get("profit_factor"), (int, float)) else None),
        # Die Basislinie: was ein MECHANISCHER Einstieg im selben Zeitraum
        # gebracht haette, und der Abstand unserer Signale dazu.
        "basislinie_erwartungswert_r": _z("basislinie_erwartungswert_r"),
        "signalbeitrag_r": _z("signalbeitrag_r"),
        "basislinie_anzahl": real.get("basislinie_anzahl"),
        # --- SCHRUMPFUNG MIT DEM RICHTIGEN ANKER (2026-08-09) -----------
        #
        # Nutzer-Einwand, und er trifft: *"Null ist schwachsinn das kann nicht
        # funktionieren."* Genau so ist es. Ein Erwartungswert von 0 R hiesse
        # "ein System, das weder gewinnt noch verliert" - das gibt es in
        # diesem Markt nicht. Ein MECHANISCHER Einstieg verliert im selben
        # Zeitraum -0,094 R. Gegen Null zu schrumpfen wuerde ein schlechtes
        # System besser aussehen lassen, als der Markt ueberhaupt zulaesst -
        # das waere Beschoenigung.
        #
        # Die beiden Anker sind deshalb verschieden, und beide folgen
        # derselben Frage: "was nehme ich an, wenn ich NICHTS weiss?"
        #
        #   Erwartungswert -> die BASISLINIE. Ohne Information nimmt man an,
        #                     man liefert wie ein mechanischer Einstieg.
        #   Signalbeitrag  -> NULL. Ohne Information nimmt man an, man fuegt
        #                     dem Markt nichts hinzu. Hier ist die Null der
        #                     richtige Anker, weil der Beitrag eine DIFFERENZ
        #                     ist und nicht ein Niveau.
        # FLACH, wie bei der Trefferquote: der gewichtete Wert und sein
        # Gewicht stehen NEBEN dem rohen und der Basislinie, nicht eine Ebene
        # tiefer in einem Dict, das beide nochmal doppelt.
        # ANKER MIT RUECKFALL (2026-08-09). Erste Wahl ist die Basislinie -
        # was ein mechanischer Einstieg im selben Zeitraum brachte. Fehlt sie
        # (unter 200 Ziehungen: Aktien, Themen-ETF, Hedge), faellt der Anker
        # auf NULL zurueck, also "kein Vorteil angenommen".
        #
        # Das ist NICHT der Fall, der am 09.08. zu Recht verworfen wurde. Dort
        # ging es darum, einen GEMESSENEN Wert gegen Null zu schrumpfen und
        # ihn damit besser aussehen zu lassen, als der Markt zulaesst. Hier
        # gibt es keine Basislinie, und "kein Vorteil" ist die neutrale
        # Annahme - kein Schoenrechnen, sondern das Eingestaendnis, den
        # Marktpreis fuer diese Assetklasse nicht zu kennen.
        #
        # VORBEHALT, der dazugehoert: in einem Markt, in dem mechanische
        # Einstiege verlieren, ist 0 R leicht optimistisch. Ohne gemessene
        # Basislinie waere jede andere Zahl aber erfunden.
        "erwartungswert_anker": ("basislinie" if _z("basislinie_erwartungswert_r")
                                 is not None else "null_kein_vorteil"),
        "erwartungswert_gewichtet": (
            _ew["gewichtet"] if (_ew := schrumpfe_zu_neutral(
                _z("expectancy_r"), n,
                _z("basislinie_erwartungswert_r")
                if _z("basislinie_erwartungswert_r") is not None else 0.0))
            else None),
        "signalbeitrag_gewichtet": (
            _sb["gewichtet"] if (_sb := schrumpfe_zu_neutral(
                _z("signalbeitrag_r"), n, 0.0)) else None),
        "gewicht": _ew["gewicht"] if _ew else (_sb["gewicht"] if _sb else None),
        # Kategoriale Zwillingsform. Toleranz 0,02 R - darunter ist der
        # Unterschied zur Basislinie kleiner als die Kostenspanne eines
        # einzelnen Trades und damit keine Aussage.
        "einordnung": einordnung_gegen(
            _z("expectancy_r"), _z("basislinie_erwartungswert_r"), 0.02),
        # DIE eigentliche Aussage des Intervalls, als Ja/Nein statt als zwei
        # Zahlen, die das Modell mit der Null vergleichen muesste.
        "ci_enthaelt_null": (
            None if _z("expectancy_ci_unten") is None
            else bool(_z("expectancy_ci_unten") <= 0 <= _z("expectancy_ci_oben"))),
        # Die Unsicherheit der eigenen Schaetzung.
        "erwartungswert_ci": (
            [_z("expectancy_ci_unten"), _z("expectancy_ci_oben")]
            if _z("expectancy_ci_unten") is not None else None),
        "aufloesungsquote": _z("aufloesungsquote", 2),
        "belastbar": belastbar,
        "vorlaeufig_hinweis": (
            None if belastbar else
            f"VORLAEUFIG: nur {n} ausgewertete Trades (belastbar ab "
            f"{_MIN_N_SYSTEMGUETE_BELASTBAR}). Lies die gewichteten Werte, "
            f"nicht die rohen - das Gewicht sagt, wie viel der Messwert "
            f"ueberhaupt zaehlt. Bei kleinem n liegt er nahe an der "
            f"Basislinie, und genau das ist die ehrliche Aussage: noch "
            f"nicht unterscheidbar."),
        "lesehilfe": (
            "Erwartungswert in R = durchschnittliches Ergebnis je Signal, gemessen "
            "an tatsaechlich eroeffneten Trades dieser Kategorie. Ein negativer Wert "
            "heisst, dass die bisherigen Signale im Schnitt Geld gekostet haben. "
            "WICHTIG zur Einordnung: `basislinie_erwartungswert_r` ist das Ergebnis "
            "eines MECHANISCHEN Einstiegs im selben Zeitraum - liegt sie ebenfalls "
            "im Minus, war der Markt teuer, nicht nur die Auswahl. Der eigene "
            "Beitrag ist `signalbeitrag_r`, also der Abstand dazu. Und "
            "`erwartungswert_ci` ist der Vertrauensbereich der Schaetzung: "
            "enthaelt er die Null, ist der Wert statistisch nicht von 'kein "
            "Effekt' zu unterscheiden."
        ),
        "wie_du_das_nutzt": (
            "Das ist Kalibrierungs-Kontext, KEINE Handlungsanweisung und kein Grund, "
            "grundsaetzlich zurueckhaltender zu werden. Es sagt dir, wie streng die "
            "Latte fuer ein lohnendes Setup liegt - nicht, dass du keines mehr "
            "vorschlagen sollst."
        ),
        "belegt": True,
    }


# Tages-Cache fuer die CRV-Baender. Schluessel (tier, horizont) -> (datum, wert).
# NOETIG, nicht Kosmetik: crv_baender_kontext_fuer_prompt() simuliert jedes
# Signal mit Zonen gegen die Kursreihen, und der Fakt wird JE SIGNAL gebaut.
# Die zugrunde liegenden outcome_*-Spalten schreibt nur der taegliche
# Backward-Tracking-Lauf - zwischen zwei Laeufen kann sich das Ergebnis nicht
# aendern. Genau die Lehre vom 03.08.: "wie teuer ist ein Aufruf" ist ohne
# "wie oft passiert er" wertlos (damals 288 statt 24 Berechnungen taeglich).
_CRV_BAENDER_PROMPT_CACHE: dict[tuple, tuple] = {}


def crv_baender_kontext_fuer_prompt(conn, tier: str = "hebel", horizont: int = 7,
                                    min_n: int = 20, watchlist: list | None = None,
                                    heute: str | None = None) -> dict | None:
    """Gemessene CRV-Erfolgsbaender als FAKT - fuer ALLE sechs Pipelines (2026-08-06).

    DIE LUECKE (Fakten-Entscheidungsmappe Abschnitt 8, Kandidat A1). Der
    Hebel-Analyst SETZT das CRV und kannte dazu nur die Mindestgrenze aus
    Regel 5 - keine gemessene Einordnung. Der Krypto-Spot-Analyst bekam seit
    dem 03.08. Baender als Regel 36, obwohl seine Datenbasis mit 19
    ausgewerteten Trades gegen 124 weit duenner ist; Aktien, Rohstoffe und
    Themen-ETF hatten gar nichts.

    `tier` ist einer von: "hebel", "krypto", "aktien", "rohstoffe", "etf"
    (Themen-ETFs; seit 07.08. OHNE die Hedge-Instrumente, die einen eigenen
    Tier "hedge" haben - fuer eine Absicherung sind CRV-Baender ohnehin die
    falsche Groesse, siehe compute_hedge_wirksamkeit()) (oder "spot" fuer den Sammel-Topf). Fuer alles ausser "hebel"
    wird ueber `spot_symbole_je_tier()` auf die Symbole DIESER Assetklasse
    gefiltert - ohne den Filter waere jeder Befund ein Mischwert, in dem
    hinterher niemand sagen kann, ob er krypto-spezifisch war (Fund 29.07.).
    Ohne Watchlist gibt es fuer die Spot-Familie deshalb bewusst None statt
    einer stillen Mischung.

    NUR DER ABSTAND ZUR BASISLINIE GEHT IN DEN FAKT, NIE DIE ABSOLUTE QUOTE.
    Das ist keine Feinheit, sondern der Kern: die absolute Zielquote faellt mit
    steigendem CRV zwangslaeufig, weil das Ziel CRV-mal weiter liegt als der
    Stop und der Horizont endlich ist. Bei CRV 4,0 und H=7 erreicht selbst ein
    Zufallseinstieg nur 3,1 %. Wer die absoluten Quoten nebeneinanderstellt,
    liest daraus "hohes CRV ist schlecht" - genau der Trunkierungs-Artefakt,
    der am 03.08. als Befund gemeldet und noch am selben Tag widerrufen wurde
    (7e1928a -> a9f1e32). Der Abstand zur mechanischen Basislinie desselben
    Bandes ist gegen diesen Effekt immun, weil er beide Seiten gleich
    behandelt.

    WARUM DAS MASS "ZIEL ERREICHT" UND NICHT "MFE >= 1R" (gepruefte
    Entscheidung, 2026-08-06, `pruefe_sprung_bei_crv4.py`). Die alte
    Regel-36-Konstante nutzte "MFE >= 1R". Auf dieses Mass wirkt die
    Trunkierung NICHT - die Schwelle 1R ist fest, unabhaengig vom CRV. Dafuer
    wirkt dort etwas Schlimmeres: CRV = Zielabstand / Stopabstand, ein hohes
    CRV entsteht also auch durch einen ENGEN Stop. Bei engem Stop ist 1R eine
    winzige Kursbewegung, MFE >= 1R wird mechanisch leicht. An 871 Signalen
    gemessen faellt der Median-Stop ueber die CRV-Baender monoton von 6,25 %
    auf 2,56 %, und der Stop-Abstand ALLEIN trennt schaerfer als das CRV
    (54,0 / 25,1 / 15,8 % ueber die Stop-Terzile, KIs getrennt). Kontrolliert
    man ihn, schrumpft der CRV-Effekt von +36,8 auf +13,4 pp und alle
    Intervalle ueberlappen.

    UND DANN KIPPT ES. Bei Stops unter 2 % erreichen 55,3 % der Signale
    MFE >= 1R - bei einem Erwartungswert von -1,043 R (n=47). Die Kennzahl
    meldet Erfolg, waehrend praktisch jeder Trade voll ausgestoppt wird: der
    Kurs tippt 1R an, weil 1R dort fast nichts ist, und nimmt danach den Stop
    mit. Ein Mass, das genau das belohnt, was das Ergebnis zerstoert, taugt
    nicht als Grundlage einer Empfehlung. Deshalb misst dieser Fakt "Ziel
    erreicht" gegen die Basislinie - beide Seiten tragen denselben Stop und
    denselben Horizont, der Vergleich ist damit gegen beide Effekte immun.

    BAENDER OHNE `belastbar` WERDEN MITGELIEFERT, ABER GEKENNZEICHNET. Sie
    wegzulassen waere Rosinenpickerei - das Modell saehe dann nur das eine
    gute Band und hielte den Rest fuer ungemessen statt fuer unsicher.

    Gibt None zurueck, wenn KEIN Band belastbar ist: dann traegt die Tabelle
    keine Aussage, und eine Liste unsicherer Zahlen waere schlechter als gar
    nichts (dieselbe Linie wie die n>=30-Schwelle bei der Systemguete)."""
    schluessel = (tier, horizont)
    tag = heute or datetime.now(timezone.utc).date().isoformat()
    gecacht = _CRV_BAENDER_PROMPT_CACHE.get(schluessel)
    if gecacht and gecacht[0] == tag:
        return gecacht[1]

    # Tabellen-Tier vs. Auswertungs-Tier: `hebel_signals` und `signals` sind
    # zwei Tabellen, aber innerhalb von `signals` liegen alle vier
    # Spot-Assetklassen gemeinsam - die Trennung passiert ueber die Symbole.
    tabellen_tier = "hebel" if tier == "hebel" else "spot"
    erlaubte_symbole = None
    if tier not in ("hebel", "spot"):
        erlaubte_symbole = spot_symbole_je_tier(watchlist).get(tier)
        if not erlaubte_symbole:
            # Kein stiller Rueckfall auf den Sammel-Topf: lieber kein Fakt als
            # ein Mischwert ueber vier Assetklassen.
            _CRV_BAENDER_PROMPT_CACHE[schluessel] = (tag, None)
            return None

    try:
        roh = compute_crv_breakeven_baender(conn, tabellen_tier, horizont=horizont,
                                            mit_halten=False,
                                            erlaubte_symbole=erlaubte_symbole)
    except Exception:
        return None

    baender = []
    for b in ((roh or {}).get("baender") or []):
        if not isinstance(b.get("anzahl"), int) or b["anzahl"] < min_n:
            continue
        abstand = b.get("abstand_zur_basislinie_pp")
        if not isinstance(abstand, (int, float)):
            continue
        baender.append({
            "crv_von": b.get("crv_von"),
            "crv_bis": b.get("crv_bis"),
            "anzahl_signale": b["anzahl"],
            "vorsprung_vor_zufallseinstieg_pp": round(float(abstand), 1),
            "erwartungswert_r": (round(b["erwartungswert_r"], 3)
                                 if isinstance(b.get("erwartungswert_r"), (int, float))
                                 else None),
            "belastbar": bool(b.get("belastbar")),
        })

    ergebnis = None
    if any(b["belastbar"] for b in baender):
        ergebnis = {
            "gilt_fuer": tier,
            "horizont_tage": horizont,
            "grundlage": (roh or {}).get("anzahl_signale"),
            "baender": baender,
            "lesehilfe": (
                "'vorsprung_vor_zufallseinstieg_pp' = um wie viele Prozentpunkte "
                "Signale dieses CRV-Bandes ihr Ziel oefter erreichen als ein "
                "mechanischer Zufallseinstieg mit demselben CRV und demselben "
                "Stop-Abstand. Nur dieser Vorsprung ist vergleichbar."
            ),
            "warum_keine_absoluten_quoten": (
                "Die absolute Zielquote faellt mit steigendem CRV zwangslaeufig - "
                "das Ziel liegt CRV-mal weiter als der Stop, der Beobachtungs-"
                "zeitraum ist aber endlich. Bei CRV 4,0 kommt auch ein "
                "Zufallseinstieg fast nie an. Absolute Quoten wuerden dich "
                "deshalb systematisch gegen hohe CRV-Werte lenken, ohne dass "
                "dahinter ein Qualitaetsunterschied steht."
            ),
            "wie_du_das_nutzt": (
                "Einordnung beim SETZEN der Zonen, KEINE Vorgabe und kein "
                "Mindestwert - die Mindestgrenze steht unveraendert in Regel 5. "
                "Baender mit belastbar=false sind gemessen, aber zu unsicher fuer "
                "eine Schlussfolgerung; behandle sie als 'unbekannt', nicht als "
                "'schlecht'. Die Struktur des Charts hat Vorrang: ein CRV, das nur "
                "durch einen zu nahen Stop entsteht, ist kein besseres Signal."
            ),
            "belegt": True,
            "quelle": ((roh or {}).get("schaetzer")
                       or "kumulative Inzidenz (Aalen-Johansen), Competing Risks"),
        }

    _CRV_BAENDER_PROMPT_CACHE[schluessel] = (tag, ergebnis)
    return ergebnis
