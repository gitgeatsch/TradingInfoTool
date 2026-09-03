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
| **N-16d** | eine **Ausstiegs**bewertung gibt es nicht | die Beiträge sind auf Einstiegen gemessen (F-183) |

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
| **N-17-0** | **Den Horizont kennen** — aus Stop und Volatilität die erwartete Zeit bis zur Barriere. Zum Zeitpunkt von Stufe 12 ist der Stop bekannt (urteil → aktion → geometrie → **entscheider**). ⚠️ Eine **Messung**, keine Formel: die 239 Trades tragen Stop, CRV und Dauer | **neu, Vorbedingung für alles** |
| **N-17a** | die Beiträge tragen ihren Horizont; Schwelle je Horizont (**R-R9**) | Messwerte liegen seit 31.08. vor |
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
