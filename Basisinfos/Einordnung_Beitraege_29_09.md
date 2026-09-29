# Einordnung der Beiträge — wo wir stehen und wie die Erkenntnisse ins System gehören (29.09.2026)

**Nutzer:** *„Langsam und vorsichtig … Ich denke, es ist der richtige Zeitpunkt, kurz zurück zur aktuellen Lage der
Ergebnisse und Messungen zu gehen. Prüfe, welche Beiträge aus den Messungen je Lage (Kurve, Schwellen?) für uns
geeignet sind und wie wir diese einordnen sollten im System. Die langen Messungen bringen wenig, wenn wir keinen
tragfähigen Plan und Ansatz haben, die bisherigen Erkenntnisse einzuordnen."*

> **Urteil in einer Zeile:** Wir haben ein **Risikomodell** (ATR → Hebelstufe) und einen **Fortsetzungsbeitrag**
> (rsi), beide gemessen. Für das eigentliche Ziel — die Lage **vor** der Bewegung — haben wir **Kandidaten mit
> klaren Kurven** (Positionierung am Terminmarkt), aber **noch keinen Nachweis**. Das System braucht darum
> **getrennte Rollen**, nicht eine gemeinsame Summe.

**Zustandsdokument** — nach jedem Befund nachzuziehen (wie Plan und Regelwerk).

---

## 1. Die Frage, die jede Einordnung entscheidet: WANN weiß ein Beitrag etwas?

| Zeitpunkt | Was der Beitrag misst | Nutzerbild | Rolle |
|---|---|---|---|
| **vor** der Bewegung | eine Lage, die sich aufbaut, bevor der Kurs läuft | das Auto steht, der Motor läuft | ⭐ **Chance** (OPTIMUM) |
| **während** der Bewegung | die Bewegung selbst | das Auto fährt schon 200 | **Fortsetzung** — Wahrscheinlichkeit, kein OPTIMUM |
| **Umfeld** | wie weit es gegen mich gehen kann | die Straße ist glatt | **Risiko** — Hebelstufe |
| **Markt** | für alle Assets gleich | das Wetter | **Kontext** — nicht vorhersagbar (2.599) |

Geprüft wird das mit der **Karenz** (2.650/2.651: trägt der Beitrag noch, wenn das Ereignis erst später zählt?) und
künftig mit dem **Losfahren aus dem Stand** (nur Anker ohne bisherigen Anstieg).

---

## 2. Die Beiträge — Stand je Beitrag

### 2a. Chance VOR der Bewegung — Kandidaten, kein Nachweis

| Beitrag | Kurve (F5, 2.683) | Beleg | Vorbehalt |
|---|---|---|---|
| **konten_verh** (Long/Short-Konten) | **stärkste**: wenige Longs **+0,15**, viele **−0,25** (Log-Odds), monoton | Lift 2,96 bei ≤ 0,5759 (2.663); K1 vor allem **Markt**anteil (2.673) | nur in der **Suche** nachgewiesen (2.675); ungesehene Zeit im Marktrauschen |
| **funding** (Vortag) | stark negativ **+0,11**, sehr hoch **−0,10**, monoton; Extreme oben = Risiko | Lift 4,45 bei ≤ −0,0040 (2.663), hält 2022 (2.666) | Hälfte des alten Lifts war Vorgriff (2.663); nur Suche (2.675); vor allem **Markt** |
| **oi_aenderung** | sinkendes OI **+0,11**, Mitte leicht negativ | asset-eigen (2.673), unterer Rand 3 von 4 (2.675) | ohne unabhängige Bestätigung (2.675: gleich dem Versatz) |

➤ Zusammen ist das fachlich das Bild eines **aufgestauten Short-Squeeze** (wenige Longs, Shorts zahlen, OI wird
abgebaut). Es baut sich **vor** dem Kurs auf. **Aber:** In der Kombination mit rsi kommt davon nichts an
(2.682/2.683, Tor nicht bestanden), und für sich ist es in ungesehener Zeit nicht gesichert.
**→ Offene Kernfrage des Projekts.**

### 2b. Fortsetzung WÄHREND der Bewegung — gemessen, aber kein OPTIMUM

| Beitrag | Stand | Einordnung |
|---|---|---|
| **rsi** (14 h, gegen die eigenen 30 Tage) | ✔ trägt je Asset (2.675), jetzt **und** 24 h alt (2.676); keine Normal-Verzerrung (2.684); roh fast kalibriert (2.683); **2024 schwach**, zeitstabil nur in der Betriebsform (2.684); Karenz-Haltequote 0,43 (2.650) | misst die **laufende** Bewegung. Brauchbar als **Gewicht/Auskunft** (*Bewegung ist bestätigt*), **nicht** als Auslöser für OPTIMUM |
| **momentum_kurz** | trägt am oberen Rand (2.675), korreliert +0,62 mit rsi; schwächer als rsi (2.680) | **dieselbe** Information wie rsi — nicht zusätzlich zählen |
| **ema_abstand** (selbstbezogen) | Kurve trägt (2.671); der **aktuelle** Wert kehrt 2022 (2.676) | dieselbe Familie; als **Risiko** (MAE) belegt, siehe 2c |

### 2c. Risiko — Bewertung 2 (Hebelstufe)

| Beitrag | Stand | Einordnung |
|---|---|---|
| **ATR zum Einstieg** | ✔ sagt die Liquidationsgefahr je Stufe voraus, 5x vorwärts kalibriert, 3x geordnet (2.667, 2.681) | ⭐ **das Risikomodell** — Tabelle je Grenze liegt vor |
| volumenschub, oi_aenderung, ema_abstand als Risikokurven | ⛔ nichts über die ATR hinaus (2.681) | nicht verwenden |
| **Extreme der Lage** (funding sehr hoch, sehr viele Longs) | Kurven fallen dort (F5); funding ≥ 0,0016 zeigt nach unten (2.663); Recherche: hoher Carry sagt **Crashs** voraus (BIS) | ⭐ **Kandidaten als Risikogewicht** — ungemessen gegen die Liquidation (K6 R+S) |
| Markpreis gegen Spot-Tief, Marge | fast gleich; m = 0,09 vorsichtig, echte Marge je Asset rund 2–8 % (2.679: BTC 2–3,5, SUI 3,7–6,9, TAO ≥ 7,3) | Mechanik, geklärt |

### 2d. Kontext — Markt

| | Stand |
|---|---|
| Kontextfläche BTC × Dominanz, Dominanz-Sperren | ⛔ fallen (2.670, 2.672) |
| funding/konten **marktweit** | nur in der Suche (2.675) |
| Regime | wiegt zwölfmal mehr als die Lage (2.598), ist aber **nicht vorab erkennbar** (2.599). Recherche: gehört in die **Positionsgröße**, nicht ins Signal |

### 2e. Gefallen — nicht weiter verfolgen

turnover, oi_je_umsatz, taker_verh, top_konten_verh, top_summe_verh (nur Bewegung oder kein Band, 2.663) ·
volumenschub (Einstieg: nur Bewegung) · vola (nur Bewegung, 2.650) · bandenge (misst nichts, 2.650) ·
Käuferanteil und Premium (begleiten die Bewegung, 2.665).

---

## 3. Form — Kurve, Rand oder Schwelle?

| Form | Wann | Beleg |
|---|---|---|
| **Kurve** (glatt, 12 Stufen, Log-Odds) | Standard für jeden Beitrag: zeigt Optimum **und** Extreme (Nutzer: *Extreme eher Risiko, bis zu einem Bereich positiv*) | K1-Entscheidung; F5 (2.683) |
| **Rand** (oberes/unteres Zehntel) | als **Urteil**, ob ein Beitrag überhaupt trägt (Randkriterium, vorab festgelegt) | 2.675 |
| **Schwelle** | erst **am Ende** einer Rolle — auf dem kalibrierten Wert, als 3–5 Stufen; nie ein Blocker | K5; Nutzer 28.09. *Achsen sind Gewichte* |

⚠️ Eine Kurve je Beitrag heißt **nicht**, dass alle Kurven in **eine** Summe gehören. Das ist die Lehre aus 2.680–2.683.

---

## 4. Was die Recherche beigetragen hat

| Recherche | bei uns | Folge für die Einordnung |
|---|---|---|
| Momentum in Krypto ist **regimeabhängig**, zerfällt | rsi 2024 schwach, 2026 stark | rsi nur als Gewicht, nie als Hebelbegründung allein |
| **Forecast-Combination-Puzzle** | die gemeinsame Schätzung verwässert rsi | Rollen **getrennt** schätzen, einfach verknüpfen |
| Funding/OI erklären die **gleiche** Periode | ohne Vorlauf gemessen | Vorlauf eigens messen (*Losfahren*) |
| hoher Carry → **Crash** | Kurve fällt bei hohem funding | funding-Extreme als **Risiko** (K6 R+S) |
| **Winner's Curse** / Schrumpfung | Normal ist meist Rauschen (2.683) | Bezug = **geschrumpftes** Normal |
| Kalibrierung: Steigung lang, Achsenabschnitt kurz | ⛔ der kurze Achsenabschnitt scheitert (2.683) | hier widerlegt: **nicht** kurz nachführen |
| Regime in die **Positionsgröße** | Regime nicht vorhersagbar (2.599) | Phase 2 |

---

## 5. Der Ansatz — getrennte Rollen statt einer Summe

| Stufe | Frage | Eingänge heute | Ausgabe |
|---|---|---|---|
| **A · Lage** (Chance vorher) | baut sich etwas auf? | ⭐ **offen** — Kandidaten 2a | Wahrscheinlichkeit, dass es **losgeht** |
| **B · Fortsetzung** | läuft es schon? | rsi (2b) | Gewicht: *bestätigt* / *schon gelaufen* (A4) |
| **C · Risiko** | wie weit kann es gegen mich gehen? | ATR (2c), später Extreme der Lage | Hebelstufe aus der Liquidationsgefahr |
| **D · Kontext** | wie ist der Markt? | — (nicht vorhersagbar) | Positionsgröße (Phase 2) |
| **Mail** | warum? | alle Fakten und Bewertungen | Begründung, kein Auslöser |

➤ Ein **Signal** entsteht nach OPTIMUM aus **A**; B verändert nur das Gewicht, C die Hebelstufe, D die Größe.
Solange **A leer** ist, gibt es **kein** begründetes Einstiegssignal *vor* der Bewegung — nur ein
Fortsetzungssignal (B). Ob das für den Hebel reicht, ist eine **Nutzerentscheidung**, keine Messung.

---

## 6. Der Plan — langsam und vorsichtig, in dieser Reihenfolge

| # | Schritt | wozu |
|---|---|---|
| **1** | diese Einordnung abstimmen; danach `BEITRAGSLAGE` im Standblatt auf die Rollen umstellen | Zustand im Code = Zustand im Kopf |
| **2** | ⭐ **Losfahren aus dem Stand** — Voranalyse, dann messen: nur Anker ohne bisherigen Anstieg; Lage **für sich**, mit Vorlauf, eigenes Tor; rsi als Gegenprobe | füllt **A** oder zeigt, dass es leer ist |
| **3** | **K6 R+S** — Extreme der Lage als Risikogewicht; der 10./11.10. nur als **Störfaktor** ausgewiesen | vervollständigt **C** |
| **4** | **K5** neu vorlegen — auf dem Ergebnis von 2 | die Schwelle auf der richtigen Rolle |
| **5** | **H0** — Liquidationsgefahr auf der tatsächlichen Einstiegsauswahl | Pflicht vor der Verwendung |
| **6** | **Simulation Ebene 3** und neue Monate ab 2026-09 (Z6) | die Zeitfrage endgültig |

---

## 7. ⚠️ Black Swans — Nutzervorgabe 29.09.2026

> *„Du kannst den 10. und 11.10. zwar als Störfaktor mitführen, ABER so ein Ereignis kann man nicht abfangen — dies war Marktmanipulation, und es wurden Existenzen zerstört. Black-Swan-Events haben keine Möglichkeit der Messung.“*

| | |
|---|---|
| **mitführen** | jede betroffene Zahl **mit und ohne** den 10./11.10. ausweisen (Störfaktor, J10) |
| **nicht** | kein Modell, keine Schwelle, kein Deckel wird an einem solchen Ereignis ausgerichtet; der *Stresstag-Deckel* aus der Recherche entfällt als Messziel |
| **Schutz dagegen** | liegt nicht in der Vorhersage, sondern in der **Hebelhöhe und Positionsgröße** (Rolle C/D) — die Frage ist, ob eine Stufe einen solchen Tag **übersteht**, nicht, ob man ihn kommen sieht |
