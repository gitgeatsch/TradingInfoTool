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

## ⚠️⚠️ N-13: EIN NEU AUFGENOMMENER WERT IST NICHT BEWERTBAR (01.09.2026)

**Nutzerauftrag, der es aufdeckte:** *„Prüfe, wenn wir neue Assets
hinzufügen, muss das System auch funktionieren — also prüfe, wie das System
funktioniert und ob für neue Werte die Bewertungen ebenfalls geladen werden
oder vorgeladen sind."*

**Am Code geprüft. Was ein neu aufgenommener Wert automatisch bekommt:**

| | Quelle | automatisch? |
|---|---|---|
| Kursreihe | `refresh_prices_job`, `refresh_ohlc_job` | ✔ **ja** |
| **Funding** | `hole_fremdreihen.py` | ✖ **nur von Hand** |
| **Umlaufmenge** | `hole_umlaufmenge.py` | ✖ **nur von Hand** |
| Historie rückwärts | `lade_historie_nach.py` | ✖ nur von Hand |

⚠️ **Funding und Turnover sind die EINZIGEN zwei tragenden Beiträge.** Fehlen
beide, ist `potential.bewertbar` falsch, und Stufe 11 verwirft mit *„keine
Datengrundlage"*. **Ein neu aufgenommener Wert erzeugt also nie ein Signal,
bis jemand drei Skripte von Hand startet.**

✔ **Immerhin nicht still:** der Trichter nennt den Grund, und die Modulkarte
führt die drei Werkzeuge. Aber es steht nirgends, dass sie beim Aufnehmen
eines Werts zu laufen haben.

### N-13a — Der Turnover-Engpass, und er ist gelöst

**Gemessen:** Turnover ist heute für **6 von 43** Krypto-Werten bestimmbar.
Ursache: `api/onchain.py` liest die **CoinMetrics Community-API**, und die
deckt einen festen Bestand von **66 überwiegend älteren** Werten ab
(1INCH, AAVE, ADA, …). TAO, SUI, SEI, KAS, ONDO, RENDER stehen nicht darin.

⚠️ **Damit steht bei 86 % der Krypto-Werte das Potential auf EINEM Beitrag.**

**An der Quelle geprüft — CoinGecko liefert es vollständig:**

    /coins/markets?ids=…  ->  43 von 43 mit `circulating_supply`
                              EINE Anfrage, `total_volume` kommt mit
    /coins/{id}/market_chart  ->  Umlaufmenge = Marktkap. / Preis,
                              365 Tage (länger nur mit Schlüssel: HTTP 401)

**Alle 43 Watchlist-Werte haben bereits eine CoinGecko-ID** — die Quelle ist
schon im System.

⚠️ **Die Unterscheidung, auf die es ankommt:** Zum ANWENDEN des Beitrags
genügt der HEUTIGE Wert (`turnover_fuenftel` ist ein Querschnittsrang). Zum
MESSEN braucht es Historie — und die ist bereits erledigt, auf
`messdaten.db` und den 66 CoinMetrics-Reihen. **Der Engpass ist also die
Anwendung, nicht die Messung**, und eine einzige Anfrage je Tag behebt ihn.

### ⚠️⚠️ N-13-1 GEPRÜFT — UND ES IST NICHT DER QUELLENTAUSCH, DEN ICH ANGEKÜNDIGT HATTE

**Ich hatte N-13-1 als „klein" eingestuft: Umlaufmenge aus CoinGecko statt
CoinMetrics, 6 → 43. Das war zweimal falsch.**

**Erstens: die Laufzeit holt die Menge SCHON von CoinGecko** (`marktrang.py`
Zeile 47 und 436). Der Engpass sitzt woanders — bei `messbasis()`,
Zeile 483:

> *„AUF DIE MESSBASIS EINGRENZEN … Ein Rang über die falsche Menge sähe aus
> wie ein richtiger."*

⚠️ **Das ist ein SCHUTZ, kein Loch.** Turnover wurde auf den 66
CoinMetrics-Werten gemessen; ihn auf TAO anzuwenden wäre genau der
H-Fehler — die Anwendung reicht weiter als die Messung. Die Basis zu
weiten verlangt also eine **neue Messung**, und die braucht Mengen-
HISTORIE, nicht den heutigen Wert.

**Zweitens: es gibt keine freie Mengen-Historie über 365 Tage.**
An der Quelle geprüft:

| Quelle | Ergebnis |
|---|---|
| CoinGecko `market_chart` | **365 Tage**, darüber HTTP 401 |
| CoinGecko `market_chart/range` | dieselbe Grenze (`error_code 10012`) |
| CoinPaprika `tickers/historical` | **HTTP 402** — kostenpflichtig |
| CryptoCompare `histoday` | **Schlüssel erforderlich** |
| Messari `sply.circ` | nicht erreichbar |
| CoinCap | Verbindung scheitert |

365 Tage ergeben bei Horizont H20 (Block = 60 Tage) **6 Blöcke** — nötig
sind 20 (Methodik 2.95). **Untermächtig.**

**Drittens: die naheliegende Näherung versagt — gemessen, nicht vermutet.**
„Heutige Menge rückwärts anwenden", geprüft an 53.714 Ankern über 63 Werte
mit echter Historie:

| Mengenwachstum | Symbole | Fünftel wechselt |
|---|---|---|
| < 1 % | 27 | 6,3 % |
| 1–5 % | 5 | 5,2 % |
| 5–20 % | 12 | 7,3 % |
| **> 20 %** | 5 | **39,3 %** |

Insgesamt 89,2 % Übereinstimmung — ⚠️ **aber der Gesamtwert täuscht:** die
63 Testwerte sind das alte CoinMetrics-Universum mit träger Menge. **Bei
wachsender Menge versagt die Näherung, und das sind genau die jungen
Werte, für die wir sie bräuchten.**

### N-13-1' — was stattdessen möglich ist

**Ein Beitrag, der die Menge gar nicht braucht.** Turnover misst
Aufmerksamkeit: viel Umschlag je Bestand. Dieselbe Idee ohne den fehlenden
Nenner:

> **Anteil dieses Werts am GESAMTVOLUMEN des Tages** — ein reiner
> Querschnitt, nur aus dem Volumen, das für alle **578** Messreihen
> vorliegt.

| | Turnover (heute) | Volumenanteil (Vorschlag) |
|---|---|---|
| Nenner | Umlaufmenge | Gesamtvolumen des Tages |
| Messbasis | 66 Werte | **578** |
| Anwendbar auf | 6 von 43 | **alle, ab Tag 1** |
| Form | Querschnitt | Querschnitt ✔ (N-13b) |

⚠️ **Es ist ein NEUER Kandidat und braucht seine eigene Messung** — mit
Tagesklammer, Placebo-Band, beiden Hälften und Wirkung als Regel. Er ist
nicht dasselbe wie Turnover und darf dessen Zahlen nicht erben.

### N-13b — Und die Bauform künftiger Beiträge

**Gemessen am 01.09.:** Die elf Werte ohne Binance-Perpetual sind die
**jüngeren** — Median-Alter der Kursreihe **496 gegen 1.113 Tage**.

| Ein morgen aufgenommener Wert | Querschnitt | Zeitreihe |
|---|---|---|
| mit Perpetual | ✔ **ab Tag 1** | ✖ ab Tag 250 |
| ohne Perpetual | ✖ nie | ✖ nie |

⚠️ **Folge: der OI-Beitrag gehört als QUERSCHNITTSRANG gebaut**, nicht als
Zeitreihen-Extremum — sonst ist er bei neuen Werten doppelt blind. Das
trifft rückwirkend auch `funding_extrem` aus H-4b (250 Tage nachlaufend,
und mit +1,0 Punkten ohnehin der schwächste der vier Kandidaten).

### Die Schritte

| # | | Größe |
|---|---|---|
| **N-13-1** | **Umlaufmenge aus CoinGecko** statt CoinMetrics — eine Anfrage je Tag, 43 von 43 | klein |
| **N-13-2** | **Ein Job für neue Werte**: erkennt einen Wert ohne Beitragsdaten und holt Funding + Menge nach, statt auf einen Handgriff zu warten | mittel |
| **N-13-3** | Beim Bau jedes neuen Beitrags: **Querschnitt vor Zeitreihe**, sonst begründen | Regel |

---

### ✔ STAND 01.09.2026 — SIEBEN VON ACHT SCHRITTEN SIND GEBAUT

| # | Schritt | Stand | Nachweis |
|---|---|---|---|
| 1 | Messung H1–H20 | ✔ | Beiträge registriert |
| 2 | Spalte `instrument` in `signals` | ✔ | `_migrate_signal_instrument` |
| **3** | **`laeufe()` liefert Zellen je Asset** | ✔ **01.09.** | 57 Zellen über 54 Assets; BTC/ETH/SOL mit zweien |
| **4** | **Bewertung je Zelle, EIN Modellurteil** | ✔ **01.09.** | Urteilsspeicher — zwei Zellen kosten **einen** Aufruf |
| **5** | **`hebel_triggers` als Anlass einspeisen** | ✔ **01.09.** | Terminmarkt in `bc_ein["terminmarkt"]`; Fingerabdruck ändert sich |
| **6** | **I-2: Paarprüfung nach der Rechnung** | ✔ **01.09.** | `hebel × akkumulation` **entsteht nicht mehr** (vorher 2× gemeldet, jetzt 0×) |
| **7** | **Positionsführung verdrahten** | ✔ **01.09.** | Abschnitt „WAS SIE HALTEN" in der fertigen Mail |
| **8** | **Altbestand abgrenzen** | ✔ **01.09.** | Wächter: die neue Kette schreibt **nichts** in den Altbestand |

⚠️ **Was in den Zellen NICHT entsteht:** `hebel × einstieg` als eigene Zelle
für gewöhnliche Assets — dort ist es dieselbe Frage wie `spot × einstieg`
(gebührenfrei identisches Potential, F-163). Für **Kern-Assets** ist es die
einzige taktische Kauffrage und entsteht sehr wohl — sie fällt aber weg,
wenn die Rechnung keinen Hebel ergibt (Nutzerentscheidung 01.09.: *„nur wenn
die Rechnung tatsächlich einen Hebel ergibt"*).

⚠️ **OFFEN AUS SCHRITT 8: die Aufbewahrung.** Gemessen am NB-Stand 29.08.:

| Tabelle | Zeilen | Anteil | Wachstum |
|---|---|---|---|
| `open_interest_snapshot` | 227.395 | 26,8 % | **1.804.330 / Jahr** |
| `hebel_triggers` | 82.655 | 9,7 % | **655.849 / Jahr** |

**Zusammen 36,5 % aller Zeilen der Produktionsdatenbank (331 MB), wachsend
um rund 2,5 Mio Zeilen im Jahr.** Genau das Datenbankproblem, das der Nutzer
benannt hat. Seit Schritt 5 haben die Rohdaten einen Abnehmer — aber der
**Anlass braucht nur die jüngste Stunde**, die Perzentile ein begrenztes
Fenster. ⚠️ **Eine Aufbewahrungsregel ist damit begründbar, aber sie löscht
Daten — das ist eine Nutzerentscheidung und wurde NICHT ausgeführt.**

---

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
| **Basis-/Cash-and-Carry-Handel** | ⚠️ **VERWORFEN 01.09.2026, Nutzerentscheidung.** In der Literatur die dominante institutionelle Krypto-Strategie (long Spot + short Perpetual, um positives Funding einzusammeln) und die **einzige** der fünf Praxisbegründungen für Hebel, bei der ein Ertrag entsteht, den Spot strukturell nicht haben kann. Wörtlich: *„Basis-Handel ist noch kein Thema gewesen und aus aktueller Sicht keine Option, keine Short und zu teuer."* — **Zwei Gründe, beide tragend:** (1) Die Short-Seite ist seit dem Nur-Long-Umbau (05.08.) nicht im System; sie wieder aufzumachen wäre ein eigener Umbau. (2) Der Ertrag ist die Funding-Differenz, typisch im niedrigen einstelligen Prozentbereich p. a. — bei **1,50 % je Seite** bleibt davon nichts. ⚠️ **Bei einem Wechsel des Handelsplatzes (Standardsatz 0,30 %) wäre Punkt 2 neu zu rechnen; Punkt 1 bliebe.**
| Akkumulations-Verbilligungssatz für den Kern | Befund 28.08.: das Maß trägt über 505 Reihen, **nicht für BTC/ETH/SOL**. Empfehlung B+C: Kern akkumulieren **ohne** Verbilligungssatz, **mit** Ausschlussbremse (> +30 % über dem Schnitt, −11,2 Punkte, 3/3 Jahre) |

---

# NACHTRAG 01.09.2026 — zwei Themen, die getrennt bleiben müssen

**Nutzerauftrag:** *„Nimm die erforderlichen Änderungen für G in den Plan
auf"* — und, nach dem Hebel-Befund: *„die Inkonsistenz zum Hebel sauber in
der Historie, Messdokumenten, Dokumentation, Zentraldokumenten, Regelwerken
etc. nachschlagen — dieses Loch müsste dir doch aufgefallen sein."*

⚠️ **Die beiden Themen sind getrennt zu halten.** Nutzervorgabe 31.08.:
*„G ist eine LLM-Bewertung ‚als Gegenprüfung', aber nicht als
Signalbewertung… wenn es eine Lücke bei LLM G ist, müssen wir das bei der
Rolle G berücksichtigen, aber das ist von unserer Signalbewertung zu
trennen."*

---

## 8. Rolle G — was sie ist, und was an ihr zu ändern ist

### 8.1 Was Rolle G in der Kette genau ist

| | |
|---|---|
| **Modul** | `agent/zweite_meinung.py` |
| **Rolle** | zweiter LLM (Z.ai), **Gegenprüfung** des Urteils von Rolle BC |
| **Stellung** | läuft **NACH** dem Mailbau, steht in **keiner** Trichterstufe |
| **Ausgabe** | ein eigener Mailabschnitt (`gegenpruefung=`) |
| **Besonderheit** | ⚠️ **sie sieht als einzige Rolle den Terminmarkt** — die OI-Fakten kommen bei ihr an (geprüft 01.09.: BTC +0,91 %, LINK +0,08 %, TAO −0,42 %, `fehlt: []`) |

### 8.2 Der Befund — 725 Widersprüche ohne Folge

Gemessen an der Notebook-Produktion (2.789 Signale):

    urteilt bei          1.352 Signalen (48 %)
    sagt "nein" in         725 Fällen (54 % ihrer Urteile)
    davon gesperrt           0
    -> rund 45 Widersprüche je Tag, alle versendet

**Die Mail sagt „kaufen" und zwei Absätze weiter „ich würde nicht".** Das ist
kein Fehler in G, sondern eine fehlende Festlegung: **was soll ein
Widerspruch bewirken?**

### 8.3 ⚠️ Was NICHT gemacht wird

**Rolle G wird keine Trichterstufe.** Mein erster Vorschlag am 31.08. war
genau das — er ist zurückgezogen. Begründung des Nutzers, und sie trägt:

* Eine **Gegenprüfung** prüft ein fertiges Ergebnis. Wer sie in die Kette
  hängt, macht sie zum **Erzeuger** des Ergebnisses — dann prüft sie sich
  selbst.
* Das Potential ist die Signalbewertung (Stufe 11). Ein LLM-Votum daneben
  wäre eine **zweite, konkurrierende** Bewertung — genau die Vermischung,
  die dieser Umbau beseitigen soll.
* Ein LLM-Nein ist eine **Prognose**, kein gemessener Beitrag. Es dürfte
  nach Regel 4 ohnehin nichts auslösen, solange es nicht gegen den Zufall
  gemessen ist (Regelwerk: *„Die LLM-Ebene muss den Zufall messbar
  schlagen"*).

### 8.4 Die drei Änderungen, die aufgenommen werden

| # | Änderung | Größe | Warum |
|---|---|---|---|
| **G-a** | **Das Vokabular vereinheitlichen.** G liefert heute `ja` / `nein` / `konsistent` / `unklar` durcheinander | klein | ⚠️ **Vorbedingung für alles Weitere.** Solange vier Wörter zwei Bedeutungen tragen, ist jede Auswertung ihrer Quote eine Schätzung. Kein Filter, keine Messung, kein Bericht darf vorher gebaut werden |
| **G-b** | **Den Widerspruch sichtbar machen, nicht wirksam.** Ein Widerspruch bekommt eine eigene, benannte Zeile am Kopf des Gegenprüfungsblocks — nicht am Ende, wo er heute untergeht | klein | Der Nutzer soll ihn sehen und selbst entscheiden. Das ist die Rolle einer Gegenprüfung |
| **G-c** | **Die Trefferbilanz von G führen.** Je Widerspruch wird der Ausgang mitgeschrieben: hatte G recht? | mittel | ⚠️ **Erst danach ist die Frage „soll G sperren dürfen?" überhaupt beantwortbar.** Vorher wäre jede Sperre eine Vermutung. Maßstab: der quotengleiche Zufall, nicht das Bauchgefühl |

⚠️ **G-c ist ausdrücklich KEIN Vorgriff auf eine Sperre.** Es ist die
Messung, die eine spätere Entscheidung erst erlaubt — und sie kann genauso
gut ergeben, dass G nichts sperren darf.

### 8.5 Der offene Punkt daneben (G2)

`simuliere_kette.py` meldet ihn seit dem 31.08. als **bekannten Zustand,
nicht als Fehler:** *„Rolle G urteilt auf BTC-weiter Grundlage."* G bekommt
das Marktlagebild, aber nicht immer die asset-eigene Faktenlage. Das gehört
zu G-a/G-b, nicht zur Signalbewertung.

---

## 9. ⚠️⚠️ DER HEBEL — die Inkonsistenz, nachgeschlagen

**Nutzerfrage 01.09.:** *„Wir reden schon seit drei Tagen, wie wir Hebel
umsetzen wollen, und dann fehlt das Wichtigste."*

### 9.1 Der Befund, in einem Satz

**Die Bewertung hat keine Instrument-Achse und keine Horizont-Achse.** Am
Code belegt (01.09.):

    _gilt(b, klasse, strategie, richtung)      DREI Achsen
    Beitrag(klassen, strategien, richtungen)   kein `instrumente`
                                               kein `horizont`
    basisrate(crv) = 1/(1+CRV)                 kennt keinen Horizont
    potential.rechne(..., instrument=...)      reicht es an HA.pruefe und
                                               an die ANZEIGE - nie an _gilt

**Folge, gemessen:** `spot × einstieg` und `hebel × einstieg` liefern bei
gleicher Lage **exakt dieselbe Zahl** (+0,119100 R). Die zweite Zelle kann
sich von der ersten **nicht unterscheiden** — nicht weil die Messung fehlt,
sondern weil es keinen Ort gibt, an dem ein zellen-eigener Wert stünde.

⚠️ **Das ist derselbe Fehlertyp wie S6b eine Ebene tiefer:** `instrument`
wird mitgeführt, aber an der entscheidenden Stelle nicht gefragt.

### 9.2 ⚠️ Es stand längst da — an drei Stellen

| Wo | Wann | Was dort steht |
|---|---|---|
| `Befund_Instrument_nach_S6b_28_08.md` Abschnitt 4 | **28.08.** | *„…daraus der kleine Hebel (Median 1,10) — und daraus, dass **‚spot' und ‚hebel' dasselbe Signal mit zwei Etiketten sind**."* |
| dieser Plan, Abschnitt **5.2** | **28.08.** | *„Das Instrument fällt weiterhin aus dem Stopabstand an… Für die 40 taktischen Krypto-Assets bleibt es dabei: **Der Stop bestimmt, ob es ein Hebel-Trade wird**."* |
| dieser Plan, Abschnitt **6** | **28.08.** | Schritt **5 „Zweite Frage für V1 (L2)"** — *groß*, Vorbedingung Schritte 2 und 3, **bis heute offen** |

**Die Lücke war also nicht unbekannt — sie war als bewusster Kompromiss
notiert, mit einer Bedingung daran:**

> *„Das ist vertretbar, **wenn die Kostenrechnung dem Etikett folgt (L3)**.
> Es ist **nicht** vertretbar, solange 35 % der Signale ohne
> Finanzierungskosten bewertet werden."*

### 9.3 ⚠️⚠️ Und genau diese Bedingung war NICHT erfüllt

**L3 galt seit dem 28.08. als erledigt (I-1a).** Am 01.09. nachgerechnet:
Die Weiche funktionierte, das Ziel-Tier nicht. Dem Hebel-Tier fehlte die
**Handelsgebühr auf das Nominal** vollständig:

| Stop 5 %, 3 Tage | gerechnet bis 01.09. | richtig |
|---|---|---|
| Spot | 0,6000 R | 0,6000 R |
| Hebel 3 | **0,1120 R** | **0,7120 R** |

**Ein Hebeltrade erschien siebenmal billiger als derselbe Trade in Spot.**
Der Kompromiss aus 5.2 stand damit **vier Tage lang auf einer Bedingung, die
er nicht erfüllte** — und zwar in die gefährliche Richtung: die
Wirtschaftlichkeit des Hebels wurde systematisch zu gut dargestellt.

✔ **Repariert 01.09.** (Commit „Trennung Bewertung/Wirtschaftlichkeit"):
Handel + Finanzierung, beide Gebührensätze getrennt, Suite 1.876 grün,
Kettensimulation weist es in der fertigen Mail nach.

### 9.4 Warum es mir nicht aufgefallen ist — die ehrliche Auskunft

**Vier Gründe, keiner davon eine Entschuldigung:**

1. **Ich habe die Tabelle gelesen, nicht den Fließtext darüber.** Am 31.08.
   habe ich Abschnitt 6 zitiert (Schritte 3/4/5) und Schritt 3 = L3
   geprüft. Der Kompromiss und seine **Bedingung** stehen in 5.2, in Prosa,
   direkt über der Tabelle. Ein Plan wird nicht an seiner Übersicht gelesen.

2. **Ich habe gefragt „ist es gebaut?" statt „stimmt die Zahl?".** Die
   Antwort auf L3 lautete *„erledigt, I-1a"* — nach einem Blick auf die
   Weiche. Mein Verifikationsaufruf lief in einen Signaturfehler, und ich
   bin zur nächsten Frage übergegangen, statt ihn zu Ende zu bringen.
   ⚠️ **Genau die stehende Vorgabe: *„gebaut" heißt nicht „geprüft".***

3. **Die eigene Suite hat die falsche Antwort bestätigt.** Die Prüfung
   „Hebel kostet mehr als Spot" stand auf **30 Tagen** — der einzigen
   Stufe, bei der die aufgelaufene Finanzierung die fehlende
   Handelsgebühr übersteigt. Bei der geplanten Hebel-Haltedauer von 1–3
   Tagen wäre sie rot gewesen. Ein grüner Haken auf einem einzigen
   Parameterwert ist kein Nachweis.

4. **`Befund_Instrument_nach_S6b_28_08.md` habe ich in drei Tagen
   Hebel-Arbeit nie geöffnet.** Ich habe mit `grep` gesucht — und `grep`
   findet, was man schon vermutet. ⚠️ Es gibt eine stehende Regel
   *„`zeige_modulkarte.py` vor jeder Ausarbeitung"* für **Module**. Für
   **Dokumente** gibt es keine. Daraus folgt Regel **R-R10** unten.

### 9.5 Was zu tun ist — und in welcher Reihenfolge

| # | | Vorbedingung | Größe |
|---|---|---|---|

⚠️⚠️ **H-1 IST GELAUFEN — UND DIE FRAGE WAR UMZUSTELLEN (01.09.2026).**
Vollstaendig: `Fakten_Entscheidungsmappe.md` **F-164**.

Die oben notierte Fassung (*„traegt sich ein gehebelter Trade mit engem
Stop?"*) ist **erstens beantwortet** — die Kopplung Stopabstand/
Tragfaehigkeit steht seit dem 22.08. je Signal in der Mail — und
**zweitens eine WIRTSCHAFTLICHKEITSfrage**, die die Bewertung nach
stehender Vorgabe nicht entscheiden darf.

**Nutzerkorrektur:** *„Hebel steil-kurz, Spot flach-lang."* Gemessen wurde
deshalb: trennt eine Groesse zum Bewertungszeitpunkt, ob der Ertrag auf
H3 hoeher ist als auf H20? **916.021 Anker, 7.269 Kalendertage, sechs
vorab benannte Kandidaten: KEINER trennt.**

⚠️ **Aufloesungsgrenze:** die Kunstgroesse wird gefunden (+0,8330 R),
ein aufgepflanzter Effekt von +0,05 R nicht. **Grosse Effekte sind
ausgeschlossen, kleine nicht.**

**Und der Kern, arithmetisch:** R ist `Nominal x stop_rel`, der Hebel
kuerzt sich heraus. **Gebuehrenfrei sind Hebel und Spot dasselbe
Geschaeft.** Nur ueber den HORIZONT kann die Bewertung das Instrument
ueberhaupt waehlen — und dort trennt nichts.

**Folge fuer H-3:** nicht begruendbar. Es gaebe nichts zu hinterlegen.
**5.2 steht damit vorerst als endgueltige Antwort, nicht als Kompromiss.**
**H-4 (Terminmarkt) ist der naechste und aussichtsreichste Weg.**

| **H-1** | ⚠️ **Die Messung nachholen, die 5.2 selbst verlangt hat:** *„Bei einem Stop von 2 % kostet allein die Referenzgebühr 0,30 R — mehr als der gesamte gemessene Vorsprung. Ein gehebelter Trade mit engem Stop trägt sich rechnerisch nicht, bevor er begonnen hat. **Das wäre zu messen, bevor Aufwand in seine Verwaltung fließt.**"* | ✔ L3 jetzt korrekt | klein |
| **H-2** | **Entscheiden, ob die Bewertung eine Instrument-Achse bekommt** — oder ob der Hebel eine reine **Ausführungsfrage** bleibt (dann ist 5.2 die endgültige Antwort, nicht ein Kompromiss) | H-1 | ⚠️ **Nutzerentscheidung** |
| **H-3** | Falls ja: **`Beitrag` um `horizonte` erweitern**, die H1–H20-Messung je Horizont eintragen, `potential.rechne` einen Horizont annehmen lassen | H-2 | groß |
| **H-4** | ⚠️ **KORRIGIERT — siehe 9.6.** Die Terminmarkt-**Rohgrößen** als Beitragskandidaten messen (OI, OI-Veränderung, OI-Divergenz, Funding-Extrema). Meine erste Fassung wollte den **Screening-Score validieren** — das wäre die Vermischung von Alt- und Neubestand | H-2 | mittel |

⚠️ **H-1 kann H-3 überflüssig machen** — dieselbe Logik, mit der Abschnitt 6
schon Schritt 2 vor Schritt 5 gestellt hat. **Erst messen, dann bauen.**

⚠️ **Zur Datenlage:** Die Terminmarkt-Historie für H-4 liegt auf dem
**Notebook**, nicht am Desktop. Lokal geprüft 01.09.:
`open_interest_snapshot` **227 Zeilen**, `hebel_triggers` **49**. Die Zahlen
82.655 / 227.395 stammen aus der NB-Produktion. **H-4 braucht einen Pull
oder läuft am NB.**

### 9.6 ⚠️⚠️ ALT UND NEU — die Grenze, bevor irgendetwas gemessen wird

**Nutzervorgabe 01.09., während dieser Recherche:** *„Ganz wichtig zu deiner
Recherche — genau trennen, was Alt- und Neubestand ist, damit keine
Vermischung erfolgt."*

**Die Grenze, am Code festgestellt (01.09.):**

| | ALTBESTAND | NEUBESTAND |
|---|---|---|
| **Erzeugung** | `hebel_screening.py` → `hebel_triggers` | `rollen_lauf.fuehre_lauf` → die elf Trichterstufen |
| **Bewertung** | Score 0–100, Schwelle **70** | `potential.rechne` → Schwelle **0,080 R** |
| **Signalbau** | `hebel_pipeline.generate_hebel_signal` | `rollen_lauf` → `signals` |
| **Aufrufer** | `budget_allocator` (der **einzige**) | `rollen_job.fuehre_umlauf` |
| **Tabellen** | `hebel_signals`, `hebel_positions`, `hebel_triggers` | `signals` (mit `instrument` seit 31.08.) |
| **Anzeige** | `ui/hebel_view` (Historie, read-only) | `signals_view` |

**Der Laufzeitzustand — und er ist NICHT „alles tot":**

    hebel_screening_job     laeuft ALLE 15 MINUTEN eigenstaendig weiter
                            (background.py:3983) -> hebel_triggers waechst
    budget_allocator        UEBERSPRUNGEN seit 22.08. (background.py:3373),
                            sobald EINE Gruppe die neue Kette bedient
    generate_hebel_signal   damit unerreichbar - letztes Signal 10.08.

⚠️ **Das Screening ist also lebendig, seine Verwertung tot.** Die Module
stehen deshalb **nicht** in `zeige_modulkarte.py --tot` — sie haben
Aufrufer, der Pfad wird nur zur Laufzeit übersprungen. **Eine Modulkarte
beantwortet „hat es einen Aufrufer", nicht „läuft es".**

#### ⚠️ Die Korrektur an meinem eigenen Vorschlag H-4

**H-4 lautete zuerst:** *„Die Terminmarkt-Größen validieren, die das
Screening bereits benutzt (OI, Funding-Extrema, Long-Bias)."*

**Das ist genau die Vermischung, vor der der Nutzer warnt.** Der
Screening-Score ist **Altbestand**: eine nie gegen den Zufall gemessene
Konstruktion mit einer eigenen Schwelle (70), aus einer Kette, die es nicht
mehr gibt. Ihn zu „validieren" hieße, ein altes Kriterium zu adeln und in
die neue Bewertung zu heben — und dann wäre die Frage nicht mehr *„trägt
diese Größe?"*, sondern *„war unsere alte Formel gut?"*. Das ist die
Umkehrung der Regel *„Wir messen UNSERE Qualität, nicht den Markt"* in ihre
schlechte Richtung.

**H-4 lautet daher neu:**

> **Die Terminmarkt-ROHGRÖSSEN als Beitragskandidaten messen** — Open
> Interest, seine Veränderung, die OI-Divergenz, Funding-Extrema — nach dem
> Verfahren, mit dem Funding und Turnover aufgenommen wurden: Tagesklammer,
> Placebo-Band, beide Historienhälften, Positivkontrolle **je Horizont**,
> Wirkung als **Regel** (R-R9 anschließend).
>
> ⚠️ **Der Screening-Score ist dabei Hypothesenquelle, nicht Maßstab.** Er
> darf sagen, *welche* Rohgrößen einen Blick wert sind. Er darf nicht
> vorgeben, *wie* sie verrechnet werden, und sein Ergebnis ist kein
> Vergleichswert.

#### ⚠️ Nutzervorgabe 04.09.: das Thema bleibt zu lösen — weitere Kandidaten für die nächste N-17b-Runde

**Nutzerauftrag:** *„Unabhängig davon ist und bleibt das Thema als zu
lösen im Plan. Nur weil es schwierig ist, geben wir nicht auf — in der
Realität werden auch dazu Entscheidungen getroffen. Es kommt auf die
richtigen Indikatoren in der richtigen Lage an."* Vorgeschlagene
Kandidaten, noch nicht gemessen, für N-17b zusätzlich zu den
Terminmarkt-Rohgrößen zu prüfen:

    RSI überverkauft/überkauft   klassisches Umkehr-Signal
    Bodenbildung                 Musterkennung am Kursboden
    BTC führt (Altcoin folgt)    Marktbreite/Leitwert-Verzögerung
    Volumensänderung             Umschlag als Vorlauf-Indikator

⚠️ **Vor der Messung zu klären (dieselbe Vorabfestlegung-Pflicht wie
immer):** die Zielgröße bleibt **Frontloading** (H-4a/b, nicht die
gescheiterte Richtungsgröße aus H-1) — die Frage ist „wie schnell/wie
ausgeprägt", nicht „in welche Richtung". Und: `RSI überverkauft` und
`Bodenbildung` sind KEINE unabhängigen Größen — beide beschreiben
denselben Zustand aus verschiedenen Blickwinkeln; vor der Messung
prüfen, ob sie stark korrelieren (wie es `momentum_kurz`/`schnitt50` in
F-165 taten, ρ=0,364), sonst zählt ein Effekt doppelt.

#### ⚠️⚠️ N-17c — DIE VORABFESTLEGUNG (04.09.2026), geschrieben BEVOR gerechnet wird

**Nutzerkorrektur, die diesen Schritt ausgelöst hat:** *„1. der Wert bringt
etwas ok, wissen wir was die Aussage ist, gibt es Schwellen, etc.
2. du bist immer in der Messung, gehe in unsere Dokumente wie wir
Bewertungen integriert haben."*

##### Die Lücke, die geschlossen werden soll

9.6 schreibt für H-4 *„das Verfahren, mit dem Funding und Turnover
aufgenommen wurden"* vor. Dieses Verfahren hat **drei** Schritte; bei den
Frontloading-Kandidaten (F-165, F-209) ist nur der erste gegangen:

| Schritt | Werkzeug | Funding/Turnover | Frontloading-Kandidaten |
|---|---|---|---|
| 1 Wirkung als Regel | `messe_regel_wirksamkeit` | ✔ | ✔ (F-165/F-209) |
| 2 Beitragspunkte je Fünftel | `rechne_*_beitrag.py` | ✔ | ✖ **fehlt** |
| 3 Schwelle kalibrieren | `messe_schwelle_kalibrierung.py` | ✔ | ✖ **fehlt** |

⚠️⚠️ **Der Grund, warum Schritt 2 fehlt, ist inhaltlich und nicht
Bequemlichkeit:** die Umrechnungsformel `d(quote) = d(Potential)/(1+CRV)`
setzt eine Wirkung **in R** voraus. `messe_form_kurz_gegen_lang._ziel()`
liefert bei `ZIEL="frontloading"` aber den **Frontloading-Anteil** (0..1,
„wie viel der Bewegung fällt in die ersten drei Tage"), nicht die
Trade-Rendite. **Die Beschriftung „R" in F-165s und F-209s Tabellen ist
ein Überbleibsel aus der H-1-Fassung (`R_kurz − R_lang`) und keine
Einheit** — sie ist bei der Umstellung auf Frontloading nicht mitgezogen
worden. Es gibt daher bis heute **keine Brücke** von „Frontloading trägt"
zu einer Potential- oder Schwellenaussage.

##### Die zwei Aussagen, die nicht dasselbe sind — und das ist der Kern

| | sagt | taugt für |
|---|---|---|
| **Frontloading trägt** | die Bewegung ist früh konzentriert — *wie schnell*, nicht *wohin* | die **Horizontwahl** (kurz statt lang) |
| **R-Beitrag trägt** | der Ausgang ist besser | das **Potential** und damit eine **Schwelle** |

F-165/F-209 haben ausschließlich die erste gemessen. Für eine Bewertung
im Sinne des übergeordneten Ziels wird die zweite gebraucht.

##### Was gemessen wird

Für **jeden Kandidaten, der auf Frontloading trägt**, die Beitragstabelle
in **echten R** auf dem **Hebel-Horizont**, nach exakt dem Verfahren von
`rechne_funding_beitrag.py` / `rechne_oi_beitrag.py` — Tagesklammer,
Fünftel je Kalendertag, Median je Fünftel, Mittel über die Tage,
`faktor = 1/(1+CRV)`, In-Sample-**Schrumpfung auf die Hälfte**.

    Horizonte     H3 (das kurze Fenster aus F-165) UND H2 (die Geometrie,
                  auf der N-17a/F-203 kalibriert hat) - zwei Zellen, damit
                  die Zahl gegen die Horizontwahl robust ist
    Kandidaten    turnover · vola · momentum_kurz · schnitt50 · rsi ·
                  oi_aenderung · funding_extrem   (die auf Frontloading
                  tragenden, `oben`-Richtung)
    Kontrolle     `zufall` läuft mit - er MUSS eine flache Tabelle liefern

⚠️ **Der Suchpreis ist benannt:** 7 Kandidaten × 2 Horizonte = **14 Zellen**
(Methodik 2.49). Die Entscheidung hängt an **turnover** — dem stärksten und
am wenigsten redundanten Fund; die übrigen laufen als Einordnung mit und
dürfen den Befund nicht allein tragen.

⚠️ **`turnover` und `funding_extrem` sind teilweise Wiederholung:**
`rechne_turnover_beitrag.py --horizont 2` ist in F-203 bereits gelaufen
(+0,34/+0,08/+0,15/−0,25/−0,32). Diese Zahl dient hier als **Kontrolle**:
weicht sie ab, stimmt etwas am Aufbau, nicht am Befund.

##### ⚠️ Vorab festgelegt — was als Befund gilt

    NUTZBAR        die Stufen sind MONOTON über die fünf Fünftel
                   UND die Spanne (Fünftel 0 gegen 4) ist größer als null
                   UND die Kontrollgröße `zufall` bleibt flach
    NICHT NUTZBAR  sonst - dann wird NICHT registriert und KEINE Schwelle
                   gerechnet

⚠️ Genau diese Monotonie-Bedingung ist am 31.08. beim Schnittabstand
gefallen (+1,27/+1,59/…) und wurde damals **trotzdem** registriert. Sie
steht hier, damit das nicht ein drittes Mal passiert.

##### ⚠️ Und was diese Messung ausdrücklich NICHT entscheidet

1. **Nicht, ob registriert wird.** R-R9 verlangt bei jedem Beitragswechsel
   eine Neukalibrierung der Schwelle; die Vorgabe (heute 0,080) ist eine
   **Nutzerentscheidung**. Diese Messung liefert nur die Zahlen dafür.
2. **Nicht den Gabelpunkt aus F-164.** Selbst tragfähige Stufen machen den
   Hebel nicht automatisch zu einer Bewertungsfrage — H-2 bleibt offen.
3. **Nicht die Richtung.** Alle Kandidaten sagen Ausmaß/Tempo, keiner sagt
   wohin (F-165, unverändert gültig).

##### Die ehrliche Erwartung, vorab notiert

F-203 hat für Funding/Turnover auf H2 bereits gezeigt: die Spannen sind
dort **6–7× kleiner** als auf H20, und die gemeinsame Schwellenkalibrierung
verlor jede Trennschärfe. **Ein ähnlich ernüchterndes Ergebnis ist der
wahrscheinlichere Ausgang, kein Ausreißer.** Der Wert der Messung liegt
darin, die Aussage *belegt* statt *vermutet* zu machen — und die
Beitragstabelle ist die einzige Form, in der dieses Projekt eine
Bewertung überhaupt aufnehmen kann.

##### Betriebsrahmen

Reine lokale SQLite-Lesevorgänge (`data/messdaten.db`,
`data/funding_historie.db`, `data/onchain_historie.db`,
`data/terminmarkt_historie.db`) — **keine API-Abrufe**, kein Kontingent
betroffen. Werkzeug: bestehende `rechne_*_beitrag.py` wo vorhanden, sonst
ein gemeinsames neues, das dieselbe Rechnung für die übrigen Kandidaten
ausführt (keine zweite Kopie der Fünftel-Logik).

#### ⚠️⚠️ N-17d — TEMPO × TRENDRICHTUNG, die Vorabfestlegung (04.09.2026)

**Nutzerfrage, die diesen Schritt ausgelöst hat:** *„1. haben wir eine
Aussage über Tempo und Richtung, ja wollen wir, check. 2. in Kombination
mit einer Trendrichtung hoch, seitwärts, runter ist das unser Ziel. haben
wir, eigentlich ja? was ist das Problem hierbei genau?"* — und die
Nachschärfung: *„für die kurzen Zeiträume sollten auch die Mess- und
Analyseparameter sauber kalibriert werden, 0 bis 3 oder 5 Tage."*

##### Warum die Frage bisher nicht beantwortet war

Beide Hälften existieren, aber nicht als kombinierbare Teile:

- **Tempo:** gemessen (F-165/F-209), aber **absichtlich richtungsblind** —
  wir rechnen mit Beträgen, weil die vorzeichenbehaftete Fassung (H-1)
  nichts fand. „Hohes Tempo" schließt „schneller Absturz" ein.
- **Richtung:** Das System führt **kein Trendetikett mehr**. Es wurde am
  16.08. entfernt (`lagebeschreibung._struktur`), weil „aufwärts" nur zu
  **42 %** mit der 60-Tage-Bewegung übereinstimmte — *„kaum besser als ein
  Münzwurf"*. Was bleibt, ist das Gesamturteil der Kette (48,2 %
  Trefferquote), das sich nicht in einen Faktor zerlegen lässt.

**Die Kombination ist also nie gemessen worden** — nicht aus Versäumnis,
sondern weil eine der beiden Hälften als Faktor gar nicht existiert.

##### ⚠️⚠️ Der Kalibrierungsfehler in N-17c, vom Nutzer gefunden

Die tatsächliche Handelsdauer ist **gemessen** (F-202, 239 entschiedene
Trades): **Median 2,0 Tage**, Mittel 2,6 — TP und SL identisch. Das System
plante 1,2–2,1 Tage. Dagegen die Rückblicke, mit denen N-17c gemessen hat:

| Größe | Rückblick | Verhältnis zur Handelsdauer |
|---|---|---|
| `vola` (Normierung) | 250 Tage | 125× |
| Trendrichtung (60-Tage) | 60 Tage | **30×** |
| `schnitt50` | 50 Tage | **25×** |
| `rsi`, `adx` | 14 Tage | 7× |
| `momentum_kurz` | 3 Tage | **1,5×** ✔ |

⚠️ **Und der Kandidat mit der größten Wirkung war ausgerechnet der
einzige, dessen Parameter passt** — `momentum_kurz`, Spanne 1,29 (H2) und
1,39 (H3) gegen `turnover` 0,75/1,11. Er fiel in N-17c nur durch, weil ich
ausschließlich auf die Monotonie-**Form** geschaut habe und nicht auf die
**Größe**. Das war zu schematisch: seine Gestalt ist ein **Schalter**
(oberstes Fünftel −1,07/−1,19, auf beiden Horizonten konsistent) — genau
die Form, die bei `oi_aenderung` als Sperre gebaut wurde (F-168/N-14).

##### ⚠️⚠️ Was die Fachrecherche ergeben hat — und sie widerspricht meiner Arbeitshypothese

Externe Recherche 04.09. (Volltexte, peer-reviewed bevorzugt). Vier
Befunde, die die Messung umsteuern:

1. **Die Tempo-Hypothese steht GEGEN die Literatur.** Trend-/Momentum­
   effekte sind **stärker in ruhigen, nicht in schnellen Phasen**. Für
   Krypto direkt einschlägig (CTREND, *JFQA* 2025, >3.000 Coins):
   Long-Short **5,46 %/Woche bei niedriger** gegen **2,27 % bei hoher**
   Marktvolatilität. Ebenso Cooper/Gutierrez/Hameed (*JF* 2004),
   Moreira/Muir (*JF* 2017). ⚠️ **Die Beweislast liegt damit bei uns**,
   wenn wir „schnell = besser" behaupten.
2. **Mein `momentum_kurz`-Nebenbefund IST der Lehrbuchbefund.**
   Kurzfrist-Umkehr: Lehmann (1990), Jegadeesh (1990); in Krypto
   repliziert (CTREND `sma_5d`: **−2,90 %/Woche**, t = −3,35). Was kurz
   stark gestiegen ist, läuft kurz darauf schlechter. **Das ist keine
   Zufallsfindung, sondern erwartbar** — und es erklärt die Schalterform.
3. **DIE literaturgestützte Kombination ist Trend × TURNOVER, nicht Trend
   × Volatilität.** Lee/Swaminathan (*JF* 2000, „Momentum Life Cycle"):
   **bei hohem Turnover kippt Umkehr in Fortsetzung.** Dazu passt, dass
   die Krypto-Tagesumkehr liquiditätsabhängig ist — die größten Coins
   zeigen Momentum, das breite Feld Umkehr. **Und es passt zu unserem
   eigenen Befund** (`n13_1_volumenanteil_traegt`, F-205).
4. **Drei unserer Kandidaten haben KEINE Validierung.** Efficiency Ratio
   (Kaufman), Choppiness Index und Varianzverhältnis sind Praktiker- bzw.
   Testgrößen ohne Wirkungsnachweis als Renditeprädiktor; das
   Varianzverhältnis (Lo/MacKinlay) ist ein **Random-Walk-Test, kein
   Signal**. Sie waren in F-165 als „aus der Standardliteratur" geführt —
   **das war für diese drei zu großzügig**.

**Realistische Effektgröße laut Literatur: R² 1–3 %, also 1–3
Prozentpunkte Trefferquote.** ⚠️ Damit ist unser N-17c-Ergebnis
(turnover H3: +0,51 Punkte) **kein Messversagen, sondern der erwartete
Größenbereich** — und die Schwelle 0,080 R verlangt mit +2,67 Punkten
mehr, als die Literatur für einen Einzelfaktor überhaupt hergibt.

5. **Für Hebel-Timing gibt es keine Literatur.** Kein peer-reviewed
   Kriterium, wann ein *kurzfristiger gehebelter* Einstieg einem
   ungehebelten überlegen ist. Hebel wird als Positionsgrößen- und
   Kapitaleffizienzfrage behandelt (Vola-Targeting, Kelly), nicht als
   Signal. ⚠️ Frazzini/Pedersen (*JFE* 2014) zeigen sogar die
   Gegenrichtung: eingebauter Hebel kostet eine Prämie. **Wenn wir eine
   Regel wollen, müssen wir sie selbst messen — es gibt nichts, worauf
   man sich stützen könnte.**

##### Was gemessen wird — EINE Haupthypothese, vorab benannt

> **H-N17d:** Die Kurzfrist-Umkehr (oberstes Fünftel `momentum_kurz` →
> schlechterer Ausgang) ist **bei niedrigem Turnover stark und kippt bei
> hohem Turnover** — Lee/Swaminathans Momentum Life Cycle, auf unserem
> Horizont.

    Zielgroesse   R auf H2, VORZEICHENBEHAFTET  (nicht Frontloading -
                  wir wollen "schnell UND richtig", nicht nur "schnell")
    Horizont      H2 - die gemessene Median-Haltedauer (F-202), nicht H20
    Achse A       momentum_kurz (3 Tage, horizontproportional)
    Achse B       turnover  (die literaturgestuetzte Schicht)
    Verfahren     Schichtentest `messe_kandidaten_als_regel.geschichtet` -
                  dasselbe Werkzeug, mit dem H-4c geprueft wurde, ob
                  `oi_aenderung` nur Funding mit Umweg ist
    Kontrolle     `zufall` als Achse A; Negativkontrolle je Schicht

⚠️ **Der Suchpreis: EINE Hypothese, EINE Zelle.** Nicht mehrere Trendmaße
gegen mehrere Schichten — das wäre die Parametersuche, vor der 2.49 warnt,
und bei erwarteten 1–3 Punkten Effekt würde sie zuverlässig Scheinbefunde
liefern.

##### ⚠️ Nachrangig und getrennt zu halten

Die **Parameter-Neukalibrierung** (Trendkontext 10 statt 60 Tage, RSI
kürzer) ist berechtigt, aber sie ist ein **zweiter Block** und wird
getrennt ausgewiesen — sonst ist hinterher nicht zu trennen, ob ein
Befund von der Hypothese oder von der neuen Parameterwahl kommt.

##### Vorab festgelegt — was als Befund gilt

    TRAEGT       die Umkehr ist in den Turnover-Schichten UNTERSCHIEDLICH
                 stark, die Differenz ist ausserhalb ihres Bandes, UND
                 die Kontrollgroesse bleibt still
    TRAEGT NICHT sonst - dann ist Tempo x Richtung fuer uns erledigt, und
                 der Gabelpunkt H-2 ist ohne diese Option zu entscheiden

⚠️ **Erwartung, ehrlich vorab:** Bei 1–3 Punkten realistischer Effektgröße
und einer Schwelle, die 2,67 verlangt, ist auch ein *positiver* Befund
wahrscheinlich **zu klein für eine Auslösung**. Der Wert läge dann darin,
ihn als **Sperre** (Schalterform) zu prüfen — nicht als Beitrag.

##### Betriebsrahmen

Nur lokale SQLite-Lesevorgänge, keine API-Abrufe.

#### Was aus dem Altbestand übernommen werden darf — und was nicht

| | Umgang |
|---|---|
| `hebel_triggers` als **Rohdaten** (OI-Reihen, Funding) | ✔ **verwendbar** — es sind Messwerte, keine Urteile |
| `hebel_triggers.score` und die Schwelle 70 | ✖ **nicht verwendbar** als Kriterium — nie validiert |
| `hebel_positions` (188, alle geschlossen) | ⚠️ **nur als Nutzerverhalten** — nicht als Systemempfehlung (Abschnitt 4, Fallstrick F5) |
| `hebel_signals` (letztes 10.08.) | ✔ Historie, read-only (Abschnitt 7) |
| Die Kostensätze `_KOSTEN_HEBEL_*` | ✔ **gemeinsam genutzt** — an 104 Positionen belegt, gilt für beide Ketten |

⚠️ **Die letzte Zeile ist die eigentliche Gefahrenstelle.**
`backward_tracking.kosten_in_r` wird von **beiden** Ketten benutzt. Genau
dort saß der Fehler vom 01.09. — eine Änderung dort wirkt in Altbestand und
Neubestand zugleich. **Jede Änderung an gemeinsamen Modulen ist gegen beide
Ketten zu prüfen**, nicht nur gegen die neue.

### 9.7 ⚠️ Eine neue stehende Regel

| | |
|---|---|
| **R-R10** | **Vor jeder Ausarbeitung zu einem Thema: die Dokumente zum Thema AUFLISTEN und die drei dichtesten ÖFFNEN — nicht greppen.** `grep` findet nur die eigene Vermutung; ein Befunddokument, dessen Kernsatz man nicht erwartet, findet es nie. Der Hebel-Fall hat vier Tage gekostet: der Satz *„spot und hebel sind dasselbe Signal mit zwei Etiketten"* stand seit dem 28.08. da. **Das ist die Doku-Entsprechung zu `zeige_modulkarte.py` (F7).** |

---

---

## ⚠️⚠️ N-14: DIE OI-SPERRE — der erste Terminmarkt-Wert neben Funding (02.09.2026)

**Grundlage:** F-168. `oi_aenderung` trägt auf breiter Basis (126.491 Anker,
117 Symbole, 1.702 Tage) mit **+0,0145 R**, überlappt praktisch nicht mit
Funding (Schichtentest +0,0136 R) und ist damit ein **eigener** Beitrag.

### ⚠️ Die Form steht schon fest — und sie ist NICHT die erwartete

Die vorab gesetzte Monotonie-Bedingung ist **gefallen**. Belastbar ist
allein das oberste Fünftel (−0,89 Punkte, [−1,32 .. −0,44]); die vier
übrigen sind einzeln nicht von null zu trennen.

> **`oi_aenderung` gehört als SPERRE in eine Trichterstufe, nicht als
> abgestufter Beitrag in `wahrscheinlichkeit.BEITRAEGE`.**

Wer sie trotzdem als fünfstufigen Beitrag registriert, registriert drei
Zahlen, die nichts bedeuten — derselbe Fehler wie beim Schnittabstand am
31.08.

### N-14a — Wo die Stufe hingehört

Der Trichter kennt eine ausdrückliche Regel dafür: *eine Bremse, die
**keinen** Modellaufruf kostet, bekommt eine **eigene** Stufe* — so sind
`anlass` (16.08.) und `auswahl` (23.08.) entstanden. Die OI-Sperre kostet
keinen Aufruf. Sie gehört damit **vor `urteil`**, neben `auswahl`:

    auswahl  ->  positionierung  ->  wiederholung  ->  urteil
                 (NEU)

⚠️ **Nicht in `auswahl` hineinlegen.** Dort steht der Rangplatz, und der
wählt aus, *welche* Werte beurteilt werden. Die OI-Sperre sagt etwas
anderes: *dieser Zeitpunkt ist überhitzt*. Zusammengelegt wäre hinterher
nicht mehr zu trennen, ob ein Wert nicht gut genug war oder ob der
Zeitpunkt schlecht war — genau die Vermischung, für die `anlass` und
`auswahl` eigene Stufen bekommen haben.

### N-14b — Was vorher zu messen ist

| | Frage | warum |
|---|---|---|
| 1 | **Wieviele Empfehlungen bleiben übrig?** | Die Regel sperrt 20,6 % der Anker. Was sie im **laufenden Trichter** sperrt, ist eine andere Zahl — dort sind schon zehn Stufen davor. `simuliere_kette.py` muss das zeigen, nicht die Messung. |
| 2 | **Wieviel sperrt sie zusätzlich zu Funding?** | Gemessen: beide zusammen 36,9 % gegen 20,6 % allein — praktisch keine Überlappung (F-168, Abschnitt E). |
| 3 | **Was passiert mit den 12 Werten ohne OI?** | Nach dem Muster von G-6: **drei Zustände** (`vermessen` / `bewertbar` / `trägt`). Ein Wert ohne OI-Daten darf nicht gesperrt werden — er ist *nicht vermessen*, und das ist keine Aussage über den Zeitpunkt. |

⚠️ **Punkt 3 ist der, an dem G-6 am 31.08. schon einmal gescheitert ist:**
die Stufe sperrte vier von fünf Assetklassen nach Datenlage, die Suite war
grün, und die Produktion lieferte **0 Signale**.

### N-14c — ⚠️ R-R9 gilt hier NICHT, und das ist zu begründen

R-R9 verlangt bei jedem Beitragswechsel eine Neukalibrierung der Schwelle,
*„sonst kippt das System"* — weil jeder zusätzliche positive Beitrag den
Filter **durchlässiger** macht. Eine **Sperre** ist kein Summand im
Potential. Sie verschiebt keine Schwelle, sondern entfernt Einstiege.
Die Wirkrichtung ist umgekehrt: das System wird **strenger**.

**Was trotzdem gemessen werden muss, ist die Durchlassmenge** (N-14b.1) —
eine Stufe, die zu viel wegnimmt, ist genauso ein Fehler wie eine, die zu
wenig nimmt.

### N-14d — ⚠️ Die Größe wird BEREITS gerechnet und fließt nirgendwohin

`hebel_screening.compute_oi_change_pct()` läuft im 15-Minuten-Takt und
schreibt `hebel_triggers.oi_change_pct_lookback`. Sie geht ausschließlich in
den Hebelzweig — und der ist seit dem 10.08. aufgelöst (Kapitel 9).

| | |
|---|---|
| ✔ **verwendbar** | die **Rohgröße** `compute_oi_change_pct` — sie ist ein Messwert, kein Urteil (Kapitel 9.6, erste Zeile der Übernahmetabelle) |
| ✖ **nicht verwendbar** | die Schwelle `schwelle_prozent` und `score_trendfolge` — nie validiert, und F-168 hat eine **andere** Form gemessen (Querschnittsrang je Tag, nicht absolute Prozentschwelle) |

⚠️ **Die Form ist der Unterschied.** Das Screening fragt *„hat sich der OI um
mehr als X % bewegt?"* — ein absoluter Wert ohne Tagesklammer. Gemessen
wurde *„liegt der Wert heute im obersten Fünftel aller Werte"* — ein
Querschnittsrang. Das sind zwei verschiedene Größen; die alte Schwelle
belegt nichts über die neue.

### N-14e — Die Einschränkungen, die mitzuführen sind

1. **19 Blöcke statt 20** (Methodik 2.95). Das Archiv beginnt für alle
   Altcoins am 2021-12-01; die Blockgröße wurde **nicht** gesenkt.
   Entlastend: sechs stille Negativkontrollen, beide Hälften tragen,
   beide Positivkontrollen feuern.
2. **Abdeckung 32 von 44 Watchlist-Werten** (72,7 %; Funding 36).
3. **In-sample kalibriert.**

### ✔ N-14 IST GEBAUT (02.09.2026) — und was dabei NICHT gezeigt werden konnte

| | |
|---|---|
| **Stufe** | `terminmarkt` — „OI-Aufbau nicht im obersten Fünftel", zwischen `auswahl` und `wiederholung`. Der Trichter hat jetzt **zwölf** Stufen |
| **Daten** | `marktrang.oi_werte()` — `openInterestHist period=1d limit=2`, **122 von 122 Symbolen in 35,8 s**, Gewicht 122 gegen 2400/min. Tagesspeicher, weil der Wert sich nur einmal je UTC-Tag ändert |
| **Messbasis** | Vereinigung beider Terminmarkt-Tabellen = **122 Symbole**; davon 32 aus der Watchlist |
| **Prüfungen** | Paket „Terminmarkt", **16 Prüfungen**; Suite **1928 bei 0 FEHL** |
| **Wirkungsnachweis** | `simuliere_kette.py --nachweis-n14` — sechs Fälle, alle gezeigt |

#### Die drei Zustände, im Lauf nachgewiesen

    A  Fünftel 4, einstieg, kein Bestand   -> GESPERRT      ✔
    B  Fünftel 1                           -> durch         ✔
    C  kein Rang                           -> NOTIZ, durch  ✔
    D  Fünftel 4 MIT Bestand               -> NOTIZ, durch  ✔
    E  Akkumulationslauf                   -> keine Sperre  ✔
    F  gesperrt wird nur, wer Fünftel 4 ohne Bestand hatte  ✔

#### ⚠️ E2: der Strategie-Zweig selbst ist NICHT im Lauf gezeigt

Fall E zeigt weniger, als sein Name verspricht. Die Notiz, die dabei
erscheint, lautet **„Bestand vorhanden"** — es greift die
**Bestands**ausnahme, nicht die Strategieausnahme. Zwei Gründe, beide
strukturell:

1. Kern-Assets sind genau die, die gehalten werden — ETH, SOL und BTC
   haben alle Bestand, und diese Ausnahme steht in der Kette **vor** der
   Strategieprüfung.
2. Die zweite Zelle eines Assets fällt ohnehin an `anlass` (siehe F-169).

Der Zweig ist **strukturell** über den Syntaxbaum geprüft (Suite-Paket
„Terminmarkt": *„nur `einstieg` kann überhaupt gesperrt werden"*). Das ist
weniger als ein Lauf-Nachweis, und es steht hier, statt als Haken verbucht
zu werden.

#### ⚠️ Ein echter Codefehler, den erst die Prüfung fand

`marktrang.saetze()` kehrt früh zurück, wenn Funding, Turnover und
Schnittabstand alle fehlen. Ein Wert, der **nur** einen OI-Rang hat, hätte
die Zeile „für diesen Wert liegt keiner vor" bekommen — falsch, und
womöglich neben einer Sperre, die genau dieser Rang gerade ausgelöst hat.
Die Abfrage kennt jetzt vier Größen.

#### Was NICHT gebaut wurde — und warum

| | |
|---|---|
| ✖ ein abgestufter Beitrag in `wahrscheinlichkeit.BEITRAEGE` | die Monotonie ist gefallen (F-168); belastbar ist allein Fünftel 4 |
| ✖ eine Neukalibrierung der Schwelle | R-R9 gilt für **Beiträge**. Eine Sperre ist kein Summand im Potential — sie macht das System strenger, nicht durchlässiger |
| ✖ ein eigener Sammel-Job für OI | nicht nötig: `openInterestHist` liefert beide Tagespunkte in einem Abruf, eine gespeicherte Reihe wäre ein zweiter Bestand, der veralten kann |

### ✔ N-13-1′ IST GEMESSEN (02.09.2026) — und die Form entscheidet den Einbau

**Vollständig in F-170.** Kurzfassung:

| | |
|---|---|
| **Die rohe Form fällt** | 69,8 % Asset-Anteil gegen 49,7 % beim Maßstab — sie sagt „dieses Asset", nicht „dieser Zeitpunkt" (Regel 3). **Nicht** auf Wirkung gemessen |
| **Die relative Form trägt** | +0,0231 R [+0,0093 .. +0,0368] über 1.026.279 Anker, 578 Symbole, 7.536 Tage, 84 Blöcke |
| **Auf der Zielmenge** | +0,0246 R [+0,0103 .. +0,0393] — 512 Werte **ohne** Turnover |
| **Kein Volatilitäts-Mitläufer** | +0,0184 R bei festgehaltener Volatilität |
| **Die Form für den Einbau** | ⚠️ **SPERRE, kein Regler** — nicht monoton, belastbar allein Fünftel 4 |

### N-13-1′a — Was das für den Einbau bedeutet

Es wäre die **dreizehnte** Trichterstufe, gebaut wie N-14:

    kein Rang     -> NOTIZ, nicht sperren (die drei Zustände)
    Fuenftel 4    -> sperren
    Fuenftel 0-3  -> durchlassen

⚠️ **R-R9 gilt wieder nicht** — eine Sperre ist kein Summand im Potential.

### ⚠️⚠️ N-13-1′b — Was VOR dem Bau zu rechnen ist

**Zwei Sperren nacheinander verengen mehr als eine.** N-14 sperrt 20,6 %,
diese Stufe 20,7 %. Wären sie unabhängig, blieben nach beiden noch 63 %.
Was sie im **laufenden Trichter** wegnehmen, ist eine andere Zahl — dort
stehen zwölf Stufen davor.

> **Vor dem Bau ist die Durchlassmenge zu messen** (`simuliere_kette.py`),
> und die Überlappung der beiden Sperren wie in F-168, Abschnitt E.

⚠️ Das ist dieselbe Frage wie bei N-14b.1, und sie wird dringender: eine
Kette, die an jeder Stelle ein Fünftel wegnimmt, schweigt am Ende.

### ⚠️ N-13-1′c — Der Nebenbefund, der offen bleibt

> **Turnover ist zu 52 % eine Asset-Eigenschaft.**

Ein registrierter, tragender Beitrag sagt zur Hälfte, *welches* Asset —
nicht *wann*. Das ist keine Widerlegung, aber es heißt, dass ein Teil
seiner Wirkung eine Ebene höher gehört, zur Auswahl (wie der Rangplatz
seit dem 23.08.). **Nicht gemessen, nicht entschieden — und es betrifft
den Bestand, nicht den Kandidaten.**

---

## ⚠️⚠️ N-15: DIE EINORDNUNG — „verglichen mit allem anderen" fehlt in der Mail (02.09.2026)

**Nutzerfrage nach dem Lesen einer echten Mail:** *„Ich dachte, ich
erhalte auch Informationen zu den Bewertungen — warum war dieses Signal
besser als die anderen Assets? Wo liegt der Coin besonders gut, welche
Bewertungen und Potential liegen gut, hoch, mittel, niedrig?"*

**Die Frage trifft den Kern des übergeordneten Ziels**, wörtlich: *„wie
viel ist hier zu holen, **verglichen mit allem anderen**."* Genau dieser
Vergleich steht heute in keiner Mail.

### Was die Mail heute sagt — und was jede Zeile wirklich bedeutet

| Angabe | was sie ist |
|---|---|
| „Rang 28 von 41 nach der Entwicklung der letzten 250 Handelstage" | die **Auswahl**größe: *welche* Werte beurteilt werden |
| „Finanzierung Platz 15, OI-Aufbau Platz 20 von 32" | ausdrücklich **„Auskunft, keine Bewertung"** |
| „ein niedriges Fünftel im Marktvergleich (302 Werte)" | ein **Merkmal**, kein Vergleich der Gesamtbewertung |

**Es fehlt der Rang der Bewertung selbst.**

### ⚠️ Was NICHT geht, und warum

Ein Rang des **Potentials** über alle Werte ist heute unmöglich: das
Potential hängt an Stop und CRV, und die kommen aus dem Modellurteil. Eine
Rangfolge über 44 Werte bräuchte 44 Urteile je Lauf, neunmal am Tag —
genau der Deadloop, aus dem das System kommt.

**Was geht, steht auf den Beiträgen.** Die sind vor jedem Urteil bekannt
und kosten nichts.

### Die vier Varianten, an AVAX vorgerechnet

**A — Der Querschnitt: wo steht der Wert heute?**

    Nach den gemessenen Beitraegen: Platz 26 von 36 — im unteren Mittelfeld.
    Punkte -0,54 · bester Wert +4,45 (BTC) · schlechtester -1,70 (SEI)

**B — Die eigene Lage: ist das für DIESEN Wert gut?**

    Funding-Rang von AVAX heute: 0,23 (0 = guenstigstes Funding)
    In 400 Tagen lag er 102 mal guenstiger -> Perzentil 26
    Zuletzt guenstiger am 2026-08-29.

**C — Die Zerlegung: woher kommt die Zahl?**

    Funding-Rang im Markt   Fuenftel 3   -0,54 Punkte  (100 % der Bewegung)
    ⚠️ ohne Wert und NICHT eingerechnet: Turnover-Rang im Markt

**D — Die anderen: was war heute besser?**

    25 Werte haben heute bessere Beitraege als AVAX:
    BTC, XLM, BNB, QNT, ASTER, BIO, IO, MORPHO, ONDO, SUI, TURBO, W, …

### ⚠️⚠️ Was die Vorrechnung nebenbei aufdeckt

> **AVAX steht auf Platz 26 von 36. Fünfundzwanzig Werte hatten heute
> bessere Beiträge — und die Kaufempfehlung ging für AVAX heraus.**

Der Grund ist bekannt: AVAX hat Bestand und ist damit von der
Auswahlstufe ausgenommen. **Die Mail sagt das nirgends.** Sie liest sich,
als sei der Wert ausgewählt worden.

Und **Variante C** zeigt die eigentliche Schwäche: die Bewertung steht auf
**einem einzigen** Beitrag, und der ist **negativ**. Turnover fehlt, weil
AVAX nicht in der Messbasis steht.

### Die Empfehlung — was zuerst gebaut werden sollte

| | Variante | warum |
|---|---|---|
| **1** | **C — Zerlegung** | deckt auf, wenn eine Bewertung auf einem einzigen Beitrag steht. Das ist heute bei 37 von 44 Werten der Fall und in keiner Mail sichtbar |
| **2** | **A — Querschnitt** | beantwortet die Frage direkt, ein Satz, kostet nichts |
| **3** | **D — die anderen** | beantwortet *„warum dieses"* ehrlich — braucht die Trichtergründe, die seit dem 02.09. im Log stehen |
| **4** | **B — eigene Lage** | wertvoll, aber eine Zeitreihe: bei neuen Werten blind |

⚠️ **Die Wörter müssen an Fünftel gebunden bleiben.** Eine Skala
„hoch/mittel/niedrig" ohne gemessenen Bezug wäre eine erfundene Zahl —
genau das, was Regel 4 verbietet.

⚠️ **Und vor dem Bau ist zu messen, ob die Rangfolge selbst etwas taugt:**
trennt ein hoher Beitragsrang tatsächlich bessere von schlechteren
Einstiegen? Das ist dieselbe Frage wie bei jedem Beitrag — und sie ist für
die **Summe** der Beiträge noch nie gestellt worden.

Werkzeug: `rechne_einordnung_vorschau.py [SYMBOL]`
Verwandt: F-178 · das übergeordnete Ziel in `CLAUDE.md`

### ✔ N-15a GEMESSEN (03.09.2026) — die Vorbedingung ist beantwortet, und sie ändert den Plan

Die Frage oben („taugt die Rangfolge selbst etwas?") ist gestellt und
beantwortet: **75.701 Anker · 41 Symbole · 2.358 Kalendertage.** Ergebnis
vollständig in **F-179**.

| | war geplant | ist gedeckt |
|---|---|---|
| **die Größe** | Summe aller tragenden Beiträge | ⚠️ **der Funding-Rang allein** — die Summe ist **nicht wohlgeordnet** (Fünftel 2 liegt unter Fünftel 1) |
| **die Sprache** | „Platz 26 von 36 — im unteren Mittelfeld" | Fünftel-Sprache, aber ⚠️ **die obersten beiden sind untereinander nicht unterscheidbar** |
| **der Gewinn** | „die Summe ist genauer" | ✖ **nicht nachweisbar** — gepaart −0,0031 R [−0,0180 .. +0,0097], während die Anlage 0,02 R fände |

**Warum die Summe scheitert, ist kein Messproblem, sondern Arithmetik:**
ihre Skala hängt an der Datenlage. Ein Wert mit Funding −0,54 und
fehlendem Turnover hat Summe −0,54; ein Wert mit Funding −0,54 und
Turnover +0,54 hat Summe 0,00 — und steht **höher**, ohne besser zu
liegen. Bei **37 von 44** Werten ist genau das der Fall.

### Die Reihenfolge des Baus — geändert

| | Variante | Stand nach N-15a |
|---|---|---|
| **1** | **C — Zerlegung** | ✔ **unverändert gedeckt.** Sie behauptet keine Ordnung, sie zerlegt. Und sie deckt genau die Schwäche auf, die N-15a bestätigt hat: die Bewertung steht meist auf einem einzigen Beitrag |
| **2** | **A — Querschnitt** | ⚠️ **nur über den Funding-Rang**, nicht über die Summe. Fünftel-Wörter zulässig, aber „im besten Fünftel" darf nicht schärfer klingen als „im vierten" |
| **3** | **D — die anderen** | unverändert — braucht die Trichtergründe aus dem Log |
| **4** | **B — eigene Lage** | unverändert — Zeitreihe, bei neuen Werten blind |

⚠️ **Eine Folge, die über N-15 hinausgeht:** wenn die Summe als Rangfolge
nicht taugt, ist zu prüfen, ob sie als **Potentialschwelle** taugt — dort
wird sie heute verwendet (Stufe 11). Die Trennschärfe war gepaart
gleichwertig, das spricht nicht dagegen; die fehlende Ordnung hingegen
heißt, dass ein **Regler** dort nie funktionieren wird, ein **Schalter**
schon. Das deckt sich mit dem Befund „die Schwelle ist ein Schalter, kein
Regler" — jetzt mit einer zweiten, unabhängigen Begründung.

**Neuer Prüfpunkt N-15b:** trägt die Summe an der Schwelle besser als der
Funding-Rang allein? Gleiche Anlage, gepaarter Test, eine Zelle.

Werkzeug: `messe_beitragssumme.py` · `rechne_einordnung_vorschau.py [SYMBOL]`
Verwandt: **F-179** · F-171 · 2.104 · 2.105

### ✔ N-15 VARIANTE C GEBAUT (03.09.2026) — die Zerlegung steht in der Mail

Gebaut wurde genau das, was N-15a deckt: **keine Rangfolge**, sondern die
Auskunft, **worauf die Zahl steht**.

**Was jetzt in der Mail steht** (Fall AVAX, ein Beitrag, negativ):

    = geschaetzte Trefferquote                           32,8 %
       Woher die Bewegung kommt:
          Funding-Rang im Markt                           100 %
    ⚠️ Die Bewertung steht auf EINEM Beitrag (Funding-Rang im Markt).
       Faellt er weg, bleibt die nackte Basisrate.
    ⚠️ Tragende Beitraege, die HIER keinen Wert haben - nicht gefallen,
       sondern ohne Datenlage:
          Turnover-Rang im Markt - an diesem Anker nicht bestimmbar
       Deshalb ist diese Zahl NICHT mit der eines Werts vergleichbar, bei
       dem alle Beitraege vorliegen.

Und aus der Auswahl, wenn der Wert **gehalten** wird:

    ⚠️ Dieser Wert wurde NICHT ausgewaehlt - er wird beurteilt, weil Sie
       ihn halten. Bei einer gehaltenen Position lautet die Frage 'halten
       oder verkaufen', und die stellt sich unabhaengig vom Rang.

**Die drei Unterscheidungen, die C einführt:**

| | vorher | jetzt |
|---|---|---|
| Anteil je Beitrag | fehlte | „100 %" / „50 % / 50 %" |
| Bewertung auf **einem** Beitrag | unsichtbar (37 von 44 Werten!) | eigene Warnzeile |
| „gefallen" gegen „kein Wert da" | **eine gemeinsame Liste** | getrennt, mit eigener Überschrift |
| warum dieser Wert überhaupt da ist | verschwiegen | benannt, wenn Bestand |

### ⚠️ Wie gebaut wurde — auf Nutzerhinweis geändert

*„Vorsicht bei den Änderungen wegen Altbestand an Code und weil die
Komplexität hoch ist."*

Meine erste Fassung führte für „trägt, aber hier kein Wert" einen neuen
**Zustandswert** `"fehlt"` ein. Das hätte funktioniert und trotzdem
Schaden angerichtet: `pruefe_wahrscheinlichkeit_bitgleich.py` vergleicht
`zustand` **wörtlich** gegen einen eingefrorenen Stand — der Test wäre rot
geworden, obwohl sich rechnerisch nichts ändert.

**Umgebaut auf additiv:** der Zustand bleibt `"nie"`, die neue Information
kommt als Feld `luecke` daneben. Kein Leser der Struktur ändert sein
Verhalten. Ebenso `hat_bestand` in `auswahl.saetze()` — neuer Parameter
**mit Vorgabe**, jeder bestehende Aufrufer bleibt gültig.

### Was dabei nebenbei gefunden wurde

Drei Fehler und ein Zählproblem — vollständig in **F-181**:
dieselbe Mail nannte **zwei verschiedene Trefferquoten** (F-178 eine Zeile
tiefer, T6 sah es nicht) · das Vorzeichen stand doppelt (`+-0,5`) · meine
eigene neue Prüfung war zunächst blind · die Terminmarkt-Stufe zählt
Notizen als „bestanden".

### Prüfung

`pruefe_wahrscheinlichkeit_bitgleich.py` **432 Fälle, 0 FEHL** (neu
aufgezeichnet — der alte Stand war seit dem 31.08. vollständig rot, und
zwar zu Recht: 2e und R1 haben die Beiträge legitim geändert. **Geprüft,
bevor neu aufgezeichnet wurde: keine einzige Zahl weicht ab**, nur ein
Zustandswechsel bei einem 0,0-Punkte-Beitrag, ein neuer Beitrag und drei
Audit-Texte).

Suite **1943 bei 0 FEHL**, darunter T7 und neun neue C-Prüfungen.

### Offen — die Reihenfolge nach C

| | Variante | Stand |
|---|---|---|
| **2** | **A — Querschnitt** | ⚠️ nur über den **Funding-Rang** (F-179), nicht über die Summe |
| **3** | **D — die anderen** | ⚠️ **hat durch F-180 eine andere Antwort bekommen**: die Auswahl wählt seit zehn Tagen dieselben zwei Werte. „Was war heute besser" hieße heute „dasselbe wie gestern" |
| **4** | **B — eigene Lage** | unverändert |

Werkzeug: `agent/wahrscheinlichkeit.py` · `agent/auswahl.py`
Verwandt: **F-179** · **F-180** · **F-181** · 2.106

---

## ⚠️⚠️ N-16: DER AUSSTIEG — eigener Planpunkt, bewusst ZURÜCKGESTELLT (03.09.2026)

**Nutzervorgabe, die das aufmacht:** *„auch der Ausstieg sollte
grundsätzlich durch eine saubere Bewertung erfolgen und nicht durch einen
Takt."*
**Und die Priorisierung dazu:** *„wenn das Ausstiegsthema größer ist,
müssen wir das u. U. eigenständig im Plan berücksichtigen und zuerst die
offenen Einstiegs- bzw. Bewertungsfragen für Spot und Hebel reparieren."*

**Es ist größer.** Deshalb hier nur der Umfang — gebaut wird nichts.

### Warum es Regel 4 berührt

Der Ausstieg wird heute vom **Trailing-Stop** ausgelöst.
`positionsfuehrung.py` nennt die Quelle wörtlich: *„Offene SIGNALE, bei
denen der Trailing-Stop nachgezogen gehört."*

> **„Kurs unter der nachgezogenen Marke" ist ein FAKT über die Gegenwart,
> keine Aussage über das, was kommt.** Nach der Prüffrage aus `CLAUDE.md`
> ist das dieselbe Klasse wie „Kurs unter Einstand → kaufen" — Regel 4.

Es ist zwar kein *Takt* im engeren Sinn (keine Uhr), aber es ist auch
keine **Bewertung**. Und der Schaden ist bereits gemessen: der
Block-Bootstrap vom 01.09. hat belegt, dass **das Trailing in der
Aufwärtsphase das Vorzeichen dreht**.

### Der Umfang — vier Baustellen, keine davon klein

| | | Stand |
|---|---|---|
| **N-16a** | die **Bestandshistorie** fehlt — wann wurde welcher Wert gehalten? | ⚠️ **Vorbedingung für alles andere.** Ohne sie ist die Ausstiegsfrage nicht messbar (F-183: von 37 Bestandssymbolen sind 5 in der Messbasis) |
| **N-16b** | der Trailing-Stop als Auslöser | Schaden belegt (01.09.), Ersatz offen |
| **N-16c** | die Ausstiegsprüfung läuft über **Signale**, nicht über Positionen | teilweise gelöst durch `positionsfuehrung` (27.08.), aber die greift **nicht ein** — sie ist eine Lesefunktion |
| **N-16d** | eine **Ausstiegs**bewertung gibt es nicht | ⚠️⚠️ **am 03.09. in PROD nachgewiesen (F-187):** der Ausstiegspfad verlässt die Kette bei Stufe 9 (`aktion`, Zeile 1642 `return`) und durchläuft **weder `geometrie` noch `risikoschicht` noch den `entscheider`**. `_sende_ausstieg` setzt `gate_passed = 1` selbst. Ergebnis: VERKAUFEN kommt zu **100 %** durch, REDUZIEREN zu 70,6 %, NACHKAUFEN nur zu 36,1 % |

### ⚠️⚠️ PROD-MENGE GEMESSEN (03.09.) — die Erwartung war falsch gestellt

Im scharfen Stand (02.09. 12:00 – 03.09. 04:17):

    13,3 mailfaehige Signale je Tag
       davon Einstieg   4,4
       davon AUSSTIEG   8,8   <- zwei Drittel, ungefiltert

Meine frühere Erwartung *„0,5 bis 1 je Tag"* betraf ausschließlich die
**Einstiegsseite** („ein Pull senkt 113 Signale auf 2"). Die
Ausstiegsseite kam in der Rechnung nicht vor — und stellt heute zwei
Drittel des Aufkommens.

⚠️ **Damit ist N-16 nicht nur ein Qualitätsthema, sondern das
Mengenthema.** Wer die Signalflut senken will, muss dort ansetzen: auf
der Einstiegsseite wirkt die Sperre bereits (28 NACHKAUFEN → 3).

⚠️ Unsicherheit (2.107): neun Ereignisse in 16,3 Stunden, Poisson-Band
rund ±9 je Tag. Die Größenordnung trägt, die Zahl nicht.

⚠️ **N-16a ist der Engpass und zugleich der billigste Schritt:** eine
Tabelle, die täglich den Bestand fortschreibt. Sie kostet nichts, muss
aber ab jetzt laufen — jeder Tag ohne sie ist ein Tag, den die spätere
Messung nicht hat.

### Was ZUERST kommt — die offenen Einstiegs- und Bewertungsfragen

Nach Nutzervorgabe vor N-16 zu erledigen:

| | Punkt | Spot | Hebel | Stand |
|---|---|---|---|---|
| **1** | ⚠️⚠️ **ZWEIMAL KORRIGIERT 03.09. — gültig ist F-185: es fehlt die HORIZONT-Achse** | ✔ | ✔ | Die Beiträge sind auf **H20** kalibriert, ein Hebel-Trade läuft **1–3 Tage** — dort ist die Wirkung **6–7× kleiner** (gemessen 31.08.). `Beitrag` hat kein `horizont`-Feld, die Haltedauer geht nicht in die Bewertung, die Schwelle hängt nur an der Datenlage. **R-R9 ist notiert und nicht umgesetzt** |
| ~~1a~~ | ~~KORRIGIERT 03.09. (F-184): die Wegwahl hängt nicht an der Bewertung~~ | ✔ | ✔ | ⚠️ Die frühere Fassung („der Bewertung fehlt eine Instrument-Achse") ist **widerlegt** — sie fehlt zu Recht (S6b/Kapitel 88, in R gerechnet identisch, Liquidation per RM-11 nie relevant). Der echte Punkt: **das Potential entscheidet nur OB, nicht WIE.** Den Weg wählt heute der **ATR** über den Stopabstand, die Akkumulation ein **GUI-Schalter** |
| **2** | ⚠️⚠️ **Die zweite Zelle läuft nicht** (F-169) | ✔ | ✔ | `strategie` war **nie** etwas anderes als `einstieg` (F-180). Damit ist auch **L4** (Cooldown 48 h) toter Code und N-14s Einschränkung „nur einstieg" folgenlos |
| **3** | ~~Der Hebel existiert in keiner der beiden Ketten~~ | — | — | ✖ **FALSCH, gestrichen (F-184).** Nutzerhinweis 03.09., bestätigt: der Hebel ist **nicht abgeschaltet**, er ist ein **Ergebnis** (Kapitel 88). Dieselbe Fehllesart wurde schon am 31.08. widerlegt. Was stimmt, steht jetzt in Punkt 1 |
| **4** | **Die Hebelbewertung wurde nie validiert** | — | ✔ | offen |
| **5** | N-15 **Variante A** (Querschnitt) | ✔ | ✔ | nur über den **Funding-Rang** (F-179), gedeckt und klein |
| **6** | ⚠️ **Turnover deckt nur 23 % des Krypto-Bestands** | ✔ | ✔ | F-183 — bei Ausstiegen steht die Bewertung fast immer auf **einem** Beitrag |

**Punkt 1 und 2 sind dieselbe Wurzel:** eine Bewertung, die ihre eigenen
Achsen nicht fragt. Wer sie behebt, macht N-16d überhaupt erst möglich —
denn eine *Ausstiegs*bewertung ist genau eine weitere Achse.

Verwandt: **F-183** · F-180 · F-169 · Abschnitt 9 · `Bestandsaufnahme_Positionsfuehrung_26_08.md`

---

## ⚠️⚠️ N-17: DIE HORIZONT-ACHSE — der eigentliche Punkt 1 (03.09.2026)

**Bestandsaufnahme vollständig in F-185.** Kurzfassung: F-184 prüfte die
Instrument-Achse (fehlt zu Recht — Arithmetik), der Plan nannte in 9.1
aber **zwei** Achsen. Die zweite ist die relevante.

### Der Befund in einer Zeile

> **Die Beiträge sind auf H20 kalibriert. Ein Hebel-Trade läuft 1–3 Tage.
> Dort ist ihre Wirkung 6–7× kleiner — und die Schwelle, gegen die
> geprüft wird, ist für H20 gesetzt.**

| Horizont | Funding | Turnover |
|---|---|---|
| H1 | +0,0019 | +0,0044 |
| H2 | +0,0026 | +0,0107 |
| **H20** | **+0,0246** | **+0,0616** |

### Was NICHT der Weg ist — schon gemessen

| | | |
|---|---|---|
| ✖ | eine **Instrument**-Achse in `_gilt()` | Arithmetik: gebührenfrei sind Hebel und Spot dasselbe Geschäft (H-1, F-184) |
| ✖ | die Wegwahl über **Kursmerkmale** | H-1 hat sechs Kandidaten über **916.021 Anker** gemessen — keiner trennt steil-kurz von flach-lang |
| ✖ | den Hebel über die **Wirtschaftlichkeit** wählen | verbotene Ebenenvermischung (stehende Vorgabe) |

### Die zwei Wege, die offen sind

| | | Größe | Vorbedingung |
|---|---|---|---|
| **N-17a** | **Die Beiträge tragen ihren Horizont** — `Beitrag` bekommt ein Feld `horizont`, und die Schwelle wird je Horizont kalibriert (**R-R9**, seit 31.08. notiert) | mittel | keine — die Messwerte je Horizont **liegen bereits vor** (31.08.) |
| **N-17b** | **Das Hebel-Screening messen** — `hebel_triggers` (82.655 Zeilen, 42 Tage, 13.254 Kandidaten ≥ 70) gegen spätere Kursbewegungen. ⚠️ *„Der Score 70 ist gesetzt, nicht gemessen."* | mittel | keine — seit **42 Tagen** messbar |

⚠️ **N-17b ist der aussichtsreichere Weg.** Das Screening arbeitet mit
**Terminmarktdaten** (OI, Funding-Extrema, Long-Konten, RSI) — genau der
Quelle, aus der die beiden einzigen tragenden Beiträge stammen. Wo
Kursmerkmale gescheitert sind (H-1), ist der Terminmarkt **ungeprüft**.

⚠️ **N-17a ist die ehrlichere Reihenfolge.** Solange die Schwelle für H20
gilt und auf H2-Trades angewendet wird, misst jede weitere Hebelarbeit
gegen einen falschen Maßstab.

### ✔ DIE KETTENPRÜFUNG IST GELAUFEN (03.09.) — vollständig in F-186

**Ergebnis in einem Satz:** die Kette ist auf **H20** begründet und
entscheidet ihre Signale im **Median nach 2 Tagen** (239 entschiedene
Trades). Auf H2 ist die Wirkung der Beiträge um **Faktor 9,5** (Funding)
bzw. **5,8** (Turnover) kleiner.

⚠️ **Das erklärt die 48,2 % Trefferquote neu:** nicht die Beiträge taugen
nichts — sie wirken auf einem Zeitraum, den die Kette nie erreicht.

### ⚠️⚠️ Die Reihenfolge — und warum jede Abkürzung schadet

Der Horizont ist **keine unabhängige Größe, sondern eine Folge der
Geometrie**. Wer eine einzelne Stelle anfasst, verschiebt das Problem:

| wer … | … erzeugt |
|---|---|
| nur die **Schwelle** senkt | mehr Signale bei gleicher Trennschärfe — eine zweite Mengenbremse |
| nur die **Beiträge** auf H2 umkalibriert | eine Bewertung, die schwächer trennt, und eine Schwelle, die nicht mehr passt → **derselbe Fehler wie G-6** (vier Klassen nach Datenlage gesperrt) |
| nur den **Stop** weitet | einen anderen Trade — das ist eine Strategieänderung, keine Kalibrierung |

⚠️ **Quer dazu:** die Beitragsmessung ist **barrierefrei**, die Kette hat
TP und SL. Wer die H2-Zahlen einsetzt, ohne das zu prüfen, tauscht einen
bekannten Fehler gegen einen unbekannten.

**Daraus die Reihenfolge für N-17:**

| | Schritt | Stand |
|---|---|---|
| **N-17-0** | **Den Horizont kennen** — aus Stop und Volatilität die erwartete Zeit bis zur Barriere. ⚠️ **GEMESSEN (F-202, 03.09.): Nullbefund** — weder Stop-Abstand noch Volatilität sagen die Dauer voraus (r=-0,05/-0,06, Bänder schließen Null ein). Pro-Trade-Schätzung entfällt; der kettenweite Maßstab (F-186/F-189, Median 2,0 Tage → H2) bleibt gültig | ✖ **abgeschlossen, negativ — kettenweiter Ersatz steht** |
| **N-17a** | ⚠️⚠️ **GEMEINSAM gemessen (F-203, 04.09.): Ergebnis ist ernüchternd.** H2-Stufen für Funding/Turnover gerechnet, Schwelle mit derselben Methode wie H20 neu kalibriert — die beste Schwelle ist praktisch 0,000 (keine Trennschärfe mehr). Korrelation Potential↔Ertrag real, aber winzig (r=0,02, Band schließt Null aus, erklärt ~0,04 % der Varianz). **Nicht live registriert** — wäre eine Mengenbremse ohne Qualitätsaussage | Messwerte liegen seit 31.08./04.09. vor, Registrierung ausstehend (Nutzerentscheidung) |
| **N-17b** | das Hebel-Screening messen | ⚠️ **erst danach** — sonst gegen falschen Maßstab |

### ⚠️ Zwei Stufen, die die Prüfung nebenbei aufgedeckt hat

| | | |
|---|---|---|
| **anlass** | nimmt 28,2 % | die Regel ist *„Faktensatz unverändert seit N h"* — ein **Fakt über die Gegenwart**, keine Bewertung. Dieselbe Klasse wie der Trailing-Stop (N-16b) und Regel 4 |
| **wiederholung** | nimmt **93,8 %** | der Cooldown ist die **schärfste Stufe der Kette** und **nie gegen Ergebnisse gemessen**. Am 27.08. bereits notiert: *„eine Mengenbremse ohne Qualitätsaussage — die schlechten Signale verschwinden im selben Verhältnis wie die guten"* |

⚠️ **Beide gehören in dieselbe Familie wie N-16b:** Auslöser, die einen
Zustand beschreiben statt etwas über das zu sagen, was kommt. Sie sind
**nicht** Teil von N-17 — aber wer N-17 baut, ohne sie zu kennen, misst
die Wirkung einer Bewertung hinter einer Bremse, die 93,8 % wegnimmt.

### Der ursprüngliche Prüfauftrag

**Nutzervorgabe 03.09.:** *„Wenn wir wissen was zu tun ist, in den Plan,
dokumentieren — und danach müssen wir zuerst die bestehende Kette prüfen,
ob diese korrekt funktioniert."*

Verwandt: **F-185** · F-184 · H-1 · R-R9 · Abschnitt 9

---

# ⚠️⚠️ DER STUFENPLAN — Schritt für Schritt, mit Abhängigkeiten (03.09.2026)

**Nutzerauftrag:** *„dann brauchen wir einen Plan, um Schritt für Schritt
die korrekten Anpassungen zu planen und durchzuführen."*

Dieser Abschnitt fasst N-16, N-17 und die Befunde F-183 bis F-188 zu
**einer** Reihenfolge zusammen. Er ersetzt keine der Einzelbeschreibungen
— er sagt, **in welcher Reihenfolge** sie gebaut werden und **warum jede
Abkürzung schadet**.

## Der Ausgangszustand, gemessen

    Krypto, scharfer Stand (65 Laeufe, 16,3 h):
      25 Bestandswerte  -> 55 beurteilt -> 39 Signale -> 7 durch
      18 ohne Bestand   ->  0 beurteilt ->  0 Signale -> 0 durch
      Einstieg 4,4/Tag · Ausstieg 5,9/Tag

    Die Einstiegsseite ist bewertet und gesperrt.      ✔
    Die Ausstiegsseite ist WEDER bewertet NOCH gesperrt. ⚠️
    Die Bewertung ist auf H20 kalibriert, entschieden
      wird nach 2 Tagen (Faktor 6-10).                  ⚠️
    Nur Krypto hat Beitraege; vier Klassen haben keine. ⚠️

## Die Reihenfolge

| # | Schritt | Größe | Vorbedingung | ⚠️ was passiert, wenn man ihn überspringt |
|---|---|---|---|---|
| **S0** | ✔ **GEBAUT 03.09. (F-190).** Die Abbruchstelle je Asset schreiben. `rollen_gate` führt `letzte_stufe[symbol]` bereits im Speicher — sie muss nur in den Lauf-Datensatz | **klein** | keine | jede Wirkungsmessung danach ist blind: man sieht, dass ein Asset still ist, nicht warum |
| **S1** | ⚠️⚠️ **GAB ES SCHON (F-190).** `portfolio_wert_historie.mengen_json` läuft seit dem **08.05.**, 91 Zeilen. ⚠️ Sie zählt aber `quantity` ohne `staked_quantity` — sechs Werte fehlen (dieselben wie in F-180). **Nicht repariert:** ein Fix ließe `wert_eur`/`index_wert` springen → **Nutzerentscheidung**. Die Dringlichkeit ist weg | **klein** | keine | ⚠️ **zeitkritisch** — jeder Tag ohne sie fehlt der späteren Messung dauerhaft. Heute sind von 37 Bestandssymbolen **5** in der Messbasis (F-183) |
| **S2** | ✖ **GEMESSEN (F-202), Nullbefund:** weder Stop-Abstand noch Volatilitätsperzentil sagen die Dauer bis zur Entscheidung voraus (Spearman r=-0,05/-0,06, beide Bänder schließen Null ein, jedes Terzil Median 2,0 Tage). Eine Pro-Trade-Horizontschätzung trägt mit diesen Feldern **nicht**. ⚠️ Unberührt bleibt der **kettenweite** Maßstab aus F-186/F-189 (Median 2,0 Tage → H2) — N-17a kann damit weiterlaufen, nur gröber als geplant | mittel | S0 | ohne diese Größe ist „Schwelle je Horizont" nicht implementierbar — man müsste sie raten |
| **S3** | ⚠️⚠️ **GEMEINSAM kalibriert (F-189 + F-203, 04.09.): fertig gemessen, NICHT gebaut.** Beiträge und Schwelle zusammen auf H2 umgerechnet — die resultierende Schwelle hat praktisch keine Trennschärfe mehr (bestes Ergebnis bei Schwelle≈0). Funding/Turnover tragen auf H2 fast nichts (Korrelation real, aber r=0,02). **Registrierung bewusst zurückgestellt** — würde eine wirkungslose Mengenbremse einbauen | mittel | S2 | ⚠️ wer nur die Schwelle senkt, baut eine zweite Mengenbremse; wer nur die Beiträge umkalibriert, wiederholt **G-6** (Stufe 11 sperrt alles). Jetzt gemessen: selbst GEMEINSAM kalibriert bleibt kaum etwas übrig |
| **S4** | **Ausstiegsbewertung** (N-16d) | groß | **S1** (Historie), S3 | ohne S1 nicht messbar; ohne S3 gegen den falschen Maßstab gemessen |
| **S5** | **Hebel-Screening messen** (N-17b): `hebel_triggers`, 82.655 Zeilen, Score 70 ist gesetzt statt gemessen | mittel | S3 | ⚠️ misst sonst gegen einen H20-Maßstab, den die Kette nie erreicht |
| **S6** | **Die vier anderen Assetklassen** | groß | S3 | Stufe 11 zählt dort heute nur — eine Sperre ohne Beiträge wäre eine Sperre nach Datenlage (**Regel 4**) |

## ⚠️ Drei Dinge, die NICHT auf dieser Liste stehen — und warum

| | | |
|---|---|---|
| eine **Instrument-Achse** in `_gilt()` | ✖ | Arithmetik: gebührenfrei sind Hebel und Spot dasselbe Geschäft (F-184, H-1) |
| die **Wegwahl über Kursmerkmale** | ✖ | H-1 hat sechs Kandidaten über 916.021 Anker gemessen — keiner trennt |
| **A1 anfassen**, weil es „immer dieselben wählt" | ✖ | 12 Tage, 0 Wechsel bei einer Erwartung von ~1 — normal (F-182) |

## ⚠️ Die Querschnittsregel für jeden Schritt

> **Vor jedem Schritt die Ebene benennen:** bewertet er (dann
> **gebührenfrei**, auch beim Hebel) oder berichtet er (dann dürfen
> Gebühren vorkommen)? Dauerprüfung **T8** hält das fest.

> **Nach jedem Schritt die Wirkung je Asset prüfen**, nicht nur die Suite:
> `pruefe_kette_je_asset.py`. Eine grüne Suite ist kein Wirkungsnachweis,
> und „0 Signale" ist immer ein Befund.

## Zwei offene Punkte, die quer liegen

| | | |
|---|---|---|
| **anlass** nimmt 28,2 % | die Regel ist *„Faktensatz unverändert seit N h"* — ein **Fakt**, keine Bewertung | dieselbe Familie wie N-16b |
| **wiederholung** nimmt **93,8 %** | der Cooldown ist die schärfste Stufe und **nie gegen Ergebnisse gemessen** | ⚠️ wer S3 baut, misst die Wirkung einer Bewertung **hinter** dieser Bremse |

Verwandt: **F-183** · **F-186** · **F-187** · **F-188** · N-16 · N-17

---

# ⚠️⚠️⚠️ GESAMTSICHTUNG — vergessene und offene Punkte seit 27.08. (03.09.2026)

**Nutzervorgabe, die das auslöst:** *„Wir müssen zukünftig alle
anstehenden Themen in Pläne übernehmen, sonst vergessen wir diese —
nimm die offenen Punkte auf in den Plan und gehe zuvor in alle
Dokumente und Umbauarbeiten bis mindestens 27.08.26, um ‚vergessene'
oder geplante, offene Punkte zu identifizieren."*

**Methode:** systematische Durchsicht aller 16 seit 27.08. geänderten
Basisinfos-Dokumente (99 Commits). Punkte aus der laufenden N-13…N-17-
Linie von heute sind hier **nicht** wiederholt — die stehen bereits
oben. Jeder Punkt unten wurde **stichprobenartig am heutigen Code
gegengeprüft**, nicht nur aus der Doku übernommen.

## ⚠️⚠️⚠️ A — das ÜBERGEORDNETE ZIEL für Krypto ist an EINER Stelle blockiert

Das Ziel aus `CLAUDE.md`: *„eine neutrale, begründete Aussage über das
POTENTIAL — wie viel ist hier zu holen, verglichen mit allem anderen."*
Für **Krypto** ist das gebaut (N-13…N-17 regeln, wie gut). Für die
**anderen vier Klassen** existiert der Vergleichsmaßstab nicht.

### N-18: Rolle G — drei beschlossene Änderungen

**G-a, G-b, G-c** (01.09. beschlossen): Vokabular vereinheitlichen
(ja/nein/konsistent/unklar) — ausdrücklich als *„Vorbedingung für alles
Weitere, kein Filter/keine Messung/kein Bericht darf vorher gebaut
werden"* markiert — Widerspruch sichtbar machen, Trefferbilanz von G
führen.

✔ **G-a GEBAUT (03.09., F-195).** Beim Aufsetzen stellte sich heraus,
dass das Vokabular seit dem 16.08. bereits eindeutig ist — live läuft
nur noch der Einwand (`ja`/`nein`/`unklar`), die alten Werte
(`konsistent`/`widerspruch`, `zai_eigene_richtung`,
`zai_uebereinstimmung`) sind seit drei Wochen eingefroren. Gebaut:
`einwand_liegt_vor()` (eindeutige Form), ein **Kanarienvogel** statt
Löschung (die alten Werte sind ein **dokumentierter Rückfallweg** für
die sechs alten Pipelines — Löschen hätte ihn gekappt und eine
bestehende Prüfung gebrochen), und der NB-Export-Fehler behoben
(zählte drei Wochen lang eine tote Kennzahl aus einer erstarrten
Tabelle).

✔ **G-b GEBAUT (03.09., F-196).** Die Urteilszeile stand bereits seit
dem 17.08. am Anfang von Abschnitt 5 — was noch unterging: der Abschnitt
ist der letzte von fünf. Das Urteil wandert jetzt zusätzlich in die
**Überschrift** von Abschnitt 5 (nicht in den Betreff — dort hat dieselbe
Idee schon zweimal Schaden angerichtet, O-37/S5/S6). ⚠️ Der Gegentest
ließ die eigene erste Prüfung durchfallen (sie testete eine Kopie statt
des echten Codes) — behoben durch Auslagerung in
`signal_mail.gegenpruefung_titel()`.

○ **G-c GEMESSEN, nicht entschieden (03.09., F-197).** Keine neue
Tabelle nötig — Gs Einwand blockiert nichts, das Signal hat einen echten
Ausgang auf derselben Zeile. Bei 55 aufgelösten Fällen: Richtung stimmt
(Einwand → 45,8 % Trefferquote, kein Einwand → 54,8 %), aber das
90-%-Band schließt die Null ein — **nicht nachweisbar, nicht widerlegt.**
⚠️ Die Frage *„soll G sperren dürfen?"* bleibt offen, weil die Fallzahl
noch nicht reicht, nicht weil G nachweislich nichts trägt. **G-c ist eine
laufende Messung** — erneut ausführen, sobald mehr aufgelöste
Einwand-Fälle vorliegen. Damit ist **N-18 vollständig aufgesetzt**: G-a
und G-b gebaut, G-c gemessen und zur Wiederholung vorgemerkt.

⚠️ **Und Rolle G hat für zwei von fünf Klassen gar keinen Zweig.** Am
Code bestätigt (03.09.): `positionierung.lage()` kennt nur `aktien` und
`rohstoffe`. **Themen-ETF und Hedge fehlen** — `saetze()` bleibt leer,
`zweite_meinung.py` bricht dort ab.

⚠️ **Nachtrag 03.09. (aus F-194, zurückgezogenem N-22):** falls die
Qualität von Rolle G / dem LLM-Urteil je über eine Fallzahl beurteilt
werden soll (Meta-Labeling-Gedanke, `Test_und_Verifikationsmethodik.md`
Abschnitt G, 09.08. — *„keine Entscheidung, gehört dem Nutzer
vorgelegt"*, bis heute nicht entschieden), gehört die Zielgrößen-Frage
**hierher**, nicht an A1. Noch nicht bearbeitet.

### N-19: Die Messbasis der vier Nicht-Krypto-Klassen (P6) — ✔ aufgesetzt (03.09.)

**Am Code gemessen (03.09.), `data/messdaten.db`, nach drei Bugfixes und
einer Schema-Migration (F-198):**

    krypto        516 Reihen   ✔ unveraendert, nicht Teil von N-19
    aktien        470 Reihen   ✔ Ziel 300-500 erreicht
    themen_etf    293 Reihen   ✔ Ziel 150-300 erreicht
    rohstoffe      35 Reihen   ✔ Ziel ~38 erreicht (Universum klein, kein Screening moeglich)
    hedge           —          ⚠️⚠️ kein Querschnitt MÖGLICH (Konstruktionsproblem, keine Fleißaufgabe — Hedge ist eine Rolle im Portfolio, keine Anlageklasse)

**Unterwegs gefunden (F-198):** `yf.EquityQuery` statt `yf.ETFQuery` für
Themen-ETF, klassenspezifisches `sortField`, `pruefe()` außerhalb des
try/except (ein Symbol riss den ganzen Lauf ab) — und, schwerer: `symbol`
war über die Klassen hinweg keine eindeutige Kennung. `INSERT OR REPLACE`
auf `messreihen` (nur `symbol` als Primary Key) hatte sieben Symbole
(`DASH`, `STX`, `T`, `C`, `BOND`, `DIA`, `MDT`) stillschweigend mit
Kursdaten eines völlig anderen Instruments überschrieben (Aktie ↔
gleichnamiger Coin). Behoben: `price_history_ohlc` führt `assetklasse`
jetzt im Primary Key, `messreihen`-Schreibzugriff meldet Kollisionen statt
sie stumm auszuführen. Die sieben Symbole wurden bereinigt und sauber neu
geladen. Suite 1967/1967.

⚠️ Krypto absichtlich nicht neu geladen — falls unter den sieben
bereinigten Symbolen echte Altcoin-Ticker steckten, fehlen sie
möglicherweise in Kryptos eigener Messbasis. Offener Punkt.

P6c/d (die andere Größenform — Regel 30.08.: *Rohwert · Veränderung ·
Verhältnis · Niveau — Querschnitt oder Zeitreihe?*) sind mit der
Messbasis noch nicht bearbeitet.

⚠️ **Ohne P6c/d bleibt „verglichen mit allem anderen" für 4 von 5 Klassen
eine Notiz statt einer Aussage.** Das ist derselbe Befund wie **S6** im
Stufenplan oben — die Datengrundlage steht jetzt, die Auswertung noch nicht.

### N-20: `fakten_roh` erreicht seit dem 13.08. keine Mail — GEGENGEPRÜFT, unverändert

Am Code bestätigt (03.09.): `rollen_lauf.py:2202` und `:2252` sind
weiterhin die **einzigen** zwei Fundstellen für `fakten_roh` im ganzen
Projekt — beide lesen, keine schreibt. Elf Zusatzfakten
(`funding_eur_tag`, `kgv`, `analysten_trend`, `cot_netto_pct`, …) und
das **Lagebild von Rolle A** erreichen seit **drei Wochen** keine Mail.

> Das ist ein Baustein der neutralen Begründung, der im Kaufpfad fehlt
> — nicht im Ausstiegspfad wie N-16, sondern in der Bewertung selbst.

## ⚠️⚠️ B — die Verkaufsseite hängt zusätzlich TIEFER als N-16 bereits zeigt

**Nutzerfrage 03.09.:** *„die Verkaufsseite hängt noch immer falsch im
System oder?"* — Ja, und zwar auf zwei Ebenen:

| Ebene | Befund | Status |
|---|---|---|
| **Bewertung** | Ausstiege durchlaufen weder Geometrie noch Entscheider (F-187) | ✔ heute erkannt, N-16 |
| ⚠️⚠️ **Positionsführung selbst** | **sieben Lücken L1–L7** vom 26.08. — ⚠️ GEGENGEPRÜFT 03.09. (F-199): **nicht** unverändert, L1 teilweise gebaut. **L3 teilweise behoben (F-201):** Stop-Trailing-Text für Spot aus Kauf- UND Verkaufsmail entfernt. L2/L4/L6/L7 weiterhin ZU BAUEN, aber nicht mehr blockiert | **N-16e ✔ geklärt, F-199/F-200/F-201** |

**N-16e — Vorbedingung für N-16d:** vier Grundsatzfragen zur
Positionsdefinition (Bestandsaufnahme 26.08., Abschnitt 6). ⚠️
GEGENGEPRÜFT 03.09. (F-199/F-200) — **alle vier jetzt geklärt:**

    1. Stop einer gewachsenen Spot-Position?
       → Nutzerentscheidung 03.09.: KEIN Stop, rein bewertungsbasiert.
    2. Was ist "eine Position" bei Nachkauf?
       → bereits beantwortet und gebaut (positionsfuehrung.py, 27.08.):
         eine Position, ein gewichteter Durchschnittseinstand
    3. Soll taktisch/core den Ablauf steuern?
       → stellt sich fuer Multiassets nicht: alle 13 Eintraege (inkl.
         beider Hedge-ETFs) tragen `taktisch`, KEINER `core`. Die
         Bestandsaufnahme hatte core/taktisch faelschlich Nicht-Krypto/
         Krypto zugeordnet - `rolle` ist eine rein krypto-interne
         Unterscheidung (13 Krypto-Kernwerte vs. Rest), siehe F-200.
    4. Gilt fuer Core-Assets dieselbe Logik wie fuer taktische?
       → Hedge ist BEREITS eigenstaendig (eigenes `instrument`, Budget,
         invertierte These, kein Kelly-Deckel) - nicht ueber `rolle`,
         sondern ueber `hauptgruppe: absicherung`. Fuer die uebrigen elf
         ETF/Rohstoff/Aktien-Symbole: Empfehlung dieselbe Logik wie
         Krypto-`taktisch` (kein bestehender Trennmechanismus, C1: 2-7
         Symbole je Klasse validieren keine eigene Kalibrierung, die
         Rollen-Kette ist bewusst auf EINE gemeinsame Kette migriert) -
         Einschaetzung, keine Messung, siehe F-200.

⚠️ **N-16e ist damit vollständig aufgesetzt.** Mit „kein Stop" (Frage 1)
steht zugleich fest, dass **L2/L3/L4 kein R-/Trailing-Konzept** bekommen
können — ein Ausstieg für Spot bleibt eine reine Potential-Bewertung
(konsistent mit dem übergeordneten Ziel). Das ist die Vorbedingung für
**N-16d**, die jetzt erfüllt ist: **S4 kann mit N-16e als Grundlage
weiterlaufen.**

## C — Hebel: ein Nebenpunkt, kein neuer Kernpunkt

Die Kernfragen (Instrument-Achse, Horizont-Achse, Wegwahl) sind mit
F-184/F-185/N-17 abgedeckt. Ein Punkt lag daneben und ist noch offen:

**N-21: Aufbewahrungsregel für `hebel_triggers`/`open_interest_snapshot`**
— beide Tabellen machen **36,5 % der Produktions-DB** aus (331 MB),
wachsen um ~2,5 Mio Zeilen/Jahr. Eine Regel ist begründbar, **löscht
aber Daten — Nutzerentscheidung, nicht getroffen.**

## D — ⚠️⚠️⚠️ N-22 GEPRÜFT UND KRITISCH GEGENGEPRÜFT (03.09.) — ZURÜCKGEZOGEN

**Vollständig in F-194.** Die Frage von 24.08. — *„braucht A1 mehr
Fallzahl, ist k=2 richtig?"* — steht auf einer Prämisse, die **U-1
(30./31.08.) bereits widerlegt hat**: Stufe 11 entscheidet seither über
das **Potential** (historische Querschnitte), nicht mehr über die
Trefferbilanz-Zellen. Die 50-Fälle-Schwelle gehört zu einem Mechanismus,
der nicht mehr entscheidet — er läuft nur noch als Auskunftszeile in der
Mail mit.

**Und selbst als reine Fallzahl-Frage gestellt, ist `k` der falsche
Hebel:** A1 wählt seit 23.08. ausschließlich HYPE und MORPHO, beide mit
Bestand — A1s eigener Beitrag zur Fallzahl ist **null** (F-182, F-188).
Seit dem 01.09. ist kein einziger neuer Fall ohne Bestand entstanden. Die
scheinbare Aufholrate der letzten 7 Tage (88 Fälle) ist zu **97 % ein
Nachlauf** alter, vor der Umschaltung erstellter Signale — kein Maßstab.

⚠️ **Auswirkungsprüfung der vier denkbaren Hebel** (Nutzervorgabe: *„jede
Änderung kann zu zig Nebenwirkungen führen"*):

| Hebel | Fallzahl-Wirkung | Nebenwirkung |
|---|---|---|
| k erhöhen | marginal, unsicher | verwässert A1s gemessenen Vorsprung (*„ab k=5 ist nichts mehr da"*), mehr Cooldown-Last |
| Cooldown lockern | direkt | öffnet die Stufe, die heute 93,8 % nimmt — Risiko des alten 133-Mails/Tag-Takts |
| Bestand vergrößern | direkt | keine Code-Frage — Kapitaleinsatz-Entscheidung |
| Ausstiege als Fälle zählen | unklar | keine TP/SL-Struktur wie bei Einstiegen — eigenes Design nötig |

**N-22 zurückgezogen.** Kein Eingriff an A1. Der einzige plausible
Restzweck einer Fallzahl-Zielgröße — die Qualität von Rolle G / dem
LLM-Urteil zu beurteilen (Meta-Labeling) — gehört an **N-18** und wird
dort nachgetragen.

## E — kleinere Punkte, gesammelt

| # | Punkt | seit | Aufwand |
|---|---|---|---|
| **N-23** | Baustein „Auslöser statt Grund" (N-8 verwandt): 11 von 20 Zellen ungeprüft, seit 27.08. unangefasst | 27.08. | mittel |
| **N-24** | `marktbreite`-Modul ohne Aufrufer — totes Modul | 23.08. | klein |
| **N-25** | Reparaturliste-Reste: A6 (Mail-Betreff hängt am Lauf) · C1 (Einsatz 800€/1000€, Nutzerentscheidung) · C3 (`crv_spreizung` Config vs. Code) · D3 (27 Config-Schlüssel ohne Leser) | 23.08. | klein je Punkt |
| **N-26** | V3 „Greed-Teilverkauf" — nie gemessen, Daten liegen seit Wochen | — | klein |
| **N-27** | Lebendigkeit/TVL (J) — nie gemessen, 188 Reihen bereit | — | klein |
| **N-28** | Nachrichten (C3) — *„die einzige nie erprobte Informationskategorie"*, Konzept existiert | 24.08. | groß |
| **N-29** | Fehlerbenachrichtigung ist ein blinder Fleck: scheitert das Netz, scheitert auch die Meldung darüber | 02.09. | mittel |
| **N-30** | Remote-Warnschwelle 1,0 s erzeugt ~1.000 Meldungen/Tag ohne Aussagekraft | 27.08. | klein |

⚠️ **N-25 bis N-30 bewusst nicht weiter untersucht** — sie waren im
Original bereits als „offen, nicht dringend" markiert und sind hier nur
gesammelt, damit sie nicht erneut verloren gehen.

## Die Reihenfolge — eingeordnet in den bestehenden Stufenplan

| | | Verhältnis zu S0–S6 |
|---|---|---|
| **N-18/N-19/N-20** | Rolle G, Messbasis, `fakten_roh` | **parallel zu S2/S3** möglich — betreffen die Bewertung der 4 Nicht-Krypto-Klassen, nicht die Krypto-Kette |
| **N-16e** | Positionsführungs-Grundsatzfragen | ✔ **alle vier geklärt (F-199/F-200, 03.09.)** — Vorbedingung für S4/N-16d erfüllt |
| **N-21** | Aufbewahrungsregel | unabhängig, jederzeit |
| ~~N-22~~ | ~~Zielgröße Fallzahl~~ | ✖ **ZURÜCKGEZOGEN (F-194, 03.09.)** — Prämisse durch U-1 überholt, `k` ist nicht der begrenzende Hebel. Restfrage an **N-18** angehängt |
| N-23–N-30 | kleinere Punkte | nach Bedarf, konkurrieren nicht mit S0–S6 |

Verwandt: **S6** (Messbasis, jetzt mit Zahlen) · **N-16** (jetzt mit N-16e) · CLAUDE.md (übergeordnetes Ziel)

---

# ⚠️⚠️ STAND NACH DEM 04.09. — was heute abgeschlossen wurde und was OFFEN bleibt

*Nutzervorgabe 03.09.: „Wir müssen zukünftig alle anstehenden Themen in
Pläne übernehmen, sonst vergessen wir diese." Dieser Abschnitt hält den
Stand nach dem Messtag fest.*

## Was am 04.09. ABGESCHLOSSEN wurde

| | Ergebnis | Fakt |
|---|---|---|
| **S2 / N-17-0** | ✖ Nullbefund — Stop/Volatilität sagen die Dauer nicht voraus | F-202 |
| **N-17a** | ⚠️ H2-Kalibrierung ernüchternd — Schwelle ohne Trennschärfe | F-203 |
| **N-17b** | ✔ vier neue Kandidaten, Redundanz geprüft, zwei Kombinationen gemessen | F-205, F-206 |
| **N-17c** | ✔ die **Brücke** gebaut: Beitragspunkte statt „trägt/trägt nicht" | F-210 |
| **N-17d** | ✖ Hypothese widerlegt (umgekehrtes Vorzeichen), `vola` fällt an der Validierung | F-211 |
| Nebenprüfungen | Kombination verbessert die live Sperre nicht (F-207); F-165 auf sauberer Basis bestätigt (F-209) | F-207–F-209 |

**Der harte Kern in einem Satz:** Für die Schwelle 0,080 R sind **+2,67
Beitragspunkte** nötig; der beste Kandidat auf der Hebel-Geometrie liefert
**+0,51**. Die Fachliteratur nennt **1–3 Punkte** als realistisch für
einen Einzelfaktor — die Schwelle verlangt also mehr, als ein einzelner
Faktor überhaupt hergeben kann.

## ⚠️⚠️⚠️ N-31 — DIE OFFENE LÜCKE, die alles andere überwiegt

> **Tragen die registrierten Beiträge auf der Ankermenge, die die AUSWAHL
> übrig lässt — oder nur auf der freien Menge?**

**Warum das der wichtigste offene Punkt ist:** Alle Beiträge — auch die
**live registrierten** Funding und Turnover — sind auf **rohen** Ankern
gemessen (516 Symbole × ~2.900 Tage). Die Kette bewertet aber nicht diese
Menge, sondern was nach zwölf Trichterstufen übrig ist, und die Auswahl
*„wählt immer dieselben"*.

**F-183** (03.09.) hat die Frage gestellt — *„eine Größe kann auf der
freien Menge trennen und auf der selektierten nicht"* — und nur für die
**Ausstiegs**seite halb beantwortet. Für den Einstieg lautete die
Begründung *„der Zeitpunkt ist frei wählbar"*: das verteidigt die
**Zeit**achse, **nicht die Asset-Achse**.

    Zeitachse    ✔ verteidigt (F-183)
    Asset-Achse  ✖ fuer KEINEN Beitrag geprueft, auch nicht fuer die
                   live registrierten

⚠️ **Das ist ein Befund über das laufende System, nicht über einen
Kandidaten** — und deshalb vorrangig vor jedem neuen Kandidaten.

**Datenlage:** vorhanden. NB-Export mit den echten Trichterdurchläufen
(`K:\My Drive\Claude_Austauschordner\DB_Backups\`, Stand 03.09.).
**Werkzeuge:** `rechne_sperren_zusammen.py`, `pruefe_kette_je_asset.py`,
`rechne_takt_je_asset.py` — alle vorhanden, keines dafür benutzt.

## N-32 — die Schwelle selbst ist der Engpass, nicht die Kandidaten

Aus F-210 + Literatur: Kein Einzelfaktor erreicht +2,67 Punkte. Entweder
- die Schwelle 0,080 ist für die kurze Geometrie zu hoch angesetzt
  (sie wurde auf **H20** kalibriert — R-R9), **oder**
- es braucht mehrere Beiträge gemeinsam (dann ist N-31 die Vorfrage).

⚠️ **Nutzerentscheidung**, nicht durch Messung zu ersetzen.

## N-33 — H-2 (der Gabelpunkt) ist entscheidungsreif, aber NICHT entschieden

Aus F-163/F-164: gebührenfrei liefern `hebel` und `spot` **dieselbe**
Bewertungszahl; der einzige legitime Hebel ist der **Horizont**. Nach
F-165/F-205–F-211 ist die verfügbare Kandidatenmenge dafür
**vollständig durchgemessen**, mit konsistentem Nein.

    Entweder  der Hebel bleibt ausgesetzt
    oder      er wird bewusst als AUSFUEHRUNGSVARIANTE ohne eigene
              Begruendung gefuehrt (Stop-Rechnung, wie heute)

⚠️ **Nutzerentscheidung.** Die Datenlage dafür ist jetzt vollständig.

## N-34 — stehende Vorgaben, heute ergänzt

| | |
|---|---|
| **Keine Sperre in erster Instanz** | Ein Kandidat gehört zuerst als **Beitrag** geprüft. Der Trichter hält mit zwölf Stufen ohnehin fast alles; eine 13. Sperre geht gegen *„mehr Signale durch Qualität"* und *„aufmachen statt einschränken"* |
| **Beitragstabelle ist KEIN Nachweis** | Erst die Regel-Validierung (Band, Hälften, Positivkontrolle) entscheidet. Bei `vola` zeigten beide in verschiedene Richtungen — F-211, dieselbe Falle wie der Schnittabstand am 31.08. |
| **Parameter horizontproportional** | Gemessene Handelsdauer **2,0 Tage** (F-202). Rückblicke von 25–125× dieser Dauer messen etwas anderes als den Trade |
| **Die Einzelmessung ist die Fingerübung** | Was zählt, ist die Wirkung **in der Kette** — siehe N-31 |

## Die Reihenfolge von hier

    1  N-31   die selektierte Ankermenge  <- VORRANG, betrifft das
              laufende System
    2  N-33   H-2 entscheiden (Nutzer)    <- Datenlage vollstaendig
    3  N-32   Schwelle (Nutzer)           <- haengt an N-31
    4  N-18/N-19/N-20   die 4 Nicht-Krypto-Klassen (unveraendert offen)
    5  N-16d  Ausstiegsbewertung (Vorbedingung N-16e ist erfuellt)

⚠️ **Nicht auf dieser Liste:** weitere Einzelkandidaten (BTC-Führung,
Bodenbildung). Sie sind nicht falsch, aber nach F-211 nachrangig — solange
N-31 offen ist, weiß niemand, ob ein neuer Kandidat in der Kette
überhaupt ankommt.

---

# ⚠️⚠️ N-35 — „VARIANTE B" (Intraday): die Vorabfestlegung UND die Dimensionierung (04.09.2026)

*Nutzerauftrag: Doku prüfen, was bereits geplant/gemessen/abgestimmt ist —
dann die stündliche Auswertung, „versichere dich vorher, dass alles sauber
dimensioniert ist: 1. für die Messung, 2. für unser System".*

## 1 — Was bereits abgestimmt ist (Doku-Nachschau, R-R10 nachgeholt)

**Die Stundenauflösung ist eine Nutzerentscheidung vom 01.09.2026**,
dokumentiert in `hole_terminmarkt_historie.py`:

> **„3 JAHRE, 1 STUNDE, EIGENE DATEI"**
> `1 Stunde` — *„Sie passt zum **VERSANDTAKT**… ein 5-Minuten-Signal ist
> veraltet, bevor es gelesen wird. Und die **Praxisquelle des Nutzers**
> nennt für MACD ausdrücklich den 1-Stunden-Chart."*

- Das Rohaarchiv liegt in **5 Minuten** vor; verdichtet wurde auf Stunden,
  **letzter Wert statt Mittel** (OI ist ein Bestand, Methodik 2.85).
- Ausdrücklich **reversibel**: *„Wenn sich zeigt, dass 5 Minuten nötig
  sind, lädt man neu."*
- **Zweck benannt, nie ausgeführt** — F-167: *„Die Stundenauflösung wird
  nur für **Variante B (Intraday-Ereignisse)** gebraucht."*

⚠️ Die Stundentabelle ist bisher **ausschließlich als Tages-Rückfallquelle**
benutzt worden: `lade_terminmarkt()` führt beide zusammen, und die
Tagestabelle gewinnt. In eigener Auflösung wurde sie nie ausgewertet.

## 2 — Dimensionierung MESSUNG — ⚠️ sie reicht NICHT

    STUENDLICH   2023-09-01 .. 2026-08-30 | 32 Symbole | 700.943 Zeilen
      Kalendertage      1.095  ->  12,2 Bloecke      ⚠️ Mindestmass ist 20
      Symbole je Stunde Median 32, min 15, 100 % der Stunden >= 15   ✔
      Stunden je Tag    Median 24 von 24                             ✔

    TAGESTABELLE 2021-12-01 .. 2026-08-31 | 100 Symbole | 1.735 Tage
                                          ->  19,3 Bloecke

⚠️⚠️ **12,2 Blöcke ist exakt die Lage, die F-167 zur Zurückstellung geführt
hat** (*„1.066 Tage (3 Jahre) → 12 Blöcke ⚠️"*). Jetzt zu messen hieße,
denselben Fehler **wissentlich** zu wiederholen.

⚠️ **Die Blockgröße 90 wird NICHT gesenkt.** Methodik 2.95 verbietet genau
das, und ein kürzerer Block wäre hier die selbstdienliche Anpassung, die
das Ergebnis erzeugt statt es zu prüfen.

⚠️ **Zweiter Mangel: 32 WATCHLIST-Werte, keine Messbasis.** F-167 hält das
als **meinen eigenen** Fehler fest: *„Watchlist statt Messbasis… sonst
misst man seine eigene Auswahl."* Für einen Querschnitt je Stunde wäre das
derselbe Fehler ein zweites Mal.

## 3 — Dimensionierung SYSTEM — teils ja, teils nein

| | Wert | reicht für Stundensignale? |
|---|---|---|
| Kettentakt | **alle 15 Minuten** (`HEBEL_SCREENING_INTERVAL_MINUTES`) | ✔ schnell genug |
| Cooldown Krypto Spot | 15 h | ✖ höchstens ~1,6 Signale/Tag/Asset |
| **Cooldown wenn gehebelt** | **3,5 h** (`VORGABE_WENN_GEHEBELT`) | ✔ **sub-Tag ist vorgesehen** |
| Cooldown Akkumulation | 48 h | ✖ |
| **Live-OI der Produktion** | `openInterestHist **period=1d**` | ✖ **holt Tageswerte** |
| **OHLC-Auffrischung** | alle **24 h** | ✖ die Kursreihe ist täglich |

⚠️⚠️ **KORREKTUR 04.09. — dieser Absatz stand hier FALSCH und wird nicht
gelöscht, sondern richtiggestellt.**

Ich hatte geschrieben: *„Die Produktion könnte ein Stundensignal heute gar
nicht rechnen… ein Intraday-Beitrag verlangt zwei Datenänderungen im
Betrieb."* **Beides ist falsch, und der Stand vom 02.09. sagt es genau
umgekehrt.**

**Nutzereinwand:** *„Warum benötigt die Produktion die vollständigen
Marktdaten — das sollte doch nur bei der Kalibrierung erforderlich sein?"*
— Richtig, und genau so ist es gebaut.

`baue_messbasis_paket.py` (02.09.) hält fest: **drei der vier Datenbanken
werden vom Produktionscode NUR nach der Symbolliste gefragt:**

    funding    SELECT DISTINCT symbol FROM funding
    turnover   SELECT DISTINCT symbol FROM splycur
    oi         SELECT DISTINCT symbol FROM terminmarkt_tag
               UNION SELECT DISTINCT symbol FROM terminmarkt

*„Aus 176 MB werden damit wenige Kilobyte."* Und `messdaten.db` (1,5 GB)
wird **bewusst nicht ans Notebook übertragen** — bestätigt in
`marktrang.messbasis()`: *„`messdaten.db` (166 MB) wurde bewusst nicht
übertragen"*, ein **zugestimmter** Zustand, kein Mangel.

**Die Naht ist im Code selbst benannt** (`marktrang.oi_werte`):

    gemessen    OI am Tagesschluss aus dem Archiv (data.binance.vision)
    angewandt   dieselbe Groesse aus openInterestHist period=1d, limit=2
                122 Symbole in ~36 s, Gewicht 122 gegen 2400/Minute

**Was ein Stundensignal im Betrieb WIRKLICH kostet:**

| | |
|---|---|
| OI-Abruf | `period=1d` → **`period=1h`** — derselbe Endpunkt, dieselbe Anfragenzahl |
| Zwischenspeicher | Tages- → Stundenverfall: 122 × 24 = 2.928 Abrufe/Tag gegen **2.400 je Minute** — unkritisch |
| Symbolliste | **unverändert** — die 100 Messbasis-Werte stehen bereits in `terminmarkt_tag` |
| NB-Paket | **unverändert** — es enthält nur Symbollisten |
| Stündliche Kursreihe | **NICHT nötig** für die drei vorab benannten Kandidaten (alle Terminmarkt, keine Kursgrößen). Die R-Geometrie bleibt tagesbasiert, passend zur gemessenen Haltedauer von 2,0 Tagen |

⚠️ **Der Archivlauf (100 × 5 Jahre) ist damit reine MESSUNG, desktopseitig.
Er verändert am Notebook nichts.**

⚠️ **Meine Lehre daraus:** Ich hatte aus zwei Konstanten
(`period=1d`, `OHLC_REFRESH_INTERVAL_HOURS=24`) auf einen Betriebsaufwand
geschlossen, ohne die Trennung von Messung und Anwendung nachzuschlagen,
die seit dem 02.09. dokumentiert und **gebaut** ist. Das ist derselbe
Fehlertyp wie bei den Stundendaten selbst — siehe die stehende Vorgabe
unten.

✔ **Aber die Absicht ist im System bereits angelegt:** der Cooldown für
gehebelte Signale steht auf **3,5 Stunden** — das System ist für einen
schnelleren Hebel-Takt gebaut, nur nicht mit Daten versorgt.

## 4 — Die Vorabfestlegung (gilt, sobald die Datenlage steht)

    Frage        Sagt die Terminmarktlage einer STUNDE etwas ueber die
                 naechsten Stunden - jenseits dessen, was der Tageswert
                 schon sagt?
    Zielgroesse  R ueber H+4 Stunden, vorzeichenbehaftet
    Klammer      STUNDENKLAMMER (Querschnitt je Stunde, >=15 Symbole)
    Kandidaten   oi_aenderung_1h · taker_verh · konten_verh   (vorab, 3)
    Kontrolle    `zufall` mitlaufend
    Block        ueber KALENDERTAGE (24 Stunden eines Tages sind nicht
                 24 Beobachtungen - Methodik 2.107), Blockgroesse 90
    ⚠️ Gegen     dieselbe Groesse auf TAGESbasis - traegt die Stunde NUR
                 dann, wenn sie MEHR sagt als der Tageswert. Sonst haben
                 wir Aufwand ohne Gewinn.

    NUTZBAR      Band ueber null, Kontrolle still, UND besser als die
                 Tagesfassung im gepaarten Vergleich (2.105)

## 5 — Der Weg dorthin, mit Kosten

`hole_terminmarkt_historie.py` ist **wiederaufnehmbar, ohne Kontingent**
(öffentliches Archiv, kein Schlüssel). Gemessener Durchsatz: 6,8 Anfragen/s.

    A  32 Symbole auf 5 Jahre     +23.360 Anfragen   ~  1 h   -> 20 Bloecke
    B  100 Symbole auf 5 Jahre   ~182.500 Anfragen   ~7,5 h   -> 20 Bloecke
                                                                + Messbasis
                                                                statt Watchlist

⚠️ **Nur B behebt BEIDE Mängel.** A repariert die Blockzahl, lässt aber die
Watchlist-Verzerrung stehen — und die ist der Fehler, den F-167 bereits
einmal gekostet hat.

**Empfehlung: B, und erst danach messen.** Bis dahin ist N-35 blockiert —
nicht aus Vorsicht, sondern weil das Ergebnis sonst nach unserem eigenen
Maßstab nicht entscheidbar wäre.

---

# ⚠️⚠️⚠️ KONSOLIDIERTE PLANUNG NACH DEM 04.09. — N-31 bis N-36

*Diese Liste ersetzt die frühere Reihenfolge am Ende der GESAMTSICHTUNG.
Nutzervorgabe: „damit nichts verloren geht".*

## ⚠️ N-36 — DIE NEUEINORDNUNG DES HEBELS (aus der Nutzerrecherche 04.09.)

**Nutzerrecherche zu algorithmischen Hebel-Entscheidungen**, Säule 3
wörtlich: *„Der Bot wählt den Hebel **dynamisch basierend auf der
Volatilität** (ATR)… um das Risiko pro Trade mathematisch immer exakt bei
1 % zu halten."*

⚠️⚠️ **Das ist keine Entscheidung „Hebel ODER Spot" — das ist
Positionsgrößenrechnung. Der Hebel FÄLLT AN, er wird nicht gewählt.**

Deckt sich mit der externen Fachrecherche (N-17d): kein peer-reviewed
Kriterium für Hebel-**Timing**; Hebel wird durchgehend als Sizing- und
Kapitaleffizienzfrage behandelt (Vola-Targeting, Kelly). Frazzini/Pedersen
zeigen sogar die Gegenrichtung — eingebauter Hebel **kostet** eine Prämie.

**Und wir haben alle drei Säulen des Regelwerks bereits:**

| Recherche | bei uns |
|---|---|
| CRV-Prüfung, Ziel 2–3× Stop | ✔ CRV fest 2,0 (`potential.py`) |
| Hebel dynamisch aus Volatilität | ✔ `hebel = verlustanteil / stop_rel` |
| Funding Rate Check | ✔ `funding_fuenftel` registrierter Beitrag |

> **Folge für H-2/N-33: die Frage „bekommt die Bewertung eine
> Instrument-Achse?" ist eine Kategorienverwechslung.** Die Praxis stellt
> sie nicht. Was seit 01.09. als „Kompromiss" geführt wird (5.2: der Hebel
> ist eine Ausführungsfrage), **ist die branchenübliche Lösung** — nicht
> ein Mangel.

⚠️ **Zwei Kandidaten der Recherche sind bei uns bereits gemessen und
gefallen:** EMA-200-Durchbruch = unser Schnittabstand (31.08. gefallen);
CVD/Aggressive Market Orders = `taker_verh`/`taker_bias` (Nullbefund).
Und der Bollinger-Squeeze prognostiziert **Volatilität, nicht Richtung** —
derselbe Befund wie bei allen unseren Pfadmaßen.

⚠️ **Was wir NICHT haben:** Orderbuchtiefe und Liquidations-Cluster. Beide
nur als Momentaufnahme sammelbar, rückwirkend nicht verfügbar → nach 2.95
ein Jahr Sammeln vor der ersten belastbaren Messung. **Und
„Liquidations-Hunting" funktioniert mit Größe und Geschwindigkeit** — wer
auf Stundenbasis folgt, ist nicht der Jäger, sondern die Liquidität.

## Die Reihenfolge — verbindlich ab 04.09.

| # | Punkt | Art | Status |
|---|---|---|---|
| **1** | **N-31** — tragen die Beiträge auf der **selektierten** Ankermenge? | Messung | **VORRANG** — betrifft das laufende System, Daten und Werkzeuge liegen bereit |
| **2** | **N-36/N-33** — Hebel als Sizing-Frage neu einordnen | **Nutzerentscheidung** | entscheidungsreif, Datenlage vollständig |
| **3** | **N-35** — Variante B (Intraday) | Messung | **blockiert** bis Archiv erweitert (siehe unten) |
| **4** | **N-32** — Schwelle 0,080 auf kurzer Geometrie | **Nutzerentscheidung** | hängt an N-31 |
| 5 | N-18/N-19/N-20 | Bau | unverändert offen (4 Nicht-Krypto-Klassen) |
| 6 | N-16d | Bau | Vorbedingung N-16e erfüllt |

## ⚠️ Was N-35 konkret blockiert — und was es kostet

    Mangel 1   1.095 Tage = 12,2 Bloecke, Mindestmass 20   (F-167-Lage)
    Mangel 2   32 WATCHLIST-Werte statt Messbasis          (F-167-Fehler)

    Behebung   hole_terminmarkt_historie.py, 100 Symbole x 5 Jahre
               ~182.500 Anfragen, ~7,5 h, wiederaufnehmbar,
               oeffentliches Archiv, KEIN Kontingent

⚠️ **KORRIGIERT 04.09.** — hier stand „zwei Betriebsänderungen". Richtig
ist **eine**, und sie ist klein:

    marktrang.OI_HIST   period=1d  ->  period=1h   (+ Stundenspeicher)

Die stündliche Kursreihe wird NICHT gebraucht — die drei Kandidaten sind
Terminmarktgrößen. Symbolliste und NB-Paket bleiben unverändert; der
Archivlauf ist reine Messung, desktopseitig. Vollständig unter N-35.

✔ **Der Cooldown steht bereits richtig:** `VORGABE_WENN_GEHEBELT = 3,5 h`
— das System ist für einen schnelleren Hebel-Takt gebaut, nur nicht mit
Daten versorgt.

## Die stehenden Vorgaben aus diesem Tag (N-34, ergänzt)

| | |
|---|---|
| **Keine Sperre in erster Instanz** | Ein Kandidat gehört zuerst als **Beitrag** geprüft |
| **Beitragstabelle ist kein Nachweis** | Erst die Regel-Validierung entscheidet (F-211, `vola`) |
| **Parameter horizontproportional** | Gemessene Handelsdauer 2,0 Tage (F-202) |
| **Die Einzelmessung ist die Fingerübung** | Was zählt, ist die Wirkung **in der Kette** (N-31) |
| **Blockgröße nie senken** | 2.95 — sie zu senken erzeugt das Ergebnis, statt es zu prüfen |
| **Messbasis statt Watchlist** | P6/F-167 — sonst misst man die eigene Auswahl |
| ⚠️⚠️ **Messung und Anwendung sind GETRENNT gebaut** | Die Produktion liest aus drei der vier Datenbanken **nur die Symbolliste**; `messdaten.db` ist am Notebook bewusst nicht vorhanden. Wer aus einer Konstante im Betriebscode auf Datenbedarf schließt, ohne diese Naht nachzuschlagen, erfindet Hürden (04.09., korrigiert unter N-35) |
| ⚠️ **R-R10 gilt auch für die eigene Datenlage** | Die Stundendaten existierten, weil sie am 01.09. **bestellt** wurden. Ich habe sie am 04.09. als „Fund" präsentiert. **Vor jeder Aussage über vorhandene Daten: nachschlagen, warum sie da sind** |

---

# ⚠️⚠️⚠️ N-31 — DIE VORABFESTLEGUNG (04.09.2026)

*Nutzervorgabe: „das entspricht unserer Regel — was wir nicht haben,
simulieren wir."*

## Warum simuliert wird, und nicht gemessen

Aus dem NB-Export (9.474 Rollen-Läufe, bis 03.09.) abgelesen:

    hinein            124.194
    anlass verliert    29.461   (28,4 %)
    auswahl verliert   17.666   (42,7 %)
    wiederholung       58.729   (94,1 %)   <- der dominante Filter
    ENTSCHEIDER         1.849 Anker gesehen, 1.576 verworfen (85,2 %)
    heraus              2.115

**Die Beiträge wirken auf 1.849 von 124.194 Ankern — 1,5 %.** Kalibriert
wurden sie auf 612.000–724.000 rohen Ankern.

⚠️ **Und die beitragsbasierte Entscheidung läuft erst seit dem 02.09.**
Davor verwarf die Stufe mit „trägt sich nicht" (der alten
Kostenprüfung); die Umschaltung ist im Log tagesgenau sichtbar
(01.09.: 44/0 · 02.09.: 15/16 · 03.09.: 0/25). **Im Export sind das
41 beitragsbasierte Entscheidungen** — nach eigenem Maßstab nichts.

> **N-31 ist aus Produktionsdaten heute nicht beantwortbar. Die
> Selektionsregel ist aber bekannt und auf der Historie nachbaubar.**

## Die Selektionsregel — aus dem Betriebslog ABGELESEN, nicht geschätzt

    Grund     "Rang N von 41 nach der Entwicklung der letzten
               250 Handelstage"                  17.660 Verwerfungen
    Rang 2    nur     11 mal verworfen
    Rang 3    550 mal verworfen                  ->  k = 2
    Feld      Median 41 Werte je Lauf

**Selektionsstärke: 2 von 41 ≈ 5 % je Tag, nach 250-Tage-Momentum.**

## Was gemessen wird

    Frage       Tragen `funding_fuenftel` und `turnover_fuenftel` auch auf
                der SELEKTIERTEN Menge - dem oberen Rand des
                250-Tage-Momentum-Rangs?
    Horizont    H20 - die Geometrie, auf der beide registriert sind
    Rang        wie in der Produktion ueber die MESSBASIS gebildet, nicht
                ueber die selektierte Teilmenge (`marktrang` tut genau das)
    Stufen      5 % (die Produktion) · 10 % · 20 % · 100 % (keine Auswahl)
                -> eine Dosis-Wirkungs-Kurve, keine freie Suche
    ⚠️ Ent-     die Entscheidung haengt an der 5-%-Stufe. Die uebrigen
    scheidung   sind Einordnung und duerfen den Befund nicht allein tragen.

⚠️ **DIE TAGESKLAMMER TRAEGT HIER NICHT.** Bei 5 % je Tag bleiben zu
wenige Werte für einen Vergleich innerhalb des Tages. Nach **Methodik
2.109** wird deshalb **gepoolt gemessen und gepoolt gemischt** — die
Kontrollgröße durchläuft dieselbe Verengung.

⚠️ **GEPAARTER VERGLEICH (2.105):** gemessen wird die **Differenz**
zwischen selektierter und freier Menge, nicht zwei Bänder nebeneinander.

⚠️ **POSITIVKONTROLLE AUF DIE DIFFERENZ.** F-183 hat gezeigt, dass genau
sie fehlen kann: dort fand die Anlage einen aufgeprägten Abfall von
0,02 R bei Funding **nicht** — und damit war „kein Abfall" dort keine
Aussage. Findet sie ihn hier nicht, gilt derselbe Vorbehalt.

## Vorab festgelegt — was als Befund gilt

    TRAEGT WEITER   der Beitrag traegt auf der 5-%-Menge, UND der gepaarte
                    Abfall gegen die freie Menge ist nicht von null zu
                    trennen, UND die Positivkontrolle auf die Differenz
                    feuert
    FAELLT AB       der Abfall ist von null zu trennen -> die Beitraege
                    sind auf der Menge, auf der sie WIRKEN, schwaecher als
                    dort, wo sie GEMESSEN wurden
    NICHT ENTSCHEIDBAR  die Positivkontrolle feuert nicht (2.88)

## ⚠️ Die Näherung, benannt statt versteckt

Die Produktion wählt 2 aus ~41 **Watchlist**-Werten; die Historie kennt
diese Watchlist nicht rückwirkend. Nachgebaut wird deshalb die
**Selektionsstärke** (oberste 5 % je Tag), nicht die absolute Zahl. Das
hält die Schärfe des Filters fest und gibt zugleich eine brauchbare
Stichprobe — die absolute Zahl 2 wäre je Tag zu klein für jede Statistik.


---

# ⚠️⚠️⚠️ STARTPUNKT FÜR DEN 05.09. — hier weitermachen

*Stand nach dem Messtag 04.09. Alles darüber ist Historie; diese Liste ist
der Einstieg.*

## Der Satz, der den Tag zusammenfasst

> **Die Bewertung ist besser als gedacht, der Takt ist schlechter als
> gedacht.**

Die Beiträge tragen auf der Menge, auf der sie wirken, sogar **stärker**
als dort, wo sie gemessen wurden (F-212). Aber der stärkste Filter der
ganzen Kette ist kein Bewerter, sondern eine **Uhr** — und die läuft
anders, als sie soll (F-213).

## ➊ ZUERST: F-213 zu Ende bringen (klein, konkret, ~30 min)

    Zustand   Der Cooldown sperrt 94,1 % und ist damit der staerkste
              Filter der Kette. Trotzdem stehen 67 % der Signale enger
              zusammen, als er erlaubt - und zwar AUSSCHLIESSLICH im
              15-Stunden-Zweig (85,5 % verletzt), waehrend der
              3,5-Stunden-Zweig sauber ist (13,1 %).

    Ausge-    zweiter Schreibpfad · quelle_kette · zeitliche Aenderung ·
    schlossen Aufrufstelle · "3,5 h gilt fuer alles"

    Schritt   `wiederholung.gesperrt_bis()` an ECHTEN Zeilen aufrufen und
              den Rueckgabewert gegen den erwarteten halten - dieselbe
              Datenlage, an der die Funktion im Betrieb entschieden hat.
              Kein neues Werkzeug, ein gezielter Aufruf.

⚠️ **Warum zuerst:** Regel 1 lautet *„Der Takt ist nie Signalgeber."* Was
die Kette heute durchlässt, folgt einem Takt von **3,7 Stunden**. Solange
das gilt, ist jede Bewertungsverbesserung nachgelagert.

## ➋ DANN: N-35 (Intraday) — die Daten sollten über Nacht da sein

    Vorabfestlegung  steht (9.6, Abschnitt N-35)
    Probelauf        ✔ erfolgreich (144 Stundenzeilen, 0 Fehler)
    Nachtlauf        100 Messbasis-Symbole x 5 Jahre, ~7 h
    Danach pruefen   `terminmarkt` muss ~100 Symbole und ~1.825 Tage
                     zeigen (heute: 34 Symbole, 1.095 Tage = 12 Bloecke)

⚠️ **Vor der Messung nachzaehlen**, ob die 20 Blöcke wirklich erreicht
sind. Werden sie es nicht, wird **nicht** gemessen.

## ➌ OFFEN, unverändert

| | | |
|---|---|---|
| **N-31 Turnover** | nicht entscheidbar aus Datenlage | Positivkontrolle feuert nicht (2.88) |
| **N-32** Schwelle 0,080 auf kurzer Geometrie | **Nutzerentscheidung** | hängt an N-31 |
| **N-33/N-36** Hebel als Sizing-Frage | **Nutzerentscheidung** | entscheidungsreif, Datenlage vollständig |
| N-18/N-19/N-20 | Bau | die 4 Nicht-Krypto-Klassen |
| N-16d | Bau | Vorbedingung erfüllt |

## ➍ Was heute dazugelernt wurde — als stehende Vorgaben

| | |
|---|---|
| **Keine Sperre in erster Instanz** | ein Kandidat gehört zuerst als **Beitrag** geprüft |
| **Beitragstabelle ist kein Nachweis** | erst die Regel-Validierung entscheidet (F-211, `vola`) |
| **Parameter horizontproportional** | gemessene Handelsdauer 2,0 Tage |
| **Die Einzelmessung ist die Fingerübung** | was zählt, ist die Wirkung in der Kette |
| **Messung und Anwendung sind getrennt gebaut** | die Produktion liest nur Symbollisten; wer aus einer Betriebskonstante auf Datenbedarf schließt, erfindet Hürden |
| **R-R10 gilt auch für die eigene Datenlage** | vorhandene Daten sind fast nie Zufall — nachschlagen, warum sie da sind |
| ⚠️⚠️ **Die Reproduktionskontrolle ist die wichtigste** | sie hat heute **dreimal** einen Befund gerettet oder gekippt (F-207, F-210, F-212). Ein bei zwei Größen **identischer Faktor** ist die Signatur eines Definitionsunterschieds, nie von Rauschen |

## Die Bilanz des Tages, ehrlich

**Kein einziger neuer Beitrag registriert.** Gefunden wurden: ein
bestätigter Befund (F-212), eine geschlossene Kette (F-209/F-210), eine
Neueinordnung des Hebels (N-36), ein eingegrenzter Betriebsfehler
(F-213) — und **über ein Dutzend eigener Messfehler**, alle von den
Kontrollen gefunden, keiner vom Zufall.


---

# ⚠️⚠️⚠️ N-37 — IST DIE BEWERTUNG KALIBRIERT? Die Vorabfestlegung (05.09.2026)

*Nutzervorgabe: „was wir nicht haben, simulieren wir“ — und: „präzise
aufsetzen, vorher genau in die Doku, um die bisherigen Fehler zu
vermeiden.“*

## Die Frage

> **Liefert ein höheres Potential tatsächlich eine höhere Trefferquote?**

Sie ist die **Vorbedingung für jede Hebelabstufung** (N-36/H-2): Kelly
ohne kalibriertes µ ist eine Formel ohne Eingabe. Und sie beantwortet
zugleich, ob eine Leiter überhaupt begründbar ist oder ob es beim Gate
bleibt — die Architekturfrage folgt der Datenlage, nicht umgekehrt.

## Warum simuliert wird — und nicht gesammelt

Das Potential wird **nirgends gespeichert**: nicht in `signals`, in keinem
der fünf JSON-Felder. Nur die 41 verworfenen Fälle stehen als Text im
Ablehnungsgrund. Mein erster Reflex war „ab jetzt mitschreiben“ — das ist
die **fünfte Variante derselben Ausrede**, vor der die stehende Vorgabe
warnt (*„n reicht nicht“, „in X Wochen erneut prüfen“*).

**Alle Eingaben sind historisch rekonstruierbar**, und die echte Funktion
`potential.rechne()` kann sie verarbeiten.

## ⚠️ Die vier Fallen dieser Messung — und ihre Behandlung

### Falle 1: ZIRKULARITÄT — die größte

Die Beitragsstufen sind **in-sample gefittet**: `rechne_*_beitrag.py`
leitet sie aus dem Ergebnis je Fünftel ab. Auf denselben Ankern zu
messen, ob ein höheres Fünftel ein besseres Ergebnis bringt, ist **per
Konstruktion wahr** und beweist nichts.

    Behandlung   Stufen auf der ERSTEN Haelfte fitten (echte
                 `beitragstabelle()`), Kalibrierung auf der ZWEITEN
                 Haelfte pruefen. Out-of-sample, kein Ueberlapp.

### Falle 2: DIE FORM DER ZIELGRÖSSE (Methodik 2.85)

Das Potential ist für ein **Barrierensystem** definiert:
`quote × CRV − (1−quote)` mit `quote = P(Ziel vor Stop)`. Es ist **keine**
Aussage über die Rendite nach festen 20 Tagen. Gegen `in_r` zu
kalibrieren wäre exakt der Formfehler, vor dem 2.85 warnt.

    Behandlung   Barrieren-Ausgang aus dem PFAD, ueber die bestehende,
                 validierte `messe_zielregel.ergebnisse()`: Ziel = e+2r,
                 Stop = e-r, Stop gewinnt bei Gleichstand, Datenbrueche
                 entfernt. Gezaehlt werden nur ENTSCHIEDENE Anker
                 (Ziel oder Stop getroffen) - dieselbe Konvention wie
                 die 48,2-%-Trefferquote der Kette.

### Falle 3: DIE ARITHMETIK STEHT SCHON DA

`project_barrierensystem_erwartungswert_null`: auf driftfreiem Pfad ist
`quote = 1/(1+CRV) = 33,3 %` **per Konstruktion** — gemessen 34,0 % über
19.891 Anker. Die Bewertung behauptet also nicht „irgendeinen“ Vorteil,
sondern eine **eng begrenzte Verschiebung**:

    Potential 0,000  ->  vorhergesagte quote  33,3 %
    Potential 0,080  ->                       36,0 %   (unsere Schwelle)
    Potential 0,133  ->                       37,8 %   (das Maximum)

    Die gesamte Behauptung ist ein Shift von 4,5 Prozentpunkten.

⚠️ **Das ist die eigentliche Prüfgröße** — nicht „trägt/trägt nicht“,
sondern: liegt die realisierte Quote je Potentialgruppe **da, wo die
Bewertung sie hinsagt**?

### Falle 4: AUFLÖSUNG UND MACHT — vorab gerechnet, nicht hinterher beklagt

    Um 33,3 % von 37,8 % zu trennen (alpha 5 %, Macht 80 %):
        rund 1.800 ENTSCHIEDENE Anker je Gruppe

    Verfuegbar: 516 Reihen x ~2.700 Anker  ->  ueber 1 Mio Anker
    Bindend ist NICHT die Ankerzahl, sondern die Blockzahl:
        ~2.900 Kalendertage / 90  =  ~32 Bloecke        OK, ueber 20

⚠️ Anker überlappen (Vorwärtsfenster 60 Tage) — die Inferenz läuft
deshalb über **Block-Bootstrap über Kalendertage** (2.107), nicht über
Anker.

## Was gemessen wird

    Zielgroesse   quote = Anteil "Ziel vor Stop" unter den ENTSCHIEDENEN
    Geometrie     Ziel e+2r, Stop e-r  (CRV 2,0 - der registrierte Wert)
    Gruppen       Potentialstufen, wie sie tatsaechlich anfallen
                  (nicht vorab in Quantile gezwungen - die Aufloesung
                  IST Teil des Ergebnisses)
    Klammer       Block-Bootstrap ueber Kalendertage, Blockgroesse 90
    Split         erste Haelfte fitten, zweite Haelfte pruefen

## Die Kontrollen — jede aus einem früheren Fehler

| | |
|---|---|
| **Reproduktion** | die auf der ersten Hälfte gefitteten Stufen müssen den registrierten Werten nahekommen. Weichen sie stark ab, ist der Split nicht repräsentativ — **dann gilt kein Befund**. Diese Kontrolle hat gestern dreimal getragen (F-207, F-210, F-212) |
| **Zufallskontrolle** | Potentialwerte je Kalendertag mischen → die Kalibrierung muss verschwinden |
| **Positivkontrolle** | eine künstliche Welt mit bekanntem Zusammenhang → muss gefunden werden. Findet sie ihn nicht, ist ein Nullbefund **untermächtig, nicht widerlegend** (2.88) |
| **Basisraten-Anker** | die Gruppe mit Potential ≈ 0 muss bei ≈ 33,3 % landen. Tut sie das nicht, stimmt etwas an der Barrieren-Rechnung, nicht an der Bewertung |

## Vorab festgelegt — was als Befund gilt

    KALIBRIERT       die realisierte Quote steigt monoton ueber die
                     Potentialgruppen UND die Steigung ist von null zu
                     trennen UND die Zufallskontrolle ist still
    NICHT KALIBRIERT die Steigung ist nicht von null zu trennen, obwohl
                     die Positivkontrolle feuert
    UNTERMAECHTIG    die Positivkontrolle feuert nicht (2.88)

⚠️ **Und die Auflösung wird mitberichtet**, nicht nur die Kalibrierung:
wie viele unterscheidbare Potentialstufen entstehen, und wie sind sie
besetzt? **Ohne diese Zahl ist die Gate-gegen-Leiter-Frage nicht
entscheidbar.**

## ⚠️ Was diese Messung NICHT entscheidet

1. **Nicht die Hebelhöhe.** Auch bei perfekter Kalibrierung folgt daraus
   nur `f* = Potential/CRV` als Kelly-Anteil — die Frage nach Deckel,
   Fraktionierung und Stufung ist Konstruktionsarbeit, keine Messung.
2. **Nicht die Architektur.** Sie liefert die Auflösung, aus der Gate
   oder Leiter folgt — die Entscheidung bleibt beim Nutzer.
3. **Nicht die Positionsführung.** Spot ist ein Bestand, Hebel ein Trade
   mit Lebenszyklus — ein eigener Punkt.

## Suchpreis

**EINE Frage, EINE Zielgröße, EIN Split.** Keine Variation von CRV,
Horizont oder Gruppengrenzen — das wäre Parametersuche bei einem
erwarteten Effekt von 4,5 Prozentpunkten und würde zuverlässig
Scheinbefunde liefern (2.49).

## Betriebsrahmen

Nur lokale SQLite-Lesevorgänge, keine API-Abrufe.
