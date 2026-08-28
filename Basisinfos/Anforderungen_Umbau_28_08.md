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
