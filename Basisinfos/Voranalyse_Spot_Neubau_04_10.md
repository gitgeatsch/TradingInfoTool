# Voranalyse Spot-Neubau — die Grundlage aus fachlicher und technischer Sicht

**04.10.2026** · E-54, Plan Hebel **O23** (dazu O14, O19, O24) · Nutzer: *„Ich würde gerne den Spot-Ast neu umbauen, analog dem Hebelablauf“* — *„vorerst nur eine Voranalyse und Analyse, damit wir die Grundlage aus fachlicher und technischer Sicht haben“*.

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
