# Voranalyse Vorsprungs-Atlas (25.10.2026)

**Wozu:** Nutzer 25.10.:
- *„wir müssen den Vorsprung ausbauen und das ist unabhängig von den Kosten“*
- *„der Drift muss über die besseren assets und optimale Einstiege ausgeglichen werden, es gibt Assets und Einstiege welche dies ermöglichen wir wissen nicht wie“*
- *„ja Voranalyse Vorsprungs-Atlas starten, prüfen gegenprüfen und doku“*

**Frage:** Wo im Ertrag eines Einstiegs sitzt ein Vorsprung (Markt, Klasse, Auswahl, Zeitpunkt), und lassen sich Auswahl und Einstieg so verbinden, dass zusammen etwas trägt, was einzeln nicht trägt?

**Hauptgröße:** **Vorsprung gegen die Drift, ohne Kosten** (Nutzer Punkt 1); die Kosten sind eine spätere Prüfung.

Hier wird **nicht** gemessen, ob die Kombination trägt; das macht erst der Messplan (§5), nach Ja. Werkzeuge: `p85_atlas_voranalyse.py`, Gegenprobe `p85_gegenprobe.py`, Ausgaben jeweils als `.txt`.

## 1. Was schon belegt ist

| Teil | Befund | Quelle |
|---|---|---|
| **Auswahl** (Watchlist-Ordnung in der Klasse) | trägt: Saldo „verdoppelt minus abgestürzt“ gegen die Klasse +10,4 (2021–23) / +14,4 Pp (ab 2024), Rang 1,000; Wirkung steigt monoton von Fünftel zu Fünftel; jedes Jahr 2019–2025 positiv | Spot §25.6 |
| **Auswahl in Dollar** (Wert ohne F9, B4-Regel) | Wirkung von Fünftel 1 bis 5 ab 2024: −17,2 / −4,7 / +3,0 / +6,0 / **+12,1 Pp** über 12 M gegen die Zelle; unteres Fünftel −12,5 Pp gegen Zufall, Rang 0,000 | `b4_vormessung.txt`, E-101 |
| ⚠️ **Klasse gegen BTC** | auch der beste Korb verlor gegen BTC: −7 % (2021–23), **−26 %** (ab 2024) in 12 M | Spot §25.6 |
| **Einstieg** (REGEL0) | Vorsprung gegen die Drift je Handel +0,2 bis +0,4 % (bei echtem Datenbeginn), nicht von Zufall zu trennen; je Tag negativ; sitzt an marktweiten Tagen | E-139 |
| **Markt** | Season-Ampel trennt Season und Bärenmarkt (Holdout 2017/18) | E-124 |
| Kombination Auswahl × Einstieg | **nie gemessen** | — |

## 2. Machbarkeit (`p85`)

- **R-R11 der Auswahl:** Mit kurzem Horizont (`paare_mw(1)` statt `(365)`) ist der Wert an allen **19.610** gemeinsamen Ankern **gleich** (Klasse und Perzentil 100 %). Er liegt damit für 93 Monatsstichtage vor, 2019-01 bis 2026-09.
- **Abdeckung der REGEL0-Einstiege** (Wert am letzten Stichtag vor dem Einstieg, gültig ab Stichtag + 1 Tag):

| Einstiege | mit Wert | Fünftel 1 / 2 / 3 / 4 / 5 | Klassen H / M / S |
|---|---|---|---|
| Referenz 2024–26 (10.732) | **95 %** | 2.563 / 2.210 / 1.705 / 1.789 / 1.980 | 1.051 / 3.856 / 5.340 |
| Lauf B 2023 (1.714) | **94 %** | 329 / 172 / 364 / 373 / 372 | 242 / 780 / 588 |

Ohne Wert bleiben vor allem **BTC, ETH und SOL**: Der Kern ist in der Watchlist bewusst ausgenommen. Dazu kommen ganz junge Coins.

## 3. Auflösung (`p85`, Zufallseinteilung je Coin und Stichtag, ohne Blick auf den echten Effekt)

| Horizont | kleinster erkennbarer Unterschied „oberes Fünftel − alle“, je Handel / je Tag (2024–26) | dasselbe für 2023 | **erwarteter Auswahl-Effekt** (Dosis +12,1 Pp / 12 M, anteilig) |
|---|---|---|---|
| 24 h | 0,29 / 0,77 Pp | 0,43 / 1,00 Pp | **0,03 Pp** |
| 7 T | 0,80 / 1,79 Pp | 2,41 / 2,82 Pp | 0,23 Pp |
| 30 T | 2,71 / 5,09 Pp | 9,94 / 9,98 Pp | 0,99 Pp |

⚠️ **Der Kernbefund der Voranalyse:**
- Der Auswahl-Vorsprung wirkt **langsam, über Monate**. Innerhalb eines Einstiegs über 24 h ist er rund **zehnmal kleiner** als messbar, bei 7 und 30 Tagen etwa 3- bis 5-mal kleiner.
- ⇒ Eine Kombination, bei der sich Auswahl und Einstieg einfach **addieren**, ist mit REGEL0-Einstiegen **nicht nachweisbar**.
- **Nachweisbar** ist nur ein **Zusammenwirken**: REGEL0-Einstiege in guten Coins laufen deutlich besser, als die Summe der Teile erwarten lässt. Ab etwa 0,3 Pp je Handel bzw. 0,8 Pp je Tag wäre das sichtbar.
- Und der **Drift-Ausgleich**, nach dem du fragst, findet auf der **Monatsebene** statt, nicht im Einzelhandel. Dort ist die Auswahl belegt, aber sie schlug in beiden Epochen BTC nicht (Korb −7 % bzw. −26 %).

## 4. Gegenprobe (`p85_gegenprobe.py`, 3/3)

| | Ergebnis |
|---|---|
| G1 Abdeckung über `merge_asof` statt `searchsorted` | gleich: 10.247 mit Wert, gleiche Verteilung über die Fünftel |
| G2 Auflösung als Formel (cluster-robuster Standardfehler, 2.807 Coin-Stichtage) | 0,26 Pp gegen 0,29 Pp aus der Simulation (Faktor 0,88) |
| G3 angesetzte Dosis | +12,1 Pp steht so in `b4_vormessung.txt` |

⚠️ **Eigener Fehler, vor der Bewertung behoben:** Die erste Fassung zog die Zufallseinteilung je **Einstieg**. Das Fünftel gilt aber je **Coin und Stichtag**, und derselbe Coin feuert mehrmals. Neu gezogen je Coin und Stichtag; die Auflösung bei 30 T ist dadurch deutlich schlechter (1,60 → 2,71 Pp).

## 5. Messplan A Fassung 1 — Vorschlag (abgelöst durch die Festlegung in §6)

**Teil A1 — Zerlegung auf der Monatsebene** (Auskunft, beschreibend; 2021–23 und ab 2024):
- je Monatsstichtag der Ertrag über 1 und 12 Monate, zerlegt in:
  - **Markt:** BTC;
  - **Klasse gegen BTC:** Mittel der Altcoins in der Klasse;
  - **Auswahl:** Fünftel 5 gegen die Klasse.
- Dazu die Frage: **Wie viel der Drift gegen BTC gleicht die beste Auswahl aus**, je Klasse und je Season-Ampel-Stufe?
- Beantwortet deinen Punkt 2 mit Zahlen. Kein Urteil „trägt“.

**Teil A2 — Zusammenwirken Auswahl × Einstieg** (Test, ein vorab festgelegter Vergleich):
- **Größe:** Z1 (24 h, ohne Kosten) der REGEL0-Einstiege im **oberen Fünftel** minus der übrigen Einstiege, je Handel **und** je Tag.
- **Rang:** Tagesblock-Rang (7-Tage-Blöcke, 1.000 Ziehungen).
- **Einstiege auf zwei Wegen:**
  - Referenz (Daten wie im Betrieb);
  - Lauf A (Datenbeginn 2019), weil die REGEL0 selbst nicht robust ist (E-139).
- **Bestätigung:** Lauf B 2023, unberührt.
- **Selbsttest vor dem ersten Blick:**
  - (a) 100 Zufallseinteilungen je Coin und Stichtag: Fehlalarm ≤ 5 %;
  - (b) gepflanzt +0,5 Pp im oberen Fünftel: erkannt ≥ 80 %.
- **Trägt, wenn:**
  - Differenz > 0 und Rang ≥ 0,95, je Handel **und** je Tag, auf **beiden** Einstiegswegen 2024–26;
  - **und** in 2023 dieselbe Richtung (Differenz > 0) bei beiden Gewichtungen.
- **Auskunft:** dasselbe über 7 und 30 Tage und je Klasse.

**Folgen:**
- **A2 trägt:** Kandidat „REGEL0 nur im oberen Fünftel“. Danach Kosten und Betriebs-Voranalyse.
- **A2 trägt nicht:** Der Einstieg auf kurzem Horizont ist für Altcoins als Quelle des Vorsprungs **erledigt** (Abbruchregel). Weiter geht es nur auf der Monatsebene, mit den Zahlen aus A1: Monatskorb aus dem oberen Fünftel, gelenkt von der Season-Ampel, gegen BTC.

**Aufwand:** rund 1 h Rechenzeit, kein Download, keine Betriebsänderung.

⚠️ **Ehrlich:**
- 2024–26 ist für die REGEL0 schon gesehen. A2 ist deshalb **ein** vorab festgelegter Vergleich, keine Suche. Die Bestätigung auf 2023 ist klein (372 Einstiege im oberen Fünftel, Auflösung 0,43 / 1,00 Pp).
- BTC, ETH und SOL haben keinen Wert und fallen aus A2 heraus.

## 6. Messplan A Fassung 1 — VORAB FESTGELEGT 25.10.2026

Nutzer 25.10.: *„ja Messplan A festlegen, prüfen gegenprüfen und doku - immer alle Teilergebnisse mit mir Abstimmen und berücksichtigen, dass sich Krypto bis heute massiv geändert hat (millionen von Altcoins großteil unintressant, btc volatilität hat nachgelassen). Bevor wir abbrechen muss es einen grund geben und wenn es diesen gibt immer eine Lösung suchen.“*

### 6.1 Drei Vorgaben des Nutzers, eingearbeitet

| Vorgabe | Umsetzung |
|---|---|
| **Teilergebnisse abstimmen** | A1 wird gerechnet und **vorgelegt**; A2 läuft erst nach der Abstimmung über A1. Der Plan für A2 ist trotzdem jetzt fest |
| **Krypto hat sich massiv geändert** | Ausweis **je Epoche**: E2 2021–23 und **E3 ab 2024** (der heutige Markt, Gewicht im Urteil). **Je Klasse:** H und M (die relevanten) getrennt von S (die Masse der Kleinwerte). Dazu die **BTC-Volatilität je Jahr** und die **Zahl der Coins je Klasse** als Auskunft. Universum bleibt die Binance-Messbasis (schon eine Auswahl aus den Millionen) |
| **Kein Abbruch ohne Grund, dann Lösung suchen** | Die Abbruchregel aus §5 entfällt. Trägt ein Teil nicht, folgt eine **Ursachenanalyse** (welche Klasse, welcher Horizont, welche Tage, welcher Einstiegsweg) und ein **Lösungsvorschlag Fassung 2**, zur Abstimmung |

### 6.2 Teil A1 — Zerlegung auf der Monatsebene (Auskunft; `p86_a1_zerlegung.py`)

- **Anker:** jeder Monatsstichtag × Coin der Messkette (`mk_messung.paare_mw(h)`, h = 30 und 365 Tage, eingestellte Coins wie in B4). Fünftel nach Wert ohne F9 (B4-Regel) am Stichtag, aus `paare_mw(1)` (R-R11 §2).
- **Größen je Stichtag × Klasse:**
  - BTC-Ertrag;
  - Mittel der Klasse;
  - Klasse − BTC;
  - Fünftel 1–5 − Klasse (Dosis);
  - **Fünftel 5 − BTC**;
  - Anteil der Stichtage, an denen Fünftel 5 BTC schlägt.
- **Gewichtung:** jeder Stichtag gleich (wie B4). Epoche = Mittel der Stichtage.
- **Band:** gleitende Blöcke über die Stichtage (Blocklänge = Horizont in Monaten, mindestens 1), 2.000 Ziehungen.
- **Je Season-Ampel-Stufe:** Stufe am Stichtag aus `season_ampel.geltend(stufen(...))` auf `am_kalibrierung.csv` (2019-04 bis 2026-06).
- **Auskunft:** BTC-Volatilität je Jahr (CoinMetrics, Tagesrenditen, aufs Jahr gerechnet) und Zahl der Coins je Klasse und Epoche.
- **Kein Urteil „trägt“.** A1 beantwortet, wie viel der Drift gegen BTC die beste Auswahl ausgleicht, wo (Klasse, Ampel-Stufe) und wie sich das seit 2024 verändert hat.

### 6.3 Teil A2 — Zusammenwirken Auswahl × Einstieg (Test; erst nach der Abstimmung über A1)

- **Einstiege:**
  - Referenz `kern48jbz_einstiege_bestand.csv` und Lauf A `data/_hist/einstiege_A.csv`, je 2024-01 bis 2026-08;
  - Bestätigung Lauf B `data/_hist/einstiege_B.csv` (2023).
- **Fünftel:** Wert ohne F9 am letzten Stichtag t mit t + 1 Tag ≤ Einstieg.
- **Z1 (24 h):** Ertrag (Schluss zu Schluss, ohne Kosten) minus Drift Coin-Jahr, genau wie `p83`.
- **Größe D:** Z1(Fünftel 5) − Z1(Fünftel 1–4).
  - **je Handel:** jeder Einstieg gleich;
  - **je Tag:** Tagesmittel je Gruppe, dann jeder Tag gleich.
- **Rang:** Tagesblock-Bootstrap (7-Tage-Blöcke, 1.000 Ziehungen), Anteil D > 0.
- **Selbsttest vor dem ersten Blick:**
  - (a) 100 Zufallseinteilungen je Coin und Stichtag (gleicher Anteil wie echt): Fehlalarm (Rang ≥ 0,95) ≤ 5 %, je Gewichtung;
  - (b) +0,5 Pp auf Z1 des oberen Fünftels gepflanzt: erkannt ≥ 80 %, je Gewichtung.
- **Trägt, wenn:**
  - D > 0 und Rang ≥ 0,95, je Handel **und** je Tag, auf **beiden** Einstiegswegen 2024–26;
  - **und** 2023 D > 0 in beiden Gewichtungen.
- **Auskunft:** 7 T und 30 T; je Klasse H/M/S; je Jahr; je Season-Ampel-Stufe.
- **Folgen:**
  - trägt → Kandidat „REGEL0 nur im oberen Fünftel“, danach Kosten und Betriebs-Voranalyse;
  - trägt nicht → Ursachenanalyse und Lösungsvorschlag Fassung 2 (§6.1).

### 6.4 Ergänzung vor dem ersten Lauf (25.10.2026)

Nutzer 25.10.: *„Vergleiche auch ob die top 100 Altcoins oder u.U. top 50 ggf. anders als der Gesamtmarkt gesehen werden kann.“*

- A1 weist zusätzlich die Gruppen **Top 30, Top 50 und Top 100** aus, nach dem Marktwert-Rang am Stichtag (`mk_messung.rang_mw`: Umlauf CoinGecko × Kurs, Näherung geprüft in Spot §25.1), ohne die Stabilitätsbedingung der Klasse H.
- Daneben steht der **Gesamtmarkt** (alle Anker, auch S und Coins ohne Umlaufangabe).
- Je Gruppe und Epoche dieselben Größen wie §6.2: Gruppe − BTC, Fünftel 5 in der Gruppe − Gruppe, Fünftel 5 − BTC, Anteil der Stichtage mit Fünftel 5 > BTC, Band.
- Coins **ohne Umlaufangabe** haben keinen Rang und fehlen in den Top-Gruppen. Ihr Anteil am Gesamtmarkt wird ausgewiesen.
- In A2 kommt dieselbe Gruppierung als **Auskunft** hinzu; das Urteil bleibt wie in §6.3.

### 6.5 Abgleich mit dem Mess-Regelwerk vor jeder Bewertung (25.10.2026; Nutzer: *„gehe auch vorher in unser mess Regelwerk damit wir hier keine Abweichungen haben“*)

| Regel (`messnorm`) | Abweichung gefunden | Behebung |
|---|---|---|
| **Blocklänge** = max(15 T, 3 × Horizont) (`_block`), je Messung nachgeprüft (Autokorrelation beim Blockabstand ≤ 0,15, `pruefe_block`) | A1 lief zuerst mit 1 bzw. 12 Monaten; der Plan A2 und Messplan R (`p83`) mit 7 Tagen | A1: Block 3 Stichtage (1 M) bzw. 37 (12 M), Autokorrelation ausgewiesen. **A2: 15-Tage-Blöcke** plus `pruefe_block`. R: siehe Nachtrag E-139 |
| **Unter 20 Blöcken: KEIN BEFUND** (`Befund`, Z. 689) | nicht angewendet | A1 gibt unter 20 Blöcken kein Band aus, nur den Punktwert („beschreibend“) |
| **Urteilsstufen** TRÄGT / TRÄGT NICHT BIS X / NICHT TRENNBAR / KEIN BEFUND; Bezug = **Nullpunkt** (Mittel der Nullwelten) | Plan A2 kannte nur „trägt / trägt nicht“ und den Bezug 0 | A2 übernimmt die Stufen und den Nullpunkt (Mittel der 100 Zufallseinteilungen); „trägt nicht bis X“ aus der Pflanzung |
| Band über Blöcke, nicht über Einzelwerte (Methodik 2.47) | A1 lief zuerst mit gleitenden Blöcken **ohne Umlauf**; der Punktwert lag teils außerhalb seines Bands | zirkuläre Blöcke |

**Plan A2, damit vor dem Lauf berichtigt:**
- Rang und Band über **15-Tage-Blöcke**, Autokorrelation geprüft.
- Bezug ist der Nullpunkt der Zufallseinteilungen.
- Urteil in den Stufen der Norm: „trägt“ nur, wenn das Band den Nullpunkt ausschließt, je Handel **und** je Tag, auf beiden Einstiegswegen; 2023 in derselben Richtung.
- Alles Übrige wie §6.3.

## 7. Ergebnis Teil A1, 25.10.2026 (Auskunft; `p86_a1_zerlegung.py`, Gegenprobe `p86_gegenprobe.py` 3/3)

**Nach dem Regelwerk belastbar ist nur 1 Monat über alle Jahre 2019–2026** (92 Stichtage, 31 Blöcke, Autokorrelation ≤ 0,15). Je Epoche hat 1 M nur 10–12 Blöcke, 12 M höchstens 2. Das ist **KEIN BEFUND**; die Punktwerte sind dort nur beschreibend.

### 7.1 Belastbar: 1 Monat, alle Jahre (Pp je Monat, Band 95 %)

| Gruppe | Gruppe − BTC | **oberes Fünftel − Gruppe** | oberes Fünftel − BTC |
|---|---|---|---|
| Top 30 | −0,9 [−4,8; +3,1] | **+3,5 [+0,7; +7,5]** | +2,6 [−3,0; +9,4] |
| Top 50 | −0,8 [−4,6; +3,4] | +2,0 [−0,6; +5,8] | +1,2 [−3,7; +7,1] |
| Top 100 | −0,3 [−4,8; +5,3] | +1,7 [−0,4; +4,2] | +1,4 [−4,2; +8,1] |
| Gesamt | −0,7 [−5,1; +5,1] | **+1,5 [+0,3; +2,9]** | +0,8 [−4,2; +7,1] |

- **Die Auswahl wirkt auch auf 1 Monat**, am stärksten in den **Top 30**: Das obere Fünftel liegt +3,5 Pp je Monat über seiner Gruppe; das Band schließt die Null aus.
- **Gegen BTC ist in keiner Gruppe etwas belegt.** Alle Bänder schließen die Null ein.

### 7.2 Beschreibend je Epoche (KEIN BEFUND nach der Norm; Pp)

| | 1 M ab 2024 | | | 12 M ab 2024 | | |
|---|---|---|---|---|---|---|
| Gruppe | Gruppe − BTC | F5 − Gruppe | F5 − BTC | Gruppe − BTC | F5 − Gruppe | F5 − BTC |
| **Top 30** | −2,9 | +5,3 | **+2,4** | −43,7 | +33,0 | **−10,7** |
| Top 50 | −3,7 | +4,9 | +1,3 | −55,3 | +21,5 | −33,8 |
| Top 100 | −4,8 | +2,5 | −2,3 | −62,7 | +22,8 | −39,9 |
| H | −1,9 | +4,7 | +2,8 | −31,0 | +24,2 | −6,8 |
| S | −5,7 | −0,3 | −6,0 | −77,0 | +1,7 | −75,3 |
| **Gesamt** | −5,5 | +0,5 | −4,9 | −72,7 | +7,9 | −64,8 |

**Zur Nutzerfrage „Top 100 / Top 50 anders als der Gesamtmarkt?“ (beschreibend):**
- **Ja, und je enger, desto deutlicher.** Ab 2024 verlor der Gesamtmarkt in 12 M −73 Pp gegen BTC, die Top 100 −63, die Top 50 −55, die **Top 30 −44**.
- Die Auswahl wirkt in den großen Gruppen (Top 30 +33 Pp) und **nicht bei den Kleinwerten** (S +1,7).
- **Das obere Fünftel der Top 30 kam nahe an BTC heran** (−11 Pp in 12 M, +2,4 Pp je Monat), das des Gesamtmarkts nicht (−65 Pp).
- Die Masse der Kleinwerte (S) zieht den Gesamtmarkt nach unten; dort hilft keine Auswahl. Das bestätigt deinen Hinweis.

### 7.3 Je Season-Ampel-Stufe (beschreibend, alle Epochen)

- **kalt** (56 von 88 Stichtagen): Altcoins −5 Pp je Monat gegen BTC; auch das obere Fünftel liegt darunter (Top 100 −3,4); oberes Fünftel > BTC nur in 29 %.
- **Season-Klima, Überhitzung, Ende** (6–15 Stichtage, fast nur 2020–21): Altcoins weit über BTC (+10 bis +24 Pp je Monat).
- ⇒ Die Ampel trennt die Lage, in der Altcoins BTC schlagen, von der, in der sie es nicht tun. Für eine Regel sind die Stichtage zu wenige.

### 7.4 Wie sich Krypto verändert hat (Auskunft)

- **BTC-Volatilität** je Jahr: 2017 93 % · 2018 84 % · 2019 70 % · 2020 78 % · 2021 79 % · 2022 65 % · **2023 43 % · 2024 52 % · 2025 42 % · 2026 45 %**. Seit 2023 etwa halb so hoch wie bis 2021.
- **Coins je Stichtag** (Binance-Messbasis): E1 72 → E2 284 → **E3 375**. Fast der ganze Zuwachs liegt in S (20 → 161 → 268), die Top 100 sind voll besetzt.
- In **2021–23** wirkte die Auswahl auch bei S (+36,5 Pp in 12 M), **ab 2024 nicht mehr**. Das ist ein Zeichen des veränderten Markts.

### 7.5 Was A1 für das Ziel heißt (zur Abstimmung)

1. Die **besseren Assets** gibt es **messbar**: Die Auswahl schlägt ihre Gruppe, belastbar auf 1 Monat, am stärksten bei den Top 30.
2. Den **Drift gegen BTC** gleicht sie bisher **nicht belegt** aus. Am nächsten kommt das obere Fünftel der **Top 30**, gerade im heutigen Markt.
3. **Kleinwerte** tragen nichts zur Lösung bei; sie sind der Hauptteil des Drifts.

### 6.6 A2 Fassung 1b — Selbsttest sperrt Fassung 1, Ursache und Lösung VOR dem ersten Blick (25.10.2026)

**Selbsttest Fassung 1** (Referenz, 24 h, 100 Zufallseinteilungen je Coin und Stichtag; `p87_a2_fassung1.txt`):

| | je Handel | je Tag |
|---|---|---|
| Fehlalarm (Soll ≤ 5 %) | 3 % | **6 %** |
| +0,5 Pp erkannt (Soll ≥ 80 %) | 99 % | **65 %** |
| Nullpunkt | −0,021 Pp | **+0,297 Pp** |

⇒ **Nicht bestanden, nicht gemessen;** das echte D ist ungesehen.

**Ursache:** „je Tag“ verglich das Mittel über die Tage **mit** Einstiegen im oberen Fünftel (440 von ~970 Tagen) mit dem Mittel über die Tage der übrigen Einstiege (fast alle Tage). Das sind **verschiedene Markttage**. Daher der Nullpunkt weit über null und das große Rauschen.

**Lösung, Fassung 1b:**
- „je Tag“ wird als **Tagesklammer** gerechnet: nur Tage mit Einstiegen in **beiden** Gruppen; je Tag das Mittel oben minus das Mittel der übrigen; jeder dieser Tage gleich gewichtet.
- Die Bewegung des Tages fällt damit heraus. Das ist die Gewichtung „Tagesklammer“, die im Projekt bereits gilt (Memory: Gewichtung ausweisen).
- „Je Handel“, die Blöcke, der Nullpunkt, die Urteilsstufen und die Kriterien bleiben wie §6.3/§6.5.
- Der Selbsttest läuft in Fassung 1b erneut vor dem ersten Blick.

## 8. Ergebnis Teil A2, 25.10.2026 — TRÄGT NICHT BIS 0,50 Pp (E-144)

Nutzer 25.10.: *„wenn wir bei den top werten einen positiven Effekt sehen u.U. können wir dies auf Assetebene für das bestehende Portfolio nutzen und somit selektiv nur bestimmte Krypto Assets für Regel0 bzw. das System nutzen. warten wir auf die Ergebnisse“*

**Prüfung:**
- **R-R11:** Z1 der Referenz +0,718 % = p83.
- **Selbsttest Fassung 1b bestanden** (§6.6):
  - Nullpunkt −0,021 / +0,008 Pp;
  - Fehlalarm 3 % / 4 %;
  - Erkennung +0,5 Pp 99 % / 83 %.
- **Block** 15 Tage, 65 Blöcke, Autokorrelation −0,02 / 0,00.
- **Gegenprobe** `p87_gegenprobe.py` **3/3** (groupby, Tagestabelle, 30-Tage-Blöcke).

| Einstiege | D je Handel [Band] · Rang | D je Tag (Tagesklammer) [Band] · Rang | Stufe |
|---|---|---|---|
| Referenz 2024–26 | +0,12 Pp [−0,21; +0,53] · 0,75 | +0,03 Pp [−0,36; +0,44] · 0,53 | **TRÄGT NICHT BIS 0,50 Pp** |
| Lauf A 2024–26 | +0,07 Pp [−0,25; +0,44] · 0,67 | +0,29 Pp [−0,18; +0,84] · 0,89 | **TRÄGT NICHT BIS 0,50 Pp** |
| Lauf B 2023 | +0,05 Pp · 0,60 | +0,10 Pp · 0,63 | **KEIN BEFUND** (152 Signaltage = 10 Blöcke) |

⇒ **Ein Zusammenwirken von ≥ 0,5 Pp je 24-h-Einstieg ist ausgeschlossen.** Die Richtung ist überall positiv, aber klein und nicht von Zufall zu trennen.

**Auskunft** (Punktwerte, nicht belegt; Referenz / Lauf A, je Handel):
- 7 T: +0,62 / +0,60 Pp
- **30 T: +2,39 / +2,93 Pp**
- Top 30: +0,66 / +0,80 · H: +0,98 / +0,84
- M: −0,13 / −0,13
- je Jahr: 2024 +0,72 / +1,04 · 2025 −0,14 / −0,26 · 2026 +0,08 / −0,21

Der Unterschied wächst mit dem Horizont, so wie es die langsame Auswahl erwarten lässt (A1, §3).

### 8.1 Ursachen (nicht abbrechen ohne Grund)

1. **Horizont:** Die Auswahl wirkt über Monate (A1: belastbar auf 1 M). Im 24-h-Einstieg ist sie nach §3 rund zehnmal kleiner als messbar. A2 bestätigt das: kein messbarer Unterschied in 24 h, ein wachsender bei 7 und 30 T.
2. **Kein Zusammenwirken:** Der REGEL0-Zeitpunkt ist in guten Coins nicht deutlich besser als in den übrigen (≥ 0,5 Pp ausgeschlossen). Die Auswahl verbessert den **Coin**, nicht den **Zeitpunkt**.
3. **Bestätigung 2023 zu klein:** 152 Signaltage ergeben nach der Norm nur 10 Blöcke. ⚠️ Eigener Planungsfehler: Die Voranalyse prüfte die Auflösung, nicht die 20-Blöcke-Regel für 2023.

### 8.2 Lösungsvorschläge (zur Abstimmung)

| | Lösung | Begründung | offen |
|---|---|---|---|
| **L-1 (Empfehlung)** | **Die Auswahl als Asset-Filter auf Monatsebene**: welche Coins das System führt, kauft und hält (Spot, Bestand), Top 30 bzw. oberes Fünftel. Das ist die Nutzeridee | Die Auswahl wirkt dort, wo sie belegt ist (A1, 1 M, alle Jahre; Top 30 +3,5 Pp/M gegen die Gruppe) | gegen BTC nicht belegt; im heutigen Markt allein KEIN BEFUND (zu wenige Monate) → Voranalyse muss die Prüfbarkeit klären (alle Jahre gemeinsam, E3 als Auskunft; Season-Ampel als Lenkung) |
| L-2 | **REGEL0 nur auf ausgewählte Coins** | schadet nicht (D ≥ 0), bringt aber in 24 h keinen messbaren Vorteil | für den Hebel keine Verbesserung belegt; ein längeres Halten gefilterter Coins wäre eine neue Regel (7/30 T sind schon gesehen; für Hebel kostet Halten 0,3–0,4 %/Tag, E-123) |
| L-3 | 2023 als Bestätigung vergrößern | — | nicht möglich: Die REGEL0 feuert vor 2023 nicht (E-136) |

## 9. A1 mit zeitrichtigem Marktwert-Rang — Bau und Messplan VORAB festgelegt 26.10.2026 (Nutzer: *„2 ja - prüfen gegenprüfen und doku“*, E-153)

**Anlass:** E-151. `mk_messung.umlauf` nimmt vor dem 21.09.2025 die **heutige** Umlaufmenge. Dadurch stehen Tokens mit großen Freigaben historisch zu hoch (ENA 2024-06 Rang 9 statt 61).

### 9.1 Bau in `mk_messung` (Messcode, kein Betrieb)

- **Schalter `RANG_QUELLE`**, Vorgabe **`"cmc"`** (zeitrichtig). `"eigen"` ist der bisherige Rang; er bleibt **nur zum Nachrechnen** alter Befunde (R-R11).
- **Zeitrichtiger Marktwert zu t:**
  - Steht der Coin in der CMC-Woche w ≤ t: MW = CMC-Marktwert(w) × Binance-Schluss(t) ÷ Binance-Schluss(w). Das Skalieren über den Binance-Kurs macht die Rechnung unabhängig von Bündel-Einheiten (1000SATS).
  - Zuordnung über das Symbol; bei Bündeln über den Grundnamen (`hole_umlaufmenge_cg.vervielfacher`).
  - Bei doppeltem Symbol in der Woche gilt der Eintrag, dessen Preis dem Binance-Kurs (in Einzeltoken) am nächsten liegt.
  - Steht der Coin **nicht** in den CMC Top 200 der Woche: eigener Marktwert, aber höchstens knapp unter dem Marktwert von CMC-Rang 200 derselben Woche. Wer nicht in den Top 200 steht, kann nicht über ihnen stehen.
  - Vor der ersten CMC-Woche (2016-07) gilt der eigene Wert. Das betrifft die Messungen ab 2019 nicht.
- **Klassen wie bisher** (H = Rang ≤ 30 an t, t−1M, t−2M und ≥ 730 T; M ≤ 100; S Rest). Es ändert sich nur der Marktwert.
- Betrieb (`agent/spot_abbau`) unberührt: Er rechnet mit der CoinGecko-Historie ab 21.09.2025, die zeitrichtig ist.

### 9.2 Prüfung des Baus (vor der Messung)

| # | Prüfung | Soll |
|---|---|---|
| B1 | `RANG_QUELLE="eigen"` reproduziert A1 (`p86_a1_zerlegung.txt`) **bitgleich** | alle Zeilen gleich |
| B2 | zeitrichtiger Rang gegen den CMC-Altcoin-Rang an den Monatsstichtagen 2019–26 (gemeinsame Coins) | Rangkorrelation im Mittel ≥ 0,95 |
| B3 | Beispiele aus E-151: ENA/TIA 2024-06, WLD 2025-06 | nicht mehr in den Top 30 |
| B4 | **Wirkung auf die Grundgesamtheit** (CLAUDE.md: *wer sie ändert, misst die Wirkung*) | Anteil der Anker mit anderer Klasse H/M/S, je Jahr, nur ausgewiesen |

### 9.3 Messung A1 neu (`p94_a1_zeitrichtig.py`)

- **Derselbe Code wie A1** (`p86`), nur mit `RANG_QUELLE="cmc"`: Horizonte 1 M und 12 M, Gruppen Top 30/50/100, H/M/S, Gesamt, Epochen E2/E3/alle, Band zirkulär mit Norm-Block, < 20 Blöcke KEIN BEFUND, Season-Ampel und Vola als Auskunft.
- **Urteil wie A1:** **belastbar** = Band (1 M, alle) ohne 0. Sonst **NICHT TRENNBAR** bzw. KEIN BEFUND.
- **Gegenprobe:** `p86_gegenprobe` mit `RANG_QUELLE="cmc"` (zweiter Rechenweg A1), gleiche Aussagen.
- **Folge:**
  - Die neuen Zahlen **ersetzen** E-143. Nach R-R11 ist das zulässig: Reproduktion B1 plus ein einziger getauschter Bestandteil.
  - E-142, E-144 und E-145 bekommen einen Vorbehaltsvermerk. Neu gerechnet werden sie erst nach Abstimmung.
