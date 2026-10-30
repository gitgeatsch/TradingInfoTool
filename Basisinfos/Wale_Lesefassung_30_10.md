# Wale (G16) – Ergebnisse zum Lesen und Entscheiden

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

*Stand 30.10.2026 · Volltext: `Messplan_Wale_29_10.md` §10 und §13*

## Die Frage in einem Satz

Wenn an einem Tag **große Aufträge** (Sweeps ab 5 % des Tagesumsatzes) netto **kaufen**, und zwar **mehr**, als der übrige Fluss und die Tagesbewegung erklären: Steht der Kurs danach höher als nach Tagen, an denen die Großen netto **verkaufen**?

**D** = Ertrag nach dem obersten Fünftel minus Ertrag nach dem untersten Fünftel, in Prozentpunkten (Pp), brutto. Der Einstieg liegt um 00:00 UTC am Folgetag.

---

## 1. Fassung 1 – 2025/26 (die Jahre, aus denen die Idee kam)

**Spot BTC**

| Horizont | D | Urteil |
|---|---|---|
| 1 Tag | +0,33 | trägt nicht |
| 3 Tage | +0,71 | trägt nicht |
| 7 Tage | +2,08 | nicht trennbar |

- Der Wert ist in **jeder** Teilmenge positiv (Jahre, Schwellen, Verzug), das Band schließt den Nullpunkt aber nicht aus.
- **Futures:** Hier zeigt sich nichts, das Vorzeichen wechselt. Futures sind damit **erledigt**.

## 2. Fassung 3 – ungesehene Jahre 2020–22 (die Bestätigung)

Die Richtung war **vorher** festgelegt, deshalb ist das Band einseitig.

**Spot BTC**

| Horizont | D | Urteil |
|---|---|---|
| **1 Tag** | **+1,26** | **✔ TRÄGT** |
| 3 Tage | +1,36 | nicht trennbar |
| 7 Tage | +0,88 | trägt nicht |

**BTC, 1 Tag, je Jahr**

| 2020 | 2021 | 2022 | 2025 | 2026 |
|---|---|---|---|---|
| +1,75 | +1,05 | +0,99 | +0,43 | +0,21 |

- Der Wert ist **in jedem Jahr positiv, wird aber kleiner.** Wie du sagst, verhalten sich die Epochen verschieden.
- Ein Einstieg erst um 06:00 bringt noch +0,81. Der Vorteil ist also nicht nach Minuten weg.
- **ETH** ist in allen drei Horizonten positiv (+0,66 / +1,99 / +2,26), das Band schließt den Nullpunkt aber nicht aus.
- **SOL:** 1 Tag +0,58, 3 Tage +0,78, **7 Tage −0,75**.

**Urteil nach der Vorab-Regel: nicht bestätigt.** Von acht Punkten fehlt **nur einer**, nämlich dass auch ETH für sich trägt. Diese Regel hatten wir vorher streng festgelegt, und ich weiche sie nachträglich nicht auf.

Die Gegenprobe ist exakt, der Selbsttest bestanden (Fehlalarm 1–4 %).

## 3. Was das heißt (meine Einordnung)

| | |
|---|---|
| ✔ Belegt | Bei **BTC über 1 Tag** sagt der Großfluss am Spotmarkt etwas über den Folgetag. Das ist auf Jahren belegt, die vorher niemand angesehen hat |
| ⚠️ Kleiner geworden | Statt 1–2 Pp (2020–22) sind es heute nur noch 0,2–0,4 Pp. **Allein** ist das kein Handelsgrund |
| ⚠️ Kurz | Über eine Woche zeigt sich kein Vorteil; bei SOL geht er sogar ins Minus |
| Lehre | Wird der übliche Fluss herausgerechnet, sagt der Großfluss mehr als roh. Die Großen sind also mehr als Begleiter der Bewegung |

Passt zur stehenden Regel: **Ein Einzelbeitrag ist schwach, angewendet wird die Kombination.**

---

## 4. Die Entscheidung: Wie geht es weiter?

| | Weg | was passiert | Aufwand |
|---|---|---|---|
| **a (Empfehlung)** | **Als Beitrag zur REGEL0 messen** | Frage: Hebt der Großfluss der letzten 24 h **vor einem REGEL0-Einstieg** auf BTC/ETH/SOL die Trefferquote oder das Potential **dieses** Handels? Das ist eine neue Frage (bedingt auf Einstiege), mit einem Vorab-Messplan wie immer. Trägt es, wird daraus ein Hebel-/Einstiegsbeitrag, der eine Handlung auslöst | Daten liegen vor (stündlich). ~1 Tag Messplan + Messung |
| b | **Nur als Auskunft in die Mail** | „Großfluss gestern: Netto-Kauf, oberstes Fünftel“ als Fakt bei BTC, ohne Auslöser | klein, braucht aber einen täglichen Abrufer am NB (aggTrades BTC, eine Tagesdatei aus dem Binance-Archiv) |
| c | **Parken** | Befund dokumentiert, Daten bleiben liegen, wir prüfen erneut, wenn mehr Daten der neuen Epoche da sind | keiner |

**Warum a:** Nur über a wird aus dem Befund eine **Handlung**, also dein Ziel. b ist Information ohne Handlung („jede Mail eine Handlung“). c verschenkt einen Befund, der gerade auf unabhängigen Jahren getragen hat.

⚠️ **Nicht** zur Wahl steht, die ETH-Bedingung jetzt zu lockern. Das wäre eine Regel, die wir nach dem Ergebnis wählen.

**Deine Antwort genügt so:** „Wale a“ (oder b oder c).

---

## 5. RÜCKSPRACHE: Weg a ist auf dem Kern allein nicht messbar (Voranalyse 30.10. abends)

*Du hast gesagt: „Wale a, wenn sinnvoll, sonst Rücksprache“. Die Voranalyse sagt: so nicht sinnvoll.*

| | |
|---|---|
| REGEL0-Einstiege BTC/ETH/SOL 2024–26 | nur **276** (BTC 95, ETH 91, SOL 90), also je Fünftel rund **55** |
| Streuung über 24 h | BTC 2,4 %, ETH 3,5 %, SOL 4,1 % |
| Was die Messung sicher findet | ab etwa **1,6 Pp** Unterschied, mit Tagesklumpen eher mehr |
| Was zu erwarten ist | heute **0,2–0,4 Pp** (Fassung 3, BTC 2025/26) |
| Fundquote | rund **10 %**. Ein „trägt nicht“ wäre das **erwartete** Ergebnis und kein Beleg gegen den Effekt |

Die Großfluss-Daten liegen nur für BTC/ETH/SOL vor. Die übrigen ~10.000 REGEL0-Einstiege fallen auf Altcoins, und für die haben wir keine Wal-Daten.

**Die Wege, die bleiben:**

| | Weg | was | Aufwand |
|---|---|---|---|
| **a2 (Empfehlung)** | **Vorprüfung auf Altcoins** | Fassung 3 unbedingt auf **5–6 liquiden REGEL0-Altcoins** (2024–26) rechnen. Trägt es dort auch, lohnt der große Schritt: Wal-Daten für alle REGEL0-Assets laden, dann Beitrag zur REGEL0 auf ~10.000 Einstiegen (dort findet die Messung ~0,4 Pp) | Download vorher messen und dir vorlegen (geschätzt einige 10 GB) |
| b | Nur Auskunft in der Mail | wie oben | klein |
| c | Parken | dokumentiert, Daten bleiben liegen | keiner |

**Warum a2:** Es ist der einzige Weg, auf dem aus dem Befund noch eine **Handlung** werden kann, also ein Beitrag zur REGEL0. Er ist **gestuft**: zuerst die kleine Prüfung, ob der Effekt außerhalb von BTC überhaupt existiert. ⚠️ Fassung 3 spricht eher dagegen (ETH schwächer, SOL über 7 Tage negativ). Ein „nein“ ist also gut möglich, und dann wäre **c** ehrlich.

**Antwort genügt so:** „Wale a2“ (oder b oder c).

---

## Nachtrag 30.10. abends — Ergebnis Weg a2 (Volltext: Messplan §14–§15)

**Frage:** Gibt es den Wal-Effekt auch außerhalb von BTC? Geprüft auf sechs Altcoins (BNB, ADA, TRX, AVAX, LINK, NEAR), Spot,
2024-01 bis 2026-09. Die Regel stand vor jedem Wert fest.

**Antwort: Ja, über einen Tag, aber knapp.**

| | |
|---|---|
| Tage mit stärkstem Großkauf gegen Tage mit stärkstem Großverkauf | **+0,35 Pp** am Folgetag (brutto, Mittel der sechs) |
| Zufallsprobe (Permutationstest) | p **0,034**, Schwelle 5 % ✔ |
| Werte positiv | 5 von 6 (BNB ±0) |
| Jahre | 2024 +0,10 · 2025 +0,42 · 2026 +0,45 |
| über 3 / 7 Tage | **kein** Beleg |

⚠️ **Hängt an AVAX:** Ohne AVAX liegt p bei 0,12. Ohne ADA, TRX oder LINK liegt p jeweils bei etwa 0,06.

**Was daraus folgt (deine Vorgabe):** Laut Vorab-Regel ist das jetzt **Stufe 2**, ein eigener Messplan mit der Frage, ob der
Wal-Fluss **REGEL0 verbessert**, ohne sie irgendwo zu verschlechtern. Er wäre dort ein Gewicht, kein Auslöser. Gelingt das nicht,
geht er als Befund ins **Dashboard** zur LLM-Bewertung.
