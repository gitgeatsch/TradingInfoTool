# Voranalyse (b): Was könnte überhaupt noch einen Vorsprung liefern? (26.10.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

Nutzer 26.10.: *„c - prüfen gegenprüfen und doku“* (zuerst das NB-Bündel, dann diese Voranalyse).

**Frage:** Welche **kostenfreien** Daten haben wir für einen Vorsprung je Asset und Handlung noch nicht genutzt? Und ist die Frage mit ihnen **fachlich beantwortbar**, bevor gemessen wird?

**Vorgehen (bestehendes Schema zuerst):** Es gibt kein neues Inventar. Grundlage sind die bestehenden: Spot §27.2 und §45 (Quellenprobe U1–U10), Schritt7 §23.22 (Ereignisse), §23.71/§23.72 (Nachrichtenarchiv), E-125 (LLM-Bilanz). Neu geprüft wurden heute nur zwei Quellen, die dort fehlten oder sich geändert haben könnten.

## 1. Was schon gemessen ist — vollständig

| Familie | gemessen | wo | Ergebnis |
|---|---|---|---|
| Kurs, Umsatz | 11+ Merkmale, Momentum, Boden, Tiefe, Dauer, Alter | Spot §19, §35, §37, §40 | Bewegung statt Richtung; nur **defensiv** (Fortbestand) |
| Terminmarkt | Funding, OI, Käuferanteil, Top-Trader-Long/Short, Taker | Spot §35, F-164 ff., N-f | trägt keine Richtung |
| On-Chain / Fundament | aktive Adressen, TVL gegen Kurs, Gebühren-Wachstum, Halter-Einnahmen, MVRV je Coin, Stablecoins je Kette | Spot §19, §45, §46 | ab 2024 **kein Einstieg belegbar** (§46.6) |
| Ereignisse | Binance (1.009), Upbit, DefiLlama-Hacks | §23.22, §23.71 | selten; **Verkaufsanlass** (B3), kein Einstieg |
| Nachrichten | 9 RSS-Feeds im Wayback-Archiv, 39.926 Meldungen 2025–26 | §23.71, §23.72, E-125 | Abdeckung: 51–200 nur 8 %, außerhalb Top 200 0,2 %; LLM ohne Mehrwert |
| Markt / Regime | Liquidität, Makro, Dominanz, Season, Klima, Trendfilter | Spot §8, §16, §60; E-126, E-133, E-151 | nur Fakt; Regime **nicht entscheidbar** (zu wenige Wechsel) |
| Auswahl (B4-Wert) | Watchlist-Fünftel | E-143, **E-154** | ordnet den Fortbestand; Monatsvorsprung zeitrichtig **nirgends belastbar** |

## 2. Heute geprüft (Proben, je eine Abfrage, nichts geladen)

| Quelle | Probe | Ergebnis |
|---|---|---|
| **Token-Freigaben** (DefiLlama `/emissions`) | Abfrage 26.10. | **402 Payment Required**: Die Quelle ist inzwischen kostenpflichtig. ✘ Projektregel *nur kostenfrei*. Damit bleibt die Verwässerung ein **Fakt aus der Mengenänderung** (P22), kein Kalender |
| **Wikipedia-Seitenaufrufe** (Wikimedia, frei) | Wikidata P5777 (CMC-Kennung): 131 Coins, davon **50** mit englischem Artikel. Reihen: BTC/ETH/DOGE/LTC ab 2015; LINK, ADA, DOT erst ab 2021 (Umbenennung kappt die Reihe); XRP auf dem falschen Artikel (189 Aufrufe im Monat) | bestätigt Spot §45 U8: **Abdeckung zu dünn**, Zuordnung brüchig. ✘ |

## 3. Ist die Frage noch fachlich beantwortbar?

- **Zeitreihen-Fragen** (Marktphase, Regime) sind mit unseren Jahren **nicht** auflösbar. Selbst 12 Jahre BTC haben nur 72 Regimewechsel (E-151).
- **Querschnitts-Fragen** (Coin gegen Coin am selben Tag) haben genug Beobachtungen. Dort sind **alle freien Quellen gemessen**: Kurs, Terminmarkt, On-Chain, Fundament, Ereignisse, Nachrichten.
- Was übrig bleibt, ist entweder **kostenpflichtig** (Freigabekalender, Liquidationshistorie, Börsenbestände, Social X/Reddit, Google Trends ohne offizielle Schnittstelle) oder **zu dünn** (Wikipedia, GitHub ≈ ⅓, DEX-Umsatz 8 Coins).
- ⇒ **Mit freien Daten ist die Suche nach einem Einstiegsvorsprung erschöpft.** Ein weiterer Messlauf auf derselben Datenlage wäre Mehrfachtesten.

## 4. Was das System heute nachweislich kann

| Teil | Stand |
|---|---|
| **Führung des Bestands** | B1 Mitnahme ×3, B3 Upbit-Listing, B4 Abbau-Reihenfolge: gemessen, gebaut, im Betrieb |
| **Fortbestand ordnen** | B4-Fünftel auf 12 M (E3 −19,4 bis +11,4) |
| **Lage als Fakt** | Lagebild Gesamtmarkt, Makro, Season-Ampel, Klima |
| **Hebel** | REGEL0 im Betrieb, Vorsprung **nicht robust** (E-136/E-139); Hebelführung H15, Messstand im Betrieb |
| **Kern** | Sparplan des Nutzers; die alte Kette fragt nicht mehr (K-4) |

## 5. Entscheidung (eine, mit Alternativen)

| | Weg | Bewertung |
|---|---|---|
| **(a) Vorschlag** | **Suche abschließen.** Das System bleibt ein **Fakten- und Führungssystem**: Bestand führen, Fortbestand ordnen, Lage zeigen, REGEL0 mit dem Vorbehalt *„nicht robust“* weiter im Messstand des Betriebs. Weiterentwickelt wird, was trägt (Führung, Ordnung), statt neuer Einstiegsmessungen | ehrlich zur Datenlage; keine weitere Messrunde ohne neue Information |
| (b) | **CryptoCompare/CoinDesk-Data mit kostenfreiem Schlüssel** (du legst das Konto an): lückenloses Nachrichtenarchiv | niedrige Erwartung: E-125 und §23.72 zeigen, dass die Abdeckung bei den Coins des linken Endes fehlt, nicht die Lücken im Archiv |
| (c) | **Projektregel „nur kostenfrei“ überdenken** (Freigabekalender, Liquidationen, Börsenbestände) | **deine** Grundsatzentscheidung. Ich empfehle sie nicht und schlage sie nicht vor; sie ist der einzige offene Hebel |

## 6. Gegenprüfung dieser Voranalyse

- **Vollständigkeit:** Jede Zeile in §1 ist gegen ihre Fundstelle nachgelesen (Spot §45.1/§45.2/§46.6, Schritt7 §23.71/§23.72, E-125, E-151, E-154). Keine Quelle aus den Inventaren §27.2, §45 und §23.22 fehlt.
- **Die zwei neuen Proben** sind je eine Abfrage. Es wurde nichts geladen und nichts gespeichert.
- **Gegenläufige Prüfung:** Wikipedia hätte Spot §45 U8 (≈ 8 % Abdeckung) widerlegen können. Die Probe über Wikidata (50 Coins mit Artikel) bestätigt U8.
