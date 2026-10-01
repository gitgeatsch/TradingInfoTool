# Voranalyse B — den Kern stabilisieren (M1-3), mit der Ursache der Verluste als Auskunft (ENTWURF 01.10.2026, zur Abstimmung)

**Auftrag:** Nutzer 01.10. nach 2.702: *„deine Empfehlung – A, dann B, und eigentlich kannst du, wenn es passt, die Ursache für die
Verluste behandeln – aber du bist hier der Experte."* Dazu: *„die Minus-Trades und die Marktphasen sind ohnehin ein eigenes Thema
und können nicht vollends durch eine einfache mathematische Rechnung gelöst werden."*
⚠️ **Das ist nur ein Entwurf.** Es wird nichts gemessen und nichts gebaut, bevor du Ja sagst.

> **Urteil in einer Zeile:** B ändert **nur, wie das rsi-Modell jeden Monat seine Dämpfung wählt**, und zwar feiner statt in
> Zehnersprüngen. Ziel ist, dass das Signalangebot nicht mehr **zufällig** von Monat zu Monat springt. Vorher zeigt eine Auskunft,
> **wo** die Verluste der REGEL0 entstehen, damit wir sehen, welchen Teil B überhaupt treffen kann.

---

## 0. Ziel, Stand, Test oder Betrieb

| | |
|---|---|
| **Ziel** | Ein Kern, dessen Signalangebot dem **Markt** folgt und nicht dem **Schätzer**. Das ist Pflicht vor jedem Betrieb (Lagebewertung 30.09., REGEL0-Dokument Schwäche 2) |
| **Stand** | M1-1 (Kern-Short-Voranalyse Abschnitt 11): Die Dämpfung wird je Monat aus **6 Stufen im Faktor 10** gewählt (`GITTER_NEU` 20 … 2.000.000). In vielen flachen Monaten liegen 2.000 und 20.000 **fast gleichauf**. Kippt die Wahl, springt die Spannweite von v̂ (0,47 gegen 0,24) und der Kern schaltet sich ab (2024: 5 Monate ohne einen Einstieg). Echt flach ist nur **Oktober bis Dezember 2025** (deutlicher Abstand) |
| **Test oder Betrieb** | Test, Ebene A (Bewertung 1). Es ändert den Kern, also gibt es eine **neue Wahl und eine neue Bestätigung** gegen die REGEL0 (E-33: REGEL1 gegen REGEL0) |

**Was B NICHT kann:** Die echte Flachheit im Gegenwind (Oktober bis Dezember 2025) bleibt. Dort trägt rsi nach dem Modell wirklich
nichts. Das ist das Thema **Marktphasen** (R, eigenes Thema laut Nutzer), nicht B.

---

## 1. Teil 0 — AUSKUNFT: Wo entstehen die Verluste der REGEL0? (kein Urteil, keine Regel)

Bekannt ist schon: Der Vorteil je Handel liegt in den unverzerrten Mengen bei +0,33..+0,35 % und damit **unter den Kosten** von 0,48 %
(2.690/2.694), auf deiner Liste darüber (+0,82..+0,87 %, 2.700). Im Gegenwind ist er negativ (2.697). Was fehlt, ist die **Aufteilung**
der Verluste, und zwar aus **einer** Rechnung:

| Achse | Frage |
|---|---|
| Kosten gegen Rohvorteil | Wie viel des Kontoverlusts sind Gebühren und Finanzierung, wie viel sind Verlusthandel selbst? |
| Monatsklasse | Gegenwind (K_IG < 1, aus 2.697) gegen den Rest; und **knappe** Stufenwahl gegen deutliche (M1-1) |
| später eingestellt oder nicht | Treffen die Verluste vor allem Paare, die **später** eingestellt wurden? (2.697 Punkt 3; nur in unverzerrt) |
| Hebelstufe | 2x, 3x, 5x |
| Asset | die 10 größten Verlustbringer je Menge, und wie viel die übrigen tragen |

**Umsetzung:** `messe_k6_hebelstufe.py --spur` schreibt heute nur die Spot-Rendite. Erweitert um Hebelstufe, Hebelrendite, Kosten und
Monat; die Aufteilung rechnet ein kleines eigenes Skript aus der Spur. R-R11: Die Summe der Teile muss das REGEL0-Konto **bitgleich**
ergeben (+0,2708 / −0,4887 / −0,4592 / −0,4065).

➤ **Wozu fürs Ziel:** Wir sehen, **welcher Anteil** der Verluste überhaupt aus dem Schätzer-Kippen kommen kann (B), welcher aus dem
Gegenwind (R, Marktphasen) und welcher aus schwachen oder später eingestellten Assets (Grundgesamtheit, deine Idee O9). Damit ist B
nicht blind.

---

## 2. Teil B — die Messung (Vorschlag)

| | |
|---|---|
| **F0 = REGEL0** | 6 Stufen, Faktor 10, Wahl per Kreuzvalidierung (4 Zeitblöcke). Referenz, **bitgleich** zur REGEL0 (R-R11) |
| **F1 feines Raster** | 16 Stufen von 20 bis 2.000.000 im Faktor ≈ 2,15 (drei Stufen je Zehnerschritt), sonst identisch |
| **F2 stetige Dämpfung** | wie F1, dazu der Tiefpunkt der Verlustkurve über log λ durch die drei besten Nachbarn **interpoliert** (Parabel). Keine zusätzlichen Schätzungen, nur genauer |
| Nicht im Vorschlag | λ über Monate glätten: Die Kreuzvalidierung nutzt schon die **ganze** Historie ab 2023 (wachsendes Fenster). Eine Glättung über Monate wäre doppelt und träge |
| Schwelle | Die v̂-Skala hängt an der Dämpfung. Deshalb wird die Schwelle **je Form neu gemessen**, mit derselben Regel wie 2.699: Raster +0,010..+0,050, größter Abstand *echt − P90 Nullwelt*, bei Gleichstand (< 0,005) die niedrigere Stufe, nur 2024, Menge bestand |
| Einstieg sonst | unverändert REGEL0: Ersteintritt, Ruhe 48 h, J, BTC, Einstieg 1 h später |

**Maß für das Springen (vorab festgelegt):** je Monat die Spannweite P99−P1 von v̂. Das Springen ist der **Median von |log(Spannweite
Monat / Spannweite Vormonat)|** über die Monate. Dazu die Zahl der **Abschaltmonate** (Spannweite so klein, dass kein Einstieg möglich ist).

**Wahl auf 2024 (bestand), per Regel:**
1. Eine Form zählt nur, wenn sie **weniger springt** als F0 **und** ihr Abstand *echt − P90 Nullwelt* nicht mehr als 0,005 unter dem von F0 liegt (Stabilität darf die Chance nicht kosten).
2. Unter diesen gewinnt der größte Abstand *echt − P90 Nullwelt* an der je Form gemessenen Schwelle (dasselbe Maß wie 2.699).
3. Gleichstand (< 0,005): die **einfachere** Form (F1 vor F2).
4. Erfüllt keine Form Punkt 1: **B nicht bestanden**, ohne Bestätigung.

**Bestätigung einmal 2025–26, 4 Mengen:** die Kriterien des Kerns wie 2.688 (B1–B6), dazu
- in ≥ 3/4 Mengen **weniger Springen** als F0,
- in ≥ 3/4 Mengen das Hebelkonto (REGEL0-Erfolgsmessung, 24 h, ohne Stop) **mindestens so gut** wie die REGEL0.
- Auskunft: Abschaltmonate, Informationsgewinn K_IG je Monat, Teil 0 für die neue Form.

---

## 3. Prüfung und Gegenprüfung

| | |
|---|---|
| R-R11 | F0 über den neuen Code bitgleich zur REGEL0 (Einstiege zeilengleich, Konto gleich) |
| Gegenprüfung | Für 3 Monate (ein knapper, ein deutlicher, ein normaler) Verlustkurve und gewählte λ von Hand nachgerechnet |
| Nullwelt | wie 2.688 (verschobene rsi-Modelle) |
| Zeitstabilität | je Jahr, Juli–Dezember 2025 getrennt |
| Spiegel | wie 2.688 |
| Weglassprobe | ohne 10./11.10.2025 |

---

## 4. ⚠️ Zwei Punkte, die du wissen solltest, bevor du Ja sagst

| # | |
|---|---|
| **1. Die Bestätigungsjahre werden knapp** | 2025–26 ist jetzt für J, BTC, A und dann B je **einmal** bestätigt worden. Jede einzelne Bestätigung war vorab festgelegt, aber je mehr Stufen wir auf denselben 20 Monaten prüfen, desto eher hält eine Stufe dort zufällig. ➤ Vorschlag: Besteht B, gilt es als **bestätigt, Vorwärtstest ausstehend**. Das Urteil auf den neuen Monaten ab 2026-09 (C) wird damit wichtiger. Bisher liegt dort ein Monat |
| **2. Betrieb (E-35)** | Das feinere Raster heißt im Monatstraining **16 statt 6** Schätzungen je λ-Kurve, am Notebook also etwa **2,7-mal** so lange. Ich messe die Trainingszeit am Desktop und rechne sie für den T440 hoch. Sonst ändert sich am Betrieb nichts, kein neuer Datenbedarf |

---

## 5. Umfang

| | Zeit (Desktop, geschätzt) |
|---|---|
| Teil 0: Spur erweitern, 4 Simulationen (REGEL0, unverändert) und Aufteilung | etwa 1 h |
| Teil B Wahl 2024: F0/F1/F2 je mit Schwellenmessung | etwa 1 h |
| → **Stopp und Bericht** (Teil 0 und Wahl) | |
| Bestätigung nach deinem Ja: 4 Mengen, Kern und Simulation | etwa 2–3 h |

---

## 6. Zur Abstimmung (B1–B4)

| # | Vorschlag |
|---|---|
| **B1** | **Teil 0** zuerst: die Verluste der REGEL0 aufteilen (Kosten, Monatsklasse, später eingestellt, Hebelstufe, Asset). Nur Auskunft |
| **B2** | **F1** feines Raster und **F2** stetige Dämpfung gegen F0, Schwelle je Form neu gemessen |
| **B3** | Wahl 2024 per Regel (weniger Springen als Pflicht, dann Chance, dann die einfachere Form), Bestätigung einmal in 4 Mengen |
| **B4** | Besteht B: Vermerk **bestätigt, Vorwärtstest ausstehend** |
