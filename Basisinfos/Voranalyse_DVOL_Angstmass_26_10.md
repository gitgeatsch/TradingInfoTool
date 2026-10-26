# Voranalyse DVOL / Angstmaß — Stufe 0 Machbarkeit (26.10.2026)

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
