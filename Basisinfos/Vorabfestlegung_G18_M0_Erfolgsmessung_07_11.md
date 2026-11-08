# Vorabfestlegung G18 M0 — Erfolgsmessung REGEL0 im Betrieb (07.11.2026)

> Zurück zum laufenden Plan: [`Gesamtplan.md`](Gesamtplan.md)

Nutzer 07.11.: *„ja G18 Beginnen - aber sollten wir nicht die neuesten Daten nehmen und nicht die von 4.11?“* · Grundlage: E-170 F-A,
[`Voranalyse_G18_Gesamtkonzept_06_11.md`](Voranalyse_G18_Gesamtkonzept_06_11.md) §1.3 und §5 (M0).

**Festgelegt, BEVOR eine Zahl je Signal angesehen wird.** Bekannt war vorher nur die Sammelzeile, die jede REGEL0-Mail ohnehin trägt
(NB-Export 07.11.: 1.960 Signale an 34 Tagen, „im Band“).

## 1. Was M0 kann und was nicht

- M0 **beschreibt**. Über das **Niveau** von REGEL0 entscheidet weiter E-139/E-140: brutto positiv, aber nicht robust. Der kleinste
  erkennbare Unterschied liegt vorwärts bei ≈ 1 Pp nach zwei Jahren, der erwartete Effekt bei ≈ 0,5 %.
- M0 **kann** einen groben **Bruch** zeigen: Daten, Zuordnung oder ein Regime, das die Regel umkehrt. Und M0 liefert die
  Ausgangslage für Regel1, Regel2 … (M1–M7).

## 2. Daten — die neuesten

| | Quelle | Stichtag |
|---|---|---|
| Signale + 24-h-Ausgänge | **frische** NB-Kopie `regel0_signale.db` (Backup-Schnittstelle, Quelle nur lesend) im Austauschordner | Zeitpunkt der Kopie |
| echte Trades (EUR) | jüngste NB-Sicherung `DB_Backups/tradinginfotool_*.db.gz`, Tabelle des Hebel-Buchs | Zeitpunkt der Sicherung |
| rückwärts Sep./Okt. 2026 | `data/_g7/regel0/b_einstiege_betrieb.csv` (Betriebsrechnung, G7 §10), 24-h-Ertrag aus der Kurs-Arbeitskopie `data/_g7/kurse` (bis 02.11.) | – |

Die Kopie vom 04.11. dient nur als **Prüfstand** für das Werkzeug. Gezählt werden nur Signale mit **abgeschlossenem** 24-h-Ausgang
(`ausgang.status = 'ok'`).

## 3. Was ausgewiesen wird

Die Rechnung ist die von `agent/regel0_messstand.py`: Einstieg = Schluss der Einstiegsstunde, 24-h-Ertrag brutto, Spanne 99 % über
**Tage** (ein Tag = eine Beobachtung), Referenz +0,545 % je Einstieg (Messung 2025-01 bis 2026-08).

| # | Teil | Mengen |
|---|---|---|
| D1 | Niveau gegen die Referenz | **alle** (Prüfung der Regel) · **gemailt** (was ankam) · je Hebelstufe |
| D2 | **E-138-Spur** (*Plus nur an marktweiten Tagen*): Tage mit **> 20** Signalen gegen **≤ 20** | nur Tage **ab 25.10.** (E-170 F-C: davor ist die Hypothese aus den Daten selbst entstanden) |
| D3 | Vorsprung gegen die **Drift**: 24-h-Ertrag minus Mittel aller Werte der Breite-Menge zur selben Stunde | **Auskunft**, nur bis 01.11. (Kurse der Arbeitskopie) |
| D4 | echte Trades: Zahl, Eigenkapital, Ergebnis **zum Schlusskurs** (nie „realisiert“), Bezug zum Signal | alle seit 03.10. |
| D5 | rückwärts **Sep./Okt. 2026** (die einzigen Monate, die nach R-R11 neu sind) | alle · Schalter-Werte |

Netto nach 0,48 % Hebelkosten steht **nachgelagert** daneben, nie als Urteilsgröße (Regel 2).

## 4. Urteilskriterium — vorab

| Befund | Bedingung | Folge |
|---|---|---|
| **kein Befund** | < 10 Tage | nur Zahlen |
| **im Band** | Referenz +0,545 % liegt in der 99-%-Spanne des Tagesmittels | **keine Handlung**. REGEL0 läuft wie gemessen; über das Niveau entscheidet weiter E-139/E-140 |
| **UNTER der Messung** | obere Spannengrenze < Referenz | **Bruch** → Ursachensuche (Daten, Zuordnung, Regime), danach Vorlage an den Nutzer. Kein automatisches Abschalten |
| **über der Messung** | untere Spannengrenze > Referenz | ebenfalls Ursachensuche (zu gut ist auch verdächtig) |
| D2 | **nur Beschreibung**: Vorzeichen und Abstand der beiden Tagesgruppen, je mit Spanne | ein Hinweis für M1 (Regel-Katalog), **kein** Befund. Dafür sind es zu wenige Tage |
| D5 | wie D1 gegen die Referenz | Auskunft. Kann E-139 nach R-R11 nicht umstoßen |

Werkzeug: `Rechenkern_02_10/g18_m0_erfolgsmessung.py` → `g18_m0_erfolgsmessung.txt`.

## 5. Prüfstand (07.11.2026, Kopie 04.11. — nur Form, `g18_m0_erfolgsmessung_pruefstand.txt`)

- **Gegenprobe:** D1 „alle“ ist gleich `regel0_messstand.stand()` auf derselben Kopie: 1.680 Signale, 31 Tage, +0,68 %,
  Halbbreite 1,69 Pp. Ebenso „gemailt“: 68 Signale, +1,22 %.
- Ein Fehler wurde gefunden und behoben: „Vorsprung gemailt“ war gleich „alle“, weil pandas `NaN` statt `None` trägt.
- Die Trades in EUR werden gelesen (2 Trades, −162,57 € zum Schlusskurs, wie §23.67). D5 rechnet Sep./Okt. aus der Arbeitskopie.
- ➤ **Die Messung selbst** läuft auf der **frischen** NB-Kopie, sobald sie im Austauschordner liegt.

## 6. Ergebnis (07.11.2026, frische NB-Kopie 17:13, Ausgänge bis 07.11. 05:50 · `g18_m0_erfolgsmessung.txt`)

| | n | Tage | Mittel brutto | Spanne 99 % | Befund (§4) |
|---|---|---|---|---|---|
| **D1 alle** | 1.960 | 34 | **+0,24 %** | −1,67 … +2,14 % | **im Band** → keine Handlung |
| D1 gemailt | 81 | 19 | +0,67 % | −2,03 … +3,38 % | im Band |
| D2 marktweit (> 20/Tag, ab 25.10.) | 526 | 7 | **−1,06 %** | −5,58 … +3,45 % | Beschreibung |
| D2 ruhig (≤ 20/Tag, ab 25.10.) | 68 | 5 | +0,25 % | −2,08 … +2,57 % | Beschreibung |
| D3 Drift der Breite-Menge (bis 31.10.) | 1.662 | 29 | +0,76 % | | Auskunft |
| **D3 Vorsprung alle gegen Drift** | 1.662 | 29 | **−0,08 %** | −0,53 … +0,37 % | Auskunft |
| D3 Vorsprung gemailt | 67 | 17 | +0,40 % | −1,18 … +1,97 % | Auskunft |
| D4 echte Trades | 2 | | −162,57 € zum Schlusskurs | | seit 09.10. kein neuer Trade |
| D5 Sep. / Okt. rückwärts, alle | 1.798 / 1.668 | 29 / 28 | +0,74 / +0,61 % | | im Band |

**Lesart, ohne mehr hineinzulegen:**
- **D1:** Der Betrieb läuft im Band der Messung, kein Bruch. Seit dem Prüfstand (04.11.: +0,68 %) ist das Mittel auf +0,24 % gefallen.
  Ursache ist **ein Tag**: Am 04.11. kamen 216 Signale mit −3,37 % im Mittel. Netto nach Kosten (nachgelagert): −0,24 %.
- **D3:** Im Oktober war das Plus von REGEL0 **das Plus des Markts**. Gegen das Mittel der Breite-Menge zur selben Stunde bleibt −0,08 %,
  mit einer engen Spanne (±0,45 Pp). Die Regel wählte in diesem Monat keine besseren Werte als den Durchschnitt. Das passt zu
  E-139 und zur Bilanz (*„kein Einstiegssignal mit belegtem Vorsprung“*).
- **D2:** Der erste Blick **nach** der Hypothese E-138 zeigt das **Gegenteil**: An marktweiten Tagen lag das Mittel unter dem an ruhigen.
  Getragen wird das vom 04.11. Nach §4 ist das **kein Befund** (7 gegen 5 Tage), aber ein Hinweis gegen die E-138-Spur für M1.
- **Folge für M1 (Regel-Katalog):** Jede neue Regel wird **gegen die Drift** gemessen, nicht gegen null und nicht gegen die absolute
  Referenz. Sonst misst sie den Markt.
