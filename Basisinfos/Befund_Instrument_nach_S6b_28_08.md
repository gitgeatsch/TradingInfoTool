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