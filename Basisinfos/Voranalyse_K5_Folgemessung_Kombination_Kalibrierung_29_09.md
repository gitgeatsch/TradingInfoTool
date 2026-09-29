# Voranalyse K5-Folgemessung — Kombination, Kalibrierung, Normal-Schrumpfung, PBO, Wirkungskurven (29.09.2026)

**Nutzer:** *„JA, dein Vorschlag 1 und 3, und wenn möglich noch weitere Punkte — baue die Messung und führe diese auch gleich aus, ich bin dann einige Stunden nicht am Rechner."*
Dazu, zum Funding: *„oft sind Extremwerte eher als Risiko zu bewerten, aber der Beitrag selbst hat bis zu einem Bereich einen positiven Einfluss — das ist sauber einzuordnen."*

> **Urteil in einer Zeile:** eine Folgemessung auf **denselben Daten und Familien** wie K5 neu
> (`messe_k5_lage_vorlauf.py`). Sie ändert nichts an dessen Urteil. Sie prüft die Vorschläge
> aus der externen Recherche (Voranalyse K5 neu, Abschnitt 11). Kriterien vorab, Werkzeug vor
> dem Lauf committet.

---

## 1. Was gemessen wird

| # | Punkt (Recherche) | Messung |
|---|---|---|
| **F1** | Vorschlag 1 — Kombination | fünf Varianten auf denselben Familien (rsi; funding, oi, konten je drei Fenster): **K0** rsi allein · **K1** gleichgewichtete Summe der einzeln geschätzten Beiträge · **K2** Stacking auf dem Training (= K5 neu) · **K3** Stacking mit **nicht-negativen** Gewichten auf **Out-of-Fold**-Schätzungen (4 Zeitblöcke, 24 h Abstand) · **K4** alle Spalten **gemeinsam** in einem Modell (die Form, die in 2c verlor; Kontrolle) |
| **F2** | Vorschlag 3 — Kalibrierung | **Platt** auf dem Logit: Steigung aus bis zu **24 Monaten** ungesehener Schätzungen (mindestens 6), Achsenabschnitt aus den letzten **3 Monaten**; dazu Platt ohne Nachführung und die monotone Kalibrierung (3/12 Monate) aus K5 neu als Vergleich |
| **F3** | Vorschlag 5 — PBO | Wahrscheinlichkeit der Überanpassung über die fünf Varianten, CSCV über 8 Monatsgruppen |
| **F4** | Vorschlag 4 — Normal-Schrumpfung | Empirical Bayes: das Phase-Normal je Asset zur Mitte des Monats gezogen, im Verhältnis *wahre Streuung / (wahre Streuung + Schätzrauschen)* |
| **F5** | Nutzerhinweis — Wirkungskurven | die geschätzte Kurve je Beitrag und Fenster (12 Stufen, Log-Odds): Wo steigt sie, wo fällt sie an den Rändern? |
| – | Vorschlag 2 (Funding als Risiko für die Hebelstufe) | **nicht hier**: gehört in die K6-Folgemessung R+S |

---

## 2. Das Kriterium — vorab

| # | Bedingung | bei Nein |
|---|---|---|
| **S0** | R-R11: K0 (rsi allein) bitgleich zu 2.680 | nicht verwertbar |
| **S1** | ⭐ eine **der** Varianten K1/K2/K3 schlägt rsi allein: Differenz (eigenes Zehntel) über dem **Bestes-von-3**-Nullband (nur die Lage verschoben, 40 Ziehungen), feste Teilung **und** rollierend (gegen dasselbe Band, B1), in ≥ 3 von 4 Mengen | die Lage bringt in **keiner** Kombinationsform etwas dazu |
| **S2** | Auskunft: K4 (gemeinsam) gegen K1–K3 | – (bestätigt oder widerlegt die Diagnose aus 2.680) |
| **S3** | ⭐ Platt-Kalibrierung (F2) auf rsi allein und auf der besten der Varianten nach S1: Steigung 0,7–1,3 **und** oberstes Zehntel \|geschätzt − beobachtet\| ≤ 0,02 | die Höhe bleibt unkalibriert → K5-Stufen nur als Rangstufen, nicht als Wahrscheinlichkeit |
| **S4** | Zeit: die Variante aus S1 in jedem Jahr 2024/2025/2026 und 2022 positiv | nicht zeitstabil |
| **S5** | Auskunft PBO: ist die im Training beste Variante außerhalb meist unter dem Median? | – (PBO > 0,5 heißt: Auswahl unter den Varianten ist Überanpassung) |
| **S6** | Auskunft F4 — die **Abnahmeprobe muss fehlschlagen können**: Auswahl des obersten Normal-Zehntels je Monat. Roh liegt das beobachtete q **unter** dem Normal (Rückkehr zur Mitte, 2.678). Mit dem geschrumpften Normal muss der Abstand **mindestens halbiert** sein | die Schrumpfung behebt die Rückkehr nicht |
| **S7** | Auskunft F5: Kurvenform je Beitrag | – |

⚠️ **Mehrfachtesten:** Drei Kombinationsvarianten gegen **ein** Bestes-von-3-Band, nicht je Variante
einzeln. K4 geht nicht ins Band, es ist nur Kontrolle.

⚠️ **Dieselbe Prüfzeit** wie K5 neu. Jedes *trägt* ist ein **Kandidat** bis zu neuen Monaten (Z6)
und der Simulation.

---

## 3. Bauentscheidungen (vor dem Lauf)

| # | |
|---|---|
| **B1** | Out-of-Fold für K3: dieselben 4 Zeitblöcke wie die Kreuzvalidierung, 24 h Abstand; die Dämpfung je Familie aus der vollen Schätzung (keine verschachtelte Kreuzvalidierung) |
| **B2** | Die Nullwelt für S1 schätzt die drei Lage-Familien je Ziehung neu, rsi bleibt echt; K4 läuft nicht in der Nullwelt (Rechenzeit, Kontrolle) |
| **B3** | Platt: Steigung aus der ganzen verfügbaren ungesehenen Vorgeschichte bis 24 Monate (mindestens 6), Achsenabschnitt aus 3 Monaten bei fester Steigung; nur Ausgänge, die vor dem Zielmonat bekannt waren |
| **B4** | Normal-Schrumpfung: effektive Zahl unabhängiger Ereignisse je Asset = Trefferrate × 365 (ein Ereignis je Tag), Schätzrauschen q(1−q)/n, wahre Streuung = Querschnittsvarianz − mittleres Rauschen (≥ 0), je Monat |
| **B5** | Reihenfolge: nach K5 neu (Kette), Werkzeugtest → vier Mengen; nie zwei große Rechnungen zugleich |

---

## 4. Was NICHT folgt

Kein Betrieb, keine Hebelstufe, keine Änderung an K5 neu. Die Ergebnisse zeigen, **wo** wir
ansetzen (Nutzer), und werden vorgelegt.

---

## 5. ⚠️ Nachtrag VOR der Auswertung (29.09.2026, 03:40) — das K5-Tor ist nicht bestanden

S1 stützte sich auf das Tor von K5 neu (gleiche Familien, gleiche Statistik). Dieses Tor ist **nicht bestanden** (2.682: +0,04 in 3 von 5). Darum, festgehalten **bevor** ein Ergebnis der Folgemessung gelesen wurde:

| | |
|---|---|
| **S1** | gilt nur als **Auskunft**, bis ein eigenes Tor für die Varianten K1–K3 bestanden ist |
| **Tor der Folgemessung** | nach der Kette, eigener Lauf (`--tor`, Menge bestand): gepflanzt +0,04 auf dem obersten Zehntel von `oi_24` (Lage verschoben), gemessen an der **Bestes-von-3**-Differenz gegen rsi allein, 40 Ziehungen; bestanden bei ≥ 4 von 5 |
| S2–S7 | unberührt (Kalibrierung, PBO, Schrumpfung, Kurven hängen nicht an diesem Tor) |

Die Vorabfestlegung wird **nicht** geändert, nur ihre Gültigkeit für S1 eingeschränkt. Die Kette läuft unverändert weiter.

---

## 6. Ergebnis (29.09.2026) — Befund 2.683

Beleg `Basisinfos/K5_Folge_29_09/`. R-R11 bitgleich in allen vier Mengen.

| | Ergebnis |
|---|---|
| **Tor** (Nachtrag) | ⛔ +0,04 in 1 von 5 — die nicht-negativen Gewichte setzen die Lage auf 0. **S1 nur Auskunft** |
| **S1** (Auskunft) | keine Variante schlägt rsi allein, in keiner Menge, fest wie rollierend; K4 gemeinsam etwa gleich |
| **S4** Zeit | ✔ rsi allein in 4 von 4: jedes Jahr, jede BTC-Lage, **2022 +0,014..+0,022**, jedes Normal-Drittel, 84–90 % der Assets |
| **S3** Kalibrierung rsi allein | **roh** Steigung 0,77 / 0,69 / 0,73 / 0,71, Niveau ±0,006 → fast kalibriert · Platt ohne Nachführung ✔ in 2 von 4 · ⛔ **Platt mit 3-Monats-Achsenabschnitt in 4 von 4** (Niveau kippt: geschätzt +0,08, beobachtet −0,04) |
| **S6** Schrumpfung | ✔ in 4 von 4 (roh −0,036..−0,042 → geschrumpft +0,002..+0,011); Schrumpfungsfaktor 0 bis 0,53: das Phase-Normal ist **größtenteils Rauschen** |
| **S7** Kurven | rsi steigend; funding fallend (Extreme oben Risiko); oi fallend; **konten am stärksten** (wenige Longs +0,15, viele −0,25); leichtes Optimum bei ko_48/fu_48 |
| **S5** PBO | ⛔ **nicht auswertbar** — Auswahlanteil nicht angeglichen (eigener Fehler) |

---

## 7. Gegenprüfung (Nutzer 29.09.: *„kannst du zur Sicherheit die letzten Messungen noch einmal prüfen und gegenprüfen"*) — vorab festgelegt

**Der Verdacht, aus S6:** Das Phase-Normal ist größtenteils Rauschen. Assets mit **niedrigem** Normal liegen darum
ohne jedes Signal über ihrem Normal (unterstes Zehntel roh +0,06). Wählt rsi bevorzugt solche Assets, wäre ein Teil
des rsi-Effekts (2.680, 2.683) nur **diese Verzerrung**. Die Frage: *Hält rsi allein auch gegen das geschrumpfte
Normal?*

| # | Bedingung | bei Nein |
|---|---|---|
| **G1** | feste Teilung: Dq der rsi-Auswahl (eigenes Zehntel) gegen das **geschrumpfte** Normal über dem 90. Perzentil der Nullwelt (rsi verschoben, 40 Ziehungen, ebenfalls gegen das geschrumpfte Normal), in ≥ 3 von 4 Mengen | der rsi-Effekt ist zum großen Teil Normal-Verzerrung → 2.680/2.683 einschränken |
| **G2** | rollierend (gleicher Anteil) gegen das geschrumpfte Normal > 0 in **jedem** Jahr 2024/2025/2026, in ≥ 3 von 4 | nicht zeitstabil gegen den richtigen Bezug |
| **G3** | in **jedem** Drittel des Normals > 0 (gegen das geschrumpfte Normal), in ≥ 3 von 4 | der Effekt sitzt in einer Normal-Lage |
| **G4** | Auskunft: wie viel des Effekts auf die Verzerrung entfällt (roh minus geschrumpft), und derselbe Abstand für eine **Zufallsauswahl** | – |

Werkzeug: `messe_k5_folge.py --gegen` (Schrumpfung wie F4/B4), vier Mengen, nacheinander.
