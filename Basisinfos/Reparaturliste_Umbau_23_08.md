# Reparaturliste — was der Umbau offen gelassen hat

*Nutzervorgabe 23.08.: „zuerst sollte feststehen was ist alles zu reparieren."*

> **Jede Zeile ist gemessen oder am Code gelesen, mit ihrem Zeitraum.** Wo ich
> gewertet habe statt zu messen, steht es dabei. **Ob etwas obsolet ist, steht
> hier nicht als Meinung** — sondern mit der Stelle, an der es entschieden
> wurde.

---

## 0. Die Liste auf einen Blick

| # | was | Zustand | Gewicht |
|---|---|---|---|
| **A1** | `rechne()` rechnet den Hebel aus dem **Lauf** → immer 1,0 | ✔ **repariert** 23.08. (Kapitel 145) | – |
| **A2** | `hebel`-Spalte folgt dem Lauf → nie gefüllt | ✔ **repariert** 23.08. (Kapitel 145) | – |
| **A3** | Hebel-Topf (3.000 €) ohne Gegenstand | ✔ **greift wieder** durch A2 | – |
| **A4** | Hebel-Cooldown greift wieder | ✔ **geprüft und repariert** 23.08. (Kapitel 146) — kein Doppeln, aber ein neuer Defekt aus A1/A2 | – |
| **A5** | `_crv_faktor` unterscheidet Spot/Hebel nicht mehr | ✔ **repariert** 23.08. (Kapitel 147) | – |
| **A6** | Mail-Betreff und -Abschnitt hängen am Lauf | ⚠️ offen | leicht |
| **B1** | Verkaufsseite: `facts_json` = Stummel, **zwei** Schreibpfade | ⚠️ **offen** | **schwer** |
| **B2** | Verkaufsseite: `familien=None` in `_sende_ausstieg` | ⚠️ offen | schwer |
| **B3** | Verkaufsseite: **keine** Z.ai-Zweitmeinung (0 von 561) | ⚠️ offen | mittel |
| **C1** | Einsatz 800 € statt 1.000 € | ⚠️ **Entscheidung**, dokumentiert | mittel |
| **C2** | Risiko je Trade schwankt um Faktor 9 | ⚠️ **Entscheidung** | **schwer** |
| **C3** | `crv_spreizung`: config 5,0, Code 1,0 | ⚠️ **vermessen** (Kapitel 146): nicht die Abstufung ist falsch, sondern ihre **Eichung** (2,0–6,0 gegen eine Verteilung 1,6–3,0). Vermerk gesetzt, Entscheidung offen | mittel |
| **D1** | Strategien `swing`/`akkumulation` nie benutzt | seit jeher, **kein** Umbaufolge | offen |
| **D2** | 5 Module ohne Aufrufer (`szenario_*`, `marktbreite`) | ⚠️ zu klären | leicht |
| **D3** | 27 config-Schlüssel liest niemand | ⚠️ zu klären | leicht |
| **E1** | Cooldown Krypto 15 h → 3,5 h | ✔ **repariert** 23.08. | – |
| **E2** | Finanzierungsrate + Liquidationsabstand im Lagebild | ✔ **repariert** 23.08. | – |
| **E3** | Richtungspflicht instrumentunabhängig | ✔ repariert 23.08. | – |
| **E4** | `REDUZIEREN` wird aufgelöst | ✔ repariert 22.08. | – |
| **E5** | E2: Erstellungstag nur mit Schlusskurs | ✔ repariert 22.08. | – |

---

## A — Der Hebel

### A1 ⚠️ `rechne()` rechnet den Hebel aus dem Lauf

```python
if instrument == "hebel":          # seit S6b nie wahr
    hebel_noetig = risiko_eur / (betrag * stop_rel)
```

**Gemessen:** `rechne(instrument="spot")` liefert bei jedem Stopabstand
Hebel **1,00**; mit `"hebel"` liefert es 6,00 bei 2,5 % und 2,50 bei 6 % —
**identisch zu `dimensioniere()`**. Die beiden Rechnungen unterscheiden sich
also **nicht im Rechnen**, sondern nur darin, woher sie die Handelbarkeit
nehmen.

**Wurzel:** Der Docstring von `dimensioniere()` sagt *„Zwei Aufrufer: die
Messung und **später die Produktion**"* — später ist nie gekommen. `_vor`
(die einzige Produktionsverwendung) dient nur der Topf-Zuordnung.

### A2 ⚠️ Die `hebel`-Spalte folgt dem Lauf

```python
if str(instrument) == "hebel" and rechnung and rechnung.get("hebel"):
    aus["hebel"] = float(rechnung["hebel"])
```

Der Kommentar daneben begründet die Umstellung vom Wert aufs Instrument:
*„Das Instrument ist bekannt und eindeutig; der Wert ist es nicht."*
⚠️ **Seit S6b ist es nicht mehr eindeutig.**

**Gemessen am Export:**

| 22.08. | Signale | mit Hebelspalte |
|---|---:|---:|
| bis 11:30 (zwei Läufe) | 97 | 55 |
| ab 11:30 (ein Lauf) | 16 | **0** |

### A3 ⚠️ Der Hebel-Topf — keine Meinung, eine Nutzerentscheidung

**Nicht obsolet, sondern ohne Gegenstand.** Der Topf ist eine
Nutzerentscheidung vom **13.08.**:

> *„Hebeltopf gesamt kann 3000 Euro sein, eine Hebelposition vorerst 1000"* —
> drei Positionen gleichzeitig.

Und seine Begründung steht im Modulkopf:

> **„HEBEL BEHÄLT ALS EINZIGER EINEN DECKEL: er ist die einzige Position, die
> MEHR verlieren kann als ihr Einsatz. Dort ist eine Obergrenze kein
> Hindernis, sondern der Sinn der Sache."**

Fachlich: **Core-Satellite mit explizitem Risikobudget.**

⚠️ **Die Sicherheitsfolge, und sie bindet die Reihenfolge:**

> **A1 ohne A2 wäre die gefährliche Kombination.** Der Hebel entstünde wieder,
> würde aber nicht in den gedeckelten Topf gebucht — `sql_bedingung("hebel")`
> ist `hebel IS NOT NULL`. Eine 3.000-€-Obergrenze, die nichts sieht.
> **A1 und A2 gehören zusammen oder gar nicht.**

### A4 Der Hebel-Cooldown

Dieselbe Mechanik: `wiederholung` trennt nach Instrument, und der Hebel-Topf
hat 3,5 h gegen 15 h bei Spot. Seit S6b ohne Gegenstand.

⚠️ **Und E1 hängt daran.** Die Reparatur vom 23.08. (Krypto auf 3,5 h) war
richtig, **solange kein Hebel entsteht**. Kommt er zurück, muss nachgeprüft
werden, ob der Gruppenwert den Instrumentwert nicht doppelt.

### A5 `_crv_faktor(crv, instrument, kostenklasse)`

Die CRV-Abstufung unterscheidet Spot und Hebel — seit S6b nicht mehr.
⚠️ **Wirkungslos, weil C3 die Abstufung ohnehin stilllegt** (Spreizung 1,0).

### A6 Mail-Betreff und -Abschnitt

`signal_mail.baue_mail` verzweigt zweimal am `instrument`. Kosmetisch —
**aber falsch, sobald die Rechnung wieder einen Hebel ergeben kann.**

---

## B — Die Verkaufsseite

### B1 ⚠️ Der Faktenstummel

| Aktion | Zeilen | `facts_json` |
|---|---:|---:|
| ERÖFFNEN | 881 | **2.187 Zeichen** |
| HALTEN | 475 | **17** |
| REDUZIEREN | 75 | **17** |
| VERKAUFEN | 11 | **18** |

**Zwei Schreibpfade verdrahten `fakten={"asset": symbol}` fest:**
`_schreibe_nein` und `_sende_ausstieg`.

⚠️ **Die naheliegende Erklärung ist widerlegt:** „kein Bestand" stimmt nicht —
**72 von 75 REDUZIEREN haben Bestand**; Staking auch nicht (1 von 34 voll
gestakt).

> **Das erklärt O-29** („die Verkaufsseite ist durch nichts erklärt, alle
> p > 0,47"): **es gab keine Merkmale zu messen.**

### B2 `familien=None`

`_sende_ausstieg` übergibt die drei gemessenen Familien gar nicht. Deshalb
tragen **10 von 75** REDUZIEREN und **2 von 11** VERKAUFEN ein
Schwankungsperzentil — gegen 460 von 475 bei HALTEN.

### B3 Keine Zweitmeinung

Z.ai erreicht **668 von 881** ERÖFFNEN — und **0 von 561** auf der
Verkaufsseite.

⚠️ **Priorität: nicht 1.** Nutzerbegründung, und sie wird von den Daten
gestützt:

> *„wenn der Einstieg falsch ist … am Ende werde ich ausgestoppt oder der
> Ausstieg ist im Verlust."*

**Gemessen (66 aufgelöste Signale, Stand vor E1/E2):** von 24 Stops standen
**nur 5 (20,8 %) je bei ≥ 1R** — 79 % waren nie irgendwo. Die Lücke
„erreichbar 71,2 % gegen angekommen 63,6 %" beträgt **7,6 Punkte**.

---

## C — Die Größenfrage: der Fachstandard steht schon im Projekt

**Nutzervorgabe 23.08.:** *„das Risiko sollte sich über die Qualität der
Indikatoren und der daraus resultierenden Wahrscheinlichkeit ableiten."*

**Genau das ist der Fachstandard, und das Projekt hat ihn gemessen**
(Entscheidungslog 03.08.):

> *„Van Tharp/Kelly bemessen damit die **Position** statt Ja/Nein zu
> entscheiden; ein Gate ist der Sonderfall ‚Größe 0 oder 1'."*

| gemessen | Gate | größenbasiert |
|---|---|---|
| **Hebel** | **SQN +3,25** | +1,25 |
| **Spot** | SQN +0,63 | **+1,36 bei 5× Spreizung** |

**Der Befund ist gegenläufig je Instrument:** beim Hebel entfernt das Gate
65 % der Signale und das ist richtig; bei Spot entfernt es nur 12 % und
**Größe schlägt Gate deutlich** (Summe R: +9,8 → +23,1).

### C3 ⚠️ Und die Abstufung ist heute abgeschaltet

```python
"crv_spreizung": 1.0,   # STILLGELEGT 15.08.2026
```

**Mit Begründung, nicht vergessen:** seit dem Struktur-Ziel (12.08.) fällt das
CRV aus dem Chart statt mechanisch bei 2,0 zu liegen — die auf 298 Altsignale
geeichte Abstufung *„kürzte damit fast jede Empfehlung pauschal auf ein
Fünftel"*.

> **Der Mechanismus, den der Nutzer beschreibt, existiert also, war gemessen
> wirksam und ist mit gutem Grund stillgelegt — er braucht eine neue Eichung,
> keine Neuerfindung.**

### C1 / C2 Die zwei offenen Zahlen

| | heute | offen |
|---|---|---|
| **Einsatz** | 800 € (der alte Spot-Wert) | Obergrenze 1.000 €; vorläufig, dokumentiert in `betraege.py` |
| **Risiko je Trade** | schwankt **um Faktor 9** (20 € bei 2,5 % Stop, 176 € bei 22 %) | fest oder folgend? |

---

## D — Was aus dem Umbau NICHT stammt

⚠️ **Getrennt aufgeführt, damit es nicht als Umbaufolge gilt.**

| | |
|---|---|
| **D1** `swing`/`akkumulation` | `rollen_job.py` fährt seit jeher `einstieg`. **Kein Umbaufehler** — eine nie verdrahtete Strategie |
| **D2** 5 Module ohne Aufrufer | `marktbreite` wurde am 12.08. **ersatzlos gestrichen** (L1–L6) — das ist entschieden. Die vier `szenario_*` sind **nicht entschieden**, nur unbenutzt |
| **D3** 27 config-Schlüssel | überwiegend Absichtserklärungen ohne Code (`risiko.stop_loss_pflicht`, `antizyklisch.*`, `hebel_screening.gewichte.*`) |

---

## Was ich als Reihenfolge vorschlage — und warum

| | | Begründung |
|---|---|---|
| **1** | **A1 + A2 gemeinsam** | ⚠️ einzeln unsicher (A3). Danach entsteht der Hebel wieder **und** wird gedeckelt |
| **2** | **A4 nachprüfen** | die Cooldown-Reparatur von heute darf sich nicht doppeln |
| **3** | **B1 + B2** | zwei Zeilen je Schreibpfad — danach ist die Verkaufsseite überhaupt messbar |
| **4** | **C2 messen, nicht entscheiden** | wie oft weicht das reale Risiko vom Budget ab? Aus den vorhandenen Signalen rekonstruierbar |
| **5** | **C3 neu eichen** | die Abstufung auf der **neuen** CRV-Verteilung messen, statt die alte Eichung zurückzuholen |

⚠️ **A5, A6, D1–D3 bewusst nicht in der Reihenfolge** — sie sind benannt und
warten, damit die Liste nicht zur Baustelle wird.
