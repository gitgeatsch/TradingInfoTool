# Voranalyse M1-2 — der INFORMATIONSGEWINN des rsi-Modells als Regime-Kontext (30.09.2026)

**Auftrag (Nutzer 30.09.):** *„Ja bitte, prüfen und gegenprüfen. Nach M1 gehen wir in Abstimmung und Bewertung der Lage und
Ergebnisse."* Vorher: *„wir müssen u. U. zwischen Regime und kürzeren Wetterwechseln, also Trendumkehr, unterscheiden können"* und
*„deine Auslegung teile ich"*.
**Vorher:** 2.694 (Verlust im Gegenwind), 2.696 (das rsi-Modell ist in 8 von 20 Monaten fast flach), M1 Schritt 0 und M1-1
(`Voranalyse_Kern_Short_30_09.md` Abschnitte 10–11).

> **Urteil in einer Zeile:** Wir prüfen, ob Kern-Einstiege in Monaten, in denen das rsi-Modell **weniger Information als zuletzt**
> hat, schlechter laufen. **Ehrlich vorab:** Auf 2024 ist das nicht wählbar, und 2025–26 ist gesehen. Deshalb gibt es heute nur
> eine **Auskunft**, und das **Urteil** fällt auf den Monaten ab 2026-09.

---

## 0. Ziel, Stand, Test oder Betrieb

| | |
|---|---|
| **Ziel** | Regime von Wetter unterscheiden, und zwar über die Frage *„trägt unser Werkzeug gerade?“*, nicht *„ist Bullen- oder Bärenmarkt?“*. Einfach gesagt: Nicht die Jahreszeit vorhersagen, sondern merken, wann das Werkzeug stumpf ist |
| **Stand** | Die Verluste sitzen im Gegenwind (2.694). Das Modell ist dort flach, im Kern Oktober bis Dezember 2025 **deutlich** (M1-1). Der **stetige Informationsgewinn** fällt genau dort |
| **Test oder Betrieb** | nur **Test**, Ebene A (Kontext) und B (Simulation als Auskunft) |

---

## 1. Das Maß — vorab festgelegt, keine gewählte Zahl

| | |
|---|---|
| **IG** | Informationsgewinn des Monatsmodells = Validierungsverlust *flach* (Stufe 2.000.000) minus Verlust der gewählten Stufe, je 1.000 Trainingsanker (M1-1) |
| **K_IG** ⭐ | IG des Monats ÷ **Median der 6 Vormonate** (mindestens 3). **Relativ**, weil IG mit dem wachsenden Training steigt (2024 ≈ 0,3–1,0, 2025–26 ≈ 0,6–2,5). Absolute Grenzen wären nicht übertragbar (wie bei der v̂-Skala, E-31) |
| **Grenze** | **K_IG < 1** heißt *weniger Information als zuletzt*. Das ist die **natürliche** Grenze (unter dem eigenen jüngsten Median), **nicht** aus Daten gewählt |
| **vorab bekannt?** | ✔ Das Modell ist nur auf Stunden vor Monatsbeginn geschätzt (−24 h), IG steht also zum Monatsanfang fest |
| **Art** | **Kontext** (E-20): für alle Assets gleich, verschiebt alle Einstiege eines Monats |

**Die Werte (bestand, aus M1-1, nur das Modell):**

| | K_IG < 1 (*wenig*) | K_IG ≥ 1 |
|---|---|---|
| 2024 | Apr, Jun, Jul, Aug (**keine** Kern-Einstiege, das Modell war dort flach) | Mai, Sep–Dez |
| 2025 | Mai (0,94), **Sep–Dez (0,44–0,63)** | Jan–Apr, Jun–Aug |
| 2026 | Jan (0,98), Aug (0,78) | Feb–Jul |

---

## 2. ⚠️ Warum heute kein Urteil möglich ist — gegengeprüft

1. **2024 ist nicht wählbar.** In **keinem** Monat mit K_IG < 1 gab es Kern-Einstiege. Der Kern hat sich dort selbst abgeschaltet
   (v̂ ≥ +0,035 bei 0 %). Die Frage *„sind Einstiege in schwachen Monaten schlechter?“* kommt 2024 gar nicht vor.
2. **2025–26 ist gesehen.** Die Monatswerte des Kerns (24 h Ruhe) stehen in 2.688, zum Beispiel 2025-10 −0,127 und 2025-12 −0,080,
   aber auch 2025-09 +0,107. Ein *bestanden* dort wäre zum Teil **Rückschau**.
3. **Wenige Einheiten:** Der Kontext wechselt je **Monat**. 2025–26 hat 7 *wenig*-Monate und 13 andere. Das ist eine Handvoll
   Regimewechsel, wie beim Wetter (2.686).

➤ Deshalb **zwei Teile**:

---

## 3. Teil A — AUSKUNFT auf 2025–26 (heute, 4 Mengen), ausdrücklich kein Urteil

| # | was |
|---|---|
| **A1** | Kern + Ruhe 48 h: Chance (Dq) der Einstiege in *wenig*-Monaten gegen die übrigen, je Menge, je Jahr |
| **A2** | **Umkehr oder Abschwächung?** Liegt Dq in *wenig*-Monaten **≤ 0** (Umkehr, dann wäre eine **Sperre** zulässig, E-20) oder nur **kleiner** (dann ein **Gewicht**, etwa die Hebelstufe)? |
| **A3** | **Monats-Nullwelt:** die K_IG-Kennzeichen über die 20 Monate **zufällig vertauscht** (1.000 Ziehungen). Wie oft ist der Unterschied im Zufall so groß? Einheit ist der **Monat**, nicht der Einstieg |
| **A4** | **Erfolgsmessung:** Rohvorteil je Handel (N4-Simulation, feste Zelle aus 2.690) in *wenig*- gegen übrige Monate, und der Rohvorteil **ohne** die *wenig*-Monate gegen die 0,48 % Kosten |
| A5 | Tagesblock-Bootstrap, Spiegel (E-29), mit/ohne 10./11.10.2025 |

---

## 4. Teil B — URTEIL auf den Monaten ab 2026-09 (Vorwärtstest), vorab festgelegt

| | |
|---|---|
| Regel | **K_IG < 1** (unverändert, keine Anpassung nach Teil A) |
| Urteil | sobald **≥ 3 *wenig*-Monate** und **≥ 3 übrige** mit Einstiegen vorliegen: Dq(übrig) − Dq(*wenig*) > 0 und Rohvorteil ohne *wenig*-Monate höher, in ≥ 3/4 Mengen |
| Form | Sperre nur bei **Umkehr** (A2), sonst Gewicht |
| ⚠️ | Das kann Monate dauern. Die Messbasis braucht dafür neue Monate (Nachladen ab 2026-09) |

---

## 5. Prüfung und Gegenprüfung

| Prüfung | wie |
|---|---|
| **R-R11** | IG und K_IG bitgleich zu M1-1; 48-h-Einstiege und Dq bitgleich zu 2.691/2.692 |
| **Nullwelt** | Monats-Vertauschung (A3) |
| **Zeitstabilität** | 2025 und 2026 getrennt (2026 hat nur 2 *wenig*-Monate) |
| **Weglassprobe** | Kern mit gegen ohne *wenig*-Monate |
| **Mehrfachtesten** | eine vorab feste Grenze (1), keine Wahl |
| **Je Asset** | Auskunft |
| **Ebene** | A (Kontext) · B (Simulation nur Auskunft) |
| **Vorgriff** | IG nur aus dem Training vor dem Monat |

---

## 6. Umfang

Werkzeug `messe_losfahren.py --kern --ruhe 48 --m1` (Teil A1–A3, A5) und die N4-Simulation mit einer Monatsmarke (A4). Etwa 4 × 8 Minuten
plus 4 × 12 Minuten → **Stopp und Bericht** → danach wie abgestimmt **Abstimmung und Bewertung der Lage** (Nutzer).

**Im Plan vorgemerkt (nicht jetzt):** **M1-3** den Kern stabilisieren (feineres Dämpfungsraster oder geglättete Dämpfung), weil
das Signalangebot heute zufällig springt. Das ändert den Kern, also gibt es eine neue Wahl und eine neue Bestätigung.

---

## 7. Zur Abstimmung (T1–T4)

| # | Vorschlag |
|---|---|
| **T1** | K_IG relativ (÷ Median der 6 Vormonate), Grenze **1** vorab fest |
| **T2** | Teil A **nur als Auskunft** auf 2025–26 (A1–A5), ausdrücklich kein Urteil |
| **T3** | Teil B: das **Urteil** auf den Monaten ab 2026-09, Regel unverändert |
| **T4** | danach die **Abstimmung und Bewertung der Lage** (wie von dir vorgegeben). M1-3 bleibt vorgemerkt |
