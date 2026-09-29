# Voranalyse KERN Schritt 2 — H0 und das ZEITFENSTER: gilt die ATR-Hebeltabelle auf den Einstiegen, und in welchem Fenster messen wir? (29.09.2026)

**Nutzer:** *„ja, H0 Voranalyse schreiben — prüfen und gegenprüfen. Wichtig: das Thema Liquidation hatten wir schon, ja,
kann man prüfen, aber die Erfolgsmessung kann man als Vergleich heranziehen, aber nicht als Kalibrierung. Wichtig: wie
lange oder welches Fenster hast du genutzt, um zu messen — 12 h oder Tage? Hebel ist kurz, schnell, hoch — hier
entscheiden Stunden."* Und: *„Vorsicht, der Cooldown ist jetzt nicht das Thema — es geht um das ZEITFENSTER, das du zur
Messung nutzt."*

> **Urteil in einer Zeile:** Unsere Fenster sind **nicht** auf einen kurzen, schnellen Hebel abgestimmt — der Erfolg ist in
> **24 h** gemessen, das Risiko in K6 hauptsächlich in **72 h**, und **kürzer als 24 h wurde der Kern nie gemessen**. H0 wird
> darum über eine **Fensterachse 6 / 12 / 24 h** gemessen (72 h nur als Anschluss an K6), für Chance **und** Risiko im
> **selben** Fenster. Kalibriert wird nur aus der Liquidation, der Erfolg steht daneben. Test, nicht Betrieb.

---

## 0. Welche Fenster wir heute nutzen — ehrlich

| Messung | Fenster | passt zu *kurz, schnell, hoch*? |
|---|---|---|
| Signal (rsi) | RSI der letzten **14 h**, gegen die eigenen **30 Tage** | ✔ Stunden |
| Ersteintritt | davor **24 h** unter der Schwelle, Einstieg **1 h** nach dem Signal | ✔ Stunden |
| **Erfolg** (Bewertung 1) | +5 % vor −5 % binnen **24 h** | ⚠️ ein Tag — *ob* es in 2, 6 oder 20 Stunden kommt, sieht man nicht |
| **Risiko** (Bewertung 2, K6) | Liquidation binnen **24 / 72 / 120 h**, Hauptfall **72 h** | ⛔ drei Tage — für einen schnellen Hebel zu lang, und **nicht** dasselbe Fenster wie der Erfolg |
| kürzer als 24 h | – | ⛔ **nie gemessen** für den Kern |

➤ **Fachlich:** Ein Hebel entscheidet sich in den **ersten Stunden** — ein Rückgang, der bei 5x nach 6 Stunden liquidiert,
kommt in einer 24-h-Rate vor, ist aber etwas **anderes** als ein Rückgang nach 20 Stunden. Die Abstimmung K4 (27.09.) nennt
das Fenster ausdrücklich eine **Achse** (*Höhe × Fenster*) — für den Kern ist sie **nicht gemessen**. Das ist die Lücke,
auf die deine Frage zeigt.

---

## 1. Was bringt das für das Ziel?

| wenn H0 über die Achse … | dann | fürs Ziel |
|---|---|---|
| **hält** (in 6, 12 und 24 h) | die ATR-Tabelle gilt für die Einstiege, **gleich in welchem Fenster** | Bewertung 2 (**wie viel Hebel**) für den Kern belegt |
| **in kurzen Fenstern riskanter** | ein **gemessener** Aufschlag je Fenster und Stufe | Bewertung 2 mit Korrektur — und eine klare Vorgabe für die Positionsführung |
| **hält nicht** | Ursache messen, Lösung vorlegen (Nutzer: *Lösung MUSS*) | – |

---

## 2. Was schon feststeht (2.681, alle Anker, Markpreis, bestand)

| | 24 h | 72 h |
|---|---|---|
| 5x Liquidationsrate | 4,1 % | 17,5 % |
| 5x Kalibrierung | Steigung 0,86 | Steigung 0,93, V1 ✔ |
| 3x Liquidationsrate | 0,33 % | 1,86 % |
| auf *rsi oben* (Zustand) beobachtet / geschätzt | 5x 0,76 · 3x 0,63 | 5x 0,90 · 3x 0,58 |

---

## 3. Der Aufbau

| | |
|---|---|
| **Einstiege** | die Ersteintritte aus Schritt 1 (s = +0,035), 2024-01 bis 2026-08, **zu jeder Stunde** — exportiert aus `messe_losfahren.py --kern --export` (Datei in `data/_vergleich/`, nicht committet) |
| **Werkzeug** | `messe_k6_hebelstufe.py --einstiege <Datei>`: dasselbe Risikomodell wie 2.681 (ATR allein, rollierend, Markpreis, m = 0,09), auf dem 6-h-Gitter geschätzt, **ausgewertet an den Einstiegsstunden** |
| ⭐ **Fensterachse** | Liquidation binnen **6 / 12 / 24 h** (neu), 72 h als Anschluss an K6 — für 5x, 3x, 2x |
| **Risiko-Maß** | je Stufe und Fenster **beobachtet / geschätzt**, je Jahr 2024 / 2025 / 2026; wo genug Fälle: Kalibrierung je Zehntel |
| **Chance im selben Fenster** (Vergleich, nicht Kalibrierung) | für dieselben Einstiege: +5 % vor −5 % binnen **6 / 12 / 24 h** gegen das Normal, und die **Zeit bis +5 %** und bis −5 % (Median, Quartile) — *wann* passiert es? |
| **Vergleich je Stufe** | wie oft erreicht der Einstieg **+5 % vor der Liquidation** — nur ausgewiesen |
| **Black Swan** | mit / ohne 10./11.10.2025 |

## 4. Die Kriterien — vorab

| # | Bedingung | bei Nein |
|---|---|---|
| **H0-0** | R-R11: ohne `--einstiege` gibt das Werkzeug **2.681 bitgleich** (5x/72 h beob 17,493 %, gesch 17,627 %, bestand, Markpreis) | nicht weiter |
| **H0-1** ⭐ | **5x** in **jedem** Fenster 6 / 12 / 24 h: beobachtet / geschätzt zwischen **0,5 und 1,25**, gesamt und je Jahr, in ≥ 3 von 4 Mengen | H0-2 |
| **H0-2** | über **1,25** in einem Fenster: der **gemessene Faktor** wird als Aufschlag je Fenster ausgewiesen — eine Lösung, kein Scheitern | – |
| **H0-3** | 3x und 72 h: Auskunft (3x hat wenige Fälle) | – |
| ⚠️ | unter 0,5 (sicherer als gedacht) ist **kein** Grund für mehr Hebel — die Tabelle bleibt vorsichtig | – |

---

## 5. Prüfung und Gegenprüfung

| Falle | Gegenmittel |
|---|---|
| Erfolg fließt in die Hebelstufe | ⛔ ausgeschlossen: Schätzung und Grenze nur aus der Liquidation; q5 nur daneben |
| Chance und Risiko in verschiedenen Fenstern | **dieselbe** Achse 6 / 12 / 24 h für beide |
| kurze Fenster, wenige Fälle | 5x liquidiert in 24 h bei ~4 % der Anker — in 6 h deutlich seltener; Fallzahl je Fenster wird ausgewiesen, Urteil nur mit ≥ 30 Liquidationen |
| Gitter gegen Einstiegsstunde | Modell auf dem Gitter geschätzt, Liquidation an der **echten** Stunde |
| Einstieg und Tief aus derselben Reihe | Markpreis für beides (2.679) |
| Teilmengenregel | genau das ist H0 |
| Black Swan | mit/ohne |
| Kleine Läufe täuschen | volle Daten; zuerst `bestand` (Stufe 1), dann die übrigen drei Mengen |

---

## 6. Zur Abstimmung (H1–H4)

| # | Punkt | Empfehlung |
|---|---|---|
| **H1** | Fensterachse **6 / 12 / 24 h** für Risiko und Chance, 72 h nur als Anschluss | ja |
| **H2** | Kalibrierung nur aus der Liquidation, Erfolg nur als Vergleich | ja |
| **H3** | Kriterien H0-0 bis H0-3 wie Abschnitt 4 | ja |
| **H4** | zuerst `bestand`, die übrigen drei Mengen danach | ja |

---

## 7. Umfang

Export der Einstiege (je Menge ein kurzer Lauf) · `messe_k6_hebelstufe.py --einstiege` mit der Fensterachse bauen und
vorab committen · R-R11 · `bestand` (etwa 1–1,5 h) · Stopp · die übrigen drei Mengen.

---

## 8. ✔ ABGESTIMMT (29.09.2026) — H1 bis H4; Umsetzung VOR dem Lauf

**Nutzer:** *„ja, H1 bis H4 wie empfohlen — prüfen und gegenprüfen — dann Ergebnis bewerten, detailliert."*

| | |
|---|---|
| **Export** | `messe_losfahren.py --kern --export 0.035` je Menge → `data/_vergleich/kern_einstiege_<menge>.csv` (Symbol, Stunde, Jahr, Zeit bis +5 %, Zeit bis −5 %), 2024-01 bis 2026-08. Derselbe Lauf gibt die **Chance im Fenster** 6 / 12 / 24 h aus (gegen den rohen 12-Monats-Normal **je Fenster** — nur Vergleich) und die **Zeit bis +5 % / −5 %** |
| **H0** | `messe_k6_hebelstufe.py --kurs mark --einstiege <csv>`: Fensterachse 6 / 12 / 24 / 72 / 120 h; Modell ATR allein rollierend auf dem Gitter wie 2.681; Liquidation an den **Einstiegsstunden** mit Markpreis (Einstieg und Tief aus derselben Reihe, Fenster ohne fehlende Stunde) |
| ⚠️ **Abweichung H0-0** | die Reproduktion von 2.681 läuft **im selben Lauf** über den unveränderten Gitter-Codepfad (5x/72 h atr: 17,493 / 17,627) statt in einem **eigenen** Lauf ohne `--einstiege`. **Grund:** das spart 1–1,5 h je Menge; die 72-h-Zahlen hängen nicht an den zusätzlichen Fenstern (je Fenster ein eigenes Modell). Im Einstiegsmodus entfallen **V2** (Mehrwert der Risikokurven, in 2.681 entschieden) und die **Tabelle** |
| Ablauf | Export für alle vier Mengen · H0 `bestand` · technische Prüfung · H0 für die übrigen drei · Stopp · detaillierte Bewertung |


---

## 9. ERGEBNIS — Befund 2.689 (Stopp, gemeinsame Bewertung)

**Risiko: beobachtet / geschätzt** (Kalibrierung nur aus der Liquidation)

| | bestand | unverzerrt:1 | unverzerrt:2 | unverzerrt:3 | Liquidationen |
|---|---|---|---|---|---|
| 5x · 6 h | 0,36 | 0,41 | 0,35 | 0,52 | 22–35 (Fallgrenze) |
| 5x · 12 h | 0,42 | 0,43 | 0,40 | 0,45 | 71–85 |
| **5x · 24 h** | **0,48** | **0,56** | **0,56** | **0,59** | 228–304 (1,9–2,5 % der Einstiege) |
| 5x · 72 h | 0,76 | 0,81 | 0,80 | 0,81 | 1.563–1.825 |
| 3x · 24 h / 72 h | 0,50 / 0,47 | 0,88 / 0,59 | 0,73 / 0,56 | 0,94 / 0,59 | 18–40 / 107–158 |

- ✔ H0-0 bitgleich. Nirgends über 1,25 — **die Tabelle unterschätzt das Risiko der Einstiege nie**; sie ist **vorsichtig**.
- ⚠️ 2025 bei 72 h 0,94–0,95 — im schwachen Regime ist der Sicherheitsabstand fast weg.
- ⚠️ 2x: alle Liquidationen am **10./11.10.2025** (ohne ihn 0,0–0,4) — Black Swan, nur Störfaktor.
- H0-1 formal (0,5–1,25) in 12 h nicht erfüllt, in 24 h in 3 von 4 — jeweils auf der **sicheren** Seite; nach Abschnitt 4
  bleibt die Tabelle, wie sie ist.

**Chance im selben Fenster** (nur Vergleich)

| Fenster | +5 % zuerst | −5 % zuerst | Dq gegen den Normal |
|---|---|---|---|
| 6 h | 6,7–7,0 % | 4,4–4,7 % | +0,10 |
| 12 h | 14,3–15,0 % | 9,7–10,3 % | +0,10 |
| 24 h | 25,1–26,0 % | 19,8–20,8 % | +0,07..+0,08 |

**Zeit bis +5 %** (wo zuerst): Median **19–20 h**, Quartile 9 / 35 h, binnen 6 h nur **16 %**, binnen 12 h 33–34 %.
**Zeit bis −5 %**: Median 24–25 h.

➤ **Folge:** (1) Bewertung 2 für den Kern belegt — die ATR-Tabelle gilt und ist vorsichtig, **kein Aufschlag**. (2) Der
Kern ist ein **Tageshandel**, kein Stundenhandel — ein Hebel über wenige Stunden erreicht +5 % selten; **Haltedauer und
Zielhöhe** werden in Schritt 3 als **Achse** gemessen, nicht gesetzt. (3) Das schwache Regime ist Pflichtfrage für
Schritt 3.
