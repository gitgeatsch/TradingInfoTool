# Voranalyse 1b — die Bewertungsebene neu aufsetzen

**27.09.2026** · vor der Messung · Phase 1b

> **Auftrag:** Chance-Risiko-Verhältnis aus Stop- und Zielabstand, **ohne
> jede Ertragsgröße**. Daraus die Schwelle **und** der Hebel.

---

# ⚠️ Die Abgrenzung, die vorher stehen muss

2.641 verbietet Erträge in der Bewertung. 2.642 hat aber mit **MFE und
MAE aus der Historie** gemessen — und die sind auch Vergangenheit.
**Wo genau liegt die Grenze?**

Die Nutzervorgabe zieht sie selbst:

> *„was aber bekannt ist **aus der Historie** — welche Lagen und Potential
> führten zu einem hohen kurzen Anstieg"*

| | erlaubt | verboten |
|---|---|---|
| **Was** | eine **Prognosefunktion**: Lage → erwartetes Risiko / erwartete Chance | eine **Optimierung auf das Ergebnis**: „wo war der Ertrag maximal / null" |
| **Zielgröße** | **MFE und MAE in ATR** — regelfrei, eine Markteigenschaft | **Ertrag** — enthält Stop, Trailing, und damit die Regel selbst |
| **Richtung** | vorwärts: was ist von dieser Lage zu erwarten | rückwärts: welche Schwelle hätte am besten funktioniert |
| **Beispiel** | ✔ „bei W ≤ −1,5 fällt es im Mittel 0,75 statt 1,08 ATR" | ⛔ „bei W ≤ −1,2881 wird Kelly null" *(2.632/2.640, abgelöst)* |

⭐ **Der Unterschied ist nicht „Historie ja/nein", sondern was kalibriert
wird.** Eine Risikoprognose ist zum Entscheidungszeitpunkt verfügbar; eine
Ertragsoptimierung kennt das Ergebnis, das sie vorhersagen soll.

---

# Die Konstruktion

## Was zum Bewertungszeitpunkt bekannt ist

| Größe | Quelle |
|---|---|
| `ema_abstand_atr` (**die Lage**) | Kurs und EMA48, beide vorhanden |
| **ATR** | Schwankungsbreite, vorhanden |
| **Stopabstand** | `Stopweite × ATR` — gesetzt, nicht gemessen |
| **RM-11-Deckel** | `max_safe_hebel(stop, 0,09)` |

## Was die Historie beisteuert — einmalig kalibriert

| | |
|---|---|
| `mae_erwartet(W)` | wie tief fällt es von dieser Lage aus, in ATR |
| `mfe_erwartet(W)` | wie hoch steigt es, in ATR |
| ➤ `crv_erwartet(W)` | das Verhältnis — **die Chance-Risiko-Prognose** |

⚠️ Beide **regelfrei** (2.642). Kein Stop, kein Trailing, kein Ertrag.

## Daraus die zwei gesuchten Größen

| | |
|---|---|
| **Der Hebel** | folgt dem **Risiko**: je kleiner `mae_erwartet(W)`, desto geringer die Stopwahrscheinlichkeit bei gegebener Stopweite — desto mehr Hebel ist vertretbar. Gedeckelt durch RM-11 und die Zielzone 2–5× |
| **Die Schwelle** | dort, wo der so gerechnete Hebel unter **2×** fällt — die Untergrenze ist eine **Nutzervorgabe**, kein Messergebnis |

⭐ Das ist **2.627 wörtlich** (*„die Hebelhöhe folgt dem Risiko, nicht der
Statistik"*), jetzt mit einer gemessenen Risikoprognose statt einer
gesetzten Annahme.

---

# ⚠️ Die Fallen

| # | |
|---|---|
| **1** | ⛔ **Kein Ertrag, kein Kelly, kein q, kein CRV aus Ergebnissen.** Der Fehler vom 27.09. (2.641) |
| **2** | ⚠️ **`crv_erwartet` ist NICHT das CRV der Handelsregel.** Das eine ist eine Markterwartung in ATR, das andere das Verhältnis von Ziel- zu Stopabstand. Gleicher Name, zwei Größen — sie dürfen im Code nie denselben Bezeichner tragen |
| **3** | **Die Kalibrierung muss out-of-sample halten** — sonst ist die Prognosefunktion angepasst |
| **4** | ⭐ **Die Zielzone 2–5× ist gesetzt, nicht gemessen.** Sie stammt vom Nutzer (*„nicht 10, zu hohes Risiko"*) und ist als Vorgabe zu kennzeichnen, nicht als Befund |
| **5** | ⚠️ **MAE ist nicht die Stopwahrscheinlichkeit.** Der mittlere MAE sagt nichts darüber, wie oft eine bestimmte Stopmarke gerissen wird — dafür braucht es die **Verteilung**, nicht den Mittelwert |
| **6** | **Zeitstabilität und Weglassprobe** — sie haben heute schon zwei Befunde gekippt |
| **7** | ⚠️ Die Prognose gilt für den **Streckenanfang** (2.638), nicht für jeden Anker |

---

# ➤ Die Entscheidung, die vor der Messung steht

Falle 5 ist der Kern: **welche Größe bestimmt den Hebel?**

| Weg | | |
|---|---|---|
| **A** | **Stopwahrscheinlichkeit** aus der MAE-**Verteilung**: wie oft reißt `Stopweite × ATR` bei Lage W? | ⭐ direkt, prüfbar, und es ist eine reine Risikogröße |
| **B** | **Erwartetes CRV** `mfe(W)/|mae(W)|` | ⚠️ enthält die Chance — näher an „Potential", aber weiter von „Risiko" |
| **C** | **Beides**: Stopwahrscheinlichkeit setzt den Deckel, CRV die Feinstufung | mehr Stellschrauben |

**Meine Empfehlung: A.** Die Nutzervorgabe sagt *„zum Zeitpunkt der
Beitragsprüfung ist **das Risiko** und somit der Hebel zu bewerten"* — und
die Stopwahrscheinlichkeit ist genau das. Sie ist außerdem die Größe, die
RM-11 bereits verwendet, und sie lässt sich gegen den realen Stop prüfen.
