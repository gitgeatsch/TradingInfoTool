# Die Selektion trägt — der erste positive Befund der Messreihe

**26.09.2026** · Befund **2.605** · Vorabfestlegung 20 · `messe_selektion.py`
**116 Symbole · 3.211.104 Anker · vier Horizonte · vier Schärfegrade**

**Nutzervorgabe, die es auslöste:** *„wir suchen GUTE Einstiege mit
OPTIMALEN Voraussetzungen für eine schnelle hohe Bewegung nach oben — das
ist SELEKTION der besten Ausgangslagen innerhalb von 1–5 Tagen."*

---

# § 1 Das Ergebnis

> ⭐⭐⭐ **Die Spitze ist messbar besser — und der Vorsprung WÄCHST mit der
> Schärfe.** `ema_abstand_atr` und `rsi` liegen bei 0,1 % Auswahl in allen
> vier Horizonten über dem Nullband, **out-of-sample bestätigt**.
>
> ⭐ **MFE/MAE liegt bei 1,44 bis 1,80** — die Aufwärtsbewegung ist bis zu
> 80 % größer als der Rücklauf. Bei `zufall` ist sie **1,00**.
>
> ⛔ **Mit festem Ziel und Stop trägt es trotzdem nicht.** Der Ertrag hängt
> an der **Positionsführung**, nicht an der Einstiegsmessung.

---

# § 2 Warum diese Messung anders ist als 2.595 bis 2.604

| | bisher | hier |
|---|---|---|
| **Menge** | Fünftel = 20 %, ~575.000 Anker | **0,1 % = ~3.200 Anker** |
| **Horizont** | 6 und 24 Stunden | **1, 2, 3, 5 Tage** |
| **Zielgröße** | `E[R]` bei festem Ausstieg | **MFE** in ATR + Trefferquote |

⚠️⚠️ **Ein Mittelwert über 20 % kann eine Spitze von 1 % nicht zeigen.** Das
stand seit 2.594 registriert (*„ein Merkmal kann im Mittel nichts bewegen und
trotzdem die Extreme ordnen"*) — und ich hatte danach wieder Mittelwerte
gemessen. **Der Hinweis kam vom Nutzer, nicht aus der Messung.**

---

# § 3 Die Zahlen — Schärfe 0,1 %

| Horizont | Merkmal | MFE | Nullband | MAE | **MFE/MAE** | Treffer |
|---|---|---|---|---|---|---|
| **1 Tag** | `ema_abstand_atr` | **1,053** | 0,607 | −0,726 | **1,45** | 12,2 % |
| | `rsi` | **0,913** | 0,607 | −0,583 | **1,57** | 10,7 % |
| | `vola` ⚠️ | 0,339 | 0,607 | −0,290 | 1,17 | 1,3 % |
| | `zufall` ⚠️ | 0,586 | 0,607 | −0,598 | **0,98** | 2,7 % |
| **3 Tage** | `ema_abstand_atr` | **1,677** | 1,130 | −1,067 | **1,57** | 24,5 % |
| | `rsi` | **1,485** | 1,130 | −0,955 | **1,56** | 21,7 % |
| **5 Tage** | `ema_abstand_atr` | **2,174** | 1,521 | −1,282 | **1,70** | 30,0 % |
| | `rsi` | **1,960** | 1,521 | −1,230 | 1,59 | 28,6 % |

## 3.1 ⭐ Die Dosis-Wirkung — der eigentliche Nachweis

**Vorsprung der MFE über die Nullwelt, von 20 % zu 0,1 % Schärfe (1 Tag):**

| Merkmal | 20 % | 5 % | 1 % | 0,1 % | |
|---|---|---|---|---|---|
| `ema_abstand_atr` | +0,066 | +0,156 | +0,284 | **+0,461** | ⭐⭐ wächst |
| `rsi` | +0,049 | +0,110 | +0,205 | **+0,321** | ⭐⭐ wächst |
| `ema_lage` | +0,027 | +0,039 | +0,073 | +0,139 | ⭐⭐ wächst |
| `oi_aenderung` | +0,011 | +0,032 | +0,100 | +0,186 | ⭐⭐ wächst |
| **`vola`** ⚠️ | −0,095 | −0,126 | −0,172 | **−0,253** | **fällt** |
| **`zufall`** ⚠️ | +0,000 | +0,001 | −0,000 | **−0,005** | ✔ **flach** |

✔✔ **`zufall` bleibt flach** — das war die Abnahmeprobe aus Vorabfestlegung
20 § 6. Die Nullwelt ist korrekt gebaut.

⭐ **`vola` FÄLLT** — der Dauerverdacht dieser Messreihe („es ist nur
Volatilität") ist damit so klar entkräftet wie nie.

## 3.2 ✔✔ B6 — out-of-sample, Grenze auf Hälfte 1 bestimmt

| Horizont | Merkmal | H1 | **H2** | Band | MFE/MAE |
|---|---|---|---|---|---|
| 1 Tag | `ema_abstand_atr` | 0,995 | **1,072** | 0,624 | 1,44 |
| | `rsi` | 0,716 | **1,062** | 0,629 | **1,80** |
| 3 Tage | `ema_abstand_atr` | 1,520 | **1,768** | 1,177 | 1,62 |
| | `rsi` | 1,184 | **1,707** | 1,164 | 1,76 |
| | `zufall` / `vola` | | im Band | | ✔ |

⭐ **Out-of-sample ist stärker als in-sample** — keine Überanpassung.

---

# § 4 ⛔ Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔⛔ **Nicht, dass es mit festem Ziel und Stop trägt.** Bei `rsi`/3 Tage: `E[R] = 0,259 × 2 − 0,741 × 1 = −0,22`. **Negativ.** Der Ertrag hängt am **Trailing** |
| **2** | ⚠️ **Bei 5 Tagen liegt `zufall` ÜBER dem Band** (1,556 gegen 1,521). Ein Fehlalarm von vier — im Rahmen, aber die 1- bis 3-Tage-Befunde sind **sauberer** |
| **3** | ⚠️ **`ema_abstand_atr` bei 0,1 % heißt STARK ÜBERDEHNT** — Kurs weit über der EMA. Das widerspricht der Nutzervorgabe *„nicht überkauft"*. Die Daten sagen: die überdehntesten Lagen laufen am weitesten weiter |
| **4** | ⛔ **Nichts über Handelbarkeit.** 0,1 % sind rund 3 Signale pro Tag über 116 Symbole — Liquidität und Slippage ungeprüft |
| **5** | ⚠️ **Die EMA-Länge ist GESETZT, nicht gemessen** (48 Stunden). Siehe § 5 |

---

# § 5 ⚠️ Offen: die EMA-Länge

Gemessen wurde mit **EMA über 48 Stunden** (2 Tage), dazu 12 h, 20 h und
200 h für `trendstruktur`.

⚠️⚠️ **Das ist NICHT der klassische 50er oder 200er** — die beziehen sich
auf **Tageskerzen** und entsprächen 1.200 bzw. 4.800 Stunden. Meine
„EMA200" sind 200 **Stunden**, also gut 8 Tage.

➤ **Die Längen sind gesetzt, nicht gemessen.** Ob 48 h die richtige Wahl für
einen 1- bis 3-Tage-Horizont ist, ist eine offene Frage — und sie ist als
Achse messbar.
