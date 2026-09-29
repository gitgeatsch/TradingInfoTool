# Voranalyse KERN Schritt 3 — die SIMULATION: verdient der Kern mit Hebel nach Kosten Geld? (29.09.2026)

**Nutzer:** *„ja, Voranalyse Schritt 3 schreiben — prüfen und gegenprüfen."* Dazu: *„ich war der Meinung, die Beiträge wären
optimiert, um genau dies über die Niveaus 2x, 3x und 5x abzudecken — hier stelle ich das Risiko ein über den Hebel. Also
ich hoffe, das ergibt sich aus der Messung für Schritt 3."*

> **Urteil in einer Zeile:** Die Simulation spielt die Ersteintritte mit Hebel aus der ATR, echten Kosten und einem Konto
> durch. **Alles Messbare wird gemessen** — die Haltedauer, das Ziel **und** die Liquidationsgrenze —, per vorab
> festgelegter Regel auf 2024, **einmal** bestätigt auf 2025–26. Test, nicht Betrieb.

---

## 0. Ziel, Stand, Test oder Betrieb

| | |
|---|---|
| **Ziel** | je Asset und Handlung eine begründete Aussage über das **Potential** — hier die Frage: *ist das Potential des Kerns nach Hebel und Kosten **echt Geld**?* |
| **Stand** | ✔ Einstieg trägt ungesehen (2.688) · ✔ die ATR-Hebeltabelle ist auf den Einstiegen vorsichtig (2.689) · der Kern ist ein **Tageshandel** (+5 % im Median nach 19–20 h) · stark **regimeabhängig** (Juli–Dezember 2025 negativ) |
| **Test oder Betrieb** | ⛔ nur **Test** (Ebene B, Erfolgsmessung). Nichts davon fließt zurück in die Bewertung; Betrieb erst nach der ganzen Kette inkl. LLM-Rollen |
| **Deine Frage** | ✔ ja: die Hebelstufe folgt **je Handel** aus dem gemessenen Risiko (ATR); die **eine** Grenze dazu wird hier ebenfalls **gemessen**, nicht von dir gesetzt (E-27) |

---

## 1. Was bringt das für das Ziel?

| wenn … | dann | fürs Ziel |
|---|---|---|
| das Hebelkonto nach Kosten **wächst**, ungesehen, jenseits des Zufalls | der Kern ist ein **handelbares** Potential | ein erster belegter Handel: Einstieg, Hebel, Ausstieg, Kosten |
| nur **ohne** Hebel (Spot 1x) etwas bleibt | der Hebel lohnt nicht — der Vorteil ist zu klein für das Risiko | Spot-Kern statt Hebel-Kern |
| **nichts** bleibt | Ursache messen (Kosten? Regime? Geometrie?), Lösung vorlegen (E-25) | – |

---

## 2. Die Grundlage

| | Quelle |
|---|---|
| Einstiege | die Ersteintritte, s = +0,035, 2024-01 bis 2026-08, `data/_vergleich/kern_einstiege_<menge>.csv` (2.688/2.689) |
| Hebelstufe | die **höchste** Stufe (5x / 3x / 2x), deren ATR-geschätzte Liquidationswahrscheinlichkeit binnen der Haltedauer **unter der Grenze** liegt — sonst **kein** Handel (K6, 2.681, H0 2.689) |
| Liquidation | Bitpanda-Formel `Liq = E (1 − 1/L + t·0,0018) / (1 − 0,09)` am **Markpreis-Tief** (2.679) |
| **Kosten** | `docs/hebel_positionsformel.md`: **0,3 %** je Handel, **0,18 % je Tag** Finanzierung (anteilig je Stunde), **+1 %** Zwangsliquidationsgebühr — auf den **Positionswert** gerechnet (vorsichtig) |
| Nutzerwirklichkeit | an den echten Hebelpositionen Ø **1,1 Tage** Haltedauer (dieselbe Doku) — passt zum *Tageshandel* |

---

## 3. Der Aufbau

| | |
|---|---|
| **Einstieg** | Markpreis-Schluss der Einstiegsstunde |
| **Ausstieg** (Messgeometrie, eine **Achse**, nicht gesetzt) | **Ziel** erreicht (Markpreis-Hoch ≥ Einstieg × (1 + Z)) · **Liquidation** (Markpreis-Tief ≤ Liq) · sonst **Zeitablauf** nach H Stunden zum Schluss. Liegen Ziel und Liquidation in **derselben** Stunde, zählt die **Liquidation** (vorsichtig) |
| **Achsen** | Haltedauer **H = 6 / 12 / 24 / 72 h** · Ziel **Z = +3 % / +5 % / ohne** · Grenze **g = 0,5 / 1 / 2 / 5 %** — 48 Zellen |
| **Kein Stop** | ein Stop gehört zur **Positionsführung** (Phase 5) und würde das Risiko verändern, das der Hebel schon trägt (K6a); hier nur Ziel, Liquidation, Zeit |
| **Konto** (Messgröße, nicht Betrieb) | Start 1,0; jeder Handel setzt **f = 1 %** des aktuellen Kontos als Einsatz; gleichzeitige Handel erlaubt; Auskunft mit f = 0,5 % und 2 % (bleibt die Wahl gleich?) |
| **Maße** | **Kontowachstum** (log, Endwert) · größter Rückgang · längste Verlustserie · schlechtester Monat · Anteil Liquidationen · je Jahr und Monat |
| **Vergleichsarm Spot** | dieselben Einstiege und dieselbe Geometrie **ohne** Hebel (1x, ohne Finanzierung) |
| **Nullwelt** | dieselben Handel mit **zeitverschobenen** Einstiegen je Asset (≥ 60 Tage, 40 Ziehungen) — trennt das **Signal** vom Markt und von der Geometrie (2026 war stark, der Prüfzeit-Versatz ist positiv) |
| **Black Swan** | mit / ohne 10./11.10.2025 |

## 4. Wahl und Bestätigung — wie Schritt 1

| | |
|---|---|
| **Wahl** (nur 2024, `bestand`) | die Zelle (H, Z, g) mit dem **größten Kontowachstum nach Kosten**; Gleichstand (weniger als 1 % Endwert Unterschied) → die **kleinere Grenze**, dann die **kürzere** Haltedauer |
| **R-R11** | die Einstiege sind bitgleich die aus 2.689 (Anzahl je Menge) |
| **Bestätigung** (2025-01 bis 2026-08, **einmal**, dieselbe Zelle in allen vier Mengen) | **S1** Konto wächst in **2025 und 2026** · **S2** über dem P90 der Nullwelt · **S3** ≥ 3 von 4 Mengen · **S4** Hebelkonto **über** dem Spotkonto derselben Geometrie · **S5** mit/ohne Black Swan ausgewiesen |
| **Pflichtauskunft Regime** | Juli–Dezember 2025: Kontoverlauf, Rückgang, Liquidationen — *was passiert in sechs Monaten Gegenwind?* |

⚠️ **Mehrfachtesten:** 48 Zellen auf 2024 — die Wahl überschätzt 2024 sicher; genau darum die **einmalige** Bestätigung.
⚠️ **Fällt S4, nicht S1–S3:** der Kern trägt, der **Hebel** nicht → Lösung vorlegen (Spot-Kern, andere Geometrie).

---

## 5. Prüfung und Gegenprüfung

| Falle | Gegenmittel |
|---|---|
| Ertrag fließt in die Bewertung | ⛔ ausgeschlossen: das ist Ebene B; Hebelmodell und Einstieg bleiben, wie sie sind (Regelwerk *Trennung*) |
| Kosten zu mild | auf den **Positionswert**, dazu 1 % bei Liquidation — eher zu streng |
| Ziel und Liquidation in einer Stunde | die Liquidation zählt |
| Hebel ohne Grenze gleich 5x überall | die Grenze wird **mitgemessen**; bei g = 5 % ist 5x fast immer erlaubt (2.681) — das Konto zeigt, ob das trägt |
| gleichzeitige Handel (Ballung an Markttagen) | im Konto enthalten; das Risiko der Ballung zeigt der **größte Rückgang** |
| Regime | Nullwelt mit verschobenen Einstiegen; Juli–Dezember 2025 ausdrücklich |
| Vorgriff | ATR und Modell nur aus der Vergangenheit (rollierend wie 2.681); Ausstieg nur aus den Stunden **nach** dem Einstieg |
| Messgeometrie ist nicht Betrieb | Ziel/Haltedauer sind Messgrößen; die Positionsführung (Phase 5) kann besser **oder** schlechter sein |
| Kleine Läufe täuschen | volle Daten; zuerst `bestand` (Wahl), dann die Bestätigung in vier Mengen |

---

## 6. Zur Abstimmung (Z1–Z6)

| # | Punkt | Empfehlung |
|---|---|---|
| **Z1** | Geometrie als Achse: H 6/12/24/72 h × Ziel +3 % / +5 % / ohne, **kein** Stop | ja |
| **Z2** | Grenze **gemessen** (0,5 / 1 / 2 / 5 %), Regel: größtes Kontowachstum, Gleichstand → vorsichtiger | ja |
| **Z3** | Kosten wie Abschnitt 2 (auf den Positionswert, +1 % bei Liquidation); Spot-Arm: 0,3 % je Handel, keine Finanzierung (Annahme — die Spot-Gebühr ist nicht dokumentiert) | ja |
| **Z4** | Konto mit f = 1 % je Handel als Messgröße; 0,5 % / 2 % als Auskunft | ja |
| **Z5** | Wahl auf 2024, **einmalige** Bestätigung S1–S5, Pflichtauskunft Regime | ja |
| **Z6** | dein **Veto** (optional): ein größter Rückgang, den du **nicht** akzeptierst — sonst entscheidet die Regel | *nur wenn du willst* |

---

## 7. Umfang

Werkzeug `messe_kern_simulation.py` (liest die Einstiege, den Markpreis mit Hoch/Tief und das ATR-Modell wie K6) bauen und
vorab committen · Funktionstest · Wahl 2024 (`bestand`) · Stopp · Bestätigung in vier Mengen · Stopp · Bewertung.

---

## 8. ✔ FREIGEGEBEN (29.09.2026) — Z1 bis Z5 nach Expertenurteil, kein Veto (Z6)

**Nutzer:** *„sonst kann ich zu Z1 bis Z5 so nichts sagen — wenn du der Meinung bist, so ist es ok, starten wir."* Frage
dazu: *„das mit Spot habe ich nicht verstanden — ist das nur wegen der Dauer, die ein Trade dauert, also die
Hebelgebühr?"*

➤ **Zum Spot-Arm:** er ist ein **Maßstab**, kein Vorschlag für Spot-Handel. Er beantwortet *„lohnt der Hebel überhaupt?"*:
der Hebel vervielfacht Gewinn **und** Verlust, dazu kommen Finanzierung (0,18 %/Tag auf den Positionswert) und die
Liquidationen. Bei einem **kleinen** Vorteil kann das Hebelkonto darum **schlechter** laufen als dieselben Einstiege ohne
Hebel — dann zerstört der Hebel den Vorteil. Die Gebühr ist ein Teil davon, die Liquidation der größere.

| umgesetzt VOR dem Lauf | |
|---|---|
| Werkzeug | `messe_k6_hebelstufe.py --kurs mark --einstiege <csv> --simulation` (Wahl) bzw. `--simulation H,Z,g` (Bestätigung) — statt eines eigenen Skripts, weil dort Markpreis, ATR-Modell und die Einstiege schon stehen (R-R11 2.681 und 2.689 im selben Lauf) |
| Konto | Kontowachstum als Summe von log(1 + f·r) über die Handel, geordnet nach der Ausstiegszeit (Rückgang, Serie, Monate daraus) — mit f = 1 % ist der Unterschied zur exakten Mitbuchung gleichzeitiger Handel vernachlässigbar |
| Rendite je Handel (auf den Einsatz) | Ziel: L·Z · Zeit: L·(Schluss/Einstieg − 1) · Liquidation: −1 − L·1 % · jeweils minus L·(0,3 % + 0,18 %/Tag·Dauer); Spot: ohne Liquidation und Finanzierung |
| Nullwelt | die Einstiege 2025–26 je Asset um ≥ 1.440 gültige Stunden zeitverschoben (innerhalb 2025–26), Hebelstufe aus dem ATR-Modell am neuen Zeitpunkt, 40 Ziehungen |
| Ablauf | Funktionstest · Wahl 2024 (`bestand`) · Stopp · Bestätigung vier Mengen · Stopp · Bewertung |

---

## 9. ERGEBNIS WAHL 2024 (bestand) — Stopp

Beleg `Kern_Sim_29_09/wahl__bestand.txt`. ✔ R-R11: 2.681 bitgleich, 12.163 Einstiege wie 2.689 (davon 2.095 in 2024).

**Kontowachstum 2024** (log, f = 1 % Einsatz je Handel, nach Kosten) — Auszug, ohne Ziel:

| Haltedauer | Grenze 0,5 % | 1 % | 2 % | 5 % | Spot 1x |
|---|---|---|---|---|---|
| 6 h | −0,111 | −0,123 | −0,102 | −0,108 | −0,005 |
| 12 h | +0,077 | +0,067 | +0,131 | +0,079 | +0,058 |
| **24 h** | +0,147 | +0,121 | **+0,215** | +0,222 | +0,135 |
| 72 h | +0,091 | +0,166 | +0,175 | +0,123 | +0,218 |

- **Ziel +3 % / +5 %** ist in **jeder** Haltedauer schlechter als **ohne Ziel** — das Ziel kappt die Gewinner.
- **6 h** ist überall negativ — zu kurz: die Kosten fressen den Vorteil (der Kern ist ein Tageshandel, 2.689).
- **72 h**: Spot (+0,218) schlägt jeden Hebel — Finanzierung und Rückgang (bis 0,71) wiegen schwerer.

➤ **Nach der Regel gewählt: H = 24 h, ohne Ziel, Grenze 2 %** (log +0,215 = Konto ×1,24; die Grenze 5 % mit +0,222 liegt
0,7 % Endwert darüber — **Gleichstand**, darum die vorsichtigere). Hebel im Mittel 3,4, Liquidationen 0,43 % der Handel,
größter Rückgang 0,209 (log), längste Verlustserie 29, schlechtester Monat −0,129.

⚠️ **Gegenprüfung:**
1. Mit f = 0,5 % und 2 % gewinnt jeweils der **Gleichstandspartner** (Grenze 5 %) — das ist dieselbe Zelle bis auf die
   Grenze, keine Instabilität der Wahl.
2. Die Wahl aus 48 Zellen **überschätzt** 2024 sicher; auch Spot ist 2024 positiv — ein Teil ist **Markt**. Beides prüft
   erst die Bestätigung (Nullwelt, Spot-Vergleich).
3. Der Rückgang von 0,21 (log) bei nur 1 % Einsatz je Handel ist **groß** — die Ballung vieler Handel an Markttagen.


---

## 10. ERGEBNIS BESTÄTIGUNG 2025-01 bis 2026-08 — Befund 2.690 (Stopp)

| | bestand | unverzerrt:1 | unverzerrt:2 | unverzerrt:3 |
|---|---|---|---|---|
| **Hebelkonto** (log / Faktor) | −0,484 / ×0,62 | −1,335 / ×0,26 | −1,087 / ×0,34 | −1,262 / ×0,28 |
| S1 2025 / 2026 | −0,195 / −0,289 ⛔ | −0,715 / −0,620 ⛔ | −0,525 / −0,562 ⛔ | −0,611 / −0,651 ⛔ |
| S2 Nullwelt P90 | −2,310 ✔ | −2,725 ✔ | −2,403 ✔ | −2,443 ✔ |
| S4 **Spot** | +0,029 ⛔ | −0,176 ⛔ | −0,127 ⛔ | −0,189 ⛔ |
| S5 ohne 10./11.10. | −0,382 | −0,954 | −0,756 | −0,974 |
| Juli–Dezember 2025 | ×0,69 | ×0,43 | ×0,50 | ×0,44 |
| Liquidationen | 0,18 % | 0,50 % | 0,44 % | 0,47 % |

➤ **Schritt 3 NICHT bestanden** — der Hebel verliert, Spot liegt um null. **Das Signal selbst ist echt** (S2: zufällige
Einstiege verlieren weit mehr).

**Ursache — gemessen, nicht vermutet (E-25):**

| Prüfung | Ergebnis |
|---|---|
| **Kostenbasis** | am echten Bitpanda-Buch (K7-Gebührensignatur, 2.679): 0,30 % + 0,18 %/Tag auf den **Positionswert** — die Annahme stimmt, eher zu mild (eine Eröffnungsgebühr wäre zusätzlich) |
| **Rohvorteil je Handel** (auf den Positionswert, aus Spot und Hebel unabhängig gleich) | 2025–26: **+0,33 / +0,14 / +0,17 / +0,12 %** · 2024: **+0,95 %** |
| **Kosten je Tageshandel** | **0,48 %** (0,30 % Gebühr + 0,18 % Finanzierung) |
| **Kostenblock im Hebelkonto** | 1,71 bis 1,90 (log) — erklärt das Ergebnis allein |

➤ Der Hebel **vervielfacht einen Nettoverlust**: der Vorteil je Handel ist kleiner als das, was ein Handel kostet — 2024
war er dreimal so groß (Regime).

**Lösungsvorschläge** (je neue Vorabfestlegung, zur Abstimmung):

| # | Lösung | beantwortet |
|---|---|---|
| **L1** | **Kostenachse**: dieselbe Simulation mit den Kosten einer Terminbörse (Auskunft) | liegt es an der **Plattform** oder am **Kern**? |
| **L2** | **weniger, stärkere Signale** — Signalstärke als Achse (K6 S Stufe 1: oben etwa doppelter Vorteil) | hebt eine strengere Auswahl den Vorteil **über 0,48 %**? |
| **L3** | **länger halten ohne Hebel** — die feste Gebühr auf größere Bewegungen (2024: 72 h Spot vorn) | ein **Spot-Kern** statt Hebel-Kern? |
| **L4** | die **Summe der Beiträge** — ein zweiter tragender Beitrag | größerer Vorteil je Handel |
