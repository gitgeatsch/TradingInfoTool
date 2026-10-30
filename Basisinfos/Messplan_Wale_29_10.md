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

---

## 9. VORPRÜFUNG und SELBSTTEST (29.10.2026 abends, vor jedem echten Ergebnis)

**Voller Download** (`wale_voll.py`, Nutzer *„Ok a, BTC und ETH voll laden“*): 4 × 1.396 Tage (01.01.2023–27.10.2026), 0 Ausfälle,
Tag und Stunde verdichtet, Rohdaten nicht behalten. Engpass war die Leitung (6,3 MB/s, Prozessor 17 %), nicht der Rechner;
Spot BTC 2023 (gebührenfrei, ~100 MB je Tag) über Zeitabschnitte auf mehrere Lader verteilt (jeder Tag wird vor dem Laden in der
Ablage nachgesehen). Der 28.10. fehlt bei Futures noch im Archiv (Nachlauf).

**Vorprüfung** (`p102_wale_vorpruefung.txt`): ✔ **BESTANDEN**

| | |
|---|---|
| Vollständigkeit | alle 4 Reihen 1.396/1.396 Tage, Stunden = Tag an jedem Tag |
| Archiv gegen REST-Kerze | Spot 1,0000–1,0011 · Futures 0,987–1,033, **drei auffällige Tage je Wert**, alle außerhalb des Urteilsfensters (unten) |
| Reproduktion | G und R auf allen 93 Stichprobentagen je Markt exakt (6,9·10⁻¹⁸) |
| Kurse | an jedem Einstiegszeitpunkt (00:00, 06:00) vorhanden |
| Blöcke im Urteilsfenster | H1/H3 43 à 15 T · H7 31 à 21 T (≥ 20 ✔) |
| Autokorrelation E (lag 1) | +0,06 / −0,04 / −0,07 / +0,02 — E ist fast unabhängig von Tag zu Tag |

**Die drei auffälligen Futures-Tage — Stunde für Stunde gegen die REST-Stundenkerzen geprüft:**

| Tag | Befund | Folge |
|---|---|---|
| 16.08.2023 | Archiv = Summe der REST-**Stunden**kerzen (1,0000); nur die REST-**Tages**kerze weicht um 3 % ab | Archiv stimmt |
| 28.10.2024 | Archiv in den Stunden 19–21 UTC über REST (Stunde 21 ×3,9) | offen, welche Seite fehlt; ein Tag der zweiten Epoche, Fluss als **Anteil** am Umsatz → klein |
| 27.10.2026 | Archiv in Stunde 00 nur ~50 % von REST | frische Datei — Nachlauf; außerhalb jeder Auswertung |

**Selbsttest** (`p102_wale_selbsttest.txt`, 1.000 Welten): ✔ **BESTANDEN**, Messung freigegeben (`p102_wale_selbsttest.json`)

| | Ergebnis |
|---|---|
| S1 Fehlalarm | **0,3–1,4 %** in allen 12 Zellen (Soll ≤ 5 %, Stufungsgrenze 1,4 %) |
| S2 Ballung | Blockvertauschung **1,4–4,2 %** (Soll ≤ 5 % ✔) · zirkuläre Verschiebung bis 5,4 % ✖ |
| **Nullwelt** nach Vorab-Regel | **Blockvertauschung** (nur sie hält S1 und S2) |
| D Orakel | 200 von 200 in allen 6 Zellen |
| **S3 Auflösung X** (k, D verschiebt um 2k) | BTC H1/H3 **1 Pp**, H7 2 Pp · ETH H1 1 Pp, H3 2 Pp, H7 über 2 Pp |

⚠️ **Was die Auflösung heißt:** Gefunden wird ein Unterschied zwischen oberstem und unterstem Fünftel ab **2 Pp in 1–3 Tagen**
(BTC) — das ist ein **großer** Effekt. Kleinere Vorsprünge sieht diese Messung nicht; ein „trägt nicht“ gilt nur **bis X**.
⚠️ S2 liegt über der Stufungsgrenze (bis 4,2 % statt 1,4 %): unter Ballung ist die Messung weniger streng als nominell — die
Punkte 2–7 (Jahre, q-Leiter, ETH, Schichten, Verzug) sind deshalb Pflicht, nicht Beiwerk.

---

## 10. ERGEBNIS (30.10.2026, `p102_wale_messung.txt`, Gegenprobe `p102_wale_gegenprobe.txt` ✔)

**Geltungsbereich:** BTC (Haupt) und ETH (zweiter Weg), Binance Spot und USDⓈ-M-Futures, Urteil 2025-01-01 bis 2026-09-30
(638 Tage), q 5 %, Einstieg 00:00 UTC nach dem Signaltag, Log-Ertrag brutto. D = oberstes minus unterstes Fünftel von E, in Pp.

### Spot: trägt NICHT nach der Vorab-Regel — aber durchgehend POSITIV

| | H1 | H3 | H7 |
|---|---|---|---|
| **BTC** D [Band] | +0,33 [−0,44 .. +1,10] | +0,71 [−0,52 .. +1,95] | +2,08 [−0,12 .. +4,28] |
| Stufe | TRÄGT NICHT BIS 2 Pp | TRÄGT NICHT BIS 2 Pp | NICHT TRENNBAR |
| 2025 / 2026 | +0,43 / +0,21 | +0,77 / +0,64 | +2,04 / +2,10 |
| q 1 / 5 / 10 / 20 % | alle positiv | alle positiv | alle positiv |
| Schichten Fall / Mitte / Anstieg | −0,48 / +0,96 / +0,38 | +0,33 / +0,68 / +1,13 | +0,37 / +2,40 / +3,41 |
| Verzug 06:00 | +0,48 | +0,82 | +2,10 |
| **ETH** D | +0,61 (NICHT TRENNBAR) | +1,29 (TRÄGT NICHT BIS 4 Pp) | +1,86 (NICHT TRENNBAR) |
| Epoche 2023-07..2024-12 (BTC) | +1,04 **TRÄGT** | +1,27 | −0,12 |
| Vergleichsarme BTC: G roh / R roh | +0,06 / +0,15 | +0,50 / −0,27 | +1,48 / −0,11 |

Punkte 1–7 (BTC): ✖ ✔ ✔ ✖ ✔ ✔ ✔ in allen drei Horizonten — es fehlen **das Band** (1) und das **ETH-Band** (4).

### Futures: trägt NICHT

BTC D +0,31 / +0,40 / −0,09 (TRÄGT NICHT BIS 2 / 2 / 4 Pp), 2026 bei H1/H3/H7 negativ; ETH H3/H7 **negativ** (−0,57 / −0,84).
Das Vorzeichen wechselt zwischen Jahren und Werten — kein Muster.

### Zwischenfazit zum Ziel (ehrlich gewichtet)

| | |
|---|---|
| Fakt | Am **Spotmarkt** lag der Kurs nach Tagen mit starkem Netto-Großkauf (nach Abzug von Restfluss und Tagesbewegung) in **jeder** Teilmenge höher als nach Tagen mit Netto-Großverkauf: BTC rund **+0,7 Pp in 3 T** und **+2 Pp in 7 T** |
| Warum kein Befund | Das Band schließt den Nullpunkt nicht aus. Die Messung sieht sicher erst ab **2 Pp** (Selbsttest) — der gemessene Wert liegt **darunter** bzw. knapp daran |
| ⚠️ Wie viel die Gleichförmigkeit wert ist | **weniger, als sie aussieht:** die q-Stufen teilen großteils dieselben Tage, BTC und ETH bewegen sich gemeinsam (dieselben Markttage), Verzug 06:00 ist fast derselbe Ertrag. **Unabhängig** sind nur die Jahre 2025/2026 und die frühere Epoche — und die sind alle positiv (außer BTC H7 2023-24) |
| Futures | zeigt nichts — passt zur Stichprobe (Futures-Große laufen mit dem Rest, §6 Voranalyse) |
| Herausrechnen | wirkt: E zeigt mehr als der rohe Großfluss (BTC H1 +0,33 gegen +0,06) — die Großen sind am Spot mehr als Begleitung der Bewegung (Lehre 2.665) |

⚠️⚠️ **Nutzervorgabe 29.10.: nicht abhaken, sondern Abstimmung und Lösungssuche.** Ein neuer Weg darf die Richtung nicht auf
**denselben** Daten nachträglich bestätigen — sonst ist er eine Wahl nach dem Ergebnis.

## 11. Lösungswege (zur Abstimmung)

| | Weg | warum | Daten |
|---|---|---|---|
| **a (Empfehlung)** | **Unabhängige Bestätigung**: dieselbe Rechnung, **gerichtet** (aus 2025–26: oberstes Fünftel höher), auf Jahren, die noch **niemand gesehen** hat: Spot BTC und ETH **2019–2022**, dazu **SOL** (dritter Kernwert, 2021–2026) | die einzige Prüfung, die eine Richtung **bestätigen** kann; einseitig ist zulässig, weil die Richtung **vorher** feststeht; ~190 statt 43 Blöcke → Auflösung etwa halb so grob | Spot BTC 29,6 GB + ETH 12,3 GB + SOL 10,3 GB ≈ **52 GB, ~3 Std.** (HEAD gemessen 30.10.) |
| b | Stufe 2: Großfluss der letzten 24 h **vor REGEL0-Einstiegen** auf dem Kern, Horizont 24 h | näher am Betrieb, viele Fälle; aber **derselbe Zeitraum** → nicht unabhängig von dem, was wir gesehen haben | liegt vor (`stunde`) |
| c | Vorwärts sammeln (NB-Abrufer) | sauberste Unabhängigkeit | ⛔ Jahre bis zu genug Blöcken (stehende Regel: keine Zwei-Jahres-Lösung) |

⚠️ Zu **a**: 2019–2022 ist eine **andere Marktepoche** (Memory: Krypto hat sich geändert). Trägt es dort nicht, ist das allein kein
Widerspruch — deshalb je Jahr ausweisen. Binance Spot BTC war bis **22.03.2023** gebührenfrei (Ankündigung im V1-Archiv); der
**Beginn** (nach meinem Wissen 08.07.2022) liegt vor dem Archiv (ab 01/2023) und wird beim Laden an Dateigröße und
Geschäftszahl je Tag **nachgewiesen**, nicht angenommen. Die relative Schwelle fängt den aufgeblähten Umsatz auf; getrennt
ausgewiesen.

---

> ## ⚠️ FASSUNG 3 — UNABHÄNGIGE BESTÄTIGUNG (30.10.2026, VORAB: vor jedem Wert auf 2019–2022 und auf SOL)
>
> **Nutzer 30.10.:** *„Ok a, laden und wie immer prüfen, gegenprüfen, Doku“* (§11 Weg a). **Anlass:** Fassung 1/2 trug nach der
> Vorab-Regel nicht, war aber am Spot in jeder Teilmenge positiv (§10). Eine Richtung darf nur auf **ungesehenen** Daten bestätigt
> werden. Stand beim Festlegen: Spot BTC/ETH 2019–2022 und SOL werden **geladen**, kein Wert ist gerechnet.
>
> | | Festlegung |
> |---|---|
> | **Hypothese** | **gerichtet** (aus 2025–26): am **Spot** liegt der Ertrag nach Tagen im **obersten** Fünftel von E **höher** als nach Tagen im untersten. E, q 5 %, Fünftel, Einstieg 00:00 UTC t+1, Log-Ertrag brutto — **unverändert** aus Fassung 1/2 |
> | **Hauptwert** | **BTC**, Urteil **2020-01-01 bis 2022-12-31**; 2019 ist Vorlauf für Schätzfenster (180 T) und Rang (Fünftel ab 2019-08-29) |
> | Horizonte | 1 / 3 / 7 T → **3 Hypothesen**, **einseitig**, Bonferroni: Untergrenze des einseitigen Bandes bei 5 %/3 |
> | Blöcke | wie Fassung 1 (`messnorm._block`), erwartet 2020–22 ≈ 73 à 15 T bzw. 52 à 21 T |
> | Nullwelt | Blockvertauschung 15 T (Selbsttest 29.10.) — der Selbsttest läuft **neu** auf den Erträgen 2020–22, **einseitig**, 1.000 Welten, sonst keine Messung |
>
> **BESTÄTIGT** verlangt **alle** Punkte (BTC 2020–22, q 5 %):
>
> | # | Punkt |
> |---|---|
> | 1 | Untergrenze des einseitigen Bandes **über** dem Nullpunkt |
> | 2 | Jahre 2020, 2021, 2022 einzeln: D > 0 in ≥ 2 von 3 |
> | 3 | q-Leiter 1 / 5 / 10 / 20 %: D > 0 in ≥ 3 von 4 |
> | 4 | **ETH** 2020–22: D > 0 **und** einseitige Untergrenze über dem eigenen Nullpunkt (streng, wie Fassung 2) |
> | 5 | Schichten nach Tagesbewegung: D > 0 in ≥ 2 von 3 |
> | 6 | Verzug 06:00: D > 0 |
> | 7 | **SOL** (Urteil 2021-07-01 bis 2026-09-30, ungesehener Wert): D > 0 |
> | 8 | Selbsttest bestanden |
>
> **Auskunft ohne Urteil:** BTC 2022-07 bis 2022-12 getrennt (Binance BTC gebührenfrei — der Beginn wird an Umsatz und
> Geschäftszahl je Tag **nachgewiesen**); BTC gepoolt 2020–2026 (enthält die gesehenen Jahre, deshalb kein Urteil); SOL mit Band.
>
> | Ergebnis | Folge |
> |---|---|
> | **BESTÄTIGT** | Spot-Großfluss wird **Bewertungszeile für den Kern** (§8): Spot-Einstieg auslösen/zurückhalten, Hebel-Wahrscheinlichkeit, Begründung in der Mail — danach Kostenprüfung, Bauentscheid, NB-Abrufer |
> | **nicht bestätigt** | Abstimmung und Lösungssuche (Nutzer 29.10.); ⚠ 2019–22 ist eine **andere Epoche** — ein Nichtbestätigen dort widerlegt 2025–26 nicht allein; die Jahre einzeln ausweisen |

### Fassung 3 — Download, Vorprüfung, Selbsttest (30.10.2026 nachts, vor jedem echten Ergebnis)

| | |
|---|---|
| **Download** | Spot BTC/ETH 2019-01-01 bis heute je **2.858 Tage**, SOL **2.270 Tage** ab Handelsbeginn 11.08.2020 (davor gibt es keine Datei), 0 Ausfälle |
| **Gebührenfreiheit nachgewiesen** | Spot BTC ab **08.07.2022**: Geschäfte je Tag 0,89 → 3,99 Mio. (×4,5), Umsatz ×2,8; ab 22.03.2023 zurück (11,9 → 2,3 Mrd $/Tag) |
| **Vorprüfung** (`p102_wale_vorpruefung_f3.txt`) | ✔ BESTANDEN — Archiv = Kerze (Spot 1,0000–1,0011), Stichprobe exakt, Stunden = Tag, Blöcke BTC/ETH 74 (H7 53), SOL 128 (H7 92) |
| Kurslücken | **nur 06:00** und bei **allen** Werten gleich (Binance-Ausfälle 12.03., 15.05., 15.08.2019, 30.11.2020, 25.04.2021) → Börsenausfall, nur die Verzugsprobe verliert diese Tage. SOL 29.11.2020 endet 23:48 (derselbe Ausfall) |
| ⚠️ **Eigene Fehler, von der Gegenprüfung gefunden** | (1) die Vollständigkeitsabfrage hatte kein Anfangsdatum (zählte 2019–22 in Fassung 1 mit), (2) Kurse je Tag neu geladen (Laufzeit). Beide behoben; Fassung 1 Messung/Gegenprobe/Vorprüfung danach **bitgleich** |
| **Selbsttest** (`p102_wale_selbsttest_f3.txt`, 1.000 Welten, einseitig) | ✔ BESTANDEN — S1 Fehlalarm **1,0–1,7 %**, S2 Ballung **2,1–3,7 %** (Soll ≤ 5 %, Stufungsgrenze 2,5 %), Orakel 200/200 in allen 9 Zellen, Nullwelt Block |
| **Auflösung X** (D-Unterschied 2X) | BTC H1/H3 **1 Pp** (D 2 Pp), H7 2 Pp · ETH H1 1, H3/H7 2 · SOL H1/H3 1, H7 2 |

⚠️⚠️ **Die Auflösung ist NICHT feiner geworden** (erwartet: etwa halb so grob). Mehr Blöcke, aber 2020–22 schwankte der Kurs
deutlich stärker (2021) — beides hebt sich auf. **Was das für die Bestätigung heißt** (Fundquote aus S3 bei der Größe, die
Fassung 1 gemessen hat): BTC H3 D +0,71 ≈ k 0,35 → rund **15 %**; BTC H7 D +2,08 ≈ k 1,0 → rund **50 %**. Eine Bestätigung ist also
nur wahrscheinlich, wenn der Effekt in 2020–22 **größer** war als 2025–26 — ein **Nichtbestätigen** wäre bei dieser Stärke das
**erwartete** Ergebnis und **kein** Beleg gegen den Effekt.

## 13. ERGEBNIS FASSUNG 3 — unabhängige Bestätigung (30.10.2026, `p102_wale_messung_f3.txt`, Gegenprobe `p102_wale_gegenprobe_f3.txt` ✔)

**Nutzer 30.10. vor der Messung:** *„Messen und Vergleichen ja, aber die Erwartung, dass [Epochen] das gleiche Ergebnis liefern
sollen, ist nicht realistisch. Das gilt m. E. für alle Messungen.“* — die Epochen-Punkte unten sind in diesem Licht zu lesen.

| BTC Spot, 2020–22 (ungesehen) | H1 | H3 | H7 |
|---|---|---|---|
| D [einseitige Untergrenze] · Nullpunkt | **+1,26 [+0,16]** · +0,08 | +1,36 [−0,27] · +0,03 | +0,88 [−1,72] · +0,52 |
| Stufe | ✔ **TRÄGT (oberstes Fünftel HÖHER)** | NICHT TRENNBAR | TRÄGT NICHT BIS 4 Pp |
| 2020 / 2021 / 2022 | +1,75 / +1,05 / +0,99 | +0,75 / +1,10 / +2,16 | +0,66 / +0,70 / +0,95 |
| q 1 / 5 / 10 / 20 % | alle positiv | 3 von 4 | 2 von 4 |
| Verzug 06:00 | +0,81 | +0,93 | +0,01 |
| **ETH** 2020–22 | +0,66 (TRÄGT NICHT BIS 2) | +1,99 (NICHT TRENNBAR) | +2,26 (NICHT TRENNBAR) |
| **SOL** 2021-07–2026-09 | +0,58 | +0,78 | **−0,75** |
| Punkte 1–8 | ✔ ✔ ✔ **✖** ✔ ✔ ✔ ✔ | ✖ ✔ ✔ ✖ ✔ ✔ ✔ ✔ | ✖ ✔ ✖ ✖ ✔ ✔ ✖ ✔ |
| **Urteil (Vorab-Regel)** | nicht bestätigt — **nur** Punkt 4 (ETH-Band) fehlt | nicht bestätigt | nicht bestätigt |

### Zwischenfazit zum Ziel

| | |
|---|---|
| ✔ **Belegt** | Auf **ungesehenen** Jahren trägt der Spot-Großfluss bei **BTC über 1 Tag** für sich (Band über dem Nullpunkt, Bonferroni 3, einseitig): nach Tagen mit starkem Netto-Großkauf lag BTC am Folgetag **+1,26 Pp** höher als nach Tagen mit Netto-Großverkauf — in jedem Jahr 2020, 2021, 2022 positiv, auch beim Einstieg erst um 06:00 |
| ⚠️ Warum trotzdem „nicht bestätigt“ | der vorab strenge zweite Weg: ETH ist in allen drei Horizonten **positiv**, sein Band schließt den Nullpunkt aber nicht aus |
| Bild über alle Daten (Fakt) | BTC H1: 2020 +1,75 · 2021 +1,05 · 2022 +0,99 · 2025 +0,43 · 2026 +0,21 — **immer positiv, aber kleiner geworden** (Epoche, Nutzerhinweis 30.10.) |
| ⚠️ Gegenrichtung | SOL H7 negativ (−0,75), BTC H7 schwach — über eine Woche zeigt sich **kein** Vorteil; wenn, dann **kurz** (1 Tag) |
| Herausrechnen | wirkt wieder: E trägt mehr als der rohe Großfluss (BTC H1 +1,26 gegen +0,92) |

**Gegenprobe** ✔: E bis 6·10⁻¹⁷, Fünftel 100 % gleich, D exakt, Bootstrap-Band 0,93–1,01 der t-Breite, alle Vorgriff-Mutationen erkannt.
