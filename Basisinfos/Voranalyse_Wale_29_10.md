# Voranalyse Wale — welche Größe zeigt welches Verhalten (29.10.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 29.10.):** *„prüfe ob wir auch das ‚BTC-Wale‘-Verhalten abfragen und messen können für unser Vorhaben“* ·
Entscheid **A** (*„vorerst A“*) · Vorgabe dazu: *„wir müssen die Metriken auch korrekt ordnen, was zeigt uns wenn Wale kaufen
oder verkaufen, halten, etc.“* · Gesamtplan **G16**.

⚠️ **Die Prüffrage zuerst:** Jede Größe hier ist zunächst ein **FAKT** (was geschah). Zur **BEWERTUNG** (was kommt) wird sie erst
durch eine Messung. Die Spalte „Deutung“ ist deshalb eine **Hypothese** — sie wird **zweiseitig** gemessen, nicht vorausgesetzt.

## 1. Je Größe: was sie DIREKT zeigt — und was man daraus nur VERMUTET

Nachweis je ein Abruf am 29.10., **nichts heruntergeladen**.

| # | Größe | Quelle | zeigt direkt (Fakt) | Deutung (Hypothese) | Fallstrick | Vorgriff | Stand |
|---|---|---|---|---|---|---|---|
| W1 | **Großer Taker-Kauf** — Einzelgeschäft ≥ Schwelle, Käufer nimmt (`is_buyer_maker = false`) | Binance `aggTrades` Spot/Futures | jemand hat ein großes Stück **sofort** gekauft | Kaufdruck großer Teilnehmer | Wale **stückeln** (Algo/TWAP) — große Einzelgeschäfte sind nur der **sichtbare** Teil; auch Market Maker | ✔ sauber (Zeitstempel je Geschäft) | ✔ abrufbar |
| W2 | **Großer Taker-Verkauf** | dito | großes Stück sofort verkauft | Verkaufsdruck großer Teilnehmer | dito | ✔ | ✔ |
| W3 | **Netto-Großfluss** W1 − W2, als Anteil am Tagesumsatz | dito | Überhang der großen Aggressoren | Richtung der Großen | Schwelle muss **relativ** sein (Preis 2023 ≈ 17 k$, 2026 ≈ 80 k$) | ✔ | ✔ |
| W4 | **Passive Wal-Orders** (Limit-Wände im Orderbuch) | Orderbuch | wo Große warten | Unterstützung/Widerstand | Wände werden gestellt und zurückgezogen (Täuschung) | – | ✖ **keine freie Historie**, nur live |
| W5 | **Börsenabfluss netto** (Abfluss − Zufluss), **Börsenbestand** sinkt | CoinMetrics Community `FlowOutExNtv`, `FlowInExNtv`, `SplyExNtv` | BTC verlassen **als Börse gekennzeichnete** Adressen | **Halten / Ansammeln** (Eigenverwahrung) | interne Umbuchungen; ETF-Verwahrer; Adresszuordnung | ⚠️⚠️ **NEIN** — die ganze Reihe seit 2023 wurde **im April 2026 neu berechnet** (Rechenstand jedes Werts 10.–17.04.2026), ältere Jahrgänge gibt es nicht | nur **Fakt für die Mail** |
| W6 | **Börsenzufluss** | dito | BTC **auf** Börsen gebracht | Vorstufe zum **Verkauf / Verteilen** | auch Sicherheiten für Termingeschäfte | ⚠️⚠️ dito | nur Fakt |
| W7 | **ETF-Nettozuflüsse** | Farside (liegt vor: `data/_etf/`) | Anteile geschaffen/zurückgegeben | **Kauf/Verkauf** institutioneller Anleger | Veröffentlichung nach US-Schluss → `bekannt_ab` Folgetag | ✔ mit `bekannt_ab` | ✔ vorhanden |
| W8 | **Coinbase-Prämie** | Coinbase gegen Binance (G4, geladen) | US-Preis über/unter Welt | **Kaufdruck US-Institutioneller** | Wechselkurs USD/USDT | ✔ | ✔ geladen (`sichten.db`) |
| W9 | **Ruhende Coins** — Alter der bewegten Coins (Coin Days Destroyed), Langzeithalter-Bestand | nur **Blockchain-Rohdaten** | wie alt die bewegten Coins sind | **Halten** (alt ruht) gegen **Verteilen** (alt bewegt sich) | Umbuchungen von Verwahrern | ✔ aus Rohdaten | ✖ **CoinMetrics Community hat es nicht** (31 Größen geprüft); nur über **BigQuery = Option B** |
| W10 | **Zahl der Wal-Adressen** (≥ 1.000 BTC) | dito | wie viele große Bestände es gibt | Ansammeln/Verteilen | eine Börse = viele Adressen | ✔ aus Rohdaten | ✖ nur Option B (Blockchair: IP sofort gesperrt, Schlüssel kostet) |
| W11 | **Positionierung der großen Terminkonten** (Top-Trader Long/Short) | Binance-Metrikdateien | Long/Short der größten Konten bei Binance Futures | **Erwartung** der Großen — **kein Spot-Kauf** | | ✔ | ✔ **liegt vor und ist GEMESSEN**: `top_bias` trägt nicht (Befund **2.219**), ρ 0,955 zu `long_bias` |
| W12 | Open-Interest-Änderung | dito | Hebelaufbau gesamt | – (nicht wal-spezifisch) | | ✔ | ✔ trägt (2.219) |

## 2. Geordnet nach VERHALTEN

| Verhalten | saubere, messbare Größe | nur als Fakt | nicht abfragbar (frei) |
|---|---|---|---|
| **Kaufen** | W1, W3, W7, W8 | – | – |
| **Verkaufen** | W2, W3, W7 (Abflüsse) | W6 | – |
| **Halten / Ansammeln** | **keine** | W5 | W9, W10 (nur Option B) |
| **Verteilen** (alte Bestände geben ab) | **keine** | W6 | W9, W10 (nur Option B) |
| **Positionieren** (Hebel, Erwartung) | W11 (gemessen, trägt nicht) | – | W4 |

⚠️⚠️ **Die Lücke ist benannt:** für **Halten** und **Verteilen** gibt es **ohne Option B keine saubere Größe**. Wer W5/W6 als Messgröße
nimmt, misst mit dem Wissen von 2026 — das ist der Fall der **Kontamination**, nur bei Daten statt beim Modell.

## 3. Was daraus für die Messung folgt (Entwurf, wird mit G7 abgestimmt)

| | |
|---|---|
| **Zielgröße** | dieselbe wie bei allen Sichten (Messnorm, Tagesklammer) — kein eigener Maßstab für Wale |
| **Form** | Zeitreihe je Kernwert (BTC, ETH), nicht Querschnitt — ein Querschnittsbefund (wie 2.219) sagt nichts über die Zeitreihe |
| **Schwelle** | **relativ**: oberstes Perzentil der Geschäftsgröße je Tag bzw. je 30 Tage, nicht fester Dollarbetrag — Vorschlag aus der **Stichprobe**, nicht vorab gewählt |
| **Zweiseitig** | „Großkäufe → steigt“ **und** „Großkäufe → Gipfel (Verteilung an Späte)“ sind beide plausibel; der Messplan legt keine Richtung fest |
| **Selbsttest** | vor dem ersten Blick, 1.000 Ziehungen, Nullwelt mit **Ballung** (Großgeschäfte häufen sich an Bewegungstagen) |
| **Fallstrick 2023 Q1** | Binance Spot BTCUSDT war bis **22.03.2023 00:00 UTC gebührenfrei** (Binance-Ankündigung vom 15.03.2023, im V1-Archiv) — Umsatz und Geschäftszahl aufgebläht (Datei 01.03.2023: **106 MB**, 2026: 13 MB). Futures waren davon nicht betroffen → Spot **und** Futures laden, 2023 Q1 getrennt ausweisen |

## 4. Datenumfang (gemessen 29.10., HEAD je Datei)

| Datei | Größe |
|---|---|
| Spot BTCUSDT 01.03.2023 (gebührenfrei) | 106 MB |
| Spot BTCUSDT März 2025 (Monat) | 815 MB (~27 MB/Tag) |
| Spot BTCUSDT 27.10.2026 | 13 MB |
| Futures BTCUSDT 01.03.2024 | 19 MB |

**Schätzung 01/2023–10/2026:** Spot BTC **~35–40 GB**, Futures BTC **~25–30 GB**. Verarbeitet wird **im Strom**: jede Datei wird gelesen,
zu Tageswerten verdichtet (`data/_wale/`), die Rohdatei **nicht gespeichert** — es entsteht nichts, was später gelöscht werden muss.

## 5. Die nächste Entscheidung — Laden

| | |
|---|---|
| **a (Empfehlung)** | **Stichprobe zuerst:** Spot + Futures BTC je 3 Monate (01/2023 gebührenfrei, 03/2024, 03/2026), ~4 GB. Daran: Verteilung der Geschäftsgrößen, Schwellenvorschlag, Abgleich mit dem Kerzenumsatz (Archiv hat abgeschnittene Kerzen — hier gegenprüfen). Danach Abstimmung über den vollen Download |
| b | gleich voll: Spot + Futures BTC 2023–26 (~65 GB) |
| c | nur Futures BTC voll (~28 GB) — umgeht 2023 Q1, verliert aber den Spot-Kauf |

**Empfehlung a**, weil die Schwelle eine **Messung** ist und keine Wahl (stehende Regel) — und eine lange Messung erst nach der
Vorprüfung kommt.
