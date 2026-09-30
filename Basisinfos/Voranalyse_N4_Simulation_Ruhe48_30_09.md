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
