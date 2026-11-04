# Voranalyse Laufzeit — die Wochen auf dem kritischen Weg sauber verkürzen (02.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag (Nutzer 02.11.):** *„Ok wir haben sehr lange messzeiträume über wochen, das sollten wir wenn möglich vermeiden bzw minimieren“* ·
*„Ja bitte prüfen für eine saubere verkürzung der Zeit. Vor allem finde ich es seltsam dass wir hier auf die alte Groq Schiene setzen müssen.“*
**Gehört zu:** [`Voranalyse_G7_Messplan_02_11.md`](Voranalyse_G7_Messplan_02_11.md) §3–§5 (Stufen, Budget) ·
[`Voranalyse_A1_Ereignisleser_01_11.md`](Voranalyse_A1_Ereignisleser_01_11.md) §9 (Prompt 3, Volllauf) ·
[`Voranalyse_Dashboard_LLM_28_10.md`](Voranalyse_Dashboard_LLM_28_10.md) §1.5a (Anbieter gemessen) · Gesamtplan G3, G7, G8.
**Stand:** Voranalyse — gemessen, **nichts umgestellt**. Der Groq-Lauf A1 läuft weiter, bis entschieden ist. Skript:
`Rechenkern_02_10/zeit_voranalyse.py` → `zeit_voranalyse_r.txt`; LLM-Antworten nur in `data/_a1/a1_stichprobe_llm_gemini.db`.

---

## 1. Warum A1 auf Groq läuft — die Ursache

Am 28.10. wurde festgelegt (Dashboard-Voranalyse §1.5a): *„Rückspiel und Klassifikation zur Messung (A1, später A2) auf Groq gpt-oss-120b …
Gemini nie für ein Rückspiel 2025“*. Der Grund ist die **Kontamination**: Gemini kennt Kurse bis etwa Oktober 2025.

⚠️ **Für A1 trifft der Grund nicht zu.** A1 liest Nachrichten erst **ab Dezember 2025** (`NACHRICHT_AB`). Für diesen Zeitraum sind die Gemini-
Modelle 3.1/3.5/3.5-lite/3.6 **gemessen sauber** (G7 §7, Positivkontrolle). Und Einordnen ist ohnehin keine Prognose (A1-9). Die Regel
war für 2025-Rückspiele gemacht und wurde pauschal auf A1 übertragen. **Für 2025 (G7 Stufe 5) gilt sie weiter.**

## 2. Befunde — gemessen am 02.11.

| # | Befund | Beleg |
|---|---|---|
| **L-1** | Am Schlüssel 2 (eigener Desktop-Topf) stehen **neun Text-Flash-Modelle**, jedes mit eigenem Topf von 500 Aufrufen am Tag: 3-flash-preview, 3.1-flash-lite, 3.5-flash, 3.5-flash-lite, 3.6-flash, 3.7-flash, 3.8-flash u. a. | Modellliste der API |
| **L-2** | **gemini-2.5-flash und 2.5-flash-lite sind gesperrt**: *„no longer available to new users“* (404). Ein Gemini-Weg für **2025** mit älterem Wissensstand besteht damit **nicht** | Fehlerkörper der API |
| **L-3** | **A1 Prompt 3 auf gemini-3.5-flash taugt** (Regel vorab: Fehlalarm ≤ 3, Verlust ≤ 5, Wiederholung ≥ 57/60) — Tabelle unten. 3.6-flash verfehlt knapp (4 Fehlalarme) | Stichprobe 3, Hand vorher festgeschrieben |
| **L-4** | OpenRouter (kostenlos): 14 Modelle, **kein gpt-oss mehr**, alle jünger → für 2025 unbrauchbar, für Aufgaben ab Dez. 2025 Reserve | Modellliste |
| **L-5** | Groq: gpt-oss-120b und gpt-oss-20b haben **je einen** Topf von 200.000 Token am Tag | Modellliste, §1.5a |
| **L-6** | Gemini meldet zeitweise **503 „high demand“** (3.5-flash beim Test). Der Aufruf wartet und wiederholt — es kostet Zeit, keine Daten | Fehlerkörper |
| **L-7** | Der Groq-Lauf A1 steht bei **Stapel 65 von 1.009** nach 11 h (≈ 4 Stapel/h) → Rest **≈ 10 Tage** | Protokoll `a1_volllauf_p3.txt` |

**L-3 im Einzelnen** (dieselben 60 Titel, dieselbe Handeinordnung):

| | gpt-oss-120b (Groq) | **gemini-3.5-flash** | gemini-3.6-flash |
|---|---|---|---|
| Typ richtig | 77 % | **85 %** | 85 % |
| Ereignis ja/nein | 92 % | 93 % | 93 % |
| Sicht relevant ja/nein | 90 % | 90 % | 90 % |
| Fehlalarm / Verlust | 2 / 4 | **3 / 3** | 4 / 2 |
| ohne die 15 zweifelhaften Handfälle | 96 %, 0 / 2 | 93 %, 3 / 0 | 93 %, 3 / 0 |
| gleicher Typ bei Wiederholung | 100 % | 95 % | 95 % |
| hochgerechnet Fehlalarm / Verlust | 3 % / 7 % | **1 % / 6 %** | 4 % / 3 % |

→ Gemini liest **mindestens so gut** wie gpt-oss; es rauscht etwas mehr (95 % statt 100 % gleiche Typen bei Wiederholung).

## 3. Der kritische Weg — heute und mit den Hebeln

| Schritt | heute | mit Hebel | Hebel | sauber, weil |
|---|---|---|---|---|
| **A1 Nachrichten** | ≈ 10 T (Groq) | **≈ 2–3 T** | gemini-3.5-flash, 1.009 Stapel bei 500/Tag + Nachfassen, Puffer für 503 | gemessen sauber ab Dez. 2025; liest mindestens so gut (L-3); **ein** Modell für den ganzen Zeitraum |
| **Stufe 1** Sicht-Gutachten | ≈ 4 T | ≈ 4 T, **überlappt** mit Stufe 3 | ein Modell für alle Sichten (sonst wären Sicht und Modell vermengt) | unverändert |
| **Stufe 3** finales LLM + A4 | ≈ 5 + 5 T | **≈ 1–2 T**, läuft hinter Stufe 1 her | **ein Aufruf je Tag** mit allen Einstiegen des Tages (≈ 322 statt 2.379), A4 parallel auf eigenem Topf | nur mit **Gleichheitsprobe** vorher (§4.2) — live kommt jeder Einstieg einzeln |
| Stufe 2, 4 | Stunden | Stunden | — | — |
| **Stufe 5** (2025, zweiter Weg) | 6–9 Wo (Groq) | **nur wenn 2/3 tragen**, Umfang dann | auf das beschränken, was trägt (steht schon im Plan) | Gemini scheidet für 2025 aus (L-2) |
| **GDELT-Nachweis am NB** | 2 Wo **nach** G8 | 2 Wo **jetzt, parallel** | eigenständige Probe: nur Netzabruf, eigene Datei im Austauschordner, **kein Pull, kein Betriebscode** | berührt den Betrieb nicht |

**Zusammen:** der Gemini-Teil (A1 → Stufe 1 mit Stufe 3 dahinter → Stufe 2) schrumpft von **≈ 4 Wochen auf ≈ 1–1,5 Wochen**. Stufe 5 kostet
nur dann Wochen, wenn es etwas zu bestätigen gibt. Der GDELT-Nachweis ist bis G8 schon gelaufen.

**Töpfe (Schlüssel 2), damit nichts aufeinander wartet:** je Rolle ein eigenes Modell — A1 auf 3.5-flash; Stufe 1 und Stufe 3 / A4 auf
anderen, für Dez. 2025 gemessen sauberen Modellen (3.1-flash-lite, 3.5-flash-lite, 3.6-flash; 3.5-flash nach A1). Die genaue Zuordnung
gehört in die Voranalyse von Stufe 1 und 3 — mit derselben Frage für **live** (Ü8): das Modell einer Rolle muss am NB einen freien Topf
haben (Schlüssel 1; 3.5-flash-lite ist dort der Prüfblock).

## 4. Zur Abstimmung

### 4.1 A1 — auf Gemini umstellen?

| | Weg | Folge |
|---|---|---|
| **a** | **Groq-Lauf anhalten, alle Nachrichten neu auf gemini-3.5-flash** | ≈ 2–3 T statt ≈ 10 T. Die ≈ 65 fertigen Groq-Stapel (≈ 1.600 Nachrichten, Dez. 2025) bleiben als **zweiter Weg**: Übereinstimmung zweier Modelle auf denselben Titeln, ohne Mehrkosten |
| b | Groq-Ergebnisse behalten, nur den Rest auf Gemini | spart einige Stunden, aber der Dezember käme von gpt-oss, der Rest von Gemini — **Modell und Zeitraum wären vermengt** |
| c | Groq weiterlaufen lassen | ≈ 10 T |

**Empfehlung a.** Der Ausschlussgrund für Gemini galt nur für 2025; gemessen liest 3.5-flash mindestens so gut.

### 4.2 Stufe 3 — ein Aufruf je Tag statt je Einstieg?

| | Weg | Folge |
|---|---|---|
| **a** | **bündeln, vorher Gleichheitsprobe**: an den ersten 20 Tagen jeden Einstieg einzeln **und** gebündelt fragen, dazu einzeln ein zweites Mal. Bündel zulässig, wenn Bündel ↔ einzeln **nicht** um mehr als 5 Pp seltener gleich ist als einzeln ↔ einzeln (das Eigenrauschen) | ≈ 322 Aufrufe je Rolle statt 2.379; die Probe kostet ≈ 300 Aufrufe |
| b | einzeln wie live | ≈ 5 + 5 T |

**Empfehlung a.** Live kommt jeder Einstieg einzeln (Ü8) — deshalb nur mit der Probe, nicht ungeprüft.

### 4.3 GDELT-Nachweis am NB — jetzt parallel?

| | Weg | Folge |
|---|---|---|
| **a** | **jetzt**: ein eigenständiges Skript im Austauschordner, das am NB in einem eigenen Fenster 14 Tage lang viermal am Tag die vier Töne abruft und in eine **eigene** Datei im Austauschordner schreibt — kein Pull, kein Betriebscode, nichts in `tradinginfotool.db` | der Nachweis (G7 §9.2) liegt vor, wenn G8 gebaut ist |
| b | wie geplant nach G8 | zwei Wochen mehr auf dem kritischen Weg |

**Empfehlung a.**

### 4.4 Zur Kenntnis — keine Entscheidung

- **Stufe 5 (2025)** bleibt die einzige Groq-Strecke; sie läuft nur für das, was in Stufe 2/3 trägt. Ein weiterer kostenloser Weg mit
  gpt-oss wäre **Cloudflare Workers AI** (10.000 Neurons/Tag [R]); dafür bräuchte es ein Konto, das nur du anlegen kannst — erst prüfen,
  wenn Stufe 5 ansteht.
- **gemini-2.5** fällt weg (L-2); das ist ein Fakt und kein Hebel mehr.

---

## 5. Entschieden (02.11.2026)

**Nutzer:** *„Ok A1 prüfe aber vorher ob einer unserer keys also der ältere gemini 2.5 aufrufen kann, bei 2. der bündelung bin ich
unsicher, entscheide du wenn kein negativer Impakt dann ja bei 3. Bitte um info wie der nb abruf ohne code funktioniert.“*

| | Ergebnis |
|---|---|
| **Vorprüfung gemini-2.5** | **beide** Schlüssel (`GEMINI_API_KEY` = NB-Projekt, `GEMINI_API_KEY_2` = Desktop) bekommen für 2.5-flash, 2.5-flash-lite und 2.5-pro **404 „no longer available to new users“** — über den OpenAI-kompatiblen **und** den nativen Zugang. Kein Weg |
| **§4.1 → a, umgesetzt** | `agent/ereignisse.py`: `MODELL = gemini-3.5-flash`, `SCHLUESSEL = GEMINI_API_KEY_2`; leerer Tagestopf (`PerDay`) wartet je 15 min, sonst `retryDelay`. Groq-Lauf **angehalten** bei Stapel 67/1.009; seine **2.133 Antworten** (25 unlesbar) bleiben unter `openai/gpt-oss-120b` in der Ablage — **zweiter Weg** (Übereinstimmung beider Modelle auf denselben Titeln). Neuer Lauf gestartet 02.11. 11:24 (`data/_a1/a1_volllauf_gemini.txt`), ≈ 1.023 Stapel bei 500/Tag → **≈ 2–2,5 Tage**, danach `--nachfassen` ist im Lauf enthalten. Prüfpakete Ereignisse 15/15, Zustaende 15/15 |
| **§4.2 → a, durch die Probe entschieden** | vom Nutzer an mich übertragen: *„wenn kein negativer Impakt dann ja“*. „Kein negativer Impakt“ ist die **vorab festgelegte Gleichheitsprobe**: Bündel nur, wenn Bündel ↔ einzeln höchstens 5 Pp seltener gleich ist als einzeln ↔ einzeln. Fällt sie durch, läuft Stufe 3 **einzeln** — ohne neue Rückfrage |
| **§4.3 → a** | Nutzer 02.11. abends: *„ja, Skript bauen – prüfen, gegenprüfen und doku“* → gebaut, §7 |

---

## 6. ⚠️ Korrektur nach der Gegenprüfung (02.11. nachmittags, Nutzer: *„Ok prüfen und gegenprüfen“*)

**Befund L-1 war falsch.** Der Lauf auf gemini-3.5-flash stand nach ≈ 20 Aufrufen still. Der Fehlerkörper sagt:
`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, **`quotaValue 20`**. Die „500 je Modell“ aus der Dashboard-Voranalyse §1.5a waren
am 09.08. für die **flash-lite**-Modelle gemessen; ich habe sie ohne Prüfung auf alle Flash-Modelle übertragen. Mit 20/Tag hätte A1
≈ 50 Tage gebraucht. Der Lauf ist angehalten; seine 148 Antworten bleiben unter `gemini-3.5-flash` in der Ablage und werden nicht verwendet.

| Gegenprüfung | Ergebnis |
|---|---|
| Tagesgrenze 3.5-flash (Schlüssel 2) | **20** (Fehlerkörper) |
| Tagesgrenze 3.5-flash-lite (Schlüssel 2) | **≥ 480 belegt**: N4-Lauf 05.–07.10. je 479–480 gültige Antworten am Tag (Deckel des Skripts) |
| weitere Kandidaten, dieselbe Regel vorab, dieselben 60 Titel | **3.5-flash-lite TAUGT** (Typ 82 %, Sicht relevant **93 %**, Fehlalarm/Verlust **3 / 1**, Wiederholung 95 %) · 3.1-flash-lite taugt (78 %, 88 %, 3 / 4, 100 %) · gemma-4-31b: Fehler 400/500 über die Schnittstelle, nicht prüfbar |
| gemini-2.5 | für beide Schlüssel gesperrt (§5) |

**Umgesetzt:** A1 läuft seit 02.11. ≈ 12:50 auf **gemini-3.5-flash-lite** (`agent/ereignisse.MODELL`, Log `data/_a1/a1_volllauf_gemini_lite.txt`).
≈ 1.023 Stapel bei ≈ 500/Tag (Rücksetzen 09:00 MEZ) → **≈ 2–2,5 Tage**.

**Folge für §3 (Töpfe):** am Schlüssel 2 tragen nur die **flash-lite**-Modelle (3.1, 3.5) große Läufe; die vollen Flash-Modelle sind mit
≈ 20/Tag nur für Stichproben brauchbar (Grenzen von 3.6/3.7/3.8/3-flash-preview **ungemessen** — nicht annehmen). Stufe 1 (≈ 2.010 Aufrufe)
und Stufe 3 (gebündelt ≈ 322 je Rolle) müssen sich damit **zwei** 500er-Töpfe teilen, solange A1 einen belegt → Stufe 1 ≈ 4 T nach A1,
oder ≈ 2 T, wenn beide flash-lite-Töpfe genommen werden (dann Modell je Sicht fest, nicht gemischt). Das gehört in die Voranalyse Stufe 1.
Der kritische Weg wird damit ≈ **1,5–2 Wochen** statt ≈ 1–1,5 (§3) — immer noch weit unter ≈ 4 Wochen.

**Lehre:** eine Grenze, die für **ein** Modell gemessen ist, gilt nicht für ein anderes — vor jedem großen Lauf die Grenze **des Modells**
belegen (Fehlerkörper oder eigener früherer Lauf), nie aus einer Tabelle übertragen.

### 6.1 Gegenprüfung im laufenden Betrieb des Laufs — Börsentitel

Die ersten 610 Antworten auf flash-lite hatten **73 unlesbar (12 %)** — alle im **Börsen-Rest** (Upbit 23/23, Binance 50/337; Nachrichten
0/250). flash-lite erfand Typen (`delisting_spot`, `net_upgrade`); `nachfassen` fragt diese Stapel am Ende kleiner neu. Weil Stichprobe 3
**nur Nachrichten** enthielt, zwei Gegenproben:

| | Ergebnis |
|---|---|
| **Übereinstimmung beider Modelle** auf denselben Titeln (lesbar) | Nachrichten 250: Sicht relevant gleich **84 %** (nur Gemini 24, nur gpt-oss 16) · Binance-Rest 337: **83 %** (nur Gemini 40, nur gpt-oss 18). Bei ≈ 90 % Treffer je Modell sind ≈ 82 % Übereinstimmung zu erwarten |
| **Hand gegen beide Modelle**, Stichprobe 1 (Börsentitel, Hand festgeschrieben), Prompt 3; Regel vorab: flash-lite taugt, wenn Fehlalarm und Verlust höchstens +1 gegen gpt-oss | binance_rest (30): gpt-oss **73 %**, Fehlalarm/Verlust 3/5 · flash-lite **83 %**, 3/2 · Upbit (30): beide 100 % · regelbasierte Binance (50): gpt-oss 82 %, flash-lite **96 %** · flash-lite Wiederholung 96 %, 0 unlesbar → **TAUGT** |

→ Das häufigere „relevant“ von Gemini auf dem Binance-Rest sind eher **Verluste von gpt-oss** als Fehlalarme von Gemini. Skript:
`zeit_voranalyse.py b` / `rb` → `zeit_voranalyse_rb.txt`.

---

## 7. §4.3 umgesetzt — GDELT-Probe am NB gebaut, geprüft, gegengeprüft (02.11.2026 abends)

**Nutzer 02.11.:** *„ja, Skript bauen – prüfen, gegenprüfen und doku“*. Der Betrieb ist unberührt: kein Pull, kein Betriebscode.

### 7.1 Was gebaut ist

| Datei | Zweck |
|---|---|
| `Rechenkern_02_10/gdelt_probe_nb.py` → Austauschordner `GDELT_Probe/gdelt_probe.py` | **die Probe**: nur Standardbibliothek, kein Import aus dem Projekt; schreibt **nur** `gdelt_probe_<Rechner>.jsonl` daneben (je Abfrage eine Zeile, sofort auf der Platte, Rohpunkte mit Uhrzeit). Runden: beim Start, dann 00:30/06:30/12:30/18:30 UTC; Abfragen, 600 s Abstand (jetzt auch **über** Runden), zweiter Versuch nach 120 s, Fenster 14 T bis heute 00:00 UTC — wie `sichten_quellen --laufend`. Neustart setzt fort, Ende nach 14 Tagen von selbst |
| `gdelt_probe_LIESMICH.txt` → `GDELT_Probe/LIESMICH.txt` | Anleitung für den Start am NB (`C:\Python313\python.exe "G:\Meine Ablage\Claude_Austauschordner\GDELT_Probe\gdelt_probe.py"`) |
| `gdelt_probe_auswertung.py` | Desktop, liest nur. **Vorab festgelegt** (im Kopf, vor jedem Probewert): **K1** je Ton fehlt der Tageswert 24 h nach Tagesende an ≤ 10 % der Tage · **K2** Klasse des Zustands (Tageswert und 7-T-Mittel, `zustaende.klasse`) live = Rückspiel an ≥ 90 % der Ton-Tage je Maß; live = Stand 07:00 UTC des Folgetags, wie `INSERT OR REPLACE` ihn hätte · **K3** Tagesauflösung in jedem Abruf. Hält es nicht → **c** neu vorlegen (G7 §9.2). Auskunft: Verzug, **Revision** (GDELT ändert Tageswerte nachträglich? — das Rückspiel nimmt den späten Wert mit `bekannt_ab` = Folgetag; wäre das ein Vorgriff, zeigt es sich hier), Fensterprobe 14-T- gegen Jahresfenster. `--rueckspiel` holt nach dem Probeende über `sichten_quellen.gdelt_ton` (derselbe Weg wie die Historie) und **verweigert sich vorher** |
| `gdelt_probe_pruefung.py` → `gdelt_probe_pruefung.txt` | **40/40 grün**, ohne Netz |
| NB-Kontrolle **K-GD-1** | `nb_kontrollen.yaml`, fällig 20.11. |

### 7.2 Prüfung (40/40)

| | |
|---|---|
| P1 eigenständig | nur Standardbibliothek (AST); verweigert `tradinginfotool*` und Nicht-`.jsonl`; Vorgabe = eigene Datei neben dem Skript |
| P2 = Quelltext | 9 Merkmale **aus dem Quelltext** von `sichten_quellen` abgeleitet (Regex auf `_gdelt_fenster`), nicht abgeschrieben; 4 Mutationen (Abstand, Abfrage, Pause, Fenster) je genau ein Merkmal rot |
| P3 Zeitplan | Startrunde, keine Doppelung, verschlafene Runde → nur die jüngste nachgeholt, 56 Runden in 14 T |
| P4 eine Runde | Sperre, Sperre zweimal, Netzfehler, 200 ohne JSON (gilt als Fehler, nie als leere Reihe); Wartezeiten genau 600/120; **Abstand über Runden** (500 s Rest) |
| P5/P6 14 Tage mit Absturz | Neustart nach 11 h Ausfall: Startzeit bleibt, genau die verschlafene Runde fehlt und wird von der Auswertung gezählt; endet von selbst; **einzige neue Datei = die eigene `.jsonl`** |
| P7 Auswertung gegen bekannte Wahrheit | saubere Welt → HÄLT (13 Live-Tage, Verzug ≤ 1 h, K2 52/52) · Sperre 30 h → genau 1 Lücke, K1 noch grün · 60 h → 2 Lücken, rot · gepflanzte Revision genau gefunden (1 Ton-Tag, 3,0) · Rückspiel +4 → K2 rot · eine Stundenauflösung → K3 rot · ohne Rückspiel → **offen, nicht grün** |

Bei der Prüfung gefunden und behoben: (1) eine Runde, die in die nächste Rundenzeit läuft, hätte **ohne** 600 s Abstand weitergefragt; (2) im
Klassenvergleich hätte die Historie eine **Lücke der Probe aufgefüllt** und versteckt — sie zählt jetzt nur vor dem ersten Probetag; (3) die
Auswertung meldete ohne einen einzigen erfolgreichen Abruf „K3 NICHT erfüllt“ statt „noch kein Abruf mit Werten“.

### 7.3 Gegenprüfung im echten Netz — die Desktop-Adresse ist gesperrt

Eine echte Runde mit **dem NB-Skript** (`--einmal`, Wegwerfdatei; `gdelt_probe_gegenprobe_desktop*.txt`):

| | |
|---|---|
| Ergebnis | **8 von 8 Abfragen HTTP 429** (je Ton beide Versuche), 17:02–17:41 UTC |
| Vorgeschichte | letzte GDELT-Abfrage vom Desktop **01.11. 16:34 UTC** — die Sperre hält also **über 24 h ohne jede neue Anfrage** |
| Mechanik | richtig: Abstände 600/120 s, jede Abfrage protokolliert, Auswertung läuft auf einer Datei aus lauter Sperren durch, Prüfsumme der Kopie im Austauschordner = geprüfte Fassung (`75caf5849b327086`) |
| **nicht** belegt | der **Erfolgsweg im echten Netz** (Zerlegung einer echten Antwort mit `urllib`) — nur gegen nachgebaute Antworten im Format, das der Desktop-Abrufer bis 01.11. verarbeitet hat. → nach der **ersten NB-Runde** liest der Desktop die Datei (Austauschordner) und prüft genau das |
| bewusst unterlassen | ein Abruf mit fremder Browser-Kennung, um Adresse von Kennung zu trennen — das wäre ein Umgehen der Sperre. Die Probe fragt mit der Kennung, die auch der Betrieb hätte |

**Was das für die Entscheidung heißt:** Ist das NB hinter **derselben** öffentlichen Adresse wie der Desktop, wird die Probe vermutlich
ebenfalls gesperrt — dann ist K1 rot, und das ist ein **echtes** Ergebnis: GDELT wäre im Betrieb nicht verlässlich (→ c neu vorlegen, oder
GKG-Rohdateien, G4). Die Sperrmeldung nennt selbst einen Ansprechpartner bei GDELT; eine Anfrage dort könnte nur der Nutzer stellen.

### 7.4 Offen für G8 (nicht Teil der Probe)

`sichten_quellen.lade` setzt GDELT **ab dem letzten vorhandenen Tag** fort — im laufenden Betrieb ein Fenster von 1–2 Tagen. GDELT liefert
für kurze Fenster vermutlich **Viertelstunden- statt Tageswerte**; `_gdelt_fenster` nähme dann je Tag den **letzten** Viertelstundenwert
(Wörterbuch überschreibt). **Ungeprüft** (heute gesperrt) — die Probe fragt bewusst das 14-T-Fenster, das Tageswerte liefert. Vor dem
Bau G8 mit einem Abruf klären; bis dahin ist es eine Vermutung.

### 7.5 Probe am NB gestartet (02.11. 18:07 UTC) — erste Runde, und die Trennung der Lückenursache

**Nutzer:** *„Ok, Probe am NB ist gestartet“* · *„Ok, bau die Trennung gesperrt/Quelle fehlt ein“*.

| | |
|---|---|
| NB kommt durch | Rechner T440, Python 3.13.14, Prüfsumme `75caf5849b327086` (= geprüfte Fassung). Erster Versuch je Ton oft 429, der **zweite nach 120 s erfolgreich** — anders als der Desktop (8/8 gesperrt) |
| Erfolgsweg belegt | echte Antwort, Tagesauflösung (K3), **Fensterprobe 18 von 18 Werten bitgleich** mit der Historie (14-T-Fenster = Jahresfenster) |
| ⚠ **Quelle endet am 27.10.** | das Fenster reicht bis 01.11., GDELT liefert nur bis **27.10.** — wie schon beim Historienladen am 01.11. Vermutlich ein **Ausfall bei GDELT** seit dem 28.10., nicht belegt. Hält er an, wird K1 rot — zu Recht: im Betrieb fehlt der Wert so oder so |

**Gebaut (Auswertung, nur Auskunft — K1 zählt alle Lücken gleich):** je Lücke die Ursache aus den Versuchen in der 24-h-Frist —
**gesperrt** (versucht, keiner erfolgreich: 429, Netzfehler, Unsinn) · **Quelle fehlt** (mindestens ein Abruf erfolgreich, der Tag war nicht
darin) · **kein Abruf** (gar kein Versuch, Rechner aus). Prüfung **44/44** (neu: Sperre → 2 × gesperrt; GDELT ohne 3 Tage → 3 × Quelle fehlt,
andere Töne frei; Rechner 36 h aus → 1 × kein Abruf bei allen Tönen; saubere Welt ohne Ursache).

---

## 8. A1 fertig, zweiter Weg gerechnet (04.11.2026, Nutzer: *„Entscheide du wähle die sinnvollste Variante“*)

**Lauf:** am 04.11. 08:05 wieder aufgenommen. 1.009/1.009 Stapel durch, Nachfassen 498 → **2 unlesbar**, **25.561 Ereignisse** in
`data/_sichten/sichten.db` (letzte Schreibung 09:36:40, danach nur lesend). Prompt `7b94d07d7d1d` unverändert, Fehlerdatei leer.
Stehen geblieben war der Lauf am 03.11. bei 898/1.009, weil der Tagestopf leer war (02.11. 432, 03.11. 479 Aufrufe). Dass er beim
App-Neustart am 03.11. um 22:16 endete, ist erschlossen, nicht belegt.

**Zweiter Weg:** gpt-oss-120b (Groq) gegen flash-lite auf denselben Titeln, nur lesend, ohne Netz.
Skript `Rechenkern_02_10/a1_zweiter_weg.py`, Ausgabe `a1_zweiter_weg.txt`. „Relevant“ heißt: Ereignistyp und eine Sicht, gerechnet wie
`llm_ereignisse` (Assets gegen Universum und Alias).

| | Titel | Relevanz gleich | nur flash-lite | nur gpt-oss | beide relevant: Sicht / Assets gleich |
|---|---|---|---|---|---|
| **Nachbildung 02.11.**, erste 250 Nachrichten | 225 | **84,4 %** (02.11.: 84 %) | 23 (24) | 12 (16) | 90,5 / 96,8 % |
| **Nachbildung 02.11.**, Binance-Rest | 337 | **81,9 %** (02.11.: 83 %) | 42 (40) | 19 (18) | 92,3 / 92,3 % |
| Vorfilter-Nachrichten, alle | 1.650 | 78,5 % | 223 | 132 | 88,8 / 93,0 % |
| Upbit | 23 | 65,2 % | 8 | 0 | 100 / 80 % |
| **Alle gemeinsamen** | **2.010** | **78,9 %** | **273** | **151** | 89,4 / 92,8 % |

⚠️ **Nur nachgebildet.** Die Rechnung vom 02.11. ist nicht aufbewahrt. Die Nachbildung trifft sie bis auf wenige Titel; beim Rest der
Binance-Titel ändert das Nachfassen seither einige Antworten.

**Was daraus folgt:**
1. Auf dem vollen Überschnitt sind es **78,9 %**, also etwas **unter** den ≈ 82 %, die bei ≈ 90 % Treffer je Modell zu erwarten sind
   (das entspricht ≈ 88 % je Modell). Der Abstand stammt aus den Nachrichten nach den ersten 250 (78 % statt 84 %).
2. flash-lite meldet **häufiger „relevant“** (273 gegen 151). Auf den Börsentiteln sind das nach der Handprüfung vom 02.11. (§6.1) eher
   **Verluste von gpt-oss**. Für die Nachrichten ist das **nicht** von Hand geprüft.
3. Wenn beide Modelle „relevant“ sagen, stimmen Sicht (89 %) und Assets (93 %) meist überein. Der Unterschied liegt im **Ob**, nicht im **Was**.
4. ⚠️⚠️ **Der zweite Weg deckt nur 8 % von A1 ab** (2.010 von 25.563). Die **21.670 übrigen Nachrichten (Weg b)** hat gpt-oss nie
   gelesen. flash-lite stuft dort **26 %** als relevant ein (5.562), auf den Vorfilter-Treffern 52 %. Für Weg b gibt es nur die Handprüfung
   auf Stichprobe 3 (§6). Ein zweites Modell hat ihn nicht gelesen.

**Urteil:** A1 ist **benutzbar für Stufe 1**. Die Übereinstimmung liegt in der erwarteten Größenordnung, und die Unterschiede liegen beim
„Ob“, wo die Handprüfung flash-lite den Vorzug gibt. **Nicht belegt** ist der Fehlalarm auf Weg b über Stichprobe 3 hinaus. Stufe 1 muss
deshalb Weg b getrennt ausweisen (Vorfilter-Treffer gegen übrige Nachrichten). Trägt eine Sicht nur auf Weg b, ist sie vorher an einer
Handstichprobe der übrigen Nachrichten zu prüfen.
