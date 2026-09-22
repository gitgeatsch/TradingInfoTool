# Voranalyse — Phase 3 nach dem Nennerwechsel (22.09.2026)

> **Nutzerauftrag:** *„ja mach die Voranalyse zu Phase 3"*

⚠️ **Sie entscheidet nichts und baut nichts.** Ist-Stand am Code, offene
Punkte, Risiken — wie `voranalyse-vor-jedem-schritt` es verlangt.

---

## 0. ⚠️⚠️ Die wichtigste Feststellung zuerst: Phase 3 ist fast fertig

Ich hatte Phase 3 als „noch nicht gelaufen" geführt. **Das stimmt nicht.**
Vier von fünf Punkten sind am 18.–20.09. erledigt worden:

| # | Punkt | Stand |
|---|---|---|
| 1 | R-R11: `funding`, `turnover`, `oi_aenderung` reproduzieren | ✔ 18.09. (2.460-repro) — ⚠️ **aber siehe § 1** |
| 2 | Kette gesamt gegen Nullwelten | ✔ 18.09. (2.460-kette): **TRÄGT**, +0,0403 R gegen Nullpunkt +0,0048 |
| 3 | Beitrag je Stufe (auswahl, terminmarkt, entscheider) | ✔ 19.09. vollständig — `entscheider` **+0,2137 R**, `auswahl` trägt nicht |
| 4 | Wiederholungssperre | ✔ 18.09. (2.461): **keine Länge trägt** |
| 5 | Die vier ungemessenen Größen | ✔ 20.09. (2.483): eine messbar, keine trägt |

**Voraussetzung N3 ist entschieden:** *(b) die Bewertung gilt ausdrücklich
nur auf der Stellvertretermenge validiert, mit Kennzeichnung.*

➤ **Was offen ist, ist nicht Phase 3 — es ist EIN Punkt daraus.**

---

## 1. Der eine Punkt: Punkt 1 muss wiederholt werden

Befund **2.460-norm** sagt im Wortlaut:

> *„Normurteil ab 2023: nur `oi_aenderung` trägt einzeln, funding und
> turnover liegen unter ihrer Trennschärfe — **Ursache ist die Datenlage
> (turnover: 59 Symbole)**"*

⚠️⚠️ **Genau diese Ursache ist seit dem 22.09. behoben.** Der Betrieb rechnet
mit **374** Symbolen statt 59.

| | 18.09. | heute |
|---|---|---|
| turnover-Symbole | **59** | **374** |
| Urteil `turnover` einzeln | unter der Trennschärfe | **unbekannt** |
| Urteil `funding` einzeln | unter der Trennschärfe | unverändert zu erwarten |

➤ **Die Messung ist zu wiederholen — nicht nachzuholen.** Das ist ein
Unterschied: es gibt einen registrierten Befund, und der hat Vorrang.

### ⚠️ R-R11 gilt und ist hier unbequem

> *„Ein registrierter Befund darf nur von einer Messung umgestoßen werden,
> die ihn **zuerst reproduziert**. Wer die Basis ändert und ein anderes
> Ergebnis bekommt, hat nichts widerlegt — er hat etwas anderes gemessen."*

Und genau das täte eine Messung auf 374 Symbolen: **sie misst etwas
anderes.** Der Ablauf muss deshalb sein:

```
1.  2.460-norm auf der ALTEN Datenlage reproduzieren   (59 Symbole)
2.  dieselbe Messung auf der NEUEN                     (374 Symbole)
3.  die Differenz ausweisen — und sagen, dass sie aus der DATENLAGE
    kommt, nicht aus einer besseren Größe
```

⚠️ Schritt 3 ist der, den man weglässt, wenn das Ergebnis gefällt.

---

## 2. Ist-Stand am Code — was Phase 3 liest

| Werkzeug | liest | nach dem Umbau |
|---|---|---|
| `n67_schnitt_ueber_die_kette.py` | ⛔ **fest verdrahtet** `MB.reihe("data/onchain_historie.db", "splycur")` (Z. 75) | **misst die ALTE Quelle** |
| `simuliere_kette.py` | setzt die Fünftel als **feste Kunstwerte** (`turnover_fuenftel: 1`) | nicht betroffen — es simuliert Lagen, misst keine Ränge |
| `messnorm_auswahl.zulaessige_mengen` | Momentum-Maske | unverändert ✔ |
| `marktrang.turnover_verfuegbar` | **seit 22.09. die live-Größe** | ✔ liefert 374 |

### ⛔ Das N-67-Muster misst `splycur` — hart kodiert

```python
# n67_schnitt_ueber_die_kette.py:75
"turnover": MB.reihe("data/onchain_historie.db", "splycur")
```

⚠️⚠️ Kein `live_groesse()`, kein `MESSBASIS`, kein Parameter — **der
Dateipfad steht im Quelltext**. Jede Messung auf diesem Muster misst den
abgeschalteten Nenner, und zwar **ohne dass es auffällt**: sie läuft
durch, liefert Zahlen und nennt sie „turnover".

➤ Das ist dieselbe Familie wie `turnover_verfuegbar` in S7 (2.531) —
nur eine Ebene tiefer. **Vor** einer Wiederholung von Punkt 1 zu klären,
sonst wiederholt man die Messung auf genau der Datenlage, wegen der sie
wiederholt wird.

### ⛔ Der Messkopf meldet die falsche Zahl

```
messmenge.zeile()
→ "Messmenge Krypto v1 … Funding 300 · Terminmarkt 122 · Turnover 66"
```

⚠️⚠️ **Jeder Phase-3-Lauf schreibt diesen Kopf über sein Ergebnis.** Er nennt
**66**, der Betrieb rechnet mit **374**. Wer den Kopf liest, hält das
Ergebnis für eine Messung auf 66 Symbolen.

➤ Das ist **kein Fehler der Zahl** — sie ist die Abdeckung der *Messmenge
V1*, und die ist unverändert. Es ist ein **Etikettenproblem**: der Kopf
unterscheidet nicht zwischen Messmenge und Betriebsmenge. **Vor** einem
Phase-3-Lauf zu klären, sonst trägt jedes Ergebnis ein falsches Schild.

---

## 3. Die Grundgesamtheit — der Punkt, der alles andere bestimmt

`marktrang.MESSBASIS["turnover"]` zeigt weiter auf `splycur` (66),
`messmenge.ABDECKUNG["turnover"]` ebenso. Der **Betrieb** rechnet mit dem
freien Umlauf (374).

| | Messung | Betrieb |
|---|---|---|
| Nenner | Gesamtausgabe | **freier Umlauf** |
| Symbole | 66 | **374** |

⚠️⚠️⚠️ **Solange das auseinanderläuft, misst Phase 3 eine andere Kette, als
läuft.** Das ist wörtlich F-212 und 2.410.

➤ **Das ist die eigentliche Vorfrage**, und sie ist eine
Grundgesamtheitsfrage: CLAUDE.md verlangt, die Wirkung zu **messen**
(`phase4_c_fuenftelwechsel_nenner.py`, vier Minuten) und **beide Seiten**
nachzuziehen. Gemessen ist sie bereits (2.525: 59 % der Fünftel wechseln auf
der Betriebsmenge) — **nachgezogen ist nur eine Seite.**

---

## 4. Risiken

| Risiko | Wirkung | Gegenmittel |
|---|---|---|
| ⚠️⚠️ **Messbasis ≠ Betrieb** | Phase 3 misst eine andere Kette | § 3 vor dem Lauf klären |
| ⚠️ **Falscher Messkopf** | jedes Ergebnis trägt „Turnover 66" | § 2 |
| ⚠️ **R-R11 übergangen** | „turnover trägt jetzt" wäre kein Widerruf, sondern eine andere Messung | § 1, Ablauf in drei Schritten |
| ⚠️ **Trennschärfe** | 2.460 nennt 0,02 R und merkt an, sie sei **optimistisch** (2.198) | Positivkontrolle je Lauf, wie im Plan gefordert |
| ⚠️ **Noch keine Signale nach dem Umbau** | die Kette ist live, aber unbeobachtet | den schlanken Export abwarten |

---

## 5. Was der Nutzer entscheiden muss

| # | Frage | meine Empfehlung |
|---|---|---|
| **P1** | Wird `MESSBASIS`/`ABDECKUNG` auf den freien Umlauf nachgezogen? | **ja** — sonst misst Phase 3 dauerhaft an der Kette vorbei. Die Wirkung ist gemessen (2.525), die Entscheidung fehlt |
| **P2** | Wird Punkt 1 wiederholt, oder gilt 2.460-norm weiter? | **wiederholen** — die Ursache des Nullbefunds ist ausdrücklich benannt und behoben |
| **P3** | Bekommt der Messkopf eine Betriebszahl neben der Messzahl? | **ja**, klein und billig — ein falsches Schild kostet später mehr |

---

## 6. Was NICHT Teil von Phase 3 ist

- Der **Hebel** (M1-Kriterium 2, Phase 4)
- Die **Akkumulation** (Kriterium 3)
- Die **LLM-Kette** (Kriterium 4, Phase 8)
- Der **„0 heraus"-Abbruch** und die 130 Tracebacks — eigener Fall

---

## Belege

Befunde **2.460-repro**, **2.460-norm**, **2.460-kette**, **2.461-sperre**,
**2.479-auswahlstufe**, **2.480-entscheiderstufe**, **2.481-terminmarktstufe**,
**2.483-referenz**, **2.525-fuenftelwechsel-gemessen**,
**2.530-s6-nennerwechsel-scharf**, **2.531-s7-dokuabgleich** ·
R-R11, F-212, N3/A8 · Plan Schritt 59 § Phase 3
