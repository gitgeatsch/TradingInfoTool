# Voranalyse G7 Stufe 3 — das finale LLM je REGEL0-Einstieg, mit Vorprüfung (08.11.2026)

> Zurück zum laufenden Plan: [`Gesamtplan.md`](Gesamtplan.md) · Grundlage: [`Voranalyse_G7_Messplan_02_11.md`](Voranalyse_G7_Messplan_02_11.md)
> §11 (Messanlage, Menge b), [`Fuetterung_Satzform_31_10.md`](Fuetterung_Satzform_31_10.md) §4, [`Datenbasis_Schichten_Sichten_28_10.md`](Datenbasis_Schichten_Sichten_28_10.md)
> §3a und Ü1–Ü9, [`Vorabfestlegung_Scheideweg_Ende_November_08_11.md`](Vorabfestlegung_Scheideweg_Ende_November_08_11.md) · E-174

Nutzer 08.11.: *„können wir die Prüfung so anlegen, dass die langen läufe nur erfolgen wenn wir einen Hinweis darauf haben, dass es
funktioniert. Das sind weitere Tage die vergehen und wir ggf. am Ende ohne Lösung dastehen.“* → *„1 Vorprüfung“* (E-174).

**Kein Blick auf ein Urteil gegen Kurse.** Es gibt noch kein Urteil. Entschieden sind die **Zweistufigkeit** (E-174, §4) und
der **Inhalt** (E-175, Nutzer 08.11.: *„Ja, alle vier“* — die Vorschläge in §0 Punkte 2–5). Bau: §7.

## 0. Das Ergebnis in sechs Sätzen

1. **Entschieden (E-174):** Stufe 3a prüft auf 321 Einstiegen mit Abbruchregel; 3b läuft nur, wenn 3a die Hürde nimmt. Entwurf und
   Hürde kommen aus zwei Selbsttests nach vorab festgelegter Regel (§4).
2. **Vorschlag:** A4 Gegenanwalt und die Befund-Karte (Block 5) gehören **nicht** in diese Messung (S3-1, S3-3).
3. **Vorschlag:** Block 2 enthält nur, was es im Rückspiel gibt (Kurs-Lage, REGEL0-Lage, Hebel-Abstand), live gleich (Ü8, S3-2).
4. **Vorschlag:** Block 3 ohne Schwere-Texte (wären ein Vorgriff, S3-4), mit ergänzter Asset-Zuordnung.
5. **Vorschlag:** **ein** Informationszeitpunkt je Einstieg für alle Blöcke (S3-5).
6. Bei WEITER wird gemessen wie am 02.11. festgelegt (Menge b, Arm HANDEL, a und b getrennt, beide Richtungen). Bei ENDE gilt §4.3.

---

## 1. Was das finale LLM ist

| | |
|---|---|
| **Frage** (Datenbasis §3a, wörtlich) | *„Spricht die Gesamtlage dafür, diese Handlung **wie geplant**, **vorsichtiger** (kleiner, kürzer, enger) oder **nicht** auszuführen? Nenne die zwei entscheidenden Gründe und was dich umstimmen würde.“* |
| **Antwort** | Bedenken-Stufe 0 (wie geplant) / 1 (vorsichtiger) / 2 (nicht), zwei Gründe mit Beleg, was umstimmt — als JSON (Ü4) |
| **Rolle** | entscheidet nicht (Ü9); erst Information in der Mail, Gewicht nur nach Messung |
| **Modell** | gemini-3.5-flash-lite, Schlüssel 2 — derselbe Topf wie Stufe 1; Wissensstand sauber ab Nov. 2025 (Messplan §7.4). **Modellkennung je Aufruf protokollieren** (zwischen 3a und 3b liegen Tage) |

## 2. Befunde und Vorschläge zum Inhalt

### S3-1 A4 ist nicht Teil der Bedenken-Messung (Vorschlag)

Fütterung §4 (31.10.): A4 ist *„ein eigener Aufruf mit einem anderen Modell (Ü7) und bekommt dieselben Blöcke **plus das Ergebnis des
finalen LLM**“*. Er läuft also nach dem finalen LLM, die Bedenken-Stufe hängt nicht von ihm ab. Datenbasis §3a (28.10.) nennt A4 noch
als Eingabe; Fütterung ist die jüngere Fassung. → Stufe 3 misst **ohne** A4. Ob und wann A4 eine eigene Messung bekommt, ist eine
**eigene Abstimmung**. Die Pläne, die A4 noch führen (Scheideweg §2.2, Messplan §11.5 Budget), werden nachgezogen, wenn das angenommen ist.

### S3-2 Block 2 im Rückspiel (Vorschlag)

| Teil (Fütterung §4) | im Rückspiel Dez. 2025 – Okt. 2026 | Vorschlag |
|---|---|---|
| Kurs-Lage (Abstand 200 T) | ✔ aus der Kurs-Arbeitskopie | **hinein**; bei Assets mit < 200 Tagen Kurs der feste Text „200-T-Schnitt: zu kurze Reihe“, live gleich |
| REGEL0-Lage (Signalstunde, Stufe) | Modelle ohne Vorgriff (Monatsfenster, Schrumpfung aus dem Vormonat). ⚠️ Beim Bau gefunden (§7): `vh` und `stufe` der Mengendatei sind die der **Einstiegsstunde** | **hinein, aber ohne v̂ und mit der vorläufigen Stufe** (§7) |
| Hebel-Abstand (Liquidation bei Stufe) | ✔ rechnerisch | **hinein**, aus Daten bis zum Informationszeitpunkt (S3-5) |
| Verwässerung (Fünftel) | Umlaufmenge vorhanden, aber Zeitpunkt des Wissens unklar (CoinGecko korrigiert rückwirkend), Fünftel braucht historische Rangbasis; am NB nur 14-Tage-Betriebskopie | **weg** (Rückspiel und live) |
| Wal-Zustand | Daten gibt es (`wale_s2.db` 168 Symbole bis 2026-08, `wale_voll.db` BTC/ETH), aber am NB **kein Live-Job**, s2 endet 08/2026, 168 von 551 Assets, G16 trägt nicht | **weg** |
| Bestand und Ergebnis zum Schlusskurs | keine historische Bestandsreihe; für einen neuen Einstieg ohnehin „kein Bestand“ | **weg** |

⚠️ Was im Rückspiel fehlt, fehlt auch **live** (Ü8).

### S3-3 Block 5 (Befund-Karte A3) wäre ein Vorgriff (Vorschlag)

Nicht gebaut (E-171), und ihr heutiger Inhalt („REGEL0 nicht robust“ E-139 vom 25.10., „S1 trägt nicht“ vom 07.11.) war an fast allen
Einstiegstagen noch unbekannt. → **Block 5 weg**, im Rückspiel **und live**, bis eine eigene Messung „mit/ohne A3“ (Ü6) gelaufen ist.

### S3-4 Block 3 und 4 (Vorschlag)

- **Schwere-Texte raus.** `ereignisse.zeilen()` schreibt „Schwere: …“ in jede Zeile — gemessene Wirkungen samt Urteil (C2-b
  „SCHADET“, C2-a/-c, E-1), gemessen **über den Rückspielzeitraum**. Für S7 wurden sie deshalb entfernt (`sichten_gutachten.py`), und die
  S7-Anlage verlangt ausdrücklich, dass sie fürs finale LLM *„vor 2025-12-01 gemessen sein“* müssen (P-1). → Block 3 **ohne** Schwere,
  live gleich. Das Prüfpaket B6 verlangt: kein „Schwere:“ in Block 3.
- **Kursreaktion als Fakt** (`agent/kursreaktion.py`) bleibt, wie für das finale LLM vorgesehen, aufgerufen mit dem Informationszeitpunkt (S3-5).
- **Asset-Zuordnung:** `binance_assets` **und** `upbit_assets` übersehen 1-Zeichen-Kürzel und BTC/ETH (M1 §6.2; Regex, Kurswährung).
  Ereignisse mit leerer Asset-Liste fielen einer anderen Sicht zu oder heraus. Die Ergänzung im Stufe-3-Modul liest deshalb die
  **Titel neu**. `agent/ereignisse.py` bleibt unverändert (eingefrorene S7-Eingabe). ⚠️ Folge: Block 3 kann Ereignisse zu BTC/ETH
  zeigen, die S7 in Block 4 nie beurteilt hat.
- **Block 4 Sicht-Ergebnisse:** S1, S2, S3, S4, S8 und **S7 Form d** (Hauptarm), nur das Schema (Ü4), `wdh` 0. ⚠️ Wählt die S7-Messung
  nach Stufe 1 §4.1 den Arm e, sieht der Betrieb eine andere Eingabe als gemessen (Ü8) — dann muss Stufe 3 neu gemessen werden.
- **Block 1:** *„REGEL0-Einstieg X, Hebel Ns, 24 h, setzt auf einen Anstieg nach dem Ersteintritt des Kurvenmodells“* (P1).

### S3-5 Ein Informationszeitpunkt je Einstieg (Vorschlag)

Die Zielgröße beginnt beim Schluss der Einstiegsstunde. Live wird der Aufruf beim **Signal** gemacht (Schluss der Signalstunde = Beginn
der Einstiegsstunde). Darum gilt für **alle** Blöcke: **Informationszeitpunkt t = Signalstunde + 1 h** (= Spalte `stunde`).
- Kurse, ATR, Hebel-Abstand: nur Kerzen, die bis t geschlossen sind (nicht Hoch/Tief der Einstiegsstunde).
- Ereignisse: bekannt_ab ≤ t; Kursreaktion bis t.
- **Gutachten:** das von Tag T, wenn t ≥ T 02:00 UTC (live braucht der Tageslauf der Sichten nach 00:00 rund 7 Aufrufe), sonst das von
  T−1. Dieselbe Regel live. (97 der 2.435 Einstiege liegen um 00:00, 284 bis 02:00.)

### S3-6 Kontingent, Treue, Datenlage

- 3a 321 Aufrufe (< 1 Kontingenttag), 3b 2.058 (≈ 4). Stufe 3 braucht S2/S4 als Eingabe (≈ 10.11. fertig); der Bau läuft parallel.
- Prüfer v2 zählt Angaben gegen die Eingabe, verwirft nie. „Unlesbar“: Bedenken nicht ∈ {0,1,2}, keine zwei Gründe, kein „umstimmen“.
  Unlesbare gehen nicht in p_vor ein; > 5 % unlesbar → technisch Rot.
- ⚠️ **Datenlage Nachrichten:** das Archiv bricht ab Juni 2026 ein (Mai 2.403, Juni 413, Juli 786 Meldungen; einzelne Quellen liefern
  fast nichts mehr), die A1-Ereignisse fallen von ≈ 3.500 auf 400–1.300 je Monat. Block 3, S1 und S7 sind über den Zeitraum **ungleich
  dicht** gefüttert. Live gibt es noch keinen Nachrichten-Job am NB (Ü8, G8b).

---

## 3. Bauplan

| # | Schritt |
|---|---|
| B1 | Modul `agent/finales_llm.py`: Eingabe je Einstieg aus Block 1–4 (§2), Prompt, Aufruf, Ablage `data/_g7/finales_llm.db` (nie Produktions-DB), Anfragebuch wie Stufe 1, Modellkennung je Aufruf |
| B2 | `--eingabe <symbol> <stunde>` ohne Netz; Prüfung: kein Element mit Zeit > t; kein „Schwere:“ |
| B3 | Probe 3–5 Einstiege außerhalb der Vorauswahl, nur Form und Treue, kein Kurs; danach **Prompt-SHA einfrieren** |
| B4 | Lauf 3a auf `g7_stufe3_vorauswahl_d3.csv`, dann `--vorpruefung`: zeigt nur Messbarkeit, p_b, p_a und WEITER/ENDE |
| B5 | bei WEITER: Lauf 3b, dann Messung mit `g7_stufe3_anlage.messe` auf a und b; die 321 Urteile aus 3a werden unverändert wiederverwendet; keine Zwischenblicke in 3b |
| B6 | Paket in `pruefe_pakete.py`: Ablage ≠ Produktions-DB, Vorgriff 0, kein „Schwere:“, Vorauswahl = festgeschriebene Datei (Prüfsumme, nicht neu gezogen) |

---

## 4. Die Vorprüfung (E-174) — Entwurf und Hürde aus zwei Selbsttests

### 4.1 Festlegung

| | |
|---|---|
| **Vorauswahl** | Entwurf **D3**: je Tag **1** Einstieg, und zwar aus **a**, wenn der Tag gemailte Einstiege hat, sonst aus der Stichprobe → `Rechenkern_02_10/g7_stufe3_vorauswahl_d3.csv` (321 Einstiege, 321 Tage, davon 204 aus a; SHA-256 `314c47c3d8e06077…`; Teilmenge von `g7_stufe3_menge_b.csv` `62a0641aeb643b46…`; reproduzierbar) |
| **Statistik** | wie die Messung: Arm HANDEL (Mittel `ertrag_s` Bedenken ≥ 1 − Bedenken 0), Tagesbahn, einseitig unten — **p_b** über alle 321, **p_a** über den a-Teil (204) |
| **Messbarkeit** | Anteil Bedenken ≥ 1 außerhalb 5–95 % → **ENDE „nicht messbar“** (KEIN BEFUND, Scheideweg Fall 5) |
| **Hürde** | **WEITER, wenn p_b ≤ 0,40 ODER p_a ≤ 0,40.** Ist ein p nicht rechenbar, zählt das andere |
| **Was 3a nicht darf** | nie „trägt“ melden; danach nichts an Prompt, Eingabe, Vorauswahl oder Hürde ändern |
| **3b und Messung** | Rest 2.058; ausgewertet auf **allen** 2.379 wie Messplan §11.5 (Band P5, a und b getrennt, beide Richtungen) |

### 4.2 Die zwei Selbsttests

**Fassung 1** (`g7_stufe3_vorpruefung_selbsttest.py`, `b05f9c209a0bd29e`): 1 je Tag aus b, Wirkung nur gleichmäßig über b, Rate 30 %.
Ergab k = 1, c = 0,40. **Die Gegenprüfung (§6) fand die Lücke:** wirkt das Urteil nur auf den gemailten Einstiegen (dem Betriebsfall),
lief diese Vorprüfung bei 0,3 σ nur zu 62–70 % weiter; bei Raten von 10 % / 85 % fiel sie unter 90 %.

**Fassung 2** (`g7_stufe3_vorpruefung_selbsttest2.py`, `e0d6e4ed6a3cb07a` → `…selbsttest2.txt`) — Auswahlregel wieder **vorab** im Kopf:
vier Entwürfe, fünf Erzeuger mit Wirkung (gleichmäßig 30 %, Tagesstimmung, **nur a**, Rate 10 %, Rate 85 %). Bestehen heißt: bei 0,3 σ
in allen fünf und bei 0,2 σ in den gleichmäßigen ≥ 90 % weiter; dann die wenigsten Aufrufe, dann das kleinste c. **Gewählt: D3, c = 0,40.**

| WEITER bei 0,3 σ (≈ 1,4 %) | D1 (Fassung 1) | **D3 (gewählt)** | D4 (524 Aufrufe) |
|---|---|---|---|
| gleichmäßig 30 % / Tagesstimmung | 98 / 98 % | **99 / 99 %** | 100 / 100 % |
| **nur a (Betriebsfall)** | 68 % | **97 %** | 97 % |
| Rate 10 % / 85 % | 91 / 96 % | **94 / 97 %** | 96 / 99 % |
| bei 0,2 σ (≈ 0,94 %) gleichmäßig / Tagesstimmung | 92 / 92 % | **93 / 94 %** | 97 / 95 % |
| **ohne Wirkung weiter** | 38–45 % | **49–51 %** | 50–54 % |

| Fehlalarm (1.000 Ziehungen) | ohne Vorprüfung | mit D3 |
|---|---|---|
| Tagesstimmung Lauf 1 T / gleichmäßig 30 % | 2,9 / 3,2 % | 2,2 / 3,0 % — sinkt |

⚠️ Die Fehlalarm-Werte „ohne Vorprüfung“ weichen zwischen den Fassungen ab (4,8 gegen 2,9 % bei Tagesstimmung Lauf 1 T, andere
Startwerte, je 1.000 Ziehungen; ≈ 2,2 Standardfehler). Beide liegen unter dem Soll 5 %. Die Messanlage selbst ist am 02.11. geprüft (§11.2).

**Was es kostet und bringt:**
- **Ohne Wirkung** endet Stufe 3 in rund **der Hälfte** der Fälle nach 3a → ≈ 4 Kontingenttage gespart.
- **Mit Wirkung ab ≈ 0,9–1,4 %** geht fast nichts verloren (93–99 % weiter).
- **Kleine Wirkungen (≈ 0,5 %)** verlieren mehr; die findet aber auch die volle Messung nur zu 37–58 % (Fassung 1).
- Auf a allein (Betrieb) ist die volle Messung schwach: bei 0,3 σ gleichmäßig nur 89 % (b: 100 %), Tagesstimmung 68 %. Das ist die
  Auflösung von a (Messplan §11.3), nicht die Folge der Vorprüfung.

### 4.3 Lesart bei ENDE — vorab

| p in 3a | gilt als | Scheideweg |
|---|---|---|
| p_b und p_a > 0,40, keiner ≥ 0,95 | **nicht trennbar** (Auflösung von 3a: ab ≈ 0,9 % sicher, darunter nicht) | Fall 4 |
| p_b oder p_a ≥ 0,95 | **verkehrt, Hinweis aus 3a** (Bedenken liefen *besser*, wie N5) → kein Signal, Ursachenanalyse | Fall 4 |
| Messbarkeit Rot | **KEIN BEFUND** | Fall 5 |

Bei ENDE gibt es keine Ausweisung auf a und b nach §11.5 — nur p_b und p_a aus 3a.

### 4.4 Zeitplan

| | |
|---|---|
| Bau B1–B3, Probe, Prompt einfrieren | parallel zu S7/S7w/S2/S4, bis ≈ 10.11. |
| 3a (321 Aufrufe) | ≈ 11.11. |
| WEITER/ENDE | ≈ 12.11. |
| bei WEITER: 3b (2.058) + Messung | ≈ 4 Kontingenttage → ≈ 16.11. |

---

## 5. Was festgeschrieben wird, bevor das erste Urteil entsteht

Prompt-SHA (nach B3), Vorauswahl `g7_stufe3_vorauswahl_d3.csv`, Hürde 0,40 mit ODER-Regel, Messbarkeitsgrenze, Lesart §4.3, Messung wie
Messplan §11.5. Ändert sich danach Prompt oder Eingabe, ist es eine **neue** Messung (R-R11).

---

## 6. Gegenprüfung (08.11.2026, unabhängig, nur lesend, mit eigenen Simulationen)

Jeder Muss-Punkt an der Quelle nachgeprüft (`ereignisse.zeilen` Z. 617–630, `sichten_gutachten.py` Z. 226–231, S7-Anlage P-1,
`data/_wale/`), alle bestätigt und eingearbeitet:

| Punkt | Befund | geändert |
|---|---|---|
| M1 | Block 3 trüge die Schwere-Texte — gemessen über den Rückspielzeitraum, ein Vorgriff | S3-4: Schwere raus, B2/B6 prüfen |
| M2 | Vorprüfung verlor den Betriebsfall (Wirkung nur auf a): 62–70 % weiter bei 0,3 σ | Selbsttest Fassung 2, Entwurf D3 mit ODER-Regel: 97 % |
| M3 | Wal-Begründung falsch (Daten gibt es) | S3-2 neu begründet |
| M4 | ENDE = „Fall 4/5“ widersprach „nicht trennbar“ | §4.3: nicht trennbar/verkehrt → Fall 4, nur Messbarkeit Rot → Fall 5 |
| Soll | Richtung bei ENDE; ein Informationszeitpunkt; Sonderfälle und Raten; Verwässerung; S7 d/e; Upbit-Lücke; A4 in alten Plänen, §0 als Vorschläge | §4.3, S3-5, §4.1, S3-2, S3-4, S3-1, §0 |
| Hinweise | Abbruchregel und Simulation korrekt; Vorauswahl bitgleich; Kostenvergleich k = 2 einseitig formuliert; Nachrichten-Einbruch ab Juni; `vh`/Stufe ohne Vorgriff; Kurs-Lage < 200 T | eingearbeitet (S3-6, S3-2) |

---

## 7. Bau (08.11.2026, nach E-175)

| | |
|---|---|
| Modul | `agent/finales_llm.py` (B1, B2, B4, B5): Eingabe Block 1–4, Prompt, Leser, Ablage `data/_g7/finales_llm.db` (Probe: `…_probe.db`), Lauf 3a/3b, `--vorpruefung`, `--vorgriff`. Aufruf und Anfragebuch aus `sichten_gutachten.rufe` (ein Kontingentbuch) |
| **Beim Bau gefunden** | Die Mengendatei trägt **v̂ und Hebelstufe der Einstiegsstunde** — eine Stunde nach t. Live geht die Mail beim Signal mit der **vorläufigen** Stufe (ATR der Signalstunde, `regel0_mail.py`). → v̂ wird nicht gezeigt; die Stufe ist die vorläufige aus `Rechenkern_02_10/g7_stufe3_stufe_vorlaeufig.py` (dieselbe Rechnung wie `g7_regel0_betrieb.teil_d`, eine Stunde früher). **Gegenprobe:** die endgültige Stufe nachgerechnet = Mengendatei **2.435 von 2.435**; vorläufig weicht in **65 (2,7 %)** ab |
| **Prüfen** | `--vorgriff` über alle 2.379 Eingaben: **0 Vorgriffe**. Länge Median 3.362 Zeichen ohne S2/S4/S7 (die laufen noch), mit allen Sichten ≈ 5.500 |
| **Gegenprüfen (zweiter Weg)** | Zeitangaben direkt aus dem fertigen Text gelesen (400 Eingaben, 606 Zeitangaben): **keine nach t**; Gutachten-Tag regelgerecht; überall die vorläufige Stufe; kein Schwere-Text |
| Prüfpaket | `pruefe_pakete.py --paket FinalesLLM` **9/9**: Ablage, Prüfsummen, Gutachten-Tag, **Vorgriff am Seiteneffekt** (Kurse ab t und Meldungen nach t abgeschnitten → Eingabe byte-gleich), Leser, Lauf mit Attrappe (wiederaufnehmbar, kein Anfragebuch-Eintrag), Vorprüfung (konstant → nicht messbar, Wirkung → WEITER, umgekehrt → verkehrt; p_b gleich dem Selbsttest Fassung 2 auf zwölf Stellen) |
| ⚠️ Datenlage | **88 % der Einstiege (2.089 von 2.379) haben keine Meldung zum Asset** in den 7 Tagen davor — Block 3 ist meist leer. Das finale LLM urteilt also überwiegend aus Asset-Lage und Sichten |
| B3 Probe | 5 Einstiege an den Probe-2-Tagen (dort liegen alle Sichten in den eingefrorenen Fassungen), nicht aus der Vorauswahl; läuft, sobald das Kontingent frei ist |

### 7.1 Zweite Gegenprüfung (Modul, 08.11.2026, unabhängig, nur lesend) — eingearbeitet

Alle Punkte an der Quelle nachgeprüft. Die Probe lief zu dem Zeitpunkt schon und wurde **angehalten**. Eine Anfrage war noch
durchgegangen; ihr Urteil (alter Prompt `10c72a10a680`) liegt unbenutzt in `data/_g7/finales_llm_probe_verworfen_10c72a10.db`.

| Punkt | Befund | geändert |
|---|---|---|
| **M2 Wette** | Block 1 beschrieb einen **Trendhandel** („setzt darauf, dass der Kurs steigt“), der Betrieb sagt *„Kauf auf eine Gegenbewegung nach einem Rückgang … ob die Gegenbewegung in diesen 24 Stunden trägt“* (`regel0_llm.plan_text`, P1 03.10.: ohne diesen Satz sagten die Rollen bei 9 von 10 „dagegen“). Dazu waren die Stufen asymmetrisch („0 nur, wenn nichts dagegen spricht“) → Gefahr „nicht messbar“ | Wortlaut des Betriebs übernommen; Stufen als **Abwägung** („überwiegt“); Hinweis: ein vorangegangener Rückgang ist für diese Wette kein Gegengrund für sich |
| **M1 Eingabe nicht eingefroren** | nur der Prompt-SHA band die Urteile; geänderte Daten/Code zwischen 3a und 3b wären still gemischt worden | `eingaben_geaendert()` vor Vorprüfung und vor 3b (Abbruch, R-R11); Prüfsummen auch für vorläufige Stufe und Zielgröße |
| S1 Kursreaktion | rechnete ab der ältesten Meldung des Typs, gezeigt wurde die neueste | ab der **gezeigten** Meldung, so beschriftet |
| S2 Vorgriff-Prüfung | die Prüfungen im Modul prüften nur ihren eigenen Filter (Tautologie) | Paket: Seiteneffekt über **alle 2.379** Einstiege, Gutachten-Quelle verweigert alles nach der 02:00-Regel → byte-gleich |
| S3 Schwere | Prüfung über den ganzen Text, hätte an „Schwere“ in einem Gutachtensatz abgebrochen | nur Block 3, Etikett und Register-Texte (`EV.SCHWERE`) |
| S4 Paket | fehlten: 3b ohne WEITER, Anfragebuch, Zweige der Vorprüfung, zweiter Weg für p | ergänzt: 3b verweigert, keine Zeile des Paket-Prozesses im Anfragebuch, alle Zweige (Grenze 0,40, nur p_a, NaN, Rot), p gegen eine **naive Schleife** gleich |
| S5 mehrfache Vorprüfung | jede neue Vorprüfung hätte die alte ersetzt | genau **eine** je Prompt-SHA; 3b stützt sich auf die erste |
| S8 Modellkennung | nur die Konstante abgelegt | eigene Aufruf-Funktion legt die Kennung **aus der Antwort** ab |
| Leser | 1,7 und `true` wurden still zu 1 | nur ganze Zahlen; gleicher Beleg zweimal wird gezählt |
| Block 4 | Fließtext „Aussage“ stand mit drin (Fütterung §4: nur das Schema) | entfernt |
| Ablage | Schutz nur über drei Dateinamen | schreibt **nur** in `finales_llm*.db` |
| **Nachweis Stufe** | die Gegenprobe 2.435/2.435 reproduzierte nur `teil_d` | **zweiter Weg gegen den Betrieb:** an allen **199** Einstiegen, die auch das NB im Oktober hatte (NB-Kopie 07.11.), stimmen vorläufige **und** endgültige Stufe exakt mit der NB-Ablage überein |

**Bleibt offen, benannt statt behoben:**
- **Ü8 live (G8b):** Sichten-Tageslauf am NB bis 02:00 UTC mit denselben Prompt-SHAs und demselben Modell, A1 am NB samt Weg b,
  Zustände S1–S4 am NB, die vorläufige Stufe beim Aufruf ausdrücklich übergeben (die Mail nimmt `COALESCE(stufe, stufe_vorlaeufig)`),
  dieselbe Eingabe-Funktion importieren. **Heute gibt es den Weg nur im Rückspiel.**
- **Treue:** gezählt wird nur, ob die Kennung des Belegs existiert und ob beide Gründe dieselbe nennen — nicht, ob der Inhalt zur Stelle passt.
- **Quartalsmodell an der Quartalsgrenze:** 6 Einstiege um 23:00 am Quartalsende nehmen das Modell des alten Quartals (live das neue); alle 6 ergeben dieselbe Stufe.
- **Asset-Zuordnung über Klammern:** bringt rund 50 Meldungen dazu; eine Fehlzuordnung gefunden („Seagate (STX)“ → Stacks), bei BTC/ETH nur Wartungsmeldungen.
- **S8** bezieht „Termin in x T“ auf T 00:00; abends kann der Termin schon vorbei sein — veraltet, kein Vorgriff.
- **Die Messung B5** (`messe` auf a und b) ist noch nicht im Modul; sie wird **vor 3b** gebaut und festgeschrieben.
- 3a teilt sich Schlüssel und Kontingent mit dem Stufe-1-Lauf (ein Anfragebuch).

Prüfpaket `FinalesLLM`: **13/13**.

### 7.2 Probe 08.11. — Prompt eingefroren

| | Ergebnis |
|---|---|
| Form | **5/5 lesbar** im ersten Versuch, Belege ohne Stelle 0, Modellkennung = angefragtes Modell |
| Treue (gelesen) | jeder Grund steht in der zitierten Sicht; ein Grund ordnet eine Aussage aus S7 der S1 zu |
| Treue (gezählt, zweiter Weg) | 64–90 % der Inhaltswörter je Grund in der zitierten Sichtzeile; es fehlen nur Wertungswörter |
| Verteilung (ohne Kurs) | bedenken **1, 1, 1, 1, 2** — kein 0; Gründe nur aus Marktsichten, gleicher Tag → fast gleiche Gründe |

⚠️ **Risiko:** ein Anteil „bedenken ≥ 1“ über 95 % ergibt in der Vorprüfung **„nicht messbar“** (Fall 5). Aus drei Probetagen nicht schätzbar;
die Vorprüfung fängt es ab, Kosten ein Tag Kontingent. Der Prompt wird deshalb **nicht** nachgestellt — eine Änderung nach Ansicht der
Ausgaben wäre eine neue Fassung ohne Messgrund.

**Eingefroren:** `PROMPT_EINGEFROREN = "a7d1c5048eb0"`, `lauf()` verweigert 3a/3b mit anderem Prompt. Prüfpaket `FinalesLLM`: **14/14**.

## 8. 3a und Vorprüfung — 11.11.2026

| | Ergebnis |
|---|---|
| Lauf | 10.11. 11:06 – 11.11. 09:47 MEZ (Desktop-Neustart 11.11. bei 55/321, wiederaufgenommen ohne geänderte Eingabe) |
| Form | **321/321 lesbar**, je 1 Versuch, Belege ohne Stelle 0, Modellkennung 321 × gemini-3.5-flash-lite, ein Prompt-SHA `a7d1c5048eb0` |
| Menge | = Vorauswahl D3 (Prüfsumme gleich), 204 a + 117 b, 321 Tage |
| Eingabe | `eingaben_geaendert` 0; zweiter Weg: Text-SHA 321/321 gleich, Signalzeitpunkt = Stunde 321/321 |
| Anfragebuch | 321 × 200, 11 × 503 (wiederholt), 88 × 429-Tag, nur Schlüssel 2 |
| **Vorprüfung** (genau eine) | Anteil Bedenken ≥ 1 **78,8 %** (a: 84,8 %) · **p_b 0,325** · **p_a 0,463** → **WEITER** (p_b ≤ 0,40) |
| Gegenprüfung | p_b / p_a mit eigener Schleife über 320 Tagesverschiebungen, ohne Anlage und Modul: **identisch**; Urteile durch die Vorprüfung unverändert |

⚠️ **Lesart:** WEITER heißt nur, dass 3b läuft — ohne Wirkung käme die Vorprüfung in rund der Hälfte der Fälle hierhin (§4.2). Ein
Befund entsteht erst auf allen 2.379 (Messplan §11.5). An Prompt, Eingabe, Vorauswahl und Hürde wird nichts geändert (§4.1).

⚠️ **Vor 3b:** die Messung B5 (`messe` auf a und b) ist noch nicht im Modul; sie wird vor dem ersten Blick auf 3b gebaut und festgeschrieben (§7).

## 9. Messung B5 — gebaut und festgeschrieben vor 3b (11.11.2026, Nutzer: *„Ja, erst B5“*)

| | |
|---|---|
| Ort | `agent/finales_llm.py`: `_auswerte` (je Menge) und `messung` (Sperren, Ablage Tabelle `messung`), Aufruf `--messung` |
| festgeschrieben | Quelltext-SHA `MESSUNG_EINGEFROREN = "3159f80d90e7"`; Messanlage `g7_stufe3_anlage.py` per Prüfsumme `f60cf967d8c095ea` (unverändert seit 02.11.) |
| Mengen | **b** = alle lesbaren der 2.379, **a** = deren gemailter Teil — getrennt ausgewiesen (Messplan §11.5), keine Korrektur für zwei Tests: es sind zwei verschiedene Fragen (Betrieb / Trennfähigkeit), wie vorab festgelegt |
| entscheidet | Arm HANDEL über die Tagesbahn (`messe`): **TRÄGT** nur unter P5 (Bedenken → schlechter) |
| mit ausgewiesen | oberes Ende: über P95 → **VERKEHRT** (kein Signal, Ursachenanalyse); p unten und oben; Arm TAG; roher 24-h-Unterschied |
| KEIN BEFUND | < 20 Fünfzehn-Tage-Blöcke oder Anteil Bedenken ≥ 1 außerhalb 5–95 % |
| technisch Rot | > 5 % der 2.379 unlesbar (sonst gemessen auf den lesbaren) |
| Sperren | genau EINE Messung je Prompt-SHA · erst bei 2.379/2.379 (keine Zwischenblicke in 3b) · nur nach WEITER · Eingaben 3a + 3b unverändert (R-R11) · Quelltext und Anlage per Prüfsumme |

**Geprüft** auf erfundenen Urteilen (Wegwerf-Ablagen): Wirkung → TRÄGT, umgekehrt → VERKEHRT, Zufall → TRÄGT NICHT, konstant → KEIN
BEFUND, 2 Monate → KEIN BEFUND (5 Blöcke), 130 unlesbar → technisch Rot; jede Sperre greift. Paket `FinalesLLM` 15/15.
**Gegengeprüft** in reinem Python ohne Modul und Anlage: 12 Größen je Menge **identisch**.

**3b gestartet** 11.11. 18:10 MEZ (PID 22796), 2.058 Aufrufe, ≈ 4–5 Kontingenttage.
