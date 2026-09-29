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
