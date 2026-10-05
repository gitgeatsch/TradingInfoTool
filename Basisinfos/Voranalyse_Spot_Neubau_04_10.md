# Voranalyse Spot-Neubau — die Grundlage aus fachlicher und technischer Sicht

**04.10.2026** · E-54, Plan Hebel **O23** (dazu O14, O19, O24) · Nutzer: *„Ich würde gerne den Spot-Ast neu umbauen, analog dem Hebelablauf“* — *„vorerst nur eine Voranalyse und Analyse, damit wir die Grundlage aus fachlicher und technischer Sicht haben“*.

> ▶ **05.10.2026: M-0 Machbarkeit gestartet, parallel zum Hebel und sauber getrennt (E-59, §7).** Vorher:
> ⏸⏸ **ANGEHALTEN am 04.10.2026 (Nutzer, E-55):** *„So, wir machen nun Halt bei Spot. Notiere alles bisher Vorgeschlagene in den jeweiligen Dokumentationen und im Plan, mit dem Hinweis, dass eine Totalüberarbeitung, die Machbarkeit und die offenen Punkte behandelt werden müssen. Zuerst kümmern wir uns darum, dass die Hebelfunktion – E-Mails und LLM – sauber funktioniert.“*
> Damit gilt: Alles hier Vorgeschlagene (S-a bis S-d, Messreihe M-1 bis M-5, die Nebenbefunde) ist **notiert, nicht abgestimmt**.
> Vor einer Wiederaufnahme sind drei Dinge zu behandeln: **(1) Totalüberarbeitung** – der Spot-Ast wird nicht ausgebessert, sondern
> neu gedacht (Ist-Kette §1 zeigt: das Urteil liegt beim LLM, die Regel fehlt). **(2) Machbarkeit** – ob ein Spot-Pfad mit unseren
> Daten überhaupt nachweisbar trägt (§2.2: das *Ob* entscheidet, §4.3: auf 90 Tagen nur ~11 unabhängige Fenster und 2–4
> Regimewechsel ab 2024). **(3) Die offenen Punkte** – §5 und die Liste in Plan O23.
>
> **Rahmen:** nur lesend. Keine Betriebsänderung, NB-Daten nur als Kopie (`nb_0310.db`, Sicherung 03.10. 05:20), Standard-DB `mode=ro`. Die alte Spot-Kette läuft **unverändert** weiter; wann ihre LLM-Aufrufe gestoppt werden, regelt O24. Belege: `Basisinfos/Spot_Voranalyse_04_10/`.

---

## 0. Zwischenfazit zum Ziel — vorab

| | |
|---|---|
| **Ziel** | je Asset eine neutrale, begründete Aussage über das **Potential** — für Spot auf **längerem** Horizont (Nutzer: *Hebel kurzfristig, Spot längerfristig*) |
| **Was die alte Kette tut** | Das **LLM** (Rolle BC) entscheidet KAUFEN/NACHKAUFEN, gestützt auf einen Faktentext, der den Bestand *im Plus/Minus* nennt. Ein deterministisches Potential aus `funding` und `turnover` (Altbestand H20) lässt durch oder sperrt. **Eine Regel für NACHKAUFEN gibt es nicht** (§1) |
| **Was gemessen ist (§2)** | Die Live-Signale (Juli bis Oktober 2026) wählen den Zeitpunkt **nicht besser als Zufall** (gegen dieselben Assets zur selben Stunde +0,4 %, null eingeschlossen). Die Kaufregel *unter dem 200-Tage-Schnitt* hat 2025 und 2026 in **73–74 %** der Fälle weiter verloren (−23 % bzw. −17 % in 90 Tagen) und keinen Boden gefunden. **Deine Beobachtung vom 25.09. ist damit gemessen** |
| ⭐ **Der Kern** | Das Problem ist nicht, **welches** Asset gekauft wird, sondern **ob**. 2025/26 hat **jeder** Kauf verloren, auch ein zufälliger (−17 % bis −27 % in 90 Tagen). Gegen die anderen Assets ist die Auswahl fast Zufall. Ein Spot-Neubau, der die **Frage nach dem Ob** nicht beantwortet oder ausdrücklich dir überlässt, wiederholt den Fehler |
| **Was NICHT folgt** | Dass Spot unmöglich ist. 2024 trug *unter dem Schnitt* (+2,4 %, bei −30 % sogar +20 % in 90 Tagen). Es ist **regimeabhängig** — genau das, was 2.598/2.599 für den Hebel gemessen haben |

---

## 1. V-1 Ist-Kette Spot — wer rechnet, urteilt, schreibt, liest

**Takt:** Job `hebel_screening` (Name historisch), alle 15 min → `fuehre_umlauf` → je Gruppe `fuehre_bereich` → `rollen_lauf.fuehre_lauf` (`scheduler/background.py:4352`, `scheduler/rollen_job.py:402/447`, `agent/rollen_lauf.py:275`). Alle fünf Gruppen sind umgestellt (`config.yaml` `rollen_kette.aktiv_fuer`, `betriebsart: scharf`); der alte Budget-Allocator ist aus.

**Ein Spot-Signal entsteht so** (`rollen_lauf._ein_asset`, :1284; Trichter `rollen_gate.py:67`):

| Stufe | wer | was |
|---|---|---|
| Fakten, Schalter, Anlass | deterministisch | `rollen_eingabe.baue_fall`, Nutzerschalter, gleicher Fakten-Fingerabdruck sperrt |
| Auswahl | deterministisch | `auswahl.waehle` k = 2 nach 250-Tage-Entwicklung; **Bestand kommt immer durch** |
| Terminmarkt, Cooldown | deterministisch | `oi_fuenftel ≥ 4` sperrt (nur ohne Bestand), Cooldown je Strategie (Krypto 12 h) |
| Lagebild | **LLM Rolle A** | höchstens alle 3 h |
| ⭐ **Urteil** | **LLM Rolle BC** | KAUFEN / NACHKAUFEN / REDUZIEREN / VERKAUFEN / NICHTS_TUN (`rolle_trader.py:158`) |
| Geometrie | deterministisch | Stop ≥ 2,0 ATR, Verlustanteil 6 %, Beträge, Töpfe |
| Entscheider („Stufe 11“) | deterministisch | `potential.rechne` → `wahrscheinlichkeit`: Basisrate + Zuschlag aus **funding**- und **turnover**-Fünftel (`wahrscheinlichkeit.py:406/454`), Schwelle 0,060 R; `schnitt` trägt nichts bei |
| Gegenprüfung | **LLM Rolle G** (Z.ai) | nur Terminmarkt-Positionierung, nachgelagert |
| Mail | | Einstiegsmail je Signal; Verkäufe in die **Sammelmail** je Lauf |

⚠️ **NACHKAUFEN entscheidet allein das LLM** — anhand des Satzes *„X ist im Bestand … im Plus/Minus (…%)“* (`lagebeschreibung.py:107`). Das ist **Regel 4** (*ein Fakt ist keine Begründung*) in der Form, die wir verboten haben. Danach gilt dieselbe Potentialschwelle wie für KAUFEN, aber Auswahl- und Terminmarktsperre entfallen beim Bestand.

**Akkumulation:** Zellen `einstieg` und `akkumulation` für die DCA-Assets (BTC/ETH/SOL) existieren. Die Akkumulationszelle fällt immer an `lage_gesperrt` (kein Beitrag mit `strategien=("akkumulation",)`), die taktische Zelle an der Geometrie (kein Hebel, seit S7-4 immer). **Ergebnis: null Akkumulations-Kaufsignale** (wie 2.540). ⚠️ Möglicher Doppelverbuchungsfehler: beide Zellen können denselben VERKAUFEN-Befund zweimal in die Sammelmail geben (aus dem Code, nicht nachgewiesen).

**Bestand und Führung:**

| | Takt | |
|---|---|---|
| Verkaufs-/Bestands-Sammelmail | je Lauf (15 min) | `verkaufsrechnung.sammel_mail`, innerhalb der Kette |
| Hebelführung **echter** Positionen | je Lauf | `hebelfuehrung.sammel_mail`, **innerhalb der Kette** (`rollen_lauf.py:981`) |
| Stop-Nachzieh-Sammelmail | 07:15 | `ausstiegs_job`, **unabhängig** von der Kette; Trailing +1,0 R / 1,0 R (Altbestand 04.08.). ⚠️ zieht auch für **Spot** Stops nach, obwohl *Spot hat keinen Stop* entschieden ist (`verkaufsrechnung.py:27`) — Teil von O19 |
| Backward-Tracking | 06:00 | Ausgänge in `signals`/`hebel_signals` |

**LLM:** Rolle A und BC über die Kette gemini-3.1 → **gemini-3.5** → OpenRouter → Groq (`rollen_job.py:206`), Wechsel bei 90 %. Rolle G über Z.ai. **Der REGEL0-Prüfblock nutzt denselben Client auf gemini-3.5** — beide teilen den Topf, sobald 3.1 erschöpft ist (O24).

**Der Schalter `spot_kette_angehalten` (R-4)** wird **je Umlauf** gelesen, wirkt also ab dem nächsten 15-min-Takt. Er hält an: Rollen A/BC/G aller Gruppen, Einstiegs- und Verkaufs-Sammelmails, **auch die Hebelführungs-Mail echter Hebelpositionen**. Er hält **nicht** an: Bitpanda-Abgleich, Stop-Nachzieh-Mail 07:15, Backward-Tracking, Marktscan-Mails, REGEL0 samt Prüfblock.

⚠️⚠️ **Für eine spätere Stilllegung:** Die REGEL0 hängt am Code der Kette — `regel0_llm` importiert `rollen_eingabe`, `lagebeschreibung`, `marktlage`, `gegenpruefer_rollen` (`agent/regel0_llm.py:155/235/373`). **Wer diese Module stilllegt, bricht die REGEL0.** Tabellen, die nur die Kette schreibt und nur Diagnose liest: `lagebilder`, `gate_durchlaessigkeit`, `zellen_lauf`, `auswahl_schatten`, `anlass_beobachtung`, `vorfilter_schatten`. `signals` hat viele Leser (UI-Tabs, Hebel-Tab, 07:15-Job, Trefferbilanz, Töpfe, Diagnose).

---

## 2. V-2 Kauft Spot in den Verlust nach? — gemessen

### 2.1 Die Live-Signale (`v2_nachkauf_messen.py`, Beleg `.txt`)

868 Kaufsignale (KAUFEN, NACHKAUFEN, ERÖFFNEN; Krypto; erstes je Symbol, Aktion und Tag) an 40 Assets, **14.07. bis 03.10.2026** — ältere Spot-Signale gibt es nicht. Einstieg zum Schlusskurs der Folgestunde.

| | 7 Tage | 14 Tage | 28 Tage |
|---|---|---|---|
| roh (Median) | +5,0 % | +5,3 % | +10,9 % |
| ⭐ gegen **dieselben Watchlist-Assets zur selben Stunde** | **+0,4 %** | **+0,4 %** | |
| unabhängig gezählt (Symbol-Wochen) | +0,50 % ± 0,56 (162) | +0,55 % ± 0,84 (144) | |
| Lage im 15-Tage-Bereich (0 Boden; Zufall 0,42) | Median **0,36** | | |

➤ **Kein Nachteil, kein Vorteil.** Die Rohwerte kommen aus dem steigenden Markt August/September. NACHKAUFEN liegt bei 0,39 — praktisch Zufall. ⚠️ Ein Regime, drei Monate: das sagt nichts über einen fallenden Markt.

### 2.2 Das Rückspiel *unter dem 200-Tage-Schnitt* 2024–2026 (`v2b_unter_schnitt_rueckspiel.py`)

Die Messbasis (116 Assets, eingestellte eingeschlossen), Tageskurse, ohne LLM. *unter dem Schnitt* ist das Akkumulationsmaß (`schnitt`/`UNTER_SMA`) und die einzige deterministische „Nachkauf“-Regel im Haus.

| Kauf, 90 Tage danach | 2024 | 2025 | 2026 |
|---|---|---|---|
| **jeder Tag** (Zufallskauf) | −11,6 %, 61 % im Minus | **−27,2 %, 77 %** | **−17,0 %, 73 %** |
| **unter dem Schnitt** | +2,4 %, 48 % | **−23,2 %, 74 %** | **−16,5 %, 73 %** |
| **30 % darunter** | +20,4 %, 30 % | −17,8 %, 69 % | −15,1 %, 70 % |
| **50 % darunter** | +32,1 %, 17 % | −18,0 %, 65 % | −9,1 %, 63 % |
| **30 % darüber** | −32,7 %, 80 % | −46,3 %, 97 % | −25,2 %, 85 % |
| Rang gegen die anderen Assets desselben Tages, *unter* minus *jeder Tag* | 30 T +0,02 · 90 T ±0 | 30 T +0,01 · 90 T ±0 | 30 T +0,01 · 90 T +0,01 |
| Lage (0 = Boden), *unter* gegen *jeder Tag* | 0,32 gegen 0,39 | 0,36 gegen 0,40 | 0,36 gegen 0,37 |

BTC unter dem Schnitt, 90 Tage: 2024 +55 %, **2025 −20 % (64 % im Minus)**, **2026 −10 % (64 %)**.

**Was gemessen ist:**
1. ✔ **Deine Beobachtung trifft zu — absolut.** 2025 und 2026 hat ein Kauf unter dem Schnitt in drei von vier Fällen weiter verloren, auch tief darunter.
2. **Einen Boden findet die Regel nicht.** Die Lage ist kaum tiefer als zufällig.
3. **Gegen die anderen Assets** wählt sie auf 30 Tage etwas besser, auf 90 Tage nicht.
4. ✔ **Die Ausschlussseite hält:** *weit darüber* ist 2025/26 schlechter (2026 Rang 0,31, deutlich). Als **Sperre** trägt der Schnitt, als **Kaufsignal** nicht.
5. ⭐ **Die Frage nach dem Ob entscheidet:** Der Zufallskauf verlor 2025/26 genauso. Das ist das Regime (Faktor 12, 2.598) — und es ist **nicht vorab erkennbar** (2.599).

⚠️ Vorbehalte: Tagesrang auf Asset-Monaten (überlappende 90-Tage-Fenster, der Standardfehler ist eher zu klein). Ab 2024 gemessen (Messfokus). 2026 reicht nur bis Ende Juni (90 Tage vor Datenende). Es ist ein **Rückspiel einer Einzelregel**, nicht der Kette.

---

## 3. V-3 Die Wette — was Spot sein soll

Spot ist **nicht ein** Geschäft, sondern drei Pfade (E-43: gemeinsam prüfen, je Strategie eigener Pfad):

| Pfad | Frage | Horizont | Stand |
|---|---|---|---|
| **S-E Einstieg** | Wann und welches Asset kaufen? | Tage bis Wochen | alte Kette ≈ Zufall (§2.1) |
| **S-A Akkumulation** | Bestand über Monate aufbauen — wann innerhalb? | Monate (H90) | Maß *schnitt* trägt nur als Sperre (§2.2); null Signale im Betrieb |
| **S-B Bestand und Ausstieg** | Halten, reduzieren, verkaufen? | laufend | Trailing Altbestand, Spot-Stop widersprüchlich (O19) |

**Die Frage nach dem Ob liegt quer über allen dreien** und ist die eigentliche Entscheidung (§5, S-b).

Wörtlich der Maßstab vom 23.09.: *„Spot ist als eigenes größeres fachliches Thema zu behandeln. Warum: ohne sinnvolle Strategie als **langfristiges Investment** kommen die Signale ohne Sinn und Ziel (Kauf und Verkauf).“*

---

## 4. V-4 und V-5 Was trägt, was kostet, was ist messbar

### 4.1 Befundlage (Recherche, Fundstellen in REGISTER_* und Befunden)

⚠️ Alle Spot-Messungen vor dem Hebelneubau gelten **nur als Vergleich, nicht als Grundlage** (Nutzer 26.09.). Die Rohgrößen sind frei, die Stufen gesperrt (E-3, E-8).

| Merkmal | Befund | für den Neubau |
|---|---|---|
| **turnover** | H20 +0,0616 R, trägt (2.535/2.537); Akkumulation H90 +0,035 unter Vorbehalt | Kandidat (Querschnitt), **ab 2024 neu messen** |
| **funding** | H20 +0,0246 R, kippt in Saaten; Akkumulation **umgekehrt** (2.287) | Kandidat mit Vorbehalt |
| **schnitt** | Akkumulation +0,047 (Permutation, 2.286), als Sperre +0,040 (2.159); als Einstieg Auswahlartefakt (2.222) | ✔ **Sperre**, bestätigt in §2.2 |
| **oi_aenderung** | ohne gesperrtes Fünftel null (2.576); Akkumulation umgekehrt | Sperre prüfen |
| **REGEL0-Kern als Spot 1x** | Wahl 2024: 72 h +0,218, besser als jeder Hebel (2.690); 2025/26 nur 24 h gemessen (+0,02..+0,03) | ⭐ **L3 nie gemessen** — der billigste Kandidat, die Betriebstechnik steht |
| rsi, momentum, vola u. a. | auf H20 ✖ oder Auswahl | nicht neu aufnehmen ohne Grund |
| ema_abstand, Käuferanteil | nur Hebel | für Spot nie gemessen |

### 4.2 Kosten Bitpanda Spot — **nicht belegt**

Im Umlauf sind 0,30 %, 1,0 % (`_KOSTEN_SPOT_JE_SEITE` im Code), 1,03 % (Median `vsn_fee`, nur 348 von 3.578 Trades) und 1,50 % je Seite (Brokerspread, Betriebssatz). Der Spread ist **nie gemessen**. Bei einem Rohvorteil von wenigen Zehntelprozent entscheidet der Satz über jede Erfolgsmessung. ➤ **Fachlich lösbar:** aus dem echten Bitpanda-Buch (`Notebook_Analysedaten/bitpanda_transaktionen.json`) den Ausführungskurs gegen den Binance-Kurs derselben Stunde halten. Regel 2 bleibt: Kosten nur in der **Erfolgsmessung**, nie in der Bewertung.

### 4.3 Datenlage, Grundgesamtheit, Fallzahl

| | |
|---|---|
| Daten am NB | ✔ Stundenkurse aller Binance-Assets laufend (`regel0_nachlader`), Messbasis-Kopie — für S-E und S-A reicht das (E-35). Funding/turnover am NB nur Symbolliste, Werte live |
| Grundgesamtheit | dieselbe wie die REGEL0 (unverzerrt, eingestellte eingeschlossen, E-30) — nie beiläufig ändern |
| **Fallzahl ab 2024** (unabhängige Fenster je Asset) | 24 h ~1.000 · 72 h ~330 · 20 Tage ~50 · **90 Tage ~11** — und nur **2–4 Regimewechsel** |
| Folge | Auf langen Horizonten ist nur die **Querschnittsfrage** (welches Asset, Tagesrang/Permutation) messbar. Die **Niveaufrage** (überhaupt kaufen?) ist mit unseren Daten **kaum entscheidbar** — das ist ein Fakt über die Daten, kein Urteil |

---

## 5. V-6 Zur Abstimmung — nur was bei dir liegt

Fachlich beantwortet und **keine** Frage an dich: der Horizont wird als **Achse** gemessen (24 h, 72 h, 120 h, 20 Tage, 90 Tage), nicht gesetzt. Gewählt wird auf 2024, bestätigt auf 2025/26 in vier Mengen, gegen die tagestreue Nullwelt, je Asset, mit Spiegel. Gemessen wird mit dem **Tagesrang** statt mit Mitteln (die Mittel sind hier von der rechten Schiefe verzerrt, §2.2). Der Kostensatz wird aus dem Buch **gemessen** (§4.2).

| # | Frage | Vorschlag |
|---|---|---|
| **S-a** | **Was soll Spot für dich sein?** (a) aktiver Spot-Handel über Tage bis Wochen, (b) langfristiger Aufbau (Akkumulation, Halten über Monate, Kaufzeitpunkt innerhalb), (c) beides als getrennte Pfade | **(c), mit (b) als Hauptpfad.** Das entspricht deinem *„langfristiges Investment“* vom 23.09. S-E wird nur über den billigen Kandidaten L3 (REGEL0-Kern ohne Hebel, länger gehalten) geprüft |
| **S-b** | ⭐ **Wer beantwortet das Ob?** (1) Das System versucht, ein Ob zu messen (Regime-Kontext, O10/R). (2) Das System beantwortet nur **welches und wann innerhalb**, und das Regime steht als **Fakt** in der Mail (BTC unter dem Schnitt, Marktbreite …). **Wie viel** investiert ist, entscheidest du | **(2), mit (1) als Messung im Hintergrund.** Begründung: 2.599 (nicht vorab erkennbar), 2–4 Regimewechsel ab 2024, und deine stehende Vorgabe: *„übergeordnete Kräfte nur gewichten — der Nutzer bewertet selbst“*. Ein System, das 2025 automatisch weiter nachgekauft hätte, ist genau der Fehler |
| **S-c** | **Reihenfolge der Messungen** (alle am Desktop, ohne LLM, parallel zu N4) | M-1 Kostensatz aus dem Buch → M-2 **L3** (Kern 1x auf 72 h/120 h/20 T) → M-3 Akkumulation **ab 2024 unter der Norm** (schnitt als Sperre, turnover, funding, Tagesrang) → M-4 Querschnitt Einstieg auf Wochen → M-5 Bestand und Ausstieg (O19, Trailing K-2). Je Messung eine Voranalyse und ein Zwischenfazit |
| **S-d** | **Der Betrieb** | erst nach der Hebel-Umstellung (Schritt 8); bis dahin läuft die alte Kette, ihre LLM-Aufrufe stoppt O24 rechtzeitig. ⚠️ Beim Anhalten steht auch die Hebelführungs-Mail **echter** Positionen still (§1) — vorher in die REGEL0-Seite verlegen oder bewusst hinnehmen |

**Nebenbefunde (nicht Teil des Neubaus, notiert):** Die Stop-Nachzieh-Mail zieht Spot-Stops nach, obwohl Spot keinen Stop hat (O19). Akkumulation kann Verkäufe doppelt buchen (zu prüfen). Der Kommentar in `regel0_betrieb.yaml` *„wirkt nach dem Neustart“* ist ungenau — der Schalter wirkt ab dem nächsten Umlauf.

---

## 6. Belege

| Datei | Inhalt |
|---|---|
| `Spot_Voranalyse_04_10/v2_nachkauf_messen.py` / `.txt` | §2.1, Live-Signale gegen den weiteren Verlauf |
| `Spot_Voranalyse_04_10/v2b_unter_schnitt_rueckspiel.py` / `.txt` | §2.2, Rückspiel 2024–2026. ⚠️ Erste Fassung zählte Lücken als „nicht im Minus“ (pandas 3: `stack()` behält NaN) und maß mit Mitteln, die schon beim Zufallskauf +3 bis +10 % ergaben — beides behoben, die Zahlen oben sind die korrigierten |
| Recherchen V-1 und V-4 | Fundstellen im Text (Datei:Zeile, Befundnummern) |

## 7. M-0 Machbarkeit — Messplan, vorab festgelegt (05.10.2026; E-59)

Nutzer 05.10.: *„Ja, Spot M-0 Machbarkeit parallel starten, aber so, dass beide Themen Spot und Hebel sauber getrennt bleiben und alles dokumentiert, in die Zentraldokumente nachgezogen und in den Hauptplan eingetragen wird.“*

**Frage:** Ist ein Spot-Pfad mit unseren Daten **überhaupt nachweisbar** tragfähig? Das wird entschieden, bevor irgendetwas gebaut wird (Plan O23: Totalüberarbeitung, Machbarkeit, offene Punkte).

### 7.1 Trennung Hebel / Spot (gilt ab jetzt)

| # | Regel | Woran man es sieht |
|---|---|---|
| T-1 | **Dokumente getrennt.** Hebel: `Voranalyse_Schritt7_Betrieb_02_10.md`, Plan O7/O16/O20–O25. Spot: `Voranalyse_Spot_Neubau_04_10.md`, Plan **O23** (dazu O26). Kein Spot-Inhalt im Hebel-Dokument und umgekehrt, nur Querverweise | jede Spot-Zeile hat O23 im Bezug |
| T-2 | **Kein Betriebscode für Spot** (`agent/`, `scheduler/`, `ui/`, `api/`, `importer/`), bis der Hebel freigegeben (Schritt 8) und der Spot-Bau abgestimmt ist. Spot misst nur mit Skripten unter `Basisinfos/Spot_Voranalyse_04_10/` | `git diff` eines Spot-Schritts berührt nur diesen Ordner und die Spot-Doku |
| T-3 | **Getrennte Commits** mit Präfix `Spot M-…:` bzw. `Hebel:` | Commit-Liste |
| T-4 | **Hebel hat Vorrang.** Ein NB-Befund, ein Mailfehler oder eine Kontrolle unterbricht Spot sofort. Vor jedem Spot-Schritt sehe ich die offenen Hebel-Pflichten durch (Arbeitsstand: Abschnitt HEBEL-PFLICHTEN) | Arbeitsstand |
| T-5 | **Spot misst nur am Desktop**, nur lesend gegen die Messbasis. Kein NB-Zugriff, kein LLM-Kontingent (das gehört N4 und dem Live-Block) | Skripte öffnen `mode=ro`, kein Netz |
| T-6 | **Memory getrennt:** Der Arbeitsstand führt einen eigenen Abschnitt SPOT-STRANG neben dem Hebel | Memory |

### 7.2 Die drei Teilfragen und ihre Regeln — VOR der Messung festgelegt

Gemeinsam für alle drei:
- **Urteil ab 2024** (Messfokus); 2022/23 werden nicht gerechnet.
- **Wahl auf 2024, Bestätigung auf 2025 und 2026**, je Jahr getrennt.
- Messbasis 116 Assets, eingestellte eingeschlossen, Tageskurs 23:00 UTC, nur lesend.
- **Mehrfachtesten ausgewiesen:** Die Zahl der Tests und die dabei zu erwartenden Zufallstreffer stehen im Ergebnis.

| | Frage | Maß | **tragfähig, wenn** |
|---|---|---|---|
| **M-0a** Welches (Querschnitt) | Ordnet ein Merkmal, welches Asset in den nächsten 20 bzw. 90 Tagen besser läuft? Kandidaten nur aus Kursen: Abstand zum 200-Tage-Schnitt, Momentum 60 und 250 Tage, rsi 14 Tage, Schwankung 30 Tage, Volumen relativ zu 30 Tagen. Das sind 6 Merkmale × 2 Horizonte = 12 Tests, also ~0,6 Zufallstreffer erwartet | Tagesrang des Ertrags (0 = schlechtestes, 1 = bestes Asset), **oberes minus unteres Fünftel**, gemittelt über Asset-Monate. Nullwelt: das Merkmal je Asset **zirkulär verschoben** (40 Verschübe ≥ 60 Tage) | 2024 über dem 95. Perzentil der Nullwelt **und** 2025 wie 2026 mit gleichem Vorzeichen, mindestens eines davon über dem 95. Perzentil |
| **M-0b** Ob (Niveau) | Sagt ein marktweites Merkmal am Monatsende den Ertrag eines Zufallskaufs im Folgemonat voraus? Kandidaten: BTC-Abstand zum Schnitt, Marktbreite (Anteil der Assets über dem Schnitt), Median-Momentum 60 Tage | Spearman zwischen Merkmal und Median-Ertrag aller Assets der nächsten 30 Tage, nicht überlappende Monate ab 2024 (~32). Nullwelt: Blockverschub | p < 0,05 gegen die Nullwelt **und** dasselbe Vorzeichen in beiden Hälften. ⚠️ Bei ~32 Monaten erkennt die Messung erst Korrelationen ab etwa 0,35; das wird mit ausgewiesen |
| **M-0c** L3 | Trägt der REGEL0-Einstieg **ohne Hebel und länger gehalten** (72 h, 120 h, 20 Tage)? | Einstiege aus der Referenz (`kern48jbz_einstiege_bestand.csv`, 2024–2026), Rang des Ertrags gegen Zufallsstunden derselben Assets im selben Monat | Rang 2024 über dem 95. Perzentil des Zufalls **und** 2025, 2026 gleiches Vorzeichen, mindestens eines über dem 95. Perzentil |

### 7.3 Was aus dem Ergebnis folgt — ebenfalls vorab

| Ergebnis | Folge |
|---|---|
| ein M-0a- **oder** M-0c-Kandidat trägt | Spot ist **machbar als Auswahl** (welches Asset, wann innerhalb). Weiter mit M-1 (Kosten) bis M-5 |
| M-0b trägt nicht | Das *Ob* bleibt bei dir (S-b), wie vorgeschlagen. Das ist kein Abbruchgrund |
| M-0b trägt | eigener Vorschlag zum *Ob*, getrennt zur Abstimmung |
| **nichts** trägt | Spot ist mit unseren Daten **nicht nachweisbar**. Der Spot-Ast schrumpft auf Bestand und Ausstieg (S-B) und deine eigene Investitionsquote; keine Spot-Signale |

### 7.4 Ergebnis M-0 (05.10.2026; Beleg `Spot_Voranalyse_04_10/m0_machbarkeit.py` / `.txt`, Messplan Commit 0e776be)

**Nach dem vorab festgelegten Plan trägt KEIN Kandidat:** Welches nein · Ob nein · L3 nein.

| | Ergebnis |
|---|---|
| **M-0a Welches** | 0 von 12. Abstand zum Schnitt, Momentum 60/250, rsi 14, Volumen relativ: alle in mindestens einem Jahr unter der Nullwelt oder mit wechselndem Vorzeichen |
| **M-0b Ob** | 0 von 3 (BTC-Abstand ρ −0,27, p 0,11; Marktbreite ρ −0,12; Median-Momentum ρ +0,08). Mit ~30 Monaten erst ab ρ ≈ 0,3–0,56 nachweisbar |
| **M-0c L3** | 72 h und 120 h **unter** dem Zufall (Rang 0,488–0,498); 480 h 2025/2026 knapp darüber (0,517 / 0,512 bei N95 0,508), 2024 nicht (0,502 bei N95 0,511) → trägt nicht |

**Folge nach §7.3:** *Spot ist mit unseren Daten als Auswahl nicht nachweisbar.* Der Spot-Ast schrumpft auf Bestand und Ausstieg (S-B) und deine eigene Investitionsquote; keine Spot-Signale. Das *Ob* bleibt bei dir.

⚠️ **Eine Auffälligkeit, ehrlich eingeordnet – niedrige Schwankung:**
- `schwankung30` liegt in **allen drei Jahren und auf 20 wie 90 Tagen am unteren Rand** der Nullwelt. Ruhige Assets liefen im Tagesrang besser als schwankungsreiche (20 T: −0,105 / −0,174 / −0,068; 90 T: −0,212 / −0,191 / −0,067).
- Der Messplan hatte nur den **oberen** Rand als Erfolg festgelegt. Das war eine Schwäche meines Plans: Er war einseitig, ohne dass die Richtung fachlich vorgegeben war.
- **Nachträglich umgedeutet wird es nicht** (Mehrfachtesten).
- Fachlich liegt eine Erklärung nahe: 2024–26 war für Altcoins überwiegend fallend, ruhige Assets fallen weniger und stehen im Rang oben. Das wäre ein **Effekt des Regimes**, kein dauerhafter Vorteil. Das ist zu **messen**, nicht anzunehmen.

**Vorschlag M-0d – Bestätigung, wieder vorab festgelegt** (zur Abstimmung):
1. **Unabhängige Menge:** dieselbe Regel (unteres Schwankungsfünftel minus oberes, Tagesrang, 20/90 T) auf den **~420 Assets außerhalb der Messbasis** (`stundenkurse_alle.db`, ab 2024). Diese Assets hat M-0 nie gesehen.
2. **Spiegel nach Marktrichtung:** getrennt nach Monaten mit steigendem und fallendem Median-Ertrag. Trägt es nur in fallenden Monaten, ist es das Regime, kein Spot-Vorteil.
3. **tragfähig**, wenn auf der unabhängigen Menge 2024, 2025 und 2026 je über der Nullwelt (zweiseitig, Richtung jetzt festgelegt: niedrig besser) **und** in steigenden **wie** fallenden Monaten gleichgerichtet.

### 7.5 Nutzervorgabe 05.10.: Spot neu anlegen – Klima und echte Bodenbildung (E-60)

Nutzer: *„Ok, Spot muss anders angelegt werden. BTC und Altcoins hatten gerade eine Trendwende, d. h. es ist erforderlich, das Wetter bzw. Klima für eine echte Bodenbildung zu erkennen.“*

**Fakt aus der NB-Kopie (05.10. 04:00 UTC):**
- BTC: Tief 30.06. bei 58.600, am 04.10. bei 86.500 (+48 %), 21 % über dem 200-Tage-Schnitt (06.08.: −9 %).
- Anteil der Assets über dem 50-Tage-Schnitt: 22 % (06.08.) → 91 % (21.08.) → 97 % (04.10.).
- Anteil über dem 200-Tage-Schnitt: 11 % → 84 %.
- M-0 hat fast nur die fallende Phase gesehen.

**Vorschlag zur Anlage (zur Abstimmung):**
1. **Klima** (marktweit, Fakten): Marktbreite, BTC gegen Schnitt und Steigung, Breitensprünge, Abstand zum Hoch, Schwankungsregime.
2. **Bodenbildung** (Ereignis): „echter Boden“ vorab und rückblickend festlegen. Dann eine **Ereignisstudie** seit 2021: echte Böden gegen Erholungen im fallenden Markt.
3. **Handlung:** Aufbau (Akkumulation), erst wenn 2 trägt.

**Ehrlich vorab:**
- Nur etwa 4–8 echte Böden seit 2021. Ebene 2 wird deshalb eine **beschreibende Auskunft** („erfüllt seit …; von N Lagen hielten M“), kein statistisch nachgewiesenes Signal (2.599).
- Das *Ob* bleibt beim Nutzer (S-b, *übergeordnete Kräfte nur gewichten*).
- Ein Boden ist erst mit Verzögerung bestätigt.

**Vorher das Bestehende lesen:** 2.599, 2.685 Losfahren, 2.686 Wetter, 2.697 Gegenwind (K_IG), O10 Marktphasen.

**M-0d** (niedrige Schwankung) wird nicht eigens gerechnet. Nach der Wende spricht viel für ein Regime; es geht in Ebene 1 auf.

## 8. Voranalyse Spot: Klima und echte Bodenbildung — antizyklisch über längere Zeiträume (05.10.2026; E-60)

Nutzer 05.10.: *„Ok, wir können langsam mit Spot anfangen. Führe nicht nur interne, sondern auch externe Recherche durch: wie können wir das über längere Zeiträume antizyklisch abbilden?“*

Getrennt vom Hebel (E-59, T-1 bis T-6). Gemessen wird hier noch **nichts**: Das ist die Grundlage zur Abstimmung.

### 8.1 Was im Projekt schon dazu existiert (interne Recherche)

| | Stand |
|---|---|
| Marktzustand, Regime | **nur auf Stundenhorizonten für den Hebel gemessen** (2.598, 2.599 H6/H24; Wetter 2.686 und Gegenwind 2.697 auf 24 h). Auf Wochen bis Monate gibt es nur drei Messungen: Kap. 114 (20/60/120 T, „stumm“), Sentiment 12.7, M-0b. Keine hat etwas nachgewiesen |
| ⭐ Deine Vorgabe 27.08. | *„Fehler ist, Kern-Assets über den Fear zu kaufen – der Markt ist über Monate im Fear. Es muss eine **strukturelle Bodenbildung** sein.“* Dazu `Definition_Boden_gehalten_27_08.md` (*Boden gehalten*, Dow/Wyckoff, **höheres Tief**). Vorab festgelegt, **nie gemessen** |
| Akkumulation | Antizyklisch kaufen half nur, wenn das Regime drehte. Die Tagewahl *unter dem Schnitt* schlug den quotengleichen Zufall in 91 % / 83 % der Fenster (23.08.), im Rückspiel 2025/26 verlor aber jeder Kauf (§2.2). Für BTC/ETH war das Maß nie tragend |
| Fear & Greed | Fear ist ein Dauerzustand (100 Phasen, längste 151 Tage, 27.08.). Extreme Angst hatte auf 10 Tagen **nicht** den behaupteten Vorteil (12.7) |
| Nie gemessen | eine Ereignisstudie „echter Boden gegen Erholung im fallenden Markt“ · Regime rekonstruiert mit Positivkontrolle 2018-12, 2022-11, 08/2026 · Bewertung on-chain (MVRV) mit Historie · Breitensprünge auf Wochen und Monaten |

**Daten im Haus:**
- BTC und ETH täglich **ab 2017-08** (`messdaten.db`, 527 Symbole).
- Funding ab 2019, Terminmarkt stündlich ab 2021-12.
- Fear & Greed ab 2018-02.
- On-chain nur Umlaufmenge und aktive Adressen; MVRV ohne Historie.

**Abgedeckte Tiefs:**

| Tief | Rückgang |
|---|---|
| 2018-12 | −84 % |
| 2020-03 | −73 % |
| 2021-07 | −54 % (Tagestief 20.07.2021) |
| 2022-11 | −78 % |
| 2026-07 | −54 % |

Dazu die Korrekturen 2024-08 und 2025-04 (je etwa −33 %).

### 8.2 Was außerhalb dazu bekannt ist (externe Recherche, Quellen im Recherchebericht)

1. ⭐ **2026 ist der erste echte Test außerhalb der Stichprobe – und die klassischen Schwellen haben nicht ausgelöst.** Am Tief 30.06. lag MVRV bei **1,10**; der Realized Price (~53.100) wurde **nicht** unterschritten. Ich habe das an den Rohdaten der freien CoinMetrics-Schnittstelle selbst nachgeprüft. Auch der Drawdown blieb bei −54 % statt −77 bis −87 %. ➤ **Feste Schwellen aus 3–4 Zyklen sind überangepasst**; belastbarer sind relative Lagemaße (Perzentil im wachsenden Fenster) mit Bestätigung über Trend und Breite.
2. **Belegt:**
   - **Trendfolge** (Kurs gegen gleitenden Schnitt) sagt BTC-Renditen vorher und mindert die Drawdowns (Detzel u. a. 2021).
   - Faber (10-Monats-Schnitt): Der Kern ist **Drawdown-Vermeidung, nicht Mehrrendite**.
   - **MVRV-Regeln** mit einer Fachstudie (Grobys u. a. 2026): nur 3 Einstiege, Schwellen im Nachhinein gesetzt.
   - Fear & Greed hat keine Vorhersagekraft außerhalb der Stichprobe.
   - Markov-Regime sagen nicht zuverlässig vorher (Kirby 2023), das deckt sich mit 2.599.
   - Value Averaging ist eine Rückschau-Verzerrung (Hayley).
3. **Praktikerwissen ohne Studie:** Marktbreite (Anteil über 50/200-Tage-Schnitt, unter 30 % gilt als Kapitulation) und Breitensprünge nach Zweig-Art; bei Aktien umstritten. Pi Cycle ist an 2 Böden angepasst und wird **nicht** verwendet. Hash Ribbons und Puell lassen nach.
4. **Methodik bei 4–8 Ereignissen:**
   - Ereignis vorab und mechanisch festlegen.
   - Den **Zustand** bewerten (Folgerenditen an allen Tagen mit „an“), nicht den Bodentag.
   - Einen Zyklus auslassen (Schwellen aus den früheren, Test am nächsten).
   - Gegen **DCA mit gleichem Kapital am Endvermögen** messen.
   - Fehlalarmquote und Verzögerung ausweisen.
   - ETH und Altcoins sind **keine** unabhängigen Zyklen.

### 8.3 Vorschlag: drei Stufen, als FAKT-Ampel, nicht als Kaufsignal

| Stufe | Frage | Messgrößen (alle aus freien Daten, kausal) |
|---|---|---|
| **A Zone** – ist es billig? | Liegt der Markt tief gegen seine eigene Kostenbasis und Geschichte? | BTC-MVRV als **Perzentil im wachsenden Fenster** (CoinMetrics frei) · Drawdown vom Hoch **in Einheiten der eigenen Schwankung** · Abstand zum 200-Wochen-Schnitt |
| **B Wende** – ist der Boden **strukturell**? | Hat der Markt gedreht, statt nur zu erholen? | **Breitensprung** (Anteil der Grundgesamtheit über dem 50-Tage-Schnitt von unter 30 % auf über 80 % binnen 20 Tagen; eingestellte Werte bleiben drin) · BTC zurück über dem 200-Tage-Schnitt **mit steigender Steigung** · **höheres Tief** nach Dow/Wyckoff (deine Definition vom 27.08.) |
| **C Klima** | Zustand in Worten | *Kapitulation* (A an, B aus) · *Bodenbildung läuft* (A an, B teilweise) · *Wende bestätigt* (B voll) · *Aufwärtstrend* · *überhitzt* (A am oberen Rand) |

**Was daraus wird:**
- Eine **Klima-Auskunft** in Tab und Mail. Das *Ob* bleibt bei dir (S-b; *übergeordnete Kräfte nur gewichten*).
- Erst wenn die Ereignisstudie es trägt: eine **Aufbauregel** (Akkumulation) für die Kernwerte, gemessen gegen DCA mit gleichem Kapital.

**Ehrliche Erwartung (Literatur und eigene Befunde):**
- Eher **geringere Drawdowns und bessere Kapitalbindung** als eine nachweisbar höhere Rendite.
- Ein **Nachweis** im Sinne unseres Messstandards ist bei 4–8 Ereignissen nicht erreichbar, nur die Wirkungsrichtung.
- Ein Boden ist erst mit Verzögerung bestätigt; ein Teil des Anstiegs ist dann schon gelaufen.

**Heute (Fakt, 04.10.):**
- Stufe B wäre seit etwa dem **21.08.** erfüllt (Breite über dem 50-Tage-Schnitt 22 % → 91 % in 15 Tagen; BTC 21 % über dem 200-Tage-Schnitt).
- Stufe A war am Tief **knapp nicht** erfüllt: MVRV 1,10, Realized Price nicht unterschritten.

### 8.4 Ereignisdefinition „echter Boden“ — Vorschlag, VOR jeder Messung festzulegen

Ein **echter Boden** ist ein Tagestief von BTC, das alle drei Bedingungen erfüllt:
1. Es liegt mindestens **45 %** unter dem vorherigen Allzeithoch.
2. In den **180 Tagen** danach folgt kein tieferes Tief.
3. Innerhalb von **365 Tagen** liegt der Kurs mindestens **+50 %** über dem Tief.

**Mechanisch erfüllt:**

| Tief | Status |
|---|---|
| 2018-12 | erfüllt |
| 2020-03 | erfüllt |
| 2021-07 | erfüllt |
| 2022-11 | erfüllt |
| **2026-07** | Bedingung 2 erst am **2026-12-28** prüfbar; +48 % sind heute erreicht |

**An den BTC-Tagesdaten geprüft (05.10.):** 2018-12-15 (−83 %, +315 % in 365 T), 2020-03-13 (−80 %, +1.518 %), 2021-07-20 (−54 %, +131 %), 2022-11-21 (−77 %, +145 %). Alle vier erfüllen alle drei Bedingungen, keines hatte binnen 180 Tagen ein tieferes Tief. Die Definition trennt also die bekannten Böden; ob sie Fehlalarme ausschließt, zeigt erst die Studie.

**Gegenstück:** Eine *Erholung im fallenden Markt* ist jede Phase, in der Stufe B kurz auslöste und danach ein tieferes Tief folgte. Sie ergibt die **Fehlalarmquote**.

### 8.5 Zur Abstimmung (nur, was bei dir liegt)

| # | Frage | Vorschlag |
|---|---|---|
| **K-1** | **Messfenster:** Deine Regel E-21 sagt *Urteil ab 2023/24, Fallzahl nie mit alten Jahren auffüllen*. Ab 2024 gibt es aber genau **einen** echten Boden | Ausnahme **nur für die Bodenstudie**: Die Zyklen 2018–2022 **bestimmen** die Schwellen, **2026 ist der Test**. Alles getrennt ausgewiesen, nie zusammengezählt |
| **K-2** | **Neue Datenquelle:** CoinMetrics Community (frei, ohne Schlüssel, nichtkommerzielle Lizenz) für BTC- und ETH-MVRV, Ausgabe und Hashrate | ja: einmal die Historie am Desktop laden, später am NB laufend (E-35) |
| **K-3** | **Aufbau** A Zone · B Wende · C Klima als **Fakt-Ampel** | ja, wie in §8.3 |
| **K-4** | **Ereignis „echter Boden“** wie in §8.4 (45 % / 180 Tage / +50 %) | ja, vor jeder Messung festgeschrieben |
| **K-5** | **Erfolgsmaß** einer späteren Aufbauregel: Endvermögen gegen DCA mit gleichem Kapital, dazu der größte Drawdown | ja; Mehrrendite wird **nicht** versprochen |

⚠️ **Spannung zu einer älteren Vorgabe:** Am 25.09. hast du gesagt *„nicht den Markt messen, sondern Beiträge je Asset“*. Das Klima **ist** Markt. Die Notiz selbst erlaubt Marktzustände *„in die Mail als Information oder als Sperre“*. Mein Vorschlag hält sich daran: Das Klima ist Auskunft und Gewicht, kein Auslöser je Asset. Wenn du es anders siehst, ist das K-3.

### 8.6 K-1 bis K-5 als vorläufige Hypothesen — Messplan Fassung 1, VOR der Messung (05.10.2026; E-61)

Nutzer 05.10.: *„Ja, lege diese als vorläufige Hypothesen fest, abhängig von den Ergebnissen.“*

**Versionsregel:** Ändert ein Ergebnis eine Hypothese, entsteht **Fassung 2 mit Begründung**. Fassung 1 bleibt als Maßstab stehen und wird nie still angepasst (Mehrfachtesten).

**Daten:**
- BTC täglich aus **CoinMetrics Community** (Kurs, MVRV, Umlaufmenge ab 2010; einmal geladen nach `data/_spot/coinmetrics.db`, Lizenz CC BY-NC, privat).
- Marktbreite aus allen Krypto-Reihen in `messdaten.db` (Binance täglich, eingestellte eingeschlossen). **Erst ab 2020**, weil vorher weniger als 50 Reihen vorliegen. 2018 läuft deshalb ohne Breite.
- **Zyklen** (K-1): Z1 2018-12 · Z2 2020-03 · Z3 2021-07 · Z4 2022-11 **bestimmen** · **Z5 2026-07 ist der Test**. Alles getrennt ausgewiesen.

**Zustände — kausal, täglich, ohne angepasste Schwellen** (Perzentile im **wachsenden** Fenster ab 2013, nie über die ganze Reihe):

| | Bedingung |
|---|---|
| A1 | MVRV-Perzentil ≤ 20 % |
| A2 | Drawdown vom Allzeithoch in Einheiten der Jahresschwankung (σ der Tagesrenditen über 365 T × √365), Perzentil ≥ 80 % |
| A3 | Kurs / 200-Wochen-Schnitt, Perzentil ≤ 20 % |
| **A Zone an** | mindestens 2 von 3 |
| B1 | Breitensprung: Anteil über dem 50-Tage-Schnitt von ≤ 30 % auf ≥ 80 % binnen 20 Tagen; gilt danach 60 Tage (ab 2020) |
| B2 | BTC über dem 200-Tage-Schnitt **und** der Schnitt höher als vor 20 Tagen |
| B3 | **höheres Tief** (Dow, G5 vom 27.08.): Tief der letzten 30 Tage über dem Tief der 60 Tage davor |
| **B Wende an** | B2 und B3, dazu B1, wo die Breite vorliegt |
| **C Klima** | *Kapitulation* = A an, B2 und B3 aus · *Bodenbildung läuft* = A an und (B2 oder B3) · *Wende bestätigt* = B an · *Aufwärtstrend* = B2 ohne A · *überhitzt* = MVRV-Perzentil ≥ 90 % |

**Die Hypothesen** (Fassung 1). Die Richtung ist fachlich vorgegeben (*Zone* = billig, *Wende* = besser), deshalb einseitig. Die Gegenrichtung wird mit ausgewiesen.

| # | Hypothese | gilt als gestützt, wenn |
|---|---|---|
| **H1 Zone** | Am echten Boden ist A an | in ±30 Tagen um das Tief in **≥ 3 von 4** Bestimmungszyklen; Z5 berichtet |
| **H2 Wende** | Nach jedem echten Boden schaltet B ein | binnen 120 Tagen in ≥ 3 von 4; **Verzögerung** in Tagen und **verpasster Anstieg** in % vom Tief berichtet |
| **H3 Fehlalarm** | B schaltet selten im fallenden Markt ein | Anteil der B-Einschaltungen, nach denen binnen 180 T ein Tief **20 % unter** dem Einschaltkurs folgt, ≤ 1/3 |
| **H4 Klima trägt** | Nach *Wende bestätigt* läuft BTC besser als an einem beliebigen Tag | 180-Tage-Folgeertrag an B-Tagen über dem aller Tage, in ≥ 3 von 4 Zyklen. Nullwelt: Zustandsreihe zirkulär verschoben (200×), Perzentil als **Auskunft** |
| H5 (K-5, später) | Eine Aufbauregel auf dem Klima schlägt DCA mit gleichem Kapital | Endvermögen und größter Drawdown. Erst, wenn H1–H4 tragen |

**Echter Boden** nach K-4: mindestens 45 % unter dem Hoch, 180 T kein tieferes Tief, +50 % in 365 T. Z1–Z4 sind an den Daten geprüft (§8.4).

**Ehrlich:** Bei 4 Bestimmungszyklen ist ein Nachweis nicht erreichbar. „Gestützt“ heißt Wirkungsrichtung, Fehlalarm und Verzögerung **beschrieben**, nicht bewiesen.

### 8.7 Ergebnis Fassung 1 (05.10.2026, nach dem vorab festen Plan §8.6)

Beleg: `Spot_Voranalyse_04_10/k1_klima_studie.py` → `k1_klima_studie.txt`. Daten: CoinMetrics bis 04.10.2026, Breite aus `messdaten.db` bis 20.09.2026 (nur lesend). Nichts nachgestellt.

**Auslegung, vor dem ersten Lauf im Skriptkopf festgelegt** (im Plan nicht genau bestimmt): Kurs = CoinMetrics-Tagesschluss · Zyklusfenster für H4 = Tief ±365 T · eine B-Einschaltung = erster B-Tag nach ≥ 10 Tagen ohne B · Breite nur bei ≥ 50 Reihen.

**Echte Böden** (K-4, aus den Daten gefunden, nicht vorgegeben): 15.12.2018 · 12.03.2020 · 20.07.2021 · 09.11.2022 · **30.06.2026 vorläufig** (180-Tage-Bedingung erst am 27.12.2026 prüfbar). Deckt sich mit Z1–Z5.

| | Ergebnis Bestimmung Z1–Z4 | Z5 2026 (Test) | Urteil Fassung 1 |
|---|---|---|---|
| **H1 Zone** | A an in **3 von 4**; nicht 2021-07 (Zwischentief im Bullenmarkt, MVRV 1,54 = Perzentil 40 %) | **A an** (alle drei, MVRV 1,10) | **gestützt** |
| **H2 Wende** | B binnen 120 T in **3 von 4**: 2020 nach 57 T (+99 % vom Tief), 2021 nach 30 T (+57 %), 2022 nach 78 T (+46 %); 2018 erst nach 154 T (18.05.2019) | B an **03.09.2026**, nach 65 T, **+39 %** vom Tief | **gestützt** |
| **H3 Fehlalarm** | **2 von 11** Einschaltungen (18 %): 07.03.2018 (−41 %), 19.08.2021 (−25 %) | 03.09.2026 offen bis 02.03.2027 | **gestützt** |
| **H4 Klima trägt** | 180-T-Folgeertrag an B-Tagen über dem aller Tage nur in **1 von 4** (2022: +18 Pp; 2018 −41, 2020 −55, 2021 −26 Pp); Nullwelt-Rang 0,12–0,67, nirgends auffällig | nicht messbar (Ertrag reicht nur bis 07.04.2026, also vor dem Tief) | **nicht gestützt** |

**Auskunft — keine Hypothese der Fassung 1**, die Gegenrichtung nach §8.6: derselbe Vergleich für **A-Tage (Zone)**: 2018 **+152 Pp** (Rang 1,00) · 2020 +37 Pp (0,71) · 2021 **−69 Pp** (0,34; die A-Tage im Juni 2022 lagen vor dem letzten Abverkauf) · 2022 **+28 Pp** (0,99) · 2026 +36 Pp (1,00; A-Tage Feb.–Apr. 2026, vor dem Tief).

**Klima heute (04.10.2026, Fakt):** *Wende bestätigt* seit 03.09. · Zone aus (MVRV 1,61 = Perzentil 45 %) · B1 nur noch aus dem 60-Tage-Nachlauf, weil die Breite in `messdaten.db` am 20.09. endet.

**Gegenprobe** (unabhängige Schleifenrechnung, scratchpad): Einschalttage von B2/B3 am 08.05.2020, 26.01.2023 und 03.09.2026 gleich, MVRV-Perzentil am Tief 2026 0,149 / 2022 0,010 / 2021 0,402 gleich, die fünf Tiefs als Minimum ihres Zeitraums gleich.

#### Was daraus folgt — und was nicht

- **Die Wende erkennt man, aber sie ist nicht das Potential.** B kommt verlässlich und selten falsch (H2, H3), doch im Mittel **30–78 Tage und +46 % bis +99 % nach dem Tief**. Wer erst bei der Wende kauft, hat nach dem Zyklusfenster nicht mehr als an einem beliebigen Tag (H4).
- **Das Potential lag in der Zone** — antizyklisch, wie vom Nutzer vorgegeben (E-60). ⚠️ Das ist **Auskunft**, kein Befund: dieselben 4 Zyklen, nachträglich angesehen. 2021 zeigt die Gefahr: eine Zone mitten im Abwärtsmarkt (Juni 2022) kostete −23 % über 180 T.
- **Nicht** folgt: eine Aufbauregel. H5 (gegen DCA) ist nach §8.6 erst zulässig, wenn H1–H4 tragen. H4 trägt nicht.
- **Eine Fassung 2 auf der Zone** wäre auf denselben Zyklen **kein unabhängiger Test**. Unabhängig bleiben nur Z5 (die Zone Feb.–Jun. 2026 wird ab Ende 2026 messbar) und eine zweite Menge, etwa **ETH mit eigenem MVRV** (CoinMetrics ab 2015, liegt schon in `coinmetrics.db`); ETH ist stark mit BTC verbunden, also nur teilweise unabhängig.

### 8.8 Messplan FASSUNG 2 — die Zone als Aufbaufenster, VOR der Messung (05.10.2026; E-62)

Nutzer 05.10.: *„Ja, prüfen und gegenprüfen.“* (auf den Vorschlag nach §8.7). **Gemessen wird erst nach dem Ja zu diesem Plan.**

**Begründung der Fassung 2** (Versionsregel §8.6): H4 trug nicht (die Wende kommt zu spät). Die Auskunft zeigte die Zone vorn, **aber auf einem Vergleich mit Vorgriff**: die Basis waren die Tage um das *bekannte* Tief. Fassung 2 beseitigt den Vorgriff, prüft zweiseitig und führt direkt auf die Zielfrage K-5 (Aufbau gegen DCA). Die Zustände A1–A3 bleiben **unverändert** aus Fassung 1, es gibt keine neue Schwelle.

#### Was unabhängig ist und was nicht

| Menge | Status |
|---|---|
| **BTC 2017–2022** | **Wiederholung**, kein Test. Die Zone-Tage dort sind in §8.7 schon angesehen |
| **ETH** | **teilweise unabhängig**. Folgeerträge nie angesehen; eigene Böden 2022-06, 2023-10, 2025-04 (nicht die von BTC); stark mit BTC verbunden |
| **ab 2023** (Messfokus) | Auskunft getrennt ausgewiesen; ein Nachweis ist dort mit 2–3 Episoden nicht erreichbar |
| **H5 Aufbau gegen DCA** | für **beide** Assets bisher **nie gerechnet** |

#### Daten und Zustände

- CoinMetrics täglich, BTC und ETH (`data/_spot/coinmetrics.db`, nur lesend), Messbeginn **01.01.2017** für beide.
- **A Zone = mindestens 2 der verfügbaren, mindestens 2** von A1–A3. Verfügbar sind (Vorprüfung, keine Erträge):
  - BTC: A1 und A2 ab 12.2013, A3 ab 05.2015;
  - ETH: A1 ab 08.2016, A2 ab 06.2017, **A3 erst ab 06.2020**. Vorher gilt bei ETH A1 und A2.
- ⚠️ **ETH vor 2019 hat eine kurze Vorgeschichte:** Die wachsenden Perzentile stehen dort auf ein bis drei Jahren. Ausgewiesen wird *ETH gesamt* (zählt) und *ETH ab 2019* (Auskunft).
- **Episode** = Folge von A-Tagen; eine Lücke von ≥ 30 Tagen trennt.
- Vorprüfung, rein aus A, ohne Erträge:
  - BTC 6 Episoden: 11.2018, 03.2020, 05.2022–03.2023, 05–10.2023, 02–04.2026, 06–08.2026; 2024 und 2025 keine.
  - ETH 11 Episoden, darunter 03–04.2018 und 05.2018–05.2019 (der Fall *fallendes Messer*), 2025-03 und 2026.
- **Ohne Vorgriff:**
  - A am Tag t ist erst nach dessen Schluss bekannt; MVRV erscheint am Folgetag. **Jeder Kauf erfolgt zum Schlusskurs von t+1.**
  - Die **Vergleichsbasis sind alle Tage desselben Zeitraums**, nie ein Fenster um ein bekanntes Tief.

#### Die Hypothesen der Fassung 2

| # | Frage | Messung | gilt als gestützt, wenn |
|---|---|---|---|
| **F2-H1 Zone-Ertrag** | Bringt Kaufen in der Zone mehr als an einem beliebigen Tag? | Folgeertrag ab t+1 über **180 und 365 T**, A-Tage gegen alle Tage seit 2017. **Zweiseitig**: Nullwelt aus 200 zirkulären Verschiebungen der A-Reihe, Rang ≥ 0,95 = besser, ≤ 0,05 = **umgekehrt** | Rang ≥ 0,95 in **≥ 3 von 4** Tests (2 Assets × 2 Horizonte) **und** keiner umgekehrt |
| **F2-H2 fallendes Messer** | Wie oft fällt der Kurs nach Zonenbeginn noch deutlich? | Je Episode (Einstieg t+1 nach dem ersten A-Tag): tiefster Kurs binnen 365 T, Anteil mit weiteren −20 %, Kurs nach 365 T | Kurs nach 365 T über dem Einstieg in **≥ 2/3** der Episoden mit vollem Fenster. Der weitere Rückgang wird **immer** berichtet (Risiko für Doku und Mail) |
| **F2-H3 = H5 Aufbau gegen DCA** | Schlägt ein Aufbau in der Zone regelmäßiges Kaufen mit **gleichem Kapital**? | Siehe Regel unten. **Startjahre 2017 bis 2023** (je 01.01.), Ende 04.10.2026 | **Hauptvariante V2** hat mehr Endvermögen als DCA in **≥ 5 von 7** Startjahren, **je Asset und für beide** |

**Aufbauregel, vorab und ohne Stellschraube aus den Ergebnissen:**
- **Zufluss:** 1 Einheit am Monatsersten bei beiden Varianten. Der Zufluss ist Kapital, kein Signal (Regel 1).
- **DCA:** Kauf am Monatsersten zum Schlusskurs.
- **V2 Zone gestaffelt (zählt):**
  - Der Zufluss geht ins Bargeld.
  - War A am Tag t an, wird am Tag t+1 **1/30 des Bargelds** gekauft. Das sind gut 60 % des Bargelds nach einem Monat Zone. Wegen F2-H2 kein Alles-auf-einmal.
- **V1 alles beim Zonenbeginn** (Auskunft): Das ganze Bargeld geht in den ersten Kauf einer Episode, danach fließt jeder Zufluss in der Zone sofort.
- **V3 V2 plus Wende** (Auskunft): Das Restbargeld wird bei jeder B-Einschaltung gekauft. Nur BTC, weil B auf BTC definiert ist (Breite, B2, B3).
- **Für alle Varianten:**
  - Es wird nie verkauft; der Ausstieg ist eine eigene Frage (M-5).
  - Bargeld bringt 0 % Zins, das benachteiligt die Zone bewusst.
  - Gebühren zählen nicht (Regel 2); die Zahl der Käufe wird ausgewiesen.

**Ausgewiesen je Asset und Startjahr:**
- Endvermögen V1, V2, V3 gegen DCA;
- **Anteil der Monatsenden mit V2 ≥ DCA**, weil das Endvermögen am Enddatum hängt;
- größter Rückgang des Gesamtvermögens (Bestand plus Bargeld);
- durchschnittlicher Einstand;
- ungenutztes Bargeld am Ende;
- Nullwelt-Rang der V2 bei Start 2017 (A zirkulär verschoben, 200×; Auskunft).

#### Folgen, vorab festgelegt

| Ergebnis | Folge |
|---|---|
| F2-H1 **und** F2-H3 gestützt | Klima-Zone wird **Aufbaugrundlage**. Nächster Schritt: Voranalyse der Fakt-Ampel samt Aufbauregel für den Betrieb (Schritt-8-Weg, T-2 erst nach Abstimmung); F2-H2 kommt als Risikotext in Mail und Doku |
| nur eines davon | Kein Aufbau. Die Klima-Ampel bleibt als **Fakt in der Mail**; der Nutzer entscheidet das Ob |
| keines, oder etwas umgekehrt | Spot über das Klima ist so **nicht nachweisbar**; das wird festgehalten. Kein neuer Anlauf auf derselben Menge (Mehrfachtesten) |

**Ehrlich:**
- 2 Assets mit 6 bzw. 11 Episoden, 2 Horizonte, 3 Varianten. „Gestützt“ heißt **beschrieben und stimmig**, nicht bewiesen.
- Die Tage überlappen. Die Nullwelt mit zirkulärer Verschiebung trägt das, die wirkliche Fallzahl sind die **Episoden**.

**Gegenprüfung dieses Plans (05.10., vor jeder Ertragsrechnung):**
- **Vorgriff:**
  - Kauf zu t+1 statt t. Beim Gegenprüfen gefunden: der Schlusskurs von t ist bei der Entscheidung noch nicht bekannt.
  - Vergleichsbasis ohne Fenster um ein bekanntes Tief.
- **Verfügbarkeit:** A3 fehlt ETH bis 06.2020. Deshalb „mindestens 2 der verfügbaren“.
- **Kurze ETH-Vorgeschichte** ausgewiesen.
- **Zweiseitig:** Rang ≤ 0,05 heißt umgekehrt; F2-H2 deckt den Fall 2018/2022 ab.
- **Enddatum:** Anteil der Monatsenden.
- **Startpunkt:** 7 Startjahre.
- **Regeln 1–4:** Takt und Zufluss sind kein Signal, keine Gebühren, kein Asset-Rang. Die Zone ist ein Fakt; bewertet wird **was danach kam**.
- **Grenze:** Der Plan prüft das Klima für BTC und ETH. Welches Altcoin, ist eine eigene Frage, und M-0 fand dort nichts.

### 8.9 Ergebnis Fassung 2 (05.10.2026, nach dem vorab festen Plan §8.8)

Nutzer 05.10. (Ja zum Plan, E-63): *„Ja, wir müssen an einem Punkt starten. Sollten wir während der Messungen zur Erkenntnis gelangen, dass die Annahmen und Hypothesen geändert werden müssen, dies bitte berücksichtigen. Nicht, dass wir starr an diesen festhalten.“*

Beleg: `Spot_Voranalyse_04_10/k2_zone_aufbau.py` → `k2_zone_aufbau.txt`.

**Gegenprobe:** Eine unabhängige Schleife über Kalendertage ergibt für V2 und DCA bei Start 2017 dieselben Werte (BTC 906,6 / 1.110,4 = 0,82). Die Kurse am Ende passen zu 86,5 k.

| | BTC | ETH | Urteil nach §8.8 |
|---|---|---|---|
| **F2-H1 Zone-Ertrag** seit 2017 | 180 T +19 Pp (Rang 0,65) · 365 T +9 Pp (0,60) | 180 T −69 Pp (0,33) · 365 T −244 Pp (0,23) | **nicht gestützt** (0 von 4 besser, keiner umgekehrt) |
| *ab 2023 (Auskunft)* | *+37 Pp (0,94) · +67 Pp (0,94)* | *+71 Pp (**1,00**) · +6 Pp (0,49)* | — |
| **F2-H2 fallendes Messer** | 3 von 4 Episoden nach 365 T im Plus; **weitere −20 % in 2 von 4** (2018: −30 %, 2022: −46 %) | 6 von 9 im Plus; **weitere −20 % in 8 von 11**, 2018 dreimal −86 bis −90 % | **gestützt**, das Risiko ist groß |
| **F2-H3 Aufbau V2 gegen DCA** | V2 vorn in **3 von 7** Startjahren (0,82 bis 1,21) | **3 von 7** (0,39 bis 1,35) | **nicht gestützt** |

**Folge nach dem vorab festen Plan:** Spot über das Klima ist **in dieser Form** nicht nachweisbar. Das wird so festgehalten.

#### WORAN es liegt — an den Kapitalflüssen nachgesehen (Gegenprobe, Start 2017)

1. **Warten kostet mehr, als gutes Timing bringt.** Zufallszonen gleicher Länge erreichen nur das **0,59-Fache (BTC)** bzw. **0,47-Fache (ETH)** von DCA. Jedes Warten auf ein Fenster verliert in einem Asset, das langfristig steigt. Die echte BTC-Zone liegt mit 0,82 **über** dem Zufall (Rang 0,885), aber unter DCA. ⇒ Die Annahme *„das ganze Kapital wartet auf die Zone“* ist die Ursache, nicht die Zone selbst.
2. **Die günstigste Gelegenheit wurde verpasst.** BTC im März 2020: Die Zone dauerte 12 Tage, mit der 1/30-Staffel flossen nur 4,2 Einheiten. Das gesparte Geld aus 2020–2022 (43,6 Einheiten) ging erst 05.2022–03.2023 hinein, zum Mittel 22,7 k, und dort lag das *fallende Messer* (−46 %).
3. **ETH mit kurzer Vorgeschichte meldet zu früh.** Die erste Zone kam 2018 bei 474–789 $, danach −86 %. Den Anstieg 2017 von 8 $ auf 700 $ hat die Zone ganz verpasst (Start 2017: 0,39). Ab 2019 ist ETH unauffällig (+0 / −29 Pp).
4. **Auskunft:** Der größte Rückgang ist bei V2 in allen 14 Läufen kleiner (BTC 2020: −54 % gegen −84 %). Das ist teilweise **mechanisch**, weil Bargeld gehalten wird, also kein Befund.

#### Was daraus für die Annahmen folgt (E-63: nicht starr)

| Annahme bisher | Erkenntnis | Vorschlag Fassung 3 |
|---|---|---|
| Die Zone ist ein **Fenster**, außerhalb wird nicht gekauft | Die Wartekosten dominieren (Punkt 1) | **Gewichten statt warten**, wie bei den Achsen (*Gewichte, keine Blocker*): Es wird immer gekauft, in der Zone mehr. Der Anteil folgt stetig dem MVRV-Perzentil, ohne neue Schwelle |
| Jedes Asset hat **sein eigenes** Klima | ETH-Perzentile auf 1–3 Jahren melden falsch (Punkt 3) | **Das Klima kommt aus BTC**, der längsten Reihe, und gilt als Marktklima für jeden Kauf (ETH, später Altcoins) |
| Staffel 1/30 je Zonentag | Kurze Episoden lassen Kapital liegen (Punkt 2) | Entfällt mit dem Gewichten |

⚠️ **Ehrlich zum Mehrfachtesten:** Fassung 3 wäre der **dritte Blick auf dieselben Daten**. Ihr Ergebnis ist eine **Beschreibung**. Ein unabhängiger Test entsteht erst **ab heute**, wenn die Regel laufend mitgeschrieben wird, oder auf anderen Assets. Die Ergebnisse von Fassung 1 und 2 bleiben stehen.

### 8.10 Messplan FASSUNG 3 — gewichten statt warten, Klima aus BTC, je Marktepoche (05.10.2026, VOR der Messung; E-63/E-64)

Nutzer 05.10.: *„Ja, da die ersten Jahre und ab 2024 markttechnisch doch etwas anders sind, müssen wir dies berücksichtigen, es gab nur wenige echte Zyklen.“* **Gemessen wird erst nach dem Ja zu diesem Plan.**

**Begründung** (E-63, aus der Ursache in §8.9):
- Fassung 2 scheiterte an den **Wartekosten**: Das ganze Kapital wartete auf die Zone.
- ETH meldete wegen der **kurzen Vorgeschichte** zu früh.
- Fassung 3 ändert genau diese zwei Annahmen und ergänzt die **Marktepochen**, die du genannt hast.
- ⚠️ Das ist der **dritte Blick** auf dieselben Daten. Das Ergebnis ist **Beschreibung**, der Test kommt aus neuen Daten.

#### Marktepochen — nach Fakten geschnitten, nicht nach Ergebnissen

| Epoche | Zeitraum | Warum die Grenze | Echte Böden darin |
|---|---|---|---|
| **E1 Frühzeit** | 2017 – 2020 | Privatanleger-Markt, wenige Assets, extreme Zyklen. Nutzer: *Markt seit 2021 massiv verändert* | 2018-12, 2020-03 |
| **E2 Übergang** | 2021 – 10.01.2024 | Einstieg der Institutionen, DeFi, Absturz 2022 | 2021-07, 2022-11 |
| **E3 ETF-Markt** | ab 11.01.2024 (erster Handelstag der BTC-Spot-ETFs; ETH-ETF ab 23.07.2024) | Neuer Käuferkreis, anderes Angebot. **Messfokus** | 2026-06 (vorläufig) |

⚠️ **Je Epoche 2, 2 und 1 Zyklen.** Ein Nachweis ist in keiner Epoche erreichbar. Ausgewiesen wird je Epoche **beschreibend**, damit sichtbar wird, ob die Regel in **allen** Epochen in dieselbe Richtung wirkt.

#### Das Klima-Gewicht q (aus BTC, für jeden Kauf)

- **Drei Bestandteile**, wie A1–A3: MVRV-Perzentil, 1 − Perzentil des Drawdowns in Vola-Einheiten, Perzentil des Abstands zum 200-Wochen-Schnitt.
- **q** = Mittel der verfügbaren Bestandteile, mindestens 2. 0 heißt billig wie nie, 1 heißt teuer wie nie.
- Perzentile wie bisher **im wachsenden Fenster ab 2013**. Alle drei liegen ab 05.2015 vor.
- **q stammt immer von BTC**, auch für ETH-Käufe: Das Klima ist der Markt.

**Formwahl wachsend gegen rollend — in der Vorprüfung gegengeprüft, ohne Erträge:**
- Meine Vermutung war, dass ein rollendes 4-Jahres-Fenster dem Regimewechsel besser folgt; die MVRV-Tiefs stiegen von 0,56 über 0,69, 0,88 und 0,78 auf 1,10.
- **Sie hält nicht:**
  - Rollend wäre E3 seltener billig (8 % der Tage mit q ≤ 0,2 gegen 12 %) und häufiger teuer (19 % gegen 10 %).
  - Der Grund: das 4-Jahres-Fenster enthält die tiefen Werte von 2022.
- Deshalb bleibt es **unverändert wachsend**: ein Freiheitsgrad weniger. Rollend wird nur als Auskunft ausgewiesen.

#### Die Regel V3 — gleiche Kauftage wie DCA, nur die Menge folgt dem Klima

- **Zufluss:** 1 Einheit am Monatsersten ins Bargeld.
- **Kauf am Monatsersten:** Bargeld × (1 − q des Vortags), zum Schlusskurs.
- **Begrenzte Wartekosten:** Das Bargeld pendelt sich bei q/(1 − q) Monatsraten ein, also 1 bei q = 0,5 und 9 bei q = 0,9. In Fassung 2 lagen bei BTC 2024–2025 dagegen 33 Raten still.
- **Vorprüfung:** Der mittlere Kaufanteil liegt je Epoche bei 0,43 / 0,57 / 0,46.
- **Regel 1:** Der Kauftag ist der **Zuflusstag**, also eine Kapitaltatsache. Das Klima bestimmt nur das **Wie viel**. Der Takt ist kein Signalgeber.
- Wie bisher: nie verkaufen, Bargeld 0 % Zins, keine Gebühren (Regel 2).

#### Die Fragen und wann sie als *stimmig* gelten (vorab)

| # | Frage | stimmig, wenn |
|---|---|---|
| **F3-H1 Vermögen** | Schlägt V3 regelmäßiges Kaufen bei gleichem Kapital? Startjahre **2017 bis 2023 plus 11.01.2024**, also 8 Starts. Ende 04.10.2026 | V3 ≥ DCA in **≥ 6 von 8** Starts, **für BTC und für ETH** (beide mit BTC-Klima) |
| **F3-H2 Epochen** | Wirkt es in jeder Epoche in dieselbe Richtung? Je Epoche Start am Epochenbeginn; Vermögen am Epochenende **und** am 04.10.2026 | V3/DCA ≥ 1 in **allen drei** Epochen, je Asset, am 04.10.2026. Der Wert am Epochenende wird mit ausgewiesen, weil er am Zyklusstand hängt |
| **F3-H3 Nullwelt** | Kommt der Vorteil vom **Klima** oder nur vom Mechanismus? q-Reihe zirkulär verschoben, 200×, mindestens 365 T Abstand, Start 2017 und 2021 | Rang **≥ 0,90** bei beiden Starts, BTC. Es sind wenige Zyklen, deshalb nicht 0,95; das wird so ausgewiesen |
| **F3-H4 Risiko** | Größter Rückgang von Vermögen ÷ Eingezahltem | immer ausgewiesen, kein Kriterium |

**Ausgewiesen, aber kein Kriterium:**
- durchschnittlicher Einstand. Er ist **teils mechanisch**, weil ein niedriges MVRV mit einem niedrigen Kurs einhergeht.
- Bargeld am Ende;
- Anteil der Monatsenden mit V3 ≥ DCA.

**Auskunft:** rollendes Fenster · ETH mit **eigenem** q (zeigt, was das BTC-Klima bringt) · V2 aus Fassung 2 zum Vergleich.

#### Folgen, vorab festgelegt

| Ergebnis | Folge |
|---|---|
| F3-H1 **und** F3-H3 stimmig, F3-H2 in E3 nicht gegenläufig | **Kandidat**. Nächster Schritt ist eine **laufende Mitschrift** ab dem nächsten Monatsersten: ein Schattenbuch am Desktop, kein Betriebscode (T-2, T-5). Sie ist der unabhängige Test. Parallel kommt die Voranalyse der Klima-Ampel für die Mail. Den Betrieb gibt es erst mit Belegen aus der Mitschrift; das Tempo bestimmt der Nutzer |
| nur teilweise stimmig | Nach E-63 **WORAN messen** und berichten; die Klima-Ampel bleibt als Fakt in der Mail |
| nichts stimmig oder E3 gegenläufig | Spot über das Klima ist **für den heutigen Markt** nicht belegt. Das wird so festgehalten; die Ampel bleibt als Fakt |

**Gegenprüfung des Plans (05.10., vor jeder Ertragsrechnung):**
- **Vorgriff:** q stammt vom Vortag des Kaufs; ETH nutzt das BTC-q desselben Tages.
- **Epochengrenzen** aus Fakten (ETF-Handelsbeginn, Nutzeraussage 2021), nicht aus Ergebnissen.
- **Formwahl** rollend gegen wachsend an der Vorprüfung entschieden; die eigene Vermutung ist widerlegt und festgehalten.
- **Wartekosten** jetzt mathematisch begrenzt.
- **Regeln 1–4** geprüft: Takt = Zufluss, keine Gebühren, kein Asset-Rang, q ist ein Fakt.
- **Mehrfachtesten:** dritter Blick, ausgewiesen.
- **Wenige Zyklen** (2/2/1): Die Schwelle der Nullwelt ist offen auf 0,90 gesenkt, der Grund steht dabei.
