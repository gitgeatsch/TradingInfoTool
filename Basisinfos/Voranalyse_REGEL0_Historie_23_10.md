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

### 6.1 Auslegung vor dem ersten Lauf (23.10.2026, vor jedem Blick auf ein Filterergebnis)

| # | Offene Stelle im Plan | Auslegung |
|---|---|---|
| 1 | Kriterium (2) nennt *„4 der 6 übrigen Halbjahre 2020-H2 bis 2024-H2“*. Das sind **9** Halbjahre, nicht 6 (eigener Zählfehler im Plan) | derselbe Anteil von zwei Dritteln: **mindestens 6 von 9**. Die Zahl wird ausgegeben, sodass auch die strengere Lesart nachprüfbar bleibt |
| 2 | Fear & Greed *„am Vortag“* | Tageswert von alternative.me (UTC-Tag) des Vortags. Ein fehlender Wert zählt als *an* (wie p71) |
| 3 | Lücke zwischen Historie und Datenbeginn bei einem Start mitten im Monat | `p76 --erster-monat` lädt auch den ersten vorhandenen Monat. Eingefügt wird mit INSERT OR IGNORE, vorhandene Zeilen bleiben. **Jede überlappende Zeile** wird gegen den Bestand verglichen (`p77`, Abweichung > 1e-9 relativ). Bei einer systematischen Abweichung wird nicht gemessen |
| 4 | Lauf B ohne Änderung am Betriebscode | `p78` liest den Quelltext von `rechne` und ersetzt **genau zwei** Stellen (Schrumpfung ab 2020-07, Lernbeginn 2020-06-01). Mit den Betriebswerten rechnet diese Kopie auf `data/` **zeilengleich** zur Referenz (nachgewiesen 23.10. 17:06, 10.732 = 10.732). Lauf A ruft den Erzeuger unverändert auf |
| 5 | Monate ohne Modell | Bei weniger als 5.000 Treffern bleibt der Monat ohne Einstiege. Das ist die Regel des Erzeugers; die Monate werden ausgewiesen |
| 6 | Zielgröße | wie p71: Schluss der Einstiegsstunde bis Schluss 24 h später, minus 0,48 %, Tag = UTC-Tag der Einstiegsstunde. Einstiege ohne Kurs werden gezählt und ausgewiesen |
| 7 | Permutation | Strecken-Permutation über das ganze Raster 2020-07-01 bis 2026-08-31, 1.000 Ziehungen. Im Selbsttest (a) durchläuft jeder Zufallsfilter **alle drei** Kriterien, mit 200 inneren Ziehungen |
| 8 | Kriterium (1) | über den ganzen Zeitraum, ohne Mindestzahl an Tagen *aus* |
| 9 | Auskunft E-133 | die sechs Filter mit den Regeln aus p71, lang gerechnet ab 2020-06 (Nasdaq ab 2018 für den 200-T-Schnitt). Sie fließen nicht ins Urteil |

**Werkzeuge:**
- `p76_hist_download.py` (Download, SHA-256);
- `p77_hist_aufbau.py` (Aufbau `data/_hist`, Abgleich);
- `p78_regel0_lauf_ab.py` (Lauf A/B, `--probe` = R-R11 der Kopie);
- `p79_f1_fg_gier.py` (Selbsttest, dann Messung).

## 7. Ergebnis 24.10.2026 — F-1 Fassung 2 abgebrochen; die REGEL0 hängt an der Datenlänge (E-136)

Nutzer 24.10.: *„E1 A“*.

### 7.1 Daten (`data/_hist/`, nicht versioniert)

| Schritt | Ergebnis |
|---|---|
| Download `p76` | 4.715 Monatsdateien + 127 erste Monate, alle SHA-256 gültig, 154 MB |
| Aufbau `p77` | 94 von 127 Symbolen mit Historie (die übrigen erst mit Bestandsbeginn gelistet), 1.043.913 neue Zeilen, Übergang lückenlos bei allen |
| Abgleich Überlappungsmonat | 57 von 62.359 Zeilen weichen ab. In der Stichprobe (7 Symbole, 35 Zeilen) ist die **Archivkerze von data.binance.vision abgeschnitten** (open = high = low = close, nur der erste Handel); der Bestand hat die volle Kerze |
| Zweiter Weg `p77b` | ganze Historie über die REST-Schnittstelle (Quelle des Bestands): von 1.035.809 Zeilen 1.035.634 gleich, 135 abweichend (38 flach) und durch REST ersetzt, 40 nur im Archiv (etwa eine je Symbol, offen ohne Belang), 0 nur in REST |

### 7.2 Läufe (`p78`, Betriebscode unverändert)

| | Monatsmodelle | Einstiege |
|---|---|---|
| R-R11 heute (`data/`) | 32 | 10.732 = Referenz, alle Spalten |
| R-R11 der Lauf-B-Kopie mit Betriebswerten | 32 | 10.732 = Referenz |
| **Lauf A** (2024-01 bis 2026-08) | 32 | 11.701 |
| **Lauf B** (2020-07 bis 2023-12) | 37 (2020-07 bis 11 ohne Modell) | 1.714, **nur 2023** |

### 7.3 Befund 1 — die REGEL0 feuert 2020 bis 2022 nicht

- **2022:** v-dach liegt selbst im 99,9. Perzentil bei −0,43 %; die Schwelle ist +3,5 %. Die Streuung des Modellbeitrags ist dort 0,027, 2023 sind es 0,082.
- **2021:** 4.278 Stunden liegen über der Schwelle. Es sind 189 Läufe an 6 Tagen, **alle nach einer Ankerlücke** binnen 48 h (Datenlücken über alle Assets). Die Ruheregel verwirft sie zu Recht (`p80` G3).
- **Folge:** Kriterium (2) („6 von 9 Halbjahren ab 2020-H2“) ist nicht erfüllbar. Die Messung könnte nur „trägt nicht“ ergeben, ohne etwas über Fear & Greed zu sagen. Der Filter wurde **nicht angesehen**.

### 7.4 Befund 2 — das Ergebnis hängt an der Datenlänge

Dieselbe Regel, dieselben Monate 2024–26, nur mit der Vorgeschichte ab 2019 (netto je Handel nach 0,48 %):

| | Handel | netto |
|---|---|---|
| Referenz (Daten wie im Betrieb) | 10.732 | **+0,153 %** |
| Lauf A | 11.701 | **−0,340 %** |
| — gemeinsame Einstiege | 6.122 | +0,079 % |
| — nur Lauf A | 5.579 | −0,799 % |
| — nur Referenz | 4.610 | +0,251 % |
| Lauf B (2023) | 1.714 | −0,229 % |

- Nur 37,5 % der Einstiege sind gleich.
- Die Verschiebung zeigt sich bei Assets mit Bestandsbeginn vor 2023 (+0,088 / −0,933 / +0,300 %) genauso wie danach (+0,074 / −0,726 / +0,225 %). Sie liegt also nicht an einigen neu gereiften Werten, sondern an der ganzen Rechnung: Reife, Normal, Schrumpfung über den Querschnitt, Trainingsmenge.
- **Einordnung (R-R11):** Das widerlegt die REGEL0 nicht; sie wurde mit einer anderen Basis gerechnet. Aber das Plus von +0,15 % hängt daran, **wann für jedes Symbol die Datensammlung begann**. Das ist keine Regel, sondern ein Merkmal der Grundgesamtheit.

### 7.5 Gegenprobe (`p80_gegenprobe_historie.py`, 3/3)

- **G1:** Lauf A über die Kommandozeile des Erzeugers ist zeilengleich zu p78 (11.701).
- **G2:** Der Nettoertrag, je Einstieg per SQL über den Stundentext gerechnet (ohne Raster), ergibt dieselben Werte samt Zerlegung.
- **G3:** Alle 189 Läufe über der Schwelle 2021 folgen auf eine Ankerlücke.

### 7.6 Folge (E-136)

- F-1 Fassung 2 ist **abgebrochen**.
- Fear & Greed bleibt **Fakt im Lagebild** (L6, E-137).
- **Betrieb unverändert:** Die REGEL0 läuft als Vorwärtsprotokoll weiter, mit dem Vorbehalt „Ergebnis nicht robust gegen die Datenlänge“.
- **Nächster Schritt:** Voranalyse Robustheit der REGEL0. Welcher Baustein macht den Unterschied: Reife (Reihenbeginn `st0`), eigenes Normal, Schrumpfung, Trainingsmenge des Monatsmodells? Das ist messbar, je Baustein einzeln umgeschaltet auf `data/_hist`.
