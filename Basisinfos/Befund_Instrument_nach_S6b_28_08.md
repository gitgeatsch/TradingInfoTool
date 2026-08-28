# `instrument` ist seit S6b immer „spot" — und dreizehn Stellen lesen es weiter als Entscheidung

**Angelegt 28.08.2026 abends.** Nutzerhinweis, der es aufdeckte:

> *„nicht nur falsch, sondern wir haben jetzt ein Problem mit der
> Portfolioführung und dem selektiven Aufruf sowie mit dem Vorfilter, da wir
> ja hier eine andere Strategie haben"*

---

## 0. ⚠️ Das Prüfwerkzeug gab es — es fand die drei wichtigsten Stellen nicht

**`pruefe_instrument_verzweigungen.py` existiert seit S6b** und trägt genau
diese Frage. Es meldete **15 Stellen, 9 tot**. Nach der Erweiterung sind es
**22 Stellen, 12 tot** — und die sieben neuen enthalten die drei
folgenschwersten.

**Zwei Lücken, beide nachgewiesen:**

| Lücke | Folge |
|---|---|
| **Textsuche statt Datenfluss** — es suchte den Namen `instrument` | `asset_schalter.py:89` heißt die Variable `i` (`i = str(instrument or "")…`). ⚠️ **Genau die Stelle, an der der Hebel-Schalter des Nutzers hängt** |
| **`positionsfuehrung` und `trefferbilanz` fehlten in `NEUE_KETTE`** | ⚠️ Die Portfolioführung und die **Kostenrechnung** wurden nie geprüft |

⚠️ **`positionsfuehrung` fehlte, weil ich sie am 27.08. gebaut und nicht
eingetragen habe.** Dieselbe Klasse wie „ein Schalter, den niemand fragt": ein
Werkzeug, dessen Abdeckung beim nächsten Umbau nicht mitwächst, prüft danach
etwas anderes als es behauptet.

✔ **Erweitert:** Der Sammler verfolgt jetzt Aliase (`visit_Assign` merkt jeden
Namen, der aus `instrument` entsteht), und beide Module stehen in der Liste.

---

## 1. Der gemeinsame Kern — eine Zeile erklärt alle drei Probleme

**S6b (22.08.) hat `INSTRUMENTE_JE_GRUPPE["krypto"]` von `("spot","hebel")`
auf `("spot",)` gesetzt.** Das war richtig und ist Kapitel 88: *„Hebel als
Ergebnis statt als Kategorie"*. Der Hebel fällt seither aus der **Rechnung**
an: `hebel = verlustanteil / stop_rel`.

⚠️ **Die Folge, die S6b nur zur Hälfte nachgezogen hat:**

```
instrument   ist im Lauf jetzt IMMER "spot"        (das Etikett des Durchgangs)
etikett      faellt aus der Rechnung an            (die Sachfrage)
```

**S6b hat zwei Stellen auf das Etikett umgestellt** — den Topf
(`_topf_instrument`) und die Handelbarkeit (`hebel_handelbar()`). ✔ Beide sind
nachweislich korrekt.

⚠️ **Dreizehn weitere Stellen lesen `instrument == "hebel"` unverändert
weiter** — und dort ist die Antwort seit dem 22.08. **immer nein**.

| Datei | Zeile | Wirkung heute |
|---|---|---|
| `asset_schalter.py` | 89 | ⚠️ **der Hebel-Schalter wird nie gefragt** |
| `positionsfuehrung.py` | 164 | ⚠️ **`hebel_signals` wird nie gelesen** |
| `lagebeschreibung.py` | 90 | Hebel-Block im Prompt entfällt |
| `rollen_eingabe.py` | 557, 628, 766 | drei Fakten entfallen, u.a. Finanzierung |
| `signal_mail.py` | 479, 626 | zwei Formulierungen greifen nicht |
| `trefferbilanz.py` | 191 | ⚠️ **Hebel-Tier nie vergeben — Kosten 21 % zu niedrig** |
| `entscheidungsrechnung.py` | 595 | ✔ nur Rückfall, Etikett gewinnt |
| `signal_abbildung.py` | 525 | ✔ nur Rückfall, Etikett gewinnt |
| `toepfe.py` | 92 | ✔ bekommt `_topf_instrument` |

---

## 2. Die drei Probleme, jedes nachgemessen

### ⚠️ A — Der selektive Aufruf ist wirkungslos

`asset_schalter.darf_analysiert_werden()` prüft:

```python
if i == "hebel":
    ...
    if not db.get_hebel_pruefung_erlaubt(conn, sym):
        return False, "Hebel-Pruefung fuer dieses Asset abgeschaltet"
```

`instrument` ist immer `"spot"` → **die Bedingung trifft nie zu**. Der
GUI-Schalter „Hebel-Prüfung" ist damit eine Anzeige ohne Wirkung.

⚠️ **Dieselbe Fehlerklasse wie die 13 Aktien im DCA-Standard**, die heute
Morgen entfernt wurden: ein Schalter, der etwas verspricht, was nicht
passiert. Nutzervorgabe dazu: *„überall möglich, aber nur dort Signale
erzeugen, wo ich das selektiv möchte."*

### ⚠️ B — Die Portfolioführung sieht Hebelpositionen nicht

```python
tabelle = "hebel_signals" if instrument == "hebel" else "signals"
```

`instrument` ist immer `"spot"` → **`hebel_signals` wird nie gelesen.** Ein
Symbol, das eine Hebelposition trägt, erscheint in der Führung nur mit seinem
Spot-Teil.

⚠️ **Und das Modul ist ohnehin nicht verdrahtet** — `agent/positionsfuehrung.py`
steht in der Toten-Liste der Modulkarte. Der Umbau **B** vom 27.08. ist
gebaut, aber kein Betriebsaufrufer erreicht ihn.

⚠️ **S6b hatte den Fall ausdrücklich benannt:** *„Der Bestand war ein echter
Grund für zwei Läufe: ein Symbol kann Spot UND Hebelposition tragen. Heute
theoretisch (alle 188 Positionen geschlossen), aber es kehrt zurück."* Für
`_vorabbestand` wurde das gelöst — für die Positionsführung nicht.

### ⚠️ C — Der Vorfilter bewertet Akkumulationen mit einer Barriere

`vorfilter.bewerte()` gibt `h = None` mit dem Grund *„Stop oder Ziel fehlt"* —
das ist der vorgesehene Weg für die Akkumulation, die **keinen Stop hat**.

⚠️ **Aber die Rechnung liefert immer einen Stop.** Damit bekommt H Stop und
Ziel und urteilt — über ein Signal, dessen Erfolgsmaß gar nicht
*„Ziel vor Stop"* ist, sondern *„Durchschnittskurs und Endvermögen"*.

**H ist auf CRV = 2,0 und Barrieren gemessen.** Auf eine Akkumulation
angewandt ist das eine Zahl aus der falschen Messung — genau der Grund, aus
dem `akkumulationslage.py` heute nur bei `strategie == "akkumulation"` läuft.

---

## 3. ⚠️ Und das verbotene Paar entsteht faktisch

```
ERLAUBTE_PAARE = { "spot": ("einstieg", "akkumulation"),
                   "hebel": ("einstieg", "swing"), ... }
```

`hebel × akkumulation` ist **verboten** — mit guter Begründung
(`handelsauftrag.py`: *„Die Finanzierung kostet JEDEN Tag. Eine Strategie, die
bewusst lange läuft, zahlt genau diese Kosten am längsten"*).

**Was tatsächlich passiert:**

| Schritt | |
|---|---|
| 1 | `pruefe_auftrag("spot", "einstieg")` am Lauf-Anfang → ✔ erlaubt |
| 2 | `strategie_fuer("BTC", "spot")` → **`akkumulation`** — **nicht erneut geprüft** |
| 3 | Rechnung mit `hebel_handelbar=True` → **`etikett = "hebel"`** |
| 4 | `_topf_instrument = "hebel"` → ⚠️ **Geld aus dem Hebel-Topf für eine Akkumulation** |

**Gemessen, wie leicht Schritt 3 eintritt** (Krypto, `hebel_handelbar=True`):

| Stopabstand | Hebel | Etikett |
|---|---|---|
| 2,5 % | 6,0 | **hebel** |
| 3,7 % | 4,0 | **hebel** |
| 6,2 % | 2,4 | **hebel** |
| 10,0 % | 1,5 | **hebel** |

⚠️ **Jeder Krypto-Kauf bekommt das Etikett „hebel"** — auch bei weitem Stop,
auch bei einer Akkumulation. Die Paar-Matrix steht daneben und wird an dieser
Stelle nie gefragt.

---

## 4. Was zu tun ist — Reihenfolge, nicht Liste

### ⚠️ Zuerst die vorgelagerte Frage, sonst repariert man Symptome

**Darf der Rauschboden das Modellurteil überstimmen?** Am NB-Stand 26.08.:

| Zeitraum | mit Widerlegungspreis | Stop **dort** |
|---|---|---|
| gesamt | 99,7 % | 15,4 % |
| ab 22.08. | 99,7 % | ⚠️ **6,0 %** |

**In 94 % der Fälle gewinnt die Klemme `max(2,5 %, 2,0 × ATR)`.** Daraus folgt
der weite Stop (Median 7,92 %), daraus der kleine Hebel (Median 1,10) — und
daraus, dass *„spot"* und *„hebel"* dasselbe Signal mit zwei Etiketten sind.

⚠️ **Jede Drehung an k oder am Verlustanteil bricht die Messreihe**
(Kapitel 90.2). Deshalb ist das eine **Entscheidung**, keine Messung.

### Dann die vier Reparaturen

| # | | Aufwand |
|---|---|---|
| **I-1** | **Ein Wort für die Sachfrage.** Die dreizehn Stellen dürfen nicht `instrument` fragen, sondern das Ergebnis — so wie Topf und Handelbarkeit es seit S6b tun. Vorschlag: `ist_hebelgeschaeft(rechnung)` an **einer** Stelle | mittel, mechanisch |
| **I-2** | **Die Paarprüfung nach der Rechnung wiederholen** — heute läuft sie nur einmal, mit der Vorgabe. `hebel × akkumulation` muss auffallen, wo es entsteht | klein |
| **I-3** | **Positionsführung verdrahten** (offener Punkt B1) **und** beide Quellen lesen | klein bis mittel |
| **I-4** | **Vorfilter: bei `akkumulation` kein H** — die Barrierenfrage gehört nicht zu einem Auftrag ohne Barriere | klein |

⚠️ **I-1 ist die Wurzel; I-2 bis I-4 sind Folgen davon.** Wer nur die Folgen
repariert, bekommt die nächste Stelle beim nächsten Umbau.

Verwandt: `Gesamtplan_Wo_wir_stehen_28_08.md` (Nachtrag + Korrektur) ·
`Umbauplan_Gesamtsystem_12_08.md` Kapitel 129/131/134 ·
`Befund_Akkumulationsmass_28_08.md`


---

## 5. Was die Vollprüfung ergeben hat (28.08. abends)

**Nutzerauftrag:** *„prüfe mit allen Werkzeugen und allen Dokumenten und im
Code, auch mit Simulation wenn erforderlich — im schlimmsten Fall haben wir
Fehler der letzten 3 Umbauten im Gepäck."*

| Werkzeug | Ergebnis |
|---|---|
| `pruefe_instrument_verzweigungen` | ⚠️ **7 neue Stellen**, davon 3 tot — nach Erweiterung um Aliase und 2 Module |
| `pruefe_pakete` (Suite) | ✔ **1.732 Prüfungen, alle bestanden** |
| `pruefe_aufruf_signaturen` | ✔ keine Treffer durch die neuen Parameter |
| `finde_freie_namen` | ✔ 0 Kandidaten |
| `zeige_modulkarte --tot` | ⚠️ 13 Module ohne Aufrufer, darunter `positionsfuehrung` |
| `simuliere_kette` (alle Gruppen) | ✔ 3 Gruppen, 5 Signale, 6 Mails, **0 Fehler** |

### ✔ Aus meinen drei Umbauten der letzten Tage ist **nichts** defekt

Zwei Stellen daraus standen im Verdacht, beide sind sauber:

| Stelle | Urteil |
|---|---|
| `handelsauftrag.strategie_fuer` (A, 27.08.) | ✔ **absichtlich** die Lauf-Frage — hält den Akkumulations-Schalter von der Hebel-Seite fern |
| `wiederholung.gesperrt_bis` (L4/L5, 28.08.) | ✔ fragt `INSTRUMENTE_JE_GRUPPE` statt das Instrument — S6b-bewusst gebaut |

⚠️ **Die drei toten Stellen stammen alle aus der Zeit VOR S6b** und sind am
22.08. übersehen worden, nicht in den letzten drei Umbauten entstanden.

⚠️ **Was ich dennoch zu verantworten habe:** `positionsfuehrung` nicht in die
Werkzeugliste eingetragen — dadurch blieb sie ungeprüft, obwohl das Werkzeug
sie gefunden hätte.

---

## 6. I-1 bis I-4 gebaut (28.08.2026 abends)

| # | Was | Nachweis |
|---|---|---|
| **I-1** | `handelsauftrag.ist_hebelgeschaeft(rechnung, instrument)` — **eine** Stelle beantwortet die Sachfrage, Etikett schlägt Lauf | 3 Prüfungen |
| **I-1a** | `trefferbilanz` folgt dem **Hebelwert** statt dem Lauf | ✔ **0,76 R bei Hebel 3 gegen 0,60 R bei Hebel 1** — der Kostenfehler ist weg |
| **I-1b** | Der Hebel-Schalter wird gefragt, **sobald das Etikett feststeht** | in `_ein_asset`; `asset_schalter` läuft vor der Rechnung und *kann* ihn dort nicht fragen |
| **I-2** | Paarprüfung dort, wo das Etikett entsteht | meldet `paarkonflikt`, **sperrt nicht** |
| **I-3** | Positionsführung liest **beide** Quellen | ✔ Spot + Hebel → **eine** Position, zwei Signale dahinter |
| **I-4** | Kein H bei `akkumulation` | eigene Ausnahme, damit *übersprungen* und *ausgefallen* im Log unterscheidbar bleiben |

**Verzweigungswerkzeug: 12 tote Stellen → 10.** `positionsfuehrung` hat gar
keine Fundstelle mehr — die Verzweigung ist ersatzlos verschwunden.

### ⚠️ Der Paarkonflikt ist LATENT, nicht aktiv — und das ist die wichtigere Erkenntnis

Die Simulation meldet **null** Paarkonflikte. Der Grund ist nicht, dass die
Prüfung nicht greift, sondern **wo die Schwelle liegt**:

| Stopabstand | Hebel | Etikett |
|---|---|---|
| 3,1 % | 1,9 | **hebel** |
| 5,0 % | 1,2 | **hebel** |
| **7,5 %** | 1,0 | **spot** |
| 10,0 % | 1,0 | spot |

**Das Etikett kippt bei rund 6 % Stopabstand.** Der heutige Median liegt bei
**8,94 %** — also durchgehend darüber. Deshalb entsteht heute weder ein
Hebel-Etikett noch der Konflikt.

✔ **I-2 ist damit Vorsorge für genau den Moment, in dem `stop_min_atr`
gesenkt wird.** Ohne sie entstünde `hebel × akkumulation` still, mit Geld aus
dem Hebeltopf.

### ⚠️ Und zwei eigene Fehler, beide vor dem ersten Lauf gefunden

| | |
|---|---|
| `AuftragUngueltig` nicht im Scope von `_ein_asset` | per AST-Probe gefunden — der Fehlerfang hätte den NameError geschluckt |
| `db.get_hebel_pruefung_erlaubt(...)` — **`db` ist der PFAD, nicht das Modul** | steht so im Docstring derselben Funktion. ⚠️ Der `AttributeError` wäre gefangen worden und hätte den Hebel für **jedes** Asset abgeschaltet — fail-soft mit falschem Verhalten |

**Achte Namensfalle in drei Tagen.** Beide Male hat nicht der Betrieb sie
gefunden, sondern eine Probe davor.

**Suite: 1.745 Prüfungen, alle bestanden. Simulation: 3 Gruppen, 6 Mails, 0 Fehler.**


---

## 7. Durchgerechnet: was der Umbau für die Bestandssignale bedeutet hätte

**Grundmenge:** 1.033 **Einstiegssignale** der Rollen-Kette **seit dem 19.08.**
(nach S5), davon 1.030 mit Widerlegungspreis. ⚠️ Die 2.313 aus der ersten
Zählung enthielten `HALTEN`/`REDUZIEREN` ohne echten Einstieg (Stop = Kurs,
also 0,000 %) und den Altbestand vor S5 — beides verzerrt jede Stoprechnung.

| Variante | Median L | L ≥ 2 | **L ≥ 3** | Median Stop | Kosten in R |
|---|---|---|---|---|---|
| **heute** — VA 6 %, Rauschboden | 0,75 | 3,5 % | **0,2 %** | 8,01 % | 0,292 |
| **A** — VA 12 %, Rauschboden | 1,50 | 25,7 % | 12,5 % | 8,01 % | **0,052** |
| **B** — VA 12 % + Widerlegungspreis | **4,48** | **91,4 %** | **76,4 %** | 2,68 % | 0,244 |
| **C** — VA 6 % + Widerlegungspreis | 2,24 | 57,9 % | **0,0 %** | 2,68 % | 0,192 |

**Die Stopbänder, und was M1 für sie sagt:**

| Variante | 0–2 % | 2–3 % | 3–5 % | 5–8 % | 8–12 % | > 12 % | gewichteter EW |
|---|---|---|---|---|---|---|---|
| heute / A | 0,2 % | 3,3 % | 16,0 % | 30,4 % | **34,9 %** | 15,2 % | +0,080 R |
| B / C | 0,0 % | **57,9 %** | 30,0 % | 6,0 % | 0,4 % | 5,7 % | +0,246 R |

⚠️ **Der gewichtete EW nutzt die M1-Punktschätzer je Band. Nur 0–2 % ist
belegt** — die übrigen Intervalle enthalten die Null. Die Zahl **ordnet** die
Varianten, sie sagt kein Ergebnis voraus.

### Was die Rechnung entscheidet

| | |
|---|---|
| ✔ **C scheidet aus** | am Stop allein zu drehen erreicht **nie** L ≥ 3 — bei VA 6 % und der 2,5-%-Untergrenze liegt das Maximum bei 2,4 |
| ✔ **A ist überraschend stark** | ohne den Stop anzufassen fallen die Kosten von **0,292 auf 0,052 R**, weil bei L > 1 die Hebelkosten statt der 3 % Spot-Roundtrip greifen |
| ⚠️ **B liefert die Hebel, aber** | **57,9 % landen im Band 2–3 %** — dem mit dem breitesten Intervall ([−0,604; +1,801], n = 37). Und der Median-Stop von 2,68 % zeigt: es greift meist die **Untergrenze**, nicht der Widerlegungspreis |

---

## 8. ⚠️⚠️ Der schwerste Fund: das Risikobudget ist keine Grenze

```
risiko_quelle = "folgt aus Betrag und Stopabstand"     entscheidungsrechnung.py:576
```

Bei `instrument != "hebel"` ist das Risiko ein **Ergebnis**, keine Vorgabe.
Und `instrument` ist seit S6b **immer** `"spot"` — also gilt das jetzt für
jedes Signal, auch für die, die als Hebel gehandelt würden.

**Was das im Bestand bedeutet:**

| | |
|---|---|
| Signale mit rechnerischem L unter 1,0 | **768 von 1.033 = 74,3 %** |
| Überschreitung des Budgets, Median | **+46 %** |
| 75. Perzentil | **+83 %** |
| Maximum | **+480 %** |

**Nachgerechnet an einem Fall:** Stop 8 %, 500 € Einsatz. Das Budget wären
6 % × 500 = **30 €**. Die Rechnung liefert `risiko_eur = 50,0` und
`verlust_am_stop_eur = 50,0` — **67 % über Budget**.

⚠️ **Die Formel sagt eigentlich das Richtige:** bei Stop 8 % dürfte nur
0,75 × der Einsatz investiert werden. Der Deckel auf L ≥ 1 macht daraus
„investiere voll und riskiere mehr".

⚠️ **Das ist die 13. Stelle derselben Fehlerklasse** — und sie stand nicht in
der Liste, weil sie **negiert** formuliert ist (`instrument != "hebel"`). Das
Werkzeug führt Zeile 573 als „lebt"; das Urteil ist falsch.

**Damit ändert sich die Reihenfolge der Entscheidung:** Bevor über Hebelhöhen
geredet wird, gehört geklärt, ob das Risikobudget eine **Grenze** sein soll
oder eine **Rechengröße**. Heute ist es eine Rechengröße — und wird in drei
von vier Fällen überschritten.


---

## 9. Ein hartes Budget — durchgerechnet an denselben 1.033 Signalen

**Hart** heißt: der **Betrag** folgt dem Stop, statt den Hebel auf 1 zu decken.

```
heute   betrag = Wunsch,            L = max(1, VA/stop)   ->  Risiko = betrag x stop
hart    L = max(1, VA/stop),        betrag = Budget / (L x stop)
```

| Variante | Median L | L ≥ 3 | Median Einsatz | über Budget |
|---|---|---|---|---|
| **heute** — VA 6 %, Rauschboden, weich | 1,00 | 0,2 % | 500 € | ⚠️ **74,3 %** |
| **1** — VA 6 %, Rauschboden, **hart** | 1,00 | 0,2 % | **375 €** | ✔ **0,0 %** |
| **2** — VA 12 %, Rauschboden, hart | 1,50 | 12,5 % | 500 € | ✔ 0,0 % |
| **3** — VA 12 %, Widerlegungspreis, hart | **4,48** | **76,4 %** | 500 € | ✔ 0,0 % |

✔ **Ein hartes Budget hält exakt** — Median = Maximum = Budget, in allen
1.033 Fällen. Der Mindestbetrag von 25 € wird nie unterschritten (Minimum
86 €). Bei VA 6 % sinkt der Einsatz auf 375 €, was **1,3-mal so viele
gleichzeitige Positionen** erlaubt.

⚠️ **Aber ein hartes Budget bringt keine Hebel.** Variante 1 hat denselben
Median-Hebel wie heute (1,00). Es behebt die Überschreitung, nichts sonst.

### Warum beide Probleme dieselbe Ursache haben

```
L = VA / stop     =>     L x stop = VA     =>     Risiko = Betrag x VA = Budget
```

**Solange L > 1 ist, hält das Budget von selbst** — die Formel ist in sich
richtig. Das Problem entsteht **ausschließlich** dort, wo `L < 1` und der
Deckel auf 1,0 greift. Und das ist genau dort, wo der Stop weiter ist als der
Verlustanteil.

✔ **Budgetüberschreitung und fehlender Hebel sind zwei Symptome eines
Zustands: der Stop ist weiter als der Verlustanteil.** Wer das löst, löst
beides — und wer nur das Budget hart macht, löst nur die Hälfte.

### Was das für die Reihenfolge heißt

| | |
|---|---|
| **sofort, ohne Entscheidung** | Das harte Budget ist eine **Korrektur**, keine Strategieänderung: das System hält damit ein Limit ein, das es sich selbst gegeben hat. 74,3 % → 0 % Überschreitung, ohne dass sich am Handel etwas ändert |
| **danach, mit Entscheidung** | Verlustanteil und Stopquelle — sie bestimmen, ob es überhaupt Hebel gibt |


---

## 10. ⚠️ Das harte Budget ist C2 — und die eigene Suite hat mich gestoppt

**Ich hatte es als „Korrektur, keine Strategieänderung" ausgegeben.** Das war
falsch, und zwei bestehende Prüfungen haben es beim ersten Lauf gefangen:

```
FEHL  der Spot-Betrag haengt NICHT mehr am Stopabstand
FEHL  oberhalb der Schwelle bleibt der Betrag wie bisher
      -> "Wer das aendert, entscheidet C2, und das ist eine eigene Frage"
```

**Paket Q vom 14.08. hält den Grund fest:**

> *„Tranche 800 → Risiko 800 × 15 % = 120 → Betrag 120 / 2,5 % = **4.800**.
> Dort stand 960, wo der Nutzer **800** gesagt hatte — der Betrag hätte am
> Stopabstand gehangen statt an seiner Entscheidung. Bei Spot **ohne
> Stop-Order** gibt es keine Größe, die aus dem Stop folgen könnte."*

`Umbauplan_Gesamtsystem_12_08.md` führt **C2** als *„festes Risiko oder fester
Betrag — offen, **Geldfrage**"*. Wer den Betrag aus dem Budget ableitet,
entscheidet sie — und das ist Nutzersache, nicht meine.

### Was daraus gebaut wurde

| | |
|---|---|
| **Schalter** `risikobudget_hart` | Vorgabe **False** — ändert **nichts** am heutigen Verhalten |
| ✔ **Was sich trotzdem ändert** | Der Überschuss wird **benannt**: `budget_ueberschritten_um`. Das war der eigentliche Fehler — nicht die Größe, sondern das Schweigen |
| ✔ **Unabhängige Korrektur** | `risiko_eur` folgt jetzt dem **Etikett** statt `instrument`. Vorher stand bei Hebel 1,6 dort **18,75**, während `verlust_am_stop_eur` **30,00** sagte — dieselbe Größe, zwei Zahlen |

**Verhalten im Vergleich** (Budget 30 €, Wunsch 500 €):

| Stop | Schalter | Betrag | Verlust | gemeldet |
|---|---|---|---|---|
| 3 % | egal | 500 € | 30,00 € | — *(Hebel-Zweig, hält von selbst)* |
| 8 % | **aus** | 500 € | 50,00 € | **+67 %** |
| 8 % | an | 300 € | 30,00 € | — |
| 15 % | **aus** | 500 € | 93,75 € | **+212 %** |
| 15 % | an | 160 € | 30,00 € | — |

⚠️ **Und ein eigener Fehler beim Bau:** `e["betrag_eur"] = round(betrag, 0)`
war Teil des ersetzten Blocks und fiel dabei **ersatzlos heraus** — jede
lesende Stelle hätte `None` bekommen. In der Probe gefunden, nicht im Betrieb;
sechs neue Prüfungen halten es jetzt fest.

**Suite: 1.765 Prüfungen, alle bestanden. Simulation: 3 Gruppen, 6 Mails, 0 Fehler.**


---

## 11. ⚠️ Die Simulation prüfte nicht den Produktionsstand

**Gefunden beim Verfolgen eines echten Rechenfalls durch die Kette.** Beide
Läufe von `simuliere_kette.py` liefen ohne die echte Konfiguration — der
zweite mit `config={"anlass": {"aktiv": True}}`, der erste mit **gar keiner**.
Damit fielen Einsatz und Verlustanteil auf die **Code-Vorgaben** zurück:

| | Verlustanteil | bei 5,23 % Stop |
|---|---|---|
| **Simulation** (Code-Vorgabe) | **15 %** | Hebel **2,87** |
| **Produktion** (`config.yaml`) | **6 %** | Hebel **1,15** |

⚠️ **Die Simulation zeigte einen echten Hebel, wo der Betrieb keinen erzeugt.**
Sie prüft die Kette zuverlässig — aber sie prüfte nicht die **Beträge** des
Produktionsstands, und genau die sind seit S5 die Frage.

✔ **Behoben:** `_echte_config()` lädt `config.yaml` und setzt nur
`anlass.aktiv` — der Zweck der ursprünglichen Zeile bleibt erhalten. Nach der
Korrektur zeigt die Simulation: Budget 48 €, Stop 5,23 %, `hebel_noetig` 1,15,
Hebel **1,1**, Verlust 46,04 € (unter dem Budget, weil L > 1).

**Und es ist ein unfreiwilliger Beleg:** Bei 15 % Verlustanteil entsteht ein
Hebel von 2,9 — bei 6 % einer von 1,1. Dieselbe Geometrie, dieselbe Kette,
nur die eine Zahl unterschiedlich.
