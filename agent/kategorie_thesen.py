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


# EIA-Erdgas-5-Jahres-Saisonvergleich (2026-07-24, #333 Punkt 9, siehe
# Kategorie_Basisinformationen_Release2.md Abschnitt 14) - Korrektur einer zu
# vorschnellen frueheren Einschaetzung: get_natural_gas_storage_history()
# (api/eia.py) unterstuetzt bereits beliebige n_weeks, ein 5-Jahres-Vergleich
# war also schon immer machbar, nur bisher nicht genutzt (agent/rohstoff/
# pipeline.py ruft dieselbe Funktion nur mit n_weeks=8 fuer die reine
# Lagerbestands-Anzeige auf - eigener, groesserer Aufruf hier, kein Umbau dort).
_EIA_ERDGAS_LOOKBACK_JAHRE = 5
_EIA_ERDGAS_LOOKBACK_WOCHEN = 270  # 5 Jahre + Puffer fuer Kalenderwochen-Drift
_EIA_ERDGAS_MATERIALITAETSSCHWELLE_PROZENT = 5.0
_EIA_ERDGAS_KALENDERTAG_TOLERANZ = 4  # Toleranz beim Datumsabgleich je Vorjahr (Schaltjahre/Wochentag-Drift)
_EIA_ERDGAS_MIN_VORJAHRESWERTE = 3  # von 5 - darunter zu duenn fuer einen belastbaren Schnitt


def _abgleich_eia_erdgas(these: These) -> TheseAbgleich:
    """5-Jahres-Saisonvergleich des EIA-Erdgas-Lagerbestands (Lower-48,
    woechentlich) - siehe Kategorie_Basisinformationen_Release2.md Abschnitt
    14 fuer die volle Herleitung. Lagerbestand ueber dem 5-Jahres-Schnitt =
    reichliches Angebot = bearish fuer den Erdgaspreis (gegen 'uebergewichten'),
    darunter = knapperer Markt = bullisch. In config.py NUR fuer
    'energie:erdgas' mit cot_positionierung kombiniert (2-von-2), NICHT fuer
    die Energie-Hauptgruppe insgesamt (die poolt Erdgas+Rohoel im COT-Check,
    der EIA-Lagerbestand betrifft aber nur Erdgas)."""
    import os
    from datetime import datetime

    eia_api_key = os.environ.get("EIA_API_KEY")
    if not eia_api_key:
        return TheseAbgleich("nicht_pruefbar", "Kein EIA_API_KEY gesetzt.", None)

    from api.eia import get_natural_gas_storage_history

    try:
        readings = get_natural_gas_storage_history(eia_api_key, n_weeks=_EIA_ERDGAS_LOOKBACK_WOCHEN)
    except Exception as exc:  # noqa: BLE001 - P-10, sauberer nicht_pruefbar statt Absturz
        return TheseAbgleich("nicht_pruefbar", f"EIA-Abruf fehlgeschlagen: {exc}", None)
    if not readings:
        return TheseAbgleich("nicht_pruefbar", "EIA-Erdgas-Abruf lieferte keine Daten.", None)

    aktueller = readings[-1]
    aktuelles_datum = datetime.fromisoformat(aktueller.date)

    vergleichswerte: list[float] = []
    for jahre_zurueck in range(1, _EIA_ERDGAS_LOOKBACK_JAHRE + 1):
        try:
            ziel_datum = aktuelles_datum.replace(year=aktuelles_datum.year - jahre_zurueck)
        except ValueError:
            # 29. Februar existiert im Zieljahr nicht - auf den 28. ausweichen.
            ziel_datum = aktuelles_datum.replace(year=aktuelles_datum.year - jahre_zurueck, day=28)
        naechster = min(readings, key=lambda r: abs((datetime.fromisoformat(r.date) - ziel_datum).days))
        abstand_tage = abs((datetime.fromisoformat(naechster.date) - ziel_datum).days)
        if abstand_tage <= _EIA_ERDGAS_KALENDERTAG_TOLERANZ:
            vergleichswerte.append(naechster.value_bcf)

    if len(vergleichswerte) < _EIA_ERDGAS_MIN_VORJAHRESWERTE:
        return TheseAbgleich(
            "nicht_pruefbar",
            f"Nur {len(vergleichswerte)} von {_EIA_ERDGAS_LOOKBACK_JAHRE} Vorjahreswerten innerhalb der "
            f"Toleranz (±{_EIA_ERDGAS_KALENDERTAG_TOLERANZ} Tage) gefunden - zu duenn fuer einen belastbaren Schnitt.",
            aktueller.date,
        )

    durchschnitt = sum(vergleichswerte) / len(vergleichswerte)
    abweichung_prozent = (aktueller.value_bcf - durchschnitt) / durchschnitt * 100 if durchschnitt else 0.0
    begruendung = (
        f"Erdgas-Lagerbestand (Lower-48) {aktueller.value_bcf:.0f} Bcf am {aktueller.date} vs. "
        f"{len(vergleichswerte)}-Jahres-Schnitt {durchschnitt:.0f} Bcf ({abweichung_prozent:+.1f}%)."
    )

    if abs(abweichung_prozent) < _EIA_ERDGAS_MATERIALITAETSSCHWELLE_PROZENT:
        begruendung += f" Innerhalb des saisonalen Rahmens (< {_EIA_ERDGAS_MATERIALITAETSSCHWELLE_PROZENT:.0f}%)."
        return TheseAbgleich("neutral", begruendung, aktueller.date)

    # Ueberschuss (ueber dem Schnitt) = reichliches Angebot = bearish fuer den
    # Erdgaspreis; Unterschuss = knapper = bullisch.
    bullisch = abweichung_prozent < 0
    return TheseAbgleich(_einschaetzung_aus_richtung(bullisch, these.richtung), begruendung, aktueller.date)


# Bellwether-Sentiment (2026-07-24, #333 Punkt 11, siehe Kategorie_
# Basisinformationen_Release2.md Abschnitt 12) - manuell kuratierte Ticker-
# Koerbe (kein automatisches Ableiten moeglich, Bitpandas Themenkorb-Symbole
# sind Produktnamen, keine Boersenticker, siehe agent/aktien/screener.py).
# Nicht alle 18 Technologie-&-KI-Unterkategorien vorbereitet, nur die
# wahrscheinlichsten Kandidaten - Rest bei Bedarf spaeter ergaenzbar.
_BELLWETHER_TICKER: dict[str, list[str]] = {
    "technologie_ki:halbleiter": ["NVDA", "AMD"],
    "technologie_ki:ki": ["MSFT", "PLTR"],
    "technologie_ki:cybersicherheit": ["CRWD", "PANW"],
    "technologie_ki:biotech": ["AMGN", "VRTX"],
    "aktien_sektoren:gesundheit": ["UNH", "JNJ"],
    "aktien_sektoren:konsum_zyklisch": ["AMZN", "HD"],
    "aktien_sektoren:konsum_basis": ["PG", "KO"],
    "aktien_sektoren:industrie": ["HON", "CAT"],
    "aktien_sektoren:kommunikation": ["GOOGL", "META"],
    "aktien_sektoren:grundstoffe": ["LIN", "DOW"],
}

_BELLWETHER_ANALYSTENTREND_SCHWELLE_PP = 5.0


def _bellwether_analystentrend(ticker_korb: list[str], finnhub_api_key: str) -> tuple[bool | None, str]:
    """Durchschnitt Buy+StrongBuy-Anteil ueber den Korb, aktuell vs. Vormonat -
    Richtung nur bei Verschiebung > 5 Prozentpunkte gewertet (Abschnitt 12)."""
    from api.finnhub import get_recommendation_trends, summarize_recommendation_trend

    def buy_anteil(d: dict) -> float | None:
        total = d["strong_buy"] + d["buy"] + d["hold"] + d["sell"] + d["strong_sell"]
        return (d["strong_buy"] + d["buy"]) / total * 100 if total else None

    aktuell_werte, vormonat_werte = [], []
    for ticker in ticker_korb:
        try:
            trends = get_recommendation_trends(ticker, finnhub_api_key)
            summary = summarize_recommendation_trend(trends)
        except Exception:  # noqa: BLE001 - P-8, ein fehlgeschlagener Ticker blockiert nicht die anderen
            summary = None
        if not summary or not summary.get("vormonat"):
            continue
        aktuell_pct = buy_anteil(summary["aktuell"])
        vormonat_pct = buy_anteil(summary["vormonat"])
        if aktuell_pct is not None and vormonat_pct is not None:
            aktuell_werte.append(aktuell_pct)
            vormonat_werte.append(vormonat_pct)

    if not aktuell_werte:
        return None, f"Analystentrend (Finnhub, {', '.join(ticker_korb)}): keine auswertbaren Daten."

    aktuell_schnitt = sum(aktuell_werte) / len(aktuell_werte)
    vormonat_schnitt = sum(vormonat_werte) / len(vormonat_werte)
    delta = aktuell_schnitt - vormonat_schnitt
    text = (
        f"Analystentrend (Finnhub, {', '.join(ticker_korb)}): Buy+StrongBuy-Anteil {aktuell_schnitt:.0f}% "
        f"vs. Vormonat {vormonat_schnitt:.0f}% ({delta:+.1f}pp)."
    )
    if abs(delta) < _BELLWETHER_ANALYSTENTREND_SCHWELLE_PP:
        return None, text + f" Unter der {_BELLWETHER_ANALYSTENTREND_SCHWELLE_PP:.0f}pp-Schwelle, kein Signal."
    return delta > 0, text


def _bellwether_insider(ticker_korb: list[str]) -> tuple[bool | None, str]:
    """Anzahl Kaeufer vs. Verkaeufer im Korb (bewusst nicht Dollar-Volumen -
    ein einzelner Grossverkauf wuerde sonst alles dominieren, Abschnitt 12)."""
    from api.sec_edgar import get_recent_insider_transactions, summarize_insider_activity

    kaeufe_gesamt = 0
    verkaeufe_gesamt = 0
    irgendeine_daten = False
    for ticker in ticker_korb:
        try:
            transactions = get_recent_insider_transactions(ticker)
            summary = summarize_insider_activity(transactions)
        except Exception:  # noqa: BLE001
            summary = None
        if summary:
            irgendeine_daten = True
            kaeufe_gesamt += summary["anzahl_kaeufe"]
            verkaeufe_gesamt += summary["anzahl_verkaeufe"]

    if not irgendeine_daten:
        return None, f"Insider-Aktivitaet (SEC EDGAR, {', '.join(ticker_korb)}): keine Form-4-Transaktionen gefunden."

    text = (
        f"Insider-Aktivitaet (SEC EDGAR, {', '.join(ticker_korb)}): {kaeufe_gesamt} Kaeufer vs. "
        f"{verkaeufe_gesamt} Verkaeufer."
    )
    if kaeufe_gesamt == verkaeufe_gesamt:
        return None, text + " Ausgeglichen, kein Signal."
    return kaeufe_gesamt > verkaeufe_gesamt, text


def _bellwether_short_interest(ticker_korb: list[str]) -> tuple[bool | None, str]:
    """Days-to-Cover-Richtung letzte vs. vorletzte Meldeperiode, gemittelt
    ueber den Korb (Abschnitt 12). Steigende Days-to-Cover = wachsende
    bearishe Wetten = bearish; fallende = Eindeckung = bullisch."""
    from api.finra import get_short_interest_history, summarize_short_interest

    deltas: list[float] = []
    for ticker in ticker_korb:
        try:
            readings = get_short_interest_history(ticker)
            summary = summarize_short_interest(readings)
        except Exception:  # noqa: BLE001
            summary = None
        if not summary or not summary.get("vorperiode"):
            continue
        aktuell_dtc = summary["aktuell"].get("days_to_cover")
        vorperiode_dtc = summary["vorperiode"].get("days_to_cover")
        if aktuell_dtc is not None and vorperiode_dtc is not None:
            deltas.append(aktuell_dtc - vorperiode_dtc)

    if not deltas:
        return None, f"Short-Interest-Trend (FINRA, {', '.join(ticker_korb)}): keine auswertbaren Days-to-Cover-Daten."

    delta_schnitt = sum(deltas) / len(deltas)
    text = (
        f"Short-Interest-Trend (FINRA, {', '.join(ticker_korb)}): Days-to-Cover-Aenderung "
        f"{delta_schnitt:+.2f} Handelstage ggue. Vorperiode."
    )
    if delta_schnitt == 0:
        return None, text + " Keine Veraenderung, kein Signal."
    return delta_schnitt < 0, text


def _abgleich_bellwether(these: These) -> TheseAbgleich:
    """Kombiniert die 3 Bellwether-Signale (Abschnitt 12): mindestens 2 von 3
    muessen in dieselbe Richtung zeigen, sonst 'gemischt/neutral' - verhindert,
    dass ein einzelnes verrauschtes Signal (z.B. ein steuerlich bedingter
    Insider-Verkauf) allein die Kategorie-Einschaetzung kippt."""
    import os

    key = f"{these.hauptgruppe}:{these.unterkategorie}" if these.unterkategorie else these.hauptgruppe
    ticker_korb = _BELLWETHER_TICKER.get(key)
    if not ticker_korb:
        return TheseAbgleich("nicht_pruefbar", "Keine Bellwether-Ticker fuer diese Kategorie hinterlegt.", None)

    signale: list[tuple[bool | None, str]] = []

    finnhub_api_key = os.environ.get("FINNHUB_API_KEY")
    if finnhub_api_key:
        signale.append(_bellwether_analystentrend(ticker_korb, finnhub_api_key))
    else:
        signale.append((None, "Analystentrend (Finnhub): kein FINNHUB_API_KEY gesetzt."))

    signale.append(_bellwether_insider(ticker_korb))
    signale.append(_bellwether_short_interest(ticker_korb))

    begruendung = " | ".join(text for _, text in signale)
    auswertbare = [richtung for richtung, _ in signale if richtung is not None]
    bullische = sum(1 for r in auswertbare if r)
    bearische = sum(1 for r in auswertbare if not r)

    if bullische >= 2:
        bullisch = True
    elif bearische >= 2:
        bullisch = False
    else:
        bullisch = None
        begruendung += " - keine 2-von-3-Uebereinstimmung, gemischtes Bild."

    return TheseAbgleich(_einschaetzung_aus_richtung(bullisch, these.richtung), begruendung, None)


_ABGLEICH_FUNKTIONEN = {
    "m2_liquiditaet": _abgleich_m2_liquiditaet,
    "cot_positionierung": lambda conn, these: _abgleich_cot_positionierung(these),
    "zinskurve": lambda conn, these: _abgleich_zinskurve(these),
    "dollar_index": lambda conn, these: _abgleich_dollar_index(these),
    "baerenmarkt_overlay": lambda conn, these: _abgleich_baerenmarkt_overlay(these),
    "eia_erdgas": lambda conn, these: _abgleich_eia_erdgas(these),
    "bellwether_sentiment": lambda conn, these: _abgleich_bellwether(these),
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
