# Vorabfestlegung 27 — die vier Hebelstufen auf der inversen Achse

**26.09.2026**, vor der Messung · `messe_vier_hebelstufen.py` ·
Frageart **`markt`**

> **Nutzervorgabe wörtlich:** *„warum soll es nicht möglich sein, je nach
> Qualität des Signals — also angenommene HÖHE und RISIKO — das in 4 TEILE
> zu teilen … es soll das positive Chance-Risiko-Verhältnis die Hebelhöhe
> bestimmen und je nach Verhältnis, gemessen von dir, 4 TEILE: HEBEL 2x
> oder 3x oder 4x oder 5x auf Basis deiner MESSUNGEN"*

---

## ⛔ Was an meiner letzten Vorlage falsch war

Ich habe die Hebelhöhe aus **Kelly** abgeleitet. Kelly beantwortet aber
eine andere Frage:

| Frage | Antwort kommt aus |
|---|---|
| Wie viel **Kapital insgesamt** darf im Feuer sein? | Kelly, Positionszahl, Korrelation |
| Wie hoch ist der Hebel **dieses einen Trades**? | Chance-Risiko-Verhältnis + RM-11 |

Weil ich die Höhe aus Kelly zog, musste ich die Positionszahl einführen —
und dann die Korrelation, um sie zu korrigieren. Ein Umweg zu einer Frage,
die nicht gestellt war.

⚠️ **2.627 hatte es bereits richtig**: *die Hebelhöhe folgt dem Risiko,
nicht der Statistik* — über RM-11 und Verlustserie, **nicht** über Kelly.
Davon bin ich abgewichen, ohne es zu bemerken.

## Die Frage

> **Trägt eine Stufung des Hebels nach Qualitätsviertel (2x/3x/4x/5x)
> gegenüber einem konstanten Hebel gleicher mittlerer Höhe?**

## Die Achse — und warum die Viertel keine gesetzten Grenzen sind

| | |
|---|---|
| Menge | alle Signale über der Mindestschwelle (dort, wo `kelly(W)` in der Kurve aus 2.630 die Null schneidet — **gerechnet**, nicht gesetzt) |
| Einteilung | **vier gleich große Teile** nach `ema_abstand_atr` |
| Stufen | bestes Viertel **5×**, dann 4×, 3×, 2× |
| Deckel | **RM-11** je Trade (`max_safe_hebel(stop, 0,09)`) |

⭐ **Vier gleich große Teile sind keine Stellschraube** — anders als die
Bandgrenzen −2,0/−1,5/−1,2, auf die es keine Antwort gab. Eine
Quartilseinteilung ist durch die Zahl der Stufen vollständig bestimmt,
und die Zahl vier ist die Nutzervorgabe.

## Der Prüfstand — er steht seit 2.508

Logwachstum `ln(1 + einsatz · hebel · kursprozent)` je Anker.

⭐ **Sizing beurteilt man am geometrischen Wachstum, nicht am
Mittelwert** — deshalb dieser Maßstab und kein anderer.

### ⚠️ Der Vergleich muss bei GLEICHEM mittleren Hebel laufen

Sonst misst man, dass mehr Hebel mehr bewegt, und nicht, ob die
**Zuordnung** trägt.

| Variante | Hebel je Viertel (bestes → schlechtestes) | Mittel |
|---|---|---|
| **gestuft** | 5 / 4 / 3 / 2 | 3,5 |
| **flach** (Kontrolle) | 3,5 / 3,5 / 3,5 / 3,5 | 3,5 |
| **invers** (Gegenprobe) | 2 / 3 / 4 / 5 | 3,5 |
| **zufällig** (Gegenprobe) | je Anker gelost aus {2,3,4,5} | 3,5 |

⭐ **Invers ist die schärfste Kontrolle**: trägt die Stufung, muss sie
schlechter sein als flach — nicht nur die gestufte besser.

## ⚠️ Die Fallen

| # | |
|---|---|
| **1** | **Gleicher mittlerer Hebel** in allen Varianten, sonst ist der Vergleich wertlos |
| **2** | **Blockbootstrap** (Block 60) statt unabhängiger Ziehungen — die Anker sind zeitlich gekoppelt, gemessen als rho 0,30 in 2.630 |
| **3** | **Bezug ist der Nullpunkt**, nicht null (Messstandard seit 08.09.) |
| **4** | Auch die **Stufenhöhen selbst** prüfen: bringt eine steilere (1/3/5/7, Mittel 4) oder flachere (3/3,3/3,7/4) Stufung mehr? Sonst ist 2–5 nur geraten |
| **5** | **Regel 2**: Gebühren und Finanzierung bleiben draußen |

## Was vorher als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| gestuft > flach **und** invers < flach, beides über dem Nullband | ✔ die vier Stufen sind belegt — das ist die Hebelhöhe |
| gestuft > flach, aber invers ≈ flach | ⚠️ die Stufung trägt, aber die **Richtung** ist nicht belegt |
| gestuft ≈ flach | ⛔ die Höhe trägt nicht — dann konstanter Hebel über der Schwelle |

## Was NICHT beantwortet wird

Gebühren (Regel 2) · Gaps und Slippage · wie viel Kapital insgesamt
gebunden wird (das ist die Kelly-Frage, und sie ist eine **andere**) ·
Short
