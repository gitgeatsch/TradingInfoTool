# Datenbasis für Dashboard und LLM — Ebenen, Sichten, Inventar (28.10.2026 spät)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 28.10. spät):**
1. *„bevor wir starten reden wir über das Konzept und wie die LLMs gefüttert werden … Schichten … Sichten und Ereignisse … in optimaler Form zur Bewertung übergeben“*
2. *„bevor wir bauen und messen brauchen wir eine Basis: was wird nur abgerufen und angezeigt, was berechnen wir selbst und was benötigen die LLMs“*

**Gehört zu:** `Voranalyse_Dashboard_LLM_28_10.md` (Aufgaben A1–A6, Anbieter §1.5a) · `Bauplan_Dashboard_A3_A4_28_10.md` (wartet auf dieses Blatt).
**Erhoben:** aus Code, Jobs und Ablagen am Desktop, nur lesend. Die Fundstellen stehen im Sitzungsbericht. Was nur am NB belegbar ist, ist als **[NB offen]** markiert.

---

## 1. Das Ebenenmodell

| Ebene | Was | Wer | Kennzeichen | Beispiel |
|---|---|---|---|---|
| **0 Rohdaten** | abgerufen, unverändert | Datenquellen | Quelle, Abrufzeit | KOSPI-Schluss, US 2J, Funding BTC, Meldung „Binance will delist X“ |
| **1 Zustände** | aus Rohdaten **berechnet**, immer mit Einordnung | unser Code | **Fakt** | „Nasdaq 25 % über 200-T-Schnitt, höchstes Zehntel seit 2000“ |
| **2 Sichten** | Zustände + Ereignisse **eines Bereichs** gebündelt | Code; Ereignisse durch den LLM-Leser (A1) | Fakt / Ereignis mit Quelle | Sicht „Asien“: KOSPI −8 %, Meldung „Handelsstopp …“ |
| **3 Gutachten je Sicht** | *„Was heißt diese Lage für das Krypto-Risiko?“* | LLM | **Einschätzung, ungeprüft** | „Risiko erhöht, weil …; umstimmen würde mich …“ |
| **4 Abwägung je Asset (finales LLM)** | Asset-Fakten + Ergebnisse der Sichten + A3 (gemessene Befunde) + A4 (Gegenanwalt) → **Bedenken-Stufe mit Gründen** (§3a) | LLM, geprüft vom Code | je Zeile gekennzeichnet | die Asset-Karte |

### Die Regeln der Übergabe (warum die alte Kette scheiterte, und wie es diesmal anders wird)

| # | Regel | Grund |
|---|---|---|
| Ü1 | **Zustand statt Zahlenreihe**: Wert + Einordnung (Perzentil der eigenen Geschichte, Abstand zum Normalen, Richtung) | LLMs lesen beschriebene Lagen gut und Zahlenkolonnen schlecht |
| Ü2 | **Fakt und Bewertung getrennt**. „Überhitzt“ ist nie Ebene 1, sondern höchstens Ebene 3 | Prüffrage BEWERTUNG oder FAKT |
| Ü3 | Jede Angabe mit **Quelle, Zeitpunkt, Kennzeichen** | nur so prüfbar und protokollierbar |
| Ü4 | **Weitergabe zwischen LLM-Stufen nur strukturiert** (Kurzfeld + Beleg), kein Fließtext | sonst wachsen Fehler von Stufe zu Stufe |
| Ü5 | **Jede Stufe bringt NEUE Information** (Weltmärkte, Ereignisse, Befunde), nicht dieselben Kurszahlen ein zweites Mal | genau daran ist Lagebild → Trader → Entscheider gescheitert |
| Ü6 | **Jede Stufe einzeln protokolliert**. Ihr Beitrag ist messbar, indem man dieselbe Abwägung mit und ohne sie rechnet | sonst weiß niemand, welche Stufe trägt |
| Ü7 | Gutachter und Gegenanwalt **verschiedene Modelle** | damit die Irrtümer nicht gleich sind |
| Ü8 | **Dieselbe Form live und im Rückspiel** | nur dann ist eine Messung des Werts möglich |
| Ü9 | Kein Urteilswort, keine LLM-Wahrscheinlichkeit; **die Regel entscheidet** | LLM ist Prüfung, nicht Entscheider |

**Kontingente:**
- NB (Betrieb): Gemini-Schlüssel 1, 500 je Modell und Tag.
- Desktop (Tests und Messungen): Gemini-Schlüssel 2 als eigenes Projekt, dazu Groq gpt-oss-120b mit 200.000 Token/Tag und OpenRouter mit 1.000/Tag.
- Bedarf: 8 Sichten-Gutachten + höchstens 60 Asset-Karten am Tag. Das passt.

---

## 2. Inventar in drei Spalten

### 2.1 Nur ABGERUFEN und angezeigt (Ebene 0, kein eigener Rechenschritt nötig)

| Größe | Quelle, Takt | NB | Historie, Zeitpunkt des Bekanntwerdens (PIT) | angezeigt heute |
|---|---|---|---|---|
| Kurs, Marktwert, Volumen | CoinGecko, 15 min | ✔ | nur der jüngste Stand | Statusseite |
| Bestand frei + gestakt, Hebelpositionen | Bitpanda, 30 min | ✔ | Wertverlauf täglich | Statusseite |
| Binance-Ankündigungen (Delisting, Monitoring) | Binance CMS, stündlich | ✔ | Betrieb ab 10.10.; Archiv `data/_a1` lädt (V1); PIT ja | REGEL0-Mail, Statusseite |
| Upbit-Listings | Upbit, stündlich | ✔ | ab 12.10.; PIT ja | Mail B3, Statusseite |
| Termine FOMC, CPI, NFP | feste Liste + FRED | ✔ | entfällt | nur REGEL0-Mail |
| Fear & Greed | alternative.me, täglich | ✔ | 2018; Tagesreihe in `macro_snapshot` | im Lagebild |
| **Nachrichten** (9 Medien) | Wayback-Archiv | **✖ nur Desktop, kein Job** | 2019 bzw. 2024/25 bis 17.10.; PIT ja | **nirgends** |

### 2.2 Selbst BERECHNET (Ebene 1, Zustände mit Einordnung, alle Fakt)

| Zustand | Modul, Takt | Eingang | angezeigt | geht an ein LLM? |
|---|---|---|---|---|
| REGEL0-Signal, Lage zur Signalstunde | `regel0_rechnung`, stündlich | Stundenkerzen, Terminmarkt, Prämie | Statusseite, Mail | **ja**: Trader (Prüfblock) |
| Makro K1–K9 + Gesamt lang/kurz | `makro_lage`, 06:35 | 11 FRED-Reihen, Rang im 5-J-Fenster | Statusseite oben, Mails | nein |
| Lagebild L1–L7 (u. a. Nasdaq, Öl, HY, DVOL) | `makro_lage`, 06:35 | FRED, Deribit | Statusseite, Mails | nein |
| Season-Ampel B1–B3, Breite Top 50 | `season_ampel`, 07:30 | Kurse, Stablecoins | Statusseite, Mails | nein |
| Verwässerung 90 T + Fünftel | `verwaesserung`, je Mail | Umlaufmenge | Mails, Statusseite | nein |
| DVOL-Fakt (Perzentil, erwartete Bewegung) | `makro_lage`, 06:35 | Deribit | Statusseite, Mails | nein |
| Spot B1 Mitnahme, B3 Upbit, B4 Abbau-Ränge | `spot_*`, täglich bzw. stündlich | Kurse, Bestand | Mails, Statusseite | nein |
| Hebel H15 (Abstand, Warnstufe) | `hebelfuehrung`, 15 min | Kurs, Position | Statusseite, H15-Mail | nein |
| REGEL0-Messstand | `regel0_messstand`, 06:50 | Ablage | Statusseite, Mail | nein |
| **Spot-Großfluss je Asset** (G16, Nachtrag 31.10.) | **fehlt** — Rechnung `p102_wale_basis` (E nach Rest und Tagesbewegung, Fünftel 365 T), täglich ab 03:00 UTC | Binance-Spot `aggTrades` Tagesdatei des Vortags | **noch nirgends** → Asset-Karte (§8) | **ja**: als Fakt **und** mit Befund-Karten-Eintrag (A3) |

**Was heute an ein LLM geht:**
- Im Betrieb **nur** der REGEL0-Prüfblock. Der **Trader** bekommt Kerzen, Prämie und Terminmarkt; die Rolle **Markt** bekommt Liquidität, Zinskurve, F&G, S&P-Trend und CPI.
- **Alle anderen Fakten** (K1–K9, L1–L7, DVOL, Termine, Verwässerung, Ankündigungen, Upbit, Season) gehen nur in Mail und Statusseite.
- Das LLM kennt also heute weniger als du in der Mail.

### 2.3 Was die LLMs BRAUCHEN (Ebene 2–4) — Soll

| Aufgabe | braucht | vorhanden? |
|---|---|---|
| A1 Ereignis-Leser | Meldungen mit Zeitstempel (Binance, Upbit, Nachrichten) | Binance ✔, Upbit ✔; Nachrichten **nur Desktop-Archiv, kein Live-Job** |
| Sichten-Gutachten (Ebene 3) | Ebene-1-Zustände je Bereich **als Sätze** + Ereignisse | Zustände großteils ✔, Satzform **fehlt** (heute nur Mail-Text); Lücken §4 |
| A3 Befund-Gedächtnis | Befund-Karte (Auswahl aus dem Register) | Register ✔, Karte **fehlt** (B1) |
| A4 Gegenanwalt | Asset-Fakten + Sichten + A3 | nach Ebene 2/3 |
| Rückspiel zur Messung | dieselben Eingaben **mit Zeitpunkt des Bekanntwerdens** für 2025–26 | Marktkurse ✔ (werden nicht revidiert); Nachrichten ✔; FRED-Makro **nur nachgeladen** (Revisionen). Die freien FRED-Jahrgänge (ALFRED) könnten das lösen **[U]** |

---

## 3. Vorschlag: acht Sichten

| Sicht | Inhalt Ebene 1 (vorhanden) | Ereignisse | Lücke |
|---|---|---|---|
| **S1 Krypto gesamt** | BTC-Trend, Season-Ampel, Breite, DVOL, Stablecoin-Angebot, Funding/OI gesamt | Nachrichten (Krypto) | Basis der Quartalsfutures |
| **S2 Liquidität und Zinsen USA** | K1 Geldmenge, K2 Netto-Liquidität, K3 Realzins, K4 2J, K5 Kurve, 10J | Termine FOMC/CPI/NFP | – |
| **S3 Risikoappetit Weltmärkte** | S&P (SPY ab 1993), Nasdaq, VIX (K9), Kredit K6/HY, Finanzlage K7 | Nachrichten (Märkte) | – |
| **S4 Dollar und Rohstoffe** | Dollar K8 (Broad-Index, **nicht** DXY), Gold, Öl Brent/WTI | – | DXY selbst |
| **S5 Asien** | Upbit-Listings | Nachrichten | **KOSPI, Nikkei fehlen** |
| **S6 Staatsschulden und Anleihen** | US-Laufzeitprämie, 10J | Nachrichten | **Frankreich–Deutschland-Abstand fehlt** |
| **S7 Börsen- und Projektereignisse** | – | Binance, Upbit; GitHub später | Nachrichten live am NB |
| **S8 Termine** | FOMC, CPI, NFP mit gemessenem Faktor | – | – |

Je Asset kommen dazu: Kurs, Bestand, REGEL0, H15, Verwässerung, Ankündigungen zum Asset.

---

## 3a. Die FRAGE ist wichtiger als die Eingabe (Nutzer 28.10. spät)

> *„Was ist die Fragestellung an das LLM? Was soll uns das LLM1 zum Markt1 sagen bzw. als Ergebnis bringen, damit es ein Vorteil ist?“*
> *„alle Ergebnisse sind für ein FINALES LLM neue Informationen zur Bewertung“*

**Das trifft den Kern.** Die elf gescheiterten Wege haben fast alle **dieselbe** Frage gestellt: *„Wohin geht der Kurs in 24 h?“* Dabei ist ein LLM schwach, weil die Antwort nicht in den Eingaben steckt. Stark ist es, wo es **liest, Ungewöhnliches erkennt und abwägt**. Die Frage muss also so gestellt sein, dass genau das gefragt ist.

### Wann ein Ergebnis ein VORTEIL ist (Prüfstein für jede Frage)

| # | Bedingung | Gegenbeispiel |
|---|---|---|
| F1 | Es ist auf eine **Handlung** bezogen, mit **Zeithorizont** (REGEL0 24 h · Hebel Tage · Spot Wochen) | „der Markt ist bullish“ |
| F2 | Es meldet die **Abweichung vom Normalen**. An den meisten Tagen ist die richtige Antwort *„nichts Besonderes“* | jeden Tag eine Lageschilderung |
| F3 | Es sagt, ob das **neu** ist und ob der Kurs **schon reagiert** hat (*eingepreist?*) | eine Meldung, auf die der Markt längst reagiert hat |
| F4 | Es nennt **Wirkung auf Krypto** und **Richtung**: belastet / stützt / keine | eine Aussage über Aktien ohne Brücke zu Krypto |
| F5 | Es nennt den **Auslöser**, der die Einschätzung **kippen** würde | eine Einschätzung ohne Ablaufdatum |
| F6 | Es ist **messbar**: als Zustand, der sich gegen den späteren Verlauf prüfen lässt | Fließtext |

### Die Ergebnisform jeder Sicht (dasselbe Schema für alle, damit das finale LLM sie vergleichen kann)

| Feld | Werte |
|---|---|
| `zustand` | normal / auffällig / kritisch |
| `wirkung_krypto` | belastet / stützt / keine |
| `horizont` | Stunden / Tage / Wochen |
| `neu_seit` | Zeitpunkt, an dem der Treiber bekannt wurde |
| `eingepreist` | ja / teilweise / nein, mit Beleg (Kursreaktion) |
| `treiber` | höchstens 3, jeder mit Fakt-Schlüssel oder Meldung |
| `kippt_wenn` | Auslöser oder Termin |
| `gegenargument` | eines |

### Die Frage je Sicht (Entwurf, zur Besprechung)

| Sicht | Frage an das LLM | nutzt | gemessen gegen |
|---|---|---|---|
| S1 Krypto gesamt | *Ist die Krypto-Gesamtlage heute ungewöhnlich (Hebel überdehnt, Stablecoin-Abfluss, Breite bricht weg), und erhöht das das Risiko eines breiten Einbruchs in 1–7 Tagen?* | Hebel, REGEL0 | spätere Schwankung und Einbruch des Gesamtmarkts |
| S2 Liquidität, Zinsen | *Hat sich die Liquiditäts- oder Zinslage seit letzter Woche so verändert, dass Risikoanlagen in den nächsten Wochen belastet oder gestützt werden? Welcher Termin kann das kippen?* | Spot | Wochenertrag des Gesamtmarkts |
| S3 Risikoappetit | *Gibt es Stress an Aktien- oder Kreditmärkten, der in 1–7 Tagen auf Krypto übergreifen kann?* | Hebel, REGEL0 | Einbruchstage |
| S4 Dollar, Rohstoffe | *Bewegt sich Dollar, Gold oder Öl ungewöhnlich, und auf welchem Weg träfe das Krypto?* | Spot | Wochenertrag |
| S5 Asien | *Gibt es in Korea, Japan oder China ein Ereignis, das Krypto-Handel oder Liquidität direkt trifft (Börse, Regulierung, Yen)?* | alle | Einbruchstage, Upbit-Werte |
| S6 Staatsschulden | *Spitzt sich eine Schuldenlage zu (Auktion, Herabstufung, Zinsabstand springt), die Flucht aus Risiko auslösen kann?* | Hebel, Spot | Einbruchstage |
| S7 Ereignisse je Asset | *Welche Meldung betrifft Asset X direkt, ist sie neu, und hat der Kurs schon reagiert?* | alle je Asset | Ertrag des Assets nach der Meldung |

### Das FINALE LLM — die Frage, auf die alles zuläuft

Es bekommt **je Handlung** (Signal X, Bestand Y) die Asset-Fakten, die **Ergebnisse der Sichten** (nur das Schema oben, kein Fließtext), A3 (was gemessen gilt) und A4 (Gegenanwalt). Seine Frage:

> *„Spricht die Gesamtlage dafür, diese Handlung **wie geplant**, **vorsichtiger** (kleiner, kürzer, enger) oder **nicht** auszuführen? Nenne die zwei entscheidenden Gründe und was dich umstimmen würde.“*

Ergebnis: eine **Bedenken-Stufe** (0 / 1 / 2) mit Gründen.
- Das ist eine Bewertung, und genau die fehlt heute.
- Sie **entscheidet nicht**. Sie steht in der Mail.
- Sie bekommt **Gewicht erst dann, wenn die Messung zeigt**, dass Handlungen mit Stufe 2 schlechter liefen als mit Stufe 0 (Regel: *das LLM erzeugt Information, die Messung bestimmt ihren Wert*).

### Warum das messbar ist — und was gemessen wird

| Stufe | Frage der Messung | Weg |
|---|---|---|
| jede Sicht | Kommen auf „kritisch“ wirklich häufiger Einbrüche als auf „normal“? | Rückspiel 2025–26, gpt-oss-120b (sauber), nur Eingaben mit Zeitstempel (Marktkurse, Nachrichten, Ankündigungen) |
| finales LLM | Liefen Handlungen mit Bedenken 2 schlechter als mit 0? | dasselbe Rückspiel auf den REGEL0-Einstiegen 2025–26 |
| Beitrag je Sicht | Wird das finale Urteil schlechter, wenn man die Sicht weglässt? | dieselbe Abwägung mit und ohne die Sicht (Ü6) |

⚠️ **Ehrlich:**
- Im Rückspiel fehlen die FRED-Makrowerte mit Zeitstempel (§4). S2 ist deshalb erst prüfbar, wenn die FRED-Jahrgänge nachgewiesen sind oder das Protokoll lange genug läuft.
- Die Sichten S1, S3, S4 (Marktkurse), S5 und S7 (Nachrichten, Ankündigungen) sind **jetzt** prüfbar.

---

## 4. Lücken und freie Wege

| Lücke | freier Weg | Stand |
|---|---|---|
| **Nachrichten live am NB** | dieselben 9 RSS-Feeds direkt abrufen (das Archiv ist ihr Spiegel) | Job fehlt; klein |
| **KOSPI, Nikkei** | yfinance `^KS11`, `^N225` (yfinance ist im Projekt schon im Einsatz) | **[U]** Abdeckung prüfen |
| **Frankreich–Deutschland 10J** | FRED-Langfristzinsen je Land, **nur monatlich** **[U]**; täglich frei nicht bekannt | prüfen |
| **DXY** | yfinance `DX-Y.NYB` (nur in der stillgelegten alten Kette) | vorhanden, nicht angebunden |
| **Basis Quartalsfutures** | Binance-Lieferkontrakte über die öffentliche Schnittstelle **[U]** | prüfen |
| **Spot-Großfluss live am NB** (§8) | Binance-Spot `aggTrades` Tagesdateien (data.binance.vision), wie `wale_s2_laden.py`. **Gemessen** (Monatsdateien 06–08/2026, zip): 127 Altcoins zusammen **32 MB/Tag**, die 40 größten 24 MB, Median 0,12 MB; BTC/ETH/SOL nicht gezählt **[U]** | Job fehlt; Historie 365 T per USB |
| **Historie von K1–K9 / L1–L7** | die Tageswerte wären aus FRED nachrechenbar, aber revidiert; Lösung über die FRED-Jahrgänge **[U]**. Ab jetzt **protokollieren** (V6) | Protokoll fehlt |

**[U]** heißt ungeprüft. Jeder dieser Wege wird vor dem Bau mit **einem** Abruf nachgewiesen (Datenquellen-Inventar + Abdeckung, am NB).

---

## 5. Widersprüche aus der Erhebung, nachzuziehen

1. **Voranalyse §1.3 „Makro ohne Historie“ stimmt nur zur Hälfte.**
   - Richtig für K/L: `makro_lage.json` wird überschrieben.
   - F&G, Netto-Liquidität und Zinsen stehen aber täglich in `macro_snapshot`, DVOL und Skew in `externe_reihe` (ab 17.08.).
2. **`regel0_llm.yaml`** hat `mail_block: true` und `schatten: true` zugleich. Der Code gibt `mail_block` den Vorrang, der Block wird gemailt. Die Kommentarzeile zu `schatten` ist missverständlich.
3. **Verwässerung am NB:**
   - Der 90-T-Vergleich braucht Werte von vor dem 30.07.; die NB-Reihe beginnt um den 08.09.
   - Vermutlich zeigt der NB deshalb bis etwa Dezember **keinen** Wert. **[NB offen]**, im nächsten Export zu prüfen.
4. **K8 „Dollar“** ist der Broad-Index DTWEXBGS, nicht der DXY. Die Benennung muss das sagen.
5. **`Kette_Landkarte.md`** beschreibt die stillgelegte alte Kette. Sie ist Geschichte, nicht der Ist-Stand.
6. **DVOL wird zweimal abgerufen** (`makro_lage` und `externe_reihe`).
7. **Lebendigkeit (TVL, Entwickler)** wird am NB geschrieben, aber ein Leser im heutigen Betrieb ist nicht gefunden (*Stilllegung: wer schreibt das noch*).

---

## 6. Reihenfolge danach

1. Dieses Blatt abstimmen: Sichten und Reihenfolge (§7).
2. Lücken nachweisen (je ein Abruf) und Satzform der Zustände festlegen (Ü1).
3. **Messplan:**
   - Faktentreue: die Prüfer bekommen einen Selbsttest mit 1.000 Fällen.
   - Wert der Sichten-Gutachten: Rückspiel 2025–26 mit gpt-oss-120b am Desktop, nur PIT-Eingänge.
4. **Bau:** B1–B6 aus dem Bauplan, erweitert um die Ebenen 2 und 3. Die Mail bekommt vorerst beide Blöcke (Nutzer 28.10.).

---

## 7. Zur Abstimmung — eine Frage

**Mit welchen Sichten beginnen wir?**

| | Weg | Folge | Einschätzung |
|---|---|---|---|
| **A** | **S1, S2, S3, S4, S7, S8 sofort**: alle aus vorhandenen Daten, dazu nur der kleine Nachrichten-Job am NB. **S5 und S6 folgen**, sobald KOSPI/Nikkei und der Frankreich-Abstand nachgewiesen sind | sechs Sichten in der ersten Stufe | **Empfehlung**: nichts wartet auf Unsicheres; die neuen Quellen kommen nach ihrem Nachweis |
| B | Erst alle Lücken schließen, dann alle acht Sichten | vollständig, aber später | hält das Vorhandene auf |
| C | Nur S1 Krypto und S7 Ereignisse | klein und schnell | lässt genau das weg, was du dir wünschst (Weltmärkte, Asien, Staatsschulden) |

---

## 8. Nachtrag 31.10.2026 — Wal-Verhalten (G16) eingereiht

**Nutzer 31.10.:** *„a“* — auf die Frage, wie G16 nach dem Ergebnis *„nicht für REGEL0“* weitergeht: **in Weg a einreihen**,
kein Sonderbau. Grundlage: Register `G16-wale-spot-f3`, `-alt-f4`, `-s2`, `-ursache` (Messplan Wale §13–§19).

| Teil | Form | Regel dahinter |
|---|---|---|
| **Zustand** (Ebene 1, Fakt) | ein Satz je Asset: *„Spot-Großfluss gestern: oberstes Fünftel der eigenen 365 Tage (Netto-Kauf)“* — mit Stand und Alter | Ü1 Zustand mit Einordnung · **F2: nur oberstes oder unterstes Fünftel** erscheinen, sonst nichts |
| **Asset-Karte** | Fakten-Schicht, nur für Bestände und REGEL0-Signale des Tages | Teil der Signalmail, **nie eigener Mail-Anlass** (ein Fakt ist kein Signal; jede Mail eine Handlung) |
| **Befund-Karte** (A3, Bau B1) | ein Eintrag: *BTC Folgetag positiv, kleiner geworden (2020–22 +1,26 Pp, 2026 +0,21) · Altcoins nicht trennbar (+0,16, Obergrenze +0,30 Pp) · am REGEL0-Einstieg ohne Wirkung* | bremst die LLM-Erzählung *„Wale kaufen → steigt“*: das LLM darf den Fluss nur mit diesen Grenzen nennen |
| **finales LLM** (Ebene 4) | bekommt Zustand + Eintrag; darf ihn als Bestätigung oder Gegengrund nennen, gekennzeichnet | Ü9: keine Entscheidung |
| **Wertmessung** | Rückspiel 2025–26 (gpt-oss-120b): Bedenken-Stufe **mit und ohne** Wal-Zustand (Ü6) | einer der wenigen Eingänge mit **sauberem Zeitpunkt** (Tagesdatei ab 03:00 UTC) und **voller Historie** (`wale_s2.db`, `wale_voll.db`) → sofort rückspielbar |

**Vor dem Bau nachzuweisen** (§4): Abruf am NB mit **einem** Lauf (Volumen 32 MB/Tag für 127 Altcoins gemessen; BTC/ETH/SOL offen),
Übertragung der 365-T-Historie für die Einordnung. **Nicht** Teil davon: das dünne Drittel und die eingestellten Paare aus §19 des
Messplans — sie wären eine **neue Hypothese** mit eigenem Vorab-Plan.