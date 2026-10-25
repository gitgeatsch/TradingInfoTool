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
