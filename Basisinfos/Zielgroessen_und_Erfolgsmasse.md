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

| | Maßnahme | warum zuerst |
|---|---|---|
| 0.1 | Vier fehlende Felder in den Export | ohne sie ist 0.2 nicht rechenbar |
| 0.2 | **Kostenmodell in die R-Rechnung** (Funding + Gebühren + Spread) | kann die Break-even-Lücke verdoppeln — jede Zielaussage davor ist unbelastbar |
| 0.3 | Basislinien-Funktionen: matched-Parameter als **Pflicht**, Abbruch statt Default | Deadloop-Schutz, siehe 6.1 |

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
