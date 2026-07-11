"""Datenmodelle fuer die SQLite-Tabellen (kein ORM, nur Dataclasses)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Holding:
    symbol: str
    quantity: float
    updated_at: str
    source: str = "import"
    # Einstandspreis (2026-07-11, echter Marktpreis aus Bitpanda-Trades, siehe
    # importer/bitpanda_avg_cost.py) - EUR, nicht USD (Bitpandas trade.attributes.
    # price ist EUR-denominiert, fiat_id "1" = EUR, live verifiziert). avg_buy_price_eur
    # ist automatisch berechnet (gleitender Durchschnitt), avg_buy_price_manual_eur ein
    # manueller Override mit komplettem Vorrang. tracked_qty ist die Menge, auf die
    # sich avg_buy_price_eur bezieht - kann kleiner als quantity sein (Staking-
    # Gutschriften/externe Einzahlungen ohne bepreisten Trade bleiben bewusst
    # unbepreist statt geschaetzt).
    avg_buy_price_eur: float | None = None
    avg_buy_price_tracked_qty: float | None = None
    avg_buy_price_computed_at: str | None = None
    avg_buy_price_manual_eur: float | None = None
    # 2026-07-11, Nutzer-Fund: aktuell gestakte Menge - ueber die normalen Wallet-
    # Endpunkte strukturell unsichtbar (siehe importer/bitpanda_avg_cost.py::
    # compute_staked_quantities()), additiv zu `quantity` zu behandeln, NICHT
    # bereits darin enthalten.
    staked_quantity: float | None = None

    @property
    def effective_avg_buy_price_eur(self) -> float | None:
        """Einzige Quelle der Wahrheit fuer "welcher Einstandspreis gilt" - manueller
        Override hat komplett Vorrang vor dem automatisch berechneten Wert."""
        return self.avg_buy_price_manual_eur if self.avg_buy_price_manual_eur is not None else self.avg_buy_price_eur


@dataclass
class PriceSnapshot:
    symbol: str
    # None fuer Nicht-Krypto-Assets (Multi-Asset-Tracking, Nutzer-Idee 2026-07-09) -
    # kein Default, bleibt bewusst ein Pflichtfeld, das jeder Aufrufer explizit setzt
    # (verhindert versehentliches Vergessen bei neuen Aufrufstellen).
    coingecko_id: str | None
    price_usd: float | None
    price_eur: float | None
    market_cap_usd: float | None
    volume_24h_usd: float | None
    change_24h_pct: float | None
    fetched_at: str


@dataclass
class PriceHistoryPoint:
    coingecko_id: str
    date: str  # 'YYYY-MM-DD', UTC-Tagesbucket
    price_usd: float | None
    price_eur: float | None
    fetched_at: str


@dataclass
class MacroSnapshot:
    date: str  # 'YYYY-MM-DD', UTC-Tagesbucket
    btc_dominance_pct: float | None
    fear_greed_value: int | None
    fear_greed_label: str | None
    fetched_at: str
    # FRED-Leitzinsen/CPI/M2/ISM-Ersatz (api/macro.py, Spezifikation Kap. 8) - alle
    # optional, da ein einzelner fehlgeschlagener FRED-Call die anderen Werte nicht
    # blockieren soll (P-10) und FRED_API_KEY optional ist (ohne Key bleiben alle None).
    fed_funds_rate: float | None = None
    m2_geldmenge: float | None = None
    cpi_headline: float | None = None
    cpi_core: float | None = None
    ezb_einlagensatz: float | None = None
    ezb_hauptrefinanzierung: float | None = None
    ezb_spitzenrefinanzierung: float | None = None
    ism_ersatz_philly_fed: float | None = None
    boj_tagesgeldsatz: float | None = None
    bok_diskontsatz: float | None = None
    # PBoC-LPR (Eastmoney, api/macro.py) - separat von den FRED-Werten, da eigener
    # Endpunkt/eigene Fehlerklasse.
    pboc_lpr_1y: float | None = None
    pboc_lpr_5y: float | None = None
    # Globale M2-Gesamtsicht (api/onchain.py::get_all_regional_m2, Spezifikation
    # Kap. 8) - Rohwerte in ihrer jeweiligen Landeswaehrung/Einheit, bewusst NICHT
    # umgerechnet (siehe agent/krypto/regime.py fuer die waehrungsneutrale Trendberechnung
    # ueber Prozent-Veraenderung statt absoluter Summen).
    m2_eurozone: float | None = None
    m2_china: float | None = None
    m2_japan: float | None = None


@dataclass
class Signal:
    """Ergebnis der Agent-Pipeline (Spezifikation Kap. 5, Ausgabeformat P-5).
    Append-only - jeder Pipeline-Lauf fuegt eine neue Zeile ein (Audit-Trail, Z-4/B-6),
    nie ein Upsert. id=None vor dem Insert."""
    symbol: str
    created_at: str
    action: str  # KAUFEN|VERKAUFEN|TAUSCHEN|HALTEN|NACHKAUFEN
    gate_passed: bool
    gate_reason: str | None
    risk_veto: bool
    facts_json: str
    id: int | None = None
    pipeline_version: str = "1"
    confidence_pct: float | None = None
    short_reasoning: str | None = None
    long_reasoning_technisch: str | None = None
    long_reasoning_fundamental: str | None = None
    long_reasoning_makro: str | None = None
    position_size_usd: float | None = None
    position_size_eur: float | None = None
    position_size_note: str | None = None
    entry_usd: float | None = None
    entry_eur: float | None = None
    stop_loss_usd: float | None = None
    stop_loss_eur: float | None = None
    take_profit_usd: float | None = None
    take_profit_eur: float | None = None
    holding_duration: str | None = None
    holding_duration_reason: str | None = None
    key_risks_text: str | None = None
    regime: str | None = None
    regime_source: str | None = None
    forecast_bull_text: str | None = None
    forecast_bull_prob_pct: float | None = None
    forecast_base_text: str | None = None
    forecast_base_prob_pct: float | None = None
    forecast_bear_text: str | None = None
    forecast_bear_prob_pct: float | None = None
    tauschen_target_symbol: str | None = None
    risk_veto_reason: str | None = None
    groq_raw_response: str | None = None
    groq_model: str | None = None
    # Nachtraegliche Umsetzungs-Rueckmeldung (Nutzer-Idee 2026-07-07, umgesetzt
    # 2026-07-09) - None = noch nicht entschieden/nicht abgefragt, sonst True/False.
    # umgesetzt_menge/-preis_usd sind bewusst optional (koennen leer bleiben, auch
    # wenn umgesetzt=True) - fuer eine spaetere Empfehlung-vs-Realitaet-Auswertung.
    umgesetzt: bool | None = None
    umgesetzt_am: str | None = None
    umgesetzt_menge: float | None = None
    umgesetzt_preis_usd: float | None = None
    # Entry/Stop-Loss/Take-Profit als Kurszonen statt Einzelwerte (2026-07-10,
    # Nutzer-Wunsch "von/bis" statt Punktwert). Alte *_usd/*_eur-Spalten bleiben fuer
    # Bestandszeilen (Append-only, Z-4/B-6) - neue Zeilen befuellen NUR die *_von/*_bis-Spalten.
    entry_usd_von: float | None = None
    entry_usd_bis: float | None = None
    entry_eur_von: float | None = None
    entry_eur_bis: float | None = None
    stop_loss_usd_von: float | None = None
    stop_loss_usd_bis: float | None = None
    stop_loss_eur_von: float | None = None
    stop_loss_eur_bis: float | None = None
    take_profit_usd_von: float | None = None
    take_profit_usd_bis: float | None = None
    take_profit_eur_von: float | None = None
    take_profit_eur_bis: float | None = None
    # Top-5 rangierte Gruende (2026-07-10) - flach abgelegt analog forecast_bull/base/bear,
    # rang ergibt sich implizit aus der Spaltennummer.
    top_grund_1_kategorie: str | None = None
    top_grund_1_text: str | None = None
    top_grund_2_kategorie: str | None = None
    top_grund_2_text: str | None = None
    top_grund_3_kategorie: str | None = None
    top_grund_3_text: str | None = None
    top_grund_4_kategorie: str | None = None
    top_grund_4_text: str | None = None
    top_grund_5_kategorie: str | None = None
    top_grund_5_text: str | None = None
    # Strukturiertes Halte-Kriterium (2026-07-10), ersetzt holding_duration fuer neue
    # Signale (Feld bleibt fuer Bestandszeilen erhalten).
    halte_kriterium_bucket: str | None = None
    halte_kriterium_ziel_preis_usd: float | None = None
    halte_kriterium_ziel_preis_eur: float | None = None
    halte_kriterium_ziel_datum: str | None = None
    halte_kriterium_bedingung_text: str | None = None
    halte_kriterium_reasoning: str | None = None
    # Backward-Tracking (2026-07-10, Selbstverifikations-Vision Schritt 2) - nur fuer
    # KAUFEN/NACHKAUFEN gefuellt (agent/krypto/backward_tracking.py), vergleicht die
    # Entry/Stop/Take-Zonen gegen die seit created_at vorliegende Kurshistorie.
    # None = noch nie geprueft.
    outcome_status: str | None = None  # offen | take_profit_erreicht | stop_loss_erreicht | abgelaufen_unentschieden | nicht_anwendbar
    outcome_geprueft_am: str | None = None
    outcome_entschieden_am: str | None = None
    outcome_realisiertes_crv: float | None = None
    outcome_datenquelle: str | None = None  # real (OHLC) | proxy (Tagesschlusskurs)


@dataclass
class MarktscanCandidate:
    """Ein von agent/krypto/marktscan.py entdeckter, bewerteter Kandidat (Spezifikation
    Kap. 13, Stufe A-D). Anders als Signal (reines Append-only-Log je Pipeline-Lauf)
    ist das ein EINZELNER, veraenderlicher Datensatz mit Lifecycle-`status` (U-10) -
    ein `upsert`, kein `insert` je Scan. id=None vor dem ersten Insert."""
    coingecko_id: str
    symbol: str
    name: str
    discovered_at: str
    discovery_source: str  # 'trending' | 'top_gainers'
    scan_run_id: str
    filter_a_bestanden: bool
    id: int | None = None
    # Stufe A
    tier: str | None = None  # 'tier1'|'tier2'|'tier3'|None (unter Tier-3-Untergrenze)
    market_cap_usd: float | None = None
    volume_24h_usd: float | None = None
    vol_marktkap_ratio: float | None = None
    alter_tage_geschaetzt: int | None = None
    alter_tage_quelle: str | None = None  # 'atl_date_proxy'
    filter_a_begruendung: str | None = None
    # Handelsboersen-Check (Nutzer-Wunsch 2026-07-09, api/bitpanda.py) - bewusst NUR
    # Warnung, kein Stufe-A-Ausschluss (ein nicht gelisteter Coin kann trotzdem
    # beobachtenswert sein). None = Pruefung fehlgeschlagen/nicht durchgefuehrt.
    bitpanda_gelistet: bool | None = None
    # Marktdaten zum Entdeckungszeitpunkt
    price_usd: float | None = None
    price_eur: float | None = None
    change_24h_pct: float | None = None
    # Stufe B (0-100 je Kategorie, None wenn nicht bewertbar)
    score_technik: float | None = None
    score_fundamental: float | None = None
    score_momentum: float | None = None
    score_kontext_makro: float | None = None
    signale_technik_json: str | None = None
    signale_fundamental_json: str | None = None
    signale_momentum_json: str | None = None
    signale_kontext_json: str | None = None
    # Stufe C
    score_gesamt: float | None = None
    gewichte_json: str | None = None
    regime_bei_scan: str | None = None
    # Stufe D
    einstufung: str | None = None  # 'kein_treffer'|'watchlist_wuerdig'|'kaufkandidat'
    einstufung_begruendung: str | None = None
    small_cap_budget_hinweis: str | None = None
    # optionale Groq-Begruendung (hybrid, siehe agent/krypto/marktscan.py)
    groq_kurzbegruendung: str | None = None
    groq_langbegruendung_json: str | None = None
    groq_generiert_am: str | None = None
    # Lifecycle (U-10)
    status: str = "neu"  # 'neu'|'nutzer_behalten_manuell_uebernommen'|'nutzer_verworfen'
    status_geaendert_am: str | None = None


@dataclass
class OhlcPoint:
    """Echte Tageskerze von Kraken (nicht die CoinGecko-Schlusskurs-Naeherung)."""
    symbol: str
    currency: str  # 'USD' oder 'EUR'
    date: str  # 'YYYY-MM-DD', UTC-Tagesbucket
    open: float
    high: float
    low: float
    close: float
    volume: float
    fetched_at: str
