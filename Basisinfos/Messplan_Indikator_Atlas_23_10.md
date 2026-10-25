# Messplan Indikator-Atlas (V-1) — Was bewegt den Gesamtmarkt? Fassung 1, VORAB festgelegt (23.10.2026)

**Wozu:** Nutzer 23.10.: *„ja V-1“*. Seine Gedanken dazu:
> *„Hier sollte man unterscheiden zwischen Marktindikatoren, z. B. Geldausweitung – steigt BTC auch ohne, oder ist dies Voraussetzung? Und ich denke, Krypto-Indikatoren hängen im Wesentlichen davon ab. Rezession? Wie lange haben wir die Geldmengenausweitung, wie lange haben wir bereits Bullenmarkt im Indexbereich? Die aktuelle Phase ist generell problematisch – Anleihen im kritischen Bereich, Währungen in der Krise, KI-Investitionen tragen nicht, Krisen (z. B. Corona) haben zu massiver Geldausweitung geführt. Das solltest du gesondert messen und ggf. recherchieren, da wir dies u. U. für die letzten 10 Jahre kaum messen können.“*

Herkunft: E-133 (Marktfilter nicht entscheidbar), E-134 (H-A Voranalyse, zwei Phasenebenen).

**Was der Atlas ist:** eine **Beschreibung mit Prüfung gegen den Zufall**, kein Signal. Ein Vorlauf in der Rückschau wird erst zum Kandidaten, wenn er in **zwei getrennten Zeiträumen** besteht. Getestet wird er dann auf ungesehenem REGEL0-Handel (F-1 Fassung 2).

## Aufbau in vier Teilen

| Teil | Frage | Daten | Zeitraum |
|---|---|---|---|
| **T1 Krypto-Atlas** | Welche Indikatoren drehten **vor** (Vorlauf) bzw. **nach** (Nachlauf) den Wendepunkten des Kryptomarkts, und welche blieben neutral? Je Ebene und je übergeordnetem Umfeld | BTC (CoinMetrics), Makrokanäle K1–K9 und Gesamt (`makro_lage`), Nasdaq, Stablecoin-Menge, Funding, Fear & Greed, BTC-Dominanz (CMC-Wochen) | 2013–2026 bzw. ab Verfügbarkeit |
| **T2 Voraussetzung Geld** | Steigt BTC auch **ohne** Geldausweitung, oder ist sie eine Voraussetzung? | US-M2 J/J, Netto-Liquidität der Fed, Notenbank-Bilanzen Fed + EZB + BoJ in USD (J/J); BTC-Phasen | 2013–2026 |
| **T3 Lange Historie traditioneller Märkte** | Brauchen Aktien-Bullenmärkte Geldausweitung? Wie lange dauern Geldausweitungen und Bullenmärkte? Was passiert in und vor Rezessionen? Wo stehen wir heute (Reifegrad)? | Nasdaq (1971), M2 (1959), NBER-Rezessionen (1854), Zinskurve 10J–2J (1976) und 10J–3M (1982), Fed Funds (1954), Sahm-Regel (1959) | 1959/1971–2026 |
| **T4 Recherche Lage 10/2026** | Anleihen, Währungen, KI-Investitionen, Geldmenge, Rezessionsrisiko; Literatur zum Zusammenhang BTC–Liquidität und BTC–Nasdaq | Quellen mit Zitat, Fakt und Erzählung getrennt | aktuell |

## T1 Krypto-Atlas

| | festgelegt |
|---|---|
| Wendepunkte | BTC **übergeordnet**: Bärenphasen ≥ −50 % vom Allzeithoch (6 Phasen = Hoch- und Tief-Wenden). **Kleiner**: Zickzack −20 % / +25 % (86 Wenden). Jede kleine Wende wird mit ihrem übergeordneten Umfeld markiert (Bullen- oder Bärenphase) |
| Indikatorzustand | je Indikator eine vorab feste Zustandsregel (+1 günstig / −1 ungünstig): Makrokanäle und Gesamt wie `makro_lage` (Drittel); Nasdaq über 200 T; Stablecoin-Menge 91 T > 0; Funding 30-T-Mittel unter / über dem eigenen 1-Jahres-Median (hohes Funding = ungünstig); Fear & Greed < 25 = günstig (Angst) / > 75 = ungünstig; BTC-Dominanz 30 T steigend = ungünstig für Altcoins |
| **Vorlauf** | vor einer **Hoch**-Wende wechselt der Indikator binnen W Tagen auf ungünstig, vor einer **Tief**-Wende auf günstig. W = 30 Tage (klein), 90 Tage (übergeordnet). **Nachlauf** entsprechend danach |
| **Nullwelt** | dieselbe Zahl **Zufallsdaten** im selben Zeitraum, 1.000 Ziehungen. Ausgewiesen werden Lift und Rang |
| **Kandidat, wenn** | Vorlauf-Rang ≥ 0,95 in **beiden** Hälften (2013–2019 und 2020–2026, soweit der Indikator dort vorhanden ist) **und** Lift > 1 in beiden. Die übergeordnete Ebene bleibt **beschreibend** (zu wenige Fälle) |
| **Selbsttest VOR dem ersten Blick** | (a) Zufallsindikatoren (Strecken-Permutation einer echten Zustandsreihe) → Anteil „Kandidat“ ≤ 5 %; (b) ein gebauter Indikator, der 10 Tage vor jeder Wende wechselt, muss als Kandidat erkannt werden |

## T2 Voraussetzung Geldausweitung (Nutzerfrage)

| | festgelegt |
|---|---|
| Zustand Geld | (i) US-M2 J/J > 0; (ii) Netto-Liquidität (WALCL − TGA − RRP) 26 W > 0; (iii) Notenbank-Bilanzen Fed + EZB + BoJ in USD, J/J > 0. Jeweils mit Verzug wie in `makro_lage` |
| Fragen | (a) **Anteil der BTC-Aufwärtsstrecken** (kleine Ebene, +25 %), die **ganz in einer Phase ohne Ausweitung** lagen, gegen den Zeitanteil dieser Phasen; (b) BTC-Ertrag 90 T je Zustand; (c) **übergeordnete Bullenphasen**: lag jeweils Ausweitung vor? (beschreibend, 4 Fälle) |
| **Voraussetzung belegt, wenn** | in Phasen ohne Ausweitung lag (a) **deutlich unter** dem Zeitanteil (Rang ≤ 0,05 gegen Surrogate der Geldreihe nach R-R14, Phasen-Randomisierung, 500 Ziehungen) **und** das gilt für mindestens zwei der drei Geldmaße |
| Auskunft | 2023: US-M2 schrumpfte, die Fed baute die Bilanz ab, und BTC stieg trotzdem um +154 %. Ob die Netto-Liquidität (Abbau der RRP) das erklärt, wird hier sichtbar |

## T3 Lange Historie traditioneller Märkte

| | festgelegt |
|---|---|
| Bullen-/Bärenmarkt | Nasdaq-Tagesschluss, Bärenmarkt = Rückgang ≥ 20 % vom Hoch (gängige Definition), 1971–2026 |
| Fragen | (a) **Dauer** der Bullenmärkte und der M2-Ausweitungen (Verteilung); (b) Anteil der Bullenmarkt-Monate **mit** gegen **ohne** M2-Ausweitung; (c) Nasdaq in und vor **NBER-Rezessionen** (Rückgang, Dauer); (d) **Vorlauf der Zinskurve**: Inversion 10J–2J bzw. 10J–3M → Rezessionsbeginn (Abstand in Monaten, Fallzahl); (e) **Reifegrad heute**: Dauer des laufenden Bullenmarkts und der laufenden Ausweitung als Perzentil der Geschichte |
| Bewertung | **beschreibend** (7–9 Rezessionen, ~10 Bärenmärkte). Kein Signal, sondern Fakt und Lagebild |

## T4 Recherche

Lage im Oktober 2026, mit Quelle und Zitat, Fakt und Erzählung getrennt:
- Anleihen: Renditen, Laufzeitprämie, Defizite;
- Währungen: Dollar, Yen, Euro;
- KI-Investitionen: Investitionsausgaben gegen Erträge, Bewertungen;
- Geldmenge und Notenbanken;
- Rezessionsindikatoren;
- dazu die Literatur zu BTC und Liquidität sowie zu BTC und Nasdaq (Korrelation seit 2020).

## Folgen (vorab)

| Ergebnis | Folge |
|---|---|
| T1-Kandidaten vorhanden | REGEL0-Historie 2020–23 (Download-Ja) und **F-1 Fassung 2** nur mit diesen Kandidaten |
| T1 keine Kandidaten | der Atlas bleibt **Fakt** (Statusseite, Mail); F-1 Fassung 2 entfällt oder läuft nur mit den sechs Filtern aus E-133 (Nutzerentscheidung) |
| T2 Voraussetzung belegt | sie wird **Fakt-Zeile** „Geldausweitung: ja/nein“ samt Befund; eine **Bremse** nur nach eigener Messung auf REGEL0 |
| T3 | **Lagebild Gesamtmarkt** (Reifegrad, Rezessionsampel) als Fakt auf der Statusseite, nach Abstimmung |

⚠️ **Regeln 1–4:** Dauer und Reifegrad sind **Fakten**, nie Auslöser (Regel 1, kein Kalendersignal). Kein Asset-Vorurteil. Ein Vorlauf in der Rückschau ist **keine Begründung** (Regel 4), bis er getestet ist.

## Ergebnis Fassung 1 (23.10.2026; `p73_atlas_t3_lang.py`, `p74_atlas_t2_geld.py`, `p75_atlas_t1_krypto.py`, `p75_gegenprobe.py` → `.txt`)

### T1 Krypto-Atlas: Selbsttest bestanden, ein Kandidat

**Selbsttest:**
- Zufallsindikatoren (Strecken-Permutation): **0 von 200** als Kandidat gewertet ✔.
- Der gebaute Vorlauf-Indikator wurde erkannt ✔.

**Kleine Ebene** (86 BTC-Wendepunkte, Zickzack −20 % / +25 %, W = 30 T). Vorlauf-Quote, dahinter der Zufallswert und der Rang:

| Indikator | 2013–2019 | 2020–2026 | Einordnung |
|---|---|---|---|
| **Fear & Greed** (< 25 günstig, > 75 ungünstig) | **69 % / 46 % / 0,97** (n 13, ab 2018) | **50 % / 31 % / 0,97** (n 26) | **einziger Kandidat**. ⚠️ Er wird zum Teil aus Kurs, Schwankung und Volumen berechnet, ist also eher **gleichlaufend an Extremen** als ein unabhängiger Vorlauf. Nachlauf 2020–26 ebenfalls hoch (0,93) |
| Makrokanäle K1–K9, Makro gesamt kurz und lang | durchweg im Zufallsband (Ränge 0,04–0,92) | dto. | **kein** Vorlauf auf der kleinen Ebene |
| Nasdaq über 200 T | 5 % / 15 % / **0,00** | 0 % / 11 % / **0,00** | dreht **seltener** nahe den Wendepunkten als zufällig: ein **träger** Trendzustand |
| Stablecoins 91 T | 0 % / 16 % / **0,00** | 0 % / 4 % / **0,00** | dto. (vor 2020-10 unvollständig) |
| Funding BTC 30 T | – | 20 % / 21 % / 0,35 | kein Vorlauf |
| BTC-Dominanz 4 W | 37 % / 36 % / 0,44 | 54 % / 50 % / 0,58 | kein Vorlauf |

**Übergeordnete Ebene** (6 Bärenphasen, W = 90 T, beschreibend): Seit 2017 wechseln vor den großen Wendepunkten **mehrere** Indikatoren, besonders Fear & Greed, Dominanz, VIX, Dollar und Kredit. Bei 4 Zyklen ist das aber eine Beschreibung, keine Regel. Die Matrix steht in `p75_atlas_t1_krypto.txt`.

### T2 Voraussetzung Geldausweitung (Nutzerfrage): **nicht belegt**

| Geldmaß (ab) | Zeit ohne Ausweitung | Aufwärts-Tage ohne Ausweitung | Rang (≤ 0,05 = Voraussetzung) | BTC 90 T mit / ohne | Aufwärtsstrecken ganz ohne |
|---|---|---|---|---|---|
| (i) US-M2 J/J (2014) | 10 % | 14 % | 0,89 | +18 / +25 % | 1 von 42 |
| (ii) Netto-Liquidität 26 W (2013) | 47 % | 48 % | 0,54 | **+37 / +17 %** | 8 von 42 |
| (iii) Bilanzen Fed + EZB + BoJ J/J (2014) | 40 % | 38 % | 0,37 | +21 / +15 % | 5 von 42 |
| Auskunft reales M2 | 19 % | 20 % | 0,50 | +19 / +17 % | 3 von 42 |

- BTC stieg in Phasen **ohne** Geldausweitung etwa so oft wie mit.
- Der Zyklus **2022-11 bis 2025-10 (BTC × 7,9)** lief zu **99 % der Tage bei schrumpfenden Notenbank-Bilanzen** (Fed-QT).
- ⇒ Geldausweitung ist **keine Voraussetzung**. Bei der Netto-Liquidität bleibt ein **Niveau**-Unterschied (+37 % gegen +17 % über 90 T), der in O49 nicht Bonferroni-fest war.
- ⚠️ **Eigener Fehler, vor der Bewertung behoben:** Die Nullwelt verglich zuerst nur den Anteil der Aufwärts-Tage statt der **Differenz zum Zeitanteil**, wie in §T2 (a) festgelegt. Die erste Fassung meldete beim realen M2 fälschlich Rang 0,04.

### T3 Lange Historie traditioneller Märkte (beschreibend)

| | Befund |
|---|---|
| Nasdaq-Bärenmärkte (≥ −20 %) 1971–2026 | **13**; Bullenmärkte im Median **60 Monate** (18–239) |
| heute | Bullenmarkt seit dem Tief vom **08.04.2025** (18 Monate; der Rückgang 12/2024–04/2025 war −24 %); seit dem großen Tief vom 28.12.2022 **46 Monate** ohne −30 % |
| Nominales M2 | schrumpfte seit 1960 **nur einmal** (12/2022–03/2024), und gerade dann lief ein Nasdaq-Bullenmarkt (15 von 15 Monaten) |
| Reales M2 | 12 Schrumpfungen; Bullenmarkt-Anteil der Monate **82 %** bei wachsendem gegen **80 %** bei schrumpfendem realem M2 ⇒ auch bei Aktien **keine Voraussetzung** |
| **Rezessionen** (NBER, 7 seit 1971) | der Nasdaq fiel **jedes Mal**, vom Hoch der 12 Monate davor um −24 bis −68 % ⇒ **die stärkste Größe** |
| **Zinskurve** | vor jeder Rezession 1980–2008 invertiert, mit 4–33 Monaten Vorlauf. **Die Inversion 2022–2024 (26 Monate 10J–2J) blieb bisher ohne Rezession**, zum ersten Mal seit 1976 |
| Sahm-Regel / Fed Funds | **0,00** (09/2026) / 3,75 % |

### T4 Recherche Lage 10/2026 (Quellen im Recherchebericht; Fakt und Erzählung getrennt)

| Nutzerhypothese | Urteil | Kernzahl |
|---|---|---|
| Anleihen im kritischen Bereich | **teilweise gestützt** | US-10J 5,31 % (05.10., höchster Stand seit 2002), 30J 5,67 %; Laufzeitprämie 1,10 (höchster Stand seit 2010, Langfristmittel 0,82); Defizit 6,2 % des BIP, Zinslast +11 %; Spread Frankreich 120–147 Bp; Auktionen intakt |
| Währungen in der Krise | **nicht** für USD, EUR, CNY; **teilweise** für den Yen (163,86 je USD, schwächster Stand seit 1986, Interventionen) und für ölimportierende Schwellenländer (Rupie-Rekordtief) | Broad Dollar 12 Monate ± 0 % |
| KI-Investitionen tragen nicht | **teilweise** | Capex der vier Großen 735–750 Mrd. USD 2026, freier Cashflow −24 %; **aber** Cloud-Umsatz +37 bis +82 %, S&P-Gewinne Q3 +29,6 %, KGV 19,1 |
| Krisen → massive Geldausweitung | **für Corona gestützt** (M2 +26,8 % J/J, Fed-Bilanz verdoppelt), **für 2026 nicht**: M2 +5,7 %, die Fed **erhöht** (16.09.: 3,75–4,00 %), Bilanz nur +0,2 Bio. USD |
| (implizit) Rezession droht | **derzeit nicht gestützt** | Sahm 0,00, GDPNow 3,6 %, Stellenzuwachs schwach (+29.000) |
| Auslöser 2026 | **Ölschock** (Brent 62 → 138 → 115 USD), Inflation 3,7 %, Zinserhöhungen von Fed, EZB und BoJ | |

- **BTC und der Aktienmarkt:** Die Tageskorrelation stieg von **0,02 (2017–19)** auf 0,37–0,59 (seit 2020); 2026 liegt sie bei 0,45 (eigene Rechnung, deckt sich mit dem IWF).
- **Die Trends laufen 2026 aber auseinander:** Nasdaq über 12 Monate +14 % und auf Allzeithoch, **BTC −26 %**, und das bei M2 +5,7 %. Die Liquiditätsthese erklärt 2026 **nicht**. Literatur: Karau 2023 (BTC reagiert erst seit Ende 2020 wie eine Risikoanlage), IWF-Arbeitspapier 2023/163.

### Zwischenfazit zum Ziel (fachlich, meine Einordnung)

1. **Die Nutzerfrage „Geldausweitung Voraussetzung?“ ist für BTC und für Aktien mit Nein beantwortet.** Geld wirkt höchstens auf das **Niveau** (Netto-Liquidität), nicht als Bedingung.
2. **Die stärkste Größe für den Gesamtmarkt ist die Rezession** (Aktien jedes Mal −24 bis −68 %). In der Krypto-Zeit gab es aber nur **eine** (2020). Der beste Vorläufer, die Zinskurve, hat 2022–24 zum ersten Mal **ohne** Rezession invertiert. Ein Rezessionssignal ist heute nicht aktiv.
3. **Kein Makrokanal läuft den BTC-Wenden auf der kleinen Ebene voraus.** Trendzustände (Nasdaq, Stablecoins) laufen nach. Nur Fear & Greed hält sich an den Extremen, ist aber zum Teil selbst aus dem Kurs gerechnet.
4. **Die Lage 2026 ist eine eigene Form:** ein Ölschock mit steigenden Zinsen, BTC löst sich vom Aktienmarkt. Sie passt zu keinem der früheren Muster. Das spricht dafür, den Gesamtmarkt als **Lagebild** zu zeigen (Fakt), nicht als Regel.

### Folge nach dem Messplan

**T1-Kandidat vorhanden** (Fear & Greed) ⇒ als nächster Schritt die REGEL0-Historie 2020–23 (Download-Ja) und **F-1 Fassung 2** nur mit diesem Kandidaten. Dazu, zur Abstimmung: das **Lagebild Gesamtmarkt** als Fakt (Reifegrad, Rezessionsampel, Geld, Anleihen, Öl).

**Gegenprobe 5/5:**
- G1: F&G-Quote per einfacher Schleife, gleich.
- G2: F&G-Rang mit anderem Startwert und 2.000 Ziehungen: 0,972 / 0,955.
- G3: Zickzack auf eigenem Weg: 86 Wenden.
- G4: T2-Anteil 47,8 %.
- G5: Nasdaq-Bärenmärkte per cummax: 13.
- ⚠️ G5 enthielt zuerst **einen eigenen Fehler**: Die Erwartung lautete „13 + 1 laufend“, aber T3 meldet einen laufenden **Bullen**markt. Korrigiert.

⚠️ **Berichtigung 25.10.2026 (E-141):** (a) Ein Nachlauf von Nasdaq/Stablecoins ist **nicht** belegt (Nachlauf-Ränge 0,05/0,07 und 0,00/0,33). (b) Fear & Greed ist ein Grenzfall: n = 13 in der ersten Hälfte, Gegenprobe 0,955. (c) T2 „keine Voraussetzung“ ist eine Beschreibung, kein Messbefund (nur Nicht-Verwerfen).
