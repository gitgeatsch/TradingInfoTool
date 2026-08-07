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

## 8b.1 Der zentrale Blocker — alles andere hängt daran

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

## Quellen (extern)

- [System Quality Number — Formel und Bewertungsskala, QuantMonitor](https://quantmonitor.net/system-quality-number-sqn/)
- [SQN und Mindest-Stichprobengröße, JournalPlus](https://journalplus.co/metrics/system-quality-number/)
- [Crypto CFD vs. Spot — Gebühren und Eigentum, Volity](https://volity.io/crypto/crypto-cfd-vs-crypto-spot/)
- [Versteckte Kosten von Krypto-Hebel, YieldFund](https://yieldfund.com/leverage-trading-in-crypto-what-are-the-hidden-costs/)
