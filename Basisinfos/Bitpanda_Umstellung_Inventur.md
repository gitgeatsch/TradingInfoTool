# Bitpanda-Umstellung — Inventur aller betroffenen Code-Stellen (Schritt 61, Stufe 0.6)

> **Wozu:** Nutzervorgabe 15.09.2026 — *„der Umbau ist massiv und du musst hier wirklich detailliert in Code und Doku, damit wir nichts vergessen“*.
> Jede Datei, die Bitpanda abfragt, `holdings`/`staked_quantity`/Einstand/Cash-Schluessel/Sync-Stempel oder `hebel_positions` liest oder schreibt, steht hier — mit Rolle und Umstellungsschritt.

⚠️ **Die Liste wird geprueft:** `python pruefe_pakete.py --paket BitpandaInventur` sucht mit denselben Mustern im Code (`agent/ api/ importer/ scheduler/ ui/ database/`, `main.py`, `config.py`, `extract_notebook_diagnose.py`).
Eine neue Fundstelle ohne Eintrag hier macht die Pruefung rot — **erst hier eintragen, dann bauen.**

Muster (Stand 15.09.2026, 53 Dateien):

| Kategorie | Bedeutung |
|---|---|
| Netz | Netzabruf alte API oder Schluessel |
| Sync | Abgleich-/Rekonstruktionsfunktionen |
| Zuordnung | Bitpanda-Symbol → Watchlist |
| Katalog | Katalog ,gelistet' |
| Bestand schreibt | schreibt `holdings` |
| Bestand liest | liest `holdings`, gestakt, Einstand |
| Cash | Cash-Schluessel `cash_reserve*` (auch Ziel-Reserve) |
| Stempel | Sync-Stempel |
| hebel_positions | Tabelle `hebel_positions` |

## A · SCHREIBEN ODER HOLEN VON BITPANDA — werden ersetzt oder umgestellt (12)

| Datei | Fundstellen (Funktion) | Rolle heute | Umstellung |
|---|---|---|---|
| `api/bitpanda.py` | **Netz:** Modulebene, _authenticated_get, get_crypto_wallets, get_fiat_wallets, get_non_crypto_wallets, get_trades, get_wallet_transactions<br>**Zuordnung:** Modulebene, find_listed_asset, get_non_crypto_wallets, get_trades, is_listed, resolve_bitpanda_symbol_to_watchlist<br>**Katalog:** Modulebene, _fetch_all_bitpanda_assets, find_listed_asset, get_listed_assets, get_listed_non_crypto_assets, get_non_crypto_wallets, is_listed, resolve_bitpanda_symbol_to_watchlist | Alte Schnittstelle v1 (Wallets, Trades, Transaktionen) und Katalog v3; Zuordnung Bitpanda-Symbol -> Watchlist | 1.1 neuer lesender Zugang daneben; alte Funktionen erst entfernen, wenn kein Aufrufer mehr (Stufe 4 Katalog). Zuordnung 1.10: ueber `asset_id`/ISIN statt Symbol (Katalog-Symbole 1.625-mal mehrfach) |
| `database/db.py` | **Sync:** get_bitpanda_holdings_last_synced_unix, get_bitpanda_holdings_synced_at, update_holding_staked_quantity<br>**Katalog:** Modulebene, get_bitpanda_gelistet_override<br>**Bestand schreibt:** import_holdings_manual_overrides, set_holding_avg_buy_price_manual, update_holding_avg_buy_price, update_holding_staked_quantity, upsert_holding<br>**Bestand liest:** Modulebene, export_holdings_manual_overrides, get_all_holdings, get_portfolio_prioritaets_bonus_je_symbol, import_holdings_manual_overrides, set_holding_avg_buy_price_manual, update_holding_avg_buy_price, update_holding_staked_quantity<br>**Cash:** Modulebene, _migrate_signal_cash_reserve_ziel_columns, get_bitpanda_holdings_synced_at, get_cash_reserve_fiat_eur, get_cash_reserve_synced_at, init_db, set_cash_reserve_fiat_eur, set_cash_reserve_synced_at<br>**Stempel:** get_bitpanda_avg_cost_last_synced_unix, get_bitpanda_holdings_last_synced_unix, get_bitpanda_holdings_synced_at, get_cash_reserve_synced_at, get_hebel_position_last_synced_unix, get_hebel_positions_synced_at, set_bitpanda_avg_cost_last_synced_unix, set_bitpanda_holdings_last_synced_unix, set_bitpanda_holdings_synced_at, set_cash_reserve_synced_at, set_hebel_positions_synced_at<br>**hebel_positions:** Modulebene, get_hebel_positions_synced_at, get_open_hebel_positions, get_portfolio_prioritaets_bonus_je_symbol, set_hebel_positions_synced_at, upsert_hebel_position | holdings schreiben/lesen, Einstand manuell/berechnet, Export/Import `holdings_manual_overrides.json`, Cash-Schluessel, alle Sync-Stempel, `hebel_positions`, Katalog-Override | 1.2 neue Felder (verfuegbar/gestakt/Hebel-Wallet getrennt?) nur mit Migration; Stempel-Semantik halten; 1.3 Cash gebunden/verfuegbar |
| `database/models.py` | **Bestand liest:** Holding, effective_avg_buy_price_eur<br>**Cash:** Signal<br>**hebel_positions:** HebelPosition, HebelSignal, OpenInterestSnapshot | `Holding` (quantity, staked_quantity, Einstand, `effective_avg_buy_price_eur`), `HebelPosition`; `Signal.cash_reserve_ziel_*` ist die ZIEL-Reserve, kein Bitpanda-Cash | 1.2 Bedeutung von quantity/staked_quantity dokumentiert halten (Leser rechnen quantity + staked_quantity) |
| `importer/bitpanda_avg_cost.py` | **Netz:** Modulebene, sync_avg_buy_prices<br>**Sync:** compute_avg_buy_prices, compute_staked_quantities, sync_avg_buy_prices<br>**Zuordnung:** Modulebene, sync_avg_buy_prices<br>**Bestand schreibt:** sync_avg_buy_prices<br>**Bestand liest:** Modulebene, AvgCostResult, compute_avg_buy_prices, compute_cost_basis_view, sync_avg_buy_prices<br>**Stempel:** sync_avg_buy_prices | Einstand aus alter Transaktionshistorie (Knopf, zuletzt 11.07.); `compute_staked_quantities` (ohne Rewards); `compute_cost_basis_view` (Leser fuer Prompt/GUI) | Staking-Teil in 1.2 stilllegen; Einstand = Stufe 2 (HEIKEL, abstimmen); `compute_cost_basis_view` bleibt Leser |
| `importer/bitpanda_margin_positions.py` | **Netz:** Modulebene, sync_hebel_positions<br>**Sync:** Modulebene, auto_add_unknown_hebel_symbols, reconstruct_margin_positions, sync_hebel_positions<br>**Katalog:** Modulebene, auto_add_unknown_hebel_symbols<br>**hebel_positions:** Modulebene, auto_add_unknown_hebel_symbols, sync_hebel_positions | Hebelpositionen aus alter Transaktionshistorie rekonstruiert; unbekannte Hebelsymbole aufnehmen | Stufe 3 auf `/v1/operations` (margin_trading_*), Tabelle `hebel_positions` in Bedeutung unveraendert |
| `importer/bitpanda_sync.py` | **Netz:** Modulebene, sync_fiat_cash_from_bitpanda, sync_from_bitpanda<br>**Sync:** Modulebene, DecreaseCandidate, _map_transactions_to_internal_symbols, apply_decrease, sync_fiat_cash_from_bitpanda, sync_from_bitpanda<br>**Zuordnung:** Modulebene, _map_transactions_to_internal_symbols, sync_from_bitpanda<br>**Bestand schreibt:** apply_decrease, sync_from_bitpanda<br>**Bestand liest:** Modulebene, DecreaseCandidate, sync_from_bitpanda<br>**Cash:** BitpandaSyncResult, sync_fiat_cash_from_bitpanda, sync_from_bitpanda<br>**Stempel:** Modulebene, sync_fiat_cash_from_bitpanda, sync_from_bitpanda | Bestandsabgleich: Menge = alter Wallet-Saldo, gestakt = `compute_staked_quantities` ab eigenem Cursor (URSACHE der Doppelzaehlung); Fiat-Cash; Rueckgangsbestaetigung `apply_decrease` | 1.2 ersetzen: Menge/gestakt direkt aus `/v1/portfolio` + Staking-Wallet-Saldo; 1.3 Cash; Rueckgangs-Bestaetigung entfaellt (kein Mehrdeutigkeitsproblem mehr) - Aufrufer in ui/app.py mitziehen |
| `importer/excel_import.py` | **Bestand schreibt:** import_holdings<br>**Bestand liest:** export_holdings, import_holdings | Import/Export holdings aus `Basisinfos/Assets.xlsx` (Quelle `import`) | 1.2 ENTSCHEIDEN: darf ein Excel-Import einen API-Bestand ueberschreiben? (Vorschlag: nur ohne Schluessel) |
| `main.py` | **Netz:** main | liest `BITPANDA_API_KEY`, reicht ihn an GUI und Scheduler | 1.1/1.3 zusaetzlich `FUSION_API_KEY`; 1.7 Schluesselueberwachung |
| `scheduler/background.py` | **Netz:** build_scheduler, hebel_screening_job<br>**Sync:** hebel_screening_job, refresh_bitpanda_holdings_job<br>**Katalog:** _ist_email_relevantes_asset, _on_signal_ready, hebel_screening_job, multi_asset_batch_job, refresh_bitpanda_holdings_job<br>**hebel_positions:** _refresh_hebel_position_liquidation_prices, hebel_screening_job | Jobs `refresh_bitpanda_holdings_job` (Bestand+Cash), `hebel_screening_job` (Hebelsync, Stempel), Katalogabrufe in mehreren Jobs | 1.2/1.3 Job auf neuen Zugang umstellen; Stufe 3 Hebelsync; Stufe 4 Katalog; Datenfrische-Stempel beibehalten |
| `ui/app.py` | **Netz:** __init__, _build_menu, _run_avg_cost_sync, _sync_bitpanda, _sync_bitpanda_avg_cost, run_app<br>**Sync:** AssetEditDialog, _on_confirm, _run_avg_cost_sync, _sync_bitpanda<br>**Katalog:** _refresh_bitpanda_assets, _refresh_watchlist_from_db, _toggle_bitpanda_gelistet_override, _try_auto_resolve_coingecko_id, _validate_new_asset<br>**Bestand liest:** _refresh_watchlist_from_db<br>**Cash:** _sync_bitpanda<br>**hebel_positions:** _refresh_watchlist_from_db | Menue/Knoepfe: Bitpanda-Abgleich, Einstand-Sync, Rueckgangs-Bestaetigung; Katalog fuer Watchlist-Pflege | 1.2 Knopf auf neuen Abgleich; Einstand-Knopf Stufe 2; Bestaetigungsdialog entfaellt; Katalog Stufe 4 |
| `ui/portfolio.py` | **Bestand liest:** Modulebene, AvgBuyPriceDialog, __init__, _on_edit_avg_price, refresh<br>**Cash:** __init__, _save_cash_reserve, _update_cash_reserve_synced_label, refresh, reload_cash_reserve_from_db<br>**Stempel:** reload_cash_reserve_from_db | Cash-Eingabefeld (schreibt `cash_reserve_fiat_eur`), Einstand-Dialog manuell, Bestandsanzeige, Stand-Anzeige | 1.6 Cashfeld L3 (abstimmen); Einstand-Dialog Stufe 2; Anzeige gestakt/verfuegbar |
| `ui/signals_view.py` | **Bestand schreibt:** _on_save_clicked<br>**Bestand liest:** _current_holding_quantity<br>**Cash:** _render_signal | `_on_save_clicked` schreibt holdings bei ,umgesetzt' (Quelle `signal_bestaetigung`); zeigt Cash-Ziel | 1.2 ENTSCHEIDEN: mit API als Wahrheit nur noch Vormerkung, der naechste Abgleich ueberschreibt |

## B · LESEN BESTAND, EINSTAND ODER CASH — Bedeutung halten, nach Stufe 1 gegenpruefen (29)

| Datei | Fundstellen (Funktion) | Rolle heute | Umstellung |
|---|---|---|---|
| `agent/absicherung_fakten.py` | **Bestand liest:** lage | `lage`: Bestand fuer Absicherungsfakten | nach 1.2 gegenpruefen |
| `agent/aktien/analyst.py` | **Bestand liest:** Modulebene, _build_haltung_facts, build_facts<br>**Cash:** build_facts | Haltungsfakten, Einstand, Cash | Einstand Stufe 2; nach 1.2 gegenpruefen |
| `agent/aktien/pipeline.py` | **Katalog:** Modulebene, generate_signal<br>**Bestand liest:** generate_signal | Bestand, Katalog-Veto | nach 1.2; Katalog Stufe 4 |
| `agent/datenfrische.py` | **Bestand liest:** _stand_bestand<br>**Cash:** _stand_bestand<br>**Stempel:** _stand_bestand, _stand_hebel_abgleich<br>**hebel_positions:** Modulebene, _stand_hebel_abgleich, pruefe | `_stand_bestand` (Stempel `bitpanda_holdings_synced_at`, Cash), `_stand_hebel_abgleich` | Stempel beim neuen Abgleich weiter setzen; 1.7 Schluesselfehler als eigener Zustand |
| `agent/hebel_abgleich.py` | **Sync:** Modulebene<br>**Stempel:** Modulebene, stand, stempel_setzen<br>**hebel_positions:** Modulebene, frische, stand, stempel_setzen | Frische des Hebelabgleichs (Stempel, Meldung) | Stufe 3: Stempel vom neuen Sync |
| `agent/hedge/analyst.py` | **Bestand liest:** _build_haltung_facts | Haltungsfakten, Einstand | Einstand Stufe 2 |
| `agent/hedge/pipeline.py` | **Katalog:** generate_signal<br>**Bestand liest:** _compute_portfolio_exposure, generate_signal | Portfolio-Exposure aus Bestand, Katalog-Veto | nach 1.2; Katalog Stufe 4 |
| `agent/krypto/analyst.py` | **Bestand liest:** Modulebene, _build_haltung_facts, build_facts<br>**Cash:** build_facts | Haltungsfakten (Bestand, Einstand via `compute_cost_basis_view`), Cash-Fakten | Einstand Stufe 2; nach 1.2 gegenpruefen |
| `agent/krypto/backward_tracking.py` | **Bestand liest:** compute_ausstiegs_empfehlungen<br>**hebel_positions:** compute_ausstiegs_empfehlungen | Ausstiegsempfehlungen aus Bestand und Hebelpositionen | nach 1.2 gegenpruefen |
| `agent/krypto/budget_allocator.py` | **Bestand liest:** _kern_symbole_hebel<br>**hebel_positions:** _kern_symbole_hebel, _offene_positionen_als_kandidaten | Kernsymbole Hebel aus Bestand, offene Hebelpositionen | nach 1.2/Stufe 3 gegenpruefen |
| `agent/krypto/hebel_pipeline.py` | **Bestand liest:** generate_hebel_signal<br>**hebel_positions:** Modulebene, generate_hebel_signal | Bestand und Hebelpositionen fuer Hebelsignal | nach 1.2/Stufe 3 gegenpruefen |
| `agent/krypto/marktscan.py` | **Katalog:** generate_candidate_writeup, run_scan<br>**Bestand liest:** run_scan | Bestand (gehalten ausschliessen), Katalog | nach 1.2; Katalog Stufe 4 |
| `agent/krypto/pipeline.py` | **Katalog:** generate_signal<br>**Bestand liest:** generate_signal<br>**Cash:** Modulebene, _compute_cash_reserve_ziel_context, generate_signal | Bestand, Cash-Ziel-Kontext, Katalog-Veto | nach 1.2; Katalog Stufe 4 |
| `agent/krypto/regelwerk_parameter.py` | **Cash:** Modulebene | Parameter Cash-Reserve-Ziel | nur lesen, keine Aenderung erwartet |
| `agent/krypto/risk_gate.py` | **Bestand liest:** _portfolio_values_usd, pre_check<br>**Cash:** RiskPreCheckResult, _cash_reserve_ziel_pro_asset, compute_cash_reserve_ziel, pre_check<br>**hebel_positions:** Modulebene | Portfoliowerte, Cash-Reserve-Ziel je Asset, `hebel_positions` | nach 1.2/1.3 gegenpruefen |
| `agent/krypto/signal_batch.py` | **Sync:** select_assets_due_for_signal<br>**Bestand liest:** select_assets_due_for_signal<br>**hebel_positions:** select_assets_due_for_signal | Auswahl faelliger Werte nach Bestand und Hebelpositionen | nach 1.2 gegenpruefen |
| `agent/multi_asset_batch.py` | **Bestand liest:** run_multi_asset_batch | Bestand fuer den Mehrklassen-Lauf | nach 1.2 gegenpruefen |
| `agent/portfolio_historie.py` | **Netz:** Modulebene, bestandsverlauf<br>**Bestand liest:** compute_hedge_wirksamkeit, rekonstruiere_stichtag, schreibe_tageswert<br>**Cash:** schreibe_tageswert | Tageswert/Kapital (`schreibe_tageswert`), Rueckrechnung (`rekonstruiere_stichtag`, `bestandsverlauf` aus alter Historie mit Symbol-Overrides VST-US/IS0C/CC), Hedge-Wirksamkeit | 1.5 Rueckrechnung aus `asset_balance_after` je Tag (HEIKEL); braucht 1.9 (OD7H/OD7C-Kurse) vorher |
| `agent/rohstoff/analyst.py` | **Bestand liest:** Modulebene, _build_haltung_facts, build_facts<br>**Cash:** build_facts | Haltungsfakten, Einstand, Cash | Einstand Stufe 2; nach 1.2 gegenpruefen |
| `agent/rohstoff/pipeline.py` | **Katalog:** generate_signal<br>**Bestand liest:** generate_signal | Bestand, Katalog-Veto | nach 1.2; Katalog Stufe 4 |
| `agent/rollen_eingabe.py` | **Bestand liest:** bestand<br>**hebel_positions:** bestand, gegenbestand_satz | `bestand`: Menge und Wert fuer den Prompt, Gegenbestand Hebel | nach 1.2 Pruefstand-Mail vergleichen |
| `agent/rollen_lauf.py` | **Bestand liest:** _ein_asset<br>**hebel_positions:** _ein_asset | `_ein_asset`: Menge fuer Mail und Rechnung, Hebelbestand | nach 1.2 Pruefstand-Mail vergleichen |
| `agent/themen_etf/analyst.py` | **Bestand liest:** Modulebene, _build_haltung_facts, build_facts<br>**Cash:** build_facts | Haltungsfakten, Einstand, Cash | Einstand Stufe 2; nach 1.2 gegenpruefen |
| `agent/themen_etf/pipeline.py` | **Katalog:** generate_signal<br>**Bestand liest:** generate_signal | Bestand, Katalog-Veto | nach 1.2; Katalog Stufe 4 |
| `agent/toepfe.py` | **Bestand liest:** cash_frei_eur<br>**Cash:** Modulebene, cash_frei_eur | `cash_frei_eur` = Fiat + Stablecoins - 2.000 (Docstring sagt faelschlich BEGRENZT) | 1.3 gebundenes Cash abziehen; 1.8 Docstring |
| `agent/verkaufsrechnung.py` | **Bestand liest:** stumme_bestaende | `stumme_bestaende`: gehaltene Werte ohne Messreihe | nach 1.2 gegenpruefen |
| `agent/warteschlange.py` | **Bestand liest:** _bestand_spot<br>**hebel_positions:** _bestand_hebel | Spot- und Hebelbestand je Wert | nach 1.2 gegenpruefen |
| `config.py` | **Sync:** update_watchlist_coingecko_id<br>**Bestand liest:** WatchlistAsset<br>**hebel_positions:** WatchlistAsset | `WatchlistAsset`: ,gehalten' wird live aus holdings/hebel_positions abgeleitet; Katalog fuer CoinGecko-Namensabgleich | nach 1.2 gegenpruefen; 1.10 Positionen ausserhalb der Watchlist |
| `extract_notebook_diagnose.py` | **Bestand liest:** main<br>**Cash:** Modulebene<br>**hebel_positions:** _paket_b, main | Export: Bestand, Cash, Hebelpositionen (Paket B) | 1.2/1.3 neue Felder in den Export (gebunden, Abgleichquelle) |

## C · LESEN NUR `hebel_positions` — Tabelle bleibt, Quelle wechselt in Stufe 3 (9)

| Datei | Fundstellen (Funktion) | Rolle heute | Umstellung |
|---|---|---|---|
| `agent/ausstiegsrechnung.py` | **hebel_positions:** sammel_mail | Sammelmail liest Hebelpositionen | Stufe 3 gegenpruefen |
| `agent/hebel_aggregat.py` | **hebel_positions:** Modulebene | Hebelpositionen aggregiert | Stufe 3 gegenpruefen |
| `agent/hebelfuehrung.py` | **hebel_positions:** Modulebene, lade | Hebelfuehrung laedt offene Positionen | Stufe 3 gegenpruefen |
| `agent/krypto/hebel_analyst.py` | **hebel_positions:** Modulebene, _build_position_aktuell_facts, _validate_hebel, build_hebel_facts | Positionsfakten Hebel | Stufe 3 gegenpruefen |
| `agent/krypto/hebel_risk_gate.py` | **hebel_positions:** Modulebene | Liquidationsschaetzung, Kommentarbezug | Stufe 3 gegenpruefen |
| `agent/krypto/hebel_screening.py` | **hebel_positions:** Modulebene | Hebelscreening, Kommentarbezug | Stufe 3 gegenpruefen |
| `agent/lagebeschreibung.py` | **hebel_positions:** _bestand | `_bestand` mit Hebelpositionen | Stufe 3 gegenpruefen |
| `api/derivatives.py` | **hebel_positions:** Modulebene | Kommentarbezug auf Hebelpositionen | keine Aenderung erwartet |
| `ui/hebel_view.py` | **hebel_positions:** Modulebene, refresh | Hebelansicht | Stufe 3 gegenpruefen |

## D · NUR KATALOG ,gelistet' — Stufe 4 (3)

| Datei | Fundstellen (Funktion) | Rolle heute | Umstellung |
|---|---|---|---|
| `agent/aktien/screener.py` | **Katalog:** Modulebene, scan_aktien_candidates | Aktien-Screener: gelistet? | Stufe 4 |
| `agent/asset_schalter.py` | **Katalog:** ist_handelbar | `ist_handelbar` fragt den Katalog | Stufe 4 |
| `ui/screener_view.py` | **Katalog:** _run_scan | Screener-Ansicht: Nicht-Krypto-Katalog | Stufe 4 |

## Fallen, die bei der Umstellung schon aufgefallen sind

- ⚠️ **`database/api_health.py` schreibt bei JEDEM Bitpanda-Abruf in die Standard-DB** (Ampel). Pruef- und Testskripte muessen `db.DB_PATH` vorher auf eine Wegwerf-DB umbiegen — am 15.09. im Stufe-0-Skript erst am Seiteneffekt bemerkt.
- ⚠️ **Katalog-Symbole sind nicht eindeutig** (1.625 Symbole mehrfach, z. B. ROL zweimal): Zuordnung ueber `asset_id`, nie ueber das Symbol.
- ⚠️ **Buchungsliste `/v1/operations`: der Cursor ist defekt** — abrufen ueber Datumsfenster (`to`).
- ⚠️ **`asset_amount` einer Belohnung ist BRUTTO** — die Staking-Provision steht in `fee_amount` und ist im Saldo schon abgezogen. Bestand immer aus `asset_balance_after` bzw. `/v1/portfolio`, nie aus Buchungssummen.
- ⚠️ **`average_buy_price` von Bitpanda = `invested_amount / balance`** — kein Einstand im eigenen Sinn, sobald verkauft oder getauscht wurde.
- ⚠️ **Zwei manuelle Schreibwege ausser der GUI:** Excel-Import (`Assets.xlsx`) und ,umgesetzt' im Signalfenster — Umgang in 1.2 entscheiden.
