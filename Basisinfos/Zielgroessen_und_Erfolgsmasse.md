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
