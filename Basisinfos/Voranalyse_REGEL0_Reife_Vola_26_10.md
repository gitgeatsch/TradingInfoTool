# Voranalyse: REGEL0 robust machen (Ansatz 1) und Größe nach Schwankung (Ansatz 2) — 26.10.2026

Nutzer 26.10.: *„beides - prüfen gegenprüfen und doku danach prüfe noch einmal auf recherchebasis welche Möglichkeiten noch bestehen …“*

⚠️ Das ist eine Voranalyse. Es ist **nichts** gegen ein Ergebnis gerechnet. Gezählt wurden nur Einstiege und Tage.

## 1. Ansatz 1 — REGEL0 mit einer Reife, die nicht vom Datenbeginn abhängt

### 1.1 Was die Reife im Code tut (`agent/regel0_rechnung.py:150-170`)

- **Eigenes Normal** (NA/NB, Trefferquote auf/ab): rechnet über ein **rollendes Jahr** (`st − JAHR_H`). Es hängt **nicht** am Datenbeginn.
- **Reife** (`REIF`): Ein Symbol ist reif, wenn seit dem Reihenbeginn `st0` mindestens ein Jahr vergangen ist und mehr als 1.000 Anker vorliegen. Nur reife Anker gehen in die Basis aus Training, Schrumpfung und Signal (`BASIS = … & REIF`).
- ⇒ Der Datenbeginn wirkt **nur über die Reife**, also darüber, **welche Coins in einem Monat überhaupt mitmachen**.

### 1.2 Was E-138/E-139 daraus gemessen haben

- In der Referenz beginnen die Daten von BTC, BNB, SOL, AVAX und XLM erst 2023-09 (Beginn der Terminmarktdaten). Diese Coins waren bis 2024-09 **unreif**, also ausgeschlossen.
- Mit der Historie ab 2019 (**Lauf A**) sind sie reif und machen mit; das Plus verschwindet.
- R2: Die Reife allein bildet den Unterschied zu **99,9 %** nach.
- ⇒ **Lauf A ist bereits die Fassung, deren Reife nicht vom Datenbeginn abhängt**: Jeder Coin ist reif, sobald er ein Jahr bei Binance gehandelt wurde. Auf ihr hat die REGEL0 **keinen belegten Vorsprung**: Z1 je Tag ist negativ (E-139); auf dem Kern 24 h nur +0,09 Pp, Rang 0,65 (E-146).

### 1.3 Die verbleibende Spur: Ballungstage

E-138: Rund **99 %** des Unterschieds liegen an Tagen mit mehr als 20 Signalen. An ruhigen Tagen verlieren beide Fassungen. Zählung seit 2024:

| | Einstiege | Tage | Tage > 20 Signale | Anteil der Einstiege | **getrennte Episoden** (> 7 T Abstand) |
|---|---|---|---|---|---|
| Referenz | 10.732 | 671 | 172 | 70 % | **28** |
| Lauf A | 11.701 | 701 | 192 | 71 % | **27** |

- Ballungstage sind **marktweite Abverkäufe**: Viele Coins geben zugleich ein Signal. Eine Regel „nur an Ballungstagen“ ist deshalb eine **Marktphasen-Regel** mit rund **27–28 unabhängigen Ereignissen**.
- Das ist dieselbe Grenze wie bei L2-a (72 Wechsel in 12 Jahren, Selbsttest nicht bestanden; E-151).

### 1.4 Urteil Ansatz 1

**Fachlich beantwortet, keine Messung.**
- Die naheliegende robuste Fassung ist Lauf A, und sie trägt nicht.
- Die einzige Spur darüber hinaus (Ballungstage) hat zu wenige unabhängige Fälle.
- Eine weitere REGEL0-Fassung auf denselben Daten wäre Mehrfachtesten.

## 2. Ansatz 2 — Positionsgröße nach Schwankung

### 2.1 Was die Literatur sagt (Recherche R-A, 22.10., E-129)

- Volatilitätssteuerung: **außerhalb der Stichprobe keine bessere Rendite** (Cederburg u. a.; Markt 0,42 gegen 0,46 Sharpe), aber **kleinere Ränder**. Einordnung dort: *„Bremse für die Ränder“*.
- ⇒ Erwartung: **Risiko je Handel gleichmäßiger, Rückgang des Kontos kleiner, Rendite etwa gleich.** Einen Vorsprung beim Einstieg schafft sie nicht.

### 2.2 Was im Betrieb heute gilt (`regel0_betrieb.yaml`, `agent/regel0_groesse.py`)

- **Hebelstufe** 2x/3x/5x aus dem **ATR-Modell** (Liquidationsgrenze 2 %): Schwankt ein Coin mehr, bekommt er weniger Hebel.
- **Positionswert fest 1.500 €** je Handel; Einsatz = Positionswert ÷ Hebelstufe, begrenzt auf 300–800 €.
- ⇒ Der Hebel ist schon nach Schwankung gewählt, **die Größe im Markt aber nicht**. Ein Coin mit doppelter ATR trägt bei gleichem Positionswert etwa das **doppelte Euro-Risiko** je Handel.

### 2.3 Machbarkeit (ohne Ergebnis)

| | |
|---|---|
| Daten | REGEL0-Einstiege Referenz 10.732 und Lauf A 11.701 (2024–26), Stundenkurse `data/_hist` für ATR und Ertrag, alles am Desktop |
| Fallzahl | 670–700 Handelstage, Block `messnorm._block(1)` = 15 T ⇒ rund **45 Blöcke** ✔ (Norm ≥ 20). Anders als bei Regimefragen zählen hier die Handel; die Ballung an den Signaltagen fängt die Tagesklammer ab |
| Frage | Gibt ein Positionswert ∝ 1/ATR (gleiches Euro-Risiko je Handel, **gleicher mittlerer Positionswert** wie heute) einen kleineren Konto-Rückgang und ein besseres Verhältnis von Ertrag zu Schwankung als der feste Positionswert, **vor Kosten**? |
| Nullwelt | dieselben Größen, **zufällig über die Handel desselben Tages vertauscht** (Größenverteilung gleich, Bezug zur ATR zerstört) |
| Erwartung | eher **Bremse** (kleinerer Rückgang), Rendite ≈ gleich. Weil REGEL0 keinen belegten Vorsprung hat, hebt die Größe kein Minus auf |

### 2.4 Messplan-Vorschlag V-1 (zur Abstimmung, NICHT festgelegt)

| | |
|---|---|
| Mengen | Referenz und Lauf A, 2024–26, je Handel 24 h (REGEL0-Haltedauer) |
| Arme | **G0** fester Positionswert (heute) · **G1** Positionswert ∝ ATR_Ziel / ATR(Einstiegsstunde), auf den Mittelwert von G0 normiert, gekappt auf [0,5; 2] × 1.500 € |
| Zielgrößen (neutral, vor Kosten) | (i) größter Rückgang des Kontos über die Tagesreihe · (ii) Ertrag je Tag ÷ Schwankung je Tag · (iii) Anteil der Tage mit Verlust ≥ 3 % des mittleren Tageseinsatzes |
| Urteil | **TRÄGT als Bremse**, wenn (i) **und** (ii) gegen die Nullwelt Rang ≥ 0,95 in **beiden** Mengen. Stufen nach Norm; < 20 Blöcke KEIN BEFUND |
| Selbsttest vor dem Blick | Fehlalarm auf 200 Nullwelten ≤ 5 %; Pflanzung: künstlich größerer Verlust bei hoher ATR (Auflösungskurve) |
| Gegenprobe | eigene Kontoschleife je Tag; Band mit doppelter Blocklänge |
| Folge | trägt ⇒ Bauvorschlag: `positionswert_eur` nach ATR in `regel0_groesse` (Schalter, Vorgabe aus) · trägt nicht ⇒ fester Positionswert bleibt |

### 2.5 Kern-Spot (BTC/ETH/SOL)

Eine Volatilitätssteuerung des **Bestands** hieße: in wilden Phasen verkaufen. Das widerspricht deinem Sparplan, kostet Gebühren und ist nach R-A nur eine Bremse. Auf dem Spot schlage ich sie nicht vor.

## 3. Gegenprüfung dieser Voranalyse

- Die Code-Aussagen zur Reife (`regel0_rechnung.py:150-170`) und zur Größe (`regel0_groesse.py:4-7, 167-172`, `regel0_betrieb.yaml:10-17`) sind nachgelesen.
- Die Zählung der Ballungstage beruht auf den Einstiegsdateien `kern48jbz_einstiege_bestand.csv` und `einstiege_A.csv`, gerechnet ab 2024; die Episoden sind über > 7 T Abstand gezählt. Bei einer Schwelle von > 30 Signalen ergeben sich 38 bzw. 30 Episoden, also dasselbe Bild.
- Die Literaturlage ist aus R-A übernommen (dort gegengeprüft: 12 Aussagen an Primärquellen), nicht neu behauptet.

## 4. Messplan V-1 — VORAB festgelegt 26.10.2026 (Nutzer: *„1 ja“*) · `Rechenkern_02_10/p95_v1_groesse_atr.py`

| | Festlegung |
|---|---|
| Mengen | Referenz (`data/_vergleich/kern48jbz_einstiege_bestand.csv`) und Lauf A (`data/_hist/einstiege_A.csv`), Einstiege ab 2024-01-01 mit vollständigem 24-h-Fenster |
| Ertrag je Handel | r = Schluss(t + 24 h) ÷ Schluss(t) − 1 aus den Stundenkursen `data/_hist` (Spot), **vor Kosten**, auf den Positionswert. Liquidation nicht modelliert: Die Hebelstufe hält P(Liquidation) ≤ 2 % in beiden Armen gleich |
| ATR | `regel0_rechnung.E2._atr` (Betriebsformel) in der Einstiegsstunde |
| **G0** | Gewicht 1 je Handel (fester Positionswert, heute) |
| **G1** | Gewicht = c ÷ ATR, mit c = Median der ATR aller Einstiege der **vorigen 90 T** (kausal), gekappt auf [0,5; 2]; danach **ein** fester Faktor, sodass die Summe der Gewichte der von G0 gleicht (gleiches Gesamt-Engagement) |
| Konto | Tagessumme P_d = Σ Gewicht × r über die Einstiege des Tages; Konto = laufende Summe (ohne Zinseszins) |
| Zielgrößen | (i) **größter Rückgang** des Kontos · (ii) **Mittel ÷ Schwankung** von P_d (Tage mit Einstieg) · Auskunft (iii) Anteil der Tage mit P_d ≤ −3 % des mittleren Tagesengagements, je Jahr |
| **Nullwelt** | die G1-Gewichte **innerhalb desselben Kalendermonats** zufällig über die Handel vertauscht (Verteilung und Monatsengagement gleich, Bezug zur ATR zerstört), 1.000 Ziehungen; Rang (i) = Anteil Nullwelten mit größerem Rückgang, Rang (ii) = Anteil mit kleinerem Verhältnis |
| Band | zirkulärer Tagesblock-Bootstrap, Block `messnorm._block(1)` = 15 T, für die Differenz (ii) G1 − G0; < 20 Blöcke KEIN BEFUND |
| **Urteil** | **TRÄGT als Bremse**, wenn Rang (i) **und** Rang (ii) ≥ 0,95 in **beiden** Mengen · TRÄGT NICHT, wenn eines ≤ 0,05 (Größe nach ATR schadet) · sonst NICHT TRENNBAR |
| **Selbsttest vor dem ersten Blick** | Fehlalarm: 200 Mal wird statt G1 eine Nullwelt-Ziehung getestet ⇒ Anteil „TRÄGT“ ≤ 5 %. Pflanzung: r′ = r + λ · ATR · z (z standardnormal, je Handel); G1 muss bei λ = 0,5 / 1 / 2 als Bremse erkannt werden, Soll ≥ 80 % bei λ = 1. Echte Kennzahlen werden erst nach bestandenem Selbsttest ausgegeben |
| Gegenprobe | P_d, Rückgang und Verhältnis über eine eigene Schleife je Handel (gleich ± 1e-9); Band mit doppelter Blocklänge, gleiche Aussage |
| Folge | trägt ⇒ Bauvorschlag `positionswert_eur` nach ATR in `regel0_groesse` (Schalter, Vorgabe aus, Kappung wie gemessen) · nicht trennbar / trägt nicht ⇒ fester Positionswert bleibt |

### 4.1 Selbsttest Fassung 1 NICHT BESTANDEN — Ursache und Fassung 1b, VOR dem ersten Blick (26.10.2026)

| | Fehlalarm | Fund λ 0,5 / 1 / 2 |
|---|---|---|
| Referenz (10.728 Handel, 45 Blöcke) | 0,5 % ✔ | 11 / **22** / 29 % ✖ |
| Lauf A (11.696 Handel, 47 Blöcke) | 1,0 % ✔ | 0 / **2** / 6 % ✖ |

**Ursache (eigener Planungsfehler):** Die Pflanzung r′ = r + λ · ATR · z zog z **unabhängig je Handel**. Bei rund 16 Handeln je Tag mittelt sich dieses Rauschen in der Tagessumme weg; Rückgang und Tagesschwankung werden von **gemeinsamen** Marktbewegungen bestimmt. Der Mechanismus, den eine Größe nach ATR ausnutzt, ist ein anderer: Coins mit hoher ATR bewegen sich bei einem Marktschock **stärker**.

**Fassung 1b (vorab, sonst unverändert):**
- Pflanzung r′ = r + λ · ATR · m_d, mit **einem** standardnormalen Schock m_d je Tag für alle Handel des Tages; λ = 0,5 / 1 / 2.
- Soll ≥ 80 % bei λ = 1; Fehlalarm wie gehabt.
