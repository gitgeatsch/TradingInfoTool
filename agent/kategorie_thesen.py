"""Objektiver These-Abgleich fuer Kategorie-Schwerpunkte (2026-07-19, Release 2
der Kategorie-Taxonomie, Teil der ersten Umsetzungsrunde - siehe Basisinfos/
Kategorie_Basisinformationen_Release2.md Abschnitt 5, Punkt 2 fuer die volle
Begruendung). Prueft eine aktive These NICHT gegen ihre eigene Beliebtheit,
sondern gegen unabhaengige, bereits im Projekt vorhandene objektive Daten
(M2-/Liquiditaetsregime, CFTC-COT-Positionierung, Zinskurve, Dollar-Index-
Trend) - kann eine hypebasierte These deshalb sogar als "objektiv nicht
gestuetzt" kennzeichnen, statt prozyklisch zu verstaerken (siehe Bubble-Risiko-
Diskussion im Konzept-Dokument).

Transparenz-Prinzip (ausdruecklicher Nutzer-Wunsch): jede Einschaetzung MUSS
konkrete Rohwerte in der Begruendung nennen, nie nur ein Bewertungswort ohne
Beleg."""
from __future__ import annotations

from dataclasses import dataclass

import api.cftc_cot as cftc_cot
import api.macro as macro
import config
import database.db as db
from database.models import These

# Welche COT-Rohstoffe (api.cftc_cot.COT_MARKET_NAMES-Schluessel) fuer welche
# Hauptgruppe/Unterkategorie relevant sind - mehrere Rohstoffe werden addiert
# (Netto-Positionierung ueber alle relevanten Kontrakte).
_COT_ROHSTOFF_FUER_KATEGORIE: dict[str, list[str]] = {
    "industriemetalle": ["kupfer"],
    "energie": ["erdgas", "rohoel_wti"],
    "energie:erdgas": ["erdgas"],
    "energie:rohoel": ["rohoel_wti", "rohoel_brent"],
}


@dataclass
class TheseAbgleich:
    einschaetzung: str  # "gestuetzt"|"neutral"|"widerspricht"|"nicht_pruefbar"
    begruendung: str  # MUSS konkrete Rohwerte nennen (Transparenz-Prinzip)
    datenstand: str | None  # Datum/Zeitstempel der zugrunde liegenden Daten, falls bekannt


def _einschaetzung_aus_richtung(bullisches_signal: bool | None, richtung: str) -> str:
    """`richtung`: 'uebergewichten'|'meiden' (Absicherung-Sonderfall 'aktiv'/
    'inaktiv' wird von den Absicherung-spezifischen Aufrufern separat behandelt,
    nicht hier). `bullisches_signal=None` heisst neutral/uneindeutig."""
    if bullisches_signal is None:
        return "neutral"
    if richtung == "uebergewichten":
        return "gestuetzt" if bullisches_signal else "widerspricht"
    if richtung == "meiden":
        return "widerspricht" if bullisches_signal else "gestuetzt"
    return "neutral"


def _abgleich_m2_liquiditaet(conn, these: These) -> TheseAbgleich:
    import agent.krypto.regime as regime

    status = regime.get_last_known_regime_status(conn)
    liquiditaets_regime = status.get("liquiditaets_regime") if status else None
    if not status or liquiditaets_regime in (None, "unbekannt"):
        return TheseAbgleich(
            "nicht_pruefbar",
            "Noch kein Liquiditaetsregime-Stand vorhanden (wird beim naechsten "
            "Krypto-Signal-Lauf mitberechnet).",
            None,
        )
    begruendung = status.get("liquiditaets_regime_begruendung") or f"Liquiditaetsregime: {liquiditaets_regime}."
    if liquiditaets_regime == "expansiv":
        bullisch = True
    elif liquiditaets_regime == "restriktiv":
        bullisch = False
    else:  # gemischt/widerspruechlich
        bullisch = None
    return TheseAbgleich(
        _einschaetzung_aus_richtung(bullisch, these.richtung), begruendung, status.get("created_at"),
    )


def _abgleich_cot_positionierung(these: These) -> TheseAbgleich:
    key = f"{these.hauptgruppe}:{these.unterkategorie}" if these.unterkategorie else these.hauptgruppe
    rohstoffe = _COT_ROHSTOFF_FUER_KATEGORIE.get(key) or _COT_ROHSTOFF_FUER_KATEGORIE.get(these.hauptgruppe)
    if not rohstoffe:
        return TheseAbgleich("nicht_pruefbar", "Keine CFTC-COT-Marktzuordnung fuer diese Kategorie hinterlegt.", None)

    snapshots = []
    for rohstoff in rohstoffe:
        try:
            snap = cftc_cot.get_cot_snapshot(rohstoff)
        except Exception:  # noqa: BLE001 - P-8, ein fehlgeschlagener Rohstoff blockiert nicht die anderen
            snap = None
        if snap is not None:
            snapshots.append(snap)
    if not snapshots:
        return TheseAbgleich("nicht_pruefbar", "CFTC-COT-Abruf fuer diese Kategorie fehlgeschlagen.", None)

    netto_summe = sum(s.managed_money_netto for s in snapshots)
    begruendung = "; ".join(
        f"{s.rohstoff}: Managed-Money netto {'long' if s.managed_money_netto >= 0 else 'short'} "
        f"{abs(s.managed_money_netto):,} Kontrakte ({s.managed_money_long_anteil_oi_prozent}% Long-Anteil am "
        f"Open Interest, Bericht vom {s.report_datum})"
        for s in snapshots
    )
    bullisch = True if netto_summe > 0 else (False if netto_summe < 0 else None)
    return TheseAbgleich(_einschaetzung_aus_richtung(bullisch, these.richtung), begruendung, snapshots[0].report_datum)


def _abgleich_zinskurve(these: These) -> TheseAbgleich:
    zk = macro.get_zinskurve()
    if zk is None:
        return TheseAbgleich("nicht_pruefbar", "Zinskurven-Abruf fehlgeschlagen.", None)
    begruendung = (
        f"10-Jahres-Rendite {zk.rendite_10j_pct}% vs. kurzfristiger Zins {zk.rendite_kurzfristig_pct}% "
        f"= Spread {zk.spread_pp:+.2f} Prozentpunkte "
        f"({'nicht invertiert' if zk.spread_pp >= 0 else 'invertiert'})."
    )
    bullisch = True if zk.spread_pp > 0 else (False if zk.spread_pp < 0 else None)
    return TheseAbgleich(_einschaetzung_aus_richtung(bullisch, these.richtung), begruendung, None)


def _abgleich_dollar_index(these: These) -> TheseAbgleich:
    dxy = macro.get_dollar_index_trend()
    if dxy is None:
        return TheseAbgleich("nicht_pruefbar", "Dollar-Index-Abruf fehlgeschlagen.", None)
    begruendung = (
        f"Dollar-Index (DXY) aktuell {dxy.aktueller_wert}, Trend ueber die letzten "
        f"{len(dxy.monatswerte)} Monate: {dxy.trend} (von {dxy.monatswerte[0][1]} am {dxy.monatswerte[0][0]} "
        f"auf {dxy.monatswerte[-1][1]} am {dxy.monatswerte[-1][0]})."
    )
    # Schwacher/fallender Dollar begguenstigt Emerging Markets (bullisch fuer eine
    # Uebergewichten-These), steigender Dollar ist ein Gegenwind (siehe Live-Fund
    # vom 2026-07-19 im Konzept-Dokument).
    bullisch = True if dxy.trend == "fallend" else (False if dxy.trend == "steigend" else None)
    return TheseAbgleich(_einschaetzung_aus_richtung(bullisch, these.richtung), begruendung, dxy.monatswerte[-1][0])


def _abgleich_baerenmarkt_overlay(these: These) -> TheseAbgleich:
    """Absicherung/Hedge - bewusst NICHT implementiert in dieser Runde (P-10,
    ehrlich statt vorgetaeuscht): der bestehende Aktien-Baermarkt-Indikator
    (agent/krypto/pipeline.py, S&P500/Nasdaq-Drawdown-Schwellenwert-Vergleich)
    ist aktuell reine Inline-Logik innerhalb einer groesseren Funktion, keine
    eigenstaendig aufrufbare Funktion - das haette eine groessere, ungeplante
    Refaktorierung von pipeline.py erfordert. Kleiner, klar umrissener
    Nachruestpunkt fuer eine spaetere Runde."""
    return TheseAbgleich(
        "nicht_pruefbar",
        "Automatischer Abgleich fuer Absicherung ist noch nicht angebunden (der "
        "bestehende Aktien-Baermarkt-Indikator ist noch keine eigenstaendig "
        "aufrufbare Funktion) - vorgemerkt fuer eine spaetere Runde.",
        None,
    )


_ABGLEICH_FUNKTIONEN = {
    "m2_liquiditaet": _abgleich_m2_liquiditaet,
    "cot_positionierung": lambda conn, these: _abgleich_cot_positionierung(these),
    "zinskurve": lambda conn, these: _abgleich_zinskurve(these),
    "dollar_index": lambda conn, these: _abgleich_dollar_index(these),
    "baerenmarkt_overlay": lambda conn, these: _abgleich_baerenmarkt_overlay(these),
}


def compute_these_abgleich(conn, these: These) -> TheseAbgleich | None:
    """Haupteinstiegspunkt: liefert den objektiven Abgleich fuer eine These,
    oder `None` wenn fuer die Hauptgruppe/Unterkategorie kein etablierter
    Pruef-Mechanismus existiert (z.B. Technologie & KI, Sonstige - P-10,
    bleibt bewusst leer statt einen Schein-Check vorzutaeuschen)."""
    mechanismus_info = config.get_pruef_mechanismus(these.hauptgruppe, these.unterkategorie)
    if mechanismus_info is None:
        return None
    fn = _ABGLEICH_FUNKTIONEN.get(mechanismus_info["mechanismus"])
    if fn is None:
        return None
    return fn(conn, these)


def index_aktive_thesen(thesen: list[These]) -> dict[tuple[str, str | None], These]:
    """Baut einen In-Memory-Index aktiver Thesen (2026-07-20, Task #343 -
    Stufe-1-Hervorhebung in Watchlist/Screener) fuer wiederholte Lookups ueber
    viele Assets/Kandidaten hinweg - vermeidet einen einzelnen SQL-Query pro
    Zeile. Mit `lookup_these()` zusammen dieselbe Prioritaets-Logik wie
    `db.get_aktive_these_fuer_kategorie()` (Unterkategorie-spezifisch vor
    Hauptgruppen-weit), nur eben in-memory."""
    return {(t.hauptgruppe, t.unterkategorie): t for t in thesen}


def lookup_these(
    index: dict[tuple[str, str | None], These], hauptgruppe: str | None, unterkategorie: str | None,
) -> These | None:
    """Sucht im `index` (siehe `index_aktive_thesen()`) - ein Unterkategorie-
    spezifischer Treffer hat Vorrang vor einer Hauptgruppen-weiten These,
    identische Prioritaet wie `db.get_aktive_these_fuer_kategorie()`."""
    if not hauptgruppe:
        return None
    if unterkategorie:
        treffer = index.get((hauptgruppe, unterkategorie))
        if treffer is not None:
            return treffer
    return index.get((hauptgruppe, None))


def build_these_abgleich_fact(conn, asset) -> dict | None:
    """Gemeinsamer Fact-Baustein fuer alle 4 nicht-Krypto-Pipelines (Aktien/
    Rohstoffe/Hedge/Themen-ETF) - analog `agent.krypto.wiederholungs_erkennung.
    build_wiederholung_fact()` als zentrale, wiederverwendete Funktion statt
    4x Duplikation. Liefert `None`, wenn das Asset keine Hauptgruppe hat
    (Krypto - kategorien.yaml deckt bewusst kein Krypto ab, siehe deren
    Kopfkommentar - oder ein Nicht-Krypto-Asset ohne gesetzte Kategorie) ODER
    keine aktive These fuer seine Hauptgruppe/Unterkategorie existiert - in
    beiden Faellen taucht dann einfach kein these_abgleich-Fakt im Prompt auf
    (P-8, kein Fehler).

    Bewusst NOCH OHNE Haltedauer-Mismatch-Check (siehe Konzept-Dokument
    Abschnitt 5, Punkt 5): der Signal-eigene Haltedauer-Vorschlag
    (halte_kriterium_bucket) entsteht erst ALS ERGEBNIS des LLM-Aufrufs, der
    diesen Fakt hier als Input bekommt - ein Vorab-Abgleich ist deshalb
    strukturell nicht moeglich, das waere ein Post-Check nach der LLM-Antwort
    (analog risk_gate.py::post_check()), kein Pre-Fact. Kleiner, klar
    umrissener Nachruestpunkt fuer eine spaetere Runde."""
    hauptgruppe = getattr(asset, "hauptgruppe", None)
    if not hauptgruppe:
        return None
    these = db.get_aktive_these_fuer_kategorie(conn, hauptgruppe, getattr(asset, "unterkategorie", None))
    if these is None:
        return None
    abgleich = compute_these_abgleich(conn, these)
    kategorie_name = (
        config.get_kategorie_name(these.hauptgruppe, these.unterkategorie)
        or config.get_hauptgruppe_name(these.hauptgruppe)
    )
    return {
        "kategorie": kategorie_name,
        "richtung": these.richtung,
        "begruendung_nutzer": these.begruendung,
        "objektive_einschaetzung": abgleich.einschaetzung if abgleich else "nicht_pruefbar",
        "objektive_begruendung": (
            abgleich.begruendung if abgleich
            else "Kein automatischer Pruef-Mechanismus fuer diese Kategorie hinterlegt."
        ),
        "datenstand": abgleich.datenstand if abgleich else None,
    }
