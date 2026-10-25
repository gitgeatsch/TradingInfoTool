# Voranalyse L2-a — Regime-Hebel auf dem Kern (25.10.2026)

Nutzer 25.10.: *„ja L1-a, L2-a und Kern-Regel Voranalyse starten - was ist mit den andern Werten also den aussichtsreichsten TOP Werten, diese wollen wir auch hebeln bzw. wenn die Strategie für Kern funktionieren sollte wäre dies auch eine Variante für andere Hebelpositionen oder?“*

**Herkunft:** Lösungsvorschlag L2-a aus E-146 (Voranalyse L1/L2 §9.2). Den Kern länger zu halten trug 2024–26 nicht, 2023 war es deutlich positiv. Das Vorzeichen hängt am Regime. Die Frage lautet also: **Lässt sich das Regime vorab erkennen, sodass der Hebel nur dann läuft?**

⚠️ **Das ist eine Voranalyse, keine Messung.** Ein echter Kandidat ist **nicht** bewertet. Gemessen wird erst nach deinem Ja zum Messplan (§5).

**Feste Regeln für diese Voranalyse:**
- Neutral: Ertrag **vor** Kosten, Vorsprung gegen eine Nullwelt. Gebühren sind ein späterer Schritt (Regel 2, Nutzer 25.10.).
- Der Kern BTC/ETH/SOL ist immer zugelassen (§8.0 der Voranalyse L1/L2).
- Ins Messregelwerk: `messnorm._block(h)`, mindestens 20 Blöcke, Urteilsstufen, Nullpunkt.

## 1. Was schon gemessen ist (Vorwissen, R-R11)

| Befund | Frage | Ergebnis | Was das für L2-a heißt |
|---|---|---|---|
| **E-126 M-A** (Spot §60) | BTC ↔ EURCV nach dem 10-Monats-Schnitt, 2011–2026 | **trägt nicht**. Ausstieg 54–158 T nach dem Hoch, Wiedereinstieg 50–199 T nach dem Tief. Die Monate draußen waren im Mittel **positiv** | ⚠️ Ein **langsamer Trendfilter** (200-T-Schnitt) ist praktisch dieselbe Frage. Erwartung für R1: **eher nein** |
| **2.599** | schneller Regimewechsel bei BTC | trägt nicht | kein schneller Filter |
| **E-133 F-1** | sechs Marktfilter für REGEL0 (u. a. BTC 200 T, Makro kurz) auf 2024–26 | **nicht entscheidbar**: selbst das Orakel erreicht nur Rang 0,92–0,94 (22 Strecken in 20 Monaten) | Auf 2024–26 allein ist die Frage **zu kurz** — deshalb hier ab 2015 |
| **E-117 W3** | BTC 7 T als Gewicht für REGEL0 | Vorprüfung NEIN, Vorzeichen wechselt 2025/26 | kurzer Impuls trägt nicht |
| **E-146 L-2** | Kern 24/72/168 h halten | 2024–26 trägt nicht bis 1/2/2 Pp; 2023 +5,5 % (168 h), KEIN BEFUND | das Regime entscheidet das Vorzeichen |

⚠️ **Ehrlich vorab:** L2-a mit einem Trendfilter wiederholt im Kern E-126 — nur auf dem **7-Tage-Horizont** (Hebel statt Spot) und mit **ETH/SOL**. Ein anderes Ergebnis als E-126 wäre nach R-R11 nur dann ein Befund, wenn die Messung E-126 zuerst reproduziert (§5, Schritt 0).

## 2. Machbarkeit (`Rechenkern_02_10/p91_l2a_voranalyse.py` → `.txt`)

**Daten (frei, am Desktop):** BTC/ETH Tagesschluss aus CoinMetrics (`data/_spot/coinmetrics.db`), SOL aus den Binance-Stundenkursen (`data/_hist`, 23:00). Zielgröße: Ertrag 7 T ab jedem Tag, ohne Kosten.

**Positivkontrolle (Orakel):** ein Regime mit Zukunftswissen (kommender 30-T-Mittelwert des 7-T-Ertrags > 0). **Fehlalarm-Probe:** Zufallsregime mit derselben Streckenstruktur wie jeder Kandidat. Rang gegen Strecken-Permutation.

| Kandidat (alle am Vortag bekannt) | Zeitraum | Anteil an | Strecken | Fehlalarm BTC / ETH / SOL | Orakel | Machbar? |
|---|---|---|---|---|---|---|
| **R1** BTC über 200-T-Schnitt | 2015–2026 | 60 % | 72 | **2 % / 6 % / 5 %** | 1,000 | ✔ **messbar** |
| **R2** BTC 91 T > +20 % (Season B1) | 2015–2026 | 40 % | 138 | 6 % / 4 % / 3 % | 1,000 | ⚠️ grenzwertig (BTC 6 %) |
| **R3** Season-Ampel nicht kalt | 2019–2026 | 37 % | **3** | 0 % | 1,000 | ✖ zu wenige Strecken |
| **R4** Makro Gesamt kurz kein Gegenwind | 2020–2026 | 64 % | 91 | **10 %** / 6 % / 5 % | 1,000 | ✖ Fehlalarm zu hoch |

- **Die Auflösung reicht** auf der langen Historie (Orakel überall Rang 1,000). Auf 2024–26 allein reichte sie nicht (E-133). **Die Länge ist hier die Lösung.**
- **Der Prüfstand ist nur für R1 sauber** (Fehlalarm ≤ 5 % bei BTC). R2 und R4 überschreiten den Sollwert; sie würden falsche Treffer liefern.
- R3 hat nur 3 Strecken. Mit 3 Wechseln kann nichts belegt werden.

## 3. Deine Frage: die aussichtsreichsten Top-Werte hebeln

**Kurz: Ja, das ist die richtige Fortsetzung, aber erst in Stufe 2.**

| | |
|---|---|
| **Warum es übertragbar wäre** | Ein Regime ist eine Eigenschaft des **Marktes**, nicht eines Coins. Trägt ein Regime-Hebel auf dem Kern, ist er ein Kandidat für alle Hebelpositionen. Die Altcoins hängen sogar stärker am BTC-Regime als der Kern (Beta > 1) |
| **Warum nicht gleich** | (1) Auf dem Kern ist es billiger zu prüfen: lange Historie, kein Auswahlschritt. (2) Bei den Top-Werten kommen zwei Unbekannte zusammen — die **Auswahl** und das **Regime**. Trägt das Ganze nicht, wüsste man nicht, woran es lag |
| **Was über die Top-Werte schon bekannt ist** | Die Auswahl (oberes Fünftel B4) schlägt die eigene Gruppe auf 1 Monat (Top 30 +3,5 Pp/M), **nicht** BTC (E-143). Auswahl × 24-h-Einstieg trägt nicht bis 0,5 Pp (E-144). Ab 2024 liegt das obere Fünftel der Top 30 nahe BTC |
| **Was L-1 für den Hebel bedeutet** | Die gescheiterte Brücke (CMC → Binance) betrifft die **Bestätigung 2017–19** und die Werte **außerhalb** von Binance. Für den Hebel zählt das kaum: Gehebelt wird nur, was bei Bitpanda handelbar ist, und dafür gibt es die Binance-Reihen ab 2019 |
| **Stufe 2 (nur wenn Stufe 1 trägt)** | Derselbe Regime-Hebel auf (a) die **Top 30** gleich gewichtet und (b) die **Top 30 im oberen Fünftel**. Gemessen gegen den Kern im selben Regime: bringt die Auswahl im Regime **zusätzlich** etwas? |

⚠️ Die **Kern-Regel** (Aufbau 70/20/10, Klima-Ampel) ist eine **Spot**-Regel und kein Hebel. Sie lässt sich nicht auf Hebelpositionen übertragen. Übertragbar ist nur ein Regime-Hebel aus L2-a.

## 4. Was gemessen werden kann und was nicht

| | |
|---|---|
| ✔ messbar | R1 auf BTC, ETH, SOL; Stabilität über zwei Hälften |
| ⚠️ nur Auskunft | R2 (Fehlalarm über dem Soll). Werte stehen daneben, entscheiden nicht |
| ✖ nicht messbar | R3 (3 Strecken), R4 (Fehlalarm 10 %, beginnt erst 2020) |
| ✖ nicht Teil der Frage | Gebühren und Finanzierung (nachgelagert, erst nach belegtem Vorsprung) |

## 5. Messplan-Vorschlag L2-a Stufe 1 (zur Abstimmung, NICHT festgelegt)

| | |
|---|---|
| **Schritt 0 (R-R11)** | E-126 auf dem eigenen Prüfstand **reproduzieren**: BTC, 10-Monats-Schnitt, Monatswerte 2017–2026 → Ergebnis wie E-126 „trägt nicht“. Ohne Reproduktion wird Stufe 1 nicht bewertet |
| **Kandidat** | R1: BTC-Tagesschluss am Vortag über dem eigenen 200-T-Schnitt → Regime *an* |
| **Werte** | BTC, ETH, SOL einzeln; je ab 200 T nach Datenbeginn (BTC/ETH 2015/16, SOL 2021) bis 2026-09 |
| **Zielgröße** | Ertrag 7 T vor Kosten (Kern-Haltedauer aus L-2) |
| **Vorsprung** | Mittel an *an*-Tagen minus Mittel aller Tage |
| **Nullwelt** | Strecken-Permutation, 1.000 Ziehungen; Nullpunkt = Mittel der Nullwelten |
| **Band** | zirkulärer Tagesblock-Bootstrap mit `messnorm._block(7)` = 21 T, AK-Prüfung `pruefe_block`; mindestens 20 Blöcke je Teilmenge, sonst KEIN BEFUND |
| **Selbsttest vor dem ersten Blick** | Fehlalarm auf 100 Zufallsregimen mit R1-Struktur ≤ 5 %; Pflanzung als Auflösungskurve (+0,5 / +1 / +2 / +3 Pp je 7 T an *an*-Tagen), Grenze X = kleinste Stärke mit ≥ 80 % Fundquote |
| **Urteil (Stufen)** | **TRÄGT**: Rang ≥ 0,95 bei BTC **und** bei mindestens einem von ETH/SOL, **und** in beiden Hälften (2015–2020 / 2021–2026) positiv · **TRÄGT NICHT BIS X**: Band schließt X aus · **NICHT TRENNBAR**: Band enthält null und X · **KEIN BEFUND**: < 20 Blöcke |
| **Ausweis** | je Epoche (ETF-Markt ab 11.01.2024 gesondert, Gewicht wie üblich), BTC-Schwankung je Hälfte |
| **Zweiter Weg (Gegenprobe)** | Vorsprung über eine eigene Schleife je Tag und über Monatsmittel statt Tageswerte |
| **Folge, vorab** | trägt → Stufe 2 Top 30 (§3) · trägt nicht → festhalten; Hebel bleibt bei REGEL0 (E-36) · nicht trennbar → keine weitere Fassung mit Trendfiltern (E-126 + L2-a sind dann zwei Wege mit demselben Ergebnis) |

⚠️ **Regel 1 und Regel 4:** Das Regime ist ein **Zustand**. Es wäre nur dann eine Begründung, wenn es nachweislich etwas über die kommenden 7 Tage sagt. Genau das prüft Stufe 1. Bis dahin ist R1 ein Fakt für die Mail.

## 6. Zwischenfazit zum Ziel

- **Ziel:** eine neutrale Aussage über das Potential je Asset und Handlung. Für den Hebel heißt das: *wann lohnt ein Hebel auf dem Kern überhaupt?*
- **Stand:** Auf 2024–26 ist die Frage nicht entscheidbar (E-133). Auf der langen Historie ist sie messbar, aber nur für **einen** Kandidaten (R1), und der ist mit E-126 schon einmal gescheitert.
- **Ehrliche Erwartung:** eher „trägt nicht“. Die Messung ist trotzdem billig (Minuten) und schließt die Frage auf dem 7-Tage-Horizont sauber ab.
- **Alternative, falls R1 nicht trägt:** kein weiterer Trendfilter. Dann wird die Frage zum Ertrag des Kerns über die **Haltedauer im Regime** (L-2) nicht weiterverfolgt, und der Hebel bleibt bei REGEL0.
