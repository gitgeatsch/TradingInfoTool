# Voranalyse REGEL0 – Kosten: (P-A) auf einer Perp-Börse und (P-O) weitere Optimierung auf Bitpanda (ab 23.10.2026)

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
