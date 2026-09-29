# Voranalyse — die KERNMESSUNG: trägt der Kern aus rsi-Einstieg und ATR-Hebel? (29.09.2026)

**Nutzer:** *„ja, Kern zuerst — prüfen und gegenprüfen. Die Kernmessung ist jetzt essentiell, und wir müssen extrem
sauber arbeiten und langsam, nicht überstürzen durch die Ergebnisse."*

> **Urteil in einer Zeile:** Drei Schritte, jeder mit eigenem Stopp: **(1)** der Ersteintritt einmal auf 2025–26
> bestätigen, **(2)** H0: stimmt die Liquidationsgefahr aus der ATR auf genau diesen Einstiegen, **(3)** Simulation: verdient
> der Kern nach Kosten Geld? Alles ist **Test, nicht Betrieb**. Hier wird Schritt 1 **vollständig** vorab festgelegt;
> Schritt 2 und 3 bekommen je eine eigene Voranalyse.

---

## 0. Ziel, Stand, Test oder Betrieb

| | |
|---|---|
| **Ziel** | je Asset und Handlung eine begründete Aussage über das **Potential**; ein Signal, wenn es erreicht ist (CLAUDE.md) |
| **Prinzip** (Regelwerk § 1/§ 4) | zum Prüfzeitpunkt **Bewertung 1** (Summe der Chance-Beiträge → Schwelle → Einstieg) und **Bewertung 2** (Summe der Risiko-Beiträge → Hebelstufe), neutral, ohne Ertrag |
| **Stand** | Chance: **ein** belegter Beitrag (rsi-Familie); Risiko: **ein** belegter Beitrag (ATR). Die Lage-Beiträge sind nicht widerlegt, aber mit den Daten ab 2024 nicht nachweisbar |
| **Der Kern** | Bewertung 1 = rsi (eine Summe mit **einem** Glied, ausdrücklich so benannt), Einstiegsform **Ersteintritt**; Bewertung 2 = ATR |
| **Test oder Betrieb** | ⛔ **nur Test**. Kein Betrieb vor der ganzen Kette inkl. LLM-Rollen (stehende Regel); Prüftakt und Cooldown sind Phase 2 |
| **Warum Kern zuerst** | trägt der Kern, sind weitere Beiträge **Verfeinerung**; trägt er nicht, retten ihn kleine Beiträge nicht — dann ist es **sicher** gewusst |

---

## 1. Die drei Schritte

| # | Schritt | Frage | Stand |
|---|---|---|---|
| **1** | **Bestätigung Ersteintritt** | trägt der Einstieg beim ersten Überschreiten auf **ungesehenen** Monaten 2025–26? | hier vollständig festgelegt |
| **2** | **H0** | stimmt die Liquidationsgefahr, die die ATR je Stufe vorhersagt (2.681), auf **genau diesen** Einstiegen? | eigene Voranalyse nach Schritt 1 |
| **3** | **Simulation Ebene 3** | Einstieg, Hebel aus der ATR, feste Messgeometrie, **Kosten** (0,3 % je Handel, 0,18 %/Tag): bleibt vorwärts 2024–26 etwas übrig? | eigene Voranalyse nach Schritt 2; ⚠️ hier gibt es **eine echte Nutzerentscheidung**: die Liquidationsgrenze (Risikobereitschaft) |

➤ Jeder Schritt endet mit **Stopp**, Ergebnis und Zwischenfazit zum Ziel. Fällt ein Schritt, wird **nicht** nachjustiert,
bis es passt — dann ist der Kern in dieser Form widerlegt.

---

## 2. Schritt 1 — die Definition, vorab

| | |
|---|---|
| **Signal** | rsi allein (Modell aus rsi jetzt und 24 h alt), **je Monat nur auf der Vergangenheit** geschätzt (Training wachsend ab 2023-01, Grenzen aus dem Training) — wie 2.687 |
| **Maßstab** | v̂ = expit(logit(geschrumpftes Normal) + Beitrag) − Normal — hier nur als **Skala** des Beitrags; eine Zahl q wird **nicht** behauptet (K5-1 fiel, 2.687) |
| **Ersteintritt** | die erste Stunde mit v̂ ≥ s, davor 24 h mit mindestens **20 gültigen** Stunden **alle** unter s; **nicht** in den ersten 24 h eines Monats (Modellwechsel) — die in 2.687 gegengeprüfte Fassung (c) |
| **Einstieg** | Schluss der **nächsten** Stunde |
| **Ausgang** | q5: +5 % vor −5 % binnen 24 h ab dem Einstieg; Dq gegen das stündliche geschrumpfte Normal |

## 3. Schritt 1 — die Schwelle s: gemessen, nicht gewählt

| | |
|---|---|
| **Raster** | s = +0,010 · +0,015 · … · +0,050 (9 Stufen) |
| **nur auf 2024, Menge `bestand`** (Wahl) | je Stufe Ersteintritt-Dq und Nullwelt (rollierende Modelle auf verschobenem rsi, 40 Ziehungen) |
| **Regel** (vorab) | gewählt wird die Stufe mit dem **größten Abstand echt − P90 der Nullwelt**; bei Gleichstand (< 0,005) die **niedrigere** |
| **R-R11 zuerst** | die Stufen +0,02 und +0,04 geben **bitgleich** 2.687 (c): +0,0928 / +0,0759 |
| ⚠️ **Mehrfachtesten** | die Wahl aus 9 Stufen überschätzt 2024 — genau darum die **einmalige** Bestätigung auf ungesehener Zeit |

## 4. Schritt 1 — die Bestätigung 2025-01 bis 2026-08, vorab

**Einmal**, für die **eine** auf `bestand` gewählte Stufe — dieselbe in allen vier Mengen —, ohne Änderung danach:

| # | Bedingung | bei Nein |
|---|---|---|
| **B1** | Ersteintritt-Dq > 0 in **2025 und 2026** | ⛔ der Kern trägt ungesehen nicht |
| **B2** | über dem P90 der Nullwelt (40 Ziehungen), gesamt 2025–26 | ⛔ nicht vom Zufall zu trennen |
| **B3** | **vier Mengen**: B1 und B2 in ≥ 3 von 4 (`bestand`, `unverzerrt:1–3`) | ⛔ hängt an der Auswahl der Assets |
| **B4** | **je Asset**: ≥ 60 % der Assets mit ≥ 20 Ersteintritten haben Dq > 0 | ⛔ Klumpen |
| **B5** | **mit und ohne** 10./11.10.2025 (Einstiege, deren 24 h diese Tage berühren) — das Urteil ändert sich nicht | Black Swan nur als Störfaktor ausgewiesen (Nutzer) |
| A | Auskunft: Zustand gegen Ersteintritt; Einstieg +2 h/+6 h; Zahl der **verschiedenen Tage** mit Einstiegen (Markttage hängen zusammen); je Monat | – |

➤ **Alle** B1–B4 erfüllt → Schritt 2 (H0). Sonst **Stopp** — der Kern in dieser Form trägt nicht.

---

## 5. Prüfung und Gegenprüfung — extrem sauber

| Falle | Gegenmittel |
|---|---|
| **Vorgriff** | rsi bis zum Schluss der Signalstunde, Einstieg eine Stunde später; Modell nur auf Daten bis Monatsbeginn − 24 h; Normal nur aus Ausgängen bis t − 24 h |
| **Schein-Übertritte** | Fenster nur aus gültigen Stunden; kein Übertritt am Monatswechsel (2.687 gegengeprüft) |
| **Schwelle nach dem Ergebnis** | Wahl nur auf 2024, Regel vorab; 2025–26 wird **erst** in der Bestätigung berechnet — und nur **einmal** |
| **abhängige Einstiege** | viele Assets am selben Markttag: die Nullwelt verschiebt rsi je Asset; die Zahl der **Tage** wird ausgewiesen |
| **Grundgesamtheit** | vier Mengen (`unverzerrt` = Bestand + Eingestellte) |
| **Black Swan** | nur mit/ohne |
| **Kleine Läufe täuschen** | volle Daten; ein Funktionstest ohne inhaltliche Meldung |
| **2024 ist das schwache Jahr** | die Wahl dort ist eher **vorsichtig** |
| **Messgeometrie ist nicht Betrieb** | q5 ist die Zielgröße der Bewertung, kein Handelsergebnis — das Geld beantwortet erst Schritt 3 |

---

## 6. Zur Abstimmung

| # | Punkt | Empfehlung |
|---|---|---|
| **N1** | drei Schritte, je mit Stopp; Schritt 2 und 3 eigene Voranalysen | ja |
| **N2** | Definition Ersteintritt wie Abschnitt 2 (die gegengeprüfte Fassung) | ja |
| **N3** | Schwelle gemessen: Raster, Regel, R-R11 wie Abschnitt 3 | ja |
| **N4** | Bestätigung B1–B5, einmal, keine Änderung danach | ja |

➤ Du musst hier **nichts** wählen — alles Messbare ist vorab geregelt. Die einzige echte Entscheidung (die
Liquidationsgrenze) kommt erst in Schritt 3.

---

## 7. Umfang

Werkzeug (Modus in `messe_losfahren.py`) bauen und vorab committen · Funktionstest · **Wahllauf 2024** (etwa 40 Min) ·
Stopp mit der gewählten Stufe · **Bestätigung** 2025–26 in vier Mengen (je etwa 40 Min, nacheinander) · Stopp.

---

## 8. ✔ ABGESTIMMT (29.09.2026) — N1 bis N4, mit einer Korrektur

**Nutzer:** *„ja, N1 bis N4 wie empfohlen — prüfen und gegenprüfen. Wir brauchen Lösungen, und nicht nur, damit wir eine
Regel einhalten, weil eine Messung u. U. einen Fehler oder falsche Annahmen getroffen hat — also an der Messung
herumschrauben NEIN, aber Fehler oder eine Aussage zum Ergebnis und mögliche Lösungen JA, MUSS."*

⛔ **Korrigiert:** Abschnitt 1 und 4 sagten *„fällt ein Schritt … dann ist der Kern in dieser Form widerlegt“*. Das war
falsch und widerspricht der stehenden Regel *kein Beitrag fällt ohne Lösungssuche*. **Es gilt:**

| fällt ein Schritt | |
|---|---|
| ⛔ **nicht** | an der Messung schrauben, bis sie passt (Schwelle, Fenster, Definition nachträglich ändern) |
| ✔ **Pflicht** | (1) **Fehler prüfen** — Werkzeug, Daten, Vorgriff; (2) **Annahmen prüfen** — welche Annahme der Messung trifft nicht zu, und das **gemessen**, nicht vermutet; (3) **Aussage zum Ergebnis** — was genau hält nicht, wo, wie groß; (4) **Lösungsvorschläge** — jeder als **neue** Vorabfestlegung, zur Abstimmung |

---

## 9. ERGEBNIS WAHL 2024 (bestand) — Stopp

Beleg `Kern_29_09/wahl__bestand.txt`. ✔ R-R11: rsi allein +0,0808, Auswahl 29.390, Normal gleich, **2.687 (c) bitgleich**
(+0,0928 / +0,0759).

| Stufe | Einstiege | Tage | echt | Null Mittel | Null P90 | Abstand |
|---|---|---|---|---|---|---|
| +0,010 | 2.381 | 222 | +0,058 | +0,039 | +0,053 | +0,005 |
| +0,015 | 2.709 | 248 | +0,072 | +0,034 | +0,052 | +0,020 |
| +0,020 | 2.524 | 229 | +0,093 | +0,031 | +0,047 | +0,046 |
| +0,025 | 2.449 | 206 | +0,089 | +0,021 | +0,037 | +0,052 |
| +0,030 | 2.157 | 186 | +0,110 | +0,024 | +0,037 | +0,073 |
| **+0,035** | **2.095** | **190** | **+0,110** | +0,014 | +0,030 | **+0,079** |
| +0,040 | 1.871 | 178 | +0,076 | −0,000 | +0,014 | +0,062 |
| +0,045 | 1.631 | 157 | +0,037 | −0,019 | −0,007 | +0,044 |
| +0,050 | 1.357 | 135 | +0,030 | −0,023 | −0,006 | +0,036 |

➤ **Nach der Regel gewählt: s = +0,035** (Abstand +0,079; +0,030 liegt 0,006 darunter — kein Gleichstand).
Die Kurve ist ein **glatter Bogen** mit Gipfel bei +0,030..+0,035, kein einzelner Ausreißer.

⚠️ **Gegenprüfung — eine Annahme, die nicht zutrifft:** die Einstiege **ballen sich**: 2.095 Einstiege an nur **190 Tagen**
(rund 11 je aktivem Tag) — viele Assets laufen an denselben Tagen los. Die Nullwelt verschiebt rsi **je Asset** und
zerstört diese Ballung; ihr Band ist darum vermutlich **zu eng** (dieselbe Falle wie 2.673 bei Marktmerkmalen). Die
wahre Fallzahl sind eher die **Tage** als die Einstiege.

➤ **Lösungsvorschlag (neue Vorabfestlegung, VOR der Bestätigung):** **B6** — ein **Tagesblock-Bootstrap** (die Einstiege
tageweise gezogen, 1.000 Ziehungen): das 95-%-Intervall des Dq muss in der Bestätigung **über null** liegen. Das ist
**strenger**, nicht milder, und prüft genau die Annahme, die nicht zutrifft.

---

## 10. ✔ B6 AUFGENOMMEN — festgehalten VOR der Bestätigung (29.09.2026)

**Nutzer:** *„ja, B6 aufnehmen und Bestätigung starten — prüfen und gegenprüfen. Hinweis: Vorsicht, wenn du die
Konzentration der steigenden Assets, also der Gesamtmarkt steigt, als Anomalie siehst, dann ist das falsch — es ist
normales Marktverhalten, wenn BTC steigt und vorläuft. Wenn nicht, dann ist die Messung und Prüfung ok."*

➤ **So ist B6 gemeint und gebaut:** die Ballung ist **normales Marktverhalten** und bleibt **vollständig drin** — kein Tag,
kein Einstieg wird entfernt. B6 rechnet nur die **Unsicherheit** über die **Tage** statt über die einzelnen Einstiege,
weil Einstiege am selben Markttag keine unabhängigen Beobachtungen sind.

| | |
|---|---|
| **B6** | Tagesblock-Bootstrap: die Einstiege tageweise mit Zurücklegen gezogen, 1.000 Ziehungen (eigene Saat), 95-%-Intervall des Dq **> 0** |
| Lauf | `--kern --bestaetigen 0.035` in `bestand`, `unverzerrt:1`, `unverzerrt:2`, `unverzerrt:3` — nacheinander, **einmal**; danach Stopp |
| Urteil | B1, B2, B4, B6 je Menge; **B3** = B1 und B2 in ≥ 3 von 4 Mengen; B5 als mit/ohne ausgewiesen |
