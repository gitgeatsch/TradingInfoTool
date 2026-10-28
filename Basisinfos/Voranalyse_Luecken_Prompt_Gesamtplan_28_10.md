# Vor dem Bau: Lücken und Quellen, Prompt-Umfang, Gesamtplan (28.10.2026 spät)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 28.10. spät):** *„bevor wir wieder scheitern …“*
1. *„recherchieren, was uns fehlt und wo wir uns auf die Suche nach Datenquellen begeben müssen“*
2. *„vorher prüfen, ob und wie wir mit dem Prompt auskommen aufgrund der Menge an Informationen“*
3. *„das Vorhaben in den Gesamtplan einpflegen und die alten, nicht mehr gültigen Informationen entfernen. Wenn ein Umbau nicht sauber möglich ist, mache einen Vorschlag, ob wir einen neuen Gesamtplan brauchen“*

**Gehört zu:** `Datenbasis_Schichten_Sichten_28_10.md` (Sichten S1–S8, §3a Fragen) · `Voranalyse_Dashboard_LLM_28_10.md` · `Bauplan_Dashboard_A3_A4_28_10.md`.

---

## A. Lücken und Datenquellen

**Stand:**
- Recherche 28.10. über offizielle Seiten.
- Eigene Nachweise je mit einem Abruf: yfinance, Bundesbank, EZB, ECOS.
- Stufen: **✔N** nachgewiesen (eigener Abruf) · **[B]** offizielle Seite · **[S]** Sekundärquelle · **[U]** unsicher.

### Übersicht je Sicht

| Sicht | gedeckt | neu nachgewiesen | Lücke, und wo wir suchen müssen |
|---|---|---|---|
| **S1 Krypto gesamt** | BTC-Trend, Season, Breite, DVOL, Stablecoins, Funding/OI | **Coinbase-Prämie** aus der öffentlichen Coinbase-Kerzen-API gegen Binance [B]; **Basis Quartalsfutures** über Binance `continuousKlines` (selbst rechnen; `/futures/data/basis` hat nur 30 Tage) [B] | **ETF-Zuflüsse**: kein freier maschinenlesbarer Weg (Farside nur HTML, SoSoValue unklar, CoinGlass kostet) → Suchrichtung: **Tagesbestände der Emittenten** (iShares/Fidelity veröffentlichen Bestände) [U]. **Liquidationen**: nur live per Websocket, untererfasst → nicht für das Rückspiel |
| **S2 Liquidität, Zinsen USA** | K1–K5, 10J, Termine | **ALFRED** (FRED-Jahrgänge) über unseren FRED-Schlüssel: `realtime_start/end`, Erstveröffentlichung [B] → das löst das Rückspiel für Makro | Ratenlimit von ALFRED nicht genannt → beim Bau messen |
| **S3 Risikoappetit** | S&P, VIX, K6, K7 | **^NDX, SOXX, ^VIX ✔N** | ⚠️ **HY-Aufschlag bei FRED seit April 2026 nur noch 3 Jahre** [B]. Überhitzung: CAPE nur monatlich und revidiert, Margin Debt nur monatlich als Excel, Put/Call-Historie unbestätigt → **Überhitzung über Marktkurse messen** (Abstand zum Schnitt, Halbleiter gegen Index), nicht über Bewertungskennzahlen |
| **S4 Dollar, Rohstoffe** | K8 (Broad-Index), Öl | **DXY, Gold, Brent, Kupfer ✔N** | – |
| **S5 Asien** | Upbit-Listings | **KOSPI, Nikkei, Hang Seng, Shanghai, KRW, JPY ✔N**; **JGB 10J** täglich ab 1974 beim japanischen Finanzministerium als CSV [B]; **Kimchi-Prämie** aus Upbit KRW-BTC ÷ (Binance × USD/KRW) [B] | ECOS (Korea-Anleihen, amtlich): **Schlüssel leer** (A0). Yuan: `CNH=X` ✖, Ersatz `CNY=X` [U]. **Nachrichten Asien**: Yonhap, Korea Herald, Japan Times als RSS [S], Historie nur über Wayback (wie unsere 9 Feeds). Bithumb: keine API |
| **S6 Staatsschulden** | US-Laufzeitprämie, 10J | **Deutschland 10J täglich ✔N** (Bundesbank, 2.858 Werte ab 2019, heute 3,37 %); **MOVE ✔N**; **US-Auktionen mit Bid-to-Cover** (fiscaldata, ab 1979) [B]; **US-Schuldenstand täglich** (Debt to the Penny) [B]; UK 10J (Bank of England) [S] | ⚠️ **Frankreich/Italien 10J TÄGLICH: kein freier Weg** (EZB-Reihen 404/504 ✔N, Eurostat täglich 404 [B], Banque de France nur mit Login) → **monatlich** über Eurostat/FRED; täglich nur über die **Nachrichtenlage** (GDELT-Ton). Staats-Ratings: keine freie strukturierte Quelle |
| **S7 Ereignisse** | Binance (V1 lädt), Upbit, 9 Krypto-Medien (Archiv) | **GDELT DOC 2.0**: Zeitreihen und Ton je Land oder Thema **ab 2017**, Artikellisten nur 3 Monate [B] | **Token-Freigaben: keine freie Quelle** (DefiLlama emissions = Pro, Tokenomist mit Schlüssel) [B]. **Hacks**: DefiLlama Pro, rekt.news ruht seit 04/2026 [B]. **Wirtschaftsnachrichten live**: Yahoo-Schlagzeilen je Symbol [S], Reuters eingestellt. **Nachrichten live am NB**: Job fehlt (die 9 Feeds direkt) |
| **S8 Termine** | FOMC, CPI, NFP | – | EZB/BoJ-Sitzungen nur als HTML [U] |

### Was das heißt — wo wir suchen müssen

| Rang | Lücke | warum wichtig | Suchrichtung |
|---|---|---|---|
| 1 | **Nachrichten live am NB** | ohne sie keine Ereignisse im Betrieb, A1 bleibt Labor | kein Suchen nötig: die 9 Feeds und die Asien-Feeds direkt abrufen (klein) |
| 2 | **Frankreich/Italien täglich** | die Schuldenfrage Europa, dein Beispiel | weiter suchen: Börse Paris/Euronext-Daten, OAT-Futures (Eurex) über yfinance-Kürzel, Banque-de-France-Webstat mit freiem Konto (**du** müsstest es anlegen); bis dahin monatlich + GDELT-Ton |
| 3 | **Token-Freigaben** | Freigaben sind ein häufiger Auslöser bei Altcoins | Projektdokumente, GitHub der Projekte, **Binance-Ankündigungen** (V1 lädt sie mit) und Nachrichten über A1 lesen lassen; keine strukturierte Quelle frei |
| 4 | **ETF-Zuflüsse** | wichtigster Nachfragekanal für BTC/ETH seit 2024 | Bestände der Emittenten (iShares-Bestandsdatei täglich) [U] |
| 5 | **ECOS-Schlüssel** | amtliche Korea-Daten | **du** registrierst dich, ich prüfe danach |
| 6 | **Hacks** | Risiko-Wächter A2 | über A1 aus den Nachrichten lesen; strukturiert nicht frei |

⚠️ **Gegenprobe ausstehend:** Groq-Grenzen im Free-Reiter (die Seite zeigte die Werte des Developer-Plans; Sekundärquellen nennen dieselben), Gemini-Grenzen in AI Studio, `CNY=X`, UK-Reihe.

### A0. Bank of Korea ECOS — geprüft am 28.10. mit dem Schlüssel (Nutzer: *„das musst du prüfen mit dem Schlüssel“*)

| | |
|---|---|
| Eintrag in `.env` (Desktop) | `ECOS_API_KEY` vorhanden, **Wert leer** (Länge 0). Kommentarzeile: *„kostenlos, Identitätsprüfung bei Registrierung – Korea-M2“* |
| Abruf KOSPI, USD/KRW, Staatsanleihe 10J (täglich) | ECOS antwortet `INFO-100 Invalid activation key` |
| Ursache | Die Registrierung war wegen des „Mock Hack“ der Bank of Korea vom 29.06. bis 24.07.2026 ausgesetzt (`Spezifikation.md` Z. 504ff.). Der Schlüssel wurde danach **nie eingetragen** |
| Was nötig ist | **Du** registrierst dich bei ecos.bok.or.kr (Identitätsprüfung; ein Konto lege ich nicht an) und trägst den Schlüssel in die Desktop-`.env` ein. Danach prüfe ich mit denselben drei Abrufen |
| Bis dahin | KOSPI und Won über yfinance (`^KS11`, `KRW=X`) ohne Schlüssel, nachgewiesen in A1. ECOS brächte zusätzlich die **koreanische Staatsanleihe** und amtliche Reihen |

### A1. Weltmärkte über yfinance — NACHGEWIESEN am 28.10. (je ein Abruf, Tageskerzen ab 2019)

| Sicht | Symbol | Zeilen | Stand | Ergebnis |
|---|---|---|---|---|
| S5 Asien | `^KS11` KOSPI | 1.916 | 27.10. | ✔ |
| S5 | `^N225` Nikkei | 1.905 | 28.10. | ✔ |
| S5 | `^HSI` Hang Seng | 1.924 | 28.10. | ✔ |
| S5 | `000001.SS` Shanghai | 1.893 | 28.10. | ✔ |
| S5 | `KRW=X`, `JPY=X` | je 2.036 | 28.10. | ✔ |
| S5 | `CNH=X` | **1** | – | ✖ nur ein Wert → `CNY=X` prüfen |
| S4 | `DX-Y.NYB` (echter DXY), `GC=F` Gold, `BZ=F` Brent, `HG=F` Kupfer | je ~1.970 | 28.10. | ✔ |
| S3 | `^NDX`, `SOXX` (Halbleiter), `^VIX` | je ~1.968 | 28.10. | ✔ |
| S6 | `^MOVE` (Anleihe-Schwankung) | 1.953 | 28.10. | ✔ |

**Bewertung:**
- Das sind **Marktkurse**. Sie werden nicht revidiert und haben damit einen sauberen Zeitpunkt des Bekanntwerdens (Tagesschluss je Börse). Sie sind für das **Rückspiel geeignet**.
- ⚠️ Asiatische Börsen schließen **vor** Europa und den USA. Ein Rückspiel muss den Tageswert zur **eigenen** Schlusszeit ansetzen, nicht zum UTC-Tagesende (*Tageswert an Stundenanker ist Vorgriff*).
- ⚠️ yfinance ist inoffiziell. Es läuft im Projekt schon (Rohstoffe, SPY), darf aber nicht die einzige Quelle einer Sicht sein, ohne dass ein Ausfall angezeigt wird.

### A2. Nachweis für die gewählten Sichten S1–S4, S7, S8 — 29.10. (G4, je ein Abruf am Desktop, nichts abgelegt)

Anlass: G2 entschieden (*„G2 und G3 wie empfohlen“*). Geprüft wurde, was in der Übersicht oben nur **[B]** oder **[U]** war.

| Sicht | Quelle | Ergebnis | Befund |
|---|---|---|---|
| S1 | **Coinbase-Prämie** (Coinbase BTC-USD gegen Binance BTCUSDT, Tagesschluss) | ✔N | 274 Tage ab 01.01.2023 aus einem Abruf, Median +0,016 %. Je Abruf höchstens 300 Kerzen → rund 5 Abrufe je Jahr |
| S1 | **Basis Quartalsfutures** (`continuousKlines` CURRENT_QUARTER gegen Perp) | ✔N | BTC und ETH lückenlos ab 01.01.2023 bis heute (500 + 366 + 423 Tage in drei Fenstern), Median +1,00 % absolut |
| S2 | **ALFRED** (Jahrgänge über unseren FRED-Schlüssel) | ✔N | NFP Dez. 2024: Stand 15.01.2025 **159.536**, heute **158.316** → die Revision ist sichtbar, das Rückspiel kann den **damals bekannten** Wert nehmen. 45 Veröffentlichungstage seit 2023 |
| S3 | **HY-Aufschlag** `BAMLH0A0HYM2` | ✔N | 793 Werte ab **30.10.2023**. ⚠️ Nur 3 Jahre — reicht aber für **beide** Rückspiel-Zeiträume aus G3 (2025 und Dez. 2025 – Okt. 2026) |
| S7 | **die 9 Krypto-Feeds live** | ✔N | alle 9 antworten mit HTTP 200, zusammen 193 Meldungen im Abruf. Für den Betrieb fehlt nur der **Job**, keine Quelle. Historie liegt schon in `data/_lc/nachrichten.db` (Wayback) |
| S7 | **GDELT DOC** Ton-Zeitreihe | ✔N | „bitcoin“ Jan. 2023: 32 Punkte → Historie vorhanden |
| S7 | GDELT DOC Artikelliste | ✖ | HTTP **429** auch nach 60 s Pause (*„one every 5 seconds“*). Nicht nötig: Artikel kommen aus den Feeds, GDELT nur für den **Ton** |
| S8 | EZB-Sitzungskalender | ✔ (HTML) | Seite erreichbar, die Termine stehen aber nicht vollständig im HTML (nur 2 Datumsangaben 2026 gefunden) → **Termine von Hand je Jahr** eintragen (8 Sitzungen), wie bisher FOMC |

**Fazit A2:** Für S1–S4, S7 und S8 gibt es **keine offene Quellenlücke mehr**, die den Messplan blockiert. Es bleiben die bekannten Lücken, die **nicht** frei zu haben sind: ETF-Zuflüsse, Token-Freigaben, Hacks. Sie kommen nur über die Ereignisse (A1 liest Binance-Ankündigungen und Nachrichten).

---

## B. Reicht der Prompt? — gemessen, nicht geschätzt

**Wie gemessen:**
- Beispiel-Eingaben aus **echten** Daten: Nachrichtenarchiv, ein Median-Tag (2026-05-09, 60 Meldungen) und ein starker Tag (90. Perzentil, 2026-01-29, 150 Meldungen); Befunde aus `bestand.py`.
- Gezählt von **beiden** Modellen: Gemini `countTokens` (Desktop-Schlüssel 2, zählt nicht gegen das Kontingent) und Groq gpt-oss-120b (`max_tokens=1`, Feld `prompt_tokens`).
- Skript: Sitzungs-Scratchpad `token_probe.py`, nur lesend.

| Eingabe | Zeichen | Gemini | gpt-oss-120b (Groq) |
|---|---|---|---|
| Ereignis-Leser (A1), Median-Tag, Meldungen mit Beschreibung | 19.661 | 4.912 | 4.630 ✔ |
| Ereignis-Leser, starker Tag, mit Beschreibung | 43.530 | 10.848 | ✖ **413 zu groß** |
| Ereignis-Leser, starker Tag, nur Titel | 15.398 | 4.921 | (429, Minutengrenze erschöpft) |
| Sicht S1: 12 Zustände + 8 Ereignisse | 3.017 | 1.099 | 1.105 ✔ |
| Sicht S1: 12 Zustände + 25 Ereignisse | 5.855 | 2.043 | 2.025 ✔ |
| Sicht **roh**: Zustände + alle Meldungen des starken Tags | 45.165 | 11.485 | ✖ **413** |
| Finales LLM: Fakten + 8 Sicht-Ergebnisse + 12 Befunde | 7.647 | 2.987 | (429) |

Beide Modelle zählen fast gleich, die Abweichung liegt unter 6 %. Faustregel: **etwa 3,5–4 Zeichen je Token**.

### Was daraus folgt

| # | Befund | Folge |
|---|---|---|
| T1 | **Die Stufung ist Pflicht, kein Stil.** Rohmeldungen direkt in eine Sicht ergeben 11.500 Token, über das Ereignis-Leser-Ergebnis sind es 1.100–2.000 | Jede Ebene bekommt **nur das Schema-Ergebnis der Ebene darunter** (Ü4). Sichten nie mit Rohmeldungen füttern |
| T2 | **Betrieb (Gemini): kein Engpass.** Die größte Eingabe hat 11.000 Token bei einem Kontextfenster in Millionengröße. Tagesbedarf: A1 ~2 Aufrufe, 8 Sichten, ≤ 60 Asset-Karten → **~70 Aufrufe, ~250.000 Token/Tag** | passt in den Topf eines Modells (500/Tag) |
| T3 | **Groq: jede Anfrage muss unter ~8.000 Token bleiben** (Eingabe + Ausgabe). Größere scheitern **sofort mit 413**, weil die Grenze **je Minute** gilt | A1 auf Groq nur in Bündeln von **≤ 50 Meldungen** (~4.500 Token); höchstens **eine** große Anfrage je Minute |
| T4 | **Der echte Engpass ist das Rückspiel**, also der Test an der Vergangenheit. Auf Groq je Tag Geschichte: A1 ~10.000 + 8 Sichten ~16.000 + finale Abwägungen ~4.000 je REGEL0-Einstieg. Bei **200.000 Token/Tag** sind das etwa **5–7 Tage Geschichte je Kalendertag**; 2025–26 (~600 Tage) bräuchte **3–4 Monate** | **so nicht machbar**: das wäre die „2-Jahres-Lösung“ in klein |
| T5 | **Ausweg 1: Gemini für die Zeit NACH seinem Wissensstand.** Gemini 3.5-flash-lite kennt Kurse bis etwa Okt. 2025 (gemessen 19.10.). Ab **Dez. 2025** ist es für ein Rückspiel sauber; das sind ~11 Monate mit 500 Aufrufen/Tag am **Desktop-Schlüssel 2** | Rückspiel Dez. 2025–Okt. 2026 auf Gemini in **~1 Woche** möglich. **Vorher** Positivkontrolle wiederholen (Horizont gilt je Modell) |
| T6 | **Ausweg 2: weniger, aber gleich gut.** Langsame Sichten (S2 Zinsen, S4 Dollar, S6 Staatsschulden) **wöchentlich**; Meldungen **entdoppeln** (dieselbe Nachricht in 9 Medien); A1 auf **Titel + erste 150 Zeichen** | etwa halbiert den Bedarf |
| T7 | **Ausweg 3: 2025 auf gpt-oss-120b nur für die Ebenen, die es brauchen**, also Sichten und finale Abwägung, mit den A1-Ergebnissen aus Ausweg 1 bzw. aus Regeln | Messung über zwei Modelle **getrennt ausweisen**, nicht vermischen |
| T7b | **Ausweg 4: Cloudflare Workers AI als zweiter sauberer Topf.**
  - Der Dienst bietet gpt-oss-120b mit 10.000 Neurons pro Tag. Das sind nach der Preisliste rund **244.000 Token/Tag** bei einer Mischung von drei Teilen Eingabe zu einem Teil Ausgabe [B]; Kontext 128k, also **keine 8.000er-Minutengrenze** [U].
  - Er würde die saubere Kapazität **verdoppeln**.
  - Dafür ist ein kostenloses Konto nötig, das **du** anlegen müsstest. | eigene Entscheidung, nicht jetzt |
| T7a | **Ausweg 5: Groq führt die Töpfe JE MODELL. NACHGEWIESEN am 28.10.** Je ein Aufruf an gpt-oss-120b und gpt-oss-20b ergab für **beide** `remaining-requests 999` von 1.000 und `limit-tokens 8000` je Minute. Bei einem gemeinsamen Topf hätte der zweite Aufruf 998 gezeigt. Damit ist **gpt-oss-20b ein zweiter sauberer Topf** (gleicher Wissensstand ~Mitte 2024, schwächeres Modell) | **A1, also das Einordnen von Meldungen, auf 20b** und die Abwägungen auf 120b. Vorher eine Positivkontrolle des Wissensstands für 20b. Die Tagesgrenze für Token (200.000) zeigt der Header nicht, sie ist beim Lauf zu messen |
| T7c | **OpenRouter scheidet für das Rückspiel aus.** `gpt-oss-120b:free` antwortet am 28.10. mit **404**; der Free-Bereich hat kein brauchbares Modell mit Wissensstand vor 2025 [B, Stichprobe] | nur noch Reserve im Betrieb |
| T8 | **Ausgabe zählt mit.** gpt-oss denkt vor der Antwort (Reasoning-Token). Ohne Begrenzung (`reasoning_effort: low`) wächst jede Anfrage um 500–2.000 Token | im Messplan festlegen |

### B2. Warum überhaupt Groq? (Nutzerfrage 28.10.: *„Gemini haben wir zwei Schlüssel und damit gesamt 2 plus 2 Modelle oder?“*)

Geprüft am 28.10. mit beiden Schlüsseln:

| | |
|---|---|
| **Schlüssel** | zwei Projekte. **Schlüssel 1 = NB-Betrieb**, Schlüssel 2 = Desktop. Grenzen gelten **je Projekt und je Modell** |
| **Modelle** | mehr als zwei. Antworten können 3.1-flash-lite, 3.5-flash-lite, 3.5-flash, 3.6-, 3.7- und 3.8-flash sowie 3-flash-preview. Jedes hat einen **eigenen** Topf. Die Größe des Topfs ist je Modell verschieden und nur bei den flash-lite-Modellen gemessen (500/Tag) |
| **Ältere Modelle 2.5** (die 2025 noch nicht kennen würden) | **für beide Schlüssel gesperrt**: *„no longer available to new users“* (404) |
| **Wissensstand** | 3.5-flash-lite kennt Kurse bis ~Okt. 2025 (gemessen). Die **neueren** Modelle (3.6–3.8) kennen vermutlich **noch mehr**, nicht weniger. Dann wäre ihr sauberer Zeitraum kürzer. Ungemessen, also vorher prüfen |

**Antwort:**
- Für den **Betrieb** und für ein **Rückspiel ab Dez. 2025** brauchen wir Groq **nicht**. Gemini reicht, mit Schlüssel 1 für den NB und Schlüssel 2 für den Desktop, und mehrere Modelltöpfe.
- Groq brauchen wir nur für zwei Dinge:
  1. ein **sauberes Rückspiel auf 2025**, denn alle erreichbaren Gemini-Modelle kennen 2025;
  2. eine **zweite Modellfamilie** für den Gegenanwalt (Ü7: verschiedene Modelle, damit die Irrtümer nicht gleich sind).
- **Vorschlag (Gesamtplan G3):** zuerst Gemini auf Dez. 2025 – Okt. 2026; Groq auf 2025 danach als zweiter Zeitraum, als Gegenprobe des Geltungsbereichs.

### Fazit B — so kommen wir aus

| | Betrieb (NB) | Rückspiel 2025 | Rückspiel Dez. 2025 – Okt. 2026 |
|---|---|---|---|
| Ereignis-Leser A1 | Gemini 3.1, ~2 Aufrufe/Tag | Groq **gpt-oss-20b**, Bündel ≤ 50 Meldungen, entdoppelt | Gemini, Desktop-Schlüssel 2 |
| Sichten | Gemini 3.1, 8/Tag | Groq **gpt-oss-120b**; S1, S3, S5, S7 täglich, S2, S4, S6 wöchentlich | Gemini, Desktop-Schlüssel 2 |
| Finales LLM + A3/A4 | Gemini 3.1, ≤ 60/Tag | Groq 120b, nur auf REGEL0-Einstiegen | Gemini, Desktop-Schlüssel 2 |
| Größe je Aufruf | ≤ 11.000 Token, unkritisch | **≤ 8.000 Token inkl. Ausgabe** (hart) | unkritisch |
| Dauer | – | ~3–4 Wochen bei zwei Groq-Töpfen und Ausweg 2, mit Cloudflare etwa halb so lang | ~1 Woche |

Die Rückspiele der beiden Zeiträume werden **je Modell getrennt ausgewiesen**. Der Wissensstand ist **je Modell vorher** mit Positivkontrolle zu prüfen: bei gpt-oss-20b und Gemini 3.1 ist er noch ungemessen.

⚠️ **Ehrlich:**
- Ausweg 1 heißt: Das Rückspiel trägt **ein Jahr**, nicht zwei. Nach Messnorm (Blöcke von 15 Tagen, mindestens 20) reicht das gerade so.
- Ein Ergebnis aus nur dieser Zeit gilt **nur für diese Zeit**; der Geltungsbereich ist auszuweisen.

---

## C. Gesamtplan — Vorschlag: ein NEUER Plan

### Die Lage

| Dokument | Umfang | gültig | veraltet | Historie |
|---|---|---|---|---|
| `Plan_Schritt59_Gesamtkette_17_09.md` (heute „der laufende Plan“) | 2.767 Zeilen, 85 Nachträge | **~3–5 %**: §0-Regeln, M1-Definition, Nachträge 79–85 | **~65–70 %**: alte LLM-Kette (§3/3a), Phase 4 Hebel alt, Phasen 5–9, §11.2ff. | ~25–30 % |
| `Gesamtplan_Wo_wir_stehen_28_08.md` | 5.252 Zeilen, Stand 12.09. | ~3 % (in CLAUDE.md übernommen) | ~30 % | ~65 % |

**Was heute tatsächlich „als Nächstes“ beantwortet:** nur `Arbeitsstand_Schritt59.md`, ganz unten. Der Plan selbst endet vor dem Entscheid a.

### Warum ein Umbau an Ort und Stelle NICHT sauber geht

1. **Es müssten ~95 % gelöscht werden.**
2. **Genau die veralteten Abschnitte werden zitiert**: §3, §6a, §11.1, „Takt und Cooldown“, Paket V, §5.1 (Register-Quellen in `bestand.py`, `soll_ist.py`, Messpläne, Entscheidungen). Nimmt man sie heraus, zeigen diese Verweise ins Leere. Einer verweist sogar auf eine **Zeilennummer** im alten Gesamtplan.
3. **Historie darf nicht umgeschrieben werden** (Zentraldokumente: *Umschreiben wäre Geschichtsfälschung*). Der Plan ist zur Hälfte Chronik.

### Vorschlag

| | |
|---|---|
| **Neu** | `Basisinfos/Gesamtplan.md`: **nur ZUSTAND**, ohne Datum im Namen, kurz (Ziel ≤ 400 Zeilen) |
| **Inhalt** | 1 Ziel und die vier Regeln · 2 Was heute läuft (Betrieb: REGEL0, Spot B1/B3/B4, Hebel H15, Statusseite, Prüfblock) · 3 Was gemessen gilt (Verweis aufs Register, keine Kopie) · 4 **Das Vorhaben** Dashboard/LLM: Ebenen, Sichten, Fragen, Stufen mit Prüfung · 5 Offene Punkte und Reihenfolge (eine Liste, eine Wahrheit) · 6 Feste Regeln (D vor L, Messstandard, R-R11, NB = Produktion, kostenfrei) · 7 Wo die Historie liegt |
| **Alt** | Beide alten Pläne bleiben **unverändert als Historie** und bekommen **oben eine Zeile**: *„Historie — abgelöst durch `Gesamtplan.md` am …; nicht fortschreiben.“* Damit halten alle Verweise |
| **Fortschreibung** | Neue Lage = **den Zustand ändern**, nicht unten anhängen. Die Chronik steht in Arbeitsstand, Entscheidungen und Register; der Plan wiederholt sie nicht |
| **Prüfung** | Ein Prüfpaket `Gesamtplan`: Datei vorhanden, jeder genannte Befund im Register `gilt`, keine Nennung der stillgelegten alten Kette als laufend, offene Punkte gleich `nb_kontrollen.yaml` |
| **Bleibt, wie es ist** | `Plan_Hebel_fuenf_Phasen_27_09.md` (wird maschinell gelesen: fünf Phasenzeilen und *„Wir sind in Phase N.“*). `Arbeitsstand_Schritt59.md` (Paket Abbildung). Beide verweisen künftig oben auf den neuen Plan |
| **Nachzuziehen** | CLAUDE.md (Verweis Z. 268), Memory `reference_zentraldokumente` (welcher Plan der laufende ist), Kopf des Arbeitsstands („Stand 07.10.“ / „HIER ANFANGEN 18.10.“ sind irreführend) |
| **Aufwand** | etwa ein halber Tag, ohne Betriebsänderung |

---

## D. Zur Abstimmung — eine Frage

**Neuer Gesamtplan nach C?**

| | Weg | Einschätzung |
|---|---|---|
| **1** | **Ja, neuer `Gesamtplan.md` nur mit Zustand**; die alten Pläne werden zur Historie mit Verweis | **Empfehlung**: eine Wahrheit, kurz, prüfbar; kein Verweis bricht |
| 2 | Den alten Plan kürzen | ~95 % löschen, Verweise brechen, Historie geht verloren |
| 3 | Nur den neuen Abschnitt anhängen (Nachtrag 86) | ändert nichts an deinem Einwand: das Alte bleibt neben dem Neuen stehen |
