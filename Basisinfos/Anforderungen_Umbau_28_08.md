# Anforderungen an den Umbau — vor dem Bauen erhoben

**Angelegt 28.08.2026.** Nutzervorgabe:

> *„Bevor wir umbauen — prüfe die Anforderungen an den Umbau, dass wir alle
> Varianten abdecken und trennen können, auch die Inhalte sind zu
> berücksichtigen. Genau unseren Bedarf erheben und dann eine Lösung, welche je
> Asset, Strategie und Variante **langfristig funktioniert und kein
> Dauerkompromiss** ist."*

Und die Präzisierung, die eine Korrektur ausgelöst hat:

> *„Das Signal bewertet **0,3 Standardsatz**, und nur in der eMail werden die
> BP-Kosten von 1,5 geführt. Die Begründung, also das Potential beim Signal,
> muss neutral ohne der Gebührenfrage 1,5 Prozent sein."*

---

## 0. ⚠⚠ KORREKTUR DIESES ABSCHNITTS (28.08., nach dem Nachlesen)

**Hier stand: „Das Potentialmaß rechnet mit 0,30 %, nicht mit null" (A0).
Das war falsch, und die Doku sagt es eindeutig.**

**Nutzervorgabe N-5 vom 25.08., wörtlich:**

> *„Ein guter Trade ist dann gegeben, wenn für dieses Asset eine bestimmte
> Handlungsempfehlung — **Grund** — eintritt. **NICHT** ob der Trade oder
> Handel bei einer Börse wirtschaftlich ist — also **Fokus auf das Asset und
> das Potential**."*

Und die abgeleitete Regel: *„Börsengebühren gehören in die **Geldrechnung der
Mail**, nicht in die Handelsbewertung."*

### Es sind DREI Verwendungen, nicht zwei

| | Satz | wofür |
|---|---|---|
| **Potential** — Bewertung, Auslöser, Rangfolge | **0,00 %** | *„wie viel ist zu holen"* |
| **Messreferenz** — historische Auswertungen | 0,30 % | *„trägt die Regel bei üblichen Gebühren"* |
| **Wirtschaftlichkeit** — die Mail | 1,50 % | *„rechnet es sich bei meinem Broker"* |

Ich hatte die mittlere mit der ersten verwechselt. `agent/potential.py`
bleibt bei **0,00 %**.

### Die Begründung, die der Nutzer gegeben hat — und sie ist die tragende

> **Die Gebühr ist keine Eigenschaft des Trades, sondern des Ausführungswegs.**

Ein Trade mit CRV 2,0 und 3 % Stop hat dasselbe Potential, ob er bei Bitpanda
(1,5 %) oder anderswo (0,1 %) ausgeführt wird. **Das Asset weiß nichts von
unserem Broker.**

⚠️ **Und beim Hebel kommt die Haltedauer dazu.** Die Finanzierung kostet JE
TAG; um sie einzurechnen, müsste man wissen, wie lange die Position läuft.
Das ist zum Entscheidungszeitpunkt unbekannt — Nutzer: *„diese können wir zum
Zeitpunkt der Handelsentscheidung nicht voraussagen, aber das wollen wir auch
nicht mehr."*

**Damit ist die gebührenfreie Bewertung nicht eine Wahl unter mehreren,
sondern die einzige, die keine verdeckte Prognose enthält** — weder über den
Ausführungsweg noch über die Haltedauer.

### ⚠️ Der Preis dieser Entscheidung, offen benannt

Das Potential sagt **nicht**, ob sich ein Trade rechnet. Bei 1,5 % je Seite
und 3 % Stop sind das **1,0 R Kosten** — ein Trade mit +0,135 R Potential ist
wirtschaftlich klar negativ.

**Anforderung A0 (neu):** Die Mail muss beide Zahlen so nebeneinander zeigen,
dass die wirtschaftliche nicht übersehen wird. Sonst hat die Trennung die
Bewertung sauber gemacht und die Entscheidung verschlechtert.

## 1. Der Bedarf — was das System unterscheiden können muss

### 1.1 Fünf Asset-Varianten, die sich wirklich unterscheiden

| # | Variante | Assets | Hebel handelbar? | Instrumente |
|---|---|---:|---|---|
| **V1** | **Kern-Krypto** | 3 (BTC, ETH, SOL) | ✔ ja | spot **und** hebel |
| **V2** | taktisch Krypto | 40 | ✔ ja | spot **oder** hebel |
| **V3** | Multi-Asset | 11 (Aktien, ETF, Rohstoff) | ✘ **nein** | nur spot |
| **V4** | Absicherung | 2 | ✘ nein | nur absicherung |
| **V5** | Cash-Äquivalent | 1 (EURCV) | — | **kein Lauf** |

⚠️ **V3 ist keine Designentscheidung, sondern eine Tatsache:** Bitpanda bietet
Hebel nur für Krypto (`HEBEL_HANDELBAR_JE_GRUPPE = {"krypto": True}`).

### 1.2 Drei Strategien, die vorhanden und definiert sind

| Strategie | Erfolgsmaß | Stop | Ausstieg | erlaubt für |
|---|---|---|---|---|
| `einstieg` | Ziel vor Stop | ja | Stop + Ziel + V1 | spot, hebel, absicherung |
| `swing` | Haltekriterium | nachgezogen | + Trailing | **nur hebel** |
| `akkumulation` | Durchschnittskurs, Endvermögen | **keiner** | **nur V1** | **nur spot** |

**Anforderung A1:** Die Paar-Matrix aus `handelsauftrag.ERLAUBTE_PAARE` bleibt
die einzige Quelle. Kein zweiter Ort, an dem Kombinationen entstehen.

### 1.3 ⚠️ Der Konflikt, den V1 erzeugt

**Ein Kern-Asset soll beides können** — langfristig aufbauen **und**
kurzfristig gehebelt handeln. Das sind zwei Positionen, zwei Horizonte, zwei
Fragen.

**Heute geht das nicht:** ein Lauf, eine Strategie je Asset, und
`akkumulation` hat keinen Stop → `hebel = verlustanteil / stop_rel` ist nicht
rechenbar. **Ein Kern-Asset kann seit dem 27.08. keinen Hebel mehr bekommen.**

**Anforderung A2:** V1 braucht **zwei Bewertungen** je Asset — mit
**verschiedenen Fragen**, nicht derselben (das war der Fehler vor S6b).
Betroffen: **3 Assets, +21 Bewertungen/Tag (+12 %)**.

---

## 2. Die Trennungen, die sauber bleiben müssen

### 2.1 Zwei Gebührenebenen — nie vermischt

```
POTENTIAL      0,00 %   "wie viel ist hier zu holen"
               -> Auslöser, Rangfolge, Selektion         (N-5)
MESSREFERENZ   0,30 %   "trägt die Regel bei üblichen Gebühren"
               -> historische Auswertungen, NICHT der Betrieb
WIRTSCHAFTLICH 1,50 %   "rechnet es sich bei meinem Broker"
               -> die Mail, die Entscheidung des Nutzers
```

✔ **Geprüft am 28.08.: die Mail zeigt beide Gebührensätze nebeneinander** —
`wahrscheinlichkeit.saetze()` gibt „nötig bei Referenz 0,30 %" und „nötig bei
Betrieb 1,50 %" untereinander aus, jeweils mit Punkteabstand und R je Trade.
**A0 ist damit erfüllt.**

**Anforderung A3:** Keine Stelle, die filtert, ordnet oder auswählt, darf den
Betriebssatz sehen. **Geprüft am 27.08.: heute hält das** — aber nur, weil die
Ebene nichts entscheidet. Sobald das Potential zum Rangkriterium wird, muss
die Trennung im Code verankert sein.

⚠️ **Und beide Sätze werden IMMER nebeneinander berichtet** (Methodik 2.58.2,
*„achtzehn Kapitel lang beantwortete das Projekt unbemerkt die falsche"*).

### 2.2 Bewertung, Auslöser, Handlung

```
1 MESSFENSTER   der Takt erlaubt eine Prüfung   begrenzt, erzeugt nichts
2 AUSLÖSER      ein benennbares Ereignis        die Begründung
3 POTENTIAL     die Wahrscheinlichkeit trägt    die Selektion
```

**Anforderung A4:** ⚠️ **Der Takt ist nie Signalgeber** (Nutzervorgabe, mehrfach).

### 2.3 Instrument und Strategie

**Anforderung A5:** Das Instrument darf nicht aus dem Stopabstand *anfallen*,
wenn es die Kostenrechnung bestimmt. Heute tragen **275 von 781** Krypto-
Signalen (35 %) einen Hebel > 1,0 — und werden **ohne Finanzierungskosten**
bewertet, weil `_tier_fuer_spot_symbol` nie `TIER_HEBEL` vergibt.

⚠️ **Genau davor warnt `handelsauftrag.pruefe()` im eigenen Docstring:** *„er
würde einen Hebel-Trade als Spot-Trade bewerten — ohne die
Finanzierungskosten, die ihn erst teuer machen."*

---

## 3. Die Takt-Anforderung je Variante

| Variante | Spot-Takt | Hebel-Takt | Begründung |
|---|---|---|---|
| **V1 Kern** | **48 h** | **3,5 h** | Horizont Jahre gegen 0,30 Tage |
| **V2 taktisch** | **12 h** *(Nutzervorgabe)* | 3,5 h wenn gehebelt | |
| **V3 Multi-Asset** | 12 h | — | kein Hebel handelbar |
| **V4 Absicherung** | eigene | — | folgt dem Exposure |

**Gemessene Wirkung** (8 Tage, 1.613 Krypto-Signale):

| | Bewertungen/Tag | gegen heute |
|---|---:|---:|
| heute (3,5 h für alles) | 180 | — |
| Kern 48 h + übrige 12 h | 57 | −68 % |
| + gehebelte früher (3,5 h) | 72 | −60 % |
| **+ zweiter Lauf für V1** | **92** | **−49 %** |

⚠️ **Die Zahlen 12 / 48 sind gesetzt, nicht gemessen.** 3,5 stammt aus der
alten Kette.

---

## 4. Was heute fehlt — die Lückenliste

| # | Lücke | Größe |
|---|---|---|
| ~~L1~~ | ~~Potentialmaß rechnet mit 0,0 statt 0,30 %~~ | ✔ **entfällt** — 0,00 % ist nach N-5 richtig |
| **L2** | Kern-Assets können keinen Hebel bekommen | 3 Assets |
| **L3** | gehebelte Signale ohne Finanzierungskosten | ⚠️ **entschärft** — seit S5 (18.08.) kein Hebel über 3,0 mehr, engster Stop 2,61 %. Bleibt für 159 Signale ≤ 3,0 |
| **L4** | Cooldown kennt keine Strategie | alle |
| **L5** | Cooldown kennt das Ergebnis nicht (Hebel/Spot) | alle |
| **L6** | ⚠️ **Nur ein tragender Beitrag im Potential** | strukturell |

⚠️ **L6 ist die einzige, die kein Umbau schließt.** Alles andere ist Mechanik.

---

## 5. Was der Fachexperte sagt — die Lösung ohne Dauerkompromiss

**Das Prinzip:** *Nicht alles gleich behandeln* (Nutzervorgabe). Fünf Varianten,
fünf Behandlungen — aber **eine** Mechanik, die sie unterscheidet.

### 5.1 Die eine Mechanik

```
je Asset:
  1  Variante bestimmen        aus Assetklasse + Kern-Schalter   (steht fest)
  2  Fragen ableiten           1 oder 2, je Variante             (steht fest)
  3  je Frage: Cooldown        aus Strategie + letztem Ergebnis  (steht fest)
  4  je Frage: bewerten        Potential GEBUEHRENFREI (N-5)
  5  Handlung                  wenn Auslöser UND Potential trägt
  6  Mail                      beide Gebührensätze nebeneinander
```

**Warum das kein Kompromiss ist:** Jede Unterscheidung hat einen **fachlichen**
Grund, nicht einen historischen.

| Unterscheidung | Grund |
|---|---|
| V1 zwei Fragen | zwei Horizonte, zwei Positionen — Praxis |
| V3 kein Hebel | Bitpanda bietet ihn dort nicht |
| Akkumulation kein Stop | ein Stop bricht die Strategie in ihrem besten Moment |
| Hebel 3,5 h | Median-Haltedauer 0,30 Tage |
| 0,30 statt 1,50 in der Bewertung | *„guter Trade"* ist nicht *„rechnet es sich bei meinem Broker"* |

### 5.2 ⚠️ Und die eine Stelle, an der ein Kompromiss bleibt

**Das Instrument fällt weiterhin aus dem Stopabstand an** — außer bei V1, wo
beide Fragen getrennt gestellt werden. Für die 40 taktischen Krypto-Assets
bleibt es dabei: Der Stop bestimmt, ob es ein Hebel-Trade wird.

**Das ist vertretbar, wenn die Kostenrechnung dem Etikett folgt (L3).** Es ist
**nicht** vertretbar, solange 35 % der Signale ohne Finanzierungskosten
bewertet werden.

⚠️ **Und mit 0,30 % Referenzsatz ist die Frage womöglich ohnehin erledigt:**
Bei einem Stop von 2 % kostet allein die Referenzgebühr **0,30 R** — mehr als
der gesamte gemessene Vorsprung. **Ein gehebelter Trade mit engem Stop trägt
sich rechnerisch nicht, bevor er begonnen hat.** Das wäre zu messen, bevor
Aufwand in seine Verwaltung fließt.

---

## 6. Reihenfolge — was worauf aufbaut

| | Schritt | Vorbedingung | Größe |
|---|---|---|---|
| ~~1~~ | ~~Potentialmaß auf 0,30 %~~ | ✔ **entfällt** — 0,00 % ist richtig (N-5) | — |
| ~~2~~ | ~~Messen: trägt ein enger Stop?~~ | ✔ **war gemessen** (06.08.): unter 2 % zerstörerisch, und S5 hat den Boden am 18.08. eingebaut | — |
| **3** | Kostenrechnung folgt dem Etikett (L3) | — | mittel |
| **4** | Cooldown je Strategie und Ergebnis (L4/L5) | — | mittel |
| **5** | Zweite Frage für V1 (L2) | 2, 3 | groß |

⚠️ **Schritt 2 kann Schritt 5 überflüssig machen.** Wenn ein Trade mit engem
Stop sich bei Referenzgebühren nicht trägt, braucht der Kern keinen zweiten
Lauf für eine Handelsart, die rechnerisch nicht funktioniert.

**Das ist die Empfehlung: erst messen, dann bauen** — und zwar in dieser
Reihenfolge, weil die Messung den größten Bauschritt erübrigen könnte.

Verwandt: `Roter_Faden_27_08.md` · `Kombinationsmatrix_27_08.md` ·
`agent/handelsauftrag.py` · `Test_und_Verifikationsmethodik.md` 2.58.2, 2.80


---

# UMSETZUNGSPLAN 31.08.2026 — der dritte Anlauf, und warum er anders ist

**Nutzervorgabe 31.08., wörtlich:** *„Die Kette und Scheduler wurden nun
bereits 2mal umgebaut — zuerst eigene Aufrufe je Strategie, dann ‚über Spot'
pseudo-Hebel generiert. Jetzt im 3. Anlauf wäre meine Meinung: Asset z. B.
LINK kommt in die Bewertung — entweder es kommt nur eine Strategie in Frage,
weil dies die Bewertung ergibt, oder u. U. beides, Akkumulation und Hebel,
aber nur wenn die Bewertung dies zulässt."*

Und: *„Ich ersuche, alle deine Skills für diesen Umbau anzuwenden —
Fachexperte, technischer Experte — damit wir eine stabile Basis erhalten,
die funktioniert."*

## 0. Warum die ersten beiden Anläufe gescheitert sind

| | Anlauf | Was daran brach |
|---|---|---|
| **1** | eigene Aufrufe je Strategie | jede Strategie ein eigener Lauf → das teure Modellurteil mehrfach je Asset, Kosten und Takt explodieren |
| **2** | „über Spot", Hebel als Etikett (S6b, Kapitel 88) | ⚠️ **die Hebelkette wurde dabei aufgelöst** — siehe Abschnitt 1 |
| **3** | **eine Bewertung, mehrere zulässige Zellen** | dieser Plan |

⚠️ **Anlauf 2 war fachlich richtig und technisch unvollständig.** Kapitel 88
(*„Hebel als Ergebnis statt als Kategorie"*) bleibt gültig — der Hebel*faktor*
wird nicht geraten, er fällt aus der Rechnung an. Der Fehler war, daraus zu
schließen, dass auch die **Frage** „gehebelt handeln?" entfällt.

---

## 1. ⚠️⚠️ DER SCHADEN, DEN ANLAUF 2 ANGERICHTET HAT — lückenlos belegt

**Nutzerbefund:** *„Vorsicht, du hast durch den Umbau die Hebelkette
aufgelöst!!"* — Ursache, ebenfalls vom Nutzer: *„du hast im Produktivcode
alles als SPOT geführt!!!"*

Beides bestätigt, am Code und an den Produktionsdaten:

    1  S6b setzt INSTRUMENTE_JE_GRUPPE["krypto"] = ("spot",)
    2  assetklassen.laeufe() erzeugt fünf Läufe - KEINER mit `hebel`
    3  rollen_job.bedient_neue_kette(g) ist für ALLE fünf Gruppen True
    4  scheduler/background.py:3373
         if any(bedient_neue_kette(g) for g in {g for g,_,_ in laeufe()}):
             -> Budget-Allocator ÜBERSPRUNGEN
    5  budget_allocator ist der EINZIGE Aufrufer von generate_hebel_signal()
    6  Die neue Kette führt kein Hebel-Instrument
       -> der Hebel existiert in KEINER der beiden Ketten

### Das Screening läuft weiter — ins Leere

    hebel_triggers        82.655 Zeilen, 1.872-2.664 PRO TAG
    davon über Schwelle 70    60-619 Kandidaten PRO TAG
    höchster Score seit 11.08.  100,0  (Schwelle 70)
    hebel_signals         letztes Signal 10.08.2026
    hebel_positions       188, alle geschlossen, letzte Eröffnung 22.07.

⚠️ **Der Kommentar an `background.py:3373` sagt „Eine Klasse, eine Kette."**
Die Bedingung ist aber `any(...)`, nicht je Klasse. **Eine einzige umgestellte
Gruppe legt den gesamten alten Weg still.** Der Kommentar beschreibt die
Absicht, der Code etwas anderes.

---

## 2. Die Architektur des dritten Anlaufs

```
Asset  →  EINE Faktenlage · EIN Lagebild · EIN Modellurteil    (teuer, einmal)
              │
              ├─ spot  × einstieg        immer zulässig
              ├─ spot  × akkumulation    nur wenn dca_erlaubt  (BTC/ETH/SOL)
              └─ hebel × einstieg        nur wenn hebel_pruefung_erlaubt (24)
              │
              ▼
        je Zelle ein eigenes Potential  →  Signal, wenn es trägt
        Ergebnis: keine, eine oder mehrere Handlungen je Asset
```

`hebel × swing` entfällt (Nutzerentscheidung 31.08.: *„nur Einstieg reicht,
Swing aktuell kein Thema"*).

### Die Schalter — erhoben, nicht angenommen

    asset_hebel_settings.hebel_pruefung_erlaubt = 1   24 Assets
                                                = 0   19 Assets
    asset_dca_settings                          BTC explizit; Vorgabe
                                                _DCA_ERLAUBT_DEFAULT_SYMBOLS
                                                = {BTC, ETH, SOL} (db.py:1878)

⚠️ **BTC, ETH und SOL dürfen beides** — genau der Fall, den A2 (28.08.)
gefordert hat: *„V1 braucht ZWEI Bewertungen je Asset, mit VERSCHIEDENEN
Fragen."*

---

## 3. Die zwei Ebenen — je Strategie getrennt

**Nutzervorgabe 31.08.:** *„Du musst sauber unterscheiden zwischen Bewertungen
(neutrale Signale nur durch Potential und Wahrscheinlichkeit) ohne Gebühren
etc. und den Berechnungen im Mailtext mit den echten Werten. Ganz wichtig,
sonst vermischt man zwei verschiedene Ebenen."* Ergänzt: *„für alle relevanten
Strategien, wo Gebühren bzw. die Wirtschaftlichkeit ein Thema sind."*

| Zelle | **BEWERTUNG** | **MAIL** |
|---|---|---|
| `spot × einstieg` | **0,00 %** | 0,30 / 1,50 % als **Text** |
| `spot × akkumulation` | **0,00 %** | **gerechnet** — viele Tranchen à 250 €; die Gebühr summiert sich anders als bei einem Einmalkauf |
| `hebel × einstieg` | **0,00 %** | **gerechnet** — 0,30 / 1,50 % **plus laufende Finanzierung** |

⚠️ **Die Bewertung ist überall neutral — auch beim Hebel.** Begründung aus
`Anforderungen_Umbau_28_08.md`: *„Die Finanzierung kostet JE TAG; um sie
einzurechnen, müsste man wissen, wie lange die Position läuft. Das ist zum
Entscheidungszeitpunkt unbekannt. Damit ist die gebührenfreie Bewertung nicht
eine Wahl unter mehreren, sondern die einzige, die keine verdeckte PROGNOSE
enthält."*

---

## 4. Die Messentscheidung — und der Fallstrick, in den ich gelaufen bin

**Zu messen:** die Beiträge (Funding, Turnover, Schnittabstand) auf der
Hebel-Geometrie. Heute sind sie auf **H20** gemessen — 20 Handelstage.

### ⚠️ FALLSTRICK: die falsche Grundgesamtheit

Ich hatte gemessen: *„Hebel hält Ø 1,14 Tage, 86 von 188 unter 6 Stunden —
also brauchen wir Stundenkerzen."* **Das war falsch.**

| Quelle | Haltedauer | was es ist |
|---|---|---|
| `hebel_positions` (188) | Median **0,29 Tage** | ⚠️ **realisiertes Nutzerverhalten**, 11 Symbole, TAO allein 84 |
| `hebel_signals.mindestziel_zeitraum_tage_geschaetzt` | **1,2 – 2,1 Tage** | was das System **plante** |
| Nutzervorgabe 31.08. | **1 – 20 Tage** | der Horizont, für den bewertet werden soll |

**Die Messung bewertet die SYSTEMEMPFEHLUNG, nicht das Nutzerverhalten.**
Wer die realisierte Haltedauer misst, misst, wann jemand ausgestiegen ist —
nicht, ob die Empfehlung trug.

✔ **Entscheidung: H1 bis H20 auf Tageskerzen. Keine Stundendaten.**
Dieselben 523 Messreihen, nur andere Horizonte.

⚠️ Dieselbe Fehlerklasse wie am 30.08. („H cross-sectional geprüft, obwohl
`auswahl.py` die Auswahl macht") und wie die Tagesklammer bei H.
**Prüffrage vor jeder Messung: messe ich die Empfehlung oder das Verhalten?**

---

## 5. Die Schritte

| # | Schritt | Risiko | Nachweis |
|---|---|---|---|
| **1** | **Messung H1–H20** für die drei Beiträge | keins | Placebo-Band, beide Hälften, Survivorship, **Wirkung als Regel** |
| **2** | **Spalte `instrument` in `signals`**, Altbestand → `'spot'` | ⚠️ Migration | die 5.772 Altsignale waren tatsächlich Spot — die Migration ist wahrheitsgemäß |
| **3** | **`laeufe()` liefert Zellen je Asset** aus den Schaltern statt einer festen Gruppenliste | mittel | Trockenlauf: erwartete Zellenzahl je Asset |
| **4** | **Bewertung je Zelle** in `_ein_asset`, EIN Modellurteil für alle Zellen | ⚠️ **hoch** | Kettensimulation über alle Gruppen, Signale je Zelle |
| **5** | **`hebel_triggers` als Anlass einspeisen** | mittel | Nutzerbegründung: *„einspeisen, sonst haben wir ein Performance- und Datenbankproblem"* |
| **6** | **I-2: Paarprüfung nach der Rechnung** — `hebel × akkumulation` darf nicht entstehen | klein | |
| **7** | **Spot-Positionsführung verdrahten** + `instrument`-Filter reparieren | mittel | 268 Führungen → 43 Positionen |
| **8** | **Altbestand abgrenzen** | klein | |

### Zu Schritt 8 — Altbestand

| | Zeilen | Umgang |
|---|---|---|
| `hebel_positions` | 188, alle geschlossen | ✔ **bleibt** — echte Positionsführung, Bitpanda-Import füllt weiter, `ui/hebel_view.py` zeigt sie |
| `hebel_signals` | 1.998, letztes 10.08. | ✔ **bleibt lesbar**, wird nicht mehr geschrieben. **Kein Rückbau** — die GUI zeigt Historie |
| `hebel_triggers` | 82.655, wächst | → **Schritt 5**, wird Anlass der neuen Kette |

⚠️ **Keine offene Hebelposition** (Nutzer bestätigt 31.08.). Ein Umbau kann
keine laufende Position beschädigen — das entschärft Schritt 2 und 4
erheblich.

---

## 6. ⚠️ Die Fallstricke — für mich, beim Bauen

| # | Fallstrick | Gegenmittel |
|---|---|---|
| **F1** | **Verdrahtung über Textsuche prüfen.** Am 31.08. meldete die Prüfung `positionsfuehrung` als verdrahtet — der Treffer war ein **Docstring** | Erreichbarkeit über echte `import`-Kanten (AST), mit Gegenprobe auf eine bekannte Lücke |
| **F2** | **Grüne Suite als Wirkungsnachweis nehmen.** 1.828 Prüfungen grün, echte Produktion: **0 Signale** | `simuliere_kette.py` über ALLE Gruppen; „M = 0 Signale" ist immer ein Befund |
| **F3** | **Reichweite nicht prüfen.** Beiträge auf `krypto` registriert → vier Klassen dauerhaft gesperrt | `pruefe_beitragsabdeckung.py` VOR jeder Scharfschaltung |
| **F4** | **Leeres Feld als Erlaubnis lesen.** `strategien=()` hieß „gilt überall" — bei einer auf EINER Geometrie gemessenen Größe nie wahr | jeder Beitrag nennt seine Strategien explizit; Prüfung hält es fest |
| **F5** | **Falsche Grundgesamtheit messen** (Abschnitt 4) | Prüffrage: messe ich die Empfehlung oder das Verhalten? |
| **F6** | **Eigene Prüfungen frieren den alten Zustand ein.** Zwei Prüfungen schlugen fehl, weil sie Zahlen statt Eigenschaften festhielten | Eigenschaft prüfen, nie einen Zahlenwert |
| **F7** | **Neues bauen, was es gibt.** `zeige_bewertungsabdeckung.py` gebaut, obwohl `pruefe_assetklassen_datenlage.py` existierte | ⚠️ **`zeige_modulkarte.py` VOR jeder Ausarbeitung** — die Regel steht seit 27.08. und wurde übersprungen |
| **F8** | **Die Ebenen vermischen.** Bewertung neutral, Mail gerechnet — je Strategie verschieden | Abschnitt 3; keine Stelle, die filtert oder ordnet, sieht einen Gebührensatz |
| **F9** | **`any(...)` statt je Gruppe.** Der Fehler, der die Hebelkette auflöste | jede Weiche je Gruppe UND Instrument, nie global |

---

## 7. Was NICHT gebaut wird — und warum

| | |
|---|---|
| `hebel × swing` | Nutzerentscheidung 31.08. Bei 1–20 Tagen Horizont ist der praktische Unterschied zu `einstieg` klein, und Swing verlangt ein eigenes Ausstiegswerk |
| Tabelle `positionen` | Die Position ist **ableitbar**. Eine zweite Fassung wäre die nächste Stelle, an der Mail und Datenbank auseinanderlaufen (`positionsfuehrung.py`-Modulkopf) |
| Stundenkerzen | Abschnitt 4 — falsche Grundgesamtheit |
| Rückbau `hebel_signals` | die GUI zeigt Historie; read-only genügt |
| Akkumulations-Verbilligungssatz für den Kern | Befund 28.08.: das Maß trägt über 505 Reihen, **nicht für BTC/ETH/SOL**. Empfehlung B+C: Kern akkumulieren **ohne** Verbilligungssatz, **mit** Ausschlussbremse (> +30 % über dem Schnitt, −11,2 Punkte, 3/3 Jahre) |
