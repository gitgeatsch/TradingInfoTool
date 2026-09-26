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

---

# § 6 Die EMA-Länge — gemessen statt gesetzt (Nachtrag, Befund 2.606)

**Nutzerfrage:** *„EMA — was meinst du damit? dieser Indikator hat auch
mehrere Bedeutungen und muss korrekt angewendet werden."*

## 6.1 Was gemessen wurde

`ema_abstand_atr = (close − EMA_L) / (ATR × close)` für **sieben Längen**
von 12 bis 1.200 Stunden, also 0,5 bis 50 Tage. Die letzte entspricht dem
**klassischen 50-Tage-EMA**.

| Konstruktionspunkt | warum |
|---|---|
| **Vorlauf für ALLE gleich** (5 × 1.200 h) | sonst hätte jede Länge ihre eigene Ankermenge — verschiedene **Grundgesamtheiten** |
| **Nullwelt zieht SIEBEN Zufallsreihen** und nimmt die beste | sieben Längen zu prüfen und die beste zu nehmen ist Auslese; so enthält die Nullwelt das **Mehrfachtesten** |
| ⚠️ EMA vektorisiert (`lfilter`) | gegen die Schleifenfassung geprüft: relative Abweichung **1e-5** nach 5 × Periode |

## 6.2 Das Ergebnis — MFE/MAE hat ein Optimum bei 2 Tagen

| EMA | Tage | 1T/1 % | 1T/0,1 % | 3T/1 % | 3T/0,1 % |
|---|---|---|---|---|---|
| 12 h | 0,5 | 1,38 | 1,38 | 1,40 | 1,38 |
| 24 h | 1,0 | 1,42 | 1,40 | 1,47 | 1,46 |
| **48 h** | **2,0** | **1,42** | **1,45** | **1,55** | **1,58** |
| 96 h | 4,0 | 1,39 | 1,36 | 1,54 | 1,48 |
| 240 h | 10 | 1,26 | 1,33 | 1,32 | 1,41 |
| 480 h | 20 | 1,05 | 1,32 | 1,12 | 1,30 |
| **1.200 h** | **50** | **0,95** | **0,96** | **1,01** | **0,99** |

➤ **In allen vier Zellen ist 48 h maximal**, und zum klassischen 50-Tage-EMA
fällt MFE/MAE auf **≈ 1,00** — also auf **vollkommen symmetrisch**.

⭐ **Die gesetzte Länge war richtig — aber das war Glück.** Jetzt ist sie
gemessen, mit sauberer Dosis-Wirkung über die Länge.

## 6.3 ⚠️ Warum MFE allein nicht genügt hätte

Nach **MFE allein** liegen **alle sieben** Längen über dem Mehrfach-Band —
das Maß unterscheidet nicht. Bei 0,1 %/3 Tagen wäre sogar **480 h** die
„beste" Länge (MFE 1,776 gegen 1,694 bei 48 h).

➤ **Erst MFE/MAE trennt.** Ein hoher MFE kann auch durch mehr **Bewegung**
entstehen; die Asymmetrie zwischen Auf und Ab kann das nicht.

## 6.4 Die fachliche Einordnung

| | |
|---|---|
| **SMA** | einfacher Durchschnitt, alle Punkte gleich gewichtet |
| **EMA** | exponentiell, Gewicht α = 2/(p+1) — reagiert schneller |
| **klassisch** | EMA50/EMA200 auf **Tageskerzen** als mittelfristiger Trendfilter („liegt über dem 50er") |

⚠️⚠️ **Für die Frage „springt dieser Wert in 1–3 Tagen" ist der klassische
50er zu träge** — gemessen MFE/MAE ≈ 1,00, also keinerlei Asymmetrie.

➤ **Die Bezugslänge muss zum Vorhersagehorizont passen.** Bei 1–3 Tagen sind
das rund **2 Tage**. Das ist kein Widerspruch zur klassischen Verwendung,
sondern eine andere Frage: der 50er misst, ob ein **Trend intakt** ist, nicht
ob eine **schnelle Bewegung** bevorsteht.


---

# § 7 Absicherung, Umlegung und Trailing (Nachtrag, Befund 2.607)

**Nutzerauftrag:** *„zuerst sichere die aktuelle messung ab dass diese auch
zukünftig gültigkeit hat. Was du mir unterschlagen hast ist die UMLEGUNG und
WIRKUNG AUF UNSER SYSTEM."*

## 7.1 ✔✔ Absicherung — der Befund gilt in JEDEM Jahr

| Jahr | Anker | MFE | Nullband | MFE/MAE | |
|---|---|---|---|---|---|
| 2022 | 344.849 | 1,193 | 1,001 | 1,34 | ✔ |
| 2023 | 448.723 | 1,498 | 1,205 | 1,58 | ✔ |
| 2024 | 705.730 | 1,328 | 1,070 | 1,47 | ✔ |
| 2025 | 956.850 | 1,402 | 1,056 | 1,40 | ✔ |
| **2026** | 708.146 | **1,848** | 1,244 | **1,82** | ✔ **am stärksten** |

⭐ **Anders als alle Regime-Befunde ist dieser nicht fensterabhängig** — und
das **jüngste** Jahr ist das beste. ⚠️ B6 allein hätte das nicht gezeigt: ein
Effekt, der 2022 stark war und seit 2025 fehlt, bestünde B6 und wäre wertlos.

## 7.2 Die Umlegung auf das System

| Schärfe | **Signale/Tag** | MFE/MAE | Treffer 2R | `E[R]` (1 ATR Trail) |
|---|---|---|---|---|
| 20 % | 364 | 1,22 | 15,9 % | +0,0115 |
| 5 % | 91 | 1,40 | 19,1 % | +0,0692 |
| **1 %** | **18** | **1,55** | 22,8 % | **+0,1155** |
| 0,1 % | **1,8** | 1,57 | 25,7 % | +0,1034 |

⭐⭐ **Die Qualität steigt monoton, der Erwartungswert je Risiko aber
nicht.** Bei **1 %** liegt das Optimum — mehr Schärfe bringt ab dort nur
weniger Signale, keinen höheren Ertrag.

➤ **Die Hebelabstufung ist damit ablesbar:** 20 % kein Hebel, 5 % klein,
**1 % das Optimum**, 0,1 % nicht besser.

## 7.3 ✔✔ Trailing — der erste positive Erwartungswert der Messreihe

| Schärfe | 0,5 ATR | 1,0 ATR | 1,5 ATR | 2,0 ATR |
|---|---|---|---|---|
| 20 % | +0,0106* | +0,0115* | +0,0112* | +0,0105* |
| 5 % | +0,0576* | +0,0692* | +0,0595* | +0,0496* |
| 1 % | +0,1212* | **+0,1155*** | +0,1005* | +0,0808* |
| 0,1 % | +0,1458* | +0,1034* | +0,0797* | +0,0598* |
| **ALLE Anker** | **−0,0001** | −0,0020 | −0,0062 | −0,0091 |

⭐ **Die Gesamtmenge liegt bei null** — der positive Wert kommt aus der
**Selektion**, nicht aus der Geometrie. Genau wie 2.597 es verlangt.

### Signifikanz und B6

| Trailing | Schärfe | `E[R]` | ±Tagesfehler | H1 | H2 |
|---|---|---|---|---|---|
| **1,0 ATR** | **1,0 %** | **+0,1155** | 0,0188 | +0,0407 | **+0,1786** |
| 1,0 ATR | 0,1 % | +0,1034 | 0,0355 | +0,0704 | +0,1260 |
| 1,5 ATR | 1,0 % | +0,1005 | 0,0181 | +0,0699 | +0,1263 |
| 1,5 ATR | 0,1 % | +0,0797 | 0,0324 | +0,0623 | +0,0916 |

➤ `E[R]` ist das **Sechsfache** des Tagesfehlers, und die **jüngere** Hälfte
ist in allen vier Fällen die stärkere.

### ⚠️ Ein Darstellungsfehler, der dabei auffiel

`R` ist in Einheiten des **Anfangsrisikos** (Weite × ATR). Bei 0,5 ATR ist
der Nenner halb so groß — der Wert ist **anders skaliert**, nicht besser:

| Schärfe 0,1 % | 0,5 ATR | 1,0 ATR | 1,5 ATR | 2,0 ATR |
|---|---|---|---|---|
| R | +0,1458 | +0,1034 | +0,0797 | +0,0598 |
| **absolut in ATR** | 0,0729 | 0,1034 | **0,1196** | **0,1196** |

➤ **Die Reihenfolge dreht sich.** Beide Sichten gelten: **R** ist die
**Hebelfrage** (Ertrag je eingesetztem Risiko), **absolut** die Frage, ob der
Trade Gebühren trägt.

## 7.4 ✔✔ Die Trailing-Rechnung, an bekannter Wahrheit geprüft

| Testfall | Ergebnis | erwartet | |
|---|---|---|---|
| monoton steigend | +5,2311 | +5,2311 | ✔ exakt |
| monoton fallend | −1,0000 | −1,0000 | ✔ exakt |
| hoch, dann Absturz | +4,2592 | Höchststand +5,2040 | ✔ sichert einen Teil |
| engere Weite sichert mehr | 0,5→+9,52 · 1,0→+4,26 · 2,0→+1,63 | monoton | ✔ |
| flach | +0,00000 | 0 | ✔ exakt |

## 7.5 ⛔ Was weiter NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Kein Ertrag im Betrieb.** Gebühren und Finanzierung bleiben draußen (Regel 2), die Ausführbarkeit ist ungeprüft |
| **2** | ⚠️ **Die Messung lief auf 116 Symbolen** aus `stundenkurse.db` — der Betrieb hat eine **andere** Grundgesamtheit |
| **3** | ⚠️ **Die Hebelhöhe selbst ist nicht gemessen** — die Abstufung ist ein Verhältnis zwischen Schärfegraden |
| **4** | ⛔ Nichts über Short |
