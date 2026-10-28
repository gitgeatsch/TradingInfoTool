# Messplan H-1 „Lagegerechte Handlung“ — VORAB festgelegt (28.10.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Bezug:** Konzept `Basisinfos/Konzept_Lagegerechte_Handlung_27_10.md` §5.3 und §6.5 · Entscheidung E-165.
**Stand:** vorab committet, **bevor** ein Werkzeug gebaut oder ein Ergebnis angesehen wird. Jede spätere Änderung erscheint als **Fassung 2** mit Ursachenbegründung und nicht still.

**Nutzerfestlegungen:**
- 27.10.: beide Stränge, nur Long, Haltedauer 24 h bis 5 T und länger, bis die Führung schließt.
- 28.10.: L5 ohne „nach oben“, L2 nur Fakt, L8 in den Spot-Strang, *„unsicher bei allen Punkten“* (die Messung entscheidet).
- 28.10. zu Rückenwind je Trade: *„ja a – ist sicher der kurzfristig relevantere Bereich, aber B und C finde ich nicht falsch“*.


> ## ⚠️ FASSUNG 2 (28.10.2026, vor jedem Werkzeug und jedem Ergebnis)
>
> **Anlass:** Nutzerfrage *„hast du unser Konzept mit dem Gesamtplan abgeglichen bzw. adaptiert?“*. Der Abgleich mit `Plan_Schritt59` (Nachträge 79–82) und den Entscheidungen fand zwei Überschneidungen:
>
> | | Fassung 1 | Abgleich | Fassung 2 |
> |---|---|---|---|
> | **H-1a** Größe nach Schwankung | Positionswert ∝ ATR̄/ATR gegen fest | **ist V-1** (E-157/E-158, vorab 857c9b9e): Positionswert ∝ 1/ATR gegen fest, Nullwelt Größen je Tag vertauscht. Ergebnis: Bremse ohne Ertragsverlust, **NICHT TRENNBAR**. Eine Wiederholung auf derselben Basis brächte nichts Neues (R-R11; Nutzer 27.10.: *„es macht keinen Sinn die Messungen zu wiederholen“*) | **gestrichen.** L1 ist beantwortet: Die **Stufe** folgt im Betrieb der ATR (K6), die **Größe** nach ATR ist eine Bremse, nicht trennbar → Fakt (Risikodisziplin) |
> | **marktweiter Rückenwind** | Auskunft | **ist L2-a** (E-151/E-153): BTC über/unter 200-T-Schnitt als Regime für längeres Halten, *nicht entscheidbar* (zu wenige Regimewechsel). E-153: *„Kein weiterer Trendfilter.“* Die Vorprüfung §2 hat das nur bestätigt | bleibt **Auskunft**, ohne Urteil |
> | **H-1b** je Trade | Hauptfrage | **neu**: L2-a fragte das Regime des **Marktes** als Bedingung auf dem Kern. H-1b fragt den Trend des **Assets** im Querschnitt, am selben Tag (Tagesklammer), und setzt keinen Filter auf den Einstieg, sondern wählt die **Haltedauer**. ⚠ Zu E-153 „kein weiterer Trendfilter“: H-1b ist kein Filter, der Einstieg bleibt unverändert | bleibt |
> | **H-1c** Extrem kurz | Hauptfrage | **neu**: 2.694 hat die Wucht nur als Auskunft (mehr Hoch binnen 24 h), keine Haltedauer je Zustand | bleibt |
>
> **Damit gilt:** H-1 = **H-1b** (drei Hypothesen) und **H-1c** (zwei Hypothesen). Die Abschnitte zu H-1a und S4 unten gelten **nicht mehr** und bleiben nur zur Nachvollziehbarkeit stehen.
>
> ⚠️ **Lehre:** Der Abgleich mit dem Gesamtplan gehört **vor** den Messplan, nicht danach. Das Konzept (§9.2) hatte V-1 genannt, aber als „Vorläufer mit einer Dimension“ eingeordnet statt als dieselbe Messung.

> ## ⚠️ FASSUNG 3 (28.10.2026, beim Bau, vor jedem echten Ergebnis)
>
> | | Lücke | Festlegung |
> |---|---|---|
> | **Zweiter Weg H-1c** | Fassung 1/2 nannten keinen. TRÄGT braucht ihn aber (E-141, §5 Punkt 3) | die beiden Extrem-Merkmale **getrennt**: `momentum_kurz` ≥ 0,8509 allein und `rsi` ≥ 85,6631 allein. TRÄGT braucht in **beiden** dasselbe Vorzeichen wie die Hauptfrage (Mittel), in ≥ 3 von 4 Mengen |
> | **„sein Band schließt das Gegenteil aus“** (§5 Punkt 3, H-1b) | mehrdeutig | **wörtlich und streng:** Das Band des zweiten Wegs b liegt ganz auf **derselben** Seite des eigenen Nullpunkts wie die Hauptfrage (b trägt selbst in dieselbe Richtung), in ≥ 3 von 4 Mengen |
> | **Kosten** | §4 „nachgelagert“ | In der Tagesklammer heben sich Gebühr und Finanzierung **auf**, weil beide Zustände dieselbe Haltedauer haben. Ausgewiesen wird das Netto-Niveau je Zustand als Auskunft (0,30 % + 0,18 %/T) |
> | **Führung F** | §4 | ATR wie 2.702 und Betrieb (24 Stundenspannen ÷ Schluss × √24, bis einschließlich Einstiegsstunde), Linie = höchstes Hoch seit Einstieg **bis zur Vorstunde** − 1,5 × ATR, Ausstieg an der Linie. Abweichend von 2.702: **Spot-Stundenkurse statt Markpreis** und Verzug 0 statt 1 h (wie §4 festgelegt) |

> ## ⚠️ FASSUNG 4 (28.10.2026, nach dem nicht bestandenen Selbsttest, vor jedem echten Ergebnis)
>
> **Selbsttest Fassung 3 NICHT bestanden** (`p101_h1_selbsttest_fassung3_nicht_bestanden.txt`): Fehlalarm etwa **doppelt** so hoch wie das Nennniveau (H-1c bis 7 %, Soll ≤ 5 %), Auflösung in `unverzerrt_3` selbst bei 2 Pp nur 66 %.
>
> **Ursache gemessen:** Einzelne echte Kursexplosionen beherrschen ihren Tag. Wölbung D72 58 (`bestand`) bzw. **958** (`unverzerrt_3`). Größter Fall **ALPACA** 24.04.2025: +96 % in 24 h, +537 % in 72 h (Squeeze vor der Einstellung, in den Rohkursen bestätigt, **kein Datenfehler**, bleibt drin). An den äußeren Quantilen wird das Perzentil-Band zu eng, um den Ausreißertag zu breit.
>
> **Wahl auf künstlichen Zuständen** (`p101_h1_fassung4_wahl.py`/`.txt`, Vorab-Regel im Docstring: höchste Fundquote bei 1 Pp unter der Bedingung S1/S2 ≤ 5 %):
>
> | Fassung | S1/S2 höchstens | Mittel | Fundquote 1 Pp |
> |---|---|---|---|
> | einfach + Bootstrap (Fassung 3) | 9,5 % | 3,9 % | 68 % |
> | log + Bootstrap | 7,0 % | 3,2 % | 79 % |
> | einfach + t-Band | 6,0 % | 2,4 % | 66 % |
> | **log + t-Band** | **5,0 %** | **2,0 %** | **74 %** |
>
> ⇒ **Fassung 4:** Zielgröße ist die **Differenz der Log-Erträge** ln(1 + r_lang) − ln(1 + r_kurz), wie „Konto log“ in 2.702. Das **Band** ist cluster-robust über die 15-T-Blöcke, mit t-Quantil (nb − 1 Freiheitsgrade) und Faktor √(nb/(nb − 1)), also derselben Kleinstichproben-Korrektur wie `agent.regel0_messstand._kennzahl`. Nullpunkt, Nullwelt, Blöcke und Urteilsregeln bleiben unverändert. ⚠ Einzige Fassung ohne Wert über 5 %; die Grundgesamtheit bleibt **vollständig** (nichts gekappt, nichts entfernt).
>
> **Gegenprobe ohne Ergebnis** (`p101_h1_gegenprobe.txt`): 1.200 Stichproben aus den Rohdaten gleich (Erträge, Stop, Zustände, Extrem-Merkmale). Beide Vorgriff-Mutationen werden erkannt (a 73, rF 28 Abweichungen). Ein Fehler lag **in der Gegenprobe** selbst: Sie nahm bei einer früher endenden Tagesreihe (AERGO bis 03/2025) einen Monate alten Schluss als „Vortag“. Behoben, jetzt dieselbe Regel wie das Werkzeug: Der Einstiegstag muss in der Reihe stehen. Ohne Zustand a bleiben **1.315 von 43.090** Einstiegen (3 %).
>
> **Selbsttest Fassung 4 mit 200/100 Welten** (`p101_h1_selbsttest_fassung4_100welten.txt`): 19 von 20 Zellen bestanden, eine mit S2 6,0 % (6 von 100; Zufallsstreuung bei 100 Welten ≈ ±2 Pp). ⚠ **Eigener Parameterfehler:** §6 setzte 200/100 Ziehungen, der Projektstandard verlangt **mindestens 1.000** (Lehre B4 11.10.). Korrigiert: S1 und S2 mit je 1.000 Welten wiederholt. Soll bleibt das vorab festgelegte ≤ 5 %; die strengere Grenze aus der Stufung (Nennniveau je Hypothese + 2 Standardfehler) wird zusätzlich ausgewiesen.
>
> ✔ **Selbsttest Fassung 4 mit 1.000 Welten BESTANDEN** (`p101_h1_selbsttest.txt`), 20 von 20 Zellen, auch nach der strengen Stufungsgrenze (H-1b ≤ 2,5 %, H-1c ≤ 3,5 %): Fehlalarm S1 1,1–3,2 %, Ballung S2 1,0–2,8 %, Orakel 100 %. **Auflösung X** (≥ 80 % gefunden): 1 Pp bei D72/DF/D6 in den meisten Mengen, sonst **2 Pp** (Log-Differenz je Einstieg, Tagesklammer). ⚠ Kleinere Unterschiede zwischen den Zuständen kann diese Messung **nicht** sehen; ein „trägt nicht“ gilt deshalb nur **bis X**.

---

## 1. Die Frage

> **Gleicher Auslöser, gleicher Zeitpunkt: Passt eine andere Handlung besser zu den Gegebenheiten dieses Trades?**

Gemessen wird das **Wie**, nicht das Ob. Verglichen wird immer **innerhalb** desselben Einstiegs (gepaart) oder **innerhalb** desselben Tages (Tagesklammer). Dadurch fällt der Markt großteils heraus (Konzept §6.1).

## 2. Was vorab feststand (Vorprüfung 28.10., nur Zählungen)

| | Ergebnis | Folge |
|---|---|---|
| Marktweiter Rückenwind (BTC über 200-T-Schnitt) | 2025–26 im Kern **vier Phasen**, je Zustand ≈ 13–15 Blöcke | **nicht auflösbar** → nur Auskunft |
| Rückenwind je Trade **a** (Asset über eigenem 50-T-Schnitt, Vortag), Menge `unverzerrt_1` | RW-Anteil 2024 59 %, 2025 23 %, 2026 25 %. **Tage mit beiden Zuständen:** 2024 78, 2025 161, 2026 157 (Einstiege daran 1.747 / 4.042 / 3.061) | 2025–26 ≈ 318 Klammertage → **≈ 40 Blöcke à 15 T**: messbar |
| je Trade **b** (eigener 200-T-Schnitt) | RW 43 / 16 / 7 %; Klammertage 79 / 159 / 112 | zweiter Weg messbar, 2026 dünn |
| **L1 im Betrieb** | Die **Hebelstufe** hängt schon an der ATR: höchste Stufe mit P(Liquidation binnen 24 h) ≤ 2 % (`agent/regel0_rechnung.py` `hebelstufe`, K6, 2.681) | Neu an L1 ist nur noch die **Größe** nach Schwankung → H-1a misst die **Größe**, nicht die Stufe |
| §23.68 | 2025–26 längeres Halten **auch brutto** schlechter (H24 +0,30 %, H168 −0,51…−0,93 %) | Das ist der Bezug, gegen den H-1b die **Bedingung** misst |

⚠️ Die REGEL0-Einstiege liegen 2025–26 zu ≈ 75 % **unter** dem eigenen 50-T-Schnitt. Das Signal ist eher gegenläufig (kurzfristige Umkehr). Deshalb gibt es keine sichere fachliche Richtung, und die Prüfung ist **zweiseitig** (Memory „Messplan ohne fachliche Richtung zweiseitig“).

## 3. Daten (Desktop, nur lesend, `mode=ro`)

| Was | Quelle |
|---|---|
| Einstiege | `data/_vergleich/kern48jbz_einstiege_{bestand, unverzerrt_1, unverzerrt_2, unverzerrt_3}.csv` (REGEL0-Referenz, 2024-01 bis 2026-08), Einstieg = Schluss der Einstiegsstunde (wie p62) |
| Stundenkurse | `stundenkurse.db`, `stundenkurse_alle.db`, `eingestellt_historie.db`; die erste Datei gewinnt (wie p62) |
| Tagesschlüsse (Trend a/b/c) | `messdaten.db` `price_history_ohlc`, `assetklasse='krypto'`; Stand **Vortag** (kein Tageswert am Stundenanker, Memory „Tageswert an Stundenanker ist Vorgriff“) |
| ATR | **dieselbe Funktion wie der Betrieb**: `agent.regel0_rechnung.atr_je_stunde` (importiert, nicht nachgebaut) |
| Extrem | `messe_assetebene_und_vorhersage.merkmale` (importiert); Schwellen aus 2.648: `momentum_kurz` ≥ 0,8509 **oder** `rsi` ≥ 85,6631, zur Einstiegsstunde |
| Liquidation (Auskunft) | Markpreis `markpreis_historie.db`/`markpreis_alle.db`, Schwellen wie K6 (`K6.liq_schwelle`) |

Kein Download. **Keine Produktion:** Das Notebook ist nicht beteiligt, `data/tradinginfotool.db` wird nicht geöffnet. Jedes Werkzeug prüft am Ende, dass die Dateien vorher und nachher gleich sind (Größe und Änderungszeit).

## 4. Die drei Teilmessungen

**Gemeinsam:**
- **brutto** (Regel 2); Finanzierung 0,18 %/Tag und Gebühr 0,30 % nur **nachgelagert** ausgewiesen;
- **Urteil auf 2025–26**, beide Jahre einzeln, **2024 als zweite Epoche** (Auskunft mit Vorzeichen);
- **vier Mengen**, Urteil ≥ 3 von 4;
- Einstiege nur mit lückenlosen 168 h danach (gleiche Menge in jeder Zelle).

### ~~H-1a — Größe nach Schwankung (L1, V1)~~ (gestrichen in Fassung 2: ist V-1, E-158)

| | |
|---|---|
| Arm A | fester Positionswert je Trade (heute) |
| Arm B | Positionswert ∝ ATR̄ / ATR_e. ATR̄ ist der Median der ATR aller Einstiege der **vorangehenden 365 T** (kein Vorgriff), Gewicht gekappt auf [0,25; 4]; danach so skaliert, dass der **mittlere Einsatz je Kalendermonat** gleich A ist |
| Ergebnis je Trade | Spot-Ertrag 24 h × Gewicht. Die Stufe ist in A und B dieselbe, deshalb skaliert der Hebel beide gleich |
| **Hauptgröße** | Unterschied der **Ertrag-zu-Schwankung-Verhältnisse** der Tagessummen: (Mittel/Std)_B − (Mittel/Std)_A, gepaart auf denselben Tagen |
| Nebengrößen | linkes Ende (schlechteste 5 % der Tage), größter Rückgang, Mittelwert (Nebenbedingung: kein Ertragsverlust über das Band hinaus) |
| Nullwelt C | Gewichte von B **innerhalb desselben Tages** zufällig auf die Einstiege verteilt (Verteilung und Ballung bleiben, die Bindung an die ATR fällt weg) |

### H-1b — Haltedauer nach dem Trend dieses Trades (L6/L7, V2)

| | |
|---|---|
| Zustand (Hauptfrage) | **a**: Schluss des Vortags > eigener 50-T-Schnitt (Stand Vortag) |
| Zellen (je Einstieg) | Δ72 = r72 − r24 · Δ120 = r120 − r24 · **ΔF** = rF − r24 mit F = nachgezogener Stop 1,5 ATR, höchstens 120 h (die „Führung“; trennt Haltedauer und Stop, offene Frage aus 2.702). ⚠ **Kurslücken** werden nicht modelliert: Ein Stop wird zum Stopkurs ausgeführt, wie in p62. Das schont den Stop und wird ausgewiesen |
| **Hauptgröße** | **Tagesklammer:** je Tag mit beiden Zuständen d_t = Mittel(Δ ∣ RW) − Mittel(Δ ∣ GW), dann Mittel über die Tage |
| Hypothesen | **drei** (Δ72, Δ120, ΔF) → Band nach Bonferroni (`hypothesen=3`) |
| Nullwelt C | Zustände **innerhalb des Tages** zufällig vertauscht |
| zweiter Weg | Zustand **b** (200-T-Schnitt je Asset), dieselbe Rechnung |
| Auskunft | Zustand **c** (Ertrag gegen BTC über 30 T > 0), marktweit BTC > 200 T, gepoolt je Handel |

### H-1c — kurz halten bei einem Extrem (L5, V3)

| | |
|---|---|
| Zustand | Extrem zur Einstiegsstunde (Schwellen aus 2.648, §3) |
| Zellen | Δ6 = r6 − r24 · Δ72 = r72 − r24 |
| Hauptgröße | Tagesklammer wie H-1b: Mittel(Δ ∣ Extrem) − Mittel(Δ ∣ nicht Extrem) |
| Hypothesen | zwei → Bonferroni |
| Nullwelt C | wie H-1b |
| ⚠ Fallzahl | vorab unbekannt. Unter 20 Blöcken mit Klammertagen: **KEIN BEFUND**, ausgewiesen und nicht als Nullbefund gelesen |

## 5. Messregelwerk (`messnorm`, Abgleich vorab)

| Regel | Umsetzung |
|---|---|
| Block | `messnorm._block(h)` = max(15, 3 × Horizont in T): H-1a/H-1c-Δ6 15 T, Δ72 15 T, Δ120/ΔF 15 T. Je Messung `pruefe_block` (Autokorrelation ≤ 0,15), sonst KEIN BEFUND |
| unter 20 Blöcken | **KEIN BEFUND** |
| Bezug | **Nullpunkt** = Mittel der Nullwelten C, **40 Ziehungen** (Messstandard 09.09.), 90. Perzentil als obere Grenze ausgewiesen |
| Band | Block-Bootstrap über Tagesblöcke, 2.000 Ziehungen, zweiseitig, Niveau nach Bonferroni |
| Positivkontrolle | gepflanzte Stärken (§6), sonst kein „trägt nicht“ |
| Urteile | **TRÄGT** · **TRÄGT NICHT BIS X** · **NICHT TRENNBAR** · **KEIN BEFUND** (`messnorm` Befund.urteil) |
| je Handel und je Tag | Tagesklammer ist das Urteil, gepoolt je Handel als Auskunft (E-141) |
| Gewichtung | Tagesklammer, ausgewiesen (Memory „Gewichtung ausweisen“) |

**TRÄGT** verlangt **alle** dieser Punkte (vorab):
1. Das Band 2025–26 schließt den Nullpunkt aus, in ≥ 3 von 4 Mengen.
2. 2025 und 2026 **einzeln** haben dasselbe Vorzeichen.
3. Der **zweite Weg** hat dasselbe Vorzeichen, und sein Band schließt das Gegenteil aus. Das gilt nur für H-1b (Zustand b). Für H-1a ist der zweite Weg die **ATR aus Tageskerzen** (14 T, `messdaten.db`) statt der Stunden-ATR.
4. Positivkontrolle D und Selbsttest bestanden (§6).

**Geltungsbereich im Urteilssatz:** Menge, Zeitraum, Gewichtung, REGEL0-Einstiege. Was daraus folgt, gilt **nicht** ohne neue Messung für andere Auslöser.

**R-R11:** Je Menge muss H24 brutto 2025–26 **p62 reproduzieren** (gleiche Einstiegsmenge mit 168 h). Ohne Reproduktion wird nicht ausgewertet.

## 6. Selbsttest — VOR dem ersten Blick auf echte Ergebnisse

Läuft auf den **echten** Renditen mit **künstlichen** Zuständen bzw. Gewichten. Fällt ein Punkt durch, wird **nicht** gemessen, sondern das Werkzeug korrigiert (Fassung 2).

| # | Welt | Soll |
|---|---|---|
| S1 Fehlalarm | 200 Welten, Zustand zufällig je Einstieg (Anteil wie echt) | TRÄGT in ≤ 5 % (zweiseitig); Dreierregel ausgewiesen |
| S2 Ballung | 100 Welten, Zustand je **Tagesblock** einheitlich (Regime-Etikett) | **kein** Fehlalarm über 5 %; Klammertage fallen weg → KEIN BEFUND ist richtig |
| S3 Auflösung | Pflanzung Δ += k für RW-Einstiege, k = 0,1 / 0,25 / 0,5 / 1,0 / 2,0 % | Fundquote je k; **X** = kleinstes k mit ≥ 80 %. Ausgewiesen als Auflösungskurve |
| ~~S4 H-1a bekannte Wahrheit~~ (entfällt, Fassung 2) | künstliche Renditen r = μ + (ATR/ATR̄)^κ · z, κ = 0 / 0,5 / 1 | κ = 0: B nicht besser (Fehlalarm ≤ 5 %); κ = 1: B klar besser (≥ 80 %) |
| D Orakel | Zustand bzw. Gewicht mit Zukunftswissen (z. B. RW := Δ > 0) | muss TRÄGT ergeben, sonst sieht der Aufbau nichts (Lehre E-133) |

## 7. Werkzeuge (gebaut erst nach Nutzer-Ja zu diesem Plan)

| Datei | Inhalt |
|---|---|
| `Rechenkern_02_10/p101_h1_vorpruefung.py` | Fallzahlen je Zustand, Menge und Jahr; Blöcke; `pruefe_block`; R-R11 gegen p62 |
| `Rechenkern_02_10/p101_h1_selbsttest.py` | §6, **ohne** echtes Ergebnis auszugeben |
| `Rechenkern_02_10/p101_h1_messung.py` | §4/§5; Ausgabe `.txt` mit Geräte- und Zeitstempel |
| `Rechenkern_02_10/p101_h1_gegenprobe.py` | **zweiter Rechenweg** (eigene Schleife je Tag statt Vektorrechnung) für Hauptgrößen und Nullwelt |

Reihenfolge: Vorprüfung → Selbsttest → **Zwischenstand an den Nutzer** → Messung → Gegenprobe → Teilergebnisse einzeln abstimmen (je H-1a/b/c).

## 8. Was ein Ergebnis bedeutet

| Ergebnis | Folge |
|---|---|
| **TRÄGT** | Die Zeile darf die Handlung **verschieben** (Bewertung). Danach Kostenprüfung (Finanzierung, Gebühren), dann Bauentscheid (Konzept §10) |
| **TRÄGT NICHT BIS X** | Ein Effekt ab X ist ausgeschlossen. Die Zeile bleibt **Fakt** in der Mail |
| **NICHT TRENNBAR / KEIN BEFUND** | Fakt; offen ist, wie die Frage anders messbar wird (kein Abbruch ohne Ursache). Erst Ursache, dann Lösung |

⚠️ **Ehrliche Erwartung:** Am ehesten trägt H-1a, weil der Mechanismus fast zwangsläufig wirkt (Risiko sinkt, die Frage ist nur je Risiko). H-1b hat das größte Potential und die größte Unsicherheit (2.702, Umkehr 2024 gegen 2025–26). H-1c könnte an der Fallzahl scheitern.

---

## 9. ERGEBNIS (28.10.2026, `p101_h1_messung.txt`, Gegenprobe `p101_h1_gegenprobe.txt` ✔)

**Geltungsbereich:** REGEL0-Einstiege, vier Mengen, lückenlose 168 h, 2025-01 bis 2026-08, Tagesklammer, Log-Differenz brutto, Spot-Stundenkurse. Auflösung X = 1–2 Pp.

### H-1b — Haltedauer nach dem Trend dieses Assets: **TRÄGT NICHT** (nach Vorab-Regel)

| Zelle | Zustand a (Haupt), Mittel je Menge in Pp | Stufen | zweiter Weg b |
|---|---|---|---|
| D72 (72 h − 24 h) | +0,06 / −0,19 / +0,35 / −0,23 | 2× NICHT TRENNBAR, 2× TRÄGT NICHT BIS 2 Pp | Vorzeichen gemischt |
| D120 (5 T − 24 h) | +0,44 / −0,13 / +0,43 / −0,45 | 3× TRÄGT NICHT BIS 2 Pp, 1× NICHT TRENNBAR | gemischt |
| DF (Führung − 24 h) | −0,42 / −0,53 / +0,05 / −0,64 | 3× NICHT TRENNBAR, 1× TRÄGT NICHT BIS 2 Pp | gemischt |

⇒ Ob das Asset über seinem 50-T-Schnitt liegt, ändert den Wert des längeren Haltens **nicht erkennbar** (Vorzeichen wechseln zwischen Mengen und Jahren). **L6/L7 bleiben Fakt.**

**Auskunft c (Stärke gegen BTC über 30 T), KEIN Urteil (nicht vorab als Hypothese, Mehrfachtesten):** durchgehend **negativ**: D72 −0,36 / −1,05 / −0,04 / −0,77 (2× TRÄGT niedriger), DF −0,92 / −1,25 / −0,46 / −1,16 (3× TRÄGT niedriger). Lesart: Bei Assets, die vorher **stärker als BTC** waren, ist längeres Halten **schlechter**. Das ist eher das Gegenteil von „Gewinner laufen lassen“. Nur ein **Hinweis** für eine eigene Vorab-Hypothese auf **anderen** Daten (vorwärts oder Lauf A).

**Marktweit m:** KEIN BEFUND (keine Klammertage, wie erwartet; L2-a).

### H-1c — kurz halten bei einem Extrem: **TRÄGT NICHT** (nach Vorab-Regel), D6 an der Nachweisgrenze

| Zelle | extrem (Haupt), Mittel je Menge in Pp | Stufen | je Jahr 2024/25/26 | zweiter Weg mom / rsi | gepoolt je Handel (Unterschied) |
|---|---|---|---|---|---|
| **D6** (6 h − 24 h) | +0,60 / **+1,21** / **+1,07** / +1,26 | **2× TRÄGT (höher)**, 2× NICHT TRENNBAR | **alle 12 positiv** | **alle 8 positiv** | −0,48 / −0,04 / −0,30 / +0,18 |
| D72 (72 h − 24 h) | +0,73 / +0,59 / +0,44 / +0,55 | 3× TRÄGT NICHT BIS 2 Pp, 1× NICHT TRENNBAR | gemischt | gemischt | gemischt |

⚠ **D6 knapp:** In `unverzerrt_3` liegt die Untergrenze des Bandes bei +0,03 Pp, der Nullpunkt aus 40 Ziehungen bei +0,10 Pp (Gegenprobe mit eigener Nullwelt: −0,02). Mit einem anderen Zufallszug wäre das ein drittes TRÄGT und damit alle vier Punkte erfüllt. Das Urteil steht nach der Vorab-Regel; die 40 Ziehungen sind der Messstandard. Eine Änderung **nach** dem Ergebnis wäre nachträglich und braucht eine Nutzerentscheidung.

⚠ **Fachlich:** Die Tagesklammer misst **gegen die anderen Einstiege desselben Tages**. Gepoolt je Handel (das absolute D6 der Extrem-Einstiege) ist **kein** Vorteil zu sehen: Extrem-Einstiege geben zwischen 6 h und 24 h nicht mehr ab, die übrigen gewinnen in dieser Zeit dazu. Als **Handlung** („bei Extrem nach 6 h aussteigen“) ergibt das kein erkennbares Plus im Geld.

### Zwischenfazit zum Ziel

Auf den REGEL0-Einstiegen 2025–26 verschiebt **keine** der gemessenen Gegebenheiten die **Haltedauer** messbar (Auflösung 1–2 Pp). Mit K6 (Stufe nach ATR, im Betrieb) und V-1 (Größe nach ATR: Bremse, nicht trennbar) ist die **Wie-Schicht** damit in ihren drei messbaren Achsen geprüft: **Risiko** ja (Stufe), **Ertrag** nein.
