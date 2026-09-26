# Der Ende-zu-Ende-Test — die Bewertung läuft in die falsche Richtung

**26.09.2026** · Befunde 2.624, 2.625 ·
`messe_endetest_out_of_sample.py` · Vorabfestlegung 23

> **Nutzerauftrag:** *„vor der Verdrahtung hätte ich gerne einen
> ausführlichen Test ob unsere Bewertungen, Kalibrierung, bei echten Daten
> auch das Ergebnis liefert dass es soll"*

**Der Test hat geliefert, wofür er gebaut wurde: er hat eine Verdrahtung
verhindert, die in die falsche Richtung gelaufen wäre.**

---

## ⛔ Der Auslöser: ein Standardverstoß in meinem eigenen Test

Nach dem Nutzerhinweis *„halte dich an unser Regelwerk und Messstandards"*
geprüft — und gefunden:

```python
# messnorm.py:590
raise ValueError("nur die Tagesklammer ist zulaessig (31.08.)")
# messnorm.py:454
gepoolt statt Tagesklammer  ->  12,4 Punkte auf einem Nulleffekt
```

**Meine Nullwelt zog Anker frei**, der Standard verlangt **Ränge je Tag
gemischt**. Echte Signale häufen sich an wenigen Tagen (Median 10/Tag,
Maximum 620), freie Zufallsziehungen nicht — **das Nullband war zu eng**.

✔ **Die Gegenprüfung zeigt, dass der Vergleich aussagefähig ist:** Signale
machen im Median nur **0,6 %** des Tagespools aus, an keinem Tag über
50 %. Die Nullwelt hat genug Auswahl.

---

## ⛔⛔⛔ R-R11: 2.608 reproduziert — und es fällt

Dieselbe Menge, dieselbe Geometrie, **nur die Nullwelt korrigiert**:

```
3181434 Anker — 2.608 hatte 3.181.434  ✔ reproduziert
```

| Schwelle | gemessen | Null **gepoolt** | Null **tagestreu** | |
|---|---|---|---|---|
| 0,5 | +0,1172 | −0,0348 ✔ | **+0,9898** | ⛔ |
| 0,7 | +0,4198 | −0,0320 ✔ | **+1,4457** | ⛔ |
| 0,9 | +0,6628 | +0,0002 ✔ | **+1,8113** | ⛔ |
| **1,0** | **+0,6611** | +0,0320 ✔ | **+1,9243** | ⛔ |
| 1,2 | +0,5640 | +0,0398 ✔ | **+1,9784** | ⛔ |

**Gepoolt: 5 von 6 tragen. Tagestreu: 0 von 6.**

➤ **An denselben Tagen hätte eine Zufallsauswahl +1,92 % gebracht — die
Bewertung bringt +0,66 %.**

---

## ⛔⛔⛔ Die Ursache: die Achse ist invertiert

Ertrag **relativ zum eigenen Tag**, über die ganze Merkmalsachse:

| `ema_abstand_atr` | Anker | roh | **relativ zum Tag** |
|---|---|---|---|
| **unter −0,74** | 159.072 | +0,0017 | **+1,3143** |
| −0,74 bis −0,38 | 477.215 | +0,0272 | **+0,6888** |
| −0,38 bis −0,14 | 636.287 | −0,0068 | +0,2759 |
| −0,14 bis 0,07 | 636.286 | −0,0933 | −0,0517 |
| 0,07 bis 0,30 | 636.287 | −0,1152 | −0,3415 |
| 0,30 bis 0,62 | 477.215 | −0,2164 | −0,6560 |
| **über 0,62** | 159.072 | +0,3284 | **−0,9437** |

**Perfekt monoton, Spanne 2,25 Prozentpunkte — mit umgekehrtem
Vorzeichen.**

⛔ Die Bewertung wählt `≥ 1,0` — **die schlechteste Gruppe**. Die beste sind
Assets **weit unter** ihrem EMA.

### Damit erklärt sich jede Zahl der Messreihe

| Beobachtung | Erklärung |
|---|---|
| roh positiv (+0,66 %) | diese Anker treten an **guten Tagen** auf |
| tagestreu −12 bis −22× Trennschärfe | am selben Tag ist fast jedes andere Asset besser |
| `q` trifft out-of-sample nicht (8 von 20) | die Tabelle beschreibt den **Markttag**, nicht das Asset |
| Differenzierung 1 von 4 | keine nutzbare Stufung in der falschen Richtung |
| Kelly-Maximum bei Band 1,1–1,3 | ein Artefakt der Tageshäufung |

⚠️⚠️ **Die Bewertung ist ein Markt-Timing-Indikator, kein Asset-Selektor.**
Sie erkennt gute Tage und greift dort nach dem schlechtesten Wert.

---

## ⭐⭐ Die Nutzerklarstellung, die den methodischen Konflikt löst

> *„Dass wenn sich btc bewegt und der gesamte Markt reagiert ist klar, dass
> eine Verschiebung erfolgt … **na und dann darf nur das asset mit den
> besten werten gewinnen** (Qualität, Regelwerk, Kalibrierung, etc.)"*

Ich hatte einen Konflikt gesehen: der **Messstandard** verlangt die
Tagesklammer, die **Nutzervorgabe vom selben Tag** nennt die Tageshäufung
erwartetes Verhalten (*„an sehr guten Tagen kommen auch mehr Signale"*).

✔ **Beides gilt, und es widerspricht sich nicht:**

| | |
|---|---|
| Die **Tageshäufung** ist erwartet — mehr Signale an guten Tagen, keine im Bärenmarkt | **Beobachtung** |
| Die **Auswahl** muss *innerhalb* des Tages gewinnen — nur das beste Asset | **Anforderung** |

➤ **Die tagesrelative Messung ist damit nicht nur Standard, sondern die
fachlich richtige Frage.** Genau sie fällt heute aus.

---

## Was daraus folgt

| # | |
|---|---|
| **1** | ⛔ **2.608 ist widerlegt** — reproduziert und mit korrigiertem Prüfstand gefallen. Damit fallen auch die darauf aufbauenden Aussagen zur Schwellenhöhe |
| **2** | ⛔ **2.622 (`q`) ist hinfällig**, weil sein Eingang die falsche Achse war |
| **3** | ⭐ **Die Ordnung existiert** — sie ist monoton, stark (2,25 Pp) und zeigt in die **andere** Richtung |
| **4** | ✔ **Die Geometrie (2.620) ist davon unberührt** — Horizont, Stop und Trailing sind unabhängig von der Auswahlrichtung gemessen |
| **5** | ✔ **Der Prüfstand ist geeicht** — Positivkontrolle 5 von 5 in allen Fenstern |

## Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Die invertierte Achse ist KEIN neuer Befund** — sie ist eine Beobachtung auf derselben Menge, in-sample, und verdient dieselbe Skepsis wie die gefallene. Out-of-sample und je Asset **ungeprüft** |
| **2** | „Relativ zum eigenen Tag" ist **nicht unmittelbar handelbar** — man kauft absolut. Ob die Ordnung im Betrieb nutzbar ist, ist offen |
| **3** | Die **Hebelhöhe** bleibt ohne Grundlage (2.609, 2.621) |
| **4** | Nichts über **Short** |
