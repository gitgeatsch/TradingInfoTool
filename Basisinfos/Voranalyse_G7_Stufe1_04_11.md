# Voranalyse G7 Stufe 1 — Sicht-Gutachten im Rückspiel (04.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag:** Nutzer 04.11.: *„Ja, Voranalyse heute“*
**Grundlage:**
- [`Voranalyse_G7_Messplan_02_11.md`](Voranalyse_G7_Messplan_02_11.md): §3 Messplan, §6 → a/a/a, §7 Stufe 0, §8/§9 S7-Menge a
- [`Datenbasis_Schichten_Sichten_28_10.md`](Datenbasis_Schichten_Sichten_28_10.md) §3a: Frage, Ergebnisform, F1–F6
- [`Voranalyse_Laufzeit_02_11.md`](Voranalyse_Laufzeit_02_11.md) §8: A1 fertig, zweiter Weg

**Stand:** nur Dokument. Nichts gebaut, kein LLM-Aufruf, Betrieb unberührt.

---

## 0. Worum es geht

Stufe 1 erzeugt die **Sicht-Gutachten**: je Sicht und Tag eines, im Rückspiel vom 01.12.2025 bis 31.10.2026 (335 Tage), auf Gemini.
Jedes prüft Prüfer v2 auf Faktentreue (Frage **F**).

Stufe 1 **misst noch nichts**. Gemessen wird in Stufe 2 (Frage **W**: kommt nach „kritisch“ wirklich Schlechteres?). Weil Stufe 2 dann auf
fertige Urteile schaut, muss **vor** dem ersten Gutachten feststehen und committet sein, **was** gemessen wird. Diese Vorabfestlegung steht
in §4.

---

## 1. Was da ist — und was fehlt

| Baustein | Stand | Für Stufe 1 |
|---|---|---|
| Zustände `agent/zustaende.py` | ✔ 35 Zustände S1–S4/S7 + S8, mit Jahrgängen (FRED), kein Vorgriff an 333 Tagen | Eingabe je Sicht: `zeilen(liste, sicht)` |
| Ereignisse A1 `agent/ereignisse.py` | ✔ **fertig 04.11.**: 6.701 Börsen (Regeln) + 25.561 LLM, `am(E, T, assets=assets_am(T))` | an die Sichten, je ≤ 7 T alt |
| S7-Menge | ✔ §9.1 a: REGEL0 zum Zeitpunkt + Kern | `assets_am(T)` |
| Prüfer v2 `agent/gutachten_pruefer.py` | ✔ 100 % erkannt / 0 Fehlalarme (Stufe 0a) | `eingabe()` + `pruefe()` je Gutachten |
| Messanlage `g7_messanlage.py` | ✔ Selbsttest bestanden (Stufe 0b), Kreisverschiebung über die volle Bahn | erst Stufe 2 |
| Vergleichsarm | ✔ Stufe 0c: Zustände allein, 15 Befunde | erst Stufe 2 |
| Kurse | ✔ Arbeitskopie `data/_g7/kurse/` bis 02.11. (§9.5) | erst Stufe 2 |
| **Fragen-Prompt je Sicht** | ✗ **fehlt.** Es gibt nur das Format im Prüfer (`treiber` mit `schluessel`/`wert`/`rang`/`klasse`) und den Entwurf der Fragen (Datenbasis §3a) | **zu bauen** |
| **Lauf und Ablage** | ✗ **fehlt** | **zu bauen**, eigene Ablage, nie Produktion |
| **Frage S8** | ✗ steht in keinem Dokument (Datenbasis §3a nennt S1–S7) | **festzulegen** (§4) |

---

## 2. Befunde

### S1-1 Die Auflösung reicht nur für starke Sichten

Gemessen in Stufe 0b, Zeitraum Dez. 2025 bis Okt. 2026: **22 Blöcke**, sicher gefunden wird erst eine Wirkung von **≈ 0,5 σ** (bei
0,3 σ nur 36–65 %).

Nachgeprüft heute, Breite aus der Arbeitskopie: bis 01.11. vorhanden, 127 Werte je Tag, H = 1/3/5 je **22 Blöcke**. Die Grenze von
18 Blöcken aus Stufe 0b ist damit weg.

⚠️ **Folge:** Ein Gutachten muss stark sein, um gesehen zu werden. Der Vergleichsarm (Stufe 0c) trägt |ρ| 0,07–0,23. Liegt das LLM in
dieser Größenordnung, lautet das ehrliche Ergebnis von Stufe 2 **„nicht trennbar“**, nicht „trägt nicht“. Erst der zweite Zeitraum
(Stufe 5: 2025 auf gpt-oss) gibt mehr Blöcke. Das ist vorab festzuhalten, damit ein Nullbefund nicht als Widerlegung gelesen wird.

### S1-2 S2 und S4 fragen nach Wochen — die Messung trägt nur bis 5 Tage

Die Fragen an S2 (Liquidität, Zinsen) und S4 (Dollar, Rohstoffe) zielen auf **Wochen** (Spot). Ein Zeitraum allein trägt nur **H ≤ 5**
(G7-1). H = 7/10 geht nur mit beiden Zeiträumen, H = 14 nie.

→ S2/S4 werden in Stufe 1 **trotzdem erzeugt**: das finale LLM (Stufe 3) und der Beitrag je Sicht (Stufe 4) brauchen **alle** Sichten
als Eingabe. In Stufe 2 bekommen sie nur H = 5 als **Auskunft**. Ihr eigentlicher Horizont wartet auf Stufe 5.

### S1-3 S7 ist eine andere Messung

S1–S4 sind **Tagesurteile über den Markt** und werden gegen BTC und die Breite gemessen. S7 urteilt **je Asset über ein Ereignis**
(„betrifft Asset X, neu, schon eingepreist?“) und wird gegen den **Ertrag dieses Assets** gemessen.

- Dafür hat die Messanlage aus Stufe 0b **keinen Selbsttest**: andere Einheit (Asset × Tag), Ballung je Asset und je Tag, andere σ.
- Memory: *Selbsttest vor dem ersten Blick bei jeder neuen Nullwelt*.

→ S7 wird in Stufe 1 erzeugt. **Vor** Stufe 2 bekommt S7 eine eigene Anlage mit Selbsttest (eigener kleiner Schritt, ohne LLM).

### S1-4 Weg b der Nachrichten hat keinen zweiten Weg

Laufzeit §8: Die 21.670 übrigen Nachrichten (Weg b) hat nur flash-lite gelesen, 26 % als relevant eingestuft. An die Sichten gehen sie
zusammen mit den Vorfilter-Treffern.

→ Jede Ereigniszeile in der Eingabe wird in der Ablage mit ihrer **Herkunft** vermerkt (Regel / Vorfilter / Weg b). Dann kann Stufe 2
getrennt ausweisen, ob ein Urteil an Weg b hing.

### S1-5 Kontingent und Laufzeit

| | |
|---|---|
| Modell | **gemini-3.5-flash-lite**, Schlüssel 2. Das einzige Modell mit belegt ≥ 480 Aufrufen/Tag (Laufzeit §6), Wissensstand sauber ab Dez. 2025 (Stufe 0d) |
| Aufrufe | 6 Sichten × 335 Tage = **2.010** · dazu Wiederholung (S1-6) ≈ 100 · Nachfassen bei Formfehlern ≈ 5 % ≈ 100 → **≈ 2.200** |
| Token je Aufruf | Eingabe 105–830 (G7-3; S1 und S7 jetzt mit Nachrichten mehr) + Anweisung ≈ 1.000 + Antwort ≈ 500 |
| Dauer | bei 480/Tag **≈ 4,5 Tage**. Das Kontingent setzt um 09:00 MEZ zurück |
| Danach | Stufe 3 (finales LLM, 903 + 1.532 Einstiege, Menge b) braucht dasselbe Modell weitere ≈ 5 Tage. A4 Gegenanwalt braucht ein **anderes** Modell (Ü7). Dessen Kontingent ist **nicht belegt** (3.6-flash: sauber, Tagesgrenze ungemessen) |

⚠️ Nach Memory *Kontingent je Modell belegen*: vor Stufe 3 die Tagesgrenze des A4-Modells messen, nicht aus einer Tabelle übernehmen.

### S1-6 Eigenrauschen

Dieselbe Eingabe gibt nicht immer dasselbe Urteil (L-4: 16 %). Ohne Messung ließe sich ein schwacher Befund nicht vom Würfeln trennen.

→ **5 % der Tage** (17 Tage, fest ausgelost mit Saat, je alle 6 Sichten) werden ein zweites Mal gefragt. Gemessen wird die Übereinstimmung
von `zustand` und `wirkung_krypto`.

### S1-7 Faktentreue wird gezählt, nicht verworfen

Prüfer v2 zählt je Gutachten die Abweichungen (falscher Wert, Rang, Bezug, Zahl ohne Beleg). Wie bei Z-1 wird **nichts verworfen**:
Ein Wächter, der selbst verwirft, macht seine Wirkung unsichtbar.

In Stufe 2 steht die Messung **mit allen** Gutachten als Hauptlauf. Ohne die beanstandeten läuft sie nur zur Auskunft.

---

## 3. Bauplan

| # | Was | Wo |
|---|---|---|
| B1 | **Fragen-Prompt je Sicht:** Rolle, Frage (§4), Ergebnisform nach Datenbasis §3a. Jeder Treiber mit Schlüssel und angezeigtem Wert, so wie Prüfer v2 ihn liest. JSON, je Sicht eine Antwort | `agent/sichten_gutachten.py` (in `agent/`, weil G8b es live braucht) |
| B2 | **Eingabe je Sicht und Tag:** `zustaende.zeilen` + Ereignisse `ereignisse.am(..., assets=assets_am(T))`, je Zeile mit Herkunft (S1-4). Eingabe-Prüfsumme | dto. |
| B3 | **Lauf:** wiederaufnehmbar wie A1. Tagestopf leer → warten. Formfehler → Nachfassen. Wiederholung 5 % (S1-6) | dto., `python -m agent.sichten_gutachten --lauf` |
| B4 | **Ablage** `data/_g7/gutachten.db`: Tag, Sicht, Lauf, Modell, Prompt-SHA, Eingabe, Antwort roh, Felder, Prüfergebnis v2. **Nie** `tradinginfotool.db`, nie `sichten.db` | dto. |
| B5 | **Prüfpaket** `SichtenGutachten`: Eingabe ohne Vorgriff (nur bekannt bis T), Schlüssel aus dem Prompt = Schlüssel des Prüfers, Ablage-Pfad nie Produktion, Antwortleser gegen kaputte und erfundene Felder, Wiederaufnahme ohne Doppelaufruf | `pruefe_pakete.py` |
| B6 | **Probe vor dem Lauf:** 3 Tage × 6 Sichten = 18 Aufrufe. Ich sehe Form und Prüfergebnis an, **nicht** gegen Kurse | — |

⚠️ Die Probe B6 ist **kein Blick auf den Wert**. Sie prüft nur, ob die Antworten lesbar und treu sind. Kursreihen werden bis zum Ende von
Stufe 1 nicht mit Urteilen zusammengebracht.

---

## 4. Vorabfestlegung für Stufe 2 — Entwurf (wird vor dem ersten Lauf-Aufruf committet)

**Urteil als Zahl je Sicht und Tag:**
- `zustand`: normal 0 · auffällig 1 · kritisch 2
- `wirkung_krypto`: stützt −1 · keine 0 · belastet +1

**Hauptgröße je Sicht — EINE.** Alles andere ist Auskunft. Damit gibt es vier Haupttests statt 48.

| Sicht | Frage (Datenbasis §3a, Horizont eingesetzt) | Hauptgröße | Richtung | Begründung der Richtung |
|---|---|---|---|---|
| **S1** Krypto gesamt | Ist die Krypto-Gesamtlage ungewöhnlich (Hebel überdehnt, Stablecoin-Abfluss, Breite bricht weg), und erhöht das das Risiko eines breiten Einbruchs in **1–5 Tagen**? | `zustand` ≥ auffällig gegen **Breite `tief_s`, H = 3** | einseitig unten | Die Frage fragt nach einem Einbruch. Die Breite trägt im Vergleichsarm die meisten Befunde |
| **S3** Risikoappetit | Gibt es Stress an Aktien- oder Kreditmärkten, der in **1–5 Tagen** auf Krypto übergreifen kann? | `zustand` ≥ auffällig gegen **BTC `tief_s`, H = 3** | einseitig unten | Übergriff von außen trifft zuerst die liquiden Werte |
| **S2** Liquidität, Zinsen | Hat sich die Liquiditäts- oder Zinslage so verändert, dass Risikoanlagen in den nächsten Wochen belastet oder gestützt werden? Welcher Termin kann das kippen? | `wirkung_krypto` gegen **BTC `ertrag_s`, H = 5** — **nur Auskunft** (S1-2) | einseitig unten | belastet → niedriger Ertrag |
| **S4** Dollar, Rohstoffe | Bewegt sich Dollar, Gold oder Öl ungewöhnlich, und auf welchem Weg träfe das Krypto? | wie S2, **nur Auskunft** | einseitig unten | dto. |
| **S8** Termine | Steht in den nächsten **1–3 Tagen** ein Termin an, der nach seinem gemessenen Faktor die Schwankung erhöht, und in welche Richtung kann er kippen? | `zustand` ≥ auffällig gegen **BTC \|ertrag_s\|, H = 1** | einseitig oben | Ein Termin sagt die Größe der Bewegung, nicht ihre Richtung |
| **S7** Ereignisse je Asset | Welche Meldung betrifft Asset X direkt, ist sie neu, und hat der Kurs schon reagiert? | `wirkung` je Asset gegen **Asset `ertrag_s`, H = 3** | einseitig unten bei „belastet“, oben bei „stützt“ | — erst nach eigener Anlage und Selbsttest (S1-3) |

**Haupttests:** S1, S3, S8 und (nach S1-3) S7. Über diese vier wird nach **Holm** korrigiert. Alle anderen Kombinationen (H = 1/5,
`ertrag` statt `tief`, BTC statt Breite) sind Auskunft und werden **nie** zu einem Befund hochgestuft.

**Gegen den Vergleichsarm (Stufe 2, §3 des Messplans):** je Hauptgröße ein Vergleichsurteil **ohne LLM** mit **gleicher Rate**. Die
Tage mit den meisten auffälligen Zuständen derselben Sicht werden so markiert, dass der Anteil der LLM-„auffällig“-Tage gleich ist.
Das Gutachten **bringt etwas** nur, wenn seine Wirkung über der des Vergleichsurteils liegt, mit Abstand außerhalb des Bands derselben
Nullwelt.

**Regeln, die dazugehören:**
- „trägt“ nur mit Band, je Tag (Tagesblock), Geltungsbereich (Dez. 2025 – Okt. 2026, ein Modell) und **zweitem Weg** (Stufe 5).
  Ohne Stufe 5 heißt ein Treffer **„Hinweis“**.
- Kein gleiches Ergebnis in 2025 erwartet (Memory *Epochen*).
- Weg b getrennt ausweisen (S1-4).
- Faktentreue: Hauptlauf mit allen Gutachten (S1-7).
- Auflösung vorab: ≈ 0,5 σ (S1-1). Unterhalb heißt es „nicht trennbar“.

### 4.1 Vorabfestlegung S7 — nachgetragen 05.11.2026, VOR dem ersten S7-Aufruf

Grundlage: `Voranalyse_G7_S7_Anlage_05_11.md` (§1–§4b), Nutzer 05.11.: *„Ja, d + Wort-Arm“*. Anlage und Selbsttest:
`Rechenkern_02_10/g7_s7_anlage.py` → `g7_s7_anlage.txt`.

| | Festlegung |
|---|---|
| **Arme** | **S7 = Form d (HAUPTARM)**: das LLM sieht keinen Kurs, `eingepreist` = unbekannt; die Kursreaktion je Meldung und Asset liegt als Fakt daneben (`agent/kursreaktion.py`, geht an das finale LLM). **S7w = Arm e**: dieselbe Eingabe, je Asset nur das Wort gestiegen / gefallen / unverändert (gegen BTC, Grenze ±0,5 übliche Schwankungen, vorab) |
| **Einheit** | Zelle Asset × Stichtag, nur Ereigniszellen (in der S7-Eingabe betrifft eine Zeile das Asset), nur `wdh` 0 |
| **Urteil** | je Zelle: stützt +1, belastet −1, keine 0; mehrere Einträge → Vorzeichen der Summe, Gleichstand 0; nicht genannte Assets 0 |
| **Zielgröße** | `ertrag_s = ln(P[T 01:00 + 72 h] / P[T 01:00]) / (σ_a · √3)`, σ_a aus 60 Tagen vor T (S7-5) |
| **Statistik** | t = (Mittel stützt − Mittel belastet) / Standardfehler, **einseitig oben** (= unten bei belastet, oben bei stützt) |
| **Nullwelt** | **Asset-Zeit**: Urteilsreihe jedes Assets um dasselbe k im Kreis, k = 1 … 334 (volle Bahn) |
| **Band** | 95. Perzentil der Nullwelt — oder das **im Selbsttest geeichte** Band, falls ein Erzeuger über 6,5 % lag (steht in `g7_s7_anlage.txt`, Zeile „Band für die Messung“) |
| **Mindestmaß** | ≥ 20 Blöcke à 15 Tage mit Urteilen, sonst KEIN BEFUND |
| **Holm** | S7 ist einer der vier Haupttests (S1, S3, S8, S7). Der Platz S7 hat **zwei Schüsse** (d und e): der Platz gilt als getroffen, wenn **d** trägt; trägt nur **e**, muss e das **97,5. Perzentil** (Bonferroni im Platz) schlagen |
| **Vergleichsarm** | Typ-Regel (S7-4) auf gleicher Zahl Zellen je Seite wie S7, gewählt nach Zahl der Meldungen. S7 **bringt etwas** nur, wenn die gepaarte Differenz t(S7) − t(Typ) über ihrem Nullband liegt (beide um dasselbe k verschoben) |
| **Wahl d / e** | e **ersetzt** d nur, wenn (e trägt nach der Holm-Zeile und d nicht) **oder** die gepaarte Differenz t(e) − t(d) über ihrem Nullband liegt. Sonst bleibt d. Die Wahl wird **berichtet**, nicht still getroffen |
| **Auskunft, nie hochgestuft** | H = 1 und H = 5 · Kern getrennt · nur Meldungen < 24 h · Weg b getrennt · Kurs-Regel (das Wort selbst als Urteil, Fortsetzung und Gegenrichtung) · Eigenrauschen aus `wdh` 1 |
| **Reihenfolge** | gemessen wird erst, wenn S7 **und** S7w vollständig abgelegt sind (`--messen` verweigert sich vorher) |
| **Nachtrag 05.11. (nach der Gegenprüfung, VOR dem ersten S7-Aufruf)** | Selbsttest auf der um die eingestellten Werte erweiterten Menge (10.296 Zellen): G-Lauf 5/Tag 7,0 % > Toleranz → Band **geeicht auf das 96,5. Perzentil** (alle Erzeuger ≤ 5 %). Damit gilt für e im Platz S7 die Bonferroni-Grenze **1 − (1 − 0,965)/2 = P98,25** statt P97,5. Entschieden wird über den **Rang** (wie im Selbsttest). S7/S7w ohne Schwere-Text, Kursfakt und Schwere in der Ablage; S8 mit Terminfaktor nur aus Daten vor 2025-12-01 (`Voranalyse_G7_S7_Anlage_05_11.md` §7) |

---

## 5. Zur Abstimmung — eine Frage: Umfang von Stufe 1

| | Weg | Aufrufe / Dauer | Folge |
|---|---|---|---|
| **a** | **alle sechs Sichten** täglich (S1–S4, S7, S8) | ≈ 2.200 / ≈ 4,5 T | Stufe 3 und 4 haben alle Eingaben. S2/S4 nur Auskunft, S7 nach eigener Anlage |
| b | nur die **jetzt messbaren** S1, S3, S8 | ≈ 1.100 / ≈ 2,3 T | 2 Tage schneller bis Stufe 2. Für Stufe 3 müssten S2, S4 und S7 nachgeholt werden, sonst fehlt dem finalen LLM die Hälfte der Lage |
| c | erst S7-Anlage und Selbsttest, dann a | wie a, Start 1 T später | S7 wäre beim Lauf schon messbar. Am Lauf selbst ändert das nichts |

**Empfehlung a.** Das finale LLM in Stufe 3 bekommt laut Datenbasis §3a die Ergebnisse **aller** Sichten. b spart also nur scheinbar
Zeit. Die S7-Anlage (c) kann **während** des Laufs gebaut werden, sie braucht kein LLM.

**Danach, ohne weitere Frage:** B1–B5 bauen, prüfen, Probe B6 (18 Aufrufe), Vorabfestlegung §4 committen, dann der Lauf.

### 5.1 Entschieden 05.11.2026: a, S7 zuletzt

Nutzer 05.11.: *„ja hört sich vernünftig an also deine Empfehlung“*

- **a**: alle sechs Sichten in **einem** Lauf, ein Modellstand für die ganze Eingabe von Stufe 3.
- **Reihenfolge im Lauf:** zuerst S1, S3, S8, S2, S4 (≈ 1.700 Aufrufe, ≈ 3,7 T), **S7 zuletzt**. In dieser Zeit entstehen
  S7-Anlage mit Selbsttest und der Selbsttest für \|ertrag_s\| (S8), ohne LLM. Verlangt der S7-Selbsttest eine andere
  Antwortform, wird S7 vor dem ersten S7-Aufruf angepasst (neue Prompt-SHA, im Dokument vermerkt).
- **Kein Blick** auf S1/S3/S8 gegen Kurse, bevor Stufe 1 ganz fertig ist (sonst Prompt-Anpassung nach Ergebnis).

---

## 5.2 Bau 05.11.2026 (B1–B5)

| # | Gebaut | Wo |
|---|---|---|
| B1 | Prompt je Sicht mit Rolle, Frage (Horizont eingesetzt), Regeln, Ergebnisform §3a. **S7** zusätzlich `assets: [{asset, wirkung, ereignis, neu, eingepreist}]` = das Urteil je Asset für §4 | `agent/sichten_gutachten.py` `prompt()` |
| B2 | Eingabe: Zeilen tragen den **Prüfer-Schlüssel** in eckigen Klammern (`[S1.dvol.BTC]`, `[termin fomc]`), Ereignisse eine **E-Nummer** statt des Links (das Modell muss keinen Link abschreiben; der Leser setzt den Beleg wieder ein). Herkunft je E-Nummer (`boerse_regel`/`boerse_llm`/`vorfilter`/`weg_b`) in der Ablage | `eingabe()`, `herkunft()` |
| B3 | Lauf wiederaufnehmbar je (Tag, Sicht, Wiederholung, Modell, **Prompt-SHA je Sicht**). Reihenfolge S1, S3, S8, S2, S4, **S7 zuletzt**, je Sicht 335 Tage + 17 Wiederholungen = **2.112 Aufrufe**. Formfehler → bis 3 Versuche, dann **unlesbar abgelegt** (gezählt) | `plan()`, `lauf()` |
| B4 | Ablage `data/_g7/gutachten.db` (Probe getrennt: `gutachten_probe.db`); verweigert `tradinginfotool.db` und `sichten.db` | `verbinde()` |
| B5 | Prüfpaket **`SichtenGutachten` 12/12**: Ablage, Plan, SHA je Sicht, Leser (zählt statt verwirft), Herkunft, Treue end-to-end, Nachfassen, Wiederaufnahme ohne Doppelaufruf, **Vorgriff bricht vor dem Aufruf ab**, echte Eingabe an 3 Tagen × 6 Sichten (Schlüssel = Prüfer-Schlüssel), **kein Kurszugriff im Modul** | `pruefe_pakete.py` |

Weitere Entscheidungen, mit Grund:
- **Stichtag** T = 00:00 UTC wie der Vergleichsarm (Zustände Stand ≤ T−1, Ereignisse bekannt ≤ T).
- **`reasoning_effort` medium** (A1: low). A1 ordnet ein, hier wird abgewogen. Das Kontingent zählt Aufrufe, nicht Token.
- **`eingepreist_beleg`** wird als Freitext mitgeprüft (an Prüfer v2 als `zustand_text`), die S7-Asset-Belege als weitere Ereignis-Treiber. Prüfer v2 selbst ist **unverändert**.
- ⚠️ **S7 und „eingepreist“:** Die S7-Eingabe enthält **keine Kursreaktion je Asset**. F3 („hat der Kurs schon reagiert?“) kann das Modell dort nur mit „unbekannt“ beantworten. Wird mit der S7-Anlage entschieden, **bevor** der erste S7-Aufruf geht (§5.1).

## 5.3 Probe B6 (05.11.2026) — drei Durchgänge, nur Form und Treue

Tage ausgelost (Saat, nicht ausgesucht): 12.02., 14.05., 25.10.2026. Ablage `data/_g7/gutachten_probe.db`, getrennt vom Lauf. Kein
Abgleich mit Kursen.

| Durchgang | Aufrufe | lesbar | beanstandet | Ursache | Behoben |
|---|---|---|---|---|---|
| 1 | 10 (Zeitdeckel) | 10 | 9 | `klasse` mehrdeutig („wie angegeben“ → „yfinance“, „Zustand“); bei S8 Faktor und Tage im Text | Klassenliste ausgeschrieben; **in Texten keine Zahlen** außer dem Horizont |
| 2 | 18 | 18 | 5 | Schlüssel samt `[ ]` übernommen; bei Ereignissen der **Bereich** (`makro_usa`) als Typ | Prompt „ohne Klammern“ + Leser entfernt Klammern; Ereigniszeile beschriftet `betrifft:` / `Typ:` |
| **3** | **18** | **18** | **0** | — | **160 Angaben geprüft, alle belegt** |

⚠️ **Alle Beanstandungen lagen am Prompt, keine am Modell.** Prüfer v2 hat sie genau so gefunden, wie er gebaut ist. Das zeigt, dass
er trennt, und zugleich: ein Prompt muss gegen den Prüfer erprobt sein, bevor ein Lauf startet.

Beobachtungen ohne Urteil (gehören nicht in eine Bewertung, nur Vormerkung für Stufe 2):
- **S4** an allen drei Tagen „auffällig“ (Gold, Öl, Kupfer 2026 oft am Rand ihres 5-J-Rangs). Wird das über alle Tage so, trennt S4
  nicht. In Stufe 2 erst die Rate ansehen.
- **S7** sagt zu `eingepreist` fast immer „teilweise“, obwohl die Eingabe keine Kursreaktion je Asset hat (siehe §5.2 ⚠).
- **S8** am 12.02. (CPI in 1,6 T) „normal“: das Modell liest den 24-h-Faktor 1,1× als gering. Das ist ein Urteil, kein Formfehler.

Laufende Prompt-SHA (Durchgang 3), gelten für den Lauf: S1 `62578b8c9a98` · S3 `6d524389486d` · S8 `03d10f22fdb6` · S2 `31f7526e934c` ·
S4 `e8502a4bed81` · S7 `8fe0759a2510` (S7 kann sich nach §5.1 noch ändern).

Kontingent heute: 46 Aufrufe für die Probe. Lauf **2.112 Aufrufe**, bei ≈ 480 am Tag ≈ 4,4 Tage; rund 40 s je Aufruf.

## 5.4 Lauf-Beobachtung 05.11. (nur Form und Treue)

Nach 98 S1-Gutachten: alle lesbar, 6 beanstandet — 5 × der **zweite** Wert der Zeile unter `wert` (Feld vertauscht, kein Faktenfehler), 1 × **Fehler in Prüfer v2** (`-2.43e-05` als −2 gelesen). Kein Abbruch, alles roh abgelegt; Neurechnung mit Prüfer v2.1 in Stufe 2. Ausführlich: [`Voranalyse_G7_S7_Anlage_05_11.md`](Voranalyse_G7_S7_Anlage_05_11.md) S7-7.

## 5.5 Beschleunigung — entschieden 05.11.2026 abends, VOR dem ersten Blick gegen Kurse

Nutzer 05.11.: *„ja - paket so übernehmen“*. Ersetzt in §5.1 „S7 zuletzt“ und „kein Blick, bevor Stufe 1 ganz fertig ist“.

| | Festlegung |
|---|---|
| **Reihenfolge** | **S1, S3, S8, S7, S7w**, danach die Auskunftssichten **S2, S4** (`REIHENFOLGE`). Gesperrte Sichten überspringt der Lauf. Grund: Bis zu den vier Haupttests fallen ≈ 700 Aufrufe weniger an |
| **Messen je Sicht** | Jede Hauptsicht wird **genau einmal** gemessen, sobald sie **vollständig** abgelegt ist (335 Tage + Wiederholungen). Kein Teilblick, kein zweites Mal |
| **Schutz** | Die erste Messung geschieht erst, wenn **alle** Prompt-SHAs fest sind, S7/S7w also nach Probe 2 freigegeben. Ändert sich danach ein Prompt, ist die betroffene Sicht **nur noch Auskunft**. Das Ergebnis einer Sicht ist **kein Grund**, eine andere abzubrechen oder anzupassen |
| **Holm** | Gilt am Ende über alle **vier** Haupttests (m = 4 bleibt, auch wenn einer fehlt). Eine früh gemessene Sicht wird bis dahin **roh** berichtet (Rang, p), als „trägt“ erst nach der Holm-Zeile |
| **Frist** | **30.11.2026.** Reicht sie nicht, werden zuerst S2/S4 nicht mehr gefragt. Eine unvollständige Hauptsicht wird **nicht** gemessen. Ob verlängert wird, entscheidet der Nutzer |
| **Abbruch** | nur aus vorab festgelegten Gründen: technisch Rot (unlesbar > 5 %) · Messbarkeit Rot (Anteil außerhalb 5–95 % oder < 20 Blöcke je Seite bei vollständiger Sicht) · Frist |
| **Laufwache** | täglich 08:00, `g7_laufwache.py`, ohne Blick gegen Kurse; Meldung nur bei Gelb oder Rot |

**Kontingent, gemessen 05.11.:** Google nennt die Grenze im Fehlerkörper, `GenerateRequestsPerDayPerProjectPerModel-FreeTier` = **500**
(Schlüssel 2, `gemini-3.5-flash-lite`). Am Kontingenttag 05.11. (ab 09:00 MEZ) waren beim 429 aber nur **52** Gutachten abgelegt.
⚠️ Verdacht, **nicht belegt**: Die 503-Fehlversuche zählen mit (bis 15:00 alle 30 s wiederholt, zwei Prozesse parallel). Deshalb gibt es seit
05.11. 15:24 UTC das **Anfragebuch** `data/_g7/anfragen.csv`: jede echte Anfrage mit Kontingenttag, Schlüsselname und Status, ohne
Schlüsselwert. Die Laufwache weist aus, nach wie vielen Anfragen die Tagesgrenze kam und wie viele davon 5xx waren. Seit 15:00 wird ein
503 ansteigend wiederholt (30 s … 600 s).

**Probe 2 und Freigabe S7/S7w, 06.11.2026** (`data/_g7/gutachten_probe2.db`, 3 Tage × 7 Sichten, nur Form und Treue, kein Kurs danach):
21/21 lesbar, 0 Formfehler, 1 Treue-Beanstandung — S7 am 25.10. schreibt den Typ `pair_entfernt`, die Eingabe sagt `paar_entfernt`
(Schreibweise, kein Falschwert). S7 setzt `eingepreist` 3 × wie verlangt auf „unbekannt“. S7w folgt dem gezeigten Wort: WAL „gefallen“ → ja,
ON „gestiegen“ → ja, BTC mit gemischten Wörtern → teilweise. → **`GESPERRT = ()`, alle sieben Prompt-SHAs ab jetzt eingefroren**; Lauf neu
(`_g7_stufe1_lauf9.txt`). Eine alte Planprüfung im Paket verlangte noch „S7 zuletzt“ und war damit rot; sie folgt jetzt §5.5 (28/28).
⚠️ Der Lauf war am 06.11. zweimal ohne Fehler beendet (05.11. ≈ 18:25 UTC und 06.11. 11:05 UTC, `^C` im Fehlerprotokoll). Seit lauf9 startet
er in einer **eigenen Prozessgruppe ohne Konsole** (`CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW`), damit ihn kein Strg+C-Signal erreicht.

## 6. Gegenprüfung dieser Voranalyse

| Aussage | geprüft wie | Ergebnis |
|---|---|---|
| Kein Fragen-Prompt vorhanden | Suche nach `kippt_wenn` im ganzen Projekt | nur Prüfer v2, Stufe-0-Selbsttest, Datenbasis-Entwurf und Prüfsuite ✔ |
| Sichten S1–S4, S7, S8 | `zustaende.SICHTEN` | `("S1", "S2", "S3", "S4", "S7", "S8")` ✔. S5/S6 haben keine Zustände |
| S2 mit Jahrgängen | `zustaende.py` Kopf und Z. 130–136 | Jahrgang gilt ab `bekannt_ab` (Z1) ✔ |
| Breite bis Okt. messbar | heute nachgerechnet aus `data/_g7/kurse/` | 22 Blöcke bei H = 1/3/5 ✔ |
| Messanlage einseitig verfügbar | `g7_messanlage.messe(richtung="unten"/"oben")` | ✔ |
| \|ertrag_s\| für S8 | `zielgroesse` kennt nur `ertrag`/`tief` | ⚠ **nicht vorhanden** → in Stufe 2 aus `ertrag_s` gebildet. Dafür ist ein **eigener Selbsttest** nötig, weil ein Betrag eine andere Verteilung hat |
| Kontingent flash-lite | Laufzeit §6 (Fehlerkörper, N4-Lauf), A1-Volllauf 432/479 am Tag | ✔ ≈ 480/Tag |
