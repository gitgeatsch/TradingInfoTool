# Messplan H-1 „Lagegerechte Handlung“ — VORAB festgelegt (28.10.2026)

**Bezug:** Konzept `Basisinfos/Konzept_Lagegerechte_Handlung_27_10.md` §5.3 und §6.5 · Entscheidung E-165.
**Stand:** vorab committet, **bevor** ein Werkzeug gebaut oder ein Ergebnis angesehen wird. Jede spätere Änderung erscheint als **Fassung 2** mit Ursachenbegründung und nicht still.

**Nutzerfestlegungen:**
- 27.10.: beide Stränge, nur Long, Haltedauer 24 h bis 5 T und länger, bis die Führung schließt.
- 28.10.: L5 ohne „nach oben“, L2 nur Fakt, L8 in den Spot-Strang, *„unsicher bei allen Punkten“* (die Messung entscheidet).
- 28.10. zu Rückenwind je Trade: *„ja a – ist sicher der kurzfristig relevantere Bereich, aber B und C finde ich nicht falsch“*.

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

### H-1a — Größe nach Schwankung (L1, V1)

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
| S4 H-1a bekannte Wahrheit | künstliche Renditen r = μ + (ATR/ATR̄)^κ · z, κ = 0 / 0,5 / 1 | κ = 0: B nicht besser (Fehlalarm ≤ 5 %); κ = 1: B klar besser (≥ 80 %) |
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
