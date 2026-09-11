# REGISTER — DIE KANDIDATEN

*Erzeugt aus `bestand.py`. **Nicht von Hand aendern** — die Aenderung gehoert in das Modul, sonst laeuft das Blatt weg.*

⚠️ **Wofuer dieses Blatt existiert:** am 06.09.2026 wurden drei Kandidaten auf der FALSCHEN Basis gemessen, weil ihre Registrierungsbasen ueber `wahrscheinlichkeit.BEITRAEGE`, Memory-Dateien, Befundkarte und Methodik verstreut lagen. Und `schnitt` wurde mit `schnitt50` verwechselt. Beides waere mit diesem Blatt nicht passiert (R-R11).

⚠️⚠️ **VOR ODER NACH DEM UMBAU?** Die Grenze ist der Messstandard vom 08./09.09.2026. **7 von 18 Blaettern stammen von davor** — ihre Urteile haben die Norm nicht gesehen (anderer Nullpunkt, andere Trennschaerfe, kuerzere Leiter).

⚠️ Das Datum ist ein **Anhalt, kein Urteil**: ein altes Ergebnis kann richtig sein. Es sagt nur, dass es unter anderen Regeln entstanden ist und vor einem Widerruf reproduziert gehoert (R-R11).

## Uebersicht

| | Kandidat | Form | Zustand | Umbauseite | letzte Messung | Registrierungsbasis |
|---|---|---|---|---|---|---|
| ✔ | **`funding`** | regler | traegt | ✔ nach | 11.09. | H20 · 2.369 Kalendertage · 290 Symbole · 6,3 Jahre |
| ✔ | **`turnover`** | regler | traegt | ✔ nach | 11.09. | H20 · 2.636 Kalendertage |
| ✔ | **`oi_aenderung`** | schalter | traegt | ✔ nach | 11.09. | H20 · 1.702 Kalendertage · 117 Symbole · 126.491 Anker |
| ○ | **`vola`** | regler | offen | ✔ nach | 10.09. | H5/H20 · volle Historie · Massstab RAND > +2 R |
| ○ | **`vola ODER turnover`** | schalter | offen | ⚠️ VOR | 06.09. | H5 · volle Historie · Rand > +2 R · Menge frei · 167 Bloecke |
| ○ | **`schnitt50`** | regler | offen | ✔ nach | 11.09. | 31.08. bei H2 und H20 gemessen - H5 NIE |
| ○ | **`akkumulationsmass (= schnitt, H90)`** | regler | offen | ⚠️ VOR | 07.09. | H90 · 505 Krypto-Reihen · 3.292 Tage · zirkulaerer Verschub |
| ○ | **`schnitt`** | regler | offen | ✔ nach | 11.09. | H1..H20 Horizontlauf 31.08. |
| ✖ | **`amihud`** | regler | traegt nicht | ✔ nach | 11.09. | H20 volle Historie, beide Richtungen geprueft |
| ↩ | **`H (Vorfilter)`** | schalter | zurueck | ⚠️ VOR | 31.08. | gepoolt ueber die ganze Historie |
| ✖ | **`oi_je_umsatz`** | regler | traegt nicht | ⚠️ VOR | 06.09. | H20 · 122 Symbole · rund 1.400 bis 1.736 Tage |
| ✖ | **`long_bias`** | regler | traegt nicht | ⚠️ VOR | 06.09. | H20 · 122 Symbole · rund 1.400 bis 1.736 Tage |
| ✖ | **`top_bias`** | regler | traegt nicht | ⚠️ VOR | 06.09. | H20 · 122 Symbole · rund 1.400 bis 1.736 Tage |
| ✖ | **`taker_bias`** | regler | traegt nicht | ⚠️ VOR | 06.09. | H20 · 122 Symbole · rund 1.400 bis 1.736 Tage |
| ✖ | **`rsi`** | regler | traegt nicht | ✔ nach | 09.09. | H20 · volle Historie · 536 Symbole |
| ✖ | **`momentum`** | regler | traegt nicht | ✔ nach | 09.09. | H20 · volle Historie · 536 Symbole |
| ✖ | **`momentum_kurz`** | regler | traegt nicht | ✔ nach | 09.09. | H20 · volle Historie · 536 Symbole |
| ✖ | **`funding_extrem`** | regler | traegt nicht | ✔ nach | 09.09. | H20 · 300 Symbole (Funding-Abdeckung) |

### ⚠️ Diese Blaetter stammen von VOR dem Messstandard

`vola ODER turnover`, `akkumulationsmass (= schnitt, H90)`, `H (Vorfilter)`, `oi_je_umsatz`, `long_bias`, `top_bias`, `taker_bias`

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
| **Umbauseite** | ✔ **nach** dem Messstandard (letzte Messung 11.09.) |

**Die Messkette:**

- **30.08.** — 2e registriert, als REGEL gemessen (R-R8)
- **06.09.** — F-212 reproduziert +0,0274 (registriert +0,0246)
- **06.09.** — Schritt 3: H5 ab 2024 +0,0041 - traegt nicht
- **06.09.** — Schritt 4a A: H20 voll +0,02741 REPRODUZIERT
- **06.09.** — Schritt 4a B: H5 voll  +0,00841 TRAEGT
- **06.09.** — G2: faellt in BEIDEN 959-Tage-Fenstern -> Datenmenge, nicht Epoche
- **10.09.** — ⚠️ V2/N-73: besteht die Huerde NICHT - 2 von 3 Beitragsmengen (10 %% +0,0688 TRAEGT · 20 %% +0,0582 NICHT TRENNBAR · 50 %% +0,0313 TRAEGT)
- **11.09.** — ⚠️ V11: kippt unter dem schaerferen Stabilitaetstest mit ZUFALLSauswahl in 1 von 3 Saaten (+0,0417 [+0,0036 .. +0,0785])

⚠️ Fremdquelle, deshalb Luecken in der Abdeckung.

---

## ✔ `turnover`

**Hypothese:** Handelsvolumen je Umlaufmenge - viel Aufmerksamkeit heisst eher ueberbewertet.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H20 · 2.636 Kalendertage |
| **Wert** | +0,0616 R [+0,0203 .. +0,1111] |
| **Live** | agent/wahrscheinlichkeit.BEITRAEGE · merkmal turnover_fuenftel · Stufen (+3.15, +0.83, +0.22, -1.79, -2.40) · 07.09. entzerrt NACHGERECHNET und bestaetigt (Querschnitt +3,13/+0,76/+0,22/-1,73/-2,38, Methodik 2.165) |
| **Zustand** | **traegt** |
| **Umbauseite** | ✔ **nach** dem Messstandard (letzte Messung 11.09.) |

**Die Messkette:**

- **30.08.** — 2e registriert
- **02.09.** — F-171 Audit: Band sehr breit, groesste Stufen auf der unsichersten Zahl
- **02.09.** — F-170: Rang ist zu 52 % ASSET-Eigenschaft
- **06.09.** — Schritt 4a A: H20 voll +0,06352 REPRODUZIERT
- **06.09.** — Schritt 4a B: H5 voll  +0,02059 TRAEGT
- **06.09.** — G2: juengere Epoche STAERKER (+0,0172 gegen +0,0137)
- **06.09.** — N13: verschiebt die FRONTLOADING-Quote um +4,0 bis +4,5 Punkte - bei JEDER Breite (20/10/5 %), Band durchgehend ohne Null. Der Tempo-Anzeiger
- **10.09.** — ⚠️ V2/N-73: 1 von 1 - aber nur, weil bei seiner Abdeckung (66 von 536) UEBERHAUPT NUR EINE Beitragsmenge zulaessig ist. Eine SCHWAECHERE Aussage als 3-von-3
- **11.09.** — ✔ V11: stabil auf seiner einen Menge (bis 0,10)

⚠️ ✔✔ TABELLE STEHT (Stand 07.09. nach dem Audit 2.143). F-212 vom 04.09. hat auf der SELEKTIERTEN Menge gemessen und reproduziert: +0,0635 R gegen registriert +0,0616. ⚠️ Meine Gegenmessungen N-56 und N-58 liefen auf der FREIEN Menge, wo die Beitraege laut F-212 auf 1,5 % der Anker wirken - dort liegt selbst funding bei -0,0003 R. Beide sind abgeloest, die daraus gefolgte Live-Aenderung (+0,33/-0,48) ist ZURUECKGENOMMEN. ⚠️ WER DIESE TABELLE AENDERN WILL, MUSS AUF DER SELEKTIERTEN MENGE MESSEN. --- UEBERHOLT: ⚠️⚠️⚠️ REPRODUKTION FEHLGESCHLAGEN 06.09. (N-56): auf der EIGENEN Basis (H20, bewegung_r, oberstes Fuenftel) kommt -0,06293 [-0,13183 .. -0,00785] heraus gegen registriert +0,0616 - gleiche Groessenordnung, UMGEKEHRTES Vorzeichen. Die Fuenftel haben keine Ordnung: +0,009 · +0,053 · -0,265 · -0,041 · +0,229; das BESTE ist Fuenftel 4, das die Tabelle mit -2,40 am haertesten bestraft. Bestaetigt 2.133 (0 von 2 Nachbarn getrennt, beide Haelften). ⚠️ DIE GROESSE BLEIBT - sie traegt Richtung (GS +0,00512, der staerkste der drei). NICHT belegt ist die TABELLE, und es sind die groessten Stufen im System. Nach 2.133 ist die belegte Form eine ZWEITEILUNG. --- ✔✔ REHABILITIERT 06.09. (N-53): `turnover` traegt RICHTUNG +0,00512 [+0,00212 .. +0,00831], 0/5 - richtungsrein der STAERKSTE der drei Groessen, zweieinhalbmal `funding`. Auf der registrierten Barrieren-Quote traegt es NICHT (+0,00168, Band mit Null), weil sein Aufloesungskanal (-0,00218) gegen die Richtung laeuft und den Effekt verdeckt. Der Vorschlag vom Vormittag (2.133: stilllegen) ist damit ueberholt - er stand auf dem gemischten Massstab. ⚠️ R-R9 OFFEN: auf welcher Zielgroesse die Stufen kalibriert werden. `q` ist ,Ziel vor Stop' (= G0); dort ist turnover schwach, weil die GEOMETRIE es daempft - das ist eine Aussage ueber die Geometrie, nicht ueber den Beitrag. --- FRUEHER: Nur 65 Symbole Abdeckung - das Nullband ist dreimal so breit wie bei den anderen, das Urteil wandert mit der Saat. ⚠️ OFFEN (N6): turnover traegt AUCH am Randmassstab (+0,01389 bei H20, 2.119) - registriert ist er nur am Mittel. Und er erklaert 18 % von `vola` (N1, p=0,025).

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
| **Umbauseite** | ✔ **nach** dem Messstandard (letzte Messung 11.09.) |

**Die Messkette:**

- **02.09.** — H-4c: traegt, aber SCHALTER statt Regler - die Monotonie fiel
- **02.09.** — N-14: als 12. Trichterstufe gebaut
- **04.09.** — F-207: Kombination mit funding_extrem verbessert die Sperre NICHT - Status quo bleibt
- **06.09.** — Schritt 3: H5 ab 2024 - traegt nicht
- **06.09.** — Schritt 4a A: H20 voll +0,01418 REPRODUZIERT
- **06.09.** — Schritt 4a B: H5 voll +0,00663 - traegt nicht
- **10.09.** — ✔ V2/N-73: 2 von 2 - der einzige live laufende Beitrag, der die Huerde ohne Einschraenkung nimmt
- **11.09.** — ✔ V11: stabil auf beiden Mengen (bis 0,05 · 0,02) - die schaerfsten Schranken im Feld

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
| **Umbauseite** | ✔ **nach** dem Messstandard (letzte Messung 10.09.) |

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
- **10.09.** — ⚠️ V9: unabhaengig von funding, aber geschichtet NICHT MEHR TRENNBAR (echter Nullbefund, 0,05 R)
- **10.09.** — ⚠️⚠️ Kriterium 2 FAELLT: +0,2039 [+0,0760 .. +0,3912] auf der 20-%%-Menge, Band schliesst die Null aus
- **10.09.** — ⚠️ N-73 nur 1 von 3 Mengen - der wackligste Kandidat

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
| **Umbauseite** | ⚠️ **VOR** dem Messstandard — Urteil unter anderen Regeln entstanden (letzte Messung 06.09.) |

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
| **Umbauseite** | ✔ **nach** dem Messstandard (letzte Messung 11.09.) |

**Die Messkette:**

- **31.08.** — H2 traegt nicht (Messung maechtig), H20 kein Urteil - die Positivkontrolle versagte dort
- **06.09.** — Schritt 4a: H5 voll +0,0101 TRAEGT, H5 2024 +0,0095 TRAEGT
- **10.09.** — ✔ V9: unabhaengig von funding · ✔ Kriterium 2: stabil auf ALLEN drei Mengen (bis 0,20 · 0,20 · 0,05)
- **11.09.** — ⚠️⚠️ V11: Kriterium 1 erfuellt (100 %%), N-73 aber NICHT - 2 von 3. Als Ersatz fuer `schnitt` gefallen

**Die Loesungsspur** — *kein Beitrag faellt ohne Grund:*

> ⚠️⚠️ ALS ERSATZ FUER `schnitt` GEPRUEFT UND GEFALLEN (V11, 11.09.): Kriterium 1 erfuellt er mit 100 %% Abdeckung, N-73 aber NICHT - 2 von 3 Mengen (10 %% +0,0846 TRAEGT · 20 %% +0,0698 TRAEGT · 50 %% +0,0156 TRAEGT NICHT bis 0,0213 R). Bei 50 %% ist es eine ECHTE Aussage, kein ,nicht trennbar'. ⚠️⚠️ UND DIE ZWEITE STUETZE IST AUCH WEG: ,die einzige MONOTONE Form' stammt aus **F-222/N-45** - einem Blatt mit Sperrkopf (,GILT NICHT ALS BEITRAGSURTEIL', gemessen auf Ziel-vor-Stop und/oder der freien Menge). Beide Argumente fuer ihn sind damit gefallen. ➔ OFFEN bliebe nur eine andere FORM oder ein anderer HORIZONT (N2: H5 ist nie gegengeprueft)

⚠️ NICHT VERWECHSELN mit `schnitt` (200-Tage), der am 31.08. zurueckgenommen wurde. H5 ist neu und gegenzupruefen (N2) - der Horizontverlauf H2 klein / H5 gross / H20 klein ist erklaerungsbeduerftig.

---

## ○ `akkumulationsmass (= schnitt, H90)`

**Hypothese:** Kauf in BODENNAEHE: je tiefer unter dem eigenen 200-Tage-Schnitt, desto guenstiger der Einstieg innerhalb einer Akkumulation.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H90 · 505 Krypto-Reihen · 3.292 Tage · zirkulaerer Verschub |
| **Wert** | stetig monoton ueber NEUN Baender: unter -40 % +0,0960 (+6,06 %) bis ueber +30 % -0,1508 (-11,79 %) |
| **Live** | - NICHT registriert |
| **Zustand** | **offen** |
| **Umbauseite** | ⚠️ **VOR** dem Messstandard — Urteil unter anderen Regeln entstanden (letzte Messung 07.09.) |

**Die Messkette:**

- **28.08.** — Nutzerauftrag: ,fuer Akkumulation eine Begruendung, also echtes Signalmass finden'
- **28.08.** — Schalter UNTER_SMA +0,0283 (p=0,000) - traegt, aber feuert an 68,5 % aller Tage
- **28.08.** — Die STETIGE Form ist staerker und monoton ueber neun Baender, in BEIDEN Kalenderhaelften
- **28.08.** — Kontrollen: TIEFPUNKT +0,4242 (Maschine intakt) · WOCHENTAG -0,0008 p=0,978 · DCA exakt 0,0000
- **28.08.** — ⚠️⚠️ TRAEGT NICHT FUER BTC/ETH/SOL - und genau die sind fuer akkumulation freigeschaltet
- **07.09.** — N-59: DERSELBE Wert traegt bei `einstieg` auf der selektierten Menge (+0,1707 R, 100 % Abdeckung)

⚠️⚠️ ES IST DERSELBE WERT WIE `schnitt` - nur auf H90 statt H20 und als Akkumulationsmass gelesen. Das war bis zum 07.09. nicht verknuepft: der Befund vom 28.08. stand in `Befund_Akkumulationsmass_28_08.md` und NICHT im Register. ⚠️ DIE ENTSCHEIDENDE EINSCHRAENKUNG: fuer BTC (-0,0251, p=0,723), ETH (-0,0308) und SOL (-0,0291) traegt es NICHT - und `asset_dca_settings` enthaelt genau BTC und ETH. Es ist kein n=3-Rauschen: die Kernwerte liegen 2,39 Standardfehler unter dem Mittel, und nur 14,3 % aller 505 Symbole haben einen negativen Vorsprung. ⚠️ Der Effekt SCHRUMPFT: unterstes Band 1. Haelfte +0,2020 -> 2. Haelfte +0,0879, Faktor 2,3. ⚠️ Und es ist KEIN Alpha-Nachweis: es sagt, WANN innerhalb einer Akkumulation gekauft wird - nicht, OB akkumuliert werden soll.

---

## ○ `schnitt`

**Hypothese:** Abstand zum eigenen 200-Tage-Schnitt.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H1..H20 Horizontlauf 31.08. |
| **Wert** | H5 -0,0069 · H10 -0,0118 · H20 -0,0221 |
| **Live** | - zurueckgenommen |
| **Zustand** | **offen** |
| **Umbauseite** | ✔ **nach** dem Messstandard (letzte Messung 11.09.) |

**Die Messkette:**

- **31.08.** — mittags als dritter tragender Beitrag registriert
- **31.08.** — abends im Horizontlauf gefallen - bei keinem Horizont trennbar, bei langen negativ
- **07.09.** — ✔ N-59: traegt auf der selektierten Menge, 100 %% Abdeckung
- **10.09.** — ✔ A2: traegt fuer die AKKUMULATION (+0,0470, p 0,000, 481 von 518 Symbolen) - auf der FREIEN Messmenge V1
- **10.09.** — ⚠️⚠️ Kriterium 2 FAELLT auf der Betriebsmenge: +0,1973 [+0,0717 .. +0,3892] bei 20 %%
- **11.09.** — ⚠️⚠️⚠️ ABER die Instabilitaet gehoert der AUSWAHL: mit ZUFALLSauswahl +0,0380 / +0,0264 / +0,0310, stabil in 3 von 3 - bei VIERMAL schaerferem Test
- **11.09.** — ⚠️⚠️ Der tragende Einwand ist ein anderer: Spearman +0,704 mit der Auswahl, Wirkung zu 4/5 Auswahlartefakt (2.222/2.335)

⚠️ ✔✔ DER 31.08.-BEFUND IST ABGELOEST (07.09., 2.153). Reproduziert mit DEMSELBEN Werkzeug drehen ALLE Vorzeichen: H5 -0,0069 -> +0,0092 ✔ · H10 -0,0118 -> +0,0158 ✔ · H20 -0,0221 -> +0,0299 (nicht trennbar). Die Kontrolle reproduziert bitgenau (funding H20 +0,0246). ⚠️ URSACHE: am 31.08. lief die Messung auf 1.314 Symbolen - Krypto PLUS 798 Aktien/ETF/Rohstoffe. Der N-19-Fix kam erst am 03./04.09. `funding` war geschuetzt (krypto-exklusive Quelle), `schnitt` NICHT - er kommt aus Kursreihen, und die gab es fuer Aktien. ⚠️⚠️ MEIN VERFAHRENSFEHLER: N-59 hat den Befund umgestossen, OHNE ihn zuerst zu reproduzieren (R-R11). Dass er am Ende faellt, macht das Verfahren nicht richtig. --- FRUEHER: ⚠️ Die Marken tragen weiterhin den STOP - nur als BEWERTUNGSbeitrag tragen sie nicht.

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
| **Umbauseite** | ✔ **nach** dem Messstandard (letzte Messung 11.09.) |

**Die Messkette:**

- **30.08.** — gemessen, beide Richtungen null
- **06.09.** — Schritt 4a: auf keinem Lauf, keinem Massstab
- **09.09.** — 2.244-amihud: der EINZIGE mit sauberem Stabilitaetsbild - nirgends trennbar UND konsistentes Vorzeichen (+0,004 bis +0,029)
- **11.09.** — ⚠️ laeuft LAENGS rueckwaerts (V4, offen)

**Die Loesungsspur** — *kein Beitrag faellt ohne Grund:*

> ⚠️⚠️ NICHT ALS BEITRAG, SONDERN AN ANDERER STELLE - und das ist belegt, nicht geraten: 2.166-woanders haelt fest, dass er AUSFUEHRBARKEIT misst, nicht Ertrag. Eine Groesse, die sagt ,wie teuer ist der Ausstieg hier', gehoert in die DIMENSIONIERUNG (Positionsgroesse, Slippage), nicht in die Potentialbewertung. ⚠️ Dazu 2.244-amihud: er ist zeitstabil und wirkungslos - das ist kein Kandidat, aber ein Grund, ihn nicht abzuschreiben. ⚠️ OFFEN bleibt V4: er laeuft LAENGS rueckwaerts, und das ist ungeklaert

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
| **Umbauseite** | ⚠️ **VOR** dem Messstandard — Urteil unter anderen Regeln entstanden (letzte Messung 31.08.) |

**Die Messkette:**

- **31.08.** — R1: faellt als Beitrag - gepoolt gemessen, unter der Tagesklammer nicht trennbar

⚠️ Die Marken tragen weiterhin den Stop.

---

## ✖ `oi_je_umsatz`

**Hypothese:** Offene Terminpositionen je Umsatz - wie stark steht der Terminmarkt relativ zum Kassamarkt?

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H20 · 122 Symbole · rund 1.400 bis 1.736 Tage |
| **Wert** | traegt auf KEINER der 3 zulaessigen Mengen |
| **Live** | - nicht registriert |
| **Zustand** | **traegt nicht** |
| **Umbauseite** | ⚠️ **VOR** dem Messstandard — Urteil unter anderen Regeln entstanden (letzte Messung 06.09.) |

**Die Messkette:**

- **06.09.** — N-9: 0 von 3 zulaessigen Mengen auf `bewegung_r` (Referenz `oi_aenderung` 3 von 3)
- **06.09.** — 2.169-zielgroesse: trug in N-17b gegen FRONTLOADING - eine ANDERE Zielgroesse

**Die Loesungsspur** — *kein Beitrag faellt ohne Grund:*

> ⚠️⚠️ OFFEN UND KONKRET: er ist gegen `bewegung_r` gefallen, also gegen die SPOT-Frage. Die HEBEL-Frage ist `barriere` (Ziel vor Stop) - dagegen ist er NIE gemessen. Der Weg dorthin fuehrt ueber **A1**: das Band auf binaeren Daten ist viermal zu eng (2.238), deshalb traegt dort sogar `zufall`. A1 hat einen benannten Loesungsweg (2.238-klasse): Fehlalarmquote der Barrieren-Anlage auf Nullwelten - dasselbe Verfahren, das am 09.09. den Nullbezug entschieden hat

---

## ✖ `long_bias`

**Hypothese:** Anteil der Long-Konten am Terminmarkt - viele Longs heissen einseitige Positionierung.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H20 · 122 Symbole · rund 1.400 bis 1.736 Tage |
| **Wert** | traegt auf KEINER der 3 zulaessigen Mengen |
| **Live** | - nicht registriert |
| **Zustand** | **traegt nicht** |
| **Umbauseite** | ⚠️ **VOR** dem Messstandard — Urteil unter anderen Regeln entstanden (letzte Messung 06.09.) |

**Die Messkette:**

- **06.09.** — N-9: 0 von 3 zulaessigen Mengen auf `bewegung_r`
- **06.09.** — 2.169-zielgroesse: trug gegen FRONTLOADING
- **05.09.** — N-17b: NICHT unabhaengig vom `rsi`

**Die Loesungsspur** — *kein Beitrag faellt ohne Grund:*

> ⚠️ ZWEIFACH belastet: gegen `bewegung_r` gefallen UND nicht unabhaengig vom `rsi`. Die `barriere`-Spur aus `oi_je_umsatz` gilt auch hier, ist bei ihm aber schwaecher - selbst wenn er dort traegt, bliebe die Redundanz mit `rsi` zu klaeren

---

## ✖ `top_bias`

**Hypothese:** Positionierung der groessten Konten - folgen die Grossen oder stehen sie dagegen?

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H20 · 122 Symbole · rund 1.400 bis 1.736 Tage |
| **Wert** | traegt auf KEINER der 2 zulaessigen Mengen |
| **Live** | - nicht registriert |
| **Zustand** | **traegt nicht** |
| **Umbauseite** | ⚠️ **VOR** dem Messstandard — Urteil unter anderen Regeln entstanden (letzte Messung 06.09.) |

**Die Messkette:**

- **06.09.** — N-9: 0 von 2 zulaessigen Mengen auf `bewegung_r`
- **06.09.** — 2.169-zielgroesse: trug gegen FRONTLOADING
- **05.09.** — N-17b: NICHT unabhaengig vom `rsi`

**Die Loesungsspur** — *kein Beitrag faellt ohne Grund:*

> ⚠️ Wie `long_bias` - und mit der duennsten Datenlage der vier: nur ZWEI Mengen sind ueberhaupt zulaessig. Ein Urteil auf zwei Mengen ist schwaecher als eines auf drei (2.312: ,1 von 1' ist keine starke Aussage)

---

## ✖ `taker_bias`

**Hypothese:** Verhaeltnis aggressiver Kaeufer zu Verkaeufern - wer nimmt den Preis, statt zu warten?

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H20 · 122 Symbole · rund 1.400 bis 1.736 Tage |
| **Wert** | traegt auf KEINER der 3 zulaessigen Mengen |
| **Live** | - nicht registriert |
| **Zustand** | **traegt nicht** |
| **Umbauseite** | ⚠️ **VOR** dem Messstandard — Urteil unter anderen Regeln entstanden (letzte Messung 06.09.) |

**Die Messkette:**

- **06.09.** — N-9: 0 von 3 zulaessigen Mengen auf `bewegung_r`

**Die Loesungsspur** — *kein Beitrag faellt ohne Grund:*

> ⚠️⚠️ DER AUSSICHTSREICHSTE DER VIER - und der einzige, bei dem die Redundanzfrage offen ist statt negativ beantwortet: `oi_wert` und `taker_bias` sind laut 2.168-offen NIE unter der Norm gemessen worden, und anders als `long_bias`/`top_bias` ist er nicht als `rsi`-redundant belegt. Dieselbe `barriere`-Spur wie `oi_je_umsatz`, ohne dessen Vorbelastung

---

## ✖ `rsi`

**Hypothese:** Relative-Staerke-Index - ueberkauft heisst Rueckschlag, ueberverkauft heisst Erholung.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H20 · volle Historie · 536 Symbole |
| **Wert** | traegt nicht UND auf drei Mengen zeitinstabil |
| **Live** | - nicht registriert |
| **Zustand** | **traegt nicht** |
| **Umbauseite** | ✔ **nach** dem Messstandard (letzte Messung 09.09.) |

**Die Messkette:**

- **09.09.** — Gesamtlauf: traegt auf keiner Menge (2.219)
- **09.09.** — N-89: auf DREI Mengen zeitinstabil (2.244)
- **09.09.** — 2.256: besteht die Spannenpruefung auf `frei` mit 2,16 - aber die Pruefung laesst JEDEN durch und taugt nicht

**Die Loesungsspur** — *kein Beitrag faellt ohne Grund:*

> ⛔ DOPPELT gefallen: wirkungslos UND zeitinstabil. Das ist der einzige Kandidat, bei dem beide Hauptkriterien gleichzeitig reissen. ⚠️ Er gehoert ausserdem zur Familie um `vola`/`schnitt` (Ueberlappung 0,25 bis 0,70, F-222/N-45) - aus der gehoert ohnehin nur EINE Vertreterin in die Bewertung. Eine Loesung waere nur ueber eine andere FORM denkbar, und dafuer gibt es keinen Anhaltspunkt

---

## ✖ `momentum`

**Hypothese:** Kursentwicklung ueber 250 Tage - wer gestiegen ist, steigt weiter.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H20 · volle Historie · 536 Symbole |
| **Wert** | widerspricht sich ueber die Mengen |
| **Live** | - nicht als Beitrag; er IST die Auswahl (`auswahl.waehle`, RUECKBLICK_TAGE = 250) |
| **Zustand** | **traegt nicht** |
| **Umbauseite** | ✔ **nach** dem Messstandard (letzte Messung 09.09.) |

**Die Messkette:**

- **09.09.** — Gesamtlauf: widerspricht sich ueber die Mengen (2.219)
- **09.09.** — 2.220: die KETTENMENGE ist gar keine momentum-selektierte - von 43 Werten passieren 25, WEIL sie Bestand haben

**Die Loesungsspur** — *kein Beitrag faellt ohne Grund:*

> ⚠️⚠️ HIER IST DIE LOESUNG KEINE MESSFRAGE: `momentum` ist bereits im System - als AUSWAHL, nicht als Beitrag. Ihn zusaetzlich als Beitrag zu fuehren, hiesse dieselbe Groesse zweimal zu zaehlen; genau daran ist `schnitt` gescheitert (2.335: Spearman +0,704 mit der Auswahl). ⚠️ Die OFFENE Frage ist eine andere und steht als N17 im Plan: **gehoert die Auswahl selbst ersetzt?**

---

## ✖ `momentum_kurz`

**Hypothese:** Kursentwicklung ueber wenige Wochen statt ueber ein Jahr - die kurze Variante von `momentum`.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H20 · volle Historie · 536 Symbole |
| **Wert** | widerspricht sich ueber die Mengen |
| **Live** | - nicht registriert |
| **Zustand** | **traegt nicht** |
| **Umbauseite** | ✔ **nach** dem Messstandard (letzte Messung 09.09.) |

**Die Messkette:**

- **09.09.** — Gesamtlauf: widerspricht sich ueber die Mengen (2.219)

**Die Loesungsspur** — *kein Beitrag faellt ohne Grund:*

> ⚠️ OFFEN, aber schwach: er ist der einzige der acht, zu dem es ausser dem Gesamtlauf KEINE eigene Untersuchung gibt. Er teilt die Kollinearitaetsfrage mit `momentum`. ⚠️ Ihn ernsthaft zu pruefen hiesse, ihn gegen die AUSWAHL zu entzerren - dasselbe Verfahren, das bei `schnitt` am 11.09. gelaufen ist (`entzerrte_reihe(auswahl_saat=...)`)

---

## ✖ `funding_extrem`

**Hypothese:** Abstand der Finanzierungsrate vom EIGENEN Normalzustand in MAD, vorzeichenlos - nicht der Querschnittsrang, sondern die eigene Auffaelligkeit.

| | |
|---|---|
| **Form** | regler |
| **Registrierungsbasis** | H20 · 300 Symbole (Funding-Abdeckung) |
| **Wert** | widerspricht sich ueber die Mengen |
| **Live** | - nicht registriert |
| **Zustand** | **traegt nicht** |
| **Umbauseite** | ✔ **nach** dem Messstandard (letzte Messung 09.09.) |

**Die Messkette:**

- **09.09.** — Gesamtlauf: widerspricht sich ueber die Mengen (2.219)
- **09.09.** — 2.255: er misst eine ANDERE Achse als `funding` - Eigen-Normalzustand statt Querschnittsrang
- **05.09.** — N-17b: die Kombination mit `oi_aenderung` ist echte Verstaerkung - aber F-207 zeigte, dass sie die LIVE-Sperre nicht verbessert

**Die Loesungsspur** — *kein Beitrag faellt ohne Grund:*

> ⚠️ OFFEN: er ist der einzige Gefallene, der in KOMBINATION schon einmal getragen hat (N-17b mit `oi_aenderung`). ⚠️ Aber F-207/F-208 haben gezeigt, dass die Kombination weder die Live-Sperre verbessert noch F-165s Schwelle erreicht. Als EIGENSTAENDIGER Beitrag ist er widerspruechlich; als Verstaerker ist er gemessen und zu schwach

