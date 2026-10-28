# Voranalyse DVOL / Angstmaß — Stufe 0 Machbarkeit (26.10.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

Nutzer 26.10.: *„ja DVOL Stufe 0 starten - prüfen gegenprüfen und doku“*. Vorher: *„u.U. kann der Indikator auch für andere Assets oder Strategien genutzt werden und bringen einen Vorteil“*.

**Was DVOL ist:** Der Deribit-Volatilitätsindex ist die **implizite** 30-Tage-Schwankung aus BTC- bzw. ETH-Optionen. Er sagt, wie viel Bewegung der Optionsmarkt erwartet und wofür er bezahlt; er ist ein **Angstmaß**. Die **Angstprämie** (Varianzprämie) ist DVOL minus der tatsächlich gemessenen Schwankung.

**Bezug zu Bekanntem:**
- Fear & Greed ist der einzige Kandidat aus dem Indikator-Atlas (E-135: Vorlauf an BTC-Wenden, Rang 0,97 in beiden Hälften). Gemessen als Bewertung wurde er nie, weil F-1 Fassung 2 abbrach (E-136).
- Deribit wird im Betrieb schon gelesen (Put-Skew als Zusatzinfo), DVOL nicht.

⚠️ **Stufe 0 heißt: kein Ergebnis.** Geprüft wird nur, ob die Frage mit unseren Daten **auflösbar** ist; das Muster ist p91 (L2-a) und p96 (ETF).

## 1. Festlegung VORAB (26.10.2026) · `Rechenkern_02_10/p98_dvol_machbarkeit.py`

| | Festlegung |
|---|---|
| **Laden** | Deribit `public/get_volatility_index_data`, BTC und ETH, Auflösung 1 Tag, seitenweise über `continuation` ab Beginn (2021-03) → `data/_dvol/dvol.csv` (Tagesschluss). Einmal, frei, ohne Schlüssel |
| Fear & Greed | Atlas-Zustand aus `data/_ra/p75_zustaende.csv` (+1 = Wert < 25 „extreme Angst“), schon lokal |
| Kurse | BTC/ETH-Tagesschluss (CoinMetrics, `p91.kurse`) |
| REGEL0-Einstiege | Referenz und Lauf A mit 24-h-Ertrag vor Kosten (`p95.handel`) |
| **Zustände** (am **Vortag** bekannt) | **D1** DVOL im **oberen Fünftel** ihres wachsenden Fensters (ab Beginn, mindestens 180 T) · **D2** Angstprämie = DVOL − gemessene 30-T-Schwankung (aufs Jahr, %) im oberen Fünftel ihres wachsenden Fensters · **D3** Fear & Greed < 25. Für ETH gelten ETH-DVOL und ETH-Schwankung |
| **Teil A — Lage BTC/ETH** | Ertrag 7 T und 30 T ab Schluss t. Je Zustand: Tage, Anteil *an*, **Strecken**; Orakel-Rang; **Fehlalarm** (100 Zufallszustände mit derselben Streckenstruktur, Rang ≥ 0,95 als Treffer); **Auflösung** (Pflanzung auf *an*-Tagen: 7 T +0,5/1/2/3 Pp, 30 T +2/4/8 Pp; X = kleinste Stärke mit ≥ 80 % Fund) |
| **Teil B — Umfeld der REGEL0-Einstiege aller Assets** | je Tag das **Mittel** des 24-h-Ertrags der Einstiege (Tagesklammer), Zustand des Vortags (BTC-DVOL bzw. F&G). Strecken über die Einstiegstage; Fehlalarm wie oben; Pflanzung +0,25/0,5/1 Pp je Tag |
| **Messbar, wenn** | Teil A: Fehlalarm ≤ 5 % **und** X ≤ 2 Pp (7 T) · Teil B: Fehlalarm ≤ 5 % **und** X ≤ 0,5 Pp in **beiden** Mengen (die Größenordnung des REGEL0-Vorsprungs in der Referenz) |
| **Folge** | messbar ⇒ Messplan Stufe 1 (Richtung zweiseitig, Selbsttest, Norm-Blöcke) zur Abstimmung · nicht messbar ⇒ DVOL und Angstprämie nur als **Fakt** im Lagebild (Vorschlag) |
| Gegenprüfung | DVOL-Werte an 5 zufälligen Tagen gegen eine zweite API-Abfrage (`get_index_price`/Einzelabfrage) bzw. Plausibilität (BTC-DVOL 2022 > 2024); Streckenzahl über eine eigene Schleife |

**Ehrliche Erwartung:** DVOL ist ein Marktzustand, und solche Zustände wechseln selten. Ich erwarte dieselbe Grenze wie bei L2-a und den ETF-Flüssen. Teil B hat mehr Fälle, die Einstiegstage ballen sich aber (E-138: 27–28 Episoden).

## 2. Fassung 1 — Fehler in der Zustandsdefinition D1/D2, Fassung 1b VORAB (26.10.2026; `p98_dvol_fassung1.txt`)

| Zustand | Anteil *an* (Teil A BTC / ETH) | Strecken | in Teil B (2024–26) |
|---|---|---|---|
| D1 DVOL oberes Fünftel, **wachsendes** Fenster | **1 % / 3 %** | 19 / 23 | **0 %** (1–3 Strecken) |
| D2 Angstprämie, wachsendes Fenster | 4 % / 9 % | 63 / 57 | 2 % |
| D3 Fear & Greed < 25 | 22 % | 219 | 23–24 %, 39 Strecken |

- **Eigener Planungsfehler:** Die DVOL ist seit 2021 **strukturell gefallen**, mit dem Median je Jahr von BTC 89,6 → 73,0 → 50,6 → 56,4 → 45,7 → 39,9. Im **wachsenden** Fenster bleiben die hohen Werte von 2021/22 maßgeblich, und spätere Angstphasen erreichen das obere Fünftel nie. Das ist dasselbe Muster wie beim Klima q im ETF-Markt (E-69: q nie über 0,90). D1/D2 messen so den Zeitraum 2021/22, nicht die Angst.
- **D3** ist sauber definiert. Fassung 1: Teil A mit X = 3 Pp (BTC 7 T) über der Grenze von 2 Pp; Teil B ohne Auflösung bis 1 Pp ⇒ **nicht messbar**. D3 bleibt in Fassung 1b unverändert und wird nicht neu gewählt.

**Fassung 1b (vorab, vor jedem Ergebnis):**
- D1 und D2 werden als **oberes Fünftel des rollenden Fensters der letzten 365 T** gebildet (mindestens 180 T), also Angst **relativ zum aktuellen Niveau**.
- Alles andere bleibt wie §1, auch die Grenzen.

## 3. Ergebnis Fassung 1b — NICHT MESSBAR (26.10.2026; `p98_dvol_machbarkeit.py` → `.txt`)

**Teil A — Lage BTC/ETH, Ertrag 7 T** (Grenze: Fehlalarm ≤ 5 %, X ≤ 2 Pp):

| Zustand | an | Strecken | Fehlalarm | Fund +1 / +2 / +3 Pp | Urteil |
|---|---|---|---|---|---|
| BTC D1 DVOL (rollend 365 T) | 10 % | 43 | 2 % | 12 / 35 / 60 % | nicht messbar |
| BTC D2 Angstprämie | 13 % | 107 | 3 % | 13 / 39 / 68 % | nicht messbar |
| BTC D3 Fear & Greed < 25 | 22 % | 219 | 6 % | 23 / 50 / 89 % | nicht messbar (X = 3 Pp) |
| ETH D1 | 18 % | 121 | 5 % | 21 / 45 / 62 % | nicht messbar |
| ETH D2 | 17 % | 75 | 1 % | 19 / 33 / 58 % | nicht messbar |
| ETH D3 | 22 % | 219 | 3 % | 17 / 33 / 65 % | nicht messbar |

30 T (Auskunft): keine Auflösung bis 8 Pp.

**Teil B — Umfeld der REGEL0-Einstiege aller Assets** (Tagesmittel 24 h; Grenze X ≤ 0,5 Pp in beiden Mengen):

| Zustand | Referenz: an · Strecken · Fehlalarm · Fund +1 Pp | Lauf A: an · Strecken · Fehlalarm · Fund +1 Pp |
|---|---|---|
| D1 BTC-DVOL | 14 % · 16 · 6 % · 41 % | 16 % · 16 · 3 % · 46 % |
| D2 Angstprämie | 12 % · 36 · 6 % · 27 % | 13 % · 44 · 2 % · 42 % |
| D3 Fear & Greed | 24 % · 39 · 4 % · 48 % | 23 % · 39 · 6 % · 52 % |

⇒ **In keinem Fall auflösbar.** Selbst +1 Pp je Tag auf alle Einstiege wird höchstens zu 52 % gefunden.

**Gegenprüfung:**
- DVOL an 5 zufälligen Tagen gegen Einzelabfragen: **5/5 gleich**.
- Streckenzahl über eine eigene Schleife: gleich (Prüfung im Skript).
- Plausibilität: BTC-DVOL 2022 (73) > 2024 (56) ✔.

**Ursache (aus den Zahlen):**
- Es gibt **zu wenige unabhängige Angstphasen**: Seit 2021 kommen D1/D2 auf 43–121 Strecken, in den Einstiegsjahren 2024–26 auf nur **16–44**.
- Der Ertrag einer Angstphase ist eine einzige, stark streuende Größe. Wie bei L2-a (E-151), Ballungstagen (E-157) und ETF-Flüssen (E-158) fehlen **Wechsel**, nicht Tage.
- **Fear & Greed** (D3, Atlas-Kandidat) teilt dieses Schicksal: 219 Strecken über 8 Jahre, Auflösung erst ab 3 Pp je 7 T.

**Folge (vorab):**
- DVOL, Angstprämie und Fear & Greed nur als **Fakt** im Lagebild, nicht als Auslöser oder Gewicht.
- DVOL ist neu im Fakt-Teil und würde als Zeile gebaut, wenn du das willst.
- Fear & Greed steht dort schon.

## 4. L7 im Lagebild GEBAUT (27.10.2026; Nutzer: *„DVOL-Zeile ins Lagebild wenn sinnvoll so das ich etwas damit anfange als information“*, E-161)

**Was die Zeile sagt** (Beispiel vom 27.10.):

> **L7 Erwartete Schwankung (DVOL):** BTC-DVOL 38,1: Optionsmarkt erwartet ±2,0 % je Tag, ±11 % in 30 T · im Jahresvergleich ruhig (Perzentil 27 %) · Angstprämie +12,8 Pp gegen gemessene 25 % · ETH-DVOL 53,1 (ruhig)

| Teil | Bedeutung | Wozu |
|---|---|---|
| ±x % je Tag / in 30 T | DVOL ÷ √365 bzw. × √(30/365): die vom Optionsmarkt **erwartete** Bewegung (1 σ) | Stop- und Liquidationsabstand einordnen: Liegt er innerhalb der erwarteten Tagesbewegung, ist er bei normalem Markt schnell erreicht |
| Jahresvergleich | Perzentil im rollenden Jahr: sehr ruhig ≤ 20 % · ruhig · mittel · erhöht ≥ 60 % · hoch ≥ 80 % | Ist die Erwartung **für die jüngste Zeit** hoch oder niedrig? |
| Angstprämie | DVOL minus gemessene 30-T-Schwankung (Coinbase-Kurs, FRED) | positiv und groß: Der Markt zahlt für Absicherung mehr, als sich der Kurs bewegt |
| Einordnung (Spalte „gemessen“) | *Fakt, keine Regel: als Signal und als Umfeld der Einstiege nicht auflösbar (E-160)* | kein Auslöser, kein Gewicht |

**Bau** (`agent/makro_lage.py`):
- `hole_dvol` (Deribit, frei, eine Abfrage je Währung, 400 T); `dvol_fakt`; Zeile L7 in `gesamtmarkt`; Kurzform „BTC-DVOL 38 (±2,0 %/Tag)“ in der Mailzeile; Datenstand „DVOL“.
- **Eigener Fehlerpfad:** Ist Deribit nicht erreichbar, steht dort *„DVOL nicht verfügbar“*, und alles andere bleibt unverändert.
- Statusseite und GUI zeigen die Zeilen allgemein an; nur die Beschriftung ist auf L1–L7 geändert.
- L6 (Fear & Greed): Die Einordnung ist auf E-160 nachgezogen (*als Signal und als Umfeld nicht auflösbar* statt *als Regel offen*).

⚠️ **Fehler beim Bau gefunden und vor dem Commit behoben:** Die neue Warnmeldung des DVOL-Fehlerpfads schrieb den Ausnahmetext **ungefiltert** ins Log. Im Prüfstand-Fall „Quelle weg“ stand darin der **FRED-Schlüssel**: in der lokalen Testausgabe, nicht im Repository und nicht am NB.
- Jetzt ist er maskiert wie in den übrigen Fehlerpfaden (`***`).
- Der Prüfstand **p81 G5** liest das Log mit und verlangt, dass der Schlüssel darin nicht vorkommt.
- In keiner versionierten Datei steht der Schlüssel (geprüft mit `git grep`).

**Prüfung:**
- p81 **9/9**: G3/G7 auf 7 Zeilen nachgezogen; neu **G9** prüft L7 live, die Plausibilität, den Pfad ohne DVOL, Mailzeile und Datenstand; G5 prüft das Log ohne Schlüssel.
- Suite: Gesamtmarkt, Geheimnisse und Schlüsselwache grün; Makro zeigt nur den bekannten NFCI-Fall.

**NB:** K-DVOL-1 im nächsten Export (Statusseite L7, Log ohne „DVOL nicht abrufbar“).
