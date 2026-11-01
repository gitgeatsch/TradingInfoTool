# Voranalyse S1 — die fehlenden Krypto-Zustände als Reihen mit `bekannt_ab` (01.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 01.11.):** *„ja, starte mit den nächsten Schritten, wir müssen wieder vorankommen, z. B. der Voranalyse S1“*.
**Gehört zu:** [`Fuetterung_Satzform_31_10.md`](Fuetterung_Satzform_31_10.md) §6 Schritt 2 (Befund **P2**) ·
[`Datenbasis_Schichten_Sichten_28_10.md`](Datenbasis_Schichten_Sichten_28_10.md) §3 (S1 Krypto gesamt) und §3a (Frage an S1).
**Stand:** ✔ entschieden und **ausgeführt 01.11.2026** (§5). **Betrieb unberührt** — geladen nur am Desktop in `data/_sichten/sichten.db`. Gemessen nur lesend (Desktop-Dateien, öffentliche
Schnittstellen mit kleinen Abfragen).

---

## 0. Worum es geht

S1 soll beantworten: *„Ist die Krypto-Gesamtlage heute ungewöhnlich (Hebel überdehnt, Stablecoin-Abfluss, Breite bricht weg), und
erhöht das das Risiko eines breiten Einbruchs in 1–7 Tagen?“* In `sichten.db` liegen dafür bisher nur **Basis der Quartalsfutures,
Coinbase-Prämie, Nachrichtenton** (P2). Es fehlen genau die Zustände, nach denen die Frage fragt: **Trend, Breite, Season-Stufe,
DVOL, Stablecoins, Funding, OI**.

Maßstab für jeden Zustand: dieselben Regeln wie die übrigen 24 (SF1–SF8), insbesondere **Ü8/SF8** — *ein* Rechenweg live und im
Rückspiel, mit `bekannt_ab` — und **SF7** — ein 5-J-Fenster; am Rückspielbeginn 01.12.2025 heißt das Daten ab **12/2020**.

---

## 1. Je Zustand: Quelle, Tiefe, Maß, live am NB

| Zustand | heute im Betrieb | Quelle (Historie = live) | gemessen: ab | Fenster am 01.12.2025 | Maß (SF2) | `bekannt_ab` |
|---|---|---|---|---|---|---|
| **Trend BTC, ETH** | `marktlage` (Perzentil, Text) | Binance Spot-Tagesschluss (`_binance_tage`, schon im Abrufer) | 2017 | ✔ 5 J | Abstand zum 200-T-Schnitt (Preis) | Folgetag 00:00 UTC |
| **Breite** | `season_ampel.breite` (Anteil der Top 50 nach Umsatz mit 90-T-Ertrag > BTC) | **derselbe Code**: Desktop auf der Messbasis, NB auf der Betriebskopie | 2019 (+120 T Vorlauf) | ✔ 5 J | Niveau (Anteil) | Folgetag |
| **Season-Stufe** | `season_ampel` (E-124, an zwei Zyklen geprüft) | derselbe Code (`rechne`) | 2019 | — (Stufe, kein Rang) | Stufe + seit wann | Folgetag; gilt erst am 7. Tag (Haltezeit, wie im Betrieb) |
| **DVOL BTC, ETH** | Lagebild L7 (`externe_reihen`, Deribit) | Deribit `get_volatility_index_data`, 1D | **2021-03-24** (Start des Index) | ⚠ **4,7 J** | Niveau (Schwankung) | Folgetag |
| **Stablecoins** | `season_ampel.stablecoins` (B3) | DefiLlama `stablecoincharts/all`, `totalCirculatingUSD` | 2017-11 (vor 2020-10 ohne Omni — für das Fenster ab 12/2020 ohne Belang) | ✔ 5 J | Veränderung (siehe Frage 1) | Folgetag — **ohne Jahrgänge**, siehe Befund V3 |
| **Funding BTC, ETH** | Terminmarkt-Job (live), `funding_historie.db` (Desktop) | Binance `fapi/v1/fundingRate` | **2019-09-10** | ✔ 5 J | Niveau (Tagesmittel der drei Zahlungen) | Folgetag |
| **OI BTC, ETH** | Terminmarkt-Job (live), `terminmarkt_historie.db` (Desktop) | Binance-Metrikdateien (`data.binance.vision`, `sum_open_interest`) für die Historie, `futures/data/openInterestHist` 1d live | **2021-12-01** (Beginn der Metrikdateien) | ⚠ **4,0 J** | in **Coins** (Kurs heraus), Veränderung (siehe Frage 1) | Folgetag |

Alle Quellen sind **kostenfrei, ohne Schlüssel** und **am NB mit wenigen kleinen Abrufen je Tag** lieferbar — kein zweites GDELT.
Die Breite braucht am NB keine neue Quelle: sie läuft dort schon täglich (Season-Ampel, 409 Tage).

---

## 2. Befunde aus der Voranalyse

| # | Befund | Folge |
|---|---|---|
| **V1** | **OI für BTC fehlt am Desktop 12/2021–08/2023.** `terminmarkt_historie.db` hat BTC und SOL nur stündlich ab **2023-09**, ETH ab 2021-12. Und `openInterestHist` reicht nur **30 Tage** zurück (gemessen: 31 Punkte) | Historie aus den Metrikdateien: BTC + ETH, 2021-12 bis heute ≈ 2 × 1.800 Dateien à **11–15 KB ≈ 47 MB** (gemessen an zwei Dateien) — **Download, Frage 2** |
| **V2** | **Breite: Desktop und NB weichen um einen Coin ab.** Am 02.08.2026: Desktop (Messbasis) **0,531** = 26 von 49, NB (Season-Ampel `vor90`) **0,551** = 27 von 49 | Grundgesamtheit (CLAUDE.md): nicht beiläufig hinnehmen. Ursache vermutlich die Stablecoin-Ausnahme (`abbau_stamm` liegt nur am NB) oder die Symbolmenge. **Gegenprobe gegen eine Kopie:** `data/spot_betrieb.db` vom NB in den Austauschordner → alle 409 Tage vergleichen |
| **V3** | **Stablecoins werden revidiert**, DefiLlama führt keine Jahrgänge. Die Season-Ampel misst das je Lauf (`revision_b3`): am NB zuletzt **0,0** bzw. **2,6·10⁻⁶** | Vorgriff klein, aber nicht null. `bekannt_ab` = Folgetag mit Kennzeichen „ohne Jahrgänge“; die Revisionsgröße wird je Abruf mitgeschrieben (wie in der Ampel) |
| **V4** | **Zwei Wahrheiten vermeiden** (P3): Mail und Statusseite zeigen Season-Ampel und DVOL schon | S1 nimmt **dieselben Funktionen** (`season_ampel.breite/rechne`), nicht eine zweite Rechnung. DVOL aus derselben Deribit-Abfrage wie L7 |
| **V5** | Die **Season-Stufe hat keinen Rang** — sie ist eine Kategorie | eine eigene Zeilenform in der Satzform: *„Season-Ampel: ungewohnt seit 08.09. (2 von 3 Bedingungen) · Stand · Fakt“*, ohne P-Rang, ohne ● (SF3 gilt nur für Ränge) |
| **V6** | **Fenster:** DVOL 4,7 J und OI 4,0 J sind kürzer als 5 J — die Quellen gibt es nicht länger | wie Basis Quartal (4,8 J): mit ⚠ ausgewiesen (SF7), nicht weggelassen |

---

## 3. Umfang

S1 bekäme **11 neue Zeilen** (Trend ×2, Breite, Season-Stufe, DVOL ×2, Stablecoins, Funding ×2, OI ×2) zu den 5 bestehenden
(Basis ×2, Prämie ×2, Ton). Satzform-Probe: rund **+600 Zeichen ≈ +160 Token** je Sicht-Aufruf. BTC **und** ETH wie bei Basis und
Prämie — ETH ist im Hebel und in REGEL0 der zweite Kern und verhält sich in Einbrüchen nicht gleich.

**Bauweg** (nach Abstimmung): derselbe Abrufer `api/sichten_quellen.py`, neue Quellen in derselben Tabelle `reihe`
(`quelle`, `symbol`, `datum`, `wert`, `bekannt_ab`). Breite und Season-Stufe als **Ableitung** aus dem Ampel-Code, nicht als
eigener Abruf. Prüfpaket: Rechenweg Historie = live an überlappenden Tagen (Funding, OI, DVOL je 30 Tage), Breite Desktop = NB
(V2), Revisionsgröße Stablecoins.

---

## 4. Zur Abstimmung — drei Fragen

**Frage 1 — Maß für Krypto-Mengen (Stablecoins, OI).** SF2 sagt für Mengen „Veränderung gegen Vorjahr“ — gesetzt für M2 und
Netto-Liquidität, die sich in Monaten bewegen.

| | Weg | Folge | Einschätzung |
|---|---|---|---|
| **a** | **Veränderung über 30 Tage** für Krypto-Mengen | passt zur Frage an S1 (*Abfluss*, *Hebel überdehnt*, 1–7 Tage); ein Jahresvergleich zeigt einen Abfluss der letzten Wochen kaum | **Empfehlung** — als eigene Art in SF2 („Krypto-Mengen“), fest im Code, mit Begründung |
| b | Vorjahr wie M2 | einheitlich mit SF2 | träge: der Ausstieg von Hebel in einer Woche verschwindet im Jahresvergleich |
| c | beides als zwei Zeilen | volle Information | doppelte Zeilen je Menge, die Sicht muss zwei Ränge derselben Größe wägen |

**Frage 2 — OI-Historie laden?** (V1) ≈ 47 MB Binance-Metrikdateien, BTC und ETH ab 12/2021, nur Desktop.

| | Weg | Folge |
|---|---|---|
| **a** | **laden** (Empfehlung) | OI im Rückspiel mit 4,0 J ⚠; dazu Gegenprobe Metrikdatei = `openInterestHist` an den letzten 30 Tagen |
| b | nicht laden | BTC-OI erst ab 2023-09 → im Rückspiel 2,25 J, wachsendes Fenster (verletzt SF7) |

**Frage 3 — Gegenprobe Breite (V2):** beim nächsten Gang zum NB `data\spot_betrieb.db` in den Austauschordner kopieren (nur
kopieren, nichts ändern). Ohne sie bleibt der Abstand von einem Coin unerklärt — **Ja/Nein**.

✔ **Entschieden 01.11.2026 (Nutzer: *„1a, 2a, 3 ja – prüfen gegenprüfen und doku“*):** Krypto-Mengen über **30 Tage**,
OI-Historie **laden**, Gegenprobe Breite gegen die NB-Kopie **ja** (`spot_betrieb.db` liegt seit 01.11. im Austauschordner).

---

## 5. Ausführung und Nachweis (01.11.2026)

**Gebaut** — nur Desktop, Betrieb unberührt:

| Teil | was |
|---|---|
| `api/sichten_quellen.py` | sieben neue Abrufer in **derselben** Auftragsliste (Ü8): `kurs_spot`, `dvol`, `funding`, `oi` (+ `_oi_datei`), `stablecoins` (Funktion der Ampel), `breite` und `season_stufe` (Ampel-Code `season_ampel.rechne`). OI setzt ab dem letzten Tag fort. **Nebenbei behoben:** „heute“ war Ortszeit statt UTC (`_heute`) — zwischen 00:00 und 01:00 MEZ rutschte die offene UTC-Kerze in Kurs, Basis, Prämie und GDELT |
| `Rechenkern_02_10/fuetterung_satzform_probe.py` | die elf S1-Zeilen; Maß `tage30` (30 **Kalender**tage) und `stufe` (ohne Rang); „vor 4 Wochen“ mit drei gültigen Stellen (vorher Funding „+0.01“); leere Reihe → eigene Zeile, nie still |
| `pruefe_pakete.py` Paket **SichtenQuellen** | ohne Netz, 9 Prüfungen: UTC-Tag, Stufen-Codes **abgeleitet** aus `season_ampel.NAME`, elf Reihen in der einen Auftragsliste, offene Kerze nicht dabei, Funding-Tagesmittel, OI aus der Zeile 00:00 der Folgetagsdatei (nicht der ersten), API als Rückfall, > 3 fehlende Tage = Fehler, nie Produktions-DB |
| `Rechenkern_02_10/s1_nachweis.py` → `s1_nachweis.txt` | die Gegenproben gegen echte Daten (unten) |

**Geladen** in `data/_sichten/sichten.db` (Sicherung `sichten_vor_s1_01_11.db`):

| Reihe | Tage | Zeitraum |
|---|---|---|
| Kurs BTC, ETH · Funding BTC, ETH · Stablecoins | je 2.496 | 2020-01-01 – 2026-10-31, lückenlos |
| DVOL BTC, ETH | je 2.048 | 2021-03-24 – 2026-10-31, lückenlos |
| OI BTC, ETH | 1.797 | 2021-11-30 – 2026-10-31, lückenlos (BTC 2021-12-13 nach Verbindungsfehler nachgeholt → Abrufer wiederholt jetzt dreimal) |
| Breite, Season-Stufe | je 2.455 | 2020-01-01 – **2026-09-20** (Desktop-Messbasis eingefroren; am NB laufend) |

**Gegenproben** (`s1_nachweis.txt`, 31 Prüfungen, **30 grün**):

| # | Ergebnis |
|---|---|
| G1/G2 | alle elf Reihen lückenlos, `bekannt_ab` überall = Folgetag 00:00 UTC, kein Tag ≥ heute |
| G3 | Kurs = Desktop-Messbasis an 2.454 Tagen **bitgleich**. Ausnahme ausgewiesen: der **letzte** Messbasis-Tag 20.09.2026 wurde mit **offener Kerze** geladen (BTC −0,82 %, ETH −2,51 %) — ein Befund über die Messbasis, nicht über die neue Reihe |
| G4 | Funding × 3 = `funding_historie.db` (dort Tagessumme) an 2.435 Tagen, 100 % |
| G5 | OI Datei gegen `openInterestHist` an 30 Tagen: größte Abweichung **0,36 %** (BTC) / 0,26 % (ETH), Median 0,04 % / 0,03 %. Grenze **0,5 %**, begründet: die 30-T-Veränderung liegt im Median bei **7,2 % / 9,6 %**, im 10. Perzentil bei 1,3 % / 1,7 %; aus der API kommt nur der jeweils **letzte** Tag |
| G6b | **Season-Stufe Desktop = NB an allen 368 gemeinsamen Tagen** |
| G7 | Stablecoins B3 (91 T) aus unserer Reihe = NB-Ampel an 409 Tagen, Abweichung 0 — dieselbe Funktion, dieselbe Datierung |
| ⚠ **G6a offen** | **Breite Desktop ≠ NB**: gleich an 45 von 368 Tagen, im Mittel 0,022 (≈ 1 Coin von 50), höchstens 0,088 (4,4 Coins); **Klasse im 5-J-Rang anders an 23 von 368 Tagen (6,2 %)**. Ausgeschlossen: Stablecoin-Ausnahme (beide Seiten dieselben 11). Die eingestellten Werte erklären nur einen Teil (ohne sie gleich an 80 statt 45 Tagen). **Vermutung:** die Kurs- und Umsatzreihen der Betriebskopie (NB) und der Messbasis (Desktop) unterscheiden sich. **Nächster Schritt:** NB-Betriebskopie `data\messdaten.db` in den Austauschordner, Breite darauf nachrechnen, Ursache je Coin |

**Probe** (beide Stichtage, 35 Zustände, ≈ 1.750 Token): am **01.12.2025** fällt S1 mit **OI hoch** (BTC P87, ETH P85, +15–20 % in 30 T) und **BTC tief** (P17, −17,6 % zum Schnitt) auf; am **29.10.2026** mit DVOL tief, Stablecoin-Abfluss (P16), Coinbase-Prämie tief, Krypto-Ton sehr tief. **Fenster:** OI am Rückspielbeginn **3,9 J** (nicht 4,0 — die 30-T-Veränderung braucht den ersten Monat), DVOL 4,7 J, Basis 4,8 J — alle mit ⚠.

⚠ **Grundgesamtheit (G6a):** bis die Ursache gefunden ist, geht die Breite im Rückspiel mit dem Kennzeichen *„Desktop ≠ NB, 6,2 % Klasse anders“* in die Befund-Karte — nicht still.
