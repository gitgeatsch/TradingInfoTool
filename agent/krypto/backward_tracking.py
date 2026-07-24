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

# Nur diese Aktionen haben eine Take-Profit/Stop-Loss-Semantik, die sich gegen
# Kurshistorie pruefen laesst - HALTEN/VERKAUFEN/TAUSCHEN nicht.
_TRACKABLE_ACTIONS = {"KAUFEN", "NACHKAUFEN"}

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


@dataclass
class BackwardTrackingResult:
    geprueft_count: int = 0
    resolved_take_profit: int = 0
    resolved_stop_loss: int = 0
    expired: int = 0
    superseded: int = 0
    still_open: int = 0
    warnings: list[str] = field(default_factory=list)


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


def check_signal_outcome(conn, signal, watchlist) -> tuple[str, dict]:
    """Prueft EIN Signal gegen die seit signal.created_at vorliegende Kurshistorie.
    Gibt (neuer_status, extra_felder) zurueck - schreibt selbst NICHTS in die DB
    (reiner Funktionskern, Testbarkeit ohne DB-Mocking der Schreibpfade). extra_felder
    ist ein dict mit optionalen Keys 'entschieden_am'/'realisiertes_crv'/'datenquelle',
    passend fuer db.update_signal_outcome(**extra_felder)."""
    if signal.action not in _TRACKABLE_ACTIONS:
        return OUTCOME_NICHT_ANWENDBAR, {}

    take_profit_threshold = _threshold(signal.take_profit_usd_von, signal.take_profit_usd)
    stop_loss_threshold = _threshold(signal.stop_loss_usd_von, signal.stop_loss_usd)
    if take_profit_threshold is None or stop_loss_threshold is None:
        return OUTCOME_NICHT_ANWENDBAR, {}

    asset = next((a for a in watchlist if a.symbol == signal.symbol), None)
    if asset is None:
        return OUTCOME_OFFEN, {}

    min_date = signal.created_at[:10]
    entry_mid = _entry_mid(signal)

    def resolve(exit_price: float, hit_take: bool) -> tuple[str, dict]:
        status = OUTCOME_TAKE_PROFIT if hit_take else OUTCOME_STOP_LOSS
        realized_crv = None
        if entry_mid is not None and entry_mid != stop_loss_threshold:
            realized_crv = (exit_price - entry_mid) / (entry_mid - stop_loss_threshold)
        return status, {
            "entschieden_am": day,
            "realisiertes_crv": realized_crv,
            "datenquelle": datenquelle,
        }

    ohlc_rows = db.get_ohlc_history(conn, signal.symbol, "USD", min_date=min_date)
    if len(ohlc_rows) >= 1:
        datenquelle = "real"
        for row in ohlc_rows:
            day = row.date
            hit_take = row.high >= take_profit_threshold
            hit_stop = row.low <= stop_loss_threshold
            if hit_stop:
                # Konservativ (Z-1: Kapitalerhalt vor Gewinn): trifft ein Tag beide
                # Zonen, gewinnt Stop-Loss - keine Annahme ueber die Intraday-
                # Reihenfolge ohne Tick-Daten.
                return resolve(row.low, hit_take=False)
            if hit_take:
                return resolve(row.high, hit_take=True)
    else:
        datenquelle = "proxy"
        price_rows = db.get_price_history(conn, asset.coingecko_id, min_date=min_date) if asset.coingecko_id else []
        for row in price_rows:
            if row.price_usd is None:
                continue
            day = row.date
            hit_take = row.price_usd >= take_profit_threshold
            hit_stop = row.price_usd <= stop_loss_threshold
            if hit_stop:
                return resolve(row.price_usd, hit_take=False)
            if hit_take:
                return resolve(row.price_usd, hit_take=True)

    # Kein Treffer gefunden - offen oder abgelaufen, je nach Alter.
    return OUTCOME_OFFEN, {}


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

        status, extra = check_signal_outcome(conn, signal, watchlist)

        if status == OUTCOME_NICHT_ANWENDBAR:
            db.update_signal_outcome(conn, signal.id, status)
            continue

        if status in (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS):
            db.update_signal_outcome(
                conn, signal.id, status,
                entschieden_am=extra.get("entschieden_am"),
                realisiertes_crv=extra.get("realisiertes_crv"),
                datenquelle=extra.get("datenquelle"),
            )
            if status == OUTCOME_TAKE_PROFIT:
                result.resolved_take_profit += 1
            else:
                result.resolved_stop_loss += 1
            continue

        # status == OUTCOME_OFFEN: erst Ueberholt-Check, dann Ablauf-Check.
        if _is_superseded(signal, latest_real, mindestbeob_bucket, mindestbeob_fallback, zonen_toleranz):
            db.update_signal_outcome(conn, signal.id, OUTCOME_UEBERHOLT)
            result.superseded += 1
        elif _is_expired(signal, bucket_tage, fallback_tage):
            db.update_signal_outcome(conn, signal.id, OUTCOME_ABGELAUFEN)
            result.expired += 1
        else:
            result.still_open += 1

    return result


_RESOLVED_OUTCOMES = (OUTCOME_TAKE_PROFIT, OUTCOME_STOP_LOSS, OUTCOME_LIQUIDATION)


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
    der Watchlist stehen, fallen unter "unbekannt" statt zu verschwinden."""
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
        f"SELECT symbol, groq_model AS llm_model, outcome_status, outcome_realisiertes_crv "
        f"FROM signals WHERE outcome_status IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in spot_rows:
        tier = assetklasse_by_symbol.get(row["symbol"], "unbekannt") if watchlist else "spot"
        eintrag = _stelle_sicher(tier, provider_from_label(row["llm_model"]))
        eintrag["anzahl_resolved"] += 1
        if row["outcome_status"] == OUTCOME_TAKE_PROFIT:
            eintrag["take_profit_count"] += 1
        elif row["outcome_status"] == OUTCOME_STOP_LOSS:
            eintrag["stop_loss_count"] += 1
        if row["outcome_realisiertes_crv"] is not None:
            eintrag["_crv_summe"] += row["outcome_realisiertes_crv"]
            eintrag["_crv_count"] += 1

    hebel_rows = conn.execute(
        f"SELECT llm_model, outcome_status, outcome_realisiertes_crv "
        f"FROM hebel_signals WHERE outcome_status IN ({placeholders})",
        _RESOLVED_OUTCOMES,
    ).fetchall()
    for row in hebel_rows:
        eintrag = _stelle_sicher("hebel", provider_from_label(row["llm_model"]))
        eintrag["anzahl_resolved"] += 1
        if row["outcome_status"] == OUTCOME_TAKE_PROFIT:
            eintrag["take_profit_count"] += 1
        elif row["outcome_status"] == OUTCOME_STOP_LOSS:
            eintrag["stop_loss_count"] += 1
        elif row["outcome_status"] == OUTCOME_LIQUIDATION:
            eintrag["liquidation_count"] += 1
        if row["outcome_realisiertes_crv"] is not None:
            eintrag["_crv_summe"] += row["outcome_realisiertes_crv"]
            eintrag["_crv_count"] += 1

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
