# Zielgrößen und Erfolgsmaße — woran wir Erfolg messen

**Zweck:** Dauerhaftes Referenzdokument (analog `Regler_Signal_Pipeline_
Abhaengigkeiten.md` und `Test_und_Verifikationsmethodik.md`). Jene beiden
beantworten *wie* die Regler zusammenhängen und *wie* man sauber misst.
Dieses hier beantwortet die Frage davor: **woran erkennen wir überhaupt, dass
das System funktioniert?**

**Entstehung (02.08.2026):** Nutzer-Kritik nach einem Tag mit neun revidierten
Befunden — *„habe wieder das Gefühl, wir probieren einen Grund zu finden"*.
Sie war berechtigt. Der Ablauf war durchgehend: Daten anschauen → Auffälligkeit
finden → Erklärung bauen → nach Gegenprüfung verwerfen. Ohne definierte
Zielgröße ist jede Kalibrierung beliebig, weil sich immer eine Zahl findet, die
sich verbessern lässt, und immer eine Geschichte dazu. Reihenfolge muss sein:
**Ziel → Messgröße → Kalibrierung.** Wir hatten bei Schritt 3 angefangen.

---

## 1. Die Kennzahlen-Hierarchie

### Trade-Ebene

| Kennzahl | Formel | Zielwert |
|---|---|---|
| **Expectancy (R)** | `q × CRV − (1−q)`, q = Trefferquote | **> 0** |
| **R-Multiple** je Trade | Ergebnis ÷ anfangs riskierter Betrag | — (Rohgröße) |

Bei uns ist `outcome_realisiertes_crv` **bereits das R-Multiple**. Die
Datengrundlage für alles Folgende existiert also schon.

### System-Ebene

| Kennzahl | Formel | Skala |
|---|---|---|
| **SQN** (Van Tharp) | `Mittelwert(R) ÷ Standardabweichung(R) × √n` | <1,5 kaum handelbar · 1,5–2,0 durchschnittlich · 2,0–3,0 gut · 3,0–5,0 exzellent |
| **Profit Factor** | Bruttogewinn ÷ Bruttoverlust | >1,0 profitabel · >1,5 gut · >2,0 exzellent |
| **Sharpe / Max Drawdown** | Standard der Backtest-Literatur | kontextabhängig |

**SQN ist für uns die passendste Primärkennzahl:** Sie bestraft Streuung. Zwei
Systeme mit identischem Mittelwert, aber unterschiedlicher Schwankung,
bekommen verschiedene Werte — und genau das unterscheidet ein handelbares von
einem theoretisch profitablen System. Der Faktor √n macht außerdem sichtbar,
dass eine kleine Stichprobe keine gute Bewertung *verdient*.

---

## 2. Wo CRV hingehört — und wo nicht

Der zentrale Satz aus der Recherche:

> *„Edge must be generated through **signal quality** and captured through
> **position sizing** and portfolio construction. The risk-reward ratio that
> emerges is **accepted as a system characteristic rather than manipulated as
> a profit lever**."*

Und:

> *„No stop loss placement or profit target selection will transform random
> entries into a profitable system."*

**CRV ist ein Ergebnis, kein Steuerhebel.** Es beschreibt, was ein Setup
hergibt — es erzeugt keine Vorhersagekraft.

| heute im System | fachlich richtig |
|---|---|
| Freigabe-Gate („CRV ≥ 2,0 sonst HALTEN") | **Positionsgröße** — wieviel riskiere ich hier |
| isolierte Schwelle je Einzelsignal | **verrechnet mit Trefferwahrscheinlichkeit** → Expectancy |
| systemweit statisch | **regimespezifisch** |

Das deckt sich mit der eigenen Recherche vom **29.07.**, die bereits
festhielt: *„CRV allein sagt NICHTS über Profitabilität aus"*, samt der
Warnung vor **adverser Selektion** durch einen reinen CRV-Filter — und mit
Zahlen (17,5 % gegen 45,9 % Trefferquote), die am 02.08. unabhängig
reproduziert wurden (17,4 % gegen 46,1 %). **Das Wissen fehlte nie, nur die
Umsetzung.**

---

## 3. Besonderheiten für LLM-gestützte Systeme

Die Forschung zu LLM-Trading-Agenten (2024–2026) nennt drei Fallstricke, die
unser System unmittelbar betreffen:

**a) Multiple Testing.** *„Backtests are fragile under multiple testing,
selection bias, transaction costs, market impact, and nonstationarity."* Wer
zehn Hypothesen prüft und die überlebende behält, hat keinen Befund, sondern
den besten von zehn Zufällen. Genau das ist am 02.08. passiert. Die Zahl der
getesteten Hypothesen gehört deshalb **mitprotokolliert** (Verfahren dafür:
Deflated Sharpe Ratio, Bailey/López de Prado).

**b) Knowledge-Cutoff-Kontamination.** *„Long backtests routinely overlap
with model knowledge cutoffs, allowing memorized information to substitute
for actual decision-making."* Ein LLM, das historische Zeiträume bewertet,
kennt deren Ausgang möglicherweise. **Für uns heißt das: Nur Vorwärts-Messung
zählt.** Unser Backward-Tracking ist genau deshalb methodisch richtig gebaut —
es bewertet ausschließlich Signale, die vor dem Kursverlauf entstanden sind.

**c) Kumulierte Rendite ist ein verrauschter Indikator.** *„Cumulative return
is a noisy proxy for stock-selection skill that may reflect market beta or
style exposure rather than genuine agent skill."* Deckt sich exakt mit der
eigenen Methodenlehre 2.5.7 (mechanische Basislinie je Bucket) — ohne
Vergleich gegen einen Zufallseinstieg misst man Marktphase.

### Welche Kennzahl bei „träger" LLM-Bewertung?

Die Recherche vom 29.07. hielt fest, dass selbstberichtete LLM-Konfidenz
strukturell wenig differenziert (flache/nicht-monotone Konfidenz-Treffer-
Beziehung ist der **Erwartungsfall**, nicht der Ausreißer). Die Konsequenz
aus der aktuellen Literatur: **nicht die Selbsteinschätzung messen, sondern
das Verhalten.** Die Benchmarks arbeiten mit *behavioral metrics* —
ausdrücklich genannt: **hold ratio**, Order-Anzahl, Turnover.

Für uns bedeutet das: Die „Entscheidungsfreudigkeit", die wir am 02.08. ad hoc
gemessen haben (Anteil echter Aktionen je Tag), ist keine Hilfsgröße, sondern
**die etablierte Kennzahl** für genau diese Frage — belastbarer als jede
`confidence_pct`. Sie sollte dauerhaft mitgeführt werden.

---

## 4. Zielvorgabe für dieses System

1. **Primärziel: SQN über alle real ausgeführten Trades > 1,5.**
   Rechenbar aus `outcome_realisiertes_crv`. Erst ab diesem Wert ist ein
   System praktisch handelbar.
2. **Nebenbedingung: Expectancy > 0** — notwendige, aber nicht hinreichende
   Bedingung. (Stand 02.08.: real ausgeführte Hebel-Trades liegen bei
   **−0,43 R**, also weit davon entfernt.)
3. **CRV wandert von der Freigabe in die Positionsgröße.** Als Gate ersetzt
   durch Expectancy = CRV × geschätzte Trefferquote des CRV-Bandes.
4. **Behavioral: hold ratio** dauerhaft mitführen, statt sich auf
   `confidence_pct` zu verlassen.

### Pflichtangaben bei jeder Auswertung

- **Auflösungsquote je Gruppe.** Weite Stops werden zu 0,2 % aufgelöst, enge
  zu 31 % — wer Trefferquoten über Gruppen mit unterschiedlicher Stop-Weite
  vergleicht, vergleicht Selektionsgrade (Fehler vom 02.08.).
- **Anzahl der geprüften Hypothesen** in dieser Untersuchungsrunde.
- **real vs. hypothetisch** getrennt ausweisen (Veto-Schatten sind kein
  Ersatz für ausgeführte Trades — am 02.08. waren 468 von 560 Fällen
  hypothetisch).
- **Mechanische Basislinie** mit identischen Parametern (Methodik 2.5.7).

---

## 5. Was daraus folgt

Die vier heute (02.08.) gebauten Gates sind sauber verifiziert, wirken aber
auf 0,5–5,5 % der Signale, während das CRV-Gate 72–79 % filtert — und dieses
Gate misst nachweislich die falsche Größe. **Reihenfolge für den Umbau:**

1. SQN und Expectancy als Kennzahlen berechnen und anzeigen (Messung, ändert
   nichts am Verhalten)
2. Genügend reale Trades sammeln, um beide belastbar zu schätzen
3. Erst dann CRV-Gate durch Expectancy-Gate ersetzen

Schritt 1 ist sofort umsetzbar und ohne Risiko. Schritt 3 ohne Schritt 1 wäre
wieder Kalibrierung ohne Zielgröße.

---

## Quellen

- System Quality Number (Van Tharp): https://nexusfi.com/a/risk-management/system-quality-number-sqn
  und https://quantmonitor.net/system-quality-number-sqn/
- Strategie-Kennzahlen-Übersicht: https://strategyquant.com/doc/strategyquant/results-overview/strategy-analysis-metrics/
- CRV als Systemeigenschaft statt Hebel: https://blog.traderspost.io/article/risk-reward-ratio-trading-systems
- Warum feste RR-Ziele scheitern: https://blog.pfhmarkets.com/trading-risk-management/risk-reward-ratio-strategy-rrr-trading/
- Deflated Sharpe Ratio (Bailey/López de Prado): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551
- Probabilistic Sharpe Ratio / Minimum Track Record Length: https://portfoliooptimizer.io/blog/the-probabilistic-sharpe-ratio-hypothesis-testing-and-minimum-track-record-length-for-the-difference-of-sharpe-ratios/
- LLM-Trading-Agenten, Metriken und Fallstricke: https://arxiv.org/pdf/2510.02209 (StockBench),
  https://arxiv.org/pdf/2510.07920 (Profit Mirage: Information Leakage),
  https://arxiv.org/html/2605.19337 (Agentic Trading)
- Eigene Vorrecherche 29.07.: Memory `reference_externe_recherche_konfidenz_crv_risikofaktoren_29_07`

---
---

# 6. Gesamtplan (04.08.) — und warum die bisherigen Anläufe im Deadloop endeten

**Anlass, wörtlich:** *„bevor wir irgendwas weiter bauen brauchen wir einen
Gesamtplan und müssen prüfen ob wir mit den bestehenden mitteln diesen
überhaupt erreichen — das ist nicht das erste mal das wir das Thema
aufgreifen."*

Richtig. Task #598 hat am 02.08. bereits eine Dead-Loop-Synthese erstellt.
Dieser Abschnitt ersetzt sie nicht, sondern beantwortet die dort offen
gebliebene Frage: **welcher Plan führt zum Ziel, und reichen die vorhandenen
Mittel dafür?**

---

## 6.1 Die Deadloop-Mechanik — belegt, nicht vermutet

Der Deadloop entsteht nicht durch fehlende Erkenntnisse. Er entsteht, weil
**Regeln in Dokumenten stehen statt im Code**.

**Beweis am eigenen Fall.** Am 02.08. wurde in
`Test_und_Verifikationsmethodik.md` 2.5.7 festgehalten:

> *„Eine Basislinie muss MATCHED sein — gleiche Richtung, gleicher Stop,
> gleiches CRV, gleicher Zeitraum."*

Am 03.08. wurde `basislinie_erwartungswert()` gebaut. Sie ignorierte den
Zeitraum. Der Fehler wurde am 04.08. als **neuer Befund** hergeleitet — mit
Stunden Aufwand und einem Vorzeichenwechsel von 0,30 R.

**Die Regel existierte. Sie war nur nicht durchsetzbar.**

### Sieben Fehler, eine Familie

An zwei Tagen siebenmal dieselbe Ursache — Signal- und Vergleichsseite
ungleich behandelt:

| | Fehler | Auswirkung |
|---|---|---|
| 1 | Basislinie 2 Jahre, Signale 3 Wochen | 0,30 R, Vorzeichen kippt |
| 2 | Basislinie zählt Unaufgelöste, Signale nicht | Asymmetrie #617 |
| 3 | Bänder gegen horizontlose Formel | dreht ab CRV 2,5 das Vorzeichen |
| 4 | Basislinie ab Einstiegstag (Entry = Schlusskurs) | Basislinie zu niedrig |
| 5 | Perzentil über LONG+SHORT, Auswertung getrennt | ungleiche Quartile |
| 6 | entartetes Intervall [0,0–0,0] galt als belastbar | falsches „belastbar" |
| 7 | 163 simulierte gegen 86 aufgelöste Trades | „Ausstiegs-Hebel 0,73 R" — real **0,079 R** |

**Fehler 7 ist der teuerste**, weil er eine Handlungsempfehlung trug: Der
Ausstieg wurde als größter Qualitätshebel bezeichnet und für die nächste Phase
vorgeschlagen. Auf denselben 86 Signalen gemessen beträgt der Abstand zwischen
tatsächlicher Verwaltung (−0,299 R) und mechanischem Ausstieg (−0,219 R)
**0,079 R** — ein Zehntel des behaupteten Werts.

### Die Gegenmaßnahme: Regeln in den Code, nicht ins Dokument

| Regel | heute | muss werden |
|---|---|---|
| Basislinie matched (Richtung/Stop/CRV/Zeitraum) | Doku 2.5.7 | Pflichtparameter, Funktion bricht ohne ab |
| Population je Kennzahl benannt | nirgends | Feldname trägt die Population |
| kein Vergleich zweier Populationen | Doku | Kennzahl trägt ihre Grundgesamtheit mit |
| entartete Intervalle | seit `b04d0f7` im Code | erledigt |

**Ohne diese Umstellung ist jeder Plan der nächste Deadloop.**

---

## 6.2 Wo wir stehen — geprüfte Zahlen, je Population benannt

Jede Zahl trägt ihre Grundgesamtheit. Das Fehlen genau dieser Angabe war die
Ursache von Fehler 7.

### Qualität

| Population | n | EW | Basislinie | Beitrag |
|---|---|---|---|---|
| **A: handelbare Trades, Mark-to-Market für laufende** | 113 | **−0,104 R** | −0,361 R | **+0,257 R** |
| Teilmenge: nur aufgelöste | 86 | −0,299 R | — | — |

**Für EW > 0 fehlen 0,104 R.** Das entspricht einem Signalbeitrag von 0,361 R
statt 0,257 R — **+41 %**.

### Volumen (7 Tage, Hebel)

| Posten | n | Anteil |
|---|---|---|
| SHORT verworfen (Broker-Vorgabe, kein Hebel) | 281 | 56,5 % |
| **gar keine Zonen erarbeitet** | **119** | **23,9 %** |
| Gate/Veto | 49 | 9,9 % |
| LLM wählt HALTEN trotz Zonen | 38 | 7,6 % |
| **handelbar** | **10** | **2,0 %** |

### Gemessene Hebelgrößen

| Hebel | Ertrag | Quelle |
|---|---|---|
| Ausstieg | **+0,079 R** | 86 Trades, identische Population |
| Selektion schärfen | bis +0,55 R, **senkt aber das Volumen** | durchgelassen +0,784 gegen Veto +0,235 |
| Screening-Score kalibrieren | **kein messbarer Effekt** | Event-Study, nicht monoton |

**Befund: Es gibt keinen großen Hebel.** Die Lücke zum Break-even beträgt
0,104 R, und kein einzelner gemessener Mechanismus liefert sie.

---

## 6.3 Machbarkeitsprüfung je Stufe

| Stufe | Was nötig wäre | Mit vorhandenen Mitteln? |
|---|---|---|
| **0 Daten** | Intraday-Auflösung (Haltedauer ~1 Tag, Daten sind Tageskerzen) | **NEIN** — keine Quelle angebunden, Kontingent an aktiven Tagen bei 96 % |
| **1 Vorfilter** | Score, der diskriminiert | **NEIN** — misst nicht; Neubau braucht Stufe 0 |
| **2 LLM1** | mehr verwertbare Zonen statt 23,9 % ohne These | **TEILWEISE** — Prompt-Änderung möglich, Wirkung unbekannt |
| **3 Gate** | lernendes Gate statt fester Schwellen (Meta-Labeling) | **NEIN** — 10 handelbare Signale/Woche, 113 bewertet gesamt |
| **4 Ausstieg** | bessere Exit-Regel | **JA**, Ertrag aber nur 0,079 R |
| **5 Positionsgröße** | Kelly scharfschalten (#606) | **JA** — entschieden, nicht umgesetzt |
| **Messung** | Regeln im Code statt im Dokument | **JA** — sofort machbar |

### Die unbequeme Schlussfolgerung

**Mit den vorhandenen Mitteln ist EW > 0 nicht sicher erreichbar.** Drei der
sieben Stufen sind blockiert, durch dieselben zwei Ursachen:

1. **Zu wenige Signale** — 10 handelbare pro Woche. Jede lernende Stufe
   (Meta-Labeling, Score-Kalibrierung) braucht ein Vielfaches.
2. **Zu grobe Zeitauflösung** — bei ~1 Tag Haltedauer sind Tageskerzen an der
   Auflösungsgrenze. Vier der sieben Fehler oben sind Symptome davon.

**Das ist kein Grund aufzuhören, aber ein Grund, das Ziel neu zu ordnen:**
nicht „EW > 0 durch bessere Selektion", sondern zuerst **Durchsatz und
Auflösung** — ohne sie kann keine Stufe lernen.

---

## 6.4 Der Plan (UEBERHOLT durch 6.6 - dort steht der Lebenszyklus-Plan)

### Phase 1 — Deadloop-Schutz (sofort, ~1 Tag)

Ohne diese Phase wiederholt sich alles.

| | Maßnahme | Prüfbar an |
|---|---|---|
| 1.1 | Basislinien-Funktionen: Zeitraum/Richtung/Stop/CRV als **Pflichtparameter**, Abbruch statt stillem Default | Test: Aufruf ohne Fenster wirft |
| 1.2 | Jede Kennzahl trägt ihre Population im Feldnamen | Export-Feldnamen |
| 1.3 | Kennzahlen-Panel vor jeder Änderung notieren | Protokoll je Änderung |

### Phase 2 — Durchsatz (die eigentliche Blockade)

Ziel: von 10 auf 30+ handelbare Hebel-Signale pro Woche, **ohne Filter zu
lockern**.

| | Maßnahme | Erwartung | Risiko |
|---|---|---|---|
| **2.1** | **Die 23,9 % ohne Zonen untersuchen** — warum erarbeitet das LLM keine These? | unbekannt, **größter nie untersuchter Posten** | keins, reine Messung |
| 2.2 | Watchlist verbreitern (RC5 aus #598: enge Watchlist, dieselben Symbole wiederholt) | mehr unabhängige Signale | Kontingent, LLM-Budget |
| 2.3 | Multi-Asset-Batch-Frequenz (Maßnahme 5 aus #598, seit 02.08. offen) | mehr Spot-Signale | Budget |

**2.1 ist der Einstieg** — kostet nichts und ist der einzige große Posten, der
nie untersucht wurde.

### Phase 3 — Auflösung (Voraussetzung für alles Lernende)

| | Maßnahme | Blockiert durch |
|---|---|---|
| 3.1 | Stundendaten prüfen: Quelle, Kosten, Volumen | Recherche |
| 3.2 | Wenn machbar: Screening-Eingang auf echtes 4h-Fenster | 3.1 |

### Phase 4 — Ernte (erst wenn 2 und 3 stehen)

| | Maßnahme | Ertrag |
|---|---|---|
| 4.1 | Positionsgröße scharfschalten (#606) | ohne sie erreicht keine Verbesserung das Depot |
| 4.2 | Ausstiegsregel | +0,079 R |
| 4.3 | Meta-Labeling: Gate lernt aus Ergebnissen | erst ab ~300 bewerteten Trades |

### Was ausdrücklich NICHT weiterverfolgt wird

| | Grund |
|---|---|
| Nur-Long lockern | reale Broker-Vorgabe, keine Regel |
| CRV-Schwelle senken | am 02.08. entschieden, am 04.08. nicht widerlegt |
| Screening-Score kalibrieren | diskriminiert nicht; Neubau erst nach Phase 3 |
| Filter lockern für mehr Volumen | jede Ablehnung ist messbar schlechter als das Durchgelassene |

---

## 6.5 Zeitrahmen, ehrlich

| Phase | Dauer | Abhängig von |
|---|---|---|
| 1 Deadloop-Schutz | ~1 Tag | nichts |
| 2 Durchsatz | 1–2 Wochen | 2.1 zuerst messen |
| 3 Auflösung | offen | externe Datenquelle |
| 4 Ernte | Wochen bis Monate | Phase 2 und 3 |

**Kein Schritt aus Phase 4 lohnt vor Phase 2.** Wer bei 10 Signalen pro Woche
an der Selektion optimiert, kalibriert auf Rauschen — genau der Deadloop, aus
dem dieser Abschnitt herausführen soll.

---

## 6.6 Der Gesamtplan über den Signal-Lebenszyklus (04.08., ersetzt 6.4)

**Grundlage:** Nutzer-Vorgabe vom 04.08. — *fehlende Daten werden simuliert, um
Regeln zu bestätigen, nicht abgewartet* (siehe
`feedback_simulieren_statt_auf_daten_warten`). Damit fällt der Grund weg, an
dem die letzten drei Anläufe hängengeblieben sind.

### Die acht Stufen, Ist-Zustand und Lücke

| # | Stufe | was heute gemessen wird | **was fehlt** | Weg dorthin |
|---|---|---|---|---|
| 1 | **Screening** erzeugt Kandidaten | `score_gesamt`, `trigger_zweig` | Score **diskriminiert nicht** (Event-Study 04.08.); Einzelkomponenten (`score_details_json`) nicht im Export | Komponenten exportieren, dann simulativ prüfen welche trägt |
| 2 | **Auswahl** (Budget-Allocator) | nichts über die 5.170 nie aufgerufenen Kandidaten | ob die Auswahl **besser als Zufall** ist — nie gemessen | mechanische Simulation ab `screened_at`, ausgewählt gegen nicht ausgewählt |
| 3 | **LLM1** setzt Zonen + action | outcome, Zonen, Konfidenz | **23,9 % erarbeiten gar keine Zonen** — Ursache unbekannt; Zonen*qualität* nie bewertet | Begründungskategorien auswerten; Zonen gegen ATR/Struktur prüfen |
| 4 | **Gate/Veto** entscheidet | Beitrag je Gruppe (durchgelassen +0,784 / Veto +0,235) | **die Ausschuss-Hypothese**: gibt es im Geblockten eine identifizierbare gute Teilmenge? | synthetische Validierung + Holdout (unten) |
| 5 | **LLM2** (Z.ai) prüft gegen | Übereinstimmungsquote | ob die Übereinstimmung **prädiktiven Wert** hat — nie gemessen; nur 24 % Abdeckung | Beitrag getrennt nach Übereinstimmung/Abweichung |
| 6 | **Laufzeit** | `outcome_status`, Überholung | `halte_kriterium` wird **gesetzt, aber nie gegen den Verlauf ausgewertet** (941 Zielpreise, 57 Mindestziel-Treffer) | Auswertung nachrüsten |
| 7 | **Ausstieg** | R-Multiple aus Zonen | **Kosten fehlen vollständig** — siehe unten | Kostenmodell in die R-Rechnung |
| 8 | **Messung** | Systemgüte, Bänder, Basislinie | steht seit 04.08. | — |

### Was wir vergessen haben: die Kosten

**In keinem R-Multiple stecken Funding, Gebühren oder Spread.** Weder im
Backward-Tracking noch in einer der Simulationen.

Das ist kein Detail, sondern Standard: In der Backtest-Literatur zu Krypto-
Perpetuals gilt, dass Ausführungsverzögerung, Funding, Gebühren und Slippage
die berichtete Performance aufblähen — *„funding payments can turn a profitable
strategy into a losing one if the position is held while funding repeatedly
moves against it"*.

Größenordnung, gerechnet mit unseren echten Werten (Hebel median 3,0×,
Stop median 4,42 % → `Kosten in R = Kostensatz ÷ Stop-Abstand`):

| Kostenart | Annahme | in R |
|---|---|---|
| Gebühren Ein+Ausstieg | 0,1 % / 0,3 % / 0,5 % | 0,023 / 0,068 / 0,113 |
| Funding | 0,03 %/Tag × 3 Tage | 0,020 |
| Funding | 0,10 %/Tag × 7 Tage | 0,158 |

**Spanne 0,04 bis 0,27 R** — gegen eine Break-even-Lücke von **0,104 R**. Der
vergessene Kostenblock kann also kleiner oder **doppelt so groß** wie das Ziel
sein, das wir zu erreichen versuchen.

**Wichtig zur Einordnung:** Der Hebel vervielfacht die Funding-Kosten in
R-Rechnung *nicht* — Gewinn und Funding skalieren beide mit dem Nominalwert.
Entscheidend sind Haltedauer und Stop-Abstand, nicht der Hebel.

**Was zur Quantifizierung fehlt:** `funding_rate_aktuell` steht in
`HebelTrigger`, ist aber nicht im Backtest-Export. Die Gebührensätze von
Bitpanda für Hebelprodukte sind nirgends hinterlegt.

### Weitere Export-Lücken (Daten vorhanden, nicht exportiert)

| Feld | wofür es fehlt |
|---|---|
| `funding_rate_aktuell` | Kostenmodell |
| `score_details_json` | welche Score-Komponente trägt |
| `oi_change_pct_lookback` | Merkmal für die Ausschuss-Analyse |
| `long_konten_anteil_prozent` | dito |

Alle vier sind reine Export-Ergänzungen ohne Verhaltensrisiko.

---

### Der Ablauf

**Phase 0 — Ehrliche Grundlinie (zuerst, sonst messen wir gegen falsche Zahlen)**

| | Maßnahme | warum zuerst | Stand |
|---|---|---|---|
| 0.1 | Vier fehlende Felder in den Export | ohne sie ist 0.2 nicht rechenbar | offen — die Annahme stimmte nicht, 0.2 war ohne sie rechenbar |
| 0.2 | **Kostenmodell in die R-Rechnung** (Funding + Gebühren + Spread) | kann die Break-even-Lücke verdoppeln — jede Zielaussage davor ist unbelastbar | **erledigt 04.08.** — Lücke verdoppelt sich tatsächlich (0,104 → 0,233 R). Details in 6.7 |
| 0.3 | Basislinien-Funktionen: matched-Parameter als **Pflicht**, Abbruch statt Default | Deadloop-Schutz, siehe 6.1 | offen |

**Phase 1 — Die Ausschuss-Hypothese (der Kern deines Konzepts)**

Frage: Gibt es im geblockten Bestand (464 Fälle mit Zonen) eine über Merkmale
identifizierbare Teilmenge, deren Beitrag mindestens dem der durchgelassenen
entspricht?

Ablauf, in dieser Reihenfolge:

| | Schritt |
|---|---|
| 1.1 | **Synthetische Validierung zuerst**: künstliche Signalmengen mit *eingebauter* guter Teilmenge erzeugen. Findet das Verfahren sie wieder? Findet es eine, wo keine ist? Das kalibriert die Falschtrefferquote, bevor echte Daten angefasst werden. |
| 1.2 | Erst dann die 464 echten Fälle, Suche auf der ersten Hälfte (bis 22.07.) |
| 1.3 | Prüfung auf der zweiten Hälfte, unangetastet |
| 1.4 | Erfolg nur bei: Teilmenge ≥ durchgelassene **und** Volumen steigt |

**Warum 1.1 der entscheidende Schritt ist:** Der Holdout hat nur 17 Symbole.
Ob ein gefundenes Muster echt ist, kann er allein nicht klären. Die Simulation
mit *bekannter Wahrheit* kann es — sie sagt, wie oft das Verfahren etwas
findet, wo nichts ist. Genau dieses Vorgehen hat am 04.08. den
Competing-Risks-Schätzer widerlegt, wo echte Daten schwiegen.

**Phase 2 — Die unbeantworteten Stufen** (jede für sich klein, zusammen der Rest)

| | Frage | Methode |
|---|---|---|
| 2.1 | Warum erarbeitet LLM1 bei 23,9 % keine Zonen? | Begründungskategorien + Regime auswerten |
| 2.2 | Ist die Allocator-Auswahl besser als Zufall? | mechanische Simulation ab `screened_at` |
| 2.3 | Hat die Z.ai-Übereinstimmung prädiktiven Wert? | Beitrag getrennt nach Urteil |
| 2.4 | Wird `halte_kriterium` je eingelöst? | Zielpreis gegen Verlauf |

**Phase 3 — Ernte** (erst wenn 0–2 stehen)

Positionsgröße (#606), Ausstiegsregel, gleitendes Gate. Alle drei setzen eine
ehrliche Grundlinie voraus — ohne Phase 0 optimieren sie auf zu gute Zahlen.

| | Maßnahme | Stand |
|---|---|---|
| 3.1 | Positionsgröße #606 (Kelly-Empfehlung + RM-1-Obergrenze) | entschieden 04.08., nicht gebaut |
| 3.1b | **Spot auf CRV-Positionsgröße umstellen** (Gate behalten nur beim Hebel) | **gebaut und verifiziert 04.08.** — stufenlose Abstufung, CRV 2,0 → 20 % / 3,0 → 40 % / 4,0 → 60 % / ab 6,0 volle Größe. Noch nicht deployed |
| 3.2 | **Ausstiegsregel** — Trailing-Stop ab +1R, Abstand 1R | **gemessen und gebaut 04.08.** — EW −0,176 → −0,084 R, SQN −3,07 → −1,59; Block-Bootstrap [+0,051; +0,131] R. Notification-Verdrahtung offen |
| 3.3 | **Gleitendes Gate = Expectancy-Gate = CRV-Breakeven-Bänder** | Messung steht, kein Aufrufer |

**3.1b/3.3 — was am 04.08. beim Umschreiben dieses Plans herausgefallen war**

Beides war gemessen und entschieden und stand dann in keiner Phase. Damit es
nicht ein drittes Mal passiert (nach „Komplementarität" und diesen beiden),
hier ausdrücklich:

| Befund | Zahl | Code-Stand |
|---|---|---|
| **Spot**: CRV gehört in die Positionsgröße, nicht ins Gate | SQN 0,63 → **1,36** (03.08.) | nicht umgesetzt |
| **Hebel**: CRV gehört ins Gate, nicht in die Größe — gegenläufig! | SQN **3,25** gegen 1,25 (03.08.) | bestehendes Verhalten ist richtig |
| **CRV-Schwelle 2,0**: trennt signifikant, **aber die Kante liegt nicht dort** | +0,558 R, p<0,0001, n=491; Sprung bei CRV **4,0** (31,9 % → 51,0 %), 04.08. | `CRV_MINIMUM = 2.0` unverändert |

> **Die drei Namen sind eine Sache.** `compute_crv_breakeven_baender()` misst
> `q > 1/(1+CRV)` — und *Expectancy > 0* ist algebraisch genau das. „Gleitendes
> Gate", „Expectancy-Gate" und „CRV-Breakeven-Bänder" bezeichnen denselben
> Mechanismus. Er ist **gemessen, aber von keinem Gate aufgerufen**: einziger
> Aufrufer ist `extract_notebook_diagnose.py`. Das ist die Wirkebene-Lücke in
> einem Satz.

**Die CRV-Schwellenfrage wird NICHT separat entschieden.** CRV ist aus den
Zonen ableitbar und damit eines der 49 Merkmale in Phase 1. Die Suche dort
prüft es mit Falschtrefferkontrolle und symbolgeblocktem Bootstrap — also
sauberer, als eine Einzelmessung es könnte. Ein separater Anlauf wäre nach
der Abbruchregel eine Messung ohne abhängige Entscheidung.

**Verbindung zur Roadmap aus Abschnitt 5:** Deren Schritt 1 (SQN/Expectancy
messen) ist fertig, Schritt 2 (genug reale Trades) ist der Deadloop, den
Phase 1 umgeht, Schritt 3 (CRV-Gate durch Expectancy-Gate ersetzen) ist
Punkt 3.3 hier. Es ist dieselbe Roadmap, nur feiner aufgeteilt.

**3.2 Die Ausstiegsregel — warum sie hierher gehört und nicht nach vorn**

Gemessen am 04.08.: Signale lösen nach **2,57 T** auf, gehandelt wird nach
**0,30 T** (75 % unter einem Tag). Zugleich standen **50 % bei +1R, aber nur
17,6 % kamen an** — wer bis zur Barriere hält, gibt regelmäßig zurück, was
schon da war.

**Beides zusammen heißt: der Ausstieg ist ein echter Hebel, aber er ist noch
nicht entscheidbar.** Es fehlt die Grundlage:

| | fehlt |
|---|---|
| a | Ein Feld, das eine **Zieldauer** trägt. `halte_kriterium_bucket` ist eine Ablauffrist, `mindestziel_zeitraum_tage_geschaetzt` eine Volatilitätsrechnung — beide keine Strategieangabe, und sie widersprechen einander |
| b | Eine **Messung des Ist-Ausstiegs** — die Entscheidung liegt heute vollständig außerhalb des Systems |
| c | Die Volatilität taugt **nicht** als Dauer-Prognose (belegt in 6.7, Trennschärfe 95 %, rho ≈ 0 mit echtem σ) |

**Deshalb bewusst NACH Phase 1.** Der Ausstieg verändert das Ergebnismaß, an
dem der Vorfilter kalibriert wird. Beides gleichzeitig zu bewegen macht jede
Kalibrierung unbeurteilbar.

> **Feste Messkonvention bis dahin:** Der Vorfilter wird gegen *„Barriere
> erreicht innerhalb 14 Tagen, Bewertung zum Schlusskurs"* kalibriert — das
> Maß von `compute_systemguete()`. Diese Konvention wird während Phase 1
> **nicht** geändert. Wird sie später geändert, sind alle Phase-1-Ergebnisse
> neu zu rechnen; das ist der Preis und er ist bewusst akzeptiert.

**Einstiegsdaten sind NICHT der Engpass — geprüft am 04.08.**

Feldinventur auf der kalibrierbaren Population (86 durchgelassene und 327
vetote aufgelöste Hebel-Signale):

| | Anzahl |
|---|---|
| **auf beiden Seiten ≥ 60 % befüllt — für Phase 1 brauchbar** | **49 Felder** |
| davon zu 100/100/100 % | `confidence_pct`, `trigger_score`, `forecast_bull/base/bear_prob_pct`, `top_grund_1–5_kategorie`, `regime`, `richtung`, `trade_thesis_typ`, `halte_kriterium_*`, alle Zonen |
| einseitig, für real/schatten-Vergleich **unbrauchbar** | `hebel_final`, `eigenkapitalbedarf_*`, `liquidationspreis_geschaetzt_usd` (0 % im Schatten) — strukturell, sie entstehen erst nach dem Gate |
| zu dünn | Z.ai-Felder (15–26 %), `mindestziel_*` (8–23 %), ATR (0 % auf aufgelösten) |

**Damit ist Phase 0.1 kein Vorläufer von Phase 1.** Die vier dort genannten
Exportfelder werden für die Ausschuss-Hypothese nicht gebraucht; 49 Felder
liegen an. Phase 0.1 bleibt sinnvoll, aber sie blockiert nichts.

### 2.3b LLM2 (Z.ai) — Planung, kein Bau (Stand 04.08.)

> **KORREKTUR einer eigenen Fehlmessung vom selben Tag.** Ich hatte
> `zai_gegenpruefung_urteil` gegen den Erwartungswert gestellt und daraus
> geschlossen, LLM2 trage nichts bei. **Das war eine Kategorienverwechslung.**
> Die Doku ist eindeutig: LLM2 ist ein *reiner Konsistenz-Check* zwischen der
> Kurzbegründung des Primärmodells und den bereits vorhandenen Fakten —
> **keine zweite Handelsentscheidung, keine Prognose.** Ein Konsistenzprüfer
> gegen Handelsergebnisse zu messen ist wie zu prüfen, ob eine
> Rechtschreibkorrektur Kurse vorhersagt. Die Zahlen (−0,918 / −1,001 R je
> Urteil) sind deshalb **gestrichen, nicht relativiert** — sie beantworten
> keine sinnvolle Frage.

**Was LLM2 ist und warum es so gebaut wurde** (siehe
`agent/krypto/gegenpruefung.py`, Regelwerksmanual):

Die ursprüngliche Idee, Z.ai eigenes Wissen (z. B. Nachrichtenlage)
einbringen zu lassen, wurde wegen **Halluzinationsrisiko verworfen** — Z.ai
hat keinen echten Nachrichtenzugriff. Stattdessen der enge, prüfbare Auftrag:
*widerspricht die Begründung des Primärmodells den harten Fakten?*
Vom Nutzer bestätigt. **Phase 1 ist rein beobachtend**: kein Risikofaktor,
kein Gate — bewusst, siehe
`feedback_llm_synthese_kein_deterministischer_override`.

**Rahmenbedingung, die den Zuschnitt erklärt:** Z.ai bietet nur wenig
Prompt-Platz, deshalb mehrere getrennte Abfragen statt einer großen. Die
Abdeckung ist damit keine Schwäche der Idee, sondern eine Folge der
Plattform.

**Die Fragen, die vor einem Bau zu beantworten sind — neu gefasst:**

| | Frage | Methode |
|---|---|---|
| a | **Tut der Prüfer, wofür er gebaut ist?** Erkennt er echte Widersprüche zwischen `short_reasoning` und Fakten? | Trefferquote und Fehlalarmquote gegen eine Stichprobe, deren Widersprüche unabhängig festgestellt wurden — NICHT gegen Handelsergebnisse |
| b | ~~Warum liegt die Abdeckung bei 40,7 %?~~ | **beantwortet 04.08.: kein Problem.** Vor dem 27.07. 2,6 % (Feature existierte nicht), ab 27.07. **96,5 %** (576/597). Die 40,7 % waren ein Mittelwert über einen Zeitraum, in dem es die Funktion zur Hälfte nicht gab. Restlücke ~3,5 % ohne Tages- oder Symbolmuster — plausibel Zeitüberschreitungen der asynchronen Prüfung |
| c | Was kostet sie an Budget und Laufzeit? | gegen den Nutzen aus (a) stellen |
| d | Welche Rolle soll sie künftig haben? | offen — laut Regelwerksmanual käme ein Gate nur infrage, wenn sich die Prüfung über Zeit als treffsicher erweist |

**Reihenfolge (Nutzer-Klarstellung 04.08.):** Die drei Ebenen sind eine
**Folge** — *1. deterministisch kalibriert und misst → 2. bessere Datenmenge
und -qualität an LLM1, dadurch bessere Zustimmung → 3. LLM2 als Gegenprüfung
bzw. Bestätigung.* LLM2 prüft das Material, das aus Stufe 2 kommt. Solange
dessen Konfidenz keine Information trägt (−0,021), wird jede Bewertung von
LLM2 am Fehler des Vorgängers gemessen.

**Deshalb: nicht bauen, nicht entfernen, nicht bewerten — bis Stufe 1 und 2
stehen.** Was LLM2 künftig leisten muss, ist noch nicht vollständig
bestimmbar, und das ist ein zulässiger Zustand, kein offener Mangel.

### Abbruchregel gegen den Deadloop (04.08.)

Diese Untersuchungsreihe läuft seit Tagen und hat bisher jede Analyse mit dem
Grund für die nächste beendet. Ab sofort gilt:

1. **Eine Messung wird nur begonnen, wenn vorher benannt ist, welche
   Entscheidung von ihrem Ergebnis abhängt.** Fällt die Entscheidung bei jedem
   möglichen Ausgang gleich aus, entfällt die Messung.
2. **Ein Nebenbefund erzeugt keine neue Messung**, sondern eine Zeile in
   diesem Dokument.
3. **„n zu klein" ist kein Abschluss** (stehende Vorgabe) — aber „Trennschärfe
   simuliert, Effekt nicht vorhanden" ist einer, und zwar ein endgültiger.

### Was NICHT weiterverfolgt wird

Unverändert gegenüber 6.4: Nur-Long lockern (reale Broker-Vorgabe),
CRV-Schwelle senken (02.08. entschieden), Score-Kalibrierung ohne
Komponentenanalyse, Filter pauschal lockern.

**Neu gestrichen:** „auf mehr Daten warten" in jeder Form — siehe die stehende
Vorgabe. Wo Daten fehlen, wird simuliert; wo Simulation die Frage nicht trägt,
ist das zu begründen.

### Quellen zu diesem Abschnitt

- Kosten im Backtest: [Crypto Perpetual Trading Strategy Backtest](https://stingray.fi/blog/crypto-perpetual-trading-strategy-backtest/),
  [How to Backtest a Crypto Strategy](https://coinbureau.com/guides/how-to-backtest-your-crypto-trading-strategy)
- Multiples Testen / Backtest-Overfitting: [The Dangers of Backtesting](https://portfoliooptimizationbook.com/book/8.3-dangers-backtesting.html),
  Bailey/López de Prado (bereits in Abschnitt „Quellen" oben)
- Meta-Labeling als Zielbild für Stufe 4: [Meta-Labeling](https://en.wikipedia.org/wiki/Meta-Labeling),
  [Does Meta Labeling Add to Signal Efficacy?](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/)

---

## 6.7 Der Kostenrahmen — Stand 04.08.2026, an der App verifiziert

**Anlass:** Nutzer-Vorgabe — es sollen **Standard-Hebeltrades** werden, kein
Scalping; Kapital und Zeit bilden den Rahmen. Die beobachtete Haltedauer von
~1,1 Tagen ist Information, keine Vorgabe.

### Die gültigen Sätze

**Maßgeblich ist die Kostentransparenz-Unterlage Version 4.0.0 vom
08.07.2026.** An diesem Stichtag wurde umgestellt; die Produktbezeichnung in
der App wechselte dabei mehrfach („Leverage" / „Margin Trading"), die
Gebührenstruktur ist aber eindeutig.

| | aktuell (ab 08.07.2026) | vorher |
|---|---|---|
| Kauf / Trading | **0 %** (in der App bestätigt: „Tradinggebühr 0,00 €") | 0 % |
| **Tagesgebühr** | **0,18 % / Tag**, alle 4 h anteilig (0,03 % je 4 h) | 0,1 % / Tag |
| Staffelung | 0,18 % bis Tag 60 · 0,12 % bis 100 · 0,06 % bis 180 · 0,0312 % ab 181 | keine |
| Schließung | **0,3 %** | 1 % |
| Liquidation | 1 % zusätzlich | — |
| Hebel | 2× / 3× / 5× / 10×, **nur Long** | 2× Long, 1× Short |

**An einem echten App-Screen gegengeprüft** (100 EURCV, 3× Long LINK):
Gesamtposition 300 €, geliehenes Kapital 200 €, Tagesgebühr 0,18 %,
Tradinggebühr 0,00 €, Liquidation bei −28,67 %.

Die Liquidations-Gegenrechnung geht auf und zeigt einen Wartungspuffer:
42,10 LINK × 5,0831 € = 213,99 € Positionswert minus 200 € Schuld =
**14 € Restkapital**. Liquidiert wird also bereits bei ~14 % verbliebenem
Eigenkapital, nicht bei null.

**Bemessungsgrundlage: das geliehene Kapital — an eigenen Daten belegt.**
Weder App noch Produktseite sagen es ausdrücklich; der Helpdesk-Wortlaut nennt
*„0,18 % per day of the Borrowed E-Token"*. Nachgerechnet an **104 echten,
geschlossenen Positionen** aus dem Bitpanda-Transaktionsexport (Tag
`margin_trading.fee`, 315 Buchungen):

Der implizite Satz fällt mit steigender Haltedauer — die Signatur einer
Fixgebühr plus Tagesrate in derselben Buchung. Per Regression getrennt
(`Gebühr / Bezugsgröße = a + b × Haltetage`):

| Bezugsgröße | Fixgebühr geschätzt | offiziell (alte Sätze) | Treffer |
|---|---|---|---|
| **Kredit** | **1,081 %** | **1,00 %** | **ja** |
| Nominal | 0,624 % | 1,00 % | nein, 38 % daneben |

Auf Kreditbasis trifft die geschätzte Schließungsgebühr den offiziellen Wert
nahezu punktgenau. **Alle Zahlen unten rechnen deshalb mit dem geliehenen
Kapital**; die Nominal-Variante steht nur noch als Obergrenze daneben.

*Was die Regression NICHT klären konnte:* die Tagesrate (R² ≈ 0). Die in Krypto
abgebuchten Gebühren werden mit dem Einstandspreis in Euro umgerechnet, was bei
volatilen Coins stark rauscht, und kurze Haltedauern lassen die Fixgebühr
dominieren. **Seit dem Stichtag 08.07.2026 liegen erst 3 Positionen vor** — die
0,18 %/Tag sind offiziell belegt, aber noch nicht an eigenen Daten verifiziert.

### Kosten sind nicht Steuer — die Abgrenzung

Bitpanda ist steuereinfach, die KESt wird automatisch einbehalten. Für diese
Rechnung ist der Unterschied wesentlich:

| | fällt an | Wirkung |
|---|---|---|
| **Gebühren und Finanzierung** | **immer**, auch beim Verlusttrade | verschieben den **Break-even** |
| **KESt** | nur auf **realisierte Gewinne** | verschiebt den Break-even **nicht**, mindert den Ertrag darüber |

Die Steuer macht die Break-even-Analyse also nicht kaputt — sie beantwortet
eine andere Frage („was bleibt übrig") als die hier gestellte („ab wann trägt
sich ein Trade"). Beides darf nicht in einen Topf.

**Stablecoin-Swaps sind in Österreich steuerfrei.** Der Kredit läuft in EURCV,
also sind die Buchungen `margin_trading.borrow` und `.repay` steuerneutral —
sie erscheinen im Transaktionsexport, dürfen aber weder als Kapitalfluss noch
als steuerliches Ereignis gewertet werden. Im Gebühren-Tag steckt keine Steuer
(geprüft: nur eine einzelne verdächtige Buchung, außerhalb der Margin-Tags).

### Die Formel

Einsatz E, Hebel L, damit Nominal N = E × L und Kredit K = E × (L−1). Das
Risiko N × Stop ist 1 R. Die Gebühren fallen auf K an:

```
Kosten in R  =  (L−1)/L  ×  (Schließung + Tagesgebühr × Tage)  ÷  Stop-Abstand
```

**Der Einsatz kürzt sich heraus.** Die Kostenlast in R hängt nur an Hebel,
Haltedauer und Stop-Abstand — nicht an der Positionsgröße. Nur deshalb passt
sie überhaupt in eine R-Rechnung. Implementiert und geprüft in
`agent/krypto/backward_tracking.py::kosten_in_r()` (04.08.).

> **Korrektur zur ersten Fassung dieses Abschnitts (04.08.).** Sie rechnete
> die Schließungsgebühr auf das **Nominal**, die Tagesgebühr auf den Kredit —
> im Widerspruch zur eigenen Regression eine Seite weiter oben, die den
> Fixanteil auf **Kreditbasis** belegt. Der Code rechnet jetzt beides auf den
> Kredit. Die Kosten fallen dadurch um rund 9 % niedriger aus als in der
> ersten Tabelle.

### Kosten am konkreten Beispiel (100 € Einsatz, 3×, Stop 3,94 %)

Stop 3,94 % ist der **gemessene Median** der ausgeführten Hebel-Trades
(n=86, Quartile 2,30 / 5,70 %), nicht mehr ein angenommener Wert.
Risiko: 300 € × 3,94 % = **11,82 €** = 1 R.

| Haltedauer | Kosten | in R | nötige Kursbewegung |
|---|---|---|---|
| **0,3 Tage** (heutige Praxis) | 0,71 € | **0,060** | 0,24 % |
| 1 Tag | 0,96 € | **0,081** | 0,32 % |
| **2,6 Tage** (Signal-Auflösung) | 1,53 € | **0,129** | 0,51 % |
| 7 Tage | 3,12 € | **0,264** | 1,04 % |
| 14 Tage | 5,64 € | **0,477** | 1,88 % |

### Zwei gemessene Haltedauern, die nicht zusammenpassen

| | Median | Verteilung |
|---|---|---|
| **tatsächlich gehandelte Positionen** (n=188) | **0,30 Tage** | 75 % unter 1 Tag, 14 % 1–3 T, 8 % 3–7 T, 3 % über 7 T |
| **Auflösung der Signale** (n=86, davon 62 mit echtem Enddatum) | **2,57 Tage** | Quartile 1,03 / 5,28 T, Max 12,5 T |

**Gehandelt wird heute faktisch Scalping** — drei von vier Positionen sind
binnen eines Tages wieder zu. Die Signale dagegen brauchen im Median 2,6 Tage,
bis eine Barriere fällt. Positionen werden also regelmäßig geschlossen, bevor
die These, auf der sie beruhen, überhaupt entschieden ist.

Das ist ein Befund, keine Vorgabe — aber es ist genau der Gegensatz zur
gesetzten Richtung „Standard-Trades, kein Scalping". **Der Preis dieser
Umstellung ist bezifferbar:** von 0,3 auf 7 Tage kostet **+0,20 R je Trade**.
Gegen die gemessene Spreizung von 0,55 R zwischen durchgelassenen und vetoten
Signalen sind das 37 % der verfügbaren Kante.

### Der Befund

**Der gemessene Erwartungswert von −0,104 R ist BRUTTO.** Die R-Multiples
entstehen aus Zonen — reine Preisbewegung, ohne jede Gebühr.

| Haltedauer | Netto-EW |
|---|---|
| 0,3 Tage (heutige Praxis) | −0,164 R |
| **2,6 Tage (gemessene Signal-Auflösung)** | **−0,233 R** |
| 7 Tage | −0,368 R |
| 14 Tage | −0,581 R |

**Die Lücke zum Break-even ist nicht 0,104 R, sondern beim gemessenen Stand
0,233 R — mehr als das Doppelte.** Sie wächst mit jeder Stunde Haltedauer.

**Was Kosten NICHT kaputtmachen: den Signalbeitrag.** Die Basislinie ist ein
alternativer Trade, kein Nulltarif — sie trägt dieselben Sätze, aber zu **ihrer
eigenen Haltedauer**. Der Signalbeitrag verschiebt sich deshalb nicht um die
vollen Kosten, sondern **genau um die Kostendifferenz beider Seiten**.

> **Kosten kippen die ABSOLUTE Frage („trägt sich das System?"), nicht die
> RELATIVE („ist die Auswahl besser als Zufall?").** Alle Selektionsbefunde
> der Vortage bleiben damit gültig. Die Break-even-Aussagen nicht.

**Diese Differenz ist nicht klein, und ihr Vorzeichen ist unbequem günstig.**
Ein Zufallseinstieg trifft seltener eine Barriere und läuft deshalb häufiger
bis zum Horizont — er zahlt also **länger**. Im E2E-Test (flache Kurse, 5 %
Stop) standen 0,400 R Basislinienkosten gegen 0,160 R Signalkosten; der
Signalbeitrag verbesserte sich dadurch um 0,24 R. Auf echten Daten fällt der
Effekt kleiner aus, weil unaufgelöste Signale per Mark-to-Market ebenfalls bis
zum Horizont laufen und mitzahlen. **Ein Signalbeitrag, der sich durch die
Kostenrechnung verbessert, ist deshalb genau zu prüfen, bevor er zitiert
wird** — er kann echt sein (schnellere Auflösung ist ein realer Vorteil) oder
ein Artefakt der Horizontwahl.

Deshalb bleiben `expectancy_r` und `sqn` brutto und behalten ihre Bedeutung;
`expectancy_r_netto`, `sqn_netto` und `signalbeitrag_r_netto` stehen als
eigene Felder daneben. Ein still korrigierter Wert ließe sich nicht mehr
nachrechnen — und für Spot ist der Satz ausdrücklich **nicht belegt**
(`kosten_belegt=False`).

**Das ist der wichtigste Befund dieser Untersuchungsreihe.** Die Daten lagen
vor, die Rechnung wurde nie gemacht.

### Zwei Hebel, die dieselbe Formel aufzeigt

```
Kosten in R  =  Kostensatz  ÷  Stop-Abstand
```

**Erstens: weitere Stops senken die Kostenlast.** Damit die Kosten unter 0,15 R
bleiben, müsste der Stop bei 3× sitzen bei

| Haltedauer | nötiger Stop |
|---|---|
| 3 Tage | 3,7 % |
| 7 Tage | 6,9 % |
| 14 Tage | 12,5 % |

Der gemessene Median-Stop von 3,94 % trägt rechnerisch **rund 3,3 Tage** —
und liegt damit knapp über der gemessenen Signal-Auflösung von 2,6 Tagen.
Für die angestrebten Mehrtages-Trades reicht er nicht.

**Zweitens: höherer Hebel kostet mehr pro R** — weil mehr geliehen wird,
während das Risikobudget gleich bleibt (Kosten in R, Stop 3,94 %):

| Hebel | (L−1)/L | 1 Tag | 7 Tage | 14 Tage |
|---|---|---|---|---|
| 2× | 0,50 | 0,061 | 0,198 | 0,358 |
| **3×** | **0,67** | **0,081** | **0,264** | **0,477** |
| 5× | 0,80 | 0,097 | 0,317 | 0,573 |
| 10× | 0,90 | 0,110 | 0,356 | 0,644 |

*(Korrigiert eine frühere Aussage in diesem Dokument: bei Bemessung auf das
Nominal wäre der Hebel kostenneutral in R — bei Bemessung auf das Geliehene
ist er es nicht. Von 2× auf 10× steigt die Kostenlast um 80 %.)*

**Zusammen ergibt das ein stimmiges Bild für Standard-Trades:**
Mehrtages-Positionen verlangen **weite Stops, hohe CRV-Ziele und eher
niedrigen Hebel** — das Gegenteil von Scalping. Enge Stops sind doppelt teuer:
häufiger getroffen *und* höhere Kostenlast pro R. Das stützt RM-1b
(Mindeststop 2,5 %) und RM-1c (0,75× ATR) nachträglich mit einer zweiten,
unabhängigen Begründung.

### Die Zeitrahmen-Frage ist eine Kostenrechnung

„1, 7 oder 14 Tage" lässt sich nicht unabhängig vom Stop-Abstand beantworten —
die Kostenformel koppelt beide:

- bei **3,94 % Stop** (gemessener Median) trägt der Trade etwa **3,3 Tage**
- für **7 Tage** braucht es rund **6,9 %** Stop
- für **14 Tage** rund **12,5 %**

**Wer mehrtägige Standard-Trades will, muss die Stops weiten.** Sonst frisst
die Finanzierung die These, bevor sie aufgehen kann.

**Die Messung vom 04.08. macht daraus eine belegte Aussage statt einer
Rechnung:** Der heutige Stop trägt 3,3 Tage, die Signale lösen im Median nach
2,6 Tagen auf, gehandelt wird nach 0,3 Tagen. Die drei Zahlen beschreiben drei
verschiedene Strategien im selben System. Bevor eine Zieldauer festgelegt
wird, muss Lücke 2 („keine Zieldauer am Signal") geschlossen sein — sonst
bleibt jede Vorgabe folgenlos, weil kein Feld sie trägt.

### Was im System dazu fehlt — Stand nach Phase 0.2

| | Lücke | Stand |
|---|---|---|
| 1 | **Kein Kostenmodell** in irgendeiner Messung | **erledigt 04.08.** — `kosten_in_r()`, verdrahtet in `compute_systemguete()` inkl. Basislinie, Export und Anzeige |
| 3 | **Der Hebel geht nicht in die Kostenrechnung ein** | **erledigt 04.08.** — `hebel_final` vor `hebel_vorschlag`, Median je Gruppe, Rückfall auf 3,0 |
| 5 | Die Staffelung (0,18 → 0,12 → 0,06 %) nirgends hinterlegt | **erledigt 04.08.** — `_KOSTEN_HEBEL_STAFFEL`, über die Stufen integriert |
| 2 | **Keine Zieldauer am Signal.** `halte_kriterium_bucket` ist eine Ablauffrist (14/45/120 T), `mindestziel_zeitraum_tage_geschaetzt` eine Volatilitätsrechnung (Median 1,5 T, nur 35 % befüllt). Beide sind keine Strategieangabe und widersprechen einander | **offen** — jetzt schärfer: die gemessene Auflösung liegt bei 2,6 T, die Praxis bei 0,3 T, keiner der beiden Felder sagt das |
| 4 | **Das LLM kennt die Kostenstruktur nicht** und kann sie beim Setzen von Stop und Ziel nicht berücksichtigen | **offen** — der Faktor existiert jetzt deterministisch, die Weitergabe in den Prompt fehlt |
| 6 | **Spot-Kosten sind nicht belegt** — nur 348 von 3578 Trades tragen eine explizite Gebührenbuchung (`vsn_fee`, Median 1,03 % je Seite), bei den übrigen steckt sie im Spread und ist ohne Marktmitte nicht messbar | **offen** — als Annahme geführt und als solche gekennzeichnet (`kosten_belegt=False`) |
| 7 | **Die Tagesrate 0,18 %/Tag ist offiziell belegt, aber nicht an eigenen Daten verifiziert** — seit dem Stichtag 08.07.2026 liegen erst 3 Positionen vor | **offen** — klärt sich mit der Zeit von selbst |

### Der Zeitrahmen 0–5 Tage — Bewertung vom 04.08.

**Vorgabe des Nutzers:** Trades unter einem Tag sollen *möglich* sein, aber
nicht Standard. Der Rahmen ist **0 bis max. 5 Tage**.

> **Korrektur meiner eigenen Darstellung.** Die 7 und 14 Tage weiter oben sind
> **Messhorizonte, keine Sollwerte**. Die daraus abgeleitete Forderung „wer
> Mehrtages-Trades will, muss die Stops weiten" gilt für 7–14 Tage und ist für
> den Rahmen 0–5 Tage gegenstandslos.

**Wir sind bereits im Rahmen:** Signale lösen im Median nach **2,57 Tagen**
auf, **68 %** innerhalb von 0–5 Tagen. Der Stop trägt rechnerisch 3,3 Tage.
Für den Zeitrahmen ist **keine Stop-Änderung nötig**.

#### Die Volatilitätsthese: Mechanismus richtig, als Prognose untauglich

Die Zeit bis zur Barriere folgt der Diffusionsnäherung

```
T  ≈  c × (Stop-Abstand ÷ Tagesvolatilität)²        k := Stop ÷ σ
```

Eigene Simulation (3000 Pfade je Stützstelle, 24 Schritte/Tag): **c ≈ 2,0,
stabil über k = 0,8 bis 2,5.** Der Mechanismus existiert.

Auf unseren Daten trägt er aber **nicht als Vorhersage**:

| Prüfung | Ergebnis |
|---|---|
| Rangkorrelation k² ↔ Haltedauer | +0,300 (n=47) |
| einfacher Permutationstest | p = 0,039 |
| **symbolgeblockt** (16 Symbole) | **p = 0,194 — nicht gesichert** |
| **Trennschärfe, simuliert** | **95 %** — n=47 hätte gereicht |
| mit σ **während** des Trades (nicht vorhersagbar) | rho ≈ **0** (n=26) |

**Da die Trennschärfe bei 95 % liegt, ist p = 0,194 kein Datenmangel, sondern
ein echter Unterschied zum Modell** (simuliertes rho +0,57 gegen gemessene
+0,30). Die Ordnung der Haltedauern lässt sich mit k² nicht herstellen — auch
nicht mit perfekter Kenntnis der Volatilität im Trade.

**Was dagegen sauber herauskommt:** Eichfaktor mit Rückblick-σ **c = 1,18**,
mit tatsächlichem σ **c = 1,88** (nahe der simulierten 2,0). **Die
Volatilität während unserer Trades liegt rund 30 % über der Schätzung aus 20
Rückblicktagen** — Signale feuern in erhöhte Volatilität hinein, deshalb lösen
sie schneller auf als jede naive Rechnung sagt.

**Das ATR-Feld kann das nicht ersetzen:** `atr_relativ_prozent_bei_signal` ist
bei 307 von 1471 Signalen befüllt, aber bei **null aufgelösten** — als
Prädiktor derzeit nicht bewertbar.

#### Warum die kurzen Trades kein Defekt sind

Gehandelt wird bei **0,30 Tagen** Median, 75 % unter einem Tag. Das steht
gegen 2,57 Tage Signal-Auflösung — Positionen werden geschlossen, bevor die
These entschieden ist.

**Daraus folgt aber nicht, dass das falsch wäre.** Der Befund vom 04.08.
(#615/#618) sagt: **50 % standen bei +1R, nur 17,6 % kamen an.** Wer bis zur
Barriere hält, gibt regelmäßig zurück, was schon da war. Ein Ausstieg nach
Stunden kann genau das einsammeln.

> **Belegbar ist heute weder das eine noch das andere** — weil die
> Ausstiegsentscheidung außerhalb des Systems liegt: keine Regel, keine
> Messung, kein Feld. Das ist die eigentliche Lücke, nicht die Haltedauer.

#### Ein Messfehler, der fast durchgegangen wäre

Die erste Volatilitätsmessung ergab 14 % Tagesvolatilität für **jedes**
Kryptosymbol (Quartile 13,44/13,84 — fast eine Konstante). Ursache: die
Kursreihen im Notebook-Export führen **EUR- und USD-Zeilen verschachtelt**
(je 88 bei AIOZ). Gemessen wurde der Sprung zwischen den Währungen —
15,08 % = ln(1/0,86) = der EUR/USD-Kurs.

**Die Produktion ist nicht betroffen** (`lade_kursreihen()` filtert auf USD),
nur Auswertungen direkt auf `preishistorie_je_symbol`. Aufgefallen ist es
allein daran, dass die „Verteilung" keine war.

> **Lehre für künftige Auswertungen des Exports: immer auf eine Währung
> filtern.** Und: eine unplausibel enge Streuung ist ein Messfehler-Signal.

### Quellen

- [Bitpanda Margin Trading — Produktseite](https://www.bitpanda.com/en/margin-trading): 0 % Kauf, 0,18 %/Tag, 0,3 % Schließung, 1 % Liquidation, Hebel 2×–10×
- [Kostentransparenz Krypto, Version 4.0.0 vom 08.07.2026](https://cdn.bitpanda.com/terms-and-conditions/cost-transparency-crypto-bitpanda-en-latest.pdf) (bildbasiert, nicht maschinell auslesbar)
- [Introducing Bitpanda Leverage](https://blog.bitpanda.com/en/introducing-bitpanda-leverage) — alte Sätze (1 % / 0,1 %), historisch
- App-Screen vom 04.08.2026 (100 EURCV, 3× Long LINK) — Gegenprobe der Positions- und Liquidationswerte

---

## 7. Der durchgeplante Ablauf (04.08.2026)

Ausgearbeitete Fassung des Plans aus 6.6. Nutzer-Vorgabe: **„wir sind bei
Hebel — ziehe parallel die anderen Assets mit, damit wir nicht 3 Lösungen
bauen müssen."**

### 7.1 Eine Lösung für alle Assetklassen — geprüft, nicht angenommen

**Merkmalsinventur auf den aufgelösten Zeilen** (Befüllung ≥ 60 % auf beiden
Seiten, 04.08.):

| | Anzahl | |
|---|---|---|
| **gemeinsamer Kern Hebel ∩ Spot** | **43** | trägt eine Lösung |
| nur Hebel | 7 | `trigger_score`, `trigger_zweig`, `hebel_vorschlag`, `richtung`, `trade_thesis_typ`, `llm_model`, `regime_source` |
| nur Spot | 5 | `position_size_eur/usd`, `position_size_note`, `cash_veto`, `groq_model` |

> **43 gemeinsame Merkmale sind der Beleg, dass eine Lösung reicht.** Das
> Suchverfahren bekommt die Merkmalsliste als **Eingabe**, nicht fest
> verdrahtet. Es läuft je Tier mit der jeweils gültigen Liste; der Code ist
> einer.

**Eine Einschränkung, die daraus folgt und die vorher niemand gesehen hat:**
`trigger_score` gibt es **nur beim Hebel**. Die Frage „Komplementarität von
Screening-Score und LLM-Konfidenz" ist damit **nur für den Hebel
beantwortbar** — die Spot-Familie führt den Score nicht in der Signalzeile.
Das ist keine Blockade für Phase 1, aber es begrenzt eine ihrer Teilfragen.

**Kalibrierbare Populationen je Tier** (aufgelöste Fälle, Export 04.08.):

| Tier | Signale mit Zonen | real aufgelöst | Schatten aufgelöst |
|---|---|---|---|
| **hebel** | 941 | **86** | **327** |
| **spot** (alle Klassen) | 681 | **10** | **226** |

> **Spot hat nur 10 durchgelassene aufgelöste Trades.** Die Ausschuss-Suche
> läuft dort auf der Schattenseite (226) technisch identisch, aber der
> Vergleichsanker „Teilmenge ≥ durchgelassene" steht auf 10 Fällen. **Für
> Spot wird deshalb nur ein Richtungsbefund erwartet, keine Entscheidung.**
> Das steht hier vorher, damit es hinterher nicht als Ausrede gelesen wird.

Die Aufschlüsselung nach Assetklasse (Aktien/Rohstoffe/Themen-ETF getrennt)
scheitert derzeit an der Exportseite: `holdings_check` führt keine
`assetklasse`. **Das ist die erste konkrete Aufgabe** — ohne sie bleibt Spot
ein Sammeltopf, und der Fehler vom 29.07. (Mischtopf-Auswertung) wäre wieder
möglich.

### 7.2 Phase 1.1 — was genau gebaut wird

**Zweck: nicht Signale finden, sondern das Suchverfahren vermessen.**

Rechnerisch: 43 Merkmale × ~10 Schwellen = rund 430 Einzelhypothesen, dazu
Paare. Bei naiven 5 % erwarten wir **~21 „Funde" aus reinem Rauschen**. Die
Symbolklumpung verschärft das — am 04.08. gemessen: naiv p = 0,039,
symbolgeblockt p = 0,194 für denselben Zusammenhang.

**Teil A — das Suchverfahren** (läuft später unverändert auf echten Daten)

| | |
|---|---|
| Eingabe | Signale mit Merkmalen + R-Ergebnis + Symbol + Tier |
| Gesucht | Regel über Merkmale, deren Teilmenge einen Signalbeitrag ≥ dem der durchgelassenen hat |
| Tiefe | 1 (Einzelschwelle) und 2 (Paar) — **nicht tiefer**, sonst explodiert der Hypothesenraum |
| Unsicherheit | **symbolgeblocktes Bootstrap**, nie naive Intervalle |
| Basislinie | je Teilmenge eigene, matched (Methodik 2.5.7 — **Pflicht**) |
| Buchführung | Zahl der geprüften Hypothesen wird mitgeführt (Pflichtangabe Abschnitt 4) |

**Teil B — der synthetische Prüfstand**

Erzeugt Datensätze mit der **gemessenen** Struktur: Populationsgrößen je Tier
wie oben, 16–21 Symbole mit der echten Größenverteilung (LINK 11, KAIA 11,
INJ 8, …), korrelierte Merkmale, R-Werte überwiegend −1 / +CRV.

| Welt | Aufbau | gemessen wird |
|---|---|---|
| **H0** | Ergebnis hängt von **keinem** Merkmal ab | **Falschtrefferquote** — wie oft meldet das Verfahren trotzdem einen Fund? |
| **H1** | bekannte Regel definiert Teilmenge mit erhöhtem EW (+0,2 / +0,3 / +0,5 R) | **Trennschärfe** — wie oft wird sie gefunden? |
| **H1-grob** | eingebauter Effekt +2,0 R | **Funktionsprüfung** — muss fast immer gefunden werden |

Daraus wird die Entscheidungsschwelle so geeicht, dass **H0 höchstens 5 %
Fehlalarme** erzeugt.

**Akzeptanzkriterien — vorher festgelegt (Methodik 2.2, Vorher-Hypothese)**

| # | Kriterium | wenn verletzt |
|---|---|---|
| 1 | H0-Falschtrefferquote ≤ 5 % nach Eichung | Verfahren untauglich, nicht die Daten |
| 2 | H1-grob (+2,0 R) wird in ≥ 95 % gefunden | Verfahren defekt — Bau prüfen, nicht Datenlage |
| 3 | Das symbolgeblockte Bootstrap reproduziert den bekannten Fall vom 04.08. (naiv 0,039 / geblockt 0,194) | Bootstrap falsch implementiert |
| 4 | Generator trifft die realen Randverteilungen und Merkmalskorrelationen | Simulation nicht übertragbar |

**Meine Vorher-Hypothese, ausdrücklich vor der Messung notiert:**

> Ich erwarte eine H0-Falschtrefferquote **deutlich über 5 %** bei naiver
> Auswertung (Schätzung 30–60 %, weil 430 Hypothesen auf 16 Symbolclustern
> laufen), und dass die Eichung sie auf 5 % drückt. Für H1 bei **+0,3 R**
> erwarte ich eine Trennschärfe **unter 50 %** — die realistische Effektgröße
> liegt nahe der Nachweisgrenze dieser Stichprobe.

**Geringe Trennschärfe ist ein Parameter, kein Abbruchgrund.**

> **Korrektur der ersten Fassung dieses Abschnitts.** Dort stand: „liegt die
> Trennschärfe unter 50 %, ist Phase 1 nicht entscheidbar — das ist ein
> Abschluss." Das ist die vierte Variante derselben Ausrede („zu wenige
> Fälle" → „Holdout zu klein" → „n reicht nicht" → **„zu wenig
> Trennschärfe"**). Nutzer-Vorgabe, wiederholt am 04.08.: *„Was wir nicht an
> Daten haben, rechnen wir vorwärts und simulieren und testen und bestätigen
> soweit möglich."*

Fällt die Trennschärfe niedrig aus, liefert 1.1 stattdessen **vier Zahlen**:

| | statt „nicht entscheidbar" |
|---|---|
| 1 | **Welche Effektgröße ist mit n=86/327 nachweisbar?** Ein Wert in R, keine Ausrede |
| 2 | **Welches n bräuchte +0,3 R?** Damit wird aus „zu wenig" ein Zielwert, der mit der Signalrate in eine Zeitangabe umrechenbar ist |
| 3 | **Kandidatenregel vorwärts simulieren:** eine schwach belegte Regel gegen synthetische Welten mit den gemessenen Eigenschaften laufen lassen. Hält sie dort, ist das **Teilbestätigung** |
| 4 | **Teilbestätigung wird ausgewiesen**, nicht gegen einen Vollbeweis eingetauscht, der dann ausbleibt |

**Ein Ergebnis mit benannter Unsicherheit ist ein Ergebnis. „Nicht
entscheidbar" ist keines.** Die Abbruchregel aus 6.6 gilt weiter für
*Messungen ohne abhängige Entscheidung* — sie deckt ausdrücklich **nicht** den
Fall ab, dass eine Entscheidung ansteht und die Datenlage dünn ist. Dort wird
vorwärts gerechnet.

### 7.3 Phase 1.2 bis 1.4 — der Ablauf auf echten Daten

| | Schritt | Bindung |
|---|---|---|
| 1.2 | Suche auf der **ersten Hälfte** (bis 22.07.), je Tier getrennt | Verfahren aus 1.1 **unverändert** |
| 1.2a | **Benannter Prüffall**: Komplementarität `trigger_score` × `confidence_pct` — nur Hebel | war am 04.08. schon einmal aus dem Plan gefallen |
| 1.2b | **Benannter Prüffall**: CRV als Merkmal (aus Zonen ableitbar) — beantwortet die offene Schwellenfrage 2,0 gegen 4,0 mit Falschtrefferkontrolle | ersetzt einen separaten Anlauf |
| 1.3 | Prüfung auf der **zweiten Hälfte**, bis dahin unangetastet | kein Blick vorher |
| 1.4 | Erfolg **nur** bei: Teilmenge ≥ durchgelassene **und** Volumen steigt | beides, nicht eines |

### 7.4 Verbindliche Methodik je Schritt

Aus `Test_und_Verifikationsmethodik.md`, hier auf diesen Plan angewendet:

| Methodik | wo sie greift |
|---|---|
| **0** Statusvokabular (5 Stufen) | jede Statusangabe benennt die Stufe — „geschrieben" ≠ „im Betrieb bestätigt" |
| **1.1** Änderungsklassen | 1.1 ist Klasse 2/3 (deterministische Logik) → synthetischer Test **Pflicht**, hartes Vorher/Nachher erwartbar |
| **2.1a** Export-Vollständigkeitscheck | **vor** 1.2, nicht mittendrin |
| **2.2** Vorher-Hypothese | oben notiert, wird nach der Messung ehrlich gegengehalten |
| **2.5** Symbol-/Konzentrationscheck | **vor jeder** Musterinterpretation — der Grund, warum 1.1 überhaupt existiert |
| **2.5.5** Beitrags-Konzentration | zusätzlich zur Anzahl: trägt ein Symbol den halben Effekt? |
| **2.5.7** Basislinie je Bucket | **Pflicht** — jede gefundene Teilmenge bekommt ihre eigene matched Basislinie |
| **2.6** Mehrebenen-Erfolgsmessung | striktes Outcome **und** MFE getrennt ausweisen |
| **2.8** Schwellen rechnerisch herleiten | keine geschätzten Schnitte |

### 7.5 Messkonvention und Statusführung

**Feste Messkonvention für die gesamte Phase 1** (aus 6.6, hier wiederholt
weil zentral): *„Barriere erreicht innerhalb 14 Tagen, Bewertung zum
Schlusskurs"* — das Maß von `compute_systemguete()`. **Wird während Phase 1
nicht geändert.**

Kosten werden **brutto und netto** geführt (6.7). Für die Ausschuss-Suche ist
der **Signalbeitrag** die Zielgröße, nicht der absolute EW — er ist
kostenrobust, weil beide Seiten dieselben Sätze tragen.

**Reihenfolge der Umsetzung:**

| | Schritt | Status |
|---|---|---|
| a | `assetklasse` in `holdings_check` exportieren | offen — Voraussetzung für die Spot-Aufschlüsselung |
| b | Phase 1.1 Teil A + B bauen | offen |
| c | Akzeptanzkriterien 1–4 prüfen | offen |
| d | Entscheidung: 1.2 starten oder Phase 1 abschließen | offen |
