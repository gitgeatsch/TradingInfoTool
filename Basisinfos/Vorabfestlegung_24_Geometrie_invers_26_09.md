# Vorabfestlegung 24 — die Geometrie auf der inversen Achse

**26.09.2026**, vor der Messung · `messe_geometrie_invers.py` ·
Frageart **`geometrie`**

> **Nutzerauftrag:** *„Geometrie auf der inversen Achse nachmessen, prüfen,
> gegenprüfen"*

---

## Warum die Geometrie aus 2.620 nicht übernommen werden darf

Horizont 72 h, Stop 1,0 ATR, Trailing 1,5 / 0,5 wurden für die **alte
Richtung** dimensioniert — die inzwischen widerlegt ist (2.624).

⚠️ **Und ein Messwert zeigt, dass sie nicht passt:** Bei H6 wird der Stop
in **0,4 % der Fälle** erreicht (2.627). In sechs Stunden bewegt sich der
Kurs selten um 1 ATR — das ist eine **Tagesspanne**. Ein Stop, der nie
greift, ist keine Risikobegrenzung, sondern Dekoration.

## Was sich gegenüber Vorabfestlegung 22 ändert

| | 2.620 (alt) | **jetzt** |
|---|---|---|
| Auswahl | globale Schwelle `≥ 1,0 ATR` | **je Tag die besten 2 %** (niedrigster Wert) |
| Nullwelt | gepoolt | ⭐ **tagestreu** — der Standard, und genau daran fiel 2.608 |
| Stopweiten | 1,0 – 3,0 ATR | ⭐ **nach unten erweitert**: 0,15 – 2,0 |

⭐ **Die Erweiterung nach unten ist der Kern:** Bei H2–H12 muss geprüft
werden, ob ein **engerer** Stop trägt — die 0,4-%-Quote sagt, dass 1,0 ATR
dort wirkungslos ist.

## Die Achsen

| Achse | Werte |
|---|---|
| **Horizont** | 2 · 3 · 6 · 12 · 24 · 48 h |
| **Stopweite** | 0,15 · 0,25 · 0,4 · 0,6 · 1,0 · 1,5 · 2,0 ATR |
| **Trailing-Auslöser** | 0 · 0,5 · 1,0 · 1,5 R *(Stufe T)* |
| **Trailing-Abstand** | 0,5 · 1,0 R *(Stufe T)* |

Gestaffelt wie in 2.620: **Stufe G** (Horizont × Stop) bestimmt R, **Stufe
T** folgt auf den zwei besten Geometrien.

## Die Fallen — unverändert gültig

| # | |
|---|---|
| **1** | `R` ist keine feste Einheit → **nur Kursprozent** vergleicht über Stopweiten |
| **2** | Auswahlanteil angleichen — hier durch „täglich 2 %" **automatisch erfüllt** |
| **3** | Die Hebelhöhe folgt dem **geometrischen** Ertrag, nicht `E[R]` |
| **4** | ⭐ **NEU: tagestreue Nullwelt.** Eine freie Ziehung zerstört die Tagesclusterung und macht das Band zu eng (`messnorm`: 12,4 Punkte auf einem Nulleffekt) |

## Zusätzlich berichtet

**Die Stopquote** — wie oft der Stop überhaupt greift. Eine Zelle, in der
er unter 5 % greift, ist als Risikobegrenzung wertlos, auch wenn ihr
Ertrag gut aussieht.

## Die Gegenprüfungen

| # | |
|---|---|
| **P1** | **Bitgleichheit**: `ausloese_r = 0`, Abstand = Weite reproduziert `trailing()` |
| **P2** | **Tagestreue Nullwelt** je Zelle, 40 Ziehungen |
| **P3** | **Ankermenge identisch** über alle Zellen (gültig für den längsten Horizont) |
| **P5** | **Mehrfachtesten** — bestes von N Zufallszellen |

## Was vorher als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| Eine Zelle über dem Mehrfach-Band **und** Stopquote ≥ 5 % | sie wird die Geometrie |
| Beste Zelle hat Stopquote < 5 % | ⚠️ **verworfen** — kein Stop, kein Hebel |
| Keine übersteht P5 | ⛔ die Geometrie ist nicht bestimmbar |

## Was NICHT beantwortet wird

Gebühren und Finanzierung (Regel 2) · Gaps und Slippage · Short
