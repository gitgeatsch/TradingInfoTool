# Voranalyse K5 — die Schwelle: ab wann ist ein rsi-Signal ein Signal? (29.09.2026)

**Nutzer:** *„ja, K5 Voranalyse schreiben — prüfen und gegenprüfen. Ich stimme dir nur unter Protest zu: wenn das die
Realität ist, dass wir nur die Tachonadel als Einstieg nutzen, dann soll es so sein. Im Umkehrschluss bedeutet es, in
ein fahrendes Auto aufzuspringen und zu hoffen, dass man es schafft."*

> **Urteil in einer Zeile:** K5 legt fest, **ab welchem Vorsprung** rsi ein Signal gibt und ob es **Stufen** und eine
> **Sperre** gibt — auf der Einstiegsregel, die in jeder Phase und jedem Wetter trägt (2.685, 2.686). Die Höhe der
> Schwelle wählst **du** nach einer Tabelle, in zwei Schritten: erst auf 2024, dann **einmal** bestätigt auf 2025–26.

---

## 0. Dein Einwand — festgehalten, nicht weggeredet

| | |
|---|---|
| **Richtigstellung** | der Einstieg ist **nicht** die Tachonadel (der Kursanstieg), sondern **rsi** (die Stärke der Bewegung gegen das eigene Normal des Assets). Die Nadel spielt **keine** Rolle (2.685) |
| **„aufspringen und hoffen“** | *Aufspringen* — ja: rsi ist ein **Fortsetzungs**-Einstieg, das Auto fährt schon. *Hoffen* — nein: gemessen ist, dass im obersten Zehntel **+5 % vor −5 %** rund **5–8 Prozentpunkte öfter** eintritt als im eigenen Normal des Assets, in jedem Jahr, jeder Phase, jedem Wetter. Das ist ein kleiner, belegter Vorteil, kein sicherer |
| **was das Aufspringen absichert** | nicht das Signal, sondern **Rolle C** (die ATR bestimmt die Hebelstufe, 2.681) und die **Positionsführung** (Stop, Ausstieg, Phase 5) |
| **was fehlt** | der Einstieg **vor** der Bewegung (OPTIMUM). Mit den vorhandenen Kurs- und Terminmarktdaten nicht gefunden (2.650, 2.657, 2.665, 2.673, 2.675, 2.685). ➤ Der abgestimmte **Suchpfad „A vorher — nur mit neuer Datenquelle“** bekommt einen **festen Platz im Plan** nach K5 (Abschnitt 8) |

---

## 1. Was bringt das für das Ziel?

| wenn K5 … | dann | fürs Ziel |
|---|---|---|
| **kalibriert** ist und die Tabelle trägt | aus *„die Chance ist erhöht“* wird *„die Chance liegt bei q, das ist x über dem Normal“* — eine **Zahl** je Signal, dieselbe Bedeutung für jedes Asset | der erste Teil von **Potential**: *wie wahrscheinlich* |
| **Stufen** trennscharf sind | *Signal* und *starkes Signal* bedeuten messbar Verschiedenes | Abstufung nach Potential (später Positionsgröße, Phase 2) |
| eine **Sperre** trägt (Umkehr unten) | ein Zustand, in dem *nicht* eingestiegen wird, weil es messbar schlechter läuft | weniger Fehleinstiege |
| **nicht kalibriert** ist | die Zahl q darf **nicht** in die Mail und nicht in die Größe — nur die Ordnung (*besser/schlechter*) | Rückschritt auf *ja/nein* |

---

## 2. Was abgestimmt ist — und was schon gemessen ist

| | |
|---|---|
| **K5 (27.09.)** | Schwelle **absolut**, kein Rang (*muss auch bei EINEM Asset funktionieren*); **Kalibrierung vorwärts Pflicht**; die **Höhe wählt der Nutzer nach einer Tabelle**, *im Suchzeitraum gewählt, einmal auf dem ungesehenen bestätigt*; Hebelstufe nicht hier (K6) |
| **K5 geändert (28.09., vorläufig)** | Schwelle auf dem **Beitrag** = Vorsprung gegen das **eigene** Normal; das Normal ist nur Bezugspunkt |
| **K5b** | **3 bis 5 Stufen**, symmetrisch mit Sperren (*Sperre · neutral · Signal* bis *starke Sperre … starkes Signal*); Trennschärfe benachbarter Stufen **direkt** getestet; enger als ~0,04 nicht unterscheidbar |
| **2.680** | der Kombinations-Beitrag ist **nicht kalibriert** (Steigung 0,42–0,55) und nicht besser als rsi allein → K5 neu vorlegen |
| **2.683** | rsi allein **roh fast kalibriert** (Steigung 0,69–0,77, oberstes Zehntel ±0,006); Platt ohne Nachführung 2 von 4; **kurz nachgeführter Achsenabschnitt scheitert**; das Normal ist meist Rauschen → **geschrumpftes** Normal |
| **2.684** | zeitstabil nur in der **Betriebsform** (Grenze aus dem Training); 2024 schwach |
| **2.685 · 2.686** | keine Phasenregel, keine Wetterregel nötig — rsi trägt überall |
| **K6 S Stufe 1** | im obersten Zehntel sticht nur **P98–100** heraus (+0,079 gegen +0,035..+0,059), nur 2025 → *starkes Signal* ist fraglich |

---

## 3. Der Aufbau

| | |
|---|---|
| **Signal** | rsi allein (Modell aus rsi jetzt und 24 h alt), **rollierend** je Monat nur auf der Vergangenheit geschätzt, 2024-01 bis 2026-08 — dieselbe Auswahlrechnung wie W2 |
| **Beitrag** | der geschätzte Vorsprung in **Prozentpunkten**: **v̂ = q̂ − Normal**, mit q̂ = expit(logit(geschrumpftes Normal) + Beitrag des Modells) |
| **Kalibrierung** | v̂ gegen den beobachteten Vorsprung (Dq gegen das geschrumpfte Normal), je Zehntel von v̂ |
| **Tabelle** | je Schwelle **v̂ ≥ +0,02 · +0,04 · +0,06 · +0,08**: Anteil der Anker, **Signale je Asset und Monat**, beobachteter und geschätzter Vorsprung, je Jahr |
| **Sperre** (unten) | je Schwelle **v̂ ≤ −0,02 · −0,04**: beobachteter Vorsprung — eine Sperre nur bei **Umkehr** (deutlich negativ), sonst gibt es keine Sperrstufe |
| **Zwei Schritte** (K5, 27.09.) | das Werkzeug zeigt **zuerst nur 2024** (Wahl); du wählst die Schwelle; **danach** einmal 2025-01 bis 2026-08 (Bestätigung, `--bestaetigen <Schwelle>`) — ich sehe die Bestätigungszahlen vorher **nicht** |
| **Nullwelt · Tor** | feste Teilung (Suche → Prüfzeit), rsi je Asset verschoben, 40 Ziehungen; Tor als **Leiter** (+0,04 / +0,08) für den Stufenunterschied |
| **Menge** | **Stufe 1: `bestand`** — die übrigen drei nur, wenn K5-1 trägt |

---

## 4. Die Kriterien — vorab

| # | Bedingung | bei Nein |
|---|---|---|
| **K5-0** | R-R11: rsi allein +0,0808 (fest); die rollierende Auswahl wie W2 (29.390 Anker im obersten Zehntel) | nicht weiter |
| **K5-1** ⭐ | **kalibriert vorwärts** auf 2024: Steigung v̂ → beobachtet 0,7–1,3; oberstes Zehntel \|geschätzt − beobachtet\| ≤ 0,02 | **keine** Zahl q in Mail oder Größe; nur die Ordnung — **reden** |
| **K5-2** | Tabelle je Schwelle (2024) — **keine** Schwelle von mir gesetzt | – |
| **K5-3** | Sperre nur, wenn v̂ ≤ −0,04 beobachtet **unter** dem Nullband liegt (Umkehr) | keine Sperrstufe → 2 Stufen (*neutral · Signal*) |
| **K5-4** | *starkes Signal* nur, wenn der Unterschied zur Signalstufe ≥ 0,04, über dem Nullband **und** über der Auflösung der Leiter liegt | höchstens eine Signalstufe |
| **K5-5** (nach deiner Wahl) | Bestätigung 2025–26: die gewählte Schwelle hat beobachteten Vorsprung > 0 **in beiden Jahren** und bleibt kalibriert (Steigung 0,7–1,3) | die Schwelle wird **nicht** übernommen — neu abstimmen |

⚠️ **Mehrfachtesten:** vier Signalschwellen und zwei Sperrschwellen werden **gezeigt**, nicht getestet — die **Wahl** triffst
du auf 2024, bestätigt wird **eine**.
⚠️ **Regel 1:** die Häufigkeit (Signale je Asset und Monat) ist **Folge**, kein Ziel.

---

## 5. Zur Abstimmung (S1–S7)

| # | Punkt | Empfehlung |
|---|---|---|
| **S1** | Signal | rsi allein, rollierend (Betriebsform) |
| **S2** | Maß der Schwelle | Vorsprung **v̂ in Prozentpunkten** gegen das **geschrumpfte** Normal (lesbar: *+0,05 = fünf Punkte öfter +5 % vor −5 %*) |
| **S3** | Tabelle | Schwellen +0,02 / +0,04 / +0,06 / +0,08, Sperre −0,02 / −0,04 |
| **S4** | zwei Schritte | Wahl auf 2024, **einmal** bestätigt auf 2025-01 bis 2026-08 |
| **S5** | Kriterien | K5-0 bis K5-5 wie Abschnitt 4 |
| **S6** | Stufe 1 | nur `bestand` |
| **S7** | Plan | nach K5: **H0** (Liquidationsgefahr auf dieser Auswahl) → **Simulation Ebene 3** → **Suchpfad A vorher mit neuer Datenquelle** (eigene Voranalyse: welche Quellen es gibt, was schon gemessen ist) |

---

## 6. Prüfung und Gegenprüfung

| Prüfung | Ergebnis |
|---|---|
| gegen die Abstimmung K5/K5b | ✔ absolut, Kalibrierung Pflicht, Höhe durch dich nach Tabelle, Wahl und **einmalige** Bestätigung, 3–5 Stufen mit Sperre nur bei Umkehr |
| gegen *K5 geändert* | ✔ die Schwelle liegt auf dem **Beitrag** (v̂), das Normal ist Bezug |
| Vorgriff | ✔ rsi je Monat nur auf der Vergangenheit; geschrumpftes Normal je Monat nur aus dem Querschnitt der Normale |
| Beitrag auf welchem Normal? | ⚠️ das Modell schätzt den Beitrag mit dem **rohen** Normal als Versatz; hier wird er auf das **geschrumpfte** gesetzt. rsi hängt kaum am Rauschen des Normals (2.684: Verzerrungsanteil ~0), die Übertragung ist also plausibel — **geprüft wird sie genau von K5-1** |
| Fokus ab 2024 | ✔ Wahl 2024, Bestätigung 2025–26; 2022 nur Gegenprobe (Auskunft) |
| Kleine Läufe | ✔ volle Daten; eine Menge — Stufe 1 |
| *2024 schwach* (2.684) | ⚠️ die **Wahl** fällt ausgerechnet auf das schwächste Jahr — das macht die Wahl **vorsichtig**, nicht zu mild; offen ausgewiesen |
| Was folgt NICHT | kein Betrieb (erst nach der ganzen Kette inkl. LLM-Rollen); keine Hebelstufe (K6); keine Mail-Änderung (eigene Abstimmung) |

---

## 7. Umfang

Werkzeug (Modus `--k5` in `messe_losfahren.py`) bauen und vorab committen · ein Lauf `bestand`, etwa **30–40 Minuten**
· Stopp · Tabelle 2024 an dich · nach deiner Wahl ein kurzer Bestätigungslauf.

---

## 8. Der Plan danach (zur Bestätigung, S7)

| # | Schritt | wozu |
|---|---|---|
| 1 | **K5** | ab wann ist ein Signal ein Signal |
| 2 | **H0** | ist die Liquidationsgefahr auf **dieser** Auswahl so, wie die ATR sagt |
| 3 | **Simulation Ebene 3** | läuft die ganze Regel (Einstieg, Hebel, Stop) vorwärts auf 2024–26 |
| 4 | ⭐ **A vorher — neue Datenquelle** | dein Einwand: vorhanden sind z. B. aktive Adressen und Umlaufmenge (täglich, `onchain_historie.db`); ob gemessen, und welche Quellen (Optionen, Liquidationen, Börsenzuflüsse) frei verfügbar sind, prüft eine eigene Voranalyse |
| 5 | neue Monate ab 2026-09 | die Regel eingefroren, echter ungesehener Nachweis |

---

## 9. ✔ ABGESTIMMT UNTER PROTEST (29.09.2026) — S1 bis S7; dazu ein neuer Einwand

**Nutzer:** *„OK — S1 und S7 weiter unter Protest. Wie sollen wir auf ein fahrendes Auto aufspringen, wenn diese
Anstiege durch unser System mit Prüftakt und Cooldown bereits auf 150 sind, ohne dass wir echte und gute Signale haben?
Ein steigender RSI ist wie: ich schau aufs Mobiltelefon, sehe, der Kurs steigt, und reite die Welle, solang es dauert,
auf gut Glück."*

**Am Code nachgesehen (Betrieb):** `HEBEL_SCREENING_INTERVAL_MINUTES = 15` (scheduler/background.py) — geprüft wird alle
**15 Minuten** auf Stundenkerzen; der **Cooldown** (3,5 h, `budget_allocator.cooldown_stunden`) greift erst **nach** einem
Signal auf demselben Asset, er verzögert das **erste** nicht. Der Verzug bis zum Einstieg liegt damit bei rund
**0–75 Minuten** nach dem Stundenschluss.

**Was schon gemessen ist:**

| Einwand | Befund |
|---|---|
| *„schon auf 150“* | der Einstieg mit einem **1–2 h alten** rsi-Signal trägt noch +0,030..+0,050, mit einem **24 h alten** +0,049..+0,062 (Prüfzeit, 2.676) — ein Verzug von Stunden macht das Signal nicht wertlos. Nach > 1 ATR Anstieg trägt die Auswahl sogar **mehr** (2.685) |
| *„Kurs steigt, aufs Handy schauen“* | das ist die **Tachonadel** — und genau die ist gemessen: *alle* Anker mit demselben Anstieg gegen die rsi-Auswahl im selben Anstieg: rsi bringt **zusätzlich** rund +0,05..+0,07 (2.685, Tabelle je Klasse; ⚠️ als Differenz nachträglich gelesen). rsi ist **nicht** „der Kurs steigt“, sondern *„für dieses Asset ungewöhnlich stark, gemessen an seinen eigenen 30 Tagen“* — das zeigt kein Handy |
| *„auf gut Glück“* | ein **kleiner** Vorteil, kein Glück — aber ob er nach Gebühren, Hebel und Stop **etwas einbringt**, zeigt erst die **Simulation** (Plan Schritt 3). Fällt er dort durch, fällt die Regel |

**⭐ Eine echte Lücke, die dein Einwand aufdeckt:** gemessen wird der **Zustand** (rsi oben, an festen Ankern alle
6 h); der Betrieb löst beim **ersten Überschreiten** der Schwelle aus. Ob der **Ersteintritt** so viel trägt wie der
Zustand, ist **nicht gemessen**.

➤ **Vorschlag K5-6 (zur Abstimmung, noch nicht gebaut):** im selben Lauf zusätzlich der **Ersteintritt** — die erste
Stunde, in der v̂ die Schwelle überschreitet (davor 24 h darunter) — mit Einstieg **eine Stunde später** (Betriebsverzug,
aufgerundet). Kriterium: der Vorsprung am Ersteintritt ist in 2024 **> 0** und **nicht kleiner als die Hälfte** des
Zustandswerts. Bei Nein: die Betriebsform (Auslösen am Überschreiten) muss **geändert** werden, bevor K5 gilt.
