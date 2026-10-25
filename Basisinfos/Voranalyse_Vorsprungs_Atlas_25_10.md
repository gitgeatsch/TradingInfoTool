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
