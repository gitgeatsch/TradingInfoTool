# Voranalyse: Das Fakten- und Führungssystem weiterentwickeln (26.10.2026)

Nutzer 26.10.: *„a - prüfen gegenprüfen und doku“*, also die Suche nach einem Einstiegsvorsprung abschließen (E-155) und weiterentwickeln, was trägt.

**Grundlage:**
- die offenen Punkte der O-Liste (`Plan_Hebel_fuenf_Phasen_27_09.md`);
- der Prüfbericht A.4 (`Bilanz_Gesamt_25_10.md`);
- die Entscheidungen E-36 bis E-155;
- ein Blick in den Code, welche Lücken wirklich bestehen.

## 1. Was trägt und im Betrieb läuft

| Teil | gemessen | gebaut |
|---|---|---|
| B1 Mitnahme ×3 je L-Bestand | Spot §32–§34 | ✔ P14 |
| B3 Upbit-Listing | Spot §38 | ✔ P16 |
| B4 Abbau-Reihenfolge (unteres Fünftel) | Spot §48; Fortbestand 12 M, zeitrichtig bestätigt (E-154) | ✔ P18 |
| C1 Season-Ampel | Spot §36/§59, zwei Zyklen | ✔ P19 |
| Lagebild Gesamtmarkt, Makro | E-137, O54 | ✔ (NB-Kontrolle offen) |
| H15 Hebelführung, Haltedauer, Erinnerungen | E-88, §23.68 | ✔ |
| REGEL0 | Plus **nicht robust** (E-136/E-139), im Betrieb unverändert (E-140) | ✔ mit Messstand im Betrieb (O21) |
| K-4 | — | ✔ E-152 |

## 2. Offene Punkte mit Nutzen — im Code nachgesehen

| # | Punkt | Befund im Code / in der Doku | Nutzen | Aufwand |
|---|---|---|---|---|
| **F-1** | **Grundgesamtheit REGEL0 am NB prüfen** (`st0`, der Reihenbeginn je Symbol) | Prüfbericht A.4: *„ob der Betrieb am NB dasselbe `st0` hat wie die Desktop-Referenz, ist nicht geprüft. Nach E-139 ist das die Größe, an der alles hängt.“* Die Diagnose führt `st0` **nicht** (`extract_notebook_diagnose.py`, kein Feld) | ⭐⭐⭐ Am Reihenbeginn hängt, ob die REGEL0 am NB **dieselben** Signale erzeugt wie gemessen (Leitsatz E-35) | klein: Diagnose-Abschnitt nur lesend, Abgleich am Desktop gegen die Kopie |
| **F-2** | **Vorbehalt in der REGEL0-Mail** | `regel0_mail.py` hat keinen Satz zu E-136/E-140. Du bekommst Signale ohne den Hinweis, dass ihr Plus nicht robust ist | ⭐⭐ Regel 4 und *Fakt statt Begründung*: Die Mail soll sagen, was belegt ist und was nicht | klein, eine Zeile Fakt; Prüfstand Mail |
| **F-3** | **Doku-Lücken aus dem Prüfbericht** | `hebel_neubau.py` NEUESTER_STAND, `Regelwerk_Hebel_Bewertung_27_09.md`, `UEBERGABE_Hebelneubau_27_09.md`, `bestand.py`/Register auf dem Stand 02.–16.10.; §23.x für E-137 fehlt; Altwerkzeuge mit Rang-Vorgriff ohne Kennzeichen | ⭐⭐ Die Einstiegsdokumente stimmen sonst nicht mit E-136 bis E-155 | mittel, nur Doku und Register |
| F-4 | **Alte Rollen-Kette stilllegen statt nur anhalten** | Seit 05.10. angehalten; bei unlesbarer `regel0_betrieb.yaml` läuft sie wieder an (`regel0_groesse.py:137`). Sie ist gemessen falsch (O23/E-55) | ⭐ Risiko: ungewollter Neustart mit LLM-Kosten und Nachkauf-Mails | ⚠️ groß, ein Umbau: vorher prüfen, was fehlt; Rücksprache |
| F-5 | Bestand = frei + gestakt im Teilexport (O37) | offen laut Plan | Diagnosegenauigkeit | klein |
| F-6 | REGEL0-Zusatzuniversum per Regel statt Liste (O38) | offen | sauberere Grundgesamtheit | mittel, mit Messung der Wirkung (Grundgesamtheit!) |
| F-7 | GUI „Meine Assets“ / Spot-Bereich (O40/O41) | offen | Bedienung | mittel |

**Nicht aufgenommen** (mit Grund):
- ein Nachlauf-Stop für Rolle L: bewusst nicht (E-86); er hängt am Regime (Spot §40);
- neue Einstiegsmessungen: E-155;
- die Kern-Regel: E-148.

## 3. Vorschlag: Reihenfolge

| Paket | Inhalt | Warum zuerst |
|---|---|---|
| **W-1** | **F-1 + F-2** zusammen: Diagnose-Abschnitt `regel0_reihenbeginn` (je Symbol `st0`, Quelle, Stunden bis Reife; nur lesend) und die Fakt-Zeile *„REGEL0: Plus in der Messung nicht robust gegen die Datenlänge (E-136) – Signal ist Fakt, keine Gewinnerwartung“* in der REGEL0-Mail | beides klein, beides betrifft den **Hebel im Betrieb**; geht in **ein** NB-Bündel nach dem morgigen Export |
| W-2 | F-3 Doku-Lücken | danach; keine Betriebsänderung |
| W-3 | F-4 Stilllegung der alten Kette | eigene Voranalyse *was fehlt*, Rücksprache |
| später | F-5 bis F-7 | nach Bedarf |

**Prüfung W-1 (vorab):**
- Der Diagnose-Abschnitt wird an einer Wegwerf-Kopie getestet (kein Schreibzugriff auf die Produktion).
- Der Abgleich `st0` NB gegen Desktop läuft auf der Kopie im Austauschordner.
- Die Mailzeile geht über den Prüfstand mit echter `config.yaml`.
- Suite-Paket mit Mutationsprobe; NB-Kontrolle K-R0-ST0.
