# REGISTER — DIE KANDIDATEN

*Erzeugt aus `bestand.py`. **Nicht von Hand aendern** — die Aenderung gehoert in das Modul, sonst laeuft das Blatt weg.*

⚠️ **Wofuer dieses Blatt existiert:** am 06.09.2026 wurden drei Kandidaten auf der FALSCHEN Basis gemessen, weil ihre Registrierungsbasen ueber `wahrscheinlichkeit.BEITRAEGE`, Memory-Dateien, Befundkarte und Methodik verstreut lagen. Und `schnitt` wurde mit `schnitt50` verwechselt. Beides waere mit diesem Blatt nicht passiert (R-R11).

## Uebersicht

| | Kandidat | Form | Zustand | Registrierungsbasis |
|---|---|---|---|---|
| ✔ | **`funding`** | regler | traegt | H20 · 2.369 Kalendertage · 290 Symbole · 6,3 Jahre |
| ✔ | **`turnover`** | regler | traegt | H20 · 2.636 Kalendertage |
| ✔ | **`oi_aenderung`** | schalter | traegt | H20 · 1.702 Kalendertage · 117 Symbole · 126.491 Anker |
| ○ | **`vola`** | regler | offen | H5/H20 · volle Historie · Massstab RAND > +2 R |
| ○ | **`schnitt50`** | regler | offen | 31.08. bei H2 und H20 gemessen - H5 NIE |
| ↩ | **`schnitt`** | regler | zurueck | H1..H20 Horizontlauf 31.08. |
| ✖ | **`amihud`** | regler | traegt nicht | H20 volle Historie, beide Richtungen geprueft |
| ↩ | **`H (Vorfilter)`** | schalter | zurueck | gepoolt ueber die ganze Historie |

---

## ✔ `funding`

**Hypothese:** Querschnittsrang der Finanzierungsrate: wer heute am wenigsten zahlt. Viel Funding heisst ueberhitzt.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H20 · 2.369 Kalendertage · 290 Symbole · 6,3 Jahre |
| **Wert** | +0,0246 R (Regelwirkung) |
| **Live** | agent/wahrscheinlichkeit.BEITRAEGE · merkmal funding_fuenftel · Stufen (+0.82, +1.30, +0.12, -0.54, -1.70) |
| **Zustand** | **traegt** |

**Die Messkette:**

- **30.08.** — 2e registriert, als REGEL gemessen (R-R8)
- **06.09.** — F-212 reproduziert +0,0274 (registriert +0,0246)
- **06.09.** — Schritt 3: H5 ab 2024 +0,0041 - traegt nicht
- **06.09.** — Schritt 4a A: H20 voll +0,02741 REPRODUZIERT
- **06.09.** — Schritt 4a B: H5 voll  +0,00841 TRAEGT
- **06.09.** — G2: faellt in BEIDEN 959-Tage-Fenstern -> Datenmenge, nicht Epoche

⚠️ Fremdquelle, deshalb Luecken in der Abdeckung.

---

## ✔ `turnover`

**Hypothese:** Handelsvolumen je Umlaufmenge - viel Aufmerksamkeit heisst eher ueberbewertet.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H20 · 2.636 Kalendertage |
| **Wert** | +0,0616 R [+0,0203 .. +0,1111] |
| **Live** | agent/wahrscheinlichkeit.BEITRAEGE · merkmal turnover_fuenftel · Stufen (+3.15, +0.83, +0.22, -1.79, -2.40) |
| **Zustand** | **traegt** |

**Die Messkette:**

- **30.08.** — 2e registriert
- **02.09.** — F-171 Audit: Band sehr breit, groesste Stufen auf der unsichersten Zahl
- **02.09.** — F-170: Rang ist zu 52 % ASSET-Eigenschaft
- **06.09.** — Schritt 4a A: H20 voll +0,06352 REPRODUZIERT
- **06.09.** — Schritt 4a B: H5 voll  +0,02059 TRAEGT
- **06.09.** — G2: juengere Epoche STAERKER (+0,0172 gegen +0,0137)

⚠️ Nur 65 Symbole Abdeckung - das Nullband ist dreimal so breit wie bei den anderen. Urteil wandert mit der Saat.

---

## ✔ `oi_aenderung`

**Hypothese:** Aufbau von Open Interest zum Vortag: wo sich Hebel auftuermt, kippt die Bewegung eher.

| | |
|---|---|
| **Form** | schalter |
| **Registrierungsbasis** | H20 · 1.702 Kalendertage · 117 Symbole · 126.491 Anker |
| **Wert** | +0,0145 R [+0,0097 .. +0,0193] |
| **Live** | agent/rollen_gate.py Stufe terminmarkt - sperrt das OBERSTE Fuenftel · nur einstieg · nicht bei Bestand |
| **Zustand** | **traegt** |

**Die Messkette:**

- **02.09.** — H-4c: traegt, aber SCHALTER statt Regler - die Monotonie fiel
- **02.09.** — N-14: als 12. Trichterstufe gebaut
- **04.09.** — F-207: Kombination mit funding_extrem verbessert die Sperre NICHT - Status quo bleibt
- **06.09.** — Schritt 3: H5 ab 2024 - traegt nicht
- **06.09.** — Schritt 4a A: H20 voll +0,01418 REPRODUZIERT
- **06.09.** — Schritt 4a B: H5 voll +0,00663 - traegt nicht

⚠️ GELTUNGSBEREICH H20. Der Betriebshorizont sind 3-5 Tage. Ob H20 der richtige Horizont fuer diese Sperre ist, ist eine ENTWURFSfrage (D3) - keine Messfrage.

---

## ○ `vola`

**Hypothese:** Schwankungsbreite als Querschnittsrang - hohe Volatilitaet als Ausschlusskriterium.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H5/H20 · volle Historie · Massstab RAND > +2 R |
| **Wert** | +0,0100 (H20) · +0,0033 (H5 voll) · +0,0038 (H5 2024) |
| **Live** | - noch nicht registriert |
| **Zustand** | **offen** |

**Die Messkette:**

- **06.09.** — Schritt 3: traegt am RAND (+0,0038), nicht am Mittel - der von 2.112 vorhergesagte Fall
- **06.09.** — Gegenpruefung: ueber drei Saaten stabil
- **06.09.** — Schritt 4a: TRAEGT auf ALLEN DREI Laeufen

⚠️ VOR der Registrierung: Redundanz gegen funding und turnover pruefen (N1). F-206 fand turnover+vola praktisch identisch mit turnover allein.

---

## ○ `schnitt50`

**Hypothese:** Abstand zum eigenen 50-Tage-Schnitt als Trendlage.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | 31.08. bei H2 und H20 gemessen - H5 NIE |
| **Wert** | H2 +0,0029 [-0,0005 .. +0,0065] · H20 kein Urteil |
| **Live** | - nicht registriert |
| **Zustand** | **offen** |

**Die Messkette:**

- **31.08.** — H2 traegt nicht (Messung maechtig), H20 kein Urteil - die Positivkontrolle versagte dort
- **06.09.** — Schritt 4a: H5 voll +0,0101 TRAEGT, H5 2024 +0,0095 TRAEGT

⚠️ NICHT VERWECHSELN mit `schnitt` (200-Tage), der am 31.08. zurueckgenommen wurde. H5 ist neu und gegenzupruefen (N2) - der Horizontverlauf H2 klein / H5 gross / H20 klein ist erklaerungsbeduerftig.

---

## ↩ `schnitt`

**Hypothese:** Abstand zum eigenen 200-Tage-Schnitt.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H1..H20 Horizontlauf 31.08. |
| **Wert** | H5 -0,0069 · H10 -0,0118 · H20 -0,0221 |
| **Live** | - zurueckgenommen |
| **Zustand** | **zurueck** |

**Die Messkette:**

- **31.08.** — mittags als dritter tragender Beitrag registriert
- **31.08.** — abends im Horizontlauf gefallen - bei keinem Horizont trennbar, bei langen negativ

⚠️ Die Marken tragen weiterhin den STOP - nur als BEWERTUNGSbeitrag tragen sie nicht.

---

## ✖ `amihud`

**Hypothese:** Illiquiditaet |Rendite|/Umsatz - die Literatur behauptet eine Praemie fuer illiquide Werte.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H20 volle Historie, beide Richtungen geprueft |
| **Wert** | -0,0016 R |
| **Live** | - nicht registriert |
| **Zustand** | **traegt nicht** |

**Die Messkette:**

- **30.08.** — gemessen, beide Richtungen null
- **06.09.** — Schritt 4a: auf keinem Lauf, keinem Massstab

---

## ↩ `H (Vorfilter)`

**Hypothese:** Weg frei UND Stop gedeckt.

| | |
|---|---|
| **Form** | schalter |
| **Registrierungsbasis** | gepoolt ueber die ganze Historie |
| **Wert** | gepoolt +3,57 Punkte · je Kalendertag -1,02 nicht trennbar |
| **Live** | agent/wahrscheinlichkeit.BEITRAEGE mit punkte=0.0 - stillgelegt, nicht entfernt |
| **Zustand** | **zurueck** |

**Die Messkette:**

- **31.08.** — R1: faellt als Beitrag - gepoolt gemessen, unter der Tagesklammer nicht trennbar

⚠️ Die Marken tragen weiterhin den Stop.

