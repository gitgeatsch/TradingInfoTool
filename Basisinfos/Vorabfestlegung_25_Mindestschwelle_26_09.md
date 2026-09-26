# Vorabfestlegung 25 — die Mindestschwelle auf der inversen Achse

**26.09.2026**, vor der Messung · `messe_mindestschwelle.py` ·
Frageart **`markt`**

> **Nutzerauftrag:** *„Mindestschwelle zuerst messen, prüfen und
> gegenprüfen, dann Simulation mit Rang und Schwelle"*

---

## Warum sie fehlt

2.626/2.628 wählen **je Tag die besten 2 %** — eine reine **Rangfolge**.
Das hat zwei Lücken:

| # | |
|---|---|
| **1** | ⛔ **Bei einem einzelnen Asset gibt es keinen Rang.** Genau der Einwand vom Vormittag: *„das System muss auch bei nur EINEM Asset funktionieren"* |
| **2** | ⛔ **An einem Tag ohne gute Lage kauft sie trotzdem** — der beste von 115 schlechten Werten ist immer noch schlecht |

➤ Gesucht ist eine **absolute Schwelle** in `ema_abstand_atr`, unterhalb
derer ein Signal für sich steht.

## Die Frage

> **Ab welchem absoluten Wert trägt ein Signal — unabhängig vom Rang?**

## Die Achse

| | |
|---|---|
| Schwellen | −1,5 · −1,2 · −1,0 · −0,8 · −0,6 · −0,4 · −0,2 · 0,0 |
| Auswahl | **alle** Anker mit `ema_abstand_atr ≤ Schwelle` |
| Geometrie | H24 / Stop 1,00 ATR / Trailing 1,5 / 0,5 (aus 2.628) |

## ⚠️ Die Fallen

| # | |
|---|---|
| **1** | **Beide Maßstäbe ausweisen**: absolut (die Schwelle wirkt absolut) **und** relativ zum Tag (misst die Auswahlgüte). Die registrierte Regel *„Gewichtung ausweisen"* gilt |
| **2** | **Tagestreue Nullwelt** — sonst dasselbe Artefakt wie bei 2.608 |
| **3** | ⭐ **Die Abdeckung gehört dazu**: an wie vielen Tagen gibt es überhaupt ein Signal? Eine Schwelle, die nur an 5 % der Tage greift, ist für den Betrieb etwas anderes als eine, die täglich feuert |
| **4** | **Kein Mehrfachtesten-Freifahrtschein**: acht Schwellen sind acht Ziehungen, P5 gilt |

## Was vorher als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| Eine Schwelle trägt **absolut** über dem Mehrfach-Band, mit brauchbarer Abdeckung | sie wird die Mindestschwelle |
| Nur mit Rang, nicht absolut | ⚠️ die Auswahl bleibt eine **Rangfolge** — und funktioniert bei einem Asset nicht |
| Keine trägt | ⛔ dann ist die inverse Achse **nur** ein Querschnittsmaß |

⭐ **Die Simulation danach nutzt beides**: Rang (je Tag die besten k)
**und** Schwelle (absolut) — ein Signal muss beide erfüllen.

## Was NICHT beantwortet wird

Gebühren in der Bewertung (Regel 2) · Gaps und Slippage · Short
