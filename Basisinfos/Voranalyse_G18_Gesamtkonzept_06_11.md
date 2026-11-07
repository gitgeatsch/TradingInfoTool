# Voranalyse G18 — Gesamtkonzept Strang 1: Krypto · REGEL0 · Hebel (06.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 06.11.2026, E-169):** *„der wichtigste ungeklärte Punkt ist das Gesamtkonzept, was die Signale also deterministisch und über LLM ein besseres Ergebnis liefern soll“* · *„Krypto Regel0 Hebel alle Assets sofort und im Detail planen inkl. Dashboard“*.

**Kernaussage des Nutzers (E-169):** REGEL0 trägt — dafür ist eine **Erfolgsmessung** nötig —, aber *„nur für genau einen spezifischen Fall deterministisch, ohne Markt, ohne Politik … das System ist zu starr, eine Regel … dann können in einem Fall Regel0, in einem anderen Regel1 usw. spezifische Aktionen, also Signale, auslösen; das sollte für Einstieg, Positionsführung und Ausstieg sinnvoll sein.“*

**Status:** Voranalyse, nur gelesen und aus belegten Zahlen gerechnet. **Nichts gebaut, Betrieb unberührt.** Gliederung abgestimmt (Nutzer 06.11.: *„ja 1“*). Fassung 2 nach der Gegenprüfung (§10: drei schwere Befunde, alle eingearbeitet).

---

## 0. Das Ergebnis in sechs Sätzen

1. **„REGEL0 trägt“ ist nicht belegt — belegt ist „brutto positiv, nicht robust“** (§1.2). Und die Kernaussage „ein Fall **ohne Markt**“ stimmt nach den Messungen nicht: das Plus von REGEL0 liegt zu **99 % an Tagen mit mehr als 20 Signalen**, also an **marktweiten** Tagen; an ruhigen Tagen verliert die Regel (E-138, Bilanz B.7).
2. **Eine Erfolgsmessung im Betrieb kann das Niveau von REGEL0 praktisch nicht entscheiden:** der kleinste erkennbare Effekt nach 365 Signaltagen (≈ zwei Kalenderjahre) ist 1,01 Pp, der Effekt liegt bei ≈ 0,55 %. Sie kann beschreiben, nicht urteilen — und rückwärts kann sie E-139 nicht umstoßen (R-R11) (§1.3).
3. **Mit den vorhandenen Daten sind weitere Regeln schon gesucht worden — ohne Ergebnis:** die Suche nach einem Einstiegsvorsprung mit freien Daten ist **abgeschlossen** (E-155/E-156); keines der neun Richtungsmerkmale trägt `E[R]` (2.604); *„die Lage trägt einen Hebel“* ist widerlegt, 0 von 60 (H2). **Neue Regeln brauchen neue Information** (E-156).
4. **Diese neue Information entsteht gerade:** Sicht-Gutachten (G7), Ereignisse je Asset (A1, S7/S7w), Kursreaktion als Fakt. Sie liefern genau die *„Sichten bzw. Schichten“*, die der Nutzer vermisst.
5. **Vorschlag:** *Mehrere Regeln, gewählt nach neuer Information — nach dem **Tageszustand des Markts** und nach **Ereignissen je Asset**; die langsame Marktlage (Regime, Trend, Makro) bleibt Information; die eigene ATR des Assets schützt.* Je Phase Einstieg · Führung · Ausstieg (§4).
6. **Dashboard (G19)** kann zu einem großen Teil ohne LLM vorgezogen werden: B1, B2, B4, B5, B6; die LLM-Rolle B3 folgt getrennt (§6).

---

## 1. REGEL0 und Hebel heute

### 1.1 Was REGEL0 ist

| Punkt | Fakt | Quelle |
|---|---|---|
| Auslöser | rsi-Kurvenmodell, monatlich trainiert; Signal = **Ersteintritt** v̂ ≥ +0,035 nach 48 h Ruhe darunter; Einstieg 1 h später; nicht in den ersten 24 h eines Monats; eigenes Normal ab 240 h; stündlich für alle Assets | `REGEL0_Hebel_Entwurf_30_09.md` §2; E-36 |
| Fassung | REGEL0.1: Schrumpfung kausal aus dem Vormonat (τ² in 31 von 33 Monaten null) | Entwurf §13; 2.708 |
| Hebelstufe | nach der **eigenen ATR des Assets** beim Einstieg: 2x/3x/5x, die höchste mit Liquidationswahrscheinlichkeit ≤ 2 %; die ATR allein sagt die Liquidationsgefahr voraus (5x kalibriert, 3x geordnet) | Entwurf §3; 2.681 |
| Haltedauer | 24 h ohne Ziel und Stop (H24 war das **Messfenster**, E-6; zur Betriebsregel wurde es über §23.68) | Entwurf §4; E-6 |
| Größe | 1.500 € Positionswert, Einsatz 300–800 € je Stufe; Größe nach ATR nicht trennbar → fest | `regel0_betrieb.yaml`; E-44; E-158-v1 |
| Menge | trainiert auf 116 (*bestand*), bewertet 487–621 Werte; gemailt nur bei eingeschaltetem Hebel-Schalter; Kern BTC/ETH/SOL immer zugelassen | E-45, E-146; G7 §9 |
| Betrieb | NB seit 03.10., Mails seit Testwoche 10.10. (E-94), Mail mit Vorbehalt „NICHT robust“ (E-159) | `agent/regel0_*.py` |

### 1.2 Was belegt ist — und was nicht

| Aussage | Stand | Quelle |
|---|---|---|
| Festschreibung E-36 | lief gegen 0 statt gegen den Versatz → nur **2 von 4** Mengen | E-36 Nachtrag; E-141 |
| brutto | ohne Kosten 4/4 Mengen positiv (Rohvorteil +0,12 bis +0,33 % je Handel) | 2.690, 2.703 |
| nach Hebelkosten *(nachgelagert, Regel 2)* | verliert 2025–26 in 4/4 Mengen (Kosten ≈ 0,48 %); mit Historie ab 2019 je Handel nach Kosten −0,34 % statt +0,15 %, nur 37,5 % gleiche Einstiege; 2020-07 bis 2022-12 **kein** Einstieg | 2.690; E-136 |
| Robustheit | **0/6** — allein aus der Bedingung **je Tag** (je Handel wären es 6/6); das Plus kommt aus der Reife-Regel; je Tag überall negativ (Referenz −0,24 %); Geltungsbereich: Menge *bestand* | E-138/E-139; Nachtrag E-141 |
| wo das Plus liegt | **≈ 99 % an Tagen mit mehr als 20 Signalen**; an ruhigen Tagen −2,0 % bzw. −0,5 % je Handel; das Plus der Referenz (+0,153 %) war nie von null zu trennen | E-138; Bilanz B.7 *„Plus nur an marktweiten Tagen“* |
| Marktfilter | nicht entscheidbar, selbst ein Orakel besteht die Positivkontrolle nicht | E-133 |
| Gesamtbilanz | *„Kein Einstiegssignal mit belegtem Vorsprung“*; Einstiegsgeber je Asset: keiner belegt | Bilanz B.3, B.7 |
| Betriebsentscheid | REGEL0 als Hebel-Signalgeber „nicht geeignet“, bleibt vorerst unverändert | E-140 |

➤ **Fakt, nicht Bewertung:** REGEL0 findet brutto etwas, aber nicht stabil, und **nicht unabhängig vom Markt** — es greift an Tagen, an denen viele Assets zugleich auslösen. Das stützt die Kernaussage *„eine starre Regel greift nur einen Fall“*, berichtigt aber den Fall: es ist ein **marktweiter Tageszustand**, kein Fall ohne Markt.

### 1.3 Erfolgsmessung im Betrieb

| Punkt | Fakt | Quelle |
|---|---|---|
| Protokoll | `data/regel0_signale.db` am NB, Tabelle `ausgang` (O21 Stufe 1, 17.10.): 24-h-Ertrag je Signal, rollierend 90 T, 99-%-Band, Befund erst ab 10 Tagen | `agent/regel0_messstand.py`; E-120 |
| Auswertungen | Vorprüfung bis 14.10.: 532 Signale an 12 Tagen +0,74 %, 95-%-Tagesband [−1,7; +1,8] = im Band (§23.64); gebauter Messstand: 558 Signale +0,77 %, 99-%-Band [−1,64; +3,18] (§23.65); gemailt 22 an 6 Tagen +3,79 % [−2,89; +10,47] = zu wenige Tage (§23.67) | Schritt7 §23.64–§23.67 |
| danach | K-O21-1 Teilbeleg (732 gemessen, im Band); 01.11. nur gezählt: 1.642 abgeschlossen, gemailt 67 an 17 Tagen — **kein Ergebnis** | Arbeitsstand; G7 §10.2 |
| echte Trades | bis 14.10.: 2 Trades, −162,57 € (ETH −127,41 € nach 149 h statt 24 h) — nicht fortgeschrieben | §23.67, §23.69 |
| Grenze | effektiv ≈ 1 unabhängige Beobachtung **je Tag** (§23.64); kleinster erkennbarer Effekt nach 365 Signaltagen (für die Schalter-Assets **≈ zwei Kalenderjahre**): Niveau 1,01 Pp, anderer Einstieg 0,51 Pp, anderer Ausstieg 0,93 Pp; der Effekt selbst ≈ 0,55 % | Messstand-Kopf; §23.70 |
| rückwärts | Dez. 2025 – Aug. 2026 liegen im Bestätigungszeitraum 2025-01 bis 2026-08 (2.690); **neu sind nur Sep./Okt. 2026**; eine Rückwärtsmessung kann E-139 nach R-R11 nicht umstoßen | 2.690; G7 §10.3 |
| **fehlt** | ein vorab festgelegtes **Urteilskriterium**, eine fortgeschriebene Auswertung, die Trades in EUR | – |

➤ **Die Erfolgsmessung kann beschreiben, nicht entscheiden.** Für das *Niveau* von REGEL0 bleibt E-139/E-140 die gültige Antwort; vorwärts wird ein Unterschied von ≈ 0,5 % auch nach zwei Jahren nicht sicher. Entscheidbar sind vorwärts nur **Unterschiede zwischen Regeln** ab 0,5–0,9 Pp (Herausforderer, §23.70) — das ist der Weg für Regel1, Regel2 …

### 1.4 Führung und Ausstieg heute

| Punkt | Fakt | Quelle |
|---|---|---|
| H15 | alle 15 min auf echten Positionen; Warnung bei Abstand zur Liquidation 15/10/5 %; kennt den Stop an der Börse **nicht** | E-88, E-92; `agent/hebelfuehrung.py` |
| 24 h / 72 h | Erinnerung als Fakt, kein Gate | E-123 |
| gemessen | 2025–26 kostet jeder Tag über 24 h netto 0,3–0,4 %, Liquidationsnähe in 7 T ≈ ×20; Stop −8 % ändert nichts; **2024 umgekehrt** (Regime) | §23.68 |
| nachgezogener Stop (REGEL1 A) | nicht bestätigt (0/4) | 2.702 |
| Bitpanda | Hebel: kein Limit-Kauf, **Verkauf mit TP/SL möglich** (Nutzer 23.10.: *„bei hebel kein Limit kauf aber verkauf mit TP SL“*); in der Doku bisher nur „Hebel ohne Limit-Kauf“ (E-131) | Nutzer 23.10.; E-131 |
| fehlt | ein Ausstiegs- und Stop-Plan je REGEL0-Position; Führung und Ausstieg sind Phase 5 des Fünf-Phasen-Plans, der seit 27.09. auf „Phase 1“ steht | Plan_Hebel Z. 375, 541 |

---

## 2. Was „besser“ heißen kann

| | Was besser wird | Zielgröße | bisher |
|---|---|---|---|
| **a** | **Auslöser**: weitere Regeln neben REGEL0 | Ertrag je Einstieg gegen die Drift, je Tag | mit vorhandenen Daten abgeschlossen (E-155/E-156, 2.604, H2); REGEL1 A/B/L waren **keine** neuen Auslöser (A = Ausstieg, B = Form des Kerns, L = Filter; 2.702–2.704); Kern-Short nicht bestanden, aber echte Richtung 4/4 (2.696); O13 Fortsetzung nie gemessen, Gegenbelege §23.68 und E-165-h1b |
| **b** | **Auswahl** unter den Auslösern | Ertrag der zugelassenen gegen die verworfenen Einstiege, je Tag | G7 Stufe 3 (Bedenken 0/1/2) misst genau das |
| **c** | **Handlung**: Hebel, Größe, Haltedauer, Ausstieg | Handlung A gegen B auf demselben Einstieg (gepaart) | H-1b/H-1c tragen nicht; Größe nach ATR nicht trennbar; nachgezogener Stop 0/4 |
| **d** | **Information** für die eigene Entscheidung | Faktentreue | Dashboard G19 |

➤ **Die Kernaussage betrifft a und c.** Für a gilt E-156: nur mit **neuer Information**.

---

## 3. Welche Lage kann eine Regel wählen?

### 3.1 Drei Arten von Lage

| | **langsame Marktlage** (Regime, Trend, Makro) | **schnelle Marktlage** (Tageszustand) | **Asset-Lage** (Merkmale dieses Assets) |
|---|---|---|---|
| Wirkung im Rückblick | groß: Spanne der Jahresdrift 0,0869 gegen Lageordnung 0,0072 (Faktor 12; die Ordenbarkeit steht dort selbst als Hypothese) | REGEL0-Plus an marktweiten Tagen (E-138) | Lage vor scharfen Anstiegen ordenbar, Lift ≈ 1,9 (2.594, eine `markt`-Frage), Assetebene 6,9 / 4,7 (2.648) — als **Ereignis**, nicht als Ertrag |
| vorab verwertbar? | **nicht nachgewiesen**: `btc_trend` 1,09 gegen Zufall 1,04, unentschieden (2.599); Marktfilter selbst als Orakel nicht trennbar (E-133); L2-a Selbsttest nicht bestanden, Auflösung erst bei +3 Pp je 7 T (E-151-l2a, E-153: *„kein weiterer Trendfilter“*); DVOL/Angst/F&G nicht auflösbar (E-160); Makro 0 von 60 (O49) | **offen** — G7 Stufe 2/3 misst es: ein Urteil, das einer Tagesstimmung folgt (G-Tag), wird bei 0,9–1,3 % zu 72–79 % gefunden (G7 §11.3) | **widerlegt für den Ertrag**: keines der neun Richtungsmerkmale trägt `E[R]` (2.604); *„die Lage trägt einen Hebel“* 0 von 60 (H2) |
| Fälle | 72 Wechsel in 12 Jahren (E-151), 22 Strecken in 20 Monaten (E-133) | Tage (321 im Rückspiel) | Einstiege, aber effektiv ≈ 1 Beobachtung je Tag (§23.64) |

Die Befunde widersprechen sich nicht: Ordnung im Rückblick ist keine verwertbare Vorhersage, und Ordnung auf ein Ereignis ist kein Ertrag.

### 3.2 Was daraus für „Regel0 hier, Regel1 dort“ folgt

- **Langsame Marktlage als Regelwahl:** mit unseren Daten nicht nachweisbar (E-133, E-151, 2.599). Längere Historie hebt zwar die Fundquote (E-134), aber die Auflösung bleibt grob (+3 Pp je 7 T, E-151). → **Information**, nie Auslöser, nie Gewicht, kein Deckel (Ausweichregel E-169; Nutzervorgabe 01.10.: *keinen Deckel aus Makro/Marktwandel*).
- **Schnelle Marktlage (Tageszustand) als Regelwahl:** **offene Spur** — die einzige, auf der REGEL0 selbst sein Plus zeigt (E-138). Messbar über G7 (Sichten S1/S3/S8 als Tageszustand, Stufe 3 je Einstieg). Ein Befund aus E-138 selbst (z. B. „REGEL0 nur an Tagen mit > 20 Signalen“) wäre **im Nachhinein gefunden** und darf nur auf Daten **nach** der Entdeckung (ab 25.10.) geprüft werden; die Bilanz führt dieselbe Spur als Kandidat **K-b marktweite Tage** (*„2024–26 ist gesehen“*, Bilanz B.6).
- **Asset-Lage mit den vorhandenen Merkmalen:** für den Ertrag widerlegt (2.604, H2). Neu nur mit **neuer Information je Asset**: Ereignisse (A1: Listing, Delisting, Monitoring, Upbit, Nachrichten), S7/S7w, Kursreaktion als Fakt.
- **Blockzahl (nur zur Einordnung):** H = 24 h → Block 15 T, unter 20 Blöcken kein Befund; im Rückspiel Dez. 2025 – Okt. 2026 gibt es 21–23 Blöcke. Eine **langsame** Lageklasse, die blockweise gleich bleibt, kann darin höchstens einmal 20 Blöcke erreichen; eine **schnell** wechselnde Klasse kommt in fast allen Blöcken vor — dort begrenzen die Tage, nicht die Blöcke.

---

## 4. Vorschlag: das Gesamtkonzept

> **Mehrere Regeln, gewählt nach NEUER Information: nach dem Tageszustand des Markts und nach Ereignissen je Asset. Die langsame Marktlage informiert. Die eigene ATR des Assets schützt.**

| Ebene | Rolle | Messbar? | Beispiel |
|---|---|---|---|
| **Tageszustand wählt** | ob und welche Regel heute gilt: REGEL0 an Tagen eines bestimmten Zustands, eine andere Regel an anderen | ✔ über G7 (Stufe 2 je Sicht, Stufe 3 je Einstieg); E-138-Hypothese nur auf Daten ab 25.10. | „S1: Breite bricht ein → REGEL0 nicht; S3 Risikoappetit hoch, viele gleichzeitige Signale → REGEL0“ |
| **Ereignis je Asset wählt** | eigene Regel je Ereignistyp (A1-Typen, S7/S7w) | ✔ Querschnitt, je Regel eigener Selbsttest und eigene Auflösung | „Upbit-Listing → Regel E1 mit eigener Haltedauer“ · „Delisting-Ankündigung → kein Einstieg“ |
| **Bewertung je Einstieg** | Bedenken 0/1/2 aus Sichten, Ereignissen, Befund-Karte (LLM, vom Code geprüft) | ✔ G7 Stufe 3 | „Bedenken 2: Monitoring-Tag, Funding extrem“ |
| **ATR des Assets schützt** | Hebelstufe 2x/3x/5x aus der eigenen ATR (2.681) — wie heute | ✔ am Risiko (Liquidation) | unverändert |
| **langsame Marktlage informiert** | Dashboard und Mail: Season, Makro, Lagebild, Termine — kein Deckel, kein Gewicht | Faktentreue | Statusseite, Asset-Karte |
| **Führung und Ausstieg je Regel** | jede Regel bringt Haltedauer und Ausstieg mit (TP/SL bei Bitpanda) | ✔ gepaart je Einstieg | REGEL0: 24 h; Ereignisregel: eigener Ausstieg |

**Warum diese Form:**
- Sie setzt die Kernaussage um — mehrere Regeln, je Lage, je Phase — und hält **E-156**: jede neue Regel stützt sich auf Information, die es bei der abgeschlossenen Suche nicht gab.
- Sie nimmt E-138 ernst: REGEL0 ist eine Regel für einen **Tageszustand**, und der Tageszustand ist genau das, was die Sichten neu beschreiben.
- Sie hält die vier Regeln: der Takt löst nicht aus (Regel 1); Kosten bleiben nachgelagert (Regel 2); gewählt wird nach Zustand und Ereignis, nicht nach Name oder Rang (Regel 3); ein Fakt wie „Regime unsicher“ begründet keine Handlung, er steht nur in der Mail (Regel 4).

**Abgrenzung zu E-165** (*„REGEL0 bleibt Auslöser, die Schichten wählen das Wie“*): neu ist, dass die Schichten auch wählen dürfen, **ob und welche** Regel auslöst — nicht nur das Wie. Der Nachtrag zu E-165 (*„Wert nur in Risiko und Fakten“*) ist nicht festgeschrieben; dieses Konzept hält ihn offen: Wert kann aus der **neuen** Information kommen, das misst G7.

**Was es nicht kann:** eine Regel „nur im Bullenmarkt“ (langsame Marktlage). Das bleibt die Entscheidung des Nutzers mit dem Dashboard.

---

## 5. Der Messweg

| Schritt | Was | Grundlage | Bedingung |
|---|---|---|---|
| **M0 Erfolgsmessung REGEL0** | Urteilskriterium vorab; vorwärts 03.10.–heute **beschreibend** (alle, gemailt, Trades in EUR); rückwärts nur Sep./Okt. 2026 als neue Monate | `regel0_messstand`, G7 §10, §23.70 | NB-Kopie von `regel0_signale.db` über den Austauschordner (nur lesen) |
| **M1 Regel-Katalog** | Kandidaten **nur aus neuer Information** (E-156): Tageszustände aus den Sichten, Ereignistypen aus A1/S7, E-138-Hypothese (nur ab 25.10.) — je mit Hypothese, Herkunft, erwarteter Teilmenge | G7 Stufe 1, A1, E-138 | Voranalyse |
| **M2 Selbsttest je Regel** | Auflösung für die Teilmenge (nicht gemessen!), Fehlalarm, Ballung — vor dem ersten Blick | Messstandard | Regelwerk |
| **M3 Messung je Regel** | gegen die Drift, je Tag, zweiter Weg, Geltungsbereich, Epochen getrennt | Messnorm | nach M2 |
| **M4 Bewertung je Einstieg** | G7 Stufe 3 wie festgeschrieben (Menge b) | G7 §11 | nach G7 Stufe 2 |
| **M5 Führung/Ausstieg je Regel** | gepaart auf denselben Einstiegen, TP/SL als Handlung | §23.68, H-1-Anlage | nach M3 |
| **M6 Kette am Desktop** | alles zusammen am Desktop gebaut und nachgewiesen | Gesamtplan §6 *Signale erst nach der ganzen Kette* | dann NB |
| **M7 vorwärts** | Herausforderer gegen REGEL0 im Betrieb (O21 Stufe 2) — entscheidbar ab 0,5–0,9 Pp | §23.70 | nach M6 |

Abbruch- und Erfolgskriterien je Regel vorab im Messplan. Ein negatives Ergebnis führt zur Abstimmung und Lösungssuche.

---

## 6. Dashboard (G19): was ohne LLM vorgezogen werden kann

| # | Bauschritt (Bauplan) | braucht ein G7-Ergebnis? | Code heute | vorziehbar |
|---|---|---|---|---|
| B1 | Befund-Karte in `bestand.py` (30–60 Einträge aus dem Register, je Handlung) | nein | fehlt | ✔ |
| B2 | Fakt-Sammler `agent/asset_lage.py` (Kurs, Bestand, REGEL0, H15, Ankündigungen, Upbit, Verwässerung, Season, Makro, Termin, Wal-Fünftel) | nein | fehlt; Quellen laufen am NB bis auf den Wal-Fluss | ✔ (ohne Wal-Fünftel zuerst) |
| B3 | LLM-Rolle A3/A4 (`asset_lage_llm.py`) | A3/A4 nein, die Erweiterung um Ebene 2/3 ja | fehlt; Prüfer v2 vorhanden | getrennt, später |
| B4 | Job 07:45 und nach jedem Signal | nein | fehlt | ✔ mit B2 |
| B5 | Statusseite „Asset-Lage“ | nein | fehlt (andere Karten vorhanden) | ✔ |
| B6 | Prüfungen, NB-Bündel | nein | K-AL-0/K-AL-1 fehlen in `nb_kontrollen.yaml` | ✔ |

**Zu klären (nicht blockierend):**
- `Voranalyse_G8_NB_Buendel_03_11.md` §1 sagt noch „Bau hängt an G7“ — seit E-169 überholt.
- Die Sicht-Zustände (`agent/zustaende.py`) gibt es am NB erst mit dem Abrufer (G8b); die Asset-Karte zeigt dort anfangs nur, was schon läuft.
- B3 (A3 + A4 in **einem** Aufruf) widerspricht Ü7 (Gutachter und Gegenanwalt verschiedene Modelle); `regel0_llm.yaml` vermerkt noch „3.1 ausgelastet“ (Nachweis K-AL-0 fehlt).
- Prüfer v2 prüft Sicht-Gutachten, nicht Befund-Kennungen und -Zahlen — für A3 zu ergänzen.

---

## 7. Der Weg zum NB

- **Signale** (neue Regeln, Auswahl, Führung): erst wenn **alles** am Desktop gebaut und nachgewiesen ist (M6, Gesamtplan §6).
- **Dashboard und Bewertung**: vorziehbar, Funktionsnachweis am Desktop zuerst, dann ein NB-Bündel (B1, B2, B4, B5, B6).
- **G8a** (S-2, G14, Z-1): Kontrollen K-W3-S2, K-G14-1 offen; der Stand des Pulls ist hier nicht geprüft.

---

## 8. Eckpunkte Spot (G20) und Multiasset (G21) — nur Roadmap

| | Hebel (Strang 1) | Spot (Strang 2) | Multiasset (Strang 3) |
|---|---|---|---|
| Horizont | 24 h bis Tage | **Wochen bis Monate** | je Klasse verschieden |
| Messbarkeit im Rückspiel | ein Zeitraum trägt H ≤ 5 | H = 7/10 nur mit **beiden** Zeiträumen, H = 14 nie (G7-Messplan) → längere Historie nötig | eigene Historien je Klasse |
| Einstieg | Regeln nach neuer Information (§4) | Kaufzeitpunkte schlugen regelmäßiges Kaufen nicht (E-59–E-64); E-156 gilt auch hier; Limit-Kauf bei Bitpanda möglich | offen |
| Führung | H15, Liquidationsabstand, ATR-Stufe | Mitnahme ×3, Abbau-Fünftel (B1/B4 laufen) | offen |
| Kosten (nachgelagert) | Hebelkosten ≈ 0,48 % je Trade | nur Einmalgebühren (Nutzer 23.10.) | je Börse |
| Daten | stündlich, Terminmarkt, Funding, Ereignisse | täglich/wöchentlich, Umlaufmenge, Verwässerung, Listings | Aktien, Rohstoffe, Zinsen — andere Quellen |
| Grundgesamtheit | Binance-Spot TRADING + BREAK | dieselbe, plus Coins außerhalb Binance (P22b) | eigene je Klasse |
| Wann | jetzt | wenn Hebel trägt | wenn Krypto trägt |

---

## 9. Entscheidungsfragen

> ✔ **Entschieden 07.11.2026 (E-170):** Nutzer *„ok - dann 1 1 1 1“* — F-A 1, F-B 1, F-C 1, F-D 1, jeweils die Empfehlung.

**F-A — Erfolgsmessung REGEL0 (M0).**
1. **Kriterium vorab festlegen und beschreibend auswerten:** vorwärts 03.10.–heute (alle Signale, gemailt, Trades in EUR) und rückwärts nur die neuen Monate Sep./Okt. 2026; als laufende Zeile auf Statusseite/Mail fortschreiben. *Folge:* du siehst, wie REGEL0 im Betrieb läuft, ehrlich mit Band; ein Urteil über das Niveau ist damit nicht möglich (≈ 2 Jahre, 1,01 Pp), E-139/E-140 bleiben gültig. Braucht eine NB-Kopie von `regel0_signale.db` im Austauschordner.
2. **E-139/E-140 als Antwort übernehmen**, nur das Kriterium festlegen und die bestehende Messstand-Zeile weiterlaufen lassen. *Folge:* keine Arbeit jetzt; die Kernaussage „REGEL0 trägt“ bleibt durch E-139 beantwortet (brutto ja, robust nein).

*Empfehlung 1* — die Beschreibung kostet wenig, und das Kriterium braucht ohnehin die Zahlen; das Urteil bleibt bei E-139.

**F-B — Wonach die Regel gewählt wird.**
1. **Nach neuer Information: Tageszustand (Sichten) und Ereignisse je Asset**; langsame Marktlage nur Information; ATR des Assets schützt (§4). *Folge:* hält E-156, ist mit G7 messbar, nutzt die laufende Arbeit; keine Regel „nur im Bullenmarkt“.
2. **Zusätzlich die langsame Marktlage über längere Historie messen** (2020–26). *Folge:* längere Historie hebt die Fundquote (E-134), aber die Auflösung bleibt grob (+3 Pp je 7 T, E-151) — ein Urteil ist unwahrscheinlich, Aufwand Wochen.
3. **Nur Information, keine weitere Regel** (Nachtrag E-165: *„Wert nur in Risiko und Fakten“*). *Folge:* REGEL0 bleibt allein; das Vorhaben wird zum reinen Dashboard.

*Empfehlung 1.*

**F-C — Der Regel-Katalog (M1).**
1. **Voranalyse Regel-Katalog nur aus neuer Information** (E-156): Tageszustände aus G7 Stufe 1, Ereignistypen aus A1/S7, E-138-Hypothese nur auf Daten ab 25.10. *Folge:* eine geordnete Liste vor jeder Messung, ohne Mehrfachtesten.
2. **Zusätzlich Kandidaten aus vorhandenen Daten** (O13 Fortsetzung, Kern-Short 2.696). *Folge:* dafür müsstest du die Regel aus E-156 ausdrücklich ändern; Gegenbelege §23.68, E-165-h1b, 2.696 stehen schon.

*Empfehlung 1* — der Katalog kann aber erst sinnvoll gefüllt werden, wenn G7 Stufe 1 die ersten vollständigen Sichten liefert (S1 voraussichtlich in den nächsten Tagen).

**F-D — Dashboard (G19) vorziehen.**
1. B1, B2 (ohne Wal-Fünftel), B4, B5, B6 am Desktop bauen und nachweisen, dann ein NB-Bündel; B3 getrennt danach, mit zwei Modellen für A3 und A4 (Ü7). *Folge:* das Dashboard kommt in Tagen, ohne auf G7 zu warten.
2. Alles zusammen mit B3. *Folge:* ein Bündel weniger, wartet aber auf die Modellfrage und K-AL-0.

*Empfehlung 1.*

---

## 10. Gegenprüfung (06.11.2026, unabhängig, nur lesend)

Drei schwere, sieben mittlere, sechs leichte Befunde; **alle eingearbeitet**:

| # | Schwere | Befund | Eingearbeitet |
|---|---|---|---|
| 1 | schwer | Fassung 1 ließ die **Marktlage Hebel und Größe begrenzen** — die ATR ist die **eigene** des Assets (2.681); ein marktweiter Deckel ist nicht entscheidbar (E-151, E-153), widerspricht der Ausweichregel und der Nutzervorgabe 01.10. (*kein Deckel aus Makro/Marktwandel*), und „Regime unsicher → 3x“ verletzt Regel 4 | §4: Marktlage nur Information; ATR des Assets schützt |
| 2 | schwer | **E-155/E-156, 2.604, H2 fehlten**: die Suche nach einem Einstiegsvorsprung mit freien Daten ist abgeschlossen, Asset-Lage trägt keinen Ertrag — Fassung 1 schlug genau diese Lage als Regelwahl vor | §0, §2, §3, §4: neue Regeln nur aus neuer Information |
| 3 | schwer | „Regelwahl nach Marktlage nicht messbar“ war zu breit — gilt für die **langsame** Marktlage; die **schnelle** (Tageszustand) misst G7 Stufe 3 (G-Tag) | §3.1 drei Lagearten, §3.2 |
| 4 | mittel | „6–10 Regimewechsel“ gilt für 4,75 Jahre (2.599); E-151: 72 Wechsel in 12 Jahren, E-134: längere Historie hebt die Fundquote | §3.1, F-B 2 |
| 5 | mittel | „Makro-Nachmessung 10/2027“ stammt aus E-108 (Verwässerung), nicht aus O49 | gestrichen |
| 6 | mittel | „Tausende unabhängige Fälle“ falsch: effektiv ≈ 1 je Tag; das REGEL0-Plus ist ein Effekt marktweiter Tage (E-138) | §0, §1.2, §3.1 |
| 7 | mittel | Tagesklammer-Quelle §6.1 betrifft den gepaarten Handlungsvergleich; Abkehr von E-165 nicht benannt | §4 Abgrenzung zu E-165 |
| 8 | mittel | Erfolgsmessung zu optimistisch: 365 Signaltage ≈ zwei Jahre, MDE 1,01 Pp > Effekt; rückwärts nur Sep./Okt. neu, R-R11 | §1.3, F-A |
| 9 | mittel | E-136 ist **nach Kosten**; E-139 0/6 nur aus der Je-Tag-Bedingung, Geltungsbereich *bestand* | §1.2 |
| 10 | mittel | REGEL1 A/B/L sind keine Auslöser; Kern-Short 2.696, Ruhe 72 h 2.695 fehlten; O13-Gegenbelege fehlten | §2 |
| 11–16 | leicht | Blockzählung 21–23; Band 95 % statt 99 % verwechselt; Beleg Schutz = 2.681; 2.599 „unentschieden“; Auflösung G-Tag 72–79 %; O13-Gegenbelege | §1.3, §3, §1.1 |

Fragen: F-A um „E-139/E-140 übernehmen“ ergänzt, F-B um „nur Information“, F-C um die Bedingung aus E-156.

*Grundlage: drei lesende Bestandsaufnahmen (REGEL0/Hebel, Lage/Regime, Dashboard/Messanlage) am 06.11.2026 gegen Register, Entscheidungen und Voranalysen; E-138, E-155, E-156, 2.604, 2.681 und H2 am Wortlaut nachgeprüft.*
