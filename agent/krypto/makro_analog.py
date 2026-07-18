"""Historischer Makro-Konstellationsvergleich (2026-07-18, Nutzer-Idee vom
2026-07-17, siehe Memory project_historischer_makro_konstellationsvergleich_idee.md
+ project_konfidenz_kalibrierung_regelwerk.md). Vergleicht die AKTUELLE Konstellation
mehrerer Makro-Faktoren (Dollarstaerke, Zinsen, Anleiherenditen, Oelpreis, Aktien-
bewertung) gegen HISTORISCHE Monate mit aehnlicher Konstellation UND bekanntem
weiteren Verlauf (Forward-Rendite S&P 500 / BTC).

Recherche-Ergebnis (Build-vs-Buy, 2026-07-18): kein kostenloses fertiges Tool macht
"aktuelle Konstellation -> historisches Analog -> Wahrscheinlichkeit" als nutzbaren
Service. MacroMicro-API waere das einzige nahe dran, kostet aber 5.000 $/Jahr - fuer
dieses Nur-kostenlose-Werkzeuge-Projekt nicht tragbar. Deshalb Eigenbau auf Basis
bereits vorhandener kostenloser, bereits integrierter Datenquellen:

- FRED (api/macro.py::get_fred_history(), bereits integriert): DXY-Ersatz
  (DTWEXBGS, seit 2006), Fed Funds Rate (FEDFUNDS, seit 1954), 10-Jahres-Rendite
  (DGS10, seit 1962), CPI (CPIAUCSL, seit 1913, YoY selbst berechnet), Oelpreis WTI
  (WTISPLC, monatlich seit 1946 - LAENGERE Historie als das sonst im Projekt
  genutzte DCOILWTICO, wichtig fuer die 1970er-Oelschock-Aera).
- yfinance (api/yfinance_history.py::get_full_price_history(), bereits
  integriert): S&P-500-Vollhistorie (^GSPC) als Bewertungs-/Blasen-Proxy UND als
  Aktien-Outcome-Referenz.
- blockchain.com (api/onchain.py::get_btc_full_price_history(), bereits
  integriert): BTC-Vollhistorie seit 2009 als Krypto-Outcome-Referenz.

BEWUSST KEIN Shiller-CAPE (waere der methodisch etabliertere Bewertungs-Proxy, aber
Yale liefert nur eine fragile Legacy-.xls-Datei ohne bestehende Parser-Infrastruktur
in diesem Projekt - openpyxl kann NUR .xlsx, kein xlrd installiert, siehe
requirements.txt). Stattdessen: log-linear Trend-Abweichung des S&P 500 selbst
(indicators/calculations.py::compute_log_linear_trend_deviation_series()) - gleiche
Grundidee (Abweichung vom langfristigen Wachstumspfad in Standardabweichungs-
Einheiten signalisiert eine Blase/Unterbewertung), aber komplett selbst berechnet
aus ohnehin schon abgerufenen Kursdaten, kein externer Datei-Download noetig.

KONSTELLATIONS-DIMENSIONEN sind bewusst NICHT alle ueber die volle Historie
verfuegbar (DXY-Proxy z.B. erst ab 2006) - die Aehnlichkeitsberechnung ist
fehlend-Werte-tolerant: fehlt eine Dimension bei Kandidat ODER aktuellem Monat,
wird sie fuer DIESEN Vergleich einfach uebersprungen (nicht als 0 angenommen,
gleiches Prinzip wie risk_gate.py::_portfolio_values_usd()) - ein Kandidat mit zu
wenigen ueberlappenden Dimensionen (config: mindest_dimensionen) wird verworfen.

KRYPTO-SONDERBEHANDLUNG (Nutzer-Entscheidung 2026-07-18, siehe Memory
project_konfidenz_kalibrierung_regelwerk.md): BTC hat nur ~3 volle Halving-Zyklen
mit statistischem Gewicht, und diese 3 Zyklen waren makro-maessig selbst nicht
vergleichbar (Nahe-Null-Zinsen 2013-2021 vs. heute) - ein aggregiertes "BTC-
Forward-Rendite ueber die Top-N-Analoge"-Kennzahl waere Pseudo-Statistik mit
irrefuehrender Praezision. Deshalb: summarize_analogs_for_facts() liefert BTC-
Forward-Renditen NUR pro einzelnem Analog (None bei Analogen vor BTCs Existenz),
aber KEIN aggregiertes/gemitteltes Krypto-Feld - das ist STRUKTURELL so, nicht nur
per Prompt-Anweisung unterdrueckt (P-10-Philosophie: das Modell wird nie blind
vertraut, die Versuchung wird also gar nicht erst als fertiger Fakt angeboten). Fuer
S&P 500 WIRD ein aggregiertes Feld geliefert (Median-Forward-Rendite ueber die
Top-N-Analoge) - dort ist die Stichprobentiefe (Jahrzehnte, viele unabhaengige
historische Analoge) deutlich groesser und methodisch tragfaehiger."""
from __future__ import annotations

import json
import logging
import statistics
from datetime import datetime, timezone

import database.db as db
from api.macro import get_fred_history
from api.onchain import get_btc_full_price_history
from api.yfinance_history import get_full_price_history
from database.models import MakroAnalogErgebnis, MakroHistorieMonat
from indicators.calculations import compute_log_linear_trend_deviation_series

logger = logging.getLogger(__name__)

FRED_SERIES_FUER_ANALOG = {
    "dxy_proxy": "DTWEXBGS",
    "fed_funds_rate": "FEDFUNDS",
    "rendite_10y": "DGS10",
    "cpi_headline_index": "CPIAUCSL",  # nur Zwischenwert, YoY wird selbst berechnet
    "oel_wti": "WTISPLC",
}

KONSTELLATIONS_DIMENSIONEN = (
    "dxy_proxy", "fed_funds_rate", "rendite_10y", "cpi_yoy_prozent",
    "oel_wti", "spx_trend_deviation_std",
)

FORWARD_HORIZONTE_MONATE = (6, 12)


def _to_monthly_last(observations: list) -> dict[str, float]:
    """(YYYY-MM -> letzter Wert des Monats) aus einer chronologisch aufsteigenden
    FredObservation-Liste. Werte mit value=None (FRED-Luecke) werden uebersprungen."""
    monthly: dict[str, float] = {}
    for obs in observations:
        if obs.value is None:
            continue
        monthly[obs.date[:7]] = obs.value
    return monthly


def _to_monthly_last_from_pairs(pairs: list[tuple]) -> dict[str, float]:
    """Wie _to_monthly_last(), aber fuer (datetime-artig, float)-Paare (yfinance-/
    BTC-Preishistorie statt FredObservation). `d` kann datetime ODER date sein -
    beide haben .strftime()."""
    monthly: dict[str, float] = {}
    for d, value in pairs:
        monthly[d.strftime("%Y-%m")] = value
    return monthly


def fetch_and_store_fred_series(conn, fred_api_key: str) -> None:
    """Laedt die volle Historie der 5 FRED-Reihen (siehe FRED_SERIES_FUER_ANALOG),
    resampled auf Monats-Granularitaet, berechnet CPI-YoY selbst (FRED liefert nur
    den Rohindex) und upserted alles additiv in makro_historie_monat. P-10: eine
    fehlgeschlagene Reihe blockiert die anderen nicht."""
    monthly_by_series: dict[str, dict[str, float]] = {}
    for feld, series_id in FRED_SERIES_FUER_ANALOG.items():
        try:
            obs = get_fred_history(series_id, fred_api_key, "1900-01-01")
            monthly_by_series[feld] = _to_monthly_last(obs)
        except Exception as exc:  # noqa: BLE001 - eine Reihe darf die anderen nicht blockieren
            logger.warning("FRED-Historie fuer %s (%s) fehlgeschlagen: %s", feld, series_id, exc)
            monthly_by_series[feld] = {}

    cpi_monthly = monthly_by_series.get("cpi_headline_index", {})
    cpi_yoy: dict[str, float] = {}
    for monat, wert in cpi_monthly.items():
        jahr, mon = monat.split("-")
        vorjahreswert = cpi_monthly.get(f"{int(jahr) - 1}-{mon}")
        if vorjahreswert is not None and vorjahreswert != 0:
            cpi_yoy[monat] = (wert / vorjahreswert - 1) * 100

    alle_monate: set[str] = set()
    for feld in ("dxy_proxy", "fed_funds_rate", "rendite_10y", "oel_wti"):
        alle_monate.update(monthly_by_series.get(feld, {}).keys())
    alle_monate.update(cpi_yoy.keys())

    for monat in sorted(alle_monate):
        db.upsert_makro_historie_monat(
            conn,
            MakroHistorieMonat(
                monat=monat,
                dxy_proxy=monthly_by_series.get("dxy_proxy", {}).get(monat),
                fed_funds_rate=monthly_by_series.get("fed_funds_rate", {}).get(monat),
                rendite_10y=monthly_by_series.get("rendite_10y", {}).get(monat),
                cpi_yoy_prozent=cpi_yoy.get(monat),
                oel_wti=monthly_by_series.get("oel_wti", {}).get(monat),
            ),
        )


def fetch_and_store_price_series(conn) -> None:
    """Laedt S&P-500- und BTC-Vollhistorie, berechnet die SPX-Trend-Abweichung
    (siehe Modul-Docstring) und upserted Monats-Schlusskurse + Abweichung additiv
    in makro_historie_monat. P-10: ein Fehlschlag einer Quelle blockiert die andere
    nicht."""
    try:
        spx_history = get_full_price_history("^GSPC")
        spx_monthly_close = _to_monthly_last_from_pairs(spx_history)
        deviation_series = compute_log_linear_trend_deviation_series(spx_history)
        spx_monthly_deviation = _to_monthly_last_from_pairs(
            [(datetime.fromisoformat(p.date), p.deviation_std) for p in deviation_series.points]
        )
        for monat, close in spx_monthly_close.items():
            db.upsert_makro_historie_monat(
                conn,
                MakroHistorieMonat(
                    monat=monat, spx_close=close,
                    spx_trend_deviation_std=spx_monthly_deviation.get(monat),
                ),
            )
    except Exception as exc:  # noqa: BLE001 - Krypto-Abruf soll trotzdem laufen
        logger.warning("SPX-Historie-Abruf/Regression fuer Makro-Analog fehlgeschlagen: %s", exc)

    try:
        btc_history = get_btc_full_price_history()
        btc_monthly_close = _to_monthly_last_from_pairs([(d, p) for d, p in btc_history if p > 0])
        for monat, close in btc_monthly_close.items():
            db.upsert_makro_historie_monat(conn, MakroHistorieMonat(monat=monat, btc_close=close))
    except Exception as exc:  # noqa: BLE001
        logger.warning("BTC-Historie-Abruf fuer Makro-Analog fehlgeschlagen: %s", exc)


def _dimension_stats(historie: list[MakroHistorieMonat]) -> dict[str, tuple[float, float]]:
    """Mittelwert+Standardabweichung je Dimension ueber alle Monate mit einem
    verwertbaren Wert - Grundlage fuer die Z-Score-Normalisierung (unterschiedliche
    Dimensionen haben voellig verschiedene Skalen, z.B. Zinsen 0-20 vs. Oelpreis
    10-150)."""
    stats: dict[str, tuple[float, float]] = {}
    for dim in KONSTELLATIONS_DIMENSIONEN:
        werte = [getattr(m, dim) for m in historie if getattr(m, dim) is not None]
        if len(werte) >= 2:
            std = statistics.stdev(werte)
            if std > 0:
                stats[dim] = (statistics.mean(werte), std)
    return stats


def _distanz(
    kandidat: MakroHistorieMonat, aktuell: MakroHistorieMonat, dim_stats: dict[str, tuple[float, float]],
) -> tuple[float, int]:
    """Euklidischer Abstand ueber Z-Score-normalisierte Dimensionen, NUR ueber
    Dimensionen, die bei BEIDEN Monaten vorhanden sind (fehlend-Werte-tolerant,
    siehe Modul-Docstring). Gibt (Distanz, Anzahl_verglichener_Dimensionen)
    zurueck - letzteres fuer den mindest_dimensionen-Filter des Aufrufers."""
    quadratsumme = 0.0
    anzahl = 0
    for dim, (mean, std) in dim_stats.items():
        wert_kandidat = getattr(kandidat, dim)
        wert_aktuell = getattr(aktuell, dim)
        if wert_kandidat is None or wert_aktuell is None:
            continue
        z_kandidat = (wert_kandidat - mean) / std
        z_aktuell = (wert_aktuell - mean) / std
        quadratsumme += (z_kandidat - z_aktuell) ** 2
        anzahl += 1
    return (quadratsumme ** 0.5, anzahl) if anzahl > 0 else (float("inf"), 0)


def _forward_return_lookup(historie: list[MakroHistorieMonat], feld: str):
    """Baut eine Nachschlage-Funktion monat -> {horizont_monate: forward_rendite_pct}
    aus dem gegebenen Preis-Feld (spx_close oder btc_close). Monate ohne Preiswert
    werden uebersprungen (Index bleibt trotzdem konsistent zur chronologischen
    Reihenfolge der VERFUEGBAREN Preispunkte, nicht zur vollen Kalendermonats-Liste -
    wichtig, weil btc_close z.B. erst ab 2009 existiert)."""
    punkte = [(m.monat, getattr(m, feld)) for m in historie if getattr(m, feld) is not None]
    index_by_monat = {monat: i for i, (monat, _) in enumerate(punkte)}

    def lookup(monat: str) -> dict[int, float | None]:
        ergebnis: dict[int, float | None] = {}
        idx = index_by_monat.get(monat)
        if idx is None:
            return {h: None for h in FORWARD_HORIZONTE_MONATE}
        basis_preis = punkte[idx][1]
        for horizont in FORWARD_HORIZONTE_MONATE:
            ziel_idx = idx + horizont
            if ziel_idx < len(punkte) and basis_preis:
                ergebnis[horizont] = round((punkte[ziel_idx][1] / basis_preis - 1) * 100, 2)
            else:
                ergebnis[horizont] = None
        return ergebnis

    return lookup


def _monat_differenz(a: str, b: str) -> int:
    """Anzahl Monate zwischen zwei 'YYYY-MM'-Strings (absoluter Wert, Reihenfolge egal)."""
    jahr_a, mon_a = (int(x) for x in a.split("-"))
    jahr_b, mon_b = (int(x) for x in b.split("-"))
    return abs((jahr_a * 12 + mon_a) - (jahr_b * 12 + mon_b))


def find_historical_analogs(
    conn, top_n: int = 5, mindest_abstand_monate: int = 24, mindest_dimensionen: int = 3,
) -> tuple[MakroHistorieMonat | None, list[dict]]:
    """Kernfunktion: findet die `top_n` historisch aehnlichsten Monate zum
    AKTUELLEN (=letzten gespeicherten) Monat. `mindest_abstand_monate` hat ZWEI
    Aufgaben: (1) schliesst die juengste Vergangenheit vor "jetzt" aus (triviale
    Selbst-Aehnlichkeit waere kein echtes unabhaengiges historisches Analog), UND
    (2) erzwingt denselben Mindestabstand ZWISCHEN den ausgewaehlten Analogen
    untereinander - live gegen echte Daten gefunden (2026-07-18): ohne diese
    zweite Regel waeren die Top-5-Analoge staendig 5 fast identische, nur wenige
    Monate auseinanderliegende Monate (z.B. Feb/Mar/Mai/Jun/Jul desselben Jahres) -
    autokorreliertes Rauschen statt unabhaengiger historischer Vergleichspunkte,
    weil benachbarte Monate fast immer aehnliche Makro-Werte haben. Gibt
    (aktueller_monat, liste_von_analog_dicts) zurueck - aktueller_monat ist None,
    wenn noch keine Historie vorliegt (z.B. erster Lauf ohne FRED_API_KEY)."""
    historie = db.get_makro_historie(conn)
    if len(historie) < 2:
        return None, []

    aktuell = historie[-1]
    dim_stats = _dimension_stats(historie)
    if not dim_stats:
        return aktuell, []

    grenzmonat_index = len(historie) - 1 - mindest_abstand_monate
    kandidaten = historie[: max(0, grenzmonat_index + 1)]

    bewertet = []
    for kandidat in kandidaten:
        distanz, anzahl_dim = _distanz(kandidat, aktuell, dim_stats)
        if anzahl_dim >= mindest_dimensionen:
            bewertet.append((distanz, anzahl_dim, kandidat))
    bewertet.sort(key=lambda t: t[0])

    top: list[tuple[float, int, MakroHistorieMonat]] = []
    for distanz, anzahl_dim, kandidat in bewertet:
        if len(top) >= top_n:
            break
        zu_nah_an_bereits_gewaehltem = any(
            _monat_differenz(kandidat.monat, gewaehlt.monat) < mindest_abstand_monate
            for _, _, gewaehlt in top
        )
        if zu_nah_an_bereits_gewaehltem:
            continue
        top.append((distanz, anzahl_dim, kandidat))

    spx_lookup = _forward_return_lookup(historie, "spx_close")
    btc_lookup = _forward_return_lookup(historie, "btc_close")

    analoge = []
    for distanz, anzahl_dim, kandidat in top:
        spx_forward = spx_lookup(kandidat.monat)
        btc_forward = btc_lookup(kandidat.monat)
        analoge.append({
            "monat": kandidat.monat,
            "distanz": round(distanz, 2),
            "dimensionen_verglichen": anzahl_dim,
            "konstellation": {dim: getattr(kandidat, dim) for dim in KONSTELLATIONS_DIMENSIONEN},
            "spx_forward_6m_prozent": spx_forward.get(6),
            "spx_forward_12m_prozent": spx_forward.get(12),
            "btc_forward_6m_prozent": btc_forward.get(6),
            "btc_forward_12m_prozent": btc_forward.get(12),
        })
    return aktuell, analoge


def summarize_analogs_for_facts(aktuell: MakroHistorieMonat | None, analoge: list[dict]) -> dict | None:
    """Baut den fuer build_facts()/build_hebel_facts() geeigneten Fakt. Siehe
    Modul-Docstring fuer die KRYPTO-SONDERBEHANDLUNG (kein aggregiertes BTC-Feld).
    Gibt None zurueck, wenn (noch) keine auswertbare Historie vorliegt - der
    Fakt sollte dann im Prompt einfach fehlen statt eines leeren/irrefuehrenden
    Platzhalters."""
    if aktuell is None or not analoge:
        return None

    spx_6m = [a["spx_forward_6m_prozent"] for a in analoge if a["spx_forward_6m_prozent"] is not None]
    spx_12m = [a["spx_forward_12m_prozent"] for a in analoge if a["spx_forward_12m_prozent"] is not None]

    return {
        "aktueller_monat": aktuell.monat,
        "aktuelle_konstellation": {dim: getattr(aktuell, dim) for dim in KONSTELLATIONS_DIMENSIONEN},
        "anzahl_analoge": len(analoge),
        "top_analoge": analoge,
        "spx_median_forward_6m_prozent": round(statistics.median(spx_6m), 2) if spx_6m else None,
        "spx_median_forward_12m_prozent": round(statistics.median(spx_12m), 2) if spx_12m else None,
        "hinweis": (
            "Aktien-Aggregat (spx_median_forward_*) basiert auf den gelisteten historischen "
            "Analogen und darf als grobe Orientierung fuer Aktien-Signale verwendet werden. "
            "Krypto (BTC) BEWUSST OHNE aggregierte Kennzahl - nur ~3 volle Halving-Zyklen mit "
            "statistischem Gewicht (n=3), ein Durchschnitt waere irrefuehrend praezise. "
            "btc_forward_*-Werte je Analog NUR zur qualitativen Einordnung nutzen (und nur "
            "dort vorhanden, wo BTC zum damaligen Zeitpunkt bereits existierte), NIEMALS als "
            "belastbare Statistik fuer eine Krypto-Konfidenz-Zahl."
        ),
    }


def run_makro_analog_update(conn, fred_api_key: str | None, config: dict) -> dict | None:
    """Vom Scheduler-Job (scheduler/background.py::makro_analog_job()) taeglich
    aufgerufen: Historie auffrischen, Analoge neu berechnen, Ergebnis cachen (siehe
    MakroAnalogErgebnis-Docstring - teure Berechnung, NICHT pro Signal neu
    ausgefuehrt). Gibt den berechneten Fakt zurueck (auch fuer einen sofortigen
    manuellen Testlauf nuetzlich), oder None bei zu duenner Datenlage."""
    if fred_api_key:
        fetch_and_store_fred_series(conn, fred_api_key)
    else:
        logger.info("Kein FRED_API_KEY gesetzt - Makro-Analog-Historie bleibt bei DXY/Zinsen/CPI/Oel unveraendert.")
    fetch_and_store_price_series(conn)

    cfg = config.get("makro_analog", {})
    aktuell, analoge = find_historical_analogs(
        conn,
        top_n=cfg.get("top_n_analoge", 5),
        mindest_abstand_monate=cfg.get("mindest_abstand_monate", 24),
        mindest_dimensionen=cfg.get("mindest_dimensionen", 3),
    )
    fakt = summarize_analogs_for_facts(aktuell, analoge)
    if fakt is not None:
        db.upsert_makro_analog_ergebnis(
            conn,
            MakroAnalogErgebnis(
                berechnet_am=datetime.now(timezone.utc).date().isoformat(),
                ergebnis_json=json.dumps(fakt, ensure_ascii=False),
            ),
        )
    return fakt


def get_cached_makro_analog_fact(conn) -> dict | None:
    """Fuer build_facts()/build_hebel_facts() (agent/krypto/analyst.py,
    agent/aktien/analyst.py, agent/krypto/hebel_analyst.py) - liest das
    gecachte Ergebnis, KEINE Neuberechnung pro Signal (siehe run_makro_analog_update()
    Docstring)."""
    ergebnis = db.get_latest_makro_analog_ergebnis(conn)
    if ergebnis is None:
        return None
    return json.loads(ergebnis.ergebnis_json)
