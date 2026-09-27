# Voranalyse — die ANWENDUNGSEBENE: Beiträge kombinieren (27.09.2026)

> **Nutzer 27.09.:** *„Was mir reicht, steht nicht zur Diskussion, ich
> möchte ein funktionierendes System. [...] Das System basiert grundsätzlich
> darauf, dass ein Beitrag selbst schwach ist, aber in Kombination der Effekt
> stärker ist."* — und: *„Die nächste Phase gehen wir sorgsam gemeinsam
> durch."*

⚠️ **Dieses Blatt baut nichts.** Es legt den Ist-Stand, die offenen Fragen
und einen Prüfplan vor. Gebaut wird erst nach Abstimmung, Punkt für Punkt.

---

## 0. Auf welcher Ebene wir stehen

| Ebene | Frage | Stand |
|---|---|---|
| **1 Einzelbeitrag** | trägt ein Merkmal allein, gemessen über alle Assets gegen das eigene Asset? | ✔ gemessen, Pflichtablauf (2.662 bis 2.667) |
| **2 Kombination** | trägt die **Summe** der Beiträge je Asset und Zeitpunkt mehr als jeder allein? | ⛔ **nie gemessen** |
| **3 Anwendung** | ab welcher **absoluten** Summe kommt ein Signal, mit welcher Hebelstufe — und wie oft, mit welchem Ergebnis, je Asset? | ⛔ offen |

➤ Alle Aussagen bis heute sind Ebene 1. Ein schwacher Einzelbeitrag ist
ein **Kandidat** für Ebene 2, kein Misserfolg.

---

## 1. Ist-Stand — die Beiträge, die in die Kombination gehen könnten

Nur was den Pflichtablauf gehalten hat oder dort ausdrücklich als Sperre
belegt ist. Zahlen: Dq = Trefferverhältnis der Auswahl minus das des
eigenen Assets im selben Monat (q5: +5 % vor −5 % in 24 h).

### 1a. Richtung (Bewertung 1 — Einstieg)

| Beitrag | Wirkung | Belegt durch | Vorbehalt |
|---|---|---|---|
| `funding` Vortag **negativ** (≤ P5) | Dq **+0,025** (Mittel über 12 Startstunden), 2022 bestätigt **+0,028** | 2.665, 2.666 | klein; als **Phase** deutlich stärker (gegen das Asset im ganzen Zeitraum / den Markt) — ob es die Phase **vorhersagt**, ist ungemessen |
| `funding` Vortag **hoch** (≥ P95) | **Sperre**, Dq −0,045, 12 von 12 Startstunden negativ | 2.665, 2.666 | 2022 nicht prüfbar (4 Episoden) |
| `konten_verh` **hoch** (viele Longs) | **Sperre**, in allen Regimen negativ | 2.660 (E3, Gegenprüfung) | in E2f auf q5 jenseits des Bandes, aber vorwärts nicht stabil genug für *trägt* |

### 1b. Kontext (marktweit — für alle Assets zur selben Stunde gleich)

| Lage | Messung (Einzeltests, kein Bestes-von-N) | Nutzerhypothese 27.09. |
|---|---|---|
| BTC 24 h ↑ **und** Dominanz 24 h ↑ | q5 Dq **−0,020** (z −6,9) — die Sperre aus 2.601 in Stundendaten | *„eher schlecht"* ✔ passt |
| BTC 24 h ↑ **und** Dominanz 24 h ↓ | q5 −0,003 · q15 **+0,119** (z +8,5) | *„zwei positive Effekte"* — ✔ bei großen Bewegungen, ⛔ nicht bei ±5 % |
| BTC **seitwärts** und Dominanz ↓ | ⛔ **nicht getrennt gemessen** | *positiv* — offen |
| BTC 24 h ↓ | um null | – |

⚠️ Kontext ist nach stehender Vorgabe **kein Beitrag je Asset** — er kann
aber als **Bedingung** in die Kombination (Achse, 2.601).

### 1c. Risiko (Bewertung 2 — Hebelhöhe)

| Beitrag | Wirkung | Belegt durch |
|---|---|---|
| **ATR zum Einstieg** | das Risikomaß selbst: −12 % (≈ 5x) binnen 72 h im untersten Fünftel **5,8 %**, im obersten **26,9 %**; stabil 2022–2026 | 2.667 (E2i) |
| `volumenschub` hoch | mehr Bewegung **über** die ATR hinaus (+0,08 ATR) | 2.667 |
| `oi_aenderung` tief | weniger Bewegung (−0,09 bis −0,16 ATR) | 2.667 |
| `ema_abstand_atr` tief | Risikosperre (MAE in ATR, regelfrei) | 2.642, 2.647 |

### 1d. Nicht als Einstieg zugelassen

| Merkmal | warum |
|---|---|
| `kaeufer_24h` hoch | **begleitet** die Bewegung (12 h alt nur noch 30 %) — 2.665 |
| `momentum_kurz`, `rsi` hoch | **sind** die Vorbewegung — Nutzerdefinition OPTIMUM: *„ein bereits gestiegenes Asset ... dazu brauche ich kein System"* |
| Premium, Käuferanteil auf ±5 % | ohne tragende Wirkung — 2.665 |

---

## 2. Die Fragen, die vor dem Bau zu klären sind

Je Frage: was ich empfehle und warum. **Keine davon entscheide ich allein.**

| # | Frage | Empfehlung | Warum |
|---|---|---|---|
| **K1** | **Wie wird verrechnet?** | ✔ **ENTSCHIEDEN 27.09. — siehe Abschnitt 2a** (Wirkungskurven statt Punktsumme) | – |
| **K2** | **Welcher Bezug?** | ✔ **ENTSCHIEDEN 27.09. — siehe Abschnitt 2b** (Urteil gegen die Phase, Kontrollen zerlegen) | – |
| **K3** | **Wie geht der Kontext ein?** | ✔ **ENTSCHIEDEN 27.09. — siehe Abschnitt 2c** (Kontextfläche zuerst, dann Kurven) | – |
| **K4** | **Zielgröße?** | ✔ **ENTSCHIEDEN 27.09. — siehe Abschnitt 2d** (q5/24 h als Ausgangsbasis, Fenster als Achse) | – |
| **K5** | **Ab wann ein Signal?** | ✔ **ENTSCHIEDEN 27.09. — siehe Abschnitt 2e** (Schwelle auf kalibriertem q) | – |
| **K6** | **Hebelstufe?** | ✔ **ENTSCHIEDEN 27.09. — siehe Abschnitt 2f** (Liquidationswahrscheinlichkeit, zuerst R) | – |
| **K7** | **Mit welchem Kurs wird die Liquidation gemessen?** | ✔ **ENTSCHIEDEN 27.09. — siehe Abschnitt 2g** (Binance, Markpreis vor Spot-Tief, Abgleich an echten Liquidationen) | – |

## 2a. ✔ K1 ENTSCHIEDEN (27.09.2026) — Wirkungskurven, keine Schalter

**Nutzer:** *„A ist komplett starr und bildet nicht ab, wie ich es mir
vorstelle: zu einem Beitrag gibt es einen Optimalwert und Abweichungen nach
oben und unten, und diese in Kombination sollten eine robuste Aussage liefern.
Was sind zu viele Longs? Dann 0 — kein Übergang, keine Schwelle."* Und:
*„je besser der Wert, desto besser die Wirkung — auch in Kombination — das
muss gemessen werden."*

⛔ **Verworfen:** die Punktsumme (Schalter, ±1 je Lage) — sie wirft den
Verlauf weg. In E2f ist er für `konten_verh` schon sichtbar: P1 +0,027 ·
P5 +0,004 · P95 −0,027 · P99 −0,056.

| | Entscheidung |
|---|---|
| **Kurve** | je Beitrag eine **feste Wirkungskurve** über den ganzen Wertebereich (Regler, nicht Schalter) — steigend, fallend oder mit **Optimum** |
| **Form des Merkmals** | **roh** und **selbstbezogen** (gegen die eigenen letzten 30 Tage) nebeneinander; die bessere gewinnt nach vorab festgelegtem Kriterium. Der selbstbezogene Nullpunkt wandert mit der Lage, **ohne** ein Regime schätzen zu müssen |
| **Regime** | nur als **Prüfung**: hält die Form der Kurve in jedem Regime? Wenn nicht, reden wir — erst dann wandernde Kurven. ⚠️ Ein Regime im Betrieb muss zum Prüfzeitpunkt **bekannt** sein (die BTC-Monatslage ist Rückschau); der Marktzustand ist vorab kaum erkennbar (2.599) |
| **Kombination** | die **Summe der Kurven** (additiv, Kurven nur aus der Vergangenheit kalibriert) — trägt sie mehr als der beste Einzelbeitrag? |
| **Wechselwirkungen** | ein Baummodell als **Suchgerät** nur im Suchzeitraum; seine Funde werden **Hypothesen** und als lesbare Regeln auf ungesehenen Daten geprüft. Die Blackbox entscheidet nie. ⚠️ Grenze: wenige unabhängige Regimewechsel (44 Monate) |

**Die drei Schritte:**

| Schritt | Was | Frage |
|---|---|---|
| 1 | Wirkungskurve je Beitrag (z. B. 20 Stufen), gegen das eigene Asset, Nullwelt je Stufe, vorwärts, je Jahr und Regime | Form? Optimum? hält sie? |
| 2 | Summe der Kurven, rollierend kalibriert | mehr als der beste Einzelbeitrag? |
| 3 | Wechselwirkungen suchen (Suchzeitraum), als Regeln prüfen (ungesehen) | wirken Paare zusammen mehr als ihre Summe? |

## 2b. ✔ K2 ENTSCHIEDEN (27.09.2026) — Urteil gegen die Phase, Kontrollen zerlegen

**Nutzer:** *„ganzer Markt steigt ist nur ein Problem, wenn das Asset, das
gemessen wird, nicht steigt — korrekt?"* — für den **einzelnen Trade** ja.
Die Unterscheidung zählt erst in der **Kombination**: (1) **Doppelzählung**
mit dem Kontext, (2) **Klumpen** — ein Marktsignal feuert bei vielen Assets
zugleich, also viele Trades auf eine Wette, (3) **Haltbarkeit** — ein
Marktmuster kann wechseln, eine Eigenschaft des Assets ist robuster.

⛔ **Verworfen: die drei Bezüge zu einem Beitrag verschmelzen.** Sie sind
dieselbe Messung gegen drei Maßstäbe, stark verbunden — ein Mittel gibt keine
zusätzliche Sicherheit, es verwischt nur die Herkunft. Echte Bestätigung
kommt aus **unabhängigen** Prüfungen (anderer Zeitraum, vorwärts, andere
Assets).

| | Entscheidung |
|---|---|
| **Urteil = der Beitrag** | die Wirkungskurve gegen die **Phase**: eigenes Asset gegen seine **eigenen letzten 12 Monate**, nur Vergangenheit — die Frage des Betriebs: *läuft dieses Asset jetzt besser, als es normalerweise läuft?* |
| **Kontrolle Moment** | eigenes Asset im selben Monat — wie viel der Wirkung ist Zeitpunkt? (⚠️ der Monatsschnitt enthält die Zukunft im Monat; darum Kontrolle, nicht Urteil) |
| **Kontrolle Tag** | andere Assets am selben Tag (tagestreu) — wie viel ist **Markt**? |
| **Folge der Tageskontrolle** | trägt der Markt einen großen Teil, wird das Merkmal **geteilt**: `<merkmal>_markt` (Mittel aller Assets zur selben Stunde → **Kontext**) und `<merkmal>_eigen` (Asset minus Markt → **Beitrag**); jede Hälfte bekommt ihre eigene Kurve, in der Summe zählt nichts doppelt |
| **gilt für alle Beiträge** | funding, konten_verh, oi_aenderung, … |
| ⛔ **Markt-Bezug** (gegen alle Assets) | scheidet als Urteil aus — Asset-Vergleich, beim Hebel kein Asset-Rang (Regel 3) |

## 2c. ✔ K3 ENTSCHIEDEN (27.09.2026) — Kontextfläche zuerst, dann Kurven

**Nutzerhypothese:** *„ja, zu viele Longs sind eher schlecht, aber BTC
steigt oder geht seitlich und die Dominanz fällt sind zwei positive
Effekte."* — wird **direkt gemessen**, nicht angenommen.

| | Entscheidung |
|---|---|
| **Merkmale** | BTC-Rendite und Änderung des Dominanz-Index über **24 / 72 / 120 h** (Achse), streng kausal; später die Markt-Hälften aus K2 (`funding_markt` …) |
| **Erster Schritt** | die **Kontextfläche**: BTC-Rendite in Fünfteln × Dominanz-Änderung in Fünfteln, je Zelle die Wirkung auf die Alts gegen ihre eigene Phase (K2), vorwärts, je Jahr. *Seitwärts* wird nicht gesetzt — die Fläche zeigt, wo es noch gut ist |
| **Form danach** | **addieren** sich die Effekte → zwei Kontextkurven in der Summe (Regler wie K1); **hängen sie voneinander ab** → die Fläche bleibt **ein** Kontextbeitrag |
| ⛔ **verworfen** | Kontext als **Tor** (Schalter, starr — K1) |
| **Wechselwirkung** Kontext × Beitrag | Schritt 3 (Suche, dann Prüfung), durch die Zahl der Regimewechsel begrenzt |
| **Prüfung** | ⚠️ **Zeitverschiebungs-Nullwelt**: die Kontextreihe wird gegen die Ausgänge um zufällige Monate verschoben (Verlauf bleibt, Zuordnung fällt); die effektive Fallzahl sind **Tage**, nicht Episoden. Die z-Werte der Kontextprobe in E2f (−6,9 / +8,5) waren mit Episoden-Ziehung **zu optimistisch** (Nachtrag in 2.665) |
| **Klumpen** | ein guter Kontext hebt alle Assets zugleich → viele gleichzeitige Signale. **Nutzer 27.09.:** *„Klumpen ist da, kein Fehler — aber wir definieren, wie wir damit umgehen; sehe aktuell kein Problem."* → Umgang wird in Phase 2 (Kapazität, Positionsgröße) festgelegt, nicht in der Bewertung |

## 2d. ✔ K4 ENTSCHIEDEN (27.09.2026) — der Lehrer der Messung

Der Lehrer gehört **nur zur Messung**, nicht zur Bewertung (die bleibt ohne
Zeit). Stop und Ziel sind hier erlaubt — Nutzer: *„zum MESSEN und PRÜFEN ...
da sollen Kurs und ggf. Stop, erreichtes Ziel Verwendung finden."*

| | Entscheidung |
|---|---|
| **Urteil** | **q5**: +5 % **vor** −5 %, binnen 24 h (Gleichstand in einer Stunde = Rückgang zuerst) — vorab festgelegt, damit die Wahl der Zielgröße nicht selbst zur Suche wird |
| **Achse** | Höhen 3 / 5 / 10 % × Fenster 24 / 72 / 120 h — prüft, ob die **Form** der Wirkungskurve überall dieselbe ist |
| **Ergänzung** | Ausgang +5 / −5 / sonst Kurs am Fensterende — für die spätere Erfolgsrechnung |
| ⛔ **nicht als Lehrer** | Ereignis ohne Reihenfolge (misst Volatilität, 2.650/2.657) · Trailing (Positionsführung) |
| **Messlatte** | Grundrate q = 0,49; funding allein hebt auf ~0,515–0,53. Die **Kombination** muss q deutlich über 0,5 heben |

⭐ **Nutzerhinweis 27.09. (keine Anweisung):** *„die 24 h sind eine
Ausgangsbasis, und ich glaube, deine Messungen haben ergeben: je mehr Zeit
vergeht, desto öfter werden diese wieder abverkauft. Das bedeutet aber nicht,
dass wir auf einem fixen Fenster von 24 h oder darunter liegen müssen. Auch
ein späterer Erfolg soll zählen."* → Die 72-/120-h-Spalten sind darum **mehr
als eine Formprüfung**: sie zeigen, ob eine Lage **später** noch Erfolg hat,
und sie gehen in die Erfolgsrechnung ein. Das *Abverkaufen* ist belegt
(2.657: über alle Einstiege binnen 120 h im Median −10 bis −15 %; E1 2.654:
ab +10 % braucht es meist mehr als 24 h) — wie lange gehalten wird, ist eine
Frage der **Positionsführung**, nicht der Bewertung.

## 2e. ✔ K5 ENTSCHIEDEN (27.09.2026) — Schwelle auf der kalibrierten Trefferquote

| | Entscheidung |
|---|---|
| **fest** | absolut, **kein Rang** (*muss auch bei nur EINEM Asset funktionieren*, Regel 3) · Häufigkeit ist **Folge**, kein Ziel · der Takt gibt kein Signal (Regel 1) |
| **Schwelle auf** | der **erwarteten Trefferquote q** = eigenes Normal (Phase, K2) + Summe der Kurven — dieselbe Bedeutung für jedes Asset |
| ⛔ **nicht auf** | der Summe allein — ein Asset, das oft abverkauft wird, braucht mehr Vorsprung |
| **Pflicht** | **Kalibrierung vorwärts**: sagt das System q = 0,60, müssen auf ungesehenen Monaten auch ~60 % zuerst +5 % erreichen. Sonst keine Schwelle |
| **Wer legt die Höhe fest** | der Nutzer, **nach** der Tabelle je möglicher Schwelle (Signale je Monat und Asset · tatsächliches q · Ergebnis · je Regime); gewählt im Suchzeitraum, **einmal** auf dem ungesehenen bestätigt |
| **Hebelstufe** | nicht hier — K6, aus dem Risiko |
| **Zahl der Stufen** | ✔ siehe **K5b** unten |

### K5b ✔ ENTSCHIEDEN (27.09.2026) — wie viele Stufen

**Nutzer:** *„gut und sehr gut waren nur ein Beispiel — 3 oder 5 wären eher
meine Vorstellung, aber ... wir messen und bewerten danach?"*

| | Entscheidung |
|---|---|
| **Regel vorab** | so viele Stufen, wie sich **vorwärts in jedem Regime trennscharf** unterscheiden — **3 bis 5** |
| **Trennschärfe** | der **Unterschied** zweier benachbarter Stufen wird direkt getestet — nicht über *Bänder überlappen nicht* (überlappende Bänder sagen nichts über ihren Unterschied, stehende Regel) |
| **Rahmen** | **symmetrisch um das eigene Normal, mit Sperren**: 3 = *Sperre · neutral · Signal*; 5 = *starke Sperre · Sperre · neutral · Signal · starkes Signal* |
| **Warum die Messung zählt** | Spanne des kalibrierten q und Unschärfe je Stufe begrenzen die Zahl: bei ~1.000 Fällen ±0,016 — Stufen enger als ~0,04 sind nicht unterscheidbar |
| **Wozu die Stufe dient** | Einstieg ja/nein, Sperre, später evtl. Positionsgröße (Phase 2), Einordnung in der Mail — **nicht** die Hebelhöhe (K6); die Zahl q bleibt erhalten |
| **Erwartung** | mit den heutigen Beiträgen eher **3**; mit weiteren tragenden Beiträgen **5** möglich |

## 2f. ✔ K6 ENTSCHIEDEN (27.09.2026) — Hebelstufe aus der Liquidationsgefahr

Regelwerk: *„Einstieg misst gegen die CHANCE, Hebel gegen das RISIKO."* Das
Risiko ist die **Liquidation vor dem Ausstieg**. Prinzip:
**Volatilitätsskalierung** — der Liquidationsabstand muss deutlich größer
sein als der zu erwartende Gegenlauf.

Kontext aus E2i (2.667), 95. Perzentil des Rückgangs: unterstes ATR-Fünftel
7,0 % (24 h) / 12,6 % (72 h), oberstes 15,0 % / 23,3 % — gegen die
Orientierungswerte 5x ≈ −12 %, 3x ≈ −27 %, 2x ≈ −45 %.

| | Entscheidung |
|---|---|
| **Regel** | die **höchste Stufe (2x / 3x / 5x), deren vorhergesagte Liquidationswahrscheinlichkeit binnen der Haltedauer unter einer Grenze liegt** |
| **vorhergesagter Gegenlauf** | ATR zum Einstieg + Risikokurven (volumenschub, oi_aenderung, ema_abstand_atr) nach K1 |
| **Liquidationsabstand** | die echte Börsenformel (Wartungsmarge) — **nachzurechnen**, nicht die Orientierungswerte |
| **Kurs** | **Markpreis**, nicht Spot-Tief (K7) |
| **Haltedauer** | Achse 24 / 72 / 120 h, bis die Positionsführung sie festlegt |
| **Grenze** (z. B. ≤ 1 % Liquidationen) | **Nutzerentscheidung** nach der Tabelle je Grenze (welche Stufe wie oft, Ergebnis) |
| **Pflicht** | Kalibrierung **vorwärts**: vorhergesagte gegen eingetretene Liquidationen |
| **Signalstärke** | ✔ **Nutzer: zuerst R** (nur Risiko) messen; **R+S** (Risiko als Obergrenze, die Signalstufe darf darunter bleiben) als **Folgemessung und ggf. Optimierung** — lohnt nur, wenn starke Signale messbar **besser ausgehen**, nicht nur häufiger |
| **Wann** | erst, wenn die Kombination (Schritt 2) trägt |

## 2g. ✔ K7 ENTSCHIEDEN (27.09.2026) — Messbasis Binance

⭐ **Zwei Richtigstellungen beim Vorbereiten:** (1) die Orientierungswerte
5x ≈ −12 % · 3x ≈ −27 % · 2x ≈ −45 % sind **keine ungeprüften Altzahlen**,
sondern die Bitpanda-Formel `hebel_risk_gate.estimate_liquidation_price`
mit Wartungsmarge m = 0,09 — kalibriert an **vier echten Liquidationen**
(LINK, TAO, TAO, SUI, `importer/bitpanda_margin_positions.py`); dazu schiebt
die Finanzierung (0,18 %/Tag) die Liquidation je Haltetag näher (Mechanik
des Abstands, keine Gebühr in der Bewertung). (2) Gehebelt wird bei
**Bitpanda** — liquidiert wird an dessen Kurs, nicht am Binance-Markpreis.

**Nutzer:** *„Recherche kann man machen — tendiere aber für unsere Messungen
eher zu Binance und den Symbolen. Binance ist eine echte Börse, soweit ich
weiß, und BP ist ein Broker."*

| | Entscheidung |
|---|---|
| **Messbasis** | **Binance** — Börse mit eigener Preisbildung, die Symbole und Kurse, auf denen alle Messungen stehen |
| **Kurs für die Liquidation** | der **Binance-Markpreis** (Terminmarkt, über Börsen geglättet) als Maßstab, das **Spot-Tief** daneben als Vergleich — das Spot-Tief zählt Dochte (STX −70 % in einer Stunde, 2.667) |
| **Liquidationsformel** | die Bitpanda-Formel (m = 0,09, Finanzierung je Tag) — sie ist an echten Fällen kalibriert |
| **Prüfung** | Abgleich an den **echten Positionen** (188, davon 4 Liquidationen): hätte der gewählte Kurs dieselben ausgelöst — und keine anderen? Lesen nur `mode=ro`, Desktop-Kopie |
| **Recherche Bitpanda-Kurshistorie** | optional, nicht Voraussetzung |
| **Wann** | erst, wenn die Kombination (Schritt 2) trägt |
| ⚠️ **Grundgesamtheit** | gemessen auf 115 Binance-Symbolen; bei Bitpanda sind 43 für den Hebel freigegeben, nicht alle mit Stundenkursen — Stammsatz-Frage (S1–S6), bleibt eigene Aufgabe |

---

## 3. Der Prüfplan — Pflichtablauf plus zwei Lehren von heute

1. **Vorab festlegen** (im Kopf des Werkzeugs): Beitragsliste, Schwellen,
   Punktregel, Zielgrößen, Kriterium *trägt* — vor dem ersten Lauf.
2. **Kalibrierung nur aus der Vergangenheit** — rollierend 12 Monate;
   geprüft Monat für Monat 2024-01 bis 2026-08 (Maßstab) und auf 2022
   (unberührt, soweit die Daten reichen).
3. **Die Kombination gegen ihre Teile:** trägt die Summe **mehr** als der
   beste Einzelbeitrag? Das ist die eigentliche Frage von Ebene 2.
4. **Nullwelt** symboltreu; **Episoden**; **Bekanntheitszeitpunkt** je
   Beitrag.
5. **Gegenprüfung** P2 (1 h älter), P4 (Tausch), **P5 Zufallsbeiträge** —
   dieselbe Punktregel mit zufälligen Merkmalen statt der echten.
6. ⭐ **NEU (2.666):** für jedes **Tagesmerkmal** über die **Startstunden**
   mitteln — sonst misst eine Episodenregel nur Mitternacht.
7. **Je Asset** und **je Regime** ausweisen — *in jedem Regime funktionieren,
   wenn nicht, dann reden wir.*
8. **Ebene 3 nur, wenn Ebene 2 trägt:** Signalhäufigkeit je Asset, Ergebnis
   je Hebelstufe, Liquidationen.

---

## 4. Risiken und Fallen

| Falle | Gegenmittel |
|---|---|
| **Mehrfachtesten durch die Wahl der Kombination** — wer zehn Summen probiert, findet eine | die Punktregel wird **vorab** festgelegt; Varianten nur mit Bestes-von-N-Band und P5 |
| **Anpassung** der Gewichte an die Prüfdaten | K1: erst Punkte, keine Gewichte; Kalibrierung rollierend |
| **Wenige Beiträge** — Richtung hat heute nur funding (+/−) und eine Sperre | die Kombination kann nur zeigen, was da ist; trägt sie nicht, ist das ein Befund über die **Beitragslage**, nicht über das System |
| **Grundgesamtheit** — 115 Symbole mit Stundenkursen, nicht alle Hebelwerte (CANTON, FLOKI …) | die Messung gilt für diese Menge; der Stammsatz (S1–S6) bleibt eine eigene Aufgabe |
| **Live-Beschaffbarkeit** — funding im Betrieb nur als Einzelsatz, der Tageswert erst nach Tagesende | der Vortag ist live bekannt; gemessen wird die Form, die der Betrieb hat |
| **Betrieb zu früh** | Betriebsumstellung erst nach der ganzen Kette inklusive LLM-Rollen (Nutzervorgabe 27.09.) |

---

## 5. Was NICHT in diese Phase gehört

Betrieb am Notebook · LLM-Rollen · Positionsführung (Stop, Trailing,
Ausstieg) · Positionsgröße · Stammsatz/Neuaufnahme.

---

## 6. ✔ Abgestimmt (27.09.2026)

| # | Entscheidung | Abschnitt |
|---|---|---|
| K1 | Wirkungskurven (Regler), roh und selbstbezogen; Summe der Kurven; Wechselwirkungen als Suche mit Prüfung | 2a |
| K2 | Urteil gegen die Phase (eigene letzte 12 Monate); Kontrollen Moment und Tag; Teilung in Markt und eigen | 2b |
| K3 | Kontextfläche BTC × Dominanz zuerst, Zeitverschiebungs-Nullwelt; Klumpen → Phase 2 | 2c |
| K4 | q5/24 h als Ausgangsbasis, Höhe × Fenster als Achse, späterer Erfolg zählt | 2d |
| K5 | Schwelle auf kalibriertem q, Höhe durch den Nutzer nach der Tabelle | 2e |
| K5b | 3 bis 5 Stufen, so viele wie trennscharf, symmetrisch mit Sperren | 2e |
| K6 | Hebelstufe aus der Liquidationswahrscheinlichkeit; zuerst R, R+S als Folgemessung | 2f |
| K7 | Messbasis Binance, Markpreis vor Spot-Tief, Abgleich an echten Liquidationen | 2g |

➤ **Erster Schritt (nach der Prüfung in Abschnitt 7 geändert):** die
**Messbasis vervollständigen** — eingestellte Binance-Paare und BTC ab
2021-12 nachladen, Kernbefunde reproduzieren, mit gegen ohne vergleichen
(Ü1/Ü2, Befund 2.668). **Dann** K3, die Kontextfläche (3 × 3), und danach
Schritt 1 aus K1: die Wirkungskurven je Beitrag.

---

## 7. ⚠️⚠️ PRÜFUNG UND GEGENPRÜFUNG VON K1 BIS K7 (27.09.2026 abends)

**Nutzer:** *„mache noch eine Prüfung und Gegenprüfung der K1 bis 7."*
Geprüft gegen die stehenden Regeln (Regeln 1–4, Pflichtablauf § 6,
CLAUDE.md), auf Widersprüche zwischen den Punkten, die zitierten Zahlen und
die Datenlage. **Die Entscheidungen K1–K7 bleiben** — die Funde sind
Korrekturen an ihrer Umsetzung, und zwei betreffen die **Messbasis** selbst.

### 7a. ⛔⛔ Übergreifend — die Messbasis

| # | Fund | Beleg | Folge |
|---|---|---|---|
| **Ü1** | ⛔⛔ **ÜBERLEBENSVERZERRT.** `stundenkurse.db` enthält nur Paare mit Status `TRADING` — 116 Symbole, **kein einziges eingestelltes** | `hole_stundenkurse.py:117`; Abfrage: 0 von 116 Reihen enden vor 2026-09 | verstößt gegen die stehende Regel *„eingestellte Werte gehören dazu — ohne sie ist jede Messung überlebensverzerrt, und der Boden der Verteilung fehlt"* (CLAUDE.md, Kap. 120.3). Betrifft **alle** Neubau-Messungen 2.647–2.667 und die Richtungsdaten (der Lader nahm dieselben Symbole). Erwartete Richtung: Treffer **zu optimistisch**, Liquidationsgefahr **unterschätzt** — die Größe ist **ungemessen** |
| **Ü2** | ⛔ **BTC-Stundenkurse erst ab 2023-09-01** (die Alts ab 2021-12) | Abfrage: BTC 2023-09-01 bis 2026-09-24 | die Kontextfläche (K3) hat nur ~1.120 Tage; eine Prüfung auf 2022 ist für jeden BTC-Kontext unmöglich |
| **Ü3** | Grundgesamtheit Messung ≠ Betrieb: 115 Binance-Symbole gemessen, 43 bei Bitpanda für den Hebel freigegeben | 2.612, Stammsatz | jede Kurve zusätzlich auf der **Hebel-Teilmenge** ausweisen (Regel: *Betrieb und Messung dieselbe Grundgesamtheit*) |
| **Ü4** | die echten Positionen liegen **nur am Notebook** (Desktop-DB: `hebel_positions` 0 Zeilen) | Abfrage `mode=ro` | der Abgleich in K7 braucht eine **Kopie im Austauschordner** — keine Abfrage an der Produktion |

➤ **Gegenmittel Ü1/Ü2:** die eingestellten Binance-Paare und BTC ab 2021-12
aus dem Archiv nachladen (Kurse, Käuferanteil, Premium; funding und
Terminmarkt auf Vollständigkeit prüfen), dann die Kernbefunde **zuerst
reproduzieren** (R-R11) und **mit gegen ohne** Eingestellte vergleichen —
wie viele Urteile verschieben sich? (Prinzip `messe_grundgesamtheit.py`).
**Vor K3.**

### 7b. Zu den einzelnen Punkten

| # | Fund | Korrektur |
|---|---|---|
| **K1a** | getrennt gemessene Kurven einfach **summieren** zählt gemeinsame Information **doppelt** (korrelierte Beiträge, z. B. funding und konten_verh) | in Schritt 2 die Kurven **gemeinsam** schätzen (additives Modell) und gegen die Summe der Einzelkurven halten |
| **K1b** | eine Summe auf der **Wahrscheinlichkeits**skala kann über 0…1 hinauslaufen | auf der **Log-Odds**-Skala addieren (logistisch additiv), Ausgabe wieder als q — gilt auch für K5 |
| **K1c** | der Suchzeitraum für das Baummodell ist nicht festgelegt | Vorschlag: Suche 2023-09 bis 2024-12, Prüfung 2025-01 bis 2026-08 (und 2022, wo die Daten reichen) |
| **K1d** | 20 Stufen × Merkmale × zwei Formen = sehr viele Zellen — Mehrfachtesten über die Kurvenform | geurteilt wird über die **ganze Kurve** (ein Test je Kurve, z. B. Abweichung vom Nullband über alle Stufen), nicht je Stufe |
| **K2a** | ⚠️ **die Nullwelt passt nicht zum Phasen-Urteil:** symboltreu im selben Monat ziehen beantwortet die **Moment**-Frage | für die Phase eine **Zeitverschiebungs-Nullwelt je Asset** (Merkmalsreihe gegen die Ausgänge verschoben) — dieselbe wie in K3 |
| **K2b** | das 12-Monats-Normal braucht 12 Monate Vorlauf — junge Listings sind erst nach einem Jahr messbar, und im Betrieb fehlt ihnen das Normal | eine Regel für junge Assets festlegen (z. B. Marktnormal als gekennzeichneter Ersatz) |
| **K2c** | zwei Fenster, leicht zu verwechseln | **30 Tage** = Selbstbezug des Merkmals (K1) · **12 Monate** = Normal des Ausgangs (K2) |
| **K3a** | 5 × 5 Zellen × 3 Fenster ist bei ~1.120 Tagen **zu fein** (~45 Tage je Zelle) | **3 × 3** (Drittel) je Fenster; *seitwärts* = mittleres Drittel — gemessen, nicht gesetzt |
| **K4a** | bei ruhigen Assets (ATR < 4,6 %) wird ±5 % in 24 h selten erreicht — q5 steht dort auf wenigen Treffern | den Anteil *keine Grenze erreicht* je ATR-Fünftel ausweisen; der Ergänzungsausgang deckt diese Fälle ab |
| **K4b** | *späterer Erfolg zählt* (Nutzer), geurteilt wird auf 24 h | Pflicht: die Kurve darf bei 72 / 120 h das Vorzeichen **nicht drehen** |
| **K6a** | ⚠️ **Widerspruch K4 ↔ K6:** der Lehrer q5 endet bei −5 % — das wirkt wie ein Stop, und mit Stop bei −5 % liquidiert 2x–5x praktisch nie (nur über Lücken und Dochte). K6 setzt Halten **ohne** Stop voraus | das Hebelrisiko hängt an der **Ausstiegsregel** (Positionsführung). Beides messen: ohne Stop über die Haltedauer (obere Grenze) und mit Stop (Lückenrisiko) |
| **K6b** | die Wartungsmarge 0,09 stammt aus vier Fällen; die Bitpanda-Doku nennt 4,76 % bis 9,09 % | die Unsicherheit der Marge als **Band** mitführen |
| **K7a** | Markpreis gibt es nur für Terminmarkt-Paare | ✔ alle 115 haben einen Premium-Index, also einen Terminmarkt (CVC 21 Monate ohne) |
| **K7b** | die Zahl *188 Positionen* ist Stand 28.08. | an der Kopie nachzählen (Ü4) |

### 7c. Gegen die stehenden Regeln — ohne Befund

| Regel | Prüfung |
|---|---|
| 1 Takt ist nie Signalgeber | ✔ die Schwelle hängt nur an der Lage |
| 2 Gebühren nicht in die Bewertung | ✔ die Finanzierung geht nur in den **Liquidationsabstand** ein (Mechanik), nicht in q |
| 3 kein Asset-Rang beim Hebel | ✔ Stufen der Kurven sind absolute Werte; Urteil gegen das **eigene** Asset; der Markt-Bezug ist ausgeschlossen |
| 4 Fakt ist keine Begründung | ✔ *BTC gestiegen* ist ein Fakt — es wirkt nur über seine **gemessene** Kurve, nicht als Begründung |
| Pflichtablauf § 6 | ✔ alle zehn Schritte vorgesehen; ergänzt um die Startstunden (2.666) und die Zeitverschiebungs-Nullwelt (K2a/K3) |
