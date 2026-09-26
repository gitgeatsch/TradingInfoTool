# CoinGecko gegen Binance — die Quelle trägt, und BTC auch

**26.09.2026** · Befunde 2.618, 2.619 · `messe_coingecko_gegen_binance.py`

> **Nutzerauftrag:** *„dann CoinGecko gegen Binance messen"*

Grund: 2.616 hat die Fallback-Stufen an Kerzen gemessen, die aus den
**eigenen Binance-Stundenkursen aggregiert** waren. Der Unterschied war
dort rein die **Auflösung**. Ob CoinGecko dieselben Werte liefert, war
damit **nicht** gezeigt — Stufe 2 (67 %) und Stufe 3 (65 %) waren
**Annahmen**.

---

## Teil 1 — die Rohdaten: wie weit liegen die Quellen auseinander?

**27 Symbole mit beiden Quellen**, je rund 2.100 gemeinsame Stunden:

| | Median | Spanne |
|---|---|---|
| Schlusskurs-Abweichung | **0,3913 %** | 0,169–0,490 % |
| Korrelation | **0,9955** | 0,9901–0,9994 |
| High-Abweichung *(4-h-Kerze)* | 0,7201 % | 0,310–1,071 % |
| Low-Abweichung *(4-h-Kerze)* | 0,7272 % | 0,286–1,136 % |
| **ATR-Verhältnis** CG/BN | **0,9886** | 0,968–0,998 |

⚠️ **Ein Unterschied ist kein Fehler:** CoinGecko mittelt über Börsen,
Binance ist eine einzelne. Die Frage ist, ob er klein gegen den Effekt ist.

⚠️⚠️ **Und ein eigener Darstellungsfehler, im Probelauf gefunden:** Das
ATR-Verhältnis stand zuerst bei **0,46** — weil ich den Renditeschätzer
(CoinGecko) gegen den Spannenschätzer (Binance) gehalten hatte. Das
mischte den **Quellen**-Unterschied mit der bekannten **Methoden**-Differenz
(0,48× laut 2.616) und war nicht lesbar. Mit **demselben Schätzer auf
beiden Seiten**: **0,9886** — die Quelle allein macht rund **1 %** aus.

⚠️ Auch das Zeitformat war zunächst falsch (`%Y-%m-%dT%H` statt
`%Y-%m-%d %H:00`) — der Lauf meldete **null gemeinsame Stunden** und hätte
sonst leise nichts gemessen.

---

## ⭐⭐⭐ Teil 2 — die entscheidende Prüfung

Die Rohabweichung von 0,39 % beantwortet die **falsche** Frage. Sie ist ein
**Niveau**-Unterschied, während im Betrieb **aus CoinGecko bewertet** und
**auf Binance gehandelt** würde. Also genau so gemessen:

> **Bewertung aus CoinGecko gerechnet (Stufe D, nur Schlusskurse),
> Ertrag auf Binance gemessen.**

**46.461 Anker aus 27 Symbolen**, gemeinsames 90-Tage-Fenster:

| Anteil | Auswahl nach **Binance** | Auswahl nach **CoinGecko** | Verlust | Nullband | Überlappung |
|---|---|---|---|---|---|
| **1 %** | +2,7111 % | **+2,4416 %** | **−10 %** | +0,6273 | 53,9 % |
| **2 %** | +2,9350 % | **+2,5396 %** | **−13 %** | +0,6339 | 61,9 % |
| **5 %** | +3,0748 % | **+2,8353 %** | **−8 %** | +0,5756 | 75,4 % |

✔✔ **Alle drei tragen deutlich über dem Nullband.** Rangkorrelation
**0,9413** — die Ordnung bleibt weitgehend erhalten.

⛔⛔ **Zwei Einschränkungen, die dazugehören:**

| # | |
|---|---|
| **1** | **Nur 90 Tage** — das rollende CoinGecko-Fenster. Gegen die 1.746 Tage aus 2.616 ist das eine schmale Basis |
| **2** | Die Periode trägt **deutlich höhere Erträge** als der Fünfjahresschnitt (+2,7 % gegen +0,66 %). Der Verlust von 8–13 % ist deshalb **nicht** mit den 35 % aus 2.616 vergleichbar — andere Periode, andere Basis |

➤ **Belastbar ist:** die Ordnung bleibt erhalten (0,9413), und die
CoinGecko-Auswahl trägt gegen ihr eigenes Nullband. **Nicht belastbar:**
eine genaue Zahl für den Verlust.

---

## ⭐ Teil 3 — trägt die Bewertung auf BTC?

> **Nutzeranmerkung 26.09.:** *„btc muss beides erfüllen — der Wert muss
> handelbar sein, seine Eigenschaften dürfen ‚genutzt' werden. Das ist aber
> ein eigenes Thema … Meine Meinung zu BTC ist keine Vorgabe sondern nur
> eine Anmerkung."*

**Die Faktenlage war widersprüchlich:**

| | |
|---|---|
| aus **9 Messwerkzeugen** ausgeschlossen | `if sym.upper() == "BTC": continue` |
| im Betrieb **freigegeben** | `asset_hebel_settings.hebel_pruefung_erlaubt = 1` |
| **gehalten** | 0,0506 BTC |
| **30 Signale** | in `signals` |

➤ **BTC wurde bewertet, war aber nie gemessen.** Befund 2.608 galt für BTC
**nicht** — es war nicht in der Menge.

⭐⭐ **Das war keine Entscheidung, sondern eine Messung** — dieselbe
Meta-Lehre wie beim Grundgesamtheits-Fall, wo dreimal eine „Entscheidung"
vorgelegt wurde, die vier Sekunden Rechenzeit war. Gemessen:

| | |
|---|---|
| Anker | 26.560 |
| Signale | 428 (**1,6 %** der Anker) |
| ALLE Anker | +0,2138 % |
| **SIGNALE** | **+1,2848 %** *(`E[R]` +0,4686)* |
| Nullband 90 | +0,3880 % |

✔ **Die Bewertung trägt auch auf BTC** — und zwar deutlich.

⚠️ **Ein Symbol ist keine Menge.** Das Band ist breit, der Befund gilt für
BTC und sonst nichts.

➤ **Damit braucht BTC keine Sonderbehandlung in der Bewertung.** Der
Ausschluss aus der **Messbasis** bleibt davon unberührt und ist sachlich
richtig: er verhindert, dass ein Wert den Querschnitt dominiert. Das ist
etwas anderes, als es nicht zu bewerten.

---

## Was daraus folgt

| # | |
|---|---|
| **1** | ✔ **Die Fallback-Stufen sind belegt, nicht mehr angenommen** — CoinGecko-Daten tragen die Bewertung |
| **2** | Die Quelle selbst weicht nur ~1 % in der ATR ab (gleicher Schätzer) |
| **3** | ✔ BTC trägt — **keine Sonderbehandlung nötig**, und kein Entscheidungsbedarf |
| **4** | Der Weg ist frei für **Stammsatz → Lader → Stufe als Feld** (Reihenfolge aus dem Fallback-Entwurf) |

## Was NICHT folgt

| # | |
|---|---|
| **1** | Eine **genaue Zahl** für den Verlust durch CoinGecko-Daten — 90 Tage sind zu wenig |
| **2** | Ob es über **fünf Jahre** genauso ist — CoinGecko liefert das Fenster nicht |
| **3** | Die **Hebelhöhe** bleibt gesperrt (2.609) |
| **4** | Warum das **höchste ATR-Fünftel** nicht trägt (2.617) |
| **5** | Nichts über **Short** |
