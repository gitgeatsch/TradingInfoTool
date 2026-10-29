# Messplan W „Wal-Fluss“ — VORAB festgelegt (29.10.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Bezug:** [`Voranalyse_Wale_29_10.md`](Voranalyse_Wale_29_10.md) §3, §6, §7 · Gesamtplan **G16**.
**Nutzervorgaben:** *„was zeigt uns, wenn Wale kaufen oder verkaufen, halten“* (29.10.) · *„Ziel soll immer noch eine intelligente
Lösung sein, die einen Vorteil beim Handel darstellt und sich daraus Aktionen ableiten lassen in die Zukunft“* (29.10.) ·
*„alles Schritt für Schritt, keine Fehler, bei Problemen Lösungen suchen“* (29.10.).
**Stand:** ✔ **Nutzer-Ja 29.10.** (*„Ok a, Plan wie vorgelegt – wenn das Ergebnis negativ sein sollte, gehen wir in Abstimmung und
Lösungssuche, nicht einfach abhaken“*). Vorab committet, **bevor** ein Werkzeug gebaut oder ein Ergebnis angesehen wird; jede
spätere Änderung erscheint als **Fassung 2** mit Ursachenbegründung.

> ## ⚠️ FASSUNG 2 (29.10.2026, beim Bau, vor jedem echten Ergebnis)
>
> Festlegungen, die Fassung 1 offen ließ. Keine ändert eine Hypothese, eine Schwelle oder ein Kriterium.
>
> | | Lücke in Fassung 1 | Festlegung |
> |---|---|---|
> | **Rang-Vorlauf** | „gegen die vorangehenden 365 Tage“: E beginnt erst nach 120 Tagen Schätzfenster, der volle 365-T-Rang erst 2024-07 — die zweite Epoche wäre fast leer | bis 365 Werte vorliegen, gilt der **vorhandene** Vorlauf, mindestens 120 Werte (dieselbe Mindestzahl wie das Schätzfenster). Fünftel ab 2023-08-29 |
> | **Zweiter Weg ETH** „sein Band schließt das Gegenteil aus“ | mehrdeutig | **wörtlich und streng**, wie H-1 Fassung 3: das ETH-Band liegt ganz auf **derselben** Seite des eigenen Nullpunkts wie BTC |
> | **Kurs zum Zeitpunkt T** | offen | **Eröffnungskurs** der Spot-Stundenkerze, die um T beginnt. Gegenprobe: Eröffnung gegen Schluss der Vorstunde, größte Abweichung 0,08 %. ⚠ Eine Kerze fehlt bei Binance (24.03.2023 13:00 UTC, BTC und ETH gleich); kein Einstiegszeitpunkt |
> | **Schichten (Punkt 5)** | Grenzen offen | Drittel der Tagesbewegung r_t **im Urteilsfenster** (nur zur Einteilung der Auswertung, kein Signal) |
> | **Vorzeichen (Punkte 2–6)** | Bezug offen | Vorzeichen von D; die Hauptrichtung ist das Vorzeichen von D − Nullpunkt (Punkt 1) |
> | **S3 Auflösung** | Welten je k offen | 250 Welten je k; die Pflanzung ±k verschiebt D um **2k** — X wird in k ausgewiesen, die Messung vergleicht das Band mit **2X** |
> | **D Orakel** | Schwelle offen | 200 Welten, bestanden bei TRÄGT HÖHER in ≥ 95 % je Zelle |
> | **Freigabe** | offen | die Messung läuft nur, wenn der Selbsttest mit **≥ 1.000** Welten bestanden hat (Datei `p102_wale_selbsttest.json`) |
>
> **Werkzeuge:** `p102_wale_basis.py` (EIN Rechenweg für Vorprüfung, Selbsttest und Messung) · `p102_wale_vorpruefung.py` ·
> `p102_wale_selbsttest.py` · `p102_wale_messung.py` · `p102_wale_gegenprobe.py` (eigener Rechenweg, zwei Vorgriff-Mutationen).
> **Vorab nachgewiesen** (künstliche Daten): Residuum trennt (ρ zum gepflanzten Eigenen 0,993, zu R und r ≤ 0,014), Fünftel
> 21/60/20 %, t-Band deckt 95,5 % bei Soll 95 %. Reproduktion der Stichprobe: G und R in allen vier q exakt (≤ 1,4·10⁻¹⁷).

## 1. Die Frage

> **Zeigt der Netto-Fluss der GROSSEN Aufträge an einem Tag etwas über den Kurs der folgenden Tage — über das hinaus, was der
> übrige Fluss und die Bewegung desselben Tages schon zeigen?**

Nur das wäre eine **Bewertung** (was kommt). Dass Große an einem Tag netto gekauft haben, ist für sich ein **Fakt**.

## 2. Abgleich mit dem Bestand (vor dem Plan, Lehre aus H-1 Fassung 2)

| Was schon gemessen ist | Ergebnis | Folge für diesen Plan |
|---|---|---|
| `taker_bias` (Terminmarkt, alle Größen, Querschnitt 122 Symbole, H20) | **trägt nicht** (2.169, 2.219; vor dem Messstandard) | ein Fluss **ohne Größenzerlegung** trägt im Querschnitt nicht — gemessen wird hier die **Zerlegung** und die **Zeitreihe** |
| Käuferanteil 1/6/24 h, Spot, Querschnitt (2.665) | `kaeufer_24h` **begleitet die Bewegung** (ρ +0,29 zur Vorbewegung, 12 h alt nur noch 30 %) | ⚠️⚠️ die Großen müssen **Lage vorher** sein, nicht Begleitung → die Bewegung des Tages wird **herausgerechnet** (§4) und nach ihr **geschichtet** (§5) |
| `top_bias` (W11) | trägt nicht (2.219) | nicht wiederholt |
| Stichprobe a (Voranalyse §6) | feste Schwelle taugt nicht; Spot-Große laufen weitgehend unabhängig vom Rest, Futures-Große stärker mit; 2026 entkoppelt | **relative** Schwelle, Märkte **getrennt** |

Neu ist also: die **Größe** des Auftrags, **Spot gegen Futures**, die **Zeitreihe** auf dem Kern.

## 3. Daten (Desktop, nur lesend, `mode=ro`; NB nicht beteiligt, Produktions-DB nicht geöffnet)

| Was | Quelle |
|---|---|
| Fluss je Tag und Stunde | `data/_wale/wale_voll.db` (BTCUSDT, ETHUSDT · Spot und Futures · 01.01.2023 bis 28.10.2026), abgeglichen mit der REST-Kerze |
| Kurse | Binance **Spot**-Stundenkerzen BTCUSDT/ETHUSDT per REST (die Stundenkurse im Bestand haben BTC erst ab 2023-09, 2.668), einmal geholt und in `wale_voll.db` abgelegt |

## 4. Größen

| | Definition |
|---|---|
| **G** (Großfluss) | Kauf − Verkauf der größten **Sweeps**, die zusammen ≥ q des Tagesumsatzes ausmachen, geteilt durch den Tagesumsatz — je Wert a, Markt m, Tag t |
| **R** (Rest) | Netto-Fluss aller übrigen Sweeps, geteilt durch den Tagesumsatz (≈ der Käuferanteil aus 2.665) |
| **E** (Hauptgröße) | **Residuum** von G nach R und der Tagesbewegung r_t: E_t = G_t − (b₀ + b₁·R_t + b₂·r_t), die b aus den **vorangehenden 180 Tagen** (bis t−1) geschätzt — kein Vorgriff |
| Rang | Fünftel von E gegen die **vorangehenden 365 Tage** (bis t−1) |
| q-Leiter | **5 %** ist die Hauptstufe; 1 / 10 / 20 % laufen mit (vorab festgelegt, keine nachträgliche Wahl) |
| **Zielgröße** | Log-Ertrag Spot vom **Schluss des Tages t** (00:00 UTC t+1) bis **t+H**, H = 1 / 3 / 7 T, **brutto** (Regel 2) |
| Verzug (Betrieb) | dieselbe Rechnung mit Einstieg **06:00 UTC** t+1 — so lange kann es dauern, bis die Tagesdatei vorliegt |

**Hauptstatistik:** mittlerer Ertrag an Tagen mit E im **obersten** Fünftel minus Tage im **untersten** Fünftel (in Pp, Log).
**Zweiseitig** — „Große kaufen → steigt“ und „Große kaufen → Gipfel“ sind beide plausibel.

## 5. Messregelwerk (`messnorm`, Abgleich vorab)

| Regel | Umsetzung |
|---|---|
| Hypothesen | 2 Märkte × 3 Horizonte = **6** je Wert → Band nach Bonferroni |
| Urteilszeitraum | **2025-01 bis 2026-09** (Messfokus); 2023-07 bis 2024-12 als **zweite Epoche** (Auskunft mit Vorzeichen); 2023 Q1 Spot (gebührenfrei) ausgewiesen |
| Block | `messnorm._block(h)` = max(15, 3·H): 15 T für H 1 und 3, 21 T für H 7; `pruefe_block` (Autokorrelation ≤ 0,15) |
| unter 20 Blöcken | **KEIN BEFUND** (erwartet: 2025-01 bis 2026-09 ≈ 42 Blöcke à 15 T, ≈ 30 à 21 T) |
| Band | Block-Bootstrap über Tagesblöcke, 2.000 Ziehungen, t-Band mit Kleinstichproben-Korrektur (wie H-1 Fassung 4) |
| Nullwelt | E in **15-T-Blöcken** vertauscht (Ballung bleibt, die Bindung an den Kurs fällt weg); **zirkuläre Verschiebung** als Alternative — welche gilt, entscheidet der **Selbsttest** (§6) nach Vorab-Regel: die, die S1 **und** S2 ≤ 5 % hält; halten beide, Blockvertauschung |
| Nullpunkt | Mittel der Nullwelten, 40 Ziehungen (Messstandard 09.09.), 90. Perzentil als obere Grenze |
| Urteile | **TRÄGT** · **TRÄGT NICHT BIS X** · **NICHT TRENNBAR** · **KEIN BEFUND** |

**TRÄGT** verlangt **alle** dieser Punkte (vorab, BTC als Hauptwert):
1. Das Band 2025–26 schließt den Nullpunkt aus (q 5 %).
2. **2025 und 2026 einzeln** dasselbe Vorzeichen.
3. **q-Leiter:** dasselbe Vorzeichen in ≥ 3 von 4 Stufen.
4. **Zweiter Weg ETH:** dasselbe Vorzeichen, und sein Band schließt das Gegenteil aus.
5. **Lage vorher** (Lehre 2.665): nach der Tagesbewegung r_t in drei Schichten geteilt, dasselbe Vorzeichen in ≥ 2 von 3.
6. **Verzug 06:00:** dasselbe Vorzeichen (sonst wäre es im Betrieb nicht erreichbar).
7. Selbsttest und Orakel bestanden (§6).

**Vergleichsarme, ausgewiesen ohne Urteil:** G roh und R roh in derselben Rechnung. Trägt R so gut wie E, zeigen die Großen
nichts Eigenes. **Geltungsbereich im Urteilssatz:** Wert, Markt, Zeitraum, q, Einstieg am Tagesschluss.

## 6. Selbsttest — VOR dem ersten Blick auf echte Ergebnisse

Läuft auf den **echten** Erträgen mit **künstlichen** Signalen. Fällt ein Punkt durch, wird **nicht** gemessen, sondern das
Werkzeug korrigiert (Fassung 2).

| # | Welt | Soll |
|---|---|---|
| S1 Fehlalarm | **1.000** Welten, Signal AR(1) mit der **echten** Autokorrelation von E | TRÄGT (Punkt 1) in ≤ 5 %; Stufungsgrenze (Nennniveau + 2 Standardfehler) ausgewiesen |
| S2 Ballung | 1.000 Welten, Signal je **Monat** gleichgerichtet (Regime-Etikett) | kein Fehlalarm über 5 % |
| S3 Auflösung | Pflanzung: Ertrag += k im obersten, −k im untersten Fünftel, k = 0,1 / 0,25 / 0,5 / 1 / 2 Pp | **X** = kleinstes k mit ≥ 80 % gefunden, als Kurve |
| D Orakel | Signal = künftiger Ertrag + Rauschen | muss TRÄGT ergeben |

## 7. Werkzeuge (gebaut erst nach dem Nutzer-Ja)

| Datei | Inhalt |
|---|---|
| `Rechenkern_02_10/p102_wale_vorpruefung.py` | Vollständigkeit, Blöcke, Autokorrelation, Fallzahlen je Fünftel und Jahr — **ohne** Kursbezug |
| `Rechenkern_02_10/p102_wale_selbsttest.py` | §6, **ohne** echtes Ergebnis auszugeben |
| `Rechenkern_02_10/p102_wale_messung.py` | §4/§5; Ausgabe `.txt` mit Geräte- und Zeitstempel |
| `Rechenkern_02_10/p102_wale_gegenprobe.py` | **zweiter Rechenweg** (Schleife je Tag statt Vektorrechnung) für E, Fünftel und Hauptstatistik |

Reihenfolge: Vorprüfung → Selbsttest → **Zwischenstand an den Nutzer** → Messung → Gegenprobe → Teilergebnisse einzeln abstimmen.

## 8. Was ein Ergebnis bedeutet — welche HANDLUNG daraus folgt

| Ergebnis | Folge |
|---|---|
| **TRÄGT** | eine **Bewertungszeile für den Kern** (BTC, ETH): sie darf (a) einen **Spot-Einstieg** im Kern auslösen oder zurückhalten, (b) beim **Hebel** die Wahrscheinlichkeit **dieses** Trades verschieben (Regel 3: kein Asset-Rang), (c) in der Mail als **Begründung** stehen (*„Große kaufen am Spotmarkt netto, oberstes Fünftel seit 365 T; daraus in 3 T im Mittel +x Pp“*). Danach Kostenprüfung, Bauentscheid, **NB-Abrufer** (Tagesdatei des Vortags, 13–100 MB) |
| **TRÄGT NICHT BIS X** | Ein Effekt ab X ist ausgeschlossen. Der Großfluss bleibt **Fakt** in der Mail — ⚠️ **und** es folgt Abstimmung mit Lösungssuche (unten) |
| **NICHT TRENNBAR / KEIN BEFUND** | Fakt; die Ursache wird gemessen, dann eine Lösung gesucht |

⚠️⚠️ **Nutzervorgabe 29.10.: ein negatives Ergebnis wird NICHT abgehakt.** Es geht als Teilergebnis in die **Abstimmung**, mit
Ursachenanalyse und Lösungswegen (z. B. andere Einheit als Sweep, Stunde statt Tag, Bedingung auf Lage oder Regime, andere
Werte) — jeder neue Weg als eigene Vorab-Fassung, nie als nachträgliche Wahl auf denselben Daten.

**Stufe 2 (eigener Plan, erst nach Stufe 1):** dieselbe Frage **stündlich** — der Großfluss der letzten 24 h **vor einem
REGEL0-Einstieg** auf dem Kern, Horizont 24 h. Die Stundendaten liegen dafür schon vor (`wale_voll.db`, Tabelle `stunde`).
SOL (Kern) braucht einen eigenen Download und folgt nur bei TRÄGT.

⚠️ **Ehrliche Erwartung:** Der übrige Fluss trägt im Querschnitt nicht (2.169) und begleitet nur die Bewegung (2.665). Am ehesten
trägt der **Spot-Großfluss** (er läuft unabhängig vom Rest, Voranalyse §6), am wenigsten der Futures-Großfluss. Zwei Werte und
rund 640 Urteilstage sind wenig: X wird eher bei 1 Pp und darüber liegen, ein kleinerer Effekt bliebe unsichtbar.
