# Regelwerk — Entscheidungslog (Chronologie)

**Zweck:** chronologisches Protokoll aller Regelwerks-Änderungen, Untersuchungen und bewusst verworfenen Optionen. Beantwortet "*warum* haben wir X so entschieden, und was haben wir geprüft und verworfen?".

**Abgrenzung zu `Regelwerksmanual.md`:** dort steht der **Ist-Zustand** ("welche Regel gilt?"), hier die **Entstehungsgeschichte** ("wie kam es dazu?"). Bis 2026-08-02 waren beide in einer Datei — mit 146 chronologischen Nachträgen gegenüber 19 Kapiteln Ist-Zustand war der Ist-Zustand darin nicht mehr auffindbar. **Wichtig:** das Manual bildet den Stand bis ca. 2026-07-17 strukturiert ab; alle späteren Regeländerungen sind bisher NUR hier dokumentiert — bei einer Frage nach dem aktuellen Stand immer beides prüfen (Index unten nach Thema).

**Pflege:** neue Nachträge unten anhängen (chronologisch), Index oben ergänzen. Bestehende Nachträge nie überschreiben — Korrekturen als neuer Nachtrag mit Verweis.

---

## Index nach Thema (201 Einträge)

Ein Nachtrag kann mehrere Themen berühren — hier jeweils nach dem dominanten Thema einsortiert. Volltextsuche im Dokument bleibt der zuverlässigere Weg bei Detailfragen.

### Regelwerk / deterministische Gates (39)

- **2026-08-07** — Manuelle Schwerpunkte mit garantiertem Raum: eine gesetzte Überzeugung wird nicht von einem trendenden Thema verdrängt (Aufmerksamkeit, keine Richtungsvorgabe)

- **2026-08-07** — Schwerpunkte: Struktur (10 Hauptgruppen/72 Unterkategorien) und Mechanik sind gebaut; blockiert wird die Erweiterung durch `richtgroesse_max_aktive_thesen: 6` bei 6 aktiven Thesen

- **2026-08-07** — RM-Bitpanda für Hedge nachgezogen (fehlte als einzige der sechs Pipelines) + Marktsuche-Filter `marktsuche.nur_bitpanda_gelistet` mit GUI-Schalter

- **2026-08-07** — H-2 Zeithorizont-Deckel je Klasse (Maximum, kein Mindestwert) + H-3 Basislinie folgt der gemessenen Haltedauer; dazu Zwischenrecherche: Spot-Kosten zu hoch, RM-3 tot, Risikoparameter global

- **2026-08-07** — W2: Hedge-Risikofaktoren mit umgekehrter Wirkrichtung + Zonenwache — 9 von 11 Hedge-Empfehlungen hatten Stop über und Ziel unter dem Einstieg

- **2026-08-07** — W1: Hedge bekommt eigenen Tier + `compute_hedge_wirksamkeit()` (Dämpfung statt Expectancy) — „invertieren" wäre falsch gewesen, der Fehler lag in der Fragestellung

- **2026-07-17** — RM-4 (Cash-Reserve) war rueckwaerts- statt vorwaertsgerichtet
- **2026-07-18** — Cash-Veto-Warnsystem - RM-4-Block sichtbar machen statt stillschweigend zu HALTEN downzugraden
- **2026-07-19** — Liquidationspreis-Sicherheitsmarge neu kalibriert
- **2026-07-19** — Retail-Konsens-Deckel + Risikofaktoren-Liste + 3-Abschnitte-Neustrukturierung (E-Mail/App, alle Assetklassen)
- **2026-07-22** — Retail-Konsens + CRV/Stop-Loss - "Fakt zuerst, Wertung danach"
- **2026-07-22** — Zwei weitere echte Funde aus einem LINK-Hebel-Signal (Antizyklisch-Regelverstoss + Funding-Rate-Rohfloat)
- **2026-07-23** — Liquidationspreis/Eigenkapitalbedarf zusätzlich in EUR (Hebel-Signal-Detail-Panel)
- **2026-07-24** — Spot-Positionsgrößen-Deckel von Multiplikation auf min() umgestellt (Überstrenge-Prüfung)
- **2026-07-24** — Gates-Kalibrierung — echte Ursache gefunden, Prompt-Anker statt Zahlenwerte korrigiert
- **2026-07-25** — Retail-Konsens-Risiko Fakt-zuerst-Fix für Spot umgesetzt (Datenanalyse vorgeschaltet)
- **2026-07-25** — echter BTC-Hebel-Signal-Review - Antizyklisch-Kategorie-Loophole + Liquiditätszonen-Währungs-Bug
- **2026-07-26** — Retail-Konsens ("antizyklisch") wird bei Hebel nie wieder in top_gruende zugelassen - deterministisch statt...
- **2026-07-28** — Nur-Long-Deckel — echter Bug, keine reine Konfigurationsfrage (NEAR/TAO SHORT ERÖFFNEN trotz aktivem `nur_l...
- **2026-07-28** — Veto-Schatten-Tracking — vetote Trade-Vorschläge werden jetzt weiterverfolgt statt spurlos zu verschwinden
- **2026-07-28** — Option D umgesetzt (Fakt + Prompt-Regel, bewusst OHNE Hard-Veto) - Root-Cause-Analyse vor Umsetzung
- **2026-07-29** — Eigenkapital-Richtwert fuer Hebel-Positionsgroesse (weicher Deckel)
- **2026-07-29** — Regelwerk-Audit (3 Stufen) + Stufe 0 - Eigenkapital-Deckel-FX-Fallback gefixt
- **2026-07-30** — Regime-Konflikt/-Ausrichtung für die Spot-Familie nachgerüstet (Punkt B der LLM-Optimierungs-Abdeckungsprüf...
- **2026-07-30** — R-5.10-Konfidenzschwelle - Live-Test, Backtest-Infrastruktur, Korrektur
- **2026-08-01** — R-5.10-Konfidenzschwelle erneut geprüft bei größerer Stichprobe (n=148) - Vorzeichenwechsel bleibt bestehen
- **2026-07-31** — Blinder Fleck behoben — Schatten-Tracking auch für selbst gewähltes HALTEN (kein Gate/Veto)
- **2026-07-31** — zwei echte Funde beim ersten Notebook-Lauf - NameError-Bugfix + Veto-Schatten-Kontamination behoben
- **2026-08-01** — Marktscan Top-N-Deckel umgesetzt + "unbekannte Aufrufe" geklaert
- **2026-08-01** — Hebel-CRV-Pflicht-Symmetrie (Spot-Verkaufs-Luecke Roadmap-Punkt 5) - Praemisse geprueft und verworfen, KEIN...
- **2026-08-03** — CRV-Gate abschliessend geprueft: es filtert RICHTIG (#602 geschlossen, 02.08.-Befund widerrufen)
- **2026-08-03** — Gate oder Positionsgroesse? Antwort je Tier gegenlaeufig - Hebel Gate behalten, Spot Groesse
- **2026-08-03** — Z-3/RM-7 Drawdown-Notbremse gebaut (#612) - mengenkonstanter Index, Margin-Regel, loeste sofort aus
- **2026-08-04** — Der Einstieg ist nicht das Problem, der AUSSTIEG ist es (50 % standen bei +1R, nur 17,6 % kamen an)
- **2026-08-04** — Positionsgroesse #606 entschieden: Kelly-Empfehlung UND RM-1-Obergrenze gemeinsam anzeigen
- **2026-08-05** — Die Richtungswahl ist eine REGIME-WETTE, keine Kante - plus 93→3 % beim Ausfuehrungshinweis
- **2026-08-05** — Nur-Long-Umbau in fuenf Schritten: der BP-Schalter wirkt nur noch auf E-Mail und Anzeige
- **2026-08-05** — Ausstiegsregel scharfgeschaltet: Config, taeglicher Job 7:15, Sammel-E-Mail
- **2026-08-06** — Gate-Untergrenze Stop-Abstand: EXISTIERT BEREITS (RM-1b 2,5 % + RM-1c 0,75xATR), richtig kalibriert, nichts gebaut

### LLM-Prompts / Analysten (Stage 2) (21)

- **2026-08-07** — Themen-Brücken quer zu den Hauptgruppen (Kupfer = Material + Miner) + Asset-Steckbrief aus vorhandenen Daten; Lücken ausdrücklich erlaubt

- **2026-08-07** — H-6 (`original_action` für die Spot-Familie) + H-5 (`pruefe_fakten_rollout.py`); dazu Korrektur: Befolgungsgrad war als „zentraler Blocker" überzeichnet

- **2026-08-07** — Ausbaustand-Drift gemessen: von 11 Fakten seit dem 09.07. wurde genau EINER auf alle Spot-Klassen ausgerollt; Nicht-Krypto-Analysten stehen im Kern auf dem 09.07.

- **2026-08-07** — Warum Aktien/ETF/Rohstoffe nur HALTEN sagen: kein Akkumulations-Framework (Krypto 7x Tranche/15x antizyklisch, die anderen null) + Zeithorizont hängt am LLM statt an der Klasse

- **2026-07-18** — Konfidenz-Kalibrierung nach dem echten CAT-Fall (fünf Bausteine A-E)
- **2026-07-19** — Release 2 (Schwerpunkte/Thesen-Verwaltung) - Konzeptionsrunde
- **2026-07-20** — Release 2 (Schwerpunkte/Thesen-Verwaltung) - Umsetzung #332/#343
- **2026-07-24** — Kontrathese-Übersetzung für offene Hebel-Positionen
- **2026-07-25** — Konfidenz-Prompt-Fix auf Aktien/Rohstoffe/Themen-ETF ausgeweitet
- **2026-07-25** — Signal-Fazit (`eigene_einschaetzung`) - abschließendes LLM-Synthese-Verdikt, alle 6 Assetklassen mit LLM-Be...
- **2026-07-25** — Kontrathese-Übersetzung Lücke geschlossen - echter HYPE-Fund
- **2026-07-25** — #333 Schicht 2 + #334 Stufe 2 - kategorienübergreifende LLM-Synthese und objektiv gegatete Screener-Gewichtung
- **2026-07-28** — Fakten-Entscheidungsmappe + Hebel-Regel 22 (FOMC/CPI-Kontext)
- **2026-07-31** — Hebel Regel 6 um Take-Profit-ATR-Leitplanke erweitert + neuer Messstandard atr_relativ_prozent_bei_signal
- **2026-08-02** — Dead-Loop-Synthese (Task #598) - Gliederung, Root-Cause-Analyse, Massnahme 1 umgesetzt
- **2026-08-03** — CRV-Erfolgsbaender als Fakt + Regel 36 (Krypto-Spot) - glatter Verlauf statt Ja/Nein-Schwelle
- **2026-08-05** — Konfidenz-Schwellen NICHT neu kalibriert - die Konfidenz sagt nichts vorher, Neukalibrierung waere Theater
- **2026-08-05** — Drei neue Hebel-Fakten (Kosten, Ausstiegsregel, Systemguete) + Regeln 30/31 - kombiniert gemessen, kein Nachweis, bleiben drin
- **2026-08-06** — Gesamtaufnahme der fehlenden Fakten (Abschnitt 8) + vierstufiges Ausstiegsverfahren statt Abbruchschwelle
- **2026-08-06** — Regime-Glaettung (Schatten) + Divergenz-Fakt btc_zu_ema50, Regeln 33/37 - Korrektur einer eigenen Uebergeneralisierung
- **2026-08-06** — Divergenz-Fakt gemessen (n=28): Waechter haelt, EROEFFNEN in allen Armen identisch, keine Wirkung nachweisbar

### Z.ai-Gegenpruefung (Stage 3) (23)

- **2026-07-20** — Z.ai (Zhipu AI) testweise als vierte, unverifizierte Fallback-Stufe VOR Mistral eingehaengt
- **2026-07-20** — Z.ai auf letzte Fallback-Stufe zurueckgestuft + Budget-Neukalibrierung
- **2026-07-21** — Erste Nacht-Auswertung + BUGFIX Zeitzonen-Anzeige in Signal-E-Mails + zweiter Zai-Datenpunkt
- **2026-07-21** — Zai-Root-Cause endgueltig geklaert - Kontextlaengen-Drosselung >8K Token
- **2026-07-26** — Z.ai-Gegenprüfungslogik - unabhängiger Konsistenz-Check (Hard Facts vs. eigene Begründung), Hebel-only, rei...
- **2026-07-26** — Z.ai-Gegenprüfung um unabhängigen Richtungs-Abgleich erweitert + sichtbar in App/E-Mail
- **2026-07-26** — E-Mail zeigte Z.ai-Zeilen nie - echter Fund per Screenshot, begrenzte Wartezeit als Fix
- **2026-07-26** — extract_notebook_diagnose.py verschluckte teilweise erfolgreiche Z.ai-Richtungs-Calls
- **2026-07-26** — Z.ai-Konsistenz-Check verwechselte Positions-Richtung mit Markteinschaetzung (echter HYPE-Fund)
- **2026-07-27** — Z.ai-Konsistenz-Check auf Spot-Signale ausgeweitet (nicht der Richtungs-Abgleich)
- **2026-07-27** — LLM-Budget-Anzeige/-Zaehlung nach Groq-Entfernung + Z.ai-Gegenpruefungs-Umbau nachgezogen
- **2026-07-27** — Z.ai-Gegenpruefung auf alle 6 Signal-Pipelines ausgeweitet (Konsistenz-Check UND Richtungs-Abgleich)
- **2026-07-27** — Z.ai-Richtungs-Erfolgsquote - unabhängig von Mistrals Übereinstimmung gemessen
- **2026-07-27** — Punkt 3 - Z.ai-Erfolgsquote auf Richtungstreffer/MFE statt binärem TP/SL-outcome_status umgestellt
- **2026-07-27** — Sell-Side-Backward-Tracking - VERKAUFEN/TAUSCHEN jetzt vollständig trackbar (Mistral UND Z.ai)
- **2026-07-28** — HOTFIX - Z.ai-429-Sturm behoben (`api/zai.py`)
- **2026-07-28** — Krypto-Spot-Luecke im Z.ai-E-Mail-Versand geschlossen (`scheduler/background.py`)
- **2026-07-28** — Z.ai-E-Mail-Wartezeit auf 90s erhöht (60s zu knapp)
- **2026-07-28** — Z.ai-Fakten-Prüfung ("Punkt 0") — kein Fakten-Bug, sondern durch `nur_long`+Bär-Regime vollständig erklärt
- **2026-07-30** — BUGFIX - Z.ai-Gegenprüfung fehlte in allen Multi-Asset-Batch-E-Mails
- **2026-07-31** — Staggering der Sofort-Start-Jobs, CoinGecko-Kontingent-Tracking, Remote-Fehlerisolierung, Z.ai-Kartenfix
- **2026-07-31** — Multi-Asset Z.ai-Wartemechanismus statt Re-Fetch (Entscheidungskatalog Punkt 1)
- **2026-08-01** — Spot-Verkaufs-Luecke Roadmap Schritt 4 (Z.ai-Re-Evaluierungs-Anzeige) - Roadmap-Praemisse korrigiert VOR de...

### Backward-Tracking / Erfolgsmessung (12)

- **2026-07-19** — Backtracking-Aussagekraft-Audit - Überholt-Erkennung neutralisierte die eigene Ergebnisstatistik
- **2026-07-20** — Provider-Performance-Karte nach Assetklasse aufgeschluesselt (Krypto/Aktien/Rohstoffe/ETF getrennt statt ge...
- **2026-07-21** — Historische-Trefferquote-Risikofaktor + Provider-Performance-Karte verstaendlicher
- **2026-07-22** — Ueberholt-Erkennung repariert - Mindestbeobachtung + Zonen-Reaffirmation (Hebel+Spot)
- **2026-07-23** — Ueberholt-Erkennung - erste Live-Verifikation auf dem Notebook
- **2026-07-24** — Provider-Performance zeigt jetzt auch offene/laufende Signale, nicht nur Abschlüsse
- **2026-07-27** — Mindestziel/MFE-Tracking - unabhaengige Erfolgsmessung neben Take-Profit
- **2026-07-30** — Marktscan-Reifegrad-Scoring + Erfolgsmessung
- **2026-08-03** — Systemguete um mechanische Basislinie, Signalbeitrag und Bootstrap-Intervalle erweitert
- **2026-08-04** — Kostenrahmen recherchiert und in die R-Rechnung eingebaut (Phase 0.2) + der Haltedauer-Widerspruch
- **2026-08-05** — `halte_kriterium` erstmals ausgewertet - kein Trennnachweis, zwei strukturelle Maengel
- **2026-08-06** — Die drei neuen Fakten sind im Betrieb ANGEKOMMEN (22/22) - Verifikation abgeschlossen, Zaehler-Fehler behoben

### Datenquellen / APIs (29)

- **2026-08-07** — Bitpanda-Gebühren recherchiert (Aktien/ETF **fix 1 €**, nicht prozentual — Kostenmodell 3–20× zu hoch) + Schwerpunkte/Screener: vier Lücken, Allocator kennt die Thesen nicht

- **2026-08-07** — Offene Punkte recherchiert und priorisiert (Zwischenstand 8b): vier von sieben Einträgen veraltet; `umgesetzt` fehlt auf `hebel_signals` komplett — Export-Fehlversuch zurückgenommen

- **2026-08-07** — Export-Verifikation: alle Fixes wirken; NEU der tägliche Portfolio-Job bewertete den laufenden statt des Vortags — beide je geschriebenen Zeilen unbrauchbar; CoinGecko bei 83 % Projektion

- **2026-08-06** — Info-E-Mails: Farbe hing an den Bildern (Hedge-Mails immer unformatiert), und eine Meldung stand für drei verschiedene Sachverhalte

- **2026-08-06** — Export 14:20: CRV-Bänder kommen an, ETC-Reihen da, aber der Ausreißer war nur in den Schattenarm umgezogen — Korrektur deckte nur 1 von 3 Messarmen ab

- **2026-08-06** — Erste Verifikation am Export: FX und 3QSS erfüllt, ETC-Rekonstruktion lief nie (zwei Frische-Begriffe an einem Guard), +20,5-R-Ausreißer steht als gespeichertes Ergebnis weiter drin

- **2026-08-06** — Fehler 3 und 4 derselben Runde (`build_hebel_facts()` ohne `crv_baender`, Refresh-Filter auf Phantom-Assetklassen) + `pruefe_aufruf_signaturen.py` belegt: kein Dominoeffekt

- **2026-08-06** — `.get()` auf sqlite3.Row: ein Einzeiler legte Systemgüte, Basislinie und den CRV-Bänder-Fakt seit 09:17 still — fail-soft hat es versteckt, gefunden wurde es im Log

- **2026-08-06** — Audit der Remote-Übersichtsseite: Richtungsverteilung wurde ausgeliefert aber nie angezeigt, Regime-Karte zeigte das alte Verfahren, zwei Karten ohne ihre eigene Einschränkung

- **2026-08-06** — Drei Lücken vor dem Push: Nicht-Krypto-OHLC-Refresh fehlte ganz, Export konnte die Behebung nicht belegen, Z-3 fehlte auf der Übersichtsseite (inkl. neuer Gegenprobe)

- **2026-08-06** — Rekonstruktion der fehlenden Kursreihen (Rohstoffe/3QSS/DBPK) + Scheinwert von 51.000 EUR gefunden - zwei Defekte, die sich gegenseitig verdeckt haben

- **2026-07-18** — Historischer Makro-Konstellationsvergleich umgesetzt
- **2026-07-18** — VIX-Frühindikator als beschreibender Fakt
- **2026-07-18** — Detailanalyse Bärenmarkt-Schwellenwerte + VIX als zweiter Boden-Zielzone-Trigger
- **2026-07-18** — LLM-Budget-Neukalibrierung nach Mistral-Einführung + Zeitpunkt/Anbieter-Anzeige + LLM-Anfrage in der Historie
- **2026-07-19** — erste Notebook-Nacht-Analyse - Misfire-Fehlalarm, klare OI-Fehlermeldungen, persistente OI-Abdeckungs-Warnu...
- **2026-07-19** — CoinGecko-Symbolsuche im
- **2026-07-19** — automatische coingecko_id-Aufloesung
- **2026-07-19** — zwei neue Datenquellen - FRED-CPI-Kalender + SEC-EDGAR-Insider-Trading
- **2026-07-19** — EIA-Erdgas-Lagerbestand + Finnhub-Analysten-Trend
- **2026-07-19** — EIA + Finnhub live mit echten Nutzer-Keys verifiziert
- **2026-07-19** — FINRA Equity Short Interest (Aktien-Pipeline)
- **2026-07-23** — Staleness-Watchdog - Krypto-Kurshistorie blieb ueber Nacht auf altem Stand, 390 Signale blockiert
- **2026-07-24** — #333 letzte zwei offene Mechanismen gebaut (EIA-Erdgas + Bellwether-Sentiment)
- **2026-07-27** — JIT-Historie-Nachladen + deterministische EUR-Ableitung - echter LINK-Vorfall
- **2026-07-28** — DXY-Trend (Dollar-Index) fuer alle 6 Pipelines verdrahtet
- **2026-07-28** — OI-Squeeze-Divergenz + Funding-Rate-Perzentil (Krypto Spot+Hebel)
- **2026-08-01** — Spot-Verkaufs-Luecke Roadmap Schritt 3 (Aktien/Rohstoffe/Themen-ETF) + CoinGecko-Tageszaehler
- **2026-08-01** — CoinGecko-Kontingent-Tiefenanalyse - Marktscan USD-only, JIT-Refresh-Drossel bewusst unveraendert gelassen

### Multi-Asset-Pipelines (11)

- **2026-07-18** — Rohstoff-Pipeline (Phase 2) + Portfolio-Hedge-Logik
- **2026-07-18** — Bugfix Bitpanda-Listing-Spalte fuer Aktien/Rohstoffe/Hedge
- **2026-07-18** — Multi-Asset-Batch - automatische Signal-Erzeugung fuer Aktien/Rohstoffe/Hedge
- **2026-07-18** — Multi-Asset-Vollstaendigkeitspruefung - Themen-ETF-Pipeline + 6 Konsistenz-Fixes
- **2026-07-19** — Aktien/ETF-Screener + Bitpanda-Sonderthema
- **2026-07-20** — Bitpanda-Gelistet-Override fuer Aktien/ETF/Rohstoffe
- **2026-07-20** — Bitpanda-Katalog-Dedup verwarf Krypto-Token bei Ticker-Kollision mit Aktien
- **2026-07-22** — Zwei Hedge-Funde - Bitpanda-Override im E-Mail-Gate + Batch-Budget-Bewusstsein
- **2026-07-28** — Multi-Asset-Batch Cron/Cooldown-Mismatch gefixt
- **2026-07-29** — extract_notebook_diagnose.py - Assetklassen-Aufschluesselung nachgezogen
- **2026-07-30** — Multi-Asset-Batch-Nachhol-Mechanismus (fehlende Hedge-/Aktien-/Rohstoff-/Themen-ETF-Signale)

### LLM-Budget / Provider-Steuerung (7)

- **2026-07-18** — LLM-Tagesbudget-Konsistenzpruefung + E-Mail-Versand-Audit
- **2026-07-18** — Groq-Tageserschöpfung erkennen - kein unnötiger Erschöpfungs-Versuch mehr pro Kandidat
- **2026-07-20** — Groq als Primär-LLM abgeloest - Mistral vor Groq + DB-persistente Erschoepfungs-Erkennung
- **2026-07-21** — Groq-Alternative-Recherche Runde 3+4 abgeschlossen - 32 Kandidaten insgesamt verworfen, Suche vorerst beendet
- **2026-07-21** — Budget-Allocator neu gedacht - SLA-Reservierung statt Score-Ranking (Abschnitt 2+3 umgesetzt)
- **2026-07-28** — Punkt 0b — Wartezeit bis Mistral-Hebel-Signale als Stop-Loss/Richtungsverfehlung aufgelöst werden, PLUS Eng...
- **2026-08-05** — Kanarienvogel (Provider-Drift-Ueberwachung) gebaut, aber BEWUSST NICHT aktiviert - Nutzer-Einwand trug

### GUI / E-Mail / Remote (19)

- **2026-07-19** — Watchlist-Tab-Konsistenzprüfung -
- **2026-07-20** — Screener-Auto-Scan + Mouseover-Tooltips fuer Tabs/Aktionen
- **2026-07-20** — Risikofaktoren-Legende + drei kleine Bugfixes
- **2026-07-20** — Risikofaktoren-Symbole von farbigen Emoji auf Form-Marker umgestellt
- **2026-07-20** — Dark-Mode-Comboboxen kaum lesbar (TCombobox-Styling-Luecke)
- **2026-07-21** — Abschnitt 4 - Wartezeit-Transparenz in UI + E-Mail
- **2026-07-22** — Abschnitt 3 (Konklusion) verschmolz in Outlook zu einem Fliesstext
- **2026-07-23** — E-Mail-Latenz-Fix - Benachrichtigungen hingen 18+ Minuten am Ende des Gesamt-Batches fest
- **2026-07-23** — Liquiditätszonen-Grafik in App-Detail-Panel UND E-Mail
- **2026-07-23** — Hervorhebung in den Signal-Detail-Panels (Hebel/Spot-Familie/Marktscan)
- **2026-07-23** — E-Mail bekam keine Hervorhebung + Liquiditätszonen-Grafik in echten Clients kaum lesbar
- **2026-07-23** — echte Kursverlauf-Linie in der Liquiditätszonen-Grafik
- **2026-07-25** — Liquiditätszonen-Grafik für Spot nachgezogen (Hebel-only-Lücke geschlossen)
- **2026-07-25** — Signale-/Hebel-Tab-Sortierung - Standard-Reihenfolge + gemischte Wertetypen beim Klick-Sortieren
- **2026-07-26** — GUI zeigte Zeitstempel systemweit roh in UTC statt lokal - derselbe Fehler wie beim E-Mail-Fix vom 2026-07-...
- **2026-07-27** — Hebel-Tab-Anzeigefilter - deaktivierte Symbole ohne offene Position + Zeit-Switch
- **2026-07-28** — `hebel_richtung_modus`/E-Mail-Bitpanda-Filter von `data/settings.json` nach `config.yaml` migriert
- **2026-08-03** — Drei Betriebsfehler an einem Abend (Remote-Seite): kaputtes JS, 2-Sekunden-Takt, Cache-Nachbesserungen
- **2026-08-05** — Remote-Seite bereinigt: entfernte Provider und Nur-Long-Altbestand raus, Richtungsverteilung dazu

### Portfolio / Bitpanda (2)

- **2026-07-27** — HYPE-Hebel-Position blieb trotz Vollverkauf "offen" - Kredit-Rueckzahlung als zusaetzliches Signal
- **2026-07-27** — HYPE-Fix Runde 2 - "borrow"-Tag-Theorie war falsch, echte Ursache ist "repay"-Tag + sell_value

### Taxonomie / Screener / Schwerpunkte (4)

- **2026-07-19** — Schwerpunkt-Feld + Diversifikations-Übersicht
- **2026-07-19** — Kategorie-Taxonomie ERSETZT das Freitext-Schwerpunkt-Feld (Release 1)
- **2026-07-21** — Marktscan-Dedup-Bug behoben - "immer dieselben Coins" (APE/EIGEN)
- **2026-07-30** — Screener × Schwerpunkte — geplante, noch nicht umgesetzte Kandidaten-Benachrichtigung (echter Gap, kein Bug)

### Betrieb / Scheduler / Infrastruktur (8)

- **2026-07-19** — "Info-Leichen" - automatischer Verfall
- **2026-07-19** — Konsistenz-Ausweitung des Verfall-Fixes
- **2026-07-23** — Watchlist-Aenderungen wirkten nur nach App-Neustart - in 3 Phasen behoben
- **2026-08-01** — Zwei Zeit-Domaenen im Projekt (UTC-Daten vs. lokale Scheduler-Zeit) - bewusst KEIN Fix
- **2026-08-06** — Cron-Staggering NICHT gebaut: die DB-Sperren fallen in eigene App-Neustarts, das 06:30-Fenster ist seit zwei Tagen sauber
- **2026-08-06** — Vollcheck des Exports: zwei Pruefwerkzeuge, DB-Backup mit Rotation 7, und ein falsches Gruen im eigenen Skript
- **2026-08-06** — FX-Ableitung: Spannweite durch Interquartilsabstand ersetzt (4 statt 91 gueltige Tage); Z-3 arithmetisch bestaetigt
- **2026-08-06** — CAT: die EUR-Seite ist kaputt (Renditekorrelation 0,149 gegen Median 0,992) - Ursache Illiquiditaet, kein aktueller Schaden

### Methodik / Audits / Synthesen (13)

- **2026-07-17** — Spot-Regelwerk-Konsistenzprüfung nach dem Hebel-Fix
- **2026-07-19** — Konsistenzprüfung über ALLE
- **2026-07-24** — Liquiditätszonen Phase A - Backtest ohne Kante gefunden, Stufe 2 bewusst nicht gebaut
- **2026-07-25** — Echter KAIA-Hebel-Signal-Review (7 Funde) + INJ-Signal-Stabilität-Diskussion
- **2026-07-27** — NEAR-Hebel-Signal-Review -
- **2026-07-29** — Risikofaktoren-Häufung bei Hebel — Backtest durchgeführt, kein Gate gebaut
- **2026-08-03** — Regler-Audit: 36 von 202 Config-Schluesseln ohne Wirkung; Volatilitaet steckt laengst in RM-1
- **2026-08-03** — Messmethodik-Umbau (#617): FUENF eigene Fehler derselben Familie, drei Befunde widerrufen
- **2026-08-04** — Vier saubere Negativbefunde geschlossen (Score, Ausschuss, LLM1-Prompt, Selbstjustierung)
- **2026-08-05** — Der Dead-Loop aufgeloest: die Ursache liegt bei MISTRAL, nicht im Code (Replay-Nachweis)
- **2026-08-05** — Allocator gegen Zufall: an historischen Daten NICHT beantwortbar - Vorfilter blockierte die Messung
- **2026-08-06** — "Sprung bei CRV 4,0" gegengeprueft: es gibt keinen, und MFE >= 1R ist als Erfolgsmass untauglich
- **2026-08-06** — Widerspruch 3-5 % vs 5-8 % aufgeloest: beide Zahlen waren Survivorship-Artefakte, nur <2 % traegt

### Hebel- / Signal-Einzelfunde (12)

- **2026-07-18** — SOL in AZ-4-Tranchen + neuer Hebel-Prüfung-Toggle
- **2026-07-19** — echter KAITO-Fund - Geschwisterzeilen
- **2026-07-19** — 29× "Auto-Add unbekannter
- **2026-07-20** — `key_risks` bei Hebel-Signalen wurde bei
- **2026-07-22** — Alt-Coin-Marktphase fehlte im Hebel-Regelwerk (echter VIRTUAL-Fund)
- **2026-07-23** — Liquiditätszonen (Marketmaker-Konzept), Stufe 1
- **2026-07-25** — Baustein 1 - BTC-Relativwert (Korrelation/Beta/Relativstärke), Krypto-Relativwert-Bausteine komplett
- **2026-07-27** — Hebel-Pruefung-Toggle bei bereits gequeueten Kandidaten wirkungslos (KAITO-Fund)
- **2026-07-27** — HALTEN auf Symbol mit offener Hebel-Position zeigt jetzt deren aktuellen Stand (Abschnitt 1)
- **2026-07-27** — Grundsatzfix Teil 2 - derselbe
- **2026-07-31** — Hebel-Cooldown-Umgehungs-Bugfix (echter VIRTUAL-Fund) - angefragte_richtung
- **2026-08-01** — Spot-Verkaufs-Luecke identifiziert + Phase 1 "halte_kriterium scharfschalten" umgesetzt

---

## Chronologie

## Nachtrag (2026-07-17, gleicher Tag): Spot-Regelwerk-Konsistenzprüfung nach dem Hebel-Fix

**Auslöser:** Nutzer-Wunsch, dieselbe Detailanalyse, die zum 4-Punkte-Hebel-
Fix führte (siehe oben), auf das Spot-Regelwerk (`agent/krypto/risk_gate.py`,
`agent/krypto/analyst.py`, `agent/krypto/pipeline.py` — gilt größtenteils
auch für `agent/aktien/*`, das `risk_gate.py` wiederverwendet) anzuwenden,
explizit als Detailanalyse VOR jeder Implementierung.

**Ergebnis der Analyse (Stand + Meinung, 4 Punkte gegen die Hebel-
Nachbesserung gespiegelt):**

1. **Ungenutzte Forecast-Wahrscheinlichkeiten — echte Lücke, identisch zum
   Hebel-Fall.** `analyst.py` lässt sich bereits `forecast.bull/base/bear.
   probability_pct` liefern, `risk_gate.py::post_check()` hat das nie
   ausgewertet. **Umgesetzt** (siehe unten).
2. **Regime-Richtungs-Konflikt-Deckel — KEINE Lücke, bereits anders
   abgedeckt.** Hebel brauchte das wegen Liquidationsrisiko bei einer
   Position gegen das Regime. Spot/Aktien haben keinen Hebel/keine
   Liquidation — Kaufen im Bär-Regime ist oft die beabsichtigte Strategie
   (AZ-4-Tranchen-Akkumulation). R-5.10s bereits bestehende regime-skalierte
   `min_konfidenz_prozent` (85 % im `baer`, nur 60 % im `bulle`) leistet
   strukturell dasselbe. **Bewusst NICHT umgesetzt** — kein Fix nötig.
3. **HEBEL_SENKEN-Konkretisierung — nicht anwendbar.** Spot/Aktien haben
   keine Hebel-Reduktions-Aktion.
4. **Wiederholte, wirkungslose Empfehlungen — echte, aber geringere Lücke
   als bei Hebel.** Der bestehende "Überholt"-Mechanismus (`backward_
   tracking.py`) erkennt einen ANDEREN Fall (eine offene Empfehlung wird
   durch eine NEUERE Analyse überholt), nicht "VERKAUFEN/TAUSCHEN wiederholt
   empfohlen, Position aber weiterhin gehalten". Geringere Dringlichkeit als
   bei Hebel (kein eskalierendes strukturelles Risiko wie Liquidation, nur
   eine verpasste Gelegenheit). **Umgesetzt** (siehe unten).

**Umsetzung Punkt 1 — Gegenszenario-Deckel (`risk_gate.py::post_check()`):**
bei KAUFEN/NACHKAUFEN wird zusätzlich zur bestehenden Konfidenz-Skalierung
geprüft, ob `forecast.bear.probability_pct` die neue Schwelle
`risiko.gegenszenario_wahrscheinlichkeit_schwelle_prozent` (Startwert 35)
erreicht/überschreitet — falls ja, wird die bereits konfidenz-skalierte
Positionsgrößen-Obergrenze zusätzlich multiplikativ auf
`risiko.gegenszenario_positionsgroesse_deckel_anteil` (Startwert 0.5, d.h.
50 %) reduziert. Bewusst **kein hartes Veto** wie beim Hebel-Pendant
(`risiko.hebel.gegenszenario_hebel_deckel`) — Spot/Aktien tragen kein
Liquidationsrisiko, eine Korrektur der Größe (bestehende Philosophie dieser
Funktion) reicht aus. Wirkt automatisch auch für Aktien-Signale, da
`agent/aktien/pipeline.py` dieselbe `post_check()`-Funktion aufruft.

**Umsetzung Punkt 4 — Wiederholungs-Erkennung (`analyst.py::build_facts()` +
`pipeline.py::generate_signal()`):** neuer Fakt `vorherige_empfehlung` —
`pipeline.py` lädt vor jedem neuen Signal-Lauf das zuletzt gespeicherte
Signal für dasselbe Symbol (`db.get_latest_signal()`) und reicht es an
`build_facts()` durch. War die letzte Aktion VERKAUFEN oder TAUSCHEN
(NICHT KAUFEN/NACHKAUFEN — eine ignorierte Kauf-Empfehlung ist risikoneutral,
keine Warnung wert), UND wird das Asset laut aktuellem Bestand weiterhin
gehalten, UND sind mindestens 4 Stunden vergangen (Grace-Period, bewusst
großzügiger als Hebels 2 Std. — Spot-Signale laufen manuell oder über einen
mehrstündigen Cooldown, kein 15-Min-Trigger-Takt), wird der Fakt gesetzt.
SYSTEM_PROMPT-Regel 21 verlangt vom Modell, den Umstand zu benennen statt
die Begründung wortgleich zu wiederholen. **Bewusst NUR in `agent/krypto/
analyst.py` umgesetzt, NICHT in `agent/aktien/analyst.py`** (eigene, separate
`build_facts()`/SYSTEM_PROMPT-Kopie) — der Nutzer sprach explizit von
"Spot"; Aktien-Analog auf Anfrage nachrüstbar.

**Config (`Basisinfos/config.yaml`, unter `risiko:`, NICHT `risiko.hebel:`):**
```yaml
gegenszenario_wahrscheinlichkeit_schwelle_prozent: 35
gegenszenario_positionsgroesse_deckel_anteil: 0.5
```
Beide Startwerte unkalibriert, identisch zum Hebel-Pendant übernommen — nach
echten Betriebsdaten anzupassen.

**Verifiziert:** 7 synthetische Testfälle (Gegenszenario-Deckel greift bei
hoher/nicht bei niedriger Bear-Wahrscheinlichkeit, Rückwärtskompatibilität
ohne `forecast`-Feld; Wiederholungs-Fakt gesetzt bei VERKAUFEN vor 5 Std. +
Position gehalten, NICHT gesetzt innerhalb der Grace-Period, NICHT gesetzt
wenn Position nicht mehr gehalten wird, NICHT gesetzt bei KAUFEN als letzter
Aktion) plus ein echter Kompatibilitätstest gegen eine Kopie der Produktions-
DB (`db.get_latest_signal()` auf 5 echten Symbolen, reale ISO-Zeitstempel
korrekt geparst, reale `forecast_bear_prob_pct`-Werte 20-30 % liegen
plausibel unter der neuen 35 %-Schwelle).

## Nachtrag (2026-07-17, gleicher Tag): RM-4 (Cash-Reserve) war rueckwaerts- statt vorwaertsgerichtet

**Auslöser:** Nutzer-Wunsch, das Thema Spot-Regelwerk breiter zu denken -
nicht nur Hebel-Punkte auf Spot uebertragen, sondern zusaetzliche,
eigenstaendige Luecken und Eigenheiten des Spot-Markts identifizieren.

**Fund:** RM-4 (`risk_gate.py::pre_check()`) prueft bisher nur, ob die
Cash-Reserve JETZT SCHON unter dem Minimum liegt (`cash_value_usd <
required_reserve_usd`) - anders als RM-1 (berechnet eine maximale
Positionsgroesse aus dem Risikobudget) und RM-2 (deckelt zusaetzlich auf das
verbleibende Allokations-Headroom), die beide VORWAERTSGERICHTET sind. RM-4
rechnete nie durch, ob die konkret vorgeschlagene Positionsgroesse SELBST die
Reserve unter das Minimum druecken wuerde - ein Kauf, der die Reserve von
z. B. 21 % auf 15 % senkt, wurde anstandslos durchgelassen; erst der
NAECHSTE Kaufversuch haette die dann bereits unterschrittene Reserve
gesehen. Verwandter, nicht behobener Nebeneffekt (bewusst zurueckgestellt,
siehe unten): mehrere KAUFEN-Empfehlungen im selben Batch-Lauf
(`signal_batch.py`/Budget-Allocator) werten unabhaengig voneinander gegen
denselben `db.get_all_holdings()`-Snapshot aus - keine "weiss" von den
anderen vorgeschlagenen Kaeufen desselben Laufs.

**Fix (umgesetzt):** analog zu RM-2s Allokations-Headroom wird jetzt ein
Cash-Reserve-Headroom (`cash_value_usd - required_reserve_usd`) berechnet
und per `min()` direkt in `max_position_size_usd` eingerechnet, sobald RM-4
selbst nicht bereits vetoed (im "OK"-Zweig) - ein einzelner Kauf kann die
Reserve dadurch nicht mehr unter das Minimum druecken, unabhaengig davon,
was sonst im Portfolio passiert. Kein neues Feld in `RiskPreCheckResult`
noetig (reine `max_position_size_usd`/`_eur`-Anpassung, wie bei RM-1/RM-2).

**Bewusst zurueckgestellt:** die Batch-Kumulierung (mehrere gleichzeitige
Kaufempfehlungen im selben Lauf, die sich gegenseitig nicht "sehen") -
Nutzer moechte hierzu erst mehr Informationen, bevor entschieden wird
(z. B. wie haeufig Nutzer tatsaechlich mehrere Tages-Empfehlungen gleichzeitig
exekutiert). Deutlich aufwaendiger als Fix 1 (braeuchte einen laufenden
Spend-Akkumulator ueber den gesamten Batch-Lauf), fuer einen eher seltenen
Grenzfall.

**Verifiziert:** 2 synthetische Testfaelle gegen ein handgebautes Portfolio
(BTC-Allokation bewusst unter dem RM-2-Limit gehalten, um RM-4 isoliert zu
pruefen) - (1) knappe Cash-Reserve (21 % bei 20 % Minimum, nur 100 USD
Headroom): Obergrenze korrekt auf ~100 USD gedeckelt, obwohl RM-1 rechnerisch
110.600 USD erlaubt haette; (2) reichlich Cash-Reserve: RM-1/RM-2 bleiben
weiterhin die bindende (kleinere) Grenze, RM-4 greift nicht faelschlich ein.

## Nachtrag (2026-07-18): Konfidenz-Kalibrierung nach dem echten CAT-Fall (fünf Bausteine A-E)

**Auslöser:** Nutzer teilte ein echtes, per E-Mail zugestelltes Spot-KAUFEN-
Signal für "CAT — Simon's Cat" (Konfidenz 80 %, Regime baer) zur eigenen
Experten-Durchsicht. Eigene Bewertung: schwach/kein starker Kauf -
widersprüchliche technische Konfluenz ("EMA-Ordnung bearish, aber MACD/RSI
bullish") wurde von der KI zwar in der Begründung erwähnt, aber NICHT in der
Konfidenz-Zahl (80 %) berücksichtigt; CRV lag nur knapp über der 2.0-
Pflichtgrenze (~2,08), was das binäre CRV-Gate bisher identisch zu einem
CRV von 4,0 behandelte. Nutzer bestätigte diese Einschätzung als deutlich
kritischer/besser als die Systembewertung selbst und beauftragte eine
umfassende Nachbesserung ("heute müssen wir versuchen umfangreiche
Verbesserungen einzuführen") - fünf Bausteine A-E, alle am selben Tag
umgesetzt. Gleichzeitig wurden zwei unabhängige E-Mail-Bugs gefunden und
behoben (siehe eigener Abschnitt oben: wissenschaftliche Notation bei sehr
kleinen Preisen, fehlende Regime-/Risiken-/Halte-Kriterium-Felder).

**A — Technischer-Konflikt-Deckel (`risk_gate.py::post_check()` +
`hebel_risk_gate.py::post_check_hebel()`):** `indicators/calculations.py::
summarize_confluence()` klassifiziert Indikator-Übereinstimmung bereits
deterministisch als `"bullish"|"bearish"|"neutral"|"gemischt"` - der
"gemischt"-Fall (weder bullish noch bearish dominiert) existierte exakt für
den CAT-Fall, wurde aber nirgends im Risiko-Gate ausgewertet. Jetzt: ist
`confluence.overall_bias == "gemischt"`, wird die Positionsgrößen-Obergrenze
(Spot) zusätzlich multiplikativ auf `technischer_konflikt_deckel_anteil`
(Config, Default 0.6) reduziert, bzw. bei Hebel als zusätzlicher Deckel-
Kandidat (`technischer_konflikt_hebel_deckel`, Default 3.0x) in die
bestehende `_hebel_deckel_kandidaten()`/`min()`-Logik eingereiht (Muster aus
dem Hebel-4-Punkte-Fix vom Vortag, siehe oben). Beide Pfade sind rein
deterministisch - unabhängig davon, ob das Modell den Widerspruch selbst
benennt.

**B — CRV-Distanz-abhängige Positionsgrößen-Skalierung ("CRV-Knapp-
Deckel"):** `CRV_MINIMUM = 2.0` war bisher ein binäres Gate (2,01 und 4,0
identisch behandelt). Neu: liegt `crv < CRV_MINIMUM * (1 +
crv_knapp_schwelle_relativ)` (Config, Default 0.2 → Schwelle 2.4), greift
eine weitere multiplikative Reduktion (`crv_knapp_positionsgroesse_
deckel_anteil`, Spot Default 0.6) bzw. ein weiterer Hebel-Deckel-Kandidat
(`crv_knapp_hebel_deckel`, Default 4.0x). Alle vier Spot-Deckel (Konfidenz-
Skalierung, Gegenszenario, Konflikt, CRV-Knapp) sind Geschwister-Blöcke, die
sich multiplikativ verketten (verifiziert: alle vier gleichzeitig aktiv
ergaben korrekt `1000 × 0.5 × 0.5 × 0.6 × 0.6 = 90 USD`); bei Hebel bleibt
es beim bestehenden `min()`-über-alle-Kandidaten-Prinzip (der kleinste
Deckel-Wert bindet, kein Produkt).

**C — bereits durch A+B abgedeckt:** die vom Nutzer gewünschte CRV-Distanz-
abhängige Skalierung ist identisch mit Baustein B (dieselbe Mechanik löst
beide Anliegen), kein separater Code-Pfad nötig.

**D — Gegenargument-Pflichtfeld statt zweitem LLM-Call (`analyst.py`
[Krypto+Aktien] + `hebel_analyst.py`):** Nutzer-Frage, ob eine adversariale
Selbstkritik zwingend zwei getrennte LLM-Calls braucht - Antwort: nein, ein
neues PFLICHT-Schema-Feld `gegenargument` wurde bewusst VOR `confidence_pct`
im JSON-Schema platziert. Da LLM-APIs JSON überwiegend sequenziell links-
nach-rechts erzeugen, "sieht" das Modell sein eigenes, bereits geschriebenes
Gegenargument, wenn es die Konfidenz-Zahl committet - eine kostengünstige
Annäherung an Chain-of-Thought-Selbstkorrektur ohne zweiten Aufruf (relevant
angesichts des knappen ~15-18-Calls/Tag-Groq-Budgets, siehe Memory
project_batch_signal_berechnung.md). Neue SYSTEM_PROMPT-Regel (22 in
`agent/krypto/analyst.py`, 18 in `agent/aktien/analyst.py`, 13 in
`agent/krypto/hebel_analyst.py`) verlangt das STÄRKSTE Gegenargument (nicht
ein Feigenblatt) und verbietet explizit die Kombination "genuin starkes
Gegenargument + Konfidenz > 75 %". `_validate()`/`_validate_hebel()`
erzwingen eine Mindestlänge (15 Zeichen) - ein leeres oder trivial kurzes
Gegenargument macht die gesamte Antwort ungültig (`AnalystResponseInvalid`).
Neues additiv migriertes Feld `gegenargument` (TEXT, nullable) auf `Signal`
und `HebelSignal` (`database/models.py` + `database/db.py::
_migrate_gegenargument_columns()`).

**E — Historische Trefferquote als Kalibrierungs-Fakt
(`backward_tracking.py::compute_win_rate_fact()`):** neue, rein lesende
Funktion aggregiert bereits aufgelöste Signale (`outcome_status` in
`take_profit_erreicht`/`stop_loss_erreicht`/`liquidation_wahrscheinlich`)
getrennt für `signals` ("spot" - Krypto UND Aktien zusammen, gleiche
Vereinfachung wie in `compute_provider_performance()`, Stichprobe zu klein
für eine weitere Aufspaltung) und `hebel_signals` ("hebel"). Gibt `None`
zurück, solange keine Signale aufgelöst sind (aktuell der Fall - reine
Infrastruktur). Unter `_MIN_SAMPLE_FUER_AUSSAGE = 15` Signalen bekommt das
Modell einen expliziten Ehrlichkeits-Hinweis im Fakt selbst
(`hinweis`-Feld), der vor Überschätzung einer kleinen Stichprobe warnt -
bewusst NUR eine grobe Gesamtzahl, kein Per-Asset/Per-Regime-Split. Neuer
Fakt `historische_erfolgsquote` in `build_facts()` (Krypto + Aktien) und
`build_hebel_facts()`, mit neuer SYSTEM_PROMPT-Regel (23/19/14), die das
Modell anweist, die Zahl NUR als schwaches Zusatzindiz zu behandeln.

**Config (`Basisinfos/config.yaml`):**
```yaml
# unter risiko: (Spot/Aktien)
technischer_konflikt_deckel_anteil: 0.6
crv_knapp_schwelle_relativ: 0.2
crv_knapp_positionsgroesse_deckel_anteil: 0.6

# unter risiko.hebel:
technischer_konflikt_hebel_deckel: 3.0
crv_knapp_schwelle_relativ: 0.2
crv_knapp_hebel_deckel: 3.0
```
Alle Startwerte unkalibriert (analog zu den bereits bestehenden Gegenszenario-
Deckeln) - nach echten Betriebsdaten anzupassen.

**Verifiziert:** Import-Smoke-Test aller geänderten Pipelines (keine
Zirkelimporte); synthetische Tests für `compute_win_rate_fact()` (leere DB →
`None`, kleine Stichprobe → Ehrlichkeits-Hinweis, große Stichprobe → kein
Hinweis, Hebel-Liquidation zählt als Fehlschlag); `gegenargument`-Validierung
(gültig akzeptiert, zu kurz/fehlend abgelehnt) für Spot-Krypto UND Hebel;
Konflikt-Deckel + CRV-Knapp-Deckel-Zusammenspiel bei Spot (multiplikativ,
alle vier Deckel gleichzeitig korrekt verkettet) und bei Hebel (`min()`-
Logik, korrekter bindender Grund im Hinweistext); echter Migrations- und
Kompatibilitätstest gegen eine Kopie der Produktions-DB (76 Spot- +
5 Hebel-Signale, neue Spalte vorhanden, `Signal(**dict(row))`/
`HebelSignal(**dict(row))` funktionieren mit `gegenargument=None` für
Alt-Zeilen, `compute_win_rate_fact()` liefert dort korrekt `None`).

**Bewusst zurückgestellt (eigene, dedizierte Session):** der vom Nutzer als
Favorit genannte historische Makro-Konstellationsvergleich (DXY/Aktien-
Blase/Ölpreis/Zinsen gegen historische Perioden mit bekanntem Ausgang) - als
mögliche zusätzliche Kalibrierungs-Basis für Spot/Hebel/andere Assets neben
Bär/Bulle/Regime identifiziert, aber bewusst NICHT im selben Aufwasch
umgesetzt (methodische Komplexität, siehe Memory
project_historischer_makro_konstellationsvergleich_idee.md). Ebenfalls
zurückgestellt: Wiederholungs-Erkennung (Punkt 4 der letzten Runde) für
Aktien nachrüsten - wurde beim Portieren von B+D nach `agent/aktien/
analyst.py` nicht mit angefragt, bleibt als latenter Punkt vorgemerkt.

## Nachtrag (2026-07-18, gleicher Tag): Historischer Makro-Konstellationsvergleich umgesetzt

**Auslöser:** Nutzer wollte das oben zurückgestellte Thema nicht lange
aufschieben ("möchte ich nicht zu lange nach hinten schieben - also asap
angehen") und beauftragte zwei Recherche-Stränge: was lässt sich frei
verfügbar nutzen, was muss selbst gebaut werden - sowie eine eigenständige
Krypto-Bewertung statt der Aktien-Methodik 1:1 zu übertragen.

**Recherche-Ergebnis (Build vs. Buy):** kein kostenloses fertiges Tool macht
"aktuelle Konstellation → historisches Analog → Wahrscheinlichkeit" als
nutzbaren Service. MacroMicro-API wäre das einzige nahe dran, kostet aber
5.000 $/Jahr - für dieses Nur-kostenlose-Werkzeuge-Projekt nicht tragbar.
Also Eigenbau, aber auf Basis bereits vorhandener, bereits integrierter
kostenloser Datenquellen (FRED, yfinance, blockchain.com) statt neuer
Abhängigkeiten - reduziert den Bauaufwand erheblich.

**Datenquellen (alle bereits im Projekt integriert, nur neu genutzt):**
FRED (`api/macro.py::get_fred_history()`) für DXY-Ersatz (`DTWEXBGS`, seit
2006), Fed Funds Rate (`FEDFUNDS`, seit 1954), 10-Jahres-Rendite (`DGS10`,
seit 1962), CPI (`CPIAUCSL`, seit 1913, YoY selbst berechnet), Ölpreis WTI
(`WTISPLC`, monatlich seit 1946 - bewusst länger zurückreichend als das
sonst im Projekt genutzte `DCOILWTICO`, wichtig für die 1970er-
Ölschock-Ära); yfinance (`api/yfinance_history.py::get_full_price_history()`)
für die S&P-500-Vollhistorie (^GSPC, seit 1927); blockchain.com
(`api/onchain.py::get_btc_full_price_history()`) für die BTC-Vollhistorie
seit 2009.

**Bewusst KEIN Shiller-CAPE** (methodisch der etabliertere Bewertungs-Proxy,
aber Yale liefert nur eine fragile Legacy-`.xls`-Datei ohne bestehende
Parser-Infrastruktur - `openpyxl` kann nur `.xlsx`, kein `xlrd`
installiert). Stattdessen: eine neue, selbst berechnete log-linear
Trend-Abweichung des S&P 500 (`indicators/calculations.py::
compute_log_linear_trend_deviation_series()`) - Regression von
log10(Preis) auf LINEARE Zeit (Jahre seit erstem Datenpunkt), bewusst
anders als das bestehende `compute_btc_log_regression_risk()` (log10(Preis)
auf log10(Tage seit Genesis) - ein Power-Law-Adoptionsmodell, das für einen
Aktienindex methodisch nicht passt). Synthetisch mit einer
10%-Jahr-Wachstumskurve gegengeprüft (Regression erkannte die Rate korrekt
wieder).

**Architektur:** neues Modul `agent/krypto/makro_analog.py` mit zwei neuen
DB-Tabellen (`makro_historie_monat` - monatliche Zeitreihe der 6
Konstellations-Dimensionen + SPX-/BTC-Schlusskurse, additiv gemerged wie
`macro_snapshot`; `makro_analog_ergebnis` - gecachtes Tages-Ergebnis als
JSON-Blob). Neuer täglicher Scheduler-Job `makro_analog_job()` (06:30, nach
Backward-Tracking) frischt die Historie auf und berechnet die Top-5
historischen Analoge neu - die teure Berechnung läuft NICHT pro Signal,
`build_facts()`/`build_hebel_facts()` lesen nur das gecachte Ergebnis
(`get_cached_makro_analog_fact()`).

**Ähnlichkeitsmetrik:** Euklidischer Abstand über Z-Score-normalisierte
Dimensionen, fehlend-Werte-tolerant (fehlt eine Dimension bei Kandidat ODER
aktuellem Monat, wird sie für DIESEN Vergleich übersprungen, nicht als 0
angenommen - gleiches Prinzip wie `risk_gate.py::_portfolio_values_usd()`).
**Live-Fund beim ersten echten Testlauf:** ohne Zusatzregel bestand die
Top-5-Liste aus fast identischen, nur wenige Monate auseinanderliegenden
Kandidaten (z. B. Feb/Mär/Mai/Jun/Jul desselben Jahres) - autokorreliertes
Rauschen statt unabhängiger historischer Vergleichspunkte, weil benachbarte
Monate fast immer ähnliche Makro-Werte haben. Fix: derselbe
`mindest_abstand_monate`-Parameter (Default 24) erzwingt jetzt zusätzlich
einen Mindestabstand ZWISCHEN den ausgewählten Analogen untereinander, nicht
nur gegenüber "jetzt". Nach dem Fix lieferte derselbe echte Testlauf fünf
genuin unabhängige Analoge über 20 Jahre verteilt (2006, 2015, 2018, 2022,
2024) mit einer plausibel breiten Streuung der Forward-Renditen (S&P
6-Monats-Vorwärtsrendite der Analoge reichte von −20,9 % bis +9,7 %).

**Krypto-Sonderbehandlung (Nutzer-Entscheidung):** BTC hat nur ~3 volle
Halving-Zyklen mit statistischem Gewicht, und diese 3 Zyklen waren
makro-mäßig selbst nicht vergleichbar (Nahe-Null-Zinsen 2013-2021 vs.
heute) - ein aggregiertes "BTC-Forward-Rendite über die Top-N-Analoge"-Feld
wäre Pseudo-Statistik mit irreführender Präzision. Deshalb liefert
`summarize_analogs_for_facts()` BTC-Forward-Renditen NUR pro einzelnem
Analog (null bei Analogen vor BTCs Existenz), aber KEIN aggregiertes Feld -
das ist STRUKTURELL so (das Feld existiert schlicht nicht im Fakt-Dict),
nicht nur per Prompt-Anweisung unterdrückt (P-10-Philosophie: das Modell
wird nie blind vertraut, die Versuchung wird also gar nicht erst als
fertiger Fakt angeboten). Für den S&P 500 WIRD ein Median-Aggregat über die
Top-N-Analoge geliefert - dort ist die Stichprobentiefe (Jahrzehnte, viele
unabhängige Analoge) deutlich größer und methodisch tragfähiger.

**Prompt-Integration:** neuer Fakt `historischer_makro_vergleich` in allen
drei `build_facts()`/`build_hebel_facts()`-Funktionen (Krypto-Spot, Aktien,
Hebel), mit je einer neuen SYSTEM_PROMPT-Regel (24 in `agent/krypto/
analyst.py`; 20 in `agent/aktien/analyst.py`; 15 in `agent/krypto/
hebel_analyst.py`). Krypto/Hebel-Formulierung verbietet
explizit, `btc_forward_*`-Werte als belastbare Statistik zu behandeln;
Aktien-Formulierung erlaubt die Nutzung von `spx_median_forward_*` als
groben Kalibrierungs-Input, mit Streuungs-Warnhinweis.

**Config (`Basisinfos/config.yaml`, neue Sektion `makro_analog:`):**
```yaml
top_n_analoge: 5
mindest_abstand_monate: 24
mindest_dimensionen: 3
```

**Verifiziert:** synthetischer Regressionstest (10%-Jahr-Wachstumskurve
korrekt zurückgerechnet); Migrations-/CRUD-Test gegen eine Kopie der
Produktions-DB (Merge-Verhalten, Cache-Schreiben/-Lesen); vollständiger
echter End-to-End-Lauf gegen FRED (5 Reihen, ~21 s), yfinance (^GSPC-
Vollhistorie seit 1927) und blockchain.com (BTC seit 2009) - 1.184 Monate
Historie aufgebaut, Analog-Suche + Fakt-Erzeugung geprüft; Diversitäts-Fix
gegen dieselben echten Daten erneut verifiziert (alle 5 Analoge ≥ 24 Monate
auseinander UND ≥ 24 Monate vor "jetzt"); 4 synthetische Edge-Case-Tests
(leere Historie, ein einzelner Monat, konstante Dimension ohne Streuung,
zu wenige überlappende Dimensionen) - alle degradieren graceful (`None`/
leere Liste) statt zu crashen; vollständiger Import-Smoke-Test aller
geänderten Pipelines nach der Verdrahtung.

**Bewusst zurückgestellt:** kein UI-Element für die Analoge selbst (z. B.
ein neuer Tab oder eine Karte im Regime-Tab) - der Fakt fließt direkt in
die LLM-Signale ein, eine separate Visualisierung war nicht Teil des
heutigen Auftrags und kann bei Bedarf nachgerüstet werden.

## Nachtrag (2026-07-18, gleicher Tag): Rohstoff-Pipeline (Phase 2) + Portfolio-Hedge-Logik

**Auslöser:** Nutzer bekräftigte, die Multi-Asset-Roadmap Phase 2-4
(Rohstoffe/ETF/Discovery, siehe Memory project_multi_asset_erweiterbarkeit.md)
als nächstes Großthema angehen zu wollen, und ergänzte explizit die
"Bitpanda-Sonderkonstellation und Absicherung" - da Bitpanda keine echten
Krypto-Short-Positionen anbietet, sollten die bereits gehaltenen inversen/
gehebelten Aktienindex-ETFs (DBPK, 3QSS) als praktischer Kompromiss-Hedge
gegen das GESAMTE Portfolio (nicht nur Aktien) eine eigene Bewertungslogik
bekommen. Nutzer wählte den vollen Durchstich beider Bausteine am selben Tag.

### Baustein 1: Rohstoff-Pipeline (`agent/rohstoff/`)

Neues, eigenständiges Modul (gleiche Architektur-Entscheidung wie bei Aktien -
kein verallgemeinertes Framework). Vier ETCs (OD7N Silber, OD7H Gold, OD7C
Kupfer, OD7L Erdgas, `assetklasse: rohstoffe`). Kein KGV-Äquivalent für
physische Rohstoffe - stattdessen `makro_ueberlagerung` (10J-TIPS-Realrendite
DFII10, Dollar-Index DTWEXBGS, Industrieproduktion INDPRO - alle via FRED)
und `positionierung` (CFTC-COT-Report, "Managed Money"-Netto-Positionierung,
neues Modul `api/cftc_cot.py`, kostenlose Socrata-API, kein Key nötig).

**Datenquellen-Recherche (Build vs. Buy):** kostenlose, echte APIs identifiziert
für COT (`publicreporting.cftc.gov`, Dataset `72hh-3qpy`, live verifiziert für
alle 4 Rohstoffe) und FRED-Realrendite/Dollar/Industrieproduktion. Bewusst
NICHT einbezogen (dokumentierte Lücke, spätere Erweiterung möglich): EIA-
Erdgaslager (bräuchte neuen API-Key, nicht heute testbar), COMEX-/LME-
Lagerbestände (Dateiformat-Risiko, gleiche Kategorie wie das bereits
verworfene Shiller-CAPE), ETF-Gold-/Silber-Bestandsflüsse (CSV-Format
ungeprüft).

**Kritischer Live-Fund bei der Verifikation:** die WisdomTree-ETC-
Börsennotierungen selbst (`asset.yfinance_symbol`) liefern über yfinance
KEINE `.history()`-Daten - nur `fast_info` (aktueller Kurs) funktioniert,
dieselbe Einschränkung, die 2026-07-09 bereits für OD7N/3QSS dokumentiert
wurde (siehe Memory project_multi_asset_yfinance_symbols.md), hier aber
erstmals fest eingebaut vorausgesetzt und dadurch übersehen. **Fix:**
technische Analyse (EMA/MACD/RSI/Bollinger/ATR/Fibonacci/S&R) wird stattdessen
aus dem liquiden, kontinuierlichen Futures-Kontrakt abgeleitet, den das ETC
nachbildet (GC=F/SI=F/HG=F/NG=F, 25+ Jahre Historie, live verifiziert).

**Zweiter, direkt daraus folgender Fund:** Futures- und ETC-Kurs liegen auf
VÖLLIG unterschiedlichen absoluten Preisskalen (z. B. Gold-Future ~4.000
USD/Unze vs. das Bruchteils-ETC bei ~18-20 USD) - ohne Korrektur wären
EMA/Bollinger/ATR/Support-Resistance/Fibonacci-Level absolute Preis-Level auf
der FALSCHEN Skala, eine daraus abgeleitete Stop-Loss-Zone wäre um
Größenordnungen falsch. **Fix:** `_rescale_ohlc_zum_etc_kurs()` skaliert die
GESAMTE Futures-Historie mit einem einzigen, heute gültigen Faktor (ETC-Kurs
/ letzter Futures-Kurs) auf die ETC-Größenordnung, bevor sie in
`build_technical_snapshot()` geht - technische Muster (Trendrichtung,
Support/Resistance-Abstände in Prozent) bleiben dabei unverändert, nur die
absolute Preisachse verschiebt sich. Live verifiziert: ATR/Preis-Verhältnis
nach der Korrektur für alle 4 ETCs plausibel im Bereich 0,018-0,045 (vorher
absurd, z. B. Gold-ATR von ~40 USD auf einen ~18-USD-Kurs angewendet).

**Dritter Fund (Robustheits-Lücke, ebenfalls behoben):** `price_usd` wird für
diese EUR-notierten ETCs erst nachträglich aus `price_eur * eur_usd_fx_rate`
abgeleitet und kann fehlen, wenn beim letzten Preisabruf kein aktueller FX-Kurs
vorlag - ohne explizites Gate hätte das Fehlen von `price_usd` die Skalierung
still auf die (falsche) Futures-Skala zurückfallen lassen. Neuer Gate-Check
VOR der Skalierung: fehlt `price_usd`, wird das Signal als `gate_passed=False`
mit klarem Grund abgelehnt statt eine falsch skalierte Analyse zu erzeugen.

**Verifiziert:** Live-Test aller 4 ETCs gegen echtes FRED/CFTC/yfinance
(Fakten-Generierung + Skalierungs-Korrektheit), ein echter End-to-End-Lauf mit
echtem Groq-Call (OD7H/Gold: HALTEN, 60 % Konfidenz, korrekt begründet mit
gemischter Konfluenz + belastenden Makro-Faktoren + COT-Positionierung).

### Baustein 2: Portfolio-Hedge-Logik (`agent/hedge/`)

Bewusst ANDERS architektiert als Aktien/Rohstoff: KEINE
Einzeltitel-Technikanalyse (3QSS hat wie die Rohstoff-ETCs keine
yfinance-Historie, UND ein Hedge-Instrument sollte ohnehin nicht nach eigener
technischer Stärke bewertet werden, sondern danach, wie viel ungesichertes
PORTFOLIO-Risiko es gerade abdeckt). KEIN `risk_gate.pre_check()`/
`post_check()` (RM-1/2/4/5 + CRV-Pflicht sind für profitorientierte
Directional-Wetten gebaut, nicht für eine Absicherungs-Position) - eigener,
einfacherer Deckel.

**Kernmechanik:** `_compute_portfolio_exposure()` berechnet die ungesicherte
Long-Exposure (Portfolio-Wert ohne Hedge-Instrumente und ohne
Cash-Äquivalente) sowie die aktuelle Hedge-Abdeckung (Summe über ALLE
gehaltenen Hedge-Instrumente, je mit ihrem Hebelfaktor multipliziert - 1 USD
in einem 3x-Short-ETF deckt effektiv 3 USD Long-Exposure ab). Ein
konfigurierbares Ziel-Maximum (`hedge.max_abdeckung_anteil`, Default 1.0 =
100 %) begrenzt deterministisch, wie viel zusätzliche Hedge-Position
vorgeschlagen werden darf.

**Live-Fund während der Verifikation:** `_portfolio_values_usd()` lässt ein
Symbol ohne bekannten Preis (P-10) einfach aus der Wertesumme weg - ein
ANDERES, tatsächlich gehaltenes Hedge-Instrument mit fehlendem `price_usd`
hätte die Gesamt-Abdeckung dadurch STILLSCHWEIGEND unterschätzt (0 statt des
echten Werts), was einen KAUFEN/NACHKAUFEN-Vorschlag zu einer unbemerkten
Übersicherung hätte führen können. **Fix:** `fehlende_preise`-Erkennung +
explizite Warnung im Fakt (`berechnung_unsicher_fehlende_preise`) + das
verbleibende Hedge-Budget wird in diesem Fall vorsorglich auf 0 gedeckelt
(VERKAUFEN/HALTEN bleiben davon unberührt, nur ein Hedge-AUFBAU wird
blockiert). Live gegen das echte Portfolio verifiziert: mit vollständigen
Preisen korrekt 1.768 USD Gesamt-Abdeckung (1.739 DBPK × 0,163 × 2 + 218
3QSS × 1,836 × 3 = 12,7 % der 13.936 USD Long-Exposure), ohne einen der
beiden Preise korrekt auf 0 USD Budget gedeckelt mit klarer Warnung.

**Volatility-Decay-Warnung:** neue SYSTEM_PROMPT-Regel verlangt, gehebelte/
inverse ETFs NIE als Buy-and-Hold-Position zu behandeln (tägliches
Rebalancing erzeugt bei Seitwärtsbewegung strukturellen Wertverlust,
unabhängig von der Richtung des zugrunde liegenden Index) - explizit in
`key_risks`/`long_reasoning.risiko` zu benennen.

**Verifiziert:** Facts-Generierung + Exposure-Berechnung gegen echtes
Portfolio (mit und ohne fehlende Preise), ein echter End-to-End-Lauf mit
echtem Mistral-Call (DBPK: HALTEN, 60 % Konfidenz, korrekt begründet mit
12,7 % bestehender Abdeckung + inaktivem Aktien-Bärenmarkt-Indikator +
Decay-Erwägung).

**Config (`Basisinfos/config.yaml`):**
```yaml
hedge:
  max_abdeckung_anteil: 1.0
```

**UI-Wiring:** `ui/signals_view.py` verzweigt jetzt nach `assetklasse ==
"rohstoffe"` (→ `agent/rohstoff/pipeline.py`) bzw. Symbol-Zugehörigkeit zu
`agent.hedge.pipeline.SYMBOL_ZU_HEBEL_FAKTOR` (→ `agent/hedge/pipeline.py`),
zusätzlich zur bestehenden Aktien-/Krypto-Verzweigung.

**Bewusst zurückgestellt:** Themen-ETFs (Phase 3) und Discovery (Phase 4) der
Multi-Asset-Roadmap - eigene, spätere Themen. EIA-Erdgaslager/COMEX-Lagerbestände/
ETF-Bestandsflüsse als Rohstoff-Datenquellen-Erweiterung (siehe oben).

## Nachtrag (2026-07-18, gleicher Tag): Bugfix Bitpanda-Listing-Spalte fuer Aktien/Rohstoffe/Hedge

Nutzer-Fund: die Watchlist zeigte fuer alle Nicht-Krypto-Assets (Aktien, ETFs,
Rohstoffe/ETCs) in der "Bitpanda"-Spalte hartkodiert "-", statt eines echten
✓/✗-Status. Ursache war eine seit 2026-07-09 bestehende, seit dem
2026-07-16-Ausbau ueberholte Annahme in `ui/app.py::_refresh_watchlist_from_db()`:
"Bitpanda-Listing-Check ergibt fuer Nicht-Krypto keinen Sinn". Das stimmte zum
Zeitpunkt des urspruenglichen Kommentars (reines Krypto-Multi-Asset-Tracking),
war aber seit `api/bitpanda.py::get_listed_non_crypto_assets()` (2026-07-16,
schliesst die Aktien-Pipeline-Luecke) nicht mehr aktuell: `agent/aktien/pipeline.py`
und `agent/rohstoff/pipeline.py` berechnen den echten Listing-Status seither
laengst fuer den Bitpanda-Veto (`risk_gate.py::pre_check()`) - er wurde nur nie
in der allgemeinen Watchlist-UI angezeigt.

**Fix:** `ui/app.py` laedt jetzt zusaetzlich zum bestehenden Krypto-Katalog
(`self._bitpanda_assets`) den Nicht-Krypto-Katalog
(`self._bitpanda_non_crypto_assets`, ueber `get_listed_non_crypto_assets()`,
gleiches P-10-Fehlschlag-Verhalten: `None` bei Abrufsfehler statt falschem
Wert). Die Zeilen-Render-Logik waehlt den passenden Katalog nach
`asset.assetklasse` und nutzt fuer beide denselben `bitpanda_is_listed()`-
Vergleich - keine getrennte Logik mehr fuer Krypto vs. Nicht-Krypto. Deckt
damit einheitlich Aktien (`stock`), Rohstoff-ETCs (`etc`) UND die
Hedge-ETFs DBPK/3QSS (`etf`, `NON_CRYPTO_ASSET_GROUPS` in `api/bitpanda.py`) ab.

**Verifiziert:** Logik-Smoke-Test (Krypto BTC/ETH, Aktie PLTR, Rohstoff-ETC
OD7H, Hedge-ETF DBPK, unbekanntes Symbol, sowie Katalog-Fehlschlag-Fall) -
alle 7 Faelle korrekt.

## Nachtrag (2026-07-18, gleicher Tag): VIX-Frühindikator als beschreibender Fakt

Direkt im Anschluss an die Bitpanda-Listing-Bugfix-Bestandsaufnahme fragte der
Nutzer explizit nach dem "nachlaufenden M2"-Konzept und ob wir bereits für
den Aktien-Bärenmarkt aufgestellt sind. Antwort: das bestehende
`equities_baermarkt_aktiv`-Flag ist ein reiner **Drawdown-Schwellenwert**
(S&P 500/Nasdaq ≥20 % unter 5-Jahres-Hoch, siehe AZ-4 Baustein 2) - NACHLAUFEND.
VIX (CBOE Volatility Index) ist dagegen ein **VORLAUFENDES** Optionsmarkt-
Stimmungssignal, im Code bisher komplett ungenutzt (kein einziger Treffer).
Nutzer bestätigte nach Bestandsaufnahme: erst die kleine Rohstoff-Lücke
(aktien_baermarkt-Fakt, siehe oben) schließen, dann VIX "mit korrekter
Implementierung" ergänzen - bewusst NUR als beschreibender LLM-Fakt (KEIN
deterministischer Deckel), analog `liquiditaets_regime`/`equities_baermarkt`.

**Datenquelle:** `api/yfinance_history.py::get_vix_reading()` - nutzt
denselben Timeout-geschützten `get_full_price_history("^VIX")` wie
`get_equities_bear_market_status()`, EIGENER try/except in
`_fetch_boden_zielzone_context()` (P-10: ein VIX-Ausfall darf die
Aktien-Bärenmarkt-Fakten nicht mit sich reißen und umgekehrt - zwei
unabhängige yfinance-Ticker-Abrufe).

**Bänder (branchenübliche CBOE-Praktiker-Konvention, KEIN projekteigener
Schwellenwert wie bei den equities_baermarkt-[OFFEN]-Werten):** <20 "ruhig",
20-30 "erhöht", 30-40 "gestresst", >40 "krise" - `agent/krypto/regime.py::
VIX_BANDS`/`_vix_label()`.

**Caching:** täglich über `macro_snapshot.vix_wert` (neue additive Spalte,
gleiches COALESCE-Upsert-Muster wie alle anderen Boden-Zielzone-Felder,
`database/db.py::_MACRO_SNAPSHOT_NEW_COLUMNS`).

**Konsum:** neuer `regime.vix.{wert,label}`-Fakt in ALLEN VIER Analysten
(Krypto/Aktien/Rohstoff/Hedge) - dasselbe Synergie-Muster wie beim
Bitpanda-Listing-Fix: EIN Berechnungsort (`compute_current_regime()`) statt
vier Einzellösungen. Rohstoff-spezifisch: "gestresst"/"krise" verstärkt bei
Gold/Silber die Safe-Haven-Logik, bei Kupfer/Erdgas eher neutral. Hedge-
spezifisch: zusätzliches (schwächeres als `aktien_baermarkt.aktiv`) Signal
FÜR mehr Absicherung, da VIX früher ausschlagen kann als der Drawdown.

**Verifiziert:** `_vix_label()` gegen alle 4 Bandgrenzen (8 Testfälle) +
echter Live-Abruf gegen `^VIX` (18,77 → "ruhig") + DB-Migrationstest gegen
Kopie der Produktions-DB (Spalte fehlte vorher, Upsert/Reread danach korrekt)
+ echter End-to-End-Lauf von `compute_current_regime()` gegen die migrierte
DB-Kopie (liefert echten VIX-Wert + korrektes Label im vollständigen
Regime-Objekt, inkl. BTC-Regime "baer" parallel korrekt berechnet).

**Bewusst NICHT umgesetzt:** kein deterministischer Deckel (Nutzer-
Entscheidung), keine Anzeige in `ui/regime_view.py`/Remote-Status-Karte
(bestehendes `equities_baermarkt` ist dort ebenfalls nicht enthalten -
konsistent, kein Präzedenzbruch) - beides mögliche spätere Ausbaustufen.

**Nebenfund behoben (selbes Datum):** `agent/rohstoff/analyst.py::build_facts()`
gab `aktien_baermarkt`/`equities_baermarkt` (aus `compute_current_regime()`)
nicht als LLM-Fakt weiter, obwohl Krypto-, Aktien- und Hedge-Analyst das tun.
Ergänzt: `regime.aktien_baermarkt.{aktiv,begruendung}` im Facts-Dict + neue
SYSTEM_PROMPT-Regel-8-Ergänzung (Gold/Silber tendenziell Safe-Haven-Nachfrage
bei Aktien-Bärenmarkt, Kupfer/Erdgas eher neutral/leicht belastend wegen
schwächerer Industriekonjunktur) - Gewichtung je `asset.symbol`, analog Fakt 9.
Syntax- und Feld-Smoke-Test bestanden (`equities_baermarkt_aktiv`/
`_begruendung` existieren exakt so auf `RegimeResult`, keine Kollision mit
`_FREMDE_KONTAMINATIONS_BEGRIFFE`).

## Nachtrag (2026-07-18, gleicher Tag): Detailanalyse Bärenmarkt-Schwellenwerte + VIX als zweiter Boden-Zielzone-Trigger

Nutzer bat um eine Detailanalyse der vier `[OFFEN]`-Parameter in
`boden_zielzone` (`reifegrad_daempfer_staerke`, `equities_baermarkt_
schwelle_prozent`, `equities_baermarkt_lookback_jahre`,
`equities_overlay_shift_std`) statt einer schnellen Einschätzung, mit einem
wichtigen Korrektur-Einwand: die Standard-Bärenmarkt-Definition (20% Drawdown)
gilt für Aktienindizes, NICHT für BTC — dort sind 50-70%+ historisch die
Norm. Das führte zu einer echten, datengestützten Analyse statt einer
Bauchgefühl-Antwort.

**Echte historische BTC-Zyklus-Böden nachgerechnet** (yfinance BTC-USD seit
2014, laufendes ATH + Drawdown, Phasenerkennung zwischen neuen ATHs):
2015-01-14 (-61%), 2018-12-15 (-83%), 2022-11-21 (-77%) — normale
Bullenmarkt-Korrekturen liegen dagegen bei 15-35% und sind deutlich häufiger,
sollten nicht mit echten Zyklus-Bärenmärkten verwechselt werden.

**Wichtiger Fund:** diese 3 Daten sind EXAKT dieselben, die bereits in
`indicators/calculations.py::BTC_CYCLE_BOTTOM_DEVIATIONS_STD = (-1.16,
-0.78, -1.26)` (Kommentar: "2015-01-14, 2018-12-15, 2022-11-21") verwendet
werden — die BTC-eigene Boden-Zielzone ist also bereits sauber gegen die
echten historischen Böden kalibriert, nur als Log-Regressions-Abweichung
(Std.), nicht als rohe %-Zahl. Das war beim ersten Analyse-Durchgang
übersehen worden.

**Trefferquoten-Analyse:** geprüft, ob `equities_baermarkt_aktiv` (S&P500/
Nasdaq, 20%/5J) an den 3 echten BTC-Böden aktiv gewesen wäre:

| BTC-Boden | S&P500-DD (5J) | Nasdaq-DD (5J) | VIX (Tag) | VIX-Max ±10 Tage |
|---|---|---|---|---|
| 2015-01-14 | -3,2% | -3,0% | 21,5 | 22,4 |
| 2018-12-15 | -11,3% | -14,8% | 21,6 | **36,1** |
| 2022-11-21 | -17,3% | -30,6% | 22,4 | 24,5 |

Ergebnis: **1 von 3** (nur 2022, über Nasdaq). `lookback_jahre`-Änderungen
hätten daran nichts geändert (die Tiefe lag unter 20%, nicht das Zeitfenster
war das Problem) — `schwelle_prozent` selbst ist Marktkonvention, keine
projekteigene Erfindung, daher nicht weiter kalibrierbar.

**VIX als zweiter, unabhängiger ODER-Trigger:** nach erneuter Prüfung (erste
Einschätzung "das wäre dieselbe Overfitting-Falle wie MVRV" war zu pauschal
- Unterschied: VIX-Bänder 20/30/40 sind branchenübliche CBOE-Konventionen,
NICHT aus diesen 3 Punkten gefittet) umgesetzt: `_boden_zielzone()` in
`agent/krypto/regime.py` löst den Overlay jetzt bei
`equities_baermarkt_aktiv ODER vix_label in (gestresst, krise)` aus, nutzt
denselben `overlay_shift_std` (kein zweiter, unbelegbarer Parameter).
2018 wäre damit zeitversetzt erfasst worden (VIX-Peak 36,1 wenige Tage um
den Boden) → **realistische Verbesserung von 1/3 auf ~2/3**, 2015 bleibt
weiterhin unerreicht (VIX nur ~21,5, "erhöht" statt "gestresst"). Bei n=3
bewusst mit Vorsicht zu interpretieren, aber ein echter, nicht erfundener
Fortschritt.

**Bewusst NICHT geändert:** `equities_baermarkt_aktiv` als eigenständiger
Fakt (von Krypto-, Aktien-, Rohstoff- und Hedge-Analyst konsumiert) bleibt
unverändert eng definiert ("Aktienindex im Drawdown") - der neue VIX-Pfad
wirkt NUR innerhalb des Boden-Zielzone-Overlays, nicht auf diesen Fakt.
`reifegrad_daempfer_staerke`/`equities_overlay_shift_std` bleiben
unveränderte Schätzwerte - bei n=3 Vergleichspunkten wäre jede weitere
Kalibrierung Overfitting, `config.yaml`-Kommentare entsprechend ehrlich
umformuliert (kein `[OFFEN]` mehr, sondern "bewusst nicht weiter
kalibrierbar" mit Begründung).

**Verifiziert:** 6 synthetische Testfälle (nur Aktien/nur VIX gestresst/nur
VIX krise/beide/keins/beide unbekannt) - alle korrekt; echter End-to-End-Lauf
von `compute_current_regime()` gegen Kopie der Produktions-DB (aktueller VIX
18,77 "ruhig" + `equities_baermarkt_aktiv=False` → Overlay korrekt NICHT
ausgelöst, keine Regression gegenüber dem bisherigen Verhalten).


## Nachtrag (2026-07-18, gleicher Tag): Multi-Asset-Batch - automatische Signal-Erzeugung fuer Aktien/Rohstoffe/Hedge

Nutzer-Fund: das letzte VST-Signal war 3 Tage alt, kein Kaufsignal
erhalten. Bestandsaufnahme (echte Notebook-Diagnose via
extract_notebook_diagnose.py, siehe Memory project_multi_asset_batch)
zeigte: die Krypto-Pipeline lief normal weiter, aber VST/PLTR/OD7N-L/DBPK/
3QSS hatten seit Erstellung der Rohstoff/Hedge-Pipelines KEINEN einzigen
automatischen Bewertungsversuch - agent/krypto/budget_allocator.py
enthaelt keine Referenz auf aktien/assetklasse, diese 8 Assets waren
ausschliesslich ueber den manuellen "Signal berechnen"-Klick erreichbar.

**Bewusst NICHT in den bestehenden 15-Min-Krypto-Allocator integriert**
(Nutzer-Auftrag "Job bauen, aber vorher genau durchdenken"):
- Die strikte Tier-1>2>3-Kaskade (Hebel>Marktscan>Spot,
  budget_allocator.py::_verteile_budget()) wuerde ein Tier 4 an
  geschaeftigen Tagen nie erreichen - genau das Problem, das geloest
  werden soll.
- Aktien/Rohstoffe/Hedge bewegen sich strukturell langsamer
  (Boersenzeiten/Wochenenden, 5-Tage-OHLC-Staleness-Schwelle vs. Kryptos
  2 Tage) - der 15-Min-Takt waere verschwendet.
- Kein Regressionsrisiko fuer den gut getesteten, kritischen Krypto-Pfad.

**Neues Modul agent/multi_asset_batch.py::run_multi_asset_batch()** -
eigenstaendige, kleinere Variante desselben Fallback-Musters wie
budget_allocator.py::_mit_fallback_chain()/_mit_conn() (Groq -> Mistral
-> Gemini, eigene Connection je Call), bewusst NICHT die private
Closure aus budget_allocator.py wiederverwendet (Entkopplung von einem
kritischen, bereits gut funktionierenden Pfad). Nutzt dasselbe geteilte
Tagesbudget (count_real_llm_calls_today_by_provider() zaehlt bereits
assetklassen-uebergreifend ueber die signals-Tabelle) - kein separates
Kontingent noetig.

**Cooldown bewusst nur 2-stufig** (kein drittes "ausgemustert"-Level wie
bei Krypto, alle 8 Assets sind beobachtungsstatus: beobachtung):
"gehalten" live aus der holdings-Tabelle abgeleitet (identisches Muster
wie signal_batch.py), cooldown_stunden_gehalten: 24 /
cooldown_stunden_beobachtet: 72 (config.yaml multi_asset_batch) -
deutlich traeger als Kryptos 10h/20h, passend zur langsameren
Marktdynamik.

**Neuer Job** scheduler/background.py::multi_asset_batch_job(),
ursprünglich registriert mit MULTI_ASSET_BATCH_INTERVAL_HOURS = 12
(reines Intervall + next_run_time=jetzt bei jedem Neustart) - der
Job-Takt gab nur Redundanz bei einem verpassten Lauf, der eigentliche
Rhythmus lief ueber die Cooldown-Werte. Eigener Lock
(multi_asset_batch_lock), P-8-Gate (nur aktiv mit groq_client). Neue
_notify_multi_asset_signal() (E-Mail bei handlungsrelevanten Signalen,
NIE bei HALTEN) - wiederverwendet dieselben Formatierungs-Helfer wie
Spot/Hebel (_formatiere_top_gruende/_formatiere_key_risks/
_formatiere_halte_kriterium/_formatiere_positionsgroesse_und_tranchen),
keine Duplikation.

**Nachtrag (2026-07-20): Quotrix-Handelsfenster-Fix.** Bitpandas Aktien/
ETFs/ETCs laufen seit 2026 ueber die Quotrix-Boerse (Duesseldorf), mit
echten, begrenzten Handelszeiten (Mo-Fr 07:30-23:00 CET), NICHT 24/7 wie
Krypto (siehe Memory project_bitpanda_exchange - erst bei der Recherche
zur Eigentumsstruktur/Real-Securities-Frage entdeckt). Das alte reine
Intervall mit next_run_time=jetzt bei jedem Neustart konnte zu jeder
Uhrzeit (auch nachts) ein Signal mit Kurszonen erzeugen, die auf einem
Stunden/Tage alten Schlusskurs basierten UND vom Nutzer erst zum
naechsten Handelsstart ueberhaupt umsetzbar waren. Jetzt fester Cron
(MULTI_ASSET_BATCH_CRON_HOURS = "9,19", nur Mo-Fr) statt Intervall, kein
next_run_time-Sofortstart mehr - ein Neustart wartet bewusst bis zum
naechsten reguleaeren Takt.

**Nachtrag (2026-07-20): OI-Abdeckungs-Warnung respektiert jetzt den
Hebel-Pruefung-Toggle.** Echter Nutzer-Fund: CANTON wurde ueber den
Hebel-Pruefung-Toggle abgeschaltet (siehe Kap. "SOL-Tranchen + Hebel-
Pruefung-Toggle"), meldete aber ueber die persistente OI-Abdeckungs-
Warnung (siehe Kap. "Persistente OI-Abdeckungs-Warnung") weiterhin per
E-Mail "seit 9 aufeinanderfolgenden Laeufen keine OI-Daten" - obwohl
laengst keine neuen Laeufe mehr fuer dieses Symbol stattfanden. Ursache:
`oi_abdeckung_status.konsekutive_fehlschlaege` wird ausschliesslich beim
tatsaechlichen Screening-Lauf aktualisiert - ein per Toggle
abgeschaltetes Symbol friert einfach beim letzten Stand ein, der aber
weiterhin >= Schwelle blieb und nach jedem Cooldown-Ablauf erneut eine
(inhaltlich falsche) Warnmail ausloeste.
db.py::get_symbole_mit_ueberschrittener_oi_schwelle() prueft jetzt per
LEFT JOIN gegen asset_hebel_settings zusaetzlich den Toggle-Status
(COALESCE-Default 1/erlaubt, wenn keine Zeile existiert) - abgeschaltete
Symbole werden von der Warnung ausgenommen, unabhaengig vom eingefrorenen
Zaehlerstand.

**Verifiziert:** _kandidaten() liefert exakt die erwarteten 8 Assets
(VST/PLTR/OD7N/OD7H/OD7C/OD7L/DBPK/3QSS), korrekt auf ihre Pipeline
gemappt. _ist_faellig() gegen 5 synthetische Cooldown-Faelle (gehalten/
beobachtet, jeweils knapp unter/ueber der Schwelle, kein Vorsignal). Echter
End-to-End-Lauf gegen Kopie der Produktions-DB: VST-Preis live aktualisiert
(vorher gate_passed=False, "Preis veraltet" korrekt erkannt), danach
echter Groq-Call erfolgreich (gate_passed=True, gegenargument befuellt,
provider_je_symbol={"VST": "groq"}), Cooldown blockierte einen sofortigen
zweiten Lauf korrekt. Kompletter Job-Wrapper (multi_asset_batch_job())
inkl. Lock/E-Mail-Pfad fehlerfrei durchgelaufen (kein Versand bei HALTEN,
wie erwartet).


## Nachtrag (2026-07-18, gleicher Tag): Multi-Asset-Vollstaendigkeitspruefung - Themen-ETF-Pipeline + 6 Konsistenz-Fixes

**Ausloeser:** Nutzer-Nachfrage "welche Assetklassen haben wir jetzt konkret
und wie sind diese unterteilt" fuehrte zur Live-Watchlist-Abfrage (55 Assets:
42 Krypto, 7 etf, 4 Rohstoffe, 2 Aktien) und dabei zum Fund, dass 5 der 7
"etf"-Assets (VVMX/X136/EXH3/CEBS/ISOC - Themen-/Sektor-ETFs: Seltene Erden/
Bioenergie/Food&Bev/Kupferminen/Agribusiness) seit ihrer Ersterfassung in
config.yaml OHNE JEDE Pipeline dastanden - weder im neuen Multi-Asset-Batch
(nur aktien/rohstoffe/Hedge-Symbole beruecksichtigt) noch sauber im manuellen
UI-Klick (fielen dort auf die Krypto-Pipeline durch, die weder CoinGecko-ID
noch Kraken-Symbol fuer sie kennt).

Nutzer-Auftrag danach: "wir sollten das multiasset Thema jetzt vollinhaltlich
abschliessen" - vollstaendiger Audit ueber API-Monitoring/Regelwerksuebersicht/
Marktscan/Feature-Paritaet/Doku-Aktualitaet ueber alle 4 Nicht-Krypto-Pipelines
(Aktien/Rohstoffe/Hedge + die neue Themen-ETF-Pipeline). Ergab 7 konkrete
Befunde, alle in dieser Runde abgearbeitet:

### 1. Themen-ETF-Pipeline (agent/themen_etf/)

Neues, eigenstaendiges Modul (gleiche Architektur-Entscheidung wie bei Aktien/
Rohstoffen - siehe Spezifikation.md "Zielarchitektur fuer Multi-Asset-
Erweiterbarkeit"), mirror von agent/rohstoff/. Entfernt gegenueber Rohstoff:
makro_ueberlagerung (kein sauberer Treiber-Bezug) + positionierung
(CFTC-COT existiert nur fuer Rohstoff-Futures). Neu: sektor_rotation - relative
Staerke des ETFs gegenueber einem breiten Markt-Benchmark (SPY) ueber 30/90
Handelstage, berechnet aus bereits vorhandener OHLC-Historie (KEIN neuer
externer Datenanbieter - Ersatz fuer das fehlende KGV/COT-Aequivalent).

**Live-Fund bei der Verifikation:** anders als die duenn gehandelten
WisdomTree-Rohstoff-ETCs haben die meisten UCITS-Themen-ETFs eine echte,
direkt handelbare yfinance-Historie (VVMX/EXH3/CEBS live bestaetigt, 778-4707
Handelstage) - KEIN Futures-Proxy-Workaround noetig. X136 (Boerse Berlin-
Notierung) liefert dagegen 0 Punkte ("Period 'max' is invalid"), ISOC hat
eine seit 2025-09-10 eingefrorene Historie (>10 Monate) - fuer beide greift
bewusst NUR das bestehende Staleness-Gate (gate_passed=False, sauber
degradiert), KEIN Ersatz-Ticker gesucht (P-10: sauber degradieren statt eine
fragile Ersatzloesung erzwingen; kann spaeter nachgeruestet werden, falls
gewuenscht).

Verdrahtet in ui/signals_view.py (_themen_etf_watchlist, _run_pipeline()-
Branch, _asset_by_symbol()/_refresh_list()-Listen ergaenzt - waren zunaechst
uebersehen und haetten die 5 Themen-ETFs sonst weiterhin unsichtbar in der
Signale-Tab-Liste gelassen) UND in agent/multi_asset_batch.py
(_kandidaten()/_pipeline_fuer() - Multi-Asset-Batch deckt jetzt 13 statt 8
Assets ab).

### 2. API-Monitoring-Luecke

api/cftc_cot.py trackt korrekt via @track_api_health("cftc_cot"), tauchte
aber in remote/server.py::API_HEALTH_GROUPS in KEINER der drei Gruppen auf -
die API-Status-Karte zeigte CFTC-Gesundheit also nie an, obwohl die Daten in
der DB vorhanden waren. Ergaenzt zu api-health-makro.

### 3. Regelwerksuebersicht-Luecke

agent/krypto/regelwerk_parameter.py (Parameter-Uebersicht-Tab/-Karte) war
komplett Krypto-fokussiert - enthielt keinen einzigen Hedge- oder Multi-Asset-
Batch-Parameter. Ergaenzt: hedge.max_abdeckung_anteil,
multi_asset_batch.cooldown_stunden_gehalten/beobachtet, sowie (siehe Punkt 6)
die beiden neuen Hedge-Bull-Deckel-Parameter.

### 4. Wiederholungs-Erkennung: nur Krypto hatte sie

Die "letzte VERKAUFEN/TAUSCHEN-Empfehlung wurde nicht umgesetzt"-Erkennung
(urspruenglich 2026-07-17 nur in agent/krypto/analyst.py eingebaut) nach
agent/krypto/wiederholungs_erkennung.py ausgelagert (build_wiederholung_fact(),
5 synthetische Testfaelle verifiziert) und fuer Aktien/Rohstoffe/Hedge/
Themen-ETF nachgeruestet (_WIEDERHOLUNG_RELEVANTE_AKTIONEN = ("VERKAUFEN",)
statt Kryptos ("VERKAUFEN", "TAUSCHEN"), da diese 4 Klassen kein TAUSCHEN
kennen). Jede Pipeline laedt jetzt letztes_signal vor dem build_facts()-Call
und reicht es durch, jeder SYSTEM_PROMPT bekam die entsprechende Regel ergaenzt.

### 5. Historische Trefferquote: stillschweigend gepoolt

compute_win_rate_fact(conn, "spot") pool­te FRUEHER ALLE Zeilen aus der
signals-Tabelle ungefiltert - urspruenglich eine bewusste, dokumentierte
Krypto+Aktien-Vereinfachung ("Stichprobe zu klein fuer weitere Aufspaltung"),
aber seit Rohstoff/Hedge/Themen-ETF ebenfalls in dieselbe Tabelle schreiben,
OHNE dass das je neu entschieden wurde - eine Rohstoff-Trefferquote haette
z.B. stillschweigend Krypto-Momentum-Ergebnisse mit eingerechnet.
compute_win_rate_fact() um einen optionalen erlaubte_symbole-Parameter
erweitert (5 synthetische Testfaelle: Krypto+Aktien-Pool/Rohstoff-Pool/
Hedge-Pool/leerer Themen-ETF-Pool/ungefiltert - alle bestaetigt exakt).
Krypto+Aktien bleiben BEWUSST gepoolt (die urspruengliche Begruendung gilt
weiterhin), Rohstoffe/Hedge/Themen-ETF bekommen je einen EIGENEN Pool (anfangs
meist None, bis genug eigene Signale ausgewertet sind - ehrlicher als eine
geliehene fremde Zahl).

### 6. Hedge-Gegenszenario-Frage (SPIEGELVERKEHRT, nicht 1:1 uebernommen)

Kritischer Punkt bei der Konsistenzpruefung: der bestehende Gegenszenario-
Deckel (risk_gate.py::post_check(), wirkt automatisch fuer Krypto/Aktien/
Rohstoffe, die post_check() teilen) kappt die Positionsgroesse bei hoher
forecast.bear.probability_pct - richtig fuer eine normale Long-Position (das
IST das Risiko-Szenario). Fuer ein inverses Hedge-Instrument (DBPK/3QSS) waere
ein 1:1 uebernommener Bear-Deckel FUNKTIONAL FALSCHHERUM gewesen: die Position
GEWINNT bei fallenden Kursen, ihr eigentliches Risiko-Szenario ist eine hohe
forecast.bull.probability_pct (Volatility-Decay bei anhaltendem Aufwaertstrend
ohne Absicherungsnutzen, siehe SYSTEM_PROMPT Regel 4). Neu implementiert:
_post_check_hedge() um einen SPIEGELVERKEHRTEN "Bull-Wahrscheinlichkeits-
Deckel" erweitert (hedge.bull_wahrscheinlichkeit_schwelle_prozent: 35,
hedge.bull_wahrscheinlichkeit_deckel_anteil: 0.5 - identische Werte wie das
Spot/Aktien-Pendant, aber eigene Config-Keys unter hedge:). 4 synthetische
Testfaelle verifiziert: hohe Bull-WK bei KAUFEN -> gekappt; niedrige Bull-WK ->
unveraendert; VERKAUFEN -> Deckel greift nicht; hohe BEAR- statt Bull-WK bei
KAUFEN -> KEIN Deckel (bestaetigt die Spiegelung ist korrekt, kein versehentlich
uebernommener Bear-Deckel).

### 7. RM-3-Tabelle war stale

Zeile behauptete weiterhin "Aktien/ETF/Rohstoffe je 0%, nur Krypto im Einsatz"
- seit den Pipelines vom 15./18.07. schlicht falsch. Korrigiert: der
KONFIGURATIONSWERT ist unveraendert 0%, aber die eigentliche offene Luecke ist,
dass der Cross-Klassen-Deckel selbst nirgends durchgesetzt wird (jede Pipeline
rechnet nur gegen ihre eigene Assetklassen-Teilmenge).

**Verifiziert:** _kandidaten()/_pipeline_fuer() liefern exakt 13 Assets,
korrekt gemappt (Live-Check gegen echte Watchlist). Echter End-to-End-Lauf
gegen Kopie der Produktions-DB (nach Migration + frischen Preis-Snapshots fuer
alle 5 Themen-ETFs): VVMX - vollstaendiger echter Groq-Call, HALTEN, 42%
Konfidenz, sektor_rotation-Fakt korrekt in der Begruendung genutzt ("negative
Sektor-Rotation gegenueber dem breiten Markt (SPY)"), alle 15 inhaltlichen
Pflichtfelder befuellt (Top-5-Gruende/Key-Risks/Forecast/Halte-Kriterium/
Gegenargument - Entry/Stop/Take-Profit bei HALTEN leer, identisches Verhalten
wie bei bestehenden Aktien-HALTEN-Signalen, kein Regressionsfund). X136 -
sauberer Gate-Fehlschlag ("keine historischen Daten vorhanden"), kein Absturz.
Kompletter run_multi_asset_batch()-Lauf gegen alle 13 Kandidaten: korrekte
Kandidaten-Erkennung, Cooldown-Pruefung, Gate-Handling (mehrere Assets mit
nicht-aktualisierten Preisen korrekt als gate_passed=False verarbeitet, kein
Budget verbraucht), 3 echte Groq-Calls liefen tatsaechlich (429-Rate-Limit
durch die vorangegangenen Testaufrufe in derselben Sitzung erwartungsgemaess
sauber als "fehlgeschlagen" behandelt, kein Crash - P-10 funktioniert wie
vorgesehen).


### 8. Nachtrag zum Nachtrag: Watchlist-/Portfolio-Asset-Verwaltung geprueft

Nutzer-Hinweis "vergiss auch nicht die Asset-Verwaltung in der Watchlist und
im Portfolio - manuelle Eingabe und automatische Befuellung" fuehrte zu einem
gezielten Audit von AssetAddDialog (ui/app.py), Bitpanda-Sync
(importer/bitpanda_sync.py) und Portfolio-Tab (ui/portfolio.py). Ergebnis:
Portfolio-Tab und Bitpanda-Sync sind bereits vollstaendig assetklassen-neutral
(keine Aenderung noetig). EIN echter Fund: das "etf"-Dropdown im
AssetAddDialog deckt sowohl Themen-ETFs als auch Hedge-Instrumente ab, die
NUR per Symbol-Zugehoerigkeit zu SYMBOL_ZU_HEBEL_FAKTOR unterschieden werden
(kein eigenes UI-Feld dafuer) - ein neu hinzugefuegtes Hedge-Instrument waere
ohne Warnung als Themen-ETF behandelt worden, bis ein Entwickler es zusaetzlich
im Code eintraegt (hebel_faktor/Referenzindex sind hartkodiert, nicht per UI
abbildbar). Fix: `_validate_new_asset()` warnt jetzt (P-10, nicht blockierend)
bei jedem neuen etf-Symbol, das nicht in SYMBOL_ZU_HEBEL_FAKTOR steht, mit
konkretem Hinweis auf den noetigen Code-Schritt. Synthetisch verifiziert (Nicht-
Hedge-Symbol -> Warnung, echtes Hedge-Symbol DBPK -> keine Warnung).

Nebenbefund (bewusst NICHT geaendert, vorbestehendes und symmetrisches
Verhalten ueber alle Assetklassen): ein automatisches Hinzufuegen unbekannter
Bitpanda-Symbole zur Watchlist existiert nur fuer offene Hebel-/Margin-
Positionen (auto_add_unknown_hebel_symbols(), importer/bitpanda_margin_
positions.py). Neue Spot-/Nicht-Krypto-Bestaende fuer noch nicht in der
Watchlist gefuehrte Symbole werden NICHT automatisch angelegt, sondern per
result.unmatched_bitpanda_symbols im Sync-Ergebnis-Dialog angezeigt (ui/app.py,
zwei Stellen) - der Nutzer fuegt sie bei Bedarf manuell ueber AssetAddDialog
hinzu. Gilt gleichermassen fuer Krypto und Nicht-Krypto, keine Themen-ETF-
spezifische Luecke.


## Nachtrag (2026-07-18, gleicher Tag): LLM-Tagesbudget-Konsistenzpruefung + E-Mail-Versand-Audit

**Ausloeser:** Nutzer bemerkte auf der Remote-Status-Seite ein verdaechtiges
Bild (Groq "Fehler", "cerebras (2)" in der Hebel-Provider-Performance-Karte,
angezeigtes LLM-Budget) und bat um eine Pruefung des E-Mail-Versands sowie
des LLM-Tagesbudgets speziell im Zusammenspiel mit den neuen Multi-Asset-
LLM-Verbrauchern.

**"cerebras (2)" in der Provider-Performance:** korrekte historische
Anzeige, kein Bug - diese 2 Hebel-Signale wurden vor der vollstaendigen
Cerebras-Entfernung erzeugt und sind seither aufgeloest (siehe
project_cerebras_free_tier_aenderung_2026-08-17.md). Kein Code aendert das
mehr, es ist reine Vergangenheitsdaten-Anzeige.

**Groq "Fehler (vor 20 Min)":** ebenfalls kein Bug - echter 429-Rate-Limit
durch die vorangegangenen Verifikations-Testlaeufe dieser Session (mehrere
echte Groq-Calls kurz hintereinander waehrend der Themen-ETF-Verifikation).
Selbstheilend.

**Echter Fund: `count_real_signals_today()` war fuer das Krypto-Tagesbudget
verfaelscht.** Diese Funktion zaehlt Zeilen in der `signals`-Tabelle seit
Mitternacht UTC, OHNE Assetklassen-Filter. Sie wird an 3 Stellen fuer
Krypto-spezifische Tagesbudget-Entscheidungen verwendet (das Krypto-Budget-
System - Hebel/Marktscan/Spot, `taegliches_budget_gesamt: 15` - kalibriert
auf Groqs reale Token-Kapazitaet fuer Krypto allein):

1. `agent/krypto/signal_batch.py::run_signal_batch()` - der manuelle "Batch
   berechnen"-Button berechnete sein verbleibendes Tagesbudget als
   `daily_budget - bereits_heute`. Seit der automatische Multi-Asset-Batch
   (Aktien/Rohstoffe/Hedge/Themen-ETF, alle 12h) in dieselbe `signals`-
   Tabelle schreibt, schrumpfte das verbleibende KRYPTO-Budget
   stillschweigend um jede Multi-Asset-Signal-Erzeugung - eine echte
   Funktionsbeeintraechtigung, nicht nur eine Anzeige-Ungenauigkeit.
2. `remote/status.py::_get_budget_heute()` - die "LLM-Budget heute"-Karte
   (die im Screenshot zu sehende Karte) zeigte ein verzerrtes Verhaeltnis
   zum 15er-Deckel.
3. `ui/marktscan_view.py::_run_writeup()` - dieselbe Verzerrung in der
   Budget-Warnung des manuellen Marktscan-Buttons.

**Fix:** `database/db.py::count_real_signals_today()` um einen optionalen
`erlaubte_symbole`-Parameter erweitert (identisches Muster wie bereits heute
bei `compute_win_rate_fact()`). Alle 3 Aufrufstellen filtern jetzt auf
Krypto-Symbole. `remote/status.py` weist den Multi-Asset-Verbrauch
zusaetzlich als eigene, sichtbare Zeile (`multi_asset_heute`) aus statt ihn
unsichtbar zu verschlucken - neue Karten-Zeile in `remote/server.py`.

Synthetisch verifiziert (4 Faelle: ungefiltert/Krypto-only/leeres Set/
unbekanntes Symbol). Echter Nachweis-Lauf gegen eine Kopie der Produktions-
DB mit realistischem Mischszenario (8 echte Krypto- + 6 Multi-Asset-Signale
am selben Tag): ALTE Zaehlweise haette 14/15 (93%) angezeigt - faelschlich
fast erschoepft; NEUE Zaehlweise zeigt korrekt 8/15 (53%) Krypto-Verbrauch,
6 separat als Multi-Asset ausgewiesen.

**E-Mail-Versand-Audit (bereits sauber, keine Aenderung noetig):**
`_notify_spot_signal()`/`_notify_hebel_signal()`/`_notify_multi_asset_signal()`
decken alle 6 Signal-erzeugenden Pfade ab (Krypto Spot, Hebel, Aktien,
Rohstoffe, Hedge, Themen-ETF). Marktscan-Tier-2-LLM-Writeups (reine
Text-Anreicherung eines bereits per Score entdeckten Kandidaten, kein
eigenstaendiges Signal-Objekt) senden bewusst keine zweite E-Mail - der
Kandidat wurde bereits ueber `_notify_marktscan_kaufkandidaten()` beim
eigentlichen Scan gemeldet, kein Duplikat noetig. Manuelle "Signal
berechnen"-Klicks (alle Assetklassen) senden bewusst NIE eine E-Mail - nur
automatische Jobs, konsistent ueber die gesamte App.


## Nachtrag (2026-07-18, gleicher Tag): SOL in AZ-4-Tranchen + neuer Hebel-Prüfung-Toggle

**Auslöser:** Nutzer-Wunsch, Solana in die bisher BTC/ETH-exklusive AZ-4-
Tranchen-Funktion aufzunehmen (mit Verifikationsauftrag), plus ein neuer
per-Asset-Schalter, ob ein Krypto-Asset überhaupt fürs automatische
Hebel-Screening berücksichtigt werden soll.

### 1. SOL in AZ-4-Tranchen

Zwei getrennte BTC/ETH-Hardcodierungen identifiziert: `tranchen_erlaubt`
(gestaffelte Kauf-/Verkaufszonen fürs eigene Signal - einfach erweiterbar)
und `cash_reserve_ziel` (AZ-4 Baustein 3, ein *portfolioweites* Ziel, das
BTC+ETH fest zu zwei Gewichten kombiniert - eine echte 3-Wege-Erweiterung
wäre ein groesserer Umbau der Gewichtungsformel). Bewusst NUR
`tranchen_erlaubt` um SOL erweitert (`agent/krypto/pipeline.py`,
`database/db.py::_DCA_ERLAUBT_DEFAULT_SYMBOLS`, alle 5 Text-/Spalten-Stellen
in `ui/app.py`) - `cash_reserve_ziel` bleibt unverändert BTC/ETH-exklusiv.

**Verifikation:** 5 synthetische `_validate()`-Testfälle (gültige Tranchen,
Summe≠100, doppelter Rang, von>bis, null) - alle bestätigt korrekt. Echter
End-to-End-Lauf gegen Kopie der Produktions-DB mit erzwungenem Bär-Regime
(`dataclasses.replace()` auf ein echtes `RegimeResult`): SOL/BTC/ETH liefen
alle drei fehlerfrei durch `generate_signal()`. Zusätzlich ein Fake-LLM-
Client mit einer kanonischen Antwort inkl. echtem 3-Tranchen-Vorschlag durch
die komplette Pipeline geschickt - `tranchen_json` korrekt serialisiert,
`entry_usd_von/bis` blieb korrekt die Gesamtspanne (nicht die Tranchen-
Einzelzonen), aus der DB neu geladen identisch mit dem Original-Objekt -
genau der Pfad, den `ui/signals_view.py` beim Anzeigen nimmt.

**Nebenfund bei der Verifikation (kein Code-Bug, reines Testartefakt):**
die Desktop-DB-Kopie hatte für SOL eine veraltete `price_history` (CoinGecko-
Tabelle, separat von der Kraken-`price_history_ohlc`-Tabelle) - beide Tabellen
speisen die Staleness-Pruefung in `_load_closes_and_ohlc()` unabhaengig
voneinander. Kein Fix noetig, nur ein frischer Preis-/Historie-Abruf im
Testaufbau.

### 2. Neuer Hebel-Prüfung-Toggle

Per-Asset-Schalter (analog zum bestehenden AZ-4-Tranchen-Toggle-Muster,
`asset_dca_settings`): neue Tabelle `asset_hebel_settings` +
`get/set_hebel_pruefung_erlaubt()` in `database/db.py`. Default **true**
für ALLE Krypto-Assets (bewusst anders als der Tranchen-Toggle, dessen
Default nur für BTC/ETH/SOL an ist) - kein Verhaltenswechsel für bestehende
Nutzer ohne explizites Abschalten.

Greift in `agent/krypto/hebel_screening.py::run_hebel_screening()` VOR dem
teuren OI-Abruf (Binance/Bybit/OKX) - ein abgeschaltetes Asset bekommt weder
neue Trigger noch einen LLM-Call noch einen neuen Kandidaten im Hebel-Tab.
Bewusst NICHT verdrahtet in `agent/krypto/budget_allocator.py::
_offene_positionen_als_kandidaten()` - bereits offene Hebel-Positionen
bleiben unabhängig vom Toggle weiter risikoüberwacht (Nutzer-Bestätigung im
Vorgespräch).

Neue Spalte "Hebel-Prüfung" im Watchlist-Tab (`ui/app.py`, gilt für alle
Krypto-Assets, nicht nur eine feste Liste), neuer Toolbar-Button "Hebel-
Prüfung umschalten" mit Guard-Klausel (nur Krypto ohne Stablecoins).

**Verifikation:** Tk-Smoke-Test gegen Kopie der Produktions-DB (leichtgewichtig
über `TradingInfoToolApp.__new__()` statt der vollen `__init__` mit allen 5
Tabs, um unnötige Netzwerk-Aufrufe zu vermeiden) - Spalte korrekt vorhanden,
Toggle-Klick flippt den Wert korrekt in der DB UND in der Anzeige, Guard-
Klausel für ein Nicht-Krypto-Asset (VST) löst korrekt nur den Info-Dialog
aus, OHNE einen DB-Write auszulösen.

## Nachtrag (2026-07-18, gleicher Tag): LLM-Budget-Neukalibrierung nach Mistral-Einführung + Zeitpunkt/Anbieter-Anzeige + LLM-Anfrage in der Historie

**Auslöser:** Nutzer-Beobachtung ("wir kämpfen um jede Abfrage") anhand der
Remote-Status-Seite: Groq wirkte ausgelastet, Gemini praktisch ungenutzt (27h
seit letztem Call), das Tagesbudget zeigte weiterhin "15" an, obwohl seit der
Mistral-Integration (2026-07-17) eine dritte, deutlich größere Kapazitätsstufe
existiert. Zusätzlich zwei Wünsche: Zeitpunkt/Anbieter der LLM-Abfrage im
Info-Fenster und in der E-Mail sichtbar machen, und die zugehörige LLM-Anfrage
in der Signal-Historie einsehbar machen.

### 1. Budget-Neukalibrierung (`taegliches_budget_gesamt`, B)

Klargestellt: `B` ist **kein** literaler Tages-Deckel für LLM-Calls, sondern
steuert nur, wie viele Kandidaten pro 15-Minuten-Tick überhaupt einen
LLM-Versuch bekommen (`agent/krypto/budget_allocator.py::_verteile_budget()`,
siehe `docs/budget_queue_design.md`) - jeder ausgewählte Kandidat durchläuft
danach individuell die Groq→Mistral→Gemini-Kaskade. `B` war 1:1 auf Groqs
eigene Tageskapazität kalibriert (~15-18 Calls, siehe
`signale_batch.taegliches_budget`), bevor Mistral existierte, und wurde seither
nie angepasst. Die echte Schutzgrenze ist Mistrals eigenes Tagesbudget
(`mistral_taegliches_budget`, unverändert 150) - unabhängig von `B`.

**Berechnung (Nutzer-Vorgabe "berechne zuerst die Auswirkungen"):** anhand der
live über `config.get_watchlist()` abgefragten Watchlist (41 nicht-cash-
äquivalente Krypto-Assets, davon 13 `rolle=="core"`) wurde der theoretische
maximale Spot-Rotation-Bedarf je Cooldown-Regime berechnet
(`asset_anzahl × 24 / cooldown_stunden`). Ergebnis: selbst beim ALTEN Cooldown
(10h Kern/20h taktisch) lag der Bedarf bei ~65/Tag, weit über dem alten
`B=15` - die Drosselung war real, kein reines Anzeige-Problem. Beim neuen,
gelockerten Cooldown (8h/15h, siehe Punkt 2) liegt der Bedarf bei
13×24/8 + 28×24/15 ≈ 39 + 45 = 84/Tag.

Neu kalibriert: `taegliches_budget_gesamt: 90` (deckt die vollen 84/Tag plus
Puffer für Hebel-/Marktscan-Aktivität, bleibt deutlich unter Mistrals 150er-
Deckel - echte Ausreißertage laufen kontrolliert in Gemini als dritte Stufe).
`spot_rotation_reserve` proportional mitskaliert (5→30, Verhältnis F/B ≈ 33%
wie ursprünglich 2026-07-13 festgelegt) - Spot-Rotation behält denselben
relativen Mindestanteil auch an sehr Hebel-/Marktscan-aktiven Tagen.

### 2. Cooldown-Lockerung (Nutzer entschied sich für die moderate Empfehlung)

`spot_cooldown_stunden_kern` (rolle=core ODER gehalten ODER offene Hebel-
Position): 10h → 8h. `spot_cooldown_stunden` (rein taktische Watchlist-Assets
ohne Position): 20h → 15h. Beide waren ursprünglich als Bremse gegen die
knappe Groq-Kapazität gesetzt (2026-07-15/16) - jetzt, wo Mistrals große
Fallback-Kapazität den Groq-Engpass abfedert, ist die Bremse weniger nötig.

**Verifikation:** 4 synthetische `_verteile_budget()`-Testszenarien (ruhiger
Tag, normaler Tag, Crash-Tag mit vielen Hebel-Triggern, "nur Spot volle
Berechnung") - alle bestätigt korrekt: der volle gelockerte Spot-Bedarf
(84/Tag) läuft jetzt ohne Drosselung durch `B=90`, Crash-Tag-Priorität
(Hebel > Marktscan > Spot) und Spot-Rotations-Mindestreserve (`F=30`)
funktionieren weiterhin wie vorgesehen.

### 3. Zeitpunkt + Anbieter in Detail-Panel und E-Mail

`ui/hebel_view.py` zeigte bereits Anbieter+Zeitpunkt im Detail-Panel
(`meta_label`); `ui/signals_view.py` zeigte nur den Zeitpunkt, ohne Anbieter -
um `Anbieter: {signal.groq_model}` ergänzt (deckt Spot UND Aktien/Rohstoffe/
Hedge/Themen-ETF ab, da alle dieselbe `SignalsView`-Klasse und `Signal`-
Dataclass nutzen). Alle drei E-Mail-Funktionen in `scheduler/background.py`
(`_notify_spot_signal`, `_notify_hebel_signal`, `_notify_multi_asset_signal`)
zeigten bisher WEDER Zeitpunkt noch Anbieter - je eine Zeile
`Berechnet: <Datum Uhrzeit> · Anbieter: <provider:modell>` ergänzt.

### 4. LLM-Anfrage/Antwort in der Signal-Historie

Neue Spalte "Anbieter" in beiden History-Dialogen (`SignalHistoryDialog` in
`ui/signals_view.py`, `HebelSignalHistoryDialog` in `ui/hebel_view.py`).
Doppelklick auf eine Historien-Zeile öffnet einen neuen Detail-Dialog
(`LlmAbfrageDialog` bzw. `HebelLlmAbfrageDialog`) mit den an die KI gesendeten
Fakten (`facts_json`, JSON-formatiert) und der Roh-Antwort (`groq_raw_response`
bzw. `groq_raw_response` bei `HebelSignal`) - beide Felder waren bereits in der
DB gespeichert, reine UI-Sichtbarmachung ohne neuen Netzwerk-Call oder neue
Datenerfassung.

**Verifikation:** Tk-Smoke-Test gegen Kopie der Produktions-DB - Anbieter-
Spalte korrekt befüllt (z. B. `gemini:gemini-3.1-flash-lite`,
`groq:llama-3.3-70b-versatile`), simulierter Doppelklick öffnet den
Detail-Dialog korrekt für ein echtes Spot-Signal (BTC, 20 Historien-Einträge)
und ein echtes Hebel-Signal (CAT LONG), `facts_json`/Roh-Antwort werden
lesbar formatiert angezeigt (mehrere Tausend Zeichen, korrekt eingerückt).

## Nachtrag (2026-07-18, gleicher Tag): Cash-Veto-Warnsystem - RM-4-Block sichtbar machen statt stillschweigend zu HALTEN downzugraden

**Auslöser:** Nutzer-Auftrag "prüfe bitte - wichtig Anzeige und Info, wenn
über einen der Cash-Parameter ein Block oder die weitere Verarbeitung
verhindert werden - Detailanalyse durchführen". Ergebnis der Analyse: RM-4
(Cash-Reserve-Minimum, `risk_gate.py::pre_check()`) ist der einzige echte
Cash-Block (Spot/Aktien/Rohstoffe/Themen-ETF - nicht Hebel/Hedge). Vier
konkrete Lücken gefunden, alle auf Nutzer-Wunsch ("ja alles umsetzen")
behoben.

### 1. Der wichtigste Fund: `risk_veto` erfasste den häufigeren Fall gar nicht

Der bestehende `risk_veto`/`risk_veto_reason`-Mechanismus in `post_check()`
feuert NUR, wenn das Modell die `risiko_check.kauf_erlaubt`-Regel MISSACHTET
und trotzdem KAUFEN/NACHKAUFEN vorschlägt (deterministischer Backstop). Ein
regelkonformes Modell, das bei `kauf_erlaubt == false` bereits von sich aus
HALTEN sagt (der häufigere Fall, da genau das per Prompt-Regel verlangt
wird), löste bisher GAR KEIN sichtbares Signal aus - der Cash-Block blieb
komplett unsichtbar, obwohl das System dadurch faktisch beeinträchtigt war.

**Fix:** Neues, unabhängiges Feld `RiskPreCheckResult.cash_veto`/
`cash_veto_reason` in `risk_gate.py` - wird IMMER gesetzt, wenn RM-4 bei
dieser Bewertung aktiv war, unabhängig vom tatsächlichen Modellverhalten.
`post_check()` reicht `_cash_veto`/`_cash_veto_reason` jetzt IMMER durch
(nicht nur bei einer tatsächlichen Aktions-Überschreibung). Persistiert auf
`Signal.cash_veto`/`cash_veto_reason` (additive Migration, nur `signals`-
Tabelle, da RM-4 hebel-/hedge-unabhängig ist) - an allen 4 Pipelines
verdrahtet (Krypto, Aktien, Rohstoffe, Themen-ETF, alle nutzen dieselbe
`risk_gate.pre_check()`/`post_check()`).

### 2. WARNUNG-E-Mail statt Stille (Nutzer-Vorgabe: "System beeinträchtigt")

Ein cash-blockiertes Signal endet als HALTEN - HALTEN löst normalerweise NIE
eine E-Mail aus (bewusstes Design gegen Postfach-Spam). Für `cash_veto`
wurde das bewusst durchbrochen: neue `_notify_cash_veto_warning()` in
`scheduler/background.py`, aufgerufen aus `_notify_spot_signal()` und
`_notify_multi_asset_signal()` VOR deren HALTEN-Guard. Betreff
`WARNUNG - Cash-Veto (<Symbol>)`, Body erklärt explizit, dass das System
aktuell durch eine zu geringe Cash-Reserve beeinträchtigt ist und das für
ALLE Spot-/Aktien-/Rohstoff-/Themen-ETF-Bewertungen gilt, nicht nur das
eine Asset.

**Cooldown bewusst EIN globaler Zeitstempel, nicht pro Asset/Job**
(`config.yaml benachrichtigung.email.cash_veto_warnung_cooldown_minuten`,
Default 360 Min/6h) - RM-4 ist ein PORTFOLIOWEITER Zustand: ohne Cooldown
würde jedes während der Unterschreitung bewertete Asset eine eigene Mail
auslösen (potenziell ein Dutzend am Tag). Gleiches Muster wie
`_notify_job_failure()`, nur mit einem einzelnen statt einem pro-Job-
Zeitstempel.

### 3. Detail-Panel-Warnung unabhängig vom bestehenden Risiko-Veto

`ui/signals_view.py`: neue Zeile `⚠ WARNUNG - Cash-Veto (System
beeinträchtigt): <Grund>` im `gate_label`, geprüft über `signal.cash_veto`
(NICHT über `signal.risk_veto`) - erscheint also auch dann, wenn das Modell
sich schon regelkonform verhalten hat (der unter Punkt 1 beschriebene,
häufigere Fall).

### 4. Zwei kleinere Detailfunde ebenfalls behoben

- EURCV-Kurs fehlt → Fiat-Guthaben zählte bisher schon nicht in die
  Cash-Reserve mit, der Grund dafür landete aber nur in einer nirgends
  verwendeten `checks`-Liste. Jetzt als Zusatzsatz direkt an
  `cash_veto_reason` angehängt, sobald es tatsächlich zu einem Veto kam.
- `db.get_cash_reserve_fiat_eur()`: ein korrupter DB-Wert (`ValueError`)
  fiel bisher still auf 0.0 zurück, ohne jede Spur. Jetzt `logger.warning()`
  mit dem kaputten Rohwert.

**Verifikation:** 4 synthetische `pre_check()`/`post_check()`-Szenarien
gegen eine In-Memory-DB + echte `config.yaml`-Werte (kein Cash → Veto,
inkl. des bisher unsichtbaren "Modell sagt selbst korrekt HALTEN"-Falls;
genug Cash → kein Veto; EURCV fehlt → Veto mit Zusatzhinweis; korrupter
DB-Wert → geloggt) - alle bestätigt korrekt. Migration + Signal-Roundtrip
gegen echte Kopie der Produktions-DB (ALTER TABLE, alte Zeilen laden
korrekt mit `cash_veto=False`). Tk-Smoke-Test für die neue Detail-Panel-
Zeile (erscheint bei `cash_veto=True`, verschwindet bei `False`, keine
Verwechslung mit der bestehenden Risiko-Veto-Zeile). Cooldown-Logik der
Warnmail synthetisch getestet (erste Warnung geht raus, zweite wird
unterdrückt, nach simuliertem Cooldown-Ablauf geht die dritte wieder raus).

## Nachtrag (2026-07-18, gleicher Tag): Groq-Tageserschöpfung erkennen - kein unnötiger Erschöpfungs-Versuch mehr pro Kandidat

**Auslöser:** Nutzer-Beobachtung: "mir kommt vor, dass trotz Erschöpfung
immer zuerst Groq abgefragt wird". Bestätigt durch Code-Prüfung: anders als
Mistral/Gemini (echter, aus der DB gelesener Tageszähler, siehe
`_mit_fallback_chain()`) hatte Groq **kein** eigenes Tagesbudget - Kommentar
im Code war explizit: "Groqs reales Tageslimit wirkt extern über echte
429s". Das bedeutete: sobald Groqs echtes tägliches Token-Limit erreicht
war, wurde **jeder weitere Kandidat** - in diesem UND allen folgenden
15-Minuten-Läufen desselben Tages - trotzdem zuerst erfolglos gegen Groq
versucht, bevor Mistral übernahm. Kein verlorenes Mistral/Gemini-
Kontingent (der Fallback funktionierte pro Call korrekt), aber unnötige
Latenz: ein garantiert scheiternder HTTP-Call pro Kandidat, den ganzen
Resttag über.

**Warum es diesen Zähler bisher nicht gab:** Groqs echte Tagesgrenze ist
token-basiert, nicht anfrage-basiert - anders als bei Mistral/Gemini gibt
es keine feste Zahl, die man lokal vorab prüfen könnte. Die ursprüngliche
Design-Entscheidung war, das der echten API zu überlassen statt zu raten.

**Fix:** neuer In-Memory-Zustand in `agent/krypto/budget_allocator.py`
(gleiches Muster wie `scheduler/background.py::_consecutive_failures`) -
`_groq_failure_date`/`_groq_failure_count`/`_groq_exhausted_date`. Ab
`groq_exhaustion_schwelle_fehlschlaege` (neuer Config-Wert, Default 2)
aufeinanderfolgenden Groq-Fehlschlägen **am selben Kalendertag (UTC)** wird
Groq in `_mit_fallback_chain()` für den Rest des Tages direkt übersprungen
(kein Call-Versuch mehr) - Kandidaten gehen sofort an Mistral/Gemini.
Schwelle 2 statt 1, damit ein einzelner transienter Netzwerk-Ausrutscher
nicht sofort fälschlich als Tageserschöpfung gewertet wird. Reset erfolgt
implizit über den Kalendertag-Vergleich (kein expliziter Reset-Code nötig)
- passt zur echten Ursache (ein TAGES-Limit). In-Memory statt DB-persistiert
(wie bei `_consecutive_failures`) - überlebt keinen Prozess-Neustart,
bewusst akzeptabel (selten, im schlimmsten Fall wird Groq danach einfach
frisch neu probiert). Ein Datenqualitäts-Gate-Skip (`gate_passed=False`,
kein echter LLM-Call) zählt bewusst NICHT als Erfolg oder Fehlschlag - der
Erfolgs-/Fehlschlag-Zähler wird nur bei einem tatsächlich stattgefundenen
Groq-Call aktualisiert.

Neues `AllocationResult.groq_erschoepft_erkannt`-Feld (Analogie zu
`mistral_budget_erschoepft`/`gemini_budget_erschoepft`) für Logging/
Nachvollziehbarkeit, in der bestehenden Budget-Allocator-Log-Zeile in
`scheduler/background.py` ergänzt.

**Verifikation:** synthetische Tests der Schwellenwert-Logik (1 Fehlschlag
→ noch nicht erschöpft, 2. Fehlschlag → erschöpft, Erfolg setzt nur den
Zähler zurück, nicht das Tages-Flag; simulierter Tageswechsel → alter
Zählerstand wird verworfen, ein einzelner Fehlschlag am neuen Tag erschöpft
noch nicht). Echter End-to-End-Test über zwei komplette
`run_budget_allocator()`-Läufe gegen eine echte (Datei-)DB mit 5 Spot-
Kandidaten und einem Fake-Groq-Client, der immer fehlschlägt: im ersten
Lauf wird Groq genau 2x versucht (dann Schwelle erreicht), alle 5
Kandidaten laufen über Mistral; im zweiten Lauf (simuliert den nächsten
15-Minuten-Takt am selben Tag) wird Groq kein einziges Mal mehr versucht.

## Nachtrag (2026-07-19): erste Notebook-Nacht-Analyse - Misfire-Fehlalarm, klare OI-Fehlermeldungen, persistente OI-Abdeckungs-Warnung pro Symbol

**Auslöser:** erster kompletter Notebook-Nachtlauf mit dem neuen Release.
Der Nutzer schickte einen Screenshot mit mehreren "Job fehlgeschlagen"-
E-Mails kurz nach Mitternacht und bat um eine Detailanalyse. Dafür wurde
zunächst `extract_notebook_diagnose.py` um einen Log-Ausschnitt-Export,
eine Job-Fehlschlag-Historie und eine Groq-Erschöpfungs-Ereignisliste
erweitert (siehe eigener Abschnitt weiter unten) und gegen die echten
Notebook-Logs ausgeführt. Ergebnis: drei unabhängige Funde.

### 1. Falscher Alarm: APScheduler-Misfire bei Sofort-Start-Jobs

Der 00:32-E-Mail-Cluster war **kein Absturz** - alle 7 Jobs, die beim
Scheduler-Start sofort laufen sollen (`next_run_time=datetime.now()`,
u. a. `refresh_prices`, `hebel_screening`, `multi_asset_batch`), liefen
tatsächlich korrekt durch. APScheduler meldet aber standardmäßig nach nur
1 Sekunde (`misfire_grace_time`-Default) ein `EVENT_JOB_MISSED`, wenn der
Scheduler zwischen `add_job()`-Aufruf und tatsächlichem Start etwas
beschäftigt ist (mehrere synchrone `add_job()`-Calls + Vorbereitungsarbeit
beim Start brauchten hier ca. 1,1 Sekunden) - und
`_log_job_event()`s Misfire-Zweig verschickt dafür unbedingt eine
"fehlgeschlagen"-E-Mail, obwohl der Job danach ganz normal lief.

**Fix:** neue Konstante `_IMMEDIATE_START_MISFIRE_GRACE_SECONDS = 300` in
`scheduler/background.py`, als `misfire_grace_time=` an alle 7 betroffenen
`scheduler.add_job(...)`-Aufrufe ergänzt. 5 Minuten statt 1 Sekunde Toleranz
- reicht für jede realistische Scheduler-Startverzögerung, ohne einen
echten, dauerhaft blockierten Job zu verschleiern (der würde nach 5 Minuten
immer noch als Misfire gemeldet).

### 2. Wiederkehrender Fund: fünf Symbole ohne Open-Interest-Daten

Dieselbe Log-Analyse zeigte ein **echtes, wiederkehrendes** (nicht
einmaliges) Muster: KAS, KAIA, FLOKI, TURBO und CANTON scheiterten beim
15-Minuten-Hebel-Screening regelmäßig bei **allen drei** OI-Börsen
(Binance/Bybit/OKX) mit einem nichtssagenden `IndexError: list index out
of range`. Ursache: Bybit/OKX antworten bei einem auf der jeweiligen Börse
nicht gelisteten Symbol mit HTTP 200 und einer **leeren** Liste statt einem
Fehlerstatus - `liste[0]` warf dafür nur den rohen IndexError statt einer
erklärenden Meldung. War vorher schon abgefangen (P-10-Isolation, kein
Crash), aber ohne erkennbaren Grund im Log.

**Fix:** neue `NoOpenInterestDataError`-Exception + `_erstes_element()`-
Hilfsfunktion in `api/derivatives.py`, ersetzt die drei rohen
`liste[0]`-Zugriffe (Bybit-OI, OKX-OI, Binance-Long-Short-Ratio). Ändert
NICHTS am Fehlerverhalten selbst (weiterhin pro Börse einzeln
abgefangen), macht die Ursache im Log aber sofort erkennbar.

### 3. Nutzer-Vorschlag: sichtbare Warnung bei dauerhaft fehlender OI-Abdeckung

Der Nutzer fragte, ob ein solcher wiederholter Fehlschlag nicht auch ein
"relativ eindeutiges Zeichen" sei, dass die Hebel-Prüfung für so ein Symbol
u. U. problematisch sei, und ob das für eine gewisse Zeit in GUI/E-Mail
sichtbar gemacht werden sollte, gerade weil es sich um ein dauerhaftes (nicht
nur vorübergehendes) Problem handeln könnte.

**Bewertung:** zugestimmt, mit einer bewussten Einschränkung - **kein
automatisches Abschalten** der Hebel-Prüfung. Ein fehlender OI-Wert ist ein
Kontextverlust (das Hebel-Signal wird ohne Positionierungs-Kontext
bewertet), kein Grund, die Prüfung selbst zu unterbinden - die Entscheidung
soll beim Nutzer über den bestehenden Hebel-Prüfung-Toggle bleiben, nicht
beim System automatisch getroffen werden.

**Fix, drei Teile:**

- **Neue Tabelle** `oi_abdeckung_status` (`database/db.py`) - ein Zustand
  je SYMBOL (nicht je Börse wie bei `api_health_status`), weil erst das
  gleichzeitige Scheitern bei ALLEN drei Börsen als ein Fehlschlag zählt
  (siehe `fetch_and_store_oi_snapshot()`-Rückgabewert, jetzt `bool`).
  4 neue Funktionen: `record_oi_abdeckung_ergebnis()` (Erfolg setzt den
  Zähler zurück, Fehlschlag erhöht ihn), `get_oi_abdeckung_status()` (für
  die GUI), `get_symbole_mit_ueberschrittener_oi_schwelle()` (Schwelle +
  Cooldown-Filter, gleiches Prinzip wie beim Cash-Veto),
  `set_oi_abdeckung_gemeldet()`. DB-persistiert statt in-memory wie bei der
  Groq-Erschöpfung oben - bewusst, weil dieser Zustand laut Nutzer-
  Einschätzung potenziell DAUERHAFT ist und einen Neustart überleben soll,
  nicht nur eine kurze Störung wie Groq.
- **E-Mail-Warnung** (`scheduler/background.py::_notify_oi_abdeckung_
  warnung()` + `_pruefe_oi_abdeckung_warnung()`, aufgerufen direkt nach
  jedem `run_hebel_screening()`-Lauf) - neue Config-Werte
  `oi_abdeckung_schwelle_fehlschlaege` (Default 8, also gut 2 Stunden
  durchgängiger Fehlschlag bei 15-Minuten-Takt) und `oi_abdeckung_warnung_
  cooldown_stunden` (Default 24) unter `hebel_screening:`. Erklärt in der
  Mail explizit: keine automatische Abschaltung, Hinweis auf den manuellen
  Toggle. Die Meldung wird nur bei TATSÄCHLICH verschicktem Mail-Erfolg als
  "gemeldet" markiert (nicht schon beim bloßen Versuch) - sonst würde eine
  deaktivierte E-Mail-Benachrichtigung oder ein Versandfehler den Cooldown
  fälschlich anlaufen lassen und eine später (wieder) aktivierte Warnung
  bis zu 24 Stunden lang unterdrücken, obwohl nie etwas verschickt wurde
  (im ersten Entwurf ein echter Bug, beim Testen gefunden und behoben).
- **GUI-Markierung** (`ui/app.py`, Watchlist-Tab) - ein `⚠`-Zeichen direkt
  in der bestehenden Hebel-Prüfung-Spalte, wenn `konsekutive_fehlschlaege
  >= oi_abdeckung_schwelle_fehlschlaege`, mit erklärendem Spalten-Tooltip.
  Kein neuer Schalter, keine automatische Aktion - reine Sichtbarmachung.

**Verifikation:** 8 synthetische DB-Tests für die neue Tabelle/Funktionen
(Erfolg setzt zurück, Schwelle wird erkannt, Symbol darunter wird NICHT
gemeldet, Cooldown unterdrückt eine zweite Meldung, Cooldown=0 hebt das
sofort wieder auf, Erholung setzt den Zähler zurück). End-to-End-Test von
`_pruefe_oi_abdeckung_warnung()` mit gemocktem E-Mail-Versand (genau 1 Mail
für das Symbol über der Schwelle, keine für das Symbol darunter, Cooldown
verhindert eine zweite Mail, deaktivierte E-Mail verschickt nichts UND
markiert nichts als gemeldet - deckte den oben beschriebenen Bug auf, der
noch vor der Verifikation behoben wurde). Tk-Smoke-Test der Watchlist-
Spalte (Warnzeichen erscheint für das Symbol über der Schwelle, fehlt beim
Symbol darunter). Migrationstest gegen eine echte Kopie der Produktions-DB
(`init_db()` legt die neue Tabelle sauber an, bestehende `cash_veto`-Spalten
weiterhin vorhanden). Regressionstest der `NoOpenInterestDataError`/
`_erstes_element()`-Fixes sowie aller 7 `misfire_grace_time`-Ergänzungen.

### Erweiterung: `extract_notebook_diagnose.py` konsolidiert Log-Analyse

Im Zuge dieser Analyse wurde außerdem ein zweites, nicht im Repo verwaltetes
Export-Skript entdeckt (6-Datei-Format, offenbar direkt auf dem Notebook
entstanden und nie zurücksynchronisiert). Statt es zu pflegen, wurde
`extract_notebook_diagnose.py` (das bereits bestehende, repo-versionierte
Skript) erweitert: optionales Log-Zeitfenster (Standard 72 Stunden,
CLI-Parameter), Log-Zeilen-Auszug inkl. mehrzeiliger Tracebacks,
extrahierte Job-Fehlschlag-Historie, extrahierte Groq-Erschöpfungs-
Ereignisse, sowie eine regelbasierte Auffälligkeiten-Liste (u. a.
`risk_veto=True` bei einer Nicht-HALTEN-Aktion) - deckt jetzt sowohl
DB-Snapshot als auch Log-Historie in einem einzigen Export ab. Siehe
Memory `reference_notebook_analyseordner_standard`.

### Nachtrag: zwei weitere yfinance-"nur fast_info"-Ticker in die Unterdrückungsliste aufgenommen

Dieselbe Log-Analyse zeigte 826 yfinance-ERROR-Zeilen ("possibly delisted;
no price data found") über das 72-Stunden-Fenster. Fünf der betroffenen
Ticker (OD7N/3QSS/OD7L/OD7H/OD7C) waren bereits seit 2026-07-16 als bekannte,
unkritische "nur fast_info"-Fälle in `api/yfinance_client.py::
YFINANCE_HISTORY_UNRELIABLE_TICKERS` erfasst und wurden per Logging-Filter
in `main.py` unterdrückt. Zwei weitere Ticker - X136.BE und IS0C.DE (X136/
ISOC) - zeigten das identische Muster (je 272 ERROR-Zeilen über 72 Std.,
`fast_info` lieferte dabei durchgehend gültige Kurse, "Wertpapier-Preis-
Refresh: 13 Assets aktualisiert" bei jedem Lauf), waren aber NICHT in der
Liste enthalten und erzeugten dadurch unnötiges Log-Rauschen.

**Fix:** beide Ticker zur `YFINANCE_HISTORY_UNRELIABLE_TICKERS`-Menge
ergänzt (jetzt 7 statt 5 Einträge). Kein funktionaler Fehler, reine
Log-Hygiene - `fast_info` war in allen Fällen erfolgreich, nur `.history()`
schlägt intern erwartungsgemäß fehl (dünn gehandelte ISIN-/Berlin-Börsen-
Instrumente, siehe ursprüngliche Data-Quality-Caveats vom 2026-07-09).

**Verifikation:** Filter synthetisch gegen die echten Log-Zeilen getestet -
X136.BE/IS0C.DE/OD7C.SG werden jetzt unterdrückt, ein unbekanntes Symbol
(Kontrollfall) bleibt weiterhin sichtbar (P-10-Prinzip unverändert: nur
bestätigte Fälle werden unterdrückt, kein pauschales Wegfiltern).

## Nachtrag (2026-07-19): Liquidationspreis-Sicherheitsmarge neu kalibriert

**Auslöser:** Nutzer-Beobachtung beim gemeinsamen Durchsehen zweier echter
Hebel-Empfehlungs-E-Mails (VIRTUAL/AVAX): "den Liquidationspreis müssen wir
auf ein realistisches Niveau bringen, ist u.U. zu restriktiv." Der bisherige
Config-Wert `liquidations_sicherheitsmarge_relativ: 0.175` (17,5%) war seit
seiner Einführung explizit als `[OFFEN]` markiert - laut Kommentar nur ein
"Mittelwert einer 15-20%-Spanne", **keine echte Quelle**, nicht kalibriert.

**Vorgehen:** zwei unabhängige Kalibrierungsquellen kombiniert.

1. **Bitpandas offizielle Doku** (Bitpanda Helpdesk, "Amplify your trading
   with Bitpanda Leverage"): Liquidation greift, wenn Margin Level =
   Positionswert / (Kreditbetrag + Tagesgebühren) unter ~105-110% fällt.
   Mathematisch übersetzt in unsere Formel (sicherheitsmarge_relativ =
   1 - 1/Schwelle) ergibt das einen theoretisch plausiblen Bereich von
   **4,76% bis 9,09%**.
2. **4 echte, aus der Bitpanda-Transaktionshistorie rekonstruierte
   Liquidationsfälle** (LINK id=5, TAO id=77, TAO id=87, SUI id=54, alle aus
   `importer/bitpanda_margin_positions.py`, Status `wahrscheinlich_
   liquidiert`) gegen die echte tägliche OHLC-Kurshistorie der App geprüft.
   Bei 2 Fällen (TAO id=87, SUI id=54) verlief der Kurs am Schließungstag
   ruhig statt in einem Crash-Docht, was eine präzise Rückrechnung erlaubte:
   implizierte Marge **6,75% (SUI)** bzw. **8,4% (TAO)** - beide innerhalb
   des Bitpanda-Bereichs. Die beiden anderen Fälle (LINK, TAO id=77) hatten
   Crash-Dochte weit unterhalb der berechneten Zone, was nicht widerspricht,
   aber keine präzise Eingrenzung erlaubt. Zusammen mit dem bereits am
   2026-07-16 live verifizierten LINK-Fall (~6,5%, siehe oben) ergeben sich
   **drei präzise Datenpunkte im Bereich 6,5%-8,4%**, alle konsistent mit der
   offiziellen Bitpanda-Spanne.

**Fix:** `liquidations_sicherheitsmarge_relativ` von 0,175 auf **0,09 (9%)**
gesetzt - knapp über dem höchsten real beobachteten Wert (8,4%), damit
bewusst weiterhin ein kleiner Sicherheitspuffer, aber keine ~2x-Übertreibung
mehr. Wirkt an zwei Stellen gleichzeitig (Nutzer-Vorgabe: "Anpassung soll
generell passieren, auch bei den Signalen und Empfehlungen"):
- `estimate_liquidation_price()` - der angezeigte "Geschätzte
  Liquidationspreis" in App/E-Mail liegt jetzt näher an der Realität.
- `max_safe_hebel()` (RM-11) - der Deckel für den bei neuen Positionen
  empfohlenen Hebel erlaubt jetzt etwas mehr (bei 15% Stop-Loss-Distanz z. B.
  6,07x statt vorher 5,50x maximal sicherer Hebel).

**Verifikation:** Reproduktion des LINK-Live-Falls (Entry 7,42 €, Hebel 5x)
mit dem neuen Wert ergibt 6,52 € gegen den echten Bitpanda-Wert 6,3515 € -
Abweichung nur noch +2,7% (vorher +13,3% mit 17,5%), UND weiterhin in der
sicheren Richtung (zeigt Liquidation nicht später an als real). `config.yaml`
lädt den neuen Wert korrekt, Syntax-/YAML-Validität beider geänderten
Dateien bestätigt.

## Nachtrag (2026-07-19): Retail-Konsens-Deckel + Risikofaktoren-Liste + 3-Abschnitte-Neustrukturierung (E-Mail/App, alle Assetklassen)

**Auslöser:** gemeinsame Durchsicht zweier echter Hebel-Empfehlungs-E-Mails
(VIRTUAL, AVAX) deckte zwei Inkonsistenzen auf:

1. **AVAX-Signal** begründete eine LONG-Empfehlung u. a. mit "Retail-Bias
   extrem long (65,9% Long-Konten), was für eine Gegenbewegung spricht" -
   eine antizyklische Beobachtung, die logisch GEGEN LONG spricht (eine
   bereits stark in eine Richtung positionierte Crowd wird bei einer
   Gegenbewegung zuerst liquidiert/ausgestoppt), aber trotzdem zur Stützung
   von LONG verwendet wurde.
2. Beide Signale hatten `trade_thesis_typ: swing_strategie` ("bestätigter,
   noch nicht ausgereizter Trend") UND gleichzeitig einen erkannten
   Regime-Konflikt (Position widerspricht dem Regime) - ein innerer
   Widerspruch in der eigenen Klassifikation.

Der Nutzer bat außerdem darum, E-Mail und App-Detailansicht für **alle**
Assetklassen einheitlich in drei Abschnitte zu gliedern: 1. was ist
mathematisch berechnet, 2. was sagt die LLM-Bewertung, 3. eine ausführliche
Konklusion mit positiven/neutralen/negativen Risikofaktoren.

### 1. Retail-Konsens-Deckel (neu, Hebel) + Prompt-Fix (Hebel UND Spot)

Ursachenanalyse: `build_hebel_facts()`/`build_facts()` liefern dem Modell nur
Rohzahlen (Long-Konten-Anteil, zwei Extrem-Flags) - **keine** Regel im
SYSTEM_PROMPT erklärte bisher, wie ein extremer Retail-Konsens richtungsmäßig
zu interpretieren ist. `agent/krypto/anticyclic.py`s einzige gerichtete Logik
ist an den Spezialfall "möglicher Flush nach Kursabsturz" gekoppelt, keine
allgemeingültige Übersetzung.

**Fix, zwei Ebenen (wie überall in diesem System - nie blind auf
Prompt-Befolgung vertrauen):**
- **Prompt-Regel** (`hebel_analyst.py` Regel 8, `analyst.py` Regel 15):
  extremer Retail-Konten-Anteil in eine Richtung ist ein Kontraindikator
  GEGEN diese Richtung - ein `top_gruende`-Eintrag mit `kategorie:
  antizyklisch`, der auf Retail-Konsens verweist, darf NIEMALS dieselbe
  Richtung wie die eigene Empfehlung stützen.
- **Neuer deterministischer Hebel-Deckel** `retail_konsens_hebel_deckel`
  (config.yaml, 3.0): `hebel_risk_gate.py::retail_konsens_risiko()` - True,
  wenn `retail_long_bias_extreme` UND `richtung == LONG` (bzw. symmetrisch
  `long_account_pct <= 35%` UND `richtung == SHORT`, gleiche 65%-Schwelle wie
  `anticyclic.py::LONG_BIAS_EXTREME_THRESHOLD_PCT`). Als fünfter Kandidat in
  `_hebel_deckel_kandidaten()` ergänzt.
- **These-Regime-Widerspruch** (neu, reine Sichtbarmachung, KEIN Deckel - es
  gibt keine saubere numerische Dimension dafür): `hebel_risk_gate.py::
  these_regime_widerspruch()` - True, wenn `trade_thesis_typ == swing_
  strategie` UND gleichzeitig ein Regime-Konflikt vorliegt.
- `regime_konflikt_hebel()` als eigene Funktion extrahiert (vorher inline in
  `_hebel_deckel_kandidaten()`), damit Deckel-Logik UND Risikofaktoren-Liste
  auf exakt derselben Bedingung basieren.

### 2. Neue Risikofaktoren-Liste (Kern von Abschnitt 3)

`agent/krypto/hebel_risk_gate.py::compute_risikofaktoren_hebel()` und
`agent/krypto/risk_gate.py::compute_risikofaktoren()` (Spot/Aktien/Rohstoffe/
Themen-ETF-Pendant) fassen alle bereits vorhandenen Deckel-/Veto-Checks
deterministisch in eine kompakte 🟢positiv/⚪neutral/🔴negativ-Liste
zusammen - bewusst NICHT vom LLM generiert (genau das war beim AVAX-Fund das
Problem). Geprüfte Faktoren: Regime-Konflikt, These-Regime-Widerspruch
(nur Hebel), Gegenszenario-Wahrscheinlichkeit, technische Konfluenz, CRV-Höhe,
Retail-Konsens-Risiko, Konfidenz-Niveau, sowie Cash-Veto/Risiko-Veto als
Kurzschluss-Fälle (Spot). Jeder Check liefert sowohl den negativen ALS AUCH
den positiven Gegenfall (z. B. "Regime-Ausrichtung: positiv", wenn KEIN
Konflikt vorliegt) - keine reine Fehlerliste, sondern eine vollständige
Bilanz.

Neues Feld `risikofaktoren_json` (JSON-serialisierte Liste von `{name,
bewertung, begruendung}`) auf `Signal` UND `HebelSignal` (additive Migration,
beide Tabellen), deterministisch am Ende von `post_check()`/
`post_check_hebel()` berechnet und in der Pipeline persistiert (`hebel_
pipeline.py` und alle 4 Spot-family-Pipelines).

### 3. 3-Abschnitte-Neustrukturierung (E-Mail + App, alle Assetklassen)

`scheduler/background.py`: alle drei E-Mail-Builder (`_notify_spot_signal()`,
`_notify_hebel_signal()`, `_notify_multi_asset_signal()`) sowie `ui/hebel_
view.py`/`ui/signals_view.py`s Detail-Panels zeigen jetzt einheitlich:

- **1. MATHEMATISCH BERECHNET** - bei Hebel: Hebel final, Liquidationspreis,
  Eigenkapitalbedarf/-Nachschuss, Ausführbarkeit. Bei Spot/Aktien/Rohstoffe/
  Themen-ETF: Boden-Zielzone, Cash-Reserve-Ziel (beide AZ-4-Bausteine,
  vollständig deterministisch).
- **2. LLM-BEWERTUNG (Konfidenz X%)** - Kurz-/Langbegründung, Top-Gründe,
  **Gegenargument (NEU - existierte seit 2026-07-18 als Pflichtfeld, fehlte
  aber bisher komplett in E-Mail UND App)**, Entry/SL/TP-Zonen, Positions-
  größe/Tranchen, Halte-Kriterium, wichtigste Risiken, **Forecast-Szenarien
  (NEU, waren bisher nur in der DB sichtbar)**.
- **3. KONKLUSION (RISIKOFAKTOREN)** - die neue deterministische Liste.

Neue gemeinsame Formatierungs-Helper: `scheduler/background.py::
_formatiere_gegenargument()`/`_formatiere_forecast()`/`_formatiere_
risikofaktoren()` (E-Mail-Textformat) und `ui/formatting.py::format_
risikofaktoren_lines()` (App-Textformat, von beiden Detail-Panels
wiederverwendet).

**Verifikation:** 9 synthetische Testgruppen (Pure-Funktionen isoliert,
`compute_risikofaktoren_hebel()` reproduziert den echten AVAX-Fall korrekt
mit 3 negativen Flags, sauberer Gegenfall überwiegend positiv, Kurzschluss-
Fälle bei `hebel_erlaubt=False`/`cash_veto=True`, `post_check_hebel()`
End-to-End bestätigt Deckel-Wert UND Risikofaktoren-Liste gleichzeitig
korrekt). Tk-Smoke-Test beider Detail-Panels (alle 3 Abschnitte + Gegen-
argument + Risikofaktoren korrekt gerendert, inkl. Sortierung negativ vor
positiv). E-Mail-Formatierungstest (Gegenargument/Forecast/Risikofaktoren-
Text, leerer Fall ohne Exception). DB-Roundtrip-Test gegen echte
Produktions-DB-Kopie für beide Tabellen. Gesamt-Import-Check aller 15
geänderten Module fehlerfrei, `retail_konsens_hebel_deckel` lädt korrekt aus
`config.yaml`.

## Nachtrag (2026-07-19, gleicher Tag): "Info-Leichen" - automatischer Verfall
unanalysierter Hebel-Kandidaten

**Auslöser:** Nutzer bemerkte im Hebel-Tab eine lange Liste von Kandidaten
("Kandidat (wartet auf Analyse)") mit Zeitstempeln bis zu 3 Tage zurück und
fragte, ob sich diese von selbst ausschleichen. Antwort nach Codeprüfung:
**nein** - `hebel_triggers` bekommt bei jedem 15-Min-Screening-Tick nur dann
eine neue Zeile, wenn der Score-Schwellenwert erneut erreicht wird
(`agent/krypto/hebel_screening.py::run_hebel_screening()`). Sinkt der Score
später wieder (Marktbedingung nicht mehr gegeben), bleibt die alte
`status='neu'`-Zeile trotzdem als "neuester Kandidat" bestehen -
`update_hebel_trigger_status()` wird nur beim tatsächlichen LLM-Verbrauch
aufgerufen (`agent/krypto/hebel_pipeline.py`), es gab weder eine
Alters-Ablaufgrenze noch (anders als beim Marktscan-Tab) einen manuellen
"Ablehnen"-Button.

**Funktional relevant, nicht nur optisch:** `db.get_pending_hebel_candidates()`
sortiert nach `score_gesamt DESC`, nicht nach Aktualität - sowohl die
Hebel-Tab-Anzeige als auch der Budget-Allocator (`agent/krypto/
budget_allocator.py`) übernehmen diese Reihenfolge unverändert. Ein alter,
hoch bewerteter, aber längst überholter Kandidat konnte damit einen
frischen, niedriger bewerteten Kandidaten dauerhaft um das knappe
LLM-Budget verdrängen.

**Fix (Nutzerentscheidung: automatischer Verfall nach X Stunden, kein
manueller Button):** neue Funktion `database/db.py::
expire_stale_hebel_candidates(conn, verfall_stunden)` setzt Trigger mit
`status='neu'` und `screened_at` älter als die Schwelle auf
`status='verfallen'` (einfaches UPDATE, kein neuer Tabellen-Status-Enum
nötig, da `hebel_triggers.status` kein CHECK-Constraint hat). Aufgerufen am
Ende jedes Screening-Laufs (`run_hebel_screening()`, nach dem Insert aller
neuen Trigger), mit Log-Zeile bei tatsächlichem Verfall. Neuer Config-Wert
`hebel_screening.hebel_kandidat_verfall_stunden` (48h) - lang genug, um eine
einzelne budgetknappe Tagesphase zu überstehen, kurz genug, um wochenlanges
Anwachsen zu verhindern. Da sowohl die UI-Anzeige als auch der Allocator
`get_pending_hebel_candidates()` nutzen (WHERE `status='neu'`), verschwinden
verfallene Kandidaten automatisch aus beiden Stellen, ohne dass an der
Abfrage selbst etwas geändert werden musste.

**Verifiziert:** synthetischer In-Memory-Test (3 Kandidaten - alt/status=neu,
frisch/status=neu, alt/status=llm_generiert; nach Verfall bleibt nur der
frische als pending, der bereits verarbeitete bleibt unangetastet,
zweiter Aufruf ist idempotent/findet nichts mehr). DB-Roundtrip gegen eine
Kopie der echten Produktions-DB (1 echter Kandidat, FLOKI vom 14.07., korrekt
als verfallen erkannt und aus der Pending-Liste entfernt) - dabei auffällig:
die lokale Desktop-DB enthält deutlich weniger Kandidaten als der vom
Nutzer gezeigte Notebook-Screenshot, konsistent mit der bekannten
Desktop/Notebook-DB-Trennung (getrennte lokale Datenbanken, siehe Kapitel
zum USB-Sync-Workflow).

## Nachtrag (2026-07-19, gleicher Tag): Konsistenz-Ausweitung des Verfall-Fixes
auf Marktscan-Kandidaten

Nutzer bat explizit darum, den gerade gebauten Hebel-Verfall-Fix auf andere
Bereiche zu prüfen, damit das System konsistent bleibt. Codeweite Suche nach
allen "Kandidat-wartet-auf-Analyse"-Warteschlangen (Muster: `status='neu'`,
Selektion via Self-Join auf neuesten Eintrag) ergab genau eine weitere
Stelle mit derselben Struktur-Schwäche: `marktscan_candidates`
(`db.get_pending_marktscan_kaufkandidaten()`, ebenfalls
`score_gesamt DESC` statt aktualitätssortiert). Multi-Asset-Batch (Aktien/
Rohstoffe/Themen-ETF) und Hedge sind **strukturell nicht betroffen** - sie
iterieren pro Lauf direkt über die aktuelle Watchlist mit Cooldown-Logik
(`agent/multi_asset_batch.py::_kandidaten()`), es gibt dort keine separate
Scoring-Warteschlange, die veralten könnte.

**Fix (identisches Muster wie Hebel):** neue `database/db.py::
expire_stale_marktscan_candidates(conn, verfall_stunden)`, scoped auf
`einstufung='kaufkandidat' AND status='neu' AND groq_generiert_am IS NULL`
(exakt die Bedingungen von `get_pending_marktscan_kaufkandidaten()`). Neuer
Config-Wert `budget_allocator.marktscan_kandidat_verfall_stunden` (48h).
**Ein Unterschied zum Hebel-Fix:** der Aufruf sitzt NICHT in der Discovery-
Funktion (`agent/krypto/marktscan.py::run_scan()`, läuft nur 2x/Tag um
04:00/16:00), sondern in `agent/krypto/budget_allocator.py::
run_budget_allocator()` direkt vor dem Abruf der Pending-Kandidaten - der
Allocator läuft alle 15 Min (huckepack auf `hebel_screening_job`), damit
bleibt die Warteliste deutlich zeitnaher aktuell als bei einer Kopplung an
den seltenen Scan-Takt. Ergänzt (ersetzt nicht) den bereits bestehenden
manuellen "Ablehnen"-Button im Marktscan-Tab (`status=
'nutzer_verworfen'`) - der deckt nur Kandidaten ab, die der Nutzer aktiv
sieht und beurteilt, der automatische Verfall greift zusätzlich für alle
anderen. `ui/marktscan_view.py::STATUS_LABELS` um `"verfallen": "verfallen
(zu alt)"` ergänzt, damit der neue Status in der allgemeinen
Kandidatenliste lesbar dargestellt wird (die Pending-Abfrage selbst filtert
ihn bereits automatisch heraus).

**Verifiziert:** synthetischer In-Memory-Test (4 Kandidaten - alt/
kaufkandidat/neu, frisch/kaufkandidat/neu, alt/bereits mit
`groq_generiert_am` versehen, alt/andere Einstufung "beobachten"; nach
Verfall bleibt nur der frische pending, die anderen drei bleiben
unangetastet weil außerhalb der Verfall-Bedingung, zweiter Aufruf
idempotent). Import-Check aller geänderten Module fehlerfrei.

## Nachtrag (2026-07-19, gleicher Tag): echter KAITO-Fund - Geschwisterzeilen
beim Übernehmen/Verwerfen nicht mitaufgelöst

**Auslöser:** Nutzer hatte zum ersten Mal einen Marktscan-Kandidaten über
"In Watchlist übernehmen" real in die Watchlist aufgenommen (KAITO), die App
neu gestartet und danach im Marktscan-Tab immer noch eine KAITO-Zeile mit
Status "neu" gesehen - obwohl der Coin bereits übernommen war.

**Root Cause (zwei zusammenhängende Stellen):**
1. `marktscan_candidates` hat `UNIQUE(coingecko_id, scan_run_id)` - jeder
   neue Scan-Lauf, der denselben Coin erneut findet, legt eine EIGENE Zeile
   an. Klickt der Nutzer "In Watchlist übernehmen" auf EINER dieser Zeilen,
   setzte `ui/marktscan_view.py` bisher nur den Status GENAU dieser einen
   Zeile (`db.update_marktscan_candidate_status(conn, candidate.id, ...)`) -
   andere, bereits vorher ODER danach entdeckte Zeilen desselben Coins
   blieben unverändert `status='neu'` und wirkten wie eine "nie aktualisierte"
   Info-Leiche.
2. Zusätzlich fand sich beim Nachvollziehen ein zweiter, eigenständiger Bug:
   `db.get_latest_marktscan_status_by_coingecko_id()` (der Cross-Lauf-
   Duplikat-Check in `_duplicate_should_skip()`) sortiert nach
   `discovered_at DESC` - also nach ENTDECKUNGSZEITPUNKT, nicht danach,
   welche Zeile die tatsächliche Nutzer-ENTSCHEIDUNG trägt. Im KAITO-Fall
   war die spätere, nie angeklickte Zeile (14 Uhr) chronologisch "neuer" als
   die tatsächlich übernommene (2 Uhr) - die Funktion hätte fälschlich
   `'neu'` statt `'nutzer_behalten_manuell_uebernommen'` zurückgegeben, was
   künftige Scans theoretisch wieder hätte verwirren können (in diesem
   konkreten Fall zusätzlich durch den bereits vorhandenen
   Watchlist-Mitgliedschafts-Check in `_duplicate_should_skip()` abgefangen,
   aber nicht robust).

**Fix:** neue `database/db.py::resolve_marktscan_candidate_siblings(conn,
coingecko_id, status)` - setzt ALLE noch `status='neu'`-Zeilen desselben
`coingecko_id` auf den neuen Status. Aufgerufen direkt nach dem bestehenden
Einzelzeilen-Update in BEIDEN Handlern (`_on_adopt_to_watchlist_clicked()`
und `_on_reject_clicked()` in `ui/marktscan_view.py`). Löst damit auch
Punkt 2 auf, ohne die Sortierlogik selbst anfassen zu müssen: sobald alle
Zeilen eines entschiedenen Coins konsistent denselben Status tragen, ist es
irrelevant, welche davon `get_latest_marktscan_status_by_coingecko_id()`
zurückgibt. Nebenbei `_on_reject_clicked()` um ein fehlendes
`self._refresh_list()` ergänzt (war vorher nicht vorhanden, `_on_adopt_
to_watchlist_clicked()` hatte es bereits) - sonst wären die aufgelösten
Geschwisterzeilen zwar in der DB korrekt, aber nicht sofort sichtbar
gewesen.

**Verifiziert:** synthetischer Test reproduziert den echten KAITO-Fall 1:1
(zwei Zeilen desselben `coingecko_id`, früh entdeckte übernommen, spät
entdeckte bleibt `status='neu'`) - bestätigt zunächst den Bug
(`get_latest_marktscan_status_by_coingecko_id()` liefert fälschlich `'neu'`),
dann den Fix (nach `resolve_marktscan_candidate_siblings()` liefert dieselbe
Abfrage korrekt `'nutzer_behalten_manuell_uebernommen'`, die zweite Zeile
trägt jetzt denselben Status, zweiter Aufruf idempotent). Import-Check
fehlerfrei.

## Nachtrag (2026-07-19, gleicher Tag): Watchlist-Tab-Konsistenzprüfung -
fehlende coingecko_id verschwendet dauerhaft Spot-Budget

**Auslöser:** Nutzer bat explizit darum, die Watchlist-Tab-Konsistenz
ebenfalls zu prüfen (nach den Info-Leichen-Funden bei Hebel/Marktscan).
Codeprüfung ergab keine Duplikat-/Entfernungs-Lücke (`add_watchlist_entry()`
prüft bereits zentral auf doppelte Symbole, alle drei Aufrufer -
Marktscan-Übernehmen, manueller "Asset hinzufügen"-Dialog, Hebel-Auto-Add -
nutzen dieselbe Funktion; ein "Watchlist entfernen"-Feature existiert
bewusst nicht, die Datei ist explizit handgepflegt). Stattdessen ein
eigenständiger, bisher unbemerkter struktureller Bug gefunden.

**Root Cause:** ein per `importer/bitpanda_margin_positions.py::
auto_add_unknown_hebel_symbols()` automatisch ergänztes Krypto-Asset (offene
Hebel-Position auf einem noch unbekannten Symbol) bekommt bewusst KEINE
`coingecko_id` (keine zuverlässige automatische Symbol→ID-Auflösung, siehe
Docstring dort). `agent/krypto/signal_batch.py::
select_assets_due_for_signal()` filterte bisher nur nach `assetklasse ==
"krypto"`, nicht zusätzlich auf eine gesetzte `coingecko_id`. Ohne ID liefert
`agent/krypto/pipeline.py::generate_signal()` strukturell IMMER sofort ein
Fixed-HALTEN (`gate_reason='keine historischen Daten vorhanden'`), OHNE
`groq_raw_response` zu setzen - `db.get_latest_real_signal_per_symbol()`
(WHERE `groq_raw_response IS NOT NULL`) sieht das Asset dadurch für immer als
"nie berechnet". Da `select_assets_due_for_signal()` "nie berechnet zuerst"
sortiert, wäre so ein Asset bei JEDEM 15-Min-Budget-Allocator-Lauf dauerhaft
an Position 1 der Prioritätsliste gelandet und hätte einen echten
Spot-Budget-Slot verschwendet - unbegrenzt, ohne jede sichtbare Warnung.
Aktuell 0 betroffene Symbole in der lokalen Watchlist (noch nicht
zugeschlagen), aber strukturell jederzeit möglich, sobald eine Hebel-Position
auf einem neuen, unbekannten Symbol eröffnet wird.

**Fix (zwei Ebenen, gleiches Muster wie beim Info-Leichen-Fix):**
1. `select_assets_due_for_signal()` filtert jetzt zusätzlich auf
   `a.coingecko_id` (truthy) - das Asset wird gar nicht erst als Kandidat
   ausgewählt, verschwendet also keinen Slot mehr.
2. `ui/app.py::_refresh_watchlist_from_db()` markiert ein betroffenes Asset
   sichtbar in der Status-Spalte ("⚠ keine CoinGecko-ID", neuer Tag
   `coingecko_id_fehlt`, `theme.danger_color()` wie beim bestehenden
   `bitpanda_fehlt`-Muster) UND in der Spalten-Kopfzeilen-Tooltip - der
   Nutzer sieht so weiterhin, WARUM Spot-Analyse für dieses Symbol inaktiv
   ist, und kann die ID über den bestehenden "Asset hinzufügen/bearbeiten"-
   Dialog nachtragen. `ui/signals_view.py`s identisches Filtermuster (manuelle
   "Signal berechnen"-Auswahl) bewusst NICHT geändert - ein manueller Klick
   liefert dort bereits eine klare, sofortige Fehlermeldung, kein
   wiederkehrender stiller Ressourcenverbrauch wie beim automatischen
   Allocator.

**Verifiziert:** synthetischer Test von `select_assets_due_for_signal()`
(Asset ohne `coingecko_id` wird korrekt ausgeschlossen, Asset mit ID bleibt
Kandidat). Tk-Smoke-Test der Watchlist-Tab-Zeile (Asset ohne ID zeigt korrekt
"⚠ keine CoinGecko-ID" + gesetztes Tag, unbetroffenes Asset bleibt
unverändert). Echte Watchlist-Prüfung: aktuell 0 betroffene Symbole.

## Nachtrag (2026-07-19, gleicher Tag): CoinGecko-Symbolsuche im
"Asset hinzufügen/bearbeiten"-Dialog

**Auslöser:** Nutzer fragte direkt nach der obigen Warn-Markierung, warum die
`coingecko_id` nicht einfach automatisch aus dem Symbol ergänzt werden kann.
Live gegen die echte CoinGecko-API geprüft, um die Antwort auf Fakten statt
Vermutung zu stützen: das Symbol (z. B. "SOL") ist bei CoinGecko NICHT
eindeutig - `coingecko_id` ist der interne eindeutige Schlüssel, das Symbol
nur der Ticker. Konkret geteilt: **12 verschiedene IDs** tragen den Ticker
"SOL" (das echte Solana plus 11 gebrückte/gewrappte Varianten über andere
Chains - Base, Near, Eclipse, Neon, Osmosis, Binance). Insgesamt sind 2.116
von 13.704 Symbolen bei CoinGecko mehrdeutig. Eine stille automatische
Zuordnung (z. B. "erstes Ergebnis nehmen") hätte das Risiko, dauerhaft die
FALSCHE Coin-Historie zu laden, ohne dass es auffällt. Marktkapitalisierung
disambiguiert aber zuverlässig (bei SOL: echtes Solana Rang 7 / ~44 Mrd. $,
die Wrapped-Varianten ohne Rang und nur Bruchteile davon) - deshalb Suche
mit Nutzer-Bestätigung statt automatischer Auswahl.

**Umgesetzt (drei Ebenen):**
1. Neue `api/coingecko.py::CoinGeckoClient.search_coins(query)` - nutzt
   CoinGeckos `/search`-Endpunkt (liefert `market_cap_rank` bereits mit, kein
   zusätzlicher `/coins/markets`-Call nötig), sortiert exakte Symbol-Treffer
   zuerst nach Rang aufsteigend (kein Rang zuletzt), danach die übrigen
   Namens-Treffer in CoinGeckos eigener Relevanz-Reihenfolge.
2. Neuer `ui/app.py::CoinSearchDialog` - zeigt die Treffer in einer Tabelle
   (Symbol/Name/ID/Rang), Nutzer wählt per Doppelklick oder Button, KEINE
   automatische Vorauswahl auch bei nur einem Treffer.
3. Neuer "Suchen …"-Button neben dem CoinGecko-ID-Feld in `AssetAddDialog`
   UND `AssetEditDialog` - **wichtiger Nebenbefund dabei:** `AssetEditDialog`
   bot das Feld bisher überhaupt nicht an (Docstring: "Symbol/Name/
   CoingeckoID etc. bleiben hier unverändert"), es gab also für ein bereits
   BESTEHENDES Asset (z. B. genau die im vorherigen Nachtrag beschriebenen
   automatisch ergänzten Hebel-Symbole) gar keinen GUI-Weg, die ID
   nachzutragen - nur beim Erst-Anlegen über `AssetAddDialog`. Jetzt
   ergänzt, sichtbar nur für `assetklasse=krypto`, mit derselben
   Warn-Markierung wie im Watchlist-Tab, falls die ID noch fehlt. Neue
   `config.py::update_watchlist_coingecko_id()` - eigenständige
   Implementierung statt Erweiterung von `_update_watchlist_field()` (die
   kann nur bereits VORHANDENE Feldzeilen aktualisieren, keine neuen
   einfügen - `add_watchlist_entry()` lässt die Zeile bei `coingecko_id=None`
   komplett weg). Fügt die Zeile bei Bedarf direkt nach `beobachtungsstatus:`
   ein (identische Position wie beim Erst-Anlegen), sonst wird die
   vorhandene Zeile aktualisiert - gleiches Backup+Validierungs+Rollback-
   Muster wie alle anderen `config.yaml`-Schreibfunktionen.

**Verifiziert:** live gegen die echte CoinGecko-API (Symbolmehrdeutigkeit
quantifiziert, `search_coins()` liefert für "SOL" korrekt "solana" als
ersten exakten Treffer). Synthetischer Test von
`update_watchlist_coingecko_id()` gegen eine Konfigurationskopie (Einfügen
einer neuen Zeile, Aktualisieren einer vorhandenen, Idempotenz bei
gleichem Wert, unbekanntes Symbol - alle 4 Fälle korrekt). Tk-Smoke-Test
der kompletten Kette: `CoinSearchDialog` direkt, `AssetAddDialog` mit
Suchen-Button, `AssetEditDialog` für ein Krypto-Asset ohne ID (Feld+Warnung
sichtbar, Suche+Auswahl übernimmt korrekt) und für ein Nicht-Krypto-Asset
(Feld bleibt korrekt unsichtbar) - sowie ein echter End-to-End-Test des
kompletten Speicherpfads gegen eine Konfigurationskopie (`_on_submit()`
persistiert die gewählte ID tatsächlich in `config.yaml`).

## Nachtrag (2026-07-19, gleicher Tag): automatische coingecko_id-Aufloesung
per Bitpanda-Namensabgleich - Dialog kommt gleich bei der Aufnahme

**Auslöser:** Nutzer stellte zwei zusammenhängende Fragen zur gerade gebauten
CoinGecko-Symbolsuche: (1) ob der Suchdialog nicht direkt bei der Aufnahme
in die Watchlist erscheinen sollte statt einen manuellen "Suchen"-Klick zu
verlangen, (2) ob der bereits vorhandene CoinGecko-Scan-mit-Bitpanda-Prüfung-
Ablauf (Marktscan-Discovery) das Symbol nicht schon eindeutig machen sollte,
bevor überhaupt eine manuelle Auswahl nötig wird. Live geprüft: Bitpandas
kuratierter Katalog listet nie zwei verschiedene Coins unter demselben
Ticker - der Bitpanda-Name für SOL ("Solana") matcht exakt GENAU EINEN von
25 CoinGecko-Suchtreffern für "SOL". Diese Kreuzreferenz löst die
Mehrdeutigkeit in der überwiegenden Mehrheit der Fälle automatisch auf,
ohne dass der Nutzer manuell auswählen muss - eine echte Mehrdeutigkeit
(kein oder mehr als ein Namenstreffer) bleibt dabei eine ECHTE Inkonsistenz
zwischen Bitpanda- und CoinGecko-Katalog, kein Fall für automatisches Raten.

**Umgesetzt (drei Ebenen):**
1. `api/bitpanda.py::find_listed_asset()` - wie `is_listed()`, gibt aber das
   tatsächlich gefundene `BitpandaAsset`-Objekt zurück statt nur eines Bool
   (fürs Namensfeld gebraucht). `is_listed()` selbst ruft die neue Funktion
   nur noch auf (reiner Refactor, verhaltensidentisch, Regressionstest
   bestätigt).
2. `api/coingecko.py::resolve_coingecko_id_by_name(results, expected_name)`
   - reine Funktion, filtert `search_coins()`-Treffer auf Namensgleichheit,
   gibt nur bei GENAU EINEM Treffer die ID zurück, sonst `None`.
3. Neue gemeinsame `ui/app.py::_try_auto_resolve_coingecko_id(symbol,
   coingecko_client)` - kombiniert beide Bausteine (Bitpanda-Listing prüfen
   + Namensabgleich), genutzt von:
   - **`AssetAddDialog._on_submit()`**: bei leerem CoinGecko-ID-Feld und
     `assetklasse=krypto` wird zuerst still automatisch aufgelöst; schlägt
     das fehl (nicht bei Bitpanda gelistet ODER echte Mehrdeutigkeit), öffnet
     sich der `CoinSearchDialog` jetzt AUTOMATISCH (`self.wait_window()`,
     blockiert bis zur Nutzer-Auswahl/zum Abbrechen) - genau der vom Nutzer
     gewünschte "kommt gleich bei der Aufnahme"-Ablauf, kein manueller Klick
     mehr nötig im Regelfall.
   - **`AssetEditDialog.__init__()`**: still (KEIN Dialog-Popup) versucht,
     sobald ein Krypto-Asset ohne ID geöffnet wird - deckt genau den Fall ab,
     der die ganze Erweiterung ausgelöst hat (automatisch aus einer Hebel-
     Position ergänzte Symbole). Kein Popup beim blossen Öffnen, da der
     Nutzer den Dialog auch nur für rolle/beobachtungsstatus öffnen könnte -
     die Warn-Markierung verschwindet automatisch, wenn die stille Auflösung
     erfolgreich war.
   - **`importer/bitpanda_margin_positions.py::
     auto_add_unknown_hebel_symbols()`**: neuer optionaler `coingecko_client`-
     Parameter (aus `scheduler/background.py::hebel_screening_job()` bereits
     im Scope durchgereicht) - versucht dieselbe Auflösung, BEVOR der
     Watchlist-Eintrag geschrieben wird. Der Nutzer-Punkt "in dieser Schleife
     sollte das Symbol schon eindeutig sein" trifft damit jetzt genau zu -
     das Bitpanda-Listing wird an dieser Stelle ohnehin schon geprüft
     (`find_listed_asset()`), der Namensabgleich kostet nur einen
     zusätzlichen `search_coins()`-Call. `coingecko_client=None` erhält das
     alte Verhalten (ID bleibt leer) für Aufrufer ohne Netzwerkzugriff.

**Verifiziert:** Regressionstest von `is_listed()` nach dem Refactor
(identisches Verhalten). Synthetischer Test von
`resolve_coingecko_id_by_name()` (eindeutig/mehrdeutig/kein Treffer).
Synthetischer Test von `auto_add_unknown_hebel_symbols()` mit drei Fällen
(automatische Auflösung erfolgreich, `coingecko_client=None` behält altes
Verhalten, mehrdeutiger Namenstreffer fällt korrekt auf leer zurück statt
abzustürzen) gegen eine Konfigurationskopie. Tk-Smoke-Test des kompletten
`AssetAddDialog`-Submit-Flows (automatische Auflösung UND automatisch
geöffneter `CoinSearchDialog` bei Mehrdeutigkeit, jeweils bis zum
tatsächlichen Schreiben in `config.yaml` durchgetestet) sowie von
`AssetEditDialog` (stille Auflösung beim Öffnen, Warn-Markierung
verschwindet korrekt bei erfolgreicher Auflösung).

## Nachtrag (2026-07-19, gleicher Tag): Konsistenzprüfung über ALLE
Assetklassen - echter Absturz-Fund bei Aktien ohne yfinance-Symbol

**Auslöser:** Nutzer bat explizit darum, die coingecko_id-Konsistenzprüfung
nicht nur für Krypto/Hebel, sondern für alle Bereiche durchzuführen ("prüfe
das gegenüber allen Bereichen nicht nur Hebel, Spot, etc."). Systematisch
alle vier Multi-Asset-Pipelines (Aktien/Rohstoffe/Hedge/Themen-ETF) auf das
Krypto-Muster (fehlende externe ID → strukturell nie erfolgreiche
Analyse) geprüft.

**Echter, eigenständiger Fund - Absturz statt nur Budget-Verschwendung:**
`agent/aktien/pipeline.py::_ensure_ohlc_backfilled()` rief
`get_full_ohlc_history(asset.yfinance_symbol, ...)` bisher OHNE Guard auf -
im Gegensatz zum strukturell identischen `agent/themen_etf/pipeline.py`,
das den Guard (`if not asset.yfinance_symbol: ... return`) bereits hatte.
Live bestätigt: `yf.Ticker(None)` wirft `AttributeError: 'NoneType' object
has no attribute 'upper'`. Ein manuell hinzugefügtes Aktien-Asset ohne
yfinance-Symbol (im "Asset hinzufügen"-Dialog als "optional" markiert)
hätte damit sowohl im automatischen Multi-Asset-Batch als auch beim
manuellen "Signal berechnen"-Klick einen rohen, unbehandelten Absturz
ausgelöst statt einer sauberen HALTEN-Meldung.

**Geprüft und für strukturell unbetroffen befunden:**
- `agent/rohstoff/pipeline.py`: nutzt einen hartkodierten Futures-Ticker
  (`SYMBOL_ZU_FUTURES_TICKER`), unabhängig vom Watchlist-Feld - ein neues
  Rohstoff-Asset bräuchte ohnehin eine Code-Änderung, kein GUI-Feld dafür.
- `agent/hedge/pipeline.py`: braucht überhaupt keine OHLC-Historie (arbeitet
  nur mit Live-Preisen + Portfolio-Exposure).
- **Auto-Add-Mechanismus:** `config.py::add_watchlist_entry()` wird
  automatisch nur an GENAU EINER Stelle aufgerufen
  (`auto_add_unknown_hebel_symbols()`) - kein analoges automatisches
  Hinzufügen für Aktien/Rohstoffe/ETF, die kommen nur über den manuellen
  "Asset hinzufügen"-Dialog rein.

**Fix (drei Ebenen, gleiches Muster wie beim Krypto-Fund):**
1. `agent/aktien/pipeline.py::_ensure_ohlc_backfilled()` bekommt denselben
   Guard wie `themen_etf/pipeline.py` - fällt jetzt sauber in den bereits
   vorhandenen `len(closes)==0`-Pfad (Fixed-HALTEN mit klarem
   `gate_reason`) statt abzustürzen.
2. `agent/multi_asset_batch.py::_kandidaten()` schließt Aktien- UND
   Themen-ETF-Assets ohne `yfinance_symbol` jetzt aus der automatischen
   Kandidatenauswahl aus (analog zu `signal_batch.py`s coingecko_id-Filter)
   - Rohstoffe/Hedge bleiben unberührt (siehe oben).
3. `ui/app.py::_refresh_watchlist_from_db()` markiert betroffene Aktien-/
   Themen-ETF-Assets jetzt ebenfalls sichtbar ("⚠ kein yfinance-Symbol").
   Das bisherige Tag `coingecko_id_fehlt` wurde dafür in `externe_id_fehlt`
   umbenannt (deckt jetzt beide Fälle ab, gleiche rote Hervorhebung).

**Verifiziert:** synthetischer Regressionstest des Absturz-Fixes (Guard
verhindert die `AttributeError`, `_load_ohlc()` bleibt korrekt leer).
Synthetischer Test von `_kandidaten()` mit 6 Fällen (Aktie mit/ohne ID,
Themen-ETF mit/ohne ID, Rohstoff ohne ID bleibt Kandidat, Hedge-Instrument
ohne ID bleibt Kandidat). Tk-Smoke-Test der erweiterten Watchlist-Tab-
Warnung (Aktie/ETF ohne ID markiert, Hedge-Instrument korrekt unmarkiert).

## Nachtrag (2026-07-19, gleicher Tag): Backtracking-Aussagekraft-Audit - Überholt-Erkennung neutralisierte die eigene Ergebnisstatistik

**Auslöser:** Nutzer bat vor der Governance-Diskussion (Selbstverifikations-
Vision Schritt 3, siehe Kap. 7) darum, sicherzustellen, dass Backward-
Tracking "sauber funktioniert und auch kurzfristig eine gewisse
Aussagekraft hat" - erst wenn das gewährleistet ist, soll die Governance-
Frage angegangen werden.

**Echter, gravierender Fund:** Live gegen den frischesten Notebook-
Datenexport geprüft (`notebook_diagnose.json`, 2026-07-19), da die lokale
Desktop-DB seit dem NB-Umzug veraltet ist. Ergebnis: von 9 trackbaren Spot-
Signalen (KAUFEN/NACHKAUFEN) wurden **alle 9 (100%)** als "überholt"
markiert, bevor der Kurs jemals gegen Take-Profit/Stop-Loss geprüft werden
konnte (nach durchschnittlich ~29 Std., Spanne 18-56 Std.) - **kein
einziges** reales Ergebnis liegt vor. Bei Hebel wurden 21 von 35 ERÖFFNEN-
Signalen (60%) nach durchschnittlich **11,7 Std.** (Spanne 4,2-22,7 Std.)
überholt; nur 2 von 35 kamen je zu einem echten Ergebnis (beide Stop-Loss,
beide aus der inzwischen entfernten Cerebras-Ära - die aktuelle Kette
Groq/Mistral/Gemini hat bislang null ausgewertete Ergebnisse).

**Root Cause:** `_is_superseded()` (Kap. „Info-Leichen"-Nachtrag oben,
2026-07-16 eingeführt gegen doppelte/widersprüchliche Anzeigen) markierte
ein offenes KAUFEN/ERÖFFNEN als überholt, sobald **irgendein** neueres
reales Signal für dasselbe Symbol vorlag - unabhängig von dessen Aktion.
Da HALTEN die weit überwiegende Aktion ist (>95%) und gehaltene/offene
Positionen sehr häufig neu bewertet werden (`hebel_position_cooldown_
stunden`: 3 Std., `spot_cooldown_stunden_kern`: 8 Std.), wurde praktisch
jede offene Kauf-These durch eine bloße HALTEN-Bestätigung "überholt" -
lange bevor ein realistischer mehrtägiger Kursverlauf Take-Profit/Stop-Loss
überhaupt erreichen konnte. Die Funktion, die Doppel-Anzeigen verhindern
sollte, hielt dadurch strukturell die Ergebnisstatistik leer, die
Governance Schritt 3 als Grundlage braucht.

**Fix 1 - Überholt-Erkennung eingeschränkt:** `_is_superseded()` (Spot UND
Hebel) überholt eine offene These jetzt nur noch bei einer echten neuen
Aktion (erneutes KAUFEN/NACHKAUFEN/ERÖFFNEN = redundant, oder VERKAUFEN/
TAUSCHEN/SCHLIESSEN/HEBEL_SENKEN = widersprechend) - eine reine HALTEN-
Bestätigung widerspricht der offenen These nicht und überholt sie nicht
mehr. Die ursprüngliche Absicht (Duplikate/Widersprüche ausblenden) bleibt
dadurch unverändert erhalten.

**Fix 2 - inhaltsbasierte Ablaufzeit statt fixer 90-Tage-Frist:** Nutzer-
Vorgabe: "der zeitliche Faktor sollte durch den Inhalt bzw. Angabe - wann
soll ein Zielwert erreicht werden - besser abschätzbar sein". Statt eine
neue Datenstruktur zu erfinden, wird das bereits bestehende, vom Modell
zuverlässig gefüllte `halte_kriterium` genutzt (Regel 17 in
`analyst.py`/`hebel_analyst.py`, bereits vollständig als eigene
Spalten in `signals`/`hebel_signals` persistiert): `ziel_datum` hat
Vorrang, wenn gesetzt (in der Praxis fast nie - live geprüft: 0 von 9
Fällen), sonst der grobe `bucket` (kurz/mittel/lang, in der Praxis
**zuverlässig** gefüllt - live geprüft: 9 von 9 Fällen). Neue Config-Werte
`backward_tracking.abgelaufen_nach_tagen_bucket` (kurz: 14, mittel: 45,
lang: 120 Tage) + `abgelaufen_nach_tagen_fallback` (90 Tage, für ältere
Signale ohne halte_kriterium) ersetzen den alten einzelnen
`abgelaufen_nach_tagen`-Wert. Die konkreten Tageswerte sind selbst
`[OFFEN]`/vorläufig (siehe Kap. 15), erste plausible Startwerte analog dem
bisherigen 90-Tage-Vorschlag.

**Fix (drei Dateien, identisches Muster fuer Spot und Hebel):**
1. `agent/krypto/backward_tracking.py`: `_is_superseded()` + `_is_expired()`
   wie beschrieben geändert, `DEFAULT_ABGELAUFEN_TAGE_BUCKET`/
   `DEFAULT_ABGELAUFEN_TAGE_FALLBACK` ersetzen `DEFAULT_ABGELAUFEN_NACH_
   TAGEN`.
2. `agent/krypto/hebel_backward_tracking.py`: identischer Fix (mirror-
   Muster), importiert die neuen Konstanten von oben.
3. `Basisinfos/config.yaml`: `backward_tracking`-Sektion umgestellt.

**Verifiziert:** 14 synthetische Tests (HALTEN überholt nicht mehr/andere
Aktionen weiterhin doch, für Spot UND Hebel; bucket-Mapping kurz/mittel/
lang; ziel_datum-Override in beide Richtungen; Fallback bei fehlendem
bucket; ungültiges ziel_datum fällt korrekt auf bucket zurück). Echter Lauf
gegen eine Kopie der Produktions-DB: von 51 vorher unverarbeiteten Spot-
Signalen bleiben danach korrekt nur die 2 tatsächlich noch unentschiedenen
trackbaren Signale offen (vorher wären sie durch die alte Regel fälschlich
überholt worden, da fuer beide zwischenzeitlich nur HALTEN-Bestätigungen
vorlagen), alle anderen korrekt `nicht_anwendbar`.

## Nachtrag (2026-07-19, gleicher Tag): 29× "Auto-Add unbekannter
Hebel-Symbole fehlgeschlagen" im Notebook-Export - Bug war bereits gefixt,
keine neue Ursache

**Auftrag:** vollen Traceback zu 29 Vorkommen von "Auto-Add unbekannter
Hebel-Symbole fehlgeschlagen" im `notebook_diagnose.json`-Export finden,
Root Cause klären, fixen.

**Ergebnis: kein neuer Fix nötig - der Export zeigt einen bereits
abgeschlossenen Vorfall.** Vollständiger Traceback aus `log_auszug`
extrahiert (72h-Fenster, `job_fehlschlaege` listet nur die Kurzmeldung ohne
Traceback): 28 der 29 Vorkommen sind exakt der `AttributeError: 'str'
object has no attribute 'get'`-Bug aus `get_listed_assets(bitpanda_api_key)`
statt `get_listed_assets()` - **derselbe Bug, der bereits am selben Tag
(2026-07-16, Commit `fe970ef`) live anhand eines FRÜHEREN
Notebook-Diagnose-Exports gefunden und gefixt wurde** (siehe
Commit-Nachricht: "Live in den Notebook-Logs gefunden
(Notebook_Analysedaten-Export)"). Alle 28 Vorkommen liegen zeitlich
zwischen 2026-07-16 13:10:02 und 2026-07-17 02:52:35 - der Fix wurde um
15:33 Uhr desselben Tages committet, das Notebook lief bis zum nächsten
USB-Sync aber noch mit dem alten Code weiter (siehe
[[reference_usb_sync_workflow]]). Aktueller Code
(`scheduler/background.py`, `importer/bitpanda_margin_positions.py`,
`api/bitpanda.py`) wurde geprüft und ruft an allen vier Stellen bereits
korrekt `get_listed_assets()` ohne Positionsargument auf - keine Änderung
nötig, per Signatur-Check bestätigt.

Das **29. Vorkommen** (2026-07-17 02:52:35, letztes in der Reihe) ist ein
eigenständiger `requests.exceptions.ReadTimeout` gegen
`api.bitpanda.com` (15s-Timeout in `_fetch_all_bitpanda_assets()`,
paginierter Abruf des gesamten Asset-Katalogs) - eine normale transiente
Netzwerkstörung, kein Code-Fehler, kein Wiederholungsmuster (kein weiteres
Vorkommen im restlichen 72h-Fenster bis 2026-07-19 06:03). Konsistent mit
dem bestehenden Muster anderer transienter API-Fehler in diesem Projekt
(z. B. FRED-Timeouts), die ebenfalls ohne Sonderbehandlung beim nächsten
15-Min-Tick automatisch erneut versucht werden - `hebel_screening_job`
fängt den Fehler ohnehin lokal ab (eigener `try/except` um den Auto-Add-
Aufruf), sodass weder der restliche Job-Lauf noch die U-8-Job-Ausfall-
E-Mail-Benachrichtigung betroffen sind.

**Wichtige Korrektur der Auftragsbeschreibung:** der im Auftrag genannte
"letzter Treffer 2026-07-19 06:03:30" bezieht sich nicht auf diese
Fehlermeldung - der tatsächlich letzte "Auto-Add..."-Eintrag im Export
liegt auf 2026-07-17 02:52:35. Der spätere Zeitstempel gehört zu einer
andersartigen, unabhängigen Meldung ("FRED-Abruf für bok_diskontsatz
fehlgeschlagen"). Lektion: bei mehrdeutigen/verwechselbaren Log-Zeitstempel-
Angaben im Auftrag den vollen `job_fehlschlaege`/`log_auszug`-Datensatz
selbst nachprüfen statt die genannten Eckwerte ungeprüft zu übernehmen.

**Verifiziert:** vollständige Traceback-Extraktion aller 29 Vorkommen aus
`log_auszug` (Python-Skript, Gruppierung per Zeitstempel-Regex), Diff der
Exception-Endzeilen (2 eindeutige Cluster: `AttributeError` × 28,
`ReadTimeout` × 1). Aktueller Code an allen 4 `get_listed_assets()`-
Aufrufstellen per `grep` + Signatur-Introspektion (`inspect.signature()`)
gegengeprüft - keine Regression.

## Nachtrag (2026-07-19, gleicher Tag): zwei neue Datenquellen - FRED-CPI-Kalender + SEC-EDGAR-Insider-Trading

**Auslöser:** direkter Nachfolger der Backtracking-Aussagekraft-Audit-Runde:
Nutzer wollte generell, "nicht nur Krypto", zusätzliche Marktdaten-Quellen
zur Aufwertung der LLM-Abfragen recherchiert haben - mit dem expliziten
Hinweis, dass X (Twitter) und YouTube bereits als problematisch bekannt sind
(API-Kosten bzw. ToS-Risiko) und deshalb nicht erneut vertieft werden
müssen. Ein spezialisierter Recherche-Agent lieferte eine priorisierte
Top-5-Liste kostenloser, offizieller Quellen; Nutzer entschied sich, mit
FRED-Release-Kalender + SEC-EDGAR-Insider-Trading zu beginnen.

### FRED-CPI-Veröffentlichungskalender (analog zum bestehenden FOMC-Kalender)

Live gegen die echte FRED-API verifiziert (`/fred/series/release`,
`/fred/release/dates`): CPI hat `release_id=10`. Bewusst NUR CPI
aufgenommen, nicht alle bereits genutzten `FRED_SERIES` - H.15 (Fed Funds,
`release_id=18`) wird taeglich veröffentlicht und wäre als "bevorstehendes
Ereignis" nie aussagekräftig (immer "morgen"), M2/ISM-Ersatz haben keinen so
ausgeprägten Markt-Reaktions-Charakter wie der monatliche CPI-Print. Live
auch bestätigt: FRED veröffentlicht den JEWEILS NÄCHSTEN Termin nicht immer
im Voraus (kurz nach einem CPI-Print am 2026-07-14 lieferte die API noch
keinen Eintrag für den nächsten Termin) - kein Fehler, `get_next_fred_release()`
liefert dann korrekt `None` statt zu raten (P-10).

**Umgesetzt:** `api/macro.py::get_next_fred_release()`/`get_upcoming_fred_releases()`
(neu, `FRED_RELEASE_IDS`-Konstante). `agent/krypto/pipeline.py::
fetch_market_context()` bekommt einen neuen optionalen `fred_api_key`-
Parameter und füllt `naechste_cpi_veroeffentlichung` analog zu
`upcoming_fomc` (gleiches Footprint wie der bestehende FOMC-Kalender:
Spot/Hebel/Marktscan - NICHT Aktien/Rohstoffe/Hedge/Themen-ETF, die nutzen
`fetch_market_context()` bisher nicht). Drei Aufrufstellen entsprechend
angepasst (`agent/krypto/pipeline.py::generate_signal()`,
`agent/krypto/hebel_pipeline.py::generate_hebel_signal()`,
`agent/krypto/marktscan.py::generate_candidate_writeup()` inkl. dessen
beiden Callern `budget_allocator.py`/`ui/marktscan_view.py`). Neue Regel 13-
Erweiterung in `agent/krypto/analyst.py` (analog zur bestehenden FOMC-Regel:
CPI-Print innerhalb von 5 Tagen wird als möglicher kurzfristiger
Volatilitäts-Faktor in `key_risks` erwähnt), reines Fakten-Feld in
`agent/krypto/hebel_analyst.py` (kein eigener Regeltext, wie beim FOMC-
Pendant dort auch).

**Verifiziert:** live gegen die echte FRED-API (Endpunkt-Verhalten,
inkl. des "noch kein Termin bekannt"-Falls). Synthetischer Test der
Facts-Zusammenbau-Logik (gesetzter Fakt/None/fehlender Key). Echter
End-to-End-Lauf von `fetch_market_context()` mit und ohne Key - kein Fehler.

### SEC-EDGAR-Insider-Trading (Form 4, nur Aktien-Pipeline)

Live gegen die echte SEC-EDGAR-API verifiziert (CIK-Auflösung für VST/PLTR,
echte Form-4-Rohdaten-XML-Struktur): `submissions/CIK##########.json`
liefert die Filing-Liste inkl. `primaryDocument`-Pfad wie
"xslF345X06/wk-form4_XXXX.xml" - das ist die XSLT-GERENDERTE HTML-Ansicht,
NICHT die Rohdaten. Die eigentliche Roh-XML mit den strukturierten
Transaktionsdaten liegt im selben Verzeichnis OHNE das "xslF345X06/"-
Präfix (für beide Testfälle bestätigt) - reiner String-Präfix-Strip, kein
zusätzlicher Index-Abruf nötig. Nur Transaktionscode P (offener Markt-Kauf)
und S (offener Markt-Verkauf) gelten als echtes Insider-Conviction-Signal -
A (Zuteilung/Grant), M (Optionsausübung), F (Steuerabzug) etc. sind
administrativ/vergütungsbedingt und werden bewusst herausgefiltert (P-10:
keine Fehlinterpretation als Kauf-/Verkaufssignal).

**Umgesetzt:** neue `api/sec_edgar.py` (kein API-Key nötig, nur ein
Pflicht-User-Agent-Header laut SEC-Vorgabe) -
`get_cik_for_ticker()` (in-memory gecacht, die ~800KB-Gesamtliste wird
nur einmal pro App-Lauf geladen), `get_recent_insider_transactions()`
(max. 5 Filings, 90-Tage-Fenster), `summarize_insider_activity()`
(Aggregation zu Kauf-/Verkaufszahlen + -Volumen, reine Lesefunktion, keine
Bewertung). `agent/aktien/analyst.py::build_facts()` bekommt neuen
`insider_trading`-Parameter, neue Regel 22 (niedrig gewichteter
Zusatzkontext, explizite Warnung vor Überinterpretation einzelner
Transaktionen - Insider-Verkäufe sind oft routinemäßig/steuerlich bedingt).
`agent/aktien/pipeline.py::generate_signal()` ruft den Abruf mit
`asset.yfinance_symbol` (nicht `asset.symbol` - SEC braucht den echten
Börsen-Ticker) in einem eigenen try/except auf, degradiert bei Fehlschlag
auf `None` (P-10). `remote/server.py::API_HEALTH_GROUPS` um `sec_edgar`
ergänzt.

**Verifiziert:** live gegen die echte SEC-EDGAR-API fuer VST und PLTR
(reale Insider-Transaktionen korrekt geparst, inkl. Edge-Case unbekannter
Ticker -> leere Liste statt Fehler). JSON-Serialisierbarkeit geprüft.
**Echter End-to-End-Signal-Lauf fuer VST gegen eine Kopie der (migrierten)
Produktions-DB, inklusive echter LLM-Antwort (Mistral):** das Modell hat
den neuen Fakt tatsächlich in seiner Begründung verwendet ("Die
Insideraktivitäten sind negativ") - nicht nur strukturell verdrahtet,
sondern nachweislich wirksam. Ein erster Versuch mit Groq schlug wegen
bereits ausgeschöpftem Tageskontingent fehl (429), kein Code-Fehler.

**Bewusst nicht umgesetzt (Nutzer-Vorgabe: "Fang mit FRED-Kalender + SEC
EDGAR an"):** die weiteren drei Top-5-Empfehlungen (EIA-Energiedaten,
Finnhub Recommendation-Trends/Earnings-Kalender, FINRA Equity Short
Interest) bleiben als nächste Kandidaten vorgemerkt, sobald gewünscht.

## Nachtrag (2026-07-19, gleicher Tag): EIA-Erdgas-Lagerbestand + Finnhub-Analysten-Trend

**Auslöser:** direkter Nachfolger obigen Nachtrags - Nutzer bat "Fang mit EIA
und Finnhub an".

**Wichtiger Unterschied zu FRED/SEC-EDGAR (Ehrlichkeits-Hinweis, P-10):**
beide neuen Quellen brauchen einen kostenlosen, aber PERSÖNLICHEN API-Key
(E-Mail-Registrierung), den ich nicht selbst anlegen kann/darf (Accounts
erstellen ist eine Nutzer-Aktion). Anders als bei FRED/SEC-EDGAR konnte die
tatsächliche DATEN-Struktur der Antworten deshalb noch NICHT live gegen
eine echte Antwort verifiziert werden - nur die Endpunkt-ROUTEN selbst
wurden live bestätigt (EIA: 403 `API_KEY_MISSING` statt 404, Finnhub: 401
"Please use an API key" statt 404, d.h. beide URLs/Parameter-Strukturen
existieren tatsächlich). Die konkreten Feld-/Series-Namen basieren auf der
offiziellen Dokumentation der beiden Anbieter, sind aber bis zur ersten
echten Antwort als "wahrscheinlich korrekt, noch nicht bestätigt"
einzustufen - explizit als TODO im jeweiligen Modul-Docstring vermerkt.
Key-Setup wie gewohnt: `.env.example` + leere Platzhalterzeile in der
echten `.env` vorbereitet (`EIA_API_KEY`/`FINNHUB_API_KEY`), Nutzer trägt
den Wert selbst ein (siehe Memory `feedback_key_setup_workflow`).

### EIA-Erdgas-Lagerbestand (nur Rohstoff-Pipeline, nur OD7L)

Schließt die im Rohstoff-Disclaimer bereits dokumentierte Lücke ("EIA-
Erdgas-Speicher NOCH NICHT einbezogen", siehe Nachtrag "Rohstoff-Pipeline
Phase 2"). Neue `api/eia.py::get_natural_gas_storage_history()` (Weekly
Natural Gas Storage Report, Lower 48, Series-ID `NW2_EPG0_SWO_R48_BCF` -
siehe Vorbehalt oben) liefert die letzten 8 Wochenwerte inkl. Woche-zu-
Woche-Änderung (Build/Draw). Bewusst KEIN 5-Jahres-Saisonvergleich in
dieser Runde (würde eine laengere historische Datenbasis + eigene
Berechnungslogik brauchen) - stattdessen wird dem Modell der 8-Wochen-
Verlauf mitgegeben und in der neuen Regel 21 (`agent/rohstoff/analyst.py`)
explizit angewiesen, den Verlaufstrend statt eines Einzelwerts zu nutzen
und die fehlende Saisonalitäts-Einordnung als Einschränkung zu
berücksichtigen. `agent/rohstoff/pipeline.py::_fetch_lagerbestaende()` nur
für `asset.symbol == "OD7L"` aktiv (kein Erdgas-Äquivalent für Gold/
Silber/Kupfer), Disclaimer-Text in `build_facts()` entsprechend
aktualisiert.

### Finnhub-Analysten-Trend (nur Aktien-Pipeline)

Bewusst NUR `recommendation-trends` umgesetzt, NICHT der ebenfalls
empfohlene Earnings-Kalender - wäre redundant mit dem bereits vorhandenen
`fundamentaldaten.naechstes_earnings_datum` (aus yfinance); zwei
potenziell abweichende Terminquellen im selben Prompt wären mehr
Verwirrung als Mehrwert (P-10). Neue `api/finnhub.py::
get_recommendation_trends()`/`summarize_recommendation_trend()` liefert
die Analysten-Empfehlungsverteilung (strong_buy/buy/hold/sell/strong_sell)
des aktuellsten UND des Vormonats - ergänzt den bereits vorhandenen
`fundamentaldaten.analysten_konsens` (reiner Momentanwert aus yfinance) um
eine RICHTUNGSKOMPONENTE ("wird der Konsens optimistischer oder
pessimistischer?"). Neue Regel 23 in `agent/aktien/analyst.py` (niedrig
gewichtet, analog zu den bestehenden Analysten-Fakten).

**Umgesetzt:** `api/eia.py`, `api/finnhub.py` (neu). `agent/rohstoff/
pipeline.py`/`agent/rohstoff/analyst.py` (Lagerbestände, Regel 21).
`agent/aktien/pipeline.py`/`agent/aktien/analyst.py` (Analysten-Trend,
Regel 23). `.env.example` + `.env`: zwei neue Platzhalter mit
Registrierungs-Anleitung. `remote/server.py::API_HEALTH_GROUPS` um `eia`/
`finnhub` ergänzt.

**Verifiziert:** 14 synthetische Tests (EIA-Wochenwerte-Parsing inkl.
Delta-Berechnung, Rohstoff-Symbol-Filter, Finnhub-Trend-Sortierung +
Zusammenfassung inkl. Ein-Monats-Edge-Case, JSON-Serialisierbarkeit).
Modul-Imports fehlerfrei. Endpunkt-Routen live gegen die echten Server
bestätigt (siehe Vorbehalt oben).

## Nachtrag (2026-07-19, gleicher Tag, Folge): EIA + Finnhub live mit echten Nutzer-Keys verifiziert

Nutzer hat beide kostenlosen Keys angelegt und in `.env` eingetragen. Damit
konnte die zuvor offene Lücke geschlossen werden - nicht mehr nur die
Endpunkt-Route, sondern die tatsächliche Datenform der Antworten.

**EIA:** `get_natural_gas_storage_history()` liefert 8 echte Wochenwerte
(2026-05-22 bis 2026-07-10), Lower-48-Bestand steigt saisonal korrekt von
2.483 auf 3.024 Bcf (Build in jeder Woche, konsistent mit der
US-Sommer-Füllsaison). Series-ID, Feldnamen und Delta-Berechnung bestätigt
korrekt - kein Ratefehler in der ursprünglichen Implementierung.
`agent/rohstoff/pipeline.py::_fetch_lagerbestaende("OD7L", ...)` direkt
gegen die echte API getestet, liefert das erwartete Fakten-Dict inkl.
8-Wochen-Verlauf; für andere Rohstoff-Symbole weiterhin korrekt `None`.

**Finnhub:** `get_recommendation_trends()` liefert für VST und PLTR je 4
Monatswerte mit den erwarteten Feldern (period/strongBuy/buy/hold/sell/
strongSell). Konsens plausibel unterschiedlich zwischen beiden Aktien (VST
fast ausschließlich Buy/Strong-Buy, PLTR mit spürbarem Hold-Anteil) -
Datenform bestätigt korrekt, `summarize_recommendation_trend()` bildet die
Monat-zu-Monat-Richtungskomponente wie vorgesehen.

**Rechtliche Einordnung (auf Nutzerfrage hin geprüft):** EIA-Daten sind
U.S.-Government-Public-Domain (eia.gov/about/copyrights_reuse.php) - jede
Nutzung erlaubt, keine Einschränkung, Attribution nur optional empfohlen.
Finnhubs Free-Tier ist vertraglich klar auf "Non-Professional/persönliche,
nicht-kommerzielle Nutzung" beschränkt (finnhub.io/terms-of-service) und
verbietet Weitergabe der Daten/Ergebnisse an Dritte - beides passt exakt
zum tatsächlichen Nutzungsmuster von TradingInfoTool (privates
Single-User-Tool, Daten fließen nur in lokale LLM-Prompts, keine
Weiterverteilung). Bei der Finnhub-Registrierung ist die Kontoart aktiv als
"Non-Professional/Personal" zu wählen - keine reine Formsache, sondern
deckt sich inhaltlich mit der echten Nutzung.

Modul-Docstrings in `api/eia.py`/`api/finnhub.py` von "wahrscheinlich
korrekt, noch nicht bestätigt" auf "live verifiziert" aktualisiert. Damit
sind alle vier vom Nutzer gewählten neuen Datenquellen (FRED, SEC-EDGAR,
EIA, Finnhub) vollständig umgesetzt UND live verifiziert - nur FINRA Equity
Short Interest bleibt als letzter, noch nicht angegangener Kandidat aus der
ursprünglichen Auswahl offen.

## Nachtrag (2026-07-19, gleicher Tag, Folge 2): FINRA Equity Short Interest (Aktien-Pipeline)

**Auslöser:** Nutzer bat "jetzt FINRA Short Interest angehen" - der letzte
der vier ursprünglich gewählten Datenquellen-Kandidaten.

**Wichtiger Fund:** anders als EIA/Finnhub braucht FINRAs Consolidated-
Short-Interest-Endpunkt (`api.finra.org/data/group/otcMarket/name/
ConsolidatedShortInterest`) KEINEN API-Key - live bestätigt oeffentlich
zugänglich (dieselbe Backend-API, die FINRAs eigene Daten-Browse-
Oberfläche nutzt). Für VST/PLTR (beide NYSE) echte, plausible Historie
zurückbekommen (VST: 205 Datenpunkte seit 2017, PLTR: 138 seit 2019).
Ein Sortierversuch über den Partition-Key `settlementDate` scheitert ohne
zusätzlichen Datums-Filter (API-Einschränkung) - stattdessen wird die
komplette Historie mit einem großzügigen `limit` geholt und clientseitig
sortiert/zugeschnitten. Bei unbekanntem Symbol liefert die API HTTP 204
mit leerem Body (kein valides JSON) statt einer leeren Liste - live mit
einem Fantasiesymbol bestätigt, expliziter Check in
`get_short_interest_history()`.

**Umgesetzt:** neue `api/finra.py` - `get_short_interest_history(symbol,
n_periods=6)` (letzte 6 zweiwöchentliche Meldeperioden, aufsteigend),
`summarize_short_interest()` (aktuelle vs. vorherige Periode, analog zum
Finnhub-Muster). Nur Aktien-Pipeline (`agent/aktien/pipeline.py`,
`asset.yfinance_symbol` wie bei SEC-EDGAR/Finnhub), neue Regel 24 in
`agent/aktien/analyst.py`: niedrig gewichteter Zusatzkontext, explizit
AMBIVALENT markiert (steigende Short-Position + hohes `days_to_cover`
kann sowohl anhaltenden Abwärtsdruck als auch ein Short-Squeeze-Setup
bedeuten, je nach technischem Kontext) - Erwähnung nur bei auffälligem
`days_to_cover` (>3-4 Tage) oder starker Periodenänderung (>15-20%).
Meldelag (1-3 Wochen, zweiwöchentliche FINRA-Meldung) explizit als "kein
Echtzeit-Signal" vermerkt. `remote/server.py::API_HEALTH_GROUPS` um
`finra` ergänzt. Kein `.env`-Eintrag nötig (kein Key).

**Verifiziert:** synthetische Tests für `summarize_short_interest()`
(leer/1-Eintrag/2-Eintraege), Pipeline-Block-Simulation mit echtem
API-Aufruf für VST (JSON-serialisierbar), Live-Test für VST/PLTR (echte
Werte, z. B. VST 2026-06-30: 15.917.274 Short-Aktien, 3,45 Tage
Eindeckungsdauer, +3,61% ggü. Vorperiode) sowie für ein Fantasiesymbol
(leere Liste, kein Crash trotz HTTP-204-Sonderfall). `build_facts()`-
Signatur-Check bestätigt korrekte Parameter-Durchreichung. Damit sind
JETZT ALLE FÜNF ursprünglich recherchierten Datenquellen-Kandidaten
(FRED, SEC-EDGAR, EIA, Finnhub, FINRA) vollständig umgesetzt und live
verifiziert - keine offenen Kandidaten aus dieser Recherche-Runde mehr.

## Nachtrag (2026-07-19, gleicher Tag, Folge 3): Aktien/ETF-Screener + Bitpanda-Sonderthema

**Auslöser:** Nutzer fragte nach dem Stand von "Marktscan-analogen" Mechanismen
für Aktien/Rohstoffe/ETF. Antwort: es gab bisher KEINE automatische Neu-
Kandidaten-Entdeckung für diese drei Klassen (nur die 11 manuell in
`config.yaml` gepflegten Symbole werden per `agent/multi_asset_batch.py`
regelmäßig neu bewertet, siehe Cooldown-Werte 24h/72h dort) - die
Bewertung bestehender Positionen lief also schon automatisch, nur die
Kandidaten-Suche fehlte. Nutzer bat: "bau einen einfachen Aktien/ETF-
Screener über eine kostenlose Quelle und berücksichtige auch hier das
Sonderthema - was ist bei Bitpanda davon gelistet und was nicht."

**Wichtiger Fund VOR der Implementierung (direkt relevant für die Bitpanda-
Frage):** ein Live-Check aller 9 aktuell gehaltenen Rohstoff-/Themen-ETF-
Positionen (OD7N/OD7H/OD7C/OD7L/VVMX/X136/EXH3/CEBS/ISOC) gegen
`api.bitpanda.is_listed()` ergab: KEINE davon ist bei Bitpanda gelistet -
nur die beiden Aktien (VST/PLTR) sind es. Bitpanda führt zwar eigene ETF/
ETC-"Themenkörbe" (z.B. "COPPERMINE", "NATGAS", 209 Einträge insgesamt),
das sind aber ANDERE, Bitpanda-eigene Produkte - keine echten UCITS-ETFs/
WisdomTree-ETCs wie in der Watchlist. Der Nutzer hält diese 9 Positionen
also nachweislich über einen anderen Broker (die Bestände selbst sind
über den bestehenden Excel-Import erfasst, nicht über Live-Bitpanda-Sync).
Diese Erkenntnis hat die Architektur direkt geprägt (siehe unten).

**Datenquelle (kostenlos, kein neuer API-Key):** `yfinance` (bereits im
Projekt für OHLC/Fundamentaldaten genutzt) Version 1.5.1 hat ein
eingebautes `yf.screen()`-Feature (Yahoo-Finance-Screener-Backend, live
verifiziert: `most_actives`/`day_gainers`/`growth_technology_stocks`/
`undervalued_growth_stocks`/`small_cap_gainers` liefern je 30-325 Treffer
mit >90 Feldern pro Symbol).

**Bewusst ASYMMETRISCHE Architektur** (`agent/aktien/screener.py`, neu),
direkt begründet durch den Bitpanda-Fund oben:
- **Aktien:** `scan_aktien_candidates()` durchsucht 3 Yahoo-Finance-Screens
  (Momentum + Growth + Value gemischt), filtert Mikro-Caps (<500 Mio. $
  Marktkap.) und Illiquides (<500k Tagesvolumen) heraus, dedupliziert,
  schließt bereits gelistete Watchlist-Symbole aus und markiert pro
  Kandidat `bitpanda_gelistet` via `is_listed()`.
- **ETF/ETC:** `scan_etf_candidates()` enumeriert NICHT über yfinance,
  sondern DIREKT Bitpandas eigenen ETF/ETC-Katalog (`get_listed_non_crypto_
  assets()`, Gruppen `etf`+`etc`) - das IST das bei Bitpanda tatsächlich
  kaufbare Angebot, während eine echte UCITS-ETF-Discovery über yfinance
  an Bitpandas Sortiment vorbeigegangen wäre (siehe Fund oben). Kein
  `yfinance_symbol` ableitbar (Bitpandas Symbole wie "COPPERMINE" sind
  eigene Produktnamen, keine Börsenticker) - degradiert sauber auf "keine
  technische Historie" (bereits bestehender Fix, Ticket #319).

**Bewusst EINFACH gehalten** (Nutzer-Wunsch): kein vierstufiges Scoring wie
beim Krypto-Marktscan (`agent/krypto/marktscan.py`), keine DB-Persistenz,
kein automatischer LLM-Call - ein manueller "Jetzt scannen"-Klick liefert
eine frische Kandidatenliste, "In Watchlist übernehmen" nutzt exakt
dasselbe bereits etablierte Muster wie Marktscan (`config.py::
add_watchlist_entry()`, Backup + Validierung + Rollback). Die eigentliche
Bewertung übernommener Kandidaten läuft danach ganz regulär über den
bereits bestehenden `multi_asset_batch_job` - kein Doppelbau.

**Umgesetzt:** `agent/aktien/screener.py` (neu, `ScreenerCandidate`-
Dataclass, `scan_aktien_candidates()`, `scan_etf_candidates()`), `ui/
screener_view.py` (neu, Treeview + Scan-Button + Übernehmen-Button, Muster
identisch zu `ui/marktscan_view.py`, aber ohne Score-Spalte/Detail-Panel).
`ui/app.py`: neuer Tab "Screener" zwischen Marktscan und Hebel.

**Verifiziert:** synthetische Tests (`_bereits_in_watchlist()` Groß-/
Kleinschreibung), echter Live-Lauf gegen beide Quellen (144 Aktien-
Kandidaten aus 3 Screens, 209 ETF/ETC-Kandidaten aus Bitpandas Katalog,
u.a. NVDA/TSM/AVGO mit korrektem Bitpanda-Listing-Flag), Tk-Smoke-Test
der `ScreenerView` isoliert UND als Teil der vollständigen `App`
(gegen eine Kopie der Produktions-DB, alle 7 Tabs inkl. "Screener"
korrekt registriert). `config.add_watchlist_entry()` selbst wurde NICHT
erneut gegen die echte `config.yaml` getestet (bereits durch die
bestehende Marktscan-Nutzung etabliert/verifiziert, Signatur-Kompatibilität
per Code-Review bestätigt) - kein ungewolltes Schreiben in die reale Datei
während der Verifikation.

## Nachtrag (2026-07-19, gleicher Tag, Folge 4): Schwerpunkt-Feld + Diversifikations-Übersicht

**Auslöser:** Nutzer bat um eine "konkrete Einordnung der Assets - z.B.
Inhalt und Zweck damit wir dies z.B. bei der Diversifikation - Gold,
Silber, Kupfer, seltene Erden, Güter, Energie korrekt einordnen können"
und wollte diese Schwerpunkte selbst in der Oberfläche pflegen können.

**Umgesetzt:** neues, optionales Freitext-Feld `schwerpunkt` auf
`WatchlistAsset` (`config.py`) - bewusst freier Text statt fester
Enum-Liste, da die sinnvollen Kategorien vom konkreten Portfolio abhängen
und nicht im Code vorgegeben werden sollen. Neue Funktion
`update_watchlist_schwerpunkt()` (gleiches Backup+Validierung+Rollback-
Muster wie `update_watchlist_coingecko_id()`), ABER mit einer bewussten
Abweichung: Einfügeposition ist das ENDE des Eintrags-Blocks statt einer
festen Position - `schwerpunkt` ist das zuletzt hinzugekommene optionale
Feld und soll bestehende Einträge mit bereits vorhandenen optionalen
Feldern (coingecko_id/assetklasse/yfinance_symbol/ist_cash_aequivalent)
nicht durcheinanderbringen. `add_watchlist_entry()` um den Parameter
erweitert (Neuanlage).

**GUI:** `AssetAddDialog`/`AssetEditDialog` (`ui/app.py`) um ein
"Schwerpunkt"-Textfeld erweitert (analog zum bestehenden coingecko_id-
Muster im Edit-Dialog). Watchlist-Tab-Treeview um eine neue Spalte
"Schwerpunkt" ergänzt.

**Diversifikations-Übersicht (`ui/portfolio.py`):** neue kompakte Tabelle
unterhalb der Bestandsliste, gruppiert den aktuellen Portfoliowert (inkl.
gestakter Anteile) nach `schwerpunkt` und zeigt EUR-Wert + Anteil-%.
Assets ohne gesetzten Schwerpunkt fallen in einen Sammel-Eintrag "ohne
Schwerpunkt", Fiat-Cash in "Cash/Sonstiges" - die Prozentwerte summieren
sich dadurch sauber auf denselben `Gesamtwert:` wie in der bestehenden
Anzeige. Bewusst als Tabelle statt Pie-Chart (kein bestehendes
Chart-Vorbild für Verteilungsdarstellungen, `ui/charts.py` deckt nur
Kursverlaufs-Liniencharts eines einzelnen Assets ab).

**Direkt befüllt** für alle 13 bestehenden Nicht-Krypto-Watchlist-
Einträge (Aktien/Rohstoffe/Themen-ETF) über die neue Funktion gegen die
echte `config.yaml`: VST → Energieversorger, PLTR → Software/KI-
Datenanalyse, OD7N → Silber, OD7H → Gold, OD7C → Kupfer, OD7L → Erdgas/
Energie, VVMX → Seltene Erden & strategische Metalle, X136 → Bioenergie,
EXH3 → Nahrungsmittel & Getränke, CEBS → Kupferminen (Aktien), ISOC →
Agrarwirtschaft, DBPK/3QSS → Absicherung (S&P 500/Nasdaq 100 Short).
Krypto-Einträge bewusst NICHT befüllt (außerhalb des ursprünglichen
Anfrage-Kontexts, kann der Nutzer bei Bedarf selbst über die GUI
nachtragen).

**Verifiziert:** synthetische Tests für `update_watchlist_schwerpunkt()`
(neue Zeile einfügen/bestehende Zeile ändern/unveränderter Wert -> kein
Schreibvorgang/unbekanntes Symbol) - dabei ZUERST versehentlich gegen die
echte `config.yaml` statt einer Kopie gelaufen (Testskript-Fehler, keine
Datenverlust, siehe git diff danach leer), sofort per Backup-Restore
korrigiert, danach sauber gegen eine echte Kopie wiederholt. Tk-Smoke-Test
`PortfolioView` gegen eine Kopie der Produktions-DB (Diversifikations-
Tabelle vor UND nach dem Befüllen der 13 Schwerpunkte geprüft - 13
korrekte Kategorien + "ohne Schwerpunkt"/"Cash/Sonstiges"-Sammeltöpfe),
voller `TradingInfoToolApp`-Smoke-Test (Watchlist-Tab zeigt die neue
Spalte korrekt), `AssetEditDialog`/`AssetAddDialog`-Instanziierungstest.
`git diff Basisinfos/config.yaml` vor dem Commit geprüft - ausschließlich
13 neue `schwerpunkt:`-Zeilen, keine sonstigen Änderungen.

## Nachtrag (2026-07-19, gleicher Tag, Folge 5): Kategorie-Taxonomie ERSETZT das Freitext-Schwerpunkt-Feld (Release 1)

**Auslöser - Nutzer-Korrektur:** der Freitext-`schwerpunkt` aus Folge 4 war
ein Missverständnis. Nutzer-Originalzitat: *"du hast mich falsch verstanden
- nicht ich will etwas manuell befüllen sondern schritt für schritt -
unabhängig von Krypto - 1. brauche eine Grundmenge an existierenden
Hauptgruppen - z.B. ETF Gruppen - dann unterkategorien z.B. Energie, KI,
Software etc, aus denen kann ich dann für den Marktscan und die
Diversifikation Schwerpunkte selbst gestalten u.U. gestützt durch
Vorschläge der KI [...] Das kann über einen Bereich komfortabel über die
GUI und automatischen Prozessen gesteuert werden."* Kernpunkt: Freitext
kann von automatischen Prozessen (Marktscan-Bias, KI-Vorschläge,
Gruppierung) strukturell nicht zuverlässig ausgewertet werden - es braucht
einen kontrollierten Vokabular-Baum. Auf Nachfrage (AskUserQuestion)
präzisierte der Nutzer zwei weitere Anforderungen: (a) wo verfügbar,
Detailinformationen zur Asset-Zusammensetzung zeigen (z.B. "wie setzt sich
ein ETF zusammen"), (b) bei mehreren ähnlichen Bitpanda-Produkten die
"Besseren" filtern helfen - explizite Motivation: *"damit die Investition
besser funktioniert und wir nicht wieder Produkte im Portfolio haben welche
gleich wieder delisted werden oder sind."* Auf die Frage nach der
Taxonomie-Quelle entschied der Nutzer: *"Erst Bitpanda-Katalog systematisch
auswerten"* statt einer vom Assistenten vorgeschlagenen Liste.

**Umfang dieser Runde (Release 1):** die Taxonomie-Infrastruktur komplett
(Kategorien-Datei, Datenmodell, GUI-Migration, Bestandsmigration,
Kompositions-/Qualitätsmodul, Screener-Integration, Diversifikations-
Umbau). Die aktive Schwerpunkt-Steuerung selbst (Prioritäten setzen, KI-
Vorschläge, Marktscan-Bias) ist bewusst als "Release 2" zurückgestellt -
noch nicht umgesetzt, siehe Ausblick am Ende dieses Nachtrags.

### Zwei echte Bitpanda-API-Bugs gefunden und behoben (betrifft die GESAMTE App, nicht nur dieses Feature)

Bei der Herleitung der Taxonomie aus dem echten `/v3/assets`-Katalog
(`api/bitpanda.py::_fetch_all_bitpanda_assets()`) fiel auf, dass
wiederholte Aufrufe im selben Moment gegen denselben Datensatz
unterschiedliche Ergebnisanzahlen lieferten (209/187/228/213 ETF/ETC/
Metal-Einträge beobachtet) - das betraf JEDEN bisherigen Aufrufer der
Funktion (Bitpanda-Listing-Prüfung in allen Signal-Pipelines, Screener,
Watchlist-Konsistenzprüfung), nicht nur die neue Taxonomie-Arbeit.

- **Bugfix 1 (Duplikate über Seitengrenzen):** derselbe Symbol-Eintrag
  tauchte teils auf mehreren Paginierungsseiten gleichzeitig auf (bis zu 53
  Duplikate bei `total_count=3238` gemessen). Erster Fix: Deduplizierung
  per Symbol beim Sammeln - reichte allein NICHT aus (siehe Bugfix 2/3).
- **Bugfix 2 (verworfen, aber dokumentiert):** die Vermutung, das
  ursprüngliche Abbruchkriterium `page_number * page_size >= total_count`
  sei die Ursache (da `total_count` selbst instabil ist), führte zu einem
  Ersatz-Abbruchkriterium `len(page_data) < page_size`. Live-Test zeigte:
  das machte es NICHT robuster, sondern schlimmer (163/173/211 Einträge
  über 6 Wiederholungen, teils fehlte real ZINC/SXR8/WTI komplett) - auch
  NICHT-letzte Seiten kamen serverseitig manchmal unvollständig zurück.
- **Bugfix 3 (tatsächliche Lösung):** das Problem war die MEHRSEITIGE
  Paginierung selbst - der Datensatz verschiebt sich offenbar leicht
  zwischen einzelnen Roundtrips (Ursache serverseitig unbekannt). Live
  bestätigt: ein EINZELNER Request mit `page_size=10000` (deutlich über dem
  aktuellen `total_count=3238`) liefert den kompletten Datensatz in einer
  Antwort - 6/6 Wiederholungen exakt stabil (3238 Einträge, 3185 eindeutige
  Symbole, alle 211 realen ETF/ETC/Metal-Symbole). Die Dedup-Notwendigkeit
  aus Bugfix 1 bleibt (der Datensatz selbst enthält echte Symbol-Kollisionen,
  ca. 53 Stück, keine Paginierungs-Artefakte) - die `while`-Schleife bleibt
  nur noch als Sicherheitsnetz für ein zukünftiges Wachstum über 10.000
  Einträge hinaus im Code, wird im Normalfall aber nie ein zweites Mal
  durchlaufen. **Lektion:** bei unzuverlässigen Paginierungs-APIs mit
  überschaubarer Gesamtgröße ist "alles in einer Anfrage mit großzügigem
  `page_size`" robuster als Mehrseiten-Konsistenz-Reparaturen.

### `Basisinfos/kategorien.yaml` (neu)

10 Hauptgruppen, 72 Unterkategorien, systematisch aus dem (nach obigen
Bugfixes) stabilen Bitpanda-ETF/ETC/Edelmetall-Katalog hergeleitet:
Edelmetalle (Gold/Silber/Platin&Palladium/Diversifiziert), Industriemetalle,
Energie, Agrarrohstoffe & Nahrungsmittel, Technologie & KI, Absicherung,
Aktien - Regionen & Länder, Aktien - Sektoren, Anleihen & Geldmarkt,
Sonstige. Jede Unterkategorie trägt eine `bitpanda_symbole`-Liste zur
automatischen Vor-Klassifikation neuer Kandidaten. Vollständigkeits-Check
bestätigt: alle 211 realen Symbole sind genau einer Unterkategorie
zugeordnet, keine Waisen, keine erfundenen Symbole (per Live-Test gegen den
echten, jetzt stabilen Katalog reproduzierbar). Eigene Watchlist-Assets
(auch nicht bei Bitpanda gelistete) speichern ihre Hauptgruppe/
Unterkategorie direkt am Asset, unabhängig von dieser Datei - die Datei ist
nur die Vorschlagsquelle für neue Kandidaten.

### `config.py`: strukturelle Migration

`WatchlistAsset.schwerpunkt` (Freitext, Folge 4) ersetzt durch
`hauptgruppe`/`unterkategorie` (beide `str | None`, IDs aus
`kategorien.yaml`). Neue Lookup-Funktionen: `get_kategorien()` (gecached),
`find_kategorie_fuer_bitpanda_symbol()`, `get_hauptgruppe_name()`,
`get_kategorie_name()`. `update_watchlist_kategorie(symbol, hauptgruppe,
unterkategorie)` ersetzt `update_watchlist_schwerpunkt()` - schreibt beide
Felder ATOMAR (beide oder keins), validiert beide IDs gegen
`kategorien.yaml` VOR jedem Schreibvorgang (Fail-Fast, nie ein ungültiger
Halbzustand in `config.yaml`). Alle 13 bestehenden Nicht-Krypto-Assets
wurden auf die neue Struktur migriert, die alten `schwerpunkt:`-Zeilen
entfernt (`git diff` bestätigt: nur die erwarteten Zeilenänderungen).

### GUI-Migration (`ui/app.py`)

Freitext-Feld in `AssetAddDialog`/`AssetEditDialog` ersetzt durch
kaskadierende Hauptgruppe→Unterkategorie-Comboboxen
(`_build_kategorie_selector()`). Watchlist-Tab-Spalte zeigt jetzt
`config.get_kategorie_name(...)`. Diversifikations-Tabelle
(`ui/portfolio.py`) gruppiert entsprechend nach Hauptgruppe um (Fix eines
dabei live gefundenen `AttributeError` durch die Feldumbenennung).

### Asset-Qualitäts-/Kompositionsmodul (`api/asset_quality.py`, neu) - "wie setzt sich zusammen"

`get_asset_quality(yfinance_symbol)` liefert über `yfinance`s
`Ticker.info`/`Ticker.funds_data` Top-10-Holdings, Sektorgewichtung, AUM
(`totalAssets`) und Kostenquote (`netExpenseRatio`) für Assets mit echtem
Börsenticker - live verifiziert (VVMX.DE/EXH3.DE/VST/PLTR). Neuer
Watchlist-Toolbar-Button "Zusammensetzung anzeigen…" öffnet
`AssetQualityDialog`. **Bewusste, dokumentierte Grenze (P-10):** Bitpandas
EIGENE synthetische ETF/ETC-Themenkörbe (z.B. "COPPERMINE") haben KEINEN
echten Börsenticker und damit strukturell KEINE öffentliche AUM/
Kostenquote - für diese Kandidaten bleibt `get_asset_quality()` `None`, ein
"besseres Produkt"-Vergleich ist dort nicht möglich. Die AUM-basierte
Delisting-Risiko-Einschätzung (kleine Fonds werden häufiger geschlossen)
funktioniert NUR für echte Fonds mit Ticker.

### Screener-Integration (`agent/aktien/screener.py`, `ui/screener_view.py`)

`ScreenerCandidate` um `hauptgruppe`/`unterkategorie` erweitert.
`scan_etf_candidates()` taggt jeden Bitpanda-Katalog-Kandidaten automatisch
per `config.find_kategorie_fuer_bitpanda_symbol()` (204 von 204 aktuellen
Kandidaten live erfolgreich zugeordnet - alle 211 Katalog-Symbole sind ja
per Definition in der Taxonomie erfasst). Neue "Kategorie"-Spalte im
Screener-Tab. Bei "In Watchlist übernehmen" wird die erkannte Kategorie
gleich mit übernommen, damit der Nutzer sie nicht nochmal manuell setzen
muss. **Kein Qualitätsvergleich für diese Kandidaten** (siehe Grenze oben,
dokumentiert im Modul-Docstring mit Querverweis auf `asset_quality.py`) -
`scan_aktien_candidates()` (Einzelaktien) bewusst NICHT um Kategorie-Tagging
erweitert, da die Taxonomie nur ETF/ETC/Edelmetall-Gruppen abbildet, keine
Einzeltitel.

### Verifikation

Synthetisch: `kategorien.yaml`-Vollständigkeit (211=211, 0 Waisen, 0
erfunden) über 10 Wiederholungen NACH Bugfix 3 stabil (VORHER, mit den
verworfenen Fixes, war das nicht der Fall - siehe Bugfix-Historie oben).
Echt: `_fetch_all_bitpanda_assets()`/`get_listed_assets()`/
`get_listed_non_crypto_assets()` je 5-10x wiederholt gegen die echte API,
alle stabil (822 Krypto/2363 Nicht-Krypto/3185 eindeutige Symbole gesamt).
`get_asset_quality()` live gegen mehrere echte Ticker + einen erfundenen
Ticker (korrektes `None`). Voller `TradingInfoToolApp`-Smoke-Test:
`PortfolioView.refresh()`, `ScreenerView`-Aufbau, `AssetAddDialog`/
`AssetEditDialog`-Instanziierung mit echten Produktionsdaten - keine
Exceptions. `git status`/`git diff` vor dem Commit geprüft.

### Ausblick: Release 2 (noch NICHT umgesetzt, separate Runde)

Schwerpunkte/Thesen-Verwaltung (GUI zum Setzen von Prioritäten/
Zielgewichtungen pro Kategorie mit Begründung+Datum), ein periodischer
KI-Vorschläge-Job (Muster wie `makro_analog.py`, schlägt Kategorie-
Schwerpunkte basierend auf bestehenden Makro-Fakten vor, Nutzer
akzeptiert/verwirft), sowie Marktscan-/Screener-Bias (Kandidaten aus
priorisierten Kategorien höher gewichten) - alle drei bewusst
zurückgestellt, bis die Taxonomie-Infrastruktur (dieser Nachtrag) im
laufenden Betrieb bestätigt ist.

## Nachtrag (2026-07-19, gleicher Tag, Folge 6): Release 2 (Schwerpunkte/Thesen-Verwaltung) - Konzeptionsrunde

**Status dieses Nachtrags:** reine Konzeption/Entscheidungsfindung, kein
Code zum Zeitpunkt dieses Eintrags. Vollständige Ausarbeitung liegt in
`Basisinfos/Kategorie_Basisinformationen_Release2.md`/`.docx` - dieser
Eintrag hält nur die wichtigsten Entscheidungen und Funde fest, damit sie
auch ohne die separate Datei nachvollziehbar bleiben. **Umsetzung folgte
noch am selben Tag, siehe Nachtrag Folge 7 weiter unten** - die
Konzeptionsrunde und die Implementierungsrunde fielen beide auf den
2026-07-19/2026-07-20-Übergang.

**Datenmodell einer "These":** `hauptgruppe`/`unterkategorie` (beide Ebenen
erlaubt, GUI zeigt bei Hauptgruppen-These transparent die darunter
konsolidierten Unterkategorien), `richtung` (Übergewichten/Neutral/Meiden),
`staerke`, `begruendung` (Freitext), `pruef_mechanismus` (strukturiert,
siehe unten), `gesetzt_am`, `review_am`, `status`, `quelle`
(manuell/KI-Vorschlag). Neue DB-Tabelle, nicht `config.yaml`.

**#334 (Marktscan-/Screener-Bias) zweistufig entschieden - wichtigster
Punkt dieser Runde:**
- Stufe 1 (Teil der ersten Umsetzungsrunde): NUR Hervorhebung/Sortierung,
  KEINE Scoring-Gewichtung. Grund: eine aktive These spiegelt die
  subjektive, aktuelle Einschätzung des Nutzers - würde sie das Scoring
  gewichten, entstünde bei trendgetriebenen Themen (Beispiel Technologie &
  KI) eine prozyklische Verstärkung ("KI ist im Trend" → System zeigt mehr
  KI-Aktien → verstärkt die Wahrnehmung, obwohl das Thema evtl. bereits
  überhitzt ist) - direkter Widerspruch zur bestehenden antizyklischen
  Risikogate-Philosophie im Projekt (Retail-Konsens-Deckel, siehe Nachtrag
  vom 2026-07-19 weiter oben).
- Zusatz, Teil der ersten Runde: neuer Fakt `these_abgleich` je Signal -
  prüft die These NICHT gegen ihre eigene Beliebtheit, sondern gegen
  unabhängige, bereits im Projekt vorhandene objektive Daten (M2-/
  Liquiditätsregime für Edelmetalle, CFTC-COT-Positionierung für
  Industriemetalle/Energie, Zinskurve für Finanzsektor-Aktien,
  Dollar-Index für Emerging Markets). Kann eine hypebasierte These sogar
  als "objektiv nicht gestützt" kennzeichnen - das eingebaute Gegenmittel
  zum Bubble-/Trend-Chasing-Risiko.
- Stufe 2 (später, vorsichtig): echte Scoring-Gewichtung nur für
  strukturelle/langsame Kategorien (Edelmetalle, Industriemetalle, Energie,
  Anleihen), nie für Technologie & KI.

**Acht Kandidaten-Thesen mit Mechanik durchgearbeitet** (Energie,
Edelmetalle, Industriemetalle/Kupfer, Erneuerbare & Clean Energy, Anleihen/
TIPS, Aktien-Sektoren/Finanzen, Aktien-Regionen/Emerging Markets,
Absicherung) - für jede die zugrundeliegende ökonomische Mechanik ("wann
funktioniert das grundsätzlich") plus echter Live-Datenabgleich (yfinance,
CFTC COT, FRED M2/Fed Funds, EIA), nicht nur Trainingswissen. Bewusst als
Mechanik-Erklärung + aktuelle Datenlage kommuniziert, NICHT als
Kaufempfehlung (siehe Modul-Docstring-Stil im restlichen Projekt).

**Echter Fund dabei (Dollar-Index-Trend):** für die Emerging-Markets-These
zeigte eine Momentaufnahme des Dollar-Index (100,69) zunächst nichts
Eindeutiges - erst der 12-Monats-Verlauf (yfinance, monatliche Kerzen)
zeigte einen klaren Aufwärtstrend seit Jahresbeginn 2026 (96,99 im Januar
auf Höchststand 101,19 im Juni) - das ist ein Gegenwind für eine
EM-Übergewichtungs-These, kein Rückenwind, obwohl die Fed erkennbar lockert.
Lektion: ein einzelner aktueller Wert reicht bei makroökonomischen
Indikatoren oft nicht, der Trend über mehrere Monate ist aussagekräftiger.

**Lücken-Prüfung (auf Nutzer-Wunsch, sieben Funde, Details in der
Basisinformationen-Datei):**
1. CFTC-COT deckt kein Rohöl ab (`COT_MARKET_NAMES` in `api/cftc_cot.py`
   hat nur Gold/Silber/Kupfer/Erdgas) - Energie-These fehlt damit die
   Positionierungs-Perspektive für WTI/Brent.
2. Dollar-Index und Zinskurve (10J vs. kurzfristig) sind NICHT als eigene,
   `@track_api_health`-überwachte Datenquellen im Projekt vorhanden - für
   heutige Zwecke ad-hoc direkt über yfinance abgefragt, für einen
   verlässlichen `these_abgleich`-Fakt müssten das richtige, abgesicherte
   Funktionen werden.
3. Absicherung/Hedge passt nicht sauber ins Standard-Datenmodell (Feld
   `richtung` ergibt bei einer Versicherungs-Logik wenig Sinn) - eigene
   GUI-Darstellung (Aktiv/Inaktiv) vermutlich nötig.
4. Krypto ist komplett außen vor (`kategorien.yaml` deckt bewusst keine
   Kryptowerte ab) - der `these_abgleich`-Fakt erscheint deshalb nie bei
   Krypto-Signalen, muss in GUI/Doku klar kommuniziert werden.
5. Kein automatisches Verhalten bei Ablauf von `review_am` definiert.
6. Keine Verbindung zur Diversifikations-Tabelle (Portfolio-Tab) vorgesehen.
7. Synergie mit dem Screener (`scan_etf_candidates()` taggt Kandidaten
   schon heute mit Hauptgruppe/Unterkategorie, Release 1) noch nicht
   genutzt - Kandidaten aus Kategorien mit aktiver, aber in der Watchlist
   noch nicht vertretener These könnten hervorgehoben werden.

**Weitere Entscheidungen:** Granularität beide Ebenen erlaubt; 3-6
gleichzeitig aktive Thesen als weiche Richtgröße, kein Hard-Limit;
KI-Vorschläge-Job (#333) täglich wie `makro_analog_job` (06:30 Uhr),
Rhythmus-Optimierung vorgemerkt für später.

**Nachtrag zum Nachtrag, gleicher Tag - drei weitere Punkte auf
Nutzer-Wunsch ergänzt:**
- **Haltedauer/Zeithorizont:** die Prüf-Mechanismen haben unterschiedliche
  natürliche Zeithorizonte (COT wöchentlich → kürzer, M2/Zinskurve/
  Dollar-Index-Trend brauchen Monate → länger) - der `review_am`-Vorschlag
  in der GUI orientiert sich daran (z. B. 4 Wochen bei COT-gestützten
  Thesen, 3 Monate bei M2-gestützten). Ein zusätzlicher Mismatch-Check
  zwischen dem Zeithorizont der These und der Haltedauer-Empfehlung des
  konkreten Signals (`holding_duration`/`halte_kriterium_bucket`) war hier
  angedacht, ist aber bei der Umsetzung (Folge 7) bewusst NICHT eingebaut
  worden: dieses Feld entsteht erst als LLM-OUTPUT, ein Vorab-Abgleich vor
  dem LLM-Aufruf ist strukturell nicht möglich - das wäre ein Post-Check
  nach der Antwort (analog `risk_gate.py::post_check()`), siehe
  `agent/kategorie_thesen.py::build_these_abgleich_fact()`-Docstring für den
  dokumentierten, offenen Nachrüstpunkt.
- **Gehaltene Assets erhalten Priorität:** innerhalb einer Kategorie mit
  aktiver These werden in der Stufe-1-Hervorhebung zuerst bereits gehaltene
  Assets (`wird_aktuell_gehalten`) angezeigt, dann neue Watchlist-/
  Screener-Kandidaten, dann alles Übrige - unterschiedliche Dringlichkeit
  (echte Entscheidung vs. "einen Blick wert").
- **Transparenz-Prinzip, ausdrücklicher Nutzer-Wunsch, gilt durchgängig:**
  jede automatische Wirkung einer These (Sortierung, Hervorhebung,
  Review-Datum-Vorschlag, `these_abgleich`-Text) muss ihre konkrete
  Begründung sichtbar mitliefern, minimaler Interpretationsaufwand für den
  Nutzer - keine stille Umsortierung, kein Badge ohne Klartext-Erklärung.

**Nächster Schritt:** die sieben Lücken-Punkte (plus die drei
Ergänzungen oben) sind kleinere Ausbau-Entscheidungen, kein Blocker für den
Start der Umsetzung von #332 - Implementierung kann beginnen, offene
Punkte während der Umsetzung nach und nach klären.

## Nachtrag (2026-07-20, Folge 7): Release 2 (Schwerpunkte/Thesen-Verwaltung) - Umsetzung #332/#343

Direkte Fortsetzung von Folge 6 (Nutzer-Anweisung "starten wir hier") - die
komplette Backend- + GUI-Infrastruktur für #332 sowie die Stufe-1-
Hervorhebung aus #343 wurden implementiert und verifiziert. #333
(KI-Vorschläge-Job) und die eigentliche Stufe 2 von #334 (Scoring-Gewichtung
für strukturelle Kategorien) sind bewusst NICHT Teil dieser Runde, siehe
Folge 6.

**Backend:**
- `database/models.py::These`-Dataclass + `database/db.py`: `thesen`-Tabelle
  (2 Indizes) + volles CRUD (`create_these`/`update_these`/
  `set_these_status`/`get_these`/`get_aktive_thesen`/`get_alle_thesen`/
  `get_aktive_these_fuer_kategorie()` - Unterkategorie-spezifische These hat
  Vorrang vor einer Hauptgruppen-weiten, identische Priorität überall wo
  Thesen nachgeschlagen werden).
- `config.py::PRUEF_MECHANISMUS_MAPPING`/`get_pruef_mechanismus()` - welcher
  objektive Check (m2_liquiditaet/cot_positionierung/zinskurve/dollar_index/
  baerenmarkt_overlay) für welche Hauptgruppe/Unterkategorie gilt, inkl.
  `review_tage_vorschlag` + `review_begruendung` fürs Transparenz-Prinzip.
- Lücke 1 (CFTC-COT ohne Rohöl) geschlossen: `api/cftc_cot.py::
  COT_MARKET_NAMES` um `rohoel_wti`/`rohoel_brent` erweitert (echte
  Marktnamen live über die CFTC-API mit `LIKE`-Filtern ermittelt, nicht
  geraten).
- Lücke 2 (Dollar-Index/Zinskurve ohne überwachte Datenquelle) geschlossen:
  `api/macro.py::get_zinskurve()`/`get_dollar_index_trend()`, beide
  `@track_api_health("yfinance")` (kein neuer API_HEALTH_GROUPS-Eintrag
  nötig, teilen sich den bestehenden yfinance-Block).
  `get_dollar_index_trend()` liefert IMMER den 12-Monats-Verlauf, nie nur
  eine Momentaufnahme (siehe der echte DXY-Fund in Folge 6).
- `agent/kategorie_thesen.py` (neu): `these_abgleich`-Berechnungsmodul.
  `compute_these_abgleich()` + 4 `_abgleich_*()`-Funktionen (M2/COT/
  Zinskurve/Dollar-Index) plus `_abgleich_baerenmarkt_overlay()`, die ehrlich
  `"nicht_pruefbar"` zurückgibt (P-10, Absicherung-Check bleibt bewusst
  Lücke 3/unimplementiert, siehe Folge 6). `build_these_abgleich_fact()` als
  gemeinsamer, in allen 4 Nicht-Krypto-Pipelines (Aktien/Rohstoffe/Hedge/
  Themen-ETF) wiederverwendeter Fact-Baustein (Muster wie
  `agent.krypto.wiederholungs_erkennung.build_wiederholung_fact()`) - je ein
  neuer SYSTEM_PROMPT-Regel-Eintrag in den 4 Analysten, der die KI anweist,
  den Abgleich zu kommentieren, aber NIE die Action über das hinaus zu
  schieben, was die übrigen Fakten hergeben (Stufe-1-Prinzip: Hervorhebung,
  kein Scoring-Einfluss).
- `index_aktive_thesen()`/`lookup_these()` (selbes Modul) - In-Memory-Index
  für wiederholte Lookups über viele Assets/Kandidaten (Watchlist-Tab,
  Screener), vermeidet einen SQL-Query pro Zeile, identische
  Prioritäts-Logik wie `get_aktive_these_fuer_kategorie()`.

**GUI Task #342 - neuer Tab "Schwerpunkte":** `ui/thesen_view.py` (neu).
Liste aller Thesen (Kategorie/Richtung/Stärke/Prüf-Mechanismus/Status/
Termine) + Add/Edit-Dialog. Eigener, lokaler Kategorie-Selector (nicht der
aus `ui.app` wiederverwendet - eine These kann sich auf eine GANZE
Hauptgruppe beziehen, zeigt dabei live alle darunter konsolidierten
Unterkategorien, Nutzer-Entscheidung #1 aus Folge 6). Absicherung-Sonderfall
sauber gelöst: Richtung-Feld zeigt bei `hauptgruppe=absicherung` automatisch
Aktiv/Inaktiv statt Übergewichten/Neutral/Meiden (schließt Lücke 3 aus
Folge 6 GUI-seitig). Transparenz-Prinzip live umgesetzt: der
`review_am`-Vorschlag erscheint direkt neben dem Feld mit konkretem Datum
UND Begründungstext (z. B. "Vorschlag: 2026-08-17 (heute + 28 Tage) -
CFTC-COT-Berichte erscheinen wöchentlich..."), nie eine stille Vorbelegung.
Statuswechsel (aktiv → erledigt/verworfen) über eigene Listen-Buttons, nicht
im Dialog (eine neue These startet immer aktiv/manuell).

**GUI Task #343 - Stufe-1-Hervorhebung, schließt Lücken 6+7 aus Folge 6:**
alle drei Stellen nutzen dieselben Marker (▲ Übergewichten/Aktiv, ▼ Meiden,
● Neutral/Inaktiv) mit denselben drei Farb-Tags (`these_positiv`/
`these_negativ`/`these_neutral`) und demselben Prinzip: sichtbarer Marker +
Zeilen-Tooltip mit der konkreten These-Begründung, NIE eine stille
Umsortierung (Transparenz-Prinzip).
- **Watchlist-Tab** (`ui/app.py`): Sortier-Priorität nur bei der initialen
  Einsortierung (Gruppe 0 = gehalten + aktive These, 1 = nicht gehalten +
  aktive These, 2 = Rest, jeweils alphabetisch), greift NICHT in eine
  manuelle Spaltensortierung ein (Nutzer-Entscheidung "gehaltene Assets
  sollten Priorität erhalten" aus Folge 6). Marker an die
  Schwerpunkt-Spalte angehängt, Zeilen-Tooltip erweitert (zeigt aktive
  These VOR dem letzten Signal, falls beides vorhanden).
- **Diversifikations-Tabelle** (`ui/portfolio.py`): Marker je
  Hauptgruppen-Zeile, wenn irgendeine aktive These (Hauptgruppen-weit ODER
  eine ihrer Unterkategorien) zutrifft - bei mehreren Treffern bestimmt die
  "stärkste" Richtung den Marker (Übergewichten/Aktiv vor Meiden vor
  Neutral), der Tooltip listet trotzdem ALLE Treffer einzeln auf. Bewusst
  KEIN Eingriff in die bestehende Wert-Sortierung (größte Position bleibt
  oben - das ist die eigentlich nützliche Ordnung für diese Tabelle), nur
  der Marker.
- **Screener-Tab** (`ui/screener_view.py`): Sortier-Priorität (Treffer vor
  Nicht-Treffer, sonst Scan-Reihenfolge unverändert) - ohne
  gehalten-Priorität, Screener-Kandidaten sind per Definition noch nicht in
  der Watchlist. Neu: `add_row_tooltips()` für diesen Tab (gab es vorher
  nicht).

**Verifikation:** drei synthetische Tk-Smoke-Test-Skripte gegen Kopien der
Produktions-DB (nie die echte DB) - `ThesenView` (Liste/Filter/Add-Dialog
inkl. Absicherung-Sonderfall/Edit-Dialog-Vorbelegung/Statuswechsel, alle
Assertions bestanden), Watchlist-Sortier-/Marker-Logik (isoliert
nachgebaut, exakt dieselbe `index_aktive_thesen()`/`lookup_these()`-Funktion
wie im echten Code), Portfolio-Diversifikation + Screener (beide mit echten
Tk-Widgets, `PortfolioView`/`ScreenerView` direkt instanziiert, Marker/Tags/
Tooltips/Sortierreihenfolge geprüft). Zusätzlich ein kombinierter
Import-Regressionstest über alle geänderten/neuen Module (`ui.app`,
`ui.portfolio`, `ui.screener_view`, `ui.thesen_view`, `agent.
kategorie_thesen`, alle 4 Nicht-Krypto-Pipelines, `main`) - keine Fehler.

**Verbleibend offen (bewusst nicht Teil dieser Runde):**
- #333: täglicher KI-Vorschläge-Job für neue Thesen-Kandidaten.
- #334, Stufe 2: echte Scoring-Gewichtung für strukturelle Kategorien
  (Edelmetalle, Industriemetalle, Energie, Anleihen) - erst nach einer
  Beobachtungsphase mit Stufe 1.
- Lücke 5 aus Folge 6: kein automatisches Verhalten, wenn `review_am` in der
  Vergangenheit liegt (weder Benachrichtigung noch visuelle Markierung) -
  bisher rein manuell im Schwerpunkte-Tab einsehbar.
- Der in Folge 6 angedachte Haltedauer-Mismatch-Check (These-Zeithorizont
  gegen die Haltedauer-Empfehlung eines konkreten Signals) bleibt aus dem
  oben genannten strukturellen Grund unimplementiert (`agent/
  kategorie_thesen.py::build_these_abgleich_fact()`-Docstring).
- Absicherung/Hedge-`these_abgleich` bleibt `"nicht_pruefbar"` (Lücke 3 aus
  Folge 6, Bärenmarkt-Overlay-Indikator ist noch keine eigenständig
  aufrufbare Funktion).

## Nachtrag (2026-07-20, Folge 8): Screener-Auto-Scan + Mouseover-Tooltips fuer Tabs/Aktionen

Nutzer-Feedback nach dem ersten Test der Folge-7-Neuerungen: der Screener-Tab
war leer, weil er ausschliesslich manuell scannt, und die neuen Elemente
(Schwerpunkte-Tab, Screener-Auto-Scan) hatten keine erklaerenden Tooltips.
Zwei kleine, in sich abgeschlossene Nachbesserungen.

**Screener-Auto-Scan** (Nutzer-Wunsch "Auto-Screen beim Start bzw.
regelmaessige Updates", Nutzer-Bestaetigung "60 Minuten passt"): bewusst ein
GUI-lokaler, selbstverlaengernder `self.after()`-Timer in
`ui/screener_view.py` (Muster wie `ui/app.py::_poll_prices()`), KEIN neuer
Scheduler-Job - der Screener persistiert bewusst nichts in die DB (siehe
Folge-Ur-Docstring "keine DB-Persistenz"), ein Scheduler-Job haette dafuer
eine neue Tabelle gebraucht, nur damit die GUI sie wieder ausliest. Erster
Scan kurz nach dem Tab-Aufbau, danach alle `Basisinfos/config.yaml::
screener.auto_scan_intervall_minuten` (Default 60) Minuten erneut - der
Folge-Timer wird IMMER ab dem letzten tatsaechlichen Scan neu geplant
(egal ob manuell oder automatisch ausgeloest), mit Schutz gegen doppelte
Timer-Ketten (`after_cancel()` vor jedem Neuplanen) und gegen
ueberlappende Scans (Guard: ein Aufruf waehrend `scan_button` disabled
ist, wird ignoriert). 60 Minuten bewusst zurueckhaltend gewaehlt: Yahoo-
Finance-`day_gainers` ist zwar echt intraday-dynamisch, aber Bitpandas
ETF/ETC-Katalog aendert sich kaum, und das Notebook hatte bereits einen
echten yfinance-Haenger (siehe Memory
`project_multi_asset_yfinance_symbols`).

**Mouseover-Tooltips fuer Tabs/Aktionen** (Nutzer-Wunsch: "fuer die
Primaerseiten - Tabs und Aktionen - eine konkrete Kurzbeschreibung bei
Mouseover was diese bewirken/nutzung und optional [...] was sie nicht
koennen"): neues Modul `ui/widget_tooltip.py` - Ergaenzung zu den
bestehenden `ui/heading_tooltip.py` (Treeview-Spaltenkoepfe) und
`ui/row_tooltip.py` (Treeview-Zeilen), die beide NICHT auf normale Widgets
oder Notebook-Tab-Kopfzeilen anwendbar sind. Zwei neue Funktionen:
`add_widget_tooltip(widget, text)` (statischer Tooltip fuer z.B. einen
Button) und `add_notebook_tab_tooltips(notebook, {index: text})` (ueber
`notebook.identify()`/`notebook.index("@x,y")`). Bewusst eingegrenzter
Scope fuer diese Runde: NUR die beiden Tabs, deren Verhalten sich neu
geaendert hat (Schwerpunkte: neuer Tab; Screener: neuer Auto-Scan) -
Tab-Kopf-Tooltip fuer beide (`ui/app.py`) + Aktions-Tooltip fuer jeden
Button/jede Checkbox im Schwerpunkte-Toolbar (`ui/thesen_view.py`) und im
Screener-Toolbar (`ui/screener_view.py`), jeweils inkl. explizitem Hinweis
auf fehlenden Automatismus wo relevant (z.B. "Uebernimmt NICHTS
automatisch in die Watchlist"). Die uebrigen, bereits laenger bestehenden
Tabs (Watchlist/Portfolio/Signale/Marktscan/Hebel/Regime) sind bewusst NICHT
Teil dieser Runde - koennten im selben Muster nachgeruestet werden, falls
gewuenscht.

**Lesbarkeits-Check der neuen Marker-Farben (▲/▼/●, `these_positiv`/
`these_negativ`/`these_neutral`):** WCAG-Kontrastverhaeltnis berechnet
gegen Standard- UND Zebra-Streifen-Hintergrund, beide Modi. Echter,
bereits VORHANDENER Befund (nicht durch diese Runde neu verursacht - die
drei Marker-Tags nutzen die laengst etablierten `theme.success_color()`/
`danger_color()`/`info_color()`, dieselben Farben wie z.B. `pl_positive`/
`pl_negative` im Portfolio-Tab): im Light Mode liegen alle drei knapp an
oder leicht unter der WCAG-AA-Schwelle (4,5:1) auf dem Zebra-Streifen
(4,26-4,82:1); im Dark Mode ist der Kontrast auf normalem Hintergrund gut
(5,2-6,0:1), faellt aber auf dem dunklen Zebra-Streifen (`#404040`) auf
3,2-3,7:1 - unter der AA-Schwelle fuer normalen Text. Da dies ein
projektweites, bereits lange bestehendes Theme-Farbthema betrifft (nicht
nur die neuen Marker) und eine Korrektur alle Stellen mit `pl_positive`/
`pl_negative`/`bitpanda_fehlt`/etc. gleichermassen beeinflussen wuerde,
wurde dem Nutzer der Befund zunaechst nur gemeldet statt am Theme-System
vorbeizukorrigieren.

**Nachtrag zum Nachtrag, gleicher Tag - Nutzer bestaetigte den Fix nach
einem echten Screenshot** (Screener-Tab, Dark Mode: die "AGRICULTURE"/
"SOFTS"-Zeilen kaum lesbar grau auf dunkelgrauem Zebra-Streifen): bewusst
NICHT die Text-Farben selbst geaendert (haette die etablierte Bedeutung
von success/danger/warn/swap/info ueberall im Projekt angefasst), sondern
NUR `theme.py::_LIGHT["zebra_odd"]`/`_DARK["zebra_odd"]` selbst justiert -
ein einziger, zentraler Wert, den `restripe_treeview()` ohnehin bei jedem
Aufruf dynamisch nachschlaegt (`_palette()["zebra_odd"]`), also automatisch
ueberall wirksam ohne weitere Codeaenderung. Dark Mode: `#404040` ->
`#2d2d2d` (bewusst der bereits etablierte `entry_bg`-Ton wiederverwendet,
keine neue, ungetestete Farbe) - success/danger/info/muted/warn/swap jetzt
bei 4,0-6,5:1 (vorher 3,0-4,9:1), die meisten ueber der AA-Schwelle, der
Rest deutlich naeher dran. Light Mode: `#ebebeb` -> `#f2f2f2` (naeher an
`bg`) - success/danger/info jetzt bei 4,5-5,1:1 (vorher 4,3-4,8:1), alle
drei jetzt ueber der Schwelle.

**Verifikation:** synthetischer Tk-Test gegen eine DB-Kopie (kein echter
Produktivstart) mit gemockten `scan_aktien_candidates()`/
`scan_etf_candidates()`/`get_listed_non_crypto_assets()` (kein echter
Netzwerkzugriff im Test) - Auto-Scan-Ausloesung beim Tab-Aufbau, korrekt
geladenes Intervall aus `config.yaml`, Folge-Timer-Planung nach
Scan-Abschluss, Doppel-Scan-Guard, doppelter `_schedule_next_auto_scan()`-
Aufruf ohne Fehler, sowie die Tooltip-Bindung an allen neuen Widgets (2
Screener-Buttons, 4 Schwerpunkte-Buttons + 1 Checkbox, Notebook-Tab-Helper)
- alle 9 Testfaelle bestanden. Kombinierter Import-Regressionstest von
`ui.app` weiterhin fehlerfrei.

## Nachtrag (2026-07-20): `key_risks` bei Hebel-Signalen wurde bei
gleichem Regime/gleicher Aktion praktisch wortgleich wiederholt

**Auslöser:** Nutzer verglich zwei echte Hebel-ERÖFFNEN-E-Mails (ONDO,
KAIA) und bemerkte, dass die "Risiken:"-Liste vor dem Halte-Kriterium bei
beiden fast wortidentisch war ("Liquidationsrisiko bei schnellen
Kursbewegungen", "laufende Finanzierungsgebühr bei längerer Haltedauer",
"Gegen-Trend-Position ... Bärenregime").

**Root Cause:** anders als bei den Top-5-Gründen (Regel 8, verweist
explizit auf konkrete Indikatorwerte) gab Regel 9 dem Modell fuer
`key_risks` bisher fast woertlich die Zielformulierung als Beispiel vor
("Liquidationsrisiko bei schnellen Kursbewegungen, laufende
Finanzierungsgebühr bei längerer Haltedauer") - das Modell übernahm diese
Beispielsätze praktisch unveraendert statt sie nur als Kategorie-Vorgabe
zu behandeln. Der dritte, ebenfalls wiederkehrende Punkt stammt aus einer
strukturell identischen Formulierung in der Regime-Konflikt-Anweisung
(Regel 2, `regime.richtungs_konflikt_mit_trigger`).

**Fix (Nutzer-Entscheidung: Textbausteine behalten, aber um Zahlen
ergaenzen - minimal-invasiv statt Neuformulierung):** beide Prompt-Stellen
in `agent/krypto/hebel_analyst.py` fordern jetzt explizit, die
Beispielformulierungen mit den KONKRETEN Werten dieses Signals zu
ergaenzen - bei `key_risks` der eigene `hebel_vorschlag`-Wert (je hoeher,
desto groesser das Liquidationsrisiko bei gleicher Kursbewegung) sowie die
aktuelle `funding_rate_aktuell` aus den Fakten; beim Regime-Konflikt-Punkt
das konkrete `regime.regime` und die eigene Gegenszenario-Wahrscheinlichkeit
aus `forecast`. Eine reine Wortwiederholung ohne Zahlen ist damit explizit
als nicht ausreichend markiert.

**Bewusst NICHT angefasst:** die deterministische Risikofaktoren-Liste
("3. KONKLUSION", farbige Punkte) ist von diesem Fund nicht betroffen -
die wird NICHT vom LLM generiert (siehe `hebel_risk_gate.py::
compute_risikofaktoren_hebel()`-Docstring), sondern rein regelbasiert
berechnet.

**Verifikation:** reine Prompt-Textaenderung, keine Schema-/Code-Logik-
Aenderung - per Syntax-/Import-Check sowie manueller Sichtpruefung des
zusammengesetzten `SYSTEM_PROMPT`-Strings verifiziert. Kein echter
LLM-Testaufruf in dieser Runde (Wirkung zeigt sich erst am naechsten
echten Hebel-ERÖFFNEN-Signal auf dem Notebook).

## Nachtrag (2026-07-20): Risikofaktoren-Legende + drei kleine Bugfixes
aus der Notebook-Nachtanalyse

**Risikofaktoren-Legende:** Nutzer-Fund per Screenshot - das weisse
Neutral-Emoji (`_RISIKOFAKTOR_SYMBOL["neutral"]`) wird in manchen
E-Mail-Clients (Gmail-Web) blass-lila statt eindeutig grau gerendert, was
zu einer falschen Vermutung ueber die Farblogik fuehrte (tatsaechlich:
gruen = unterstuetzt die Empfehlung, rot = Warnsignal/Risiko). Neue
`RISIKOFAKTOREN_LEGENDE`-Konstante (`ui/formatting.py` fuer App-Kontext,
eigene Kopie in `scheduler/background.py` fuer E-Mail-Kontext, gleiches
Muster wie `_formatiere_risikofaktoren()`) direkt ueber der Liste in
Detail-Panel UND allen drei E-Mail-Vorlagen (Spot/Hebel/Multi-Asset).

**Drei kleine Bugfixes**, alle aus derselben Notebook-Diagnose-Auswertung:

1. `api/history.py::backfill_history()` - Guard fuer fehlende
   `coingecko_id` (verursachte taeglich einen sinnlosen
   `.../coins/None/market_chart`-404, im API-Health-Log sichtbar).
2. `api/yfinance_history.py::get_full_ohlc_history()` - bekannte "nur
   fast_info"-Ticker (`YFINANCE_HISTORY_UNRELIABLE_TICKERS`, z.B.
   X136.BE/IS0C.DE) wurden im taeglichen OHLC-Job bisher nicht
   beruecksichtigt (nur im 15-Min-Live-Preis-Pfad) - yfinance wirft dort
   hart "Period 'max' is invalid, must be one of: 1d, 5d" statt nur zu
   loggen. Jetzt zentraler Skip vor dem Call.
3. `api/onchain.py` - neue `MissingOnChainMetricError` statt rohem
   `TypeError: float() argument ... not 'NoneType'`, wenn CoinMetrics fuer
   den neuesten Tag eine einzelne Metrik noch nicht nachgetragen hat
   (bekannter Anbieter-Lag). Muster identisch zu
   `api/derivatives.py::NoOpenInterestDataError`.

Alle drei per synthetischem Test verifiziert (kein echter API-Call noetig,
da jeweils reines Verhalten bei fehlenden/fehlerhaften Rohdaten getestet).

## Nachtrag (2026-07-20): Risikofaktoren-Symbole von farbigen Emoji auf Form-Marker umgestellt

Fortsetzung des obigen Legende-Fixes - Nutzer schickte einen Screenshot des
LIVE laufenden Detail-Panels am Notebook (12:30 Uhr, Hebel-Tab): die
farbigen Kreis-Emoji (🟢/🔴) rendern in Tkinters Standardfont unter Windows
NICHT farblich unterscheidbar - beide fallen auf denselben Ersatzglyph
("⊘") zurueck, nur das weisse Neutral-Emoji (⚪) blieb als "○" sichtbar
unterscheidbar. Damit beschrieb die gerade erst hinzugefuegte
`RISIKOFAKTOREN_LEGENDE` eine Farbunterscheidung, die auf dem Bildschirm gar
nicht existierte - Ursache: `_set_detail_text()` (`ui/hebel_view.py`,
`ui/signals_view.py`) ist ein reiner `tk.Text.insert()`-Aufruf ohne jedes
`tag_configure(foreground=...)`, die Farbwirkung haengt komplett vom
(nicht vorhandenen) Emoji-Farb-Support des Fonts ab.

**Fix:** `_RISIKOFAKTOR_SYMBOL` in `ui/formatting.py` UND der parallelen
Kopie in `scheduler/background.py` von `{"positiv": "🟢", "neutral": "⚪",
"negativ": "🔴"}` auf `{"positiv": "▲", "neutral": "●", "negativ": "▼"}`
umgestellt - dieselben Form-Marker (unterschiedliche Glyphen, nicht nur
unterschiedliche Farbe), die bereits fuer die These-Marker im Schwerpunkte-
Tab etabliert sind (`ui/app.py`/`portfolio.py`/`screener_view.py`, gleiche
Semantik: ▲ positiv/unterstuetzend, ▼ negativ/Warnung, ● neutral). Form
statt Farbe macht die Unterscheidung robust sowohl gegen Tkinter-
Emoji-Rendering (App) als auch gegen E-Mail-Client-Eigenheiten (bereits der
Ausloeser des vorherigen Legende-Fixes). `RISIKOFAKTOREN_LEGENDE`-Text in
beiden Dateien entsprechend angepasst. Bewusst KEINE echten Tk-Farb-Tags
zusaetzlich eingefuehrt (haette eine Restrukturierung von `_set_detail_text()`
auf zeilenweises Einfuegen mit Tags erfordert) - die Form-Marker loesen das
gemeldete Problem bereits vollstaendig und bleiben minimal-invasiv.

Verifikation: synthetischer Test der Beispielszenerie aus dem Nutzer-
Screenshot (Regime-Konflikt=negativ, Retail-Konsens-Risiko=positiv) gegen
beide Formatierungsfunktionen, Tk-Smoke-Test bestaetigt, dass `tk.Text`
die drei Zeichen (U+25B2/U+25CF/U+25BC) unveraendert speichert/liefert.

## Nachtrag (2026-07-20): Dark-Mode-Comboboxen kaum lesbar (TCombobox-Styling-Luecke)

Nutzer-Screenshot vom "These bearbeiten"-Dialog (Schwerpunkte-Tab, live am
Notebook): alle vier readonly-Comboboxen (Hauptgruppe, Unterkategorie,
Richtung, Staerke) erschienen hell/kaum lesbar - sahen aus wie deaktivierte
Felder, obwohl `state="readonly"` (der Standard-Zustand fuer feste
Auswahllisten im gesamten Projekt) korrekt und normal editierbar ist.

Root Cause: `ui/theme.py::apply_dark_mode()` konfigurierte `TCombobox` nur
generisch mit `background`/`foreground`, setzte aber nie `fieldbackground`
(die eigentliche Textfeld-Flaeche im 'clam'-Theme, getrennt von
`background`) und keinen `style.map()` fuer den `readonly`-Zustand -
'clam' fiel dadurch im geschlossenen Zustand auf seine eingebaute helle
Systemfarbe zurueck. Zusaetzlich ist das aufklappende Popdown einer
ttk.Combobox intern ein klassisches Tk-Listbox-Widget, das `ttk.Style`
gar nicht erreicht und eigene `option_add()`-Zeilen braucht.

**Fix:** `style.configure("TCombobox", fieldbackground=..., arrowcolor=...)`
+ `style.map("TCombobox", fieldbackground=[("readonly", ...), ("disabled",
...)], foreground=[("readonly", ...), ("disabled", ...)], ...)` sowie vier
neue `root.option_add("*TCombobox*Listbox...")`-Zeilen fuer das Popdown.
Betrifft alle Comboboxen im Dark Mode projektweit (nicht nur den
Schwerpunkte-Tab) - reiner Style-Fix in der zentralen Theme-Datei, keine
Aenderung an einzelnen Dialogen noetig.

Verifikation: `ttk.Style.lookup("TCombobox", "fieldbackground"/"foreground",
state=["readonly"])` nach `apply_dark_mode()` liefert die erwarteten
Dark-Palette-Werte (vorher lieferte die Style-Lookup keinen expliziten
Override, `clam` nutzte seine Vorgabe); Tk-Smoke-Test baut den echten
`TheseDialog` fehlerfrei unter Dark Mode auf. Light Mode unveraendert (ruft
`apply_dark_mode()` gar nicht auf).

## Nachtrag (2026-07-20): Bitpanda-Gelistet-Override fuer Aktien/ETF/Rohstoffe

**Ausloeser:** Nutzer bemerkte im Signale-Detail-Panel und im laufenden
Notebook, dass mehrere gehaltene Rohstoff-/Themen-ETF-Positionen (CEBS,
EXH3, ISOC, VVMX, X136, OD7C/H/L/N, DBPK, 3QSS) durchgaengig als "nicht bei
Bitpanda gelistet" markiert wurden, obwohl er sie real haelt und handeln
kann - belegt mit zwei echten Bitpanda-Screenshots (DBPK = "S&P 500 2X
Inverse", ISOC = "iShares Agribusiness"), beide mit aktiven Kaufen/
Verkaufen/Tauschen-Buttons und real gehaltenen Anteilen.

**Root Cause (live verifiziert):** `api/bitpanda.py`s `/v3/assets`-
Endpunkt fand fuer keines der genannten Symbole einen Treffer - weder per
Symbol- noch per Namensvergleich (Volltextsuche nach "Copper Miners"/
"Food & Beverage"/"Agribusiness" ueber den kompletten Katalog, 3185
Eintraege inkl. 177 "etf" + 30 "etc", ergab null Treffer). Der Endpunkt ist
fuer Bitpandas "Bitpanda Stocks"-Fractional-ETF/ETC-Produktlinie offenbar
keine vollstaendige Quelle - PLTR/VST (echte Aktien) werden dagegen korrekt
gefunden. Reine Datenquellen-Luecke, kein Logikfehler in `is_listed()`.

**Konkreter Schaden:** `pre_check()` setzt `kauf_erlaubt = len(veto_reasons)
== 0`, `bitpanda_gelistet is False` landet in `veto_reasons`. In
`post_check()` erzwingt das bei jedem KAUFEN/NACHKAUFEN-Vorschlag
automatisch `risk_veto=True` -> `action="HALTEN"` (siehe RM-Bitpanda,
Kap. 3/Abschnitt 100/101 in diesem Manual). Fuer die betroffenen Assets
konnte die App also strukturell NIE einen (Nach-)Kauf empfehlen, unabhaengig
von der eigentlichen Analyse. VERKAUFEN/TAUSCHEN sind nicht betroffen (der
Veto greift nur bei `_BUY_ACTIONS`).

**Fix: manueller Override statt Abschaltung der Pruefung.** Neue Tabelle
`asset_bitpanda_override` (`database/db.py`, analog `asset_hebel_settings`)
+ `get_bitpanda_gelistet_override()`/`set_bitpanda_gelistet_override()`.
Default (keine Zeile): kein Override, der Live-Check gilt unveraendert -
keine Verhaltensaenderung fuer alle anderen Assets, insbesondere echtes
Krypto (CANTON/CC-Fall bleibt korrekt erfasst). Alle 4 Spot-family-
Pipelines (`agent/krypto/pipeline.py`, `agent/aktien/pipeline.py`,
`agent/rohstoff/pipeline.py`, `agent/themen_etf/pipeline.py`) pruefen den
Override direkt nach dem Live-Check: `if not bitpanda_gelistet and
db.get_bitpanda_gelistet_override(conn, asset.symbol): bitpanda_gelistet
= True`. Neuer Button "Bitpanda-Override umschalten" im Watchlist-Tab
(gleiches Auswahl-Toggle-Muster wie "Hebel-Pruefung umschalten", aber fuer
JEDE Assetklasse verfuegbar, nicht nur Krypto). Die Bitpanda-Spalte zeigt
bei aktivem Override "✓ (M)" statt "✗" - macht den effektiven Wert, den die
Pipelines tatsaechlich verwenden, transparent sichtbar.

**Nutzer-Vorgabe:** fuer zukuenftige Assets soll der Override manuell in
der App setzbar sein, nicht nur fuer die aktuell elf identifizierten
Symbole - deshalb ein generischer Toggle statt einer Hardcoded-Ausnahme-
liste im Code. Der Nutzer aktiviert den Override selbst am Notebook fuer
die von ihm bestaetigten Symbole (Desktop darf keine Produktivdaten
schreiben, siehe `feedback_desktop_kein_produktivstart`).

Verifikation: synthetischer Test von `get_/set_bitpanda_gelistet_override()`
(Default False, Toggle, ON-CONFLICT-Update ohne Fehler); Tk-Smoke-Test der
kompletten `TradingInfoToolApp` (In-Memory-DB, synthetisches CEBS-Asset) -
Watchlist-Spalte zeigt vor Override "✗", nach Klick auf den neuen Button
"✓ (M)", nach erneutem Klick wieder "✗", `get_bitpanda_gelistet_override()`
spiegelt den DB-Zustand exakt; Import-Check aller 4 Pipelines + `ui/app.py`
fehlerfrei.

## Nachtrag (2026-07-20): Bitpanda-Katalog-Dedup verwarf Krypto-Token bei Ticker-Kollision mit Aktien

**Ausloeser:** Nutzer bemerkte im Watchlist-Screenshot, dass mehrere Krypto-
Assets (SUI, W/Wormhole, BIO/Bio Protocol, CAT/Simon's Cat) - darunter SUI
als `core`-Position - ploetzlich rot/"nicht bei Bitpanda gelistet" zeigten,
obwohl es sich um bekannte, real gehandelte Token handelt.

**Root Cause (live bestaetigt):** `api/bitpanda.py::_fetch_all_bitpanda_assets()`
dedupliziert seit dem 2026-07-19-Bugfix ("erstes Vorkommen gewinnt") per
`symbol` UEBER ALLE Anlageklassen hinweg. Der Rohdatensatz enthaelt aber
echte Ticker-Kollisionen ZWISCHEN unterschiedlichen Klassen: Krypto-Token
"SUI" koexistiert mit der Aktie "Sun Communities" (REIT), "BIO" mit
"Bio-Rad Laboratories", "W" mit "Wayfair", "CAT" mit "Caterpillar" - live
im Rohdatensatz (vor Dedup) bestaetigt: beide Eintraege sind vorhanden.
Da die Aktien-Eintraege im Rohdatensatz vor den Krypto-Eintraegen auftraten,
"gewann" jeweils die Aktie den Dedup-Slot, der echte Krypto-Token wurde
schon VOR der gruppenspezifischen Filterung (`get_listed_assets()`) still-
schweigend verworfen. Der urspruengliche Bugfix vom 19.07. hatte diese ca.
53 "echten Symbol-Duplikate" bereits im eigenen Docstring korrekt als
"vermutlich verschiedene interne Assets mit kollidierendem Ticker"
identifiziert - aber trotzdem pauschal dedupliziert, ohne die Assetklassen-
uebergreifende Konsequenz zu bedenken.

**Fix:** Dedup-Schluessel von `symbol` auf `(symbol, group)` geaendert -
entfernt weiterhin echte Innerhalb-derselben-Gruppe-Duplikate (der
urspruengliche Zweck), behaelt aber Eintraege aus unterschiedlichen Gruppen
mit zufaellig gleichem Ticker als eigenstaendige Assets. Betrifft nur
`api/bitpanda.py`, keine Aenderung an Aufrufern noetig (`is_listed()`
bekommt ohnehin schon gruppen-gefilterte Listen).

**Vollstaendigkeits-Check:** alle 56 Watchlist-Symbole gegen den echten
Katalog geprueft - genau die 4 vom Nutzer gefundenen Symbole betroffen,
keine weiteren Kollisionen. Verifikation: Live-Check bestaetigt SUI/BIO/W/
CAT jetzt korrekt als gelistetes Krypto-Asset; Regressionstest bestaetigt
PLTR/VST (Aktien) weiterhin korrekt, die vier Kollisions-Symbole bleiben
auf der Aktien-Seite ebenfalls korrekt vorhanden (Sun Communities/Bio-Rad/
Wayfair/Caterpillar), CANTON/CC-Namens-Fallback weiterhin funktionsfaehig;
Tk-Smoke-Test der Watchlist-Spalte zeigt SUI/W jetzt "✓" statt "✗".

## Nachtrag (2026-07-20): Groq als Primär-LLM abgeloest - Mistral vor Groq + DB-persistente Erschoepfungs-Erkennung

**Ausloeser:** Nutzer bewertete Groq nach Auswertung der heutigen echten
LLM-Aufrufe als Primär-LLM "relativ unbrauchbar" - reale Zahlen bestaetigten
das: nur 9 von 79 echten Calls (~11%) liefen ueber Groq, `api_health` zeigte
echte `429 Too Many Requests`-Fehler. Zusaetzlich bestand seit dem
2026-07-18-Fund (siehe Nachtrag "Groq-Erschoepfungs-Erkennung") eine offene
Schwaeche: die In-Memory-Erschoepfungssperre wurde bei jedem App-Neustart
zurueckgesetzt - in der aktiven Entwicklungsphase (Notebook startet bei
jedem Git-Pull neu, ~8x/Tag beobachtet) lief Groq dadurch wiederholt binnen
Minuten erneut in dieselben 429-Fehlschlaege, bevor die Sperre erneut
greifen konnte.

**Fix 1 - Reihenfolge umgedreht:** `agent/krypto/budget_allocator.py` versucht
fuer jeden Kandidaten (Hebel/Marktscan/Spot) jetzt zuerst Mistral (falls
`mistral_client` gesetzt), erst bei dessen Fehlschlag Groq, dann Gemini.
Mistrals echt verifizierte Kapazitaet (2.250.000 TPM/300 RPM, siehe Nachtrag
Mistral-Integration) macht es zur zuverlaessigeren ersten Stufe; Groq bleibt
als kostenlose zweite Stufe erhalten (schlaegt gelegentlich noch erfolgreich
an), Gemini bleibt bewusst am Ende der Kette (ungueenstigste
Vertragsbedingungen, siehe Modul-Docstring).

**Fix 2 - DB-persistente Erschoepfungs-Erkennung:** neue Tabelle
`groq_exhaustion_status` (Einzeilen-Tabelle, `datum`/`fehlschlaege`/
`erschoepft`) in `database/db.py`, mit `is_groq_exhausted_today(conn)`/
`record_groq_failure(conn, schwelle)`/`record_groq_success(conn)` - ersetzen
1:1 die bisherigen modul-globalen In-Memory-Variablen (gleiche
Kalendertag-Semantik: N Fehlschlaege in Folge am selben Kalendertag ->
erschoepft, Erfolg setzt zurueck), ueberleben aber jetzt einen App-Neustart,
da der Zustand direkt aus der DB gelesen/geschrieben wird statt aus einer
Prozess-Variable. `_mit_fallback_chain()` in `budget_allocator.py` ruft
diese drei Funktionen ueber eine kurzlebige `conn_factory()`-Verbindung auf
(gleiches Muster wie der bestehende `_mit_conn()`-Helfer fuer die LLM-Calls
selbst).

**Verifikation:** synthetischer Test bestaetigt DB-Persistenz (Erschoepfung
ueberlebt einen simulierten "Neustart", d.h. eine neue Connection auf
dieselbe DB-Datei, Erfolg setzt korrekt zurueck) sowie die neue
Fallback-Reihenfolge in `run_budget_allocator()` gegen eine echte
In-Memory-SQLite-Kopie mit Fake-Clients: (1) Mistral erfolgreich -> Groq
wird gar nicht erst aufgerufen, (2) Mistral schlaegt fehl -> Fallback auf
Groq greift korrekt, (3) Groq DB-seitig als erschoepft markiert -> wird bei
einem Mistral-Fehlschlag korrekt uebersprungen (kein Aufruf, `result.
groq_erschoepft_erkannt=True`). Import-/Syntax-Check von
`agent/krypto/budget_allocator.py` und `scheduler/background.py` bestaetigt
keine verwaisten Referenzen mehr auf die entfernten In-Memory-Funktionen.

**Offen (bewusst nicht Teil dieser Runde):** `agent/multi_asset_batch.py`
(separater Cron fuer Aktien/Rohstoffe/Themen-ETF) hat weiterhin keinerlei
Groq-Erschoepfungs-Bewusstsein (kein Skip-Check, keine Erfolg-/Fehlschlag-
Aufzeichnung), obwohl es denselben Groq-Rate-Limit-Pool teilt - eine
natuerliche Erweiterung fuer Konsistenz, aber nicht Teil dieses expliziten
Nutzer-Auftrags ("ja mach beides" bezog sich nur auf die zwei oben
genannten Punkte).

## Nachtrag (2026-07-20): Provider-Performance-Karte nach Assetklasse aufgeschluesselt (Krypto/Aktien/Rohstoffe/ETF getrennt statt gepoolter "Spot"-Topf)

**Ausloeser:** Nutzer fragte nach dem Status von Backward-Tracking bei
Nicht-Krypto-Assetklassen anhand eines Remote-Status-Screenshots ("Provider-
Performance (Spot): noch keine Daten"). Antwort: Backward-Tracking selbst
lief fuer Aktien/Rohstoffe/Hedge/Themen-ETF bereits automatisch mit (alle 4
Spot-family-Pipelines schreiben ueber `db.insert_signal()` in dieselbe
`signals`-Tabelle, `run_backward_tracking()` liest diese Tabelle OHNE
Assetklassen-Filter) - das war kein Luecken-Fund. Die eigentliche Luecke:
`compute_provider_performance()` poolte ALLE Spot-Assetklassen (Krypto,
Aktien, Rohstoffe, Hedge, Themen-ETF) unter einem einzigen "spot"-
Schluessel in der Anzeige-Karte, wodurch nicht sichtbar war, ob eine
spaetere Win-Rate von Krypto oder z.B. Rohstoffen kommt - derselbe
Pooling-Fehler, der fuer den internen Win-Rate-Prompt-Fakt
(`compute_win_rate_fact()`) schon am 2026-07-18 behoben worden war, aber
fuer diese Anzeige-Karte nie nachgezogen wurde.

**Fix:** `agent/krypto/backward_tracking.py::compute_provider_performance()`
bekommt einen neuen optionalen Parameter `watchlist` (Default `None` = altes
Verhalten, ein gepoolter "spot"-Schluessel - erhaelt `extract_notebook_
diagnose.py` unveraendert funktionsfaehig, das ohne Watchlist aufruft). Ist
`watchlist` gesetzt, wird jedes aufgeloeste Spot-Signal ueber sein Symbol
der `asset.assetklasse` (krypto/aktien/rohstoffe/etf) zugeordnet statt
pauschal "spot" - bewusst FEINER als `compute_win_rate_fact()`s Pooling
(das Krypto+Aktien fuer die Prompt-Kalibrierung bewusst zusammenlegt),
weil diese Anzeige-Karte dem Nutzer Sichtbarkeit PRO Assetklasse geben
soll, nicht ein Modell kalibrieren. `remote/status.py::_get_provider_
performance()` reicht die Watchlist jetzt durch. `remote/server.py`
rendert die Spot-Seite ueber eine neue Funktion `renderSpotProviderPerformanceByAssetklasse()`
mit fester Reihenfolge/Beschriftung (Krypto/Aktien/Rohstoffe/ETF -
Themen-ETF und Hedge teilen sich die Watchlist-Assetklasse "etf" und
werden hier bewusst nicht weiter unterschieden), damit auch eine noch
leere Assetklasse sichtbar "noch keine Daten" zeigt statt stillschweigend
zu fehlen. Die Hebel-Karte bleibt unveraendert (Hebel ist ohnehin
krypto-exklusiv).

**Verifikation:** synthetischer Test mit 4 synthetischen, ueber den echten
Schreibpfad (`db.insert_signal()` + `db.update_signal_outcome()`) erzeugten
Signalen (je eins pro Assetklasse, je ein anderer Provider) bestaetigt:
(1) mit `watchlist` werden Krypto/Aktien/Rohstoffe/ETF korrekt getrennt
ausgewiesen, kein gepoolter "spot"-Schluessel mehr vorhanden; (2) ohne
`watchlist` (Legacy-Aufruf wie in `extract_notebook_diagnose.py`) bleiben
alle Spot-Signale weiterhin unter einem gemeinsamen "spot"-Schluessel
gepoolt, exakt wie vor der Aenderung. Syntax-Check aller 3 geaenderten
Dateien bestanden.

## Nachtrag (2026-07-20): Z.ai (Zhipu AI) testweise als vierte, unverifizierte Fallback-Stufe VOR Mistral eingehaengt

**Ausloeser:** Direkte Fortsetzung der Groq-Alternative-Recherche (siehe
[[project_groq_alternative_recherche_2026-07-20]] und
[[reference_llm_provider_recherche_uebersicht]]) - Z.ai/Zhipu GLM-4.5-Flash
wurde als echtes, dauerhaftes Free-Tier-Modell identifiziert (kein Trial-
Guthaben, OpenAI-kompatibler Endpunkt, gute Vertragsbedingungen fuer API-
Kunden: keine Speicherung, keine Trainings-Nutzung). Einzige offene Luecke:
die exakten Rate-Limits sind oeffentlich nicht dokumentiert (nur ein
Concurrency-Limit von 2 im Nutzer-Dashboard sichtbar, keine RPM/TPM/RPD-
Zahl). Nutzer-Entscheidung, trotzdem sofort produktiv zu testen: "kein
Grund nicht auf ein bestimmtes hoeheres Limit zu gehen, wenn diese Quelle
blockiert wird passiert auch nichts fuer diese eine Nacht".

**Umgesetzt:**
- `api/zai.py` (neu) - `ZaiClient`, identisches `.chat()`-Interface wie
  Groq/Mistral/Gemini (OpenAI-kompatibel, `https://api.z.ai/api/paas/v4/
  chat/completions`, Modell `glm-4.5-flash`). Bewusst KEIN konservativer
  Rate-Limiter wie bei Mistral (`RATE_LIMIT_PER_MINUTE = 120` ist nur ein
  grobes Sicherheitsnetz, keine Kapazitaetsschaetzung) - Nutzer-Vorgabe.
- `agent/krypto/budget_allocator.py`: neuer optionaler Parameter
  `zai_client`, eigener Tagesbudget-Zaehler (`zai_taegliches_budget`,
  Default 300 in `config.yaml`), neue `AllocationResult`-Felder
  (`zai_calls_verbraucht`/`zai_budget_erschoepft`). Alle 3 Tiers (Hebel/
  Marktscan/Spot) versuchen jetzt Z.ai VOR Mistral/Groq - testweise, NICHT
  final, siehe Modul-Docstring.
- `main.py`: `ZAI_API_KEY` gelesen, `ZaiClient` konstruiert (P-8-optional),
  an `build_scheduler()`/`app.run_app()` durchgereicht.
- `scheduler/background.py`: `hebel_screening_job()`/`build_scheduler()`
  reichen `zai_client` durch.
- UI-Wiring: `ui/app.py`, `ui/hebel_view.py`, `ui/signals_view.py` - neuer
  `zai_client`-Parameter, `_any_llm_client_available()` erweitert, die
  manuellen Einzel-Klick-Fallback-Tupel (Hebel-Tab + Signale-Tab, alle
  Assetklassen) versuchen Z.ai ebenfalls zuerst.
- `agent/krypto/llm_provider.py`: neuer `zai`-Zweig in `llm_model_label()`.
- `remote/server.py`: `"zai"` zu `API_HEALTH_GROUPS["api-health-llm"]`
  ergaenzt.
- `.env.example`/`.env`: `ZAI_API_KEY`-Platzhalter mit vollem
  Recherche-Kontext als Kommentar (gleiches Muster wie Mistral).

**Bewusst NICHT Teil dieser Runde:** `agent/multi_asset_batch.py` (Aktien/
Rohstoffe/Themen-ETF-Cron) - gleiche Scope-Entscheidung wie beim Groq-
Erschoepfungs-Fix, Z.ai bleibt vorerst auf die Krypto-Kette beschraenkt.

**Verifikation:** (1) echter Testaufruf gegen die echte Z.ai-API - einfacher
Chat-Call UND JSON-Mode (`response_format={"type": "json_object"}`) beide
erfolgreich, bestaetigt volle OpenAI-Kompatibilitaet. (2) Import-/Syntax-
Check aller 9 geaenderten Dateien fehlerfrei. (3) Synthetischer Test der
kompletten Fallback-Kette mit Fake-Clients gegen eine echte In-Memory-
SQLite-Kopie: Z.ai erfolgreich -> Mistral/Groq werden nicht gerufen; Z.ai
schlaegt fehl -> Fallback auf Mistral korrekt; Z.ai-Tagesbudget erschoepft
-> wird korrekt uebersprungen, Kette faellt auf Mistral zurueck.

**Offen:** Reihenfolge ist testweise, nicht final - sobald genug echte
Betriebsdaten (api_health-429-Rate, Provider-Performance) vorliegen, wird
neu entschieden, ob Z.ai vor Groq bleibt, dahinter wandert, oder bei
schlechten Ergebnissen wieder entfernt wird.

## Nachtrag (2026-07-20, spaet abends): Z.ai auf letzte Fallback-Stufe zurueckgestuft + Budget-Neukalibrierung

**Ausloeser:** Erste echte Testnacht mit Z.ai an erster Stelle (siehe
Nachtrag oben) lieferte sofort 2/2 `Read timed out`-Fehlschlaege
(hebel:NEAR:LONG, hebel:SUI:LONG, je nach ~80-100s) auf dem Notebook.
Root-Cause-Diagnose ueber mehrere Schritte:
1. Notebook-Log gruendlich durchsucht (`zai-Call für ... fehlgeschlagen`-
   Zeilen gefunden) - kein Haenger, sondern echte `ReadTimeout`-Exceptions.
2. Live-Test vom Desktop aus mit trivialem Prompt ("Antworte nur mit OK"):
   3/3 Erfolge in 4.6-10.2s - Z.ai grundsaetzlich erreichbar und schnell.
3. Live-Test vom Desktop mit REALISTISCHER Payload (echter `SYSTEM_PROMPT`
   aus `hebel_analyst.py`, 11.761 Zeichen + synthetisches Facts-JSON,
   JSON-Mode wie in der echten Pipeline): Timeout nach exakt 60.4s -
   reproduziert unabhaengig vom Notebook, also ein echtes Kapazitaets-
   problem der Payload-Groesse, kein Notebook-Netzwerk-/Hardware-Problem.
4. Vergleichstest beider echter Free-Tier-Modelle mit 150s-Timeout:
   GLM-4.5-Flash antwortete nach 109.2s korrekt und vollstaendig (valides
   JSON gemaess Schema) - GLM-4.7-Flash lieferte auch nach vollen 150s
   keine Antwort (Concurrency-Limit 1 statt 2, damit endgueltig verworfen).

**Fazit:** GLM-4.5-Flash ist nicht kaputt/unerreichbar, sondern schlicht zu
langsam fuer eine FRUEHE Fallback-Stufe (~110s realistische Antwortzeit,
der bisherige 60s-Timeout war strukturell zu knapp). Als erste Stufe wuerde
das jeden einzelnen Kandidaten um bis zu 2 Minuten verzoegern, bevor der
Fallback ueberhaupt greift - direkt gegensaetzlich zum parallel
dokumentierten Delta-Thema (siehe [[project_delta_berechnung_llm_abfrage_timing]]).

**Umgesetzt:**
- `agent/krypto/budget_allocator.py`: alle 3 Tiers (Hebel/Marktscan/Spot)
  neu geordnet auf Mistral -> Groq -> Gemini -> Z.ai (Z.ai jetzt echte
  letzte Stufe statt erste).
- `api/zai.py`: neue Konstante `REQUEST_TIMEOUT_SECONDS = 150` (vorher
  hart codiert 60s) - als letzte Stufe faellt die laengere Wartezeit kaum
  ins Gewicht, da nur genutzt wenn Mistral/Groq/Gemini alle drei
  fehlschlagen.
- Docstrings/Log-Zeilen in `main.py`, `budget_allocator.py`, `api/zai.py`,
  `config.yaml` auf die neue Reihenfolge korrigiert (vorher ueberall
  "testweise VOR Mistral").
- **Budget-Neukalibrierung** (Nutzer-Vorgabe: "flachere Budgetkurve,
  Glaettung, vernuenftige Last auf die ersten Quellen, dann sehen wir wo
  wir liegen" - Ziel: reale Kapazitaetsgrenzen von Mistral/Groq/Gemini
  ueber echte Nutzung sichtbar machen, UND beobachtete "1h-Leerlaufphasen"
  reduzieren, bei denen das Tagesbudget B schon frueh erschoepft war und
  fuer den Rest des Tages kein neuer Kandidat mehr einen LLM-Versuch
  bekam):
  - `mistral_taegliches_budget`: 150 -> 400 (weiterhin klar unter der
    echt verifizierten ~300/Min-Kapazitaet).
  - `gemini_taegliches_budget`: 200 -> 500 (weiterhin unter der
    recherchierten ~1.000-1.500/Tag-Kapazitaet).
  - `taegliches_budget_gesamt` (B): 90 -> 180 - deutlich mehr Puffer
    ueber dem rein rechnerischen Spot-Rotation-Bedarf (84/Tag bei 8h/15h-
    Cooldown), bleibt aber weiterhin unter Mistrals neuem 400er-Deckel,
    damit echte Ausreissertage kontrolliert in Gemini/Zai ueberlaufen
    statt den ganzen Tag ungebremst durchzuschlagen.
  - `spot_rotation_reserve` (F): 30 -> 60 (Verhaeltnis F/B ≈ 33%
    beibehalten).
  - Groq hat weiterhin keinen Tages-Deckel (nur echte 429-
    Erschoepfungserkennung) - laeuft also bereits "unter Last".

**Verifikation:** Reihenfolge-Aenderung per `grep` in allen 3 Tiers
bestaetigt (Mistral->Groq->Gemini->Zai). Syntax-Check aller 4 geaenderten
Python-/YAML-Dateien fehlerfrei. `_verteile_budget()` mit einem
synthetischen Ausreissertag getestet (20 Hebel + 15 Marktscan + 84 faellige
Spot-Kandidaten = 119 gesamt): mit dem alten B=90 waeren Spot-Kandidaten
auf 55 gekappt worden, mit B=180 bekommen alle 119 einen LLM-Versuch.

**Offen:** Erst nach einem echten Notebook-Neustart (config.yaml wird nur
einmal pro Prozess gelesen) wirksam. Weiterhin zu beobachten: ob die neuen,
grosszuegigeren Budgets zu mehr echten 429-Fehlern bei Mistral/Gemini
fuehren (dann waere die reale Kapazitaetsgrenze gefunden), und ob die
"1h-Leerlaufphasen" durch B=180 tatsaechlich seltener werden.

## Nachtrag (2026-07-21, Vormittag): Erste Nacht-Auswertung + BUGFIX Zeitzonen-Anzeige in Signal-E-Mails + zweiter Zai-Datenpunkt

**Nacht-Auswertung (frischer `extract_notebook_diagnose.py`-Export, ca.
9,5 Std. nach dem Neustart, Fokus letzte 6 Std.):** Die Umstellung wirkt
wie gedacht. Letzter `zai-Call`-Fehlschlag im gesamten Log war um 21:57 Uhr
- noch mit dem ALTEN Code (Timeout=60, Zai zuerst). Danach: kein einziger
Zai-Versuch mehr trotz durchgehender Aktivitaet, weil Zai jetzt hinten
steht und Mistral seither JEDEN Kandidaten sofort erfolgreich bedient
(alle stichprobenartig geprueften Hebel-/Spot-Signale der letzten 6 Std.
zeigen `llm_model: mistral:mistral-small-2506`, keine Mistral-Fehlschlaege,
kein 429, Tageszaehler von 3 - nach UTC-Mitternachts-Reset - auf 25 bis
06:18 Uhr, deutlich unter dem neuen 400er-Deckel). Groq/Gemini: 0 Calls,
nicht wegen Erschoepfung sondern weil Mistral nie fehlschlaegt. Keine
1h-Leerlaufphasen mehr sichtbar - alle `Budget-Allocator:`-Zusammenfassungs-
zeilen liegen durchgehend ~15 Minuten auseinander.

**BUGFIX - Zeitzonen-Anzeige in Signal-E-Mails (Nutzer-Fund):** eine
Hebel-E-Mail (KAIA ERÖFFNEN) zeigte `"Berechnet: 2026-07-21 01:17"` im
Mail-Body, waehrend der Gmail-Header den Empfang um `03:18 Uhr` (lokale
Zeit) auswies - wirkte wie eine 2-Stunden-Verzoegerung zwischen Berechnung
und Versand. Tatsaechlich war `signal.created_at` in der DB korrekt als
UTC gespeichert (`01:17:44+00:00` = `03:17:44` lokal, CEST = UTC+2) - der
Mail-Text zeigte aber den rohen UTC-String OHNE Umrechnung
(`signal.created_at[:16].replace("T", " ")`, an 3 Stellen in
`scheduler/background.py` identisch). Kein echtes Latenzproblem, reiner
Anzeige-Bug. **Fix:** neue Funktion `_formatiere_zeitpunkt_lokal()`
(`datetime.fromisoformat(...).astimezone().strftime(...)`, konvertiert auf
die lokale Systemzeitzone) ersetzt alle 3 Vorkommen. Wichtig: dieser Fund
betrifft NICHT die andere, echte Beobachtung vom Vorabend (Marktscan-
Discovery 16:00 Uhr vs. Signal 19:30 Uhr, siehe
[[project_delta_berechnung_llm_abfrage_timing]]) - das ist ein separater,
weiterhin ungeloester Mechanismus (Warteschlange im Budget-Allocator),
kein Zeitzonen-Darstellungsfehler.

**Zweiter Zai-Realdaten-Punkt (Desktop-Live-Test, gleiche realistische
Payload wie am Vorabend):** GLM-4.5-Flash, das am Vorabend noch nach
109,2s erfolgreich geantwortet hatte, schaffte es diesmal NICHT innerhalb
von 150s (`ReadTimeout` nach 150,8s). GLM-4.7-Flash ebenfalls Timeout nach
150,6s. Die Antwortzeiten sind also nicht stabiler/schneller geworden,
eher volatiler - bestaetigt die Entscheidung, Zai nur noch als letzte,
selten erreichte Stufe zu fuehren.

**Verifikation:** `_formatiere_zeitpunkt_lokal()` funktional getestet
(UTC `2026-07-21T01:17:44...+00:00` -> lokal `2026-07-21 03:17`, `None` ->
`"-"`, kaputter String -> Fallback auf alte Slicing-Logik). Syntax-Check
von `scheduler/background.py` fehlerfrei.

## Nachtrag (2026-07-21): Groq-Alternative-Recherche Runde 3+4 abgeschlossen - 32 Kandidaten insgesamt verworfen, Suche vorerst beendet

Ausgeloest durch Zais enttaeuschende erste Nacht, vom Nutzer bewusst NICHT
nach dem ersten Fehlschlag abgebrochen ("Runde nicht vorbei, nur durch
Fehlschlag unterbrochen"), spaeter fortgesetzt bis zu einem selbst gesetzten
Budget ("noch ca. 5 Kandidaten, dann Schluss fuer heute"). Runde 3 (7
Kandidaten: Vercel AI Gateway, OpenCode Zen, OVHcloud AI Endpoints,
SambaNova-Re-Check, Moonshot/Kimi, MiniMax, SiliconFlow) und Runde 4 (10
Kandidaten: xAI-Re-Check, Scaleway, AI21 Labs, Fireworks AI, Nebius AI
Studio, StepFun, 01.AI/Yi, Poe API, Reka AI, Baidu Qianfan/ERNIE) - alle
Details in Memory [[project_groq_alternative_recherche_2026-07-20]].

**Bemerkenswertester Fund: Nebius AI Studio** (Nebius B.V., Amsterdam,
Nasdaq-gelistet) - qualitativ die besten Vertragsbedingungen der gesamten
Recherche: automatische Rate-Limit-Skalierung basierend auf echter Nutzung
statt Bezahlung (Dokumentation: "wenn Nutzung in einem 15-Min-Fenster
>=80% des Limits erreicht, steigt das Limit um 20%"), GDPR-nativ, ToS
woertlich "Nebius will not use Customer Content to train Nebius Models".
Scheiterte trotzdem am selben harten Ausschlusskriterium wie fast alle
anderen Kandidaten dieser beiden Runden: eine Kreditkarte ist fuer den
Signup zwingend ("$0 authorization to verify the card"). Nutzer hat den
Schritt bewusst abgebrochen, keine Kartendaten eingegeben.

**Durchgaengiges Muster ueber beide Runden:** praktisch jeder gepruefte
Kandidat gehoert zu einer von drei Kategorien - (1) reiner Einmal-Trial
statt dauerhaftem Free-Tier (Scaleway, AI21, Fireworks, StepFun, Reka,
Moonshot), (2) Kreditkarte/Zahlungsmethode zwingend fuer brauchbare Limits
(Vercel, OVHcloud, SiliconFlow, Nebius), oder (3) struktureller Zugangs-
Ausschluss (Baidu: chinesische Mobilfunknummer noetig, wie schon Alibaba/
Qwen in Runde 2).

**Status:** Kette bleibt Mistral -> Groq -> Gemini -> Z.ai. Suche fuer
diese Session auf Nutzer-Wunsch beendet. Revisit-Bedingung siehe Memory:
entweder ein Anbieter mit echtem Dauer-Free-Tier ohne Kreditkarte/China-
Telefon/Umsatzschwelle taucht auf, oder Nebius bietet irgendwann einen
Signup-Pfad ohne Kreditkarten-Pflicht an.

## Nachtrag (2026-07-21, Nachmittag): Zai-Root-Cause endgueltig geklaert - Kontextlaengen-Drosselung >8K Token

Nutzer entdeckte auf der Z.ai-"Rate Limits"-Dashboardseite einen bisher
uebersehenen Erklaerungstext: "To ensure stable access to GLM-4-Flash
during the free trial, requests with context lengths over 8K will be
throttled to 1% of the standard concurrency limit." Das erklaert die seit
zwei Tagen beobachteten Zai-Probleme (2/2 Timeouts erste Nacht, 109,2s-
Erfolg vs. 150s-Doppel-Timeout am naechsten Vormittag) potenziell vollstaendig
- keine allgemeine Modell-Langsamkeit, sondern eine gezielte Drosselung ab
einer bestimmten Kontextgroesse.

**Gezielter Vergleichstest** (`test_zai_context_length_hypothesis.py`,
identischer echter `SYSTEM_PROMPT` aus `hebel_analyst.py`, einmal mit
kleinem, einmal mit auf >8K Token aufgeblaehtem Facts-Payload, glm-4.5-flash,
150s Timeout) bestaetigt die These eindeutig:
- Klein (echte 3.910 Prompt-Tokens laut API-`usage`-Feld, unter 8K): Erfolg
  nach 105,9s (2.184 Zeichen Antwort, 3.387 Completion-Tokens) - deckt sich
  mit dem 109,2s-Erfolgswert vom Vorabend.
- Gross (>8K Token): kompletter `ReadTimeout` nach den vollen 150s, keine
  Antwort.

**Praktische Einordnung:** Unser Hebel-`SYSTEM_PROMPT` allein ist bereits
~11.761 Zeichen (~3.360 Token geschaetzt), der Spot-`SYSTEM_PROMPT` sogar
~18.119 Zeichen (~5.177 Token geschaetzt) - bei echten (nicht synthetischen)
Facts-Payloads mit vollem Kontext (Historie, Risikofaktoren, Makro-Analog-
Vergleich) rutscht man damit speziell bei Spot- und bei umfangreicheren
Hebel-Signalen plausibel regelmaessig ueber die 8K-Grenze.

**Entscheidung:** keine Code-Aenderung. Ein Zai-spezifischer gekuerzter
Prompt wuerde den Aufwand nicht rechtfertigen, da Zai ohnehin nur die
seltenste letzte Rueckfallstufe ist (Mistral bedient real praktisch die
gesamte Last). Root-Cause-Recherche hiermit abgeschlossen.

**Nebenbefund - Dashboard-Anomalie "Last used: Not used" geklaert:** Der
API-Key ("TIT") zeigte durchgehend "Last used: Not used", obwohl mehrfach
echte, erfolgreich abgeschlossene Testcalls liefen (inkl. des obigen
Kleinpayload-Calls mit echten `usage`-Daten in der Antwort). Komplette
Dashboard-Seitenleiste durchgeprueft (Account, Rate Limits, GLM Coding
Plan/My Plan/Usage, API Keys, Billing) plus oberer "API"-Navigationspunkt -
"My Plan"/"Usage" gehoeren nachweislich zu einem anderen Produkt (GLM Coding
Plan, IDE-Abo, "You don't have any subscription"), "Billing" zeigt nur
$0-Bilanz. Auch nach dem definitiv erfolgreichen Testcall weiterhin "Not
used" - damit endgueltig als kosmetische Z.ai-Dashboard-Einschraenkung
eingeordnet (vermutlich rein Billing-Event-basierte Anzeige, die fuer
kostenlose Flash-Modell-Calls ohne Zahlungsereignis nie aktualisiert wird),
OHNE Auswirkung auf unser eigenes (DB-basiertes) Budget-Tracking.
Investigation abgeschlossen.

**Nachtrag - Isolationstest bestaetigt zweite, unabhaengige Bremse:
Generierungsgeschwindigkeit selbst.** Nutzer hinterfragte zurecht, warum
selbst der erfolgreiche Kleinpayload-Call (unter 8K) noch 105,9s brauchte.
Gezielter Isolationstest (`test_zai_speed_isolation.py`, identischer Prompt
~3.866 Token, aber `max_tokens=20` erzwungen statt voller Antwort): Erfolg
nach nur 5,1s. Damit klar getrennt: Prompt-Verarbeitung/Warteschlange ist
schnell (~5s fuer ~3.900 Token Input), die reine Text-Generierung ist der
Flaschenhals (~34-35 Tokens/Sekunde). Das heisst: selbst ein perfekt unter
8K gehaltener Prompt waere bei uns real weiterhin ~100s+ langsam, weil
unser Signal-Schema lange strukturierte JSON-Antworten verlangt - die
Langsamkeit ist NICHT nur kontextlaengenabhaengig, sondern eine zweite,
unabhaengige Bremse der Generierungsgeschwindigkeit auf dem kostenlosen
Tier. Bestaetigt die Entscheidung (Zai bleibt letzte, selten gebrauchte
Rueckfallstufe) noch eindeutiger - Prompt-Kuerzung allein wuerde das
Problem nicht loesen.

**Bestaetigung durch offizielle Z.ai-FAQ** (docs.z.ai/help/faq), Frage "Why
hasn't my account balance changed after I used the API?": "The billing
history reflect daily consumption records, and therefore display the
billing status from the previous day (n-1). Current day consumption will
not be immediately visible in the billing details" (zusaetzlich: "there is
currently a processing delay in our billing system"). Offizielle
Bestaetigung einer generellen n-1-Verzoegerung im gesamten Billing-/
Nutzungssystem - unser Key wurde erst 2026-07-20 abends angelegt, "Not
used" ist damit die dokumentierte Verzoegerung, kein Fehler.

## Nachtrag (2026-07-21): Marktscan-Dedup-Bug behoben - "immer dieselben Coins" (APE/EIGEN)

Im Rahmen der Budget-Allocator-Neuplanung (siehe Plan-Datei
swift-napping-muffin.md) fiel beim historischen Backtest auf, dass ueber
12 Tage/24 Scan-Laeufe nur 8 verschiedene Coins je als `kaufkandidat`
auftauchten. Nutzer-Skepsis ("immer dieselben Ergebnisse sehe ich eher
negativ als positiv") war berechtigt und deckte einen echten, eigenstaendigen
Bug auf - getrennt vom SLA-/Warteschlangen-Thema.

**Root Cause:** `agent/krypto/marktscan.py::_duplicate_should_skip()` prueft
bisher nur, ob ein Coin bereits auf der echten Watchlist ist oder final
entschieden wurde (`nutzer_verworfen`/`nutzer_behalten_manuell_
uebernommen`). Ein Coin mit Status `neu` (unbearbeitete Kaufkandidat-Zeile)
oder `verfallen` wurde NICHT uebersprungen - da jeder der zwei taeglichen
Scan-Laeufe eine komplett neue Zeile anlegt (eigene `scan_run_id`,
`UNIQUE(coingecko_id, scan_run_id)`), wurde derselbe, laengst entdeckte
Coin bei jedem Lauf erneut dupliziert. Historischer Beleg aus der lokalen
DB: APE und EIGEN bekamen am 2026-07-09 acht frische 'neu'-Zeilen innerhalb
weniger Stunden, bevor der Nutzer reagierte - dieselben zwei Coins
dominierten zwei Wochen spaeter noch immer die Stichprobe.

**Einordnung:** Zwei getrennte Effekte. (1) Beabsichtigt/gesund: die
Kaufkandidat-Schwelle (Score >=70) ist bewusst eng - von 468 historischen
Rohkandidaten-Zeilen erreichten nur 3,8% je "kaufkandidat", 84 verschiedene
Coins wurden aber roh entdeckt (Filter A filtert 86% vorher raus, siehe
`apply_stufe_a_filters()`). (2) Echter Bug obendrauf: das fehlende Dedup
liess denselben Coin immer wieder dieselben knappen Plaetze belegen, statt
echten neuen Tages-Kandidaten eine faire Chance zu geben.

**Fix:**
- `database/db.py`: `has_pending_marktscan_kaufkandidat()` (existenzielle
  Pruefung: gibt es IRGENDWO in der Historie eine unbearbeitete
  Kaufkandidat-Zeile fuer diesen Coin?) + `get_letzter_marktscan_verfall_am()`
  (juengster Verfallszeitpunkt fuer die Abklingzeit-Pruefung).
- `_duplicate_should_skip()` erweitert: ueberspringt jetzt zusaetzlich (a)
  Coins mit bereits unbearbeiteter Kaufkandidat-Zeile (unabhaengig von
  einer Zeitschwelle - die bestehende Zeile wartet einfach in Ruhe weiter)
  und (b) kuerzlich (< `verfallen_abklingzeit_stunden`) verfallene Coins
  (verhindert sofortiges Wiederauftauchen, gibt der Marktlage aber nach
  einer Abklingzeit eine neue Chance).
- `config.yaml::marktscan.verfallen_abklingzeit_stunden` (neu, Default 24h).

**Verifikation:** 5 synthetische Testfaelle (unbearbeiteter Kaufkandidat,
kuerzlich verfallen, lange verfallen, nutzer_verworfen, nie gesehener Coin)
- alle bestanden. Smoke-Test gegen die lokale Desktop-DB reproduziert den
echten APE-Fall (`has_pending_marktscan_kaufkandidat` liefert korrekt
`True`).

## Nachtrag (2026-07-21): Budget-Allocator neu gedacht - SLA-Reservierung statt Score-Ranking (Abschnitt 2+3 umgesetzt)

Umsetzung der in `docs/budget_queue_design.md` (Nachtrag) revidierten
Design-Entscheidung, nach vollstaendiger Genehmigung des Plans
(swift-napping-muffin.md) inkl. historischem Backtest VOR jeder Code-
Aenderung (siehe eigener Nachtrag oben zu "Wahre Wartezeit-Erkennung").

**Kernaenderung:** `agent/krypto/budget_allocator.py::_priorisiere_nach_
wartezeit()` teilt jede Kandidatenliste (Hebel-Trigger, Marktscan-
Kaufkandidaten - beide bereits DB-seitig `score_gesamt DESC` sortiert) in
"ueberfaellig" (wahre Wartezeit seit Erstkandidatur >= effektiver SLA-
Schwelle) und "normal". Ueberfaellige werden IMMER zuerst eingereiht (FIFO
untereinander, nach Wartezeit absteigend), Normale behalten die
bestehende Score-Reihenfolge. Der bestehende `[:tier_n]`-Deckel aus
`_verteile_budget()` bleibt unveraendert - echte Garantie statt Soft-Boost,
wie vom Nutzer gefordert.

**Portfolio-Bezug** (`database/db.py::get_portfolio_prioritaets_bonus_
je_symbol()`): die effektive SLA-Schwelle wird pro Symbol reduziert, wenn
es bereits gehalten wird (Spot ODER offene Hebel-Position, 12h Bonus) oder
`WatchlistAsset.rolle=='core'` ist (6h Bonus - deckt den Fall "noch nie
gehalten, aber bewusster Erstkauf-Kandidat" ab). Bewusst NICHT These-
basiert - Krypto ist von der Kategorie-Taxonomie ausgeschlossen (siehe
Marktscan-Dedup-Nachtrag oben).

**Neue config.yaml-Schluessel:** `budget_allocator.hebel_kandidat_sla_
stunden` (6), `marktscan_kandidat_sla_stunden` (30), `bonus_gehalten_
stunden` (12), `bonus_kern_rolle_stunden` (6), `marktscan_kandidat_
luecken_toleranz_stunden` (20), `marktscan_wartezeit_lookback_tage_cap`
(14); `hebel_screening.hebel_kandidat_luecken_toleranz_stunden` (1.5),
`hebel_wartezeit_lookback_tage_cap` (14).

**Verfall-Backstop korrigiert:** `expire_stale_hebel_candidates()`/
`expire_stale_marktscan_candidates()` pruefen jetzt die wahre Kandidatur-
Dauer statt des Alters der (immer frischen) einzelnen Zeile - der 48h-
Verfall wirkt damit erstmals tatsaechlich als Backstop (siehe eigener
Nachtrag oben).

**Verifikation:** Unit-Test `_priorisiere_nach_wartezeit()` (Ueberfaellige
zuerst, Normale behalten Reihenfolge, keine Kandidaten verloren). Info-
Leichen-Regressionstest (Paar mit 60h durchgehender Requalifizierung, 241
Zeilen) - verfaellt jetzt korrekt, waere mit der alten Logik nie verfallen.
End-to-End-Trockenlauf gegen die echte Desktop-DB-Kopie (alle LLM-/
Netzwerk-Clients=None, garantiert kein echter Call) - kompletter Durchlauf
ohne Exception, neue Log-Zeile zeigt korrekt "ueberfaellig=1" fuer den
einzigen vorhandenen Hebel-Kandidaten (FLOKI SHORT).

**Methodik dieser Runde (als Vorgehens-Standard fuer kuenftige aehnliche
Faelle festgehalten):**

1. **Harte Garantie statt Soft-Boost bei systemischen Verzoegerungs-/
   Fairness-Problemen.** Ein "Prioritaet nach Wartezeit leicht erhoehen"-
   Vorschlag wurde vom Nutzer explizit verworfen, weil er das Problem nur
   abschwaecht, nicht strukturell begrenzt (weiterhin von noch hoeher
   gescorten/frischeren Kandidaten verdraengbar). Stattdessen: die
   Kandidatenliste strukturell in "ueberfaellig" (immer zuerst, FIFO
   untereinander) und "normal" (unveraenderte Reihenfolge) teilen - das
   ist eine echte Obergrenze, kein Wahrscheinlichkeits-Vorteil. Gilt als
   Leitplanke fuer jede kuenftige Priorisierungs-/Scheduling-Aenderung in
   diesem Projekt: bei einer echten Deadline-/Fairness-Anforderung ein
   strukturelles Zwei-Klassen-Modell pruefen, bevor ein Score-Zuschlag
   vorgeschlagen wird.
2. **Historischer Backtest gegen echte Produktionsdaten ist ein
   verpflichtendes Gate VOR jeder Aenderung an produktivem Entscheidungs-
   code** (Budget-Allocator, Risk-Gate, Scoring o.ae.) - nicht optional
   und nicht nachtraeglich. Erst nach Ruecksprache zu den Backtest-
   Ergebnissen wurde ueberhaupt mit der eigentlichen Code-Aenderung
   begonnen (siehe Ablauf im Plan `swift-napping-muffin.md`).
3. **Eine einzige Quelle der Wahrheit fuer Backtest und Live-Betrieb**:
   die neuen Wartezeit-Funktionen (`get_hebel_wartezeit_stunden_je_paar()`/
   `get_marktscan_wartezeit_stunden_je_coin()`) bekamen einen optionalen
   `as_of`-Parameter, damit der Backtest exakt dieselbe Produktionslogik
   mit einem Zeitpunkt aus der Vergangenheit aufruft - kein separat
   gepflegter Simulations-Nachbau derselben Regel, der unbemerkt
   auseinanderlaufen koennte.
4. **Nutzer-Skepsis gegenueber einer "harmlosen" Erklaerung ernst nehmen
   und tiefer graben, statt sie als Datensparsamkeit abzutun.** Die
   Beobachtung "immer dieselben Coins (APE/EIGEN)" wurde zunaechst als
   plausible Folge duenner Marktscan-Historie eingeordnet - der Nutzer
   wies das explizit als "eher negativ als positiv" zurueck und verlangte
   eine echte Mechanik-Pruefung. Das deckte den zweiten, unabhaengigen
   Dedup-Bug auf (siehe eigener Nachtrag oben). Bestaetigt/erweitert
   [[feedback_thorough_diagnosis_before_conclusion]]: gilt auch, wenn die
   erste Erklaerung technisch plausibel klingt, aber der Nutzer aus
   Erfahrung/Beobachtung widerspricht.

## Nachtrag (2026-07-21): Abschnitt 4 - Wartezeit-Transparenz in UI + E-Mail

Letzter Baustein des Plans (`swift-napping-muffin.md`): der Nutzer soll die
neue SLA-Logik nicht nur an weniger Verzoegerung erkennen, sondern die
wahre Wartezeit auch direkt einsehen koennen - konsistent mit dem bereits
etablierten Anzeige-Prinzip (`_formatiere_zeitpunkt_lokal()`): reine
Anzeige, nie ein neuer LLM-Fakt.

- `ui/hebel_view.py`/`ui/marktscan_view.py`: Mouseover-Tooltip (nicht neue
  Spalte, `ui/row_tooltip.py`-Muster wie in `regime_view.py`/`thesen_view.py`)
  auf noch unbearbeiteten Kandidaten-Zeilen, live berechnet bei jedem
  `refresh()`/`_refresh_list()` ueber `get_hebel_wartezeit_stunden_je_paar()`/
  `get_marktscan_wartezeit_stunden_je_coin()` - kein neues DB-Feld.
- `scheduler/background.py::_notify_hebel_signal()`: neuer optionaler
  `conn_factory`-Parameter, Zeile "· Wartezeit seit Erstkandidatur: Xh"
  neben "Berechnet: ... · Anbieter: ...". **Bewusst NICHT** in
  `_notify_spot_signal()` ergaenzt (Abweichung von der urspruenglichen
  Plan-Formulierung, nach Code-Pruefung korrigiert): Tier 3 (Spot-Rotation)
  hat keine Kandidatur-Historie wie Hebel/Marktscan (keine wiederholt
  eingefuegten "ist_kandidat"-Zeilen, nur Cooldown-Intervalle) - eine
  Wartezeit-seit-Erstkandidatur ist dort konzeptionell nicht definiert.
  Marktscan-Kaufkandidaten (Tier 2) erzeugen ohnehin kein Signal-Objekt
  (nur eine Kurzbegruendung/"Writeup", siehe `budget_allocator.py`s
  `marktscan:`-Zweig) und werden daher schon bisher gar nicht per E-Mail
  benachrichtigt - unveraendert, kein Teil dieser Aenderung.

**Verifikation:** Tk-Smoke-Test beider Views gegen eine echte DB-Kopie
(FLOKI/SHORT-Tooltip zeigt korrekt 177,8h, identisch zum direkt per
`db.py`-Funktion berechneten Wert) + synthetischer E-Mail-Test
(`_notify_hebel_signal()` mit echtem CAT/SHORT-Wartezeitwert, Zeile
erscheint korrekt im Mail-Body).

**Nebenbefund waehrend der Verifikation:** der End-to-End-Trockenlauf aus
Abschnitt 2+3 (`test_budget_allocator_dry_run.py`) hatte `db.DB_PATH` nie
auf eine Kopie umgebogen und dadurch versehentlich einen echten
Gate-Fail-HALTEN-Datensatz (FLOKI/SHORT, "Preis veraltet oder nicht
vorhanden", kein LLM-Call/keine Kosten) in die echte lokale Desktop-DB
geschrieben - dasselbe Muster wie bei den Desktop-Produktivstart-Vorfaellen
zuvor, diesmal durch ein Test-Skript statt die App selbst. Nutzer
entschied sich fuer Bereinigung, Zeile wurde nach Bestaetigung geloescht.
Lehre: Verifikationsskripte gegen Produktivdaten IMMER `db.DB_PATH` explizit
auf eine Kopie umbiegen, nie den Default-Pfad implizit verwenden.

## Nachtrag (2026-07-21): Historische-Trefferquote-Risikofaktor + Provider-Performance-Karte verstaendlicher

Echter Anlass: erstes BTC-LONG-Hebel-Signal, dessen Gegenargument die
historische Erfolgsquote (0%) nannte, aber den mitgelieferten
Stichprobengroessen-Hinweis (nur 5 aufgeloeste Hebel-Signale bisher, alle 5
Stop-Loss) NICHT erwaehnte - obwohl `hebel_analyst.py`s SYSTEM_PROMPT Regel
14 das Modell explizit dazu anweist. Genau das gleiche Prinzip wie beim
AVAX-Fund (Modell-Interpretationsfehler nicht dem Modell ueberlassen):

- `hebel_risk_gate.py::compute_risikofaktoren_hebel()`: neuer Parameter
  `historische_erfolgsquote` (+ `min_sample_fuer_aussage`, Default 15,
  identisch zu `backward_tracking.py::_MIN_SAMPLE_FUER_AUSSAGE`). Bei
  `anzahl_ausgewertete_signale < 15` erscheint IMMER ein neutraler
  Risikofaktor "Historische Trefferquote X% (n=Y)" mit explizitem
  Stichproben-Hinweis - unabhaengig davon, ob das LLM es im freien
  Gegenargument-Text erwaehnt. Bei ausreichender Stichprobe wird die Quote
  stattdessen als positiv/neutral/negativ bewertet (Schwellen 30%/60%).
  `post_check_hebel()` reicht den bereits in `hebel_pipeline.py` berechneten
  `historische_erfolgsquote`-Fakt einfach durch (keine zweite DB-Abfrage).
- Verifiziert per 3 synthetischen Faellen: kleine Stichprobe (n=5, neutral +
  Hinweistext), grosse Stichprobe mit schlechter Quote (n=20/20%, negativ),
  kein Fakt vorhanden (kein Risikofaktor-Eintrag).

**Provider-Performance-Karte auf der Remote-Seite** (`remote/server.py`):
Nutzer-Fund - "keine Daten" ohne Begruendung war nicht nachvollziehbar. Fix:
- Erklaerender Untertitel unter beiden Karten-Ueberschriften (Spot/Hebel),
  was die Kennzahl bedeutet (nur ECHTE, bereits aufgeloeste Signale, kein
  Backtest) und warum sie je Assetklasse/Tier getrennt ist.
- Leerer Zustand nennt jetzt den Grund ("noch keine abgeschlossenen Signale
  ... kann Tage bis Wochen dauern") statt nur "noch keine Daten" zu meiden.
- Jede Provider-Zeile mit `anzahl_resolved < 15` bekommt denselben
  Stichproben-Hinweis wie oben ("noch nicht belastbar") direkt neben der
  Zahl - dieselbe Schwelle wie im neuen Hebel-Risikofaktor, konsistent
  sichtbar an beiden Stellen.

## Nachtrag (2026-07-22): Retail-Konsens + CRV/Stop-Loss - "Fakt zuerst, Wertung danach"

Ausloeser: Nutzer wertete alle 9 ERÖFFNEN-Empfehlungen einer Nacht (7
Symbole, LONG, Regime baer) im Detail aus und fand zwei echte, wiederholt
auftretende Probleme - beide vom selben Muster ("eine abgeleitete
Kennzahl/binaere Phrase versteckt den eigentlich relevanten Rohwert").

**1. Retail-Konsens-Risiko (5 von 7 Signalen mit Wert betroffen, ~71%):**
Die alte Version pruefte nur "ist die Mehrheit EXTREM (>65%)?" und
beschriftete JEDEN Nicht-Extremfall pauschal als "positiv"/"steht NICHT im
Konsens" - auch bei 51-64% long UND einer LONG-Empfehlung, was tatsaechlich
DIESELBE Richtung wie die (nicht-extreme) Mehrheit ist. Fix in
`hebel_risk_gate.py::compute_risikofaktoren_hebel()`: der Text nennt jetzt
IMMER explizit den Prozentsatz und ob die empfohlene Richtung mit der
Mehrheit uebereinstimmt oder nicht ("Fakt zuerst") - die Bewertung wird
danach in drei Stufen abgeleitet: negativ (extreme gleiche Richtung,
unveraendert), **neutral (NEU - moderate gleiche Richtung, weder klarer
Kontraindikator noch antizyklischer Pluspunkt)**, positiv (nur noch bei
echter Gegenrichtung zur Mehrheit).

**2. CRV kann durch einen unrealistisch engen Stop-Loss aufgeblaeht werden:**
Ein echtes BTC-Signal (21:35 derselben Nacht) hatte einen Stop-Loss nur
1,12% vom Entry entfernt - bei 3x Hebel reicht normales Kursrauschen (kein
Krisenereignis) zum Ausloesen - wurde aber wegen der dadurch aufgeblaehten
CRV (16,41) als "deutlich ueber Minimum, positiv" bewertet. Zum Vergleich:
XLM hatte eine aehnlich hohe CRV (4,20) bei einem soliden 7,72%-Stop - die
reine CRV-Zahl unterscheidet diese sehr unterschiedlichen Risikoprofile
nicht. Fix:
- CRV-Risikofaktor-Text nennt jetzt immer den Stop-Loss-Abstand in % mit.
- Neuer eigener Risikofaktor "Enger Stop-Loss (X%)" (negativ), wenn der
  Abstand unter `risiko.hebel.sl_abstand_eng_schwelle_relativ` (NEU, 2%)
  liegt - unabhaengig von einer gleichzeitig hohen CRV.
- `post_check_hebel()` berechnet `sl_abstand_relativ` aus den bereits
  vorhandenen `entry_mid`/`stop_von`-Werten (keine neue Berechnung, nur
  zusaetzlich exportiert).

**Verifikation:** synthetischer Test reproduziert alle 9 echten Nacht-Werte
(Retail-Konsens 51-70%, CRV/SL-Kombinationen BTC/XLM) sowie einen echten
End-to-End-Aufruf von `post_check_hebel()` mit einem BTC-aehnlichen
Szenario - alle Ergebnisse decken sich mit der Handanalyse.

## Nachtrag (2026-07-22): Ueberholt-Erkennung repariert - Mindestbeobachtung + Zonen-Reaffirmation (Hebel+Spot)

Ausloeser: Nutzer-Frage nach der ersten inhaltlichen BTC-Signal-Review "so
wie ich es verstehe funktioniert das aktuelle System auf Glueck bzw.
Zufall?" - konkret ausgeloest durch die Beobachtung "es kommen genuegend
LONG-Signale rein, aber es gibt kaum echte Ergebnisse (Take-Profit/
Stop-Loss)".

**Root Cause:** Die Ueberholt-Erkennung (siehe Abschnitt 7, Punkt 6 oben,
2026-07-16/07-19) markierte ein offenes Signal sofort als ueberholt, sobald
IRGENDEINE neuere Nicht-HALTEN-Aktion fuer denselben Schluessel existierte -
unabhaengig vom Alter und unabhaengig davon, ob die neue These inhaltlich
ueberhaupt etwas anderes sagte (z. B. ein erneutes ERÖFFNEN mit praktisch
identischen Entry-/Stop-/Take-Profit-Zonen). Da das SLA-reservierte
Screening (Nachtrag 2026-07-21 oben) Hebel-Kandidaten alle ~3,5-7h und Spot
alle 8-15h neu bewertet - weit unter der Zeit, die eine 10-30% entfernte
Zielzone realistischerweise braucht -, verschwand die grosse Mehrheit der
Signale spurlos als "ueberholt", bevor der Kurs eine faire Chance hatte.
Die "historische Trefferquote" (n=5 fuer Hebel) war dadurch nicht nur
klein, sondern strukturell survivorship-verzerrt.

**Fix - zwei zusaetzliche Gates vor einer Ueberholung** (nur fuer den
"gleiche Richtung/erneute These"-Fall - eine echte Gegenrichtung bei Spot,
VERKAUFEN/TAUSCHEN nach KAUFEN, ueberholt weiterhin SOFORT, unveraendert
seit 2026-07-16):
1. **Mindestbeobachtung:** ein Signal darf erst ueberholt werden, nachdem
   seit seiner Erstellung mindestens eine Mindestzeit vergangen ist -
   abgeleitet aus `halte_kriterium_bucket` (`backward_tracking.
   mindestbeobachtung_tage_bucket`: kurz=2/mittel=5/lang=10 Tage, deutlich
   unter den bestehenden Abgelaufen-Schwellen 14/45/120). Bei Hebel
   zusaetzlich ein praeziserer Override ueber `trade_thesis_typ`:
   `einmal_trade` (kurzlebige Squeeze-Gegenbewegung) nutzt eine kuerzere
   Stunden-Schwelle (`hebel_mindestbeobachtung_stunden_einmal_trade`, 18h)
   statt der Tage-Bucket-Logik.
2. **Zonen-Reaffirmation:** liegen Entry-/Stop-Loss-/Take-Profit-
   Mittelwert des neuen Signals alle innerhalb einer relativen Toleranz
   (`zonen_reaffirmation_toleranz_relativ`, 3%) um die Werte des offenen
   Signals, gilt das als reine Bestaetigung derselben These, keine neue
   Information - keine Ueberholung. Konservativ: fehlt einer der drei
   Werte bei einem der beiden Signale, gilt das NICHT als Reaffirmation.

Beide Gates muessen die Ueberholung ERLAUBEN (Mindestbeobachtung erreicht
UND keine Zonen-Reaffirmation), sonst bleibt das Signal offen. Implementiert
in `agent/krypto/backward_tracking.py`/`hebel_backward_tracking.py::
_is_superseded()`, neue Config-Schluessel unter `backward_tracking:`.

**Backtest VOR Live-Umstellung** (gleicher Standard wie beim
Budget-Allocator-SLA-Fix, Nachtrag 2026-07-21 oben): neues Skript
`backtest_ueberholt_erkennung.py` spielte die beiden neuen Gates gegen ALLE
historisch echt "ueberholten" Hebel-/Spot-Signale nach (Rohdaten aus
`extract_notebook_diagnose.py`, neu ergaenzte Preishistorie-Sektion) -
Ergebnis: **24 von 27 (89%) historisch ueberholten Hebel-Signalen waeren
gerettet worden** (weiter offen geblieben statt zu verschwinden), darunter
mind. 1 Take-Profit- und 3 Stop-Loss-Treffer, die die historische
Trefferquote von n=5 auf n=9 erweitert haetten. Bei Spot (nur 2 historische
Faelle) blieb die echte Gegenrichtung (KAS) korrekt sofort ueberholt, der
zweite Fall (CAT) wurde gerettet. Ein besonders anschauliches Beispiel:
VIRTUAL LONG lief vom 16.07. bis 21.07. (5 Tage) als praktisch dieselbe
These durchgehend weiter, wurde aber unter der alten Regel 8-mal
hintereinander als "ueberholt" markiert.

**Verifikation:** synthetischer Test gegen die ECHTEN Produktivfunktionen
(nicht nur die Backtest-Kopien) reproduziert die zentralen Faelle (BTC-
artig gerettet, VIRTUAL-artig weiterhin ueberholt, KAS `einmal_trade`-
Override, Spot-Gegenrichtung, HALTEN-Regression) sowie ein echter
End-to-End-Lauf von `run_backward_tracking()`/`run_hebel_backward_
tracking()` gegen eine Kopie der Desktop-DB.

## Nachtrag (2026-07-22): Zwei weitere echte Funde aus einem LINK-Hebel-Signal (Antizyklisch-Regelverstoss + Funding-Rate-Rohfloat)

Ausloeser: Nutzer teilte einen echten LINK LONG ERÖFFNEN-Vorschlag (16:09
Uhr, Mistral) zur fachlichen Begutachtung. Zwei zusaetzliche, unabhaengige
Funde neben der eigentlichen inhaltlichen Bewertung (fuenf ▼-Warnsignale
gegen nur ein ▲, u.a. Bear-Forecast 50% > Bull-Forecast 25% trotz LONG-
Empfehlung, Regime-Konflikt, niedrige Konfidenz 50%):

**1. Antizyklisch-Regelverstoss trotz bestehender Regel (Regel 8,
`hebel_analyst.py`):** Top-Grund #5 des Signals lautete "Long-Konten-Anteil
von 63,5% zeigt eine moderate Positionierung, was Raum für eine Erholung
lässt" - als Stuetze fuer die eigene LONG-Empfehlung formuliert, obwohl
63,5% bereits eine (nicht-extreme) Mehrheit IN DERSELBEN Richtung ist. Die
bestehende Regel 8 verbietet das explizit fuer EXTREME Retail-Mehrheiten -
ein frueheres Signal desselben Tages (02:49 Uhr, HALTEN) formulierte
denselben Fakt korrekt neutral ("zeigt keine extreme Positionierung"),
zeigt also, dass die Regel grundsaetzlich befolgt werden KANN, nur nicht
zuverlaessig wird. Fix: Regel 8 um ein konkretes Gegenbeispiel ergaenzt,
das explizit auch den MODERATEN (nicht-extremen), gleichgerichteten Fall
verbietet - "noch nicht extrem, also ist noch Luft nach oben" als
derselbe Fehler nur anders formuliert benannt. Reine Prompt-Verschaerfung
(kein deterministischer Filter moeglich/sinnvoll fuer freien Fliesstext,
anders als bei den folgenden zwei Punkten) - die bereits bestehende
deterministische Retail-Konsens-Bewertung in Abschnitt 3 bleibt die
verlaessliche Quelle, unabhaengig davon, was das LLM im freien Text
formuliert.

**2. Funding-Rate als unformatierter Rohfloat im Risiken-Text:** "Laufende
Finanzierungsgebühr bei längerer Haltedauer, aktuell bei
2.624963888888792e-06." - der rohe Python-Float wurde unformatiert an das
LLM gereicht (`hebel_analyst.py`, `funding_rate_aktuell`) und von diesem
gemaess Regel 9 unveraendert in den Text kopiert. Fix in zwei Teilen:
- `hebel_analyst.py`: der LLM-Fakt heisst jetzt
  `funding_rate_aktuell_prozent_pro_stunde` und ist bereits als gerundeter
  Prozentwert formatiert (z.B. `0.00026` statt `2.624963888888792e-06`) -
  Regel 9 verlangt zusaetzlich explizit die Einheit "% pro Stunde" im Text.
- **Nutzer-Nachfrage:** macht eine reine Prozentzahl ohne Kontext ueberhaupt
  Sinn, oder waere ein EUR/Zeiteinheit-Betrag sinnvoller? Antwort: beides,
  nach demselben "Fakt zuerst, Wertung danach"-Prinzip wie Retail-Konsens/
  CRV - die Rate selbst MIT Zeiteinheit (Kraken veroeffentlicht Funding
  stuendlich, `rates[-24:]` in `hebel_screening.py` = 24h-Durchschnitt der
  Stundenrate) als Fakt, plus ein neuer deterministischer Risikofaktor
  "Funding-Kosten" (`hebel_risk_gate.py::compute_risikofaktoren_hebel()`)
  mit einem konkreten USD/Tag-Betrag bei der TATSAECHLICHEN Positionsgroesse
  (`positionsgroesse_usd * funding_rate_stunde * 24`, aus der bereits
  vorhandenen Positionsgroessen-Berechnung in `post_check_hebel()`) - klar
  benannt als Momentaufnahme ("schwankt mit dem Satz, keine feste
  Kostenzusage"), nicht als LLM-Rechnung (LLMs sind kein verlaesslicher
  Taschenrechner). Neue Schwelle
  `risiko.hebel.funding_rate_hoch_schwelle_relativ_stunde` (0.0001, identisch
  zum bereits kalibrierten `hebel_screening.kontra.funding_rate_extrem_
  schwelle`, aber als eigener Schluessel fuer ein unabhaengiges Konzept)
  faerbt den Faktor ab dieser Rate "negativ" statt "neutral".

**Verifikation:** synthetischer Test bestaetigt: (a) niemals mehr
wissenschaftliche Notation im Text, (b) korrekte USD/Tag-Berechnung fuer
den echten Screenshot-Wert (≈0,13 USD/Tag bei einer Beispiel-Positionsgroesse),
(c) Schwellenwert-Verhalten (neutral/negativ), (d) kein Faktor ohne
vorhandenen Fakt, (e) echter End-to-End-Lauf von `post_check_hebel()` mit
einem LINK-aehnlichen Szenario, (f) Regressionstest der vorherigen Retail-
Konsens-/CRV-Fixes weiterhin gruen.

## Nachtrag (2026-07-22): Alt-Coin-Marktphase fehlte im Hebel-Regelwerk (echter VIRTUAL-Fund)

Ausloeser: ein weiteres echtes Signal (VIRTUAL LONG ERÖFFNEN, Mistral,
15:40 Uhr) zur fachlichen Begutachtung. Gegenargument des LLM nannte
korrekt "Regime (baer_flucht)" als staerksten Einwand - Nachforschung
ergab: `baer_flucht` ist KEIN Wert des einfachen Baer/Bulle-Regimes
(`regime.regime`), sondern ein separates Label der BTC-Dominanz-Matrix
(`agent/krypto/regime.py::BTC_MATRIX`), das explizit dokumentiert "Alt-
Ausbrueche meist Fallen - erhoehte Vorsicht bei Alt-Kaufsignalen". VIRTUAL
ist ein Alt-Coin, also genau der Fall, fuer den diese Warnung gedacht ist.

**Fund:** Die Spot-Pipeline (`analyst.py` Regel 8) kennt diese Regel
bereits seit laengerem UND uebergibt sowohl das Label (`btc_matrix`) als
auch die erklaerende Beschreibung (`btc_matrix_hinweis`) als Fakt. Die
Hebel-Pipeline (`hebel_analyst.py`) uebergab bisher NUR das nackte Label
ohne Erklaerung und hatte KEINE SYSTEM_PROMPT-Regel dazu - das LLM hat den
Zusammenhang diesmal aus eigenem Wissen richtig hergestellt, aber ohne
System-Vorgabe (gleiches Muster wie beim Antizyklisch-Regel-8-Fund: "hat
diesmal zufaellig richtig geraten" ist keine verlaessliche Grundlage,
gerade fuer die risikoreichere Hebel-Pipeline).

**Fix:**
- `hebel_analyst.py`: `asset.rolle` und `btc_matrix_hinweis` (=
  `regime_result.btc_matrix_beschreibung`) neu ins Fakten-JSON aufgenommen
  (identische Feldnamen wie bei Spot). Neue Regel 16 im SYSTEM_PROMPT,
  wortgleich zum Spot-Muster: bei `asset.rolle != "core"` (nicht BTC/ETH)
  UND `richtung == LONG` soll bei `btc_season`/`baer_flucht` erhoehte
  Skepsis gegenueber Alt-Kaufsignalen gelten, bei `altseason` normal/hoeher
  gewichtet werden.
- `hebel_risk_gate.py`: neuer deterministischer Risikofaktor "Alt-Coin-
  Marktphase" (`compute_risikofaktoren_hebel()`) - erscheint nur bei
  `richtung == LONG`, `ist_core_asset == False` und
  `btc_matrix_state in ("btc_season", "baer_flucht")`. Text wird bewusst
  1:1 aus `btc_matrix_hinweis` uebernommen (bereits ein vollstaendiger,
  verstaendlicher Satz aus `regime.py::BTC_MATRIX`) statt neu formuliert -
  eine Quelle der Wahrheit, kein driftender Zweittext, und direkt die vom
  Nutzer gewuenschte "sinnvolle Beschreibung fuer den User" ohne
  zusaetzliche Uebersetzungsarbeit.
- `hebel_pipeline.py`: `asset.rolle` an `post_check_hebel()` durchgereicht;
  `btc_matrix_state`/`btc_matrix_beschreibung` werden dort direkt aus dem
  bereits vorhandenen `regime_result` gelesen (kein zusaetzlicher
  Parameter noetig).

**Verifikation:** synthetischer Test bestaetigt: (a) Faktor erscheint fuer
Alt-Coin+LONG+`baer_flucht`/`btc_season` mit korrektem, unveraendertem
Hinweistext, (b) kein Faktor fuer BTC/ETH (`asset.rolle == "core"`), (c)
kein Faktor fuer SHORT (Regel betrifft nur Alt-Kaufsignale), (d) kein
Faktor bei `altseason`/`unklar_defensiv`/fehlendem Zustand, (e) echter
End-to-End-Lauf von `post_check_hebel()` mit einem VIRTUAL-aehnlichen
Szenario, (f) Regressionstest der Funding-Kosten-/Retail-Konsens-/CRV-Fixes
weiterhin gruen.

## Nachtrag (2026-07-22): Abschnitt 3 (Konklusion) verschmolz in Outlook zu einem Fliesstext

Nutzer-Fund (Screenshot derselben VIRTUAL-E-Mail): die Legende
"(▲ unterstützt die Empfehlung · ● neutral · ▼ Warnsignal/Risiko)" und der
erste Risikofaktor erschienen in Outlook Web als EIN zusammenhaengender
Fliesstext statt als zwei Zeilen - Outlook zeigte dabei den Hinweis "Wir
haben zusätzliche Zeilenumbrüche aus dieser Nachricht entfernt". Root
Cause: `scheduler/background.py::_formatiere_risikofaktoren()` trennte
Risikofaktoren-Zeilen bisher nur mit einfachem `\n`, und auch der Uebergang
Legende -> erster Faktor nutzte nur ein einfaches `\n` - Outlook Web
entfernt offenbar genau solche einzelnen Zeilenumbrueche beim Anzeigen
(vermutlich ein Reflow-Mechanismus, der einzelne "\n" als reinen
Wortumbruch interpretiert). Alle ANDEREN Abschnitte der E-Mail trennen
Bloecke bereits durchgehend mit `\n\n` (echte Leerzeile) und rendern
deshalb zuverlaessig als eigene Absaetze - genau dieses Muster fehlte hier.

**Fix:** `_formatiere_risikofaktoren()` verbindet die einzelnen
Risikofaktor-Zeilen jetzt mit `"\n\n"` statt `"\n"`, und alle drei
Aufrufstellen (Spot-, Hebel-, Multi-Asset-E-Mail) trennen die Legende vom
ersten Faktor ebenfalls mit `"\n\n"` statt `"\n"` - konsistent mit dem
bereits etablierten Absatz-Trenn-Muster der uebrigen E-Mail-Abschnitte.
Rein die E-Mail-Formatierung betroffen - `ui/formatting.py::
format_risikofaktoren_lines()` fuer die App-Anzeige (Tkinter, keine
Reflow-Problematik) blieb unveraendert.

**Verifikation:** synthetischer Test bestaetigt echte Leerzeilen zwischen
allen Risikofaktor-Zeilen sowie zwischen Legende und erstem Faktor;
bestehender Regressionstest der Risikofaktor-Symbole weiterhin gruen.

## Nachtrag (2026-07-22): Zwei Hedge-Funde - Bitpanda-Override im E-Mail-Gate + Batch-Budget-Bewusstsein

Ausloeser: echte Hedge-Signale (DBPK/3QSS, beide NACHKAUFEN im selben Lauf
07:01) aus dem Signale-Tab. Nutzer fragte, warum keine E-Mail dafuer
ankam, und bat um eine fachliche Bewertung der beiden Empfehlungen.

**Fund 1: Bitpanda-Override wurde vom E-Mail-Gate ignoriert.** Erste
(falsche) Vermutung: DBPK/3QSS seien schlicht nicht bei Bitpanda gelistet -
vom Nutzer korrigiert unter Verweis auf einen bereits bestehenden
Mechanismus. Tatsaechlicher Stand (siehe `asset_bitpanda_override`-
Tabellendocstring, 2026-07-20, Commit `1ae800c`): der oeffentliche
`/v3/assets`-Endpunkt deckt Bitpandas "Bitpanda Stocks"-Fractional-ETF/ETC-
Produktlinie nachweislich NICHT vollstaendig ab - echte Bitpanda-App-
Screenshots hatten das damals bewiesen (DBPK/ISOC dort real gehalten,
aktive Kaufen/Verkaufen-Buttons). Deshalb existiert der manuelle
"Bitpanda-Override umschalten"-Button im Watchlist-Tab. Alle 4 Spot-
family-Pipelines (`agent/krypto|aktien|rohstoff|themen_etf/pipeline.py`)
fragen `db.get_bitpanda_gelistet_override()` bereits nach einem negativen
Live-Check ab - `scheduler/background.py::_ist_email_relevantes_asset()`
(das E-Mail-Gate) war die einzige Stelle, die den Override noch NICHT
respektierte, obwohl fuer DBPK/3QSS bereits ein bestaetigter Override-
Eintrag existierte.

**Fix 1:** `_ist_email_relevantes_asset()` bekommt einen optionalen
`conn_factory`-Parameter (Standard `None`, rueckwaertskompatibel) - nach
einem negativen Live-Check wird jetzt zusaetzlich der Override abgefragt,
identisches Muster wie die 4 Pipelines. `conn_factory` wird an allen 3
Aufrufstellen (`_notify_spot_signal()`, `_notify_hebel_signal()` [hatte es
bereits fuer die Wartezeit-Anzeige], `_notify_multi_asset_signal()`)
durchgereicht - beide Jobs (`hebel_screening_job()`, `multi_asset_batch_
job()`) haben `conn_factory` bereits im Scope.

**Fund 2: zwei Hedge-Instrumente im selben Batch-Lauf kannten sich
nicht.** `agent/hedge/pipeline.py::_compute_portfolio_exposure()` liest
`verbleibendes_hedge_budget_usd` unabhaengig aus dem tatsaechlichen
DB-Bestand - da nichts real ausgefuehrt wird (rein advisory), sehen zwei im
selben Lauf verarbeitete Hedge-Kandidaten (hier: 3QSS dann DBPK)
denselben, noch unveraenderten Ausgangsbestand. Setzt der Nutzer beide
Vorschlaege manuell um, kann die tatsaechliche Gesamt-Abdeckung ueber
`ziel_hedge_abdeckung_max_prozent` hinausschiessen, ohne dass eine der
beiden Empfehlungen davon wissen konnte.

**Fix 2 (Nutzer-Entscheidung: strukturelle Loesung statt reinem Hinweis):**
- `_compute_portfolio_exposure()` bekommt einen neuen Parameter
  `bereits_vorgeschlagen_effektiv_usd` (Standard 0.0, kein
  Verhaltensunterschied bei Einzelaufruf) - wird zusaetzlich von der
  aktuellen Hedge-Abdeckung abgezogen, BEVOR das verbleibende Budget durch
  den `hebel_faktor` DIESES Instruments geteilt wird. Der `hinweis`-Text
  erklaert den Abzug explizit, wenn er greift.
- `generate_signal()` reicht den (keyword-only) Parameter
  `bereits_vorgeschlagen_effektiv_usd` durch.
- `agent/multi_asset_batch.py::run_multi_asset_batch()`: neuer lokaler
  Akkumulator `hedge_effektiv_vorgeschlagen_usd` (nur fuer Hedge-Symbole
  relevant, bleibt bei 0.0 fuer Aktien/Rohstoffe/Themen-ETF - kein
  zusaetzliches kwarg fuer diese Pipelines, kein Regressionsrisiko). Nach
  jedem erfolgreichen KAUFEN/NACHKAUFEN-Signal eines Hedge-Instruments wird
  `position_size_usd * hebel_faktor` (leverage-adjustiert) zum Akkumulator
  addiert, bevor der naechste Hedge-Kandidat im selben Lauf verarbeitet
  wird - macht den Deckel ueber den ganzen Batch hinweg real konsistent.

**Verifikation:** synthetischer Test bestaetigt (a) E-Mail-Gate respektiert
den Override jetzt (mit `conn_factory`), bleibt ohne `conn_factory`
rueckwaertskompatibel beim alten (strengeren) Verhalten; (b)
`_compute_portfolio_exposure()` reduziert das verbleibende Budget korrekt
um den uebergebenen Wert, deckelt nie unter 0; (c) echter Integrationstest
von `run_multi_asset_batch()` mit zwei gestubbten Hedge-Signalen bestaetigt,
dass das ZWEITE Instrument im Lauf tatsaechlich die vom ERSTEN vorgeschlagene,
leverage-adjustierte Summe als Ausgangswert erhaelt.

**Fachliche Bewertung der beiden echten Signale (zur Nutzer-Frage):** beide
Empfehlungen entsprechen dem Hedge-Regelwerk (`agent/hedge/analyst.py`) -
korrekte `exposure/makro/risiko/timing`-Kategorien (Regel 10, NICHT die
Spot-Taxonomie), Decay-Warnung explizit genannt (Regel 4), rein
exposure-/regimebasierte Begruendung (Regel 3), `aktien_baermarkt.aktiv`
korrekt als noch nicht aktiv benannt, aber `regime=='baer'` allein reicht
laut der ODER-Verknuepfung in Regel 3. Die fehlenden strukturierten
Risikofaktoren ("Keine strukturierten Risikofaktoren verfügbar") in
Abschnitt 3 sind KEIN Bug, sondern bewusste Architektur (Hedge durchlaeuft
laut Modul-Docstring absichtlich NICHT `risk_gate.pre_check()/post_check()`
- CRV-Pflicht etc. passen nicht auf eine Absicherungsposition).

## Nachtrag (2026-07-23): Ueberholt-Erkennung - erste Live-Verifikation auf dem Notebook

Der 06:00-Cron-Lauf (04:00 UTC) am 07-23 war der erste echte Lauf unter den am
07-22 eingefuehrten Gates (Mindestbeobachtung + Zonen-Reaffirmation, siehe
Nachtrag oben "Ueberholt-Erkennung repariert"). Ausgewertet ueber den
`extract_notebook_diagnose.py`-Export (Rohzeilen `hebel_signals`/
`spot_signals`, gefiltert auf `outcome_geprueft_am` vom 07-23):

- **Hebel:** 172 geprueft -> 162 `nicht_anwendbar`, 4 `stop_loss_erreicht`,
  4 `take_profit_erreicht`, **nur 1x `ueberholt_durch_neuere_analyse`**
  (KAIA LONG vom 07-21 08:38, `trade_thesis_typ=einmal_trade` - mit 43h Alter
  weit ueber der 18h-Schwelle fuer Einmal-Trades, also ein legitimer Fall,
  kein Fehl-Rescue).
- **Spot:** 328 geprueft -> alle 328 `nicht_anwendbar`, **0x ueberholt**.
- Die zuvor identifizierten Sorgenkinder BTC/HYPE/SUI LONG (9-13
  Wiederholungs-Instanzen je Symbol seit 07-22) blieben durchgehend
  `nicht_anwendbar` - keines davon wurde vorzeitig ueberholt.

Im Vergleich zur vorherigen Baseline (Backtest hatte ~89%, 24/27, der
historischen Hebel-Ueberholungen als Fehl-Rescues identifiziert) ist das eine
sehr deutliche Bestaetigung: von geschaetzt ~89% Fehl-Rescues auf 1/172
(0,6%) bei Hebel und 0/328 bei Spot im ersten echten Live-Tag - und die
4+4 echten TP/SL-Treffer zeigen, dass Signale jetzt tatsaechlich bis zu einem
echten Ergebnis ueberleben statt vorzeitig weggewischt zu werden. Kein
Live-Code-Fix noetig, reine Bestaetigung.

**Offener Punkt (nicht behoben, nur dokumentiert):** `BackwardTrackingResult.
superseded` existiert im Code, wird aber in der Log-Zeile von
`backward_tracking_job()`/`hebel_backward_tracking_job()` (`scheduler/
background.py`) nicht mitgeloggt - eine schnelle Log-basierte Pruefung war
deshalb nicht moeglich, die obige Auswertung musste direkt gegen die
Rohzeilen des Diagnose-Exports laufen. Waere ein guenstiger kuenftiger
Zusatz fuer die Log-Zeile selbst, aber kein Bug und nicht Teil dieser Runde.

## Nachtrag (2026-07-23): Staleness-Watchdog - Krypto-Kurshistorie blieb ueber Nacht auf altem Stand, 390 Signale blockiert

**Ausloeser:** Nutzer meldete Fehler im Notebook-Log + fragte nach dem
Backward-Tracking-Job-Takt. Bei der Diagnose ueber
`extract_notebook_diagnose.py` fiel auf: `llm_calls_heute`/
`signal_volumen_heute` standen bei 0/180 fuer ALLE Kategorien, obwohl das Log
"Hebel 12, Spot 23 verarbeitet, 0 fehlgeschlagen" zeigte - "verarbeitet"
zaehlt laut `budget_allocator.py` nur "Pipeline-Aufruf ist nicht
gecrasht", nicht "hat wirklich einen LLM aufgerufen". Filterung der
`hebel_signals`/`spot_signals`-Rohzeilen des Exports auf `created_at` vom
07-23 ergab: **alle 116 Hebel- und alle 274 Spot-Kandidaten** (116+274=390,
darunter auch BTC/ETH) scheiterten von 00:11 bis mind. 04:15 Uhr am
P-10-Gate mit identischem `gate_reason`: `"Historie veraltet (letzter Tag:
2026-07-20)"` - Fixed-HALTEN ohne jeden echten LLM-Call.

**Root Cause (per Log-Timeline zweifelsfrei belegt, KEINE Vermutung):** die
zeitgleiche yfinance-Kaskade um 05:41 Uhr (13 haengende Multi-Asset-Threads,
siehe `YFINANCE_HISTORY_UNRELIABLE_TICKERS`-Doku) war eine falsche Spur -
sie betrifft eine komplett andere Datenquelle/Tabelle und begann erst NACH
dem ersten blockierten Signal (00:11). Die echte Ursache:

- `refresh_history_job()` (CoinGecko-basierte taegliche Krypto-Kurshistorie,
  genau die Quelle hinter `get_last_history_date()`/dem P-10-Gate) lief im
  gesamten sichtbaren 72h-Fenster **genau einmal** erfolgreich durch: 07-20
  08:44:57 ("43/56 Assets aktualisiert").
- Der Job hat einen Nachhol-Mechanismus (`_history_data_is_stale()`), der
  aber bisher **nur einmalig beim App-Start** in `build_scheduler()` prueft
  und bei Bedarf `next_run_time=jetzt` setzt - analog zu
  `_ohlc_data_is_stale()` fuer den Kraken-OHLC-Job.
- Die App wurde zwischen 07-20 und 07-22 ca. 28x neu gestartet (jedes Mal ein
  frisches "Added job..."-Log). Der **letzte Neustart in diesem Fenster war
  07-22 23:26:04** - zu diesem exakten Zeitpunkt lag die Historie erst *2,0*
  Kalendertage zurueck (`is_history_stale()` vergleicht Kalendertage,
  Schwelle `> 2 Tage`), der Start-Check schlug also korrekt "noch nicht
  stale" vor.
- Danach lief die App **durchgehend weiter, ohne weiteren Neustart**, ueber
  Mitternacht hinweg. Um 00:00 Uhr am 07-23 kippte die Historie auf "3 Tage
  alt" - aber der Staleness-Check laeuft NUR beim Start, nie waehrend des
  laufenden Betriebs. Niemand hat das Ueberschreiten der Schwelle bemerkt,
  `refresh_history_job` blieb auf seinen bei 23:26 fest einprogrammierten
  24h-Slot gepinnt.

Das ist ein struktureller, kein transienter Bug: er kann sich jederzeit
wiederholen, wenn ein Neustart zufaellig knapp unter der 2-Tage-Schwelle
landet und die App danach lange genug durchlaeuft (was durch den
Watchdog/Tray-Monitor sogar der Normalfall sein soll).

**Fix:** neuer periodischer Job `staleness_watchdog_job()` (`scheduler/
background.py`), Takt `STALENESS_RECHECK_INTERVAL_MINUTES = 15` (gleicher
Takt wie `refresh_prices`/`hebel_screening`). Wiederholt denselben Check
(`_history_data_is_stale()`/`_ohlc_data_is_stale()`) waehrend des laufenden
Betriebs und loest bei Bedarf ueber `scheduler.modify_job(job_id,
next_run_time=jetzt)` einen sofortigen Nachhol-Lauf von `refresh_history`/
`refresh_ohlc` aus - bewusst KEIN direkter Funktionsaufruf, damit
APScheduler's eigene Lauf-Serialisierung je `job_id` weiterhin greift (kein
Doppel-Lauf-Risiko, falls der reguläre 24h-Takt zufaellig zeitgleich
feuert). Gleiches `modify_job()`-Muster wie der bestehende
Job-Ausfall-Backoff (`_record_job_failure_for_backoff()`).

**Backtest gegen die echte Log-Timeline** (`backtest_staleness_watchdog.py`,
Nutzer-Vorgabe: Backtest vor jeder Live-Aenderung, gleiche Methodik wie beim
Budget-Allocator-SLA-/Ueberholt-Erkennungs-Fix): simuliert, wie viele der 390
real blockierten Signale ein periodischer Watchdog (angesetzt am echten
letzten Neustart-Zeitpunkt 07-22 23:26:04) gerettet haette:

| Watchdog-Takt | Erster Erkennungs-Tick | Gerettete Signale |
|---|---|---|
| 15 Min | 00:11 Uhr | **389 / 390** |
| 30 Min | 00:26 Uhr | 388 / 390 |
| 60 Min | 00:26 Uhr | 388 / 390 |
| 120 Min | 01:26 Uhr | 320 / 390 |

15 Minuten gewaehlt - rettet praktisch alle Signale (nur das allererste um
00:11 waere knapp vor dem ersten Tick noch verpasst worden, da die Historie
exakt um Mitternacht kippt) und passt zum bestehenden Takt anderer haeufiger
Jobs.

**Verifikation:** synthetischer Test (`test_staleness_watchdog.py`)
bestaetigt: (a) beide Jobs stale -> beide ueber `modify_job(next_run_time=
jetzt)` nachgetriggert; (b) nichts stale -> kein Aufruf; (c) nur eine
Quelle stale -> nur der betroffene Job nachgetriggert; (d)
`_scheduler_ref is None` (z.B. in einem Testkontext ohne echten Scheduler)
-> sauberer No-Op, kein Absturz.

## Nachtrag (2026-07-23): E-Mail-Latenz-Fix - Benachrichtigungen hingen 18+ Minuten am Ende des Gesamt-Batches fest

**Ausloeser:** Nutzer sah im Hebel-Tab drei echte ERÖFFNEN-Signale (NEAR
SHORT, SUI LONG, VIRTUAL LONG, alle kurz nach dem Neustart 06:57 Uhr
erzeugt), aber keine einzige E-Mail kam an. Diagnose per
`extract_notebook_diagnose.py` (zwei Exporte im Abstand von 16 Minuten,
Nutzer-Korrektur: kein Ad-hoc-SQL, sondern der etablierte Diagnose-Prozess).

**Root Cause (per Log-Timeline zweifelsfrei belegt):** In `scheduler/
background.py::hebel_screening_job()` lief das bisher so ab:
```python
allocation = run_budget_allocator(...)   # EIN blockierender Aufruf fuer ALLE Kandidaten
logger.info("Budget-Allocator: ...")     # erst NACH vollstaendigem Abschluss
for schluessel, ergebnis in allocation.ergebnis_objekt.items():
    _notify_hebel_signal(...)            # E-Mail-Versand erst HIER, fuer den GANZEN Batch
```
Die Benachrichtigungs-E-Mails wurden also erst verschickt, wenn der
komplette Batch (an diesem Tag: 12 Hebel- + 26 Spot-Kandidaten = 38) fertig
durchgelaufen war - nicht einzeln, sobald ein Signal feststand. Dieser
Batch brauchte ungewoehnlich lange, weil mehrere externe Abrufe haengen/
timeouten (Eastmoney China-M2/PBoC-LPR mit 15s-Timeout, wiederholte
OKX-Open-Interest-Fehlschlaege) - jeder einzelne davon summiert sich
sequenziell auf. Log-Beleg: der naechste planmaessige 15-Min-Takt (07:12:01)
musste uebersprungen werden ("maximum number of running instances reached
(1)"), der Batch lief laut zweitem Export noch bei 07:16:38 - ueber 18
Minuten nach Start, ohne Ende in Sicht.

NEAR (fertig 06:58:19), SUI (07:02:52) und VIRTUAL (07:04:56) standen damit
zwar laengst in DB und GUI, ihre E-Mails hingen aber fest, bis der GANZE
Batch durch ist - ein strukturelles Problem, kein Zufall: es kann sich
wiederholen, sobald irgendein externer Abruf im Batch haengt.

**Fix:** `run_budget_allocator()` (`agent/krypto/budget_allocator.py`)
bekommt einen neuen optionalen Parameter `on_signal_ready(schluessel,
ergebnis)`, der DIREKT in `_mit_fallback_chain()` aufgerufen wird - im
selben Moment, in dem `result.ergebnis_objekt[schluessel] = res` gesetzt
wird, nicht erst nachdem die gesamte Funktion zurueckkehrt. Ein Fehler im
Callback selbst darf die Allocator-Schleife nicht stoppen (P-10, eigenes
try/except mit Logging).

`scheduler/background.py::hebel_screening_job()` baut die Benachrichtigungs-
Logik jetzt VOR dem `run_budget_allocator()`-Aufruf als Closure
(`_on_signal_ready()`) und reicht sie als `on_signal_ready` durch - der
alte Nachlauf (`for schluessel, ergebnis in allocation.ergebnis_objekt.
items(): ...`) entfaellt komplett, sonst wuerde doppelt gemailt. Der
Bitpanda-Listing-Abruf (`get_listed_assets()`) bleibt bewusst LAZY beim
ERSTEN echten Signal dieses Laufs (nicht vorab unbedingt) und wird
innerhalb des Laufs zwischengespeichert - identisches Verhalten wie vorher
(kein API-Call bei einem Zyklus ohne echtes Signal), nur zeitlich
vorgezogen statt an den Batch-Abschluss gekoppelt.

**Backtest gegen den echten Vorfall:** mit den echten Zeitstempeln von
heute (Batch-Start 06:57:50, Log lief zum Export-Zeitpunkt 07:16:38 noch
ohne Abschluss):

| Signal | Fertig um | ALT (gebuendelt) | NEU (sofort) |
|---|---|---|---|
| NEAR SHORT | 06:58:19 | mind. 18,3 Min Wartezeit | ~0 Min |
| SUI LONG | 07:02:52 | mind. 13,8 Min Wartezeit | ~0 Min |
| VIRTUAL LONG | 07:04:56 | mind. 11,7 Min Wartezeit | ~0 Min |

Die "ALT"-Werte sind Untergrenzen (der Batch war zum Exportzeitpunkt
immer noch nicht fertig) - der tatsaechliche alte Verzug waere je nach
Batch-Laufzeit noch groesser gewesen.

**Verifikation:** `test_email_latenz_fix.py` bestaetigt (a) `on_signal_
ready()` feuert SOFORT nach dem LLM-Call, nicht erst am Ende des Batches
(Aufrufreihenfolge protokolliert); (b) `on_signal_ready=None` (Default)
bleibt rueckwaertskompatibel, `ergebnis_objekt` weiterhin befuellt; (c)
eine Exception im Callback selbst stoppt die Signal-Verarbeitung nicht
(P-10) - der Kandidat wird trotzdem korrekt in `ergebnis_objekt`/
`hebel_verarbeitet` gefuehrt.

## Nachtrag (2026-07-23): Watchlist-Aenderungen wirkten nur nach App-Neustart - in 3 Phasen behoben

**Ausloeser:** Nutzer fuegte XNO (echter Marktscan-Kaufkandidat, echter Kauf
umgesetzt) ueber "In Watchlist uebernehmen" hinzu und stellte fest, dass ein
App-Neustart noetig war, damit der neue Eintrag irgendwo wirkt - Nutzer-
Einschaetzung: das sollte auch ohne Neustart moeglich sein. Vollstaendige
Analyse ergab: **kein neuer Bug, sondern eine seit 2026-07-16 bewusst
dokumentierte, aber nie hinterfragte Einschraenkung** (`ui/app.py::
_on_watchlist_changed()` warnte davor explizit).

**Root Cause (identisch an 3 Stellen, ein einziger Ursprung):**
`main.py:186` laedt `watchlist = config.get_watchlist()` EINMALIG beim
App-Start. Diese eine Variable wird an drei Subsysteme weitergereicht, die
sie NIE wieder aktualisieren:
1. **Scheduler-Jobs** (`build_scheduler(watchlist_provider=lambda:
   watchlist)` - die Lambda liefert immer denselben eingefrorenen Wert,
   egal wie oft sie aufgerufen wird, UND `watchlist_provider()` selbst
   wurde in `build_scheduler()` nur einmal aufgerufen, das Ergebnis dann an
   alle 10 Jobs als fixer Parameter durchgereicht).
2. **Haupt-GUI** (`ui/app.py::TradingInfoToolApp.__init__(): self.
   _watchlist = watchlist` - alle 5 Tabs lesen dieselbe, nie aktualisierte
   Liste).
3. **Remote-Steuer-Seite** (`remote/server.py::create_app()` - `watchlist`
   als Flask-Closure erfasst, nie erneut abgefragt).

`config.get_watchlist()` selbst liest bei JEDEM Aufruf frisch aus
`config.yaml` (kein Caching) - das Problem lag ausschliesslich darin, WANN/
WIE OFT diese Funktion aufgerufen wurde, nicht in ihr selbst.

**Nutzer-Vorgabe vor der Umsetzung:** "genau analysieren und bewerten...
bitte auch fuer zukuenftige Aenderungen unser Standardschema inkl. Doku
verfolgen bevor wir umsetzen" - vollstaendige Bestandsaufnahme aller 3
betroffenen Stellen VOR jeder Code-Aenderung, dann Umsetzung in 3 klar
abgegrenzten, einzeln verifizierten Phasen.

### Phase 1: Scheduler-Jobs (`scheduler/background.py`, `main.py`)

Alle 10 Job-Funktionen (`refresh_prices_job`, `refresh_securities_prices_
job`, `refresh_history_job`, `refresh_ohlc_job`, `refresh_aktien_ohlc_job`,
`marktscan_job`, `backward_tracking_job`, `staleness_watchdog_job`,
`hebel_screening_job`, `multi_asset_batch_job`) bekommen statt des
Parameters `watchlist` den Parameter `watchlist_provider` (Callable) - als
allererste Zeile jeder Funktion `watchlist = watchlist_provider()`, Rest
der Funktion unveraendert. `build_scheduler()`s `scheduler.add_job(...)`-
Aufrufe reichen `watchlist_provider` statt der eingefrorenen Liste durch.
`main.py` uebergibt `config.get_watchlist` DIREKT (echte Funktionsreferenz)
statt `lambda: watchlist`.

### Phase 2: Haupt-GUI (`ui/app.py`)

`_refresh_watchlist_from_db()` (laeuft bereits alle 3 Sek. per
`_poll_prices()`) aktualisiert `self._watchlist` jetzt IN-PLACE
(`self._watchlist[:] = config_module.get_watchlist()`, nicht
Neuzuweisung) - dieselbe Listeninstanz bleibt bestehen, alle 5 Tabs (die
sie referenzieren) sehen die Aenderung automatisch mit, ohne selbst
angepasst werden zu muessen. Nutzt die bestehende, bereits bewaehrte
Sortierungs-/Auswahl-Erhaltung (Task #139) unveraendert weiter - kein
Eingriff in diese Logik noetig.

`_on_watchlist_changed()`-Meldung entsprechend aktualisiert: kein "Neustart
noetig" mehr, sondern "Anzeige aktualisiert sich automatisch, Signale/
Cooldown beim naechsten Job-Takt".

**Echter Fund waehrend der Verifikation:** `_manual_refresh()` (manueller
"Preis-Refresh"-Button) rief `refresh_prices_job()` bisher DIREKT mit der
rohen `self._watchlist`-Liste auf - nach der Phase-1-Signaturaenderung
haette das mit `TypeError: 'list' object is not callable` gecrasht. Auf
`lambda: self._watchlist` umgestellt.

### Phase 3: Remote-Steuer-Seite (`remote/server.py`, `main.py`)

`create_app()` bekommt `watchlist_provider` statt `watchlist`. `/api/
status` ruft `watchlist_provider()` bei jedem Request frisch auf.

**Zweiter echter Fund waehrend der Analyse:** `/api/refresh-prices` und
`/api/marktscan` riefen `refresh_prices_job()`/`refresh_securities_prices_
job()`/`marktscan_job()` ebenfalls DIREKT auf (nicht nur ueber den
Scheduler) - beide Routen mussten ebenfalls auf `watchlist_provider`
umgestellt werden, sonst waeren die manuellen Remote-Buttons durch die
Phase-1-Signaturaenderung gebrochen.

### Verifikation (3 separate Testdateien, wie vom Nutzer verlangt "moeglichst gut testen")

- **Phase 1** (`test_watchlist_live_reload_scheduler.py`): strukturelle
  Pruefung aller 10 Signaturen; funktionale Probe (`refresh_prices_job`
  sieht eine zwischen zwei Laeufen geaenderte Watchlist ohne Neustart);
  `main.py` uebergibt die echte Funktionsreferenz.
- **Phase 2** (`test_watchlist_live_reload_gui.py`, echter Tk-Smoke-Test
  mit realer `TradingInfoToolApp`-Instanz): Ausgangszustand korrekt;
  XNO erscheint nach simulierter Watchlist-Aenderung OHNE Neustart;
  **Zeilenauswahl bleibt ueber den Refresh hinweg erhalten** (Task #139
  nicht gebrochen); `self._watchlist` bleibt dieselbe Listeninstanz
  (in-place, keine Neuzuweisung); wiederholter Refresh bleibt stabil.
- **Phase 3** (`test_watchlist_live_reload_remote.py`, echte Flask-Test-
  Client-Requests): `/api/status` ruft `watchlist_provider()` pro Request
  frisch auf; sieht eine Aenderung sofort; `/api/refresh-prices` reicht
  das Callable korrekt an beide Preis-Jobs durch (Regressionscheck fuer
  den zweiten Fund).
- **Zusaetzliche Regressionsprobe** fuer den ersten Fund (`_manual_
  refresh()`): echte `TradingInfoToolApp`-Instanz, bestaetigt dass der
  manuelle Preis-Button ein gueltiges Callable uebergibt statt der jetzt
  inkompatiblen rohen Liste.

Insgesamt 4 Testdateien, alle grün, inklusive zweier echter, sonst erst im
Betrieb aufgefallener Regressionen (manueller GUI-Preis-Button, beide
manuellen Remote-Buttons).

## Nachtrag (2026-07-23): Liquiditätszonen (Marketmaker-Konzept), Stufe 1

Umsetzung des seit 2026-07-21 offenen Punkts "Marketmaker-Trading" (siehe
Task-Backlog): Kurse laufen oft gezielt zu Punkten, an denen viele Stop-
Loss-/Pending-Orders clustern (typischerweise an markanten Swing-Hochs/
-Tiefs = "Liquidity Pools"), holen dort die Liquidität ab ("Stop-Hunt"/
"Liquidity Sweep") und drehen erst danach in die eigentliche Richtung.

**Scope-Entscheidung (Nutzer-Rückfrage):** Krypto Spot + Hebel only (24/7-
Markt + hoher Retail-/Hebel-Anteil, klassische Marketmaker-Dynamik-
Annahme) - nicht für Aktien/Rohstoffe/Hedge/Themen-ETF verdrahtet. Stufe 1
= nur Liquidity Pools (Swing-Hoch/-Tief-Cluster), bewusst **rein
Transparenz/Kontext, kein aktiver Deckel** - kein automatisches Verschieben
von Entry/CRV/Hebel basierend auf Zonen. Order Blocks/Fair Value Gaps
(Stufe 2) bewusst noch nicht gebaut. Was bewusst NICHT abgedeckt ist (nicht
kostenfrei verfügbar): echte Order-Book-Tiefe (Bitpanda hat keine
öffentliche API dafür), Liquidations-Heatmaps (kostenpflichtig).

**Architektur** (folgt dem bestehenden Fibonacci/Support-Resistance-
Muster):
1. `indicators/calculations.py::liquidity_pools()` - neue Berechnungs-
   funktion, analog `support_resistance_levels()`, aber Swing-Highs (Buy-
   Side, oberhalb) und Swing-Lows (Sell-Side, unterhalb) GETRENNT NACH
   RICHTUNG geclustert (0,5% Toleranz statt der 2% bei Support/Resistance -
   Stop-Cluster liegen praeziser um exakte Swing-Extrema) + "bereits
   gefegt"-Erkennung (Kurs hat die Zone nach ihrer letzten Beruehrung
   mind. einmal durchbrochen). Neues `TechnicalSnapshot.liquidity_zones`-
   Feld, in `build_technical_snapshot()` berechnet - wiederverwendet exakt
   den bereits vorhandenen `swing`-Wert (keine doppelte Swing-Erkennung),
   nutzt bei echten Kraken-OHLC-Daten die passende Datumsreihe (`ohlc_dates`/
   `ohlc_closes`), sonst die Proxy-Reihe (`dates`/`closes`) - eine reine
   Mischung beider Serien haette die 'bereits gefegt'-Datumsvergleiche
   verfälscht.
2. `agent/krypto/liquidity_zones.py::liquiditaetszonen_fakt()` (neu) -
   Interpretations-Layer: findet die naechste Buy-/Sell-Side-Zone relativ
   zum aktuellen Kurs (gefiltert nach `min_beruehrungen`), meldet
   `in_naehe_ungefegter_zone` + `seite`, wenn der Kurs innerhalb der
   `naehe_warnschwelle_relativ` einer noch nicht durchbrochenen Zone liegt.
3. Facts-Integration: neuer `liquiditaetszonen`-Fakt in `build_facts()`
   (Spot) und `build_hebel_facts()` (Hebel), neue SYSTEM_PROMPT-Regel in
   beiden Analysten (Regel 25 Spot / Regel 17 Hebel) - beschreibt den Fakt
   als reinen TIMING-Hinweis, verbietet dem Modell ausdrücklich, Entry-/
   Stop-Loss-/Take-Profit-Zonen allein deswegen zu verschieben.
4. Pipeline-Verdrahtung: `agent/krypto/pipeline.py::generate_signal()` und
   `agent/krypto/hebel_pipeline.py::generate_hebel_signal()` berechnen den
   Fakt vor dem jeweiligen `build_*_facts()`-Aufruf und reichen ihn
   zusätzlich an `post_check()`/`post_check_hebel()` durch.
5. Neuer deterministischer Risikofaktor (Abschnitt 3, gleiches Muster wie
   Retail-Konsens/Funding-Kosten): `hebel_risk_gate.py::
   compute_risikofaktoren_hebel()` und `risk_gate.py::compute_risikofaktoren()`
   fügen bei `in_naehe_ungefegter_zone=True` einen Faktor "Nähe zu
   Liquiditätszone (buyside/sellside)" hinzu - bewusst IMMER `neutral`
   (nie negativ), da das Konzept nicht "schlecht" bedeutet, sondern reine
   Timing-Vorsicht. `risk_gate.py`s Version bekommt den Parameter nur von
   der Krypto-Spot-Pipeline gereicht - Aktien/Rohstoffe/Themen-ETF lassen
   ihn auf `None` (Default), der Block wird dort automatisch übersprungen,
   ohne dass die 4 Pipelines selbst geändert werden mussten.
6. `Basisinfos/config.yaml`, neue Sektion `liquiditaetszonen:` (`aktiv`,
   `min_beruehrungen: 2`, `naehe_warnschwelle_relativ: 0.01`).

**Verifikation:**
- Synthetisch: `liquidity_pools()`-Clustering + "bereits gefegt"-Erkennung
  mit konstruierten Swing-Punkten; `liquiditaetszonen_fakt()` inkl. Naehe-
  Warnung nur für ungefegte Zonen, `min_beruehrungen`-Filter, `aktiv=false`-
  Abschaltung; beide `compute_risikofaktoren*()`-Funktionen erzeugen den
  neuen Faktor korrekt (immer neutral) bzw. lassen ihn bei `None`/HALTEN
  korrekt weg (Regressionscheck).
- Echter Lauf gegen eine Kopie der Produktions-DB (BTC + ETH, echte Kraken-
  OHLC-Historie): plausible Zonen-Anzahl (BTC 49 Buy-/57 Sell-Side-Zonen,
  ETH 57/63), Naehe-/Sweep-Logik verhielt sich korrekt (naechste BTC-Buy-
  Side-Zone war bereits gefegt, daher keine Naehe-Warnung trotz 0,59%
  Abstand - die weiter entfernte, noch ungefegte Sell-Side-Zone lag mit
  2,88% über der 1%-Schwelle).
- Regressionscheck: `support_resistance_levels()`/`ui/charts.py` bleiben
  unverändert nutzbar (eigene neue Funktion, kein Umbau der bestehenden);
  alle 4 Aktien/Rohstoffe/Hedge/Themen-ETF-Pipelines importieren weiterhin
  fehlerfrei (das neue `liquiditaetszonen`-Kwarg in `post_check()`/
  `compute_risikofaktoren()` ist optional mit Default `None`).

Noch offen (bewusst nicht Teil dieser Runde): Stufe 2 (Order Blocks/Fair
Value Gaps), Backtest der Naehe-Warnung gegen echte Signal-Ausgänge (erst
sinnvoll mit ausreichend Live-Daten).

## Nachtrag (2026-07-23): Liquidationspreis/Eigenkapitalbedarf zusätzlich in EUR (Hebel-Signal-Detail-Panel)

Nutzer-Fund am Signal-Detail-Panel (Screenshot "1. MATHEMATISCH BERECHNET"):
Entry/Stop-Loss/Take-Profit werden in EUR angezeigt, Liquidationspreis und
Eigenkapitalbedarf standen direkt darunter nur in USD - erzwang eine stille
Kopfrechnung, um z.B. zu prüfen, ob die Liquidation unter dem (EUR-)Stop-Loss
liegt. Bereits für offene Positionen (`HebelPosition.liquidationspreis_
geschaetzt_eur`) war EUR bewusst gewählt worden (Bitpanda-Margin-Trades sind
EUR-denominiert) - für Signale fehlte dieselbe Konsequenz.

**Fix:** `HebelSignal` bekommt zwei neue, additive Felder
(`liquidationspreis_geschaetzt_eur`, `eigenkapitalbedarf_eur`, additive
DB-Migration `_migrate_hebel_signal_eur_columns()`, gleiches Muster wie alle
vorherigen additiven Migrationen dieser Tabelle). `agent/krypto/hebel_
pipeline.py::generate_hebel_signal()` leitet `eur_usd_fx_rate` kostenlos aus
dem EURCV-Preis-Snapshot ab (`eurcv.price_usd / eurcv.price_eur`, exakt
dasselbe Muster wie `risk_gate.py::pre_check()` für den Spot-Cash-Reserve-
Vergleich - kein neuer API-Call nötig) und reicht ihn an `hebel_risk_gate.py
::post_check_hebel()` durch, das die bereits deterministisch berechneten
USD-Werte einfach durch den Kurs teilt. Fehlt der EURCV-Snapshot einmal
(P-10), bleiben die EUR-Felder `None` statt eines falschen 1:1-Werts.
`ui/hebel_view.py` (Detail-Panel) und `scheduler/background.py`
(E-Mail-Template) zeigen den EUR-Wert jetzt in Klammern hinter dem
bestehenden USD-Wert.

**Verifikation:** synthetisch (`post_check_hebel()` mit/ohne `eur_usd_fx_rate`,
korrekte Umrechnung + Regressionscheck ohne Kurs), DB-Migration + Insert/
Read-Roundtrip gegen `:memory:`-DB, Migration zusätzlich gegen eine Kopie
der echten Produktions-DB (bestehende Zeilen bleiben unverändert lesbar, neue
Spalten `NULL`), Textbaustein-Logik für beide UI-/E-Mail-Stellen.

## Nachtrag (2026-07-23): Liquiditätszonen-Grafik in App-Detail-Panel UND E-Mail

Nutzer-Wunsch nach dem ersten Textbeispiel des Liquiditätszonen-Risikofaktors:
"Berührungen"/Datum ohne Erklärung waren nicht selbsterklärend, zusätzlich
sollte eine kleine Grafik mit konkreten Zahlen/Einheiten sowohl in der App
als auch in der E-Mail erscheinen (bisher waren E-Mails reiner Text, keine
Bilder).

**Ein gemeinsamer Renderer für beide Stellen** (`ui/liquidity_chart.py::
render_liquiditaetszonen_chart()`) - nutzt `matplotlib.figure.Figure` direkt
(wie `ui/charts.py`, nicht `pyplot`) und ist damit sowohl aus dem Tk-Main-
Thread (App) als auch aus einem Scheduler-Hintergrund-Thread (E-Mail-Versand)
sicher aufrufbar. Baut aus demselben `liquiditaetszonen`-Fakt (bereits in
`facts_json` gespeichert) ein kompaktes PNG (~560×260px) mit dem aktuellen
Kurs und der nächsten Buy-/Sell-Side-Zone, inkl. Preis+Einheit, Abstand in %,
Anzahl Berührungen und Datum der letzten Berührung DIREKT als Text im Bild -
kein reines Linienbild ohne Kontext. Farb-/Stilkonvention: blau gestrichelt
= aktive Buy-Side-Zone, orange durchgezogen = aktive Sell-Side-Zone, blass-
grau gepunktet = bereits gefegte Zone (deckt sich mit dem zuvor mit dem
Nutzer abgestimmten SVG-Mockup). `None`, wenn keine der beiden Zonen
vorhanden ist (nichts Sinnvolles darzustellen).

**E-Mail:** `api/email_notify.py::send_notification_email()` bekommt einen
neuen optionalen Parameter `inline_image_png` - `None` (Default) belässt
JEDEN bestehenden Aufrufer (Job-Ausfall-/Cash-Veto-Mails etc.) unverändert
bei einer reinen `text/plain`-Mail (kein Regressionsrisiko). Ist ein PNG
übergeben, wird eine `multipart/related`-Mail gebaut: `multipart/alternative`
mit Text- UND HTML-Variante (Fallback für Clients ohne Bilder) plus das PNG
als eingebettetes Inline-Bild (Content-ID, kein Anhang). `scheduler/
background.py::_notify_hebel_signal()` liest den Fakt aus `signal.
facts_json`, holt den aktuellen EUR-Preis frisch aus der DB und übergibt das
gerenderte PNG.

**App:** `ui/hebel_view.py::_render_signal()` bettet dieselbe Grafik direkt
im `tk.Text`-Detail-Panel ein (`image_create()`), die `tk.PhotoImage`-
Referenz wird auf `self._detail_chart_image` gehalten (ohne diese Referenz
gibt Tk das Bild sofort wieder frei - bekannte Tkinter-Falle).

**Verifikation:** Chart-Renderer visuell geprüft (mehrere Beispiel-PNGs,
inkl. Buy-Side+Sell-Side gleichzeitig, nur Sell-Side, gefegt vs. ungefegt);
E-Mail-MIME-Struktur synthetisch geprüft (multipart/related mit beiden
Alternativen + korrekt referenziertem Content-ID, UND Regressionscheck dass
der bestehende reine Text-Pfad ohne Bild unverändert bleibt); echter
Tk-Smoke-Test (reale `HebelView`-Instanz, reale SQLite-DB) bestätigt die
Einbettung im Detail-Panel inkl. Regressionscheck für ein Signal ohne
Liquiditätszonen-Fakt (keine Grafik, kein Crash); Scheduler-Glue-Logik
(facts_json → aktueller Preis → Renderer) isoliert nachgestellt und
verifiziert.

## Nachtrag (2026-07-23): Hervorhebung in den Signal-Detail-Panels (Hebel/Spot-Familie/Marktscan)

**Nutzer-Fund:** "Text und GUI ist alles schwarz weiss" — die drei
Signal-Detail-Panels (`ui/hebel_view.py`, `ui/signals_view.py`,
`ui/marktscan_view.py`) übergaben ihre komplette Zeilen-Liste bisher als
einen einzigen unformatierten Textblock an `tk.Text`, ohne jede
Hervorhebung von Abschnitts-Überschriften, Unter-Überschriften, Warnungen
oder den ▲/●/▼-Risikofaktor-Markern.

**Lösung:** neues gemeinsames Modul `ui/detail_panel.py` — erkennt bekannte
Zeilenmuster rein per Text-Pattern (keine Änderung an den drei
Zeilen-Bau-Funktionen selbst nötig):
- Abschnitts-Kopfzeilen (`--- 1. ... ---` etc.): fett, größer, neue
  Akzentfarbe `theme.header_color()` (Light `#0056b3`, Dark `#5b9bd5`,
  eigener Palette-Eintrag, absichtlich nicht `select_bg` wiederverwendet,
  das fuer Auswahl-Hintergruende reserviert bleiben soll).
- Unter-Überschriften (z. B. "Top 5 Gründe:", "Halte-Kriterium:",
  "MARKTDATEN", "EINSTUFUNG: KAUFKANDIDAT"): fett, normale Textfarbe.
- Warnzeilen (`⚠ ...`): fett + `theme.danger_color()`.
- Risikofaktor-Zeilen (▲/●/▼, aus `ui/formatting.py::
  format_risikofaktoren_lines()`): eingefärbt mit denselben
  success/info/danger-Farben, die im übrigen Programm bereits fuer
  positiv/neutral/negativ-Marker verwendet werden (Konsistenz mit
  Portfolio-/Screener-Ansicht).

Die Liquiditätszonen-Grafik (siehe Abschnitt oben) bleibt davon unberührt —
sie ist ein eigenständiges, bereits vollfarbiges PNG (matplotlib), komplett
unabhängig vom Text-Hervorhebungssystem.

**Verifikation:** Klassifikations-Heuristik pur an 17 synthetischen
Testzeilen geprüft (alle bekannten Muster aus allen drei Dateien plus
Negativ-Fälle wie eingerückte Detailzeilen); echter Tk-Smoke-Test mit einer
realen `HebelView`-Instanz (reale SQLite-DB, reales Signal mit 3
Risikofaktoren) bestätigt korrekte Tag-Zuordnung UND korrekte Farbe/Fett-
Schrift der Section-Header-Tags; Konstruktions-Smoke-Test für
`SignalsView`/`MarktscanView` mit leerer Watchlist bestätigt, dass die
Verdrahtung (Import + `configure_tags()`-Aufruf + `_set_detail_text()`-

## Nachtrag (2026-07-23): E-Mail bekam keine Hervorhebung + Liquiditätszonen-Grafik in echten Clients kaum lesbar

**Zwei echte Nutzer-Funde anhand eines echten Screenshots (NEAR-SHORT-Mail):**

1. **E-Mail-Text ohne jede Hervorhebung.** Die Hervorhebung oben betraf nur
   das App-Detail-Panel (`tk.Text`-Tags) - die E-Mail (`api/email_notify.py`)
   baute weiterhin einen reinen, unformatierten `<pre>`-Block. Fix: die
   Zeilen-Klassifikation (`_classify()`) wurde aus `ui/detail_panel.py`
   (Tk-abhängig) nach `ui/formatting.py` (Tk-frei) verschoben und in
   `classify_detail_line()` umbenannt - jetzt von BEIDEN Stellen nutzbar,
   ohne dass der Scheduler/E-Mail-Pfad tkinter importieren muss. Neue
   Funktion `render_detail_html()` (ebenfalls in `ui/formatting.py`) baut
   aus demselben Text ein `<pre>`-HTML-Fragment mit Inline-Styles (feste
   Light-Mode-Farben, unabhängig vom App-Dark-Mode) - `send_notification_email()`
   nutzt das jetzt statt des rohen Escape-Wraps.
2. **Gmails automatische Dark-Mode-Invertierung** griff sowohl den
   eingebetteten Chart als auch den (damals noch unformatierten) Text an -
   ein fast-weisses Diagramm mit dezenten Grautönen wurde dadurch praktisch
   unlesbar (nur der dunkelste Text blieb nach der Invertierung sichtbar).
   Fix: `<meta name="color-scheme" content="light">` +
   `<meta name="supported-color-schemes" content="light">` im `<head>` der
   HTML-Mail erzwingen für DIESE Mail immer Light-Mode-Darstellung
   (unterdrückt die automatische Invertierung komplett); das `<img>` bekommt
   zusätzlich einen expliziten weissen Hintergrund + Rahmen (verhindert ein
   nahtloses Verschmelzen mit dunklem Mail-Chrome, verbessert die
   Sichtbarkeit unabhängig vom Invertierungs-Fix).
3. **Chart-Hintergrund war implizit, nicht explizit weiss.** `ui/liquidity_chart.py`
   erzeugte die `Figure`/`Axes` ohne explizites `facecolor` - anfällig für
   jeden ambienten matplotlib-rcParams-Zustand des aufrufenden Prozesses
   (Notebook-Scheduler-Thread vs. App-Hauptthread). Fix: `facecolor="white"`
   jetzt explizit auf beiden gesetzt, unabhängig von jedem globalen Zustand.
4. **Kontrast der "bereits gefegt"-Zonenlinien zu schwach fürs echte Rendering.**
   `_FARBE_GEFEGT` war `#9a9a95` (Kontrast nur ~2,7:1 auf Weiss) mit dünner
   gepunkteter Linie (1.6px) - in einer isolierten PNG-Ansicht noch gerade
   erkennbar, in echten Browsern/E-Mail-Clients (Skalierung, Rendering)
   praktisch unsichtbar ("wirkt wie eine Grafik ohne Linien", echtes
   Nutzer-Zitat). Fix: Farbe auf `#6e6e69` nachgedunkelt (WCAG-AA-Kontrast
   ~4,6:1) und Strichbreite fuer gepunktete (gefegte) Linien auf 2.2px erhöht
   (gepunktete Muster tragen pro Längeneinheit weniger sichtbare "Tinte" als
   durchgezogene/gestrichelte bei gleicher Breite).

**Verifikation:** Vollständige Regressionssuite erneut gelaufen (Klassifikations-
Heuristik, echter Tk-Smoke-Test HebelView, Konstruktions-Smoke-Test
SignalsView/MarktscanView, E-Mail-MIME-Test) - alle bestanden. Chart visuell
vor/nach dem Kontrast-Fix verglichen (deutlich sichtbarer Unterschied bei
gleicher "gefegt"-Zonenkonstellation wie im echten Nutzer-Screenshot).
HTML-E-Mail-Fragment mit echtem Signal-Text erzeugt und auf vorhandene
Meta-Tags + korrekte Eskapierung geprüft.

Verdrahtung 3 (App-Dark-Mode-Unabhängigkeit der E-Mail-Farben) ist bewusst so
gewählt, dass ein Umschalten des App-Themes (Light/Dark) die E-Mail-Optik nie
beeinflusst - E-Mail-Clients haben ihr eigenes, unabhängiges Farbschema-Konzept.

## Nachtrag (2026-07-23): echte Kursverlauf-Linie in der Liquiditätszonen-Grafik

**Nutzer-Klarstellung** (nach den obigen Kontrast-Fixes, per hand-gezeichnetem
Beispiel): die Grafik zeigte bisher nur die beiden Zonen-Referenzlinien + die
Kurslinie als drei flache horizontale Striche - der Nutzer wollte den
tatsächlichen historischen Kursverlauf als echte Chart-Linie sehen, wie in
einem normalen Trading-Chart.

**Umsetzung** (single-source-of-truth, kein zusätzlicher Netzwerk-Call):
- `agent/krypto/liquidity_zones.py::liquiditaetszonen_fakt()` bekommt zwei
  neue optionale Parameter `dates`/`closes` - dieselbe Preisreihe, die der
  Aufrufer ohnehin schon an `build_technical_snapshot()` übergeben hat (in
  `hebel_pipeline.py`/`pipeline.py` bereits im Scope). Bettet ein Trailing-
  Fenster (max. 90 Punkte, `_KURSVERLAUF_MAX_PUNKTE`) als
  `"kursverlauf": [{"datum": ..., "preis": ...}, ...]` direkt in den Fakt
  ein - landet damit automatisch in `facts_json` und ist später (App-Anzeige,
  E-Mail-Versand) ohne erneuten API-Call verfügbar.
- `ui/liquidity_chart.py::render_liquiditaetszonen_chart()`: wenn
  `kursverlauf` mit ≥2 Punkten vorhanden ist, läuft der x-Achsen-Bereich über
  die echte Punktzahl (statt des alten schematischen 0-10-Platzhalters) und
  alle Referenzlinien (Zonen + aktueller Kurs) laufen über die VOLLE Breite
  (Achsen-Bruchteil `xmax=1.0` statt `0.5`) - die tatsächliche Kursverlauf-
  Linie wird zusätzlich in einer eigenen, klar unterscheidbaren Akzentfarbe
  (`#9c1458`) darübergezeichnet.
- **Rückwärtskompatibel:** bereits vor diesem Nachtrag erzeugte Signale haben
  kein `kursverlauf` im gespeicherten `facts_json` - für diese bleibt das
  alte schematische Halbbreite-Layout unverändert erhalten (kein Fehler,
  keine kaputte/leere Grafik).

**Verifikation:** `liquiditaetszonen_fakt()` synthetisch getestet (Kursverlauf
korrekt eingebettet, 90-Punkte-Cap greift korrekt auf die neuesten Punkte,
Regressionscheck ohne `dates`/`closes` liefert weiterhin `kursverlauf: None`
bei unveränderten Zonen-Feldern); beide Chart-Varianten (mit/ohne
Kursverlauf) visuell geprüft; echter Tk-Smoke-Test mit einer realen
`HebelView`-Instanz und einem Signal MIT eingebettetem Kursverlauf bestätigt
fehlerfreie Einbettung; volle Regressionssuite (E-Mail-MIME-Test,
Pipeline-Imports) erneut gelaufen.

**Zusatz (gleicher Tag):** ein statischer, immer gleicher Erklärsatz direkt
im Bild ("Berührungen = frühere Kursreaktionen an dieser Zone · gefegt =
bereits durchbrochen (kein akutes Warnsignal mehr) · ungefegt = noch aktiv
(möglicher Stop-Hunt vor einer Bewegung)") - erklärt nur die Begrifflichkeit,
bewusst OHNE jede Signal-spezifische Wertung (das übernimmt weiterhin
ausschließlich die LLM in der eigenen Kurz-/Langbegründung, siehe
`hebel_analyst.py` Regel 17). Bleibt damit neutral im Sinne des
Stufe-1-Designs (reine Transparenz, kein Deckel, keine zweite
Interpretationsebene neben der KI). In beiden Chart-Varianten (mit/ohne
Kursverlauf) visuell geprüft, volle Regressionssuite erneut gelaufen.

**Weiterer Zusatz (gleicher Tag, echter Screenshot mit eng beieinander
liegenden Zonen):** das "Aktueller Kurs"-Label stand bislang wie die
Zonen-Labels links (`x=0.2`) - lagen Zonen/Kurs preislich nahe beieinander,
überlappten sich die Textblöcke trotz vertikalem Puffer. Fix: das
"Aktueller Kurs"-Label steht jetzt rechts (`ha="right"`, via
"Blend"-Transform - x als Achsen-Bruchteil unabhängig vom Datenbereich, y
weiterhin am echten Kurswert), die Zonen-Labels bleiben links - räumliche
statt nur vertikale Trennung, funktioniert auch bei sehr nahe beieinander
liegenden Preisen. Zusätzlich die Kursverlauf-Linie von 2.2px auf 1.4px
verschlankt (Nutzer-Wunsch). Beide Szenarien (eng beieinander/gut getrennt)
visuell geprüft, volle Regressionssuite erneut gelaufen.
Umbau) in allen drei Dateien fehlerfrei greift.

## Nachtrag (2026-07-24): Kontrathese-Übersetzung für offene Hebel-Positionen

**Echter Fund:** NEAR und HYPE (beide mit offener LONG-Hebel-Position)
produzierten über mehrere Tage wiederholte "Hebel ERÖFFNEN (SHORT)"-E-Mails
im 15-Minuten-Takt der Positions-Überwachung, obwohl die Einstellung "Nur
Long" durchgehend aktiv war und kein anderes Symbol im selben Zeitraum ein
SHORT-Signal erzeugte. Root Cause (Analyse siehe Session-Verlauf, vollständig
im Code dokumentiert): `hebel_analyst.py` SYSTEM_PROMPT Regel 2 erlaubt dem
Modell explizit, für ein Symbol mit offener Position frei eine Gegenrichtung
vorzuschlagen ("Short aktuell nicht über Bitpanda ausführbar ... KEINE
Einschränkung deiner Bewertung"). Der GUI-Schalter `hebel_richtung_modus`
filtert nur die Kandidaten-Richtung VOR dem LLM-Call - bei einer offenen
Position ist diese Kandidaten-Richtung strukturell immer die Positions-
Richtung selbst (LONG), der Filter also für diesen Pfad wirkungslos, während
das Modell hinterher trotzdem frei SHORT ausgeben durfte. Ein reines Veto auf
HALTEN hätte die eigentliche Information (das Modell sieht erhöhtes Risiko
für die bestehende Position) weggeworfen.

**Lösung - Kontrathese-Übersetzung statt Veto** (`hebel_risk_gate.py::
post_check_hebel()`, neu VOR dem CRV-Gate/HEBEL_SENKEN-Zweig): schlägt das
Modell `ERÖFFNEN` in der Gegenrichtung zur bestehenden Position vor, wird
das deterministisch in eine Aktion AUF die bestehende Position übersetzt,
`richtung` wird auf die Positions-Richtung zurückgesetzt:

- Konfidenz ≥ 70% (`KONFIDENZ_SCHWELLE_HOCH`, bereits bestehende, dem Nutzer
  aus jedem Signal bekannte Einstufung, jetzt als benannte Konstante in
  `risk_gate.py` gemeinsam mit `hebel_risk_gate.py` genutzt) → sofort
  `SCHLIESSEN`, kein Zeitfenster nötig (eindeutiger Alarm).
- Konfidenz 55-70% → `TEILVERKAUF`, aber nur wenn die Kontrathese über ein
  Zeitfenster (`kontrathese_bestaetigung_stunden`, Standard 2h) DURCHGEHEND
  bestanden hat (`_kontrathese_bestaetigt_seit_stunden()`, läuft die
  bisherige Positions-Historie rückwärts, bis der erste nicht-passende
  Eintrag auftaucht). Vor Ablauf des Zeitfensters bleibt es bei `HALTEN`.
- Konfidenz < 55% → immer `HALTEN`.
- In allen drei Fällen bleibt die Kontrathese als eigener, immer zuerst
  gelisteter Risikofaktor "Kontrathese zur offenen Position" sichtbar (auch
  im HALTEN-Fall, damit die Information nicht verloren geht, nur eben ohne
  E-Mail, da HALTEN wie bisher keine E-Mail auslöst).

**Bewusst zeitfenster- statt zyklusbasiert:** die Positions-Überwachung
selbst bleibt unverändert häufig (kein gedrosseltes Monitoring - erhöhtes
Risiko soll weiterhin engmaschig beobachtet werden), nur das tatsächliche
AUSLÖSEN einer Aktion wird gedämpft. Ein echter Export der Notebook-Signal-
Historie (07-24) bestätigte den Bedarf: die real beobachteten SHORT-Ausschläge
lagen durchgehend bei 40-65% Konfidenz und kehrten binnen 15-30 Minuten
wieder auf LONG zurück - eine reine "letzte Bewertung stimmt zu"-Prüfung
wäre bei diesem Takt wirkungslos gegen Rauschen gewesen.

**Bewusst NICHT genullt:** Entry-/Stop-Loss-/Take-Profit-Zonen aus dem
Original-Vorschlag bleiben unverändert erhalten (Nutzer-Entscheidung: eine
stille Löschung wäre ein vergessbarer Sondereingriff) - Anzeige (App +
E-Mail) beschriftet sie bei einer Kontrathese-Übersetzung um
("Referenzzonen der Kontrathese ... kein neuer Einstieg") statt sie zu
verstecken. Zwei neue, rein auditierende Felder (`HebelSignal.
kontrathese_zu_position`/`kontrathese_llm_richtung`) machen die Übersetzung
dauerhaft nachvollziehbar, statt sie stillschweigend in `action`/`richtung`
verschwinden zu lassen.

**Zusätzlicher, unabhängig gerechtfertigter Cooldown-Fix:** `budget_
allocator.py::_filter_hebel_cooldown()` nutzte für ALLE Kandidaten (auch
Positions-Überwachung) die richtungsblinde `get_latest_hebel_signal_per_
symbol()` statt der bereits existierenden `get_latest_hebel_signal_per_
symbol_and_richtung()` - ein gespeichertes SHORT-Signal liess den 3h-
Positions-Cooldown für den nächsten LONG-Kandidaten leerlaufen (`sig.
richtung == c.richtung` war nie erfüllt). Realer Export bestätigte die
Auswirkung: Positions-Neubewertung lief dadurch alle ~15 Min. statt der
vorgesehenen 3h. Durch die Kontrathese-Übersetzung (richtung wird immer auf
die Positions-Richtung zurückgesetzt) trägt dieser Pfad künftig ohnehin nie
mehr eine abweichende Richtung, der Cooldown-Fix bleibt aber unabhängig
korrekt (schützt z.B. echte parallele LONG-/SHORT-Thesen desselben Symbols
voreinander) und wurde mit umgesetzt.

**Interaktion mit Ueberholt-Erkennung geprüft** (`hebel_backward_tracking.py::
_is_superseded()`, auf Nutzer-Nachfrage explizit analysiert): das bestehende
Zonen-Reaffirmation-Gate (2026-07-22) vergleicht Entry-/Stop-Loss-/Take-
Profit-Mittelwerte zwischen einem alten und einem neuen Signal, um eine
echte neue These von einer blossen Wiederholung zu unterscheiden - bei einem
Kontrathese-Signal sind die (bewusst nicht genullten) Zonen aber der
Original-Vorschlag für die NIE ausgeführte Gegenrichtung, nicht vergleichbar
mit der echten Position. Ein zufälliger Zahlenabgleich wäre weder eine echte
Reaffirmation noch ein echter Widerspruch. Fix: das Zonen-Gate wird
übersprungen, wenn das neuere Signal `kontrathese_zu_position` trägt - das
Mindestbeobachtung-Gate bleibt unverändert in Kraft (schützt weiterhin vor
zu früher Überholung eines gerade erst eröffneten Signals).
`check_hebel_signal_outcome()` selbst ist nicht betroffen - filtert bereits
vorher auf `_TRACKABLE_HEBEL_ACTIONS` (nur ERÖFFNEN/NACHKAUFEN), SCHLIESSEN/
TEILVERKAUF/HALTEN werden dort unverändert übersprungen.

**Verifikation:** 24 synthetische Checks (Zeitfenster-Logik pur, alle drei
Konfidenz-Buckets End-to-End, Regressionstest ohne offene Position/bei
gleicher Richtung/für HEBEL_SENKEN, Zonen-Reaffirmation-Bypass in
`_is_superseded()` inkl. Gegenprobe dass das Gate für normale Signale
weiterhin aktiv bleibt) - alle bestanden. Echter Nachvollzug: die komplette
reale NEAR/HYPE-Signalhistorie (Notebook-Export 2026-07-24) durch die neue
Logik laufen lassen - jeder historisch tatsächlich versendete "ERÖFFNEN
SHORT"-Ausschlag wäre unter der neuen Logik `HALTEN` (keine E-Mail)
geblieben, da die Konfidenz nie durchgehend 2h über der Schwelle blieb
(maximal beobachtet: 0,5h vor Rückkehr auf LONG).

**Nachtrag (gleicher Tag): Liquiditätszonen-Chart-Konsistenz + Kombianzeige.**
Nutzer-Fund an einem echten Screenshot: die "Aktueller Kurs"-Linie nutzte
einen LIVE nachgeladenen Preis, während `kursverlauf`/Zonen-"gefegt"-Flags
zum Signal-Erstellungszeitpunkt eingefroren sind - bei einem älteren, erneut
geöffneten Signal lief das sichtbar auseinander. Root Cause NICHT nur ein
Anzeigefehler: der gesamte Liquiditätszonen-Fakt ist wie jeder Fakt eines
Signals eine Zeitpunkt-Momentaufnahme, keine Live-Prognose.

Lösung - Kombianzeige statt reinem Umbenennen: `render_liquiditaetszonen_
chart()` zeigt jetzt BEIDE Preise - "Kurs zum Analysezeitpunkt" (aus
`facts["preis"]["eur"]`, konsistent mit `kursverlauf`) UND optional
"Aktueller Kurs (jetzt)" (live nachgeladen, eigene Farbe/gestrichelt, nur
gezeichnet bei spürbarem Unterschied). Automatischer Hinweis je Zone, wenn
der Live-Preis eine noch "nicht gefegte" Zone seit der Analyse bereits
erreicht/durchbrochen hat - der eingefrorene historische Status selbst wird
NICHT überschrieben (Audit-Prinzip). Beide Aufrufer laden den Live-Preis
zusätzlich, mit Fallback auf die reine Analysezeitpunkt-Ansicht bei
Abruffehler.

Konzeptionelle Klarstellung (Nutzer-Diskussion): der Chart liefert und
lieferte nie einen "Blick in die Zukunft" - rein deskriptiv, analog zu
jedem anderen Fakt (RSI, Regime). Die tatsächliche Forecast-Einschätzung
liefert ausschließlich das LLM selbst (Bull/Base/Bear-Abschnitt). Eine
echte Verbesserung der Vorhersagekraft (Stufe 2: Order Blocks/Fair Value
Gaps) würde eine Validierung gegen echte historische Preisdaten erfordern
(`agent/krypto/backtesting.py`, bereits vorhanden) - bewusst NICHT
ungeprüft ergänzt, siehe [[feedback_backtest_first_hard_guarantee]].

**Nachtrag (gleicher Tag): Provider-Performance-Verwässerung durch
Kontrathese-Phantome.** Nutzer-Beobachtung: Provider-Performance (Hebel)
zeigte seit einem Tag keine Veränderung. Echte Logs bestätigten: der
tägliche `backward_tracking_job` läuft korrekt (9 echte Auflösungen am
23.07.) - kein Stillstand. Der "weiterhin offen"-Pool wuchs aber auffällig
(38→41→62), weil jedes wiederholte Kontrathese-"ERÖFFNEN SHORT"-Phantom für
NEAR/HYPE selbst ein trackbares Hebel-Signal ist (erfüllt
`_TRACKABLE_HEBEL_ACTIONS`) - mit Zonen einer nie echten These, die nie
sauber auflösen. Strukturell ab sofort durch die Kontrathese-Übersetzung
selbst behoben (action wird zu SCHLIESSEN/TEILVERKAUF/HALTEN). Für bereits
entstandene Alt-Einträge: einmaliges Skript `bereinigung_kontrathese_
phantome.py` (Dry-Run per Default, `--apply` zum Anwenden) markiert sie
retroaktiv als `outcome_status = "nicht_anwendbar"` - keine Löschung,
volle Audit-Spur erhalten.

## Nachtrag (2026-07-24): Liquiditätszonen Phase A - Backtest ohne Kante gefunden, Stufe 2 bewusst nicht gebaut

**Fragestellung:** sagt die Nähe zu einer noch nicht gefegten Liquiditätszone
(Stufe 1, Marketmaker-/Smart-Money-These) eine echte Kursbewegung in die
erwartete Richtung voraus, oder ist eine beobachtete Trefferquote nicht
besser als eine Zufalls-Baseline? Reine Erkenntnisphase (Nutzer-Vorgabe:
offenes Ergebnis, keine Vorentscheidung für Stufe 2/Order Blocks/Fair Value
Gaps), explizit um kein unbelegtes Konzept ("totes Pferd") weiterzubauen.

**Methodik** (`backtest_liquiditaetszonen.py`, neues eigenständiges Skript,
kein Live-Seiteneffekt): ereignisbasiert statt tagesbasiert (Flanken-Trigger
wie in `backtesting.py` - nur der erste Tag der Zonen-Nähe zählt, sonst
blähen Folgetage an derselben Zone die Stichprobe künstlich auf) MIT
Kontrollgruppe (Gegenflanke "nicht mehr nahe irgendeiner Zone", Richtung
per fixem Zufalls-Seed zugeordnet - simuliert die Nullhypothese). Kein
Lookahead-Bias (identische Tag-für-Tag-Slices, dieselbe
`build_technical_snapshot()`/`liquiditaetszonen_fakt()`-Logik wie live -
eine Quelle der Wahrheit). Ein einziger vorab festgelegter Test (3%-
Bewegungsschwelle, 10-Tage-Fenster), keine Parameter-Variation im
Nachhinein.

**Ergebnis:** 16 Krypto-Symbole, ~2 Jahre echte Kursdaten (2024-07 bis
2026-07), 130 Ereignisse je Gruppe. Treatment (nahe ungefegter Zone):
76/130 (58,5%). Control (Zufalls-Baseline): 81/130 (62,3%) - Treatment liegt
sogar leicht UNTER der Kontrollgruppe. Zwei-Proportionen-Z-Test: p=0,53,
kein statistisch signifikanter Unterschied. Explorative Randnotiz (kein
eigener vorregistrierter Test, nicht belastbar): Buy-Side 67,3% (n=49) vs.
Sell-Side 53,1% (n=81).

**Entscheidung: Stufe 2 (Order Blocks/Fair Value Gaps) wird NICHT gebaut.**
Beide Konzepte beruhen auf derselben unbestätigten Smart-Money-Prämisse -
kein Grund zur Annahme, dass sie sich anders verhalten würden als die hier
getestete Kernthese.

**Wichtige Abgrenzung:** widerlegt ist die VORHERSAGE-These ("Zonen-Nähe
sagt Richtung voraus"), NICHT die reine Existenz der Zonen selbst (Swing-
Extrema mit historischen Berührungen sind eine deterministische Beobachtung,
keine falsifizierbare These). Stufe 1 bleibt unverändert - sie hat von
Anfang an bewusst NUR die unstrittige Beobachtung gezeigt ("Zone, N
Berührungen, gefegt/ungefegt"), nie eine Richtungsaussage (siehe der
statische Erklärsatz "kein Richtungsurteil"). Das heutige Ergebnis
bestätigt nachträglich, dass diese Zurückhaltung richtig war.

**Bekannte Grenzen:** Krypto-Symbole sind untereinander stark korreliert
(kein voll unabhängiges Stichproben-Multiplikatorargument über die
Symbolanzahl), Zeitraum ist ein einzelner ~2-Jahres-Marktzyklus - ein
Nullergebnis heißt "kein großer Effekt in diesem Zeitraum gefunden", nicht
"für alle Zeit widerlegt". Skript bleibt im Repo für eine mögliche
spätere Wiederholung mit mehr/anderer Historie.

**Nachtrag (gleicher Tag): BTC/ETH-Teilmenge separat geprüft, längere
Historie bewusst NICHT nachgeladen.** Nutzer-Hypothese: BTC/ETH als
liquideste, "smart-money-nahe" Assets könnten eine sauberere Kante zeigen
als das durch Alt-Coin-Rauschen (News-Pumps, dünne Orderbücher, kurzlebiger
Hype) verwässerte Gesamtbild. Isolierter Test (BTC+ETH, dieselbe Methodik):
Treatment 15/31 (48,4%) vs. Control 20/31 (64,5%), z=-1,28, p=0,20 - auch
hier keine Kante, Punktschätzer sogar in die Gegenrichtung. Bei n=31 je
Gruppe zu klein für eine belastbare Aussage in beide Richtungen.

Vorschlag, mehrjährige BTC/ETH-Historie nachzuladen (beide seit Jahren frei
verfügbar, anders als die meisten Alt-Coins) wurde geprüft und bewusst
verworfen: die Liquiditätszonen-/Stop-Hunt-These setzt strukturell eine
Marktphase mit breiter Verfügbarkeit gehebelter Perpetual-Futures-Positionen
voraus, die sich erst ab ca. 2019/2020 in großem Maßstab etabliert hat.
Ältere BTC/ETH-Daten (z.B. 2015-2018) stammen aus einer strukturell anderen
Marktphase (kaum Institutionelle, andere Derivate-Tiefe/Liquidationsdynamik)
- das wäre keine echte Erhöhung der Stichprobenpower für die Frage "gilt das
HEUTE", sondern eine Vermischung zweier nicht vergleichbarer Marktregime
(Nicht-Stationarität). Die vorhandenen ~2 Jahre sind der tatsächlich
relevante, vergleichbare Zeitraum - eine bessere Antwort gäbe es nur durch
organisches Warten auf mehr Daten AUS DERSELBEN Marktphase, nicht durch
Rückgriff auf eine andere Ära. Untersuchung damit für jetzt abgeschlossen.

## Nachtrag (2026-07-24): Provider-Performance zeigt jetzt auch offene/laufende Signale, nicht nur Abschlüsse

Nutzer-Beobachtung nach Sichtung der Remote-Seite: für Spot (alle 4
Assetklassen) stand durchgehend "Noch keine abgeschlossenen Signale" - ohne
jeden Hinweis, ob überhaupt Fortschritt passiert oder das Tracking
stillsteht. Analyse per `extract_notebook_diagnose.py`-Export ergab: über die
gesamte Projektlaufzeit gab es nur **11 echte trackbare Spot-Signale**
(KAUFEN/NACHKAUFEN - HALTEN/TAUSCHEN werden nicht getrackt). 9 davon
(07-14 bis 07-18) fielen dem am 07-22 gefixten Überholt-Bug zum Opfer
(siehe [[project_ueberholt_erkennung_mindestbeobachtung_fix]]) und können
rückwirkend nicht mehr aufgelöst werden. **2 Signale seit dem Fix** (3QSS
und DBPK, beide NACHKAUFEN vom 2026-07-22, beides Absicherungspositionen -
`hauptgruppe: absicherung`, `assetklasse: etf`) laufen unauffällig weiter,
ohne vorzeitig als "überholt" markiert zu werden - ein gutes Zeichen für den
Fix, aber in der alten Kartendarstellung unsichtbar.

**Root Cause der Anzeige-Lücke:** `compute_provider_performance()`
(`agent/krypto/backward_tracking.py`) fragt ausschließlich bereits
AUFGELÖSTE Signale ab (`outcome_status IN (take_profit_erreicht,
stop_loss_erreicht, liquidation_wahrscheinlich)`) - es gab keine Abfrage für
"wie viele Signale laufen gerade offen mit".

**Fix:** neue Funktion `compute_offene_signale_uebersicht()` (gleiche Datei,
direkt nach `compute_provider_performance()`) - liest `outcome_status IS
NULL` UND eine echte trackbare Aktion (`KAUFEN`/`NACHKAUFEN` bei Spot,
`ERÖFFNEN`/`NACHKAUFEN` bei Hebel), gruppiert nach derselben Tier-Logik
(Spot nach Assetklasse, Hebel gesondert), aber OHNE Provider-Aufschlüsselung
(ein offenes Signal hat noch kein Ergebnis). Rückgabe je Tier: Anzahl +
ältestes `created_at`. `remote/status.py::build_status()` reicht das Ergebnis
als neues Feld `offene_signale` durch (`_get_offene_signale_uebersicht()`,
reiner Lesezugriff). `remote/server.py`: neue Funktion
`renderOffeneSignaleHinweis()` haengt bei jeder Tier-Zeile (auch wenn
bereits aufgelöste Signale vorhanden sind) einen Zusatzsatz an, z.B. "2
offene Signale in Beobachtung (ältestes seit 2 Tagen)" - nutzt die bereits
bestehende `fmtRelativeTime()`.

Verifiziert: synthetischer Test gegen eine temporäre DB (gemischte
offene/aufgelöste/HALTEN-Signale über mehrere Assetklassen + Hebel, mit UND
ohne `watchlist`-Parameter) + End-to-End-Lauf von `build_status()` gegen
dieselbe DB, `to_dict()`-Ausgabe geprüft.

**Nebenbefund (gleicher Anlass): Einstandspreis-Lücke bei VSN/XNO.** Zwei
kürzlich gekaufte Krypto-Assets (`beobachtungsstatus: beobachtung`) zeigten
`avg_buy_price_eur` UND `avg_buy_price_manual_eur` beide `null` im
Notebook-Export. Kein Bug - die automatische Einstandspreis-Berechnung
(`importer/bitpanda_avg_cost.py::sync_avg_buy_prices()`) ist bewusst ein
eigener manueller Menüpunkt ("Einstandspreise von Bitpanda berechnen",
`ui/app.py`), der seit dem Kauf nicht erneut ausgelöst wurde. Nutzer hat die
von Bitpanda selbst angezeigten Durchschnittspreise geliefert (VSN 0,1273 €,
XNO 0,6279 €) - manuell über `db.set_holding_avg_buy_price_manual()`
gesetzt (VSN: Zeile existierte lokal) bzw. direkt in
`data/holdings_manual_overrides.json` ergänzt (XNO: hatte auf diesem Gerät
noch keine `holdings`-Zeile, `import_holdings_manual_overrides()` überspringt
das gefahrlos, bis die Zeile - z.B. auf dem Notebook, wo sie bereits
existiert - auftaucht). Kein Anlegen einer Phantom-Zeile, bestehendes
Invariant respektiert.

## Nachtrag (2026-07-24): #333 letzte zwei offene Mechanismen gebaut (EIA-Erdgas + Bellwether-Sentiment)

Die beiden zuvor nur entschiedenen, aber nicht gebauten Design-Punkte der
#333-Statustabelle (siehe Kategorie_Basisinformationen_Release2.md Abschnitt
11, Punkte 9+11) sind jetzt vollständig implementiert - damit ist Schicht 1
von #333 (deterministische Mechanismen) komplett, offen bleibt nur noch
Schicht 2 (tägliche LLM-Synthese über alle Kategorien, bewusst
zurückgestellt).

**EIA-Erdgas-5-Jahres-Saisonvergleich** (`agent/kategorie_thesen.py::
_abgleich_eia_erdgas()`): ruft `get_natural_gas_storage_history()`
(`api/eia.py`, unverändert) mit `n_weeks=270` statt der bisherigen 8 auf,
gleicht den aktuellsten Wert gegen die letzten 5 Kalenderjahre am selben Tag
(±4 Tage Toleranz, Schaltjahr-sicher über `try/except ValueError` bei
29. Februar) ab. Materialitätsschwelle ±5% vom 5-Jahres-Schnitt. Wichtige
Abgrenzung: in `config.py` NUR unter der spezifischeren Kategorie
`energie:erdgas` mit `cot_positionierung` kombiniert (2-von-2), NICHT unter
der Energie-Hauptgruppe insgesamt - die poolt COT-seitig Erdgas UND Rohöl,
der EIA-Lagerbestand betrifft aber ausschließlich Erdgas. Live-Test (2026-07-24):
3.056 Bcf vs. 5-Jahres-Schnitt 2.871 Bcf (+6,4%) → widerspricht einer
"übergewichten"-These (reichliches Angebot = bearish für Erdgaspreis).

**Bellwether-Sentiment** (`agent/kategorie_thesen.py::_abgleich_bellwether()`
+ `_BELLWETHER_TICKER`): manuell kuratierte 2-Ticker-Körbe für 10
Unterkategorien (Halbleiter NVDA/AMD, KI MSFT/PLTR, Cybersicherheit CRWD/PANW,
Biotech AMGN/VRTX unter Technologie & KI; Gesundheit UNH/JNJ, Konsum-zyklisch
AMZN/HD, Konsum-Basis PG/KO, Industrie HON/CAT, Kommunikation GOOGL/META,
Grundstoffe LIN/DOW unter Aktien-Sektoren) - kein automatisches Ableiten
möglich, da Bitpandas Themenkorb-Symbole Produktnamen statt Börsenticker sind
(`agent/aktien/screener.py`). Drei Signale je Korb:
- Analystentrend (Finnhub `get_recommendation_trends()`): Buy+StrongBuy-Anteil
  aktuell vs. Vormonat, gemittelt über den Korb, nur bei Verschiebung > 5
  Prozentpunkte gewertet.
- Insider-Aktivität (SEC EDGAR `get_recent_insider_transactions()`): Anzahl
  Käufer vs. Verkäufer im Korb (bewusst nicht Dollar-Volumen).
- Short-Interest-Trend (FINRA `get_short_interest_history()`): Days-to-Cover-
  Änderung ggü. Vorperiode, gemittelt über den Korb.

Kombinationsregel: mindestens 2 von 3 auswertbare Signale müssen in
dieselbe Richtung zeigen, sonst "gemischt/neutral". 5 synthetische Tests
(alle 3 bullisch, 2 von 3 bearisch, gemischt ohne Mehrheit, unbekannte
Kategorie, fehlender Finnhub-Key mit noch 2 verbleibenden Signalen)
bestanden. Echter Live-Lauf (Halbleiter-Korb NVDA/AMD): Analystentrend +1,8pp
(unter der Schwelle, kein Signal), Insider 0 Käufer vs. 29 Verkäufer
(bearisch), Short-Interest Days-to-Cover +0,01 (bearisch) → 2 von 3 bearisch
→ widerspricht einer "übergewichten"-These.

**Bekannte Design-Lücke (nicht selbstständig nachgeschärft, da nicht Teil
des dokumentierten Auftrags):** die 5-Prozentpunkte-Materialitätsschwelle aus
Abschnitt 12 gilt laut Konzept-Dokument nur für den Analystentrend - für
Insider-Aktivität und Short-Interest-Trend ist dort keine Mindestgröße
spezifiziert. Der echte Live-Test zeigte das: eine Days-to-Cover-Änderung von
nur +0,01 Handelstagen (praktisch Rauschen) zählte bereits als vollwertiges
bearishes Signal. Sollte sich das im laufenden Betrieb als zu sensibel
erweisen, wäre eine analoge Mindestschwelle für Short-Interest (z.B. > 0,1
Handelstage) ein naheliegender Nachbesserungspunkt - bewusst nicht
eigenmächtig ergänzt, da das Konzept-Dokument hier explizit keine Schwelle
vorsah.

Config-Wiring (`config.py::PRUEF_MECHANISMUS_MAPPING`): `energie:erdgas`
sowie alle 10 Bellwether-Unterkategorien neu, `review_tage_vorschlag=45`
für Bellwether (an FINRAs zweimal-monatlicher Meldefrequenz orientiert, der
langsamsten der drei Quellen).

Status-Tabelle (Kategorie_Basisinformationen_Release2.md Abschnitt 11, Punkte
9+11) auf `[GEBAUT]` aktualisiert - damit sind alle #333-Punkte entweder
gebaut oder bewusst zurückgestellt (Schicht 2), keine offenen Design-Lücken
mehr in Schicht 1.

## Nachtrag (2026-07-24): Spot-Positionsgrößen-Deckel von Multiplikation auf min() umgestellt (Überstrenge-Prüfung)

**Auslöser:** Nutzer-Auftrag, nach dem #333-Push zur Sicherheit zu prüfen, ob
die Spot-Regeln/-Gates/-Berechnungen sich durch Akkumulation zu streng
auswirken. Befund: `risk_gate.py::post_check()` verkettete die vier
Positionsgrößen-Deckel (Konfidenz-Skalierung, Gegenszenario, technischer
Konflikt, CRV-knapp) bisher **multiplikativ** — bereits am 18.07. bewusst so
gebaut und verifiziert (siehe Nachtrag oben: "alle vier gleichzeitig aktiv
ergaben korrekt 1000 × 0,5 × 0,5 × 0,6 × 0,6 = 90 USD"). Das war zum
Zeitpunkt des Baus eine korrekt umgesetzte Designentscheidung, aber bei
genauerer Prüfung problematisch, weil:
1. Die vier Faktoren sind inhaltlich NICHT unabhängig voneinander (gemischte
   Konfluenz und eine hohe Bear-Wahrscheinlichkeit treten oft gemeinsam auf,
   beides sind Symptome derselben unklaren Marktlage) - eine Multiplikation
   unterstellt aber unabhängige Beweise und überschätzt dadurch systematisch,
   wie schlecht das Setup wirklich ist.
2. Die Risikorichtung war verkehrt herum: `hebel_risk_gate.py` (das
   strukturell risikoreichere Instrument, Liquidationsgefahr) nutzt bei
   denselben vier Deckel-Kandidaten bereits die mildere `min()`-über-
   Kandidaten-Logik (`_hebel_deckel_kandidaten()`, seit 2026-07-18) - Spot
   (kein Hebel-/Liquidationsrisiko) verkettete dagegen strenger.
3. RM-1 begrenzt den maximalen Verlust bereits über die Stop-Loss-Distanz auf
   `risiko_pro_trade_prozent` (2%) - die vier Deckel sind als zusätzliche,
   FEINERE Konviktions-Skalierung gedacht, nicht als zweite vollwertige
   Risikoprüfung. Multiplikative Verkettung behandelt sie aber genau so.

**Fix:** `risk_gate.py::post_check()` sammelt jetzt vier Deckel-Kandidaten
(je ein `(Grund, USD-Obergrenze)`-Paar, nur falls die jeweilige Bedingung
tatsächlich zutrifft) und nimmt `min()` darüber - identisches Prinzip wie
bereits bei `hebel_risk_gate.py::_hebel_deckel_kandidaten()` etabliert,
inklusive derselben "bindender Grund"-Formulierung in der Positions-Notiz.
Eigene Config-Werte bleiben komplett getrennt von Hebels eigenen (nur die
Verknüpfungslogik wird angeglichen, keine Werte geteilt).

Beispiel (identischer Testfall wie beim ursprünglichen Bau): Konfidenz genau
an der Regime-Mindestschwelle (75% im Bärenmarkt, Skalierung 50%),
Gegenszenario 40% (Deckel 50%), gemischte Konfluenz (Deckel 60%), CRV 2,1
(Deckel 60%) - alle vier gleichzeitig aktiv. **Vorher:** 1000 × 0,5 × 0,5 ×
0,6 × 0,6 = 90 USD (9% der Obergrenze). **Jetzt:** `min(500, 500, 600, 600)`
= 500 USD (50%, gebunden durch die Konfidenz-Skalierung als strengsten
Einzelgrund).

**Zusätzlicher, separat dokumentierter Befund derselben Prüfung (nicht
Bestandteil dieses Fixes):** die regimeabhängige Mindestkonfidenz
(`min_konfidenz_prozent`, aktuell 75% im Bärenmarkt-Regime, siehe
`config.yaml risiko.regime.profile`) bleibt ein hartes Veto, unverändert -
das ist vermutlich der Hauptgrund für die beobachtete Flaute an echten
Spot-KAUFEN-Signalen (0 neue seit 18.07., siehe Provider-Performance-
Analyse weiter oben), nicht die jetzt gefixte Positionsgrößen-Kumulation.
Ob diese Schwelle selbst nachjustiert werden sollte, ist ein bewusst
zurückgestellter, separater Prüfpunkt - vom Nutzer als "wieder relevant
geworden" markiert, noch nicht bearbeitet.

**Verifiziert:** synthetische Tests gegen die echte `post_check()`-Funktion -
(a) alle vier Trigger gleichzeitig aktiv → 500 USD statt der alten 90 USD,
(b) kein Trigger aktiv → keine Reduktion, (c) nur ein einzelner Trigger (CRV-
knapp) → exakt dessen Faktor (600 USD), (d) vorgeschlagene Positionsgröße
bereits unter der Obergrenze → unverändert, kein Clamp. Import-Smoke-Test
aller abhängigen Pipelines (keine Regression).

## Nachtrag (2026-07-24, gleicher Tag): Gates-Kalibrierung — echte Ursache gefunden, Prompt-Anker statt Zahlenwerte korrigiert

**Auslöser:** Nutzer-Auftrag, im Anschluss an den Deckel-Fix oben zu prüfen, ob
die harten Gates selbst (`min_konfidenz_prozent` je Regime, `CRV_MINIMUM`)
nachjustiert werden sollten - explizit als Folgepunkt aus der Deckel-Prüfung
markiert.

**Befund (Auswertung von `notebook_diagnose.json`, 2026-07-24 19:32 exportiert,
1236 Spot- + 713 Hebel-Signale der echten Produktion):** Die Gates selbst waren
NICHT die Ursache. Von allen Spot-Risiko-Vetos der letzten 10 Tage kamen 200
vom Konfidenz-Gate (`min_konfidenz_prozent`=75% im Bär-Regime), nur 19 vom
CRV-Gate - aber der eigentliche Befund liegt tiefer: die Konfidenz-AUSGABE der
KI selbst ist am 18./19.07. abrupt kollabiert, exakt am Tag der "5-Bausteine-
A-E"-Nachbesserung (siehe Nachtrag weiter oben, 2026-07-18):

| Zeitraum | Anteil Signale ≥75% Konfidenz | Ø Konfidenz (Spot) | Ø Konfidenz (Hebel) |
|---|---|---|---|
| vor 07-19 | 28-79%/Tag | 72,8% | 64,6% (37,4% ≥75%) |
| ab 07-19 | 0-2%/Tag | 63,4% | 49,0% (**0,0%** ≥75%, Maximum je 65%) |

Zwei naheliegende Alternativerklärungen wurden geprüft und ausgeschlossen:
Provider-Wechsel (Bruch bleibt exakt am selben Datum bestehen, isoliert nur
auf `mistral:mistral-small-2506`-Zeilen: 69,0% → 63,4%), sowie die
Historische-Trefferquote (Baustein E) - strukturell fast immer `null`, da
0 von 1236 Spot-Signalen je ein reales TP/SL-Ergebnis haben.

**Wahre Ursache:** Regel 22 (`analyst.py`) bzw. Regel 13 (`hebel_analyst.py`),
beide am 18.07. eingeführt (Pflichtfeld `gegenargument` vor `confidence_pct`,
mit hartem Anker "ein GENUIN starkes Gegenargument darf NICHT mit hoher
Konfidenz (>75%) kombiniert werden"). Dabei ein echter Autoren-Widerspruch
gefunden: der Fließtext verlangte für "genuin stark" bereits ZWEI gleichzeitig
zutreffende Schwachpunkte (Konfluenz gemischt UND CRV knapp), das direkt
folgende Beispiel zeigte aber nur EINEN Schwachpunkt (Konfluenz gemischt
allein) als bereits disqualifizierend für 80% Konfidenz - ein einzelner,
häufig auftretender Faktor wurde damit faktisch zum generellen Deckel, obwohl
die Regel das gar nicht so meinte.

**Fix:** In beiden Dateien wurde NICHT die Zahl (75%) geändert, sondern die
Gradierung präzisiert: ein einzelner, isolierter Schwachpunkt rechtfertigt nur
eine moderate Abwertung (kein Fall unter 75%), erst mehrere gleichzeitig
zutreffende Schwachpunkte rechtfertigen eine deutliche Abwertung (>75% dann
nicht mehr angemessen). Das widersprüchliche Beispiel wurde korrigiert (zeigt
jetzt den echten CAT-Fall mit BEIDEN Faktoren gleichzeitig). Zusätzlich ein
expliziter Hinweis, die volle Bandbreite 0-100% zu nutzen - eine Konfidenz,
die praktisch immer im selben schmalen Band landet, sei selbst ein
Kalibrierungsfehler.

**Verifiziert (echte Mistral-API-Calls, A/B-Vergleich mit identischen Fakten,
alter vs. neuer Prompt):**
- Spot, EIN isolierter Schwachpunkt (nur Konfluenz gemischt, CRV komfortabel
  über 2.4): ALT 70% (unter dem Gate) → NEU 80% (klar über dem Gate).
- Spot, sauberes Setup ohne Einwand: ALT 70% → NEU 75%.
- Spot, ECHTER CAT-Fall-Nachbau (Konfluenz gemischt UND CRV knapp
  gleichzeitig): ALT ~70-75% → NEU ~75% - bewusst weiterhin gedämpft, der Fix
  wertet also nicht pauschal alles auf.
- Hebel, EIN isolierter Schwachpunkt: ALT sogar `action=HALTEN` bei 40%
  Konfidenz (keine Positions-Eröffnung vorgeschlagen!) → NEU `action=ERÖFFNEN`
  bei 70%.

**Bewertung zur ursprünglichen Frage (Gates nachjustieren?):** Noch NICHT
nötig. Der Prompt-Fix hebt die Konfidenz-Decke im entscheidenden Einzelfall-
Szenario bereits über die bestehende 75%-Schwelle (80% statt 70%), ohne die
Unterscheidungsfähigkeit für echte Mehrfach-Warnsignale zu verlieren (CAT-Fall
bleibt korrekt gedämpft). Variante B (Gates absenken) bleibt eine Option,
falls sich nach einigen Tagen echtem Produktionsbetrieb zeigt, dass die
Konfidenz-Verteilung trotz Fix weiterhin zu eng um 70-75% clustert -
Beobachtungszeitraum vom Nutzer explizit vereinbart, keine Live-Umstellung der
Zahlenwerte ohne diesen Zwischen-Check.

## Nachtrag (2026-07-25): Liquiditätszonen-Grafik für Spot nachgezogen (Hebel-only-Lücke geschlossen)

**Auslöser:** Nutzer-Frage anhand eines echten Spot-Signal-Screenshots, warum
die am 2026-07-23 gebauten Verbesserungen (Detail-Panel-Farben/Überschriften,
Liquiditätszonen-Grafik) nicht überall gleich ankommen. Prüfung ergab zwei
getrennte Befunde:

1. **Farben/Überschriften: kein Fund, bereits korrekt.** `ui/signals_view.py`,
   `ui/marktscan_view.py` und `ui/hebel_view.py` rufen alle drei ausschließlich
   `ui/detail_panel.py::configure_tags()`/`render_detail_text()` auf - die
   einzige Stelle, die Tk-Tags vergibt. Alle drei bauen zudem identische
   Zeilenmuster (`--- N. ... ---`-Überschriften, `▲/●/▼`-Risikofaktor-Marker
   über das gemeinsame `ui/formatting.py::format_risikofaktoren_lines()`) -
   es gibt keine Möglichkeit, dass Spot/Marktscan/Hebel hier auseinanderlaufen.

2. **Liquiditätszonen-GRAFIK (PNG-Chart): echter Fund, nur Hebel.** Der
   zugrunde liegende Fakt + Text-Risikofaktor (Abschnitt 3) läuft korrekt auch
   für Spot-Krypto (bewusste, dokumentierte Scope-Entscheidung: Krypto Spot +
   Hebel, NICHT Aktien/Rohstoffe/Hedge/Themen-ETF, siehe Nachtrag "Liquiditäts­
   zonen (Marketmaker-Konzept)" weiter oben). Die VISUELLE Grafik
   (`ui/liquidity_chart.py::render_liquiditaetszonen_chart()`) wurde beim Bau
   am 2026-07-23 aber ausschließlich in `ui/hebel_view.py` und
   `scheduler/background.py::_notify_hebel_signal()` verdrahtet - nie in das
   parallele Spot-Pendant (`ui/signals_view.py`, `_notify_spot_signal()`)
   übertragen. Anders als bei der Aktien/Rohstoffe/Hedge/Themen-ETF-Abgrenzung
   war das keine bewusste Entscheidung, sondern schlicht nicht mitgezogen -
   die Session war durch einen konkreten Hebel-Screenshot ausgelöst und direkt
   gegen den bereits offenen Hebel-Code-Pfad gebaut.

**Fix:** `ui/signals_view.py` bekommt eine neue `_render_liquiditaetszonen_
chart()`, 1:1 aus `ui/hebel_view.py` gespiegelt (gleicher Renderer, gleiche
Live-Preis-Kombianzeige aus `db.get_latest_prices()`, gleiche Fehlerbehandlung
- kein Hard-Fail, wenn keine Zone/kein Preis vorliegt). `scheduler/
background.py::_notify_spot_signal()` bekommt denselben Chart-Rendering-Block
wie `_notify_hebel_signal()`, `inline_image_png` wird jetzt an `send_
notification_email()` durchgereicht.

**Zweiter, separat identifizierter Fund derselben Prüfung (NICHT Teil dieses
Fixes, bewusst zurückgestellt bis nach Datenanalyse):** die "Retail-Konsens-
Risiko auf Fakt-zuerst umbauen"-Nachbesserung vom 2026-07-22 (siehe
`hebel_risk_gate.py::retail_konsens_risiko()`, 3-stufige Bewertung statt
binärer Ja/Nein-Phrase) wurde ebenfalls nur in `hebel_risk_gate.py`
umgesetzt, nie nach `risk_gate.py` (Spot) gespiegelt - Spot nutzt dort
weiterhin die alte binäre Logik (nur "extrem" vs. "positiv", kein neutraler
Mittelbereich). Nutzer bat ausdrücklich um sorgfältige Datenanalyse vor einer
Änderung an dieser Stelle, da erst kürzlich mehrere Spot-Gates/-Parameter
angepasst wurden (siehe beide Nachträge oben) - Fix bewusst noch nicht
umgesetzt.

**Verifiziert:**
- Echter Tk-Smoke-Test von `SignalsView._render_liquiditaetszonen_chart()`
  (3 Fälle: mit echten Zonen inkl. Kursverlauf → Bild korrekt eingebettet,
  ohne Zonen → sauber übersprungen kein Absturz, kaputtes JSON → abgefangen).
- Echter Funktionstest von `_notify_spot_signal()` mit gemockter `send_
  notification_email()`/`config_module.load_config()`: Chart-PNG kommt jetzt
  tatsächlich als `inline_image_png` in der Spot-Benachrichtigungsmail an.
- Import-Sanity-Check über alle betroffenen Module (`ui.signals_view`,
  `ui.hebel_view`, `scheduler.background`, `agent.krypto.pipeline`,
  `agent.krypto.risk_gate`) - keine Regression.

## Nachtrag (2026-07-25, gleicher Tag): Retail-Konsens-Risiko Fakt-zuerst-Fix für Spot umgesetzt (Datenanalyse vorgeschaltet)

**Auslöser:** Fortsetzung des Nachtrags oben - Nutzer bat um sorgfältige
Datenanalyse (frischer `notebook_diagnose.json`-Export, 1266 Spot-Signale)
vor jeder Änderung, da erst kürzlich mehrere Spot-Gates/-Parameter angepasst
wurden.

**Datenanalyse (wichtige Korrektur der ersten Einschätzung):** `compute_
risikofaktoren()` hat bereits eine frühe Rückgabe (`if action not in
_BUY_ACTIONS: return faktoren`) - der Retail-Konsens-Block läuft also NUR,
wenn die ursprüngliche (Pre-Veto-)Aktion KAUFEN/NACHKAUFEN war, unabhängig
davon, was `risikofaktoren_json` als finale Aktion zeigt (z.B. nach einem
Konfidenz-Veto auf HALTEN). Die erste Zählung anhand der finalen Aktion war
dadurch fehlerhaft (nur 1 falsch gelabelter Fall gefunden). Korrekte
Auswertung: von 98 historischen "positiv"-Fällen betrafen tatsächlich alle
98 eine originale Kauf-Empfehlung - 79 davon bei einer NICHT-extremen
long-Mehrheit (50-65%), also fälschlich als "positiv/antizyklisch" gelabelt,
obwohl die Kauf-Empfehlung tatsächlich mit der Mehrheit mitlief. Nur 19 waren
tatsächlich korrekt (Kauf gegen eine Short-Mehrheit).

**Fix:** `agent/krypto/risk_gate.py::compute_risikofaktoren()` - Retail-
Konsens-Block auf dieselbe 3-Stufen-Fakt-zuerst-Logik wie `hebel_risk_
gate.py` umgestellt. Bewusst VEREINFACHT gegenüber Hebel: da `action` an
dieser Stelle durch die bereits bestehende frühe Rückgabe (Zeile ~512)
immer KAUFEN/NACHKAUFEN ist, gibt es - anders als bei Hebel (LONG/SHORT) -
keine "short-seitige" Gegenrichtung zu prüfen; "folgt die Empfehlung der
Mehrheit" reduziert sich auf "ist die Mehrheit selbst long". Kein
`_SELL_ACTIONS`-Zweig und keine symmetrische Extrem-Schwellen-Prüfung
nötig (beide wären an dieser Stelle toter Code) - erste Entwurfsversion
hatte das noch 1:1 aus Hebel übernommen, beim Review als unerreichbar
erkannt und entfernt.

**Verifiziert:**
- Historische Redistribution simuliert (98 alte "positiv"-Fälle durch die
  neue Logik gejagt): 79 → korrekt "neutral", 19 → weiterhin korrekt
  "positiv", 0 → "negativ" (erwartungsgemäß, da kein historischer Fall über
  der Extrem-Schwelle lag).
- Echter Funktionstest gegen `compute_risikofaktoren()` (5 Fälle): echter
  ALGO-Fall (KAUFEN, 60% long, nicht extrem) → jetzt korrekt "neutral";
  extreme Mehrheit (80% long) → weiterhin "negativ"; Kauf gegen die
  Mehrheit (30% long) → weiterhin "positiv"; Grenzfall exakt 50% →
  "positiv" (dokumentiertes Verhalten); HALTEN → früher Return, gar kein
  Faktor (unverändert).
- Regressionscheck: alle anderen Blöcke derselben Funktion (Gegenszenario/
  Konfluenz/CRV/Konfidenz) liefern bei gleichzeitiger Auswertung
  unverändert korrekte Werte.
- Import-Sanity-Check über alle 5 Spot-family-Pipelines (Krypto/Aktien/
  Rohstoffe/Hedge/Themen-ETF), die `risk_gate.py` gemeinsam nutzen.

## Nachtrag (2026-07-25, gleicher Tag): Konfidenz-Prompt-Fix auf Aktien/Rohstoffe/Themen-ETF ausgeweitet

**Auslöser:** Nutzer-Frage, ob die gestrigen Multi-Asset-Signal-Pipelines
(gebaut 2026-07-18) vom Konfidenz-Prompt-Fix (siehe Nachtrag oben,
"Konfidenz-Kollaps behoben") überhaupt erfasst wurden. Prüfung ergab: NEIN -
`agent/aktien/analyst.py`, `agent/rohstoff/analyst.py`,
`agent/themen_etf/analyst.py` haben jeweils ihre EIGENE, unabhängige Kopie
der Gegenargument-Regel (Regel 18/17/16) - der gestrige Fix wurde nur in
`agent/krypto/analyst.py` und `agent/krypto/hebel_analyst.py` gemacht, nie
hierher gespiegelt. Alle drei hatten denselben unkorrigierten harten Anker
("…darf NICHT mit hoher Konfidenz (>75%) kombiniert werden", ohne
Gradierung). `agent/hedge/analyst.py` (Regel 7) ist NICHT betroffen -
deutlich einfachere, ältere Formulierung ohne harten >75%-Anker.

**Empirisch bestätigt:** 58 historische Multi-Asset-Signale (PLTR, VST,
DBPK, 3QSS, OD7H, VVMX, X136, EXH3, CEBS, ISOC) zeigen dasselbe
Clustering-Muster wie Spot vor dem Fix (überwiegend 50-72% Konfidenz, kaum
je ≥75%).

**Fix:** identische Gradierungs-Logik wie gestern (einzelner Schwachpunkt =
moderate Abwertung, erst mehrere gleichzeitig = deutliche Abwertung,
korrigiertes Zwei-Faktor-Beispiel, expliziter Hinweis auf volle Bandbreite
0-100%) in allen drei Dateien nachgezogen, jeweils an die dortige
Faktoren-Liste angepasst (Aktien: Konfluenz/CRV/Fundamental-Allgemeinheit;
Rohstoffe: Konfluenz/CRV/Managed-Money-Positionierung; Themen-ETF:
Konfluenz/CRV/Sektor-Rotation).

**Verifiziert:** echter Mistral-A/B-Test für `agent/aktien/analyst.py`
(identisches Muster wie gestern bei Spot/Hebel, stellvertretend für alle
drei - gleicher Mechanismus, gleiches Modell): einzelner Schwachpunkt
(Konfluenz gemischt, CRV komfortabel über 2.4) - ALT 65% (beide Läufe) →
NEU 70-75%. Syntax-Check + Import-Sanity-Check über alle vier Multi-Asset-
Pipelines (Aktien/Rohstoffe/Hedge/Themen-ETF) bestanden.

**Übergreifende Lektion für künftige Analysen (Nutzer-Vorgabe):** bei
Prompt-/Regelwerk-Funden künftig IMMER alle Varianten durchprüfen - Spot,
Hebel, Multi-Asset (Aktien/Rohstoffe/Themen-ETF) UND Absicherungspositionen
(Hedge) - nicht nur die zuerst gefundene. Heute war das bereits der dritte
Fund dieses Musters am selben Tag (Liquiditätszonen-Grafik nur Hebel,
Retail-Konsens nur Hebel, jetzt Konfidenz-Prompt nur Spot/Hebel).

---

## Nachtrag (2026-07-25): echter BTC-Hebel-Signal-Review - Antizyklisch-Kategorie-Loophole + Liquiditätszonen-Währungs-Bug

Nutzer bat um eine Experten-Bewertung eines real eingetroffenen BTC-Hebel-
ERÖFFNEN-LONG-Signals (Screenshots). Zwei inhaltliche Funde, beide nach der
"alle Varianten prüfen"-Vorgabe auf Spot+Hebel bzw. Spot+Hebel+App+E-Mail
ausgeweitet:

### 1. Antizyklisch-Regel-8-Loophole (Hebel) + fehlende Absicherung (Spot)

Die bestehende Regel 8 (`hebel_analyst.py`, siehe Nachtrag 2026-07-22 oben)
verbot bereits, einen gleichgerichteten Retail-/Long-Konten-Konsens unter
`kategorie: antizyklisch` als Stütze zu formulieren - erlaubte aber
ausdrücklich, denselben Inhalt unter "eine andere Kategorie" zu verschieben.
Genau das geschah im echten Signal: Long-Konten-Anteil 65,2% wurde zweimal
als bullisher "Top-Grund" verwendet (einmal vermutlich unter einer anderen
Kategorie als `antizyklisch`), obwohl Abschnitt 3 (deterministischer
Risikofaktor) die Lage korrekt als Warnsignal einordnete - ein innerer
Widerspruch im selben Signal.

**Fix:** Regel 8 (Hebel) um einen expliziten Satz ergänzt: das Verbot gilt
für den INHALT, nicht nur für das Label `kategorie: antizyklisch` - unter
KEINER Kategorie (auch nicht technisch/fundamental/makro) darf ein
gleichgerichteter Retail-Konsens als Stütze formuliert werden, das
Umbenennen der Kategorie umgeht das Verbot nicht.

**Spot (`analyst.py`, Regel 15) hatte zusätzlich eine ältere, größere
Lücke:** dort stand bisher NUR der Extremfall-Satz (`retail_long_bias_
extrem`), die 2026-07-22 nachgezogene Moderat-Fall-Absicherung ("auch bei
NUR moderater Mehrheit") und die Kategorie-Loophole-Schließung fehlten
komplett. Beide beim heutigen Fix nachgezogen - Spot-Regel 15 ist jetzt
inhaltlich identisch zu Hebel-Regel 8 (angepasst auf `action`-Werte
KAUFEN/NACHKAUFEN statt `richtung`).

**Scope-Prüfung (Nutzer-Vorgabe):** `long_account_pct`/Retail-Konsens-Daten
existieren nur in Krypto Spot+Hebel (`anticyclic.py`), nicht in Aktien/
Rohstoffe/Themen-ETF/Hedge - dort ist kein Fix nötig, per Grep bestätigt.

### 2. Liquiditätszonen-Grafik: USD/EUR-Verwechslung (Spot+Hebel, App+E-Mail)

Zweiter, unabhängiger Fund aus demselben Signal: die Liquiditätszonen-
Grafik zeigte Funding-Kosten-Nachbarschaft im falschen Referenzsystem.
Root Cause: `liquiditaetszonen_fakt()` (`agent/krypto/liquidity_zones.py`)
wird in `pipeline.py`/`hebel_pipeline.py` mit `price_snap.price_usd` bzw.
USD-denominierten `closes` aufgerufen (aus `db.get_price_history()`) - die
gespeicherten Zonen-Preise UND die eingebettete `kursverlauf`-Reihe sind
also faktisch USD-Werte. Alle vier Aufrufstellen von
`render_liquiditaetszonen_chart()` (`ui/signals_view.py`, `ui/hebel_view.py`,
`scheduler/background.py` x2 für Spot-/Hebel-E-Mail) lasen jedoch
`facts["preis"]["eur"]` als Referenzpreis und beschrifteten den Chart als
"EUR" - eine EUR-Referenzlinie wurde mit USD-Zonenlinien und einer USD-
Kursverlaufslinie gemischt und falsch beschriftet. Betraf sowohl die
Achsen-Skalierung (Y-Range gebaut aus gemischten EUR+USD-Werten) als auch
jede angezeigte Zahl.

Der LLM-Prompt selbst (Regel 17 Hebel / Regel 16 Spot) ist NICHT betroffen -
dort wird nur mit `abstand_prozent` (währungsneutral) argumentiert, nie
mit einer absoluten Preis-Einheit.

**Fix:** alle vier Aufrufstellen auf `facts["preis"]["usd"]` bzw.
`live_snap.price_usd` und Label `"USD"` umgestellt - konsistent mit der
Datengrundlage, keine Änderung an der Berechnungslogik nötig (nur
Anzeigeschicht). Alternative (historische EUR-Umrechnung der Zonen-Preise)
wurde verworfen, da keine historischen Tages-FX-Kurse verfügbar sind -
gleiche Pragmatik wie beim Funding-Kosten-EUR-Fix (aktueller `eur_usd_fx_
rate`, keine rückwirkende Umrechnung).

### 3. Funding-Kosten jetzt auch in EUR (Hebel)

Dritter, kleinerer Fund: der Funding-Kosten-Risikofaktor
(`hebel_risk_gate.py::compute_risikofaktoren_hebel()`) zeigte den USD-
Betrag pro Tag, aber (anders als Liquidationspreis/Eigenkapitalbedarf seit
Task #401) keine EUR-Entsprechung. Fix: `eur_usd_fx_rate`-Parameter
ergänzt, gleiche `wert_eur = wert_usd / eur_usd_fx_rate`-Formel wie bei
Liquidationspreis - Ergebnis z. B. "2,66 USD/Tag (2,32 EUR/Tag) zulasten
der Position". Reiner Hebel-Fund (Funding-Kosten existieren nur bei
gehebelten Positionen, kein Spot-Pendant nötig - per Scope-Prüfung
bestätigt).

**Verifiziert:** Syntax-/Import-Check aller sieben geänderten Dateien
(`hebel_analyst.py`, `analyst.py`, `ui/signals_view.py`, `ui/hebel_view.py`,
`scheduler/background.py`, `hebel_risk_gate.py`), synthetischer Funktionstest
für die EUR-Umrechnung (mit/ohne `fx_rate`), synthetischer Rendering-Test
für `render_liquiditaetszonen_chart()` mit USD-Daten (kein Absturz, PNG
> 1000 Bytes). Kein Mistral-A/B-Test für die Regel-8/15-Textänderung in
dieser Runde (reine Präzisierung eines bereits bestehenden Verbots, kein
neuer Schwellenwert/Gate - anders als die Konfidenz-Prompt-Fixes, die
tatsächlich das Konfidenz-Niveau verschieben).

---

## Nachtrag (2026-07-25): Baustein 1 - BTC-Relativwert (Korrelation/Beta/Relativstärke), Krypto-Relativwert-Bausteine komplett

Letzter der drei geplanten "Krypto-Relativwert-Bausteine" (siehe Plan-Datei
swift-napping-muffin.md, ursprünglich aus der NEAR/HYPE-Hebel-Diskussion
entstanden) - übersetzt eine BTC-/Makro-Ebene-Einschätzung (z.B. den bereits
vorhandenen `historischer_makro_vergleich`, der nur SPX/BTC-Werte liefert)
in eine coinspezifische Größenordnung.

**Berechnung** (`indicators/calculations.py::compute_btc_relativwert()`,
neue `BtcRelativwert`-Dataclass): richtet die Preisreihe des Coins und von
BTC auf gemeinsame Handelstage aus (inner join, beide Reihen können
unterschiedliche Lücken haben), berechnet dann über ein 90-Tage-Fenster
(`fenster_tage_beta`) Korrelation und Beta aus den täglichen Returns
(`np.corrcoef`/`np.cov`/`np.var`, keine externe Statistik-Bibliothek nötig)
sowie über ein kürzeres 30-Tage-Fenster (`fenster_tage_relativstaerke`,
passend zur typischen `swing_strategie`-Haltedauer) die Relativstärke
(Coin-Rendite minus BTC-Rendite in Prozentpunkten). P-10 (Fail-Loud): unter
`fenster_tage_beta + 1` gemeinsamen Handelstagen gibt es KEIN Ergebnis
(`None`) statt einer instabilen Schätzung aus zu wenigen Punkten; ebenso bei
Nullvarianz in einer der beiden Reihen (degenerierter Fall).

**Einordnung** (neues Modul `agent/krypto/btc_relativwert.py::
btc_relativwert_fakt()`): reine Formatierungs-/Einordnungsschicht (Beta
<0,7/0,7-1,3/>1,3 → unter-/gleich-/überdurchschnittlich, Korrelation
<0,3/0,3-0,7/>0,7 → kaum/moderat/stark korreliert, Relativstärke außerhalb
±3 Prozentpunkte → Tailwind/Headwind), liefert immer eine klassifizierende
`einordnung`-Aussage statt roher Zahlen (Design-Entscheidung 1 der
Bausteine-Planung).

**Self-Comparison-Guard:** BTC selbst braucht keinen Vergleich zu sich
selbst - `pipeline.py`/`hebel_pipeline.py` überspringen die Berechnung komplett,
wenn `asset.symbol == "BTC"` ist (kein unnötiger zweiter DB-Read).

**Zeithorizont-Caveat (wichtigster Designpunkt, siehe Regel 28 Spot / Regel 20
Hebel):** Beta/Korrelation sind ein MEHRMONATIGER Kontext-Wert, KEINE Aussage
über die nächsten Tage - der Prompt verbietet explizit, den Fakt als
eigenständigen Grund für `action`/`richtung` zu nutzen, er darf höchstens
eine bereits vorliegende BTC-/Makro-Einschätzung auf den Coin übersetzen.
Bewusst KEIN Risikofaktor in `risk_gate.py`/`hebel_risk_gate.py` - eine feste
Schwelle (z.B. "Beta > 2 = riskant") wäre ohne echte Backtests unbegründet,
gleiche Zurückhaltung wie bei `historischer_makro_vergleich`.

**Verifiziert:**
1. Synthetischer Test von `compute_btc_relativwert()`: konstruierte Reihe mit
   bekanntem Beta (~2,0 eingebaut, Ergebnis 1,89 durch beigemischtes
   Rauschen - plausibel), Korrelation 0,98; Grenzfall zu wenig gemeinsame
   Punkte (50 von nötigen 91) → `None`; Grenzfall disjunkte Datumsreihen
   (keine Überschneidung) → `None`.
2. Synthetischer Test von `btc_relativwert_fakt()`: Toggle aus → `None`,
   `ergebnis=None` (z.B. BTC selbst) → `None`, Normalfall liefert
   klassifizierende `einordnung`.
3. **Echter Lauf gegen eine Kopie der Produktions-DB** (378 Tage BTC-Historie):
   ETH (Beta 1,26, Korrelation 0,88 - stark korreliert, leicht
   überdurchschnittlich), SOL (Beta 1,23, Korrelation 0,82), NEAR (Beta 0,94,
   Korrelation NUR 0,30 - plausibel, NEAR gilt in dieser Session bereits
   mehrfach als auffällig eigenständig/volatil), LINK, APT, AVAX, BNB -
   alle Werte plausibel im erwarteten Bereich, keine Ausreißer/Artefakte.
4. Gesamt-Regressionscheck: Import aller Krypto- (Spot/Hebel), Aktien-,
   Rohstoff-, Hedge-, Themen-ETF-Pipelines sowie `ui/hebel_view.py`,
   `ui/signals_view.py`, `scheduler/background.py` - keine Fehler.

**Damit sind alle drei Krypto-Relativwert-Bausteine (Signal-Stabilität,
Volatilitäts-Perzentil, BTC-Relativwert) vollständig implementiert und
verifiziert.** Offen bleibt laut ursprünglicher Nutzer-Vorgabe (Design-
Entscheidung 3) eine mehrtägige Beobachtung im echten Betrieb, bevor das
Feature endgültig als abgeschlossen gilt - siehe `extract_notebook_
diagnose.py`-Auswertung als nächster Schritt nach einigen Tagen Laufzeit.

### Nachtrag (2026-07-30): Mehrtägige Beobachtung abgeschlossen - alle drei Bausteine bestätigt

Nach 5 realen Produktionstagen (25.-30.07.) gegen einen frischen Notebook-
Export geprüft, wie in der ursprünglichen Design-Entscheidung 3 vorgesehen:

- **Baustein 1 (BTC-Relativwert):** Korrelationswerte je Symbol plausibel
  und differenziert (TAO 0,63-0,66, KAIA 0,56-0,59, VIRTUAL 0,57, ONDO
  0,29-0,30, KAITO 0,22-0,25, NEAR 0,29-0,31, INJ 0,39, HYPE 0,48) - keine
  Ausreißer.
- **Baustein 3 (Signal-Stabilität):** 144 positiv / 142 negativ über 308
  Signale seit Deploy - gesunde, nicht-entartete Verteilung.
- **Baustein 2 (Volatilitäts-/ATR-Perzentil):** BTC/ETH/LINK/TAO/VIRTUAL/
  HYPE/INJ blieben über alle 5 Tage nahe einem festen Wert (BTC durchgehend
  0, HYPE durchgehend 57, INJ durchgehend 10), während KAIA (0→12), KAITO
  (72→98), NEAR (16→19) und ONDO (15→21) im selben Zeitraum deutliche
  Bewegung zeigten. Zunächst wie ein Fehler wirkend (siehe Abschnitt 4a der
  offenen Beobachtungspunkte), aber durch Kontrollgruppen-Vergleich erklärt:
  die beweglichen Symbole sind exakt die bereits anderweitig dokumentierte
  Altcoin-Rally-Gruppe (siehe [[project_r510_konfidenz_veto_analyse_29_07]])
  - echte Volatilitätsereignisse bei diesen Coins, während BTC/ETH/Majors im
  selben Fenster ruhig blieben. Ein langsam geglätteter (Wilder-ATR)
  Perzentilrang bleibt bei fehlendem Ereignis über 5 Tage erwartbar
  konstant - kein Bug.

**Ergebnis: kein Code-Änderungsbedarf, alle 3 Bausteine bestätigt.
Krypto-Relativwert-Bausteine damit vollständig abgeschlossen** (Design-
Entscheidung 3 erfüllt). Methodik der Kontrollgruppen-Plausibilitätsprüfung
jetzt auch in `Test_und_Verifikationsmethodik.md` Abschnitt 2.7 verankert.

## Nachtrag (2026-07-25, gleicher Tag): Signal-Fazit (`eigene_einschaetzung`) - abschließendes LLM-Synthese-Verdikt, alle 6 Assetklassen mit LLM-Bewertung

Direkt im Anschluss an die Krypto-Relativwert-Bausteine entstandene Idee:
unter der Risikofaktoren-Liste steht jetzt ein zusammenfassendes Fazit -
genau die Frage, die man einem Analysten im Gespräch stellen würde ("würdest
du dieser Empfehlung selbst folgen?"), als eigenes strukturiertes Feld im
Signal. Umgesetzt für ALLE Assetklassen mit LLM-Bewertung: Krypto Spot,
Krypto Hebel, Aktien, Rohstoffe, Themen-ETF, Hedge.

### Design-Grundsatz: keine deterministische Nachkorrektur

Explizite Nutzer-Vorgabe (Zitat, gekürzt): "sollte dies nur LLM sein - wenn
wir hier wieder 'eingreifen' müssen wäre das für mich der Hinweis, dass der
Einsatz der LLM-Abfragen nicht sinnvoll bzw. unsicher ist [...] mehrere
negative Faktoren müssen nicht zwingend das gleiche Ergebnis bringen [...]
die einzelnen Punkte und Gewichtungen soll das LLM selbst durchführen." Das
deckt sich mit der Lehre aus dem Konfidenz-Kollaps (siehe Nachtrag
2026-07-24 oben, `project_konfidenz_prompt_anker_fix.md`): eine starre
Zähl-/Schwellenregel hatte dort genau die granulare Abwägung zerstört, die
eigentlich gewollt war (siehe auch Memory `feedback_llm_synthese_kein_
deterministischer_override.md`). Deshalb gilt für dieses Feld, im
Unterschied zu harten deterministischen Gates wie RM-4/Cash-Veto/CRV-Floor:
**das Werturteil selbst (`folgen`/`kurzfazit`) wird NIE nachträglich
überschrieben oder gedeckelt.** Erlaubt bleibt ausschließlich reine
Daten-INTEGRITÄTS-Validierung (Enum-Wert korrekt, Mindestlänge) - exakt
dasselbe Muster wie beim bestehenden `gegenargument`-Feld.

### Schema und Befüllungs-Reihenfolge

Neues Feld `eigene_einschaetzung` in der JSON-Antwort jedes der 6
Analysten (`agent/krypto/analyst.py` Regel 29, `hebel_analyst.py` Regel 21,
`agent/aktien/analyst.py` Regel 26, `agent/rohstoff/analyst.py` Regel 19,
`agent/themen_etf/analyst.py` Regel 21, `agent/hedge/analyst.py` Regel 16):
```json
"eigene_einschaetzung": {"folgen": "ja|nein|mit_vorbehalt", "kurzfazit": "<1 Satz>"}
```
`mit_vorbehalt` ist bewusst eine echte dritte Option (kein erzwungenes
Binär) - deckt "Setup ist plausibel, aber X macht mich vorsichtig" ab. Das
Feld wird laut Prompt-Regel GANZ ZULETZT ausgefüllt, nachdem `action`,
`confidence_pct`, `gegenargument`, `top_gruende` und `long_reasoning`
bereits feststehen - ein echter Rückblick auf die fertige eigene Analyse
("würde ich selbst dieser Empfehlung folgen?"), keine Wiederholung.

### Validierung (reine Formatintegrität)

`_validate()` in jedem Analysten (gleiche Stelle wie der bestehende
`gegenargument`-Check): `folgen` muss exakt einer von
`("ja", "nein", "mit_vorbehalt")` sein (case-insensitiv, wird normalisiert),
`kurzfazit` muss nach dem Trimmen mindestens 15 Zeichen haben - sonst
`AnalystResponseInvalid`. Kein inhaltlicher Eingriff.

### Diagnostischer Konsistenz-Hinweis (kein Deckel)

Neue reine Funktion `_fazit_konsistenz_hinweis()` in
`agent/krypto/risk_gate.py` (von `hebel_risk_gate.py` und
`agent/hedge/pipeline.py` importiert - Aktien/Rohstoffe/Themen-ETF nutzen
`risk_gate.py::post_check()` bereits direkt und bekommen die Wiring damit
automatisch):
```python
def _fazit_konsistenz_hinweis(folgen, confidence_pct, schwelle_niedrig=55.0, schwelle_hoch=65.0) -> str | None:
    if folgen == "ja" and confidence_pct < schwelle_niedrig:
        return "Fazit 'ja' bei vergleichsweise niedriger eigener Konfidenz - ggf. genauer prüfen."
    if folgen == "nein" and confidence_pct > schwelle_hoch:
        return "Fazit 'nein' trotz vergleichsweise hoher eigener Konfidenz - ggf. genauer prüfen."
    return None  # mit_vorbehalt wird NIE geflaggt - das ist bereits die Zwischenposition.
```
Vergleicht bewusst NUR mit der eigenen `confidence_pct` DESSELBEN Laufs -
nicht mit einer separat gezählten Risikofaktoren-Anzahl, das wäre bereits
eine zweite, primitivere Bewertung. Das Ergebnis landet als reiner
Anzeige-Zusatz (`fazit_konsistenz_hinweis`), ändert `folgen`/`kurzfazit`
nie. Schwellen konfigurierbar über `config.yaml::signal_fazit` (Default
55/65, gemeinsam für alle 6 Assetklassen).

### Persistenz

`database/models.py`: `Signal` und `HebelSignal` je um drei Felder
erweitert (`fazit_folgen`, `fazit_kurzfazit`, `fazit_konsistenz_hinweis`).
`database/db.py::_migrate_signal_fazit_columns()`: additive `ALTER TABLE`
auf `signals` UND `hebel_signals` (gleiches Guard-Muster wie die
Kontrathese-Migration), bestehende Zeilen bleiben unangetastet (NULL in den
drei neuen Spalten). Alle 6 Pipelines (`agent/krypto/pipeline.py`,
`hebel_pipeline.py`, `agent/aktien/pipeline.py`, `agent/rohstoff/pipeline.py`,
`agent/themen_etf/pipeline.py`, `agent/hedge/pipeline.py`) lesen
`eigene_einschaetzung` aus dem validierten LLM-Ergebnis und den gepoppten
`_fazit_konsistenz_hinweis` und reichen alle drei Felder in den jeweiligen
`Signal(...)`/`HebelSignal(...)`-Konstruktor durch.

### Anzeige (App + E-Mail, alle 6 Assetklassen)

Neuer Block direkt unter der Risikofaktoren-Liste (Abschnitt 3), sowohl im
App-Detail-Panel als auch in der E-Mail. Wiederverwendet BEWUSST dieselben
▲/●/▼-Symbole wie die bestehenden Risikofaktoren
(`_FAZIT_SYMBOL = {"ja": "▲", "mit_vorbehalt": "●", "nein": "▼"}`,
`ui/formatting.py::format_fazit_lines()`) - dadurch färbt die bereits
bestehende `classify_detail_line()`/`render_detail_html()`-Pipeline die
neuen Zeilen automatisch korrekt ein, sowohl in der App (Tk-Tags,
`ui/detail_panel.py`) als auch in der E-Mail (HTML-Inline-Styles), ohne
neue Farb-/Tag-Infrastruktur. `ui/signals_view.py` ist die gemeinsame
Detail-Ansicht für Spot UND Aktien/Rohstoffe/Themen-ETF/Hedge - eine Edit
deckt alle vier ab. `ui/hebel_view.py` bekam den identischen Block separat.
E-Mail-seitig analog in `scheduler/background.py::_formatiere_fazit()`,
verdrahtet in `_notify_spot_signal()`, `_notify_hebel_signal()` und
`_notify_multi_asset_signal()` (letztere deckt wieder Aktien/Rohstoffe/
Themen-ETF/Hedge gemeinsam ab).

**Verifiziert:**
1. `_fazit_konsistenz_hinweis()` pur: alle Kombinationen aus `folgen` und
   Konfidenz über/unter beiden Schwellen (inkl. exakter Grenzwerte 55/65,
   die korrekt NICHT auslösen) - Hinweis nur in den beiden echten
   Widerspruchsfällen, `mit_vorbehalt` nie geflaggt, `None`-Eingaben sicher.
2. `_validate()`-Formatintegrität (Krypto-Spot-Analyst stellvertretend
   geprüft, identisches Muster in allen 6 Dateien): fehlendes Feld,
   ungültiger Enum-Wert, zu kurzes `kurzfazit` lösen jeweils
   `AnalystResponseInvalid` mit der korrekten, feldspezifischen Meldung
   aus; gültige Eingabe wird normalisiert (`folgen` klein/getrimmt,
   `kurzfazit` getrimmt).
3. DB-Migrationstest gegen eine Kopie der Produktions-DB (118 Spot- + 5
   Hebel-Signale): additive Migration idempotent, Zeilenzahl unverändert,
   bestehende Zeilen bleiben NULL, neue Werte schreiben/lesen sich über
   `_row_to_signal()`/`_row_to_hebel_signal()` korrekt zurück.
4. Anzeige-Regressionstest: `format_fazit_lines()`/`_formatiere_fazit()`
   liefern für alle drei `folgen`-Werte + optionalen Konsistenz-Hinweis das
   erwartete Symbol/den erwarteten Text; `classify_detail_line()`/
   `render_detail_html()` färben die neuen Zeilen korrekt ein (▲ grün, ●
   grau, ▼ rot, ⚠-Hinweiszeile als Warnung), bestehende Risikofaktoren-
   Legende und -Zeilen unverändert (keine Regression).
5. Gesamt-Import-Check: alle 6 Analysten, alle 6 Pipelines, `risk_gate.py`,
   `hebel_risk_gate.py`, `database/models.py`, `database/db.py`,
   `ui/formatting.py`, `ui/signals_view.py`, `ui/hebel_view.py`,
   `scheduler/background.py` - keine Fehler.
6. `config.yaml::signal_fazit` lädt korrekt (`konsistenz_schwelle_niedrig:
   55`, `konsistenz_schwelle_hoch: 65`).

Echte Betriebsdaten (füllt sich erst mit den nächsten LLM-Läufen) noch
nicht ausgewertet - analog zu den Krypto-Relativwert-Bausteinen ist eine
spätere Durchsicht sinnvoll, ob das LLM tatsächlich differenzierte Fazits
liefert (nicht immer "ja"/reine Kopie von `action`) und ob der
Konsistenz-Hinweis in der Praxis selten/oft auftritt.

## Nachtrag (2026-07-25, gleicher Tag): Kontrathese-Übersetzung Lücke geschlossen - echter HYPE-Fund

Echte E-Mail traf ein: "Hebel TEILVERKAUF HYPE (SHORT)" - für HYPE existierte
zu diesem Zeitpunkt aber NUR eine offene LONG-Position, keine SHORT-Position.
Das Signal war folglich nicht ausführbar (die Mail selbst bestätigte das:
"Short-Positionen werden auf Bitpanda noch nicht unterstützt").

### Root Cause

Die Kontrathese-Übersetzung (siehe Nachtrag 2026-07-24 weiter oben,
`HebelSignal.kontrathese_zu_position`) übersetzt genau diesen Fall - ein
LLM-Vorschlag in der Gegenrichtung zu einer bestehenden Position - in eine
Aktion auf die TATSÄCHLICHE Position. Das Gate dafür
(`hebel_risk_gate.py::post_check_hebel()`) griff bisher aber NUR, wenn das
LLM selbst `action == "ERÖFFNEN"` gewählt hatte:
```python
elif (
    action == "ERÖFFNEN"
    and position_aktuell is not None
    and richtung != str(position_aktuell.richtung).upper()
):
```
`hebel_pipeline.py::generate_hebel_signal()` lädt `position_aktuell` NUR
nach Symbol (`db.get_open_hebel_positions(conn, symbol=asset.symbol)`),
nicht nach Richtung - das LLM sieht also bei jeder Bewertung eines
SHORT-Triggers für HYPE trotzdem die bestehende LONG-Position in den
Fakten. `hebel_analyst.py` Regel 3 listet "Position existiert bereits" als
generische Voraussetzung für NACHKAUFEN/HEBEL_ERHÖHEN/HEBEL_SENKEN/
TEILVERKAUF/SCHLIESSEN, ohne dort explizit auf Richtungs-Gleichheit zu
bestehen - das Modell wählte hier direkt `action="TEILVERKAUF"` (nicht
`ERÖFFNEN`), wodurch der Fall am alten Gate komplett vorbeirutschte und
unübersetzt versendet wurde.

### Fix (zwei Ebenen, wie im Projekt üblich)

1. **Deterministisches Gate erweitert** (`hebel_risk_gate.py:653`): die
   Bedingung prüft jetzt `action != "HALTEN"` statt `action == "ERÖFFNEN"` -
   greift bei JEDER Nicht-HALTEN-Aktion mit Richtungs-Mismatch, nicht nur
   bei ERÖFFNEN. `HALTEN` bleibt bewusst ausgenommen (das LLM sagt bereits
   "keine Aktion", keine Übersetzung nötig).
2. **Prompt-Regel 3 präzisiert** (`hebel_analyst.py`): stellt jetzt
   explizit klar, dass die "Position existiert bereits"-Beschreibungen NUR
   gelten, wenn die eigene `richtung` mit `position_aktuell.richtung`
   übereinstimmt - weicht sie ab, ist die Aktionswahl auf ERÖFFNEN/HALTEN
   beschränkt (Regel 2 gilt unverändert für die Richtungswahl selbst).

### Sorgfalts-Check: keine korrekten Bewertungen gehen verloren

Nutzer-Einwand vor Umsetzung: "das deine Gate-Änderung nicht korrekte
Bewertungen u.U. wegschmeisst". Geprüft und verifiziert:
- Bei ÜBEREINSTIMMENDER Richtung (`richtung == position_aktuell.richtung`,
  der Normalfall) greift die Bedingung unverändert NICHT - kein Einfluss
  auf reguläre NACHKAUFEN/TEILVERKAUF/HEBEL_SENKEN/SCHLIESSEN-Signale.
- Jede vom erweiterten Gate NEU abgefangene Aktion war bei
  Richtungs-Mismatch strukturell NIE ausführbar (keine Position in der
  vom LLM gewählten Richtung vorhanden) - es geht also keine gültige,
  ausführbare Bewertung verloren, sondern ein bereits kaputtes Signal wird
  repariert. Die volle LLM-Analyse (Konfidenz, Begründung, Top-Gründe,
  Gegenargument, Risikofaktoren, Fazit) bleibt unverändert erhalten - nur
  `action`/`richtung` werden nach derselben, bereits am 2026-07-24
  verifizierten Konfidenz-/Zeitfenster-Logik neu berechnet.
- Theoretisches Risiko einer Mehrfach-Positions-Verwechslung
  (`get_open_hebel_positions()` gibt bei mehreren offenen Positionen
  desselben Symbols nur die erste zurück) empirisch geprüft: aktuell hat
  kein Symbol mehrere gleichzeitig offene Positionen, alle 188 historischen
  Positionen sind LONG (Bitpanda unterstützt SHORT-Ausführung derzeit
  ohnehin nicht) - der Fall kann aktuell nicht auftreten.

### Scope-Prüfung (Nutzer-Vorgabe "alle Varianten/Assetklassen")

Per Grep bestätigt: `position_aktuell`/`kontrathese_zu_position` existieren
ausschließlich in `hebel_risk_gate.py`/`hebel_pipeline.py` - kein anderer
Assetklassen-Pfad (Spot/Aktien/Rohstoffe/Themen-ETF/Hedge) hat ein
Richtungskonzept (LONG/SHORT), der Bug kann dort strukturell nicht
auftreten. Kein weiterer Anpassungsbedarf.

**Verifiziert:** bestehendes Testskript `test_kontrathese.py` um 15 neue
Fälle erweitert (alle 5 vormals unabgefangenen Aktionen bei
Richtungs-Mismatch, der reale HYPE-Fall exakt nachgestellt, HALTEN-Mismatch
bleibt unberührt) - 39/39 Checks bestehen, inkl. aller 24 bereits
bestehenden Regressionsfälle unverändert grün.

## Nachtrag (2026-07-25, gleicher Tag): Signale-/Hebel-Tab-Sortierung - Standard-Reihenfolge + gemischte Wertetypen beim Klick-Sortieren

Nutzer-Nachfrage zur aktuellen Standard-Sortierung beider Tabellen deckte
zwei getrennte Punkte auf.

### 1. Standard-Reihenfolge beim Start/Refresh

Empirisch gegen eine echte DB-Kopie geprüft (nicht nur am Code): Hebel-Tab
war bereits korrekt (`created_at` absteigend, neuestes zuerst,
`ui/hebel_view.py::refresh()`). Signale-Tab war dagegen alphabetisch nach
Symbol sortiert (`ui/signals_view.py::_refresh_list()`), nicht chronologisch
- Nutzer-Wunsch: beide Tabellen sollen beim Start die aktuellsten Einträge
oben zeigen. Fix: Signale-Tab sortiert jetzt ebenfalls nach `created_at`
absteigend; Assets ganz ohne Signal fallen automatisch ans Ende (leerer
String als Sortierschlüssel).

### 2. Klick-Sortierung mischte Wertetypen (echter Nutzer-Fund)

`make_sortable()` (`ui/sortable_tree.py`) sortierte bisher JEDE Spalte ohne
`numeric_columns`-Angabe rein alphabetisch als String - betraf beide
Tabellen komplett, da keine von beiden `numeric_columns` gesetzt hatte.
Konkret gefundener Fall: die Hebel-Tab-Spalte "Hebel/Score" zeigt je nach
Zeilentyp ENTWEDER den Hebel-Multiplikator eines echten Signals ("5.0x")
ODER den rohen Score eines noch unbewerteten Kandidaten ("78", ohne "x") -
beim reinen String-Vergleich landete "10.0x" durch die Ziffer "1" VOR
"5.0x", und Werte wie "78" wurden komplett falsch zwischen den "x"-Werten
einsortiert ("Vermischung").

**Fix** (`ui/sortable_tree.py`):
- `_STRIP_RE` entfernt jetzt zusätzlich das "x"-Suffix, sodass
  `_numeric_key()` "5.0x" korrekt als 5.0 parst (bisheriges Verhalten für
  alle anderen `numeric_columns` unverändert - per Regressionstest
  bestätigt, siehe unten).
- Neue Funktion `_date_key()` + neuer `date_columns`-Parameter für
  `make_sortable()`: Datumsspalten ("YYYY-MM-DD HH:MM") sortierten für sich
  genommen zwar bereits korrekt chronologisch als String, aber '-' (kein
  Wert) landete je nach Sortierrichtung inkonsistent mal vorne, mal hinten
  (ASCII: '-' < Ziffern) statt wie bei Zahlen IMMER ans Ende.
- `ui/hebel_view.py`: `numeric_columns={"hebel_score"}`,
  `date_columns={"zeitpunkt"}`.
- `ui/signals_view.py`: `date_columns={"berechnet"}`.

**Verifiziert:** `_numeric_key()`/`_date_key()` pur (Hebel-Suffix, fehlende
Werte); echter Tk-Smoke-Test mit exakt der gemeldeten Mischung (Signal
"5.0x"/"10.0x"/"-", Kandidat "78") - auf-/absteigend korrekt für beide neuen
Spalten; Regressionstest bestätigt `ui/marktscan_view.py` (`score`) und
`ui/screener_view.py` (`preis`/`marktkap`/`aenderung`) unverändert korrekt
(kein "x" in deren Werten, von der `_STRIP_RE`-Erweiterung nicht betroffen).

## Nachtrag (2026-07-25): #333 Schicht 2 + #334 Stufe 2 - kategorienübergreifende LLM-Synthese und objektiv gegatete Screener-Gewichtung

**Auslöser:** Schicht 1 von #333 (deterministische Mehrfach-Mechanismus-
Kombination je Kategorie, siehe Nachtrag vom 2026-07-24) betrachtet jede
Kategorie IMMER isoliert - nie im Vergleich zu den anderen. Nutzer-Wunsch:
ein täglicher LLM-Call soll ALLE Kategorien gemeinsam betrachten und
signalisieren, welche Assetklassen je nach Marktphase gerade Rückenwind/
Gegenwind bekommen, mit sanftem Ein-/Ausschleichen bei graduellen
Verschiebungen, aber schneller Reaktion bei abrupten Wechseln. In derselben
Runde wurde zusätzlich #334 Stufe 2 (bisher bewusst zurückgestellte
Screener-Score-Gewichtung) umgesetzt, weil beide Bausteine laut Nutzer
"zusammenpassen" mussten.

**Tragendes Prinzip (löst die ursprüngliche 2026-07-21-Prozyklik-Sorge
strukturell, siehe [[project_schwerpunkt_diversifikation]]):** die frühere
Idee, Stufe 2 nur für "unverdächtige" Kategorien zu bauen und Technologie &
KI kategorisch auszuschließen, wurde damals explizit verworfen zugunsten
eines einzigen, universell auf ALLE Hauptgruppen angewendeten objektiven
Prüf-Mechanismus (`compute_these_abgleich()`, bereits seit Schicht 1
vorhanden). Beide neuen Bausteine dieser Runde bauen ausschließlich auf
dieser bereits vorhandenen Funktion auf - keine neue Datenquelle, keine
Trend-/Popularitäts-Gewichtung.

### #333 Schicht 2 - `agent/kategorie_synthese.py` (neu)

Neuer täglicher Job `kategorie_synthese_job` (`scheduler/background.py`,
Cron **06:15, bewusst VOR** `kategorie_vorschlaege_job` um 06:30 - Schicht 1
liest das Tagesergebnis für die Gleichzeitigkeits-Moderation unten, das muss
deshalb vorliegen, BEVOR Schicht 1 läuft). Baut je prüfbarer Kategorie einen
Fakten-Block (aktuelle These, objektive Einschätzung, Tracker-Alter,
Persistenzziel, `ist_heute_fall_a_reif`) und lässt EIN LLM (Mistral→Groq→
Gemini-Fallback-Kette, gleiche Philosophie wie `budget_allocator.py`, hier
als einfache sequentielle Kette ohne Tagesbudget-Buchhaltung) je Kategorie
zwei zusätzliche Einordnungen liefern:

- `phase_charakter`: `sanfter_uebergang` | `schneller_wechsel` | `stabil` -
  Letzteres NUR bei einem in diesem Zyklus neu erreichten, klar akuten
  Schwellenwert (z. B. VIX-Sprung, COT neu "gedrängt"), nicht für "der Trend
  hält an".
- `prioritaet_rang`: nur unter den heute Fall-A-reifen Kandidaten vergeben.

Validierung über `_validate_kategorie_synthese()` (gleiches Muster wie
`_validate_hebel()`: Enum-Prüfung, Mindestlänge, eindeutige Ränge, harte
Pflicht, dass JEDE Fall-A-reife Kategorie einen Rang bekommt). Ergebnis
gecacht in neuer Tabelle `kategorie_synthese_ergebnis` (ein Datensatz/Tag,
gleiches Cache-Prinzip wie `makro_analog_ergebnis`).

**Wirkung auf Fall A/B (macht Schicht 2 nicht-passiv, statt #334 Stufe 2
vorzuziehen):**
- **Gleichzeitigkeits-Moderation** (`agent/kategorie_vorschlaege.py::
  _bestimme_gesperrte_fall_a_kandidaten()`): werden an einem Tag mehr
  Fall-A-Kandidaten reif, als innerhalb der Richtgröße (`kategorie_
  vorschlaege.richtgroesse_max_aktive_thesen`, Default 6) noch Platz haben,
  entscheidet die Schicht-2-Rangfolge, welche automatisch übernommen werden
  - der Rest landet als offener Vorschlag (`these_id=None`, `status='offen'`)
  zur manuellen Bestätigung statt automatischer Anlage.
- **Schnell-Pfad** (`_verarbeite_signal()`, NUR Fall B): eine als
  `schneller_wechsel` markierte Kategorie überspringt die normale
  Persistenzfrist - spiegelt exakt das bereits etablierte Hebel-Kontrathese-
  Hochkonfidenz-Muster (`hebel_risk_gate.py::KONFIDENZ_SCHWELLE_HOCH`,
  sofortige Reaktion statt Zeitfenster-Bestätigung).
- **Aktive Benachrichtigung** (`scheduler/background.py::
  _notify_schneller_wechsel()`): E-Mail NUR für `schneller_wechsel`-
  Einträge, Cooldown-geschützt (`benachrichtigung.email.schneller_wechsel_
  email_cooldown_minuten`, Default 360 Min - der eigentliche Spam-Risiko-Fall
  ist ein App-Neustart während des Tages, nicht der Job selbst, der nur 1x/
  Tag läuft).
- **GUI**: neues Panel "Tages-Synthese (KI, Schicht 2)" im Schwerpunkte-Tab
  (`ui/thesen_view.py`), Rangliste mit Phasen-Badge (⚡/»/●) + Tooltip. Das
  bestehende "Offene Änderungsaufforderungen"-Panel zeigt jetzt Fall A UND
  Fall B gemeinsam (vorher zeigte es Fall-A-Einträge gar nicht an - ein
  echter, durch diese Änderung erstmals relevanter Gap, da Fall A bisher
  IMMER sofort automatisch anlegte und nie `status='offen'` erreichte).

**P-8 durchgängig:** liegt für den aktuellen Tag kein Schicht-2-Ergebnis vor
(Job noch nicht gelaufen/fehlgeschlagen/kein LLM-Client konfiguriert),
verhalten sich Fall A/B und der Screener exakt wie vor dieser Änderung - kein
harter Block irgendwo.

### #334 Stufe 2 - objektiv gegatete Screener-Score-Gewichtung

`agent/aktien/screener.py::_kategorie_score_bonus()` - NUR für ETF-
Kandidaten (`scan_etf_candidates()`, tragen bereits Kategorie-Tags; Einzel-
aktien bleiben bewusst außen vor, da yfinance-Screens keine Kategorie-Daten
liefern, keine erfundenen Kategorien). Bonus/Malus hängt AUSSCHLIESSLICH an
`compute_these_abgleich()`s objektiver Einschätzung, NICHT an der bloßen
Existenz einer aktiven These (das bleibt Stufe 1, unverändert) und NICHT an
Trend/Beliebtheit:

- `gestuetzt` → moderater Bonus (`kategorie_score_gewichtung.bonus_
  gestuetzt`, Default 5.0).
- `widerspricht` → moderater Malus (`malus_widerspricht`, Default 5.0) -
  schließt eine echte Lücke: die bestehende Stufe-1-Hervorhebung (Watchlist/
  Diversifikation/Screener) ignoriert `richtung`/die objektive Einschätzung
  bis dahin komplett - eine objektiv widerlegte These wurde genauso
  hervorgehoben wie eine gestützte.
- `neutral`/`nicht_pruefbar`/keine These → keine Anpassung.
- Schicht-2-`schneller_wechsel` verstärkt Bonus/Malus (`schnell_wechsel_
  multiplikator`, Default 2.0) - Screener-Neusortierung ist risikoarm/
  reversibel, darf deshalb schneller/stärker reagieren als eine echte
  These-Änderung.

Wirkt als sekundärer Sortierschlüssel INNERHALB der bestehenden Stufe-1-
Partition (`ui/screener_view.py::_on_scan_done()`, unverändert die äußere
Sortierebene) - Ergänzung, keine Ablösung der bisherigen UX. Zeilen-Tooltip
zeigt die konkrete Begründung.

**Bereits vorhandene Infrastruktur (nicht neu gebaut):** Stufe-1-
Hervorhebung (#343) verbindet jede aktive These bereits automatisch mit
Watchlist-Sortierpriorität, Diversifikations-Marker UND Screener-
Vornesortierung (auch für Kandidaten, die noch nicht in der Watchlist sind).
Screener läuft bereits automatisch alle 60 Min (#346/#347). Jede Fall-A/B-
Änderung wirkt dadurch bereits "zeitgerecht" weiter, ohne neuen
Verdrahtungscode - das war die Antwort auf die Nutzer-Nachfrage "wirkt sich
das auch auf bestehende Assets und den Screener aus, sonst ist es nur
passiv?".

**Verifiziert:** 20 synthetische Checks (Validator-Fehlerfälle inkl. der
harten Fall-A-Rang-Pflicht, Gleichzeitigkeits-Moderation mit knappem Budget,
Schnell-Pfad-Bypass vs. normale Persistenz, Score-Bonus für alle 4
Einschätzungswerte + Multiplikator + deaktiviert + kategorielose Aktie,
P-8-Regression ohne/mit veraltetem Schicht-2-Ergebnis, Import-Regression) -
alle bestanden. Echter Mistral-Lauf gegen eine Kopie der Produktions-DB:
19 Kategorien korrekt eingeordnet, Begründungen nennen durchgängig konkrete
Rohwerte aus dem Fakten-JSON (COT-%, DXY, VIX, S&P500-Drawdown,
Analystentrend, Insider-Aktivität) - keine Halluzination in der Stichprobe.
Echter Screener-Scan gegen dieselbe Kopie: 209 reale ETF-Kandidaten, Bonus
korrekt 0.0 für alle (aktuell keine aktiven Thesen im System), Fallback auf
die bisherige alphabetische Sortierung funktioniert wie vorgesehen (P-8 mit
echten Daten bestätigt). Tk-Smoke-Test für das neue GUI-Panel (Fall A + Fall
B gemeinsam gerendert, Übernehmen/Ablehnen für beide Fälle, Tages-Synthese-
Rangliste inkl. Phasen-Badges).

## Nachtrag (2026-07-25): Echter KAIA-Hebel-Signal-Review (7 Funde) + INJ-Signal-Stabilität-Diskussion

Nutzer bat um Expertenreview eines real eingetroffenen KAIA-Hebel-ERÖFFNEN-
LONG-Signals (Screenshots) sowie eine anschließende Grundsatzdiskussion zur
Signal-Stabilität anhand eines INJ-Falls. Ergab 8 unabhängige Änderungen,
nach der Standard-Vorgabe (siehe `feedback_alle_asset_varianten_
konsistenzpruefung`) auf alle betroffenen Varianten (Hebel UND Spot/Aktien/
Rohstoffe/Themen-ETF, wo zutreffend) geprüft.

**1. Technische Konfluenz ignorierte die Richtung (hoch, hebel_risk_gate.py
+ risk_gate.py).** Eine "eindeutige Tendenz" wurde bisher IMMER als positiv
gewertet, egal ob sie der Position widerspricht - bearish-Konfluenz bei
einem LONG wurde fälschlich als ▲ ("unterstützt die Empfehlung") gezeigt.
Fix: Vergleich gegen `richtung` (Hebel: bullish stützt LONG/bearish stützt
SHORT und umgekehrt; Spot-Familie: nur BUY-Aktionen betroffen, erwartete
Tendenz ist dort immer bullish).

**2. Funding-Kosten-Symbol ignorierte zulasten/zugunsten (mittel,
hebel_risk_gate.py).** Das Icon hing bisher nur an der Betragshöhe, nicht
daran, ob der Satz der Position nützt oder schadet - ein hoher Satz
"zugunsten" (z.B. negative Rate bei LONG) wurde faelschlich als Warnsignal
(▼) markiert. Fix: `positiv` bei zugunsten, `negativ` nur bei zulasten UND
hoher Betragshöhe, sonst `neutral`. Zusätzlich: das Vorzeichen der
zulasten/zugunsten-Berechnung selbst berücksichtigte `richtung` nicht (nur
für LONG korrekt, bei SHORT invertiert falsch) - jetzt mit
`funding_richtungs_vorzeichen` korrigiert.

**3. LLM zitierte Funding-Kosten in kaum interpretierbarer Einheit
(hebel_analyst.py).** Regel 9 verlangte bisher die stündliche Rate
("-0,02411% pro Stunde") in `key_risks` - für einen Menschen kaum
einzuordnen. Neuer Fakt `funding_rate_aktuell_prozent_pro_tag` (dieselbe
Rohrate ×24, kein neuer Datenpunkt), Regel 9 zitiert jetzt ausschließlich
diesen Tagessatz und verweist auf den bereits vorhandenen EUR/Tag-Betrag in
Abschnitt 3 (Konklusion), statt ihn zu duplizieren.

**4. Fazit-Prompt-Anker kollabierte auf einen Stehsatz (hoch, alle 6
Analyst-Dateien: Krypto Spot+Hebel, Aktien, Rohstoffe, Hedge, Themen-ETF).**
Echte Daten zeigten: 15/15 aktuelle Hebel-Signale mit Fazit waren
"mit_vorbehalt" (nie "ja"/"nein"), 5 davon nutzten fast wortgleich die im
Prompt gegebene Beispielformulierung "Setup ist plausibel, aber etwas macht
mich vorsichtig" - klassischer Prompt-Anker-Effekt (gleiches Muster wie der
Konfidenz-Anker-Fund vom 24.07.). Fix: das wörtliche Beispiel aus der Regel
entfernt, stattdessen explizite Anweisung, dass "mit_vorbehalt" kein
bequemer Standardfall ist und `kurzfazit` mit konkreten, signalspezifischen
Zahlen begründet werden muss statt einer Floskel.

**5. Signal-Stabilität: Kategoriewechsel-Zählung erzeugte einen
strukturellen Fehlalarm (hoch, agent/krypto/signal_stabilitaet.py, echter
INJ-Fund, Nutzer-Grundsatzdiskussion).** Die alte Logik zählte JEDEN rohen
Übergang - ein einzelner Ausflug in eine aktive Kategorie, umrahmt von
Neutral (der normale Lebenszyklus "abwarten → einmal handeln →
beobachten"), erzeugte dabei IMMER genau 2 Übergänge und wurde damit
fälschlich als instabil gewertet, obwohl nur eine einzige Entscheidung
getroffen wurde - bei jedem Signal, das irgendwann aktiv wird, praktisch der
Regelfall statt der Ausnahme. Neue Funktion `_aktive_kategorie_wiederholt()`:
komprimiert die Kategoriefolge zu "Runs" und prüft, ob Aufbau ODER Abbau in
MEHR ALS EINEM getrennten, unterbrochenen Abschnitt auftaucht - nur DAS ist
echtes Hin-und-Her (ursprüngliches LINK-Vorbild: wiederholtes
Eröffnen/Zurückziehen). Verifiziert: INJ-Fall jetzt korrekt stabil, LINK-
Flip-Flop weiterhin korrekt instabil, ein normaler Trade-Zyklus
(Eröffnen→Teilverkauf→Halten, keine Neutral-Umrahmung) ebenfalls korrekt
stabil.

**6. Neuer Risikofaktor "Richtungswende" (hebel_risk_gate.py + risk_gate.py,
agent/krypto/signal_stabilitaet.py::juengste_richtungswende()).** Aus der
INJ-Diskussion hervorgegangen: eine ECHTE Richtungswende (Aufbau↔Abbau) ist
immer bemerkenswert, unabhängig vom Signal-Stabilität-Gesamturteil - jetzt
ein eigener, eigenständiger Faktor statt Nebensatz. Bewusst KEINE
Uhrzeit-Schwelle (Nutzer-Diskussion: Krypto handelt 24/7, Volatilität ist
pro Coin sehr unterschiedlich, ein fixer Zeitwert wäre geraten) - stattdessen
ATR-relative Kursbewegung seit der vorherigen aktiven Kategorie
(`richtungswende_atr_schwelle_relativ`, Startwert 0.5, noch nicht an echten
Fällen kalibriert): ▼ wenn die Bewegung darunter bleibt (Wende vermutlich
noch Rauschen), ● wenn bestätigt. Preis-Rekonstruktion über die bereits
vorhandene Tages-Kurshistorie (`_preis_am_datum()`), kein neuer API-Call.

**7. Liquiditätszonen-Chart: USD/EUR-Entscheidung neu durchdacht
(agent/krypto/liquidity_zones.py, ui/liquidity_chart.py, hebel_pipeline.py,
pipeline.py).** Der Chart zeigte bisher bewusst USD (Entscheidung vom
25.07. selbst, Commit f4e9c0e: keine historischen Tages-FX-Kurse
verfügbar). Nutzer-Nachfrage deckte eine elegantere Lösung auf: derselbe
`eur_usd_fx_rate`, der bereits für Liquidationspreis/Eigenkapitalbedarf/
Funding-Kosten in EUR verwendet wird, wird jetzt zusätzlich EINMALIG zum
Signal-Erstellungszeitpunkt im `liquiditaetszonen`-Fakt selbst eingefroren
(`liquiditaetszonen_fakt(..., eur_usd_fx_rate=...)`). `render_
liquiditaetszonen_chart()` rechnet damit intern konsistent auf EUR um
(Zonen, Kursverlauf, beide Preislinien) - App (auch Tage später erneut
geöffnet) und die bereits verschickte E-Mail zeigen dadurch immer denselben
EUR-Wert, kein Live-Nachschlagen/Drift. Ohne eingefrorenen Kurs (ältere
Signale, EURCV-Abruf fehlgeschlagen) bleibt der Chart bei USD (P-8).

**8. E-Mail-Graufarbe nachgedunkelt (ui/formatting.py).** Der neutrale
Grauton (`risk_neutral`/`fazit_neutral`/`legend`) war mit `#666666` in der
echten Gmail-Darstellung teils schwer lesbar - auf `#4a4a4a` nachgedunkelt
(Kontrast zu Weiß steigt von ~5,7:1 auf ~8,4:1). Betrifft ausschließlich die
E-Mail-HTML-Variante, nicht das App-Detail-Panel (eigenes, Theme-
abhängiges Tk-Tag-System).

**Zusätzlich (kleinere UI-Nachbesserungen, aus derselben Runde):**
Konfidenzwerte werden jetzt direkt über jedem Punkt im Signal-Stabilität-
Sparkline-Chart angezeigt (`ui/signal_stabilitaet_chart.py`).

**Verifiziert:** Compile-Check aller 17 geänderten Dateien, konsolidierter
Regressionstest (INJ stabil, LINK-Flip-Flop weiterhin instabil, Technische
Konfluenz bearish/LONG=negativ, Funding-Kosten zugunsten=positiv,
Richtungswende-Erkennung, Liquiditätszonen-Chart mit/ohne eingefrorenem
Kurs) - alle bestanden. Import-Regressionscheck über alle betroffenen
Module (Hebel+Spot-Pipelines, alle 6 Analyst-Module, beide Chart-Renderer).

**Warum:** ausgelöst durch einen einzelnen, vom Nutzer als Experte
angeforderten Signal-Review (KAIA) plus eine daran anschließende, bewusst
in mehreren Runden geführte Grundsatzdiskussion (INJ) - kein einzelner
Fund, sondern ein methodisches Vorgehen (Diskussion vor Umsetzung, siehe
Punkte 5-7 oben, wo der Nutzer explizit auf "das ist mir zu schnell/
ungenau" bestand, bevor Code geändert wurde).

## Nachtrag (2026-07-26): Z.ai-Gegenprüfungslogik - unabhängiger Konsistenz-Check (Hard Facts vs. eigene Begründung), Hebel-only, rein beobachtend

Nutzer-Idee: Z.ai (bisher Teil der automatischen Fallback-Kette in
`budget_allocator.py`, aber praktisch selten genutzt, da Mistral/Groq/Gemini
meist ausreichen) aus dieser Rolle lösen und stattdessen für eine kleine,
dedizierte zweite Aufgabe verwenden - eine unabhängige Gegenprüfung, ob die
vom Primär-Modell selbst gelieferte Kurzbegründung (`short_reasoning`) den
harten, deterministisch berechneten Fakten widerspricht.

### Design-Grundsatz: keine zweite Handelsentscheidung, keine externe "Meinung"

Der Nutzer schlug zunächst vor, Z.ai zusätzlich zu den Hard Facts auch sein
eigenes "Wissen" (z.B. Nachrichtenlage, "neuer Investor bei Asset X")
einbeziehen zu lassen, um der teils deterministisch wirkenden Antwortqualität
mehr Tiefe zu geben. Nach Rückfrage/Abwägung: verworfen wegen Halluzinations-
Risiko (Z.ai hat keinen echten, aktuellen Nachrichtenzugriff, würde also
plausibel klingende, aber ggf. erfundene "Fakten" einbringen). Stattdessen
umgesetzt: ein reiner Konsistenz-Check zwischen der eigenen Begründung des
Primär-Modells und den bereits vorhandenen harten Fakten - Z.ai bekommt keine
Rolle als zweiter Entscheider, sondern rein als Prüfinstanz für innere
Widerspruchsfreiheit. Diese Umformulierung wurde vom Nutzer ausdrücklich
bestätigt ("trifft es genau"), mit der zusätzlichen Vorgabe, bekannte
LLM-Bias-/Anker-Probleme von vornherein einzukalkulieren.

### Live-Kalibrierung gegen die echte Z.ai-API (nicht nur angenommen)

1. `response_format={"type": "json_object"}` ist Pflicht - ohne dieses Feld
   verpackt Z.ai die Antwort gelegentlich in Markdown-Codefences statt reinem
   JSON (Parse-Fehler in 1 von 3 Testläufen ohne das Feld, danach 3/3 sauber
   mit dem Feld).
2. Sykophantie-/Überzeugungs-Bias getestet: ein bewusst überzeugend
   formuliert, aber inhaltlich falscher Begründungstext wurde trotzdem korrekt
   als Widerspruch erkannt.
3. Fehlender-Kontext-Fehlalarm getestet: ein Begründungstext mit Bezug auf
   Informationen außerhalb der gegebenen Fakten wurde korrekt NICHT als
   Widerspruch gewertet.
4. Antizyklik-Verträglichkeit getestet: ein Begründungstext, der gegenläufige
   Fakten offen benennt und bewusst dagegen argumentiert (Kernprinzip der
   projekteigenen Antizyklisch-Regeln), wurde korrekt als konsistent gewertet.
5. Persona-Framing verworfen: eine Testvariante mit expliziter
   "Risikomanager mit Fokus auf Selbstüberschätzung"-Rolle lieferte in beiden
   Testfällen (sauber/überzogen) IDENTISCHE Urteile wie die neutrale Formulierung,
   war aber messbar langsamer (47-50s vs. 26-35s) - kein Erkennungsvorteil,
   echter Latenzverlust. Entscheidung: neutrale Rahmung ohne Persona.
6. Kein im Prompt eingebettetes Beispiel - bewusst zur Vermeidung des bereits
   dokumentierten Anker-Kollaps-Fehlers (Regel 22/13, siehe Nachtrag
   2026-07-24 "Gates-Kalibrierung").

Typische Antwortzeit: 12-25s (eine reichere Faktenmenge kostet live verifiziert
keine zusätzliche Zeit gegenüber einer minimalen Menge).

### Architektur-Falle erkannt und korrigiert: echte Entkopplung statt bloßer Umordnung

Erster Entwurf platzierte den Z.ai-Call synchron innerhalb von
`generate_hebel_signal()`, nach dem DB-Insert, aber noch vor `return signal`.
Bei genauerer Prüfung (ausgelöst durch Nutzer-Hinweis auf den Z.ai-Timeout):
der `on_signal_ready`-E-Mail-Callback (`budget_allocator.py`, siehe
`project_email_latenz_fix_batch_notification.md`) feuert erst, NACHDEM
`generate_hebel_signal()` tatsächlich zurückkehrt - eine Platzierung "nach dem
Insert, aber noch in der Funktion" hätte die Rückgabe der Funktion und damit
den E-Mail-Versand um bis zu 150s (`api/zai.py::REQUEST_TIMEOUT_SECONDS`)
verzögert und genau die Latenz-Regression wieder eingeführt, die dieser Fix
bereits einmal behoben hatte. Korrektur: echte Entkopplung über einen
Hintergrund-Thread (`threading.Thread(daemon=True)`) mit eigener,
frisch geöffneter DB-Verbindung (`db.get_connection()` - sqlite3-Verbindungen
sind nicht Thread-sicher teilbar, analog zum bestehenden `ThreadPoolExecutor`-
Muster aus dem yfinance-Fix). `generate_hebel_signal()` kehrt jetzt exakt so
schnell zurück wie vor dieser Änderung; die Konsistenzprüfung und der
DB-Update laufen vollständig asynchron danach ab, begrenzt nur durch Z.ais
eigenen 150s-Timeout.

### Umsetzung

- `agent/krypto/gegenpruefung.py` (neu): `baue_fakten()` (schmale Faktenmenge:
  symbol/richtung/action/confidence_pct/rsi/trend/regime/funding-Vorzeichen/
  technische Konfluenz/Optionsmarkt-Skew), `pruefe_konsistenz()` (P-8, fängt
  Netzwerkfehler und ungültige Antworten ab, gibt `None` zurück statt zu
  werfen).
- `database/models.py` + `database/db.py`: zwei neue Felder auf `HebelSignal`
  (`zai_gegenpruefung_urteil`, `zai_gegenpruefung_kurzbegruendung`), additive
  Migration, neue Funktion `update_hebel_signal_zai_gegenpruefung()` (Post-
  Insert-Update, da der Wert erst nach dem asynchronen Z.ai-Call vorliegt).
- `agent/krypto/hebel_pipeline.py`: `_zai_gegenpruefung_im_hintergrund()`
  (Hintergrund-Thread-Ziel, eigene DB-Verbindung, P-8 doppelt abgesichert),
  Dispatch am Ende von `generate_hebel_signal()` nur wenn `zai_client is not
  None`.
- `agent/krypto/budget_allocator.py`: Z.ai aus allen 3 automatischen
  Fallback-Ketten (Hebel-Kandidaten, Marktscan-Writeup, Spot-Rotation)
  entfernt, stattdessen als `zai_client`-Parameter an `generate_hebel_signal()`
  durchgereicht (Mistral- und Gemini-Zweig). Die bestehende Z.ai-Budget-
  Tracking-Maschinerie (`zai_taegliches_budget` etc.) ist dadurch vestigial
  (meldet dauerhaft 0/False für die Primär-Generierung) - bewusst nicht
  entfernt, um diese Änderung im Scope zu halten (dokumentierter, niedrig
  priorisierter loser Faden).

### Phase 1 (aktueller Stand): rein beobachtend

`urteil`/`kurzbegruendung` werden gespeichert, aber nicht als Risikofaktor
angezeigt, nicht als Gate verwendet, beeinflussen `action`/`richtung`/
`confidence_pct` in keiner Weise (siehe `feedback_llm_synthese_kein_
deterministischer_override`). Ob ein Gate jemals sinnvoll wäre, hängt davon
ab, ob sich diese Gegenprüfung über Zeit als tatsächlich treffsicher erweist
(Nutzer-Position: "eher zu bezweifeln, es sei denn die Gegenprüfung ist so
erfolgreich, dass dies tatsächlich als Modell dienen kann").

Scope v1: nur Hebel (analog zur Deribit-Optionsmarkt-Anreicherung).

**Verifiziert:** Compile-Check, voller Import-Regressionscheck (`main.py`,
`scheduler/background.py`, `budget_allocator.py`, `hebel_pipeline.py`),
additive DB-Migration gegen echte Produktions-DB angewendet, End-to-End-
Synthesetest (echter DB-Insert, simulierter langsamer Z.ai-Call via
Hintergrund-Thread, Dispatch bestätigt nicht-blockierend in <1ms, DB-Update
nach Thread-Abschluss verifiziert).

**Notebook-Analyse ergänzt** (`extract_notebook_diagnose.py`):
`zai_gegenpruefung_urteil`/`zai_gegenpruefung_kurzbegruendung` zu
`_HEBEL_SIGNAL_SPALTEN` ergänzt sowie neue Aggregat-Sektion
`zai_gegenpruefung_verlauf` (Zählung konsistent/widerspruch samt
Begleitwerten für spätere Korrelation mit dem tatsächlichen Signal-Ausgang,
analog zum Deribit-Cross-Check) - echter Lauf gegen die Produktions-DB
bestätigt (aktuell 0 Einträge, da das Feature gerade erst gebaut wurde).

## Nachtrag (2026-07-26, später): Z.ai-Gegenprüfung um unabhängigen Richtungs-Abgleich erweitert + sichtbar in App/E-Mail

Erweitert die obige Gegenprüfungslogik direkt am selben Tag, ausgelöst durch
eine Rückfrage des Nutzers, wo das Z.ai-Urteil im E-Mail-Text überhaupt zu
sehen sei (bisher: nirgends, Phase 1 war bewusst rein beobachtend, nur in der
DB gespeichert). Bei der Gelegenheit stellte sich heraus, dass der Nutzer sich
an eine frühere Absprache erinnerte, die von der tatsächlich umgesetzten
abwich - direkter Transkript-Abgleich (nicht nur Erinnerung) bestätigte: was
tatsächlich vereinbart und mit "trifft es genau" bestätigt wurde, war ein
reiner Text-vs-Fakten-Konsistenz-Check (siehe oben) - was der Nutzer jetzt
zusätzlich wollte, war ein echtes JA/NEIN, ob Z.ai *unabhängig* zur selben
Richtung (LONG/SHORT) kommt wie das Primär-Modell. Nutzer-Entscheidung nach
kurzer Abwägung: **beide Prüfungen als Paket**, nicht als Ersatz füreinander.

### Zwei getrennte Z.ai-Calls, bewusst NICHT ein kombinierter Call

Der naheliegende erste Entwurf (ein Call, der beides zugleich beantwortet)
wurde vor jeder Code-Zeile verworfen: `baue_fakten()` enthält bereits
`richtung`/`action`/`confidence_pct` als Fakt. Würde dieselbe Faktenmenge auch
für die Richtungsableitung verwendet, bekäme Z.ai die gesuchte Antwort
praktisch vorgegeben (Echo-/Anker-Effekt) - der zweite Check wäre wertlos, da
er keine wirklich unabhängige zweite Meinung mehr wäre. Lösung: ein zweiter,
schmalerer Fakten-Baustein `baue_objektive_fakten()` (identisch zu
`baue_fakten()`, aber OHNE `richtung`/`action`/`confidence_pct`), nur für den
neuen Call `leite_eigene_richtung()` verwendet. Die eigentliche
Übereinstimmungs-Prüfung (`uebereinstimmung = "ja"|"nein"`) wird NICHT vom LLM
selbst beurteilt, sondern deterministisch in Python berechnet (Vergleich
`eigene_richtung == primaer_richtung`) - robuster als eine dritte Frage an ein
LLM, ob es "übereinstimmt". `NEUTRAL` zählt wie jede andere Abweichung als
"nein" (keine Sonderbehandlung, Nutzer-Entscheidung).

### Live-Kalibrierung: echte, nicht temperaturbedingte Antwort-Varianz gefunden

Wiederholte identische Grenzfall-Faktensets (bearisher Trend + überverkaufter
RSI als Gegen-Indikator) ergaben bei `temperature=0.2` 5/6 SHORT zu 1/6
NEUTRAL, bei `temperature=0.0` 4/6 SHORT zu 2/6 NEUTRAL - die Varianz
verschwindet bei Temperatur 0 NICHT, ist also keine Sampling-Eigenart, sondern
echte Modell-Unsicherheit beim Abwägen widersprüchlicher Signale. Per
`AskUserQuestion` mit drei Optionen zur Entscheidung vorgelegt (Prompt
nachschärfen / Rauschen akzeptieren / Frage anders stellen) -
**Nutzer-Entscheidung: Rauschen akzeptieren, keine Prompt-Nachschärfung**,
ausdrücklich unter Verweis auf die bereits dokumentierte Anker-Kollaps-Gefahr
bei übermäßig spezifizierten Prompts (Regel 22/13, siehe Nachtrag 2026-07-24
"Gates-Kalibrierung"). Die beobachtete Inkonsistenz wird als Teil dessen
behandelt, was über Zeit beobachtet werden soll, statt weg-konstruiert zu
werden.

### Umsetzung

- `agent/krypto/gegenpruefung.py`: `baue_objektive_fakten()`,
  `SYSTEM_PROMPT_RICHTUNG`, `leite_eigene_richtung()` (P-8, validiert
  `eigene_richtung` gegen `{LONG, SHORT, NEUTRAL}`).
- `database/models.py` + `database/db.py`: drei neue `HebelSignal`-Felder
  (`zai_eigene_richtung`, `zai_uebereinstimmung`, `zai_richtung_kurzbegruendung`),
  additive Migration gegen die echte Produktions-DB angewendet und verifiziert.
  `update_hebel_signal_zai_gegenpruefung()` um die drei Parameter erweitert -
  Docstring warnt jetzt explizit davor, die Funktion zweimal pro Datensatz
  aufzurufen (würde den ersten Aufruf durch die Default-`None`-Werte des
  zweiten stillschweigend überschreiben).
- `agent/krypto/hebel_pipeline.py`: `_zai_gegenpruefung_im_hintergrund()` führt
  beide Z.ai-Calls sequenziell im selben Hintergrund-Thread aus, berechnet
  `uebereinstimmung` deterministisch, schreibt alle 5 Felder in EINEM
  `db.update_...()`-Aufruf (verhindert das oben genannte Überschreiben bei
  Teilfehlschlägen - nur wenn BEIDE Calls fehlschlagen, entfällt der Update
  komplett).
- `ui/formatting.py`: `format_zai_gegenpruefung_lines()` (zwei Zeilen, gleiche
  ▲/▼-Symbolik wie Risikofaktoren, farbig aber NICHT fett - Abstufung
  Abschnitts-Header > Fazit > Risikofaktoren/Z.ai bleibt erhalten). Bei der
  Gelegenheit zusätzlicher, unabhängiger Nutzer-Wunsch umgesetzt: bei der
  Fazit-Zeile ist jetzt nur noch das Wort "Fazit:" unterstrichen, nicht mehr
  die ganze Zeile (`_split_fazit_label()`, zwei HTML-Spans für die E-Mail,
  zwei Tk-Tags mit Bereichs-Split für die App - Tk mischt Font-Eigenschaften
  überlappender Tags nicht, daher zwei vollständig eigene Font-Objekte statt
  eines gemeinsamen).
- `ui/detail_panel.py`: neue `fazit_label_*`-Tags (fett+unterstrichen), nach
  den bestehenden `fazit_*`-Tags (fett only) konfiguriert - später
  konfigurierte Tags gewinnen bei Tk für überlappende Zeichenbereiche.
- `ui/hebel_view.py`: `format_zai_gegenpruefung_lines()`-Aufruf direkt nach dem
  bestehenden Fazit-Block im Detail-Panel.
- `scheduler/background.py`: neue `_formatiere_zai_gegenpruefung()` (eigene
  Kopie für den E-Mail-Textkontext, analog `_formatiere_fazit()`), nur in
  `_notify_hebel_signal()` verdrahtet (Signal/Spot hat diese Felder nicht).

**Verifiziert:** Compile-Check + Import-Regression (`ui.hebel_view`,
`scheduler.background`, `main`); synthetischer Test aller 3
E-Mail-Textbau-Fälle (beide Felder gesetzt, nur Konsistenz-Check gesetzt,
beide leer); Tk-Smoke-Test von `render_detail_text()` mit Fazit- und
Z.ai-Zeilen gemischt (bestätigt: Fazit bekommt `fazit_positiv` +
`fazit_label_positiv` nur über "Fazit:", Z.ai-Zeilen bekommen `risk_negativ`/
`risk_positiv` über die ganze Zeile, keine Fett-Formatierung); HTML-Rendering
(`render_detail_html()`) mit derselben Zeilenmischung geprüft (Fazit-Split in
zwei Spans, Z.ai-Zeilen ein Span, keine Unterstreichung).

Scope bleibt Hebel-only (v1-Entscheidung unverändert). Phase 1 (rein
beobachtend, kein Gate) gilt unverändert auch für den neuen Richtungs-Abgleich.

## Nachtrag (2026-07-26, noch später): E-Mail zeigte Z.ai-Zeilen nie - echter Fund per Screenshot, begrenzte Wartezeit als Fix

Nutzer schickte einen Screenshot der echten BTC-SHORT-Benachrichtigungs-Mail:
Risikofaktoren und Fazit waren korrekt formatiert, die neu verdrahteten
Z.ai-Zeilen (siehe voriger Nachtrag) fehlten jedoch komplett - obwohl die DB
zum exakt selben Zeitstempel bereits `zai_gegenpruefung_urteil = "konsistent"`
für dieses Signal enthielt (per Notebook-Diagnose-Export verifiziert,
`created_at` 15:14:07 UTC = 17:14 lokal, passend zur E-Mail-Zeit).

### Root Cause

`generate_hebel_signal()` gibt das `signal`-Objekt bewusst zurück, BEVOR der
Z.ai-Hintergrund-Thread ueberhaupt fertig ist (siehe voriger Nachtrag,
Architektur-Falle-Abschnitt) - das ist korrekt fuer die urspruengliche
Design-Absicht (GUI liest ohnehin live aus der DB), aber `_on_signal_ready()`
in `scheduler/background.py` reicht genau dieses In-Memory-Objekt direkt an
`_notify_hebel_signal()` durch. Die E-Mail wird also strukturell IMMER
komponiert, bevor die Z.ai-Felder existieren koennen - unabhaengig davon, wie
schnell Z.ai tatsaechlich antwortet. Der neue E-Mail-Anzeige-Code (voriger
Nachtrag) war fuer sich genommen korrekt, griff aber nie, weil die
Datenquelle strukturell nie etwas zum Anzeigen hatte.

### Entscheidung

Per `AskUserQuestion` drei Optionen vorgelegt: (1) nur GUI, E-Mail-Aufruf
entfernen (Standard-Empfehlung - kein Risiko einer neuen Latenz-Regression),
(2) separate Kurz-Mail nur bei Widerspruch/Abweichung, (3) E-Mail-Versand um
bis zu 60s verzoegern. **Nutzer-Entscheidung: Option 3**, bewusst gegen die
Empfehlung, mit vollem Bewusstsein ueber den Tradeoff (Beschreibung der
Option nannte den Zielkonflikt mit dem urspruenglichen E-Mail-Latenz-Fix
explizit).

### Umsetzung: begrenztes Warten in einem EIGENEN Thread, nicht im Allocator-Loop

Ein simples "60s schlafen, dann E-Mail schicken" INNERHALB von
`_on_signal_ready()` haette exakt die Batch-Blockade zurueckgebracht, die der
E-Mail-Latenz-Fix (siehe `project_email_latenz_fix_batch_notification.md`)
bereits einmal behoben hat: `_on_signal_ready()` laeuft synchron in der
Aufrufer-Schleife von `run_budget_allocator()` - ein Block dort haette JEDES
nachfolgende Signal im selben Lauf um bis zu 60s verzoegert, nicht nur dieses
eine.

Stattdessen:
- `agent/krypto/hebel_pipeline.py`: `signal.id = new_id` direkt nach dem
  Insert gesetzt (das Feld existierte bereits auf `HebelSignal`, wurde aber
  bisher nirgends befuellt - weder hier noch beim analogen Spot-`Signal`).
  Ermoeglicht das spaetere gezielte Nachladen per
  `db.get_hebel_signal_by_id()`.
- `scheduler/background.py`: neue Funktion
  `_sende_hebel_email_mit_zai_wartezeit()` - laeuft in einem EIGENEN,
  von `_on_signal_ready()` gestarteten Hintergrund-Thread (nicht im
  Allocator-Loop selbst). Fruehausstieg bei HALTEN/nicht-benachrichtigungs-
  relevanten Aktionen (kein Warten fuer den haeufigsten Fall). Begrenztes
  Polling (`_ZAI_EMAIL_WARTE_MAX_SEKUNDEN` = 60, alle
  `_ZAI_EMAIL_POLL_INTERVALL_SEKUNDEN` = 3 Sekunden per
  `db.get_hebel_signal_by_id()`) statt festem Sleep - beendet die Wartezeit
  sofort, sobald mindestens eines der beiden Z.ai-Urteile vorliegt (typische
  Antwortzeit 12-25s je Call). Wird das Limit erreicht (z.B. bei einem
  Z.ai-Timeout von bis zu 150s je Call), geht die E-Mail trotzdem OHNE
  Z.ai-Zeilen raus (P-8, kein Hard-Fail wegen einer optionalen Zusatzinfo).
  `_on_signal_ready()` dispatcht diese Funktion nur, wenn `zai_client is not
  None` - ist Z.ai gar nicht konfiguriert, bleibt der alte, sofortige Pfad
  unveraendert (kein sinnloses Warten auf etwas, das nie laeuft).

**Zusaetzliche Log-Instrumentierung** (Nutzer-Nachfrage: wie lange dauert die
Pipeline vom deterministischen Signal ueber LLM-Pruefung 1 und LLM-Pruefung 2
bis zum E-Mail-Versand wirklich?): bisher gab es dafuer KEINE Log-Zeile - Z.ai-
Erfolge wurden nie geloggt, nur Fehlschlaege (`gegenpruefung.py`, P-8). Die
neue Wartefunktion loggt jetzt bei jedem Durchlauf entweder "Z.ai-Gegenpruefung
fuer SYMBOL nach Xs abgeschlossen" (Fruehausstieg) oder "... nach 60s
(Zeitlimit) noch nicht abgeschlossen" (Timeout-Fall) - ab dem naechsten
Notebook-Deployment liefert das erstmals echte, fortlaufende Messwerte fuer
genau diese Frage.

**Real gemessene Zahlen aus dem heutigen Batch (17:12-17:22 Uhr, ALTER
Code-Stand ohne diesen Fix):** Budget-Allocator waehlt Kandidaten aus
(17:12:58) -> BTC-SHORT-E-Mail nach 73s (17:14:11, reine LLM-Pruefung-1-Zeit
via Mistral + Pipeline, da die alte E-Mail noch vor Z.ai verschickt wurde) ->
NEAR-LONG-E-Mail 34s spaeter (17:14:45) -> INJ-LONG-E-Mail 161s spaeter
(17:17:26, vermutlich externe Datenabruf-Retries) -> gesamter Batch (8 Hebel +
11 Spot) fertig nach knapp 10 Minuten (17:22:47). Die Z.ai-Gegenpruefung selbst
(Pruefung 2) ist fuer diesen Batch NICHT separat messbar, da (a) keine
Erfolgs-Log-Zeile existierte (siehe oben, jetzt behoben) und (b) das Notebook
zu diesem Zeitpunkt noch den Code-Stand VOR diesem Fix fuhr. Einzige
bisherige Referenz: die isolierte Kalibrierung gegen die echte Z.ai-API
(voriger Nachtrag) mit 12-25s je Call, nicht aus echtem Produktivbetrieb.

**Verifiziert:** Compile-Check + Import-Regression
(`agent.krypto.hebel_pipeline`, `scheduler.background`,
`agent.krypto.budget_allocator`, `main`); drei synthetische Tests
(HALTEN -> sofortiger Ausstieg ohne DB-Zugriff/E-Mail, Fruehausstieg nach
Z.ai-Fertigstellung mit angereichertem Signal, Timeout-Fall -> E-Mail geht
nach vollem Zeitbudget trotzdem OHNE Z.ai-Daten raus); separater Test
bestaetigt, dass der Thread-Dispatch selbst nicht blockiert (<1ms), nur der
Hintergrund-Thread tatsaechlich wartet - die urspruengliche Garantie des
E-Mail-Latenz-Fixes (andere Kandidaten im selben Batch werden nicht
verzoegert) bleibt damit erhalten.

**Noch offen (Notebook-Deployment):** der Notebook-Diagnose-Export vom
26.07. abends zeigte, dass der 24/7-Produktivserver zum Zeitpunkt des
Screenshot-Funds noch auf dem Code-Stand VOR dem Richtungs-Abgleich lief
(keine `zai_eigene_richtung`/`zai_uebereinstimmung`-Werte in den exportierten
Rohdaten) - erst nach Pull+Neustart am Notebook greifen sowohl der
Richtungs-Abgleich als auch dieser E-Mail-Fix dort live. Zusaetzlich wurde
`extract_notebook_diagnose.py` in dieser Runde NICHT um die 3 neuen Spalten
erweitert - die `zai_gegenpruefung_verlauf`-Aggregatsektion zeigt bis dahin
weiterhin nur den Konsistenz-Check, nicht den Richtungs-Abgleich (loser
Faden, niedrige Prioritaet, siehe Memory).

## Nachtrag (2026-07-26, zum Abschluss dieses Tages): GUI zeigte Zeitstempel systemweit roh in UTC statt lokal - derselbe Fehler wie beim E-Mail-Fix vom 2026-07-21, nur an 11 anderen Stellen

Nutzer verglich einen Screenshot des Hebel-Tabs mit der zugehoerigen E-Mail:
BTC-SHORT stand in der GUI-Liste mit "2026-07-26 15:14", die E-Mail kam aber
laut Posteingang um "17:14" an - auf den ersten Blick wie eine 2-Stunden-
Verzoegerung. War keine: exakt derselbe Fund wie im Nachtrag vom 2026-07-21
("Delta Berechnung/LLM-Abfrage"), nur diesmal zwischen GUI und E-Mail statt
zwischen Berechnung und Versand.

### Root Cause

Der 2026-07-21-Fix (`_formatiere_zeitpunkt_lokal()`, konvertiert UTC auf die
lokale Systemzeitzone via `astimezone()`) lebte ausschliesslich in
`scheduler/background.py` und wurde nur fuer den E-Mail-Text verwendet. Die
App-GUI hatte ihr eigenes, nie synchronisiertes Muster
(`created_at[:16].replace("T", " ")`, ROH, ohne Umrechnung) an **11 Stellen
in 5 Dateien**: `ui/app.py`, `ui/hebel_view.py` (4×), `ui/signals_view.py`
(4×), `ui/letzte_bewertung.py`, `ui/regime_view.py`. Jede Liste/jedes
Detail-Panel/jeder Historie-Dialog zeigte also weiterhin die rohe UTC-Zeit -
bei CEST (UTC+2) optisch immer exakt 2 Stunden "zu frueh".

### Fix: eine gemeinsame Funktion statt zwei getrennter Kopien

`_formatiere_zeitpunkt_lokal()` nach `ui/formatting.py::
format_zeitpunkt_lokal()` verschoben (dieses Modul ist bereits das etablierte,
Tk-freie Gemeinsamkeits-Modul zwischen App und E-Mail, siehe
`format_zai_gegenpruefung_lines()`/`format_fazit_lines()` weiter oben).
`scheduler/background.py` importiert die Funktion jetzt von dort (Re-Export
unter dem alten Namen, alle bestehenden Aufrufstellen unveraendert). Alle 11
GUI-Stellen auf `format_zeitpunkt_lokal()` umgestellt - dadurch koennen GUI
und E-Mail nicht mehr auseinanderlaufen, weil es nur noch EINE Implementierung
gibt statt zweier potenziell divergierender Kopien.

**Verifiziert:** Compile-Check + Import-Regression aller 7 geaenderten
Dateien; direkter Funktionstest gegen den echten BTC-Zeitstempel aus dem
Vorfall (`2026-07-26T15:14:07+00:00` → `2026-07-26 17:14`, exakt die
E-Mail-Ankunftszeit aus dem Nutzer-Screenshot) sowie Randfaelle (None, leerer
String, ungueltiges Format). Kein Tk-Smoke-Test noetig - reine
Funktionsaufruf-Substitution mit identischer Signatur je Stelle.

## Nachtrag (2026-07-26, Abschluss): extract_notebook_diagnose.py verschluckte teilweise erfolgreiche Z.ai-Richtungs-Calls

Nutzer wollte eine echte Gegenueberstellung LLM 1 (Mistral, Primaer-Richtung)
vs. LLM 2 (Z.ai, unabhaengige Richtungsableitung) und wies zurecht darauf hin,
dass Z.ai-Abfragen bereits gelaufen waren - die vorherige Einschaetzung
("keine Daten vorhanden") war unvollstaendig recherchiert.

### Root Cause

`_zai_gegenpruefung_verlauf()` in `extract_notebook_diagnose.py` wurde beim
Bau des zweiten Z.ai-Calls (Richtungs-Abgleich, siehe voriger Nachtrag) nicht
mit erweitert: weder SELECT-Spaltenliste noch `_HEBEL_SIGNAL_SPALTEN` kannten
`zai_eigene_richtung`/`zai_uebereinstimmung`/`zai_richtung_kurzbegruendung`.
Schlimmer als reines Fehlen: der WHERE-Filter (`zai_gegenpruefung_urteil IS
NOT NULL`) haette jeden Datensatz, bei dem NUR der Richtungs-Call gelang
(Konsistenz-Call fehlgeschlagen), komplett aus der Aggregation verschwinden
lassen, obwohl er echte Z.ai-Ergebnisse enthaelt.

### Fix

`_HEBEL_SIGNAL_SPALTEN` um die 3 neuen Spalten erweitert. WHERE-Filter in
`_zai_gegenpruefung_verlauf()` auf ODER umgestellt
(`zai_gegenpruefung_urteil IS NOT NULL OR zai_eigene_richtung IS NOT NULL`),
neue Aggregat-Felder `anzahl_richtung_gesamt`/`anzahl_uebereinstimmung`/
`anzahl_abweichung` ergaenzt, symmetrisch zu den bestehenden
Konsistenz-Feldern.

**Verifiziert:** Compile-Check; synthetischer Test mit 4 Szenarien (kein
Z.ai-Call, nur Konsistenz-Call, nur Richtungs-Call, beide Calls mit
Abweichung) - bestaetigt insbesondere, dass der zuvor verschluckte
"nur Richtungs-Call gelang"-Fall jetzt korrekt erfasst wird.

**Naechster Schritt (Nutzer-Aktion erforderlich):** `extract_notebook_
diagnose.py` muss am Notebook (nicht Desktop, siehe [[feedback_desktop_kein_
produktivstart]]) mit dem aktuellen Code-Stand erneut laufen und der Export
nach Google Drive synchronisiert werden, damit die eigentlich gewuenschte
LLM1-vs-Z.ai-Gegenueberstellung ueberhaupt moeglich wird.

## Nachtrag (2026-07-26, Folgetag): Retail-Konsens ("antizyklisch") wird bei Hebel nie wieder in top_gruende zugelassen - deterministisch statt nur per Prompt

Nach der ersten echten LLM1-vs-Z.ai-Gegenueberstellung (0 von 12 Faellen mit
Uebereinstimmung, Z.ai sagte in keinem einzigen Fall LONG obwohl Mistral 11 von
12 Mal LONG waehlte) verlangte der Nutzer eine tiefere Analyse - mit der
korrekten Einordnung, dass der bestehende "antizyklisch"-Mechanismus zwei
voellig unterschiedliche Dinge verwechselt: AZ-4 (Boden-Akkumulation, siehe
`docs/`-Baustein zu Tranchen) gilt bewusst nur Spot, nur BTC/ETH/SOL, gebunden
an eine objektiv geschaetzte Bodenzielzone - bei Hebel gibt es dafuer keine
fachliche Rechtfertigung, hier muss eine echte Long-Chance aus echter
technischer Bestaetigung hervorgehen (MACD/EMA-Struktur/RSI/Konfluenz), nicht
aus Positionierungsdaten.

### Root Cause (echter Fund, nicht nur Konzeptfrage)

Der Vortag (`f4e9c0e`, 2026-07-25) hatte bereits eine Regel-Luecke bei genau
diesem Thema gefixt (Retail-Konsens durfte nicht unter anderem Kategorie-Label
verkleidet werden). Trotzdem verletzten 4 von 5 am Folgetag geprueften echten
Hebel-Signalen (ONDO/INJ/BTC/TAO, alle Baer-Regime) dieselbe Regel erneut -
teils sogar unter dem korrekten Label `antizyklisch` selbst, nicht nur ueber
die Umbenennungs-Luecke. Log-Analyse bestaetigte: das Notebook lief zwischen
Fix-Commit und den betroffenen Signalen mehrfach neu (mehrere `Remote-Steuer-
Seite gestartet`-Log-Zeilen dazwischen) - kein Deployment-Verzug, sondern eine
strukturelle Luecke: Regel 8 war ausschliesslich eine Prompt-Anweisung, keine
Code-Pruefung des tatsaechlichen `text`-Inhalts. Der bereits vorhandene,
korrekte deterministische Risikofaktor (`compute_risikofaktoren_hebel()`,
Abschnitt 3) klassifiziert denselben Rohwert (`long_konten_anteil_prozent`)
schon laengst richtig (negativ bei extremer gleichgerichteter Mehrheit, neutral
bei moderater, positiv nur bei echter Gegenrichtung) - das Modell durfte
denselben Wert in Abschnitt 1 (`top_gruende`) trotzdem gegenteilig
interpretieren, ein interner Widerspruch im selben Signal.

### Fix

1. `agent/krypto/hebel_analyst.py`: `antizyklisch` komplett aus
   `TOP_GRUENDE_KATEGORIEN` entfernt (nur noch technisch/fundamental/makro/
   risiko) - das alte Label wird jetzt schon von der Schema-Validierung
   (`_validate_hebel()`) abgelehnt. Regel 8 neu gefasst: Retail-/Long-Konten-
   Positionierung gehoert grundsaetzlich NICHT in `top_gruende`, weder
   stuetzend noch neutral, da sie bereits vollstaendig in Abschnitt 3 bewertet
   wird.
2. `agent/krypto/hebel_risk_gate.py`: neue Funktion
   `filtere_retail_konsens_top_gruende()` - entfernt jeden `top_gruende`-
   Eintrag, dessen Text auf Retail-/Long-/Short-Konten-Positionierung oder
   Long-Short-Ratio verweist, unabhaengig von Kategorie-Label. Angewendet ganz
   am Anfang von `post_check_hebel()`, bevor irgendeine andere Deckel-Logik
   greift. Lenient wie bei der Tranchen-Validierung: fehlende Rangplaetze sind
   unschaedlich (`hebel_pipeline.py` liest je Rang per `.get()` mit
   None-Default), kein Retry/HALTEN-Fallback noetig.

Retail-/Long-Konten-Daten bleiben unveraendert als Fakt UND als Risikofaktor
(Abschnitt 3) vorhanden - nur die Verwendung als eigenstaendiger Grund in
Abschnitt 1 ist jetzt beidseitig (Prompt UND Code) ausgeschlossen.

### Warum das eine echte fachliche Verbesserung ist, nicht nur andere Zahlen

"Long-Konten-Anteil zeigt Raum fuer Erholung" ist ein Non-Sequitur:
Positionierungsdaten sagen etwas ueber Squeeze-/Liquidations-Risiko einer
bereits gehebelten Crowd aus, nicht darueber, ob der Kurs steigen sollte. Die
interne Konsistenz zwischen Abschnitt 1 und Abschnitt 3 desselben Signals war
vorher nicht gegeben (derselbe Rohwert wurde an zwei Stellen gegensaetzlich
gewertet) - das ist eine Korrektheits-, keine Geschmacksfrage. Die
quantitative Wirkung auf die reale Trefferquote (aktuell 9,4 %, CRV −0,54)
muss trotzdem erst durch Beobachtung bestaetigt werden, nicht nur logisch
angenommen - siehe [[feedback_backtest_first_hard_guarantee]]. Als
Nebenbefund notiert, noch nicht geprueft: die Makro-Analogie-Formulierungen
("gemischt, aber teilweise positiv") wirkten in denselben Beispielen aehnlich
beliebig verwendbar - moeglicher Geschwister-Fall fuer eine spaetere Runde.

**Verifiziert:** Compile-/Import-Regressionscheck aller 4 betroffenen Module
(`hebel_analyst`, `hebel_risk_gate`, `hebel_pipeline`, `scheduler.background`).
Synthetischer Test mit den 4 echten Verstoss-Faellen (ONDO/INJ/BTC/TAO, exakte
Formulierungen aus dem Notebook-Export) - alle korrekt entfernt; legitime
technische/Risiko-Gruende bleiben unveraendert; Randfaelle (None/leere Liste/
fehlendes `text`-Feld) sowie weitere Formulierungsvarianten (Retail-Bias/
Short-Konten-Anteil/Long-Short-Ratio) ebenfalls abgedeckt. `_validate_hebel()`
lehnt das alte `antizyklisch`-Label jetzt korrekt mit `AnalystResponseInvalid`
ab, ein gueltiger 4-Kategorien-Fall wird weiterhin akzeptiert.

## Nachtrag (2026-07-26, gleicher Tag): Z.ai-Konsistenz-Check verwechselte Positions-Richtung mit Markteinschaetzung (echter HYPE-Fund)

Nutzer zeigte einen echten Screenshot (HYPE, TEILVERKAUF einer offenen LONG-
Position): Z.ai-Konsistenz-Check meldete "widerspruch - Text spricht von
Abwaertsbewegung bei LONG-Signal", obwohl das Signal fachlich korrekt war.

### Root Cause

Bei `action` TEILVERKAUF/SCHLIESSEN (Kontrathese-Uebersetzung) beschreibt
`richtung` die BESTEHENDE Position, die abgebaut wird - NICHT Mistrals eigene
Markteinschaetzung (die steht separat in `kontrathese_llm_richtung`). Eine
baerische Begruendung fuer den Teilverkauf einer LONG-Position ist fachlich
korrekt (genau deshalb verkauft man teilweise), aber `gegenpruefung.py::
pruefe_konsistenz()` gibt Z.ai `richtung`+`action` roh mit, ohne diese
Semantik zu erklaeren - Z.ai las `richtung=LONG` naiv als "Text soll bullisch
sein" und wertete die korrekte baerische Rechtfertigung als Widerspruch.

Haeufigkeit geprueft: von 8 "widerspruch"-Urteilen desselben Tages war NUR
dieser eine (HYPE, `kontrathese_zu_position=1`) betroffen - die anderen 7
sind echte, unabhaengige Text-vs-Fakten-Widersprueche bei regulaeren HALTEN-
Signalen (kein offener Positions-Bezug), korrekt erkannt.

### Fix + eigener Fund waehrend der Umsetzung

`SYSTEM_PROMPT` in `agent/krypto/gegenpruefung.py` ergaenzt: bei `action`
TEILVERKAUF/SCHLIESSEN/HEBEL_SENKEN beschreibt `richtung` die bestehende
Position, gegenlaeufige Begruendung ist dort konsistent; bei ALLEN anderen
Aktionen (insbesondere HALTEN) bleibt `richtung` die Markteinschaetzung,
normale Widerspruchspruefung gilt weiter.

**Erster Entwurf hatte einen echten Regressions-Bug**, live gegen die echte
Z.ai-API entdeckt: eine zu weit gefasste erste Formulierung ("bei HALTEN/
HEBEL_SENKEN ist beides moeglich") kippte einen ECHTEN, unabhaengig
bestehenden Widerspruchsfall (KAIA, HALTEN, `richtung=LONG` bei durchgehend
baerischem Text, KEIN offener Positions-Bezug) von "widerspruch" (3/3 mit
altem Prompt) auf faelschlich "konsistent" (3/3 mit erstem Entwurf) - HALTEN
wurde faelschlich in die Ausnahme mit hineingezogen. Sofort korrigiert:
Ausnahme gilt nur noch fuer TEILVERKAUF/SCHLIESSEN/HEBEL_SENKEN, HALTEN
explizit wieder ausgeschlossen.

**Verifiziert:** echter Live-A/B-Test gegen die echte Z.ai-API (kein
synthetischer Mock) mit den exakten Fakten/Texten beider realer Faelle -
HYPE (TEILVERKAUF) bleibt nach dem Fix 3/3 "konsistent", KAIA (HALTEN) kehrt
nach der Korrektur 3/3 zu "widerspruch" zurueck (identisch zum
Alt-Prompt-Verhalten). Compile-/Import-Regressionscheck.

**Lehre (uebergreifend mit dem Antizyklisch-Fund vom selben Tag):** auch eine
gezielte, klein wirkende Prompt-Praezisierung kann unbeabsichtigt eine
bestehende, korrekte Erkennung in einer ANDEREN Aktionsklasse aufweichen -
ein Live-A/B-Test gegen einen bekannten POSITIVEN Referenzfall (hier: KAIA)
ist deshalb genauso wichtig wie der Test gegen den eigentlichen Zielfall.

## Nachtrag (2026-07-27): Z.ai-Konsistenz-Check auf Spot-Signale ausgeweitet (nicht der Richtungs-Abgleich)

Nutzer-Nachfrage: warum gibt es die Z.ai-Gegenpruefung nur bei Hebel, nicht bei
Spot? Antwort nach Recherche: reine "Scope v1"-Eingrenzung (Hebel zuerst, da
hoeherer Einsatz durch Liquidationsrisiko - gleiches Muster wie bei
Liquiditaetszonen-Grafik/Retail-Konsens-Fakt-zuerst, die beide zuerst bei
Hebel gebaut und spaeter auf Spot nachgezogen wurden), kein Kosten-/
Kapazitaetsgrund (Z.ai laeuft ueber `glm-4.5-flash`, eines der dauerhaft
kostenlosen Modelle, Rate-Limit 120/Min, kein wirksames Tagesbudget mehr auf
diesem Pfad). Nutzer-Entscheidung: Ausweitung umsetzen, NUR der Konsistenz-
Check (`pruefe_konsistenz()`), NICHT der unabhaengige Richtungs-Abgleich
(`leite_eigene_richtung()`) - Spot-Signale kennen kein `richtung`/LONG-SHORT-
Konzept, eine Ausweitung des Richtungs-Abgleichs wuerde eine neue, eigene
Interpretation erfordern (z.B. KAUFEN/VERKAUFEN statt LONG/SHORT) und war
nicht angefragt.

### Umsetzung

- `agent/krypto/gegenpruefung.py`: `baue_fakten()`s `richtung`-Parameter jetzt
  optional (Default None, ans Ende der Signatur verschoben) - fehlt er, wird
  der Schluessel im Fakten-Dict komplett weggelassen statt mit einem
  erfundenen Wert befuellt. Der SYSTEM_PROMPT musste NICHT angepasst werden:
  die TEILVERKAUF/SCHLIESSEN/HEBEL_SENKEN-Klausel (siehe Nachtrag oben) greift
  nur bei diesen drei Hebel-exklusiven Aktionsnamen - Spot-Aktionen
  (KAUFEN/VERKAUFEN/TAUSCHEN/NACHKAUFEN/HALTEN) fallen automatisch unter die
  "ALLEN anderen Aktionen"-Regel.
- `database/models.py`: `Signal`-Dataclass um `zai_gegenpruefung_urteil`/
  `zai_gegenpruefung_kurzbegruendung` erweitert - bewusst NUR diese 2 Felder
  (kein `zai_eigene_richtung`/`zai_uebereinstimmung`/
  `zai_richtung_kurzbegruendung` wie bei `HebelSignal`, da kein Richtungs-
  Abgleich fuer Spot).
- `database/db.py`: additive Migration `_migrate_signal_zai_gegenpruefung_
  columns()` (analog zur bestehenden Hebel-Migration, nur `signals` statt
  `hebel_signals`, nur 2 statt 5 Spalten) + neue, schlankere
  `update_signal_zai_gegenpruefung()`.
- `agent/krypto/pipeline.py`: neue `_zai_konsistenz_im_hintergrund()`
  (Spot-Pendant zu `hebel_pipeline.py::_zai_gegenpruefung_im_hintergrund()`,
  nur der Konsistenz-Teil), `generate_signal()` bekommt `zai_client=None`-
  Parameter, Dispatch direkt nach `db.insert_signal()` (gleiches
  Async-Thread-Muster wie bei Hebel - Z.ai hat einen 150s-Timeout, ein
  synchroner Call vor `return signal` wuerde den `on_signal_ready`-E-Mail-
  Callback verzoegern).
- `agent/krypto/budget_allocator.py`: `zai_client=zai_client` an beide Spot-
  Tier-3-Aufrufe (Mistral/Gemini) durchgereicht - `run_budget_allocator()`
  hatte den Parameter bereits (Hebel nutzte ihn schon).
- `ui/signals_view.py`: `format_zai_gegenpruefung_lines()`-Block im Detail-
  Panel ergaenzt (identisch zu `ui/hebel_view.py`, Richtungs-Parameter bewusst
  `None`).
- `scheduler/background.py`: `_formatiere_zai_gegenpruefung()` in
  `_notify_spot_signal()`s E-Mail-Body eingehaengt. **Echter Fund dabei:** die
  Funktion griff bisher DIREKT auf `signal.zai_eigene_richtung` zu - waere bei
  einem `Signal`-Objekt (das dieses Feld bewusst NICHT traegt) mit
  `AttributeError` abgestuerzt. Auf `getattr(signal, "zai_eigene_richtung",
  None)` (und die beiden zugehoerigen Folgefelder) umgestellt - funktioniert
  dadurch unveraendert fuer `HebelSignal` UND `Signal`, ohne dass `Signal` die
  drei ungenutzten Richtungs-Felder tragen muesste. Docstring (behauptete
  faelschlich "Signal (Spot) hat diese Felder nicht") korrigiert.
- `extract_notebook_diagnose.py`: `_SPOT_SIGNAL_SPALTEN` um die 2 neuen
  Konsistenz-Spalten ergaenzt (analog zu `_HEBEL_SIGNAL_SPALTEN`, dort aber 5
  Spalten wegen des zusaetzlichen Richtungs-Abgleichs).

### Eigener Fund waehrend der Verifikation: Test haette beinahe die echte lokale Desktop-DB beruehrt

Ein erster Testlauf von `_zai_konsistenz_im_hintergrund()` gegen eine isolierte
Temp-DB schlug fehl mit `sqlite3.OperationalError: no such column`. Ursache:
`database/db.py::get_connection()` verwendet einen FEST verdrahteten
`DB_PATH` (`data/tradinginfotool.db`, die echte lokale Desktop-DB) statt der
im Test uebergebenen Connection - der Hintergrund-Thread ruft `db.
get_connection()` intern selbst auf (bewusst, siehe Docstring: eigene
Connection noetig, da sqlite3-Connections nicht Thread-uebergreifend geteilt
werden koennen), umgeht dadurch aber jede von aussen injizierte Test-
Connection. Der Fehler kam VOR jedem `commit()`, es wurde nachweislich nichts
geschrieben (per Nachkontrolle der echten Datei bestaetigt: weder die neue
Spalte noch ein Test-Datensatz vorhanden) - trotzdem ein echter Beinahe-
Verstoss gegen [[feedback_desktop_kein_produktivstart]]. Test korrigiert:
`db.get_connection` fuer die Testdauer per Monkeypatch auf die isolierte
Temp-DB umgebogen, danach sauber zurueckgesetzt. **Lehre:** bei jedem Test
einer Funktion, die intern selbst eine neue DB-Connection oeffnet (statt eine
uebergebene zu nutzen - hier bewusst wegen Thread-Sicherheit), muss der Test
diese interne Connection-Erzeugung selbst isolieren, eine isolierte Connection
nur an der Aufruf-Oberflaeche zu uebergeben reicht nicht.

**Verifiziert:** Compile-/Import-Regressionscheck (8 geaenderte Dateien +
4 Hebel-Module als Regressionscheck). DB-Migration + Idempotenz gegen
isolierte Temp-DB. `baue_fakten()` mit/ohne `richtung` (Keyword-Aufruf).
Echter Live-Test von `_zai_konsistenz_im_hintergrund()` gegen die echte
Z.ai-API (isolierte Temp-DB, korrekt erkannter Widerspruch). `_formatiere_
zai_gegenpruefung()` mit Signal-artigem Stub (kein `AttributeError`, korrekt
nur Konsistenz-Zeile) UND Hebel-artigem Stub (Regressionscheck, Richtungsteil
weiterhin korrekt). `format_zai_gegenpruefung_lines()` Spot-Aufruf (nur 1
Zeile). Kein manueller Button (Signale-Tab-Batch, Hebel-Tab "Jetzt
analysieren") einbezogen - gleiche Einschraenkung besteht bereits fuer Hebel
(Gegenpruefung laeuft dort ebenfalls nur automatisch ueber den
Budget-Allocator, nicht bei manuellen Einzelklicks).

## Nachtrag (2026-07-27): Hebel-Pruefung-Toggle bei bereits gequeueten Kandidaten wirkungslos (KAITO-Fund)

Nutzer-Meldung: KAITO steht in der Watchlist unter Status "Beobachtung", der
per-Asset Hebel-Pruefung-Toggle (`asset_hebel_settings`, siehe #268/2026-07-19)
ist fuer KAITO AUS - trotzdem wurde KAITO weiterhin ueber den Hebel-Pfad
gefuehrt und erhielt neue Signale.

### Ursache

Der Toggle wird korrekt an GENAU EINER Stelle geprueft:
`agent/krypto/hebel_screening.py::run_hebel_screening()` filtert
`krypto_assets` VOR dem OI-Abruf/Scoring - ein Symbol mit Toggle AUS erzeugt
also ab dem Moment der Umschaltung keine NEUEN `hebel_triggers`-Zeilen mehr.

Bereits VOR der Umschaltung angelegte Zeilen (`status='neu'`, bleiben laut
[[project_kaia_review_inj_stabilitaet_diskussion|Info-Leichen-Verfall]]
(#306-#310, 2026-07-25) bis zu `hebel_kandidat_verfall_stunden` = 48h
gueltig) wurden davon NICHT erfasst: `database/db.py::
get_pending_hebel_candidates()` - die gemeinsame Lese-Funktion, die SOWOHL
`agent/krypto/budget_allocator.py` (Tier-1-Kandidatenauswahl, Zeile 384) ALS
AUCH `ui/hebel_view.py` (Zeile 189, "Kandidat wartet auf Analyse"-Warteliste)
verwendet - selektierte weiterhin ALLE `status='neu'`-Zeilen unabhaengig vom
aktuellen Toggle-Zustand. Ein Toggle-Wechsel wirkte dadurch erst nach Ablauf
des 48h-Verfallsfensters der zu diesem Zeitpunkt bereits gequeueten Kandidaten.

**Strukturell identisch** zu einem bereits behobenen Bugmuster: der CANTON-
Fund (2026-07-20, siehe [[project_hebel_rahmenbedingungen]]) bei
`get_symbole_mit_ueberschrittener_oi_schwelle()` - dort exakt dieselbe fehlende
Pruefung an einer ANDEREN Lese-Stelle. Beide Faelle: der Toggle wird bei der
NEU-Erfassung korrekt geprueft, aber nicht erneut bei der spaeteren
Selektion/Anzeige bereits gespeicherter Zeilen.

### Fix

`database/db.py::get_pending_hebel_candidates()`: `LEFT JOIN
asset_hebel_settings s ON s.symbol = t.symbol` + `AND COALESCE(s.
hebel_pruefung_erlaubt, 1) = 1` in der WHERE-Klausel ergaenzt - identisches
Muster wie beim CANTON-Fix. `COALESCE(..., 1)`, da Symbole ohne Eintrag in
`asset_hebel_settings` per Default erlaubt sind (siehe `get_hebel_pruefung_
erlaubt()`).

**Positiver Nebeneffekt:** da `ui/hebel_view.py` dieselbe Funktion fuer die
Warteliste nutzt, verschwindet ein toggle-ausgeschalteter Kandidat dadurch
automatisch auch aus der GUI-Anzeige - kein zusaetzlicher Patch an der
UI-Stelle noetig, einmaliger Fix an der gemeinsamen Lese-Funktion behebt
Signal-Erzeugung UND Anzeige gleichzeitig.

**Bewusst unveraendert:** die zweite, unabhaengige Hebel-Kandidatenquelle -
bereits offene Positionen (`budget_allocator.py::_offene_positionen_als_
kandidaten()`, #130, 2026-07-19) - umgeht den Toggle weiterhin ABSICHTLICH
(bestehende offene Positionen muessen weiter verwaltbar bleiben, auch wenn
die Neu-Pruefung fuer dieses Symbol deaktiviert wurde, siehe [[project_sol_
tranchen_hebel_toggle]]).

Geprueft, ob eine Schwesterfunktion dasselbe Luecken-Muster hat:
`get_pending_marktscan_kaufkandidaten()` (Docstring verweist zum Vergleich auf
`get_pending_hebel_candidates()`) betrifft Marktscan/Spot-Kandidaten - dort
existiert kein Hebel-Pruefung-Toggle-Konzept, kein Fix noetig.

**Verifiziert:** synthetischer Test gegen isolierte In-Memory-DB - 3
Kandidaten (KAITO Toggle AUS, ETH kein Toggle-Eintrag = Default AN, SOL Toggle
explizit AN), `get_pending_hebel_candidates()` schliesst KAITO korrekt aus,
ETH+SOL korrekt enthalten, Sortierung nach `score_gesamt DESC` bleibt intakt.
Compile-/Import-Regressionscheck: `database/db.py`, `agent/krypto/
budget_allocator.py`, `ui/hebel_view.py`.

## Nachtrag (2026-07-27): HALTEN auf Symbol mit offener Hebel-Position zeigt jetzt deren aktuellen Stand (Abschnitt 1)

Nutzer-Nachfrage anhand eines Screenshots (VIRTUAL LONG HALTEN): Abschnitt 1
("MATHEMATISCH BERECHNET") im Hebel-Detail-Panel blieb bei HALTEN immer leer.

### Einordnung

Kein Bug im bisherigen Sinne - Abschnitt 1 zeigt bewusst NUR deterministisch
berechnete Werte, die aus einer Positionsveraenderung entstehen (Hebel final,
Liquidationspreis, Eigenkapitalbedarf/-nachschuss), siehe die urspruengliche
3-Abschnitte-Entscheidung vom 2026-07-19 (AVAX-Fund). HALTEN veraendert nichts,
also gibt es dafuer folgerichtig nichts zu berechnen. Bei VIRTUAL im
Screenshot kommt hinzu: keine offene Position auf VIRTUAL vorhanden.

**Aber:** bei einem Symbol MIT offener Position (im Screenshot: HYPE) ist der
*aktuelle* Stand dieser Position (Hebel, Eigenkapital, geschaetzter
Liquidationspreis - alles echte, im letzten Positions-Sync berechnete Werte,
siehe `hebel_positions`/`importer/bitpanda_margin_positions.py`) eine legitime
Ergaenzung fuer Abschnitt 1 - er wird nur bisher nicht angezeigt, weil
`_render_signal()` keinen Zugriff auf die offenen Positionen hatte.

Nutzer-Entscheidung: E-Mail-Politik "HALTEN nie" bleibt unveraendert (siehe
`_notify_hebel_signal()`/`_notify_spot_signal()`, `scheduler/background.py`,
beide pruefen `signal.action == "HALTEN"` als fruehen Return - unabhaengig
von offener Position, das war schon immer so). Nur die GUI-Anzeige wird
nachgezogen.

### Umsetzung

`ui/hebel_view.py`:
- Neues Instanzfeld `self._offene_positionen: dict[(symbol, richtung),
  HebelPosition]`, in `refresh()` direkt nach dem bereits vorhandenen
  `db.get_open_hebel_positions()`-Aufruf befuellt (kein neuer DB-Zugriff -
  `refresh()` hatte die Positionsliste bereits fuer das separate
  "Offene Hebel-Positionen"-Panel geladen, wird jetzt zusaetzlich fuer die
  Signal-Detail-Anzeige indiziert).
- `_render_signal()`: neuer Block am Ende von Abschnitt 1, NUR wenn
  `signal.action == "HALTEN"` UND ein Eintrag fuer `(signal.symbol,
  signal.richtung)` in `self._offene_positionen` existiert - zeigt Hebel,
  Eigenkapital, Eroeffnungsdatum und (falls vorhanden) den geschaetzten
  Liquidationspreis der bestehenden Position. Bewusst als "(Stand letzter
  Sync)" gekennzeichnet, um klarzustellen: das ist NICHT neu fuer dieses
  HALTEN-Signal berechnet, sondern der zuletzt synchronisierte Positions-
  Zustand (identisch mit der Zahl im "Offene Hebel-Positionen"-Panel).

**Bewusst NICHT angefasst:**
- `scheduler/background.py`s E-Mail-Guards (`action == "HALTEN"` -> return) -
  Nutzer-Entscheidung, "HALTEN nie" bleibt unveraendert.
- `ui/signals_view.py` (Spot) - Spot kennt keine Hebel-Positionen/
  Liquidationspreise, dieses Thema betrifft ausschliesslich `ui/hebel_view.py`.

**Verifiziert:** Tk-Smoke-Test (isolierte Temp-DB, kein sichtbares Fenster) mit
3 Faellen: (1) HALTEN OHNE offene Position (VIRTUAL) - Abschnitt 1 bleibt wie
zuvor ohne Positions-Zeile (Regression). (2) HALTEN MIT offener Position
(HYPE) - neue Zeile korrekt mit Hebel/Eigenkapital/Datum/Liquidationspreis.
(3) ERÖFFNEN (LINK) - bestehende `hebel_final`-Anzeige unveraendert, keine
faelschliche Positions-Zeile. Compile-/Import-Regressionscheck `ui/hebel_view.py`.

## Nachtrag (2026-07-27): LLM-Budget-Anzeige/-Zaehlung nach Groq-Entfernung + Z.ai-Gegenpruefungs-Umbau nachgezogen

Nutzer-Nachfrage anhand von zwei Remote-Steuer-Seite-Screenshots: "LLM-Budget
heute (Krypto)" und "API-Status: LLM-Anbieter" pruefen, ob nach den
juengsten Aenderungen (Groq aus der automatischen Kette entfernt, Z.ai macht
pro Hebel-Signal 2 zusaetzliche Abfragen) etwas angepasst werden sollte.

### Fund 1: Z.ai-Budget-Buchhaltung war seit dem Gegenpruefungs-Umbau toter Code

`agent/krypto/budget_allocator.py` hatte seit 2026-07-26 (Commit, in dem
Z.ai von einer primaeren Analyst-Fallback-Stufe zur dedizierten
Gegenpruefungslogik umgebaut wurde) noch die komplette alte
Budget-Buchhaltung dafuer (`zai_taegliches_budget` in config.yaml,
`tages_verbraucht["zai"]`, `tages_budget["zai"]`,
`AllocationResult.zai_calls_verbraucht`/`zai_budget_erschoepft`) - konnte
aber strukturell nie mehr > 0 werden, weil Z.ai in KEINER `calls`-Liste der
3 Tiers mehr auftaucht (bereits im damaligen Modul-Docstring als "bewusst
nicht entfernt, kein funktionaler Schaden" dokumentiert). Gleichzeitig wurde
die ECHTE Z.ai-Last durch die Gegenpruefung (1 Aufruf/Spot-Signal, 2
Aufrufe/Hebel-Signal - Konsistenz-Check UND Richtungs-Abgleich sind zwei
unabhaengige Calls) nirgends gezaehlt oder angezeigt.

**Fix:**
- `database/db.py`: neue `count_zai_gegenpruefung_calls_today()` - zaehlt
  echte Z.ai-Gegenpruefungs-Aufrufe seit Mitternacht UTC (Spot-Konsistenz +
  Hebel-Konsistenz + Hebel-Richtung, jeweils separat gezaehlt, da unabhaengig
  scheitern koennen). REIN INFORMATIV, kein Tagesdeckel (Z.ai hat laut
  Nutzer-Vorgabe keinen, nur den 120/Min-Rate-Limiter im Client selbst).
- `remote/status.py::_get_budget_heute()`: neues Feld
  `zai_gegenpruefung_heute`, bewusst NICHT in `verbraucht_gesamt`/`gesamt`
  eingerechnet (Z.ai ist kein primaerer Analyst mehr, keine Ressourcen-
  Konkurrenz zum B-Tagesbudget) - gleiche Trennung wie bei
  `multi_asset_heute`.
- `remote/server.py`: neue Zeile "Z.ai-Gegenpruefung heute (Konsistenz+
  Richtung, kein Tagesdeckel)" in der LLM-Budget-Karte.
- `agent/krypto/budget_allocator.py`: die tote Zai-Budget-Buchhaltung
  komplett entfernt (`AllocationResult`-Felder, `tages_verbraucht`/
  `tages_budget`-Eintraege, beide `elif provider_name == "zai":`-Zweige in
  `_mit_fallback_chain()`), Modul-Docstring + zwei weitere stale
  Kommentarstellen ("Mistral->Groq->Gemini->Zai-Kaskade") korrigiert.
- `scheduler/background.py`: Log-Zeile um die toten Zai-Werte gekuerzt.
- `Basisinfos/config.yaml`: `zai_taegliches_budget`-Schluessel entfernt,
  `gemini_taegliches_budget`-Kommentar korrigiert ("dritte" -> "zweite und
  aktuell letzte Fallback-Stufe" - die Kette ist seit der Groq-Entfernung
  nur noch 2-stufig: Mistral -> Gemini).

### Fund 2: Groq-Eintrag im API-Status zeigte irrefuehrend rot

Groq wurde bereits am 2026-07-26 bewusst aus der automatischen Kette
entfernt (Commit "Groq aus automatischer Signal-Kette entfernt, Client
bleibt fuer manuelle Tests" - siehe project_groq_entfernung_2026-07-26.md),
bleibt aber fuer manuelle Einzelklicks nutzbar. Die "API-Status:
LLM-Anbieter"-Karte zeigte dafuer weiterhin rot "Fehler (vor 3 Tagen)" -
technisch korrekt (letzter tatsaechlicher Call schlug fehl/liegt lange
zurueck), aber irrefuehrend: rot suggeriert "hier ist etwas kaputt, das
repariert werden muss", nicht "wird absichtlich nicht mehr automatisch
aufgerufen".

**Fix:** `remote/server.py::renderApiHealthGroup()` - neues
`MANUAL_ONLY_SOURCES`-Set (aktuell nur `"groq"`). Bei `status === "fehler"`
UND manueller Quelle: neutrales Grau ("nur manuell · letzter Test vor Xd
fehlgeschlagen") statt Rot. Ein ECHTER Erfolg (`status === "ok"`) bleibt
weiterhin gruen "OK (vor X)" - eine erfolgreiche manuelle Pruefung ist
weiterhin eine gute Nachricht.

### Nebenbefund (kein Fix, nur geprueft): `groq_exhaustion_schwelle_fehlschlaege`
ist NICHT tot - wird weiterhin von `agent/kategorie_synthese.py` verwendet
(eigenstaendiger taeglicher Job, der Groq unabhaengig vom Budget-Allocator
in seiner eigenen Fallback-Kette nutzt) - bewusst unveraendert gelassen.

**Verifiziert:** `count_zai_gegenpruefung_calls_today()` synthetisch (3
Signale: 1 Spot-Konsistenz, 1 Hebel mit beiden Zai-Calls, 1 Hebel nur mit
Konsistenz -> korrekt 1+2+1=4). `_get_budget_heute()`-Integration End-to-End
(Config/Watchlist gemockt). `AllocationResult`-Felder korrekt bereinigt.
`run_budget_allocator()` Smoke-Test (aktiv=False fruehzeitiger Return,
aktiv=True mit leerer Watchlist) laeuft ohne Fehler. YAML-Parse-Check
config.yaml. Compile-/Import-Regressionscheck aller 6 geaenderten
Python-Dateien.

## Nachtrag (2026-07-27): Mindestziel/MFE-Tracking - unabhaengige Erfolgsmessung neben Take-Profit

Ausloeser: Nutzer bat um eine Experten-Bewertung der Performance-Messung
(Backward-Tracking, siehe Kap. 9/16) - Ergebnis: solide Grundlage
(R-Multiple, Kalibrierungskurve, Forward-statt-Backtest-Methodik), aber die
bestehende Trefferquote misst nur "wurde exakt die Take-Profit-Zone
getroffen", nicht "war die Richtung wenigstens zeitweise richtig". Nach
Nutzer-Rueckfrage klar in zwei Ebenen getrennt.

### Ebene 1: sofort bei Signal-Erstellung (rein arithmetisch, kein Backward-Tracking noetig)

Neue Felder `mindestziel_usd`/`mindestziel_zeitraum_tage_geschaetzt` auf
`signals`/`hebel_signals`, berechnet in `agent/krypto/pipeline.py`/
`hebel_pipeline.py` direkt vor dem `Signal()`/`HebelSignal()`-Konstruktor-
aufruf, ueber neue Funktionen in `backward_tracking.py`:

- `mindestziel_preis(entry_mid, risiko_distanz, richtungstreffer_mindest_crv,
  ist_short)`: Min-Kurs = Entry + 1x Risikodistanz (dieselbe Distanz wie der
  Stop-Loss, nur in die guenstige Richtung) - CRV-Schwelle konfigurierbar
  (`backward_tracking.richtungstreffer_mindest_crv`, Default 1.0, bewusst
  niedriger als CRV_MINIMUM=2.0 der bestehenden Take-Profit-Vorgabe). Bei
  Hebel richtungsabhaengig (SHORT spiegelt die Distanz unter den Entry).
  Take-Profit (bereits vorhanden) ist das Max-Ziel-Gegenstueck.
- `schaetze_mindestziel_zeitraum_tage(ziel_preis, entry_mid, ohlc_rows)`:
  rechnerisch ANGENOMMENE Anzahl Tage bis zum Mindestziel = Kursdistanz /
  durchschnittliche Tages-High-Low-Spanne der letzten 14 bereits gehandelten
  Tage vor Signal-Erstellung (Random-Walk-Annahme). Kein Versprechen, kann
  verfehlt werden - explizit so gekennzeichnet in GUI/E-Mail.

### Ebene 2: erst nachtraeglich per Backward-Tracking (kann naturgemaess erst nach Zeitablauf feststehen)

`outcome_max_realisiertes_crv` (Maximum Favorable Excursion - hoechstes je
erreichtes guenstiges CRV, richtungsabhaengig) + `outcome_mindestziel_
erreicht_am` (Datum des ersten Treffers). Laeuft PARALLEL zur bestehenden
TP/SL/Liquidation-Aufloesung in `check_signal_outcome()`/`check_hebel_
signal_outcome()` mit, veraendert deren Ergebnis NICHT (Mindestbeobachtung/
Zonen-Reaffirmation-Gates bleiben unberuehrt) - auch ein spaeter per
Stop-Loss/Ueberholt/Abgelaufen aufgeloestes Signal bekommt seinen
tatsaechlichen Zwischenhoehepunkt persistiert. Neue Aggregationsfunktion
`compute_richtungstreffer_quote()` (breiter gefasst als `compute_win_rate_
fact()` - zaehlt auch spaeter ueberholte/abgelaufene Signale mit, wenn sie
zwischenzeitlich in die richtige Richtung liefen), zeigt "Ø Tage bis
Mindestziel" nur bei n>=15 als empirisch belastbar an.

### Anzeige

- GUI (`ui/signals_view.py`/`ui/hebel_view.py`): Mindestziel-Zeile direkt
  neben der bestehenden Take-Profit-Zeile im Detail-Panel.
- E-Mail (`scheduler/background.py`): neue `_formatiere_mindestziel()`-
  Helper-Funktion, in allen 3 E-Mail-Buildern (Spot/Hebel/Multi-Asset)
  verdrahtet.
- Remote-Steuer-Seite (`remote/status.py`/`server.py`): neue Karte
  "Richtungstreffer-Quote (Mindestziel/MFE)".
- `extract_notebook_diagnose.py`: alle 4 neuen Felder in den Export-
  Spaltenlisten fuer Spot- und Hebel-Signale aufgenommen.

Bewusst NICHT umgesetzt: LLM-Prompt-Wiring (Werte existieren zwar zum
LLM-Erzeugungszeitpunkt, aber eine Rueckkopplung waere eine eigene
Verhaltensaenderung), Positions-Lifecycle-Tracking, EUR-Variante von
mindestziel_usd.

**Verifiziert:** synthetische Tests (Spot LONG mit Zwischenhoehepunkt ueber
Mindestziel, der dann bis zum Stop-Loss reversiert - outcome_status bleibt
korrekt stop_loss_erreicht, MFE-Werte werden trotzdem korrekt persistiert;
Hebel SHORT-Szenario richtungsabhaengig; MFE persistiert auch beim
Ueberholt-Pfad). Compile-/Import-Regressionscheck aller 11 geaenderten
Python-Dateien (models.py, db.py, backward_tracking.py, hebel_backward_
tracking.py, pipeline.py, hebel_pipeline.py, signals_view.py, hebel_view.py,
background.py, status.py, server.py, extract_notebook_diagnose.py).

## Nachtrag (2026-07-27): HYPE-Hebel-Position blieb trotz Vollverkauf "offen" - Kredit-Rueckzahlung als zusaetzliches Signal

Nutzer-Fund: eine auf Bitpanda VOLLSTAENDIG geschlossene 3x-Hebel-Position (HYPE) blieb in der App mit reduziertem Eigenkapital (100 -> 67,14 EUR, exakt 1/3) als "offen" haengen - das Gegenteil des NEAR-Bugs vom 26.07. (dort wurde ein echter Teilverkauf faelschlich als Vollverkauf gewertet und verschwand komplett).

**Root Cause:** die am 26.07. eingefuehrte Mengen-Toleranz (`sell_qty >= running_qty * 0,995`) erkennt einen Vollverkauf einer GEHEBELTEN Position strukturell fast nie zuverlaessig - `sell_qty` deckt nur den eigenkapital-realisierenden Teil der Menge ab, der Rest (bei 3x Hebel: 2/3) wird direkt zur Kredit-Rueckzahlung verwendet, taucht also nie im "sell"-Leg auf.

**Fix:** `importer/bitpanda_margin_positions.py::reconstruct_margin_positions()` - zweites, unabhaengiges Vollstaendig-Signal: wird beim Close-Ereignis der GESAMTE verbleibende Kredit zurueckgezahlt (gleiche 99,5%-Toleranz), gilt das unabhaengig von `sell_qty` als Vollverkauf. Nutzt `e["borrow"]` (bisher nur fuer "open"-Ereignisse verwendet, negativ = Rueckzahlung). Reine ODER-Erweiterung, kann echte Teilverkaeufe nicht neu falsch klassifizieren (eine Teil-Reduktion zahlt den Kredit strukturell nur proportional, nie vollstaendig zurueck).

Neuer optionaler `debug_symbols`-Parameter (print-basiert, kein Verhaltenseinfluss) fuer den vollstaendigen Ereignis-/Entscheidungs-Trace inkl. Roh-Tags - bleibt fuer kuenftige aehnliche Faelle im Code.

**Korrektur der bereits haengengebliebenen Zeile:** neues Skript `fix_stuck_hebel_positions.py` (Projekt-Root) - rekonstruiert alle aktuell "offen" gefuehrten Positionen komplett neu aus der vollen Bitpanda-Historie (`existing=None`, schliesst Drift aus), zeigt Alt-vs-Neu-Vergleich, schreibt nur mit explizitem `--apply`-Flag. Muss auf dem Notebook laufen (echter API-Key + echte Produktiv-DB).

**Verifiziert:** synthetisch (3x-Hebel-Vollclose mit `sell_qty` bei nur 1/3 der Menge aber 100% Kredit-Rueckzahlung -> jetzt korrekt geschlossen; Gegentest echter Teilverkauf ohne Kredit-Rueckzahlung bleibt korrekt Teilverkauf). Compile-/Import-Regressionscheck.

## Nachtrag (2026-07-27, gleicher Tag): HYPE-Fix Runde 2 - "borrow"-Tag-Theorie war falsch, echte Ursache ist "repay"-Tag + sell_value

Der obige Fix (Runde 1) beruhte auf einer plausiblen, aber FALSCHEN Annahme: dass Bitpanda die Kredit-Rueckzahlung mit einem "borrow"-Tag versieht (analog zum OPEN-Ereignis). Der Nutzer bestand zurecht auf einer Pruefung an echten, unverarbeiteten Rohdaten, nachdem mehrere Notebook-KI-Zusammenfassungen widerspruechliche/erfundene Ergebnisse lieferten ("es gibt keinen Teilverkauf - die Position ist ZU"). Erst eine per `> datei.txt`-Redirect direkt in Notepad geoeffnete Rohausgabe von `fix_stuck_hebel_positions.py` lieferte vertrauenswuerdige Daten.

**Echte Root Cause:** Bitpanda taggt die HYPE-Rueckzahlung mit `"margin_trading.repay"`, nicht "borrow" - der Runde-1-Fix hat dieses Tag nie erkannt. Zusaetzlich ist die Rueckzahlung hier kein separates Leg, sondern im Verkaufserloes (`sell_value`) der Close-Transaktion enthalten: `sell_qty` deckte nur 66,4% der offenen Menge (Gebuehren + Kredittilgungsanteil verwaessern die Krypto-MENGE), aber `sell_value` deckte exakt 100% von `running_borrow` (400,00 EUR Erloes = 400,00 EUR Kredit).

**Fix (Runde 2):** drittes, unabhaengiges Signal in `reconstruct_margin_positions()` - deckt der Verkaufserloes (`sell_value`) mindestens 99,5% des verbleibenden Kredits (`running_borrow`), gilt das unabhaengig von `sell_qty` UND vom "borrow"-Tag als Vollverkauf. Der Runde-1-Fix (`borrow`-Tag-Signal) bleibt zusaetzlich bestehen fuer Faelle mit echtem separaten Rueckzahlungs-Leg.

**Verifiziert:** alle Runde-1-Tests weiterhin gruen (kein Regressionsverlust); neuer Test mit den EXAKTEN echten HYPE-Rohdaten (OPEN buy_value=600/buy_qty=11,58535869/borrow=400; CLOSE sell_value=400/sell_qty=7,69619853, Tags `margin_trading.close`+`margin_trading.repay`) liefert `sell_value/running_borrow=1,0000 => ist_vollstaendiger_verkauf=True`. Compile-/Import-Regressionscheck OK.

Commit `6c92103`.

## Nachtrag (2026-07-27, gleicher Tag): JIT-Historie-Nachladen + deterministische EUR-Ableitung - echter LINK-Vorfall

Nutzer meldete ein LINK-Hebel-Signal (LONG, ERÖFFNEN) mit Entry-Zone 6,81-6,91 EUR,
waehrend der Live-Kurs bereits bei 7,7 EUR stand - die Take-Profit-Zone
(7,80-7,90 EUR) lag praktisch auf dem aktuellen Kurs. Vom Nutzer explizit als
"make or break"-Thema eingestuft, mit der Vorgabe, die eigentliche Ursache zu
beheben statt nur ein Symptom (z.B. ein deterministisches Veto-Gate) zu
kaschieren - ein Gate haette die ohnehin knappe Signal-Frequenz weiter
reduziert, ohne das Grundproblem zu loesen.

**Root Cause (per Live-Diagnose an echten Notebook-Daten gefunden):** die
technische Analyse (RSI/MACD/EMA/ATR/Support-Resistance), aus der Entry-/
Stop-Loss-/Take-Profit-Zonen abgeleitet werden, basiert auf `price_history`
(CoinGecko)/`price_history_ohlc` (Kraken) - beide werden nur alle 24h per
Scheduler-Job aktualisiert. Der separate Live-Ticker (`price_cache`, 15-Min-
Takt, `staleness.py::PRICE_STALE_THRESHOLD_MINUTES`) war die ganze Zeit
korrekt - nur die technische Basis konnte bis zu 24h alt sein. Fachlich
bewertet (Nutzer-Vorgabe): eine feste 15-Min-Sequenz mit erst nach 6h+
sichtbarem Kurs-Gap ist fuer eine Entry-/Exit-Berechnung unbrauchbar.

**Zweiter, unabhaengiger Befund:** die EUR-Werte fuer Entry/Stop-Loss/Take-
Profit/Halte-Kriterium/Positionsgroesse kamen bisher direkt und ungeprueft aus
der eigenen `eur_von`/`eur_bis`-Antwort des LLM, nicht aus einer
deterministischen Umrechnung - obwohl der Nutzer in EUR auf Bitpanda handelt
("mir nutzt ein USD Stop Loss oder Schwelle nichts").

### Fix 1: JIT-Historie-Nachladen (Hebel + Spot, Krypto-only)

Neue Funktion `agent/krypto/pipeline.py::jit_refresh_asset_historie(conn,
asset, coingecko_client, kraken_client)` - laedt fuer GENAU EIN Asset die
juengste Tages-/OHLC-Historie unmittelbar VOR der eigentlichen Signal-
Generierung nach (USD-only), statt auf den naechsten 24h-Batch zu warten.
Eingebaut an den zwei echten Signal-Erzeugungsstellen:
`hebel_pipeline.py::generate_hebel_signal()` und `pipeline.py::
generate_signal()` (Spot) - bewusst NICHT in `_load_closes_and_ohlc()` selbst
(7 Aufrufstellen, u.a. der 15-Min-Screening-Loop ueber alle Kandidaten sowie
BTC/ETH-Kontextladungen - dort haette das Kontingent vervielfacht statt nur um
die Anzahl echter Signal-Ereignisse gewachsen).

**Burst-Schutz** (`JIT_REFRESH_MIN_ABSTAND_MINUTEN = 60`, Python-Konstante):
verhindert Mehrfach-Anfragen INNERHALB eines 15-Min-Allocator-Zyklus (Provider-
Fallback Mistral->Gemini, oder dasselbe Symbol gleichzeitig als LONG-Hebel-,
SHORT-Hebel- und Spot-Kandidat) - normale Wiederholungen (Hebel-Cooldown 3,5h,
Spot-Kern-Cooldown 8h) liegen weit darueber. Merkt sich bewusst den
VERSUCHSZEITPUNKT (Erfolg ODER Fehlschlag), nicht einen Erfolgs-Zeitstempel -
sonst wuerde ein echter CoinGecko-Ausfall bei jedem folgenden Signal-Versuch
erneut einen aussichtslosen Call ausloesen (analog zum 07-23-Staleness-
Watchdog-Vorfall, 390 blockierte Signale in einer Nacht). Zusaetzlich prueft
`CoinGeckoClient.in_cooldown()` (neu) einen aktiven 429-Backoff, um die
Signal-Erzeugung nicht bis zu 5 Minuten zu blockieren. P-10: ein Fehlschlag
(Netzwerk, fehlende coingecko_id/Kraken-Listing) darf die Signal-Erzeugung
nicht kippen - es wird einfach mit der bereits gespeicherten Historie
weitergearbeitet. Not-Aus per `Basisinfos/config.yaml`:
`datenquellen.marktdaten.jit_historie_refresh_aktiv` (Default `true`).

**Kontingent-Finanzierung (Voraussetzung, sonst waere das JIT-Nachladen ueber
das CoinGecko-Monatskontingent von 10.000 Calls gegangen):**
`_update_macro_snapshot()` rief bisher bei JEDER Signal-Generierung
ungecacht `/global` (BTC-Dominanz) ab. Jetzt: hoechstens 1x pro UTC-Tag (Pruefung
gegen `db.get_latest_macro_snapshot()`), der bestehende COALESCE-Upsert in
`upsert_macro_snapshot()` behaelt den Tageswert automatisch bei. Spart genau so
viele Calls, wie das JIT-Nachladen zusaetzlich kostet - netto quotenneutral.

**Blocker-Fix (Voraussetzung):** `database/db.py::upsert_price_history_points()`
schrieb bisher direkt (`price_usd = excluded.price_usd, price_eur =
excluded.price_eur`) statt mit COALESCE - ein USD-only-Nachladen haette die
EUR-Historie (fuer `ui/charts.py`s Euro-Chart, vom Nutzer ausdruecklich als zu
erhalten eingefordert) mit NULL ueberschrieben. Behebt zugleich einen bereits
bestehenden, unabhaengigen Bug: ein fehlgeschlagener EUR-Abruf im taeglichen
Job loeschte schon vorher echte EUR-Werte. Jetzt (analog `upsert_macro_
snapshot()`s Muster): `COALESCE(excluded.price_usd, price_history.price_usd)`
/ `COALESCE(excluded.price_eur, price_history.price_eur)`.

`api/history.py::backfill_history()` und `api/kraken_history.py::
backfill_ohlc()` haben dafuer einen neuen `currencies`-Parameter (Default
weiterhin beide Waehrungen - die taeglichen Scheduler-Jobs `backfill_all()`/
`backfill_all_ohlc()` sind dadurch unveraendert).

### Fix 2: Deterministische EUR-Ableitung (Hebel + Spot + Hedge)

Neuer Helper `agent/krypto/pipeline.py::eur_aus_usd(usd_wert,
eur_usd_fx_rate)` - identisches Muster wie das bereits produktive
`liquidationspreis_geschätzt_eur` in `hebel_risk_gate.py::post_check_hebel()`
(Live-EURCV-Snapshot, nicht die LLM-Eigenberechnung). Ersetzt die bisherige
`entry.get("eur_von")`-artige Weitergabe fuer Entry/Stop-Loss/Take-Profit/
Halte-Kriterium-Zielpreis/Positionsgroesse in `hebel_pipeline.py`,
`pipeline.py` (Spot) und `agent/hedge/pipeline.py` - alle drei hatten
`eur_usd_fx_rate` bereits im Scope. `_validate_hebel()` und das LLM-Schema/
der Prompt (`hebel_analyst.py`) bleiben bewusst unangetastet - das Modell darf
weiterhin `eur_von`/`eur_bis` liefern (bleibt in `groq_raw_response`
erhalten), es fliesst nur nicht mehr in die finale Signal-Struktur.
Beobachtungs-Log `log_eur_abweichungen()` vergleicht optional die LLM-eigene
EUR-Zahl mit dem deterministisch abgeleiteten Wert (>2% Abweichung ->
`logger.info()`), rein informativ, keine Verhaltensaenderung.

**Nebenfund in `agent/hedge/pipeline.py::_post_check_hedge()`:** die
Budget-Kappung und der Bull-Wahrscheinlichkeits-Deckel leiteten ihren eigenen
fx-Rate-Fallback bisher aus den LLM-eigenen `usd`/`eur`-Positionsgroessen-
Werten ab (`fx = proposed_usd / proposed_eur`), bevorzugt vor dem echten
`eur_usd_fx_rate` - jetzt ausschliesslich `eur_aus_usd()` mit dem echten Kurs.

**Bewusst NICHT mitgezogen:** `agent/aktien/pipeline.py`, `agent/rohstoff/
pipeline.py`, `agent/themen_etf/pipeline.py` - gleicher EUR-Bug, aber keine
lokal berechnete `eur_usd_fx_rate` (muesste neu ergaenzt werden) und ein
strukturell anderes, yfinance-basiertes Frische-Profil (Quotrix-Handelsfenster
Mo-Fr 07:30-23:00 CET, nicht 24/7, bereits eigene 5-Tage-Toleranz statt
Kryptos 2-Tage-Schwelle) - eigene Folge-Runde vorgesehen.

**Verifiziert:** COALESCE-Erhalt der EUR-Historie bei einem USD-only-Upsert
(inkl. Regressionstest, dass ein echter EUR-Update weiterhin normal
durchschlaegt); Burst-Schutz (Erst-Versuch erlaubt, Zweit-Versuch INNERHALB
der Sperrfrist blockiert, nach Ablauf wieder erlaubt, verschiedene Symbole
unabhaengig); `/global`-Tages-Cache (zwei `_update_macro_snapshot()`-Aufrufe
am selben Tag -> genau 1 CoinGecko-Call, BTC-Dominanz bleibt erhalten);
`eur_aus_usd()`-Unit-Tests (Normalfall, `usd_wert=None`, `fx_rate=None`,
`fx_rate=0`); End-to-End-Reproduktion des LINK-Vorfalls mit Fake-CoinGecko/
Kraken-Clients (genau 1 CoinGecko-Call, ausschliesslich `"usd"`, frischer Kurs
danach in `_load_closes_and_ohlc()` sichtbar, zweiter Aufruf innerhalb der
Sperrfrist macht keinen weiteren Call); Graceful-Degradation (beide Clients
werfen -> keine Exception; Asset ohne `coingecko_id` -> kein Call, kein
Fehler); Config-Schalter aus -> kein Call; `_post_check_hedge()` nutzt nach
dem Fix nachweislich den echten `eur_usd_fx_rate` statt einer aus der
LLM-Eigenangabe abgeleiteten Zahl (mit UND ohne verfuegbaren echten Kurs
geprueft); statischer Regressions-Grep bestaetigt keine verbliebenen rohen
`entry.get("eur_von")`-Vorkommen mehr in den drei geaenderten Dateien;
Compile-/Import-Regressionscheck ueber alle 7 geaenderten Module UND alle
bekannten Konsumenten (Aktien/Rohstoffe/Themen-ETF-Pipelines, Screening/
Marktscan/Budget-Allocator, Scheduler, Charts, GUI-Views, Remote-Status/
-Server) OK.

**Ausstehend:** echter Notebook-Lauf (Nutzer) - CoinGecko-Monatskontingent in
der ersten Woche gegen das Dashboard gegenchecken, ein echtes Signal
stichprobenartig nachrechnen (`entry_eur_von × fx_rate == entry_usd_von`),
EUR-Chart-Durchgaengigkeit bestaetigen. Beobachtungspunkte (kein Fix noetig):
moeglicherweise mehr Kandidaten passieren jetzt das P-10-Gate (hoehere
Mistral/Gemini-Auslastung moeglich); `signal_stabilitaet` koennte durch
haeufigere Kursaenderungen mehr Richtungswechsel zeigen als zuvor.

## Nachtrag (2026-07-27, gleicher Tag, Folge): Grundsatzfix Teil 2 - derselbe
JIT-/EUR-Fix fuer Aktien/Rohstoffe/Themen-ETF + ein unabhaengiger, schwerer
Rohstoff-Skalierungsbug

Der Nutzer stellte nach dem LINK-Fix explizit klar: "der Fix ist ein
Grundsatzfix, Link war nur der Ausloeser" - und fragte, ob fuer die drei
verbliebenen, yfinance-basierten Pipelines (Aktien, Rohstoffe, Themen-ETF)
noch etwas fehlt. Vertiefte Recherche (Explore- + Plan-Agent, alle Kernbefunde
selbst im Code nachverifiziert) ergab ein praeziseres, teils anderes Bild als
bei Krypto - vier Einzelfunde:

**1. EUR-Bug identisch vorhanden, aber KEIN neuer Ableitungs-Helfer noetig.**
Die vom 07-27-Nachtrag oben als "eigene Folge-Runde vorgesehen" markierte
Luecke (`entry.get("eur_von")` etc., unveraendert in allen drei Pipelines)
existierte tatsaechlich - aber `agent/hedge/pipeline.py` beweist bereits live,
dass das bestehende `eur_aus_usd()` fuer EUR-native UND USD-native Instrumente
gleichermassen korrekt ist (Regel 4 aller Analyst-Prompts: "berechne den
prozentualen Abstand EINMAL in USD und wende ihn auf EUR gleichermassen an" -
algebraisch unabhaengig von der Herkunftsrichtung des USD-Preises, siehe
Verifikation unten). Kein neuer, richtungsbewusster Helfer noetig - 1:1 dasselbe
Muster (`eur_aus_usd()`/`log_eur_abweichungen()`) wie bei Hedge/Spot/Hebel
uebernommen.

**2. Ein unabhaengiger, deutlich schwererer Fund bei der Vertiefung:**
`api/yfinance_history.py::get_full_ohlc_history(ticker, symbol, currency)`
speichert OHLC-Rohwerte OHNE Waehrungsumrechnung unter dem uebergebenen
`currency`-Label - alle drei Pipelines uebergaben dafuer hartkodiert `"USD"`,
unabhaengig von der tatsaechlichen Notierungswaehrung. Zwei Faelle
unterschiedlichen Schweregrads:
- **Aktien/Themen-ETF:** reines Label-Problem (Zahlen korrekt, nur die
  Waehrungsspalte bei EUR-nativen Tickern falsch beschriftet). Aktuell
  folgenlos fuer Aktien (nur USD-native VST/PLTR in der Watchlist), aber
  bereits aktiv falsch fuer alle 5 Themen-ETF-Symbole (VVMX/X136/EXH3/CEBS/
  ISOC, alle `.DE`/`.BE`, EUR-nativ).
- **Rohstoffe - ein echter, aktiver Zahlenfehler, kein Label-Problem:**
  `agent/rohstoff/pipeline.py::_ensure_ohlc_backfilled()` laedt/speichert die
  OHLC-Historie vom liquiden Futures-Kontrakt (GC=F/SI=F/HG=F/NG=F, USD,
  Groessenordnung ~4000 fuer Gold). `_rescale_ohlc_zum_etc_kurs()` (siehe
  Docstring vom 07-18, Rohstoff-Pipeline Phase 2) skaliert diese Reihe auf die
  tatsaechliche ETC-Preisebene (~18-20 USD) herunter - aber bisher NUR im
  Arbeitsspeicher, nie zurueck in die DB geschrieben. Direkt verifiziert:
  `agent/krypto/backward_tracking.py::check_signal_outcome()` (keine
  Assetklassen-Filterung) las genau diese unskalierte, gespeicherte Reihe und
  verglich sie gegen `take_profit_usd_von`/`stop_loss_usd_von` auf ETC-
  Preisebene (~18-20) - ein Futures-High von ~4000 erfuellt `high >= ~20`
  praktisch immer sofort. Das liess Rohstoff-KAUFEN/NACHKAUFEN-Signale seit
  Einfuehrung der Pipeline vermutlich fast immer sofort faelschlich als
  `take_profit_erreicht` aufloesen - korrumpiert nicht nur die Anzeige,
  sondern via `compute_win_rate_fact()` auch die `historische_erfolgsquote`,
  die als Fakt in jedes kuenftige Rohstoff-Signal zurueckfliesst (LLM bewertet
  seine eigene, durch den Bug verzerrte Erfolgsbilanz). **Der mit Abstand
  wichtigste Einzelfund dieser Runde.**

**3. Staleness strukturell schlechter als der urspruengliche Krypto-Zustand:**
Rohstoffe und Themen-ETF hatten GAR KEINEN Scheduler-Job (Aktien immerhin
einen taeglichen 24h-Job seit 07-19) - Historie wurde ausschliesslich beim
Signal-Lauf selbst nachgeladen, und nur nach Ueberschreiten der 5-Tage-
Schwelle. Bis zu 5 statt 1 Tag, ohne jeden autonomen Auffrisch-Mechanismus.

**4. Kein CoinGecko-Kontingent-Analogon noetig:** yfinance dokumentiert
keinerlei Monats-/Rate-Limit in diesem Codebase (nur Timeout-Guards). Der
Krypto-Fix hatte einen eigenen "Schritt 0" (`/global`-Deckelung), um das
JIT-Nachladen kontingent-neutral zu finanzieren - hier bewusst nicht
nachgebaut, da nicht noetig.

### Commit 1: Rohstoff-Skalierung tatsaechlich persistieren (hoechste Prioritaet)

`agent/rohstoff/pipeline.py::generate_signal()`: nach `_rescale_ohlc_zum_etc_kurs()`
einen `db.upsert_ohlc_points(conn, ohlc_history)`-Schreibvorgang
ergaenzt. Bewusste Verhaltensaenderung, kein reiner Nebeneffekt: der
Skalierungsfaktor (`etc_preis_usd / closes[-1]`) aendert sich bei jedem Lauf
leicht mit dem aktuellen Futures/ETC-Verhaeltnis - jeder Schreibvorgang
ueberschreibt die GESAMTE historische Reihe mit dem jeweils neuesten
Verhaeltnis. Erwuenscht (haelt die Reihe konsistent zum aktuell bekannten
Faktor), aber nicht zeilenweise idempotent - hier explizit dokumentiert, damit
niemand spaeter einen Bug vermutet.

### Commit 2: Deterministische EUR-Ableitung (alle drei Pipelines)

`eur_aus_usd()`/`log_eur_abweichungen()` (aus `agent/krypto/pipeline.py`)
1:1 wie bei Hedge/Spot/Hebel eingebaut: `eur_usd_fx_rate` aus dem Live-EURCV-
Snapshot abgeleitet, alle 7 betroffenen Felder (`position_size_eur`,
`entry_eur_von/bis`, `stop_loss_eur_von/bis`, `take_profit_eur_von/bis`,
`halte_kriterium_ziel_preis_eur`) von der rohen LLM-Antwort auf die
deterministische Ableitung umgestellt. `agent/aktien/pipeline.py` zusaetzlich:
neues Gate-Problem `price_snap.price_usd is None`, falls ein kuenftiges
EUR-natives Aktien-Asset ohne echten `eur_usd_fx_rate` sauber scheitern soll
statt still weiterzulaufen. Analyst-Prompts/Schema bewusst unveraendert - das
LLM darf weiter `eur_von`/`eur_bis` liefern, nur nicht mehr uebernommen.

### Commit 3: OHLC-Waehrungslabel Aktien/Themen-ETF + Migration

Neue Funktion `api/yfinance_client.py::resolve_native_currency(yfinance_symbol)`
- billiger `fast_info.get("currency")`-Call (kein `.history()`),
P-10-sicher (`None` bei Fehlschlag, Aufrufer faellt auf `"USD"` zurueck).
`agent/aktien/pipeline.py` und `agent/themen_etf/pipeline.py` bekamen je einen
`_resolve_asset_currency(asset)`-Helper sowie einen um `currency`
parametrisierten `_ensure_ohlc_backfilled()`/`_load_ohlc()`. Themen-ETFs
SPY-Benchmarkserie bleibt hartkodiert `"USD"` (SPY ist echt USD-nativ).
Rohstoffe bewusst NICHT parametrisiert - Futures sind genuin USD, das ist kein
Label- sondern ein reines Skalierungsproblem (siehe Commit 1).

Einmaliges Migrationsskript `migrate_themen_etf_ohlc_currency.py`
(Projekt-Root, Dry-Run per Default, `--apply` fuer echtes Schreiben) relabelt
die 5 betroffenen Themen-ETF-Symbole (VVMX/X136/EXH3/CEBS/ISOC) von
`currency='USD'` auf `'EUR'`. Sicher wegen `PRIMARY KEY (symbol, currency,
date)` und keiner bereits existierenden `'EUR'`-Kollision (verifiziert). Kein
Blocker, falls nicht sofort ausgefuehrt - die 5-Tage-Staleness-Schwelle
wuerde die falsch beschrifteten Zeilen ohnehin binnen 5 Tagen durch den
korrigierten Code selbst heilen. **Muss vom Nutzer auf dem Notebook (echte
Produktions-DB) ausgefuehrt werden, NIE auf dem Desktop** - analog zum
`fix_stuck_hebel_positions.py`-Workflow vom HYPE-Fix.

### Commit 4: JIT-Nachladen fuer alle drei Pipelines + Config

Neue Funktion `jit_refresh_ohlc()` in jeder der drei Pipeline-Dateien
(eigener, unabhaengiger Burst-Schutz-Dict pro Datei - Symbole ueberschneiden
sich nicht zwischen Assetklassen), gleiches attempt-based 60-Minuten-Muster
wie beim Krypto-Fix. Aufrufstellen jeweils direkt vor dem bestehenden
`_ensure_ohlc_backfilled()` in `generate_signal()`
(`agent/multi_asset_batch.py` ruft `generate_signal()` ohnehin auf, ist also
automatisch mitabgedeckt). Rohstoff-Besonderheit: der JIT-Aufruf laedt ueber
`SYMBOL_ZU_FUTURES_TICKER[asset.symbol]` mit `currency="USD"` und laeuft VOR
`_ensure_ohlc_backfilled()`/`_rescale_ohlc_zum_etc_kurs()`, damit die frisch
geladene Futures-Reihe auch reskaliert+persistiert wird (Commit 1). Eigener,
neuer Config-Schalter `datenquellen.marktdaten_wertpapiere.jit_historie_
refresh_aktiv` (bewusst getrennt von Kryptos `datenquellen.marktdaten.*` -
reiner operativer Not-Aus gegen einen yfinance-Ausfall, KEINE
Kontingent-Finanzierung wie bei Krypto, da yfinance keine dokumentierte Quote
kennt).

### Explizit NICHT Teil dieser Runde

Kein neuer richtungsbewusster/bidirektionaler Umrechnungs-Helfer (algebraisch/
live durch Hedge bereits bewiesen unnoetig); keine CoinGecko-Analogie-
Kontingent-Finanzierung (yfinance hat keine dokumentierte Quote); `post_
check()`s fehlende `current_price`/`atr_value`/`dates`/`closes`-Kwargs bei
Aktien/Rohstoff/Themen-ETF/Hedge (verifiziert folgenlos, gated durch
`richtungswende is None`, eigenes kuenftiges Ticket falls je ausgeweitet); JIT-
Nachladen fuer die Themen-ETF-SPY-Benchmarkserie (niedrige Prioritaet, rein
informativer Fakt); Migration bereits gespeicherter Aktien-OHLC-Zeilen (aktuell
keine EUR-native Aktie in der Watchlist, nichts zu migrieren).

**Verifiziert (synthetisch, In-Memory-SQLite, keine Produktions-DB beruehrt):**
Rohstoff-Skalierungs-Regressionstest (persistierte Reihe liegt nach dem Fix
auf ETC-Skala statt Futures-Skala; `check_signal_outcome()` loest ein
`take_profit_usd_von=20.0`-Signal NACH dem Fix nicht mehr sofort auf, OHNE
Fix beweisbar schon); EUR-Ableitung-Identitaetstest (`eur_aus_usd()`
numerisch identisch zur unabhaengig nachgerechneten Regel-4-Formel, inkl.
Graceful-Degradation bei fehlendem `usd_wert`/`fx_rate`); OHLC-Label-
Migrationstest (nach UPDATE liefert `get_ohlc_history(..., "EUR")` die
migrierten Zeilen, `"USD"` liefert nichts mehr; `ui/charts.py::
KRAKEN_PAIR_MAP` bestaetigt frei von allen 5 Themen-ETF-Symbolen); JIT-
Burst-Schutz (zwei Aufrufe kurz hintereinander -> genau 1 echter Abruf, nach
Ablauf des 60-Min.-Fensters wieder erlaubt); Graceful-Degradation (fehlendes
`yfinance_symbol`, werfender Fake-Client, Config-Schalter aus - je kein
Fehler, kein Abruf); statischer Regressions-Grep (keine verbliebenen rohen
`entry.get("eur_von")`-Vorkommen ausserhalb der bewusst beibehaltenen
Beobachtungs-Vergleiche in `log_eur_abweichungen()`); Compile-/Import-
Regressionscheck ueber alle 6 geaenderten Module UND alle bekannten
Konsumenten (`agent/multi_asset_batch.py`, `scheduler/background.py`,
`ui/charts.py`, `remote/status.py`, `remote/server.py`) OK.

**Ausstehend:** echter Notebook-Lauf (Nutzer) - ein Rohstoff-Signal nach dem
Fix beobachten, ob `outcome_status` nicht mehr sofort `take_profit_erreicht`
wird; `historische_erfolgsquote` fuer Rohstoffe nach einigen Tagen erneut
gegenchecken (sollte sich strukturell veraendern, da die bisherige Quote auf
dem Skalierungsbug beruhte); Migrationsskript `migrate_themen_etf_ohlc_
currency.py --apply` auf dem Notebook ausfuehren.

## Nachtrag (2026-07-27, gleicher Tag, Folge): NEAR-Hebel-Signal-Review -
Mindestziel-EUR-Luecke gefunden und geschlossen

Nutzer bat um eine Konsistenzpruefung eines konkreten NEAR-LONG-Hebel-Signals
gegen den frisch gepushten Grundsatzfix (EUR/USD-Umrechnung, Ablaufkette). Zwei
Punkte geprueft:

1. **Bestaetigt, echt: Mindestziel hatte nie eine EUR-Ableitung.** Anders als
   Entry/Stop-Loss/Take-Profit/Halte-Kriterium/Liquidationspreis/
   Eigenkapitalbedarf (alle laengst deterministisch in EUR via `eur_aus_usd()`)
   zeigte `_formatiere_mindestziel()` (`scheduler/background.py`) das
   Mindestziel nur in USD - `HebelSignal`/`Signal` hatten schlicht kein
   `mindestziel_eur`-Feld (Luecke seit Einfuehrung des Mindestziel/MFE-
   Feature am selben Tag). Gefixt: neues additives Feld `mindestziel_eur` in
   beiden Dataclasses (`database/models.py`), additive Migration (dieselbe
   Migrationsfunktion wie `mindestziel_usd`, `database/db.py`), Ableitung via
   `eur_aus_usd(mindestziel_usd_wert, eur_usd_fx_rate)` in `agent/krypto/
   pipeline.py`/`hebel_pipeline.py`, Anzeige nachgezogen in E-Mail
   (`scheduler/background.py::_formatiere_mindestziel()`) UND beiden
   App-Detail-Panels (`ui/hebel_view.py`, `ui/signals_view.py` - vorher
   ebenfalls USD-only, derselbe Fund), sowie im Diagnose-Export
   (`extract_notebook_diagnose.py`).

2. **Zurueckgezogen: vermeintliche CRV-Diskrepanz war ein eigener
   Rechenfehler, kein Systemfehler.** Erster Verdacht: der gedruckte CRV-Wert
   (2,79) liess sich aus der gedruckten EUR-Entry/Stop-Loss/Take-Profit-Zone
   nicht nachrechnen (~3,57 statt 2,79). Code-Pruefung (`hebel_risk_gate.py::
   post_check_hebel()`, Zeilen ~994-1010) zeigt: `entry`/`stop_loss`/
   `take_profit` werden einmal aus der LLM-Antwort gelesen und danach nie
   veraendert - CRV, `sl_abstand_relativ` UND die spaetere EUR-Ableitung
   (`hebel_pipeline.py`) lesen beweisbar dieselben, unveraenderten USD-
   Rohwerte. Ursache der scheinbaren Diskrepanz: `format_money()`
   (`ui/formatting.py`) rundet ab `|Wert| ≥ 1` auf 2 Nachkommastellen - bei
   NEAR (~1,6 EUR, ~2-3% Stop-Loss-Abstand) reicht diese Rundung aus, um beim
   Zurueckrechnen aus den ANGEZEIGTEN Zonenwerten einen CRV zwischen ~2,56 und
   ~5,40 zu ergeben, obwohl intern nur EIN exakter Wert (2,79) existiert. Kein
   Fix noetig - Lehre: bei engen Hebel-Stops (Coins im 1-5-EUR-Bereich) ist der
   gedruckte CRV/SL-Abstand-Wert selbst massgeblich, eine manuelle Nachrechnung
   aus der 2-Dezimal-EUR-Zone ist bei kleinen Stop-Distanzen nicht zuverlaessig
   moeglich.

**Verifiziert:** synthetischer Migrations-/Rundtrip-Test (`mindestziel_eur` in
beiden Tabellen, `eur_aus_usd()`-Identitaet, Insert+Read fuer Signal UND
HebelSignal, E-Mail-Zeile zeigt EUR, Graceful-Degradation ohne
`mindestziel_eur`); Compile-/Import-Regressionscheck ueber alle 8 geaenderten
Module + bekannte Konsumenten.

## Nachtrag (2026-07-27): Z.ai-Gegenpruefung auf alle 6 Signal-Pipelines ausgeweitet (Konsistenz-Check UND Richtungs-Abgleich)

Auslöser: Prüfung eines echten ALGO-Spot-Signals ("wo ist hier ZAI?"). Analyse
ergab eine gewachsene, asymmetrische Teil-Umsetzung: Krypto-Hebel hatte beide
Z.ai-Calls (Konsistenz-Check + unabhängiger Richtungs-Abgleich) plus einen
E-Mail-Wartemechanismus; Krypto-Spot nur den Konsistenz-Check ohne
Wartemechanismus (Z.ai-Ergebnis kam strukturell fast nie rechtzeitig in die
E-Mail); Aktien/Rohstoffe/Themen-ETF/Hedge hatten gar keine Z.ai-Integration.
Nutzer-Vorgabe: **"soll vom Grundprinzip bei allen Assets ident
funktionieren"** - beide Z.ai-Calls für alle 6 Pipelines.

### Bestätigt vor der Umsetzung: Fakten sind bereits 1:1 kompatibel

`baue_fakten()`/`baue_objektive_fakten()` (`agent/krypto/gegenpruefung.py`)
waren bereits asset-neutral - alle Krypto-exklusiven Parameter
(`funding_rate_stunde`, `optionsmarkt_skew`) sind optional und werden bei
`None` einfach aus dem Fakten-Dict weggelassen, kein Fake-Wert nötig.

### Zwei technische Lücken geschlossen

1. **DB-Schema-Asymmetrie:** `hebel_signals` hatte bereits alle 5
   Z.ai-Spalten, `signals` (gemeinsam für Krypto-Spot/Aktien/Rohstoffe/
   Themen-ETF/Hedge) nur die 2 Konsistenz-Check-Spalten. Additive Migration:
   `_ZAI_GEGENPRUEFUNG_SPOT_NEW_COLUMNS` (`database/db.py`) um
   `zai_eigene_richtung`/`zai_uebereinstimmung`/`zai_richtung_kurzbegruendung`
   erweitert; `update_signal_zai_gegenpruefung()` auf dieselbe 5-Parameter-
   Signatur wie `update_hebel_signal_zai_gegenpruefung()` gebracht (3 neue
   Parameter mit `None`-Default, bestehende 4-Parameter-Aufrufer bleiben
   kompatibel); `Signal`-Dataclass (`database/models.py`) um die 3 Felder
   erweitert (1:1 wie `HebelSignal`).
2. **4 Pipelines ohne `zai_client`-Parameter und ohne Plumbing:** kein
   `generate_signal()` von Aktien/Rohstoffe/Themen-ETF/Hedge kannte
   `zai_client`; die Multi-Asset-Batch-Kette (`main.py` → `build_scheduler()`
   → `multi_asset_batch_job()` → `run_multi_asset_batch()`) reichte
   `zai_client` nirgends durch, obwohl er in `build_scheduler()` bereits im
   Scope war (wird dort schon an `hebel_screening_job` durchgereicht).

### Gemeinsame Logik statt Duplikation (`agent/krypto/gegenpruefung.py`)

`hebel_pipeline.py::_zai_gegenpruefung_im_hintergrund()` (die Thread-Funktion,
die beide Z.ai-Calls sequentiell ausführt und EIN kombiniertes DB-Update
schreibt) wurde nach `gegenpruefung.py` verschoben und in
`fuehre_beide_calls_im_hintergrund()` umbenannt - parametrisiert über
`update_fn` (entweder `db.update_hebel_signal_zai_gegenpruefung` oder das neu
erweiterte `db.update_signal_zai_gegenpruefung`, seit deren Angleichung
identische Signatur). Von allen 6 Pipelines wiederverwendet statt sechsmal
dupliziert.

Neue Funktion `richtung_aus_action(action, ist_hedge_invertiert=False)`: die
Spot-family (alle außer Hebel) hat kein echtes `richtung`-Feld (LONG/SHORT),
nur Action-Verben. Deterministisches Mapping: `KAUFEN`/`NACHKAUFEN` → `LONG`,
`VERKAUFEN`/`TAUSCHEN` → `SHORT`, `HALTEN` → `None` (kein Vergleich, analog
zu Hebel-Sonderfällen).

### Design-Entscheidung: Hedge-Invertierung (mit Nutzer abgestimmt)

Hedge-Instrumente sind inverse Absicherungen - `KAUFEN` (Hedge aufbauen)
korreliert mit einer **bärischen** Gesamtmarkterwartung, nicht mit einer
bullischen Erwartung an das Hedge-Instrument selbst. Die an Call 2
übergebenen Fakten sind bei Hedge ohnehin nur Makro-/Regime-Fakten (keine
Einzeltitel-Technikanalyse, siehe `agent/hedge/pipeline.py` Modul-Docstring),
Z.ais `eigene_richtung` bedeutet dort faktisch "Einschätzung zum
Gesamtmarkt". Entschieden: **deterministische Invertierung in Python**
(`ist_hedge_invertiert=True`, nur in `agent/hedge/pipeline.py` gesetzt, dort
IMMER `True` - diese Pipeline verarbeitet ausschließlich Hedge-Instrumente,
kein Symbol-Lookup nötig), KEIN neuer Fakt/Prompt-Zweig für Z.ai (Nutzer
erwog auch "Z.ai die Funktion des Assets erklären" als Alternative -
verworfen: die Invertierung ist hier ein einzelnes, fest verdrahtetes
Boolean, keine wartungsbedürftige neue Regel; ein Prompt-Zweig hätte
zusätzliches Fehlinterpretations-Risiko ins LLM-Urteil getragen, entgegen dem
bestehenden Architekturprinzip, den eigentlichen Abgleich deterministisch in
Python zu halten).

### Bestätigt (keine Änderung nötig): JA/NEIN ist bereits erzwungen

Nutzer-Nachfrage, ob beim Richtungs-Abgleich "JA/NEIN-Entscheidungen
erzwungen" werden sollen - Abgleich mit der ursprünglichen Absprache vom
2026-07-26 (Z.ai darf selbst LONG/SHORT/NEUTRAL antworten, Live-Test zeigte
echte Modell-Unsicherheit bei Grenzfällen, Nutzer entschied damals explizit
"Rauschen akzeptieren, keine Prompt-Nachschärfung"): das JA/NEIN ist bereits
auf der Ebene des Vergleichsergebnisses (`uebereinstimmung`) erzwungen -
NEUTRAL zählt deterministisch als "nein", nie als "unklar". Keine
Prompt-Änderung nötig, weder bei Hebel noch bei der Erweiterung.

### E-Mail: Re-Fetch statt Hebel-artigem Wartemechanismus

Für Multi-Asset-Batch bewusst KEIN Poll-Wait-Mechanismus wie bei Hebel
(`_sende_hebel_email_mit_zai_wartezeit()`): die Batch-Schleife verarbeitet
bis zu 13 Assets sequentiell, bevor die E-Mail-Benachrichtigung überhaupt
beginnt - für die meisten Signale ist die Z.ai-Hintergrundprüfung durch diese
Restlaufzeit bereits fertig. Stattdessen in
`scheduler/background.py::multi_asset_batch_job()` ein günstiger Re-Fetch
per `db.get_signal_by_id()` direkt vor `_notify_multi_asset_signal()` -
fehlschlagender Re-Fetch verhindert die E-Mail nicht (Fallback aufs
ursprüngliche Objekt).

### Bewusst unverändert: manueller "Signal berechnen"-Button

`ui/signals_view.py::_run_pipeline()` reicht `zai_client` an KEINE der 6
Pipelines durch - das war bereits vor dieser Runde so (auch für Krypto-Hebel/
Spot), eine bestehende, bewusste Scope-Grenze. Sie jetzt nur für die 4 neuen
Pipelines aufzubrechen hätte eine neue Asymmetrie geschaffen statt eine zu
schließen - unverändert gelassen.

### Verifiziert

Compile-/Import-Regressionscheck über alle 11 geänderten Module; additive
Migration (frische + simulierte Alt-DB, erneuter Migrationslauf ohne
Exception); `update_signal_zai_gegenpruefung()` mit 4 UND 5 Positions-
argumenten; `Signal`-Dataclass-Rundtrip für alle 3 neuen Felder;
`richtung_aus_action()` alle Kombinationen inkl. Hedge-Inversion (Regressions-
schutz: `KAUFEN` → `SHORT` bei `ist_hedge_invertiert=True`);
`fuehre_beide_calls_im_hintergrund()` mit Mock-Client (genau EIN kombinierter
Update-Aufruf, korrekte `ja`/`nein`-Berechnung, Call-1-Fehlschlag verhindert
Call-2-Update nicht); Signatur-Regressionscheck aller 4 neuen Pipelines +
der Plumbing-Kette (`run_multi_asset_batch()`, `multi_asset_batch_job()`).
**Echter Notebook-Lauf ERLEDIGT (2026-07-30):** frischer Produktions-Export
bestätigt Z.ai-Richtung für alle 4 neuen Pipelines (Aktien n=1, Rohstoffe n=1,
Themen-ETF n=3, Hedge n=2 - DBPK/3QSS). Hedge-Inversion mit einem echten
`action=VERKAUFEN`-Fall bestätigt (`zai_eigene_richtung=SHORT` korrekt als
Abweichung gegen die invertierte Erwartung LONG gewertet). Aktien/Rohstoffe
mit n=1 noch zu duenn fuer eine Trefferquoten-Aussage, aber die Grund-
Verdrahtung funktioniert nachweislich in allen 4 Pipelines. Details siehe
[[project_zai_alle_6_pipelines_ausgeweitet]].

## Nachtrag (2026-07-27): Hebel-Tab-Anzeigefilter - deaktivierte Symbole ohne offene Position + Zeit-Switch

Auslöser: Nutzer-Wunsch, deaktivierte Symbole (Hebel-Prüfung-Toggle aus)
automatisch aus der Hebel-Tab-Liste zu entfernen. Der bereits am selben Tag
gefixte KAITO-Fund (`87f325b`) deckte nur die Warteliste
(`get_pending_hebel_candidates()`) ab - die Haupt-Tabelle zeigt zusätzlich
das jeweils letzte generierte Signal je Symbol+Richtung
(`get_latest_hebel_signal_per_symbol_and_richtung()`), das den Toggle gar
nicht kennt. Ohne offene Position bleibt die letzte Zeile eines deaktivierten
Symbols dadurch für immer stehen.

**Bewusst NICHT an der geteilten Funktion selbst gefixt:**
`get_latest_hebel_signal_per_symbol_and_richtung()` wird an 4 weiteren,
echten Business-Logik-Stellen verwendet (`budget_allocator.py`-Cooldown-
Prüfung, `hebel_backward_tracking.py`-Überholt-Erkennung, `regime.py`-
Regime-Konflikt-Kennzahl, `hebel_analyst.py`-Wiederholungs-Erkennung) - alle
vier brauchen das VOLLSTÄNDIGE, toggle-unabhängige Ergebnis. Eine Filterung
an der geteilten Funktion hätte dort stillschweigend falsche Ergebnisse
erzeugt (z.B. Überholt-Erkennung für ein deaktiviertes Symbol funktionslos).

**Fix, ausschließlich in `ui/hebel_view.py::refresh()`:**
1. Neue Bulk-Funktion `database/db.py::get_hebel_pruefung_toggle_map()` -
   liest `asset_hebel_settings` einmalig komplett statt N Einzelabfragen.
2. Zeilen-Filter beim Aufbau der Haupt-Tabelle: ein Signal wird ausgeblendet,
   wenn (a) der Toggle für dieses Symbol aus ist UND (b) keine offene
   Position für genau dieses Symbol+Richtung existiert (offene Positionen
   bleiben aus demselben Grund wie beim `87f325b`-Fix immer verwaltbar).
3. Zusätzlich ein Anzeige-Switch ("2 Tage"/"Alle", `ttk.Radiobutton`-Paar im
   Toolbar) - blendet Signale älter als 2 Tage aus, ebenfalls mit Ausnahme
   offener Positionen (deren aktueller Stand soll unabhängig vom Signal-Alter
   sichtbar bleiben). Session-only, keine Persistenz (Nutzer-Vorgabe:
   "keine Speicherung notwendig"), Standardwert bei jedem App-Start "2 Tage".
4. Kritische Reihenfolge-Feinheit: die `covered`-Menge (verhindert doppelte
   "Kandidat wartet auf Analyse"-Platzhalter für bereits echte Signale) wird
   weiterhin aus der VOLLSTÄNDIGEN, ungefilterten `signals`-Menge gebaut, VOR
   dem Anzeigefilter - sonst hätte ein ausgeblendetes Signal seinen Platz
   fälschlich wieder für einen Kandidaten-Platzhalter freigegeben.

**Verifiziert:** synthetischer Test mit 5 Szenarien (aktiv+frisch, deaktiviert
ohne Position, deaktiviert MIT offener Position, aktiv aber 5 Tage alt ohne
Position, aktiv 5 Tage altes Signal MIT offener Position) gegen beide
Zeitfenster-Einstellungen - alle Kombinationen wie erwartet; echter
Tk-Smoke-Test (`HebelView()`-Erstellung, Standardwert "2_tage" bestätigt,
Umschalten auf "alle" + `refresh()` ohne Absturz); Import-Regressionscheck
für `database/db.py` + alle 4 anderen Verbraucher der geteilten Funktion
(unverändert, keine Regression).

## Nachtrag (2026-07-27): Z.ai-Richtungs-Erfolgsquote - unabhängig von Mistrals Übereinstimmung gemessen

**Auslöser:** Analyse eines frischen Notebook-Exports zeigte, dass Z.ais
unabhängige Richtungs-Ableitung (`zai_eigene_richtung`, Call 2) so gut wie nie
mit Mistrals Hebel-Empfehlung übereinstimmte (57 LONG/2 SHORT bei Mistral vs.
0 LONG/29 SHORT/28 NEUTRAL bei Z.ai). Der Nutzer stellte dazu die entscheidende
Rückfrage, ob Mistral wisse, "dass wir nur long können" - Prüfung von
`ui/settings.py`/`agent/krypto/budget_allocator.py` (Zeile ~383/388/435)
bestätigte: die per-Gerät persistierte Einstellung `hebel_richtung_modus`
(`data/settings.json`, NICHT im Git, getrennt vom statischen
`Basisinfos/config.yaml`-Wert `hebel.nur_long`) filtert SHORT-Kandidaten
bereits VOR jedem LLM-Call heraus, wenn auf `"nur_long"` gestellt - und der
Nutzer bestätigte, dass genau das auf dem Notebook (der produktiven 24/7-
Maschine) seit Einführung der Long/Short-Funktion (2026-07-15) der Fall ist,
weil "1. bitpanda kann noch immer kein short" (weiterhin gültige Einschränkung,
keine Änderung an `hebel_richtung_modus` geplant).

**KORREKTUR (2026-07-28, siehe Nachtrag weiter unten):** Diese Einschätzung war
UNVOLLSTÄNDIG - "57 LONG/2 SHORT bei Mistral" wurde damals als Beleg dafür
gewertet, dass der Kandidaten-Filter ausreicht, aber genau diese 2 SHORT-Fälle
waren vermutlich bereits die hier beschriebene Lücke: der Filter greift nur VOR
dem LLM-Call (auf `trigger.richtung`), das LLM entscheidet die tatsächliche
`richtung` seiner Antwort aber selbst und wird danach nicht mehr geprüft. Ein
echter Vorfall (NEAR/TAO SHORT ERÖFFNEN trotz aktivem `nur_long`) bestätigte
das am 2026-07-28 - siehe dortigen Nachtrag für den vollständigen Fix. Die
extreme LONG-Bias in den bisherigen Auswertungen ist also ein strukturelles Konfigurations-
Artefakt, keine organische Strategie - der reine "Z.ai stimmt mit Mistral
überein"-Vergleich (`zai_uebereinstimmung`, bestehend seit dem 2026-07-26er
Nachtrag) sagt unter dieser Einschränkung wenig darüber aus, ob Z.ais eigene
Richtungs-Einschätzung tatsächlich GUT ist. Nutzer-Auftrag: **"2. ja ZAI
unabhängig mit seinen unterschiedlichen Entscheidungen und deren Erfolgsquote
messen"** - eine zu `compute_provider_performance()`/`compute_win_rate_fact()`
analoge, aber von Mistrals Bias unabhängige Kennzahl.

### Kein neuer Kursabruf nötig - Wiederverwendung des bereits aufgelösten Outcomes

`check_signal_outcome()`/`check_hebel_signal_outcome()` lösen Take-Profit/
Stop-Loss bereits RICHTUNGS-KORREKT orientiert auf (LONG: TP oberhalb/SL
unterhalb des Entrys, SHORT: umgekehrt, siehe `hebel_backward_tracking.py`
Zeile ~146-206). Damit lässt sich die TATSÄCHLICHE Marktrichtung aus dem
bereits gespeicherten `outcome_status` ableiten, ohne selbst nochmal OHLC-
Daten zu lesen:

- `primaer_richtung`=LONG + `take_profit_erreicht` → Kurs stieg → Markt war LONG
- `primaer_richtung`=LONG + `stop_loss_erreicht`/`liquidation_wahrscheinlich` → Kurs fiel → Markt war SHORT
- `primaer_richtung`=SHORT + `take_profit_erreicht` → Kurs fiel → Markt war SHORT
- `primaer_richtung`=SHORT + `stop_loss_erreicht`/`liquidation_wahrscheinlich` → Kurs stieg → Markt war LONG

Neue reine Funktion `agent/krypto/gegenpruefung.py`-Nachbar
`agent/krypto/backward_tracking.py::bewerte_zai_richtung(primaer_richtung,
outcome_status, zai_eigene_richtung)` vergleicht `zai_eigene_richtung` gegen
diese abgeleitete tatsächliche Richtung - "treffer"/"fehlschlag", oder `None`
wenn kein Vergleich möglich ist (Z.ai NEUTRAL, oder `outcome_status` außerhalb
der aufgelösten Zustände).

### NEUTRAL-Behandlung - Nutzer-Entscheidung

Z.ai-NEUTRAL-Urteile fließen NICHT in die Trefferquote ein (weder als Treffer
noch als Fehlschlag), sondern werden separat als `neutral_bei_klarer_bewegung`
gezählt. Nutzer-Begründung, explizit erfragt und bestätigt: **"würde ich
neutral zählen eher nein - denn wir messen es auch nicht oder?"** - analog
dazu, dass Mistrals eigenes HALTEN/NEUTRAL ebenfalls nicht in
`compute_provider_performance()`/`compute_win_rate_fact()` einfließt.

### Scope - alle 6 Pipelines, mit einer bekannten Einschränkung bei Spot

Nutzer-Vorgabe: **"Scope sollte analog für alle Assets und Assetklassen
angewendet werden - jedenfalls spot"**, mit der Annahme "kaufen bevor es
steigt also long, verkaufen bevor es fällt also short" (bestätigt als
korrekte Grundannahme). Neue Aggregat-Funktion
`compute_zai_richtung_performance(conn, watchlist=None)` deckt beide Tabellen
ab:

- **Hebel** (`hebel_signals`): echtes `richtung`-Feld, volle Abdeckung -
  `check_hebel_signal_outcome()` löst BEIDE Richtungen korrekt auf.
- **Spot-family** (`signals`, Krypto-Spot/Aktien/Rohstoffe/Themen-ETF/Hedge):
  `primaer_richtung` wird über das bereits bestehende
  `agent/krypto/gegenpruefung.py::richtung_aus_action()` aus `action`
  abgeleitet (identische Ableitung wie für `zai_uebereinstimmung` bereits
  verwendet) - inklusive der Hedge-Invertierung (`ist_hedge_invertiert=True`
  für Symbole aus `agent.hedge.pipeline.SYMBOL_ZU_HEBEL_FAKTOR`: KAUFEN =
  Hedge aufbauen = bärische Gesamtmarkterwartung → SHORT-Erwartung an das
  Instrument selbst).

**Bekannte Lücke, transparent an den Nutzer kommuniziert statt stillschweigend
übergangen:** `backward_tracking.py::_TRACKABLE_ACTIONS = {"KAUFEN",
"NACHKAUFEN"}` - nur die KAUFEN-Seite der Spot-family wird von
`check_signal_outcome()` überhaupt outcome-aufgelöst, VERKAUFEN/TAUSCHEN
(die SHORT-Seite) liefern strukturell NIE `take_profit_erreicht`/
`stop_loss_erreicht` und tauchen deshalb in dieser Kennzahl praktisch nicht
auf, bis ein eigenes Sell-Side-Backward-Tracking existiert (nicht Teil dieser
Runde). Bei Hebel gilt diese Einschränkung NICHT.

### Anzeige + Export

- `remote/status.py`: neues Feld `zai_richtung_performance`
  (`_get_zai_richtung_performance()`, gleicher Lesezugriffs-Stil wie
  `_get_provider_performance()`).
- `remote/server.py`: neue Karte "Z.ai-Richtungs-Erfolgsquote (unabhängig von
  Mistral)" - Tiers Hebel + Spot-family nach Assetklasse (analog
  `SPOT_ASSETKLASSEN`), zeigt `n`, Trefferquote und NEUTRAL-Anzahl je Tier;
  leere Tiers bleiben sichtbar statt stillschweigend zu fehlen.
- `extract_notebook_diagnose.py`: `zai_richtung_performance`-Feld ergänzt
  (Aggregat mitschicken statt nur Rohspalten, gleiches Prinzip wie
  `provider_performance`/`konfidenz_kalibrierung`).

**Verifiziert:** 11 synthetische Fälle für `bewerte_zai_richtung()` (alle
LONG/SHORT × TP/SL/Liquidation-Kombinationen, NEUTRAL, `None`, nicht
aufgelöster Status) + 8 End-to-End-Fälle für `compute_zai_richtung_performance()`
gegen eine In-Memory-SQLite-DB (Hebel Treffer/Fehlschlag/NEUTRAL/fehlendes
Feld, Spot KAUFEN-Treffer, Spot HALTEN korrekt ausgeschlossen, Hedge-
Invertierung korrekt angewendet) - alle 19 Checks bestanden. Import-
Regressionscheck für alle 4 geänderten Module (`backward_tracking.py`,
`remote/status.py`, `remote/server.py`, `extract_notebook_diagnose.py`) ohne
Fehler.

**Bewusst NICHT Teil dieser Runde:** keine Änderung an `hebel_richtung_modus`
selbst (Bitpanda-Short-Einschränkung bleibt gültig); kein Sell-Side-Backward-
Tracking für VERKAUFEN/TAUSCHEN (siehe Lücke oben); keine GUI-Integration
außerhalb der Remote-Seite (gleiche Platzierung wie Provider-Performance/
Richtungstreffer-Quote, aus denen dieses Feature abgeleitet ist).

## Nachtrag (2026-07-27, noch später): Punkt 3 - Z.ai-Erfolgsquote auf Richtungstreffer/MFE statt binärem TP/SL-outcome_status umgestellt

**Auslöser:** direkt nach dem Push der obigen Version stellte der Nutzer vier
Anschlussfragen zum weiteren Optimierungsbedarf, von denen Punkt 3 die
gerade gebaute Metrik selbst betraf: **"wir haben als Erfolgsquote auch nicht
mehr die Take Profit Zone ausgereizt"** - zurecht, die erste Version nutzte
den binären `outcome_status` (nur `take_profit_erreicht`/`stop_loss_erreicht`/
`liquidation_wahrscheinlich`), ein Signal, das nie eine der beiden Zonen
erreicht (später überholt/abgelaufen), aber zwischenzeitlich klar in eine
Richtung lief, wurde komplett übersehen - exakt dasselbe Problem, das die
bestehende Richtungstreffer-Quote (`compute_richtungstreffer_quote()`,
2026-07-27 früher am selben Tag) bereits für Mistrals eigene Signale löst.

**Zusatzfrage des Nutzers, direkt beantwortet:** "ist das für Mistral Quote
und Richtung bereits korrekt für alle Assets oder nicht?" - Antwort nach
Code-Prüfung (`run_backward_tracking()` Zeile ~382: `SELECT id FROM signals
WHERE outcome_status IS NULL OR outcome_status = 'offen'` - KEIN Assetklassen-
oder Symbol-Filter):

1. **Datenberechnung**: JA, vollständig korrekt für alle 6 Pipelines.
   `check_signal_outcome()`/`check_hebel_signal_outcome()` laufen
   unverändert über die komplette geteilte `signals`/`hebel_signals`-Tabelle,
   unabhängig davon, welche Pipeline das Signal erzeugt hat - kein
   pipeline-spezifischer Sonderfall nötig, kein "vergessenes" Backfill.
2. **Richtungskorrektheit**: bei Hebel vollständig korrekt für BEIDE
   Richtungen (verifizierter Code, `ist_short`-Verzweigung sowohl in
   `resolve()` als auch `_erfasse_mfe()`). Bei der Spot-family gilt
   dieselbe Lücke wie beim binären Outcome: NUR KAUFEN/NACHKAUFEN
   (`_TRACKABLE_ACTIONS`) werden je MFE-getrackt, VERKAUFEN/TAUSCHEN nie -
   dieselbe, bereits dokumentierte Lücke, keine neue.
3. **Anzeige-Aufschlüsselung**: `compute_richtungstreffer_quote(conn, tier,
   ...)` bricht NICHT nach Assetklasse auf (anders als Provider-Performance/
   Konfidenz-Kalibrierung) - poolt aktuell "spot" über Krypto-Spot/Aktien/
   Rohstoffe/Themen-ETF/Hedge hinweg. Keine Korrektheitslücke, aber gröber
   als die anderen Karten - nicht Teil dieser Runde, da nicht explizit
   angefragt.

**Umsetzung:** `bewerte_zai_richtung()` (Signatur geändert: `outcome_status`
→ `max_realisiertes_crv: float | None` + `richtungstreffer_mindest_crv:
float`) nutzt jetzt `outcome_max_realisiertes_crv` (bereits relativ zu
`primaer_richtung` berechnet) statt des binären Status:
- `max_realisiertes_crv >= Schwelle` → Markt bestätigte `primaer_richtung`.
- `max_realisiertes_crv <= -Schwelle` → Markt lief klar in die Gegenrichtung.
- Dazwischen → neuer Rückgabewert `ZAI_URTEIL_KEINE_KLARE_BEWEGUNG` (Markt
  hat sich nicht entscheidend genug bewegt, unabhängig von Z.ais Antwort -
  bewusst NICHT dasselbe wie NEUTRAL).
- Z.ai=NEUTRAL (oder kein MFE-Wert vorhanden) → `ZAI_URTEIL_NEUTRAL`.

`compute_zai_richtung_performance()` bekommt einen neuen Parameter
`richtungstreffer_mindest_crv` (Default identisch zu `compute_richtungstreffer_
quote()`, config-Schlüssel `backward_tracking.richtungstreffer_mindest_crv`,
aktuell 1.0) - `remote/status.py::_get_zai_richtung_performance()` liest jetzt
dieselbe config-Schwelle wie `_get_richtungstreffer_quote()`, damit beide
Karten konsistent kalibriert sind. Rückgabe-Dict pro Tier jetzt mit vier statt
zwei Zählern: `treffer`/`fehlschlaege`/`neutral`/`keine_klare_marktbewegung` -
`anzahl_bewertet` (Basis der Trefferquote) zählt bewusst NUR treffer+
fehlschlaege, die anderen beiden würden sonst die Quote verwässern.

`remote/server.py`: Kartentext + Render-Funktion angepasst (zeigt jetzt
beide Nebenkategorien getrennt, z.B. "3x NEUTRAL, 2x keine klare
Marktbewegung, nicht mitgezählt").

**Verifiziert:** 14 synthetische Randfälle für `bewerte_zai_richtung()`
(Schwellenwert exakt getroffen/knapp verfehlt, beide Richtungen, NEUTRAL,
`None`, fehlender MFE-Wert, konfigurierbare Schwelle) + 8 End-to-End-Fälle
für `compute_zai_richtung_performance()` (inkl. Schwellenwert-Verschiebung
end-to-end getestet: dieselben Rohdaten ergeben bei Schwelle=2.0 andere
Buckets als bei Schwelle=1.0) + 2 Kontroll-Checks - alle 24 bestanden.
Import-Regressionscheck für alle 4 betroffenen Module ohne Fehler.

**Offen, vom Nutzer selbst als mehrtägiges Thema angekündigt** ("das Thema
wird uns noch einige Zeit und Tage beschäftigen"), NICHT Teil dieser Runde:
- Was folgt daraus, wenn Z.ai über längere Zeit signifikant besser liegt als
  Mistral (Aufwertung von "rein beobachtend" zu einer echten zweiten Stimme)?
- Zufalls-Trefferquote-Risiko: eine hohe SHORT-Trefferquote in einem
  anhaltenden Bär-Regime kann ohne Baseline-Vergleich (z.B. gegen "Regime-
  Richtung geraten") bedeutungslos sein - noch kein Baseline-Vergleich
  gebaut.
- Generelle Frage nach präziserer Kalibrierung beider Z.ai-Calls (Konsistenz-
  Check UND Richtungs-Abgleich).

## Nachtrag (2026-07-27, Abschluss der Sitzung): Sell-Side-Backward-Tracking - VERKAUFEN/TAUSCHEN jetzt vollständig trackbar (Mistral UND Z.ai)

**Auslöser:** direkter Nutzer-Auftrag, nachdem die Z.ai-Richtungs-Erfolgsquote
fertiggestellt war: **"bitte bei spot, etc. auch auf sinkende short Kurse -
also verkauf Tracken damit es vollständig ist für alle Assets - für ZAI und
Mistral - falls noch nicht angepasst."** Recherche ergab: VERKAUFEN/TAUSCHEN-
Signale bekamen zwar formal `entry`/`stop_loss`/`take_profit`-Zonen vom LLM,
aber OHNE erzwungene Richtung - Regel 3 (Stop-Loss/CRV-Pflicht) galt bisher
NUR für KAUFEN/NACHKAUFEN, Regel 16 (Zonen-Beispiele) war durchgehend
bullisch formuliert. Ohne Fix wären die Zonen bei VERKAUFEN strukturell
unzuverlässig orientiert gewesen - eine reine Python-Erweiterung von
`_TRACKABLE_ACTIONS` hätte mit Zonen gerechnet, die keine verlässliche
bearische Struktur hatten. Nutzer-Vorgabe zur Lösung, nach kurzer
Rückfrage bestätigt: **"verkaufen sprich short Richtung muss aus dem Trading
ebenfalls eine Zielzone haben welche dann umgekehrt funktioniert - also
mathematisch deterministisch wie für die kauf - long positionen wie wir sie
haben"** - identisches Muster wie bei Hebel-SHORT, nur auf Spot übertragen.

### Fünfteilige Umsetzung

1. **Regel 3 + Regel 16/13/12/11 (Zonen-Beispiel) gespiegelt** in
   `agent/krypto/analyst.py`, `agent/aktien/analyst.py`,
   `agent/rohstoff/analyst.py`, `agent/themen_etf/analyst.py` (4 Dateien,
   NICHT Hedge - siehe Punkt 5): bei VERKAUFEN/TAUSCHEN ist Stop-Loss jetzt
   ebenfalls PFLICHT, CRV MUSS mindestens 2.0 betragen, gespiegelt gerechnet:
   `(entry_mitte - take_profit.usd_bis) / (stop_loss.usd_bis - entry_mitte)`
   - Take-Profit-Zone muss vollständig UNTERHALB, Stop-Loss-Zone vollständig
   OBERHALB der Entry-Zone liegen.
2. **`agent/krypto/risk_gate.py::post_check()`**: neuer `_SELL_ACTIONS`-Block,
   identische Philosophie wie der bestehende `_BUY_ACTIONS`-CRV-Block, nur
   Zonen-Vorzeichen gedreht (konservativ: die jeweils NÄHERE Zonen-Grenze
   `_bis` statt `_von`). `crv is None` (z.B. Zonen falsch orientiert) fällt
   automatisch unter denselben Veto-auf-HALTEN-Zweig - keine separate
   Richtungsprüfung nötig, die Mathematik erzwingt sie implizit. Gilt für
   alle 4 Pipelines, die `post_check()` teilen (Aktien/Rohstoffe/Themen-ETF
   reuse identisch, siehe deren Pipeline-Docstrings).
3. **`agent/krypto/backward_tracking.py::check_signal_outcome()`** komplett
   überarbeitet: neue `ist_short`-Verzweigung (via
   `agent.krypto.gegenpruefung.richtung_aus_action()`, da `Signal` - anders
   als `HebelSignal` - kein natives `richtung`-Feld hat), spiegelt TP/SL-
   Treffer-Logik UND die MFE-Berechnung (`_erfasse_mfe()`) - direkter Mirror
   von `hebel_backward_tracking.py::check_hebel_signal_outcome()`s bereits
   bewährter SHORT-Logik. `_TRACKABLE_ACTIONS` um `VERKAUFEN`/`TAUSCHEN`
   erweitert (vorher nur `KAUFEN`/`NACHKAUFEN`). Hedge-Invertierung
   (`ist_hedge_invertiert`) ist hier NICHT relevant - die Zonen beschreiben
   immer die Kursbewegung des Instruments selbst, nicht die Gesamtmarkt-
   Interpretation (unabhängig von Punkt 5 unten).
4. **`agent/krypto/pipeline.py`**: `mindestziel_preis()`-Aufruf korrigiert -
   `ist_short` wird jetzt aus `richtung_aus_action()` abgeleitet, `risiko_
   distanz` entsprechend gespiegelt berechnet (vorher immer LONG-Annahme,
   hätte bei VERKAUFEN eine negative/falsche Distanz ergeben und `None`
   geliefert).
5. **Hedge bewusst AUSGENOMMEN**: `agent/hedge/analyst.py` hat laut eigener
   Regel 9 explizit KEINE CRV-Pflicht ("die Zonen sind informativer Kontext,
   keine harte Kauf-Voraussetzung") - das gilt unverändert für BEIDE
   Richtungen, kein neues Ungleichgewicht. `agent/hedge/pipeline.py` ruft
   `risk_gate.py::post_check()` ohnehin nicht auf (eigener Deterministik-
   Deckel). Hedge-VERKAUFEN-Signale werden trotzdem automatisch mitgetrackt,
   wenn ihre Zonen zufällig korrekt orientiert sind (`check_signal_outcome()`
   ist pipeline-agnostisch) - nur ohne die erzwungene Garantie.
6. **`database/models.py`**: Docstring von `outcome_max_realisiertes_crv`
   korrigiert (war "richtungsunabhängig für Spot immer 'steigend'" -
   inzwischen unwahr).

**Wichtige Konsequenz, die dem Nutzer bewusst ist:** die Formel oben verhält
sich bei VERKAUFEN GENAUSO streng wie bei KAUFEN - eine VERKAUFEN-Empfehlung
mit schlecht orientierten oder zu engen Zonen wird jetzt EBENFALLS auf
HALTEN korrigiert, auch wenn die zugrunde liegende fundamentale These (Regel
7: langfristige These gebrochen) berechtigt wäre. Das ist eine bewusste
Design-Entscheidung des Nutzers (mathematische Parität zu KAUFEN), keine
versehentliche Nebenwirkung - wird beobachtet, ob das in der Praxis zu
unerwünschten Vetos führt.

**Bekannte, unveränderte Lücke:** bereits bestehende VERKAUFEN/TAUSCHEN-
Signale in der Produktions-DB (vor diesem Fix erzeugt) profitieren NICHT
rückwirkend - ihre Zonen wurden ohne die neue Richtungs-Garantie erstellt und
könnten falsch orientiert sein. Nur Signale NACH diesem Fix sind verlässlich
trackbar.

**Verifiziert:** 15 synthetische Fälle (`check_signal_outcome()` LONG-
Regression, VERKAUFEN Take-Profit/Stop-Loss/MFE-ohne-Treffer, TAUSCHEN
identisch zu VERKAUFEN, HALTEN weiterhin nicht trackbar,
`mindestziel_preis(ist_short=True)` gespiegelt, `risk_gate.py::post_check()`
CRV-Veto für VERKAUFEN/TAUSCHEN bei gutem/schlechtem CRV) - alle bestanden.
Vollständiger Import-Regressionscheck über alle 4 geänderten Analyst-Dateien
+ `risk_gate.py` + `backward_tracking.py` + alle 5 Spot-family-Pipelines +
`scheduler/background.py` ohne Fehler.

**Automatischer Nebeneffekt, kein zusätzlicher Code nötig:** sowohl
`compute_provider_performance()`/`compute_win_rate_fact()`/
`compute_richtungstreffer_quote()` (Mistral) als auch
`compute_zai_richtung_performance()` (Z.ai, siehe vorheriger Nachtrag) lesen
bereits aus denselben `outcome_status`/`outcome_max_realisiertes_crv`-
Feldern - sobald neue VERKAUFEN/TAUSCHEN-Signale nach diesem Fix aufgelöst
werden, erscheinen sie automatisch in allen bestehenden Auswertungskarten,
ohne dass diese selbst angepasst werden mussten.

**Committet und gepusht** (`cf79071`).

## Nachtrag (2026-07-28): Fakten-Entscheidungsmappe + Hebel-Regel 22 (FOMC/CPI-Kontext)

Nutzer-Anstoß: bei der Detailanalyse eines frischen Notebook-Diagnose-Exports fiel
auf, dass Z.ais unabhängige Richtungseinschätzung bei Hebel-Signalen fast nie mit
dem Haupt-Signal übereinstimmt (75/76 Fällen "Abweichung"). Tiefere Analyse ergab:
kein Datenqualitätsproblem wie beim früheren Retail-Konsens-Fund, sondern ein
Mess-Artefakt - `hebel_richtung_modus="nur_long"` filtert SHORT-Kandidaten schon
vor jedem LLM-Call heraus (Bitpanda kann nicht shorten), daher ist die Haupt-
Richtung praktisch immer LONG, während Z.ais unabhängige Einschätzung im
anhaltenden Bär-Regime ehrlich SHORT/NEUTRAL liest. Der Vergleich misst also nicht
"liegt Z.ai falsch", sondern "stimmt eine strukturell auf LONG beschränkte
Empfehlung mit einer unvoreingenommenen Einschätzung überein" - in einem
Bärenmarkt naturgemäß selten.

Als Nebenbefund beim Faktencheck fiel auf: die Krypto-Fakten enthalten `markt_
kontext.naechste_fomc_sitzungen`/`naechste_cpi_veroeffentlichung`, aber der
Hebel-Prompt (`agent/krypto/hebel_analyst.py`) hatte dafür KEINE Regel (die
Spot-Regel 13 dagegen eine schwache 14-/5-Tage-Schwelle ohne Richtung/Magnitude).
Das führte zu einer breiteren, grundsätzlichen Diskussion: soll man Fakten
deterministisch vor-bewerten (dann: wozu die KI?) oder soll man sie roh ohne
jede Einordnung durchreichen (dann: unreproduzierbares, im schlimmsten Fall
zufälliges LLM-Verhalten)? Antwort: keins von beidem - Fakten, die echtes,
kontextabhängiges Abwägen brauchen, gehören dem LLM, aber mit einer
dokumentierten Marktbasis als Kontext, nicht mit einer vorgegebenen
Schlussfolgerung. Fakten, deren "richtige" Reaktion immer dieselbe ist, gehören
stattdessen hart ins Risk-Gate (unverändertes Prinzip, siehe CRV-Minimum/Cash-
Reserve/Konfidenz-Regime-Schwelle).

**Vollständige Bestandsaufnahme:** neues, dauerhaftes Referenzdokument
`Basisinfos/Fakten_Entscheidungsmappe.md` - alle 156 Fakten der Krypto-Spot- und
Hebel-Pipeline katalogisiert und in vier Kategorien eingeordnet (Regel+Gate /
nur Regel / nur Gate / weder noch - letztere ~28 Fakten sind der eigentliche
Handlungsraum). Zusätzlich neue vierte Prüf-Dimension "Zeithorizont-Passung"
(Nutzer-Vorgabe): Hebel = kurzfristige Taktik (~1 Tag Haltedauer), Spot =
langfristige Investitionsthese/Zyklus-Positionierung (sinngemäß "Bitcoin-
Sparplan": antizyklisch kaufen im Bärenmarkt, AZ-4-Bausteine). Ein Fakt ohne
Kontext ist in der Pipeline dringlicher, zu der er zeitlich passt - FOMC-Nähe
fehlte komplett dort, wo sie am relevantesten ist (Hebel), während die schwache
Spot-Regel für die Langfrist-These fast proportional richtig ist.

**Umgesetzt (Punkt 1 der Prioritätenliste):** neue Regel 22 in
`agent/krypto/hebel_analyst.py::SYSTEM_PROMPT` - liefert dokumentierten
Marktkontext (FOMC-Sitzungen/CPI-Veröffentlichungen zeigen in etablierten
Marktstudien typischerweise erhöhte realisierte Volatilität um den Termin,
oft nach einer ruhigeren Phase davor; für Krypto weniger belastbar untersucht;
KEINE Richtungsaussage ableitbar) statt einer vorgegebenen Schlussfolgerung -
das LLM gewichtet selbst, ob und wie stark das bei der konkreten Stop-Loss-
Distanz relevant ist, insbesondere fürs Liquidations-/Stop-Loss-Risiko einer
gehebelten Position. `praesidentschaftszyklus` wird explizit als für Hebel
kaum aussagekräftiger Hintergrund-Fakt eingeordnet (mehrjähriger Zyklus vs.
Stunden-/Tage-Haltedauer). Bewusst KEIN neues Gate/Deckel - passend zum
Grundsatz "Kontext liefern, Urteil nicht vorwegnehmen".

Vorherige Regel 22 ("eigene_einschaetzung") zu Regel 23 verschoben; dabei auch
3 bereits vorher veraltete "Regel 21"-Verweise im Code (Schema-Kommentar +
2 Docstrings) auf "Regel 23" korrigiert - waren schon vor dieser Änderung um
eins versetzt.

**Verifiziert:** Modul-Import, Compile-Check, durchgängige Regelnummerierung
1-23 ohne Lücke geprüft.

**Weitere, noch offene Punkte** (Priorisierung bestätigt, siehe
`Fakten_Entscheidungsmappe.md` Abschnitt 5+6): Fear&Greed-Index anbinden/
entfernen, `regime_profil.gewicht_*` anbinden/entfernen, Spot-Retail-Konsens-
Filter analog zu Hebel nachziehen, `historischer_makro_vergleich` bei Hebel
ggf. entfernen (Zeithorizont-Fehlpassung), plus drei "sofort machbare" neue
Fakten (DXY-Trend direkt in Krypto-Fakten, OI-Trend-vs-Kurs-Divergenz,
Funding-Rate-Perzentil) - alle mit bereits vorhandenen, kostenfreien Daten
umsetzbar, nur noch nicht verdrahtet.

**Ergaenzung noch am selben Tag:** drittes Referenzdokument
`Basisinfos/Test_und_Verifikationsmethodik.md` - Ausloeser war eine Nutzer-
Rueckfrage ("was meinst du mit umgesetzt?"), die aufdeckte, dass der Status
"erledigt" ohne feste Bedeutung missverstaendlich ist. Enthaelt ein 5-Stufen-
Statusvokabular (Geschrieben/Verifiziert/Committet/Deployed/Im Betrieb
bestaetigt - ab jetzt IMMER die konkrete Stufe nennen statt "erledigt"), 4
Aenderungsklassen mit Mindest-Testtiefe fuer synthetische Tests, sowie einen
festen 8-Punkte-Kennzahlenkatalog fuer Notebook-Export-Analysen inkl.
Vorher-Hypothese-Prinzip (vor jeder Verhaltensbeobachtung im Betrieb
festhalten, was erwartet wird, statt die Beobachtung nachtraeglich passend
zu interpretieren).

**Committet und gepusht** (`7eac0ec`) - Stufe 3 des in diesem Nachtrag selbst
eingefuehrten Statusvokabulars.

**Ergaenzung (2026-07-28, Punkt 2 der Prioritaetenliste): Fear&Greed-Index.**
`regime.fear_greed.wert`/`einstufung` war ein komplett toter Fakt (an
`build_facts()` geliefert, aber ohne Prompt-Regel bei Spot, ganz ohne
Fakt-Uebergabe bei Hebel). Neue Regel 29 in `agent/krypto/analyst.py::
SYSTEM_PROMPT` (vorherige Regel 29 "eigene_einschaetzung" zu Regel 30
verschoben, 3 Kreuzverweise korrigiert). Nutzer-Praezisierung machte die Regel
bewusst ASYMMETRISCH statt eines einfachen Kontraindikators: im Baerenmarkt
sind Angstphasen langanhaltend und alleine kein verlaesslicher Bodenindikator
(Bodenbildung braucht zusaetzliche Bestaetigung, z.B. niedriges
`zyklus_risiko`), waehrend Gier-Extreme historisch kuerzer und als
Warnsignal fuer lokale Uebertreibung brauchbarer sind - darf staerker
gewichtet werden, vor allem kombiniert mit hohem `zyklus_risiko`. Passt zum
Grundsatz "Kontext liefern, Urteil nicht vorwegnehmen" und zur
Zeithorizont-Frage (Spot = langfristige Zyklus-These).

**Bewusst NUR Spot, nicht Hebel (verworfene Variante B):** eine analoge
Hebel-Regel wurde geprueft und explizit NICHT umgesetzt (Muster siehe
[[feedback_document_rejected_options]]) - die fuer Fear&Greed relevante
Unterscheidung Baerenmarkt-Angstphase-vs-Hype-Phase ist eine
mehrwoechige/mehrmonatige Marktstruktur-Frage, unpassend fuer die typische
Hebel-Haltedauer von Stunden bis wenigen Tagen (Zeithorizont-Fehlpassung,
identisches Muster wie beim `historischer_makro_vergleich`-Befund, siehe
Punkt 5 der Prioritaetenliste). Nutzer-Einschaetzung: "hier ist weniger
mehr". Revisit-Bedingung: nur falls ein Backtest gegen echte
`hebel_signals`-Outcomes einen eigenstaendigen Tages-Signalwert belegt -
dann eigener neuer Fakt, keine Kopie von Regel 29. Vollstaendig dokumentiert
in `Fakten_Entscheidungsmappe.md` Abschnitt 5, Punkt 2.

**Token-Budget-Pruefung (Nutzer-Vorgabe, ab jetzt Standard fuer jede
Regeländerung):** Regel 29 ist mit ca. 150 Token ein vernachlaessigbarer
Zuwachs. Wichtiger: waehrend dieser Pruefung stellte sich heraus, dass eine
in dieser Sitzung zunaechst herangezogene Sorge - Z.ais 8K-Kontext-Drosselung
koennte durch SYSTEM_PROMPT-Wachstum verschaerft werden - auf einer
veralteten Memory-Notiz beruhte (Stand 2026-07-20, 4-stufige Kette
Mistral->Groq->Gemini->Z.ai). Nutzer-Korrektur: "ZAI ist kein fallback mehr
hat andere anwendung gefunden". Code-Verifikation (`agent/krypto/
budget_allocator.py`-Docstring + `grep` nach `_client is not None`)
bestaetigt: die tatsaechliche Haupt-Fallback-Kette fuer Signal-Generierung
ist seit dem Gegenpruefungs-Umbau (2026-07-26) nur noch **Mistral -> Gemini**
(kein Groq, kein Z.ai mehr). Z.ai laeuft seitdem ausschliesslich als
separate Gegenpruefung mit eigenem schlanken Fakten-Satz und sieht den
Haupt-SYSTEM_PROMPT nie - die urspruengliche Sorge war damit gegenstandslos,
aus dem richtigen aktuellen Grund. `reference_llm_provider_recherche_
uebersicht.md` entsprechend korrigiert (alte 4-stufige Kette als
"historischer Stand" markiert, neue Kette + Einordnung fuer
Prompt-Laengen-Diskussionen ergaenzt).

**Verifiziert:** Modul-Import, Compile-Check, durchgaengige Regelnummerierung
1-30 ohne Luecke geprueft (Klasse 1).

**Ergaenzung (2026-07-28, Punkt 3 der Prioritaetenliste): regime_profil.
gewicht_*.** `regime_profil.gewicht_technik`/`gewicht_fundamental`/
`gewicht_momentum`/`gewicht_kontext_makro` war in BEIDEN Pipelines (Spot +
Hebel) ein toter Fakt - das komplette `regime_profile`-Dict wird via
`build_facts()`/`build_hebel_facts()` an die LLM geliefert, aber keine
Prompt-Regel referenzierte es (im Unterschied zu `min_konfidenz_prozent`/
`small_cap_budget_prozent` aus demselben Profil, die bereits deterministisch
im Gate bzw. Scoring genutzt werden, siehe `agent/krypto/hebel_screening.py`/
`marktscan.py`). Inhaltlich kein Nebensaechlichkeits-Fakt, sondern ein
durchdachtes, regimeabhaengiges Gewichtungsschema aus `Basisinfos/config.yaml`
(`regime.profile`) - z.B. `krise_extrem`: Technik 0.15/Fundamental 0.45/
Momentum 0.15/Makro 0.25; `bulle`: Technik 0.43/Fundamental 0.25/Momentum
0.17/Makro 0.15.

Neue Regel 30 in `agent/krypto/analyst.py` (`eigene_einschaetzung` zu Regel
31 verschoben) und neue Regel 23 in `agent/krypto/hebel_analyst.py`
(`eigene_einschaetzung` zu Regel 24 verschoben, je 3 Kreuzverweise korrigiert):
nutzt das Gewichtungsschema als ORIENTIERUNG dafuer, wie stark die KI
technische/fundamentale/Momentum-/Makro-Aspekte in `long_reasoning`/
`top_gruende` gewichtet - ausdruecklich KEINE starre Formel oder Pflichtquote,
die eigene Einschaetzung der konkreten Fakten bleibt massgeblich. Passt zum
Grundsatz "Kontext liefern, Urteil nicht vorwegnehmen".

**Bewusst fuer BEIDE Pipelines** (anders als Fear&Greed, Punkt 2): die Frage
"welche Analyse-Linse ist in diesem Regime verlaesslicher" gilt nicht nur
langfristig - die Regime-Klassifikation selbst wird bei Hebel bereits
intensiv genutzt (Regime-Konflikt-Deckel, Regime-Persistenz), die
Zeithorizont-Frage spricht hier also nicht gegen eine gemeinsame Regel.

**Verifiziert:** Modul-Import + Compile-Check beider Dateien, durchgaengige
Regelnummerierung Spot 1-31 / Hebel 1-24 ohne Luecke geprueft (Klasse 1).
Token-Budget-Check: ca. 150 Token je Datei, vernachlaessigbar.

**Ergaenzung (2026-07-28, Punkt 4 der Prioritaetenliste): Spot-Retail-
Konsens-Filter.** Bei Hebel gibt es zwei getrennte Mechanismen, die beide
"Retail-Konsens" heissen: `retail_konsens_risiko()` (richtungsabhaengige
Deckel-Formel fuer den erlaubten Hebel) und `filtere_retail_konsens_
top_gruende()` (reiner Text-Filter, entfernt jeden `top_gruende`-Eintrag,
der sich auf Retail-Konten-Positionierung beruft, unabhaengig von der
Richtung). Nur Letzteres ist fuer Spot relevant (kein Hebel-Konzept bei
Spot) - Spot hat aber bereits denselben zugrunde liegenden Fakt
(`retail_long_bias_extrem`/`long_konten_anteil_prozent`) und dieselbe
Prompt-Warnung (Regel 15), nur ohne deterministische Rueckversicherung.

**Bewusst dupliziert statt importiert** (Nutzer-Einschaetzung: Spot/Hebel
koennten hier eher auseinanderlaufen als gleich bleiben - abweichend vom
sonst ueblichen "einzige Quelle der Wahrheit"-Muster wie bei `CRV_MINIMUM`):
`risk_gate.py` bekommt eine eigene Kopie von `_RETAIL_KONSENS_TOP_GRUND_
MUSTER`/`filtere_retail_konsens_top_gruende()`, mit Kreuzverweis-Kommentar
zum Hebel-Pendant in `hebel_risk_gate.py`.

**Anwendungsort:** neuer Parameter `filter_retail_konsens_top_gruende`
(Default `False`) in `risk_gate.py::post_check()` - nur `agent/krypto/
pipeline.py` (Krypto-Spot) setzt `True`. NICHT generisch fuer alle 4
Spot-family-Pipelines aktiv: Aktien hat mit `short_interest_finra` ein
aehnlich klingendes, aber fachlich anderes Konzept (institutionelle
FINRA-Meldungen, kein Retail-Konsens) - per synthetischem Test empirisch
bestaetigt, dass der Regex bei FINRA-Short-Interest-Formulierungen NICHT
anschlaegt, trotzdem bewusst nur am Krypto-Spot-Aufruf aktiviert statt
generisch in `post_check()`.

**Verifiziert:** Klasse 2, 4 Testfaelle - T1 Hebel-Regression (Verhalten
unveraendert), T2 Spot-Positivfall (identisches Verhalten zu Hebel), T3
Grenzfaelle (kein list, leere Liste, fehlendes `text`-Feld, `None`-Eintrag),
T4 Kombinationsfall (Retail-/Long-Short-Ratio-Varianten gefiltert,
FINRA-Short-Interest/Short-Squeeze-Text bleibt erhalten). Regressionscheck:
Import aller 5 Spot-family-Pipeline-Module OK.

**Ergaenzung (2026-07-28, Punkt 5 der Prioritaetenliste): historischer_
makro_vergleich bei Hebel.** Anders als Fear&Greed/`regime_profil` war das
KEIN toter Fakt ohne Kontext - Hebel-Regel 15 hatte bereits eine auffaellig
starke Warnung ("NIEMALS als belastbare Statistik... insbesondere fuer
Hebel-Positionen"). Die eigentliche Frage: lohnt sich der Fakt trotz starker
Warnung noch, angesichts der 6-/12-Monats-Vorwaertsrenditen (`top_analoge`,
`spx_forward_*`/`btc_forward_*`), die strukturell ein Mehrmonats-Konzept
sind - ein Kategorie-Problem, das selbst starke Prompt-Warnungen nicht
zuverlaessig loesen (dasselbe Muster wie beim Retail-Konsens-Fund).

**Loesung (Nutzer-Vorschlag, verfeinert): destillieren statt entfernen.**
Die aktuelle Makro-Konstellation (`aktuelle_konstellation`) ist zeitlos
gueltig, kein Mehrmonats-Konzept, bleibt erhalten. Neue Funktion
`agent/krypto/makro_analog.py::distill_makro_vergleich_fuer_hebel()`
reduziert auf `aktuelle_konstellation` + `anzahl_analoge` +
`spx_median_forward_6m_prozent` (12-Monats-Wert bewusst weggelassen;
`top_analoge`-Liste entfaellt komplett - groesster Umfang UND groesste
Fehlinterpretationsgefahr; kein aggregiertes BTC-Feld, unveraendert).
Gleicher Fakt-Schluesselname `historischer_makro_vergleich` fuer Spot UND
Hebel beibehalten (Fakt wird nirgends dauerhaft gespeichert, beide
Fassungen werden nie gemeinsam vom selben Code gelesen) - Kreuzverweis-
Kommentar an der Hebel-Aufrufstelle (`hebel_pipeline.py`) fuer menschliche
Lesbarkeit.

Hebel-Regel 15 komplett neu gefasst: die verbleibende Kennzahl wird
ausdruecklich als RICHTUNGSNEUTRALER Risikoappetit-Hintergrund fuer
`key_risks`/`gegenargument` gerahmt - bewusst KEINE LONG/SHORT-Ableitung
und KEINE Kategorie-Bucket-Uebersetzung (beides Scheingenauigkeit), rohe
Zahl mit klarer Einordnung, konsistent mit `zyklus_risiko`/`atr.perzentil`.

**Verifiziert:** Klasse 2, 4 Testfaelle - T1 `None`-Input, T2 Positivfall
(Destillation entfernt `top_analoge`/`aktueller_monat`/12-Monats-Wert
korrekt), T3 Grenzfall (fehlende/`None`-Werte), T4 Kombinationsfall
(Import-Konsistenz `hebel_pipeline.py`<->`makro_analog.py`). Regressionscheck:
Spot unveraendert, Regelnummerierung Hebel 1-24 ohne Luecke.

---

## Nachtrag (2026-07-28): HOTFIX - Z.ai-429-Sturm behoben (`api/zai.py`)

**Ausloeser:** Nutzer-Meldung "alle Z.ai-Infos sind aus den E-Mails gefallen, Hebel
UND Spot". Live-Test des Z.ai-API-Keys war unauffaellig (funktionierte einwandfrei),
die DB (`zai_gegenpruefung_verlauf` im Notebook-Export) zeigte sogar durchgaengig
frische Eintraege bis kurz vor Exportzeitpunkt - der Fehler lag also nicht am Key
oder an Z.ai selbst, sondern irgendwo im Zusammenspiel.

**Root Cause (im Log-Auszug des Notebook-Exports eindeutig nachgewiesen):**
210 Z.ai-bezogene Log-Zeilen in einem Zeitfenster, praktisch ausschliesslich
`"429 Client Error: Too Many Requests"`. `api/zai.py` dokumentiert selbst ein von
Z.ai vorgegebenes Concurrency-Limit von 2 fuer GLM-4.5-Flash - der Client hatte
aber bewusst KEINE eigene Drosselung (Nutzer-Entscheidung 2026-07-20, kalibriert
fuer Hebel-only-Volumen, also niedrige Last). Seit der Ausweitung der
Z.ai-Gegenpruefung auf alle 6 Signal-Pipelines (Commit `17b1c9b`, 2026-07-27 - je
2 sequenzielle Calls pro Signal, ueber mehrere gleichzeitig laufende Batches)
wurde das Concurrency-Limit chronisch ueberschritten - Calls scheiterten schlicht,
statt nur langsamer zu sein (auch der schon vorhandene 60s-Wartemechanismus vor
dem Hebel-E-Mail-Versand konnte das nicht kompensieren, wenn der Call selbst nie
durchkam).

**Fix (`api/zai.py`, `ZaiClient`):**
1. **Echtes Concurrency-Gate:** `threading.Semaphore(MAX_CONCURRENT_REQUESTS=2)`
   als Instanzattribut - `chat()` wartet jetzt auf einen freien Slot, statt sofort
   zu feuern und ggf. per 429 abgewiesen zu werden. Da `main.py` genau EINE
   `ZaiClient`-Instanz erstellt und an alle 6 Pipelines durchreicht, wirkt das
   Semaphore global ueber alle gleichzeitig laufenden Hintergrund-Threads.
2. **429-Retry:** bis zu `RETRY_ON_429_MAX_VERSUCHE=2` zusaetzliche Versuche mit
   steigender Wartezeit (`RETRY_ON_429_BASIS_WARTEZEIT_SEKUNDEN=5.0` je Versuch),
   respektiert einen `Retry-After`-Header falls vorhanden. Andere Fehler (Timeout,
   5xx, Verbindungsfehler) werden NICHT wiederholt - bleibt P-8 (kein Hard-Fail,
   Aufrufer faengt die Exception weiterhin ab).
3. `RATE_LIMIT_PER_MINUTE` (Gesamtvolumen/Minute) bleibt unveraendert bestehen -
   andere Achse (Durchsatz vs. Gleichzeitigkeit), beide Mechanismen ergaenzen sich.

**Verifiziert (Klasse 2, 6 Testfaelle, alle mit gemocktem `_session.post`):**
T1 Concurrency-Gate (6 parallele Threads, max. gleichzeitig aktive Calls <= 2),
T2 429-Retry (429 dann 200 - Erfolg nach 1 Wiederholung), T3 `Retry-After`-Header
wird respektiert, T4 Nicht-429-Fehler (500) wird NICHT wiederholt (1 Aufruf,
sofortige Exception), T5 Regressionsfall (sofortiger 200-Erfolg, kein Retry-Sleep),
T6 Retries ausgeschoepft (3 Versuche gesamt, dann Exception). Regressionscheck:
`main.py`-Import weiterhin unveraendert funktionsfaehig.

---

## Nachtrag (2026-07-28): Krypto-Spot-Luecke im Z.ai-E-Mail-Versand geschlossen (`scheduler/background.py`)

**Ausloeser:** Nutzer-Nachfrage nach dem 429-Hotfix oben: "hast du das fuer alle
ZAI und eMail benachrichtigung beruecksichtigt?" - Rundum-Pruefung aller Z.ai-
Aufrufstellen und E-Mail-Pfade ergab eine ZWEITE, vom Concurrency-Fix unabhaengige
Luecke.

**Root Cause:** `generate_hebel_signal()`/`generate_signal()` geben das Signal-
Objekt zurueck, BEVOR der Z.ai-Hintergrund-Thread ueberhaupt fertig ist (siehe
`api/zai.py`-Docstring). Fuer Hebel existierte deshalb bereits seit 2026-07-26 ein
Wartemechanismus (`_sende_hebel_email_mit_zai_wartezeit()`, begrenztes Polling bis
zu `_ZAI_EMAIL_WARTE_MAX_SEKUNDEN`), fuer Multi-Asset-Batch (Aktien/Rohstoffe/
Themen-ETF/Hedge) ein guenstiger Re-Fetch-by-ID direkt vor dem Versand (Commit 10
der Z.ai-6-Pipelines-Ausweitung). **Krypto-Spot hatte WEDER von beidem** -
`_on_signal_ready()` rief `_notify_spot_signal()` in ihrem `"spot:"`-Zweig direkt
mit dem In-Memory-Objekt auf, dessen Z.ai-Felder strukturell nie gesetzt sein
konnten. Ein reiner Re-Fetch (wie bei Multi-Asset) haette hier NICHT geholfen, da
Krypto-Spot pro Signal sofort benachrichtigt (E-Mail-Latenz-Fix), nicht erst am
Ende eines mehrstuendigen Batches wie Multi-Asset - es brauchte echtes Warten wie
bei Hebel.

**Fix:** die bisher Hebel-spezifische `_sende_hebel_email_mit_zai_wartezeit()`
wurde zu einer generischen, parametrisierten Funktion
`_sende_signal_email_mit_zai_wartezeit(ergebnis, watchlist, bitpanda_assets,
conn_factory, required_actions, get_signal_by_id_fn, notify_fn)` verallgemeinert
(die Wartemechanik selbst ist asset-neutral - anders als z.B. der Retail-Konsens-
Filter, der bewusst je Assetklasse dupliziert bleibt, weil dort inhaltliche
Unterschiede bestehen). Zwei duenne Wrapper `_sende_hebel_email_mit_zai_
wartezeit()` (unveraendertes Verhalten, reiner Regressions-Checkpoint) und neu
`_sende_spot_email_mit_zai_wartezeit()` rufen die generische Funktion mit ihren
jeweiligen `REQUIRED_*_ACTIONS`/`get_*_signal_by_id`/`_notify_*_signal` auf.
`_on_signal_ready()`s `"spot:"`-Zweig spawnt jetzt analog zum `"hebel:"`-Zweig
einen eigenen Hintergrund-Thread mit Wartezeit (nur wenn `zai_client is not None`,
sonst unveraendert direkter Aufruf).

**Selbst gefundener und selbst gefixter Regressions-Bug beim Verallgemeinern:**
die urspruengliche Fruehausstiegs-Pruefung fuer HALTEN/nicht-relevante Aktionen war
in der Hebel-Fassung ein blanker `return` VOR jedem `notify_fn`-Aufruf (sicher fuer
Hebel, da `_notify_hebel_signal()` denselben HALTEN-Guard ohnehin selbst hat).
Fuer Spot waere das ein echter Fehler gewesen: `_notify_spot_signal()` prueft
`cash_veto` UNABHAENGIG von der Aktion (auch bei HALTEN) - ein blanker Return
haette die Cash-Veto-Warnmail fuer Spot-HALTEN-Signale mit `cash_veto=True`
verschluckt. Gefixt, indem der Fruehausstieg `notify_fn` weiterhin aufruft (nur
OHNE Wartezeit) statt komplett zu returnen.

**Rundum-Pruefung sonst ergebnislos (bewusst dokumentiert, damit klar ist, was
geprueft wurde):** `agent/krypto/gegenpruefung.py`s zwei Z.ai-Aufrufstellen
(`leite_eigene_richtung()`, `pruefe_konsistenz()`) haben keine eigene Retry-Logik
(einfaches try/except-return-None, P-8) - kein Konflikt mit dem neuen Retry im
Client. Die manuellen "Signal berechnen"-Buttons (`ui/signals_view.py::
_run_pipeline()`, `ui/hebel_view.py::_run_analysis()`) loesen ueberhaupt keine
E-Mail aus (nur GUI-Update) - koennen die Fixes also nicht umgehen.

**Verifiziert (Klasse 2, 7 Testfaelle, gemockte `time.sleep`/Signal-Objekte):**
T1 HALTEN (sofortiger `notify_fn`-Aufruf, kein Sleep), T2 Positivfall (Loop endet
nach 1 Poll, sobald Z.ai-Urteil vorliegt, `notify_fn` bekommt das frische Signal),
T3 `conn_factory=None` (kein Wartezeit-Pfad, Original-Signal durchgereicht), T4
Zeitlimit erreicht (volle 20 Polls, `notify_fn` trotzdem aufgerufen), T5 (KRITISCH)
Spot-HALTEN mit `cash_veto=True` - `notify_fn` wird trotzdem aufgerufen, Cash-Veto-
Warnung bleibt erhalten, T6/T7 Delegations-Regressionstests fuer beide duennen
Wrapper. Regressionscheck: `main.py`/`scheduler/background.py`/`agent/krypto/
gegenpruefung.py`-Import weiterhin unveraendert funktionsfaehig.

---

## Nachtrag (2026-07-28): DXY-Trend (Dollar-Index) fuer alle 6 Pipelines verdrahtet

**Kontext:** Abschnitt 6 Punkt 1 der Fakten-Entscheidungsmappe. `api/macro.py::
get_dollar_index_trend()` existierte bereits (2026-07-20, fuer `agent/kategorie_
thesen.py`), war aber nie an die 6 Signal-Pipelines angebunden - nur indirekt und
stark verzoegert ueber den monatlichen Makro-Analog-Cache. Nutzer bestaetigt:
keine Gegenargumente gegen Gleichbehandlung aller 6 Pipelines (analog zum
VIX-Vorbild).

**Datenschicht (bereits vorhanden aus Vorlaeufer-Session):**
`RegimeResult.dollar_index_wert`/`dollar_index_trend` (Trend bereits
vorklassifiziert: "steigend"/"fallend"/"gleichbleibend"/"unbekannt",
`DOLLAR_INDEX_TREND_THRESHOLD_PCT = 1.5`), gecacht ueber `MacroSnapshot`
(1x/Tag, analog VIX), fliesst ueber `compute_current_regime()` (gemeinsame
Funktion aller 6 Pipelines) automatisch durch.

**Fakt-Wiring (diese Runde):** `regime.dollar_index.wert`/`.trend` in
`build_facts()`/`build_hebel_facts()` aller 6 Analyst-Dateien ergaenzt (`agent/
krypto/analyst.py`, `agent/krypto/hebel_analyst.py`, `agent/aktien/analyst.py`,
`agent/rohstoff/analyst.py`, `agent/themen_etf/analyst.py`, `agent/hedge/
analyst.py`). In den 5 Spot-family-Pipelines als Ergaenzung an die bestehende
VIX-Regel angehaengt (identisches Makro-Kontext-Muster: "steigender" DXY
korreliert historisch tendenziell negativ mit Krypto/hoeher-Beta-Assets,
direkter preisbelastend bei USD-denominierten Rohstoffen, belastend fuer
Auslandsumsaetze bei Aktien) - bewusst MINIMALER Zusatz-Tokenaufwand (ein
Satz je Datei), kein eigener Regel-Absatz, da inhaltlich eng verwandt mit VIX.
Hebel hat KEIN VIX-Aequivalent im Fakten-Dict - dort neue eigenstaendige Regel
24 (vor dem abschliessenden `eigene_einschaetzung`-Rueckblick, der auf 25
verschoben wurde).

**Verifiziert (Klasse 1):** `python -m py_compile` + Import-Regressionscheck
fuer alle 6 Analyst- + 6 Pipeline-Module, Regelnummerierung 1..N luecken-/
duplikatfrei in 5 von 6 Dateien prognostiziert und bestaetigt (Ausnahme:
`agent/rohstoff/analyst.py` hat einen VORBESTEHENDEN, von dieser Aenderung
unabhaengigen Nummerierungs-Doppler bei Regel 18/19 - separat als Task
geflaggt, nicht Teil dieser Aenderung). Synthetischer Test: `RegimeResult` mit
gesetzten `dollar_index_wert`/`_trend`-Werten instanziierbar. Reines,
risikoarmes Fakten-Wiring nach bereits produktiv laufendem VIX-Muster, keine
neue Berechnungslogik - kein hoeherer Testklassen-Aufwand noetig.

---

## Nachtrag (2026-07-28): OI-Squeeze-Divergenz + Funding-Rate-Perzentil (Krypto Spot+Hebel)

**Kontext:** Abschnitt 6 Punkt 2+3 der Fakten-Entscheidungsmappe. Vor der
Umsetzung Mengenanalyse gegen die echte Desktop-DB durchgefuehrt (Nutzer-
Vorgabe: "erst eine Mengenanalyse, dann entscheiden"), da unklar war, ob die
Doku-Behauptung "Daten bereits vorhanden" auch fuer Krypto-Spot gilt (die
zugrundeliegende `open_interest_snapshot`-Tabelle wird technisch nur ueber
den Hebel-Screening-Job befuellt).

**Mengenanalyse-Fund:** `asset_hebel_settings` (Hebel-Pruefung-Toggle) ist ein
reiner OPT-OUT - Default `True` fuer ALLE Krypto-Assets (`database/db.py::
get_hebel_pruefung_erlaubt()`), Tabelle war zum Pruefzeitpunkt komplett leer.
Von 43 Krypto-Watchlist-Assets hatten bereits 38 (88%) historische OI-/
Funding-Daten. Ergebnis: beide Fakten von Anfang an fuer Spot UND Hebel bauen,
keine Zeitreihen-Infrastruktur fehlt real.

**OI-Squeeze-Divergenz:** neue reine Funktion `classify_squeeze_divergenz()`
(`agent/krypto/hebel_screening.py`) - vergleicht Open-Interest-Aenderung
(`compute_oi_change_pct()`, NEUES eigenes Lookback-Fenster `config.yaml
krypto_oi_fakten.squeeze_oi_lookback_stunden=72`, bewusst NICHT Hebels
bestehendes 4h-Trendfolge-Fenster - zeitlich nicht vergleichbar mit einem
mehrtaegigen Kursfenster) mit der Kursaenderung (bereits vorhandenes
`antizyklisch.kursaenderung_letzte_tage_prozent`, 3-Tage-Fenster aus
`anticyclic.py`). Vier Label: `aufbau_bestaetigt` (beide gleiche Richtung -
frisches Kapital, robuster), `short_squeeze_verdacht`/`long_squeeze_verdacht`
(gegenlaeufig - Zwangs-Ein-/Eindeckung, fragiler), `abbau_deleveraging`
(beide fallend, normale Korrektur), plus `neutral` bei zu kleinen Aenderungen
(`squeeze_schwelle_prozent=1.0`, [OFFEN] Platzhalter ohne Live-Kalibrierung).

**Funding-Rate-Perzentil:** neue Funktion `funding_rate_percentile()`
(`indicators/calculations.py`) exakt nach dem `atr_percentile()`-Muster
(eigene `MIN_FUNDING_PERZENTIL_PUNKTE=30`-Konstante, bewusst NICHT dieselbe
Funktion wiederverwendet, um deren ATR-spezifischen Docstring nicht zu
verwaessern - reine 3-Zeilen-Logik). DB-Fetch-Wrapper
`hebel_screening.py::compute_funding_rate_percentile()` liest die Kraken-
Funding-Rate aus (redundant in allen 3 Boersen-Zeilen von
`open_interest_snapshot` gespeichert, EINE Boerse als Quelle reicht), filtert
None-Luecken.

**Wiring:** beide Fakten in `agent/krypto/pipeline.py`/`hebel_pipeline.py`
berechnet, als `antizyklisch.squeeze_divergenz`/`.funding_rate_perzentil` in
`analyst.py`/`hebel_analyst.py` verdrahtet (neue Regel 31 Spot, Regel 25
Hebel - Funding-Rate-Perzentil bewusst als ANDERES Signal zur absoluten
Funding-Kosten-Hoehe gerahmt, keine Duplizierung in `key_risks`).

**Verifiziert (Klasse 2, 16 synthetische Testfaelle):** T1-T4 alle 4 Squeeze-
Quadranten, T5-T6 neutral bei zu kleiner OI-/Kursaenderung, T7-T9 None-
Propagierung, T10 Grenzfall (exakte Schwelle zaehlt nicht als neutral), T11
unavailable bei zu wenig Punkten, T12-T13 Perzentil bei Maximal-/Minimalwert
(identische Formel wie `atr_percentile()`: `(werte < aktuell).sum()/len*100`,
Grenzwert selbst zaehlt nicht mit), T14 Grenzfall genau Mindestpunkte, T15-T16
DB-Wrapper mit None-Filterung. Regelnummerierung + Import-Regressionscheck
ueber alle 6 betroffenen Module (`pipeline.py`, `hebel_pipeline.py`,
`analyst.py`, `hebel_analyst.py`, `hebel_screening.py`,
`indicators/calculations.py`) sowie `main.py`.

## Nachtrag (2026-07-28): Nur-Long-Deckel — echter Bug, keine reine Konfigurationsfrage (NEAR/TAO SHORT ERÖFFNEN trotz aktivem `nur_long`)

**Auslöser:** Nutzer meldete zwei tatsächlich verschickte E-Mails -
"Hebel ERÖFFNEN NEAR (SHORT)" (28.07. 08:46 Uhr) und "Hebel ERÖFFNEN TAO
(SHORT)" (28.07. 11:50 Uhr) - obwohl der "Nur Long"-Schalter (`ui/settings.py::
hebel_richtung_modus`) auf dem Notebook durchgehend aktiv war. Log-Beweis
direkt aus dem 72h-Fenster des Notebook-Exports:

```
08:44:46 Budget-Allocator: Hebel 2/2 (Richtung=nur_long, ...)
08:46:28 E-Mail gesendet: "Hebel ERÖFFNEN NEAR (SHORT)"
11:47:39 Budget-Allocator: Hebel 3/3 (Richtung=nur_long, ...)
11:50    E-Mail gesendet: "Hebel ERÖFFNEN TAO (SHORT)"
```

Der Kandidaten-Filter lief korrekt (alle Kandidaten passierten `hebel_richtung_
modus=="nur_long"`), trotzdem kam eine SHORT-Empfehlung durch.

### Root Cause

`agent/krypto/budget_allocator.py` (Zeile ~388/435) filtert `hebel_pending`/
`offene_positionen_roh` NUR nach `trigger.richtung` - der Kandidaten-
Klassifikation VOR dem LLM-Call (vergeben von `hebel_screening.py`'s Trigger-
Discovery). Das LLM (Mistral/Gemini) entscheidet `parsed["richtung"]` in
seiner strukturierten Antwort aber KOMPLETT FREI (Schema `hebel_analyst.py`
Zeile 338: `"richtung": "LONG|SHORT"`) - `trigger.richtung` wird ihm nur als
EIN beschreibender Fakt mitgegeben (`regime.richtungs_konflikt_mit_trigger`),
niemals als bindende Vorgabe, und `hebel_richtung_modus` selbst ist dem Modell
komplett unbekannt (kein Prompt-Hinweis irgendwo). `hebel_pipeline.py::
generate_hebel_signal()` uebernimmt am Ende `richtung=corrected.get("richtung")`
1:1 aus der LLM-Antwort in das persistierte/versendete `HebelSignal` - nichts
prueft das danach nochmal gegen den Schalter.

**Klarstellung zu Mistral vs. Z.ai (Nutzer-Rueckfrage):** Mistral bekommt keine
zwingende Richtungsvorgabe, sondern `trigger.richtung` nur als EINEN von vielen
Fakten (daher "kennt die Richtung indirekt"). Z.ai (`gegenpruefung.py::
leite_eigene_richtung()`) bekommt dagegen ausschliesslich objektive Marktfakten,
kennt weder Mistrals Empfehlung noch `hebel_richtung_modus`, leitet komplett
unabhaengig eine eigene Richtung her (reiner Bestaetigungs-/Widerspruchs-
Abgleich) und laeuft zudem asynchron in einem Hintergrund-Thread ERST NACHDEM
das Signal bereits gespeichert und die E-Mail schon raus ist - kann also auch
prinzipiell nichts mehr verhindern.

**Bezug zur bereits bestehenden Kontrathese-Erkennung (Nachtrag 2026-07-24
oben):** dort wird ein SHORT-Vorschlag GEGEN eine bestehende LONG-Position
bewusst NICHT geblockt, sondern als Kontrathese behandelt (Zeitfenster-
Bestaetigung, `kontrathese_zu_position`). Der neue Nur-Long-Deckel darf diesen
Fall nicht anfassen - beide NEAR/TAO-Faelle betrafen aber Symbole OHNE
aktuell offene Position (`hebel_positions`-Check: alle bisherigen TAO/NEAR-
Positionen bereits `geschlossen`/`wahrscheinlich_liquidiert`), also echte
Fresh-ERÖFFNEN-Vorschlaege ohne Kontrathese-Bezug.

### Fix

Neuer deterministischer Veto-Zweig in `agent/krypto/hebel_risk_gate.py::
post_check_hebel()`, als eigener `elif` DIREKT NACH dem bestehenden
Kontrathese-Zweig (greift also nur, wenn `position_aktuell is None` - der
Kontrathese-Fall hat bereits vorher entschieden):

```python
elif (
    hebel_richtung_modus == "nur_long"
    and richtung == RICHTUNG_SHORT
    and action == "ERÖFFNEN"
):
    risk_veto = True
    risk_veto_reason = "\"Nur Long\"-Einstellung aktiv, LLM empfahl SHORT ERÖFFNEN (auf Bitpanda nicht ausfuehrbar)"
    action = "HALTEN"
```

Neuer Parameter `hebel_richtung_modus: str | None = None` (Default `None` =
kein Veto, rueckwaertskompatibel). `agent/krypto/hebel_pipeline.py::
generate_hebel_signal()` liest den aktuellen Wert direkt vor dem Aufruf
(`ui_settings.load_settings().get("hebel_richtung_modus", "beide")`) und
reicht ihn durch - identisches Muster wie `budget_allocator.py`'s bereits
bestehender Kandidaten-Filter, nur eben NACH statt VOR dem LLM-Call.

### Korrektur einer früheren Fehleinschätzung

Der Nachtrag vom 27.07. ("Z.ai-Richtungs-Erfolgsquote", weiter oben in diesem
Kapitel) wertete "57 LONG/2 SHORT bei Mistral" als Beleg dafür, dass der
Kandidaten-Filter ausreicht, mit der expliziten Schlussfolgerung "keine
Änderung an `hebel_richtung_modus` geplant" - siehe dort eingefügte Korrektur.
Die 2 SHORT-Faelle damals waren vermutlich bereits genau diese Luecke, nur
nicht als solche erkannt, weil die Verifikation nur bis zur Kandidaten-Filter-
Ebene ging und nicht bis zur tatsaechlichen LLM-Entscheidung.

### Verifiziert (Klasse 2, synthetisch)

8 Checks gegen `post_check_hebel()`: SHORT ERÖFFNEN bei `nur_long` ohne
Position → HALTEN + Veto-Reason gesetzt; LONG ERÖFFNEN bei `nur_long` →
unveraendert; SHORT ERÖFFNEN bei `modus=beide` → unveraendert (kein
Veto, korrekte CRV-Werte fuer beide Richtungen verifiziert); kein
`hebel_richtung_modus` uebergeben (Default) → unveraendertes Altverhalten;
Kontrathese-Fall (bestehende LONG-Position, LLM schlaegt SHORT vor) bleibt
vom neuen Deckel UNBERUEHRT, der bestehende Kontrathese-Zweig greift weiterhin
zuerst. Import-Regressionscheck ueber `hebel_pipeline.py`, `hebel_risk_gate.py`,
`budget_allocator.py`, `scheduler/background.py`, `main.py`.

**Bewusst NICHT Teil dieser Runde:** kein Prompt-Hinweis an Mistral/Gemini
ueber `hebel_richtung_modus` (der deterministische Veto ist die garantierte
Absicherung, unabhaengig von Prompt-Befolgung - Nutzer-Praeferenz, siehe
`feedback_backtest_first_hard_guarantee`-Prinzip); die Architektur-Frage
`data/settings.json` (device-lokal, git-ignoriert) vs. `Basisinfos/config.yaml`
(git-synchronisiert) wurde noch am selben Tag entschieden und umgesetzt - siehe
direkt folgender Nachtrag.

## Nachtrag (2026-07-28, noch selber Tag): `hebel_richtung_modus`/E-Mail-Bitpanda-Filter von `data/settings.json` nach `config.yaml` migriert

**Auslöser:** Nach dem Nur-Long-Deckel-Fix (siehe Nachtrag oben) Nachfrage des
Nutzers, ob die geraete-lokale Persistenz der beiden Schalter selbst noch ein
Problem ist. Zwar war sie im diagnostizierten Vorfall NICHT die Ursache (der
Notebook-Wert stand die ganze Zeit korrekt auf `nur_long`), aber ein latentes
Risiko bleibt bestehen: eine kaputte/fehlende `data/settings.json` faellt
STILLSCHWEIGEND auf den Code-Default `"beide"`/`True` zurueck (kein Log-
Hinweis), und die Datei ist bewusst git-ignoriert - toggelt der Nutzer den
Schalter auf dem "falschen" Geraet, bleibt das unbemerkt. Abwaegung Kosten
(Verlust des sofortigen Wirkens, "handgepflegt"-Charakter von `config.yaml`
wird durch GUI-Schreibzugriff etwas aufgeweicht) vs. Nutzen (garantierte
Konsistenz zwischen Desktop und Notebook fuer zwei Schalter, die reales
Trading-/Versand-Verhalten steuern) - Entscheidung: migrieren, da selten
umgestellt und Korrektheit hier wichtiger als Tempo.

**Umsetzung:**
- `Basisinfos/config.yaml`: `budget_allocator.hebel_richtung_modus` (Default
  `nur_long`, der tatsaechliche Produktionswert) und
  `benachrichtigung.email.nur_bitpanda_gelistet` (Default `true`) neu.
- `config.py`: neue gemeinsame Schreibfunktion `_set_top_level_skalar()`
  (identisches Backup-/Schreib-/Reparse-/Rollback-Muster wie
  `set_regime_manueller_override()`, mit optionalem `block_scope`-Parameter
  fuer die Zeilensuche, da `nur_bitpanda_gelistet` allein nicht eindeutig
  genug waere) + zwei duenne Wrapper `set_hebel_richtung_modus()`/
  `set_email_nur_bitpanda_gelistet()`.
- `agent/krypto/budget_allocator.py`/`agent/krypto/hebel_pipeline.py`: lesen
  `hebel_richtung_modus` jetzt aus dem ohnehin bereits geladenen `config_dict`
  statt `ui_settings.load_settings()` - `import ui.settings` in beiden
  Dateien entfernt (nicht mehr benoetigt).
- `scheduler/background.py::_ist_email_relevantes_asset()`: liest
  `nur_bitpanda_gelistet` jetzt aus `config.load_config()` statt
  `ui_settings.load_settings()`.
- `ui/settings.py`: `_DEFAULTS` auf `dark_mode` reduziert (einzige echte
  GERAETE-LOKALE GUI-Praeferenz, die bewusst NICHT synchronisiert werden soll -
  Dark Mode ist reine Optik, kein Trading-Verhalten).
- `ui/app.py`: beide Menü-Handler (`_toggle_hebel_richtung()`,
  `_toggle_email_nur_bitpanda()`) rufen jetzt die neuen `config.py`-
  Schreibfunktionen auf statt `ui_settings.save_settings()`, mit
  Nutzer-Hinweis-Dialog ("wirkt erst nach Commit+Push+Pull") statt der
  bisherigen stillschweigenden Sofort-Wirkung.

**Verifiziert:** 9 synthetische Checks (`config.set_hebel_richtung_modus()`/
`set_email_nur_bitpanda_gelistet()`) direkt gegen die echte `config.yaml`
(vorher per Backup gesichert, in `finally`-Block garantiert wiederhergestellt) -
Wertaenderung, Ruecksetzung, No-Op bei identischem Wert (`False`-Rueckgabe),
ungueltiger Wert wirft `ValueError`. Import-Regressionscheck ueber alle 7
geaenderten Module inkl. `ui/app.py` (tkinter-Import) und `main.py`.

**Bewusst NICHT Teil dieser Runde:** keine Migration von `dark_mode` (bleibt
bewusst geraete-lokal, siehe Begruendung oben); keine generelle Ueberarbeitung
des `config.yaml`-vs-`data/settings.json`-Musters fuer eventuelle zukuenftige
GUI-Schalter - jeweils im Einzelfall neu abwaegen, ob ein Schalter
Trading-/Versand-relevant (→ config.yaml) oder reine GUI-Optik (→
data/settings.json) ist.

## Nachtrag (2026-07-28, frischer NB-Export): Multi-Asset-Batch Cron/Cooldown-Mismatch gefixt

**Auslöser:** Nutzer meldete "aus dem Multiassets Bereich NULL Signale" - Analyse
eines frischen `extract_notebook_diagnose.py`-Exports (22 MB, 07-28 19:36) plus
`tradinginfotool.log` bestätigte den Verdacht als echten, aktuellen Bug (nicht
nur historisch/erledigt wie eine frühere Session vermutet hatte).

**Root Cause:** `MULTI_ASSET_BATCH_CRON_HOURS = "9,19"`
(`scheduler/background.py:98`, seit dem Quotrix-Handelsfenster-Fix 2026-07-20)
laesst den Job 2x/Tag laufen, Abstand abwechselnd 10h (09→19 Uhr) und 14h
(19→09 Uhr). `cooldown_stunden_gehalten` stand aber auf 24 - ueber BEIDEN
Abstaenden. Ein gehaltenes Asset, das um 09:00 verarbeitet wird, ist beim
naechsten Lauf (10h spaeter) UND beim uebernaechsten (14h spaeter, 24h
insgesamt) noch im Cooldown - erst der 3. Lauf (~24h nach dem 1.) verarbeitet
es wieder. Log-Beweis: von 07-26 bis 07-28 (~15 Cron-Firings) gab es genau
EINEN produktiven Lauf ("13 verarbeitet", 07-27 09:05), alle anderen zeigten
"0 verarbeitet, 13 Cooldown-uebersprungen".

**Fix:** `multi_asset_batch.cooldown_stunden_gehalten` von 24 auf 8 gesenkt
(`Basisinfos/config.yaml`) - liegt unter beiden Cron-Abstaenden (10h/14h),
angelehnt an das bereits bestehende Krypto-Spot-"Kern"-Muster
(`spot_cooldown_stunden_kern=8`). `cooldown_stunden_beobachtet` (72h, reine
Beobachtungs-Kandidaten alle 3 Tage) bewusst unveraendert - eigenstaendiges,
absichtliches Design, nicht Teil des Cron-Mismatches.

**Verifiziert:** `yaml.safe_load()` gegen die geaenderte `config.yaml` -
`multi_asset_batch.cooldown_stunden_gehalten == 8`.

**Weitere Funde derselben Analyse (kein Bug, informativ):**
- "84%/93% Historie veraltet"-Muster bei Hebel-Gate-Vetos weiterhin bestaetigt
  reine 07-23-Altlast (keine neuen Treffer seither).
- Krypto-Hebel-Rueckgang bei echten ERÖFFNEN-Signalen (18→10→8→4→3 an den
  letzten 5 Tagen) ueberwiegend durch CRV-Risk-Veto (CRV < 2.0) erklaerbar -
  Hebel-Screening findet weiterhin konstant 5-11 Kandidaten/15-Min-Zyklus,
  keine Erkennungslücke gefunden.
- Krypto-Spot "massiver Rueckgang" nicht bestaetigt: 68 echte Signale am
  07-28 (bis 19:36), alles reine Krypto-Symbole, normale Aktivitaet bis 10:33
  UTC, danach Stille durch reguläre 8h/15h-Cooldown-Fenster erklaerbar.

**Bewusst NICHT Teil dieser Runde:** Z.ai-Antwortzeit/Wartemechanismus bei
Hebel-E-Mails - Nutzer-Beobachtung (Screenshot, Hebel ERÖFFNEN ETH LONG,
07-28 19:37), dass das Fazit des 2. Z.ai-Calls (Richtungs-Abgleich,
`zai_eigene_richtung`/`zai_uebereinstimmung`) in der E-Mail fehlte, obwohl der
1. Call (Konsistenz-Check) erschien - siehe
[[reference_offene_zeitbasierte_beobachtungspunkte]] fuer Details, zum
Zeitpunkt dieses Nachtrags noch nicht untersucht (siehe Folge-Nachtrag unten).

## Nachtrag (2026-07-28, noch selber Tag): Z.ai-E-Mail-Wartezeit auf 90s erhöht (60s zu knapp)

**Auslöser:** Nutzer-Auftrag "Z.ai-Wartezeit-Konstante lokalisieren und
Call-2-Laufzeiten prüfen" - direkte Fortsetzung des oben vermerkten
ETH-LONG-Screenshot-Funds.

**Fund:** `_ZAI_EMAIL_WARTE_MAX_SEKUNDEN = 60` /
`_ZAI_EMAIL_POLL_INTERVALL_SEKUNDEN = 3` in
`scheduler/background.py::_sende_signal_email_mit_zai_wartezeit()`. Beide
Z.ai-Calls laufen SEQUENZIELL (Call 2 Richtungs-Abgleich startet erst nach
Call 1 Konsistenz-Check, siehe
`agent/krypto/gegenpruefung.py::fuehre_beide_calls_im_hintergrund()`) und
werden GEMEINSAM in einem DB-Update geschrieben - kein Teilschreiben, die
E-Mail bekommt entweder beide Z.ai-Zeilen oder keine.

Log-Auswertung (`tradinginfotool.log`, 8 echte Fälle 07-26 bis 07-28):
HYPE 48s/27s, LINK 42s, NEAR 42s/60s(genau am Limit)/60s(Zeitlimit,
gescheitert), VIRTUAL 60s (Zeitlimit, gescheitert), TAO 57s. 2 von 8 Fällen
(25%) liefen tatsächlich ins alte 60s-Limit, mehrere weitere lagen knapp
darunter (48s/57s/60s) - die "typisch 12-25s je Call"-Doku-Annahme summiert
sich sequenziell auf 24-50s im Normalfall, mit Ausreißern darüber.

**Fix:** `_ZAI_EMAIL_WARTE_MAX_SEKUNDEN` von 60 auf 90 erhöht (Puffer über
dem beobachteten Maximalwert 60s). Poll-Intervall (3s) unverändert.

**Verifiziert:** Syntax-/Import-Check von `scheduler/background.py`.

**Bewusst NICHT Teil dieser Runde:** die konkrete ETH-LONG-Mail (07-28 19:37)
selbst konnte nicht direkt nachvollzogen werden - sie wurde nach dem letzten
verfügbaren Log-Sync (19:36) verschickt, dafür gibt es keine Log-Zeile. Die
Neukalibrierung stützt sich auf die 8 anderen, bereits geloggten Fälle.
Keine Umstellung von sequenziell auf parallel (beide Calls gleichzeitig
starten würde die Wartezeit auf `max(Call1, Call2)` statt `Call1+Call2`
senken) - nicht angefragt, würde eine tiefere Änderung an
`fuehre_beide_calls_im_hintergrund()` erfordern.

## Nachtrag (2026-07-28, noch selber Tag): Z.ai-Fakten-Prüfung ("Punkt 0") — kein Fakten-Bug, sondern durch `nur_long`+Bär-Regime vollständig erklärt

**Auslöser:** offener Nutzer-Auftrag vom selben Tag, die an Z.ai übergebenen
Fakten (`baue_objektive_fakten()` in `agent/krypto/gegenpruefung.py`) zu
prüfen: ob dieselbe Klasse von irreführenden/beliebig-interpretierbaren
Fakten wie beim gefixten Mistral-Retail-Konsens-Fall die anhaltend hohe
Abweichungsquote zwischen Z.ais unabhängigem Richtungsvotum und dem
Primär-Signal (zuletzt 98%, siehe frühere Nachträge) verursacht.

**Code-Audit:** `trend_label` ist bereits die neutrale EMA-Beschreibung
("Preis > EMA20 > EMA50 > EMA200"), nicht vorinterpretiert.
`_funding_rate_vorzeichen_text()` beschreibt nur den mechanischen Sachverhalt
("Longs zahlen Shorts"), keine Wertung. Kein struktureller Bug analog zum
Retail-Konsens-Fall gefunden.

**Direkte Datenauswertung (alle 103 Hebel-Signale mit `zai_eigene_richtung`,
07-26 bis 07-28 — ALLE bereits NACH dem Retail-Konsens-Fix vom 07-22, die
Abweichungsquote hat sich seither nicht verändert):**
- 101/103 "nein" (98%), davon 51 `NEUTRAL` (keine Gegenmeinung, nur keine
  klare Tendenz) und 50 echte Gegenrichtung.
- **Alle 50** echten Gegenrichtung-Fälle sind exakt `primaer=LONG,
  zai=SHORT` (keine einzige Ausnahme, nie SHORT→LONG) und **alle 50** bei
  `regime="baer"`.

**Root Cause:** `hebel_richtung_modus="nur_long"` filtert SHORT-Kandidaten
bereits VOR jedem LLM-Call heraus (98 von 103 Primär-Signalen sind LONG,
unabhängig vom Regime). Z.ai bekommt nur objektive Fakten OHNE Kenntnis
dieser Einschränkung und leitet aus bärischen Fakten (Regime/Trend/
Konfluenz/Funding/Skew) korrekt und konsistent SHORT ab. Die Abweichung ist
also kein Fakten-Qualitätsproblem, sondern die logische Konsequenz aus der
Kombination von Geschäftsregel (kein Shorting auf Bitpanda) und anhaltendem
Bär-Regime.

**Bezug zu einem separaten Fund desselben Tages:** erklärt vermutlich auch
die schwache Mistral-Hebel-Performance (Ø realisiertes CRV vor dem
Retail-Konsens-Fix +0,22, danach -0,48 bei n=416) - LONG-only-Signale in
einem anhaltenden Bär-Regime sind strukturell benachteiligt, unabhängig von
der Modellqualität.

**Verifiziert:** direkte Auswertung des vollständigen `hebel_signals`-Exports
(103 von 958 Zeilen mit gesetztem `zai_eigene_richtung`).

**Nutzer-Entscheidung:** nur dokumentieren, keine Code-Änderung.
`hebel_richtung_modus="nur_long"` bleibt wie besprochen (Bitpanda-
Limitierung weiterhin gültig). Punkt 0 damit abgeschlossen — mit
umgekehrtem Ergebnis als ursprünglich angenommen: kein Fakten-Bug, sondern
Bestätigung eines bereits bekannten strukturellen Trade-offs.

**Bewusst NICHT Teil dieser Runde:** keine Umsetzung der im Vorfeld
diskutierten Idee, Z.ais SHORT-Votum bei primärem LONG+Bär-Regime als
zusätzlichen (rein informativen) Risikofaktor/Warnhinweis anzuzeigen -
Nutzer entschied sich für die Dokumentations-Option. Punkt 0b (Wartezeit bis
Mistral-Signale als Stop-Loss/Richtungsverfehlung aufgelöst werden) bleibt
weiterhin offen, siehe [[reference_offene_zeitbasierte_beobachtungspunkte]].

## Nachtrag (2026-07-28): Veto-Schatten-Tracking — vetote Trade-Vorschläge werden jetzt weiterverfolgt statt spurlos zu verschwinden

**Auslöser:** Nutzer prüfte ein NEAR-Signal (LONG 01:17, SHORT 08:46 desselben
Tages) und fragte im Fachexpertenmodus nach: "werden aktuell potenzielle
Shorts auf Halten gesetzt, und fallen die dann unter den Tisch bei Schwankung/
Performance/Trefferquote?" Antwort nach Code-Prüfung: ja — jeder Risk-Gate-
Veto, der `action` auf `HALTEN` zurückstuft (CRV-Pflicht, Bitpanda/Cash-Veto,
Regime-Mindestkonfidenz R-5.10, Nur-Long-Deckel, Regime-Konflikt-Deckel,
Retail-Konsens-Deckel), macht das Signal für JEDE bestehende Performance-
Statistik unsichtbar — inklusive Z.ais unabhängigem Richtungsurteil auf genau
diesen Fall.

**Root Cause (verifiziert im Code):** `_TRACKABLE_ACTIONS`
(`agent/krypto/backward_tracking.py`) bzw. `_TRACKABLE_HEBEL_ACTIONS`
(`agent/krypto/hebel_backward_tracking.py`) filtern beim Backward-Tracking
konsequent auf `action IN (KAUFEN, NACHKAUFEN, VERKAUFEN, TAUSCHEN)` bzw.
`(ERÖFFNEN, NACHKAUFEN)` — ein vetotes `HALTEN` fällt sofort auf
`OUTCOME_NICHT_ANWENDBAR` und wird nie ausgewertet.
`compute_provider_performance()`/`compute_zai_richtung_performance()` lesen
wiederum nur `outcome_status`/`outcome_max_realisiertes_crv`, die für einen
vetoten Vorschlag nie gesetzt werden. Wichtig: der Veto überschreibt NUR
`action`/`risk_veto`/`risk_veto_reason` — Entry/Stop-Loss/Take-Profit-Zonen
und bei Hebel `richtung` bleiben unverändert in der DB erhalten, die
Information zum ursprünglichen LLM-Vorschlag geht also nicht verloren, sie
wird nur nicht mehr AUSGEWERTET.

**Konzept (mit Nutzer im Detail abgestimmt, "Fachexpertenmodus"):**
Pipeline-Stufen sind Stufe 0 (deterministische Vorauswahl, `hebel_screening.py`),
Stufe 1 (Budget/Cooldown-Auswahl), Stufe 2 (LLM1, entscheidet `action`/
`richtung` frei), Stufe 3 (`post_check()`/`post_check_hebel()`, deterministische
Vetos AUF LLM1s eigene Entscheidung), Stufe 4 (Z.ai/LLM2, rein beobachtend).
Gate/Parameter/Deckel-Funktionen VOR LLM1 (`pre_check()`/`pre_check_hebel()`)
blockieren den LLM-Call selbst NICHT (Ausnahme: `krise_extrem`-Regime, und
selbst dort läuft LLM1 noch) — sie bereiten nur Fakten/spätere Ceiling-Werte
vor. Nur Stufe-3-Vetos erzeugen das hier behobene Problem.

**Umsetzung — Option B (komplett getrennte Schatten-Felder statt
Wiederverwendung der `outcome_*`-Felder mit Filter-Flag), Nutzer-Entscheidung
nach Abwägung:** ein vergessener Filter an irgendeiner Konsumentenstelle
würde sonst hypothetische mit echten Trade-Ergebnissen vermischen — mit
komplett getrennten Spalten ist das strukturell ausgeschlossen.

- `database/db.py`: `_SIGNAL_VETO_SHADOW_NEW_COLUMNS`/`_HEBEL_SIGNAL_VETO_
  SHADOW_NEW_COLUMNS` (additive Migration, je 6 Felder: `veto_outcome_status`,
  `veto_outcome_geprueft_am`, `veto_outcome_entschieden_am`, `veto_outcome_
  realisiertes_crv`, `veto_outcome_max_realisiertes_crv`, `veto_outcome_
  mindestziel_erreicht_am`) + `update_signal_veto_shadow_outcome()`/
  `update_hebel_signal_veto_shadow_outcome()`. Bewusst KEIN `veto_outcome_
  datenquelle`-Feld (verifiziert per grep: `outcome_datenquelle` wird im
  gesamten bestehenden Code nirgends tatsächlich beschrieben — keine tote
  Spalte duplizieren) und keine Schatten-Kopie für `mindestziel_usd`/
  `mindestziel_eur`/`mindestziel_zeitraum_tage_geschaetzt` (rein arithmetisch
  aus Entry/Stop-Loss abgeleitet, unabhängig vom Veto).
- `database/models.py`: 6 neue Felder je in `Signal` und `HebelSignal`.
- Diskriminator "echter Schatten-Kandidat" (kein eigenes Feld nötig):
  `risk_veto=True AND action="HALTEN"` UND Entry-/Stop-Loss-/Take-Profit-
  Zonen alle gesetzt (ein regelkonformes, selbst gewähltes HALTEN hat KEINE
  Zonen und fällt automatisch durch).
- Richtungs-Ableitung für den Schatten-Zweig: bei Hebel unverändert
  `signal.richtung` (übersteht den Veto), bei Spot-family (`action` steht
  bereits auf HALTEN, `richtung_aus_action()` liefert also `None`) neu aus der
  relativen Zonen-Reihenfolge abgeleitet (`_richtung_aus_veto_zonen()`
  /`_richtung_aus_hebel_veto_zonen()`-Äquivalent: Stop-Loss über Entry =
  SHORT-Orientierung, darunter = LONG — spiegelt dieselbe implizite Logik,
  die `risk_gate.py::post_check()` für die CRV-Pflicht-Vetos bereits nutzt).
- `agent/krypto/backward_tracking.py`: `check_signal_veto_shadow_outcome()` +
  zweiter, unabhängiger Durchlauf in `run_backward_tracking()` (identische
  TP/SL/MFE-Mechanik wie der reale Zweig, inkl. Ablauf-Check; BEWUSST OHNE
  Überholt-Check — eine hypothetische, nie ausgeführte These kann nicht im
  selben Sinn "überholt" werden wie eine offene reale Position).
- `agent/krypto/hebel_backward_tracking.py`: `check_hebel_signal_veto_shadow_
  outcome()` analog, inkl. Liquidations-Prüfung (bewusst beibehalten — zeigt,
  wie riskant der vetote Vorschlag gewesen wäre, auch ohne echte Position).
- Neue Aggregationen: `compute_veto_shadow_performance()` (Provider-/Tier-
  Aufschlüsselung wie `compute_provider_performance()`, Aggregations-Kern
  gemeinsam in `_aggregate_resolved_signal_rows()` extrahiert),
  `compute_zai_richtung_performance_schatten()` (Z.ais Urteil NUR für vetote
  Fälle), `compute_gesamt_signalqualitaet()` ("Gesamt-Signalqualität,
  unabhängig vom Risk-Gate" — additive Zusammenführung von Real+Schatten AUF
  DER ANZEIGE-EBENE, Rohzähler-Summierung statt Rückrechnung aus bereits
  gemittelten Werten, um Rundungsfehler bei fehlendem `entry_mid` auszuschließen;
  Storage bleibt getrennt).
- Provider-Sendezähler-Fix (separater, aber verwandter Fund): `compute_
  provider_sendezaehler()` zählt jede Zeile mit `groq_raw_response IS NOT
  NULL` unabhängig von `outcome_status` — ein selten eingesetzter Provider
  (Gemini) konnte in der bisherigen Provider-Performance-Karte komplett
  unsichtbar bleiben, solange kein einziges seiner Signale aufgelöst war.
- `remote/status.py`/`remote/server.py`: Remote-Seite in 3 Gruppen
  reorganisiert (Nutzer-Wunsch: "sauber in eigene Bereiche aufteilen mit
  einem bestimmten Zweck") — Gruppe A "Ausgeführte Empfehlungen" (Provider-
  Performance/Konfidenz-Kalibrierung/Richtungstreffer-Quote, unverändert),
  Gruppe B "Unabhängige Zweitmeinung (Z.ai)" (Z.ai-Richtungs-Erfolgsquote,
  unverändert), Gruppe C "Veto-Schatten + Gesamt" (3 neue Karten). Provider-
  Performance-Karte zeigt jetzt zusätzlich die Sendezahl je Provider.
- `extract_notebook_diagnose.py`: alle 6 neuen `veto_outcome_*`-Spalten in
  beiden Spaltenlisten + alle 4 neuen Aggregationen im Export-Payload.

**Bewusst NICHT Teil dieser Runde (Nutzer-Fragen im Detail geklärt, siehe
Diskussion):**
- Gruppe B bereits vollständig für alle 6 Pipelines verdrahtet bestätigt
  (Call 1+2, siehe früherer Nachtrag "Z.ai auf alle 6 Pipelines") — keine
  weitere Arbeit nötig, nur zur Klarstellung erneut geprüft.
- Kein eigener "Z.ai-Konsistenz-Check-Trefferquote"-Karte (nur Call-Zähler
  vorhanden) — separat vermerkt, nicht Teil dieser Runde.
- Kein Ueberholt-Check im Veto-Schatten-Zweig (siehe Begründung oben).

**Verifiziert:** synthetische Tests für alle neuen Funktionen (LONG-/SHORT-
Zonen-Ableitung, Diskriminator, TP/SL/Liquidation/Abgelaufen/Offen,
Aggregations-Konsistenz Real vs. Schatten vs. Gesamt), Flask-Smoke-Test
(Index-HTML enthält alle 3 Gruppen-Header + neuen Karten-IDs, `/api/status`
liefert alle 4 neuen Felder), SQL-Spaltenlisten-Syntaxcheck, und ein echter
Lauf gegen eine Kopie der Produktions-DB (Original nie direkt geöffnet,
siehe [[feedback_desktop_kein_produktivstart]]): 4 reale Spot- und 1 reales
Hebel-Veto-HALTEN gefunden, davon 0 Spot-/1 Hebel-Zeile mit vollständigen
Zonen als echter Schatten-Kandidat identifiziert; End-to-End-Lauf löste eine
echte historische Aktien/Cerebras-Zeile als Stop-Loss auf (Ø CRV -2,10) und
die Hebel-Zeile als Abgelaufen — keine Abstürze, kein Datenverlust.

## Nachtrag (2026-07-28): Punkt 0b — Wartezeit bis Mistral-Hebel-Signale als Stop-Loss/Richtungsverfehlung aufgelöst werden, PLUS Enge-Stop-Loss-Backtest jetzt ausreichend Stichprobe

**Auslöser:** Nutzer-Auftrag im selben Analyseblock wie Punkt 0 (Z.ai-Fakten-
Prüfung): "wie lange die Wartezeit war bis Mistral - als falsche Richtung
bzw. hat Zielzone nicht erreicht gemessen wurde - als Experte". Analysiert
gegen den frischesten Notebook-Export (28.07., 22:07 Uhr).

**Methodischer Hinweis (wichtig für künftige Zeit-Analysen dieser Art):**
`outcome_entschieden_am`/`outcome_geprueft_am` sind reine Kalendertag-Strings
(aus der Tages-OHLC-Zeile `row.date`), `created_at` ist ein voller
Zeitstempel — eine naive Sekunden-Differenz erzeugt bei Auflösung am
Erstellungstag scheinbar negative Wartezeiten. Korrekt: auf Kalendertag-Basis
rechnen (`date(entschieden_am) - date(created_at)`, min. 0).

**Ergebnis (694 Mistral-Hebel-Signale, gefiltert nach `outcome_status`):**

| Ausgang | n | Median | Mittelwert |
|---|---|---|---|
| Stop-Loss erreicht | 50 | 1 Tag | 1,60 Tage |
| Take-Profit erreicht | 11 | 2 Tage | 2,36 Tage |
| Richtungsverfehlung ohne SL (überholt/abgelaufen, Mindestziel nie erreicht) | 19 | 1 Tag | 1,53 Tage |

**Einordnung:** Verluste lösen sich fast doppelt so schnell auf wie Gewinne
(1 vs. 2 Tage Median) — die Messung wartet bei Fehlschlägen NICHT zu lange,
sie schlägt eher zu früh zu. Die Hypothese "die Wartezeit selbst verzerrt
das schlechte Mistral-Bild nach unten" ist damit entkräftet — wenn überhaupt
wirkt die Asymmetrie in die andere Richtung.

**Direkter Anschluss an den bestehenden Enge-Stop-Loss-Fund (22.07.,
`sl_abstand_eng_schwelle_relativ`, siehe
[[project_historische_trefferquote_nachbesserung]]):** von den 50
Stop-Loss-Fällen haben 39 (78%) einen SL-Abstand unter 5%, Ø aller 50 Fälle
nur 3,5% — mitten in der damals identifizierten blinden Zone (2-5%), die der
bestehende Risikofaktor mit seiner 2%-Schwelle verpasst. Diese engen Fälle
lösen sich noch schneller auf (Median 1 Tag, 44% schon an Tag 0) als die
wenigen mit weiterem SL (Median 2 Tage) — konsistent mit "zu enger Stop,
von normalem Kursrauschen ausgelöst, bevor die These eine faire Chance
hatte".

**Backtest jetzt mit ausreichender Stichprobe (Wiedervorlage-Bedingung
n≥15/Bucket aus dem 27.07.-Fund war bei n=5-11 noch nicht erfüllt, jetzt
erfüllt):**

| SL-Abstand-Bucket | n | Win-Rate | Ø realisiertes CRV |
|---|---|---|---|
| <2% | 9 | 0,0% | -1,00 |
| 2-5% | 36 | 16,7% | -0,41 |
| 5-10% | 16 | 31,2% | +0,31 |
| ≥10% | 0 | — | — |

Monotoner Zusammenhang: je enger der Stop, desto schlechter Win-Rate/CRV.
Die 5-10%-Zone liegt nahe/über der Gewinnschwelle, alles darunter ist klar
verlustträchtig. `<2%` weiterhin zu klein für Alleinstellung (n=9), aber
`2-5%` (n=36) und `5-10%` (n=16) sind jetzt beide über der n≥15-Schwelle —
die 27.07. gesetzte Wiedervorlage-Bedingung ist damit erfüllt, eine
Entscheidung über Gegenmaßnahmen ist jetzt sachlich fundiert möglich (siehe
Diskussion mit Nutzer, Optionen unten).

**Diskutierte Lösungsoptionen (mit Nutzer besprochen, Entscheidung siehe
[[project_enge_stop_loss_backtest_und_massnahmen]]):**
- **A (soft):** `sl_abstand_eng_schwelle_relativ` von 2% auf 5% anheben —
  rein informativ, bestehender "Enger Stop-Loss"-Risikofaktor deckt dann
  auch die eigentliche Problemzone ab, kein Verhaltenszwang.
- **B (hart):** neuer deterministischer Veto in `post_check_hebel()` analog
  zur CRV-Pflicht — SL-Abstand < 5% erzwingt HALTEN. Würde durch das frisch
  gebaute Veto-Schatten-Tracking automatisch weiterbeobachtet (Selbstprüfung
  ohne separaten Backtest-Harness).
- **C (mittel):** Positionsgröße statt Hard-Veto skalieren (analog
  Konfidenz-Skalierung), reduziert Exposure statt Trade komplett zu blocken.
- **D (praeziser, groesserer Aufwand):** Schwelle relativ zur Volatilitaet
  (ATR-Perzentil, bereits vorhanden aus Baustein 2) statt fixem Prozentsatz -
  ein "5%-Stop" bedeutet fuer BTC etwas anderes als fuer einen volatilen
  Altcoin.

## Nachtrag (2026-07-28): Option D umgesetzt (Fakt + Prompt-Regel, bewusst OHNE Hard-Veto) - Root-Cause-Analyse vor Umsetzung

**Root-Cause-Analyse (vor der Umsetzung durchgefuehrt, Nutzer-Auftrag "berechnen
wir etwas falsch oder treffen falsche Annahmen"):** `agent/krypto/hebel_analyst.py`
Regel 6 durchgesehen - der bestehende CRV-Formel-Code selbst rechnet korrekt
(fruehere Verifikation), das Problem liegt eine Ebene davor. Zwei konkrete
Luecken gefunden:
1. Regel 6 sagt dem Modell nur, Entry/Stop/Take-Profit aus `atr.wert`/
   `support_resistance`/`fibonacci` abzuleiten - OHNE eine Mindestdistanz-
   Vorgabe. Das Modell erfuellt die Regel bereits formal, sobald es irgendeinen
   der drei Referenzpunkte zitiert, unabhaengig davon wie nah er liegt.
2. `technische_analyse.atr.wert` wurde bisher NUR als absoluter Preiswert
   (USD) geliefert, nicht als Prozentsatz vom Kurs - das Modell musste diese
   Umrechnung selbst vornehmen, um die Stop-Distanz gegen die Volatilitaet
   einzuordnen (fehleranfaelliger Rechenschritt).
3. Nebenbefund: fuer Symbole OHNE Kraken-Spot-Paar liefert
   `atr_close_to_close_proxy()` (per Docstring ausdruecklich "kein echtes
   ATR") eine strukturell zu niedrige Volatilitaets-Naeherung (keine
   untertaegigen Ausschlaege erfasst) - verschaerft das Problem zusaetzlich
   fuer diese Teilmenge.

**Kein Rechenfehler in der Kern-Logik gefunden** (CRV-Formel, Zonen-Vergleich
korrekt) - die Ursache ist eine Prompt-/Fakten-Luecke: keine Volatilitaets-
Verankerung fuer die Stop-Distanz, nicht ein Bug in einer bestehenden Formel.

**Cross-Check-Empfehlung (wie man das serioes verifiziert, zweite Nutzerfrage):**
der bereits durchgefuehrte Backtest gegen reale Trade-Ausgaenge (Win-Rate/CRV
je SL-Abstand-Bucket) ist der belastbarste Cross-Check ueberhaupt (validiert
gegen tatsaechliche Marktergebnisse, nicht nur gegen eine andere Formel).
Zusaetzlich sinnvoll (nicht Teil dieser Runde): eigene Wilder-ATR-Implementierung
gegen eine Referenzbibliothek (z.B. pandas-ta) mit denselben Kraken-OHLC-
Rohdaten gegenrechnen; Stichprobenvergleich unserer ATR-%-Werte gegen eine
externe Chartquelle (TradingView/Binance).

**Entscheidung: D statt B, mit Begruendung ueber die reinen Bucket-Zahlen
hinaus.** B (harter 5%-Fixprozent-Veto) wuerde nur das Symptom kappen - ein
fixer Cutoff ist fuer BTC in ruhiger Phase zu grosszuegig und fuer einen
volatilen Altcoin in einer Squeeze-Phase immer noch zu eng, das
Grundproblem (keine Volatilitaets-Bindung) bliebe bestehen. D behebt die
tatsaechliche Ursache. Nutzer-Vorgabe fuer die Umsetzung: "safe genug ...
dass wir keine Signale unnoetig wegschmeissen" - deshalb bewusst OHNE
deterministischen Backstop-Veto in dieser Runde, rein informativ/Prompt-
Guidance (siehe unten).

**Umsetzung (`agent/krypto/hebel_analyst.py::build_hebel_facts()`):**
- Neuer Fakt `technische_analyse.atr.relativ_prozent` = ATR-Wert / aktueller
  Kurs × 100 (gerundet auf 2 Nachkommastellen), `None` wenn ATR oder Preis
  fehlt/0 ist (kein Crash, kein irrefuehrender Wert).
- Regel 6 um einen Richtwert erweitert: Stop-Loss-Abstand sollte in der
  Regel mindestens dem 1,5-fachen von `atr.relativ_prozent` entsprechen,
  MIT explizitem Hinweis auf den Backtest-Befund (SL<5% = 0-16,7% Win-Rate,
  5-10% = 31,2%). Ausdruecklich als RICHTWERT markiert (nicht wie das
  CRV-Minimum in Regel 5 eine harte Vorgabe) - begruendetes Abweichen bei
  einem klar naeheren Support/Widerstand/Fibonacci-Level ist erlaubt, muss
  aber in `short_reasoning` explizit genannt werden.
- Bewusst NICHT veraendert: der bestehende "Enger Stop-Loss"-Risikofaktor
  in `hebel_risk_gate.py::compute_risikofaktoren_hebel()` (weiterhin fixer
  2%-Schwellenwert, rein informativ) - keine zusaetzliche Verhaltensaenderung
  ueber die Prompt-Regel hinaus in dieser Runde.

**Verifiziert:** Import-Regressionscheck, isolierter Test der neuen
Berechnung inkl. Edge Cases (ATR/Preis `None`, Preis 0 - kein Crash, `None`-
Rueckgabe statt falscher Wert).

**Bewusst NICHT Teil dieser Runde:** kein harter Veto (Option B verworfen,
siehe Begruendung oben); keine Aenderung an Spot-family-Analysten (Fund war
Hebel-spezifisch, gleiche Luecke dort nicht verifiziert); kein Cross-Check
gegen externe ATR-Referenzbibliothek (empfohlen, aber nicht durchgefuehrt).

**Doku-Zuordnung (korrigiert):** der neue Fakt `atr.relativ_prozent` ist in
`Basisinfos/Fakten_Entscheidungsmappe.md` katalogisiert (Abschnitt 4.2, plus
neuer Asymmetrie-Punkt 6 in Abschnitt 3.3 zur offenen Spot-Frage) - das ist
der bestehende, richtige Ort fuer Fakt-Entscheidungen (Frage-1/Frage-2-
Raster), nicht eine neue Datei. Der Backtest selbst bleibt in
[[project_enge_stop_loss_backtest_und_massnahmen]] (Memory).

## Nachtrag (2026-07-29): Eigenkapital-Richtwert fuer Hebel-Positionsgroesse (weicher Deckel)

**Ausloeser:** Bei der Diskussion des R-5.10-Konfidenz-Veto-Fundes (siehe
`project_r510_konfidenz_veto_analyse_29_07.md`, Memory) pruefte der Nutzer
konkret nach, welche Eigenkapitalbetraege die App aktuell fuer Hebel-
Signale empfiehlt. Ergebnis (149 Signale mit Eigenkapitalbedarf): **Median
~1.204 USD (~1.100 EUR), Spanne 290 bis 41.242 USD** - weit ueber der
tatsaechlichen Handelspraxis des Nutzers (100-300 EUR ueblich, max. 500 EUR
normal, bis 1.000 EUR nur bei bewusster Sonderlage).

**Wichtige Klarstellung (Nutzerfrage "was bringt uns das?"):** diese
Aenderung behebt NICHT das eigentliche Konfidenz-Kalibrierungsproblem
(bleibt offen, separat zu besprechen) und veraendert auch nicht Win-Rate/
CRV/Liquidations-Klassifikation eines Signals - all das haengt nur von den
Preiszonen ab, nicht von der Positionsgroesse. Es ist eine reine Praxis-/
Risikomanagement-Anpassung: die bestehende RM-1-Risikoformel (1% Portfolio-
Verlustrisiko) zielt auf ein FESTES Verlustrisiko, nicht auf ein gedeckeltes
Eigenkapital - bei engem Stop-Loss/niedrigem Hebel kann das einen sehr hohen
Eigenkapitalbedarf verlangen, unabhaengig von der Signalqualitaet.

**Umsetzung (`agent/krypto/hebel_risk_gate.py::post_check_hebel()`):**
- Neuer Config-Wert `risiko.hebel.eigenkapital_richtwert_eur` (Default 500).
- Wenn der berechnete `eigenkapitalbedarf_eur` diesen Wert ueberschreitet,
  wird `positionsgroesse_usd` (und damit `eigenkapitalbedarf`/
  `eigenkapitalbedarf_eur`) proportional heruntergerechnet, bis der
  Richtwert genau erreicht ist. **Hebel (`hebel_final`), Zonen und These
  bleiben unveraendert** - die Empfehlung bleibt bestehen, nur die
  Positionsgroesse wird realistischer dimensioniert.
- **Bewusst KEIN Veto/harte Grenze.** Neues Transparenz-Feld
  `eigenkapital_deckel_hinweis` (analog `hebel_korrektur_hinweis`),
  NUR gefuellt wenn tatsaechlich skaliert wurde.
- **Bewusst KEINE automatische Sonderfall-Erkennung** fuer die vom Nutzer
  genannte Ausnahme ("bis 1.000 EUR bei BTC-Absturz + hoher Rebound-
  Wahrscheinlichkeit") - das waere eine komplexe, wahrscheinlich
  unzuverlaessige Mustererkennung fuer eine Situation, die der Nutzer selbst
  besser erkennt und manuell entscheidet.
- Nutzer-Vorgabe ausdruecklich als **"Gummi-Parameter"** verstanden: der
  Wert 500 EUR gilt nur, solange das System nicht besser kalibriert ist
  bzw. wesentliche Luecken bestehen - bei wachsendem Vertrauen in die
  Kalibrierung ist eine Anpassung vorgesehen, kein dauerhaft fixer Wert.

**Neue Felder:** `database/models.py::HebelSignal.eigenkapital_deckel_hinweis`
(additive Migration `_migrate_hebel_signal_eigenkapital_deckel_column()`),
angezeigt in App (`ui/hebel_view.py`) und E-Mail (`scheduler/background.py`),
exportiert in `extract_notebook_diagnose.py`.

**Verifiziert (synthetisch, Testklasse 3 - DB-Schema-Aenderung):**
T1 Migration frische In-Memory-DB (Spalte vorhanden) - PASS; T2 Migration
zweimal ausgefuehrt (idempotent) - PASS; T3 Positivfall (Eigenkapitalbedarf
3.035 EUR -> auf 500 EUR gedeckelt, Hinweis gesetzt) - PASS; T4 Negativfall
(Eigenkapitalbedarf 84 EUR, kein Deckel) - PASS; T5 fehlender Config-Wert
(kein Crash, keine Skalierung) - PASS; T6 DB-Insert/Read-Roundtrip erhaelt
das Feld korrekt - PASS. Import-Regressionscheck aller 7 geaenderten Module
bestanden.

**ERLEDIGT (29.07., spaeter am selben Tag):** die Frage, ob die mangelnde
Vorhersagekraft der LLM-Konfidenz bei Hebel ein Fehler in unserem System
oder eine bekannte Grenze ist, wurde per externer Fachliteratur-Recherche
beantwortet (LLM-Konfidenz-Kalibrierung, CRV/Reward-Risk als Praediktor +
Positionsgroessen-Normen, Risikofaktoren-Aggregation + Backtest-Overfitting-
Fallstricke) - Grundlage fuer die nachgeschaerfte n>=50-Regel in
`Test_und_Verifikationsmethodik.md`. Details siehe
[[reference_externe_recherche_konfidenz_crv_risikofaktoren_29_07]].

## Nachtrag (2026-07-29): extract_notebook_diagnose.py - Assetklassen-Aufschluesselung nachgezogen

**Ausloeser:** bei der Kauf-vs-Nichtkauf-Analyse (siehe Nachtrag oben) fiel auf,
dass `extract_notebook_diagnose.py` sieben Aggregat-Funktionen
(`compute_provider_performance()`, `compute_veto_shadow_performance()`,
`compute_gesamt_signalqualitaet()`, `compute_konfidenz_kalibrierung()`,
`compute_zai_richtung_performance()`, `compute_zai_richtung_performance_
schatten()`, `compute_provider_sendezaehler()`) OHNE das seit 2026-07-20
verfuegbare optionale `watchlist`-Argument aufrief - dadurch landeten alle
Spot-family-Signale (Krypto/Aktien/Rohstoffe/ETF) in einem einzigen
"spot"-Topf, waehrend die Live-App-Remote-Seite (`remote/status.py`)
dieselben Funktionen laengst MIT `watchlist` aufruft und nach
`asset.assetklasse` aufschluesselt (siehe `SPOT_ASSETKLASSEN` in
`remote/server.py`). Folge: bei Analysen aus diesem Export war nicht
unterscheidbar, ob ein Muster krypto-spezifisch war oder auch andere
Assetklassen betraf.

**Umsetzung:** `watchlist = config_module.get_watchlist()` einmalig geladen
(reiner Lesezugriff auf config.yaml, kein Schreibzugriff, keine
Verhaltensaenderung an der Produktions-App), an alle sieben Aufrufe
durchgereicht - identisch zum bereits etablierten Muster in
`remote/status.py`. Kein neues Verhalten, nur ein bereits vorhandener
Aufschluesselungs-Modus wird jetzt auch im Export genutzt.

**Verifiziert (Testklasse 2):**
  Betroffene Datei(en): extract_notebook_diagnose.py
  Aenderungsklasse: 2
  Testfaelle: T1 ohne watchlist -> altes Verhalten (alles unter "spot") - PASS
              T2 mit watchlist -> BTC->krypto, PLTR->aktien korrekt getrennt - PASS
  Regressionscheck (Import des gesamten Moduls, __main__-Guard verhindert
  main()-Ausfuehrung beim Import): PASS
  Gesamturteil: verifiziert (Stufe 2)

**Ausstehend:** Nutzer muss `extract_notebook_diagnose.py` am Notebook erneut
laufen lassen + syncen, damit der naechste Export die feinere Aufschluesselung
tatsaechlich enthaelt (Stufe 5, "im Betrieb bestaetigt", noch offen).

## Nachtrag (2026-07-29): Risikofaktoren-Häufung bei Hebel — Backtest durchgeführt, kein Gate gebaut

**Ausloeser:** offener Folgepunkt vom 2026-07-23 (siehe Fakten_Entscheidungsmappe-
Historie): "Regime-Konflikt"/"Technische Konfluenz"/"Alt-Coin-Marktphase"/
"These-Regime-Widerspruch" werden bei Hebel-Signalen als unabhaengige
Risikofaktor-Bulletpoints gelistet, obwohl sie teilweise korreliert sind -
Wiedervorlage-Bedingung war n>=30-50 aufgeloeste Hebel-Signale fuer einen
Backtest.

**Datenlage:** n=62 aufgeloeste Hebel-Signale mit `risikofaktoren_json`
(nach Behebung der Assetklassen-Export-Luecke, siehe Nachtrag oben).

**Erster Durchgang** (naiv, Anzahl gleichzeitig negativer Struktur-Faktoren):
zeigte scheinbar das GEGENTEIL der Ausgangs-Hypothese (>=3 negative Faktoren
schnitten mit 24,4% Win-Rate besser ab als <3 mit 4,8%).

**Vertiefung deckte zwei Konfundierungen auf:**
1. `Regime-Konflikt` ist fuer LONG-Signale im anhaltenden Bär-Regime eine
   Tautologie (54/54 LONG-Signale "negativ", bei SHORT nie gebildet) - der
   Faktor traegt keine unabhaengige Information, sondern kodiert nur die
   Richtungswahl selbst.
2. Nach Herausrechnen dieses Konfunds (nur LONG, verbleibende 3 Faktoren)
   UND Anwendung des Symbol-Konzentrations-Checks (siehe
   `Test_und_Verifikationsmethodik.md` Abschnitt 2.5) zerfaellt auch dieser
   Rest: der scheinbar schlechteste Bucket (1 negativer Faktor, 0% WR) ist
   zu 100% ein einziges Symbol (KAIA, 8/8) - kein echtes Muster.

**Fazit:** weder die urspruengliche Hypothese (mehr negative Faktoren =
schlechter) noch ihre scheinbare Umkehr sind robust genug belegt. Einzig
der groesste, diverseste Bucket (3 von 4 Faktoren negativ, n=29→16 nach
Symbol-Bereinigung, 10 unterschiedliche Symbole) bleibt einigermassen
belastbar mit 31-50% Win-Rate - deutlich ueber dem Hebel-Gesamtdurchschnitt.

**Entscheidung:** kein deterministischer Häufungs-Deckel gebaut, kein Code
geändert. Punkt gemäß eigener Wiedervorlage-Kriterien geschlossen als
"geprüft, kein belastbarer Zusammenhang gefunden" (nicht "Gegenteil
bestätigt" - diese anfängliche Lesart wurde im Gespräch selbst korrigiert).

## Nachtrag (2026-07-29): Regelwerk-Audit (3 Stufen) + Stufe 0 - Eigenkapital-Deckel-FX-Fallback gefixt

**Ausloeser:** Nutzer-Auftrag nach der Hebel-Gap-Analyse, das gesamte Regelwerk
(Determinismus/Gates → Mistral-LLM → Z.ai-Gegenpruefung) als Experte auf
Fehler/Ungenauigkeiten/fehlende Info zu pruefen - ausgeloest durch die
zugespitzte, berechtigte Frage, ob das System ueberhaupt besser als ein
Muenzwurf ist. 3 parallele Audit-Agenten (je eine Pipeline-Stufe) fanden
mehrere zusammenhaengende Kernbefunde:

1. **CRV≥2.0-Gate ist kein Prognosefilter, sondern ein Selbstkonsistenz-Check**
   der vom LLM selbst gewaehlten Entry/Stop/Take-Zonen - erklaert strukturell,
   warum durchgelassene Trades (17,5% WR) schlechter abschneiden als vetote
   (45,9% WR).
2. **Regel 13 im Mistral-Prompt (`hebel_analyst.py`) haelt die Konfidenz
   kuenstlich ueber 75%**, im direkten Widerspruch zu Regel 2/16 (die eine
   Daempfung bei Regime-Konflikt fordern) - konkrete, behebbare Ursache fuer
   die fehlende Trennschaerfe der Konfidenz.
3. **Schaerfste Baseline:** bei CRV≥2.0 liegt die Break-even-Trefferquote bei
   33,3% - tatsaechlich gemessen: 17,5%. Das System schlaegt nicht nur keinen
   Muenzwurf, sondern nicht einmal seine eigene Chance-Risiko-Mathematik.
4. **Z.ai bekommt strukturell weniger Fakten als Mistral** (6 statt ~26 Werte) -
   die 4,8%-Uebereinstimmungsquote misst teils unterschiedliche
   Informationslage, nicht nur unterschiedliche Bewertung.
5. **Es existiert nirgends ein Baseline-Vergleichsmechanismus** - alle drei
   Audits fanden das unabhaengig und schlugen dieselbe Loesung vor (siehe
   Justierungsplan unten, Stufe 2).

Vollstaendige Befundliste (je Stufe, priorisiert Kritisch/Wichtig/Kosmetisch)
in [[project_regelwerk_audit_29_07]] (Memory).

### Justierungsplan (4 Stufen)

- **Stufe 0** (sofort, isolierter Bug): Eigenkapital-Deckel-FX-Fallback -
  SIEHE UNTEN, umgesetzt.
- **Stufe 1** (kleiner Prompt-Fix): Regel-13-Widerspruch aufloesen - SIEHE
  UNTEN, umgesetzt.
- **Stufe 2** (Baseline-Infrastruktur): konsolidierte Baseline-Vergleichs-
  Funktion(en) in `backward_tracking.py` - SIEHE UNTEN, umgesetzt.
- **Stufe 3** (groessere Strukturfragen, Diskussion noetig): 4 Punkte -
  Punkt 1 (CRV-Expectancy-Gate) bewusst IN EVIDENZ gehalten (Backtest zeigt
  negative CRV-Trefferquoten-Korrelation, ueberwiegend Echo des
  Enge-Stop-Loss-Befunds, Wiedervorlage bei n≥50 Post-Fix-Signalen); Punkt 2
  (Deckel-Konstanten kalibrieren) vertagt (aktuell 0 Varianz im Outcome,
  Kalibrierung derzeit prinzipiell unmoeglich); Punkt 3
  (Regime-Konflikt-Restrukturierung) SIEHE UNTEN, umgesetzt; Punkt 4
  (Prompt-Bias zugunsten Empfehlungen entschaerfen) SIEHE UNTEN, umgesetzt.
  **Stufe 3 damit vollstaendig bearbeitet.**

### Stufe 0 umgesetzt: Eigenkapital-Deckel griff nicht ohne FX-Kurs

**Fund:** der am 29.07. eingefuehrte 500-EUR-Eigenkapital-Deckel
(`hebel_risk_gate.py::post_check_hebel()`) steckte komplett innerhalb von
`if eur_usd_fx_rate:` - schlug der EURCV-Snapshot fehl/fehlte, wurde der
Deckel STILLSCHWEIGEND uebersprungen, obwohl `eigenkapitalbedarf` (USD)
laengst bekannt war.

**Fix:** `eigenkapital_deckel_hinweis` wird jetzt IMMER vorbelegt (`None`),
und bei fehlendem FX-Kurs wird ein sichtbarer Warn-Hinweis gesetzt
("Eigenkapital-Richtwert NICHT geprueft - EUR/USD-Kurs aktuell nicht
verfuegbar"), statt den Ausfall lautlos zu verstecken. Bewusst KEIN
Fallback-FX-Schaetzwert eingefuehrt - wuerde der bestehenden Konvention
widersprechen, EUR-Felder bei fehlendem Kurs auf `None` zu lassen statt zu
schaetzen.

**Verifiziert (Testklasse 2):**
  Betroffene Datei(en): agent/krypto/hebel_risk_gate.py
  Aenderungsklasse: 2
  Testfaelle: T1 FX-Kurs vorhanden, ueber Richtwert -> Deckel greift (Regression) - PASS
              T2 FX-Kurs fehlt (None) -> sichtbarer Warn-Hinweis statt stillem Ausfall - PASS
              T3 FX-Kurs=0 (falsy) -> gleiches Verhalten wie None - PASS
              T4 FX-Kurs fehlt + kein Richtwert konfiguriert -> kein Crash, kein Hinweis - PASS
  Regressionscheck (Import aller betroffenen Module): PASS
  Gesamturteil: verifiziert (Stufe 2)

### Stufe 1 umgesetzt: Regel-13-Widerspruch im Mistral-Prompt aufgeloest

**Fund:** Regel 13 (`hebel_analyst.py::SYSTEM_PROMPT`) schreibt vor, dass ein
EINZELNER isolierter Schwachpunkt im `gegenargument` (z.B. gemischte
Konfluenz, knappes CRV) die Konfidenz nur moderat daempfen darf, niemals
unter 75%. Regel 2 und Regel 16 verlangen aber ausdruecklich, dass genau
EIN Faktor - Regime-Konflikt (`regime.richtungs_konflikt_mit_trigger`) bzw.
btc_season/baer_flucht-Alt-Skepsis bei Nicht-Core-Assets - Konfidenz UND
Hebel-Vorschlag daempft, weil eine gehebelte Gegen-Trend-Position
strukturell riskanter ist. In der Praxis (persistentes Baer-Regime) ist
Regime-Konflikt bei LONG-Signalen quasi immer vorhanden und quasi immer der
EINZIGE Schwachpunkt - Regel 13 hielt die Konfidenz dadurch systematisch
ueber 75%, obwohl Regel 2 genau das verhindern wollte. Das ist eine der
konkreten, behebbaren Ursachen fuer die fehlende Trennschaerfe der Konfidenz
(siehe Audit-Fund 2 oben).

**Fix:** Regel 13 bekommt eine explizite AUSNAHME-Klausel: der in Regel 2
beschriebene Regime-Konflikt und die in Regel 16 beschriebene
btc_season/baer_flucht-Alt-Skepsis sind KEINE generischen, mit gemischter
Konfluenz/knappem CRV gleichwertige Einzel-Schwachpunkte, sondern die
einzigen beiden Faelle, fuer die Regel 2 bzw. Regel 16 selbst schon eine
Daempfung verlangen. Liegt einer dieser beiden Faelle vor, DARF die
Konfidenz auch als einziger Schwachpunkt unter 75% fallen. Reiner
Prompt-Wortlaut-Fix, keine Code-/Schema-Aenderung - kein anderer Codepfad
haengt an der exakten 75%-Zahl (die Konstanten `KONFIDENZ_SCHWELLE_NIEDRIG`/
`KONFIDENZ_SCHWELLE_HOCH` in `risk_gate.py` sind 55/70, unabhaengig davon).

**Verifiziert (Testklasse 1, Prompt-only):**
  Betroffene Datei(en): agent/krypto/hebel_analyst.py
  Aenderungsklasse: 1
  Testfaelle: Import von hebel_analyst.py - PASS
              Regelnummerierung weiterhin fortlaufend 1-26 (keine Luecke/Dopplung) - PASS
              Ausnahme-Klausel vorhanden und referenziert Regel 2/16 korrekt - PASS
              Umlaute/Zeilenumbrueche im zusammengefuegten Prompt-Text korrekt (kein
              Mojibake, keine fehlenden/doppelten Leerzeichen an der Einfuegestelle) - PASS
  Gesamturteil: verifiziert (Stufe 1)

### Stufe 2 umgesetzt: konsolidierte Baseline-Vergleichs-Funktionsfamilie

**Fund:** alle drei Audit-Agenten fanden unabhaengig voneinander denselben
Mangel - nirgends im Code existiert eine Antwort auf die vom Nutzer selbst
aufgeworfene Frage ("kann ich nicht auch einfach eine Muenze werfen?"). Eine
Trefferquote ohne Referenzgroesse (Muenzwurf, CRV-Pflichtgrenze, regimenaive
Baseline, Z.ai-Zufallsuebereinstimmung) ist nicht interpretierbar.

**Fix:** zwei neue Funktionen in `agent/krypto/backward_tracking.py`
(gebuendelt statt drei getrennter, wie von allen drei Audits vorgeschlagen):
  - `compute_baseline_vergleich(conn, tier, erlaubte_symbole=None,
    crv_minimum=CRV_MINIMUM)`: Trefferquote je Tier (spot/hebel) plus (a)
    Muenzwurf-Vergleich (50%) mit exaktem zweiseitigem Binomialtest, (b) bei
    Hebel zusaetzlich CRV-Breakeven-Vergleich (`1/(1+crv_minimum)`, bei
    CRV_MINIMUM=2.0 also 33,3%), (c) bei Hebel zusaetzlich regimenaiver
    Vergleich (Trefferquote des `trigger_zweig='trendfolge'`-Teilsatzes -
    ein simpler Momentum-Trade OHNE LLM-Analyse als Referenz).
  - `compute_zai_uebereinstimmung_baseline(conn, watchlist=None)`: die
    bislang nur ad-hoc in `extract_notebook_diagnose.py` berechnete
    LLM1-vs-Z.ai-Uebereinstimmungsquote (`zai_uebereinstimmung`) gegen eine
    3-Weg-Zufalls-Baseline (33,3% - `zai_eigene_richtung` kann LONG/SHORT/
    NEUTRAL sein, die Primaer-Richtung ist binaer, ein zufaelliger 3-Weg-Tipp
    traefe sie im Schnitt in 1/3 der Faelle).
  - Gemeinsamer Helfer `_binomialtest_zweiseitig_p_wert(erfolge, n, p)`:
    exakter Test via `math.comb()`, BEWUSST ohne scipy (nicht in
    requirements.txt, nirgends sonst im Projekt verwendet - keine neue harte
    Abhaengigkeit fuer einen einzelnen Test).

Reine Diagnose-/Leseinfrastruktur (kein Seiteneffekt, keine Aenderung an
Gates/Prompt/E-Mail) - noch NICHT an GUI/Remote-Seite/E-Mail angebunden;
folgt bei Bedarf separat.

**Verifiziert (Testklasse 2):**
  Betroffene Datei(en): agent/krypto/backward_tracking.py
  Aenderungsklasse: 2
  Testfaelle: Binomialtest-Helper (Grundeigenschaften: Symmetrie, n=0->None,
              korrekte Signifikanz bei starker Abweichung) - PASS
              compute_baseline_vergleich() Hebel (63 synth. Signale, 17,5%
              WR, reproduziert echten Gruppe-A-Fund: Muenzwurf-Vergleich
              signifikant negativ, CRV-Breakeven 33,3% korrekt, Regime-Naiv-
              Vergleich ueber trigger_zweig='trendfolge') - PASS
              compute_baseline_vergleich() Spot (kein CRV-/Regime-Vergleich,
              da kein trigger_zweig-Feld; Kleine-Stichprobe-Hinweis) - PASS
              0 Signale -> None - PASS
              compute_zai_uebereinstimmung_baseline() (3/63, reproduziert
              echten 4,8%-Fund, Zufalls-Baseline 33,3% korrekt) - PASS
              keine Daten -> leeres Dict, kein Crash - PASS
  Echter Lauf gegen Kopie der lokalen Desktop-DB: kein Absturz, sauberer
  Leerfall (Desktop-Bestand aktuell zu klein/veraltet fuer inhaltliche
  Zahlen - siehe project_dev_setup.md, Notebook ist alleinige Produktivinstanz)
  Regressionscheck (Import aller abhaengigen Module): PASS
  Gesamturteil: verifiziert (Stufe 2)

### Stufe 3, Punkt 3 umgesetzt: Regime-Konflikt als Kontext statt gezaehlter Bulletpoint

**Fund:** `compute_risikofaktoren_hebel()` listet Regime-Konflikt/-Ausrichtung
als einen von mehreren gleichberechtigten ▲/▼/●-Bulletpoints in Abschnitt 3
("Konklusion"). Da dieser Faktor in einem anhaltenden Regime fuer praktisch
jedes Signal derselben Richtung vorhanden ist (87% aller Gruppe-A-Faelle),
wirkt eine z.B. "3 rote Warnungen"-Wahrnehmung irrefuehrend, wenn eine davon
kaum Unterscheidungskraft zwischen guten und schlechten Setups liefert.

**Fix (rein anzeigerelevant, keine Gate-/Prompt-Aenderung):** neues optionales
Feld `ist_kontext: bool = False` auf der `Risikofaktor`-Dataclass
(`hebel_risk_gate.py`), gesetzt fuer Regime-Konflikt/-Ausrichtung. Beide
Renderer (`ui/formatting.py::format_risikofaktoren_lines()` fuer GUI,
`scheduler/background.py::_formatiere_risikofaktoren()` fuer E-Mail) zeigen
`ist_kontext=True`-Eintraege zuerst als eigene Kontext-Zeile ("--- ... ---")
ohne ▲/▼/●-Symbol, getrennt von der gezaehlten negativ/neutral/positiv-Liste.
Rueckwaertskompatibel (`.get("ist_kontext", False)`) - aeltere gespeicherte
Signale ohne das Feld rendern identisch wie vorher.

**Verifiziert (Testklasse 2):**
  Betroffene Datei(en): agent/krypto/hebel_risk_gate.py, ui/formatting.py,
                        scheduler/background.py
  Aenderungsklasse: 2
  Testfaelle: Risikofaktor-Dataclass mit korrektem Default - PASS
              compute_risikofaktoren_hebel() markiert Regime-Konflikt (LONG im
              baer-Regime) UND Regime-Ausrichtung (SHORT im baer-Regime)
              korrekt mit ist_kontext=True, alle anderen Faktoren False - PASS
              format_risikofaktoren_lines(): Kontext-Zeile ohne Symbol zuerst,
              kein Duplikat in der Restliste - PASS
              Rueckwaertskompatibilitaet: altes JSON ohne ist_kontext-Feld
              rendert identisch wie vorher - PASS
              Leerfaelle (None/leer/[]) weiterhin robust - PASS
  Regressionscheck (Import aller abhaengigen Module): PASS
  Gesamturteil: verifiziert (Stufe 3, Punkt 3)

### Stufe 3, Punkt 4 umgesetzt: Action-Bias-Korrektur (Regel 27) - echter Live-Test gegen Mistral UND Gemini

**Fund:** externe Recherche (Sycophancy-/Omission-Bias-Literatur, Analysis of
Competing Hypotheses, Premortem-Technik) plus eigener Live-Test bestaetigten:
eine Prompt-Struktur, die IMMER dieselbe aufwendige Begruendung verlangt
(5 top_gruende, key_risks, forecast), egal welche Aktion gewaehlt wird, foerdert
einen Action-Bias zugunsten von Empfehlungen. Live-Test (Mistral, n=5
Wiederholungen auf IDENTISCHEN, bewusst mehrdeutigen Fakten): die
Baseline-Variante empfahl in Szenario 2 (Kontra/Squeeze, Retail-Extrem,
schwache historische Trefferquote 18,2%) in 3 von 5 unabhaengigen Laeufen
ERoeFFNEN - trotz im eigenen `gegenargument` selbst benanntem Regime-Konflikt.
Ein erster kleinerer Test hatte das faelschlich als "einmaligen Zufallstreffer"
missverstanden (temperature=0.2 ist nicht deterministisch) - erst die
Wiederholungsmessung zeigte, dass die Mehrheit der Baseline-Laeufe tatsaechlich
ERoeFFNEN waehlte, kein Rauschen.

**Wichtiger Zwischenfund:** die urspruenglich getestete Kombination aus 3
Bausteinen (A: symmetrische Gruende fuer/gegen, B: bindendes Selbstzweifel-Gate,
C: Premortem-Ueberlegung) widersprach in Baustein B der bestehenden Leitplanke
gegen deterministische Ueberschreibung von `eigene_einschaetzung`/Werturteil
(siehe Fakten_Entscheidungsmappe/Memory feedback_llm_synthese_kein_
deterministischer_override). Direkter Vergleich A+B+C gegen A+C (ohne
bindendes Gate), je n=5 auf 2 Szenarien: **A+C allein erreichte in BEIDEN
Szenarien exakt dieselbe Aktionskorrektur (5/5 HALTEN) wie A+B+C** - der
bindende Zwang war fuer den beobachteten Effekt nicht noetig.

**Fix:** neue Regel 27 in `hebel_analyst.py::SYSTEM_PROMPT` - symmetrische
Gruende-Pflicht (3 staerkste Argumente fuer JEDE Option) + Premortem-Frage
(48h-Scheitern-Ueberlegung, fliesst in `eigene_einschaetzung` ein) + explizite
Gleichwertigkeit von HALTEN (auch bei bestehender Position). BEWUSST ohne
deterministische Nachkorrektur von `action`/`confidence_pct` - Regel 27 enthaelt
eine explizite Abgrenzung zu Regel 26 dazu.

**Verifiziert (Testklasse 1, Prompt-only + echte Live-Tests):**
  Betroffene Datei(en): agent/krypto/hebel_analyst.py
  Aenderungsklasse: 1
  Live-Tests (echte API-Calls, Mistral + Gemini):
    - 3 Basis-Szenarien (mehrdeutig/Regime-Konflikt, Kontra/Squeeze, klar
      regimekonform) je Baseline vs. A+B+C - PASS (kein Uebervorsichts-
      Nebeneffekt bei klar gutem Setup)
    - Erweiterter Test: 5 Szenarien x 2 Provider (Mistral+Gemini) x 2 Varianten
      - kein Fall, in dem die modifizierte Variante ein klar gutes Setup zu
        HALTEN kippte
    - Wiederholungsmessung n=5 je Szenario (Mistral): Baseline zeigt echten
      Action-Bias (Szenario 2: 60% ERoeFFNEN trotz schwacher Fakten),
      A+B+C korrigiert konsistent auf 5/5 HALTEN in beiden Szenarien - PASS
    - A+C-vs-A+B+C-Vergleich (n=5 je Variante je Szenario): identische
      Aktionskorrektur (5/5 HALTEN in beiden Szenarien) OHNE bindendes Gate - PASS
  Prompt-Integritaet: Regelnummerierung fortlaufend 1-27, kein Mojibake,
  Abgrenzung zu Regel 26 explizit im Text - PASS
  Regressionscheck (Import aller abhaengigen Module) - PASS
  Gesamturteil: verifiziert (Stufe 3, Punkt 4) - **Stufe 3 damit vollstaendig
  bearbeitet** (Punkt 1+2 bewusst in Evidenz gehalten/vertagt, Punkt 3+4 umgesetzt)

### Nachtrag (2026-07-29): Z.ai `leite_eigene_richtung()` - Temperature-Fix + Positions-Bias-Fix (Position Swapping)

Anschlussfrage des Nutzers nach Stufe 3 Punkt 4: soll die Action-Bias-Korrektur
auch auf die Z.ai-Prompts (`agent/krypto/gegenpruefung.py`) uebertragen werden?
Ergebnis einer eigenen, breiten Recherche + Live-Tests gegen die echte Z.ai-API
(insgesamt 64 rohe Z.ai-Calls in dieser Runde): der Hebel-spezifische
Action-Bias-Mechanismus (asymmetrische Begruendungstiefe je Aktion) existiert
bei Z.ais `pruefe_konsistenz()`/`leite_eigene_richtung()` strukturell NICHT
(beide liefern ein bereits symmetrisches Output-Schema unabhaengig vom
Urteil) - stattdessen wurden ZWEI unabhaengige, tatsaechlich relevante Funde
gemacht.

**Fund 1 - Temperature 0.2 unnoetig fuer eine Klassifikationsaufgabe:**
`pruefe_konsistenz()`/`leite_eigene_richtung()` sind reine Ja/Nein- bzw.
3-Wege-Klassifikationsaufgaben (kein kreativer Text) - LLM-als-Klassifikator-
Literatur empfiehlt hierfuer `temperature=0.0`. Live bestaetigt (n=8,
identische mehrdeutige Fakten): `temperature=0.2` lieferte 7/8 SHORT + 1/8
NEUTRAL, `temperature=0.0` lieferte 8/8 SHORT - 0.2 fuegte nur zusaetzliches,
rein zufallsbedingtes Sampling-Rauschen hinzu, ohne Nutzen.
**Fix:** beide Funktionen auf `temperature=0.0` umgestellt.

**Fund 2 - echter Positions-Bias in `leite_eigene_richtung()` (deutlich
gewichtiger als Fund 1):** die Reihenfolge der JSON-Schluessel im
Fakten-Dict beeinflusst das Urteil bei mehrdeutigen Fakten erheblich, auch
bei `temperature=0.0` (also KEIN Sampling-Effekt, ein echter, reproduzierbarer
"Recency"-Effekt). Live getestet (2 unabhaengige, spiegelbildliche Szenarien,
je n=6, 3 Positionen des Gegenindikators):

| Position des Gegenindikators | Szenario 1 (bearisch) | Szenario 2 (bullisch) |
|---|---|---|
| Zuerst | 6/6 SHORT | 5/6 LONG, 1/6 NEUTRAL |
| Mitte | 6/6 SHORT | 6/6 LONG |
| Zuletzt | 4/6 NEUTRAL, 2/6 SHORT | 4/6 NEUTRAL, 2/6 LONG |

Steht der Gegenindikator frueh/mittig, wird er fast vollstaendig ignoriert;
steht er ganz am Ende, wird er deutlich staerker gewichtet - deckt sich mit
der "Lost in the Middle"-Literatur (U-foermige Aufmerksamkeitskurve). Eine
Nutzer-Hypothese ("Mitte waere neutraler") wurde damit live widerlegt (Mitte
war sogar am entschiedensten). Da bei einem echten Signal vorher nicht
bekannt ist, welcher Fakt der Ausreisser ist, loest keine feste Reihenfolge
das Problem grundsaetzlich - jede feste Reihenfolge bevorzugt strukturell
den zuletzt genannten Fakt (aktuell `technische_konfluenz`).

**Fix (Position Swapping, etabliertes Gegenmittel aus der LLM-Gutachter-
Literatur):** neue Funktion `leite_eigene_richtung_positionsrobust()` -
ruft `leite_eigene_richtung()` ZWEIMAL auf (Original-Reihenfolge + komplett
umgekehrte Reihenfolge, neuer Helfer `_kehre_objektive_fakten_um()`,
`symbol` bleibt bewusst erster Schluessel). Stimmen beide Urteile ueberein,
wird dieses Urteil verwendet. Weichen sie ab, wird NEUTRAL mit explizitem
Vermerk ("Positions-uneinheitlich") zurueckgegeben, statt eine der beiden
Antworten verdeckt zu bevorzugen. `fuehre_beide_calls_im_hintergrund()`
ruft jetzt diese Funktion statt der einfachen Variante auf - macht insgesamt
**3 statt 2 sequenzielle Z.ai-Calls pro Signal** (`pruefe_konsistenz()` +
2x `leite_eigene_richtung()`). Liefert nach aussen weiterhin GENAU EIN
kombiniertes `eigene_richtung`/`kurzbegruendung`-Ergebnis - am DB-Update
(ein einziges `update_fn`-Callback) und an `backward_tracking.py::
bewerte_zai_richtung()` (liest nur das gespeicherte Endergebnis) aendert
sich dadurch nichts.

**E-Mail-Wartezeit angepasst:** `scheduler/background.py::
_ZAI_EMAIL_WARTE_MAX_SEKUNDEN` von 90s auf 135s erhoeht (proportional
skaliert 90*3/2, da jetzt 3 statt 2 sequenzielle Z.ai-Calls pro Signal
anfallen) - bis genug echte 3-Call-Faelle fuer eine erneute Log-Auswertung
vorliegen (wie schon bei der 60s->90s-Kalibrierung 2026-07-28).

**Verifiziert:**
  Synthetisch (gemockter zai_client, Testklasse 1+2): `_kehre_objektive_
  fakten_um()` (symbol bleibt erst, Rest umgekehrt, Original unveraendert,
  Leerfall, Randfall ohne symbol) - PASS. `leite_eigene_richtung_
  positionsrobust()`: Uebereinstimmung -> diese Richtung - PASS. Abweichung
  -> NEUTRAL mit Vermerk - PASS. Je ein Call schlaegt fehl -> anderes
  Ergebnis verwendet (beide Richtungen) - PASS. Beide fehlgeschlagen ->
  None - PASS. `zai_client=None` -> None ohne Call - PASS. Regression
  `fuehre_beide_calls_im_hintergrund()`: genau EIN DB-Update trotz 3
  Z.ai-Calls (1+2) - PASS. Import-Regressionscheck (gegenpruefung, alle 6
  Pipelines, backward_tracking, scheduler.background) - PASS.
  Live-Bestaetigung (echter Produktionscode inkl. `baue_objektive_
  fakten()`, echte Z.ai-API, 2 Szenarien, je n=3): lief fehlerfrei durch,
  beide Reihenfolgen stimmten in dieser kleinen Stichprobe ueberein (bei
  n=3 statistisch plausibel, kein Widerspruch zum breiteren Befund oben) -
  PASS (Integrationstest, nicht erneute Bias-Messung).

Dokumentiert hier + Memory. Committet als `67571bd`, gepusht.

**Nachtrag (2026-07-29, frischer NB-Export 21:18 Uhr): Konfidenz-Kalibrierung
x CRV/SL-Korrelation - Analyse durchgefuehrt, Ergebnis "noch nicht
entscheidbar" statt eines definitiven Befunds.**

Anlass: Nutzer-Frage, ob die frueher (project_r510_konfidenz_veto_analyse_
29_07.md) gefundene flache/uneinheitliche Konfidenz-Kalibrierung (niedrig
20,6% WR > mittel 14,3% WR trotz hoeherer vorhergesagter Konfidenz) mit den
bereits bekannten CRV-/SL-Abstand-Mustern (Stufe 3 Punkt 1 oben)
zusammenhaengt - diese zwei Untersuchungsstraenge waren bisher nie direkt
gegeneinander korreliert worden.

**Export-Skript-Check (aktiv geprueft, wie vom Nutzer verlangt):**
`extract_notebook_diagnose.py` brauchte KEINE Anpassung - alle noetigen
Felder (`confidence_pct`, `llm_model`, `outcome_status`,
`outcome_max_realisiertes_crv`, `zai_eigene_richtung`, `zai_uebereinstimmung`)
waren bereits vorhanden, keine der heutigen Aenderungen (Regel 27,
Z.ai-Fix) hat neue DB-Spalten eingefuehrt.

**Datenqualitaets-Fund waehrend der Analyse:** `compute_konfidenz_
kalibrierung()` mischt ALLE Provider (Mistral+Groq+Cerebras+Gemini) unter
Tier "hebel" ohne Provider-Filter. Die fruehere "hoch"-Band-Zahl (n=9) war
dadurch verzerrt - 8 von 9 stammen von laengst aus der Kette entfernten
Providern (Groq/Cerebras), nur 1 von Mistral. Eine Mistral-only-
Neuberechnung war deshalb noetig, um wirklich Mistrals eigene Kalibrierung
zu beurteilen (n=63 Mistral-Gruppe-A-Signale, identisch zu
`provider_performance.hebel.mistral.anzahl_resolved`, als Cross-Check
verifiziert).

**Erste Analyse (Pearson-Korrelationen, Mistral-Gruppe-A, n=63):**
Konfidenz vs. CRV r=0,041, Konfidenz vs. SL-Abstand r=-0,070, Konfidenz vs.
Win r=-0,067 - alle nahe Null. Zusaetzlicher Nebenbefund: CRV vs. Win
INNERHALB Gruppe A allein r=+0,117 (schwach POSITIV, anders als das
Gesamt-r=-0,25 aus der gemischten A+B-Population in Stufe 3 Punkt 1) -
deutete zunaechst auf einen Zwischen-Gruppen-Effekt (Schwelleneffekt bei
CRV=2,0) statt eines durchgehenden Dosis-Wirkungs-Zusammenhangs hin.

**Selbstkorrektur nach Signifikanztest (Nutzer-Nachfrage "ist das Thema
abgehakt oder fehlt eine Grundlage?"):** ALLE oben genannten Korrelationen
UND der niedrig-vs-mittel-Bandunterschied sind bei den aktuellen
Stichprobengroessen NICHT signifikant:

| Vergleich | r / Differenz | 95%-CI bzw. z-Test |
|---|---|---|
| Konfidenz vs. CRV | r=0,041 | CI [-0,21, +0,29] |
| Konfidenz vs. SL-Abstand | r=-0,070 | CI [-0,31, +0,18] |
| Konfidenz vs. Win | r=-0,067 | CI [-0,31, +0,18] |
| CRV vs. Win (nur Gruppe A) | r=0,117 | CI [-0,13, +0,36] |
| SL-Abstand vs. Win (nur Gruppe A) | r=0,154 | CI [-0,10, +0,39] |
| niedrig (20,6%) vs. mittel (14,3%) WR | Diff. 6,3 Pkt | z=0,65 (Schwelle 1,96) |

Jedes Konfidenzintervall schliesst Null ein, der z-Test liegt weit unter
der Signifikanzschwelle. **Korrigierte, ehrliche Schlussfolgerung:** bei
n=63 (bzw. n=34/n=28 je Band) ist KEINE der beobachteten Differenzen von
reinem Stichprobenrauschen unterscheidbar - weder die urspruengliche
Annahme "Konfidenz korreliert mit gar nichts" noch der CRV/SL-Gruppe-A-
Nebenbefund. Faustregel-Ueberschlag: um r≈0,15 mit 80%-Power zuverlaessig
zu erkennen, braucht es ca. n≈340; fuer den 6-Prozentpunkte-Bandunterschied
bei ~15-20% Basisrate aehnliche Groessenordnung.

**Konsequenz fuer die Wiedervorlage-Bedingung:** die bisherige n≥50-Schwelle
fuer Stufe 3 Punkt 1 (CRV-Expectancy-Gate, Post-Enge-Stop-Fix) reicht fuer
die KONFIDENZ-Kalibrierungsfrage spezifisch NICHT aus - dafuer braucht es
eine deutlich hoehere Schwelle (Groessenordnung mehrere Hundert aufgeloeste
Mistral-Hebel-Signale), bevor eine belastbare Aussage zur Konfidenz-CRV/SL-
Beziehung moeglich ist. Kein Code-Aenderungsbedarf, reine Analyse-
Erkenntnis. Scratchpad-Analyseskripte (nicht committet):
`analyse_konfidenz_crv_sl_korrelation.py`.

**Nachtrag geprueft und geschlossen (2026-07-29):** ob der bei
`leite_eigene_richtung()` gefundene Positions-Bias auch bei
`pruefe_konsistenz()` existiert, wurde live getestet (2 spiegelbildliche
Szenarien, temperature=0.0, Original- vs. komplett umgekehrte Reihenfolge
der Evidenz-Fakten, je n=6 - `symbol`/`action`/`confidence_pct`/`richtung`
bleiben als Kopf-Felder fix, da sie die zu pruefende Behauptung selbst
sind, keine Evidenz). Bewusst grenzwertiger Begruendungstext: argumentiert
nur ueber RSI/Funding-Rate, OHNE den gegenlaeufigen Trend/Regime-Fakt zu
erwaehnen (reine Auslassung, nicht zu verwechseln mit dem am 26.07. bereits
getesteten Fall, wo der Text den Gegenfakt offen benennt und bewusst
dagegen argumentiert).

**Ergebnis: 24/24 gueltige Antworten (1x transienter Server-500er,
netzwerkbedingt) - ALLE "konsistent", unabhaengig von Szenario UND
Reihenfolge.** Kein Positions-Bias gefunden. Nachvollziehbar: `pruefe_
konsistenz()` prueft nur "widerspricht der Text den Fakten", nicht "waege
mehrere Fakten gegeneinander ab" - eine reine Auslassung eines Gegenfakts
wird laut Prompt-Regel korrekt NICHT als Widerspruch gewertet, unabhaengig
davon, an welcher Position der ausgelassene Fakt in der Liste steht.

**Entscheidung: kein Code-Aenderungsbedarf** - `pruefe_konsistenz()` bleibt
unveraendert (nur der bereits umgesetzte Temperature-Fix 0.2->0.0 gilt
weiterhin). Negativbefund dokumentiert, Punkt abgeschlossen.

### Nachtrag (2026-07-30): Detailverifikation aller heutigen Aenderungen - Gates, Z.ai, E-Mail/GUI, Backtracking Stufe 2

Anlass: Nutzer-Wunsch, nach Neustart der App im Detail zu pruefen, ob Gates,
E-Mail, Backtracking und die uebrigen heutigen Aenderungen (6 geaenderte
Dateien seit `6756601`) tatsaechlich korrekt funktionieren - nicht nur die
Notebook-Datenanalyse allein.

**Teil 1 - Live-Integrationstest gegen eine DB-Kopie (Desktop, echte APIs):**
`data/tradinginfotool.db` in den Scratchpad kopiert, `db.DB_PATH` VOR der
ersten Verbindung ueberschrieben (siehe `feedback_desktop_kein_
produktivstart.md`), `db.init_db()` fuer die Migrationen nachgezogen (reine
Datei-Kopie durchlaeuft den Start-Migrationslauf sonst nicht), frischer
Preis-Snapshot fuer BTC geholt (sonst kurzschliesst das Datenqualitaets-Gate
das Signal vor Erreichen der eigentlichen Testpunkte). Danach echter
Aufruf von `generate_hebel_signal()` mit echten Mistral-/Z.ai-/CoinGecko-
Clients:
- **Gates:** Signal lief komplett durch (`gate_passed=True`). `ist_kontext`
  korrekt NUR bei "Regime-Konflikt" gesetzt, alle 9 uebrigen Risikofaktoren
  korrekt `False`. Stufe-0-Fix griff real: `eigenkapital_deckel_hinweis` =
  "Eigenkapitalbedarf von 3516 EUR auf Richtwert 500 EUR reduziert" mit
  echtem EUR/USD-Kurs.
- **Z.ai:** Hintergrund-Thread lief mit 3 echten Calls (2x Position-Swap +
  1x Konsistenz) durch, schrieb nach 54s GENAU EIN kombiniertes Update
  (`urteil=widerspruch`, `eigene_richtung=SHORT`, `uebereinstimmung=nein`).
- **E-Mail/GUI-Formatierung:** beide Renderer liefern identischen Inhalt -
  Kontext-Zeile zuerst ohne Symbol, danach ▼/●/▲-gruppiert. (Zwei Fehler im
  ersten Testlauf-Versuch waren reine Bugs im eigenen Testskript - falscher
  Rueckgabetyp angenommen -, nicht im Produktivcode.)
- **Backtracking Stufe 2:** `compute_zai_uebereinstimmung_baseline()` lief
  korrekt (n=1, Binomialtest p=1,0). `compute_baseline_vergleich()` gab
  `None` zurueck - korrektes Verhalten bei 0 ausgewerteten Signalen in der
  Desktop-DB-Kopie (nur 8 `hebel_signals`-Zeilen, keine aufgeloest - die
  eigentliche Handelshistorie liegt auf dem Notebook), kein Bug.

**Teil 2 - Frischer Notebook-Export (30.07., 04:38 Uhr) mit echten
Produktionsdaten, unabhaengig von Teil 1:**
- **Z.ai-Positions-Bias-Fix laeuft live:** seit Deploy (erster beobachteter
  Fall 29.07. 18:45 Uhr) zeigen 8 von 25 Eintraegen (32%) den neuen
  "Positions-uneinheitlich"-Fallback auf NEUTRAL - genau das designte
  Verhalten, 0 Ausfaelle (`zai_eigene_richtung=None`). Die durchgehend hohe
  Abweichungsrate (`zai_uebereinstimmung=nein` in allen 25 Faellen seit
  Deploy) ist der bereits bekannte, separate Befund aus dem 27.07.-
  Quickcheck, keine neue Regression.
- **Regel-27-Action-Bias-Korrektur laeuft live:** 29.07. 61/64 Signale (95%)
  HALTEN, 30.07. bisher 7/7 (100%). Konsistent mit der Fix-Absicht
  (uebereifriges ERoeFFNEN bei mehrdeutigen Fakten korrigieren) UND dem
  anhaltenden Baer-Regime-Konflikt auf praktisch jedem Signal - kein
  Hinweis auf einen neuen Bug.
- `ist_kontext` bestaetigt auch hier: "Regime-Konflikt" erscheint korrekt
  als Kontext-Faktor auf allen juengsten echten Notebook-Signalen.
- `auffaelligkeiten: []`, keine neuen Job-Fehler (nur bekanntes
  Hintergrundrauschen: yfinance-/FRED-Timeouts, unabhaengig von heute).

**Ergebnis: alle 6 heute geaenderten Dateien doppelt verifiziert (echter
Desktop-Livetest + echte Notebook-Produktionsdaten), keine Bugs gefunden.**
Kein Code-Aenderungsbedarf. Scratchpad-Testskripte (nicht committet):
`integrationstest_gates_email_backtracking.py`,
`integrationstest_formatierung_nachtrag.py`.

### Nachtrag (2026-07-30): compute_sl_mfe_analyse() - Mehrebenen-Erfolgsmessung

Nutzer-Frage: "wie pruefen wir Erfolgsquoten auf mehreren Ebenen" - Anlass war
eine gezielte Verschneidung bereits vorhandener Felder (`outcome_max_
realisiertes_crv`/MFE, `outcome_mindestziel_erreicht_am`) gegen den strikten
`outcome_status`, OHNE neue Daten zu erheben. Volle Methodik-Begruendung
siehe `Test_und_Verifikationsmethodik.md` Abschnitt 2.6 - hier nur die
Code-Seite.

**Neue Funktion `compute_sl_mfe_analyse(conn, tier, erlaubte_symbole=None)`**
(`agent/krypto/backward_tracking.py`, direkt nach den Stufe-2-Baseline-
Funktionen): fuer alle Signale mit `outcome_status == stop_loss_erreicht`,
welcher Anteil zeigt trotzdem einen positiven MFE-Wert (Kurs lief
zwischenzeitlich profitabel, bevor er zurueckdrehte und den Stop ausloeste)?
Trennt damit "Richtung war falsch" von "Richtung war richtig, aber zu eng
gestoppt" - zwei Fehlerbilder, die eine reine Win/Loss-Quote vermischt.

Rueckgabe: `anzahl_sl_gesamt`, `anzahl_mit_mfe_daten`, `anzahl_mit_positivem_
mfe`/`quote_positiver_mfe_trotz_stop_pct` (Kern-Kennzahl), `anzahl_
mindestziel_vor_stop_erreicht` (strengere Teilmenge), `anzahl_distinkte_
symbole_bei_positivem_mfe`/`haeufigstes_symbol_anteil_pct` (Symbol-
Konzentrations-Check, Test_und_Verifikationsmethodik.md 2.5 - IMMER mit
ausgewiesen, da diese Funktion typischerweise auf kleinen Stichproben
laeuft), `hinweis` (Kleine-Stichprobe- + Konzentrations-Warnung). `None` bei
0 Stop-Loss-Faellen.

**Erster Blick auf echte Daten (30.07., frischer NB-Export, Hebel):** von 57
SL-Faellen haben 23 MFE-Daten, davon 20 (87%) mit positivem MFE - 9 davon
erreichten sogar das Mindestziel vor dem Stop. Bestaetigt aus einem neuen
Blickwinkel den bereits behobenen Enge-Stop-Loss-Befund vom 28.07. (siehe
[[project_enge_stop_loss_backtest_und_massnahmen]]). Konzentrations-Hinweis:
SUI stellt 3 der 9 Mindestziel-Faelle (33%) - ueber der 20-25%-Schwelle,
im Hinterkopf behalten.

**Verifiziert (synthetisch, Testklasse 1):** T1 gemischte Faelle (positiver/
negativer/fehlender MFE, Mindestziel-Fall, ein Nicht-SL-Fall der nicht
mitzaehlt) - alle Kennzahlen korrekt berechnet - PASS. T2 leerer Datensatz
(0 SL-Faelle) -> `None` - PASS. T3 Konzentrations-Warnung greift korrekt bei
einem dominanten Symbol - PASS. T4 `erlaubte_symbole`-Filter - PASS. T5
`tier="spot"` liest korrekt die `signals`-Tabelle statt `hebel_signals` -
PASS. Zusaetzlich gegen eine echte DB-Kopie ausgefuehrt (0 SL-Faelle dort,
da die Desktop-DB-Kopie kaum aufgeloeste Hebel-Signale hat - korrektes
`None`-Verhalten bestaetigt, keine Diskrepanz zu den echten Notebook-Zahlen,
die aus einer physisch anderen Datenbank stammen).

Dokumentiert in `Basisinfos/Regelwerksmanual.md`/`.docx` +
`Test_und_Verifikationsmethodik.md`/`.docx`. Reine Lesefunktion, noch nicht
an GUI/Remote-Seite/E-Mail angebunden (wie bei den Stufe-2-Baseline-
Funktionen) - Anbindung kann bei Bedarf separat erfolgen.

## Nachtrag (2026-07-30): Multi-Asset-Batch-Nachhol-Mechanismus (fehlende Hedge-/Aktien-/Rohstoff-/Themen-ETF-Signale)

**Auslöser:** Nutzer berichtete, seit ~2 Tagen nur noch Krypto-Hebel-Signale
und einen einzigen Marktscan-Kaufkandidaten erhalten zu haben - keine
Hedge- (Absicherungspositionen DBPK/3QSS), Aktien-, Rohstoff- oder
Themen-ETF-Signale. Analyse gegen den frischen Notebook-Export (30.07.,
05:51 Uhr) zeigte den Root Cause: `multi_asset_batch_job()` (deckt genau
diese vier Assetklassen ab) läuft nur 2x/Tag (`cron[mon-fri, hour='9,19']`,
siehe `MULTI_ASSET_BATCH_CRON_HOURS`), OHNE Nachhol-Mechanismus - anders als
`backward_tracking_job()`, der genau dafür bereits am 2026-07-17 einen Fix
bekam (`backward_tracking_catchup_if_missed()`).

**Konkreter Befund (Log-/DB-Auswertung):**
- Die App startete während intensiver Entwicklungsarbeit auffällig oft neu
  (11x am 27.07., 11x am 28.07., 4x am 29.07. - laut Nutzer der
  Entwicklungsarbeit geschuldet, kein unbekanntes Problem).
- 28.07. 19:00-Termin: komplett ausgefallen, kein einziger Log-Eintrag.
- 29.07. 09:00-Termin: durch einen Neustart mitten im Lauf abgebrochen -
  8 von 9 Symbolen (VST, OD7N, VVMX, 3QSS, DBPK, X136, EXH3, CEBS) liefen
  noch durch (DBPK sogar mit einem echten VERKAUFEN-Signal), PLTR (Aktien)
  wurde nie erreicht.
- 29.07. 19:00-Termin: ebenfalls komplett ausgefallen.
- Die häufiger getakteten Krypto-Jobs (15-Min-Intervall) bemerken einen
  kurzen Ausfall praktisch nie - das schmale 2x/Tag-Fenster des Multi-Asset-
  Batches dagegen verliert bei jedem Treffer einen ganzen Termin ersatzlos.

**Fix (analog zum bestehenden Backward-Tracking-Muster):**
- `database/db.py`: neue Funktionen `get_multi_asset_batch_last_run_iso()`/
  `set_multi_asset_batch_last_run_iso()` (nutzen die bestehende `meta`-
  Tabelle, kein neues Schema/keine Migration nötig) - voller ISO-Zeitstempel
  statt nur Datum, da zwei Termine pro Tag existieren.
- `scheduler/background.py::multi_asset_batch_job()`: setzt den Zeitstempel
  erst NACH erfolgreichem Abschluss von `run_multi_asset_batch()` - bricht
  der Prozess vorher ab (wie am 29.07. real passiert), bleibt der alte Wert
  stehen und der nächste Start holt den Termin nach.
- Neue Helferfunktion `_letzter_faelliger_multi_asset_termin(now)`: ermittelt
  rein per Datumsarithmetik den letzten bereits erreichten Mo-Fr-9/19-Slot
  (geht bei Bedarf mehrere Tage zurück, überspringt Wochenenden korrekt).
- Neue Funktion `multi_asset_batch_catchup_if_missed()`: vergleicht beim
  App-Start den letzten fälligen Termin gegen den zuletzt erfolgreich
  abgeschlossenen Lauf - nur bei einem GENUIN verpassten Termin wird
  `multi_asset_batch_job()` sofort synchron nachgeholt. Bewusst KEIN
  `next_run_time=jetzt` am Job selbst (das würde bei JEDEM Neustart
  außerhalb der Handelszeiten feuern, siehe bestehender Kommentar an der
  `add_job()`-Stelle) - der Nachhol-Check greift gezielt nur bei einem
  tatsächlich verpassten Slot.
- Aufruf in `build_scheduler()` direkt neben dem bestehenden
  `backward_tracking_catchup_if_missed()`-Aufruf verdrahtet.

**Verifiziert (synthetisch, Testklasse 2):** T1-T4
`_letzter_faelliger_multi_asset_termin()` - Montag vormittags/abends,
Rückfall über Montag-früh auf Freitag-abend, Samstag auf Freitag-abend -
alle PASS. T5 DB-Roundtrip (get vor jedem Set → `None`, set/get, Überschreiben
via ON CONFLICT) - PASS. T6 Regressionsfall (letzter Lauf bereits nach dem
fälligen Termin → kein Nachhol-Lauf) - PASS. T7 Positivfall (28.07.-19:00-
Termin verpasst → Nachhol-Lauf wird ausgelöst) - PASS. T8 Grenzfall (nie
gelaufen, `None` → Nachhol-Lauf wird ausgelöst) - PASS. T9 Kombinationsfall
(kaputter ISO-Zeitstempel in der DB → kein Crash, Nachhol-Lauf wird
trotzdem ausgelöst) - PASS. Zusätzlich: Compile-/Import-Regressionscheck
beider geänderter Module + End-to-End-Smoke-Test von `build_scheduler()`
mit dem neuen Aufruf verdrahtet - kein Fehler, 13 Jobs korrekt registriert.

**Separat abgegrenzt (Nutzer-Nachfrage zum Screener):** der Aktien-/ETF-
Screener (`ui/screener_view.py`) ist bewusst ein rein GUI-lokaler
`.after()`-Timer, KEIN Scheduler-Job - er persistiert nichts in die DB und
verschickt keine E-Mails (siehe Modul-Docstring dort, Entscheidung vom
2026-07-20) - das ist so gewollt und kein Fehler in der aktuellen
Funktionsweise. **Aber (siehe Nachtrag direkt im Anschluss):** die vom
Nutzer vermutete GRÖSSERE Lücke - fehlende Schwerpunkte-gesteuerte
Kandidaten-Empfehlung/Benachrichtigung - ist real und jetzt als geplante
Erweiterung dokumentiert.

Dokumentiert in `Basisinfos/Regelwerksmanual.md`/`.docx`. Committet+gepusht
ausständig.

## Nachtrag (2026-07-30): Screener × Schwerpunkte — geplante, noch nicht umgesetzte Kandidaten-Benachrichtigung (echter Gap, kein Bug)

**Auslöser:** Nutzer widersprach der obigen "kein Bug, reines Design"-
Einordnung: er habe mehrfach angemerkt, dass der Screener NICHT dauerhaft
rein GUI-only bleiben soll, sondern ähnlich zur Marktscan-Funktion
Benachrichtigungen/Signale liefern muss - konkret: die aussichtsreichsten
NEUEN Kandidaten sollen selektiv je nach aktivem Schwerpunkt (z.B. KI,
Rohstoffe) empfohlen bzw. per E-Mail übermittelt werden, wahlweise manuell
override oder automatisch anhand der aktiven Schwerpunkte.

**Nachrecherche (schriftliche Historie, nicht nur Erinnerung):** kein
Beleg für einen bereits DISKUTIERTEN, dann liegengelassenen Plan (Regel-
werksmanual/Fakten-Entscheidungsmappe/Memory enthalten dazu nichts) -
ABER ein klar erkennbarer STRUKTURELLER Vorläufer seit dem allerersten
Screener-Konzepttag:

- **2026-07-19, "Lücke 7" (Schwerpunkte-Konzeptrunde, derselbe Tag wie der
  Screener-Erstbau):** *"Synergie mit dem Screener (`scan_etf_candidates()`
  taggt Kandidaten schon heute mit Hauptgruppe/Unterkategorie, Release 1)
  noch nicht genutzt - Kandidaten aus Kategorien mit aktiver, aber in der
  Watchlist noch nicht vertretener These könnten hervorgehoben werden."*
  Diese Lücke wurde SEITHER ZWEIMAL angegangen, aber beide Male bewusst nur
  PASSIV geschlossen:
  - **2026-07-20 (#343):** Treffer-vor-Nicht-Treffer-Sortierung im
    Screener-Tab (Stufe 1, reine GUI-Priorisierung).
  - **2026-07-25 (#442, `_kategorie_score_bonus()`):** zusätzlicher
    Score-Bonus/-Malus als sekundärer Sortierschlüssel, weiterhin NUR
    GUI-Sortierung, keine Benachrichtigung.
- Der einzige echte E-Mail-Mechanismus im gesamten Schwerpunkte-System
  (`_notify_schneller_wechsel()`, #440, 2026-07-25) hat einen komplett
  ANDEREN Auslöser: warnt bei einem akuten Regime-Umschwung einer
  BESTEHENDEN These, nicht bei neu entdeckten Screener-Kandidaten.

**Einordnung:** ein echter, plausibler Gap - die Verbindung zwischen
Schwerpunkte (existiert seit 07-19/07-24) und Screener-Kandidaten-Entdeckung
war von Anfang an naheliegend und wurde zweimal aufgegriffen, aber beide
Male nur bis zur GUI-Sortierung zu Ende gedacht, nie bis zur aktiven
Benachrichtigung. Es ist aber KEINE bereits spezifizierte, dann abgebrochene
Umsetzung - die konkrete Ausgestaltung (Trigger-Schwelle, manuell vs.
automatisch je Schwerpunkt, Cooldown, E-Mail-Format) wurde nie im Detail
besprochen und muss vor einer Umsetzung erst geklärt werden.

**Status: bewusst nur als geplante Erweiterung dokumentiert, NICHT jetzt
umgesetzt** (Nutzer-Wunsch: erst sauber verankern, damit das Thema nicht
wiederholt unklar wieder auftaucht - Umsetzung folgt als eigener,
separater Schritt nach weiterer Detailklärung). Siehe Memory
[[project_screener_schwerpunkte_benachrichtigung_gap]] für die volle
Herleitung und als Anlaufstelle für die künftige Umsetzungsdiskussion.

**Nachtrag (2026-07-30, weitere Planungsrunde): vages Grundgerüst erarbeitet.**
Kein Neubau - alle Bausteine nutzen bereits vorhandenen Code: (1) keine
LLM-Bewertung an der Entdeckungsstelle (wie bei Krypto-Marktscan, rein
deterministisch); (2) Bitpanda-Pflicht wird von reinem Anzeige-Flag zu
echtem Ausschlussfilter (wiederverwendet `is_listed()`, mit globalem
Ein/Aus-Schalter analog Hebel-Prüfung-Toggle); (3) Qualitäts-Vorfilter über
die bereits vorhandenen, bisher für Screener-Kandidaten ungenutzten
`fetch_fundamentals()` (Aktien) und `api/asset_quality.py::get_asset_
quality()` (ETF mit echtem Yahoo-Ticker); (4) Klassifikation +
wiederkehrende Benachrichtigung analog `_notify_marktscan_kaufkandidaten()`,
aber bewusst OHNE automatische Watchlist-Aufnahme - der Nutzer entscheidet
weiterhin manuell. Grund für Punkt 4: ein frischer 13-Tage-Export (30.07.)
zeigt 0 von 80 Signalen mit einer Aktion außer HALTEN für Aktien/Rohstoffe/
Themen-ETF (LLM real aufgerufen, keine Gate-Blockade) - automatische
Watchlist-Aufnahme würde aktuell vor allem HALTEN-Rauschen erzeugen. Die
Takt-Frage (2x/Tag-Cron erhöhen?) bleibt deshalb bewusst ABHÄNGIG von der
separaten, breiteren LLM-Optimierungs-Abdeckungsprüfung (siehe eigener
Nachtrag) - nicht isoliert entschieden.

## Nachtrag (2026-07-30): Regime-Konflikt/-Ausrichtung für die Spot-Familie nachgerüstet (Punkt B der LLM-Optimierungs-Abdeckungsprüfung)

**Auslöser:** breite Prüfung, wo die gestrigen (29.07.) LLM-Qualitäts-Fixes je
Assetklasse bereits greifen und wo nicht. Ergebnis für Punkt B: der
Regime-Konflikt/-Ausrichtung-Risikofaktor (Hebel: `hebel_risk_gate.py`,
Regelwerk-Audit Stufe 3 Punkt 3, 2026-07-29) existierte für die Spot-Familie
(Krypto-Spot/Aktien/Rohstoffe/Themen-ETF) überhaupt nicht - die alte
`compute_risikofaktoren()`-Docstring-Behauptung *"kein eigenes
Regime-Konflikt bei Spot"* war falsch. RM-10/-11 (Hebel-Deckel) sind
tatsächlich hebel-spezifisch, aber die reine ANZEIGE eines
Regime-Konflikts/einer -Ausrichtung fehlte schlicht, obwohl `regime_result`
für alle 4 Pipelines längst als Pflichtparameter durch `post_check()` läuft.

**Fix (`agent/krypto/risk_gate.py`):** neue Funktion `regime_konflikt(regime,
richtung)` - asset-neutrales Pendant zu `hebel_risk_gate.py::
regime_konflikt_hebel()` (bewusst eigene Kopie statt Import, wie beim
gesamten Modul üblich - Zirkelbezug-Vermeidung). `Risikofaktor` bekam das
bereits bei Hebel bestehende Feld `ist_kontext: bool = False`.
`compute_risikofaktoren()` bekam zwei neue optionale Parameter (`regime`,
`regime_persistenz_tage`) und berechnet daraus - NUR innerhalb des
bestehenden BUY-only-Blocks (`action not in _BUY_ACTIONS: return`, eine
bewusste, bereits vorher bestehende Design-Grenze der Funktion, siehe
dortiger Kommentar zur Kauf-Idee-Fokussierung - unverändert gelassen, keine
Ausweitung auf VERKAUFEN/TAUSCHEN in dieser Runde) - denselben
Regime-Konflikt/-Ausrichtung-Faktor wie bei Hebel, `ist_kontext=True`. Kein
BTC-Relativwert-Dämpfungstext wie bei Hebel (asset-übergreifend nicht
sinnvoll, betrifft nur Krypto-Alt-Coins gegen BTC).

**Wiring:** keine Änderung an den 4 Pipeline-Dateien nötig - `regime_result`
war in `post_check()` bereits ein Pflichtparameter für Krypto-Spot/Aktien/
Rohstoffe/Themen-ETF, der neue Faktor aktiviert sich also automatisch für
alle 4 gleichzeitig. Hedge bewusst NICHT betroffen (nutzt `risk_gate.py::
post_check()` gar nicht, hat eine eigenständige, spiegelverkehrte
Deckel-Logik in `agent/hedge/pipeline.py` - eine automatische Aktivierung
hätte dort wegen der invertierten Hedge-Semantik falsche Ergebnisse
geliefert). `regime_persistenz_tage` bleibt vorerst auf dem Default `None`
(reine Text-Anreicherung, kein Pipeline-Wiring in dieser Runde - optional
nachrüstbar wie bei `hebel_pipeline.py`). Anzeige (App-Detail-Panel +
E-Mail) brauchte KEINE Änderung - `ui/formatting.py::
format_risikofaktoren_lines()` und `scheduler/background.py::
_formatiere_risikofaktoren()` lesen `ist_kontext` bereits generisch aus dem
JSON, unabhängig davon, welche Pipeline den Eintrag erzeugt hat.

**Verifiziert (synthetisch):** `regime_konflikt()` alle 4 Kombinationen
bulle/baer × LONG/SHORT plus None-Fälle. `compute_risikofaktoren()`: KAUFEN
im Bär-Regime → Regime-Konflikt/negativ/`ist_kontext=True`; KAUFEN im
Bulle-Regime → Regime-Ausrichtung/positiv; `regime=None` → kein Faktor, kein
Crash (Rückwärtskompatibilität); VERKAUFEN → weiterhin kein Faktor
(bestätigt die unveränderte BUY-only-Grenze); Persistenz-Text wird korrekt
angehängt. End-to-End über `post_check()` mit echtem `RiskPreCheckResult`/
`regime_result`-Mock: Regime-Konflikt UND Regime-Ausrichtung korrekt im
`_risikofaktoren`-Dict inkl. `ist_kontext`-Feld, alle anderen Faktoren
weiterhin mit `ist_kontext=False`. Import-Regressionscheck aller 5
betroffenen Module (risk_gate.py + 4 Pipelines) plus Hedge zur Kontrolle -
keine Fehler.

## Nachtrag (2026-07-30): R-5.10-Konfidenzschwelle - Live-Test, Backtest-Infrastruktur, Korrektur

**Auslöser:** die Live-Test-Untersuchung zu Punkt C (siehe oben, Regime-Konflikt-Nachtrag)
zeigte KEINEN Inaktivitäts-Bias auf LLM-Ebene für Aktien/Rohstoffe/Themen-ETF - beide
Provider (Mistral, Gemini) empfehlen bei eindeutiger Lage zuverlässig KAUFEN/VERKAUFEN.
Die echte Ursache des 0/80-Befunds lag stattdessen im deterministischen R-5.10-
Konfidenzschwellen-Veto (`config.yaml::regime.profile.<regime>.min_konfidenz_prozent`,
laut dortigem Kommentar "Alle Werte VORLAEUFIG" - nie durch einen Backtest kalibriert):
238+ Fälle von `"Konfidenz X% unter Regime-Mindestschwelle Y% (R-5.10)"` im Notebook-
Export, die eigenen Live-Test-Konfidenzwerte (70-85%) lagen genau in diesem kritischen
Band.

**Neue Infrastruktur (bleibt bestehen):** `agent/krypto/backward_tracking.py::
compute_veto_shadow_performance_nach_grund()` - wie die bestehende `compute_veto_shadow_
performance()`, aber nach (Assetklasse, Veto-GRUND: Konfidenzschwelle/CRV/Sonstige) statt
(Assetklasse, Provider) gruppiert, damit künftige Schwellen-Entscheidungen ohne Ad-hoc-
Analyse möglich sind. `agent/krypto/risk_gate.py::post_check()` bekam einen neuen
optionalen Parameter `min_konfidenz_override_prozent` - ersetzt, wenn gesetzt, den
Regime-Profil-Wert für BEIDE Verwendungen (harter Veto + Konfidenz-skalierte
Positionsgrößen-Obergrenze). Export (`extract_notebook_diagnose.py`) und Remote-Status-
Seite (neue Karte "Veto-Schatten-Performance nach Veto-Grund") wurden entsprechend
erweitert.

**Erste Auswertung (Krypto-Spot, Konfidenzschwellen-Vetos): n=106 aufgelöst, Win-Rate
41,5%, Ø realisiertes CRV +0,222** - auf den ersten Blick eine belastbare Stichprobe
(>= 50, siehe Test_und_Verifikationsmethodik.md) mit leicht positivem Ergebnis. Ein
`min_konfidenz_prozent_krypto_spot_override` (-5 Prozentpunkte je Regime) wurde daraufhin
kurzzeitig in `config.yaml` eingeführt und live verdrahtet.

**KORREKTUR (gleicher Tag):** der verbindliche Symbol-Konzentrations-Check (Abschnitt 2.5
der Test_und_Verifikationsmethodik.md - genau für diese Art Befund eingeführt, nach einem
fast identischen Fall am 29.07.) wurde nachträglich auf diesen Befund angewendet und
NICHT bestanden: die Top-5-Symbole (AKT, CAT, GRIFFAIN, KAITO, S) stellen 39,6% der
Fälle; ohne sie fällt die Win-Rate auf 32,8% und das Ø realisierte CRV **kippt im
Vorzeichen** auf -0,242 - laut Methodik-Dokument explizit disqualifizierend ("Vorzeichen-
wechsel beim CRV" ist eine der beiden harten Ausschlusskriterien). Der Override wurde
noch am selben Tag aus `config.yaml` zurückgenommen. Der `min_konfidenz_override_
prozent`-Mechanismus in `risk_gate.py` bleibt als generische, ungenutzte Infrastruktur
bestehen (behauptet nichts Falsches) - eine spätere, belastbarere Wiedervorlage kann die
Config-Sektion einfach neu befüllen, ohne Code-Änderung.

**Zusätzlich klargestellt (Nutzer-Nachfrage):** auch die zweite Teilauswertung (Krypto-
Spot, CRV<2,0-Vetos: n=18, Win-Rate 33,3%, Ø CRV -0,137, ursprünglich als "Veto arbeitet
korrekt" eingeordnet) ist NICHT belastbar - n=18 liegt unter der n>=50-Mindestschwelle,
unabhängig von der Konzentration (hier gut verteilt, größtes Symbol nur 11%). Beide
Krypto-Spot-Fragen (Konfidenzschwelle UND CRV-Schwelle) bleiben damit echt OFFEN, nicht
bestätigt - als Wiedervorlage vermerkt (siehe Memory-Referenzliste). Aktien/Rohstoffe/
Themen-ETF hatten ohnehin nie eine ausreichende Stichprobe (n=4 bzw. n=0).

Dokumentiert in `Basisinfos/Regelwerksmanual.md`/`.docx` +
`Basisinfos/Test_und_Verifikationsmethodik.md` (neuer Fallbeispiel-Eintrag zu Abschnitt
2.5) + Memory. Noch NICHT committet/gepusht.

## Nachtrag (2026-08-01): R-5.10-Konfidenzschwelle erneut geprüft bei größerer Stichprobe (n=148) - Vorzeichenwechsel bleibt bestehen

Im Rahmen einer allgemeinen "Detailanalyse aller Messpunkte" gegen einen frischen
Notebook-Export lag die R-5.10-Konfidenzschwellen-Veto-Schatten-Auswertung (Krypto-Spot)
diesmal bei n=148 (statt n=106 beim 30.07.-Fund) mit Ø realisiertem CRV +0,334 - erneut
auf den ersten Blick eine belastbare, jetzt noch größere Bestätigung.

Der Symbol-Konzentrations-Check (Abschnitt 2.5 der Test_und_Verifikationsmethodik.md)
wurde diesmal VOR der Interpretation angewendet (direkt aus den rohen `spot_signals`-
Exportdaten, gefiltert auf `risk_veto_reason` enthält "R-5.10" UND Symbol in der
Krypto-Watchlist): die prozentuale Verteilung ist tatsächlich breiter als beim
30.07.-Fund (22 Symbole, größter Anteil nur 8,1% statt der damaligen 39,6%-Top-5-
Häufung). Der Vorzeichenwechsel bleibt trotzdem bestehen, ausgelöst durch ein einzelnes
Symbol statt einer Gruppe: AIOZ allein (n=12, 8% der Fälle, 100% Take-Profit-Quote, Ø
CRV +4,71) trägt den gesamten positiven Gesamtdurchschnitt. Ohne AIOZ fällt n=136 auf
Ø CRV **-0,052** - Vorzeichenwechsel, identisch disqualifizierend wie beim 30.07.-Fund.
Zusätzlich: von allen 148 Einzel-Outcomes sind 91 (61,5%) negativ, nur 57 (38,5%)
positiv - der positive Mittelwert ist eine Ausreißer-getriebene Verzerrung, kein
Mehrheitsmuster.

**Lehre (siehe Test_und_Verifikationsmethodik.md 2.5.4):** eine breitere prozentuale
Verteilung allein reicht nicht, um den Konzentrations-Check als bestanden zu werten -
ein einzelner Ausreißer mit extremem CRV kann denselben Effekt auslösen wie eine
Gruppen-Häufung. Die 30.07. getroffene Entscheidung, den Krypto-Spot-R-5.10-Override
NICHT zu setzen, bleibt bei 1,4x größerer Stichprobe bestätigt - keine Revision nötig,
kein Code-Change.

## Nachtrag (2026-07-30): BUGFIX - Z.ai-Gegenprüfung fehlte in allen Multi-Asset-Batch-E-Mails

**Auslöser:** Nutzer-Fund an einem echten, bereits versendeten Produktions-Signal (3QSS
NACHKAUFEN, Hedge, 30.07. 09:05) - die E-Mail enthielt keinerlei Z.ai-Abschnitt, obwohl
die Z.ai-Ausweitung auf alle 6 Signal-Pipelines (siehe Nachtrag oben, "Z.ai-Gegenprüfung
auf alle 6 Signal-Pipelines ausweiten") bereits am 27.07. abgeschlossen wurde.

**Root Cause:** die Z.ai-Daten waren für dieses Signal korrekt in der DB vorhanden
(`zai_eigene_richtung=SHORT`, `zai_uebereinstimmung=ja`, `zai_gegenpruefung_urteil=
konsistent`, inkl. Kurzbegründungstext) - das Problem lag ausschließlich in
`scheduler/background.py::_notify_multi_asset_signal()` (die E-Mail-Funktion für ALLE
VIER Multi-Asset-Batch-Pipelines: Aktien/Rohstoffe/Themen-ETF/Hedge, nicht nur Hedge):
diese Funktion rief `_formatiere_zai_gegenpruefung(signal)` nie auf und fügte den Text
nie in den E-Mail-Body ein - anders als `_notify_spot_signal()` (Krypto-Spot) und
`_notify_hebel_signal()` (Hebel), die das von Anfang an korrekt tun. Die Plumbing-Seite
(Commits 1-10 der Z.ai-Ausweitung) war vollständig korrekt - inklusive Re-Fetch der
frischen Z.ai-Felder aus der DB vor dem E-Mail-Versand - nur der finale
Text-Rendering-Schritt in der E-Mail-Vorlage selbst fehlte.

**Fix:** in `_notify_multi_asset_signal()` (Zeile ~1833) `zai_text =
_formatiere_zai_gegenpruefung(signal)` ergänzt und ans Ende des Body-Strings angehängt
(`+ (f"\n\n{zai_text}" if zai_text else "")`) - exakt analog zu `_notify_spot_signal()`.
Bei derselben Gelegenheit fiel eine zweite, kleinere Inkonsistenz auf: die
"Regime: ..."-Zeile am Kopf der E-Mail existierte ebenfalls nur bei Spot/Hebel, nicht bei
Multi-Asset-Batch - `signal.regime` wird aber in allen 4 Pipelines korrekt befüllt
(verifiziert per Grep), daher ebenfalls ergänzt.

**Verifikation:** `py_compile` nach beiden Änderungen fehlerfrei; synthetischer Test mit
einem Mock-Signal-Objekt (Felder analog dem echten 3QSS-Fall) bestätigt, dass
`_formatiere_zai_gegenpruefung()` einen nicht-leeren Text liefert. Ein echter
Notebook-Lauf (nächstes reales Aktien/Rohstoffe/Themen-ETF/Hedge-Signal) steht noch aus,
um die End-to-End-E-Mail zu bestätigen.

**Betroffener Zeitraum:** alle Multi-Asset-Batch-E-Mails seit der Z.ai-Ausweitung
(27.07.) bis zu diesem Fix (30.07.) hatten keinen Z.ai-Abschnitt - reiner
Anzeige-/Text-Bug, keine Daten gingen verloren (in der DB waren die Felder immer
korrekt befüllt).

**Zweiter, verwandter Fund bei derselben Gelegenheit:** `ui/signals_view.py` (Detail-
Panel im App-Signale-Tab, verwendet für Krypto-Spot UND alle 4 Multi-Asset-Pipelines)
übergab an `format_zai_gegenpruefung_lines()` für die drei Richtungs-Abgleich-Parameter
fest `None, None, None`, mit dem veralteten Kommentar "Signal/Spot hat kein
richtung-Feld" - dieser Kommentar stammte aus der Zeit VOR der Z.ai-Ausweitung
(27.07., Commit 1 erweiterte die `Signal`-Dataclass genau um diese 3 Felder) und wurde
danach nie aktualisiert. Ergebnis: der Konsistenz-Check wurde im App-Detailpanel korrekt
angezeigt, der Richtungs-Abgleich dagegen NIE - weder für Spot noch für die 4
Multi-Asset-Pipelines. Fix: die drei `signal.zai_*`-Felder werden jetzt tatsächlich
durchgereicht (Zeile ~560-564).

## Nachtrag (2026-07-30): Marktscan-Reifegrad-Scoring + Erfolgsmessung

Zwei zusammengehörige Bausteine, in einer Runde gebaut und hier gemeinsam dokumentiert
(Teil 1 zeitlich zuerst umgesetzt, aber gemeinsam mit Teil 2 committet).

### Teil 1: Reifegrad-Scoring (Streak-Malus + ATH-Malus)

Ausgangspunkt war die Frage, ob `score_kaufkandidat_ab=70`/`score_watchlist_wuerdig_ab=50`
(beide VORLAEUFIG) gut kalibriert sind. Ein Vorab-Backtest gegen echte Notebook-Daten
zeigte: die Konzentration weniger, wiederholt entdeckter Coins macht eine klassische
Schwellen-Kalibrierung unzuverlässig (Symbol-Konzentrations-Check schlägt fehl, siehe
Test_und_Verifikationsmethodik.md Abschnitt 2.5) - ABER dieselbe Wiederholung ist ein
bisher ungenutztes Signal: je öfter ein Coin schon als Kandidat gesichtet wurde
("Streak"), desto schlechter die anschließende Kursentwicklung. Per Backtest bestätigt
(70 Coins mit ≥4 Tages-Sichtungen, Tages-Kollabierung um den Launch-Tag-Burst vom
09.07. nicht zu verfälschen): Win-Rate fällt sauber von 57% (3. Sichtung) über 49%
(4.) auf 36% (5.), ohne Symbol-Konzentrations-Problem.

Zusätzlich, auf Nutzer-Domainwissen basierend (nicht per eigenem Backtest bestätigt):
der ATH-Abstand eines Coins kann ein "Potential ausgeschöpft"-Signal sein.
**Korrektur einer eigenen Fehleinschätzung während der Diskussion:** ursprünglich
formuliert als "ATH-Abstand ist bei alten Coins bedeutungslos" (Beleg: DigiByte,
-97,8% ATH-Abstand, ohne erkennbare Aussagekraft) - der Nutzer korrigierte das: die
ATH-Thematik ist besonders bei JUNGEN Altcoins ausgeprägt (Erstpump-Zyklus), aber auch
bei reifen, weiterhin aktiv gehandelten Projekten kann sie bedeutsam sein (Beispiel
XRP: ATH Januar 2018, seither über Jahre weit darunter, eine real diskutierte
Marktfrage). Die daraufhin eingeführte 180-Tage-Alters-Schwelle ist deshalb eine
bewusste, PRAKTISCHE Scope-Entscheidung nur für die Marktscan-Zielgruppe (Top-Gainer/
Trending sind so gut wie immer kleine/junge Pump-Coins, große reife Projekte tauchen
dort kaum auf) - keine allgemeingültige Aussage über ATH-Abstand bei alten Coins im
Allgemeinen. Der DigiByte-Fall bleibt ein Beispiel für ein Legacy-Projekt ohne aktuelle
Relevanz, nicht ein Beleg für "alt = bedeutungslos".

**Umsetzung** (`agent/krypto/marktscan.py::score_momentum()`): zwei neue optionale
Parameter, `sichtung_position` (Anzahl distinkter Kalendertage bisheriger Sichtungen +
1, aus `database/db.py::get_marktscan_sichtung_position()`) und `ath_change_pct`
(`api/coingecko.py::get_coin_ath_change_percentage()`, `/coins/{id}`-Endpunkt). Zwei
neue Abzüge:
- **Streak-Malus**: ab Sichtung 3, `-5 Punkte je Stufe`, gedeckelt bei `-20`
  (`_STREAK_MALUS_PRO_STUFE=5.0`, `_STREAK_MALUS_MAX=20.0`).
- **ATH-Malus**: `clamp(ath_change_pct - (-30), 0, 20)` - ausgelaufen ab -30% Abstand,
  gedeckelt bei `-20` (`_ATH_MALUS_MAX=20.0`, `_ATH_ABSTAND_MALUS_SCHWELLE=-30.0`).
  Der ATH-Abruf erfolgt in `run_scan()` NUR für Stufe-A-bestandene Coins innerhalb der
  Altersschwelle (`config.yaml marktscan.filter.ath_abstand_junger_coin_max_alter_tage`,
  180 Tage) - deutlich schwererer Call als der übrige Scan, deshalb gezielt gegated.

Beide Signale sind rückwärtskompatibel (bestehende Aufrufer ohne die neuen Parameter
bekommen unverändertes Verhalten) und wurden synthetisch verifiziert (Formel-
Grenzwerte, Streak-Malus-Werte für Sichtung 1-10).

### Teil 2: Erfolgsmessung für Kaufkandidaten/"heiße" Watchlist-Kandidaten

Marktscan-Kandidaten hatten bisher KEINE Erfolgsmessung (anders als Signale mit vollem
MFE/Outcome-Tracking) - nur den Preis zum Entdeckungszeitpunkt und einen reinen
Lifecycle-Status. Ziel: eine leichtgewichtige, aber echte Erfolgsmessung, die (a) bei
schnellem Erfolg aktiv reagiert, (b) auch über mehrere Tage eine Aussage liefert, und
(c) konsequent bestehende Bausteine wiederverwendet.

**Kraken→CoinGecko-OHLC-Korrektur (dokumentierte Lehre):** der ursprüngliche Plan sah
vor, die bestehende `mindestziel_preis()`/`schaetze_mindestziel_zeitraum_tage()`-Logik
(`agent/krypto/backward_tracking.py`) unverändert wiederzuverwenden. Bei der Umsetzung
fiel auf: diese Funktionen brauchen `ohlc_rows` aus `db.get_ohlc_history()` →
`price_history_ohlc` - Kraken-basiert, NUR für Watchlist-Assets befüllt. Marktscan-
Kandidaten sind meist obskure, nicht Kraken-gelistete Altcoins - der Aufruf hätte fast
immer `None` geliefert. **Fix:** neues Modul `agent/krypto/marktscan_backward_tracking.py`
nutzt CoinGecko `/coins/{id}/ohlc` statt der Kraken-Tabelle, mit derselben Ø-Tagesspanne-
Formel (`_durchschnittliche_tagesspanne_coingecko()`, eigene Kopie statt Import der
privaten Kraken-Version). Da CoinGecko je nach `days`-Parameter unterschiedlich grobe
Kerzen liefert (30 Min./4h/4 Tage, dynamisch), werden die rohen Kerzen zuerst zu echten
Kalendertag-Balken aggregiert (`_ohlc_rows_zu_tages_bars()`, High=Tagesmaximum,
Low=Tagesminimum aller Kerzen des Tages) - garantiert eine echte "Tage"-Einheit,
unabhängig von der gelieferten Rohgranularität.

**CRV-Schwelle 0,8 (marktscan-eigen, getrennt von `backward_tracking.
richtungstreffer_mindest_crv=1.0`):** rechnerisch hergeleitet aus echten Daten - Ø
absolute Tagesbewegung der Marktscan-Kandidaten = 13,9% (Median 8,8%); Ziel-Move am
P70-P75 der beobachteten Forward-Returns (+9,1% bis +15,9%) ergibt CRV-Äquivalent
0,65-0,94 (Ziel-Move ÷ Ø Tagesbewegung), Empfehlung Mitte = 0,8, vom Nutzer bestätigt.
Wichtig: 12-24h- und 3-Tage-Renditeverteilung sind fast identisch (P70: +9,1% vs.
+7,5%) - EIN Schwellenwert bedient sowohl schnelle als auch mehrtägige Erfolge.

**Watchlist-Trigger** (welche `watchlist_wuerdig`-Kandidaten bekommen überhaupt eine
Messung): ein Datencheck (Zeit bis 3. Sichtung vs. spätere Kaufkandidat-Beförderung,
n=7) zeigte keine robuste Korrelation für eine eigene enge Zeitfenster-Regel - bewusst
KEINE neue Regel erfunden, stattdessen Wiederverwendung von `sichtung_position >= 3`
(bereits per Streak-Backtest aus Teil 1 bestätigt).

**Architektur (`agent/krypto/marktscan_backward_tracking.py`):**
- `starte_messung()`: holt CoinGecko-OHLC, berechnet Mindestziel-Preis (CRV-basiert)
  + geschätzte Zeitspanne, setzt `outcome_status='offen'`. Kein OHLC verfügbar → bleibt
  `nicht_anwendbar`, kein Hard-Fail.
- `pruefe_messung()`: `outcome_return_pct` wird bei JEDEM Check aktualisiert (auch
  während `offen`). Erfolg = aktueller Preis ≥ bereits gespeichertes `mindestziel_usd`
  (direkter Preisvergleich, kein erneutes CRV-Zurückrechnen nötig). Kein Erfolg nach
  Ablauf von `config.yaml marktscan.erfolgsmessung.mindestziel_zeitraum_tage_cap`
  (7 Tage, harte Obergrenze) ohne Zielerreichung.
- `run_marktscan_backward_tracking()`: 2 Schritte pro Lauf - (1) neue Messungen für
  Kaufkandidaten + "heiße" Watchlist-Kandidaten starten, (2) alle offenen Messungen
  gebündelt gegen EINEN `get_simple_prices()`-Call prüfen (kein Call pro Zeile). Bei
  Erfolg: falls noch keine LLM-Kurzbegründung vorhanden, synchroner
  `generate_candidate_writeup()`-Aufruf (kein Wartemechanismus nötig - anders als der
  Z.ai-Wartemechanismus bei Hebel/Spot, der existiert WEIL Z.ai in einem Hintergrund-
  Thread läuft; hier läuft der LLM-Call synchron im selben taeglichen Job).
- Neuer täglicher Scheduler-Job `marktscan_backward_tracking_job` (07:00, nach dem
  bestehenden 06:00 Spot/Hebel-Backward-Tracking).

**"Hohes Potential"-Definition** (`agent/krypto/marktscan.py::
ist_hohes_potential_kandidat()`, EINE Definition an zwei Stellen wiederverwendet):
`sichtung_position <= 2` (noch kein Streak-Malus) UND `score_gesamt >=
score_kaufkandidat_ab + hohes_potential_score_marge` (VORLAEUFIG 15, also ≥85). Genutzt
für (1) einen SLA-Bonus in `budget_allocator.py::effektive_sla_marktscan` (analog zum
bestehenden `portfolio_bonus`-Muster, senkt die effektive SLA zusätzlich für frische,
starke Kandidaten - der Zwei-Eimer-Mechanismus in `_priorisiere_nach_wartezeit()`
selbst bleibt unverändert) und (2) einen Hinweis-Satz in Mail 1.

**Benachrichtigung - 3 eigenständige E-Mails statt einer gebündelten (Nutzer-Korrektur):**
Der erste Entwurf sah EINE gebündelte Erfolgs-E-Mail für jeden CRV-0,8-Treffer vor -
eigene Schlussfolgerung aus der Recherche, keine explizit bestätigte Vorgabe. Der
Nutzer erinnerte sich anders (Benachrichtigung nur für "Sonderfälle mit hohem
Potential"). Bei der Recherche dazu wurde ein echter, schon bestehender Verdrahtungs-
Fehler gefunden: der Tier-2-Marktscan-Zweig von `run_budget_allocator()`
(`budget_allocator.py:644-655`) feuert bereits seit dem E-Mail-Latenz-Fix (27-07-23)
`on_signal_ready(f"marktscan:{coingecko_id}", res)` nach jedem fertigen LLM-Kurzgutachten
- der Dispatcher `_on_signal_ready()` in `scheduler/background.py` hatte dafür aber nur
Zweige für `"hebel:"`/`"spot:"`, für `"marktscan:"` passierte nichts (das fertige
Kurzgutachten verschwand nach dem stillen DB-Update). Die Benachrichtigung gliedert
sich jetzt in 3 unabhängig getriggerte Mails:
1. **Kaufkandidat-Tier2-Mail** (`_notify_marktscan_writeup()`): schließt die
   gefundene Lücke - feuert bei JEDEM Tier-2-Writeup (keine Potential-Schwelle als
   Trigger nötig), enthält zusätzlich den "hohes Potential"-Hinweis falls zutreffend.
   Voraussetzung: `_writeup()` in `budget_allocator.py` gab bisher implizit `None`
   zurück (kein `return`-Statement) - gibt jetzt `candidate` zurück, damit der Callback
   überhaupt Inhalt hat.
2. **Watchlist-"heiß"-Mail** (`_notify_marktscan_watchlist_heiss()`, in
   `marktscan_job()`): NUR wenn ein `watchlist_wuerdig`-Kandidat GENAU beim Übergang zu
   `sichtung_position==3` (nicht bei jeder weiteren Sichtung) UND die 3 Sichtungen
   innerhalb `config.yaml marktscan.erfolgsmessung.watchlist_heiss_fenster_stunden`
   (48h, vom Nutzer bestätigt - ca. 2x der beobachteten Median-Zeit bis zur
   3. Sichtung von 24h, n=172) aufeinander folgten. Neue DB-Funktion
   `get_marktscan_sichtungs_zeitspanne_bis_n()`.
3. **Schnellerfolg-Mail** (`_notify_marktscan_schnellerfolg()`, in
   `marktscan_backward_tracking_job()`): NUR wenn die tatsächliche Dauer bis Erfolg
   ≤ `config.yaml marktscan.erfolgsmessung.schnellerfolg_anteil_max` (0,5, vom Nutzer
   bestätigt) mal der geschätzten Dauer war - ein ungewöhnlich schneller Treffer gilt
   als zusätzliche Bestätigung des hohen Potentials. JEDER Erfolg wird trotzdem
   vollständig in der DB erfasst (Abschnitt Datenmodell) - nur die E-Mail ist auf die
   schnellen Fälle beschränkt.

**GUI (`ui/marktscan_view.py`) - zwei getrennte Elemente, ursprünglich im ersten
Plan-Entwurf ein fehlendes Element:** "Potential" (Vorhersage, sofort bei Entdeckung
verfügbar) wurde im ersten Entwurf übersehen - der Nutzer wies darauf hin, dass dies
sein ursprünglicher Wunsch aus der Diskussion war. Lösung ohne neue Backend-Berechnung:
der bereits gespeicherte `score_momentum`-Wert reflektiert bereits Streak-/ATH-/
Verlängerungs-Malus + Rank-Bonus - er IST bereits die "Potential"-Kennzahl. Neue Spalte
`"potential"` + Detail-Panel-Zeile mit transparenter Aufschlüsselung aus
`signale_momentum_json` (z.B. "3. Sichtung (-5), ATH-Abstand -12,3% (-18)"). "Outcome"
(gemessenes Ergebnis, erst nach `starte_messung()` verfügbar) ist unabhängig davon:
neue Spalte `"outcome"` + `_MARKTSCAN_OUTCOME_LABELS`/`_marktscan_outcome_color()`
(analog `ui/signals_view.py::_OUTCOME_LABELS`/`_outcome_color()`) + Detail-Panel-Zeile.

**Remote-Status:** neue Karte "Marktscan-Erfolgsquote" (`_get_marktscan_erfolgsquote()`
→ `agent/krypto/marktscan_backward_tracking.py::compute_marktscan_erfolgsquote()`,
analog `compute_richtungstreffer_quote()`) - Anteil erfolgreicher ABGESCHLOSSENER
Messungen (offene zählen nicht mit), Ø Tage bis Erfolg nur bei n≥15 als belastbar
markiert.

**Neue Config-Schlüssel** (`Basisinfos/config.yaml`):
```yaml
marktscan:
  erfolgsmessung:
    richtungstreffer_mindest_crv: 0.8
    mindestziel_zeitraum_tage_cap: 7
    watchlist_heiss_fenster_stunden: 48
    schnellerfolg_anteil_max: 0.5
    hohes_potential_score_marge: 15
budget_allocator:
  marktscan_reifegrad_bonus_stunden: 10
```

**Verifikation:** durchgängig synthetisch getestet (In-Memory-SQLite + Mock-CoinGecko-
Client) - Kalendertag-Aggregation, Streak-/ATH-Malus-Grenzwerte, `starte_messung()`/
`pruefe_messung()` (Erfolg/Kein-Erfolg/Ablauf/Schnellerfolg-Fälle), `has_pending_
marktscan_messung()`, `get_marktscan_sichtungs_zeitspanne_bis_n()` (positiv + negativ),
kompletter `run_marktscan_backward_tracking()`-Durchlauf inkl. Watchlist-Filter-Guard,
`ist_hohes_potential_kandidat()` (4 Fallkombinationen), GUI-Smoke-Test (Tk-Instanziierung
+ Spalten/Tags/Detail-Panel-Rendering gegen echte In-Memory-DB), `compute_marktscan_
erfolgsquote()` gegen befüllte Testdaten, sowie ein Kompilier-/Import-Check aller
geänderten/neuen Dateien. Ein echter Lauf gegen Notebook-Produktivdaten steht als
Nachtrag aus (kein direkter Notebook-Zugriff in dieser Session).

## Nachtrag (2026-07-31): Blinder Fleck behoben — Schatten-Tracking auch für selbst gewähltes HALTEN (kein Gate/Veto)

**Auslöser:** ein frischer Notebook-Export zeigte 49 von 51 Hebel-Signalen an
einem Tag als reines, selbst gewähltes HALTEN (`risk_veto=False`) - die letzte
echte ERÖFFNEN-Empfehlung lag zu dem Zeitpunkt bereits ~27 Stunden zurück,
trotz eines BTC-Anstiegs an diesem Tag. Der Nutzer konnte nicht beurteilen, ob
das System "einfach nur gute Trades filtert" oder "vollständig blockiert" ist,
und ordnete das explizit den Vortages-Optimierungen zu (Regel-13-Fix + Regel
27 "Action-Bias-Korrektur", siehe [[project_regelwerk_audit_29_07]]) - Prüfung
bestätigte: erwarteter, bereits dokumentierter Effekt von Regel 27, kein Bug.
Das eigentliche Problem lag tiefer: das bestehende Veto-Schatten-Tracking
(Nachtrag 28.07. oben) verfolgt NUR Fälle, in denen ein Gate eine Empfehlung zu
HALTEN zurückstuft (`risk_veto=True`) - ein **selbst gewähltes** HALTEN (das
LLM entscheidet sich von sich aus dagegen, Regel 27 mandatiert genau das als
Normalfall) hatte bisher gar keine Preiszonen und fiel beim bestehenden
Diskriminator automatisch durch. Ohne Gegenmaßnahme bleibt die Kernfrage des
Nutzers ("war die eigene Zurückhaltung richtig?") auf unbegrenzte Zeit
unbeantwortbar - explizite Nutzer-Vorgabe: "diesen Blinden Fleck müssen wir
beheben sonst haben wir auch in 2 Monaten keine Daten."

**Design-Entscheidung - neues Flag statt nachträglicher Ableitung:** ein
naiver Diskriminator (`action=='HALTEN' and risk_veto==False`) hätte bei Hebel
einen echten Sonderfall falsch eingeschlossen: die "Kontrathese-Übersetzung"
(`hebel_risk_gate.py::post_check_hebel()`, siehe [[project_hebel_kontrathese_
uebersetzung]]) kann eine LLM-Empfehlung in Gegenrichtung zu einer offenen
Position ebenfalls zu `action="HALTEN"` machen, OHNE `risk_veto=True` zu
setzen - ein anderes Phänomen (Positions-Management statt "LLM lehnt jedes
Handeln ab"). Lösung: die ursprüngliche LLM-Aktion wird direkt bei der
Generierung festgehalten (`ursprüngliche_action` in `post_check_hebel()`, vor
jeder Verzweigung), am Funktionsende gilt `ist_reines_llm_halten =
(ursprüngliche_action == "HALTEN" and action == "HALTEN" and not risk_veto)` -
schließt so sowohl Gate-Veto-HALTEN als auch Kontrathese-übersetztes HALTEN
korrekt aus. Spot (`risk_gate.py::post_check()`) hatte die Erfassung
`original_action = action` bereits vorhanden (kein Kontrathese-Äquivalent,
Prinzip aber aus Symmetriegründen identisch übernommen).

**Umsetzung - Option B (komplett eigenständige Spalten/Funktionen, gleiches
Muster wie das Veto-Schatten-Tracking, siehe Nachtrag 28.07. oben):**
- `database/models.py`/`db.py`: neues Feld `ist_reines_llm_halten: bool` +
  additive Migration (`Signal`+`HebelSignal`), plus 6 neue `selbst_halten_
  outcome_*`-Felder (byte-identisches Schema zu `veto_outcome_*`) +
  `update_signal_selbst_halten_outcome()`/`update_hebel_signal_selbst_halten_
  outcome()`.
- `hebel_risk_gate.py::post_check_hebel()`/`risk_gate.py::post_check()`:
  Flag-Berechnung wie oben beschrieben, `result["_ist_reines_llm_halten"]`.
- `hebel_pipeline.py`/`pipeline.py`: Flag durchgereicht in `HebelSignal(...)`/
  `Signal(...)`.
- Neuer Diskriminator `_hat_hebel_selbst_halten_these()`/`_hat_selbst_halten_
  these()`: `ist_reines_llm_halten == True` UND alle drei Preiszonen gesetzt -
  bewusst KEIN Rücklesen von `risk_veto`/`action` (das Flag existiert genau
  deshalb, um den Kontrathese-Fallstrick strukturell auszuschließen, nicht nur
  per Konvention).
- `_richtung_aus_veto_zonen()` in `backward_tracking.py` umbenannt zu
  `_richtung_aus_zonen()` (dient jetzt zwei Diskriminatoren - Veto-Schatten UND
  Selbst-Halten-Schatten, beide brauchen dieselbe Zonen-Richtungs-Ableitung,
  da `action` in beiden Fällen bereits auf HALTEN steht).
- `check_hebel_signal_selbst_halten_outcome()`/`check_signal_selbst_halten_
  outcome()`: identische TP/SL/Liquidation/MFE-Mechanik wie das Veto-Schatten-
  Pendant, eigene `selbst_halten_outcome_*`-Spalten. Neuer SQL-Zweig in
  `run_hebel_backward_tracking()`/`run_backward_tracking()`, kein Überholt-
  Check (gleiche Begründung wie beim Veto-Schatten-Zweig).
- Neue Aggregationen `compute_selbst_halten_performance()`/`_nach_grund()`
  (letztere gruppiert nach `top_grund_1_kategorie` - bereits ein sauberes
  Enum, kein Freitext-Klassifikator wie bei `_kategorisiere_veto_grund()`
  nötig). **Bewusst NICHT in `compute_gesamt_signalqualitaet()` gemischt:**
  jene Funktion beantwortet "hätte gehandelt, wurde ausgeführt ODER vom Gate
  verhindert" (LLM wollte handeln) - Selbst-Halten beantwortet die strukturell
  andere Frage "war die eigene Zurückhaltung richtig" (LLM wollte NICHT
  handeln). Bleibt eine eigene, separate Kennzahl.
- `extract_notebook_diagnose.py`: neue Spalten + 2 neue Payload-Keys
  (`selbst_gewaehltes_halten_performance`/`_nach_grund`).
- **Remote-Status-Anzeige** (Nutzer-Nachforderung nach dem ersten Plan-Entwurf:
  "sollen auf der Remote Seite mit kurzer Info angezeigt werden um zu
  Monitoren - füge diese Sauber in die bestehende Sortierung ein"): zwei neue,
  kompakte Karten direkt nach der bestehenden "Veto-Schatten-Performance nach
  Veto-Grund"-Karte, innerhalb derselben Gruppe C - keine neue Gruppe, keine
  Umsortierung. Wiederverwendet die bereits vorhandenen generischen Renderer
  (`renderSpotProviderPerformanceByAssetklasse()`/`renderProviderPerformance()`
  - identisches Datenformat wie `veto_schatten_performance`, keine neue
  JS-Render-Funktion nötig).
- Neue Prompt-Regeln (rein Daten-Vervollständigung, KEINE Entscheidungs-
  änderung, konsistent mit [[feedback_llm_synthese_kein_deterministischer_
  override]]): Regel 28 (`hebel_analyst.py`) und Regel 33 (`analyst.py`,
  Spot hatte bisher gar keine Action-Bias-Regel) verlangen, bei selbst
  gewähltem HALTEN trotzdem eine hypothetische Entry/Stop-Loss/Take-Profit-
  Zone anzugeben, so als wäre man bei der (Regel 27 mandatierten) Abwägung zur
  Gegenoption gekommen. `action`/`confidence_pct` bleiben unverändert auf
  HALTEN bezogen; ohne kohärentes Setup keine Zahlen erfinden - Zonen bleiben
  dann wie bisher leer (Konsistenz mit demselben Guardrail: das Werturteil
  selbst wird nicht angetastet, nur zusätzliche Information angefordert).

**Bewusst NICHT Teil dieser Runde (Scope-Cut, Nutzer-Vorgabe):** App-GUI-
Spalten (`ui/hebel_view.py`/`ui/signals_view.py`) und E-Mail-Vorlagen bleiben
außen vor - erst sinnvoll, sobald genug aufgelöste Fälle für eine
detailliertere Anzeige vorliegen (Remote-Status-Karten reichen für das
Monitoring-Bedürfnis dieser Runde).

**Verifikation:** synthetische Tests für alle 6 Plan-Fälle (Gate-Veto-HALTEN,
Kontrathese-übersetztes HALTEN als kritischer Negativfall, echtes selbst
gewähltes HALTEN mit/ohne Zonen, normales ERÖFFNEN ohne Gate-Eingriff, Spot-
Äquivalente ohne Kontrathese-Fall) direkt gegen `post_check_hebel()`/
`post_check()` und die neuen Diskriminatoren, Migrationstest gegen frische
temp-SQLite-Datei (Idempotenz zweier `init_db()`-Läufe, alle 7 neuen Spalten
je Tabelle vorhanden), DB-Rundlauf (Insert/Read-back/Update-Funktion für
Hebel+Spot), End-to-End-Check-Funktions-Test gegen synthetische OHLC-Daten
(Take-Profit-Treffer, realistisches CRV), Regressionscheck der bestehenden
Veto-Schatten-Diskriminatoren (einzige gemeinsame Code-Berührung war die
Umbenennung `_richtung_aus_veto_zonen()`→`_richtung_aus_zonen()`) - alle 33
Prüfungen bestanden. Kompilier-Check aller 13 geänderten Dateien fehlerfrei.
Ein echter Lauf gegen Notebook-Produktivdaten steht als Nachtrag aus
(braucht mehrere Wochen echter Signale, bis genug selbst gewählte HALTEN-Fälle
aufgelöst sind, um die Frage "war die Zurückhaltung richtig?" belastbar zu
beantworten - Wiedervorlage entsprechend spät).

## Nachtrag (2026-07-31): zwei echte Funde beim ersten Notebook-Lauf - NameError-Bugfix + Veto-Schatten-Kontamination behoben

**Auslöser 1 (Nutzer-Meldung):** der erste `extract_notebook_diagnose.py`-
Lauf am Notebook nach dem obigen Feature schlug mit `NameError: name
'_richtung_aus_veto_zonen' is not defined` fehl. Root Cause: beim Umbenennen
`_richtung_aus_veto_zonen()` → `_richtung_aus_zonen()` wurde EIN Aufrufer
übersehen - `compute_zai_richtung_performance_schatten()`, eine bereits
bestehende Funktion vom 28.07., die nicht Teil des bearbeiteten Funktions-
Sets war und daher beim manuellen Nachvollzug der Call-Sites nicht als
Aufrufer erkannt wurde. `python -m py_compile` UND `ast.parse()` waren
beide gruen, weil beide nur Syntax pruefen - der Fehler zeigte sich erst
zur Laufzeit, als `main()` (indirekt) diese Funktion tatsaechlich aufrief.
**Fix:** Aufrufstelle + 2 stale Docstring-Referenzen korrigiert
(`agent/krypto/backward_tracking.py`). Methodik-Lehre in
`Basisinfos/Test_und_Verifikationsmethodik.md` (Abschnitt 1.4) festgehalten:
Umbenennungen brauchen ein repository-weites Grep VOR Abschluss, UND
Skripte mit klarem Einstiegspunkt (`main()`) brauchen zusaetzlich zum reinen
Klasse-2/3-Funktionstest einen End-to-End-Smoke-Test des Einstiegspunkts
selbst.

**Auslöser 2 (eigene Kontraprüfung, vom Nutzer explizit angefordert -
"mach eine Kontraprüfung - kritisch als Experte"):** bei der kritischen
Durchsicht der eigenen Loesung fiel ein zweiter, unabhaengiger Fund auf:
`post_check_hebel()`s AZ-7/`krise_extrem`-Deckel (`if not pre_result.
hebel_erlaubt:`) ist die EINZIGE **unbedingte** Veto-Verzweigung der
Funktion - sie feuert unabhaengig davon, was das LLM urspruenglich
entschied (alle anderen Veto-Zweige sind an `action != "HALTEN"` bzw. eine
bestimmte `action` gebunden). Hatte das LLM in einem `krise_extrem`-Regime
von sich aus schon HALTEN gewaehlt (und dank der neuen Regel 28 jetzt
hypothetische Zonen dazu ausgefuellt), wurde dieser Fall trotzdem mit
`risk_veto=True` markiert - und landete damit im bestehenden Veto-Schatten-
Diskriminator (`risk_veto=True AND action=="HALTEN" AND Zonen gesetzt`),
obwohl nie ein Trade vorgeschlagen wurde. **Vor Regel 28 war dieser Pfad
strukturell inaktiv** (ein selbst gewaehltes HALTEN hatte nie Zonen, der
Diskriminator schied schon an der Zonen-Bedingung aus) - die neue Regel 28
hat diesen latenten Fall erst scharf geschaltet. Geprueft und ausgeschlossen:
Spot hat keine unbedingte Veto-Verzweigung (`kauf_erlaubt`-Check ist immer
an `action in _BUY_ACTIONS` gebunden) - Kontamination betrifft ausschliesslich
Hebel.

**Fix:** neues Feld `original_action: str | None` (additive Migration,
`Signal`+`HebelSignal`) - persistiert dieselbe rohe Vor-Veto-Aktion, die
`ist_reines_llm_halten` intern bereits berechnet, zusaetzlich als eigenes
Feld. `_hat_hebel_veto_schatten_these()` verlangt jetzt zusaetzlich
`original_action != "HALTEN"`. Bewusst rueckwaertskompatibel: fuer Alt-
Zeilen ohne `original_action` (vor dieser Migration, Wert `None`) gilt
`None != "HALTEN"` weiterhin als `True` - keine rueckwirkende Neubewertung
bereits aufgeloester Faelle, der Fix wirkt nur auf Signale ab jetzt.

**Verifiziert (9 zusaetzliche synthetische Pruefungen, alle PASS):**
Kontaminations-Fall (`krise_extrem` + bereits selbst gewaehltes HALTEN mit
Regel-28-Zonen) - `original_action` wird korrekt als `"HALTEN"` persistiert,
Diskriminator schliesst den Fall jetzt korrekt aus; Kontroll-Fall (echter
`ERÖFFNEN`-Vorschlag, per `krise_extrem` vetoed) - `original_action` wird
korrekt als `"ERÖFFNEN"` persistiert, Diskriminator erfasst den Fall
weiterhin unveraendert; Backward-Compat-Fall (Alt-Zeile ohne
`original_action`) - Diskriminator erfasst den Fall weiterhin unveraendert.
Zusaetzlich zwei End-to-End-`extract_notebook_diagnose.py::main()`-Laeufe
gegen frische temp-SQLite-Dateien (vor und nach dem `original_action`-Fix)
ohne Fehler durchgelaufen - reproduziert exakt den Pfad, der beim Nutzer
fehlschlug.

## Nachtrag (2026-07-31): Staggering der Sofort-Start-Jobs, CoinGecko-Kontingent-Tracking, Remote-Fehlerisolierung, Z.ai-Kartenfix

**Staggering der 8 Sofort-Start-Jobs** (`scheduler/background.py`,
`_staggered_start(index)`, committet `88c0b82`): alle Sofort-Start-Jobs
(`next_run_time=jetzt`) feuerten bisher gleichzeitig bei jedem Neustart -
Root Cause fuer wiederholte yfinance-Timeouts und mindestens einen SQLite-
"database is locked"-Absturz direkt nach dem Start. Jetzt um
`index * 5s` gestaffelt. Per echtem Log-Vergleich bestaetigt: 0 yfinance-
Timeouts und 0 DB-Lock-Vorfaelle ueber 3 Neustarts nach dem Fix, gegenueber
nahezu 100% Vorfallquote davor.

**Remote-Status-Fehlerisolierung** (`remote/status.py`, `_safe()`-Wrapper,
committet `a9849fa`): eine einzelne kaputte `_get_*()`-Funktion riss bisher
die komplette `/api/status`-Antwort mit - jetzt einzeln abgefangen und
geloggt, Rest der Seite bleibt intakt.

**CoinGecko-Kontingent-Tracking** (`api/coingecko.py`, `database/db.py`,
`scheduler/background.py`, `remote/status.py`+`server.py`, committet
`9a744a8`): ausgeloest durch eine echte CoinGecko-E-Mail ("80% consumption
reached"). Zaehlt jeden tatsaechlich gesendeten Call ueber den einzigen
Funnel-Punkt `CoinGeckoClient._get()`, Warnmails bei 80%/90% (DB-Flag statt
Zeit-Cooldown, damit ein Neustart keine Duplikat-Mail ausloest - siehe
Begruendung in Memory `project_coingecko_kontingent_tracking`).
**Bekannte Einschraenkung:** der Zaehler startet bei Feature-Deploy
(31.07., letzter Tag des Monats), nicht rueckwirkend ab Monatsanfang -
die Remote-Karte zeigte am Deploy-Tag deshalb einen stark untertriebenen
Prozentwert (z. B. 0,1% statt der von CoinGecko tatsaechlich gemeldeten
80%). Ab dem 1. eines Monats beginnt der Zaehler jeweils zum echten
Monatsanfang und ist dann akkurat - betrifft nur den einmaligen
Deploy-Tag.

**Z.ai-Richtungs-Karten: fehlender Kleine-Stichprobe-Hinweis behoben**
(`remote/server.py::renderZaiRichtungPerformanceTier()`, Fund beim
Screenshot-Review der Remote-Seite): anders als `renderProviderPerformance()`
zeigte diese Funktion nie den "(n<15, noch nicht belastbar)"-Hinweis, auch
bei n=1. Betraf beide Z.ai-Karten (Gruppe B und Veto-Schatten-Variante in
Gruppe C), da beide dieselbe Renderfunktion nutzen. Jetzt dieselbe
`PROVIDER_PERF_MIN_SAMPLE`-Schwelle nachgeruestet - rein kosmetisch, die
zugrunde liegenden Prozentwerte waren immer korrekt.

## Nachtrag (2026-07-31): Multi-Asset Z.ai-Wartemechanismus statt Re-Fetch (Entscheidungskatalog Punkt 1)

**Ausloeser:** echter Nutzer-Fund - eine S&P-Hedge-VERKAUFEN-E-Mail hatte
trotz unbedingtem Z.ai-Aufruf (`agent/hedge/pipeline.py`, `if zai_client is
not None:` ohne Aktions-Filter) ueberhaupt keine Z.ai-Zeilen. Nutzer verwies
auf seine fruehere Vorgabe "soll vom Grundprinzip bei allen Assets ident
funktionieren" (27.07.) sowie die explizite Rueckfrage "hast du das fuer
alle ZAI und eMail benachrichtigung beruecksichtigt?" (28.07.) und wollte
wissen, ob dieser Fall damals uebersehen wurde. **Klarstellung:** nicht
uebersehen - die Multi-Asset-Re-Fetch-Loesung (2026-07-27, "E-Mail: Re-Fetch
statt Hebel-artigem Wartemechanismus") wurde bei der 28.07.-Pruefung explizit
als ausreichend eingestuft ("fuer die meisten Signale bereits fertig"). Der
heutige Fund zeigt den Fall, in dem diese probabilistische Annahme nicht
zutraf - ein damals bewusst akzeptiertes Restrisiko, das jetzt real
aufgetreten ist.

**Fix:** neue Funktion `_sende_multi_asset_email_mit_zai_wartezeit()`
(`scheduler/background.py`), dritter duenner Wrapper um die bereits
bestehende, generische `_sende_signal_email_mit_zai_wartezeit()` (Hebel/Spot
haben je einen eigenen). `REQUIRED_ACTIONS` ist bei allen 4 Multi-Asset-
Analysten (Aktien/Rohstoffe/Themen-ETF/Hedge) identisch (`("KAUFEN",
"VERKAUFEN", "HALTEN", "NACHKAUFEN")`, per Grep bestaetigt) - hier inline
statt eines beliebig wirkenden Imports aus nur einem der vier Module.
`multi_asset_batch_job()`s Benachrichtigungsschleife spawnt jetzt pro Signal
einen eigenen Hintergrund-Thread (exakt das Muster von `_on_signal_ready()`
fuer Hebel/Spot) statt des bisherigen einmaligen Re-Fetches - blockiert die
anderen Signale in der Schleife nicht (E-Mail-Latenz-Fix bleibt intakt), da
die Schleife selbst nur Threads startet und sofort zurueckkehrt. Bei
`zai_client=None` weiterhin direkter Aufruf ohne jeden Refetch-Versuch
(kein Z.ai-Hintergrund-Thread existiert in diesem Fall ueberhaupt).

**Verifiziert (Klasse 2, 21 Pruefungen, alle PASS):** Wrapper-Funktion
isoliert (HALTEN-Fruehausstieg ohne Wartezeit, Z.ai-Urteil trifft waehrend
der Wartezeit ein -> Early-Break mit angereichertem Signal, Z.ai-Urteil
trifft nie ein -> Zeitlimit greift, E-Mail trotzdem ohne Z.ai-Zeilen);
`multi_asset_batch_job()` end-to-end gegen frische temp-SQLite-Datei (nie
Produktions-DB) mit gemocktem `run_multi_asset_batch()`/`get_listed_assets()`
und abgefangenem `threading.Thread` (erfasst Ziel+Argumente statt echter
Thread-Ausfuehrung, danach synchron im Test nachvollzogen): `zai_client`
gesetzt -> genau 1 Thread mit korrektem Ziel gespawnt, kein synchroner
`notify_fn`-Aufruf in der Schleife selbst; `zai_client=None` -> kein Thread,
direkter `notify_fn`-Aufruf, `db.get_signal_by_id()` kein einziges Mal
aufgerufen (kein toter Refetch-Versuch mehr). Regressionscheck: beide
bestehenden Wrapper (Hebel/Spot) sowie ihre `REQUIRED_ACTIONS`-Importe
unveraendert funktionsfaehig.

**Status:** Committet + gepusht (`b2b4438`, zusammen mit dem Z.ai-n<15-
Kartenfix vom selben Tag).

## Nachtrag (2026-07-31): Hebel Regel 6 um Take-Profit-ATR-Leitplanke erweitert + neuer Messstandard atr_relativ_prozent_bei_signal

Fortsetzung der CRV-Gate-Untersuchung (siehe project_enge_stop_loss_backtest_
und_massnahmen.md fuer die volle Herleitung): ein granularerer Vergleich der
CRV-Baender zeigte einen unerklaerten Trefferquote-Einbruch von 67,3% (Band
1,0-1,5) auf 30,4% (Band 1,5-2,0), der sich nicht durch Stop-Loss-Abstand,
Konfidenz, Symbol-Konzentration oder These-Typ erklaeren liess. Ein echter
CoinGecko-OHLC-Abruf (14 Symbole, Wilder ATR-14) zeigte: die Take-Profit-
Distanz relativ zum ATR ist im schlechten Band ~29% weiter (0,75x vs. 0,58x),
waehrend die Stop-Loss-Distanz nahezu identisch bleibt (0,44x vs. 0,48x).

Ueber ein Random-Walk-Barrier-Race-Modell (Optionstheorie "Probability of
Touch": P(obere Barriere zuerst getroffen) = Distanz_unten / (Distanz_unten +
Distanz_oben)) wurde quantifiziert, dass diese TP-ATR-Asymmetrie genau ~23%
des beobachteten Einbruchs erklaert - real und bedeutsam, aber mit ~77%
unerklaertem Rest (Tage-Clustering suggestiv, nicht abschliessend geklaert).
Externe Literatur (Marcos Lopez de Prado, "Advances in Financial Machine
Learning", 2018 - Triple-Barrier-Method) bestaetigt: professionelle Ansaetze
skalieren Take-Profit UND Stop-Loss gleichermassen relativ zur Volatilitaet;
unser bisheriges Design (Option D, 28.07.) skalierte nur die Stop-Seite.

**Umsetzung:** `agent/krypto/hebel_analyst.py` SYSTEM_PROMPT Regel 6 um einen
symmetrischen Take-Profit-Zusatz erweitert (~1,5-2x ATR-relativ als
Richtwert, kein hartes Limit, exakt gleiches Muster wie die bestehende
Stop-Loss-Leitplanke - Abweichung bei klarem Support/Widerstand/Fibonacci-
Level bleibt erlaubt, muss aber in `short_reasoning` benannt werden).

**Live-API-Test vor Einsatz (Nutzer-Vorgabe):** echter Mistral-Call, ALT- vs.
NEU-SYSTEM_PROMPT, 3 reale Coins (INJ/KAITO/NEAR, echte CoinGecko-Preis-/
ATR-Werte) plus 3 Wiederholungslaeufe je Variante fuer INJ zur Trennung von
Signal und Sampling-Rauschen. Ergebnis: kein Format-/Parsing-Problem in 9
echten Calls; der beabsichtigte Effekt (TP-ATR-Vielfaches steigt) zeigt sich
im Mittel (0,62x zu 0,83x bei INJ-Wiederholungen), die Lauf-zu-Lauf-Streuung
bei Mistral temperature=0.2 ist aber genauso gross wie der zugeschriebene
Effekt - bei n=3 pro Bedingung statistisch nicht von Zufall zu unterscheiden.
Bewusst KEIN neuer harter Schwellenwert/Risikofaktor (Konsistenz mit
"Backtest first, harte Garantie statt Soft-Boost" - dieser TP-Zusatz hat noch
keinen dedizierten Vorher-Nachher-Bucket-Backtest wie der urspruengliche
SL-Fix).

**Neuer Messstandard:** `database/models.py::HebelSignal.
atr_relativ_prozent_bei_signal` (additive Migration
`_migrate_hebel_signal_atr_column()` in `database/db.py`, verdrahtet in
`agent/krypto/hebel_pipeline.py` aus `facts["technische_analyse"]["atr"]
["relativ_prozent"]`, exportiert in `extract_notebook_diagnose.py::
_HEBEL_SIGNAL_SPALTEN`) - persistiert den ATR-Fakt-Wert, der dem LLM
tatsaechlich vorlag, direkt bei Signal-Erstellung. Ersetzt fuer kuenftige
Signale die bisherige retroaktive CoinGecko-OHLC-Rekonstruktion (naeherungs-
weise, abhaengig von Datums-Zuordnung) durch eine exakte, sofort verfuegbare
Messgroesse.

**Verifiziert:** Klasse-1 (Import + Textmarker + Regel-7-Anschluss fuer den
Prompt-Zusatz); Klasse-2 (4 Tests: Migration idempotent, Spalte existiert,
Insert+Read-Rundlauf mit korrektem Wert, NULL-Fall fuer fehlenden Wert -
alle PASS); Import-Regressionscheck fuer `hebel_pipeline.py` und
`extract_notebook_diagnose.py`.

**Wiedervorlage (kein festes Datum):** sobald n>=15 neue, nach diesem Fix
aufgeloeste Hebel-LONG-Signale mit gesetztem `atr_relativ_prozent_bei_signal`
vorliegen, direkter Vorher-Nachher-Bucket-Vergleich moeglich - siehe
project_enge_stop_loss_backtest_und_massnahmen.md fuer den vollstaendigen
Stand und die noch offene ~77%-Erklaerungsluecke.

## Nachtrag (2026-07-31): Hebel-Cooldown-Umgehungs-Bugfix (echter VIRTUAL-Fund) - angefragte_richtung

**Anlass:** Nutzer meldete eine Verdopplung der taeglichen Mistral-/CoinGecko-
Abfragen ab dem 31.07. (Remote-Seite zeigte `LLM-Budget heute (Krypto):
314 / 180`, davon 217 allein Hebel). Genaue Analyse (exakte Timestamps,
`richtung`/`ist_reines_llm_halten`-Verlauf) zeigte: fuer VIRTUAL wechselte das
LLM ab exakt 12:07:38 UTC konsistent von "antwortet LONG" auf "antwortet
SHORT" (korreliert mit Fear&Greed="Extreme Fear"=25), obwohl die Kandidatur
weiterhin LONG war (`hebel_richtung_modus: nur_long`). Ab diesem Zeitpunkt
lief VIRTUAL alle ~15 Min. erneut durch die Analyse statt im vorgesehenen
3,5h-`cooldown_stunden`-Abstand (43 Analysen an einem Tag statt ~7).

**Root Cause:** `_filter_hebel_cooldown()` (`agent/krypto/budget_allocator.
py`) nutzte `db.get_latest_hebel_signal_per_symbol_and_richtung()`, deren
Lookup-Key `richtung` die vom LLM FREI gewaehlte Antwort ist (siehe deren
eigener Docstring + `HebelSignal.kontrathese_llm_richtung`-Praezedenzfall) -
NICHT die tatsaechlich angefragte Richtung. Der Nur-Long-Deckel-Veto-Zweig in
`hebel_risk_gate.py::post_check_hebel()` ("Nur-Long-Deckel"-Kommentar) laesst
`richtung` bewusst unveraendert (anders als die Kontrathese-Uebersetzung
direkt darueber, die `richtung` deterministisch zurueckssetzt) - das ist seit
dem 2026-07-28-Fix ("Nur-Long-Deckel-Luecke") beabsichtigt, weil `hebel_
backward_tracking.py::check_hebel_signal_veto_shadow_outcome()` explizit
darauf angewiesen ist, dass `richtung` die WAHRE (SHORT-)Form des vetoten
Vorschlags behaelt (sonst wuerde die Veto-Schatten-Performance-Auswertung
SHORT-foermige Zonen faelschlich als LONG auswerten - TP/SL-Richtung
invertiert). Sobald das LLM ueber viele Zyklen konsistent SHORT statt LONG
antwortete, fand `latest.get((symbol, "LONG"))` also nie mehr einen aktuellen
Treffer - der Cooldown griff nicht mehr.

**Kritische Gegenpruefung vor Umsetzung (Nutzer-Auftrag):** ein erster
Loesungsansatz ("wie bei Kontrathese `richtung` zuruecksetzen") wurde anhand
von `Regelwerksmanual.md` (Kontrathese-Nachtrag oben) und `hebel_backward_
tracking.py`s Docstring explizit verworfen - das haette die Veto-Schatten-
Tracking-Kette fuer alle Nur-Long-Deckel-Faelle stillschweigend korrumpiert.

**Fix (rein additiv, beruehrt NUR den Cooldown-Filter):**
- `database/models.py::HebelSignal.angefragte_richtung: str | None = None` -
  neues, unabhaengiges Feld, haelt die vom Kandidaten (Screening-Trigger ODER
  offene Position, `HebelTrigger.richtung`) tatsaechlich angefragte Richtung
  fest, komplett unabhaengig von der LLM-Antwort `richtung`.
- `database/db.py`: additive Migration `_migrate_hebel_signal_angefragte_
  richtung_column()`, neue Spalte in `_HEBEL_SIGNAL_COLUMNS`, neue Funktion
  `get_latest_hebel_signal_per_symbol_and_angefragte_richtung()` (exakter
  struktureller Zwilling der bestehenden richtungsbasierten Funktion, aber
  gruppiert auf `angefragte_richtung`).
- `agent/krypto/hebel_pipeline.py`: `angefragte_richtung=trigger.richtung` an
  beiden `HebelSignal(...)`-Konstruktionsstellen (Fixed-Signal-Pfad + echter
  LLM-Pfad) ergaenzt.
- `agent/krypto/budget_allocator.py::_filter_hebel_cooldown()`: Lookup auf
  die neue Funktion umgestellt (einzige Verhaltensaenderung).
- `extract_notebook_diagnose.py`: `angefragte_richtung` zu `_HEBEL_SIGNAL_
  SPALTEN` ergaenzt (Diagnose-Sichtbarkeit fuer kuenftige Divergenz-Faelle).
- **Unveraendert (bewusst):** `get_latest_hebel_signal_per_symbol_and_
  richtung()` selbst und alle 4 anderen Konsumenten (Ueberholt-Erkennung in
  `hebel_backward_tracking.py`, GUI-Historie in `ui/hebel_view.py`, `regime.
  py`, Doku-Verweis in `hebel_analyst.py`), die Kontrathese-Uebersetzung, der
  Nur-Long-Deckel-Veto-Zweig selbst, die Veto-Schatten-Tracking-Logik.

**Verifiziert:** Klasse-1 (Compile-Check aller 5 geaenderten Dateien); Klasse-
2 synthetisch gegen temp-DB (10 Tests, alle PASS) - Migration idempotent,
Insert+Read-Rundlauf, exakte Reproduktion des echten VIRTUAL-Bugs (alte
Funktion findet nur eine 10h alte Stale-Zeile statt der frischen SHORT-
Antwort-Zeile, haette den Kandidaten faelschlich durchgelassen; neue Funktion
blockt korrekt), unabhaengige LONG-/SHORT-Thesen bleiben unabhaengig,
Altzeilen ohne `angefragte_richtung` (NULL) verhalten sich wie "kein
Treffer" (einmaliges Nachhol-Verhalten, kein Absturz); Regression bestaetigt
(alte Funktion + alle 4 anderen Konsumenten unveraendert grep-verifiziert).

**Wiedervorlage:** keine - der Fix ist in sich abgeschlossen. Beobachten, ob
sich die taegliche Mistral-/CoinGecko-Abfragezahl nach Deploy wieder auf das
Vor-31.07.-Niveau normalisiert (Notebook-Deploy ausstehend).

## Nachtrag (2026-08-01): Zwei Zeit-Domaenen im Projekt (UTC-Daten vs. lokale Scheduler-Zeit) - bewusst KEIN Fix

**Anlass:** Nutzer bemerkte auf der Remote-Seite/in Logs eine 2h-Differenz
zwischen manchen Zeitangaben und fragte, ob Scheduler-Trigger faelschlich nach
"amerikanischer Zeit" statt lokaler Zeit laufen bzw. ob UTC und lokale Zeit im
Projekt unbeabsichtigt gemischt werden.

**Befund (Code-Analyse, keine Aenderung):** das Projekt nutzt bewusst/faktisch
zwei getrennte, jeweils in sich konsistente Zeit-Domaenen:
1. **Alle Daten** (`created_at`, `api_call_kontingent.monat`, Tages-/Monats-
   grenzen fuer Budgets/Kontingente, Regime-Datum etc.) - durchgehend
   `datetime.now(timezone.utc)`, UTC ueberall. Keine Ausnahme gefunden.
2. **Der APScheduler selbst** (`BackgroundScheduler()` in `scheduler/
   background.py`, siehe `build_scheduler()`) bekommt KEINE explizite
   `timezone=`-Angabe - APScheduler faellt dann automatisch auf die lokale
   Systemzeitzone des ausfuehrenden Rechners zurueck (Windows: aktuell "W.
   Europe Standard/Daylight Time", also Europe/Berlin, UTC+2 im Sommer).
   Alle CronTrigger-Jobs mit fester Uhrzeit (`multi_asset_batch`, `marktscan`
   4/16 Uhr, `backward_tracking` 6:00, `kategorie_synthese` 6:15, `makro_
   analog`/`kategorie_vorschlaege` 6:30, `marktscan_backward_tracking` 7:00)
   sowie alle begleitenden `datetime.now()`-Aufrufe im selben File
   (Staggering, Nachhol-/Misfire-Logik, `next_run_time`) sind konsistent auf
   dieselbe lokale Referenz abgestimmt - kein Mix INNERHALB dieser Domaene.

Die vom Nutzer beobachtete 2h-Differenz ist schlicht der korrekte UTC+2-
Versatz derselben Sommerzeit-Sekunde, ausgedrueckt in zwei unterschiedlichen
Uhren (lokale Job-Anzeige vs. UTC-Log-/DB-Zeitstempel) - keine Fehlfunktion.

**Diskutierte Alternative (explizites Festnageln der Zeitzone im Code,
`zoneinfo`/`pytz`) - bewusst VERWORFEN:** wuerde auf Windows zusaetzlich das
`tzdata`-Paket als neue Abhaengigkeit erfordern, nur um ein Risiko
abzusichern, das im aktuellen Betriebskontext nicht zutrifft: Desktop UND
Notebook werden von derselben Person in derselben echten Zeitzone betrieben,
`multi_asset_batch` (bewusst an Bitpandas reales Quotrix-Handelsfenster
gekoppelt) laeuft dadurch schon heute korrekt zur richtigen Real-Uhrzeit,
ohne dass eine eigene Zeitzone-Funktion noetig waere. Explizites Festnageln
wuerde Komplexitaet fuer einen rein hypothetischen Fall einfuehren.

**Entscheidung:** Code bleibt unveraendert (lokale/Windows-Zeit fuer alle
Scheduler-Trigger, UTC fuer alle Daten) - dieser Nachtrag dokumentiert die
Architektur, damit die 2h-Differenz kuenftig nicht erneut als vermeintlicher
Bug missverstanden wird.

**Wiedervorlage (Beobachtungspunkt, kein festes Datum):** falls jemals eine
dritte Maschine in einer ANDEREN echten Zeitzone hinzukommt, oder falls die
Windows-Zeitzone auf Desktop ODER Notebook versehentlich veraendert wird,
wuerde `multi_asset_batch` lautlos zur falschen Real-Uhrzeit relativ zu
Bitpandas Handelsfenster laufen (keine Fehlermeldung, nur stille
Fehlausrichtung) - dann waere das Festnageln der Zeitzone (siehe verworfene
Alternative oben) neu zu bewerten.

## Nachtrag (2026-08-01): Spot-Verkaufs-Luecke identifiziert + Phase 1 "halte_kriterium scharfschalten" umgesetzt

**Anlass:** breite Root-Cause-Untersuchung (Nutzer-Auftrag, vier parallele
Recherche-Agenten) zu einem am selben Tag empirisch bestaetigten Befund: von
1142 echten Krypto-Spot-Signalen ueber die gesamte Historie gab es **0**
VERKAUFEN-Aktionen (98,2% HALTEN). Root Cause laut Agenten-Berichten NICHT
die deterministischen Gates (auf der Sell-Seite sogar lockerer als beim
Kauf), sondern (a) Prompt-Bias in `agent/krypto/analyst.py` (Regel 7 setzt
fuer Core/These-Kandidaten eine sehr hohe Verkaufs-Huerde, keine Regel
draengt aktiv Richtung Verkauf) und (b) das vom LLM selbst gesetzte
`halte_kriterium` (Regel 17) war bisher rein deskriptiv - nie gegen den
aktuellen Kurs geprueft. Externe Recherche (Disposition Effect vs. Status-
quo-/Endowment-Bias, RL-Trading-Literatur "buy more, sell less", RLHF-
bedingtes Hedging bei LLMs) stuetzt den Befund als bekanntes, dokumentiertes
Muster, kein Einzelfall dieses Projekts.

**Roadmap (mehrstufig, laufender Prozess, keine Einmalaktion):**
1. `halte_kriterium` scharfschalten (dieser Nachtrag) - Infrastruktur-Fix,
   gilt ueber die geteilte `signals`-Tabelle automatisch fuer Spot/Aktien/
   Rohstoffe/Themen-ETF/Hedge.
2. Echte VERKAUFEN-vs-HALTEN-Abwaegung fuer Spot (Regel-27-Aequivalent,
   analog zu Hebel) - noch offen.
3. Ausweitung auf Aktien/Rohstoffe/Themen-ETF (nur noch Prompt-Teil, da
   Infrastruktur ab Schritt 1 mitlaeuft) - noch offen.
4. Z.ai fuer Re-Evaluierungs-Kandidaten, eng gefasst NICHT blanket fuer alle
   HALTEN-Faelle (Kapazitaetsgrund: `MAX_CONCURRENT_REQUESTS=2`, kein
   Tagesdeckel, bereits ein echter 429-Sturm-Vorfall bei geringerem Volumen)
   - noch offen.
5. Separates, spaeteres Thema (vorgemerkt, nicht Teil dieser Runde): Hebel-
   CRV-Pflicht symmetrisch auch fuer TEILVERKAUF/SCHLIESSEN.

**Umsetzung Schritt 1 (2026-08-01):** `database/db.py::get_symbole_mit_
erreichtem_halte_kriterium()` prueft fuer jedes Krypto-Symbol mit letztem
echten HALTEN-Signal, ob `halte_kriterium_ziel_preis_usd/eur` oder
`halte_kriterium_ziel_datum` (Regel 17) mittlerweile erreicht ist - NUR
diese beiden maschinell auswertbaren Felder, `bedingung_text` (Freitext wie
"RSI faellt unter 30") bleibt bewusst aussen vor (kein NLP-Parsing).
Richtungs-Mehrdeutigkeit bei `ziel_preis` (das Prompt-Schema legt nicht
fest, ob ein Kursziel eine Aufwaerts- oder Abwaerts-Schwelle ist) wird
relativ zur eigenen Entry-Zone des Signals aufgeloest. Nutzt ausschliesslich
bereits gecachte Preise (`get_latest_prices()`) - **kein zusaetzlicher
CoinGecko-Kontingent-Verbrauch**.

Ein erreichtes Kriterium loest **keinen automatischen Verkauf** aus, sondern
nur eine schnellere echte Neubewertung: neue, vierte Cooldown-Stufe in
`agent/krypto/signal_batch.py::select_assets_due_for_signal()`
("Re-Evaluierung faellig", `SPOT_COOLDOWN_STUNDEN_RE_EVALUIERUNG=1h`,
config.yaml `spot_cooldown_stunden_re_evaluierung`), Praezedenz VOR dem
bestehenden Kern-Tier - analog zum bereits etablierten Drei-Stufen-Cooldown-
Muster (Kern/Taktisch/Ausgemustert). Verdrahtet in `agent/krypto/
budget_allocator.py` (neuer Aufruf vor `select_assets_due_for_signal()`,
neue Log-Kennzahl "halte_kriterium faellig").

Verifiziert: 10 synthetische Faelle (Aufwaerts-/Abwaerts-Ziel erreicht/
offen, Datum erreicht/offen, kein Kriterium gesetzt, falsche Aktion, fehlende
Entry-Zone, Kern-Symbol) + 2 Cooldown-Praezedenz-Tests (Re-Evaluierung
schlaegt 100h-Cooldown; `None` deaktiviert die Stufe komplett, altes
Verhalten) - alle bestanden. Import-/Config-Parse-Regressionscheck fuer alle
drei geaenderten Dateien bestanden.

**Wiedervorlage:** Schritt 2 (echte Abwaegungs-Regel) als naechster
Roadmap-Schritt, dann 3/4 - jeweils eigene Punkt-fuer-Punkt-Analyse vor der
Umsetzung, kein festes Datum.

**Umsetzung Schritt 2 (2026-08-01): neue Regel 34 "Exit-Abwaegung fuer aktiv
gehaltene taktische Assets OHNE Regel-7-These"** in `agent/krypto/analyst.py`
(SYSTEM_PROMPT, additiv nach Regel 33 eingefuegt, Regel 7/8-Text unveraendert
gelassen). Template/Vorbild war Hebel-Regel 27 ("Action-Bias-Korrektur",
29.07.) - beim genauen Nachlesen von Regel 27 stellte sich heraus, dass diese
tatsaechlich eine ENTRY-seitige Regel ist (ERROEFFNEN/NACHKAUFEN/
HEBEL_ERHOEHEN vs. HALTEN), nicht wie zunaechst angenommen exit-seitig -
Regel 34 ist also ein neues Muster (HALTEN-vs-VERKAUFEN/TAUSCHEN statt
HALTEN-vs-ERROEFFNEN), mechanisch an Regel 27 angelehnt (3 staerkste Argumente
je Seite, "male dir aus, wie es schiefgeht, wenn du bei HALTEN bleibst"-
Formulierung, expliziter Hinweis: keine deterministische Override von
`action`/`confidence_pct`). Gilt NUR fuer den Regel-8-Anwendungsbereich
(aktiv gehaltene taktische Assets ohne Regel-7-These, `asset.
wird_aktuell_gehalten==true`) - Regel 7 (Core/These-Kandidaten) bleibt
unangetastet, dort bleibt die hohe Verkaufs-Huerde bewusst bestehen.

**Verifikation, zwei Stufen:**
1. Klasse 1 (Prompt-Text): Compile/Import/Text-Marker/Regelnummerierung
   1-34 sequenziell - bestanden, ein Formatierungsfehler ("Regel-7- Assets"
   statt "Regel-7-Assets") gefunden und behoben.
2. Echter Live-API-Test (ALT-Prompt = git HEAD vor Regel 34, 33 Regeln, vs.
   NEU = Arbeitskopie mit Regel 34) gegen echte, aktuelle Marktdaten (echter
   `build_facts()`-Payload aus der vollen Pipeline, echte Mistral-API-Calls,
   n=3 je Variante) fuer drei real gehaltene Symbole:
   - **KAIA** (taktisch, Regel-8-scoped, -82,8% Verlust, durchgehend
     bearische Konfluenz): ALT 2/3 HALTEN + 1/3 VERKAUFEN, NEU 3/3
     VERKAUFEN - klare Verschiebung.
   - **ASTER** (taktisch, Regel-8-scoped, -9,9% Verlust, These intakt):
     ALT 3/3 HALTEN, NEU 3/3 HALTEN - KEINE Verschiebung. Wichtiger
     Gegenbefund: Regel 34 ist kein pauschaler Verkaufs-Bias, sondern wiegt
     erkennbar ab - bei moderatem Verlust und intakter These bleibt die
     Empfehlung in beiden Varianten identisch HALTEN.
   - **MORPHO** (core, Regel-7-scoped, +4,7% Gewinn, Kontrollfall): ALT
     3/3 HALTEN, NEU 3/3 HALTEN - Regel 34 greift korrekt NICHT ein, kein
     Uebergriff in den Core-Bereich.

   Alle 18 Live-Calls lieferten valides JSON, kein Retry noetig, keine
   Schema-Verletzung. Rohdaten (facts-Payloads + volle Antworten) im
   Scratch-Verzeichnis der Session archiviert.

**Offene, ehrlich benannte Luecke:** aktuell existiert im echten Portfolio
keine im Gewinn stehende Regel-8-Position (alle taktischen Haltungen sind im
Minus, siehe P&L-Tabelle in der zugehoerigen Session) - ob Regel 34 auch bei
einem profitablen taktischen Halt eine echte Verkaufs-/Tausch-Abwaegung
ausloest (statt nur bei starken Verlusten), bleibt bis zu einem passenden
realen Fall ungetestet.

## Nachtrag (2026-08-01): Spot-Verkaufs-Luecke Roadmap Schritt 3 (Aktien/Rohstoffe/Themen-ETF) + CoinGecko-Tageszaehler

**Anlass Schritt 3:** Ausweitung der Regel-34-Logik (siehe vorheriger Nachtrag)
von Krypto auf die drei anderen Spot-family-Pipelines. Eigene Punkt-fuer-Punkt-
Analyse (Nutzer-Standing-Vorgabe) zeigte: die Roadmap-Annahme "nur Prompt-Teil
noetig, Infrastruktur laeuft schon fuer alle Pipelines mit" war UNVOLLSTAENDIG -
`database/db.py::get_symbole_mit_erreichtem_halte_kriterium()` (Schritt 1) war
hart auf `assetklasse == "krypto"` gefiltert und `agent/multi_asset_batch.py`
hatte nur ein zweistufiges Cooldown-Schema ohne die "Re-Evaluierung faellig"-
Stufe. Auf Nutzer-Entscheidung ("beide mitbauen") wurden Prompt-Teil UND
Cooldown-Erweiterung gemeinsam umgesetzt, nicht nur der Prompt-Teil.

**Umsetzung:**
1. `database/db.py::get_symbole_mit_erreichtem_halte_kriterium()`: neuer
   Parameter `assetklassen: frozenset[str] = frozenset({"krypto"})` - Default
   erhaelt das bestehende Krypto-only-Verhalten (kein Code-Change am
   bestehenden Aufrufer in `budget_allocator.py` noetig). Themen-ETF und Hedge
   teilen sich `assetklasse == "etf"` - die Funktion kennt Hedge-Symbole
   bewusst NICHT (keine agent/-Importe in database/), der Ausschluss passiert
   beim Aufrufer.
2. `agent/multi_asset_batch.py`: `_ist_faellig()` um `re_evaluierung_faellig`-
   Parameter erweitert (Vorrang vor dem bestehenden 2-Stufen-Cooldown, analog
   zu `signal_batch.py`). `run_multi_asset_batch()` berechnet
   `re_eval_symbole` via `get_symbole_mit_erreichtem_halte_kriterium(...,
   assetklassen={"aktien","rohstoffe","etf"})` MINUS Hedge-Symbole
   (`SYMBOL_ZU_HEBEL_FAKTOR`-Set) - Hedge bewusst ausgeschlossen, kein Teil
   dieser Roadmap-Runde.
3. Neue Regel in allen drei SYSTEM_PROMPTs, wortgleiches Muster zu Krypto-
   Regel 34, aber ohne TAUSCHEN (diese drei Pipelines kennen nur 4 Actions:
   KAUFEN/VERKAUFEN/HALTEN/NACHKAUFEN) - Aktien Regel 27, Rohstoff Regel 24,
   Themen-ETF Regel 22 (jeweils direkt nach der letzten bestehenden Regel,
   additiv). Gilt jeweils nur fuer Regel-6-Assets OHNE These (das
   Regel-7-Aequivalent dieser drei Pipelines ist dort Regel 6).
4. Empirischer Befund aus der Vor-Analyse (read-only DB-Query): Rohstoffe
   und Themen-ETF hatten zum Zeitpunkt der Analyse 0 Signale ueberhaupt in
   der DB - beide Pipelines liefen bislang nicht produktiv. Aktien 8/8
   Signale HALTEN (Stichprobe zu klein fuer eine eigene Aussage). Die neue
   Regel wirkt also bei Rohstoffen/Themen-ETF zunaechst nur "auf Vorrat",
   bis diese Pipelines echte Produktivlaeufe haben.

**CoinGecko-Tageszaehler (zusaetzlich, Nutzer-Nachfrage nach ungewoehnlich
hohem Verbrauch):** neue Tabelle `api_call_kontingent_taeglich` (additiv,
gleiche Schreibstelle wie der bestehende Monats-Zaehler in
`increment_api_call_counter()` - kein zweiter Fehlerpunkt). Neue Funktion
`get_api_call_counter_taeglich()`. Remote-Status-Karte "CoinGecko-Kontingent"
zeigt jetzt zusaetzlich "davon heute". Macht kuenftig sichtbar, an welchem
Tag der Verbrauch tatsaechlich ansteigt - vorher war das nur ueber den
Monats-Gesamtwert rekonstruierbar.

**Verifikation (Klasse 1 + synthetisch):**
- Compile/Import aller 7 geaenderten Dateien bestanden.
- Regelnummerierung 1..N sequenziell fuer alle drei SYSTEM_PROMPTs bestanden
  (Aktien bis 27, Rohstoff bis 24, Themen-ETF bis 22), kein TAUSCHEN-Leck in
  den neuen Regeln.
- `get_symbole_mit_erreichtem_halte_kriterium()`: synthetischer Test mit
  gemischter Watchlist (Aktien+Krypto) bestaetigt Default (krypto-only),
  Aktien-Scope und kombinierten Scope korrekt.
- `_ist_faellig()`: 4 synthetische Faelle (Re-Eval-Vorrang trotz frischem
  Signal, bestehende Cooldown-Logik unveraendert, kein Signal -> faellig)
  bestanden.
- `run_multi_asset_batch()`: echter Trockenlauf gegen eine frische Test-DB
  mit echter Watchlist (13 Multi-Asset-Symbole), `coingecko_client=None`/
  `mistral_client=None`/`gemini_client=None` - lief ohne Absturz durch, alle
  Kandidaten korrekt als faellig erkannt.
- CoinGecko-Tageszaehler: synthetischer Increment-Test bestaetigt Monats-
  UND Tages-Zaehler laufen parallel korrekt hoch, `init_db()` bleibt bei
  wiederholtem Aufruf idempotent.

**Wiedervorlage:** Schritt 4 (Z.ai fuer Re-Evaluierungs-Kandidaten, eng
gefasst) als naechster Roadmap-Schritt, jeweils eigene Punkt-fuer-Punkt-
Analyse davor. Rohstoff/Themen-ETF-Wirkung der neuen Regel kann erst
beurteilt werden, sobald diese Pipelines echte Produktivdaten haben.

## Nachtrag (2026-08-01): Spot-Verkaufs-Luecke Roadmap Schritt 4 (Z.ai-Re-Evaluierungs-Anzeige) - Roadmap-Praemisse korrigiert VOR dem Bau

**Wichtig, dieser Abschnitt ERGAENZT den vorherigen Nachtrag (Schritt 3) -
nichts davon wurde geloescht oder ueberschrieben. Zweck: nachvollziehbare
Historie, was wann geaendert wurde.**

**Urspruengliche Roadmap-Annahme (aus der Wiedervorlage oben):** "Z.ai fuer
Re-Evaluierungs-Kandidaten, eng gefasst" - implizierte NEUE Z.ai-Calls
speziell fuer Symbole, bei denen das eigene `halte_kriterium`/Regel 17
erreicht wurde.

**Pre-Build-Analyse (Nutzer-Standing-Vorgabe, hier durch einen Analyse-Agenten
durchgefuehrt) ergab: diese Annahme war FALSCH.** `agent/krypto/
gegenpruefung.py::fuehre_beide_calls_im_hintergrund()` ruft Z.ai bereits
IMMER auf - fuer jedes Signal, jede Action, inklusive HALTEN (einziges Gate
projektweit: `if zai_client is not None`, identisch in allen 6 Pipelines).
Neue Calls speziell fuer Re-Evaluierungs-Kandidaten waeren also (a) reine
Redundanz und (b) ein Risiko, exakt den Z.ai-429-Sturm-Vorfall (27./28.07.,
siehe `api/zai.py`-Modul-Kommentare Zeile 30-42) zu wiederholen, den das
Projekt bereits einmal live hatte.

**Der eigentliche, reale Gap:** `_notify_spot_signal()`
(`scheduler/background.py:1582`) verschickt fuer `action == "HALTEN"` NIE
eine E-Mail - Z.ais bereits vorhandene, unabhaengige Richtungseinschaetzung
(`zai_eigene_richtung`) fuer die kleine Teilmenge der "Re-Evaluierung
faellig"-HALTEN-Faelle war also nur in der App sichtbar, dort aber nicht von
den 98%+ routinemaessigen HALTEN-Faellen unterscheidbar (`abgleich_text`
zeigte in beiden Faellen generisch "unklar", weil `zai_uebereinstimmung`
fuer HALTEN strukturell immer `None` ist - `richtung_aus_action()` gibt fuer
HALTEN bewusst `None` zurueck, siehe Modul-Docstring).

**Korrigierter, deutlich kleinerer Umfang (vom Nutzer bestaetigt: "ja, passt
so - bau es"):** rein GUI-seitige Datensichtbarkeit, KEINE neuen Z.ai-Calls,
KEINE E-Mail-Aenderung (HALTEN erreicht den E-Mail-Pfad ohnehin nie).

**Umsetzung:**
1. Neues Flag `war_re_evaluierung_faellig: bool = False` auf `Signal`
   (NICHT auf `HebelSignal` - Hebel hat kein `halte_kriterium`-Aequivalent).
   Muss zur GENERIERUNGSZEIT persistiert werden, nicht nachtraeglich
   ableitbar, weil `get_symbole_mit_erreichtem_halte_kriterium()` nur den
   AKTUELLEN Kurs/die aktuelle Watchlist kennt - eine rueckwirkende
   Berechnung anhand eines gespeicherten Signals waere nicht mehr moeglich.
2. `database/db.py`: additive Migration `_migrate_signal_re_evaluierung_
   faellig_column()` (eigene, von der Schritt-3-Migration unabhaengige
   Funktion - beide Features entstanden unabhaengig voneinander), Spalte
   in `_SIGNAL_COLUMNS`/Bool-Cast in `insert_signal()`/`_row_to_signal()`
   aufgenommen.
3. Alle vier Spot-family-`generate_signal()`-Funktionen (Krypto/Aktien/
   Rohstoffe/Themen-ETF) um Parameter `war_re_evaluierung_faellig: bool =
   False` erweitert, an die jeweilige `Signal(...)`-Konstruktion
   durchgereicht.
4. Aufrufer-Wiring: `agent/krypto/budget_allocator.py` (Tier-3-Spot-
   Rotation, beide Provider-Lambdas) nutzt das bereits vorhandene
   `re_evaluierung_faellig`-Set (Zeile ~517). `agent/multi_asset_batch.py`
   nutzt das in Schritt 3 bereits berechnete `re_eval_symbole`-Set - dort
   ueber `extra_kwargs` durchgereicht, bewusst NUR fuer Nicht-Hedge-Symbole
   (Hedge-`generate_signal()` kennt den Parameter nicht, hat kein
   `halte_kriterium`-Aequivalent).
5. `ui/formatting.py::format_zai_gegenpruefung_lines()`: neuer optionaler
   Parameter `war_re_evaluierung_faellig: bool = False`. Wenn gesetzt UND
   `zai_uebereinstimmung is None` (der HALTEN-Regelfall), zeigt
   `abgleich_text` jetzt "Re-Evaluierung fällig - unabhängige Einschätzung
   beachten" statt des generischen "unklar" - Faelle mit `ja`/`nein`
   bleiben unveraendert (das Flag greift nur, wenn sonst nichts Konkreteres
   vorliegt). `ui/signals_view.py` reicht `signal.war_re_evaluierung_
   faellig` durch; `ui/hebel_view.py` braucht KEINE Aenderung (Default
   `False` gilt automatisch, `HebelSignal` hat das Feld nicht).

**Bewusster Scope-Cut (identisch zur urspruenglichen Nutzer-Vorgabe):**
keine E-Mail-Template-Aenderung (unerreichbarer Pfad fuer HALTEN), keine
neuen Z.ai-Calls, keine Aenderung an `zai_uebereinstimmung`-Berechnung
selbst - reine Anzeige-Verbesserung fuer bereits vorhandene Daten.

**Verifikation (Klasse 1 + synthetisch):**
- Compile/Import aller 10 beruehrten Dateien bestanden.
- DB-Round-Trip-Test: `war_re_evaluierung_faellig=True`/`False` ueberleben
  `insert_signal()`/`get_latest_signal()` korrekt (bool-Cast in beide
  Richtungen bestaetigt).
- `format_zai_gegenpruefung_lines()`: 4 synthetische Faelle bestanden -
  (1) routinemaessiges HALTEN ohne Flag -> "unklar" unveraendert, (2) Flag
  gesetzt + `zai_uebereinstimmung=None` -> neues Label, (3) Flag gesetzt
  ABER `zai_uebereinstimmung="ja"` -> "stimmt überein" bleibt unveraendert
  (Flag ueberschreibt keine konkrete Uebereinstimmung), (4) Alt-Aufruf ohne
  den neuen Parameter (Hebel-Muster) -> unveraendertes Verhalten, volle
  Rueckwaertskompatibilitaet bestaetigt.

**Wiedervorlage:** wie bei Schritt 3 - erst nach einigen Wochen echter
Produktivdaten laesst sich beurteilen, ob die Re-Evaluierung-faellig-
Kennzeichnung in der Praxis zu besseren HALTEN-Entscheidungen fuehrt oder
nur Anzeige-Rauschen bleibt. Hebel-CRV-Pflicht-Symmetrie (urspruenglich
Roadmap-Punkt 5) bleibt separates, noch nicht begonnenes Thema.

## Nachtrag (2026-08-01): CoinGecko-Kontingent-Tiefenanalyse - Marktscan USD-only, JIT-Refresh-Drossel bewusst unveraendert gelassen

**Anlass:** Nutzer-Beobachtung anhand eines frischen Notebook-Exports -
Remote-Statusseite zeigte "CoinGecko-Kontingent diesen Monat: 353/10.000
(3,5%), davon heute: 30", Nutzer-Projektion "kommen locker bis Tagesende
auf ca. 400" -> bei diesem Tempo waere das Monatskontingent in ~20-25 Tagen
erschoepft. Auftrag: genau aufschluesseln, wann wer eine CoinGecko-Abfrage
ausloest, u.U. einschraenken.

**Vorab gefundene Export-Luecke:** `extract_notebook_diagnose.py` exportierte
die `api_call_kontingent[_taeglich]`-Tabellen (siehe [[project_coingecko_kontingent_tracking]])
bisher NICHT - nur die Remote-Statusseite zeigte sie live. Neue Funktion
`_coingecko_kontingent(conn)` (liest Monatszaehler + volle Tageshistorie),
neuer Payload-Key `coingecko_kontingent`. Synthetisch verifiziert (DB-
Roundtrip-Test). Kuenftige Verbrauchsanalysen brauchen damit keine Log-
Archaeologie mehr.

**Vollstaendige Call-Site-Landkarte** (jede Methode in `api/coingecko.py`,
die tatsaechlich `_get()` aufruft, gegen alle Aufrufer im Code geprueft):
- Fixer Boden (~223/Tag, siehe [[project_coingecko_kontingent_tracking]]):
  `refresh_prices_job` (96/Tag, 1 gebuendelter Call), `refresh_history_job`
  (114/Tag, 57 Watchlist-Coins × 2 Waehrungen, NICHT gebuendelt),
  `marktscan_backward_tracking_job` (~10/Tag). `coingecko_quota_check_job`
  kostet NICHTS (reiner Lesecheck gegen den lokalen Zaehler, verifiziert
  gegen `scheduler/background.py:897-912`).
- Marktscan (`agent/krypto/marktscan.py::run_scan()`, fest 2×/Tag um 04:00/
  16:00 Uhr, cron): `fetch_top_gainers()` 5 Calls + `get_trending()` 1 Call
  (Fixkosten je Lauf) + 1 `get_simple_prices()`-Call je Trending-Coin
  ausserhalb der Top-Gainer + 2 `backfill_history()`-Calls (USD+EUR, Default)
  je Stufe-A-Ueberlebendem (`_try_backfill_snapshot()`) + 1 `get_coin_ath_
  change_percentage()`-Call je jungem Stufe-A-Ueberlebenden.
- JIT-Historie-Refresh (`agent/krypto/pipeline.py::jit_refresh_asset_
  historie()`, ausgeloest bei JEDER echten Signal-Generierung in Krypto-Spot
  UND Hebel, 60-Min-Drossel je Symbol): 1 `get_market_chart`-Call (USD-only)
  pro nicht gedrosseltem Trigger.

**Backtest 1 (`backtest_coingecko_marktscan_kosten.py`, neu, 38 echte
Marktscan-Laeufe 09.07.-01.08., liest `rohdaten_fuer_backtest.marktscan_
alle_kandidaten`):**
- Baseline (aktuell): Ø 52,3 Calls/Tag, aber fetter Schwanz - ein einzelner
  Lauf am 09.07. mit 51 Stufe-A-Ueberlebenden kostete allein 197 Calls.
- USD-only: Ø 42,2 Calls/Tag (-19,2%), gleichmaessige Ersparnis unabhaengig
  von der Tagesform.
- USD-only + Top-N-Deckel (N=5/10/15): zusaetzliche Ersparnis nur marginal
  (Deckel griff in nur 1-8 von 38 Laeufen), aber genau dort, wo es zaehlt -
  der 09.07.-Ausreisser waere mit Top-5 auf ~103 statt 197 Calls gefallen.
  NICHT umgesetzt (kein eindeutiger Fall wie bei USD-only, echter Kompromiss
  zwischen Kontingent-Sicherheit und Marktscan-Abdeckung, siehe unten).
- Uebernahmequote als Begruendung fuer USD-only: `kandidaten_warteschlangen_
  status.marktscan_candidates` zeigt 1701 "neu", nur 7 "nutzer_behalten_
  manuell_uebernommen" (~0,4%). EUR-Historie wird fuer 99,6% der Kandidaten
  nie gebraucht; selbst im seltenen Uebernahme-Fall holt der naechste
  taegliche `refresh_history_job` die fehlende EUR-Historie automatisch nach
  (max. 24h Verzoegerung, kein Kaltstart-Risiko). Doppelt gegengeprueft, dass
  EUR-Historie fuer Marktscan-Kandidaten SONST NIRGENDS gelesen wird (weder
  `_try_backfill_snapshot()` noch `generate_candidate_writeup()` - beide
  nutzen nur `closes`/USD; der im Prompt gezeigte EUR-Preis kommt aus dem
  bereits kostenlosen Discovery-Snapshot `candidate.price_eur`, nicht aus der
  Historie).
- **Umgesetzt:** `_try_backfill_snapshot()` ruft `backfill_history(...,
  currencies=("usd",))` statt Default. Synthetisch verifiziert (Mock-Test
  bestaetigt nur-USD-Aufruf).

**Backtest 2 (JIT-Refresh, gegen echte heutige Signal-Zeitstempel aus
`spot_signals`/`hebel_signals` - 71 Spot- + 21 Hebel-Signale, 43 betroffene
Symbole):** heutiger Marktscan-Beitrag war mit nur 46 Calls (2 Laeufe)
UNTERDURCHSCHNITTLICH klein - entgegen der ersten Arbeitshypothese war
Marktscan heute NICHT der Haupttreiber. Rekonstruktion der 60-Min-Drossel
ergab ~88 JIT-Calls heute - schliesst die Luecke zwischen Fixboden+Marktscan
(223+46=269) und dem beobachteten Gesamtwert (353) fast exakt. JIT-Refresh
war der eigentliche Haupttreiber des Tages.

Drossel-Fenster durchgerechnet: 60 Min (aktuell) 88 Calls, 2h 82, 4h 75, 6h
72, 8h 72 (Plateau), 12h 45. Kein sauberer Hebel wie bei Marktscan: bis 6-8h
sinkt die Zahl nur um ~18%, weil die meisten der 43 Symbole ohnehin nur 1-2×/
Tag real bewertet werden (bestehende 8h/15h-Cooldowns greifen schon) - die
60-Min-Drossel ist meist gar nicht die begrenzende Groesse. Ein spuerbarer
Sprung kommt erst bei 12h, aber `_bucket_prices_by_date()`
(`api/history.py:30`) haelt bewusst den LETZTEN Intraday-Preis pro Tag -
jeder JIT-Call refresht "heute" auf einen aktuelleren Kurs (RSI/MACD-Basis).
Eine Verlaengerung waere also ein echter Signalqualitaets-Kompromiss, keine
reine Redundanz-Eliminierung wie bei der Marktscan-EUR-Frage.

**Nutzer-Entscheidung:** JIT-Drossel unveraendert lassen (Empfehlung
gefolgt - Ersparnis/Risiko-Verhaeltnis lohnt sich nicht), Marktscan USD-only
umsetzen (risikofrei, hilft an Ausreisser-Tagen deutlich).

**Ehrliches Gesamtbild:** die "20-Tage"-Sorge ist mit den geprueften Hebeln
NICHT grundlegend geloest - an einem JIT-lastigen Tag wie dem 01.08. bringt
USD-only nur eine kleine Ersparnis (~9 von 353 Calls), weil Marktscan an
diesem Tag klein war. Der Nutzen zeigt sich vor allem an Marktscan-lastigen
Ausreisser-Tagen. Der neue Tageszaehler-Export ermoeglicht ab jetzt
lueckenlose Beobachtung ohne erneute Log-Archaeologie.

**Verifikation:** Compile aller 2 geaenderten Dateien (`extract_notebook_
diagnose.py`, `agent/krypto/marktscan.py`) + neues `backtest_coingecko_
marktscan_kosten.py`. Synthetische Tests: `_coingecko_kontingent()` DB-
Roundtrip (Monats+Tageszaehler korrekt gelesen), `_try_backfill_snapshot()`
Mock-Test (bestaetigt USD-only-Aufruf). Backtests liefen gegen echte
Produktivdaten aus dem Notebook-Export (read-only, keine Schreiboperation
gegen die Produktions-DB, siehe [[feedback_desktop_kein_produktivstart]]).

**Wiedervorlage:** neuer Tageszaehler-Export beobachten, sobald mehrere
Tage/Wochen echter Daten vorliegen erneut pruefen, ob Marktscan-USD-only
allein ausreicht oder ein Top-N-Deckel doch noetig wird (Backtest-Skript
bleibt fuer eine erneute Auswertung nutzbar).

## Nachtrag (2026-08-01, spaeter am selben Tag): Marktscan Top-N-Deckel umgesetzt + "unbekannte Aufrufe" geklaert

**Anlass:** frischer Notebook-Export (21:35 Uhr) zeigte den Verbrauch weiter
steigend, Nutzer-Entscheidung nach Ruecksprache: "wir werden einen Deckel
brauchen sonst wird es kritisch" - der oben dokumentierte USD-only-Fix allein
reicht nicht, wenn JIT-Refresh (nicht Marktscan) der Haupttreiber eines Tages
ist. Zusaetzliche Nutzerfrage: was sind die "unbekannten Aufrufe" aus dem
vorherigen Nachtrag?

**Klaerung "unbekannte Aufrufe":** die ATH-Abstand-Calls (`get_coin_ath_
change_percentage()`) fuer junge Stufe-A-Ueberlebende - das Kandidaten-Alter
wird nirgends dauerhaft gespeichert, daher nicht exakt rekonstruierbar (nur
nach oben begrenzt durch die Anzahl Stufe-A-Ueberlebender). Zusaetzlich
geprueft und AUSGESCHLOSSEN als versteckte Mehrfach-Call-Quelle: `hebel_
screening_job` nutzt kein CoinGecko (Binance/Bybit/OKX/Kraken), `/global`
(BTC-Dominanz) ist bereits auf 1×/Tag gecacht (Schritt-0-Fix, `agent/krypto/
pipeline.py::_update_macro_snapshot()`). Abgleich mit dem frischen Export
(21:32 Uhr, 90% des Tages): das rekonstruierte Modell (Fixboden+Marktscan+
JIT) kam auf ~348 Calls, LIEGT UNTER dem bereits um 18:47 Uhr real
beobachteten Wert 353 - das Modell untertreibt den echten Verbrauch leicht
(ATH-Checks + moeglicher weiterer kleiner Rest). Genau deshalb ist ein
Deckel der pragmatischere Weg als jede Quelle perfekt zu attribuieren: er
begrenzt die groesste, beherrschbare variable Quelle hart, unabhaengig davon
ob jede letzte Call-Quelle bekannt ist.

**Umgesetzt:** `agent/krypto/marktscan.py::run_scan()` umstrukturiert in
zwei Durchlaeufe - ein Vorpass ermittelt fuer alle Stufe-A-Ueberlebenden
eine guenstige Vorab-Note (`score_fundamental()` + `score_momentum(...,
ath_change_pct=None)`, KEIN externer Call, nutzt nur bereits vorhandene
Discovery-Daten), nur die `config.yaml marktscan.stufe_b_top_n_deckel`
(=10, Nutzer-Wahl) besten davon bekommen danach `_try_backfill_snapshot()`
+ ATH-Check. Nicht ausgewaehlte Ueberlebende durchlaufen die Klassifikation
trotzdem (bleiben als Kandidat sichtbar, kein Datenverlust) - mit
degradiertem Score (kein `snapshot`/`ath_change_pct`), EXAKT derselbe
Code-Pfad wie ein heute schon existierender fehlgeschlagener Backfill
(kein neuer Sonderfall). `top_n=None`/Schluessel entfernen = unveraendertes
Alt-Verhalten.

**Backtest-Update (`backtest_coingecko_marktscan_kosten.py`, erweitert um
Top-N-Varianten, gegen dieselben 38 echten Laeufe):** Top-10-Deckel zusaetzlich
zu USD-only: Ø 40,1 Calls/Tag (-23,4% ggu. Baseline), Deckel griff nur in
1/38 Laeufen (2,6%) - normale Tage bleiben praktisch unveraendert, der
09.07.-Ausreisser (51 Ueberlebende, 197 Calls in einem Lauf) waere auf einen
Bruchteil gekappt worden.

**Verifikation:** Compile bestanden. Synthetischer Test (15 synthetische
Stufe-A-Kandidaten, gemockter `backfill_history()`/`get_coin_ath_change_
percentage()`): Top-5-Deckel -> genau 5 Backfill- UND 5 ATH-Calls (dieselben
5 Coins fuer beide, korrekt gekoppelt), alle 15 Kandidaten trotzdem
gespeichert. Default aus config.yaml (10) bestaetigt. `top_n=None` ->
alle 15 bekommen Backfill (Alt-Verhalten unveraendert, Regressionscheck
bestanden).

**Ehrliches Fazit bleibt bestehen:** der Deckel wirkt gezielt gegen
Marktscan-Ausreisser-Tage, loest aber nicht die JIT-Refresh-lastigen Tage
(bewusst unangetastet, siehe vorheriger Nachtrag - Signalqualitaets-
Kompromiss). Der neue Tageszaehler-Export bleibt der Weg, um zu beobachten,
ob beide Massnahmen zusammen ausreichen oder weitere Schritte noetig werden.

## Nachtrag (2026-08-01): Hebel-CRV-Pflicht-Symmetrie (Spot-Verkaufs-Luecke Roadmap-Punkt 5) - Praemisse geprueft und verworfen, KEIN Code-Change

**Anlass:** letzter offener Punkt der Spot-Verkaufs-Luecke-Roadmap (siehe
[[project_spot_verkaufs_luecke_roadmap]]) - urspruengliche Idee: die CRV-
Pflicht (Chance-Risiko-Verhaeltnis, Mindestschwelle `CRV_MINIMUM`=2.0) soll
bei Hebel-TEILVERKAUF/SCHLIESSEN symmetrisch zur bereits umgesetzten Spot-
Spiegelung gelten (siehe Nachtrag Zeile ~10519, VERKAUFEN/TAUSCHEN, Task
#522/#523).

**Recherche-Befund:** `agent/krypto/hebel_risk_gate.py::post_check_hebel()`
- der CRV-Gate-Block (~Zeile 1056-1078) feuert NUR fuer `_HEBEL_ACTIONS_MIT_
HEBEL = ("ERÖFFNEN", "NACHKAUFEN", "HEBEL_ERHÖHEN")`. `HEBEL_SENKEN` ist
bereits EXPLIZIT von der CRV-Pflicht ausgenommen (~Zeile 1035-1036, Docstring-
Zitat: "eine Risikoreduktion braucht keine Chance-Risiko-Rechtfertigung").
`TEILVERKAUF`/`SCHLIESSEN` stehen in KEINER der beiden Listen - fuer sie
laeuft im gesamten `post_check_hebel()` bereits heute kein einziger CRV-
Check, weder fuer originaere LLM-Empfehlungen noch fuer die Kontrathese-
uebersetzten Faelle (Zeile 921-964, setzt `action` direkt auf SCHLIESSEN/
TEILVERKAUF).

**Fachliche Pruefung (Nutzer-Bitte um Experten-Einschaetzung, da nicht
selbst entscheidbar):** die Spot-CRV-Pflicht bei VERKAUFEN/TAUSCHEN
behandelt den Verkauf wie eine eigene gerichtete Wette und verlangt dieselbe
Qualitaetsschwelle wie bei einer Neu-Eroeffnung - sicher bei Spot, WEIL die
Rueckfalloption (HALTEN bei zu schwachem CRV) selbst risikofrei ist (kein
Liquidationsrisiko, keine Finanzierungskosten). Bei einer offenen Hebel-
Position ist die Rueckfalloption HALTEN NICHT risikofrei - sie bedeutet
weiterlaufendes Liquidationsrisiko und Funding-Kosten. Eine CRV-Pflicht, die
ein schwaches TEILVERKAUF/SCHLIESSEN-Signal zu HALTEN zurueckstuft, wuerde
die Position trotz LLM-Empfehlung zur Reduktion exponiert lassen - das Risk-
Gate wuerde damit paradoxerweise MEHR Risiko erzwingen statt zu verhindern.
Exakt dieselbe Logik, die HEBEL_SENKEN bereits von der CRV-Pflicht ausnimmt -
TEILVERKAUF/SCHLIESSEN sind strukturell dasselbe (Risikoreduktion/-abbau),
kein neuer gerichteter Einsatz.

**Ergebnis:** die urspruengliche Roadmap-Praemisse ("symmetrisch zu Spot")
ging von einem Modell aus, in dem HALTEN immer der sichere Rueckfall ist -
das stimmt bei Spot, aber nicht bei Hebel, wo die Position selbst das
Risiko traegt. Der bestehende Zustand (keine CRV-Pflicht bei TEILVERKAUF/
SCHLIESSEN) ist bereits korrekt - **kein Code-Change noetig**, reine
Verifikation + Dokumentation der Begruendung (Muster [[feedback_document_rejected_options]]:
verworfene Optionen mit Grund dokumentieren).

**Damit ist die Spot-Verkaufs-Luecke-Roadmap (5 Punkte) vollstaendig
abgeschlossen** - Schritte 1-4 umgesetzt+committet, Punkt 5 geprueft und
als bereits korrekt bestaetigt.

## Nachtrag (2026-08-02): Dead-Loop-Synthese (Task #598) - Gliederung, Root-Cause-Analyse, Massnahme 1 umgesetzt

**Auftrag (Task #598):** "Root-Cause-Analyse warum Kalibrierung/Erfolgsmessung
systemweit an n<15 haengt, priorisierte Massnahmen zur Beschleunigung
vorschlagen." Auf Nutzer-Wunsch zunaechst die Gliederung aus Memory + Task
#598 rekonstruiert (keine fruehere schriftliche Fassung vorhanden), dann die
vollstaendige Root-Cause-Analyse erstellt, bevor mit einzelnen Massnahmen
begonnen wurde.

### Gliederung (4 Gruppen, entlang der Signal-Pipeline)

- **A. Deterministische Stufe (Regler/Gates):** CRV-Mindestschwelle,
  Enger-Stop-Loss/ATR-Regeln, R-5.10-Konfidenzschwelle, Risikofaktoren-
  Haeufung, Backward-Tracking-Fristen - das "Regler"-Thema. Groesstenteils
  bereits mehrfach untersucht (siehe [[project_enge_stop_loss_backtest_und_massnahmen]],
  [[project_r510_konfidenz_veto_analyse_29_07]]).
- **B. LLM1/Analyst-Stufe:** Konfidenz-Kalibrierung, historische
  Trefferquote-Fakt, Fazit-Selbsteinschaetzung (LLM sagt fast nie "ja"), UND
  strukturell ungueltige LLM-Antworten ("Agent-Antwort ungueltig", 3
  Versuche, dann Verwurf) - bis 02.08. komplett unquantifiziert, siehe
  Massnahme 1 unten.
- **C. LLM2/Z.ai-Gegenpruefung-Stufe:** Konsistenz-Check + Richtungs-
  Abgleich, Deribit-Cross-Check, Coverage je Assetklasse. Groesstenteils
  "Phase 1, rein beobachtend"; ein Sonderfall (Z.ai-Richtungs-"Abweichung")
  ist bereits strukturell durch `hebel_richtung_modus=nur_long` erklaert,
  kein Kalibrierungsproblem.
- **D. Cross-Cutting/Meta-Infrastruktur:** die n-Schwelle selbst (n≥15 →
  n≥50 + Symbol-Konzentrations-Check, fuer Korrelationsfragen real eher
  n≈340+, siehe [[reference_test_und_verifikationsmethodik]] Abschnitt 2.5)
  sowie mehrere ruecklaeufig erklaerende Infra-Bugs, die ueber Wochen fast
  jede Stichprobe klein gehalten haben, bevor sie gefixt wurden (siehe unten,
  RC1).

### Sechs Root-Cause-Kategorien

1. **RC1 - Ruecklaeufige Infra-Bugs:** `_is_superseded()`-Bug (Fix 19.07.,
   siehe [[project_selbstverifikation_ki_trimmen]]) hat fast jedes offene
   Signal durch ein neueres HALTEN vorzeitig "ueberholt", bevor es TP/SL
   erreichen konnte. Dazu ein verpasster Cron-Job (Fix 17.07.) und das
   Veto-Schatten- (seit 28.07.) bzw. Selbst-Halten-Schatten-Tracking (seit
   31.07.), die vorher schlicht nicht existierten. Ein Grossteil der
   aktuell kleinen Stichproben ist erst seit 1-3 Wochen ueberhaupt messbar.
2. **RC2 - Bewusste Durchsatz-Bremsen:** `hebel_richtung_modus=nur_long`,
   Multi-Asset-Batch nur 2x/Tag, Regel-27-Action-Bias-Korrektur (HALTEN als
   Normalfall) - alle drei korrekt so, schrumpfen aber den Nenner
   messbarer Trade-Outcomes.
3. **RC3 - Messlatte war anfangs zu niedrig:** n≥15 war ein willkuerlicher
   Schwellenwert, spaeter auf n≥50+Konzentrations-Check verschaerft; fuer
   Korrelationsfragen liegt der reale Bedarf bei n≈340+.
4. **RC4 - Viele Messebenen sind schlicht neu:** Marktscan-Erfolgsmessung
   (seit 30.07.), Selbst-Halten-Schatten (seit 31.07.), Z.ai-Abdeckung
   Nicht-Krypto (seit 29.07.) - hier ist Abwarten die einzig korrekte
   Antwort.
5. **RC5 - Enge Watchlist erzeugt Pseudo-Unabhaengigkeit:** dieselbe
   Handvoll Symbole (AIOZ, INJ, KAIA, KAITO, CAT...) erscheint ueber
   Cooldown-getriebene Re-Signale wiederholt - n waechst schneller als
   echte unabhaengige Beobachtungen.
6. **RC6 - LLM1-Validierungsfehler waren komplett unquantifiziert** (siehe
   Massnahme 1).

### Priorisierte Massnahmen (Uebersicht)

1. Systematische Auswertung der LLM1-Validierungsfehler (RC6) - **umgesetzt,
   siehe unten**.
2. Wiedervorlage-Bedingungen aus [[reference_offene_zeitbasierte_beobachtungspunkte]]
   mit Zeitschaetzung versehen (RC1/RC4) - naechster Schritt.
3. Vor-01.08.-Befunde gegen die neue n≥50-Regel nachpruefen (RC3).
4. Durchsatz-Bremsen (RC2) an einer Stelle explizit als Trade-off
   dokumentieren.
5. Pruefen, ob Multi-Asset-Batch-Frequenz erhoeht werden kann (RC2), jetzt
   wo Mistral/Gemini/Z.ai kein reales Budget-Limit mehr haben.

### Massnahme 1 umgesetzt: LLM1-Validierungsfehler quantifiziert + 2 von 3 Fehlerklassen behoben

**Auswertung (frischer NB-Export 02.08. 06:49, `spot_signals`+`hebel_signals`
roh ausgewertet, 14.07.-02.08., 19 Tage):** 27 "Agent-Antwort ungueltig"-
Faelle von 3522 Signal-Generierungen insgesamt (0,77%) - absolut zu klein,
um irgendeinen n<15-Thread spuerbar zu beschleunigen (RC6 damit deutlich
abgeschwaecht gegenueber der urspruenglichen Vermutung). Drei Fehlerklassen
erklaeren 24/27 (89%):

| Klasse | n | Root Cause |
|---|---|---|
| Preiszonen-Vertauschung (`von>bis`) | 12 (44%) | LLM liefert Ober-/Untergrenze gelegentlich vertauscht |
| `eigene_einschaetzung`-Pflichtfeld fehlt | 7 (26%) | LLM laesst das Objekt komplett weg |
| `top_gruende.kategorie` ungueltig | 5 (19%) | 100% Rohstoff/Themen-ETF: Schema verlangt "positionierung"/"sektor", `long_reasoning` nennt dieselbe Dimension aber durchgaengig "fundamental" (Prompt-interner Widerspruch) |

**Kritische Gegenpruefung vor Umsetzung (Nutzer-Vorgabe):** urspruenglich
erwogen, `long_reasoning.fundamental` in Rohstoff/Themen-ETF-Prompts auf
`positionierung`/`sektor` umzubenennen. Verworfen: `long_reasoning_
fundamental=long_reasoning.get("fundamental")` ist in allen 6 `pipeline.py`-
Dateien fest verdrahtet (gemeinsame DB-Spalte `long_reasoning_fundamental`
ueber alle Assetklassen, siehe `database/models.py`) - eine Umbenennung
haette das Feld fuer jedes kuenftige Rohstoff/Themen-ETF-Signal
stillschweigend geleert. Fix daher auf den `top_gruende.kategorie`-
Validator beschraenkt (per Grep bestaetigt: "positionierung"/"sektor"
werden sonst nirgends hart verglichen). Die Zonen-Tausch-Logik wurde gegen
`risk_gate.py`s CRV-Berechnung gegengeprueft: dort wird `von`/`bis` bei der
CRV-Berechnung ausschliesslich nach numerischer Lage gewaehlt (nicht nach
LLM-Reihenfolge) - ein Tausch stellt exakt die bereits vorausgesetzte
Invariante her, kein Eingriff in die vom LLM gelieferten Preiswerte.

**Umgesetzt (verifiziert per `py_compile` + synthetischen Tests, 5/5 PASS
inkl. Negativtest fuer echte ungueltige Kategorien):**
- `agent/krypto/analyst.py`, `agent/krypto/hebel_analyst.py`,
  `agent/aktien/analyst.py`, `agent/rohstoff/analyst.py`,
  `agent/themen_etf/analyst.py`, `agent/hedge/analyst.py`: `von>bis` wird
  jetzt getauscht statt die Antwort zu verwerfen (identischer Fix in allen
  6 Kopien, Option-B-Konvention dieses Projekts).
- `agent/rohstoff/analyst.py`, `agent/themen_etf/analyst.py`:
  `top_gruende.kategorie="fundamental"` wird vor der Pruefung auf
  `"positionierung"`/`"sektor"` normalisiert statt abgelehnt.

**Bewusst nicht umgesetzt:** `eigene_einschaetzung`-Pflichtfeld-Fix (7
Faelle, 0,2% aller Versuche) - ein Prompt-Eingriff waere unverifiziert
(siehe eigene Erfahrung 31.07. in [[project_enge_stop_loss_backtest_und_massnahmen]]:
"Lauf-zu-Lauf-Streuung bei Prompt-Aenderungen oft groesser als der Effekt")
und bei dieser Fallzahl nicht gerechtfertigt. Bleibt offener
Beobachtungspunkt, kein Code-Change.

Committet als `ca8b098`.

### Massnahme 2 umgesetzt: Zeitschaetzung + Handlungsansatz je Wiedervorlage-Thread

Alle offenen Wiedervorlage-Bedingungen wurden gegen echte Generierungs-/
Aufloesungsraten (Export 02.08. 06:49) hochgerechnet und je Zeile um einen
Handlungsansatz ergaenzt - Nutzer-Vorgabe: "wenn wir nicht mit den Messungen
weiterkommen sind Alternative Loesungsvorschlaege erforderlich". Volle
Tabelle in Memory `project_dead_loop_synthese_root_cause.md` (dort
autoritativ gepflegt, nicht hier dupliziert). Kernergebnisse:

- **Praktikabel, passiv abwarten (4 Threads):** Enge-Stop-Loss/TP-ATR
  Post-Fix (~09.-11.08.), Krypto-Spot CRV<2,0 (~20.08.), ADX/Choppiness
  (~12.-13.08.), Deribit Cross-Check (~17.08.).
- **Strukturell NICHT durch Messung loesbar (3 Threads, neue explizite
  Kategorie):** Konfidenz-Kalibrierung "mittel"-Band (n≈340 = ~4,5 Monate),
  Aktien/Rohstoffe/Themen-ETF-R-5.10 (>200 Tage), Backward-Tracking-
  "lang"-Bucket (120 Tage strukturell). Hier loest reines Warten das
  Problem nicht - Alternativvorschlaege statt weiterer Datensammlung:
  (a) Konfidenz-Kalibrierung auf den bereits einmal (29.07.) durchgefuehrten
  kontinuierlichen Korrelationstest umstellen statt auf Bucket-n zu warten
  (nutzt alle ~86 Datenpunkte statt 3-Buckets-Split); (b) Nicht-Krypto-
  R-5.10: den robust abgesicherten Krypto-Spot-Befund (n=148) als
  ausdruecklich gekennzeichnete Arbeitsannahme uebertragen statt
  unabhaengig zu verifizieren.
- **Positiv ueberraschend:** Selbst-Halten-Schatten-Tracking laeuft mit
  ~14,5 Kandidaten/Tag deutlich schneller als die urspruengliche Annahme
  "mehrere Wochen" - Wiedervorlage auf ~09.-16.08. vorgezogen.
- **Eigener Auswertungsfehler gefunden+korrigiert:** der Deribit-Wert wurde
  zunaechst als "n=3, moeglicherweise Datenanomalie" gemeldet - tatsaechlich
  war `len()` auf das umschliessende Dict statt auf die enthaltene
  `eintraege`-Liste angewendet worden (echte Struktur: 538 Eintraege, davon
  16 aufgeloest). Kein Datenproblem.

### Neues Referenzdokument: Stage-Abhaengigkeitsmatrix

Nutzer-Vorgabe: "die einzelnen Probleme koennen nicht vollstaendig isoliert
werden... eine Anpassung X in Stage 1 kann oder muss sich auf Funktionalitaet
Y in Stage 2 LLM1 und dann auf Funktion Z in Stage 3 LLM2 auswirken - sonst
bleibt es auch mit Messungen beim Regler probieren".

Neues Dokument `Basisinfos/Regler_Signal_Pipeline_Abhaengigkeiten.md`
(dauerhaftes Referenzdokument analog `Fakten_Entscheidungsmappe.md`):
buendelt erstmals die bereits bekannten, aber ueber Dutzende Einzel-Memories
verstreuten Kopplungen zwischen Stage 1 (Regler/deterministisch), Stage 2
(LLM1/Analyst) und Stage 3 (LLM2/Z.ai) in einer Matrix. Enthaelt u.a.:
`nur_long` → SHORT erreicht Mistral nie → Z.ai-SHORT erscheint strukturell
als "Abweichung" (bereits einmal als Kalibrierungsproblem fehlgedeutet);
CRV-/R-5.10-Schwellen verschieben unbemerkt die Z.ai-Vergleichspopulation;
die heute gefixte Preiszonen-Validierung schuetzt Stage 1s CRV-Berechnung
mit, nicht nur Stage 2. **Regel fuer kuenftige Regler-Aenderungen:** vor
jeder Schwellen-Aenderung pruefen, ob sie die an Stage 2 uebergebene
Kandidatenmenge und damit die Stage-3-Vergleichsbasis verschiebt.

### Memory-Konsolidierung (Nutzer-Wunsch, ohne Informationsverlust)

`reference_offene_zeitbasierte_beobachtungspunkte.md` wurde entschlackt: alle
statistischen n<15-/Wiedervorlage-Fragen (frueher Abschnitte 3, 4b, 5, 6)
sind jetzt ausschliesslich in `project_dead_loop_synthese_root_cause.md`
gepflegt - dort mit Zeitschaetzung und Handlungsansatz statt nur der rohen
Bedingung. Die Beobachtungspunkte-Datei bleibt zustaendig fuer aktive
Debug-Logs und Deploy-Verifikationspunkte. Beide Dateien verweisen
gegenseitig aufeinander; kein Inhalt wurde geloescht, nur an genau eine
zustaendige Stelle verschoben.

Committet ff887a2 (Split) bzw. 3688d8a (.docx-Konverter).


## Nachtrag (2026-08-02): Trendstaerke (ADX) trennt Treffer von Verlusten - erster an zwei Datensaetzen replizierter Befund

**Frage:** laufen Signale in trendlosen Marktphasen schlechter? Ausgangspunkt
war die Wiedervorlage "ADX/Choppiness-Filter" aus der Dead-Loop-Synthese.

**Methodisch neu:** verglichen wurde nicht gegen null, sondern gegen eine
**ADX-spezifische mechanische Basislinie** (Einstieg an beliebigem Tag,
fester Stop, Ziel bei CRV 2.0, 14 Tage Horizont, getrennt je ADX-Niveau).
Ohne diese Trennung haette man nur "in Seitwaertsphasen laeuft alles
schlechter" gemessen - eine Marktphasen-Aussage, keine Signalqualitaets-
Aussage.

**Befund (Hebel, Veto-Schatten, LONG):** Trefferquote steigt monoton mit der
Trendstaerke - ADX 5-15: 29,6% | 10-20: 28,2% | 15-25: 41,8% | 20-30: 62,0%.
Der Bereich 20-30 liegt mit n=50 auch Bonferroni-korrigiert (6 Zellen
getestet) ueber der Basislinie von 29,5%, und die Signifikanz haelt beim
Entfernen JEDES einzelnen Symbols. 5 Symbole, Top-Symbol 32%, 12
verschiedene Tage.

**Konfirmation an Spot (unabhaengiger Datensatz, anderer Veto-Grund - R-5.10
statt CRV):** derselbe Verlauf, deutlicher - 5-15: 14,6% | 10-20: 18,7% |
15-25: 39,6% | 20-30: 50,0% | 25-35: 69,2% | 30-40: 100% (n=12).
Median-Split ohne jede Grenzziehung: 22,7% vs. 52,6%. Ueber Raenge:
Treffer liegen im ADX im Schnitt 35 Raenge (von 151) hoeher als Verluste.

**Was die Recherche verhindert hat (siehe Test_und_Verifikationsmethodik
2.5.6):** die Schwellen 20/25/30 stammen aus Forex/Aktien und sind laut
Literatur **marktabhaengig, nicht absolut**. Die Sensitivitaetspruefung
zeigte daraufhin, dass die ADX-Spanne der Hebel-Daten nur bis 30,7 reicht -
der urspruenglich gemeldete "ADX > 30: 0 von 26 Treffer" war kein Bucket,
sondern der Randbereich, dominiert von AKT-SHORT (17 von 26). Ohne die
Recherche waere dieses Randartefakt in die Konfirmation getragen und dort
als Kategorie zementiert worden.

**Belastbarer Kern, bewusst OHNE harte Schwelle formuliert:** je staerker der
Trend zum Signalzeitpunkt, desto besser laufen Kauf-/LONG-Signale - auch
solche, die die Gates verworfen haben. Beide Gates (CRV bei Hebel, R-5.10 bei
Spot) ignorieren diesen Kontext bisher vollstaendig.

**Noch KEINE Regelaenderung.** Ein Regel-Kandidat waere eine
kontextabhaengige statt pauschale CRV-Anforderung; wegen des in der Literatur
dokumentierten ADX-Flackerns nahe Schwellen muesste er gestuft wirken, nicht
als harte Grenze. Offen bleibt ausserdem: 5 Symbole (CANTON, KAIA, KAITO,
SUPRA, XNO) fehlen mangels OHLC in beiden Auswertungen.

## Nachtrag (2026-08-03): CRV-Gate abschliessend geprueft - es filtert RICHTIG (#602 geschlossen)

**Widerruft den Befund vom 02.08.** („das Gate filtert invers") nicht nur, sondern
belegt die Gegenrichtung. Ursache des Fehlbefunds war Survivorship: ob ein Signal
ueberhaupt aufloest, haengt selbst vom Stop-Abstand ab.

**Messaufbau ohne DB-Status.** Jedes Signal mit Zonen laeuft selbst gegen die
Preishistorie ab seinem Erstellungstag - Ziel getroffen +CRV, Stop −1,0, keins von
beidem Mark-to-Market am Fensterende. Damit bekommt auch das Signal ein Ergebnis,
das nie ausgewertet wurde; die Selektion entfaellt **strukturell statt korrigiert
zu werden**.

**Drei Kontrollen, jede hat vorher einen Befund gekippt:** gleiche
Beobachtungsdauer · mechanische Basislinie je Gruppe mit identischen Parametern
(2778-3065 Zufallseinstiege je Satz) · Symbol-Konzentration.

| Signalbeitrag ueber Zufallseinstieg | 7 Tage | 14 Tage |
|---|---|---|
| Hebel ausgefuehrt | +0,620 R (n=153) | +0,696 R (n=36) |
| Hebel CRV-vetot | +0,092 R (n=282) | +0,435 R (n=83) |
| Spot ausgefuehrt | +0,210 R (n=62) | +0,289 R (n=47) |
| Spot CRV-vetot | −0,060 R (n=37) | −0,286 R (n=15) |

**KEIN Gate-Umbau.** Der am 02.08. vorgeschlagene Wechsel auf ein Expectancy-Gate
haette ein nachweislich richtig trennendes Gate gegen eines ersetzt, das auf 86
Datenpunkten kalibriert waere.

**Wichtigster Nebenbefund:** die Basislinie ist durchgehend negativ (−0,11 bis
−0,26 R) - mit n≈3000 die statistisch sicherste Zahl der Messung. Damit ist die
absolute Negativitaet des Systems zu einem erheblichen Teil **Marktphase, nicht
Signalqualitaet**. `compute_systemguete()` mass bis dahin nur absolut und
alarmierte dadurch strukturell falsch, solange nur ein Regime beobachtet ist.

## Nachtrag (2026-08-03): Systemguete um mechanische Basislinie, Signalbeitrag und Bootstrap erweitert

**Direkte Folge des Befunds oben.** Wer SQN ohne Bezugspunkt liest, haelt ein
funktionierendes System in einer schlechten Phase fuer kaputt und steuert in die
falsche Richtung nach - genau die Fehlerklasse, die diese Kennzahl verhindern soll.

Neue Felder je Gruppe: `basislinie_erwartungswert_r`, `basislinie_anzahl`,
`basislinie_stop_rel`, `basislinie_crv`, `basislinie_anteil_short`,
`signalbeitrag_r`. Dazu **Bootstrap-Konfidenzintervalle** fuer Expectancy und SQN
(1000 Ziehungen mit Zuruecklegen, fester Seed) - bewusst Bootstrap statt Formel,
weil sich R-Multiples bei genau −1,0 haeufen und eine Normalverteilungsannahme
schlicht falsch waere. Van Tharp nennt 100+ Trades fuer eine Live-Bewertung, 30 als
Untergrenze; mit 86 lagen wir genau dazwischen.

**`anteil_positiv`** ist der praktisch wichtigste neue Wert: Anteil der Ziehungen
mit positiver Expectancy. Bei 0,5 ist die Datenlage unentschieden, egal wie
ueberzeugend der Punktwert aussieht.

**Die Gegenpruefung fand zwei eigene Fehler vor dem Commit:** `ist_short` war hart
auf False - bei Hebel mit SHORT-Signalen waere die Basislinie spiegelverkehrt und
der Signalbeitrag frei erfunden gewesen. Und die Kursreihen wurden je Gruppe neu
geladen (64.000 Zeilen mal acht).

**Wirkung auf die Kennzahl:** Signalbeitrag hebel/real **+0,244** statt vorher
−0,379 - dieselben Signale, andere Methode.

## Nachtrag (2026-08-03): drei Betriebsfehler an einem Abend - Remote-Seite

Alle drei vom Nutzer gemeldet, alle drei Folgen derselben Erweiterung. Sie stehen
hier, weil jeder eine uebertragbare Lehre traegt.

**1. Kaputtes JavaScript legte ALLE Karten lahm.** Im JS-Block stand ein mit
Backslash escaptes Anfuehrungszeichen (`\"`). Der umgebende Python-String ist kein
Raw-String - Python loeste es auf, ausgeliefert wurde ein Syntaxfehler, und der
bricht nicht nur die betroffene Karte ab, sondern das **gesamte Script**.

> **LEHRE (gilt dauerhaft):** In `_INDEX_HTML` niemals `\"` verwenden. Und: den
> Block nach jeder Aenderung **zur Laufzeit aus dem geparsten String** pruefen,
> nicht aus der Quelldatei. Ich hatte Klammern- und Quote-Balance geprueft - die
> waren korrekt, aber im Python-Quelltext. Ausgeliefert wird ein anderer String.
> Derselbe Fehler trat am 04.08. ein zweites Mal auf.

**2. Der 2-Sekunden-Takt ueberlastete den Server.** Basislinie und Bootstrap
kosteten zusammen 1-1,5 s je Aufruf, `/api/status` wird alle 2 s abgerufen - die
Anfragen ueberlappten.

> **LEHRE:** Ich hatte die Laufzeit gemessen (0,06 s / 0,35 s) und als
> „vertretbar" eingestuft, **ohne zu pruefen, wie oft die Funktion aufgerufen
> wird**. Die Frage „wie teuer ist ein Aufruf" ist ohne „wie oft passiert er"
> wertlos.

**3. Zwei Nachbesserungen bis zur tragfaehigen Loesung:** erst Cache (5 min), dann
Hintergrund-Thread mit **eigener DB-Verbindung** (sqlite3-Verbindungen duerfen
nicht ueber Threads hinweg benutzt werden), schliesslich Stundentakt - die Zahlen
stammen ausschliesslich aus den `outcome_*`-Spalten, und die schreibt nur das
taegliche 06:00-Backward-Tracking. Von 288 Berechnungen taeglich waren 287
folgenlos. Auf dem Notebook (zwei Kerne) kostete ein Durchlauf ein Vielfaches der
1,8 s vom Desktop.

## Nachtrag (2026-08-03): Gate oder Positionsgroesse? - die Antwort ist je Tier gegenlaeufig

**Nutzerfrage:** „es gibt eine uebliche Methode wie man CRV anwendet, warum machen
wir das nicht?" - berechtigt. Van Tharp/Kelly bemessen damit die **Position** statt
Ja/Nein zu entscheiden; ein Gate ist der Sonderfall „Groesse 0 oder 1".

**Hebel - Gate behalten.** SQN +3,25 gegen +1,25 fuer jede Kelly-Variante. Das Gate
entfernt dort 65 % der Signale, laut #602 die richtigen.

**Spot - Groesse schlaegt Gate deutlich.** Das Gate entfernt dort nur 12 %, beisst
also kaum; praktisch bekommt alles dasselbe Gewicht.

| Spot | SQN | Summe R | Rueckschlag |
|---|---|---|---|
| heute | +0,63 | +9,8 | 36,3 R |
| CRV-Groesse, Spreizung 3x | +1,11 | +17,9 | 29,6 R |
| CRV-Groesse, Spreizung 5x | +1,36 | +23,1 | 27,1 R |
| ungedeckelt (399x, unbrauchbar) | +1,82 | +35,3 | 21,3 R |

**Warum heute nichts davon greift:** die Infrastruktur existiert
(`deckel_kandidaten`), aber die CRV-Abstufung hat **genau eine Stufe** - ab CRV 2,4
wird nicht mehr differenziert, ein CRV von 2,5 und eines von 6,0 sind gleichwertig.

**Zwei eigene Fehler, beide vor dem Melden gefunden:** der erste Lauf verglich
Einsatzhoehen statt Auswahlqualitaet (Kelly-Groessen um 0,06 gegen Gate 1,00), und
der Deckel-Test war als `max(g, 1/S)` gebaut - das **ebnet ein statt zu deckeln**
und liess Kelly faelschlich zusammenbrechen. Ohne Nachpruefung waere ein falsches
Negativergebnis gemeldet und der Spot-Befund unter den Tisch gefallen.

**Nutzer-Hinweis, der die Ausgangslage aenderte:** der tatsaechliche Einsatz liegt
zwischen 100 und 500 EUR und variiert bereits - nach Marktkapitalisierung. Das sind
**exakt 5-fache Spreizung**, also der Bereich mit dem groessten gemessenen Nutzen.
Vorbehalt, der dazugehoert: die 5x der Messung sind eine RELATIVE Spreizung der
Risikogewichte, die 100-500 EUR absolute Betraege - beides deckt sich nur bei
aehnlichem Stop-Abstand.

## Nachtrag (2026-08-03): Regler-Audit - 36 von 202 Config-Schluesseln ohne Wirkung

**Anlass:** Nutzerfrage nach „unbekannten bzw. aktuell nicht beruecksichtigten
Reglern". Ergebnis groesser als erwartet. Klassifikation dauerhaft in
`Regler_Signal_Pipeline_Abhaengigkeiten.md`.

**Der wichtigste Einzelfund: Volatilitaet steckt seit jeher in der
Positionsgroesse.** RM-5 setzt den Stop auf 2×ATR, RM-1 rechnet Groesse =
Risikobudget / Stop-Abstand - die Groesse ist also proportional zu 1/ATR. **Das IST
Volatility Targeting.** Eine Volatilitaets-Komponente im Groessenmodell zaehlt
damit doppelt. Genau das passierte am selben Tag: die Variante „nur Volatilitaet"
war signifikant SCHLECHTER (−0,029 R je Signal, [−0,051..−0,008]) und waere ohne
den Kontrollfall als Literaturempfehlung eingebaut worden.

**Drei Methodenfallen, alle real eingetreten:**

1. **Dynamisch gebaute Namen** - `gewicht_*` wird per f-String zusammengesetzt,
   Textsuche findet das nicht. 7 der 36 waren Fehlalarm.
2. **Falsche Ausschlussfilter** - der erste Durchgang schloss `analyse_*.py`,
   `backtest_*.py` und den Export aus, also genau die Orte, an denen eine
   Verwendung als MESSGRUNDLAGE laege. **Vom Nutzer gefunden, nicht von mir.**
3. **Namensaehnlichkeit statt Beleg** - `auto_watchlist` fuer implementiert
   erklaert, weil `auto_add_unknown_hebel_symbols()` aehnlich klingt. Das ist der
   Hebel-Pfad; fuer den Marktscan fuehrt der einzige Weg ueber einen Button.

**Bereinigt (kein Verhaltensunterschied):** `api_key_noetig`,
`rate_limit_pro_minute` (irrefuehrend: 30 ohne, 100 MIT API-Key - ein einzelner
Wert kann beide Betriebsfaelle nicht abbilden), die AZ-7-Dublette
(`max_hebel_faellt_regime_krise_extrem_auf_null` + `aus_bei_krise_extrem`, zwei
Namen fuer EINE Codestelle), sowie `begruendung_pflicht`,
`liquidationspreis_ausweisen`, `ema_perioden`, `rsi_periode`,
`forecast_szenarien` - beschrieben korrekt, steuerten nicht.

**BEWUSST NICHT ersetzt:** ein Drossel-Regler fuer CoinGecko. Der Minutentakt ist
eine harte Vorgabe, und gegen das MONATSkontingent hilft langsamer nichts - am
Monatsende steht dieselbe Zahl. Die wirksame Bremse sitzt bei der ANZAHL der
Abfragen. Ein dritter Ort fuer dieselbe Aufgabe haette die Suche nur verlaengert.

**AZ-7 bleibt bewusst ein hartes Gate ohne Regler** - es schuetzt das Instrument
mit Liquidationsrisiko in genau dem Regime, in dem Liquidationen passieren. Der
Notausstieg liegt eine Ebene hoeher bei `regime.manueller_override` (RG-8).

**Nichts wurde spurlos geloescht.** Jede Entfernung steht als Kommentar an
derselben Stelle, mit Grund und Verweis auf den echten Ort. Nutzer-Vorgabe:
„Nachvollziehbarkeit ist Trumpf - u.U. ersetzen wir einen Dummy gegen etwas
Besseres und dann soll es auch so stehen."

**Offen geblieben:** der gesamte `antizyklisch`-Block (AZ-1..AZ-7, acht Schluessel)
wird nirgends gelesen - das Verhalten lebt als Prompt-Text auf Stage 2, waehrend
die Config Stage 1 suggeriert. **Ein ganzes Spezifikationskapitel auf der falschen
Stufe.**

## Nachtrag (2026-08-03): Z-3 / RM-7 Drawdown-Notbremse gebaut (#612) - stand seit Projektbeginn offen

Die Regel war seit Projektbeginn als „OFFEN - fehlt noch eine Portfolio-Wert-
Historie" gefuehrt. `holdings` ist eine ZUSTANDStabelle (symbol als PRIMARY KEY,
jeder Sync ueberschreibt), eine Transaktionstabelle gab es nicht.

**Ich hatte „hart oder weich?" faelschlich zur Nutzer-Entscheidung vorgelegt.** Das
Regelwerk hatte es laengst festgelegt - RG-6 stellt Z-3 unter Aenderungsschutz,
RG-9 fuehrt es unter den harten Limits, die Spezifikation definiert es als
**dringenden Alert, nicht als Automatik**. Nachlesen haette gereicht.

**Der Weg:** Rekonstruktion aus 9582 Wallet-Transaktionen + `price_history`.
Obergrenze **88 Tage**, begrenzt durch die KURSE (alle 41 Symbole starten
einheitlich am 2026-05-08), nicht durch die Transaktionen. Nur 112 der 9582
Buchungen liegen im Kursfenster - einzeln nachpruefbar.

**Die zentrale Konstruktionsentscheidung:** der Drawdown wird auf einem
**mengenkonstanten Index** gemessen, nicht auf dem rohen Portfoliowert. Sonst sieht
ein Zukauf wie ein Gewinn aus und ein Verkauf wie ein Verlust - eine EUR-Einzahlung
ueber 2.500 EUR am 12.07. haette die Reihe sonst verdreht. **Wer die 15 % auf den
rohen Wert bezieht, legt die Schwelle falsch aus.**

**Die Margin-Regel, an einer vollstaendigen NEAR-Episode abgelesen:**
`margin_trading.open` eingehend zaehlt NICHT (Margin-Wallet), ausgehend zaehlt;
`.repay`/`.fee` zaehlen nicht; `.close` nur die eingehende Seite; `.borrow`
eingehend zaehlt. **Warum das noetig war, obwohl der Endstand auch naiv stimmte:**
ueber eine abgeschlossene Episode heben sich Eroeffnung und Schliessung auf, das
Episoden-Netto ist exakt 0. Fuer einen Tag MITTENDRIN gilt das nicht - NEAR am
24.07. naiv 355,33 gegen margin-bewusst 0,0000, gut 570 EUR Scheinvermoegen quer
durchs Kursfenster. **Genau die Sorte Fehler, die jeden Endstands-Test besteht und
trotzdem da ist.**

**Methodisch:** vorwaerts von null rechnen, nicht rueckwaerts vom heutigen Bestand
- rueckwaerts waere der Pruefstein per Konstruktion erfuellt und wuerde jede noch
so falsche Regel bestehen. Erste Runde bewusst mit der NAIVEN Regel, um zu sehen
WO sie bricht.

**Vier eigene Fehler, alle vom Probelauf-Modus abgefangen** (nur ein
Symbol-Override-Dict statt beider, Fliesskomma-Staub als „Position ohne Kurs",
fehlender `init_db()`-Aufruf, widerlegte Wochenend-Hypothese). Das ist das Argument
dafuer, kuenftige Schreibskripte wieder so zu bauen.

**Befuellt:** 88 Tage, Index 100,000 → 85,628. **Z-3 loeste beim ersten Lauf aus**
(16,73 % gegen 15 % Schwelle).

**Kategorien: Diagnose ja, zweiter Ausloeser nein.** Nutzer-Vorschlag „nach
Kategorien - Krypto nur fuer Krypto?" - die Aufschluesselung wird gebaut,
**ausgeloest wird weiter auf dem Gesamtwert**. Z-3 schuetzt Kapital, und
Diversifikation ist genau dafuer da: faellt Krypto 20 % waehrend Aktien halten, ist
das Portfolio intakt. Ein zweiter Ausloeser waere eine NEUE REGEL unter
RG-6-Aenderungsschutz - falls je gewollt, gehoert das separat entschieden, nicht
nebenbei mitgebaut.

**Einschraenkung, die man beim Lesen der Zahl kennen muss:** der Drawdown ruht auf
rund 90 % des Portfolios - fuenf Positionen (~765 EUR) haben keine Kursdaten (#614).

**Folgeaufgabe #613 mit BEDINGUNG statt Datum:** die 13 Nicht-Krypto laufen mit
konstanter Menge. Nachzuziehen, bevor Z-3 genug Historie hat um scharf zu werden,
ODER frueher sobald dort gehandelt wird. Grund: solange nichts passiert, ist die
Naeherung nicht ungefaehr richtig, sondern EXAKT - ab dem ersten Trade driftet sie
still, und rueckwirkend ueber den ganzen Zeitraum.

## Nachtrag (2026-08-03): Messmethodik-Umbau (#617) - fuenf eigene Fehler DERSELBEN Familie an einem Tag

**Der wichtigste methodische Eintrag dieser Phase.** Fuenfmal an einem Tag dieselbe
Ursache: **Signal- und Basislinienseite ungleich behandelt.** Jedes Mal sah das
Ergebnis plausibel aus.

| | Fehler | gefunden durch |
|---|---|---|
| 1 | Basislinie ueber 2 Jahre, Signale ueber 3 Wochen | Isolationstest, 0,30 R |
| 2 | Basislinie zaehlt Unaufgeloeste mit, Signale nicht | #617-Kernfrage |
| 3 | Baender gegen horizontlose Formel `1/(1+CRV)` statt gegen Basislinie | synthetische Daten |
| 4 | Basislinie ab Einstiegstag simuliert (Entry = Schlusskurs) | absurder Wert (0,0 %) misstraut |
| 5 | Perzentil ueber LONG+SHORT gemeinsam, Auswertung getrennt | ungleiche Quartile |

> **STEHENDE PRUEFFRAGE, gehoert vor jede Auswertung:** *Werden beide Seiten des
> Vergleichs wirklich gleich behandelt?*

**Fachlicher Kern.** Das ist die Triple-Barrier-Methode (Lopez de Prado):
statistisch **Competing Risks mit Rechtszensierung**. `Ziel/alle` unterschaetzt,
`Ziel/aufgeloeste` ist Complete-Case-verzerrt - **beide bekannt-falsch**,
nebeneinanderstellen mittelt zwei Fehler. Korrekt ist die kumulative Inzidenz
(Aalen-Johansen); der Hauptgewinn ist nicht Genauigkeit, sondern **Datenausbeute:
759 statt 455 auswertbare Signale**. Wilson-Intervalle sind zu eng, weil einzelne
Symbole bis zu einem Drittel eines Bandes stellen - deshalb Block-Bootstrap ueber
Symbole.

**Die entscheidende Einsicht, an synthetischen Daten mit bekannter Wahrheit
belegt:** der Vergleich gegen `1/(1+CRV)` **dreht ab CRV 2,5 das Vorzeichen**,
Ursache ist Horizont-Trunkierung. Ein Zufallseinstieg misst bei CRV 4,0 und H=7
exakt 0,0 %.

| CRV | wahre Kante | gegen Basislinie | gegen `1/(1+CRV)` |
|---|---|---|---|
| 2,0 | +24,3 pp | +22,7 pp | +11,7 pp |
| 2,5 | +26,7 pp | +16,7 pp | −1,0 pp |
| 4,0 | +31,3 pp | +0,5 pp | −18,4 pp |

→ **Nur `abstand_zur_basislinie_pp` ist interpretierbar, absolute Quoten nie.** Das
ist Methodik 2.5.7 („Basislinie je Bucket ist PFLICHT"), die ich zweimal
weggelassen hatte.

**DREI BEFUNDE WIDERRUFEN - nicht wiederbeleben:**

- **„CRV ≥ 4,0 ist das schlechteste Band"** - Trunkierungs-Artefakt.
- **„Gate-Senkung unter 2,0 ist gemessen erledigt"** - war Wilson-Artefakt, die
  Frage ist **offen**.
- **„36 % Aufloesungsquote belegt Selektion"** - der Nenner enthielt 94 Zeilen, die
  nie ein Trade waren. Ehrlich: 58 %.

**Ausserdem: der Screening-Score diskriminiert nicht.** Event-Study auf allen
Kandidaten (nicht auf Signalen - dort liegen vier Selektionsschichten dazwischen):
LONG −1,2 / +4,0 / **+13,0** / +2,4 pp - **nicht monoton**, drittes Quartil am
besten. SHORT alle vier Quartile −19 bis −23 pp, keinerlei Ordnung. Nullbefund mit
begrenzter Trennschaerfe, kein Beweis der Wirkungslosigkeit.

**Architektur-Entscheidung daraus: der Score gehoert NICHT ins LLM.** Er ist eine
Stage-1-Selektionsvariable, die CRV-Baender sind Stage-2-Fakt - Vermischung waere
Doppelzaehlung. Heute bekommt das LLM `score_gesamt` als **nackte Zahl ohne jede
Regel**, die schlechteste aller Varianten: kann ankern, ist aber nicht deutbar.

## Nachtrag (2026-08-03): CRV-Erfolgsbaender als Fakt + Regel 36 (Krypto-Spot)

Direkte Anwendung des #602-Befunds: das CRV trennt stetig, nicht an einer Kante.
Ein glatter Verlauf verlangt glatte Behandlung - also gemessene Baender als
**gewichtender Fakt** statt einer Ja/Nein-Schwelle.

**Konflikt, der am 04.08. auf sauberen Krypto-Spot-Daten sichtbar wurde:** Regel 36
sagt „bevorzuge CRV > 4,0", gemessen erreichen im Band ≥ 4,0 aber **0,0 % das Ziel
(n=20)** - die Basislinie liegt dort bei 2,3 %, ein Zufallseinstieg kommt also auch
fast nie an. Beide Aussagen sind vereinbar (Regel 36 misst „MFE ≥ 1R", nicht „Ziel
erreicht"), die praktische Folge bleibt: **ein CRV ueber 4,0 zu bevorzugen liefert
Signale, die ihr Ziel im relevanten Zeitfenster nie erreichen.** Hinweis, kein
Beweis - n=20.

## Nachtrag (2026-08-04): Kostenrahmen recherchiert und in die R-Rechnung eingebaut (Phase 0.2)

**Bis dahin enthielt KEINE Messung im System Kosten.** Die Break-even-Luecke ist
4-7x groesser als angenommen.

```
Kosten in R = (L−1)/L × (Schliessung + Tagesgebuehr × Tage) ÷ Stop-Abstand
```

**Der Einsatz kuerzt sich heraus** - die Last haengt nur an Hebel, Haltedauer und
Stop-Abstand. Zwei Folgerungen fallen direkt aus der Formel und stuetzen RM-1b/1c
mit einer **von der Trefferquote unabhaengigen** Begruendung: enge Stops sind
doppelt teuer, und hoeherer Hebel kostet MEHR je R (der Faktor (L−1)/L geht von
0,50 auf 0,90).

**Netto-EW hebel/real: −0,233 R statt −0,104 R brutto.**

> **Kosten kippen die ABSOLUTE Frage („traegt sich das System?"), nicht die
> RELATIVE („ist die Auswahl besser als Zufall?").** Die Basislinie ist ein
> alternativer Trade und traegt dieselben Saetze. **Alle Selektionsbefunde der
> Vortage bleiben gueltig.** Deshalb bleiben `expectancy_r`/`sqn` brutto, die
> Netto-Werte stehen daneben.

**Achtung bei der Auswertung:** ein Zufallseinstieg trifft seltener eine Barriere
und laeuft oefter bis zum Horizont - er zahlt also *laenger*. Ein Signalbeitrag,
der sich durch die Kostenrechnung **verbessert**, ist zu pruefen bevor er zitiert
wird.

**Belegt vs. angenommen - die Trennung ist Teil des Modells:**

| | Status |
|---|---|
| Bemessungsgrundlage = **geliehenes Kapital** | **belegt** an 104 Positionen; Regression 1,081 % auf Kredit gegen 1,00 % offiziell (auf Nominal 0,624 %) |
| Schliessung 0,3 %, Liquidation 1 %, Staffel | offiziell belegt |
| Tagesrate 0,18 %/Tag | offiziell belegt, **nicht** an eigenen Daten - erst 3 Positionen seit Stichtag |
| Spot-Kosten | **NICHT belegt** - nur 348/3578 Trades tragen `vsn_fee`, sonst steckt sie im Spread. `kosten_belegt=False` |

**DER EIGENTLICHE FUND, vorher unsichtbar: drei Haltedauern, die nicht
zusammenpassen.**

| | Median | Quelle |
|---|---|---|
| tatsaechlich gehandelt | **0,30 T** (75 % unter 1 Tag) | 188 echte Positionen |
| Signal loest auf | **2,57 T** | 86 Trades |
| Stop traegt rechnerisch | **3,3 T** | 3,94 % Stop bei 3× |

Positionen werden regelmaessig geschlossen, **bevor die These entschieden ist**.
Faktisch ist das Scalping - der Gegensatz zur Vorgabe „Standard-Trades". Bevor eine
Zieldauer festgelegt werden kann, muss das **Feld dafuer existieren**:
`halte_kriterium_bucket` ist eine Ablauffrist, `mindestziel_zeitraum_tage_
geschaetzt` eine Volatilitaetsrechnung. Keins von beiden ist eine Strategieangabe,
und sie widersprechen einander. **Offen bis heute.**

**Zwei eigene Fehler vor dem Commit gefunden:** Abschnitt 6.7 rechnete die
Schliessungsgebuehr auf das Nominal, im Widerspruch zur eigenen Regression eine
Seite darueber (Kosten ~9 % zu hoch). Und zum **zweiten Mal** ein `\"` in einem
nicht-rohen Python-String in `remote/server.py` - haette wieder die ganze
Statusseite lahmgelegt. Gefunden, indem der *geparste* String geprueft wurde.

## Nachtrag (2026-08-04): der Einstieg ist nicht das Problem - der AUSSTIEG ist es

**Der wichtigste Befund dieser Projektphase.** Aus der SQN-Recherche (#615),
ausgeloest durch den Nutzer-Einwand, dass Hebel und nicht Spot die echten Daten
produziert.

| Hebel, 86 real bewertete Signale (2026-07) | |
|---|---|
| erreichten unterwegs ≥ 1R (MFE) | **50,0 %** |
| endeten tatsaechlich im Plus | **17,6 %** |

**Die Haelfte aller Signale stand einmal bei +1R und ging trotzdem als Verlust
aus.** Die Einstiege finden die Bewegung; zwischen Maximum und Ergebnis geht sie
verloren. Wir haben monatelang an Gates, Konfidenz, CRV-Schwellen und
Einstiegsqualitaet gemessen - an einer Stelle, die laut dieser Messung
funktioniert.

**Nachtrag desselben Tages, unangenehm:** der Befund war **nicht neu**.
`compute_sl_mfe_analyse()` (gebaut am 30.07. auf eine Nutzerfrage hin) trennt
exakt dies - „Richtung war falsch" gegen „Richtung war richtig, aber zu eng
gestoppt" - inklusive Konzentrations-Check. **Sie wird nirgends aufgerufen.** Ich
habe stundenlang von Hand nachgerechnet, was fertig im Code lag.

**Bestandsaufnahme der Massstaebe (#618): drei Mess-Funktionen haben null externe
Aufrufer** - gebaut, dokumentiert, verifiziert, nie angeschlossen
(`compute_baseline_vergleich`, `compute_sl_mfe_analyse`,
`compute_zai_uebereinstimmung_baseline`). Laufnachweis erbracht: sie sind nicht
kaputt, nur unsichtbar.

**Von vier Bezugspunkten taugt einer uneingeschraenkt:**

| Bezugspunkt | Urteil |
|---|---|
| CRV-Breakeven `1/(1+CRV)` | brauchbar - arithmetisch, keine Asymmetrie |
| regime-naiv | brauchbar - empirisch, braucht Daten |
| **Muenzwurf 50 %** | **unbrauchbar, strukturell falsch** |
| `basislinie_erwartungswert` | problematisch - Aufloesungs-Asymmetrie |

**Warum der Muenzwurf falsch ist:** er unterstellt symmetrische Ausgaenge, die
Ziele sind aber per Konstruktion asymmetrisch. Eine 50-%-Quote bei CRV 3,27
entspraeche **+1,14 R** Erwartungswert - ein fantastisch profitables System, kein
neutraler Vergleichspunkt.

**Warnung fuer den Anschluss:** Breakeven-Lock ist die naheliegende Antwort und
wurde am 01.08. bereits geprueft und **verworfen** - kostete 63 % der Gewinner. Die
Frage ist nicht *ob* abgesichert wird, sondern **wo zwischen +1R und Stop die
Bewegung kippt.** Nicht blind wiederholen.

**Daraus die Ausstiegsregel** (Trailing ab +1R, Abstand 1R): gemessen an 495
aufgeloesten Signalen, EW −0,176 → −0,084 R, Bootstrap [+0,051 ; +0,131], 100 %
positive Ziehungen. Am 04.08. gebaut und verdrahtet, am 05.08. scharfgeschaltet.

## Nachtrag (2026-08-04): Positionsgroesse #606 entschieden - Empfehlung UND Obergrenze gemeinsam

**Der eigentliche Grund fuer die sichtbare Empfehlung:** der gemessene Vorteil
entsteht **nur, wenn die Groessen tatsaechlich variieren**. Der Nutzer setzt den
Einsatz bisher selbst (100-500 EUR). Bleibt das so, **tritt der Vorteil nie ein** -
ein weiterer Deckel waere folgenlos, genau wie die vier bereits geprueften
Positionsgroessen-Deckel, die alle unter dem tatsaechlichen Einsatz lagen. Deshalb
muss die Zahl **sichtbar und benannt** sein: *„Empfohlen nach CRV: 340 EUR - RM-1
erlaubt bis 780 EUR"*.

**Ein eigener Konstruktionsfehler, vom Nutzer gefunden.** Ich hatte „Kelly ersetzt
die Empfehlung" und „beide getrennt ausweisen" als **Alternativen** vorgelegt.
Nutzer-Einwand: *„kannst du nicht Option A wie Option C bauen?"* - richtig, der
Unterschied war reine Beschriftung, technisch rechnet das System beide Zahlen.
**Lehre: vor dem Vorlegen von Optionen pruefen, ob sie sich technisch unterscheiden
oder nur in der Benennung.**

**Als Empfehlung, nicht als Information** - bewusst so entschieden. Fuer den Code
egal, fuer die Auswertung nicht: **nur bei einer Empfehlung bedeutet „nicht
gefolgt" eine Abweichung, die etwas aussagt.** Daraus der neue Messpunkt
Befolgungsgrad (Methodik 2.11).

**KEIN Volatilitaets-Divisor** - siehe Regler-Audit, die Doppelzaehlung war
signifikant schaedlich.

**Live gegangen ist an diesem Tag die stufenlose Spot-CRV-Groesse** (CRV 2,0 → 20 %
/ 3,0 → 40 % / ab 6,0 volle Groesse), erwartet SQN 0,63 → 1,36. **Die einzige
Verhaltensaenderung des Tages** - alles andere war Messung.

## Nachtrag (2026-08-04): vier saubere Negativbefunde - geschlossen, nicht vertagt

| | Ergebnis |
|---|---|
| **Score-Komponenten** | 41.552 Trigger auf 723 Faelle verdichtet: **keine traegt**. Bester Kandidat war ein Richtungs-Confounder (p=0,735 innerhalb LONG) |
| **Ausschuss-Hypothese** | p = 0,32 (Hebel) / 0,49 (Spot). Vorher bekannt: nur Effekte ≥ 1,2 R auffindbar |
| **LLM1-Prompt** | zwei Varianten, zwei Laeufe: Wirkung **0,009 R gegen 0,752 R Eigenrauschen** = 0,01×. Vorzeichen kippte zwischen den Laeufen |
| **Selbstjustierung** | kein rollierendes Fenster schlaegt den festen Wert, bei keinem Horizont. Rauschen 0,98 R gegen 0,24 R Phasensignal |

**Auch mehr Symbole helfen nicht:** 84 Symbole → 5 %, 168 → 2 % Trennschaerfe.

**Der LLM1-Thread im Detail, weil er einen Widerruf enthaelt.** Zuerst wurde LLM1
als positionsempfindlich gemessen (`trigger` ans Ende: 3,20 pp Konfidenzverschiebung
gegen 0,60 pp Eigenrauschen, 5,3×) - die U-foermige Aufmerksamkeitskurve der
*Lost-in-the-Middle*-Literatur. **Der daraus abgeleitete Befund wurde am selben Tag
WIDERRUFEN**, nachdem ein historischer Backtest die RICHTIGKEIT statt nur die
Veraenderung mass: keine der beiden abgeleiteten Prompt-Aenderungen traegt. Der
CoT-Effekt liegt bei 1 % des Eigenrauschens.

**Was daraus NICHT folgt:** dass eine „bessere" feste Reihenfolge die Loesung ist.
Bei einem echten Signal ist vorher nicht bekannt, welcher Fakt der Ausreisser ist,
und *jede* feste Reihenfolge bevorzugt strukturell den zuletzt genannten. Das
etablierte Gegenmittel ist Position Swapping (bei LLM2 vorhanden, bei LLM1 nicht).

**Gebaut und geprueft, aber ohne Ertrag im Betrieb:** acht Analyseskripte. Sie
haben an diesem Tag allerdings **vier Fehlentscheidungen verhindert**.

**Sechster Fehler derselben Familie wie am 03.08.:** ein **entartetes
Konfidenzintervall galt als belastbar**. Erreicht in einem Band kein Fall sein
Ziel, liefert der Bootstrap in jeder Ziehung 0,0 - das Intervall [0,0..0,0]
verfehlt die Basislinie rein rechnerisch. Ausgerechnet das Band mit der duennsten
Datenlage stand dadurch als einziges auf „belastbar". Behoben durch eine
Mindestbreite.

**LLM2 (Z.ai) bewusst geparkt.** Nutzer-Klarstellung: die drei Ebenen sind eine
**Folge** - 1. deterministisch misst, 2. LLM1 entscheidet auf besserer Grundlage,
3. LLM2 prueft gegen. **Nicht bewerten, bevor Stufe 1 und 2 stehen** - sonst misst
man den Gegenpruefer am Fehler des Vorgaengers. Punkt b wurde beantwortet: die
40,7 % Abdeckung waren ein Artefakt, real 96,5 % seit Rollout.

**Betriebsbefund nebenbei: SQLite-Sperrkonflikte um 06:30** - 19 Treffer „database
is locked", vier fehlgeschlagene Remote-Statuskarten, Hebel-Screening ausgefallen.
Ursache: drei Cron-Jobs auf derselben Minute. Selbstheilend, aber erzeugt
Fehlermails und Datenluecken. Loesung waere Staggering.

## Nachtrag (2026-08-05): der Dead-Loop aufgeloest - die Ursache liegt bei MISTRAL, nicht im Code

**Beantwortet die Leitfrage „warum kommen so wenige Signale".** Der Weg dorthin
enthaelt drei eigene Korrekturen und ist deshalb ausfuehrlich festgehalten.

**Es waren zwei getrennte Vorgaenge, die ich zunaechst zu einem verschmolzen
hatte.**

**Vorgang 1 - Signal-Knappheit, auf die Minute datiert.** `c8dd982` („Nur-Long-
Deckel: LLM-Output wurde nie gegen `hebel_richtung_modus` geprueft") ging am
28.07. 17:08 UTC ein. Das **erste Nur-Long-Veto ueberhaupt faellt 17:37 UTC - 29
Minuten spaeter.** Vorher liefen SHORT-Empfehlungen unbemerkt durch. Weder
Umsetzungsfehler noch gewolltes Verhalten, sondern **ein korrekter Bugfix, der auf
eine unerklaerte SHORT-Verschiebung trifft**.

**Vorgang 2 - echter Qualitaetseinbruch, aber ab 29.07.** Sauber an LONG allein
gemessen (dort ist kein Nur-Long-Veto moeglich, also kein Zusammensetzungseffekt):
**45,1 % (n=206) → 3,2 % (n=31)**, +41,9 pp, Block-Bootstrap ueber Symbole
[+14,4 ; +64,9] pp, p = 0,0029.

> **METHODISCH ZENTRAL:** der Trennpunkt wurde **gesucht statt gesetzt**
> (Max-Statistik ueber alle Splits mit Block-Permutation). Mein erster Versuch
> datierte auf den 31.07., weil ich die Reihe angesehen und *dann* dort getestet
> hatte. Ein nach Sichtung gewaehlter Trennpunkt ist kein Test.

**Fuenf Erklaerungen geprueft und ausgeschlossen:** Markt (direkt ueber 41 Symbole
gemessen - die Einbruchsperiode war minimal **besser**), Stop-Breite (jedes Band
bricht gleich ein), Richtung, Zensierung (Landmark H=3/4/5), Symbol-Clusterung.

> **LEHRE:** Marktausschluss immer an der **tatsaechlichen Bewegung** messen, nie
> am Regime-Label. Label und Fear & Greed haetten das nie gezeigt.

**Der Nachweis.** 12 echte Faktensaetze aus `facts_json`, die im Juli zu 100 %
HALTEN erzeugten, erneut gefragt - mit bitgleichem Juli-Prompt aus git:

```
Betrieb Juli, dieselben Faelle    55,4 %   (n=104)
Replay heute, gleiche Fakten      68,0 %   +12,6 Punkte, t = +12,8
Produktionssprung am 31.07.       54,1 % → 68,3 %
```

**Das Replay reproduziert nicht den Juli-Zustand, sondern den Zustand NACH dem
31.07. - auf 0,3 Punkte genau.** Modellname `mistral-small-2506` unveraendert, das
Verhalten dahinter nicht.

**Vorher ausgeschlossen** (Nutzer-Vorgabe: ein von hier aus nicht widerlegbarer
Grund darf erst am Ende stehen): Prompt bitgleich aus git, Fakten bitgleich,
Aufrufparameter identisch, Validierung kann ERÖFFNEN nie in HALTEN drehen, drei
Pipeline-Pfade, Markt, und die drei Prompt-Regeln vom 28./29.07. (28 Anker,
Einzeleffekte praktisch null).

**Regel 28 ist entlastet - gegen die eigene Hypothese.** Mit Regel 28 haelt das
Modell **haeufiger** (14 % gegen 9 %), nicht seltener.

**Zwei Feldfallen, die jede Auswertung ueber den 31.07. hinweg betreffen:**
`original_action` existiert erst seit 31.07. 07:01 (davor bei JEDEM Signal leer -
wer damit ueber die Grenze vergleicht, misst die Feldeinfuehrung; stattdessen
`risk_veto_reason`), und `ist_reines_llm_halten` kam am selben Tag.

**KORREKTUR eines eigenen Befunds - das Nur-Long-Veto ist der schaerfste Filter,
nicht Verschwendung.** Ich hatte die 313 verworfenen SHORT-Signale als „nie
ausfuehrbar - 20,8 % der Kapazitaet" committet. Nutzer-Korrektur: SHORT ist nicht
tot, laeuft nur unsichtbar weiter, und muss als **Vergleich** gemessen werden.

| Gruppe | n | aufgeloest | Trefferquote | EW |
|---|---|---|---|---|
| SHORT, Nur-Long-Veto | 313 | 88 | **10,2 %** | −1,136 R |
| LONG, ausgefuehrt | 162 | 70 | 17,1 % | −0,332 R |
| andere Vetos (KONTROLLE) | 415 | 274 | **43,8 %** | +0,054 R |

Die Kontrollgruppe traegt den Schluss: **dasselbe** Schattenverfahren liefert bei
anderen Vetos 43,8 %. Das Verfahren funktioniert - die verworfenen SHORTs sind
wirklich die schlechteste Gruppe im System.

> **LEHRE:** Ich hatte „wird verworfen" mit „geht verloren" gleichgesetzt, ohne den
> Block zu lesen, der genau das misst. Vor jeder Aussage ueber verworfene Signale
> erst die Schattenmessung nachschlagen.

**Zahlenkorrektur zum Gate:** meine fruehere Aussage „das Gate dreht 64-67 % der
LLM-Empfehlungen" war irrefuehrend. Fuer **ausfuehrbare** Signale filtert es 11 von
207 = **5 %**. Die 64 % waren fast vollstaendig SHORT-Ablehnungen.

**Das HALTEN kommt NICHT aus dem Faktensatz** - zwei Ablationsrunden, 8 Anker × 3
Wiederholungen, echte Mistral-Calls: V0-V3 je 100 % EROEFFNEN, V4 96 %, V5-V7 je
100 %. Kein Faktenblock traegt es, auch nicht `regime_profil` mit seiner
Mindestkonfidenz. **Offen bleibt**, warum das Modell im Betrieb 64 % HALTEN sagt
und im Backtest 0 % - struktureller Unterschied: der Backtest stellt jeden Anker
als frische, isolierte Entscheidung, im Betrieb werden dieselben 33 Symbole
mehrmals taeglich gefragt. Mit den vorhandenen Daten nicht pruefbar.

## Nachtrag (2026-08-05): Kanarienvogel gebaut, aber BEWUSST NICHT aktiviert

Nach dem Mistral-Nachweis lag eine Drift-Ueberwachung nahe: feste Faktensaetze
periodisch neu fragen, Abweichung melden, bevor sie den Betrieb erklaert.

**Gebaut und getestet** (`agent/krypto/kanarienvogel.py` + 5 eingefrorene
Faktensaetze), **aber ohne `add_job()`**. Auslöser war ein Nutzer-Einwand:
*„bringt uns das Feature einen Wert, finde das kann eigentlich nach hinten"* - und
er trug. Ein zweiter Drift wuerde sich auch ohne Kanarienvogel in den
Betriebszahlen zeigen; die laufenden Kosten fielen dagegen taeglich an.

**Aktivieren = eine Zeile. Revisit-Bedingung: sobald ein zweiter unerklaerter
Verhaltenssprung auftritt.**

## Nachtrag (2026-08-05): die Richtungswahl ist eine REGIME-WETTE, keine Kante

**Vorarbeit fuer den Nur-Long-Umbau** - die Architekturfrage wurde gemessen statt
vorausgesetzt. Nutzer-Vorgabe: „miss beides, Richtung und Zonenqualitaet".

| Marktfenster | LONG − SHORT | Intervall |
|---|---|---|
| steigend | **+1,744 R** | [+0,867 ; +2,429] |
| fallend | −0,133 R | schliesst 0 ein |

**Der Nur-Long-Veto schuetzte also keinen dauerhaften Ertrag.** Das entzieht der
Begruendung „SHORT ist ertragsschwaechr" die Grundlage - die Richtung folgt dem
Regime, nicht der Signalqualitaet.

**Zweiter, wichtigerer Befund aus demselben Lauf:** der **Ausfuehrungshinweis
zerstoert den Signalfluss**. Bekommt das Modell ehrlich mitgeteilt, dass SHORT
nicht ausgefuehrt wird, faellt die EROEFFNEN-Quote von **93 % auf 3 %**. Es
schlaegt dann gar nichts mehr vor, statt LONG-Alternativen zu suchen.

> **Diese Zahl ist seither die stehende Warnung** vor jedem Fakt, der dem Modell
> eine Einschraenkung mitteilt. Sie hat spaeter die Formulierung des
> Systemguete-Fakts bestimmt (Regel 31) und den Z-3-Fakt verhindert.

## Nachtrag (2026-08-05): Nur-Long-Umbau in fuenf Schritten - der BP-Schalter wirkt nur noch auf E-Mail und Anzeige

**Nutzer-Vorgabe, woertlich:** der Schalter soll „NULL Einfluss auf die
Funktionsweise im Hintergrund" haben - SHORTs sollen lediglich nicht per E-Mail
kommen und nicht in der GUI erscheinen. Dazu: *„wir operieren wieder am Herzen und
diesmal muss alles klappen"*.

**Warum der Umbau noetig war - es ging um Messhygiene, nicht um Ertrag.** Solange
der Veto vor der Verarbeitung sass, landeten SHORT-Signale im Veto-Schatten statt
im regulaeren Outcome-Pfad. Jede Auswertung ueber Richtungen war dadurch
strukturell verzerrt, und der Allocator-gegen-Zufall-Test war **gar nicht
durchfuehrbar** (siehe unten).

**Entfernt:** beide Vorfilter im Budget-Allocator, der Veto in
`hebel_risk_gate.py::post_check_hebel()`, der `hebel_richtung_modus`-Parameter aus
der Pipeline, und der Satz in Regel 2, der auf einen Ausfuehrungshinweis verwies,
**den es nie gab**.

**Verblieben:** genau zwei funktionale Lesestellen, beide an der
Praesentationsgrenze - `scheduler/background.py:1453` (E-Mail) und
`ui/hebel_view.py:121` (Anzeige). Die GUI bekam einen **Umschalter**
„handelbar/alle" statt hartem Ausblenden; Standard folgt der Einstellung.

**An der entfernten Stelle steht jetzt ein Nachtrag** („HIER STAND EIN
NUR-LONG-VETO, ES IST BEWUSST ENTFERNT") mit drei Gruenden: Messverfaelschung,
kein geschuetzter Gewinn, falscher Ort. Damit kann er nicht versehentlich
wiederkehren.

**Kein Budget angehoben - bewusst.** Gemessener Kopfraum 7- bis 16-fach
(`mistral_taegliches_budget` 400 gegen Tageslast 24-56). Wichtig zum Verstaendnis:
`taegliches_budget_gesamt` ist ein Deckel **pro Allocator-Lauf**, kein Tageszaehler.
Spot ist ueber `spot_rotation_reserve` garantiert, egal wie viele Hebel-Kandidaten
kommen; Marktscan waere der ungeschuetzte, aber die Schwelle liegt 15× ueber der
Realitaet.

**Im Betrieb bestaetigt** (05.08. abends, symbolgenau): sechs SHORT-Signale liefen
durch die Verarbeitung (ETH, LINK, TURBO, RENDER, XLM, GRIFFAIN), der E-Mail-Filter
unterdrueckte **genau diese sechs**. Die weiter feuernden Vetos sind CRV und
Stop-Abstand - die echten Qualitaetsgates.

## Nachtrag (2026-08-05): Konfidenz-Schwellen NICHT neu kalibriert - die Neukalibrierung waere Theater

**Ausgangslage:** durch den Mistral-Drift hat sich die Konfidenzverteilung um 10
Punkte verschoben und liegt als Masse exakt auf 70.

| | Median | ≥70 % | ≥75 % |
|---|---|---|---|
| bis 30.07. | 60,0 | 9 % | 5 % |
| ab 31.07. | 70,0 | **61 %** | 5 % |

Im aktuellen Baerenregime filtert die Schwelle 75 unveraendert. **Bei einem Wechsel
nach seitwaerts (65) liesse das Gate schlagartig 61 % statt 9 % durch.**

**Das Ergebnis der Messung beendet die Frage anders als erwartet: die Konfidenz
sagt nichts vorher.** Sie traegt keine Information ueber den Ausgang. Eine
Neukalibrierung haette also eine Schwelle auf einer Groesse justiert, die nicht
diskriminiert - **Theater mit Zahlen**.

**Verworfen, mit Revisit-Bedingung:** die Bucket-Methode (Testmethodik 2.8 verlangt
Verteilung vor Herleitung, die Dead-Loop-Synthese verwirft sie ohnehin). Revisit
nur, falls Konfidenz je nachweislich diskriminiert.

**Der Regimewechsel-Effekt bleibt aber ein realer Betriebspunkt** und ist als
solcher dokumentiert - er folgt nicht aus der Konfidenzqualitaet, sondern aus der
Verteilungsverschiebung.

## Nachtrag (2026-08-05): Ausstiegsregel scharfgeschaltet - Config, taeglicher Job, E-Mail

**Der groesste gemessene Hebel im System** (50 % standen bei +1R, nur 17,6 % kamen
an) lief bis dahin **rein passiv**: die Regel rechnete zwar, aber nur in Export und
Remote-Seite - beides muss man aufrufen. Im Export vom 05.08. standen **15 von 28
offenen Signalen ueber der Ausloeseschwelle, darunter SOL mit 10,63 R
ungesichert** - gesehen nur, weil zufaellig jemand hineinschaute.

**Gebaut:** Config-Schluessel mit vollstaendiger Herleitung
(`ausstieg_trailing_ausloese_r` / `_abstand_r`, beide 1,0), taeglicher Job **um
7:15** und eine Sammel-E-Mail (hoechstens eine pro Tag, keine wenn nichts anliegt,
sortiert nach hoechstem erreichten Buchgewinn).

**Die Uhrzeit ist keine Nebensache:** 7:15 liegt **nach** dem Backward-Tracking um
6:00, weil die Regel auf dessen `outcome_max_realisiertes_crv` rechnet. Vorher
haette sie auf Zahlen des Vortags gearbeitet.

**Abschaltbar** ueber `ausstieg_trailing_ausloese_r = 0`, ohne Codeaenderung. Der
Grund steht in der Config: **alle Kalibrierungszahlen stammen aus einer einzigen
Marktphase** (Baerenregime). In einer Aufwaertsphase koennte ein Trailing-Stop
Gewinner zu frueh beenden.

**Desktop-GUI bewusst NICHT gebaut, als OPTIONAL dokumentiert.** Die E-Mail bringt
die Information aktiv, die Remote-Seite zeigt sie unterwegs - die Desktop-GUI waere
der dritte Kanal fuer dasselbe. Nutzer-Entscheidung: „GUI machen wir spaeter".

## Nachtrag (2026-08-05): Remote-Seite bereinigt - was nicht mehr gemessen wird, wird nicht mehr gezeigt

Nutzer-Vorgabe: Informationen, die wir nicht mehr messen, sollen verschwinden,
neue wie die SHORT-Verteilung dazukommen.

**Umgesetzt:** ein **rekursiver** Filter `_ohne_entfernte_provider()` ueber fuenf
Karten statt fuenf Einzelloesungen (Groq und Cerebras sind vollstaendig entfernt,
tauchten aber weiter in Zaehlern und Historien auf), die Nur-Long-Gruppe aus der
Veto-Grund-Karte, und `_get_richtungsverteilung()` neu.

**Wichtig:** gefiltert wird **nur die Anzeige**. Daten und Export bleiben
vollstaendig - der Altbestand ist historisch korrekt und darf nicht verschwinden,
er ist nur nicht mehr aussagekraeftig fuer den laufenden Betrieb.

## Nachtrag (2026-08-05): Allocator gegen Zufall - an historischen Daten NICHT beantwortbar

**Stufe 2 der Messkette, nie gemessen.** Die Frage ist wichtig: waehlt der Allocator
besser als Zufall? Wenn nein, ist die ganze Screening-Ebene fraglich.

**Ergebnis: strukturell blockiert.** Der Nur-Long-Vorfilter hat bis zum 05.08.
bestimmt, welche Kandidaten ueberhaupt in die Auswahl kamen - jeder historische
Vergleich misst den Vorfilter mit, nicht die Auswahl.

**Kein Nullbefund, sondern eine Nichtmessbarkeit** - der Unterschied ist wichtig,
weil er die Frage offen laesst statt sie zu beantworten.

**Wiedervorlage in 2-3 Wochen mit Datumsfilter ab 2026-08-05**, sobald genug
Kandidaten ohne Vorfilter vorliegen. Das ist einer der konkreten Ertraege des
Nur-Long-Umbaus: die Messung wird ueberhaupt erst moeglich.

## Nachtrag (2026-08-05): halte_kriterium erstmals ausgewertet - zwei strukturelle Maengel

**941 gesetzte Zielpreise, nie gegen den tatsaechlichen Verlauf geprueft** (Stufe 6
der Messkette).

**Kein Trennnachweis** - das Kriterium unterscheidet Treffer nicht von Verlusten.
Wichtiger sind aber zwei **strukturelle** Maengel, die unabhaengig von der
Stichprobe gelten:

1. Der 45-Tage-Eimer ist mangels Zeit noch gar nicht auswertbar - **fruehestens ab
   Mitte September**.
2. `halte_kriterium_bucket` ist eine **Ablauffrist**, keine Strategieangabe - und
   widerspricht `mindestziel_zeitraum_tage_geschaetzt`. Damit haengt dieser Punkt
   am selben ungeloesten Konstruktionsfehler wie die Zieldauer (04.08.).

## Nachtrag (2026-08-05): drei neue Hebel-Fakten (Kosten, Ausstiegsregel, Systemguete) + Regeln 30/31

**Ausgangslage.** Acht Selektionsmechanismen waren zu diesem Zeitpunkt gemessen
und keiner trug nachweisbar — Screening-Score, Konfidenz, Richtungswahl,
Prompt-Regeln, CRV-Baender, `halte_kriterium`, Allocator-Auswahl. Am *Sortieren*
vorhandener Information war nichts mehr zu holen. Nutzer-Vorgabe deshalb: „merke
dir vor allem die Punkte wo wir Informationen derzeit NICHT dem LLM geben".
**Neue Information war die letzte unerprobte Kategorie.**

**Sechs Luecken identifiziert, drei umgesetzt.** Auswahlkriterium: die beiden
aussichtsreichsten (Kosten, Ausstiegsregel) waren bereits deterministisch
berechnet — es fehlte nur die Weitergabe. Und beide betreffen genau die Groessen,
die das Modell selbst setzt: Stop und Ziel.

| Fakt | Regel | Kern |
|---|---|---|
| `kosten` | 30 | Tabelle Kosten-in-R (5 Stop-Abstaende × 3 Haltedauern) + Median-Haltedauer 2,6 T. Tabelle statt Formel, weil ein rechnendes Modell falsch rechnet. Ausdruecklich **KEIN Limit** — Struktur hat Vorrang. |
| `ausstiegsregel` | 31 | Trailing-Mechanik der am selben Tag scharfgeschalteten Regel, inkl. „kein Breakeven-Lock" mit Begruendung. Liest die Config, ist also stumm wenn die Regel aus ist. |
| `systemguete` | 31 | EW / SQN / Profitfaktor der eigenen Trades. Mindestschwelle n≥30 → greift derzeit **nur bei Hebel** (124); Krypto 19, uebrige Tiers ≈ 0. |

**Drei bewusst NICHT gebaut** (verworfene Optionen, mit Revisit-Bedingung):

- **Z-3 Portfolio-Drawdown** — das 3+1-Raster ordnet ihn dem **Gate** zu (Frage 1
  bejaht: „Drawdown ueber Schwelle → Risiko reduzieren" ist kontextunabhaengig).
  Revisit nur, falls Z-3 je als graduelle statt binaerer Groesse gebraucht wird.
- **Ausfuehrbarkeit / `nur_long`** — gemessen und verworfen: der ehrliche Hinweis
  liess die EROEFFNEN-Quote von 93 % auf 3 % einbrechen. **Nicht anfassen.**
- **Zieldauer** — die zwei vorhandenen Felder widersprechen einander. Das ist ein
  Konstruktionsfehler, keine Prompt-Ergaenzung. Revisit nach Schliessen von
  Luecke 2 (Zielgroessen).

**Die Systemguete war der heikelste der drei.** Die Zahl ist unerfreulich (EW
−0,114 R, SQN „kaum handelbar"). Die naheliegende Formulierung „sei deshalb
vorsichtiger" waere genau der Fehler gewesen, der beim Ausfuehrbarkeits-Hinweis
den 93→3-%-Einbruch ausgeloest hat. Der Fakt traegt deshalb woertlich
„Kalibrierungs-Kontext, KEINE Handlungsanweisung". **Daraus folgt eine
Messpflicht:** die EROEFFNEN-Quote gehoert in jeden Test dieses Fakts, nicht nur
die Zonenqualitaet.

**Messung: kein Nachweis.** Drei-Arm-Design mit Rauschboden (A1/A2 identisch + B),
gepaart, 24 Faelle, alle drei Fakten kombiniert. Wirkung auf den Stop-Abstand
−0,334 pp, noetiges n **212**. Der Effekt halbierte sich beim Verdoppeln der
Stichprobe (−0,734 → −0,334) — klassische Signatur eines Nullbefunds.
EROEFFNEN-Waechter 92,5 / 92,1 / 95,7 %, kein Einbruch.

**Methodisch:** der Kosten-Fakt **allein** haette n=618 gebraucht, kombiniert
waren es 16. Fakten einzeln zu testen ist bei dieser Effektgroesse aussichtslos —
der gemeinsame Test war die richtige Entscheidung.

**Warum sie trotzdem bleiben:** bei 0,3 pp Effekt gegen 4,5 pp Rauschboden ist
„nicht nachweisbar" eine Aussage ueber die **Messgrenze**, nicht ueber die
Wirkung; Herausnehmen hiesse, auf eine Nicht-Messung hin zu handeln. Kein Schaden
messbar. Und sie schliessen namentlich dokumentierte Luecken (Zielgroessen 6.7,
Punkt 4).

**Offen (Stand 2026-08-06):**

1. **Ankunft im Produktivlauf nicht bestaetigt** — der letzte Export (05.08.
   19:54) ist aelter als die Commits (20:33 / 21:34); 0 von 176 Faktensaetzen
   enthalten die neuen Bloecke. Pruefpunkt des naechsten Exports.
2. **Beobachtungspunkt:** beide A-Arme lagen konsistent ~3 pp unter B. Bei
   n=67/69 nicht von Rauschen zu trennen, aber es ist die Richtung, vor der
   Regel 31 selbst warnt. Verfestigt sich das im Betrieb, gehoert `systemguete`
   wieder heraus.

**Uebergreifende Lehre, zweimal unabhaengig belegt:** kleine Stichproben erzeugen
zuverlaessig Scheinbefunde in der erwarteten Richtung. Regel-Ablationstest: +0,281
und +0,182 bei 12 Ankern, +0,014 und −0,013 bei 28. Hier: −0,734 bei 12, −0,334
bei 24. **Vielversprechende Zwischenstaende immer aufstocken, bevor berichtet
wird.**

*Ist-Zustand: `Regelwerksmanual.md` Kapitel 22. Katalog und Herleitung:
`Fakten_Entscheidungsmappe.md` Abschnitte 4.3 und 7.*

## Nachtrag (2026-08-06): Regime-Glaettung + Divergenz-Fakt - und eine Korrektur an meiner eigenen Begruendung

**Ausloeser:** Nutzer-Beobachtung „BTC ist drei Tage leicht gestiegen, aber
keine Aenderung in den Signalen". Nachgemessen: +1,78 %, Signale unveraendert.

**URSACHE IST KEINE TRAEGHEIT, SONDERN EINE ODER-BEDINGUNG.** `regime.py`:
`btc < ema50 ODER fgi in (Fear, Extreme Fear)` -> "baer". Eine Bedingung
genuegt. Fear & Greed stand an allen 31 Tagen zwischen 20 und 33. Zur
Einordnung: ausnahmslos jedes Signal der Historie traegt "baer" (1.391 Hebel,
2.223 Spot). Der halb erholte Zustand - Kurs ueber der EMA50 bei weiter
aengstlicher Stimmung - war fuer das System NICHT DARSTELLBAR.

**KORREKTUR AN MEINER EIGENEN BEGRUENDUNG, vom Nutzer angestossen.** Ich hatte
geschlossen, die Information gehoere nicht ans LLM - gestuetzt auf drei Belege:
das Modell reagiert nicht messbar auf das Label (n=29), Modelle sind mit
stetigen Zahlen schwach, und ein Mehrdeutigkeits-Label loest Abstention aus.

Nutzer-Einwand: das widerspricht den eigenen Regeln, es handelt sich um
essentielle Information, und der einzige Hinderungsgrund ist, dass wir nicht
wissen WIE wir sie uebergeben. **Der Einwand war berechtigt.** Meine drei Belege
rechtfertigen "nicht als Rohzahl" und "nicht als Mehrdeutigkeits-Label" - ich
hatte daraus "gar nicht" gemacht. Das ist eine Uebergeneralisierung und
widerspricht Frage 2 des eigenen Rasters.

Schlimmer: ich hatte einen Befund falsch herum gelesen. Dass das Modell auf das
heutige Label nicht reagiert, ist KEIN Beleg dass die Information nutzlos ist -
es ist ein Beleg dass die heutige UEBERMITTLUNG kaputt ist. Ein Label ohne Regel,
das sich nie aendert, kann nichts ausloesen.

**UMGESETZT, ZWEI TEILE:**

1. FAKT + REGEL (Krypto-Spot Regel 37, Hebel Regel 33). Neu:
   `regime.btc_zu_ema50.abstand_prozent` und `.einordnung`. Bewusst BEIDE
   Formen - Zahl fuer die Groessenordnung, Kategorie fuer die Verlaesslichkeit,
   dasselbe Muster wie CRV-Baender und Kostentabelle. Kein Band heisst "unklar"
   oder "uebergang"; die Regel benennt die Divergenz BEJAHEND ("fruehe
   Erholung") und sagt ausdruecklich, dass sie kein Grund fuer pauschale
   Vorsicht ist - der Hedging-Schutz, der bei Regel 31 schon noetig war.
   Nur die beiden Krypto-Pipelines; Aktien/Rohstoffe/Themen-ETF haben einen
   anderen Regime-Block ohne BTC-Bezug.

2. STETIGE KONFIDENZSCHWELLE, vorerst NUR IM SCHATTEN. `regime_score()` und
   `min_konfidenz_stetig()` in regime.py, als Felder in RegimeResult. Kein Gate
   liest sie; die Aktivierung ist ein eigener Schritt.

**KALIBRIERUNG, NACHGERECHNET STATT BEHAUPTET:** heutiger Zustand ergibt 74,7
statt hart 75,0. Da alle 3.614 Konfidenzwerte im System ganzzahlig sind, filtert
74,7 EXAKT wie 75,0 - gemessen 594 gegen 594 durchgelassene Signale, kein
Unterschied. Sichtbar wird die Aenderung erst in Lagen, die es heute nicht gibt
(BTC +3 % ueber EMA50 -> 73,7; +6 % -> 71,7).

**GEGENPRUEFUNG (`pruefe_regime_glaettung.py`, 33 Pruefungen, alle bestanden)** -
und sie hat einen ECHTEN FEHLER gefunden: beim Einfuegen des Einordnungs-Helfers
hatte ich die Interpolationsschleife von `min_konfidenz_stetig` herausgeschnitten
(die Ankersuche traf das erste von zwei `return punkte[-1][1]`). Die Funktion gab
danach fuer alle Zwischenwerte None zurueck. Ein Importtest haette das nie
gezeigt - die Datei laedt sauber. Dazu Struktur-Test per AST (liegt der Fakt
wirklich IM regime-Block?) und ein End-to-End-Lauf mit echten BTC-Daten:
Abstand -0,74 % -> "knapp darunter", Score 0,356 -> 74,8, diskretes Regime
unveraendert "baer".

## Nachtrag (2026-08-06): Divergenz-Fakt GEMESSEN - der Waechter haelt, keine Wirkung nachweisbar

Dreiarm-Test zu Regel 33/37 und `regime.btc_zu_ema50`, drei Laeufe, 94 Antworten,
**28 Faelle mit allen drei Armen**. Die historischen Faktensaetze tragen den Fakt
noch nicht - er wurde je Signaldatum aus der BTC-Reihe rekonstruiert (EMA50 nur
aus Kursen BIS zum Signaltag, kein Blick in die Zukunft). Beobachtete Spanne
-1,94 % bis +0,15 %, also drei verschiedene Baender.

| | Wirkung (B−A1) | t | Rauschboden | Verhaeltnis | noetiges n |
|---|---|---|---|---|---|
| **EROEFFNEN** | **96,4 / 96,4 / 96,4 %** | — | — | — | — |
| Konfidenz | −0,750 | −0,74 | 4,087 | 0,18x | 197 |
| Stop-Abstand | −1,014 | −0,78 | 6,321 | 0,16x | 176 |

**DER WAECHTER HAELT - das war die entscheidende Frage.** Die EROEFFNEN-Quote ist
in allen drei Armen auf die Nachkommastelle identisch. Ein Fakt ueber eine
Marktlagen-Divergenz haette strukturell in dieselbe Richtung wirken koennen wie
der Ausfuehrbarkeits-Hinweis, der die Quote einmal von 93 % auf 3 % gedrueckt
hat. Der Hedging-Schutz in der Regel ("weder ein Grund fuer pauschale Vorsicht
noch fuer pauschale Zuversicht, und kein Anlass weniger vorzuschlagen") war
also nicht ueberfluessig, sondern hat seinen Zweck erfuellt.

**Kein Wirkungsnachweis, aber auch kein Schaden** - dieselbe Lage wie bei den
drei Fakten vom 05.08. Nach dem Ausstiegsverfahren (Mappe 7.4b) bleibt die Regel
damit drin: kein Ausstiegsgrund ist ein fehlender Wirkungsnachweis, wenn der
Effekt unter der Messgrenze liegt (hier 0,16-0,18x des Eigenrauschens).

**Stabil ueber die Aufstockung**, anders als beim Regime-Test: n=20 zeigte
EROEFFNEN 95,0/95,0/95,0 und Konfidenz −0,500, n=28 zeigt 96,4 dreimal und
−0,750. Kein Vorzeichenwechsel, keine Halbierung - das Bild war von Anfang an
dasselbe.

## Nachtrag (2026-08-06): Gesamtaufnahme der fehlenden Fakten + Ausstiegsverfahren statt Abbruchschwelle

**Nutzer-Einwand, der beides ausgeloest hat:** die drei neuen Fakten wirkten wie
„ok wir haben sie, aber ob es etwas bringt und warum wir sie einsetzen ist unklar
bzw. koennte das auch negative Auswirkungen haben". Dazu die Vorgabe: kein
radikaler Abbruch, sondern ein sauberer Ausstieg - und vorher pruefen, welche
Fakten dem Modell sonst noch fehlen.

### Teil 1: Ausstiegsverfahren statt Schwellwert

Ich hatte zuvor ein hartes Kriterium gesetzt („EROEFFNEN-Quote unter 85 % ueber
≥60 Faelle → Block fliegt raus"). **Das war derselbe Konstruktionsfehler wie ein
hartes Gate: es entscheidet ohne Ursachenpruefung.** Eine gesunkene Quote kann vom
Fakt kommen - oder vom Regime, von einem Provider-Drift wie am 31.07., oder von
einer anderen Aenderung im selben Fenster.

**Neu, vierstufig** (`Fakten_Entscheidungsmappe.md` 7.4b, gilt fuer JEDEN Fakt):

| Stufe | |
|---|---|
| 0 | laufende Beobachtung ueber `bloecke_je_tag` im Export |
| 1 | Schwelle loest **Pruefpflicht** aus, nicht Entfernung |
| 2 | **drei Alternativen ausschliessen**: Provider-Drift (Kanarienvogel-Replay), Regime (getrennt auswerten), andere Aenderung im Fenster (Deploy-Liste) |
| 3 | Entscheidung mit schriftlicher Begruendung im Entscheidungslog + Revisit-Bedingung; **kleinste wirksame Aenderung** (nur der verdaechtige Block, nicht die Gruppe) |
| 4 | Ruecknahme nach dem **Nur-Long-Muster**: Nachtrag an der Codestelle, Katalogeintrag auf *entfernt*, und die Wirkung der Entfernung messen |

**Ausdruecklich KEIN Ausstiegsgrund:** eine weiterhin negative Systemguete (der
Block soll die Zahl melden, nicht sie verbessern), ein weiterhin fehlender
Wirkungsnachweis (bei 0,3 pp gegen 4,5 pp Rauschboden waere die Entfernung
genauso unbegruendet wie die Einfuehrung), und ein Abrieb innerhalb des
Rauschbodens - genau die Konsistenz erzeugen kleine Stichproben zuverlaessig.

### Teil 2: Gesamtaufnahme der fehlenden Fakten

Erstellt durch **Differenzbildung** statt Nachdenken: alle 48 Bloecke des
Notebook-Exports gegen die 20 Bloecke, die `build_hebel_facts()` liefert. Jeder
Kandidat durch das 3+1-Raster. Vollstaendig in `Fakten_Entscheidungsmappe.md`
Abschnitt 8.

**Die klarste Luecke ist eine PIPELINE-ASYMMETRIE:** der Hebel-Analyst setzt das
CRV und kennt nur die Mindestgrenze aus Regel 5. Der Spot-Analyst - mit n=19
ausgewerteten Trades weit duennerer Datenbasis - bekommt seit dem 03.08. die
vollen gemessenen Baender als Regel 36. **Die Pipeline mit den belastbaren Daten
hat die schwaechere Regel.** Die Hebel-Baender sind gemessen und exportiert:

| CRV-Band | n | Ziel | Basislinie | Abstand | belastbar |
|---|---|---|---|---|---|
| 2,0-2,5 | 79 | 24,0 % | 13,1 % | +10,9 pp | nein |
| **2,5-3,0** | 34 | 43,1 % | 8,6 % | **+34,5 pp** | **ja** |
| 3,0-4,0 | 33 | 20,5 % | 7,7 % | +12,7 pp | nein |
| ≥ 4,0 | 26 | 5,1 % | 3,1 % | +2,1 pp | nein |

> **Beim Bauen aufpassen:** die absolute Quote im Band ≥ 4,0 bricht ein, **aber
> die Basislinie bricht mit**. Das ist Horizont-Trunkierung - exakt der Artefakt,
> der am 03.08. als „CRV ≥ 4,0 ist das schlechteste Band" gemeldet und widerrufen
> wurde. Nur `abstand_zur_basislinie_pp` darf in einen Fakt, absolute Quoten nie.

**Sechs weitere Kandidaten, alle bewusst nachgelagert - nicht aus Aufwandsgruenden:**

- **Eigene HALTEN-Bilanz** (n=12, Trefferquote 8,3 %) und **Konfidenz-Versatz**
  (vorhergesagt 77,5 % → tatsaechlich 33,3 %): warten auf den Abschluss des
  Ausstiegsverfahrens zu `systemguete`. **Zwei Selbstbewertungs-Fakten
  gleichzeitig einzufuehren machte einen negativen Befund unzuordenbar.**
- **Zieldauer**: Datenarbeit, keine Prompt-Arbeit - solange kein Feld eine
  Zieldauer traegt, hat jede Prompt-Regel nichts, worauf sie sich bezieht.
- **Klumpenrisiko im Portfolio**: offene Achsenfrage, kein Blocker. Meine erste
  Einschaetzung („`hauptgruppe` nur bei 13 von 57 befuellt") war zu eng -
  Nutzer-Hinweis vom 06.08.: *„die Kategorie-Thematik halte ich fuer nicht so
  problematisch, die Bewertung muss ohnehin je Gruppe gesondert erfolgen."*
  Richtig: `assetklasse` und `rolle` sind 57 von 57 befuellt. Offen ist damit
  nicht die Datenlage, sondern **welche Gruppierungsachse** die richtige ist.
- **Veto-Schatten je Grund**: naechster Verwandter des Ausfuehrbarkeits-Hinweises,
  zudem fragile Zahl (5 Faelle tragen 221 % des Mittelwerts, `vorzeichen_kippt`).
- **Relative Rangposition**: strukturell die einzige Information, die das Modell
  nicht selbst herleiten kann - kaeme aber aus dem Screening-Score, und der
  diskriminiert gemessen nicht. Scheinpraezision.

**`score_gesamt` gehoert entfernt, nicht ergaenzt** - liegt heute als nackte Zahl
ohne Regel im Faktensatz, die schlechteste aller Varianten (Beschluss 03.08.).

### Teil 3: ein Messfehler, der die Verifikation fast in die Irre gefuehrt haette

Bei der Verifikation am Morgen des 06.08. trugen **0 von 177 Faktensaetzen** die
neuen Bloecke. Das sah nach einem Verdrahtungsfehler aus und war keiner:
`_hebel_faktensaetze()` hatte das Fenster fest auf `2026-07-26`..`2026-08-05`
verdrahtet - das Fenster des Regel-28-Tests. Die Fakten kamen am Abend des 05.08.

**Behoben:** rollierendes Fenster (14 Tage) plus neuer Block `bloecke_je_tag`, der
je Tag zaehlt, welche Fakt-Bloecke tatsaechlich im `facts_json` standen - ueber
ALLE Zeilen des Fensters, nicht nur ueber die geschichtete Stichprobe. Damit ist
die Ankunftsfrage fuer jede kuenftige Fakten-Aenderung ohne Umweg beantwortbar.

> **LEHRE:** ein Analyse-Export, der fuer EINE Fragestellung gebaut wurde,
> verfaellt still. Wer ihn danach zur Verifikation benutzt, misst das Fenster
> statt der Sache.

### Teil 4: der Nur-Long-Umbau ist im Betrieb bestaetigt

Am Morgen des 06.08. liefen 22 Hebel-Signale, davon **5 EROEFFNEN - alle SHORT**
(TURBO ×2, HYPE, ONDO, INJ), alle mit `hebel_final = 3.0`. Dass dort ein Hebel
steht, ist der Beleg: das Risk-Gate hat sie bewertet und nicht vetot. Der
E-Mail-Filter unterdrueckte genau diese fuenf, protokolliert je Symbol. Zum
Vergleich die Vortage: 02.08. 38 SHORT und **0** EROEFFNEN, 04.08. 25 SHORT und
**0** EROEFFNEN. Seit dem Umbau 12 SHORT-EROEFFNEN - eine Kategorie, die es
vorher strukturell nicht geben konnte.

**Nicht bewertbar bleibt die Signalmenge** (22 gegen 32-57 an Vortagen): die
Produktion war waehrend der Desktop-Tests zeitweise offline, und es war erst der
Morgen-Batch. Zwei moegliche Ursachen fuer dieselbe Zahl - deshalb kein Befund.

## Nachtrag (2026-08-06): der "Sprung bei CRV 4,0" gegengeprueft - es gibt keinen, und MFE >= 1R ist als Erfolgsmass untauglich

**Nutzer-Einwand:** der Sprung sei ihm „sehr oft vorgekommen und war irgendwie
bewiesen, dass dieser existiert und eine besondere Zone ist". Berechtigt - und
meine Erklaerung dafuer war **falsch adressiert**. Nachgerechnet in
`pruefe_sprung_bei_crv4.py` an **871 Signalen** gegen 491 der Originalmessung.

**KORREKTUR AN MIR SELBST.** Ich hatte den Sprung pauschal als
Trunkierungs-Artefakt bezeichnet. Das gilt nur fuer das Mass "Ziel erreicht".
Regel 36 nutzte aber "MFE >= 1R", und darauf wirkt Trunkierung **nicht** - die
Schwelle 1R ist fest, unabhaengig vom CRV. Zwei verschiedene Messgroessen unter
einem Etikett.

**WAS STATTDESSEN DAHINTERSTECKT.** CRV = Zielabstand / Stopabstand. Ein hohes
CRV entsteht auch durch einen ENGEN Stop - und bei engem Stop ist 1R eine
winzige Kursbewegung, "MFE >= 1R" wird mechanisch leicht.

| CRV-Band | MFE >= 1R | Median-Stop |
|---|---|---|
| 2,0-2,5 | 27,1 % | 6,25 % |
| 2,5-3,0 | 37,3 % | 5,62 % |
| 3,0-4,0 | 46,7 % | 4,22 % |
| >= 4,0 | 63,9 % | **2,56 %** |

**Es gibt gar keinen Sprung** - in der groesseren Stichprobe steigt es glatt,
und der Stop-Abstand faellt spiegelbildlich. **Der Stop-Abstand ALLEIN trennt
schaerfer als das CRV** (54,0 / 25,1 / 15,8 % ueber die Stop-Terzile, Intervalle
getrennt). Kontrolliert man ihn, schrumpft der CRV-Effekt von +36,8 auf
+13,4 pp und alle Intervalle ueberlappen. Das CRV war ein **Stellvertreter fuer
die Stop-Enge**.

**UND DANN KIPPT ES** - die Nutzer-Formulierung traf den Kern: „es geht nicht um
den Wert, sondern wann dieser Wert alles zum Kippen bringt."

| Stop-Abstand | n | MFE >= 1R | Ergebnis (EW) |
|---|---|---|---|
| **0-2 %** | 47 | **55,3 %** | **-1,043 R** |
| 2-3 % | 53 | 37,7 % | -0,479 R |
| **3-5 %** | 117 | 64,1 % | **+0,340 R** |
| 5-8 % | 136 | 36,0 % | -0,438 R |

Unter 2 % Stop-Abstand meldet die Kennzahl 55 % Erfolg bei einem Erwartungswert
von **-1,04 R**: praktisch jeder Trade wird voll ausgestoppt. Der Kurs tippt 1R
an, weil 1R dort fast nichts ist, und nimmt danach den Stop mit.

> **STEHENDE LEHRE:** "MFE >= 1R" taugt NICHT als Erfolgsmass fuer Fragen, bei
> denen der Stop-Abstand mitvariiert - es belohnt genau das, was das Ergebnis
> zerstoert. Fuer solche Fragen "Ziel erreicht" gegen eine Basislinie mit
> DEMSELBEN Stop und DEMSELBEN Horizont verwenden.

**FOLGEN.** Die Umstellung von Regel 36 auf das Mass "Ziel erreicht" war damit
richtig - aber aus einem anderen Grund als dem, den ich angegeben hatte. Die
Warnung in den neuen Regeln ("zieh niemals den Stop enger, um in ein besseres
Band zu rutschen") ist jetzt an Zahlen belegt statt nur vorsichtig formuliert.

**Dieser Punkt wurde noch am selben Tag geklaert - siehe naechster Nachtrag.**

## Nachtrag (2026-08-06): Widerspruch 3-5 % gegen 5-8 % aufgeloest - beide Zahlen waren Survivorship-Artefakte

**Nutzer-Auftrag:** "den Widerspruch 3-5 % vs 5-8 % sauber nachmessen". Der
Export vom selben Morgen reichte dafuer (vollstaendige OHLC aller 33
Hebel-Symbole, 08.05.-06.08.) - kein neuer Lauf noetig.

**ES GAB NIE EINEN WIDERSPRUCH.** Beide Ausgangszahlen litten am selben Fehler:
sie werteten nur AUFGELOESTE Faelle aus.

  01.08.: "SL < 5 % hat 0-16,7 % Trefferquote, 5-10 % hat 31,2 %" - 61
          aufgeloeste Trades.
  06.08.: "3-5 % kommt auf +0,340 R, 5-8 % auf -0,438 R" - 446 aufgeloeste.

Ob ein Signal aufloest, haengt aber vom STOP-ABSTAND ab - genau der Variablen,
um die es geht. Ein enger Stop wird fast immer getroffen, loest schnell auf und
landet mit -1 R in der Stichprobe. Ein weiter Stop bleibt offen und faellt
HERAUS, auch wenn er spaeter gewonnen haette. **Die Stichprobenauswahl hing am
Messgegenstand.** Das ist derselbe Mechanismus, an dem die CRV-Gate-Messung vom
02.08. gebrochen ist (widerlegt 03.08. in bd7aa86) - und ich bin ihm am 06.08.
erneut aufgesessen, keine 48 Stunden nachdem er dokumentiert wurde.

**RICHTIG GEMESSEN** (`messe_stop_abstand_baender.py`): kein Aufloesungs-Filter,
jedes Signal mit Zonen neu gegen die Preisreihe simuliert (Unaufgeloeste
bekommen Mark-to-Market statt herauszufallen), Basislinie je Band mit DEMSELBEN
Stop und CRV, Block-Bootstrap ueber Symbole, zwei Horizonte, nach Richtung
getrennt. Simulation aus `analyse_crv_gate_survivorship.py` importiert statt
nachgebaut.

| Stop-Band | n | EW | Bootstrap-KI | Abstand zur Basislinie |
|---|---|---|---|---|
| **0-2 %** | 26 | -0,770 | **[-1,124; -0,500]** | **-0,526** |
| 2-3 % | 37 | +0,182 | [-0,604; +1,801] | +0,421 |
| 3-5 % | 98 | +0,433 | [-0,185; +0,848] | +0,668 |
| 5-8 % | 147 | -0,036 | [-0,359; +0,364] | +0,142 |
| 8-12 % | 113 | -0,047 | [-0,319; +0,163] | +0,082 |
| > 12 % | 72 | +0,224 | [-0,285; +0,521] | +0,317 |

**EINZIGER BELASTBARER BEFUND: Stops unter 2 % sind zerstoererisch.** Als
einziges Band schliesst das Intervall die Null aus und liegt klar unter der
Basislinie. Bei H14 bestaetigt (-1,088, [-1,198; -1,000]), bei LONG allein
ebenfalls (-1,061). **Alles andere ist nicht trennbar** - jedes uebrige
Intervall enthaelt die Null, 3-5 % ueberlappt 5-8 % vollstaendig.

Beide Behauptungen fallen damit: "unter 5 % schlecht" ist zu grob (wirft das
schlechteste Band mit den beiden besten Punktschaetzern zusammen), "5-8 %
negativ" haelt survivorship-bereinigt nicht.

**FOLGE FUER REGELN: die Daten stuetzen eine UNTERGRENZE, keinen Optimalwert.**
Ein Richtwert "Stop moeglichst bei X %" waere durch nichts gedeckt. Ein Hinweis
"unter 2 % ist der Trade strukturell nicht ueberlebensfaehig" ist es - und er
deckt sich mit dem Kostenfakt (enge Stops doppelt teuer) und mit dem Befund aus
dem vorigen Nachtrag, dass genau dort MFE und Ergebnis auseinanderlaufen.
NOCH KEINE REGELAENDERUNG - erst zur Entscheidung vorlegen.

**Einschraenkung:** 533 Signale fielen bei H7 aus, weil die Preisreihe den
Horizont nicht abdeckt. Reiner Zeiteffekt (junge Signale haben noch keine 7 Tage
Zukunft), also NICHT stop-abhaengig - die Bandvergleiche bleiben unberuehrt.
SHORT ist je Band zu duenn (n=2-17); die Aussage traegt LONG.

## Nachtrag (2026-08-06): Gate-Untergrenze fuer den Stop-Abstand - EXISTIERT BEREITS, nichts gebaut

**Auftrag:** die Untergrenze als Gate ausarbeiten, mit Begruendung warum ja und
warum nein, plus die Frage "wie kommen die unter 2 Prozent ueberhaupt zustande
und wo erfolgt die richtige Filterung". **Die Ausarbeitung endet bei NICHT
UMSETZEN** - die Regel gibt es, zweistufig, und sie ist richtig kalibriert.

**WAS EXISTIERT** (beides seit 02.08., fuer ALLE Assetklassen, es vetot die
STRENGERE der beiden):

| | Schwelle | faengt |
|---|---|---|
| **RM-1b** `sl_abstand_eng_schwelle_relativ` | Stop < **2,5 %** absolut | den strukturellen Mindestabstand: Gebuehren, Spread, Grundrauschen |
| **RM-1c** `sl_abstand_min_atr_faktor` | Stop < **0,75 × ATR** | den Fall, wo 2,5 % absolut reichen, fuer DIESES Symbol aber im Rauschen liegen |

**WIE DIE UNTER-2-%-FAELLE ZUSTANDE KAMEN - sie sind aelter als die Regel.** Von
36 Signalen mit Stop < 2 % haben 24 kein Veto, und **alle 24 stammen vom
14.-29.07.**, also von VOR dem 02.08. Seit RM-1b scharf ist, ist kein einziges
mehr ohne Veto durchgekommen. Der Befund aus dem vorigen Nachtrag ist damit
**keine Luecke, sondern eine unabhaengige survivorship-freie Bestaetigung** einer
Regel, die auf ganz anderer Datenbasis kalibriert wurde.

**DIE KALIBRIERUNG SITZT RICHTIG.** Feinaufloesung um die Schwelle, Horizont 7,
Abstand zur mechanischen Basislinie mit demselben Stop:

| Band | n | Abstand zur Basislinie |
|---|---|---|
| 0,0-1,5 % | 11 | −0,667 |
| 1,5-2,0 % | 15 | −0,395 |
| 2,0-2,5 % | 14 | +0,133 |
| **2,5-3,0 %** | 23 | **+0,597** |
| 3,0-4,0 % | 49 | +0,348 |

Der Uebergang zu klar positiv liegt bei **2,5 %** - exakt dort, wo RM-1b steht.
Und die Schwelle ist auch nicht zu streng: das Band direkt darunter traegt mit
+0,133 praktisch nichts ueber dem Zufall bei.

**WARUM KEIN ZWEITES GATE.** Es waere eine **Dublette** - zwei Regeln fuer
dieselbe Sache mit zwei Schwellen, die auseinanderlaufen koennen. Genau diesen
Fehlertyp hat der Regler-Audit am 03.08. gefunden und entfernt (zwei
Config-Namen fuer eine Codestelle). Ein *lockereres* Gate bei 2 % waere zudem
reine Attrappe, weil die strengere Grenze ohnehin gewinnt.

**DIE ARCHITEKTUR IST BEWUSST DREITEILIG** und beantwortet die Frage nach dem
richtigen Filterort: weiche **Prompt-Leitplanke** (Regel 6: ziele auf
1,5-2 × ATR) als Zielwert, **RM-1c** als volatilitaets-relative Notbremse bei
0,75 × ATR, **RM-1b** als absolute Untergrenze. Das Gate ist die Notbremse,
nicht der Zielwert - deshalb liegt die Prompt-Empfehlung deutlich darueber.

**GEAENDERT, beides ohne Verhaltenswirkung:** die Veto-Begruendung in
`hebel_risk_gate.py` zitierte "0 von 20 aufgeloesten Signalen" aus der
01.08.-Messung - also genau die survivorship-behaftete Zahl, die derselbe Tag
widerlegt hat. Ersetzt durch die sauberen Werte. Im Spot-Gate
(`risk_gate.py`) ein Bestaetigungsvermerk ergaenzt, damit die Verifikation auch
dort auffindbar ist (stehende Regel "bei Funden immer ALLE Asset-Varianten
pruefen").

**Falls je eine Aenderung gewollt ist:** der einzige begruendbare Hebel waere
eine ANHEBUNG von 2,5 %, weil das Band 2,5-3,0 % mit Abstand am besten
abschneidet. Davon ist abzuraten - n=23, und ein schaerferes Gate widerspricht
der Vorgabe "mehr Signale durch Qualitaet, nicht durch Lockerung" in die andere
Richtung.

## Nachtrag (2026-08-06): Cron-Staggering NICHT gebaut - die Sperren sind selbst produziert

**Nutzer-Einwand vor der Umsetzung:** *"mach das Cron-Staggering aber nur wenn
tatsaechlich vorhanden - Ursache vom zeitlichen Bereich sind diese Faelle selbst
produziert meiner Meinung nach."* **Der Einwand war richtig, und der Beleg ist
eindeutig.** Ich hatte das Staggering selbst vorgeschlagen, gestuetzt auf einen
Befund vom 04.08. - ohne zu pruefen, ob er sich wiederholt.

**23 "database is locked" im 72-Stunden-Fenster. Alle vier abendlichen Sperren
fallen exakt in einen App-NEUSTART:**

| Neustart (`Added job ... to job store`) | Sperre |
|---|---|
| 03.08. 20:11:28 | 20:12 |
| 04.08. 20:51:54 | 20:52 |
| 05.08. 19:43:11 | 19:43 |
| 05.08. 19:52:37 | 19:53 |

Beim Start feuern alle Jobs gleichzeitig, waehrend die DB noch initialisiert
wird. Das sind unsere eigenen Pull-und-Neustart-Zyklen, kein
Produktionsverhalten.

**Und das 06:30-Fenster haelt der Pruefung ebenfalls nicht stand:**

| Tag | Sperren im Fenster 06:29-06:36 |
|---|---|
| 04.08. | 8 |
| 05.08. | **0** |
| 06.08. | **0** |

Am 05. und 06.08. lief praktisch dieselbe Job-Konstellation ohne jede Sperre.
Der Unterschied am 04.08.: dort liefen zusaetzlich `kategorie_synthese_job` und
`refresh_aktien_ohlc_job` in diesem Fenster - eine Sonderkonstellation, nicht
der Normalfall.

**Ein Einzelfall vor zwei Tagen, seither nicht reproduzierbar.** Den Scheduler
dafuer umzubauen waere eine Aenderung ohne belegtes Problem, mit der bekannten
Nebenwirkung, dass Job-Zeiten auseinanderlaufen.

> **LEHRE:** Ein Betriebsfehler, der EINMAL auftrat, ist kein Muster. Vor jeder
> Infrastruktur-Aenderung pruefen, ob er sich in den Folgetagen wiederholt -
> und ob die betroffenen Zeitpunkte mit eigenen Eingriffen zusammenfallen.

## Nachtrag (2026-08-06): die drei neuen Fakten sind im Betrieb ANGEKOMMEN - Verifikation abgeschlossen

Der seit dem 05.08. offene Punkt ist geschlossen. Export vom 06.08. 07:56, neuer
Block `bloecke_je_tag`:

```
2026-08-06:  22 Saetze | kosten=22  ausstiegsregel=22  systemguete=22
```

**Alle 22 Faktensaetze des Tages tragen alle drei Bloecke**, mit echtem Inhalt
(Kostentabelle 5 Zeilen, Trailing aktiv, Systemguete n=126 / EW -0,106). Das
rollierende Fenster aus demselben Commit funktioniert ebenfalls.

**Noch offen, beides erwartbar:** `crv_baender` und die `score_gesamt`-Entfernung
kamen nach dem Morgen-Signallauf und brauchen einen weiteren Pull.

**EIGENER FEHLER IM NEUEN WERKZEUG, am selben Tag gefunden und behoben:** der
Zaehler zaehlte nur Top-Level-Bloecke - und sah damit ausgerechnet den Fall
nicht, der gerade verfolgt wurde. `score_gesamt` liegt VERSCHACHTELT unter
`trigger`; seine Entfernung waere im Zaehler unsichtbar geblieben und ich haette
sie faelschlich als erledigt gelesen. Zaehlt jetzt zwei Ebenen ("eltern.kind").
Verifiziert an einer synthetischen DB: 3 von 5 Saetzen mit
`trigger.score_gesamt` korrekt erkannt.

## Nachtrag (2026-08-06): Vollcheck des Exports - zwei neue Werkzeuge, ein DB-Backup, und ein falsches Gruen im eigenen Skript

**Nutzer-Auftrag nach der Aenderungsphase:** neue Fehler, funktionieren die
Fixes, laeuft Monitoring/Backtracking/Messen sauber, fehlen relevante
Informationen, Status der Messpunkte.

**Zwei Werkzeuge gebaut**, weil beide Fragen verschieden sind:

- `pruefe_export_standard.py` - der feste 15-Punkte-Katalog aus
  Test_und_Verifikationsmethodik 2.1. Fragt: *sind die Kennzahlen auffaellig?*
- `pruefe_export_vollcheck.py` - fragt: *stimmt das, was wir glauben gebaut zu
  haben?* Der Nur-Long-Umbau haette in JEDEM Kennzahlen-Katalog unauffaellig
  ausgesehen, weil er die Kennzahlen gar nicht beruehrt.

**ERGEBNIS - alles Wesentliche gruen.** Nur-Long-Veto tot seit 05.08. 13:46,
5 SHORT-EROEFFNEN im regulaeren Pfad, E-Mail-Filter griff exakt 5x;
Ausstiegsregel gelaufen mit 16 Empfehlungen ueber 22,4 R; die drei neuen Fakten
in 22 von 22 Faktensaetzen; Backward-Tracking, Veto-Schatten, Selbst-HALTEN,
Systemguete und Z.ai-Gegenpruefung alle aktuell; **null haengende Signale**
aelter als 21 Tage ohne Outcome.

**ALLOCATOR VERDRAENGT NICHTS** - der beim Umbau befuerchtete Effekt tritt nicht
ein: "Hebel 22/22, Marktscan 0/0 (ueberfaellig=0), Spot 40/40 ausgewaehlt".
Jede Stufe bekam 100 % dessen, was sie angefordert hat.

**ZWEI FEHLER IM EIGENEN SKRIPT, beim ersten Lauf gefunden:**

1. **Falsches Gruen bei `score_gesamt`.** Gemeldet wurde "entfernt: 0 von 22" -
   der Zaehler in jenem Export war aber die alte, nur-Top-Level-Fassung. Eine
   Null bedeutet dort "nicht gezaehlt", nicht "nicht vorhanden". Der Check
   haengt jetzt explizit an der Zaehler-Version und meldet "NICHT PRUEFBAR".
   **Ein Pruefskript, das einen blinden Fleck als Bestaetigung ausgibt, ist
   schlimmer als keines.**
2. **Falsche Erwartung bei Cerebras.** Ich hatte Altdaten im Export als Problem
   gewertet - die Entscheidung vom 05.08. war aber ausdruecklich, dass NUR die
   Anzeige gefiltert wird. Historische Cerebras-Signale sind korrekte Historie.

**DB-BACKUP im Exportlauf** (Nutzer-Vorschlag), bewusst nicht als Dateikopie:
`Connection.backup()` fuer einen konsistenten Snapshot waehrend die App
schreibt, `PRAGMA integrity_check` AUF DER KOPIE, gzip, Rotation 7 - und die
Rotation loescht erst NACH bestandener Pruefung, sonst nimmt ein
fehlgeschlagener Lauf die letzten guten Staende mit. Ablage
`Claude_Austauschordner/DB_Backups`; der Laufwerksbuchstabe wird ueber
`_google_drive_wurzel()` je Geraet aufgeloest (Notebook G:, Desktop K:).

## Nachtrag (2026-08-06): FX-Ableitung - die Pruefgroesse war der Fehler, und Z-3 ist arithmetisch korrekt

**Ausloeser:** der Vollcheck meldete 1174 verworfene FX-Ableitungen im
Log-Fenster, waehrend Z-3 seit dem 05.08. Alarm schlaegt. Nutzer-Auftrag: dem
nachgehen und den Z-3-Wert pruefen.

**Z-3 IST ARITHMETISCH KORREKT.** Aus der Reihe nachgerechnet: Hoch 102,832 am
2026-05-10, aktuell 85,515 -> Rueckschlag **16,84 %**, groesster Rueckschlag
**19,04 %**. Beides trifft `z3_status` auf zwei Nachkommastellen. Auch die
Verkettung ist sauber gebaut - die Tagesrendite laeuft auf dem VORTAGES-Korb
und verlangt beide Kurse, ein Basiswechsel erzeugt also keinen Levelsprung
(am 05.08. wechselt die Reihe von "rekonstruiert" mit 156 Symbolen auf
"laufend" mit 33).

**DIE REIHE DARUNTER WAR AUSGEHUNGERT, und zwar durch ein untaugliches Mass.**
`tages_fx_kurse()` verwarf einen Tag, wenn die SPANNWEITE max-min der aus 35
Symbolen abgeleiteten Quotienten 2 % ueberstieg. Die Spannweite ist nicht
robust - sie haengt nur an den beiden Extremwerten und waechst mit der
Stichprobe. EIN kaputtes Symbol genuegt, egal wie einig die anderen 34 sind.

| Verfahren | gueltige Tage |
|---|---|
| bisher: (max-min)/Median <= 2 % | **4** von 91 |
| Interquartilsabstand <= 2 % | **91** von 91 |
| >= 80 % der Symbole binnen 1 % | 91 von 91 |
| getrimmte Spannweite | 91 von 91 |

Ueber die gesamte Kurshistorie wurden 589 von rund 750 Tagen verworfen, davon
**88 der 90 Tage im Z-3-Fenster**.

**DER MEDIAN WAR DIE GANZE ZEIT RICHTIG:** 0,8486 bis 0,8810 mit hoechstens
0,87 % Tagesaenderung - genau das Verhalten eines echten EUR/USD-Kurses.
Verworfen wurde ein korrekter Wert wegen eines falschen Streuungsmasses.

**HAUPTAUSREISSER IST CAT:** an 59 von 91 Tagen der schlechteste Wert, mediane
Abweichung **3,79 %** - zwoelfmal so viel wie das naechstschlechte Symbol. CAT
ist hier nicht zum ersten Mal auffaellig (Spot-Konzentration 03.08.: ohne CAT
kippt das Ergebnis von +10,7 auf -6,1 R). **Der Fix macht das System nur robust
DAGEGEN - die Kursreihe selbst gehoert eigenstaendig geprueft.**

**UMGESETZT:** Interquartilsabstand statt Spannweite, Grenze unveraendert 2 %.
Zweck bleibt erhalten (breite Uneinigkeit und zu duenne Tage werden weiter
verworfen), das Log nennt jetzt den groessten Ausreisser namentlich.

> **FOLGE, die man kennen muss:** der Z-3-Wert WIRD sich beim naechsten Lauf
> aendern, weil mehr Tage einen FX-Kurs bekommen und dadurch weniger Symbole
> als "ohne Kurs" ausfallen. Die 16,84 % sind richtig gerechnet, ruhen aber auf
> duenner Abdeckung (3 bis 20 Symbole ohne Kurs je Tag). **Ob der Alarm danach
> noch steht, ist offen.**

> **UEBERGREIFENDE LEHRE:** eine Kennzahl, die auf Extremwerten beruht
> (Spannweite, Minimum, Maximum), ist bei wachsender Stichprobe kein
> Qualitaetsmass mehr, sondern ein Ausreisser-Detektor. Wo "sind sich die
> Quellen einig?" gemeint ist, gehoert ein robustes Streuungsmass hin.

## Nachtrag (2026-08-06): CAT - die EUR-Seite ist kaputt, und die Ursache ist Illiquiditaet

**Folgeauftrag zum FX-Befund:** welche der beiden Kursreihen stimmt nicht?

**DER ENTSCHEIDENDE TEST IST DIE RENDITEKORRELATION, nicht der Kursstand.** Aus
dem Quotienten allein laesst sich das nicht sagen - er ist symmetrisch. Beide
Reihen beschreiben aber DENSELBEN Vermoegenswert, ihre Tagesrenditen muessen
sich also fast decken (EUR/USD bewegt sich taeglich um Bruchteile).

| | CAT | Median aller 35 Symbole |
|---|---|---|
| **Korrelation der Tagesrenditen EUR/USD** | **0,149** | **0,992** |
| Verhaeltnis sd(EUR)/sd(USD) | 1,06 | ~0,95 |
| wiederholte Schlusskurse EUR | 15,6 % | 0,0 % |
| Handelsvolumen-Anteil EUR | 3,5 % (Rang 2 von unten) | 15,8 % |

**Die EUR-Seite ist die kaputte** - kein anderes Symbol liegt unter 0,78
Korrelation.

**URSACHE IST ILLIQUIDITAET, NICHT VERALTUNG - und die beiden sind
unterscheidbar.** Waere die Reihe nur veraltet, muesste sie sich WENIGER
bewegen (fortgeschriebene Werte). Sie bewegt sich aber **genauso stark**
(sd-Verhaeltnis 1,06), nur in andere Richtungen. Das ist die Signatur eines
illiquiden Paars: bei einem Micro-Cap zu 1,4e-06 mit 3,4 % Tagesvolatilitaet -
der hoechsten im ganzen Feld - ist der EUR-Schlusskurs ein zufaelliger letzter
Trade und kein Marktpreis.

**Volatilitaet allein erklaert es nicht:** BIO hat mit 3,19 % fast dieselbe
Tagesvolatilitaet, aber nur 0,32 % FX-Abweichung. Es braucht die Kombination
aus duennem EUR-Volumen, extremem Micro-Cap-Kursniveau und hoher Volatilitaet.

**PRAKTISCHER SCHADEN AKTUELL: KEINER.** CAT wird nicht gehalten (Menge 0,0),
steht nicht im Mengen-Korb der Z-3-Reihe, und alle Simulationen dieses Projekts
rechnen ohnehin **in USD** ("wie im Produktivcode"). Der Schaden beschraenkte
sich auf die FX-Ableitung - und die ist durch den Wechsel auf den
Interquartilsabstand bereits robust dagegen.

**KEINE weitere Aenderung gebaut, bewusst.** Eine Denylist waere eine zweite
Loesung fuer ein Problem, das der IQR schon loest - genau die Dublette, die der
Regler-Audit am 03.08. als Fehlerquelle entfernt hat. Der sauberere Weg waere,
fuer Symbole mit duennem EUR-Volumen den EUR-Wert aus USD x Konsens-FX
abzuleiten statt dem Schlusskurs zu trauen. Das betrifft aber die
Kursbehandlung insgesamt und gehoert nicht nebenbei entschieden.

> **REVISIT-BEDINGUNG:** sobald CAT (oder ein anderes Symbol mit
> EUR-Volumenanteil unter 5 %) tatsaechlich gehalten wird - dann geht die
> fehlerhafte EUR-Reihe direkt in die Portfoliobewertung und damit in Z-3.

**Werkzeug:** `pruefe_fx_ableitung.py` rechnet die Quotienten je Symbol und Tag
nach, rankt die Ausreisser und erklaert die Unterscheidung Veraltung gegen
Illiquiditaet.


---

## Nachtrag (2026-08-06): Rekonstruktion der fehlenden Kursreihen - und der Scheinwert von 51.000 EUR, den erst der FX-Fix gefaehrlich gemacht haette

**AUFTRAG:** Rekonstruktion fuer Rohstoffe und 3QSS bauen (Phase A des
Nicht-Krypto-Umbauplans), danach Zwischenbilanz fuer die uebrigen Klassen.

### Was gebaut wurde

`agent/rekonstruktion.py` - EIN Verfahren fuer beide Faelle: eine Referenzreihe
liefert die Form, ein Ankerpreis die Hoehe.

    ETC (ungehebelt):  wert[t] = anker x (referenz[t] / referenz[anker_tag])
    Hebelprodukt:      taegliche Rendite = -faktor x Referenzrendite, VERKETTET

**Die Verkettung ist nicht optional.** Ein taeglich zuruecksetzendes Produkt
bildet das Faktor-fache der TAGESrendite ab, nicht der Gesamtrendite - der
Unterschied ist der Volatilitaets-Drag. Am konstruierten Fall gemessen: Index
-1,99 %, naive Hochrechnung **+5,97 %**, Verkettung **-17,19 %**. An echten
^NDX-Daten: Index +0,48 % ueber 30 Handelstage, 3QSS -5,69 %, naiv waere -1,44 %.

**Fenster auf 520 Handelstage begrenzt.** ^NDX reicht bis 1985 zurueck; ohne
Grenze haette die 3QSS-Reihe dort bei **4,7e+14 EUR** begonnen. Die Grenze ist
kein Sparzwang - die nicht modellierte Drift (Roll, Gebuehren, FX) akkumuliert
mit jedem Tag rueckwaerts, und die Reihen taugen ohnehin nur fuer kurze
Horizonte.

**Verdrahtung:**
- Rohstoffe: Futures unter `_ROHSTOFF_FUTURES_<SYM>`, rekonstruierter ETC unter
  dem echten Symbol. Die technische Analyse liest weiterhin den **Future** -
  die rekonstruierte Reihe traegt Drift und ist fuer Indikatoren die
  schlechtere Grundlage. Rueckfall auf die ETC-Reihe nur, wenn die Futures-Reihe
  fehlt, und dann mit Warnung.
- Hedge: 3QSS aus `^NDX` (3x invers), DBPK aus `^GSPC` (2x invers), verankert am
  aktuellen `fast_info`-Preis. **Die dokumentierte Entscheidung gegen
  Einzeltitel-Technikanalyse fuer Hedges bleibt unberuehrt** - die Reihe dient
  ausschliesslich der Bewertung.
- `quelle`-Spalte in `price_history_ohlc` (additiv, idempotent, Standard
  `gemessen`), damit eine rekonstruierte Reihe nie wie eine gemessene aussieht.

### Der Fund, der beim Verifizieren auffiel

**OD7H trug 4.215,90 USD statt 18,22 EUR** - das ist der Gold-Future je
Feinunze, abgelegt unter dem ETC-Symbol.

| Symbol | laut Reihe | echt | Differenz |
|---|---:|---:|---:|
| OD7H | 51.059 EUR | 255 EUR | **-50.803** |
| OD7N | 670 | 551 | -120 |
| OD7C | 30 | 156 | +126 |
| OD7L | 100 | 169 | +69 |
| 3QSS | 0 | 315 | +315 |
| DBPK | 0 | 230 | +230 |
| **Summe** | **51.859** | **1.676** | **-50.182** |

Gemeldeter Portfoliowert am 06.08.: **6.180 EUR**.

### WARUM DAS BISHER FOLGENLOS BLIEB - und warum genau das das Problem ist

Der Scheinwert lief **nicht** in die Bewertung ein, weil ein ZWEITER Defekt ihn
abfing: die FX-Ableitung wurde an praktisch jedem Tag verworfen, und ohne
Wechselkurs faellt jedes USD-Symbol aus der Bewertung. Am Export nachgerechnet:

| Streuungsmass | angenommene Tage |
|---|---|
| Spannweite max-min (alt) | **4 von 91** |
| Interquartilsabstand (neu) | **91 von 91** |
| Spannweite ohne CAT | 18 von 91 |

Die letzte Zeile **korrigiert den Vorbefund von heute frueh**: CAT war der
schlimmste Ausreisser, aber nicht die Ursache - das Streuungsmass selbst war es.

**Daraus folgt die zentrale Erkenntnis:** der FX-Fix ALLEIN waere schaedlich
gewesen. Er holt die USD-Symbole zurueck in die Bewertung - und damit 51.000 EUR
Scheinvermoegen in ein Portfolio von 6.180 EUR. Z-3, jede Allokationsquote und
jede Prozentregel waeren unbrauchbar geworden, und zwar mit plausibel
aussehenden Zahlen.

> **UEBERGREIFENDE LEHRE:** zwei Defekte, die sich gegenseitig verdecken, sehen
> im Betrieb wie EIN Defekt aus. Wer einen davon behebt, verschlimmert die Lage.
> Vor jedem Einzelfix gehoert deshalb die Frage: *was hat diesen Fehler bisher
> unsichtbar gehalten, und was passiert, wenn ich dieses Etwas entferne?*

### Zwei Sicherungen, die daraufhin dazukamen

**1. Datenmigration beim Start** (`database/db.py::
_migrate_rohstoff_futures_reihen_umziehen()`). Haengt die falsch abgelegten
Zeilen auf `_ROHSTOFF_FUTURES_<SYM>` um - kein Datenverlust, dort sind sie genau
das, was sie immer waren. **Beim Start und nicht erst beim naechsten
Pipeline-Lauf**, weil sonst die Reihenfolge der Cron-Jobs darueber entscheidet,
ob der Portfolio-Job den Scheinwert sieht. Idempotent: laeuft nur, solange das
Zielsymbol leer ist.

**2. Plausibilitaetsfilter in der Bewertung** (`agent/portfolio_historie.py::
_verwerfe_unplausible_reihen()`). Vergleicht den juengsten Reihenwert mit dem
aktuellen Snapshot-Preis derselben Waehrung; Faktor > 3 bedeutet "zwei
verschiedene Instrumente". Das Symbol wird dann KOMPLETT aus der Bewertung
genommen und faellt in "Symbole ohne Kurs" - sichtbar statt still falsch.

**Zwei bewusste Einschraenkungen des Filters:**
- Ohne Snapshot-Preis wird nicht verworfen. Fehlende Gegenprobe ist kein Beleg.
- Eine Reihe, deren juengster Punkt aelter als 5 Tage ist, wird nicht geprueft.
  Eine grosse Bewegung ueber eine Datenluecke ist eine Kursbewegung, kein
  Etikettenfehler - bei kleinen Coins ist Faktor 3 in zwei Wochen normal.

**Verworfen: eine Denylist fuer betroffene Symbole.** Waere eine zweite Loesung
fuer ein Problem, das die Migration schon loest - genau die Dublette, die der
Regler-Audit am 03.08. als Fehlerquelle entfernt hat.

### Testung

30 Pruefungen, alle bestanden, ausschliesslich gegen temporaere Datenbanken:
Verdrahtung beider Pipelines (12), Migration und Filter (14 inkl. Grenzfaelle
Faktor 2,99/3,01 und Veraltung), Robustheit (3), plus ein Regressionslauf gegen
eine Kopie der lokalen DB (85.280 OHLC-Zeilen vorher wie nachher, FX-Tage
verworfen: 0).

### Was daraus fuer die anderen Klassen folgt

**Aktien und Themen-ETF hatten nie einen Datendefekt** - sie fielen ueber
DENSELBEN FX-Bruch aus der Bewertung wie die Rohstoffe. Ihre Bewertung ist
heute mitrepariert, ohne dass an ihnen etwas geaendert wurde. Wer nur fragt
"welche Klasse war kaputt", verpasst das.

**Hedge braucht zusaetzlich eine eigene Erfolgsdefinition** (D-d): ein Hedge,
der Geld verliert waehrend das Portfolio steigt, hat funktioniert. Solange
Hedge-Signale nach derselben Systemguete gemessen werden wie Long-Signale, ist
das Ergebnis garantiert negativ und garantiert bedeutungslos. Das gehoert VOR
die erste Hedge-Auswertung.

**Erwartete Werte nach dem Pull** (vorab falsifizierbar): Portfoliowert +~1.700
EUR, "Symbole ohne Kurs" von 19 auf <= 4, Z-3-Rueckschlag **sinkt**,
Rohstoff-Systemguete verliert den +20,5-R-Ausreisser und hat damit **null**
ausgewertete Trades statt einer erfundenen Kante.

**Werkzeuge:** `agent/rekonstruktion.py` (Verfahren + `ankertag_abweichung()`
als Pflicht-Pruefgroesse). Details und offene Punkte: `Basisinfos/
Plan_Nicht_Krypto_Umbau_06_08.md`, Abschnitt "Zwischenbilanz".


---

## Nachtrag (2026-08-06): drei Luecken, die vor dem Push auffielen - Refresh, Export, Uebersichtsseite

Nach dem Bau der Rekonstruktion die Frage gestellt, was ausser Code noch
nachzuziehen ist. Drei Antworten, alle drei sind echte Luecken gewesen.

### 1. Die Kursreihen der Nicht-Krypto-Klassen wurden gar nicht taeglich gezogen

`api/yfinance_history.py::backfill_all_aktien_ohlc()` filtert auf
`assetklasse == "aktien"`. Fuer **Rohstoffe, Themen-ETF und Hedge** entstand eine
Reihe nur, wenn die jeweilige PIPELINE lief - und die laeuft im
Multi-Asset-Batch **um 9 und 19 Uhr, Mo-Fr**. Der Portfolio-Wert-Job laeuft
**taeglich um 6:30**. Die Bewertung dieser Positionen hing also daran, ob am
Vortag ein Signal erzeugt wurde; am Wochenende gar nicht.

Mit der Rekonstruktion wiegt das schwerer als vorher: die rekonstruierte Reihe
haengt an einem Ankerpreis, der sich taeglich bewegt - ohne eigenen Refresh
waere sie am Montagmorgen drei Tage alt verankert.

**Gebaut:** `scheduler/background.py::_refresh_nicht_aktien_ohlc()`, aufgerufen
im bestehenden taeglichen OHLC-Refresh-Job. Ruft bewusst die PIPELINE-eigene
Funktion je Klasse auf statt einer Kopie - Staleness-Wache, Symboltrennung und
Rekonstruktion sind dort schon richtig entschieden. Fail-soft je Asset.

### 2. Der Export konnte die Behebung nicht belegen

`z3_status` liefert nur das Ergebnis. Daneben stand "19 Symbole ohne Kurs" - und
aus dem Export war **nicht rekonstruierbar, welche 19 und warum**. Damit waere
die Verifikation nach dem Pull unmoeglich gewesen.

**Ergaenzt in `extract_notebook_diagnose.py`:**
- `ohlc_aktualitaet_je_symbol` traegt jetzt **Waehrung und `quelle`** je Reihe,
  plus eine eigene Liste `rekonstruierte_reihen`. Ohne die Waehrung war nicht
  sichtbar, dass die Nicht-Krypto-Symbole nur EINE Seite fuehren (OD7C/PLTR nur
  USD, X136/CEBS nur EUR) - genau der Grund, warum sie bei kaputter
  FX-Ableitung geschlossen aus der Bewertung fielen.
- neue Sektion `bewertungs_diagnose`: je gehaltenem Symbol Tage direkt in EUR /
  ueber FX / ohne Kurs, dazu `fx_tage_verworfen` und `reihen_verworfen`.

### 3. Z-3 stand nicht auf der Uebersichtsseite - und die Gegenprobe fehlte

Die Notbremse loeste am 05. und 06.08. aus. Sichtbar war das nur per E-Mail und
im Log; die Remote-Uebersichtsseite zeigte den Drawdown **gar nicht**.

**Der wichtigere Teil ist die Gegenprobe.** Die Seite rechnet den Portfoliowert
aus den **Snapshot-Preisen** (`price_cache`), Z-3 aus der **Kursreihe**
(`price_history_ohlc`). Beide beschreiben dasselbe Portfolio. Am 06.08. lagen
sie um ueber 100 % auseinander - und niemand sah es, weil die beiden Zahlen nie
nebeneinander standen. Ab jetzt stehen sie es, mit Abweichung in Prozent und
Warnfarbe ab 5 %.

> **Das ist die billigste Dauerueberwachung, die aus dem Fund folgt.** Zwei
> unabhaengige Wege zur selben Groesse, nebeneinander gestellt. Kein neuer
> Datenbezug, keine Schwellenwert-Diskussion - nur die Weigerung, zwei Zahlen
> getrennt anzuzeigen, die dasselbe meinen.

**Geprueft:** Z-3-Block gegen eine DB-Kopie mit eingesetzter Wertreihe -
Abweichung 21,6 % korrekt berechnet und als Warnung markiert, Karte im
`to_dict()` enthalten, Renderer nutzt die vorhandene `.err`-Klasse statt einer
eigenen Farbe.


---

## Nachtrag (2026-08-06): Audit der Remote-Uebersichtsseite - beschreiben die Karten noch das laufende System?

**Nutzer-Frage:** "sind die Beschreibungen und die Nutzung der Kapitel noch
aktuell, z. B. Veto und Schattenmessungen - hier haben wir jetzt ein anderes
Konzept im Einsatz". Berechtigt: alle 17 Karten durchgegangen, vier Befunde.

### 1. Die Richtungsverteilung wurde AUSGELIEFERT, aber nie angezeigt

`richtungsverteilung` steckt seit dem Nur-Long-Umbau in `to_dict()` und damit in
jeder `/api/status`-Antwort - es gab nur **keine Karte dafuer**. Das aktuellste
Konzept des Systems war das einzige, das man auf der Seite nicht sehen konnte.
Karte nachgezogen, inklusive der `belastbar`-Regel: unter 30 aufgeloesten
Faellen wird **keine Trefferquote** gezeigt, sondern der Fallstand. Eine
Prozentzahl aus drei Faellen sieht aus wie eine aus dreihundert.

### 2. Die Regime-Karte beschrieb ein Verfahren, das so nicht mehr laeuft

Sie zeigte nur das harte Label ("baer"/"bulle") - waehrend die Mindestkonfidenz
seit der Glaettung vom selben Tag am **stetigen Score** haengt. Genau die
vermutete Luecke.

Die drei Werte (`score_stetig`, `min_konfidenz_stetig_wert`,
`btc_abstand_ema50_prozent`) waren berechnet, aber nirgends gespeichert.
**Persistiert an der Stelle, die 2026-07-17 genau dafuer angelegt wurde** -
dieselbe reine Persistierungs-Erweiterung, kein neuer Netzwerk-Call, kein
Live-Recompute (die Karte bleibt passiver Lesezugriff). Drei additive Spalten
ueber die vorhandene generische macro_snapshot-Migration.

### 3. `nur_long_historisch` beschreibt ein Veto, das es nicht mehr gibt

Der Grund steht mit 90 aufgeloesten Faellen in der Veto-Schatten-Aufschluesselung
- ein Veto, das seit dem 05.08. **nicht mehr feuert**. Die Faelle bleiben als
Historie stehen (sie sind echt), aber die Karte sagt jetzt dazu, dass keine
neuen hinzukommen und eine Quote daraus die Vergangenheit beschreibt.

**Bewusst NICHT ausgeblendet.** Eine verschwundene Karte wirft die Frage auf,
ob die Messung je stattgefunden hat. Ein gekennzeichneter Historienblock
beantwortet sie.

### 4. Die MFE-Karte trug die eigene Einschraenkung nicht

"Richtungstreffer-Quote (Mindestziel/MFE)" beschrieb ausfuehrlich, was sie
misst - aber nicht, dass **MFE bei variablem Stop-Abstand kein Erfolgsmass ist**
(am 06.08. hergeleitet: sie belohnt enge Stops, und die liefern gemessen
-1,04 R). Einordnung ergaenzt, mit Verweis auf die Systemguete als zustaendige
Karte fuer die Qualitaetsfrage.

### Was NICHT geaendert wurde, und warum

| Karte | Warum sie bleibt wie sie ist |
|---|---|
| Veto-Schatten (nach Provider) | Aktiv und gefuettert (527 aufgeloeste Faelle), Konzept unveraendert |
| Z.ai-Richtung (unabh. Mistral), n=12 | Hat die Kleine-Stichproben-Warnung bereits seit dem 31.07. |
| Entfernte Provider (Groq/Cerebras) | `_ohne_entfernte_provider()` filtert sie auf der Seite bereits; im Export bleiben sie bewusst stehen, weil die Historie echt ist |
| Selbst-gewaehltes HALTEN | Aktiv (25 Faelle), unabhaengig vom Nur-Long-Umbau |

> **Muster, das dieses Audit sichtbar macht:** eine Anzeige veraltet nicht, wenn
> das Konzept sich aendert - sie veraltet **still**. Der Code lief weiter
> korrekt, die Karte beschrieb weiter das alte Verfahren, und beides sah
> unauffaellig aus. Nach jeder Konzeptaenderung gehoert deshalb die Frage dazu:
> *welche Anzeige behauptet jetzt etwas, das nicht mehr stimmt?*


---

## Nachtrag (2026-08-06): `.get()` auf sqlite3.Row - ein Einzeiler, der drei Produktivpfade seit 09:17 abgeschaltet hat

**Gefunden vom Nutzer im Betriebslog**, nicht von mir und nicht von einem Test.

### Der Fehler

Die Plausibilitaetsschranke gegen den Instrumenten-Verwechsler (Commit
185d4f3, 09:17) schrieb:

```python
erster = next((p["close"] for p in tage if p.get("close")), None)
```

`lade_kursreihen()` liefert **sqlite3.Row**, und Row kennt **kein `.get()`**.
Jeder Aufruf von `simuliere_signal()` warf ab 09:17 einen `AttributeError`.

Doppelt falsch: die Spalte `close` ist in der DB `NOT NULL` - der Fall, gegen
den `.get()` absichern sollte, kann ueber diesen Pfad gar nicht auftreten.

### Was dadurch ausfiel

| Pfad | Wirkung |
|---|---|
| `compute_systemguete()` (mark-to-market) | Systemguete-Karte der Remote-Seite ohne Neuberechnung, Fehler alle paar Sekunden im Log |
| `basislinie_ziel_anteil()` | Basislinien-Vergleich ohne Ergebnis |
| `compute_crv_breakeven_baender()` | **und damit `crv_baender_kontext_fuer_prompt()`** |

Die dritte Zeile ist die unangenehmste: der **CRV-Baender-Fakt**, am selben Tag
in alle sechs Pipelines eingebaut und als Regel 32/36 dokumentiert, **hat das
LLM seit 09:17 nie erreicht**. Der Kontext-Bauer faengt die Exception ab und
gibt `None` zurueck - der Fakt fehlt dann einfach im Prompt.

### WARUM ES NIEMAND GEMERKT HAT - das ist der eigentliche Befund

**Fail-soft hat den Defekt versteckt.** `_safe()` auf der Remote-Seite,
try/except im Export, try/except im Kontext-Bauer: jede Schicht hat brav
weitergemacht. Die Anwendung lief, die Seite lud, Signale entstanden - nur drei
Kennzahlen und ein Fakt waren still weg.

Fail-soft ist richtig; ein Nebenblock darf die Anwendung nicht toeten. Aber
**fail-soft ohne sichtbare Meldung ist fail-silent**. Der einzige Ort, an dem
der Ausfall stand, war das Log.

> **KONSEQUENZ FUER DIE ARBEITSWEISE:** nach einem Deploy reicht "die Anwendung
> laeuft" als Abnahme nicht. Ein Blick ins Log auf `ERROR`-Zeilen gehoert dazu -
> genau das hat der Nutzer getan und damit den Fehler gefunden, den meine
> Testsuite nicht gefunden hat.

### Warum meine Tests ihn nicht gefunden haben

Die Testsuite vom selben Tag baute Zeilen als **dicts** nach, statt sie durch
`lade_kursreihen()` zu laden. Mit dicts funktioniert `.get()` einwandfrei. Der
Test hat also eine Welt geprueft, die es in der Produktion nicht gibt.

**Neu: `teste_simuliere_signal_zeilentypen.py`** laedt die Reihen ueber
`lade_kursreihen()` gegen eine echte SQLite-Verbindung - dieselbe Ladeform wie
die Produktion - und prueft beide Zugriffsformen (Row und dict) auf identische
Ergebnisse, dazu die Schranke selbst (Faktor 5,5 faellt, Faktor 2,5 bleibt) und
`basislinie_ziel_anteil()` als zweiten Pfad.

> **REGEL, die daraus folgt:** ein Test, der die Datenstruktur der Produktion
> nachbaut statt sie zu LADEN, prueft die eigene Annahme mit. Wo eine Funktion
> DB-Zeilen entgegennimmt, muss der Test sie aus der DB holen.

### Fix

```python
erster = next((p["close"] for p in tage if p["close"] is not None), None)
```

Indexzugriff funktioniert bei Row und dict gleichermassen - genau wie in der
Schleife direkt darunter, die schon immer `p["high"]`/`p["low"]` benutzt hat.
Der Fehler war, in derselben Funktion zwei verschiedene Zugriffsformen zu
mischen.


---

## Nachtrag (2026-08-06): zwei weitere Fehler DERSELBEN Runde - und die Pruefung, die die ganze Klasse auf einmal abraeumt

Nutzer-Vorgabe beim zweiten Betriebsfund: **"vor einem Fix sauber analysieren
und recherchieren, damit wir keinen Dominoeffekt haben."** Genau richtig - ich
haette sonst den dritten Fehler einzeln behoben und auf den vierten gewartet.

### Fehler 3: `build_hebel_facts()` kannte `crv_baender` nicht

`hebel_pipeline.py` uebergab `crv_baender=fakt_crv_baender`, der Funktionsrumpf
benutzte `crv_baender` bereits - **nur der Parameter fehlte in der Signatur**.
Jeder Hebel-LLM-Call brach mit `TypeError` ab, seit Commit 486c1c0 (07:12).

Die fuenf anderen Analysten (Krypto-Spot, Aktien, Rohstoffe, Themen-ETF) hatten
den Parameter von Anfang an. **Genau einer von sechs wurde uebersehen** - und
weil der Rumpf ihn schon benutzte, sah der Code beim Lesen vollstaendig aus.

### Fehler 4: der neue OHLC-Refresh filterte auf Assetklassen, die es nicht gibt

Im Log stand `Nicht-Aktien-OHLC-Refresh: 4 Assets aktualisiert (0
fehlgeschlagen)` - unauffaellig, erwartet waren **11**.

Die Watchlist kennt nur `aktien`, `rohstoffe`, `krypto` und `etf`. Es gibt
**keine** Assetklasse `hedge` und **keine** `themen_etf`: Hedge-Instrumente
werden ueber die Mitgliedschaft in `SYMBOL_ZU_HEBEL_FAKTOR` erkannt,
Themen-ETFs sind die uebrigen `etf`. Mein Filter fragte nach Klassennamen, die
nicht existieren, und erwischte deshalb nur die vier Rohstoffe.

**Folge: die 3QSS-Rekonstruktion lief nie** - der Teil des Tages, um den es
ueberhaupt ging.

**Fix ohne zweite Regelfassung:** die Auswahl kommt jetzt aus
`agent/multi_asset_batch.py::_kandidaten()`, der bereits vorhandenen Regel.
Eine eigene Fassung waere die Dublette gewesen, die am 03.08. schon einmal
auseinandergelaufen ist. Zusaetzlich loggt der Job die **Aufschluesselung je
Art** statt nur einer Summe - "4 Assets" sah unauffaellig aus, obwohl zwei
Arten komplett fehlten. Nachher: `11 Assets aktualisiert (0 fehlgeschlagen) -
hedge: 2, rohstoffe: 4, themen_etf: 5`.

### Die Pruefung, die die Klasse abraeumt: `pruefe_aufruf_signaturen.py`

Statt Fehler 3 einzeln zu beheben, wurde die ganze Fehlerklasse geprueft: ein
AST-Durchlauf ueber **181 Dateien und 1.270 Funktionsnamen**, der jeden Aufruf
gegen die Signatur der Zielfunktion haelt.

**Ergebnis nach dem Fix: kein einziger weiterer Fall.** Kein Dominoeffekt - die
`crv_baender`-Luecke war die einzige ihrer Art. Das ist der Unterschied zwischen
"behoben" und "belegt behoben".

Die drei verbleibenden Meldungen sind Namenskollisionen mit `subprocess.run()`
und `app.run()` und bewusst als "zu pruefen" statt als Fehler ausgewiesen -
eine Pruefung, die Rauschen erzeugt, wird nicht mehr gelesen.

### Was diese Runde insgesamt zeigt

Vier Fehler an einem Tag, **alle vier fail-silent**, alle vier vom Nutzer im
Betriebslog gefunden:

| # | Fehler | seit | versteckt durch |
|---|---|---|---|
| 1 | Scheinwert 51.000 EUR unter OD7H | laenger | kaputte FX-Ableitung |
| 2 | `.get()` auf `sqlite3.Row` | 09:17 | `_safe()`, try/except |
| 3 | `build_hebel_facts()` ohne `crv_baender` | 07:12 | try/except im LLM-Call |
| 4 | Refresh-Filter auf Phantom-Assetklassen | 13:32 | Summe statt Aufschluesselung |

> **Das gemeinsame Muster ist nicht Unachtsamkeit, sondern die
> Rueckmeldeschleife.** Jeder dieser Fehler haette sich sofort selbst gemeldet,
> wenn irgendetwas laut geworden waere. Keiner hat es. Deshalb sind die
> Gegenmassnahmen dieser Runde alle vom selben Typ: Aufschluesselung statt
> Summe, Gegenprobe statt Einzelwert, statische Pruefung statt Vertrauen -
> und ein Blick ins Log als Teil der Abnahme, nicht danach.


---

## Nachtrag (2026-08-06): erste echte Verifikation am Export - zwei Erwartungen erfuellt, zwei NICHT

Der Export von 13:57 ist der erste mit dem neuen Stand. Gegen die am Vormittag
schriftlich festgelegten Erwartungen geprueft - genau dafuer standen sie da.

| Erwartung | Ergebnis | |
|---|---|---|
| FX-Ableitung repariert | **0 verworfene Tage** (vorher 87 von 91) | erfuellt |
| 3QSS bewertbar | 520 rekonstruierte Punkte, Ankerabweichung 0 | erfuellt |
| "Symbole ohne Kurs" <= 4 | **11** | NICHT erfuellt |
| Rohstoff-Systemguete ohne +20,5-R-Ausreisser | **20,51 R steht weiter drin** | NICHT erfuellt |

Portfoliowert 6.180 -> **7.150,24 EUR**. Z-3 unveraendert bei 16,84 % - das
Fenster reicht 90 Tage zurueck, ein einzelner Tag verschiebt es kaum.

### Warum "11 statt <= 4": die ETC-Rekonstruktion lief NIE

Von den 11 sind **7 harmlos**: Aktien und ETFs handeln nicht am Wochenende,
Krypto schon. 64 + 27 = 91 Tage - das ist der Kalender, kein Defekt.

**Die vier OD7*-ETCs dagegen haben 91 von 91 Tagen ohne Kurs.** Ursache:
`_ensure_ohlc_backfilled()` fragte die Frische der FUTURES-Reihe und sprang bei
frischem Stand sofort heraus - und uebersprang damit die Rekonstruktion gleich
mit.

**Zwei Groessen, zwei Frische-Begriffe** - sie an denselben Guard zu haengen war
der Fehler:

    Futures : veraltet, wenn der letzte Handelstag zu lange her ist
    ETC     : haengt an einem ANKERPREIS, der sich JEDEN Tag bewegt

Auf dem Entwicklungsstand fiel es nicht auf, weil die Futures-Reihe dort
veraltet war und der Abruf ohnehin lief. Im Betrieb war sie frisch. **Der Test
hat den guenstigen Fall geprueft.** Neuer Regressionsfall A9b prueft jetzt
genau den unguenstigen: frische Futures-Reihe, Rekonstruktion muss trotzdem
laufen, und zwar ohne neuen Netzabruf.

Dieselbe Falle hatte ich beim Hedge erkannt und behandelt (rekonstruierte Reihe
faellt nicht unter die Staleness-Wache) - bei den Rohstoffen nicht. Ein Muster
an einer Stelle zu sehen und an der baugleichen zweiten zu uebersehen.

### Warum der +20,5-R-Ausreisser noch da ist

**Die Schranke verhindert NEUE Fehlbewertungen, sie korrigiert keine alten.**
Der Wert steht als ERGEBNIS in der DB (Signal #137, OD7C vom 03.08.,
`take_profit_erreicht`, R=20,51) und geht weiter in jede Systemguete ein. Die
Systemguete liest gespeicherte Ergebnisse, sie simuliert nicht neu.

Das war ein Denkfehler in meiner eigenen Erwartung: ich hatte "der Ausreisser
verschwindet" angekuendigt, ohne zu pruefen, woher die Kennzahl ihre Werte
nimmt.

**`korrigiere_rohstoff_outcome.py`** setzt betroffene Signale auf `offen`
zurueck - Standard ist TROCKENLAUF, Anwenden nur mit `--anwenden`. Es erfindet
kein Ergebnis: der naechste Backward-Tracking-Lauf bewertet neu, dann gegen die
rekonstruierte Reihe auf der richtigen Skala. Kommt nichts zustande, bleibt es
offen - der ehrliche Zustand.

Bewusst KEIN automatischer Teil der Migration: eine Migration, die stillschweigend
Messergebnisse aendert, ist genau die Sorte Automatik, die man spaeter nicht mehr
nachvollziehen kann. Abgegrenzt ueber einen Stichtag; ein nach der Symboltrennung
entschiedenes Signal bleibt unangetastet (im Test gegengeprueft), zweiter Lauf
ist ein No-op.

> **Was diese Verifikationsrunde methodisch zeigt:** die vier Erwartungen VORHER
> aufzuschreiben war das Wertvollste an der ganzen Runde. Zwei davon waren
> falsch - und beide Irrtuemer waeren ohne die schriftliche Vorfestlegung als
> "sieht doch gut aus" durchgegangen. Ein Ergebnis, das man erst nach dem
> Messen formuliert, kann nicht widerlegt werden.


---

## Nachtrag (2026-08-06, Export 14:20): der Ausreisser war nicht weg, er war umgezogen

Zweiter Export nach den Fixes. Vier von fuenf Erwartungen erfuellt - und ein
Fehler in meiner eigenen Korrektur.

| | Ergebnis |
|---|---|
| ETC-Reihen rekonstruiert | **alle vier** (520/520/131/520 Punkte bis 06.08.) |
| CRV-Baender-Fakt im Prompt | **12 Faktensaetze am 06.08.**, vollstaendiger Block |
| +20,51 R im realen Arm | **weg** (Systemguete real: n=0) |
| FX-Ableitung | weiterhin **0 verworfene Tage** |
| Portfoliowert | 6.180 -> 7.150 -> **7.698 EUR** |

### Der Fehler: eine Korrektur, die den Fehler verschiebt statt ihn zu beheben

Nach dem Lauf stand in der Rohstoff-Systemguete **Schattenarm: -18,81 R**.
Dasselbe Instrumenten-Missverstaendnis, nur mit umgekehrtem Vorzeichen und in
einem anderen Messarm: `veto_outcome_realisiertes_crv` von OD7C (30.07.).

Mein Korrekturskript setzte **nur `outcome_*`** zurueck. Jedes Signal wird aber
in bis zu **drei** Armen bewertet:

    outcome_*                das echte Ergebnis
    veto_outcome_*           was waere ohne das Veto passiert?
    selbst_halten_outcome_*  was waere ohne das selbst gewaehlte HALTEN?

**Zweite Luecke derselben Korrektur:** die Bedingung verlangte ein gesetztes
`realisiertes_crv`. Ein Signal mit nur einem MFE (`*_max_realisiertes_crv`) und
Status `offen` fiel durch - obwohl auch dieses MFE gegen die falsche Reihe
gerechnet wurde (OD7L, MFE 2,69).

Behoben: alle drei Arme, Bedingung auf `realisiertes_crv ODER
max_realisiertes_crv`, Zeitbezug jetzt `*_geprueft_am` (Zeitpunkt der BEWERTUNG,
nicht der Entscheidung - ein offenes Signal hat kein entschieden_am, sein MFE
ist trotzdem falsch). Gegengeprueft: ein nach dem Stichtag bewertetes Signal
bleibt unangetastet, zweiter Lauf ist ein No-op.

> **Das Muster wiederholt sich zum dritten Mal an einem Tag:** ein Begriff
> existiert MEHRFACH (sechs Hedge-Pruefungen, zwei Frische-Begriffe, drei
> Messarme), ich behandle eine Auspraegung und uebersehe die anderen. Die
> Gegenmassnahme ist jedes Mal dieselbe: **zuerst zaehlen, wie viele
> Auspraegungen es gibt**, dann handeln.

### Noch offen: drei ETC-Reihen sind da, werden aber nicht bewertet

OD7C/OD7H/OD7L stehen mit 91 von 91 Tagen ohne Kurs in der Diagnose, obwohl ihre
Reihen im selben Export vorhanden sind. **OD7N dagegen wird bewertet** (62 von
91 Tagen ueber FX - genau die Zahl der Handelstage).

Wahrscheinlichste Erklaerung: ein Wettlauf. Im Refresh-Log steht OD7N als
ERSTES, danach 3QSS, DBPK, OD7H, OD7C, OD7L - und genau OD7N ist der einzige,
der in der Bewertung ankommt. Der Export duerfte die Bewertungsdiagnose
berechnet haben, waehrend der Refresh noch lief. **Nicht bewiesen** - der
naechste Export entscheidet es. Steht dort weiterhin 91/91, ist es kein
Wettlauf, sondern ein Fehler.


---

## Nachtrag (2026-08-06): Info-E-Mails geprueft - Farbe hing an den Bildern, und eine Meldung stand fuer drei verschiedene Sachverhalte

Nutzer-Beobachtung: "es werden keine strukturierten Risikofaktoren mehr
uebermittelt" und "die farbliche Kennzeichnung ist nicht ueberall vorhanden".
Beides bestaetigt - mit unterschiedlicher Ursache.

### 1. Die Farbe hing an den Bildern - ein Unfall, keine Entscheidung

`api/email_notify.py::send_notification_email()` baute die HTML-Fassung **nur,
wenn `inline_images` gesetzt war**. Ohne Bild ging eine reine Textmail raus,
ganz ohne Hervorhebung. Zwei voellig unabhaengige Dinge - Bildanhang und
Textformatierung - hingen an derselben Bedingung.

Sichtbar wurde es an den **Hedge-Mails**: Hedge-Instrumente bekommen bewusst
keine technische Analyse, also nie eine Liquiditaetszonen- oder
Stabilitaets-Grafik, also nie ein Bild - **also nie Farbe**. Dieselbe
Mailstruktur sah je nach Assetklasse anders aus, ohne dass das je entschieden
worden waere.

Ab jetzt wird die HTML-Alternative **immer** gebaut, Bilder kommen zusaetzlich
dazu. Nebeneffekt, der dazugehoert: die `color-scheme`-Meta-Tags gegen Gmails
Dark-Mode-Invertierung gelten jetzt auch fuer Job-Ausfall- und Z-3-Mails, die
ihr bisher ungeschuetzt ausgesetzt waren.

### 2. Die Risikofaktoren fehlen nicht - die Meldung war irrefuehrend

An 276 Signalen seit dem 04.08. nachgemessen: **kein Datenverlust, keine
Regression.** Derselbe Satz "Keine strukturierten Risikofaktoren verfuegbar"
stand fuer drei verschiedene Sachverhalte:

| Fall | Anzahl | Bedeutung |
|---|---|---|
| HALTEN/VERKAUFEN | 239 von 276 | `compute_risikofaktoren()` steigt bei allem ausser KAUFEN/NACHKAUFEN frueh aus - die Liste ist als Pruefung einer KAUFIDEE gebaut |
| Hedge-Instrumente | 8 von 276 | `_post_check_hedge()` ruft `compute_risikofaktoren()` gar nicht auf - **echte, offene Luecke** |
| tatsaechlich fehlende Daten | Rest | der einzige Fall, fuer den der Satz gedacht war |

**"Verfuegbar" liest sich wie "die Daten fehlen".** Fall 1 heisst aber "alles in
Ordnung, nichts zu berichten", Fall 3 heisst "hier ist etwas kaputt". Ein Satz
fuer beide macht den einen unlesbar und den anderen unsichtbar - genau deshalb
kam die Beobachtung auf.

`ui/formatting.py::risikofaktoren_hinweis()` unterscheidet die drei Faelle und
wird an **allen fuenf** Stellen benutzt (drei Mailtypen, Signale-Tab,
Hebel-Tab) - nicht an jeder Stelle neu formuliert, siehe die Lehre vom selben
Tag zum Hedge-Praedikat.

### Offen: Risikofaktoren fuer Hedge-Instrumente

Die Faktorenliste prueft eine Long-Kaufidee (Regime-Konflikt LONG,
Retail-Long-Bias, Konfluenz). Fuer ein Absicherungs-Overlay sind die relevanten
Faktoren **andere** - dieselbe umgekehrte Wirkrichtung wie beim Erfolgsmass
(Punkt D-d). Bewusst nicht nebenbei erfunden; die Mail sagt jetzt ehrlich, dass
es sie noch nicht gibt.

### Gegenprobe der uebrigen Struktur

Alle drei Mailtypen auf zwoelf Bausteine verglichen (Abschnitte 1-3, Legende,
Gegenargument, Risiken, Halte-Kriterium, Forecast, Fazit, Z.ai, Mindestziel,
Positionsgroesse): **identisch**, bis auf die Positionsgroesse, die bei der
Hebel-Mail durch die Hebel-/Korrektur-Zeilen ersetzt ist. Kein weiterer
Konsistenzbruch gefunden.

**Werkzeug:** `teste_email_darstellung.py` - baut echte Mails mit und ohne Bild,
dekodiert den HTML-Teil und prueft Farbe, Meta-Tags und alle vier
Risikofaktoren-Faelle. 13 Pruefungen.


---

## Nachtrag (2026-08-07, Export 06:07): alle gestrigen Fehler sind weg - und der taegliche Portfolio-Job hat noch NIE einen brauchbaren Wert geschrieben

### Erst die Bestaetigung: die Fixes vom 06.08. wirken im Betrieb

| | vorher | Export 07.08. |
|---|---|---|
| ERROR-Zeilen | 1.069 am 06.08. um 12:xx | **0 am 07.08.** |
| `TypeError build_hebel_facts` | 255 Faelle 07:xx-13:xx | **0** |
| verworfene FX-Ableitungen | 586 (05.08.), 588 (06.08.) | **0** |
| CRV-Baender im Prompt | 0 | **29 von 29 Faktensaetzen** |
| `score_gesamt` im Prompt | - | **0** (korrekt entfernt) |
| Rohstoff-Schattenarm | -18,81 R | **-1,06 R** (ein normaler Stop) |
| Rohstoff realer Arm | +20,51 R | **n=0, offen=4** - ehrlich leer |
| OD7C/H/L bewertet | 91/91 Tage ohne Kurs | **60 Tage ueber FX**, Kurse 29,99 / 17,86 / 3,82 EUR |

Der vermutete Wettlauf zwischen Export und Refresh war es also - **nicht** ein
Fehler im Bewertungspfad. Die Vermutung ist damit bestaetigt, nicht nur
plausibel.

### Der neue Fund: der taegliche Job bewertet den falschen Tag

`schreibe_tageswert()` bewertete den **laufenden** Tag - und laeuft um 06:30.
Zu dieser Uhrzeit fehlen die meisten Tageskerzen noch. Ergebnis: **beide**
Zeilen, die der Job je geschrieben hat, sind unbrauchbar.

    2026-08-05   1.241,35 EUR   Abdeckung  3,0 %  ( 1 von 33 Symbolen)
    2026-08-06   6.180,00 EUR   Abdeckung 42,4 %  (14 von 33 Symbolen)

Zum Vergleich: die 88 nachtraeglich rekonstruierten Zeilen liegen durchgehend
bei **87-98 %**. Das ist kein Ausreisser, sondern die Bauweise.

Im Export vom 07.08. um 06:07 stand entsprechend **1.367,44 EUR bei 31 von 33
Symbolen ohne Kurs** - der naechste Lauf haette das als dritten Truemmerwert
festgeschrieben.

**Z-3 SELBST IST NICHT BETROFFEN.** `pruefe_z3()` rechnet auf `index_wert`, und
der Index ueberspringt Symbole, die an einem der beiden Tage keinen Kurs haben.
Deshalb steht Z-3 seit Tagen stabil bei 16,84 %, waehrend die EUR-Spalte
zwischen 1.241 und 7.698 sprang. Der Schaden ist `wert_eur` und alles, was
diese Spalte liest - unter anderem die **Gegenprobe auf der Uebersichtsseite**,
die ich am 06.08. gebaut habe. Sie haette hier korrekt Alarm geschlagen; das
war ihr Zweck.

**Nebenbefund:** der Modul-Docstring behauptete seit dem 04.08. das Gegenteil
("Z-3 rechnet auf `wert_eur`"). Falsche Doku an genau der Stelle, an der man
bei der Fehlersuche nachliest. Korrigiert.

### Zwei Korrekturen

1. **Bezugstag ist der VORTAG.** Ein Tagesschlusswert existiert erst nach
   Tagesende - das ist die Ursachenbehebung, nicht ein Schwellenwert.
2. **Abdeckungswache** (`MIN_ABDECKUNG_FUER_TAGESWERT = 0,80`) als Netz
   darunter: faellt die Abdeckung, wird **gar nichts** geschrieben. Lieber eine
   sichtbare Luecke als ein Wert, der wie ein Kurssturz aussieht - dasselbe
   Prinzip wie bei der FX-Ableitung.

`korrigiere_tageswerte.py` raeumt die beiden Altlasten weg (Trockenlauf als
Standard). `teste_tageswert_abdeckung.py` prueft beides, inklusive der beiden
echten Betriebsfaelle und der Schwelle bei genau 80 %.

### CoinGecko: eng, aber nicht rot

| | |
|---|---|
| verbraucht (01.-07.08.) | 2.067 von 10.000 = **20,7 %** |
| Schnitt je vollem Tag | 261 |
| Hochrechnung auf 31 Tage | **8.335 = 83 %** |

Die 80-%-Warnschwelle wird beim aktuellen Tempo **gegen Monatsende** gerissen,
das Limit selbst nicht. Kein Handlungsbedarf heute, aber die Warnmail kommt.

Der Haupttreiber ist der Preis-Refresh: 67 Laeufe/Tag (statt der moeglichen 96 -
die Luecke geht auf 24 App-Neustarts im Fenster zurueck). Der Rest verteilt sich
auf Historien-Nachladungen und den OHLC-Rueckfall fuer Coins ohne Kraken-Listing.
**Kein Ausreisser durch die Umbauten vom 06.08.** - die laufen ueber yfinance.

> **Wenn Entlastung noetig wird**, ist der erste Hebel das Refresh-Intervall
> (15 Min), nicht die Zahl der Coins: 96 moegliche Laeufe taeglich sind fuer ein
> System, das zweimal taeglich Signale erzeugt, reichlich. Bewusst noch NICHT
> geaendert - erst messen, ob die Preise zwischen den Laeufen ueberhaupt
> gebraucht werden.


---

## Nachtrag (2026-08-07): offene Punkte recherchiert und priorisiert - vier von sieben Dokumenteintraegen waren veraltet

Nutzer-Auftrag: alle offenen Themen recherchieren, gegenpruefen, Abhaengigkeiten
aufdecken, priorisieren. Ergebnis steht in `Zwischenstand_Gesamtprojekt_06_08.md`
**Abschnitt 8b** (der bestehende Abschnitt 8 bleibt darunter stehen - seine
Begruendungen sind der wertvollere Teil).

### Der Befund ueber die Dokumente selbst

Jeder Punkt wurde am Code und am Export nachgeprueft statt uebernommen. **Vier
von sieben Eintraegen aus Abschnitt 8 waren nicht mehr aktuell:**

| Punkt | Dokument | tatsaechlich |
|---|---|---|
| M1 Rohstoff-Ausreisser | offen | erledigt 06./07.08. |
| Q1 Z-3 nach FX-Fix | offen | erledigt; Z-3 rechnet auf `index_wert` und war nie beschaedigt |
| H2 Zieldauer *als Feld* | "blockiert halte_kriterium" | Feld existiert, ist befuellt (211/318) und wird exportiert - offen ist die AUSWERTUNG |
| 0.1 vier Export-Felder | "erledigt 04.08." | teilweise - zwei fehlen in beiden Signal-Exporten |

> **Ein Dokumentstand ist keine Messung.** Vor jeder Priorisierung gehoert die
> Pruefung am Code - sonst arbeitet man an Erledigtem und uebersieht das Offene.

### Der zentrale Blocker, und ein Fehlversuch dabei

`umgesetzt` ist bei **allen 2.742 Spot- und 1.703 Hebel-Signalen leer**. Damit
beschreibt jede Kennzahl - Systemguete, CRV-Baender, Basislinie, Erwartungswert
- **Empfehlungen, nicht Trades**.

Der erste Reflex war, die vier Spalten in `_HEBEL_SIGNAL_SPALTEN` aufzunehmen -
"ein Quick Win, eine Zeile". Der Test gegen eine DB-Kopie: **`no such column:
umgesetzt`**. Auf `hebel_signals` existieren die Spalten gar nicht; die
Umsetzungs-Rueckmeldung wurde am 09.07. ausschliesslich fuer Spot gebaut.

**Die Aenderung haette den gesamten Export zum Absturz gebracht** - und zwar
erst im Betrieb, nicht beim Schreiben. Zurueckgenommen und als Warnkommentar an
der Stelle hinterlassen, damit der naechste Anlauf nicht dieselbe Abkuerzung
nimmt.

Damit ist B1 keine Export-Luecke, sondern eine **fehlende Funktion** fuer die
Klasse mit der einzigen belastbaren Datenbasis: Migration + Schreibpfad + UI.

### Was daraus als Reihenfolge folgt

Zwei Ketten laufen parallel und behindern sich nicht - die Messkette (Export,
dann Befolgungsgrad) und die Hedge-Kette (Erfolgsmass, dann Risikofaktoren).
Eine dritte ist blockiert und bleibt es: Universum -> Screening -> Regime je
Klasse wartet auf eine Nutzer-Entscheidung, nicht auf Arbeit.

Vollstaendige Tabellen, Abhaengigkeitskette und Reihenfolge: Zwischenstand 8b.

### Doku-Disziplin: derselbe Fehler zum zweiten Mal

Die Priorisierung wurde zuerst als **neue Datei** `Offene_Punkte_Priorisiert_
07_08.md` angelegt - obwohl Abschnitt 8 des Zwischenstands genau diese Liste
fuehrt. Nutzer-Hinweis noch waehrend der Arbeit. Eingearbeitet als Abschnitt 8b,
neue Datei entfernt.

Derselbe Vorfall wie am 28.07. (zwei ueberfluessige Dateien). Die Memory-Regel
dazu hat nicht gereicht, weil sie nur drei Bestandsdateien kannte - inzwischen
sind es **14**. Sie enthaelt jetzt die vollstaendige Landkarte: welches Dokument
wofuer zustaendig ist, und welche fuenf **laufend fortzuschreiben** sind
(Entscheidungslog, Regelwerksmanual, Methodik, Fakten-Entscheidungsmappe,
Zielgroessen).


---

## Nachtrag (2026-08-07): W1 Hedge-Erfolgsmass - und warum "invertieren" der falsche Begriff war

Der Punkt hiess in meiner eigenen Priorisierung "Hedge-Erfolgsmass
**invertieren**". Beim Bauen stellte sich heraus: **das waere falsch gewesen.**

### Warum das Vorzeichen NICHT gedreht wird

Kauft man 3QSS bei 1,45 mit Stop 1,35 und Ziel 1,65 und der Nasdaq faellt,
steigt 3QSS auf 1,65 - der Trade gewinnt, und `R = +2` ist **richtig gerechnet**.
Das R-Multiple des einzelnen Hedge-Trades stimmt bereits.

Falsch ist etwas anderes: es zu einer **Guetekennzahl** zu aggregieren, die
"negativ = schlecht" bedeutet. Eine Absicherung ist eine
Versicherungspraemie - sie hat konstruktionsbedingt einen negativen
Erwartungswert, weil man sie fuer Varianzreduktion kauft und nicht fuer
Rendite. Nach Expectancy gemessen ist das Ergebnis garantiert negativ und sagt
genau nichts ueber ihre Guete.

> Der Fehler lag also nicht im Vorzeichen, sondern in der **Fragestellung**.
> Ein Trade-Mass auf ein Portfolio-Instrument angewandt.

### Was stattdessen gebaut wurde

**1. Hedge bekommt einen eigenen Tier.** Bis hierher landeten DBPK und 3QSS in
`etf` - zusammen mit den fuenf Themen-ETFs, weil sie dieselbe assetklasse
tragen. Ein Themen-ETF soll steigen, ein Hedge soll fallen wenn das Portfolio
steigt; in einem Topf heben sich zwei gegenlaeufige Logiken auf, und die
entstehende Zahl beschreibt nichts. **Noch war kein Schaden entstanden**
(`etf: real n=0`), aber der erste aufgeloeste Hedge-Trade haette ihn
angerichtet - lautlos, weil eine Mischzahl immer plausibel aussieht.

**2. `compute_hedge_wirksamkeit()`** - ein PORTFOLIO-Mass statt eines
Trade-Masses:

    Daempfung = Rueckschlag OHNE Hedge - Rueckschlag MIT Hedge

Derselbe Bestand zweimal mengenkonstant verkettet, einmal mit und einmal ohne
die Absicherungspositionen. Dazu die **Praemie**: der Renditeunterschied ueber
den Zeitraum, im steigenden Markt negativ. Beides zusammen ist die ehrliche
Bilanz einer Versicherung - was sie gekostet und was sie verhindert hat. Eine
der beiden Zahlen allein ist immer irrefuehrend.

**3. Messbarkeits-Wache.** Ohne sie liefert die Funktion still `0,0 Daempfung`,
wenn die Hedge-Kursreihe fehlt: `verketteter_index()` ueberspringt Symbole ohne
Kurs, beide Reihen werden identisch, und "0,0 Prozentpunkte" liest sich wie
"die Absicherung hat nichts gebracht" statt wie "nicht messbar". Genau das
fail-silent-Muster, das diese Woche schon dreimal zugeschlagen hat - hier vorab
abgefangen.

**4. Der Systemguete-Topf `hedge` bleibt stehen**, traegt aber
`nicht_als_guete_lesen=True` plus Verweis. Bewusst kein Unterdruecken: eine
fehlende Zahl wirft die Frage auf, ob ueberhaupt gemessen wurde - eine
gekennzeichnete nicht.

### Gegenpruefung, damit nichts bricht

Der Tier-Split wirkt auf **alle zwoelf Aggregationen**, die
`_assetklasse_index()` nutzen. Geprueft:

| | Ergebnis |
|---|---|
| alle 12 Aggregationen gegen eine DB-Kopie | laufen fehlerfrei |
| `spot_symbole_je_tier()` | `hedge` sauber getrennt, `etf` = nur die 5 Themen-ETFs |
| CRV-Baender fuer Themen-ETF (`tier="etf"`) | enthaelt jetzt **keine** Hedge-Trades mehr - eine Verbesserung, kein Bruch |
| Watchlist, Pipelines, Batch-Auswahl, UI-Filter | **unberuehrt** - die Aenderung sitzt im Mess-Index, nicht in der Watchlist |
| fest verdrahtete Tier-Listen der Anzeige (2 Stueck) | nachgezogen, sonst waere `hedge` stillschweigend aus der Darstellung gefallen |
| Signaturpruefung, 6 Testsuiten | gruen |

Der Test `teste_hedge_wirksamkeit.py` rechnet einen **konstruierten Fall mit
bekannter Antwort**: eine perfekt gegenlaeufige Absicherung nimmt einen
29,36-%-Einbruch vollstaendig heraus (Daempfung 29,36 pp), und im reinen
Aufwaertsmarkt kostet sie Rendite (Praemie negativ). Beide Vorzeichen stimmen.

### Was damit freigeschaltet ist

W2 (Hedge-Risikofaktoren) haengt an derselben Wurzel und ist jetzt baubar. Die
Hedge-Klasse ist damit **messbar** - ob sie etwas taugt, ist eine andere Frage
und braucht Zeit.


---

## Nachtrag (2026-08-07): W2 Hedge-Risikofaktoren - und dabei der Fund, dass 9 von 11 Hedge-Empfehlungen verdrehte Zonen hatten

W2 war als Anhaengsel an W1 geplant: die Hedge-Mails schrieben "Keine
strukturierten Risikofaktoren verfuegbar", weil die Pipeline gar keine
berechnet. Beim Bauen kam die Nutzer-Frage dazu, ob Hedge-Positionen ueberhaupt
korrekt bewertet und in Mail/GUI richtig dargestellt werden. Die Antwort auf
diese Frage ist der eigentliche Fund des Tages.

### Der Fund: die Zonen stehen falsch herum

Am Export gemessen, alle Hedge-Kaufempfehlungen:

| | |
|---|---|
| Zonen KORREKT (Stop unter Entry, Ziel darueber) | **2** |
| Zonen VERDREHT (Stop ueber Entry, Ziel darunter) | **9** |
| ohne Zonen | 3 |

Beispiel DBPK vom 06.08.:

    Entry 0,1217   Stop 0,1565 (+28,6 %)   Ziel 0,0870 (-28,6 %)

Bei einer NACHKAUFEN-Empfehlung heisst das: **der Stop ist schon beim Einstieg
ausgeloest**, und das Ziel liegt in Verlustrichtung. Beide Symbole betroffen
(3QSS 4x, DBPK 5x) - kein Einzelfall, sondern der Regelfall.

**DIE URSACHE ist eine Denkrichtung, kein Rechenfehler.** Das Modell denkt in
der MARKTrichtung ("wir wollen, dass der Index faellt") statt in der
INSTRUMENTENrichtung ("wir kaufen ein inverses Produkt, das STEIGT, wenn der
Index faellt"). Der Prompt sagt seit dem 18.07. inhaltlich das Richtige
(Regel 9) - **es reicht nicht.**

### Was der Fehler angerichtet hat, und warum er unsichtbar blieb

Ein Stop oberhalb des Einstiegs bedeutet fuer das Backward-Tracking: sofort
ausgeloest. Genau deshalb stand die Klasse im Export bei `etf real n=0` -
**der Fehler hat sich hinter der fehlenden Auswertung versteckt.** Haette sie
funktioniert, waeren reihenweise sofortige Stop-Loss-Treffer entstanden, und
die Systemguete der Klasse waere aus lauter -1-R-Faellen zusammengesetzt
gewesen.

In der E-Mail stand er dagegen die ganze Zeit sichtbar - Stop ueber dem
Einstieg, bei einer Kaufempfehlung. Der Nutzer hat genau dort nachgefragt.

### Die Behebung: Wache statt besserer Worte

`_pruefe_hedge_zonen()` prueft deterministisch `stop < entry < ziel` bei
KAUFEN/NACHKAUFEN. Ist die Ungleichung verletzt, werden **die Zonen
verworfen** - die Handlungsempfehlung bleibt (Regel 9: die Zonen sind
informativer Kontext, keine Kauf-Voraussetzung).

**WARUM VERWORFEN UND NICHT GETAUSCHT.** Ein Tausch waere verlockend: die
Abstaende sehen plausibel aus (6-29 %), nur die Rollen scheinen vertauscht.
Aber wir wissen NICHT, was die Zahl bedeuten sollte - ob das Modell den
Instrumentenpreis meinte und die Richtung verwechselte, oder ob es ueber ein
Indexniveau nachdachte und es als Instrumentenpreis ausgab. Eine Zahl
umzudeuten, deren Bedeutung unklar ist, waere genau die stille Annahme, an der
diese Woche schon mehrfach etwas gescheitert ist.

Zusaetzlich **Regel 9b im Prompt**, diesmal als Ungleichung statt als Prosa:
`stop_loss < entry < take_profit`, mit dem gemessenen Befund als Begruendung.
Die Wache bleibt trotzdem - ein Prompt ist eine Bitte, kein Gate.

### W2 selbst: sieben Risikofaktoren mit umgekehrter Wirkrichtung

`compute_risikofaktoren_hedge()` - eigene Funktion, weil in
`compute_risikofaktoren()` saemtliche Vorzeichen fuer eine Long-Kaufidee
stehen:

| Faktor | Wirkrichtung |
|---|---|
| Abdeckungsgrad | Kontext - wo steht die Absicherung heute |
| Absicherung weitgehend aufgebaut (>= 80 % des Ziels) | **negativ** - Nachkauf bringt wenig Schutz, kostet volle Praemie |
| VIX hoch (>= 25) | **negativ** - Praemie ist teuer, WEIL der Markt die Gefahr sieht |
| VIX niedrig (<= 16) | **positiv** - der bessere Zeitpunkt ist, bevor es gebraucht wird |
| Aktien-Baerenmarkt aktiv | **negativ** - nachlaufend, jetzt aufstocken heisst nach dem Schaden versichern |
| Volatilitaets-Drag (2x/3x taeglich) | **negativ** - struktureller Preis, spricht gegen langes Halten |
| Bull-Wahrscheinlichkeit >= 50 % | **negativ** - Spiegelbild des Gegenszenarios |
| Hedge-Budget ausgeschoepft | **negativ** - Empfehlung wurde bereits gekuerzt |

Zwei davon sind bei einer Long-Position gar nicht vorhanden (Drag,
Abdeckungsgrad), und zwei haben dort das **entgegengesetzte** Vorzeichen (VIX,
Baerenmarkt). Das ist der ganze Punkt von W2.

Bei allem ausser KAUFEN/NACHKAUFEN bleibt nur der Kontextfaktor - fuer ein
HALTEN ist "wie teuer waere der Zukauf" gegenstandslos.

### Zur Bewertungsfrage: die Zahlen selbst sind RICHTIG

Der Bestandswert einer Hedge-Position (`Menge x Kurs`) und ihr P&L gegen den
Einstandspreis sind **arithmetisch korrekt und duerfen nicht invertiert
werden** - ein 3QSS-Bestand, der 10 % gefallen ist, ist real 10 % weniger wert.
Was fehlte, war nicht die Umkehrung der Zahl, sondern der **Kontext**, der ein
Minus lesbar macht: dass es die Praemie ist und nicht ein Fehler. Den liefern
jetzt die Risikofaktoren (Mail und GUI) und die Wirksamkeits-Karte aus W1.

**Geprueft:** 19 Pruefungen in `teste_hedge_risikofaktoren.py`, darunter der
echte DBPK-Fall vom 06.08. und der korrekte 3QSS-Fall vom selben Tag als
Gegenprobe. Sieben Testsuiten und die Signaturpruefung gruen.


---

## Nachtrag (2026-08-07): warum die Nicht-Krypto-Klassen fast nur HALTEN sagen - untersucht, nicht vermutet

Vollstaendige Untersuchung in `Zwischenstand_Gesamtprojekt_06_08.md` Abschnitt
**8c**. Kurzfassung der Befunde:

**Es kommen Signale** - 201 Nicht-Krypto-Spot-Signale im Exportfenster. Aktien
(43) und Themen-ETF (89) haben in der GESAMTEN Historie nie etwas anderes als
HALTEN gesagt, Rohstoffe 65x HALTEN gegen 4x VERKAUFEN.

**Hauptursache: es fehlt das Akkumulations-Framework.** Wortzaehlung in den
Prompts - Krypto-Spot hat 7x "Tranche" und 15x "antizyklisch", Aktien,
Themen-ETF und Rohstoffe haben **null**. Sie kennen NACHKAUFEN nur als Wort
ohne Mechanik. Fuer eine langfristig gehaltene Position ohne Aufstockungsanlass
bleiben HALTEN oder VERKAUFEN - und Regel 6 schreibt HALTEN sogar ausdruecklich
vor, solange die These intakt ist. **Das System verhaelt sich regelkonform; die
Luecke ist eine fehlende Handlungsoption, kein Fehler.**

**Zweite Ursache: 49 von 201 erreichen das LLM gar nicht** (Fixed-Signale) -
aber die Datierung zeigt, dass der Grossteil **Vergangenheit** ist. ISOC
("Historie veraltet, letzter Tag 2025-09-10", 6x) und X136 ("keine historischen
Daten", 6x) traten zuletzt am **27.07.** auf; beide fuehren heute Daten bis zum
06.08. **Ein Vorschlag "ISOC/X136 reparieren" waere Arbeit an einem erledigten
Punkt gewesen - erst die Datierung der Faelle hat das gezeigt.** Es bleibt
"Preis veraltet" mit 13 Faellen seit dem 05.08., und das betrifft auch BTC
(12x) und ETH - also die Staleness-Ueberwachung insgesamt, nicht diese
Untersuchung.

**Das Gate ist NICHT die Ursache:** 5 Risk-Vetos in der gesamten Historie, 0
Cash-Vetos. Konfidenz-Median 66 % gegen 70 % bei Krypto - das Modell ist nicht
ratlos, es hat keinen Anlass zu handeln.

### Der Zeithorizont - Nutzer-Vorgabe und Ist-Zustand

Vorgabe: Spot/ETF/Aktien/Rohstoffe ueber **Monate**, Hebel **1-5, max 14 Tage**.

Das System staffelt die Ablauffristen bereits (kurz 14 / mittel 45 / lang 120),
ordnet sie aber **je Signal vom LLM** zu - und rechnet die Basislinie fuer ALLE
Klassen fest auf **14 Tage**. Daraus zwei Messfehler:

- eine 120-Tage-Position wird gegen einen 14-Tage-Zufallseinstieg verglichen;
  der Signalbeitrag der langfristigen Klassen ist damit falsch berechnet
- 1.117 von 1.703 Hebel-Signalen tragen `mittel` = 45 Tage, bei einer Praxis von
  1-5 Tagen. Themen-ETF traegt denselben Bucket fuer Monate. **Zwei voellig
  verschiedene Praxen, derselbe Horizont.**

> **Die "andere Loesung", nach der gefragt wurde:** der Zeithorizont gehoert an
> die ASSETKLASSE gebunden, nicht an das Einzelurteil des Modells. Das Modell
> darf innerhalb des Klassenrahmens verfeinern, aber keinen Hebel-Trade auf 45
> Tage stellen.

### Vier Massnahmen, priorisiert (Details in 8c)

| | | Aufwand |
|---|---|---|
| ~~H-1~~ | ~~ISOC/X136-Historie~~ - bereits behoben, letzter Fall 27.07. | - |
| H-2 | Zeithorizont je Assetklasse deckeln | mittel |
| H-3 | Basislinien-Horizont an den Bucket koppeln | mittel |
| H-4 | Akkumulations-Konzept fuer Aktien/ETF/Rohstoffe | gross |

H-4 ist die Ursache, H-2 und H-3 sind die Voraussetzung dafuer, den Erfolg von
H-4 ueberhaupt messen zu koennen. **H-1 wurde beim Gegenpruefen zurueckgezogen** -
zum zweiten Mal an diesem Tag haette ein Befund zu Arbeit an etwas Erledigtem
gefuehrt, wenn er nicht datiert worden waere. **Bewusst NICHT auf der Liste: die Gates
lockern** - sie sind nachweislich nicht die Ursache, und eine Lockerung wuerde
die Diagnose verwischen.


---

## Nachtrag (2026-08-07): der Ausbaustand-Drift - genau EIN Fakt wurde je auf alle Spot-Klassen ausgerollt

Nutzer-Einwand zur HALTEN-Untersuchung: *"hier musst du bei den Multi- oder
sonstigen Assets genau achten, wo und wie diese umgesetzt wurden, u.U. haengen
die noch Wochen zurueck vom Code und Themenlage."*

Berechtigt - und der gemessene Rueckstand ist groesser als die Untersuchung in
8c angenommen hatte. Vollstaendige Tabellen in
`Zwischenstand_Gesamtprojekt_06_08.md` **Abschnitt 8d**.

### Der Befund in einer Zeile

**Von elf Fakten, die zwischen dem 09.07. und dem 06.08. entstanden sind, wurde
genau EINER auf alle fuenf Spot-Klassen ausgerollt** - `crv_baender`, gestern,
und der nur, weil er ausdruecklich so gefordert war ("nicht selektiv fuer eine
Funktionalitaet sondern ueber alle Assets korrekt anpassen").

Alles andere - `markt_kontext`, `regime_profil`, `antizyklisch` (alle 09.07.),
`tranchen_erlaubt` (12.07.), `liquiditaetszonen` (23.07.), `signal_stabilitaet`
(25.07.), `marktscan_reifegrad` (30.07.), `ausstiegsregel`, `systemguete`,
`kosten` (alle 05.08.) - ging ausschliesslich an Krypto-Spot und/oder Hebel.

**Der Stand der Nicht-Krypto-Analysten entspricht im Kern dem 09.07.**

Auf Pipeline-Ebene dasselbe Bild: Hebel hat 9 von 12 geprueften Mechanismen,
Krypto-Spot 7, Aktien/Themen-ETF/Rohstoffe je 5, Hedge 3.

### Was das an der HALTEN-Diagnose aendert

Sie bleibt richtig, aber ihre Ursache ist breiter: es fehlt nicht nur das
Akkumulations-Framework, sondern sechs von elf Weiterentwicklungen.

Und ein Punkt aus 8c wird erst jetzt erklaerbar: dort stand, dass
`original_action` bei allen Nicht-Krypto-Signalen None ist und sich deshalb
nicht unterscheiden laesst, ob das LLM HALTEN sagte oder ein Gate es
ueberschrieb. Der Grund ist, dass diese Pipelines das Feld **nie setzen** - die
Unterscheidung ist strukturell unmoeglich, nicht nur ungemessen.

### Die eigentliche Lehre

Der Rueckstand ist **kein Zufall, sondern ein Muster**: jede Erweiterung wurde
dort gebaut, wo gerade gearbeitet wurde. Der Rollout auf die uebrigen Klassen
war nie Teil der Definition von "fertig".

> **Eine Erweiterung an einer Pipeline ist nicht fertig, wenn sie dort laeuft.
> Sie ist fertig, wenn entschieden ist, ob sie fuer die anderen fuenf gilt - und
> die Entscheidung dokumentiert ist.** Ein "gilt nur fuer Krypto, weil X" ist ein
> gueltiges Ergebnis; ein stilles Auslassen nicht.

### Vier Massnahmen ergaenzen die Liste aus 8c

| | | Aufwand |
|---|---|---|
| H-5 | Rollout-Pruefung als Pflichtschritt bei jeder Fakten-/Regel-Aenderung | klein, dauerhaft |
| H-6 | `original_action` + Selbst-HALTEN-Tracking auf die Spot-Familie | klein |
| H-7 | `ausstiegsregel`/`systemguete`/`kosten` von Hebel auf die Spot-Familie pruefen | mittel |
| H-4 | Akkumulations-Konzept fuer Aktien/ETF/Rohstoffe | gross |

**H-6 ist der guenstigste Punkt und macht 8c erst auswertbar. H-5 ist der
eigentliche Befund** - ohne ihn entsteht derselbe Drift bei der naechsten
Erweiterung wieder.


---

## Nachtrag (2026-08-07): H-6 ausgerollt, H-5 als dauerhafte Pruefung gebaut - und eine Korrektur an meiner eigenen Priorisierung

### H-6: `original_action` und Selbst-HALTEN-Tracking fuer die Spot-Familie

`post_check()` setzt `_original_action` und `_ist_reines_llm_halten` seit dem
31.07. fuer **alle vier** Spot-Pipelines - abgeholt hat sie bisher
ausschliesslich `agent/krypto/pipeline.py`. Drei Zeilen je Pipeline in Aktien,
Themen-ETF und Rohstoffe, die Signal-Felder und der Export existierten laengst.

Damit wird beantwortbar, was in Abschnitt 8c offen bleiben musste: **wie viele
der 201 HALTEN kommen vom Modell und wie viele vom Gate?** Vorher war das nicht
ungemessen, sondern strukturell unmoeglich.

Zusaetzlich laeuft ab jetzt das Selbst-gewaehltes-HALTEN-Schattentracking auch
fuer diese drei Klassen - dieselbe Messung, die fuer Krypto seit dem 31.07.
existiert.

### H-5: `pruefe_fakten_rollout.py`

Vergleicht die `build_facts()`-Quelltexte aller sechs Pipelines und meldet jeden
Fakt, der nur in einer Teilmenge existiert, dazu zehn Mechanismen auf
Pipeline-Ebene. **Das Skript faellt kein Urteil** - viele Unterschiede sind
richtig (`btc_relativwert` gehoert nicht zu Rohstoffen, Hedge hat bewusst keine
technische Analyse). Es stellt die Frage, ob sie ENTSCHIEDEN wurden; begruendete
Faelle wandern in `BEGRUENDETE_UNTERSCHIEDE` und tauchen dann nicht mehr auf.

Erster Lauf nach H-6: **vier Fakten und zwei Mechanismen** in der Spot-Familie
ungleich verteilt - `antizyklisch` (seit 09.07.), `tranchen_erlaubt` (12.07.),
`liquiditaetszonen` (23.07.), `signal_stabilitaet` (25.07.), dazu Mindestziel
und JIT-Historie. Das sind genau die offenen Entscheidungen, nicht mehr und
nicht weniger.

### Korrektur: B1 (Befolgungsgrad) war als "zentraler Blocker" ueberzeichnet

Nutzer-Position vom 07.08.: *"das System muss auch ohne explizite Durchfuehrung
der Empfehlungen funktionieren - Anwendung kommt nach Funktion. Ansonsten muss
das System mit den systeminternen Messungen seine Qualitaet messen und
kalibrieren."*

**Das ist fachlich richtig, und meine Einordnung vom 07.08. frueh war zu stark.**
Ich hatte den leeren Befolgungsgrad zum "zentralen Blocker" erklaert, an dem die
Aussagekraft aller Kennzahlen haengt. Tatsaechlich misst
`umgesetzt`/`umgesetzt_am` das Verhalten des NUTZERS, nicht die Qualitaet des
SYSTEMS. Beides zu vermengen erzeugt genau die Schleife, die der Nutzer benennt:
keine handelbaren Signale -> keine Trades -> keine Befolgungsdaten -> keine
Messung -> keine besseren Signale.

Die Qualitaetsmessung steht bereits auf eigenen Beinen und braucht den
Befolgungsgrad nicht:

| vorhanden | was es misst |
|---|---|
| R-Multiples aus dem Backward-Tracking | Ergebnis gegen ECHTE Kursreihen |
| Basislinie (Zufallseinstieg, gleiche Parameter) | ist das Signal besser als Zufall |
| Schattenarm | was das Gate verhindert hat |
| Systemguete (SQN/Expectancy/Profit-Faktor) | die Zielgroesse |

**B1 faellt damit von "zentraler Blocker" auf "waere zusaetzlich interessant".**
Was die systeminterne Messung dagegen WIRKLICH braucht, steht schon auf der
Liste: Kosten im R (bisher nur Hebel), Horizont je Assetklasse (H-2/H-3) und
ueberhaupt handelbare Signale (H-4). Eine Trefferquote ueber 200x HALTEN misst
nichts.

> **Die Lehre:** eine Kennzahl, die das Verhalten des Nutzers misst, gehoert
> nicht in die Bewertung des Systems. Ich hatte sie dorthin gestellt, weil sie
> die Zahlen "ehrlicher" gemacht haette - aber sie haette sie nur unmessbar
> gemacht.


---

## Nachtrag (2026-08-07): H-2/H-3 Zeithorizont - und eine Zwischenrecherche zu den Bewertungsparametern, die drei Luecken findet

### H-2: Zeithorizont-Deckel je Assetklasse

`halte_kriterium_bucket` kommt vom LLM je Signal. Gemessen: **1.117 von 1.703
Hebel-Signalen tragen "mittel" = 45 Tage** - bei einer Handelspraxis von 1-5,
maximal 14 Tagen. `gedeckelter_bucket(bucket, tier)` begrenzt das auf "kurz"
fuer Hebel; die Spot-Klassen bleiben ungedeckelt.

**DER DECKEL IST EIN MAXIMUM, KEIN MINDESTWERT** - und das war die
entscheidende Praezisierung durch den Nutzer: *"auch bei laengerfristigen
Positionen kann es zu sehr hoher Volatilitaet und ggf. kuerzeren Trades kommen,
auch wenn diese urspruenglich laengerfristig geplant sind."*

Genau deshalb wird nur nach oben begrenzt. Der Bucket steuert ausschliesslich,
ab wann ein NICHT aufgeloestes Signal als abgelaufen gilt. Ein Signal, das nach
drei Tagen seine Zone trifft, loest nach drei Tagen auf - der Deckel verkuerzt
nie einen Trade, er verhindert nur, dass ein Hebel-Signal 45 Tage lang als
"offen" gefuehrt wird.

### H-3: Basislinien-Horizont folgt der Gruppe

Bis hierher rechnete die Basislinie fuer JEDE Klasse fest 14 Tage - eine
Position mit 120 Tagen Frist wurde gegen einen 14-Tage-Zufallseinstieg
gestellt, und der Signalbeitrag der langfristigen Klassen war damit
systematisch falsch.

Genommen wird jetzt die **gemessene mediane Haltedauer der Gruppe** (die fuers
Kostenmodell ohnehin berechnet wird), nicht der konfigurierte Bucket. Das ist
der empirisch richtige Vergleich - und erledigt denselben Nutzer-Hinweis von der
anderen Seite: schliessen die Signale einer Gruppe tatsaechlich nach vier Tagen,
misst die Basislinie vier Tage, unabhaengig davon was geplant war. Das
Fensterende folgt demselben Horizont.

---

## Zwischenrecherche: haben alle Assetklassen die richtigen Bewertungsparameter?

Nutzer-Frage vor dem naechsten Umbau: *"haben wir fuer alle Assetklassen die
korrekten Bewertungsparameter oder gibt es da noch Luecken, u.U. eine kurze
Zwischenrecherche, sonst bauen wir wieder mehrmals um."*

**Antwort: es gibt drei Luecken.**

### Luecke 1: die Spot-Kosten sind fuer Nicht-Krypto zu hoch angesetzt

`_KOSTEN_SPOT_JE_SEITE = 0,01` - **1 % je Seite, 2 % Roundtrip, fuer ALLE
Spot-Klassen gleich.** Bei einem Stop von 5 % ergibt das **0,40 R Kosten**:

| Klasse | kosten_r (Stop 5 %, 10 Tage) | belegt |
|---|---|---|
| hebel | 0,280 | **ja** (104 Positionen) |
| krypto / aktien / etf / rohstoffe / hedge | **0,400** | nein |

Fuer Krypto bei Bitpanda ist 1 % je Seite plausibel - der Spread dort ist weit.
Fuer **Aktien und Themen-ETFs an einer Boerse** (Ordergebuehr plus enger
Spread) ist er es nicht; realistisch liegt der Roundtrip dort um eine
Groessenordnung niedriger. Die Folge: der Netto-Erwartungswert dieser Klassen
wird systematisch zu schlecht gerechnet - und zwar um mehr, als die gesamte
Break-even-Luecke ausmacht.

**Fuer Hedge fehlt zusaetzlich eine ganze Kostenart**: gehebelte ETPs tragen
eine laufende Gebuehr und Swap-Kosten. Das Spot-Kostenmodell kennt aber gar
keine Haltedauer-Komponente (`_KOSTEN_SPOT_JE_SEITE` faellt einmal je Seite an).
Eine ueber Monate gehaltene Absicherung erscheint damit billiger als sie ist.

### Luecke 2: RM-3 existiert nur auf dem Papier

`max_allokation_pro_klasse_prozent` steht in der config:

    krypto: 100     # [OFFEN] aktuell nur Krypto im Einsatz
    aktien: 0
    etf: 0
    rohstoffe: 0

**Der Wert wird an KEINER Stelle im Code gelesen** (kein Treffer fuer
`pro_klasse` in `*.py`). RM-3 ist damit nicht implementiert.

Zwei Seiten davon:

- **Entwarnung:** die Nullen blockieren heute nichts. Sie sind NICHT die
  Ursache der HALTEN-Flut.
- **Aber:** wuerde RM-3 morgen implementiert, blockierte es mit diesen Werten
  **genau die drei Klassen, die laut Nutzer gehandelt werden sollen** - lautlos
  und mit voller Regelwerks-Legitimation. Der Kommentar "[OFFEN] aktuell nur
  Krypto im Einsatz" stammt aus einer Zeit, in der das stimmte.

### Luecke 3: die Risikoparameter sind global, die Praxis ist es nicht

Klassenspezifisch differenziert sind heute nur `risiko.hebel.*` und die (tote)
Allokationstabelle. **Global fuer alle Klassen gelten dagegen:**

| Parameter | Wert | passt das fuer eine Monats-Aktienposition? |
|---|---|---|
| `ziele.crv_minimum` | 2,0 | fraglich - bei Monaten ist ein CRV von 2 eine andere Aussage als bei 3 Tagen |
| `risiko_pro_trade_prozent` | 2 | fraglich - gilt fuer einen 3-Tage-Hebel wie fuer eine Kernposition |
| `sl_abstand_min_atr_faktor` | 0,75 | ATR ist tagesbasiert; ueber Monate eine andere Groesse |
| `sl_abstand_eng_schwelle_relativ` | 0,025 | dito |
| `max_allokation_pro_asset_prozent` | 25 | plausibel klassenuebergreifend |

Das ist **kein akuter Defekt**, aber es ist der Grund, warum ein
Akkumulations-Konzept (H-4) nicht einfach "wie Krypto, nur woanders" gebaut
werden kann: die Schwellen, gegen die es arbeitet, sind fuer den kurzen
Horizont kalibriert.

### Was daraus fuer die Reihenfolge folgt

> **Die Recherche hat sich gelohnt: zwei der drei Luecken haetten nach einem
> H-4-Umbau erneut zu einem Umbau gefuehrt.** Kostensaetze und
> Klassenparameter gehoeren VOR das Akkumulations-Konzept, nicht danach.

| # | | vor H-4? |
|---|---|---|
| **P-1** | Spot-Kostensaetze je Klasse trennen (Krypto/Bitpanda gegen Boerse) + laufende Gebuehr fuer Hedge-ETPs | **ja** |
| **P-2** | RM-3 entscheiden: implementieren mit realistischen Werten, oder die tote Tabelle entfernen | **ja** (klein) |
| **P-3** | `crv_minimum` und `risiko_pro_trade_prozent` je Klasse pruefen | **ja** |
| H-4 | Akkumulations-Konzept | danach |

**Bewusst nichts davon heute gebaut** - die Frage war eine Recherche, und jede
dieser drei Aenderungen braucht eine eigene Entscheidung ueber die Zahlen.


---

## Nachtrag (2026-08-07): Bitpanda-Gebuehren recherchiert und Schwerpunkte/Screener geprueft - zwei Konzeptfragen vor H-4

Vollstaendig in `Zwischenstand_Gesamtprojekt_06_08.md` **Abschnitt 8e**.

### Gebuehren: drei STRUKTURELLE Probleme, nicht nur falsche Zahlen

**1. Aktien und ETFs haben bei Bitpanda eine FIXE Gebuehr** - 1 EUR je Trade
plus Spread bis 0,5 %, unabhaengig vom Ordervolumen. Damit **kuerzt sich der
Einsatz nicht mehr heraus**, und genau darauf beruht unser Kostenmodell. Bei
einem 5-%-Stop: 300-EUR-Position 0,133 R, 1.000 EUR 0,040 R, 2.000 EUR 0,020 R -
das Modell setzt fuer alle drei **0,400 R** an, also drei- bis zwanzigfach zu
hoch.

**2. Die Gebuehr ist nicht separat ausgewiesen, sie steckt im Kurs.** An 5.734
echten Trades geprueft: `Fiat / (Menge x Preis)` ergibt **0,000 % Median**. Aus
den Transaktionsdaten allein ist sie nicht messbar.

**3. Krypto ist coin-abhaengig** (0,99 % BTC bis 2,49 % Altcoin) - pauschal 1 %
ist fuer BTC plausibel und fuer kleine Coins zu niedrig, also in die
GEGENRICHTUNG falsch wie bei Aktien.

**Wichtige Abgrenzung, die leicht schiefgeht:** OD7N/OD7H/OD7C/OD7L sind
BOERSENGEHANDELTE ETCs, nicht Bitpanda Metals. Die Metals-Aufschlaege (Silber
2,5 % Kauf / 2,0 % Verkauf) gelten fuer sie NICHT. Wer das verwechselt, rechnet
mit dem Dreifachen.

**Konzept in drei Stufen** (Details in 8e): Struktur je Klasse statt eines
Satzes fuer alle (`prozentual` gegen `fix_plus_spread`), dann ein konservativer
Satz je Klasse statt je Symbol, dann messen statt schaetzen. Der Spread ist
gegen die eigene Kursreihe messbar - erster Versuch mit dem 90-Tage-Fenster
ergab n=31/16, zu wenig; gegen die volle OHLC-Tabelle auf dem Notebook waere es
belastbar. Bis dahin bleibt `kosten_belegt = False`.

### Schwerpunkte/Screener: vier Luecken

Es existieren **sechs aktive Kategorie-Thesen** (energie und edelmetalle
uebergewichten, agrar/industriemetalle neutral, absicherung), Pruefmechanismen,
105 Synthese-Laeufe und `these_abgleich` als Fakt in vier Analysten.

Was fehlt:

1. **Der Budget-Allocator kennt die Thesen nicht** - keine Erwaehnung von
   These/Kategorie/Schwerpunkt. Eine uebergewichtete Kategorie bekommt keinen
   bevorzugten LLM-Slot. Genau der "Fokus", um den es geht, fehlt an der
   Stelle, an der er wirken muesste.
2. **Keine aktive Benachrichtigung** fuer Screener-Kandidaten je Schwerpunkt -
   der Gap ist seit dem 19.07. bekannt und wurde ZWEIMAL nur passiv geschlossen
   (GUI-Sortierung 20.07., Score-Bonus 25.07.).
3. **Die Thesen decken nur Rohstoff-Hauptgruppen und Absicherung ab** - es gibt
   keine These fuer Krypto, Aktien oder Themen-ETF. Ein Schwerpunkt "KI", den
   der Nutzer als Beispiel nennt, liesse sich heute gar nicht setzen.
4. **Kein Override** - ein manuell gesetzter Schwerpunkt ist nicht vorgesehen.

> **Warum das H-4 vorgelagert ist:** ein Akkumulations-Konzept beantwortet "wann
> aufstocken?", der Schwerpunkt "wo ueberhaupt hinsehen?". Baut man H-4 zuerst,
> entsteht eine Aufstockungslogik, die alle Kategorien gleich behandelt - und
> der Schwerpunkt muesste nachtraeglich hineinoperiert werden.

Quellen: Handelsblatt (Bitpanda-Gebuehren je Anlageklasse), Finanzfuchs
(Krypto-Spreads und Fusion-Staffel).


---

## Nachtrag (2026-08-07): Bitpanda-Handelbarkeit als Regel vervollstaendigt und in der Marktsuche schaltbar gemacht

Nutzer-Vorgabe: *"auch bei diesen Assets ist es relevant, ob bei BP handelbar
oder nicht - als Regel bitte entsprechend beruecksichtigen und auch bei der
Marktsuche aus- und einschaltbar machen."*

### Erst der Bestand: mehr vorhanden als erwartet

**RM-Bitpanda ist eine echte Gate-Regel** in `risk_gate.py::pre_check()` und
assetklassen-neutral formuliert: ein nachweislich nicht gelistetes Asset
bekommt ein Veto, `None` (Abruf fehlgeschlagen) fuehrt bewusst zu KEINEM Veto
(P-10: unbekannt ist kein Ausschlussgrund). Dazu existiert ein
Override-Mechanismus (`asset_bitpanda_override`, seit 20.07.).

Verdrahtet war sie in **vier von sechs** Pipelines: Krypto-Spot, Aktien,
Rohstoffe, Themen-ETF. **Hedge hatte sie nicht** - als einzige, weil es ein
eigenes Gate (`_post_check_hedge`) nutzt und die Regel deshalb nie mitbekam.
Genau das Muster, das der Rollout-Check vom selben Tag sichtbar machen soll.

Ebenfalls vorhanden: ein Schalter `benachrichtigung.email.nur_bitpanda_gelistet`
- der steuert aber nur den **E-Mail-Versand**, nicht die Marktsuche.

### Der eigentliche Fund: die Marktsuche filterte nie

Screener und Marktscan **erfassen** `bitpanda_gelistet` seit jeher als Merkmal
und zeigen es im Screener-Tab als Spalte. **Gefiltert wurde nie danach** - ein
nicht handelbarer Kandidat stand gleichberechtigt in der Liste, obwohl die
Umsetzung ueber die Bitpanda-App laeuft.

### Was gebaut wurde

1. **`marktsuche.nur_bitpanda_gelistet`** in `config.yaml`, Standard `true`.
   Bewusst ein SCHALTER und kein hartes Gate: die Information "es gaebe da
   etwas, nur nicht bei deinem Broker" kann wertvoll sein.
2. **`config.kandidat_ist_handelbar()`** - eine Stelle fuer die Entscheidung,
   mit derselben P-10-Regel wie das Gate: **unbekannt bleibt drin**, nur ein
   ausdrueckliches `False` filtert.
3. **Filter im Screener-Tab** beim Rendern, plus die Zahl der ausgeblendeten
   Kandidaten in der Statuszeile - **ein Filter, der unbemerkt wirkt, ist ein
   Datenverlust**.
4. **GUI-Menue "Marktsuche"** mit dem Schalter, neben dem bestehenden
   E-Mail-Schalter, aber bewusst in einem eigenen Menue: er steuert die
   ANZEIGE, nicht den Versand.
5. **RM-Bitpanda fuer Hedge** nachgezogen. Heute kein akuter Fehler - DBPK und
   3QSS SIND gelistet, sonst waeren sie nicht im Bestand. Aber ein kuenftiges
   Hedge-Instrument ohne Listing waere lautlos empfohlen worden.

### Offen und bewusst nicht mitgebaut

Der **Krypto-Marktscan** erfasst `bitpanda_gelistet` ebenfalls, filtert aber
weiterhin nicht - er speist die Kandidaten-Warteschlange, und ein Filter dort
wuerde die Discovery selbst beschneiden statt nur die Anzeige. Das ist eine
eigene Entscheidung (Discovery gegen Anzeige) und gehoert nicht nebenbei
getroffen.


---

## Nachtrag (2026-08-07): warum nur Rohstoffe eine These haben - es ist der Deckel, nicht die Mechanik

Nutzer-Hinweis: es gebe bereits ein Grobkonzept mit Haupt- und Untergruppen,
und bei Rohstoffen habe man nur begonnen. Beides bestaetigt. Vollstaendig in
`Zwischenstand_Gesamtprojekt_06_08.md` **Abschnitt 8f**.

### Die Struktur ist vollstaendig

`Basisinfos/kategorien.yaml` fuehrt **10 Hauptgruppen, 72 Unterkategorien und
211 zugeordnete Bitpanda-Symbole** - darunter "Technologie & KI" mit 18
Unterkategorien (inklusive "Kuenstliche Intelligenz"), "Aktien - Regionen &
Laender" mit 66 Symbolen, "Aktien - Sektoren", "Anleihen & Geldmarkt".

Thesen gibt es fuer **5 von 10** Hauptgruppen - die vier Rohstoffgruppen plus
Absicherung. **160 von 211 Symbolen (76 %) haben kein Themenfeld-Urteil.**

**Korrektur an meinem eigenen Vorschlag von vorhin:** ich hatte gefragt, ob
"KI" als neue Hauptgruppe oder als eigene Ebene angelegt werden soll. Beides
ueberfluessig - es existiert seit dem 19.07. Haette ich vor dem Vorschlag in
die Doku gesehen, waere die Frage nicht entstanden. Zum zweiten Mal an diesem
Tag ein Vorschlag zu etwas, das es schon gibt.

### Auch die Mechanik ist gebaut - und sie laeuft

`_BELLWETHER_TICKER` deckt `technologie_ki:ki`, `:halbleiter`,
`:cybersicherheit`, `:biotech` und vier `aktien_sektoren:*` ab (Analystentrend
Finnhub + Insider SEC EDGAR + Short-Interest FINRA). Von 16
Aenderungsvorschlaegen entfallen **4 auf technologie_ki und 6 auf
aktien_sektoren** - der KI-Vorschlag steht seit dem **25.07.** in Beobachtung.

### Die Ursache: ein Deckel bei sechs

    richtgroesse_max_aktive_thesen: 6
    aktive Thesen heute:            6
    Budget:                         0

`_bestimme_gesperrte_fall_a_kandidaten()` rechnet `budget = richtgroesse_max -
aktuelle_anzahl`. Bei sechs aktiven Thesen ist das null - **kein reifer
Vorschlag kann mehr automatisch uebernommen werden.** Der Status belegt es: 14
von 16 Vorschlaegen stehen auf "beobachtung", genau einer wurde je uebernommen.

**Das ist kein Bug** - die Richtgroesse 3-6 ist eine bewusste Entscheidung
(Kategorie_Basisinformationen_Release2.md Abschnitt 5). Der Punkt ist:

> **Die sechs Plaetze sind von den Rohstoffen belegt, weil sie zuerst da waren -
> nicht weil sie die wichtigsten waeren.** Zwei davon stehen auf `neutral` und
> belegen denselben Platz wie eine potenziell relevante KI-These. Es gibt keinen
> Verdraengungsmechanismus: first come, first served statt Prioritaet.

### Vier Massnahmen (Details in 8f)

| | | Aufwand |
|---|---|---|
| S-1 | **Verdraengung statt Sperre** - bei vollem Budget die schwaechste bestehende These gegen die neue abwaegen | mittel |
| S-2 | Richtgroesse erhoehen oder je Hauptgruppe vergeben - sechs Plaetze bei zehn Gruppen heisst strukturell, dass vier Felder nie ein Urteil bekommen | klein/mittel |
| S-3 | Sichtbarkeit - "seit 13 Tagen wartet ein KI-Vorschlag" gehoert auf die Uebersichtsseite | klein |
| S-4 | Allocator-Prioritaet (8e Luecke 1) - erst sinnvoll, wenn die Themenfelder Thesen tragen | mittel |

**S-1 und S-2 sind die eigentliche Antwort auf den Nutzer-Wunsch nach einem
Override**: ein manueller Override ist technisch der einfachste Fall von S-1 -
der Nutzer entscheidet die Verdraengung selbst.


---

## Nachtrag (2026-08-07): Themen-Bruecken und Asset-Steckbrief - zwei Nutzer-Vorgaben, eine gemeinsame Regel

### Die Vorgaben

**1. Themen quer zu den Hauptgruppen.** Am Kupfer-Beispiel: *"es gibt
Kupferminer (Aktien), Kupfer als Material oder ETF ... Es werden Werte aus
diesem Bereich mit Potential vorgeschlagen - eine automatische Bewertung halte
ich vorerst als fast nicht umsetzbar - und ICH entscheide, das riskantere Aktien
oder in nicht so riskante ETF einzusteigen."*

**Diese Arbeitsteilung ist richtig, und zwar aus dem Grund, den der Nutzer
selbst nennt.** Die Wahl zwischen Einzelaktie und ETF haengt an
Risikobereitschaft, Bestand und Zeithorizont - drei Dinge, die das System nicht
kennt. Ein Automatismus wuerde eine Praezision vortaeuschen, die es nicht gibt.

Der Befund dahinter: die zehn Hauptgruppen sind nach **Instrumententyp**
geschnitten (Rohstoffe / Aktien-Sektoren / Aktien-Regionen / Anleihen). Kupfer
liegt deshalb in ZWEI getrennten Gruppen - `industriemetalle:kupfer` (Material)
und `aktien_sektoren:grundstoffe` (Miner). Das System konnte bisher gar nicht
"Werte aus diesem Bereich" quer ueber Instrumententypen zeigen.

**Gebaut:** `themen_bruecken` in `kategorien.yaml` - fuenf Bruecken (Kupfer,
Edelmetalle, Energie, Technologie/Halbleiter, Gesundheit/Biotech), dazu
`config.verwandte_kategorien()` und `bruecken_name_fuer()`. Bewusst die
**einfache Variante** (Verknuepfung statt neuer Themen-Ebene) - der Nutzer hat
sie ausdruecklich gewaehlt.

**2. Was ist das Symbol eigentlich?** *"falls moeglich waere es hilfreich zu
wissen, wenn ein Symbol z.B. ABCDE vorgeschlagen wird, welches Asset und was
macht das Asset - vor allem bei ETF relevant, da oft ueber einen Themenbereich
verteilt."*

**Gebaut ohne jede neue Datenquelle.** Drei Bausteine lagen bereits vor: der
`name` aus dem Bitpanda-Katalog, das `group`-Feld (liefert den
INSTRUMENTENTYP: stock/etf/etc/metal) und die Kategorienstruktur. Zusammen:

    COPPERMINE - Copper Miners, ETF (Korb aus vielen Werten),
                 Industriemetalle / Kupfer, Thema Kupfer
    OD7C       - WisdomTree Copper, ETC (besichertes Rohstoff-Zertifikat),
                 Industriemetalle / Kupfer, Thema Kupfer
    PLTR       - Palantir, Einzelaktie, Technologie & KI / Kuenstliche
                 Intelligenz, Thema Technologie und Halbleiter

Der Steckbrief steht im Screener-Tooltip, zusammen mit den thematisch
verwandten Kategorien.

### Die gemeinsame Regel: LUECKEN SIND ERLAUBT

Nutzer-Vorgabe woertlich: *"fuer den User handhabbar (auch wenn kleine Luecken
entstehen) - es muss nicht alles abgedeckt sein und Sinn machen, z.B. kann
Kupfer das Material steigen, aber Miner performen schlecht, aber aus anderen
Gruenden."*

Beide Bausteine folgen dem: fehlt eine Angabe, **faellt sie weg statt geraten zu
werden**. Ein erfundener Steckbrief waere schlechter als ein knapper, und eine
Bruecke, die eine Verbindung behauptet, die es nicht gibt, waere schlechter als
gar keine. Im Test ausdruecklich abgesichert (B7-B9, A5-A7).

**19 Pruefungen**, alle bestanden - inklusive des Falls aus der Nutzer-Frage:
"Kupfer interessant" liefert Material und Miner nebeneinander, und der Nutzer
entscheidet.


---

## Nachtrag (2026-08-07): Kostenmodell strukturell getrennt - die Positionsgroesse geht jetzt ein

Schritt 1 des Gesamtkonzepts. Bis hierher galt EIN Satz fuer die gesamte
Spot-Familie: 1 % je Seite, 2 % Roundtrip, bei 5 % Stop also **0,400 R** - fuer
Bitpanda-Krypto plausibel, fuer Boersen-Aktien um eine Groessenordnung zu hoch.

### Der strukturelle Kern

Bei Bitpanda kosten **Aktien und ETFs 1 EUR FIX je Trade** plus Spread. Eine
fixe Gebuehr bricht die Eigenschaft, auf der die ganze R-Rechnung beruht: **der
Einsatz kuerzt sich nicht mehr heraus.** Deshalb zwei Kostenarten statt einer,
und deshalb geht die Positionsgroesse ein.

| Klasse | Kosten in R (5 % Stop) | Position |
|---|---|---|
| hebel | 0,280 | irrelevant (belegt) |
| krypto | 0,600 | irrelevant |
| aktien / etf / rohstoffe | **0,233** | 300 EUR |
| | **0,200** | 400 EUR (Referenz) |
| | **0,140** | 1.000 EUR |
| | **0,120** | 2.000 EUR |
| hedge | 0,184 (10 T.) / **0,259** (180 T.) | 500 EUR |

### Vier Entscheidungen, jede begruendet

**1. Positionsgroesse je Signal statt eines Pauschalwerts.** Nutzer-Angabe:
aktuell 300-500 EUR, kuenftig eher 500-1.000. Statt eine Spanne zu waehlen wird
die **tatsaechliche** Groesse aus dem Signal genommen (`position_size_eur`),
Referenz 400 EUR nur wenn sie fehlt. Damit rechnet das System mit der echten
Praxis und waechst automatisch mit, ohne dass jemand eine Zahl nachzieht.

**2. Ein Satz je Klasse, nicht je Symbol.** Krypto kostet bei Bitpanda 0,99 %
(BTC) bis 2,49 % (Altcoins); angesetzt sind **1,5 % je Seite** als konservative
Mitte. Eine symbolgenaue Tabelle waere nicht pflegbar - genau der
Handhabbarkeits-Einwand des Nutzers.

> **ACHTUNG BEIM LESEN DER KENNZAHLEN:** Krypto steigt damit von 0,400 auf
> **0,600 R**. Der Netto-Erwartungswert der Krypto-Klassen faellt entsprechend
> um 0,2 R. Das ist keine Verschlechterung des Systems, sondern eine
> Korrektur der Annahme - aber jede Zahl vor dem 07.08. ist damit nicht mehr
> direkt vergleichbar.

**3. Laufende ETP-Gebuehr nur fuer Hedge.** Gehebelte ETPs tragen eine
Verwaltungsgebuehr (angesetzt 0,8 % p.a., geschaetzt und als unbelegt
markiert). Erst dadurch wird die Haltedauer einer Absicherung kostenwirksam -
vorher erschien eine ueber Monate gehaltene Absicherung so billig wie eine ueber
zehn Tage.

**4. Die Basislinie traegt dieselbe Positionsgroesse.** Sonst waere der
Vergleich schief: die Fixgebuehr haengt an der Ordergroesse, und eine Basislinie
mit anderer Groesse traegt eine andere Kostenlast.

### Abgrenzung, die leicht schiefgeht

Die Rohstoff-ETCs (OD7N/OD7H/OD7C/OD7L) sind **boersengehandelte ETCs**, nicht
Bitpanda Metals. Die Metals-Aufschlaege (Silber 2,5 % Kauf / 2,0 % Verkauf)
gelten fuer sie NICHT - wer das verwechselt, rechnet mit dem Dreifachen. Im Code
als Kommentar an `_KOSTEN_ART_JE_TIER` festgehalten.

### Was ehrlich bleibt

`belegt=True` gilt weiterhin **nur fuer Hebel** (an 104 echten Positionen
gemessen). Boerse und Krypto sind recherchiert, aber nicht an den eigenen Daten
verifiziert - der Spread steckt bei Bitpanda im Kurs und ist aus den
Transaktionsdaten allein nicht messbar (an 5.734 Trades geprueft: 0,000 %
Median). Die Messung gegen die eigene Kursreihe bleibt offen.

**19 Pruefungen** in `teste_kostenmodell_je_klasse.py`, alle bestanden; neun
Testsuiten und die Signaturpruefung gruen.

Quellen: Handelsblatt (Bitpanda-Gebuehren je Anlageklasse), Finanzfuchs
(Krypto-Spreads).


---

## Nachtrag (2026-08-07): manuelle Schwerpunkte mit garantiertem Raum - die Anforderung war umgekehrt, als ich sie verstanden hatte

Schritt 3 des Gesamtkonzepts. Nutzer-Sorge im Wortlaut:

> *"die Gewichtung war meine Befuerchtung, dass wenn z.B. ein Thema trendet,
> andere wichtige Bereiche keinen Raum bekommen, obwohl ich der Meinung bin,
> dass Energie aktuell unterbewertet ist und zukuenftig massiv steigen wird -
> und diese Trades vergessen werden bzw. untergehen."*

**Das dreht die Anforderung um.** Ich hatte den Fokus als "Trend verstaerken"
verstanden - gemeint ist das Gegenteil: **eine gesetzte Ueberzeugung muss sich
gegen einen Trend behaupten koennen.**

Fachlich ist das der staerkere Entwurf. Ein Mechanismus, der Aufmerksamkeit nach
TRENDSTAERKE verteilt, tut systematisch das Gegenteil dessen, was
antizyklisches Investieren braucht: ein Themenfeld ist oft gerade dann
interessant, WEIL niemand hinsieht. Ein Trendverstaerker haette genau die
Faelle ausgeblendet, die den Ertrag bringen sollen.

### Was gebaut wurde

**`schwerpunkte.manuell`** in `config.yaml` - eine Liste von
`"hauptgruppe"` oder `"hauptgruppe:unterkategorie"`. Ein Eintrag auf
Hauptgruppen-Ebene deckt alle ihre Unterkategorien ab.

**Wirkung in `_bestimme_gesperrte_fall_a_kandidaten()`:** gesetzte Schwerpunkte
werden VOR der Budget-Rechnung herausgenommen. Sie werden nie zurueckgestellt
und zaehlen auch nicht gegen das Budget der uebrigen Kandidaten - sonst wuerden
sie denselben Verdraengungswettbewerb nur von der anderen Seite fuehren.

**Schalter im Thesen-Tab** ("Schwerpunkt an/aus"), schreibt nach `config.yaml`
wie die uebrigen GUI-Schalter.

### Was ein Schwerpunkt ausdruecklich NICHT tut

**Er erfindet keine Richtung.** Ob die Pruefmechanismen eine Uebergewichtung
hergeben, entscheiden weiterhin die Daten. Ein Schwerpunkt sorgt dafuer, dass
ein Themenfeld Raum BEKOMMT - er ist eine **Aufmerksamkeits-Entscheidung, keine
Richtungsvorgabe**. Diese Trennung steht im Config-Kommentar, im Tooltip und im
Test (E1), weil sie sonst schleichend verwaessert.

Damit bleibt auch die Spezifikationsregel gewahrt, die eine Scoring-Gewichtung
fuer sentimentgetriebene Kategorien ausdruecklich verbietet
(`Kategorie_Basisinformationen_Release2.md` Abschnitt 5): ein Schwerpunkt wirkt
auf die REIHENFOLGE, nicht auf den Score. Der Nutzer hat diese Abgrenzung
ausdruecklich bestaetigt.

### Der Konfliktfall im Test

`teste_schwerpunkte.py` bildet genau die Sorge nach: fuenf reife Kandidaten,
Budget null, "energie" als gesetzter Schwerpunkt. Ergebnis: die vier
Wettbewerber werden zurueckgestellt, **Energie kommt durch**. Ohne gesetzten
Schwerpunkt bleibt das Verhalten unveraendert - das Feature ist opt-in und
aendert nichts, solange die Liste leer ist.

**16 Pruefungen**, alle bestanden; zehn Testsuiten und die Signaturpruefung
gruen.

## Nachtrag (2026-08-07): wartende Themen-Vorschlaege sichtbar gemacht - die Statusverteilung sagt nichts ueber den Vorlauf

### Der Anlass

Am 07.08. standen 14 von 16 Vorschlaegen auf `beobachtung`. Diese Zahl stand so
in der GUI, im Export und auf der Uebersichtsseite - und sie ist **fuer eine
Entscheidung wertlos**. Sie sagt nicht, ob ein Vorschlag seit gestern oder seit
dem 25.07. laeuft, und schon gar nicht, wann er reif wird.

Der Befund kam nur zustande, weil die Vorschlaege in dieser Session **von Hand
datiert** wurden. Dabei stellte sich heraus: der vermeintete "Themen-Deckel"
existierte nicht - die Kandidaten waren schlicht noch nicht reif. Ein Fund, der
sich beim Datieren in Luft aufloest, ist ein Hinweis darauf, dass die Datierung
fehlt, nicht der Deckel.

### Die zweite Zahl ist die wichtigere

Nicht "wie viele warten", sondern **wie viele am selben Tag reif werden**.
Uebersteigt diese Zahl das freie Budget, entscheidet die
Gleichzeitigkeits-Moderation, welche durchkommen. Am 24./25.08. betrifft das
neun Kandidaten - eine Entscheidung, die mit siebzehn Tagen Vorlauf fallen kann
oder unter Druck am Tag selbst. `engpass_am`/`engpass_anzahl` machen genau das
sichtbar, und die Seite faerbt die Zahl **nur dann rot, wenn sie das freie
Budget wirklich uebersteigt** - sonst ist sie eine harmlose Terminmeldung.

### Was gebaut wurde

**`agent/kategorie_vorschlaege.py::wartende_vorschlaege(conn, jetzt=None)`** -
reine Lesefunktion. Persistenzschwellen und Reife-Logik kommen aus **denselben**
Funktionen wie der Job selbst (`_persistenz_tage_fuer_mechanismen()`,
`db.get_kandidat_in_beobachtung()`). Eine zweite Fassung wuerde garantiert
auseinanderlaufen - das ist die Lehre vom 03.08.

**Klartext neben den IDs, nicht statt ihnen.** `kategorie_anzeige`,
`richtung_anzeige`, `mechanismus_anzeige` liefern "Technologie & KI /
Kuenstliche Intelligenz · Uebergewichten · Bellwether-Sentiment"; die stabilen
IDs stehen unveraendert daneben, weil eine Auswertung sie braucht. Die
Klartext-Tabellen liegen in `kategorie_vorschlaege.py` und nicht in der GUI:
Export, Seite und GUI sollen dieselben Woerter benutzen.

**Export** (`extract_notebook_diagnose.py`): neuer Abschnitt
`wartende_themen_vorschlaege` plus Konsolenzeile, fail-soft gekapselt, aber mit
sichtbarem `nicht_verfuegbar`-Feld statt stillem Verschwinden.

**Uebersichtsseite**: eigene Karte "Themen in Beobachtung - wann wird was reif?"
vor der Hedge-Karte, mit Liste nach Restzeit sortiert und ★ fuer gesetzte
Schwerpunkte.

### Nebenbefund: der Schwerpunkte-Tab war unbedienbar

Nutzer-Fund im selben Zug (Screenshot): *"den Bereich unten sieht bzw. bedient
man ohne Verschieben nicht vernuenftig"*. Zwei Ursachen, die sich addiert
haben - und die erste war seit dem 25.07. drin, also seit dem Fix, der genau
dieses Problem loesen sollte:

1. **Zwei Panes fuer drei Bereiche.** Vorschlaege UND Tages-Synthese lagen beide
   im unteren Frame, beide mit `expand=True`. Der zuletzt gepackte Block
   (Synthese) faellt dann unten aus dem Fenster.
2. **50/50 war die falsche Aufteilung.** Die Thesen-Liste bekam die halbe
   Fensterhoehe fuer typisch 5-8 Zeilen - oben zwoelf Zeilen Leere, unten
   abgeschnittene Tabellen. `height=18` hat diesen Hunger als Mindesthoehe
   zementiert.

Jetzt: drei eigene Panes mit eigenen Trennern, Startaufteilung 45/25/30, und
die `sashpos`-Setzung wartet, bis das Fenster wirklich Hoehe hat (beim ersten
`<Configure>` steht sie auf 1 - dann waeren beide Trenner auf 0 gelandet).
Gemessen gegen eine DB-Kopie: bei 1600x900 sind es 386/215/258 px, bei 1100x600
noch 251/140/168 px - alle drei Bereiche bedienbar.

### Und ein eigener Fehler, der eine Naht bekommen hat

Beim Verifizieren der Export-Erweiterung wurde `_google_drive_wurzel()`
umgelenkt - **wirkungslos**, weil `ZIEL_ORDNER` eine Modul-Konstante ist, die
schon beim Import feststeht. Der Testlauf hat damit den echten
`notebook_diagnose.json` im Austauschordner ueberschrieben.

Konsequenz: `TIT_EXPORT_ZIEL` als Umgebungsvariable, die **vor** der Konstanten
wirkt. Mit gesetzter Variable kann ein Testlauf den Austauschordner gar nicht
mehr erreichen. Eine Naht schlaegt eine Absichtserklaerung - dieselbe Logik wie
bei `db.DB_PATH`.

**`teste_wartende_vorschlaege.py`, 20 Pruefungen**, alle bestanden; elf
Testsuiten und die Signaturpruefung gruen. Die Karte wurde in beiden Zustaenden
im Browser gerendert (Engpass innerhalb des Budgets / darueber).

## Nachtrag (2026-08-07): Richtgroesse weich gemacht - die Spezifikation stand seit dem 25.07. auf dem Kopf

### Der Widerspruch

`Kategorie_Basisinformationen_Release2.md` Abschnitt 5, Punkt 3, im Wortlaut:

> **Richtgroesse:** 3-6 gleichzeitig aktive Thesen, weich in der GUI angezeigt,
> kein Hard-Limit im Code.

Implementiert war exakt das Gegenteil in **beiden** Halbsaetzen:

- **Im Code ein hartes Limit.** Wurde die Obergrenze erreicht, landeten reife
  Fall-A-Kandidaten als `offen` statt als These -
  `_bestimme_gesperrte_fall_a_kandidaten()` hat sie stumm zurueckgestellt.
- **In der GUI gar nicht angezeigt.** Die Zahl 6 stand nur in `config.yaml`.
- Die **Untergrenze 3 existierte ueberhaupt nicht** - obwohl sie derzeit die
  interessantere ist.

### Warum der Deckel weg kann, ohne dass etwas verwaessert

Das Hauptargument fuer die Begrenzung war, mehr Thesen wuerden die Rangfolge im
Screener verduennen. **Das traegt nicht:** eine aktive These bringt einem
Kandidaten keinen Bonus durch ihre blosse Existenz, sondern nur, wenn
`compute_these_abgleich()` sie objektiv als "gestuetzt"/"widerspricht"
bestaetigt (`agent/aktien/screener.py::_kategorie_score_bonus()`, so seit der
2026-07-21-Korrektur). Mehr Thesen erzeugen also nicht mehr Bonus, sondern nur
mehr Kandidaten fuer denselben objektiven Test.

### Was der Deckel stattdessen getan hat

Er hat eine Schieflage **stabilisiert statt sie zu zeigen**. Sechs aktive
Thesen klingen nach "voll" - tatsaechlich sind vier davon Rohstoffe, zwei
stehen auf `neutral`, und ausserhalb der Rohstoffe traegt praktisch kein
Themenfeld eine These. `richtgroessen_lage()` liefert deshalb nicht nur die
Zahl, sondern auch **die Verteilung**: `hauptgruppen_abgedeckt` und
`davon_neutral`. Sechs Thesen auf fuenf Hauptgruppen sind etwas anderes als
sechs auf zwei.

### Was bleibt: ein Qualitaets-, kein Mengenkriterium

Zurueckgestellt wird nur noch, wenn ein Themenfeld **gar kein handelbares Asset**
hat (G-5) - dann koennte eine These darauf nichts ausloesen.

**Vor dem Bauen gemessen, und die Messung hat die Umsetzung geaendert:**

| Pruefung | Ergebnis |
|---|---|
| Unterkategorien mit Katalog-Symbolen | 70 von 72 |
| Ohne Katalog-Symbole | `absicherung/aktienmarkt_short`, `absicherung/sektor_short` |
| Diese beiden ueber die Watchlist abgedeckt | ja - DBPK und 3QSS |
| Unterkategorien ohne JEDES handelbare Asset | **0** |
| Nicht-Krypto-Watchlist mit Kategorie | 13 von 13 |

Zwei Konsequenzen daraus:

1. **Eine Pruefung nur ueber den Katalog haette ausgerechnet die beiden
   Hedge-Kategorien gesperrt**, die der Nutzer aktiv haelt.
   `kategorie_handelbare_assets()` liest deshalb Katalog **und** Watchlist.
2. **G-5 feuert heute bei keiner einzigen Kategorie.** Es ist ein Wachhund fuer
   neu angelegte Kategorien, kein Filter fuer den Bestand. Das steht so im
   Code-Kommentar, damit niemand spaeter eine Wirkung vermutet, die es nicht
   gibt.

Die 44 Krypto-Assets ohne Kategorie sind **kein** Befund: die Taxonomie ist
bewusst fuer Nicht-Krypto gebaut, Krypto laeuft ueber die Watchlist-Mechanik.

### Nebenwirkung auf Schritt 3, offen benannt

Die manuellen Schwerpunkte schuetzten bisher davor, in der
Gleichzeitigkeits-Moderation verdraengt zu werden. **Diese Schutzwirkung ist
jetzt gegenstandslos** - es gibt nichts mehr, wovor zu schuetzen waere. Der
Schalter, die Konfiguration und die ★-Markierung bleiben und sind der Eingang
fuer **Schritt 6 (Allocator-Prioritaet)**, wo der Schwerpunkt tatsaechlich
greifen wird. Der Plan hatte diese Abhaengigkeit bereits so notiert.

### Tests

`teste_richtgroesse_weich.py`, **26 Pruefungen**. Der wichtigste ist B2/C1:
neun reife Kandidaten bei sechs aktiven Thesen, nichts wird zurueckgestellt -
**und die siebte These entsteht auch wirklich**. Getestet wird die aufrufende
Funktion `_verarbeite_signal()`, nicht nur der Helfer: dass die Sperrmenge leer
ist, nuetzt nichts, wenn die Anlage trotzdem ausbleibt (Lehre vom 02.08.,
Stop-Regelfamilie). Zwoelf Testsuiten und die Signaturpruefung gruen.

49 Zeilen toter Code (Budget-Rechnung, Schicht-2-Sortierung fuer die Sperre)
entfernt statt auskommentiert.

## Nachtrag (2026-08-07): Erfolgsmaß je Themenfeld - die geplante Kennzahl waere eine leere Tabelle gewesen

### Die Messung vor dem ersten Zeilencode

Geplant war "Systemguete zusaetzlich nach Hauptgruppe" (G-2). Am
Notebook-Export vom 07.08. nachgezaehlt:

| | Signale | davon aufgeloest |
|---|---|---|
| Spot | 2795 | 10 |
| Hebel | 1759 | 91 |

**Von diesen 101 aufgeloesten gehoert kein einziges zu einem Themenfeld.** Das
ist kein Datenloch, sondern Konstruktion: die Themen-Taxonomie ist bewusst fuer
Nicht-Krypto gebaut, und Nicht-Krypto hat bisher keine aufgeloesten Signale
hervorgebracht - genau das ist ja der offene Befund "alle Nicht-Krypto-Signale
sagen HALTEN".

Eine Systemguete je Hauptgruppe waere heute also eine Tabelle aus leeren Zellen
und wuerde dabei aussehen wie ein funktionierendes Instrument. **Das ist
schlimmer als keine Zahl.**

### Was stattdessen gemessen wird

Eine These ist keine Trade-Folge, sondern eine **Richtungsaussage auf einen
Korb**. SQN und Expectancy sind dafuer derselbe Kategorienfehler wie beim Hedge
(`compute_hedge_wirksamkeit()`, W1 heute frueh): Kennzahlen, die eine andere
Frage beantworten als die gestellte. `agent/themenfeld_erfolg.py` misst deshalb
zwei Dinge:

1. **Traf die Richtung?** Gleichgewichtete Korbrendite der Kategorie seit
   `gesetzt_am` gegen die aller uebrigen Themen-Assets. Der Vergleichskorb ist
   nicht schmueckendes Beiwerk: "uebergewichten" ist eine RELATIVE Aussage -
   ohne Gegenueber misst man den Gesamtmarkt und nennt es Themenwahl.
2. **Kam die These ueberhaupt bei einem Asset an?** Assets gesamt, davon mit
   Kursreihe, davon mit Signal. Das macht die eigentliche Engstelle sichtbar,
   statt sie zu verdecken - bei Energie sind es **2 von 22**.

### Die Absicherung fehlt bewusst

Ein Hedge, der verliert waehrend das Portfolio steigt, hat funktioniert. Eine
Ueberrendite-Messung wuerde ihn systematisch als Fehlschlag ausweisen. Statt
einer falschen Zahl steht dort ein Verweis auf `compute_hedge_wirksamkeit()` -
dieselbe Abgrenzung wie am Vormittag, diesmal von der anderen Seite.

### Drei Dinge, die kein Urteil bekommen

- **`neutral`** trifft keine Richtungsaussage. Die Zahl steht da, ein Treffer
  waere eine erfundene Aussage.
- **Unter `SCHWELLE_TREFFER_PROZENT` (2,0 pp)** heisst "unentschieden". Bei
  einem Korb aus ein bis drei Werten ist ein halber Prozentpunkt kein Signal.
- **Unter `MIN_TAGE_FUER_URTEIL` (10 Tage)** gibt es kein Urteil - darunter
  misst man Tagesrauschen und nennt es Treffer.

### Welcher Korb fehlt, muss dastehen

Erster Entwurf meldete pauschal "zu wenige Kurspunkte". Das laesst offen, ob
die Kategorie oder der Vergleichsmassstab leer ist - und das sind voellig
verschiedene Probleme: das eine betrifft eine Kategorie, das andere blockiert
JEDE Themenfeld-Messung. Die Meldung unterscheidet jetzt drei Faelle, und die
spezifischere Pruefung ("kein Asset hat ueberhaupt eine Kursreihe") greift
zuerst.

Beim Rauchtest gegen die Entwicklungskopie hat genau das getragen: dort sind
**null** Symbole mit USD-Kurspunkten im Fenster - die Meldung sagt das jetzt,
statt es einer Kategorie anzulasten.

### Tests

`teste_themenfeld_erfolg.py`, **30 Pruefungen**. Die Kursreihen sind
**simuliert**, nicht abgewartet: ohne sie liesse sich nur der
Nicht-Messbar-Zweig testen, und genau das waere der Fehler, den die stehende
Vorgabe verbietet. Abgedeckt sind Treffer, Fehlschlag, `meiden` als
Richtungsumkehr, `unentschieden`, `neutral` ohne Urteil, zu junge These,
Absicherungs-Ausnahme, Wirkungskette und alle drei Diagnose-Zweige.
Dreizehn Testsuiten und die Signaturpruefung gruen.

### Offene Befunde aus Log und Export vom 07.08. (nicht in diesem Commit)

| | Befund | Einordnung |
|---|---|---|
| A | **OD7C und OD7H: 0 von 91 Tagen bewertet**, `letzter_kurs_eur` leer | Die Rekonstruktion vom Vormittag lief fuer diese beiden nie. OD7L/OD7N/PLTR/VST haben 60 Tage ueber FX. |
| B | FX-Ableitung: **1 Tag** verworfen (06.08., IQR 2,2 % vs. Grenze 2 %), aber **dutzendfach geloggt** | Log-Defekt, kein Datenfehler. In diesem Takt ersaeuft jeder echte Fund. |
| C | `mistral: 402 Payment Required` -> Synthese lief ueber Gemini | Kette hat gegriffen (19 Kategorien), Mistral als Erstanbieter derzeit tot. |
| D | CoinGecko `ConnectTimeout`, `refresh_prices_job` einmal fehlgeschlagen | Erklaert die "1 Tag ohne Kurs" bei allen Krypto-Werten. Kein Handlungsbedarf. |

Die "30 von 33 Symbolen ohne Kurs" aus der Bewertungs-Diagnose sind **kein**
Befund: gezaehlt werden Symbole mit mindestens EINEM fehlenden Tag im
91-Tage-Fenster - bei Boersenwerten sind das die Wochenenden.
