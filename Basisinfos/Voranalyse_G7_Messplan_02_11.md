# Voranalyse G7 — Messplan: Faktentreue der Prüfer und Wert der Sichten (02.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 02.11.):** *„ja, starte mit der Voranalyse G7 – prüfen, gegenprüfen und doku“*.
**Gehört zu:** [`Datenbasis_Schichten_Sichten_28_10.md`](Datenbasis_Schichten_Sichten_28_10.md) §3a (Frage je Sicht, finales LLM, „Warum das
messbar ist“) und §6 Schritt 3 · [`Bauplan_Dashboard_A3_A4_28_10.md`](Bauplan_Dashboard_A3_A4_28_10.md) §6 (Faktentreue 100 %, Selbsttest
Prüfer ≥ 1.000 je Art) · [`Fuetterung_Satzform_31_10.md`](Fuetterung_Satzform_31_10.md) §4 (Blöcke des finalen LLM), §5 (Takt), §6 Schritt 5 ·
[`Voranalyse_Luecken_Prompt_Gesamtplan_28_10.md`](Voranalyse_Luecken_Prompt_Gesamtplan_28_10.md) T4–T7 (Budget, Modelle) ·
[`Voranalyse_A1_Ereignisleser_01_11.md`](Voranalyse_A1_Ereignisleser_01_11.md) (Ereignisse) · Gesamtplan G3 (Modelle, Reihenfolge) · G7.
**Stand:** Voranalyse — **nichts gebaut, kein LLM-Aufruf, Betrieb unberührt.** Gemessen nur lesend (`sichten.db`, Kursdaten, REGEL0-Referenz)
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
