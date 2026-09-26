# Die Geometrie auf der inversen Achse — und die Kalibriergrenze

**26.09.2026** · Befunde 2.628, 2.629 · `messe_geometrie_invers.py` ·
Vorabfestlegung 24

---

## Das Ergebnis

**3.184.194 Anker · 63.628 Signale** (täglich beste 2 %, niedrigster
`ema_abstand_atr`) · **tagestreue Nullwelt**

| | |
|---|---|
| **Horizont** | **24 h** |
| **Stopweite** | **1,00 ATR** |
| **Trailing-Auslöser** | **1,5 R** |
| **Trailing-Abstand** | **0,5 R** |
| Ertrag | **+1,5883 %** je Trade |
| Stopquote | 17,6 % |
| längste Verlustserie | 119 |

✔ **P1** bitgleich gegen `trailing()` **und** `trailing_mit_ausloeser()` ·
✔ **P3** identische Ankermenge · ✔ **P5** auf beiden Stufen ·
✔ derselbe Trailing-Sieger wie in 2.620 — er ist von der Auswahlrichtung
unabhängig

### Stufe G — die drei besten brauchbaren

| | Kurs % | geom % | Stopquote | Serie |
|---|---|---|---|---|
| **H24 / Stop 1,00** | **+1,5196** | +0,20254 | 28,1 % | 119 |
| H48 / Stop 1,00 | +1,3312 | +0,18391 | 60,8 % | 133 |
| H48 / Stop 1,50 | +1,3082 | +0,11751 | 15,5 % | 118 |

P5: Bestes-von-42-Band **+0,3423 %** — die Siegerzelle liegt darüber.

### Stufe T — derselbe Sieger auf beiden Geometrien

| Geometrie | beste Zelle | Ertrag |
|---|---|---|
| H24 / Stop 1,00 | Auslöser **1,5** / Abstand **0,5** | **+1,5883 %** |
| H48 / Stop 1,00 | Auslöser **1,5** / Abstand **0,5** | +1,4671 % |

---

## ⛔ Zwei Fehler, vor dem Ergebnis gefunden

### 1. Die Stopquote war falsch gerechnet

Ich hatte sie über die Haltedauer bestimmt (`dauer < H`). Das verpasst
jeden Stop, der in der **letzten Stunde** greift — bei H2 wurde nur der
Ausstieg nach *einer* Stunde gezählt, bei H3 nach *einer oder zwei*.
Ergebnis war ein unmöglicher Sprung von **15,9 % auf 97,0 %** zwischen
zwei benachbarten Horizonten.

✔ Behoben: die Stopmarke wird dort gesetzt, wo der Stop greift.

### 2. P1 prüfte den falschen Rechner

Die Bitgleichheitsprobe lief gegen die **importierte** Funktion — gerechnet
wurde mit der **neuen, lokal gebauten**. Eine Probe auf fremdem Code sagt
nichts über den eigenen.

✔ Behoben: P1 prüft jetzt die neue Funktion gegen **beide** bestehenden.

---

## ⭐⭐ Die Kalibriergrenze — eine Nutzerpräzisierung

> *„bei Handelbarkeit nicht Bewertung bin ich kritisch … es muss immer um
> die Bewertung gehen — ABER wenn ich es richtig verstehe geht es hier mehr
> um **Kalibrierung**: von wo bis wohin macht ein Hebel Sinn, und das zielt
> zum Teil auf die Geometrie ab … darf aber **keinen Einfluss auf die
> Bewertung selbst** haben."*

✔ **Genau richtig, und präziser als meine Formulierung.** Ich hatte von
„Handelbarkeit statt Bewertung" gesprochen — das ist keine eigene
Kategorie:

| | bestimmt durch | Gebühren? |
|---|---|---|
| **Bewertung** — welches Asset, welche Lage | `ema_abstand_atr`, täglich bester Wert | ⛔ **nie** (Regel 2) |
| **Geometrie** — Stop, Horizont, Trailing | diese Messung | ⚠️ nur als **Grenze des sinnvollen Raums** |

➤ **Die Auswahl der Signale ändert sich um keinen einzigen Anker.**

### ⛔ Der Mangel meiner Vorabfestlegung

Ich hatte nur eine **Untergrenze** für die Stopquote festgelegt (< 5 % =
wertlos). Die Daten zeigten, dass **auch das andere Ende unbrauchbar ist**:

| Stop | Kurs % | geom % | Stopquote |
|---|---|---|---|
| **0,15** | +0,5502 | **+0,48973** ← Maximum | **100,0 %** |
| 1,00 | +1,5196 | +0,20254 | 28,1 % |

Der geometrische Ertrag war bei Stop 0,15 **mehr als doppelt so hoch** —
aber dort wird **jeder** Trade ausgestoppt.

### ✔ Gelöst durch Messung, nicht durch eine gesetzte Zahl

Gebühren laut `docs/hebel_positionsformel.md`: **0,3 % je Trade +
0,18 %/Tag**:

| Stop | Stopquote | Dauer | brutto | Kosten | **NETTO** |
|---|---|---|---|---|---|
| **0,15** | 46,1 % | 3,5 h | +0,6109 | 0,3266 | **+0,2844** |
| 0,40 | 35,6 % | 13,8 h | +1,2461 | 0,4037 | +0,8424 |
| 0,60 | 24,1 % | 19,0 h | +1,4797 | 0,4423 | +1,0373 |
| **1,00** | 10,4 % | 22,5 h | +1,5885 | 0,4686 | **+1,1200** |
| 1,50 | 4,0 % | 23,5 h | +1,5852 | 0,4761 | +1,1092 |
| 2,00 | 1,9 % | 23,8 h | +1,5924 | 0,4783 | +1,1141 |

⭐⭐ **Das Netto-Optimum liegt bei Stop 1,00 ATR — genau dem Wert aus
Stufe G.** Kein Konflikt zwischen den beiden Wegen.

⭐ **Und der scheinbare geometrische Vorteil enger Stops löst sich auf:**
Stop 0,15 ist netto der **schlechteste**. Die Gebühr frisst bei kurzen,
häufig gestoppten Trades mehr als die Hälfte. Das geometrische Maximum war
ein Artefakt einer Rechnung, die Kosten nicht kannte.

➤ **Eine gesetzte Obergrenze für die Stopquote ist damit unnötig** — sie
ergibt sich aus den Kosten selbst.

---

## Was NICHT folgt

| # | |
|---|---|
| **1** | **Slippage ist nicht modelliert** — sie träfe enge Stops zusätzlich, verstärkt das Ergebnis also nur |
| **2** | Die Stopquote ist in der Kostenrechnung über den **Ertrag** geschätzt (10,4 %), in Stufe G über die **Stopmarke** (17,6 %) — Größenordnung gleich, Zahlen nicht identisch |
| **3** | Die **Gebühren gehören nicht in die Bewertung** und stehen nur in dieser Kalibrierung |
| **4** | **Gaps** sind weiter nicht modelliert (2.627) |
| **5** | Nichts über **Short** |
