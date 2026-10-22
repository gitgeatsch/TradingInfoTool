# Bestandsaufnahme: Was trägt vor Kosten, was nach Kosten? (Stand 22.10.2026)

**Wozu:** Nutzer 22.10.: *„ja A1 Bestandsaufnahme starten, prüfen, gegenprüfen und Doku – mit Alternativen meine ich nicht nur Anpassungen der bestehenden Strategien, sondern auch neue Ansätze, welche wir nicht betrachtet haben – aber mach zuerst die Prüfung A1.“*

Dieses Blatt stellt jeden Strang auf **eine** Zeile:
- Wie groß ist der Vorteil **vor** Kosten?
- Was kosten die Handel?
- Bleibt **nach** Kosten etwas?
- Gibt es einen Hebel, der eine Lücke schließen **könnte**?

Ein Hebel wird nur dann gemessen, wenn er die Lücke **rechnerisch** schließen kann (Vorgabe A1, Chat 22.10.). Die Rechnung dazu ist eine **Obergrenze in der Rückschau**, keine Messung einer neuen Regel.

## 1. Alle Stränge auf einen Blick

| Strang | Vorteil vor Kosten | Kosten | nach Kosten | Quelle |
|---|---|---|---|---|
| **Hebel REGEL0** (Kern + Ruhe 48 h + J) | **+0,30 %** je Handel (unverzerrt, 2025-26; bestand +0,55 %, überlebensverzerrt) | **0,48 %** je Tageshandel (0,30 % Gebühr + 0,18 %/Tag Finanzierung) | **−0,17 bis −0,19 Pp** je Handel | 2.690, 2.694, 2.698; hier §2 |
| Spot Altcoins **Einstieg** (Momentum, Ruhiger Boden, Listings, Bodenkauf, Zyklus) | **keiner** gegen BTC | 0,36 / 0,88 / 3,20 % halbe Spanne je Seite (H/M/S) | — | Spot §15–§20, §37, §38, §40 |
| Spot Altcoins **Grundrate** | Korb ab 2024 −57 % gegen BTC auf 365 T; 6 % der Altcoins vor BTC | — | — | Spot §10.8 |
| Spot **Mitnahme ×3** | **+4,9 Pp** gegen Halten (besser als Zufall) | ein Verkauf, nachrangig | **trägt**, als **Schadensbegrenzung**, nicht als Ertrag gegen BTC | Spot §31.6, §39.6; gebaut (B1) |
| Spot **Watchlist** (Asymmetrie) | ordnet den **Fortbestand** innerhalb der Klasse (+13,9 Pp, Rang 1,000) | selten gehandelt | ordnet, ist aber **kein** Kaufsignal; findet Ausbrüche nicht (Lift 0,99) | Spot §25.6, §30 |
| **Akkumulation** BTC/ETH/SOL | regelmäßiges Kaufen ist **nicht zu schlagen** (F1–F3); 70/20/10 = 1,00 × BTC | gering | Grundlage, kein Mehrertrag | Spot §8, §12 |
| **Season-Ampel** / Trendallokation | Ampel beschreibt Phasen (Holdout trägt); **als Zeitpunkt trägt nichts** (M-A) | gering | Fakt, keine Handlung | Spot §59, §60 |
| **LLM-Komponente** | auf elf Wegen kein Mehrwert | API frei | — | E-125 |
| **Grid** | Rückkehr zur Mitte ≈ 0,02–0,03 % je Ausführung | 0,25 % je Ausführung | ≈ −0,22 % | E-127 |

⇒ **Nur ein Strang hat einen echten Vorteil vor Kosten, der als Ertrag gemeint ist: die REGEL0.** Ihre Lücke zu den Kosten beträgt rund **0,18 Pp je Handel**. Die Spot-Stränge haben vor Kosten gegen BTC keinen Vorteil; Mitnahme ×3 und Watchlist begrenzen den Schaden.

## 2. Die Hebel für die REGEL0-Lücke, nachgerechnet (`Rechenkern_02_10/a1_hebel_rechnung.py` → `.txt`)

**Grundlage:** REGEL0-Einstiege 2025-01 bis 2026-08, vier Mengen, 24-h-Ertrag wie O21.
- **R-R11:** Die Menge `bestand` reproduziert die Referenz **+0,545 %** (Schritt7 §23.64: +0,55 %).
- Die Mengen `unverzerrt` liegen bei +0,30 / +0,30 / +0,31 %, stimmig zu 2.694.

| Hebel | Rechnung (Obergrenze, Rückschau) | Lücke danach (unverzerrt 1 / 2 / 3) | Urteil |
|---|---|---|---|
| **K1 Fusion ohne Hebel** | Kosten 2 × 0,25 % = **0,50 %**, also mehr als die heutigen 0,48 %. Die Staffel 0,21 % gilt erst ab 100.000 € Umsatz in 30 Tagen, bei Einsätzen von 300–750 € unerreichbar | schlechter | ✘ |
| **K2 Haltedauer 12 h** | Mittel bei 12 h fast gleich wie bei 24 h (+0,30 / +0,32 / +0,28 %). Würde die Finanzierung **je Stunde** abgerechnet, kostete der Handel 0,39 % | −0,09 / −0,07 / −0,11 Pp | ✘ (und wie Bitpanda abrechnet, ist eine **offene Faktfrage**) |
| **A1 Sperre bei Signalflut** | ohne Einstiege mit vielen Signalen in den 24 h davor (N24 ≥ P70 / P80 / P90; nur frühere Stunden, vorab beobachtbar) | bestenfalls **−0,04 Pp** (P70: −0,04 / −0,09 / −0,06); die Dosis ist nicht stetig | ✘ |
| **K2 + A1 zusammen** | 12 h halten und Sperre P70/P80, gegen 0,39 % | **−0,03 bis −0,08 Pp** in allen vier Mengen | ✘ |
| A2 Monate mit wenig Information (K_IG) | schon gemessen (2.697): ohne diese Monate +0,38..+0,59 %, aber **statistisch schwach** (nur in einer Menge jenseits der Nullwelt); vorwärts erst nach Jahren entscheidbar | — | ✘ (keine Jahreslösung, E-18.10.) |
| A3 Wucht (beide Merkmale oben) | schon gemessen (2.692–2.694): hebt die **Bewegung**, nicht die Richtung; der Spiegel fällt | — | ✘ |

⚠️ **Zur Unsicherheit:**
- Die Tagesblock-Breite des Mittels beträgt **±0,5 Pp** (Gegenprobe G3: Formel ±0,50, Bootstrap ±0,52).
- Die Lücke ist mit 0,18 Pp kleiner als diese Unsicherheit. Auch ein Hebel, der sie in der Rückschau schlösse, wäre damit **nicht nachweisbar**; schon §23.64 hielt das fest.
- Hier schließt **keiner** sie, nicht einmal als Obergrenze in der Rückschau.

**Gegenprobe 4/4** (`a1_hebel_gegenprobe.py` → `.txt`):
- G1: 24-h-Ertrag direkt per SQL, 300/300 gleich.
- G2: N24 durch Abzählen, 300/300 gleich.
- G3: Tagesblock-Breite über Formel und Bootstrap, gleich.
- G4: R-R11, +0,545 %.

⚠️ **Eigener Fehler dabei, behoben:**
- Meine Gegenprobe hieß zuerst `a1_gegenprobe.py` und überschrieb damit eine **eingecheckte** Gegenprobe gleichen Namens (Schritt7 §23.14, LLM-A1).
- Die alte Datei ist aus git wiederhergestellt und unverändert; die neue heißt `a1_hebel_gegenprobe.py`.

## 3. Ergebnis

| | |
|---|---|
| **Was trägt** | **vor** Kosten nur die REGEL0, und zwar als Rückkehr nach starkem Rückgang, gemessen über alle Coins |
| **Was fehlt** | rund **0,18 Pp je Handel**. Weder Kosten (Fusion, Haltedauer) noch Auswahl (Signalflut, Informationsmonate, Wucht) schließen das, auch nicht zusammen und auch nicht in der Rückschau |
| **Was netto trägt** | **Mitnahme ×3** im Spot, als Schadensbegrenzung; das regelmäßige Kaufen der Kernwerte als Grundlage |
| ⇒ **für den nächsten Schritt** | Innerhalb der **bestehenden** Ansätze ist mit den freien Daten und den heutigen Kosten kein Weg mehr offen. Was bleibt, sind **neue Ansätze**: andere Ertragsquellen, nicht noch eine Anpassung (Nutzer 22.10.) |

**Betrieb:** unverändert. Die REGEL0 läuft weiter als Vorwärtsprotokoll mit kleinen Einsätzen; die Freigabe galt ausdrücklich *„nach Kosten nicht als gewinnbringend belegt“* (Schritt7 §23.38, E-94).

**Nachtrag 22.10.2026:** Die offene Faktfrage zu K2 ist geklärt. Bitpanda berechnet die Margin-Finanzierung **alle 4 Stunden**, 0,03 % je 4 h in Tag 1–60 (Kostendokument v4.0.0 vom 08.07.2026, `Recherche_Neue_Ansaetze_22_10.md` §5.3). 12 h kosten damit 0,09 %, die Rechnung mit 0,39 % stimmt, und das Urteil *schließt nicht* bleibt.
