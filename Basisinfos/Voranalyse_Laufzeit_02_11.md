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
| **§4.3** | Erklärung an den Nutzer, Entscheidung offen (s. Gesprächsverlauf 02.11.) |
