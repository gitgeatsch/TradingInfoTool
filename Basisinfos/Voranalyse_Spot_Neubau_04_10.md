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

## 15. Messplan Altcoin-Spot Fassung 2 — antizyklisch kaufen und Positionen führen, VOR der Messung (06.10.2026; E-70)

Nutzer 06.10.: *„hier kann und soll nicht die Kernwert-Berechnung angewendet werden, meines Erachtens. Antizyklisch – Bodenkauf ist erforderlich, dann sollte eine massive Outperformance möglich sein; eigentlich müssen die Spot-Positionen auch geführt werden. Versuche für die Altcoins auch alternative Ansätze, wie wir damit sinnvoll umgehen können.“*

### 15.1 Warum Fassung 2 (E-63)

- §14.6 hat die **Grundrate** gemessen: Kauf an jedem Monatsersten, auch am Hoch, ungeführt gehalten. Das ist der Maßstab *zufälliger Zeitpunkt*, **nicht** die Strategie des Nutzers.
- Die Zulassungsregel („höchstens −10 Pp“) unterstellte, eine Regel bringe nur wenige Pp. Für **Bodenkauf mit Positionsführung** gilt das nicht: Sie vermeidet die schlechten Einstiege und sichert Gewinne.
- ⇒ Die Strategie wird **direkt** gemessen. Die Zulassungsregel aus §14.3 **entfällt** für diese Fassung.
- Lehre: Eine Grundrate taugt nicht als Filter für eine **Zeitpunkt**-Strategie.

### 15.2 Vorprüfung (`Spot_Voranalyse_04_10/a2_vorpruefung.py`, nur Zahl der Ereignisse)

| Ansatz | Ereignisse je Jahr 2020 · 21 · 22 · 23 · 24 · 25 · 26 (H/M/S) |
|---|---|
| **A** Boden je Coin: ≥ 75 % unter dem 365-T-Hoch, dann **Wende** (Schluss über dem 50-T-Schnitt nach ≥ 60 T darunter), Ruhe 180 T je Coin | 9 · 89 · 328 · 140 · 69 · 280 · 379 (meist M/S; H 0–9 je Jahr) |
| **B** Markt-Boden: Korb kaufen in der BTC-Zone (q ≤ 0,20) | 7 Episoden: 2018/19 · 03/2020 · 05/2022–03/2023 · 2023 (2) · 2026 (2) |
| D Trendfolge Coin/BTC über steigendem 200-T-Schnitt | 0–15 je Jahr → **nur Auskunft** |

### 15.3 Die Fälle (vorab, höchstens 15 Kombinationen)

| Einstieg | Klassen | Ausstieg |
|---|---|---|
| **A1** Boden je Coin mit Wende (Kauf zum Schluss t+1) | H, M, S | X1, X2, X3 |
| **A2** Boden je Coin **ohne** Wende: erster Tag ≥ 75 % unter dem Hoch (*fallendes Messer*, Vergleich zu A1) | M, S | X2 |
| **B** Markt-Boden: am ersten Zonentag jeder Episode ein gleich gewichteter Korb der Klasse | H, M | X1, X2 |

**Positionsführung (Ausstieg) — vorab:**

| | Regel |
|---|---|
| **X1 gestaffelt** | ⅓ verkaufen bei **+100 %**, ⅓ bei **+200 %**; der Rest mit Nachlauf −35 % vom Hoch seit Einstieg. Höchstens 730 T |
| **X2 Nachlauf** | Verkauf, wenn der Kurs **35 % unter sein Hoch seit Einstieg** fällt; **Notbremse −50 %** vom Einstieg. Höchstens 730 T |
| **X3 Zeit** | 365 T halten, ungeführt (Bezug: Bodenkauf **ohne** Führung) |

### 15.4 Messung

- **Je Handel:** Ertrag nach Kosten (1,25 % je Kauf und Verkauf; Smallcaps zusätzlich mit 3 % je Seite als Auskunft) **gegen BTC**, gekauft und verkauft an **denselben Tagen**. ⇒ *Vorteil gegen BTC*.
- **Nullwelt:** 20 zufällige Einstiegstage **desselben Coins im selben Kalenderjahr**, gleiche Ausstiegsregel. ⇒ Wie viel bringt der **Zeitpunkt** Boden?
- **Tagesklammer:** Handel am selben Tag zuerst gemittelt, damit ein Crashtag mit 50 Ereignissen nicht 50-fach zählt.
- **Eingestellte:** Ausstieg zum letzten Kurs. **Offene** Handel am Datenende werden zum letzten Kurs bewertet und als *offen* gezählt.
- **Ausgewiesen:**
  - Median und Mittel des Vorteils gegen BTC;
  - Anteil mit ≥ +100 % (*massive Outperformance*) und mit ≤ −50 %;
  - mittlere Haltedauer, Anteil offen;
  - Nullwelt-Rang;
  - je **Klasse** und **Epoche**.

### 15.5 Wann es trägt (vorab)

- **Wahl auf E2** (Einstiege 2021 bis 10.01.2024), **Bestätigung einmal auf E3** (ab 11.01.2024). E1 nur Auskunft.
- **Trägt** heißt: in **E2 und E3** Median **und** Mittel des Vorteils gegen BTC nach Kosten **> 0** **und** Nullwelt-Rang ≥ 0,95.
- **Mehrfachtesten:** 15 Kombinationen. Erst die Forderung *beide Epochen* hält Zufallstreffer klein.
- **Folge:**
  - Trägt eine Kombination: Voranalyse für den Betrieb (Signal je Coin, Führung in der Mail, Bitpanda-Katalog, Betriebsprüfung).
  - Trägt keine: WORAN je Ansatz, dann D4 zur Vorlage.

### 15.6 Gegenprüfung des Plans

| | |
|---|---|
| Vorgriff | Hoch, Schnitt und Wende nur aus Daten bis zum Tag t; Kauf zum Schluss t+1 |
| Überleben | eingestellte enthalten; gerade bei −75 % sterben viele Coins |
| Kosten | im Ertrag des Handels; bei Smallcaps mit höherer Annahme als Auskunft |
| Vergleich | BTC zu denselben Tagen (der faire Maßstab: BTC ist am Boden ebenfalls billig) |
| Fallzahl | A: Hunderte Ereignisse je Jahr. B: nur 7 Episoden, also Beschreibung |
| Betrieb | Tageskerzen aus `stundenkurse_alle.db` am NB (ab 2023, 365-T-Hoch ✔); Bitpanda-Handelbarkeit als Auskunft |

### 15.7 Ergebnis Altcoin Fassung 2 (06.10.2026, nach §15) — und WORAN

Belege:
- `Spot_Voranalyse_04_10/a2_messung.py` → `.txt`
- Gegenprobe `a2_gegenprobe.py`: 15 von 15 Handeln gleich
- Ursache `a2_woran.py` → `.txt`

Nutzer vor der Messung: *„müssen jedenfalls die Altcoin-Strategie so weit wie möglich optimieren, sehen wir, was die Messungen bringen“*.

**Korrigiert vor der Bewertung:** Die Kennzahl *eingestellt* zählte Coins, die irgendwann innerhalb von 730 T nach dem Kauf eingestellt wurden, auch wenn der Handel längst beendet war. Richtig ist nur ein **erzwungenes** Ende durch Einstellung. Alle anderen Zahlen sind unverändert.

**Vorteil gegen BTC (an denselben Tagen, nach Kosten; Tagesklammer Mittel / Median):**

| Fall | E2 2021–23 | E3 ETF-Markt | E3: ≥ +100 % gg. BTC · Haltedauer | Nullwelt-Rang E2/E3 |
|---|---|---|---|---|
| A1 Boden + Wende · H · X1/X2 | +22 % / +16 % (n 15) | −6 % / −3 % (n 11) | 0 % · 47 T | 0,64 / 0,49 |
| A1 · M · X1 | −2 % / −10 % | −11 % / −14 % | 0 % · 51 T | 0,47 / 0,43 |
| A1 · S · X1 | +6 % / −7 % | −13 % / −17 % | 1 % · 51 T | **1,00** / 0,82 |
| A1 · M/S · X3 (365 T ungeführt) | −36 / −24 % | −31 / −32 % | ≤ 1 % · 230–250 T | — |
| A2 fallendes Messer · M/S · X2 | −11 % / −18 % | −14 bis −17 % | 1 % | 0,00 / 0,36–0,57 |
| B Markt-Boden-Korb · H/M | −0 bis −10 % | −7 bis −11 % | 2–3 % | ≤ 0,81 / 0,00 |

- **Nach der vorab festen Regel: keine Kombination trägt.**
- **E1 (2019–2020)** zeigte die *massive Outperformance*: A1 · M · X3 +238 % im Mittel; der Markt-Boden-Korb 03/2020 +47 bis +75 % gegen BTC. Das ist **eine** Phase (Altcoin-Saison 2021).
- **Die Führung hilft deutlich** gegenüber ungeführtem Halten (X1/X2 statt X3: +20 bis +40 Pp). Das reicht aber nicht über BTC.
- **Der Zeitpunkt Boden ist besser als Zufall** (A1 · S: Rang 1,00 in E2): Die Wende trennt. Gegen BTC verliert der Coin trotzdem, weil die Grundrate stärker zieht.
- **Wende abwarten** ist besser als ins fallende Messer greifen (A2: Rang 0,00 in E2).

**WORAN** (A1 · M/S · X2, 1.258 Handel):

| | E2 | E3 |
|---|---|---|
| Ausstieg nach (Median) | 56 T | 41 T |
| **größter Gewinn vor dem Ausstieg** (Median) | **+39 %**; ≥ +50 % in 40 % der Handel | **+16 %**; ≥ +50 % in 18 % |
| Coin gegen BTC in den 180 T **nach** dem Ausstieg | **−28 %** | **−36 %** |
| Wende auch gegen BTC (Coin/BTC über 50-T) | hilft nicht (Mittel −5 % gegen +6 %) | hilft nicht |
| BTC im Aufwärtstrend als Filter | hilft nicht | schadet (−21 % gegen −11 %) |

⇒ **Nach dem Boden kommt eine kurze Erholung, dann fällt der Coin gegen BTC weiter.**
- Der Nachlauf von −35 % gibt die Erholung zurück, das Ziel +100 % wird selten erreicht.
- **Länger halten wäre schlechter**, nicht besser.

### 15.8 Vorschlag Fassung 3 — die Erholung nach dem Boden mitnehmen (begründet aus §15.7, E-63)

| | |
|---|---|
| **Gedanke** | Altcoin-Spot nicht als *Halten bis zur Altcoin-Saison*, sondern als **Gegenbewegung über Wochen**: Bodenkauf mit Wende (A1, der Zeitpunkt trennt) und **schnelle Gewinnmitnahme**, bevor die Erholung verpufft. Das ist dieselbe Wette wie die REGEL0, nur auf Tagesbasis, ohne Hebel, über Wochen |
| **X4** | die Hälfte bei **+30 %**, der Rest bei **+60 %**; Nachlauf −20 % vom Hoch; höchstens 120 T |
| **X5** | ganz bei **+40 %**; Stop −25 % vom Einstieg; höchstens 90 T |
| **Klassen** | H, M, S |
| **Messung, Regel** | wie §15.4/§15.5: gegen BTC an denselben Tagen, Nullwelt, Kosten, Tagesklammer, E2 wählt, E3 bestätigt einmal |
| ⚠️ **Ehrlich** | Die Gewinnziele sind aus dem **E2**-MFE abgeleitet (+39 %), nicht nachgestellt. **E3 ist nicht mehr ganz unberührt**: Sein MFE (+16 %) ist jetzt bekannt. Es ist der dritte Blick auf die Altcoin-Daten, also **Beschreibung**. Der echte Test wäre vorwärts |

### 15.9 Messplan Altcoin Fassung 3 — Swing UND Zyklus, VOR der Messung (06.10.2026; Nutzer: *„die Zeiträume sind eng … ein Zyklus ist länger als ein Kalenderjahr“* · *„Ja“*)

**Einstieg:** A1 Boden je Coin mit Wende (§15.3). Er trennt nachweislich besser als Zufall, das fallende Messer (A2) nicht. Klassen H, M, S.

| Ausstieg | Regel | höchstens |
|---|---|---|
| **X4 Swing gestaffelt** | ½ bei Schluss ≥ **+30 %**, Rest bei ≥ **+60 %**; Nachlauf −20 % vom Hoch seit Einstieg auf den Rest | 120 T |
| **X5 Swing einfach** | alles bei Schluss ≥ **+40 %**; Stop bei Schluss ≤ **−25 %** vom Einstieg | 90 T |
| **X6 Zyklus** | Halten, bis das **Klima** endet: BTC-Klima war nach dem Einstieg über **0,80** und fällt **0,10** unter sein Zyklushoch (K2-Regel) **oder** die Altseason-Breite (Top 50 gegen BTC über 90 T, §13.4) erreicht **75 %** (das Endsignal aus S1) | **1.095 T** |

Alle Ausstiege werden am Folgetag zum Schluss ausgeführt.

**Nullwelten** (beide, je Ereignis 20 Zufallseinstiege desselben Coins, gleiche Ausstiegsregel):
- **N1:** im selben Kalenderjahr (wie Fassung 2);
- **N2 Zyklus:** im Abstand von bis zu **±365 Tagen** um das Ereignis. Sie zeigt, ob der Boden im **Zyklus** besser lag.

**Trägt (vorab):** in **E2 und E3** Mittel **und** Median des Vorteils gegen BTC (Tagesklammer, nach Kosten) > 0 **und** Rang ≥ 0,95 in **N1 und N2**.

**Sonst wie §15.4:**
- Kosten 1,25 % je Seite (BTC 0,4 %);
- eingestellte bis zum letzten Kurs;
- **offene** Handel am Datenende werden zum letzten Kurs bewertet und getrennt ausgewiesen.

⚠️ **Ehrlich:**
- Die Ziele von X4/X5 kommen aus dem E2-MFE (+39 %). Der E3-MFE (+16 %) ist bekannt.
- X6 hat nur **etwa zwei** Zyklen, und der ETF-Zyklus ist **nicht abgeschlossen**; viele E3-Handel sind offen.
- Es ist der dritte Blick auf die Altcoin-Daten: **Beschreibung**.

### 15.10 Ergebnis Altcoin Fassung 3 (06.10.2026, nach §15.9) — und WORAN

Belege:
- `Spot_Voranalyse_04_10/a3_messung.py` → `.txt`
- Gegenprobe `a3_gegenprobe.py` → `.txt`: 15 von 15 Handeln gleich (eigene Schleife direkt aus SQL), dazu die Ausstiegsgründe von X6

**Vorteil gegen BTC (an denselben Tagen, nach Kosten; Tagesklammer Mittel / Median; Rang N1 / N2):**

| Fall | E2 2021–23 | E3 ETF-Markt | E3: Coin selbst (Median) · offen |
|---|---|---|---|
| H · X4 gestaffelt | **+21 % / +16 %** · 0,99 / 0,95 (n 15) | −1 % / −1 % · 0,63 / 0,53 (n 11) | +4 % · 36 % |
| H · X5 +40/−25 | **+23 % / +24 %** · 0,93 / 1,00 | −3 % / −3 % · 0,43 / 0,33 | +3 % · 36 % |
| H · X6 Zyklus | −0 % / +2 % · 0,57 / 0,69 | +2 % / +0 % · 0,74 / 0,60 | +4 % · **82 %** |
| M · X4 / X5 | +2 % / −0 % · +0 % / −5 % · Rang 0,83–0,94 | −4 % / −10 % · −3 % / −8 % | −13 % / −24 % |
| M · X6 | +4 % / −5 % · 0,67 / 0,67 | **−15 % / −14 %** · 0,12 / 0,12 | −12 % · 59 % |
| S · X4 / X5 | +6 % / +1 % · +4 % / −3 % · Rang **1,00 / 1,00** | −7 % / −11 % · −11 % / −14 % · Rang 0,08–0,28 | −14 % / −25 % |
| S · X6 | +10 % / −0 % · 0,81 / 0,99 | **−16 % / −19 %** · 0,54 / 0,27 | −15 % · 53 % |

- **Nach der vorab festen Regel: keine der 9 Kombinationen trägt.**
- **Nächster Kandidat:** Highcaps mit Swing (H · X4/X5). In E2 ist der Vorteil gegen BTC deutlich, der Rang 0,93–1,00. In E3 liegt er bei null: n 11, davon 36 % noch offen.
- **Länger halten (X6) hilft nicht.** In E2 ist es schlechter als der Swing, in E3 bei M/S am schlechtesten.

**WORAN:**

| | |
|---|---|
| **Der Bruch ist die EPOCHE, nicht die Regel** | Drei Fassungen, ein Muster. In E2 schlägt der Bodenzeitpunkt den Zufall (S: Rang 1,00 mit jeder Führung). In E3 fällt er **unter** den Zufall (S · X4: 0,08). Nach dem Boden mit Wende fällt der Coin in E3 **auch absolut** (M/S Median −13 bis −25 %), während BTC ±0 % macht. Die *Wende über den 50-T-Schnitt* ist in E3 bei M/S kein Boden mehr |
| **X6 ist kein Zyklus-Halten geworden** | Ausstiegsgründe X6 (alle Klassen): **E2** Breite 451 · K2 89 · Frist/Ende 17. **E3** Frist/Ende **450** · K2 210 · Breite 67. In E2 löst die Altseason-Breite schon bei **kurzen** Alt-Rallyes aus (90-T-Fenster; Halten 152–182 T im Mittel). In E3 ist der Zyklus **nicht abgeschlossen**: 53–82 % der Handel sind offen. ⇒ X6 kann für E3 **noch nicht** urteilen |
| **Highcaps sind die Ausnahme, aber dünn** | 15 bzw. 11 Ereignisse an 9 bzw. 10 Tagen. Das reicht nicht für eine Regel |

**Zwischenfazit zum Ziel (Potential je Asset und Handlung):**
- Ein Altcoin-Spot-Signal *Boden mit Wende* hatte 2021–23 Potential gegen BTC (Highcaps deutlich, Smallcaps im Zeitpunkt).
- Im ETF-Markt hat es das bisher **nicht**. Dort ist BTC der bessere Spot-Wert.
- Ein Betriebssignal folgt daraus **nicht**.
- Was bleibt: **Auskunft** in der Mail (Boden + Wende als Fakt neben dem Klima) und die Wiedervorlage vorwärts, sobald der ETF-Zyklus abgeschlossen ist (X6 offen).

**Messbare Ursache für E3 (Vorschlag, noch nicht gemessen):** Verwässerung durch Token-Freigaben.
- `umlaufmenge_cg.db` hat Tageswerte erst ab 21.09.2025.
- Messbar sind damit nur A1-Ereignisse ab etwa 03/2026, mit 180-T-Wachstum **vor** dem Ereignis.
- Das wäre der vierte Blick auf die Daten: **Beschreibung**.

## 16. Makro-Liquidität, Verwässerung und externe Recherche — Voranalyse und Messplan VOR der Messung (06.10.2026)

Nutzer 06.10.: *„Denke, du solltest noch wichtige Makrodaten wie Liquiditätsausweitung etc. heranziehen und eine externe Recherche zu unseren Themen durchführen.“*

⚠️ **Stehende Vorgabe (01.10.):** Übergeordnete Kräfte werden nur **gewichtet**, sie werden **kein Signal und kein Blocker**. Liquidität kommt deshalb höchstens als **Gewicht** in die Klima-Ampel und als **Auskunft** in die Mail.

**Prüffrage:** Hat das Merkmal zur selben Stunde für zwei Assets verschiedene Werte?
- **Nein** bei der Liquidität: Sie ist eine Zeitachse, und deren Fallzahl ist die Zahl der Phasenwechsel (2.599).
- **Ja** bei der Verwässerung: Sie ist ein Kandidat je Asset.

### 16.1 Externe Recherche — was zu unseren Befunden passt

| Thema | Quelle | Aussage | Bezug zu uns |
|---|---|---|---|
| **Altseason nach dem ETF** | Bybit × Block Scholes | Frühere Zyklen: BTC-Dominanz von > 80 % auf < 32 %, Alt-Marktwert ×6–7. 2024 blieb die Dominanz trotz neuer BTC-Hochs fast flach. ETH hat die Führungsrolle verloren (ETH/BTC 0,03 gegen 0,08 im letzten Zyklus). Mögliche Ursache: Kapital in Spot-ETFs **gebunden**, die Rotation fällt aus | **deckt §15.10:** Der Bruch ist die Epoche E3 |
| **M2 und BTC** | CF Benchmarks (monatlich 2000–02/2026) | 4-Jahres-Korrelation 0,4–0,6; R² 0,71–0,90 im Jahr 2022. **2025/26 entkoppelt:** M2 +12 %, BTC −12 %, R² auf 0,59, Abstand zum Modellwert 46 % | Liquidität erklärt **nicht** stabil, gerade in E3 nicht |
| **„M2 führt BTC um 10–13 Wochen“** | Au79, Netliquidity, arXiv 2607.26188 | Verbreitete Faustregel; als Artefakt **einer** Epoche kritisiert | Verzögerung nur als Auskunft, nicht als Hauptarm |
| **Indikatoren verfallen** | arXiv 2607.26188 („Bitcoin Runs on a Clock“) | Pi Cycle, **MVRV**, Mayer, Puell: Ausschläge werden von Zyklus zu Zyklus kleiner, feste Schwellen veralten. Die Halving-Zeitstruktur sei stabil. **Vorab-Prognose: Boden 05.10.–16.11.2026** | Unser Klima nutzt MVRV, aber als Perzentil im wachsenden Fenster, nicht als feste Schwelle. Die Prognose ist **Auskunft** (ein Autor, nicht begutachtet); sie ist jetzt überprüfbar |
| **Token-Freigaben** | Keyrock (16.000 Freigaben, 40 Tokens) | 90 % drücken den Kurs. Wirkung beginnt **30 T vorher**. Große Freigaben (> 5 % des Umlaufs): Median −8 bis −15 %. **Team-Freigaben −25 %**, Ökosystem +1 % | Ursache für E3 plausibel: 2024er Tokens starteten mit im Schnitt **12 % Umlauf** zum vollen Wert |
| **Querschnitt Krypto** | Liu, Tsyvinski, Wu (NBER 25882); Studie zu Größe und Umsatz | **Momentum** über 1–4 Wochen trägt im Querschnitt. Kleine, illiquide Coins zeigen **kurzfristige Umkehr**, große und liquide Momentum | Unser Bodenkauf ist eine **Umkehr**-Wette über Wochen. Die Literatur spricht für Umkehr nur kurz und nur bei Kleinen, sonst für **Momentum** → mögliche Fassung 4 |
| **Altseason-Auslöser** | Acheron, Block Scholes | ETH/BTC über dem 250-T-Schnitt, Dominanz unter dem 250-T-Schnitt, wachsender Stablecoin-Umlauf, Zinssenkungen | Stablecoins: siehe 16.2 |

### 16.2 Vorprüfung Datenlage (`l1_vorpruefung.py` → `.txt`, nur Datenlage)

Quellen ohne Schlüssel, live:
- FRED `fredgraph.csv`: WALCL, WTREGEN, RRPONTSYD, M2SL, bis 30.09.2026;
- DefiLlama: Stablecoins gesamt, bis 06.10.2026.

| | |
|---|---|
| **Netto-Liquidität USA** (Fed-Bilanz − TGA − RRP) | heute **5,78 Bio. USD**, RRP praktisch leer (0,012 Bio.). 13-W-Änderung ab 2019: steigend in **52 %** (E2) und **48 %** (E3) der Zeit; **14** bzw. **27** Vorzeichenwechsel ⇒ als Zeitachse **messbar**, mit zirkulärer Nullwelt |
| **Stablecoin-Umlauf** (91-T-Änderung) | E2 nur **2** Wechsel; E3 zu **89 %** steigend, 4 Wechsel ⇒ als Zeitachse **nicht messbar**, nur Auskunft. ⚠️ **Fakt dazu:** In E3 wuchs der Stablecoin-Umlauf fast durchgehend, und die Altcoins fielen trotzdem gegen BTC (§15.10). Die Faustregel *Stablecoins steigen → Alts steigen* hat in E3 **nicht** gegolten |
| **Verwässerung** (Umlaufmenge 180 T vor dem Ereignis) | Coin Metrics `splycur` 66 Coins ab 2013 (eher ältere Coins); CoinGecko `umlaufmenge_cg` ab 21.09.2025. A1-Ereignisse mit Wert: **E2 86** (H 6, M 28, S 52), **E3 209** (H 6, M 31, S 172) |

### 16.3 Messplan (vorab; Einstieg A1, Ausstiege X4/X5 wie §15.9; Vergleich, Kosten und Tagesklammer wie §15.4)

| | Frage | Zustand / Gruppe | Trägt (vorab) |
|---|---|---|---|
| **L1** | Bringt der Bodenkauf bei **steigender** Netto-Liquidität mehr gegen BTC? | 13-W-Änderung des **zuletzt veröffentlichten** Wochenwerts am Ereignistag (Mittwochswert gilt ab Freitag): steigend gegen fallend. Klassen **gepoolt**, je Klasse Auskunft. Verzögerung 13 W nur als Auskunft | Unterschied (steigend − fallend) **> 0 in E2 und E3** und Rang **≥ 0,95** gegen 200 **zirkuläre Verschiebungen** der Liquiditätsreihe (mindestens 26 W). Je X4 und X5 |
| **L2** | Stablecoin-Umlauf | — | **nur Auskunft** (zu wenige Wechsel) |
| **L3** | Bringt **geringe Verwässerung** mehr gegen BTC? (Kandidat je Asset) | Umlaufwachstum 180 T vor dem Ereignis, Hälften am Median **je Epoche**. Wachstum > +300 % oder Sprung > 50 % an einem Tag gilt als Datenfehler (Token-Umstellung): ausgeschlossen und ausgewiesen; bei CoinGecko nur `urteil = ok` | niedrig − hoch **> 0 in E2 und E3**, Rang **≥ 0,95** gegen 200 Permutationen des Wachstums innerhalb der Epoche. Je X4 und X5 |
| **L4** | **Kern:** Liquidität als zusätzliches **Gewicht** zum BTC-Klima? | BTC-Folgeertrag 180 T je Tag, nach Klima-Drittel (q) × Liquidität steigend/fallend | in E2 und E3 je Klima-Drittel steigend − fallend > 0 **und** Rang ≥ 0,95 (zirkulär, wie L1). Sonst bleibt die Liquidität Auskunft in der Ampel |

- **Mehrfachtesten:** 5 Hauptfragen (L1 ×2, L3 ×2, L4). Die Forderung *beide Epochen* gilt überall.
- **Folge:**
  - Trägt eines davon, kommt es als **Gewicht** in die Ampel bzw. ins Altcoin-Signal; Voranalyse vor dem Bau.
  - Trägt nichts, geht die Liquidität als **Fakt** in die Ampel und die Mail; die Altcoins gehen nach D4.

⚠️ **Ehrlich:**
- Es ist der vierte Blick auf die Altcoin-Ereignisse: **Beschreibung**.
- Bei L3 ist die Fallzahl in E2 klein (86), und Coin Metrics deckt eher Überlebende ab.
- L4 überschneidet sich mit der Klima-Messung K3 (gleiche Tage).
- **Möglicher nächster Schritt aus der Recherche, kein Teil dieses Plans:** Fassung 4 **Momentum** statt Umkehr (Querschnitt der H/M-Coins gegen BTC), eigener Plan nach diesem Ergebnis.

### 16.4 Ergebnis L1–L4 (06.10.2026, nach §16.3) — und WORAN

Belege:
- `Spot_Voranalyse_04_10/l_messung.py` → `.txt`
- Gegenprobe `l_gegenprobe.py` → `.txt`, eigener Rechenweg:
  - Liquiditätszustand 1.295 von 1.295 gleich;
  - Umlaufwachstum 8 von 8 gleich;
  - L1-Unterschied E2/E3 gleich;
  - L4 *q Mitte* E2/E3 gleich.

⚠️ In E1 steht bei L1 *Rang 0,00*, weil alle Ereignisse in steigende Liquidität fielen. Dort ist kein Vergleich möglich; E1 ist ohnehin nur Auskunft.

**Nach der vorab festen Regel trägt keine der fünf Fragen.**

| | E2 2021–23 | E3 ETF-Markt | Urteil |
|---|---|---|---|
| **L1** Liquidität × Bodenkauf, X4 | steigend +15,6 % gegen fallend +2,6 % gg. BTC · **+12,9 Pp, Rang 0,97** (nur 70 von 557 Ereignissen in steigender Liquidität) | −6,8 % gegen −7,8 % · +1,0 Pp, Rang **0,57** | trägt nicht (E3) |
| **L1** X5 | +11,0 Pp, Rang 0,94 | +1,3 Pp, Rang 0,56 | trägt nicht |
| **L2** Stablecoins (Auskunft) | steigend +2,6 % · fallend +5,4 % | steigend **−9,3 %** · fallend −0,2 % | Faustregel in **beiden** Epochen **umgekehrt** |
| **L3** geringe gegen hohe Verwässerung, X4 | +3,7 Pp, Rang 0,81 (n 85) | **−8,6 Pp**, Rang 0,04 (n 191, 15 Datenfehler aus) | trägt nicht; in E3 eher umgekehrt |
| **L3** X5 | +4,7 Pp, Rang 0,73 | −8,0 Pp, Rang 0,08 | trägt nicht |
| **L4** Kern BTC 180 T, *q Mitte* | **+68,7 Pp**, Rang 0,91 | +20,9 Pp, Rang 0,58 | trägt nicht |
| **L4** *q billig* / *q teuer* | −1,0 Pp (0,56) / nicht beurteilbar (fast nur steigend) | nicht beurteilbar (54 Tage, alle steigend) / **−14,0 Pp** (0,27) | trägt nicht. Auskunft E1 2019/20: steigende Liquidität ging **schlechter** aus (−87 / −58 Pp) |

**WORAN:**

| | |
|---|---|
| **Liquidität wirkte 2021–23, im ETF-Markt nicht** | Das passt genau zur Recherche (CF Benchmarks: 2025/26 entkoppelt). Ein Gewicht, das in der laufenden Epoche nichts trennt, verbessert die Ampel nicht. In E2 hängt der Effekt zudem an **70** Ereignissen in wenigen Phasen |
| **Stablecoins: das Gegenteil der Faustregel** | Wachsender Stablecoin-Umlauf ging in **beiden** Epochen mit **schlechteren** Bodenkäufen einher. Wenige Phasen, also keine Regel, aber die Faustregel ist für uns widerlegt |
| **Die Verwässerung ist mit unseren Daten NICHT messbar** | Coin Metrics zeigt bei **45 von 85** (E2) bzw. **29 von 48** (E3) Ereignissen **keine** Veränderung in 180 T. Vermutlich zählt die Reihe bei vertragsgebundenen Tokens die ausgegebene Menge, und Freigaben aus Sperrverträgen sieht sie nicht (nicht geprüft). CoinGecko gibt es erst ab 09/2025. **Und:** Keyrock misst **bevorstehende** Freigaben (Wirkung ab 30 T vorher), wir die **vergangene** Ausweitung. Das ist eine andere Frage. ⇒ **Verworfen, weil:** kein historischer Freigabekalender. **Neu prüfen, falls** ein Freigabekalender (z. B. Tokenomist) mit Historie verfügbar ist |
| **Kern: Liquidität ändert das Klima-Urteil nicht stabil** | Das Vorzeichen wechselt zwischen den Epochen (E1 negativ, E2 und E3 *Mitte* positiv, E3 *teuer* negativ) |

**Zwischenfazit zum Ziel:**
- Die Makro-Liquidität **rettet** den Altcoin-Spot nicht. Sie **bestätigt** den Bruch im ETF-Markt: 2021–23 hing der Erfolg des Bodenkaufs an der Liquidität, seit 2024 nicht mehr.
- **Für den Betrieb:**
  - Netto-Liquidität (Stand und 13-W-Richtung) und Stablecoin-Umlauf kommen als **Fakt** in die Klima-Ampel und die Mail, ohne Gewicht (Vorgabe 01.10.).
  - Am Kern-Aufbau 70/20/10 mit R1 ändert sich nichts.
- **Nächster Schritt (Nutzer):**
  - entweder Fassung 4 **Momentum** statt Umkehr (Literatur §16.1), eigener Plan;
  - oder D4: Altcoin-Spot ruht als Regel, Auskunft in der Mail, Wiedervorlage vorwärts.

## 17. Messplan Altcoin Fassung 4 — Momentum statt Umkehr, VOR der Messung (06.10.2026; Nutzer: *„Ok, messe alles durch und stimmen die Punkte danach ab“*)

**Warum Fassung 4 (E-63):**
- Drei Fassungen *Bodenkauf* (eine Umkehr-Wette) tragen nicht (§15.7, §15.10).
- Die Literatur (§16.1) findet im Krypto-Querschnitt **Momentum**. Eine Umkehr gibt es nur kurz und nur bei kleinen, illiquiden Coins.
- ⇒ Die Gegenhypothese wird gemessen: **Stärke kaufen statt Schwäche.**

| Fall | Regel | Klassen |
|---|---|---|
| **M1 Querschnitt 4 W** | Am Monatsersten t: Rang der Coins der Klasse nach Ertrag **gegen BTC** über 28 T. Kauf des **oberen Fünftels** (mindestens 2), gleich gewichtet, Schluss t+1; Verkauf nach 28 T | H, M, S |
| **M2 Querschnitt 12 W** | wie M1, Rückblick **84 T** | H, M, S |
| **M3 Trend gegen BTC je Coin** | Kauf, wenn Coin/BTC über seinen 50-T-Schnitt schließt **und** der 28-T-Ertrag gegen BTC > 0 ist (Signal t, Kauf t+1). Verkauf, wenn Coin/BTC unter den 50-T-Schnitt schließt (t+1), höchstens 365 T. Neuer Kauf erst nach dem Verkauf | H, M, S |
| *M0 Auskunft* | Literatur 1 W: Rückblick 7 T, Halten 7 T, wöchentlich, **brutto und netto** | H, M |

**Maßstab und Kosten (wie §15.4):**
- Vorteil gegen BTC an denselben Tagen; Coin 1,25 % je Seite, BTC 0,4 %.
- Bei M1/M2 voller Umschlag je Monat. Als Auskunft kommt **brutto** dazu, damit Signal und Kosten getrennt sichtbar sind.
- Eingestellte bis zum letzten Kurs.
- Klasse am Monatsersten wie §14; gerankt werden nur Coins mit Kurs an t und t−Rückblick.

**Nullwelten:**
- **M1/M2:** am selben Monatsersten **zufällig** gleich viele Coins derselben Klasse, 200 Ziehungen. Die Frage: Bringt die **Auswahl** etwas?
- **M3:** 20 Zufallseinstiege desselben Coins im selben Kalenderjahr, gleiche Ausstiegsregel (N1 wie §15.4).

**Statistik:**
- M1/M2: Vorteil je Monat (Portfolio), Mittel und Median über die Monate.
- M3: Tagesklammer je Einstiegstag.

**Trägt (vorab):** in **E2 und E3** Mittel **und** Median > 0 **und** Rang ≥ 0,95.
- 9 Fälle (M1–M3 × H/M/S). M0 und E1 nur Auskunft.

**Folge:**
- Trägt ein Fall: Voranalyse für den Betrieb (Signal je Monat, Bitpanda-Katalog, Betriebsprüfung).
- Trägt keiner: WORAN, dann Abstimmung über D4.

⚠️ **Ehrlich:**
- Es ist der fünfte Blick auf die Altcoin-Daten seit §14: **Beschreibung**.
- M1/M2 haben je Epoche nur rund 36 bzw. 32 Monate.
- Die Ränge vergleichen Coins untereinander (Regel 3 erlaubt den Querschnitt). Ein **Hebel** folgt daraus nie (Regel 3).

### 17.1 Ergebnis Fassung 4 Momentum (06.10.2026, nach §17) — und WORAN

Belege:
- `Spot_Voranalyse_04_10/m4_messung.py` → `.txt`
- Gegenprobe `m4_gegenprobe.py` → `.txt`: 10 von 10 gleich; vier Monatsportfolios (Auswahl und Ertrag) und sechs Trend-Handel mit eigener Schleife direkt aus SQL

**Vorteil gegen BTC nach Kosten (M1/M2 je Monat, M3 je Handel mit Tagesklammer):**

| Fall | E2 Mittel / Median · Rang | E3 Mittel / Median · Rang | E3 brutto · ganze Klasse |
|---|---|---|---|
| M1 4 W · H | −3,4 / −5,3 % · 0,14 | −1,9 / −2,7 % · **0,95** | −0,3 % · **−4,6 %** je Monat |
| M1 · M | +0,5 / −6,9 % · 0,65 | −10,0 / −12,9 % · 0,03 | −8,4 % · −8,2 % |
| M1 · S | +3,0 / −6,5 % · 0,86 | −8,9 / −8,1 % · **0,00** | −7,3 % · −7,0 % |
| M2 12 W · H/M/S | −1,4 bis +2,8 % / Median ≤ −2,4 % | −2,4 bis −8,6 % · Rang 0,02–0,92 | −0,8 bis −7,0 % |
| M3 Trend · H | +1,5 / −4,1 % · 0,44 | −1,7 / −4,3 % · 0,93 | −0,1 % |
| M3 · M | +0,9 / −5,0 % · 0,29 | −5,5 / −6,4 % · **0,00** | −3,9 % |
| M3 · S | +2,5 / −4,8 % · **1,00** | −4,9 / −5,8 % · **0,00** | −3,3 % |
| *M0 1 W (Auskunft)* | H −1,1 % · M −1,1 % (brutto +0,6 %) | H −2,0 % · M −3,7 % (Rang 0,01) | brutto −0,3 / −2,1 % |

- **Nach der vorab festen Regel: keiner der 9 Fälle trägt.**
- **M3:** Die Haltedauer liegt bei nur 8–14 T, und nur 14–23 % der Handel schlagen BTC.

**WORAN:**

| | |
|---|---|
| **Im ETF-Markt dreht Momentum bei M/S ins Gegenteil** | Ausgewählte Stärke ist **schlechter** als eine Zufallsauswahl (Rang 0,00–0,03). Stärke bei Mid- und Smallcaps kehrt um. Das ist der Gegenbefund zu §15: Dort war der Boden *besser als Zufall* (E2), aber gegen BTC verloren. Hier ist es weder das eine noch das andere |
| **Highcaps: Auswahl hilft, gegen BTC reicht es nicht** | In E3 liegt die ganze H-Klasse im Mittel bei **−4,6 % je Monat** gegen BTC. Die Momentum-Auswahl verliert nur −1,9 % (Rang 0,95), aber sie verliert |
| **Nicht die Kosten, die Grundrate** | Schon **brutto** ist E3 bei M/S negativ (−3 bis −8 %). Kosten verschlimmern, entscheiden aber nicht |
| **Literatur (1 W) bei uns nicht nachweisbar** | brutto +0,6 % in E2, negativ in E3. Die Befunde aus 2014–2018 gelten im ETF-Markt nicht mehr |

## 18. Gesamtbild Altcoin-Spot nach vier Fassungen und der Makro-Messung — Punkte zur Abstimmung (06.10.2026)

**Was jetzt feststeht** (§14.6, §15.7, §15.10, §16.4, §17.1; je mit Gegenprobe):

| | |
|---|---|
| **Grundrate** | Im ETF-Markt verliert **jede** Altcoin-Klasse gegen BTC: Highcaps −16 %/−29 % (§14.6), je Monat H −4,6 %, M −8 %, S −7 % (§17.1) |
| **Zeitpunkt** | Umkehr (Bodenkauf, 3 Fassungen) und Stärke (Momentum, 3 Formen) überwinden die Grundrate nicht. Mit Führung, ohne Führung, kurz, über den Zyklus |
| **Makro** | Liquidität trennte 2021–23, im ETF-Markt nicht. Stablecoins sind umgekehrt zur Faustregel. Die Verwässerung ist mit unseren Daten nicht messbar |
| **2021–23** | Es gab Potential: Highcaps-Swing +21/+23 % gg. BTC, Liquidität +13 Pp. Diese Lage besteht seit 2024 **nicht** |
| **Ehrlich** | Es sind viele Blicke auf dieselben Daten. Die Ergebnisse sind **Beschreibung**, sie stimmen aber in **einer** Richtung überein |

**Zur Abstimmung:**

| # | Punkt | Vorschlag |
|---|---|---|
| **A1** | Altcoin-Spot als **Regel** | **D4: ruht.** Kein Kauf- oder Verkaufssignal für Altcoins im Spot |
| **A2** | **Vorwärtstest** statt weiterer Rückblicke | Ab jetzt werden Boden + Wende (A1/X5) und die Momentum-Auswahl der Highcaps (M1-H) **protokolliert**, ohne Geld, als Fakt in der Ampel. Abrechnung nach 6 und 12 Monaten gegen BTC. Das ist der einzige saubere Test (E-63) |
| **A3** | **Wiedervorlage** mit Auslöser statt Kalender (Regel 1) | erneute Messung, sobald (a) die Altseason-Breite ≥ 75 % erreicht oder (b) Liquidität und BTC wieder gleichlaufen. Spätestens ist die Abrechnung aus A2 der Anlass |
| **A4** | **Klima-Ampel und Fakt-Mail** (S7/O27, Ersatz für die angehaltene Kette) | als Fakten ohne Gewicht: BTC-Klima q mit K1-Hinweis und Rückkauf-Hinweis, Netto-Liquidität (Stand + 13-W-Richtung), Stablecoin-Umlauf, Altseason-Breite, BTC-Dominanz, Protokoll aus A2. Danach als nächster **Bau**: Voranalyse, dann Betriebsprüfung am NB |
| **A5** | **Kern** | unverändert: 70/20/10 (BTC/ETH/SOL) mit Ausgleich über die Raten (R1), K1 als Hinweis |
| **A6** | **Verwässerung** | verworfen, bis ein Freigabekalender mit Historie verfügbar ist; Quelle prüfen nur auf Wunsch |

### 18.1 Begriffsklärung „ETF-Markt“ (06.10.2026; Nutzer: *„es hört sich an, als ob wir ETF traden“*)

- **„ETF-Markt“ ist nur der Name der Epoche E3:** der Zeitraum **ab 11.01.2024**, dem ersten Handelstag der US-Spot-ETFs auf BTC.
- **Gehandelt und gemessen werden ausschließlich Coins** (Kurse aus `messdaten.db`, Kosten wie Bitpanda), **keine ETFs**.
- **Gemessen ist nur:** Ab 2024 verhalten sich die Altcoins gegen BTC anders als 2021–23.
- **Nicht gemessen ist, dass die ETFs die Ursache sind.** Das ist eine Vermutung aus der Recherche (Block Scholes, §16.1: Kapital in BTC-ETFs gebunden). Andere Ursachen sind ebenso möglich, etwa mehr neue Tokens mit kleinem Umlauf, Memecoins oder die Zinslage.
- **Ab jetzt** steht in neuen Texten **„E3 (ab 2024)“** statt „ETF-Markt“, damit der Name keine Ursache unterstellt. Ältere Abschnitte bleiben unverändert und sind so zu lesen.

## 19. Neue Zielgröße Altcoins: ASYMMETRIE statt Durchschnitt (06.10.2026; E-71)

Nutzer 06.10.: *„Altcoins sind mehr als 2 Jahre gefallen und sollten einen gewissen Boden erreicht haben, und je nach Wirtschaftslage kann es auch wieder eine massive Altseason geben. Offenbar haben wir aber keine Lösung zur Thematik, wie wir die Altcoin-Diamanten finden. Ziel sollte sein, aus den unsicheren Assets jene zu identifizieren, welche ein ausgewogeneres bzw. möglichst asymmetrisches Chance-Risiko-Verhältnis aufzeigen.“*

**Was das an §14–§18 ändert:**
- Die vier Fassungen fragten: *Schlägt eine Regel BTC im **Mittel und Median**?*
- Diamanten zu finden ist eine Frage nach dem **rechten Ende**: wenige große Gewinner, viele Verlierer. Bei einer solchen Verteilung ist der **Median von Natur aus negativ**.
- ⇒ Die Forderung *Median > 0* hätte jede Diamanten-Strategie **schon vom Aufbau her** verworfen. Die Ergebnisse §14–§18 bleiben gültig, beantworten aber **diese** Frage nicht.
- A1–A6 (§18) ruhen bis zur Asymmetrie-Messung. Unabhängig davon gilt: Der Kern bleibt unverändert, Liquidität und Stablecoins sind Fakt.

**Fakt Lage heute** (Auskunft, keine Bewertung — Regel 4; Klasse am Monatsersten, Median je Coin):

| Stichtag | Klasse | Abstand zum Allzeithoch | gegen BTC | Hoch vor |
|---|---|---|---|---|
| 01.01.2023 (Boden davor) | H / M / S | −89 / −93 / −93 % | −73 / −81 / −84 % | 20 / 16 / 18 Monaten |
| **20.09.2026** | H / M / S | **−83 / −95 / −97 %** | **−90 / −96 / −98 %** | **44 / 31 / 56 Monaten** |

⇒ Die Altcoins stehen heute **tiefer und länger** unter dem Hoch als am Boden 2023, gegen BTC deutlich tiefer. Das ist ein **Fakt**. Ob daraus ein Boden folgt, ist eine Bewertung und erst zu messen.

**Weg (Vorschlag, Voranalyse folgt nach Ja):**

| | |
|---|---|
| **Zielgröße** | je Asset und Monatserstem über 12 und 24 Monate: **rechtes Ende** (Anteil ≥ ×3 bzw. ≥ ×2 des Einstiegs, höchster Stand) gegen **linkes Ende** (Anteil ≤ −70 %, eingestellt). Zusätzlich das Ergebnis eines **Korbs** kleiner gleicher Einsätze gegen BTC |
| **Merkmale je Asset** (Querschnitt, Regel 3) | Tiefe und Dauer des Absturzes · **Basisbildung** (Schwankung zusammengezogen; Bezug Spot M-0) · Widerstandskraft (hielt das Tief, fiel weniger als die Klasse) · Umsatz hält trotz Kursverfall · Alter/Überleben · TVL gegen Kurs (188 Protokolle) · aktive Adressen (66 Coins) · Positionierung (Funding, Terminmarkt) |
| **Nullwelt** | Merkmal innerhalb desselben Datums vertauscht |
| ⚠️ **Grenze** | Es gibt nur **zwei** Alt-Aufschwünge in den Daten (2019–21 und 2023/24). In E3 (ab 2024) ist noch keiner abgeschlossen. ⇒ Das Ergebnis ist **Beschreibung**; ein Vorwärtsprotokoll gehört dazu |

### 19.1 Vorprüfung Asymmetrie (`as_vorpruefung.py` → `.txt`; nur Grundrate und Datenlage, kein Merkmalsschnitt)

**Zielgröße je Coin und Monatserstem** (Kauf am Schluss t+1):
- **R2 / R3:** Der höchste Schluss im Fenster erreicht das Zwei- bzw. Dreifache des Einstiegs; das ist das **Potential**.
- **L:** Der tiefste Schluss liegt bei −70 % oder tiefer, **oder** der Coin wird eingestellt.

**Grundrate, Fenster 12 Monate:**

| Epoche | Klasse | Paare / Anker | R2 | R3 | L | davon eingestellt | Endwert Median | Korb gg. BTC |
|---|---|---|---|---|---|---|---|---|
| E1 2019–20 | H / M / S | 96 · 1.464 · 156 | 100 / 79 / 97 % | 93 / 68 / 94 % | 0 / 12 / 10 % | 0 / 3 / 10 % | +304 / +184 / +395 % | +50 / +67 / +99 % |
| E2 2021–23 | H / M / S | 493 · 3.207 · 6.794 (37 Anker) | **35 / 36 / 40 %** | 16 / 19 / 21 % | 21 / 38 / 31 % | 1 / 5 / 8 % | −14 / −39 / −21 % | −11 / −3 / −7 % |
| E3 ab 2024 | H / M / S | 251 · 1.748 · 5.472 (20 Anker) | **25 / 21 / 22 %** | 9 / 7 / 7 % | **30 / 61 / 57 %** | 6 / 4 / 18 % | −45 / −67 / −65 % | −28 / −58 / −57 % |

**24 Monate:**
- In E3 gibt es nur **8** Anker ⇒ nur Auskunft.
- In E2: R2 44–52 %, L 35–62 %.

⇒ **Auch in E3 (ab 2024) verdoppelt sich jeder vierte bis fünfte Coin binnen 12 Monaten zeitweise.** Das rechte Ende ist also vorhanden.

Gleichzeitig enden 57–61 % der Mid- und Smallcaps bei −70 % oder eingestellt. Die Frage ist also, ob ein Merkmal das rechte Ende **anhebt** und das linke **senkt**.

**Datenlage der Merkmalsquellen** (Coin-Anker mit Werten über [t−180, t], 12 Monate):

| Quelle | E2 | E3 | Folge |
|---|---|---|---|
| Kurs und Umsatz | alle | alle | Hauptmerkmale |
| TVL (188 Protokolle) | 20 % (2.092) | 30 % (2.274) | Teilmenge, eigene Nullwelt |
| Aktive Adressen (66 Coins) | 18 % (1.839) | 12 % (926) | Teilmenge, eigene Nullwelt |
| Funding | 29 % (3.054) | 49 % (3.693) | Teilmenge, eigene Nullwelt |
| Terminmarkt OI | 8 % | 18 % | **nur Auskunft** (ab 12/2021) |

**Gegenprobe der Vorprüfung** (`as_gegenprobe_vorpruefung.py` → `.txt`): 12 zufällige Coin-Anker mit eigener Schleife direkt aus SQL, R2/R3/L/eingestellt **12 von 12 gleich**.

### 19.2 Messplan Asymmetrie (vorab)

**Merkmale.**
- Alle Werte sind am Tag t bekannt.
- Gerankt wird je Stichtag **innerhalb der Klasse**.
- Die Richtung ist fachlich **nicht** vorgegeben ⇒ **zweiseitig**: Geprüft werden das oberste **und** das unterste Fünftel.

| # | Merkmal | Definition |
|---|---|---|
| F1 | Tiefe | Schluss t / Allzeithoch bis t − 1 |
| F2 | Dauer | Tage seit dem Allzeithoch |
| F3 | Schwankung | Standardabweichung der Tagesrenditen über 90 T |
| F4 | Basisbildung | Schwankung 90 T / Schwankung 365 T |
| F5 | Abstand zum Tief | Schluss t / 365-T-Tief − 1 |
| F6 | Stärke in der Klasse | 180-T-Ertrag minus Median der Klasse |
| F7 | Umsatzverlauf | mittlerer Umsatz 90 T / 365 T |
| F8 | Alter | Tage seit dem ersten Kurs |
| F9 | TVL gegen Kurs | log(TVL t / t−180) − log(Kurs t / t−180) · Teilmenge |
| F10 | Aktive Adressen | log(30-T-Mittel t / 30-T-Mittel t−180) · Teilmenge |
| F11 | Funding | Mittel der 30 T vor t · Teilmenge |
| *F12* | *OI-Änderung 90 T* | *nur Auskunft* |

**Statistik je Merkmal und Seite (Fünftel):**
- **Saldo** = Anteil R2 − Anteil L im Fünftel, abzüglich desselben Saldos der **ganzen Klasse am selben Stichtag**.
- Erst gemittelt je Stichtag (Klassen nach Paarzahl gewichtet), dann über die Stichtage.
- Ausgewiesen werden zusätzlich:
  - R2-Überschuss und L-Überschuss getrennt, dazu R3;
  - Korb des Fünftels gegen BTC und gegen den Korb der ganzen Klasse;
  - alle fünf Fünftel (Dosis-Wirkung);
  - je Klasse und je Jahr.

**Nullwelt:** das Merkmal innerhalb von Stichtag und Klasse vertauscht, 200 Ziehungen. Bei F9–F11 nur innerhalb der Teilmenge.

**Trägt (vorab), alle drei Bedingungen:**
1. Saldo-Überschuss > 0 in **E2 und E3**, mit Rang ≥ **0,975** in beiden (zweiseitig 5 %).
2. **Spiegelprobe** (stehende Regel 2.603): Lift(R2) / Lift(D2) ≥ **1,717** in E2 und E3. D2 ist das gespiegelte Ereignis *tiefster Schluss ≤ −50 % oder eingestellt*; ×2 und ÷2 sind auf der Log-Skala gleich weit. Ohne diese Probe ist *mehr Potential* nur *mehr Bewegung*.
3. **Je Asset:** Die R2-Treffer des Fünftels stammen in jeder Epoche aus mindestens **10 verschiedenen Coins** (keine Ein-Coin-Geschichte).

**Mehrfachtesten:**
- 11 Merkmale × 2 Seiten = 22 Tests.
- Bei unabhängigen Tests und *beide Epochen bei 0,975* liegt der Fehlalarm je Test bei etwa 0,06 %, für die Familie bei etwa 1,4 %.

**Stufe 2, Kombination** (Einzelbeitrag schwach, die Kombination ist die Anwendung):
- Merkmale, deren eine Seite in **E2** Rang ≥ 0,90 **und** die Spiegelprobe besteht, werden zu einem **Wert** zusammengefasst: Mittel der richtungsgerechten Perzentile innerhalb der Klasse.
- Die Auswahl fällt nur auf E2.
- Das oberste Fünftel des Werts wird **einmal auf E3** geprüft, mit Saldo-Rang ≥ 0,95 und Spiegelprobe.
- Dazu als Auskunft: der Korb gegen BTC.

**Selbsttest der Anlage, vor dem Hauptlauf:**
- (a) 40 **Zufallsmerkmale** durch dieselbe Anlage. Erwartet sind höchstens 2,5 % je Epoche über 0,975, und kein einziges *trägt* in beiden.
- (b) Ein **gepflanztes** Merkmal = R2-Ausgang · 0,3 + Normalrauschen muss *tragen*.
- Fällt (a) oder (b) durch, wird nicht gemessen; erst die Anlage reparieren.

**Die sechs Prüfungen vor jeder Meldung:**
- Nullwelt;
- Zeitstabilität (je Jahr);
- **Weglassprobe**: ohne die 5 Coins mit dem größten Beitrag;
- Mehrfachtesten;
- Ebene: Klasse;
- je Asset.

**Folge:**
- Trägt ein Merkmal oder die Kombination: Voranalyse *Diamanten-Kandidaten* für die Ampel. Gemeint ist eine Liste je Monat mit Begründung als **Auskunft**, mit kleinem Einsatz je Coin, und dazu das Vorwärtsprotokoll.
- Trägt nichts: WORAN, dann Abstimmung.

### 19.3 Gegenprüfung des Plans

| | |
|---|---|
| **Vorgriff** | Alle Merkmale nutzen nur Daten bis t. Umsatz `U90` ist schon um einen Tag verschoben (s3_stufe1), das Allzeithoch reicht bis t, der Kauf erfolgt zum Schluss t+1. TVL, Adressen und Funding gelten am Tag ihres Datums ⚠️; ob das der Veröffentlichungstag ist, wird im Lauf je Quelle ausgewiesen (Tageswert an Stundenanker war schon einmal ein Vorgriff, hier ist die Auflösung Tag gegen Monat) |
| **Überleben** | Eingestellte zählen ins **linke** Ende. Genau das ist bei Smallcaps das Risiko |
| **Grundgesamtheit** | wie §14 (Universum ohne Stablecoins, Sondertokens, BTC/ETH/SOL), Klasse am Stichtag. Nicht verändert |
| **Überlappung** | 12-Monats-Fenster an Monatsersten überlappen. Die Nullwelt vertauscht innerhalb des Stichtags, die Zeitstruktur bleibt erhalten |
| **Fallzahl** | E2 37 und E3 20 Stichtage. H hat nur 13–20 Coins je Stichtag, also 3–4 im Fünftel ⇒ H vor allem gepoolt, je Klasse Auskunft |
| **Ehrlich** | Zwei Alt-Aufschwünge in den Daten. E1 (2019–20) war ein Aufschwung, in dem fast **alles** stieg; dort trennt kein Merkmal, also nur Auskunft. Es ist **Beschreibung**; das Vorwärtsprotokoll ist der eigentliche Test |

## 20. Monatlicher MACD der Altcoins — Messplan VOR der Messung (06.10.2026)

Nutzer 06.10.: *„Prüfe den monatlichen MACD bei den Altcoins – dies war erst 3-mal der Fall und jedes Mal Altseason.“*

**Einordnung:**
- Ein Marktsignal mit **drei** Fällen ist eine **Zeitachse** mit drei Beobachtungen. Eine Nullwelt kann darüber nicht entscheiden (2.599).
- ⇒ Das Ergebnis ist **nur Auskunft**: Wann trat das Signal auf, was folgte, und gab es **Fehlsignale**?
- Gewichtet wird höchstens, wie Makro (Vorgabe 01.10.).

**Daten:**
- CoinMetrics Community API (frei, ohne Schlüssel), Tageswert `CapMrktCurUSD` aller 135 dort geführten Assets.
- Daraus ohne BTC, Stablecoins, Wrapped/Bridge-Tokens und Doppelzählungen (bnb_eth, flow_native, wnxm, leo-Zweitnetz) ein **Altcoin-Marktwert**.
- Schreibt **nur** nach `data/_spot/altcap.db` (Messdatei des Spot-Strangs).
- ⚠️ SOL, TON, HYPE und andere fehlen bei CoinMetrics. Der Index ist also ein Näherungswert, vor allem für die Zeit ab 2021.

**Reihen (alle Auskunft):**

| | |
|---|---|
| **I1** | Altcoin-Marktwert in USD (mit ETH, ähnlich TOTAL2) |
| **I2** | I1 / BTC-Marktwert |
| **I3** | ohne ETH, in USD (ähnlich OTHERS) |
| **I4** | I3 / BTC-Marktwert |

**Signal:**
- MACD(12, 26, 9) auf **Monatsschlüssen**; gilt am Monatsende, Handel ab dem Folgemonat.
- **S:** MACD-Linie kreuzt die Signallinie nach oben.
- **N:** MACD-Linie kreuzt die Nulllinie nach oben.
- Die ersten 35 Monate je Reihe sind Einschwingzeit und werden nicht gewertet.

**Was folgte**, je Signal 3, 6 und 12 Monate danach:
- I1 und I2;
- höchster Stand von I2 in 12 Monaten;
- **Altseason** (vorab):
  - I2 steigt binnen 12 Monaten um **≥ +50 %** gegenüber dem Signalmonat;
  - zusätzlich ab 2018 die Breite aus §13.4: ≥ 75 % der Top 50 schlagen BTC über 90 T.

**Vergleich:**
- alle Monate ohne Signal (Grundrate);
- Zählung der **Fehlsignale**, also Signale ohne folgende Altseason.

**Heute:** Wo stehen MACD und Signallinie jeder Reihe zum letzten Monatsschluss?

### 20.1 Ergebnis monatlicher MACD (06.10.2026, nach §20) — nur Auskunft

Belege:
- `lade_altcap.py`: CoinMetrics, 135 Assets, 347.242 Tageswerte, nach `data/_spot/altcap.db`.
- `macd_messung.py` → `.txt`.
- Gegenprobe `macd_gegenprobe.py` → `.txt`:
  - eigene EMA-Schleife: alle Kreuzungsdaten gleich;
  - Kettenindex in 85 von 86 Monaten ohne Zu- oder Abgang gleich der einfachen Summe. Der eine Monat (04/2023) weicht um 0,3 % ab, weil ein Asset dort an einzelnen Tagen den Marktwert 0 hat.

Der Index umfasst 93 Altcoins (2017: 19, 2021: 87, 2026: 70); SOL, TON und andere fehlen. Gewertet wird ab 12/2016.

| Reihe · Signal | Signale (Monat) | danach Altseason (Alt/BTC ≥ +50 % binnen 12 M) |
|---|---|---|
| **I3 ohne ETH, USD · MACD über Null** (am nächsten an *OTHERS*) | **3:** 03/2017 · 12/2020 · **11/2024** | **JA · JA · nein** (11/2024: Alt/BTC 12 M −23 %, Höchststand nur +21 %) |
| I1 mit ETH, USD · Signallinie | 3: 07/2020 · 11/2023 · 07/2025 | JA · nein · nein |
| I1 · Nulllinie | 2: 11/2020 · 02/2024 | JA · nein |
| I2 Alt/BTC · Signallinie | 5: 03/2017 · 07/2020 · 08/2022 · 12/2024 · 07/2025 | JA · JA · nein · nein · nein |
| I2 · Nulllinie | 1: 04/2017 | JA |
| I3 · Signallinie | 2: 07/2020 · 11/2023 | nein · nein |
| I4 ohne ETH / BTC · Signallinie | 5: 03/2017 · 08/2020 · 01/2021 · 07/2023 · 08/2024 | JA · nein · JA · nein · JA |
| I4 · Nulllinie | 1: 05/2017 | nein |

- **Grundrate:** In **25–26 %** aller Monate folgte binnen 12 Monaten eine Altseason.
- **Über alle Signale:** 2/5 (I1), 3/6 (I2), 2/5 (I3), 3/6 (I4), also rund **40–50 %**. Das ist etwas besser als die Grundrate, aber **nicht „jedes Mal“**.
- **Die Aussage „erst 3-mal, jedes Mal Altseason“** passt in unseren Daten am ehesten zu **I3, Nulllinie**: drei Signale. Die ersten beiden (2017, 2020) gingen einer Altseason voraus, das **dritte (11/2024) nicht**.
  - Die Faustregel stammt vermutlich aus der Zeit **vor** 2024.
  - Seit 2024 gab es in jeder Form **nur Fehlsignale**, außer I4 08/2024 (Höchststand +100 % gegen BTC, danach wieder abgegeben).
- ⚠️ Die Breite ≥ 75 % wird in den 12 Monaten nach fast **jedem** Signal erreicht (87–100 %). Sie trennt hier also nicht.

**Heute** (Monatsschluss 30.09.2026):

| Reihe | Lage |
|---|---|
| I1 und I3 (USD) | MACD unter Null, unter der Signallinie, Histogramm fallend |
| I2 und I4 (gegen BTC) | MACD unter Null, aber **knapp über der Signallinie** (Histogramm leicht positiv) |

**Zwischenfazit:**
- Der monatliche MACD ist mit 1–5 Fällen je Form eine **Auskunft**, kein Signal (Regime nicht vorab erkennbar, 2.599).
- Er gehört als **Fakt** in die Klima-Ampel: Stand von MACD und Signallinie für I2 und I4, letztes Kreuz.
- Die Einschränkung gehört immer dazu: Das letzte Nulllinien-Kreuz (11/2024) war ein Fehlsignal.

### 20.2 Abgleich mit der Quelle des Nutzers (06.10.2026; Bild eines X-Beitrags)

Die Behauptung: *„Der monatliche MACD bei Alts hat gerade bullisch gekreuzt. Die letzten 3 Male: 2017, 2020, 2023. Alle 3 endeten in Altcoin-Saison.“* Das Bild zeigt den Gesamtmarktwert im Monatschart, MACD(12, 26, 9), Kreuz mit der **Signallinie**.

| | Quelle | unsere Messung (I1 Signallinie, ähnlich) |
|---|---|---|
| **Signale** | 2017 · 2020 · 2023 | 03/2017 (I2–I4) · **07/2020 · 11/2023 · 07/2025** |
| **„Altcoin-Saison“** | gemeint: der Alt-Marktwert steigt **in USD** stark | 07/2020: I1 +271 % in 12 M, **BTC +275 %** · 11/2023: I1 **+116 %**, **BTC +159 %**. ⇒ In USD stark, **gegen BTC nicht** |
| **ausgelassen** | — | **07/2025:** I1 −56 % in 12 M (BTC −45 %). Das Kreuz steht in unserer Näherung, im Bild nicht. Unser Index ist ohne SOL, TON und andere; ob das Kreuz im Original-Index fehlt, ist nicht geprüft |
| **„gerade gekreuzt“** | 2026 | In unserer Näherung zum Monatsschluss 30.09. **noch nicht**: Histogramm −3,15, aber steigend seit 06/2026 (−6,80). Der **laufende** Oktober steht bei −1,78. ⚠️ Ein Kreuz auf einer **nicht abgeschlossenen** Monatskerze kann bis zum 31.10. wieder verschwinden (die letzte Periode ist nicht abgeschlossen) |
| **Grundrate** | — | In 24 % aller Monate verdoppelte sich I1 binnen 12 Monaten; Median +12 %, BTC im selben Fenster +57 % |

⇒ **Die Aussage ist in USD für 2020 und 2023 richtig**: Die Altcoins stiegen danach stark. **Gegen BTC** stimmt sie nur für 2017. Im Fenster von 12 Monaten stieg BTC 2020/21 genauso stark und 2023/24 stärker. Das Kreuz 07/2025 fehlt in der Aufzählung. Als **Fakt** für die Ampel taugt der Stand (Histogramm steigt, Kreuz nahe); als Signal mit drei Fällen nicht.

### 19.4 Selbsttest NICHT bestanden — die Spiegelschwelle 1,717 passt hier nicht; Vorschlag *bewegungsgleiche Spiegelprobe* (06.10.2026)

**Selbsttest** (`as_messung.py` → `.txt`):

| Teil | Ergebnis |
|---|---|
| (a) 80 Zufallstests | Rang ≥ 0,975 in E2 zu 2,5 %, in E3 zu 1,2 %, in beiden 0; trägt 0 ⇒ **bestanden** |
| (b) gepflanzt 0,3 · R2 + Rauschen | **sicher gefunden**: Saldo +9,1 / +9,9 Pp, Rang 1,000 / 1,000. Die Spiegelprobe verwirft es aber: 1,21 / 1,38 < 1,717 ⇒ **nicht bestanden** |

⇒ Nach Plan wird **nicht gemessen**. Die Schwelle 1,717 war für **stündliche Hebel-Ereignisse** geeicht (2.603), nicht für 12-Monats-Fenster.

**Eichung nach der Methode vom 26.09.** (`as_eichung_spiegel.py` → `.txt`): Eine **feste** Verhältnisschwelle trennt hier nicht.
- In der reinen Bewegungswelt steigt das Verhältnis mit der Stärke mit: E3 von 1,08 auf 1,48.
- Die Regel *höchstes 97,5. Perzentil* ergäbe 1,557.
- Bei dieser Schwelle fände die Probe die Richtung 0,3 nie, die Richtung 0,6 nur in E3.
- ⇒ Das ist dieselbe Falle wie am 26.09.: **Das Verhältnis vermischt Stärke und Richtung.**

**Vorschlag: bewegungsgleiche Spiegelprobe** (`as_spiegel_bewegt.py`):
- *Hebt ein Merkmal die Chance auf eine Verdopplung so stark wie reine Bewegung, dann muss es das Absturzrisiko **weniger** heben.*
- Verglichen wird mit den **200 Bewegungswelten** (f = s · (R2 + D2) + Rauschen, s von 0 bis 2,0), deren **beobachteter** Lift(R2) dem des Merkmals am nächsten liegt.
- Das Merkmal besteht, wenn sein Lift(D2) **unter dem 2,5. Perzentil** dieser Welten liegt.

| Selbsttest der Probe, je 40 Ziehungen | E2 | E3 | **beide** (das zählt für *trägt*) |
|---|---|---|---|
| Lauf 1/2: Zuordnung über den **Mittelwert** je Stärke (Gitter 0,1 bzw. 0,05) | Bewegung 5–18 % | 0–12 % | 0–5 % ⇒ zu lax je Epoche. Ursache: Ein zufällig hoher Lift wurde mit zu starker Bewegung verglichen |
| **Lauf 3: nächste Nachbarn im beobachteten Lift** (`as_spiegel_nachbarn.txt`) — reine Bewegung | 0–5 % | 0–5 % | **0 %** |
| Lauf 3 — Zufallsmerkmale | 0 % | 8 % | **0 %** |
| Lauf 3 — Richtung s 0,15 / **0,3** / 0,6 | 92 / **100** / 100 % | 75 / **100** / 100 % | 68 / **100** / 100 % |

⚠️ **Ehrlich:**
- Je Epoche schwankt die Fehlalarmquote mit 40 Ziehungen zwischen 0 und 8 %: 3 von 40 sind 7,5 %, das Band reicht bis rund 20 %.
- Entscheidend ist *beide Epochen*: **0 von 200** Bewegungs- und Zufallswelten.

**Zur Freigabe (Nutzer):** In §19.2 wird die Spiegelprobe *Verhältnis ≥ 1,717* durch die **bewegungsgleiche Spiegelprobe (Lauf 3)** ersetzt, in E2 und E3. Alles andere bleibt, wie vorab festgelegt. Danach läuft zuerst der Selbsttest (b) erneut, erst dann die Messung.

### 19.5 Entscheid und Maßstab *Systemfunktion oder Newsletter* — festgelegt VOR dem Ergebnis (06.10.2026; E-72)

Nutzer 06.10.: *„Denke, wir sollten alle Möglichkeiten prüfen und gegenprüfen, du entscheidest jetzt. Wichtig wäre die Zielerreichung, und hier bin ich nicht sicher, ob das ein schlechter Newsletter wird oder echte Systemfunktionalität.“*

**Entschieden:**
- Die bewegungsgleiche Spiegelprobe (§19.4, Lauf 3) ersetzt 1,717.
- Gemessen wird der volle Plan §19.2: alle 11 Merkmale beidseitig, die Kombination E2 → E3, 24 Monate als Auskunft.
- Der Selbsttest läuft erneut vorweg.

**Maßstab, vorab:**

| Ergebnis | Was es ist | Was gebaut wird |
|---|---|---|
| **A · Systemfunktion** | Ein Merkmal **oder** die Kombination *trägt* nach §19.2, **und** der Korb des Fünftels hat in E3 ein besseres Verhältnis aus Chance und Risiko als die Klasse (Saldo > 0, Spiegelprobe besteht) | Monatliche **Kandidatenliste** am NB, ohne Desktop-Handgriff (B1–B9). Je Coin die Begründung und ein **kleiner fester Einsatz**. **Vorwärtsprotokoll** mit Abrechnung nach 6 und 12 Monaten gegen die Klasse und gegen BTC. Erst danach Geld in nennenswerter Höhe |
| **B · Hinweis mit Vorbehalt** | Etwas trägt nur in **einer** Epoche, oder nur die Kombination in E2 | **Kein** Signal. Das Vorwärtsprotokoll läuft ohne Geld; die Entscheidung fällt nach 6 Monaten |
| **C · Newsletter** | Nichts trägt | Nur Fakten in der Ampel (Lage, MACD, Liquidität, Stablecoins), ausdrücklich **ohne** Kaufaussage. Altcoins bleiben Auskunft (D4) |

⚠️ Ein *Newsletter* ist kein Misserfolg, wenn er sich **so nennt**. Schlecht wird er erst, wenn er Fakten wie ein Signal verkauft (Regel 4).

### 19.6 Ergebnis Asymmetrie (06.10.2026, nach §19.2 mit §19.4/§19.5) — Urteil: **A · Systemfunktion, mit Vorbehalt**

**Belege:**
- `as_messung.py` → `.txt`
- Gegenprobe `as_gegenprobe.py` → `.txt`: 66 von 66 Merkmalswerten direkt aus SQL gleich, Saldo und Lifts mit pandas gleich
- Pflichtprüfungen `as_pruefungen_komb.py` → `.txt`

⚠️⚠️ **Korrigiert vor der Bewertung (mein Fehler, im Lauf gefunden):**
- `paare()` nahm auch Stichtage nach 09/2025 auf, deren 12-Monats-Fenster noch offen ist. Dort blieben nur die **später eingestellten** Coins übrig, also eine Auswahl nach der Zukunft.
- Das waren E3 mit 31 statt 20 Stichtagen und 499 Paare. Die Vorprüfung hatte es richtig.
- Die Gegenprobe fand es nicht, weil sie dieselbe Funktion nutzte. Gefunden habe ich es am Beispiel-Stichtag 08/2026, der kein volles Fenster haben kann.
- Alles wurde auf 19.681 Coin-Ankern neu gerechnet. Die Werte unten sind die korrigierten.
- ⚠️ Die Kopfzeilen im Protokoll nennen noch *1,717*. Gerechnet wurde mit der bewegungsgleichen Probe (`spiegel_ok`); die Beschriftung ist inzwischen im Code korrigiert.

**Selbsttest (korrigierte Menge):**
- (a) 80 Zufallstests: in E2 1,2 %, in E3 5,0 %, in beiden 0, trägt 0;
- (b) das gepflanzte Merkmal trägt.
- ⇒ **bestanden.**

**Was trägt (12 Monate; Saldo = Anteil *verdoppelt* − Anteil *−70 % oder eingestellt*, gegen die eigene Klasse am selben Stichtag):**

| | E2 2021–23 | E3 ab 2024 | Korb E3 gg. BTC (ganze Klasse) |
|---|---|---|---|
| **Kombination** (Wahl auf E2: **tiefer Absturz** F1 unten — korrigiert 06.10., siehe §19.7 · lange **Dauer** seit dem Hoch F2 oben · hohes **Alter** F8 oben · **TVL** wächst schneller als der Kurs F9 oben) | +11,0 Pp · Rang 1,000 · Lift R2 1,14 / D2 0,87 | **+13,2 Pp · Rang 1,000 · Lift R2 1,22 / D2 0,94**, Spiegelprobe besteht, 102 Coins | **−34 %** (−48 %) |
| **F8 Alter** allein, oberes Fünftel | +3,2 Pp · Rang 1,000 | +17,2 Pp · Rang 1,000 · R2 1,22 / D2 0,90 | −22 % (−48 %) |
| alle übrigen 20 Einzeltests | trägt nicht | | |

**Die sechs Prüfungen (Kombination):**

| | |
|---|---|
| **Nullwelt** | Rang 1,000 in beiden Epochen |
| **Dosis** | monoton. E2: −6,6 · −3,6 · −2,7 · +1,5 · +11,0 Pp. E3: −18,2 · −1,2 · −0,3 · +5,6 · +13,2 Pp. Das **unterste** Fünftel ist deutlich schlechter, die Ordnung trägt über die ganze Breite |
| **Zeitstabilität** | jedes Jahr positiv: 2019 +15 · 2020 +4 · 2021 +14 · 2022 +9 · 2023 +10 · 2024 +21 · 2025 +4 Pp. ⚠️ 2025: Lift R2 0,81, die Asymmetrie kommt dort nur aus dem **kleineren** Absturzrisiko |
| **Weglassprobe** | ohne die 5 stärksten Coins: E2 +10,4 Pp, E3 +10,3 Pp, Spiegelprobe besteht in beiden ⇒ keine Ein-Coin-Geschichte |
| **Mehrfachtesten** | 22 Einzeltests, 1 trägt (Familien-Fehlalarm vorab ≈ 1,4 %). Die Kombination ist **einmal** auf E3 geprüft |
| **Ebene / je Klasse** | H: E2 −0,1, E3 +27,9 Pp · M: E2 +14,0, E3 +27,5 Pp · S: E2 +10,3, E3 +7,9 Pp. ⇒ In der laufenden Epoche am stärksten bei **Highcaps und Midcaps** |

**Vorbehalte (gehören zu jeder Aussage):**
1. **Gegen BTC verliert auch der beste Korb in E3:** −34 % in 12 Monaten, die Klasse −48 %. Die Asymmetrie gilt **innerhalb der Altcoins**. Sie beantwortet *welche Altcoins*, nicht *Altcoins statt BTC*.
2. **Das Alter trägt mit.**
   - Die Hälfte des Kombinations-Fünftels liegt auch im obersten Alters-Fünftel.
   - Ohne F8 trägt der Rest in E3 nicht: +2,3 Pp, Rang 0,935.
   - F8 allein fällt in E2 bei der Weglassprobe (+0,7 Pp ohne DUSK, FET, WAVES, CTXC, COCOS).
   - ⇒ Die Kombination ist robuster als jedes einzelne Merkmal.
3. **Es ist der fünfte Blick auf die Altcoin-Daten.** Die Wahl fiel auf E2 und wurde einmal auf E3 bestätigt; das ist sauber, bleibt aber **Beschreibung**. Der eigentliche Test ist das Vorwärtsprotokoll.
4. **Für die Praxis zu lang:** Das Fünftel umfasst je Stichtag rund 3 Highcaps, 18 Midcaps und rund 50 Smallcaps (Beispiel 01.09.2025: ADA, LTC, UNI · ALGO, ATOM, NEAR …).

**Inhaltlich:**
- Asymmetrisch sind **etablierte Überlebende am Boden**: lange am Markt, **sehr tief gefallen** (bis 06.10. stand hier fälschlich *weniger tief*, siehe §19.7), das Hoch liegt lange zurück, die Nutzung (TVL) wächst schneller als der Kurs.
- Ihr Vorteil kommt vor allem aus dem **kleineren** linken Ende: weniger Abstürze und weniger Einstellungen.
- In E3 kommt eine höhere Chance auf eine Verdopplung dazu.

**Folge nach dem Maßstab §19.5 → A:**
- Der **Bau** einer monatlichen Kandidatenliste am NB mit Vorwärtsprotokoll ist begründet. Vor dem Bau kommt die Voranalyse des Betriebs.
- ⚠️ Für die NB-Daten (B1–B9) ist zu klären: Die Kombination braucht das **Allzeithoch** und das **erste Kursdatum** je Coin. Am NB liegen Stundenkurse erst ab 2023, also braucht es Stammdaten vom Desktop plus eine laufende Fortschreibung. Außerdem TVL am NB.
- Nicht gemessen und offen: die Wahl **innerhalb** des Fünftels, also wie lang die Liste sein soll.

**Nachtrag §19.4/§19.6:** Der Selbsttest der bewegungsgleichen Spiegelprobe (Lauf 3) wurde auf der **korrigierten** Menge (19.681 Coin-Anker) nachgerechnet (`as_spiegel_nachbarn_korr.txt`). Ergebnis in beiden Epochen:

| Welt | besteht in beiden Epochen |
|---|---|
| reine Bewegung | **0 %** |
| Zufall | **0 %** |
| Richtung s 0,3 / 0,6 | **100 %** |
| Richtung s 0,15 | 72 % |

Je Epoche liegt der Fehlalarm bei 0–5 %. Die Probe gilt damit unverändert.

### 19.7 Wie die Kandidatenliste funktioniert — Faktoren, Wirkung, Liste gegen Watchlist, Rangwechsel, Bezug zum Bestand (06.10.2026)

Nutzer 06.10.: *„Die bisherige Beschreibung der Funktionalität ist mir noch zu wenig erklärt, und welche fachlichen Faktoren nun tatsächlich zum Einsatz kommen und mit welcher Wirkung, fixe Listen vs. Watchlist, Rangänderungen über Zeit? Offenbar hat das Ganze nichts mehr mit dem Bestehenden zu tun?“*

Beleg: `as_erklaerung.py` → `.txt` (Auskunft, keine neue Hypothese).

⚠️⚠️ **Korrektur meiner Beschreibung in §19.6 und in der Meldung vom 06.10.:**
- F1 *unten* heißt **am tiefsten unter dem Allzeithoch** (F1 = Schluss / Allzeithoch − 1, das unterste Fünftel ist der größte Absturz).
- Ich hatte *weniger tief gefallen* geschrieben. Gerechnet war richtig, beschrieben falsch herum.
- Die aktuelle Liste zeigt es: 87–100 % unter dem Hoch.

**1. So entsteht die Liste (jeden Monatsersten, je Klasse H/M/S):**

| Schritt | |
|---|---|
| a | Für jeden Coin der Klasse vier Werte, alle aus Daten **bis gestern** |
| b | Jeder Wert wird in der Klasse zu einem **Rang zwischen 0 und 1**. 1 bedeutet: am stärksten in der günstigen Richtung |
| c | **Gesamtwert** = Mittel der vorhandenen Ränge. TVL gibt es nur für einen Teil der Coins; fehlt er, zählen die übrigen drei |
| d | Das **oberste Fünftel** des Gesamtwerts ist die Kandidatenliste |

**2. Die vier Faktoren und ihre Wirkung** (*Saldo* = Anteil *hat sich binnen 12 Monaten zeitweise verdoppelt* minus Anteil *−70 % oder eingestellt*, gegen die eigene Klasse am selben Stichtag):

| Faktor | günstig ist | allein E2 / E3 | Kombination OHNE ihn, E2 / E3 (mit allen: +11,0 / +13,2 Pp) | Rolle |
|---|---|---|---|---|
| **F8 Alter** | **lange am Markt** | +3,2 / **+17,2** Pp | +9,9 / **+2,3** | **der tragende Faktor im E3.** Er senkt vor allem das Absturz- und Einstellungsrisiko |
| **F1 Absturz** | **sehr tief unter dem Allzeithoch** | +6,0 / **−7,6** Pp | +6,5 / +15,8 | in E2 die Quelle der **Chance** (ohne F1 fällt der Verdopplungsanteil von +5,1 auf +0,2 Pp); in E3 **allein schädlich**, im Verbund neutral bis leicht bremsend |
| **F2 Dauer** | das Hoch liegt **lange zurück** | +3,4 / +5,4 Pp | +10,5 / +13,2 | klein, gleichgerichtet. Er hält die Liste bei *ausgebrannten* Zyklen statt bei frischen Abstürzen |
| **F9 TVL gegen Kurs** | Nutzung wächst **schneller** als der Kurs | +7,6 / +3,6 Pp | +9,9 / +10,5 | klein, nur für etwa 20 % der Coins vorhanden |

⇒ **Fachlich:** Die Liste sucht **alte Überlebende am Boden**, deren Hoch lange zurückliegt und deren Nutzung nicht mitgefallen ist.
- Sie gewinnt vor allem, weil sie **seltener abstürzt oder eingestellt wird**: Absturz −4 bis −8 Pp gegen die Klasse.
- Dazu kommt eine etwas höhere Chance auf eine Verdopplung (+5 bis +8 Pp).
- Das ist die Bodenkauf-Idee des Nutzers, aber über die **Auswahl** gelöst, nicht über den Zeitpunkt.
- ⚠️ Die Faktoren stammen aus einer Auswahl auf E2. Dass F1 in E3 allein schadet, ist ein Warnzeichen für diesen Faktor.

**3. Rangwechsel über die Zeit:**

| Klasse | im Fünftel je Monat | schon im Vormonat drin | nach 12 Monaten noch drin | Verweildauer Median / Mittel | verschiedene Coins 2019–2025 |
|---|---|---|---|---|---|
| H | 3 | 70 % | 40 % | 2 / 3,2 Monate | 19 |
| M | 16 | 75 % | 27 % | 2 / 3,8 Monate | 146 |
| S | 41 | 80 % | 43 % | 3 / 6,0 Monate | 150 |

⇒ Es ist eine **wandernde Liste mit festem Kern**. Drei Viertel bleiben von Monat zu Monat. Viele Coins sind aber nur kurz drin, und nach einem Jahr ist der größere Teil ausgetauscht.

**4. Feste Liste gegen Watchlist:**

| | E2: verdoppelt · −70 %/eingestellt (Klasse) | E3: verdoppelt · −70 %/eingestellt (Klasse) |
|---|---|---|
| **neu** ins Fünftel gekommen | 39,2 % · 40,0 % (36,7 · 41,0) | 24,3 % · 48,3 % (21,2 · 57,2) |
| **schon im Vormonat** drin | **45,8 % · 24,3 %** (39,5 · 30,6) | 27,2 % · 48,4 % (22,1 · 56,7) |

In E2 waren die **Bestätigten** (zwei Monate in Folge im Fünftel) deutlich besser, die Neuzugänge nicht besser als die Klasse. In E3 sind beide ähnlich. ⇒ Ein Hinweis, kein Befund (nicht vorab geplant): Eine **Watchlist mit Bestätigung** wäre eine eigene Messung wert.

| Form | Gemessen? | |
|---|---|---|
| **Feste Monatsliste:** alle im Fünftel kaufen, 12 Monate halten | **ja**, genau das ist §19.6 | jeden Monat eine neue Tranche, viele kleine Positionen |
| **Watchlist mit Bestätigung:** Kauf erst nach ≥ 2 Monaten im Fünftel | nein | Hinweis aus E2, siehe oben |
| **Watchlist mit Zeitpunkt:** Kauf aus der Watchlist erst bei einem Phasen-Fakt (Klima, MACD-Kreuz, Breite) | nein | Zeitpunkt-Regeln haben bisher nie getragen (§15, §17), also nur mit eigener Messung |
| **Kurze Liste:** nur die ersten k je Klasse | nein | Die Listenlänge ist offen |

**5. Bezug zum Bestehenden:**

| Baustein | Verhältnis zur Kandidatenliste |
|---|---|
| **Hebel / REGEL0** (Stunden, Futures, ATR-Schwelle) | **unberührt**. Die Liste darf den Hebel **nie** speisen; ein Asset-Rang beim Hebel ist ausgeschlossen (Regel 3). Die Stränge bleiben getrennt (T-1..T-6) |
| **Spot-Kern** BTC/ETH/SOL 70/20/10 mit R1, BTC-Klima | **unberührt**. Die Liste ist ein **Satellit** für Altcoins neben dem Kern, kein Ersatz. Gegen BTC verliert auch der beste Korb in E3 (−34 % in 12 M) |
| **alte Spot-Kette** (LLM-Rollen, NACHKAUFEN), angehalten seit E-67 | die Liste und die Klima-Ampel sind der **Ersatz** (O27): Fakten und eine gemessene Auswahl statt der LLM-Begründung *im Minus → nachkaufen* |
| **Klima-Ampel / Fakt-Mail** (A4) | beantwortet das **Wann** (Phase, als Fakt: Klima, MACD, Liquidität). Die Liste beantwortet das **Welche** |
| **gemeinsame Grundlage** | dieselben Kursdaten, dieselben Klassen H/M/S (§14), dieselben Kosten, derselbe Messstandard (Nullwelt, Selbsttest, sechs Prüfungen) und dieselben Betriebsregeln am NB |

### 19.8 Reifegrad und Gliederung — Einschätzung VOR einem Bau (06.10.2026)

Nutzer 06.10.: *„Denke, wir müssen das Thema nach Bedarf und fachlicher Einordnung aufteilen, z. B. Watchlist und Assetliste kombinieren oder was auch immer. Bist du der Meinung als Experte, dass das Thema einen Reifegrad besitzt, um fortzusetzen, und konzeptionell sauber ist?“*

**Einschätzung:**

| | Reif? | |
|---|---|---|
| **Die Messung** | **ja** | vorab festgelegt, Selbsttest, Nullwelt, Gegenprobe aus SQL, sechs Prüfungen. Monoton, jedes Jahr positiv, Weglassprobe hält. Zwei eigene Fehler wurden **vor** der Meldung bzw. bei der Erklärung gefunden und behoben (offene Fenster, Richtung von F1) |
| **Das Konzept** | **noch nicht** | In *Kandidatenliste* stecken fünf verschiedene Fragen, die bisher vermischt sind. Drei davon sind nicht gemessen |
| **Kaufsystem mit Geld** | **nein** | Das Ergebnis ist Beschreibung (fünfter Blick); gegen BTC verliert auch der beste Korb in E3. Der einzige saubere Test ist vorwärts |

**Gliederung nach fachlicher Frage:**

| # | Baustein | Frage | Stand | Art |
|---|---|---|---|---|
| **B1** | **Assetliste (Universum)** | Welche Coins kommen überhaupt in Frage? Bitpanda-handelbar, Datenqualität (Token-Umstellungen verfälschen das Allzeithoch), **tote Projekte** ausschließen (z. B. FTT), Klasse H/M/S | Regeln da (§14), Ausschluss und Datenprüfung **fehlen** | Fakten und Regeln |
| **B2** | **Watchlist (Asymmetrie-Rang)** | Welche Coins aus B1 haben das bessere Verhältnis aus Chance und Risiko? Monatlicher Rang mit Begründung je Faktor, Rangverlauf, Bestätigung | **gemessen** (§19.6); Bestätigung und Länge offen | gemessene Ordnung, **Auskunft** |
| **B3** | **Phase** (Klima-Ampel) | Ist gerade eine Lage, in der das rechte Ende häufiger ist? BTC-Klima, MACD, Liquidität, Breite | als Fakten gemessen (§16, §20). Als Signal **nicht** vorab erkennbar (2.599) | Fakt, kein Auslöser |
| **B4** | **Allokation und Einsatz** | Wie viel vom Vermögen in den Satelliten neben dem Kern? Fester kleiner Einsatz je Coin, Tranchen | **nicht gemessen**; die Höhe des Satelliten ist eine **Nutzerentscheidung** (Ziel, Risiko) | Regelwerk |
| **B5** | **Führung und Ausstieg** | Wann wird verkauft? Gemessen ist nur *12 Monate halten*. Beim Bodenkauf half die Führung deutlich (§15.7: +20–40 Pp gegen Halten) | **nicht gemessen** für die Liste | Messung nötig |

**Empfehlung (Reihenfolge):**
1. **B1 + B2 zusammen als Watchlist mit Vorwärtsprotokoll, ohne Geld**, als Abschnitt der Klima-Ampel-Mail (B3).
   - B1 liefert die *Assetliste*, B2 den Rang darin. Das ist die vom Nutzer genannte Kombination *Watchlist und Assetliste*.
   - Vorher muss der Ausschluss toter Projekte und die Datenprüfung stehen.
2. **Parallel messen** (je eigener Plan vorab): B2-Bestätigung (≥ 2 Monate im Fünftel), Listenlänge (die besten k je Klasse), B5-Führung auf der Liste.
3. **B4 erst nach 6 Monaten Vorwärtsprotokoll**, zusammen mit dem Nutzer: Satellitenanteil und Einsatz je Coin.

⇒ **Fortsetzen ja, als Watchlist und Auskunft. Kein Kaufsystem, solange B1, B4 und B5 offen sind und kein Vorwärtsergebnis vorliegt.**

## 21. Erster Wurf Watchlist: Messpläne B1, B2, B5 — VOR der Messung (06.10.2026)

Nutzer 06.10.: *„Ja, ich denke, für den ersten Wurf mit Luft nach oben können wir weiterarbeiten. Nach den Messungen machen wir ein langes Fazit und gemeinsame Abstimmung.“*

**Grundlage für alle drei:**
- Die Liste V0 ist das oberste Fünftel der Kombination aus §19.6: F1 unten, F2 oben, F8 oben, F9 oben. Je Stichtag und Klasse, 12 Monate, Anker wie §19.6.
- Wahl auf **E2**, Bestätigung **einmal auf E3**.
- Die Nullwelt ist immer eine **Zufallsauswahl gleicher Größe aus V0 in derselben Zelle**. Gefragt wird also: *Verbessert die Regel die Liste?*
- 200 Ziehungen. *Trägt* heißt: Wirkung in die erwartete Richtung in E2 **und** E3, Rang ≥ 0,95 in beiden.

### 21.1 B1 Assetliste — Ausschlussregeln

| # | Regel (am Stichtag t, Daten bis t) | Gedanke |
|---|---|---|
| **XA Restwert** | Kurs ≤ 1 % des Allzeithochs | *praktisch null*, z. B. tote Börsen-Tokens |
| **XB Umsatzschwund** | mittlerer Umsatz 90 T < 20 % des Umsatzes 365 T | das Interesse ist weg |
| **XC Mindestumsatz** | 90-T-Umsatz im untersten Zehntel der Klasse am Stichtag | nicht handelbar genug |
| **XD Datenfehler** | in der Kursreihe bis t ein Tagessprung über Faktor 5 (Token-Umstellung, Befund 29.08.) | Allzeithoch und Absturztiefe unzuverlässig |

- **Gemessen:** Saldo (verdoppelt − Absturz/eingestellt) der Liste **nach** dem Ausschluss minus Saldo von V0.
- **Nullwelt:** gleich viele Coins zufällig aus V0 entfernt.
- **Signalbilanz:** wie viele Coins je Klasse und Monat die Regel entfernt (Vorgabe 01.10.: Filter nur mit Qualitätsgewinn).
- **Auskunft:**
  - *Allzeithoch erst ab dem 31. Handelstag* (ohne Listing-Spitzen), Wirkung auf V0;
  - *heute bei Bitpanda handelbar* (nur als Fakt; Rückmessung wäre Vorgriff).

### 21.2 B2 Watchlist — Bestätigung und Länge

| # | Variante | Nullwelt |
|---|---|---|
| **V1** | im Fünftel an t **und** am Vormonat | Zufallsauswahl gleicher Größe aus V0 |
| **V2** | an t, t−1 **und** t−2 | ebenso |
| **K5 / K10** | nur die besten 5 bzw. 10 je Klasse nach Gesamtwert (nur M und S; H hat im Mittel 3) | ebenso |

**Gemessen:** Saldo, Lift R2 und D2, Korb gegen BTC und gegen V0, Zahl der Coins je Monat.

### 21.3 B5 Führung und Ausstieg (Einstieg = Mitglied von V0, Kauf zum Schluss t+1, höchstens 12 Monate, Kosten 1,25 % je Seite)

| # | Ausstieg |
|---|---|
| **X0** | 12 Monate halten (Bezug, so ist §19.6 gemessen) |
| **X1** | gestaffelt: ⅓ bei ×2, ⅓ bei ×3, Rest mit Nachlauf −35 % vom Hoch |
| **X2** | Nachlauf −35 % vom Hoch, Notbremse −50 % vom Einstieg |
| **X7a** | **Rang-Ausstieg:** Verkauf am ersten Monatsersten, an dem der Coin **nicht mehr in der oberen Hälfte** seiner Klasse liegt (Gesamtwert) |
| **X7b** | wie X7a, aber schon, wenn er **aus dem Fünftel** fällt |

- **Gemessen:** Korb-Ertrag nach Kosten je Stichtag, **gepaart** gegen X0 auf denselben Einstiegen.
- **Trägt:** Mittel **und** Median der Differenz je Stichtag > 0 in E2 und E3. Blockbootstrap über die Stichtage (Block 3, 1.000 Ziehungen): Anteil > 0 ≥ 0,95 in beiden.
- **Auskunft:** realisiert ≥ ×2, realisiert ≤ −70 %, Haltedauer, gegen BTC.
- Die Ränge für X7 stammen aus derselben Monatsrechnung, auch für Monate ohne abgeschlossenes Fenster (nur Merkmale, kein Ausgang).

### 21.4 Gegenprüfung des Plans

| | |
|---|---|
| **Vorgriff** | Alle Regeln nutzen Daten bis t. Ausnahme: der Bitpanda-Stand, deshalb nur Auskunft |
| **Mehrfachtesten** | B1 4, B2 4, B5 4 Regeln, jeweils *beide Epochen* gefordert. Ein Fehlalarm in beiden bei Rang ≥ 0,95 liegt je Regel bei etwa 0,25 % |
| **Selbsttest** | Die Anlage aus §19 ist geprüft. Für B5 wird X0 gegen sich selbst gerechnet (Differenz muss 0 sein); eine Zufallsregel *Ausstieg nach zufälliger Monatszahl* darf nicht tragen |
| **Ehrlich** | Sechster Blick auf die Altcoin-Daten: **Beschreibung**. Das Vorwärtsprotokoll bleibt der eigentliche Test |

### 21.5 Nachtrag zum Plan B5, VOR dem ersten Lauf (06.10.2026)

- **Verzerrung im Plan erkannt:** In E3 verliert *12 Monate halten* im Mittel −48 % gegen BTC bzw. −45 bis −65 % absolut (§19.1).
  - Jede Regel, die früher verkauft, schlägt X0 dann schon, weil sie **kürzer** im fallenden Markt ist.
  - Das ist keine Führungsleistung.
- **Zusätzliche Bedingung für *trägt* (strenger, nicht lockerer):** Die Regel muss auch eine **Zufallswelt mit derselben Haltedauer** schlagen.
  - Die Haltedauern der Regel werden innerhalb der Epoche zufällig auf die Einstiege verteilt, 200 Ziehungen.
  - Rang ≥ 0,95 in E2 und E3.
- **Selbsttest B5:** X0 gegen X0 ergibt 0. Eine Zufallsregel *Verkauf nach zufälliger Monatszahl 1–12* darf unter der vollen Bedingung **nicht** tragen.
- Bei X7 zählt ein Monat **ohne** Rangwert (Merkmal fehlt) als *halten*.

### 21.6 Ergebnis erster Wurf Watchlist (06.10.2026, nach §21 mit §21.5)

**Belege:**
- `wl_messung.py` → `.txt`
- Gegenprobe `wl_gegenprobe.py` → `.txt`: 28 von 28 gleich
  - B5-Ausstiege und B1-Flags direkt aus SQL;
  - ⚠️ G3 (Bestätigung) liest dieselbe Monatstabelle und prüft damit nur die Nachschlagelogik.

**Selbsttest B5:** X0 gegen X0 ergibt 0. Der Zufallsausstieg trägt nicht: gleiche Dauer Rang 0,04 / 0,03.

**B1 Ausschlussregeln — keine trägt, keine schadet nennenswert:**

| Regel | entfernt E2 / E3 | Wirkung E2 / E3 (Rang) |
|---|---|---|
| XA Restwert (≤ 1 % des Allzeithochs) | 2 % / 5 % | −0,0 (0,43) / −0,6 Pp (0,08) |
| XB Umsatzschwund | 3 % / 1 % | −0,1 / +0,1 Pp |
| XC Mindestumsatz (unterstes Zehntel) | 11 % / 13 % | −0,8 (0,04) / −0,3 Pp |
| XD Datenfehler (Sprung > ×5) | 0 % / 1 % | −0,0 / +0,6 Pp (1,00) |

**Auskunft:**
- Allzeithoch erst ab dem 31. Tag: Saldo E3 +15,2 statt +13,2 Pp, 89–92 % der Liste gleich.
- **Bitpanda:** 64 der 67 Coins der aktuellen Liste sind gelistet.

⇒ *Tote Projekte* lassen sich mit diesen Fakten **nicht** vom Rest unterscheiden. FTT verhielt sich im Mittel wie die übrigen Listenmitglieder.

**B2 Bestätigung und Länge — keine trägt, kurze Listen deuten in die gute Richtung:**

| Variante | E2 Wirkung (Rang) | E3 Wirkung (Rang) | je Monat | E3 Absturz/eingestellt (V0 48,4 %) |
|---|---|---|---|---|
| V1 bestätigt (Vormonat) | +2,1 Pp (0,99) | +0,6 Pp (0,84) | 47 / 65 | 48,1 % |
| V2 bestätigt (2 Vormonate) | +2,4 Pp (0,93) | +0,6 Pp (0,73) | 41 / 58 | 47,5 % |
| **K10** (beste 10 je Klasse M, S) | **+5,1 Pp (1,00)** | **+4,2 Pp (0,90)** | 23 / 23 | **41,4 %** |
| K5 (beste 5 je Klasse) | +2,0 Pp (0,79) | +6,1 Pp (0,91) | 13 / 13 | 37,1 % |

**B5 Führung und Ausstieg** (Korb je Stichtag nach Kosten; BTC an denselben Tagen):

| Regel | E2 Korb (BTC) · gg. X0 Mittel / Median · Bootstrap · gleiche Dauer | E3 Korb (BTC) · gg. X0 · Bootstrap · gleiche Dauer | Urteil |
|---|---|---|---|
| X0 12 Monate halten | +29,7 % (+36,0 %) | **−42,0 %** (+21,9 %) | Bezug |
| X1 gestaffelt | +23,4 % · −6,3 / +23,3 Pp · 0,73 · 0,78 | **+0,1 %** · +42,1 / +42,3 Pp · 1,00 · 1,00 | E2 nein |
| **X2 Nachlauf −35 % / Notbremse −50 %** | **+31,8 %** (+14,8 %) · +2,1 / +20,7 Pp · **0,81** · **0,99** | **−4,0 %** (+13,6 %) · +38,0 / +41,3 Pp · 1,00 · 1,00 | **knapp nein** (nur Bootstrap E2 0,81) |
| X7a Rang-Ausstieg (obere Hälfte) | +43,7 % · +14,0 / +4,9 Pp · 0,99 · 1,00 | −39,5 % · +2,5 Pp · 1,00 · **0,00** | E3 nein |
| X7b Rang-Ausstieg (Fünftel) | +28,1 % · −1,6 / +17,9 Pp · 0,82 · 0,55 | −25,7 % · +16,3 Pp · 1,00 · 0,80 | nein |
| *Zufall (Selbsttest)* | gleiche Dauer 0,04 | 0,03 | richtig *nein* |

⇒ **Die Führung ist der größte Hebel im ganzen Strang.**
- Mit Nachlauf (X2) wird aus dem E3-Korb **−4 % statt −42 %**: kein Absturz ≤ −70 % mehr, statt 34 %.
- In E2 liegt X2 gleichauf bis besser als Halten (Median +21 Pp, Mittel +2 Pp).
- Der Mittelwert in E2 ist schwach, weil der Nachlauf in der Altseason 2021 die großen Läufe früh beendet.
- **Nach der vorab festen Regel trägt X2 knapp nicht** (Bootstrap E2 0,81 < 0,95).
- Gegen BTC liegt auch der geführte Korb in E3 darunter (−4 % gegen +14 %).

## 22. FAZIT Spot-Altcoins nach allen Messungen des 06.10.2026 — zur gemeinsamen Abstimmung

### 22.1 Was wir heute gelernt haben (alles mit Gegenprobe)

| # | Frage | Antwort | Beleg |
|---|---|---|---|
| 1 | Schlägt eine **Zeitpunkt-Regel** (Boden, Momentum, Zyklus) BTC im Mittel? | **nein**, in keiner Form, seit 2024 schon gar nicht | §15–§17 |
| 2 | Hilft **Makro** (Liquidität, Stablecoins, MACD)? | 2021–23 ja, **seit 2024 nicht**. Stablecoins umgekehrt zur Faustregel, der MACD hatte 07/2025 ein Fehlsignal | §16, §20 |
| 3 | Gibt es Altcoins mit **asymmetrischem** Chance-Risiko-Verhältnis? | **ja**: alte Überlebende am Boden. Saldo E3 +13 Pp gegen die Klasse, monoton, jedes Jahr positiv | §19.6 |
| 4 | Woher kommt der Vorteil? | vor allem **weniger Absturz und Einstellung**, dazu eine etwas höhere Chance auf eine Verdopplung. Das **Alter** trägt am meisten | §19.7 |
| 5 | Lassen sich **tote Projekte** ausfiltern? | mit Kurs- und Umsatzfakten **nicht** | §21.6 B1 |
| 6 | Hilft **Bestätigung** oder eine **kurze** Liste? | Bestätigung nicht; eine kurze Liste deutet in die gute Richtung (K10: E3 +4,2 Pp, Rang 0,90) | §21.6 B2 |
| 7 | Hilft **Führung**? | **stark**: Nachlauf −35 % macht E3 aus −42 % zu −4 %. Nach der strengen Regel knapp nicht bestätigt (E2) | §21.6 B5 |
| 8 | Schlägt das **BTC**? | **nein, nicht seit 2024**: weder gehalten noch geführt. Es beantwortet *welche Altcoins und wie führen*, nicht *Altcoins statt BTC* | §19.6, §21.6 |

### 22.2 Was daraus folgt — das System im ersten Wurf

| Baustein | Vorschlag | Status |
|---|---|---|
| **B1 Assetliste** | Klassen H/M/S wie §14. Als **Betriebsfakten**: bei Bitpanda handelbar, Datenfehler-Ausschluss, Allzeithoch erst ab dem 31. Tag (Hygiene, gemessen neutral) | Fakten |
| **B2 Watchlist** | Kombination aus Alter, Absturz, Dauer und TVL; monatlicher Rang je Klasse mit Begründung je Faktor. **Kurze Form:** alle H + die besten 10 je M und S (rund 23 Coins) | gemessen (§19.6); die Länge ist Hinweis |
| **B3 Phase** | BTC-Klima, MACD-Stand, Netto-Liquidität, Stablecoins, Breite **als Fakt** in derselben Mail | Fakt |
| **B5 Führung** | für jede Watchlist-Position die **Nachlauf-Marke** (−35 % vom Hoch seit Kauf, Notbremse −50 %) als **Hinweis** | Hinweis, knapp nicht bestätigt |
| **B4 Allokation** | **offen, Nutzerentscheidung** nach dem Vorwärtsprotokoll: Anteil des Satelliten neben dem Kern, fester kleiner Einsatz je Coin | offen |
| **Vorwärtsprotokoll** | ab dem nächsten Monatsersten: Liste, Rang und Begründung protokolliert, **ohne Geld**. Abgerechnet nach 6 und 12 Monaten gegen die Klasse und gegen BTC, gehalten **und** geführt (X0, X2). Abrechnungsregel vorab wie §19.2 / §21 | einziger sauberer Test |

### 22.3 Zur Abstimmung

| # | Punkt | Empfehlung |
|---|---|---|
| **W1** | Watchlist als **Auskunft** in der Klima-Ampel-Mail, mit Vorwärtsprotokoll, **ohne Geld** | ja |
| **W2** | Listenform | **kurz** (H alle + M/S je 10): praktisch handhabbar, Messung zeigt in die gute Richtung |
| **W3** | Filter | keine Leistungsfilter (keiner trägt); nur die Betriebsfakten aus B1 |
| **W4** | Führung | **Nachlauf-Marke X2** als Hinweis je Position; das Protokoll führt X0 und X2 nebeneinander |
| **W5** | Allokation (B4) | nach 6 Monaten Protokoll gemeinsam entscheiden |
| **W6** | Bau | Voranalyse Betrieb am NB: Stammdaten Allzeithoch und Erstdatum vom Desktop, laufend fortgeschrieben; TVL am NB; monatlicher Job; Mailabschnitt; Betriebsprüfung B1–B9 |
| **W7** | Weitere Messungen | mit Luft nach oben: X2-Varianten (Nachlauf −25 / −45 %), Listenlänge feiner, ein Freigabekalender für die Verwässerung, falls eine Quelle gefunden wird |

⚠️ **Was nicht folgt:**
- Kein Kaufsignal.
- Kein Hebel aus dieser Liste (Regel 3).
- Keine Änderung am Kern 70/20/10.
- Keine Aussage, dass Altcoins BTC schlagen.

### 22.4 Was das System leistet — am Beispiel aus echten Daten (06.10.2026; E-73)

Nutzer 06.10.: *„Ich kann mir noch immer nicht vorstellen, was das System leistet oder leisten soll.“*

Beleg: `beispiel_watchlist_mail.py` → `.txt`, Stichtag 01.09.2026, Datenstand 20.09.2026. Nur Anschauung, kein Signal.

**In einem Satz:** Einmal im Monat sagt das System, **welche Altcoins** gerade das bessere Verhältnis aus Chance und Risiko haben und **warum**. Für jeden Coin nennt es, **ab wo** man ihn wieder verkaufen würde. Es führt Buch, ob das stimmt. **Kaufen** tut es nicht, und es rät auch nicht dazu.

**Ablauf je Monat:**

| Wer | Was |
|---|---|
| **System, am Monatsersten** | 1. Phase als Fakten (BTC-Klima, Breite, Liquidität, MACD). 2. Rang aller Altcoins je Klasse aus den vier Faktoren. 3. Kurze Liste: alle Highcaps im obersten Fünftel und die besten 10 je Mid- und Smallcap. 4. Je Coin die Begründung (vier Teilränge), seit wann in der Liste, neu oder herausgefallen. 5. Je Coin die Nachlauf-Marke. 6. Das Protokoll: wie sich die Liste seit dem letzten Mal gegen ihre Klasse und gegen BTC entwickelt hat |
| **Nutzer** | liest, entscheidet selbst, ob und was er kauft (B4 ist offen). Bei gehaltenen Coins sieht er die Marke, unter der der Nachlauf verkaufen würde |
| **System, laufend** | schreibt die Marke täglich fort und meldet als Fakt, wenn ein Kurs sie unterschreitet |
| **nach 6 und 12 Monaten** | Abrechnung des Protokolls: Liste gegen Klasse und gegen BTC, gehalten und geführt. Erst dann wird über Geld (B4) entschieden |

**Auszug aus dem Beispiel:**
- **Phase:** BTC-Klima 0,33 (Grenze billig/mittel) · Breite 51 % · Netto-Liquidität 5,78 Bio. USD, 13 Wochen fallend (−1,0 %) · MACD unter Null, Kreuz nahe.
- **Highcaps:** LTC (0,81: Alter 8,7 J, 87 % unter dem Hoch, Hoch vor 64 Monaten, seit 6 Monaten in der Liste) · ADA (0,78) · DOGE (0,72, neu) · FET (0,67, neu).
- **Midcaps:** FIL · CHZ · STRAX · CELO · COTI · ICP · ATOM · ALGO · ALICE · ONG.
- **Smallcaps:** ONT · NEO · SNX · AUDIO · SKL · ZIL · BAND · HOT · WIN · ONE.
- **Herausgefallen:** DASH, ETC, FIDA, GALA, ICX, SLP, THETA, UNI, ZEN.
- **Nachlauf-Marke**, Beispiel LTC: Kauf am 02.09. bei 49,69, heute +15 %, Marke 37,88 (−34 % von heute), Notbremse 24,84.
- **Protokoll nach 18 Tagen** (vor Kosten; nur Anschauung, keine Aussage):

  | | Liste | ganze Klasse | BTC |
  |---|---|---|---|
  | H | +10 % | +21 % | +4 % |
  | M | +15 % | +13 % | +4 % |
  | S | **+63 %** | +19 % | +4 % |

⚠️⚠️ **Was das Beispiel an Lücken zeigt (vor einem Bau zu beheben):**
1. **ONE (+464 % in 18 Tagen)** ist in `symbol_zuordnung.csv` **gesperrt** (Kollision mit dem gleichnamigen Bitpanda-Asset, +23,76 %). **AUDIO** (wie MBL und ONE) ist bei den Markpreisen als *fremdes Instrument* gesperrt (2.705, `markpreis_alle.db`), steht aber nicht in der csv. Der Smallcap-Wert +63 % hängt an ONE. ⇒ B1 braucht als **Pflicht** beide Sperrlisten (gesperrt = nicht in die Liste) und eine Plausibilitätsprüfung extremer Kurssprünge.
2. *NEU* bezog sich auf die **kurze** Liste, nicht auf das Fünftel. Deshalb steht bei ZIL und WIN zugleich *neu* und *seit 6 Monaten*. ⇒ getrennt beschriften: *neu im Fünftel* und *neu unter den besten 10*.
3. Viele Werte zeigen *100 % unter dem Hoch* (gerundet ≥ 99,5 %). Bei Allzeithochs aus den ersten Handelstagen ist das Allzeithoch ab dem 31. Tag sauberer (§21.6 Auskunft).
4. TVL gibt es nur für wenige Coins der kurzen Liste.

**Was es leistet, und was nicht:**

| leistet | leistet nicht |
|---|---|
| Aus über 300 Altcoins monatlich rund 23 mit nachweislich besserem Chance-Risiko-Verhältnis als ihre Klasse, **begründet** | sagt nicht, **ob** man Altcoins kaufen soll statt BTC; seit 2024 hat BTC jede Altcoin-Auswahl geschlagen |
| eine Verkaufsmarke je Coin, die in der Rückmessung die großen Abstürze verhindert hätte | keine Garantie; der Nachlauf ist knapp nicht bestätigt |
| ein ehrliches Vorwärtsprotokoll, an dem nach 6 und 12 Monaten entschieden wird | keinen Kaufzeitpunkt (Phase nur als Fakt) |

## 23. Nutzer-Rückmeldung zum Beispiel: Bestand, Smallcaps, Lesbarkeit, inhaltliche Bewertung (06.10.2026)

Nutzer 06.10.:
1. *„Kennzeichen im Bitpanda-Bestand wird benötigt.“*
2. *„Bin unsicher, ob das System bei Smallcaps überhaupt Sinn macht.“*
3. *„Ranking und eine reine Faktenliste je Asset ohne Bewertungsschema ist viel Lesen mit zu vielen Zahlenwerten.“*
4. *„Prüfe, ob man je Asset auch eine inhaltliche Bewertung zusammenbringen kann. Das Problem bei Krypto ist, die wenigsten Assets haben einen echten Nutzen, z. B. ETH, und somit auch höheres Potential bzw. ein geringeres Risiko, dass das Asset stirbt. Kann man diesen Aspekt sinnvoll integrieren, ohne dass man auf wertlose News angewiesen ist?“*

### 23.1 Bestand

- Die Tabelle `holdings` gibt es. Am Desktop ist sie eine **alte Kopie** (19.07.2026, 28 Symbole); der aktuelle Stand liegt am NB.
- ⇒ Im Bau liest der Mailabschnitt den Bestand am NB, **nur lesend** (`mode=ro`).
- Er zeigt:
  - je Listen-Coin das Kennzeichen *im Bestand*;
  - einen eigenen Block *deine gehaltenen Altcoins*: Einstufung und Rang in der Klasse, auch wenn sie nicht in der Liste stehen (z. B. LINK, XLM, QNT, KAS), samt Nachlauf-Marke.

### 23.2 Smallcaps — gemessen schon beantwortet (§19.6, `as_pruefungen_komb.txt`)

| Klasse | Saldo E3 gegen die Klasse | Lift verdoppelt / Absturz | Korb E3 (Klasse) |
|---|---|---|---|
| H | **+27,9 Pp** | 1,53 / **0,74** | −0 % (−28 %) |
| M | **+27,5 Pp** | 1,36 / **0,85** | −44 % (−58 %) |
| **S** | +7,9 Pp | 1,15 / **0,98** | **−57 % (−56 %)** |

⇒ Bei **Smallcaps** senkt die Auswahl das Absturzrisiko **nicht** (0,98), und der Korb ist nicht besser als die Klasse. Dazu sitzen dort die Datenfehler (ONE, AUDIO). **Vorschlag: Smallcaps raus**, die Watchlist nur für H und M.

### 23.3 Lesbarkeit — Bewertungsschema statt Zahlenliste

Je Coin **eine Zeile**: Stufe · Begründung in Worten · Status. Die Zahlen kommen in einen Anhang.

```
★★★ FIL      Midcap · alt, sehr tief gefallen, Hoch lange her            · Marke ok (−35 %)
★★  LTC      Highcap · sehr alt, Hoch lange her · Nutzung gering         · im Bestand · Marke ok
★★  ATOM     Midcap · sehr alt · Nutzung 4,5 Mio. USD Gebühren/Jahr      · NEU · Marke ok
```

- **Stufe:**
  - ★★★ Wert im obersten Zehntel der Klasse;
  - ★★ übriges oberstes Fünftel;
  - ★ Bestand außerhalb der Liste (nur bei gehaltenen Coins).
- **Begründung:** die zwei bis drei Faktoren mit dem höchsten Teilrang, in Worten.
- **Status:** im Bestand · neu · Marke ok / nahe (< 10 %) / unterschritten.

### 23.4 Inhaltliche Bewertung ohne News — Vorprüfung (`nutzen_vorpruefung.py` → `.txt`, Daten nach `data/_spot/gebuehren.db`)

**Gedanke:** Echten Nutzen kann man messen, ohne Nachrichten zu lesen. **Gebühren** sind das, was Nutzer für die Nutzung **bezahlen**.

| Quelle (frei) | was sie sagt | Historie |
|---|---|---|
| **DefiLlama Gebühren** | tatsächliche Nachfrage nach der Blockchain oder dem Protokoll (BNB 788, LDO 616, POL 365, ARB 322 Mio. USD im Jahr; LTC 0,5, DOGE 0,1) | ETH ab 2015; die meisten Coins erst ab 2023/24 |
| DefiLlama Einnahmen für Tokenhalter | ob der **Token** etwas davon hat | wie oben (noch nicht geladen) |
| TVL, aktive Adressen | Nutzung (schon gemessen: F9, F10) | Teilmengen |
| Kategorie (CoinGecko: Meme, Gaming, L1, DeFi …) | ob es überhaupt einen Nutzen **gibt** | nur der heutige Stand |

**Abdeckung:**
- Zum 01.09.2026 haben **H 18 von 20, M 55 von 80**, S 102 von 232 eine Gebührenreihe.
- Je Stichtag mit 180 T Vorlauf:
  - 2022: H 2/12 · M 6/88;
  - 2024: H 6/12 · M 16/88;
  - 2026: H 12/18 · M 33/82.
- ⚠️ **Mehrdeutig** (ein Kürzel, mehrere Protokolle), also noch nicht zugeordnet: unter anderem **AAVE, UNI, LINK, COMP, CRV, SNX, JUP**. Lösbar über die CoinGecko-ID, die für 407 Symbole schon vorliegt (`umlaufmenge_cg.abruf_symbol`).

**Folge für die Messung:**
- Mit Wahl auf E2 und Bestätigung auf E3 ist ein Gebührenfaktor **nicht** prüfbar; die Historie beginnt dafür zu spät.
- Möglich sind:
  - (a) Nutzung als **Fakt** in der Begründungszeile, ohne Gewicht;
  - (b) eine **Beschreibung** auf E3, ob Coins mit hohen und wachsenden Gebühren seltener abstürzen;
  - (c) der Vorwärtstest.
- Die Kategorie *Meme ohne Nutzen* kann als Fakt mitlaufen. Ob sie das Absturzrisiko trennt, ist mit dem heutigen Stand auf E2/E3 als Auskunft messbar; dabei ist der Vorgriff zu prüfen.

### 23.5 Nutzer-Entscheide und was *Nutzen* genau heißt (06.10.2026)

Nutzer 06.10.:
1. *„Der Bestand und Neuzugänge (alle) – die Rangliste dann ohne Small- und Ultrasmallcaps“*
2. *„Ja, Schema ist nicht schlecht, bei den Zahlen im Anhang ja Kriterium mit Skala, was warum gut oder schlecht“*
3. *„Kategorien passt auch – aber der Nutzen, den du mir schilderst, ist noch unklar: Was meinst du hier genau je Asset, die Information von Total Value Locked oder etwas anderes?“*

**Festgehalten (vorläufig, E-73):**
- **Rangliste nur H und M.**
- Der Block **Bestand** zeigt **alle** gehaltenen Coins und alle **Neuzugänge**, auch Smallcaps. ⚠️ Auslegung zu bestätigen: *Neuzugänge* = neu in den Bestand gekommene Coins.
- **Schema** mit Sternen und Worten.
- Im **Anhang** je Kriterium eine **Skala**: welcher Bereich günstig oder ungünstig ist und **warum** (aus der gemessenen Dosis-Wirkung).
- **Kategorie** als Fakt.

**Was *Nutzen* je Asset heißen kann — drei Größen, nicht dasselbe** (Beleg: Abfrage 06.10., DefiLlama; Marktwert = Umlaufmenge × Kurs 20.09.):

| Größe | was sie misst | Vergleich | Falle |
|---|---|---|---|
| **TVL** (Total Value Locked) | wie viel Geld in einem Protokoll oder auf einer Blockchain **geparkt** ist | Kundeneinlagen einer Bank | sagt nicht, ob jemand **bezahlt**; durch Belohnungsprogramme aufblasbar, oft doppelt gezählt. Beispiel: Bei BNB stehen 174 Mrd. USD; das sind die Bestände der Börse Binance, keine Nutzung der Blockchain |
| **Gebühren** | was Nutzer **tatsächlich bezahlen**, um die Blockchain oder App zu nutzen | **Umsatz** eines Unternehmens | enthält zum Teil durchgereichte Erträge. Beispiel: LDO 616 Mio. USD sind überwiegend Staking-Erträge, die an die Einleger gehen |
| **Halter-Einnahmen** | der Teil der Gebühren, der **beim Token ankommt** (Rückkauf, Verbrennen, Ausschüttung an Staker) | **Gewinn bzw. Dividende** | die meisten Tokens erhalten nichts davon. Dann ist der Token ein Stimmrecht, kein Anteil |

| Coin | Gebühren 365 T | Trend (180 T gegen 180 T davor) | Halter-Einnahmen 365 T | Marktwert | Marktwert / Gebühren |
|---|---|---|---|---|---|
| ETH | 4.631 Mio. USD | −28 % | 325 Mio. | 315 Mrd. | 68× |
| BNB | 788 Mio. | −17 % | 71 Mio. | 100 Mrd. | 127× |
| AVAX | 125 Mio. | −27 % | 23 Mio. | 4,2 Mrd. | 34× |
| TRX | 83 Mio. | +36 % | 0,7 Mio. | 32 Mrd. | 390× |
| ADA | 8,3 Mio. | −29 % | 0,7 Mio. | 8,3 Mrd. | 996× |
| ATOM | 4,5 Mio. | −71 % | ~0 | 0,9 Mrd. | 204× |
| LTC | 0,5 Mio. | −21 % | ~0 | 4,4 Mrd. | 8.603× |
| DOGE | 0,1 Mio. | −40 % | ~0 | 13,3 Mrd. | 92.570× |

**Vorgeschlagenes Nutzen-Kriterium** (Fakt in der Zeile, Zahlen im Anhang, ohne Gewicht bis zur Messung §23.4 b):
- **Nutzung vorhanden:** Gebühren der letzten 365 T über einer Mindesthöhe.
- **Trend:** Gebühren steigend oder fallend.
- **Wert beim Token:** Halter-Einnahmen ja/nein und Marktwert je Dollar Halter-Einnahmen. Das entspricht einem Kurs-Gewinn-Verhältnis.
- **Kategorie:** Meme, Gaming, Blockchain, DeFi …

Beispielzeile:
```
★★ ADA  Highcap · sehr alt, Hoch lange her · Nutzung gering (8 Mio. $/Jahr, fallend), Token erhält wenig
```

### 23.6 Der Prüfstein Quant — wo das System heute zu kurz greift (06.10.2026)

Nutzer 06.10.: *„Neu in den Bestand gekaufte Coins, aber ja, diese könnten natürlich auch Neuemissionen sein. Zum Schema: ja gut, aber etwas zu kurz, z. B. was ist ‚Token erhält wenig'? … Der Punkt ist eher: Wenn die Adaption der Wallstreet und Tokenisierung Fahrt aufnimmt, werden nur bestimmte Assets dauerhaft Bestand haben. Siehe Quant – der Coin galt als tot, hat aber begrenzte Tokenanzahl, alles ausgegeben. Ich fürchte, hier sind wir nicht weit genug bzw. ist der Weg noch nicht klar.“*

**Festgehalten:**
- *Neuzugänge* sind neu gekaufte Coins. Sind sie zu jung für einen Rang, erscheinen sie mit Fakten und dem Vermerk *zu jung für eine Einstufung*.
- Das Schema bekommt **ganze Sätze** statt Kürzeln (Beispiel unten).

**QNT, nachgesehen** (Beleg: Abfrage 06.10., messdaten, CoinGecko):

| | |
|---|---|
| Kurs | Allzeithoch 394,9 (09/2021), heute 64,2 (**−84 %**). Die Klasse liegt im Median bei −97 % bis −99 % |
| Angebot | **14,54 von 14,61 Mio. ausgegeben (99,5 %), Höchstmenge fest** ⇒ praktisch keine künftige Verwässerung |
| Kategorien | Infrastructure, **Real World Assets (RWA)**, Coinbase 50 Index |
| im System | Klasse **S** (Binance-Umsatzrang über 100) ⇒ nach dem Entscheid *ohne Smallcaps* **gar nicht in der Rangliste**. In der Klasse nur Perzentil 0,43, weil QNT **weniger tief** gefallen ist als die anderen |

⇒ Das System hätte QNT **nicht** hervorgehoben. Der Grund liegt in **drei Lücken**:
1. **Klasse nach Binance-Umsatz statt nach Marktwert.** Für einen Spot-Anleger bei Bitpanda zählt die Größe des Projekts, nicht der Umsatz an einer Börse. QNT ist nach Marktwert deutlich größer als nach Binance-Umsatz.
2. **Alter ab dem Binance-Listing** (QNT 07/2021), nicht ab dem Projektstart (2018). Das echte Alter fehlt als Stammdatum.
3. **Angebot und Tokenisierung fehlen ganz:** feste, voll ausgegebene Menge, RWA- und Institutionsbezug. Genau das ist die These des Nutzers zum Fortbestand.

**Einordnung:**
- *Welche Assets haben dauerhaft Bestand, wenn Wall Street und Tokenisierung Fahrt aufnehmen?* Das ist eine These über einen **Strukturwandel, der erst kommt**. Mit den Kursen der Vergangenheit lässt sie sich nicht beweisen (Regime nicht vorab erkennbar, 2.599).
- Das ist aber kein Grund, sie wegzulassen. Nach der Vorgabe vom 01.10. werden übergeordnete Kräfte **gewichtet**, und **der Nutzer** gewichtet sie.
- ⇒ Es braucht eine **zweite Ebene** neben der gemessenen.

**Vorschlag: zwei Ebenen**

| Ebene | Frage | Inhalt | Art |
|---|---|---|---|
| **1 · Fortbestand (Strukturprofil)** | Hat das Asset das Zeug, dauerhaft zu bestehen? | **Angebot:** Höchstmenge fest, % ausgegeben, künftige Verwässerung · **Nutzung:** Gebühren, Halter-Einnahmen, Trend · **Institution/Tokenisierung:** RWA-Kategorie, RWA-Volumen auf der eigenen Blockchain, ETF/ETP vorhanden, Index-Aufnahme · **echtes Alter** (Projektstart) · **Größe nach Marktwert** · Kategorie | **Fakten-Profil, vom Nutzer gewichtet.** Teilweise messbar als Auskunft (z. B. ob eine feste, voll ausgegebene Menge seltener abstürzt) |
| **2 · Gelegenheit (Watchlist)** | Steht dieses Asset **gerade** günstig? | der gemessene Asymmetrie-Rang (§19.6) und die Nachlauf-Marke | gemessen |

Zusammen: zuerst Ebene 1, dann Ebene 2. *Ein Asset mit gutem Strukturprofil, das gerade asymmetrisch steht.*

**Beispiel einer Zeile mit ganzen Sätzen** (QNT, mit den Fakten von oben):

> **QNT** (nach Marktwert Midcap) · *Fortbestand:* Die Gesamtmenge ist fest und zu 99,5 % ausgegeben; es kommen kaum neue Tokens auf den Markt. Kategorie Tokenisierung realer Werte (RWA). Gebühren sind bei DefiLlama nicht erfasst; der Nutzen liegt außerhalb öffentlicher Blockchains und ist damit nicht messbar. · *Gelegenheit:* 84 % unter dem Hoch von 2021. Es ist weniger tief gefallen als vergleichbare Coins, was im gemessenen Rang eher gegen eine Aufnahme spricht. · *Marke:* …

⇒ **Der Weg ist noch nicht klar. Der Nutzer hat recht:**
- Ebene 2 ist gemessen; Ebene 1 fehlt.
- Nächster Schritt: eine **Voranalyse Strukturprofil**. Welche Fakten gibt es frei und mit welcher Historie (CoinGecko: Angebot, Kategorien, Projektstart; DefiLlama: Gebühren, RWA; ETF/ETP-Liste)? Welche lassen sich als Auskunft messen? Und die Klasseneinteilung nach Marktwert statt nach Binance-Umsatz neu rechnen.

### 23.7 Fallbeispiel QNT — Kauf am Boden, massiver Anstieg (06.10.2026; E-74)

Beleg: Abfrage 06.10. auf `messdaten.db` und `beispiel_watchlist_mail.monat()`.

| | |
|---|---|
| Hoch | 394,9 $ am 10.09.2021 |
| **Boden** | **44,4 $ am 16.06.2022** (−89 %) |
| **Anstieg** | **209,9 $ am 17.10.2022 = ×4,73 in vier Monaten**; BTC im selben Zeitraum ×0,96 |
| danach | 2023 um 100–150 $, heute 64 $ |

**Was die gemessene Watchlist (Ebene 2) am Boden gezeigt hätte:**

| Stichtag | Klasse | Perzentil in der Klasse | Teilränge Alter / Absturz / Dauer | 12-M-Hoch danach |
|---|---|---|---|---|
| 01.06.2022 | S | **0,22** | 0,30 / 0,20 / 0,33 | ×3,13 |
| 01.07.2022 | S | **0,21** | 0,32 / 0,21 / 0,36 | **×4,00** |

⇒ QNT stand am Boden im **untersten** Fünftel und wäre **aussortiert** worden. Zwei Gründe:
- auf Binance erst seit 07/2021, also *jung*;
- **weniger tief** gefallen als die anderen Coins.

Die gemessenen Faktoren beschreiben den **Durchschnitt** (alte Überlebende am Boden stürzen seltener ab). QNT ist ein **Qualitätsfall**, den sie nicht sehen.

**Was das Strukturprofil (Ebene 1) für QNT zeigen müsste:**
- feste Gesamtmenge, praktisch voll ausgegeben;
- Kategorie Tokenisierung (RWA) und Infrastruktur;
- Projektstart 2018 statt Binance 2021;
- Marktwert-Klasse statt Umsatz-Klasse;
- **Widerstandskraft:** fiel weniger als die Klasse.

⚠️ **Ehrlich:**
- Ein Einzelfall begründet keine Regel (*Kleine Läufe täuschen*); QNT ist ein **Prüfstein**, kein Beweis.
- Im Mittel waren *weniger tief gefallene* Coins **schlechter** (F1 oben: E2 −7,8, E3 −2,2 Pp).
- Ob das Strukturprofil den Unterschied macht, muss eine Messung zeigen. Dabei darf QNT nicht die Messung bestimmen.

**Nachlauf am Beispiel:**
- Kauf Juni/Juli 2022 bei rund 52–67 $; Marke −35 % vom Hoch 209,9 ⇒ Verkauf bei rund 136 $ im November 2022, also **×2 bis ×2,6**.
- 12 Monate halten hätte ×1,7 bis ×2,1 gebracht.

## 24. Voranalyse Strukturprofil (Ebene 1) — Datenlage (06.10.2026; E-74)

Beleg: `sp_vorpruefung.py` → `.txt`, Daten nach `data/_spot/strukturprofil.db`. Ergebnis folgt in §24.1.

### 24.1 Ergebnis Datenlage Strukturprofil (06.10.2026)

**Abdeckung (Universum zum 01.09.2026: 332 Altcoins):**

| Fakt | Quelle | Abdeckung | Historie |
|---|---|---|---|
| Marktwert | CoinGecko | 312 | frei nur 365 T. Länger: CoinMetrics (93 Altcoins), sonst eigene Rechnung Umlauf × Kurs |
| Höchstmenge, Anteil ausgegeben, FDV / Marktwert | CoinGecko | 223 mit fester Höchstmenge | nur **heute**; Umlaufmenge ab 09/2025 (`umlaufmenge_cg`), CoinMetrics 66 Coins ab 2013 |
| Kategorien (Meme 29, RWA 18, L1 68, DeFi 86 …) | CoinGecko | 332 | nur heute |
| Projektstart | CoinGecko | **nur 40** | — ⇒ das *echte Alter* bleibt eine Lücke |
| Gebühren, Halter-Einnahmen | DefiLlama | 121 (§23.4) | meist erst ab 2023/24 |
| RWA-Volumen je Blockchain | DefiLlama | Ethereum 2,52 · Solana 0,60 · Arbitrum 0,37 · Avalanche 0,18 · Algorand 0,13 Mrd. USD … | heute (Verlauf je Protokoll abrufbar) |

**Klasse nach Binance-Umsatz gegen Klasse nach Marktwert:**

| Umsatz \ Marktwert | H | M | S | ohne |
|---|---|---|---|---|
| **H** | 19 | 1 | 0 | 0 |
| **M** | 10 | 26 | **42** | 2 |
| **S** | 1 | **43** | 170 | 18 |

⇒ **Fast die Hälfte der Midcaps und Smallcaps steht nach Marktwert in einer anderen Klasse.**
- **QNT: Umsatz-Klasse S, nach Marktwert Rang 16 ⇒ Highcap** (3,81 Mrd. USD; feste Menge, 100 % ausgegeben, FDV/Marktwert 1,00).
- Ebenso HBAR (M → H), ONDO (M → H).
- ⇒ **Für Spot bei Bitpanda ist der Marktwert die richtige Klassengrundlage.** Der Binance-Umsatz stammt aus dem Hebel-Strang.

**Angebot je Marktwert-Klasse** (heute): feste Höchstmenge H 77 % · M 66 % · S 73 %. Median ausgegeben 82–89 %. *Viel kommt noch* (FDV/Marktwert > 1,5): H 20 % · M 24 % · S 29 %.

**Folgen:**
1. **Betrieb:** Klasse nach Marktwert ist am NB machbar (CoinGecko `markets`, eine Abfrage je 250 Coins).
2. **Messung:** Die gemessene Watchlist (§19.6) beruht auf **Umsatz-Klassen**. Für Marktwert-Klassen in der Vergangenheit fehlt eine freie Historie. Möglich ist eine **Näherung** aus heutiger Umlaufmenge × damaligem Kurs (Vorbehalt: Coins mit späteren großen Freigaben wirken früher zu groß) oder CoinMetrics für 93 Altcoins.
3. **Strukturprofil, erste Gruppierung** (wird verfeinert):
   - A **Angebot**: fest, % ausgegeben, FDV/Marktwert;
   - B **Nutzung**: Gebühren, Halter-Einnahmen, Trend;
   - C **Institution und Tokenisierung**: RWA-Kategorie, RWA-Volumen der eigenen Blockchain, ETF/ETP, Indexaufnahme (z. B. Coinbase 50);
   - D **Bestand**: Alter, Widerstandskraft gegen die Klasse;
   - E **Kategorie**: Meme, Gaming, L1, DeFi, Infrastruktur.
4. **Messbar als Auskunft** (mit Vorgriffsvorbehalt, weil die Fakten von heute stammen): Stürzen Coins mit fester, voll ausgegebener Menge, mit Nutzung, mit RWA-Kategorie bzw. ohne Meme-Kategorie seltener ab, und verdoppeln sie sich häufiger?

## 25. Messplan Marktwert-Klassen, Strukturprofil und Prüfstein QNT — VOR der Messung (06.10.2026)

Nutzer 06.10.: *„Ja, Messplan vorbereiten, prüfen und gegenprüfen.“*

### 25.1 Vorprüfung: Taugt die Näherung *Marktwert(t) = Umlauf heute × Kurs(t)*? (`mw_naeherung_pruefung.py` → `.txt`)

Verglichen mit dem echten Marktwert von CoinMetrics an 16–40 Coins je Stichtag:

| Stichtag | n | Rangkorrelation | Abweichung Median | andere Klasse |
|---|---|---|---|---|
| 01.01.2020 | 16 | 0,96 | 26 % | 25 % |
| 01.01.2021 | 30 | 0,97 | 22 % | 20 % |
| 01.06.2022 | 36 | 0,95 | 17 % | 11 % |
| 01.01.2024 | 36 | 0,84 | 15 % | 17 % |
| 01.01.2026 | 35 | 0,90 | 6 % | 11 % |

- Ausreißer: KNC ×18 (Token-Umstellung), XVG ×0,01, XLM ×0,33, GNO ×0,26. Das sind Unterschiede in der **Definition** der Umlaufmenge zwischen CoinMetrics und CoinGecko, nicht nur Näherungsfehler.
- ⇒ **Brauchbar als Näherung.** Die Rangfolge stimmt weitgehend; rund 10–25 % der Coins stehen an einem Stichtag in einer anderen Klasse.
- ⚠️ Geprüft nur an älteren, großen Coins; bei jungen Coins mit späteren Freigaben ist die Näherung schlechter (sie wirken früher zu groß).

### 25.2 Teil 1 — Watchlist auf Marktwert-Klassen

| | |
|---|---|
| **Marktwert** | Umlauf heute (CoinGecko) × Schluss t. Wo CoinMetrics eine Umlaufmenge zu t hat (66 Coins), gilt die echte |
| ⚠️ **Überlebensverzerrung** | **Eingestellte** Coins haben heute bei CoinGecko keinen Umlauf. Ohne Gegenmaßnahme fielen sie heraus, und genau sie sind das linke Ende. ⇒ Coins **ohne** Umlauf behalten ihre **Umsatz-Klasse** als Ersatz (Ersatzklasse). Ihr Anteil wird je Epoche ausgewiesen |
| **Klassen** | Rang nach Marktwert unter den Altcoins des Universums (ohne BTC, ETH, SOL und Stablecoins wie §14): H Rang 1–30 an t, t−1 und t−2 und ≥ 730 T Kurs · M Rang ≤ 100 (oder ≤ 30 ohne H) · S übrige |
| **Kombination** | **unverändert** aus §19.6 (F1 unten, F2 oben, F8 oben, F9 oben). Keine neue Auswahl, damit es eine Prüfung bleibt und keine neue Suche |
| **Trägt** | wie §19.2/§19.4: Saldo > 0 und Rang ≥ 0,975 in E2 **und** E3, bewegungsgleiche Spiegelprobe besteht, ≥ 10 Coins mit R2. Selbsttest (a)/(b) läuft auf den neuen Zellen erneut vorweg |
| **Ausgewiesen** | je Klasse, Dosis, Weglassprobe, Zeitstabilität, Korb gegen BTC und gegen die Klasse; Wechsel der Klassenbesetzung gegenüber den Umsatz-Klassen |

### 25.3 Teil 2 — Strukturprofil A–E als Auskunft

| Gruppe | Fakt (Stand **heute**) | Vergleich in der Zelle |
|---|---|---|
| A Angebot | Höchstmenge fest · ausgegeben ≥ 90 % · FDV/Marktwert ≤ 1,2 | mit gegen ohne |
| B Nutzung | Gebühren ≥ 1 Mio. $ in den 365 T vor t (DefiLlama, Historie) · Halter-Einnahmen > 0 | mit gegen ohne, nur Stichtage mit Daten (meist E3) |
| C Institution | Kategorie RWA · Coinbase-50-Index | mit gegen ohne |
| D Bestand | Widerstandskraft: Rückgang kleiner als der Median der Klasse | Fünftel (= F1 oben, §19.6) |
| E Kategorie | Meme · L1 · DeFi · Infrastruktur · Gaming · KI | je Kategorie gegen den Rest |

- **Statistik:** Anteil verdoppelt (R2), Anteil Absturz/eingestellt (L), Saldo und Lift gegen die Zelle.
- **Nullwelt:** das Merkmal innerhalb der Zelle vertauscht, 200 Ziehungen.
- **Vergleich nur unter Coins MIT Fakt.** Fehlt der Fakt (häufig bei eingestellten Coins), zählt der Coin nicht als *ohne*, sonst misst man Überleben statt Fakt. Der Anteil fehlender Fakten wird je Epoche ausgewiesen.
- ⚠️ **Kein Urteil *trägt*.** Die Fakten stammen von heute (Vorgriff: Kategorien und Angebot kennt man nur für Coins, die es noch gibt). Hervorgehoben wird *deutlich*, wenn Rang ≥ 0,975 in E2 und E3 und die Spiegelprobe besteht.

### 25.4 Teil 3 — Prüfstein QNT (Anschauung, keine Regel)

- Für 04/2022 bis 12/2022: Klasse nach Marktwert, Rang in der Watchlist (Marktwert-Klassen), die Profil-Fakten A–E.
- Frage: Hätte die Verbindung *gutes Profil + Rang* QNT am Boden gezeigt? QNT bestimmt **keine** Schwelle und keine Auswahl.

### 25.5 Gegenprüfung des Plans

| | |
|---|---|
| **Vorgriff** | Teil 1: der Umlauf von heute (Näherung, §25.1 geprüft). Teil 2: alle Fakten von heute ⇒ nur Auskunft. Gebühren mit echter Historie bis t−1 |
| **Überleben** | Ersatzklasse für Coins ohne Umlauf (Teil 1); Vergleich nur mit Fakt (Teil 2); Anteile ausgewiesen |
| **Grundgesamtheit** | Das Universum bleibt wie §14, nur die **Einteilung** ändert sich. Die Wirkung wird gemessen (Kreuztabelle je Epoche), nicht angenommen |
| **Mehrfachtesten** | Teil 1 ist **ein** Test (unveränderte Kombination). Teil 2 ist Auskunft (rund 14 Fakten), *deutlich* verlangt beide Epochen |
| **Reproduktion (R-R11)** | Vor Teil 1 wird §19.6 mit den **Umsatz-Klassen** bitgleich reproduziert (Saldo E2 +11,0, E3 +13,2 Pp). Erst dann wird die Einteilung getauscht |
| **Gegenprobe** | Marktwert und Klasse für 10 Coins von Hand; Saldo eines Fakts mit pandas; QNT-Werte direkt aus SQL |
| **Ehrlich** | Siebter Blick auf die Altcoin-Daten: Beschreibung. Teil 2 ist mit dem Vorgriff belastet. Der eigentliche Test bleibt vorwärts |

### 25.6 Ergebnis Messung §25 (06.10.2026)

**Belege:**
- `mk_messung.py` → `.txt`
- Gegenprobe `mk_gegenprobe.py` → `.txt`: 11 von 11 gleich (Marktwert, Rang und Klasse für 10 Fälle direkt aus SQL; Saldo eines Fakts mit pandas)

**Teil 0 (R-R11):** §19.6 reproduziert: E2 +0,1098, E3 +0,1319.

**Teil 1 — Watchlist auf Marktwert-Klassen: TRÄGT.**

| | E2 2021–23 | E3 ab 2024 |
|---|---|---|
| Saldo gegen die Klasse · Rang | **+10,4 Pp · 1,000** | **+14,4 Pp · 1,000** |
| Lift verdoppelt / Absturz | 1,12 / 0,86 | 1,24 / 0,93 |
| Spiegelprobe bewegungsgleich | besteht | besteht |
| Korb gg. BTC (Klasse) | −7 % (−12 %) | −26 % (−45 %) |

- **Selbsttest auf den neuen Zellen bestanden.**
- **Dosis** monoton: E3 −16,4 · −6,1 · +2,8 · +4,6 · +14,4 Pp.
- **Weglassprobe** hält: E2 +9,9, E3 +10,2 Pp.
- **Jedes Jahr positiv**, 2019–2025.

| Klasse (Marktwert) | E3 Saldo | Lift verdoppelt / Absturz | Korb E3 (Klasse) |
|---|---|---|---|
| H | **+21,0 Pp** | 1,29 / **0,83** | −4 % (−24 %) |
| M | **+26,5 Pp** | 1,47 / **0,88** | −17 % (−50 %) |
| S | +9,4 Pp | 1,16 / 0,96 | −55 % (−59 %) |

⚠️ **Vorbehalte:**
- **Ersatzklasse 30–39 %:** So viele Coins haben heute bei CoinGecko keinen Umlauf; meist sind sie eingestellt oder klein. Sie stehen mit ihrer Umsatz-Klasse in der Messung. Die Marktwert-Einteilung gilt also voll nur für etwa zwei Drittel.
- **Smallcaps** bleiben auch nach Marktwert schwach (Absturz 0,96).
- **QNT im Juni 2022:** CoinMetrics nennt 24,4 Mio. Umlauf, CoinGecko heute 14,6 Mio. Die Quellen definieren den Umlauf verschieden.

**Teil 2 — Strukturprofil (Auskunft; die Fakten stammen von heute, außer Gebühren und Halter-Einnahmen):**

| Fakt | E2 Saldo (Rang) | E3 Saldo (Rang) | Urteil |
|---|---|---|---|
| A1 Höchstmenge fest | +0,6 (0,82) | +0,8 (0,92) | neutral |
| A2 ausgegeben ≥ 90 % | −0,3 (0,32) | +1,5 (0,94) | neutral |
| A3 FDV/Marktwert ≤ 1,2 | +0,2 (0,74) | +4,1 (1,00) | nur E3 |
| B1 Gebühren ≥ 1 Mio. $/J | −11,9 (0,00; nur 4 % bekannt) | −3,2 (0,01) | **deutlich ungünstig** (wenige Fälle) |
| B2 Halter-Einnahmen > 0 | — | +3,6 (0,95; 7 % bekannt) | zu wenig Daten |
| **C1 Kategorie RWA** | **+8,8 (1,00)** | **+14,2 (1,00)** | **deutlich günstig** (11 bzw. 13 Coins) |
| **C2 Coinbase 50 Index** | **+15,3 (1,00)** | **+13,3 (1,00)** | **deutlich günstig** — ⚠️ starker Vorgriff, siehe unten |
| D1 Widerstand (fiel weniger) | −3,0 (0,00) | −2,3 (0,01) | **deutlich ungünstig** (wie F1 oben) |
| E1 Meme | +2,4 (0,67) | **−15,1 (0,01)** | ungünstig in E3 |
| E2 Layer 1 | +10,6 (1,00) | +0,8 (0,69) | nur E2 |
| E3 DeFi | −9,5 (0,00) | +11,3 (1,00) | **dreht** |
| E4 Infrastruktur | +8,6 (1,00) | −4,5 (0,03) | **dreht** |
| E5 Gaming | +4,5 (0,94) | **−23,8 (0,00)** | ungünstig in E3 |
| E6 KI | +10,8 (1,00) | **−18,2 (0,00)** | **dreht** |

**Einordnung Teil 2:**
1. **Der Vorgriff ist bei C2 am stärksten.** In den Coinbase-50-Index kommt, wer **heute** groß und erfolgreich ist. Damit misst das Merkmal zu einem guten Teil das spätere Ergebnis. ⇒ **Kein Beleg.**
2. **RWA** ist günstig in beiden Epochen. Die Fallzahl ist klein (11–13 Coins), und die Kategorie ist heute vergeben: Wer heute als RWA gilt, hat das Thema überlebt. ⇒ **Hinweis, kein Beleg.**
3. **Angebot (fest, voll ausgegeben)** war in der Vergangenheit **neutral**. Die These *begrenzte Menge schützt* ist mit den Kursen bis heute nicht bestätigt, aber auch nicht widerlegt; der Strukturwandel kommt laut These erst.
4. **Gebühren** wirkten eher **ungünstig**, bei wenigen Fällen. Eine mögliche Ursache sind Freigabe-lastige L2- und DeFi-Tokens (ARB, OP …); das ist **nicht** gemessen.
5. **Kategorien drehen zwischen den Epochen** (DeFi, KI, Infrastruktur). Das sind Moden, keine Qualität. Nur Meme und Gaming waren in E3 klar ungünstig.

**Teil 3 — QNT (Anschauung):**
- Nach Marktwert in 2022 **Midcap** (Rang 47 → 37 → 16 bis 11/2022).
- **Watchlist-Perzentil am Boden 0,26–0,28**, also auch mit Marktwert-Klassen **nicht** im Fünftel.
- **Strukturprofil am Boden:** Höchstmenge fest, voll ausgegeben, FDV/Marktwert ≤ 1,2, RWA, Coinbase 50, Infrastruktur, Widerstand.
- ⇒ Das **Profil** hätte QNT hervorgehoben, die **Watchlist** nicht. Genau dafür ist die Ebene 1 da.

**Zwischenfazit zum Ziel:**
- **Ebene 2 (Gelegenheit)** steht jetzt auf der richtigen Grundlage: Marktwert-Klassen, trägt, am stärksten bei H und M.
- **Ebene 1 (Fortbestand)** lässt sich mit der Vergangenheit nur begrenzt prüfen:
  - Die günstigsten Fakten (RWA, Coinbase 50) sind vom Vorgriff belastet.
  - Das Angebot war neutral, und die Kategorien wechseln mit den Moden.
  - ⇒ Ebene 1 bleibt ein **Fakten-Profil, das der Nutzer gewichtet** (Vorgabe 01.10.). In der Mail wird kenntlich gemacht, welche Fakten in der Vergangenheit **neutral**, **günstig mit Vorbehalt** oder **ungünstig** waren.
- Der echte Test der Nutzer-These *Fortbestand bei Tokenisierung* ist **vorwärts**: Das Protokoll führt das Profil je Coin mit.

## 26. Mailentwurf mit beiden Ebenen (07.10.2026)

Nutzer 06.10.: *„Ja, Mailentwurf mit beiden Ebenen vorbereiten, prüfen und gegenprüfen.“*

**Belege:**
- `mail_entwurf.py` → **`mail_entwurf_beide_ebenen.md`** (Stichtag 01.09.2026, Kurse bis 20.09.2026, Bestand aus der Desktop-Kopie vom 19.07.2026)
- Gegenprobe `mail_gegenprobe.py` → `.txt`: **19 von 19 gleich**. Sie liest den erzeugten Text und rechnet aus SQL nach:
  - keine gesperrten Symbole in der Liste;
  - alle Krypto-Bestände im Bestand-Block;
  - Klasse je Abschnitt;
  - 6 Verkaufsmarken;
  - Profil- und Gebührenwerte;
  - Sprache: kein Kaufaufruf, deutsche Zahlen.

**Aufbau:**
1. Lesehilfe.
2. Phase (Fakten).
3. **Dein Bestand**: alle Krypto-Bestände; Kern gesondert; je Coin Einstufung oder Grund, warum keine; Fortbestand in Sätzen.
4. **Rangliste** nach Marktwert-Klassen: H alle im obersten Fünftel, M und S je die besten 10. Je Coin Sterne, *Gelegenheit* in Worten, seit wann im Fünftel, *neu im Fünftel* bzw. *neu unter den besten 10*, *Fortbestand* mit der Einordnung aus §25.6 und die Verkaufsmarke.
5. Protokoll.
6. **Anhang mit Skalen.**

**Beim Prüfen gefunden und behoben (vor der Gegenprobe):**
- Zahlen mit Punkt und in e-Schreibweise.
- Der irreführende Satz *öffentliche Blockchains*.
- *0,00 Mio. $*.
- Fehlender Warnhinweis bei FTT (kein Strukturprofil).
- AUDIO doppelt unter *nicht mehr* und *gesperrt*.
- Pauschaler Grund bei Bestand-Coins außerhalb des Universums.

**Offene Punkte für den Bau** (aus dem Entwurf sichtbar geworden):
1. **Kursquelle für Bestand-Coins ohne Binance-Spot:** KAS, MORPHO, SUPRA und BRETT enden in den Desktop-Messdaten am 19.08.2026; CANTON läuft als CC an den Futures. Am NB braucht es dafür den Bitpanda-Ticker oder CoinGecko.
2. **Profil-Zuordnung über eine Tabelle statt Kürzelsuche.** CANTON und SUPRA wurden nicht gefunden; mehrdeutige Gebühren-Kürzel (UNI, LINK) sind offen.
3. **Smallcaps:** Fast alle der besten 10 stehen im obersten Zehntel (★★★). Die Sterne trennen dort nicht; das ist mit dem Nutzer zu klären.
4. **QNT** erscheint mit *100 % ausgegeben* (99,5 %, gerundet).
5. Neuzugänge kommen im Betrieb aus dem Bitpanda-Abgleich (im Entwurf Platzhalter).

## 27. Echtes Beispiel der E-Mail und Prüfung der Datenquellen mit Abdeckung (07.10.2026; E-75)

Nutzer 07.10.: *„Ok, ja, Aufbau der Mail ist ok – gib mir ein echtes Beispiel der E-Mail aus. Prüfe die Datenquellen, wir haben bereits einiges angebunden; lies dich ein, was wir haben und was wir benötigen. Ohne Datenquellen und Abdeckungsprüfung bringt das System nichts. Ich bin unterwegs bis abends – schreibe alles Relevante ins Memory, Zentraldokumente und Regelwerke, dann trage alles in den Gesamtplan ein, damit nichts verloren geht.“*

### 27.1 Echtes Beispiel der E-Mail

`mail_beispiel_html.py` → **`mail_beispiel_altcoins.html`**:
- im Stil der REGEL0-Mail (`agent/regel0_mail._als_html`: Inline-CSS, 680 px, Abschnittsüberschriften, Tabellen);
- Betreff *Altcoins September · Fortbestand und Gelegenheit · Watchlist 26 Coins, Bestand 11*;
- am Handy (375 px) im Browser geprüft;
- **nicht versendet.**

Der Inhalt ist der gegengeprüfte Entwurf (§26, 19/19). Der Nutzer hat den Aufbau bestätigt: *„Aufbau der Mail ist ok“*.

### 27.2 Inventar der angebundenen Datenquellen (gelesen am Code, 07.10.)

**Am NB im Betrieb (Scheduler `scheduler/background.py`, Jobs ab Zeile 5110):**

| Job | Takt | Quelle | Ziel |
|---|---|---|---|
| refresh_prices | 15 min | CoinGecko `/simple/price` | Prod `price_cache` (Kurs, Marktwert) |
| refresh_ohlc | 24 h | Kraken OHLC, Rückfall Binance/Bybit | Prod `price_history_ohlc` (auch Nicht-Binance-Coins) |
| marktscan | 04:00 / 16:00 | CoinGecko `/coins/markets` | Prod `marktscan_candidates` (Marktwert, Volumen, Alter geschätzt) |
| lebendigkeit | 03:20 | DefiLlama `/protocols`, `/v2/chains` (TVL-Tageswert); CoinGecko Commits | Prod `lebendigkeit_beobachtung` |
| externe_reihen | 06:35 | CoinMetrics SplyCur; **CoinGecko Umlauf** (`hole_umlaufmenge_cg.taeglich`); DefiLlama Stablecoins; Deribit; CFTC | Prod `externe_reihe`, **`umlaufmenge_cg.db`** (Betriebskopie) |
| lagebild_reihen | 06:40 | **FRED Netto-Liquidität**, Zinsen, Fear & Greed | Prod `macro_snapshot` |
| betriebsreihen | 03:30 | Binance Spot 1d (TRADING + BREAK) | `messdaten.db` **Betriebskopie 500 T** (`_nur_betrieb`) |
| regel0_nachlader | stündlich | Binance Spot/Futures klines, Markpreise | `stundenkurse*.db`, `markpreis*.db` |
| bitpanda_holdings | 30 min | Bitpanda Public API (Schlüssel `BITPANDA_API_KEY`) | Prod **`holdings`** |
| portfolio_wert | 06:30 | — | Prod `portfolio_wert_historie` (`mengen_json` täglich, daraus **Neuzugänge**) |
| Mail | — | Gmail SMTP | `api/email_notify.send_notification_email` |

**Nur am Desktop, von Hand:**
- volle Messbasis (`lade_messreihen.py`, 1,5 GB);
- `hole_tvl_historie.py` (TVL-Verlauf);
- `hole_fremdreihen.py` (Funding, aktive Adressen);
- volle `umlaufmenge_cg.db`.

**Nur in den Spot-Voranalyse-Skripten:** CoinMetrics PriceUSD/MVRV/Marktwert (`coinmetrics.db`, `altcap.db`), **DefiLlama Gebühren und Halter-Einnahmen** (`gebuehren.db`), **CoinGecko Höchstmenge, FDV, Kategorien** (`strukturprofil.db`). Im Betriebscode gibt es sie **nicht**.

### 27.3 Abdeckungsprüfung (`Abfrage 07.10.`, Universum 01.09.2026: 332 Altcoins, Marktwert-Klassen)

| Bedarf der Watchlist | Quelle | im Betrieb angebunden? | Abdeckung (Desktop gemessen) | Lücke / Maßnahme |
|---|---|---|---|---|
| Tageskurs je Altcoin | Binance Spot (`betriebsreihen`) | ✔ NB | **332/332** | — |
| Umlaufmenge → Marktwert-Klasse | CoinGecko (`externe_reihen` → `umlaufmenge_cg.db`) | ✔ NB | **324/332 (98 %)**, Zuordnung 332/332 | 8 Smallcaps ohne Urteil *ok* |
| Allzeithoch, Datum des Hochs, Erstdatum (F1, F2, F8) | volle Kursgeschichte | ✘ NB hat nur **500 T** Betriebskopie | 308/332 brauchen mehr als 500 T | **Stammdatei vom Desktop** (Allzeithoch, Datum, erster Kurs je Coin) per Repo oder USB, am NB täglich fortgeschrieben (neues Hoch → überschreiben) |
| Umsatz 90/365 T (F7, Klassen-Ersatz) | Binance Volumen | ✔ NB (500 T reichen) | 332/332 | — |
| TVL-Verlauf (F9) | DefiLlama | ◐ NB nur Tageswert in `lebendigkeit_beobachtung` | Zuordnung 124/332 (37 %) | prüfen, ob der Tagesverlauf am NB ≥ 180 T reicht; sonst Teilmenge/Desktop-Stammdaten |
| Höchstmenge, FDV, Kategorien (Ebene 1 A, C, E) | CoinGecko `/coins/markets`, `/coins/{id}` | ✘ | **312/332 (94 %)** im Spot-Skript | **monatlicher Abruf am NB** (rund 330 Abfragen; Kontingent 10.000/Monat, gedrosselt) |
| Gebühren, Halter-Einnahmen (Ebene 1 B) | DefiLlama | ✘ | **121/332 (36 %)**; mehrdeutige Kürzel (UNI, LINK, AAVE …) offen | monatlicher Abruf am NB, Zuordnung über die CoinGecko-ID |
| Sperrlisten | `symbol_zuordnung.csv`, Markpreis-Sperre | ✔ Repo/Code | — | beide Listen zusammenführen |
| **Bestand** | Bitpanda (`bitpanda_holdings`) | ✔ NB | 12 Krypto-Positionen (Desktop-Kopie 19.07.) | — |
| **Kurs für Bestand ohne Binance-Spot** | Prod `price_history_ohlc` (Kraken/Bybit), `price_cache` (CoinGecko) | ✔ NB | **7 von 12** ohne Binance-Spot: KAS, MORPHO, BRETT, SUPRA, MON, CANTON, ASTER | Einstufung aus Prod-Kursen rechnen (Universum bleibt Binance; diese Coins nur im Bestand-Block) |
| CoinGecko-ID für Bestand | `abruf_symbol`, config-Watchlist, Prod `price_cache.coingecko_id` | ✔ teilweise | **6 von 12 ohne ID** in `abruf_symbol` | über `price_cache.coingecko_id` (am NB) ergänzen; sonst Zuordnungstabelle |
| Neuzugänge | `portfolio_wert_historie.mengen_json` | ✔ NB | — | Tagesvergleich der Mengen |
| Phase: Netto-Liquidität, Stablecoins | FRED, DefiLlama | ✔ NB | — | — |
| Phase: BTC-Klima (MVRV) | CoinMetrics | ✘ (nur Spot-Skript) | — | Lader am NB (frei, ohne Schlüssel) |
| Phase: Altseason-Breite | Binance-Kurse | ✔ NB (rechenbar) | — | Rechnung einbauen |
| Phase: MACD der Altcoins | CoinMetrics-Marktwerte (`altcap.db`) | ✘ | 93 Altcoins | Lader am NB oder Index aus Umlauf × Kurs |
| Vorwärtsprotokoll | — | ✘ | — | eigene Tabelle/Datei; Schreiber nur der Monatsjob |
| Versand | Gmail SMTP | ✔ | — | neuer Mailtyp |

**Ergebnis:**
- Für den **Kern der Watchlist** (Kurse, Klassen, Rang) sind die Daten am NB **weitgehend da**. Es fehlt eine **Stammdatei** für Allzeithoch und Erstdatum.
- Für **Ebene 1** fehlen im Betrieb **drei Abrufe**: CoinGecko-Profil monatlich, DefiLlama-Gebühren monatlich, CoinMetrics MVRV/Marktwerte täglich.
- **Der Bestand ist die größte Lücke.** 7 von 12 Positionen liegen außerhalb des Binance-Universums. Sie brauchen Prod-Kurse und eine ID-Zuordnung.
- ⚠️ **Am NB nicht nachgewiesen.** Es gibt keinen aktuellen NB-Export, und die Desktop-Prod-Kopie ist vom 19.07. ⇒ Vor dem Bau eine **Betriebsprüfung B1–B9** mit sparsamem Teilexport: Tabellen `lebendigkeit_beobachtung` (Verlaufslänge), `price_history_ohlc` (Nicht-Binance-Coins), `price_cache.coingecko_id`, `umlaufmenge_cg.db` (Frische).
- ⚠️ **Widerspruch in CLAUDE.md:** Die Messbasis-Tabelle sagt *messdaten.db am NB fehlt – mit Absicht*, der Job `betriebsreihen` schreibt dort aber seit 20.09. eine **Betriebskopie** (500 T, `_nur_betrieb`). Beides stimmt im Sinn von *keine Messbasis*; die Zeile ist missverständlich. ⇒ **Dem Nutzer zur Korrektur vorgelegt**, nicht selbst geändert.

### 27.4 KORREKTUR zum Bestand und nächste Schritte für den Weiterbau (07.10.2026)

Nutzer 07.10.: *„Ja, CLAUDE.md korrigieren, falls erforderlich – du hast meinen Bestand bereits mit Kursen abgeglichen, MORPHO, CANTON etc. sollten auch Kurse haben, soweit mir bekannt. Jetzt machen wir Pause, halte alles fest und die nächsten Schritte für den Weiterbau; u. U. sollten wir einen NB-Export full starten davor.“* · *„Hinweis: es gibt bereits eine Übersetzungstabelle für die Symbole bei Hebel.“*

⚠️⚠️ **Korrektur zu §27.3:** Die Bestand-Coins haben **Kurse und CoinGecko-IDs**. Ich hatte nur das Binance-Spot-Universum und die Umlauf-Zuordnung (`abruf_symbol`) abgefragt, nicht die Produktion.

| Coin | Prod `price_history_ohlc` (täglich, Job `refresh_ohlc`) | Prod `price_cache` (15 min) | `stundenkurse_alle` |
|---|---|---|---|
| KAS | ✔ seit 2023 (Bybit/gemessen) | kaspa | ✔ |
| MORPHO | ✔ seit 2024 (Binance/gemessen) | morpho | — |
| BRETT | ✔ seit 2024 (Bybit) | based-brett | ✔ |
| SUPRA | ✔ seit 2024 (Bybit) | supra | — |
| MON | ✔ seit 2025 | monad | ✔ |
| ASTER | ✔ seit 2025 | aster-2 | ✔ |
| CANTON | — | canton-network | ✔ als **CC** (Futures) |

Stand der Desktop-Kopie: Prod-OHLC bis 19.08.; am NB laufend.

- ⇒ Die Lücke ist **kleiner** als in §27.3 beschrieben. Diese Coins liegen nur außerhalb des **Binance-Spot-Universums der Rangliste**.
- Ihre Einstufung wird aus den **Prod-Kursen** gerechnet, ihr Marktwert aus `price_cache`.
- **Übersetzungstabelle:** `Basisinfos/symbol_zuordnung.csv` (Bitpanda ↔ Binance, z. B. CANTON → CC) wird im Hebel-Strang schon genutzt (`agent/regel0_rechnung.py`, `agent/regel0_stundenlauf.py`). Die Watchlist nutzt **dieselbe** Tabelle, dazu `price_cache.coingecko_id` für CoinGecko. **Keine neue Tabelle.**

**CLAUDE.md korrigiert (Nutzer-Ja 07.10.):**
- Die Zeile `messdaten.db` am NB nennt jetzt die Betriebskopie (500 T Binance-Spot, Job `betriebsreihen` 03:30, `_nur_betrieb`, keine Messbasis).
- Bei `umlaufmenge_cg.db` steht jetzt die tägliche Fortschreibung durch `externe_reihen`.

**Nächste Schritte für den Weiterbau (O28), in dieser Reihenfolge:**

| # | Schritt | Wo | Nachweis |
|---|---|---|---|
| **W0** | **NB-Export.** Empfehlung: der **Teilexport** `python nb_teilexport_betriebsdaten.py`; er ist für die Betriebsprüfung B1–B9 gebaut, nur lesend und leicht. Er zeigt Datenbanken, Tabellen, Zeitauflösung und Historie: `lebendigkeit_beobachtung` (TVL-Verlauf), `price_history_ohlc` und `price_cache` (Bestand außerhalb Binance), `umlaufmenge_cg.db` (Frische), `holdings`, `portfolio_wert_historie`. Der **volle** Export (`extract_notebook_diagnose.py`, rund 295 MB) belastet den Betrieb und ist nur nötig, wenn Logs oder Mailverläufe gebraucht werden — **Entscheidung beim Nutzer** | NB | Datei `nb_betriebsdaten_T440.txt` im Austauschordner |
| W1 | Abdeckung **am NB** gegen §27.3 nachweisen; Lücken neu bewerten | Desktop, aus W0 | Tabelle *Bedarf → am NB → Abdeckung* |
| W2 | **Stammdatei** Allzeithoch, Datum des Hochs, erster Kurs je Coin aus der vollen Messbasis (Desktop), ins Repo; am NB täglich fortschreiben (neues Hoch → überschreiben) | Desktop → Repo → NB | Prüfung gegen die volle Messbasis |
| W3 | **Abrufe am NB:** CoinGecko-Profil monatlich (Höchstmenge, FDV, Kategorien; rund 330 Abfragen im Kontingent), DefiLlama-Gebühren und Halter-Einnahmen monatlich (Zuordnung über die CoinGecko-ID), CoinMetrics täglich (MVRV, Marktwerte für BTC-Klima und MACD) | NB-Job | Wache und Seiteneffekt-Nachweis |
| W4 | **Bestand-Einstufung** aus Prod-Kursen für Coins außerhalb Binance-Spot; Übersetzung über `symbol_zuordnung.csv`; Sperrlisten (csv + Markpreis-Sperre) zusammenführen | Code | Gegenprobe wie §26 |
| W5 | **Vorwärtsprotokoll:** eigene Datei/Tabelle; Schreiber nur der Monatsjob | Code | — |
| W6 | **Monatsjob + Mail** (Inhalt `mail_entwurf.py`, Darstellung `mail_beispiel_html.py`) | Code | Prüfstand mit echter config.yaml |
| W7 | **Betriebsprüfung B1–B9** am NB; dann Pull, Neustart, Export nach ~30 min | NB | Kontrollen K-WL-1… |

⚠️ **Für Hebel und Spot gilt weiter:** Der Hebel hat Vorrang (Testwoche bis 10.10., N4). Die Watchlist ist Spot-Strang (T-1..T-6) und **kein** Kaufsignal.

### 27.5 W0/W1 — Abdeckung AM NB nachgewiesen (Teilexport 07.10.2026 07:19, `nb_betriebsdaten_T440.txt`, *SCHLUSS: vollständig*)

Nutzer 07.10.: *„Teilexport am NB erledigt, prüfe die Abdeckung und noch alle offenen Punkte beim Hebel.“*

| Bedarf (§27.3) | am NB vorgefunden | Urteil |
|---|---|---|
| Tageskurse Binance-Spot | `messdaten.db` Betriebskopie (`_nur_betrieb`): **532 Symbole**, 2019-02-14 bis 2026-10-07, rund 488.000 Zeilen, Stand heute | ✔. ⚠️ Die Spanne reicht weiter zurück als 500 T (im Mittel rund 900 Zeilen je Symbol). Ob das Allzeithoch je Coin vollständig drin ist, zeigt der Export nicht ⇒ **W2 Stammdatei bleibt**, sie ist auch die robustere Lösung |
| Umlaufmenge → Marktwert-Klasse | `umlaufmenge_cg.db`: **374 Symbole**, 08.09. bis **07.10.** (täglich frisch), Zuordnung `abruf_symbol` 407 | ✔ |
| Marktwert direkt | Prod `marktscan_candidates` **955 Symbole** mit `market_cap_usd` (CoinGecko, zweimal täglich) | ✔ zusätzliche Quelle, Gegenprobe zu Umlauf × Kurs |
| Bestand | Prod `holdings` **39 Symbole** mit Menge > 0. Krypto u. a.: ALGO, ASTER, AVAX, BEAMX, BIO, BRETT, BTC, CANTON, ETH, INJ, KAIA, KAS, LINK, MON, MORPHO, PLUME, QNT, SOL, SUPRA, TURBO, XDC, XLM; dazu ETC/ETF/Aktien | ✔. Die Desktop-Kopie (12 Krypto) ist **veraltet**; im Betrieb rund 22 Krypto-Positionen |
| Kurse Bestand außerhalb Binance | Prod `price_history_ohlc` **67 Symbole** (bis 06.10.), `price_cache` **61 Symbole** (Watchlist + Bestand) | ✔ |
| Neuzugänge | `portfolio_wert_historie` 08.05. bis 06.10. (`mengen_json`) | ✔ |
| TVL-Verlauf (F9) | Prod `lebendigkeit_beobachtung` **203 Symbole**, rund 8.450 Zeilen (im Mittel ~42 je Symbol); Zeitspanne im Export **nicht** ausgewiesen | ◐ für eine 180-T-Änderung vermutlich zu kurz ⇒ **W3:** DefiLlama-Protokollverlauf monatlich (ein Abruf je Protokoll liefert den ganzen Verlauf) |
| Höchstmenge, FDV, Kategorien | — | ✘ wie erwartet ⇒ W3 CoinGecko monatlich. Kontingent messbar über `api_call_kontingent(_taeglich)` |
| Gebühren, Halter-Einnahmen | — | ✘ ⇒ W3 DefiLlama monatlich |
| Phase: Stablecoins, Liquidität | `externe_reihe` 7.087 Zeilen ab 2017, `macro_snapshot` bis 07.10. | ✔ |
| Phase: BTC-Klima (MVRV), MACD | — | ✘ ⇒ W3 CoinMetrics täglich |
| `tvl_historie.db`, Spot-Messdateien (`data/_spot/*`) | nicht am NB | wie erwartet (Desktop) |

**Ergebnis W1:**
- Der **Kern** der Watchlist (Kurse, Klasse, Rang, Bestand, Neuzugänge, Liquidität, Stablecoins) ist **am NB nachgewiesen**.
- **Offen bleiben:**
  - W2 Stammdatei Allzeithoch und Erstdatum;
  - W3 drei Abrufe (CoinGecko-Profil, DefiLlama-Gebühren und TVL-Verlauf, CoinMetrics).
- **Neu:** Der Bestand ist am NB fast doppelt so groß wie in der Desktop-Kopie. Der Bestand-Block muss rund 22 Krypto-Positionen tragen; XDC und PLUME liegen dort ebenfalls außerhalb von Binance-Spot.


## 28. O28 Bauumfang — Vorlage zur Abstimmung (08.10.2026, Paket P4, nur Papier)

Nutzer 08.10.: *„Ja, P4 vorbereiten, prüfen und gegenprüfen.“* Dazu der Entscheid zu O26: *„… ich habe CT wie auch XDC manuell hinzugefügt; wenn wir das automatisieren können analog Hebel, wäre das gut. Es muss sauber und stabil über die unterschiedlichen Symbole je Datenquelle funktionieren.“*

⚠️ **Regeln für diesen Bau:**
- **T-2:** Spot-Betriebscode erst, wenn der Hebel freigegeben **und** dieser Umfang abgestimmt ist, also frühestens nach dem 10.10.
- **Hebel hat Vorrang** (T-4). **Eine NB-Änderung zur Zeit**, nicht parallel zu O29.
- **Nur kostenfreie Quellen** (Projektregel). Alle unten genannten sind frei.
- Die Watchlist-Mail ist **Information, kein Kaufsignal** (Regel 4); ihr Takt ist kein Signalgeber (Regel 1).

### 28.1 Was das System liefert

Die Monatsmail **„Altcoins: Fortbestand und Gelegenheit“**, Aufbau bestätigt (§26, E-75):
1. Lesehilfe, Phase.
2. **Dein Bestand**: alle Krypto-Positionen und Neuzugänge, mit Einstufung oder Grund, warum keine.
3. **Rangliste** nach Marktwert-Klassen H/M/S.
4. Protokoll, Anhang mit Skalen.

Dazu **O26**: Neue Bitpanda-Bestände kommen von selbst in die Watchlist.

### 28.2 Bausteine — Stufe 1 (Kern) und Stufe 2 (Ebene 1 Strukturprofil)

| # | Baustein | Daten am NB (Nachweis §27.5 / 08.10.) | neu zu bauen | Prüfung | Stufe |
|---|---|---|---|---|---|
| **W2** | **Stammdatei** Allzeithoch, Datum des Hochs, erster Kurs je Coin | Betriebskopie `messdaten.db` reicht nicht sicher (≥ 500 T, Hoch oft früher) | einmal aus der vollen Messbasis (Desktop) ins Repo; am NB täglich fortschreiben (neues Hoch → überschreiben) | gegen die volle Messbasis, alle 332 Coins | 1 |
| **W4** | **Bestand-Einstufung**, auch außerhalb Binance-Spot | ✔ Prod `price_history_ohlc` und `price_cache` (alle 25 Krypto-Bestände mit CoinGecko-ID; Kurs fehlt nur beim neuen CT) | Einstufung aus Prod-Kursen; Übersetzung `symbol_zuordnung.csv` (eine Tabelle für Hebel und Spot); Sperrlisten zusammenführen | Gegenprobe wie §26, an allen Beständen | 1 |
| **W8 = O26** | **Automatische Aufnahme** neuer Bitpanda-Bestände in die Watchlist (Regeln §28.4) | ✔ `holdings`, `bitpanda_wallet_saldo` (asset_id), `bitpanda_katalog` (Gruppe), `price_cache` | Aufnahme über die **Asset-ID**, nicht über das Kürzel; ersetzt die tägliche Warnmail *„Position ohne Watchlist-Eintrag“* | Gegenprobe an allen 40 Beständen und den Fällen CT, XDC, BIO, CANTON | 1 |
| **W5** | **Vorwärtsprotokoll** der Watchlist (welcher Coin stand wann wo, Folge nach 3/6/12 Monaten) | — | eigene Tabelle; Schreiber nur der Monatsjob | Seiteneffekt | 1 |
| **W6** | **Monatsjob und Mail** (Inhalt `mail_entwurf.py`, Darstellung `mail_beispiel_html.py`) | ✔ Kern: Kurse, Klasse (`umlaufmenge_cg.db`), Rang, Bestand, Neuzugänge, Phase Liquidität/Stablecoins | Job, Mailtyp, Abschnitte | Prüfstand mit echter `config.yaml` | 1 |
| W3a | **CoinMetrics** täglich: BTC-Klima (MVRV), Marktwerte für den MACD | ✘ | Lader (frei, ohne Schlüssel) | Wache, Seiteneffekt | 2 |
| W3b | **CoinGecko-Profil** monatlich: Höchstmenge, FDV, Kategorien | ✘ | ~330 Abrufe im Monat (Kontingent 10.000, gedrosselt) | Seiteneffekt | 2 |
| **W3t** | **DefiLlama TVL-Verlauf** je Protokoll (ein freier Abruf liefert den ganzen Verlauf) — ⚠️ **Korrektur 08.10.: gehört in Stufe 1**, denn F9 (*Nutzung wächst schneller als der Kurs*) ist eines der **vier Merkmale der gemessenen Rangliste** (F1, F2, F8, F9; `as_messung.txt`) | ◐ nur Tageswert (`lebendigkeit_beobachtung`, ~42 Werte je Symbol) | Zuordnung Protokoll ↔ Coin über die CoinGecko-ID | gegen `tvl_historie.db` der Messung | **1** |
| W3c | **DefiLlama** monatlich: Gebühren, Halter-Einnahmen (nur Auskunft im Fortbestand) | ✘ | Zuordnung über die CoinGecko-ID | Seiteneffekt | 2 |
| **W7** | **Betriebsprüfung** B1–B9 am NB, dann Pull, Neustart, Export | — | — | Kontrollen K-WL-1… | je Stufe |

**Grundsatz der Trennung (Korrektur 08.10.):**
- **Stufe 1** enthält **alles, was in die Bewertung eingeht**: die vier Merkmale der Rangliste einschließlich TVL-Verlauf, die Klasse, den Bestand und die Marke.
- **Stufe 2** enthält **nur Auskunft**: das Strukturprofil (Ebene 1 A–E), BTC-Klima und MACD in der Phase.
- So rechnet der Betrieb von Anfang an **dieselbe** Rangliste wie die Messung. Die Auskunftsstellen stehen bis Stufe 2 als *„noch nicht angebunden“* da.

### 28.3 Aufwand und Reihenfolge (Schätzung)

| | Inhalt | Aufwand | NB-Änderungen |
|---|---|---|---|
| Stufe 1 | W2 → W3t → W4 → W8 (O26) → W5 → W6 → W7 | etwa 3 Arbeitstage am Desktop | **eine** (Pull + Neustart, dann Kontrolle) |
| Stufe 2 | W3a → W3b → W3c → W7 | etwa 1–2 Arbeitstage | eine |

### 28.4 O26 — die Brücke der Symbolwelten (Befund an der NB-Sicherung 08.10. 06:31)

**Bestand:** 40 Positionen mit Menge > 0, davon **25 Krypto** (Gruppe *coin* oder *token*), der Rest Aktien, ETF und ETC.

| Befund | Fälle | Folge für die Regel |
|---|---|---|
| **Gleiches Kürzel, anderes Asset** | **BIO** steht im Bitpanda-Katalog als **Aktie** *und* als Token. Der Bestand ist der Token (CoinGecko `bio-protocol`, Binance BIO) | Zuordnung **über die Asset-ID** (`bitpanda_wallet_saldo.asset_id` → `bitpanda_katalog`), nie über das Kürzel. ⚠️ Die Hebel-Aufnahme (`auto_add_unknown_hebel_symbols`) sucht über das Kürzel; dieselbe Lücke ist dort möglich (zum Hebel-Strang gemeldet) |
| **Anderer Name bei Binance** | CANTON → CC (Futures), CAT → 1000CAT | nur über `symbol_zuordnung.csv` (eine Tabelle), nie Namensgleichheit allein |
| **Kein Binance-Spot** | XDC, SUPRA, VSN, EURCV, CANTON | Kurs aus Prod (`price_history_ohlc`, `price_cache`); nur im Bestand-Block, nicht in der Rangliste (Grundgesamtheit bleibt Binance) |
| **Neu und noch ohne Prod-Kurshistorie** | **CT** (CoinGecko `concrete`; Binance führt ein CT) | **Preisabgleich** Bitpanda ↔ CoinGecko ↔ Binance vor der Aufnahme; bei Abweichung > 2 % keine Binance-Zuordnung |
| CoinGecko-ID | alle 25 Krypto-Bestände haben eine in `price_cache` | — |

**Regeln für die automatische Aufnahme (Vorschlag):**
1. **Nur Krypto:** Gruppe *coin* oder *token* laut Katalog **zur Asset-ID**.
2. **CoinGecko-ID:**
   - zuerst aus `price_cache`;
   - sonst Namenssuche (wie beim Hebel), aber **nur bei genau einem Treffer** und mit **Preisabgleich** gegen Bitpanda (≤ 2 %).
3. **Binance-Zuordnung:**
   - zuerst `symbol_zuordnung.csv`;
   - sonst gleiches Kürzel **mit Preisabgleich** (≤ 2 %);
   - sonst keine (der Coin steht nur im Bestand-Block).
4. **Bei Zweifel** (mehrere Treffer, Preisabweichung, Gruppe unklar): **nicht** aufnehmen, sondern **einmal** melden mit Grund (*„manuell prüfen“*). Gesperrte Kürzel bleiben gesperrt.
5. Aufgenommen mit `rolle=taktisch`, `beobachtungsstatus=beobachtung` wie beim Hebel; die Mail vermerkt *„neu aufgenommen“*.
6. **Gegenprobe vor dem Bau:**
   - Die Regel nachträglich auf alle 40 Bestände anwenden. Sie muss für die 25 Krypto-Werte dieselben IDs liefern wie heute in `price_cache`, die 15 übrigen ablehnen und BIO dem Token zuordnen.

### 28.5 Zur Abstimmung (Nutzer)

| | Frage | Empfehlung |
|---|---|---|
| U1 | Umfang: **Stufe 1 zuerst**, Stufe 2 danach — oder beides in einem Bau? | **Stufe 1 zuerst**: Der Kern ist am NB nachgewiesen, und die Mail kommt früher |
| U2 | O26 wie §28.4 (Asset-ID, Preisabgleich ≤ 2 %, bei Zweifel melden statt aufnehmen)? | ja |
| U3 | Takt: Monatsmail (wie entworfen); neue Bestände werden **sofort** aufgenommen, erscheinen aber erst in der nächsten Monatsmail | ja |

**Fachlich, also von mir zu lösen und nicht abzustimmen:** Bei den Smallcaps trennen die Sterne nicht, weil fast alle im obersten Zehntel liegen (§26, offener Punkt 3). Das wird in W6 per Messung entschieden (Rang innerhalb der Klasse statt fester Zehntel).

### 28.6 Gegenprüfung dieser Vorlage
- **Daten am NB:** Kurse, Klasse, Rang, Bestand und Neuzugänge sind am Teilexport vom 07.10. nachgewiesen (§27.5); Bestand, IDs und Prod-Kurse an der Sicherung vom 08.10. (§28.4).
- **Kostenfrei:** Binance, CoinGecko (Demo-Kontingent, schon genutzt), DefiLlama, CoinMetrics Community: ✔ alle frei.
- **Keine neue Übersetzungstabelle:** `symbol_zuordnung.csv` ist die eine Tabelle (Nutzerhinweis 07.10.). ✔
- **T-1 bis T-6:** Spot-Doku hier und Plan O28/O26; kein Spot-Code in diesem Paket. ✔
- **Offen und genannt:** Preisabgleich CT, BIO-Lücke im Hebel-Weg.


### 28.7 Entscheidungsgrundlage U1–U3 im Detail (08.10.2026)

Nutzer 08.10.: *„Ja, gib mir alle U1 bis U3 Details für die Entscheidung – was sind genau die Monatsmails, keine Signale je Asset? Halte alles fest in Plan und Doku.“*

#### Was die Monatsmail ist — und was nicht

**Sie ist eine Übersicht mit Bewertung je Asset, aber kein Signal mit Zeitpunkt.**

| | Monatsmail Altcoins (Spot) | zum Vergleich: REGEL0-Mail (Hebel) |
|---|---|---|
| Frage | *Welche Altcoins haben auf 6–12 Monate ein günstiges Chance-Risiko-Verhältnis?* | *Lohnt dieser Kauf in den nächsten 24 Stunden?* |
| je Asset | **Rang in seiner Marktwert-Klasse** (★★★ oberstes Zehntel, ★★ übriges oberstes Fünftel), *Gelegenheit* in Worten, *Fortbestand* als Fakten, die **Marke** | Kauf JETZT, Hebelstufe, Ausstieg nach 24 h |
| Zeitpunkt | keiner; der Monatserste ist nur der **Berichtstag** (Regel 1: der Takt ist kein Signalgeber) | die Signalstunde |
| Wer handelt | du, mit der Mail als Grundlage | du, nach der Signalmail |

**Warum keine Signale mit Zeitpunkt:**
- Für Spot-Altcoins wurden **Zeitpunkt-Regeln** gemessen: wann kaufen nach Lage, Makro, Liquidität, MACD, Momentum (§7, §16, §20 u. a.).
- **Keine schlug BTC.** Was trägt, ist die **Auswahl**: Coins im obersten Fünftel ihrer Klasse hatten über 12 Monate häufiger eine Verdopplung und seltener einen Absturz. Der Saldo liegt in E3 bei **+14,4 Pp** gegen die eigene Klasse, bei H **+21,0**, bei M **+26,5**, bei S nur **+9,4** (§25.6).
- Der Horizont ist **12 Monate**. Darauf passt ein Monatsbericht; eine Stundenauslösung würde dort einen Zeitpunkt vortäuschen, der nicht gemessen ist.

**Inhalt Monat für Monat** (Aufbau bestätigt §26, Beispiel `mail_beispiel_altcoins.html`):
1. **Lesehilfe:** die zwei Ebenen *Fortbestand* (Fakten, du gewichtest) und *Gelegenheit* (gemessener Rang); die Sterne; die Marke.
2. **Phase**, nur Fakten: Altseason-Breite, Netto-Liquidität, Stablecoins. BTC-Klima und MACD kommen ab Stufe 2.
3. **Dein Bestand:** jede Krypto-Position und jeder Neuzugang. Je Coin steht der Rang in der Klasse oder der Grund, warum keiner (zu jung, kein Binance-Spot …), dazu die Fakten des Fortbestands. BTC/ETH/SOL stehen als Kern gesondert.
4. **Rangliste:** Highcaps alle im obersten Fünftel, Mid- und Smallcaps je die besten 10. Je Coin: Sterne, seit wann im Fünftel, *neu im Fünftel* bzw. *neu unter den besten 10*, Fortbestand und die **Marke**.
5. **Nicht mehr in der Liste** und **wegen Datensperre ausgeschlossen**.
6. **Protokoll:** Jede Liste wird gegen ihre Klasse und gegen BTC mitgeschrieben; abgerechnet wird nach 6 und 12 Monaten.
7. **Anhang mit Skalen:** welches Kriterium günstig oder ungünstig war, und warum.

**Die Marke** ist der gemessene Ausstieg des Protokolls: 35 % unter dem Höchststand seit dem Kauf, mindestens aber die Hälfte des Kaufkurses. In der Mail steht sie als Wert mit dem heutigen Abstand (*„ok“* oder *„unterschritten“*). **Sie löst nichts aus.** Bis das Protokoll nach 6 und 12 Monaten abgerechnet ist, wird über Geld nicht nach Regel entschieden (§26).

#### U1 — Umfang des ersten Baus

| Option | Inhalt | Für | Gegen |
|---|---|---|---|
| **A Stufe 1, danach Stufe 2** (Empfehlung) | Stufe 1 = alles, was in die **Bewertung** eingeht: Stammdatei Allzeithoch (W2), **TVL-Verlauf (W3t)**, Bestand-Einstufung (W4), O26 (W8), Protokoll (W5), Monatsjob und Mail (W6), Betriebsprüfung (W7). Stufe 2 = **Auskunft**: Strukturprofil, BTC-Klima, MACD | die Mail kommt früher; die Rangliste ist von Anfang an **dieselbe wie gemessen**; eine NB-Änderung je Stufe | der Fortbestand steht bis Stufe 2 nur teilweise da (Alter, Abstand zum Hoch; ohne Höchstmenge, FDV, Kategorien, Gebühren) |
| B Stufe 1 und 2 in einem Bau | alles auf einmal | eine einzige NB-Änderung | ~1–2 Tage später, ein größerer Pull mit mehr Fehlerstellen |
| C nur Stufe 1 | Stufe 2 entfällt | am wenigsten Aufwand | dein Wunsch nach einer *inhaltlichen* Bewertung (Fortbestand, z. B. Höchstmenge wie bei QNT) bliebe unerfüllt |

**Folge von A:**
- Erster Monatsbericht nach dem Bau von Stufe 1, etwa 3 Arbeitstage nach dem Start (frühestens ab dem 10.10., nach der Freigabe Hebel, T-2), dann nächster Monatserster oder einmalig sofort.
- Stufe 2 folgt etwa 1–2 Tage später, als eigene NB-Änderung.

#### U2 — Regeln der automatischen Aufnahme (O26)

| Option | Ablauf | Risiko |
|---|---|---|
| **A streng** (Empfehlung) | (1) Asset über die **Bitpanda-Asset-ID** bestimmen, nicht über das Kürzel; (2) nur Gruppe *coin* oder *token*; (3) CoinGecko-ID aus `price_cache`, sonst Namenssuche mit **genau einem Treffer** und **Preisabgleich**; (4) Binance aus `symbol_zuordnung.csv`, sonst gleiches Kürzel **mit Preisabgleich**, sonst keine; (5) bei Zweifel **nicht** aufnehmen, sondern **einmal** melden *„manuell prüfen: Grund“* | gering. Im Zweifel macht es eine Meldung, nie eine falsche Aufnahme |
| B wie beim Hebel | Kürzel-Suche im Bitpanda-Katalog, Namenssuche bei CoinGecko | **BIO** würde womöglich der **Aktie** zugeordnet (Kürzel doppelt); ein falscher Binance-Kurs ginge in Rang und Marke ein |
| C weiter von Hand | wie heute (CT, XDC) | Aufwand bei dir; die Warnmail kommt täglich |

**Was A mit dem heutigen Bestand täte** (geprüft an der NB-Sicherung 08.10.):

| Fall | Ergebnis |
|---|---|
| BIO | Asset-ID → Token *Bio Protocol*, CoinGecko `bio-protocol`, Binance BIO ✔ |
| CT | CoinGecko `concrete`; Binance-CT nur nach Preisabgleich, sonst nur im Bestand-Block |
| XDC, SUPRA, VSN, EURCV | aufgenommen, kein Binance-Spot ⇒ nur im Bestand-Block (Prod-Kurse) |
| CANTON | aufgenommen, Binance über die Tabelle als CC (Futures) |
| Aktien, ETF, ETC (15) | nicht aufgenommen (Gruppe) |

**Die Schwelle des Preisabgleichs** (Vorschlag ≤ 2 %) wird nach unserer Regel **gemessen, nicht gewählt**: vor dem Bau die Abweichungen Bitpanda ↔ CoinGecko ↔ Binance an allen Beständen, Schwelle über der normalen Streuung. Abzustimmen ist nur das Prinzip.

Gleichzeitig wird die Hebel-Aufnahme (H13) auf **dieselbe** Regel umgestellt: **eine** Zuordnung für Hebel und Spot.

#### U3 — Takt und Hinweise zwischendurch

| Option | Inhalt | Für | Gegen |
|---|---|---|---|
| **A Monatsmail** (Empfehlung), O26-Aufnahme sofort und still | Rang, Bestand und Neuzugänge einmal im Monat; ein neuer Bestand wird sofort aufgenommen und steht in der nächsten Mail als *„neu aufgenommen“* | passt zum 12-Monats-Horizont; keine Scheinaktualität | ein Neukauf am 2. erscheint erst am nächsten Monatsersten |
| A+ wie A, dazu ein **Sofort-Hinweis nur bei Fakten zum Bestand** | Binance kündigt für einen **gehaltenen** Coin ein Delisting an oder setzt ein Monitoring-Kennzeichen (Daten aus O29); oder O26 meldet *„manuell prüfen“* | wichtige Fakten zum Bestand kommen rechtzeitig, ohne neue Bewertung | eine zusätzliche Mailart; das Delisting eines gehaltenen Coins ist selten, aber teuer |
| B wöchentlich | Rangliste jede Woche | häufiger Überblick | der Rang ändert sich wöchentlich kaum; mehr Lesen ohne neue Information |

**Empfehlung A+:** Der Sofort-Hinweis zum Delisting eines **gehaltenen** Coins nutzt die O29-Daten. Er ist ein **Fakt** und kein Signal (Regel 4: kein Auslöser, du entscheidest).

#### Was nach deiner Entscheidung geschieht
1. Eintrag als **E-85** und in Plan **O28/O26**.
2. **Bau ab dem 10.10.** nach der Freigabe Hebel und nach P5 (O29 einschalten), in der Reihenfolge von U1.
3. Vor dem Bau: **Messung der Preisabgleich-Schwelle** (U2) und **Gegenprobe O26** an allen 40 Beständen.


## 29. Spot-EINSTIEG auf der Watchlist — Vorprüfung und Messplan VOR der Messung (08.10.2026)

Nutzer 08.10.:
- *„Also meine Meinung zur Spot-Lösung: Ein Newsletter 1× pro Monat ohne konkrete Handlungen, nur Rangfolgen mit Informationen, das ist nicht das eigentliche Ziel für den Einstieg – weil es somit keinen gibt.“*
- *„Ja, Messplan vorbereiten, prüfen und gegenprüfen – den Newsletter-Plan nicht gänzlich verwerfen, sondern prüfen, wie wir zusätzlich sinnvolle Spot-Einstiege bewerten können.“*

**Die Frage:** Gibt es auf der Watchlist eine **Einstiegsregel** (wann, welcher Coin, wie aussteigen), die **BTC schlägt**? Gemessen gegen BTC, weil das die Alternative ist: Wer keine Altcoins kauft, hält den Kern.

**Was schon gilt (R-R11):**
- Die Auswahl trägt gegen die eigene Klasse (§25.6).
- Die Führung X2 (= Marke: Nachlauf −35 % vom Hoch seit Kauf, Notbremse −50 % vom Kauf) machte aus dem E3-Korb −4 % statt −42 %, nach der strengen Regel *knapp nicht bestätigt* (§21.6 B5).
- **BTC schlug seit 2024 weder Halten noch Führen** (§22, Punkt 8).
- Zeitpunkt-Regeln ohne Watchlist (Lage, Makro, Liquidität, Momentum, MACD) schlugen BTC nicht.

### 29.1 Vorprüfung (Stufe 1) — nur die Wahl-Epoche E2, von E3 nur Anzahlen

`ein_vorpruefung.py` → `.txt`, Gegenprobe `ein_vorpruefung_gegenprobe.py` **52/52** (Ausstieg mit zweiter Umsetzung, Breite mit eigener Rangrechnung, E-c-Einstiege, **E3 ohne Ertragszahl**).

| Arm | Regel | E2 Einstiege | E2 gegen BTC Mittel / Median | Anteil > BTC | E3 Einstiege (nur Anzahl) |
|---|---|---|---|---|---|
| KL | ein beliebiger Coin der Klasse (Vergleich) | 10.494 | +2,7 % / −15,8 % | 28 % | 7.471 |
| A0 | im obersten Fünftel (= die Liste der Monatsmail) | 2.133 | +5,5 % / −13,5 % | 29 % | 1.519 |
| E-a | **Eintritt** ins Fünftel | 367 | +4,9 % / −12,6 % | 31 % | 183 |
| **E-b** | E-a **und Phase offen** (Altseason-Breite ≥ 50 %) | **143** | **+17,6 % / −6,6 %** | **43 %** | **28** |
| E-c | E-a und Relativstärke (30 T besser als BTC, binnen 60 T) | 345 | +5,5 % / −12,9 % | 30 % | 156 |

**Was die Vorprüfung zeigt:**
1. **Ausgestiegen wird fast immer über die Marke** (98–100 %), im Median nach 38–68 Tagen. Altcoins fallen fast immer irgendwann 35 % unter ihr Hoch.
2. **Nur das Phasen-Tor (E-b) verschiebt das Bild deutlich:** Median −6,6 % statt −13 %, 43 % statt 30 % schlagen BTC. Eintritt (E-a) und Relativstärke (E-c) allein bringen kaum etwas gegenüber A0.
3. ⚠️ **In E3 war die Phase selten offen:** Die Breite stand nur an **15 %** der Stichtage auf ≥ 50 % (E2: 30 %). E-b hat in E3 nur **28 Einstiege**. Ob das für eine Bestätigung reicht, ist offen. Das legt der Plan unten vorab fest.

### 29.2 Messplan (vorab festgelegt; Rechnung `ein_messung.py`, Desktop, nur lesend)

| | Festlegung |
|---|---|
| Grundlage | wie §25.6: Marktwert-Klassen, Kombination F1 unten / F2 oben / F8 oben / F9 oben, oberes Fünftel = Perzentil in der Zelle > 0,8, monatliche Stichtage, eingestellte Coins eingeschlossen; Kauf zum Schluss des Folgetags |
| **Haupt-Hypothese** | **E-b:** Eintritt ins oberste Fünftel **bei offener Phase** (Altseason-Breite ≥ 50 % am Stichtag: Anteil der 50 größten Altcoins nach Marktwert mit 90-T-Ertrag über BTC) |
| Ausstieg | **X2 = die Marke** (wie §21.6); Auskunft dazu **X0** 12 Monate halten |
| Zielgröße | Ertrag **gegen BTC** über dieselbe Haltedauer, (1 + r_Coin) / (1 + r_BTC) − 1, brutto (Kosten beiderseits gleich; netto mit 1 % je Seite als Auskunft, `kosten_belegt=False`) |
| Gewichtung | je Stichtag der Korb (Mittel seiner Einstiege), dann Mittel über die Stichtage (wie B5) |
| **Teil 0 (R-R11)** | §21.6 B5 X2 mit dieser Ausstiegsumsetzung nachrechnen (Korb nach Kosten 1,25 % je Seite: E2 +31,8 %, E3 −4,0 %); Abweichung > 1 Pp **bricht ab** |
| **Trägt** (E3, alle Bedingungen) | (1) Mittel der Stichtag-Körbe gegen BTC **> 0**, Block-Bootstrap über Stichtage (2.000) **≥ 95 %** über null; (2) **besser als die Zufallswelt** *gleiche Stichtage mit offener Phase, zufällige Coins derselben Klasse, gleicher Ausstieg* (200 Ziehungen, Rang ≥ 0,95); (3) **mindestens 20 Einstiege an mindestens 4 Stichtagen** |
| **Nicht entscheidbar** | wenn (3) fehlt. ⇒ Das Ergebnis steht als Beschreibung da, und E-b geht ins **Vorwärtsprotokoll** |
| Auskunft | E-a, E-c, A0, KL mit denselben Kennzahlen; E-b gegen E-a (bringt das Tor etwas?); je Klasse H/M/S; Jahre 2024/2025; Weglassprobe ohne die 5 größten Gewinner; Asymmetrie (realisiert ≥ ×2 gegen ≤ −50 %); X0 statt X2 |
| Selbsttest | (a) **Zufalls-Tor**: dieselbe Zahl offener Stichtage zufällig verteilt, 100 Welten → Fehlalarm ≤ 5 %; (b) **gepflanzt**: nur Einstiege mit späterem Ertrag über BTC → muss tragen |
| Mehrfachtesten | **eine** Haupt-Hypothese; alle anderen Arme sind Auskunft |

### 29.3 Was aus jedem Ergebnis folgt (vorab)

| Ergebnis | Folge für Spot und die Mail |
|---|---|
| **trägt** | Aus der Watchlist wird ein **Einstiegssignal je Coin**: *„Eintritt ins oberste Fünftel bei offener Phase → Kauf; Marke X; Ausstieg über die Marke.“* Es kommt als **Ereignis-Mail**, sobald es eintritt, mit Größe nach deinen Startwerten. Die Monatsübersicht bleibt daneben |
| **nicht entscheidbar** (wahrscheinlich, 28 Fälle) | Die Monatsmail bekommt den Abschnitt **„Einstiegskandidaten“** mit dem Phasen-Tor als **Fakt** (*Phase offen / zu*) und den Eintritten ins Fünftel. Jeder E-b-Eintritt wird ab sofort **vorwärts protokolliert**; Prüfung, sobald 20 neue Fälle da sind |
| **trägt nicht** | Ein Altcoin-Einstieg gegen BTC ist **nicht belegt**. Die Handlung ist dann der **Kern** (Akkumulation, G1 §10 offen); die Mail bleibt Beobachtung mit Vorwärtsprotokoll |

⚠️ **Ehrliche Erwartung:**
- E3 war für Altcoins gegen BTC ein **durchgehend fallender** Markt (Korb der Klasse −45 %).
- Die Phase war nur an 15 % der Stichtage offen. Am wahrscheinlichsten ist **„nicht entscheidbar“**.
- Das Phasen-Tor ist trotzdem die richtige Spur. Die Vorgabe des Nutzers (*„massive Altseason möglich“*) ist genau die Lage, in der das Tor aufgeht. Für diesen Fall braucht es die Regel **fertig und protokolliert**, bevor er eintritt.

### 29.4 Ergebnis der Messung (08.10.2026, nach dem Plan §29.2)

⚠️ **ÜBERHOLT am 08.10. nachmittags (§30.1/§30.3):** Nach drei Datenkorrekturen an den Umlaufmengen hat E3 **34 Einstiege an 4 Stichtagen** (−23,9 % gegen BTC). Das vorab festgelegte Urteil ist damit **TRÄGT NICHT** statt *nicht entscheidbar*; die Folge ist praktisch dieselbe. Die Zahlen unten sind der Stand vor der Korrektur.

`ein_messung.py` → `.txt` (2 min, Kurse bis 20.09.2026). Gegenprobe `ein_messung_gegenprobe.py` **11/11**: Anzahlen, alle 186 E-b-Anker mit einer zweiten Umsetzung der Marke, Korb neu gemittelt, Erwartung der Zufallswelt analytisch, Kostenformel, Tor an 80 Stichtagen, X0.

**Teil 0 (R-R11):** B5 X2 mit dem alten Werkzeug `wl_messung.b5` genau reproduziert: E2 **+31,8 %**, E3 **−4,0 %**. Die Marke dieser Messung liefert an **4.001 von 4.001** B5-Käufen denselben Ausstiegstag wie `a2_messung.ausstieg('X2')`.

**Haupt-Hypothese E-b** (Eintritt ins Fünftel bei Altseason-Breite ≥ 50 %, Ausstieg X2, gegen BTC):

| | E2 (Wahl) | E3 (Bestätigung) |
|---|---|---|
| Einstiege / Stichtage | 143 / 11 | **28 / 3** (01.02.2024, 01.03.2024, 01.12.2024) |
| Korb gegen BTC (Median der Körbe) | +21,7 % (+3,0 %) | **−28,6 %** (−31,1 %) |
| Anteil > BTC | 43 % | **0 %** |
| Bootstrap · Rang gegen Zufallswelt | 0,87 · **0,66** | 0,00 · 0,03 |
| Zufallswelt-Erwartung (H4) | +20,4 % | −17,8 % |
| netto (Coin 1,25 %, BTC 0,4 % je Seite wie B5) | +19,7 % | −29,8 % |
| X0 (12 Monate halten) statt X2 | −5,5 % | −54,3 % |

⇒ **URTEIL nach Plan: NICHT ENTSCHEIDBAR** — Bedingung (3) fehlt (3 Stichtage statt ≥ 4).

**Was die Zahlen beschreiben (kein Test, nur Beschreibung):**
1. **In E3 schlug kein einziger E-b-Einstieg BTC.** Alle 28 lagen in den drei kurzen Öffnungen 2024 und waren schlechter als zufällige Coins derselben Klasse an denselben Tagen (−28,6 % gegen −17,8 %).
2. **In E2 kommt der Vorteil aus dem ZEITPUNKT, nicht aus der Auswahl:**
   - Zufällige Coins der Klasse an denselben offenen Tagen erreichen +20,4 %, E-b +21,7 % (Rang 0,66).
   - Die Phase wirkt, die Watchlist-Auswahl innerhalb der Phase bringt nichts Messbares.
3. **Getragen von 2021:**
   - 2021: +38,3 % (116 Einstiege); 2022: −14,2 %; Jänner 2024: −39,0 %.
   - Ohne die 5 größten Gewinner (ANKR, DOGE, NKN, DENT, CTXC) bleiben +6,4 %.
4. **Die Führung trägt wieder den größten Teil:** X2 statt Halten bringt bei E-b +27 Pp (E2) und +26 Pp (E3), wie in B5.
5. Die anderen Arme liegen in E3 alle unter BTC (KL −17,5 %, A0 −12,5 %, E-a −10,7 %, E-c −14,0 %). Eintritt (E-a) und Relativstärke (E-c) bringen gegenüber A0 auch in E2 nichts.

**Selbsttest:**
- (b) gepflanzt: **erkannt**.
- (a) Zufalls-Tor: **Fehlalarm 22 %**, also NICHT bestanden. Ursache (Gegenprobe H7): Bei 3 Stichtagen und Blöcken zu 3 ist jede Bootstrap-Ziehung die volle Reihe, der Bootstrap kann dann nur 0 oder 1 sein.
- ⇒ Die Anlage gilt bei dieser Fallzahl nicht. Das stützt das Urteil „nicht entscheidbar“, statt es zu schwächen.

Abweichung vom Plan, offen ausgewiesen: Netto wurde mit den B5-Kosten gerechnet (Coin 1,25 %, BTC 0,4 % je Seite) statt mit pauschal 1 %. Es ist nur Auskunft und ändert kein Urteil.

### 29.5 Eichung der Prüfanlage — Mindestzahl Stichtage (nachträglich, kein Ergebnis zu E-b)

`ein_selbsttest_stichtage.py` → `.txt`. Gemessen wird der Fehlalarm des Zufalls-Tors (Bedingungen 1+2) nach der Zahl offener Stichtage, 100 Welten je Zeile:

| offene Stichtage | 3 | 4 | 6 | 8 | 12 | 16 |
|---|---|---|---|---|---|---|
| E2 | 4 % | 4 % | 1 % | 1 % | 0 % | 0 % |
| E3 | **17 %** | **7 %** | 2 % | 0 % | 0 % | 0 % |

⇒ **Die Anlage hält ihr Soll (≤ 5 %) erst ab 6 offenen Stichtagen.** Das vorab gesetzte Kriterium (3) mit ≥ 4 Stichtagen war zu locker; hier hätte es nicht gegriffen, weil E3 nur 3 hatte.

**Korrektur für alles Folgende** (Vorwärtsprotokoll, Teil B): **mindestens 20 Einstiege an mindestens 6 offenen Stichtagen.** Das ersetzt *„sobald 20 neue Fälle da sind“* in §29.3.

⚠️ **Was das zeitlich heißt:** Die Phase war in E2 an 30 %, in E3 an 15 % der Monate offen. Sechs offene Stichtage dauern im Mittel **1½ bis 3 Jahre**. Kommt die Altseason wirklich, sind sie in wenigen Monaten erreicht, weil die Öffnungen zusammenhängen (2021).

### 29.6 Zwischenfazit zum Ziel und Folge (Folge vorab §29.3: „nicht entscheidbar“)

| Frage | Antwort |
|---|---|
| Gibt es eine belegte Einstiegsregel je Coin, die BTC schlägt? | **Nein.** Nicht entscheidbar; was beschrieben wird, spricht in E3 eher **dagegen** |
| Was wirkt? | Die **Phase** (Zeitpunkt) und die **Führung** (X2). Die Auswahl innerhalb der Phase wirkt nicht messbar |
| Was folgt (vorab festgelegt)? | Die Monatsmail bekommt den Abschnitt **„Einstiegskandidaten“**: die Phase als **Fakt** (offen/zu, Breite in %) und die Eintritte ins Fünftel. Jeder E-b-Eintritt wird **vorwärts protokolliert**, Prüfung bei ≥ 20 Einstiegen an ≥ 6 offenen Stichtagen (§29.5) |
| Was folgt **nicht**? | Kein Einstiegssignal je Coin, keine Ereignis-Mail „Kauf“, keine Größe |
| Was gewinnt das Ziel? | Die ehrliche Grenze: **Mit den vorhandenen Daten ist ein Altcoin-Einstieg gegen BTC nicht belegbar.** Der greifbare Hebel im Spot ist die **Führung je Bestand** (B5, hier wieder +26 Pp in E3), und die Phase als Fakt in der Mail |

⚠️ **Der Zufallswelt-Befund ist neu und wichtig für O28:** Bei offener Phase brachte ein *beliebiger* Coin der Klasse gleich viel wie die Watchlist-Auswahl. Die Rangliste ist damit keine **Kauf**-Auswahl, sondern bleibt, was §25.6 gemessen hat: die Ordnung **innerhalb** der Klasse über alle Stichtage (Fortbestand, Gelegenheit).

### 29.7 Teil B — Führung und Ausstieg JE BESTAND (Nutzer 08.10.2026, eingeplant, Messplan folgt)

Nutzer 08.10.: *„Der optimale Einstieg je Asset ist nur ein Teil des Paketes. Analog Hebel brauchen wir je Bestand eine Führung bzw. optimalen Ausstieg. Wie du richtig angemerkt hast, sind diese Anstiege meist nicht dauerhaft.“*

**Bestehendes Schema (nicht neu erfinden):**
- S-B *Bestand und Ausstieg* (§2);
- M-5 in der Reihenfolge S-c;
- O14 Spot-Positionsführung und O19 Stop-Nachzieh-Sammelmail (Plan);
- `Bestandsaufnahme_Positionsfuehrung_26_08.md` (holdings tragen weder Stop noch These);
- B5 §21.6 (X0/X1/X2/X7).

Teil B **ersetzt** den Altbestand der Trailing-Regel vom 04.08. (+1,0 R / 1,0 R).

**Was schon gemessen ist:**

| | |
|---|---|
| X2 (Nachlauf −35 % / Notbremse −50 %) | E3-Korb −4 % statt −42 %, kein Absturz ≤ −70 % mehr; E2 Bootstrap 0,81 → *knapp nein* (§21.6) |
| hier bei E-b | +27 Pp (E2) / +26 Pp (E3) gegen Halten |
| Ausstieg | 98–100 % über die Marke, Median 38–68 T (§29.1) — Anstiege halten selten |
| X1 gestaffelt | E3 +42 Pp gegen Halten, E2 schwächer als Halten |

**Fragen für den Messplan** (Voranalyse vor dem Plan, dann Nutzer-Ja):

| # | Frage | warum |
|---|---|---|
| B-1 | **Bezugspunkt für Bestände, die nicht über das System gekauft wurden:** Kaufdatum und Einstand aus dem Bestand (Importer), Hoch seit Kauf aus den Kursen in Prod | Der Bestand ist älter als jede Regel. *Hoch seit Kauf* gilt dort ab dem echten Kauf, nicht ab heute |
| B-2 | **Nachlaufweite gemessen statt gesetzt:** Dosis-Wirkung über mehrere Weiten, je Klasse H/M/S oder in Schwankungseinheiten; Regel vorab | −35 % stammt aus dem ersten Wurf. Eine Smallcap schwankt anders als LINK |
| B-3 | **Zielgröße zweifach:** gegen **Halten** (schützt die Führung?) und gegen **BTC** (lohnt der Bestand überhaupt?) | Die Führung kann gegen Halten tragen und gegen BTC trotzdem verlieren (§29.4) |
| B-4 | **Teilverkauf** (X1) gegen ganz | E3 stark, E2 schwach: zweiseitig planen (Regel *Messplan zweiseitig*) |
| B-5 | **Phase zu** als Ausstiegsgrund (Breite fällt unter 50 %) | Es wirkt die Phase, nicht die Auswahl (§29.4) |
| B-6 | **Wohin nach dem Ausstieg?** Bargeld oder Kern | Sonst ist der Ausstieg ein Verlust gegen BTC im Aufschwung |
| B-7 | ⚠️ **Widerspruch zur Altregel *Spot hat keinen Stop*** (`verkaufsrechnung.py:27`) | X2 ist ein Nachlauf-Stop. Die Messung entscheidet; die Altregel wird abgelöst oder bestätigt, nicht stillschweigend übergangen |
| B-8 | **Datenquellen-Inventar und Abdeckung am NB** je Bestand (auch außerhalb Binance: KAS, MORPHO, BRETT, SUPRA, MON, CANTON, ASTER) | Regel *vor jedem Bau Abdeckung am NB nachweisen* |
| B-9 | **Mail:** *Marke gerissen* je Bestand als Ereignis-Mail, mit dem **gemessenen** Effekt als Begründung | Regel 4: Der Bruch der Marke ist ein Fakt. Begründung ist erst die Messung, dass Führen besser ist als Halten |

**Reihenfolge:** Voranalyse B-1 bis B-9 (Datenlage, Altregel, Bestand am NB) → Messplan vorab → Messung am Desktop → Zwischenfazit → Bau erst nach Abstimmung (T-2: nach der Hebel-Freigabe).


## 30. Situationsbewertung 2024 bis heute, Datenkorrekturen und Voranalyse Teil B (08.10.2026)

Nutzer 08.10.:
- *„Davor müssen wir die Situation bewerten. Der Markt 2021 als Maßstab war schon immer problematisch – eigentlich muss das System an die aktuellen Gegebenheiten 2024 bis heute angepasst werden, wir haben nur diese Daten.“*
- *„Der gesamte Altcoinmarkt ist in einem Abstiegstrend. Zwischen den BTC-Anstiegen können einige Altcoins auch ausbrechen. Unabhängig davon ist die Annahme weiterhin, dass in bzw. vor positiven Phasen der Altcoins eine Altseason erforderlich ist, wobei nicht alles steigen wird, sondern wir unsere Diamanten identifizieren müssen.“*
- *„Sauber auf Fehler oder Optimierung prüfen und gegenprüfen – das Thema ist komplex aufgrund der Rahmenbedingungen und der zeitlichen Faktoren.“*

⚠️ **Selbstkorrektur:** Die Regel *Messfokus ab 2023/2024* (Urteil ab 2024, Training ab 2023, Älteres nur Auskunft) gilt seit 29.09. Der Spot-Strang hat sie verletzt:
- E2 (2021 bis Jänner 2024) war die **Wahl**-Epoche für die Watchlist-Kombination (§25), für B5 (§21.6) und für O31 (§29).
- Getestet wurde zwar auf E3, gewählt aber auf dem Markt von 2021.
- Ab hier gilt die Regel auch im Spot (§30.6).

### 30.1 Prüfung auf Fehler — fünf Funde, alle behoben und in ihrer Wirkung gemessen

| # | Fund | Wirkung (gemessen) | Behebung |
|---|---|---|---|
| 1 | **Bündelfaktor fehlte** in `mk_messung.umlauf` (Befund 2.501-buendelpaare: 1000SATS, 1MBABYDOGE, 1000CHEEMS, 1000CAT handeln Bündel, die Quellen führen Einzeltoken) → Marktwert bis 10⁶ zu hoch, 1MBABYDOGE ab 2025 auf Rang 1 | E1/E2 unberührt (erst ab 2024 gelistet); E3 **1,4 %** der Klassen; Breite am 01.09.2025 0,46 → 0,50 (Tor geht auf) | Stufe 2: Menge / `hole_umlaufmenge_cg.vervielfacher` (eine Stelle, aus dem Namen) — `mk_buendel_wirkung.py` |
| 2 | **CoinMetrics-Ausreißer:** XVG ×100, KNC ×0,054, GNO ×3,8 gegen CoinGecko (XVG mit 11 Mrd Marktwert unter den Top 15) | mit Fund 3 zusammen: E2 **0,36 %**, E3 **1,9 %** der Klassen | Stufe 3: CoinMetrics nur, wenn letzter Wert / CoinGecko heute in [1/3, 3] — `mk_umlauf_pruefung.py` U1 |
| 3 | **Umlauf von HEUTE** für die Vergangenheit (342 von 384 Coins am 01.06.2025) — ein Vorgriff: Coins mit späterer Ausgabe neuer Token stehen historisch zu hoch | ab 10/2025 mit echter Historie gemessen: **3,5 %** der Klassen, Breite Juni 2026 0,46 → 0,50; für 2024 größer (U3: Umlauf wächst im Median +4,6 %/Jahr, 14 % der Coins > +50 %) | Stufe 3: CoinGecko-Historie zu t (`umlaufmenge_cg.db`, ab 21.09.2025) vor allem anderen. ⚠️ **Vor 21.09.2025 bleibt der Vorgriff** — keine freie ältere Historie |
| 4 | Lagebild L5: Führung über 365 T, Hoch über 180 T (verschiedene Fenster) | Anteil „gehalten“ verzerrt | vor der Auswertung angeglichen (180 T beide) |
| 5 | Lagebild L1 endete im März 2026 (180-T-Fenster der Ausbrüche mitbenutzt) | die letzten 5 Monate fehlten | L1 bis 08/2026 (30-T-Fenster genügt) |

**Wirkung auf registrierte Ergebnisse** (alles neu gerechnet, Gegenproben 52/52, 11/11, 55/55):

| | vorher | nach Stufe 3 | |
|---|---|---|---|
| Watchlist §25.6 E3 (oberes Fünftel, Saldo, Rang) | +14,4 Pp, 1,000 | **+13,9 Pp, 1,000**; Dosis −16,4 / −6,3 / +3,4 / +4,9 / +13,9; 2024 +20,4, 2025 +5,9 | **robust** |
| Breite offen in E3 | 15 % der Stichtage | **20 %** | |
| O31 E-b in E3 | 28 an 3 Stichtagen, −28,6 %, *nicht entscheidbar* | **34 an 4 Stichtagen, −23,9 %, 3 % > BTC, Zufallsrang 0,29 → TRÄGT NICHT** | §30.3 |
| Eichung (Fehlalarm bei k Stichtagen, E3) | 17 / 7 / 2 % bei 3 / 4 / 6 | **29 / 11 / 0 %** | Mindestzahl **6** bleibt |

### 30.2 Lagebild 2023 bis heute (`lage_e3.py` → `.txt`, Gegenprobe `lage_e3_gegenprobe.py` **55/55**) — reine Beschreibung

Grundgesamtheit wie die Watchlist (Marktwert-Klassen, eingestellte Coins eingeschlossen, ohne die Kernwerte BTC, ETH, SOL). 2023 ist Trainingsjahr, Urteil ab 2024.

**L1 Markt** (Top 100 nach Marktwert, 30-T-Ertrag gegen BTC je Monat, verkettet):

| Halbjahr | BTC | Breite offen | Altindex gleichgewichtet | marktwertgewichtet |
|---|---|---|---|---|
| 2023-H1 | +72 % | 0 von 6 | −36 % | −36 % |
| 2023-H2 | +34 % | 0 von 6 | +11 % | +9 % |
| 2024-H1 | +43 % | 3 von 6 | −39 % | −35 % |
| 2024-H2 | +53 % | 1 von 6 | −11 % | +21 % |
| 2025-H1 | +9 % | 0 von 6 | −59 % | −35 % |
| 2025-H2 | −16 % | 2 von 6 | −22 % | +10 % |
| 2026-H1 | −26 % | 1 von 6 | −15 % | −11 % |
| 2026 Jul–Aug | +31 % | 0 von 2 | −13 % | −5 % |
| **ab 2024** | **+94 %** | **7 von 32** | **−87 %** | **−52 %** |

Dazu ETH/BTC −41 %, SOL/BTC −47 % (Kern, Auskunft).

**L2 Ausbrüche** („Diamant“ = Coin verdoppelt sich **gegen BTC** binnen 180 T):

| | 2023 (Training) | ab 2024 |
|---|---|---|
| Quote je Coin und Monat | 13,9 % | **8,1 %** (H 6,6 · M 6,6 · S 8,8 %) |
| verschiedene Coins | 156 | **238** |
| Hoch erreicht nach (Median) | 113 T | **85 T** |
| nach 180 T noch ≥ ×2 | 19–30 % | **14–20 %** |
| Rückgabe vom Hoch (Median) | 41–57 % | **55–62 %** |
| junge Coins (< 1 Jahr Kurs) | | Quote 10,1 % gegen 7,8 %; 20 % der Ausbrecher |

Größte seit 2024: DEXE und ZEC ×24, TUT ×21, SYN ×15, BNX ×13, PEPE ×11, OM ×11.

**L3 Lage am Stichtag → Ausbruchsquote ab 2024:**

| | Stichtage | Quote | Median Ende gegen BTC |
|---|---|---|---|
| BTC 90 T fällt, Breite zu | 10 | 9,3 % | −32 % |
| BTC 90 T steigt, Breite offen | 6 | 8,2 % | **−50 %** |
| BTC 90 T steigt, Breite zu | 11 | 7,1 % | −44 % |
| Rückschau: BTC im Fenster < −10 % / ±10 % / > +10 % | 9 / 3 / 15 | 8,6 / 5,1 / 8,4 % | |

**L4 Waren die Ausbrecher vorab in der Watchlist?**

| | Quote im Fünftel | außerhalb | Lift |
|---|---|---|---|
| 2023 | 9,6 % | 15,0 % | 0,64 |
| **ab 2024** | 8,1 % | 8,2 % | **0,99** (H 9,2/5,8 · M 8,8/6,1 · S 7,7/9,0) |

⚠️ **Kein Widerspruch zu §25.6.** Die Watchlist wurde auf *absolute* Verdopplung binnen 365 T gegen *Absturz* gemessen (Saldo R2 − L). Hier geht es um *Verdopplung gegen BTC* binnen 180 T. Die Watchlist ordnet **Fortbestand** (weniger Absturz), nicht **Ausbruch**.

**L5 Was hält die Führung X2 (180 T, gegen BTC)?**

| ab 2024 | n | X2 Median / Mittel | > BTC | Halten 180 T Median / Mittel | Vielfaches vom Hoch gehalten |
|---|---|---|---|---|---|
| Ausbrecher | 828 | **+39 % / +58 %** | 73 % | +7 % / +44 % | 0,57 |
| übrige | 9.333 | −25 % / −22 % | 10 % | −43 % / −41 % | 0,65 |
| **alle** | 10.161 | **−24 % / −16 %** | **15 %** | −41 % / −34 % | 0,64 |

### 30.3 O31 nach der Korrektur — formales Urteil und Bewertung

- **Vorab-Regel §29.2:** ≥ 20 Einstiege an ≥ 4 Stichtagen sind jetzt erfüllt (34 an 4). Korb −23,9 % gegen BTC, Bootstrap 0,00 → **TRÄGT NICHT**.
- **Eichung §29.5:** Bei 4 Stichtagen liegt der Fehlalarm bei 11 %. Das schwächt nur ein *positives* Urteil. Ein negatives an 4 Stichtagen hat wenig Trennschärfe; einen kleinen echten Vorteil könnte es übersehen.
- **Bewertung:** *Nicht bestätigt, und in allem Beschriebenen negativ* (E3 3 % > BTC, in E2 nur Zeitpunkt statt Auswahl, 2021 trägt alles).
- **Folge:** Die Folgen „trägt nicht“ und „nicht entscheidbar“ (§29.3) fallen praktisch zusammen: **kein Kaufsignal**, Phase als Fakt in der Mail, Vorwärtsprotokoll bis ≥ 20 Einstiege an ≥ 6 offenen Stichtagen.

### 30.4 Bewertung der Annahmen des Nutzers gegen die Daten 2024 bis heute

| Annahme | Daten ab 2024 | Bewertung |
|---|---|---|
| Der Altcoin-Markt ist im **Abstiegstrend** | Altindex gegen BTC −87 % gleichgewichtet, −52 % marktwertgewichtet; ETH −41 %, SOL −47 % | **bestätigt — stärker als gedacht**, bei Smallcaps am stärksten |
| Zwischen BTC-Anstiegen **brechen einige aus** | 8,1 % je Coin und Monat, 238 Coins | **bestätigt** — aber **unabhängig von der BTC-Lage** (7–9 % in jeder Lage), und **selten dauerhaft** (nach 180 T noch 14–20 %, Rückgabe 55–62 %) |
| Es braucht eine **positive Phase / Altseason** | Breite nur an 7 von 32 Stichtagen offen, immer kurz; Käufe bei offener Phase endeten **schlechter** (−50 %) | **mit unseren Daten nicht prüfbar**: Seit 2024 gab es keine Altseason. Die Annahme ist weder belegt noch widerlegt; die kurzen Öffnungen waren Strohfeuer |
| Wir müssen die **Diamanten identifizieren** | Watchlist Lift 0,99; Lage, Phase, Eintritt, Relativstärke trennen nicht | **offen — bisher ohne Werkzeug.** Was wir haben, ordnet Fortbestand, nicht Ausbruch |
| (ergänzt) Die **Führung** hilft | Ausbrecher +39 % statt +7 % (Median), alle −24 % statt −41 % | **bestätigt** — sie halbiert den Verlust. Gegen BTC bleibt ein Altcoin-Kauf ohne Erkennung trotzdem im Minus (15 % > BTC) |

⇒ **Das Gesamtbild 2024 bis heute:**
- Ein Altcoin-Kauf schlägt BTC nur, wenn man einen **Ausbrecher** erwischt (8 % je Monat) **und** ihn führt.
- Die Führung haben wir, gemessen.
- Die Erkennung haben wir nicht.
- Ohne Erkennung bleibt der Erwartungswert gegen BTC klar negativ, mit Führung halb so schlimm.

### 30.5 Zeitliche Faktoren — was die Fenster an Daten kosten

| Fenster | letzter auswertbarer Stichtag | Monate ab 2024 |
|---|---|---|
| 30 T (Markt) | 08/2026 | 32 |
| 180 T (Ausbruch, Führung) | 03/2026 | 27 |
| 365 T (§25, O31) | 09/2025 | 21 |

⇒ Je länger das Fenster, desto weniger der ohnehin knappen Jahre 2024+.
- **Teil B misst deshalb mit höchstens 180 T.** Die Haltedauer bei Ausstieg über die Marke liegt im Median bei 34–85 T, das passt.
- **Anker täglich statt monatlich**, gebündelt nach Monat für den Bootstrap. Damit kommen mehr Fälle zusammen, ohne die Abhängigkeit zu verstecken.
- **Neue Monate sind der einzige Weg zu mehr Fallzahl.** Jede Regel geht ab Bau ins Vorwärtsprotokoll.

### 30.6 Methodische Folgen für den Spot-Strang (ab sofort)

| | bisher | ab jetzt |
|---|---|---|
| Wahl einer Regel / Schwelle | E2 (2021–01/2024) | **2023** (Training) |
| Urteil | E3 | **ab 2024** — und weil diese Jahre schon beschrieben sind: neue Hypothesen auf 2024+ nur als **Beschreibung**, Test **vorwärts** (Regel *Hypothesen nicht starr*) |
| 2021/2022 | Wahl-Epoche | nur Auskunft, gekennzeichnet |
| Watchlist-Kombination | auf E2 gewählt | **bleibt**, denn ihr E3-Test ist echt außerhalb der Wahl und hält nach Korrektur (+13,9 Pp). Eine Neuwahl auf 2023 wäre Fassung n+1 und bräuchte Vorwärtsdaten |
| Umlauf | heute | Stufe 3 (Historie, Riegel); der Vorgriff vor 21.09.2025 steht als **Grenze** in jedem Ergebnis |

### 30.7 Voranalyse Teil B — Führung und Ausstieg je Bestand (Fragen aus §29.7, mit Ist-Stand)

**Bestand am NB** (Diagnose 08.10. 08:31):
- **46** Positionen mit Menge, **44** mit Einstand (`holdings.avg_buy_price_eur`, gleitender Durchschnitt aus den Bitpanda-Käufen), **24** in der Binance-Kursbasis.
- Außerhalb liegen vor allem Aktien und ETFs (3QSS, CEBS, OD7…, nicht Teil des Krypto-Spots) und EURCV (Stablecoin).
- An Krypto liegen außerhalb ASTER, CANTON, CT, MON, XDC; BW, ROL, VSN und VST sind zu klären. Kurse dazu in Prod (`price_history_ohlc`), am NB nachzuweisen (B-8).

| # | Frage | Ist-Stand (geprüft 08.10.) | für den Messplan |
|---|---|---|---|
| B-1 | Bezugspunkt *Hoch seit Kauf* | **Kein Kaufdatum abgelegt.** `holdings` trägt nur Menge und Einstand. Die Buchungen liest `importer/bitpanda_bestand.py` bei jedem Abgleich über die Schnittstelle, legt sie aber nicht ab. Der Export vom 03.08. hat **3.463 Käufe mit Datum und Preis** (89 Coins, ab 13.09.2024) | Messung braucht es nicht (Marktdaten). **Betrieb braucht eine Kaufablage am NB** (kostenfrei, eigene Schnittstelle) |
| B-2 | Nachlaufweite gemessen | X2 (−35 % / −50 %) stammt aus dem ersten Wurf, gewählt auf E2 | Dosis-Wirkung über mehrere Weiten, zusätzlich in Schwankungseinheiten; **Wahl auf 2023, Urteil ab 2024**, Regel vorab, zweiseitig |
| B-3 | Zielgröße | L5: Führung schlägt Halten deutlich, gegen BTC bleibt sie negativ | **drei** Bezüge ausweisen: gegen Halten (schützt die Führung?), gegen BTC (lohnt der Altcoin?), gegen Bargeld (absolut) |
| B-4 | Teilverkauf | X1 in E3 stark, in E2 schwach | Variante im selben Plan, zweiseitig |
| B-5 | *Phase zu* als Ausstieg | Die Phase war seit 2024 nur an 7 von 32 Stichtagen offen | nur Auskunft. Als Regel greift sie zu selten |
| B-6 | Wohin nach dem Ausstieg | — | Bargeld oder BTC; beides ausweisen |
| B-7 | Altregel *Spot hat keinen Stop* | `agent/verkaufsrechnung.py`: *beim Spot ist die Positionsgröße die einzige Risikosteuerung* (Nutzerangabe 14.08.). Der `ausstiegs_job` zieht Stops **je Signal** nach (O19); `agent/positionsfuehrung.py` beschreibt **eine Position je Symbol** (27.08.) | Die Messung entscheidet. Der Bau setzt auf `positionsfuehrung` auf, nicht auf den Signalweg |
| B-8 | Abdeckung am NB | 24 von ~30 Krypto-Beständen in der Binance-Kursbasis; die übrigen in Prod | vor dem Bau am NB nachweisen (Teilexport) |
| B-9 | Mail | — | *Marke gerissen* je Bestand, Begründung = gemessener Effekt |
| **B-10** (neu) | **Einstieg in die Führung mitten in einer Position** | Viele Bestände liegen tief unter Einstand. Mit *Hoch seit Kauf* wäre die Marke bei vielen **schon gerissen**, sobald die Führung startet | Der Messplan muss den echten Fall messen: Führung **beginnt an einem beliebigen Tag** einer laufenden Position, nicht nur am Kauftag. Er braucht eine Regel für den Start (z. B. *Hoch ab Start* gegen *Hoch seit Kauf*) |
| **B-11** (neu) | **Zeitfenster** | §30.5 | höchstens 180 T, Anker täglich, Bootstrap nach Monat, 2023 Wahl / ab 2024 Urteil |

### 30.8 Zwischenfazit zum Ziel

| | |
|---|---|
| **Ziel** | Spot: Einstieg je Asset und Führung je Bestand, gemessen gegen BTC |
| **Stand** | Einstieg: *nicht belegt* (O31). Führung: *wirkt deutlich* (L5, B5). Erkennung der Diamanten: *kein Werkzeug* (L4) |
| **Test oder Betrieb** | alles Desktop, nur lesend; nichts am NB geändert |
| **Was folgt** | Teil B Messplan (B-1 bis B-11) zur Abstimmung. Die Erkennung von Ausbrüchen ist eine **eigene** Frage (Teil C), siehe die Punkte zur Abstimmung |
| **Was nicht folgt** | kein Kaufsignal; keine Aussage, dass eine Altseason kommt oder nicht kommt |
