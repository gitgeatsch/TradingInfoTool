# Voranalyse L4 — die Summe auf dem Kern (30.09.2026)

**Auftrag (Nutzer 30.09.):** *„Ja"* zur L4-Voranalyse mit volumenschub als Vergleichsarm, danach ein Zwischenfazit.
**Vorher:** 2.688 (Kern), 2.690 (Simulation verliert an den Kosten), 2.691 (L2), **2.692 (N3)**.

---

## 1. Worum es geht — und was es fürs Ziel bringt

Die Bausteine sind gemessen. L4 setzt sie zu **einer** Bewertung zusammen und legt die **Schwelle** fest — per Regel, nicht
per Wahl (E-24):

| Baustein | Rolle | Befund |
|---|---|---|
| **Kern**: rsi-Ersteintritt, s = +0,035 | A — *ob* (Ereignis, Schalter) | 2.688, 2.691 |
| **Ruhe 48 h** davor | Regel am Kern (Einstiegsform) | 2.691, 2.692 |
| **ema_abstand_atr** | B — *wie weit* (Potential) | 2.692, Form per Regel |
| volumenschub | B — *wie weit* | **Vergleichsarm** (2.692) |
| ATR | C — *wie viel Hebel* | 2.681, 2.689 — unverändert, Bewertung 2 |

**Fürs Ziel:** Heute ist jeder Kern-Einstieg gleich viel wert, weil der Kern ein Schalter ist. L4 gibt jedem Einstieg eine
**Zahl**, das **erwartete Potential**, und die Schwelle darauf wählt die Einstiege mit dem **meisten zu holen** aus. Das ist die
Aussage *„wie viel ist hier zu holen"* aus dem übergeordneten Ziel. Außerdem beantwortet L4 die erste Hälfte von **H-Schalter**:
Ordnet die Summe?

---

## 2. ⚠️ Die Grundsatzfrage vorab (P1) — was misst die Summe?

**Stand im Regelwerk:** Bewertung 1 = Summe der **Chance**-Beiträge (Ereignis +5 % vor −5 %, q5). **Gemessen ist aber:** ema und
volumenschub heben das **Potential**, **nicht** die Chance (2.692). Summierte man sie auf die Chance, fielen sie heraus. Sie
würden sie sogar senken (ema eigen −0,04..−0,10).

| Möglichkeit | was | Folge |
|---|---|---|
| **(a)** ⭐ Vorschlag | Die Summe ist das **erwartete Potential** (MFE 24 h in eigener ATR über dem Normal). Der **Kern** bleibt das Ereignis (*ob*), die **Chance** läuft als Auskunft mit | entspricht W2 (Lösungsweg 30.09.: *Potential als Zielgröße*), den Rollen A/B/C (25.09., geprüft 29.09.) und dem Ziel *wie viel ist zu holen*. Regelwerk § 1 wird **präzisiert**: Bewertung 1 = Ereignis (Kern) + Potential-Summe |
| (b) | die Summe bleibt auf der **Chance** | ema und volumenschub haben dort nichts. L4 bestünde nur aus Kern + Ruhe, und die Wucht ginge verloren |

⚠️ **Neutral bleibt es in beiden Fällen**: keine Kosten, keine Börse (Nutzer 30.09.). Das Potential ist eine Marktgröße.

---

## 3. Die Messung — vorab festgelegt

**Menge:** die Kern-Ersteintritte mit **48 h Ruhe** (s = +0,035). **Maß:** Potential (MFE 24 h / ATR minus eigenes Normal).
**Auskunft:** Chance (q5), Risiko (Rückgang vor dem Hoch), Einstiege je Tag.

| Arm | Summe | Rolle |
|---|---|---|
| **A** (Urteil) | Kern-Potential + **Beitrag(ema)**. Der Beitrag ist das mittlere Potential je ema-**Fünftel** minus das Mittel, Grenzen und Werte nur aus **2024** | die Form per Regel (2.692) |
| **B** (Vergleich) | Kern-Potential + Beitrag(ema) + Beitrag(volumenschub), **gemeinsam** geschätzt (lineare Rechnung auf beiden Fünftel-Kurven, 2024), sodass nichts doppelt zählt (ρ 0,33–0,45) | vorab festgelegter Vergleichsarm |
| C (Auskunft) | die 3×3-Tafel ema × volumenschub (Gewicht-Form, *beide oben*) | nur Auskunft, die nächste Loop-Ebene |

**Schwelle per Regel (auf 2024):**
- **Stufen** sind die Summen-Quantile der 2024-Einstiege: alle, oberste 50 %, 33 %, 20 %, 10 %.
- **Regel:** die Stufe mit dem größten Abstand *echt − P90 Nullwelt*. Echt ist das mittlere Potential der ausgewählten Einstiege. Die Nullwelt ist die Summe aus dem **je Asset verschobenen** Beitrag, 40 Ziehungen.
- Bei **Gleichstand** (< 0,01 ATR) wird die **niedrigere** Stufe gewählt, also mehr Einstiege (wie K5).
- Die Schwelle gilt für Arm A. Arm B bekommt nach derselben Regel seine eigene.

**Bestätigung** einmal 2025-01..2026-08, **4 Mengen**, Urteil für Arm A:

| # | Kriterium | Art |
|---|---|---|
| **L4-1** | Potential der Ausgewählten minus Potential **aller** 48-h-Einstiege > **Null-P90**, in **2025 und 2026** > 0, **Tagesblock** untere Grenze > 0, **≥ 3 von 4 Mengen** | Urteil |
| **L4-2** | **Ordnet die Summe?** Beobachtetes gegen vorhergesagtes Potential je Summen-Fünftel: Steigung **> 0,5**, in ≥ 3/4 Mengen | Urteil (erste Hälfte H-Schalter) |
| L4-3 | Chance und Risiko der Ausgewählten gegen alle 48-h-Einstiege, je Asset, Einstiege je Tag, Prozentmaß | Auskunft |
| L4-4 | Arm B gegen Arm A (dieselben Kriterien), Arm C | Auskunft, geht an N4 |

⚠️ **Ehrlich zur Datenlage:** 2025–26 ist für die Bausteine schon gesehen (2.691, 2.692), für **Kalibrierung und Schwelle**
nicht. Der ungesehene Prüfstein sind die Monate **ab 2026-09**.

---

## 4. Prüfung und Gegenprüfung

| Prüfung | wie |
|---|---|
| **R-R11** | 48-h-Einstiege 1.486 (2024) bzw. 6.328 (bestand 2025–26), Potential +0,069 / +0,087, bitgleich zu 2.691 N2 |
| **Nullwelt** | Beitrag je Asset verschoben, 40 Ziehungen |
| **Zeitstabilität** | 2025 und 2026 getrennt |
| **Weglassprobe** | Arm A gegen *alle 48-h-Einstiege* (ohne Beitrag); Arm B gegen A (mit/ohne volumenschub) |
| **Mehrfachtesten** | 5 Stufen, nur auf 2024 gewählt; ein Urteil auf 2025–26 |
| **Auswahlanteil** | Gegenprüfung: die Ausgewählten gegen **gleich viele zufällig** gezogene 48-h-Einstiege (40 Ziehungen, P90). Sonst misst L4-1 nur die Härte |
| **Je Asset** | Anteil der Assets, deren Ausgewählte über ihren eigenen 48-h-Einstiegen liegen (Auskunft, ≥ 10 je Asset) |
| **Ebene** | A, neutrale Bewertung ohne Kosten. Die Wirtschaftlichkeit prüft erst **N4** |

---

## 5. Umfang und Ablauf

Wie N3: Werkzeug `messe_losfahren.py --l2 --l4` → Funktionstest → **Commit** → Wahl 2024 (etwa 8 Minuten) → **Stopp und
Bericht** → nach deinem Ja die Bestätigung (4 × etwa 8 Minuten). Danach **N4** (Simulation, Erfolgsmessung) und **H-Schalter**.

---

## 6. Zur Abstimmung (Q1–Q5)

| # | Vorschlag |
|---|---|
| **Q1** ⭐ | **(a)** die Summe misst das **erwartete Potential**, der Kern bleibt das Ereignis, die Chance ist Auskunft. Das Regelwerk § 1 wird so präzisiert |
| **Q2** | Arm A = Kern + Ruhe 48 h + ema (Fünftel-Kurve aus 2024), Arm B = + volumenschub gemeinsam geschätzt (Vergleich), Arm C Auskunft |
| **Q3** | Schwelle **per Regel** auf 2024: fünf Stufen, größter Abstand zur Nullwelt, bei Gleichstand die niedrigere |
| **Q4** | Bestätigung einmal 2025–26, L4-1 und L4-2 als Urteil, ≥ 3/4 Mengen |
| **Q5** | danach N4 (Arm A, Arm B als Vergleich) und H-Schalter |


---

## 7. ✔ ABGESTIMMT (30.09.2026) — Q1 bis Q5; Umsetzung VOR dem Lauf

**Nutzer:** *„Ja — planen, prüfen, gegenprüfen, Doku, dann messen, Ergebnisse abstimmen mit weiterem Zwischenfazit."*

**Gegenprüfung der Vorlage gegen das Regelwerk.** Die Zeile *Bewertung 1* hält fest: *ein Lift allein zeigt vor allem **mehr
Bewegung** (2.657)*, und *der Rückgang vor dem Hoch steigt mit, das ist die **Größe** der Bewegung, kein Vorteil (2.662)*. Ein
höheres Potential kann also bloß **mehr Bewegung in beide Richtungen** sein. Darum kommt, **vor** der Rechnung, eine fünfte
Prüfung als Urteil dazu. Sie **verschärft** die Vorlage und stützt sich auf die bestehende Regel, sie ist keine neue Zahl:

| # | Kriterium | Art |
|---|---|---|
| **L4-5** ⭐ | **Spiegel — Vorteil oder nur Bewegung?** Anteil *+5 % binnen 24 h* (gleich, was zuerst kommt) und Anteil *−5 % binnen 24 h*, jeweils Ausgewählte minus alle 48-h-Einstiege. **Vorteil**, wenn der Zuwachs oben **größer** ist als unten, in **2025 und 2026**, in **≥ 3 von 4 Mengen** | **Urteil** |

➤ Q1 gilt damit **so**: Die Summe misst das erwartete Potential, und das Potential zählt nur, wenn der Spiegel hält.

**Umsetzung (keine neue Wahl):**
- Werkzeug `messe_losfahren.py --l2 --l4`. Ohne `--bestaetigen` rechnet es die Wahl 2024 und schreibt `data/_vergleich/l2_l4_wahl_bestand.json`.
- Mit `--bestaetigen 0.035` wird einmal 2025–26 ausgewertet.
- Arm A hat nur **fünf** Summenwerte (die Fünftel). Die Stufen *50 / 33 / 20 / 10 %* fallen deshalb auf die nächste Fünftelgrenze. Der tatsächliche Anteil wird ausgewiesen, und *10 %* fällt mit *20 %* zusammen.
- Die Schwelle ist ein **fester Wert** der Summe aus 2024. In 2025–26 wird sie nicht neu als Quantil bestimmt.
- Arm B nimmt beide Fünftel-Kurven in eine gemeinsame lineare Rechnung auf 2024 (je vier Stufenmerkmale).
- Die Nullwelt verschiebt in Arm A ema je Asset, in Arm B ema und volumenschub.


---

## 8. ERGEBNIS WAHL 2024 (bestand) — Stopp, zur Abstimmung

Beleg `L2_29_09/l4wahl__bestand.txt`, Parameter in `data/_vergleich/l2_l4_wahl_bestand.json`. ✔ **R-R11:** 1.486 Einstiege mit
48 h Ruhe, Potential +0,069, bitgleich zu 2.691 N2. Alle 48-h-Einstiege 2024: Chance +0,162, Potential +0,069 ATR, 9,3 je Tag.

| Arm | Stufe per Regel | ausgewählt | Potential (alle +0,069) | Chance (alle +0,162) | Spiegel | Prozent MFE |
|---|---|---|---|---|---|---|
| **A** ema (Urteil) | *oberste 50 %* → tatsächlich **60 %** | 892 | **+0,108** | +0,180 | +0,019 | +0,25 Pp |
| **B** ema + volumenschub (Vergleich) | *oberste 20 %* → tatsächlich **25 %** | 371 | **+0,185** | +0,192 | **+0,066** | +1,44 Pp |
| C beide oben (Auskunft) | — | 323 (22 %) | +0,185 | +0,194 | +0,068 | |

**Die Regel angewandt (nachgerechnet):**
- Arm A: Die Abstände sind +0,039 / +0,032 / +0,031 / +0,044. Die schärfste Stufe liegt nur 0,005 höher, das gilt als Gleichstand, also bleibt es bei **50 %**.
- Arm B: +0,044 → +0,061 → **+0,072** → +0,081. Der letzte Schritt liegt unter 0,01, also bleibt es bei **20 %**.

⚠️ **Gegenprüfung:**
1. **Die ema-Kurve von Arm A ist nicht monoton.** Die Fünftel liegen bei −0,080 / −0,020 / −0,036 / **+0,094** / +0,043. Die
   Schwelle nimmt darum Fünftel 2 mit und lässt Fünftel 3 weg. Das ist sehr wahrscheinlich **Rauschen** der Fünftel-Mittel (je
   etwa 300 Einstiege) und kein Befund. Die Form war vorab festgelegt und bleibt. Die Bestätigung zeigt, ob die Kurve hält (L4-2).
2. **Arm B** ist 2024 deutlich stärker. Das Potential liegt beim 2,7-Fachen von *alle*, der Spiegel ist positiv, in Prozent sind es +1,44
   Prozentpunkte, und die Chance steigt mit. Das passt zu N3, wonach volumenschub 2025–26 eigen ist. Arm B bleibt aber
   **Vergleich**, wie abgestimmt.
3. Der **Spiegel ist 2024 in allen Armen positiv**: Oben steigt es stärker als unten, es ist also nicht nur Bewegung. Das Urteil fällt erst 2025–26.
4. Die **Chance** steigt 2024 mit (+0,18..+0,19 gegen +0,16). In 2025–26 tat sie das bei N3 nicht, 2024 ist ein Bullenjahr.
5. Nur **2024**, 190 Tage.
