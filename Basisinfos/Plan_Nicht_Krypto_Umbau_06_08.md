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


---

# Zwischenbilanz (06.08., nach Phase A)

## 1. Was gebaut und belegt ist

| Baustein | Zustand | Beleg |
|---|---|---|
| `agent/rekonstruktion.py` | fertig | 6 Testgruppen, 0 Fehler; Drag-Fall: Index −1,99 %, naiv +5,97 %, verkettet **−17,19 %** |
| Rohstoff-Reihen getrennt | verdrahtet | Futures unter `_ROHSTOFF_FUTURES_<SYM>`, ETC rekonstruiert, TA liest den Future |
| 3QSS/DBPK rekonstruiert | verdrahtet | aus `^NDX`/`^GSPC`, 3× bzw. 2× invers, täglich neu verankert |
| `quelle`-Spalte | fertig | additive, idempotente Migration; Standard `gemessen` |
| Datenmigration der Altzeilen | fertig | hängt falsch abgelegte Futures-Historie um, ohne Datenverlust |
| Plausibilitätsfilter Bewertung | fertig | verwirft eine laufende Reihe, die um Faktor > 3 vom Snapshot abweicht |
| Tests | 30 Prüfungen, alle bestanden | zwei Suiten gegen temporäre DBs, plus Regressionslauf auf einer DB-Kopie |

**Abnahme A2 Punkt 3 erfüllt:** Ankertagsabweichung exakt 0 — an echten Daten
gemessen (^NDX, 520 Punkte).

## 2. Der eigentliche Fund — größer als der Anlass

Beim Verifizieren, nicht beim Suchen: **OD7H trug 4.215,90 USD statt 18,22 EUR.**
Das ist der Gold-Future je Feinunze, abgelegt unter dem ETC-Symbol.

| Symbol | Wert laut Reihe | echter Wert | Differenz |
|---|---:|---:|---:|
| OD7H | 51.059 € | 255 € | **−50.803 €** |
| OD7N | 670 € | 551 € | −120 € |
| OD7C | 30 € | 156 € | +126 € |
| OD7L | 100 € | 169 € | +69 € |
| 3QSS | 0 € | 315 € | +315 € |
| DBPK | 0 € | 230 € | +230 € |
| **Summe** | **51.859 €** | **1.676 €** | **−50.182 €** |

Zum Vergleich: der gemeldete Portfoliowert beträgt **6.180 €**.

### Warum das bisher nicht aufgefallen ist — und warum genau das gefährlich war

Der Scheinwert lief **nicht** in die Bewertung ein, weil ein *zweiter* Defekt ihn
zufällig abfing: die FX-Ableitung wurde an praktisch jedem Tag verworfen, und
ohne Wechselkurs fällt jedes USD-Symbol aus der Bewertung. Am Export vom 06.08.
nachgerechnet:

| Streuungsmaß | angenommene Tage |
|---|---|
| Spannweite max−min (alt) | **4 von 91** |
| Interquartilsabstand (neu) | **91 von 91** |
| Spannweite ohne CAT | 18 von 91 |

Die letzte Zeile korrigiert eine frühere Vermutung: CAT war der schlimmste
Ausreißer, aber **nicht** die Ursache — das Streuungsmaß selbst war es.

**Daraus folgt die wichtigste Erkenntnis des Tages:** der FX-Fix allein wäre
schädlich gewesen. Er holt die USD-Symbole zurück in die Bewertung — und hätte
damit 51.000 € Scheinvermögen in ein 6.180-€-Portfolio geholt. Z-3, jede
Allokationsquote und jede Prozentregel wären unbrauchbar geworden.

Deshalb sind **drei** Dinge im selben Auslieferungsstand, und sie gehören
zusammen:

1. FX-Ableitung robust (IQR statt Spannweite)
2. Datenmigration der falsch abgelegten Zeilen — **beim Start**, nicht erst beim
   nächsten Pipeline-Lauf, damit die Reihenfolge der Jobs nicht darüber entscheidet
3. Plausibilitätsfilter als dauerhaftes Netz für den nächsten Fall dieser Art

> **Lehre, allgemein:** zwei Defekte, die sich gegenseitig verdecken, sehen im
> Betrieb wie „nur ein Defekt" aus. Wer einen davon behebt, verschlimmert die
> Lage. Vor jedem Einzelfix gehört deshalb die Frage: *was hat diesen Fehler
> bisher unsichtbar gehalten, und was passiert, wenn ich dieses Etwas entferne?*

## 3. Was noch offen ist — vollständig, ohne Lücken

### Sofort, nach dem Pull auf dem Notebook (Abnahme B)

| # | Prüfung | Erwartung |
|---|---|---|
| B3 | Z-3 vor/nach | Portfoliowert steigt um ~1.700 €, Rückschlag **sinkt**; Absicherung dämpft |
| B4 | „Symbole ohne Kurs" | von 19 auf ≤ 4; die USD-Symbole kommen über FX zurück |
| B2 | Rohstoff-Systemgüte | der +20,5-R-Ausreißer verschwindet → Klasse hat **0** ausgewertete Trades |
| B5 | Krypto-Regression | Systemgüte spot/hebel unverändert |
| — | Migrationslog | vier `Migration:`-Zeilen beim ersten Start, danach nie wieder |

**B2 ist kein Rückschritt, sondern die Korrektur einer Falschmeldung.** Die
Assetklasse Rohstoffe hat ab jetzt ehrlich null Evidenz statt einer erfundenen.

### Reihenfolge für die übrigen Klassen

Die Klassen unterscheiden sich **nicht** in dem, was ihnen fehlt, sondern nur
darin, wie weit sie in derselben Kette stehen. Deshalb dieselbe Kette für alle,
und zwar in dieser Reihenfolge — jede Stufe setzt die vorige voraus:

```
Kursdaten korrekt  →  Bewertung korrekt  →  Outcome messbar  →  Regime/Regeln  →  Universum
```

| Klasse | Kursdaten | Bewertung | Outcome | nächster Schritt |
|---|---|---|---|---|
| Rohstoffe | ✔ heute | ✔ heute | ab jetzt | B2 abwarten, dann zählen |
| Hedge | ✔ heute (rekonstruiert) | ✔ heute | ab jetzt | eigene Erfolgsdefinition (s. u.) |
| Aktien | ✔ vorhanden | ✔ über FX zurück | 4 Schattenfälle | **Universum** (Nutzer) |
| Themen-ETF | ✔ vorhanden | ✔ über FX zurück | 0 Auflösungen | Auflösungen abwarten |

**Die Lücke, die man dabei übersieht:** Aktien und Themen-ETF hatten nie einen
Datendefekt — sie fielen über *denselben* FX-Bruch aus der Bewertung wie die
Rohstoffe. Deren Bewertung ist damit heute mitrepariert, ohne dass an ihnen
etwas geändert wurde. Wer nur auf „welche Klasse war kaputt" schaut, verpasst
das.

### Was Hedge zusätzlich braucht — und in keiner der anderen Klassen vorkommt

Ein Absicherungs-Instrument mit Gewinn zu bewerten ist **falsch herum**. Ein
Hedge, der Geld verliert, während das Portfolio steigt, hat funktioniert. Solange
Hedge-Signale nach derselben Systemgüte gemessen werden wie Long-Signale,
produziert die Messung ein garantiert negatives und garantiert bedeutungsloses
Ergebnis. Das ist **D-d** aus Phase D und gehört **vor** die erste
Hedge-Auswertung, nicht danach.

### Was ausdrücklich NICHT heute passiert und warum

| Punkt | Grund | Bedingung fürs Wiederaufgreifen |
|---|---|---|
| Universum erweitern | Nutzer-Entscheidung, kein Code | jederzeit |
| Screening Nicht-Krypto | ohne Universum sinnlos | nach C1 |
| Regime je Klasse (M6) | Basis wäre eine Klasse ohne saubere Evidenz | nach B und C |
| Rollkosten/Gebühren modellieren | die Reihen taugen für kurze Horizonte; für Monate gälte das nicht — dort steht dann diese Frage | wenn eine Auswertung > 4 Wochen Haltedauer betrifft |

## 3b. Drei Lücken, die erst beim Nachfragen auffielen (nachträglich gebaut)

| Lücke | Warum sie zählt | Behoben durch |
|---|---|---|
| Rohstoff-/ETF-/Hedge-Reihen wurden **nie täglich gezogen** — nur wenn die Pipeline lief (9 und 19 Uhr, Mo–Fr), während der Portfolio-Job täglich um 6:30 läuft | Die Bewertung hing daran, ob am Vortag ein Signal entstand; am Wochenende gar nicht. Mit der Rekonstruktion schlimmer, weil deren Anker täglich wandert | `_refresh_nicht_aktien_ohlc()` im bestehenden OHLC-Refresh-Job |
| Der **Export konnte die Behebung nicht belegen** — „19 Symbole ohne Kurs", aber nicht welche und warum | Ohne das wäre B3/B4 nach dem Pull nicht prüfbar | `bewertungs_diagnose` je Symbol + Währung/`quelle` in der OHLC-Sektion |
| **Z-3 fehlte auf der Übersichtsseite**, und die beiden Portfoliowerte standen nie nebeneinander | Die Seite rechnet aus Snapshot-Preisen, Z-3 aus der Kursreihe. Am 06.08. lagen sie über 100 % auseinander — unsichtbar | Neue Z-3-Karte **mit Gegenprobe** und Warnung ab 5 % Abweichung |

> Die Gegenprobe ist die billigste Dauerüberwachung, die aus dem Fund folgt:
> zwei unabhängige Wege zur selben Größe, nebeneinander gestellt. Kein neuer
> Datenbezug, keine Schwellenwert-Diskussion — nur die Weigerung, zwei Zahlen
> getrennt anzuzeigen, die dasselbe meinen.

## 3c. Hedge sauber abgrenzen — wo gleich, wo anders (06.08.)

**Hedge ist keine Assetklasse.** Die Watchlist kennt nur `aktien`, `rohstoffe`,
`krypto` und `etf`; DBPK und 3QSS stehen als `etf` darin und sind allein über
ihre Mitgliedschaft in `SYMBOL_ZU_HEBEL_FAKTOR` erkennbar. Diese Prüfung stand
an **sechs verstreuten Stellen** — und die siebte hat sie vergessen (der neue
OHLC-Refresh filterte auf eine Assetklasse „hedge", die es nicht gibt).

> Ein Begriff, der an sechs Stellen wiederholt wird, wird an der siebten falsch
> gemacht. Deshalb jetzt **ein** Prädikat: `ist_hedge_instrument()`.

Die Trennung, die dahinter steht:

| | Hedge wird behandelt … | warum |
|---|---|---|
| Kursreihe beschaffen und aktuell halten | **gleich** | Datenversorgung ist Datenversorgung |
| Portfoliobewertung, Tageswert, Z-3 | **gleich** | eine gehaltene Position ist eine gehaltene Position |
| Staleness, Plausibilitätsprüfung der Reihe | **gleich** | dieselben Fehlerarten |
| Signalerzeugung, Cooldown, Budget-Slot | **gleich** | derselbe Batch, derselbe Wettbewerb um Slots |
| **Erfolgsmaß** | **anders** | ein Hedge, der verliert während das Portfolio steigt, hat funktioniert |
| **Richtungsdeutung** | **anders** | KAUFEN = Hedge aufbauen = bärische Erwartung → SHORT |
| **Positionsgröße** | **anders** | folgt dem Long-Exposure des Portfolios, nicht einer Kante im Instrument |
| **Technische Analyse** | **anders** | bewusst keine — bei jedem anderen Asset ist sie die Grundlage |
| **Regime** | **anders** | steigendes Aktienregime ist für ein inverses Produkt das *schlechte* Umfeld (offen, D-d) |

**Die obere Hälfte ist heute umgesetzt und im Betrieb bestätigt** (`hedge: 2` im
Refresh, 520 rekonstruierte 3QSS-Punkte). **Die untere Hälfte ist teilweise
offen:** Richtungsdeutung und Positionsgröße sind gebaut, das **Erfolgsmaß und
das Regime nicht** — und solange das Erfolgsmaß fehlt, darf keine
Hedge-Systemgüte als Ergebnis gelesen werden. Sie wäre garantiert negativ und
garantiert bedeutungslos.

## 4. Ehrliche Grenzen dieses Stands

- Die rekonstruierten Reihen tragen **keine** Rollkosten, Gebühren oder (bei
  3QSS) FX-Bewegung. Bei **Erdgas (OD7L)** ist der Rollverlust notorisch groß —
  dort ist die Reihe über Wochen zu optimistisch. Deshalb `quelle`, deshalb das
  520-Tage-Fenster, deshalb keine Monatsaussagen.
- **B3 und B4 sind heute nicht messbar.** Die Produktiv-Datenbank liegt auf dem
  Notebook; die Desktop-Kopie ist vom 21.07. und hat keine Nicht-Krypto-Reihen.
  Beide Prüfungen laufen nach dem Pull — die erwarteten Werte stehen oben und
  sind damit vorab falsifizierbar.
- Der Plausibilitätsfilter kann eine **echte** 3×-Bewegung eines kleinen Coins
  innerhalb eines Tages fälschlich verwerfen. Der Fehler geht dann in die sichere
  Richtung (Symbol gilt als „ohne Kurs", Warnung nennt es beim Namen) — aber er
  existiert und ist bewusst in Kauf genommen.
