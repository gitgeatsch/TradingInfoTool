# Voranalyse REGEL0 – Kosten: (P-A) auf einer Perp-Börse und (P-O) weitere Optimierung auf Bitpanda (ab 23.10.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Wozu:** Nutzer 23.10.: *„ja P-A Voranalyse starten, prüfen, gegenprüfen und Doku – ich hätte gerne noch REGEL0 weiter optimiert, bis wir auch auf BP tragen.“*

**Ausgangslage** (`Bestandsaufnahme_brutto_netto_22_10.md`, E-128):
- Der REGEL0-Rohvorteil liegt unverzerrt bei **+0,30 %** je Handel (2025–26) gegen **0,48 %** Kosten bei Bitpanda (0,30 % Schließgebühr plus 0,03 % je 4 h).
- Die geprüften Hebel schließen die Lücke nicht.
- ⇒ Die Plattform selbst ist der einzige ungeprüfte Kostenhebel (P-A).
- Auf Bitpanda (P-O) gibt es noch drei Stellschrauben, die **nicht** geprüft sind (§2).

**Was ausdrücklich NICHT passiert:** kein Konto, kein Handel, keine Betriebsänderung. Alles sind Rechnungen auf vorhandenen Einstiegen. Eine neue Regel wird erst nach einem eigenen Messplan **gewählt** (Wahl 2024, Bestätigung 2025–26) – nie auf 2025–26 selbst.

## 1. P-A – REGEL0 auf Kraken-EU-Perps (Vorprüfung, Obergrenze in der Rückschau)

| Schritt | Inhalt |
|---|---|
| A0 Fakten | Gebühren Maker/Taker (Grundstufe), Funding-Takt und -Historie, Liste der EU-Kontrakte, Hebelgrenze für Privatkunden, Steuer als **Fakt** (Recherche-Agent, Quellen mit Zitat) |
| A1 Abdeckung | Welcher Anteil der REGEL0-Einstiege 2025–26 (vier Mengen) liegt auf einem Coin mit Kraken-Perp? Öffentliche Instrumentenliste vom 23.10.2026 (`data/_perp/`, 209 `PF_*`) |
| A2 Kosten je Tageshandel | 2 × Gebühr je Seite (Taker als Vorgabe, Maker als Auskunft) **plus Funding über die 24 h** (Long zahlt positives Funding). Funding je Einstieg aus `funding_historie.db` (Binance, Tagessumme am Einstiegstag) als **Stellvertreter**; Abgleich mit Kraken-Funding für BTC/ETH, sobald die Historie vorliegt. Dazu ein Aufschlag für Spread und Schlupf von 0,02 / 0,05 % je Seite als Spanne |
| A3 Ergebnis | 24-h-Rohvorteil der **abgedeckten** Einstiege minus Kosten je Menge; Tagesblock-95 %; je Jahr |
| A4 Hebel 2:1 | Auskunft: Wirkung der Grenze auf das Konto (REGEL0 hat im Mittel Hebel 3,4). Das Ergebnis je Handel in % ändert sie nicht |

**Wann P-A eine Messung wert ist (vorab):**
- Der Netto-Vorteil je Handel ist in **allen vier Mengen > 0**, mit Taker-Gebühr und Schlupf 0,05 %.
- **Und** die Abdeckung liegt bei ≥ 50 % der Einstiege.

## 2. P-O – REGEL0 auf Bitpanda weiter optimieren: die noch **ungeprüften** Stellschrauben

| # | Stellschraube | Warum sie neu ist | Vorprüfung (Obergrenze, 2025–26, vier Mengen) |
|---|---|---|---|
| O1 | **Haltedauer im 4-h-Takt der Finanzierung** | A1 rechnete nur 6/12/24 h. Bitpanda rechnet die Finanzierung je **4-h-Block** ab (0,03 %) | Rohvorteil bei 4/8/12/16/20/24 h gegen 0,30 % + 0,03 % × Blöcke |
| O2 | **Auswahl nach Schwankung** | Die Kosten sind ein **fester Prozentsatz**, eine Bewegung skaliert aber mit der Schwankung. Unruhige Werte könnten je Handel mehr % bringen. 2.617 zeigt, dass die Bewertung in den mittleren ATR-Fünfteln am stärksten trägt, im obersten nicht. Nie gegen die **Kosten** gerechnet | Rohvorteil je Fünftel der Schwankung vor dem Einstieg (Standardabweichung der Stundenrenditen der 168 h davor; vorab festgelegt, nur frühere Stunden) |
| O3 | **Einstieg mit Limit unter dem Schluss** | Ein besserer Einstiegskurs wirkt wie niedrigere Kosten. Nie gerechnet. ⚠️ Er bringt negative Auswahl mit sich: Gefüllt wird vor allem dann, wenn der Kurs weiter fällt | Limit = Einstiegsschluss × (1 − x), x = 0,25 / 0,5 / 1 %, gültig 4 h. Gefüllt, wenn das Tief der Folgestunden ≤ Limit; Rohvorteil der gefüllten Einstiege ab Limit, Füllquote. **Faktfrage:** Kennt Bitpanda-Margin Limit-Orders? |

**Wann eine Stellschraube eine Messung wert ist (vorab):**
- Netto (nach 0,48 % bzw. der Kosten nach O1) ist in **allen vier Mengen > 0**, auch in der Rückschau.
- Sonst ist sie für REGEL0 auf Bitpanda erledigt.
- Kombinationen werden erst geprüft, wenn eine einzelne nahe herankommt (innerhalb von 0,05 Pp).

⚠️ **Ehrlich vorab:**
- Das ist die **zweite** Runde auf denselben Einstiegen 2025–26 (nach A1). Ein Treffer in der Rückschau ist **kein Befund**, sondern nur der Anlass für einen Messplan mit Wahl auf 2024.
- Die Tagesblock-Unsicherheit liegt bei ±0,5 Pp.

## 3. Fakten Kraken EU (A0, Recherche 23.10.2026, Kraken-Quellen)

| | Stand | Status |
|---|---|---|
| Gebühr **Kraken Pro**, Grundstufe | **Maker 0,02 %, Taker 0,05 %** vom Nominalwert (kraken.com/features/fee-schedule); die EEA-Gebührenseite verweist darauf | belegt |
| Kraken-**App** „Perps“ | 0,25 % beim Öffnen und 0,25 % beim Schließen. **Nicht** die Pro-Oberfläche | belegt (Satz), für die EU geschlossen |
| Funding | **stündlich**, Prämie ÷ 8, Obergrenze ±0,5 %/h, Long zahlt bei positiver Rate; keine weitere Finanzierungsgebühr | belegt |
| Funding BTC 2025-10 bis 2026-10 | Mittel +0,0092 % je 24 h (5.–95. Perzentil −0,015 bis +0,033 %); die öffentliche Historie reicht nur etwa ein Jahr zurück | belegt (eigener Abruf) |
| Kontrakte | API 209 `PF_*` (202 mit Plattform „europa“); die EU-Supportseite listet etwa 327 | belegt; die Abweichung ist offen |
| Hebel EEA | Kraken zeigt bis 10× (nach Positionsgröße gestaffelt). ESMA 24.02.2026: Perps fallen *„likely“* unter die CFD-Regeln (Krypto 2:1); eine Reaktion von Kraken ist nicht gefunden | belegt / offen |
| Sicherheit EUR | 0 % Abschlag, 0 % Umrechnung; abgerechnet wird in USD, ungedeckte Verluste kosten 0,0025 %/h | belegt / für EEA geschlossen |
| **Steuer** | **kein automatischer KESt-Abzug** (Sitz IE/CY); Steuer-ID nötig; ein AT-Steuerreport ist nicht gefunden | geschlossen |
| Unified Wallet (EEA seit 16.10.2026) | Cross-Margin als Standard: Spot- und Earn-Bestände können Futures-Verluste decken | belegt (Bericht) |

## 4. Ergebnisse der Vorprüfung (`Rechenkern_02_10/p68_regel0_kosten.py`, `p68_gegenprobe.py` → `.txt`)

**Rohvorteil** 24 h (R-R11 wie A1): bestand +0,545 %, unverzerrt +0,296 / +0,295 / +0,313 %.

### 4.1 P-A Kraken-Perps

| Menge | Abdeckung | Rohvorteil dort | netto Taker + Schlupf 0,05 % (Kosten ≈ 0,19 %) | 2025 / 2026 |
|---|---|---|---|---|
| bestand | 58,2 % | +0,673 % | **+0,484 %** | +0,507 / +0,454 |
| unverzerrt 1 | 47,2 % | +0,407 % | **+0,217 %** | +0,259 / +0,161 |
| unverzerrt 2 | 47,7 % | +0,377 % | **+0,182 %** | +0,260 / +0,069 |
| unverzerrt 3 | 47,1 % | +0,470 % | **+0,280 %** | +0,375 / +0,159 |

- Mit Maker-Gebühr kommen etwa +0,06 Pp dazu.
- Die Tagesblock-95 % liegen unverzerrt bei rund −0,35 bis +0,79.
- Das Funding im Einstiegsmittel ist leicht **negativ** (−0,005 bis −0,011 % je Tag): Nach einem Rückgang erhalten die Longs eher Funding.
- **Ersatzgröße geprüft:** Binance- gegen Kraken-Funding 2025-10 bis 2026-08: BTC 0,0084 gegen 0,0074 %, ETH 0,0061 gegen 0,0078 % je Tag, Korrelation 0,6.

**Urteil nach §1:**
- **Netto-Kriterium erfüllt:** alle vier Mengen und **jedes Jahr** über 0 (Gegenprobe G6).
- **Abdeckung knapp verfehlt:** unverzerrt 47 % gegen die geforderten ≥ 50 %. Sie ist an der API-Liste (209) gemessen; die EU-Liste (~327) könnte mehr abdecken (offen).

⚠️ **Vorbehalte:**
- Die Kontraktliste ist von **heute**. 2025 gab es manche Kontrakte noch nicht (Überlebensverzerrung der Liste).
- Spread und Schlupf sind angenommen, nicht gemessen.
- Ein Hebel 2:1 ist möglich (ESMA).
- **Nicht steuereinfach.**
- Nur Kraken **Pro**; die App mit 0,25 % je Seite würde den Vorteil aufzehren.

### 4.2 P-O Bitpanda

| # | Ergebnis (unverzerrt 1 / 2 / 3) | Urteil |
|---|---|---|
| O1 Haltedauer im 4-h-Takt | bestes netto 12 h: −0,09 / −0,07 / −0,11 Pp; 20 h und 24 h schlechter | ✘ |
| O2 Schwankungs-Fünftel | uneinheitlich, kein Fünftel in allen vier Mengen > 0 (F4: −0,01 / +0,17 / −0,07; bestand +0,12) | ✘ |
| **O3 Limit 1 % unter dem Schluss** (4 h gültig, 51 % gefüllt) | gesamt **+0,106 / +0,112 / +0,117 Pp** (bestand +0,336); mit strengerer Füllung +0,087 / +0,082 / +0,100. **Aber 2026: −0,120 / −0,216 / −0,108** (bestand +0,156) | ◐ **erfüllt das Kriterium über den ganzen Zeitraum, ist aber nicht jahresstabil** |
| O3 Dosis (Auskunft) | 1,5 %: +0,22..+0,29; 2 %: +0,44..+0,58 gesamt, aber 2026 bei zwei von drei unverzerrten Mengen weiter negativ | Auskunft |
| Auskunft: nur Coins mit Kraken-Perp | Rohvorteil +0,38..+0,47 % gegen 0,48 % | −0,01 bis −0,10 Pp: nahe, aber darunter |

**Gegenprobe 4 von 5:**
- G1: Kurse direkt per SQL, 300/300 gleich.
- G3: strengere Füllung.
- G5: Abdeckung auf zweitem Weg.
- G6: P-A je Jahr.
- **G2 (O3 je Jahr) fällt**, und zwar inhaltlich: 2026 ist negativ. Das ist ein Befund, kein Rechenfehler.

## 5. Einordnung und Vorschlag

1. **REGEL0 trägt auf einer Perp-Börse mit Pro-Gebühren, in der Rückschau in jedem Jahr.**
   - Der Grund ist allein die Kostenstruktur: rund 0,19 % gegen 0,48 % je Tageshandel.
   - Was dagegen steht: die Abdeckung (knapp die Hälfte der Signale), dass es nicht steuereinfach ist, die ESMA-Hebelfrage und eine zweite Börse.
2. **Auf Bitpanda bleibt eine einzige Stellschraube mit Aussicht: der Einstieg mit Limit unter dem Kurs** (O3).
   - Er wirkt wie ein besserer Einstiegskurs und bringt in der Rückschau +0,1 Pp über die Kosten.
   - **2026 kippt er aber.** Das ist ein ernster Vorbehalt, weil 2026 der jüngste Markt ist.
   - Dazu kommt die **offene Faktfrage**, ob Bitpanda-Margin Limit-Orders kennt (Hilfecenter: Limit bei Aktien nur als *Limit-to-Market*; für Krypto-Margin nicht gefunden).
3. **Ein Treffer in der Rückschau ist kein Befund.**
   - Beide Wege brauchen einen **Messplan mit Wahl auf 2024 und Bestätigung je Jahr 2025 und 2026**.
   - Für O3 hieße das: die Limit-Tiefe aus {0,5; 1; 1,5; 2 %} auf 2024 wählen.

## 6. Nutzer-Fakt 23.10.: bei Bitpanda-Hebel KEIN Limit-Kauf – O3 nur als Spot (`p68b_spot_limit.py` → `.txt`)

Nutzer 23.10.: *„Bei BP ist ein Limit-Kauf fast durchgängig bei Spot möglich, exkl. kleine Coins; bei Hebel kein Limit-Kauf, aber Verkauf mit TP/SL.“*

- ⇒ **O3 ist auf Bitpanda-Margin nicht umsetzbar.**
- Umsetzbar wäre er nur als **Spot ohne Hebel**, über Fusion: 2 × 0,25 % = 0,50 %, steuereinfach. Der Broker scheidet mit 0,99 % / 1,49 % je Seite aus.
- TP/SL beim Verkauf bringt nichts Neues: Kursziele +3/+5 % waren schlechter (2.690), der Stopp ist gemessen (8 %).

**Abdeckung:** Bitpanda-Katalog vom 08.10.2026 als Stellvertreter für Fusion: **92–94 %** der Einstiege.

| Menge | ohne Limit | Limit 1 % (51 % gefüllt) | Limit 1,5 % (34 %) | Limit 2 % (23 %) |
|---|---|---|---|---|
| unverzerrt 1 | −0,224 | +0,076 (2025 +0,19 / **2026 −0,12**) | +0,226 (2026 −0,02) | +0,410 (2026 +0,01) |
| unverzerrt 2 | −0,191 | +0,123 (2025 +0,32 / **2026 −0,22**) | +0,240 (2026 −0,22) | +0,456 (2026 −0,19) |
| unverzerrt 3 | −0,214 | +0,058 (2025 +0,17 / **2026 −0,11**) | +0,213 (2026 +0,07) | +0,425 (2026 +0,19) |
| bestand | +0,050 | +0,325 (2026 +0,18) | +0,456 | +0,641 |

**Einordnung:**
- Über 2025–26 trägt ein tieferes Limit **mehr** (Dosis monoton), aber **2026 ist uneinheitlich bis negativ**.
- Bei 1 % ist 2026 in allen drei unverzerrten Mengen negativ, bei 2 % in einer von drei.
- Ein Limit von 2 % füllt nur noch ein Viertel der Signale.
- ⇒ Als Fusion-Spot ist O3 ein **Kandidat für einen Messplan** (Wahl der Tiefe auf 2024, Bestätigung je Jahr). Die Rückschau lässt für 2026 aber eher ein Scheitern erwarten.
- Kraken (P-A) ist der einzige Weg, der in der Rückschau **in jedem Jahr** trägt.

## 7. Messplan M-L Fassung 1 — Limit-Einstieg für REGEL0 auf Bitpanda/Fusion, VORAB festgelegt (23.10.2026)

Nutzer 23.10.: *„Der Limit-Kauf müsste dann über unsere Anwendung eigenständig erfolgen – das wäre eine Möglichkeit für Hebel und Spot, manuell vs. automatisch. Aktuell müssen wir das Beste aus der BP-Börse bzw. Fusion machen.“* · *„ja Messplan M-L so festlegen, prüfen, gegenprüfen und Doku“*.

**Frage:** Hebt ein Limit-Einstieg unter dem Schluss der Einstiegsstunde REGEL0 über die Bitpanda-Kosten, und zwar **stabil in jedem Jahr**?

| | festgelegt |
|---|---|
| Einstiege | REGEL0 (`kern48jbz_einstiege_<menge>.csv`), vier Mengen, 2024-01 bis 2026-08 |
| Varianten | Tiefe x = 0,5 / 1 / 1,5 / 2 % unter dem Schluss der Einstiegsstunde; das Limit gilt **4 h** (Auskunft: 2 h und 8 h) |
| Füllung | gefüllt zum **Limitpreis**, sobald ein Stundentief in der Gültigkeit ≤ Limit ist (das entspricht einem synthetischen Limit mit laufender Beobachtung) |
| Ausstieg | unverändert: Schluss 24 h nach der Einstiegsstunde |
| Kostenbasis **H** (Hebel) | 0,48 %. Dazu eine Variante mit 0,1 % Schlupf, weil das synthetische Limit zum Marktpreis kauft |
| Kostenbasis **S** (Fusion-Spot) | 0,50 %, nur Coins im Bitpanda-Katalog (08.10.2026) |
| **Wahl auf 2024** | je Kostenbasis die Tiefe mit dem höchsten **Gesamtertrag je Signal**: Summe der Nettoerträge der gefüllten Handel geteilt durch **alle** Signale (ungefüllt = 0), gemittelt über die vier Mengen. Damit gewinnt nicht automatisch das tiefste Limit |
| **Bestätigung** | 2025 und 2026 **getrennt**, mit der auf 2024 gewählten Tiefe |
| **trägt, wenn** | netto je gefülltem Handel > 0 **in 2025 und in 2026**, in **allen drei unverzerrten** Mengen, **und** besser als die Nullwelt (unten) mit Rang ≥ 0,90 in beiden Jahren |
| **Nullwelt** | dasselbe Limit auf **zufällige Stunden derselben Coins im selben Jahr**, 200 Ziehungen (je Signal eine Zufallsstunde). Sie zeigt, ob der Vorteil von REGEL0 kommt oder nur vom mechanischen Kauf nach einem Rücksetzer. Rang = Anteil der Ziehungen mit kleinerem Nettoertrag je gefülltem Handel |
| **Selbsttest VOR dem ersten Blick** | (a) Auf künstlichen Zufallspfaden (t-verteilte Stundenrenditen, BTC-Schwankung) muss der Limit-Einstieg **brutto ≈ 0** bringen (\|Mittel\| < 0,03 %): So ist geprüft, dass die Füllregel mit dem Stundentief nichts schönrechnet. (b) Positivkontrolle: Auf Pfaden mit Rückkehr zur Mitte muss er **positiv** sein. Fällt (a) oder (b) durch, wird nicht gemessen |
| Folgen | **trägt** → Voranalyse der Ausführung (automatisch oder manuell; ob Bitpanda-Margin per API eröffnet werden kann; Fusion-API mit Limit-Orders ist belegt). **trägt nicht** → der Limit-Einstieg ist für REGEL0 auf Bitpanda erledigt und wird nicht nachgestellt |

⚠️ **Ehrlich vorab:**
- 2025–26 sind in §4 und §6 schon in der Rückschau angesehen, mit 2026 schwach. Ungesehen ist die **Wahl auf 2024** und ihre Bestätigung je Jahr; die Folge-Erwartung für 2026 ist eher negativ.
- Füllung mit Stundentief ist eine Näherung; Schlupf und Warteschlange bildet die 0,1-%-Variante ab.

### 7.1 Selbsttest sperrt Fassung 1 — Ursache geklärt, Fassung 1b VORAB (23.10.2026)

**Ergebnis Selbsttest Fassung 1:**
- Zufallspfad brutto −0,056 / −0,048 / −0,046 / −0,036 % (Tiefe 0,5 / 1 / 1,5 / 2 %), Grenze |·| < 0,03 % → **nicht bestanden**.
- Positivkontrolle +0,40 bis +1,59 % ✔.
- Nach Plan wurde **nicht gemessen**.

**Ursache, nachgewiesen** (eigene Simulation, Tiefe 1 %):

| Teilschritte je Stunde | Füllung **zum Limit** | **Marktkauf** beim Erreichen | Überschießen unter das Limit |
|---|---|---|---|
| 60, t-verteilt | −0,062 % | −0,009 % | 0,053 % |
| 60, normal | −0,035 % | +0,002 % | 0,038 % |
| 600, normal | +0,026 % | +0,038 % | 0,012 % |
| 600, t-verteilt | +0,004 % | +0,021 % | 0,017 % |

- Das Minus entspricht dem **Überschießen**: Eine echte Limit-Order wird zum Limitpreis gefüllt, wenn der Kurs schon darunter liegt. Das ist die bekannte negative Auswahl bei Limit-Orders und eine **echte** Eigenschaft, keine Verzerrung zu unseren Gunsten.
- Der Marktkauf beim Erreichen liegt bei ≈ 0, innerhalb des Rauschens (Standardfehler ≈ 0,05 %).
- ⇒ Die Füllregel **rechnet nichts schön**. Das zweiseitige Kriterium war falsch kalibriert.

**Fassung 1b (einzige Änderung):** Selbsttest (a) wird **einseitig**: Der Zufallspfad muss brutto ≤ +0,03 % ergeben, also keine positive Verzerrung. Alles andere bleibt wie §7. Kein echtes Ergebnis ist bisher angesehen.

### 7.2 Ergebnis M-L Fassung 1b: Der Limit-Einstieg TRÄGT NICHT (23.10.2026; `p69_ml_limit.py`, `p69_gegenprobe.py` → `.txt`)

**Selbsttest (einseitig):** bestanden. Zufallspfad −0,036 bis −0,056 % (Überschießen), Positivkontrolle +0,40 bis +1,59 %.

**Wahl auf 2024** nach Gesamtertrag je Signal:

| Kostenbasis | Gesamtertrag je Signal bei 0,5 / 1 / 1,5 / 2 % | gewählt |
|---|---|---|
| H (0,48 %) | +0,482 / +0,392 / +0,327 / +0,285 | **0,5 %** |
| S (0,50 %) | +0,494 / +0,428 / +0,365 / +0,307 | **0,5 %** |

**Bestätigung mit 0,5 %:** netto je gefülltem Handel, etwa 70–75 % gefüllt.

| Basis | 2025 unverzerrt 1 / 2 / 3 | **2026** unverzerrt 1 / 2 / 3 | bestand 2025 / 2026 |
|---|---|---|---|
| H | −0,045 / −0,011 / +0,047 | **−0,215 / −0,209 / −0,273** | +0,298 / +0,100 |
| H + Schlupf 0,1 % | −0,145 / −0,111 / −0,053 | −0,315 / −0,309 / −0,373 | +0,198 / −0,000 |
| S (Fusion-Spot) | −0,081 / +0,001 / −0,021 | −0,219 / −0,206 / −0,285 | +0,272 / +0,108 |

**Urteil nach §7:** **TRÄGT NICHT** auf allen drei Basen. 2025 liegt ≈ 0, 2026 klar negativ. Der Limit-Einstieg ist für REGEL0 auf Bitpanda erledigt und wird nicht nachgestellt.

**Nullwelt:** Rang **1,00** überall. Dasselbe Limit auf Zufallsstunden derselben Coins ergibt netto −0,54 bis −0,89 %.

**Gegenprobe 3/3:**
- G1: Einzelschleife, alle acht Zellen gleich.
- G2: Die Wahl auf 2024 fällt auf zweitem Weg auf dieselbe Tiefe.
- G3: Die Nullwelt ist plausibel.
- Auskunft G4: Gültigkeit 2 h oder 8 h ändert nichts; 2026 bleibt negativ.

#### ⭐ Der Befund dahinter: REGEL0 schlägt den Markt deutlich – der MARKT selbst fiel

| | 2025 | 2026 |
|---|---|---|
| zufällige Stunden derselben Coins, 24 h, ohne Kosten (G3) | **−0,28 %** | **−0,13 %** |
| REGEL0, 24 h, ohne Kosten (unverzerrt) | ≈ +0,40 % | ≈ +0,15 % |
| **Vorsprung von REGEL0 gegen den Markt dieser Coins** | **≈ +0,6 Pp** | **≈ +0,3 Pp** |

- Das Signal ist **stark gegenüber dem Markt**. Das passt zu 2.598: Der Nullpunkt von E[R] ist die **Drift**.
- Vom Vorsprung bleibt absolut aber nur +0,30 % übrig, weil die Altcoins 2025–26 im Mittel fallen. Erst die **Drift plus die Kosten** machen das Ergebnis negativ.
- ⇒ Eine Optimierung des **Einstiegs** allein kann das nicht beheben. Wer den Vorsprung **ohne** die Drift ernten will, muss den Markt absichern (Short, nur über eine Perp-Börse) oder die Kosten **ohnehin** tragen: ein Kauf, der sowieso ansteht, wird nur besser getimt.

⚠️ **Berichtigung 25.10.2026 (E-141):** P-A „trägt auf Kraken“ → **nicht entscheidbar** (Band schließt 0 ein, Abdeckung 47 % < 50 %). Der Befund in §7.2 „REGEL0 schlägt den Markt, Rang 1,00“ beruht auf einer nicht tagestreuen Nullwelt (30 % Fehlalarm); je Tag gewichtet ist der Vorsprung negativ (E-139).
