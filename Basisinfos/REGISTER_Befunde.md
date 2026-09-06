# REGISTER — DIE BEFUNDE

*Erzeugt aus `bestand.py`. **Nicht von Hand aendern.***

⚠️ **Wofuer:** eine Korrektur findet man in einem chronologischen Dokument nur durch VORWAERTSLESEN. Hier steht bei jedem abgeloesten Befund, **wodurch** und **warum**.

## ✔ WAS GILT

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

## ○ WAS OFFEN IST

**D3** — Ist H20 der richtige Horizont fuer die OI-Sperre, wenn der Betriebshorizont 3-5 Tage betraegt?

- Quelle: Methodik 2.119
- Warum: ENTWURFSfrage, keine Messfrage - Nutzerentscheidung

**N5** — Traegt die KOMBINATION `vola` UND `turnover` am Randmassstab mehr als jede Groesse einzeln?

- Quelle: Methodik 2.120
- Warum: beide tragen dort etwas, und 82 % von vola sind unabhaengig - das ist die naheliegende Frage

**N6** — `turnover` traegt auch am RAND (+0,01389 bei H20), registriert ist er nur am Mittel

- Quelle: Methodik 2.119

**N7** — Der Schichtentest braucht rueckwirkend eine Trennschaerfe - alle frueheren Nullbefunde daraus sind unbeziffert

- Quelle: Methodik 2.120
- Warum: messe_kandidaten_als_regel.geschichtet() hatte nie eine Positivkontrolle

**N2** — Warum traegt `schnitt50` bei H5, aber nicht bei H2 und H20?

- Quelle: Schritt 4a

## ↩ WAS ABGELOEST IST

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

