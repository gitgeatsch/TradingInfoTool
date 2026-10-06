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

### 8.11 Ergebnis Fassung 3 (05.10.2026, nach dem vorab festen Plan §8.10) — und das Gesamtbild aus drei Fassungen

Nutzer 05.10.: *„ok, besser wird es vorläufig nicht — ja, starten wir mit Messungen.“*

Beleg: `Spot_Voranalyse_04_10/k3_gewichten.py` → `.txt`.

**Gegenprobe** (`k3_gegenprobe.py`, eigene Monatsschleife): 0,760 / 1,009 / 1,010 gleich.

| | BTC | ETH (BTC-Klima) | Urteil |
|---|---|---|---|
| **F3-H1 Vermögen**, 8 Starts | V3 ≥ DCA in **3 von 8**. Spanne 0,76 (Start 2017) bis 1,01, sonst 0,97–1,01 | **4 von 8**. 0,56 (2017) bis 1,02 | **nicht stimmig** |
| **F3-H2 Epochen** (am 04.10.2026) | E1 **0,72** · E2 1,01 · E3 **0,985** | E1 **0,54** · E2 0,94 · E3 1,02 | **nicht stimmig** |
| **F3-H3 Nullwelt** | Start 2017: Rang **0,000**, das echte Klima war das **schlechteste** aller Verschiebungen · Start 2021: 0,75 | — | **nicht stimmig** |
| F3-H4 Rückgang | V3 gleich oder bis 7 Pp kleiner | gleich oder bis 8 Pp kleiner | Auskunft |

**Auskunft:**
- Das rollende Fenster ändert nichts (gleiche Richtung, ±0,02).
- ETH mit eigenem q liegt im selben Bereich (0,94–1,04).

**Folge nach dem vorab festen Plan:** Spot über das Klima ist **für den heutigen Markt nicht belegt**. Die Klima-Ampel bleibt als **Fakt** für die Mail.

#### WORAN — an den Jahreswerten nachgesehen (Gegenprobe)

| Jahr | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|
| Klima q (Mittel) | **0,90** | 0,49 | 0,33 | 0,50 | **0,79** | 0,28 | 0,21 | **0,65** | 0,69 | 0,23 |
| BTC im Jahr | **+1296 %** | −73 % | +88 % | +305 % | **+58 %** | −65 % | +154 % | **+112 %** | −7 % | −2 % |

- Das Klima war in den **stärksten Anstiegsjahren am teuersten** (2017, 2021, 2024) und kaufte dort wenig. In den fallenden Jahren war es billig (2022) und kaufte viel, **während der Kurs weiter fiel**.
- **Der Trend über ein Jahr ist bei Krypto stärker als die Rückkehr zum Mittel.** Das Klima gewinnt nur **an den Wendepunkten**, und die sind selten. Genau das hat der Nutzer mit den *wenigen echten Zyklen* angesprochen.
- **Der Hebel ist klein**, solange immer gekauft wird: V3 verschiebt nur gut eine Monatsrate. Wirkung hat er nur in Dauerlagen, und dort ist sie negativ (2017).

#### Das Gesamtbild aus drei Fassungen (F1 §8.7 · F2 §8.9 · F3 hier)

| Was trägt | Was nicht trägt |
|---|---|
| Das Klima **beschreibt** die Lage gut: Zone an den echten Böden 3 von 4, auch 2026; Wende verlässlich, Fehlalarm 2 von 11 | **Keine Kaufregel** auf dem Klima schlägt regelmäßiges Kaufen: weder warten (F2) noch gewichten (F3), weder BTC noch ETH, in keiner Epoche verlässlich |
| Nach Zonenbeginn war der Kurs ein Jahr später meist im Plus (F2-H2) | Die Wende kommt 30–78 Tage und +46 bis +99 % nach dem Tief (F1) |
| Im ETF-Markt (E3) ist alles **neutral**: BTC 0,985, ETH 1,02 | Ein Vorteil zeigt sich nur bei Starts in fallenden Märkten (2018, 2022), und dann nur 1–2 % |

**Was daraus fürs Ziel folgt:**
- Spot-**Aufbau** als Regel: **regelmäßig kaufen** ist mit den vorhandenen Daten nicht zu schlagen.
- Das Klima gehört als **Fakt-Ampel in die Mail** (*Kapitulation · Bodenbildung · Wende bestätigt · Aufwärtstrend · überhitzt*), samt Bewertungsgründen. **Das Ob bleibt beim Nutzer** (E-55 S-b).

⚠️ **Mehrfachtesten:** drei Blicke auf dieselben Daten. Eine **Fassung 4 einer Kaufregel** auf dieser Menge wäre Kurvenanpassung. Ein neuer Anlauf braucht **neue Daten** (laufend ab heute) oder eine **andere Frage**.

**Offen für die Abstimmung, nicht gemessen:**
- (a) Die Klima-Ampel als Mail-Fakt — Voranalyse, wo und wie (T-2: Betriebscode erst nach Abstimmung).
- (b) Die **andere Frage** M-5 Ausstieg: Taugt *überhitzt* zum **Teilverkauf**? Das ist eine neue Frage, aber dieselbe Trend-Gefahr (2017).
- (c) Eine laufende Mitschrift der Ampel ab dem nächsten Monatsersten als unabhängige Beobachtung.

## 9. SPOT-REGEL0 — der Spot-Neubau nach dem Muster des Hebels (05.10.2026; E-65)

Nutzer 05.10.: *„Ja, die Punkte erscheinen sinnvoll, die Ausstiegsfrage für Spot (aktuelle Hebelplanung) steht ohnehin an. Unabhängig davon ist eine Mitschrift für langfristige Beobachtung sinnvoll, aber für unser Konzept und Vorhaben ungeeignet. Wir brauchen jetzt sinnvolle Lösungen, Tests und Simulationen, welche uns weiterbringen, analog des gerade umgebauten Hebels.“*

**Abgestimmt:**
- (a) Die Klima-Ampel kommt als Fakt in die Mail; sie wird mit Schritt S7 gebaut.
- (b) Die Ausstiegsfrage wird **mitgemessen**, nicht nachgelagert.
- ✗ (c) Die Mitschrift ist für das Vorhaben ungeeignet. Sie entfällt; höchstens später als Langzeitbeobachtung.

### 9.1 Warum der Hebel trug und das Klima nicht — die Lehre für den Bau

| | Klima (§8, F1–F3) | Hebel (REGEL0) |
|---|---|---|
| Einheit | ein **Marktzyklus** | ein **Ereignis je Asset** |
| Fallzahl | 4–5 Zyklen, nicht messbar | Tausende je Jahr: Nullwelt, je Asset, Zeitstabilität möglich |
| Wahl / Bestätigung | unmöglich zu trennen | Wahl auf **2024**, **einmal** bestätigt auf 2025–26 (E-21/E-24) |

**Folge:**
- Spot wird wie der Hebel gebaut: ein **Ereignis je Asset auf Tagesbasis**, gehalten **Tage bis Wochen**, Einstieg **und Ausstieg** als Paar.
- Das Klima wird **Achse** (Gewicht, kein Blocker) **auf** den Ereignissen. Dort lässt sich seine Wirkung messen, weil jedes Ereignis einen eigenen Klimawert hat.
- F3 hat gezeigt: *der Trend über ein Jahr schlägt die Rückkehr zum Mittel*. Deshalb kommt eine **Trend-Familie** neben die Rückgang-Familie (die Wette des Hebels).

**Vorprüfung, keine Erträge:** `messdaten.db`, Krypto, 526 Symbole ab 06.2022, eingestellte eingeschlossen.

| Familie | 2023 | 2024 | 2025 | 2026 (bis 20.09.) | Assets 2024 |
|---|---|---|---|---|---|
| **T** Trendwende: Schluss über S50 nach ≥ 20 T darunter, Ruhe 20 T | 1.225 | 1.254 | 1.195 | 1.188 | 415 |
| T′ Spiegel: Schluss unter S50 nach ≥ 20 T darüber | 842 | 1.203 | 800 | 452 | 414 |
| **R** Rückgang: Tages-RSI14 < 30, Ersteintritt nach ≥ 10 T, Ruhe 10 T | 888 | 1.068 | 1.962 | 1.062 | 404 |
| R′ Spiegel: RSI14 > 70, Ersteintritt | 1.438 | 1.230 | 786 | 737 | 417 |

Das sind rund **1.000–2.000 Ereignisse je Familie und Jahr**, also genug für die sechs Prüfungen.

### 9.2 Der Plan — dieselben Schritte wie beim Hebel (Plan_Hebel, Abschnitt 1)

| # | Schritt | Inhalt |
|---|---|---|
| **S1** | **Stufe 1 Vorprüfung** (unten, vorab) | Trägt eine Familie mit einem Ausstieg auf 2024 über der Nullwelt, **und** ihr Spiegel nicht? Kurzer Lauf auf vollen Daten (*lange Messung nur nach Vorprüfung*) |
| **S2** | **Stufe 2 voll**, nur für Zellen, die S1 bestehen | Einmal bestätigt auf 2025 und 2026 getrennt; je Asset; Weglassprobe (ohne BTC/ETH, ohne die 10 größten); Mehrfachtesten; Spiegelprobe auf dem Ereignis (Lift, Schwelle **1,717**); Klima-Achse und Marktbreite als **Gewicht** |
| **S3** | SPOT-REGEL0 **festschreiben** | Parameter und Referenzzahlen, eine Konstante im Code, Wache |
| **S4** | **Betriebsprüfung B1–B9** (E-35) | Tageskerzen am NB aus `stundenkurse_alle.db` (laufend, Job `regel0_nachlader`) gegen die Messbasis: **R-R11 der Tagesschlüsse**; Bitpanda-Spotliste; Kosten (M-1) |
| **S5** | Messung auf **deiner Spot-Liste** (Bitpanda-Bestand) | analog 2.700 |
| **S6** | **REGEL1 … n** | Ausstiegsform (Trailing, Teilverkauf bei *überhitzt*, = M-5), Positionsgröße aus dem Klima, Nachkauf |
| **S7** | Betriebsvorbereitung | Mail samt **Klima-Ampel** (a), Tab, LLM-Rolle (kennt die Wette, P1-Lehre), Testwoche, F5 analog |
| **S8** | Umstellung | ersetzt die alte Spot-Kette, kein Parallelbetrieb; O24 stoppt rechtzeitig die alten LLM-Aufrufe |

Es gelten die Trennungsregeln T-1 bis T-6 (Spot am Desktop, kein Betriebscode bis S7, Hebel hat Vorrang).

### 9.3 Messplan Stufe 1 — VOR dem Lauf festgelegt

- **Messbasis:** `messdaten.db`, Krypto, eingestellte eingeschlossen (unverzerrt, 2.669). Nur lesend. Ereignisse **2024** (Wahljahr); 2025–26 wird in S1 **nicht** angesehen.
- **Ereignisse:**
  - T, T′, R, R′ wie in der Tabelle oben; Ruhe je Asset.
  - **Einstieg zum Schluss von t+1**: der Tagesschluss von t ist erst danach bekannt.
- **Ausstiege, vier je Familie:**
  - fest nach **10, 20, 60 T**;
  - **Bruch**: erster Schluss unter S50, höchstens 120 T;
  - bei R: erster Schluss über S50, höchstens 120 T (*Gegenbewegung erreicht*).
- **Zielgröße — Vorteil je Handel:**
  - log-Ertrag des Handels minus Mittel der **Nullwelt**: 20 Zufallseinstiege **desselben Assets im selben Monat** mit derselben Ausstiegsregel. Damit fällt die **Drift** heraus (Nullpunkt = Drift).
  - Tagesklammer: erst je Tag gemittelt, dann über die Tage.
- **Bestehen (eine Zelle = Familie × Ausstieg, 4 × 4 = 16 Zellen, für den Spiegel nur zur Gegenprobe):**
  1. Vorteil > 95. Perzentil der Nullwelt-Verteilung (200 Ziehungen der Zufallseinstiege) **und**
  2. Der Spiegel derselben Zelle ist **nicht ebenso** über seiner Nullwelt. Sonst wäre es Bewegung, nicht Richtung.
- **Mehrfachtesten:** 8 echte Zellen bei 5 % lassen **~0,4 Zufallstreffer** erwarten. Eine einzelne bestandene Zelle ist deshalb nur ein **Kandidat für S2**, kein Befund.
- **Kosten:** Ausgewiesen werden der **Rohvorteil** und die **Kostenschwelle**, bei der er null wird. Der Bitpanda-Spotsatz ist nicht belegt (M-1).
- **Auskunft:** Zahl der Handel, je Asset der Anteil positiver Vorteile, mittlere Haltedauer.
- **Folge, vorab:**
  - Mindestens eine Zelle besteht: **S2** für genau diese Zellen.
  - Keine besteht: **WORAN messen** (E-63, Ursache vor Form), z. B. Dauer, Klima, Marktbreite. Ein Anlauf auf dieselben 2024-Daten zählt dann nur noch als Beschreibung.

### 9.4 Korrektur meines Vorschlags §9 (05.10.2026, E-66)

- Die Haltedauern in §9.3 (10, 20, 60 T, höchstens 120 T) **passen nicht** zu deinem Horizont (Altcoins: Monate bis 1–2 Jahre). Ich habe das Muster des Hebels übernommen, ohne den Horizont zu prüfen.
- Ein Ereignis-Ansatz auf diesem Horizont hat ein anderes Fallzahlproblem (§10.4). SPOT-REGEL0 und Stufe 1 **ruhen**, bis G1 entschieden ist.

## 10. G1 — Was unterscheidet Spot von der Akkumulation? Diskussionsgrundlage (05.10.2026; E-66)

Nutzer 05.10.: *„Spot-Thema müssen wir offen diskutieren und abstimmen – das geht nicht in ein paar Zeilen: Was soll Spot zur Akkumulation der Kernwerte BTC etc. unterscheiden? Also ein Vergleich, ob die aktuelle Akkumulation überhaupt Sinn ergibt oder wir darauf aufsetzen können – eher nicht. G1 ist der erste Punkt, an dem wir starten werden und diese fachlich und technisch bewerten müssen, damit wir überhaupt etwas festlegen können. Der Zeithorizont geht von ein paar Monaten eher über 1–2 Jahre bei Altcoins Spot, und Akkumulation kann über mehrere Zyklen gehen (mit Teilverkauf, Kernwerte).“*

**Wozu dieser Abschnitt:**
- Er ist **keine Vorlage zum Abhaken**, sondern die fachliche und technische Grundlage für ein Gespräch.
- Er knüpft an den **Richtungsentscheid vom 24.09.** an (`Konzept_Hebel_als_eigenes_Geschaeft_24_09.md`, Befund 2.577): **drei Geschäfte**, Hebel, Akkumulation, Spot, in dieser Reihenfolge. Die *Lage* = (Instrument, Strategie) ist Eingang, nicht Ausgang.
- Akkumulation ist dort eine **Strategie**, Spot ein **Instrument mit eigener Absicht**. Das ist das bestehende Schema, kein neues.

### 10.1 Die zwei Geschäfte nebeneinander

| | **Akkumulation (Kernwerte)** | **Spot (Altcoins)** |
|---|---|---|
| Zweck | Vermögen über **mehrere Zyklen** aufbauen und halten | **Mehrertrag** in einer begrenzten Zeit |
| Assets | wenige Kernwerte (BTC, ETH; SOL zu klären) | viele, wechselnd; viele werden eingestellt |
| Horizont (Nutzer) | mehrere Zyklen, Jahre | einige Monate bis 1–2 Jahre |
| Einstieg | laufend, der Zufluss ist Kapital (Regel 1) | ein **Anlass** (Lage, Wende, Ereignis) |
| Ausstieg | **Teilverkauf** in Überhitzung, Rest bleibt | **Ausstieg** am Ziel oder bei Bruch, Position ganz zu |
| Risiko | Drawdown −75 bis −85 % je Zyklus, aber Erholung bisher immer | **Totalverlust** möglich; Überlebensverzerrung |
| richtiger Maßstab | **regelmäßiges Kaufen** desselben Kernwerts mit gleichem Kapital | ⭐ **BTC halten** im selben Zeitraum: Spot lohnt nur, wenn es den Kernwert schlägt. In USD reicht nicht |
| Fallzahl für eine Messung | 4–5 Zyklen → **beschreibend** (F1–F3) | viele Assets, aber auf 1–2 Jahre **wenige unabhängige Zeitfenster** (§10.4) |
| Rolle des Klimas | Teilverkauf (*überhitzt*) und Fakt in der Mail | **Achse**: ob Altcoins überhaupt laufen (Breite, Altcoin-Saison) |
| Wer entscheidet wie viel | der Nutzer (S-b) | der Nutzer; das System liefert *welches* und *wann* |

⚠️ **Der wichtigste Unterschied ist der Maßstab.** Akkumulation muss nur regelmäßiges Kaufen erreichen oder knapp schlagen. Spot muss **den Kernwert schlagen**, sonst wäre dasselbe Geld in BTC besser aufgehoben. Damit ist Spot die strengere Frage.

### 10.2 Wie steht die heutige Akkumulation? (fachlich)

| Ebene | Befund | Quelle |
|---|---|---|
| **im System** | Die Akkumulationszelle fällt **immer** an `lage_gesperrt` und liefert **null Kaufsignale**. Die taktische Zelle scheitert an der Geometrie | V-1 §1, 2.540 |
| **Kaufseite fachlich** | Gegen regelmäßiges Kaufen gewinnt **keine** Klima-Regel (F2 warten, F3 gewichten; BTC und ETH; alle Epochen). Regelmäßiges Kaufen ist damit die **begründete Grundlage** der Kaufseite | §8.9, §8.11 |
| **Verkaufsseite** | **ungemessen.** Teilverkauf über Zyklen ist die offene Frage, und genau dort könnte die Akkumulation über regelmäßiges Kaufen hinauskommen | M-5, §8.11 (b) |
| **dein tatsächliches Kaufen** | **ungemessen.** Wie deine Käufe aus dem Bitpanda-Buch gegen regelmäßiges Kaufen dastehen, weiß ich nicht | Vorschlag G1-M1 |
| Stop-Nachzieh 07:15 | zieht auch für Spot-Bestand Stops nach, obwohl *Spot hat keinen Stop* entschieden ist | O19 |

**Meine Einschätzung zu *„eher nicht“*:** Als **System** gibt es heute keine Akkumulation, auf die man aufsetzen könnte. Als **Kaufregel** ist regelmäßiges Kaufen gemessen nicht zu schlagen; das ist eine Grundlage, aber noch kein Geschäft. Was fehlt, sind der **Teilverkauf** und die **Gewichtung der Kernwerte**.

### 10.3 Wie steht Altcoin-Spot? (fachlich)

| | Befund | Was er für deinen Horizont sagt |
|---|---|---|
| alte Kette | kauft seit 2025 nur in den Verlust nach (V-2) | ersetzen |
| M-0 Querschnitt | 6 Merkmale × 20/90 T: nichts trägt; *niedrige Schwankung* lag umgekehrt am unteren Rand (Auskunft) | gemessen **kürzer** als dein Horizont |
| M-0 L3 | REGEL0-Einstieg 72/120/480 h: nichts | ebenfalls kürzer |
| F3 | Der Trend über ein Jahr schlägt die Rückkehr zum Mittel (BTC) | spricht für **Trendfolge** über Monate, nicht für antizyklisches Altcoin-Kaufen |
| **Grundrate Altcoin gegen BTC** über 6–24 Monate | ⭐ **ungemessen.** Bekannt aus der Recherche: die Mehrheit der Altcoins verliert über Jahre gegen BTC, viele werden eingestellt | das ist die **erste** Frage: Gibt es überhaupt etwas zu holen? |

### 10.4 Technische Bewertung

| | Akkumulation | Spot (Altcoins) |
|---|---|---|
| **Messdaten** | BTC/ETH täglich ab 2010/2015 (CoinMetrics, Desktop), Klima vorhanden | `messdaten.db` täglich ab 2017, 537 Symbole **mit eingestellten**: nötig gegen die Überlebensverzerrung |
| **Fallzahl** | 4–5 Zyklen, eine Regel ist nur beschreibbar | Auf 1–2 Jahre gibt es seit 2019 je Asset nur 3–7 **unabhängige** Fenster. Altcoins laufen gemeinsam, deshalb ist die wirkliche Fallzahl die Zahl der **Marktphasen**, nicht der Assets. ⚠️ Dasselbe Problem wie beim Klima, nur abgeschwächt |
| **Betrieb am NB** | Kurse ✔; MVRV/Klima am NB **ungeprüft** (CoinMetrics ist dort nur für Börsenflüsse angebunden) | Die Betriebskopie `messdaten.db` hat nur **500 Tage**; Merkmale über 200 Wochen fehlen dort. Die Stundenkurse ab 2023 laufen laufend ✔ |
| **Kosten** | gering je Jahr (wenige Käufe) | bei Monaten Haltedauer nachrangig; Bitpanda-Spotsatz trotzdem unbelegt (M-1) |
| **Bestand und Teilverkauf** | Bitpanda-Bestand und Einstand werden abgeglichen ✔ | dto. |
| **Ablösung der alten Kette** | R-4 vorhanden (Umfang A/B offen) | dto. |

### 10.5 Die Punkte für unser Gespräch (offen, keine Ja/Nein-Fragen)

| # | Punkt | worum es geht |
|---|---|---|
| D1 | **Welche Kernwerte**, und mit welchem Gewicht? | BTC allein, BTC+ETH, SOL dazu? Fester Mix oder gewichtet? |
| D2 | **Was soll der Teilverkauf leisten?** | Gewinne sichern, Risiko senken, Geld für den nächsten Boden bereitlegen oder in Altcoins umschichten? Davon hängt ab, **woran** er gemessen wird |
| D3 | **Soll Spot BTC schlagen müssen?** | ⭐ Mein Vorschlag: ja, als Maßstab. Sonst ist es Risiko ohne Mehrwert |
| D4 | **Darf Altcoin-Spot ganz entfallen**, wenn die Grundrate gegen BTC nichts hergibt? | eine ehrliche Option, die vorab feststehen sollte |
| D5 | **Kapital je Geschäft** | Töpfe heute: Spot 4.000, Hebel 3.000 EUR. Hat die Akkumulation einen eigenen Topf? |
| D6 | **Deine Rolle** | Ob und wie viel bei dir (S-b). Was genau soll das System liefern: Ampel, Kandidaten, Teilverkaufs-Hinweis? |

### 10.6 Messungen, die G1 fachlich entscheidbar machen — Vorschlag, nicht gestartet

| # | Messung | beantwortet | Aufwand |
|---|---|---|---|
| **G1-M1** | **Deine Akkumulation aus dem Bitpanda-Buch** gegen regelmäßiges Kaufen mit gleichem Kapital und Zeitraum, dazu die tatsächlichen Kosten (= M-1) | *ergibt die heutige Akkumulation Sinn?* (dein *eher nicht*) | klein, Desktop |
| **G1-M2** | **Grundrate Altcoins gegen BTC** über 90/180/365/730 T: Verteilung, Anteil besser als BTC, Totalverluste; mit eingestellten Werten, je Epoche (E1/E2/E3) | *gibt es bei Altcoin-Spot überhaupt etwas zu holen?* | klein, Desktop |
| **G1-M3** | **Teilverkauf über Zyklen** bei BTC/ETH: z. B. ein Anteil bei *überhitzt*, Rückkauf in der Zone, gegen reines Halten. Beschreibend, 4–5 Zyklen | *bringt der Teilverkauf etwas, und wie viel kostet er im Aufwärtstrend?* | mittel |
| **G1-M4** | **Fallzahl auf deinem Horizont:** wie viele unabhängige Phasen tragen eine Spot-Regel auf 6–24 Monate | *ist eine Spot-Regel überhaupt messbar, oder bleibt nur Beschreibung?* | klein |

**Reihenfolge:** M1 und M2 zuerst. Sie sind schnell und rein **beschreibend**, mit kleinem Mehrfachtest-Risiko. Je nach Ergebnis M3 und M4. Jede bekommt vorher einen Messplan zur Abstimmung (Pflichtablauf).

### 10.7 Messplan G1-M1 und G1-M2 — VOR dem Lauf festgelegt (05.10.2026; Nutzer: *„zuerst G1-M1 und M2 messen, prüfen und gegenprüfen“*)

Beide Messungen sind **beschreibend**: Es wird keine Regel gewählt und keine Schwelle gesetzt. Gemessen wird nur am Desktop und nur lesend.

#### G1-M1 — dein tatsächliches Handeln aus dem Bitpanda-Buch

- **Daten:**
  - `Austauschordner/Notebook_Analysedaten/bitpanda_transaktionen.json` (Spot-Trades 13.09.2024 bis 01.08.2026, 6.149, alle in EUR). ⚠️ August bis Oktober 2026 fehlen; die Datei ist vom 03.08.
  - Kurse: Kraken EUR täglich (`tradinginfotool.db`, bis 19.07.2026); danach CoinMetrics USD × Wechselkurs vom 19.07.; für Altcoins `messdaten.db` USD.
- **Stichtag** 01.08.2026 (letzter Trade).
- **Menge:**
  - Mengen aus den Trades (Käufe − Verkäufe); Staking, Belohnungen und Umbuchungen zählen nicht, weil ihnen kein Geldfluss gegenübersteht.
  - Stablecoins (EURCV, EURC, USDC, USDT …) sind ausgenommen.
  - Werte ohne Kursreihe (Aktien, ETF, nicht bei Binance gelistete) werden nur gezählt (Anzahl, EUR-Umsatz).
- **Teil A — Kernwerte BTC und ETH:**
  - **A1 Kaufqualität:** EUR-gewichteter Durchschnittskaufpreis ÷ Durchschnittspreis bei täglich gleichem Betrag im selben Zeitraum (harmonisches Mittel der Tagesschlüsse vom ersten bis letzten Kauf). < 1 heißt billiger gekauft als regelmäßiges Kaufen.
  - **Nullwelt:** dieselben Beträge an zufälligen Tagen desselben Zeitraums, 1.000-mal; ausgewiesen wird der Rang.
  - **A2 Verkaufsqualität:** EUR-gewichteter Durchschnittsverkaufspreis ÷ arithmetisches Mittel der Tagesschlüsse im Verkaufszeitraum (> 1 heißt teurer verkauft). Dazu *Halten statt Verkaufen*: Wert der verkauften Menge am Stichtag gegen den Erlös.
  - **A3 Ergebnis:** Ergebnis in EUR (Erlöse + Bestandswert − Käufe) gegen zwei Gegenwelten:
    - (i) *dieselben Käufe, nie verkauft*;
    - (ii) *regelmäßiges Kaufen*: dasselbe **Netto**kapital (Käufe − Verkäufe, falls > 0) gleichmäßig monatlich vom ersten Monat bis zum Stichtag.
- **Teil B — Altcoin-Spot gegen BTC, je Coin mit Kursreihe:**
  - Methode **PME** (*public market equivalent*, Kaplan/Schoar): Jeder Geldfluss wird am selben Tag in BTC gespiegelt. Ein Kauf von x EUR Coin entspricht einem Kauf von x EUR BTC, ein Verkauf einem Verkauf von x EUR BTC.
  - **Vorteil gegen BTC** = Ergebnis Coin − Ergebnis BTC-Spiegel.
  - Restbestand zum Stichtagskurs. Fehlt der Kurs, gilt der letzte eigene Tradepreis; das wird gezählt und ausgewiesen.
  - Ausgewiesen werden die Summe, der Anteil der Coins vor BTC und die 10 größten Beiträge in beide Richtungen.
- **Kosten (M-1):**
  - Tradepreis ÷ Tagesschluss − 1, getrennt nach Kauf und Verkauf, Median und Quartile, für BTC, ETH und alle Kraken-EUR-Werte.
  - Geschätzte **Kosten je Hin- und Rückweg** = Median beim Kauf − Median beim Verkauf. Die Tagesbewegung mittelt sich über viele Trades heraus; das ist eine Schätzung mit Streuung.

#### G1-M2 — Grundrate Altcoins gegen BTC

- **Daten:** `messdaten.db`, Krypto, USD, **mit eingestellten Werten** (unverzerrt), 2017–2026-09-20.
- **Ausgenommen:**
  - BTC selbst;
  - Stablecoins: Median der täglichen Bewegung unter 0,2 %;
  - Hebeltoken mit den Endungen UP, DOWN, BULL, BEAR.
- **Starts:** jeder Monatserste ab 01.2019. **Horizonte:** 90, 180, 365, 730 T.
- **Je Coin mit Kurs am Start:** relativer Ertrag gegen BTC = (P(t+h)/P(t)) ÷ (BTC(t+h)/BTC(t)) − 1.
  - Endet die Reihe vor t+h (eingestellt), gilt der **letzte Kurs** und das Ereignis wird gezählt. Das ist eher zu günstig für den Coin, weil Einstellungen oft nahe null erfolgen.
- **Ausgewiesen je Epoche (E1 Start 2019–2020 · E2 2021 bis 10.01.2024 · E3 ab 11.01.2024) und Horizont:**
  - Median des relativen Ertrags;
  - Anteil vor BTC;
  - Ertrag eines gleich gewichteten Korbs aller Altcoins gegen BTC (Mittel je Start, dann Median über die Starts);
  - Anteil mit −50 % und −90 % in USD;
  - Anteil eingestellt;
  - **Zahl unabhängiger Starts** (nicht überlappend: Abstand ≥ h).
- **Auskunft:**
  - ETH getrennt;
  - nur die liquidere Hälfte (30-T-Umsatz am Start über dem Median);
  - nur deine gehandelten Coins.

#### Was daraus folgt (vorab)

- **M1 und M2 sind die Faktenbasis für das Gespräch G1** (D1–D6). Sie entscheiden nichts automatisch.
- **G1-M2 an die Frage D4 geknüpft:** Liegt der Anteil vor BTC auf 365 und 730 T in **allen drei** Epochen unter 50 % **und** der Korb-Median unter 0, dann gibt es **als Grundrate** bei Altcoin-Spot nichts zu holen. Ein Spot-Weg müsste dann eine Auswahl nachweisen, die diese Grundrate deutlich schlägt; sonst gilt D4 (Spot entfällt) als ernsthafte Option.

### 10.8 Ergebnis G1-M1 und G1-M2 (05.10.2026, nach dem vorab festen Plan §10.7)

Belege `Spot_Voranalyse_04_10/g1_m1_eigenes_handeln.py` / `g1_m2_grundrate_altcoins.py`, jeweils mit `.txt`, dazu die Gegenproben `g1_m1_gegenprobe.py` und `g1_m2_gegenprobe.py`.

#### Zwei Datenbefunde beim Prüfen (vor der Auswertung behoben)

1. **Die Liste `trades` enthält die Hebel-Eröffnungen.** Bei BTC sind 39 von 79 „Käufen“ in Wahrheit `margin_trading.open`. Maßgeblich ist deshalb `transaktionen`, nur Kauf und Verkauf **ohne** Margin-Markierung; das schließt 3.908 Hebelbuchungen aus.
2. **Coins aus geschlossenen Hebelpositionen** werden danach als **normale** Verkäufe gebucht: netto aus Spot TAO −68, LINK −622, SUI −3.495. Für Coins, die je gehebelt wurden (BTC, ETH und 9 Altcoins), sind Verkäufe und Restmengen **nicht belastbar**. Belastbar sind dort nur die Kaufqualität und die 50 Coins, die **nie** gehebelt wurden.
- ⚠️ Das berührt den bekannten Importer-Befund 2.679 (Hebelpositionen falsch eingeteilt): Aus den Bitpanda-Daten lassen sich Spot und Hebel **nicht** über die Markierung allein trennen.

#### G1-M1 — dein Handeln (13.09.2024 bis 01.08.2026)

| | Ergebnis | belastbar? |
|---|---|---|
| **BTC Kaufqualität** | 40 Spot-Käufe zu Ø 58.647 EUR gegen 76.149 EUR bei täglich gleichem Betrag: **0,770**. Zufallstage: Median 1,01, **Rang 0,00**, besser als jeder Zufallszug | ✔ |
| **ETH Kaufqualität** | 30 Käufe zu Ø 2.687 gegen 2.260 EUR: **1,189**, Rang 0,98, schlechter als fast jeder Zufallszug | ✔ |
| **SOL Kaufqualität** | 1,003, Rang 0,44: neutral | ✔ |
| BTC/ETH Verkäufe und Ergebnis | enthalten Hebel-Schließungen | ✗ |
| **Altcoin-Spot gegen BTC** (PME, 50 nie gehebelte Coins, Käufe 77.694 EUR) | Ergebnis **−46.573 EUR**; dieselben Geldflüsse in BTC **−16.525 EUR**; **Vorteil gegen BTC −30.048 EUR**. Nur **6 von 50** Coins vor BTC (nach Volumen 7 %) | ✔ (6 mit Notbewertung) |
| Auskunft Stichtag 20.09. | Vorteil gegen BTC **−39.463 EUR** (Restmengen unverändert angenommen) | Auskunft |
| ohne Kursreihe | 68 Coins, 34.875 EUR Umsatz (DEAI, TAI, ORAI …), nicht bewertet | — |
| **Kosten (M-1)** | Hin- und Rückweg: **BTC 0,56–0,81 %**, **Altcoins 2,48–2,49 %** (gegen Tagesschluss bzw. Tagesmitte, n 693/502). ETH ist unsicher (−0,51 / +2,76 %, n 29/42) | ✔ als Schätzung |

**Gegenprobe:** A1 BTC unabhängig 0,770. PME für XLM, KAS, APT und INJ am 13.07. gleich: +391/+390, −1.585, −1.638, −1.392 EUR.

#### G1-M2 — Grundrate Altcoins gegen BTC (525 Altcoins, davon 186 eingestellt)

| Epoche | 365 T: Median · vor BTC · Korb | 730 T: Median · vor BTC · Korb | unabh. Starts 365/730 |
|---|---|---|---|
| **E1 2019–2020** | −10,5 % · 46 % · **+72,8 %** | −7,3 % · 48 % · **+726 %** | 2 / 1 |
| **E2 2021–10.01.2024** | −45,8 % · 17 % · −27,0 % | −74,9 % · 8 % · −58,0 % | 4 / 2 |
| **E3 ab 11.01.2024** | **−67,1 % · 6 % · −56,8 %** | **−86,4 % · 4 % · −72,0 %** | 2 / 1 |

- **Auskunft:**
  - Die liquidere Hälfte zeigt dasselbe Bild.
  - Deine gehandelten Coins liegen etwas besser, aber E3 365 T: 10 % vor BTC, Korb −46,9 %.
  - ETH gegen BTC: E1 vorn (+56 % / +146 %), E2 −13 % / −33 %, E3 −8 % / −42 % (0 von 8 vor BTC auf 730 T).
- **Gegenprobe:**
  - Starts 2022-01-01 (298 Coins, −51,0 %, 13 % vor BTC) und 2024-02-01 (366 Coins, −65,3 %, 6 %) unabhängig gleich.
  - Der positive E1-Korb kommt aus wenigen Extremgewinnern der Altcoin-Saison 2021 (FTM ×515, MATIC ×190, DOGE ×113 …). Er bleibt **ohne** die drei Coins mit Verdacht auf Token-Umstellung (COCOS ×5.322, DREP, NPXS) positiv (+27,5 % / +117 %). Mit dem **Median** statt dem Mittel im Korb ist er negativ (−25,8 % / −8,9 %).
- **Folge nach der vorab festen Regel:** **NEIN, 4 von 6 Zellen.** E1 erfüllt die Bedingung nicht, weil ihr Korb positiv ist. Formal schließt die Grundrate Altcoin-Spot damit nicht aus.
- ⚠️ **Ehrlich dazu:** Nach der stehenden Vorgabe *Messfokus ab 2023/2024, ältere Jahre nur Auskunft* wäre E1 nur Auskunft. Dann wäre die Bedingung in **allen** übrigen Zellen erfüllt (E2, E3). Die Regel ist vorab so festgelegt, wie sie steht; die Lesart gehört ins Gespräch G1.

#### Was daraus für G1 folgt — und was nicht

| | |
|---|---|
| **Der typische Altcoin verliert gegen BTC** | in **jeder** Epoche und auf **jedem** Horizont, im ETF-Markt (E3) massiv: nach einem Jahr nur 6 % vor BTC, nach zwei Jahren 4 % |
| **Gewinn nur als Lotterie** | Ein breiter Korb schlug BTC nur 2019–2021, getragen von wenigen 50- bis 500-fachen Gewinnern. Seit 2021 verliert selbst der Korb |
| **Dein Altcoin-Spot** | hat gegen dieselben Geldflüsse in BTC rund **30.000 EUR** verloren; 6 von 50 Coins lagen vorn. Dazu kommen rund **2,5 %** Kosten je Hin- und Rückweg |
| **Deine BTC-Käufe** | ⭐ waren **gut getimt** (0,77, besser als jeder Zufallszug), deine ETH-Käufe schlecht (1,19). Für die Akkumulation heißt das: Das Kaufen der Kernwerte kann **schlechter oder besser** als regelmäßiges Kaufen laufen, je nach Wert |
| ⚠️ **Nicht** folgt | dass Altcoin-Spot **nie** trägt: E3 ist im Grunde **eine** Marktphase (1–2 unabhängige Fenster). Eine neue Altcoin-Saison ist nicht ausgeschlossen, aber **nicht belegt** |
| ⚠️ **Nicht** belastbar | deine BTC/ETH-**Verkäufe** und Ergebnisse, weil sie mit dem Hebel vermischt sind; die Daten nach dem 01.08. fehlen |

## 11. Breiter denken — das Schichtenmodell für Krypto-Spot und Akkumulation (05.10.2026; E-67)

Nutzer 05.10.: *„Schalter A setzen, dann mit D1 und D2 starten. Wichtig: Wenn wir alles anhalten, brauchen wir Alternativen. Zuerst bauen wir Krypto fertig, dann die Multiasset-Schiene. Deine Anmerkung zu BTC und Altcoins finde ich gut – aber meines Erachtens ist das ein Auftrag für das Regelwerk: Welche Spotwerte, mit welcher Diversifikation bringen mehr Rendite und schlagen BTC. Schwierig – OB und WIEVIEL Rendite über Altcoins möglich ist, hängt am Zeitpunkt des Kaufes; meistens ist antizyklisch kaufen und auch korrekt verkaufen zielführend, manchmal können kurzfristige Einstiege kurz nach dem Bärenmarkt oder bei Korrekturen die bessere Wahl sein. Ich denke, wir müssen etwas breiter denken, wie wir die Probleme angehen können.“*

### 11.1 Meine Einschätzung als Fachmann

**Du hast recht, und unsere Messungen stützen das:**
- Die Grundrate der Altcoins hängt stark an der **Marktphase**: Ein Korb lag 2019–2020 vorn, 2021–2026 klar hinten (§10.8).
- Beim Hebel war das **Regime zwölfmal wichtiger als die Lage** (2.598).
- Ob es bei Altcoins etwas zu holen gibt, entscheidet also zuerst **das Wann**, erst danach **das Welche**.

**Die Schwierigkeit, ehrlich:**
- Phasen sind **selten**. Seit 2019 gab es eine echte Altcoin-Saison, und der Marktzustand war vorab nicht besser als Zufall zu erkennen (2.599).
- Das Klima erkennt den Boden, meldet die Wende aber erst 30–78 Tage später (§8.7).
- **Eine Regel, die die Phase vorhersagt, ist mit unseren Daten nicht belegbar.**

**Daraus folgt der Ansatz: zwei Arten von Fragen trennen.**

| | Fragen **über die Phase** | Fragen **innerhalb einer Phase** |
|---|---|---|
| Beispiele | Beginnt eine Altcoin-Saison? Ist das der Boden? | Welche Coins? Wie breit streuen? Antizyklisch oder nach der Korrektur einsteigen? Wann verkaufen? |
| Fallzahl | wenige Phasen | **viele**: Hunderte Coins × viele Tage je Phase |
| Behandlung | **Fakt und Ampel**, du gewichtest (S-b, *übergeordnete Kräfte gewichten*) | **messbar**, mit Nullwelt, je Phase getrennt, Maßstab **BTC halten** |

### 11.2 Das Schichtenmodell — Vorschlag für das Spot-Regelwerk Krypto

| Schicht | Frage | Messbarkeit | bisheriger Stand |
|---|---|---|---|
| **S1 Klima und Phase** | BTC-Zyklus (Zone, Wende, überhitzt) und **Altcoin-Phase** (BTC-Dominanz im Trend, ETH/BTC, Breite) | beschreibend, Fakt | Klima gebaut (§8); Altcoin-Phase noch nicht |
| **S2 Akkumulation der Kernwerte** | D1 welche und wie gewichtet, D2 Teilverkauf | wenige Zyklen, beschreibend; Kaufseite gemessen | regelmäßiges Kaufen ist nicht zu schlagen (F2/F3); deine BTC-Käufe 0,77 |
| **S3 Auswahl der Altcoins** | Welche schlagen BTC **innerhalb** der Phase: relative Stärke gegen BTC, Liquidität, Überleben? | **gut messbar** (Querschnitt je Phase) | M-0 auf 20/90 T nichts; auf deinem Horizont ungemessen |
| **S4 Einstiegsform** | (a) antizyklisch in der Zone · (b) **früh nach Bärenmarkt oder Korrektur im Aufwärtstrend** (deine Idee) · (c) Ereignis je Asset | gut messbar als Ereignis × Phase | (a) gemessen ohne Auswahl; (b) ungemessen |
| **S5 Ausstieg und Teilverkauf** | Bei Altcoins **entscheidend**, weil die Gewinne sonst zurückgegeben werden (E2/E3) | messbar je Ereignis | ungemessen |
| **S6 Streuung und Größe** | Die Gewinne kamen als **Lotterie**, von wenigen 100- bis 500-fachen Coins: viele kleine Positionen mit konsequentem Ausstieg oder wenige große? | gut messbar (Korb-Simulation) | ungemessen |

⭐ **Der Kern für Altcoin-Spot ist die Verbindung S3 × S4 × S5 × S6 innerhalb einer Phase**, gemessen gegen BTC halten nach Kosten (~2,5 % je Hin- und Rückweg). Das ist wie beim Hebel: *der Einzelbeitrag ist schwach, die Kombination ist die Anwendung*.

### 11.3 Reihenfolge (Nutzer: Krypto zuerst, dann Multiasset)

1. **S2 Akkumulation (D1, D2):** jetzt im Gespräch.
2. **S1 Altcoin-Phase** als Fakt dazubauen: BTC-Dominanz, ETH/BTC, Breite. Die Daten sind da.
3. **S3–S6 gemeinsam** als Korb-Simulation je Phase (E1/E2/E3 getrennt), mit eingestellten Werten, Kosten und Maßstab BTC.
   - Erst das zeigt, ob deine Einstiegsform (b) und eine Streuung die Grundrate schlagen.
   - Ein Messplan dafür kommt vorab zur Abstimmung.
4. Danach die **Multiasset-Schiene**.

### 11.4 Alternativen für die angehaltene Kette (O27)

| weggefallen (Schalter A) | Ersatz |
|---|---|
| Krypto KAUFEN/NACHKAUFEN | **bewusst nichts.** NACHKAUFEN war gemessen schädlich (V-2), dein Altcoin-Spot −30.048 EUR gegen BTC |
| Krypto-Verkaufs- und Bestands-Sammelmail | ⭐ **Übergangsvorschlag: eine Fakt-Mail *Bestand und Klima*** (täglich oder wöchentlich). Inhalt: Klima-Ampel BTC (Zone, Wende, überhitzt), Kernwerte (MVRV-Perzentil, Abstand zum Hoch), jeder Altcoin im Bestand **gegen BTC seit Kauf**. **Kein Auslöser**, nur Fakt. Baubedarf: MVRV am NB (CoinMetrics ist dort für Börsenflüsse schon angebunden) |
| Führung echter Hebelpositionen (alte Kette) | Für REGEL0-Trades gibt es die Ausstiegserinnerung. **Manuelle** Hebelpositionen außerhalb der REGEL0 haben bis O13 keine Führungsmail; heute ist keine offen |
| Aktien, Rohstoffe, ETF, Absicherung | ruhen bis zur Multiasset-Schiene. Bitpanda-Abgleich und Stop-Nachzieh 07:15 laufen weiter |

### 11.5 Einstieg in D1 und D2 — die Fakten, die wir haben

**D1 — welche Kernwerte, wie gewichtet?**

| Fakt | Quelle |
|---|---|
| ETH gegen BTC: 2019–2020 vorn (365 T +56 %, 730 T +146 %), **seit 2021 hinten** (E2 −13/−33 %, E3 −8/−42 %, 0 von 8 Starts vorn auf 730 T) | G1-M2 |
| Deine Kaufqualität: BTC **0,77** (sehr gut), ETH **1,19** (schlecht), SOL 1,00 | G1-M1 |
| Dein Bestand am 01.08.: BTC 0,05, ETH 0,96 (überwiegend gestakt), SOL 5,9 (gestakt) | Bitpanda |

- **Mögliche Formen:** (i) nur BTC · (ii) BTC und ETH fest, z. B. 70/30 · (iii) BTC, ETH, SOL · (iv) dynamisch nach relativer Stärke (dann ist es schon Auswahl, S3).
- ⚠️ Seit 2021 hat BTC allein alles andere geschlagen. Das ist **eine** Phase; eine Gewichtung von ETH oder SOL ist deshalb eine **Bewertung, kein Fakt**.

**D2 — was soll der Teilverkauf leisten?** Der Zweck bestimmt den Maßstab:

| Zweck | Maßstab |
|---|---|
| (a) Risiko senken | kleinerer größter Rückgang bei vertretbarem Ertragsverzicht |
| (b) Geld für den nächsten Boden | Endbestand **in BTC-Stück** (mehr Stück durch Rückkauf in der Zone) |
| (c) Umschichten in Altcoins in einer Altcoin-Saison | Ertrag gegen BTC halten (S1 × S3) |
| (d) Gewinne entnehmen | gesicherter EUR-Betrag |

⚠️ Aus F3 bekannt: *überhitzt* kam 2017, 2021 und 2024 **früh**; danach stieg der Kurs weiter. Ein Teilverkauf muss deshalb **gestaffelt** sein. Ein Rückkauf in der Zone ist Teil der Regel, nicht nachgelagert.

## 12. Messplan D1-M und D2-M — Kernwerte und Teilverkauf, VOR der Messung (06.10.2026; E-68)

Nutzer 06.10.: *„D1 – BTC, ETH und Solana. D2 – ja b und d jedenfalls, a und c eher später, denke ich. Messplan für alle relevanten Fälle.“*

### 12.1 Vorprüfung (keine Erträge; `Spot_Voranalyse_04_10/d_vorpruefung.py`)

- **Kurse:** BTC und ETH aus CoinMetrics (ab 2010 bzw. 07.2015, bis 04.10.2026); SOL aus `messdaten.db` (ab **11.08.2020**, bis 20.09.2026).
- **Klima q (BTC, wie F3)**, Tage über der Stufe:

| Jahr | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| max q | 0,49 | 0,86 | **0,98** | 0,92 | 0,72 | 0,92 | **0,97** | 0,66 | 0,49 | 0,86 | 0,84 | 0,49 |
| Tage ≥ 0,80 / 0,90 / 0,95 | 0 | 6/0/0 | **325/171/72** | 14/2/0 | 0 | 43/6/0 | **175/77/14** | 0 | 0 | 45/0/0 | 53/0/0 | 0 |
| Tage ≤ 0,20 (Zone) | 263 | 0 | 0 | 42 | 105 | 9 | 0 | 215 | 175 | 0 | 0 | 116 |

⚠️ **Im ETF-Markt (2024–25) kam q nie über 0,86.** Stufen ab 0,90 hätten dort nie ausgelöst. Deshalb gehört eine Variante **nur mit der ersten Stufe** in den Plan. Die 0,80 aus 2020 lag vor dem Anstieg 2021, das ist das bekannte Risiko *zu früh*.

### 12.2 D1-M — Gewichtung der Kernwerte (Aufbau durch regelmäßiges Kaufen, gemessen nicht schlagbar, F2/F3)

| | |
|---|---|
| **Zeitraum** | gemeinsam ab **01.09.2020** (SOL) bis 20.09.2026. Auskunft: BTC/ETH ab 2017 |
| **Mischungen** | **M0** 100 % BTC (Maßstab) · **M1** je ⅓ · **M2** 70/20/10 (etwa nach Marktgewicht) · **M3** 50/30/20 · **M4** 50/50/0 (nur BTC/ETH, Bezug) |
| **Ausgleich** | **R0** nie ausgleichen (Zufluss nach Zielmix) · **R1** über die Zuflüsse: die neue Rate geht in den untergewichteten Wert, **ohne Verkauf** (steuerneutral) · **R2** jährlich auf den Zielmix, **mit** Verkauf |
| **Zufluss** | 1 Einheit am Monatsersten; keine Gebühren (Regel 2) |
| **Startjahre** | 01.09.2020, 2021, 2022, 2023, 11.01.2024 (ETF-Markt) |
| **Ausgewiesen** | Endvermögen ÷ M0 · größter Rückgang (Vermögen ÷ eingezahlt) · Anteil Monatsenden ≥ M0 · Zahl der Verkäufe (R2) |
| **Empfehlungsregel (vorab)** | Die Mischung mit dem höchsten **Median** von Endvermögen ÷ M0 über die Starts, **sofern** ihr Median-Rückgang höchstens 5 Pp schlechter ist als bei M0. Bei Gleichstand die einfachere (R0 vor R1 vor R2) |

### 12.3 D2-M — Teilverkauf (b) und Entnahme (d), je Kernwert

| | |
|---|---|
| **Auslöser** | Klima q aus **BTC** (F3, wachsend) für **alle drei** Werte; bekannt am Tagesschluss t, ausgeführt zum Schluss t+1 |
| **Stufen** | 0,80 / 0,90 / 0,95. Jede Stufe löst **einmal je Zyklus** aus; erneut erst nach einer Zone (q ≤ 0,20) |
| **Zufluss** | 1 Einheit am Monatsersten, nie unterbrochen (wie D1) |
| **Gegenwelt H0** | dieselben Käufe, nie verkaufen |

**Die Fälle:**

| Fall | Verkauf | Rückkauf |
|---|---|---|
| **b1** | 10 % des Bestands je Stufe | alles bei der ersten Zone (q ≤ 0,20) |
| **b2** | 10 % je Stufe | gestaffelt: ⅓ bei q ≤ 0,20 / 0,10 / 0,05; der Rest nach 12 Monaten ohne tiefere Stufe (damit das Geld nicht unbegrenzt liegt, F2) |
| **b3** | 20 % je Stufe | wie b2 |
| **b4** | **nur Stufe 0,80**, 20 % | wie b2 (der Fall des ETF-Markts) |
| **d1** | 10 % je Stufe | **kein Rückkauf**: Entnahme |
| **d2** | 20 % je Stufe | Entnahme |

| | |
|---|---|
| **Zeiträume, Starts** | BTC ab 2015 (Starts 2015, 2017, 2019, 2021, 2023, 11.01.2024) · ETH ab 2017 (2017, 2019, 2021, 2023, 2024) · SOL ab 09.2020 (2020-09, 2021, 2023, 2024) |
| **Ausgewiesen (b)** | ⭐ **Endbestand in Stück ÷ H0** (das Ziel von b) · Endvermögen ÷ H0 · größter Rückgang · ungenutztes Geld am Ende · Verkäufe und Rückkäufe · Stück ÷ H0 **am Ende jeder Zone** (je Zyklus) |
| **Ausgewiesen (d)** | entnommener Betrag · Restbestand plus Entnahme ÷ H0 (was die Entnahme gekostet hat) · Anteil des Eingezahlten zurückgeholt · größter Rückgang |
| **Auskunft** | realisierte Gewinne je Verkauf (für deine Steuerprüfung; die Steuer selbst rechne ich nicht) · D1 × D2: die nach D1 empfohlene Mischung mit b2 |
| **stimmig (b), vorab** | Stück ÷ H0 > 1 bei **BTC und ETH** in **≥ 2/3** der Starts **und** beim Start 11.01.2024 nicht unter 0,95. SOL nur Auskunft (kurze Reihe) |
| **(d)** | kein stimmig/nicht: Die Entnahme entscheidest du; die Messung zeigt den **Preis** |

### 12.4 Ehrlich vorab

- **Wenige Zyklen:** BTC hat Hochs 2017, 2021 und 2024/25, ETH zwei, SOL einen. Das ist **Beschreibung**, kein Nachweis.
- **Mehrfachtesten:** Es ist der vierte Blick auf das BTC-Klima, aber eine **andere Frage** (Ausstieg statt Einstieg). Die Stufen sind vorab fest und werden nicht nachgestellt.
- **Stichtag:** Die Reihe endet im Herbst 2026 nach einer Zone (02.–08.2026). Varianten mit Rückkauf sind dadurch eher **begünstigt**; das wird ausgewiesen (Ergebnis auch zum Ende jeder Zone).
- (a) Risiko senken und (c) Umschichten folgen später (E-68).

### 12.5 Änderungen am Messplan VOR der Messung (06.10.2026; Nutzer: *„möchte hier BTC, ETH und SOL in einem sinnvollen Verhältnis“* · *„ja, mit deinem Vorschlag können wir starten“*)

| | vorher (§12.2) | jetzt | Grund |
|---|---|---|---|
| Mischungen | M1 ⅓ · M2 70/20/10 · M3 50/30/20 · M4 50/50/0 | **V1** ⅓ · **V2** 70/20/10 (BTC-lastig) · **V3** 50/30/20 · **V4 nach Schwankung** | M4 entfällt, weil SOL dazugehört (E-68). V4 ist das einzige Verhältnis, das aus den Daten kommt statt aus einer Meinung |
| V4 Regel | — | Gewicht je Wert ∝ 1 / Schwankung der Tagesrenditen der **letzten 365 Tage** (mindestens 30 Tage) am Vortag des Kaufs; neu bei jedem Kauf; kausal | Wer stärker schwankt, bekommt weniger |
| erster Start D1 | 01.09.2020 | **01.10.2020** | V4 braucht ≥ 30 Tage SOL-Historie (SOL ab 11.08.2020) |
| Maßstab | M0 100 % BTC | unverändert, **nur als Maßstab** | |

D2-M bleibt wie §12.3.

### 12.6 Ergebnis D1-M und D2-M (06.10.2026, nach dem vorab festen Plan §12 und §12.5)

Beleg `Spot_Voranalyse_04_10/d_kern_teilverkauf.py` → `.txt`.

**Gegenprobe** (`d_gegenprobe.py`, eigene einfache Schleife): D1 V2 R0 ab 2021 = **1,00** und D2 BTC b1 ab 2017 = **0,950**, beide gleich.

#### D1 — Verhältnis BTC/ETH/SOL (Endvermögen ÷ 100 % BTC; Ende 20.09.2026)

| Fall | Start 10.2020 | 2021 | 2022 | 2023 | 11.01.2024 | **Median** | größter Rückgang (Median; BTC −59 %) |
|---|---|---|---|---|---|---|---|
| V1 ⅓ je, nie ausgleichen | 1,43 | 1,13 | 0,91 | 0,98 | 0,91 | 0,98 | −75 % |
| V1, Ausgleich über Raten | 1,52 | 1,17 | 0,97 | 1,01 | 0,92 | 1,01 | −73 % |
| V1, jährlich ausgleichen | 2,09 | 1,78 | 1,06 | 1,03 | 0,90 | 1,06 | −73 % |
| **V2 70/20/10**, nie | 1,10 | 1,00 | 0,94 | 0,97 | 0,96 | 0,97 | −63 % |
| **V2**, über Raten | 1,20 | 1,03 | 0,97 | 0,99 | 0,98 | 0,99 | −62 % |
| **V2**, jährlich | 1,37 | 1,24 | 1,00 | 0,99 | 0,96 | **1,00** | **−62 %** |
| V3 50/30/20, jährlich | 1,70 | 1,48 | 1,02 | 1,00 | 0,93 | 1,02 | −67 % |
| V4 nach Schwankung (heute 43/30/27), jährlich | 1,57 | 1,46 | 1,00 | 0,97 | 0,92 | 1,00 | −68 % |

- **Nach der vorab festen Regel: V2 70/20/10 mit jährlichem Ausgleich.** Der Median liegt bei 1,00 × BTC, der Rückgang nur 3 Pp über BTC. Alle Mischungen mit mehr ETH/SOL fallen heraus, weil ihr Rückgang mehr als 5 Pp schlechter ist.
- **V2 über die Raten** (steuerneutral, ohne Verkauf) liegt praktisch gleichauf (0,99, −62 %). Der Unterschied kommt nur aus den Starts vor 2021.
- **Kein Verhältnis schlägt BTC seit 2022:** Bei Starts 2022–2024 liegen alle Mischungen bei 0,89–1,06. Der Vorteil früher Starts kommt aus **einer** Phase, dem Anstieg von SOL und ETH 2021.

#### D2 — Teilverkauf (b): Stück am Ende ÷ nie verkaufen

| | BTC (Starts 2015 / 17 / 19 / 21 / 23 / 24) | ETH (2017 / 19 / 21 / 23 / 24) | SOL (2020 / 21 / 23 / 24) |
|---|---|---|---|
| b1 10 %, alles zurück | 0,81 · 0,95 · 0,98 · 0,99 · 1,00 · 1,00 | 0,87 · 0,93 · 1,04 · 1,03 · 1,01 | 0,92 · 0,97 · 1,03 · 1,01 |
| b2 10 %, gestaffelt | 0,87 · 1,00 · 1,01 · 0,98 · 0,98 · 1,00 | 0,89 · 0,93 · 1,02 · 1,01 · 1,00 | 0,90 · 0,95 · 1,01 · 1,00 |
| b3 20 %, gestaffelt | 0,74 · 0,97 · 1,00 · 0,95 · 0,96 · 0,99 | 0,80 · 0,87 · 1,03 · 1,03 · 1,01 | 0,81 · 0,91 · 1,02 · 1,00 |
| b4 nur Stufe 0,80, 20 % | 0,78 · 0,89 · 0,91 · 0,95 · 0,96 · 0,99 | 0,89 · 0,95 · 1,04 · 1,03 · 1,01 | 0,97 · 0,98 · 1,02 · 1,00 |

- **Nach der vorab festen Regel: kein Fall stimmig.** Der Teilverkauf nach dem BTC-Klima bringt **nicht verlässlich mehr Stück**.
- **WORAN, an den Zyklen nachgesehen (b2, BTC ab 2015):**
  - Verkauft wurde **12/2016 bei ~900 $** (Stufe 0,80), zurückgekauft 2018/19 bei 3.000–4.000 $: danach 0,84.
  - Verkauft **11/2020 bei ~18.000 $**, zurückgekauft 2022 bei 30.000 bis 16.000 $: danach 0,69, nach 2023 0,90.
  - Verkauft **03/2024 bei ~67.000 $**, zurückgekauft 2026 bei ~65.000 $: 0,87.
  - ⇒ **„Überhitzt“ kommt zu früh**, wie schon in F3. Der Kurs steigt danach meist noch stark, der Rückkauf in der nächsten Zone liegt **über** dem Verkaufspreis.
- **Im ETF-Markt** (Start 2024) ist alles neutral (0,99–1,01). Es gab nur eine Stufe (0,80) und einen Rückkauf.
- **Größter Rückgang:** etwas kleiner als beim Halten (z. B. BTC −76 % gegen −79 %), weil Geld wartet. Das ist teils mechanisch.

#### D2 — Entnahme (d): Rest plus Entnommenes ÷ nie verkaufen

| | BTC (2015 / 17 / 19 / 21 / 23 / 24) | ETH (2017 / 19 / 21 / 23 / 24) | SOL (2020 / 21 / 23 / 24) |
|---|---|---|---|
| d1 10 % je Stufe | 0,62 · 0,78 · 0,86 · 0,98 · 0,99 · 1,00 | 0,76 · 0,87 · 1,01 · 1,01 · 1,00 | 0,89 · 0,94 · 1,01 · 1,00 |
| entnommen (in % des Eingezahlten) | 544 % · 116 % · 50 % · 12 % · 7 % · 1 % | 183 % · 69 % · 11 % · 6 % · 1 % | 55 % · 32 % · 16 % · 1 % |
| d2 20 % je Stufe | 0,38 · 0,62 · 0,75 · 0,95 · 0,97 · 0,99 | 0,58 · 0,75 · 1,02 · 1,02 · 1,01 | 0,80 · 0,90 · 1,02 · 1,00 |

- **Entnahme kostet auf lange Sicht viel Ertrag, sichert aber echtes Geld:** Ab 2015 wurden beim BTC das **5,4-Fache des Eingezahlten** entnommen, dafür lag das Gesamtergebnis 38 % unter Halten. Bei Starts ab 2021 kostet sie fast nichts (0,98–1,00).
- **Ob entnommen wird, entscheidest du** (E-68). Die Messung zeigt den **Preis**.

#### Zwischenfazit zum Ziel

| | Ergebnis | Folge |
|---|---|---|
| **D1** | **70/20/10 (BTC/ETH/SOL)** ist das gemessen sinnvolle Verhältnis: so gut wie BTC allein, ETH und SOL sind dabei, und das Zusatzrisiko ist gering (+3 Pp). Ausgleich über die Raten ist steuerneutral und fast gleich gut | Vorschlag für den Aufbau: 70/20/10, **Ausgleich über die Raten** (R1) statt jährlichem Verkauf; der Unterschied von 0,01 rechtfertigt keine Verkäufe und Steuern |
| **D2 (b)** | **nicht belegt.** Der Auslöser „überhitzt“ kommt zu früh | Nach E-63: WORAN = Zeitpunkt. Eine **Fassung 2** müsste später verkaufen, z. B. erst, wenn q von über 0,90 wieder **fällt** (die Überhitzung kippt). ⚠️ Das wäre ein zweiter Blick auf dieselben 2–3 Zyklen und damit nur Beschreibung |
| **D2 (d)** | Kosten und gesicherter Betrag sind jetzt bekannt | deine Entscheidung; das System kann den Zeitpunkt als **Fakt** melden (Klima-Ampel *überhitzt*) |

### 12.7 Regeln und Funktionsweise — in Klartext (für den Nutzer)

**1. Woher die Zahl „Klima q“ kommt**
- Täglich aus BTC berechnet, aus drei Zutaten:
  - **MVRV:** Kurs gegen den Durchschnittseinstand aller BTC-Halter;
  - der **Abstand zum bisherigen Hoch**;
  - der **Abstand zum 200-Wochen-Schnitt**.
- Jede Zutat wird mit **allen Tagen seit 2013** verglichen (Perzentil). q ist der Mittelwert der drei.
- **q = 0,80** heißt: *teurer als an 80 % aller bisherigen Tage*. **q = 0,20** heißt: *billiger als an 80 % aller Tage*.
- q ist am Abend eines Tages bekannt; gehandelt wird **am nächsten Tag** zum Tagesschluss. So gibt es keinen Blick in die Zukunft.

**2. Aufbau (D1)**
- Jeden Monatsersten wird **derselbe Betrag** investiert.
- Er wird nach dem Zielverhältnis auf BTC, ETH und SOL verteilt. Gemessen ist **70/20/10** als sinnvolles Verhältnis.
- **Ausgleich über die Raten:** Hat sich ein Anteil durch Kursbewegungen vom Ziel entfernt, geht die neue Rate zuerst in den Wert, der zu wenig hat. **Verkauft wird dabei nie.**

**3. Teilverkauf (D2b) — so war er gemessen, und so hätte er gewirkt**
- **Verkauf:**
  - Steigt q über **0,80**, dann über **0,90**, dann über **0,95**, wird jedes Mal ein Teil des Bestands verkauft (10 % oder 20 %).
  - Jede Stufe nur **einmal je Zyklus**. Wieder scharf wird sie erst nach der nächsten Zone (q ≤ 0,20).
- **Rückkauf:** in der Zone, entweder auf einmal (b1) oder in drei Teilen bei q ≤ 0,20 / 0,10 / 0,05 (b2–b4). Was nach 12 Monaten noch übrig ist, wird gekauft.
- **Ergebnis:** In der Vergangenheit hätte das **weniger** Coins gebracht, weil zu früh verkauft wurde.

**4. Entnahme (D2d)**
- Gleiche Verkaufsstufen, aber das Geld bleibt draußen.
- Gemessen ist, wie viel du entnimmst und was es gegenüber Halten kostet.

**5. Was in den Zahlen NICHT enthalten ist**
- **Gebühren und Steuern** (Regel 2). Jeder Verkauf kann bei dir steuerpflichtig sein; die realisierten Gewinne je Verkauf stehen im Beleg.
- **Zinsen** auf wartendes Geld (0 %).
- Die Daten **nach dem 20.09.2026** (SOL) bzw. 04.10.2026 (BTC, ETH).

**6. Wie belastbar das ist**
- **Wenige Zyklen:** BTC 3, ETH 2, SOL 1–2. Alles ist **Beschreibung**, kein Nachweis für die Zukunft.
- **Rückschau:** Das Verhältnis 70/20/10 war in der Vergangenheit sinnvoll. Ob ETH und SOL künftig mithalten, sagt es nicht.

### 12.8 Messplan D2 Fassung 2 — verkaufen, wenn die Überhitzung KIPPT, VOR der Messung (06.10.2026; Nutzer: *„1 ja, 2 Fassung 2 messen, prüfen und gegenprüfen“*)

**Abgestimmt:** Aufbau **70/20/10** mit **Ausgleich über die Raten** (R1).

**Begründung der Fassung 2** (E-63, aus der Ursache in §12.6): *„Überhitzt“ kommt zu früh.* Fassung 2 verkauft erst, wenn q nach der Überhitzung **wieder fällt**. Alles andere bleibt wie §12.3: Rückkauf gestaffelt wie b2, Zufluss, Ausführung t+1, Maßstab H0, Kriterium *stimmig*.

| Fall | scharf ab | Verkauf (je 10 % des Bestands) |
|---|---|---|
| **K1** | q ≥ 0,90 | beim Fall unter 0,85 · 0,75 · 0,65 |
| **K2** | q ≥ 0,80 | beim Fall 0,10 · 0,20 · 0,30 unter das **Zyklushoch von q** |
| dK1 / dK2 | wie K1/K2 | Entnahme statt Rückkauf (Preis der Entnahme mit späterem Zeitpunkt) |
| Auskunft | — | K1/K2 mit 20 % je Stufe |

Wieder scharf werden die Stufen erst nach einer Zone (q ≤ 0,20), wie in Fassung 1.

**Vorprüfung, nur Klima und Datum** (`d2f2_vorpruefung.py`):
- **K1** verkauft 06./11.01.2017 und 21.01. / 16.05. / 19.05.2021.
- **K2** verkauft 06.01. / 11.01.2017 und 30.01.2018, dann 21.01. / 15.05. / 19.05.2021, dann 19.03. / 01.05. / 05.08.2024.

⚠️ **Offen, und vor der Messung bekannt:**
- Beide verkaufen schon im **Januar 2017** (kurzer Ausschlag im Dezember 2016). Weil jede Stufe nur einmal je Zyklus auslöst, bleibt für das Hoch im Dezember 2017 nichts übrig.
- Die Regeln werden **nicht** nachgestellt, um bekannte Hochs zu treffen; das wäre Kurvenanpassung mit Wissen aus der Zukunft.
- **Zweiter Blick** auf dieselben 2–3 Zyklen: Das Ergebnis ist **Beschreibung**.

### 12.9 Ergebnis D2 Fassung 2 — Verkauf beim Kippen (06.10.2026, nach §12.8)

Beleg `Spot_Voranalyse_04_10/d2_fassung2.py` → `.txt`.

**Gegenprobe** (`d2f2_gegenprobe.py`, eigene Schleife): BTC K1 ab 2017 = **1,164**, ETH K2 ab 2019 = **1,203**, beide gleich.

**(b) Stück am Ende ÷ nie verkaufen:**

| | BTC (2015 / 17 / 19 / 21 / 23 / 24) | ETH (2017 / 19 / 21 / 23 / 24) | SOL (2020 / 21 / 23 / 24) |
|---|---|---|---|
| Fassung 1 b2 (zum Vergleich) | 0,87 · 1,00 · 1,01 · 0,98 · 0,98 · 1,00 | 0,89 · 0,93 · 1,02 · 1,01 · 1,00 | 0,90 · 0,95 · 1,01 · 1,00 |
| **K1** (ab 0,90, Fall unter 0,85/0,75/0,65) | 0,99 · **1,16** · **1,14** · 1,01 · 1,00 · 1,00 | **1,10** · **1,15** · 1,02 · 1,00 · 1,00 | 1,03 · 1,03 · 1,00 · 1,00 |
| **K2** (ab 0,80, Fall unter das Zyklushoch) | 1,10 · 1,15 · 1,04 · 0,93 · 0,94 · 0,98 | **1,86** · 1,20 · 1,05 · 1,01 · 1,00 | 1,16 · 1,15 · 1,09 · 1,02 |

- **Nach der vorab festen Regel: beide nicht stimmig.**
  - **K1:** BTC liegt nur in 3 von 6 Starts über 1. Bei den Starts 2023 und 2024 gab es **keinen Verkauf** (q kam nie über 0,90), Ergebnis genau 1,000. ETH 3 von 5.
  - **K2:** ETH ✔ und SOL ✔, aber BTC 3 von 6. Die jüngeren Starts liegen bei 0,93–0,98.
- **Im Vergleich zu Fassung 1 deutlich besser:**
  - **K1** ist nie spürbar schlechter als Halten (BTC schlechtestenfalls 0,99) und in den Zyklen 2017/2021 bis zu 16 % besser.
  - K1 handelt **selten**: nur bei echter, starker Überhitzung. Sonst ist es dasselbe wie Halten.
- **WORAN K2:**
  - Im ETF-Markt verkaufte K2 03.–08.2024 bei 68.000 / 59.000 / 56.000 $. Zurückgekauft wurde 2026 bei ~60.000–70.000 $, also kein Vorteil.
  - Am Stichtag warten noch **21 %** des Eingezahlten auf den Rückkauf (zweite Zone ≤ 0,05 kam nicht, Frist 02/2027). Das unfertige Ende drückt die jüngeren Starts.
- **2017:** Beide verkauften im **Januar 2017** (kurzer Ausschlag). Beim Start 2015 kostete das, bei späteren Starts kaum, weil der Bestand damals klein war.

**(d) Entnahme mit dem späteren Zeitpunkt, Rest + Entnommenes ÷ Halten:**

| | BTC | ETH | SOL |
|---|---|---|---|
| Fassung 1 d1 | 0,62 · 0,78 · 0,86 · 0,98 · 0,99 · 1,00 | 0,76 · 0,87 · 1,01 · 1,01 · 1,00 | 0,89 · 0,94 · 1,01 · 1,00 |
| **dK1** | 0,66 · 0,85 · 0,90 · 0,99 · 1,00 · 1,00 | 0,91 · 0,97 · 1,00 · 1,00 · 1,00 | 0,87 · 0,93 · 1,00 · 1,00 |
| **dK2** | 0,62 · 0,77 · 0,84 · 0,93 · 0,95 · 0,98 | 0,92 · 1,00 · 1,02 · 1,01 · 1,00 | 0,97 · 1,03 · 1,09 · 1,02 |

Mit dem späteren Zeitpunkt (dK1) kostet die Entnahme **weniger** als in Fassung 1.

#### Zwischenfazit

| | |
|---|---|
| **Ergebnis** | Die Ursache aus Fassung 1 (zu früh) war richtig erkannt: Verkaufen beim **Kippen** hilft deutlich, vor allem K1. **Nach der vorab festen Regel ist es trotzdem nicht belegt**, weil BTC nicht in 2/3 der Starts vorne liegt |
| ⚠️ **Ehrlich** | zweiter Blick auf dieselben 2–3 Zyklen. Das Ergebnis von K1 hängt praktisch an **einem** Ereignis: 2021 verkauft bei 33.000–46.000 $, zurückgekauft 2022 bei 30.000–16.000 $ |
| **Was daraus folgt** | K1 als **Hinweis** statt als Regel: *„Die Überhitzung kippt, Teilverkauf erwägen“* als Fakt in der Mail, samt der gemessenen Wirkung. Den Verkauf entscheidest du (passt zu (d)). Automatisch handeln lässt sich das nicht begründen |
| **Was NICHT folgt** | K2 im ETF-Markt: Das Klima erreicht dort keine starke Überhitzung, die Verkäufe 2024 brachten nichts |

### 12.10 Regeln in Klartext — Ergänzung Fassung 2 (für den Nutzer)

- **K1 *„die starke Überhitzung kippt“***
  - Das Klima q steigt einmal über **0,90**: Das ist starke Überhitzung, bisher nur 2017 und 2021. Ab dann gilt K1 als *scharf*.
  - Fällt q danach unter **0,85**, wird ein Zehntel verkauft. Ein weiteres Zehntel bei **0,75**, ein drittes bei **0,65**.
  - Zurückgekauft wird in der nächsten Zone in drei Teilen: bei q ≤ 0,20 / 0,10 / 0,05, der Rest spätestens nach 12 Monaten.
  - Danach ist K1 erst wieder scharf, wenn q erneut über 0,90 steigt.
- **K2 *„die Überhitzung lässt nach“***
  - Scharf ab **0,80**.
  - Verkauf je ein Zehntel, wenn q 0,10 / 0,20 / 0,30 unter seinem **bisherigen Höchstwert im Zyklus** liegt.
- **Was beide NICHT tun:** im Voraus wissen, ob das Hoch schon da war. Sie reagieren erst auf den Rückgang, deshalb verkaufen sie nie ganz oben.

### 12.11 Abgestimmt (06.10.2026; E-69)

**Aufbau:** 70/20/10 mit Ausgleich über die Raten.

**Klima-Ampel in der Mail (Inhalt für den Bau in S7):**

| Feld | Inhalt |
|---|---|
| Ampel | *Kapitulation · Bodenbildung · Wende bestätigt · Aufwärtstrend · überhitzt* (§8.3), mit q und den drei Zutaten |
| **K1-Hinweis Verkauf** | sobald q in diesem Zyklus über 0,90 war und unter 0,85 / 0,75 / 0,65 fällt: *„Starke Überhitzung kippt – Teilverkauf erwägen (je ein Zehntel)“*; dazu die gemessene Wirkung (bis +16 % Stück 2017/2021, sonst wie Halten) und der Vorbehalt *im Wesentlichen ein Ereignis (2021)* |
| **Hinweis Rückkauf** | in der Zone q ≤ 0,20 / 0,10 / 0,05: *„Rückkauf erwägen (je ein Drittel des wartenden Geldes)“*; nach 12 Monaten *„Rest kaufen“* |
| Aufbau | Zielverhältnis 70/20/10, Abweichung je Wert, Vorschlag für die nächste Rate (Ausgleich über die Raten) |

Kein Auslöser, keine automatische Handlung: Die Entscheidung bleibt beim Nutzer.

## 13. Messplan S1 — die Altcoin-Phase als Fakt, VOR der Messung (06.10.2026; Nutzer: *„Messplan für S1 vorbereiten, prüfen und gegenprüfen“*)

**Zweck:** Für Altcoin-Spot braucht es zuerst einen **Fakt**: *Ist der Markt gerade in einer Altcoin-Phase?* Er ist **kein Auslöser** (§11.1: Fragen über die Phase haben wenige Fälle). Er gehört in die Klima-Ampel, und **du gewichtest** ihn.

### 13.1 Vorprüfung (`Spot_Voranalyse_04_10/s1_vorpruefung.py`, keine Messung der Vorhersagekraft)

- ⛔ **Für die BTC-Dominanz gibt es keine Historie:** am Desktop nur 10 Tage (07/2026), eine freie Langzeitquelle fehlt (CoinGecko nur in der Bezahlversion). Sie bleibt **ungeeicht**: im Betrieb höchstens als Tageswert in der Mail.
- **Universum:** `messdaten.db` mit eingestellten Werten, 82 Altcoins (2019), 181 (2020), 295 bis 457 (2021–2025). Gemessen wird **ab 2019**.
- **Korb:** die 50 umsatzstärksten Altcoins (30-Tage-Umsatz in USD am Monatsersten), gleich gewichtet, monatlich neu, ohne BTC und Stablecoins, eingestellte bis zum letzten Kurs.
- **Ereignis „echte Altcoin-Phase“** (wie K-4, per Definition rückblickend): Der Korb schlägt BTC in den **folgenden 90 Tagen** um **mindestens 25 Pp**. Episoden mit Lücke unter 30 Tagen werden verbunden, Mindestdauer 7 Tage.

| Phase | Dauer | bester Vorsprung |
|---|---|---|
| 10.04. – 17.06.2020 | 68 T | +88 % |
| 12.11.2020 – 23.03.2021 | 131 T | +156 % |
| 11.05. – 15.06.2022 | 35 T | +50 % |
| 16. – 25.10.2023 | 9 T | +39 % |
| **2024 – 2026 (ETF-Markt)** | **keine** | — |

### 13.2 Die Kandidaten-Fakten (vorab, alle kausal, nur aus Kursen)

| # | Fakt | Tage *an* je Jahr 2019 · 2020 · … · 2026 |
|---|---|---|
| **F1** | ETH/BTC über seinem **steigenden** 200-Tage-Schnitt | 0 · 266 · 303 · 135 · 20 · 17 · 139 · 38 |
| **F2** | **Altseason-Breite:** ≥ 75 % der Top 50 schlugen BTC in den **letzten** 90 Tagen (die gängige Definition des „Altcoin Season Index“) | 0 · 28 · 79 · 37 · 0 · 10 · 16 · 0 |
| **F3** | Korb/BTC über seinem **steigenden** 200-Tage-Schnitt | 0 · 141 · 132 · 0 · 0 · 19 · 0 · 0 |
| **F4** | mindestens 2 von F1–F3 | — |
| Kontext | BTC-Klima q (Auskunft: in welchem BTC-Zustand liefen die Phasen?) | — |

### 13.3 Die Fragen (Beschreibung, wie F1 H1–H3)

| # | Frage | stimmig, wenn |
|---|---|---|
| **S1-H1 Deckung** | Ist der Fakt **während** einer Phase an? | an in ≥ 50 % der Phasentage, in ≥ 2 der 3 Phasen mit ≥ 30 Tagen |
| **S1-H2 Verzögerung** | Wie spät schaltet er nach Phasenbeginn ein, und wie viel Vorsprung ist bis dahin schon verpasst? | ausgewiesen |
| **S1-H3 Fehlalarm** | Wie oft ist er **außerhalb** jeder Phase an (±30 T Puffer)? | ≤ 50 % seiner An-Tage |
| S1-H4 Wirkung | Korb gegen BTC in den 90 T nach jedem Einschalten | **Auskunft** (zu wenige Phasen für ein Urteil) |
| zweiseitig | Gegenrichtung: Fakt aus, obwohl Phase | ausgewiesen |

**Folge, vorab:**
- Der Fakt mit der besten Kombination aus Deckung und wenig Fehlalarm kommt **als Fakt** in die Klima-Ampel.
- Erfüllt keiner H1 und H3, bekommt die Ampel **keine** Altcoin-Phase, nur die Breite als Zahl.

**Betriebsprüfung (vorab):** F1–F3 lassen sich am NB aus den laufend nachgeladenen Stundenkursen rechnen (`stundenkurse.db` / `stundenkurse_alle.db`, ab 2023, 537 Werte). Das reicht für 200 + 90 Tage. Die BTC-Dominanz kommt live aus `macro_snapshot`, ungeeicht.

**Gegenprobe:** Korb-Index für einen Monat und Breite für einen Tag, unabhängig nachgerechnet.

⚠️ **Ehrlich:**
- 3–4 Phasen, **alle vor dem ETF-Markt**. Für den heutigen Markt kann S1 **nicht** bestätigt werden; dort gab es keine Phase.
- S1 liefert eine **Beschreibung** der Vergangenheit und einen Fakt für die Mail, keine Vorhersage.

### 13.4 Ergebnis S1 (06.10.2026, nach §13)

Beleg `Spot_Voranalyse_04_10/s1_messung.py` → `.txt`.

**Gegenprobe** (`s1_gegenprobe.py`, direkt aus SQL): Korb-Rendite Januar 2021 **+63,89 %**, Breite am 29.03.2021 **0,848**, beide gleich.

**Zwei Umsetzungsfehler, vor der Bewertung behoben** (die Regel blieb unverändert):
1. Die Verzögerung H2 zählte einen An-Tag *vor* der Phase als „eingeschaltet“, auch wenn der Fakt während der Phase aus war.
2. Die Breite F2 zählte Coins ohne Kurs vor 90 Tagen als „schlägt BTC nicht“. Das drückte die Breite gerade bei vielen neuen Listings (2021).

| Fakt | Deckung 2020-04 · 2020-11 · 2022-05 | Einschalten | Fehlalarm (an außerhalb) | Korb gegen BTC in den 90 T nach dem Einschalten (Auskunft) |
|---|---|---|---|---|
| **F1** ETH/BTC über steigendem 200-T-Schnitt | **87 % · 55 %** · 0 % | 2020-04 schon an, 2020-11 nach 1 T | **74 %** ✗ | Median **−15 %**, 3 von 11 positiv |
| **F2** Altseason-Breite ≥ 75 % | 0 % · 1 % · 0 % | 2020-11 erst **nach 131 T** (+45 % verpasst) | 86 % ✗ | Median **−32 %**, 1 von 6 positiv |
| F3 Korb/BTC über steigendem 200-T-Schnitt | 32 % · 0 % · 0 % | 2020-04 nach 7 T | 80 % ✗ | Median −9 %, 2 von 7 |
| F4 mind. 2 von 3 | 32 % · 0 % · 0 % | — | 80 % ✗ | Median −5 %, 3 von 7 |

- **Nach der vorab festen Regel: kein Fakt erfüllt Deckung (H1) und Fehlalarm (H3).** F1 deckt zwei Phasen, ist aber zu drei Vierteln **außerhalb** einer Phase an.
- **Folge (vorab):** Die Klima-Ampel zeigt **nur die Altseason-Breite als Zahl**, keine Altcoin-Phase. Heute (20.09.2026): 51 % der Top 50 schlugen BTC in 90 T.
- **Auskunft, kein Befund (wenige Fälle):** Eine **hohe** Breite war eher ein **Endsignal**. Nach dem Einschalten von F2 lag der Korb in 5 von 6 Fällen 90 T später **hinter** BTC (Median −32 %). Der bekannte „Altcoin Season Index“ blickt 90 T zurück und kommt damit zu spät.
- **BTC-Klima in den Phasen:** 0,43 · 0,89 · 0,20 · 0,22. Die Phasen kamen in **jedem** BTC-Zustand; kein Zusammenhang.

#### Zwischenfazit für Altcoin-Spot

| | |
|---|---|
| **Die Phase ist nicht rechtzeitig erkennbar** | Mit Kursfakten lässt sich eine Altcoin-Phase nicht so anzeigen, dass sie hilft: entweder ständiger Fehlalarm (F1) oder zu spät (F2). Seit 2024 gab es keine Phase |
| **Was folgt** | Ein Altcoin-Weg muss **innerhalb** des Marktes tragen, unabhängig davon, ob eine Phase gerade erkennbar ist: Auswahl, Einstieg, Ausstieg und Streuung (S3–S6). Dort gibt es viele Fälle |
| **Nutzerhinweis 06.10.** | *„die Assets unterteilen und die Ergebnisse bewerten, z. B. stabile Highcaps wie LINK im Vergleich zu riskanten Smallcaps“* → kommt in den Messplan S3–S6 (§14) |

## 14. Messplan S3–S6 — Altcoin-Spot je Asset-Klasse, VOR der Messung (06.10.2026; Nutzer: *„die Assets unterteilen und die Ergebnisse bewerten, z. B. stabile Highcaps wie LINK im Vergleich zu riskanten Smallcaps“* · *„Messplan S3–S6 vorbereiten, prüfen und gegenprüfen“*)

### 14.1 Vorprüfung (`Spot_Voranalyse_04_10/s3_vorpruefung.py`, keine Erträge)

| Jahr (Juli) | Altcoins mit Kurs | Top 20 · 21–100 · 101+ | ≥ 2 Jahre gelistet | LINK nach 30-T-Umsatz |
|---|---|---|---|---|
| 2019 | 41 | 20 · 21 · 0 | 0 | 6 |
| 2020 | 105 | 20 · 80 · 5 | 13 | 5 |
| 2021 | 228 | 20 · 80 · 128 | 41 | 9 |
| 2022 | 318 | 20 · 80 · 218 | 99 | 11 |
| 2023 | 339 | 20 · 80 · 239 | 202 | 22 |
| 2024 | 380 | 20 · 80 · 280 | 279 | **34** |
| 2025 | 405 | 20 · 80 · 305 | 261 | 18 |
| 2026 | 361 | 20 · 80 · 261 | 268 | 16 |

**Befunde:**
- **Kein Marktwert über die Jahre:** Die Umlaufmenge gibt es erst ab 09/2025. Größe heißt deshalb **Umsatz**.
- **Der Rang schwankt stark:** LINK lag auf Platz 5–34. Deshalb ein **90-T-Umsatz** und eine Stabilitätsbedingung.
- **19 Sonder-Tokens** in den Daten: Fiat (EUR, AEUR, EURI, GBP, AUD), Gold (PAXG), Wrapped (WBTC, WBETH, BNSOL) und Stablecoins. Sie werden **ausgeschlossen**. „EUR“ stand sonst unter den Highcaps.
- **Smallcaps und das Alter** sind erst **ab 2021** sinnvoll; davor gibt es zu wenige Coins und keine 2-Jahres-Historie.

### 14.2 Universum und Klassen (vorab, am Monatsersten, nur mit Daten bis zum Vortag)

- **Universum:** alle Altcoins in `messdaten.db` **mit eingestellten**. Ohne BTC, ohne die Kernwerte ETH und SOL (Auskunft getrennt), ohne Stablecoins, Fiat, Gold und Wrapped.

| Klasse | Regel |
|---|---|
| **H stabile Highcaps** | 90-T-Umsatzrang **≤ 30 an drei Monatsersten in Folge** **und** ≥ 2 Jahre Kurs |
| **M Midcaps** | Rang 31–100 (90-T-Umsatz), nicht H |
| **S Smallcaps** | Rang ≥ 101 |
| quer (Auskunft) | **Alter** ≥ 2 J / 1–2 J / < 1 J · **Schwankung** (90 T) in Dritteln |

### 14.3 Stufe 1 — Grundrate gegen BTC je Klasse (beschreibend)

- **Messung:** wie G1-M2 (§10.7), getrennt je Klasse.
  - Relativer Ertrag gegen BTC über **90 / 180 / 365 T**.
  - Kennzahlen: Median, Anteil vor BTC, **Korb** (gleich gewichtet, Median über die Starts) und **Median-Korb**, Anteil mit −90 %, Anteil eingestellt.
- **Starts:** monatlich, getrennt nach **E2** (2021 bis 10.01.2024) und **E3** (ab 11.01.2024). E1 nur Auskunft (Messfokus).
- **Auskunft:** LINK einzeln; ETH und SOL gegen BTC; Querklassen Alter und Schwankung.
- **Zulässig für Stufe 2, vorab:** Der Korb der Klasse liegt in **E3** auf 180 **oder** 365 T im Median **höchstens 10 Pp hinter BTC**.
  - Begründung: Auswahl- und Ausstiegsregeln bringen erfahrungsgemäß einige Prozentpunkte, nicht Dutzende. Dazu kommen rund 2,5 % Kosten je Hin- und Rückweg.
  - **Ist keine Klasse zulässig:** D4 kommt zur Vorlage (Altcoin-Spot entfällt bzw. nur Auskunft), mit dem WORAN je Klasse.

### 14.4 Stufe 2 — Regeln innerhalb der zulässigen Klassen (Rahmen vorab; der genaue Plan kommt nach Stufe 1 zur Abstimmung)

| Schicht | Kandidaten (höchstens 12 Kombinationen) |
|---|---|
| **S3 Auswahl** | relative Stärke gegen BTC (90 T, stärkste) · Gegenbewegung (90 T, schwächste) · Spiegel der jeweils anderen |
| **S4 Einstieg** | sofort am Monatsersten · **nach Korrektur im Aufwärtstrend** (≥ 20 % unter dem 30-T-Hoch bei steigendem 200-T-Schnitt; Nutzeridee) |
| **S5 Ausstieg** | 365 T halten · Trendbruch (Schluss unter dem 200-T-Schnitt) · Nachlauf −35 % vom Hoch |
| **S6 Streuung** | 5 / 10 / 20 Coins gleich gewichtet (Auskunft) |

- **Simulation:** monatlicher Zufluss; dieselben Geldflüsse in BTC als Maßstab (PME, §10.7); **Kosten 1,25 % je Kauf und je Verkauf** in der **Erfolgsmessung** (Ebene B, nicht in der Bewertung); eingestellte bis zum letzten Kurs.
- **Wahl auf E2, einmal bestätigt auf E3** (wie beim Hebel E-21/E-24).
- **Nullwelt:** zufällige Auswahl aus derselben Klasse, gleiche Zahl und Zeitpunkte, 200 Ziehungen.
- **Trägt:** in E3 nach Kosten **vor BTC** **und** Nullwelt-Rang ≥ 0,95. Sonst D4.

### 14.5 Gegenprüfung des Plans (vor jeder Ertragsrechnung)

| | |
|---|---|
| Vorgriff | Klassen nur aus Daten bis zum Vortag; Umsatz rückblickend 90 T; der Einstieg zum Schluss des Folgetags |
| Überleben | eingestellte im Universum (186 von 525, G1-M2) |
| Sonder-Tokens | 19 ausgeschlossen (sonst stünde „EUR“ unter den Highcaps) |
| Größenmaß | Umsatz statt Marktwert (kein Marktwert vor 09/2025); Stabilität über drei Monate |
| Mehrfachtesten | Stufe 1 beschreibend (3 Klassen × 3 Horizonte × 2 Epochen); Stufe 2 höchstens 12 Kombinationen, eine Bestätigung |
| Messfokus | E2 wählt, E3 bestätigt; E1 nur Auskunft |
| **Betrieb (B-Punkte)** | Klassen sind am NB aus `stundenkurse_alle.db` rechenbar (Umsatz ✔, ab 2023; das Alter ≥ 2 J erst ab 2025 aus eigenen Daten). ⚠️ **Gehandelt wird bei Bitpanda:** Im Betrieb zählt nur, was dort handelbar ist (Katalog am NB). In Stufe 2 als Auskunft prüfen |

### 14.6 Ergebnis Stufe 1 — Grundrate je Klasse (06.10.2026, nach §14.3)

Beleg `Spot_Voranalyse_04_10/s3_stufe1.py` → `.txt`.

**Gegenprobe** (`s3_gegenprobe.py`, direkt aus SQL): Klasse H am 01.03.2024 mit **14 Coins** (ADA, AVAX, BNB, DOGE, DOT, FIL, INJ, LINK, MATIC, NEAR, RUNE, SHIB, TRB, XRP), 180-T-Korb **−27,90 %** gegen BTC, gleich.
- ⚠️ **Beim ersten Vergleich wich sie ab** (10 statt 14 Coins). Die Ursache war eine **Auslegung**, kein Rechenfehler.
  - Das Hauptskript rankt einen Coin erst ab 30 Tagen Umsatz (stand vor dem Lauf im Code, war aber nicht beschrieben). Die Gegenprobe rankte auch Neulistungen mit wenigen Hype-Tagen (DYM, PIXEL, PORTAL, STRK).
  - Für ein **Größenmaß** ist die 30-Tage-Regel richtig. Sie ist jetzt dokumentiert, die Gegenprobe nutzt sie ebenfalls.

**Korb gegen BTC** (gleich gewichtet, Median über die Starts):

| Klasse | E2 2021–23: 180 T · 365 T | **E3 ETF-Markt: 180 T · 365 T** | E3 365 T: vor BTC · −90 % · eingestellt |
|---|---|---|---|
| **H stabile Highcaps** | −14 % · −22 % | **−16 % · −29 %** | 18 % · 0 % · 6 % |
| M Midcaps | −21 % · −37 % | −36 % · −58 % | 6 % · 7 % · 5 % |
| S Smallcaps | −8 % · −26 % | −35 % · −62 % | 5 % · 8 % · 18 % |

- **Nach der vorab festen Regel: keine Klasse zulässig.** Die Grenze war höchstens −10 % in E3 auf 180 oder 365 T. Am nächsten liegen die stabilen Highcaps mit −16 % (180 T).
- **Das Gefälle ist eindeutig:** größer, älter und ruhiger verliert weniger.
  - E3 365 T nach Alter: ab 2 J −53 %, 1–2 J −68 %, < 1 J −73 %.
  - Nach Schwankung: ruhig −49 %, mittel −62 %, wild −66 %.
  - Gegen BTC liegt trotzdem **jede** Klasse hinten.
- **Auskunft:**
  - **LINK** E3 365 T **−28 %** (3 von 20 Starts vor BTC).
  - ETH −8 % (5/20), SOL −29 % (0/20).
  - LINK war in E2 und E3 fast immer Klasse H.

#### D4 zur Vorlage — mit dem WORAN je Klasse

| | |
|---|---|
| **WORAN** | Im ETF-Markt floss das Geld in **BTC**. Das zeigt sich in **allen** Klassen, nicht nur bei riskanten Werten: selbst stabile Highcaps wie LINK verloren über ein Jahr rund 30 % gegen BTC. Bei Smallcaps kommen Totalverluste und Einstellungen dazu (18 % eingestellt) |
| **Was eine Auswahlregel leisten müsste** | aus −16 % bis −62 % Grundrate **plus** 2,5 % Kosten je Hin- und Rückweg einen Vorsprung machen. Das ist ein Mehrfaches dessen, was Regeln sonst bringen |
| **Wo es Altcoin-Chancen gibt** | ⭐ **kurzfristig über den Hebel:** Die REGEL0 bewertet stündlich 636 Werte, darunter fast alle Altcoins, über 24 h. Dort ist der Vorteil gemessen |
