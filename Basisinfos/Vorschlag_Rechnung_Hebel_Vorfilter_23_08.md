# Vorschlag — die Rechnung zusammenführen, Hebel entscheiden, Vorfilter ausbauen

*Erstellt 23.08.2026. Grundlage: `entscheidungsrechnung.py`, `betraege.py`,
`anlass.py`, `signal_abbildung.py`, `wiederholung.py`, der Notebook-Export vom
22.08. und die Kapitel 88, 90.3, 127, 133–144.*

> **Alles hier ist gemessen oder am Code gelesen.** Wo ich schätze, steht es
> daneben.

---

## Teil A — Die Reparatur: `rechne()` und `dimensioniere()`

### A.1 Der Befund, nüchtern

Es gibt **zwei** Rechnungen. Der Docstring von `dimensioniere()` sagt selbst,
warum das ein Fehler ist:

> *„DIE EINE STELLE für die Dimensionierung. Zwei Aufrufer: die Messung
> (`messe_dimensionierung.py`) und **später die Produktion**. Zwei Rechnungen
> an zwei Orten sind der Fehler, an dem in diesem Projekt schon einmal Werte
> auseinandergelaufen sind."*

**„Später" ist nie gekommen.** Die Produktion ruft `rechne()`;
`dimensioniere()` wird nur für die Topf-Zuordnung benutzt (`_vor`).

| | `rechne()` | `dimensioniere()` |
|---|---|---|
| Felder | **32** | 14 |
| nur dort | Zonen, CRV, Haltedauer, Kosten, Deckel, Mindestgröße | `etikett`, `hebel_noetig`, `hebel_sicher`, `gebunden_durch`, `boeden` |
| gemeinsam | \multicolumn — **5**: `betrag_eur`, `hebel`, `risiko_eur`, `stop_eur`, `stop_regel` | |
| Hebel woher | **`instrument`** (der Lauf) | **`hebel_handelbar`** (die Gruppe) |

⚠️ **Die gute Nachricht zuerst: inhaltlich rechnen beide dasselbe.** Bei
`instrument="hebel"` liefert `rechne()` exakt die Faktoren von
`dimensioniere()` — 6,00 bei 2,5 % Stop, 2,50 bei 6 %. **Es ist keine
Zusammenführung zweier verschiedener Rechnungen, sondern eine Naht.**

### A.2 ⚠️ Was seit S6b passiert

`instrument` ist für Krypto seit S6b **immer** `"spot"`. Damit:

| | |
|---|---|
| `rechne()` | betritt den Hebel-Zweig nie → **Hebel immer 1,0** |
| `signal_abbildung` | füllt die `hebel`-Spalte nie → **Hebel-Topf und Hebel-Cooldown tot** |
| `_crv_faktor` | unterscheidet Spot und Hebel nicht mehr |

**Gemessen am Export:**

| 22.08. | Signale | mit Hebelspalte |
|---|---:|---:|
| bis 11:30 (zwei Läufe) | 97 | 55 |
| ab 11:30 (ein Lauf) | 16 | **0** |

### A.3 ⚠️ Und der tiefere Unterschied: was festgehalten wird

Die zwei Rechnungen halten **verschiedene Dinge** fest. Produktionswerte
(Verlustanteil 6 %, Einsatz 800 €, Risikobudget 48 €):

| Stop | `rechne()` Betrag | **Verlust am Stop** | `dimensioniere()` Betrag | Risiko |
|---:|---:|---:|---:|---:|
| 2,5 % | 800 € | **20 €** | 800 € | 48 € |
| 6,0 % | 800 € | **48 €** | 800 € | 48 € |
| 10 % | 800 € | **80 €** | 800 € | 48 € |
| 22 % | 800 € | **176 €** | 545 € | 48 € |

> **`rechne()` hält den Betrag fest und lässt das Risiko schwanken — um den
> Faktor 9. `dimensioniere()` hält das Risiko fest.**

`rechne()` schreibt das sogar hin: `risiko_quelle = "folgt aus Betrag und
Stopabstand"`. Das ist eine **bewusste, dokumentierte** Entscheidung — aber sie
widerspricht dem, was `verlustanteil` verspricht („wieviel vom Einsatz darf im
schlechtesten Fall verloren gehen": 6 %).

**Der Umschlagpunkt liegt bei `stop_rel = Risiko/Betrag = 6 %.** Darunter ist
die Position zu klein, darüber zu riskant. Und weil der Hebel seit S6b aus ist,
liegt **jeder** Krypto-Trade mit engem Stop heute weit unter seinem Budget:
bei 2,5 % Stop werden **20 € von 48 €** riskiert — **42 % der vorgesehenen
Risikoauslastung.**

### A.4 Der Vorschlag

**Nicht** `rechne()` durch `dimensioniere()` ersetzen — das ginge nicht, die
Zonen und das CRV fehlen dort. Sondern:

| Schritt | was | Risiko |
|---|---|---|
| **R1** | `rechne()` bekommt `hebel_handelbar: bool` statt `instrument` für die Hebelfrage. Der Parameter `instrument` bleibt für Töpfe und Texte | **klein** — beide rechnen nachweislich gleich |
| **R2** | `signal_abbildung.felder_aus_entscheidung()` schreibt die `hebel`-Spalte, wenn **die Rechnung** einen Hebel > 1 ergibt und die Gruppe hebelbar ist — statt wenn der Lauf „hebel" heißt | klein, aber ⚠️ **er belebt Hebel-Topf und Hebel-Cooldown wieder** |
| **R3** | `rechne()` holt die fünf gemeinsamen Felder aus `dimensioniere()`, statt sie zweitzurechnen | mittel — hier fällt die Entscheidung A.3 |
| **R4** | eine Dauerprüfung: für dieselben Eingaben liefern beide **dieselben** fünf Felder | – |

⚠️ **R3 enthält eine Entscheidung, die dem Nutzer gehört:** soll das Risiko je
Trade **fest** sein (dann folgt der Betrag, `dimensioniere`-Linie) oder der
Betrag fest (dann schwankt das Risiko, heutige `rechne`-Linie)? **Ohne R3 ist
R1 trotzdem sinnvoll** — der Hebel entsteht wieder, die Risikofrage bleibt
offen.

### A.5 Was das für die Messungen bedeutet

| Messung | Wirkung |
|---|---|
| **R-Vielfache** (Trefferquote, −0,609 R, MFE) | **unverändert** — R ist der Stopabstand, nicht der Euro-Betrag |
| **Hebelanteil** | ⚠️ **Bruch.** Vor S6b 55 von 97; seit S6b 0. Nach R2 wieder > 0 — **drei Regime in einer Reihe** |
| **Topf-Auslastung** | ⚠️ Hebel-Topf war seit S6b leer, füllt sich wieder |
| **Cooldown** | ⚠️ Hebel-Signale bekommen wieder ihren eigenen 3,5-h-Topf — **die Reparatur von Kapitel 142 wird dadurch teilweise überflüssig** und muss nachgeprüft werden |
| **Euro-P&L** | ändert sich nur bei R3 |
| **Backward-Tracking** | unverändert — es liest Zonen, nicht Beträge |

⚠️ **Wie bei E2 gilt Methodik 2.62:** bestehende Zeilen tragen die alte Regel.
Anders als bei E2 lässt sich hier **nichts nachrechnen** — der Hebel eines
vergangenen Signals ist nicht rekonstruierbar, weil er nie geschrieben wurde.
**Die Reihe bekommt einen Schnitt, keine Korrektur.** Der Schnitt gehört
benannt: `quelle_kette='rollen'` plus `created_at` vor/nach dem Umbau.

---

## Teil B — Wann Hebel, wann Spot: die Antwort steht in der Arithmetik

### B.1 Der Hebel ist keine Wahl, sondern eine Folge

```
hebel_noetig = verlustanteil / stop_rel
```

**Das ist die ganze Regel.** Ein Hebel entsteht, wenn der Stop so eng liegt,
dass die ungehebelte Position das Risikobudget nicht ausschöpft. **Er ist kein
Urteil über die Qualität des Trades**, sondern das Mittel, um bei engem Stop
auf volle Auslastung zu kommen.

> **„Hebel oder Spot" ist in Wahrheit „enger oder weiter Stop".** Und *das*
> ist eine Thesenfrage: ein enger Stop lohnt nur, wenn die Struktur ihn trägt
> — wenn die These also schnell widerlegt ist.

**Damit trifft die Formulierung des Nutzers genau den Mechanismus:**

| | Stop | Hebel | Horizont |
|---|---|---|---|
| **SPOT — „Bodenbildung oder Tod"** | weit | 1,0 | lang |
| **HEBEL — „kurzfristige Chance"** | eng | > 1 | kurz |

### B.2 ⚠️ Und die Kosten entscheiden mit — gegen den engen Stop

`Kosten_R = 2 × Gebühr / Stopabstand`. Der Stopabstand steht im **Nenner**:

> ⚠️ **DIE GEBÜHR DES HANDELSPLATZES GEHÖRT NICHT IN DIE BEWERTUNG**
> (Nutzervorgabe 22.08.). Ein Trade wird **neutral** beurteilt — mit der
> **Referenz 0,30 %**. Der Bitpanda-Satz von 1,50 % gehört ausschließlich in
> die **Geldrechnung der Mail**, wo der Nutzer sieht, was ihn ein Trade
> tatsächlich kostet.
>
> **Warum die Trennung trägt:** *„Es gibt den besseren Trade. Ob er sich
> rechnet, entscheidet allein der Handelsplatz."* (Kapitel 119.3). Wer den
> Betriebssatz in die Bewertung mischt, verwirft gute Trades wegen einer
> Eigenschaft, die nichts mit ihnen zu tun hat — und macht den Handelsplatz
> unsichtbar, statt ihn zur Entscheidung zu machen.

**Deshalb steht hier nur die Referenz** (CRV 2,0, Basisrate 33,3 %):

| Stop | Hebel nötig | Kosten in R | Breakeven-Trefferquote |
|---:|---:|---:|---:|
| 2,5 % | 2,40 | **24,0 %** | **41,3 %** |
| 4,0 % | 1,50 | 15,0 % | 38,3 % |
| 6,0 % | 1,00 | 10,0 % | 36,7 % |
| 12,0 % | 0,50 | 5,0 % | 35,0 % |
| 25,0 % | 0,24 | **2,4 %** | **34,1 %** |

> **Ein enger Stop braucht den Hebel UND kostet in R am meisten.**

**Die Hürde über der Basisrate:**

| | Hürde |
|---|---:|
| enger Stop (2,5 %) | **+8,0 Punkte** |
| weiter Stop (25 %) | **+0,8 Punkte** |

⚠️ **Bei Bitpanda-Gebühr (1,50 %) ist der enge Stop nicht handelbar:**
Kosten_R = 120 % — der Trade müsste mehr als das Doppelte seines Risikos
verdienen, nur um bei null zu landen.

### B.3 Was daraus für die Kette folgt

**Das ist kein Vorschlag, sondern eine Ableitung aus Zahlen, die im Projekt
schon stehen:**

1. **Der weite Stop ist die Linie, auf der das System eine Chance hat.** 0,8
   Punkte Hürde sind erreichbar; 8,0 Punkte sind es nach allem, was gemessen
   wurde, nicht.
2. **Der Hebel ist damit die Ausnahme, nicht die Regel** — und zwar aus
   Kostengründen, nicht aus Vorsicht.
3. **Er braucht eine eigene Rechtfertigung**: einen Anlass, der den engen Stop
   trägt. Genau das ist die Rolle eines Vorfilters, der etwas *aussagt* —
   nicht einer Uhr.
4. ⚠️ **Die Gebühr ist keine Eigenschaft des Trades.** Ob sich ein guter
   Trade beim eigenen Handelsplatz rechnet, ist eine zweite, getrennte
   Frage — sie gehört in die Mail, nicht in die Bewertung.

**Wo das in der Kette landet:** die Strategie (`einstieg` / `swing` /
`akkumulation`) ist die vorhandene, aber **tote** Stelle dafür —
`rollen_job.py` fährt durchgehend `einstieg`. Der Auftragstext unterscheidet
bereits *„über mehrere Wochen gehalten und laufend nachgezogen"* (swing) von
der Akkumulation. **Das ist die Naht, an der SPOT-lang und HEBEL-kurz
auseinandergehen können — sie ist gebaut und nicht verdrahtet.**

---

## Teil C — Der Vorfilter: was es gibt und was fehlt

### C.1 Es gibt ihn schon, und er ist besser gebaut als erwartet

`agent/anlass.py` führt **Fingerabdrücke über den fertigen Faktentext**:

```python
def fingerabdruecke(fakten) -> tuple[str, str]:
    """NICHT AUS DEN ROHDATEN, sondern aus dem fertigen Text. Wer den Kurs
    hashen wuerde, bekaeme bei jedem Tick einen neuen Abdruck; der Text sagt
    '1.093 EUR wert' und aendert sich erst, wenn es der Leser merkt."""
```

**Das ist genau der Gedanke des Nutzers** („wurde das Signal bereits mit
identen Indikatoren und Parametern aufgerufen"), und er ist bereits richtig
gelöst: der Abdruck hängt an dem, was das Modell **liest**, nicht an
Rohdatenrauschen.

**Zwei Abdrücke:** `voll` (mit Lagebild) und `asset` (ohne). **Und es gibt
bereits `bloeckeabdruecke()` — einen Abdruck je Faktenblock** plus
`geaenderte_bloecke`.

**Gemessen:** die Anlass-Stufe lässt 30–41 von 41 durch, blockiert also rund
**25 %**.

### C.2 ⚠️ Die Schwäche: ein Hash ist alles oder nichts

Ändert sich **irgendeine** Zahl in **irgendeinem** Block, ist der Abdruck neu
— und das Signal gilt als neu. Bei einem Faktensatz mit Kursen, Perzentilen
und Abständen ist das fast immer der Fall. **Deshalb nur 25 %.**

⚠️ **Und genau deshalb trägt heute der Cooldown die Last** — eine Uhr, die
nichts über den Inhalt weiß. Das ist die Umkehrung dessen, was sein sollte.

### C.3 Der Ausbau — in der Reihenfolge ihrer Belastbarkeit

| | was | warum es trägt |
|---|---|---|
| **V-1** | **Blockweise statt gesamt.** `geaenderte_bloecke` liegt schon vor — sperren, wenn sich **kein entscheidungsrelevanter** Block geändert hat, statt wenn sich **gar nichts** geändert hat | rein mechanisch, kein Modell, sofort messbar |
| **V-2** | **Nicht jede Änderung ist eine Änderung.** Ein Perzentil von 71 auf 72 ist keine neue Lage. Schwellen statt Gleichheit — dieselben Grenzen wie R-T11 (90/10) | ⚠️ braucht eine Entscheidung, was „relevant" heißt |
| **V-3** | **Welche Blöcke haben je etwas verändert?** Aus den bestehenden Beobachtungen messbar: bei welchen geänderten Blöcken kippte das Urteil? Blöcke ohne Wirkung gehören **nicht** in den Abdruck | rein aus Daten, kein Raten |
| **V-4** | **Erst dann den Cooldown zurücknehmen** — er ist heute die Krücke, die V-1…V-3 ersetzen sollen | ⚠️ nicht vorher: sonst steht die Bremse ganz offen |

⚠️ **V-3 ist der eigentliche Hebel** und er ist heute schon messbar: die
Tabelle `anlass_beobachtung` trägt `bloecke_json` und `geaenderte_bloecke`
seit dem 16.08.

---

## Teil D — „Gute von schlechten Trades unterscheiden" als Anforderung

**Der Stand, ohne Beschönigung:**

| | |
|---|---|
| Trefferquote der aufgelösten Signale | **27,8 %** (Kapitel 141) |
| Basisrate bei CRV 2,0 | **33,3 %** |
| kein Verfahren schlägt die Basisrate | Grundbefund 10.08., 8.441 Fälle |
| Rangplatz | trägt **negativ** (−5,8 Punkte innerhalb H) |

⚠️ **Die Anforderung ist damit nicht „das System besser machen", sondern
zuerst: eine Größe finden, die überhaupt trennt.**

**Und eine gibt es bereits: H.** Über 523 Reihen und 19.891 Anker gemessen —
zur Referenz **−0,031 R ohne Filter gegen +0,114 R mit H**, also **+0,15 R je
Trade**. ⚠️ Das ist die einzige Größe des Projekts, die den Zufall messbar
schlägt. Sie ist gebaut (`vorfilter.py`) und **entscheidet nichts**.

**Was sich aus Teil B ergibt und noch nie geprüft wurde:**

> **Die Trennung könnte im Stopabstand liegen — nicht als Filter, sondern als
> Klasse.** Weite Stops haben 0,8 Punkte Hürde, enge 8,0. Wenn die
> Trefferquote über die Stopklassen **gleich** ist, sind weite Stops
> arithmetisch überlegen, ohne dass irgendein Modell besser werden muss.

**Das ist die nächste Messung, und sie braucht keinen Umbau:** Trefferquote
und realisiertes CRV, geschichtet nach Stopabstand, über die vorhandenen
aufgelösten Signale. ⚠️ Nach E1/E2 sind es nur noch 18 — **die Messung ist
heute nicht entscheidbar** und wird es erst mit mehr Fällen.

---

## Reihenfolge, die ich vorschlage

| | | warum zuerst |
|---|---|---|
| **1** | **R1 + R2** (Hebel entsteht wieder, Spalte folgt dem Ergebnis) | ohne sie misst die Kette ein Instrument, das sie nicht schreibt |
| **2** | **V-1** (blockweiser Vorfilter) | rein mechanisch, ersetzt einen Teil der Uhr durch eine Aussage |
| **3** | **V-3** (welche Blöcke wirken) | aus vorhandenen Daten, kein Umbau |
| **4** | **R3** ⚠️ Entscheidung: festes Risiko oder fester Betrag | Geldfrage, gehört dem Nutzer |
| **5** | Stopklassen-Messung | braucht Fälle, die erst entstehen müssen |

⚠️ **Was ich NICHT vorschlage:** die Wahrscheinlichkeit jetzt an die Auswahl
zu hängen. Sie ist gebaut und zeigt an — aber solange keine Größe die
Basisrate schlägt, würde sie eine Zahl ausgeben, die nichts trennt. **Erst V-3
und die Stopklassen, dann die Wahrscheinlichkeit.**
