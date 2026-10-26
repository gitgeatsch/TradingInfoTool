# Voranalyse L-1 (Asset-Filter auf Monatsebene) und L-2 (Hebel: RegelXY mit anderer Haltedauer) (25.10.2026)

**Wozu:** Nutzer 25.10.: *„ja L-1 Voranalyse starten, prüfen gegenprüfen und doku - auch L-2 wir brauchen auch für Hebel eine Lösung, diese kann nicht wie spot sein, auch auf mein bestehendes Portfolio prüfen und eine andere Haltedauer prüfen, was eine neue RegelXY wäre und ggf. für bestimmte Assets geeignet?“*

**Herkunft:**
- E-143 (A1: Die Auswahl schlägt ihre Gruppe, am stärksten bei den Top 30);
- E-144 (A2: Die Auswahl verbessert den Coin, nicht den 24-h-Zeitpunkt).

Hier wird **nicht** gemessen, ob eine neue Regel trägt; das machen die Messpläne (§5, §6) nach Ja. Werkzeuge: `p88_l1_l2_voranalyse.py`, Gegenprobe `p88_gegenprobe.py` **3/3**, Ausgaben jeweils als `.txt`.

## 1. Vorwissen

| Thema | Befund | Quelle |
|---|---|---|
| Auswahl auf 1 M (alle Jahre) | oberes Fünftel − Gruppe: Top 30 +3,5 Pp/M [+0,7; +7,5], Gesamt +1,5 [+0,3; +2,9]; **gegen BTC nichts belegt** | E-143 |
| Auswahl × 24-h-Einstieg | trägt nicht bis 0,50 Pp; 30 T Auskunft +2,4/+2,9 Pp | E-144 |
| **Haltedauer beim Hebel** (alle Assets, 2025–26) | jeder weitere Tag netto −0,3 bis −0,4 %; H72–H168 in allen vier Mengen unter null; **2024 umgekehrt** (Aufwärtsjahr); Liquidationsnähe binnen 7 T etwa ×20–25 | Schritt7 §23.68 |
| BTC in der REGEL0 | ~30 Signale je Jahr, nicht nachweisbar, unschädlich | E-37 |
| Kosten Bitpanda-Hebel | 0,30 % Schließen + 0,18 % je Tag Finanzierung | §23.68, E-128 |
| Spot-Kosten Fusion | 0,25 % je Seite | E-126/E-128 |

## 2. Dein Bestand gegen die Filter (L1-a; Bestand laut NB-Diagnose vom 15.10., Stichtag 01.09.2026)

| Gruppe | Werte |
|---|---|
| **Kern** (nicht in der Watchlist-Ordnung) | BTC, ETH, SOL |
| **in den Top 30** (10) | ALGO (Fünftel 4), AVAX (4), BNB (2), HBAR (3), LINK (4), NEAR (3), QNT (2), **SUI (1)**, **TAO (1)**, XLM (4) |
| außerhalb der Top 30 (7) | BEAMX (2), BIO (2), INJ (3), **KAIA (1)**, SEI (2), **TURBO (1)**, W (3) |
| nicht in der Binance-Spot-Messbasis (11) | ASTER, BRETT, CANTON, CAT, HYPE, KAS, MON, MORPHO, PLUME, SUPRA, XDC — ihr Fünftel rechnet nur B4 am Notebook (`spot_betrieb.db`); ⇒ **offener Punkt fürs nächste NB-Bündel** |

- **Keiner** deiner Werte liegt im **oberen Fünftel**. Auch keiner liegt in „Top 30 & oberes Fünftel“.
- Vier liegen im **unteren Fünftel** (SUI, TAO, KAIA, TURBO), also dort, wo B4 „zuerst abbauen“ meldet.
- ⚠️ Das ist ein **Fakt** nach der Regel, keine Empfehlung. Ob das obere Fünftel BTC schlägt, ist nicht belegt (§1).

## 3. Machbarkeit und Auflösung L-1 (L1-b/c, Norm: Block max(15 T, 3 × H), ≥ 20 Blöcke)

| Filter | Coins je Stichtag | Wechsel/Monat (Gebühr) | 7 T ab 2024: MDE gg. Gruppe / gg. BTC | 30 T alle Jahre: MDE gg. Gruppe / gg. BTC |
|---|---|---|---|---|
| Top 30 | 30 | 7–8 % (0,04 %) | – / 2,5 Pp | – / 5,3 Pp |
| oberes Fünftel | 76 | 8–14 % (0,04–0,07 %) | 0,8 / 2,0 Pp | 1,6 / 7,4 Pp |
| **Top 30 & oberes Fünftel** | **5** | 14–19 % (0,07–0,10 %) | 1,5 / 2,9 Pp | 4,5 / 7,5 Pp |
| H & oberes Fünftel | 5 | 13–17 % (0,06–0,09 %) | 1,3 / 2,9 Pp | 5,2 / 8,0 Pp |

- **Gebühren sind kein Hindernis:** Der Monatswechsel kostet 0,04–0,10 % je Monat.
- **Nach der Norm** ist **30 T ab 2024** in allen Filtern **KEIN BEFUND** (10 Blöcke). **7 T** ist auch ab 2024 messbar (32 Blöcke).
- **Gegen BTC** liegt die Auflösung bei 2–3 Pp je Woche bzw. 5–8 Pp je Monat. Das ist nur für große Effekte erreichbar.

## 4. Machbarkeit und Auflösung L-2 (L2-a/b; Hebel, REGEL0-Einstiege 2024–26)

| Haltedauer | 24 h | 72 h | 7 T | 30 T |
|---|---|---|---|---|
| Kosten Bitpanda-Hebel | 0,48 % | 0,84 % | 1,56 % | 5,70 % |

| Asset-Gruppe (Referenz) | Einstiege / Tage | MDE Vorsprung 24 h | MDE 7 T | 30 T |
|---|---|---|---|---|
| BTC | 95 / 95 | 0,71 Pp | 1,54 Pp | KEIN BEFUND |
| ETH | 91 / 91 | 1,00 | 2,47 | KEIN BEFUND |
| SOL | 90 / 90 | 0,90 | 2,79 | KEIN BEFUND |
| **Kern BTC/ETH/SOL** | **276 / 192** | **0,62** | **1,94** | KEIN BEFUND |
| Top 30 & oberes Fünftel | 116 / 98 | 2,44 | 7,95 | KEIN BEFUND |
| Top 30 | 1.466 / 434 | 0,60 | 2,20 | KEIN BEFUND |
| alle | 10.732 / 671 | 0,49 | 2,20 | KEIN BEFUND |

(Lauf A ähnlich: Kern 315 Einstiege, MDE 0,51 / 1,93 Pp.)

- **Season-Ampel 2024-01 bis 2026-06: zu 100 % „kalt“.** Eine Hebelregel, die nach Regime unterscheidet, lässt sich auf 2024–26 nicht prüfen.
- **Für den Hebel geeignet und messbar ist nur der Kern.** Die Top-30-Auswahl hat zu wenige Einstiege (MDE 2,4 bzw. 8 Pp).
- **Was eine RegelXY „Kern länger halten“ bräuchte:** Bei 7 T kostet der Hebel 1,56 %, die Auflösung liegt bei rund 1,9 Pp. Nachweisbar netto positiv wäre die Regel erst ab etwa **+3,5 % brutto je 7-T-Handel**.

## 5. Messplan L-1 Fassung 1 — Vorschlag (festgelegt in §8)

- **Regel L-1:** Altcoins nur aus den **Top 30 nach Marktwert, im oberen Fünftel des Werts** (B4-Wert ohne F9), monatlich neu.
- **Vergleiche:** (a) gegen die Top 30 gesamt (Auswahl); (b) **gegen BTC** (Drift-Ausgleich, dein Ziel).
- **Bestätigung auf unberührten Daten:** **CMC-Wochen 2017-01 bis 2019-06** (`o47_cm.db`, Top 200 je Woche mit eingestellten Coins).
  - Der Wert wird aus den Kursen nachgebaut (Tiefe unter dem Hoch, Tage seit dem Hoch, Alter seit dem ersten Erscheinen); der Rang ist der echte CMC-Marktwert.
  - Horizont **7 T, Wochen-Stichtage** (rund 130 Wochen, Block 3 Wochen, über 40 Blöcke).
- **Brücke (R-R11) zuerst:** Auf 2019–2026 muss der nachgebaute CMC-Wert die Binance-Ordnung tragen (Rangkorrelation je Stichtag ≥ 0,8 im Mittel). ⚠️ Bei O47 ist eine solche Brücke schon einmal gescheitert (Binance-Universum junger Listings). Scheitert sie hier, gibt es keine Bestätigung; dann folgen Ursache und Lösung.
- **Selbsttest vor dem ersten Blick:** Zufallskörbe gleicher Größe aus derselben Gruppe; Fehlalarm ≤ 5 %; gepflanzt +0,5 Pp je Woche erkannt ≥ 80 %.
- **Urteil in den Stufen der Norm**, je (a) und (b), je Handel (Korb gleich gewichtet).
- **Auskunft:** 2019–2026 (gesehen) und dein Bestand als Fakt.

## 6. Messplan L-2 Fassung 1 (RegelXY Hebel) — Vorschlag (festgelegt in §8)

- **RegelXY:** REGEL0-Signal **nur auf BTC, ETH, SOL** (Kern), Haltedauer **72 h bzw. 168 h** statt 24 h, Bitpanda-Kosten.
- **Hauptgröße:** **netto je Handel** (Hebel long verdient absolut, die Drift zählt mit), je Handel und je Tag.
- **Daneben:** der Vorsprung gegen Zufallsstunden derselben Kern-Coins an denselben Tagen; er zeigt den Signalwert.
- **Einstiege:** Referenz und Lauf A 2024–26. Bestätigung 2023 (Lauf B, etwa 78 Kern-Einstiege), voraussichtlich KEIN BEFUND; das wird vorab so benannt.
- **Selbsttest:** Zufallsstunden der Kern-Coins an denselben Tagen; Fehlalarm ≤ 5 %; gepflanzt +1,0 Pp erkannt ≥ 80 %.
- **Norm:** Block max(15 T, 3 × H) = 15 bzw. 21 Tage; ≥ 20 Blöcke; Urteilsstufen.
- **Ehrlich:**
  - §23.68 hat längeres Halten über **alle** Assets 2025–26 schon gemessen, mit negativem Ergebnis. Der Kern-Schnitt ist neu, aber es sind dieselben Jahre.
  - 2024 (Aufwärtsjahr) war umgekehrt, und das Regime ist vorab nicht erkennbar.
  - Die Liquidationsnähe steigt bei längerem Halten; sie wird je Stufe ausgewiesen.

## 7. Zur Abstimmung

1. **L-1** so messen (CMC-Holdout 2017–19 mit Brücke)?
2. **L-2** so messen (Kern, 72/168 h)?
3. Die B4-Fünftel deiner elf Werte außerhalb von Binance kommen ins nächste NB-Bündel (Export `abbau_universum`)?

## 8. Messpläne L-1 und L-2 — VORAB FESTGELEGT 25.10.2026

Nutzer 25.10.:
- *„Messplan L1 und L2 zur Prüfung ok“*
- *„auch Werte welche nicht auf Binance sind sollten enthalten sein“*
- *„vorsicht - btc und eth und sol sollen auch regel0 und hebel nutzen können!!!“*

### 8.0 Feste Regel für beide Pläne: Der Kern ist immer zugelassen

**BTC, ETH und SOL sind für REGEL0, Hebel und Spot immer zugelassen.** Kein Filter aus L-1 schließt sie aus. Die Fünftel-Ordnung vergleicht nur die Altcoins (Rolle L), weil der Kern seine eigene Regel hat:
- Spot: Aufbau 70/20/10 (E-68/E-69);
- REGEL0: Geltungsbereich alle Binance-Assets, BTC ausdrücklich (E-37).

L-2 prüft den Hebel gerade **für** den Kern.

### 8.1 L-1 (Asset-Filter für die Altcoins, Rolle L) — `p89_l1_cmc.py`

- **Daten:** `data/_spot/o47_cm.db`, Tabelle `cmc_woche` (CMC Top 200 je Woche, mit eingestellten Coins, **auch Coins außerhalb von Binance**). Universum je Woche: alle Coins außer BTC, ETH, SOL, `spot_abbau.SONDER` und Stablecoins (Median |Wochenrendite| < 1 % über die vorhandene Historie).
- **Klasse:** CMC-Rang unter den Altcoins der Woche, H ≤ 30, M ≤ 100, S Rest.
- **Wert nachgebaut** wie `as_messung.merkmale` / `wl_messung.wert` ohne F9:
  - F1 = Preis ÷ bisheriges Hoch − 1 (tiefer besser);
  - F2 = Tage seit dem Hoch (länger besser);
  - F8 = Tage seit dem ersten Erscheinen in `cmc_woche` (älter besser).
  - F1 und F2 erst ab 26 Wochen (≈ 180 T) Beobachtung.
  - Wert = Mittel der Perzentile in der Zelle (Woche × Klasse), Zelle ab 10 Coins. Oberes Fünftel = Perzentil > 0,8.
- **Teil 1 Brücke (R-R11, zuerst und zur Abstimmung vorgelegt):**
  - An den Monatsstichtagen 2019-01 bis 2026-09: der CMC-Wert gegen den Binance-Wert (`p85.wert_tabelle(1)`), Coins in beiden, je Stichtag und Klasse.
  - Kriterium: Rangkorrelation im Mittel ≥ 0,8 **und** Anteil gleicher Coins im oberen Fünftel ≥ 50 %.
  - Hält die Brücke nicht, folgen Ursache und Lösung, keine Messung.
- **Teil 2 Bestätigung auf unberührten Daten** (erst nach der Abstimmung über Teil 1):
  - Wochen 2017-01 bis 2019-06; Ertrag über die nächste Woche (7 T) aus `preis`.
  - **Coin fällt aus den Top 200:** Sein Ertrag wird nach oben begrenzt durch (Marktwert des Rangs 200 in der Folgewoche ÷ eigener Marktwert) − 1. Ausgewiesen werden der Anteil und zum Vergleich die Rechnung ohne diese Coins.
  - **Filter:** Top 30 & oberes Fünftel.
  - **Vergleiche:** (a) gegen Top 30 gesamt; (b) gegen BTC (`cmc_woche`).
  - **Norm:**
    - Block max(15 T, 3 × 7 T) = 21 T = 3 Wochen, ≥ 20 Blöcke;
    - Bezug Nullpunkt = Mittel von 200 Zufallskörben gleicher Größe aus den Top 30;
    - Urteilsstufen TRÄGT / TRÄGT NICHT BIS X / NICHT TRENNBAR / KEIN BEFUND.
  - **Selbsttest vor dem ersten Blick:** Fehlalarm ≤ 5 %; gepflanzt +0,5 Pp je Woche erkannt ≥ 80 %.
  - **Auskunft:**
    - 2019–2026 (gesehen);
    - **Zombie-Prüfpunkt:** Mitglieder des Filters, die später aus den Top 200 fallen;
    - Klasse M & oberes Fünftel.

### 8.2 L-2 (RegelXY Hebel: Kern länger halten) — `p90_l2_kern_halten.py`

- **Einstiege:** REGEL0 auf **BTC, ETH, SOL**, Referenz und Lauf A 2024-01 bis 2026-08. Auskunft: Lauf B 2023.
- **Haltedauer** H = 24 h (heute), 72 h, 168 h. **Netto** = Schluss(t + H) ÷ Schluss(t) − 1 − (0,30 % + 0,18 % × H/24 h).
- **Größen:**
  - (i) netto je Handel und je Tag (Tagesmittel, jeder Tag gleich);
  - (ii) Vorsprung gegen Zufallsstunden derselben Coins im selben Jahr (Signalwert, wie Z1, über H);
  - (iii) Auskunft: gepaart netto(H) − netto(24 h).
- **TRÄGT (Hebel) nur, wenn** das Band von (i) über **0** liegt **und** das Band von (ii) über dem Nullpunkt, je Handel und je Tag, auf beiden Einstiegswegen.
- **Norm:** Block max(15 T, 3 × H) = 15 / 15 / 21 T, ≥ 20 Blöcke, Autokorrelation ≤ 0,15, Urteilsstufen.
- **Selbsttest vor dem ersten Blick:** 100 Zufallsmengen (Zufallsstunden der Kern-Coins, gleiche Zahl je Coin und Jahr); Fehlalarm ≤ 5 %; gepflanzt +1,0 Pp erkannt ≥ 80 %, je H.
- **Auskunft:** Liquidationsnähe je Stufe (Tief binnen H ≤ −50 % / −33 % / −20 % für 2× / 3× / 5×), je Coin, je Jahr.
- **Ehrlich (vorab):** §23.68 hat längeres Halten über alle Assets 2025–26 schon negativ gemessen; der Kern-Schnitt ist neu, aber es sind dieselben Jahre. Die Season-Ampel stand 2024–26 durchweg auf „kalt“.

### 8.3 Werte außerhalb von Binance im Bestand

Die **Notebook-Diagnose** bekommt einen Abschnitt `spot_b4_fuenftel`. Er gibt das B4-Fünftel **aller** Bestände aus, auch der Coins außerhalb von Binance, nur lesend aus `spot_betrieb.db`. Er wirkt mit dem nächsten NB-Pull (Kontrolle K-B4-D1).

### 8.4 Welche Regel heute für den Kern gilt (Nutzer 25.10.: *„es sind kernwerte und wenn dann fallen diese aus der normalen spot regel raus nur diese ist bisher noch nicht zustande gekommen, prüfe welche Regel für kern zählt“*)

| | Inhalt | Stand im Betrieb |
|---|---|---|
| **Beschlossene Kern-Regel** (E-68, E-69, Spot §12.6/§12.10/§12.11) | Aufbau **70/20/10** BTC/ETH/SOL, monatlich gleicher Betrag, **Ausgleich über die Raten** (ohne Verkauf); **Klima-Ampel** mit Hinweis **K1** (q war über 0,90, fällt unter 0,85/0,75/0,65 → Teilverkauf je ein Zehntel erwägen) und **Rückkauf** (q ≤ 0,20/0,10/0,05, je ein Drittel; Rest nach 12 Monaten). Kein Auslöser, du entscheidest | ⛔ **nicht gebaut**: „gebaut wird mit dem Spot-Betrieb (S7, O27)“; O27 Punkt 2 (Fakt-Mail Bestand und Klima) steht auf „Abstimmung“. Es gibt keinen Code für Klima-Ampel q, Aufbau oder K1 |
| B1 Mitnahme, B4 Abbau | schließen den Kern **aus** (`spot_mitnahme.KERN`) | gebaut |
| REGEL0 / Hebel | Kern **eingeschlossen** (E-37) | läuft |

⇒ **Offener Punkt (nach L-1/L-2 zur Abstimmung):** Bau-Voranalyse der Kern-Regel nach §12.11. Gemessen und beschlossen ist sie; es fehlt nur der Bau.

### 8.5 L-2 Fassung 1b — Selbsttest sperrt Fassung 1, Ursache und Lösung VOR dem ersten Blick (25.10.2026)

**Selbsttest Fassung 1** (`p90_l2_fassung1.txt`):

| H | Fehlalarm (je Handel / je Tag) | +1,0 Pp erkannt (je Handel / je Tag) |
|---|---|---|
| 24 h | 4 % / 3 % | 100 % / 100 % |
| 72 h | 1 % / 2 % | **77 % / 81 %** |
| 168 h | 1 % / 1 % | **29 % / 27 %** |

⇒ **Nicht bestanden, nicht gemessen;** das echte Ergebnis ist ungesehen.

**Ursache:** Der Fehlalarm ist niedrig, also arbeitet die Anlage richtig. Aber die **Auflösung** reicht bei längerem Halten nicht für 1 Pp (Voranalyse §4: MDE 7 T ≈ 1,9 Pp). Das feste Kriterium „+1,0 Pp für jedes H“ war ein **eigener Planungsfehler**.

**Lösung, Fassung 1b** (wie die stehende Regel „Pflanzung als Auflösungskurve“):
- Gepflanzt wird 0,5 / 1 / 2 / 3 Pp je H.
- Die Grenze X ist die kleinste Stärke, die zu ≥ 80 % erkannt wird (je Gewichtung).
- Bestanden heißt: Fehlalarm ≤ 5 % und ein X existiert.
- Ein Nicht-Tragen heißt „TRÄGT NICHT BIS X“ je H. Alles Übrige wie §8.2.

## 9. Teilergebnisse 25.10.2026 (E-146)

### 9.1 L-1 Teil 1: Die Brücke hält nicht; Ursache ist die Datenlänge (`p89_l1_cmc.py --bruecke`, `p89b_bruecke_ursache.py`)

| | Ergebnis | Soll |
|---|---|---|
| Rangkorrelation CMC-Wert gegen Binance-Wert (232 Zellen, 114 gemeinsame Coins je Stichtag) | Mittel **0,679**, Median 0,764 | ≥ 0,8 |
| oberes Fünftel Binance auch oberes Fünftel CMC | **55 %** | ≥ 50 % |
| je Jahr | 2019 0,29 · 2020 0,28 · 2021 0,49 · 2022 0,69 · 2023 0,74 · **2024 0,80 · 2025 0,84 · 2026 0,81** | |

**Ursache je Merkmal** (Rangkorrelation CMC gegen Binance):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|
| F1 Tiefe unter dem Hoch | 0,60 | 0,42 | 0,63 | 0,81 | 0,82 | 0,86 | 0,89 | 0,88 |
| F2 Tage seit dem Hoch | 0,36 | 0,34 | 0,44 | 0,71 | 0,77 | 0,78 | 0,80 | 0,81 |
| F8 Alter | 0,42 | 0,40 | 0,57 | 0,66 | 0,74 | 0,84 | 0,89 | 0,88 |

- **Alle drei Merkmale** weichen früh ab und laufen ab 2022–24 zusammen.
- Hoch, Tage seit dem Hoch und Alter hängen davon ab, **seit wann eine Quelle den Coin beobachtet**:
  - Binance ab dem Listing (2017 und später);
  - CMC ab 2016-07, und nur solange der Coin in den Top 200 ist; F8 ist 2019 zu 19 % an 2016-07 zensiert.
- ⚠️ Das betrifft auch den **Binance-Wert der frühen Jahre** selbst; er war 2019–2021 „jung“.

**Lösungsvorschläge (zur Abstimmung):**

| | Lösung | Aufwand | offen |
|---|---|---|---|
| **L1-a (Empfehlung)** | **Brücke Fassung 2 „gleiche Historie“**: nur Coins, die in beiden Quellen ≥ 2 Jahre Kursgeschichte haben. Hält sie dort (≥ 0,8), liegt die Abweichung allein an der Datenlänge, und der CMC-Wert ist bei genug Historie dieselbe Regel | 1 h | Der Holdout 2017–19 hat selbst kurze Historien (CMC ab 2016-07) |
| L1-b | **Langhistorie aus CoinMetrics** (`coinmetrics.db`, Kurse ab 2010 für die erfassten Coins): F1/F2/F8 mit voller Geschichte, Holdout 2017–19 auf diesen Coins | ½ Tag | CoinMetrics Community ist überlebensverzerrt (O47: 17–30 von 50) |
| L1-c | **Ohne Holdout entscheiden:** gegen die Gruppe ist L-1 auf 2019–2026 belastbar (A1, 1 M); gegen BTC nur vorwärts | — | „gesehen“, keine unabhängige Bestätigung |

### 9.2 L-2 RegelXY (Kern länger halten): TRÄGT NICHT 2024–26; 2023 deutlich positiv, aber KEIN BEFUND (`p90_l2_kern_halten.py`)

**Selbsttest Fassung 1b bestanden:**
- Fehlalarm 0–5 %;
- Grenze X: **1,0 Pp** (24 h), **2,0 Pp** (72 h, 168 h).

**Gegenprobe** `p90_gegenprobe.py` **3/3** (Einzelschleife SQL, gepaart über merge, doppelte Blocklänge).

| Kern BTC/ETH/SOL | 24 h netto | 72 h netto | 168 h netto | Stufe |
|---|---|---|---|---|
| Referenz 2024–26 (276) | +0,06 % [−0,40; +0,55] | −0,40 % [−1,21; +0,56] | −0,41 % [−1,86; +1,17] | TRÄGT NICHT BIS 1,0 / 2,0 / 2,0 Pp |
| Lauf A 2024–26 (315) | −0,32 % | **−0,94 % [−1,70; −0,11]** | −0,64 % | TRÄGT NICHT BIS 1,0 / 2,0 / 2,0 Pp |
| **2023 (78, Aufwärtsjahr)** | +0,38 % | **+1,52 %** | **+3,98 %** | **KEIN BEFUND** (7–10 Blöcke) |

**Auskunft:**
- **gepaart** gegen 24 h (2024–26): 72 h −0,46 / −0,62 Pp, 168 h −0,47 / −0,32 Pp.
- **je Jahr** 168 h, Referenz: 2024 +1,25 · 2025 −0,56 · 2026 −1,84 %.
- **je Coin** 168 h, Referenz: BTC +0,11 · ETH −0,07 · SOL −1,30 %.
- **Liquidationsnähe** 5× binnen 168 h: 4,3–4,4 % der Einstiege; bei 2× null.
- **Vorsprung gegen Zufallsstunden:** Kern 24 h Referenz +0,48 Pp je Handel (Rang 0,98), je Tag +0,25 (Rang 0,83). Nicht beide, also nicht tragend; Lauf A +0,09.

**Einordnung:**
- **Länger halten auf dem Kern trägt im Markt 2024–26 nicht.** Es kostet gegenüber 24 h 0,3–0,6 Pp; das bestätigt §23.68 für den Kern.
- **In Aufwärtsphasen (2023, 2024) war es deutlich positiv.** Das Vorzeichen hängt am **Regime**, wie in §23.68.

**Lösungsvorschläge Hebel (zur Abstimmung):**

| | Lösung | offen |
|---|---|---|
| **L2-a (Empfehlung)** | **Regime-Hebel auf dem Kern:** Kern long, Haltedauer 7 T, **nur in einem vorab messbaren Aufwärtsregime**. Prüfung auf **langer Kern-Historie 2019–2026** (Stundenkurse ab 2019 liegen vor), unabhängig von REGEL0-Signalen, mit der Season-Ampel und einem einfachen Trendmaß als Regime | Der Regime-Zeitpunkt war bisher **nicht vorab erkennbar** (W3, M-A, E-126). Dort muss sich zeigen, ob ein Regime-Maß die 7-T-Haltedauer trägt |
| L2-b | REGEL0 auf dem Kern bleibt 24 h (heute), nur Fakt-Zeilen | kein Ertrag belegt (netto ≈ 0) |
| L2-c | Kraken statt Bitpanda (geringere Kosten) | nicht steuereinfach (E-130) |

### 9.3 Berichtigung: L-2 neutral bewertet, Gebühren nachgelagert (Nutzer 25.10.)

Nutzer 25.10.: *„die Einstiege und Bewertung soll vorerst neutral erfolgen, ob ein Trade sich lohnt und wie sich die Gebühren auswirken ist nachgelagert zu bewerten“*.

⚠️ **Eigener Fehler:** Der Messplan §8.2 machte **netto nach Bitpanda-Kosten** zur Hauptgröße (i). Das widerspricht der stehenden Regel 2 (*Gebühren gehören nicht in die Bewertung*) und der Vorgabe vom 25.10. (*Vorsprung unabhängig von den Kosten*).

**Neutrale Bewertung derselben Läufe** (ohne Kosten; Ertrag vor Kosten = netto + Kosten aus §9.2; Vorsprung = (ii), schon ohne Kosten gerechnet):

| Kern BTC/ETH/SOL | | 24 h | 72 h | 168 h |
|---|---|---|---|---|
| Referenz 2024–26 | Ertrag vor Kosten je Handel | +0,54 % | +0,44 % | +1,15 % |
| | **Vorsprung gegen Zufallsstunden** je Handel / je Tag (Rang) | +0,48 / +0,25 Pp (0,98 / 0,83) | +0,24 / +0,09 (0,73 / 0,59) | +0,70 / +0,43 (0,83 / 0,71) |
| Lauf A 2024–26 | Ertrag vor Kosten | +0,16 % | −0,10 % | +0,92 % |
| | **Vorsprung** je Handel / je Tag (Rang) | +0,09 / +0,05 (0,65 / 0,57) | −0,32 / −0,17 (0,26 / 0,37) | +0,43 / +0,26 (0,71 / 0,59) |
| 2023 | Ertrag vor Kosten | +0,86 % | +2,36 % | +5,54 % (KEIN BEFUND) |

**Neutrales Urteil:**
- Der Vorsprung des REGEL0-Einstiegs auf dem Kern ist bei keiner Haltedauer belegt, weder je Handel **und** je Tag noch auf beiden Einstiegswegen.
- Stufen: **TRÄGT NICHT BIS 1,0 Pp (24 h) / 2,0 Pp (72 h, 168 h)**.
- Längeres Halten hebt den Ertrag vor Kosten nur in Aufwärtsphasen (2023, 2024). Das ist die **Drift des Marktes**, kein Vorsprung des Einstiegs.
- Die Kosten sind ein späterer Schritt und hier nicht Teil des Urteils.

**Ab sofort für alle Pläne:** Hauptgröße ist der Vorsprung bzw. der Ertrag **vor** Kosten. Gebühren werden erst geprüft, wenn ein Vorsprung belegt ist.

### 9.4 L1-a vorab festgelegt: Brücke Fassung 2 „gleiche Historie“ (25.10.2026; Nutzer: *„ja L1-a“*)

- Wie Teil 1 (§8.1), aber je Stichtag **nur Coins mit ≥ 2 Jahren (730 T) Kursgeschichte in beiden Quellen**: im Binance-Alter F8 ≥ 730 T **und** CMC-Tage seit dem ersten Erscheinen ≥ 730 T.
- Verglichen wird die Rangfolge des Werts unter diesen Coins je Stichtag und Klasse (Zellen ≥ 10 Coins).
- **Kriterium wie Teil 1:** Rangkorrelation im Mittel ≥ 0,8 **und** ≥ 50 % gleiche Coins im oberen Fünftel. Dazu der Ausweis je Jahr.
- **Hält sie:** Die Abweichung in Teil 1 lag an der Datenlänge. Der CMC-Wert ist bei genug Historie dieselbe Regel, und die Bestätigung 2017–19 wird auf Coins mit ausreichender CMC-Historie vorgeschlagen; dann ist die Zahl der Blöcke zu prüfen.
- **Hält sie nicht:** Es gibt einen Unterschied über die Datenlänge hinaus. Dann folgen Ursache und Lösung.

### 9.5 L1-a Ergebnis: Die Brücke hält auch bei gleicher Historie nicht (`p89c_bruecke_gleiche_historie.py`, Ursache `p89d_bruecke_ursache_gleiche_historie.py`)

| | Fassung 1 (§9.1) | **Fassung 2 (≥ 730 T in beiden Quellen)** | Soll |
|---|---|---|---|
| Rangkorrelation im Mittel | 0,68 | **0,705** (Median 0,761, 10. Perz. 0,49) | ≥ 0,8 |
| oberes Fünftel gleich | 55 % | **51 %** | ≥ 50 % |
| je Jahr | | 2020 0,49 · 2021 0,55 · 2022 0,67 · 2023 0,71 · 2024 0,78 · 2025 0,73 · 2026 0,74 | |

190 Zellen, im Mittel 58 gemeinsame Coins je Stichtag. ⇒ **HÄLT NICHT** — nach der vorab festen Regel (§9.4) gibt es einen Unterschied über die Datenlänge hinaus.

**Ursache je Merkmal** (Rangkorrelation CMC gegen Binance, nur Coins mit ≥ 730 T in beiden Quellen):

| Merkmal | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 | Lesart |
|---|---|---|---|---|---|---|---|---|
| F1 Abstand zum Hoch | 0,64 | 0,76 | 0,84 | 0,88 | 0,91 | 0,86 | 0,85 | stimmt weitgehend ab 2022 |
| **F2 Tage seit dem Hoch** | 0,53 | 0,51 | 0,71 | 0,76 | 0,80 | **0,68** | **0,72** | ⚠️ schwach, auch mit langer Historie |
| **F8 Alter** | 0,40 | 0,37 | 0,48 | 0,66 | 0,79 | 0,78 | 0,83 | ⚠️ zwei **verschiedene Größen** |

**Woran es liegt (aus dem Code, nicht vermutet):**
- **F8:** Binance misst das Alter **seit der Binance-Listung**, CMC seit dem **ersten Erscheinen in den Top 200**. Das ist nicht dasselbe Alter. Dazu ist CMC links bei 2016-07 abgeschnitten.
- **F2:** Das Hoch liegt bei CMC auf **Wochen**-Schlusskursen, bei Binance auf **Tages**-Kursen ab der Listung. Liegt das wahre Hoch vor der Binance-Listung, kennt Binance es nicht.
- **F1** ist am wenigsten betroffen, weil der Abstand zum Hoch nur grob am Zeitpunkt des Hochs hängt.

**Was das bedeutet:**
- Der Binance-Wert und der CMC-Wert sind **zwei Fassungen** derselben Idee, nicht dieselbe Regel. Eine Bestätigung auf CMC 2017–19 wäre die Bestätigung einer **anderen** Regel.
- Für den **Hebel** zählt das kaum: Gehebelt wird nur, was bei Bitpanda handelbar ist, und dafür gibt es die Binance-Reihen (Voranalyse L2-a §3).
- Für die Werte **außerhalb von Binance** (11 im Bestand) fehlt damit weiter ein bestätigter Wert.

**Lösungen (zur Abstimmung, eine Entscheidung):**

| | Weg | Aufwand | Was er löst |
|---|---|---|---|
| **L1-c (Vorschlag)** | **CMC als eigene Messbasis:** die A1-Messung (E-143) auf CMC 2019–26 **reproduzieren** (R-R11). Hält das Ergebnis dort, ist 2017–19 die unberührte Bestätigung **dieser** Fassung, und sie gilt auch für Werte außerhalb von Binance | 1 Skript, Minuten | Bestätigung + Werte außerhalb von Binance; keine Brücke nötig |
| L1-b | Ein gemeinsames Alter aus einer dritten Quelle (CoinGecko-Historie ab Handelsbeginn, frei, aber ~500 Abrufe mit Pausen) | Stunden, Download mit Ja | nur F8, F2 bleibt |
| L1-d | Den Binance-Wert auf Wochenkurse umstellen | Änderung am Messwert | ⚠️ ändert die Grundgesamtheit der Merkmale, nicht empfohlen |

### 9.6 L1-c Messplan — VORAB festgelegt 26.10.2026 (Nutzer: *„weiter mit L1-c und L2-a“*) · `p92_l1c_cmc_eigene_basis.py`

**Vorab-Befund aus dem Mess-Regelwerk (vor jeder Rechnung):** Auf 1 Monat ist der Block `messnorm._block(30)` = 90 T. Die Bestätigung 2017-01 bis 2019-06 hätte damit nur ~10 Blöcke ⇒ **KEIN BEFUND per Regel**. Deshalb bleibt die Bestätigung, wie in §8.1 Teil 2 schon festgelegt, auf **7 T** (Block 21 T, ~43 Blöcke). 1 Monat 2017–19 ist nur Auskunft.

**Schritt 0 — R-R11: A1 auf CMC nachrechnen (ersetzt die Brücke)**
- Monatsstichtage 2019-01 bis 2026-08, je die CMC-Woche am oder vor dem Monatsersten; Ertrag bis zur Woche 4 Wochen später (28 T).
- Universum, Klasse und Wert wie §8.1 (`p89.lade/merkmale/wert`). Gruppen: **Top 30** (= Klasse H), Top 100, Gesamt (CMC Top 200 ohne Kern).
- Größe wie A1 (`p86`): je Stichtag gleich gewichtet, **oberes Fünftel minus Gruppe**; Band zirkulär, Block 3 Stichtage, 2.000 Ziehungen; < 20 Blöcke KEIN BEFUND.
- **Fällt ein Coin aus den Top 200:** Ertrag nach oben begrenzt durch (Marktwert Rang 200 am Ende ÷ eigener Marktwert am Stichtag) − 1, wie §8.1; Anteil ausgewiesen, Rechnung ohne diese Coins zum Vergleich.
- **Reproduziert, wenn** Top 30: Punktwert > 0 **und** Band schließt 0 aus (A1: +3,5 Pp [+0,7; +7,5]). Top 100/Gesamt nur Auskunft neben A1.
- **Nicht reproduziert:** CMC-Fassung gilt nicht; keine Bestätigung; Ursache und Lösung. **Reproduziert:** weiter mit Teil 2 ohne Zwischenhalt (vorab so festgelegt).

**Teil 2 — Bestätigung 2017-01 bis 2019-06 auf 7 T** (unverändert §8.1 Teil 2)
- Wochen, Ertrag über die nächste Woche aus `preis`; Ausfaller wie oben.
- Filter **Top 30 & oberes Fünftel**. (a) gegen Top 30 gesamt; (b) gegen BTC (`cmc_woche`, Auskunft gegen 0).
- **Nullpunkt** = Mittel von 200 Zufallskörben gleicher Größe aus den Top 30 derselben Woche; Vorsprung = (Filter − Top 30) − Nullpunkt.
- Band zirkulär, Block 3 Wochen, 2.000 Ziehungen, AK-Prüfung beim Blockabstand ≤ 0,15; < 20 Blöcke KEIN BEFUND.
- **Selbsttest vor dem ersten Blick** (auf denselben Wochen, nur Zufallskörbe): Fehlalarm (Band unten > 0) ≤ 5 % auf 200 Zufallskörben; Pflanzung auf Zufallskörben +0,25 / +0,5 / +1,0 Pp je Woche, Auflösung X = kleinste Stärke mit ≥ 80 % Fund; Soll: +0,5 Pp ≥ 80 %. Besteht er nicht, wird das echte Ergebnis nicht angesehen.
- **Stufen:** TRÄGT (Band unten > 0) · TRÄGT NICHT BIS X (Band oben < X) · NICHT TRENNBAR · KEIN BEFUND.
- **Auskunft:** 2019-07 bis 2026 auf 7 T (gesehen) · Zombie-Prüfpunkt (Filter-Mitglieder, die später aus den Top 200 fallen) · Klasse M & oberes Fünftel · 1 M auf 2017–19.
- **Gegenprobe:** Filter-Ertrag je Woche über eine eigene Schleife; Band mit doppelter Blocklänge (gleiche Aussage).
- **Folge:** TRÄGT → die CMC-Fassung ist bestätigt und gilt auch für Werte außerhalb von Binance (Bau-Voranalyse folgt nach Abstimmung) · sonst festhalten; Werte außerhalb Binance ohne bestätigten Wert.

### 9.7 L1-c Ergebnis Schritt 0: A1 auf CMC NICHT reproduziert (26.10.2026; `p92_l1c_cmc_eigene_basis.py`, Ursache `p92b_ursache.py`)

| oberes Fünftel − Gruppe, 1 M | CMC 2019-01..2026-08 (92 Stichtage, 31 Blöcke) | ohne Ausfaller | A1 Binance |
|---|---|---|---|
| **Top 30** | **+2,3 Pp [−0,3; +5,2]** | +1,9 | +3,5 [+0,7; +7,5] |
| Top 100 | +1,2 [−0,9; +3,3] | +0,6 | +1,7 [−0,4; +4,2] |
| Gesamt | +0,7 [−0,7; +2,2] | −0,3 | +1,5 [+0,3; +2,9] |

Ausfaller aus den Top 200 binnen 4 Wochen: 7,4 % der Erträge (begrenzt gerechnet). ⇒ **Nicht reproduziert** (Band enthält 0). Nach §9.6: **keine Bestätigung**, Teil 2 wird nicht gerechnet, der Selbsttest von Teil 2 ist nicht gelaufen.

**Ursache, erster Schritt** (gemeinsame Coins, ~115 je Stichtag, dieselben CMC-Erträge, nur das Fünftel wechselt):

| Top 30 | Fünftel aus CMC-Wert | Fünftel aus **Binance-Wert** | beide oben |
|---|---|---|---|
| oberes Fünftel − Gruppe | +1,5 [−1,9; +4,7] | **−0,0 [−3,1; +3,3]** | +1,3 [−1,8; +4,8] |

- **Es liegt nicht am CMC-Wert.** Selbst die Binance-Auswahl zeigt auf CMC-Erträgen und der CMC-Gruppe keinen Vorsprung.
- Es liegt an **Gruppe, Ertrag oder Coin-Menge**: CMC-Top 30 (Marktwert-Rang der Woche, ohne Stabilitätsbedingung) gegen A1-Top 30 (`rang_mw`), 4 Wochen aus Wochenkursen gegen 30 T aus Tageskursen, nur Coins in beiden Quellen.
- ⚠️ **Das betrifft auch A1 (E-143):** Der Top-30-Vorsprung hält eine andere, gleich vernünftige Abgrenzung nicht aus. Er ist **nicht robust**. Welche der drei Abgrenzungen es ist, ist noch nicht gemessen.

### 9.8 L1-c Ursache zu Ende messen — VORAB festgelegt 26.10.2026 (Nutzer: *„2a“*) · `p92c_ursache_abgrenzung.py`

**Frage:** An welcher Abgrenzung hängt der A1-Vorsprung der Top 30 (+3,5 Pp, 1 M)? Keine neue Bestätigung, nur Ursache.

**Ausgang** ist A1 selbst (`p86.anker(30)`: Binance-Erträge 30 T, Gruppe `rang_mw ≤ 30`, Binance-Fünftel). Getauscht wird **je eine** Sache in Richtung CMC, an denselben Monatsstichtagen 2019-01 bis 2026-08:

| | Coin-Menge | Gruppe Top 30 | Ertrag | Fünftel |
|---|---|---|---|---|
| V0 | A1 | `rang_mw` | Binance 30 T | Binance |
| V1 Menge | **nur Coins auch in CMC Top 200** | `rang_mw` | Binance | Binance |
| V2 Gruppe | wie V1 | **CMC-Rang ≤ 30 (Klasse H)** | Binance | Binance |
| V3 Ertrag | wie V1 | `rang_mw` | **CMC 4 Wochen** | Binance |
| V4 | wie V1 | CMC | CMC | Binance (= p92b „b“) |

- Größe wie A1: je Stichtag oberes Fünftel − Gruppe, Band zirkulär, Block 3 Stichtage (`p86.band`), < 20 Blöcke KEIN BEFUND.
- **V0 muss A1 treffen** (+3,5 ± 0,1 Pp), sonst Halt.
- **Lesart (vorab):** Die Variante mit dem größten Abfall gegen V0 ist die Ursache. Fällt schon V1, hängt A1 an Coins außerhalb der CMC Top 200 (Kleinwerte); fällt V2, an der Gruppenabgrenzung; fällt V3, an der Ertragsrechnung.
- **Gegenprobe:** V0 und V4 über eine eigene Schleife je Stichtag (gleich ±0,01 Pp).
- **Folge:** Ursache festhalten. Ob A1 dann „nicht robust“ bleibt oder eine Abgrenzung fachlich die richtige ist, wird mit dem Nutzer abgestimmt.

### 9.9 L1-c Ursache gemessen: der Marktwert-Rang hat einen VORGRIFF (26.10.2026; `p92c_ursache_abgrenzung.py`)

| A1-Top-30, oberes Fünftel − Gruppe, 1 M | Pp | Band | gegen V0 |
|---|---|---|---|
| V0 A1 | +3,5 | [+0,5; +7,6] | — |
| V1 nur Coins auch in CMC | +3,4 | [+0,3; +7,6] | −0,1 |
| **V2 Gruppe nach CMC-Rang** | **+1,9** | **[−1,7; +6,5]** | **−1,6** |
| V3 CMC-Ertrag (ab Woche **vor** t) | +1,7 | [−0,9; +5,1] | −1,8 ⚠️ Messfehler |
| **V3b CMC-Ertrag ab Woche nach t** | **+3,6** | [+0,8; +7,7] | +0,1 |
| V4b Gruppe CMC + Ertrag b | +2,6 | [−0,4; +6,5] | −0,9 |

V0 trifft A1 (+3,50). Gegenprobe über eine eigene Schleife V0 / V4 / V3b gleich.

**⚠️ Eigener Messfehler, berichtigt:**
- V3/V4 und p92b ließen den CMC-Ertrag an der Woche **am oder vor** dem Stichtag beginnen, bis zu 6 T früher. Diese Tage kennt der Binance-Wert schon: Ein Coin, der in dieser Woche gefallen ist, steht tiefer und damit eher im oberen Fünftel. Das drückte den Ertrag künstlich.
- Richtig ausgerichtet (V3b) ist der Ertrag **nicht** die Ursache.
- **Die Aussage in §9.7 und E-149 „selbst die Binance-Auswahl zeigt −0,0“ ist damit falsch.** Sie beruhte auf demselben Versatz.
- p92 Schritt 0 selbst ist richtig ausgerichtet (CMC-Wert und Ertrag ab derselben Woche) und bleibt gültig.

**Die Ursache ist die Gruppe, und dahinter ein Datenvorgriff:**
- In `rang_mw ≤ 30`, aber nicht in den CMC-Top-30, stehen im Mittel 7,8 Coins je Stichtag, vor allem **WLD, ALGO, HBAR, OP, QNT, ARB, ENA, TIA**.
- Unser Marktwert ist dort ein Vielfaches des CMC-Werts:

| Stichtag | Coin | unser Marktwert | CMC | Rang unser / CMC |
|---|---|---|---|---|
| 2024-06 | ENA | 12,2 Mrd | 1,4 Mrd | 9 / 61 |
| 2024-06 | TIA | 11,1 Mrd | 1,7 Mrd | 12 / 52 |
| 2024-06 | ARB | 7,7 Mrd | 3,2 Mrd | 19 / 28 |
| 2025-06 | WLD | 4,4 Mrd | 1,8 Mrd | 18 / 41 |

- **Woher das kommt** (Docstring `mk_messung.umlauf_stufe`, bekannt, aber in der Wirkung nie gemessen): Vor dem 21.09.2025 gilt für die meisten Coins die **heutige** Umlaufmenge. Tokens mit großen Freigaben seither stehen damit historisch zu hoch.
- **Folge für A1 (E-143):** Mit der zeitrichtigen CMC-Rangfolge (V2) sinkt der Top-30-Vorsprung auf **+1,9 Pp [−1,7; +6,5] ⇒ NICHT TRENNBAR.** Der belastbare Top-30-Befund von E-143 trägt damit den Vorgriff in sich.
- **Was nicht betroffen ist:** Im Betrieb ist die Umlaufmenge die aktuelle, dort gibt es keinen Vorgriff. Betroffen sind alle Messungen mit `mk_messung`-Klassen und -Rängen (E-142 bis E-145: Klassen H/M/S, Top 30/50/100).

**Lösung (zur Abstimmung):** In den Messungen den Marktwert-Rang aus den CMC-Wochen nehmen (zeitrichtig, 2016–2026, Top 200), darunter den eigenen. Danach A1 einmal neu rechnen. R-R11: E-143 wird erst umgestoßen, wenn die neue Fassung V0 reproduziert und nur den Rang tauscht; das ist mit V2 erfüllt.
