# Voranalyse H-A — REGEL0-Historie verlängern und Marktphasen auf zwei Ebenen (23.10.2026)

**Wozu:** Nutzer 23.10.: *„ja H-A Voranalyse starten, prüfen, gegenprüfen und Doku“*. Seine zwei Hinweise:
1. Wie schon erwähnt, ist eine Unterscheidung **übergeordneter und kleinerer Marktphasen** erforderlich.
2. Ja, statistisch problematisch; wir müssen **rückwirkend prüfen, welche Indikatoren in welchen Phasen relevant sind**, also welche Signale die Märkte in welche Richtung bewegt oder neutral gelassen haben.

**Ausgangslage:** E-133. Ein Marktfilter für REGEL0 ist mit 2024–26 nicht entscheidbar; selbst ein Orakel ist nicht von Zufall zu trennen.

Skripte: `Rechenkern_02_10/p72_historie_voranalyse.py`, `p72_gegenprobe.py` → `.txt`. **Kein Download, keine Messung eines Filters.**

## 1. Lohnt die Verlängerung? — Auflösung vorab gerechnet

**A. Zustandsstrecken der sechs F-1-Filter** (nur die Filterreihen, ohne Ertrag):

| Filter | 2024–26 | 2020-06 bis 2026-08 | Filter verfügbar ab |
|---|---|---|---|
| F1 Makro Gesamt kurz | 51 | 91 | 2020-01 |
| F2 Makro Gesamt lang | 9 | 29 | 2019-10 |
| F3 Netto-Liquidität kurz | 27 | 57 | 2017-01 |
| F4 Dollar kurz | 31 | 72 | 2017-01 |
| F5 Nasdaq über 200 T | 9 | 21 | 2018-10 |
| F6 BTC über 200 T | 31 | 53 | 2013-01 |

**B. Auflösung** (künstliche Tageserträge aus dem echten REGEL0-Tagesnetto 2024–26, gepflanzter Unterschied D zwischen *an*- und *aus*-Tagen mit der echten Struktur von F6, Fundquote bei Rang ≥ 0,99):

| Fenster | Tage | Strecken | D = 0,5 Pp | **1,0 Pp** | 1,5 Pp |
|---|---|---|---|---|---|
| 2024–26 (heute) | 974 | 31 | 12 % | **31 %** | 67 % |
| **2020-06 bis 2026-08** | 2.283 | 53 | 30 % | **84 %** | 100 % |

- Der Orakel-Filter aus E-133 hatte D ≈ 1,15 Pp. Ein echter Filter liegt darunter.
- ⇒ Mit der Verlängerung werden **große** Markteffekte (≥ 1 Pp) nachweisbar, kleine (≈ 0,5 Pp) weiterhin nicht.
- ⚠️ Das Rauschen ist aus 2024–26 gezogen. 2020–23 hatte weniger Coins und Signale je Tag und ist vermutlich lauter.

**Gegenprobe 4/4:**
- G1: Strecken per groupby, gleich.
- G2: anderer Startwert, D 1,0 Pp: 40 % gegen 77 %.
- G3: Bärenphasen per cummax, dieselben Hochs.

## 2. Machbarkeit der Nachrechnung

| Punkt | Stand |
|---|---|
| **Erzeuger** | `agent/regel0_rechnung.py --nachrechnung --ordner <ordner>`: rechnet REGEL0 0.1 zeilengleich zur Referenz `kern48jbz_einstiege_bestand.csv` (R-R11). Mit `--ordner` lässt er sich auf einen **eigenen Datenordner** richten; die bestehenden Dateien bleiben unberührt |
| ⚠️ **Monatsmodell lernt fest ab 2023-01** | `ab = K2._h(datetime(2023, 1, 1))`, Mindestens 5.000 Treffer. Vor 2023 gibt es **kein Modell und damit keine Signale**. ⇒ Für die frühen Monate braucht es eine **dokumentierte Regel**: wachsendes Lernfenster ab dem Datenbeginn, nur für Monate vor 2024. Ab 2024 bleibt alles unverändert, und die Referenz 2024–26 muss **bitgleich** herauskommen (R-R11 vor jedem Ergebnis) |
| Zeitbasis | Stunden ab 2020-01-01; frühestes sinnvolles Signal etwa **2020-06** (Vorlauf 240 h, Normal) |
| **Daten** | Binance-Stundenkerzen (data.binance.vision, frei, ohne Konto), 2019-06 bis 2023-12. Je Coin und Monat ≈ 40 KB (BTC 2019–2023: 60 Dateien, **2,5 MB**). Für das Universum (~550 Werte, mit eingestellten) **grob 0,5–0,7 GB** ⇒ **Download-Ja nötig** |
| Ablage | neuer Ordner `data/_hist/` (Kopie der Struktur von `stundenkurse.db` / `stundenkurse_alle.db`, nicht committet) |
| Mengen | zuerst **bestand** (mit Überlebensverzerrung); die unverzerrten Mengen brauchen die eingestellten Paare (Binance behält deren Archiv), als zweite Stufe |

## 3. Marktphasen auf zwei Ebenen (Hinweis 1) — BTC 2013–2026

**Übergeordnet** (Rückgang ≥ 50 % vom Allzeithoch bis zum Tief):

| Hoch | Tief | Rückgang | Art |
|---|---|---|---|
| 09.04.2013 | 06.07.2013 | −71 % | Einbruch im Bullenmarkt |
| 04.12.2013 | 14.01.2015 | −85 % | **Zyklus-Bärenmarkt** |
| 16.12.2017 | 15.12.2018 | −84 % | **Zyklus-Bärenmarkt** |
| 13.04.2021 | 20.07.2021 | −53 % | Einbruch im Bullenmarkt |
| 08.11.2021 | 09.11.2022 | −77 % | **Zyklus-Bärenmarkt** |
| 06.10.2025 | 30.06.2026 | −53 % | **Zyklus-Bärenmarkt, laufend** (kein neues Hoch) |

**Kleiner** (Zickzack −20 % / +25 %): **86 Wendepunkte** 2013–2026, davon **24** in 2020-06 bis 2026-08 und **8** in 2024–26.
- Je Jahr: 2013 14 · 2014 7 · 2015 10 · 2016 3 · 2017 12 · 2018 8 · 2019 6 · 2020 2 · 2021 9 · 2022 5 · 2023 2 · 2024 3 · 2025 2 · 2026 3.

⇒ Auf der **übergeordneten** Ebene gibt es 4 Zyklen (beschreibbar, nicht testbar). Auf der **kleineren** Ebene gibt es genug Fälle für eine Statistik, über 2013–2026 mit 86 Wendepunkten.

## 4. Hinweis 2 — rückwirkend prüfen, welche Indikatoren in welchen Phasen gewirkt haben: der „Indikator-Atlas“

**Die Frage:** Welche Indikatoren haben vor den Wendepunkten des Marktes ihre Richtung gewechselt (Vorlauf), welche erst danach (Nachlauf), und welche blieben neutral? Getrennt nach Ebene, nach Hoch- und Tief-Wenden und nach Zeitraum.

**Skizze des Messplans** (zur Abstimmung, noch nicht festgelegt):

| | |
|---|---|
| Wendepunkte | BTC übergeordnet (6, beschreibend) und kleiner (86 seit 2013); dazu der Altcoin-Korb (Messbasis ab 2017) |
| Indikatoren (frei, schon im Haus oder im Schema) | Makrokanäle K1–K9 (Geldmenge, Netto-Liquidität, Realzins, Zinspfad, Kurve, Kredit, NFCI, Dollar, VIX), Nasdaq-Trend, US-10J, Stablecoin-Menge (verkettet), Funding (ab 2019), Fear & Greed (ab 2018), BTC-Dominanz (CMC-Wochen ab 2017), Season-Ampel B1–B3 |
| Größe | **Vorlauf-Quote**: Anteil der Wendepunkte, vor denen der Indikator binnen W Tagen (klein 30, übergeordnet 90) in die passende Richtung wechselte. Dazu der Nachlauf |
| **Nullwelt** | dieselbe Quote an **Zufallsdaten** (gleiche Zahl, gleiche Jahre), 1.000 Ziehungen; Lift und Rang |
| Stabilität | getrennt **2013–2019** und **2020–2026**; nur was in **beiden** Hälften vorläuft, gilt als Kandidat |
| Ergebnis | (a) ein **Atlas als Fakt**: welcher Indikator in welchem Phasentyp vor- oder nachlief; (b) **wenige Kandidaten** für den Marktfilter. Weniger Filter bedeuten weniger Mehrfachtesten und bessere Auflösung beim späteren Test auf der verlängerten REGEL0-Historie |
| ⚠️ Grenze | Ein Vorlauf in der Rückschau ist **noch kein Signal**. Er wird erst auf den REGEL0-Handel getestet (F-1 Fassung 2 auf 2020–26) |

## 5. Vorschlag (zur Abstimmung)

| | Reihenfolge | Warum |
|---|---|---|
| **V-1 (empfohlen)** | **Erst der Indikator-Atlas** (ohne Download, Daten vorhanden), **dann** die REGEL0-Historie 2020–23 (Download-Ja) und F-1 Fassung 2 nur mit den Atlas-Kandidaten | beantwortet Hinweis 2 direkt; senkt das Mehrfachtesten; der Download kommt erst, wenn es Kandidaten gibt |
| V-2 | erst die REGEL0-Historie (Download jetzt), dann F-1 mit den sechs Filtern | schneller beim Hebel, aber sechs Filter und schwächere Auflösung |
| V-3 | beides parallel | doppelte Arbeit vor der ersten Antwort |
"""

## 6. Messplan F-1 Fassung 2 — Fear & Greed als Marktfilter auf der verlängerten REGEL0-Historie, VORAB festgelegt (23.10.2026)

Nutzer 23.10.: *„L-A“* · *„und Download“*. Herkunft: E-133 (2024–26 nicht entscheidbar), E-134 (Verlängerung lohnt), E-135 (Atlas: einziger Kandidat Fear & Greed).

**Signale (vorab):**
- REGEL0 0.1 unverändert (`agent/regel0_rechnung`, Betriebscode **nicht** geändert), Menge *bestand* mit Zusatz (`kern48jbz_gruppe_bestand.csv`), auf `data/_hist/`. Dort liegen die heutigen Stundenkurse plus Binance 2019-06 bis zum jeweiligen Datenbeginn.
- **Zwei Läufe:**
  - **A:** Monate 2024-01 bis 2026-08, Lernbeginn wie im Betrieb 2023-01-01.
  - **B:** Monate 2020-07 bis 2023-12, Lernbeginn **2020-06-01** (wachsendes Fenster ab dem Datenbeginn). Das ist die dokumentierte Regel für die frühen Monate.
- **R-R11:**
  - (1) Auf den **heutigen** Daten (`data/`) ist die Nachrechnung **zeilengleich** zur Referenz `kern48jbz_einstiege_bestand.csv`; sonst wird nicht weitergerechnet.
  - (2) Auskunft: Anteil gleicher Einstiege 2024–26 zwischen Lauf A und der Referenz. Die längere Vorgeschichte verändert *Reife* und *Normal*, Abweichungen sind deshalb erwartet und werden ausgewiesen.
- ⚠️ Nur *bestand*, also ohne eingestellte Paare (Überlebensverzerrung). Trägt es, folgen die unverzerrten Mengen als Bestätigung.

**Filter (vorab, nur einer):**
- **FG-Gier aus:** gehandelt wird nicht, wenn Fear & Greed am **Vortag > 75** (Gier) liegt.
- Begründung aus E-135: Der Wechsel auf Gier lief den BTC-Hochs voraus.
- Auskunft:
  - *30 T nach einem Wechsel auf Gier aus*;
  - *nur bei F&G < 50 an*;
  - die sechs Filter aus E-133 (ohne Urteil).

**Zielgröße:** 24-h-Ertrag je Handel nach **0,48 %** (Bitpanda-Hebel), Tagesraster wie p71.

**Selbsttest VOR dem ersten Blick** (auf den verlängerten Signalen, ohne Filterergebnis):
- (a) 200 Zufallsfilter mit der Streckenstruktur von FG-Gier: Anteil „trägt“ ≤ 5 %;
- (b) Orakel-Filter (zentrierter 30-T-Mittelwert des Tagesnettos > 0) erreicht **Rang ≥ 0,95**.
- Fällt (b) durch, heißt das Urteil **nicht entscheidbar**, und der Filter wird nicht angesehen.

**Trägt, wenn:**
- (1) Umkehr über 2020-07 bis 2026-08: netto *an* > 0 und *aus* < 0;
- (2) netto *an* > 0 in **2025 und 2026** (der heutige Markt) **und** in mindestens 4 der 6 übrigen Halbjahre 2020-H2 bis 2024-H2;
- (3) Rang der Verbesserung (netto *an* minus netto alle) gegen die Strecken-Permutation **≥ 0,95** (ein Filter, keine Bonferroni-Korrektur).

**Folgen:**
- **trägt** → Bestätigung auf den unverzerrten Mengen (eingestellte Paare nachladen), dann Voranalyse Betrieb (Sperre der REGEL0 bei Gier).
- **trägt nicht / nicht entscheidbar** → REGEL0 bleibt Vorwärtsprotokoll; Fear & Greed bleibt Fakt im Lagebild.
