# REGISTER — DIE BEFUNDE

*Erzeugt aus `bestand.py`. **Nicht von Hand aendern.***

⚠️ **Wofuer:** eine Korrektur findet man in einem chronologischen Dokument nur durch VORWAERTSLESEN. Hier steht bei jedem abgeloesten Befund, **wodurch** und **warum**.

## ✔ WAS GILT

**2.143** — AUDIT: sechs von sieben Messungen des 06./07.09. liefen auf der FREIEN statt der selektierten Menge. F-212 belegt seit 04.09., dass die Beitraege dort auf 1,5 % der Anker wirken. Dieselbe Fehlerklasse wie 2.134 - die Grundmenge ist Teil der FRAGE

- Quelle: Methodik 2.143 / pruefe_audit_06_07_09.py

**2.143-norm** — ⚠️ Vier Nullbefunde ohne Trennschaerfe. Ich habe `messnorm` umgangen, weil meine Zielgroesse dort nicht vorgesehen war - und der Grund dafuer WAR der Befund. Wer die Norm umgeht, umgeht die Pruefung, die den eigenen Aufbau ablehnen wuerde

- Quelle: Methodik 2.143

**2.142-alt** — Kalibrierung durchgefuehrt: turnover-Stufen auf (+0,33 x3, -0,48 x2), SCHWELLE_VORGABE 0,080 -> 0,005. erreichbar_max faellt 0,1335 -> 0,0489 R, Durchlass steigt 16,4 % -> 54,0 %. Verfahren vorher an der alten Lage REPRODUZIERT (gab 0,080 zurueck)

- Quelle: Methodik 2.142 / Befundkarte 3.9d

**2.142-fiktion** — ⚠️⚠️ Haerter filtern macht das Ergebnis SCHLECHTER (bei 0,010: -0,0558 je verworfenem). Die alte Schwelle 0,080 war die beste WEGEN turnovers riesiger Stufen - die Trennschaerfe der Schwelle kam aus einer Fiktion

- Quelle: Methodik 2.142

**2.141** — `turnover`s Stufen lassen sich NICHT herleiten - weder als Fuenfteilung noch als Zweiteilung noch als SCHALTER. Trennschaerfe 2,0 Punkte; die registrierte Tabelle hat 5,55 Punkte Spanne - waere sie echt, wuerde man sie sehen

- Quelle: Methodik 2.141 / n58_turnover_stufen_neu.py

**2.140** — Bei H5 laufen 31,4 % der Anker FLACH aus (H20: 5,3 %). Die Kalibrierungsbasis zaehlt sie als Nicht-Treffer und liegt damit um +0,2898 R daneben - mit falschem Vorzeichen (-0,3654 gegen +0,0430)

- Quelle: Methodik 2.140 / n57_flach_in_der_produktion.py

**2.140-formel** — ✔ Die POTENTIALFORMEL stimmt fuer die Produktion: unter den Aufgeloesten liegt die Trefferquote bei 34,8 %, die Formel setzt basisrate(2,0) = 33,3 %. Kaputt ist die Messung, nicht die Bewertung

- Quelle: Methodik 2.140

**2.139** — Die LIVE geschaltete OI-Sperre traegt RICHTUNG: GS +0,00220 [+0,00058 .. +0,00373] bei H20 und +0,00381 [+0,00205 .. +0,00550] bei H5, beide 0/5. Reproduktion in der Live-Form gelungen (+0,00978, registriert +0,0145 im Band)

- Quelle: Methodik 2.139 / n56_oi_richtungsrein.py

**2.139-quote** — ⚠️ Dieselbe Sperre SENKT bei H5 die Barrieren-Trefferquote (-0,00262, Band ganz im Minus), weil der Aufloesungskanal dagegenlaeuft (-0,00989). Richtung besser, Quote schlechter - und `q` in der Potentialformel IST die Quote

- Quelle: Methodik 2.139

**2.139-turnover** — ⚠️⚠️ `turnover` reproduziert NICHT: gemessen -0,06293 [-0,13183 .. -0,00785] gegen registriert +0,0616 - gleiche Groessenordnung, umgekehrtes Vorzeichen. Die Fuenftel haben keine Ordnung (bestes ist 4, die Tabelle bestraft es mit -2,40). Bestaetigt 2.133

- Quelle: Methodik 2.139

**2.139-funding** — `funding` reproduziert bis in die FORM: Fuenftel +0,071 +0,083 +0,009 -0,053 -0,105, monoton, und auch die registrierte Tabelle hat bei Fuenftel 1 ihr Maximum

- Quelle: Methodik 2.139

**2.138** — `vola` ordnet den realisierten Ertrag: die Spreizung ruhig-lebhaft liegt in ALLEN 12 Geometrien ueber der artefaktbedingten (+0,035 bis +0,126 R, Tagesklammer). Es waehlt aber KEINE Bauform - dieselbe Geometrie gewinnt in allen Dritteln (Stop 2,0 x ATR / H20)

- Quelle: Methodik 2.138 / n55_vola_in_der_geometrie.py

**2.138-null** — Der Nullpunkt fuer ,EW in R' ist NICHT null: Tageskerzen ueberschiessen die Barriere, die nahe staerker als die ferne (P(Ziel|aufgeloest) 0,344 statt 0,333). Er wird aus drei GEEICHTEN Kunstwelten gewonnen; ungeeicht unterschaetzt man ihn um das Doppelte

- Quelle: Methodik 2.138

**2.136** — `turnover` traegt RICHTUNG +0,00512 [+0,00212 .. +0,00831], 0/5 - richtungsrein der STAERKSTE der drei. Auf der registrierten Barrieren-Quote traegt es nicht (+0,00168 ns), weil sein Aufloesungskanal (-0,00218) gegen die Richtung laeuft

- Quelle: Methodik 2.136 / n53_richtungsprobe_alle_drei.py

**2.136-f** — `funding` traegt RICHTUNG +0,00197 [+0,00024 .. +0,00376], 0/5, und reitet den Aufloesungskanal NICHT (AUF ns) - sein G0-Befund war sauber, nur unguenstig gemessen

- Quelle: Methodik 2.136

**2.136-EWR** — Auch der Erwartungswert in R ist kontaminiert: er feuert in der richtungsfreien Kunstwelt (+0,01363). Vier von sechs Massstaeben sind es - sauber ist allein GS

- Quelle: Methodik 2.136

**2.137** — Die zwei Ebenen spielen NICHT zusammen - funding und turnover wirken nicht staerker im guten vola-Drittel (Baender ueberlappen). `vola` ist ein UNABHAENGIGER Geometriehebel

- Quelle: Methodik 2.137

**2.135** — `vola` traegt KEINE Richtung - richtungsrein (symmetrische Barrieren, nur aufgeloeste Anker) -0,00041 [-0,00287 .. +0,00194], 2/5, keine Ordnung der Drittel. Der Befund geht restlos in zwei GROESSENkanaele auf

- Quelle: Methodik 2.135 / n52_vola_geometrieprobe.py

**2.135-AUF** — Die AUFLOESUNGSQUOTE traegt +0,03088 [+0,02753 .. +0,03436], monoton ueber die Drittel - ruhige Assets loesen ihre Barrieren nachweisbar oefter auf. Groesster sauberer Effekt des Tages, aber ueber die GEOMETRIE, nicht ueber den Markt

- Quelle: Methodik 2.135

**2.112** — Der MITTELWERT ist der falsche Massstab - der Ertrag liegt im oberen Rand (p50 -0,19 R, aber 6,65 % der Asset-Tage ueber +2 R)

- Quelle: Methodik 2.112

**2.115** — Ein im Rang GEFALLENES Asset hat auf kurzer Zeitachse mehr Randpotential (+0,0068, Band [+0,0034 .. +0,0108], Zufallskontrolle sauber)

- Quelle: Methodik 2.115

**2.116** — Die KATEGORIE traegt nicht (1,2 Prozentpunkte ueber das ganze Universum), der ZUSTAND innerhalb schon

- Quelle: Methodik 2.116

**2.117** — Der Datenqualitaetsfilter entfernt kein Rauschen, sondern den BELEG - er zerstoert den Befund aus 2.115

- Quelle: Methodik 2.117

**2.118** — Der Randmassstab hat Trennschaerfe (6 von 6 Kandidaten) und ist 2,5- bis 10-fach stumpfer als das Mittel - er wird ZWEITE Zielgroesse

- Quelle: Methodik 2.118

**2.119** — Reproduktionspflicht: alle drei Registrierungen reproduzieren; nichts ist gefallen

- Quelle: Methodik 2.119 · R-R11

**2.120** — `vola` ist kein Mitlaeufer, aber nicht reif: funding erklaert 3 % (p=0,325), turnover 18 % (p=0,025); der Rest ist im Schichtentest nicht trennbar

- Quelle: Methodik 2.120

**2.121** — `vola ODER turnover` traegt am Randmassstab mehr als jede Einzelgroesse - mengenkontrolliert, in beiden Historienhaelften, ueber drei Saaten

- Quelle: Methodik 2.121

**2.121-UND** — Werte mit BEIDEN Extremen sind WENIGER schlecht als Werte mit EINEM Extrem (UND-Reinheit +0,01267 gegen +0,01590 / +0,01678 einzeln)

- Quelle: Methodik 2.121
- Warum: unerklaert. Kein Messfehler - die Symmetrieprobe ist bitgenau. Es erklaert, warum UND versagt und ODER gewinnt

**2.122** — Die Schwelle ist ein Anteil von 59,9 % der bei DIESER Datenlage erreichbaren Spanne. Ein Wert mit nur Funding kommt zu 40 % durch, einer mit beiden Raengen nur zu 12 %

- Quelle: Methodik 2.122

**2.123** — `vola` allein traegt bei jeder Sperrmenge; der Abdeckungskompromiss kostet 17 % Wirkung

- Quelle: Methodik 2.123

**2.124** — `turnover` verschiebt die Frontloading-Quote um +4,0 bis +4,5 Punkte - bei JEDER Breite, Band ohne Null. Die Horizontwahl aus der Kursreihe ist belegbar und klein

- Quelle: Methodik 2.124

**2.126** — Die SPERRFORM ist fuer `vola` der falsche Weg - er gehoert als BEITRAG. Ein Beitrag unterliegt nicht der Bestandsausnahme und passt zur Quoten-Architektur

- Quelle: Methodik 2.126

**2.126-Auswahl** — Die 250-Tage-Momentum-Auswahl selektiert systematisch HOCHVOLATILE Werte: bei 5 % Auswahl trifft eine 20-%-vola-Sperre 74,8 % statt der erwarteten 20 %

- Quelle: Methodik 2.126
- Warum: auf der FREIEN Menge sind beide unabhaengig (20,3 % gegen 20,0 %) - die Ueberschneidung entsteht ausschliesslich durch die Auswahl

## ○ WAS OFFEN IST

**2.141-lage** — ⚠️ ENTSCHEIDUNG OFFEN: Tabelle lassen (aktiv falsch), auf die gemessene Zweiteilung +0,33/-0,48 (nicht belegt, aber 17x kleiner und gleichgerichtet) oder auf null (entfernt einen belegten Richtungstraeger). Jeder Weg verlangt R-R9

- Quelle: Methodik 2.141

**2.138-offen** — ⚠️ Die ZUSCHREIBUNG der Spreizung ist offen. Die Kunstwelt hat einen Strukturfehler: Hoch und Tief sind dort unabhaengiges Rauschen um den Schluss, in echten Daten liegt an einem Aufwaertstag das Tief nahe der Eroeffnung. Sie ueberschaetzt die Stop-Treffer. Naechster Schritt: Brownsche Bruecke je Tag

- Quelle: Methodik 2.138

**D3** — Ist H20 der richtige Horizont fuer die OI-Sperre, wenn der Betriebshorizont 3-5 Tage betraegt?

- Quelle: Methodik 2.119
- Warum: ENTWURFSfrage, keine Messfrage - Nutzerentscheidung

**N11** — Die Durchlassquote haengt an der SCHIEFE der Beitragsstufen, nicht am Asset: funding laesst 2 von 5 Fuenfteln durch, turnover nur 1 von 5

- Quelle: Methodik 2.122
- Warum: turnovers Maximum (+3,15) steht allein, der Zweite (+0,83) liegt bei 26 % davon. Bei funding liegt der Zweite (+0,82) bei 63 % des Maximums (+1,30)

**N14** — Traegt das HEBEL-SCREENING als zweite, von der Kursreihe UNABHAENGIGE Quelle fuer die Horizontwahl?

- Quelle: Methodik 2.124 · F-185
- Warum: 227.395 OI-Zeilen, 13.254 Kandidaten. Der einzige verbliebene Hebel fuer mehr Trennschaerfe - alle Kursreihengroessen sind ausgemessen

**N15** — `UND @ 10 %` zeigt 58,3 % frontlastig (+7,1 Punkte, Band [+2,8 .. +13,0]) bei nur 6,1 % der Anker

- Quelle: Methodik 2.124
- Warum: Band ohne Null, aber die anteilgewichtete Wirkung traegt nicht - zu wenige Anker. Mit mehr Terminmarkt-Historie pruefbar. Zurueckgestellt, nicht verworfen

**N16** — `vola` als BEITRAG verdrahten - Quotenpunkte je Fuenftel aus der Randwirkung

- Quelle: Methodik 2.126
- Warum: R-R9 beachten: Beitragswechsel = Neukalibrierung der Schwelle plus Nachzug von KALIBRIERT_FUER

**N17** — Traegt der Momentum-Rang etwas ueber `vola` hinaus? 74,8 % Ueberschneidung bei 5 % Auswahl

- Quelle: Methodik 2.126

**N18** — Der Engpass ist der COOLDOWN (93,8 %), nicht die Auswahl und nicht eine fehlende Sperre

- Quelle: F-180/F-182 · Methodik 2.126
- Warum: jede weitere Sperre verschaerft ein System, dessen Problem nicht Durchlaessigkeit ist

**N10** — Die Potentialformel meint eine BARRIEREN-Quote, das Randmass eine HORIZONT-Quote

- Quelle: Methodik 2.121

**N6** — `turnover` traegt auch am RAND (+0,01389 bei H20), registriert ist er nur am Mittel

- Quelle: Methodik 2.119

**N7** — Der Schichtentest braucht rueckwirkend eine Trennschaerfe - alle frueheren Nullbefunde daraus sind unbeziffert

- Quelle: Methodik 2.120
- Warum: messe_kandidaten_als_regel.geschichtet() hatte nie eine Positivkontrolle

**N2** — Warum traegt `schnitt50` bei H5, aber nicht bei H2 und H20?

- Quelle: Schritt 4a

## ↩ WAS ABGELOEST IST

**2.141** — „`turnover`s Stufen lassen sich nicht herleiten"

- Quelle: Methodik 2.141
- **Abgeloest durch: 2.143**
- Warum: auf der FREIEN Menge gemessen, wo selbst funding bei -0,0003 R liegt. Auf der selektierten reproduziert turnover: +0,0635 gegen registriert +0,0616 (F-212)

**2.142** — „Kalibrierung durchgefuehrt: turnover auf +0,33/-0,48, Schwelle 0,005"

- Quelle: Methodik 2.142
- **Abgeloest durch: 2.143**
- Warum: ZURUECKGENOMMEN - stand auf 2.139 und 2.141, beide gefallen. Es bleibt der R-R9-Verstoss (nach Wirkung statt Durchlassquote kalibriert) und die Reproduktion des Verfahrens

**2.139-quote-deutung** — „`q` in der Potentialformel zaehlt einen wertlosen Kanal mit"

- Quelle: Methodik 2.139
- **Abgeloest durch: 2.140**
- Warum: falsch adressiert. Die Kette hat KEINEN Zeitausstieg - in der Produktion laeuft eine Position bis Stop oder Ziel. Der Fehler sitzt in der Messkonvention mit festem Horizont, nicht in der Formel

**Audit-H20R** — „Die Registrierungsbasis H20/R ist kontaminiert"

- Quelle: Audit 06.09.
- **Abgeloest durch: 2.139**
- Warum: zu stark formuliert. Belegt war die Kontamination fuer H5 mit `vola`; bei H20 mit externen Kennzahlen feuert `bewegung_r` in keiner der beiden Kunstwelten

**2.133-turnover** — „`turnover` ist in keiner Form belegt und gehoert stillgelegt"

- Quelle: Methodik 2.133
- **Abgeloest durch: 2.136**
- Warum: auf der Barrieren-Quote gemessen, die Aufloesung und Richtung mischt. Richtungsrein ist turnover der staerkste der drei

**2.133-vola** — „`vola` ist die einzige Groesse mit belegter Stufenordnung und gehoert registriert"

- Quelle: Methodik 2.133
- **Abgeloest durch: 2.135**
- Warum: an der Barrieren-Quote gemessen, die Aufloesung und Richtung mischt. Richtungsrein bleibt nichts uebrig

**2.113-M4** — „tief im Rang = mehr Chance ist widerlegt - in R wird nach unten alles schlechter"

- Quelle: Methodik 2.113
- **Abgeloest durch: 2.115**
- Warum: am MITTELWERT gemessen und unzulaessig zu einer Asset-Aussage verallgemeinert - Regel 3

**2.113-S3** — Rangzugehoerigkeit traegt (+0,1020 R zwischen „in Top 100 geblieben" und „neu")

- Quelle: Methodik 2.113
- **Abgeloest durch: 2.114**
- Warum: GEPOOLT gerechnet. Mit Tagesklammer +0,0379, Band [-0,0317 .. +0,1030] - traegt nicht

**2.116-9.7** — Die 9,7 % Ueberdeckung zwischen System und Messuniversum sind ein Problem

- Quelle: Methodik 2.116
- **Abgeloest durch: 2.116-Korrektur**
- Warum: Nutzerkorrektur: die Bewertung muss allgemein und neutral funktionieren. Auf die gehandelten Symbole zu messen waere ein Zirkelschluss

**2.111-ab2024** — Der Abschnitt ab 2024 ist die primaere Messbasis

- Quelle: Methodik 2.111
- **Abgeloest durch: 2.119**
- Warum: Die Wirkung der Kandidaten ist NICHT epochenabhaengig. Auf 959 Tagen sind sie in JEDEM Fenster unentscheidbar - Datenmenge, nicht Epoche. Primaer ist jetzt die volle Historie

**S3-Meldung** — Beide registrierten Beitraege fallen bei H5 ab 2024

- Quelle: Schritt 3, 06.09.
- **Abgeloest durch: 2.119**
- Warum: Zwei Groessen gleichzeitig geaendert (Horizont UND Epoche). Alle drei Registrierungen reproduzieren auf ihrer eigenen Basis - R-R11

**N1** — Traegt `vola` unabhaengig, oder ist es redundant zu funding/turnover?

- Quelle: Schritt 4a
- **Abgeloest durch: 2.120**
- Warum: beantwortet: KEIN Mitlaeufer (82 % bleiben), aber auch nicht reif - 18 % Ueberlappung mit turnover belegt (Rang 1 von 40, p=0,025), Rest nicht trennbar

**F-206-Anfuehrung** — F-206 (turnover+vola praktisch identisch) belegt Redundanz bei N1

- Quelle: eigene Anfuehrung 06.09.
- **Abgeloest durch: 2.120**
- Warum: F-206 wurde auf H2/Frontloading gemessen; F-207 haelt fest, dass sich das nicht auf H20/R uebertraegt. Die Anfuehrung war eine Horizontverwechslung

**N5** — Traegt die KOMBINATION `vola` UND `turnover` am Randmassstab mehr als jede Groesse einzeln?

- Quelle: Methodik 2.120
- **Abgeloest durch: 2.121**
- Warum: beantwortet: ODER traegt (+0,00777), mengenkontrolliert +26 % bis +34 % ueber der besten Einzelgroesse, beide Haelften, drei Saaten. UND traegt NICHT

**N8** — `turnover` ist bereits als Regler am Mittel registriert - eine Sperre mit `turnover` wendet ihn ZWEIMAL an

- Quelle: Methodik 2.121
- **Abgeloest durch: 2.122**
- Warum: KEINE Doppelzaehlung: wo turnover vorliegt (7 von 57), verlangt das Tor ohnehin Fuenftel 0 - die Sperre wuerde Fuenftel 4 sperren, das nie durchkommt. Wo er fehlt (50 von 57), kann die Sperre ihn nicht auswerten. Wirkungslos, nicht doppelt

**88-Prozent-Meldung** — 88 % der beobachteten Werte koennen die Potentialschwelle nie erreichen

- Quelle: eigene Rechnung 06.09.
- **Abgeloest durch: 2.122**
- Warum: gegen die FESTE Vorgabe 0,080 gerechnet statt gegen `Potential.schwelle` je Datenlage. Das Projekt hatte genau diesen Fehler am 31.08. selbst gemacht und behoben - ich habe ihn nachgebaut

**N12** — Traegt `vola` ALLEIN als Sperre genug?

- Quelle: Methodik 2.122
- **Abgeloest durch: 2.123**
- Warum: JA - bei allen vier Sperrmengen (10/20/30/40 %). Bei 40 % erreicht sie 83 % der Kombinationswirkung bei 516 statt 65 Symbolen. Der Kompromiss kostet 17 % Wirkung fuer die achtfache Abdeckung

**Breite-Hebel** — Eine engere Auswahl verbessert die Frontloading-Verschiebung um 40 %

- Quelle: eigene Lesart 06.09.
- **Abgeloest durch: 2.124**
- Warum: Punktschaetzer-Vergleich ohne Deckung. Die Baender ueberlappen vollstaendig: +4,0 [+2,8 .. +5,2] gegen +4,5 [+2,8 .. +6,2]

**Kursreihe-Nullaussage** — Die Kursreihe liefert die Instrumentwahl nicht

- Quelle: eigene Formulierung 2.123
- **Abgeloest durch: 2.124**
- Warum: Kapitulationsformel statt Analyse. Der richtige Vergleich ist nicht ein perfekter Waehler, sondern der TAKT - und der hat null gemessenen Vorteil (Regel 1)

**N9** — 36 % Sperrmenge bei zwoelf bestehenden Trichterstufen - welche Durchlassmenge bleibt?

- Quelle: Methodik 2.121
- **Abgeloest durch: 2.126**
- Warum: Die Frage war falsch gestellt. Die Werte passieren die Auswahl ueber den BESTANDSVORRANG, nicht ueber den Momentum-Rang (F-180/F-182) - eine Durchlassrechnung auf der Momentum-Auswahl bildet den Betrieb nicht ab. Und eine vola-Sperre stuende vor derselben Gabel wie N-14: mit Bestandsausnahme wirkungslos, ohne sie trifft sie genau die Werte, die als einzige durchkommen

