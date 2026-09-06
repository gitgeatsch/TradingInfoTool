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
| ○ | **`vola ODER turnover`** | schalter | offen | H5 · volle Historie · Rand > +2 R · Menge frei · 167 Bloecke |
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
- **06.09.** — N13: verschiebt die FRONTLOADING-Quote um +4,0 bis +4,5 Punkte - bei JEDER Breite (20/10/5 %), Band durchgehend ohne Null. Der Tempo-Anzeiger

⚠️⚠️⚠️ REPRODUKTION FEHLGESCHLAGEN 06.09. (N-56): auf der EIGENEN Basis (H20, bewegung_r, oberstes Fuenftel) kommt -0,06293 [-0,13183 .. -0,00785] heraus gegen registriert +0,0616 - gleiche Groessenordnung, UMGEKEHRTES Vorzeichen. Die Fuenftel haben keine Ordnung: +0,009 · +0,053 · -0,265 · -0,041 · +0,229; das BESTE ist Fuenftel 4, das die Tabelle mit -2,40 am haertesten bestraft. Bestaetigt 2.133 (0 von 2 Nachbarn getrennt, beide Haelften). ⚠️ DIE GROESSE BLEIBT - sie traegt Richtung (GS +0,00512, der staerkste der drei). NICHT belegt ist die TABELLE, und es sind die groessten Stufen im System. Nach 2.133 ist die belegte Form eine ZWEITEILUNG. --- ✔✔ REHABILITIERT 06.09. (N-53): `turnover` traegt RICHTUNG +0,00512 [+0,00212 .. +0,00831], 0/5 - richtungsrein der STAERKSTE der drei Groessen, zweieinhalbmal `funding`. Auf der registrierten Barrieren-Quote traegt es NICHT (+0,00168, Band mit Null), weil sein Aufloesungskanal (-0,00218) gegen die Richtung laeuft und den Effekt verdeckt. Der Vorschlag vom Vormittag (2.133: stilllegen) ist damit ueberholt - er stand auf dem gemischten Massstab. ⚠️ R-R9 OFFEN: auf welcher Zielgroesse die Stufen kalibriert werden. `q` ist ,Ziel vor Stop' (= G0); dort ist turnover schwach, weil die GEOMETRIE es daempft - das ist eine Aussage ueber die Geometrie, nicht ueber den Beitrag. --- FRUEHER: Nur 65 Symbole Abdeckung - das Nullband ist dreimal so breit wie bei den anderen, das Urteil wandert mit der Saat. ⚠️ OFFEN (N6): turnover traegt AUCH am Randmassstab (+0,01389 bei H20, 2.119) - registriert ist er nur am Mittel. Und er erklaert 18 % von `vola` (N1, p=0,025).

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
- **06.09.** — N1-V2: Richtung geprueft - Gegenrichtung -0,00345, spiegelbildlich. Echter Richtungseffekt
- **06.09.** — N1-C: in funding +0,00309 TRAEGT · in turnover +0,00281 nicht trennbar
- **06.09.** — N1-D: turnover in vola +0,02217 TRAEGT - wird sogar staerker
- **06.09.** — N1-Rangtest, 39 Mischungen: funding erklaert 3 % (p=0,325), turnover erklaert 18 % (Rang 1 von 40, p=0,025)
- **06.09.** — N5: die Kombination `vola ODER turnover` traegt +0,00777 - mengenkontrolliert +26 % bis +34 % ueber der besten Einzelgroesse, beide Haelften, drei Saaten
- **06.09.** — N12: allein bei 10/20/30/40 % Sperrmenge - ALLE tragen. Bei 40 % +0,00647 = 83 % der Kombination, aber bei 516 statt 65 Symbolen Abdeckung
- **06.09.** — N13: beim Frontloading +1,5 Punkte (20 %) - traegt, aber deutlich schwaecher als turnover (+4,0)
- **06.09.** — N23-E1: einzige belegte DREITEILUNG, beide Haelften, 2/2 Nachbarn getrennt
- **06.09.** — ✖✖✖ N-52: KEINE RICHTUNG. Richtungsrein (GS) -0,00041 [-0,00287 .. +0,00194], 2/5 - und die Drittel haben KEINE Ordnung mehr
- **06.09.** — N-52: der Befund geht restlos in Groessenkanaele auf - Aufloesungsquote +0,03088, Rest G0R +0,00760 gegen Kunstwelt-Artefakt +0,00770 / +0,00731

⚠️⚠️⚠️ STAND NACH N-52 (06.09.): `vola` GEHOERT NICHT IN `BEITRAEGE`. Richtungsrein gemessen traegt es nichts (GS -0,00041, 2/5, keine Ordnung der Drittel). Der starke Befund war unsere eigene Geometrie: ruhige Assets loesen ihre Barrieren oefter auf (+0,03088), und eine Aufloesung ist bei CRV 2 zu einem Drittel ein Treffer. Der Rest ist zahlengleich mit dem Artefakt aus zwei richtungsfreien Kunstwelten. ✔✔ ABER KEIN NULLBEFUND: +3,1 Punkte auf die AUFLOESUNGSQUOTE sind der groesste saubere Effekt des Tages. `vola` gehoert in die GEOMETRIE- und HORIZONTWAHL - und ueber `hebel = verlustanteil / stop_rel` faellt daraus der Hebel. Das ist die als fehlend gefuehrte Horizont-Achse. ⚠️ OFFEN (R-R11): N1-V2 fand am RANDMASS einen spiegelbildlichen Richtungseffekt (-0,00345). Das ist durch N-52 NICHT widerlegt - andere Zielgroesse -, steht aber unter Verdacht, weil das Randmass sich den Schiefe-Kanal mit `bewegung_r` teilt. Richtungsreine Nachmessung am Rand steht aus. --- FRUEHERER STAND (N12): `vola` ist die einzige der beiden Groessen, die im Betrieb UEBERALL wirkt (516 von 516 Symbolen). Allein bei 40 % Sperrmenge erreicht sie 83 % der Kombinationswirkung - der Kompromiss kostet 17 % Wirkung und bringt die achtfache Abdeckung. ⚠️⚠️ N1 ENTSCHIEDEN, ABER NICHT ZUR REGISTRIERUNG. `vola` ist KEIN Mitlaeufer - 82 % bleiben, wenn turnover festgehalten wird, und funding erklaert nachweislich nichts. Aber die 18 % Ueberlappung mit turnover sind belegt, und der Rest ist im Schichtentest NICHT TRENNBAR. Naechster Schritt ist nicht mehr Messung von vola allein, sondern die KOMBINATION vola UND turnover am Rand (N5).

---

## ○ `vola ODER turnover`

**Hypothese:** Zwei weitgehend unabhaengige Ausschlussgruende: hohe Volatilitaet ODER hoher Umschlag. Wer in EINER der beiden Groessen im obersten Fuenftel liegt, wird gesperrt.

| | |
|---|---|
| **Form** | schalter |
| **Registrierungsbasis** | H5 · volle Historie · Rand > +2 R · Menge frei · 167 Bloecke |
| **Wert** | +0,00777 [+0,00480 .. +0,01153] · Reinheit +0,02143 · 36,1 % gesperrt |
| **Live** | - NICHT gebaut (siehe Warnung) |
| **Zustand** | **offen** |

**Die Messkette:**

- **06.09.** — N5: fuenf Formen geprueft. UND traegt nicht (6,8 % gesperrt, Reinheit sogar NIEDRIGER als einzeln), SUMME traegt (+0,00392), ODER traegt am staerksten
- **06.09.** — mengenkontrolliert: bei 20 % +26 %, bei 36 % +34 % ueber der besten Einzelgroesse. 43 % des rohen Vorsprungs waren MENGE
- **06.09.** — beide Historienhaelften tragen einzeln (+0,01045 / +0,00554), drei Saaten stabil
- **06.09.** — zwei Konstruktionsfehler von den eigenen Kontrollen gefangen: asymmetrische Rangbildung, fehlende Symmetrieprobe im Vorabtest

⚠️⚠️ BELEGT, ABER IM BETRIEB WEITGEHEND NICHT ABRUFBAR (N8/2.122): turnover liegt bei 7 von 57 beobachteten Werten vor. Der gemessene Kombinationsvorteil braucht beide Groessen. Die praktisch wichtigere Frage ist N12 - traegt `vola` ALLEIN als Sperre genug? ⚠️ Frueherer Verdacht auf Doppelzaehlung ist ausgeraeumt: wo turnover vorliegt, verlangt das Tor ohnehin Fuenftel 0, eine Sperre auf Fuenftel 4 waere wirkungslos. (N9) 36 % Sperrmenge ist eine erhebliche Verschaerfung bei zwoelf bestehenden Trichterstufen. (N10) die Potentialformel meint eine BARRIEREN-Quote, das Randmass eine HORIZONT-Quote. ⚠️ Der Effekt halbiert sich ueber die Zeit (+0,01045 -> +0,00554).

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

