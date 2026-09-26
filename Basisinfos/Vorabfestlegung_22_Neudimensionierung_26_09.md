# Vorabfestlegung 22 — die Neudimensionierung des Hebels

**26.09.2026**, vor der Messung · `messe_hebel_neudimension.py` ·
Frageart **`geometrie`** (Messuniversum, nach `messnorm.FRAGEARTEN`)

> **Nutzerauftrag:** *„der Hebel wird neu dimensioniert und auch neu
> vermessen, da dies bereits der dritte große Hebelumbau ist"*

Voranalyse: `Basisinfos/Voranalyse_Neudimensionierung_Hebel_26_09.md`

---

## Die Frage

Die Bewertung steht (2.608: absolute Schwelle 1,0 ATR, `E[R]` +0,2079).
Was **nicht** steht, sind die Größen, die aus einem Signal einen Trade
machen — und sie stammen aus **vier verschiedenen Quellen mit vier
verschiedenen Annahmen**.

> **Welche Dimensionierung trägt — gemessen auf EINER Ankermenge, mit
> EINER Geometrie, in EINEM Lauf?**

## ⚠️⚠️ Warum ein Lauf und nicht fünf

Die Größen hängen zusammen:

```
Horizont + Stopweite  →  bestimmen R
R                     →  bestimmt Trailing-Abstand und E[R]
E[R] + Schiefe        →  bestimmen die Hebelhöhe
Horizont              →  bestimmt Takt und Finanzierungskosten
CRV                   →  bestimmt die Kelly-Nullstelle 1/(1+CRV)
```

Fünf getrennte Läufe hätten fünf Ankermengen — und damit fünf
Grundgesamtheiten. Das verbietet die stehende Regel.

⭐ **Deshalb: eine Ankermenge, gültig über ALLE Achsen.** Ein Anker zählt
nur, wenn er in jeder Kombination auswertbar ist.

---

## Die Achsen

| # | Achse | Werte | heute |
|---|---|---|---|
| **1** | **Horizont** | 6 · 12 · 24 · 48 · 72 · 120 h | keiner im Signal |
| **2** | **Stopweite** (in ATR) | 1,0 · 1,5 · 2,0 · 2,5 · 3,0 | `stop_min_atr` 2,0 |
| **3** | **Trailing-Auslöser** | 0 · 0,5 · 1,0 · 1,5 R | `ausloese_r` 1,0 |
| **4** | **Trailing-Abstand** | 0,5 · 1,0 · 1,5 R | 1,0 R |

⛔ **Nicht als Achse, sondern als Ergebnis:**

| | |
|---|---|
| **Hebelhöhe** | folgt aus Schiefe, längster Verlustserie und **geometrischem** Ertrag (2.609) — **nicht** aus `E[R]` |
| **CRV** | wird **berichtet**, nicht gesetzt: das erreichte Chance-Risiko-Verhältnis je Zelle. Daraus die Kelly-Null 1/(1+CRV), gegen die gemessene Trefferquote gehalten |
| **Takt / Cooldown** | **eigener, späterer Schritt** — sie wirken auf die fertige Signalmenge |

---

## ⚠️ Die drei Fallen, die die Konstruktion bestimmen

### Falle 1 — `R` ist keine feste Einheit

Ändert sich die Stopweite, ändert sich `R`. `E[R]` über verschiedene
Stopweiten zu vergleichen misst den **Maßstab**, nicht die Leistung
(2.607, 2.616 — derselbe Fehler zweimal).

➤ **Jede Zelle wird in BEIDEN Einheiten ausgewiesen:** `E[R]` für die
Hebelfrage, **Kursprozent** für den Vergleich. **Nur Kursprozent
entscheidet zwischen den Stopweiten.**

### Falle 2 — die Auswahlhärte muss gleich sein

Die Schwelle 1,0 ATR wählt bei jedem Horizont eine andere Zahl Anker.
Zellen mit verschiedener Signalzahl sind nicht vergleichbar (2.616).

➤ **Der Auswahlanteil wird angeglichen**, nicht die Schwelle. Die
Referenzzelle (H=72, Stop 2,0) gibt die Zahl vor.

### Falle 3 — der geometrische Ertrag ist nicht der arithmetische

Bei schiefer Verteilung (2.609: Median −0,1885) liegt der geometrische
Ertrag **unter** dem arithmetischen, und genau er bestimmt, was ein Konto
über viele Trades tut.

➤ **Beide werden ausgewiesen**, und die Hebelhöhe folgt dem
**geometrischen**.

---

## Was je Zelle berichtet wird

| Größe | wofür |
|---|---|
| Signale, Signale/Tag | Betriebslast |
| `E[R]` | Hebelfrage |
| **Ertrag in Kursprozent** | **der Vergleich** |
| Median, getrimmt (5/95) | Schiefe sichtbar machen |
| Trefferquote | gegen die Kelly-Null |
| erreichtes CRV | Kelly-Null 1/(1+CRV) |
| **längste Verlustserie** | Hebelgrenze |
| **geometrischer Ertrag** | **Hebelhöhe** |
| Nullband (40 Ziehungen) | trägt die Zelle überhaupt? |

---

## Die Gegenprüfungen — vor der Messung festgelegt

| # | Prüfung | Was sie ausschließt |
|---|---|---|
| **P1** | **Grenzfall**: `ausloese_r = 0`, `abstand = Stopweite` muss die Trailing-Rechnung aus 2.607 **bitgleich** reproduzieren | einen Fehler im neuen Rechner |
| **P2** | **Nullwelt je Zelle** (Zufallsauswahl gleicher Größe, 40 Ziehungen) | dass ein Ergebnis aus der Auswahlgröße stammt |
| **P3** | **Ankermenge identisch** über alle Zellen | verschiedene Grundgesamtheiten |
| **P4** | **B6** auf der Siegerzelle: erste gegen zweite Fensterhälfte | eine Zelle, die nur früher trug |
| **P5** | **Mehrfachtesten**: die Nullwelt zieht so viele Zufallszellen, wie das Gitter groß ist, und nimmt die beste | dass die beste von N Zellen Auslese ist |

⚠️⚠️ **P5 ist hier entscheidend.** Die beste von N Zellen ist ohne diese
Kontrolle **wertlos** — bei genug Ziehungen findet man immer etwas.

### ⚠️ Gestaffelt statt als volles Gitter — und warum das kein Kompromiss ist

6 × 5 × 4 × 3 = **360 Zellen** auf 3,18 Mio Ankern sind nicht rechenbar
(jede Zelle ist eine eigene Trailing-Rechnung über den vollen Horizont).

➤ **Gemessen wird in zwei Stufen, in der Reihenfolge, die oben ohnehin
zwingend ist:**

| Stufe | Achsen | Zellen | warum zuerst |
|---|---|---|---|
| **G** | Horizont × Stopweite | **30** | sie bestimmen **R** |
| **T** | Trailing-Auslöser × Abstand | **12** | erst in stabiler R-Skala messbar |

⭐ **Dieselbe Ankermenge für beide Stufen** — die Staffelung betrifft die
Auswertung, nicht die Grundgesamtheit. P5 läuft je Stufe mit deren
Zellenzahl (30 bzw. 12).

⚠️ **Was die Staffelung kostet:** eine Wechselwirkung zwischen Stopweite
und Trailing-Auslöser würde sie nicht sehen. Das ist der Preis, und er
wird hier benannt statt verschwiegen. Stufe T wird deshalb **zusätzlich
auf der zweitbesten Geometrie** gerechnet — bleibt der Sieger derselbe,
ist die Wechselwirkung klein.

---

## Was VOR der Messung als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| Eine Zelle trägt **über** dem Mehrfach-Band und besteht B6 | sie wird die Dimensionierung |
| Mehrere gleichwertig | die **robusteste** (flachste Umgebung), nicht die höchste |
| Keine übersteht P5 | ⛔ **die Dimensionierung ist nicht bestimmbar** — und das wäre ein Befund, kein Misserfolg |

⛔ **Kein „das sieht gut aus".** Eine Zelle gilt erst, wenn sie P2, P4 und
P5 besteht.

## Was diese Messung NICHT beantwortet

| # | |
|---|---|
| **1** | **Takt und Cooldown** — eigener Schritt, sie wirken auf die fertige Signalmenge |
| **2** | Die **Architektur** (ein Eingang, zwei Bewertungen) — erst nach der funktionierenden Bewertung, mit dem Nutzer |
| **3** | Ob **LLM-Prompts** für Spot und Hebel getrennt gehören — zurückgestellt (Nutzermeinung: eher getrennt) |
| **4** | Die **Ursache** des Einstiegs-Einbruchs vom 24.08. |
| **5** | Gebühren und Finanzierung bleiben nach **Regel 2** draußen |
| **6** | Nichts über **Short** |
