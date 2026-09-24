# Konzept — Spot und Hebel sind **nicht** dieselbe Bewertung

**24.09.2026.** Nutzerthese: *„deine Aussage ist für mich der Nachweis, dass
deine Bewertung HEBEL und SPOT sind dasselbe **FALSCH** ist. Auch der
Einstieg von Spot und Hebel muss unterschiedlich erfolgen — zumindest
rechnerisch und fachlich anders gelagert."*

---

# § 1 Die Bewertung: **die These ist belegt**

## 1.1 Der Beleg steht in der Messung, die das Gegenteil entschieden hat

**2.490-barriere-niemand** (20.09.) hat entschieden, dass der Hebel **keine
eigene Bewertung** bekommt. Die Vorabfrage lautete wörtlich:

> *„sobald A1 behoben und `barriere` messbar ist, wird gemessen, ob ein
> Beitrag auf `barriere` **anders** wirkt als auf `bewegung_r`. Trägt er
> dort anders, bekommt der Hebel seine eigene Bewertung — sonst nicht."*

Und die Basis dieser Messung, aus dem Befund selbst:

> *„Fenster ab 2023-01-01, **H20**, Tagesklammer"*

⚠️⚠️⚠️ **Die Messung hat die ZIELGRÖSSE gewechselt (`bewegung_r` →
`barriere`), den HORIZONT aber nicht.** Sie lief auf **H20** — dem
Spot-Horizont.

**Gemessen am 24.09.:** die echten Hebelpositionen haben eine
**Median-Haltedauer von 0,30 Tagen** (188 Positionen, 2.493), der Betrieb
rechnet mit **rund 3 Handelstagen** (2.513).

> ➤ **Die Begründung für die Zusammenführung steht auf einem Horizont, den
> der Hebel nicht hat.** Ein halber Wechsel ist kein Wechsel.

## 1.2 Und Regel 3 verlangt das Gegenteil dessen, was daraus wurde

Wortlaut in `CLAUDE.md`:

> **Beim HEBEL kein Asset-Rang** — *der Hebel kommt aus der
> Wahrscheinlichkeit **dieses Trades**, nicht aus „Rang 3 von 41"*

⛔ Daraus wurde im Memory: *„die Einstiegsbewertung ist für beide Lagen
dieselbe (Regel 3), und der Hebel bekommt keine eigene Bewertung."*

**Das ist eine Fehlinterpretation.** Regel 3 verbietet einen **Asset-Rang**
als Hebelquelle. Sie verlangt die Wahrscheinlichkeit **dieses Trades** —
und ein Hebeltrade *ist* ein anderer Trade als ein Spot-Trade.

---

# § 2 Worin sich die beiden Lagen **fachlich** unterscheiden

| | `spot × einstieg` | `hebel × einstieg` |
|---|---|---|
| **Erfolgsbedingung** | Kursbewegung nach H Tagen | **Ziel vor Stop** |
| **Zielgröße** (Norm) | `bewegung_r` | **`barriere`** ✔ bereits getrennt |
| **Horizont** | H20 plausibel | **0,3–3 Tage** ⛔ nicht getrennt |
| **Beendet der Stop?** | nein | **ja** (`STOP_BEENDET`) |
| **Zusätzliches Risiko** | — | **Liquidation** (RM-11), Finanzierungskosten |
| **Offene Position** | zählt mit ihrem Kurs | zählt als **Niete** |
| **Zeitkosten** | keine | **0,18 %/Tag** (2.493) |

## ⚠️⚠️ Der Unterschied, der alles entscheidet: die Barrierengeometrie

`1/(1+CRV)` gilt für **unbegrenzte** Zeit. Bei begrenztem Horizont gewinnt
die **nähere** Barriere — Stop bei −1 R, Ziel bei +2 R.

**Gemessen (24.09., normgerecht, Block aus `messnorm._block`):**

| | Auflösungsquote | Treffer der Entschiedenen | kelly |
|---|---|---|---|
| **H5** | 64,3 … 47,9 % | **32,3 … 28,4 %** | **überall negativ** |
| H20 | 96,0 … 85,9 % | 36,4 … 31,9 % | +0,047 … −0,021 |

> ➤ **Auf dem Horizont, auf dem der Hebel stattfindet, ist Kelly in jeder
> Lage negativ — aus Geometrie, nicht aus Bewertung.**

Dieselben Beiträge, dieselbe Zielgröße, **anderer Horizont** — und das
Vorzeichen dreht. **Deutlicher lässt sich „nicht dasselbe" nicht zeigen.**

---

# § 3 Was daraus folgt — und was **nicht**

## ✔ Belegt

1. **Die Zusammenführung steht auf einer Messung mit falschem Horizont.**
   2.490 ist damit **nicht widerlegt**, aber es beantwortet die Frage
   **nicht**, die es beantworten sollte.
2. **Die Norm kennt keinen Horizont je Lage** — das ist der
   Konstruktionsfehler darunter (2.570).
3. **Spot und Hebel unterscheiden sich in sieben Punkten**, von denen die
   Norm heute genau **einen** abbildet (die Zielgröße).

## ⛔ Nicht belegt — und ausdrücklich nicht behauptet

- **Nicht**, dass ein Hebel mit eigener Bewertung *funktionieren* würde.
  Auf `barriere` trägt bei H20 kein Beitrag; auf H5 ist Kelly überall
  negativ. **Eine eigene Bewertung könnte genauso leer ausgehen.**
- **Nicht**, dass die heutige Kette falsch *rechnet*. Sie rechnet
  konsistent — nur beantwortet sie für den Hebel die falsche Frage.
- **Nicht**, dass Regel 3 verletzt wurde. Verletzt wurde ihre
  **Auslegung** im Memory, nicht die Regel.

---

# § 4 Das Konzept — wie wir damit umgehen

## Schritt 1 ⚠️ Zuerst die Norm, nicht die Messung

**`messnorm` bekommt einen `HORIZONT_JE_LAGE`**, analog zu
`ZIELGROESSE_JE_LAGE`:

```
('spot',  'einstieg')     -> 20      wie bisher, plausibel
('hebel', 'einstieg')     ->  3      die gemessene Haltedauer
('spot',  'akkumulation') -> 90      das Akkumulationsmaß misst dort
```

**Warum zuerst:** die Blocklänge folgt dem Horizont (`_block`). Solange er
fehlt, zieht jeder Horizontfehler durch die ganze Messanlage — wie mein
eigener Verstoß am 24.09. gezeigt hat. ⚠️ Und es ist **kein Umbau am
Betrieb**, nur an der Messnorm.

## Schritt 2 — 2.490 auf dem richtigen Horizont wiederholen

Dieselbe Messung, dieselben Kandidaten, **Horizont 3 statt 20**. Die
Vorabfrage von 2.291 bleibt wortgleich stehen:

> *„Trägt ein Beitrag auf `barriere` anders als auf `bewegung_r`, bekommt
> der Hebel seine eigene Bewertung — sonst nicht."*

⚠️ **Entscheidungsregel unverändert übernehmen**, nicht neu formulieren —
sonst entsteht ein Suchpreis.

## Schritt 3 — die Geometrie an die Lage binden

**Fällt Schritt 2 wieder negativ aus**, ist das *kein* Argument für die
Zusammenführung, sondern für die **Geometriefrage**: bei 3 Tagen
Haltedauer ist CRV 2 strukturell im Nachteil (§ 2). Dann wäre zu messen,
welches CRV zu *dieser Haltedauer* passt — nicht welches global optimal
ist (das ist mit 2.564 beantwortet: global gibt es kein lageabhängiges
Optimum, aber „Lage" hieß dort **Merkmalslage**, nicht **Haltedauer**).

## Schritt 4 — erst dann die Bauform

Ob der Hebel eine eigene Quote, eine eigene Schwelle oder einen eigenen
Trichterzweig bekommt, ist **nachrangig**. Es hängt daran, was Schritt 2
ergibt.

---

# § 5 Was das für M1 bedeutet

| | |
|---|---|
| **M1-Kriterium 1** Spot-Einstieg | ✔ **unberührt** — er ist auf seinem eigenen Horizont gemessen |
| **M1-Kriterium 2** Hebel gemessen | ⛔ **nicht erfüllt, und jetzt ist klar warum**: er wurde auf dem Spot-Horizont gemessen |
| Betriebsrisiko | **keines** — M1 ist die Freigabeschwelle, und sie steht nicht |

⚠️⚠️ **Der Befund ist unbequem, aber er ist ein Fortschritt:** bisher hieß
es *„der Hebel trägt nicht"*. Jetzt heißt es *„der Hebel wurde nie auf
seinem eigenen Horizont gemessen"*. Das ist eine beantwortbare Frage.

⚠️ **Und die ehrliche Erwartung:** Schritt 2 kann genauso negativ ausgehen.
Die Beiträge fallen auf kurzen Horizonten stark ab (2.514: `funding` von
2,48 auf 0,23 Punkte, Faktor 11). **Dieses Konzept verspricht keinen
Hebel — es stellt die Frage zum ersten Mal richtig.**
