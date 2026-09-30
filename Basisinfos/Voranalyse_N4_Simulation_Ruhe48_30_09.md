# Voranalyse N4 — Simulation: Kern + Ruhe 48 h als Erfolgsmessung (30.09.2026)

**Auftrag (Nutzer 30.09.):** *„Ja gut, sauber und schrittweise vorgehen, prüfen und gegenprüfen."*
**Vorher:** 2.690 (Simulation des Kerns mit 24 h Ruhe verliert an den Kosten), 2.691/2.692 (Ruhe 48 h trägt eigen), 2.693
(die Wucht ist Bewegung, keine Richtung).

> **Urteil in einer Zeile:** Wir spielen **dieselbe** Simulation wie 2.690 mit **denselben** Einstellungen, nur mit den
> besseren Einstiegen (48 h Ruhe) durch. Das zeigt, ob die bessere Richtung die Lücke zu den Kosten schließt. Test, nicht Betrieb.

---

## 0. Ziel, Stand, Test oder Betrieb

| | |
|---|---|
| **Ziel** | *Ist das Potential nach Hebel und Kosten echtes Geld?* Das ist die Erfolgsmessung (Ebene B), keine Bewertung |
| **Stand** | Der Kern mit 24 h Ruhe hat einen Rohvorteil je Handel von +0,12..+0,33 % (2025–26) gegen **0,48 %** Kosten je Tageshandel (2.690). Mit 48 h Ruhe steigen Chance (+0,01..+0,04) und Potential (+0,014..+0,032 ATR) je Einstieg, und es gibt etwa 40 % weniger Einstiege (2.691/2.692) |
| **Test oder Betrieb** | ⛔ nur **Test**. Nichts fließt in die Bewertung zurück (Regelwerk *Kosten*: nur Erfolgsmessung und Positionsführung) |
| ⚠️ **Erwartung, ehrlich** | eher **gering**. Die Verbesserung je Einstieg ist klein gegen die Lücke von etwa 0,15–0,35 Prozentpunkten. Darum **schrittweise** (Abschnitt 4) |

---

## 1. Was bringt das für das Ziel?

| wenn … | dann | fürs Ziel |
|---|---|---|
| das Hebelkonto nach Kosten wächst (S1–S4) | Kern + Ruhe 48 h ist ein **handelbares** Potential | der erste belegte Handel |
| der Rohvorteil steigt, aber unter 0,48 % bleibt | die Richtung hilft, reicht aber nicht; die Lücke ist **gemessen** | die Arbeit gehört dann auf die **Richtung** (H-Schalter, Short-Kern) und die **Positionsführung** (W4) |
| der Rohvorteil nicht steigt | die Ruhe hilft nur statistisch, nicht je Handel | ebenso, mit klarerem Befund |

⭐ Dazu die **Auskunft zur Wucht** (Rolle B, 2.693): Bringen die großen Bewegungen *beide oben* bei fester Haltedauer mehr
oder weniger, und wie viel **Hoch** (MFE) läge darin für eine Positionsführung mit nachgezogenem Stop (W4)? Das ist die
Grundlage dafür, wo Rolle B hingehört.

---

## 2. Der Aufbau — dieselbe Anlage wie 2.690

| | |
|---|---|
| **Einstiege** | die Kern-Ersteintritte (s = +0,035) mit **48 h Ruhe** (davor mindestens 40 gültige Stunden, keine über der Schwelle), Einstieg 1 h später, 2024-01..2026-08. Export `data/_vergleich/kern48_einstiege_<menge>.csv` im selben Format wie 2.689 |
| **Werkzeug** | `messe_losfahren.py --kern --export 0.035 --ruhe 48` (neu: `--ruhe`, ohne Angabe 24 wie bisher) und `messe_k6_hebelstufe.py --kurs mark --einstiege <csv> --simulation 24,ohne,0.02` |
| **Zelle** | ⭐ **FEST aus 2.690**: H = 24 h, **ohne** Ziel, Grenze **2 %**. **Keine** neue Wahl. So ändert sich nur die Einstiegsmenge (Weglassprobe 24 gegen 48 h), ohne weiteres Mehrfachtesten |
| **Hebel, Liquidation, Kosten** | unverändert: höchste Stufe unter der Grenze aus dem ATR-Modell (rollierend), Bitpanda-Formel am Markpreis-Tief, 0,3 % + 0,18 %/Tag auf den Positionswert, +1 % bei Liquidation |
| **Konto** | f = 1 % je Handel, log-Wachstum |
| **Vergleich** | Spot 1x (dieselben Einstiege), Nullwelt (Einstiege je Asset zeitverschoben, 40 Ziehungen), mit/ohne 10./11.10.2025 |

**Neu, nur Auskunft (keine Bewertung):**
- **N4-R Rohvorteil je Handel** auf den Positionswert (Spot, ohne Kosten), neben den **0,48 %**. Die entscheidende Zahl aus 2.690.
- **N4-W Wucht:** Rohvorteil und Konto für *beide oben* (Kanten aus N3) gegen den Rest, dazu das mittlere **Hoch binnen 24 h** (MFE) beider Gruppen. Das zeigt, wie viel eine Positionsführung *hätte holen können* (W4).

---

## 3. Die Kriterien — wie 2.690

| | Kriterium |
|---|---|
| **S1** | Hebelkonto wächst in **2025 und 2026** |
| **S2** | über dem **P90 der Nullwelt** |
| **S3** | **≥ 3 von 4** Mengen |
| **S4** | Hebelkonto **über** dem Spotkonto |
| **S5** | mit/ohne 10./11.10.2025 ausgewiesen |
| Pflichtauskunft | Juli–Dezember 2025 (Gegenwind) |

---

## 4. Schrittweise — Stufe 1 zuerst (Nutzerregel *lange Messung nur nach Vorprüfung*)

| Stufe | was | Dauer | weiter, wenn … |
|---|---|---|---|
| **0** | Werkzeugtest: der Export mit `--ruhe 24` ist **bitgleich** zur Datei aus 2.689 (R-R11), und die 48-h-Datei hat 1.486 Einstiege in 2024 (L4) | wenige Minuten | beides stimmt |
| **1** | **bestand**, Bestätigung der festen Zelle, mit N4-R und N4-W | etwa 12 min | Stufe 2 folgt, wenn **S1 in bestand hält oder der Rohvorteil ≥ 0,48 %** ist. Sonst **Stopp**: bestand war in 2.690 die beste Menge, und die übrigen liegen erfahrungsgemäß darunter |
| **2** | unverzerrt:1–3 | etwa 40 min | – |

⚠️ Der Stopp nach Stufe 1 ist **kein** Urteil über alle 4 Mengen. Er wird als *„in bestand nicht bestanden, übrige nicht
gerechnet (Abbruchregel)"* ausgewiesen.

---

## 5. Prüfung und Gegenprüfung

| Prüfung | wie |
|---|---|
| **R-R11** | Export `--ruhe 24` bitgleich zur 2.689-Datei; die Simulation meldet R-R11 2.681 im selben Lauf; 48-h-Einstiege 2024 = 1.486 |
| **Nullwelt** | zeitverschobene Einstiege, 40 Ziehungen (wie 2.690) |
| **Zeitstabilität** | 2025 und 2026 getrennt, dazu der Monatsverlauf |
| **Weglassprobe** | **dieselbe** Zelle wie 2.690, nur die Einstiege anders; Spot gegen Hebel |
| **Mehrfachtesten** | keins neu: die Zelle ist fest |
| **Je Asset** | Auskunft: Anteil der Assets mit positivem Rohvorteil |
| **Ebene** | B, Erfolgsmessung. ⛔ Ergebnisse gehen **nicht** in die Bewertung zurück |
| Vorgriff | ATR-Modell rollierend, Ausstieg nur aus Stunden **nach** dem Einstieg (unverändert) |

---

## 6. Zur Abstimmung (R1–R4)

| # | Vorschlag |
|---|---|
| **R1** | die **feste** Zelle aus 2.690 (24 h, ohne Ziel, 2 %), keine neue Wahl |
| **R2** | Einstiege Kern + Ruhe 48 h (Export mit `--ruhe 48`), Kriterien S1–S5 wie 2.690 |
| **R3** | Auskunft N4-R (Rohvorteil gegen 0,48 %) und N4-W (Wucht: Rohvorteil, Konto, MFE) |
| **R4** | **schrittweise**: Stufe 0 Werkzeugtest, Stufe 1 bestand, Stufe 2 nur nach der Regel aus Abschnitt 4 |

---

## 7. ✔ ABGESTIMMT (30.09.2026) — R1 bis R4; Stufe 0 bestanden

**Nutzer:** *„Ja, bitte prüfen und gegenprüfen."*

| Stufe 0 (Werkzeugtest) | Ergebnis |
|---|---|
| Export `--ruhe 24` in eine Wegwerfdatei | ✔ **bitgleich** zu `kern_einstiege_bestand.csv` aus 2.689 (12.630 Zeilen, `cmp`) |
| Export `--ruhe 48` (bestand) | 2024 **1.486** · 2025 **3.224** · 2026 **3.104**, ✔ bitgleich zu L2/N2 (2.691) |
| 48 h in 24 h enthalten | 100 % |
| Auskunft Chance 24 h (Export) | 48 h +0,116 gegen 24 h +0,082 (2024 +0,160 / 2025 +0,062 / 2026 +0,152) |
| Wucht *beide oben* | 1.163 von 7.814 (14,9 %), `kern48_wucht_bestand.csv` |
| Fehler im Test, behoben | Die Wucht-Kanten wurden neben der Wegwerfdatei gesucht statt in `data/_vergleich`. Der Pfad ist jetzt fest, am Inhalt ändert sich nichts |

Simulation: `messe_k6_hebelstufe.py --kurs mark --einstiege kern48_einstiege_<m>.csv --wucht kern48_wucht_<m>.csv --simulation 24,ohne,0.02`,
neu sind nur die Auskünfte N4-R und N4-W.


---

## 8. ERGEBNIS — Befund 2.694

Belege `Basisinfos/N4_Sim_30_09/` (`best__<menge>.txt`, `export__<menge>.txt`, `rr11_probe24__bestand.txt`, `_kette.log`).
**Ablauf nach R4:** In Stufe 1 hielt bestand S1, und der Rohvorteil lag bei 0,573 % ≥ 0,48 %. Darum folgte Stufe 2 mit allen Mengen.

| | bestand | unverzerrt:1 | unverzerrt:2 | unverzerrt:3 |
|---|---|---|---|---|
| **Hebelkonto** 48 h Ruhe (log / Faktor) | **+0,204 / ×1,23** | −0,466 / ×0,63 | −0,417 / ×0,66 | −0,382 / ×0,68 |
| zum Vergleich 2.690 (24 h Ruhe) | ×0,62 | ×0,26 | ×0,34 | ×0,28 |
| S1 2025 / 2026 | ✔ +0,189 / +0,015 | ⛔ −0,187 / −0,279 | ⛔ −0,152 / −0,265 | ⛔ −0,050 / −0,333 |
| S2 Nullwelt P90 | ✔ −1,342 | ✔ −1,563 | ✔ −1,420 | ✔ −1,515 |
| S4 Spot | ✔ +0,165 | ⛔ −0,005 | ⛔ +0,006 | ⛔ +0,005 |
| S5 ohne 10./11.10. | +0,307 | −0,201 | −0,132 | −0,284 |
| **N4-R Rohvorteil je Handel** | **+0,573 %** | **+0,294 %** | **+0,311 %** | **+0,309 %** |
| zum Vergleich 2.690 | +0,33 % | +0,14 % | +0,17 % | +0,12 % |
| Juli–Dezember 2025 | ×0,80 | ×0,56 | ×0,59 | ×0,66 |
| Assets mit positivem Rohvorteil | 83 % | 72 % | 68 % | 67 % |

➤ **N4 NICHT bestanden** (S3: nur 1 von 4). Die **Richtung wirkt aber im Geld:** Der Rohvorteil je Handel verdoppelt sich in allen 4
Mengen, Spot verliert nicht mehr, und die **Lücke** zu den 0,48 % Kosten **halbiert** sich auf etwa **0,17–0,19 Prozentpunkte**
(unverzerrt).

**N4-W Wucht (Auskunft):**

| | bestand | unv:1 | unv:2 | unv:3 |
|---|---|---|---|---|
| *beide oben*: Rohvorteil / Hoch binnen 24 h | +0,55 % / +5,54 % | −0,03 % / +5,90 % | +0,13 % / +5,81 % | −0,15 % / +5,92 % |
| Rest: Rohvorteil / Hoch binnen 24 h | +0,58 % / +3,92 % | +0,33 % / +3,89 % | +0,34 % / +3,90 % | +0,37 % / +3,92 % |

➤ Die Wucht bringt **mehr Hoch** und **weniger Rohvorteil**: Die großen Bewegungen kehren binnen 24 h wieder um. Das bestätigt
2.693 (Bewegung, keine Richtung). Für die **Positionsführung** (W4, nachgezogener Stop) liegt darin ein Kandidat. Ob sich davon
etwas **halten** lässt, zeigt nur eine Messung. Das MFE ist das Höchste, was möglich gewesen wäre, kein erreichbarer Wert.

**Prüfung und Gegenprüfung:**
1. **R-R11** ist vierfach erfüllt: Export `--ruhe 24` bitgleich (cmp), 48-h-Einstiege bitgleich zu N2, der neue Rohvorteil-Code
   reproduziert 2.690 (+0,330 %, Spot +0,0286), und H0-0 ist je Menge bitgleich zu den 2.690-Läufen.
2. ⚠️ **Die Beschriftung** der R-R11-Zeile zeigte bei unverzerrt *„✔ bitgleich“*, obwohl dort nur bestand eine Referenz hat.
   Sie ist nach dem Lauf korrigiert, die Zahlen sind unverändert (wie beim K6-Label am 29.09.).
3. ⚠️ **Überlebensverzerrung:** bestand gewinnt als einzige Menge. Dort fehlen die **eingestellten** Paare (2.668/2.669), und der
   Rohvorteil liegt fast doppelt so hoch wie in unverzerrt. Das Urteil gilt auf **unverzerrt**. Das entspricht der Regel *die
   Grundgesamtheit ist keine Stellschraube*.
4. **Regime:** Der Verlust sitzt vor allem im zweiten Halbjahr 2025 und in 2026-06/07.

**Zwischenfazit zum Ziel:**

| | |
|---|---|
| ✔ | Der Weg **Richtung** trägt messbar ins Geld. Mit einer einzigen Regel am Kern (Ruhe 48 h) hat sich der Vorteil je Handel verdoppelt |
| offen | 0,17–0,19 Prozentpunkte je Handel fehlen noch bis zu den Kosten. Die Verluste liegen im Gegenwind-Regime |
| ➤ Wege | (1) **Richtung weiter** (H-Schalter, Short-Kern W3 für das Regime) · (2) **Positionsführung W4** (die Wucht bringt Hoch, das heute wieder verloren geht) · (3) Börse/Kosten L1 erst Phase 4/5 (Nutzerentscheidung) |
