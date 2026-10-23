# Voranalyse Lagebild Gesamtmarkt (L-A Teil 1) — Bauvorschlag zur Abstimmung (23.10.2026)

**Wozu:** Nutzer 23.10.: *„L-A“*. Teil 1 ist das **Lagebild Gesamtmarkt als Fakt** auf der Statusseite und in den Handlungsmails. Grundlage ist der Indikator-Atlas (E-135). **Kein Bau vor dem Ja**; dies ist der Vorschlag.

## 1. Was es schon gibt (zuerst das Bestehende)

| Baustein | Stand | Wo |
|---|---|---|
| **O54 Makro-Lage** | Kanäle K1–K9 lang und kurz, Gesamt (Rückenwind / neutral / Gegenwind), täglich aus FRED (Schlüssel am NB nachgewiesen) | `agent/makro_lage.py` → Statusseite (Bereich oben), Zeile in REGEL0-, B1-, B3- und B4-Mails, Diagnose |
| Season-Ampel | Krypto-Phase (B1 BTC, B2 M2, B3 Stablecoins) | `agent/season_ampel.py`, Mail bei Stufenwechsel, Statusseite |
| Termine (O52) | CPI, NFP, FOMC als Fakt | REGEL0-Mail |
| Fear & Greed | wird abgefragt (`api/macro.get_fear_greed_index`) | alte Kette, nicht in den neuen Mails |

⇒ Das Lagebild wird eine **Erweiterung von O54** (`makro_lage`): derselbe Job, dieselbe Quelle, dieselbe Ablage `data/makro_lage.json`, ein neuer Abschnitt `gesamtmarkt`. Es entsteht **kein** neues Modul und **kein** neuer Job.

## 2. Was ins Lagebild soll — je Zeile ein Fakt samt Messbefund

| # | Zeile | Daten (FRED, frei) | Messbefund dazu (E-135) |
|---|---|---|---|
| L1 | **Rezessionsampel:** Zinskurve 10J–2J und 10J–3M (Stand, ob invertiert und seit wann), Sahm-Regel | T10Y2Y, T10Y3M, SAHMREALTIME | Rezessionen kosteten den Nasdaq jedes Mal 24–68 %. Die Kurven-Inversion lief 1980–2008 jeder Rezession 4–33 Monate voraus, **2022–24 erstmals ohne** Rezession |
| L2 | **Reifegrad:** Nasdaq-Bullenmarkt seit X Monaten (Median 60); BTC Y % unter dem Allzeithoch, Z Monate seit dem Hoch | NASDAQCOM; BTC-Kurs im System | beschreibend (13 Nasdaq-Bärenmärkte seit 1971; 4 BTC-Zyklen) |
| L3 | **Geld:** Netto-Liquidität 26 W, US-M2 J/J | WALCL, WTREGEN, RRPONTSYD, M2SL (schon in O54) | **keine Voraussetzung** für BTC oder Aktien; Niveau-Tendenz bei der Netto-Liquidität (+37 % gegen +17 % über 90 T, nicht belegt) |
| L4 | **Zinsen und Anleihen:** US-10J Stand und 12-Monats-Veränderung, Laufzeitprämie | DGS10, THREEFYTP10 | Fakt (Lage 10/2026: 5,13 %, höchster Stand seit 2002) |
| L5 | **Öl:** Brent Stand und 12 Monate | DCOILBRENTEU | Fakt (Ölschock 2026) |
| L6 | **Fear & Greed** (Extrem: < 25 / > 75) | alternative.me | **einziger Vorläufer** der BTC-Wenden im Atlas (Rang 0,97 in beiden Hälften), zum Teil kursabgeleitet; als Regel erst nach F-1 Fassung 2 |

**Form:**
- Je Zeile: ein Stichwort, ein Wert und ein kurzer Satz *„gemessen: …“*.
- **Kein Gesamturteil und keine Ampelfarbe**, die eine Handlung auslöst (Regel 4: ein Fakt ist kein Signal).
- Eine **Ausnahme zur Abstimmung**: Die Rezessionsampel darf **rot** zeigen, wenn Kurve **und** Sahm-Regel anschlagen. Das wäre ein Fakt mit belegter Folge für Aktien, aber ohne Regel für Krypto.

## 3. Wo es erscheint

| Ort | Inhalt | Begründung |
|---|---|---|
| **Statusseite**, Bereich *Makro* (oben) | alle Zeilen L1–L6 | Lagebild = Statusseite (Nutzer 10.10.: primär Mails und Statusseite) |
| **Handlungsmails** (REGEL0, B1, B3, B4) | **eine** verdichtete Zeile, z. B. *„Gesamtmarkt: keine Rezessionssignale · Nasdaq-Bull 18 M · BTC −35 % vom Hoch · F&G 32“* | Jede Mail eine Handlung: das Lagebild nur als Zusatz, nie eine eigene Mail |
| GUI, Reiter *Markt (Krypto)* | wie die Statusseite | Information nie nur in der GUI |
| Diagnose / Teilexport | Abschnitt `gesamtmarkt` | NB-Kontrolle |

## 4. Bau, Prüfung, NB (nach dem Ja)

- **Bau:** `makro_lage.REIHEN` um 6 FRED-Reihen erweitern (T10Y3M, SAHMREALTIME, NASDAQCOM, DGS10, THREEFYTP10, DCOILBRENTEU) und Fear & Greed aufnehmen; Funktionen `gesamtmarkt(roh)` und `zeile_gesamtmarkt()`; Statusseite und Mails über die bestehenden Wege (`stand`, `mailteil`).
- **Prüfung:**
  - Prüfstand gegen die Atlas-Rechnung (R-R11: dieselben Werte wie `p73` und `p75` an Stichtagen);
  - Gegenprobe zweiter Weg;
  - Suite-Paket;
  - Statusseite gegen eine Kopie im Browser.
- **NB:** Pull und Neustart, Kontrolle K-GM-1 (Diagnose zeigt `gesamtmarkt`, Zeile in der nächsten Handlungsmail). Das wird mit dem nächsten NB-Bündel gebündelt.
- **Kein Eingriff** in REGEL0, Hebel oder Season-Ampel.

## 5. Zur Abstimmung

1. Zeilen L1–L6: alle, oder eine Auswahl?
2. Soll die Rezessionsampel „rot“ zeigen dürfen (Kurve **und** Sahm)?
3. Die Mailzeile nur in REGEL0-Mails oder auch in B1, B3 und B4?
