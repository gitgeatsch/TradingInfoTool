# Plan: Nicht-Krypto-Assets auf stabile Beine (06.08.2026)

**Auftrag:** sauberer Plan für den Gesamtumbau der Nicht-Krypto-Assets, inklusive
Gegenprüfung und detailliertem Testing. Diese Klassen müssen ASAP stabil werden.

**Geltungsbereich:** Aktien, Rohstoffe, Themen-ETF, Hedge. Krypto-Spot und
Krypto-Hebel sind am 06.08. umgestellt und bleiben unberührt.

---

## 0. Die Ausgangslage in einer Tabelle

| Klasse | ausgewertete Trades | Symbole | Blockade |
|---|---|---|---|
| Aktien | 4 (nur Schatten), EW −1,000 | 2 | zu kleines Universum |
| **Rohstoffe** | **1** real, **+20,5 R** | 4 | **Instrumenten-Verwechslung** |
| Themen-ETF | 0 | 7 | keine Auflösungen |
| **Hedge** | 0 (bei 32 Signalen) | 2 | **keine Kursdaten, obwohl gehalten** |

**Zwei davon sind keine Datenknappheit, sondern Defekte** — und beide erzeugen
falsche Zahlen, statt gar keine. Das ist der gefährlichere Zustand.

---

## 1. Die zwei Defekte, präzise

### D1 — Rohstoffe: Zonen und Bewertungsreihe sind verschiedene Instrumente

`agent/rohstoff/pipeline.py::_ensure_ohlc_backfilled()` holt die OHLC-Historie
über den **liquiden Futures-Ticker** und legt sie **unter dem ETC-Symbol** ab:

```python
SYMBOL_ZU_FUTURES_TICKER = {"OD7N": "SI=F", "OD7H": "GC=F",
                            "OD7C": "HG=F", "OD7L": "NG=F"}
ohlc_points = get_full_ohlc_history(futures_ticker, asset.symbol, "USD")
```

**Die Absicht war richtig** (der Future hat die saubere, liquide Historie für die
technische Analyse), **die Ablage ist es nicht**: alles Nachgelagerte hält die
Reihe für den ETC.

| Symbol | Instrument | Signal-Entry | OHLC-Reihe | Faktor |
|---|---|---|---|---|
| OD7C | WisdomTree Copper (ETC) | 34,63 | 6,31 (HG=F, USD/lb) | 5,49 |
| OD7L | WisdomTree Natural Gas | 4,62 | 3,02 (NG=F) | 1,53 |
| OD7N | (Silber) | 46,00 | 62,02 (SI=F) | 0,74 |

Kein gemeinsamer Faktor — verschiedene Einheiten (lb, MMBtu, Feinunze). Der
+20,5-R-Trade entsteht daraus: `(34,63 − 6,30) / 1,37 = 20,68`.

**Der eigene Code zeigt die Lösung:** `agent/themen_etf/pipeline.py` legt seinen
SPY-Benchmark unter einem **eigenen** Symbol ab (`_THEMEN_ETF_BENCHMARK_SPY`).
Genau dieses Muster fehlt bei den Rohstoffen.

### D2 — Hedge: gehalten, aber ohne Kursdaten

**DBPK** (2× short S&P 500, 1.739 Einheiten) und **3QSS** (3× short Nasdaq-100,
218 Einheiten) sind **im Bestand**, haben aber **null Kurspunkte** und keinen
Einstandspreis. Sie stehen im Mengenkorb der Portfolio-Wertreihe und fallen
mangels Kurs aus der Bewertung.

> **Folge: Z-3 misst den Drawdown ohne die Absicherung, die ihn dämpfen soll.**

**Die Ursache ist bekannt und im Code dokumentiert** (`agent/hedge/pipeline.py`,
Modul-Docstring): diese Instrumente liefern über yfinance **keine
`.history()`-Daten, nur `fast_info`**. Es ist ein Datenquellen-Problem, kein Bug.

---

## 2. Der Plan — vier Phasen, jede mit eigener Abnahme

### Phase A — Defekte beheben (heute)

#### A1: Rohstoff-Reihen trennen

**Umbau:** die Futures-Historie kommt unter ein eigenes Symbol
(`_ROHSTOFF_FUTURES_<SYM>`), das ETC behält seine eigene Reihe über
`asset.yfinance_symbol`.

**Die Designentscheidung, die dabei zu treffen ist:**

| Zweck | Reihe | Begründung |
|---|---|---|
| Technische Analyse (EMA, RSI, ATR) | **Futures** | liquide, lückenlos — die ursprüngliche, richtige Absicht |
| Zonen und Bewertung | **ETC** | das ist, was tatsächlich gehandelt wird |

**Risiko, das benannt gehört:** die ETC-Reihe kann dünn oder lückenhaft sein —
genau deshalb wurde ursprünglich der Future genommen. Falls sie unbrauchbar
ist, lautet die ehrliche Konsequenz **nicht** „dann eben weiter mischen",
sondern: Rohstoffe bekommen **keine Outcome-Bewertung**, bis eine Reihe
vorliegt. Die Plausibilitätsschranke vom 06.08. verhindert bereits, dass daraus
Kennzahlen entstehen.

**Abnahme A1:**
1. Für jedes der vier Symbole: Verhältnis Signal-Entry zu OHLC-Median **< 1,3**
2. Die Futures-Reihe ist unter dem neuen Symbol vorhanden und unverändert lang
3. Der +20,5-R-Trade wird bei Neuauswertung **nicht mehr** produziert
4. Die technische Analyse liefert weiterhin Werte (kein `None`-Einbruch)
5. Gegenprobe: Aktien und Themen-ETF bleiben unverändert (Faktor ~1,0)

#### A2: Hedge-Kursreihe rekonstruieren

**Vorgehen:** tägliche Rendite eines Daily-Reset-Hebelprodukts ist
definitionsgemäß `−L × Indexrendite`. Beide Bestandteile liegen vor:

```python
SYMBOL_ZU_HEBEL_FAKTOR   = {"DBPK": 2.0, "3QSS": 3.0}
SYMBOL_ZU_REFERENZ_INDEX = {"DBPK": "S&P 500", "3QSS": "Nasdaq-100"}
```

Die Indexreihen sind über yfinance beschaffbar (`^GSPC`, `^NDX`), und der
SPY-Benchmark läuft bereits im Themen-ETF-Pfad.

**Zwingend als Näherung kennzeichnen.** Das Projekt hat dafür ein etabliertes
Muster (`kosten_belegt=False`, `naeherung_konstante_menge`). Eine rekonstruierte
Reihe darf nie wie eine gemessene aussehen.

**Bekannte Abweichung, die dazugehört:** Daily-Reset-Produkte haben
**Volatilitäts-Drag** — über mehrere Tage ist die Rendite *nicht* `−L ×`
Gesamtrendite, sondern systematisch schlechter. Die Rekonstruktion muss deshalb
**täglich verketten**, nicht über den Zeitraum hochrechnen. Wer das verwechselt,
baut einen Fehler ein, der bei ruhigen Märkten klein und bei bewegten groß ist.

**Abnahme A2:**
1. Rekonstruierte Reihe deckt dieselben Tage ab wie die Indexreihe
2. Verkettung ist täglich — Prüfung an einem konstruierten Fall mit bekanntem
   Drag (Index +10 %/−10 % im Wechsel muss bei 3× short **verlieren**, nicht
   gewinnen)
3. Der zuletzt bekannte `fast_info`-Preis wird als Ankerpunkt genutzt und die
   Reihe rückwärts skaliert — Abweichung am Ankertag exakt null
4. Als `quelle="rekonstruiert"` markiert, in Export und Anzeige sichtbar
5. **Z-3 neu gerechnet:** wie ändert sich der Rückschlag, wenn die Absicherung
   endlich mitzählt? Das ist der eigentliche Zweck.

### Phase B — Verifikation, dass die Behebung wirkt (heute, nach A)

Nicht „läuft durch", sondern belegt:

| # | Prüfung | Bestanden, wenn |
|---|---|---|
| B1 | Vollcheck-Skript erweitert um Skalen-Prüfung je Assetklasse | alle Faktoren < 1,3 |
| B2 | Rohstoff-Systemgüte neu | der +20,5-R-Ausreißer ist weg |
| B3 | Z-3 mit und ohne Hedge nebeneinander | beide Werte ausgewiesen, Differenz erklärt |
| B4 | Portfolio-Wertreihe: „Symbole ohne Kurs" | von 19 auf **≤ 5** gefallen |
| B5 | Keine Regression bei Krypto | Systemgüte hebel/krypto unverändert |

### Phase C — Abdeckung (nach B, mehrere Tage)

**C1 Universum.** Zwei Aktien und vier Rohstoffe sind keine Auswahl. Ohne mehr
Symbole entsteht nie eine auswertbare Stichprobe. **Das ist eine
Nutzer-Entscheidung** — es ist die Watchlist, nicht der Code.

**C2 Screening für Nicht-Krypto.** Es gibt keines; die Watchlist ist die einzige
Quelle. Erst sinnvoll, wenn C1 entschieden ist.

**C3 Messung erst ab genug Fällen.** Externer Standard: 30 als Untergrenze,
100+ für Belastbarkeit. Bis dahin gilt jede Aussage über diese Klassen als
Richtungsbefund, nicht als Ergebnis.

### Phase D — Regime-Konzept je Klasse (nach C)

Das ist **M6** aus dem Zwischenstand. Vier Teilfragen:

| # | Frage | Stand |
|---|---|---|
| D-a | Welche Referenz statt BTC? | S&P 500 und VIX liegen bereits vor und stecken schon im Regime-Block dieser Klassen |
| D-b | Ein Score je Klasse oder je Familie? | offen |
| D-c | Pendant zum Divergenz-Fakt? | denkbar (Abstand zur eigenen EMA50), ungemessen |
| D-d | **Hedge braucht UMGEKEHRTE Wirkrichtung** | inverse Produkte: steigendes Aktienregime ist das schlechte Umfeld |

**Nicht vorziehen.** Ein Regime-Konzept für eine Klasse zu bauen, deren einzige
Evidenz ein Datenfehler ist, wäre die falsche Reihenfolge.

---

## 3. Gegenprüfung — was an diesem Plan schiefgehen kann

Ehrlich vorweg, damit es nicht hinterher auffällt:

| Risiko | Gegenmittel |
|---|---|
| **Die ETC-Reihen sind zu dünn** und A1 löst das Problem nicht, sondern tauscht es gegen fehlende Daten | Vorher prüfen, nicht hinterher. Erste Handlung in A1 ist ein Abruf-Test je Symbol — erst danach wird umgebaut. |
| **Die Hedge-Rekonstruktion driftet** von den echten Kursen weg (Gebühren, Tracking-Differenz, Swap-Kosten) | Als Näherung kennzeichnen, Abweichung am Ankertag messen, und bei jedem neuen `fast_info`-Preis neu verankern statt frei laufen zu lassen |
| **Z-3 ändert sich sprunghaft**, sobald die Absicherung mitzählt — und löst eventuell nicht mehr aus | Genau das ist der Zweck. Beide Werte nebeneinander ausweisen und die Differenz begründen, statt still zu ersetzen |
| **Ich baue etwas, das Krypto beschädigt** | B5 als harte Abnahme; `risk_gate` und `backward_tracking` sind geteilt, jede Änderung dort ist klassenübergreifend |
| **Der Plan erzeugt Zahlen, bevor sie belastbar sind** | C3: unter 30 Fällen kein Ergebnis, nur Richtungsbefund |

**Was dieser Plan ausdrücklich NICHT verspricht:** bessere Signale. Er stellt
Datenkorrektheit her. Ob die Nicht-Krypto-Klassen eine Kante haben, ist danach
erst *messbar* — heute ist es das nicht.

---

## 4. Reihenfolge und Aufwand

| | heute | Voraussetzung |
|---|---|---|
| **A1** Rohstoff-Reihen trennen | ja | Abruf-Test der ETC-Reihen |
| **A2** Hedge rekonstruieren | ja | Indexreihen ^GSPC/^NDX |
| **B1–B5** Verifikation | ja, direkt nach A | A abgeschlossen |
| C1 Universum | Nutzer-Entscheidung | — |
| C2 Screening | nein | C1 |
| C3 Messung | nein | Zeit |
| D Regime je Klasse | nein | B und C |

**Heute machbar und sinnvoll: A1, A2 und die vollständige Abnahme B.** Das ist
der Teil, der die Klassen von „erzeugt falsche Zahlen" auf „erzeugt korrekte
oder gar keine" bringt — und genau das ist mit „stabile Beine" gemeint.
