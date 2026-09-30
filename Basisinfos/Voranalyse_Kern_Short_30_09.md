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

