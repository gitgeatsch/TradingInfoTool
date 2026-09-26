# Die Neudimensionierung des Hebels — Ergebnis

**26.09.2026** · Befunde 2.620, 2.621 · `messe_hebel_neudimension.py` ·
Vorabfestlegung 22

**3.181.434 Anker · 1.746 Tage · 116 Symbole · gemeinsame Ankermenge über
alle Zellen**

---

## Das Ergebnis

| Größe | heute | **gemessen** | Quelle |
|---|---|---|---|
| **Horizont** (Obergrenze) | — *nicht gesetzt* | **72 h** | Stufe G |
| **tatsächliche Haltedauer** | vier Zahlen, keine im Signal | **42,8 h** *(1,8 Tage)* | erstmals gemessen |
| **Stopweite** | `stop_min_atr` 2,0 | **1,0 ATR** | geometrischer Ertrag |
| **Trailing-Auslöser** | `ausloese_r` 1,0 | **1,5 R** | Stufe T |
| **Trailing-Abstand** | 1,0 R | **0,5 R** | Stufe T |
| **geometrischer Ertrag** | +0,08546 % | **+0,15569 %** | **+82 %** |

✔ **P1** Grenzfall bitgleich mit 2.607 · ✔ **P3** identische Ankermenge ·
✔ **P5** auf beiden Stufen bestanden · ✔ Sieger auf beiden Geometrien
identisch

---

## ⭐⭐⭐ Der Konflikt, der die Antwort entscheidet

Auf **Auslöser 1,5 / Abstand 0,5**, über alle Stopweiten:

| Stop | Kurs % | **geom %** | Dauer | Serie |
|---|---|---|---|---|
| **1,0** | +0,9673 | **+0,15569** | **42,8 h** | 198 |
| 1,5 | +1,0558 | +0,11997 | 58,9 h | 199 |
| 2,0 | +1,1317 | +0,09463 | 65,6 h | 199 |
| 2,5 | +1,2150 | +0,08192 | 68,4 h | 199 |
| **3,0** | **+1,2328** | +0,07090 | 69,9 h | 199 |
| 3,5 | +1,2141 | +0,06165 | 70,6 h | 199 |
| 4,0 | +1,2164 | +0,05357 | 71,1 h | 199 |

**Kursprozent maximiert bei Stop 3,0 — der geometrische Ertrag bei Stop
1,0, und dort ist er mehr als doppelt so hoch.**

### Warum das kein Widerspruch zur Vorabfestlegung ist

Dort stand: *„nur Kursprozent entscheidet zwischen Stopweiten"* — weil
`E[R]` über verschiedene Stopweiten den **Maßstab** mitmisst (Falle 1).
Das bleibt richtig. Aber die beiden Größen beantworten verschiedene Fragen:

| Maßstab | Frage | gilt bei |
|---|---|---|
| **Kursprozent** | Wie viel Kursbewegung fange ich ein? | fester **Kursgröße** |
| **geometrisch** | Was macht mein **Konto** über viele Trades? | festem **Risiko** |

⭐⭐ **Beim Hebel gilt festes Risiko** — RM-1 setzt 1 % je Trade. Der
geometrische Ertrag ist damit maßgeblich, und er ist **nicht** vom
R-Nenner verzerrt, weil er das Risiko explizit fixiert.

➤ **Stop 1,0 ATR** — mit dem Vorbehalt aus RM-11 (unten).

---

## Die Stufen im Einzelnen

### Stufe G — Horizont × Stopweite (35 Zellen)

Der Ertrag steigt **monoton mit dem Horizont**: +0,0152 % bei H2 bis
+1,0858 % bei H72. Bei festem Trailing (wie 2.607) lag **H72 / Stop 2,0**
vorn.

✔ **P5:** Bestes-von-35-Band **0,0510 %** — die Siegerzelle liegt mit
+1,0858 % weit darüber. Keine Auslese.

⭐ **Die Haltedauer ist erstmals gemessen** und weicht stark vom Horizont
ab: bei H72 / Stop 1,0 sind es **29,8 h**, bei Stop 2,0 schon 68,6 h. Der
Horizont ist eine **Obergrenze**, keine Dauer.

### Stufe T — Auslöser × Abstand (2 × 12 Zellen)

| Geometrie | beste Zelle | heute | Unterschied |
|---|---|---|---|
| H72 / Stop 2,0 | **1,5 / 0,5** → +1,1317 % | +1,0213 % | +0,1105 Pp |
| H72 / Stop 2,5 | **1,5 / 0,5** → +1,2150 % | +1,0827 % | +0,1323 Pp |

✔ **Derselbe Sieger auf beiden Geometrien** — und beide bestehen P5.

### ⚠️⚠️ Die Wechselwirkung war real — und die Staffelung hätte sie verfehlt

| | Stufe G *(Trailing fest)* | Stufe T *(Trailing optimiert)* |
|---|---|---|
| Stop 2,0 | **+1,0858 %** ← vorn | +1,1317 % |
| Stop 2,5 | +1,0766 % | **+1,2150 %** ← vorn |

**Die Reihenfolge dreht sich.** In der Vorabfestlegung stand, die
Staffelung könne eine Wechselwirkung nicht sehen und Stufe T laufe deshalb
auch auf der zweitbesten Geometrie. **Genau das hat sie aufgedeckt** — und
die anschließende Messung über *alle* Stopweiten war die Folge.

⚠️ Ohne diese Zusage in der Vorabfestlegung wäre Stop 2,0 das Ergebnis
gewesen, und es wäre falsch gewesen.

---

## ⛔⛔ Zwei Befunde, die bleiben

### 1. Die längste Verlustserie ist von der Geometrie unabhängig

**198–199 über alle Stopweiten** — von 1,0 bis 4,0 ATR. Bei 11,6
Signalen/Tag sind das rund **17 Tage ohne einen Gewinner**.

➤ **Sie lässt sich durch Dimensionierung nicht wegoptimieren.** Das ist
die eigentliche Hebelgrenze, und sie gehört in die Hebelhöhe (2.609),
nicht in die Geometrie.

### 2. Ein enger Stop rückt die Liquidation näher — ungeprüft

Stop 1,0 ATR ist geometrisch optimal. Ob der Stop dann noch **vor** der
Zwangsliquidation liegt, prüft RM-11 (`agent/krypto/hebel_risk_gate.py`).
**Das ist nicht gemessen** und gehört vor jede Übernahme.

⚠️ Nutzervorgabe 26.09. dazu: *„dann zu engen und weiten stop
vermeiden"* — die Stopweite braucht eine **begründete Spanne**, nicht nur
ein Optimum. Offener Punkt.

---

## Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Gebühren und Finanzierung sind NICHT eingerechnet** (Regel 2, Nutzerwarnung 26.09.: *„Finanzierung bitte aus den Bewertungen — nur rechnerisch in der Mail und u.U. bei der Positionsführung"*). Die Haltedauer steht als **Fakt** dabei, nicht als Auswahlkriterium |
| **2** | Die **Hebelhöhe** ist weiter offen (2.609) — die Verlustserie von 199 ist ihr Eingang |
| **3** | **RM-11** gegen Stop 1,0 ist **ungeprüft** |
| **4** | Die **Stopspanne** (zu eng / zu weit) ist nicht bestimmt |
| **5** | **Takt und Cooldown** sind ein eigener Schritt — der Cooldown ist laut Nutzer ein Relikt und wird adaptiert |
| **6** | Ob **Z-2** (`crv_minimum` 2,0) beim Trailing greifen darf, ist offen — das gemessene MFE/MAE liegt bei 1,55 |
| **7** | Nichts über **Short** |
