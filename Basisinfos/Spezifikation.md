# TradingInfoTool — Spezifikation (fachliche Grundlage)

> **Eigentümer:** Gernot Spiessmaier · **Version:** 1.1 · **Stand:** 2026-07-06
>
> Dieses Dokument beschreibt **was** das Tool leisten soll und **warum** (lesbarer Teil).
> Die konkreten, vom Programm auslesbaren **Parameter** (Watchlist, Risiko-Limits,
> Strategien, Indikatoren, Datenquellen) liegen in [`config.yaml`](config.yaml).
> So gibt es für jeden Wert nur **eine** Quelle der Wahrheit.
>
> **Legende:** `[OFFEN]` = noch zu entscheiden (siehe Kapitel 16).
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
  - Asset & Aktion (KAUFEN / VERKAUFEN / TAUSCHEN / HALTEN / NACHKAUFEN)
  - Kurzbegründung (1–2 Sätze) + Langbegründung (technisch + fundamental + Makro)
  - Empfohlene Positionsgröße / Stückzahl
  - Einstieg / Stop-Loss / Take-Profit — **jeweils in USD und EUR** (siehe P-9)
  - Empfohlene Haltedauer + Begründung
  - Konfidenz in % und wichtigste Risiken/Gegenargumente
- **P-6** Steuerliche Einordnung (Österreich): Ein Tausch Krypto-zu-Krypto (auch in
  Stablecoins) ist nach aktueller Rechtslage bis zur Auszahlung in Fiat steuerlich
  neutral — es fallen nur Transaktionskosten an, keine Steuer. Erst die Auszahlung
  („Realisierung" in Fiat bzw. Nutzung für Waren/Dienstleistungen) ist steuerrelevant.
  Deshalb unterscheidet das Ausgabeformat TAUSCHEN von VERKAUFEN, und der Agent soll
  bei gleichwertigen Alternativen den steuerlich günstigeren Weg vorschlagen (siehe
  R-5.9). `[OFFEN]` mit Steuerberater gegenprüfen (Details wie Spekulationsfrist bei
  Altvermögen, Besteuerung von Staking-Erträgen als laufende Einkünfte).
- **P-7** Advisory-only — **keine autonome Orderausführung.** Der Agent analysiert,
  bewertet, pflegt Watchlist/DB und erzeugt **Empfehlungen** samt Benachrichtigungen.
  Er platziert **niemals** Orders, führt keine Trades aus und bewegt kein Kapital; die
  Ausführung erfolgt stets manuell durch den Nutzer. Alle Aktionen in P-5 (KAUFEN,
  VERKAUFEN, …) sind Vorschläge. **Konsequenz:** Schutzmechanismen (Stop-Loss RM-5,
  Drawdown-Notbremse Z-3/RM-7) wirken als **dringende Alerts**, nicht als automatische
  Ausführung — der Agent eskaliert (z. B. hochpriore E-Mail + auffällige UI-Warnung),
  die Auslösung liegt beim Nutzer. Nebeneffekt: Das System benötigt **keinen
  Börsen-API-Schlüssel mit Handelsrecht** (Preise via CoinGecko, Bestände via
  Import/GUI). Deckt sich mit Kap. 12.
- **P-8** Lokale Autonomie — der Agent muss perspektivisch **vollständig eigenständig
  mit lokaler Intelligenz** funktionieren können (Hybrid-Architektur aus Decision-Trees,
  Fuzzy Logic und lokalem ML, siehe `Agent_Architecture_Analysis_2026-07-02.html`). Die
  Claude API ist eine **optionale Erweiterung** (Meta-Analyse, strategische Overrides,
  Nutzer-Dialog) — **keine Voraussetzung** für den Betrieb. Konsequenz: Kernfunktionen
  (Datenabruf, Persistenz, Basis-UI) dürfen zu keinem Zeitpunkt zwingend von einem
  Claude-API-Schlüssel abhängen; die Anbindung wird erst dann verdrahtet, wenn eine
  Phase sie tatsächlich aktiv nutzt.
  **Klarstellung (2026-07-06):** Betrifft ausschließlich den Claude/Anthropic-Key.
  `.env`-Loading wurde in Phase 2 eingeführt, aber nur für einen optionalen
  `COINGECKO_API_KEY` (siehe Kap. 8) — CoinGecko bleibt reine Marktdaten-Anbindung,
  hat nichts mit der KI-Autonomie-Frage zu tun. `ANTHROPIC_API_KEY`/`GITHUB_TOKEN`
  bleiben weiterhin ungenutzt bis zur jeweils benötigten Phase.
- **P-10** Fail-Loud statt Fail-Silent bei Datenproblemen — Ausfälle, fehlende oder
  veraltete Daten (z. B. CoinGecko nicht erreichbar, Preis-Cache veraltet, zu wenig
  Historie für einen Indikator) dürfen **niemals** zu stillschweigend falschen oder
  unvollständigen Analysen/Signalen führen. Gilt **einheitlich für alle Bereiche**:
  Datenabruf, Persistenz, UI-Anzeige und (ab Phase 3) die Agent-Pipeline. Konkret:
  - Jeder Wert, der auf veralteten/fehlenden Daten beruht, wird **sichtbar als solcher
    gekennzeichnet** (nicht einfach der letzte bekannte Wert kommentarlos angezeigt).
  - Reicht die Datenlage für eine Berechnung nicht aus (z. B. zu wenig Historie für
    EMA-200), wird **„nicht verfügbar"** angezeigt statt eines aus unzureichenden Daten
    berechneten (potenziell irreführenden) Werts.
  - Ab Phase 3: ein **Datenqualitäts-Gate** läuft in der Pipeline (Kap. 5) **vor** R-5.1
    — bei unzureichender Datenlage für ein Asset wird kein Signal erzeugt, sondern
    „HALTEN — Datenlage unsicher" mit Begründung ausgegeben (siehe R-5.0). Ergänzt die
    bestehende Risiko-VETO-Stufe (R-5.5), ersetzt sie nicht.
  - Jeder Ausfall/jede Degradation wird geloggt (Nachvollziehbarkeit, Z-4).
  - Exakte Schwellenwerte (ab wann „veraltet"/„zu wenig Historie") sind `[OFFEN]`
    (Kap. 16) und pro Datenart/Indikator festzulegen.
- **P-9** Referenzwährung Euro + durchgängige USD/EUR-Doppelanzeige — der Nutzer hält
  Bestände und denkt in **Euro**. Alle aktuellen bzw. veränderlichen Geldwertangaben
  (Live-Preise, Portfolio-Wert, P&L) werden **immer gemeinsam in USD und EUR**
  dargestellt, nicht nur in einer Währung. Gilt ausdrücklich auch für
  Empfehlungen/Signale (siehe P-5: Einstieg/Stop-Loss/Take-Profit/Positionsgröße in
  beiden Währungen). CoinGecko liefert beide Währungen direkt mit (kein zusätzlicher
  Umrechnungsschritt/Wechselkurs-Risiko nötig).

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

Watchlist in `config.yaml → watchlist`. Quelle: `Basisinfos/Assets.xlsx` (Erstimport
Stand 2026-07-01, 41 Assets — eigene Bestände und reine Beobachtungswerte).

- **A-1** Jedes Asset hat einen Typ: `core` (langfristig), `taktisch` (kürzer) oder
  `stablecoin` (Cash-/Swap-Reserve, siehe A-4, kein eigenständiges Handelssignal).
- **A-2** Klumpenrisiko vermeiden: Viele Altcoins korrelieren stark mit BTC — das ist
  **keine** echte Diversifikation und fließt in den Risiko-Score ein.
- **A-3** Watchlist ist in der UI pflegbar; Datenanbindung automatisch, falls verfügbar.
- **A-4** Jedes Asset hat einen Status: `aktiv` (Bestand vorhanden) oder `watchlist`
  (reine Beobachtung, potenzielle künftige Position, noch kein Kauf). Die konkrete
  Bestandsmenge wird nicht in `config.yaml` gepflegt, sondern in der Datenbank
  (siehe Kap. 10, B-5).
- **A-5** Stablecoins (aktuell EURCV) zählen zur Cash-Reserve (RM-4) und dienen dem
  Agenten als Ziel-/Zwischenstation für steuerneutrale Swaps (siehe P-6, R-5.9)
  sowie als Kapitalschutz-Parkplatz (S-5).

## 5. Agent-Logik & Entscheidungsgrundlagen

Zeithorizonte und Gewichtung in `config.yaml → agent`.

Entscheidungs-Pipeline (Reihenfolge je Analyse):
0. **R-5.0** Datenqualitäts-Gate (P-10, VOR allem anderen): Sind die für dieses Asset
   benötigten Daten aktuell und vollständig genug? Wenn nein → Abbruch für dieses Asset,
   Ausgabe „HALTEN — Datenlage unsicher" mit konkretem Grund (z. B. „Preis seit X Min.
   nicht aktualisiert", „nur Y Tage Historie, benötigt Z"), kein Rateversuch mit
   Lückendaten.
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
9. **R-5.9** Steuerliche Optimierung (AT, siehe P-6): Bei strategisch gleichwertigen
   Alternativen bevorzugt TAUSCHEN (Krypto-zu-Krypto/Stablecoin) statt VERKAUFEN
   vorschlagen, da steuerlich neutral bis zur Auszahlung in Fiat.
10. **R-5.10** Regime-Profil anwenden (Kap. 14): Das in R-5.1/R-5.2 bestimmte Regime
    moduliert Gewichte, Schwellen, Small-Cap-Budget und Mindest-Konfidenz; Overrides
    nach der Governance-Regel (Sicherheits-Asymmetrie, harte Limits unantastbar).
11. **R-5.11** Bei Kauf-/Nachkauf-Empfehlungen antizyklische Disziplin (Kap. 15):
    Flush vs. fundamentaler Zusammenbruch klassifizieren, Bestätigungs-Gate, gestaffelt.

> **Separater Job — Marktscan (Kap. 13):** Die Entdeckung *neuer* Assets läuft nicht
> in dieser Pro-Asset-Pipeline, sondern als periodischer Hintergrund-Scan (2× täglich).
> Treffer werden automatisch als `status: watchlist` aufgenommen und durchlaufen danach
> dieselbe Pipeline wie bestehende Watchlist-Assets.

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

**Datenqualität (P-10):** Reicht die vorhandene Historie für einen Indikator nicht aus
(z. B. Asset erst seit 50 Tagen gelistet, EMA-200 braucht 200 Tage), wird dieser
Indikator als **„nicht verfügbar"** markiert statt mit einem verkürzten/falschen Fenster
berechnet. Confluence-Bewertung berücksichtigt nur tatsächlich verfügbare Indikatoren.

- Trend: EMA (20/50/200), MACD
- Momentum: RSI (Überkauft/Überverkauft, Divergenzen)
- Volatilität: Bollinger Bands, ATR (Stop-Loss-Abstand)
- Levels: Fibonacci, Support/Resistance, Swing-Highs/-Lows
- Volumen: Bestätigung von Ausbrüchen
- Marktbreite: BTC-Dominanz, Fear & Greed Index

## 8. Datenquellen

Konfiguration in `config.yaml → datenquellen`.

**Datenqualität (P-10):** Jede hier genannte Quelle kann ausfallen oder veraltete Daten
liefern (Rate-Limit, Netzwerk, Wartung). Bei Ausfall: letzter bekannter Wert bleibt in
der DB, wird in der UI aber mit **Alter/Zeitstempel sichtbar** dargestellt, nicht
kommentarlos als aktuell präsentiert. Exakte „veraltet ab wann"-Schwellen je Datenart
sind `[OFFEN]` (Kap. 16).

**Prinzip zur Quellenwahl (2026-07-06):** CoinGecko deckt bewusst nur Krypto-
Marktdaten ab. Zwei Fälle sind zu unterscheiden: (1) Wird für eine **tatsächlich
erforderliche** Funktionalität eine Datenart benötigt, die CoinGecko grundsätzlich
nicht liefert (z. B. Makro-/Zinsdaten, Sentiment, Funding-Rates) → gezielt eine
passende zusätzliche Quelle recherchieren, nicht versuchen, es mit CoinGecko zu
erzwingen. (2) Liefert CoinGecko eine Datenart nur eingeschränkt, aber die
Einschränkung blockiert **keine** tatsächlich erforderliche Funktionalität (z. B. echtes
Tages-OHLC für ATR — Phase 2 zeigt nur an, entscheidet noch nichts) → eine transparent
gekennzeichnete Näherung bevorzugen statt vorschnell eine zweite Quelle einzubauen
(siehe P-10-Entscheidung zu ATR/Swing-Highs-Lows). Sobald eine Phase tatsächlich
Entscheidungen/Signale auf einer nur genäherten Datenart aufbauen will, ist die
Näherung an dieser Stelle neu zu bewerten.

- **Marktdaten (Pflicht):** CoinGecko. **ERLEDIGT (2026-07-06):** Anonymer Zugriff
  (30 Req/Min) erwies sich als unzuverlässig — bei intensiverer Nutzung verhängt
  CoinGecko längere Sperren, als das dokumentierte Limit vermuten lässt. Optionaler
  kostenloser **Demo-API-Key** (100 Req/Min, stabiler) via `COINGECKO_API_KEY` in
  `.env` eingebaut — App funktioniert weiterhin auch ohne Key (Fallback auf 30 Req/Min),
  ein Key wird aber empfohlen. Kein Widerspruch zu P-8 (betrifft nur Claude/Anthropic).
  **Wichtige Ergänzung:** Der Demo-Key erhöht nur das Minuten-Limit — das
  **Monats-Kontingent bleibt bei 10.000 Calls, mit oder ohne Key**. Ursprünglich
  geplanter 5-Min-Live-Preis-Takt hätte zusammen mit dem täglichen Historie-Refresh
  (41 Assets × 2 Währungen) ca. 11.100 Calls/Monat verbraucht — über dem Limit.
  Deshalb Live-Preis-Takt auf **15 Min** reduziert (`scheduler/background.py`,
  `REFRESH_INTERVAL_MINUTES`) → ca. 5.340 Calls/Monat, mit Puffer für Erstimport/
  manuelle Aktualisierungen. Staleness-Schwelle entsprechend auf 30 Min angepasst
  (weiterhin 2× Scheduler-Takt, siehe `ui/formatting.py`).
- **Historische Daten:** für TA und Backtesting (Kap. 11). Grundsatz: Historie wiederholt
  sich nicht 1:1, ähnelt sich aber oft — Muster aus der Vergangenheit sollen daher (ab
  Phase 3, Agent-Logik) als Vergleichsbasis einfließen, nicht nur aktuelle Werte isoliert
  betrachtet werden.
  **Klarstellung 365-Tage-Grenze (2026-07-06):** Gilt gleichermaßen für Charts UND für
  die Daten, die der Agent (Phase 3) nutzen wird — beide greifen auf dieselbe
  `price_history`-Tabelle zu, gespeist vom selben CoinGecko-Endpunkt mit derselben
  Grenze. Kein separater, "besserer" Datentopf für den Agenten. Ist aber **kein**
  festes Dauerlimit: Der tägliche Historie-Job löscht nie alte Tage, die DB wächst mit
  der Zeit über ein Jahr hinaus, solange die App läuft. Einschränkung bleibt aber:
  **rückwirkend** weiter als 365 Tage zurückliegende Muster (z. B. Zyklen von 2018/2021)
  sind mit dem Free/Demo-Tier grundsätzlich nicht nachträglich abrufbar — nur ab jetzt
  laufend akkumulierbar. Für echte mehrjährige Rückblicke wäre ein kostenpflichtiger
  CoinGecko-Tier oder eine andere Quelle nötig (spätere Phase, falls gewünscht).
- **Makro:** Leitzinsen (Fed, EZB, BoJ, PBoC, BoK), Leitbörsen USA/Japan/China/EU/Korea,
  BTC-Dominanz, Fear & Greed. Zusätzlich vom Nutzer gewünscht (2026-07-06), noch zu
  sondieren: **ISM** (Einkaufsmanagerindex), **M2-Geldmenge**, **CPI** (Verbraucher-
  preisindex), **Trueflation** (Echtzeit-Inflationsdaten) — und weitere vergleichbare
  Makro-/Inflationsindikatoren. `[OFFEN]` konkrete kostenlose APIs für alle genannten
  Werte, aktuell UND historisch. Gehört zu Phase 3 (Makro-Modul, `api/macro.py`), nicht
  zu Phase 2.
- **Sentiment (niedrig gewichtet):** X/Twitter (kuratierte Whitelist) und YouTube
  (ausgewählte Kanäle). `[OFFEN]` API-Kosten/ToS/Machbarkeit, spätere Phase. Sentiment
  **nie** als alleiniger Signalgeber.

## 9. Funktionen in der Oberfläche (UI)

Start mit Kryptowährungen, später erweiterbar auf Aktien, ETF, Rohstoffe.

- **U-1** Dashboard: Portfolio-Wert, P&L, Drawdown, Cash-Quote, Marktregime-Ampel —
  Geldwerte in **USD und EUR** (P-9), veraltete Werte sichtbar markiert (P-10).
- **U-2** Watchlist mit Live-Preisen (**USD und EUR**, P-9) + Asset-Risiko-Score;
  Preis-Zeitstempel/Alter sichtbar, veraltete Werte optisch markiert (P-10).
- **U-3** Chart-Ansicht je Asset mit Indikatoren + Forecast-Szenario.
- **U-4** Signal-/Empfehlungsansicht im Format P-5 (kurz + lang, Geldwerte in USD+EUR).
- **U-5** Strategie-Auswahl je Asset + Vorschlag „beste Strategie jetzt".
- **U-6** Portfolio-Verwaltung: Bestände eintragen, Signale zuordnen, Wert in USD+EUR.
- **U-7** Einstellungen: Risikoparameter (Kap. 3) pro Nutzer anpassbar.
- **U-8** Desktop-Benachrichtigungen bei neuen Signalen.
- **U-9** Interaktiver Dialog: Nutzer ergänzt Bewertungsparameter (R-5.7).
- **U-10** Marktscan-Vorschläge (Kap. 13): neu entdeckte Kandidaten mit P-5-Begründung
  anzeigen; Nutzer kann sie in der Watchlist behalten oder entfernen.
- **U-11** Regime-Anzeige (Kap. 14): aktuelles Marktregime sichtbar; manueller Override
  wählbar und — solange aktiv — permanent als Warnhinweis eingeblendet.

## 10. Agent- & Datenbank-Betrieb

- **B-1** Hintergrund-Scheduler (APScheduler) holt periodisch Marktdaten, respektiert
  das CoinGecko-Rate-Limit (Caching in SQLite).
- **B-2** Persistenz: Preise, Indikatoren, Signale, Portfolio, Strategien, Nutzer-
  Parameter und Agent-Begründungen in SQLite (Historie & Nachvollziehbarkeit).
- **B-3** Agent läuft auch ohne offene UI (Hintergrundanalyse); beim UI-Start Abgleich
  mit dem letzten DB-Stand.
- **B-4** Claude API-Key in lokaler `.env` (niemals committen).
- **B-5** Bestände (Anzahl Coins je Asset) sind sensible Finanzdaten und werden
  **ausschließlich** in der SQLite-Datenbank gehalten — nicht in `config.yaml`
  (keine Versionierung/kein Git-Commit). Erstbefüllung per Datei-Import aus
  `Basisinfos/Assets.xlsx`; danach Aktualisierung über die GUI oder erneuten Import.
  Watchlist-Zugehörigkeit und Asset-Metadaten (Typ, Status, CoinGecko-ID) bleiben in
  `config.yaml`, da sie nicht personenbezogen/sensibel sind.
- **B-6** Persistenz erweitert um: neu vom Marktscan entdeckte Assets (Kap. 13),
  Regime-Verlauf und alle Overrides (Quelle, Grund, Zeitpunkt, Dauer — Kap. 14) sowie
  antizyklische Kaufpläne/Tranchen-Status (Kap. 15) — für Nachvollziehbarkeit (Z-4).

## 11. Roadmap & Erweiterbarkeit

1. **Phase 1** Grundgerüst (Struktur, SQLite, CoinGecko, Basis-UI, Watchlist,
   Erstimport der Bestände aus `Basisinfos/Assets.xlsx`).
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

## 13. Marktscan — Entdeckung neuer Assets

Werte in `config.yaml → marktscan`. Der Agent bewertet nicht nur Bestands-/Watchlist-
Assets, sondern sucht **aktiv neue, bisher nicht erfasste Assets** und nimmt aussichts-
reiche Kandidaten eigenständig als `status: watchlist` auf — als Grundlage für Kauf-
Empfehlungen abseits der bestehenden Liste. Advisory-only (P-7): Aufnahme in die
Watchlist ist eine Daten-, keine Handelsaktion.

- **MS-1 Ablauf (hybrid):** Findet der Scan einen Kandidaten, wird er (a) automatisch
  in die Watchlist aufgenommen, (b) per E-Mail gemeldet und (c) mit vollständiger
  P-5-Begründung (warum Kauf/Potenzial) versehen. Der Nutzer entscheidet über die GUI,
  ob der Kandidat bleibt oder entfernt wird (U-10).
- **MS-2 Datenquelle:** CoinGecko **Trending/Top-Gainers als Vorfilter**, Treffer
  danach gegen die Fundamental-/Sicherheitskriterien (Stufe A) geprüft.
- **MS-3 Frequenz:** 2× täglich, **04:00 und 16:00** (reiner Watchlist-Scan). Frequenz
  für weitergehende Agent-Funktionen (laufende Bestandsbewertung, De-Risking) noch offen.

### Stufe A — Ausschluss & Einordnung (harte Filter, Tier-Modell)

Kein Einzel-Cutoff, sondern ein **Tier-Modell** (Grenzen vorläufig):

| Tier | Marktkap. | Rolle | Filter |
|------|-----------|-------|--------|
| Tier 1 | ≥ ~1 Mrd. USD | Kern-Diversifikation, Narrativ-Abdeckung | Standard |
| Tier 2 | ~150 Mio.–1 Mrd. | Wachstums-Chance | strenger |
| Tier 3 | ~20–150 Mio. | Small-Cap-Beimischung (High-Risk) | strengste Signale + Budget-Deckel |

- **A(MS)-1 Tier-3-Budgetdeckel:** Small Caps insgesamt max. **10–15 %** des Portfolios
  (`config.yaml → risiko.max_allokation_small_cap_prozent`), regime-abhängig gedrosselt.
- **A(MS)-2 Weiche Untergrenze:** Coins < 20 Mio. USD nur über **Override**, wenn der
  Risiko-Score sie trotz Größe als moderat/gering-riskant einstuft. Da die Marktkap.
  selbst in RM-8 einfließt, muss dieser Override durch **andere** Faktoren (Liquidität,
  Trend, Volumen, Narrativ) „verdient" werden — er ist selten.
- **A(MS)-3 weitere Filter:** Mindest-Handelsvolumen 24h, Mindestalter, Volumen/Marktkap.-
  Ratio (Wash-Trading-Schutz), Stablecoins ausgeschlossen, Duplikat-Check gegen
  bestehende Watchlist. Konkrete Werte in `config.yaml → marktscan.filter`.
- **A(MS)-4 Geltungsbereich:** Nur für **Agent-Neufunde**; manuelle Nutzer-Picks bleiben
  unberührt (dürfen riskanter sein).
- **A(MS)-5 Narrativ-Abdeckung** (RWA, KI, DePIN, L1/L2 …): fehlende Narrative werden
  bevorzugt ergänzt (Diversifikation, gegen Klumpenrisiko A-2) — zugleich Positiv-Signal
  in Stufe B.

### Stufe B / C / D — `[OFFEN]`, in Ausarbeitung

- **Stufe B (positive Signale):** vier Kategorien — Technik, Fundamental/Qualität,
  Markt-/Momentum, Kontext/Makro. Grundlinie: Bei *Neufunden* wiegen Fundamental &
  Momentum schwerer als reines Technik-Timing (das zählt mehr für laufende Watchlist).
- **Stufe C (Scoring/Gewichtung):** Verrechnung der Signale; Gewichte kommen aus dem
  aktiven Regime-Profil (Kap. 14).
- **Stufe D (Schwellenwerte):** ab welchem Score „watchlist-würdig" bzw. „Kaufkandidat".

## 14. Regime-Steuerung — marktabhängiges Verhalten

Werte in `config.yaml → regime`. **Querschnitts-Modul**, das sowohl den Marktscan
(Kap. 13) als auch die laufende Bestandsbewertung speist. Grundidee: Die *Struktur* der
Bewertung bleibt gleich, ihre *Parameter* atmen mit dem Markt.

**Regime-Spektrum:** `KRISE-EXTREM — BÄR — SEITWÄRTS — BULLE — EUPHORIE-EXTREM`.

- **RG-1 Bestimmung (hybrid):** (a) **regelbasiert** als Basis (deterministisch, prüfbar)
  aus BTC-Trend × BTC-Dominanz, Fear & Greed, Zinsen; (b) **KI-Override** durch den Agenten
  bei belastbaren Gegengründen oder absehbarem Regimewechsel; (c) **manueller Override**
  durch den Nutzer.
- **RG-2 BTC-Matrix:** Ein Altcoin-Signal wird immer im Kontext von BTC-Trend *und*
  BTC-Dominanz gelesen (BTC-Season / Altseason / Flucht-in-BTC / Kapitulation).
- **RG-3 Regime-Profile:** Jedes Regime überschreibt vier Stellschrauben — Tier-Schwellen,
  Kategorie-Gewichte (Stufe B), Tier-3-Budget, Mindest-Konfidenz. Im Bär z. B.
  Fundamental & relative Stärke höher, reine Ausbrüche niedriger; Budget gedrosselt.
- **RG-4 Makro-Multiplikator (`risikoappetit_faktor`, 0,3–1,0):** globaler Regler aus der
  Makro-Lage (Zinsen/Krise), der Budgets und Positionsgrößen *zusätzlich* skaliert — kann
  selbst eine Krypto-Altseason dämpfen, wenn das Makro-Umfeld feindlich ist.

### Override-Governance

- **RG-5 Sicherheits-Asymmetrie (Herzstück):** *Defensiver* werden (Richtung Bär/
  Kapitalschutz) darf jede Quelle **autonom und sofort**. *Offensiver* werden (Filter
  lockern, Budget erhöhen) braucht eine **Bremse** (höhere Konfidenz, Quellennachweis,
  beim Nutzer bewusste Bestätigung). Begründung: Z-1/P-1 — ein Fehler „zu vorsichtig"
  kostet Gewinn, „zu offensiv" kostet Kapital.
- **RG-6 Unantastbare harte Limits:** Kein Override — weder Nutzer noch KI — darf
  Pflicht-Stop-Loss (RM-5), Risiko/Trade (RM-1) oder Drawdown-Notbremse (Z-3/RM-7)
  abschalten. Overrides bewegen nur die *einstellbaren* Regime-Parameter.
- **RG-7 Vorausschauender KI-Override = Bias, kein Voll-Flip:** Ein erwarteter Wechsel
  verschiebt das Regime nur teilweise (z. B. „Bär mit aufhellender Tendenz"); voll kippt
  es erst bei Datenbestätigung. Quelle der Erwartung ist Pflichtangabe (P-2).
- **RG-8 Manueller Override:** permanent sichtbar (U-11) und mit Ablauf/periodischer
  Bestätigung, damit er nicht vergessen wird. Alle Overrides landen in der DB (B-6).
- **RG-9 Vorrang:** harte Limits > manueller Override (offensiv nur mit Bestätigung) >
  KI-Override (defensiv autonom, offensiv mit Nachweis) > regelbasierte Basis.

### Extremregime (Sonderregeln, keine bloße Extrapolation)

- **RG-10 Krise-extrem, zwei Typen:** (a) **Liquiditäts-/Deflationskrise** (Anleihenmarkt
  kippt, Korrelation→1) → maximale Defensive, Flucht in Cash. (b) **Währungs-/Vertrauens-
  krise** → BTC kann *Fluchtwert* sein, Rotation in BTC/harte Assets. Enthält eine
  **Stablecoin-Peg-Prüfung**: In einer Euro-Krise ist **EURCV** (Euro-besichert) *nicht*
  automatisch sicher. Der Agent **warnt** in diesem Fall nur (keine autonome Umschichtung).
- **RG-11 Euphorie-extrem = Offense + Sicherheitsgurt:** offensiver werden, um den
  Melt-up mitzunehmen, **gekoppelt** mit verschärfter Gewinnabsicherung (engere
  Trailing-Stops RM-6, Teilverkäufe/Distribution). Extreme Gier gilt zugleich als Chance
  *und* Warnsignal (Countdown). Offense ohne mitwachsende Absicherung bleibt verboten.

## 15. Antizyklische Kauf-Disziplin

Werte in `config.yaml → antizyklisch`. **Kern-Mehrwert des Agenten:** Er kontert den
häufigsten Kleininvestor-Fehler — in den fallenden Kurs verkaufen (Panik) und im Tief
nicht kaufen. Als regelbasiertes System kann er antizyklisch handeln, wo der Mensch an
seinen Emotionen scheitert. Grundsatz: **antizyklisch, aber bedingt.**

- **AZ-1 Klassifikation Flush vs. Zusammenbruch:** Ein **Liquidations-Flush** (sehr
  schnell, hohes Volumen, keine Fundamental-News, Zwangsverkäufe) wird meist V-förmig
  zurückgekauft → Kaufgelegenheit. Ein **fundamentaler Zusammenbruch** (zäh, Substanz
  erodiert, konkrete News) ist es *nicht*.
- **AZ-2 Bestätigungs-Gate („kaufe die Bestätigung, nicht das Messer"):** Vor Kapital-
  einsatz Stabilisierung/Umkehr abwarten — keine neuen Tiefs, Level-Rückeroberung,
  bullische Divergenz, versiegendes Verkaufsvolumen, bestätigte Umkehr-Struktur.
- **AZ-3 Abgestuftes Modell:** kleine **Spot-Sondierungstranche** nur für **Kernwerte
  (BTC/ETH)** ggf. vor voller Bestätigung; größere Positionen **und jeglicher Hebel** nur
  **nach Bestätigung**; im **Totalcrash / Extrem-Krise-Regime** wird nichts gekauft, bis
  eine klare Bestätigung vorliegt.
- **AZ-4 Gestaffelt & begrenzt:** in Tranchen kaufen (DCA/S-1/S-2), **nie all-in** →
  ein tieferer Absturz wird zur nächsten Chance statt zum Ruin; Cash-Reserve (RM-4) bleibt.
- **AZ-5 Fundamental-Gate:** Nachkaufen nur bei **intakter Substanz**. Fallender Kurs +
  erodierende Substanz = Value-Falle, **kein** Kauf.
- **AZ-6 „Gescheiterte-These"-Ausstieg:** Läuft ein antizyklischer Kauf über Schwelle
  *und* erwartete Zyklusdauer hinaus gegen die These, **stoppt** das Nachkaufen und wird
  neu bewertet — kein mechanisches Weiter-Mitteln.
- **AZ-7 Hebel-Regeln:** gehebeltes antizyklisches Kaufen **nur nach Bestätigung**, im
  Extrem-Krise-Regime und bei erhöhtem Strukturrisiko **komplett aus**; sonst nur niedrig,
  gestaffelt, Liquidationspreis weit unter dem nächsten plausiblen Tief (RM-10/RM-11).
  Grund: Hebel nimmt genau die Zeit, die die antizyklische These zum Aufgehen braucht.
- **AZ-8 Strukturell vs. zyklisch — ehrlicher Umgang:** Die Unterscheidung ist in Echtzeit
  **nicht sicher** treffbar (oft erst im Rückblick klar). Schutz kommt daher **nicht aus
  Vorhersage**, sondern aus den Schaltkreis-Unterbrechern (gestaffelt, Fundamental-Gate,
  These-Ausstieg, Drawdown-Notbremse, Cash-Reserve, Diversifikation, Hebel-Aus). Ziel:
  *beide* Fälle überleben — bei zyklisch profitieren, bei strukturell den Verlust deckeln.

## 16. Offene Punkte / zu entscheiden

**Risiko-/Basiswerte:**
- Maximaler tolerierter Gesamt-Drawdown (Z-3)? Vorschlag −15 %.
- Max. Allokation pro Einzelwert (RM-2) und pro Assetklasse (RM-3)?
- Standard-Timeframes für die technische Analyse.
- Claude-Modellversion und Budget/Token.

**Datenqualität (P-10) — ERLEDIGT (2026-07-06, Phase 2):**
- Live-Preise gelten als veraltet ab `> 10 Min` (2× 5-Min-Scheduler-Takt), historische
  Tagesdaten ab `> 2 Kalendertage` Rückstand — implementiert in `ui/formatting.py`
  (`is_price_stale`, `is_history_stale`).
- Mindest-Historienlänge je Indikator: exakt der jeweils benötigte Zeitraum (z. B. EMA-200
  braucht genau 200 Tage, kein zusätzlicher Puffer) — implementiert als Gating in
  `indicators/calculations.py` (`IndicatorResult.available`/`.reason`).
- Visuelle Konvention: `⚠`-Präfix in Warnfarbe (`#b36b00`) plus konkretes Alter im Text
  (Text + Farbe zusammen, nicht nur Farbe) — in Watchlist/Portfolio/Chart-Fenster
  umgesetzt.
- **Zusatz-Entscheidung (Phase 2):** Echtes ATR und echtes Williams-Fraktal (Swing-
  Highs/-Lows) sind mit CoinGecko Free Tier nicht in brauchbarer Tages-Auflösung möglich
  (echte OHLC-Daten nur als 4-Tage-Kerzen für ein Jahr). Stattdessen werden Näherungen
  verwendet (Schlusskurs-basierte Volatilität bzw. lokale Extrema), die in der UI **immer**
  explizit als Näherung gekennzeichnet sind, nie kommentarlos als „ATR"/„Swing-High/Low".

**Marktscan (Kap. 13):**
- **Stufe B, C, D** ausarbeiten (positive Signale, Scoring, Schwellenwerte).
- Tier-Grenzen, Small-Cap-Budget (10–15 %) und Filter-Werte (Volumen, Alter) bestätigen.
- Frequenz weiterer Agent-Funktionen (Bestandsbewertung/De-Risking) festlegen (bisher
  nur Watchlist-Scan 2× täglich).

**Regime-Steuerung (Kap. 14):**
- Regime-Profil-Werte (Gewichte, Mindest-Konfidenz, Budgets) sind Platzhalter → kalibrieren.
- Herleitung des `risikoappetit_faktor` aus konkreten Makro-Daten (hängt an Makro-APIs).

**Daten & Betrieb:**
- Konkrete kostenlose APIs für Makro-/Zinsdaten — inkl. ISM, M2-Geldmenge, CPI,
  Trueflation und weitere (siehe Kap. 8), jeweils aktuell UND historisch. Phase 3.
- X-API & YouTube-API: Kosten, Limits, ToS, Umsetzungsphase.
- **E-Mail-Versand** (Kap. 13): SMTP-Server vs. Mail-API wählen; Zugangsdaten nur in `.env`.
- **Flush-Erkennung** (AZ-1): reichere Signale (Funding-Rates, Liquidationsdaten) brauchen
  zusätzliche Datenquellen jenseits CoinGecko → spätere Phase.
- **Advisory-Konsequenz** (P-7): Eskalationsweg für Schutz-Alerts (Stop-Loss/Drawdown)
  definieren — E-Mail-Priorität, UI-Warnstufe.

**Steuer & Datenpflege:**
- Steuerregel P-6 (Swap steuerneutral bis Auszahlung) mit Steuerberater verifizieren
  (Sonderfälle: Altvermögen/Spekulationsfrist, Besteuerung von Staking-Erträgen).
- **ERLEDIGT (2026-07-06):** Zwei fehlerhafte Ticker in `Assets.xlsx` direkt in der
  Originaldatei korrigiert (nicht nur in `config.yaml`): Stellar stand als „XML" statt
  „XLM"; Canton Network stand als „CC" statt „CANTON" (beim Phase-1-Import entdeckt).
  Damit ist der `SYMBOL_OVERRIDES`-Workaround in `importer/excel_import.py` nicht mehr
  nötig und wurde entfernt. Backup der Originaldatei vor der Korrektur liegt lokal unter
  `.claude/backups/` (nicht versioniert).
