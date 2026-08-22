# Zwischenstand Gesamtprojekt — 06.08.2026

**Auftrag:** vollständiger Zwischenstand nach Kapiteln, mit kritischer
Gegenprüfung was fehlt oder ergänzt werden **muss**. Dazu ein Vergleich von
Krypto-Spot und Krypto-Hebel auf Praxistauglichkeit, mit externem Rahmen.

**Statusvokabular** nach `Test_und_Verifikationsmethodik.md` Abschnitt 0 —
„erledigt" wird bewusst vermieden, stattdessen: *gebaut* (Code steht),
*verifiziert* (isoliert getestet), *im Betrieb bestätigt* (an echten Daten
nachgewiesen), *gemessen* (mit Zahl und Unsicherheit).

---

## 0. Die eine Zahl, die alles einordnet

| | n | Erwartungswert | SQN | **Signalbeitrag** |
|---|---|---|---|---|
| **Hebel real** | 126 | −0,106 R | −0,73 | **+0,372 R** |
| Hebel Veto-Schatten | 437 | −0,232 R | −3,19 | +0,213 R |
| **Krypto-Spot real** | 19 | −0,271 R | −0,99 | **+0,337 R** |
| Krypto-Spot Schatten | 309 | −0,123 R | −1,79 | +0,262 R |
| Aktien Schatten | 4 | −1,000 R | — | — |
| Rohstoffe real | 1 | +20,511 R | — | — |

**Die Auswahl trägt, das Ergebnis nicht.** Der Signalbeitrag — der Abstand zu
einem mechanischen Zufallseinstieg mit denselben Parametern — ist in allen vier
belastbaren Gruppen **deutlich positiv**. Der absolute Erwartungswert ist
negativ. Das ist kein Widerspruch: es heißt, das System wählt besser als der
Zufall, in einer Marktphase, in der auch der Zufall verliert.

**Externer Rahmen** ([QuantMonitor](https://quantmonitor.net/system-quality-number-sqn/),
[JournalPlus](https://journalplus.co/metrics/system-quality-number/)): ein SQN
unter 1,5 gilt als „schwer handelbar", 1,5–2,0 als Durchschnitt, ab 2,0 als gut.
Für eine belastbare SQN-Aussage werden **100+ Trades** verlangt, mindestens 30.

Daraus zwei Schlüsse, die den Rest dieses Dokuments strukturieren:

1. **Hebel hat mit n=126 erstmals eine auswertbare Stichprobe.** Krypto-Spot mit
   n=19 hat sie nicht — dort ist *jede* Aussage über Systemgüte verfrüht.
2. **Bei SQN −0,73 ist das System nach externem Maßstab nicht handelbar.** Der
   positive Signalbeitrag sagt, dass die Ursache nicht (nur) die Auswahl ist.

---

## 1. Krypto-Hebel — am weitesten, und das einzige Kapitel mit Daten

### Steht und ist im Betrieb bestätigt

- **Vollständige Pipeline** — Screening → Trigger → Budget-Allocator → LLM1 →
  Risk-Gate → LLM2-Gegenprüfung → Signal → Backward-Tracking
- **Nur-Long-Umbau** (05.08.): der BP-Schalter wirkt nur noch auf E-Mail und
  Anzeige, an genau zwei Lesestellen. Im Betrieb symbolgenau bestätigt.
- **Ausstiegsregel** scharf seit 05.08. — Trailing ab +1R, täglicher Job 7:15,
  Sammel-Mail. **Der einzige belegte positive Hebel:** +0,092 R je Signal,
  Bootstrap [+0,051; +0,131], 100 % positive Ziehungen.
- **Zweistufige Stop-Untergrenze** RM-1b (2,5 % absolut) + RM-1c (0,75 × ATR),
  am 06.08. survivorship-frei unabhängig bestätigt: der Übergang zu klar
  positivem Beitrag liegt bei exakt 2,5 %.
- **Fünf LLM-Fakten** neu (kosten, ausstiegsregel, systemguete, crv_baender)
  plus Regeln 30/31/32. Drei davon im Betrieb angekommen (22/22 Faktensätze).
- **Veto-Schatten-Tracking** — verworfene Signale werden weiterverfolgt, 437
  ausgewertet. Das ist der Grund, warum wir Gate-Fragen überhaupt beantworten
  können.

### Kritische Gegenprüfung — was fehlt

| # | Lücke | Warum das zählt |
|---|---|---|
| **H1** | **Kein Ausführungs-Feedback.** Der Nutzer handelt manuell; ob er einem Signal folgt, wird nicht erfasst. Der Messpunkt „Befolgungsgrad" ist in Methodik 2.11 definiert, aber **nicht implementiert**. | Die gesamte Erfolgsmessung beschreibt *Empfehlungen*, nicht *Trades*. Solange das offen ist, ist unbekannt, wie viel der gemessenen Güte die Realität erreicht. **MUSS vor jedem Abschluss.** |
| **H2** | **Zieldauer existiert nicht.** Zwei Felder widersprechen sich; gemessene Auflösung 2,6 Tage, gehandelte Praxis 0,3 Tage. | Ein System ohne Zeithorizont kann seinen eigenen Ausstieg nicht bewerten — und blockiert die `halte_kriterium`-Auswertung. **Konstruktionsfehler, MUSS.** |
| **H3** | **Konfidenz trägt keine Information** (gemessen 05.08.), wird aber vom Gate R-5.10 als Schwelle verwendet. | Ein Gate, das auf einer nicht diskriminierenden Größe filtert, filtert zufällig. Kalibrierung 64,4 % vorhergesagt gegen 10,3 % tatsächlich. |
| **H4** | **Kein Portfolio-Kontext im Signal.** Das Modell sieht nur das eine Symbol, nie Klumpenrisiko oder Portfoliozustand. | Vier offene Positionen in derselben Wette sind ein Risiko, das kein Einzelsignal zeigt. Offene Achsenfrage. |
| **H5** | **Kein Live-Vergleich gegen den Zufall.** Der Signalbeitrag wird nur in Auswertungen berechnet, nicht laufend überwacht. | Fällt er, merken wir es Wochen später. |

### Abschlussfähigkeit

**Hebel ist das Kapitel, das am ehesten abschließbar ist** — aber nicht mit
„fertig", sondern mit **„messbar geworden"**. Was fehlt (H1, H2) sind keine
Features, sondern Voraussetzungen dafür, dass die vorhandenen Messungen etwas
über die Wirklichkeit sagen.

---

## 2. Krypto-Spot

### Steht

- Vollständige Pipeline analog Hebel, dieselben zentralen Bausteine
  (`risk_gate.py`, `backward_tracking.py` werden von allen fünf Pipelines
  geteilt — das ist eine Stärke, keine Redundanz)
- **CRV-skalierte Positionsgröße** live seit 04.08. (CRV 2,0 → 20 % / 3,0 →
  40 % / ab 6,0 volle Größe), erwartet SQN 0,63 → 1,36
- Tranchen, Cash-Reserve-Ziel, antizyklische Bausteine, Boden-Zielzone
- Regel 36 (CRV-Bänder) am 06.08. auf die dynamische Form umgestellt

### Kritische Gegenprüfung

| # | Lücke | Warum das zählt |
|---|---|---|
| **S1** | **n=19.** Externer Standard verlangt 30 als Untergrenze, 100+ für Belastbarkeit. | **Jede** Aussage über Spot-Systemgüte ist derzeit unzulässig. Auch die positiven. |
| **S2** | **Der Zweck von Spot ist AKKUMULATION — und genau die wird nicht gemessen.** Siehe 2b. | **Die schwerwiegendste Lücke des Projekts.** Wir messen ein Akkumulations-Kapitel mit Trading-Kennzahlen. |
| **S3** | Regel 36 liefert derzeit **gar nichts** — unter dem strengeren Maß („Ziel erreicht" statt „MFE ≥ 1R") bleiben 42 Fälle, kein Band belastbar. | Ehrlich, aber es heißt: der Spot-Analyst hat aktuell keine gemessene CRV-Einordnung. |
| **S4** | Nur 10 aufgelöste durchgelassene Trades. | Alles Weitere ist Richtungsbefund, keine Entscheidung. |

### 2b. Der Kern: Spot ist ein AKKUMULATIONS-Kapitel und wird wie ein Trading-Kapitel gemessen

**Nutzer-Hinweis 06.08., und er trifft den wunden Punkt: AZ-4.**

Das Regelwerk sagt es bereits selbst — **AZ-4 „Gestaffelt, nie all-in: in
Tranchen kaufen, damit ein tieferer Absturz zur Chance statt zum Ruin wird"**,
mit drei gebauten Bausteinen: AZ-4-Tranchen (gestaffelte Kauf-/Verkaufszonen),
Boden-Zielzone für BTC/ETH, Cash-Reserve-Ziel.

**Die Akkumulations-Maschinerie existiert also, ist deklariert und läuft — und
wird mit keiner einzigen Kennzahl gemessen.** Geprüft: im gesamten Code gibt es
keine Durchschnittskosten-Auswertung, keinen DCA-Vergleich, keine
Akkumulations-Metrik.

**Warum R-Multiple und SQN das nicht abbilden können.** Beide messen den
einzelnen, abgeschlossenen Trade: Einstieg, Stop, Ziel, Ergebnis in Vielfachen
des Risikos. Akkumulation hat diese Struktur nicht. Sie fragt:

> Habe ich über den Zeitraum **mehr Einheiten zu einem besseren
> Durchschnittspreis** aufgebaut als ohne das System?

Diese Frage lässt sich mit keinem R-Multiple beantworten — auch nicht mit einem
positiven Signalbeitrag von +0,337 R.

**Der richtige Vergleichsmaßstab ist nicht Buy-and-Hold, sondern DCA.** Das war
mein eigener erster Vorschlag und er war zu grob. Buy-and-Hold ist ein
Einmalkauf; AZ-4 kauft *gestaffelt über die Zeit*. Der ehrliche passive
Gegenspieler zu gestaffeltem Kaufen ist **gestaffeltes Kaufen ohne Signal** —
also Dollar-Cost-Averaging in festen Intervallen.

**Die Messung, die fehlt** (gleiches Kapital, gleicher Zeitraum, gleiche Symbole):

| Kennzahl | AZ-4 (signalgesteuert) | DCA (fester Takt) |
|---|---|---|
| durchschnittlicher Einstandspreis | ? | ? |
| erworbene Menge je eingesetztem Euro | ? | ? |
| eingesetztes Kapital zum Periodenende | ? | ? |
| maximaler Rückschlag der Position | ? | ? |

**Die Daten dafür liegen vollständig vor:** 33 gehaltene Positionen, **alle 33
mit Einstandspreis**, 90 Tage Portfolio-Wert-Historie mit Mengen, bis zu 182
OHLC-Punkte je Symbol. Es fehlt ausschließlich die Auswertung.

> **Das ist der günstigste MUSS-Punkt der ganzen Liste** — keine neue
> Datenquelle, kein neues Feature, kein API-Aufruf. Eine Vergleichsrechnung auf
> vorhandenen Daten. Und sie entscheidet, ob das Spot-Kapitel überhaupt einen
> Zweck erfüllt.

**Konsequenz für die Zielgrößen:** solange diese Zahl fehlt, ist „Spot
abschließen" nicht möglich — nicht weil Features fehlen, sondern weil der
Erfolgsmaßstab des Kapitels nie definiert wurde. Der Signalbeitrag gegen
Zufallseinstieg beantwortet bei Spot eine Frage, die in der Praxis niemand
stellt.

**Offene Grundsatzfrage an den Nutzer:** AZ-4 steht heute unter „Antizyklische
Kauf-Disziplin" — also als *Verhaltensregel beim Kaufen*. Wenn Akkumulation der
**Zweck** des Spot-Kapitels ist, gehört sie zusätzlich in die Zielgrößen als
Erfolgsmaß, nicht nur ins Regelwerk als Kaufdisziplin. Das ist eine Entscheidung
auf Regelwerksebene und wird hier nur benannt, nicht getroffen.

---

## 3. Spot gegen Hebel — kritischer Vergleich mit externem Rahmen

### Der strukturelle Unterschied, den unsere eigenen Zahlen zeigen

```
Kosten in R = (L−1)/L × (Schließung + Tagesgebühr × Tage) ÷ Stop-Abstand
```

Der Einsatz kürzt sich heraus. Die Last hängt an **Hebel, Haltedauer und
Stop-Abstand** — und der Faktor (L−1)/L geht von 0,50 bei 2× auf 0,90 bei 10×.

**Externe Bestätigung** ([Volity](https://volity.io/crypto/crypto-cfd-vs-crypto-spot/),
[YieldFund](https://yieldfund.com/leverage-trading-in-crypto-what-are-the-hidden-costs/)):
Spot zahlt **keine** Finanzierungskosten — die einzige Haltekosten sind
Opportunitätskosten. Bei gehebelten Positionen fallen Gebühren laufend an; in
Bullenphasen können Funding-Raten 0,1 % je 8 Stunden übersteigen, also über
100 % annualisiert allein fürs Halten.

### Was daraus für unser System folgt

| | Krypto-Spot | Krypto-Hebel |
|---|---|---|
| Haltekosten | praktisch null | 0,16–0,40 R je nach Stop und Dauer |
| Break-even-Hürde | Trefferquote gegen 1/(1+CRV) | **plus** Kostenlast |
| Datenlage bei uns | n=19 — nicht auswertbar | n=126 — auswertbar |
| Sinnvoller Zeithorizont | Tage bis Wochen | **0–5 Tage** (Vorgabe) |
| Echte Alternative | **Buy-and-Hold** | keine — ohne Signal kein Trade |
| Liquidationsrisiko | keines | ja |

**Die Asymmetrie ist fundamental und wird im Projekt bisher nicht abgebildet:**

- **Bei Hebel ist der Zufallseinstieg der richtige Maßstab.** Ohne Signal gäbe
  es den Trade nicht. Der Signalbeitrag +0,372 R ist dort die passende
  Kennzahl, und er ist positiv.
- **Bei Spot ist der Zufallseinstieg der FALSCHE Maßstab.** Ohne Signal würde
  man nicht „zufällig einsteigen", sondern **weiter gestaffelt akkumulieren**
  (AZ-4). Unsere +0,337 R Signalbeitrag beantworten dort eine Frage, die
  niemand stellt — siehe 2b.

> **Das ist der wichtigste Befund dieses Zwischenstands.** Wir messen Spot seit
> Wochen gegen einen Maßstab, der die praktische Entscheidung nicht abbildet.
> Und die Praxis steht im eigenen Regelwerk: AZ-4 ist eine Akkumulationsregel.

### Wo das Ziel liegen sollte — Rahmen

Nach externem Maßstab ist ein SQN von **1,5–2,0** Durchschnitt und ab **2,0**
gut. Unsere −0,73 sind weit davon entfernt, aber die Zahl ist mit einer
Marktphase konfundiert.

**Realistischer Zielrahmen, aus unseren eigenen Daten abgeleitet:**

| Kapitel | sinnvolles Ziel | warum |
|---|---|---|
| **Hebel** | Signalbeitrag **dauerhaft > +0,3 R** bei n ≥ 100 je Quartal, und Netto-EW (nach Kosten) **über null** | Der Beitrag steht bereits bei +0,372; die Netto-Hürde ist die eigentliche offene Frage (brutto −0,106, netto −0,233) |
| **Spot** | **DCA über dieselbe Periode schlagen** — besserer Durchschnittspreis bzw. mehr Einheiten je eingesetztem Euro, bei nicht höherem Rückschlag | AZ-4 kauft gestaffelt; der ehrliche Gegenspieler ist gestaffeltes Kaufen ohne Signal, nicht ein Einmalkauf |

**Abschluss-Empfehlung:** Hebel kann mittelfristig abgeschlossen werden, sobald
H1 (Befolgungsgrad) und H2 (Zieldauer) stehen. **Spot kann derzeit gar nicht
abgeschlossen werden** — nicht wegen fehlender Features, sondern weil der
Maßstab fehlt (S2) und die Stichprobe zu klein ist (S1).

---

## 4. Watchlist

**Stand:** 57 Symbole — 44 Krypto, 7 ETF, 4 Rohstoffe, 2 Aktien.
13 „core", 44 „taktisch". Hebel-Prüfung bei **17 von 36** aktiviert.

### Gegenprüfung

| # | Beobachtung |
|---|---|
| **W1** | **Alle 57 stehen auf `beobachtungsstatus = beobachtung`.** Das Feld hat drei Werte (core/ausgemustert/beobachtung), genutzt wird faktisch einer — der Drei-Stufen-Cooldown läuft damit weitgehend leer. |
| **W2** | `hauptgruppe`/`unterkategorie` nur bei **13 von 57** befüllt, und ausgerechnet nicht bei Krypto. Blockiert jede Klumpen-Auswertung. Offene Achsenfrage. |
| **W3** | Die Watchlist ist **kein Engpass** — 44 Krypto sind reichlich (übliche Empfehlung 5–10 Altcoins). Der bindende Faktor ist der Hebel-Toggle (17 von 36), und das ist eine bewusste Nutzer-Entscheidung. |
| **W4** | **CAT ist eine kaputte EUR-Kursreihe** (Renditekorrelation 0,149 gegen Median 0,992). Aktuell ohne Schaden, weil nicht gehalten. Revisit sobald gehalten. |

---

## 5. Screener / Marktscan

**Stand:** 43.853 Hebel-Trigger → 6.612 Kandidaten. Marktscan 2.007 Kandidaten
→ 39 Kaufkandidaten. Reifegrad-Scoring und Erfolgsmessung gebaut.

### Gegenprüfung

| # | Lücke |
|---|---|
| **SC1** | **Der Screening-Score diskriminiert nicht** (Event-Study 03.08.: LONG-Quartile −1,2 / +4,0 / +13,0 / +2,4 pp, nicht monoton; SHORT alle vier bei −19 bis −23 pp). Er entscheidet aber, welche Kandidaten überhaupt ins LLM kommen. **Das ist die größte ungemessene Wirkfläche im System.** |
| **SC2** | **Allocator gegen Zufall nie gemessen** — bis 05.08. strukturell blockiert durch den Nur-Long-Vorfilter. Jetzt möglich, **Wiedervorlage in 2–3 Wochen**. Fällt der Test negativ aus, ist die gesamte Screening-Ebene fraglich. |
| **SC3** | Marktscan-Writeups laufen mit 1 pro Tag sehr dünn; die Verbindung Screener → Schwerpunkte ist geplant, aber nicht umgesetzt (5 offene Designfragen). |

---

## 6. Multi-Asset — hier liegt tatsächlich am meisten brach

**Stand:** Aktien, Rohstoffe, Themen-ETF und Hedge haben je Pipeline und
Analyst. **Risk-Gate und Backward-Tracking sind zentral** in `agent/krypto/`
und werden von allen fünf Pipelines geteilt — das ist saubere Architektur, kein
Duplikat.

**Aber die Datenlage ist praktisch leer:**

| Tier | ausgewertete Trades |
|---|---|
| Aktien | 4 (Schatten), EW −1,000 |
| Rohstoffe | **1** real mit **+20,511 R** |
| ETF | 0 |

### Gegenprüfung

| # | Lücke |
|---|---|
| **M1** | **Der Rohstoff-Wert ist nicht plausibel.** Ein einzelner Trade mit +20,5 R (OD7C, Take-Profit) bei einer Assetklasse, in der am 27.07. bereits ein **OHLC-Skalierungsbug** gefunden wurde. **Vor jeder Multi-Asset-Aussage zu klären.** |
| **M2** | **Kein eigenes Screening** für Nicht-Krypto. Es gibt keine Kandidatenfindung — die Watchlist ist die einzige Quelle. Bei 2 Aktien und 4 Rohstoffen ist das keine Auswahl, sondern eine Liste. |
| **M3** | **3QSS und DBPK ohne OHLC** — bekannt (#614), unverändert. |
| **M4** | Die Multi-Asset-Analysten haben inzwischen die CRV-Bänder-Regel, liefern aber mangels Daten `None`. Korrekt, aber es heißt: kein gemessener Kontext. |
| **M5** | **Fusion-Spot-Agent** ist pausiert, **lokale KI-Ebene (P-8)** zurückgestellt. Beides bewusst. |
| **M6** | **NEU 06.08.: Regime-Konzept für Nicht-Krypto ist offen.** Der Umbau auf stetige Mindestkonfidenz und den Divergenz-Fakt ist für **Krypto** gebaut und aktiv. Für Aktien, Rohstoffe, Themen-ETF und Hedge steht die eigene Bewertung aus — siehe unten. |

### M6 im Detail — was für die anderen Klassen zu klären ist

**Ausgangslage:** R-5.10 (die regime-abhängige Mindestkonfidenz) gilt für die
**gesamte Spot-Familie**, der Regime-Score kommt aber aus **BTC-Daten**. Für
Krypto ist das die richtige Bezugsgröße. Für Aktien, Rohstoffe und Themen-ETF
ist es das vermutlich nicht — aber **das war schon vor dem Umbau so**: das
diskrete Regime war ebenfalls BTC-basiert und gatete alle Spot-Klassen.

**Der Umbau ändert daran nichts** — er filtert heute für alle Klassen identisch
(nachgerechnet). Es ist also eine **Konzeptfrage, keine Verhaltensfrage**, und
sie war schon vorher offen. Der Umbau macht sie nur sichtbar.

**Zu klären, je Klasse getrennt:**

| # | Frage |
|---|---|
| M6a | **Ist BTC die richtige Regime-Referenz für Aktien/Rohstoffe/ETF?** Naheliegender wären S&P 500 bzw. VIX — beide liegen bereits vor (`equities_baermarkt_aktiv`, `vix_wert`) und stecken schon im jeweiligen Regime-Block dieser Klassen. |
| M6b | **Braucht jede Klasse einen eigenen Score, oder genügt einer je Familie?** Ein Score je Klasse ist sauberer, vervielfacht aber die Kalibrierung. |
| M6c | **Der Divergenz-Fakt `btc_zu_ema50` geht bewusst NICHT an diese Klassen** — ihr Regime-Block hat keinen BTC-Bezug. Ein Pendant (z. B. Kursabstand zur eigenen EMA50 oder S&P-500-Abstand) wäre denkbar, ist aber ungemessen. |
| M6d | **Hedge ist ein Sonderfall.** DBPK/3QSS sind inverse Produkte auf S&P 500 und Nasdaq — für sie wäre ein steigendes Aktienregime das Gegenteil eines guten Umfelds. Ein Score müsste dort **umgekehrt** wirken. Vorher blockiert ohnehin der fehlende Kursdatenzugang (siehe Konstruktions-Dokument 2b). |

**Reihenfolge-Empfehlung:** M6 erst nach den Multi-Asset-Grundlagen — M1
(Rohstoff-Instrumentenverwechslung) und die Hedge-Kursdaten blockieren jede
Bewertung dieser Klassen. Ein Regime-Konzept für eine Klasse zu bauen, deren
einzige Evidenz ein Datenfehler ist, wäre die falsche Reihenfolge.

> **Einschätzung:** Multi-Asset ist **gebaut, aber nicht in Betrieb**. Die
> Pipelines laufen, produzieren aber zu wenig, um bewertet zu werden. Vor einer
> Erweiterung gehört M1 geklärt — sonst baut man auf einer Zahl auf, die
> vermutlich ein Bug ist.

---

## 7. Querschnitt — Messung, Betrieb, Dokumentation

**Stark:** die Messmethodik ist der reifste Teil des Projekts. Competing Risks
mit Rechtszensierung, Basislinie je Bucket als Pflicht, Block-Bootstrap über
Symbole, survivorship-freie Simulation, Dreiarm-Design mit Rauschboden. Zwei
Routine-Prüfskripte je Export, vier Basis-Werkzeuge zum Importieren.
Entscheidungslog mit 178 Nachträgen.

**Schwach:**

| # | Lücke |
|---|---|
| **Q1** | **Z-3 steht auf einer dünnen Reihe.** Arithmetisch korrekt (16,84 % nachgerechnet), aber 88 von 90 Tagen hatten keinen gültigen FX-Kurs. Der Fix vom 06.08. ist noch nicht im Betrieb bestätigt — **der Wert wird sich ändern.** |
| **Q2** | **Kein Alarm auf Verschlechterung.** Systemgüte, Signalbeitrag und Konfidenz-Kalibrierung werden berechnet und angezeigt, aber nichts meldet sich, wenn sie kippen. Z-3 ist die einzige aktive Notbremse. |
| **Q3** | Der Kanarienvogel (Provider-Drift) ist gebaut, aber nicht aktiviert. Bewusst — Revisit bei einem zweiten unerklärten Sprung. |

---

## 8. Was vor einem Abschluss von Spot und Hebel zwingend fehlt

> **STAND 07.08.2026 — die Liste unten wurde am Code und am Export nachgeprüft.
> Vier von sieben Einträgen waren veraltet.** Der geprüfte Stand steht in
> Abschnitt 8b; die ursprüngliche Liste bleibt darunter stehen, weil sie die
> Begründungen enthält, warum jeder Punkt kein „nice to have" ist.

Priorisiert, mit Begründung warum es kein „nice to have" ist:

1. **S2 — Akkumulations-Messung für Spot (AZ-4 gegen DCA).** Ohne sie misst das
   Spot-Kapitel gegen einen Maßstab, den die Praxis nicht kennt. **Der
   günstigste Punkt der ganzen Liste:** 33 Positionen mit Einstandspreis, 90
   Tage Mengenhistorie und 182 OHLC-Punkte je Symbol liegen vor — es fehlt
   ausschließlich die Vergleichsrechnung. Und sie entscheidet, ob das Kapitel
   seinen Zweck erfüllt.
2. **H1 — Befolgungsgrad.** Ohne ihn beschreibt die gesamte Erfolgsmessung
   Empfehlungen statt Trades.
3. **H2 — Zieldauer als Feld.** Blockiert `halte_kriterium`, die
   Ausstiegsbewertung und jede Aussage über den Zeithorizont.
4. **M1 — Rohstoff-Ausreißer klären.** Eine Zahl, die vermutlich ein Bug ist,
   steht als einzige Evidenz einer ganzen Assetklasse.
5. **SC2 — Allocator gegen Zufall.** Entscheidet über die Existenzberechtigung
   der Screening-Ebene. Wiedervorlage terminiert.
6. **Q1 — Z-3 nach dem FX-Fix neu bewerten.** Eine ausgelöste Notbremse auf
   unbestätigter Zahl.
7. **M6 — Regime-Konzept für die Nicht-Krypto-Klassen.** Für Krypto am 06.08.
   gebaut und aktiv; Aktien, Rohstoffe, Themen-ETF und Hedge brauchen eine
   eigene Bewertung (welche Referenz statt BTC, eigener Score je Klasse, und
   bei Hedge eine **umgekehrte** Wirkrichtung). Erst nach M1 und den
   Hedge-Kursdaten sinnvoll.

**Nicht auf dieser Liste, bewusst:** neue Fakten fürs LLM, weitere Gates, mehr
Symbole. Acht Selektionsmechanismen wurden gemessen, keiner trug nachweisbar —
die Grenze liegt derzeit nicht bei der Auswahl, sondern bei **Ausstieg,
Kostendeckung und Maßstab**.

---

---

# 8b. Geprüft und priorisiert (07.08.2026)

**Auftrag:** alle offenen Themen recherchieren, gegen den Code prüfen,
Abhängigkeiten aufdecken, dann priorisieren — Quick Wins und wichtige
Anpassungen oben.

**Methode:** jeder Punkt aus Abschnitt 8 oben, aus
`Zielgroessen_und_Erfolgsmasse.md` Abschnitt 6.6 (Acht-Stufen-Lücke) und aus
`Plan_Nicht_Krypto_Umbau_06_08.md` Phase C/D wurde **am Code und am Export vom
07.08. nachgeprüft**, nicht aus dem Dokument übernommen.

## 8b.0 Was die Prüfung an den Dokumenten selbst korrigiert

| Dokumentierter Punkt | Stand laut Dokument | **tatsächlich** |
|---|---|---|
| **M1** Rohstoff-Ausreißer | offen | **erledigt 06./07.08.** — real n=0, Schatten −1,06 R |
| **Q1** Z-3 nach FX-Fix | offen | **erledigt** — 0 verworfene FX-Tage; Z-3 rechnet auf `index_wert` und war nie beschädigt |
| **H2** Zieldauer *als Feld* | „blockiert `halte_kriterium`" | **Feld existiert und ist befüllt** (`halte_kriterium_ziel_datum`, 211 Spot / 318 Hebel) und wird exportiert. Offen ist die **Auswertung**, nicht das Feld |
| **0.1** vier Export-Felder | „erledigt 04.08." | **teilweise** — `score_details_json` und `funding_rate_aktuell` fehlen in **beiden** Signal-Exporten (sie sind nur in `hebel_triggers_alle`) |

> **Lehre, die sich heute zum vierten Mal zeigt:** ein Dokumentstand ist keine
> Messung. Vor jeder Priorisierung gehört die Prüfung am Code — sonst arbeitet
> man an Punkten, die erledigt sind, und übersieht die, die es nicht sind.

---

## 8b.1 ~~Der zentrale Blocker~~ — HERABGESTUFT am 07.08.

> **KORREKTUR (07.08., Nutzer-Position):** *„Das System muss auch ohne explizite
> Durchführung der Empfehlungen funktionieren — Anwendung kommt nach Funktion.
> Ansonsten muss das System mit den systeminternen Messungen seine Qualität
> messen und kalibrieren."*
>
> Das ist fachlich richtig. `umgesetzt` misst das Verhalten des **Nutzers**,
> nicht die Qualität des **Systems** — und beides zu vermengen erzeugt genau die
> Schleife: keine handelbaren Signale → keine Trades → keine Befolgungsdaten →
> keine Messung. Die Qualitätsmessung steht bereits auf eigenen Beinen
> (R-Multiples gegen echte Kursreihen, Basislinie, Schattenarm, Systemgüte).
>
> **B1 fällt von „zentraler Blocker" auf „wäre zusätzlich interessant".** Was
> die systeminterne Messung wirklich braucht: Kosten im R, Horizont je Klasse
> (H-2/H-3) und überhaupt handelbare Signale (H-4).

### Der ursprüngliche Befund bleibt als Faktum bestehen

### B1 · Befolgungsgrad ist zu 100 % leer

```
spot_signals : umgesetzt = None bei ALLEN 2.742 Signalen
hebel_signals: umgesetzt = None bei ALLEN 1.703 Signalen
```

Das Feld existiert seit dem 09.07. **auf `signals` (Spot)**, es gibt drei
Aufrufstellen (`importer/bitpanda_sync.py`, `ui/app.py`, `ui/signals_view.py`)
— und es wurde **nie befüllt**.

**Für Hebel ist es schlimmer, und das kam erst beim Nachbauen heraus.** Der
erste Versuch war, die vier Spalten einfach in `_HEBEL_SIGNAL_SPALTEN`
aufzunehmen — der Test gegen eine DB-Kopie antwortete `no such column:
umgesetzt`. **Auf `hebel_signals` existieren die Spalten gar nicht**: die
Umsetzungs-Rückmeldung wurde 2026-07-09 ausschließlich für Spot gebaut, mit
Tabelle, Migration und Schreibpfad. Für Hebel gibt es weder das eine noch das
andere.

Damit ist B1 **keine Export-Lücke, sondern eine fehlende Funktion** — und zwar
für die Klasse mit 1.703 Signalen und der einzigen belastbaren Datenbasis. Der
Aufwand ist entsprechend größer: Migration + Schreibpfad + UI, nicht eine
Zeile Spaltenliste.

**Warum das alles andere entwertet:** Systemgüte, CRV-Bänder, Basislinie,
Erwartungswert — jede dieser Zahlen beschreibt **Empfehlungen, nicht Trades**.
Ein System, das perfekte Signale erzeugt, die niemand ausführt, und eines, das
schlechte erzeugt, die alle ausgeführt werden, sehen in unseren Kennzahlen
identisch aus.

**Abhängig davon:** die Aussagekraft von H-Systemgüte, SC2 (Allokator), Stufe 4
(Gate-Beitrag), Stufe 7 (Kosten je echtem Trade) — also praktisch die gesamte
Messebene.

---

## 8b.2 Quick Wins — kleiner Aufwand, sofort wirksam

| # | Punkt | Aufwand | Wirkung |
|---|---|---|---|
| ~~QW1~~ | ~~`umgesetzt` in `_HEBEL_SIGNAL_SPALTEN`~~ — **kein Quick Win**, siehe 8b.1: die Spalte existiert auf `hebel_signals` nicht | — | zurückgezogen, gehört zu W4 |
| **QW2** | `score_details_json` + `funding_rate_aktuell` in beide Signal-Exporte | 2 Zeilen | schließt die letzte der vier 04.08.-Export-Lücken; Kostenmodell je Signal rechenbar |
| **QW3** | AZ-4-Messung **ausführen** (`messe_akkumulation_az4.py` liegt seit 06.08. fertig) | Skriptlauf | entscheidet, ob Spot seinen Zweck erfüllt — laut Zwischenstand „der günstigste Punkt der ganzen Liste" |
| **QW4** | Ausstiegsempfehlungen: 23 Stück, **27,2 R ungesichert** | Entscheidung | SOL allein sichert 9,63 R. Bereits berechnet, liegt unversorgt herum |

**QW1 und QW2 sind reine Export-Ergänzungen ohne Verhaltensrisiko** — dieselbe
Kategorie, die am 04.08. schon einmal als unbedenklich eingestuft wurde.

**QW4 ist kein Code, sondern eine Entscheidung.** Der Befund vom 04.08. steht:
*50 % der Signale standen bei +1R, nur 17,6 % kamen dort an.* Der Ausstieg ist
der größte gemessene Hebel des Systems, und die Empfehlungen dazu existieren
bereits.

---

## 8b.3 Wichtige Anpassungen — mittlerer Aufwand, blockieren ganze Kapitel

| # | Punkt | blockiert | Abhängig von |
|---|---|---|---|
| ~~W1~~ | **ERLEDIGT 07.08.** — nicht „invertiert": das R des Einzeltrades war richtig, falsch war die Fragestellung. Gebaut: eigener Hedge-Tier + `compute_hedge_wirksamkeit()` (Dämpfung + Prämie) | — | — |
| ~~W2~~ | **ERLEDIGT 07.08.** — sieben Faktoren mit umgekehrter Wirkrichtung. Dabei gefunden: **9 von 11 Hedge-Empfehlungen hatten verdrehte Zonen** (Stop über Entry) — Zonenwache + Prompt-Regel 9b | — | — |
| **W3** | **Halte-Kriterium auswerten** (Stufe 6) | Aussagen über Zeithorizont und Ausstiegsgüte | H2-Abdeckung (heute nur 8 % Spot / 19 % Hebel) |
| **W4** | **Befolgungsgrad erfassen** (B1 beheben) — für Spot befüllen, für Hebel erst **bauen** (Migration + Schreibpfad + UI) | siehe 8b.1 | — |

**W1 ist der sauberste Einstieg von allen vier** — er hängt an nichts, ist
inhaltlich eindeutig (ein Hedge, der verliert während das Portfolio steigt, hat
funktioniert), und er schaltet zwei Punkte auf einmal frei (W1 → W2).

---

## 8b.4 Warten auf Zeit — kein Handlungsbedarf

| Punkt | frühestens | Bedingung |
|---|---|---|
| Systemgüte-Lücke im A-Arm (~3 pp) | Ende August | genug aufgelöste Fälle |
| SC2 Allokator gegen Zufall | 3 Wochen ab 05.08. | Datumsfilter ab 05.08. |
| CoinGecko-80-%-Warnmail | Monatsende | Hochrechnung 8.335 von 10.000 |
| Tageswert-Neuschreibung mit ≥ 80 % Abdeckung | morgen 06:30 | erster Lauf nach dem Fix |
| **93 C · Lebendigkeit über TVL** | **ca. 18.09.2026** | 30 Tagesmessungen ab 20.08. — **läuft nachweislich**, 401 Zeilen am 22.08. |
| **93 C · Lebendigkeit über Entwicklerdaten** | **09.11.2026** | 12 Wochenmessungen ab Montag **24.08.** — Wochentakt, ein Abruf je Symbol |
| **93 C · Schwelle `SCHWELLE_RELATIV` kalibrieren** | **18.09.2026** | ⚠️ **Nutzerentscheidung 22.08.: bewusst vertagt.** Die 0,10 wurde mit der *echten* Änderung begründet, wirkt aber auf den Halbmittel-Vergleich — faktisch **~20 %**. Kalibriert wird am gemessenen Rauschen der eigenen Reihe, nicht am Schreibtisch. Vermerk steht in `agent/lebendigkeit.KALIBRIERUNG_FAELLIG` |

> ⚠️ **Beide Termine stehen seit dem 22.08. im NB-Export selbst**
> (`kapitel93.lebendigkeit.entwickler_takt`), samt Warnung, sobald ein
> fälliger Montag ohne Messung verstreicht. Vorher konnte der Export „noch
> nicht fällig" nicht von „nie gelaufen" unterscheiden — siehe Methodik 2.57.
>
> ⚠️ **Reichweitengrenze:** ~18 der 44 Kryptowerte sehen über TVL nur
> `keine_quelle` und werden dort **nie** auswertbar. Für sie bleibt allein die
> Entwicklerquelle.

---

## 8b.5 Nutzer-Entscheidung — Code kann das nicht lösen

**C1 · Universum.** 2 Aktien, 4 Rohstoffe, 5 Themen-ETF, 2 Hedge. Externer
Standard sind **30 aufgelöste Fälle als Untergrenze, 100+ für Belastbarkeit**.
Bei dieser Größe entsteht in keiner Nicht-Krypto-Klasse je eine auswertbare
Stichprobe — unabhängig davon, wie gut der Code wird.

**Davon abhängig:** C2 (Screening für Nicht-Krypto) und M6 (Regime je Klasse).
Beide sind ohne Universum sinnlos, nicht nur verfrüht.

---

## 8b.6 Abhängigkeitskette — was worauf wartet

```
W4 (Befolgungsgrad: Spot befuellen, Hebel BAUEN) ──►  Aussagekraft ALLER Kennzahlen
                                                        │
QW2 (Export funding/score) ─────────────────────────────┤
                                                        ├─►  Stufe 7 Kosten je echtem Trade
H2-Abdeckung  ──►  W3 (Halte-Kriterium auswerten)  ─────┘

W1 (Hedge-Erfolgsmaß)  ──►  W2 (Hedge-Risikofaktoren)  ──►  Hedge auswertbar
                        └──►  M6-Teil Hedge

C1 (Universum, Nutzer)  ──►  C2 (Screening)  ──►  M6 (Regime je Klasse)

QW3 (AZ-4 ausführen)  ──►  entscheidet über den MASSSTAB des Spot-Kapitels
QW4 (Ausstieg)  ──►  unabhängig, sofort umsetzbar
```

**Zwei Ketten laufen parallel und behindern sich nicht:** die Messkette (QW1 →
W4) und die Hedge-Kette (W1 → W2). Beide können gleichzeitig laufen.

**Eine Kette ist blockiert und bleibt es:** C1 → C2 → M6 wartet auf eine
Entscheidung, nicht auf Arbeit.

---

## 8c. FERTIGBAU-PLAN der Rollen-Ebene (Stand 2026-08-11 abends)

> **Nutzervorgabe 11.08.: „das Fertigbauen planen und nicht vergessen."** Diese
> Liste ist der Ort dafür. Alles hier ist **gebaut und geprüft, aber noch nicht
> im Betrieb** — oder bewusst offen gelassen. Details je Punkt in
> `Arbeitsstand_Deadloop_09_08.md`, Abschnitte 7.10 bis 7.20.

### 8c.1 Gehört auf das NOTEBOOK (Produktionshandlungen)

Der Desktop darf das nicht — drei dokumentierte Vorfälle, siehe die stehende
Regel. Alles hier als **ein** Deployment-Paket, nicht einzeln.

| # | Was | Stand |
|---|---|---|
| P1 | **yfinance-Rückfall ausrollen** — `api/yfinance_krypto_fallback.py` + Einhängung in `scheduler/background.py` | gebaut, verdrahtet, trocken geprüft |
| P2 | Erster Lauf: KAIA · KAITO · SUPRA · XNO bekommen echte Tageskerzen | erfolgt automatisch beim ersten `refresh_ohlc_job` |
| P3 | `pruefe_abdeckung.py` auf dem Notebook laufen lassen | Desktop-Zahlen gelten nur für den 19.07. |
| P4 | **OD7L** — keine Futures-Referenz, als einziger Rohstoff ohne Reihe | ungeklärt |

### 8c.2 Gebaut, aber NICHT an die Kette angeschlossen

| # | Was | warum es zählt |
|---|---|---|
| K1 | **Die gesamte Rollen-Ebene** (Lagebild · Befund · Entscheidung) läuft nicht in der Produktion | dort läuft weiter das Altsystem mit 34.611 Zeichen |
| K2 | **`umgeworfen_durch` wird erzeugt und nie ausgewertet** | das ist das thesenbasierte **Ausstiegskriterium**. Live geprüft: die Texte sind maschinell prüfbar („Tagesschlusskurs über 2218,75 EUR bei steigendem Volumen") |
| K3 | **`agent/waechter_zuspitzung.py`** prüft die Zwischenausgabe auf unbelegte Zuspitzung | gebaut, Ist-Zustand gemessen (1 von 8), noch nicht in der Kette |
| K4 | Granularitätswarnung erscheint im Log — die **Messskripte** sollten sie in ihrem Kopf mitausgeben | sonst liest man sie leicht über |

### 8c.3 Offene Messungen — je mit vorab festgelegter Abbruchregel

| # | Hypothese | Umfang |
|---|---|---|
| M1 | **Betragsfrage** senkt die Handlungsquote | 4 Zellen × 8 Anker × 2 Arme × 2 Wdh. ≈ 256 Aufrufe. Abbruchregel steht (Arbeitsstand 7.x) |
| M2 | **Breite-Urteil** — Größe des Effekts | Übertragung (7.3) und falsche Richtung (7.4) sind belegt, nur die Größe fehlt |
| M3 | **Bestandsblock** färbt die Entscheidung | Literatur widersprüchlich (Methodik 2.19.3) — nur eigene Messung entscheidet |
| M4 | **Persona** im Prompt | offene Frage, kein Verbot. Schalter gebaut |
| M5 | **`unabhaengige_faktoren`** — ist die Zahl stabil? | sie trägt seit dem Umbau die Positionsgröße und wurde nie geprüft |

**Vor jedem dieser Läufe:** `pruefe_abdeckung.py`, Wächter, Kausalitätsprobe.
Und die **Uniqueness-Gewichtung** (Methodik 2.19.1) — ohne sie sind die
Konfidenzintervalle zu eng.

### 8c.4 Konzeptarbeit, die vor dem Weiterbauen liegt

| # | Was | Grund |
|---|---|---|
| C1 | **Kapitel 11 der Faktenmappe** — Kette Gate → Lagebild → Befund/Entscheidung, Rollenabgrenzung über den exklusiven Eingang, Regeln R-T1…R-T9 | die Formvorgabe fehlt bis heute; 10.1 hat nur einen Grundsatz |
| C2 | **Marktlage und Historie je Assetklasse** — Benchmark statt Marktbreite | Breite ist für 4 von 5 Klassen arithmetisch unmöglich (7.15). Benchmarks vorhanden: BTC, SPY, Futures-Reihen |
| C3 | **Nachrichten in die LLM-Ebene** | nach allem Gemessenen die einzige Kategorie, die noch eine Kante enthalten kann |

### 8c.5 Kleinere Defekte, benannt und offen

| # | Was |
|---|---|
| D1 | `api/coingecko_ohlc_fallback.py:79` behauptet „bei `days` ≤ 90 Tageskerzen" — gemessen sind es Vier-Tage-Kerzen. Der Kommentar ist die Fehlerquelle |
| D2 | `braucht_fallback()` implementiert die im eigenen Modulkopf dokumentierten Ausnahmen nicht (VSN als Wertpapier, EURCV als Stablecoin). Wirkt heute nur noch als verschwendeter Abruf, weil der Granularitätswächter die Kerzen ohnehin verwirft |
| D3 | `_rohdaten_zu_tageskerzen()` heißt so, liefert aber keine Tageskerzen |
| D4 | Drei Backtest/Live-Unterschiede: `tag_vollstaendig`, `mit_bezug` in den Messskripten, und der Währungsfilter im Exportpfad (bewusst so belassen, siehe Docstring) |

### 8c.6 Was NICHT auf dieser Liste steht, und warum

Der `_struktur()`-Fix ist **erledigt** (7.13) — und hat die Entscheidung nicht
bewegt. Die Degradierungs-Hypothese ist **widerlegt** (7.12, 0 von 8). Beide
bleiben hier stehen, damit sie nicht ein drittes Mal als Idee auftauchen.

---

## 8d. NEU PRIORISIERT nach dem Befund vom 11.08. abends

> **8c bleibt stehen — es ist die Liste dessen, was gebaut und nicht im Betrieb
> ist, und die gilt unverändert.** Was sich geändert hat, ist die REIHENFOLGE
> und die Begründung. Grund: `Arbeitsstand_Deadloop_09_08.md` 7.25.

### Der Befund in einem Satz

Ein Barrierensystem auf einem näherungsweise driftfreien Pfad hat **brutto den
Erwartungswert null — für jede Geometrie.** Theoretisch 33,3 % Zielquote bei
3/1,5 ATR, gemessen 34,0 % über 19.891 Anker. Nach Kosten ist es strikt negativ.
Kein Prompt, kein Modell, keine Parametrierung ändert das.

### Was dadurch WEGFÄLLT

| bisher | warum es entfällt |
|---|---|
| Weitere Stop-, Ziel- oder Horizontvarianten | der Erwartungswert ist für jede Geometrie null — das ist Arithmetik, keine Messfrage |
| „Bessere Einstiege wählen" als Ziel | es gibt keine Ordnung, die man treffen könnte (6.1/6.2, 7.22) |
| Der Struktur-Defekt als Deadloop-Ursache | 2,71 % der Tage, und die Zellen unterscheiden sich nicht |

### Was BLEIBT, in neuer Reihenfolge

| Rang | Punkt | warum jetzt hier |
|---|---|---|
| **1** | **S2 — Akkumulation gegen DCA messen** (Abschnitt 8, dort seit 07.08. als *„günstigster Punkt der ganzen Liste"* markiert) | **Der einzige Weg, der ohne Vorhersagekraft auskommt.** Wer Drift einsammelt, muss keine Barriere treffen. Daten liegen vollständig vor, es fehlt nur die Vergleichsrechnung |
| **2** | **8c.4/C3 — Nachrichten in den Befund** | die einzige Kategorie, die den Pfad überhaupt nicht-driftfrei machen könnte. Die Rollen-Ebene ist genau die Stelle, an der sie hineinkommt |
| **3** | **8c.1 — das Notebook-Paket ausrollen** | die Datenwege sind repariert; sie gehören in Betrieb, unabhängig von der Ökonomie |
| **4** | **8c.2/K2 — `umgeworfen_durch` anschließen** | der Ausstieg existiert und wird nicht ausgewertet. Defektbeseitigung |
| **5** | 8c.3/M1 — die Betragsfrage gepaart messen | **abgestuft.** Sie klärt einen Defekt (R-A2 war nicht gebaut), nicht mehr die Frage „trägt sich das System". Die Abbruchregel gilt weiter |
| 6 | 8c.3/M2–M5, 8c.5 | Defektbeseitigung, keine Eile |

### Der Grund für die Umstellung, ausdrücklich

Die Punkte 3 bis 6 sind **Defektbeseitigung** — sie machen das System korrekt,
nicht tragfähig. Die Punkte 1 und 2 sind die einzigen, die überhaupt eine Kante
erzeugen könnten. Sie standen bisher hinten.

**Was NICHT folgt:** dass das Bisherige umsonst war. Die Frage „funktioniert
Timing mit Kursdaten" ist in sechs Wochen belastbar beantwortet worden — die
Antwort ist nein, und sie ist jetzt begründet statt vermutet. Und die
Rollen-Ebene, die dabei entstanden ist, ist die Voraussetzung für Weg 2.

---


## 8e. UMSETZUNGSPLAN PRODUKTION — laufend fortzuschreiben

> **Nutzervorgabe 12.08.:** *„die noch offenen Punkte und Detailänderungen zum
> Gesamtplan für die Umsetzung in der Produktion sollen laufend aktualisiert
> werden und kein Bereich vergessen werden."*
>
> **PFLEGEREGEL — dieser Abschnitt ist eine lebende Datei, kein Bericht.**
> 1. Jede Änderung an Code, der die Produktion berührt, kommt in 8e.1 —
>    **bevor** sie committet wird, nicht danach.
> 2. Jeder erledigte Baupunkt wird in 8e.2 **abgehakt statt gelöscht**. Die
>    Begründung ist oft wertvoller als der Punkt.
> 3. Ein Punkt gilt erst als erledigt, wenn der **Code** es bestätigt — nicht
>    das Dokument. Am 11.08. war R-A2 seit einem Tag „erledigt" und nie gebaut.
> 4. Der Ist-Zustand wird **geprüft, nicht erinnert.** Jede Zahl hier ist am
>    Code oder an den Daten erhoben.

### Der Satz, der die Lage beschreibt

**Die neue Rollen-Ebene läuft in null Produktionspfaden.** Geprüft am 12.08.
über die tatsächlichen Importe: `lagebeschreibung`, `rolle_analyst`,
`rolle_trader`, `waechter_zuspitzung`, `rollen_eingabe`, `empfehlung_vertrag`
und `marktbreite` haben **je null** Importe aus `scheduler/`, `ui/`, `main.py`,
`agent/krypto/`, `agent/aktien/`, `agent/rohstoff/`, `remote/`.

In der Produktion läuft weiter das Altsystem mit 34.611 Zeichen Prompt.

---


## 8e.0 WAS GESCHNITTEN WIRD — die Abgrenzung

> **Nutzerdefinition 12.08.:** *„Unter Altsystem meine ich Funktionen, welche
> falsch gebaut sind oder durch eine neue bessere ersetzt werden — mit Fokus auf
> das LLM, aber auch auf andere Komponenten, welche nachweislich nicht korrekt
> sind. Es soll ein glatter Schnitt werden."*
>
> **Nicht betroffen:** das deterministische Risikomanagement (RM-1 bis RM-7,
> Cash-Reserve, Positionsgrößen-Deckel, Vetos). Es ist nicht defekt und ist
> ausdrücklich die Schicht, in die Risiko gehört (Kap. 11.3).
>
> **Ein glatter Schnitt verträgt keine Umgehungen.** Wo ein Defekt nur
> umfahren wurde, geht die Naht später wieder auf. Die Liste unten trennt
> deshalb drei Zustände: **behoben · umgangen · offen.**

### A — BEHOBEN, der Schnitt ist gemacht

| Was war falsch | Beleg | behoben |
|---|---|---|
| `_struktur()` trug ein absolutes Etikett auf wenigen Tagen | 7.9 | 11.08. |
| Betragsfrage in beiden Prompts, R-A2 dokumentiert und nie gebaut | Nachtrag 205 | 11.08. |
| `lade_reihen_aus_db()` filterte USD — ETF-Klasse unsichtbar | 7.17 | 11.08. |
| `_bestand()` las nur die berechnete Einstandsspalte — 14 von 28 Positionen als „nicht im Bestand" gemeldet | 7.10 | 11.08. |
| `_kurs_eur()` las die älteste `price_cache`-Zeile | 7.10 | 11.08. |
| EUR-Reihen wurden ein zweites Mal nach EUR umgerechnet | 7.20 | 11.08. |
| Zwei Messskripte riefen die Marktbreite ohne Kalibrierungssatz | 7.14 | 12.08. |
| Helfer lagen in einem Skript, sieben Skripte importierten daraus | 8e.1 | 12.08. |

### B — UMGANGEN, NICHT BEHOBEN — hier ist der Schnitt noch nicht glatt

> **Dieser Abschnitt ist seit dem 12.08. leer.** Beide Einträge sind nach oben
> in A gewandert — nicht, weil ein Wächter sie abfängt, sondern weil die
> falschen Quellen abgeschaltet sind.

**Was hier stand und wie es geschnitten wurde.** Der CoinGecko-Rückfall lieferte
Vier-Tage-Kerzen und legte sie unbeschriftet neben Krakens Tageskerzen ab; ein
Granularitätswächter verwarf sie beim Laden. Das war eine Umgehung: die Quelle
schrieb weiter, sie wurde nur nicht mehr gelesen.

Auf Nutzervorgabe *(„schalte den CoinGecko-Rückfall ab und mach einen glatten
Schnitt auf die richtigen Daten — aber mach davor eine Gegenprüfung ob es eine
bessere Lösung gibt")* wurde vor dem Schnitt gemessen. Die Gegenprüfung fand eine
bessere Lösung — und sie ersetzt auch den yfinance-Rückfall vom Vortag:

| Kombination | Deckung | ohne |
|---|---|---|
| Kraken allein | 35/42 | |
| Kraken + yfinance (11.08.) | 39/42 | BRETT, CANTON, IO |
| **Kraken + Binance/Bybit Spot** | **41/42** | CANTON |
| Kraken + Binance/Bybit + yfinance | 41/42 | yfinance fügt **nichts** hinzu |

**Der Ausschlag gibt nicht die Deckung, sondern die Eindeutigkeit.** yfinance
riet den Ticker `<SYM>-USD`; drei von acht gehörten einem anderen, toten Asset.
Bei den Börsen fragen wir nach ihrem eigenen Paar `KAIAUSDT` — was zurückkommt,
*ist* dieses Paar. **Ein ganzer Fehlerpfad entfällt, statt abgesichert zu
werden.** Kontrast an IO: yfinance 269 % Preisabweichung (falsches Asset),
Börsen 8,9 % (richtiges Asset, zwei Tage Kursbewegung).

**An echten Daten geprüft (12.08., auf Nutzerverlangen vor dem Ausrollen):**

| Symbol | Kerzen | Abweichung zum eigenen Preis |
|---|---|---|
| KAIA | 651 | 1,1 % |
| BRETT | 847 | 3,6 % ← yfinance lieferte hier ein totes Asset |
| IO | 793 | 8,9 % ← dito |
| SUPRA | 624 | 0,5 % |
| KAITO | 539 | 7,7 % |
| XNO | 1000 | 6,8 % |
| CANTON | 0 | an keiner Börse gelistet |

Kraken 35 + Börsen 6 = **41 von 44**; bewusst ohne EURCV (Stablecoin) und VSN
(Wertpapier); ungedeckt bleibt allein CANTON — **sichtbar statt falsch.**

Beide Vorgänger bleiben im Repo, aber unverdrahtet und im Modulkopf als abgelöst
markiert. Wer sie in einem Jahr wieder erwägt, findet dort die Messung statt der
Annahme.

### C — OFFEN, noch nicht angefasst

| Was falsch oder unbelegt ist | Beleg |
|---|---|
| **Marktbreite** — gemischter Korb, wechselnde Zusammensetzung, für 4 von 5 Klassen nicht berechenbar, Richtung invers | 7.4, 7.15 |
| **`HORIZONT_KERZEN = 20`** — nie aus der Zieldistanz abgeleitet; bei 3 ATR lösen sich Fälle erst bei 16–19 Tagen auf | 7.12, 7.22 |
| **„keines = 0 R"** in der Erwartungswert-Rechnung — eine Setzung, keine Messung; betrifft 15–21 % aller Fälle | 7.23 |
| **Uniqueness-Gewichtung fehlt** — die Konfidenzintervalle der 8.441-Fälle-Messung sind zu eng | Methodik 2.19.1 |
| **`tag_vollstaendig`-Divergenz** — im Backtest sieht das Modell eine Umsatzzeile mehr als live | 7.13 |
| **Kein Gegenprüfer in der neuen Kette** — die alte hatte Z.ai, die neue nichts | 8e.2/Z1 |
| **Z.ai urteilte über eine Konstante** (`regime` auf 1.022 Fällen „baer") | Arbeitsstand 10 |
| **Kein Gate in der neuen Kette** — in keiner Messung dabei | 8e.2/G1 |

### Die Regel für den Schnitt

**Ein Defekt gilt erst als geschnitten, wenn die falsche Funktion weg ist —
nicht, wenn eine spätere Stufe ihn abfängt.** Ein Wächter ist ein Netz, keine
Reparatur. Netze gehören trotzdem gespannt: sie fangen den nächsten Fehler, den
noch niemand kennt.

---

## 8e.1 DETAILÄNDERUNGEN — was seit dem 10.08. geändert wurde

*Getrennt danach, ob die Produktion es beim nächsten Lauf merkt. Diese Trennung
ist der Kern: was isoliert ist, kann nichts kaputtmachen; was im Pfad liegt,
wirkt sofort nach dem Ausrollen.*

### A — WIRKT in der Produktion, sobald das Notebook zieht

| Änderung | Datei | Wirkung beim nächsten Lauf |
|---|---|---|
| **Börsen-Klines als einziger Krypto-Rückfall** | `api/boersen_klines.py` (neu) + `scheduler/background.py` | Der OHLC-Job ruft für Krypto ohne Kraken-Listing **nur noch** Binance, ersatzweise Bybit. **Ändert Kursdaten**, die alles Weitere nutzt: 6 Symbole bekommen erstmals echte Tageskerzen, 539–1.000 Stück statt 24 Vier-Tage-Kerzen |
| **CoinGecko-Rückfall abgeschaltet** | `api/coingecko_ohlc_fallback.py` | Nicht mehr importiert. Spart je Lauf bis zu 9 Aufrufe aus einem Kontingent, das an aktiven Tagen zu 96 % ausgeschöpft war |
| **yfinance-Krypto-Rückfall abgeschaltet** | `api/yfinance_krypto_fallback.py` | Nicht mehr importiert — trug in der Messung **null** zusätzliche Symbole bei, brachte aber den Fehlerpfad „geratener Ticker" mit |
| Funding-Funktionen | `api/derivatives.py` | **gebaut, aber nicht gerufen** — keine Wirkung, bis ein Aufrufer sie nutzt |

> **Vor dem Ausrollen geprüft (12.08.):** alle sechs bedienbaren Symbole liefern,
> Preise weichen 0,5–8,9 % vom eigenen `price_cache` ab (dieser ist zwei Tage
> älter), Median-Kerzenabstand 1 Tag. `fuelle_luecken(..., trocken=True)` zeigt
> das ohne Schreibzugriff — **die Vorgabe bleibt `trocken=True`**, ein Schreiben
> in die Kursdaten ist eine Produktionshandlung.

### B — ISOLIERT, wirkt erst mit dem Einhängen der Rollen-Ebene

| Änderung | Datei | was sie bewirkt |
|---|---|---|
| Währungsregel, eine je Symbol | `backtest_llm1_historisch.py` | ETF-Klasse überhaupt sichtbar (7 Symbole, bis 4.722 Kerzen) |
| Granularitätswächter | dito, beide Ladepfade | 9 Reihen mit Vier-Tage-Kerzen werden verworfen und **benannt** |
| Einstand aus **beiden** Spalten | `pruefe_rollenkette.py` | 14 Positionen werden nicht mehr als „nicht im Bestand" gemeldet |
| `ORDER BY fetched_at DESC` | dito | nicht mehr die älteste `price_cache`-Zeile |
| Keine EUR-Doppelumrechnung | dito | seit die ETFs sichtbar sind, sonst um den Wechselkurs daneben |
| `_struktur()` ohne Etikett, mit Fenster | `agent/lagebeschreibung.py` | R-T1/R-T2 |
| Drei Bestandszustände statt zwei | dito | „im Bestand, Einstand unbekannt" ist eine eigene Aussage |
| Finanzierungsblock | dito | erster Fakt, der nicht aus der Kursreihe stammt |
| Betragsfrage aus beiden Prompts | `rolle_analyst.py`, `rolle_trader.py` | R-A2 erstmals gebaut. Alte Fassung schaltbar erhalten |
| `PROMPT_STAND` | dito | jeder Messbefund ist einem Stand zuordenbar |
| Zuspitzungs-Wächter | `agent/waechter_zuspitzung.py` (neu) | prüft die **Naht** zwischen den Rollen |
| Eine Stelle für die Rollen-Eingabe | `agent/rollen_eingabe.py` (neu) | **0 Nutzer** — die sieben Messskripte bauen sie weiter selbst |

---

## 8e.2 BAUPUNKTE — nach der Ablaufkette

### STUFE 0 — Betrieb

| # | Was | Stand |
|---|---|---|
| B1 | **Rollen-Ebene in die Produktion einhängen** | **nicht begonnen** — kein Aufrufer außerhalb der Messskripte |
| B2 | **Börsen-Klines ausrollen** | verdrahtet, gepusht, **nicht ausgerollt**. Ersetzt den yfinance-Rückfall vom 11.08. *und* den CoinGecko-Rückfall — beide abgeschaltet. An echten Daten geprüft (8e.0 B) |
| B3 | Produktion wieder starten | steht seit 10.08. bewusst |
| B4 | `pruefe_abdeckung.py` auf dem Notebook | Desktop-Zahlen gelten nur für den 19.07. |

### STUFE 0b — STRATEGIE *(neue Lücke, 12.08.)*

> **Nutzerfrage:** *„wie oder wann wird über die Kauf- oder Verkaufsstrategie
> entschieden — am Gate, LLM oder durch mich beim Handeln?"*
>
> **Am Code geprüft: nirgends.** Das Gate entscheidet, ob eine Handlung
> **erlaubt** ist. Das LLM entscheidet **fallweise**, welche. Der Nutzer
> entscheidet über die **Ausführung**. Eine übergeordnete Absicht kennt keine
> der drei Stellen.
>
> `strategien_aktiv` in der `config.yaml` wird an das alte LLM gereicht; die
> Faktenmappe hält dazu fest: *„Liste ohne jede Anweisung. Keine Regel, kein
> Gate."* Es ändert nichts.
>
> **Die Strategie wird also nicht entschieden — sie entsteht** als Summe vieler
> Einzelurteile. Sichtbar am 12.08.: 16 von 17 Handlungen der neuen Kette waren
> Verkäufe. Niemand hat entschieden, dass wir ein verkaufendes System sind.

| # | Was | Stand |
|---|---|---|
| S1 | **Strategie als Setzung, nicht als Urteil** | fehlt. Nach dem Kriterium aus Kap. 11.3 gehört sie in die **deterministische** Schicht: sie wirkt auf alle Assets gleich |
| S2 | Umsetzung: die Strategie schränkt die **angebotenen Aktionen** ein | „wir akkumulieren" → VERKAUFEN entfällt · „wir bauen Risiko ab" → KAUFEN entfällt · „neutral" → alles offen |

**Die Achsen, die der Nutzer nennt (12.08.): Spot ↔ Hebel und Swing ↔ Einmalkauf.**

| Achse | bestimmt |
|---|---|
| **Spot ↔ Hebel** | Kostenstruktur (bei Hebel eine Gebühr **je Tag**, bei Spot nicht), Haltedauer, Pipeline |
| **Swing ↔ Einmalkauf** | ob es überhaupt einen Ausstieg gibt, welcher Horizont gilt, ob ein Stop greift — **und woran der Erfolg gemessen wird** |

> **DIE STRATEGIE ENTSCHEIDET, WELCHE MESSUNG GÜLTIG IST.** Ein Swing wird an
> Ziel und Stop innerhalb von N Tagen gemessen. Ein Einmalkauf hat weder Ziel
> noch Stop — dort zählen Einstiegspreis und langfristiger Verlauf.
>
> **Das erklärt einen Fehler in den Messungen vom 11./12.08.:** Alles wurde mit
> dem Barrieren-Maßstab gerechnet (3 ATR Ziel, 1,5 ATR Stop, 20 Tage) — das ist
> der **Swing**-Maßstab. Die daraus gezogene Schlussfolgerung „der Aufbau trägt
> sich nicht" (7.23, 7.24) gilt damit **für Swing-Handel**. Für einen
> Einmalkauf ist die Rechnung nicht die falsche Antwort, sondern die falsche
> Frage — dort ist S2/Akkumulation (7.27) der zuständige Maßstab.
>
> **Vor jeder weiteren Messung ist deshalb festzulegen, welche Strategie sie
> unterstellt.** Sonst misst sie wieder eine, die niemand gewählt hat.
| S3 | Wer setzt sie und wie oft? | offen — Nutzerentscheidung, Regelwerk, oder Rolle Lagebild |
| S4 | Verhältnis zu AZ-4 | AZ-4 *ist* eine Strategie („antizyklisch akkumulieren") und lebt heute in der Regime-Logik des Altsystems, nicht in der neuen Kette. Ihre Zusatzannahme ist zudem widerlegt (7.27) |

### STUFE 1 — GATE

| # | Was | Stand |
|---|---|---|
| G1 | **Gate mit der neuen Kette zusammen testen** | **nie geschehen.** Alle Messungen liefen ohne Gate |
| G2 | **Durchlässigkeit je Stufe messen** | nicht gebaut. Ohne sie versteckt sich der Deadloop eine Ebene tiefer |
| G3 | Vorfilter oder Nachfilter? | offen. Ein Vorfilter ist unsichtbar — was er wegschneidet, sieht das Modell nie |
| G4 | Veto-Schatten für die Rollen-Ebene | existiert für Hebel, für die neue Kette ungeprüft |

### STUFE 2 — LAGEBILD

| # | Was | Stand |
|---|---|---|
| L1 | **Marktbreite raus** | **ERLEDIGT 12.08.** — ersatzlos, nach Review (Arbeitsstand 7.31). `agent/marktbreite.py` hat **keinen Aufrufer mehr**; sechs `messe_*.py` gehen jetzt über `baue_lagebild_eingabe()`. **Pflicht-Begleitfix:** `waechter_zuspitzung` kennt jetzt beide Schreibweisen — sonst hätte er nach der Streichung jeden Grad als unbelegt gemeldet, auch den wahren |
| L2 | **Volatilitätslage** je Klasse | **ERLEDIGT 12.08.** — `agent/marktlage.py::beschreibe_volatilitaet()`, Benchmark je Klasse, Perzentil der eigenen Historie. Geprüft über vier Phasen: Krypto 0. Perzentil in der ruhigen Phase, 96. im Bären |
| L3 | **Trendlage des Klassen-Benchmarks** | **ERLEDIGT 12.08.** — `beschreibe_trend()`, zwei Aussagen aus zwei Quellen (Moskowitz/Ooi/Pedersen 2012 · George/Hwang 2004). Vier Prüfungen bestanden, `pruefe_trendlage.py`. **Befund:** die alte Strukturaussage unterscheidet ein +92 %-Jahr nicht von einem −50 %-Jahr — auf 100 % der Tage (Arbeitsstand 7.29) |
| L6 | **BTC-Historie nachladen** | **ERLEDIGT 12.08.** — 2.526 Zeilen ab 2017-08-17 von Binance, Naht zu Kraken gemessen (Median 0,039 %), Herkunft als `binance_historie` markiert. **Auf dem Notebook noch auszuführen** (8e.3) — die DB reist nicht über Git. Arbeitsstand 7.32 |
| L4 | **Liquiditätslage** | **ERLEDIGT 12.08.** — Amihud (2002) als Perzentil. Drei Kandidaten gebaut, zwei gemessen verworfen: reiner Umsatz (Korr. 0,78 zur Volatilität) und Corwin/Schultz (Niveau um Faktor 20–70 falsch, 36–58 % degeneriert). Arbeitsstand 7.30 |
| L5 | Zuspitzungs-Wächter anschließen | **ERLEDIGT 12.08.** — `rollen_eingabe.pruefe_lagebild()`, an zwei Fällen geprüft |

**Heute liefert das Lagebild zwei Sätze, beide Marktbreite. Eine von vier Dimensionen.**

### STUFE 3 — BEFUND / ENTSCHEIDUNG

| # | Was | Stand |
|---|---|---|
| E1 | **Finanzierungsrate anschließen** | **ERLEDIGT 12.08.** — im Faktensatz sichtbar, Vergleichsarm über `mit_finanzierung=False` |
| E2 | **Relative Stärke zum Klassen-Benchmark** | fehlt für Aktien/ETF/Rohstoffe |
| E3 | **Rang unter den Kandidaten** | seit 10.08. benannt, nicht gebaut |
| E4 | Insider · Short Interest · COT · Fundamentaldaten | **Module fertig**, nie angeschlossen |
| E5 | Befund und Entscheidung trennen? | offen — Argument ist der Bestandsblock |
| E6 | Persona im Prompt behalten? | offen, schaltbar gebaut, nie gemessen |
| E7 | Fibonacci | **entschieden: kommt nicht rein** |

### STUFE 4 — VALIDATOR, BETRAG, AUSSTIEG

| # | Was | Stand |
|---|---|---|
| V1 | **`umgeworfen_durch` auswerten** | wird erzeugt, prüfbar formuliert, **nie gelesen**. Das ist der Ausstieg |
| V2 | Degradierte Käufe sichtbar machen | entschieden mit vier Sicherungen, nicht gebaut |
| V3 | Betrag deterministisch | **gebaut** |
| V4 | Zeitschranke an die Zieldistanz koppeln | offen |

### STUFE 5 — LLM2 / GEGENPRÜFUNG

| # | Was | Stand |
|---|---|---|
| Z1 | **Gegenprüfer für die neue Kette** | **existiert nicht.** Alte Kette hat Z.ai, neue nichts |
| Z2 | Falls gebaut: eigener Aufruf | R-A8, entschieden |

### STUFE 6 — AUSGABE

| # | Was | Stand |
|---|---|---|
| A1 | E-Mail je Asset aus der neuen Kette | unverändert vom Altsystem |
| A2 | GUI-Anzeige | unverändert |

### QUERSCHNITT

| # | Was | Stand |
|---|---|---|
| Q1 | Die Messskripte auf `rollen_eingabe` umstellen | **teilweise 12.08.** — Helfer und `baue_eingaben` umgestellt, die sechs Messskripte importieren sie über `pruefe_rollenkette` weiter mit. Eigene Aufbauten dort noch offen |
| Q2 | Uniqueness-Gewichtung in die Messwerkzeuge | nicht gebaut |
| Q3 | Granularitätswächter | **gebaut**, beide Ladepfade |
| Q4 | Abdeckungsprüfung | **gebaut** |
| Q5 | OD7L ohne Futures-Referenz | ungeklärt |
| Q6 | 5 Krypto ohne Funding | bleiben bei zwei Faktoren |
| Q7 | ETF strukturell ungeeignet | Befund: 2 Faktoren, 0,52 R Kosten. Nutzerentscheidung |

### OFFENE MESSUNGEN

| # | Frage | Umfang |
|---|---|---|
| M1 | Betragsfrage — letzte ungeprüfte Einzelerklärung | ~256 Aufrufe, Abbruchregel steht |
| M2 | Bestandsblock färbt die Belege? | gepaart |
| M3 | Persona | gepaart |
| M4 | **Qualität nach Vervollständigung** gegen die Ausgangsmessung vom 12.08. | erst wenn L1–L4 und E1–E3 stehen |

### GRUNDSÄTZLICH OFFEN

| | Befund | Folge |
|---|---|---|
| Timing | 34,0 % gegen 33,3 % bei reinem Zufall | keine gemessene Kante aus Kursdaten |
| Kosten | 0,17–0,52 R gegen +0,03 R brutto | keine Geometrie trägt sich |
| Akkumulation | antizyklisch schlägt die Kontrolle nicht | AZ-4-Zusatzannahme unbelegt |
| **Nachrichten** | **einzige unerprobte Kategorie** | die einzige mögliche dritte Quelle |

### Was am 12.08. gesichert ist

- **Der Deadloop ist aufgehoben** — 34 % gegen 0 % auf denselben 50 Fällen
- **Das System reagiert auf die Information** — Phasenzeilen deutlich verschieden
- **Die Basisqualität der Rolleninformationen ist NICHT erreicht** — eine von vier
  Dimensionen, zwei von drei bis vier Quellen

---

## 8e.3 AUSROLL-CHECKLISTE

*Abzuarbeiten, wenn die Rollen-Ebene in die Produktion geht. Jeder Punkt einmal
teuer gelernt.*

- [ ] `git fetch` vor dem Push — das Notebook hatte schon eigene Commits
- [ ] Als **ein** Paket ausrollen, nicht in Einzelteilen
- [ ] `pruefe_abdeckung.py` auf dem Notebook — Desktop-Zahlen gelten für den 19.07.
- [ ] **Börsen-Klines**-Übernahme erst `--trocken`, dann `--schreiben` (nicht
      mehr yfinance — der ist seit 12.08. abgeschaltet, ebenso CoinGecko)
- [ ] **`python lade_historie_nach.py BTC --schreiben` auf dem Notebook.**
      Die Datenbank steht in `.gitignore` — die 2.526 nachgeladenen BTC-Zeilen
      vom 12.08. liegen **nur auf dem Desktop**. Das Skript reist über Git, die
      Daten nicht. Gefahrlos wiederholbar: es schreibt ausschließlich Tage
      **vor** dem ältesten vorhandenen Datum, ein zweiter Lauf tut nichts
- [ ] Danach prüfen: `SELECT quelle, COUNT(*) … WHERE symbol='BTC'` muss
      `binance_historie` **und** `gemessen` zeigen — die Naht gehört sichtbar
- [ ] Nach dem ersten OHLC-Lauf: Granularitätswarnung im Log lesen
- [ ] Werturteil-, Konstanten- und Zuspitzungs-Wächter grün, sonst Abbruch
- [ ] Kausalitätsprobe auf `lagebeschreibung.py`
- [ ] Gate-Durchlässigkeit **von Anfang an** mitzählen — sonst verschiebt sich
      der Deadloop eine Ebene tiefer, unbemerkt
- [ ] Erste Signale der neuen Kette **lesen**, nicht nur zählen (Lehre vom 10.08.)
- [ ] Kontingent vor dem Start: Gemini 500/Tag je Modell, Reset 09:00 MESZ.
      Ein Desktop-Lauf nimmt der Produktion Kontingent weg, sobald sie läuft

---

## 8b.7 Empfohlene Reihenfolge

1. **QW2** (Export-Ergänzung `score_details_json` / `funding_rate_aktuell`) —
   klein und ohne Verhaltensrisiko. **QW1 ist zurückgezogen** (siehe 8b.1)
2. **QW3** (AZ-4 laufen lassen) — Skript liegt fertig, beantwortet die
   Maßstabsfrage für Spot
3. **W1** (Hedge-Erfolgsmaß) — hängt an nichts, schaltet W2 frei
4. **QW4** (Ausstieg) — deine Entscheidung, 27,2 R liegen bereit
5. **W4** (Befolgungsgrad) — der größte Hebel auf die Aussagekraft, aber
   auch der größte Aufwand: für Hebel muss die Funktion erst gebaut werden

**Bewusst nicht auf dieser Liste:** neue Fakten fürs LLM, weitere Gates, mehr
Symbole. Acht Selektionsmechanismen wurden gemessen, **keiner trug nachweisbar**
— die Grenze liegt nicht bei der Auswahl, sondern bei Ausstieg, Kostendeckung
und Maßstab. Diese Aussage aus dem Zwischenstand hat die heutige Prüfung
bestätigt, nicht widerlegt.

---


---

# 8c. Warum die Nicht-Krypto-Klassen fast nur HALTEN sagen (07.08.2026)

**Anlass:** Nutzer-Beobachtung "da hier keine Signale und Empfehlungen kommen".
Nachgemessen: es kommen sehr wohl Signale — **201 Nicht-Krypto-Spot-Signale**
allein im Exportfenster. Sie lauten nur fast alle HALTEN.

| Klasse | HALTEN | KAUFEN/NACHKAUFEN | VERKAUFEN |
|---|---|---|---|
| Aktien | 43 | **0** | **0** |
| Themen-ETF | 89 | **0** | **0** |
| Rohstoffe | 65 | **0** | 4 |
| Hedge | 20 | 14 | 2 |

Aktien und Themen-ETF haben in der **gesamten Historie nie etwas anderes als
HALTEN** gesagt.

## Drei Ursachen, nach Gewicht

### 1. Es fehlt das Akkumulations-Framework — der Hauptgrund

Wortzählung in den System-Prompts:

| Prompt | „Tranche" | „antizyklisch" |
|---|---|---|
| **Krypto-Spot** | **7** | **15** |
| Aktien | – | – |
| Themen-ETF | – | – |
| Rohstoffe | – | – |

Krypto-Spot hat ein vollständiges Aufstockungs-Konzept: Tranchen, antizyklische
Zonen, Boden-Zielzone. Die drei anderen Spot-Klassen **kennen `NACHKAUFEN` nur
als Wort, ohne Mechanik dahinter**.

Für eine langfristig gehaltene Position ohne Aufstockungs-Anlass bleiben genau
zwei sinnvolle Antworten: HALTEN (These intakt) oder VERKAUFEN (These
gebrochen). Regel 6 der Prompts schreibt das sogar ausdrücklich vor:

> *„Ist nur (a) schwach, aber (b) intakt, empfiehl HALTEN trotz kurzfristiger
> Schwäche."*

**Das System verhält sich also regelkonform.** Die Lücke ist nicht ein Fehler
im Modell, sondern eine fehlende Handlungsoption im Regelwerk.

### 2. Ein Viertel erreicht das LLM gar nicht — aber der Großteil ist Vergangenheit

**49 von 201** Signalen sind Fixed-Signale ohne jede Analyse. Beim Nachdatieren
zeigt sich jedoch, dass zwei der drei Gründe **bereits behoben sind**:

| Grund | Anzahl | Zeitraum | seit 05.08. |
|---|---|---|---|
| Historie veraltet (ISOC, letzter Tag 2025-09-10) | 6 | 18.–27.07. | **0** |
| keine historischen Daten (X136) | 6 | 18.–27.07. | **0** |
| Preis veraltet oder nicht vorhanden | 38 | 07.07.–05.08. | **13** |

ISOC führt heute 3.646 OHLC-Punkte bis zum 06.08., X136 156 Punkte bis zum
06.08. — **beide Historien sind längst nachgeladen.** Ein Vorschlag „ISOC/X136
reparieren" wäre Arbeit an einem erledigten Punkt gewesen; erst die Datierung
der Fälle hat das gezeigt.

**Was bleibt: „Preis veraltet"**, 13 Fälle seit dem 05.08. Das ist aber **kein
Nicht-Krypto-Problem** — betroffen sind auch BTC (12×), ETH, SEI, KAS. Es
gehört zur Staleness-Überwachung insgesamt, nicht in diese Untersuchung.

### 3. Das Gate ist NICHT die Ursache

In der gesamten Historie: **5 Risk-Vetos** (R-5.10, Konfidenz unter
Regime-Schwelle), 0 Cash-Vetos. Die HALTEN kommen vom Modell, nicht vom Filter.
Die Konfidenz liegt mit Median 66 % nur knapp unter Krypto (70 %) — das Modell
ist nicht ratlos, es hat schlicht keinen Anlass zu handeln.

## Der Zeithorizont — die zweite Hälfte der Antwort

**Nutzer-Vorgabe (07.08.):** Spot, ETF, Aktien und Rohstoffe werden über
**Monate** gehalten; Hebel über **1–5, maximal 14 Tage**.

Was das System heute tut:

| | |
|---|---|
| Ablauffristen (gestaffelt, ✔) | kurz 14 / mittel 45 / lang 120 Tage |
| Zuordnung | **vom LLM je Signal** über `halte_kriterium_bucket` |
| Basislinien-Horizont | **fest 14 Tage für ALLE Klassen** |

Daraus folgen zwei Messfehler:

**(a) Die Basislinie passt nicht zum Horizont.** Eine Position mit 120 Tagen
Frist wird gegen einen 14-Tage-Zufallseinstieg verglichen. Der Signalbeitrag
(`Expectancy − Basislinie`) ist damit für die langfristigen Klassen
systematisch falsch berechnet.

**(b) Der Horizont kommt vom Modell, nicht von der Assetklasse.** 1.117 von
1.703 Hebel-Signalen tragen `mittel` = 45 Tage — bei einer Handelspraxis von
1–5 Tagen. Umgekehrt liegen 59 von 89 Themen-ETF-Signalen ebenfalls auf
`mittel`, obwohl dort Monate gemeint sind. **Beide Klassen bekommen denselben
Bucket für völlig verschiedene Praxis.**

> **Das ist die „andere Lösung", nach der gefragt wurde:** der Zeithorizont
> gehört an die **Assetklasse** gebunden, nicht an das Einzelurteil des Modells.
> Das Modell darf innerhalb des Klassenrahmens verfeinern, aber nicht einen
> Hebel-Trade auf 45 Tage stellen, wenn die Praxis 1–5 Tage ist.

## Was daraus folgt — Vorschläge, nach Aufwand

| # | Maßnahme | Aufwand | Wirkung |
|---|---|---|---|
| ~~H-1~~ | ~~ISOC/X136-Historie reparieren~~ — **bereits behoben**, letzter Fall 27.07.; beide führen heute Daten bis zum 06.08. | — | zurückgezogen |
| **H-2** | Zeithorizont je Assetklasse **deckeln** statt frei vom LLM setzen zu lassen | mittel | behebt (b); Voraussetzung für jede Aussage über Haltedauer und Kosten |
| **H-3** | Basislinien-Horizont an den Bucket koppeln statt fest 14 Tage | mittel | behebt (a); ohne ihn ist der Signalbeitrag der langfristigen Klassen falsch |
| **P-1** | **Spot-Kostensätze je Klasse trennen** (1 %/Seite gilt heute für Bitpanda-Krypto UND Börsen-Aktien) + laufende Gebühr für Hedge-ETPs | mittel |
| **P-2** | **RM-3 entscheiden** — `max_allokation_pro_klasse_prozent` steht auf 0 für Aktien/ETF/Rohstoffe und wird nirgends gelesen | klein |
| **P-3** | `crv_minimum` / `risiko_pro_trade_prozent` je Klasse prüfen — heute global | mittel |
| **H-4** | Akkumulations-Konzept für Aktien/ETF/Rohstoffe | groß | **der eigentliche Hebel** — ohne ihn bleibt HALTEN die einzige regelkonforme Antwort |

**H-4 ist die Ursache, H-2 und H-3 sind Voraussetzungen dafür, dass man den
Erfolg von H-4 überhaupt messen könnte.** Ein Akkumulations-Konzept einzuführen,
während die Basislinie den falschen Horizont hat, würde eine Verbesserung
erzeugen, die man nicht belegen kann.

**Nicht auf der Liste, bewusst:** die Gates lockern. Sie sind nachweislich nicht
die Ursache (5 Vetos gesamt), und eine Lockerung würde die Diagnose verwischen.



---

# 8d. Der Ausbaustand-Drift — die Nicht-Krypto-Klassen hängen vier Wochen zurück (07.08.2026)

**Anlass:** Nutzer-Einwand zu 8c — *„hier musst du bei den Multi- oder sonstigen
Assets genau achten, wo und wie diese umgesetzt wurden, u. U. hängen die noch
Wochen zurück vom Code und Themenlage."*

Berechtigt. Abschnitt 8c hatte implizit angenommen, die Nicht-Krypto-Pipelines
seien „Krypto minus Akkumulation". **Gemessen ist der Rückstand deutlich
größer — und systematisch.**

## Wann kam welcher Fakt, und wo blieb er stehen

| Fakt | Krypto-Spot | Hebel | Aktien | Themen-ETF | Rohstoffe |
|---|---|---|---|---|---|
| `markt_kontext` | 09.07. | 14.07. | **nie** | **nie** | **nie** |
| `regime_profil` | 09.07. | 14.07. | **nie** | **nie** | **nie** |
| `antizyklisch` | 09.07. | 14.07. | **nie** | **nie** | **nie** |
| `tranchen_erlaubt` | 12.07. | — | **nie** | **nie** | **nie** |
| `liquiditaetszonen` | 23.07. | 23.07. | **nie** | **nie** | **nie** |
| `signal_stabilitaet` | 25.07. | 25.07. | **nie** | **nie** | **nie** |
| `marktscan_reifegrad` | 30.07. | — | **nie** | **nie** | **nie** |
| `ausstiegsregel` | — | 05.08. | **nie** | **nie** | **nie** |
| `systemguete` | — | 05.08. | **nie** | **nie** | **nie** |
| `kosten` | — | 05.08. | **nie** | **nie** | **nie** |
| `crv_baender` | 06.08. | 06.08. | **06.08.** | **06.08.** | **06.08.** |

> **Genau EIN Fakt wurde je auf alle fünf Spot-Klassen ausgerollt** —
> `crv_baender`, gestern. Alles andere aus vier Wochen Weiterentwicklung ging
> ausschließlich an Krypto und/oder Hebel.

Der Stand der Nicht-Krypto-Analysten entspricht damit im Kern dem **09.07.**

## Dasselbe Bild auf Pipeline-Ebene

| Mechanismus | Krypto | Hebel | Aktien | ETF | Rohst. | Hedge |
|---|---|---|---|---|---|---|
| Z.ai-Gegenprüfung | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| Risikofaktoren | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ (seit heute) |
| Fazit-Konsistenz | ✔ | ✔ | ✔ | ✔ | ✔ | ✔ |
| CRV-Bänder | ✔ | ✔ | ✔ | ✔ | ✔ | — |
| **Selbst-HALTEN-Tracking** | ✔ | ✔ | **—** | **—** | **—** | — |
| **`original_action`** | ✔ | ✔ | **—** | **—** | **—** | — |
| **Mindestziel** | ✔ | ✔ | **—** | **—** | **—** | — |
| **Ausstiegsregel** | — | ✔ | — | — | — | — |
| **Systemgüte-Fakt** | — | ✔ | — | — | — | — |
| Kostenmodell | — | — | — | — | — | — |
| JIT-Historie | — | — | ✔ | ✔ | ✔ | — |

| | Mechanismen |
|---|---|
| Hebel | **9 von 12** |
| Krypto-Spot | 7 von 12 |
| Aktien / Themen-ETF / Rohstoffe | **5 von 12** |
| Hedge | **3 von 12** |

## Was das für 8c bedeutet

Die HALTEN-Diagnose bleibt richtig, aber ihre **Ursache ist breiter** als dort
beschrieben. Es fehlt nicht nur das Akkumulations-Framework — es fehlen sechs
von elf Weiterentwicklungen seit dem 09.07.

Zwei Folgerungen, die vorher nicht sichtbar waren:

**1. `original_action` fehlt → 8c konnte eine Frage gar nicht beantworten.**
In 8c stand: „bei allen Nicht-Krypto-Signalen ist `original_action = None`, also
lässt sich nicht unterscheiden, ob das LLM HALTEN sagte oder ein Gate es
überschrieb." Der Grund ist jetzt klar — das Feld wird in diesen Pipelines nie
gesetzt. **Die Unterscheidung ist strukturell unmöglich, nicht nur ungemessen.**

**2. Der Rückstand ist kein Zufall, sondern ein Muster.** Jede Erweiterung wurde
dort gebaut, wo gerade gearbeitet wurde — Krypto-Spot, dann Hebel. Der Rollout
auf die übrigen Klassen war nie Teil der Definition von „fertig". `crv_baender`
am 06.08. ist die einzige Ausnahme, und sie war ausdrücklich gefordert
(*„nicht selektiv für eine Funktionalität sondern über alle Assets korrekt
anpassen"*).

> **Konsequenz für die Arbeitsweise:** eine Erweiterung an einer Pipeline ist
> nicht fertig, wenn sie dort läuft. Sie ist fertig, wenn entschieden ist, ob
> sie für die anderen fünf gilt — und die Entscheidung dokumentiert ist. Ein
> „gilt nur für Krypto, weil X" ist ein gültiges Ergebnis; ein stilles
> Auslassen nicht.

## Was daraus folgt — Ergänzung zur Maßnahmenliste aus 8c

Die Reihenfolge aus 8c bleibt, aber H-4 wird größer und bekommt Vorstufen:

| # | Maßnahme | Aufwand |
|---|---|---|
| **H-5** | **Rollout-Prüfung als Pflichtschritt** — bei jeder Fakten-/Regel-Änderung entscheiden UND dokumentieren, ob sie für alle sechs Pipelines gilt | klein, dauerhaft |
| **H-6** | `original_action` + Selbst-HALTEN-Tracking auf die Spot-Familie ausrollen | klein |
| **H-7** | `ausstiegsregel`, `systemguete`, `kosten` von Hebel auf die Spot-Familie prüfen | mittel |
| **H-4** | Akkumulations-Konzept (`antizyklisch`, `tranchen_erlaubt`) für Aktien/ETF/Rohstoffe | groß |

**H-6 ist der günstigste Punkt der ganzen Liste** und macht 8c erst
auswertbar — ohne `original_action` bleibt unbeantwortbar, wie viele der HALTEN
vom Modell und wie viele vom Gate kommen.

**H-5 ist der eigentliche Befund.** Ohne ihn entsteht derselbe Drift bei der
nächsten Erweiterung wieder.



---

# 8e. Zwei Konzeptfragen: Bitpanda-Gebühren und Schwerpunkte/Screener (07.08.2026)

**Anlass:** zwei Nutzer-Punkte vor dem H-4-Umbau — *„zu den Gebühren bei BP ist
es problematisch, kannst du die aktuellen bzw. fehlenden Bereiche recherchieren
und wir einigen uns auf ein Konzept, sonst wird es u. U. nicht handhabbar"* und
*„was in deinem aktuellen Konzept noch nicht ausreichend Beachtung findet: die
Screener-Seite und die thematische Einteilung … dann sollen die Vorschläge und
Signale einen Fokus bzw. Priorität bei diesen setzen"*.

## A. Bitpanda-Gebühren — recherchiert

| Klasse | **Struktur** | Wert |
|---|---|---|
| Krypto, Standard (BTC) | prozentual, **im Kurs enthalten** | 0,99 % |
| Krypto, Altcoins | prozentual, im Kurs | bis 2,49 % |
| Krypto-Indizes | prozentual | 1,99 % |
| Bitpanda Fusion (Vieltrader) | Maker/Taker + Spread | 0,02–0,25 % |
| **Aktien / ETFs** | **FIX + Spread** | **1 € je Trade**, Spread bis 0,5 % |
| Sparpläne (Aktien/ETF/ETC) | — | **kommissionsfrei** |
| Edelmetalle (Bitpanda Metals) | prozentual, **asymmetrisch** | Gold 0,50 % Kauf / 1,00 % Verkauf · Silber 2,50 / 2,00 · Platin 2,50 / 2,00 · Palladium 2,20 / 1,80 |
| Depot / Verwahrung | — | 0 |

### Drei strukturelle Probleme, nicht nur falsche Zahlen

**1. Aktien und ETFs haben eine FIXE Gebühr — der Einsatz kürzt sich nicht mehr
heraus.** Das ist der Kern. Unser Kostenmodell beruht auf der Eigenschaft, dass
`Kosten in R` nur an Hebel, Haltedauer und Stop-Abstand hängt. Bei 1 € pro Trade
gilt das nicht mehr:

| Position | Stop 5 % → Risiko | Gebühr Roundtrip | **Kosten in R** |
|---|---|---|---|
| 300 € | 15 € | 2 € | **0,133 R** |
| 1.000 € | 50 € | 2 € | **0,040 R** |
| 2.000 € | 100 € | 2 € | **0,020 R** |

Das aktuelle Modell setzt für alle drei **0,400 R** an — also **3- bis 20-fach
zu hoch**.

**2. Die Gebühr ist bei Bitpanda nicht separat ausgewiesen — sie steckt im
Kurs.** An 5.734 echten Trades geprüft: `Fiat-Betrag ÷ (Menge × Preis)` ergibt
**0,000 % Median**. Aus den Transaktionsdaten allein ist die Gebühr also **nicht
messbar**; es braucht einen Referenzkurs zum selben Zeitpunkt.

**3. Krypto ist coin-abhängig** (0,99 % BTC bis 2,49 % Altcoin). Pauschal 1 % je
Seite ist für BTC/ETH plausibel und für kleine Coins zu niedrig — also in die
**andere** Richtung falsch als bei Aktien.

### Konzeptvorschlag — drei Stufen, bewusst nicht symbolgenau

Eine exakte Modellierung bräuchte je Symbol einen Satz, plus Positionsgröße,
plus Kauf/Verkauf-Asymmetrie. Das ist nicht pflegbar — genau der
Handhabbarkeits-Einwand. Stattdessen:

**Stufe 1 — Struktur je Klasse statt eines Satzes für alle.** Zwei Kostenarten
statt einer: `prozentual` (Krypto, Edelmetalle) und `fix_plus_spread`
(Aktien/ETF/ETC). Das behebt den eigentlichen Fehler und ist ein überschaubarer
Eingriff in `kosten_in_r()`.

**Stufe 2 — ein konservativer Satz je Klasse, dokumentiert, nicht je Symbol.**
Vorschlag als Ausgangspunkt:

| Klasse | Ansatz |
|---|---|
| Krypto | 1,5 % je Seite (Mitte zwischen BTC 0,99 und Altcoin 2,49) |
| Aktien / Themen-ETF | 1 € je Seite + 0,25 % Spread |
| Rohstoff-ETCs | wie Aktien — es sind **börsengehandelte ETCs**, nicht Bitpanda Metals |
| Hedge-ETPs | wie Aktien, **plus** laufende Gebühr (TER) — die fehlt heute ganz |

> **Wichtige Abgrenzung:** OD7N/OD7H/OD7C/OD7L sind **ETCs über die Börse**,
> nicht Bitpanda-Metals. Die Metals-Aufschläge (Silber 2,5 %/2,0 %!) gelten für
> sie **nicht**. Wer sie verwechselt, rechnet mit dem Dreifachen.

**Stufe 3 — messen statt schätzen, sobald die Datenlage es hergibt.** Der
Spread ist gegen die eigene Kursreihe messbar: Handelspreis gegen Tagesschluss,
Kauf und Verkauf getrennt. Erster Versuch mit dem 90-Tage-Exportfenster ergab
n = 31 Käufe / 16 Verkäufe — **zu wenig für eine Aussage**, und der
Tagesschluss-Vergleich mischt Intraday-Bewegung in den Spread. Gegen die
vollständige OHLC-Tabelle auf dem Notebook wäre es belastbar. Bis dahin bleibt
`kosten_belegt = False`, und das ist ehrlich.

## B. Schwerpunkte und Screener — der Befund

### Was heute existiert

Sechs aktive Kategorie-Thesen mit Richtung:

| Hauptgruppe | Richtung |
|---|---|
| energie | **übergewichten** |
| edelmetalle | **übergewichten** |
| agrarrohstoffe | neutral |
| industriemetalle | neutral |
| absicherung | aktiv / inaktiv |

Dazu Prüfmechanismen (COT-Positionierung, M2-Liquidität, Zinskurve,
Dollar-Index, EIA-Erdgas, Bärenmarkt-Overlay), 105 Synthese-Läufe, 16
Änderungsvorschläge, und `these_abgleich` als Fakt in den Analysten für Aktien,
Rohstoffe, Themen-ETF und Hedge.

### Vier Lücken

**1. Der Budget-Allocator kennt die Thesen nicht.** Keine einzige Erwähnung von
These/Kategorie/Schwerpunkt in `agent/krypto/budget_allocator.py`. Eine
**übergewichtete** Kategorie bekommt damit **keinen bevorzugten LLM-Slot** —
genau der „Fokus", der gemeint ist, existiert an der Stelle nicht, wo er wirken
müsste.

**2. Keine aktive Benachrichtigung** für Screener-Kandidaten je Schwerpunkt.
Der Gap ist seit dem **19.07.** bekannt („Lücke 7") und wurde **zweimal nur
passiv** geschlossen: GUI-Sortierung (20.07.) und ein Score-Bonus als sekundärer
Sortierschlüssel (25.07.). Nie bis zur Benachrichtigung zu Ende gedacht.

**3. Die Thesen decken nur Rohstoff-Hauptgruppen und Absicherung ab.** Es gibt
**keine These für Krypto, Aktien oder Themen-ETF** — obwohl das Beispiel des
Nutzers ausdrücklich „KI" nennt. Ein Schwerpunkt „KI" ließe sich heute gar nicht
setzen.

**4. Kein Override.** Die Thesen entstehen aus Prüfmechanismen und
LLM-Synthese. Ein manuell gesetzter Schwerpunkt („ab jetzt Fokus Rohstoffe") ist
nicht vorgesehen.

### Warum das H-4 vorgelagert ist

Ein Akkumulations-Konzept beantwortet die Frage *„wann aufstocken?"*. Der
Schwerpunkt beantwortet *„wo überhaupt hinsehen?"*. Baut man H-4 zuerst,
entsteht eine Aufstockungslogik, die alle Kategorien gleich behandelt — und der
Schwerpunkt müsste nachträglich wieder hineinoperiert werden.

**Vorschlag zur Reihenfolge:** die Lücken 1, 3 und 4 sind klein und unabhängig
voneinander baubar. Lücke 2 (Benachrichtigung) braucht die Detailklärung, die
seit dem 30.07. dokumentiert offen ist (Trigger, Cooldown, E-Mail-Format).



---

# 8f. Warum nur Rohstoffe eine These haben — der Deckel, nicht die Mechanik (07.08.2026)

**Anlass:** Nutzer-Hinweis, es gebe bereits ein Grobkonzept mit Haupt- und
Untergruppen, und *„bei Rohstoffen haben wir nur begonnen"*. Beides bestätigt —
und die Ursache ist eine andere, als Abschnitt 8e vermutet hatte.

## Die Struktur ist vollständig, nicht angefangen

`Basisinfos/kategorien.yaml`: **10 Hauptgruppen, 72 Unterkategorien, 211
zugeordnete Bitpanda-Symbole.**

| Hauptgruppe | Unterkat. | Symbole | These |
|---|---:|---:|---|
| Edelmetalle | 4 | 6 | übergewichten |
| Industriemetalle | 8 | 9 | neutral |
| Energie | 9 | 19 | übergewichten |
| Agrarrohstoffe & Nahrungsmittel | 8 | 17 | neutral |
| Absicherung / Hedge | 2 | 0 | aktiv |
| **Technologie & KI** | **18** | **24** | **—** |
| **Aktien – Regionen & Länder** | 7 | **66** | **—** |
| **Aktien – Sektoren** | 8 | 23 | **—** |
| **Anleihen & Geldmarkt** | 6 | 26 | **—** |
| **Sonstige** | 2 | 21 | **—** |

**160 von 211 Symbolen (76 %) haben kein Themenfeld-Urteil.**

> **Korrektur zu meinem eigenen Vorschlag von vorhin:** ich hatte gefragt, ob
> „KI" als neue Hauptgruppe oder als eigene Ebene angelegt werden soll.
> **Beides überflüssig** — „Technologie & KI" existiert seit dem 19.07. samt
> Unterkategorie „Künstliche Intelligenz". Hätte ich vor dem Vorschlag in die
> Doku gesehen, wäre die Frage nicht entstanden.

## Auch die Mechanik ist gebaut — für genau diese Kategorien

`_BELLWETHER_TICKER` deckt bereits ab: `technologie_ki:ki`,
`technologie_ki:halbleiter`, `technologie_ki:cybersicherheit`,
`technologie_ki:biotech`, dazu vier `aktien_sektoren:*`. Der Mechanismus
kombiniert Analystentrend (Finnhub), Insider-Aktivität (SEC EDGAR) und
Short-Interest (FINRA).

Und er **läuft**: von 16 Änderungsvorschlägen im Export entfallen

- **4 auf `technologie_ki`** (ki, halbleiter, cybersicherheit, biotech)
- **6 auf `aktien_sektoren`**
- 2 auf `aktien_regionen`, 1 auf `anleihen_geldmarkt`

Beispiel `technologie_ki:ki`, in Beobachtung **seit dem 25.07.**:
*„Analystentrend (Finnhub, MSFT, PLTR): Buy+StrongBuy-Anteil 81 % vs. Vormonat
80 % … Insider-Aktivität (SEC EDGAR): 0 Käufer vs. 13 Verkäufer"* — Vorschlag
`meiden`.

## Die eigentliche Ursache: ein Deckel bei 6

```
kategorie_vorschlaege.richtgroesse_max_aktive_thesen: 6
aktive Thesen heute:                                  6
verbleibendes Budget:                                 0
```

`_bestimme_gesperrte_fall_a_kandidaten()` rechnet
`budget = richtgroesse_max − aktuelle_anzahl`. Bei sechs aktiven Thesen ist das
**null** — **kein reifer Vorschlag kann mehr automatisch übernommen werden.**

Der Status der 16 Vorschläge belegt es: **14 × „beobachtung", 1 × „offen",
1 × „übernommen"**.

**Das ist kein Bug.** Die Richtgröße 3–6 ist eine bewusste Entscheidung
(`Kategorie_Basisinformationen_Release2.md`, Abschnitt 5). Der Punkt ist ein
anderer:

> **Die sechs Plätze sind von den Rohstoffen belegt, weil sie zuerst da
> waren — nicht weil sie die wichtigsten wären.** Zwei davon stehen auf
> `neutral` (Agrarrohstoffe, Industriemetalle) und belegen denselben Platz wie
> eine potenziell relevante KI-These. Es gibt keinen Verdrängungsmechanismus:
> first come, first served statt Priorität.

## Was daraus folgt

| # | Maßnahme | Aufwand |
|---|---|---|
| **S-1** | **Verdrängung statt Sperre**: wird ein Vorschlag reif und das Budget ist voll, die schwächste bestehende These (z. B. `neutral` ohne Bewegung seit X Tagen) gegen die neue abwägen — statt den Vorschlag stumm zurückzustellen | mittel |
| **S-2** | **Richtgröße spezifikationskonform machen** — die Spezifikation sagt „weich, kein Hard-Limit im Code", implementiert ist ein hartes Budget. Keine neue Zahl nötig, sondern die Rückführung auf die dokumentierte Semantik | klein |
| **S-3** | **Sichtbarkeit**: die 14 wartenden Vorschläge stehen nur im Thesen-Tab. Ein „seit 13 Tagen wartet ein KI-Vorschlag" gehört auf die Übersichtsseite | klein |
| **S-4** | Allocator-Priorität (aus 8e Lücke 1) — erst sinnvoll, wenn die Themenfelder überhaupt Thesen tragen | mittel |

**S-1 und S-2 sind die eigentliche Antwort auf den Nutzer-Wunsch** („ich kann
einen Override bzw. eigene Schwerpunkte setzen"). Ein manueller Override ist
technisch der einfachste Fall von S-1: der Nutzer entscheidet die Verdrängung
selbst.



---

# 9. GESAMTKONZEPT „Vom Themenfeld zum Signal" (07.08.2026)

**Auftrag:** aus den Einzelthemen des Tages und dem Schwerpunkte-Befund (8f)
ein Gesamtkonzept mit kritischer Gegenprüfung, dann von vorne bis hinten
durcharbeiten.

## 9.1 Die Kette — das übergeordnete Thema

Alle Einzelbefunde des Tages hängen an **einer** Kette, die der Nutzer selbst
formuliert hat:

```
① Themenfeld relevant?  →  ② welche Assets darin?  →  ③ bei BP handelbar?
                                                              ↓
      ⑥ Erfolg je Themenfeld  ←  ⑤ Signal mit Fokus  ←  ④ in der Watchlist?
```

Jeder Befund des Tages ist ein Glied dieser Kette:

| Glied | Stand | Befund aus |
|---|---|---|
| ① Themenfeld | Struktur ✔ (10 Gruppen/72 Unterkat.), Mechanik ✔, **blockiert durch Deckel 6** | 8f |
| ② Assets darin | ✔ 211 Symbole zugeordnet | 8f |
| ③ BP-handelbar | ✔ **heute gebaut** (Filter + Schalter + RM-Bitpanda für Hedge) | 8e |
| ④ Watchlist | **manuell, kein Weg vom Kandidaten zur Pipeline** | *neu, siehe 9.3* |
| ⑤ Signal mit Fokus | **Allocator kennt die Thesen nicht** | 8e |
| ⑥ Erfolg je Themenfeld | **existiert nicht** — Systemgüte tiert nach Assetklasse, nicht nach Hauptgruppe | *neu, siehe 9.3* |

Und die zweite Ebene, die unabhängig davon läuft, aber jedes Signal bewertet:

| | Stand | Befund aus |
|---|---|---|
| Kosten je Klasse | **strukturell falsch** (fix vs. prozentual) | 8e |
| Risikoparameter je Klasse | global statt klassenspezifisch | 8e |
| Zeithorizont je Klasse | ✔ **heute gebaut** (H-2/H-3) | 8c |
| Akkumulation (Aufstocken) | **fehlt für 3 von 4 Spot-Klassen** | 8c |

## 9.2 Warum die Reihenfolge zwingend ist

> **Ohne ① gibt es keinen Fokus. Ohne die Kostenebene ist jedes Ergebnis
> unbelastbar. Ohne ⑥ merkt niemand, ob der Fokus etwas taugt.**

Baut man H-4 (Akkumulation) zuerst — wie heute Vormittag geplant —, entsteht
eine Aufstockungslogik, die alle Themenfelder gleich behandelt, auf falschen
Kosten rechnet und deren Wirkung nicht messbar ist. **Drei Umbauten
hintereinander statt einem.**

## 9.3 Kritische Gegenprüfung — fünf Lücken, die in keinem Einzelbefund standen

Diese fünf sind beim Zusammensetzen entstanden, nicht bei den Einzelanalysen:

**G-1 · Vom Kandidaten in die Watchlist führt kein Weg.** Der Screener findet
Kandidaten und taggt sie mit Hauptgruppe/Unterkategorie. Aber nur Assets **in
der Watchlist** bekommen eine Pipeline und damit ein Signal. Der Schritt
dazwischen ist heute vollständig manuell und in keinem Konzept beschrieben.
**Die Kette bricht zwischen ③ und ⑤.**

**G-2 · Kein Erfolgsmaß je Themenfeld.** Die Systemgüte tiert nach Assetklasse
(krypto/aktien/hebel/…), nicht nach Hauptgruppe. Ob eine übergewichtete These
bessere Signale liefert als eine neutrale, ist heute **nicht messbar** — und
damit ist die gesamte Schwerpunkte-Ebene unbelegt. Das ist dieselbe
Kategorie wie der Hedge-Befund von heute früh: eine Ebene ohne eigenes
Erfolgsmaß.

**G-3 · Regime gegen Themenfeld — wer gewinnt?** Das Regime sagt „bär", das
Themenfeld sagt „übergewichten". Heute ist nicht definiert, wie sich das
auflöst. Beide wirken auf dieselbe Entscheidung, und der Konflikt ist
konstruktionsbedingt häufig — ein Themenfeld wird gerade dann interessant, wenn
es billig ist.

**G-4 · „Schwächste These" ist undefiniert.** S-1 (Verdrängung) braucht ein
Maß dafür, welche bestehende These weichen muss. Alter? Richtung `neutral`?
Kein Mechanismus-Signal seit X Tagen? Ohne Definition ist die Verdrängung
willkürlich — und eine willkürliche Verdrängung ist schlechter als der jetzige
Deckel, weil sie Bewegung ohne Begründung erzeugt.

**G-5 · Ein Themenfeld ohne handelbare Assets ist wertlos.** Eine These auf
`technologie_ki:ki` nützt nichts, wenn kein Asset dieser Unterkategorie bei
Bitpanda handelbar oder in der Watchlist ist. Das müsste **beim Anlegen der
These** geprüft werden, nicht erst beim Signal.

## 9.4 Der Plan — sechs Schritte, nach Abhängigkeit geordnet

Stand 07.08. abends. Die Reihenfolge hat sich während der Umsetzung um **einen
Schritt erweitert**, der in der ursprünglichen Tabelle fehlte: die manuellen
Schwerpunkte. Sie kamen aus einer Nutzer-Antwort, nicht aus der Lückenanalyse —
und sie sind Voraussetzung für Schritt 6, weil ein Allocator, der nach
Trendstärke priorisiert, ohne sie systematisch das Gegenteil von antizyklisch
tut.

| # | Schritt | löst | Aufwand | Stand |
|---|---|---|---|---|
| **1** | **Kosten strukturell trennen** (fix vs. prozentual, je Klasse, mit Positionsgröße je Signal) | P-1 | mittel | **ERLEDIGT 07.08.** |
| **2** | **Richtgröße spezifikationskonform** (weich statt hart) + G-5 (Handelbarkeits-Prüfung beim Anlegen) | S-2, G-5 | klein | **ERLEDIGT 07.08.** |
| **3** | **Manuelle Schwerpunkte mit garantiertem Raum** (`schwerpunkte.manuell`, Schalter im Thesen-Tab) | Nutzer-Vorgabe 07.08. | klein | **ERLEDIGT 07.08.** |
| **4** | **Wartende Vorschläge sichtbar machen** (S-3) — plus Layout-Fix im Schwerpunkte-Tab | S-3 | klein | **ERLEDIGT 07.08.** |
| **5** | **Erfolgsmaß je Themenfeld** (G-2) — **nicht** als Systemgüte je Hauptgruppe, siehe unten | G-2 | mittel | **ERLEDIGT 07.08.** |
| **6** | **Allocator-Priorität** (S-4: übergewichtete Themenfelder bevorzugt) — setzt Schritt 3 voraus | S-4 | mittel | **ERLEDIGT 09.08.** — stabile Partition in `multi_asset_batch`, Reichweite offen benannt (siehe unten) |
| **7** | **Rollout-Entscheidungen** der vier offenen Fakten | H-7 | klein je Fakt | **ERLEDIGT 09.08.** — drei waren bereits entschieden, nur nicht vermerkt; `tranchen_erlaubt` gebaut |

**Warum Schritt 5 anders gebaut wurde als geplant:** die Messung vor dem Bau
ergab 101 aufgelöste Signale — und **kein einziges** davon gehört zu einem
Themenfeld. Eine Systemgüte je Hauptgruppe wäre eine Tabelle aus leeren Zellen
und sähe trotzdem aus wie ein Instrument. Gemessen wird deshalb die
**Richtungsaussage auf einen Korb** (Überrendite gegen die übrigen Themen-Assets
seit `gesetzt_am`) plus die **Wirkungskette** — bei Energie haben 2 von 22 Assets
überhaupt eine Kursreihe, und genau das ist die eigentliche Engstelle. Die
Absicherung bleibt draußen: ein Hedge, der verliert während das Portfolio steigt,
hat funktioniert.

**Nachtrag 09.08. — was Schritt 6 geworden ist, und was er NICHT leistet.**
Umgesetzt als **stabile Partition** in `agent/multi_asset_batch.py`:
Schwerpunkt-Assets nach vorn, alle anderen behalten ihre Reihenfolge.
Ausdrücklich **kein** Sortieren nach Trendstärke oder Score — genau davor warnt
dieser Plan, weil das ohne die manuellen Schwerpunkte das Gegenteil von
antizyklisch täte.

Drei Einschränkungen, die vor dem Bau gemessen wurden und ins Ergebnis gehören:

- **Reichweite 13 von 57 Assets.** Nur 7 ETF, 4 Rohstoffe und 2 Aktien tragen
  überhaupt eine `hauptgruppe` — **kein einziges Krypto-Asset**. Die Krypto-Kette
  kann davon nicht profitieren, weil dort nichts zuzuordnen ist.
- **Reihenfolge, nicht Auswahl.** Der Batch hat keinen Stückzahl-Deckel; alle
  Fälligen werden ohnehin verarbeitet. Spürbar wird die Priorität erst, wenn
  mitten im Lauf ein Anbieter-Tagesbudget ausläuft oder der Circuit Breaker
  zuschlägt.
- **Derzeit inert.** `schwerpunkte.manuell` ist leer. Der Mechanismus existiert
  jetzt, damit ein gesetzter Schwerpunkt überhaupt eine Wirkung *haben kann* —
  bis dahin ist er ein No-Op, und der Test prüft ausdrücklich auch das.

**Die Achsenfrage ist am 09.08. ENTSCHIEDEN, nicht offen.** Meine
Formulierung „Krypto fehlt eine Achse" war falsch: Krypto hat eine, sie heißt
nur anders. Der Budget-Allocator sortiert nach `score_gesamt` und legt darüber
die SLA-Reservierung — überfällige Kandidaten nach echter Wartezeit, als
Garantie statt als Score-Boost. **Krypto fehlt keine Priorisierung, sondern eine
themenbasierte** — und die braucht es nur, wenn man Krypto nach Unterthemen
steuern will.

**Nutzer-Entscheidung 09.08.: Thema bestätigt, Umsetzung vertagt.** Statt zu
bauen wurde die *Naht* gezogen: die Regel steht jetzt zentral in
`agent/schwerpunkt_prioritaet.py` und gilt für jede Assetklasse, sobald eine
zweite sie braucht. Die Krypto-Kette ruft sie ausdrücklich **nicht** auf — ein
Aufruf ohne `hauptgruppe`-Daten wäre ein toter Aufruf, also genau die stille
Attrappe, die dieses Projekt schon zweimal in die Irre geführt hat.

**Ausgangspunkt für später, falls es soweit kommt** (Nutzer-Hinweis 09.08.): die
Achse wären die zugrundeliegenden **Narrative**, mit **BTC gegen Altcoins als
Grundgruppe**, danach feinere Narrative innerhalb der Altcoins. Der technische
Teil ist eine Zeile; der Aufwand liegt in der Taxonomie, und die bildet eine
Anlagesicht ab, keine Datenstruktur.

`teste_allocator_prioritaet.py`, 9 Prüfungen gegen 13 echte Kandidaten: leere
Liste ist ein No-Op, Hauptgruppen-Schwerpunkt zieht drei Assets vor,
Unterkategorie-Schwerpunkt genau zwei, die Menge bleibt gleich, und die übrigen
behalten ihre Reihenfolge.

**Was Schritt 2 verändert hat, und was dabei kippte:** die Spezifikation stand
in *beiden* Halbsätzen auf dem Kopf — im Code ein hartes Limit, in der GUI gar
nicht angezeigt, und die Untergrenze 3 existierte überhaupt nicht. Das
Hauptargument für den Deckel (mehr Thesen verwässern die Screener-Rangfolge)
hält nicht stand: der Bonus hängt am objektiven `compute_these_abgleich()`, nicht
an der Existenz einer These. Zwei Messungen haben die Umsetzung geändert —
**G-5 feuert heute bei keiner einzigen Kategorie** (alle 72 Unterkategorien haben
mindestens ein handelbares Asset), und eine Prüfung nur über den Bitpanda-Katalog
hätte ausgerechnet die beiden Hedge-Kategorien gesperrt, die aktiv gehalten
werden. Offen benannt: die Schutzwirkung der manuellen Schwerpunkte aus Schritt 3
ist damit gegenstandslos geworden — sie wird erst in Schritt 6 wieder greifen.

**Was Schritt 4 gebracht hat, über die Sichtbarkeit hinaus:** beim Datieren der
Vorschläge löste sich der vermutete „Themen-Deckel" auf — die Kandidaten waren
schlicht noch nicht reif. Die Zahl „14 in Beobachtung" hatte drei Wochen lang
wie ein Blocker ausgesehen. Ein Fund, der sich beim Datieren in Luft auflöst,
ist ein Hinweis darauf, dass die **Datierung** fehlt, nicht der Deckel.

**Bewusst NICHT in diesem Plan:**

- **H-4 (Akkumulation)** — Schritt 6 entscheidet, ob `antizyklisch` und
  `tranchen_erlaubt` überhaupt für die anderen Klassen gelten sollen. Diese
  Entscheidung ist H-4s Voraussetzung, nicht sein Nachgang.
- **S-1 (Verdrängung)** — braucht G-4, und G-4 ist eine inhaltliche
  Entscheidung über „was macht eine These schwach". Schritt 2 (Richtgröße je
  Gruppe) löst das Problem ohne diese Entscheidung.
- **G-1 (Kandidat → Watchlist)** und **G-3 (Regime gegen Themenfeld)** — beide
  sind Konzeptfragen, keine Bauaufgaben. Sie gehören benannt und entschieden,
  bevor jemand sie implementiert.
- **P-2/P-3** (RM-3, Risikoparameter je Klasse) — reine Zahlenentscheidungen,
  die der Nutzer treffen muss.


**Nachtrag 09.08. — Schritt 7 aufgeloest: drei von vier waren längst entschieden.**
Die Recherche vor dem Bau ergab, dass „vier offene Rollout-Entscheidungen" den
Stand überzeichnete. Nur eine war offen.

| Fakt | Befund | Ergebnis |
|---|---|---|
| **`antizyklisch`** | Datenquelle ist `KRAKEN_FUTURES_SYMBOL_MAP` — Funding-Rate, Open Interest, Long-Konten-Anteil. Der Aktien-Analyst dokumentiert den Ausschluss bereits wörtlich: *„keine Optionen-/Futures-Positionierungsdaten für Einzelaktien verfügbar"* | **KEIN Rollout** — mangels Daten nicht möglich, war nie offen |
| **`liquiditaetszonen`** | Scope-Entscheidung vom 23.07.: *„Krypto Spot + Hebel only — nicht Aktien/Rohstoffe/Hedge/Themen-ETF (24/7-Markt + hoher Retail-/Hebel-Anteil = klassische Marketmaker-Dynamik-Annahme)."* Dazu Stufe 2 per Backtest verworfen (130 Ereignisse, p = 0,53) | **KEIN Rollout** — die Prämisse gilt für die anderen Klassen nicht |
| **`signal_stabilitaet`** | Technisch ausrollbar, misst Konfidenz-Streuung über die letzten N Bewertungen. **Aber:** Krypto läuft alle 15 Minuten, Multi-Asset 2×/Tag. Derselbe Parameter `anzahl_zyklen: 5` bedeutet einmal 75 Minuten, einmal 2,5 Tage | **ZURÜCKGESTELLT** — baubar, aber nicht mit demselben Parameter; der Fakt müsste die Zeitspanne nennen statt der Zyklenzahl. Bei Aktien 4 Schatten-Trades und ETF 0 liefert er ohnehin `None`. Niedrige Priorität |
| **`tranchen_erlaubt`** | Nur im Krypto-Spot; der Aktien-Analyst vermerkt *„AZ-4-Tranchen (Phase 1 bewusst minimal gehalten)"* — aufgeschoben, nicht ausgeschlossen | **GEBAUT 09.08.** für alle vier Klassen, siehe unten |

**`tranchen_erlaubt` — die ganze Kette, zehn Stationen.** Nutzer-Vorgabe: *„bitte
die Funktion von vorne bis hinten umsetzen, sonst hängt wieder eine unfertige
Funktionalität im System."* Umgesetzt: Vorgabewert für die 13 gehaltenen
Symbole, Schalter in der Oberfläche für **jedes** Watchlist-Asset (er war auf
`("BTC","ETH","SOL")` verdrahtet — die Flagge hätte für alle anderen nie gesetzt
werden können), Herkunftsbedingung, Prompt-Regel, JSON-Vorlage, Fakt,
Validierung, Persistenz, E-Mail (bereits geteilt) und das abgeleitete Schema.

**Kein BTC als Basis** (Nutzer-Vorgabe): die Bedingung nutzt
`equities_baermarkt_aktiv` und `vix_label`, beide stehen im Regime-Block dieser
Klassen ohnehin. Nutzer-Einordnung: *„bei Multiassets haben wir noch nicht alles
beisammen, aber die Indexwerte sind nicht falsch"* — als Revisit-Bedingung zu M6
im Docstring vermerkt.

**Die Validierung steht jetzt zentral** (`agent/tranchen.py`) statt viermal
kopiert; Krypto-Spot wurde verhaltensneutral mit umgestellt.

**Zur Erwartung:** die Bedingung feuert nach dem Deploy zunächst *nicht* — der
VIX stand am 08.08. bei 14,9 („ruhig"). Das ist beabsichtigt.

## Quellen (extern)

- [Bitpanda Gebühren — Aktien/ETF 1 € pro Transaktion + Spread, Edelmetall-Aufschläge, Handelsblatt](https://www.handelsblatt.com/erfahrungen/bitpanda-gebuehren/)
- [Bitpanda Gebühren nach Anlageklasse — Krypto 0,00–2,49 %, Fusion 0,02–0,25 %, Finanzfuchs](https://finanzfuchs.de/bitpanda-gebuehren/)

- [System Quality Number — Formel und Bewertungsskala, QuantMonitor](https://quantmonitor.net/system-quality-number-sqn/)
- [SQN und Mindest-Stichprobengröße, JournalPlus](https://journalplus.co/metrics/system-quality-number/)
- [Crypto CFD vs. Spot — Gebühren und Eigentum, Volity](https://volity.io/crypto/crypto-cfd-vs-crypto-spot/)
- [Versteckte Kosten von Krypto-Hebel, YieldFund](https://yieldfund.com/leverage-trading-in-crypto-what-are-the-hidden-costs/)

---

## 8c. Offene Punkte — Stand 16.08.2026 (LLM-Ebene)

**Abschnitt 8 und 8b bleiben stehen.** Sie tragen die Begründungen; hier steht,
was von der LLM-Ebene nach dem Umbau vom 15.–17.08. offen ist. Diese Liste ist
**die** Liste — Umbauplan Kapitel 40 und 42.5 verweisen hierher, statt sie zu
verdoppeln.

### Vor dem nächsten Produktivgang

| # | offen | Klasse | wo |
|---|---|---|---|
| L-1 | **Rolle G erreicht ihre Mindestgrundlage nicht** — eine Quelle statt zwei (R-R3, G1) | dokumentiert, nicht behoben | Regelwerksmanual R-R3 |
| L-2 | **Rolle G ist krypto-only** — 12 von 56 Assets ohne jede Gegenprüfung | offen | Umbauplan 40.1 |
| L-3 | **Auslöser fehlt bei Rolle BC** (CSTI-T) — der Anlass ist die Uhr | offen, **nicht** als Prompt-Parameter lösbar | Umbauplan 42.5 |

### Rolle G je Assetklasse — Quellen sind gebaut, nicht verdrahtet

| Klasse | Quelle 1 | Quelle 2 | Hindernis |
|---|---|---|---|
| Rohstoffe | CFTC COT (4 Symbole gemappt) | EIA | **COT wird nicht persistiert** — Live-Abruf je Signal wäre eine neue Abhängigkeit im 34-s-Fenster |
| Aktien | FINRA Short Interest | SEC Form 4 | Historie je Symbol für Perzentile ungeprüft |
| ETF / Absicherung | COT auf Index-Futures | Nachrichten | **Marktnamen unverifiziert** |
| Krypto | Binance OI/Funding/Long ✓ | fehlt — zweite Terminbörse | Deribit ist global, nicht symbolspezifisch |

### Rolle BC — Lücken je Korb

| Korb | fehlt | Klasse |
|---|---|---|
| Krypto Hebel | Kostenhöhe · Haltedauer | **rot / gelb** |
| Aktien | **Termine · Fundamentaldaten** · Handelszeiten | grün/gelb — Daten in `api/yfinance_client.py`, **keiner Rolle zugeordnet** |
| Rohstoffe | Volumen · Zertifikatsnatur · Basiswert · Emittent | eigener Rechercheschritt |
| Themen-ETF | TER · Spread | gelb |
| alle | Handelbarkeit und Spread | **gelb** — der nächste Verwandte hat ERÖFFNEN von 93 auf 3 % gedrückt |

### Rolle A

> ⚠️ **KORREKTUR 16.08.2026 (abends).** Rolle A galt als die am besten aufgestellte Rolle. Am NB-Backup gemessen bekommt sie in der PRODUKTION **12 statt 15 Aussagen** - es fehlen Netto-Liquiditaet, Zinskurve und Anlegerstimmung, also die gesamte Makro-Dimension und die Stimmung.
>
> **Ursache:** die Nachladelaeufe vom 12.08. sind nie auf dem Notebook gelaufen (`macro_snapshot` 36 statt 3.384 Zeilen, zwei Spalten fehlen ganz). **Der Nutzer muss `lade_makro_historie_nach.py` und `lade_fear_greed_nach.py` auf dem NB ausfuehren.** Das Lagebild meldet den Ausfall seit heute.
>
> **Und ein Fund in die andere Richtung:** `makro_historie_monat` traegt 1.185 Monate ab 1927 (Rendite 10J, CPI, WTI, Fed Funds, S&P-Trendabweichung in Standardabweichungen) - aktuell bis 2026-08 und von keinem Prompt gelesen. Umbauplan Kapitel 53.


| # | offen | Klasse |
|---|---|---|
| A-5 | Stimmung über BTC hinaus — **VIX liegt vor, aber nur ein Wert in der Historie** | grün, blockiert durch Datenlage |
| A-6 | Makro-Terminkalender (FOMC, CPI) | grün, **keine Quelle** |

### ~~VERWORFEN~~ GEBAUT 16.08.2026 - der Anlassfilter

> ⚠️ **Die Verwerfung galt einen halben Tag.** Der Nutzer hat den Fehlschluss darin benannt: „Schaden“ setzt voraus, dass die entfallenden Einstiege einen Wert haben - und im selben Absatz stand, dass sie keinen haben. Das tragende Argument ist ein KORREKTHEITSargument, kein Renditeargument. **Gebaut, siehe Umbauplan Kapitel 48.** Der Absatz unten bleibt als Begruendungsquelle stehen.

#### Was gegen sie sprach (Stand mittags)

**O-36 wird nicht scharf geschaltet, weder als Sperre noch als Mailfilter.** Gemessen: er haette **zehn von 21 Symbolen** ihre einzige Einstiegsgelegenheit genommen (SOL, SUI, TURBO, CAT ...), 82 von 121 Einstiegen stammen aus Wiederholungen.

**Und er haette die Qualitaet nicht geaendert** - ein Einstieg aus einem Zufall ist genauso viel wert wie einer aus der Erstfrage, naemlich brutto null (Grundbefund: kein Verfahren schlaegt die Basisrate). Nutzerfrage, die es beendet hat: *„ist das Ziel, das Rauschen zu messen?“*

Die MESSUNG laeuft weiter - sie kostet nichts. Umbauplan Kapitel 47.

### Erst nach der ersten Blockmessung

| # | | warum |
|---|---|---|
| K-2 | `struktur` ↔ `marken` zusammenlegen | beide lesen dieselben Swing-Punkte, sagen aber Verschiedenes. Ob sie sich gegenseitig ersetzen, entscheidet `messe_begruendungen.py` — nicht eine Vermutung |

### Dokumentation

| # | offen |
|---|---|
| D-1 | **Die drei `.docx`-Pendants sind vom 02.08.** — `Fakten_Entscheidungsmappe`, `Regelwerksmanual`, `Test_und_Verifikationsmethodik` liegen als `.md` auf dem 17.08. Zwei Wochen Rückstand, nicht heute entstanden |
| D-2 | `Regler_Signal_Pipeline_Abhaengigkeiten.md` **kennt die Rollen-Kette nicht** — kein Treffer für `lagebeschreibung`, `rollen_eingabe`, Rolle A/BC. Die Regel „vor jeder Prompt-Änderung prüfen" läuft dort ins Leere |
