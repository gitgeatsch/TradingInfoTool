# Die inverse Achse — belegt, aber für den Hebel kaum brauchbar

> ⭐⭐⭐ **Nutzereinordnung 26.09. — bitte zuerst lesen:** *„nur
> dokumentieren, aber wird erst für später relevant — sollte für Hebel nur
> bedingt von Bedeutung sein."*
>
> **Das ist fachlich schlüssig:** Die inverse Achse ist **Mean Reversion** —
> sie kauft, was gefallen ist, und wartet auf die Rückkehr. Der **Hebel
> braucht das Gegenteil**: eine kurze, schnelle Aufwärtsbewegung, damit sich
> Finanzierung und Liquidationsrisiko lohnen.
>
> ➤ Was hier gemessen ist, gehört zum **Spot- und Akkumulationsarm**.
>
> ⚠️⚠️ **Für den Hebel folgt daraus:** `ema_abstand_atr` trägt in der einen
> Richtung nicht (2.624) und in der anderen nur für eine **langsame**
> Bewegung. **Keine Richtung dieser Achse ist für den Hebel brauchbar.**


**26.09.2026** · Befund 2.626 · `messe_inverse_achse.py`

Nach 2.625: die Ordnung existiert, zeigt aber in die andere Richtung.
**Diese Fassung prüft sie mit genau den Mitteln, die den Vorgänger zu Fall
gebracht haben.**

---

## Das Ergebnis

**3.181.434 Anker · 1.746 Tage · 115 Symbole** · Auswahl **je Tag** die
besten k nach **niedrigstem** `ema_abstand_atr` · tagestreue Nullwelt

| Prüfung | Ergebnis |
|---|---|
| **Out-of-sample**, rollierend mit Lücke, 3 Anteile × 4 Fenster | ✔ **12 von 12** |
| **Je Asset** — Rangkorrelation | ✔ **115 von 115 negativ** (Median −0,1537) |
| **Positivkontrolle** | ✔ 5 von 5 |
| **Absolut handelbar** | ✔ **+1,33 %** je Trade gegen **−0,05 %** über alle Anker |
| **Spiegelprobe** (Gegenrichtung) | ✔ **−1,23 %** — symmetrisch |
| **ATR-Artefakt** | ✔ ausgeschlossen |
| **Zeitstabilität** | ✔ alle 6 Jahre |

### Out-of-sample im Einzelnen

| Anteil | Fenster 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 1 % | +0,9466 | +1,8267 | +1,4526 | +1,0829 |
| 2 % | +0,9513 | +1,7360 | +1,4094 | +1,0028 |
| 5 % | +1,0276 | +1,5645 | +1,4500 | +0,9714 |

Nullbänder durchweg zwischen +0,02 und +0,10 % — die Werte liegen **10- bis
30-fach darüber**.

### Kein ATR-Artefakt — innerhalb jedes Fünftels

| ATR-Fünftel | ALLE % | Auswahl % | Differenz |
|---|---|---|---|
| 1 (niedrig) | +0,0944 | +0,7191 | **+0,62** |
| 2 | +0,0715 | +1,0372 | +0,97 |
| 3 | −0,0886 | +1,2726 | +1,36 |
| 4 | −0,2652 | +1,4373 | +1,70 |
| 5 (hoch) | −0,0867 | +2,1819 | **+2,27** |

ATR der Auswahl: **1,02×** des Medians — sie wählt keine volatileren Werte.

### Zeitstabil — alle sechs Jahre

| Jahr | ALLE % | Auswahl % | Differenz |
|---|---|---|---|
| 2021 | +0,8180 | +2,0275 | +1,21 |
| **2022** *(Bärenmarkt)* | −0,5758 | +1,4929 | **+2,07** |
| 2023 | +0,2915 | +1,3125 | +1,02 |
| 2024 | +0,0679 | +1,9344 | +1,87 |
| 2025 | −0,1483 | +1,1587 | +1,31 |
| 2026 | −0,0381 | +0,8949 | +0,93 |

---

## ⛔⛔ Die offene Flanke: Kapital, nicht Ertrag

> **Nutzererklärung 26.09.:** *„Ende 2025 ist BTC vom Bullen in den
> Bärenmarkt gewechselt … Das waren ca. **11 Monate Nachkauf** — **nach 2
> Wochen hätte man kein Kapital mehr**, wenn man den Boden bzw.
> Trendumkehr nicht erkennt."*

⚠️⚠️ **Die Messung beantwortet das nicht.** Sie sagt „+1,33 % je Trade" —
sie sagt **nichts** darüber, wie viele Trades **gleichzeitig** offen wären.

**Und das ist bei dieser Achse die entscheidende Frage:** Sie kauft, was
gefallen ist. Im Bärenmarkt fällt alles — also feuert sie ununterbrochen,
und zwar genau dann, wenn jeder einzelne Kauf zu früh kommt.

➤ Der gemessene Ertrag je Trade und die **Kapitalbindung über die Zeit**
sind zwei verschiedene Größen. Die erste ist belegt, die zweite **nicht
gemessen**.

⭐ **Ein Gegenargument steht in den Daten:** 2022 war Bärenmarkt, und die
Achse trug dort **am stärksten** (+2,07 Pp). Das entkräftet die Sorge
**nicht** — es zeigt nur, dass die *Auswahl* auch dort funktioniert. Ob
das *Kapital* reicht, ist eine andere Rechnung.

### Der Unterschied zum Spot-Fehler — und die Nähe

| | Spot-Fehler (25.09.) | inverse Achse |
|---|---|---|
| Bezug | **Einstandspreis** — „im Verlust nachkaufen" | **eigener EMA** — Kursverlauf des Assets |
| Auswahl | kein Querschnitt | **je Tag das beste von 115** |

✔ Fachlich sind es verschiedene Größen — ein Asset kann unter seinem
48-Stunden-EMA stehen und weit im Gewinn sein.

⚠️ **Die Nähe bleibt trotzdem real**, und die Ursache ist dieselbe: **ohne
Bodenerkennung kauft man in den fallenden Markt hinein.** Was die inverse
Achse davor bewahrt, ist allein der **Querschnitt** — sie nimmt nicht
alles Gefallene, sondern je Tag nur die besten 1–5 %.

---

## Was daraus folgt

| # | |
|---|---|
| **1** | ⭐ **Die Richtung ist umgedreht und belegt** — mit allen Prüfungen, die 2.608 zu Fall gebracht haben |
| **2** | **Die Auswahl gehört je Tag**, nicht über eine globale Schwelle — sonst misst man die Tageswahl mit |
| **3** | Die **Trefferquote liegt bei 48 %** — der Gewinn kommt aus der **Asymmetrie**, nicht aus häufigerem Rechthaben |
| **4** | ⛔ Die **Kapitalbindung über die Zeit** ist die nächste Messung, nicht der nächste Bau |

## Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Keine Verdrahtung.** Die Kapitalfrage steht davor |
| **2** | Die **Geometrie** (2.620) wurde für die *alte* Richtung dimensioniert — ob Stop und Trailing für die inverse passen, ist **ungeprüft** |
| **3** | Die **Hebelhöhe** bleibt offen — 48 % Trefferquote und Asymmetrie sind ein anderer Kelly-Fall als bisher gerechnet |
| **4** | Gebühren und Finanzierung bleiben draußen (Regel 2) |
| **5** | Nichts über **Short** |
