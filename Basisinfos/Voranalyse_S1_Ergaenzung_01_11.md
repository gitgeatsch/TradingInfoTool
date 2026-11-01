# Voranalyse S1 — die fehlenden Krypto-Zustände als Reihen mit `bekannt_ab` (01.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 01.11.):** *„ja, starte mit den nächsten Schritten, wir müssen wieder vorankommen, z. B. der Voranalyse S1“*.
**Gehört zu:** [`Fuetterung_Satzform_31_10.md`](Fuetterung_Satzform_31_10.md) §6 Schritt 2 (Befund **P2**) ·
[`Datenbasis_Schichten_Sichten_28_10.md`](Datenbasis_Schichten_Sichten_28_10.md) §3 (S1 Krypto gesamt) und §3a (Frage an S1).
**Stand:** Vorlage zur Abstimmung. **Nichts am Betrieb geändert, nichts geladen.** Gemessen nur lesend (Desktop-Dateien, öffentliche
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
