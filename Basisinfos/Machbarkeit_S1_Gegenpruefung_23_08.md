# Machbarkeitsprüfung vor S1 — trägt der erweiterte Ansatz über Pläne, Zentraldokumente, Regelwerke und Code?

*Nutzervorgabe 23.08.: „bitte vorab noch einmal den neuen (erweiterten) Ansatz
über alle Pläne & Baustellen, Zentraldokumente, Regelwerke und den Code
gegenprüfen — wir müssen vorher schon potentielle Showstopper und fehlende
Informationen identifizieren. Vereinfacht: haben wir alle Werkzeuge je Bereich
zur Hand, um die Zielfrage zu beantworten und das Konzept zu tragen?"*

*Und die Warnung dazu: „wir haben mehrere bzw. unterschiedliche
Rahmenbedingungen, welche je Asset und Klasse, Markt, Indikatoren
unterschiedlich zu bewerten sind — das macht die Aufgabe sehr
herausfordernd. Du musst sehr präzise arbeiten, Schritt für Schritt, keine
Schnellschüsse über die gesamte Ablaufkette."*

> **Jede Zeile hier ist am Code gelesen oder aus einer Messung mit ihrer Zahl
> zitiert.** Wo ich eine Bewertung abgebe, steht es dabei.

---

## 0. Das Ergebnis in vier Sätzen

| | |
|---|---|
| **Sind die Werkzeuge da?** | **Ja, überwiegend.** Auftrag, Potentialmaß, Rangzahl, Merkmale und die Nachweisregeln sind gebaut — meist als Anzeige verdrahtet, nicht als Entscheidung |
| **Kann S1 so gebaut werden, wie es im Konzept steht?** | **Nein.** Fünf Punkte stehen davor, zwei davon hart |
| **Ist es eine neue Baustelle?** | **Nein** — es fällt mit **8d Rang 1** und **Reparaturliste D1** zusammen |
| **Der schwerste Fund** | ⚠️ **Die zweite Vorteilsquelle ist bereits gemessen worden — und mein eigenes Konzept behauptet das Gegenteil** |

---

## 1. Werkzeugbestand je Bereich — die Antwort auf die vereinfachte Frage

| Bereich | wofür gebraucht | vorhanden | Zustand |
|---|---|---|---|
| **Auftrag an Rolle BC** | S1 | `handelsauftrag.py` (INSTRUMENTE × STRATEGIEN, `ERLAUBTE_PAARE`, `beschreibe()`), `rolle_trader.prompt_fuer(instrument, strategie)`, `_KURSSATZ`, `rollen_lauf.fuehre_lauf(strategie=…)` | **vollständig gebaut**; Produktion steht fest auf `einstieg` |
| **Potentialmaß, barrierenfrei** | S2 | `trichter.spanne()` — **numerisch**, Faktoren je Klasse gemessen | gebaut, nur als Mailsatz verdrahtet |
| **Messrahmen dafür** | S2 | `messe_drift.py`: Rangliste **quer über Symbole am selben Tag**, fester Horizont, Newey-West, empirische Placebo-Schwelle, Survivorship benannt | **genau die Bauform, die §11 verlangt** — je Merkmal neu zu parametrisieren |
| **Rangzahl** | S3 | `drift.rang()` — numerisch | gebaut, nur als Mailsatz verdrahtet |
| **Merkmale** | S2/S3 | `vorfilter.bewerte()` (H), `lebendigkeit.richtung()`, `anlass_kalender.termine()`, `positionierung`, `marktlage` | numerisch; H ist aus `c/h/l` **historisierbar** |
| **Nachweisregeln** | alles | Methodik **2.58** (sechs Teile jeder Messung), **2.59** (Positivkontrolle misst die Verschiebung), **2.60** (Uniqueness), **2.61–2.63** | steht |
| **Speicherung der Zuweisung** | S1 → S2 | — | ⚠️ **fehlt vollständig** |

> **Die Antwort auf Ihre Frage lautet also: ja, mit fünf Ausnahmen.** Die
> stehen unten, und zwei davon sind harte Blocker.

---

## 2. Die Showstopper

### S-1 ⚠️ **HART** — die Kette hinter Rolle BC kennt `akkumulation` nicht

**Gebaut ist der Auftrag, nicht seine Folge.**

| Stelle | kennt `akkumulation` / `mit_kursen`? |
|---|---|
| `handelsauftrag.py` | ✔ `_MIT_KURSEN[("spot","akkumulation")] = False` |
| `rolle_trader.py` | ✔ eigener Prompt-Satz, entfernt gelieferte Kurse wieder |
| `rollen_lauf.py` | ✘ **null Treffer** |
| `signal_abbildung.py` | ✘ null |
| `entscheidungsrechnung.py` | ✘ null |
| `krypto/backward_tracking.py` | ✘ null |
| `wiederholung.py`, `toepfe.py` | ✘ null |

⚠️ **Und es stürzt nicht ab — das ist das Schlimme.** `ER.rechne()` bekommt
den Stop nicht vom Modell, sondern **leitet ihn selbst aus dem ATR ab**
(`_stop_abstand(kurs, atr, …)`). Ein Akkumulationssignal bekäme also einen
Stop, den seine Strategie ausdrücklich nicht hat — und würde anschließend über
genau diesen Stop **aufgelöst und bewertet**.

> **Das ist „fail-soft ist fail-silent" in Reinform:** die Strategie, die
> gerade beweisen soll, dass sie ohne Barriere auskommt, bekäme im Stillen
> eine Barriere zugeteilt.

**Folge:** S1 darf `akkumulation` **nicht zuweisen**, bevor die Kette dahinter
das Paar trägt. Das ist keine Zeile, das sind vier Module.

### S-2 ✔ **ERLEDIGT 23.08.** — die Zuweisung wird gespeichert

`strategie` kommt in `database/db.py` und `database/models.py` **null Mal**
vor. `signal_abbildung` gibt aus dem Auftrag nur `hebel` weiter.

> **Ohne Speicherung ist der Zweck der Übung weg:** „je These getrennt messen"
> ist danach nicht möglich. Es wäre exakt der Z1-Fehler — läuft, geht in die
> Mail, landet nicht in der Signalzeile, kann nie gegen Ergebnisse gemessen
> werden.

**Aufwand: klein.** Aber ohne ihn ist S1 sinnlos, nicht nur unvollständig.

### S-3 ⚠️ Das Wort „These" ist im Projekt **dreifach** belegt

| # | wo | Bedeutung |
|---|---|---|
| 1 | `models.These`, `these_id`, `kategorie_thesen.py` | **Kategorie-These** (M2-Regime, COT, Zinskurve, DXY) |
| 2 | `hebel_analyst.trade_thesis_typ`, GUI-Spalte „These", Manual **Kap. 19** | `einmal_trade` / `swing_strategie` |
| 3 | Konzept §9 | **Vorteilsquelle** |

⚠️ **Und Nummer 2 ist zugleich die Warnung.** Das Manual sagt über sie
wörtlich: sie sei *„keine Vorgabe … und ändert NICHTS an der Ausführung"*.

> **Ein Thesen-Etikett ohne Folge gab es hier also schon einmal.** Genau das
> darf S1 nicht wiederholen — sonst ist die These wieder eine Spalte in der
> Anzeige.

**Vorschlag:** das neue Feld heißt **`vorteilsquelle`**, nicht `these`.

### S-4 ⚠️ H ist **barrierenabhängig** definiert — so passt es nicht in ein barrierenfreies Maß

```python
def bewerte(marken_werte, stop_eur, ziel_eur, ist_short=False, assetklasse=""):
    # A - FREIER WEG:   keine mehrfach beruehrte Marke unter dem ZIEL
    # B - STOP GEDECKT: eine mehrfach beruehrte Marke ueber dem STOP
```

Ohne Stop und Ziel liefert es `h=None` — *„wissen wir nicht"*.

> ⚠️ **Die einzige Größe, die dieses System je gegen den Zufall gewonnen hat,
> ist über genau die Geometrie definiert, die §11 aus dem Maß herausnehmen
> will.**

**Kein Widerspruch zum Befund, aber eine Bauaufgabe:** H braucht eine zweite,
barrierenfreie Fassung — *freier Weg über X %, Träger unter Y %* statt *über
dem Ziel, unter dem Stop*. Erst dann ist die Frage „verschiebt H den Trichter?"
überhaupt stellbar. **Das ist der eigentliche Kern der Messumstellung**, nicht
ein Nebenpunkt.

### S-5 ⚠️ **Der schwerste Fund: die zweite Vorteilsquelle ist längst gemessen — mein Konzept behauptet das Gegenteil**

Konzept §9 markiert die Rückkehr-zum-Mittel-Seite (Akkumulation) als
*„Hypothese, nie gemessen"*. **Das ist falsch.** `messe_akkumulation.py` ist
am **11.08.** gelaufen (`Arbeitsstand_Deadloop_09_08.md` 7.27): 43 Symbole,
wöchentlicher Takt, 100 € je Periode für **jede** Regel gleich, nicht
ausgegebenes Geld bleibt als Barmittel liegen, Kaufkosten enthalten.

| Klasse | n | DCA | **HALBE_QUOTE** | UNTER_SMA | RUECKGANG | GESTAFFELT |
|---|---:|---:|---:|---:|---:|---:|
| krypto | 32 | 0,713 | **0,856** | 0,803 | 0,741 | 0,713 |
| etf | 6 | 1,374 | 1,180 | 1,170 | 1,114 | 1,306 |
| rohstoffe | 3 | 1,039 | 1,014 | 1,006 | 1,005 | 1,001 |
| aktien | 2 | **7,123** | 4,025 | 4,252 | 4,684 | 7,081 |
| **gesamt** | **43** | 0,754 | **0,877** | 0,841 | 0,755 | 0,755 |

**Die Kontrolle schlägt alles.** `HALBE_QUOTE` investiert konstant die Hälfte —
ohne Regel, ohne Indikator, ohne einen Blick auf den Kurs.

> **Der antizyklische Vorteil ist vollständig durch die Investitionsquote
> erklärt.** Und die Gegenprobe steht in derselben Zeile: bei den beiden
> gestiegenen Aktien gewinnt DCA mit **7,123 gegen 4,025**.

⚠️ **Aber der Befund ist regimegebunden, und das steht bei ihm selbst unter
„Grenzen":** *„Der Zeitraum dominiert. Krypto umfasst rund zwei Jahre,
überwiegend fallend."*

**Und der Markt hat am 22.08. gedreht** — BTC +23,1 %, ETH +28,6 %, Median über
49 Symbole **+15,8 %** in neun Tagen.

> **Damit ist die naheliegendste erste Messung nicht eine neue, sondern eine
> Wiederholung:** derselbe Lauf in der neuen Marktphase. Er kostet **keinen
> Modellaufruf**, liest nur Kursreihen, und er entscheidet, ob die zweite
> Vorteilsquelle überhaupt eine ist — **bevor** irgendetwas gebaut wird.

**Konzept §9 ist entsprechend zu korrigieren.** Der Eintrag stand dort als
„nie gemessen", weil auch das Memory ihn so führte.

---

## 3. ⚠️ Ihre Warnung, in Zahlen: warum eine Regeltabelle je Asset nicht gefüllt werden kann

*„Wir haben mehrere Rahmenbedingungen, die je Asset und Klasse, Markt,
Indikatoren unterschiedlich zu bewerten sind."* — **Das ist der Kern, und es
ist rechenbar.**

| Rahmenbedingung | was wir dazu **gemessen** haben | Reichweite |
|---|---|---|
| **Assetklasse** | Trichterfaktor je Klasse: krypto **0,79** · aktien **0,91** · etf **1,18**, stabil über einen zwölffachen Horizont | ✔ echte Klasseneigenschaft |
| **Merkmal H** | `GEMESSEN_AUF = "krypto"`; Kapitel 106: 2 Aktien- und 4 ETF-Reihen **reichen nicht** | ⚠️ **nur Krypto** |
| **Marktphase** | BTC hatte bis vor kurzem **ein** Jahr Historie; H überträgt sich laut Kapitel 109 **nicht** über Regimewechsel | ⚠️ **eineinhalb Phasen** |
| **Indikatoren** | Drift: **1 von 27** Feldern hält die Schwelle. Marktbreite: wirkt **invers**, ersatzlos gestrichen | ⚠️ dünn |
| **Einzelasset** | Survivorship: die Datenbank enthält nur, was es noch gibt | ⚠️ verzerrt |

**Und dazu die eigene Regel des Projekts zum Preis des Absuchens:**

> **300 durchsuchte Zellen = +20,5 Punkte Hürde. EINE vorab benannte Zelle =
> +10,2.**

Eine Tabelle *Klasse × Marktphase × Merkmal × Strategie* hat bei 5 × 3 × 5 × 2
**150 Zellen**. Wer sie absucht, zahlt fast den vollen Aufschlag — bei einer
Belegdecke von 66 aufgelösten Fällen.

> ⚠️ **Daraus folgt Ihre Vorgabe zwingend, nicht nur als guter Stil: die These
> wird EINZELN vorab benannt und EINZELN geprüft.** Keine Matrix, kein
> Durchlauf über die Ablaufkette. Eine Vorteilsquelle, eine Klasse, ein
> Horizont, eine Positivkontrolle — dann die nächste.

---

## 4. Passt der Ansatz in die bestehenden Pläne?

| Plan / Dokument | Befund |
|---|---|
| **`Zwischenstand` 8d Rang 1** — *„S2 — Drift statt Timing… der einzige Weg, der ohne Vorhersagekraft auskommt"* | ✔ **dasselbe Thema.** ⚠️ Aber dort steht es als **offen**, obwohl es am 11.08. abgearbeitet wurde — **der Plan ist nicht nachgezogen** |
| **`Zwischenstand` 8d Rang 2** — Nachrichten in den Befund | ✔ unberührt; `anlass_kalender` gebaut, nie gemessen; `cycles.py` weiterhin nicht verdrahtet |
| **Reparaturliste D1** — *„Strategien `swing`/`akkumulation` nie benutzt, offen"* | ✔ **ist wörtlich S1** |
| **`Zielgroessen_und_Erfolgsmasse.md`** | ⚠️ kennt auf Trade-Ebene nur **Expectancy (R)** und **SQN** — beide barrierenabhängig. **Für das Potentialmaß gibt es dort keine Ebene.** Sie muss ergänzt werden, sonst widerspricht §11 dem Referenzdokument |
| dasselbe Dokument, Abschnitt 2 | ✔ zitiert bereits *„No stop loss placement or profit target selection will transform random entries into a profitable system"* — **der Satz stützt §11 wörtlich** |
| **Regelwerksmanual Kap. 10** (Strategie-Katalog S-1…S-6) | ⚠️ **zweiter, älterer Strategiebegriff** — HODL, DCA, Swing, Trendfolge, Kapitalschutz, Hebel-Long. Er wird von der Rollen-Kette **nicht** benutzt. Vor S1 zuordnen oder ausdrücklich abgrenzen |
| **R-T-Regeln** | ✔ eine **je Symbol** wechselnde Auftragsangabe erfüllt **R-T6** besser als heute (heute konstant je Lauf, ausdrücklich geduldet). **R-T3** beachten: Bedingung formulieren, keine Wertung |
| **Methodik 2.58/2.59** | ✔ Positivkontrolle ist Pflicht und misst die **Verschiebung** — für das Trichter-Maß direkt anwendbar |

---

## 5. Fehlende Informationen — keine Blocker, aber vor der Messung zu klären

| # | was fehlt | Stand |
|---|---|---|
| F1 | **Einsatzbetrag** für die zweite Strategie | `betraege.VORGABE_EINSATZ_EUR["spot"]["akkumulation"] = 250 €` — **existiert, nie benutzt**; die 800 € für `einstieg` sind ausdrücklich vorläufig (C1) |
| F2 | **Wiederholungssperre** trennt nach Gruppe und Instrument, **nicht** nach Strategie | zwei Strategien auf demselben Symbol wären ein neuer Fall — §12 will die Auswahl ohnehin von der Uhr wegnehmen |
| F3 | **Kein Schalter** für Strategie je Gruppe | `INSTRUMENTE_JE_GRUPPE` führt nur Instrumente |
| F4 | **Wer weist zu?** | offen: deterministische Regel, Rolle A, oder Rangplatz. ⚠️ Eine Modellfrage mehr wäre die teuerste Variante — dieselbe Linie wie beim Betrag (R-A2): *was feststeht, geben wir vor* |
| F5 | **Horizont** des Potentialmaßes | `trichter.HORIZONTE = (5, 20, 60)`; `messe_drift` misst dieselben drei. Muss **vorab** festgelegt werden, nicht nachträglich gewählt |

---

## 6. Empfohlene Reihenfolge — Schritt für Schritt, wie verlangt

| | Schritt | warum zuerst | Modellaufrufe |
|---|---|---|---|
| **1** | **`messe_akkumulation.py` erneut laufen lassen**, neue Marktphase | entscheidet, ob die zweite Vorteilsquelle eine ist — **vor** jedem Bau | **0** |
| **2** | §9 des Konzepts korrigieren (S-5), 8d Rang 1 nachziehen | ein Plan, der Erledigtes als offen führt, verschiebt die Reihenfolge | 0 |
| **3** | **Feld `vorteilsquelle` speichern** (S-2, S-3) | ohne Speicherung ist S1 sinnlos | 0 |
| **4** | **H barrierenfrei fassen** (S-4) | ohne sie ist „verschiebt das Merkmal den Trichter?" nicht messbar | 0 |
| **5** | Kette für `akkumulation` tragfähig machen (S-1) | vier Module, nicht eine Zeile | 0 |
| **6** | **S1 — die Zuweisung an Rolle BC** | erst jetzt gefahrlos | ja |

> ⚠️ **Schritt 6 vor Schritt 1 wäre genau der Schnellschuss, den Sie
> ausgeschlossen haben** — und im schlimmsten Fall bekäme eine
> Akkumulationsstrategie im Stillen einen Stop zugeteilt.
