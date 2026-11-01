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
| **SF2** | **Maß je Art:** Zinsen, Aufschläge, Schwankung, Prämien, Ton, Funding, Breite als **Niveau** · Preise als **Abstand zum 200-T-Schnitt** · Mengen (M2, Netto-Liquidität) als **Veränderung gegen Vorjahr** · **Krypto-Mengen (Stablecoins, OI in Coins) als Veränderung über 30 Tage** (Nutzer 01.11.: „1a“) · **Kategorien (Season-Stufe) ohne Rang**, mit „seit“ | ein Niveau-Rang von Preisen steht in steigenden Märkten fast immer oben und sagt nichts. Krypto-Mengen: die Frage an S1 ist Abfluss/Hebel in 1–7 Tagen, ein Jahresvergleich zeigt das kaum ([`Voranalyse_S1_Ergaenzung_01_11.md`](Voranalyse_S1_Ergaenzung_01_11.md)) |
| **SF3** | **Klasse aus dem Rang**, fest: ≤ P5 sehr tief · ≤ P20 tief · normal · ≥ P80 hoch · ≥ P95 sehr hoch | ein Wort über die Lage ist ein **Fakt** (Gegenwart), keine Bewertung (Ü2) |
| **SF4** | **Lesart je Zustand fest im Code** — was HÖHER heißt, beschreibend | ohne sie ist „hoch“ mehrdeutig: beim **Nachrichtenton** heißt hoch *freundlicher*, beim **VIX** *mehr Angst*. Die Lesart sagt nie „gut/schlecht für Krypto“ — das ist die Frage an die Sicht |
| **SF5** | **Stand je Zeile** (Datum der Beobachtung) | M2 stand am 29.10. beim **01.09.** — zwei Monate alt; ohne Stand liest das LLM ihn als heutig |
| **SF6** | **Alle** Zustände einer Sicht gehen hinein, auffällige mit **●** markiert | 24 Zustände = **4.712 Zeichen ≈ 1.260 Token** — kein Grund zu kürzen. Ob *nichts Besonderes* ist, entscheidet die Sicht (F2), nicht ein Vorfilter |
| **SF7** | **Ein Fenster für alle: 5 Jahre** — wie der Rang von K1–K9 in `makro_lage` | ein Rang ist ein Perzentil; **wer das Fenster ändert, ändert jeden Wert** (Grundgesamtheit). Kürzere Fenster werden mit ⚠ ausgewiesen, nie still |
| **SF8** | **Ein Rechenweg** für live und Rückspiel: die Zeilen entstehen aus `sichten.db` am Stichtag mit dem **damals gültigen Jahrgang** (`bekannt_ab ≤ T`, ~~`bis ≥ T`~~ **`bis` + 1 T ≥ T** — korrigiert 01.11., Z1: der Nachfolger ist erst am Tag `bis` + 2 bekannt) | Ü8; ohne Jahrgänge wäre jeder revidierte FRED-Wert ein Vorgriff. Gebaut in `agent/zustaende.py` |
| **SF9** | ⚠ **veraltet**, wenn das Alter des Stands über dem 99. Perzentil der **eigenen** Alter im Fenster liegt (*„⚠ Stand 39 T alt (üblich ≤ 20 T)“*) — neu 01.11. | das Alter ist je Zustand sehr verschieden (Krypto 1 T, M2 im Median 70 T); SF5 zeigt das Datum, aber nicht, dass es **ungewöhnlich** alt ist ([`Voranalyse_Zustaende_Modul_01_11.md`](Voranalyse_Zustaende_Modul_01_11.md) Z4) |

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
| 2 | **S1 ergänzen** um Trend, Breite, DVOL, Stablecoins, Funding/OI als Reihen mit `bekannt_ab` (P2) — **✔ 01.11. geladen und gegengeprüft**, [`Voranalyse_S1_Ergaenzung_01_11.md`](Voranalyse_S1_Ergaenzung_01_11.md) §5; Breite Desktop ↔ NB (V2/G6a) ✔ gelöst 01.11. abends (§6 dort: Grundgesamtheit des Betriebs zum Zeitpunkt) | Desktop | nein |
| 3 | **Ebene-1-Modul** `agent/zustaende.py`: die Satzform aus §1 als **ein** Rechenweg (SF8), Probe → Modul, mit Prüfpaket (Fenster, Vorgriff, Lesart je Zustand vorhanden) — **✔ 01.11. gebaut** (Weg a, mit S8 Termine; §7 der Voranalyse) · **Voranalyse 01.11.** [`Voranalyse_Zustaende_Modul_01_11.md`](Voranalyse_Zustaende_Modul_01_11.md): die Probe hat ein **Jahrgangsloch** (Z1) und stürzt bei leerer Reihe ab (Z2) | Desktop | nein |
| 4 | **Voranalyse A1** (G9) — Regeln zuerst, LLM für den Rest — **01.11. zur Abstimmung** [`Voranalyse_A1_Ereignisleser_01_11.md`](Voranalyse_A1_Ereignisleser_01_11.md) | Desktop | nein |
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

✔ **Entschieden 31.10.2026 (Nutzer: *„a, Historie ab 2020 laden“*)** — Ausführung in §8.

---

## 8. Ausführung — Historie ab 2020 (31.10./01.11.2026)

**Abrufer** `api/sichten_quellen.py`: `START` 2023-01-01 → **2020-01-01**, sonst derselbe Weg (Ü8). Sicherung des alten Stands:
`data/_sichten/sichten_vor_2020_31_10.db`.

| Quelle | Ergebnis |
|---|---|
| yfinance (9) | ✔ ab 2020-01-02 |
| FRED (13) | ✔ **neu geladen statt ergänzt**: der alte Lauf hatte 10.831 Zeilen mit `bekannt_ab` auf 02.01.2023 **gekappt** (ALFRED setzt ältere Gültigkeitsbeginne auf `realtime_start`). Ergänzen hätte sie doppelt stehen lassen. Jetzt Jahrgänge ab 2020, Beobachtungen ab 2018 wie bisher |
| Coinbase-Prämie BTC/ETH | ✔ ab 2020-01-01 |
| Basis Quartal BTC/ETH | ✔ ab **2021-02-03** — früher führt Binance keine USDT-Quartalskontrakte. Im Rückspiel ab 01.12.2025 = 4,8 J, innerhalb der Toleranz |
| **BAMLH0A0HYM2** Hochzins-Aufschlag | ✖ FRED führt ihn (ICE-Lizenz) nur ab **10/2023** → im Rückspiel 2,1 J und ein wachsendes Fenster (verletzt SF7). **Ersetzt durch `BAA10Y`** (Baa − 10 J, Jahrgänge ab 2018), dieselbe Art Aufschlag. Die Reihe bleibt in `sichten.db`, geht aber nicht in die Fütterung |
| GDELT-Ton (4) | ◐ bis auf **2022** (fed, aktien, krypto) geladen; Juni-2025-Lücke dokumentiert — siehe P6 und unten |

**Zwei Fehler im Abrufer, behoben:**
1. Ein vorverlegter Start wurde bei GDELT **nicht nachgeholt** (die Fortsetzung begann am letzten Tag). Jetzt: erst die **erste Lücke über 7 Tage** (`_erste_luecke`), dann die Fortsetzung. Dabei gefunden: **alle vier GDELT-Reihen haben eine 18-Tage-Lücke ab 14.06.2025** aus dem Lauf vom 29.10. — bisher von keiner Prüfung bemerkt.
2. Zwischen zwei Jahresfenstern lagen **6 s** → das zweite Fenster immer 429. Jetzt der volle GDELT-Abstand. Außerdem wurde ein Randtag 31.12. als eigenes 1-Tages-Fenster geholt — eine verschenkte Anfrage.

**Probe ergänzt:** Lückenprüfung im Fenster (Lücke > max(10 T, 5 × üblicher Abstand) zählt wie ein kurzes Fenster). Ohne sie
meldete die Probe für GDELT Krypto ein volles 5-J-Fenster, obwohl 2021–22 fehlten.

| # | Befund | Folge |
|---|---|---|
| P6 | **GDELT liefert nicht verlässlich.** Je Lauf kam meist nur die **erste** Anfrage durch; danach 429 über **Stunden**, auch nach 10, 20 und 40 Min. Abstand (01.11. 01:23–03:15 UTC drei Sperren in Folge). Am 29.10. scheiterten auch einzelne kurze Abrufe wie im laufenden Takt | **Für den Betrieb (G8):** täglicher GDELT-Abruf am NB ist **nicht gesichert** — vor dem Bau klären: Abstand von Stunden, oder die GDELT-Tagesdateien (GKG) statt der DOC-Schnittstelle. Die Karte zeigt den Stand je Zeile (SF5), ein alter Ton ist sichtbar alt. Datenbasis §4 |

**P6 — Ursache recherchiert, Weg entschieden (01.11.2026)**

| | |
|---|---|
| **Belegt** | GDELTs Grenze ist strenger als die dokumentierten 5 s: ein anderes Projekt maß im **September 2026** 3 von 3 Abweisungen bei **30 s** Abstand nach der Antwort, auch bei der leichtesten Abfrage (`artlist`, 1 Artikel), **ohne** `Retry-After`; eine ausgelöste Sperre „klebt“, auch über Sitzungen (github.com/cyanheads/gdelt-mcp-server, Issues #44, #16, #26). Unsere Logs: 46 Abweisungen, auch bei 40–60 Min. Abstand |
| **Selbst verursacht (behoben)** | 29./30.10. fünf Wiederholungen je Fenster, 6 s zwischen Jahresfenstern, Randtag 31.12. — haben die Sperre verlängert, erklären sie aber nicht |
| **Nicht belegt** | ob unsere schweren Jahresfenster mehr zählen; Vermutung: GDELT drosselt nach Gesamtlast. Von außen nicht messbar |
| Gemessen: Rohdateien | GKG je 15 Min. 1,9–6,5 MB → 200–600 MB/Tag, Historie ab 2020 ≈ 0,5–1 TB — andere Größe (Themen statt Suchbegriff), Ü8 verlangte dann auch die Historie daraus |

**Entscheidung (Nutzer 01.11.: „Weg 1 – vorher klären, ob Daten und Messung etwas bringen, wenn bestätigt überlegen, wie wir die
Daten auf das NB bringen bzw. zuverlässige Abrufe für die Produktion generieren“):** DOC-Schnittstelle wie bisher, Historie fertig laden.
**Zuerst** in A1/G7 messen, ob der Ton etwas beiträgt. **Nur wenn ja:** NB-Weg und zuverlässiger Produktionsabruf (Kandidaten: 4
kleine Anfragen je Tag mit Nachholen und gemessener Ausfallquote; BigQuery-Tabelle, kostenfreies Kontingent). Bis dahin **kein**
GDELT-Abruf am NB, nichts im NB-Bündel.

**GDELT vom kritischen Pfad genommen (Nutzer 01.11. mittags: „sorge dafür, dass die GDELT Sache endlich erledigt ist, dieser
Datenabruf ist eine massive Hürde“):**

| | |
|---|---|
| Geholt bis 01.11. 11:30 UTC | fed, aktien, krypto **2020–2021**; konflikt **2020–2026**; alle ab 2023 (Lauf 29.10.) |
| ~~Wird noch geholt~~ ✔ **geholt 01.11.** | **2022** für fed, aktien, krypto — je Reihe eine Anfrage (krypto 12:25, fed 13:25, aktien nach einer 429-Sperre 16:34 UTC), danach Ende. **GDELT ist damit abgeschlossen:** alle vier Reihen 2.453 Tage, 2020-01-01 bis 2026-10-27 |
| Verbleibende Lücken (alle vier Reihen gleich) | **2025-06-14 bis 07-01** (18 T, dokumentiert, Probe weist sie aus) · Einzeltage 2020-10-20, 2023-03-23 · 2026: 07-01–07-04, 09-14–09-19, 09-26, 10-03–10-05, 10-07, 10-09, 10-11–10-14. ⚠ Die 2026er Lücken weist die Probe nicht einzeln aus (sie nennt die größte) — **nicht nachgeholt**, jede weitere Anfrage riskiert die Sperre; für die Messung (G7) als bekannte Lücken führen |
| Wird **nicht** mehr geholt | die **18-Tage-Lücke 14.06.–01.07.2025** in allen vier Reihen: 18 von ~2.100 Tagen, keine Fensterfrage. **Dokumentierte Lücke** — die Tage fehlen (kein Auffüllen, keine Interpolation); die Probe meldet sie mit „⚠ Lücke“, das ist erklärt |
| Was **nicht** mehr wartet | Probe, S1-Ergänzung, Ebene-1-Modul und Voranalyse A1 laufen weiter, ohne auf GDELT zu warten. Fehlt 2022 bei Beginn von A1, geht der Ton dort mit **kurzem Fenster** gekennzeichnet ein (SF7), nicht gar nicht |
