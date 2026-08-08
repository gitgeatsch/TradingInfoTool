# -*- coding: utf-8 -*-
"""Diagnoseskript (2026-07-17, erweitert 2026-07-18): breiter Gesundheits-/
Optimierungs-Export seit dem heutigen Notebook-Neustart + Sync, PLUS
Einzelfall-Tiefenanalyse fuer ein Symbol (Standard: LINK, siehe
Hebelverhalten-Diskussion).

Ziel laut Nutzer: primaer Bugs/Fehler identifizieren, sekundaer Ansatzpunkte
fuer LLM-Budget/Parameter-Optimierung und praezisere Empfehlungen liefern -
deshalb rohe, aber vollstaendige Daten statt vorgefertigter Schlussfolgerungen,
die Bewertung passiert danach gemeinsam.

Nachtrag (2026-07-18, Nutzer-Wunsch "besser zu viel als zu wenig"):
konsolidiert jetzt auch, was zuvor ein getrenntes, nie ins Repo
zurueckgesyncstes Notebook-Skript (00_Metadaten.json bis
05_Complete_Log_Export.txt) separat abgedeckt hatte - EIN versioniertes
Skript statt zwei driftender Kopien. Neu: zeitlich begrenzter Log-Auszug
(inkl. rotierter .1/.2/.3-Dateien), daraus geparste Job-Fehlschlag-Historie
(api_health_status haelt nur den JEWEILS LETZTEN Zustand je Quelle, keine
Historie) und Groq-Tageserschoepfungs-Ereignisse, sowie ein regelbasierter
Auffaelligkeiten-Filter (KEIN Ersatz fuer die eigentliche inhaltliche
Bewertung, nur ein Vorfilter fuer offensichtliche strukturelle Widersprueche).
facts_json/*_raw_response bleiben weiterhin bewusst ausgeschlossen (siehe
Spaltenauswahl unten) - fuer einen einzelnen Kandidaten im Detail ist der
neue Doppelklick-Dialog in der App selbst (2026-07-18) der bessere Weg.

Nachtrag (2026-07-20, Nutzer-Wunsch "auf neue Features pruefen, damit wir
nichts vergessen"): seit dem letzten Update dieses Skripts (2026-07-18,
Commit 9bc950a) kamen mehrere Features hinzu, die hier bisher unsichtbar
waren - nachgezogen:
- `risikofaktoren_json` (3-Abschnitte-Neustrukturierung, 2026-07-19) fehlte
  komplett in der Spaltenauswahl fuer signals/hebel_signals.
- `halte_kriterium_ziel_preis_usd/eur`+`ziel_datum` fehlten (nur
  bedingung_text/reasoning/bucket waren erfasst - das eigentliche Ziel
  selbst nicht).
- `outcome_entschieden_am`/`outcome_datenquelle` fehlten (nur status/
  geprueft_am/realisiertes_crv waren erfasst).
- Spot-spezifische Felder `tranchen_json` (AZ-4), `cash_reserve_ziel_*`
  (RM-4) und `umgesetzt*` (hat der Nutzer die Empfehlung tatsaechlich
  ausgefuehrt?) fehlten komplett.
- Drei neue Tabellen waren gar nicht exportiert: `thesen` (Schwerpunkte-
  Tab, Release 2, steuert these_abgleich-Bias), `oi_abdeckung_status`
  (2026-07-19, direkt relevant fuer den CANTON-Warnungs-Bugfix vom
  2026-07-20) und `asset_hebel_settings` (Hebel-Pruefung-Toggle je
  Symbol) - alle drei jetzt als eigene Payload-Sektionen ergaenzt.
- Warteschlangen-Status (`hebel_triggers`/`marktscan_candidates` nach
  `status` gruppiert) ergaenzt, um zu sehen, ob der "Info-Leichen"-
  Verfall-Fix (2026-07-19) die Kandidatenliste tatsaechlich begrenzt hat.
- `llm_calls_heute["cerebras"]` entfernt - `api/cerebras.py` wurde
  vollstaendig geloescht, der Zaehler war seither dauerhaft 0 und damit
  irrefuehrende Alt-Referenz.
- `db.init_db(conn)` wird jetzt zu Beginn aufgerufen (rein additive,
  idempotente Migrationen, identisch zum Verhalten bei jedem main.py-
  Start) - stellt sicher, dass alle oben genannten neuen Tabellen/Spalten
  tatsaechlich existieren, auch falls das Skript einmal gegen eine
  Datenbank laeuft, die seit einem der letzten Feature-Commits nicht mehr
  neu gestartet wurde.

Nachtrag (2026-07-21, Nutzer-Fund "Discovery 16:00 Uhr, Signal erst 19:30
Uhr"): neue Sektion `marktscan_discovery_llm_delta` - Delta in Minuten
zwischen `discovered_at` und `groq_generiert_am` je Kandidat plus Min/Max/
Median/Durchschnitt, um zu pruefen ob die beobachtete Luecke systematisch
(Budget-Allocator-Aufschub) oder ein Einzelfall war. Siehe Memory
project_delta_berechnung_llm_abfrage_timing.md.

Nachtrag (2026-07-21, Nutzer-Fund ETH LONG "Einstieg haette gestern
passieren muessen"): analoge neue Sektion `hebel_erstmalige_erkennung_delta`
- bei Hebel-Triggern (anders als Marktscan) legt jeder 15-Min-Screening-Tick
eine NEUE Zeile an, das per hebel_trigger_id verknuepfte Objekt ist deshalb
immer der neueste Tick und verschleiert eine laenger bestehende Kandidatur -
diese Sektion sucht stattdessen den fruehesten ist_kandidat=1-Zeitpunkt seit
dem vorherigen Signal fuer dasselbe Symbol/Richtung-Paar.

Nachtrag (2026-07-21, Nutzer-Vorgabe "umfangreich testen vor finaler
Umsetzung"): neue Sektion `rohdaten_fuer_backtest` - schlanker Export ALLER
ist_kandidat=1-/kaufkandidat-Zeilen (nicht nur der zuletzt gewaehlten) als
Grundlage fuer backtest_budget_allocator_sla.py, das den neuen SLA-Algorithmus
gegen die echte Historie nachspielt, bevor Produktivcode geaendert wird.

Nachtrag (2026-07-22, Nutzer-Frage "funktioniert das System auf Glueck?"):
neue Sektion `preishistorie_ueberholte_symbole` - Preishistorie (price_
history_ohlc) fuer alle Symbole, die mindestens ein Hebel- oder Spot-Signal
mit outcome_status='ueberholt_durch_neuere_analyse' haben. `hebel_signals`/
`spot_signals` weiter oben enthalten bereits alle Zonen-/Zeitstempel-Felder
dieser Signale - diese Sektion liefert zusaetzlich die seitherige echte
Kurshistorie, damit backtest_ueberholt_erkennung.py simulieren kann, ob ein
unter den geplanten neuen Gates (Mindestbeobachtung + Zonen-Reaffirmation,
siehe Plan-Datei) "gerettetes" Signal tatsaechlich Take-Profit/Stop-Loss
erreicht haette. Bewusst nur fuer betroffene Symbole (nicht die gesamte
price_history_ohlc-Tabelle) - haelt den Export schlank.

Nachtrag (2026-08-02, Maßnahme 3 der Dead-Loop-Synthese): neue Sektion
`preishistorie_signal_symbole`. Die Sektion von 2026-07-22 (oben) deckt nur
Symbole mit 'ueberholt'-Ausgang ab - beim Versuch, ADX/Choppiness rueckwirkend
ueber bereits aufgeloeste Signale nachzurechnen, fehlten dadurch 14 von 32
Hebel-Signal-Symbolen, darunter ausgerechnet die aktiven (SOL, NEAR, AVAX,
APT, RENDER, SEI, TAO ...). Die Daten lagen in der DB, nur nicht im Export -
eine reine Export-Luecke, keine Datenluecke. Die neue Sektion nimmt alle
Signal-Symbole mit, dafuer zeitlich begrenzt (ab aeltestem Signal minus 60
Tage Indikator-Vorlauf) statt voller Historie; sie ersetzt die aeltere
Sektion nicht, weil der Ueberholt-Backtest dort die volle Historie braucht.

Nachtrag (2026-07-24, NB-Analyse-Fund): `kontrathese_zu_position`/
`kontrathese_llm_richtung` (heutiges Kontrathese-Uebersetzung-Feature,
siehe HebelSignal-Docstring) fehlten in `_HEBEL_SIGNAL_SPALTEN` - die
Produktions-DB war korrekt befuellt, nur dieser Export sah die beiden
Spalten nicht (kein Live-Bug, reine Export-Luecke, analog den fruaeheren
Nachzieh-Eintraegen oben).

Nachtrag (2026-07-26, Nutzer-Frage "brauchen die heutigen Umsetzungen neues
Logging/DB-Extrakte?"): zwei Luecken geschlossen.
- `konfidenz_kalibrierung` (compute_konfidenz_kalibrierung(), siehe
  project_konfidenz_kalibrierungskurve.md) als fertige Aggregat-Sektion
  ergaenzt - analog provider_performance, erspart eine manuelle Nachrechnung
  aus den ohnehin schon exportierten confidence_pct/outcome_status-Spalten.
- `deribit_cross_check_verlauf` (neu, siehe _deribit_cross_check_verlauf()
  unten) - der rohe Deribit-DVOL/Skew-Wert wird NIRGENDS dauerhaft
  gespeichert (Live-Fetch pro Signal, siehe agent/krypto/optionsmarkt.py) und
  steckt nur transient in facts_json, das dieser Export sonst bewusst
  ausschliesst. Gezielter Parse NUR des optionsmarkt-Teilobjekts (nicht der
  gesamte Blob) - ohne diese Sektion waere spaeter nie rekonstruierbar, ob
  der Deribit-Cross-Check ueberhaupt etwas bewirkt hat (Deribit selbst hat
  keine historischen Options-Skew-Snapshots nach Verfall).

Nachtrag (2026-07-26, Z.ai-Gegenpruefungslogik, siehe
project_zai_gegenpruefungslogik.md): `zai_gegenpruefung_urteil`/
`zai_gegenpruefung_kurzbegruendung` zu `_HEBEL_SIGNAL_SPALTEN` ergaenzt
(echte persistente Spalten, anders als der transiente Deribit-Fakt) plus
neue Aggregat-Sektion `zai_gegenpruefung_verlauf` (siehe
_zai_gegenpruefung_verlauf() unten) fuer dieselbe Korrelations-Frage wie
beim Deribit-Cross-Check: haelt sich das Urteil ('konsistent'/
'widerspruch') mit dem tatsaechlichen Signal-Ausgang?

Nachtrag (2026-07-28, Abschnitt 6 Fakten-Entscheidungsmappe - Nutzer-Hinweis
"nicht vergessen das Analyse-Skript zu adaptieren"): drei neue Fakten seit dem
letzten Update dieses Skripts nachgezogen.
- `vix_wert`/`dollar_index_wert`/`dollar_index_trend` fehlten in
  `get_last_known_regime_status()` (agent/krypto/regime.py) selbst - beide
  laenger als Fakt in allen 6 Analyst-Prompts verdrahtet, aber nie in diesen
  kuratierten Status-Export aufgenommen (den GUI-Tab/Remote-Seite/dieses
  Skript alle gemeinsam nutzen). VIX war dabei ein ECHTER Alt-Fund (seit
  2026-07-18 verdrahtet, nie hier sichtbar), Dollar-Index ist der neue Fakt
  von heute - beide zusammen ergaenzt, um keine zweite Luecke zu hinterlassen.
- `squeeze_divergenz`/`funding_rate_perzentil` (heutige OI-Squeeze-Divergenz +
  Funding-Rate-Perzentil, Krypto Spot+Hebel) stecken wie beim Deribit-Cross-
  Check NUR transient in `facts_json` (unter `antizyklisch`) - neue Sektion
  `oi_fakten_verlauf` (siehe _oi_fakten_verlauf() unten), gezielter Parse nur
  dieser beiden Teilwerte aus BEIDEN Tabellen (signals + hebel_signals, da das
  Feature fuer Spot UND Hebel gebaut wurde), damit spaeter geprueft werden
  kann, ob die Label-Verteilung plausibel ist und das Perzentil ueberhaupt
  Werte liefert (haengt an einer Mindestpunktzahl, siehe MIN_FUNDING_
  PERZENTIL_PUNKTE in indicators/calculations.py - koennte am frisch
  deployten Notebook noch zu wenig Historie haben).

Nachtrag (2026-07-29, Export-Luecke bei der R-5.10-Analyse-Session gefunden,
siehe project_r510_konfidenz_veto_analyse_29_07.md): `compute_provider_
performance()`/`compute_veto_shadow_performance()`/`compute_gesamt_
signalqualitaet()`/`compute_konfidenz_kalibrierung()`/`compute_zai_richtung_
performance()`/`compute_zai_richtung_performance_schatten()`/`compute_
provider_sendezaehler()` wurden bisher OHNE das optionale `watchlist`-Argument
aufgerufen - dadurch landeten alle Spot-family-Signale (Krypto/Aktien/
Rohstoffe/ETF) in einem einzigen "spot"-Topf, waehrend die Live-App-Remote-
Seite (`remote/status.py`) dieselben Funktionen laengst MIT `watchlist`
aufruft und dadurch nach `asset.assetklasse` aufschluesselt (siehe
`SPOT_ASSETKLASSEN` in `remote/server.py`). Folge: bei einer Muster-Analyse
aus diesem Export war nicht unterscheidbar, ob ein Befund krypto-spezifisch
war oder auch Aktien/Rohstoffe/ETF betraf. Jetzt behoben - `watchlist =
config_module.get_watchlist()` wird einmalig geladen und an alle sieben
Aufrufe durchgereicht, identisch zum bereits etablierten Muster in
remote/status.py. Reiner Lesezugriff auf config.yaml, kein Schreibzugriff,
keine Verhaltensaenderung an der Produktions-App selbst.

Nachtrag (2026-07-30, Marktscan-Schwellen-Kalibrierung): neue Sektion
`rohdaten_fuer_backtest.marktscan_alle_kandidaten` - ALLE Einstufungen
(kein_treffer/watchlist_wuerdig/kaufkandidat), nicht nur kaufkandidat wie
`marktscan_kaufkandidaten` (dessen Filter/Spaltenauswahl bewusst unveraendert
blieb, da backtest_budget_allocator_sla.py exakt davon abhaengt). Grundlage
fuer eine Score-Schwellen-Kalibrierung (aktuell 70/50, VORLAEUFIG) gegen
Forward-Kursverlauf, den ein separates Desktop-seitiges Skript per
CoinGecko-Historie (get_market_chart) fuer eine gezielte Stichprobe nachtraegt
- unabhaengig vom Notebook-Kontingent, da eigene IP/Session.

Aufruf am Notebook: python extract_notebook_diagnose.py [SYMBOL] [LOG_STUNDEN]
  (SYMBOL optional, Default LINK, fuer den Tiefenanalyse-Teil;
   LOG_STUNDEN optional, Default 72, Zeitfenster fuer den Log-Auszug)
Schreibt nach K:/My Drive/Claude_Austauschordner/Notebook_Analysedaten/
"""
import dataclasses
import json
import os
import sqlite3
import re
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config as config_module
import database.db as db
from agent.krypto.backward_tracking import (
    compute_crv_breakeven_baender,
    compute_gesamt_signalqualitaet,
    compute_konfidenz_kalibrierung,
    compute_provider_performance,
    compute_provider_sendezaehler,
    compute_selbst_halten_performance,
    compute_ausstiegs_empfehlungen,
    compute_richtungsverteilung,
    compute_systemguete,
    compute_selbst_halten_performance_nach_grund,
    compute_veto_shadow_performance,
    compute_veto_shadow_performance_nach_grund,
    compute_zai_richtung_performance,
    compute_zai_richtung_performance_schatten,
    lade_kursreihen,
    spot_symbole_je_tier,
)
from agent.krypto.regime import get_last_known_regime_status
from agent.portfolio_historie import pruefe_z3

DEEP_DIVE_SYMBOL = sys.argv[1] if len(sys.argv) > 1 else "LINK"
LOG_FENSTER_STUNDEN = int(sys.argv[2]) if len(sys.argv) > 2 else 72
# Gate-Veto-Auswertung (2026-07-28-Fund, siehe _gate_veto_analyse() Docstring):
# eigenes, kuerzeres Fenster als LOG_FENSTER_STUNDEN - signals/hebel_signals werden
# komplett all-time geladen (kein Datumsfilter), ein 7-Tage-Fenster reicht um aktuelle
# von historischer (laengst gefixter) Veto-Haeufung zu trennen.
GATE_VETO_FENSTER_TAGE = 7


def _google_drive_wurzel() -> Path:
    """Der Google-Drive-Laufwerksbuchstabe ist NICHT geraeteuebergreifend
    gleich (2026-07-17, Notebook-Fund: Desktop hat 'My Drive' unter K:,
    Notebook unter G:) - deshalb hier automatisch die erste passende
    Laufwerksbuchstabe-Kandidatin pruefen statt einen Buchstaben
    hartzucodieren. Sucht beide englischen ('My Drive') und deutschen ('Meine Ablage') Namen."""
    for buchstabe in ("G", "K", "H", "E", "F"):
        for ordnername in ("My Drive", "Meine Ablage"):
            kandidat = Path(f"{buchstabe}:/{ordnername}")
            if kandidat.exists():
                return kandidat
    raise FileNotFoundError(
        "Kein 'My Drive'/'Meine Ablage'-Ordner unter G:/K:/H:/E:/F: gefunden - "
        "bitte den tatsaechlichen Laufwerksbuchstaben in ZIEL_ORDNER unten manuell eintragen."
    )


# UEBERSCHREIB-SCHUTZ FUER TESTLAEUFE (2026-08-07).
#
# ANLASS: beim Verifizieren einer Export-Erweiterung wurde `_google_drive_wurzel()`
# umgelenkt - wirkungslos, weil ZIEL_ORDNER eine MODUL-KONSTANTE ist, die schon
# beim Import feststeht. Der Testlauf hat damit den echten
# notebook_diagnose.json im Austauschordner ueberschrieben.
#
# Deshalb ein Ausgang, der VOR der Konstanten wirkt: mit gesetztem
# TIT_EXPORT_ZIEL kann ein Testlauf den Austauschordner gar nicht mehr
# erreichen. Eine Naht schlaegt eine Absichtserklaerung.
_ZIEL_UEBERSCHREIBUNG = os.environ.get("TIT_EXPORT_ZIEL")

ZIEL_ORDNER = (
    Path(_ZIEL_UEBERSCHREIBUNG) / "Notebook_Analysedaten"
    if _ZIEL_UEBERSCHREIBUNG
    else _google_drive_wurzel() / "Claude_Austauschordner" / "Notebook_Analysedaten"
)

# Bewusst schlanke Spaltenauswahl fuer signals/hebel_signals - die langen
# facts_json/*_raw_response-Felder sind redundant zu den strukturierten
# Feldern und blaehen die Datei unnoetig auf.
#
# Nachtrag (2026-07-18, Nutzer-Wunsch "pruef ob die Signale alle gewuenschten
# und erforderlichen Inhalte haben"): Inhalts-Vollstaendigkeits-Felder ergaenzt
# (Top-5-Gruende, Key Risks, Forecast Bull/Base/Bear, Halte-Kriterium,
# Gegenargument) - fehlten bisher komplett in dieser Spaltenauswahl, obwohl
# das genau die Felder sind, die Regelwerksmanual Kap. 6/7 als Pflichtinhalt
# jedes Signals vorschreiben.
_VOLLSTAENDIGKEITS_SPALTEN = (
    "top_grund_1_kategorie, top_grund_1_text, top_grund_2_kategorie, top_grund_2_text, "
    "top_grund_3_kategorie, top_grund_3_text, top_grund_4_kategorie, top_grund_4_text, "
    "top_grund_5_kategorie, top_grund_5_text, key_risks_text, "
    "forecast_bull_text, forecast_bull_prob_pct, forecast_base_text, forecast_base_prob_pct, "
    "forecast_bear_text, forecast_bear_prob_pct, "
    "halte_kriterium_bucket, halte_kriterium_bedingung_text, halte_kriterium_reasoning, "
    "halte_kriterium_ziel_preis_usd, halte_kriterium_ziel_preis_eur, halte_kriterium_ziel_datum, "
    "gegenargument, risikofaktoren_json, "
    # 2026-07-25 (Signal-Fazit / eigene_einschaetzung, siehe
    # project_signal_fazit_umsetzung.md): fehlte hier, obwohl es exakt wie
    # gegenargument/risikofaktoren_json Pflicht-Inhalt jedes Signals ist -
    # deckt ueber die geteilte signals-Tabelle automatisch auch Aktien/
    # Rohstoffe/Themen-ETF/Hedge mit ab, nicht nur Krypto Spot/Hebel.
    #
    # Beobachtungspunkt (2026-08-01, siehe Basisinfos/Test_und_
    # Verifikationsmethodik.md Abschnitt 2.9): fazit_folgen ist bei echten
    # Trade-Empfehlungen (ERÖFFNEN/KAUFEN) praktisch IMMER "mit_vorbehalt"
    # (Hebel: 0 von 572 je "ja"), "ja"/"nein" treten fast nur bei HALTEN auf.
    # Ein Backtest (Fazit-Kategorie vs. tatsaechliches Outcome) ist erst
    # moeglich, sobald selbst_halten_outcome_status (siehe unten) erste
    # aufgeloeste Faelle zeigt - bisher (Stand 01.08.) durchgehend None/
    # nicht_anwendbar fuer alle "ja"/"nein"-Faelle.
    "fazit_folgen, fazit_kurzfazit, fazit_konsistenz_hinweis"
)
_HEBEL_SIGNAL_SPALTEN = (
    "id, symbol, created_at, richtung, action, hebel_vorschlag, hebel_final, "
    "hebel_korrektur_hinweis, trade_thesis_typ, trigger_zweig, trigger_score, "
    "confidence_pct, short_reasoning, entry_eur_von, entry_eur_bis, "
    "stop_loss_eur_von, stop_loss_eur_bis, take_profit_eur_von, take_profit_eur_bis, "
    # USD-Zonen zusaetzlich zu EUR (2026-08-02): das Backward-Tracking rechnet
    # intern in USD. Ohne diese Felder laesst sich eine Auswertung am Desktop
    # nicht bitgleich zur Produktivlogik nachrechnen - nur naeherungsweise in
    # EUR, was ueber die Haltedauer um die Wechselkursbewegung abweicht.
    "entry_usd_von, entry_usd_bis, stop_loss_usd_von, stop_loss_usd_bis, "
    "take_profit_usd_von, take_profit_usd_bis, "
    "liquidationspreis_geschaetzt_usd, eigenkapitalbedarf_usd, eigenkapitalbedarf_eur, "
    "eigenkapital_deckel_hinweis, "
    "hebel_senkung_eigenkapital_nachschuss_eur, ausfuehrbarkeit_hinweis, "
    "regime, regime_source, "
    "gate_passed, gate_reason, risk_veto, risk_veto_reason, llm_model, "
    "outcome_status, outcome_geprueft_am, outcome_entschieden_am, "
    "outcome_realisiertes_crv, outcome_datenquelle, "
    # Mindestziel/MFE-Tracking (2026-07-27, siehe agent/krypto/backward_
    # tracking.py::mindestziel_preis()/check_hebel_signal_outcome()) - erste
    # zwei stehen sofort bei Erstellung fest, letzte zwei erst nachtraeglich
    # per Backward-Tracking.
    "mindestziel_usd, mindestziel_eur, mindestziel_zeitraum_tage_geschaetzt, "
    "outcome_max_realisiertes_crv, outcome_mindestziel_erreicht_am, "
    # Veto-Schatten-Tracking (2026-07-28, siehe database/db.py::_HEBEL_SIGNAL_
    # VETO_SHADOW_NEW_COLUMNS-Docstring) - Ergebnis der vetoten (action=HALTEN
    # trotz LLM-Vorschlag ERÖFFNEN/NACHKAUFEN) hypothetischen Trades.
    "veto_outcome_status, veto_outcome_geprueft_am, veto_outcome_entschieden_am, "
    "veto_outcome_realisiertes_crv, veto_outcome_max_realisiertes_crv, "
    "veto_outcome_mindestziel_erreicht_am, "
    # Selbst-gewaehltes-HALTEN-Schatten-Tracking (2026-07-31, siehe
    # database/db.py::_HEBEL_SIGNAL_SELBST_HALTEN_NEW_COLUMNS-Docstring) -
    # Gegenfall zum Veto-Schatten oben: kein Gate/Veto, das LLM hat sich
    # selbst gegen einen Trade entschieden, aber trotzdem eine hypothetische
    # Zone angegeben. original_action (selber Tag, Fund 2 der Kontrapruefung,
    # siehe Basisinfos/Regelwerksmanual.md-Nachtrag) urspruenglich beim Fix
    # selbst vergessen - haette ohne Export nie sichtbar verifiziert werden
    # koennen.
    "ist_reines_llm_halten, original_action, "
    "selbst_halten_outcome_status, selbst_halten_outcome_geprueft_am, "
    "selbst_halten_outcome_entschieden_am, selbst_halten_outcome_realisiertes_crv, "
    "selbst_halten_outcome_max_realisiertes_crv, selbst_halten_outcome_mindestziel_erreicht_am, "
    "kontrathese_zu_position, kontrathese_llm_richtung, "
    "zai_gegenpruefung_urteil, zai_gegenpruefung_kurzbegruendung, "
    "zai_eigene_richtung, zai_uebereinstimmung, zai_richtung_kurzbegruendung, "
    # ATR-relativ_prozent bei Signal-Erstellung (2026-07-31, siehe database/
    # models.py::HebelSignal.atr_relativ_prozent_bei_signal-Docstring) -
    # Messstandard fuer den kuenftigen TP-ATR-Backtest der Regel-6-Erweiterung,
    # macht die bisherige retroaktive CoinGecko-OHLC-Rekonstruktion (siehe
    # project_enge_stop_loss_backtest_und_massnahmen.md) fuer neue Signale
    # ueberfluessig. Nur Hebel (Regel 6 existiert nur dort).
    "atr_relativ_prozent_bei_signal, "
    # Angefragte Richtung (2026-07-31, siehe database/models.py::HebelSignal.
    # angefragte_richtung-Docstring) - Cooldown-Umgehungs-Bugfix (echter
    # VIRTUAL-Fund): fuer Diagnose-Zwecke sichtbar machen, ob/wo `richtung`
    # (LLM-eigene Antwort) und `angefragte_richtung` (Kandidat/Screening)
    # auseinanderlaufen.
    "angefragte_richtung, "
    + _VOLLSTAENDIGKEITS_SPALTEN
    # HIER STAND EIN FEHLVERSUCH (2026-08-07) - bewusst als Warnung dokumentiert.
    # Der Plan war, `umgesetzt, umgesetzt_am, umgesetzt_menge,
    # umgesetzt_preis_usd` zu ergaenzen, weil der Befolgungsgrad fuer Hebel
    # nicht exportiert wurde. Beim Test gegen eine DB-Kopie: "no such column:
    # umgesetzt".
    #
    # DIE SPALTEN EXISTIEREN AUF `hebel_signals` GAR NICHT. Die
    # Umsetzungs-Rueckmeldung wurde 2026-07-09 nur fuer `signals` (Spot) gebaut
    # - Tabelle, Migration und die drei Schreibstellen. Fuer Hebel gibt es
    # weder Spalte noch Schreibpfad.
    #
    # Das ist also keine Export-Luecke, sondern eine FEHLENDE FUNKTION, und sie
    # gehoert entsprechend geplant (Migration + Schreibpfad + UI), nicht
    # nebenbei in eine Spaltenliste geschrieben. Siehe Zwischenstand
    # Abschnitt 8b, Punkt B1.
)
_SPOT_SIGNAL_SPALTEN = (
    "id, symbol, created_at, action, confidence_pct, short_reasoning, "
    "entry_eur_von, entry_eur_bis, stop_loss_eur_von, stop_loss_eur_bis, "
    "take_profit_eur_von, take_profit_eur_bis, "
    # USD-Zonen (2026-08-02, gleiche Begruendung wie bei _HEBEL_SIGNAL_SPALTEN).
    # Spot fuehrt zusaetzlich Einzelwert-Felder ohne _von/_bis - check_signal_
    # outcome() nimmt _von und faellt auf den Einzelwert zurueck, deshalb beide.
    "entry_usd_von, entry_usd_bis, entry_usd, "
    "stop_loss_usd_von, stop_loss_usd_bis, stop_loss_usd, "
    "take_profit_usd_von, take_profit_usd_bis, take_profit_usd, "
    "regime, gate_passed, gate_reason, "
    "risk_veto, risk_veto_reason, cash_veto, cash_veto_reason, groq_model, "
    "outcome_status, outcome_geprueft_am, outcome_entschieden_am, "
    "outcome_realisiertes_crv, outcome_datenquelle, "
    "mindestziel_usd, mindestziel_eur, mindestziel_zeitraum_tage_geschaetzt, "
    "outcome_max_realisiertes_crv, outcome_mindestziel_erreicht_am, "
    # 2026-08-02: die vorgeschlagene Positionsgroesse wurde zwar seit jeher
    # persistiert (signals-Tabelle, alle 5 Spot-family-Pipelines befuellen sie),
    # aber nie exportiert. Dadurch war die Nutzer-Beobachtung "die Betraege sind
    # so hoch, dass nur EIN Trade moeglich waere" am Export nicht nachpruefbar -
    # und die neuen Deckel RM-1 exakt / RM-1d waeren es ebenso wenig. Die `note`
    # traegt die Begruendung, welcher Deckel gebunden hat.
    # NUR hier, nicht bei Hebel: `hebel_signals` hat keine position_size-Spalten,
    # dort ist `eigenkapitalbedarf_usd` die entsprechende Groesse.
    "position_size_usd, position_size_eur, position_size_note, "
    # Veto-Schatten-Tracking (2026-07-28), siehe _HEBEL_SIGNAL_SPALTEN-Kommentar
    # oben - identisches Feld-Set, hier fuer die Spot-family (signals-Tabelle).
    "veto_outcome_status, veto_outcome_geprueft_am, veto_outcome_entschieden_am, "
    "veto_outcome_realisiertes_crv, veto_outcome_max_realisiertes_crv, "
    "veto_outcome_mindestziel_erreicht_am, "
    # Selbst-gewaehltes-HALTEN-Schatten-Tracking (2026-07-31), identisches
    # Feld-Set wie _HEBEL_SIGNAL_SPALTEN oben. original_action ebenfalls
    # nachgezogen (siehe Kommentar dort - beim urspruenglichen Fix vergessen).
    "ist_reines_llm_halten, original_action, "
    "selbst_halten_outcome_status, selbst_halten_outcome_geprueft_am, "
    "selbst_halten_outcome_entschieden_am, selbst_halten_outcome_realisiertes_crv, "
    "selbst_halten_outcome_max_realisiertes_crv, selbst_halten_outcome_mindestziel_erreicht_am, "
    "tranchen_json, cash_reserve_ziel_btc_usd, cash_reserve_ziel_eth_usd, "
    "cash_reserve_ziel_gesamt_usd, cash_reserve_ziel_begruendung, "
    "umgesetzt, umgesetzt_am, umgesetzt_menge, umgesetzt_preis_usd, "
    # Z.ai-Konsistenz-Check (2026-07-27, Ausweitung von hebel_signals auf
    # signals - siehe agent/krypto/gegenpruefung.py Modul-Docstring
    # "Erweiterung"), seit 2026-07-27 um die vollen 5 Z.ai-Spalten ergaenzt
    # (database/db.py::update_signal_zai_gegenpruefung(),
    # database/models.py::Signal-Dataclass) - identisches Feld-Set wie
    # _HEBEL_SIGNAL_SPALTEN.
    "zai_gegenpruefung_urteil, zai_gegenpruefung_kurzbegruendung, "
    "zai_eigene_richtung, zai_uebereinstimmung, zai_richtung_kurzbegruendung, "
    + _VOLLSTAENDIGKEITS_SPALTEN
)


def row_to_dict(row) -> dict:
    return {k: row[k] for k in row.keys()}


def haeufigkeit(rows, feld: str) -> dict:
    zaehler = Counter(r[feld] for r in rows if r[feld])
    return dict(zaehler.most_common())


def _gate_veto_analyse(rows: list[dict], feld: str, seit_tagen: int | None = None) -> dict:
    """Erweiterte Gate-/Risk-Veto-Auswertung (2026-07-28-Fund): haeufigkeit() aggregiert
    ausschliesslich global und ALL-TIME (signals/hebel_signals werden ohne Datumsfilter
    geladen) - das verschleiert, ob ein Veto-Grund noch AKTUELL auftritt oder nur ein
    laengst gefixter historischer Vorfall ist. Konkreter Live-Fund: "Historie veraltet"
    machte all-time 84% aller Spot-Gate-Vetos aus, stammte aber zu 321 von 380 Faellen
    aus einem einzigen Tag (2026-07-23, bereits mit dem Staleness-Watchdog-Fix
    behoben) - ohne Symbol-/Zeitaufschluesselung liest sich das faelschlich wie ein
    andauerndes Problem. Liefert zusaetzlich zur globalen Haeufigkeit (1) eine
    Pro-Symbol-Aufschluesselung und (2) optional ein Zeitfenster (seit_tagen), um
    aktuelle von historischer Haeufung zu trennen."""
    gefiltert = rows
    if seit_tagen is not None:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=seit_tagen)).isoformat()
        gefiltert = [r for r in rows if (r.get("created_at") or "") >= cutoff]
    gesamt = Counter(r[feld] for r in gefiltert if r.get(feld))
    je_symbol: dict[str, Counter] = {}
    for r in gefiltert:
        symbol, wert = r.get("symbol"), r.get(feld)
        if symbol and wert:
            je_symbol.setdefault(symbol, Counter())[wert] += 1
    return {
        "zeitfenster_tage": seit_tagen,
        "anzahl_zeilen_im_fenster": len(gefiltert),
        "haeufigkeit_gesamt": dict(gesamt.most_common()),
        "je_symbol": {
            symbol: dict(c.most_common())
            for symbol, c in sorted(je_symbol.items(), key=lambda kv: -sum(kv[1].values()))
        },
    }


def _marktscan_discovery_llm_delta(conn) -> dict:
    """Neu (2026-07-21, Nutzer-Fund): Delta zwischen Kandidaten-Discovery
    (discovered_at, deterministischer Marktscan-Lauf) und tatsaechlicher
    LLM-Begruendung (groq_generiert_am, Tier-2 im Budget-Allocator) - Beispiel
    des Nutzers war 16:00 Uhr Discovery vs. 19:30 Uhr Signal, 3,5h Delta.
    Siehe Memory project_delta_berechnung_llm_abfrage_timing.md. Rein
    deskriptiv (Min/Max/Median/Durchschnitt je Symbol) - keine Bewertung
    hier, das passiert gemeinsam anhand dieser Rohdaten."""
    rows = conn.execute(
        "SELECT symbol, discovered_at, groq_generiert_am FROM marktscan_candidates "
        "WHERE groq_generiert_am IS NOT NULL ORDER BY discovered_at ASC"
    ).fetchall()
    eintraege = []
    deltas_minuten = []
    for r in rows:
        try:
            entdeckt = datetime.fromisoformat(r["discovered_at"])
            generiert = datetime.fromisoformat(r["groq_generiert_am"])
        except ValueError:
            continue
        delta_min = (generiert - entdeckt).total_seconds() / 60
        deltas_minuten.append(delta_min)
        eintraege.append({
            "symbol": r["symbol"], "discovered_at": r["discovered_at"],
            "groq_generiert_am": r["groq_generiert_am"], "delta_minuten": round(delta_min, 1),
        })
    deltas_sortiert = sorted(deltas_minuten)
    n = len(deltas_sortiert)
    statistik = {
        "anzahl": n,
        "min_minuten": round(deltas_sortiert[0], 1) if n else None,
        "max_minuten": round(deltas_sortiert[-1], 1) if n else None,
        "median_minuten": round(deltas_sortiert[n // 2], 1) if n else None,
        "durchschnitt_minuten": round(sum(deltas_sortiert) / n, 1) if n else None,
    }
    return {"statistik": statistik, "eintraege": eintraege}


def _hebel_erstmalige_erkennung_delta(conn) -> dict:
    """Neu (2026-07-21, Nutzer-Fund ETH LONG): anders als bei Marktscan-
    Kandidaten (ein Discovery-Lauf, danach fix) wird bei hebel_triggers JEDEN
    15-Min-Screening-Tick eine NEUE Zeile eingefuegt, solange ein Symbol/
    Richtung-Paar weiter als Kandidat qualifiziert (kein Upsert, siehe
    db.py::insert_hebel_trigger()-Docstring). Das per hebel_trigger_id
    verknuepfte 'gewaehlte' Trigger-Objekt eines Signals ist deshalb IMMER
    der neueste Tick (get_pending_hebel_kandidaten() waehlt MAX(screened_at))
    - das Delta Trigger->Signal ist dadurch strukturell fast immer klein und
    verschleiert, seit wann das Setup TATSAECHLICH schon bestand.
    Nutzer-Beispiel: ETH LONG-Signal heute 09:58 berechnet (Entry ~1.590 EUR),
    Kurs stand aber schon gestern in aehnlicher Hoehe - "der Einstieg haette
    gestern passieren muessen". Berechnet deshalb stattdessen: fuer jedes
    Symbol/Richtung-Paar mit einem echten Signal (hebel_trigger_id gesetzt),
    den FRUEHESTEN screened_at unter allen ist_kandidat=1-Zeilen seit dem
    vorherigen Signal fuer dasselbe Paar (oder max. 14 Tage zurueck, falls
    keins existiert) - das zeigt, wie lange die aktuelle Kandidatur schon
    bestand, bevor sie tatsaechlich bewertet wurde."""
    signale = conn.execute(
        "SELECT id, symbol, richtung, created_at, hebel_trigger_id FROM hebel_signals "
        "WHERE hebel_trigger_id IS NOT NULL ORDER BY created_at ASC"
    ).fetchall()
    trigger_rows = conn.execute(
        "SELECT symbol, richtung, screened_at FROM hebel_triggers "
        "WHERE ist_kandidat = 1 ORDER BY screened_at ASC"
    ).fetchall()

    trigger_nach_paar: dict[tuple[str, str], list[str]] = {}
    for t in trigger_rows:
        trigger_nach_paar.setdefault((t["symbol"], t["richtung"]), []).append(t["screened_at"])

    vorheriges_signal_am: dict[tuple[str, str], str] = {}
    eintraege = []
    deltas_stunden = []
    for s in signale:
        paar = (s["symbol"], s["richtung"])
        try:
            signal_zeit = datetime.fromisoformat(s["created_at"])
        except ValueError:
            continue
        untere_grenze = vorheriges_signal_am.get(paar)
        untere_grenze_dt = (
            datetime.fromisoformat(untere_grenze) if untere_grenze
            else signal_zeit - timedelta(days=14)
        )
        kandidaten_im_fenster = [
            zeit for zeit in trigger_nach_paar.get(paar, [])
            if untere_grenze_dt < datetime.fromisoformat(zeit) <= signal_zeit
        ]
        if kandidaten_im_fenster:
            erstmalig = min(kandidaten_im_fenster)
            delta_std = (signal_zeit - datetime.fromisoformat(erstmalig)).total_seconds() / 3600
            deltas_stunden.append(delta_std)
            eintraege.append({
                "symbol": s["symbol"], "richtung": s["richtung"],
                "signal_created_at": s["created_at"], "erstmalig_erkannt_am": erstmalig,
                "delta_stunden": round(delta_std, 1),
            })
        vorheriges_signal_am[paar] = s["created_at"]

    deltas_sortiert = sorted(deltas_stunden)
    n = len(deltas_sortiert)
    statistik = {
        "anzahl": n,
        "min_stunden": round(deltas_sortiert[0], 1) if n else None,
        "max_stunden": round(deltas_sortiert[-1], 1) if n else None,
        "median_stunden": round(deltas_sortiert[n // 2], 1) if n else None,
        "durchschnitt_stunden": round(sum(deltas_sortiert) / n, 1) if n else None,
    }
    return {"statistik": statistik, "eintraege": eintraege}


def _rohdaten_fuer_backtest(conn) -> dict:
    """Neu (2026-07-21, Nutzer-Vorgabe "umfangreich testen vor finaler
    Umsetzung"): schlanker Rohdaten-Export ALLER (nicht nur der zuletzt
    ausgewaehlten) Kandidaten-Zeilen - Grundlage fuer
    backtest_budget_allocator_sla.py, das den neuen SLA-basierten
    Auswahlalgorithmus gegen die echte Historie nachspielt, BEVOR
    Produktivcode geaendert wird (siehe Plan-Datei). Die bisherigen Delta-
    Sektionen oben liefern nur aggregierte Werte/die jeweils gewaehlte
    Kandidatenzeile - fuer eine echte Zyklus-fuer-Zyklus-Simulation werden
    ALLE ist_kandidat=1-/kaufkandidat-Zeilen gebraucht, nicht nur die am
    Ende verwendete. Bewusst schlanke Spaltenauswahl (keine JSON-Blob-
    Spalten wie score_details_json) - das Backtest-Skript baut daraus eine
    In-Memory-SQLite-DB und ruft dieselben database/db.py-Funktionen auf
    wie der Live-Allocator (db.get_hebel_wartezeit_stunden_je_paar() etc.,
    ueber deren as_of-Parameter)."""
    # Phase 0.1 (2026-08-04): Score-KOMPONENTEN mitexportieren.
    #
    # WOFUER. Der Screening-Score diskriminiert nicht (Event-Study 04.08.,
    # nicht-monoton) und korreliert mit dem Ergebnis sogar -0,200, also
    # invers. Ob das fuer den Gesamtscore gilt oder nur fuer einzelne seiner
    # vier Komponenten (oi_aenderung, kursaenderung, funding_rate, konfluenz),
    # laesst sich ohne `score_details_json` nicht sagen - die Frage stand seit
    # dem 04.08. im Plan und wurde zweimal zurueckgestellt.
    #
    # ZWEI GETRENNTE SCHLUESSEL, bewusst keine Umdeutung des bestehenden.
    # `hebel_triggers_kandidaten` bleibt exakt wie bisher (nur ist_kandidat=1,
    # gleiche Spalten) - backtest_budget_allocator_sla.py simuliert damit den
    # Allocator und SETZT VORAUS, dass es Kandidaten sind. Denselben Schluessel
    # still mit anderer Bedeutung zu fuellen waere genau die stille
    # Degradierung aus Methodik 2.5.8: der Backtest liefe weiter und waere
    # falsch.
    hebel_triggers_kandidaten = [
        row_to_dict(r) for r in conn.execute(
            "SELECT id, symbol, richtung, screened_at, score_gesamt, status "
            "FROM hebel_triggers WHERE ist_kandidat = 1 ORDER BY screened_at ASC"
        ).fetchall()
    ]
    # NEU und OHNE Schwellenfilter: nur hierauf laesst sich die Frage "trennt
    # der Score ueberhaupt?" beantworten. Wer nur die Ueberschwelligen
    # betrachtet, misst in einem beschnittenen Wertebereich - derselbe Fehler
    # hat am 02.08. den CRV-Gate-Befund entwertet (Survivorship) und am 04.08.
    # die Volatilitaetsauswertung beinahe.
    #
    # Mit dem Ergebnis verknuepfbar ueber hebel_signals.hebel_trigger_id;
    # ohne diese Verbindung waere der Export Selbstzweck.
    # Z-3 / RM-7 Drawdown-Notbremse (2026-08-05).
    #
    # ANLASS: die Notbremse hat am 05.08. um 06:30 zum ERSTEN MAL scharf
    # gemeldet - "Rueckschlag 16,7 % >= Schwelle 15 %", E-Mail an den Nutzer
    # raus. Der Mechanismus hat funktioniert, aber die erste Frage nach so
    # einem Alarm - WOHER kommt der Rueckschlag, und stimmt die Zahl? - liess
    # sich mit dem Export nicht beantworten. Weder der ausloesende Wert noch
    # die zugrundeliegende Reihe waren darin enthalten.
    #
    # Exportiert wird deshalb beides: das Ergebnis von pruefe_z3() UND die
    # Wertreihe, auf der es beruht. Nur mit der Reihe laesst sich der Alarm
    # NACHRECHNEN statt ihm zu glauben - und das ist bei einer Groesse, die
    # eine Notbremse ausloest, keine Kuer.
    #
    # `index_wert` ist die maessgebliche Spalte, nicht `wert_eur`: Z-3 rechnet
    # mengenkonstant, sonst loeste ein grosser Verkauf die Bremse aus und ein
    # grosser Zukauf verdeckte einen echten Einbruch.
    # AUSFALLSICHER: `portfolio_wert_historie` wurde erst am 04.08. angelegt.
    # Ein Bestand ohne die Tabelle (aeltere Kopie, frische Installation) haette
    # den GESAMTEN Diagnoselauf abgebrochen - beim Rauchtest gegen die lokale
    # Entwicklungskopie genau so passiert. Ein fehlender Nebenblock darf einen
    # Export nicht toeten.
    z3_status = None
    portfolio_wert_historie = []
    bewertungs_diagnose = {}
    hedge_wirksamkeit = {}
    try:
        z3_status = pruefe_z3(
            conn,
            schwelle_prozent=config_module.load_config()["ziele"]["max_drawdown_prozent"],
        )
        portfolio_wert_historie = [
            row_to_dict(r) for r in db.get_portfolio_wert_historie(conn)
        ]
        # WARUM DIE BEWERTUNG SO AUSSIEHT, WIE SIE AUSSIEHT (2026-08-06).
        # z3_status liefert nur das Ergebnis. Am 06.08. stand daneben
        # "19 Symbole ohne Kurs" - und niemand konnte aus dem Export sagen,
        # WELCHE 19 und WARUM. Ursache waren zwei Defekte gleichzeitig
        # (FX-Ableitung verworfen + Futures-Reihe unter dem ETC-Symbol).
        # Ohne diese Diagnose ist die Verifikation der Behebung nicht moeglich.
        bewertungs_diagnose = _bewertungs_diagnose(conn)
        # HEDGE-WIRKSAMKEIT (2026-08-07, W1): das zustaendige Erfolgsmass fuer
        # Absicherungen. SQN/Expectancy beantworten fuer diese Klasse die
        # falsche Frage - siehe compute_hedge_wirksamkeit().
        hedge_wirksamkeit = _hedge_wirksamkeit(conn)
    except sqlite3.OperationalError as exc:
        # Bewusst als Wert im Export, nicht nur im Log: wer die Datei liest,
        # soll den Unterschied zwischen "kein Drawdown" und "nicht gemessen"
        # sehen (stille Degradierung, Methodik 2.5.8).
        z3_status = {"nicht_verfuegbar": str(exc)}
        bewertungs_diagnose = {"nicht_verfuegbar": str(exc)}
        hedge_wirksamkeit = {"nicht_verfuegbar": str(exc)}
        print(f"  HINWEIS: Z-3-Status nicht ermittelbar ({exc})")

    # Makro- und OI-Historie fuer den LLM1-Backtest (2026-08-04).
    #
    # WOFUER. Der historische Backtest (backtest_llm1_historisch.py) baut
    # Faktensaetze aus der Kurshistorie. Was fehlt, sind genau die
    # Gegenindikatoren, die im Betrieb das HALTEN ausloesen: Funding-Rate,
    # Open Interest, Fear&Greed, Long-Konten-Anteil. Ohne sie eroeffnete das
    # Modell im ersten Lauf in 36 von 36 Faellen - im Betrieb sind es 35 %.
    # Beide Tabellen fuehren die Werte taeglich, sie waren nur nie exportiert.
    #
    # REICHWEITE beachten: macro_snapshot beginnt erst im Juli 2026, die
    # Kurshistorie reicht 748 Tage. Der Backtest muss also entscheiden,
    # ob er lange Fenster mit duennen oder kurze mit vollen Fakten will.
    macro_historie = [
        row_to_dict(r) for r in conn.execute(
            "SELECT date, btc_dominance_pct, fear_greed_value, fear_greed_label, "
            "btc_trend_label, regime_reason, zyklus_risiko, liquiditaets_regime, "
            "vix_wert, dollar_index_wert, dollar_index_trend "
            "FROM macro_snapshot ORDER BY date ASC"
        ).fetchall()
    ]
    oi_historie = [
        row_to_dict(r) for r in conn.execute(
            "SELECT symbol, exchange, open_interest, open_interest_usd, "
            "funding_rate, long_account_pct, fetched_at "
            "FROM open_interest_snapshot ORDER BY fetched_at ASC"
        ).fetchall()
    ]
    hebel_triggers_alle = [
        row_to_dict(r) for r in conn.execute(
            "SELECT id, symbol, richtung, screened_at, trigger_zweig, "
            "score_gesamt, score_details_json, oi_change_pct_lookback, "
            "kursaenderung_pct_lookback, funding_rate_aktuell, "
            "long_konten_anteil_prozent, ist_kandidat, status "
            "FROM hebel_triggers ORDER BY screened_at ASC"
        ).fetchall()
    ]
    marktscan_kaufkandidaten = [
        row_to_dict(r) for r in conn.execute(
            "SELECT id, coingecko_id, symbol, discovered_at, score_gesamt, status, groq_generiert_am "
            "FROM marktscan_candidates WHERE einstufung = 'kaufkandidat' ORDER BY discovered_at ASC"
        ).fetchall()
    ]
    # Neu (2026-07-30, Marktscan-Schwellen-Kalibrierung): bewusst eine ZWEITE,
    # eigenstaendige Sektion statt marktscan_kaufkandidaten oben zu erweitern -
    # backtest_budget_allocator_sla.py baut aus marktscan_kaufkandidaten eine
    # In-Memory-Tabelle mit exakt dessen 7 Spalten und erwartet ausschliesslich
    # 'kaufkandidat'-Zeilen (die SLA-Simulation bildet bewusst nur die echte
    # Kaufkandidaten-Warteschlange nach) - ein Aufweichen des Filters oder der
    # Spaltenliste dort haette den bestehenden Backtest stillschweigend
    # verfaelscht. marktscan_alle_kandidaten liefert stattdessen ALLE
    # Einstufungen (kein_treffer/watchlist_wuerdig/kaufkandidat) inkl.
    # price_usd (Kurs zum Entdeckungszeitpunkt) - Grundlage fuer eine
    # Score-Schwellen-Kalibrierung (aktuell score_kaufkandidat_ab=70/
    # score_watchlist_wuerdig_ab=50, laut config.yaml VORLAEUFIG, nie
    # gegen Forward-Performance geprueft).
    # Nachtrag (2026-07-30, Nutzer-Hinweis "ungenutzte Daten, welche uns helfen"):
    # discovery_source/volume_24h_usd/change_24h_pct/signale_momentum_json (enthaelt
    # change_7d_pct + verlaengerungs_malus, siehe score_momentum()) werden pro
    # Kandidat-Zeile bereits seit Beginn gespeichert, waren hier aber nie exportiert -
    # Grundlage fuer die "Reifegrad"-Diskussion (Streak-Laenge/Verlangsamung/
    # Volumen-Trend als Erschoepfungssignal bei rasch gestiegenen Coins).
    # Nachtrag (2026-07-30, Erfolgsmessung Teil 2, siehe agent/krypto/
    # marktscan_backward_tracking.py): outcome_status/outcome_return_pct/
    # outcome_geprueft_am/mindestziel_usd fuer eine spaetere Erfolgsquote-
    # Validierung (analog zur Score-Schwellen-Kalibrierung oben).
    marktscan_alle_kandidaten = [
        row_to_dict(r) for r in conn.execute(
            "SELECT id, coingecko_id, symbol, discovered_at, discovery_source, score_gesamt, "
            "einstufung, price_usd, change_24h_pct, volume_24h_usd, market_cap_usd, "
            "signale_momentum_json, status, outcome_status, outcome_return_pct, "
            "outcome_geprueft_am, mindestziel_usd FROM marktscan_candidates ORDER BY discovered_at ASC"
        ).fetchall()
    ]
    # z3_status wird NICHT hier eingehaengt, sondern von main() auf die
    # oberste Ebene gehoben - ein Statuswert unter "rohdaten_fuer_backtest"
    # findet niemand, der ihn sucht (erster Einbau am 05.08. lag genau so
    # daneben). Die drei HISTORIEN bleiben hier: sie sind tatsaechlich
    # Backtest-Rohdaten.
    return {
        "_z3_status": z3_status,
        "_bewertungs_diagnose": bewertungs_diagnose,
        "_hedge_wirksamkeit": hedge_wirksamkeit,
        "hebel_triggers_kandidaten": hebel_triggers_kandidaten,
        "hebel_triggers_alle": hebel_triggers_alle,
        "portfolio_wert_historie": portfolio_wert_historie,
        "macro_historie": macro_historie,
        "oi_historie": oi_historie,
        "marktscan_kaufkandidaten": marktscan_kaufkandidaten,
        "marktscan_alle_kandidaten": marktscan_alle_kandidaten,
    }


def _hebel_faktensaetze(conn, je_zelle: int = 12, tage: int = 14) -> dict:
    """Echte `facts_json`-Saetze fuer den Regel-28-Test (2026-08-05).

    WOFUER. Am 31.07. kippt das Hebel-Verhalten binnen einer Stunde: vorher
    rund 50 HALTEN und 4 EROEFFNEN am Tag, danach rund 40 EROEFFNEN und 2
    HALTEN, bei 97 % SHORT-Anteil und um 10 Punkte hoeherer Konfidenz. Der
    Markt erklaert das nicht - der Indikatorsatz aus der Produktion zeigt an
    dem Tag keinen Bruch, und bei UNVERAENDERT nicht-bearischer Datenlage
    stieg der SHORT-Anteil von 5,2 % auf 69,9 %. Einzige Prompt-Aenderung im
    Deploy-Fenster davor ist Regel 28 (350918a, 31.07. 04:39 UTC), die
    verlangt, bei selbst gewaehltem HALTEN die Zonen auszufuellen, die man bei
    EROEFFNEN gewaehlt haette.

    WARUM DER HISTORISCHE BACKTEST DAS NICHT KLAEREN KANN: dort liegt die
    EROEFFNEN-Quote in ALLEN Armen bei 94-100 %. Der rekonstruierte
    Faktensatz ist zu duenn, um ueberhaupt ein HALTEN zu erzeugen - genau die
    Achse, um die es geht, ist gesaettigt. Mit den ECHTEN Faktensaetzen
    entfaellt dieses Problem: sie haben im Betrieb nachweislich HALTEN
    erzeugt.

    WARUM NICHT EINFACH IN _HEBEL_SIGNAL_SPALTEN: facts_json ist bewusst aus
    der Spaltenauswahl ausgeschlossen (siehe Kommentar dort) - ein Satz wiegt
    einige Kilobyte, ueber 1500 Signale waere das ein Vielfaches der
    restlichen Datei. Deshalb hier eine GESCHICHTETE Stichprobe statt aller
    Zeilen: je Tag und je action hoechstens `je_zelle` Saetze, und nur im
    Fenster um den Sprung.

    Die Schichtung ist nicht Kosmetik, sondern Voraussetzung des Tests: der
    entscheidende Arm braucht Faktensaetze, bei denen das Modell VOR dem
    31.07. selbst HALTEN gewaehlt hat. Eine unsortierte Stichprobe waere nach
    dem 31.07. fast leer an HALTEN (2 pro Tag) und davor fast leer an
    EROEFFNEN (4 pro Tag) - also genau dort duenn, wo gemessen werden soll.

    NACHTRAG 2026-08-06 - FENSTER ROLLIERT JETZT.
    Bis hierher stand das Fenster fest auf '2026-07-26'..'2026-08-05'. Das war
    fuer den Regel-28-Test richtig und ist es nach seinem Abschluss nicht mehr:
    ein festes Enddatum in der Vergangenheit heisst, dass JEDE kuenftige
    Prompt- oder Fakten-Aenderung in diesem Block unsichtbar bleibt. Genau das
    ist am 06.08. eingetreten - die drei neuen Fakt-Bloecke (kosten,
    ausstiegsregel, systemguete) waren in 0 von 177 Saetzen, und zwar nicht
    weil sie fehlten, sondern weil das Fenster vor ihrem Deploy endete. Die
    Verifikation lief dadurch ins Leere.

    Der R28-Test bleibt reproduzierbar: seine 104 vollstaendigen Antworten
    liegen in `data/regel28_echt_antworten.json`, und das damalige Fenster
    steht oben im Docstring.

    LEHRE, die ueber diese Funktion hinausgeht: ein Analyse-Export, der fuer
    EINE Fragestellung gebaut wurde, verfaellt still. Wer ihn danach zur
    Verifikation benutzt, misst das Fenster statt der Sache."""
    rows = conn.execute(
        "SELECT id, symbol, created_at, action, richtung, confidence_pct, "
        "regime, trigger_zweig, risk_veto_reason, facts_json "
        "FROM hebel_signals "
        "WHERE facts_json IS NOT NULL AND facts_json != '' "
        "  AND date(created_at) >= date('now', ?) "
        "ORDER BY created_at ASC",
        (f"-{int(tage)} days",),
    ).fetchall()

    je_gruppe: dict[tuple, list] = {}
    for r in rows:
        schluessel = (str(r["created_at"])[:10], str(r["action"] or "?"))
        je_gruppe.setdefault(schluessel, []).append(r)

    eintraege = []
    uebersprungen = 0
    for (tag, aktion), gruppe in sorted(je_gruppe.items()):
        # gleichmaessig ueber den Tag ziehen statt der ersten n - sonst
        # bestuende die Stichprobe nur aus dem Nacht-Batch
        schritt = max(1, len(gruppe) // je_zelle)
        gewaehlt = gruppe[::schritt][:je_zelle]
        uebersprungen += len(gruppe) - len(gewaehlt)
        for r in gewaehlt:
            eintraege.append({
                "id": r["id"], "symbol": r["symbol"], "created_at": r["created_at"],
                "action": r["action"], "richtung": r["richtung"],
                "confidence_pct": r["confidence_pct"], "regime": r["regime"],
                "trigger_zweig": r["trigger_zweig"],
                "risk_veto_reason": r["risk_veto_reason"],
                "facts_json": r["facts_json"],
            })

    # Welche Fakt-Bloecke kamen an welchem Tag tatsaechlich beim Modell an?
    # Bewusst ueber ALLE Zeilen des Fensters, nicht nur ueber die Stichprobe -
    # die Frage "ist der neue Fakt im Betrieb angekommen" darf nicht davon
    # abhaengen, ob die Schichtung den betreffenden Satz gezogen hat. Kostet
    # nur Schluesselnamen, kein facts_json.
    #
    # ZWEI EBENEN, NICHT NUR EINE (Nachtrag 2026-08-06, noch am Tag der
    # Einfuehrung): der erste Wurf zaehlte nur Top-Level-Bloecke - und hat
    # damit ausgerechnet den Fall nicht gesehen, der gerade verfolgt wurde.
    # `score_gesamt` liegt VERSCHACHTELT unter `trigger`, seine Entfernung war
    # im Zaehler also unsichtbar und ich haette sie faelschlich als "schon
    # erledigt" gelesen. Unterschluessel laufen als "eltern.kind".
    bloecke_je_tag: dict[str, dict[str, int]] = {}
    for r in rows:
        tag = str(r["created_at"])[:10]
        eimer = bloecke_je_tag.setdefault(tag, {})
        eimer["_faktensaetze"] = eimer.get("_faktensaetze", 0) + 1
        try:
            fakten = json.loads(r["facts_json"])
            for schluessel, wert in fakten.items():
                eimer[schluessel] = eimer.get(schluessel, 0) + 1
                if isinstance(wert, dict):
                    for unter in wert:
                        pfad = f"{schluessel}.{unter}"
                        eimer[pfad] = eimer.get(pfad, 0) + 1
        except Exception:
            eimer["_unlesbar"] = eimer.get("_unlesbar", 0) + 1

    groesse = sum(len(e["facts_json"] or "") for e in eintraege)
    return {
        "hinweis": f"Geschichtete Stichprobe je Tag x action, rollierendes Fenster "
                   f"der letzten {tage} Tage (seit 2026-08-06; davor fest "
                   f"26.07.-05.08. fuer den Regel-28-Test). "
                   f"`bloecke_je_tag` zaehlt ueber ALLE Zeilen des Fensters und "
                   f"beantwortet, ob ein neuer Fakt-Block im Betrieb ankommt.",
        "fenster_tage": tage,
        "je_zelle": je_zelle,
        "anzahl": len(eintraege),
        "nicht_gezogen": uebersprungen,
        "groesse_facts_json_bytes": groesse,
        "belegung": {f"{tag} {aktion}": len(g) for (tag, aktion), g in sorted(je_gruppe.items())},
        "bloecke_je_tag": dict(sorted(bloecke_je_tag.items())),
        "eintraege": eintraege,
    }


def _preishistorie_ueberholte_symbole(conn) -> dict:
    """Neu (2026-07-22, siehe Modul-Docstring-Nachtrag) - Grundlage fuer
    backtest_ueberholt_erkennung.py: liefert die echte Kurshistorie fuer
    genau die Symbole, deren Signal-Historie mindestens einen 'ueberholt_
    durch_neuere_analyse'-Ausgang enthaelt. Der Backtest prueft rueckwirkend,
    ob dieses Signal unter den geplanten neuen Gates (Mindestbeobachtung +
    Zonen-Reaffirmation) weiter offen geblieben waere - und falls ja, ob es
    seither TP/SL erreicht haette."""
    hebel_symbole = {
        r["symbol"] for r in conn.execute(
            "SELECT DISTINCT symbol FROM hebel_signals WHERE outcome_status = 'ueberholt_durch_neuere_analyse'"
        ).fetchall()
    }
    spot_symbole = {
        r["symbol"] for r in conn.execute(
            "SELECT DISTINCT symbol FROM signals WHERE outcome_status = 'ueberholt_durch_neuere_analyse'"
        ).fetchall()
    }
    alle_symbole = sorted(hebel_symbole | spot_symbole)
    preishistorie = {
        symbol: [
            row_to_dict(r) for r in conn.execute(
                "SELECT * FROM price_history_ohlc WHERE symbol = ? ORDER BY date ASC", (symbol,)
            ).fetchall()
        ]
        for symbol in alle_symbole
    }
    return {"symbole": alle_symbole, "preishistorie_je_symbol": preishistorie}


def _preishistorie_signal_symbole(conn, vorlauf_tage: int = 60) -> dict:
    """Neu (2026-08-02, Maßnahme 3 der Dead-Loop-Synthese): OHLC-Reihen fuer
    ALLE Symbole, zu denen es ueberhaupt Signale gibt - nicht nur fuer die
    'ueberholten' wie _preishistorie_ueberholte_symbole().

    Anlass: die rueckwirkende Nachrechnung deterministischer Indikatoren
    (ADX/Choppiness) ueber bereits aufgeloeste Signale scheiterte nicht an
    fehlenden Daten, sondern daran, dass der Export sie nicht mitnahm - von
    32 Hebel-Signal-Symbolen waren nur 18 enthalten, und ausgerechnet die
    aktiven (SOL, NEAR, AVAX, APT, RENDER, SEI, TAO ...) fehlten. Die
    'ueberholt'-Auswahl ist fuer diese Frage zusaetzlich verzerrt: sie
    enthaelt per Konstruktion nur Symbole mit haeufigen Neuanalysen.

    Bewusst zeitlich begrenzt statt voller Historie: ab dem aeltesten Signal
    minus `vorlauf_tage` (Indikator-Vorlauf, 60 Tage decken auch 50er-Fenster
    ab). Volle Historie ueber ~60 Symbole wuerde den Export vervielfachen,
    ohne fuer diese Frage etwas beizutragen - das Nach-Signal-Fenster ist
    automatisch enthalten, weil bis heute exportiert wird.
    """
    grenzen = conn.execute(
        "SELECT MIN(d) AS von FROM ("
        "  SELECT MIN(created_at) AS d FROM hebel_signals"
        "  UNION ALL SELECT MIN(created_at) FROM signals)"
    ).fetchone()
    aeltestes = (grenzen["von"] or "")[:10]
    if not aeltestes:
        return {"symbole": [], "ab_datum": None, "preishistorie_je_symbol": {}}

    ab = (datetime.fromisoformat(aeltestes) - timedelta(days=vorlauf_tage)).strftime("%Y-%m-%d")

    symbole = sorted({
        r["symbol"] for r in conn.execute(
            "SELECT DISTINCT symbol FROM hebel_signals"
            " UNION SELECT DISTINCT symbol FROM signals"
        ).fetchall() if r["symbol"]
    })
    preishistorie = {
        symbol: [
            row_to_dict(r) for r in conn.execute(
                "SELECT * FROM price_history_ohlc WHERE symbol = ? AND date >= ?"
                " ORDER BY date ASC", (symbol, ab)
            ).fetchall()
        ]
        for symbol in symbole
    }
    ohne_daten = sorted(s for s, v in preishistorie.items() if not v)
    return {
        "symbole": symbole,
        "ab_datum": ab,
        "vorlauf_tage": vorlauf_tage,
        "symbole_ohne_ohlc": ohne_daten,
        "preishistorie_je_symbol": preishistorie,
    }


def _ohlc_aktualitaet_je_symbol(conn) -> dict:
    """Neu (2026-07-30, siehe Test_und_Verifikationsmethodik.md Abschnitt 2.1a) -
    MAX(date)/Anzahl Zeilen je Symbol in price_history_ohlc UEBER DIE GESAMTE
    Watchlist (nicht nur ueberholte Symbole wie _preishistorie_ueberholte_
    symbole() oder einzelne deep_dive-Symbole) - Grundlage fuer eine
    Veraltungs-Pruefung, ausgeloest durch einen auf dem Desktop gefundenen
    ATR-Perzentil-Plausibilitaetsfund (Werte blieben ueber 5 Tage identisch,
    Ursache: price_history_ohlc fuer mehrere Symbole seit 11 Tagen nicht
    aktualisiert)."""
    rows = conn.execute(
        "SELECT symbol, COUNT(*) AS anzahl, MIN(date) AS von, MAX(date) AS bis "
        "FROM price_history_ohlc GROUP BY symbol ORDER BY bis ASC"
    ).fetchall()
    # WAEHRUNG UND HERKUNFT dazu (2026-08-06). Ohne die Waehrung war nicht
    # sichtbar, dass die Nicht-Krypto-Symbole nur EINE Seite fuehren (OD7C/PLTR
    # nur USD, X136/CEBS nur EUR) - genau der Grund, warum sie bei kaputter
    # FX-Ableitung geschlossen aus der Portfolio-Bewertung fielen. Ohne `quelle`
    # waere eine rekonstruierte Reihe im Export von einer gemessenen nicht zu
    # unterscheiden, und die Rekonstruktion nicht verifizierbar.
    je_reihe = conn.execute(
        "SELECT symbol, currency, quelle, COUNT(*) AS anzahl, MIN(date) AS von, "
        "MAX(date) AS bis FROM price_history_ohlc "
        "GROUP BY symbol, currency, quelle ORDER BY symbol, currency"
    ).fetchall()
    rekonstruiert = conn.execute(
        "SELECT symbol, currency, COUNT(*) AS anzahl, MAX(date) AS bis "
        "FROM price_history_ohlc WHERE quelle = 'rekonstruiert' "
        "GROUP BY symbol, currency ORDER BY symbol"
    ).fetchall()
    return {
        "symbole": [row_to_dict(r) for r in rows],
        "je_symbol_waehrung_quelle": [row_to_dict(r) for r in je_reihe],
        "rekonstruierte_reihen": [row_to_dict(r) for r in rekonstruiert],
    }


def _hedge_wirksamkeit(conn) -> dict:
    """Hat die Absicherung den Rueckschlag gedaempft? (2026-08-07, W1)

    Fenster wie bei Z-3: 90 Tage. Kuerzer waere fuer eine Drawdown-Aussage zu
    wenig, laenger vermischt Zeitraeume mit und ohne Hedge-Position."""
    from agent.portfolio_historie import compute_hedge_wirksamkeit
    from datetime import datetime, timedelta, timezone

    ab = (datetime.now(timezone.utc).date() - timedelta(days=90)).isoformat()
    return compute_hedge_wirksamkeit(
        conn, ab_datum=ab, watchlist=config_module.get_watchlist())


def _themenfeld_erfolg(conn) -> dict:
    """Traf die Richtung der These? (2026-08-07, Schritt 5 / G-2)

    NICHT die Systemguete je Hauptgruppe: von 101 aufgeloesten Signalen gehoert
    keines zu einem Themenfeld, die Tabelle waere leer. Siehe
    agent/themenfeld_erfolg.py fuer die Herleitung."""
    from agent.themenfeld_erfolg import compute_themenfeld_erfolg
    return compute_themenfeld_erfolg(conn)


def _wartende_themen_vorschlaege(conn) -> dict:
    """Welche Themen-Vorschlaege warten, und wann werden sie reif? (2026-08-07, S-3)

    ANLASS. Am 07.08. standen 14 von 16 Vorschlaegen auf "beobachtung" - und aus
    dem Export war nicht ablesbar, dass darunter ein KI-Vorschlag seit dem
    25.07. laeuft und in 18 Tagen reif wird. Die Statusverteilung allein
    ("14 beobachtung") sagt genau nichts ueber den Vorlauf.

    Die zweite Zahl ist die wichtigere: `engpass_anzahl` sagt, wie viele
    Kandidaten am SELBEN Tag reif werden. Uebersteigt sie das freie Budget,
    entscheidet die Gleichzeitigkeits-Moderation - und das gehoert mit Vorlauf
    gesehen, nicht am Tag selbst."""
    from agent.kategorie_vorschlaege import wartende_vorschlaege
    return wartende_vorschlaege(conn)


def _bewertungs_diagnose(conn) -> dict:
    """Je gehaltenes Symbol: kam ein Kurs zustande, und wenn nein - warum nicht?

    Neu 2026-08-06. Der Portfolio-Wert-Job meldete "19 Symbole ohne Kurs", und
    aus dem Export war nicht rekonstruierbar, welche das waren. Die Ursache lag
    in zwei Defekten, die sich gegenseitig verdeckten: die FX-Ableitung wurde an
    87 von 91 Tagen verworfen (Spannweite statt Interquartilsabstand), wodurch
    alle NUR-USD-Symbole aus der Bewertung fielen - und darunter lag ein zweiter
    Fehler, die Futures-Historie unter dem ETC-Symbol (OD7H mit 4.215,90 USD
    statt 18,22 EUR).

    Diese Sektion macht beide Ebenen sichtbar: fx_tage_verworfen zeigt Ebene 1,
    reihen_verworfen die Plausibilitaetspruefung, und je Symbol steht, ob der
    Kurs direkt in EUR vorlag, ueber den Wechselkurs kam oder ganz fehlte.
    """
    from agent.portfolio_historie import rekonstruiere_stichtag
    from datetime import datetime, timedelta, timezone

    ab = (datetime.now(timezone.utc).date() - timedelta(days=90)).isoformat()
    erg = rekonstruiere_stichtag(conn, ab_datum=ab, watchlist=config_module.get_watchlist())
    letzter = erg.tageswerte[-1] if erg.tageswerte else None
    return {
        "ab_datum": ab,
        "letzter_tag": letzter[0] if letzter else None,
        "letzter_wert_eur": round(letzter[1], 2) if letzter else None,
        "symbole_gesamt": letzter[2] if letzter else 0,
        "symbole_ohne_kurs": letzter[3] if letzter else 0,
        "fx_tage_verworfen_anzahl": len(erg.fx_tage_verworfen),
        "fx_tage_verworfen": erg.fx_tage_verworfen[-10:],
        "reihen_verworfen": erg.reihen_verworfen,
        "je_symbol": [
            {"symbol": d.symbol, "menge": d.menge, "tage_direkt_eur": d.tage_direkt_eur,
             "tage_ueber_fx": d.tage_ueber_fx, "tage_ohne_kurs": d.tage_ohne_kurs,
             "letzter_kurs_eur": d.letzter_kurs_eur, "problemfall": d.ist_problemfall}
            for d in erg.symbol_diagnosen
        ],
    }


def _coingecko_kontingent(conn) -> dict:
    """Neu (2026-08-01, Nutzer-Fund "Tagesverbrauch duerfte zu hoch sein") -
    bisheriger blinder Fleck: die api_call_kontingent[_taeglich]-Tabellen
    (siehe [[project_coingecko_kontingent_tracking]], Tageszaehler seit
    Schritt 3 der Spot-Verkaufs-Luecke-Roadmap) wurden bisher NUR live auf
    der Remote-Statusseite angezeigt, nie hierher exportiert - eine
    Verbrauchsanalyse musste bislang muehsam aus dem rohen Log rekonstruiert
    werden. `taeglich_verlauf` liefert die volle Tageshistorie (nicht nur
    "heute" wie db.get_api_call_counter_taeglich()), damit Trends ueber
    mehrere Tage sichtbar werden, sobald genug Tage vorliegen."""
    monat = db.aktueller_monat_utc()
    monatliches_kontingent = db.get_api_call_counter(conn, "coingecko", monat)
    taeglich_rows = conn.execute(
        "SELECT tag, anzahl FROM api_call_kontingent_taeglich WHERE source = 'coingecko' ORDER BY tag ASC"
    ).fetchall()
    return {
        "monat": monat,
        "monatliches_kontingent": monatliches_kontingent,
        "taeglich_verlauf": [row_to_dict(r) for r in taeglich_rows],
    }


# --- Log-Auszug (2026-07-18, siehe Modul-Docstring) ---------------------
# Format aus main.py::logging.basicConfig(): "%(asctime)s %(levelname)s
# %(name)s: %(message)s" - asctime ist "YYYY-MM-DD HH:MM:SS,mmm".
_LOG_ZEILEN_MUSTER = re.compile(
    r"^(?P<zeit>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),\d{3} (?P<level>\S+) (?P<logger>\S+): (?P<nachricht>.*)$"
)
_JOB_FEHLSCHLAG_MUSTER = re.compile(r"(fehlgeschlagen|verpasst \(Misfire\))")
_GROQ_ERSCHOEPFT_MUSTER = re.compile(r"Groq: \d+ Fehlschlaege in Folge")


def _deribit_cross_check_verlauf(conn) -> dict:
    """Neu (2026-07-26, Deribit-Optionsmarkt-Anreicherung, siehe
    project_deribit_optionsmarkt_anreicherung.md) - der rohe DVOL-/Skew-Wert
    wird NIRGENDS dauerhaft gespeichert (Live-Fetch pro Signal-Lauf, siehe
    agent/krypto/optionsmarkt.py Modul-Docstring) und steckt nur transient in
    `facts_json`, das dieses Skript sonst bewusst ausschliesst (siehe
    Spaltenauswahl-Kommentar oben). Ohne diese Sektion waere die Frage "hat
    der Deribit-Cross-Check ueberhaupt je etwas bewirkt, und war er
    zutreffend" NIE rueckwirkend beantwortbar - Deribit selbst liefert keine
    historischen Options-Skew-Snapshots nach Verfall. Deshalb: gezielter,
    schlanker Parse NUR des `optionsmarkt`-Teilobjekts aus facts_json (nicht
    der gesamte Blob) je Hebel-Signal, zusammen mit den bereits andernorts
    exportierten Begleitwerten (confidence_pct/gegenargument/outcome_status),
    damit spaeter geprueft werden kann, ob ein Deribit-basierter Widerspruch
    im gegenargument-Text mit dem tatsaechlichen Ausgang korrelierte."""
    rows = conn.execute(
        "SELECT symbol, richtung, action, created_at, confidence_pct, gegenargument, "
        "outcome_status, outcome_realisiertes_crv, facts_json "
        "FROM hebel_signals ORDER BY created_at ASC"
    ).fetchall()
    eintraege = []
    for r in rows:
        try:
            facts = json.loads(r["facts_json"]) if r["facts_json"] else {}
        except (TypeError, json.JSONDecodeError):
            continue
        optionsmarkt = facts.get("optionsmarkt")
        if not optionsmarkt:
            continue
        eintraege.append({
            "symbol": r["symbol"], "richtung": r["richtung"], "action": r["action"],
            "created_at": r["created_at"], "confidence_pct": r["confidence_pct"],
            "gegenargument": r["gegenargument"],
            "outcome_status": r["outcome_status"], "outcome_realisiertes_crv": r["outcome_realisiertes_crv"],
            "dvol_prozent": optionsmarkt.get("dvol_prozent"),
            "skew_prozentpunkte": optionsmarkt.get("skew_prozentpunkte"),
        })
    return {
        "anzahl_mit_optionsmarkt_fakt": len(eintraege),
        "anzahl_mit_gegenargument": sum(1 for e in eintraege if e["gegenargument"]),
        "eintraege": eintraege,
    }


def _zai_gegenpruefung_verlauf(conn) -> dict:
    """Neu (2026-07-26, Z.ai-Gegenpruefungslogik, siehe
    project_zai_gegenpruefungslogik.md) - anders als der Deribit-Cross-Check
    oben sind `zai_gegenpruefung_urteil`/`zai_gegenpruefung_kurzbegruendung`
    bereits als eigene Spalten in `_HEBEL_SIGNAL_SPALTEN` erfasst (echte
    persistente Felder, kein transienter facts_json-Wert) - diese Sektion ist
    deshalb reine Aggregations-Bequemlichkeit (analog konfidenz_kalibrierung/
    provider_performance), damit die zentrale Beobachtungsfrage ('wie oft
    widerspricht Z.ai der eigenen Begruendung, und korreliert das mit dem
    tatsaechlichen Signal-Ausgang?') nicht bei jeder Analyse neu aus den
    Rohspalten rekonstruiert werden muss. Phase 1 bleibt rein beobachtend
    (kein Gate) - siehe reference_offene_zeitbasierte_beobachtungspunkte.md.

    BUGFIX (2026-07-26, spaeter am selben Tag - Nutzer-Nachfrage nach dem
    LLM1-vs-Z.ai-Richtungsvergleich): diese Funktion wurde beim Bau des
    zweiten, unabhaengigen Z.ai-Calls (`zai_eigene_richtung`/
    `zai_uebereinstimmung`/`zai_richtung_kurzbegruendung`, siehe
    agent/krypto/gegenpruefung.py Punkt 2) NICHT mit erweitert - weder die
    SELECT-Spaltenliste noch der WHERE-Filter kannten die 3 neuen Felder.
    Zwei Faelle waren dadurch unsichtbar: (1) beide Calls liefen und lieferten
    Ergebnisse, aber der Richtungs-Teil wurde nie angezeigt, (2) der
    Konsistenz-Call schlug fehl, aber der Richtungs-Call gelang - so ein
    Datensatz wurde durch den alten WHERE-Filter (nur auf
    `zai_gegenpruefung_urteil` gefiltert) komplett verschluckt, obwohl er
    echte Z.ai-Ergebnisse enthielt. Filter jetzt auf ODER umgestellt, damit
    kein teilweise erfolgreicher Call mehr verloren geht."""
    rows = conn.execute(
        "SELECT symbol, richtung, action, created_at, confidence_pct, "
        "zai_gegenpruefung_urteil, zai_gegenpruefung_kurzbegruendung, "
        "zai_eigene_richtung, zai_uebereinstimmung, zai_richtung_kurzbegruendung, "
        "outcome_status, outcome_realisiertes_crv "
        "FROM hebel_signals WHERE zai_gegenpruefung_urteil IS NOT NULL "
        "OR zai_eigene_richtung IS NOT NULL "
        "ORDER BY created_at ASC"
    ).fetchall()
    eintraege = [row_to_dict(r) for r in rows]
    return {
        "anzahl_gesamt": len(eintraege),
        "anzahl_konsistent": sum(1 for e in eintraege if e["zai_gegenpruefung_urteil"] == "konsistent"),
        "anzahl_widerspruch": sum(1 for e in eintraege if e["zai_gegenpruefung_urteil"] == "widerspruch"),
        "anzahl_richtung_gesamt": sum(1 for e in eintraege if e["zai_eigene_richtung"] is not None),
        "anzahl_uebereinstimmung": sum(1 for e in eintraege if e["zai_uebereinstimmung"] == "ja"),
        "anzahl_abweichung": sum(1 for e in eintraege if e["zai_uebereinstimmung"] == "nein"),
        "eintraege": eintraege,
    }


def _oi_fakten_verlauf(conn) -> dict:
    """Neu (2026-07-28, OI-Squeeze-Divergenz + Funding-Rate-Perzentil, siehe
    project_oi_squeeze_funding_perzentil.md) - identisches Prinzip wie
    _deribit_cross_check_verlauf() oben: beide Fakten stecken nur transient
    im `antizyklisch`-Teilobjekt von `facts_json`, gezielter Parse NUR dieser
    zwei Werte (nicht der gesamte Blob). Anders als beim Deribit-Cross-Check
    (nur Hebel) wurde dieses Feature bewusst fuer Spot UND Hebel gebaut (siehe
    Mengenanalyse im Modul-Docstring-Nachtrag) - deshalb BEIDE Tabellen
    (`signals`+`hebel_signals`), mit einer `pipeline`-Spalte zur
    Unterscheidung. Ohne diese Sektion waere insbesondere die Frage "liefert
    das Funding-Perzentil ueberhaupt Werte, oder fehlt am frisch deployten
    Notebook noch die Mindesthistorie (MIN_FUNDING_PERZENTIL_PUNKTE)" nicht
    beantwortbar, ohne facts_json manuell durchzugehen."""
    eintraege = []
    for tabelle, pipeline in (("signals", "spot"), ("hebel_signals", "hebel")):
        rows = conn.execute(
            f"SELECT symbol, action, created_at, confidence_pct, "
            f"outcome_status, facts_json FROM {tabelle} ORDER BY created_at ASC"
        ).fetchall()
        for r in rows:
            try:
                facts = json.loads(r["facts_json"]) if r["facts_json"] else {}
            except (TypeError, json.JSONDecodeError):
                continue
            antizyklisch = facts.get("antizyklisch") or {}
            squeeze = antizyklisch.get("squeeze_divergenz")
            funding_perz = antizyklisch.get("funding_rate_perzentil")
            if squeeze is None and funding_perz is None:
                continue
            eintraege.append({
                "pipeline": pipeline, "symbol": r["symbol"], "action": r["action"],
                "created_at": r["created_at"], "confidence_pct": r["confidence_pct"],
                "outcome_status": r["outcome_status"],
                "squeeze_divergenz": squeeze, "funding_rate_perzentil": funding_perz,
            })
    return {
        "anzahl_mit_squeeze_divergenz": sum(1 for e in eintraege if e["squeeze_divergenz"] is not None),
        "squeeze_divergenz_verteilung": haeufigkeit(eintraege, "squeeze_divergenz"),
        "anzahl_mit_funding_rate_perzentil": sum(1 for e in eintraege if e["funding_rate_perzentil"] is not None),
        "eintraege": eintraege,
    }


def _log_dateien(log_pfad: Path) -> list[Path]:
    """Aelteste zuerst, damit _log_zeilen_im_fenster() den Zeitfortschritt
    korrekt verfolgen kann - RotatingFileHandler haengt .1/.2/.3 AN (ersetzt
    nicht die Endung), .3 ist die aelteste Rotation, siehe main.py."""
    rotierte = [log_pfad.with_name(log_pfad.name + f".{i}") for i in (3, 2, 1)]
    return [p for p in rotierte if p.exists()] + ([log_pfad] if log_pfad.exists() else [])


def _log_zeilen_im_fenster(log_pfad: Path, stunden: int) -> list[str]:
    """Liest die (ggf. rotierte) Log-Datei und behaelt nur Zeilen (inkl.
    mehrzeiliger Tracebacks) seit `stunden` Stunden. Reine Textzeilen ohne
    Zeitstempel-Praefix (Traceback-Fortsetzungszeilen) werden dem zuletzt
    gesehenen, im Fenster liegenden Log-Eintrag zugerechnet."""
    grenze = datetime.now() - timedelta(hours=stunden)
    ergebnis: list[str] = []
    im_fenster = False
    for datei in _log_dateien(log_pfad):
        for zeile in datei.read_text(encoding="utf-8", errors="replace").splitlines():
            treffer = _LOG_ZEILEN_MUSTER.match(zeile)
            if treffer:
                try:
                    zeitpunkt = datetime.strptime(treffer.group("zeit"), "%Y-%m-%d %H:%M:%S")
                    im_fenster = zeitpunkt >= grenze
                except ValueError:
                    im_fenster = False
            if im_fenster:
                ergebnis.append(zeile)
    return ergebnis


def _job_fehlschlaege_aus_log(zeilen: list[str]) -> list[dict]:
    """Extrahiert nur die eigentliche Fehlermeldungszeile (nicht den vollen
    Traceback, der bleibt im rohen log_auszug einsehbar) fuer jeden erkannten
    Job-Fehlschlag/-Ausfall - api_health_status haelt nur den JEWEILS LETZTEN
    Zustand je Quelle (PRIMARY KEY source), eine Historie ueber die Nacht ist
    nur ueber das Log rekonstruierbar."""
    treffer = []
    for zeile in zeilen:
        m = _LOG_ZEILEN_MUSTER.match(zeile)
        if m and m.group("level") in ("ERROR", "WARNING") and _JOB_FEHLSCHLAG_MUSTER.search(m.group("nachricht")):
            treffer.append({
                "zeitstempel": m.group("zeit"), "level": m.group("level"),
                "logger": m.group("logger"), "nachricht": m.group("nachricht"),
            })
    return treffer


def _groq_erschoepfung_aus_log(zeilen: list[str]) -> list[dict]:
    """Groq-Tageserschoepfungs-Ereignisse (2026-07-18, siehe
    agent/krypto/budget_allocator.py::_record_groq_failure()) - reiner
    In-Memory-Zustand, nirgends in der DB persistiert, nur ueber das Log
    sichtbar."""
    treffer = []
    for zeile in zeilen:
        m = _LOG_ZEILEN_MUSTER.match(zeile)
        if m and _GROQ_ERSCHOEPFT_MUSTER.search(m.group("nachricht")):
            treffer.append({"zeitstempel": m.group("zeit"), "nachricht": m.group("nachricht")})
    return treffer


def _auffaelligkeiten(hebel_rows: list[dict], spot_rows: list[dict]) -> list[dict]:
    """Leichte, regelbasierte Sanity-Checks (KEIN Ersatz fuer eine echte
    inhaltliche Bewertung, siehe Modul-Docstring) - filtert Kandidaten vor,
    bei denen ein Blick lohnt: ein gesetztes Risiko-Veto/nicht bestandenes
    Gate, das TROTZDEM nicht zu HALTEN gefuehrt hat, waere ein struktureller
    Bug in risk_gate.py::post_check() (das erzwingt HALTEN deterministisch,
    siehe dortige Doku) - sollte in der Praxis nie auftreten, ist aber genau
    der Fall, den ein Vorfilter zuverlaessiger findet als manuelles Scrollen.
    cash_veto bewusst NICHT geprueft - anders als risk_veto ist cash_veto=True
    bei bereits regelkonformem HALTEN der Normalfall, kein Hinweis auf einen
    Bug (siehe risk_gate.py::RiskPreCheckResult.cash_veto-Docstring)."""
    funde = []
    for assetklasse, rows in (("spot", spot_rows), ("hebel", hebel_rows)):
        for zeile in rows:
            if zeile.get("risk_veto") and zeile.get("action") != "HALTEN":
                funde.append({
                    "typ": "risk_veto_ohne_halten", "assetklasse": assetklasse,
                    "symbol": zeile.get("symbol"), "created_at": zeile.get("created_at"),
                    "action": zeile.get("action"), "risk_veto_reason": zeile.get("risk_veto_reason"),
                })
            if not zeile.get("gate_passed", True) and zeile.get("action") not in ("HALTEN", None):
                funde.append({
                    "typ": "gate_nicht_bestanden_ohne_halten", "assetklasse": assetklasse,
                    "symbol": zeile.get("symbol"), "created_at": zeile.get("created_at"),
                    "action": zeile.get("action"), "gate_reason": zeile.get("gate_reason"),
                })
    return funde


DB_BACKUP_ORDNER = (
    Path(_ZIEL_UEBERSCHREIBUNG) / "DB_Backups"
    if _ZIEL_UEBERSCHREIBUNG
    else _google_drive_wurzel() / "Claude_Austauschordner" / "DB_Backups"
)
DB_BACKUP_BEHALTEN = 7


def _db_backup(conn, ordner=None, behalten: int = DB_BACKUP_BEHALTEN) -> dict:
    """Konsistentes, geprueftes und rotiertes Backup der Produktiv-DB (2026-08-06).

    WOFUER. Der Export enthaelt das Analyse-relevante Extrakt, aber nicht die
    DB. Geht das Notebook verloren, ist die gesamte Signalhistorie weg - und
    genau die ist die Grundlage jeder Messung in diesem Projekt. Das ist
    Disaster-Recovery, kein Analysebedarf, und deshalb gelten andere Regeln:
    regelmaessig, versioniert, geprueft.

    WARUM NICHT EINFACH DIE DATEI KOPIEREN. Die App schreibt waehrenddessen
    weiter (Scheduler laeuft 24/7). Ein Dateikopie erwischt moeglicherweise
    einen Zustand mitten in einer Transaktion - das Ergebnis ist ein Backup,
    das erst beim Zurueckspielen als kaputt auffaellt. `Connection.backup()`
    ist die dafuer vorgesehene Online-Backup-API und zieht einen konsistenten
    Snapshot, waehrend geschrieben wird.

    WARUM DIE INTEGRITAETSPRUEFUNG. Ein Backup, das man nicht prueft, ist eine
    Vermutung. `PRAGMA integrity_check` laeuft auf der KOPIE, nicht auf dem
    Original - eine Pruefung des Originals sagt nichts ueber die Kopie aus.
    Und die Rotation loescht erst NACH bestandener Pruefung: sonst koennte ein
    fehlgeschlagener Lauf die letzten guten Staende mitnehmen.

    WARUM GZIP. SQLite komprimiert stark (Faktor 3-5 bei dieser DB). Der
    Zielordner liegt in Google Drive und wird synchronisiert - jedes
    gesparte Megabyte ist gesparte Synchronisationszeit.

    HINWEIS ZUM ABLAGEORT, bewusste Entscheidung: die DB enthaelt die
    Portfoliobestaende. Der Notebook-Export liegt mit denselben Daten bereits
    in diesem Ordner, es ist also keine neue Datenkategorie - aber es ist eine
    Entscheidung und kein Automatismus.

    Fail-soft: schlaegt irgendetwas fehl, wird geloggt und der Export laeuft
    normal weiter. Ein misslungenes Backup darf den Analyselauf nicht kosten.
    """
    import gzip
    import os
    import shutil
    import tempfile

    ziel = Path(ordner) if ordner else DB_BACKUP_ORDNER
    ergebnis = {"erfolg": False, "grund": None, "datei": None,
                "bytes": None, "geloescht": []}
    tmp_pfad = None
    try:
        ziel.mkdir(parents=True, exist_ok=True)
        stempel = datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M")
        name = f"tradinginfotool_{stempel}.db.gz"

        # 1) Online-Backup in eine temporaere Datei
        fd, tmp_pfad = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        sicherung = sqlite3.connect(tmp_pfad)
        try:
            conn.backup(sicherung)
        finally:
            sicherung.close()

        # 2) Integritaetspruefung AUF DER KOPIE
        pruef = sqlite3.connect(tmp_pfad)
        try:
            befund = pruef.execute("PRAGMA integrity_check").fetchone()[0]
        finally:
            pruef.close()
        if befund != "ok":
            ergebnis["grund"] = f"integrity_check: {befund[:200]}"
            return ergebnis

        # 3) Komprimieren an den Zielort
        endziel = ziel / name
        with open(tmp_pfad, "rb") as roh, gzip.open(endziel, "wb", compresslevel=6) as gz:
            shutil.copyfileobj(roh, gz)
        ergebnis["datei"] = str(endziel)
        ergebnis["bytes"] = endziel.stat().st_size
        ergebnis["erfolg"] = True

        # 4) Rotation - ERST JETZT, nach bestandener Pruefung
        vorhanden = sorted(ziel.glob("tradinginfotool_*.db.gz"))
        for alt in vorhanden[:-behalten] if behalten > 0 else []:
            try:
                alt.unlink()
                ergebnis["geloescht"].append(alt.name)
            except OSError:
                pass
        return ergebnis
    except Exception as exc:                                   # noqa: BLE001
        ergebnis["grund"] = f"{type(exc).__name__}: {exc}"
        return ergebnis
    finally:
        if tmp_pfad and os.path.exists(tmp_pfad):
            try:
                os.unlink(tmp_pfad)
            except OSError:
                pass


def main() -> None:
    conn = db.get_connection()
    try:
        # 0) Schema aktuell halten (2026-07-20) - rein additive, idempotente
        # Migrationen (identisch zu main.py-Start), stellt sicher, dass neu
        # hinzugekommene Tabellen/Spalten (thesen, oi_abdeckung_status,
        # risikofaktoren_json, ...) existieren, auch falls dieses Skript
        # gegen eine DB laeuft, die seit einem der letzten Feature-Commits
        # nicht mehr neu gestartet wurde.
        db.init_db(conn)

        # 1) Holdings-Check: hat der selektive Sync die Einstandspreise
        # korrekt uebernommen?
        holdings = conn.execute(
            "SELECT symbol, quantity, avg_buy_price_eur, avg_buy_price_manual_eur FROM holdings"
        ).fetchall()

        # 2) API-Gesundheit aller Quellen
        api_health = db.get_api_health_status(conn)

        # 3) Echte LLM-Aufrufe heute je Anbieter + Gesamtvolumen je Tier.
        # "cerebras" bewusst entfernt (2026-07-20) - api/cerebras.py wurde
        # geloescht, der Zaehler war seither dauerhaft 0 und eine
        # irrefuehrende Alt-Referenz.
        llm_calls_heute = {
            "groq": db.count_real_llm_calls_today_by_provider(conn, "groq:"),
            "mistral": db.count_real_llm_calls_today_by_provider(conn, "mistral:"),
            "gemini": db.count_real_llm_calls_today_by_provider(conn, "gemini:"),
        }
        # ECHTE AUFRUFE daneben (2026-08-09, Teil B). BEIDE Zahlen, nicht statt:
        # `llm_calls_heute` zaehlt Signal-ZEILEN und beantwortet "welcher
        # Anbieter hat dieses Signal erzeugt" - das ist fuers Qualitaets-
        # Tracking richtig. `llm_aufrufe_heute` zaehlt HTTP-Aufrufe und
        # beantwortet "wieviel Kontingent haben wir verbraucht".
        #
        # Der Unterschied ist genau der Defekt vom 07.08.: dort stand
        # mistral auf 0 (keine Zeile erzeugt), waehrend real ueber 140
        # vergebliche Aufrufe liefen. Erst NEBENEINANDER wird das sichtbar -
        # eine grosse Luecke zwischen beiden Zahlen heisst "viele Aufrufe ohne
        # Ergebnis", also Fehlschlaege oder Wiederholungen.
        llm_aufrufe_heute = {
            p: db.get_llm_budget_zaehler(conn, p)
            for p in ("groq", "mistral", "gemini", "zai", "openrouter")
        }
        signal_volumen_heute = {
            "spot": db.count_real_signals_today(conn),
            "hebel": db.count_real_hebel_signals_today(conn),
            "marktscan_writeups": db.count_real_marktscan_writeups_today(conn),
        }

        # 3b) Neue Tabellen seit 2026-07-18/19/20, bisher unsichtbar im Export
        # (siehe Modul-Docstring, Nachtrag 2026-07-20):
        thesen_alle = [dataclasses.asdict(t) for t in db.get_alle_thesen(conn)]
        # #333 Schicht 2 + #334 Stufe 2 (2026-07-25, siehe agent/kategorie_synthese.py) -
        # ALLE Aenderungsvorschlaege (nicht nur status='offen' wie
        # get_offene_aenderungsvorschlaege(), das GUI nutzt) fuer die volle
        # Fall-A/B-Zustandshistorie (inkl. 'beobachtung'/'uebernommen'/
        # 'abgelehnt' - zeigt z.B., ob die Gleichzeitigkeits-Moderation
        # tatsaechlich greift: these_id=None + status='offen' waere sonst nie
        # aufgetreten, bevor Schicht 2 existierte).
        these_aenderungsvorschlaege_alle = [
            row_to_dict(r) for r in conn.execute(
                "SELECT * FROM these_aenderungsvorschlaege ORDER BY beobachtung_seit ASC"
            ).fetchall()
        ]
        kategorie_synthese_ergebnisse_alle = [
            row_to_dict(r) for r in conn.execute(
                "SELECT * FROM kategorie_synthese_ergebnis ORDER BY erstellt_am ASC"
            ).fetchall()
        ]
        oi_abdeckung_status_alle = db.get_oi_abdeckung_status(conn)
        hebel_pruefung_toggles = [
            row_to_dict(r) for r in conn.execute("SELECT * FROM asset_hebel_settings").fetchall()
        ]
        # Warteschlangen-Status (2026-07-20) - Gegenprobe fuer den "Info-
        # Leichen"-Verfall-Fix (2026-07-19): waechst 'neu' unbegrenzt, oder
        # greift der automatische Verfall wie gedacht?
        kandidaten_warteschlangen_status = {
            "hebel_triggers": haeufigkeit(
                [row_to_dict(r) for r in conn.execute(
                    "SELECT status FROM hebel_triggers"
                ).fetchall()], "status",
            ),
            "marktscan_candidates": haeufigkeit(
                [row_to_dict(r) for r in conn.execute(
                    "SELECT status FROM marktscan_candidates"
                ).fetchall()], "status",
            ),
        }

        # 3c) Delta Discovery -> LLM-Begruendung (2026-07-21, Nutzer-Fund
        # "16:00 Discovery vs. 19:30 Signal") - siehe Modul-Docstring-Nachtrag
        # unten und project_delta_berechnung_llm_abfrage_timing.md.
        marktscan_discovery_llm_delta = _marktscan_discovery_llm_delta(conn)
        hebel_erstmalige_erkennung_delta = _hebel_erstmalige_erkennung_delta(conn)
        rohdaten_fuer_backtest = _rohdaten_fuer_backtest(conn)
        preishistorie_ueberholte_symbole = _preishistorie_ueberholte_symbole(conn)
        preishistorie_signal_symbole = _preishistorie_signal_symbole(conn)
        deribit_cross_check_verlauf = _deribit_cross_check_verlauf(conn)
        zai_gegenpruefung_verlauf = _zai_gegenpruefung_verlauf(conn)
        oi_fakten_verlauf = _oi_fakten_verlauf(conn)
        ohlc_aktualitaet_je_symbol = _ohlc_aktualitaet_je_symbol(conn)
        coingecko_kontingent = _coingecko_kontingent(conn)

        # Fail-soft: eine fehlende Kategorie-Konfiguration darf den Export
        # nicht toeten (Lehre 06.08.) - aber sie muss im Export SICHTBAR
        # scheitern, nicht still verschwinden.
        try:
            wartende_themen_vorschlaege = _wartende_themen_vorschlaege(conn)
        except Exception as exc:  # noqa: BLE001
            wartende_themen_vorschlaege = {"nicht_verfuegbar": str(exc)}
        try:
            themenfeld_erfolg = _themenfeld_erfolg(conn)
        except Exception as exc:  # noqa: BLE001
            themenfeld_erfolg = {"nicht_verfuegbar": str(exc)}

        # 4) Provider-Performance (Win-Rate/CRV je Anbieter, Spot+Hebel getrennt)
        # Nachtrag 2026-07-29 (Export-Luecke gefunden bei der R-5.10-Analyse-
        # Session, siehe project_r510_konfidenz_veto_analyse_29_07.md): alle
        # folgenden compute_*()-Aufrufe unterstuetzen seit 2026-07-20 ein
        # optionales `watchlist`-Argument, das Spot-family-Signale nach
        # `asset.assetklasse` (krypto/aktien/rohstoffe/etf) statt in einem
        # einzigen "spot"-Topf aufschluesselt - siehe compute_provider_
        # performance()-Docstring in agent/krypto/backward_tracking.py und
        # remote/status.py, das dieses Argument bereits durchreicht. Dieses
        # Skript rief die Funktionen bisher ohne `watchlist` auf (altes
        # Verhalten, alles unter "spot" gepoolt) - dadurch war z.B. bei der
        # R-5.10-Analyse nicht unterscheidbar, ob ein Muster krypto-spezifisch
        # war oder auch Aktien/Rohstoffe/ETF betraf.
        watchlist = config_module.get_watchlist()
        provider_performance = compute_provider_performance(conn, watchlist)
        # 4b) Konfidenz-Kalibrierungskurve (2026-07-26, Punkt 3 des Regime-
        # Persistenz-Folge-Vorschlags, siehe project_konfidenz_kalibrierungskurve.md) -
        # gleiches Prinzip wie provider_performance oben: die Aggregat-Funktion
        # selbst mitschicken statt nur die Rohspalten (confidence_pct/
        # outcome_status stehen zwar schon in hebel_signals/spot_signals unten,
        # aber die fertige Band-Aufschluesselung erspart eine manuelle
        # Nachrechnung bei jeder Analyse).
        konfidenz_kalibrierung = compute_konfidenz_kalibrierung(conn, watchlist)
        # 4c) Z.ais UNABHAENGIGE Richtungs-Erfolgsquote (2026-07-27,
        # Nutzer-Wunsch: "ZAI unabhaengig mit seinen unterschiedlichen
        # Entscheidungen und deren Erfolgsquote messen"). Die urspruengliche
        # Begruendung stuetzte sich auf den Nur-Long-Kandidatenfilter - der ist
        # seit dem 05.08. entfernt, siehe agent/krypto/backward_tracking.py::
        # compute_zai_richtung_performance() Docstring.
        zai_richtung_performance = compute_zai_richtung_performance(conn, watchlist)
        # 4d) Veto-Schatten-Aggregationen (2026-07-28, siehe agent/krypto/
        # backward_tracking.py::check_signal_veto_shadow_outcome()-Docstring
        # fuer die volle Herleitung) - hypothetische, nie ausgefuehrte Trade-
        # Vorschlaege, die durch einen Risk-Gate-Veto auf HALTEN zurueckgestuft
        # wurden, plus die additive "Gesamt"-Zusammenfuehrung mit den echten
        # Signalen und der providerunabhaengige Sendezaehler (Gemini-Sichtbarkeits-
        # Fix).
        veto_schatten_performance = compute_veto_shadow_performance(conn, watchlist)
        # R-5.10-Konfidenzschwellen-Nachtrag (2026-07-30, siehe Memory
        # project_llm_optimierung_abdeckung_pruefung) - nach (tier, veto_grund)
        # statt (tier, provider) gruppiert, direkte Grundlage fuer die
        # config.yaml::regime.min_konfidenz_prozent_krypto_spot_override-
        # Entscheidung und kuenftige Wiedervorlagen (Aktien/Rohstoffe/Themen-ETF).
        veto_schatten_performance_nach_grund = compute_veto_shadow_performance_nach_grund(conn, watchlist)
        # Selbst-gewaehltes-HALTEN-Aggregationen (2026-07-31, Gegenfall zum
        # Veto-Schatten oben - siehe agent/krypto/backward_tracking.py::
        # compute_selbst_halten_performance()-Docstring): kein Gate/Veto, das
        # LLM hat sich selbst gegen einen Trade entschieden, aber trotzdem
        # eine hypothetische Zone angegeben.
        selbst_gewaehltes_halten_performance = compute_selbst_halten_performance(conn, watchlist)
        selbst_gewaehltes_halten_performance_nach_grund = compute_selbst_halten_performance_nach_grund(
            conn, watchlist,
        )
        zai_richtung_performance_schatten = compute_zai_richtung_performance_schatten(conn, watchlist)
        gesamt_signalqualitaet = compute_gesamt_signalqualitaet(conn, watchlist)
        provider_sendezaehler = compute_provider_sendezaehler(conn, watchlist)

        # 5) Alle Hebel-Signale (fuer Long/Short-Bugfix-Verifikation +
        # Gate/Veto-Muster + Outcome-Verteilung)
        hebel_signals = conn.execute(
            f"SELECT {_HEBEL_SIGNAL_SPALTEN} FROM hebel_signals ORDER BY created_at ASC"
        ).fetchall()
        hebel_positions = conn.execute(
            "SELECT * FROM hebel_positions ORDER BY eroeffnet_am ASC"
        ).fetchall()

        # 6) Alle Spot-Signale (gleiche Fragestellung fuer die Spot-Seite)
        spot_signals = conn.execute(
            f"SELECT {_SPOT_SIGNAL_SPALTEN} FROM signals ORDER BY created_at ASC"
        ).fetchall()

        # 7) Regime-Status (laeuft der neue Tab/die Persistenz fehlerfrei?)
        regime_status = get_last_known_regime_status(conn)

        # 8) Einzelfall-Tiefenanalyse (Standard: LINK)
        deep_signale = conn.execute(
            "SELECT * FROM hebel_signals WHERE symbol = ? ORDER BY created_at ASC", (DEEP_DIVE_SYMBOL,)
        ).fetchall()
        deep_positionen = conn.execute(
            "SELECT * FROM hebel_positions WHERE symbol = ? ORDER BY eroeffnet_am ASC", (DEEP_DIVE_SYMBOL,)
        ).fetchall()
        deep_trigger = conn.execute(
            "SELECT * FROM hebel_triggers WHERE symbol = ? ORDER BY screened_at ASC", (DEEP_DIVE_SYMBOL,)
        ).fetchall()
        deep_preis = []
        if deep_signale:
            von = deep_signale[0]["created_at"][:10]
            deep_preis = conn.execute(
                "SELECT * FROM price_history_ohlc WHERE symbol = ? AND date >= ? ORDER BY date ASC",
                (DEEP_DIVE_SYMBOL, von),
            ).fetchall()
        # MUSS vor conn.close() stehen: compute_systemguete() liest die DB.
        # Alle anderen Payload-Werte sind vorberechnete Variablen - beim
        # Einbau am 02.08. war das uebersehen worden, der Aufruf stand
        # zwischen den Payload-Eintraegen und lief damit gegen eine bereits
        # geschlossene Verbindung.
        systemguete = compute_systemguete(conn, watchlist)
        # Richtungsverteilung seit dem Nur-Long-Umbau (2026-08-05). Ebenfalls
        # VOR conn.close() - siehe die Warnung darueber, dieselbe Falle.
        #
        # Die Kennzahl gibt es auch auf der Remote-Seite; sie gehoert aber
        # zusaetzlich in den Export, weil die Auswertung am Desktop laeuft und
        # die Remote-Seite nur einen Momentwert zeigt. Bis zum 05.08. war die
        # Frage nicht stellbar: SHORT-Kandidaten wurden vorgefiltert und
        # SHORT-Empfehlungen vom Risk-Gate auf HALTEN gedreht.
        try:
            richtungsverteilung = compute_richtungsverteilung(conn, watchlist)
        except Exception as exc:
            richtungsverteilung = {"fehler": f"{type(exc).__name__}: {exc}"}
        # Echte Faktensaetze fuer den Regel-28-Test (2026-08-05). MUSS
        # ebenfalls hier stehen - beim ersten Einbau stand der Aufruf oben bei
        # watchlist_stammdaten, das ist aber ein vorberechneter Wert und
        # braucht keine Verbindung mehr. Ergebnis: "Cannot operate on a closed
        # database", derselbe Fehler wie am 02.08. bei compute_systemguete().
        # Der Rauchtest fand das nicht, weil er die FUNKTION mit offener
        # Verbindung prueft, nicht ihre PLATZIERUNG in main().
        #
        # Fail-soft, aber nicht blind: ein fehlender Block darf den Exportlauf
        # nicht kippen (Lehre vom 04.08., portfolio_wert_historie) - ein
        # Verdrahtungsfehler soll aber laut sein und nicht als leeres Ergebnis
        # durchgehen.
        try:
            hebel_faktensaetze = _hebel_faktensaetze(conn)
        except Exception as exc:
            hebel_faktensaetze = {
                "fehler": f"{type(exc).__name__}: {exc}",
                "verdacht": ("VERDRAHTUNGSFEHLER - der Aufruf steht vermutlich nach "
                             "conn.close()" if "closed database" in str(exc).lower()
                             else "Datenbestand"),
                "eintraege": [],
            }
        # Punkt 3.2 (2026-08-04): welche offenen Signale haben einen
        # ungesicherten Buchgewinn ueber der Ausloeseschwelle?
        ausstiegs_empfehlungen = compute_ausstiegs_empfehlungen(
            conn, watchlist, config_module.load_config())
        # CRV-Breakeven-Baender (2026-08-03, Population B). Ebenfalls VOR
        # conn.close(), gleiche Falle wie oben.
        #
        # VIER VARIANTEN statt einer: Horizont 7/14 x mit/ohne HALTEN-Signale.
        # Welche Kombination die belastbarste Schaetzung liefert, ist NICHT
        # entschieden - sie wird walk-forward gegeneinander geprueft, und dafuer
        # muessen alle vier aus DERSELBEN Datenlage stammen. Wer eine Variante
        # vorab auswaehlt, kalibriert auf seine eigene Annahme.
        #
        # Kursreihen einmal laden und durchreichen: sonst laedt jede der acht
        # Kombinationen (4 x 2 tiers) die vollen rund 60000 Zeilen erneut.
        _reihen = lade_kursreihen(conn)
        # Spot NACH ASSETKLASSE getrennt: `signals` fuehrt Krypto, Aktien,
        # Rohstoffe und Themen-ETF gemeinsam. Ohne Symbolfilter waere jeder
        # Spot-Befund ein Mischwert, bei dem hinterher niemand sagen kann, ob er
        # krypto-spezifisch war (Fund 29.07.). Der Sammel-Topf 'spot' laeuft
        # zusaetzlich mit, damit die Aufteilung gegen die Summe pruefbar bleibt.
        _spot_tiers = spot_symbole_je_tier(watchlist)
        crv_breakeven_baender = {}
        _laeufe = [("hebel", None), ("spot", None)]
        _laeufe += [(t, s) for t, s in sorted(_spot_tiers.items())]
        for _tier, _symbole in _laeufe:
            for _horizont in (7, 14):
                for _mit_halten in (True, False):
                    _tabellen_tier = "hebel" if _tier == "hebel" else "spot"
                    _schluessel = (f"{_tier}_h{_horizont}"
                                   f"_{'mit' if _mit_halten else 'ohne'}_halten")
                    crv_breakeven_baender[_schluessel] = compute_crv_breakeven_baender(
                        conn, _tabellen_tier, horizont=_horizont,
                        mit_halten=_mit_halten, erlaubte_symbole=_symbole,
                        reihen=_reihen,
                    )
    finally:
        conn.close()

    hebel_rows = [row_to_dict(r) for r in hebel_signals]
    spot_rows = [row_to_dict(r) for r in spot_signals]

    # 9) Log-Auszug + daraus abgeleitete Auswertungen (2026-07-18, siehe
    # Modul-Docstring) - reines Datei-I/O, braucht keine DB-Connection mehr.
    log_pfad = Path(__file__).resolve().parent / "data" / "tradinginfotool.log"
    log_zeilen = _log_zeilen_im_fenster(log_pfad, LOG_FENSTER_STUNDEN)
    job_fehlschlaege = _job_fehlschlaege_aus_log(log_zeilen)
    groq_erschoepfung = _groq_erschoepfung_aus_log(log_zeilen)
    auffaelligkeiten = _auffaelligkeiten(hebel_rows, spot_rows)

    # Watchlist-Stammdaten je Symbol (2026-08-04, Phase 1 Schritt a).
    #
    # WOFUER. Die Assetklasse steht NUR in der Watchlist, nicht in `holdings`
    # und nicht in der Signalzeile. Ohne sie laesst sich die Spot-Familie im
    # Export nicht aufschluesseln - jede Auswertung landet im Sammeltopf
    # "spot" und mischt Krypto, Aktien, Rohstoffe und Themen-ETF. Genau dieser
    # Mischtopf war der Fehler vom 29.07., vor dem _assetklasse_index()
    # seither laut warnt; im Export war er bis heute unvermeidbar.
    #
    # `hauptgruppe`, `unterkategorie` und `rolle` kommen mit, weil sie
    # Merkmale sind, die in KEINER Signalzeile stehen - fuer die
    # Ausschuss-Suche (Abschnitt 7 der Zielgroessen-Doku) sind sie damit neue
    # Information, nicht bloss eine Kopie. Kosten: rund 60 Symbole x 5 Felder.
    watchlist_stammdaten = {
        a.symbol: {
            "assetklasse": a.assetklasse,
            "rolle": a.rolle,
            "beobachtungsstatus": a.beobachtungsstatus,
            "hauptgruppe": a.hauptgruppe,
            "unterkategorie": a.unterkategorie,
        }
        for a in watchlist
    }

    payload = {
        "watchlist_stammdaten": watchlist_stammdaten,
        "hebel_faktensaetze": hebel_faktensaetze,
        "richtungsverteilung": richtungsverteilung,
        "holdings_check": [row_to_dict(r) for r in holdings],
        "api_health": api_health,
        "llm_calls_heute": llm_calls_heute,
        "llm_aufrufe_heute": llm_aufrufe_heute,
        "signal_volumen_heute": signal_volumen_heute,
        "provider_performance": provider_performance,
        "konfidenz_kalibrierung": konfidenz_kalibrierung,
        "zai_richtung_performance": zai_richtung_performance,
        "veto_schatten_performance": veto_schatten_performance,
        "veto_schatten_performance_nach_grund": veto_schatten_performance_nach_grund,
        "systemguete": systemguete,
        "ausstiegs_empfehlungen": ausstiegs_empfehlungen,
        "crv_breakeven_baender": crv_breakeven_baender,
        "selbst_gewaehltes_halten_performance": selbst_gewaehltes_halten_performance,
        "selbst_gewaehltes_halten_performance_nach_grund": selbst_gewaehltes_halten_performance_nach_grund,
        "zai_richtung_performance_schatten": zai_richtung_performance_schatten,
        "gesamt_signalqualitaet": gesamt_signalqualitaet,
        "provider_sendezaehler": provider_sendezaehler,
        "hebel_signals": hebel_rows,
        "hebel_positions": [row_to_dict(r) for r in hebel_positions],
        "spot_signals": spot_rows,
        "gate_veto_haeufigkeit": {
            # bestehende reine Text-Aggregation - all-time, KEIN Symbol-/Zeitbezug
            # (siehe _gate_veto_analyse()-Docstring fuer die Einschraenkung).
            "hebel_gate_reason": haeufigkeit(hebel_rows, "gate_reason"),
            "hebel_risk_veto_reason": haeufigkeit(hebel_rows, "risk_veto_reason"),
            "spot_gate_reason": haeufigkeit(spot_rows, "gate_reason"),
            "spot_risk_veto_reason": haeufigkeit(spot_rows, "risk_veto_reason"),
            # NEU (2026-07-28-Fund): Pro-Symbol-Aufschluesselung + Zeitfenster fuer
            # gate_reason (der Veto-Grund, der Live-Datenprobleme wie "Historie
            # veraltet" anzeigt - risk_veto_reason ist ueberwiegend erwartetes
            # Regelwerk-Verhalten wie CRV<Minimum, daher hier bewusst nicht
            # aufgeschluesselt).
            "hebel_gate_reason_all_time": _gate_veto_analyse(hebel_rows, "gate_reason"),
            "spot_gate_reason_all_time": _gate_veto_analyse(spot_rows, "gate_reason"),
            "hebel_gate_reason_letzte_tage": _gate_veto_analyse(
                hebel_rows, "gate_reason", seit_tagen=GATE_VETO_FENSTER_TAGE
            ),
            "spot_gate_reason_letzte_tage": _gate_veto_analyse(
                spot_rows, "gate_reason", seit_tagen=GATE_VETO_FENSTER_TAGE
            ),
        },
        "regime_status": regime_status,
        "thesen_alle": thesen_alle,
        "these_aenderungsvorschlaege_alle": these_aenderungsvorschlaege_alle,
        "wartende_themen_vorschlaege": wartende_themen_vorschlaege,
        "themenfeld_erfolg": themenfeld_erfolg,
        "kategorie_synthese_ergebnisse_alle": kategorie_synthese_ergebnisse_alle,
        "oi_abdeckung_status_alle": oi_abdeckung_status_alle,
        "hebel_pruefung_toggles": hebel_pruefung_toggles,
        "kandidaten_warteschlangen_status": kandidaten_warteschlangen_status,
        "marktscan_discovery_llm_delta": marktscan_discovery_llm_delta,
        "hebel_erstmalige_erkennung_delta": hebel_erstmalige_erkennung_delta,
        "z3_status": rohdaten_fuer_backtest.pop("_z3_status", None),
        "bewertungs_diagnose": rohdaten_fuer_backtest.pop("_bewertungs_diagnose", None),
        "hedge_wirksamkeit": rohdaten_fuer_backtest.pop("_hedge_wirksamkeit", None),
        "rohdaten_fuer_backtest": rohdaten_fuer_backtest,
        "preishistorie_ueberholte_symbole": preishistorie_ueberholte_symbole,
        "preishistorie_signal_symbole": preishistorie_signal_symbole,
        "deribit_cross_check_verlauf": deribit_cross_check_verlauf,
        "zai_gegenpruefung_verlauf": zai_gegenpruefung_verlauf,
        "oi_fakten_verlauf": oi_fakten_verlauf,
        "ohlc_aktualitaet_je_symbol": ohlc_aktualitaet_je_symbol,
        "coingecko_kontingent": coingecko_kontingent,
        "deep_dive": {
            "symbol": DEEP_DIVE_SYMBOL,
            "hebel_signals": [row_to_dict(r) for r in deep_signale],
            "hebel_positions": [row_to_dict(r) for r in deep_positionen],
            "hebel_triggers": [row_to_dict(r) for r in deep_trigger],
            "price_history_ohlc": [row_to_dict(r) for r in deep_preis],
        },
        "log_fenster_stunden": LOG_FENSTER_STUNDEN,
        "log_auszug": log_zeilen,
        "job_fehlschlaege": job_fehlschlaege,
        "groq_erschoepfung_ereignisse": groq_erschoepfung,
        "auffaelligkeiten": auffaelligkeiten,
    }

    ZIEL_ORDNER.mkdir(parents=True, exist_ok=True)
    ziel_datei = ZIEL_ORDNER / "notebook_diagnose.json"
    ziel_datei.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    print(f"Geschrieben: {ziel_datei}")
    print(f"  Holdings: {len(holdings)}, Hebel-Signale: {len(hebel_rows)}, "
          f"Spot-Signale: {len(spot_rows)}, Hebel-Positionen: {len(hebel_positions)}")
    print(f"  LLM-Calls heute (Signalzeilen): {llm_calls_heute}")
    print(f"  LLM-Aufrufe heute (echte HTTP-Calls): {llm_aufrufe_heute}")
    print(f"  Deep-Dive ({DEEP_DIVE_SYMBOL}): {len(deep_signale)} Signale, "
          f"{len(deep_positionen)} Positionen, {len(deep_trigger)} Trigger, "
          f"{len(deep_preis)} Preispunkte")
    print(f"  Log-Fenster: {LOG_FENSTER_STUNDEN} Std., {len(log_zeilen)} Zeilen, "
          f"{len(job_fehlschlaege)} Job-Fehlschlaege, {len(groq_erschoepfung)} Groq-Erschoepfungs-Ereignisse")
    print(f"  Auffaelligkeiten (regelbasierter Vorfilter): {len(auffaelligkeiten)}")
    print(f"  Thesen: {len(thesen_alle)}, OI-Abdeckungs-Status-Eintraege: {len(oi_abdeckung_status_alle)}, "
          f"Hebel-Pruefung-Toggles: {len(hebel_pruefung_toggles)}")
    print(f"  #333 Schicht 2: {len(kategorie_synthese_ergebnisse_alle)} Tages-Synthese-Ergebnisse, "
          f"{len(these_aenderungsvorschlaege_alle)} Aenderungsvorschlaege gesamt "
          f"({haeufigkeit(these_aenderungsvorschlaege_alle, 'status')})")
    print(f"  Warteschlangen-Status: {kandidaten_warteschlangen_status}")
    print(f"  Discovery->LLM-Delta (Marktscan): {marktscan_discovery_llm_delta['statistik']}")
    print(f"  Erstmalige-Erkennung->Signal-Delta (Hebel): {hebel_erstmalige_erkennung_delta['statistik']}")
    print(f"  Rohdaten fuer Backtest: {len(rohdaten_fuer_backtest['hebel_triggers_kandidaten'])} Hebel-Trigger-"
          f"Kandidaten, {len(rohdaten_fuer_backtest['marktscan_kaufkandidaten'])} Marktscan-Kaufkandidaten, "
          f"{len(rohdaten_fuer_backtest['marktscan_alle_kandidaten'])} Marktscan-Kandidaten gesamt (alle Einstufungen)")
    print(f"  Preishistorie ueberholte Symbole: {len(preishistorie_ueberholte_symbole['symbole'])} Symbole "
          f"({', '.join(preishistorie_ueberholte_symbole['symbole']) or '-'})")
    _psy = preishistorie_signal_symbole
    _psy_punkte = sum(len(v) for v in _psy['preishistorie_je_symbol'].values())
    print(f"  Preishistorie Signal-Symbole: {len(_psy['symbole'])} Symbole ab {_psy['ab_datum']}, "
          f"{_psy_punkte} OHLC-Punkte"
          + (f" - OHNE Daten: {', '.join(_psy['symbole_ohne_ohlc'])}" if _psy['symbole_ohne_ohlc'] else ""))
    print(f"  Konfidenz-Kalibrierung: {konfidenz_kalibrierung}")
    print(f"  Deribit-Cross-Check: {deribit_cross_check_verlauf['anzahl_mit_optionsmarkt_fakt']} Signale mit "
          f"Optionsmarkt-Fakt, davon {deribit_cross_check_verlauf['anzahl_mit_gegenargument']} mit gegenargument")
    print(f"  Z.ai-Gegenpruefung: {zai_gegenpruefung_verlauf['anzahl_gesamt']} Signale mit Urteil "
          f"({zai_gegenpruefung_verlauf['anzahl_konsistent']} konsistent, "
          f"{zai_gegenpruefung_verlauf['anzahl_widerspruch']} widerspruch)")
    _wt = wartende_themen_vorschlaege
    if "nicht_verfuegbar" in _wt:
        print(f"  Wartende Themen-Vorschlaege: NICHT VERFUEGBAR ({_wt['nicht_verfuegbar']})")
    else:
        _lage = _wt["richtgroessen_lage"]
        print(f"  Wartende Themen-Vorschlaege: {_wt['anzahl_wartend']} warten, "
              f"{_wt['anzahl_reif']} reif"
              + (f" - Engpass am {_wt['engpass_am']}: {_wt['engpass_anzahl']} gleichzeitig"
                 if _wt["engpass_am"] else ""))
        print(f"  Richtgroesse (WEICH seit 07.08.): {_lage['aktive_thesen']} aktive Thesen "
              f"({_lage['minimum']}-{_lage['maximum']}), Lage '{_lage['lage']}', "
              f"{_lage['hauptgruppen_abgedeckt']} Hauptgruppen, "
              f"{_lage['davon_neutral']} davon neutral")
    _tf = themenfeld_erfolg
    if "nicht_verfuegbar" in _tf:
        print(f"  Themenfeld-Erfolg: NICHT VERFUEGBAR ({_tf['nicht_verfuegbar']})")
    else:
        print(f"  Themenfeld-Erfolg: {_tf['anzahl_thesen']} Thesen, "
              f"{_tf['anzahl_messbar']} messbar, {_tf['anzahl_mit_urteil']} mit Urteil "
              f"({_tf['treffer']} Treffer, {_tf['fehlschlaege']} daneben)")
        for _e in _tf["thesen"]:
            if _e["messbar"]:
                print(f"    {_e['kategorie_anzeige']}: {_e['ueberrendite_prozentpunkte']:+.1f} pp "
                      f"({_e['richtung']}) -> {_e['treffer']}")
            else:
                print(f"    {_e['kategorie_anzeige']}: nicht messbar - {_e['grund']}")

        _ohne = [v for v in _wt["vorschlaege"] if not v["handelbare_assets"]]
        if _ohne:
            print(f"  G-5: {len(_ohne)} Vorschlaege ohne handelbares Asset - "
                  + ", ".join(v["kategorie_anzeige"] for v in _ohne))
    print(f"  CoinGecko-Kontingent ({coingecko_kontingent['monat']}): "
          f"{coingecko_kontingent['monatliches_kontingent']} Calls, "
          f"{len(coingecko_kontingent['taeglich_verlauf'])} Tage mit Tageszaehler-Historie")

    # DB-Backup ganz zum Schluss (2026-08-06). Reihenfolge ist Absicht: der
    # Export ist zu diesem Zeitpunkt geschrieben, ein fehlgeschlagenes Backup
    # kostet ihn also nicht. Eigene Verbindung, weil die aus main() im
    # try/finally darueber bereits geschlossen sein kann.
    sicherungs_conn = db.get_connection()
    try:
        sicherung = _db_backup(sicherungs_conn)
    finally:
        sicherungs_conn.close()
    if sicherung["erfolg"]:
        print(f"  DB-Backup: {Path(sicherung['datei']).name} "
              f"({sicherung['bytes'] / 1e6:.1f} MB komprimiert, integrity_check ok"
              + (f", {len(sicherung['geloescht'])} alte entfernt" if sicherung["geloescht"] else "")
              + ")")
    else:
        print(f"  DB-Backup FEHLGESCHLAGEN: {sicherung['grund']} "
              f"- der Export ist davon unberuehrt")


if __name__ == "__main__":
    main()
