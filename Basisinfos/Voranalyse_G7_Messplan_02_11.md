# Voranalyse G7 — Messplan: Faktentreue der Prüfer und Wert der Sichten (02.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 02.11.):** *„ja, starte mit der Voranalyse G7 – prüfen, gegenprüfen und doku“*.
**Gehört zu:** [`Datenbasis_Schichten_Sichten_28_10.md`](Datenbasis_Schichten_Sichten_28_10.md) §3a (Frage je Sicht, finales LLM, „Warum das
messbar ist“) und §6 Schritt 3 · [`Bauplan_Dashboard_A3_A4_28_10.md`](Bauplan_Dashboard_A3_A4_28_10.md) §6 (Faktentreue 100 %, Selbsttest
Prüfer ≥ 1.000 je Art) · [`Fuetterung_Satzform_31_10.md`](Fuetterung_Satzform_31_10.md) §4 (Blöcke des finalen LLM), §5 (Takt), §6 Schritt 5 ·
[`Voranalyse_Luecken_Prompt_Gesamtplan_28_10.md`](Voranalyse_Luecken_Prompt_Gesamtplan_28_10.md) T4–T7 (Budget, Modelle) ·
[`Voranalyse_A1_Ereignisleser_01_11.md`](Voranalyse_A1_Ereignisleser_01_11.md) (Ereignisse) · Gesamtplan G3 (Modelle, Reihenfolge) · G7.
**Stand:** ✔ **§6 entschieden a/a/a (02.11.) → Stufe 0 gebaut und gemessen (§7); §8 fachlich geprüft und a umgesetzt (§9).** Betrieb unberührt. *(Vorlage-Stand:)* Voranalyse — nichts gebaut, kein LLM-Aufruf. Gemessen nur lesend (`sichten.db`, Kursdaten, REGEL0-Referenz)
mit `Rechenkern_02_10/g7_voranalyse.py` → `g7_voranalyse.txt`.

---

## 0. Worum es geht

G7 sind **zwei verschiedene Fragen**, die nicht vermischt werden dürfen:

| | Frage | Was es prüft | Woher |
|---|---|---|---|
| **F** | **Faktentreue:** Stimmt, was das LLM über die Eingabe sagt — und **merkt der Prüfer es, wenn nicht?** | den **Prüfer** (Code), nicht das Urteil | Bauplan §6: Soll 100 %, Selbsttest ≥ 1.000 je Fehlerart |
| **W** | **Wert:** Kommt nach „kritisch“ wirklich häufiger Schlimmes als nach „normal“? Liefen Handlungen mit Bedenken 2 schlechter als mit 0? Fehlt etwas, wenn eine Sicht fehlt (Ü6)? | das **Urteil** | Datenbasis §3a, Rückspiel nur mit Eingaben, die einen Zeitpunkt des Bekanntwerdens haben |

Dazu der Auftrag vom 01.11. (Fütterung §8 P6): **erst messen, ob der GDELT-Ton etwas trägt**, erst dann der NB-Abruf.

⚠️ Der Leitsatz bleibt: *das LLM erzeugt Information, die Messung bestimmt ihren Wert.* Ein Urteil ohne Messung bekommt kein Gewicht.

---

## 1. Was da ist

| | Stand |
|---|---|
| Zustände (Ebene 1) | `agent/zustaende.py` ✔ — 35 Zustände S1–S4/S7 + S8 Termine, kein Vorgriff an 333 Rückspiel-Tagen |
| Historie | `sichten.db` ab 2020 ✔ (Rang über 5 J ab 2021-03) |
| Ereignisse (A1) | Börsen ✔ (6.701); **Nachrichten im Volllauf** (Prompt 3, ab 01.11., Groq-Kontingent) — nur ab **Dez. 2025** (`NACHRICHT_AB`) |
| REGEL0-Einstiege | Referenz `kern48jbz` (Menge *bestand*) bis **2026-08-31** |
| Prüfer | **Z-1** `gegenpruefer_rollen.pruefe_zahlendeckung` — im Betrieb in `regel0_llm.zahlendeckung` (gezählt, nicht verworfen) |
| Messanlage | `messnorm`: Block max(15 T, 3·H), **< 20 Blöcke = kein Befund**, Nullpunkt aus 40 Nullwelten, Selbsttest |
| Modelle (G3) | **zuerst Gemini (Schlüssel 2) Dez. 2025 – Okt. 2026**, danach **Groq gpt-oss 2025** als zweiter Zeitraum und zweite Modellfamilie; Wissensstand je Modell **vorher** prüfen |

---

## 2. Befunde — geprüft und gegengeprüft

### G7-1 Ein Zeitraum allein trägt nur Horizonte bis 5 Tage

| Zeitraum | Tage | H=1 | H=3 | H=5 | H=7 | H=10 | H=14 |
|---|---|---|---|---|---|---|---|
| 2025 (gpt-oss) | 334 | 22 | 22 | 22 | 15 ✖ | 11 ✖ | 7 ✖ |
| Dez. 2025 – Okt. 2026 (Gemini) | 335 | 22 | 22 | 22 | 15 ✖ | 11 ✖ | 7 ✖ |
| beide zusammen | 669 | 44 | 44 | 44 | 31 | 22 | 15 ✖ |

Blöcke nach `messnorm._block`; ✖ = unter 20, **kein Befund möglich**.
- Die Fragen an **S1, S3, S5, S6** (*„in 1–7 Tagen“*) sind im Gemini-Zeitraum nur bis **H = 5** messbar.
- **S2 und S4** fragen nach *„den nächsten Wochen“*. **H = 14 ist in keinem Rückspiel messbar**; H = 7 bis 10 nur mit **beiden** Zeiträumen.
  → Die Frage an S2/S4 im Rückspiel heißt dann *„in 7 (bis 10) Tagen“* — oder S2/S4 bleiben **Fakt ohne gemessenes Urteil**.
- ⚠ **Gegenprüfung Datenende:** Am Desktop enden die Stundenkurse am **2026-09-14/16**, die REGEL0-Referenz am **2026-08-31**. Bis dahin
  sind es Dez. 2025 → Mitte Sep. **≈ 288 Tage = 19 Blöcke — schon bei H = 1 kein Befund.** Der Gemini-Zeitraum braucht die Kurse bis
  Ende Oktober (NB per USB oder Binance-Download) und die REGEL0-Einstiege Sep./Okt. neu gerechnet. BTC liegt in `sichten.db` bis 31.10. ✔

### G7-2 „Einbruch“ als Ja/Nein ist zu selten für eine Messung

Einbruch-Tag: Ertrag Schluss T → T+H unter −2 σ·√H (σ aus den 60 Tagen davor).

| Zeitraum | Reihe | H | Tage | **Episoden** | Blöcke mit Einbruch |
|---|---|---|---|---|---|
| 2025 | BTC | 3 | 14 | 9 | 8 von 22 |
| 2025 | Breite (Median 127 Werte) | 3 | 10 | 6 | 6 von 22 |
| Dez. 2025 – Okt. 2026 | BTC | 3 | 11 | **4** | 4 von 22 |
| Dez. 2025 – Okt. 2026 | Breite | 3 | 9 | 6 | 5 von 22 |
| Dez. 2025 – Okt. 2026 | BTC | 7 | 16 | **2** | 3 von 15 |

Gegenprobe an den Daten: die BTC-Einbrüche liegen am 17.–30.01. und 30.05.–02.06.2026 (z. B. 28.01. 89.300 → 78.741, −11,8 % in 3 T) —
es sind die bekannten Abstürze, keine Rechenartefakte.
- Mit **2 bis 6 Episoden** je Zeitraum kann kein Urteil „kritisch → häufiger Einbruch“ einen Befund tragen: die Tagesblock-Nullwelt hätte
  nur eine Handvoll Blöcke mit überhaupt einem Treffer.
- → **Zielgröße stetig**, nicht Ja/Nein: die Abwärtsbewegung über H **in σ** (Ertrag T → T+H geteilt durch σ·√H, und der tiefste Punkt
  auf dem Weg), für BTC **und** die Breite. Das ist eine Messung, keine Wahl (*Schwelle ist Messung*).

### G7-3 Der Takt spart weniger als angenommen — in S1 fast nichts

*(Fütterung §5: neues Gutachten bei Klassenwechsel eines Zustands, bei neuem Ereignis, spätestens nach 7 T. Voranalyse_Luecken T6
erwartete „etwa halbiert“.)*

| Sicht | 2025: Gutachten (Anteil der Tage) | Dez. 2025 – Okt. 2026 | Anlass meist | Eingabe ≈ Token |
|---|---|---|---|---|
| S1 | 300 (90 %) | **305 (91 %)** | Klassenwechsel | 810–830 |
| S2 | 169 (51 %) | 187 (56 %) | Klassenwechsel | 290 |
| S3 | 205 (61 %) | 198 (59 %) | Klassenwechsel | 390 |
| S4 | 101 (30 %) | 82 (24 %) | Klasse / Alter | 205–210 |
| S7 | 166 (50 %) | 165 (49 %) | Klasse, 33 × Ereignis (nur Börsen) | 105–130 |
| S8 | 51 (15 %) | 53 (16 %) | neuer Termin / Alter | 245 |
| **zusammen** | **992** ≈ 1,9 Mio. Token | **990** ≈ 1,9 Mio. Token | | |

(Token je Gutachten: Eingabe + geschätzt 1.500 für Anweisung und Antwort. ⚠ Die **Nachrichten**-Ereignisse fehlen noch — mit ihnen steigen
S1 und S7 weiter.)

**Warum S1 fast täglich neu wäre — gegengeprüft an den einzelnen Zuständen (Dez. 2025 – Okt. 2026, 335 Tage):**

| Zustand | Klassenwechsel | davon binnen 3 T zurück |
|---|---|---|
| Nachrichtenton Krypto (GDELT) | 181 | 116 |
| Nachrichtenton Fed (GDELT) | 168 | 98 |
| Nachrichtenton Aktienmarkt (GDELT) | 137 | 83 |
| Nachrichtenton Krieg/Sanktionen/Zölle (GDELT) | 129 | 74 |
| Funding ETH · BTC | 110 · 95 | 71 · 63 |
| Coinbase-Prämie BTC · ETH | 74 · 70 | 42 · 36 |
| **alle Zustände** | **1.527** | **837 (55 %) = Flackern** |

Die **Tageswerte** des GDELT-Tons springen fast jeden zweiten Tag über eine Klassengrenze und wieder zurück. Der Takt reagiert damit
vor allem auf Rauschen.

**Was eine Änderung bewirken würde** (dieselben 335 Tage, S1–S4/S7; eine zweite, unabhängig geschriebene Zählung gibt für §5 exakt dieselben
Zahlen — 305/187/198/82/165):

| Regel | S1 | S2 | S3 | S4 | S7 | zusammen |
|---|---|---|---|---|---|---|
| wie Fütterung §5 | 305 | 187 | 198 | 82 | 165 | 937 |
| Wechsel muss **2 T halten** | 195 | 76 | 102 | 69 | 101 | 543 (−42 %) |
| GDELT löst **nicht** aus (steht aber in der Eingabe) | 267 | 59 | 112 | 82 | 67 | 587 |
| beides | 167 | 52 | 87 | 69 | 67 | 442 (−53 %) |

⚠️ **Der Takt war eine Sparmaßnahme für Groq (T6).** Auf **Gemini** kostet ein Gutachten je Sicht und Tag **6 Aufrufe am Tag** — bei
500 je Modell und Tag ist das nichts, live am NB wie im Rückspiel. Eine Haltebedingung dagegen **verzögert** jede echte Änderung um einen
Tag, und ob das schadet, weiß man erst nach Stufe 2. → Frage §6.1.

### G7-4 Das finale LLM über alle Einstiege ist nur auf Gemini bezahlbar

| Zeitraum | REGEL0-Einstiege | Tage | je Tag Median (max) | Token (3.000 + 500 je Aufruf) | dazu A4 Gegenanwalt |
|---|---|---|---|---|---|
| 2025 (gpt-oss) | 4.466 | 261 | 6 (97) | ≈ 15,6 Mio. = **78 Tage** Groq-Kontingent | noch einmal so viel |
| Dez. 2025 – Aug. 2026 (Gemini) | 3.942 | 236 | 10 (111) | ≈ 13,8 Mio.; bei 500 Aufrufen/Tag je Modell **≈ 8 Tage** | ≈ 8 Tage, anderes Modell (Ü7) |

- 2025 vollständig auf Groq ist **nicht machbar** → dort eine **Stichprobe je Tag** (die Sichten sind für alle Einstiege eines Tages gleich;
  die Messung zählt ohnehin je Tag).
- Die Einstiege sind **geballt** (bis 111 an einem Tag) → Nullwelt **Tagesblock**, Selbsttest mit Ballung (Memory: *Nullwelt bei geballten
  Signalen*).

### G7-5 ⚠️⚠️ Der vorhandene Prüfer Z-1 erkennt nur ~40 % der Fehler — er kann nicht der Prüfer von G7 sein

Selbsttest an **echten Eingaben** (`zustaende.text` an 30 Tagen Dez. 2025 – Okt. 2026), je Art 1.000 gepflanzte Fälle, gepflanzt auf die
**angezeigte** Zahl der Zeile:

| gepflanzter Fehler | erkannt |
|---|---|
| Wert ±1 % | 38 % |
| Wert ±5 % | 44 % |
| Wert ±20 % · ±50 % | 41 % · 41 % |
| Wert ±100 % | 22 % |
| Rang ±10 (P14 → P24) | 40 % |
| **Wert eines anderen Zustands genannt** (falscher Bezug) | **1 %** |
| frei erfundene Zahl | 40 % |
| **korrekte Wiedergabe** (darf nicht anschlagen) | Fehlalarm |
| wie in der Eingabe · 1 Nachkommastelle · ganzzahlig · deutsches Komma | 1 % · 0 % · 1 % · 1 % |
| mit Tausenderpunkt (71.212) · in Tsd./Mrd. umgerechnet | **29 %** · **19 %** |

**Warum:** Z-1 hält jede genannte Zahl gegen **alle** Zahlen der Eingabe (Median **170** verschiedene) mit ±0,55 absolut. Bei so vielen
Zahlen deckt fast jeder Wert irgendeinen anderen (DVOL 53,3 → falsch 55,9 „gedeckt“ durch 56; Breite 28 % → falsch 29,4 gedeckt durch 0,316…).
Und eine Zahl, die richtig ist, aber beim **falschen** Zustand steht, kann ein Abgleich gegen den ganzen Text nie finden.

**⚠️ Dazu ein Fehler im Code (gefunden in der Gegenprobe):** die Zahlenerkennung `_ZAHL` **zerlegt große Zahlen**:
`71211.95 → [712, 11.95]`, `2061501 → [206, 150, 1]`, `5808 → [580, 8]`. Der Fehlalarm bei „S&P 500 7600“ (Eingabe 7599,85) kommt genau
daher. Z-1 läuft **im Betrieb** in `regel0_llm.zahlendeckung` — dort wird nur **gezählt**, nicht verworfen; die Zahl „Zahlen gedeckt“ in
Protokoll und Mail ist dadurch unzuverlässig. **Betriebscode → nicht angefasst, Frage §6.**

→ **G7 braucht einen Prüfer v2:** das Gutachten nennt je Treiber den **Schlüssel** des Zustands (z. B. `S1.dvol.BTC`) und den Wert; der Prüfer
vergleicht mit **genau diesem** Zustand, auf die angezeigte Genauigkeit. Sein Selbsttest: dieselben Fehlerarten, je 1.000, Soll **100 %
erkannt** ab einer Abweichung über der Anzeigegenauigkeit und **0 Fehlalarme** bei den erlaubten Schreibweisen. Ereignisse werden über ihren
Beleg (Link) geprüft, Termine über Art und Tag.

### G7-6 Kontamination und Wissensstand

- Gemini 3.5-flash-lite kennt Kurse bis etwa Okt. 2025 (gemessen 19.10.); **3.1 ist ungemessen** → Positivkontrolle je Modell **vor** dem
  Rückspiel (Voranalyse_Luecken T5, Gesamtplan §4.3).
- gpt-oss: Wissensstand 06/2024 [B], gemessen eher 09/2023 → 2025 sauber.

### G7-7 Was im Rückspiel noch fehlt

| | |
|---|---|
| Nachrichten-Ereignisse | Volllauf bis etwa Mitte November; für **2025** gibt es keine (A1 liest ab Dez. 2025) → der 2025-Zeitraum hätte S7/S1 **ohne** Nachrichten, oder A1 müsste 2025 lesen (weitere ~2 Wochen Groq) |
| Watchlist **zum Zeitpunkt** für S7 | offen seit A1 (heute: Watchlist von heute) |
| Kurse Sep./Okt. 2026, REGEL0 Sep./Okt. | s. G7-1 |

---

## 3. Der Messplan (Entwurf)

Grundsatz: **erst die Anlage, dann der erste Blick** — jede neue Nullwelt bekommt ihren Selbsttest, bevor ein echtes Ergebnis gesehen
wird (Memory: *Selbsttest vor dem ersten Blick*).

| Stufe | Was | LLM? | Gerät |
|---|---|---|---|
| **0a** | **Prüfer v2** bauen + Selbsttest (je Fehlerart 1.000, auf echten Eingaben): Soll 100 % / 0 Fehlalarme | nein | Desktop |
| **0b** | **Zielgrößen und Nullwelt** festschreiben (stetig, in σ, BTC und Breite, H = 1/3/5 je Zeitraum, 7/10 nur gemeinsam); **Selbsttest der Messanlage mit Ballung** (Tagesblock) | nein | Desktop |
| **0c** | **Vergleichsarm ohne LLM:** tragen die **Zustände allein** (Zahl der ●, Klassen je Sicht) etwas — über **2021–2026**, also mit vielen Blöcken? **Darin: der GDELT-Ton** (Auftrag 01.11.) | nein | Desktop |
| **0d** | **Positivkontrolle Wissensstand** je Modell (Gemini 3.1 / 3.5-flash-lite, gpt-oss) | ja, wenige Aufrufe | Desktop |
| 0e | Daten: Kurse bis 31.10., REGEL0-Einstiege Sep./Okt. neu, Watchlist zum Zeitpunkt | nein | Desktop (+ NB per USB) |
| **1** | **Sicht-Gutachten** im Rückspiel Dez. 2025 – Okt. 2026 (Gemini), Takt §5, jedes vom Prüfer v2 geprüft (Faktentreue im Rückspiel) | ja | Desktop |
| **2** | **Wert je Sicht** gegen die Zielgröße — und **gegen den Vergleichsarm 0c**: ein Gutachten muss mehr tragen als die Zustände allein, sonst bringt das LLM nichts | nein | Desktop |
| **3** | **Finales LLM** je REGEL0-Einstieg (Bedenken 0/1/2), Zielgröße wie die REGEL0-Messung (24 h, O21), Tagesblock | ja | Desktop |
| **4** | **Beitrag je Sicht (Ü6):** finales Urteil mit und ohne die Sicht — **nur** für Sichten, die in Stufe 2 etwas zeigten | ja | Desktop |
| **5** | **Zweiter Weg:** 2025 auf gpt-oss — für H = 7/10 (S2/S4) und als Bestätigung dessen, was in 2/3 trug (Memory: *TRÄGT braucht zweiten Weg*) | ja | Desktop |

**Vorab festzulegen (vor dem ersten Blick, in einem Commit):**
- je Sicht die Frage **mit Horizont** (S1/S3: 1/3/5 T · S2/S4: 7/10 T nur gemeinsam · S7: Ertrag des Assets nach dem Ereignis) und die Zielgröße
- Richtung: die Frage hat eine **fachliche** Richtung (kritisch → mehr Abwärts) → einseitig, mit Begründung; ohne Richtung zweiseitig
- Epochen getrennt ausweisen (zwei Zeiträume = zwei Modelle); **kein** gleiches Ergebnis erwartet
- „trägt“ nur mit Band, je Tag, zweitem Weg und Geltungsbereich

---

## 4. Budget

| | Gemini (Dez. 2025 – Okt. 2026) | Groq gpt-oss (2025, zweiter Weg) |
|---|---|---|
| Positivkontrolle Wissensstand | ~50 Aufrufe je Modell | ~50 Aufrufe |
| Sicht-Gutachten | täglich: 6 × 335 = **2.010 Aufrufe** (6/Tag) · mit Takt §5: 990 | mit Takt §5 ≈ 1,9 Mio. Token ≈ **10 Tage**; täglich ≈ 4 Mio. ≈ 20 Tage |
| A1 Nachrichten | läuft (bis ~Mitte Nov.) | 2025 **nicht gelesen** — ≈ 2,5 Mio. Token ≈ 13–16 Tage, falls S1/S7 2025 mit Nachrichten |
| Finales LLM | 3.942 (+ Sep./Okt.) Aufrufe ≈ **8–10 Tage** bei 500/Tag | Stichprobe 3 je Tag ≈ 780 × 3.500 ≈ 2,7 Mio. ≈ 14 Tage |
| A4 Gegenanwalt (Ü7, anderes Modell) | parallel in eigenem Modelltopf ≈ 8–10 Tage | wie oben noch einmal |
| **Summe** | **≈ 2 Wochen**, Groq unberührt | **≈ 6–9 Wochen** Groq — deshalb Stufe 5 nur für das, was in 2/3 trug |

---

## 5. Reihenfolge

1. Stufe 0a–0e — **alles ohne Groq**, läuft also **parallel** zum A1-Volllauf.
2. Stufe 1–3 auf Gemini, sobald die Nachrichten-Ereignisse fertig sind (Mitte November).
3. Stufe 4/5 nur, wenn 2/3 etwas zeigen.
4. Danach G8 (Bau, NB-Bündel).

---

## 6. Zur Abstimmung

### 6.1 Takt der Sicht-Gutachten im Rückspiel (und live)

| | Weg | Folge |
|---|---|---|
| **a** | **täglich je Sicht ein Gutachten** — der Takt §5 entfällt | 6 Aufrufe/Tag auf Gemini; kein Flackern-Problem; live und Rückspiel gleich (Ü8); ob ein Gutachten über unveränderte Lage etwas Neues sagt, lässt sich **an den Daten** nachmessen. Nachteil: das Eigenrauschen des Modells bei gleicher Eingabe geht mit hinein (L-4: 16 %) — es wird mit einer Wiederholung gemessen |
| b | Takt §5 mit **Haltebedingung 2 T** | −42 % Aufrufe; jede echte Änderung kommt einen Tag später |
| c | Takt §5 **unverändert** | reagiert zu 55 % auf Flackern; spart auf Gemini nichts, was zählt |

**Empfehlung a.** Der Takt löste ein Groq-Problem, das auf Gemini nicht besteht. Für den 2025-Zeitraum auf Groq (Stufe 5) wird er bei
Bedarf mit der Haltebedingung neu entschieden — dann mit den Daten aus Stufe 2.

### 6.2 Der Zahlen-Fehler im Betriebs-Prüfer Z-1

| | Weg | Folge |
|---|---|---|
| **a** | **im nächsten NB-Bündel (G8)** beheben, mit Prüfpaket | betrifft nur die **Zählung** „Zahlen gedeckt“ in REGEL0-Protokoll und Mail, keine Auslösung |
| b | jetzt beheben, eigener NB-Pull | ein Pull mehr gegen die Regel *NB-Änderungen bündeln* |
| c | lassen, Z-1 durch Prüfer v2 ersetzen | Z-1 bleibt bis dahin unzuverlässig |

**Empfehlung a.**

### 6.3 Kurse Sep./Okt. 2026 für Breite und REGEL0-Einstiege

| | Weg | Folge |
|---|---|---|
| **a** | **`stundenkurse.db` und `stundenkurse_alle.db` vom NB per USB** (dort stündlich fortgeschrieben, `regel0_nachlader`) | kein Download; dieselbe Quelle wie der Betrieb |
| b | Binance-Download der fehlenden Wochen | braucht dein Ja je Download; zweite Quelle neben dem Betrieb |

**Empfehlung a.**

Mit a/a/a beginnt **Stufe 0** (0a Prüfer v2 + Selbsttest, 0b Zielgröße und Nullwelt mit Selbsttest, 0c Vergleichsarm ohne LLM inkl. GDELT-Ton,
0d Positivkontrolle, 0e Daten) — alles ohne Groq, parallel zum A1-Volllauf.

✔ **Entschieden (Nutzer 02.11.): „a/a/a, Stufe 0 bauen – prüfen, gegenprüfen und doku“** — dazu die Rückfrage *„bei 6.3 warum per USB
können wir das nicht über den Austauschordner Google drive erledigen?“* → **ja, über den Austauschordner** (§7.5): USB war die
Gewohnheit für ganze Dateien (~1 GB); gebraucht werden nur die Wochen ab August, das sind ~70–100 MB in einer Datei.

---

## 7. Ausführung Stufe 0 (02.11.2026) — gebaut, geprüft, gegengeprüft

Skript `Rechenkern_02_10/g7_stufe0.py a|b|c|c2|d` → `g7_stufe0_<teil>.txt`. **Nichts im Betrieb; Groq nur für 10 Kontrollfragen.**

### 7.1 Stufe 0a — Prüfer v2 `agent/gutachten_pruefer.py`

Das Gutachten nennt je Treiber den **Schlüssel** (`S1.dvol.BTC`), der Prüfer vergleicht mit **genau diesem** Zustand: Wert als Rundung des
angezeigten Werts (keine absolute Toleranz), Rang und Klasse gleich, Ereignis über den Beleg, Termin über Art und Tag, jede Zahl im
Freitext muss zu einem **genannten** Zustand gehören. Gezählt, nicht verworfen.

**Selbsttest auf echten Eingaben** (30 Tage Dez. 2025 – Okt. 2026, je Art 1.000; daneben Z-1 auf denselben Fällen):

| gepflanzter Fehler | Prüfer v2 | Z-1 |
|---|---|---|
| Wert ±1 % · ±5 % · ±20 % · ±50 % · ±100 % | **100 %** je | 35 · 35 · 37 · 34 · 23 % |
| Rang ±1 · ±10 | **100 %** | 44 · 52 % |
| **Wert eines anderen Zustands** (falscher Bezug) | **100 %** | **0 %** |
| Klasse falsch · Schlüssel erfunden · Schlüssel aus anderer Sicht | **100 %** | — |
| Ereignis-Beleg erfunden · Ereignis-Typ falsch · Termin-Tag falsch | **100 %** | — |
| Zahl im Freitext ohne Beleg | **100 %** | — |
| **korrekte Wiedergabe:** genau · 2/3 Stellen · ganzzahlig · 1 Nachkommastelle · Rang als „P37“ · deutsches Komma | **0 Fehlalarme** von 5.000 | — |

→ **Soll (Bauplan §6) erfüllt: 13.915/13.915 erkannt, 0/5.000 Fehlalarme.**

**Gegenprüfung:** der Selbsttest hat **zwei Fehler** gefunden, bevor das Soll stand —
1. im Prüfer: die Rundungsprüfung brach bei der **ersten** bedeutsamen Stelle ab (100 aus 100,36 galt als falsch; 6,1 % Fehlalarm bei
   „ganzzahlig“) → behoben;
2. im Prüfstand: er pflanzte Zahlen in Exponentenschreibweise („1.5e+03“) und Werte, die per Regel erlaubt sind (1, Horizont) → behoben.

Prüfpaket **`Gutachtenpruefer` 8/8**; drei Mutationen (Toleranz ±0,55 wie Z-1 · Klasse ungeprüft · Freitext gegen alle Werte) **alle rot**.

### 7.2 Stufe 0b — Messanlage `g7_messanlage.py`

Zielgröße stetig in σ (`ertrag_s`, `tief_s`, σ aus den 60 Tagen davor); Block und Mindestzahl wie `messnorm` (max(15, 3 H), < 20 Blöcke
kein Befund); Nullwelt = **Kreisverschiebung** des Urteils (erhält die Ballung); Nullpunkt = Mittel; Band 5./95. bzw. 2,5./97,5.

**Selbsttest VOR dem ersten Blick** (geballte Null-Urteile, Rate 20 %, mittlere Lauflänge 1/3/10 T, 1.000 Ziehungen, einseitig; Soll ≤ 5 %):

| Zielgröße | Zeitraum | Blöcke | Fehlalarm L1 · L3 · L10 | Fund bei 0,1 · 0,2 · 0,3 · 0,5 σ |
|---|---|---|---|---|
| BTC ertrag H=3 | Dez. 2025 – Okt. 2026 | 22 | 4,3 · 4,9 · 6,3 % | 12 · 24 · 40 · 69 % |
| BTC tief H=3 | dto. | 22 | 5,7 · 5,6 · 5,5 % | 12 · 30 · 36 · 86 % |
| BTC ertrag H=1 | dto. | 22 | 6,3 · 5,4 · 4,2 % | 16 · 34 · 65 · 91 % |
| BTC ertrag H=7 | 2025 – Okt. 2026 | 31 | 6,1 · 5,7 · 5,9 % | 10 · 26 · 54 · 86 % |
| BTC ertrag H=3 | 2021-03 – Okt. 2026 | 137 | 4,5 · 5,3 · 5,0 % | 38 · 82 · 98 · 100 % |
| Breite ertrag H=3 | Dez. 2025 – Sep. 2026 | **18** | kein Befund möglich (Daten fehlen, §7.5) | — |

→ **Bestanden** (alle ≤ 6,5 % = 5 % + 2 Standardfehler). **Auflösung:** im Gemini-Zeitraum wird erst eine Wirkung von **≈ 0,5 σ**
sicher gefunden, über 2021–2026 schon **0,2–0,3 σ**. Ein Sicht-Gutachten muss im Rückspiel also **stark** sein, um gesehen zu werden.

**Gegenprüfung:** der erste Selbsttest fiel **durch** (6,3–8,8 % Fehlalarm). Die Ursache ist gemessen, nicht vermutet: die Nullwelt zog
**zufällige** Verschiebungen ab einer Blocklänge. Mit der **vollen Bahn** (alle n − 1 Verschiebungen = exakter Randomisierungstest) sind es
4,5–6,2 %. Prüfpaket **`G7Messanlage` 7/7**.

### 7.3 Stufe 0c — Vergleichsarm ohne LLM: tragen die Zustände allein?

Rang je Zustand (35), GDELT-Ton als 7-T-Mittel (4) und Zahl der auffälligen Zustände je Sicht (5) gegen `ertrag_s`/`tief_s` von BTC und
Breite, H = 1/3/7, **zweiseitig**, je Epoche 2021-22 · 2023-24 · 2025-26. **Vorab-Regel:** Befund nur, wenn ≥ 2 von 3 Epochen mit gleichem
Vorzeichen außerhalb des Bands liegen.

| | |
|---|---|
| Tests | 1.458 |
| außerhalb des Bands | **163** (ohne Wirkung erwartet ≈ 73) |
| **Befunde** nach Vorab-Regel | **15** |
| **Gegenprobe (c2): alle Zustände GEMEINSAM verschoben**, 166 Verschiebungen — derselbe Zusammenhang zwischen den Tests, kein Bezug zur Zukunft | außerhalb im Mittel 75, **höchstens 143** · Befunde im Mittel 2,0, **höchstens 12** → beobachtet 163 / 15 liegen **über jeder** Nullwelt (Reproduktion von c vorab: 1.458 / 163 / 15 ✔) |

→ **Die Zustände tragen als Ganzes etwas**, vor allem über die **Abwärtsbewegung der Breite** (Altcoins).

Die 15 Befunde (Rangkorrelation; + heißt: höherer Rang → höhere Zielgröße):

| Zustand | Ziel | H | außerhalb (Wert) | Lesart |
|---|---|---|---|---|
| Funding ETH | Breite tief | 1 · 3 · 7 | 2023-24 −0,07/−0,11/−0,17 · 2025-26 −0,09/−0,15/−0,23 | hohe Finanzierung der Long-Seite → tieferer Rückgang |
| Funding BTC | Breite tief | 7 | −0,13 · −0,20 | dto. |
| BTC (Abstand zum 200-T-Schnitt) | Breite tief | 7 | −0,12 · −0,16 | weit gelaufen → tieferer Rückgang |
| ETH (dto.) | Breite tief | 3 | −0,11 · −0,08 | dto. |
| S&P 500 · Nasdaq 100 (dto.) | Breite ertrag | 3 · 7 | −0,11 … −0,20 | Aktien weit über dem Schnitt → Altcoins danach schwächer |
| Finanzlage NFCI | Breite tief | 1 · 3 · 7 | +0,07 … +0,18 | ⚠ straffer → **flacherer** Rückgang — fachlich unerwartet; Fakt, nicht gedeutet |
| Nachrichtenton Aktienmarkt (GDELT) | BTC ertrag | 3 | −0,10 · −0,10 | freundlicher Ton → danach schwächer (gegenläufig) |
| dto., 7-T-Mittel | Breite ertrag | 3 | −0,18 · −0,19 | dto. |
| Zahl auffälliger Zustände in S4 | Breite ertrag | 1 | +0,08 · +0,07 | |

**Hinweise** (nur eine Epoche, fast alle **2025-26** — genau der Rückspiel-Zeitraum): Kreditaufschlag Baa (BTC/Breite, H 1–7,
+0,08 … +0,30), Halbleiter SOXX (−0,07 … −0,21), Nachrichtenton Fed (−0,09 … −0,21), Breite selbst (−0,10 … −0,17).

⚠ **Was das ist und was nicht:**
- Es ist der **Vergleichsarm**, kein Signal: ein Sicht-Gutachten muss im Rückspiel **mehr** tragen als diese Zustände allein — sonst bringt
  das LLM nichts (Stufe 2).
- Einzelne Befunde aus einer Suche über 1.458 Tests sind **Hinweise auf Stärke**, keine registrierten Kandidaten. Bevor einer davon
  irgendwo **gewichtet** wird, braucht er eine eigene Vorab-Messung nach `messnorm` (R-R11, Memory *TRÄGT braucht Band + zweiten Weg*).
- Die Wirkungen sind **klein** (|ρ| 0,07–0,23).

**GDELT-Ton (Auftrag 01.11.):** **Aktienmarkt trägt** (2 Befunde, gegenläufig), **Fed** zeigt nur Hinweise in 2025-26, **Krypto** und
**Krieg/Sanktionen/Zölle** nichts. Das 7-T-Mittel flackert nicht (G7-3) und trägt mindestens so gut wie der Tageswert. → Frage §8.2.

### 7.4 Stufe 0d — Positivkontrolle Wissensstand

Erzwungene Schätzung des BTC-Schlusskurses, Fehler zum echten Kurs (die Kontrolltage 2023/24 müssen klein sein, sonst taugt die Probe nicht):

| Modell | 2023-06 · 2024-03 · 2024-11 (Kontrolle) | 2025-04 · 2025-08 · 2025-10 | **2025-11** · **2025-12** · 2026-02 · 2026-06 | Lesart |
|---|---|---|---|---|
| gemini-3.1-flash-lite | 2 · 0 · 7 % | 50 · **2** · **2** % | 67 · 68 · 130 · 127 % | kennt Kurse **bis Okt. 2025**, ab Nov. nicht → **sauber ab Dez. 2025** |
| gemini-3.5-flash | 0 · 0 · 0 % | 24 · **7** · 29 % | 56 · 68 · 88 · 127 % | Wissen bis etwa Aug. 2025 → sauber |
| gemini-3.5-flash-lite | 0 · 3 · 4 % | **7** · **2** · **10** % | 44 · 45 · 47 · 96 % | bis Okt. 2025 → sauber |
| gemini-3.6-flash | 0 · 0 · 1 % | 33 · 15 · **2** % | 33 · 56 · 130 · 123 % | bis Okt. 2025 → sauber |
| gemini-3.7-flash | — | — | — | **keine Antwort** an Schlüssel 2 (Kontingent/Freigabe) — nicht verwendbar, solange das so bleibt |
| gemini-3.8-flash · gpt-oss-120b | — | — | — | nicht geprüft (kaum Antworten, Groq vom Volllauf belegt) — §9.3 |

→ **Kein erreichbares Gemini-Modell kennt den Kurs ab Nov. 2025** (Fehler ≥ 33 %, bei einer üblichen Monatsschwankung von 10–20 %). Der
Gemini-Zeitraum ab **Dez. 2025** ist damit für alle vier geprüften Modelle sauber; für **2025** sind sie es **nicht** (Aug./Okt. 2025 auf
2–10 % genau). ⚠ Die Probe prüft **Kurswissen**, nicht Ereigniswissen — ein Modell könnte Nachrichten kennen, ohne Kurse zu kennen.

### 7.5 Stufe 0e — Daten

| | |
|---|---|
| **Kurse Sep./Okt. über den Austauschordner** | `nb_auszug_kurse.py` liegt in `Claude_Austauschordner\G7_Kurse\`. Am NB liest es **nur** (`mode=ro`) die zwei REGEL0-Kursdateien ab 01.08. und schreibt **eine** Datei neben sich; es wartet auf Minute 20–50 (der `regel0_nachlader` schreibt ab Minute 5) und verweigert `tradinginfotool.db`. Am Desktop prüft `g7_kurse_einlesen.py` zuerst die **Überlappung** (Betrieb und Messbasis müssen dieselbe Reihe sein) und baut erst dann eine **Arbeitskopie** `data/_g7/kurse/` mit der Marke `_g7_rueckspiel`; die Messbasis bleibt unberührt. **Probelauf am Desktop:** 132.618 + 766.100 Stunden, **0 Abweichungen**, 67 MB |
| **Watchlist zum Zeitpunkt** | Die Grundliste (`Basisinfos/config.yaml`) hat eine Git-Historie erst **ab 30.06.2026**, die Ergänzung am NB genau **einen** Eintrag (KAITO, 15.10.). Für Dez. 2025 – Juni 2026 gibt es **keine** damalige Watchlist — die heutige wäre ein **Vorgriff** (gewählt, als 2025/26 bekannt war). Gemessen Dez. 2025 – Sep. 2026: S7-Börsenereignisse mit der heutigen Watchlist **45**, mit der **REGEL0-Grundgesamtheit zum Zeitpunkt** (127 Werte + Kern) **131**; 72 Werte kämen hinzu, 1 (AIOZ) fiele weg → Frage §8.1 |

---

## 8. Zur Abstimmung (02.11.2026)

### 8.1 Welche Assets bekommt S7 — im Rückspiel und live (Ü8)?

| | Weg | Folge |
|---|---|---|
| **a** | **REGEL0-Grundgesamtheit zum Zeitpunkt + Kern BTC/ETH/SOL** | kein Vorgriff; dieselben Werte, auf die sich die Handlungen beziehen (REGEL0-Einstiege); live wie im Rückspiel; S7-Ereignisse ×2,9 (45 → 131) |
| b | Watchlist von heute | einfacher; im Rückspiel ein Vorgriff (Auswahl nach dem Ergebnis), live ≠ Rückspiel |
| c | Watchlist ab 30.06.2026 aus der Git-Historie, davor die REGEL0-Menge | zeitgetreu, aber ein Bruch mitten im Rückspiel |

**Empfehlung a.** Es ist dieselbe Lösung wie bei G6a (Breite in der Betriebsmenge zum Zeitpunkt). ⚠ Sie ändert die Grundgesamtheit von
S7 — deshalb gemessen (45 → 131) und hier vorgelegt, nicht beiläufig gesetzt.

### 8.2 GDELT-Ton am NB (Entscheidung 01.11.: *erst messen, ob er trägt*)

| | Weg | Folge |
|---|---|---|
| **a** | **in G8 den täglichen GDELT-Abruf am NB bauen, alle vier Töne**, das 7-T-Mittel als zusätzlicher Zustand | live = Rückspiel (Ü8); ein Mechanismus; Aktienmarkt trägt, Fed als Hinweis. ⚠ der Abruf war 29.10.–01.11. oft stundenlang gesperrt (429) — er braucht ein Nachholen über mehrere Tage |
| b | nur den Aktienmarkt-Ton | weniger Abrufe; S2/S7 verlören live ihren Ton-Zustand — Rückspiel ≠ live |
| c | kein GDELT live | die Sichten laufen ohne Ton; der Befund bliebe ungenutzt |

**Empfehlung a.**

**Danach:** NB-Auszug → Kurse einlesen → REGEL0-Einstiege Sep./Okt. nachrechnen → Stufe 1 (Sicht-Gutachten im Rückspiel auf Gemini),
sobald der A1-Volllauf die Nachrichten-Ereignisse fertig hat.

---

## 9. Fachliche Prüfung zu §8 und Ausführung (02.11.2026)

**Auftrag (Nutzer 02.11.):** *„mach eine fachliche prüfung für 8.1 und 8.2 wenn diese passt zur Entscheidung A dann so vorgehen“*.

### 9.1 S7-Assets — Prüfung bestätigt a, mit einer Korrektur der Menge

| Prüffrage | Ergebnis |
|---|---|
| Welche Werte bewertet die REGEL0 **im Betrieb**? | **Nicht** die 127 der Referenz: `regel0_rechnung.lade_reihen_iter` + `betriebs_zusatz` nehmen die Messbasis (> 2.000 Stunden) **und alle** Werte aus `stundenkurse_alle.db` mit ≥ 500 Stunden, ohne die 5 gesperrten (LIT, NEIRO, ONE, QUICK, ZK). Zum Zeitpunkt gezählt: **487** (Dez. 2025) · **530** (Apr. 2026) · **621** (Sep. 2026) Werte |
| Ist a dann noch „Betrieb = Messung“? | Nur mit **dieser** Menge. Mit den 127 der Referenz hätte S7 im Rückspiel weniger Werte als live — genau der Fehler aus 2.487 (*Grundgesamtheit ist keine Stellschraube*) |
| Wirkung, gemessen Dez. 2025 – Sep. 2026 (S7-Börsenereignisse, neu je Tag) | Watchlist heute **45** · Referenz 127 + Kern **131** · **Betriebsmenge zum Zeitpunkt 236** |
| Fehlt etwas? | **Live die Spot-Bestände**: Handlungen sind auch „Bestand Y“ (Fütterung §4); 7 der 46 Watchlist-Werte stehen in **keiner** REGEL0-Datei (u. a. Werte außerhalb Binance). Im Rückspiel misst G7 nur REGEL0-Einstiege, dort gibt es keine Bestände |
| Regel 3 (kein Asset-Vorurteil) | erfüllt — die Menge folgt der Datenlage, nicht einer Auswahl |

→ **a gilt**, genau gefasst: **S7-Assets am Stichtag = was die REGEL0 dann bewertet (gleiche Schwellen, nur Stunden vor T, ohne gesperrte) +
Kern BTC/ETH/SOL + live die Bestände.** Das ist das Prinzip von a; die Zahl ist größer als in §8.1 vorgelegt (dort waren es die 127 der
Referenz). ⚠ **Folge für Stufe 3:** auch die REGEL0-Einstiege des Rückspiels sollten aus der **Betriebsrechnung** über diese Menge kommen,
nicht aus der 127er-Referenz — sonst misst Stufe 3 eine andere Grundgesamtheit als die, die live läuft. Vor Stufe 3 zu messen (Zahl der
Einstiege, Budget).

**Gebaut:** `agent/ereignisse.assets_am(T, ordner, bestand)` (Stundenzahl je Symbol und Tag einmal je Prozess gelesen, `mode=ro`, 9 s);
`zustaende.text` nimmt sie als Vorgabe statt der Watchlist von heute. Prüfpaket `Ereignisse` Nr. 15 (Kunstdateien: Schwellen 2.001/500,
nur vor T, gesperrt, Kern, Bestand) **15/15**; drei Mutationen (alle Stunden statt nur vor T · gesperrte nicht entfernt · Schwelle 2.000)
**alle rot**.

### 9.2 GDELT-Ton am NB — Prüfung bestätigt a, mit zwei Bedingungen

| Prüffrage | Ergebnis |
|---|---|
| Trägt der Ton (Entscheidung 01.11.)? | **Aktienmarkt ja** (Befunde), **Fed** nur Hinweise (2025-26, gleiches Vorzeichen), Krypto/Konflikt nein. Alle Befunde und Hinweise gegenläufig (freundlicher Ton → danach schwächer) |
| Wie stark ist das einzeln? | **Schwach.** Aus einer Suche mit im Mittel 2 Zufallsbefunden (c2) sind 2–3 Befunde einer Reihe kein Nachweis. Der Ton ist ein **Zustand in der Sicht**, kein gewichtetes Signal — das bleibt so |
| Warum dann live? | **Ü8:** die Sichten bekommen den Ton im Rückspiel; fehlt er live, gilt der gemessene Wert eines Gutachtens nicht für das, was läuft. Die Alternative wäre c (Ton auch aus dem Rückspiel nehmen) — dann bliebe der Befund ungenutzt |
| Welche Form? | **Nachgemessen (c3, `g7_stufe0_c3.txt`)** — gebaut ist der Rang des **7-T-Mittels der Tonwerte**, gemessen hatte c das 7-T-Mittel der **Ränge**. Ergebnis: Aktienmarkt Tageswert 1 Befund (reproduziert c: −0,103/−0,101), **7-T-Mittel 2 Befunde** (Breite ertrag H=1: −0,086/−0,098; H=3: −0,183/−0,185) + 10 Hinweise; Fed 0/12 bzw. 0/4; Konflikt 0/2; Krypto 0/0 |
| Ist der Abruf am NB machbar? | **Ungeprüft.** 29.10.–01.11. am Desktop oft stundenlang 429. Vier Abrufe am Tag, über den Tag verteilt, mit Nachholen, sind etwas anderes als der Historien-Abruf — aber das ist eine Vermutung |

→ **a gilt**, mit zwei Bedingungen für G8:
1. **NB-Nachweis vor dem Betrieb** (Memory *Datenquellen-Inventar + Abdeckung am NB*): zwei Wochen Probeabruf, je Tag vier Töne, Lücken
   gezählt. Hält er nicht, wird **c** neu vorgelegt (Ton auch im Rückspiel weg — Ü8).
2. Der Ton bleibt **Zustand**, nie Auslöser oder Gewicht ohne eigene Vorab-Messung.

**Gebaut:** vier Zustände **„Nachrichtenton …, 7-T-Mittel“** (`zustaende.DEFINITIONEN`, Maß `mittel7`, Symbol `<x>~7T` = dieselbe Reihe,
eigener Schlüssel für den Prüfer v2) — jetzt **42** Zustände. Prüfpaket `Zustaende` Nr. 15 **15/15**.

### 9.3 Positivkontrolle — Nachtrag

gemini-3.8-flash antwortete nur an 2 von 10 Tagen (Nov./Dez. 2025: 64 % / 45 % daneben — kein Wissen), gpt-oss-120b nur an einem
Kontrolltag (4 %): das Groq-Kontingent ist vom A1-Volllauf belegt. **Beide sind damit nicht geprüft** → vor einem Einsatz nachholen
(gpt-oss nach dem Volllauf).

### 9.4 Stand

| | |
|---|---|
| NB-Auszug Kurse | **wartet auf den Nutzer** (Anleitung: im NB-Projektordner `python "G:\Meine Ablage\Claude_Austauschordner\G7_Kurse\nb_auszug_kurse.py"`) |
| danach | `g7_kurse_einlesen.py` → REGEL0-Einstiege Sep./Okt. **aus der Betriebsrechnung** (9.1) → Stufe 1, sobald die A1-Nachrichten fertig sind |
| G8-Bündel | Z-1-Zahlenerkennung (§6.2) · GDELT-Abruf mit zwei Wochen Nachweis (9.2) · S7 live mit Beständen (9.1) |
