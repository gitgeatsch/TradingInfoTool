# Woher kommt die negative Drift? — Schritt 2 des Hebel-Neubaus

**25.09.2026** · Werkzeug `messe_drift_herkunft.py` · Befund **2.598** ·
**116 Symbole · 3.157.882 Anker · k = 1,0 × ATR · nur lesend**

**Nutzerentscheidung:** Drift zerlegen, bevor die A-Faktoren gebaut werden.

---

# § 1 Das Ergebnis in drei Sätzen

> ⭐⭐⭐ **Es ist das MARKTFENSTER, nicht eine Teilmenge von Symbolen.** In
> **2023 und 2026** ist `E[R]` brutto **positiv** — in allen vier Zellen. In
> 2022, 2024 und 2025 nicht.
>
> ⛔ **Die Symbolauswahl ist als Weg ausgeschlossen, und zwar gemessen:** die
> Rückschau verbessert `E[R]` um Faktor 4, die **kausale** Auswahl nach
> Vorjahresdrift macht es **schlechter**. Schlechte Drift ist von Jahr zu Jahr
> **nicht vorhersagbar**.
>
> ⭐⭐⭐ **Und die Zahl, die alles einordnet:** die Jahresdrift spannt
> **0,0869**, die Lageordnung **0,0072** — **Faktor 12**. Das Regime ist
> zwölfmal wichtiger als die Lage.

---

# § 2 ACHSE 1 — Das Marktfenster, über alle vier Zellen gleich

**`E[R]` brutto je Jahr, k = 1,0 × ATR:**

| Jahr | Anker | Drift H6 | **E[R] H6** | Drift H24 | **E[R] H24** | |
|---|---|---|---|---|---|---|
| 2022 | 341.969 | −0,0148 | −0,0143 | −0,0522 | −0,0430 | ⛔ |
| **2023** | 437.645 | +0,0087 | **+0,0083** | +0,0347 | **+0,0256** | ⭐⭐ |
| 2024 | 702.882 | +0,0006 | −0,0006 | +0,0027 | −0,0063 | ⛔ knapp |
| 2025 | 954.528 | −0,0094 | −0,0076 | −0,0414 | −0,0228 | ⛔ |
| **2026** | 720.042 | +0,0013 | **+0,0014** | +0,0055 | **+0,0040** | ⭐⭐ |

✔ **Bei CRV 2,0 dasselbe Muster** (2023 +0,0083/+0,0277 · 2026
+0,0011/+0,0046). Das Urteil hängt nicht am Zuschnitt.

⭐ **Und 2026 ist das laufende Jahr.** Das ist erheblich mehr wert als „in
irgendeinem Jahr der Vergangenheit".

✔✔ **Abnahmeprobe bestanden:** die ankergewichtete Summe der Jahre
reproduziert die Gesamtzahl auf **9 Dezimalstellen** (−0,0025172 gegen
−0,0025172).

⚠️ **Ein Mangel an dieser Probe, der erst in der zweiten Fassung wegfiel:**
zuerst verglich sie gegen das Gesamt über **alle** Anker und meldete eine
Abweichung von −0,000015. Die bestand genau aus den Ankern des
übersprungenen Jahres 2021 — **eine Abnahmeprobe, die zwei verschiedene
Mengen vergleicht, prüft nichts.**

---

# § 3 ⛔ ACHSE 2 und 3 — was es NICHT ist

## 3.1 Nicht die Handelbarkeit

**Volumen-Fünftel (30-Tage-Mittel bis t, streng kausal), CRV 1,5 / H6:**

| Fünftel | 0 | 1 | 2 | 3 | 4 |
|---|---|---|---|---|---|
| Drift | +0,00002 | −0,00217 | −0,00426 | −0,00449 | −0,00319 |
| `E[R]` | +0,00014 | −0,00195 | −0,00364 | −0,00410 | −0,00302 |

⚠️ **Fünftel 0 ist knapp positiv, aber es gibt keine Monotonie** — das
Minimum liegt in Fünftel 3, nicht am Rand. Ein Liquiditätseffekt müsste
geordnet verlaufen. **+0,00014 ist außerdem kleiner als die
Lageordnung selbst** und damit keine tragfähige Größe.

## 3.2 ⛔ Nicht eine Teilmenge von Symbolen — und das ist doppelt belegt

| | |
|---|---|
| **Konzentration** | Drift-**Median** über 116 Symbole **−0,00315** gegen Ankermittel **−0,00282** — der Median ist **schlechter**. Die Drift ist **breit**, nicht konzentriert |
| **Verteilung** | 10. Perzentil −0,00911 · 25. −0,00597 · 50. −0,00315 · 75. −0,00081 · **90. +0,00305** — erst das oberste Zehntel ist positiv |

## 3.3 ⭐⭐⭐ Und der Weglass-Versuch, in zwei Fassungen — der entscheidende Test

| Symbole weg | **Rückschau** `E[R]` | **KAUSAL** (Vorjahr) `E[R]` |
|---|---|---|
| 0 % | −0,00251 | −0,00251 |
| 10 % | −0,00184 | −0,00259 |
| 20 % | −0,00127 | −0,00273 |
| 30 % | **−0,00056** | **−0,00285** |

➤ **Die Rückschau verbessert um Faktor 4,5. Die kausale Auswahl
verschlechtert.** Und sie verschlechtert **monoton mit der Dosis** — das ist
keine Zufallsschwankung.

⚠️⚠️ **Damit ist der Weg „schlechte Symbole aussortieren" ausgeschlossen, und
zwar gemessen statt vermutet.** Die Rückschau-Verbesserung ist reine
Überanpassung: sie wählt nach dem Ergebnis. **Schlechte Drift eines Symbols
ist von Jahr zu Jahr nicht vorhersagbar.**

⭐ Dass beide Fassungen im Werkzeug stehen, ist der Punkt — die
Rückschauspalte allein hätte wie ein Erfolg gelesen werden können.

---

# § 4 ⭐⭐⭐ Was die Barriere tatsächlich tut: sie versichert, sie verdient nicht

**`E[R]` minus Drift je Jahr** — also was die Barriere gegenüber reinem
Halten beiträgt:

| Jahr | Drift H24 | `E[R]` − Drift | |
|---|---|---|---|
| 2025 | −0,0414 | **+0,0187** | Barriere **hilft** |
| 2022 | −0,0522 | **+0,0092** | Barriere **hilft** |
| 2026 | +0,0055 | −0,0015 | Barriere kostet |
| 2024 | +0,0027 | −0,0091 | Barriere kostet |
| 2023 | +0,0347 | −0,0091 | Barriere kostet |

➤ **Das Vorzeichen folgt dem Vorzeichen der Drift, mit umgekehrtem
Zeichen.** In fallenden Jahren schneidet der Stop den Verlust ab, in
steigenden deckelt das Ziel den Gewinn.

⚠️⚠️ **Die Barriere erzeugt keine Kante — sie verschiebt Risiko.** Das ist
exakt der registrierte Befund *„ein Barrierensystem hat Erwartungswert
null"*, hier zum ersten Mal **je Regime** aufgelöst statt im Mittel.

---

# § 5 ⭐⭐⭐ Die Zahl, die über das Vorgehen entscheidet

| | |
|---|---|
| Spanne der **Jahresdrift** (H24) | **0,0869** (−0,0522 bis +0,0347) |
| Spanne der **Lageordnung** netto (2.597) | **0,0072** |
| ➤ **Verhältnis** | **Faktor 12,1** |

⚠️⚠️⚠️ **Das Regime ist zwölfmal wichtiger als die Lage.** Die Lage lässt sich
ordnen — das ist mit Nullband in 9 von 9 Zellen belegt — aber die Ordnung
bewegt ein Zwölftel dessen, was das Marktfenster bewegt.

## 5.1 Die konstruktive Folge

➤ **Der Hebel braucht eine Aussage über das REGIME, nicht über bessere
Asset-Merkmale.** Fünf weitere A-Faktoren derselben Familie können Faktor 12
nicht schließen.

⭐ **Und das ist eine andere Art Frage als alles bisher Gemessene:** die
Symboldrift ist nachweislich **nicht** vorhersagbar (§ 3.3). Über die
**Marktdrift** sagt das nichts — sie ist eine eigene Größe, und für sie
existieren im Projekt bereits Datenquellen (BTC-Dominanz, Fear & Greed,
Marktbreite), die für Asset-Merkmale nie in Frage kamen.

⚠️ **Das ist eine Hypothese, kein Befund.** Dass die Marktdrift ordenbar
wäre, ist **nicht gemessen** — und der Analogieschluss von der Symboldrift
verbietet sich, weil dort gerade das Gegenteil herauskam.

---

# § 6 ⛔ Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Nicht, dass Long ab jetzt trägt.** 2023 und 2026 tragen, 2022/2024/2025 nicht. Ohne eine **vorab** verfügbare Regimeaussage ist das nur im Rückblick sortierbar — genau der Fehler, den § 3.3 bei den Symbolen entlarvt hat |
| **2** | ⛔ **Nicht, dass ein Regimefilter existiert.** Er ist die naheliegende nächste Frage, nicht eine Antwort |
| **3** | ⚠️ **2024 ist die Warnung:** dort war die Drift **positiv** (+0,0006/+0,0027) und `E[R]` trotzdem negativ. Ein Regimefilter müsste also nicht nur die Richtung treffen, sondern eine **Mindeststärke** — bei H24 rund **+0,009** |
| **4** | ⛔ **Nichts über Short.** Die Spiegelrichtung ist damit weiterhin ungeprüft; 2022 und 2025 hätten sie getragen, 2023 und 2026 nicht |
| **5** | ⚠️ **Fünf Jahre sind fünf Beobachtungen.** Für eine Regimeaussage ist das eine sehr kleine Stichprobe, und 2021 fiel wegen Dünne ganz heraus |
| **6** | ⚠️ **Überlebensverzerrung bleibt offen.** Gemessen wurde auf 116 Symbolen, die **heute** in der Basis sind |

---

# § 7 Standards

| | |
|---|---|
| **gilt** | Abnahmeprobe (Zerlegung setzt sich zusammen, 9 Dezimalstellen) · Dosis-Wirkung (Weglass-Leiter 0/10/20/30 %) · Rückschau **gegen** kausal ausgewiesen · kausale Merkmalsbildung (Volumen 30-Tage-Mittel bis t) |
| ⚠️ **fehlt** | **Nullband und Trennschärfe** — diese Messung stellt eine **Zerlegungs**frage (woraus besteht eine bekannte Zahl?), keine Beitragsfrage. Die Jahresunterschiede sind mit Faktor 12 über der Lageordnung, deren Nullband in 2.597 bei 0,0005 lag; ein eigenes Band würde am Urteil nichts ändern. ➤ **Bevor aus einem Regimefilter ein Beitrag wird, ist es nachzuholen** |
| ➤ **Frageart** | **`zaehlung`** — benannt: woraus besteht die in 2.597 gemessene Drift? |
