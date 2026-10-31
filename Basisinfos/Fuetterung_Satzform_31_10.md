# Fütterung Weg a — die Satzform der Zustände und was jede Stufe bekommt (31.10.2026 abends)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 31.10.):** *„ok, weiter mit dem Fütterungskonzept für Weg a“*.
**Gehört zu:** [`Datenbasis_Schichten_Sichten_28_10.md`](Datenbasis_Schichten_Sichten_28_10.md) (Ebenen, Ü1–Ü9, Fragen je Sicht §3a,
Reihenfolge §6 Schritt 2) · [`Bauplan_Dashboard_A3_A4_28_10.md`](Bauplan_Dashboard_A3_A4_28_10.md) (wartet auf die Fütterung).
**Stand:** Vorlage zur Abstimmung. **Nichts am Betrieb geändert**, nichts geladen. Probe nur lesend auf `data/_sichten/sichten.db`.

---

## 0. Was schon steht — und was dieses Blatt schließt

| Teil der Fütterung | Stand |
|---|---|
| Ebenen 0–4, Übergaberegeln Ü1–Ü9 | ✔ 28.10. (Datenbasis §1) |
| Frage je Sicht, Ergebnisschema der Sichten, Frage des finalen LLM | ✔ 28.10. (Datenbasis §3a) |
| Sichten-Reihenfolge S1–S4, S7, S8 | ✔ 29.10. (G2) |
| Quellen der Sichten nachgewiesen, Abrufer `api/sichten_quellen.py`, live = Rückspiel | ✔ 29./30.10. (G4) |
| Wal-Zustand je Asset | ✔ 31.10. (Datenbasis §8) |
| **Satzform der Zustände** (Ü1) — *wie* ein Zustand als Text aussieht | **offen → §1–§2** |
| **Was jede Stufe konkret bekommt**, in welcher Reihenfolge und welchem Takt | **offen → §3–§5** |

---

## 1. Die Satzform — ein Zustand, ein Satz

**Gebaut und an einem echten Tag geprüft** (`Rechenkern_02_10/fuetterung_satzform_probe.py`, Stichtag 29.10.2026 00:00 UTC):

```
● [S2] Realzins 10 J 2.64 % · Rang P98 der letzten 5.0 J (ab 2021-10) = sehr hoch (höher = teureres Geld nach Inflation) · vor 4 Wochen +2.91 · Stand 2026-10-27 · Fakt
● [S4] Öl Brent 115.32 USD, +25.4 % zum 200-T-Schnitt · Rang P92 der letzten 3.2 J (ab 2023-08) = hoch (höher = weiter über dem eigenen Schnitt) · vor 4 Wochen +18.56 · Stand 2026-10-28 ⚠ Fenster nur 3.2 J · Fakt
  [S3] VIX 16.9 · Rang P54 der letzten 3.8 J (ab 2023-01) = normal (höher = Aktienmarkt erwartet größere Schwankung) · vor 4 Wochen +16.34 · Stand 2026-10-28 ⚠ Fenster nur 3.8 J · Fakt
```

| # | Regel | Warum (aus der Probe) |
|---|---|---|
| **SF1** | Je Zustand **eine Zeile**: Sicht · Name · Wert · Maß · **Rang P** im Fenster · **Klasse** · **Lesart** · vor 4 Wochen · **Stand** · Kennzeichen | Ü1, Ü3: alles, was das LLM zur Einordnung braucht, steht in der Zeile, nicht im Prompt |
| **SF2** | **Maß je Art:** Zinsen, Aufschläge, Schwankung, Prämien, Ton als **Niveau** · Preise als **Abstand zum 200-T-Schnitt** · Mengen (M2, Netto-Liquidität) als **Veränderung gegen Vorjahr** | ein Niveau-Rang von Preisen steht in steigenden Märkten fast immer oben und sagt nichts |
| **SF3** | **Klasse aus dem Rang**, fest: ≤ P5 sehr tief · ≤ P20 tief · normal · ≥ P80 hoch · ≥ P95 sehr hoch | ein Wort über die Lage ist ein **Fakt** (Gegenwart), keine Bewertung (Ü2) |
| **SF4** | **Lesart je Zustand fest im Code** — was HÖHER heißt, beschreibend | ohne sie ist „hoch“ mehrdeutig: beim **Nachrichtenton** heißt hoch *freundlicher*, beim **VIX** *mehr Angst*. Die Lesart sagt nie „gut/schlecht für Krypto“ — das ist die Frage an die Sicht |
| **SF5** | **Stand je Zeile** (Datum der Beobachtung) | M2 stand am 29.10. beim **01.09.** — zwei Monate alt; ohne Stand liest das LLM ihn als heutig |
| **SF6** | **Alle** Zustände einer Sicht gehen hinein, auffällige mit **●** markiert | 24 Zustände = **4.712 Zeichen ≈ 1.260 Token** — kein Grund zu kürzen. Ob *nichts Besonderes* ist, entscheidet die Sicht (F2), nicht ein Vorfilter |
| **SF7** | **Ein Fenster für alle: 5 Jahre** — wie der Rang von K1–K9 in `makro_lage` | ein Rang ist ein Perzentil; **wer das Fenster ändert, ändert jeden Wert** (Grundgesamtheit). Kürzere Fenster werden mit ⚠ ausgewiesen, nie still |
| **SF8** | **Ein Rechenweg** für live und Rückspiel: die Zeilen entstehen aus `sichten.db` am Stichtag mit dem **damals gültigen Jahrgang** (`bekannt_ab ≤ T`, `bis ≥ T`) | Ü8; ohne Jahrgänge wäre jeder revidierte FRED-Wert ein Vorgriff |

---

## 2. Was die Probe außerdem gezeigt hat — fünf Befunde

| # | Befund | Folge |
|---|---|---|
| **P1** | **18 von 24 Zuständen haben kein 5-J-Fenster.** `sichten.db` lädt yfinance, Krypto und GDELT **ab 2023**; Preise mit 200-T-Schnitt sind erst ab **2023-08** einordenbar (3,2 J). Im Rückspiel ab **Dez. 2025** wären es nur **2,3–2,9 J**, und das Fenster **wüchse** während des Rückspiels — die Grundgesamtheit des Rangs änderte sich Tag für Tag | **Historie ab 2020-01 nachladen** (§6, zur Abstimmung). FRED liegt schon ab 2018 vor ✔ |
| **P2** | **S1 ist in `sichten.db` unvollständig.** Dort liegen nur Basis, Coinbase-Prämie und Nachrichtenton. BTC-Trend, Season-Ampel/Breite, DVOL, Stablecoin-Angebot und Funding/OI werden im Betrieb von **eigenen Modulen** gerechnet — **ohne Reihe mit `bekannt_ab`** | diese fünf als Ebene-1-Reihen ergänzen. Quellen am Desktop: `stundenkurse_alle.db` (Trend, Breite), `funding_historie.db`, Stablecoins verkettet (DefiLlama + CoinMetrics), DVOL-Historie von Deribit **[U]** |
| **P3** | **Zwei Wahrheiten drohen.** Die Mail zeigt K1–K9 aus `makro_lage` (FRED live, fester Verzug), die Sicht bekäme denselben Realzins aus ALFRED-Jahrgängen. Weichen die Ränge ab, widerspricht die Karte der Mail | Ziel: **die Mail liest dieselben Ebene-1-Zeilen**. Vorher ein Abgleich am NB (`makro_lage.json` liegt nur dort) — ins nächste NB-Bündel |
| **P4** | **„vor 4 Wochen“ ist der Wert des Maßes**, nicht die Veränderung (SOXX: heute +9,9 %, vor 4 Wochen +25,7 % über dem Schnitt) | so lassen; in der Lesehilfe des Prompts **einmal** erklärt. Eine Differenz wäre bei Rängen und Abständen missverständlich |
| **P5** | Am Stichtag sind **10 von 24 auffällig** (Coinbase-Prämie P6, Krypto-Ton P3, Realzins P98, Gold P1, Brent P92 …) | bei fünf Klassen mit 40 % Rand ist das **erwartbar** (Soll ≈ 40 %). „Auffällig“ ist Markierung, kein Alarm — die Sicht wägt |

---

## 3. Ereignisse — sie kommen NUR über den Ereignis-Leser A1

| | |
|---|---|
| **Form** | je Ereignis eine Zeile: Zeit (UTC) · Asset oder Bereich · Typ (Delisting, Hack, Freigabe, Listing, Klage, Regulierung, Makro …) · Schwere · **neu seit** · Beleg (Quelle, Link) · Kennzeichen *Ereignis* |
| **Regel** | Sichten bekommen **nie Rohmeldungen** (gemessen: 11.500 statt 1.100–2.000 Token, Voranalyse_Luecken T1) |
| **GDELT-Ton** | ist **Stimmung**, kein Ereignis — er steht als Zustand in S1/S2/S3/S7 |
| **Stand** | A1 ist **nicht entworfen** (G9: 6.276 Binance-Meldungen geladen, Voranalyse A1 offen). Bis dahin bekommt S7 nur Binance/Upbit-Ankündigungen in derselben Zeilenform, **regelbasiert** (Delisting, Monitoring, Listing) |

---

## 4. Was das finale LLM je Handlung bekommt — Reihenfolge fest

| Block | Inhalt | Form | ≈ Token |
|---|---|---|---|
| **1 Die Handlung und ihre Wette** | „REGEL0-Einstieg X, 24 h, setzt auf …“ / „Bestand Y, Spot, Wochen“ | ein Satz, aus dem Code (P1: *LLM-Rolle muss die Wette kennen*) | 50 |
| **2 Asset-Zustände** | Kurs-Lage (Abstand 200 T), REGEL0-Lage, Verwässerung (Fünftel), **Wal-Zustand** (nur oben/unten), Bestand und Ergebnis **zum Schlusskurs**, Hebel-Abstand | Satzform §1 | 300–500 |
| **3 Ereignisse zum Asset** | aus A1 bzw. den Ankündigungen | §3 | 0–300 |
| **4 Sicht-Ergebnisse** | je Sicht **nur das Schema** (Zustand, Wirkung, Horizont, neu seit, eingepreist, Treiber mit Beleg, kippt wenn, Gegenargument) | Ü4, kein Fließtext | 800–1.200 |
| **5 Befund-Karte** | die geltenden Befunde **des Strangs** mit Zahl und Grenzen | A3 | 500–800 |

Gemessen (Voranalyse_Luecken B): **≈ 3.000 Token**. Der **Gegenanwalt A4** ist ein **eigener Aufruf** mit einem **anderen Modell** (Ü7) und bekommt dieselben Blöcke plus das Ergebnis des finalen LLM.

---

## 5. Takt — dieselbe Regel live und im Rückspiel

> **Ein Sicht-Gutachten wird neu erstellt, wenn ein Zustand der Sicht die Klasse wechselt oder ein Ereignis der Sicht eintrifft — sonst gilt das letzte weiter, mit seinem Alter, spätestens 7 Tage.**

| | |
|---|---|
| Warum | Ü5: ein Gutachten über unveränderte Zustände bringt keine neue Information. Und die Regel halbiert etwa den Bedarf im Rückspiel (T6), **ohne** dass live und Rückspiel verschieden laufen (Ü8) — ein fester Wochentakt für S2/S4 hätte genau das gebrochen |
| finales LLM | je Handlung (REGEL0-Signal, Bestand einmal täglich), wie im Bauplan |
| Protokoll | jede Eingabe und jede Ausgabe mit Zeitstempel (P6, Ü6) — sonst ist der Beitrag einer Sicht nicht messbar |

---

## 6. Reihenfolge danach

| # | Schritt | Gerät | Betrieb? |
|---|---|---|---|
| 1 | **Historie ab 2020-01** in `sichten.db` (P1) — derselbe Abrufer, nur früherer Start | Desktop | nein |
| 2 | **S1 ergänzen** um Trend, Breite, DVOL, Stablecoins, Funding/OI als Reihen mit `bekannt_ab` (P2) | Desktop | nein |
| 3 | **Ebene-1-Modul** `agent/zustaende.py`: die Satzform aus §1 als **ein** Rechenweg (SF8), Probe → Modul, mit Prüfpaket (Fenster, Vorgriff, Lesart je Zustand vorhanden) | Desktop | nein |
| 4 | **Voranalyse A1** (G9) — Regeln zuerst, LLM für den Rest | Desktop | nein |
| 5 | **G7 Messplan**: Faktentreue der Prüfer + Wert der Sichten im Rückspiel | Desktop | nein |
| 6 | **G8 Bau** B1–B6 + Ebenen 2/3, Abgleich Mail ↔ Ebene 1 am NB (P3) | beide | ja, ein Bündel |

---

## 7. Zur Abstimmung — eine Frage

**Wie weit laden wir die Historie der Sichten-Quellen nach?** (P1, Schritt 1)

| | Weg | Folge | Einschätzung |
|---|---|---|---|
| **a** | **ab 2020-01** — 5-J-Fenster für das ganze Rückspiel ab Dez. 2025, gleich dem Fenster von K1–K9 | yfinance 9 Reihen, Coinbase-Prämie, Basis Quartal (BTC/ETH-Quartalsfutures gibt es bei Binance USDT-M vermutlich erst ab ~2020/21 **[U]** — dann dort kürzer und mit ⚠), GDELT 4 Abfragen (≈ 2 h wegen 10 Min. Abstand). Klein, frei, derselbe Abrufer | **Empfehlung**: ein Fenster für alles, und das Fenster wächst im Rückspiel nicht |
| b | ab 2022-06, Fenster **3 J** für alle (auch FRED) | weniger zu laden | Rang ungleich K1–K9 (5 J) → zwei Wahrheiten zwischen Mail und Karte (P3) |
| c | nichts laden, Fenster „seit 2023“ | sofort | **verletzt SF7/Ü8**: das Fenster wächst im Rückspiel von 2,9 auf 3,8 J — die Ränge sind über die Zeit nicht vergleichbar |

Die Punkte SF1–SF8, §4 und §5 sind **fachlich begründet** und hier nicht zur Wahl gestellt — Einwände natürlich willkommen.
