# Voranalyse F-1 — REGEL0 nur handeln, wenn der Gesamtmarkt nicht gegen uns steht (Marktfilter, auf Bitpanda) — ab 23.10.2026

**Wozu:** Nutzer 23.10.: *„ja F-1 Messplan festlegen, prüfen, gegenprüfen und Doku“*. Sein Hinweis:
> *„wir sollten diese Themen breiter denken und berücksichtigen, z. B. ist die größte Bremse scheinbar nicht im einzelnen Asset-Bereich, Strategie etc., sondern offenbar müssen wir mehr und besser im Bereich Gesamtmarkt sein, z. B. wie lange und warum steigt der Markt, und wann und warum fällt dieser – hier wären wir wieder bei Makro und traditionellen Märkten (Nasdaq, Zinsen, Anleihen etc.).“*

## 1. Der Hinweis ist durch unsere Messungen gestützt

| Befund | Quelle |
|---|---|
| Das **Regime** wiegt zwölfmal mehr als die Lage eines Assets (Jahresdrift-Spanne 0,087 gegen 0,007) | 2.598 |
| REGEL0 schlägt den Markt derselben Coins um +0,6 / +0,3 Pp je 24 h; die **fallende Marktdrift** plus Kosten zehrt das auf | E-131 |
| 2024 (steigender Markt) brachte REGEL0 vor Kosten **+0,95 %** je Handel, 2025–26 nur +0,12 bis +0,33 % | 2.690 |
| E-A: Kauf-Timing im fallenden Markt Rang 0,99, im steigenden 0,03 | E-132 |

⇒ Die größte Stellschraube ist der **Gesamtmarkt**, nicht das Asset.

## 2. Was zum Gesamtmarkt schon gemessen ist (Vorwissen)

| Messung | Frage | Ergebnis | Unterschied zu F-1 |
|---|---|---|---|
| 2.599 | Ist der Marktzustand (BTC-Trend u. a.) vorab erkennbar, für den Hebel-Ertrag je Stunde? | nein (`btc_trend` ≈ Zufallsreihe) | F-1 misst den **Netto-Ertrag nach BP-Kosten** der REGEL0-Handel, ein/aus |
| W3 (E-117) | BTC 7 T als **Gewicht** für REGEL0 | nein, Vorzeichen wechselt 2025/2026 | kurzer Trend; F-1 nimmt langsame Zustände und Makro |
| O49 Makro-Umfeld (Spot §51) | Richtung BTC / Altkorb über 90 T aus 9 Makrokanälen (Geldmenge, Netto-Liquidität, Realzins, Zinspfad, Kurve, Kredit, NFCI, Dollar, VIX) | **0 von 60, nicht entscheidbar**: 13 Jahre sind nur drei Zyklen. Beste Kandidaten: Netto-Liquidität kurz und Dollar kurz | Zielgröße dort: Richtung über Monate. F-1: REGEL0-Handel über 24 h, **viele Handel je Zustand** |
| O53 (Schritt7 §23.56) | Makro als **Risikobremse** für REGEL0 (tiefster Stand) | nicht belegt; die ATR trägt das Makro schon mit | F-1 misst den **Ertrag**, nicht das Risiko |
| M-A (Spot §60) | Trendallokation BTC ↔ EURCV | trägt nicht (Verspätung) | F-1 sperrt nur den **kurzen Handel**, kein Halten |

⚠️ **Ehrlich vorab:**
- Die effektive Fallzahl ist die **Zahl der Zustandswechsel**, nicht die der Handel (2.599).
- REGEL0-Einstiege gibt es für 2024-01 bis 2026-08. Langsame Zustände wechseln dort nur wenige Male.
- Gut möglich ist deshalb das Urteil *„nicht entscheidbar“*. Ausgewiesen wird es mit der Auflösung.

## 3. Die Filter — vorab, ohne Parametersuche, aus dem bestehenden Schema

| # | Filter (*an* = handeln) | Quelle und Berechnung |
|---|---|---|
| F1 | **Makro Gesamt kurz** ≠ Gegenwind | `agent/makro_lage.scores` (wie Statusseite und O54, R-R11), Verzug je Reihe |
| F2 | **Makro Gesamt lang** ≠ Gegenwind | dto. |
| F3 | **K2 Netto-Liquidität kurz** ≠ Gegenwind | dto.; bester Kanal in O49 |
| F4 | **K8 Dollar kurz** ≠ Gegenwind | dto.; zweitbester Kanal in O49 |
| F5 | **Nasdaq** über seinem 200-Tage-Schnitt (FRED `NASDAQCOM`, Vortag) | traditioneller Risikomarkt |
| F6 | **BTC** über seinem 200-Tage-Schnitt (Tagesschluss Vortag, CoinMetrics) | Krypto-Gesamtmarkt |

Der Zustand gilt für den **Einstiegstag** und ist am Vortag bekannt (Verzug wie in `makro_lage.REIHEN`).

## 4. Messplan F-1 Fassung 1 — VORAB festgelegt

| | festgelegt |
|---|---|
| Handel | REGEL0-Einstiege (`kern48jbz_einstiege_<menge>.csv`), vier Mengen, 2024-01 bis 2026-08; Ertrag 24 h nach Kosten **0,48 %** (Bitpanda-Hebel) |
| Zielgrößen je Filter, Jahr und Menge | netto je Handel **an** · netto je Handel **aus** · **Gesamtertrag je Kalendertag** mit Filter gegen ohne (Summe der Nettoerträge ÷ Tage) |
| **trägt, wenn** | (1) **Umkehr:** netto *aus* < 0 **und** netto *an* > 0, in **2025 und 2026**, in **allen drei unverzerrten** Mengen (Jahre mit < 30 Tagen *aus* zählen nicht); **und** (2) Nullwelt-Rang der Verbesserung (netto *an* minus netto alle) ≥ **0,99** (Bonferroni 0,05 ÷ 6), gepoolt 2025–26 |
| **Nullwelt** (R-R14: keine Zeitverschiebung bei trägen Reihen) | **Permutation der Zustandsstrecken**: die Folge der an- und aus-Strecken des Filters je Tag wird zufällig umgeordnet, Längen und Anteil bleiben; 1.000 Ziehungen |
| **Selbsttest VOR dem ersten Blick** | (a) **Fehlalarm:** 200 Zufallsfilter mit derselben Streckenstruktur wie F1 gegen die echten Handel → Anteil „trägt“ ≤ 5 %; (b) **Positivkontrolle:** ein Filter mit bekannter Wahrheit (an, wenn der zentrierte 30-Tage-Mittelwert des REGEL0-Tagesnettos > 0; mit Vorgriff, nur als Prüfung) muss Rang ≥ 0,99 erreichen. Fällt (a) oder (b) durch, wird nicht gemessen |
| **Auflösung** | je Filter die Zahl der Zustandswechsel 2024–26; Pflanzprobe: +0,3 Pp auf die *an*-Tage eines Zufallsfilters → Fundquote. Reicht sie nicht, heißt das Urteil „nicht entscheidbar“, nicht „trägt nicht“ |
| Auskunft | 2024 je Filter; Kombination „alle sechs an“; Anteil der Tage *an* |
| Folgen | **trägt** → Messplan Fassung 2 als Bestätigung auf Spot-Kosten (Fusion 0,50 %) und **Voranalyse Gesamtmarkt-Modul** (Phasen, Dauer, Ursachen; Nutzerhinweis). **Nicht entscheidbar / trägt nicht** → Gesamtmarkt bleibt Fakt in der Mail; die breitere Frage *„wie lange und warum steigt oder fällt der Markt“* wird als eigene **Recherche + Messung über lange Historie** (BTC ab 2013, Nasdaq ab 1971) vorgeschlagen |
