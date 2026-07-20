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
class FundamentalsSnapshot:
    """Aktien-Fundamentaldaten (2026-07-15, Non-Krypto-Agent-Pipeline Phase 1,
    siehe agent/aktien/pipeline.py) - komplett neue Datenkategorie, bisher nirgends
    im Projekt genutzt. Rein informativ (kein eigener Regime-Baustein), fliesst als
    Fact-Kontext in agent/aktien/analyst.py ein. P-10: einzelne fehlende Felder
    bleiben None statt geraten - kein Aufrufer sollte einen Wert erzwingen.

    Wachstumsfelder (2026-07-15, Nutzer-Nachfrage "welche Regeln fehlen noch?"):
    ohne diese waere die Bubble-Risiko-Regel (agent/aktien/analyst.py) nicht wirklich
    fundiert gewesen - ein erster Live-Test bewertete PLTRs hohes KGV faelschlich als
    "ohne erkennbares Wachstum", obwohl real ein Gewinnwachstum von +325%/Umsatz-
    wachstum von +85% vorlag (nur schlicht nie mitgeschickt)."""
    symbol: str
    kgv: float | None  # KGV = trailingPE (Kurs-Gewinn-Verhaeltnis)
    forward_kgv: float | None  # forwardPE - beruecksichtigt erwartetes Gewinnwachstum
    gewinnwachstum_pct: float | None  # earningsGrowth, als Prozent (yfinance liefert Faktor, z.B. 3.25 = +325%)
    umsatzwachstum_pct: float | None  # revenueGrowth, als Prozent
    dividendenrendite_pct: float | None  # dividendYield, als Prozent
    analysten_konsens: str | None  # recommendationKey, z.B. "buy"/"strong_buy"/"hold" - Drittmeinung, KEINE eigene Empfehlung
    analysten_kursziel_usd: float | None  # targetMeanPrice
    market_cap_usd: float | None
    sektor: str | None
    naechstes_earnings_datum: str | None  # 'YYYY-MM-DD', None wenn unbekannt/nicht gemeldet
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
    # Boden-Zielzone (AZ-4 Baustein 2, 2026-07-12, agent/krypto/regime.py::
    # _boden_zielzone()) - Preiszone in USD, nicht historisiert je Aenderung sondern
    # taeglich ueberschrieben (COALESCE-Upsert wie alle anderen Spalten hier).
    btc_boden_zielzone_von: float | None = None
    btc_boden_zielzone_bis: float | None = None
    eth_boden_zielzone_von: float | None = None
    eth_boden_zielzone_bis: float | None = None
    # ETH-Regressionswerte (indicators/calculations.py::BtcLogRegressionRisk.
    # predicted_price/residual_std) zusaetzlich zur fertigen Zone gespeichert - ETH
    # braucht (anders als BTC) einen neuen yfinance-Netzwerk-Call, der hoechstens
    # 1x/Tag ausgefuehrt wird (Tages-Cache, agent/krypto/pipeline.py::
    # _fetch_boden_zielzone_context()). Mit diesen zwei Werten laesst sich
    # _boden_zielzone() bei einem Cache-Treffer trotzdem jedes Mal FRISCH neu
    # rechnen (z.B. falls sich reifegrad_daempfer_staerke seit dem letzten Fetch
    # geaendert hat), statt nur die fertige alte Zone stur zu uebernehmen.
    eth_regression_predicted_price: float | None = None
    eth_regression_residual_std: float | None = None
    # Aktien-Baermarkt-Overlay: nur die rohen Drawdown-Werte gespeichert, bewusst
    # KEIN gespeichertes "aktiv"-Bool - der Schwellenwert (config.yaml
    # boden_zielzone.equities_baermarkt_schwelle_prozent) kann sich spaeter aendern,
    # ein gespeichertes Bool wuerde alte Zeilen dann falsch einfrieren.
    equities_sp500_drawdown_pct: float | None = None
    equities_nasdaq_drawdown_pct: float | None = None
    # Regime-Status-Anzeige (2026-07-17, Regime-Status+Parameter-Uebersicht) -
    # agent/krypto/regime.py::RegimeResult berechnet diese Felder bei jedem
    # Pipeline-Lauf frisch, sie wurden bisher aber nirgends gespeichert (nur
    # regime/regime_source ueberleben in signals). Ergaenzt um sie fuer eine
    # rein passive "letzter bekannter Stand"-Anzeige verfuegbar zu machen, ohne
    # dafuer einen neuen Live-Recompute anzustossen. dominance_trend_label wird
    # bewusst NICHT gespeichert - reine Funktion, jederzeit aus der bereits
    # vorhandenen Historie neu berechenbar (siehe regime.py::_dominance_trend_label()).
    zyklus_risiko: float | None = None
    zyklus_risiko_begruendung: str | None = None
    liquiditaets_regime: str | None = None
    liquiditaets_regime_begruendung: str | None = None
    btc_trend_label: str | None = None
    regime_reason: str | None = None
    # VIX-Fruehindikator (2026-07-18) - im Gegensatz zum nachlaufenden Aktien-
    # Baermarkt-Drawdown-Status (equities_sp500/nasdaq_drawdown_pct oben) ein
    # VORLAUFENDES Optionsmarkt-Stimmungssignal (^VIX via yfinance), taeglich
    # gecacht wie die uebrigen Boden-Zielzone-Werte. Nur der Rohwert gespeichert,
    # kein Label - Baender koennten sich spaeter aendern (analog zum
    # equities_baermarkt-Bool-Verzicht oben).
    vix_wert: float | None = None


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
    # Gegenargument-Pflichtfeld (2026-07-18, Regel 22 in analyst.py::SYSTEM_PROMPT,
    # echter CAT-Fall - Selbstkritik-Schritt in einem einzigen Call statt eines
    # teuren zweiten LLM-Aufrufs) - das staerkste Argument GEGEN die eigene
    # Empfehlung, MUSS die Konfidenz beeinflussen.
    gegenargument: str | None = None
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
    # AZ-4-Tranchen (2026-07-12, gestaffelte Kauf-/Verkaufszonen) - JSON-Liste von
    # {rang, anteil_prozent, zone, trigger_bedingung}, rein informativ (siehe
    # agent/krypto/analyst.py::_validate()). None = keine Tranchierung vorgeschlagen
    # (Normalfall) oder Groq-Antwort war fehlerhaft (wird dann verworfen, kein Fehlerfall
    # fuer das Gesamtsignal).
    tranchen_json: str | None = None
    # Cash-Reserve-Ziel (AZ-4 Baustein 3, 2026-07-12, agent/krypto/risk_gate.py::
    # compute_cash_reserve_ziel()) - nur befuellt bei BTC/ETH-Signalen im Regime
    # baer/krise_extrem/seitwaerts. Rein informativ, kein neues Veto.
    cash_reserve_ziel_btc_usd: float | None = None
    cash_reserve_ziel_eth_usd: float | None = None
    cash_reserve_ziel_gesamt_usd: float | None = None
    cash_reserve_ziel_begruendung: str | None = None
    # Cash-Veto (2026-07-18, Detailanalyse "Anzeige/Info bei Cash-Block") -
    # spiegelt den tatsaechlichen RM-4-Zustand dieser Bewertung, siehe
    # agent/krypto/risk_gate.py::RiskPreCheckResult.cash_veto-Docstring. Bewusst
    # getrennt von risk_veto/risk_veto_reason (die nur feuern, wenn das Modell
    # eine Regel MISSACHTET hat) - cash_veto ist auch bei regelkonformem,
    # selbst gewaehltem HALTEN gesetzt.
    cash_veto: bool = False
    cash_veto_reason: str | None = None
    # Risikofaktoren-Liste (2026-07-19, E-Mail-/App-Neustrukturierung in 3
    # Abschnitte: Mathematisch berechnet / LLM-Bewertung / Konklusion) - JSON-
    # serialisierte Liste von {"name", "bewertung": positiv|neutral|negativ,
    # "begruendung"}, deterministisch aus agent/krypto/risk_gate.py::
    # compute_risikofaktoren() berechnet, siehe dortigen Docstring. NICHT vom
    # LLM generiert - echter AVAX-Hebel-Fund zeigte, dass das Modell
    # antizyklische Fakten selbst fehlinterpretieren kann.
    risikofaktoren_json: str | None = None


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
    # Providerkennzeichnung (2026-07-14, z.B. "cerebras:...") - analog zu
    # Signal.groq_model/HebelSignal.llm_model, siehe update_marktscan_candidate_groq_writeup().
    # Bugfix 2026-07-15: Spalte existierte seit der Gemini-Integration bereits in der
    # DB (_migrate_marktscan_candidates_columns()), aber dieses Feld fehlte hier -
    # jeder SELECT * ueber _row_to_marktscan_candidate() brach seitdem mit
    # "unexpected keyword argument 'llm_model'" (real auf dem Notebook aufgetreten).
    llm_model: str | None = None
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


@dataclass
class OpenInterestSnapshot:
    """Zeitreihen-Punkt fuer Open Interest/Funding-Rate/Long-Konten-Anteil je
    Boerse (Hebel-Screening, 2026-07-14, siehe docs/hebel_positionsformel.md).
    Bisher wurde OI nur live/on-demand in agent/krypto/anticyclic.py::assess()
    abgerufen, nie gespeichert - fuer die %-Aenderung uebers Lookback-Fenster
    (Trendfolge-Zweig) braucht es eine echte Historie. Wie price_history_ohlc
    KEINE Pruning-Logik (Zeilen akkumulieren dauerhaft)."""
    symbol: str
    exchange: str  # 'binance'|'bybit'|'okx'
    fetched_at: str  # volle ISO-Zeit (nicht nur Datum - Lookback ist in Stunden)
    open_interest: float | None = None
    open_interest_usd: float | None = None  # nur OKX liefert das direkt
    funding_rate: float | None = None
    long_account_pct: float | None = None


@dataclass
class HebelTrigger:
    """Ein Eintrag pro Hebel-Screening-Tick (agent/krypto/hebel_screening.py,
    alle 15 Min) - analog MarktscanCandidate ein Lifecycle-Datensatz mit
    status, aber EIN Eintrag PRO LAUF (nicht upsert-gemergt), da jeder
    Screening-Tick eine eigene Bewertung ist. `richtung` ist hier die vom
    Screening implizierte Richtung, keine KI-Entscheidung."""
    symbol: str
    richtung: str  # 'LONG'|'SHORT'
    screened_at: str
    screening_run_id: str
    id: int | None = None
    trigger_zweig: str | None = None  # 'trendfolge'|'kontra'|None
    score_gesamt: float | None = None
    score_details_json: str | None = None
    oi_change_pct_lookback: float | None = None
    kursaenderung_pct_lookback: float | None = None
    funding_rate_aktuell: float | None = None
    long_konten_anteil_prozent: float | None = None
    ist_kandidat: bool = False
    # Lifecycle: 'neu'|'an_llm_uebergeben'|'llm_generiert'|'budget_erschoepft_uebersprungen'
    status: str = "neu"
    status_geaendert_am: str | None = None


@dataclass
class HebelPosition:
    """Rekonstruierter Bitpanda-Margin-Positions-Lebenszyklus (importer/
    bitpanda_margin_positions.py, 2026-07-14, siehe docs/hebel_positionsformel.md).
    Bitpanda kennzeichnet Liquidationen nicht separat (identisches Tag wie
    normaler Close) - `status='wahrscheinlich_liquidiert'` ist ein statistischer
    Befund (Gebuehren-Anomalie), keine von Bitpanda bestaetigte Tatsache.
    Die Zeile MIT status='offen' ist selbst der Akkumulator-Zustand zwischen
    inkrementellen Syncs (kein separates Compute-Objekt wie bei AvgCostResult).
    liquidationspreis_geschaetzt_eur ist bewusst EUR (nicht USD wie sonst im
    Hebel-System ueblich) - Bitpanda-Margin-Trades sind EUR-denominiert
    (trade_fiat_id=1), eine Umrechnung waere hier eine zusaetzliche, ungenutzte
    Fehlerquelle ohne Mehrwert."""
    symbol: str
    richtung: str  # 'LONG' - Bitpanda fuehrt aktuell kein Short aus
    status: str  # 'offen'|'geschlossen'|'wahrscheinlich_liquidiert'
    eroeffnet_am: str
    letzte_transaktion_unix_timestamp: int
    id: int | None = None
    geschlossen_am: str | None = None
    hebel_effektiv: float | None = None
    positionswert_eur: float | None = None
    kreditbetrag_eur: float | None = None
    eigenkapital_eur: float | None = None
    # Aggregierte gekaufte Menge (Summe trade_amount_cryptocoin ueber alle Open-
    # Tranchen) - ermoeglicht einen effektiven Einstandspreis (positionswert_eur /
    # positionsmenge) fuer die Liquidationspreis-Neuberechnung offener Positionen.
    positionsmenge: float | None = None
    liquidationspreis_geschaetzt_eur: float | None = None
    liquidationspreis_berechnet_am: str | None = None
    quelle_tags_json: str | None = None


@dataclass
class HebelSignal:
    """Ergebnis der Hebel-Analyst-Pipeline (agent/krypto/hebel_pipeline.py,
    2026-07-14, Phase 4, siehe docs/hebel_positionsformel.md). Append-only wie
    Signal - jeder Lauf fuegt eine neue Zeile ein, nie ein Upsert. Bewusst eine
    EIGENE Tabelle statt Wiederverwendung von `signals` (andere Spalten:
    richtung, 7-Aktionen-Vokabular statt 5, hebel_vorschlag/hebel_final,
    trigger_*, kein position_size/tranchen)."""
    symbol: str
    created_at: str
    richtung: str  # LONG|SHORT
    action: str  # 7-Aktionen-Vokabular, siehe hebel_analyst.REQUIRED_HEBEL_ACTIONS
    gate_passed: bool
    gate_reason: str | None
    risk_veto: bool
    facts_json: str
    id: int | None = None
    pipeline_version: str = "1"
    hebel_vorschlag: float | None = None
    hebel_final: float | None = None
    hebel_korrektur_hinweis: str | None = None
    trade_thesis_typ: str | None = None
    hebel_trigger_id: int | None = None
    trigger_zweig: str | None = None
    trigger_score: float | None = None
    confidence_pct: float | None = None
    short_reasoning: str | None = None
    long_reasoning_technisch: str | None = None
    long_reasoning_fundamental: str | None = None
    long_reasoning_makro: str | None = None
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
    halte_kriterium_bucket: str | None = None
    halte_kriterium_ziel_preis_usd: float | None = None
    halte_kriterium_ziel_preis_eur: float | None = None
    halte_kriterium_ziel_datum: str | None = None
    halte_kriterium_bedingung_text: str | None = None
    halte_kriterium_reasoning: str | None = None
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
    key_risks_text: str | None = None
    regime: str | None = None
    regime_source: str | None = None
    forecast_bull_text: str | None = None
    forecast_bull_prob_pct: float | None = None
    forecast_base_text: str | None = None
    forecast_base_prob_pct: float | None = None
    forecast_bear_text: str | None = None
    forecast_bear_prob_pct: float | None = None
    liquidationspreis_geschaetzt_usd: float | None = None
    eigenkapitalbedarf_usd: float | None = None
    # Nachtrag 2026-07-17 (echter LINK-Fall): bei action == HEBEL_SENKEN der
    # konkrete, deterministisch berechnete EUR-Betrag, der ins Eigenkapital
    # der Position nachgeschossen werden muesste, um den empfohlenen
    # hebel_final tatsaechlich zu erreichen - macht die Empfehlung erst
    # praktisch umsetzbar (vorher nur "Hebel senken" ohne konkrete Zahl).
    hebel_senkung_eigenkapital_nachschuss_eur: float | None = None
    ausfuehrbarkeit_hinweis: str | None = None
    risk_veto_reason: str | None = None
    groq_raw_response: str | None = None
    llm_model: str | None = None
    # Gegenargument-Pflichtfeld (2026-07-18, siehe Signal.gegenargument-Docstring,
    # analoge Regel in hebel_analyst.py::SYSTEM_PROMPT).
    gegenargument: str | None = None
    # Hebel-Backward-Tracking (2026-07-15, agent/krypto/hebel_backward_tracking.py) -
    # nur fuer ERÖFFNEN/NACHKAUFEN gefuellt, mirror Signal.outcome_* (models.py:204-212).
    # Zusaetzlicher Status "liquidation_wahrscheinlich" gegenueber Spot (siehe dort).
    outcome_status: str | None = None
    outcome_geprueft_am: str | None = None
    outcome_entschieden_am: str | None = None
    outcome_realisiertes_crv: float | None = None
    outcome_datenquelle: str | None = None
    # Risikofaktoren-Liste (2026-07-19, siehe Signal.risikofaktoren_json-
    # Docstring) - deterministisch aus agent/krypto/hebel_risk_gate.py::
    # compute_risikofaktoren_hebel() berechnet.
    risikofaktoren_json: str | None = None


@dataclass
class MakroHistorieMonat:
    """Historischer Makro-Konstellationsvergleich (2026-07-18, Nutzer-Idee, siehe
    Memory project_historischer_makro_konstellationsvergleich_idee.md). EIN Datenpunkt
    pro Kalendermonat (Monats-Granularitaet bewusst statt taeglich - fuer einen
    Jahrzehnte-Vergleich reicht das, reduziert Datenvolumen/Rauschen erheblich).
    Alle Felder nullable (P-10) - nicht jede Quelle deckt jeden Monat ab (DXY-Proxy
    z.B. erst ab 2006, siehe agent/krypto/makro_analog.py-Modul-Docstring), fehlende
    Werte werden in der Aehnlichkeitsberechnung als fehlende Dimension behandelt,
    NICHT als 0 (gleiches Prinzip wie risk_gate.py::_portfolio_values_usd())."""
    monat: str  # 'YYYY-MM'
    dxy_proxy: float | None = None
    fed_funds_rate: float | None = None
    rendite_10y: float | None = None
    cpi_yoy_prozent: float | None = None
    oel_wti: float | None = None
    spx_close: float | None = None
    spx_trend_deviation_std: float | None = None
    btc_close: float | None = None


@dataclass
class MakroAnalogErgebnis:
    """Gecachtes Ergebnis des historischen Makro-Konstellationsvergleichs - EIN
    Row pro Berechnungstag (taeglicher Scheduler-Job, siehe scheduler/background.py::
    makro_analog_job()), nicht pro Signal neu berechnet (teure Regression + Scan ueber
    Jahrzehnte). `ergebnis_json` enthaelt die aktuelle Konstellation, die Top-N
    historischen Analoge samt bekanntem Fortgang (SPX/BTC Forward-Rendite 6/12 Monate)
    und einen Ehrlichkeits-Hinweis zur Stichprobengroesse/Methodik - siehe
    agent/krypto/makro_analog.py::summarize_analogs_for_facts()."""
    berechnet_am: str
    ergebnis_json: str


@dataclass
class These:
    """Kategorie-Schwerpunkt-These (2026-07-19, Release 2 der Kategorie-
    Taxonomie - siehe Basisinfos/Kategorie_Basisinformationen_Release2.md
    fuer die volle Konzeption). Bewusst NICHT in config.yaml - das sind sich
    aendernde, app-verwaltete Daten (Status-Uebergaenge, KI-Vorschlaege),
    keine statische Konfiguration wie die Watchlist. Bezieht sich auf
    `hauptgruppe`/`unterkategorie`-IDs aus Basisinfos/kategorien.yaml, nicht
    auf Krypto (die Taxonomie deckt bewusst kein Krypto ab, siehe
    kategorien.yaml-Kopfkommentar) - eine These kann sich deshalb nie auf
    ein Krypto-Asset auswirken.

    `richtung`: 'uebergewichten'|'neutral'|'meiden' fuer normale
    Hauptgruppen, bei hauptgruppe='absicherung' stattdessen 'aktiv'/
    'inaktiv' (Versicherungs-Logik statt Richtungswette, siehe Konzept-
    Dokument Abschnitt 8, Punkt 3 - eine Richtungswette ergibt bei einem
    Hedge-Instrument keinen Sinn).

    `pruef_mechanismus`: einer von config.PRUEF_MECHANISMUS_PRO_HAUPTGRUPPE
    (m2_liquiditaet/cot_positionierung/zinskurve/dollar_index/kein_check/
    baerenmarkt_overlay) - bestimmt, welcher objektive Datencheck fuer
    these_abgleich() anwendbar ist, None wenn fuer die Hauptgruppe kein
    automatischer Check existiert.

    `review_am`: Wiedervorlage-Datum, der GUI-Vorschlag dafuer leitet sich
    vom Zeithorizont des pruef_mechanismus ab (siehe config.py) - reine
    Vorbelegung, der Nutzer kann frei ueberschreiben."""
    hauptgruppe: str
    richtung: str
    begruendung: str
    gesetzt_am: str
    id: int | None = None
    unterkategorie: str | None = None
    staerke: int | None = None  # 1-5, wirkt sich in Stufe 1 NUR auf Sortierung/Hervorhebung aus
    pruef_mechanismus: str | None = None
    review_am: str | None = None
    status: str = "aktiv"  # 'aktiv'|'erledigt'|'verworfen'
    quelle: str = "manuell"  # 'manuell'|'ki_vorschlag'
