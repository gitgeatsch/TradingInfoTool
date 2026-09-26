# Vorabfestlegung 21 — hält die Bewertung eine gröbere Auflösung?

**26.09.2026**, vor der Messung · `messe_aufloesung_und_fallback.py` ·
Frageart **`markt`** (Messuniversum, nach `messnorm.FRAGEARTEN`)

> **Nutzerauftrag:** *„ja messen - prüfen und gegenprüfen - wir benötigen
> auch eine fallback lösung wenn eine Bewertung nicht oder nur zum Teil
> gedeckt ist."*

---

## Die Frage

Die Bewertung aus 2.608 (`ema_abstand_atr` ≥ Schwelle, Trailing) ist auf
**stündlichen OHLC-Daten von Binance** gemessen. Für 15 von 43
Watchlist-Symbolen gibt es die nicht — CoinGecko liefert stattdessen eine
**stündliche Preisreihe** und **4-Stunden-OHLC** (2.613).

> **Bleibt die Bewertung gültig, wenn die ATR aus gröberen Kerzen kommt —
> und was kostet jede Fallback-Stufe?**

## ⚠️⚠️ Zwei Fallen, die die Konstruktion bestimmen

### Falle 1 — `R` ist in Einheiten des Anfangsrisikos, also **in ATR**

Genau der Fehler aus 2.607: `R = (Ausstieg − Einstieg) / (Weite × ATR)`.
Ändert sich die ATR, ändert sich der **Nenner** — und `E[R]` wäre nicht
mehr vergleichbar, sondern nur **anders skaliert**.

➤ **Gemessen wird deshalb BEIDES und beides wird ausgewiesen:**

| Maßstab | wofür |
|---|---|
| **`E[R]`** in Anfangsrisiken | die **Hebel**frage (wie viel Risiko je Einsatz) |
| **Ertrag in Kursprozent** | die **Vergleichs**frage — der einzige Maßstab, der von der ATR unabhängig ist |

⚠️ **Nur der Kursprozent-Arm entscheidet die Vergleichsfrage.** Ein
gleiches `E[R]` bei verschiedener ATR wäre kein Beleg für Gleichheit.

### Falle 2 — die ATR geht an **zwei** Stellen ein

| Stelle | Wirkung |
|---|---|
| **Nenner des Merkmals** `(close − EMA) / (ATR × close)` | wer wird ausgewählt |
| **Stopweite des Trailings** `Weite × ATR` | wie wird geführt |

➤ Beide werden **gemeinsam** umgestellt (so wäre es im Betrieb), und
zusätzlich **einzeln**, um zu sehen, welche der beiden den Unterschied
trägt.

## Die Konstruktion

### Gepaart, auf identischer Ankermenge

Die 4-Stunden-Kerzen werden aus den **vorhandenen 1-Stunden-Kerzen
aggregiert** (`high` = Max, `low` = Min, `close` = letzte). Damit ist der
Unterschied **rein die Auflösung** — keine zweite Datenquelle, kein
Quelleneffekt, keine andere Grundgesamtheit.

⚠️ Dass CoinGecko-4h-Kerzen mit aggregierten Binance-4h-Kerzen
übereinstimmen, ist damit **nicht** gezeigt. Das ist eine **eigene
Frage** und wird getrennt gestellt.

### Die Stufen, die verglichen werden

| Stufe | ATR-Quelle | entspricht |
|---|---|---|
| **A** | 1-h-OHLC | heute (Binance) |
| **B** | 4-h-OHLC, aggregiert | CoinGecko-OHLC |
| **C** | Tages-OHLC, aggregiert | die gröbste Fallback-Stufe |
| **D** | **stündliche Preisreihe ohne High/Low** — ATR ersetzt durch die Streuung der Stundenschlusskurse | CoinGecko `market_chart`, wenn gar kein OHLC da ist |

⭐ **Stufe D ist die eigentliche Fallback-Frage:** CoinGecko liefert die
Preisreihe für **15 von 15**, das OHLC nur grob. Trägt eine ATR-Ersatzgröße
ohne High/Low, wäre die Lücke vollständig schließbar.

## Die Gegenprüfungen — vor der Messung festgelegt

| # | Prüfung | Was sie ausschließt |
|---|---|---|
| **P1** | **Bitgleichheit im Grenzfall**: Aggregation mit Faktor **1** muss Stufe A **bitgleich** reproduzieren | ein Fehler im Aggregator selbst |
| **P2** | **Nullwelt je Stufe** (Zufallsauswahl gleicher Größe, 40 Ziehungen) | dass ein Ergebnis aus der Auswahlgröße stammt |
| **P3** | **Ankermenge identisch** über alle Stufen — ein Anker zählt nur, wenn er in **allen** gültig ist | verschiedene Grundgesamtheiten (die stehende Regel) |
| **P4** | **gepaarter Fehler**: die Differenz A−B je Tag, nicht zwei getrennte Bänder | überlappende Bänder, die nichts über den Unterschied sagen |
| **P5** | **Rangkorrelation** der Merkmalswerte zwischen den Stufen | dass „gleiches `E[R]`" aus einer **anderen** Auswahl mit zufällig gleichem Mittel entsteht |

## Was VOR der Messung als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| **Stufe B gleichwertig** (Differenz im Band, Rangkorrelation hoch) | CoinGecko-OHLC taugt → die Lücke ist über 4-h-Kerzen schließbar |
| **B schlechter, D brauchbar** | die Preisreihe ist der bessere Fallback als grobes OHLC |
| **beide schlechter** | die Bewertung braucht stündliches OHLC → andere Quelle nötig, oder die betroffenen Assets bekommen **keine** Bewertung |

⛔ **Ein „geht auch" wird nicht ausgerufen, weil die Differenz klein
aussieht.** Sie muss **im gepaarten Band** liegen (P4), und die
Rangkorrelation muss zeigen, dass **dieselben** Anker gewählt werden (P5).

## Was diese Messung NICHT beantwortet

| # | |
|---|---|
| **1** | Ob **CoinGecko**-4h-Kerzen den aggregierten Binance-4h-Kerzen entsprechen — eigene Frage, eigene Messung |
| **2** | Ob die **Preisreihe** von CoinGecko dieselben Schlusskurse trägt wie Binance |
| **3** | Gebühren, Ausführbarkeit, Hebelhöhe — unverändert offen (2.609) |
| **4** | Nichts über **Short** |
