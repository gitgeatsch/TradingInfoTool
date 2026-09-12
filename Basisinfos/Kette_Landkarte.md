# Die Landkarte der Kette — was rechnet, was urteilt, und wo

*Erstellt 12.09.2026 auf Nutzerfrage: „zeige mir den vollständigen Ablauf der
Kette — was wird wo deterministisch berechnet, wie und wo bewerten die
LLM1-Rollen, und wo ist die Gegenprüfung von LLM2 (Z.ai)?"*

⚠️ **Aus dem Code gelesen, nicht aus der Erinnerung.** Die Stufennamen stammen
aus `agent/rollen_gate.py::STUFEN`, die Aufrufstellen aus `agent/rollen_lauf.py`.

---

## Der Ablauf, Stufe für Stufe

Ein Umlauf läuft alle 15 Minuten über fünf Gruppen. Je Gruppe **einmal** Rolle A,
dann je Asset die zwölf Stufen.

| # | Stufe | Wer entscheidet | Kostet einen Modellaufruf? |
|---|---|---|---|
| — | **Rolle A — Marktlage** | **LLM1** | ja, **einmal je Umlauf** |
| 1 | `auftrag` — Instrument und Strategie erlaubt | Rechnung | nein |
| 2 | `fakten` — Faktenlage ausreichend | Rechnung | nein |
| 3 | `lagebild` — Lagebild geliefert | Rechnung (prüft Rolle A) | nein |
| 4 | `anlass` — Faktensatz hat sich geändert | Rechnung | nein |
| 5 | `auswahl` — gehört zu den besten k der Gruppe | Rechnung | nein |
| 6 | `terminmarkt` — OI-Aufbau nicht im obersten Fünftel | Rechnung | nein |
| 7 | `wiederholung` — nicht kürzlich schon gefragt | Rechnung | nein |
| 8 | `urteil` — **Urteil geliefert und vertragskonform** | **LLM1 (Rolle BC)** | **ja, je Asset** |
| 9 | `aktion` — Aktion ist ein Einstieg | Rechnung | nein |
| 10 | `geometrie` — Zonen rechenbar | Rechnung | nein |
| 11 | `risikoschicht` — Töpfe, Cash, Positionsgröße | Rechnung | nein |
| 12 | `entscheider` — Trefferquote schlägt den Breakeven | **Rechnung** | nein |
| — | **Rolle G — Gegenprüfung** | **LLM2 (Z.ai)** | ja, nebenläufig |

**Sieben Stufen liegen vor dem Modell, und das ist Absicht:** Jede von ihnen hat
eine eigene Stufe bekommen, weil sie **keinen Modellaufruf kostet** — `anlass`
(16.08.), `auswahl` (23.08.), `terminmarkt` (02.09.). Wer sie zusammenlegt, kann
hinterher nicht mehr sagen, ob eine Zeitregel, ein identischer Faktensatz oder
ein Rangplatz gebremst hat.

⚠️ **Namensfalle:** Wer im Projekt „Stufe 11" liest, meint den `entscheider` —
das ist seit dem Einschub von `terminmarkt` die zwölfte. Im Code wird deshalb
nur mit Namen gearbeitet, nie mit Nummern.

---

## ⚠️ Der „Entscheider" ist keine LLM-Rolle

Der ursprüngliche Entwurf trennte **Händler** (bewerten) und **Entscheider**
(handeln) als zwei Modellaufrufe. Das ergab rund 162 Aufrufe täglich. Nach dem
Nutzereinwand vom 10.08. wurden beide **in einen Aufruf gelegt** — das ist heute
Rolle BC.

Die Stufe, die heute `entscheider` heißt, ist **deterministisch**: Sie fragt, ob
die gerechnete Trefferquote die Bewertungsschwelle schlägt (`potential.traegt()`,
Schwelle 0,080 R). Kein Modell ist daran beteiligt.

| Begriff | Was heute dahintersteckt |
|---|---|
| Rolle **Markt** | LLM1, Rolle A — einmal je Umlauf, sieht kein einzelnes Asset |
| Rolle **Händler** | LLM1, Rolle BC — Belege, Aktion, Begründung, Gegenargument |
| Rolle **Entscheider** | **kein Modell mehr** — in Rolle BC aufgegangen; die gleichnamige *Stufe* ist gerechnet |
| Rolle **G** | LLM2 (Z.ai) — zweite Quelle, kein Veto |

---

## Was das Modell entscheidet — und was gerechnet wird

**Vom Modell (Rolle BC):** Aktion · Richtung · Begründung · Gegenargument ·
Belege mit Richtung und Gewicht · Zahl unabhängiger Faktoren · Widerlegung
(wodurch, welcher Preis, bis wann) · Einstieg und Stop als **Angabe**.

**Gerechnet, nie vom Modell:** Betrag (aus der Zahl unabhängiger Faktoren,
gedeckelt) · Hebel (`r(q)`, halbes Kelly) · Ziel (CRV 2,0 mechanisch) ·
Stopweite (Rauschboden und Marken) · Trefferquote (gemessene Beiträge) ·
Aggregat-Deckel · Cash und Töpfe · Liquidationsabstand.

**Bewusst nie eingebaut** — jeweils mit Grund:

- **keine Konfidenz in Prozent** — im eigenen System 77,5 % vorhergesagt gegen
  33,3 % eingetreten. Stattdessen die Zahl **unabhängiger Belege**.
- **keine Rechnung durch das Modell** — Tokenisierung zerlegt Zahlen.
- **keine Positionsgröße** — Rolle A durfte das bis 10.08.; Beträge setzt der
  Nutzer, das Risikomanagement ist deterministisch.
- **keine „unklar"-Option.**
- **zwei Z.ai-Aufrufe stillgelegt** — Richtungsabgleich (17× LONG in 2.469
  Prüfungen, dieselben Fakten wie Rolle BC) und Konsistenzprüfung (16.08. vom
  Nutzer abgelehnt).

⚠️ Deshalb stehen in der Oberfläche „Konfidenz –" und „Trigger (-)" leer: Das
sind Felder der alten Kette (Befund 2.390-gui).

---

## Die Gegenprüfung (LLM2, Z.ai)

Sie läuft **nebenläufig in einem eigenen Faden**, nach dem Urteil, mit
**eigenen Fakten**: der Positionierung am Terminmarkt — offene Kontrakte,
Finanzierungsrate als Perzentil, Anteil der Long-Konten, Marktregime mit Dauer.
Nichts davon steht im Faktentext von Rolle BC.

**Sie hat kein Veto.** Ihr Einwand erscheint in der Mail (Abschnitt 5,
„DIE GEGENPRÜFUNG") und im Kopf unter „Was dagegen spricht" — er verändert
weder Aktion noch Betrag noch Hebel. Fällt sie aus, läuft die Kette weiter
(P-8, fail-soft); im Log steht dann „Z.ai-Rolle G fehlgeschlagen".

**Sie wird nur gefragt, wo es eine eigene Grundlage gibt** (G5): Zu einem Wert
ohne symbolspezifische Terminmarktdaten wird nicht gefragt.

---

## Die vier Wächter um das Modell — alle deterministisch

| Wächter | Was er prüft |
|---|---|
| `empfehlung_vertrag` | Pflichtfelder, Richtungspflicht, Ablehnung sich selbst zurückziehender Begründungen, Rückstufung auf NICHTS_TUN ohne unabhängigen Faktor |
| **Z1** `gegenpruefer_rollen` | **Treue zur Eingabe**: Zahlendeckung, Richtungstreue, Zuspitzung, Leerlauf. Fragt *nicht*, ob das Urteil klug ist |
| `mindestkriterien` | ohne ausreichende Grundlage wird gar nicht erst gefragt (BC3, G5) |
| `anlass` + `wiederholung` | wie oft überhaupt gefragt wird |

⚠️ **Z1 und Z.ai werden leicht verwechselt** — deshalb heißt das Modul
`zweite_meinung`: Z1 ist deterministisch und prüft die Treue, Z.ai ist ein
zweites Modell und prüft die Sache.

---

## ⚠️⚠️ Die Lücke: der Beitrag der Modelle ist unbelegt

Die Trefferquote in der Mail stammt aus **gemessenen Beiträgen**, nicht aus dem
Modell. Das Modellurteil steht **daneben** und geht in keine Zahl ein.

**Ob das Urteil der Modelle den Zufall schlägt, ist für diese Kette nie gemessen
worden.** Für die *alte* Kette gibt es `messe_allocator_gegen_zufall.py`. Für die
neue gibt es die Durchlässigkeit des Trichters (wo verliert die Kette) — aber
keine Aussage darüber, ob ein KAUFEN des Modells besser ausgeht als ein Zufall
auf derselben Menge.

Das ist die stehende Nutzervorgabe *„das LLM muss den Zufall schlagen, und das
muss messbar sein"* — offen, und Gegenstand von **Schritt 42**.

---

## Gemessen: wo die Kette wirklich verliert (7 Tage, 12.09.2026)

3.345 Läufe, 39.471 Asset-Zellen hinein, 202 heraus. Aus
`gate_durchlaessigkeit` der Notebook-Sicherung:

| Stufe | bestanden | verloren | wer entscheidet |
|---|---|---|---|
| auftrag | 39.471 | 0 | Rechnung |
| fakten | 38.802 | 669 | Rechnung |
| lagebild | 38.802 | **0** | Rechnung (Rolle A blockiert nichts) |
| anlass | 26.797 | 12.005 | Rechnung |
| auswahl | 16.242 | 10.555 | Rechnung |
| terminmarkt | 16.242 | 0 | Rechnung |
| wiederholung | 2.055 | 14.187 | Rechnung |
| **urteil** | 2.046 | **9** | Vertrag verwirft die Antwort (8× ungültig, 1× Netz) |
| **aktion** | 1.799 | **247** | davon **56 vom Modell** („NICHTS_TUN"), 166 „Ausstieg steht auf SCHLIESSEN", 25 „vollständig gestakt" |
| geometrie | 1.366 | 346 | Rechnung (taktische Zelle ohne Hebel) |
| risikoschicht | 1.366 | 0 | Rechnung |
| **entscheider** | **115** | **1.251** | **Rechnung** — Potential unter der Schwelle |

**Der härteste Filter ist gerechnet, nicht geurteilt:** Die Entscheiderstufe
verwirft **92 %** dessen, was sie erreicht. Das Modell verwirft 56 Zellen in
sieben Tagen — **2,7 %** der 2.046, die es beurteilt hat.

---

## ⚠️⚠️ Vorgabe und Ist: „Entscheidungshilfe, nichts blockieren oder ändern"

*Nutzerhinweis 12.09.2026.* Gemessen am heutigen Code gilt das **für zwei der
drei Stellen**:

| | blockiert? | ändert Zahlen? |
|---|---|---|
| **Rolle A (Markt)** | nein — 0 Verluste an `lagebild` | nein |
| **Z.ai (Gegenprüfung)** | nein — kein Veto, nur Text in der Mail | nein |
| **Rolle BC (Händler)** | **ja** — 56 Zellen in 7 Tagen über „NICHTS_TUN" | **ja** — siehe unten |

**Wo Rolle BC die Zahlen verändert:** Ihr **Widerlegungspreis** geht in die
Stopweite ein (`rechne(umgeworfen_preis_eur=…)`), und über den Stop hängen
Betrag, Hebel und Ziel daran. Die Mail sagt es selbst: *„Zone und Stop teils aus
einer Modellangabe."* In der SOL-Mail stammt der Stop 80,26 EUR aus dieser
Angabe — daraus folgen 8,9 % Stopabstand, 3,9x Hebel und 174 EUR Risiko.

➔ **Damit steht eine Entscheidung an** (Befund 2.391-hilfe): Soll das Modell
weiterhin eine Empfehlung verhindern dürfen, und soll seine Preisangabe die
Geometrie bestimmen? Beides ist heute so gebaut, beides widerspricht der
Vorgabe „Entscheidungshilfe".

---

# Die Stufen einzeln — und wer genau entscheidet

*Nutzervorgabe 12.09.2026: „gliedere mir die einzelnen Stufen so auf, dass ich
diese nachvollziehen kann — vor allem **‚Modell' ist nicht eindeutig**. Wenn es
sich um die LLM-Bewertung handelt, dann soll das angeführt sein; wenn es eine
deterministische Komponente ist, dann die korrekte Bezeichnung in der Kette."*

## ⚠️ Die Sprachregelung — ab hier verbindlich

Das Wort **„Modell"** ist im Projekt dreifach belegt und wird deshalb **nicht
mehr allein verwendet**:

| verboten | gemeint sein kann | ab jetzt zu schreiben |
|---|---|---|
| „das Modell" | das Sprachmodell im Urteil | **LLM-1 Rolle BC** |
| „das Modell" | das Sprachmodell für die Marktlage | **LLM-1 Rolle A** |
| „das Modell" | die Gegenprüfung bei Z.ai | **LLM-2 Rolle G** |
| „das Modell" | eine gerechnete Formel (z. B. Kelly) | **Rechnung**, plus Modulname |

**Die drei LLM-Stellen heißen künftig immer mit Rolle und Stufe.** Jede
deterministische Stelle wird mit ihrem **Modul** genannt — `agent/<datei>.py`,
notfalls `Modul.funktion()`. Ein Satz wie „das Modell verwirft" ist ohne diese
Angabe nicht überprüfbar, und genau daran ist diese Frage entstanden.

---

## Die zwölf Stufen, einzeln

Zahlen in der letzten Zeile jedes Blocks: gemessen über 7 Tage (39.471 Zellen
hinein, 202 heraus), aus `gate_durchlaessigkeit` der Notebook-Sicherung.

### Vor der Schleife — **LLM-1 Rolle A (Marktlage)**

| | |
|---|---|
| **Wer** | **Sprachmodell**, Rolle A |
| **Wo im Code** | `agent/rolle_analyst.py`, aufgerufen aus `agent/rollen_lauf.py` |
| **Wie oft** | **einmal je Umlauf und Gruppe** — nicht je Asset |
| **Was sie liefert** | ein Lagebild des Marktes: Regime, Rahmen, Text |
| **Was sie NICHT sieht** | kein einzelnes Asset, keine Position, keinen Betrag |
| **Wirkung** | **null Verluste** — sie blockiert nichts |

---

### 1 `auftrag` — „Instrument und Strategie erlaubt"

| | |
|---|---|
| **Wer** | **Rechnung** |
| **Modul** | `agent/asset_schalter.py::darf_analysiert_werden()` und `agent/handelsauftrag.py::pruefe()` |
| **Prüft** | die **Schalter des Nutzers** je Asset (DCA, Hebelprüfung, Bitpanda-Override) und ob das Paar Instrument/Strategie überhaupt vorgesehen ist |
| **7 Tage** | 39.471 durch, 0 verloren |

### 2 `fakten` — „Faktenlage ausreichend"

| | |
|---|---|
| **Wer** | **Rechnung** |
| **Modul** | `agent/faktenblock.py` (Werte aus der Kursreihe), `agent/lagebeschreibung.py` (Satzblöcke), Torwächter `agent/mindestkriterien.py::pruefe_bc()` |
| **Prüft** | Gibt es überhaupt eine Kursreihe, reicht die Grundlage für eine Frage? |
| **Warum eigene Stufe** | ohne Grundlage wird **gar nicht erst gefragt** — das spart den Aufruf |
| **7 Tage** | 38.802 durch, **669 verloren** |

### 3 `lagebild` — „Lagebild geliefert"

| | |
|---|---|
| **Wer** | **Rechnung** — sie prüft das Ergebnis von **LLM-1 Rolle A** |
| **Modul** | Buchung in `agent/rollen_lauf.py`, direkt nach `fakten` |
| **Prüft** | Liegt das Lagebild aus Rolle A vor? |
| **7 Tage** | 38.802 durch, **0 verloren** ➔ *Rolle A hat in sieben Tagen keine einzige Zelle gestoppt* |

### 4 `anlass` — „Faktensatz hat sich geändert"

| | |
|---|---|
| **Wer** | **Rechnung** |
| **Modul** | `agent/anlass.py::sperrt()` — Fingerabdruck über **genau den Faktensatz, den LLM-1 Rolle BC bekommt** |
| **Prüft** | Ist überhaupt etwas Neues passiert, seit zuletzt gefragt wurde? |
| **Warum eigene Stufe (16.08.)** | *kostet keinen Aufruf* — und ein identischer Faktensatz ist etwas anderes als eine Zeitregel |
| **7 Tage** | 26.797 durch, **12.005 verloren** |

### 5 `auswahl` — „gehört zu den besten k der Gruppe"

| | |
|---|---|
| **Wer** | **Rechnung** |
| **Modul** | `agent/auswahl.py`, Rangbildung in `agent/marktrang.py` |
| **Prüft** | Querschnittsrang in der Assetklasse; **Bestandspositionen sind ausgenommen** — die Verkaufsfrage darf die Auswahl nicht sperren |
| **7 Tage** | 16.242 durch, **10.555 verloren** |

### 6 `terminmarkt` — „OI-Aufbau nicht im obersten Fünftel"

| | |
|---|---|
| **Wer** | **Rechnung** |
| **Modul** | `agent/positionierung.py`, Fünftel-Rang über `open_interest_snapshot` (Grundlage F-168) |
| **Prüft** | den **Zeitpunkt**, nicht das Asset: ist der Terminmarkt überhitzt? |
| **7 Tage** | 16.242 durch, 0 verloren |

### 7 `wiederholung` — „nicht kürzlich schon gefragt"

| | |
|---|---|
| **Wer** | **Rechnung** |
| **Modul** | `agent/wiederholung.py::gesperrt_bis()` — Cooldown je Symbol, Instrument, Gruppe **und Strategie** |
| **7 Tage** | 2.055 durch, **14.187 verloren** |

---

### 8 `urteil` — hier und **nur hier** urteilt LLM-1 Rolle BC

⚠️ **Diese Stufe besteht aus vier Teilen, und nur der erste ist das
Sprachmodell.** Wer „Verlust bei urteil" liest, sieht meist die Wächter, nicht
das Urteil.

| Teil | Wer | Modul | was er tut |
|---|---|---|---|
| 8a | **LLM-1 Rolle BC** | `agent/rolle_trader.py::prompt_fuer()` | **der einzige Modellaufruf je Asset.** Liefert Aktion, Richtung, Begründung, Gegenargument, Belege, Zahl unabhängiger Faktoren, Widerlegung (wodurch / welcher Preis / bis wann), Einstieg und Stop **als Angabe** |
| 8b | Rechnung | `agent/rolle_trader.py::validiere()` → `agent/empfehlung_vertrag.py` | Pflichtfelder, Richtungspflicht, Ablehnung sich selbst zurückziehender Begründungen |
| 8c | Rechnung | `agent/gegenpruefer_rollen.py` (**„Z1"**) | **Treue zur Eingabe**: Zahlendeckung, Richtungstreue, Zuspitzung, Leerlauf. Fragt *nicht*, ob das Urteil klug ist |
| 8d | Rechnung | `urteil_memo` in `agent/rollen_lauf.py` | ein Urteil je **Asset**, nicht je Zelle — die zweite Zelle liest es aus dem Speicher, ohne neuen Aufruf |

**7 Tage:** 2.046 durch, **9 verloren** — davon 8× vom **Vertrag** (8b) als
ungültig verworfen, 1× Netzfehler. **Die 9 sind keine Ablehnung durch Rolle BC,
sondern Ablehnungen ihrer Antwort.**

⚠️ **Warum LLM-1 Rolle BC „Händler *und* Entscheider" heißt:** bis 10.08.2026
waren das zwei getrennte Aufrufe (~162 täglich). Nach dem Nutzereinwand wurden
sie in **einen** gelegt. Seither gibt es **keine LLM-Rolle „Entscheider" mehr** —
Stufe 12 heißt nur noch so.

---

### 9 `aktion` — „Aktion ist ein Einstieg"

⚠️ **Die einzige Stufe, an der Sprachmodell und Rechnung gemischt verlieren.**

| Verlustgrund | Wer entscheidet | Modul | 7 Tage |
|---|---|---|---|
| `NICHTS_TUN` / `HALTEN` | **LLM-1 Rolle BC** | die Aktion aus 8a gegen `agent/signal_mail.py::AKTIONEN_MIT_EINSTIEG` | **56** |
| „Ausstieg steht auf SCHLIESSEN" | **Rechnung** | `agent/hebelfuehrung.py` | 166 |
| „vollständig gestakt / ohne Bestand" | **Rechnung** | `agent/verkaufsrechnung.py::rechne()` | 25 |

**7 Tage:** 1.799 durch, 247 verloren — **56 davon** sind das Sprachmodell.
Das sind **2,7 %** der 2.046 Zellen, die es beurteilt hat.

### 10 `geometrie` — „Zonen rechenbar"

| | |
|---|---|
| **Wer** | **Rechnung** |
| **Modul** | `agent/entscheidungsrechnung.py::rechne()` — Stopweite aus Rauschboden und Marken, Ziel mechanisch CRV 2,0, Zonen |
| ⚠️ **Eingabe aus Rolle BC** | `umgeworfen_preis_eur` — die Preisangabe des Sprachmodells geht **als Boden in die Stopweite** ein (`_stop_abstand`) |
| **Verluste** | taktische Zelle ohne Hebel (Akkumulation) — **Rechnung**, kein Urteil |
| **7 Tage** | 1.366 durch, 346 verloren |

### 11 `risikoschicht` — „Töpfe, Cash, Positionsgröße"

| | |
|---|---|
| **Wer** | **Rechnung** |
| **Modul** | `agent/toepfe.py` (`frei_eur`, `belegt_eur`, `cash_frei_eur`), `agent/betraege.py`, **Paket B:** `agent/hebel_aggregat.py` (Aggregat-Deckel 3 %) |
| **7 Tage** | 1.366 durch, **0 verloren** — die Prüfungen laufen bereits im Geometrieblock; die Stufe bucht nur noch |

### 12 `entscheider` — ⚠️ **kein Sprachmodell**

| | |
|---|---|
| **Wer** | **Rechnung** |
| **Modul** | `agent/potential.py` — `traegt_hier` gegen die **Schwelle je Datenlage** (Vorgabe 0,080 R bei voller Datenlage) |
| **Nicht mehr** | `agent/trefferbilanz.py` — das war bis U-1 (30.08.) so und steht noch in alten Kommentaren |
| **Prüft** | Schlägt das gemessene **Potential** die Schwelle seiner Datenlage? |
| **7 Tage** | **115 durch, 1.251 verloren = 92 %** |

➔ **Der härteste Filter der ganzen Kette ist gerechnet, nicht geurteilt.**

---

### Nebenläufig nach dem Urteil — **LLM-2 Rolle G (Z.ai)**

| | |
|---|---|
| **Wer** | **Sprachmodell**, zweiter Anbieter |
| **Modul** | `agent/zweite_meinung.py`, Fakten aus `agent/positionierung.py` |
| **Eigene Fakten** | offene Kontrakte, Finanzierungsrate als Perzentil, Anteil Long-Konten, Marktregime mit Dauer — **nichts davon steht im Faktentext von Rolle BC** |
| **Wirkung** | **kein Veto.** Text in der Mail (Abschnitt 5) und im Kopf unter „Was dagegen spricht" |
| **Ausfall** | fail-soft — die Kette läuft weiter, im Log steht „Z.ai-Rolle G fehlgeschlagen" |
| **Wann gefragt** | nur bei eigener Grundlage (G5) — ohne symbolspezifische Terminmarktdaten gar nicht |

⚠️ **Z1 ist nicht Z.ai.** `gegenpruefer_rollen` (Z1, Stufe 8c) ist eine
**Rechnung** und prüft die *Treue zur Eingabe*. `zweite_meinung` (Rolle G) ist
ein **zweites Sprachmodell** und prüft die *Sache*. Die Verwechslung ist im
Projekt schon vorgekommen.

---

## Die Antwort in einem Satz

Von zwölf Stufen entscheidet **eine** ein Sprachmodell (Stufe 8, LLM-1 Rolle
BC), **eine weitere** teilen sich Sprachmodell und Rechnung (Stufe 9), **zehn
sind reine Rechnung** — und die schärfste davon (Stufe 12, `agent/potential.py`)
verwirft mehr als alle Sprachmodelle zusammen.


---

# ⚠️⚠️ Was an dieser Landkarte nicht stimmt — Nutzereinwand 12.09.

> *„Z1 kommt gar nicht vor bzw. sehe ich diese in der Kette nicht. ZAI hat
> keine Stufe? Nichts tun ist heikel bzw. ‚gemischte Stufe' hört sich schon
> seltsam an."*

**Alle drei Einwände treffen zu — und sie treffen nicht die Landkarte, sondern
die Kette.** Ich habe oben Z1 als „Teil 8c" und als „Wächter" geführt. Beides
beschönigt.

## Warum die Kette hier schief ist — die Abgrenzung des Nutzers

> *„wir bauen seit Wochen am deterministischen Einstieg je Strategie — das LLM
> wurde lange Zeit nicht ‚angegriffen', auch nicht in der Planung."*
> — dazu seine eigene Auflage: *„das ist mein Gefühl, prüfen musst du das über
> Doku und Code."*

**Geprüft an der Git-Historie und am Plan. Das Gefühl trägt — aber der Stichtag
ist der 22.08., nicht der Kettenumbau.** Die einfache Fassung („nie
angefasst") wäre falsch gewesen:

| Modul | letzte Änderung | Änderungen seit 01.08. | davon vor dem 22.08. |
|---|---|---|---|
| `rolle_trader.py` (Rolle BC) | 11.09.\* | 23 | **21** |
| `zweite_meinung.py` (Rolle G) | 03.09.\*\* | 20 | **18** |
| `gegenpruefer_rollen.py` (Z1) | **18.08.** | 6 | 6 |
| `rolle_analyst.py` (Rolle A) | **12.08.** | 7 | 7 |
| | | | |
| `entscheidungsrechnung.py` | 11.09. | **33** | — |
| `potential.py` | 11.09. | 12 | — |
| `marktrang.py` | **12.09.** | 6 | — |

\* der 11.09.-Commit kam aus dem **Hebelbau** (H-4) und hat das Urteil nicht
angefasst. \*\* der 03.09.-Commit legt nur tote Felder still (G-a).

**Und die Planung:** der erste LLM-Punkt überhaupt ist **Schritt 33, angelegt
am 11.09.** — nachgelagert („NACH den eMails") und ohne einen einzigen
Bauschritt. Davor stand kein LLM-Punkt im Plan.

➔ **Richtige Fassung: der LLM-Strang wurde im August in zwölf Tagen gebaut und
steht seit dem 22.08.** — drei Wochen Stillstand, während der deterministische
Strang durchlief. Der deterministische Teil ist **um ihn herumgewachsen**.

Die Schieflage ist damit ein Versäumnis, keine Fehlentscheidung — sie wird
aufgeräumt, nicht verteidigt. **Schritt 44 ist der erste echte Zugriff auf den
LLM-Strang seit drei Wochen**, und bewusst ein Aufräumen: keine neue Rolle,
keine neue Fähigkeit, kein zusätzlicher Aufruf.

| Einwand | Befund |
|---|---|
| **„Z1 sehe ich in der Kette nicht"** | richtig — `gegenpruefer_rollen.pruefe_und_zaehle()` bucht **immer** `bestanden`, nie `verloren`. Sie ist kein Wächter, sondern ein **Vermerk**. Im Trichter ist sie unsichtbar |
| **„Z.ai hat keine Stufe?"** | richtig — **gar keine.** Sie läuft nebenläufig, bucht nichts, hat kein Veto |
| **„gemischte Stufe hört sich seltsam an"** | richtig — sie **ist** seltsam. Stufe 9 bucht eine *Bewertung* (56× NICHTS_TUN) in dieselbe Spalte wie einen *Betriebszustand* (166× SCHLIESSEN, 25× gestakt) |

## Die Ursache: ein Zählwerk für drei Fragen

`durchlauf.verloren()` kennt **einen** Verlust. Gebucht werden drei Dinge:

| Art | Stufen | was es bedeutet |
|---|---|---|
| **nicht gefragt** | `anlass`, `auswahl`, `terminmarkt`, `wiederholung` | Kostenfilter — spart einen Aufruf |
| **nicht möglich** | `fakten`, `geometrie`, Vertrag | Datenmangel |
| **bewertet: nein** | `entscheider`, NICHTS_TUN | eine **Bewertung** — das Einzige, was den Deadloop erklärt |
| *(betriebszustand)* | SCHLIESSEN, gestakt, ohne Bestand | Lage des Depots, kein Urteil |

⚠️ **Die Unterscheidung ist im Projekt bekannt.** Sie steht wörtlich im Kopf
von `agent/rollen_gate.py`: *„drei Arten von ‚nicht jetzt': Kostenfilter,
Nutzerentscheidung, Qualitätsfilter. Nur der dritte trägt Deadloop-Risiko."*
Sie wurde nie abgebildet.

## Erster Hinweis auf die Wirkung — ⚠️ kein Befund nach Norm

Roh gezählt an `outcome_status`, **ohne Tagesklammer, ohne Nullmodell**. Er
steht hier, weil er die Richtung von Schritt 42 vorgibt.

| Stelle | wie oft sie anschlägt (7 Tage, 449 Urteile) | trennt sie die Ausgänge? |
|---|---|---|
| **Z1** (Rechnung) | **69 = 15,4 %** — 60× Zahl ohne Deckung, 9× Zuspitzung | angeschlagen **42,9 %** TP · sauber **43,0 %** — **nein** |
| **LLM-2 Rolle G** (Z.ai) | 163 beantwortet, davon **60 Einwand** · 286 nicht gefragt (G5) | Einwand **56,8 %** TP · kein Einwand **58,9 %** — **nein** |
| **LLM-1 Rolle BC**, „reines Halten" | — | 578 hätten das Ziel erreicht, 482 den Stop — **eine Sperre, die 55 % Gewinner mit aussortiert** |

⚠️ **In jedem siebenten Urteil nennt LLM-1 Rolle BC eine Zahl, die in der
Eingabe nicht steht** — und die Empfehlung geht unverändert hinaus.

⚠️⚠️ **Das heißt nicht, dass eine Stelle wegkann** (Vorgabe: kein Beitrag
fällt ohne Grund). Es heißt, dass ihr Beitrag **unbelegt** ist.

➔ **Schritt 44** ordnet (Trichter / Wächter / Entscheidungshilfe trennen),
**Schritt 42** misst. In dieser Reihenfolge — sonst misst 42 auf einer
Buchhaltung, die Bewertung und Betriebszustand vermengt.
