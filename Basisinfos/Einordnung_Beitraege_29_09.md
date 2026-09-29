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

> ⛔ **ÜBERHOLT (29.09.2026, Voranalyse Beitrag/Kontext/Gewicht P7):** Dieser Abschnitt benutzt eine **andere Buchstabenfolge** (A Lage · B Fortsetzung · C Risiko · D Kontext) als das gültige Rollenschema und nennt rsi ein „Gewicht“. **Es gilt** das Schema aus den Abschnitten **8–9** (A OB · B WIE WEIT · C WIE VIEL HEBEL) und die Begriffe **Beitrag · Kontext · Gewicht** im Regelwerk. Stehen gelassen als Verlauf, nicht als Grundlage.

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

---

## 8. ⛔ KORREKTUR (29.09.2026, beim Umbau des Standblatts gefunden) — es gibt schon ein Rollen-Schema

**Nutzerfrage:** *„Irgendwie hat dieser Plan Ähnlichkeit mit bereits besprochenem Vorgehen — einige der
Messungen haben wir doch für die Beiträge gemacht, oder?"* — **Ja.** Im Standblatt (`hebel_neubau.ROLLEN`,
Neubauplan 25.09.) steht:

| Rolle (25.09.) | Frage | Anordnung |
|---|---|---|
| **A · Richtung** | geht es aufwärts? | |
| **B · Bewegungserwartung** | kommt **überhaupt** etwas? (richtungslos) | **A und B und NICHT C** — keine Summe |
| **C · Risikosperre** | überdehnt, überhitzt? | |

Meine Einordnung (Abschnitte 1–6) hat dieselbe Einsicht neu erfunden (*getrennte Rollen, keine Summe*) — und dabei
**einen Fehler** gemacht: vola, volumenschub, oi_je_umsatz, oi_aenderung standen unter *gefallen*. Das gilt nur für
die **Richtung**. Für die **Höhe** sind sie die robustesten Beiträge überhaupt (2.655/2.662: 14 von 16 Auswahlen,
vorwärts in 24–32 von 32 Monaten, jede BTC-Lage) — **Rolle B**.

### Vorschlag: das Schema vom 25.09. bleibt, die Zeitfrage von heute wird darin eingeordnet

| Rolle | Beiträge | Stand |
|---|---|---|
| **A · Richtung — vorher** (OPTIMUM) | funding negativ, wenige Longs (Spiegel 1,10 / 1,18, 2.655; Kurven 2.683), oi_aenderung | ⭐ Kandidaten, kein Nachweis in ungesehener Zeit (2.657, 2.665, 2.675) |
| **A · Richtung — während** (Fortsetzung) | rsi, momentum_kurz (eine Familie) | ✔ gemessen (2.648, 2.675, 2.683, 2.684) — **eigener Einstiegstyp** (Nutzer: Quant +400 %, *300 mitnehmen*); die Positionsführung entscheidet (2.656) |
| **B · Bewegungserwartung** (Höhe, richtungslos) | vola_kausal/ATR, volumenschub, oi_je_umsatz, oi_aenderung | ✔ **robust** (2.655, 2.662); in ATR gemessen größtenteils die ATR selbst, darüber hinaus volumenschub und oi_aenderung tief (2.667) |
| **C · Risikosperre** | ema_abstand hoch (2.642/2.643); **Kandidaten**: funding hoch, viele Longs (Spiegel 0,85 / 0,63, 2.655; Kurven 2.683) | ✔ ema_abstand; die Extreme der Lage ungemessen als Sperre |
| **Bewertung 2 · Hebelhöhe** | ATR zum Einstieg | ✔ 2.681 (5x kalibriert, 3x geordnet) |
| **Kontext** | Regime | nicht vorhersagbar (2.599) → Positionsgröße |

⚠️ **Eine offene Spannung, zur Entscheidung:** *„A und B und NICHT C"* (25.09.) ist eine **Und-Verknüpfung** — der
Nutzer hat am 28.09. entschieden: *Achsen sind Gewichte, keine Blocker*. Vorschlag: A liefert das Signal, **B und C
wirken als Gewichte** (B hebt, C senkt), keine harte Sperre.

⚠️ **Folge für Schritt 2 (*Losfahren*):** Die Frage *Lage vorher* ist durch 2.650, 2.651/2.663, 2.657 und 2.665
**weitgehend schon gestellt** — mit niedriger Erwartung. Neu wäre nur: Anker ohne bisherigen Anstieg, Vorlauf mit
Einstieg jetzt, Bezug geschrumpftes Normal. Vorher R-R11 auf 2.657/2.665.

---

## 9. ✔ GEPRÜFT (29.09.2026) — das Schema hält, B und C wirken auf ANDERE Ausgaben

**Nutzer:** *„JA von mir, hört sich schlüssig an — DU musst noch prüfen und gegenprüfen, ob der Vorschlag halten
kann und fachlich in die richtige Richtung geht."*

| Prüfung | Messung | Ergebnis |
|---|---|---|
| A liefert das Signal | unser Dq zählt nur Anker mit Treffer = P(oben zuerst); rsi/momentum tragen (2.675, 2.683) | ✔ hält |
| **B als Gewicht auf das Signal?** | B ist richtungslos (oi_aenderung Spiegel 1,02–1,07, vola fällt als Richtung, 2.655/2.650); vergrößert Anstieg **und** Rückgang (2.655/2.662); in ATR kaum größer (2.667) | ⛔ **hält nicht** → B bestimmt **wie weit** (Potential, Geometrie), nicht *ob* |
| **C als Gewicht auf das Signal?** | hohes ema_abstand setzt sich nach **oben** fort (2.655, 6 von 6 Jahren), aber mit größerem Rückgang (2.642: *Risikofilter, kein Ertragsfilter*) | ⛔ **hält nicht** → C wirkt über **Bewertung 2** auf Hebelstufe und Stop |
| Regel 1–4 (Takt, Gebühren, Asset-Rang, Fakt) | feste Werte gegen das eigene Normal; alles Bewertungen | ✔ |
| Recherche | P(Schranke) × P(oben \| Schranke) — genau B × A | ✔ |

➤ **Geprüfte Fassung:** **A entscheidet OB · B entscheidet WIE WEIT · C mit der ATR entscheidet WIE VIEL HEBEL.**
Drei Ausgaben, keine Summe, kein Blocker. Umgesetzt im bestehenden `hebel_neubau.ROLLEN`/`KANDIDATEN` (kein zweites
Schema), Belege der Beitragslage und der Messplan nachgezogen (Proben für rsi und ATR/H0, K6 R+S ohne Stresstag).

---

## 10. Stand, Anfahren, Fahrt — der Sweet Spot (Nutzeranalogie 29.09.)

> *„Optimal wäre, als weitere Analogie: optimale Voraussetzung (Auto steht noch, wann fahren wir los?) — Sweet Spot (Kurve oder Schwelle) — das Auto hat sich in Bewegung gesetzt, nicht von 0 auf 200 mögliche Endgeschwindigkeit, sondern als Beispiel 0 auf 20 (Auslöser, geht?).“* — ausdrücklich *kein Gesetz*, fachlich eingeordnet:

| Phase | Bild | was wir messen | Befund |
|---|---|---|---|
| **Stand** | Motor läuft, Auto steht | die Lage (Positionierung am Terminmarkt) | A vorher — Kandidaten (2.665, 2.683) |
| **Anfahren** | 0 auf 20 — *geht es los?* | bisheriger Anstieg in eigener ATR (A4) **klein**, Bewegung bestätigt | ⭐ **Sweet Spot** — Hinweis: die Auswahl wirkte bei < 1 ATR, war nach > 1–2 ATR negativ (K5-Werkzeugtest, kleine Stichprobe); Recherche: nach schnellen Stößen eher Umkehr |
| **Fahrt** | schon 200 | rsi, momentum — Fortsetzung | A während — belegt (2.675, 2.683, 2.684) |

➤ **Fachlich:** Die Analogie trägt. Der bisherige Anstieg in eigener ATR ist die **Tachonadel**. Gemessen wird der Sweet Spot als **Kurve** über diese Achse (keine Schwelle festlegen, die Daten zeigen, wo er liegt) — in der Messung *Losfahren aus dem Stand*.

✔ **Gemessen (2.685, 29.09.):** **kein Sweet Spot beim Anfahren** nachweisbar. Die rsi-Auswahl trägt in jeder Phase, absolut am meisten in der **Fahrt** (0..0,5 ATR +0,076..+0,080, 1..2 ATR +0,104..+0,123) — aber alle Anker steigen mit: die Nadel ist **selbst Fortsetzung**. Ein Anfahr-Vorteil ≥ +0,08 ist ausgeschlossen, kleinere kann die Anlage nicht auflösen. ➤ Die Nadel ist **kein Gewicht**; ob sie in die Mail gehört, ist **offen** (Nutzer: *abstrakte Zahl, bereits jetzt zu viel Information*); der Hinweis aus dem K5-Werkzeugtest (*nach > 1 ATR negativ*) hat sich auf der vollen Menge **nicht** bestätigt. Der Stand (Lage vorher): funding über dem Band, aber unter der Auflösung und vor allem Markt.

---

## 11. Kalibrierung — was, worauf, wann

| was | übersetzt | Stand | im Plan |
|---|---|---|---|
| **A · Signal** | Modellwert → echte Wahrscheinlichkeit *oben zuerst* | rsi roh fast kalibriert; kurze Nachführung scheitert (2.683) | **K5**, auf der Rolle aus *Losfahren* |
| **C/ATR · Hebel** | ATR → Liquidationswahrscheinlichkeit je Stufe | ✔ 5x kalibriert, 3x geordnet (2.681) | **H0** auf der Einstiegsauswahl; die Grenze setzt der Nutzer |
| **B · Potential** | Lage → erwartete Größe der Bewegung | gemessen (2.662), nicht als kalibrierte Vorhersage | **nachgelagert** — Geometrie (Ziel, Stop), Phase 2/5 |

---

## 12. Der Plan ab 29.09. (ersetzt Abschnitt 6)

| # | Schritt | Stand |
|---|---|---|
| 1 | Rollen im Standblatt | ✔ 028a0f9 |
| 2 | ⭐ **Losfahren aus dem Stand** — R-R11 auf 2.665/2.657, stehende Anker, Lage für sich, Anfahr-Kurve, rsi als Gegenprobe | Voranalyse als Nächstes |
| 3 | **K6 R+S** — Extreme der Lage als Risiko (Black Swans nur Störfaktor) | danach |
| 4 | **K5** neu vorlegen, mit der Kalibrierung von A | nach 2 |
| 5 | **H0** | nach 4 |
| 6 | **Simulation Ebene 3**, Regel einfrieren, neue Monate ab 2026-09 | nach 5 |

➤ **Warum *Losfahren* nicht zurückgestellt wird (29.09., meine erste Empfehlung war falsch begründet):** die früheren Messungen der *Lage vorher* (2.650, 2.657, 2.665) liefen über ALLE Anker, auch die fahrenden — und rsi verdeckt die Lage (2.682/2.683). Ein schwaches Ergebnis von damals kann ein verdecktes sein.
