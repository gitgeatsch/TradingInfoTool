# TradingInfoTool — Spezifikation (fachliche Grundlage)

> **Eigentümer:** Gernot Spiessmaier · **Version:** 0.1 · **Stand:** 2026-06-30
>
> Dieses Dokument beschreibt **was** das Tool leisten soll und **warum** (lesbarer Teil).
> Die konkreten, vom Programm auslesbaren **Parameter** (Watchlist, Risiko-Limits,
> Strategien, Indikatoren, Datenquellen) liegen in [`config.yaml`](config.yaml).
> So gibt es für jeden Wert nur **eine** Quelle der Wahrheit.
>
> **Legende:** `[OFFEN]` = noch zu entscheiden (siehe Kapitel 13).
> Technik/Projektstruktur stehen in `CLAUDE.md` im Projektroot.

---

## 1. Vision & übergeordnetes Ziel

Trotz angespannter Finanzlage und künftiger Krisen mit dem TradingInfoTool einen
hohen Gewinn erzielen und Verluste vermeiden — sinnvoll investieren. Da die
investierten Summen nicht hoch sind, ist **Risikomanagement übergeordnet** für die
Zielerreichung. Es soll **keine pauschale** Bewertung sein, sondern detailliert je
**Assetklasse und Einzelwert** angewendet werden.

Messbare Zielgrößen (Werte in `config.yaml → ziele`):
- **Z-1** Kapitalerhalt hat immer Vorrang vor Gewinnmaximierung.
- **Z-2** Mindest-Chance-Risiko-Verhältnis (CRV) vor jedem Kaufsignal.
- **Z-3** Maximal akzeptierter Gesamt-Drawdown → bei Überschreitung Kapitalschutz-Modus.
- **Z-4** Jede Empfehlung ist nachvollziehbar (Begründung + Datenbasis + Konfidenz).

## 2. Leitprinzipien des Agenten

- Der Agent ist Trading-Experte und nutzt Fibonacci, Retracements, wichtige
  Indikatoren etc.
- Jede Empfehlung kommt mit **kurzer UND langer Begründung**.
- **P-1** Risikomanagement zuerst: Signal erst gegen Risiko, dann gegen Chance prüfen.
- **P-2** Transparenz: genutzte Indikatoren/Quellen + Konfidenz (0–100 %) nennen.
- **P-3** Kein Overtrading: „Halten/Abwarten" ist eine gültige Empfehlung.
- **P-4** Konsistenz mit gewählter Strategie und Haltedauer-Logik.
- **P-5** Einheitliches Ausgabeformat je Empfehlung:
  - Asset & Aktion (KAUFEN / VERKAUFEN / HALTEN / NACHKAUFEN)
  - Kurzbegründung (1–2 Sätze) + Langbegründung (technisch + fundamental + Makro)
  - Empfohlene Positionsgröße / Stückzahl
  - Einstieg / Stop-Loss / Take-Profit
  - Empfohlene Haltedauer + Begründung
  - Konfidenz in % und wichtigste Risiken/Gegenargumente

## 3. Risikomanagement (Kernmodul — höchste Priorität)

Werte in `config.yaml → risiko`. In der UI pro Nutzer einstellbar.

**Money-Management:** Risiko pro Trade (RM-1), max. Allokation pro Einzelwert (RM-2)
und pro Assetklasse (RM-3, detailliert statt pauschal), Cash-Reserve (RM-4).

**Verlustbegrenzung:** Pflicht-Stop-Loss (RM-5), Trailing-Stop (RM-6),
Portfolio-Notbremse bei Drawdown-Limit Z-3 (RM-7).

**Asset-spezifische Bewertung:** Risiko-Score je Asset aus Volatilität, Liquidität/
Marktkapitalisierung, Korrelation zu BTC, Projektreife (RM-8). Höheres Risiko →
kleinere erlaubte Position (RM-9).

**Hebel:** nur Long, kein Short (RM-10). Hebelhöhe gedeckelt und an Volatilität
gekoppelt; Liquidationspreis stets ausweisen, Sicherheitsabstand zum Stop-Loss (RM-11).

## 4. Assets & Diversifikation

Watchlist in `config.yaml → watchlist` (BTC, ETH, SOL, TAO, LINK, CANTON, MORPHO).

- **A-1** Jedes Asset hat einen Typ: `core` (langfristig) vs. `taktisch` (kürzer).
- **A-2** Klumpenrisiko vermeiden: Viele Altcoins korrelieren stark mit BTC — das ist
  **keine** echte Diversifikation und fließt in den Risiko-Score ein.
- **A-3** Watchlist ist in der UI pflegbar; Datenanbindung automatisch, falls verfügbar.

## 5. Agent-Logik & Entscheidungsgrundlagen

Zeithorizonte und Gewichtung in `config.yaml → agent`.

Entscheidungs-Pipeline (Reihenfolge je Analyse):
1. **R-5.1** Marktregime bestimmen (Bulle/Bär/Seitwärts) via BTC-Trend, BTC-Dominanz,
   Fear & Greed.
2. **R-5.2** Makro-Kontext: Leitzinsen, Risikoumfeld USA/Japan/China/EU/Korea.
3. **R-5.3** Technische Analyse je Asset: Trend, Indikatoren (Kap. 7), Fibonacci,
   Support/Resistance.
4. **R-5.4** Sentiment (X/YouTube) — nur Zusatz, niedrig gewichtet, nur seriöse Quellen.
5. **R-5.5** Risikoprüfung (Kap. 3) als **VETO-Stufe**: scheitert hier → kein Kauf.
6. **R-5.6** Signal + Konfidenz + vollständige Empfehlung (Format P-5).
7. **R-5.7** Haltedauer-Empfehlung (kurz/mittel/lang) mit Begründung; Nutzer kann eigene
   Parameter ergänzen (interaktiver Dialog), die in die nächste Bewertung einfließen.
8. **R-5.8** Forecast als Szenario (Bull/Base/Bear) mit Wahrscheinlichkeiten, statt
   einzelner Punktprognose.

## 6. Strategie-Katalog (auswählbar je Asset)

Katalog in `config.yaml → strategien`. Pro Asset wählbar; der Agent schlägt die zum
Marktregime passende Strategie vor und begründet die Auswahl („beste Strategie jetzt").

| ID | Strategie | Kern |
|----|-----------|------|
| S-1 | HODL / Core | langfristig halten, an Leveln nachkaufen |
| S-2 | DCA | regelmäßige Käufe unabhängig vom Preis |
| S-3 | Swing-Trading | Ein-/Ausstieg an Leveln & Fibonacci |
| S-4 | Trendfolge | Einstieg bei bestätigtem Trend, Trailing-Stop |
| S-5 | Kapitalschutz | defensiv, hohe Cash-Quote (auto bei Drawdown) |
| S-6 | Hebel-Long | nur geeignete Assets, nur Long (vorerst aus) |

## 7. Technische Indikatoren (Mindestumfang)

Liste in `config.yaml → indikatoren`. Kein Signal aus einem einzelnen Indikator —
**Bestätigung durch mehrere (Confluence)** ist Voraussetzung.

- Trend: EMA (20/50/200), MACD
- Momentum: RSI (Überkauft/Überverkauft, Divergenzen)
- Volatilität: Bollinger Bands, ATR (Stop-Loss-Abstand)
- Levels: Fibonacci, Support/Resistance, Swing-Highs/-Lows
- Volumen: Bestätigung von Ausbrüchen
- Marktbreite: BTC-Dominanz, Fear & Greed Index

## 8. Datenquellen

Konfiguration in `config.yaml → datenquellen`.

- **Marktdaten (Pflicht):** CoinGecko (Free Tier, max. 30 Req/Min → Caching/Scheduler).
- **Historische Daten:** für TA und Backtesting (Kap. 11).
- **Makro:** Leitzinsen (Fed, EZB, BoJ, PBoC, BoK), Leitbörsen USA/Japan/China/EU/Korea,
  BTC-Dominanz, Fear & Greed. `[OFFEN]` konkrete kostenlose APIs.
- **Sentiment (niedrig gewichtet):** X/Twitter (kuratierte Whitelist) und YouTube
  (ausgewählte Kanäle). `[OFFEN]` API-Kosten/ToS/Machbarkeit, spätere Phase. Sentiment
  **nie** als alleiniger Signalgeber.

## 9. Funktionen in der Oberfläche (UI)

Start mit Kryptowährungen, später erweiterbar auf Aktien, ETF, Rohstoffe.

- **U-1** Dashboard: Portfolio-Wert, P&L, Drawdown, Cash-Quote, Marktregime-Ampel.
- **U-2** Watchlist mit Live-Preisen + Asset-Risiko-Score.
- **U-3** Chart-Ansicht je Asset mit Indikatoren + Forecast-Szenario.
- **U-4** Signal-/Empfehlungsansicht im Format P-5 (kurz + lang).
- **U-5** Strategie-Auswahl je Asset + Vorschlag „beste Strategie jetzt".
- **U-6** Portfolio-Verwaltung: Bestände eintragen, Signale zuordnen.
- **U-7** Einstellungen: Risikoparameter (Kap. 3) pro Nutzer anpassbar.
- **U-8** Desktop-Benachrichtigungen bei neuen Signalen.
- **U-9** Interaktiver Dialog: Nutzer ergänzt Bewertungsparameter (R-5.7).

## 10. Agent- & Datenbank-Betrieb

- **B-1** Hintergrund-Scheduler (APScheduler) holt periodisch Marktdaten, respektiert
  das CoinGecko-Rate-Limit (Caching in SQLite).
- **B-2** Persistenz: Preise, Indikatoren, Signale, Portfolio, Strategien, Nutzer-
  Parameter und Agent-Begründungen in SQLite (Historie & Nachvollziehbarkeit).
- **B-3** Agent läuft auch ohne offene UI (Hintergrundanalyse); beim UI-Start Abgleich
  mit dem letzten DB-Stand.
- **B-4** Claude API-Key in lokaler `.env` (niemals committen).

## 11. Roadmap & Erweiterbarkeit

1. **Phase 1** Grundgerüst (Struktur, SQLite, CoinGecko, Basis-UI, Watchlist).
2. **Phase 2** Marktdaten & Charts (Indikatoren Kap. 7, Visualisierung).
3. **Phase 3** KI-Agent (Claude API, Pipeline Kap. 5, Risikomodul Kap. 3, Strategien, Makro).
4. **Phase 4** Portfolio, Benachrichtigungen, Sentiment (X/YouTube).
5. **Phase 5** Backtesting der Strategien gegen historische Daten.
6. **Phase 6** Erweiterung auf Aktien / ETF / Rohstoffe (neue Datenquellen).

> Architektur: Datenquellen, Indikatoren und Strategien als austauschbare Module
> (Plug-in-Prinzip) anlegen, damit Erweiterungen ohne Kern-Umbau möglich sind.

## 12. Rechtlicher Hinweis

Das Tool dient der privaten Information und Entscheidungsunterstützung und stellt
**KEINE Anlageberatung** dar. Empfehlungen sind algorithmisch/KI-generiert und können
fehlerhaft sein. Trading birgt Verlustrisiken (Hebel: Totalverlust möglich). Die letzte
Entscheidung und Verantwortung liegen beim Nutzer. Dieser Hinweis sollte in der UI
sichtbar sein.

## 13. Offene Punkte / zu entscheiden

- Maximaler tolerierter Gesamt-Drawdown (Z-3)? Vorschlag −15 %.
- Max. Allokation pro Einzelwert (RM-2) und pro Assetklasse (RM-3)?
- Verfügbarkeit/CoinGecko-ID von „Canton".
- Konkrete kostenlose APIs für Makro-/Zinsdaten.
- X-API & YouTube-API: Kosten, Limits, ToS, Umsetzungsphase.
- Standard-Timeframes für die technische Analyse.
- Claude-Modellversion und Budget/Token.
