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
