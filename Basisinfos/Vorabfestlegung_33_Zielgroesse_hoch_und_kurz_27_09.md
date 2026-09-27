# Vorabfestlegung 33 — welche Zielgröße bildet „hoch und kurz" ab?

**27.09.2026** · Phase 1a · `messe_zielgroesse.py` · Frageart **`markt`**

> **Nutzervorgabe, die den Horizont-Widerspruch auflöst:**
> *„Der Einstieg funktioniert über Lage, Richtung und Risikobewertung zu
> einem Zeitpunkt (Bewertungszeitpunkt), wo der **Horizont nicht bekannt
> ist** — was aber bekannt ist aus der Historie: **welche Lagen und
> Potential führten zu einem hohen kurzen Anstieg**."*
>
> **Und die Warnung dazu:** *„sei nur vorsichtig mit ERTRAG — u.U. nimmt
> man Kursanstieg oder eine andere Größe, die korrekter ist."*

---

## ⭐ Die Frage war falsch gestellt

Ich hatte gefragt: *„welcher Horizont gilt — H24, 3 Tage oder 0,30 Tage?"*
**Der Horizont ist kein Eingang der Bewertung** — zum Bewertungszeitpunkt
weiß niemand, wie lange der Trade läuft. Er ist ein **Messfenster**.

## ⭐⭐ Und der Maßstab war falsch gewählt

**„Ertrag" ist das, was eine bestimmte Handelsregel** (Stop 1,00,
Trailing 1,5/0,5) **aus einer Lage macht.** Wer die Regel optimiert und
den Maßstab daraus ableitet, schließt einen Kreis.

➤ Die Bewertung misst das **Potential der Lage** — nicht, was eine Regel
daraus holt.

| Größe | | |
|---|---|---|
| **MFE in ATR** | wie hoch geht es, in der eigenen Schwankungsbreite | ✔ **regelfrei** |
| **MAE in ATR** | wie tief geht es vorher gegen mich | ✔ regelfrei |
| **MFE/MAE** | die Asymmetrie | ⭐ 2.606: **MFE allein trennt nicht** |
| **Zeit bis MFE** | „kurz" | ✔ regelfrei |
| *Ertrag / R* | was die Regel erzielt | ⛔ enthält Stop und Trailing |

⚠️ **Nicht in R**: `R = Stopweite × ATR`, und die Stopweite ist ein
Regelparameter. **ATR ist eine Markteigenschaft.**

⭐ `messe_selektion.py:74 mfe_mae()` rechnet bereits so — streng kausal,
in ATR. Ergänzt wird nur die **Zeit bis MFE**.

## Die Frage

> **Über welches Fenster ordnet die Lage MFE/MAE am schärfsten — und wie
> verhält sich das zur Zeit bis MFE?**

## Der Aufbau

| | |
|---|---|
| Fenster | 6 · 12 · 24 · 48 · 72 · 120 Stunden |
| Zielgrößen | MFE · MAE · **MFE/MAE** · Zeit bis MFE · **MFE ÷ Zeit** |
| Vergleichsarm | der **Ertrag** aus der heutigen Geometrie — nur zur Einordnung |
| Maßstab | **standardisierter Abstand** `(echt − Nullmittel) / Nullstreuung`, weil die Größen verschiedene Einheiten haben |

⚠️ Bis 120 h, weil die Positionsführung mit **0–5 Tagen** rechnet. Die
Haltedauer selbst gehört **nicht** zur Bewertung (Phase 2).

## ⚠️ Die Fallen

| # | |
|---|---|
| **1** | ⛔ **Ebene B.** Das Ergebnis fließt **nicht** als Schwelle in die Bewertung zurück — daran bin ich am 27.09. gescheitert (2.641) |
| **2** | **P5**: 6 Zielgrößen × 6 Fenster = **36 Ziehungen**. Bestes-von-36-Band |
| **3** | **Gleicher Auswahlanteil** in allen Zellen |
| **4** | **Tagestreue Nullwelt** je Zelle |
| **5** | ⭐ **MFE allein ist verführerisch und untauglich** (2.606): dort lagen alle sieben EMA-Längen über dem Band, das Maß unterschied gar nicht |
| **6** | **Zeit ist umgekehrt gepolt** — kürzer ist besser. Vorzeichen prüfen |
| **7** | ⚠️ **MFE/MAE ist instabil, wenn MAE gegen null geht.** Eine Untergrenze ist zu setzen und auszuweisen |
| **8** | ⚠️ **Längere Fenster haben mechanisch höheres MFE** — ein Vergleich über Fenster hinweg braucht die Zeitnormierung, sonst gewinnt immer das längste |
| **9** | Regel 2: Gebühren und Finanzierung bleiben draußen |

## Was schon gemessen ist — und nicht wiederholt wird

| | |
|---|---|
| **2.626** | Die Achse trägt auf **allen** Horizonten 6–72 h; Ertrag **je Stunde** bei H6 um **Faktor 8,6** höher als bei H72 |
| **2.627** | Kennzahlen je Horizont: H6 q 66,9 %, Kelly 0,4253, Verlustserie 67 · H12 65,5/0,4025/69 · H24 59,9/0,3241/117 |
| **2.628** | Geometrie über 42 Zellen — ⚠️ nach **absolutem** Ertrag entschieden, deshalb H24 |
| **2.620/2.623** | MFE/MAE liegt bei **1,48 bis 1,55** |

➤ **H6 ist nach jedem Kriterium außer dem absoluten Ertrag besser.**
Diese Messung prüft, ob das auch auf der **regelfreien** Zielgröße gilt.

## Was vorher als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| MFE/MAE ordnet am schärfsten bei kurzem Fenster | ✔ bestätigt 2.626/2.627 regelfrei — die Geometrie gehört auf H6 neu gerechnet |
| Schärfste Ordnung bei H24 | ⭐ dann war 2.628 richtig, und der Widerspruch löst sich |
| Kein Fenster sticht heraus | ⚠️ dann ist das Fenster gleichgültig, und die Wahl folgt der Positionsführung |

## Was NICHT beantwortet wird

Die Schwelle (Ebene A, kommt in 1b) · Positionsgröße, Haltedauer, Takt
(Phase 2) · die übrigen Beiträge (1c) · die Quellenfrage (1d)
