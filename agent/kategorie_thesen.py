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
    # 2026-07-24, #333 Quick Win: Gold/Silber waren in COT_MARKET_NAMES
    # (api/cftc_cot.py) bereits abrufbar, aber hier nie zugeordnet.
    "edelmetalle": ["gold", "silber"],
    "edelmetalle:gold": ["gold"],
    "edelmetalle:silber": ["silber"],
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


# Net-Liquidity-Nachbesserung (2026-07-24, #333 Punkt 18, siehe Kategorie_
# Basisinformationen_Release2.md Abschnitt 15) - Fed-Bilanzsumme (WALCL) minus
# Treasury General Account (WTREGEN) minus Reverse-Repo (RRPONTSYD), alle
# wöchentlich-oder-öfter statt M2s monatlichem Takt. Live gegen FRED
# verifiziert (2026-07-24): WALCL/WTREGEN in Mio. USD, RRPONTSYD in Mrd. USD
# (deshalb *1000 skaliert). Bewusst NICHT in agent/krypto/regime.py verdrahtet
# (das ist die geteilte, live-kritische Krypto-Regime-Pipeline) - eigener,
# unabhaengiger Live-Abruf nur fuer diesen These-Abgleich, damit hier nichts
# an der Krypto-Pipeline mitgeaendert wird.
NET_LIQUIDITY_TREND_THRESHOLD_PCT = 2.0
_FRED_SERIES_WALCL = "WALCL"
_FRED_SERIES_TGA = "WTREGEN"
_FRED_SERIES_RRP = "RRPONTSYD"


def _net_liquidity_trend(fred_api_key: str, lookback_tage: int = 180) -> tuple[str, str]:
    """Liefert (trend, detail) - trend in {"steigend","fallend","gleichbleibend",
    "unbekannt"}. RRP (taeglich) wird je WALCL/TGA-Datum (woechentlich,
    Mittwoch) auf den naechstgelegenen vorherigen RRP-Tag gemappt."""
    from datetime import date, timedelta

    import agent.krypto.regime as regime

    start = (date.today() - timedelta(days=lookback_tage)).isoformat()
    try:
        walcl_obs = macro.get_fred_history(_FRED_SERIES_WALCL, fred_api_key, start)
        tga_obs = macro.get_fred_history(_FRED_SERIES_TGA, fred_api_key, start)
        rrp_obs = macro.get_fred_history(_FRED_SERIES_RRP, fred_api_key, start)
    except Exception as exc:  # noqa: BLE001 - P-10, Net-Liquidity ist ein optionales Zusatzsignal
        return "unbekannt", f"Net-Liquidity-Abruf fehlgeschlagen: {exc}"

    tga_by_date = {o.date: o.value for o in tga_obs if o.value is not None}
    rrp_sorted = sorted(((o.date, o.value) for o in rrp_obs if o.value is not None), key=lambda kv: kv[0])

    def _naechster_rrp_wert(datum: str) -> float | None:
        kandidaten = [w for d, w in rrp_sorted if d <= datum]
        return kandidaten[-1] if kandidaten else None

    netto_werte: list[float] = []
    for o in walcl_obs:
        if o.value is None:
            continue
        tga_wert = tga_by_date.get(o.date)
        rrp_wert = _naechster_rrp_wert(o.date)
        if tga_wert is None or rrp_wert is None:
            continue
        netto_werte.append(o.value - tga_wert - rrp_wert * 1000)

    if len(netto_werte) < 2:
        return "unbekannt", "zu wenig abgeglichene Wochenwerte fuer einen Trend"

    trend = regime._pct_trend(netto_werte, NET_LIQUIDITY_TREND_THRESHOLD_PCT)
    aktuelle_mrd = netto_werte[-1] / 1000
    return trend, f"aktuell ca. {aktuelle_mrd:,.0f} Mrd. USD, {len(netto_werte)} abgeglichene Wochenwerte"


def _abgleich_m2_liquiditaet(conn, these: These) -> TheseAbgleich:
    import os

    import agent.krypto.regime as regime

    status = regime.get_last_known_regime_status(conn)
    liquiditaets_regime = status.get("liquiditaets_regime") if status else None
    m2_bekannt = bool(status) and liquiditaets_regime not in (None, "unbekannt")
    m2_begruendung = (
        status.get("liquiditaets_regime_begruendung") or f"Liquiditaetsregime: {liquiditaets_regime}."
        if m2_bekannt else None
    )

    fred_api_key = os.environ.get("FRED_API_KEY")
    net_liquidity_trend, net_liquidity_detail = (
        _net_liquidity_trend(fred_api_key) if fred_api_key else ("unbekannt", "kein FRED_API_KEY gesetzt")
    )

    if net_liquidity_trend in ("steigend", "fallend"):
        bullisch = net_liquidity_trend == "steigend"
        begruendung = f"Net Liquidity (Fed-Bilanz minus TGA minus Reverse-Repo) {net_liquidity_trend} ({net_liquidity_detail})."
        if m2_bekannt:
            begruendung += f" M2-Kontext (langsamere Bestaetigung): {m2_begruendung}"
        return TheseAbgleich(
            _einschaetzung_aus_richtung(bullisch, these.richtung), begruendung, status.get("created_at") if status else None,
        )

    # Net-Liquidity nicht berechenbar (kein Key/Abruf fehlgeschlagen/zu wenig
    # Historie) - Fallback auf reines M2, wie vor Punkt 18.
    if not m2_bekannt:
        return TheseAbgleich(
            "nicht_pruefbar",
            f"Weder Net-Liquidity ({net_liquidity_detail}) noch M2-Liquiditaetsregime verfuegbar.",
            None,
        )
    if liquiditaets_regime == "expansiv":
        bullisch = True
    elif liquiditaets_regime == "restriktiv":
        bullisch = False
    else:  # gemischt/widerspruechlich
        bullisch = None
    return TheseAbgleich(
        _einschaetzung_aus_richtung(bullisch, these.richtung), m2_begruendung, status.get("created_at"),
    )


# Materialitaetsschwellen (2026-07-24, Punkt 6 der #333-Statustabelle,
# Kategorie_Basisinformationen_Release2.md Abschnitt 15) - Dreizonen-Modell
# statt "jeder Netto-Wert zaehlt gleich": < RAUSCHEN = kein Signal, dazwischen
# = echtes Richtungssignal, >= GEDRAENGT = weiterhin richtungsbestaetigend,
# aber mit explizitem Ruecksetzer-Risiko-Hinweis (professionelle COT-Analyse
# behandelt stark gedraengte Positionierung als Kontraindikator, nicht als
# noch staerkere Bestaetigung). Lehrbuch-Naeherung (kein perzentil-basierter
# Wert moeglich, da keine COT-Historie gespeichert wird), als solche
# gekennzeichnet.
_COT_RAUSCHEN_SCHWELLE_PROZENT_OI = 10.0
_COT_GEDRAENGT_SCHWELLE_PROZENT_OI = 25.0

# Zinskurve-Totzone (Punkt 7) - ein Spread nahe Null gilt als "flach/uneindeutig",
# nicht als eindeutig normal/invertiert.
_ZINSKURVE_TOTZONE_PP = 0.25


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
    oi_summe = sum(s.open_interest for s in snapshots)
    netto_prozent_oi = abs(netto_summe) / oi_summe * 100 if oi_summe else 0.0
    begruendung = "; ".join(
        f"{s.rohstoff}: Managed-Money netto {'long' if s.managed_money_netto >= 0 else 'short'} "
        f"{abs(s.managed_money_netto):,} Kontrakte ({s.managed_money_long_anteil_oi_prozent}% Long-Anteil am "
        f"Open Interest, Bericht vom {s.report_datum})"
        for s in snapshots
    )

    if netto_prozent_oi < _COT_RAUSCHEN_SCHWELLE_PROZENT_OI:
        bullisch = None
        begruendung += (
            f" - kombinierte Netto-Position nur {netto_prozent_oi:.1f}% des gemeinsamen Open Interest, "
            "zu gering fuer ein belastbares Richtungssignal (Rauschen)."
        )
    else:
        bullisch = netto_summe > 0
        if netto_prozent_oi >= _COT_GEDRAENGT_SCHWELLE_PROZENT_OI:
            begruendung += (
                f" - kombinierte Netto-Position bei {netto_prozent_oi:.1f}% des Open Interest bereits stark "
                "gedraengt (Lehrbuch-Naeherung, keine perzentil-basierte Historie verfuegbar) - Ruecksetzer-Risiko, "
                "keine noch staerkere Bestaetigung."
            )
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
    if zk.spread_pp > _ZINSKURVE_TOTZONE_PP:
        bullisch = True
    elif zk.spread_pp < -_ZINSKURVE_TOTZONE_PP:
        bullisch = False
    else:
        bullisch = None
        begruendung += f" Spread innerhalb der Totzone (±{_ZINSKURVE_TOTZONE_PP}pp) - als flach/uneindeutig gewertet."
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
    """Absicherung/Hedge (2026-07-24, #333 Quick Win - ersetzt den fruaeheren
    Stub): der Aktien-Baermarkt-/VIX-Indikator ist entgegen der urspruenglichen
    Annahme bereits eigenstaendig aufrufbar (api/yfinance_history.py::
    get_equities_bear_market_status()/get_vix_reading()) - `agent/krypto/
    pipeline.py` importiert exakt dieselben Funktionen, keine Refaktorierung
    noetig. ODER-Verknuepfung von Baermarkt+VIX, konsistent mit dem bereits
    etablierten Muster bei der Boden-Zielzone (Task #245 - VIX als zweiter
    ODER-Trigger neben dem Aktien-Baermarkt-Status). VIX-Einordnung
    wiederverwendet `agent/krypto/regime.py::_vix_label()`/`VIX_BANDS`
    (20/"ruhig", 30/"erhoeht", 40/"gestresst", "krise") statt einer neu
    erfundenen Parallel-Schwelle.

    Wiederverwendet (2026-07-24, #333 Punkt 14) auch fuer alle Aktien-Regionen
    (Global/Europa/Nordamerika/USA/Asien-Pazifik/Einzellaender/Emerging
    Markets) - dort aber mit UMGEKEHRTER Polaritaet: Risk-off ist fuer eine
    normale Uebergewichten-These ein allgemeiner Gegenwind (spricht dagegen),
    waehrend er bei Absicherung genau das Gegenteil bedeutet (spricht fuer
    'aktiv' - eine Versicherung soll ja gerade im Risk-off greifen). Deshalb
    zwei getrennte Richtungs-Zweige: Absicherung-Sonderfall (`richtung` ist
    'aktiv'/'inaktiv', siehe These-Docstring) bleibt eigene Logik, alle
    anderen Kategorien nutzen die normale _einschaetzung_aus_richtung()."""
    from api.yfinance_history import get_equities_bear_market_status, get_vix_reading
    from agent.krypto.regime import _vix_label

    cfg = config.load_config().get("boden_zielzone", {})
    schwelle = cfg.get("equities_baermarkt_schwelle_prozent", 20)
    lookback = cfg.get("equities_baermarkt_lookback_jahre", 5)

    baermarkt_aktiv: bool | None = None
    baermarkt_text = "Aktien-Baermarkt-Status nicht verfuegbar."
    try:
        equities = get_equities_bear_market_status(lookback_years=lookback)
        sp500_aktiv = equities.sp500_drawdown_pct <= -schwelle
        nasdaq_aktiv = equities.nasdaq_drawdown_pct <= -schwelle
        baermarkt_aktiv = sp500_aktiv or nasdaq_aktiv
        baermarkt_text = (
            f"S&P500 {equities.sp500_drawdown_pct:+.1f}%, Nasdaq {equities.nasdaq_drawdown_pct:+.1f}% "
            f"vom {lookback}-Jahres-Hoch (Schwelle {schwelle}%) - Baermarkt "
            f"{'aktiv' if baermarkt_aktiv else 'nicht aktiv'}."
        )
    except Exception:  # noqa: BLE001 - P-10, ein fehlgeschlagener Baustein blockiert den anderen nicht
        pass

    vix_wert: float | None = None
    vix_label = "nicht verfügbar"
    try:
        vix_wert = get_vix_reading().wert
        vix_label = _vix_label(vix_wert)
    except Exception:  # noqa: BLE001
        pass
    vix_text = f"VIX aktuell {vix_wert:.1f} ({vix_label})." if vix_wert is not None else "VIX-Abruf fehlgeschlagen."

    if baermarkt_aktiv is None and vix_wert is None:
        return TheseAbgleich("nicht_pruefbar", "Weder Baermarkt-Status noch VIX verfuegbar.", None)

    # vix_label in ("gestresst", "krise") = exakt dieselbe Schwelle wie der
    # bereits etablierte VIX-ODER-Trigger bei der Boden-Zielzone (Task #245,
    # agent/krypto/regime.py:330) - keine neue Parallel-Schwelle.
    risk_off = bool(baermarkt_aktiv) or vix_label in ("gestresst", "krise")
    risk_on = (baermarkt_aktiv is False) and vix_label == "ruhig"
    begruendung = f"{baermarkt_text} {vix_text}".strip()

    if these.hauptgruppe == "absicherung":
        # Versicherungslogik: Risk-off STUETZT 'aktiv' (Absicherung soll
        # gerade im Risk-off greifen).
        if risk_off:
            bullisch = True
        elif risk_on:
            bullisch = False
        else:
            bullisch = None
        if bullisch is None:
            einschaetzung = "neutral"
        elif these.richtung == "aktiv":
            einschaetzung = "gestuetzt" if bullisch else "widerspricht"
        elif these.richtung == "inaktiv":
            einschaetzung = "widerspricht" if bullisch else "gestuetzt"
        else:
            einschaetzung = "neutral"
    else:
        # Normale Kategorien (Aktien-Regionen): Risk-off ist ein allgemeiner
        # Gegenwind fuer Aktien, unabhaengig von der Region - umgekehrte
        # Polaritaet zu Absicherung.
        if risk_off:
            bullisch = False
        elif risk_on:
            bullisch = True
        else:
            bullisch = None
        einschaetzung = _einschaetzung_aus_richtung(bullisch, these.richtung)

    return TheseAbgleich(einschaetzung, begruendung, None)


_ABGLEICH_FUNKTIONEN = {
    "m2_liquiditaet": _abgleich_m2_liquiditaet,
    "cot_positionierung": lambda conn, these: _abgleich_cot_positionierung(these),
    "zinskurve": lambda conn, these: _abgleich_zinskurve(these),
    "dollar_index": lambda conn, these: _abgleich_dollar_index(these),
    "baerenmarkt_overlay": lambda conn, these: _abgleich_baerenmarkt_overlay(these),
}


def _kombiniere_abgleiche(ergebnisse: list[TheseAbgleich]) -> TheseAbgleich | None:
    """Kombiniert mehrere Mechanismus-Ergebnisse fuer dieselbe These (2026-07-24,
    #333 Multi-Indikator-Design, siehe Kategorie_Basisinformationen_Release2.md
    Abschnitt 14/15) - Einigkeitsregel: nur wenn ALLE verfuegbaren (nicht
    'nicht_pruefbar') Einschaetzungen uebereinstimmen, gilt das Gesamtergebnis
    als 'gestuetzt'/'widerspricht', sonst 'neutral'. Verhindert, dass ein
    einzelnes Signal eine tatsaechlich gemischte Lage als eindeutig ausgibt -
    gleiche 2-von-2-Logik wie bei COT+EIA fuer Energie."""
    if not ergebnisse:
        return None
    begruendung = " | ".join(e.begruendung for e in ergebnisse)
    datenstaende = [e.datenstand for e in ergebnisse if e.datenstand]
    datenstand = max(datenstaende) if datenstaende else None
    pruefbare = [e for e in ergebnisse if e.einschaetzung != "nicht_pruefbar"]
    if not pruefbare:
        return TheseAbgleich("nicht_pruefbar", begruendung, datenstand)
    einschaetzungen = {e.einschaetzung for e in pruefbare}
    if einschaetzungen == {"gestuetzt"}:
        gesamt = "gestuetzt"
    elif einschaetzungen == {"widerspricht"}:
        gesamt = "widerspricht"
    else:
        gesamt = "neutral"
    return TheseAbgleich(gesamt, begruendung, datenstand)


def compute_these_abgleich(conn, these: These) -> TheseAbgleich | None:
    """Haupteinstiegspunkt: liefert den objektiven Abgleich fuer eine These,
    oder `None` wenn fuer die Hauptgruppe/Unterkategorie kein etablierter
    Pruef-Mechanismus existiert (z.B. Technologie & KI, Sonstige - P-10,
    bleibt bewusst leer statt einen Schein-Check vorzutaeuschen). Ruft ALLE
    zugeordneten Mechanismen auf (meist einer, Edelmetalle hat zwei) und
    kombiniert sie ueber _kombiniere_abgleiche()."""
    mechanismus_info = config.get_pruef_mechanismus(these.hauptgruppe, these.unterkategorie)
    if mechanismus_info is None:
        return None
    ergebnisse = []
    for mechanismus in mechanismus_info["mechanismen"]:
        fn = _ABGLEICH_FUNKTIONEN.get(mechanismus)
        if fn is not None:
            ergebnisse.append(fn(conn, these))
    return _kombiniere_abgleiche(ergebnisse)


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
