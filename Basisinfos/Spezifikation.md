# TradingInfoTool — Spezifikation (fachliche Grundlage)

> **Eigentümer:** Gernot Spiessmaier · **Version:** 1.6 · **Stand:** 2026-07-08
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
  **KI-Ebene entschieden (2026-07-07):** Nach Detail-Recherche (Kosten, Nachhaltigkeit,
  Nutzungsbedingungen) fällt die Wahl auf **Groq** (Llama 3.3 70B, remote, `GROQ_API_KEY`)
  als primäre Analyse-Ebene für Phase 3 — dauerhaft kostenlos (kein Kreditkarten-Zwang,
  kein zeitlich begrenztes Guthaben), finanziell solide unterlegt (>1,4 Mrd. $ Kapital),
  Nutzungsbedingungen erlauben automatisierte Nutzung innerhalb der Rate-Limits. Damit
  ist P-8 sowohl erfüllt (lokal via Phi-4-mini weiterhin voll funktionsfähig als
  Offline-Fallback) als auch übertroffen (deutlich stärkeres Modell als lokal möglich,
  ohne Kostenschranke). Grundsatz dahinter: kostenlose Optionen zuerst voll ausschöpfen
  (lokal UND remote parallel), kostenpflichtige Quellen (z. B. Claude API) erst wenn
  eine konkrete Aufgabe die Qualität von Groq/lokalem Modell nachweislich übersteigt.
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

**Umsetzungsstand (2026-07-07, Phase 3 Slice 1 — siehe Kap. 11):** Die Pipeline läuft
seit dieser Slice erstmals real, ausgelöst manuell über den "Signale"-Tab
(`ui/signals_view.py` → `agent/krypto/pipeline.py::generate_signal()`), noch nicht geplant/
automatisch (siehe Kap. 11). KI-Ebene: Groq (Llama 3.3 70B, siehe P-8), nicht Claude —
die Fakten-Schicht (Indikatoren, Regime, Risiko-Check) ist deterministisches Python,
Groq synthetisiert daraus die Empfehlung inkl. Begründung; das Modell wird dabei nie
blind vertraut, `agent/krypto/risk_gate.py::post_check()` erzwingt die harten Regeln nach dem
Groq-Aufruf nochmals deterministisch. Detaillierter Implementierungsplan (inkl.
bewusster Vereinfachungen je Schritt) unter
`C:\Users\Geatsch\.claude\plans\deep-launching-zebra.md`.

Entscheidungs-Pipeline (Reihenfolge je Analyse):
0. **R-5.0** Datenqualitäts-Gate (P-10, VOR allem anderen): Sind die für dieses Asset
   benötigten Daten aktuell und vollständig genug? Wenn nein → Abbruch für dieses Asset,
   Ausgabe „HALTEN — Datenlage unsicher" mit konkretem Grund (z. B. „Preis seit X Min.
   nicht aktualisiert", „nur Y Tage Historie, benötigt Z"), kein Rateversuch mit
   Lückendaten. **ERLEDIGT (2026-07-07):** `agent/krypto/pipeline.py` prüft Preis-/Historie-
   Staleness (`staleness.py`) + Mindestverfügbarkeit von RSI/MACD/Bollinger, bevor
   irgendein Groq-Call erfolgt.
1. **R-5.1** Marktregime bestimmen (Bulle/Bär/Seitwärts) via BTC-Trend, BTC-Dominanz,
   Fear & Greed. **ERLEDIGT, regelbasiert (2026-07-07):** `agent/krypto/regime.py` — BTC-
   EMA-Ordnung, BTC-Dominanz-Trend (CoinGecko `/global`, neu `api/macro.py`), Fear &
   Greed (alternative.me, kostenlos/kein Key). Bewusst einfache, dokumentierte
   Heuristik statt der vollen RG-1..RG-11-Feinheit (siehe Kap. 14); KI-Override (RG-1b)
   noch nicht umgesetzt. Manueller Override (`config.yaml regime.manueller_override`)
   wird respektiert (RG-8/RG-9).
2. **R-5.2** Makro-Kontext: Leitzinsen, Risikoumfeld USA/Japan/China/EU/Korea.
   **Teilweise ERLEDIGT (2026-07-08, Nutzungs-Diskussion).** Neue Regime-Dimension
   `liquiditaets_regime` (`agent/krypto/regime.py`) kombiniert Fed-Funds-Rate-Richtung
   (Historie via `api/macro.py::get_fred_history`) mit dem globalen M2-Trend
   (USA/Eurozone/China, Mehrheitsentscheid über die prozentuale Veränderung —
   bewusst keine Währungsumrechnung/Summe, siehe Modul-Docstring) zu
   expansiv/restriktiv/gemischt/widersprüchlich/unbekannt. Bewusst als **frischer
   Live-Abruf pro Pipeline-Lauf** (`agent/krypto/pipeline.py::_fetch_liquidity_context`),
   nicht aus der `macro_snapshot`-Akkumulation abgeleitet — die Pipeline läuft nur
   bei manuellem Klick (kein täglicher Scheduler), ein reiner "erster vs. letzter
   Snapshot"-Trend hätte real Monate gebraucht, bis genug Datenpunkte da sind. Fließt
   als **Kontext, keine harte Regel** in `long_reasoning.makro` ein (Regel 10,
   `agent/krypto/analyst.py`). **Weiterhin `[OFFEN]`:** CPI/ISM-Ersatz/Trueflation/einzelne
   Leitbörsen — `disclaimers.makro_einbezogen` steht deshalb ehrlich auf
   `"teilweise"` (P-2/P-10), nicht mehr fest auf `false`.
   **Schritt 2 ERLEDIGT (2026-07-08): Zyklus-Risiko.** Weiteres neues Regime-Feld
   `zyklus_risiko` (0–1) aus dem BTC-Log-Regression-Risk-Modell
   (`indicators/calculations.py::compute_btc_log_regression_risk`), MVRV/NUPL
   (`api/onchain.py`) bewusst NICHT als eigenes Feld, sondern nur als Cross-Check-Text
   daneben (`_mvrv_band()`, eigene dokumentierte Bänder — keine Nachbildung einer
   kommerziellen Formel) — beide Modelle beantworten dieselbe Frage
   (Bewertungsextrem), ein zweites Feld würde das Signal doppelt gewichten. Gilt für
   **alle** Assets, nicht nur BTC (Prompt-Regel 11) — Alts leiden historisch am
   stärksten nahe einem BTC-Zyklus-Top. Live-verifiziert gegen echte BTC- **und**
   ETH-Pipeline-Läufe: Groq hat `zyklus_risiko: 0.32` in beiden Fällen korrekt in
   `long_reasoning.fundamental` eingeordnet.
3. **R-5.3** Technische Analyse je Asset: Trend, Indikatoren (Kap. 7), Fibonacci,
   Support/Resistance. **ERLEDIGT:** volle Wiederverwendung von
   `indicators/calculations.py` (`build_technical_snapshot()`, geteilt mit
   `ui/charts.py` — keine zwei Datenquellen), neu `summarize_confluence()` als
   einfache, explizit als Heuristik gekennzeichnete Zusammenfassung (entscheidet
   nichts selbst, liefert nur Fakten an Groq).
4. **R-5.4** Sentiment (X/YouTube) — nur Zusatz, niedrig gewichtet, nur seriöse
   Quellen. Weiterhin Phase 4 (siehe Kap. 11), im Facts-Objekt ebenfalls als
   `disclaimers.sentiment_einbezogen: false` ausgewiesen.
5. **R-5.5** Risikoprüfung (Kap. 3) als **VETO-Stufe**: scheitert hier → kein Kauf.
   **ERLEDIGT (RM-1/-2/-4/-5):** `agent/krypto/risk_gate.py::pre_check()` (vor dem Groq-Call,
   liefert eine harte Positionsgrößen-Obergrenze als Fakt) UND `post_check()` (danach,
   erzwingt dieselben Regeln nochmal deterministisch — das Modell wird nie blind
   vertraut). RM-7/Z-3 (Drawdown-Notbremse) bleibt `[OFFEN]` (braucht eine noch nicht
   existierende Portfolio-Wert-Historie), RM-8/-9 (voller Risiko-Score) und RM-10/-11
   (Hebel) ebenfalls offen (S-6 Hebel-Long ist in `config.yaml` `aktiv: false`).
6. **R-5.6** Signal + Konfidenz + vollständige Empfehlung (Format P-5). **ERLEDIGT:**
   `agent/krypto/analyst.py` — striktes JSON-Schema (Groq `response_format: json_object`),
   Validierung inkl. case-insensitiver Enum-Normalisierung (Groq antwortet nicht immer
   in Großbuchstaben), ein Retry bei kaputtem JSON, danach fail-loud
   („HALTEN — Agent-Antwort ungültig").
7. **R-5.7** Haltedauer-Empfehlung (kurz/mittel/lang) mit Begründung; Nutzer kann eigene
   Parameter ergänzen (interaktiver Dialog), die in die nächste Bewertung einfließen.
   Haltedauer-Feld **ERLEDIGT** (Teil der Groq-Antwort), der interaktive Dialog (U-9)
   bleibt `[OFFEN]`.
8. **R-5.8** Forecast als Szenario (Bull/Base/Bear) mit Wahrscheinlichkeiten, statt
   einzelner Punktprognose. **ERLEDIGT** (zusätzliches Feld in der Groq-Antwort).
9. **R-5.9** Steuerliche Optimierung (AT, siehe P-6): Bei strategisch gleichwertigen
   Alternativen bevorzugt TAUSCHEN (Krypto-zu-Krypto/Stablecoin) statt VERKAUFEN
   vorschlagen, da steuerlich neutral bis zur Auszahlung in Fiat. **ERLEDIGT:** per
   Prompt-Klausel UND mechanisch in `risk_gate.post_check()` erzwungen (VERKAUFEN →
   TAUSCHEN, wenn ein Swap-Ziel genannt wurde) — nicht nur der Prompt-Hoffnung
   überlassen.
10. **R-5.10** Regime-Profil anwenden (Kap. 14): Das in R-5.1/R-5.2 bestimmte Regime
    moduliert Gewichte, Schwellen, Small-Cap-Budget und Mindest-Konfidenz; Overrides
    nach der Governance-Regel (Sicherheits-Asymmetrie, harte Limits unantastbar).
    **ERLEDIGT (Mindest-Konfidenz + Small-Cap-Budget):** `risk_gate.py` nutzt
    `config.yaml regime.profile[<regime>]` statt der statischen Werte.
11. **R-5.11** Bei Kauf-/Nachkauf-Empfehlungen antizyklische Disziplin (Kap. 15):
    Flush vs. fundamentaler Zusammenbruch klassifizieren, Bestätigungs-Gate, gestaffelt.
    **Nur einfache Heuristik (2026-07-07):** `agent/krypto/anticyclic.py` — Funding-Rate-
    Extremwert (Kraken Futures) + Kursrückgang-Geschwindigkeit als grober Hinweis,
    NICHT die volle AZ-1..AZ-8-Klassifikation (fehlt eine unabhängige Nachrichten-/
    Fundamentalquelle). Liefert nur Kontext an Groq, trifft keine eigene Veto-
    Entscheidung. **Erweitert (Nutzungs-Diskussion Schritt 3, 2026-07-08):** zusätzlich
    Open Interest (Binance/Bybit/OKX, `api/derivatives.py`, unabhängig voneinander
    versucht — fehlt eine Börse, blockiert das nicht die anderen) und Binance-
    Long-Short-Ratio. Der Long-Konten-Anteil (`LONG_BIAS_EXTREME_THRESHOLD_PCT = 65%`,
    dokumentierter Platzhalter wie die bestehende Funding-Rate-Schwelle) verstärkt nur
    den Beschreibungstext ("zusätzlich bestätigt"/"uneindeutig"), ändert aber NICHT die
    bestehende `moeglicher_flush`-Formel selbst — kein Risiko einer Verhaltensänderung
    an bereits getesteter Logik. Live verifiziert inkl. eines echten Falls mit
    `moeglicher_flush=true` + 81,8 % Long-Bias (GRIFFAIN) und eines Falls mit
    fehlender OKX-Notierung (graceful, P-10).

> **Nutzungs-Diskussion abgeschlossen (letzter Schritt, 2026-07-08):** Facts-Feld
> `markt_kontext` (`agent/krypto/analyst.py::build_facts`) — BTC-Exchange-Flow-Netto
> (`api/onchain.py`), globale Stablecoin-Supply (DefiLlama), Präsidentschaftszyklus-
> Kontext + nächste FOMC-Sitzungen (beide `agent/cycles.py`, reine Datumsrechnung,
> kein Netzwerk-Call). **Bewusst KEINE neue Regime-Logik** — reiner, niedrig
> gewichteter Kontext für Groq (Prompt-Regel 13): FOMC-Sitzung < 14 Tage entfernt →
> explizit als Volatilitätsfaktor in `key_risks` nennen, Präsidentschaftszyklus nur
> mit explizitem "keine Prognose-Garantie"-Vorbehalt. Live verifiziert: bei der
> echten, 19 Tage entfernten Sitzung korrekt nicht erzwungen (unter der Schwelle),
> bei einer künstlich auf 5 Tage gesetzten Sitzung korrekt in `key_risks` genannt.
> Damit ist die gesamte am 2026-07-08 vereinbarte Nutzungs-Tabelle (Liquiditäts-
> Regime, Zyklus-Risiko, AZ-1-Erweiterung, Markt-Kontext) umgesetzt.

> **A-1-Ausnahme:** Stablecoins (`typ: stablecoin`, aktuell nur EURCV) durchlaufen die
> Pipeline gar nicht erst — festes „HALTEN" ohne Groq-Call, da sie laut Kap. 4 (A-1)
> kein eigenständiges Handelssignal bekommen sollen.

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
- **Echtes OHLC (ATR, Swing-Highs/-Lows):** **ERLEDIGT (2026-07-07):** Kraken liefert
  echte Kerzendaten (Open/High/Low/Close) über öffentliche Endpunkte — kein Account,
  kein API-Key, keine Anmeldung nötig, zählt nicht gegen Rate-Limits. Ersetzt die in
  Phase 2 eingeführte Schlusskurs-Näherung (`atr_close_to_close_proxy`,
  `swing_highs_lows_close_proxy`) für alle bei Kraken gelisteten Assets — echtes
  Wilder's-ATR (`atr_wilder`) und echtes Williams-Fraktal (`swing_highs_lows_fractal`)
  in `indicators/calculations.py`, verdrahtet in `ui/charts.py` (bevorzugt echte Werte,
  fällt für nicht gelistete Assets automatisch und klar gekennzeichnet auf die Näherung
  zurück). **Verifizierte Abdeckung (gegen `/0/public/AssetPairs` geprüft, nicht nur
  BTC/ETH angenommen):** 35 von 41 Watchlist-Assets haben ein Kraken-Spot-Paar in USD
  **und** EUR; 36 von 41 haben zusätzlich Funding-Rate-Daten (Kraken Futures, deckt AZ-1
  ab, ohne CoinGlass ab 29 $/Monat zu benötigen). Ohne Kraken-Listing (bleiben bei der
  Näherung): EURCV (Stablecoin, braucht ohnehin kein OHLC/ATR), KAIA, BRETT, IO, SUPRA,
  CANTON. Persistiert in eigener Tabelle `price_history_ohlc` (Schlüssel: Symbol +
  Währung + Datum, getrennt von der CoinGecko-basierten `price_history`), täglicher
  Backfill/Refresh über `api/kraken_history.py` + eigenen Scheduler-Job
  (`refresh_ohlc_job`, 24 h).
  **MiCA-Klarstellung:** Die EU-Regulierung betrifft Kunden-Dienstleistungen (Handel,
  Verwahrung, Transfer) — nicht rein lesende, öffentliche Marktdaten-APIs. Kraken wurde
  trotzdem als pragmatischer Standard gewählt (unkompliziert, gut dokumentiert), nicht
  aus einer unbegründeten Regulierungs-Sorge bei alternativen Börsen.
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
  BTC-Dominanz, Fear & Greed. **ERLEDIGT (2026-07-08):** Alle Werte sind live in
  `api/macro.py`/`agent/krypto/pipeline.py`/`database/models.py::MacroSnapshot` implementiert
  UND end-to-end mit einem echten `FRED_API_KEY` verifiziert (Fed 3,63 %, EZB
  2,25/2,40/2,65 %, M2, CPI, Philly-Fed-ISM-Ersatz, BoJ/BoK, PBoC-LPR 3,0/3,5 % —
  alle korrekt in der DB gelandet). Für die übrigen Werte (Leitzinsen + Zusatzwunsch
  vom Nutzer 2026-07-06: **ISM**, **M2-Geldmenge**, **CPI**, **Trueflation**) wurden am
  2026-07-08 alle Quellen live recherchiert und verifiziert (nicht nur angenommen):

  - **FRED (St. Louis Fed) deckt den Grossteil ab, EINE einzige API statt der
    urspruenglich angenommenen mehreren Notenbank-Systeme:**
    - Fed Funds Rate: Series `FEDFUNDS`
    - M2-Geldmenge: Series `M2SL`
    - CPI (Headline/Core): Series `CPIAUCSL` / `CPILFESL`
    - **EZB-Leitzinsen laufen ebenfalls über FRED** (nicht über eine separate ECB-SDW-
      Integration, wie urspruenglich angenommen): `ECBDFR` (Einlagensatz),
      `ECBMRRFR` (Hauptrefinanzierungssatz), `ECBMLFR` (Spitzenrefinanzierungssatz) —
      live bis 2026-07-07 verifiziert.
    - BoJ (Japan): `IRSTCI01JPM156N` (Tagesgeld-/Interbankensatz, OECD-Quelle),
      **~2 Monate Meldeverzug** — eigene, grosszuegigere Staleness-Schwelle noetig.
    - BoK (Korea): `INTDSRKRM193N` (Diskontsatz, OECD-Quelle), ebenfalls ~2 Monate
      Verzug.
    - **ISM Manufacturing PMI ist NICHT ueber FRED verfuegbar** (2016 wegen
      Lizenzrechten des Institute for Supply Management entfernt). Ersatzquelle
      DBnomics (`db.nomics.world`) hat noch Daten, ABER die letzten 4 Monatswerte
      waren beim Live-Test (2026-07-08) offensichtlich fehlerhaft (PMI ~10-11 statt
      der ueblichen 40-60er-Spanne) — als Quelle NICHT vertrauenswuerdig ohne eigene
      Plausibilitaetspruefung. **Empfohlener Ersatz:** Philadelphia Fed Manufacturing
      Index, Series `GACDFSA066MSFRBPHI`, ebenfalls ueber FRED, aktuell (bis Juni 2026
      verifiziert), etablierter Fruehindikator, methodisch aehnlich (Diffusionsindex).
    - FRED-API: kostenlos, Key wird sofort bei Registrierung vergeben
      (`fredaccount.stlouisfed.org/apikeys`), 120 Requests/Minute Limit (fuer unseren
      Bedarf grosszuegig), Nutzung fuer private/kommerzielle Projekte laut ToS erlaubt.
  - **PBoC (China): automatisierbare Quelle gefunden bei vertiefter Recherche
    (2026-07-08).** Amtliche Quelle (chinamoney.com.cn/NIFC) und World Bank/IMF (>1
    Jahr Verzug) sowie FRED (`INTDSRCNM193N`, seit Mitte 2025 nicht mehr aktualisiert)
    bleiben unbrauchbar. **Gefunden:** die Open-Source-Bibliothek `akshare`
    (16,6k GitHub-Stars, aktiv gepflegt, aggregiert chinesische Finanzdaten) nutzt
    fuer `macro_china_lpr()` intern den Endpunkt
    `https://datacenter-web.eastmoney.com/api/data/v1/get` (Eastmoney, einer der
    groessten chinesischen Finanzdatenanbieter) mit einem oeffentlichen Token im
    Query-String — liefert strukturiertes JSON mit LPR1Y/LPR5Y, live getestet:
    2026-06-22, 3,0 %/3,5 %, deckt sich mit unabhaengiger News-Recherche. Kein
    OCR/Scraping noetig. **Integrationsentscheidung:** direkter, leichtgewichtiger
    `requests`-Call (wie bei `api/kraken.py`/`api/groq.py`), NICHT die volle
    `akshare`-Bibliothek als Dependency (zieht pandas/tqdm/weitere Pakete mit) — der
    eine Endpunkt reicht. **Wichtiger Vorbehalt (P-10):** das ist keine offiziell
    dokumentierte, versionierte API, sondern der interne Endpunkt von Eastmoneys
    eigener Webseite, den `akshare` reverse-engineered hat — kann sich ohne
    Vorankuendigung aendern. Bei Fehlschlag: letzter bekannter Wert bleibt in der DB,
    mit Alters-Kennzeichnung (wie bei allen anderen Quellen), kein Absturz, keine
    Fantasiewerte. Da der LPR nur ca. 1×/Monat wechselt, ist das Abfrage-Risiko gering.
  - **Trueflation: verworfen, kein kostenloser API-Zugang.** Das Web-Dashboard ist mit
    einem kostenlosen Konto nutzbar (1.200 Credits/90 Tage, Live-Test zeigte Daten mit
    nur 1 Tag Verzug), aber programmatischer API-Zugang (das, was `api/macro.py`
    braeuchte) ist laut eigener Pricing-Seite explizit NICHT in den guenstigen Stufen
    enthalten, sondern nur in einer separaten, individuell bepreisten "API Access"-Stufe
    — vom Nutzer am eigenen Konto bestaetigt (API-Keys vorhanden, aber ohne kostenlose
    Variante beworben). Zusaetzlicher Vorbehalt: Truflations eigener "Echtzeit"-CPI-Wert
    wich beim Live-Test massiv vom offiziellen BLS-Wert ab (1,79 % vs. 4,20 % YoY) —
    andere Methodik, muesste bei Nutzung klar gekennzeichnet werden, um nicht wie ein
    Fehler zu wirken.
  - **Wichtig fuer die spaetere Umsetzung:** Makro-Daten haben von Natur aus einen viel
    laengeren Meldeverzug als Krypto-Preise (CPI/M2 ueblicherweise 1-2 Monate, selbst
    beim Erscheinen brandaktuell). Die bestehende Staleness-Logik (`staleness.py`,
    aktuell auf Minuten/Tage fuer Preise/Historie ausgelegt) braucht fuer Makro-Daten
    eigene, deutlich groessere Schwellen — sonst wuerden korrekte, aktuelle FRED-Daten
    faelschlich als "veraltet" markiert.
- **Sentiment (niedrig gewichtet):** X/Twitter (kuratierte Whitelist) und YouTube
  (ausgewählte Kanäle). `[OFFEN]` API-Kosten/ToS/Machbarkeit, spätere Phase. Sentiment
  **nie** als alleiniger Signalgeber.
- **Globale M2-Geldmenge (Eurozone/China/Japan): ERLEDIGT (2026-07-08).** Ergänzt die
  US-M2 (`M2SL` über FRED) um eine echte globale Liquiditätssicht, `api/onchain.py` +
  `agent/cycles.py`-Nachbarmodul-Muster. Eurozone über die EZB-eigene SDMX-API, China
  über denselben Eastmoney-Endpunkt wie der PBoC-LPR. **Japan ist ein HTML-Scraping-
  Fallback**, keine echte API: die 2026 gestartete BoJ-JSON-API ließ sich trotz ~30
  Versuchen (Query-Parameter, POST-Body-Varianten, ~15 Feldnamen) nicht ansteuern —
  selbst `bojpy` (einzige gefundene Community-Bibliothek) scraped aus demselben Grund
  HTML. Der Scraper sucht die M2-Spalte über ihren Namen (nicht per festem Index) und
  wirft bei Strukturänderung einen klaren Fehler statt eines falschen Werts. Alle drei
  live verifiziert (Mai 2026). **Korea-M2 pausiert** (5. der ursprünglich 5
  Notenbanken Fed/EZB/BoJ/PBoC/BoK) — Quelle ist die Bank-of-Korea-eigene ECOS-API,
  URL-Format bereits recherichert, braucht aber einen registrierten Key UND die
  Registrierung selbst ist bis 24.07.2026 ausgesetzt (die Bank of Korea fährt vom
  29.06.–24.07.2026 einen offiziellen Penetrationstest/"Mock Hack" gegen ECOS,
  Instabilität ist laut eigener Ankündigung erwartet — SSL-Zertifikat bei eigener
  Prüfung echt und gültig, kein Hinweis auf Kompromittierung). Revisit nach dem
  24.07.2026.
- **On-Chain-Metriken (MVRV/NUPL/Realized Price): ERLEDIGT (2026-07-08).**
  `api/onchain.py` nutzt die **CoinMetrics Community API**
  (`community-api.coinmetrics.io`, kein API-Key nötig, Rate-Limit 10 Req/6-Sek.-
  Fenster) für `CapMVRVCur` (MVRV), `CapMrktCurUSD`, `SplyCur`, `PriceUSD`. NUPL und
  Realized Price/-Cap sind dort selbst nicht frei ("forbidden" bei Live-Test), werden
  aber **mathematisch exakt** hergeleitet (keine Näherung): `NUPL = 1 − 1/MVRV`,
  `RealizedCap = MarketCap/MVRV`, `RealizedPrice = RealizedCap/Supply`. Live
  verifiziert: MVRV 1,196, NUPL 0,164, Realized Price 53.046 $ vs. Kurs 63.458 $ —
  intern konsistent. **Wichtig:** die API kennt keinen `order`-Parameter (Standard ist
  aufsteigend nach Zeit) — `page_size` mit Puffer abfragen und den letzten Eintrag
  nehmen, nicht `page_size=1`. **SOPR wurde endgültig verworfen** (vier Anbieter
  geprüft: BGeometrics, CoinMetrics, Glassnode, CryptoQuant zeigen alle dasselbe
  Muster — frei im Dashboard, API nur ab Professional-/Premium-Stufe; strukturell
  nicht aus Bestandsgrößen wie MVRV herleitbar, da Transaktions-Ebene-Daten nötig).
  Kein Revisit-Trigger.
- **BTC-Log-Regression-Risk-Modell: ERLEDIGT (2026-07-08).**
  `indicators/calculations.py::compute_btc_log_regression_risk()` — Log-Log-lineare
  Regression (Power-Law) über die gesamte BTC-Historie seit Genesis (2009-01-03),
  liefert Abweichung vom Regressions-Trend in Standardabweichungen + einen Risiko-Wert
  0–1. Bewusst **nicht** die Replikation einer kommerziellen proprietären Formel,
  sondern ein eigenes, einfaches statistisches Modell. Historie-Beschaffung brauchte
  eine eigene Recherche: CoinGecko (365-Tage-Grenze, live bestätigt), Kraken
  (720-Kerzen-Hardlimit, live bestätigt mit `since=2015` getestet) reichen beide nicht
  — **Blockchain.com's Charts-API liefert die volle Historie seit Genesis**, kostenlos,
  kein Key. Live gegen vier historische Extrempunkte (2017/2018/2021/2022 Top/Bottom)
  geprüft — alle Richtungen korrekt.
- **On-Chain Exchange-Reserven/Stablecoin-Supply: ERLEDIGT (2026-07-08).**
  `api/onchain.py::get_btc_exchange_flows()` nutzt CoinMetrics
  (`FlowInExNtv`/`FlowOutExNtv`) für Netto-Exchange-Flow (Zufluss = potenzieller
  Verkaufsdruck, Abfluss = Akkumulation/Self-Custody).
  `api/onchain.py::get_stablecoin_supply()` nutzt DefiLlama
  (`stablecoins.llama.fi`, kein Key) für USDT/USDC-Gesamt-Supply (wachsende
  Stablecoin-Supply gilt als "trockenes Pulver" am Seitenrand). Beide kostenlos, live
  verifiziert.
- **Derivate (Open Interest/Long-Short-Ratio): ERLEDIGT (2026-07-08).**
  Neues Modul `api/derivatives.py` — Open Interest von Binance, Bybit und OKX
  (Diversifikation über drei Börsen statt Einzelquelle), Long-Short-Ratio von Binance.
  Alle öffentliche Endpunkte, kein Key nötig. Ergänzt die bereits vorhandenen
  Kraken-Funding-Rates (Kap. 8, AZ-1-Heuristik) um eine breitere Derivate-Sicht.
- **Ereignis-Kalender (FOMC-Termine + US-Präsidentschaftszyklus): ERLEDIGT
  (2026-07-08).** Neues Modul `agent/cycles.py`, bewusst getrennt von den übrigen
  `api/*.py`-Modulen, da **keine** Live-API nötig ist: `FOMC_MEETING_DATES_2026` ist
  eine statische, öffentlich Jahre im Voraus veröffentlichte Liste
  (federalreserve.gov/monetarypolicy/fomccalendars.htm, live verifiziert) — braucht
  **jährliche manuelle Pflege**, kein automatischer Abruf. Der
  Präsidentschaftszyklus-Kontext (`get_presidential_cycle_context()`) ist reine
  Datumsrechnung (US-Wahlen sind laut Verfassung immer im November eines durch 4
  teilbaren Jahres) mit einer deskriptiven historischen Tendenz je Zyklusjahr (Jahr 1
  schwächstes, Jahr 3 stärkstes) — **explizit keine Prognose-Garantie**, nur
  Kontext-Information für Groq. Ein zunächst mit erwogener FRED-Release-Calendar-Weg
  (`release_id=101`, "FOMC Press Release") erwies sich als Fehlspur: lieferte ~187
  tägliche Pseudo-Termine statt der ~8 echten Jahressitzungen. **Noch nicht
  verdrahtet** — reine Datenschicht, gleiches "Datensicht vor Nutzung"-Muster wie der
  Rest dieses Abschnitts. Weitere Ereignistypen (NFP/CPI-Release-Termine, US-Wahltermine
  selbst, Schuldenobergrenze) wurden bewusst **nicht** in dieser Slice ergänzt (Umfang
  als "kleinerer Punkt" begrenzt) — bei Bedarf später erweiterbar, gleiches
  statisches Muster.
- **Spot-ETF-Flows (IBIT/FBTC/ARKB/BITB/GBTC etc.) — offen, bedingt pausiert
  (2026-07-08).** Mehrere echte Blockaden gefunden: Farside Investors durch
  Cloudflare-Bot-Schutz blockiert; bitbo.io lädt Flow-Daten per JavaScript nach (kein
  statischer Endpunkt); SoSoValue ohne dokumentierte freie API; CoinGlass
  kostenpflichtig; Dune Analytics API-Zugang im Gratis-Tier unklar. Eine
  Eigenkonstruktion über Shares-Outstanding-Änderungen (Yahoo Finance/Alpha Vantage)
  wäre technisch möglich, aber deutlich komplexer. **Nutzer-Bedingung:** nur
  weiterverfolgen, falls sich zeigt, dass diese Werte für die Agent-Entscheidungen
  essenziell sind.
- **Trueflation — verworfen (2026-07-08).** Kein kostenloser API-Zugang (nur
  kostenpflichtige "API Access"-Stufe), Web-Dashboard ist kein Ersatz für
  `api/macro.py`. Zusätzlich wich der eigene "Echtzeit"-CPI-Wert beim Live-Test
  massiv vom offiziellen BLS-Wert ab (1,79 % vs. 4,20 % YoY). Revisit falls ein
  echtes Gratis-API-Tier eingeführt wird.

**Wichtige Klarstellung zu allen Punkten oben:** "ERLEDIGT" heißt hier ausschließlich
die **Datenbeschaffung**. Ob/wie diese Werte tatsächlich in `agent/krypto/regime.py` oder den
Groq-Prompt (`agent/krypto/analyst.py::build_facts()`) einfließen, ist ein separates,
weiterhin offenes Thema (Kap. 16).

**Staleness-Schwellen für Makro-/On-Chain-Daten: ERLEDIGT (2026-07-08).**
`staleness.py::is_macro_value_stale()` mit vier Kategorien: Zinsen/Wirtschaftsdaten
60 Tage (Notenbank-Sitzungsrhythmus/Meldeverzug), On-Chain 4 Tage, bestehende
BTC-Dominanz/Fear&Greed (`krypto_makro`) 2 Tage. **Bekannte Einschränkung, bewusst
nicht gelöst:** `fetched_at` ist ein Zeitstempel fürs ganze Zeilen-Upsert
(COALESCE-Merge in `agent/krypto/pipeline.py::_update_macro_snapshot`), nicht pro Feld —
echte feldgenaue Frische bräuchte eine Schema-Erweiterung (pro Feld ein eigenes
"zuletzt erfolgreich aktualisiert"). Noch nicht in UI/Facts verdrahtet.

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
- **U-10** Marktscan-Vorschläge (Kap. 13): **ERLEDIGT (2026-07-09, Schreibweg am
  selben Tag nachgebessert).** Neuer Tab "Marktscan" (`ui/marktscan_view.py`) zeigt
  neu entdeckte Kandidaten mit Score-Aufschlüsselung und optionaler P-5-Begründung;
  "In Watchlist übernehmen" schreibt den Eintrag jetzt **direkt** in
  `Basisinfos/config.yaml` (`config.py::add_watchlist_entry()` — chirurgische
  Text-Einfügung statt voller YAML-Neuserialisierung, IMMER mit Backup + Nachher-
  Validierung, fällt bei Fehlschlag auf den ursprünglichen copy-paste-YAML-Weg
  zurück, siehe Kap. 13 MS-1), "Verwerfen" markiert einen Kandidaten dauerhaft als
  nicht relevant.
- **U-11** Regime-Anzeige (Kap. 14): aktuelles Marktregime sichtbar; manueller Override
  wählbar und — solange aktiv — permanent als Warnhinweis eingeblendet.
- **U-12** Datenquellen-Gesundheitsstatus `[TEILWEISE ERLEDIGT, Idee 2026-07-08]`:
  Erweiterung von P-10 — nicht nur einzelne veraltete Werte in der jeweiligen Ansicht
  kennzeichnen (bereits umgesetzt), sondern eine **zentrale, aggregierte Übersicht**,
  welche Datenquellen-Abhängigkeiten (CoinGecko, Kraken, Groq, künftig FRED/
  Eastmoney-PBoC/alternative.me) gerade fehlschlagen oder unerwartet reagieren —
  inkl. seit wann und mit welchem Fehler. Ziel: der Nutzer erfährt aktiv, wenn eine
  Quelle "nicht mehr wie gewünscht/erforderlich funktioniert" (Zitat), statt es
  zufällig in einer einzelnen Ansicht zu bemerken oder es unbemerkt zu bleiben, bis
  ein Signal falsch/unvollständig wird. Anlass: beim Live-Test mehrerer Makro-Quellen
  (Kap. 8) traten mehrfach stille Qualitätsprobleme auf (z. B. ISM-Ersatzquelle mit
  offensichtlich falschen Werten, inkonsistente Trueflation-Pricing-Angaben) — ein
  Mensch musste das manuell bemerken. **Minimalfix ERLEDIGT (2026-07-09):**
  `main.py` schreibt zusätzlich in eine rotierende Logdatei (`data/
  tradinginfotool.log`, UTF-8, 5 MB × 3) statt nur in die Konsole; `scheduler/
  background.py` hat einen `EVENT_JOB_ERROR`/`EVENT_JOB_MISSED`-Listener als zweite
  Verteidigungslinie zu den bereits vorhandenen Try/Except-Blöcken je Job, und deckt
  neu auch verpasste Läufe ab (z. B. Rechner im Standby zur geplanten Uhrzeit).
  **Weiterhin offen:** die eigentliche aggregierte UI-Übersicht, Verlaufsstatistik
  über mehrere Läufe, proaktive Benachrichtigung — aktuell muss der Nutzer die
  Logdatei selbst öffnen.
- **U-13** GUI-Usability-Standards `[Idee 2026-07-09]`: allgemeine UI-Politur für
  alle Tabs, nicht nur einzelne Features — bewusst offen als Kategorie formuliert
  ("etc."), nicht als abschließende Liste. **Sortierbare Spalten ERLEDIGT
  (2026-07-09):** neues `ui/sortable_tree.py::make_sortable()` — Klick auf einen
  Spaltenkopf sortiert (erneuter Klick kehrt um, Pfeil zeigt Richtung),
  zahlenbewusst für Preis-/Wert-/Mengen-/Prozent-Spalten (fehlende Werte immer am
  Ende), sonst alphabetisch — auf allen vier Treeview-Tabs (Watchlist, Portfolio,
  Signale, Marktscan) einheitlich verdrahtet statt Tab-für-Tab-Einzellösungen.
  **Lesbarkeits-Politur ERLEDIGT (2026-07-09):** `ui/theme.py::apply_base_style()`
  bumpt die von Tk benannten Standard-Fonts von ~9pt auf 10pt (wirkt automatisch auf
  klassische Tk- UND ttk-Widgets), größere Treeview-Zeilenhöhe, großzügigere
  Button-/Checkbutton-/Radiobutton-Abstände.
  **Dark Mode ERLEDIGT (2026-07-09).** Neues `ui/settings.py` speichert die
  Präferenz in einer lokalen, nicht versionierten `data/settings.json` (bewusst
  NICHT `config.yaml`, die Datei ist handgepflegt/versioniert). `ui/theme.py` hat
  Light-/Dark-Paletten + semantische Farbfunktionen (`action_color()`,
  `einstufung_color()`, `stale_color()`, ...), die alle vier Tabs statt verstreuter
  Farb-Literale abfragen. **Bewusster Scope-Schnitt:** Dark Mode wird einmal beim
  Start angewendet, kein Live-Umschalten während die App läuft — der Menüpunkt
  "Ansicht → Dark Mode" speichert die Einstellung nur und bittet um einen Neustart.
  ttk wechselt für Dark Mode auf das `clam`-Theme (die einzige eingebaute
  Theme-Basis, die Farb-Overrides unter Windows tatsächlich vollständig übernimmt —
  vista/xpnative zeichnen viele Elemente OS-nativ). Die Charts (matplotlib,
  `ui/charts.py`) ziehen mit: Flächen-/Text-/Gitterfarben passend zum aktiven
  Theme, einzelne Indikatorfarben (EMA/Bollinger/RSI/MACD) bleiben unverändert, da
  auf beiden Hintergründen ausreichend lesbar. Light Mode ist unverändert zum
  vorherigen Stand (keine Regression).

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
  `config.yaml`, da sie nicht personenbezogen/sensibel sind. **Export-Gegenstück
  ERLEDIGT (2026-07-09, Nutzer-Idee):** "Bestände exportieren…" schreibt den
  aktuellen `holdings`-Stand in eine SEPARATE, neue Datei (`Basisinfos/
  Assets_export.xlsx`, ebenfalls nicht versioniert) — bewusst NICHT als In-Place-
  Überschreibung der handgepflegten Original-Assets.xlsx (gleiches Risiko wie ein
  voller `config.yaml`-Rundlauf: Formatierung/Zusatzspalten könnten verlorengehen).
  "Bestände aus Datei importieren…" (Filedialog) rundet das zum echten
  Export→Bearbeiten→Import-Workflow ab, ohne dass der Nutzer die exportierte Datei
  manuell über Assets.xlsx kopieren muss. **Dritter, hybrider Pfad ERGÄNZT
  (2026-07-10, Korrektur zum Umfang siehe unten):** wer einen `BITPANDA_API_KEY`
  besitzt, kann **alle** Bestände (Krypto **und** Aktien/ETF/Rohstoffe, siehe
  Korrektur) UND EUR-Fiat-Cash live von Bitpanda abgleichen ("Datei → Bestände von
  Bitpanda abgleichen", `importer/bitpanda_sync.py::sync_from_bitpanda()`) —
  ausschließlich
  GET-Aufrufe (`api/bitpanda.py::get_fiat_wallets()`/`get_crypto_wallets()`, konform
  mit P-7: über Bitpanda-API-Keys besteht laut Doku grundsätzlich keine Order-/
  Auszahlungsfähigkeit). Neuer `Holding.source`-Wert `"bitpanda_sync"`. Atomar (P-10):
  alle Netzwerk-Aufrufe passieren vor jedem DB-Write, ein Fehlschlag lässt Bestände/
  Cash-Reserve komplett unverändert. Excel-Import/-Export UND das manuelle
  Fiat-Cash-Feld (siehe RM-4, Kap. 3) bleiben vollständig als Backup erhalten —
  bewusst hybrid (Bitpanda-Ausfälle, Nicht-Krypto-Assets sind ohnehin nicht auf
  Bitpanda gelistet). Erkennt eine Bestandsänderung, die zu einem noch offenen Signal
  passt (Einzelsymbol-Aktionen KAUFEN/NACHKAUFEN/VERKAUFEN, Richtung muss exakt
  passen; TAUSCHEN bewusst ausgeklammert), wird das als Vorschlag angezeigt
  (`ui/app.py::BitpandaMatchConfirmDialog`) — nie automatisch bestätigt, ergänzt aber
  die bisher rein manuelle Umsetzungs-Rückmeldung (R-5.7/U-9) um eine Vorausfüllung.
  **Vierter Pfad ERGÄNZT (2026-07-10): Non-Krypto-Sheet.** Design bereits 2026-07-09
  abgestimmt, aber nie umgesetzt — die 13 Non-Krypto-Assets (Aktien/ETF/Rohstoffe,
  Kap. 11) hatten trotz `status: aktiv` **keinen einzigen** `holdings`-Eintrag in der
  DB. Jetzt liest `read_holdings_from_excel()` zusätzlich ein optionales
  "Nicht-Krypto"-Sheet (P-10: fehlt es in der Nutzer-Datei, wird es übersprungen,
  kein Absturz), `export_holdings()` schreibt beide Sheets getrennt nach
  `assetklasse`, jeweils mit derselben "Quelle"-Spalte wie das Krypto-Sheet.
  **Wichtiger Fund beim Live-Test (2026-07-10):** gestakte Krypto-Bestände sind über
  die konsumentenseitige Bitpanda-API strukturell nicht auslesbar — live gegen drei
  Endpunkte geprüft (`/wallets`, `/asset-wallets`, `/wallets/transactions`, alle ohne
  Staking-Feld/Sub-Wallet-Sichtbarkeit; selbst CoinTracking unterstützt laut Recherche
  keine Bitpanda-Staking-Rewards, nur Blockpit über eine vermutlich tiefere,
  nicht-öffentliche Integration). Deshalb gilt: **Zuwächse werden automatisch
  übernommen, Rückgänge NIE** — sie landen in
  `BitpandaSyncResult.decreased_holdings_needs_confirmation` und erfordern eine
  explizite Bestätigung pro Symbol (`ui/app.py::BitpandaDecreaseConfirmDialog`,
  `importer/bitpanda_sync.py::apply_decrease()`) — verhindert, dass gestakte Anteile
  fälschlich als verkauft in die Bestände geschrieben werden. Live verifiziert: ein
  zweiter Sync-Lauf ließ alle neun betroffenen Symbole korrekt unverändert
  (`synced_count: 0`, alle als Rückgang vorgemerkt).
  **Korrektur zum Umfang (2026-07-10, vom Nutzer richtiggestellt):** ursprünglich
  als "nur Krypto" gebaut (`GET /wallets` zeigt nur die Krypto-Gruppe) — Bitpanda
  führt aber Aktien/ETF/Rohstoffe im selben Account, über `GET /asset-wallets`
  unter separaten Gruppen (`commodity`/`index`/`security`/`equity_security`, je mit
  Untergruppen wie `equity_stock`/`equity_etf`). `api/bitpanda.py::
  get_non_crypto_wallets()` deckt das jetzt ab, inkl. zweier live gefundener
  Symbol-Abweichungen (`BITPANDA_NON_CRYPTO_WALLET_SYMBOL_OVERRIDES`: Bitpanda
  "VST-US"→intern "VST", Bitpanda "IS0C"→intern "ISOC"). Dieselbe Zuwachs-/
  Rückgangs-Logik gilt jetzt einheitlich für alle Assetklassen. Nach jedem Sync
  wird automatisch auch `Assets_export.xlsx` aktualisiert (`ui/app.py::
  _sync_bitpanda()`), ohne die Original-Datei anzutasten. Live verifiziert: alle 13
  Non-Krypto-Assets korrekt gefunden und synchronisiert, `synced_count: 0` bei
  einem Wiederholungslauf nach Abgleich mit der echten `Assets.xlsx`.
- **B-6** Persistenz erweitert um: neu vom Marktscan entdeckte Assets (Kap. 13),
  Regime-Verlauf und alle Overrides (Quelle, Grund, Zeitpunkt, Dauer — Kap. 14) sowie
  antizyklische Kaufpläne/Tranchen-Status (Kap. 15) — für Nachvollziehbarkeit (Z-4).

## 11. Roadmap & Erweiterbarkeit

1. **Phase 1** Grundgerüst (Struktur, SQLite, CoinGecko, Basis-UI, Watchlist,
   Erstimport der Bestände aus `Basisinfos/Assets.xlsx`).
2. **Phase 2** Marktdaten & Charts (Indikatoren Kap. 7, Visualisierung).
3. **Phase 3** KI-Agent (Groq statt Claude API, Pipeline Kap. 5, Risikomodul Kap. 3,
   Strategien, Makro). **In Arbeit — Slice 1 ERLEDIGT (2026-07-07):** Signal-Pipeline
   (R-5.0/-5.1/-5.3/-5.5/-5.6/-5.7/-5.8/-5.9/-5.10/-5.11, jeweils mit dokumentierten
   Vereinfachungen, siehe Kap. 5) inkl. neuem „Signale"-Tab (U-4, manueller Trigger,
   noch nicht geplant/automatisch). **Nutzungs-Diskussion ERLEDIGT (2026-07-08):**
   Liquiditäts-Regime, Zyklus-Risiko, AZ-1-Erweiterung (OI/Long-Short), Markt-Kontext
   (Exchange-Flows/FOMC-Kalender) in `agent/krypto/regime.py`/`agent/krypto/anticyclic.py`/
   `agent/krypto/analyst.py` verdrahtet. **Marktscan Stufe B/C/D ERLEDIGT (2026-07-09,
   Kap. 13)** inkl. neuem „Marktscan"-Tab (U-10) und erstem Cron-Job (MS-3).
   Bewusst offen für spätere Slices: volles Makro-Modul (R-5.2, CPI/ISM-Ersatz/
   Trueflation/Leitbörsen), Sentiment (R-5.4), interaktiver Dialog (U-9),
   E-Mail-Benachrichtigung (U-8, inkl. MS-1b), KI-Regime-Override (RG-1b), Drawdown-
   Notbremse (RM-7/Z-3), Hebelpositionen (RM-10/-11, S-6 — siehe Kap. 16).
4. **Phase 4** Portfolio, Benachrichtigungen, Sentiment (X/YouTube).
5. **Phase 5** Backtesting der Strategien gegen historische Daten.
6. **Phase 6** Erweiterung auf Aktien / ETF / Rohstoffe (neue Datenquellen).

> Architektur: Datenquellen, Indikatoren und Strategien als austauschbare Module
> (Plug-in-Prinzip) anlegen, damit Erweiterungen ohne Kern-Umbau möglich sind.

### Zielarchitektur für Multi-Asset-Erweiterbarkeit `[Slice 1: Tracking ERLEDIGT 2026-07-09]`

Code-Analyse (2026-07-09) hat gezeigt: die Kopplung an Krypto ist nicht oberflächlich,
sondern reicht bis in den Kern der Agent-Entscheidungslogik. Bevor Phase 6 (Aktien/
ETF/Rohstoffe) tatsächlich angegangen wird, gilt folgende Zielarchitektur als
Leitplanke — **noch nicht implementiert**, nur festgehalten, damit spätere
Erweiterungen ohne Kern-Umbau möglich sind:

**Bereits assetklassen-agnostisch, direkt wiederverwendbar:**
- Technische Indikatoren (`indicators/calculations.py` — RSI/MACD/EMA/Bollinger
  funktionieren auf jeder Kursreihe unabhängig von der Assetklasse).
- `holdings`-Tabelle (bereits generisch auf `symbol` geschlüsselt, keine
  Krypto-Annahme im Schema).
- UI-Layer (Treeview-Tabs, `ui/theme.py`, `ui/sortable_tree.py`), Excel-Import/
  Export-Mechanismus.
- Makro-Daten (FRED/EZB/PBoC-Leitzinsen, M2, CPI, FOMC-Kalender — relevant für alle
  Assetklassen, nicht nur Krypto).

**Tief Krypto-spezifisch, braucht eigene Module statt Wiederverwendung:**
- Datenquellen (CoinGecko/Kraken/Bitpanda sind reine Krypto-Anbindungen — für
  Aktien/ETF/Rohstoffe braucht es eigene Provider).
- `agent/krypto/regime.py`: Regime-Bestimmung ist im Kern BTC-Dominanz-/BTC-Matrix-basiert,
  nicht neutral verallgemeinerbar.
- `agent/krypto/risk_gate.py`: Stablecoins als Cash-Reserve-Ersatz — hat kein Äquivalent
  bei Aktien (dort wäre Cash echtes Bargeld/Geldmarkt).
- On-Chain-Metriken (MVRV/NUPL/Exchange-Flows) und Krypto-Derivate (OI/Long-Short)
  sind außerhalb von Krypto bedeutungslos.

**Entscheidung (Empfehlung, mit Nutzer abgestimmt 2026-07-09): eigene Agent-Logik
pro Assetklasse, aber EINE gemeinsame Datenbank — keine separate DB je Assetklasse.**
Eine vollständig getrennte Datenbank je Assetklasse würde die eigentliche Stärke
eines Gesamtportfolios verhindern (echte Netto-Vermögensübersicht über
Krypto+Aktien+Rohstoffe hinweg, siehe Portfolio-Tab/Gesamtwert). Stattdessen:

1. **Eigene Agent-Module je Assetklasse** (z. B. `agent/krypto/regime.py`,
   `agent/aktien/regime.py`, jeweils mit eigenem Risiko-Gate/Facts-Schema/
   Groq-Prompt) statt einem Versuch, eine "universelle" Regime-Engine zu bauen, die
   sowohl BTC-Dominanz als auch P/E-Ratios/Sektor-Rotation/VIX abdecken müsste — das
   würde entweder zu einer aufgeblähten If/Else-Kaskade oder zu einem verwässerten
   kleinsten gemeinsamen Nenner führen, der die bereits gebaute Krypto-Feinheit
   (BTC-Zyklus-Risk-Modell, antizyklische Flush-Erkennung, Stablecoin-Cash-Logik)
   verlieren würde.
2. **DB-Schema generalisieren, aber erst beim ersten echten Zweit-Asset**, nicht
   spekulativ vorab: `price_history`/`price_cache`/`marktscan_candidates` hängen
   aktuell hart an `coingecko_id` als Schlüssel — müsste auf eine generische
   `(asset_id, asset_klasse)`-Kennung umgestellt werden. `holdings` bräuchte nur
   eine zusätzliche `asset_klasse`-Spalte zum Filtern/Routen. Bewusst NICHT vorab
   umbauen, ohne einen konkreten zweiten Anwendungsfall vor Augen — sonst besteht
   das Risiko, die Abstraktion falsch zu treffen (YAGNI).
3. **Eine Assetklasse zuerst konkret durchziehen, nicht alle gleichzeitig** —
   Aktien wären der pragmatischste Einstieg (freie Datenquellen wie yfinance
   großzügiger als bei Rohstoffen), bevor ETFs/Rohstoffe folgen.
4. **Günstige, risikoarme Vorbereitung — ERLEDIGT (2026-07-09).** `agent/analyst.py`/
   `anticyclic.py`/`marktscan.py`/`pipeline.py`/`regime.py`/`risk_gate.py` liegen
   jetzt unter `agent/krypto/*` statt `agent/*` (reines Refactoring, keine
   Verhaltensänderung — alle Cross-Imports und Aufrufstellen live geprüft).
   `agent/cycles.py` (FOMC-Kalender/Präsidentschaftszyklus) bleibt bewusst auf
   Top-Level, da bereits assetklassen-neutral.

**Slice 1 (reines Tracking) — ERLEDIGT (2026-07-09), ausgelöst durch echte
Bitpanda-Bestände des Nutzers (Aktien/ETF/Rohstoffe seit dem 29.1.2026-Relaunch des
dortigen steuereinfachen Wertpapierdepots).** Mit dem Nutzer abgestimmt: bewusst NUR
Bestand/Kurs/Wert in Watchlist/Portfolio, KEINE Signale/Regime/Risiko-Gate/Marktscan
für diese Assetklassen (Punkt 1 oben, eigene Agent-Module, bleibt ein separater,
größerer Folge-Slice).

- **Datenmodell:** `config.py::WatchlistAsset` hat jetzt `assetklasse` (Default
  `"krypto"`, rückwärtskompatibel) und `yfinance_symbol`; `coingecko_id` ist optional
  geworden. `database/models.py::PriceSnapshot.coingecko_id` ebenso.
- **DB-Migration (Punkt 2, aber minimal statt vollständig):** nur `price_cache.
  coingecko_id` wurde NULL-fähig gemacht (SQLite-Tabellen-Neubau, da kein `ALTER
  COLUMN`) — `price_history`/`price_history_ohlc`/`marktscan_candidates` bleiben
  bewusst unverändert Krypto-only, da dieser Slice keine Historie/Charts für die
  neuen Assetklassen liefert. Die volle `(asset_id, asset_klasse)`-Generalisierung
  aus Punkt 2 bleibt weiterhin offen für einen künftigen Slice mit Historie/Charts.
- **Kursquelle:** neues `api/yfinance_client.py` (yfinance, kostenlos, kein Key) —
  Bitpanda selbst liefert für diese Assetklassen keine freien Marktdaten (live
  geprüft: `/v1/ticker` deckt nur Krypto + die separate Edelmetall-Wallet ab, die
  echte Wertpapier-Marktdaten-API ist ein B2B-Enterprise-Produkt). `fast_info` statt
  `.history()`, da nur der aktuelle Kurs gebraucht wird; Währung wird aus `fast_info`
  gelesen statt angenommen (P-10).
- **Eigener Scheduler-Job**, isoliert vom Krypto-Preis-Takt (P-10-Prinzip).
- **5 echte Bestände identifiziert und eingetragen:** VST (Vistra Corp, Aktie), OD7N
  (WisdomTree Silver ETC, Rohstoff), VVMX (VanEck Rare Earth & Strategic Metals UCITS
  ETF), 3QSS (WisdomTree NASDAQ 100 3x Daily Short) und DBPK (Xtrackers S&P 500 2x
  Inverse Daily Swap UCITS ETF) — letztere zwei sind laut Nutzer bewusste
  Absicherungs-/Hedging-Positionen, kein Widerspruch zu Z-1.
- **UI:** Watchlist/Portfolio zeigen eine neue "Assetklasse"-Spalte; der
  Bitpanda-Listing-Check (Krypto-spezifisch) wird für Nicht-Krypto-Zeilen übersprungen
  (zeigt "-" statt einer irreführenden "nicht gelistet"-Warnung). Signale-/Marktscan-
  Tab filtern Nicht-Krypto-Assets bereits aus der intern verwendeten Watchlist heraus
  (nicht nur der Anzeige), da `agent/krypto/risk_gate.py::_portfolio_values_usd()`
  sonst deren Wert in die Portfolio-Gesamtsumme für die Allokations-Prozentrechnung
  hätte einfließen lassen.
- **Nebenbefund + Fix:** `config.py::add_watchlist_entry()` hatte einen echten,
  bisher unentdeckten Bug — `Path.write_text()` wandelt unter Windows beim Schreiben
  jedes `\n` in `\r\n` um, was bei jedem Aufruf die GESAMTE `config.yaml` von LF auf
  CRLF umgestellt hätte, nicht nur die neuen Zeilen (Widerspruch zum eigenen
  "byte-für-byte unangetastet"-Versprechen der Funktion). Behoben durch
  `read_bytes()`/`write_bytes()` mit expliziter Zeilenende-Erkennung.
- **Live verifiziert:** alle 5 echten Symbole liefern korrekten Kurs in der
  richtigen Währung, Fehlerisolierung je Symbol bestätigt, bestehende 41
  Krypto-Assets unverändert funktionsfähig, DB-Migration ohne Datenverlust,
  vollständiger End-to-End-Test (App-Start → Watchlist zeigt 46 Assets →
  Preis-Job befüllt `price_cache` → Portfolio berechnet korrekten Wert für einen
  Test-Bestand → Signale-/Marktscan-Tab zeigen unverändert nur Krypto-Assets).

Punkte 2 (volle Schema-Generalisierung) und 3 (eigene Agent-Module je Assetklasse)
bleiben bewusst offen für einen künftigen, separaten Slice.

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

- **MS-1 Ablauf: ERLEDIGT.** (a) **Nachgebessert (2026-07-09, gleicher Tag,
  Nutzer-Wunsch "eleganter lösen"):** ursprünglich war bewusst KEIN automatisches
  Schreiben in `config.yaml` vorgesehen (Sorge: die Datei ist explizit handgepflegt,
  "BEARBEITEN IN NOTEPAD++", ein `yaml.dump()`-Rundlauf hätte Kommentare/Formatierung
  zerstört) — stattdessen nur ein copy-paste-barer YAML-Block. Das wurde durch einen
  **sicheren direkten Schreibweg** ersetzt: `config.py::add_watchlist_entry()` fügt
  den neuen Eintrag als reinen TEXT-Block chirurgisch ans Ende des bestehenden
  `watchlist:`-Blocks an (keine volle YAML-Neuserialisierung, Rest der Datei
  byte-für-byte unangetastet), legt IMMER vorher ein Backup an
  (`.claude/backups/config.yaml.<Zeitstempel>.bak`) und validiert die neue Datei
  danach per `yaml.safe_load()` — bei jedem Fehlschlag automatische
  Backup-Wiederherstellung (Fail-Loud) + Fallback auf den ursprünglichen
  Copy-Paste-YAML-Weg, damit der Nutzer nie ohne Ausweg dasteht. Live-verifiziert:
  Diff für einen echten Add ist exakt die 5 neuen Zeilen, nichts sonst in der
  400+-Zeilen-Datei verändert. (b) Statt automatisch für JEDEN Kandidaten eine volle
  P-5-Begründung zu generieren, ist das **hybrid**: immer per UI-Klick verfügbar,
  zusätzlich per Konfig-Schalter `marktscan.groq_automatisch_kaufkandidaten`
  (Default `false`) automatisch nur für `kaufkandidat`-Treffer — kostenbewusst,
  Groq-Calls bleiben
  dadurch auf eine Handvoll/Tag begrenzt statt einer pro Rohkandidat. (c) Der
  Nutzer entscheidet über die GUI (U-10, `ui/marktscan_view.py`: "In Watchlist
  übernehmen"/"Verwerfen"), ob ein Kandidat übernommen oder verworfen wird —
  wortgetreu umgesetzt (seit dem Schreibweg-Update sogar direkter als ursprünglich
  geplant).
- **MS-2 Datenquelle: ERLEDIGT.** CoinGecko Trending (`/search/trending`) + Top-Gainers.
  **Wichtiger Live-Fund (2026-07-09):** der `order=price_change_percentage_24h_desc`-
  Parameter von `/coins/markets` ist auf der Free-Tier praktisch wirkungslos (liefert
  weiterhin nach Marktkap. sortierte Ergebnisse) — Workaround: mehrere Seiten mit
  `order=market_cap_desc` abrufen und client-seitig in Python nach 24h-Änderung
  sortieren (`api/coingecko.py::fetch_top_gainers()`).
- **MS-3 Frequenz: ERLEDIGT.** 2× täglich, **04:00 und 16:00**, per APScheduler
  `CronTrigger` (`scheduler/background.py::marktscan_job()`, erster Cron-Job im
  Projekt — vorherige Jobs nutzten nur feste Intervalle). Respektiert
  `config.yaml marktscan.aktiv` (Deaktivierung möglich, überspringt sauber statt
  Fehler zu werfen).

### Stufe A — Ausschluss & Einordnung (harte Filter, Tier-Modell)

Kein Einzel-Cutoff, sondern ein **Tier-Modell** (Grenzen vorläufig):

| Tier | Marktkap. | Rolle | Filter |
|------|-----------|-------|--------|
| Tier 1 | ≥ ~1 Mrd. USD | Kern-Diversifikation, Narrativ-Abdeckung | Standard |
| Tier 2 | ~150 Mio.–1 Mrd. | Wachstums-Chance | strenger |
| Tier 3 | ~20–150 Mio. | Small-Cap-Beimischung (High-Risk) | strengste Signale + Budget-Deckel |

- **A(MS)-1 Tier-3-Budgetdeckel: ERLEDIGT.** Small Caps insgesamt max. **10–15 %** des
  Portfolios (regime-abhängig, `config.yaml → regime.profile[*].small_cap_budget_prozent`).
  Ein Tier-3-`kaufkandidat` ohne Budget-Headroom (`agent/krypto/risk_gate.py::
  small_cap_budget_headroom()`, extrahiert aus `pre_check()`) wird in Stufe D auf
  `watchlist_wuerdig` heruntergestuft, statt einen "Kaufkandidaten" zu zeigen, den das
  echte Risiko-Gate sofort veto'en würde.
- **A(MS)-2 Weiche Untergrenze:** noch nicht als eigener Override umgesetzt (bewusst
  ausgelassen in dieser Slice — Coins < 20 Mio. USD fallen aktuell einfach durch
  Stufe A, kein Sonderpfad).
- **A(MS)-3 weitere Filter: ERLEDIGT.** Mindest-Handelsvolumen 24h, Mindestalter
  (Näherung über `atl_date`, siehe unten), Volumen/Marktkap.-Ratio, Stablecoin-Filter
  (Preis-nahe-1-$-Heuristik, kein Categories-API-Call), Duplikat-Check gegen
  bestehende Watchlist UND bereits vom Nutzer entschiedene frühere Kandidaten
  (`agent/krypto/marktscan.py::apply_stufe_a_filters()`/`_duplicate_should_skip()`).
  **Wichtiger Live-Fund:** CoinGecko liefert kein echtes Listing-Datum — das
  Mindestalter wird über das Datum des Allzeittiefs (`atl_date`) angenähert
  (dokumentierter Proxy, wie der bestehende ATR-Close-to-Close-Proxy). Für reine
  Trending-Funde (nicht auch über Top-Gainers gefunden) ist auch das nicht
  verfügbar — solche Kandidaten fallen durch den Alters-Filter.
- **A(MS)-4 Geltungsbereich:** Nur für **Agent-Neufunde**; manuelle Nutzer-Picks bleiben
  unberührt (dürfen riskanter sein).
- **A(MS)-5 Narrativ-Abdeckung** (RWA, KI, DePIN, L1/L2 …): bewusst NICHT bewertet
  (bräuchte einen zusätzlichen `/coins/{id}`-Call pro Kandidat) — als offener Punkt
  dokumentiert, kein stillschweigender Abstrich.
- **A(MS)-6 Handelsbörsen-Check (Bitpanda): ERLEDIGT (2026-07-09, Nutzer-Wunsch,
  noch am selben Tag auf Namensabgleich nachgebessert).** Weder CoinGecko noch
  Kraken wissen, ob ein Coin auf der tatsächlichen Handelsbörse des Nutzers
  (Bitpanda) überhaupt kaufbar ist — ein Marktscan-Kandidat (oder sogar ein bereits
  bestehender Watchlist-Eintrag) kann bei beiden existieren, ohne dort gelistet zu
  sein. `api/bitpanda.py::get_listed_assets()` — öffentlicher, paginierter
  `/v3/assets`-Endpunkt (kein Key nötig, live verifiziert 866 Krypto-relevante
  Einträge), liefert Symbol UND Name je Asset. `is_listed()` prüft primär per
  Symbol (inkl. bekannter Ticker-Abweichungen, `BITPANDA_SYMBOL_OVERRIDES`) und
  fällt bei Fehlschlag automatisch auf einen Namensvergleich zurück — deckt damit
  auch künftig unbekannte Symbol-Mismatches ab, ohne jeden Fall manuell nachtragen
  zu müssen. **Bewusst NUR Warnung, kein Stufe-A-Ausschluss** (ein nicht gelisteter
  Coin kann trotzdem beobachtenswert sein) — sichtbar als eigene Spalte im
  Marktscan-Tab UND im bestehenden Watchlist-Tab (`ui/app.py`), zusätzlich
  verstärkte Warnung im "In Watchlist übernehmen"-Dialog. Einmal pro Scan-Lauf bzw.
  beim App-Start/manuellen Refresh abgerufen, nicht im 3-Sekunden-Poll.
  **Live-Fund + vollständiger Audit:** deckte zunächst einen echten Bestandsfall auf
  — CANTON war in der Watchlist, aber der interne Ticker weicht vom Marktstandard
  ("CC") ab. Vollständiger Namensabgleich aller 41 Watchlist-Assets bestätigte
  danach: CANTON war der EINZIGE Fall, keine weiteren Mismatches gefunden.

### Stufe B / C / D — ERLEDIGT (Slice, 2026-07-09)

- **Stufe B (positive Signale): ERLEDIGT**, vier Kategorien (`agent/krypto/marktscan.py`,
  Rubriken je 0–100, VORLAEUFIG dokumentiert):
  - **Technik:** 24h-Änderung (immer verfügbar) + RSI-14/EMA-20/MACD-Histogramm, falls
    ein gezielter Backfill (nur für Stufe-A-Überlebende, Kosten sparen) genug Historie
    ergibt. EMA-50/-200/Fibonacci/ATR bleiben für Neufunde praktisch immer
    `nicht_verfügbar`.
  - **Fundamental/Qualität:** Tier-Basiswert + Alters-Bonus (gedeckelt) + Position
    innerhalb der Volumen/Marktkap.-Bandbreite.
  - **Markt-/Momentum:** 24h-Änderung + Trending-Rang-Bonus (falls über Trending
    gefunden).
  - **Kontext/Makro (neu, 4. Kategorie):** nutzt `liquiditaets_regime`/
    `zyklus_risiko`/`btc_matrix_state` aus `agent/krypto/regime.py` (dort bereits einmal pro
    Scan-Lauf berechnet, kein Zusatz-Call) — expansive Liquidität/niedriges
    Zyklus-Risiko/Altseason wirken als Bonus, das Gegenteil als Malus.
- **Stufe C (Scoring/Gewichtung): ERLEDIGT.** Kombination der vier Kategorie-Scores
  mit den Gewichten aus dem aktiven Regime-Profil
  (`config.yaml → regime.profile[*].gewicht_*`, neues `gewicht_kontext_makro`-Feld
  in allen 5 Regimen ergänzt, bestehende drei Gewichte proportional angepasst, Summe
  weiterhin 1.0 — höher gewichtet in den Extremregimen, wo Zyklus-/Liquiditätslage am
  aussagekräftigsten ist). Kategorien ohne Score werden aus Zähler UND Nenner
  ausgeschlossen, nicht als 0 gewertet.
- **Stufe D (Schwellenwerte): ERLEDIGT.** `score_gesamt >= 70` → `kaufkandidat`,
  `>= 50` → `watchlist_wuerdig`, sonst `kein_treffer` (VORLAEUFIG,
  `config.yaml → marktscan.schwellen`). Jeder Kandidat wird gespeichert
  (`marktscan_candidates`-Tabelle), auch `kein_treffer` (Audit/Z-4).

**Live-verifiziert (2026-07-09):** echter Scan-Lauf mit 38–42 realen Kandidaten,
korrekt in 2 Kaufkandidaten (APE, EIGEN) + 4–5 watchlist-würdige Funde eingestuft,
vollständige Score-Aufschlüsselung + verwendete Gewichte + Regime-Stand persistiert.
Echte Groq-P-5-Begründung für einen Kaufkandidaten erzeugt (manueller UND
automatischer Pfad). Neuer UI-Tab "Marktscan" (`ui/marktscan_view.py`) inkl.
"Jetzt scannen" (~46s für einen vollen Lauf, UI bleibt reaktionsfähig).

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

**Selbstverifikation & KI-gestütztes Regel-Trimmen (2026-07-10, NEU, Vision formuliert,
Umsetzung begonnen):** Der Agent soll über Zeit lernen können, ob seine eigenen
Signale/Annahmen zutrafen (kurz-/mittel-/langfristig), und daraus **manuelle**
Regel-Anpassungen mit KI-Unterstützung ermöglichen — ausdrücklich **kein** autonomes
Selbst-Justieren, der Nutzer bleibt Entscheider, die KI liefert die datenbasierte
Experten-Einschätzung. Geplanter Ablauf: (1) Regelwerksmanual (siehe unten, ERLEDIGT),
(2) Backward-/Outcome-Tracking vergangener Signale gegen tatsächliche Kursverläufe,
(3) KI-gestützte Trimm-Vorschläge auf Basis der Tracking-Daten, (4) manuelle
Prüfen/Lernen/Anpassen-Zyklen. **Schritt 1 ERLEDIGT:**
`Basisinfos/Regelwerksmanual.md` — nutzerlesbare, destillierte Fassung aller Regeln
(Z-/RM-/RG-/AZ-/R-5.x/S-Serie) mit aktuell konfigurierten Werten, als gemeinsame
Referenz für künftige Anpassungsvorschläge gedacht. Um Kap. 6 ergänzt
(2026-07-10, Nutzer-Wunsch): "Datenabfragen — was wann wie automatisch vs.
manuell passiert" — Tabelle aller Scheduler-Jobs (`scheduler/background.py`,
Takt + Quelle) und aller manuellen GUI-Aktionen (Toolbar/Menü/Tabs), inkl. der
Regel, dass alles Kostenpflichtige/API-Key-gebundene (Groq pro Signal,
Bitpanda-Sync) bewusst manuell bleibt, während kostenlose Marktdaten automatisch
laufen. **Schritt 2 ERLEDIGT (2026-07-10):** `agent/krypto/backward_tracking.py`
prüft vergangene KAUFEN/NACHKAUFEN-Signale gegen die bereits vorhandene
Kurshistorie (`price_history_ohlc` bevorzugt für echtes Intraday-High/Low,
`price_history`-Tagesschlusskurs als Fallback — Transparenz über
`outcome_datenquelle: real|proxy`) — wurde die Take-Profit- oder die
Stop-Loss-Zone zuerst erreicht? Bei Gleichzeitigkeit am selben Tag gewinnt
konservativ Stop-Loss (Z-1). Neuer täglicher Scheduler-Job
(`backward_tracking_job`, 06:00 Uhr, kein eigener Netzwerk-Call — reine
Auswertung bereits vorhandener Daten). Ergebnis in 5 neuen `signals`-Spalten
(`outcome_status`/`_geprueft_am`/`_entschieden_am`/`_realisiertes_crv`/
`_datenquelle`), sichtbar über einen neuen "Signal-Historie"-Button im
Signale-Tab (`ui/signals_view.py::SignalHistoryDialog`) — macht
`db.get_signal_history()` erstmals nutzbar (war seit seiner Einführung toter,
unverdrahteter Code). Live gegen echte BTC-OHLC-Historie verifiziert
(synthetisches Test-Signal korrekt als `stop_loss_erreicht` am erwarteten Tag
aufgelöst, danach wieder entfernt). Schritte 3-4 (KI-Trimm-Vorschläge,
Prüfzyklen) noch offen — brauchen jetzt erstmal echte KAUFEN/NACHKAUFEN-Signale
mit Zeit zum Auflösen als Datengrundlage.

**Risiko-/Basiswerte:**
- Maximaler tolerierter Gesamt-Drawdown (Z-3)? Vorschlag −15 %. Drawdown-Notbremse
  (RM-7) technisch noch nicht umgesetzt (braucht eine Portfolio-Wert-Historie, die
  noch nicht existiert) — im Facts-Objekt an Groq ehrlich als
  `risiko_check.drawdown_notbremse_geprueft: false` ausgewiesen.
- Max. Allokation pro Einzelwert (RM-2): **vorläufig entschieden (2026-07-07)** —
  25 % für taktische Assets, 35 % für Core-Assets (BTC/ETH,
  `config.yaml risiko.max_allokation_pro_core_asset_prozent`), nachdem die reale
  BTC-Allokation (28,4 %) das bis dahin einheitliche 25 %-Limit überschritten hatte.
  **Explizit weiter zu besprechen:** die grundsätzliche Rolle von BTC im Portfolio
  („BTC hat den Lead") — nicht nur die Prozentzahl. Max. Allokation pro Assetklasse
  (RM-3) weiterhin offen.
- Standard-Timeframes für die technische Analyse.
- ~~Claude-Modellversion und Budget/Token~~ — entfällt, KI-Ebene ist Groq (Llama 3.3
  70B, siehe P-8/Kap. 8, kostenlos), nicht Claude API.

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
- **Makro-/Zinsdaten-Quellen, globale M2, On-Chain-Metriken, Log-Regression-Risk,
  Exchange-Flows/Stablecoin-Supply, Derivate, Ereignis-Kalender: ERLEDIGT
  (2026-07-08).** Siehe Kap. 8 für die vollständige, live verifizierte Aufstellung
  inkl. Register verworfener/pausierter Quellen mit Revisit-Bedingung
  (Korea-M2/Spot-ETF-Flows/Trueflation/SOPR). **Staleness-Schwellen für Makro-/
  On-Chain-Daten ebenfalls ERLEDIGT** (`staleness.py::is_macro_value_stale()`, vier
  Kategorien). **Weiterhin offen, für alle diese Punkte gemeinsam:** die eigentliche
  Nutzung in `agent/krypto/regime.py`/`agent/krypto/analyst.py::build_facts()` — reine Datenschicht
  bisher, noch nicht in die Regime-Bestimmung oder den Groq-Prompt verdrahtet.
- X-API & YouTube-API: Kosten, Limits, ToS, Umsetzungsphase.
- **E-Mail-Versand** (Kap. 13): SMTP-Server vs. Mail-API wählen; Zugangsdaten nur in `.env`.
- **Web-Oberfläche für Fernzugriff** `[OFFEN, Idee 2026-07-09]`: zusätzlich zur
  lokalen tkinter-Desktop-App soll perspektivisch ein Web-GUI möglich sein, um von
  einem anderen Gerät (z. B. unterwegs, vom Notebook auf eine auf dem Desktop
  laufende Instanz) auf die App zuzugreifen. Bisher **nirgends im Code oder in der
  Architektur vorbereitet** — kein Web-Framework in `requirements.txt`, `ui/*.py`
  ist direkt an tkinter/ttk gekoppelt (keine Trennung von Anzeige-Logik und
  Business-Logik, die eine zweite Oberfläche einfach wiederverwenden könnte). Vor
  einer Umsetzung zu klären: (a) Web-GUI als vollwertiger Ersatz oder nur
  Lesezugriff (Read-Only-Dashboard) auf denselben SQLite-Stand, (b)
  Authentifizierung/Absicherung, falls von außerhalb des lokalen Netzwerks
  erreichbar, (c) ob das die bestehende tkinter-App ersetzt oder parallel dazu
  läuft. Kein akuter Auftrag, nur als offener Punkt festgehalten.
- **Flush-Erkennung** (AZ-1): **einfache Heuristik ERLEDIGT (2026-07-07)** —
  `agent/krypto/anticyclic.py` nutzt Kraken-Funding-Rates (bereits vorhanden, siehe Kap. 8)
  + Kursrückgang-Geschwindigkeit als groben Hinweis. Die volle AZ-1..AZ-8-
  Klassifikation (unabhängige Nachrichten-/Fundamentalquelle nötig) bleibt offen.
- **Advisory-Konsequenz** (P-7): Eskalationsweg für Schutz-Alerts (Stop-Loss/Drawdown)
  definieren — E-Mail-Priorität, UI-Warnstufe.
- **Umsetzungs-Rückmeldung bei Signalen** (2026-07-07, Nutzer-Idee) — **ERLEDIGT
  (2026-07-09).** `signals` hat vier neue Spalten (`umgesetzt`, `umgesetzt_am`,
  `umgesetzt_menge`, `umgesetzt_preis_usd`; Menge/Preis bewusst optional, auch bei
  `umgesetzt=True`). Im Signale-Tab öffnet ein Button "Rückmeldung erfassen" einen
  Modal-Dialog (Ja/Nein, optional Menge/Ausführungspreis). **Bewusste
  Zusatzentscheidung (hybrid, mit dem Nutzer abgestimmt):** derselbe Dialog bietet
  optional einen ZWEITEN, separat bestätigten Schreibpfad in `holdings`
  (`source="signal_bestaetigung"`) an — er schlägt einen neuen Gesamtbestand aus
  aktuellem Bestand + Aktion (KAUFEN/NACHKAUFEN: +Menge, VERKAUFEN/TAUSCHEN:
  -Menge) vor, den der Nutzer vor dem Speichern frei überschreiben kann; kein
  automatischer, unbestätigter Bestands-Write. TAUSCHEN reduziert nur die
  Quell-Position, das Ziel-Asset wird nicht automatisch angelegt (out of scope
  dieser Slice). `holdings` bleibt weiterhin Stand-ohne-Historie (kein Delta-Log) —
  dieselbe Architektur wie beim Excel-Import, nur ein zweiter Auslöser für
  denselben `upsert_holding()`-Pfad.
  **Nachgebessert nach Expertengegenprüfung (2026-07-09, gleicher Tag):** vier reale
  Lücken gefunden und behoben: (a) Excel-Reimport überschrieb einen per
  Signal-Rückmeldung gesetzten Bestand bisher kommentarlos — `import_holdings()`
  warnt jetzt, wenn ein Symbol mit `source="signal_bestaetigung"` einen
  abweichenden neuen Wert bekommt (überschreibt trotzdem, Assets.xlsx bleibt
  Quelle der Wahrheit, aber sichtbar); (b) deutsches Komma als Dezimaltrennzeichen
  wird jetzt akzeptiert (wie beim Excel-Import); (c) der Bestand-Vorschlag
  berechnet sich live neu, auch wenn die Menge erst NACH dem Ankreuzen der
  Checkbox eingegeben wird; (d) ein negativer vorgeschlagener/eingegebener Bestand
  wird beim Speichern blockiert. **Bewusst offen gelassen (dokumentierte
  Deferrals):** `holdings.source` wird im Portfolio-Tab weiterhin nicht angezeigt
  (Herkunft eines Wertes bleibt in der UI unsichtbar); `signals.umgesetzt*` wird
  bei jeder erneuten Rückmeldung überschrieben, keine Korrektur-Historie. Beide
  sind niedrigpriorisiert und ohne akuten Anlass — Revisit-Bedingung: sobald
  entweder ein Nutzer-Bericht über verwirrende Portfolio-Herkunft ODER ein
  konkreter Bedarf an Rückmeldungs-Historie auftritt.
- **Hebelpositionen als eigene Empfehlungsart** (2026-07-07, Nutzer-Idee): Der Agent
  soll perspektivisch nicht nur Spot-, sondern auch Hebel-Empfehlungen (Long/Short,
  2x/5x, aktiv/passiv gemanaged) inkl. Forecasts geben — zunächst nur Long, später
  auch Short. Betrifft RM-10/RM-11 und S-6 (aktuell `aktiv: false`). Noch nicht Teil
  der Agent-Pipeline (Slice 1 ist Spot-only).

**Steuer & Datenpflege:**
- Steuerregel P-6 (Swap steuerneutral bis Auszahlung) mit Steuerberater verifizieren
  (Sonderfälle: Altvermögen/Spekulationsfrist, Besteuerung von Staking-Erträgen).
- **ERLEDIGT (2026-07-06):** Zwei fehlerhafte Ticker in `Assets.xlsx` direkt in der
  Originaldatei korrigiert (nicht nur in `config.yaml`): Stellar stand als „XML" statt
  „XLM"; Canton Network stand als „CC" statt „CANTON" (beim Phase-1-Import entdeckt).
  Damit ist der `SYMBOL_OVERRIDES`-Workaround in `importer/excel_import.py` nicht mehr
  nötig und wurde entfernt. Backup der Originaldatei vor der Korrektur liegt lokal unter
  `.claude/backups/` (nicht versioniert).
