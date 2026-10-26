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
