# Voranalyse KERN-SHORT (W3) — der Kern gespiegelt, Schritt 1: der Einstieg (30.09.2026)

**Auftrag (Nutzer 30.09.):** *„Ja, in Doku, Plan, Ergebnis und Zentraldokumente übernehmen"* (zur Voranalyse Kern-Short),
vorher *„gute Idee mit Short-Kern — bitte abgrenzen zur Short-Strategie Krypto, damit keine Verwechslung passiert"*.
**Vorher:** 2.688 (Kern Schritt 1), 2.694 (Verlust im Gegenwind, Juli–Dezember 2025), 2.695 (die Effekte drehen mit dem Regime).

> **Urteil in einer Zeile:** Wir messen den **Kern spiegelbildlich**: nach 48 h Ruhe das erste **Unterschreiten**, Einstieg
> short, gewählt auf 2024 und einmal bestätigt, genau wie 2.688. Heute nur **Schritt 1**, den Einstieg, neutral, ohne Kosten.

---

## 0. Abgrenzung — damit nichts verwechselt wird (E-32)

| Begriff | was | berührt? |
|---|---|---|
| ⭐ **Kern-Short** (W3) | ein **Messarm** im Hebel-Neubau, Phase 1, Test | – |
| SHORT-Signale im **Betrieb** (heutige Krypto-Kette, alter Hebelarm) | Mail mit Richtung LONG/SHORT | ⛔ **nein**, der Betrieb wird erst nach der ganzen Kette umgestellt |
| **Absicherung** mit Short-Produkten | Portfolioschutz (`agent/absicherung_fakten.py`) | ⛔ **nein** |

---

## 1. Ziel, Stand, was es fürs Ziel bringt

| | |
|---|---|
| **Ziel** | Das System soll in **beiden** Regimen eine begründete Aussage liefern. Im Gegenwind zeigt der Long-Kern kaum etwas, der Kern-Short soll dort arbeiten |
| **Stand** | Long-Kern + Ruhe 48 h trägt (2.692). Die Verluste sitzen im Gegenwind (Juli–Dezember 2025: ×0,56..×0,80, 2.694), und alle Kippeffekte drehen zwischen 2025 und 2026 (2.695) |
| **Test oder Betrieb** | nur **Test**, Ebene A (neutral) |
| **fürs Ziel** | Trägt der Kern-Short, gibt es für **jedes** Regime einen belegten Einstieg, **ohne** das Regime vorher erkennen zu müssen. Das ist nicht möglich (2.599), und das Wetter als Gewicht ist nicht nachweisbar (2.686). Beide Arme laufen **immer**, und jeder meldet nur, wenn **sein** Ereignis eintritt |
| ⚠️ Erwartung | offen. rsi misst **Fortsetzung** (2.684). Ein Fall nach Ruhe ist fachlich dasselbe wie ein Anstieg nach Ruhe, nur gespiegelt. Kryptomärkte fallen aber anders (schneller, mit Liquidationskaskaden), und 2024 als Wahljahr war ein **Bullenjahr** mit wenigen Short-Lagen |

---

## 2. Der Aufbau — Spiegel von 2.688, nichts Neues erfunden

| | Long-Kern (2.688/2.692) | **Kern-Short** |
|---|---|---|
| Signal | erste Stunde mit Vorsprung v̂ **≥ +s** | erste Stunde mit v̂ **≤ −s** |
| Ruhe davor | 48 h **unter** +s (≥ 40 gültige Stunden) | 48 h **über** −s (≥ 40 gültige Stunden) |
| Einstieg | 1 h später | 1 h später |
| Monatsanfang | nicht in den ersten 24 h | gleich |
| Ereignis (Chance) | **+5 % vor −5 %** binnen 24 h (q5) | **−5 % vor +5 %** binnen 24 h (Spiegel von q5) |
| Maß | Dq gegen das geschrumpfte Normal | dasselbe, gespiegelt: Dq_short = −Dq auf den Short-Einstiegen |
| Modell | rollierendes rsi-Modell je Monat, nur Vergangenheit | **dasselbe** Modell, dasselbe v̂. Nur Vorzeichen und Seite wechseln |

**Schwelle per Regel** (wie 2.688, E-24): Raster s = 0,010..0,050 in Schritten von 0,005, auf **2024**, gewählt wird der größte
Abstand *echt − P90 Nullwelt*, bei Gleichstand (< 0,005) die niedrigere Stufe. ⚠️ **Nicht** die Long-Schwelle +0,035
übernehmen, denn der Short kann eine andere brauchen, und das wird gemessen.

---

## 3. Die Kriterien der Bestätigung (einmal 2025-01..2026-08, 4 Mengen) — B1–B6 wie 2.688, dazu der Spiegel

| # | Kriterium |
|---|---|
| **B1** | Short-Dq > 0 in **2025 und 2026** |
| **B2** | über dem **P90 der Nullwelt** (rollierende Modelle auf verschobenem rsi je Asset, 40 Ziehungen) |
| **B3** | B1 und B2 in **≥ 3 von 4** Mengen. Laufen bestand und unverzerrt auseinander, gilt unverzerrt (E-30) |
| **B4** | **je Asset** ≥ 60 % mit Dq > 0 (Assets mit ≥ 20 Einstiegen) |
| **B5** | mit/ohne 10./11.10.2025 ausgewiesen (Black Swan nur als Störfaktor) |
| **B6** | **Tagesblock**-Bootstrap, untere Grenze > 0 |
| **B7** ⭐ | **Spiegel** (E-29): Zuwachs *−5 % binnen 24 h* minus Zuwachs *+5 % binnen 24 h* gegen alle Stunden der Menge, > 0 in **2025 und 2026** |
| Pflichtauskunft | **Halbjahre** (das zweite Halbjahr 2025 ausdrücklich) und die **Überlappung** mit dem Long-Kern (wie oft beide Arme in derselben Woche melden) |

➤ Alle erfüllt → **Schritt 2** (H0: das Liquidationsrisiko short steigt mit dem **Markpreis-Hoch**, die ATR-Tabelle muss dafür
**gespiegelt geprüft** werden, eigene Voranalyse) und **Schritt 3** Simulation. Sonst: Lösung suchen (E-25), nicht *widerlegt*.

---

## 4. Prüfung und Gegenprüfung

| Prüfung | wie |
|---|---|
| **R-R11** | Das Werkzeug rechnet den **Long-Kern** im selben Lauf mit und muss 2.688/2.692 bitgleich treffen (Einstiege, Dq). So ist gesichert, dass nur das Vorzeichen wechselt |
| **Nullwelt** | wie 2.688, rollierende Modelle auf verschobenem rsi je Asset |
| **Zeitstabilität** | 2025 und 2026, dazu die Halbjahre |
| **Weglassprobe** | Short gegen den **Zustand** *v̂ unter −s* (ohne Ersteintritt) und gegen zufällige Short-Einstiege |
| **Mehrfachtesten** | 9 Stufen nur auf 2024, ein Urteil auf 2025–26 |
| **Je Asset** | B4 |
| **Spiegel** | B7 |
| **Ebene** | A, neutral, ohne Kosten. Ob und wie short bei Bitpanda **handelbar** ist, ist eine Frage für Phase 4 |
| ⚠️ **v̂-Skala** (E-31) | Die Short-Schwelle liegt am **unteren** Ende von v̂, genau dort, wo die Skala je Menge wandert (2.695). Darum wird die Schwelle **je Menge** aus deren 2024 bestimmt (dieselbe Regel) **und** die bestand-Schwelle zum Vergleich ausgewiesen. Urteil auf der Regel **je Menge** |

---

## 5. Umfang

Werkzeug `messe_losfahren.py --kern --short` (Spiegel im bestehenden Kern-Pfad) → Funktionstest → **Commit** → Wahl 2024 je
Menge (etwa 4 × 8 Minuten, wegen E-31) → **Stopp und Bericht** → Bestätigung (4 × etwa 8 Minuten).

---

## 6. Zur Abstimmung (S1–S5)

| # | Vorschlag |
|---|---|
| **S1** | der Kern **spiegelbildlich** (Abschnitt 2), dasselbe Modell, Ruhe 48 h, Einstieg 1 h später |
| **S2** | Schwelle **per Regel** auf 2024, **je Menge** (E-31), bestand-Schwelle als Vergleich |
| **S3** | Bestätigung B1–B7, einmal, ≥ 3/4 Mengen, Urteil auf unverzerrt, wenn es auseinanderläuft |
| **S4** | Pflichtauskunft Halbjahre und Überlappung mit dem Long-Kern |
| **S5** | Schritt 2 (H0 short) und Schritt 3 (Simulation) erst nach bestandenem Schritt 1, je mit eigener Voranalyse |

---

## 7. ✔ ABGESTIMMT (30.09.2026) — S1 bis S5, Umsetzung VOR dem Lauf

**Nutzer:** *„Ja, wie vorgeschlagen durchführen, prüfen und gegenprüfen."*

- Werkzeug `messe_losfahren.py --kern --short --ruhe 48`, ohne `--bestaetigen` die Wahl 2024, mit `--bestaetigen <s>` einmal 2025–26.
- Der Spiegel steckt in `erst_v` (v̂ ≤ −s) und `dqh` (Ereignis *−5 % vor +5 %*, Normal vertauscht, also genau −Dq). Ohne `--short` ist alles unverändert.
- **R-R11:** Der Long-Kern wird im selben Lauf mitgerechnet (Ruhe 48 h, s +0,035).
- Funktionstest der Wahl technisch sauber (`Kern_Short_30_09/probe_wahl__bestand.txt`, Inhalt nicht gewertet). Die
  **Bestätigung** lässt sich in der Probe nicht testen, weil die verkürzten Monate kein 2025–26 haben. Bei `--kern
  --bestaetigen` ist das genauso. Ein Probelauf auf echtem 2025–26 hieße, die ungesehenen Daten vorab anzusehen. Der neue Teil
  (B7, Halbjahre, Überlappung) ist deshalb nur gegengelesen. Bricht er ab, wird er behoben und neu gestartet, ohne Blick auf die
  Ergebnisse.
- **Wahl je Menge** (E-31): 4 Läufe, danach Stopp und Bericht.

---

## 8. ERGEBNIS WAHL 2024 je Menge — Stopp, zur Abstimmung

Belege `Kern_Short_30_09/wahl__<menge>.txt`. ✔ **R-R11:** Long-Kern im selben Lauf bestand 1.486 / +0,1615, bitgleich (unverzerrt
1.382 / 1.255 / 1.246, je +0,171..+0,172).

| Menge | nach der Regel gewählt | dort: Einstiege / Tage | echt | Null-P90 | Abstand | übrige Stufen |
|---|---|---|---|---|---|---|
| bestand | s = 0,050 | **28 / 8** | +0,238 | +0,117 | +0,121 | alle anderen Abstände **negativ** außer 0,030 (+0,009) |
| unverzerrt:1 | s = 0,045 | 206 / 25 | −0,018 | −0,035 | +0,017 | sonst negativ |
| unverzerrt:2 | s = 0,015 | 1.250 / 125 | +0,043 | +0,059 | **−0,016** | **alle negativ**, die Regel nimmt den am wenigsten schlechten |
| unverzerrt:3 | s = 0,035 | 880 / 74 | −0,078 | −0,085 | +0,007 | sonst negativ |

➤ **Urteil der Wahl:** Der Kern-Short hat **2024 in keiner Menge ein Signal über der Nullwelt**. Die gewählten Stufen streuen von 0,015
bis 0,050, und das ist das Zeichen, dass die Regel im Rauschen wählt. In bestand trifft sie eine Stufe mit **28 Einstiegen an 8 Tagen**.

⚠️ **Gegenprüfung:**
1. Die Regel hat **keine Mindestzahl**. In 2.688 war das kein Problem, weil dort ein klares Signal vorlag. Hier greift sie ins Leere.
2. **2024 ist ein Bullenjahr.** Short-Einstiege nach einem Fall aus der Ruhe schneiden fast überall **schlechter** ab als das Normal
   (echt −0,03..−0,20). Nach dem Fall erholt sich der Kurs eher. Genau das Regime, für das der Kern-Short gedacht ist (Gegenwind),
   kommt im Wahljahr kaum vor.
3. Auch die Nullwelt ist auf den hohen Stufen negativ (−0,08..−0,11). Short gegen das Normal lag 2024 **strukturell** im Minus.

**Lösungsvorschläge (Lösungspflicht, E-25) — zur Abstimmung, VOR jedem Blick auf 2025–26:**

| # | Weg | Bewertung |
|---|---|---|
| **K1** ⭐ | **Symmetrie** statt Wahl: Bestätigung einmal mit der **gespiegelten Long-Schwelle s = 0,035**, für alle Mengen gleich, als vorab festgelegte Annahme (keine datengetriebene Wahl). Die je Menge gewählten Stufen laufen als Auskunft mit. B1–B7 unverändert | sauber, weil nichts aus 2025–26 gewählt wird. Die Annahme *derselbe Signalabstand in beide Richtungen* ist fachlich die einfachste |
| K2 | Bestätigung wie festgelegt mit den gewählten Stufen je Menge | formal korrekt, aber die Stufen sind Rauschen. Ein *bestanden* wäre Glück, ein *gefallen* sagt wenig |
| K3 | Kern-Short **zurückstellen**, weiter mit W4 | verschenkt die Frage, ob der Short im Gegenwind trägt |

⚠️ **B1** verlangt Dq > 0 in **2025 und 2026**. Ein Arm, der nur im Gegenwind trägt, fällt daran. Das ist gewollt: Ein echtes
Signal muss auch im anderen Regime wenigstens nicht **schaden**, und genau das hat der Long-Kern geschafft (2.688).

**✔ ABGESTIMMT (30.09.2026): K1.** Nutzer: *„Ok, ja, starten, prüfen und gegenprüfen."* Die Bestätigung läuft einmal mit **s = 0,035**
(Symmetrie) in allen 4 Mengen, mit den Kriterien B1–B7 wie Abschnitt 3. Aufruf `--kern --short --ruhe 48 --bestaetigen 0.035`,
davor keinerlei Blick auf 2025–26. Die je Menge gewählten Stufen (0,050 / 0,045 / 0,015 / 0,035) sind nur Auskunft. Die Stufe
0,035 in unverzerrt:3 ist dabei ohnehin dieselbe.


---

## 9. ERGEBNIS BESTÄTIGUNG (K1, s = 0,035, 4 Mengen) und DIAGNOSE — Befund 2.696

Belege `Kern_Short_30_09/best__<menge>.txt`, Diagnose `diag__bestand.txt`.

| | bestand | unv:1 | unv:2 | unv:3 | Urteil |
|---|---|---|---|---|---|
| R-R11 Long-Kern im selben Lauf | ✔ 6.328 / +0,1039 | 7.121 / +0,077 | 6.463 / +0,070 | 6.782 / +0,078 | ✔ |
| Short-Einstiege / Dq gesamt | 4.174 / +0,030 | 6.286 / +0,040 | 5.763 / +0,034 | 5.794 / +0,033 | |
| B1 2025 / 2026 | ✔ +0,022 / +0,046 | ✔ +0,045 / +0,031 | ⛔ +0,054 / −0,010 | ⛔ +0,049 / −0,007 | 2/4 |
| B2 Nullwelt P90 | ✔ −0,014 | ✔ −0,006 | ✔ −0,005 | ✔ −0,015 | **4/4** |
| B4 je Asset | ⛔ 58 % | ✔ 64 % | ⛔ 58 % | ✔ 65 % | 2/4 |
| **B6** Tagesblock untere Grenze | ⛔ −0,048 | ⛔ −0,021 | ⛔ −0,029 | ⛔ −0,027 | **0/4** |
| **B7 Spiegel** 2025 / 2026 | ✔ +0,017 / +0,077 | ✔ +0,033 / +0,067 | ✔ +0,043 / +0,032 | ✔ +0,042 / +0,035 | **4/4** |
| Halbjahre (H1 / H2 2025 · H1 / H2 2026) | +0,06 / −0,08 · +0,06 / −0,02 | +0,09 / −0,01 · +0,09 / −0,15 | +0,10 / −0,01 · +0,04 / −0,12 | +0,08 / +0,01 · +0,03 / −0,10 | H1 positiv, H2 negativ |
| Überlappung mit dem Long-Kern (Asset und Woche) | 71 % | 74 % | 75 % | 75 % | die Arme melden meist in denselben Wochen |

➤ **Schritt 1 NICHT bestanden** (B6 0/4). Es ist aber ein **echtes Richtungssignal**: B2 und **B7** sind in 4/4 Mengen erfüllt,
unten wird es mehr und oben weniger. Das ist das Gegenteil der Wucht (2.693).

**DIAGNOSE — warum Monate leer sind (nachgemessen, nur das Signal, bitgleich zum Kettenlauf):**

| Monat (bestand) | Anteil v̂ ≤ −0,035 | P1 / P99 von v̂ | Short / Long |
|---|---|---|---|
| 2025-01..04, 06..08 | 4–17 % | ≈ −0,045 / +0,07..+0,10 | 288–395 / 221–427 |
| **2025-05** | **0 %** | −0,026 / +0,039 | **1** / 258 |
| **2025-09..2026-01** | **0 %** | −0,020..−0,026 / +0,032..+0,040 | **0** / 51–318 |
| 2026-02..04, 07 | 3–13 % | ≈ −0,04 / +0,07 | 357–522 / 380–464 |
| **2026-05, 06, 08** | **0 %** | −0,021..−0,034 / +0,05..+0,07 | **0–2** / 423–472 |

➤ Das monatlich geschätzte rsi-Modell ist in **8 von 20 Monaten fast flach**, in **beide** Richtungen. Dann kann der Short nicht
auslösen, und der Long nur mit extremem rsi (Januar 2026: 51 Einstiege). Das trifft genau den **Gegenwind** September 2025 bis
Januar 2026.

⭐ **Einordnung:** Das Modell sagt in diesen Monaten selbst, dass rsi **gerade keine Information** trägt. Das erklärt die
**Regimeabhängigkeit** des Kerns (2.688, 2.694) **mechanisch**. Im Gegenwind fehlt der Kurs-Fortsetzung die Aussagekraft, und kein
Filter auf rsi kann das beheben. ⚠️ Dass die **Dämpfung** der Kreuzvalidierung (λ bis 20.000) die Flachheit verursacht, ist
plausibel, aber **nicht nachgemessen**.

**Lösungsvorschläge (E-25), zur Abstimmung:**

| # | Weg | Bewertung |
|---|---|---|
| **M1** ⭐ | **Modell-Aussagekraft als Kontext**: die Spannweite von v̂ im Monat (vorab bekannt, weil das Modell aus der Vergangenheit geschätzt ist, und für alle Assets gleich, also *Kontext* nach E-20). Hypothese: Long-Einstiege in flachen Monaten sind schlechter, dort wird nicht gehandelt. **Schritt 0:** nur die v̂-Verteilung 2024 ansehen, ob es dort überhaupt flache Monate gibt (ohne Ergebnisse). Sonst ist eine Wahl auf 2024 unmöglich | mechanisch begründet und direkt am Verlust. ⚠️ Wenige Regimewechsel (wie das Wetter, 2.686), und 2025–26 ist schon gesehen |
| M2 | Kern-Short als **Spur** festhalten (B2/B7 4/4) und mit M1 später erneut prüfen | kostet nichts |
| M3 | **W4** Positionsführung (Erfolgsmessung) | offen, unabhängig davon |

---

## 10. M1 SCHRITT 0 — v̂ je Monat 2024 (nur das Signal, keine Ergebnisse)

Nutzer: *„Ja, prüfen. Jetzt sollten wir nachdenken und fachlich vorgehen. Diese zum Teil langen Schwächephasen sind in diesem Markt
gegeben, und wir müssen u. U. zwischen Regime und kürzeren Wetterwechseln, also Trendumkehr, unterscheiden können."*

Beleg `Kern_Short_30_09/m1_schritt0__bestand.txt`:

| 2024 | Spannweite P99−P1 von v̂ | Anteil v̂ ≥ +0,035 |
|---|---|---|
| Jan, Mär, Mai, Sep, Okt, Nov, Dez | 0,087–0,094 (**normal**) | 4,6–26,9 % |
| **Feb, Apr, Jun, Jul, Aug** | **0,003–0,033 (flach)**, August fast null | **0 %**: dort **kein einziger** Kern-Einstieg |

**Befund Schritt 0:**
1. 2024 hat flache Monate (5 von 12), eine Wahl auf 2024 wäre also **möglich**.
2. ⚠️ Die Flachheit **springt** 2024 von Monat zu Monat (Feb flach, Mär normal, Apr flach, Mai normal, Jun bis Aug flach, Sep normal). Die
   Spannweite ist **zweigeteilt** (≈ 0,09 oder ≤ 0,03), dazwischen fast nichts. Das passt zu einer **Schätzergröße** und nicht zu einem
   Marktzustand: Die Dämpfung wird je Monat aus nur **4 Stufen** (λ 20 / 200 / 2.000 / 20.000) über **4 Kreuzvalidierungsblöcke**
   gewählt. Kippt die Wahl eine Stufe, wird das Modell flach oder voll.
3. 2025–26 dagegen: **September 2025 bis Januar 2026 fünf Monate am Stück** flach. Das ist **anhaltend** und passt zu einem Regime.
4. In voll flachen Monaten schaltet sich der Kern **selbst ab** (2024: 0 Einstiege). In halbflachen Monaten (2025-09: P99 +0,040)
   gibt es noch Einstiege, und genau dort ist offen, ob sie schlechter sind.

➤ **Folge:** Bevor die Flachheit ein Kontext wird, muss klar sein, **was** sie misst, echtes Fehlen von Information oder das
Springen der Dämpfungswahl. Das ist messbar: λ und Validierungsverlust je Monat protokollieren (ohne Ergebnisse). Vorschlag M1 Schritt 1.

---

## 11. M1-1 — die Dämpfung je Monat (nur das Modell, keine Ergebnisse)

Nutzer: *„Ja, deine Auslegung teile ich, prüfen und gegenprüfen."* Beleg `Kern_Short_30_09/m1_1__bestand.txt`. ✔ **R-R11:** Die
Schritt-0-Tabelle 2024 ist bitgleich, die K5-0-Auswahl liegt bei 29.390. Das Mitschreiben ändert nichts.
⚠️ Korrektur: Die Dämpfung wird aus **6** Stufen gewählt (`GITTER_NEU`: 20 bis 2.000.000), nicht aus 4 wie in Abschnitt 10 und in der Ausgabe
zunächst beschriftet. Die Beschriftung ist korrigiert, die Zahlen sind unverändert.

| Monate | gewählt | Abstand zur zweitbesten Stufe (Verlust) | Informationsgewinn je 1.000 Anker (flach minus bester) |
|---|---|---|---|
| 2024 Feb, Apr, Jun, Jul | 20.000 | **1,9–6,9 (knapp)** | 0,07–0,30 |
| 2024 Aug | 200.000 | **0,1** | 0,002 |
| 2024 Jan, Mär, Mai, Sep–Dez | 2.000 | 2,4–18,2 | 0,43–1,01 |
| 2025 Jan–Apr, Jun–Aug | 2.000 | 5,6–27,3 | 0,92–**2,49** |
| **2025-05, 2025-09, 2026-01, 2026-08** | 20.000 | **2,5–7,8 (knapp)** | 0,86–1,10 |
| **2025-10, 11, 12** | 20.000 | **18,2–48,6 (deutlich)** | **0,60–0,82** |
| 2026 Feb–Jul | 2.000 | 11,9–26,4 | 1,40–1,50 |

**Befund M1-1:**
1. **Beides ist wahr.** In vielen flachen Monaten ist die Wahl **knapp**: Die Stufen 2.000 und 20.000 liegen fast gleichauf, und die
   Flachheit ist dann ein **Kippen des Schätzers**. Das gilt für 2024 fast überall sowie für Mai und September 2025, Januar 2026 und August 2026.
   Im Kern des Gegenwinds, **Oktober bis Dezember 2025**, ist sie dagegen **deutlich**. Dort trägt rsi nach dem Modell wirklich keine
   verallgemeinerbare Information.
2. Das grobe Stufenraster (Faktor 10) macht aus kleinen Unterschieden **große Sprünge** in der Spannweite (0,47 gegen 0,24). Das
   Signalangebot des Kerns springt dadurch von Monat zu Monat. Das ist eine **Schwäche des Kerns selbst** und für den Betrieb wichtig.
3. ⭐ Der **Informationsgewinn** (wie viel besser das rsi-Modell ist als ein flaches) ist ein **stetiges** Maß und springt nicht. Er ist
   **vorab bekannt**, weil nur Vergangenheit in das Training geht, und für alle Assets gleich, also *Kontext* nach E-20. Er fällt genau im Gegenwind:
   0,60–0,93 gegen 1,4–2,5 sonst in 2025–26. 2024 streut er breit (0,002–1,01). Das ist eine Voraussetzung für eine Wahl auf 2024.
4. ⚠️ Der Short fehlt 2026-05/06 auch **ohne** Dämpfung (Stufe 2.000, Spannweite normal). Dort ist die rsi-Kurve **einseitig**, unten
   flach und oben nicht. Das ist ein zweiter Grund und betrifft nur den Short.
5. ⚠️ Das Training wächst ab 2023 (keine rollierenden 12 Monate). Der Informationsgewinn ist deshalb **träge** und reagiert
   **verspätet** auf ein neues Regime.

➤ **Folge:** Als **Regime-Messgerät** eignet sich der stetige **Informationsgewinn** und nicht die sprunghafte Stufenwahl. Getrennt
davon ist die Stabilität des Kerns eine eigene Aufgabe: ein feineres Raster oder eine über Monate geglättete Dämpfung.

