# Wo wir stehen — und warum jede Änderung an derselben Stelle endet

**Angelegt 28.08.2026.** Nutzerfrage nach zwei Tagen Umbau:

> *„Wir landen wieder bei derselben Problemstellung — jede Änderung scheitert
> an der zentralen Zielsetzung. Das war für mich auch der Grund, warum ich nach
> einem Gesamtplan fragte. Wir können nicht mehr an einer Stelle etwas ändern,
> ohne 20 andere nachzuziehen, oder es bricht etwas durch den laufenden Umbau,
> ohne die übergeordneten Probleme zu beheben. Wie machen wir nun weiter?"*

---

## 1. Die Diagnose — drei Schichten, und nur eine ist das Problem

Das System besteht aus drei Schichten. **Zwei funktionieren, eine nicht** — und
alle Arbeit der letzten Tage lag in den beiden funktionierenden.

| Schicht | Zustand |
|---|---|
| **1 Mechanik** — Kette, Rollen, Cooldown, Positionen, Mail | ✔ **funktioniert**, heute deutlich verbessert |
| **2 Bewertung** — Potential, Auslöser, Selektion | ⚠️ **ein** gemessener Baustein, und der gilt **nicht** für die Kern-Strategie |
| **3 Information** — woher der Vorteil kommen soll | ⚠️ **die eigentliche Lücke** |

⚠️ **Schicht 3 ist nicht durch Bauen zu schließen.** Der Grundbefund vom
10.08. lautet: *„Die Information steckt nicht in den Kursdaten."* Über 8.441
Fälle schlug kein Verfahren die Basisrate. Die Kombinationsmatrix vom 27.08.
zeigt, dass 14 Kombinationen geprüft sind und die Kandidatenliste aus der
Kursreihe **erschöpft** ist.

**Deshalb endet jede Änderung an derselben Stelle:** Wir verbessern Schicht 1,
und Schicht 3 bleibt, wo sie ist.

---

## 2. Der neue Befund, der es verschärft (28.08.)

**Für die Kern-Strategie ist das Potential nicht einmal rechenbar:**

```
akkumulation → kein Stop → kein CRV → keine Basisrate → kein H → Potential 0
```

`vorfilter.bewerte()` gibt `h=None` zurück mit dem Grund *„Stop oder Ziel
fehlt"*. Das ist kein Fehler, sondern die Definition: `handelsauftrag` sagt
*„bei Akkumulation gibt es keinen einzelnen Einstiegszeitpunkt und keinen
Stop"*.

⚠️ **Damit fehlt für BTC, ETH und SOL nicht der ZWEITE Baustein, sondern der
ERSTE.** Sie laufen ab jetzt alle 48 Stunden durch eine Kette, die für sie
kein Potential berechnen kann.

**Und der Rahmen kann es nicht ausdrücken:** `wahrscheinlichkeit.Beitrag` hat
ein Feld `klassen`, aber **keines für Strategie oder Instrument**. Ein
Beitrag, der nur für die Akkumulation gilt, lässt sich heute nicht
registrieren.

---

## 3. ⚠️ Warum „an einer Stelle ändern zieht 20 nach"

**Der Nutzer beschreibt ein reales Muster.** Allein an diesen zwei Tagen:

| Änderung | zog nach |
|---|---|
| `strategie` je Asset (A) | Paar-Matrix · GUI-Schalter · Klassenbegrenzung · Ausstiegsrechnung |
| Akkumulation ohne Trailing (C) | Strategie-Spalte lesen · Feld ins Ergebnis · Mail-Widerspruch |
| Position je Symbol (B) | Strategie im Eintrag · Mail-Sichtbarkeit · und die Ersparnis gab es gar nicht |
| Cooldown je Strategie (L4/L5) | zwei Suite-Prüfungen, die einen Wert statt einer Aussage festschrieben |

**Die Ursache ist nicht schlechte Bauweise, sondern Kopplung durch Historie:**
Werte wie 3,5 h stammen aus einer Welt mit zwei Läufen, Schalter heißen nach
Funktionen, die es nicht mehr gibt, und Prüfungen sichern Reparaturen ab,
deren Anlass entfallen ist.

✔ **Und die Suite hat jedes Mal gefangen, was gebrochen wäre** — 1.679
Prüfungen, zweimal rot, beide Male vor dem Betrieb. Das Muster ist teuer,
aber es ist **kontrolliert**.

---

## 4. Die vier Wege — und was jeder kostet

### Weg A — Mechanik fertigstellen, Bewertung ruhen lassen

**Was bleibt:** L2 (Kern-Hebel), L3 (Finanzierungskosten + Liquidation
speichern), Positionsführung anschließen.

| | |
|---|---|
| Aufwand | überschaubar, alles benannt |
| Ertrag | ⚠️ **kein Alpha** — das System verwaltet besser, findet aber nicht mehr |
| Risiko | gering, die Suite trägt |

### Weg B — Auf die Fremdquellen warten

| Quelle | verfügbar |
|---|---|
| Vorfilter-Schatten auswerten | **~19.09.2026** |
| Lebendigkeit / TVL | 18.09.2026 |
| **Terminmarkt** (OI, Funding, Divergenz) | ⚠️ **22.10.2026** (H20), 11.03.2027 (H120) |
| Entwickleraktivität | 09.11.2026 |

⚠️ **Der Terminmarkt ist der einzige gemessene Kandidat auf Information
außerhalb der Kursreihe** (ρ 0,034 / 0,195 / 0,250 zu ATR, Umsatz, Rendite).
**Bis dahin sind es acht Wochen.**

### Weg C — Neue Datenquelle erschließen: Nachrichten

**Die vierte Vorteilsquelle** (`Konzept_Einstiegsbewertung` §9.1) ist
**Information** — *„man weiß etwas, das im Preis noch nicht steht"*. Sie ist
die einzige der vier, für die **keine Quelle existiert**.

| | |
|---|---|
| Aufwand | ⚠️ **hoch** — Quelle, Anbindung, Kontingent, Messung |
| Ertrag | unbekannt, aber es ist die einzige unerprobte Kategorie |
| Risiko | ⚠️ kostenpflichtige Quellen, LLM-Verbrauch |

### Weg D — Das Ziel neu fassen

**Statt „schlägt den Zufall" → „ordnet besser als das Alphabet".**

Das Projekt hat sich selbst diesen Maßstab gesetzt und ist an ihm gescheitert.
⚠️ **Ein Trader in der Praxis rechnet keine Blockpermutation** — er braucht
eine Reihenfolge, keine Signifikanz.

| | |
|---|---|
| Aufwand | gering — es ist eine Entscheidung, kein Bau |
| Ertrag | das System wird benutzbar, ohne Alpha zu behaupten |
| Risiko | ⚠️ **die Selbsttäuschung, gegen die die ganze Methodik gebaut wurde** |

---

## 5. Was der Fachexperte empfiehlt

**A und B parallel, C vorbereiten, D bewusst NICHT.**

**Weg A jetzt**, weil er begrenzt ist und das System benutzbar macht: Ein
Werkzeug, das Positionen führt, Ausstiege überwacht und begründete Meldungen
in vertretbarer Zahl liefert, hat Wert — **auch ohne Alpha**. Das ist kein
Rückzug, sondern die ehrliche Beschreibung dessen, was heute möglich ist.

**Weg B läuft von selbst** — die Daten sammeln sich. Der 19.09. entscheidet
über den einzigen tragenden Baustein, der 22.10. über den einzigen echten
Fremdkandidaten.

**Weg C vorbereiten, nicht bauen:** Prüfen, welche Nachrichtenquelle kostenlos
und maschinell lesbar wäre. ⚠️ **Ohne diese Quelle bleibt die vierte
Vorteilsquelle für immer leer** — das ist absehbar, nicht überraschend.

⚠️ **Weg D nicht**, obwohl er verlockt. Die Methodik dieses Projekts ist teuer
bezahlt: vier von fünf Befunden starben allein am 27.08. an der Gegenprüfung.
**Den Maßstab zu senken, weil nichts ihn nimmt, wäre die eine Änderung, die
sich nicht zurücknehmen lässt.**

---

## 6. Und das offene Stück, das keinem Weg gehört

**Für die Akkumulation fehlt ein eigenes Erfolgsmaß.** `handelsauftrag` nennt
es — *„Durchschnittskurs und Endvermögen"* — aber es ist nicht gebaut, und es
gibt **keinen gemessenen Baustein dafür**:

| Kandidat | Stand |
|---|---|
| Lage zum 200-Schnitt (Buckel) | ⚠️ an der Marktphase gescheitert (27.08.) |
| „Boden gehalten" | nie gebaut |
| Fear & Greed als Kaufauslöser | ausgeschlossen (151 Tage am Stück) |
| Lage als **Ausschluss** (> +30 %) | ✔ **hält** — 3/3 Jahre, −11,2 Punkte |

⚠️ **Der letzte ist der einzige, der steht — und er ist eine Verbotsregel,
keine Kaufregel.** Für die Kern-Strategie heißt das heute: *kaufen, außer es
ist teuer.* Mehr trägt nicht.

Verwandt: `Roter_Faden_27_08.md` · `Anforderungen_Umbau_28_08.md` ·
`Kombinationsmatrix_27_08.md` · `Befund_Lage_27_08.md`


---

# NACHTRAG 28.08. abends — der Stand nach B+C, L2 und L3

## ⚠️⚠️ KORREKTUR AM 28.08. ABENDS — der Abschnitt unten war FALSCH

> **Nutzerhinweis, der es aufdeckte:** *„dachte du hast die Hebel-Erzeugung
> bereits bewertet und angepasst"* — und präzisiert: *„durch den Umbau des
> Schedulers auf eine einzige Funktion"*.
>
> **Er hat recht, und ich lag doppelt daneben.**
>
> ⚠️ **Falsch war:** *„der Hebel hat keinen Erzeuger mehr"*, *„die Ursache
> stand nirgends"*, *„Entscheidung: entweder zweiter Lauf oder stilllegen"*.
>
> ✔ **Richtig ist:** `INSTRUMENTE_JE_GRUPPE["krypto"] = ("spot",)` ist
> **S6b vom 22.08.**, ein bewusster Umbau mit eigenem Kapitel (134), eigener
> Gegenprüfung (56 Symbole, 0 mit mehr als einem Lauf) und vier umgedrehten
> Dauerprüfungen. **S6a–S6d sind alle gebaut** (Kapitel 133–137). Der Hebel
> hat sehr wohl einen Erzeuger: die **Rechnung**
> `hebel = verlustanteil / stop_rel`. Das ist genau die Entscheidung aus
> Kapitel 88: *„Hebel als Ergebnis statt als Kategorie"*.
>
> ⚠️ **Und die eigentliche Bewertung stand längst da** — Nutzervorgabe vom
> 22.08., wörtlich: *„sehe keine echten Hebel mehr, 1,1 Hebel ist kein Hebel
> und auch nicht bewertet werden als Hebel. Nachkaufen und ‚Eröffnen' ohne
> Hebel ist eigentlich ident ein und derselbe Spot-Kauf."*
>
> **Die Aufteilung spot/hebel ist bei Hebel 1,0 keine Trennung** — das steht
> seit dem 22.08. im Memory und ich habe es heute nicht gelesen, sondern neu
> gemessen und falsch gedeutet. Dieselbe Fehlerklasse wie am 27.08.
> („siebenmal als fehlend gemeldet, was gebaut war") — und die Modulkarte
> hilft dort nicht, weil der Befund in der **Doku** stand, nicht im Code.

---

## Was wirklich offen ist: DER RAUSCHBODEN ÜBERSTIMMT DAS MODELLURTEIL

**Kapitel 129 nannte die Wurzel schon am 22.08.:** S5 drehte zwei Regler
gleichzeitig — `stop_min_atr` von 0,75 auf **2,0** und `verlustanteil` von
15 % auf **6 %**. Beide senken den Hebel. Seither ist er ein **Nebenprodukt
der Stopregel, keine Strategieentscheidung**.

**Am NB-Stand 26.08. nachgemessen — es ist schlimmer geworden:**

| Zeitraum | Signale mit Widerlegungspreis | Stop **dort** |
|---|---|---|
| gesamt | 99,7 % | 15,4 % |
| ab 18.08. (S5) | 99,8 % | 9,5 % |
| **ab 22.08.** | 99,7 % | ⚠️ **6,0 %** |

⚠️ **In 94 % der Fälle gewinnt der Rauschboden.** Das Modell nennt in 99,7 %
einen Widerlegungspreis — und er landet in 6 % im Stop. Kapitel 88.1 hatte
genau das als Defekt benannt (*„in 10 von 12 Fällen die Klemme, nicht das
Urteil"*); nach S5 ist es dasselbe Bild, nur deutlicher.

**Die Kette, die daraus folgt:**

```
Rauschboden max(2,5 %, k x ATR), k = 2,0
  -> weiter Stop (Median 7,92 % statt 3,66 %)
     -> hebel = verlustanteil / stop_rel wird klein
        -> Median 1,10, ab 22.08. max 2,20, 34,6 % auf genau 1,0
           -> "spot" und "hebel" sind dasselbe Signal mit zwei Etiketten
```

✔ **Deshalb ist „Spot ist auch Hebel" falsch** — nicht weil die Formel falsch
rechnet, sondern weil der Hebel gar nicht mehr aus einer **Entscheidung**
kommt. Er ist der Rest einer Klemme, die das Modellurteil in 94 % der Fälle
überstimmt.

⚠️ **Die vorgelagerte Frage ist deshalb nicht „welcher Hebel?", sondern:
darf der Rauschboden das Modellurteil überstimmen?** Erst danach ist über k
oder den Verlustanteil zu entscheiden — und jede Drehung bricht die Messreihe
(Kapitel 90.2).

---

## ~~Der Befund, der alles andere überlagert: DER HEBEL IST STILLGELEGT~~ (widerrufen, siehe oben)

**Gemessen am NB-Export vom 26.08.** (der Desktop-Bestand ist alt — 118
Signale, jüngstes vom 21.07., keines aus der Rollen-Kette).

| Tabelle | Zeilen | jüngstes Signal | aus der Rollen-Kette |
|---|---|---|---|
| `hebel_signals` (alte Kette) | 1.998 | ⚠️ **10.08.2026** | 0 |
| `spot_signals` | 5.296 | 26.08.2026 | **2.313** |

**Seit dem Vollumstieg am 15.08. ist kein einziges Hebel-Signal mehr
entstanden.** Die Ursache ist strukturell und stand nirgends:

```
INSTRUMENTE_JE_GRUPPE = { "krypto": ("spot",), ... }
```

`laeufe()` liefert für Krypto genau **einen** Lauf: `spot`. Der alte Weg, der
Hebel erzeugte (`budget_allocator`, `hebel_screening`), wird von seinen Gates
übersprungen. **Beides zusammen heißt: der Hebel hat keinen Erzeuger mehr.**

### Und die Antwort auf *„echte Hebelsignale oder verkappte Spot?"*

**Verkappte Spot — belegt.** Die 2.313 Signale der Rollen-Kette tragen zu
49,5 % einen `hebel`-Wert, aber:

| Zeitraum | n | Median | max | über 3,0 |
|---|---|---|---|---|
| vor 18.08. | 365 | 3,70 | **10,00** | 67,1 % |
| ab 18.08. (S5) | 781 | **1,00** | 6,00 | 10,0 % |
| **ab 22.08.** | 153 | **1,10** | **2,20** | **0,0 %** |

✔ **S5 hat gewirkt** — der Rauschboden hat den Hebel ohne Deckel auf
höchstens 2,20 gebracht. Die Entscheidung vom 27.08., *keinen* festen Deckel
bei 3,0 zu setzen, ist damit an Betriebsdaten bestätigt.

⚠️ **Aber ein Hebel von 1,10 ist kein Hebel.** 34,6 % der jüngsten Signale
stehen auf genau 1,0 oder darunter. Was das System heute erzeugt, sind
Spot-Signale mit einem Dimensionierungsfaktor — **keine Hebelprodukte.**

**Das ist keine Messfrage mehr, sondern eine Entscheidung:** entweder Krypto
bekommt in `INSTRUMENTE_JE_GRUPPE` einen zweiten Lauf (`hebel`), oder das
Instrument `hebel` wird als stillgelegt dokumentiert wie die Tranchen.
⚠️ **Solange beides nicht entschieden ist, führt das System ein Instrument in
Doku, Prüfungen und Paar-Matrix, das nichts erzeugt.**

---

## Was seit dem 27.08. erledigt ist

| | | |
|---|---|---|
| **A** | `strategie` je Asset, auf Krypto begrenzt | ✔ |
| **B** | Positionsführung — eine Position je Symbol | ✔ |
| **C** | Akkumulation ohne Trailing | ✔ |
| **L1** | Potentialmaß mit 0,30 % | ✔ **entfällt** — 0,00 % ist nach N-5 richtig |
| **L2** | Kern-Assets ohne Hebel | ✔ **war schon durch A geschlossen** |
| **L3a** | Liquidation am Signal | ✔ gebaut, 4 Stellen, Migration greift |
| **L4/L5** | Cooldown je Strategie und Ergebnis | ✔ −56 % Meldungen |
| **B+C** | Akkumulations-Lagezeile, Kern ohne Satz | ✔ in der simulierten Mail nachgewiesen |
| — | Abkapselung des alten Wegs, 4 Riegel | ✔ |
| — | Akkumulations-Signalmaß gemessen | ✔ trägt — **nicht** bei BTC/ETH/SOL |

## Was offen ist — vor dem Primärthema

| # | | Warum es offen ist |
|---|---|---|
| **H-1** | ⚠️ **Hebel hat keinen Erzeuger** | **Entscheidung, keine Messung** — siehe oben |
| **L3b** | Finanzierungskosten | **kein Satz hinterlegt.** Einen zu erfinden hieße, eine Zahl zu bauen, die aussieht wie eine gemessene. Gehört wie die 1,50 % in die Mail, nicht ins Potential |
| **N-9** | `fakten_roh` erreicht keine Mail | elf Zusatzfakten + Lagebild von Rolle A, seit 13.08. |
| **NB** | Verifikation am Notebook | `git pull` + Neustart genügt (Migrationen laufen selbst) — **aber die Suite muss dort grün sein**, nicht nur hier |

## Und dann: das Primärthema

~~**L6 — nur ein tragender Beitrag im Potential.**~~ **Erledigt am 30./31.08.
— siehe den Nachtrag unten.** Es sind jetzt zwei, und der eine, der vorher
dastand, war der falsche.

---

# NACHTRAG 31.08. — DIE ARCHITEKTUR NACH DEM H-FEHLER

## Was passiert ist, in drei Sätzen

**Vorfilter H stand elf Tage mit +4,5 Punkten im Betrieb und war der einzige
tragende Beitrag.** Seine Zahl stammte aus einem **gepoolten** Vergleich über
die ganze Historie (+3,57 Punkte, am 31.08. frisch reproduziert); unter der
Klammer, die zur Frage von Stufe 11 passt — dem Vergleich gegen andere Werte
**desselben Kalendertags** — liegt er bei **−1,02 [−2,18 .. +0,14]**, also
bei null. **Der Befund war echt, beantwortete aber eine andere Frage:** *an
welchen Tagen tritt H auf* statt *welches Asset ist heute besser*.

## ⚠️ Die Regel, die das strukturell ausschließt

`Beitrag.klammer` ist seit dem 31.08. Pflichtfeld. **`zustand="traegt"`
verlangt `klammer="tag"`** — sonst wirft `__post_init__` beim Import.

| Klammer | Vergleich | beantwortet | darf `traegt` sein |
|---|---|---|---|
| **`tag`** | gegen andere Werte **desselben Kalendertags** | „welches Asset ist heute besser" | ✔ **nur diese** |
| `block` | gegen Anker desselben Zeitblocks (120 T.) | hält die Marktphase grob fest | ✖ |
| `gepoolt` | gegen alle Anker der Historie | „an welchen Tagen tritt es auf" | ✖ |

Der Unterschied ist nicht akademisch: bei H **4,6 Punkte** (+3,57 gepoolt
gegen −1,02 je Tag), bei „Boden unten" **0,20 R** (−0,2023 je Block gegen
−0,0019 je Tag).

## Die vier Bereiche — wer wo entscheidet

Die Kette hat vier Ebenen, und **jeder Beitrag gehört in genau eine**. Sie zu
vermischen ist der Fehler, aus dem H entstanden ist.

| # | Bereich | Frage | Wer entscheidet | Maßstab |
|---|---|---|---|---|
| **1** | **AUSWAHL** | *Welche Werte werden heute überhaupt beurteilt?* | `auswahl.py` (A1), k=2 nach Jahresentwicklung | Querschnitt über Symbole |
| **2** | **VORFILTER** | *Ist das überhaupt eine neue Frage?* | `anlass`, `wiederholung`, Cooldown | kostet keinen Modellaufruf |
| **3** | **BEWERTUNG** | *Wieviel ist bei DIESER Handlung zu holen?* | `potential.rechne()` ← **hier und nur hier wirken Beiträge** | ⚠️ **Klammer `tag`** |
| **4** | **NACHFILTER** | *Reicht das?* | Stufe 11 `potential.traegt()`, Budget, Positionsführung | Schwelle 0,010 R |

**Was in keinen dieser Bereiche gehört und trotzdem wirkt:** die Geometrie
(`entscheidungsrechnung`) setzt Stop, Ziel und Größe. **Dort tragen die
Marken weiter** — `_boeden()` legt den Stop jenseits der nächsten
Unterstützung, gemessen unschädlich (Kapitel 124: −0,0008 R) und
lehrbuchkonform. **H ist als Bewertungsbeitrag gefallen, nicht als
Stopregel.**

## Der Stand der Beiträge

| Beitrag | Zustand | Klammer | Wert |
|---|---|---|---|
| **Funding-Rang im Markt** | ✔ `traegt` | `tag` | +0,82 / +1,30 / +0,12 / −0,54 / −1,70 |
| **Turnover-Rang im Markt** | ✔ `traegt` | `tag` | +3,15 / +0,83 / +0,22 / −1,79 / −2,40 |
| Vorfilter H | `null` | `gepoolt` | — gefallen am 31.08. |
| Rangplatz in der Anlageklasse | `null` | — | misst schon Bereich 1 |
| Lebendigkeit | `noch_nicht` | — | ab 18.09. |
| Termine · Trichter | `nie` / `enthalten` | — | Anzeige / in der Basisrate |

**Schwelle 0,010 R, Durchlass 43,0 %** (mit H waren es 44,3 %).

## ⚠️ Das Betriebsrisiko, das dabei sichtbar wurde

Beide tragenden Beiträge kommen aus **externen Quellen** (Binance-Funding,
CoinGecko-Turnover), abgerufen einmal je Lauf. **Fällt der Abruf aus, liegt
jedes Potential bei 0,000 und Stufe 11 sperrt den ganzen Lauf** — derselbe
Stillstand wie vor 2e, nur durch einen Netzwerkfehler statt durch eine
Registrierung. Gefunden, weil die Prüfsuite in HTTP 429 lief.

**Gebaut am 31.08.:** Der Trockenlauf ruft gar nicht mehr ab (eine Suite, die
echte Quellen anfasst, ist kein Trockenlauf), und ein Totalausfall wird als
**Warnung** ausgewiesen statt still zu sperren — *„Das ist ein Datenausfall,
kein ruhiger Tag."* Durchgelassen wird trotzdem nicht: keine Empfehlung ohne
Grund.

## Wie weitere Beiträge dazukommen — und wo sie hingehören

**Von drei Kategorien hat genau eine je getragen:**

| Kategorie | geprüft | Ergebnis |
|---|---|---|
| Eigenschaft (Liquidität, Größe, Volatilität, Alter, Beta, Amihud, Momentum) | 7 | **keine trägt** |
| Lage (Marktbreite, Marktphase, 200-Schnitt) | 3 | invers oder Schatten |
| **Bewertung** (Funding, Turnover) | 2 | ✔ **beide tragen** |

> **Beide Treffer sind Bewertungsgrößen — „wie teuer ist dieser Wert gerade,
> verglichen mit den anderen".** Dort weitersuchen.

**Der nächste Kandidat liegt bereits gemessen im Bestand:** die **Tagewahl**
(`UNTER_SMA` / `RÜCKGANG`, 23.08.) schlägt ihren *quotengleichen* Zufall in
allen drei Anlageklassen und beiden Marktphasen.

⚠️ **Und genau hier droht der H-Fehler ein zweites Mal:** Die Tagewahl ist
über **Zweijahresfenster** gemessen, nicht je Kalendertag. Bevor sie ein
Beitrag wird, muss sie in die **Querschnittsform** gebracht werden — *„welches
Asset steht heute am weitesten unter seinem eigenen Schnitt"* — und unter der
Tagesklammer gemessen. Ohne diesen Schritt wäre sie H mit anderem Namen.

**Die Reihenfolge für jeden neuen Beitrag, ohne Ausnahme:**

| | |
|---|---|
| **1** | Form klären: Querschnitt oder Zeitreihe? Rohwert, Veränderung, Verhältnis oder Niveau? |
| **2** | **Je Kalendertag messen** — nicht gepoolt, nicht je Block |
| **3** | Als **Regel** prüfen, nicht als Merkmal (bei Funding: Faktor 5,5) |
| **4** | Survivorship · beide Historienhälften · Volatilitätsschichten |
| **5** | Beitragstabelle rechnen, **geschrumpft** (halbiert, weil in-sample) |
| **6** | Registrieren **mit `klammer="tag"`** → Neukalibrierung nach R-R9 |

## Was offen bleibt

| | |
|---|---|
| **R2** | Mailzeile zu H: **Fakt statt Wertung** — „nächste Unterstützung X ATR unter dem Kurs" statt „Stop gedeckt" |
| **R3** | Tagewahl als dritten Beitrag — nach den sechs Schritten oben |
| **Schwelle** | 0,080 misst besser (+0,1324 gegen +0,0470), ist aber in-sample und sperrt 83,5 %. Out-of-sample ungeprüft |
| **N-9** | `fakten_roh` erreicht keine Mail — unverändert offen |
| **NB** | Suite am Notebook grün |


---

# UMBAUPLAN 31.08. — DER ENTSCHEIDER, DER BEI ALLEN ASSETS WIRKT

**Nutzervorgabe, die alles bestimmt:** *„Krypto muss und braucht einen
Entscheider, der bei ALLEN Assets wirkt. Die Scharfschaltung darf erst
erfolgen, wenn alle Assets einen Beitrag haben."*

## Der Anlass — mein Fehler, benannt

**Vorfilter H galt für jeden Wert** — er wurde je Anker aus den Marken
gerechnet, Abdeckung 100 %. Seine Nachfolger kommen aus **Fremdquellen** und
haben zwangsläufig Lücken:

```
Funding-Rang    27 von 43 Krypto        63 %
Turnover-Rang    7 von 43                16 %
aktien · hedge · rohstoffe · themen_etf  0 %
──────────────────────────────────────────────
29 von 56 Werten ohne jeden Beitrag
```

**Ich habe die Wirksamkeit gemessen und die Reichweite nicht.** Solange
Stufe 11 nur zählte, war das folgenlos; mit G-6 entscheidet es über jeden
Wert. `pruefe_beitragsabdeckung.py` prüft das seither.

## 1. Die vier Ebenen — wo ein Beitrag wirken darf, und wo nicht

| # | Ebene | Frage | Modul | Beiträge? |
|---|---|---|---|---|
| **1** | **AUSWAHL** | Welche Werte werden heute beurteilt? | `auswahl.py` (A1), k=2 nach Jahresentwicklung | ✖ eigene Messung |
| **2** | **VORFILTER** | Ist das überhaupt eine neue Frage? | `anlass`, `wiederholung`, Cooldown | ✖ kosten keinen Modellaufruf |
| **3** | **BEWERTUNG** | Wieviel ist zu holen? | `potential.rechne()` | ✔ **hier und nur hier** |
| **4** | **NACHFILTER** | Reicht das? | Stufe 11, Budget, Positionsführung | ✖ liest nur Ebene 3 |

**Daneben, in keiner dieser Ebenen:** die Geometrie (`entscheidungsrechnung`)
setzt Stop, Ziel, Größe — **dort tragen die Marken weiter** (Strukturboden,
Kapitel 124 unschädlich).

⚠️ **Die Regel für jeden neuen Beitrag:** Ebene 3, `klammer="tag"`, und die
Abdeckung ist Teil der Aufnahmeprüfung — nicht erst der Wirkungsnachweis.

## 2. ⚠️ ABGRENZUNG: neutrale Empfehlung gegen Wirtschaftlichkeit

**Drei Verwendungen, und nur eine rechnet.** (Nutzervorgabe 30.08., hier
gegen den Code geprüft:)

| Verwendung | Gebühren | Wo | Stand |
|---|---|---|---|
| **BEWERTUNG** — „ist das ein guter Trade" | ⚠️ **KEINE** (0,0 %) | `potential.rechne()` ruft `gebuehr_je_seite=0.0` | ✔ korrekt |
| **MAIL** — „rechnet es sich für mich" | **als TEXT**: Referenz **0,30 %**, Betrieb **1,50 %** | `wahrscheinlichkeit.saetze()` zeigt beide Sätze | ✔ korrekt |
| **HEBEL** — Finanzierung läuft täglich mit | **rechnerisch** | `entscheidungsrechnung`, Hebelzeile | ✔ eigene Ebene |

**Eine neutrale Empfehlung ist die Aussage der Ebene 3: das Potential in R,
ohne jede Gebühr.** Sie beantwortet „wieviel ist bei dieser Handlung zu
holen", nicht „lohnt es sich nach Kosten". Die zweite Frage gehört in die
Mail — als Auskunft, nie als Filter.

✔ **Der alte Verstoß ist behoben:** `trefferbilanz.breakeven()` (rechnet mit
1,50 %) speiste bis U-1 die Entscheidung. Heute liefert `trefferbilanz` nur
noch Mailtext (`TB.satz`), entschieden wird mit `potential`.

## 3. ⚠️ DIE BRUCHSTELLEN — geprüft, nicht vermutet

| # | Bruchstelle | Stand |
|---|---|---|
| **B-a** | **Mail zeigt andere Zahlen als die Entscheidung.** `wahrscheinlichkeit.saetze()` bekommt `h=`, aber **kein `merkmale`** — die Mail nennt 33,3 % und „20,0 Punkte ZU WENIG", während Stufe 11 mit 37,0 % durchlässt | ⚠️ **offen, muss mit P1** |
| **B-b** | **Trockenlauf ohne Ränge** → mit G-6 nie ein Signal, alle Prüfungen wertlos | ✔ gelöst: `antworten["marktraenge"]`, ohne Vorgabewert |
| **B-c** | **`marktrang.saetze()` war nie verdrahtet** — die tragenden Beiträge standen in keiner Mail | ✔ gebaut, in der Kette nachgewiesen |
| **B-d** | **Rang über die falsche Grundgesamtheit** (Watchlist statt Messbasis) | ✔ gelöst: Rang über die Messbasis, unabhängig von der Assetzahl |
| **B-e** | **Beitragstabelle bei wachsender Messbasis** | ✔ gemessen: +10 Symbole → 287/293 Fünftel unverändert, max. 1 Stufe. ⚠️ Bei Schrumpfung um die Hälfte nur 70 % — braucht eine Dauerprüfung |
| **B-f** | **`bewertbar` gegen `traegt`** — ein Wert ohne Daten sah aus wie einer mit gemessen schwachen | ✔ gebaut (ungeprüft), kommt mit P3 in die Suite |
| **B-g** | **Positionsführung** ändert die Assetzahl je Lauf | ⚠️ zu prüfen in P3 — der Rang ist seit B-d davon unabhängig, die Prüfung fehlt |

## 4. Die Schritte

| | Schritt | Abdeckung danach | Prüfung/Simulation |
|---|---|---|---|
| **P1** | **Funding-Historie für 10 nachladen** (AKT, ASTER, BRETT, CAT, GRIFFAIN, HYPE, KAS, MON, MORPHO, PLUME) + **B-a schließen** | 27 → **37 von 43** | Abdeckung vorher/nachher · Bitgleichheit der Mail · Kettensimulation |
| **P2** | **R3: Tagewahl als dritter Beitrag** — aus der **Kursreihe**, also 100 % verfügbar. Querschnittsform, Tagesklammer, als Regel, Beitragstabelle geschrumpft | **43 von 43** | die sechs Pflichtschritte aus dem Nachtrag 31.08. |
| **P3** | **Dauerprüfungen**: Abdeckung ≥ 100 % je Klasse · Messbasis-Größe · `bewertbar` · Positionsführung (B-g) | hält es | Paket in `pruefe_pakete.py` |
| **P4** | **G-6 bleibt scharf** (kein Rückbau) — wirkt erst mit B1 | — | Vorschau + Kettensimulation |
| **P5** | **B1: Kette verdrahten** = in Produktion | — | ⚠️ erst wenn P1–P3 grün |
| **P6** | **Andere Klassen**: eigene Messbasis (Index-Universum), dieselbe Logik | — | ⚠️ Portfolio ≠ Messbasis |

⚠️ **Warum P2 der Kern ist:** Ein Beitrag aus einer **Fremdquelle** kann nie
volle Abdeckung garantieren — Binance und CoinGecko listen nicht jeden Wert.
**Nur ein Beitrag aus der eigenen Kursreihe erreicht 100 %.** Genau das war
H's Eigenschaft, und sie ist der Grund, warum sein Wegfall eine Lücke
hinterlässt, die Funding und Turnover nicht schließen können.

⚠️ **Kein Rückbau von G-6.** Es ist korrekt gebaut und wirkungslos, solange
B1 offen ist. Der Schaden entstünde erst beim Verdrahten — und davor stehen
P1 bis P3.

---

# ⚠️⚠️ NACHTRAG 31.08. ABENDS — DER TEILUMBAU UND SEIN VERFALLSDATUM

## Was die Kettensimulation gefunden hat

G-6 war gebaut, die Paketprüfung grün (1828 von 1828). Dann lief
`simuliere_kette.py` gegen die **echte Notebook-Produktion** und lieferte:

    5 Gruppen durchlaufen, 0 Signale, 2 Mails

**Null Signale über alle fünf Assetklassen.** Nicht wegen der Datenlage
einzelner Werte — eine Ebene darüber:

| Klasse | tragende Beiträge |
|---|---|
| krypto | **3** — Funding, Turnover, Schnittabstand |
| aktien | 0 |
| themen_etf | 0 |
| rohstoffe | 0 |
| hedge | 0 |

Alle drei Beiträge tragen `klassen=("krypto",)`. Für die anderen vier hat
nie jemand gemessen — und Stufe 11 sperrte sie deshalb **nach Datenlage
statt nach Qualität**. Das ist derselbe Fehlertyp wie bei H, nur eine
Ebene höher: die Wirksamkeit war geprüft, die **Reichweite** nicht.

⚠️ **Am übergeordneten Ziel gemessen ist es ein Regelverstoß.** „Für diese
Klasse haben wir nie gemessen" ist ein **Fakt** über unseren
Kenntnisstand — keine Aussage darüber, was kommt. Regel 4: *Ein Fakt ist
keine Begründung.* Wer daraus eine Sperre macht, hat die Frage nicht
beantwortet, sondern umformuliert.

## Die Reparatur: drei Zustände statt zwei

`potential.vermessen` (neu) fragt die **Registrierung**, nicht eine
handgeschriebene Liste — sonst veraltet sie still, sobald ein Beitrag
dazukommt.

| Zustand | Bedeutung | Stufe 11 |
|---|---|---|
| **nicht vermessen** | für diese Klasse gibt es keine Messung | **Notiz, nicht sperren** |
| **vermessen, kein Wert** | Mangel dieses Assets | **sperrt** |
| **vermessen, Wert da** | echte Bewertung | **entscheidet** |

Das Durchlassen ist **sichtbar**: `durchlauf.notiz()` schreibt eine eigene
Zeile in die Trichtertabelle (`⚠️ … [nicht beurteilt]`). Ein wortloses
Durchwinken sähe aus, als hätte der Entscheider zugestimmt.

    vorher:  5 Gruppen, 0 Signale
    nachher: 5 Gruppen, 8 Signale — Krypto entscheidet scharf,
             vier Klassen laufen mit sichtbarer Notiz weiter

## ⚠️ DAS IST EIN TEILUMBAU — und nur legitim mit Verfallsdatum

**Nutzervorgabe 31.08., wörtlich:** *„Wenn wir für die anderen
Assetklassen eine Bewertung erhalten, wäre Krypto nur ein Teilumbau — ja,
du hast recht, dies ist nur legitim, wenn wir diese sofort nachziehen,
aber dazu benötigen wir vorher eine tragende Basis und einen konkreten
Plan."*

Die Notiz ist die **Übergangsform**, nicht der Zielzustand. Sie hält die
Lücke offen und sichtbar, statt sie durch eine unbegründete Sperre zu
verdecken. Sie fällt weg, sobald die Klasse vermessen ist.

## Die Basis — erhoben, nicht vermutet (31.08.)

    data/messdaten.db      523 Reihen, ALLE assetklasse='krypto'
                           485 mit >= 500 Handelstagen
                           347 Symbole am letzten Kalendertag

    Portfolio              aktien 2 · themen_etf 5 · rohstoffe 4 · hedge 2

⚠️⚠️ **Für die anderen vier Klassen existiert keine Messbasis — und das
Portfolio kann sie nicht ersetzen.** Der Querschnittsrang braucht
mindestens 15 Symbole je Kalendertag (`MIND_JE_TAG`). Mit zwei Aktien
gibt es keinen Querschnitt, egal wie lang ihre Historie ist.

Genau dieselbe Trennung gilt bei Krypto schon: 523 Messreihen gegen 43
Watchlist-Werte. Die Messbasis ist **breiter als das Portfolio und muss
es sein** — sonst misst man seine eigene Auswahl.

## Der konkrete Plan — P6 bis P8

### P6 — Messbasis je Klasse aufbauen

Vorlage ist `lade_messreihen.py`: lädt breit, schreibt in
`data/messdaten.db`, bringt die Klassenzuordnung selbst mit, **fasst die
Produktionsdatenbank nicht an**. Für Nicht-Krypto ist die Quelle
`yfinance` — im Projekt bereits im Einsatz (`agent/aktien/screener.py`).

| | Klasse | Ziel | Machbarkeit |
|---|---|---|---|
| **P6a** | aktien | 300–500 Reihen aus einem breiten Index | ✔ Querschnitt trägt |
| **P6b** | themen_etf | 150–300 ETF-Reihen | ✔ Querschnitt trägt |
| **P6c** | rohstoffe | 20–40 Reihen (ETC/Futures) | ⚠️ grenzwertig |
| **P6d** | hedge | — | ⚠️⚠️ **kein Querschnitt möglich** |

### ⚠️ P6d ist ein Konstruktionsproblem, keine Fleißaufgabe

Es gibt keine „vielen Hedge-Werte" — Hedge ist eine **Rolle im Portfolio**,
keine Anlageklasse mit hunderten Vertretern. Der Querschnittsrang ist dort
nicht knapp, sondern **nicht definiert**.

Für P6c und P6d braucht es deshalb die **andere Form der Größe** (stehende
Regel 30.08.: *Rohwert · Veränderung · Verhältnis · Niveau — und:
Querschnitt oder Zeitreihe?*):

    Querschnitt   "wo steht dieser Wert HEUTE gegen alle anderen?"
                  -> braucht viele Werte
    Zeitreihe     "wo steht dieser Wert heute gegen SEINE EIGENE
                  Geschichte?" -> braucht eine lange Reihe

Der Schnittabstand lässt sich in **beiden** Formen bilden. Die
Zeitreihenform ist für P6c/P6d der einzige Weg — und sie ist **eigenständig
zu messen**, nicht aus der Querschnittsmessung abzuleiten.

### P7 — Der Schnittabstand je Klasse messen

⚠️ **Nur einer der drei Beiträge ist überhaupt übertragbar.**

| Beitrag | übertragbar? | warum |
|---|---|---|
| Schnittabstand | ✔ **ja** | braucht nur die eigene Kursreihe |
| Funding | ✗ nein | existiert nur bei Krypto-Perpetuals |
| Turnover | ✗ nein | Umlaufmenge ist Krypto-Mechanik; ein Aktien-Äquivalent (Volumen/Streubesitz) wäre eine **eigene** Messung |

Methodik unverändert `messe_schnittabstand_beitrag.py`: Tagesklammer,
Placebo-Band aus 40 Versätzen, beide Historienhälften, Survivorship,
**und die Wirkung als REGEL** (bei Funding war der Unterschied Faktor 5,5).

⚠️ **Kein Übertragen des Krypto-Ergebnisses.** Eine Klasse gilt erst als
vermessen, wenn ihre **eigene** Messung durchläuft — sonst steht in der
Registrierung eine Zahl, hinter der keine Messung dieser Klasse steht.
Das war der H-Fehler.

### P8 — Klassenspezifische Kandidaten

Erst nach P7 und nur, wenn P7 zu dünn ausfällt. Kandidaten stehen in der
Fakten-Entscheidungsmappe; jeder braucht die volle Prüfliste 2.80.

## Reihenfolge und Abbruchbedingung

    JETZT   Krypto in Produktion — die Basis trägt (43/43, 523 Messreihen)
    P6a/P6b Messbasis aktien + themen_etf     <- der Engpass, alles Weitere hängt daran
    P7      Schnittabstand dort messen        <- entscheidet, ob die Notiz fällt
    P6c/P6d Zeitreihenform für rohstoffe + hedge
    P8      nur falls P7 zu dünn

⚠️ **Abbruchbedingung, vorab festgelegt:** Fällt P7 für eine Klasse als
Nullbefund aus, wird dort **nicht** scharf geschaltet — die Notiz bleibt.
Ein Filter ohne tragende Messung ist genau das, was dieser Nachtrag
verhindert.

---

# ⚠️⚠️ NACHTRAG 01.09.2026 — der Hebel hat keine eigene Bewertung

**Kurz, weil die Ausarbeitung woanders steht.** Vollständig:
`Anforderungen_Umbau_28_08.md` Abschnitt 9 · `Fakten_Entscheidungsmappe.md`
F-163 · `Befund_Instrument_nach_S6b_28_08.md` Abschnitt 6.

**Der Befund:** Die Bewertung kennt drei Achsen — Klasse, Strategie,
Richtung. **Keine Instrument-Achse, keine Horizont-Achse.** `spot ×
einstieg` und `hebel × einstieg` liefern bei gleicher Lage exakt dieselbe
Zahl (+0,119100 R). Der Hebel ist heute eine **Ausführungsfrage**
(`hebel = verlustanteil / stop_rel`), keine Bewertungsfrage.

**Das war notiert** — Abschnitt 5.2 des Umbauplans führt es als bewussten
Kompromiss, unter der Bedingung *„vertretbar, wenn die Kostenrechnung dem
Etikett folgt (L3)"*. ⚠️ **Diese Bedingung war vier Tage lang nicht
erfüllt:** dem Hebel-Tier fehlte die Handelsgebühr auf das Nominal, ein
Hebeltrade erschien siebenmal billiger als Spot. Repariert 01.09.

**Zur Abgrenzung des Nachtrags 31.08. (P6–P8):** Der Teilumbau dort betrifft
die **Klassen**-Abdeckung der Beiträge. Der Hebel-Befund betrifft die
**Instrument**-Achse — eine andere Achse desselben Modells. ⚠️ **P6–P8
schließen die Hebel-Lücke nicht**, auch wenn beide „fehlende Abdeckung"
heißen.

**Nächster Schritt ist H-1**, nicht H-3: die Messung, die 5.2 selbst
verlangt hat (*„ein gehebelter Trade mit engem Stop trägt sich rechnerisch
nicht, bevor er begonnen hat — das wäre zu messen, bevor Aufwand in seine
Verwaltung fließt"*). Sie kann den ganzen Umbau der Instrument-Achse
überflüssig machen.


# ⚠️⚠️ NACHTRAG 07.09.2026 — `schnitt` und das Akkumulationsmaß sind DIESELBE GRÖSSE

**Quelle:** Befundkarte 2.155 bis 2.159 · `n61` bis `n67` ·
`REGISTER_Befunde.md`

## Der Fund, der zwei Themen zusammenlegt

`schnitt` rechnet `c / mean(c[-200:]) − 1`. `UNTER_SMA` (das
Akkumulationsmaß) prüft `kurs < sma200`. **Dieselbe Achse**, einmal
stetig, einmal als Schalter. Sie standen nie nebeneinander, weil der
28.08.-Befund nie ins Register kam und `schnitt` am 31.08. auf
kontaminierter Basis verworfen wurde (2.153).

> Damit sind „`schnitt` wieder einbauen" und „das Akkumulationsmaß als
> Beitrag aufsetzen" **eine** Aufgabe, nicht zwei.

## Was am 07.09. entschieden wurde

| | |
|---|---|
| **Durchlassquote** | **0,080 R festgeschrieben** = 16,4 % Durchlass ≈ 6 Empfehlungen/Woche. R-R9 verlangte sie als Nutzerentscheidung; sie stand seit dem 30.08. aus |
| **Sichtbarkeit** | Die Schwelle stand **nur als Konstante im Code**. Jetzt: `config.yaml → bewertung: potential_schwelle_r` steuert ohne Neustart, **jede Mail nennt Wert, Quelle und Alter**, fünf Suiteprüfungen halten es offen |
| **BTC/ETH/SOL** | **Nichts zu lösen.** Die −0,0251/−0,0308/−0,0291 aus 2.154 sind mit p 0,833 nicht von null zu trennen (3 Reihen, 8–12 Blöcke). Nach Tiefanteil geschichtet trägt `UNTER_SMA` in 4 von 5 Fünfteln, im **flachsten** — dort liegen BTC und ETH — am stärksten: +0,0481 (p 0,000, 101 Reihen) |

## ⚠️⚠️ Die ABDECKUNG ist das stärkste Argument für `schnitt`

| Beitrag | Symbole | Abdeckung | Quelle |
|---|---|---|---|
| funding | 293 | 55,9 % | Binance-Perpetuals (fremd) |
| turnover | 66 | 12,6 % | onchain (fremd) |
| oi_aenderung | 117 | 22,3 % | Terminmarkt (fremd) |
| **schnitt** | **524** | **100 %** | **die Kursreihe selbst** |

**Bewertbar: 60,5 % → 100 %.** 207 Symbole bekamen bisher gar keine
Bewertung. `schnitt` ist der einzige Beitrag ohne Fremdquelle und heilt
damit genau den Defekt, den die stehende Vorgabe benennt: *„sonst kodiert
die Bewertung: hat Daten."*

## Was `schnitt` sein KANN — und was nicht

| Form | Befund |
|---|---|
| **Sperre** (oberstes Fünftel) | ✔ **trägt** — +0,1759 R allein (N-59 reproduziert), **+0,0397 R zusätzlich nach funding+turnover** (2.159) |
| **5-Stufen-Regler** | ✖ **nicht herleitbar** — entzerrt +4,07 / +5,55 / **+9,49** / +1,71 / −4,65 Punkte: ein **Buckel**, Hochpunkt bei Fünftel 2. Die Vorabfestlegung verlangt Monotonie |
| **Schalter am SMA** | ○ **nicht unterscheidbar** vom Regler — die Bänder überlappen (2.158-form) |

⚠️ **Der Buckel ist zum dritten Mal da:** 27.08. (Verbilligung), 31.08.
(+1,27 +1,59 +0,24 −1,28 −1,82), 07.09. Er ist kein Messfehler, sondern
offenbar die Form der Sache.

## ⚠️ Zwei eigene Fehler, von den eigenen Kontrollen gefangen

1. **Konstruktionsverzerrung.** `median(Gruppe) − median(alle)` lieferte
   bei *gemischten* Rängen +0,10 bis +0,16 R statt null — der
   Stichprobenmedian kleiner Gruppen ist bei schiefer Verteilung nach oben
   verzerrt. Fünftel 0 hat 1,49 Anker je Tag. **Die Verzerrung war so groß
   wie die gesuchten Effekte.** Alle Zahlen sind seither entzerrt.
2. **Gleichstandsfalle (2.157-form, zurückgezogen).** Der Schalter-Arm
   lief über den Rang; bei 65,2 % Einsen liegt das oberste Rangfünftel
   ganz in der Einser-Gruppe, und `rang` bricht Gleichstände nach
   Array-Reihenfolge. **Nach Umsortieren eines Tages waren nur 15 von 62
   Symbolen dieselben.** Der Arm maß eine beliebige Teilmenge.

## Der Plan — Reihenfolge und Abbruchbedingung

| # | Schritt | Zustand |
|---|---|---|
| **S-1** | Durchlassquote 0,080 festschreiben | ✔ erledigt 07.09. |
| **S-2** | Schwelle sichtbar und steuerbar machen | ✔ erledigt 07.09. |
| **S-3** | Stufen für `schnitt` herleiten | ✖ **nicht herleitbar** — Buckel, 2.158 |
| **S-4** | Über die Kette simulieren | ✔ trägt zusätzlich, 2.159 |
| **S-7** | Stabilität über die Zeit klären | ⛔ **erledigt 07.09. — Abbruchbedingung EINGETRETEN** |
| **S-5** | `schnitt` als Sperre bauen | ⛔ **fällt weg** (siehe unten) |
| **S-6** | R-R9: Schwelle neu kalibrieren | ⛔ entfällt mit S-5 |

## ⛔⛔ S-7 BEANTWORTET — und `schnitt` fällt (07.09. abends)

⚠️ **N-60 kam nicht weiter, weil der Aufbau falsch war**, nicht weil Daten
fehlten. Es fragte *„trägt er in A?"* UND *„trägt er in B?"* — zwei
halbierte Tests. Die richtige Frage ist **eine**: *ist (A−B) von null zu
trennen?*, gestellt auf der ganzen Reihe.

| Schnitt | A | B | A−B | Band | |
|---|---|---|---|---|---|
| **Hälften** | +0,2742 | +0,0504 | **+0,2238** | [+0,0792 .. +0,3988] | ⚠️ **Unterschied**, Trennschärfe 0,02 R |
| funding | +0,0771 | +0,0195 | +0,0576 | [−0,0450 .. +0,1804] | stabil bis 0,05 R |
| zufall | −0,0006 | +0,0060 | −0,0066 | [−0,0258 .. +0,0154] | kein |

**Der Jahresverlauf zeigt die Quelle:**

    2019 +0,4532   2021 +0,3440   2023 -0,0498   2025 +0,1280
    2020 +0,5100   2022 +0,0187   2024 +0,1603   2026 -0,1158

**Und heute trägt er nicht mehr nachweisbar** — weder allein noch in der
Kette:

| | ganz | ab 2022 | ab 2023 | ab 2024 |
|---|---|---|---|---|
| **funding** (Kontrolle) | +0,0446 ✔ | +0,0157 ✔ | +0,0170 ✔ | +0,0182 ✔ |
| **schnitt** allein | +0,1623 ✔ | +0,0414 ✖ | +0,0478 ✖ | +0,0855 ✖ |
| **schnitt in der Kette** | +0,0397 ✔ | +0,0165 ✖ | +0,0216 ✖ | +0,0264 ✖ |

⚠️⚠️ **Es liegt NICHT an der Messdauer:** `funding` trägt in denselben
Fenstern mit einem *kleineren* Effekt. `schnitt`s Bänder sind rund
fünfmal breiter — der Effekt ist groß, aber zu unruhig.

⚠️ **Genauigkeit:** „heute nicht nachweisbar" ist nicht „trägt nicht".
Die Trennschärfe liegt allein bei 0,10 R, in der Kette bei 0,05 R; die
Werte liegen darunter. Es ist **unentschieden** — aber eine
Bauentscheidung braucht einen Nachweis, keine offene Frage.

⚠️ **Das Abdeckungsargument trägt allein nicht.** 60,5 % → 100 % bleibt
ein echter Mangel, aber ihn mit einer Größe zu schließen, deren heutige
Wirkung nicht nachweisbar ist, wäre genau der Defekt der stehenden
Vorgabe: *„sonst kodiert die Bewertung: hat Daten."*

### Was daraus als nächstes folgt

    N-1   Die Abdeckungsluecke bleibt OFFEN und braucht einen ANDEREN
          Beitrag aus der eigenen Kursreihe - `schnitt` scheidet aus.
          Kandidaten aus der Kursreihe, noch nie unter der Norm gemessen:
          Lebendigkeit, Positionierung im ATR-Kanal, Rueckgang vom Hoch.
    N-3   Die Schwelle 0,080 bleibt, wo sie ist - ohne neuen Beitrag
          gibt es keine R-R9-Folgepflicht.

## ⚠️⚠️ N-2 SOFORT NACHGEZOGEN — und `turnover` hat ein Problem

Einen Kandidaten an einer Hürde scheitern zu lassen, die die **laufenden**
Beiträge nie nehmen mussten, wäre zweierlei Maß gewesen. Also derselbe
Test auf den Bestand (`n70`):

| Beitrag | Stabilität (Hälften) | ganz | ab 2022 | ab 2024 |
|---|---|---|---|---|
| **oi_aenderung** | stabil bis 0,05 R | +0,0296 ✔ | +0,0296 ✔ | +0,0287 ✔ |
| **funding** | stabil bis 0,05 R | +0,0446 ✔ | +0,0157 ✔ | +0,0182 ✔ |
| **turnover** | stabil bis 0,10 R | +0,0498 ✖ | **−0,0112** | **−0,0307** |

⚠️ **`oi_aenderung` ist der solideste Beitrag im System** — über die Zeit
praktisch unverändert.

⚠️⚠️ **`turnover` dreht ab 2022 das Vorzeichen** und trägt dabei die
**größten Stufen des Systems** (+3,15 bis −2,40). R-R11 ist erfüllt: das
Werkzeug reproduziert den registrierten Anker exakt (frei +0,0616
[+0,0185 .. +0,1084] gegen +0,06163 [+0,01851 .. +0,10841]). **Aber auf
der selektierten Menge — wo Beiträge zu beurteilen sind — liegt er bei
+0,0865 [−0,0060 .. +0,1696]: das Band schließt die Null ein.** Der
registrierte Befund stammt von der *freien* Menge.

Das verstärkt **F-217** („funding hält, turnover nicht") aus einer ganz
anderen Richtung: dort die Kalibrierung, hier die Zeitachse.

    N-4   ⚠️ turnover ist der naechste Punkt, nicht die Abdeckungsluecke.
          Zu klaeren: (a) reproduziert das Vorzeichen ab 2022 auch mit
          `pruefe_auswahl` je Zeitraum? (b) wenn ja - Stufen auf null,
          wie bei H am 31.08., oder Tabelle neu herleiten?
          ⚠️ Beides loest R-R9 aus: die Schwelle 0,080 waere neu zu
          kalibrieren.

## ⚠️ Was S-5 konkret hieße — und warum es KEIN Beitrag an Stufe 12 ist

`oi_aenderung` ist der Präzedenzfall: er trägt **als Schalter** (H-4c) und
sitzt als Sperre an Stufe 11, nicht als Punktetabelle an Stufe 12. Für
`schnitt` gilt dasselbe:

    Stufe 11   Sperre: oberstes Fuenftel des Schnittabstands
               (Durchlassquote der Simulation: sperrt 21,6 % dessen,
                was funding + turnover uebrig lassen)
    Stufe 12   UNVERAENDERT - `schnitt_fuenftel` bleibt auf `zustand="null"`,
               weil die Stufen nicht monoton sind

⚠️ **Die Redundanz ist gemessen und schließt es nicht aus:** Spearman
+0,704 zum Auswahlmomentum im vollen Querschnitt, aber **+0,418 innerhalb
der Auswahl** — und nur die zweite Zahl zählt, weil Stufe 11/12 auf der
bereits ausgewählten Menge arbeiten.

## Akkumulation — was daraus für die Strategie folgt

Die Kette winkt bei `akkumulation` an Stufe 12 durch (`vermessen=False`,
2.152). Mit `schnitt` als Sperre gäbe es dort **zum ersten Mal eine
gemessene Grundlage** — und zwar für alle Werte, auch BTC/ETH/SOL.

⚠️ **Aber die Zielgröße ist zu trennen.** `bewegung_r` beantwortet „wie
läuft es nach dem Einstieg", die *Verbilligung* beantwortet „war es ein
guter Kauftag". 2.154 gilt auf der zweiten, 2.159 auf der ersten. **Wer
sie vermischt, hat zwei Befunde zu einem gemacht.**

## Die anderen Assetklassen — vorgesehen, nicht vergessen

`schnitt` braucht **keine Fremdquelle** und ist damit der einzige Beitrag,
der in Aktien, Themen-ETF, Rohstoffen und Absicherung ohne neue Datenquelle
messbar wäre. Die Messbasis dafür steht seit N-19 (03.09.).

    A-1   `schnitt` auf den vier Nicht-Krypto-Klassen messen -
          dieselbe Norm, dieselbe selektierte Menge
    A-2   erst danach entscheiden, ob G-6 dort scharf bleibt
          (2.152: vier von fuenf Klassen sind nach DATENLAGE gesperrt,
           nicht nach Bewertung - das ist eine Luecke, kein Urteil)

⚠️ **A-1 kommt nach S-7**, nicht davor: eine Größe, deren Zeitstabilität
in Krypto ungeklärt ist, in vier weitere Klassen zu tragen, vervierfacht
nur das offene Problem.


# ⚠️⚠️ NACHTRAG 07.09.2026 SPÄT — N-4 geklärt: `turnover` gerettet, zwei eigene Befunde gefallen

**Quelle:** Befundkarte 2.162 / 2.163 · `n71` / `n72` · Register

## Die Vorgabe, unter der das lief

Nutzervorgabe: *„bevor eine Bewertung fällt müssen wir alles unternehmen —
was ist der Grund und dass wir eine Lösung finden."* Ein Nullbefund ist
eine **Zerlegung**, kein Urteil.

## ⚠️⚠️ Der Grund war nie der Beitrag, sondern die MENGE

`turnover` deckt **66 von 524** Symbolen ab. Auf der 20-%-Menge sind das
**10,1 Anker je Tag** (früh 5,3) — und N-65 hat gemessen, dass die
Statistik dort fast nur Rauschen ist. `pruefe_auswahl` sagte das selbst:
*„KEIN BEFUND — untermächtig."*

Vier Erklärungen wurden vorab benannt und getrennt geprüft:

| | | |
|---|---|---|
| **A Gruppengröße** | ✔ **bestätigt** | 10,1 Anker/Tag bei 20 %, 25,5 bei 50 % |
| **B Datenquelle** | ✖ ausgeschieden | der `splycur`-Ausreißer ab 2023 ist XVG — große Umlaufmenge macht den Quotienten *klein*; die Kennzahl ist über alle Jahre stabil und geht als Rang ein |
| **C Marktwandel** | ○ nicht nötig | A erklärt es vollständig |
| **D nur oberstes Fünftel** | ✔ **beruhigend** | die Extreme sind stabil: F0 +0,2314 → +0,2745, F4 −0,1354 → −0,1316. Nur die Mitte dreht — und die Live-Regel sperrt F4 |

## Die Lösung — eine Regel, für alle gleich

> **Die schmalste Menge, die noch ≥ 12 Anker je Tag **und** ≥ 20 Blöcke
> liefert.**

Die 12 ist nicht erfunden: `sammle` verwirft Tage unter 12 Werten bereits
im Code. Gebaut als `messnorm_auswahl.menge_nach_datenlage()`, plus die
neue Menge `50%`; fünf Suiteprüfungen halten es offen.

| Beitrag | Menge | Wirkung ab 2022 | Stabilität |
|---|---|---|---|
| **turnover** | 50 % | **+0,0598** [+0,0066 .. +0,1139] | stabil bis 0,10 R |
| **funding** | 10 % | +0,0607 [+0,0079 .. +0,0863] | stabil bis 0,10 R |
| **oi_aenderung** | 20 % | +0,0446 [+0,0270 .. +0,0633] | stabil bis 0,05 R |
| zufall | 5 % | +0,0052 [−0,0191 .. +0,0235] | stabil |

**`turnover` ist nicht gefallen — er ist ab 2022 positiv.** Alle drei
Live-Beiträge tragen und sind zeitstabil.

## ⚠️⚠️ Zwei eigene Befunde von heute sind dabei gefallen

1. **„`turnover` dreht ab 2022 das Vorzeichen"** (2.161-turnover) — auf
   der falschen Menge gemessen.
2. **„`schnitt` ist nicht zeitstabil"** (2.160) — **zwei** Fehler: die
   20-%-Menge statt seiner eigenen (10 %), *und* eine Trennschärfe, die
   auf die **echte** Reihe gepflanzt war. Ist der Unterschied schon
   trennbar, bleibt er es bei jedem Versatz — „ab 0,02 R" hieß nur „der
   Effekt ist groß". Zentriert gemessen: **>0,20 R**.

⚠️ **Ein neuer Befund über `schnitt` bleibt aber:** sein
Hälftenunterschied **dreht mit der Menge** (+0,2238 bei 20 %, −0,0647 bei
10 %). Bei `funding` und `zufall` tut er das *nicht*. Eine Größe, deren
Vorzeichen am Messfenster hängt, ist keine verlässliche Grundlage.

## Der Stand von `schnitt` — dasselbe Ergebnis, schwächerer Grund

    Stufen        nicht monoton (2.158)              -> nicht nutzbar
    heute         +0,1152 [-0,0377 .. +0,2687]       -> nicht trennbar
    Stabilitaet   -0,0647, Trennschaerfe >0,20 R     -> unentschieden
    Massstab      Vorzeichen dreht mit der Menge     -> nicht verlaesslich

⚠️ **Nicht „widerlegt", sondern „nichts davon entscheidbar".** Drei offene
Fragen sind keine Bauentscheidung.

**R-R11 nach dem Umbau:** alle sieben Anker aus `messbasis_anker.json`
reproduzieren auf fünf Stellen — `50%` und `menge_nach_datenlage` haben
keine bestehende Messung verschoben.

### Was als nächstes ansteht

    N-5   ✔ ERLEDIGT 07.09. - siehe unten.
    N-6   Die Abdeckungsluecke (60,5 % bewertbar) bleibt offen und
          braucht einen Beitrag aus der eigenen Kursreihe. `schnitt`
          scheidet vorerst aus.
    N-7   Die Schwelle 0,080 bleibt - kein neuer Beitrag, keine
          R-R9-Folgepflicht.


# ✔✔ NACHTRAG 07.09.2026 — N-5 erledigt: die Durchsicht fällt beruhigend aus

**Quelle:** Befundkarte 2.164 · `n73_durchsicht_kandidaten.py` · 11 Minuten

## Die Frage

Alle früheren Beitragsmessungen liefen auf 20 % oder 5 %, ohne je zu
prüfen, ob die Datenlage das trägt. `turnover` war daran fast gescheitert.
**Wie viele andere stehen auf zu dünner Grundlage?**

## Die Antwort: zwei von zehn

| Kandidat | zulässige Mengen | Urteil |
|---|---|---|
| **turnover** | {50 %, frei} | **trägt in BEIDEN** ✔ |
| **schnitt** | {10 %, 20 %, 50 %, frei} | trägt **nur bei 20 %** ✖ |
| funding · oi_aenderung · vola · schnitt50 · amihud · rsi · momentum | — | **über alle Mengen gleich** ✔ |
| zufall | — | trägt auf keiner ✔ |

**`amihud` und `rsi` bleiben abgelehnt, `vola` bleibt offen, `funding` und
`oi_aenderung` bleiben tragend.** Die bisherigen Befunde stehen —
`turnover` war der Einzelfall, nicht die Regel.

## ✔✔ `turnover` ist voll rehabilitiert — nicht nur ab 2022

Auf der **ganzen** Historie und seiner Menge (50 %): **+0,0909
[+0,0433 .. +0,1454], Urteil TRÄGT** — stärker als der registrierte Wert
von der freien Menge (+0,0616).

## ⚠️⚠️ `schnitt` ist nicht robust — und das ist der vierte Grund

Zulässig sind für ihn vier Mengen. Er trägt nur auf einer.

    10 %   +0,1780 [+0,0274 .. +0,3361]   nicht trennbar
    20 %   +0,1759 [+0,0715 .. +0,2907]   TRAEGT
    frei   +0,0299 [-0,0018 .. +0,0668]   nicht trennbar

**Fast derselbe Punktschätzer, anderes Urteil** — allein wegen der
Bandbreite. Der N-59-Befund hängt an der Wahl „20 %".

## ⚠️ Ein Denkfehler in der eigenen Regel, von der Durchsicht aufgedeckt

`menge_nach_datenlage` gibt die **schmalste** zulässige Menge — und die
ist zugleich die **rauschendste**. Sie zum alleinigen Maßstab zu machen
bestraft jeden Kandidaten mit guter Abdeckung.

> **Richtig:** die Zulässigkeit sortiert aus, was zu dünn ist. Das
> **Urteil** muss über **alle** zulässigen Mengen halten. Ein Kandidat,
> der nur auf einer trägt, ist nicht robust — und das ist ein Befund über
> ihn, kein Grund, sich die passende Menge auszusuchen.

Gebaut als `messnorm_auswahl.zulaessige_mengen()`, mit Suiteprüfung.

### Was jetzt ansteht

    N-6   Die Abdeckungsluecke: 60,5 % der 524 Symbole sind bewertbar,
          weil alle drei tragenden Beitraege aus FREMDQUELLEN kommen.
          Gebraucht wird ein Beitrag aus der eigenen Kursreihe -
          `schnitt` scheidet aus (nicht robust). Nie unter der Norm
          gemessene Kandidaten aus der Kursreihe: Lebendigkeit,
          Positionierung im ATR-Kanal, Rueckgang vom Hoch.
    N-7   ✔ ERLEDIGT 07.09. - die Tabelle ist RICHTIG, siehe unten.
    N-8   Die vier Nicht-Krypto-Klassen: dort ist noch KEIN Beitrag
          gemessen, und G-6 sperrt sie nach Datenlage (2.152).


# ✔✔ NACHTRAG 07.09.2026 — N-7 erledigt: `turnover`s Stufen sind richtig

**Quelle:** Befundkarte 2.165 · `n74_turnover_stufen_nachgerechnet.py`

## Die Sorge

N-73 zeigte: auf seiner zulässigen Menge (50 %) trägt `turnover` mit
+0,0909 R — **48 % stärker** als der registrierte Wert von der freien
Menge. Die live laufende Tabelle trägt die **größten Stufen des Systems**.
Wenn sie um die Hälfte danebenliegt, liegt jede Bewertung mit ihr daneben.

## Das Ergebnis: sie liegt nicht daneben

| | F0 | F1 | F2 | F3 | F4 | Spanne |
|---|---|---|---|---|---|---|
| **registriert** | +3,15 | +0,83 | +0,22 | −1,79 | −2,40 | +5,55 |
| **Querschnitt, entzerrt** | **+3,13** | +0,76 | +0,22 | −1,73 | −2,38 | +5,51 |
| Auswahl 50 % | +4,04 | +0,96 | −0,04 | −2,06 | −2,90 | +6,94 |

**Abweichung höchstens 0,07 Punkte.** Alle Varianten monoton (die
Vorabbedingung), `zufall` bei maximal 0,38 Punkten.

**R-R11 vorab erfüllt:** `rechne_turnover_beitrag.py` reproduziert die
registrierte Tabelle exakt.

## ⚠️ Warum die Entzerrung hier nichts ändert — bei `schnitt` aber alles

Im **Querschnitt** sind die Fünftel **gleich groß** (9,0 bis 9,8 Anker je
Tag). Die Verzerrung aus N-65 trifft alle fünf gleich und hebt sich im
Bezug auf den Mittelwert der fünf auf. Bei `schnitt` auf der selektierten
Menge hatte Fünftel 0 dagegen **1,49** Anker und Fünftel 4 **29,35** —
dort verschiebt die Verzerrung die Stufen gegeneinander.

> **Die Gefahr liegt nicht in der Verzerrung selbst, sondern in ihrer
> UNGLEICHHEIT über die Gruppen.**

## Die Entscheidung: Tabelle NICHT ändern

Auf der Auswahl wäre sie 25 % steiler — dieselbe Richtung wie N-73. Aber:

    Ableitungsbasis   der volle Querschnitt ist GENAU die Basis, auf der
                      `marktrang` auch in der Produktion rangt
    Besetzung         auf der Auswahl nur 3,9 bis 5,2 Anker je Fuenftel
    Stellvertreter    die momentum250-Auswahl ist nicht die Menge, die in
                      der Kette wirklich bis zur Bewertung kommt
    Folgekosten       eine Aenderung loeste R-R9 aus (Neukalibrierung der
                      Schwelle 0,080) - ohne belegten Gewinn

⚠️ **Die registrierte Tabelle unterschätzt also eher — und unterschätzen
ist die sichere Richtung.** Revidierbar, sobald die tatsächliche Menge an
Stufe 12 rekonstruiert werden kann statt über einen Stellvertreter.

### Damit ist die Beitragslage für Krypto sauber

    funding        traegt · stabil bis 0,10 R · Tabelle steht
    turnover       traegt (+0,0909 auf 50 %) · stabil bis 0,10 R ·
                   Tabelle NACHGERECHNET und bestaetigt
    oi_aenderung   traegt · stabil bis 0,05 R · Schalter
    schnitt        nicht robust - vier unabhaengige Gruende
    amihud, rsi    abgelehnt, ueber alle Mengen bestaetigt
    vola           offen (nicht trennbar auf allen Mengen)

**Offen bleiben N-6 (Abdeckungslücke) und N-8 (Nicht-Krypto-Klassen).**


# ⛔ NACHTRAG 07.09.2026 — `amihud` an der Positionsgröße: auch dort nicht

**Quelle:** Befundkarte 2.167 · `n76_amihud_an_der_groesse.py`

## Die Hypothese

`amihud` trägt als Richtungsbeitrag nicht (N-73, N-75). Aber
Illiquidität sagt nichts über die Richtung — sie sagt, **wie teuer ein
Ausstieg wird**. Und davon lebt RM-1:

    max_position = risk_budget / (stop_abstand / kurs)

Diese Rechnung **setzt voraus, dass der Stop hält.**

⚠️ **Zwei Regeln vorab geklärt:** Regel 2 (Gebühren nicht in die
Bewertung) — hier wird nichts am Potential gerechnet, die Größe ist eine
getrennte Entscheidung. Regel 3 (beim Hebel kein Asset-Rang) — `amihud`
wird **absolut** gemessen, feste Niveaus statt Tagesränge.

## ⚠️⚠️ Befund 1: Der Stop-Durchschlag existiert in Krypto praktisch nicht

**71 Fälle von 728.920 Ankern (0,0097 %).** Die Kontrolle (gemischt)
liefert 15/10/20/14 gegen echte 0/14/18/28/11 — nicht unterscheidbar.

> **Der Grund generalisiert: Krypto handelt durchgehend.** Ein Kurstag,
> der *ganz* unter dem Stop liegt, verlangt eine Übernachtlücke — die es
> an einem 24/7-Markt nicht gibt.

### ✔✔ Daraus folgt etwas Nützliches, unabhängig von `amihud`

**RM-1s Grundannahme ist für Krypto belegt:** in 99,99 % der Anker war
der Stop zum Stoppreis handelbar. ⚠️ Untergrenze — ohne Eröffnungskurs
ist nur nachweisbar, was den *ganzen* Tag unter dem Stop lag.

## ⚠️⚠️ Befund 2: Die Mehrstreuung liegt auf der falschen Seite

| Band | unten (Median−P25) | oben (P75−Median) | IQA |
|---|---|---|---|
| 0 liquideste | **1,909** | **1,342** | 3,251 |
| 4 illiquideste | **1,727** | **2,054** | 3,780 |

Der Interquartilsabstand steigt deutlich (Kontrollspanne nur 0,027) —
**aber vollständig nach oben.** Auf der **Verlustseite** sind illiquide
Werte *enger*. Kleiner zu dimensionieren wäre unbegründet.

⚠️ **Der Geometrie-Einwand wurde geprüft und ausgeräumt:** der 5-%-Boden
bindet bei Band 0 in 38,2 % und bei Band 4 in 38,5 % der Anker
(ATR/Kurs 0,0790 gegen 0,0752) — praktisch gleich.

## ⚠️ Zwei eigene Ausgabefehler, zwischen Ergebnis und Deutung gefangen

1. „Durchschlag 0,0 %" war **gerundet**, nicht null — die Mittelwerte
   standen auf 11 Fällen, ohne dass die Zahl dastand.
2. Die **Standardabweichung** als Streuungsmaß lag bei 250, getragen von
   0,06 % der Anker (ein Coin, der sich in 20 Tagen verzwanzigfacht,
   ergibt bei 5 % Stopweite 400 R).

Beides ersetzt durch absolute Zahlen und den Interquartilsabstand.

### Damit ist `amihud` an beiden Achsen erledigt

    Richtung        traegt nicht - alle Mengen (N-73), beide Achsen (N-75)
    Positionsgroesse traegt nicht - kein Rutschen, Mehrstreuung nach OBEN

**Offen bleiben N-6 (Abdeckungslücke) und N-8 (Nicht-Krypto-Klassen).**


# ⛔ NACHTRAG 07.09.2026 — N-6 ist falsch gestellt und wird gestrichen

**Quelle:** Befundkarte 2.168 · `n77_ist_die_abdeckung_repraesentativ.py`

## Die Prämisse hielt der Prüfung nicht stand

N-6 hieß: *„60,5 % der Symbole sind bewertbar — gebraucht wird ein Beitrag
aus der eigenen Kursreihe."* Gemessen:

| | ohne Beitrag |
|---|---|
| **Betrieb** (Watchlist, k=2) | **4,2 %** der gewählten Anker — FLOKI, XNO |
| Messbasis (524, 20 %) | 32,4 % |

⚠️ **Nutzervorgabe vom 07.09., wörtlich:** bei Meme- und Smallcap-Werten
ist eine fehlende Bewertung *„als unkritisch zu bewerten"*. FLOKI ist ein
Meme-Coin, XNO ein Smallcap. **Kein Betriebsproblem.**

## Als Messfrage: nicht entschieden auf der Auflösung, die zählt

`schnitt` und `vola` (beide 100 % Abdeckung) auf beiden Gruppen:

    schnitt   MIT -0,0774 gegen OHNE   Band schliesst null ein
    vola      MIT -0,0885 gegen OHNE   Band schliesst null ein
    zufall            -0,0056          Band schliesst null ein  ✔

⚠️ **Aber die Trennschärfe liegt bei 0,10 R** — größer als die Effekte, um
die es geht (0,02–0,09 R). Ein Unterschied dieser Größe könnte sich
verstecken. **Nicht „repräsentativ", sondern „nicht entscheidbar".**

⚠️⚠️ **Die Kontrolle fing dabei einen eigenen Fehler:** der erste Anlauf
differenzierte die **rohen** Tagesreihen. Bei 35 gegen 20 Ankern je Tag
ist die N-65-Verzerrung *ungleich* — `zufall` zeigte prompt einen
„Unterschied" von −0,0212 [−0,0417 .. −0,0038]. Mit je Gruppe entzerrten
Reihen verschwindet er.

## ⚠️⚠️ Warum ein neuer Kursreihen-Beitrag nicht die Antwort ist

Die **Kombinationsmatrix vom 27.08.** hat es bereits festgehalten:

> *„M2–M12 und M15–M17 sind alle aus Kurs, Volumen oder Modellantwort
> abgeleitet. M13 und M14 sind die einzigen echten Fremdquellen."*
> … *„Die Information steckt nicht in den Kursdaten. Wer nur Kursreihen
> kombiniert, kombiniert Ableitungen derselben Quelle."*

Die heutige Durchsicht bestätigt es: `schnitt`, `vola`, `rsi`, `amihud`,
`momentum`, `schnitt50` — alle gemessen, keiner trägt robust.

## Die beiden echten Fremdquellen — geprüft

| | |
|---|---|
| **M13 Terminmarkt** | ✔ realisiert (122 Symbole, 1.734 Tage bis 02.09.2026) — ⚠️ deckt aber nur 122 von 524 ab und **schließt die Lücke nicht** |
| **M14 Entwickleraktivität** | Messwerkzeug da, **in keiner Datenbank eine Tabelle** |

**Es gibt derzeit keine verfügbare Quelle, die die Lücke schließen würde.**

### Was stattdessen offen ist — ohne neue Datenquelle

    N-9   ⛔ ERLEDIGT 07.09. - KEINER traegt. Siehe unten.
    N-8   Die vier Nicht-Krypto-Klassen - dort ist noch KEIN Beitrag
          gemessen, und G-6 sperrt sie nach Datenlage (2.152).
    N-10  ⚠️ NUTZERENTSCHEIDUNG: eine neue Fremdquelle mit BREITER
          Abdeckung anbinden waere der einzige Weg, die Luecke
          wirklich zu schliessen. Das ist eine Aufwands- und
          Kostenfrage, keine Messfrage.


# ⛔⛔ NACHTRAG 07.09.2026 — N-9 erledigt: mit den vorhandenen Daten gibt es keinen vierten Beitrag

**Quelle:** Befundkarte 2.169 · `n78_terminmarkt_kanaele.py`

## Das Ergebnis

| Kanal | zulässige Mengen | trägt auf |
|---|---|---|
| `oi_je_umsatz` | 20 %, 50 %, frei | **0 von 3** |
| `long_bias` | 20 %, 50 %, frei | **0 von 3** |
| `top_bias` | 50 %, frei | **0 von 2** |
| `taker_bias` | 20 %, 50 %, frei | **0 von 3** |
| *`oi_aenderung`* (Referenz) | 20 %, 50 %, frei | **3 von 3** |

`oi_aenderung`s Band schließt in **jeder** Menge die Null aus (+0,0469 /
+0,0243 / +0,0145) — die vier Kandidaten in keiner. `zufall` trägt
nirgends.

## ⚠️⚠️ Warum die N-17b-Befunde sich nicht übertragen

Dort trugen `oi_je_umsatz`, `long_bias` und `top_bias` — **aber gegen
FRONTLOADING**, eine andere Zielgröße. Genau diese Verwechslung hat F-207
schon einmal erzeugt.

> **Ein Kandidat, der die Frontloading-Quote verschiebt, verbessert
> deshalb nicht das ERGEBNIS.**

## Zwei saubere Nebenbefunde

    oi_je_umsatz gegen turnover   -0,490   beide umsatznormiert -
                                           echte Ueberschneidung
    long_bias gegen top_bias      +0,950   N-17b mass +0,955 - REPRODUZIERT

## ⚠️⚠️ Der Gesamtbefund

> **Mit den vorhandenen Daten gibt es keinen vierten Beitrag.**

    Kursreihe      erschoepft (2.168 - 15 Merkmale, keiner robust)
    Terminmarkt    erschoepft (nur `oi_aenderung` traegt)
    onchain        liefert `turnover`
    Binance        liefert `funding`

Ein weiterer Beitrag verlangt eine **neue Datenquelle**. Das ist eine
Entscheidung über Aufwand und Kosten — keine Messfrage.

### Was offen bleibt

    N-8    Die vier Nicht-Krypto-Klassen: dort ist noch KEIN Beitrag
           gemessen, und G-6 sperrt sie nach Datenlage (2.152). Das
           ist die letzte Messfrage mit vorhandenen Daten.
    N-10   ⚠️ NUTZERENTSCHEIDUNG: neue Fremdquelle anbinden.
           Genannte Kandidaten: Entwickleraktivitaet (Werkzeug da,
           keine Daten), Sentiment/Social, CoinGecko-Metadaten.


# ⚠️⚠️ NACHTRAG 08.09.2026 — N-8 KORRIGIERT: der Aktien-Nullbefund war Untermacht

**Quelle:** Befundkarte 2.172 · Nutzerhinweis: *„ich finde es seltsam, dass
wir keinen einzigen tragenden Betrag erhalten."*

## Der Fehler

`bewegung_r` teilt durch die Stopweite `max(5 % Kurs, 0,75 ATR)`. Diese
Geometrie ist **für Krypto gebaut** — und wirkt in den anderen Klassen
völlig anders:

| Klasse | ATR/Kurs | 5-%-Boden bindet | Stopweite in ATR |
|---|---|---|---|
| krypto | 8,59 % | 29,1 % | **0,75** ← wie vorgesehen |
| aktien | 2,18 % | **97,1 %** | **2,29** |
| themen_etf | 1,13 % | **99,2 %** | **4,43** |
| rohstoffe | 2,00 % | 97,4 % | **2,50** |

**Der Stop liegt bei Nicht-Krypto drei- bis sechsmal weiter von der
eigenen Schwankung entfernt.** Damit sind die R-Werte dort gestaucht.

## Die Folge, in Zahlen

Streuung von `bewegung_r` (Interquartilsabstand): krypto **3,710** ·
aktien **1,929** · rohstoffe **1,715** · themen_etf **0,905**.

In **eigenen Streuungseinheiten** liegen die Effekte fast gleichauf:

| Klasse | Kandidat | in R | in Streuungseinheiten |
|---|---|---|---|
| krypto | schnitt 20 % | +0,1759 | 0,047 |
| **aktien** | **schnitt 20 %** | +0,0725 | **0,038** |
| **aktien** | **vola 20 %** | +0,0714 | **0,037** |
| **rohstoffe** | **schnitt 50 %** | +0,1192 | **0,070** ← größer als Krypto |
| themen_etf | vola 10 % | +0,2303 | **0,254** |

## ⛔ Was daraus folgt

**Der Aktien-Nullbefund ist zurückgezogen.** Ein Effekt der Krypto-Größe
hätte dort **+0,0915 R** ergeben — die Trennschärfe lag bei 0,05–0,10 R,
also genau an der Grenze. Gemessen wurden +0,0725. **Die Messung konnte
dort nichts zeigen.**

Und damit fällt auch die Aussage *„der Grundbefund vom 10.08. ist nicht
krypto-spezifisch"* — sie stand auf dieser Messung.

⚠️ **Der ETF-Befund wird dadurch größer, nicht kleiner:** `vola` liegt
bei **0,254** Streuungseinheiten (bei 5 %: 0,322) — das **Fünffache** des
stärksten Krypto-Effekts. Der Vorbehalt bleibt (1 von 5 Mengen, effektiv
1,9 unabhängige Reihen), aber die Größe verdient eine eigene Messung.

## Die Lehre

> **Eine Zielgröße, die durch eine GEOMETRIE normiert, ist nur dort
> vergleichbar, wo die Geometrie gleich wirkt.**

Wer Klassen vergleicht, muss die Effekte in **eigenen
Streuungseinheiten** ausdrücken — oder die Geometrie je Klasse
kalibrieren.

### Was daraus als Arbeit folgt

    N-11   ⚠️ N-8 WIEDERHOLEN mit klassengerechter Geometrie. Zwei Wege:
           (a) den 5-%-Boden je Klasse kalibrieren, so dass der Stop
               ueberall bei rund 0,75 ATR liegt, oder
           (b) die Effekte grundsaetzlich in Streuungseinheiten messen.
           ⚠️ (a) aendert die PRODUKTION, (b) nur die MESSUNG - das ist
           eine Entscheidung, keine Messfrage.
    N-12   Der ETF-Befund `vola` eigens messen - groesster Effekt des
           Projekts, aber auf effektiv 1,9 unabhaengigen Reihen.


# 📋 NACHTRAG 08.09.2026 — DATENLAGE: die Meldelücke, die Auffrischung, und was offen bleibt

**Nutzervorgabe 08.09.:** *„immer wieder die Schritte mitdokumentieren und
im Plan niederschreiben."* Dieser Abschnitt ist das Protokoll.

## Der Anlass — ein Beispiel, das keines war

*„Neues Asset wird in der Watchlist aufgenommen oder neuer Coin-Bestand
Spot — es müssen die Daten zur Bewertung für das Asset vorhanden sein."*

Beim Nachsehen war es der **Ist-Zustand**: acht gehaltene
Krypto-Positionen ohne Messreihe, drei Kernwerte betroffen (CANTON,
MORPHO, HYPE), und **nichts hat es gemeldet**.

## Was gebaut wurde

| | |
|---|---|
| `pruefe_neuaufnahme.py` | prüft die drei Lebenszyklus-Fälle (**neu** · **fällt weg** · **ändert sich**) plus die Beitragslage |
| Suitepaket `Neuaufnahme` | sechs Prüfungen, davon vier rot — **und das ist richtig** |
| Ausnahmeliste | mit **Grund** je Eintrag (EURCV: Cash-Äquivalent) |

⚠️ **Zwei Fehler in der eigenen Prüfung, beide beim Gegenprüfen gefunden:**
1. Die Frische wurde über das **Maximum** je Klasse gemessen — sechs frische
   Reihen ließen 518 alte frisch aussehen. Jetzt Median + Anteil.
2. **Eingestellte** Reihen wurden als veraltet gezählt. Sie sind
   *vollständig*, nicht alt — jetzt getrennt ausgewiesen.

## Die Datenlage, geklärt

**Es war kein Übernahmeversäumnis, sondern eine Quellenfrage.** Die
Messbasis lädt Binance-USDT (`quelle='binance_mess'`, einheitlich).
Binance führt die fehlenden Symbole überwiegend nicht.

| Gruppe | Symbole | Weg |
|---|---|---|
| **aufnehmbar (10)** | AIOZ · AKT · BRETT · CAT · GRIFFAIN · **HYPE** · KAS · MORPHO · PLUME · SUPRA | Übernahme **mit Quellenkennzeichnung** |
| **Datenlage-Grenze (2)** | ASTER (318 T) · MON (269 T) | Coins existieren erst seit 10/2025 bzw. 11/2025 |
| **nicht lösbar (1)** | **CANTON** | 252 Tagespreise **ohne Hoch/Tief** — kein ATR, keine Stopgeometrie. ⚠️ **Kernwert im Bestand** |
| nicht relevant | VSN | Nutzerentscheidung 08.09. |

⚠️ **HYPE war eine eigene Korrektur:** ich hatte die Quellen einzeln geprüft
(bybit 238, gemessen 167) und „zu kurz" geurteilt. **Kombiniert sind es 405
lückenlose Tage.**

## Die Auffrischung — Schritt für Schritt protokolliert

    1  Sicherung   data/messdaten_vor_auffrischung_08_09.db
                   SHA-256 bitgleich geprueft, 110 GB frei
    2  Anker       `pruefe_messbasis_wechsel.py --vorher`
                   sieben Anker, reproduzieren die registrierten Werte
                   exakt (+0,17593 · +0,06163 · +0,02458)
    3  Trockenlauf 347 von 487 brauchbar, 140 abgelehnt (ALLE "zu kurz")
    4  Schreiben   `lade_messreihen.py --schreiben`
                   347 Reihen, 539.568 Kerzen, 259 s
    5  Ergebnis    347 Reihen stehen jetzt auf 2026-09-08 (vorher 21.08.)
    6  Gegenprobe  `pruefe_messbasis_wechsel.py --nachher`

⚠️ **Der Lader meldet die Kollisionen selbst:** *„C: bleibt aktien, wollte
krypto"* — fünf Symbole, Kerzen getrennt gespeichert, Klasse nicht
umgestellt.

## ⚠️⚠️ Was dabei offen blieb — F-198 ist nur halb bereinigt

Sieben Symbole (**BOND · C · DASH · DIA · MDT · STX · T**) tragen in
`price_history_ohlc` eine **andere Klasse** als in `messreihen`. Alle
haben Kurse in **zwei** Klassen — aber `messreihen.symbol` ist PRIMARY
KEY und kann nur *einer* zuordnen.

| | |
|---|---|
| ✔ | **Die Messungen sind nicht betroffen** — `_reihen_roh` nutzt die Spalte, nicht `messreihen` |
| ⚠️ | **`klassen_aus_db()` liefert dort die falsche Klasse** — über **zehn** Werkzeuge importieren sie |

**Nicht repariert, mit Grund:** der saubere Fix verlangt eine
Mehrfachzuordnung — eine Strukturänderung an `messreihen`, die zehn
Werkzeuge berührt. Als Suiteprüfung gemeldet.

### Offene Punkte aus diesem Abschnitt

    D-1   Die zehn aufnehmbaren Symbole uebernehmen - MIT
          Quellenkennzeichnung, plus eine Pruefung, die meldet, wenn
          eine Messung gemischte Quellen benutzt.
    D-2   ⚠️ NUTZERENTSCHEIDUNG: CANTON ist ein Kernwert im Bestand und
          nicht bewertbar (keine Tagesspanne). Entweder eine OHLC-Quelle
          beschaffen oder die Rolle anpassen.
    D-3   F-198 zu Ende bringen: `messreihen` muss ein Symbol MEHREREN
          Klassen zuordnen koennen, oder `klassen_aus_db()` liest aus
          `price_history_ohlc`.
    D-4   Die Nicht-Krypto-Klassen sind mit 5 Tagen aktuell - fuer sie
          gibt es noch keinen eigenen Auffrischungstakt.

## Nachtrag 08.09. abends — D-1 erledigt, zwei neue Punkte (NIEDRIG)

**D-1 ✔ erledigt:** zehn Reihen übernommen (6.768 Zeilen), Messbasis
526 → 536, gehaltene Lücken **acht → drei**. Quellenreinheit sichtbar
(`uebernommen_bybit` / `_gemessen` / `_binance`), Status `uebernommen`
statt `handelnd`, weil `lade_messreihen.py` sie **nie** auffrischen kann.
Ankervergleich: **alle fünf inhaltlichen Anker unverändert**, größte
Verschiebung +0,00375 R.

### ⚠️ CANTON — korrigiert

Meine Aussage *„gar keine Kursreihe"* war **zu eng**. CANTON hat **252
CoinGecko-Tagespreise**; was fehlt, ist **OHLC**. Und das
Symbolproblem (CoinGecko führt es als **`CC`**) ist seit 31.08. über die
`coingecko_id` gelöst.

| | |
|---|---|
| gleitender Schnitt | ✔ möglich |
| ATR · Stopgeometrie · `vola` | ✖ ohne Tagesspanne nicht |
| funding · turnover · oi | ✖ nirgends gelistet |

    D-5  ⚠️ NIEDRIG: acht der zehn Uebernommenen haben einen
         200-Tage-Schnitt, aber KEINEN Abstand - `schnitt_werte()`
         braucht einen aktuellen Binance-Ticker, und dort sind sie
         nicht. HEUTE FOLGENLOS (`schnitt` ist nicht registriert),
         aber bei einer Aktivierung waeren sie ohne Rang.

    D-6  ⚠️ NIEDRIG *fuer die Desktop-Kopie*: `price_history`
         (CoinGecko-Tagespreise) steht dort seit dem 19.07. still -
         BTC, KAS und CANTON alle 51 Tage alt. Deshalb faellt CANTON
         an `SCHNITT_FRISCHE_TAGE = 10`.
         ⚠️⚠️ ABER: laeuft `refresh_prices_job` auch auf dem NOTEBOOK
         nicht mehr, fehlen dort seit 51 Tagen die Tagespreise fuer
         ALLE Werte ohne Boersenlisting. Das waere NICHT niedrig.
         -> Das ist eine RUECKFRAGE an den Nutzer, keine Messung.

---

## ⚠️⚠️⚠️ NACHTRAG 08.09.2026 — DIE URSACHE DES HIN UND HER IST GEFUNDEN

Nutzervorgabe 08.09.: *„beachte dass wir schon mehrfach Beiträge
unterschiedlich als gefallen und wieder aufgenommen haben."*

Er hatte recht, und die Ursache liegt **nicht bei den Kandidaten**,
sondern in der Messanlage selbst.

### Der Fund

`messnorm.Befund.traegt` lautet:

```python
return self.unten > max(0.0, self.null_oben)
```

und `null_oben` entsteht so (`messnorm_auswahl.py`):

```python
for z in range(ZIEHUNGEN):          # ZIEHUNGEN = 5
    ...
null_oben = float(np.max(nullo))    # das MAXIMUM ueber fuenf Ziehungen
```

> **Ein Maximum über fünf Ziehungen ist kein Schätzer.** Es wächst mit
> jeder weiteren Ziehung und hat keinen Grenzwert. Damit hängt die
> Strenge jedes Urteils an einer Zahl, die niemand begründen kann.

### Der Beleg — zweifach geführt

**Auf Kunstdaten**, wo die Wahrheit bekannt ist (400 Welten, Ziehungen
aus N(0; 0,02), echtes 90. Perzentil = 0,0256):

| n | max Mittel | max **Streuung** | p90 Mittel | p90 **Streuung** |
|---|---|---|---|---|
| 5 | 0,0226 | 0,0140 | 0,0172 | 0,0118 |
| 20 | 0,0374 | 0,0108 | 0,0227 | 0,0066 |
| 80 | 0,0489 | **0,0095** | 0,0244 | **0,0038** |

`max` steigt weiter und **seine Streuung schrumpft nicht** — das tut ein
Schätzer nicht. `p90` läuft ab n = 20 in ein Band, Streuung schrumpft
auf ein Drittel.

⚠️ **Und bei fünf Ziehungen liegt `max` mit 0,0226 UNTER dem wahren 90.
Perzentil von 0,0256.** Die Latte hängt zu tief — das Urteil fällt zu
wohlwollend aus.

**Auf den echten Daten** (`n81_konvergiert_der_nullpunkt.py`, 80
Ziehungen je Fall):

| | Band unten | max(5) | max(80) | p90 ab n=20 |
|---|---|---|---|---|
| `schnitt` 20 % | +0,0974 | +0,0382 | +0,0524 ⬈ | ~0,039 → **trägt** |
| `funding` 50 % | +0,0195 | +0,0193 | +0,0267 ⬈ | ~0,0218 → **trägt nicht** |

`funding` bei 50 % trug mit einem Abstand von **+0,0002 R** — zwei
Zehntausendstel. Ab **zehn** Ziehungen kippt es.

### ⚠️ Es widerspricht zwei eigenen stehenden Vorgaben

*„Die ZIEHUNGSZAHL gehört in JEDE Kontrolle"* und *„EINE ZIEHUNG IST
KEIN NULLPUNKT"*. Beide wurden für die **Wirkung** befolgt und für den
**Nullpunkt** übersehen.

### Was daran NICHT hängt

`schnitt` bei 20 % hält bei 5, 10, 20, 40, 60 und 80 Ziehungen
durchgehend. Sein Abstand beträgt +0,058 statt +0,0002. **Ein Befund
mit großem Abstand ist robust; gefährlich sind die knappen.**

### Der Eingriff — bewusst neutral gehalten

`pruefe_auswahl` bekommt zwei neue Parameter, deren **Vorgabewerte das
bisherige Verhalten exakt reproduzieren**:

```python
null_ziehungen: int = 0        # 0 -> ZIEHUNGEN (=5), wie bisher
null_perzentil: float = 0.0    # 0 -> MAXIMUM, wie bisher
```

⚠️ Gegen die vorherige Fassung Ziffer für Ziffer geprüft: `schnitt` 10 %
und 20 %, `funding` 20 % — Band, Nullpunkt, Trennschärfe und Urteil
identisch. **Kein bestehender Befund verschiebt sich.**

Damit lassen sich beide Regeln nebeneinander messen, statt die Norm
blind umzustellen (`n82_beitragslage_beide_nullregeln.py`).

### ⚠️ Ein zweiter, noch offener Punkt in derselben Anlage

Die **Trennschärfe** prüft `pb["unten"] > 0` — gegen NULL. Das **Urteil**
prüft gegen `null_oben`. Ist `null_oben` positiv, ist das Urteil
strenger als die ausgewiesene Trennschärfe angibt. Ein Kandidat kann
„Trennschärfe 0,02" tragen und bei einem Effekt von 0,05 trotzdem kein
TRÄGT erreichen. **Bewusst nicht im selben Lauf geändert** — zwei
Änderungen wären nicht mehr zuzuordnen.

### Eine eigene Vermutung, die dabei widerlegt wurde

Ich hielt `null_oben` für saatabhängig. Es ist **deterministisch**: die
Nullziehungen laufen auf der festen Saat `SAAT + z`, nicht auf der
übergebenen `rng`. Fünf Saaten liefern +0,0375 bis +0,0383. Was wandert,
ist die Reaktion auf geänderte **Daten**, nicht auf Zufall.

### Was die stabile Regel an der Beitragslage ändert — N-82 und N-83

**N-82**, 16 Kandidaten auf allen zulässigen selektierten Mengen, beide
Regeln nebeneinander, 37,5 Minuten:

- ✔ `zufall` trägt unter **keiner** der beiden Regeln — der Lauf gilt
- **14 von 16 Kandidaten behalten ihr Urteil unverändert**
- Genau einer wechselt: `funding` von TRÄGT auf **NICHT ENTSCHEIDBAR**

⚠️ *Nicht entscheidbar* ist laut Norm eine Aussage über die **Messung**,
nicht über den Kandidaten. `funding` ist damit **nicht widerlegt**.

⚠️⚠️ **Die neue Regel ist nicht strenger, sondern stabil** — sie bewegt
sich in beide Richtungen. `schnitt` bei 10 % kippt **umgekehrt**, von
„trägt nicht" auf TRÄGT, weil `max(5)` dort mit 0,0609 zufällig hoch lag
(p90 über 40: 0,0482). Wer die Regel für eine Verschärfung hält, hat sie
nicht verstanden.

**N-83** holt die Reproduktionspflicht nach. Der `funding`-Befund vom
30.08. stand auf der Menge **`frei`** — die Mengen-Systematik gab es
damals noch nicht. Auf dieser Basis nachgemessen:

| auf `frei` | Wirkung | Abstand alt | Abstand neu | |
|---|---|---|---|---|
| **`funding`** | +0,0249 | +0,0042 | **+0,0044** | ✔ trägt unter beiden |
| **`turnover`** | +0,0639 | +0,0018 | **−0,0008** | ⚠️ kippt → nicht trennbar |
| `schnitt` | +0,0314 | −0,0154 | −0,0156 | trägt hier nicht |
| `zufall` | +0,0043 | −0,0097 | −0,0142 | ✔ sauber |

> ✔✔ **R-R11 erfüllt: der `funding`-Originalbefund ist reproduziert und
> NICHT umgestoßen.** 353.892 Anker, 299 Symbole, 39 Blöcke.

✔ Und die **live genutzte Form passt dazu**: `funding` ist als
*„Funding-Rang im Markt"* registriert, und `frei` beantwortet nach
P6/F-212 genau die Marktfrage. Was fällt, ist `funding` als **Beitrag**
auf der selektierten Menge — nicht die Form, die läuft.

⚠️⚠️ **`turnover` dagegen verliert seine einzige Basis.** Auf den
selektierten Mengen war er schon vorher nicht entscheidbar; auf `frei`
kippt er jetzt.

Und ausgerechnet dort schlägt die zweite Unstimmigkeit durch. Sein
Urteil lautet wörtlich:

> *„Wirkung +0,0639 über der Trennschärfe 0,0500 R, aber …"*

**Die Trennschärfe wurde gegen NULL bestimmt, das Urteil fällt gegen
`null_oben` = 0,0220.** Zwei Maßstäbe in einem Satz, und sie
widersprechen sich (2.188-inkonsistenz).

### Der Stand der drei live gemessenen Beiträge

| | unter der stabilen Nullregel |
|---|---|
| **`schnitt`** | ✔ trägt als **Beitrag** — 10 % und 20 %, Abstand bis +0,0569 |
| **`funding`** | ✔ trägt als **Markt-Aussage** — `frei`, Abstand +0,0044 |
| **`turnover`** | ⚠️ trägt **nirgends** mehr |

### ⚠️ Was NICHT geschehen ist

**Die Nullregel ist nicht umgestellt.** Sie ist als Parameter verfügbar,
der Vorgabewert reproduziert das bisherige Verhalten Ziffer für Ziffer.
Ob sie zum Standard wird, ist eine **Nutzerentscheidung** — sie ändert
den Maßstab für jeden künftigen Befund.

### Die zwei Folgefunde — N-84 und N-85

Ihre stehende Vorgabe *„bevor eine Bewertung fällt, müssen wir alles
unternehmen — was ist der Grund und dass wir eine Lösung finden"* galt
hier für `turnover`. Sie hat sich gelohnt: es kamen **zwei weitere
Fehler derselben Anlage** heraus.

#### N-84 — die Trennschärfe gleichgezogen

Wird die Trennschärfe gegen `null_oben` geprüft statt gegen null, ändert
sich **kein einziges `traegt`** — wie vorhergesagt. Aber die
Begründungen kippen falsch herum:

```
schnitt 20 %   Wirkung +0,1858   traegt = TRUE   ->  Urteil "KEIN BEFUND"
```

⚠️ **Ordnungsfehler in `messnorm.urteil`:** die Abfrage
`if self.trennschaerfe is None: return "KEIN BEFUND"` steht **vor**
`if self.traegt: return "TRAEGT"`. Ein echtes TRÄGT wird verdeckt.

#### N-85 — die Leiter der gepflanzten Stärken ist zu kurz

Sie endet bei **0,10**, während `schnitt` eine Wirkung von **+0,1858**
hat. „Untermächtig — selbst +0,10 R gepflanzt wurde nicht gefunden" ist
eine Aussage über die **Leiter**, nicht über die Anlage.

⚠️ Und der eigene Werkzeugkasten widerspricht sich: `messnorm_rand.py`
benutzt seit jeher `(0,02 · 0,05 · 0,10 · 0,20)`.

Mit der Leiter bis 0,40, stabiler Nullregel und gleichgezogener
Trennschärfe:

| | Wirkung | trägt | Trennsch. | Urteil |
|---|---|---|---|---|
| `schnitt` 20 % | +0,1858 | ✔ | 0,40 | **TRÄGT** |
| `schnitt` 10 % | +0,1830 | ✔ | 0,40 | **TRÄGT** |
| **`funding` frei** | +0,0249 | ✔ | **0,10** | **TRÄGT** |
| `turnover` frei | +0,0639 | ✖ | 0,20 | trägt nicht **bis 0,20 R** |
| `turnover` 50 % | +0,0913 | ✖ | 0,40 | trägt nicht bis 0,40 R |
| `funding` 50 % | +0,0313 | ✖ | 0,20 | trägt nicht bis 0,20 R |
| `zufall` frei | +0,0043 | ✖ | 0,10 | ✔ trägt nicht |
| `zufall` 20 % | +0,0163 | ✖ | 0,40 | ✔ trägt nicht |

✔ **Die vorab benannte Probe hält: die lange Leiter ist kein
Freibrief.** Sie holt `schnitt` zurück, rettet `turnover` und
`funding`-50 % aber **nicht** — und `zufall` trägt unter keiner Variante.

#### ⚠️ Was das für `turnover` heißt — er ist NICHT widerlegt

> **„Trägt nicht bis 0,20 R" schließt nur Effekte ab 0,20 R aus. Seine
> gemessene Wirkung beträgt +0,0639. Über DIESE Größe sagt die Anlage
> nichts.**

`turnover` ist **unentschieden**, nicht gefallen. Das ist ein anderer
Zustand, und er verlangt eine bessere Messung, keine Abwertung.

#### ✔✔ Und `funding` ist der robusteste Befund des Projekts

Er trägt unter **beiden** Nullregeln, **beiden** Trennschärfe-Maßstäben
und **beiden** Leitern — der einzige Fall, der alle vier Varianten
übersteht, und das mit einer Trennschärfe von 0,10 statt 0,40.

#### ⚠️ Ein dritter Punkt, bewusst nicht verfolgt

Die Positivkontrolle pflanzt in die **gemischte** Welt, deren Band
breiter sein kann als das der echten. Dann überschätzt die Trennschärfe
systematisch — `schnitt` trägt mit +0,186 bei ausgewiesener Trennschärfe
0,40. Nicht im selben Zug geändert.

### ⚠️⚠️ Der Stand — drei Parameter liegen bereit, KEINER ist gesetzt

| Parameter | Vorgabe heute | geprüfte Alternative |
|---|---|---|
| `null_ziehungen` / `null_perzentil` | 5, Maximum | 40, 90. Perzentil |
| `trennschaerfe_gegen_nullpunkt` | `False` (gegen null) | `True` |
| `staerken` | bis 0,10 | bis 0,40 |

**Alle drei Vorgabewerte reproduzieren das bisherige Verhalten Ziffer
für Ziffer.** Ob sie zum Standard werden, ist eine Nutzerentscheidung —
sie ändert den Maßstab für jeden künftigen Befund.

### ✔ Nutzerentscheidung 08.09.: alle drei sind gesetzt

```python
MESSSTANDARD_AB = "2026-09-08"
NULL_ZIEHUNGEN = 40
NULL_PERZENTIL = 90.0
TRENNSCHAERFE_GEGEN_NULLPUNKT = True
STAERKEN = (0.02, 0.05, 0.10, 0.20, 0.40)
```

Durchgezogen in: `messnorm.py` (die Quelle) · `messnorm_auswahl.py` ·
`messnorm_rand.py` · `pruefe_pakete.py` (Paket **`Messstandard`**, zehn
Prüfungen, alle durch Mutation belegt) · `CLAUDE.md` · Methodik **2.188**
· Befunde **2.188 bis 2.200** · Memory.

⚠️ **Ein viertes betroffenes Modul kam dabei heraus:**
`messnorm_rand.py` hatte alle drei Fehler, und zwar in **beiden**
Messfunktionen. Es gehört zur Normfamilie und war nie mitbetrachtet
worden — genau die Uneinheitlichkeit, die 2.194 aufgedeckt hat.

**Abnahme, in dieser Reihenfolge:** erst neutral parametrisiert und
Ziffer für Ziffer gegen die `git`-Vorgängerfassung geprüft → dann beide
Regeln nebeneinander → dann R-R11 auf der Originalbasis → dann die vorab
benannte Probe gegen Gefälligkeit. Erst danach gesetzt.

### ⚠️⚠️ R-R9 greift — die Neukalibrierung ist fällig

Die Beitragslage hat sich geändert, also ist eine Neukalibrierung fällig.
Live registriert sind drei gemessene Größen:

| | Stand nach dem Standard |
|---|---|
| `funding` (Markt-Rang) | ✔ hält |
| `schnitt` | ✔ hält — und trägt jetzt auf **zwei** Mengen statt einer |
| `turnover` (Markt-Rang) | ⚠️ unentschieden; seine Stufen (3,15 / 0,83 / 0,22 / −1,79 / −2,4) stehen auf einer Basis, die keinen tragenden Befund mehr liefert |

> ⚠️ **`turnover` wird NICHT abgeräumt.** „Trägt nicht bis 0,20 R"
> schließt nur Effekte ab 0,20 R aus — seine Wirkung beträgt +0,0639.
> Über diese Größe sagt die Anlage nichts. Das verlangt eine **bessere
> Messung**, keine Abwertung.

### Der nächste Schritt, den ich empfehle

**Der Selbsttest der Messanlage gegen bekannte Wahrheit.** Künstliche
Welten mit eingebautem Effekt bekannter Größe, und dann die zwei Quoten
messen, die alles entscheiden:

| | |
|---|---|
| **Fehlalarmquote** | wie oft meldet die Anlage TRÄGT, wo nichts ist? |
| **Fundquote** | wie oft findet sie einen Effekt, der wirklich da ist? |

Für die **Nullregel** allein ist das getan (N-81). Für die Anlage als
Ganzes nie. Solange es fehlt, ist jede Aussage über Stabilität eine
Behauptung — und die Fehlerrate von heute (drei Funde an einem Tag in
einem Modul, das als geprüft galt) spricht dagegen.

### ⚠️⚠️ FEHLER 5, gefunden beim Bau des Selbsttest-Prüfstandes

Beim Vorabtest des Prüfstandes fiel auf, dass eine gepflanzte Stärke von
0,40 nur eine **gemessene** Wirkung von 0,079 erzeugt — konstant rund
**20 %**. Der Grund ist herleitbar: gepflanzt wird auf die oberen 20 %,
und `median(alle)` verschiebt sich nur um diesen Anteil.

> **`trennschaerfe` war die gepflanzte Zahl, `wirkung` die gemessene — und
> `messnorm.urteil` verglich sie miteinander.**

An Theorie, Kunstwelt und echten Daten belegt (20,3 / 20,1 / 19,6 /
19,2 %). Behoben; `messnorm_rand` machte es seit jeher richtig — **zum
dritten Mal an einem Tag war das ausgeklammerte Modul im Recht.**

✔ **Befund 2.198 ist damit aufgelöst** — `schnitt` trägt mit +0,186 bei
einer *gemessenen* Trennschärfe von 0,0944. Kein Widerspruch. Meine
Vermutung über die gemischte Welt war die falsche Spur.

⚠️ **`turnover` bekommt das ehrliche Urteil:** „nicht trennbar" statt
„trägt nicht bis 0,20 R". Wirkung +0,0639 gegen Auflösung 0,0456 — die
Wirkung liegt über der Auflösung, das Band schließt die Null ein.

Ausführlich: Methodik **2.201**.

---

## ✔✔✔ DER SELBSTTEST IST GELAUFEN — 08.09.2026

Die Frage war Ihre: *„haben wir eine stabile Basis?"* Jetzt gibt es eine
Zahl statt einer Behauptung.

```
Fehlalarmquote        0 von 150 Nullwelten, drei Beharrlichkeitsstufen
                      -> obere 95-%-Schranke 2 %   (nominal 2,5 %)
Auflösung             +0,0293 R  (80-%-Fundquote)
Selbstauskunft        +0,0389 R  -> sie ist 25 % BESSER als versprochen
```

**Die Übergangszone ist schmal:** +0,0195 → 30 %, **+0,0293 → 95 %**,
+0,0363 → 100 %. Von blind zu sicher in 0,01 R.

### Die drei Sorgen, die ich Ihnen genannt hatte

| Sorge | Befund |
|---|---|
| meldet sie Befunde ins Leere? | ✔ **nein** — 0 von 150 |
| ist sie übervorsichtig? | ✔ **nein**, im Gegenteil — sie findet besser als sie behauptet |
| trübt Beharrlichkeit das Bild? | ✔ **nein** — 0/50 auch bei AK 0,985 |

⚠️ **Eine eigene Vermutung war falsch:** ich erwartete, die Beharrlichkeit
(`schnitt` hat 0,985) treibe die Fehlalarmquote. Sie tut es nicht.

### ✔✔ Und die Skalenkorrektur ist unabhängig bestätigt

Vor ihr hätte die Anlage „Trennschärfe 0,20" behauptet bei einer echten
Auflösung von 0,029 — **Faktor 7 daneben**. Danach: 0,0389 behauptet
gegen 0,0293 tatsächlich.

### Was die drei live gemessenen Beiträge jetzt wert sind

| | Wirkung | gegen die Auflösung 0,0293 |
|---|---|---|
| `schnitt` 20 % | +0,1858 | **6,3-fach** — solide |
| `funding` frei | +0,0249 | knapp **darunter** — trägt, aber am Rand |
| `turnover` frei | +0,0639 | **2,2-fach darüber** — und trägt trotzdem nicht |

⚠️⚠️ **`turnover` ist damit nicht „zu schwach", sondern über die Blöcke
instabil.** Das ist ein anderer Befund, und er sagt, wo nachzusehen wäre.

⚠️ Einschränkung: die Kunstwelt hat 150 Symbole, `turnover` nur 66 — die
Zahl ist ein Hinweis, kein Beweis.

### ⚠️⚠️ Was auch jetzt NICHT belegt ist

Geprüft wurde: ein **Niveauversatz** auf den oberen 20 %, auf der
**20-%-Menge**, bei **H20**, mit **150 Symbolen**, bei **unabhängiger
Auswahl**.

Offen bleiben: gradueller Zusammenhang statt Sprung · die Mengen `frei`,
`10 %`, `50 %` · kleine Symbolzahlen · andere Zielgrößen · eine Auswahl,
die mit dem Effekt zusammenhängt.

> **„Geprüft" heißt hier: in diesem Ausschnitt.** Das ist erheblich mehr
> als heute früh — und es ist nicht dasselbe wie „überall richtig".

Ausführlich: Methodik **2.204**, Befunde **2.204 bis 2.207**.

---

## ✔✔✔ 09.09.2026 — DER NULLBEZUG IST GEMESSEN ENTSCHIEDEN

R-R9 abzuarbeiten hat auf eine tiefer liegende Frage geführt: **wogegen
wird eigentlich geprüft?**

### Was R-R9 selbst ergab

✔ **Im engeren Sinn erfüllt.** Beitragslage im Code unverändert,
Fingerabdruck stimmt, Kalibrierung reproduziert ziffergenau: **0,080 →
16,5 % Durchlass**, Gewinn +0,1316 gegen +0,1324.

⚠️ Dabei kam heraus: **`schnitt` wurde nie wieder aufgenommen.** Seine
Rücknahme vom 31.08. gilt seit dem 07.09. als abgelöst (kontaminierte
Basis) — im Code steht er weiter auf `stufen=None`. ⚠️ Er kann aber auch
kein Regler sein: seine fünf Stufen sind ein **Buckel**, zweimal
gemessen. **Es gibt also gar keinen Beitragswechsel, für den zu
kalibrieren wäre.**

⚠️ Und eine eigene Korrektur: ich hatte `turnover` auf der vollen
Historie gemessen — seine registrierte Basis ist **50 % ab 2022**.
Derselbe R-R11-Verstoß, den ich bei `funding` am selben Tag vermieden
hatte. Auf der eigenen Basis reproduzieren die Wirkungen ziffergenau.

### Der eigentliche Fund

`traegt` verglich die **untere** Vertrauensgrenze des Effekts mit der
**oberen** der Nullwelt — zwei 95-%-Bänder, die sich nicht überlappen,
also etwa p < 0,005. **Die Unsicherheit wurde zweimal gezählt.**

### Wie entschieden wurde — gemessen, nicht diskutiert

150 Nullwelten über **drei echte Basen** (Ränge je Tag gemischt):

| Bezug | Fehlalarme (Soll 2,5 %) | Fundquote |
|---|---|---|
| `null_oben` (bis 08.09.) | **0/150 = 0,0 %** | 34/54 = **63 %** |
| **`nullpunkt`** ← gewählt | **4/150 = 2,7 %** | 53/54 = **98 %** |
| `null` (Befund 2.162) | **42/150 = 28,0 %** | 54/54 = 100 % |

⚠️⚠️ **Das alte Kriterium erzeugte 28 % Fehlalarme** — auf der
`oi_aenderung`-Basis sogar 40 %. Darauf standen `turnover`, `funding` und
`oi_aenderung`.

### ⚠️ Der Prüfstand vom 08.09. musste dafür ersetzt werden

Er war **sechsmal präziser als die Wirklichkeit**. Drei Erklärungen
probiert (Überlappung, Beharrlichkeit, Effektschwankung) — zusammen 0,029
gegen echte 0,108. Dann **abgebrochen statt weiterkalibriert**, und auf
Nullwelten aus **echten** Daten gewechselt.

⚠️ Damit ist auch die gestrige Aussage eingeschränkt: die dort gemessene
Auflösung von +0,0293 galt für eine leichtere Welt.

### Der Stand jetzt

```python
messnorm.NULLBEZUG = "nullpunkt"     # Urteil UND Trennschaerfe
```

Alle sechs registrierten Messpunkte tragen, **`zufall` trägt nicht** —
weder auf `frei` noch auf 5 %. Die Trennschärfen liegen bei 0,010 bis
0,053 statt 0,08 bis 0,10.

### ⚠️⚠️ Und was das ausdrücklich NICHT ist

Nutzerhinweis 09.09.: *„wir sind noch in der Prüfung und Kalibrierung
einzelner Beiträge. **Die Leistung der Kette ist hier noch nicht
berücksichtigt.**"*

Ungemessen: das Zusammenwirken der Beiträge · die Wirkung der Schwelle
auf die tatsächlich erzeugten Signale · die Trichterstufen davor · ob die
Kette am Ende besser ist als ihre Teile.

Ausführlich: Methodik **2.216**, Befunde **2.208 bis 2.218**.

---

# ⚠️⚠️ DIE PRÜFUNG DER KETTE — der Plan (abgestimmt 09.09.2026)

Nutzervorgabe: *„setze die Prüfung der Kette detailliert auf und stimme
dies mit mir ab — denke die ist u.U. nicht eine Messung sondern
mehrere."* Er hatte recht: es sind **sieben**, plus eine Vorfrage.

## Die drei abgestimmten Grundentscheidungen

| | Entscheidung |
|---|---|
| **Zielgröße** | **beides getrennt** — `bewegung_r` für Block I und II (viel Macht), realisiertes R für Block III (wenig Macht) |
| **Messbasis** | **hybrid** — deterministische Stufen über die volle Historie simuliert, nicht-deterministische (LLM-Rollen) nur am echten Signalbestand |
| **Reihenfolge** | **I → II → III** — erst die entscheidbaren Fragen |

## ⚠️ Der Rahmen, der über allem steht

Der Befund *„Barrierensystem = Erwartungswert null"* gilt weiter: brutto,
für jede Geometrie. Es helfen nur **Drift, neue Information oder
niedrigere Kosten**.

> **Die Kette kann keinen Gewinn erzeugen — sie kann nur den positiven
> Rand besser treffen als der Zufall.** Das ist die einzige sinnvolle
> Kettenfrage; alles andere ist eine Frage an die Arithmetik.

## ⚠️ Die Machtlage, vorher benannt

| | Beobachtungen |
|---|---|
| Beiträge (bisher gemessen) | **740.336 Anker** |
| Kette, Signale gesamt (NB-Backup) | 2.789 über 16 Tage |
| Kette, **entschieden** (Ziel oder Stop) | **139** |

**Faktor 5.000.** Block III wird deshalb voraussichtlich „nicht
entscheidbar" liefern — das ist **vorher gesagt** und kein Grund, es zu
unterlassen, aber ein Grund, es **nicht als Freigabekriterium** zu
setzen.

---

## BLOCK I — trägt die Bewertung DORT, wo sie wirkt?

Die Beiträge sind auf **536 Symbolen** belegt. Die Kette beurteilt **~43**,
davon 25 mit Bestand. Ob ein Beitrag auf dieser verengten Menge noch
trägt, ist nie geprüft worden — außer für `schnitt` (2.159).

### K-1 — Reproduzieren die Beiträge nach der Auswahl?

| | |
|---|---|
| **Basis** | Messbasis, aber verengt auf die Menge, die die Auswahl durchlässt |
| **Zielgröße** | `bewegung_r`, H20 |
| **Kandidaten** | `funding`, `turnover`, `oi_aenderung` — je auf ihrer eigenen registrierten Basis |
| **Kontrolle** | `zufall` an derselben Stelle |
| **Vorhersage** | sie tragen weiter, aber **schwächer** — die Auswahl greift bereits nach Momentum, und `schnitt` korreliert damit zu +0,418 |
| **Was sie widerlegt** | trägt einer **nicht mehr**, ist er als Kettenbeitrag ungeeignet, egal wie gut er auf der Messbasis dasteht |

### K-2 — Trägt die SUMME mehr als der beste Einzelbeitrag?

| | |
|---|---|
| **Anlass** | Memory: *„Die Summe der Beiträge taugt nicht als Rangfolge"* — unter dem neuen Nullbezug nie nachgemessen |
| **Vergleich** | Summe gegen den besten Einzelnen, auf derselben Menge |
| **Vorhersage** | die Summe trägt, aber **nicht mehr** als der beste Einzelne |
| **Warum es zählt** | trifft das zu, ist die Punktetabelle Aufwand ohne Ertrag — und R-R9 verliert seinen Gegenstand |

### K-3 — Trennt die Schwelle 0,080, oder kürzt sie nur?

| | |
|---|---|
| **Frage** | ist das **Durchgelassene** messbar besser als das **Gesperrte** — mit Band und Kontrolle? |
| **Bisher** | `messe_schwelle_kalibrierung` zeigt +0,1316 „gegen ohne" — aber **ohne Band und ohne Nullkontrolle** |
| **Vorhersage** | sie trennt, aber der Abstand ist klein gegen die Auflösung |
| **⚠️ Bedeutung** | das ist die **praktisch wichtigste Einzelfrage**: 0,080 steuert den Produktivgang direkt |

---

## BLOCK II — trägt jede STUFE ihren eigenen Beitrag?

Eine Ablation: jede Stufe einmal weglassen und messen, was sich ändert.

### K-4 — Was trägt jede einzelne Trichterstufe bei?

| | |
|---|---|
| **Verfahren** | je Stufe: mit / ohne, auf derselben Menge, mit Band |
| **Bekannt** | die **Auswahl bringt null zusätzliche Werte** (alle Gewählten haben Bestand) · die **Sperren nehmen 14 %**, nicht 33 % |
| **Vorhersage** | mehrere Stufen tragen **nichts Messbares** bei — die Auswahl am ehesten |
| **⚠️ Regel** | eine Stufe, die nichts beiträgt, wird **nicht gelöscht, sondern stillgelegt** (G-a, Kanarienvogel) |

### K-5 — Sind die Stufen komplementär oder redundant?

| | |
|---|---|
| **Anlass** | am 02.09. für **zwei** Sperren gemessen (komplementär) — für die ganze Kette nie |
| **Verfahren** | paarweise Überschneidung der gesperrten Mengen + Rangkorrelation |
| **Vorhersage** | die Bewertungsstufen überschneiden sich stark mit der Auswahl (Spearman +0,418 bei `schnitt` ist der Hinweis) |

---

## BLOCK III — was macht die Kette daraus? ⚠️ wenig Macht

### K-6 — Die 79 % „Einstieg nie erreicht"

| | |
|---|---|
| **Der Posten** | **538 von 677** Signalen erreichten die Einstiegszone nie |
| **Frage** | Absicht (die Zone ist bewusst günstig gelegt) oder Konstruktionsfehler? |
| **Zielgröße** | realisiertes R, plus: was wäre gewesen, hätte man **sofort** eingestiegen? |
| **⚠️ Bedeutung** | **der größte unerklärte Posten im ganzen System.** Ist es ein Fehler, ändert er alles danach |

### K-7 — Schlägt die Kette end-to-end den quotengleichen Zufall?

| | |
|---|---|
| **Kontrolle** | quotengleicher Zufall — **nie** gegen die Gesamtmenge (Methodik 2.93) |
| **Vorhersage** | ⚠️ **nicht entscheidbar** bei n = 139 |
| **Was es trotzdem liefert** | die **Größe** des Vertrauensbands — also die Antwort darauf, wieviele Signale es bräuchte, um die Frage je zu beantworten |

---

## ⚠️ Was dieser Plan NICHT enthält

| | |
|---|---|
| **Wirtschaftlichkeit** | Gebühren gehören nicht in die Bewertung (Regel 2). Die Breakeven-Rechnung ist eine **Betriebsfrage**, keine Messung |
| **Die LLM-Rollen** | ihre Qualität ist bis heute nicht messbar (Memory: *„LLM-Qualität nicht messbar"*) — sie bleiben im Hybrid der ungeprüfte Teil, und das gehört benannt |
| **GUI und Anwendungsfälle** | eigener Plan, seit 07.09. offen |

## ⚠️⚠️ Und was am Ende NICHT herauskommen wird

Ein „die Kette ist gut". Was herauskommen kann:

1. welche Stufen **messbar beitragen** und welche nicht
2. ob die Bewertung **auf der Kettenmenge** noch trägt
3. ob die Schwelle **trennt oder nur kürzt**
4. **wieviele Signale** es bräuchte, um die Endfrage je zu entscheiden

**Das ist die Grundlage für den Produktivgang** — nicht ein Gütesiegel.

## ⚠️⚠️ KORREKTUR DES PLANS, noch vor der ersten Messung

Beim Nachsehen in `agent/auswahl.py` — statt die Kettenmenge anzunehmen —
fiel auf, dass **K-1 falsch entworfen war**.

### Die Kettenmenge ist keine momentum-selektierte Menge

```
43 Krypto-Werte im Lauf
  25 mit Bestand    passieren die Auswahl IMMER - nach NICHTS selektiert
   2 von A1         top-2 nach Jahresentwicklung (gemessen +2,74 % H20, t 4,52)
```

Die Beiträge sind auf den Mengen `5/10/20/50 %` belegt — alle nach
**Momentum** verengt. Die Kette wendet sie aber überwiegend auf den
**Bestand** an, und der ist nach nichts selektiert.

**Die Signalverteilung bestätigt es:** `NACHKAUFEN` mit **51,7 Mails/Tag**
hat per Definition Bestand.

### ⚠️⚠️ Und eine zweite Frage, die daraus folgt

`agent/auswahl.py` schreibt es selbst in die Mail:

> *„Dieser Wert wurde NICHT ausgewählt — er wird beurteilt, weil Sie ihn
> halten. Bei einer gehaltenen Position lautet die Frage **‚halten oder
> verkaufen'**, und die stellt sich unabhängig vom Rang."*

Alle Beiträge sind für die Lage `instrument=spot, strategie=einstieg`
gemessen. Ob sie für die **Haltefrage** gelten, ist nie geprüft worden.

### K-1 wird deshalb in drei Teile zerlegt

| | Frage |
|---|---|
| **K-1a** | Tragen die Beiträge auf der **A1-Menge** (top-k nach Jahresentwicklung)? Das ist die Menge, für die sie gedacht sind |
| **K-1b** | Tragen sie auf der **BESTANDS-Menge** — also dort, wo die meisten Signale entstehen? ⚠️ Diese Menge ist nach nichts selektiert; die Beiträge sind dort nie gemessen worden |
| **K-1c** | Gelten sie überhaupt für die **Haltefrage**, oder nur für den Einstieg? ⚠️ Alle Belege stehen auf `strategie=einstieg` |

**Vorhersage:** K-1a trägt (dafür sind sie gebaut) · K-1b ist offen und
das eigentliche Risiko · K-1c ist ungemessen und könnte einen großen Teil
der laufenden Signale betreffen.

> ⚠️ **Das ist bereits ein Befund, noch vor der Messung:** die Beiträge
> werden auf einer Menge angewandt, auf der sie nie geprüft wurden — und
> für eine Frage, für die sie nie gemessen wurden.

---

## ✔ 09.09. — DIE MESSMENGE IST EINGEFROREN, und der Nutzer hatte recht

### ⚠️ Der Einwand, der eine eigene Verwechslung aufdeckte

> *„wenn die Watchlist ein Asset ist, sollte es egal sein. wenn es um die
> Messmenge geht, ok — dann definiere ein Krypto-Standardset."*

**Er hat recht, und ich hatte zwei Fragen vermischt:**

| Frage | richtige Basis |
|---|---|
| **„Trägt die Regel?"** — Aussage über die Welt | **die Messbasis** — je mehr Daten, desto besser |
| **„Wirkt sie auf unseren Werten?"** | die Watchlist |

K-1w hat die zweite gemessen, ich habe sie als Antwort auf die erste
gelesen. Auf 43 statt 536 Symbolen werden **92 % der Daten weggeworfen** —
`turnover`s 5 Blöcke sind ein Befund über die **Messanlage**, nicht über
`turnover`. **Der Messbasis-Befund steht.**

### `messmenge.V1` — 536 Symbole, eingefroren

| | |
|---|---|
| **Inhalt** | alle Symbole über dem Historienfilter, **einschließlich der 174 eingestellten** |
| **Auswahl** | ⚠️ **keine** nach Größe, Liquidität oder Leistung |
| **Änderung** | nur mit neuer Versionsnummer |
| **`lade()`** | liefert genau sie — und **meldet**, wenn eine Reihe fehlt |

⚠️⚠️ **Der Grund ist Reproduzierbarkeit, nicht Abdeckung.** `oi_aenderung`
war auf **117** Symbolen registriert, heute waren es **122** — und der
Wert wanderte von +0,0145 auf +0,0126. **R-R11 ist nicht durchsetzbar,
wenn sich die Basis unter dem Befund wegschiebt.**

✔ Abgenommen: 536 = 536, `funding` +0,0249 und `turnover` +0,0639
reproduzieren ziffergenau. Vier Wächter halten es fest.

### ✔ Und `turnover`s Abdeckung ist eine Grenze der QUELLE

```
Coin Metrics Community, Katalog SplyCur (1d):   139 Assets
davon in unserer Messmenge (536):                66  = 12 %
theoretisches Maximum:                          139  = 26 %
```

⚠️⚠️ **Die 18 scheinbar gewinnbaren sind nicht brauchbar:** `BNB_ETH`,
`USDC_ETH`, `SHIB_ETH`, `MATIC_ETH` — das sind die Mengen **auf
Ethereum**, nicht die Umlaufmengen. `turnover` ist Umsatz durch
Umlaufmenge; die Wrapped-Menge einzusetzen machte die Kennzahl **still
falsch**.

**66 ist die tatsächliche Obergrenze.** Kein Zuschnitt ändert das.

⚠️ Offen bleibt der Weg über eine **andere Quelle** (CoinGecko führt
Umlaufmengen für weit mehr Coins) — der einzige, der etwas ändern würde,
und er braucht eine eigene Prüfung.

---

# 09.09. — `schnitt` ENTSCHIEDEN, und der Review der erledigten Punkte

## N-88: die Abbruchbedingung ist bestätigt, nicht aufgelöst

Das Kandidatenregister hielt fest: *„die Zeitstabilität ist unentschieden.
**Wer vor ihrer Klärung baut, wiederholt den 31.08.-Fehler.**"* Über
**alle fünf Mengen** gemessen, auf der entzerrten Reihe:

| | 5 % | 10 % | 20 % | 50 % | frei | |
|---|---|---|---|---|---|---|
| **`schnitt`** | **−0,431** ⚠️ | −0,081 | **+0,197** ⚠️ | +0,002 | +0,018 | **trennbar auf 5 % UND 20 % — gegenläufig** |
| `funding` | +0,060 | +0,043 | +0,052 | +0,003 | +0,011 | ✔ gleiches Vorzeichen, **keiner** trennbar |
| `zufall` | −0,068 | −0,022 | +0,003 | −0,018 | +0,003 | ✔ keiner trennbar |

> ⚠️⚠️ **„Unentschieden" war zu freundlich.** `schnitt` liefert je nach
> Menge **widersprüchliche signifikante** Antworten — der Zufall dreht
> zwar auch, wird aber **nie** trennbar. **Die Sperre ist nicht baubar.**

✔ **`funding` ist dagegen zeitstabil** — und ein Nullbefund ist bei
diesem Test **stark** (er erklärt zu oft einen Unterschied, 18 % statt
10 %).

⚠️ Der neue Messstandard hat daran nichts geändert — **richtig so**: die
Zeitstabilität hängt nicht am Nullbezug, sondern an der Menge. Die
Vorhersage stand vor dem Lauf und ist eingetroffen.

## Der Review der „erledigten" Punkte

Nutzerauftrag: *„keine neue Doppelmessung, aber prüfe ob du relevante
Fehler und Showstopper findest."*

### ✔ Kein Showstopper beim Hebel-Kalibrierungsfaktor

`hebel_scheitert_an_der_bewertung` rechnet mit **19,5 %** — das ist der
**Ersatz F-219**, gemessen mit der Invarianz als vorab gesetztem
Annahmekriterium (ROH und ANTEIL fielen durch, RANG war exakt invariant).
Gefallen war die **alte** Zahl 16,8 %.

### ⚠️⚠️ Der eine echte Showstopper ist bekannt und gemessen

```
Horizont   Funding    Turnover
H1        +0,0019    +0,0044
H2        +0,0026    +0,0107
H20       +0,0246    +0,0616
```

Die Beiträge sind auf **H20** belegt; bei H1/H2 sind sie **6–7× kleiner**.
N-17a hat die H2-Kalibrierung vollständig durchgemessen (F-203): **die
beste Schwelle ist praktisch 0,000**, r ≈ 0,02.

✔ **Bewusst NICHT live registriert** — *„eine Schwelle ohne Trennschärfe
wäre eine Mengenbremse ohne Qualitätsaussage."* Er wurde also **nicht
übersehen**, sondern gemessen und die Konsequenz gezogen.

### ✔✔ Und er trifft NUR den Hebel, nicht Spot

Die **2,0 Tage mediane Dauer** (F-202) stammen aus Trades **mit
Barrieren**. **Spot hat nach Nutzerentscheidung vom 03.09. keinen Stop** —
der Ausstieg ist rein bewertungsbasiert, nichts zwingt zum frühen
Ausstieg.

> **Für `spot × einstieg` ist H20 damit stimmig.** Genau deshalb heißt der
> Befund *„der **Hebel** scheitert an der Bewertung"* und nicht *„die
> Bewertung scheitert."*

## Der Stand nach dem Review

| | |
|---|---|
| **`spot × einstieg`** | ✔ die einzige belegte und kalibrierte Lage — H20 ist dafür stimmig |
| **Akkumulation** | ⚠️ `schnitt` als Sperre **nicht baubar** (N-88). BTC/ETH/SOL brauchen keine eigene Lösung (Untermacht, kein Gegenbefund) |
| **Hebel** | ⚠️ Entwurf steht (Sizing, kein Timing), scheitert aber an der Bewertung — und zusätzlich am Horizont. **Beides gemessen, nichts übersehen** |

---

# ⚠️⚠️⚠️ DIE OFFENEN PUNKTE — Stand 09.09.2026, vollständig

Nutzervorgabe 09.09.: *„alle neuen und noch offenen Punkte von gestern
und heute bitte in den Plan, Doku eintragen falls noch nicht erfolgt,
sonst vergessen wir diese."*

**Diese Liste ist die Sammelstelle.** Erledigte Punkte werden hier
durchgestrichen, nicht gelöscht — sonst geht verloren, warum etwas
einmal offen war.

## A — DIE MESSANLAGE (aus dem Umbau vom 08./09.09.)

| # | Punkt | Stand |
|---|---|---|
| **A1** | ⚠️⚠️ **Das Band ist auf BINÄREN Daten viermal zu eng** — erwartet ±0,0023, beobachtet ±0,0006. Die Kontrolle `zufall` trägt dadurch | **offen, blockiert den Hebel** (2.238) |
| **A2** | ⚠️ **Die Blockregel ist bei H90 unerreichbar** — 20 Blöcke bräuchten 5.400 Tage ≈ 22 Jahre, der Markt hat 2.900. Entweder Horizont oder Regel muss sich ändern | **offen — Entwurfsfrage** (2.236) |
| **A3** | ⚠️ `ZIEHUNGEN = 5` steckt weiter in der **Positivkontrolle** (4 von 5 — eine Quote mit sechs möglichen Werten) | offen (2.188-offen) |
| **A4** | ⚠️ Ob das **90. Perzentil** zum Vertrauensniveau des Bandes passt, ist ungeprüft | offen |
| **A5** | ⚠️ Die Positivkontrolle pflanzt in die **gemischte** Welt | ✔ weitgehend erklärt durch 2.201 (Skalenfehler), Rest gering |
| **A6** | ⚠️⚠️ `messe_volumenanteil.py` fährt seine Negativkontrolle mit **EINER** Ziehung — und daraus stammt der registrierte Befund N-13-1' | **offen, Befund unter Vorbehalt** (2.203) |
| **A7** | ⚠️ `messe_schwelle_kalibrierung.py` liest nur **zwei fest verdrahtete** Merkmale — ein dritter Beitrag würde still ignoriert | offen (2.211) |
| **A8** | ⚠️⚠️⚠️ **Die Messnorm ist auf der LIVE-Menge nicht anwendbar** — `pruefe_auswahl` misst unter der Tagesklammer, bei k=2 bleiben **0 verwertbare Tage**. Dritte Sperre derselben Bauart neben A1 und A2 | **offen — Nutzerentscheidung** (2.273) |

## B — DIE BEITRÄGE

| # | Punkt | Stand |
|---|---|---|
| **B1** | `schnitt` **Zeitstabilität** | ✔ **GELÖST 09.09.** — war Kollinearität mit der Auswahl (2.242) |
| **B2** | `schnitt` **Form** (Buckel, dreimal aufgetreten) | ✔ **GELÖST 09.09.** — die Rangkorrelation zeigt **keinen Buckel**: beide Hälften negativ, auf Momentum wie Zufall. Der Buckel war ein Artefakt der Gruppenmediane bei 1,5 gegen 29,7 Ankern (2.249) |
| **B3** | ⚠️ `vola` trägt mit **einer** Aussage von drei Mengen und ist auf 20 % zeitinstabil — **an derselben Stelle wie `schnitt`** | offen, Kollinearität vermutet, ungeprüft |
| **B9** | `funding`s Buckel | ✔ **GEKLÄRT 09.09.** — er ist auf der 20-%-Menge trennbar, auf **`frei` nicht** (untere Hälfte +0,0211 [−0,000..+0,042]). Die Live-Stufen stehen auf `frei` und **reproduzieren exakt** (+0,77/+1,40/+0,22/−0,64/−1,75 gegen +0,82/+1,30/+0,12/−0,54/−1,70); die Fünftel sind dort ausgeglichen besetzt (30/29/30/29/30). ⚠️ Die Nicht-Monotonie bleibt real (2.251) |
| **B11** | ⚠️⚠️ **Die MENGE entscheidet die Antwort** — auf `frei` ist der Knick Rauschen, auf der Auswahlmenge (20 %) trennbar. Es gibt keine Menge, auf der `d01` und der Prüfstein `d34` zusammenpassen; auf der Live-Menge (k=2/Tag) ist die Frage mangels Besetzung **nicht beantwortbar** | **offen — Datenlage** (2.263, 2.264) |
| **B10** | ⚠️ `schnitt` als **Regler**: Form geklärt (monoton), Zeitstabilität geklärt (Kollinearität) — **die Stufen müssen aber noch aus einem monotonen Verfahren abgeleitet werden**, nicht aus Gruppenmedianen | **offen — der nächste Schritt** |
| **B4** | `amihud` ist **zeitstabil mit konsistentem Vorzeichen** — trägt aber nicht. 2.166 sagt: er misst **Ausführbarkeit**, nicht Potential | offen als Nebenweg |
| **B5** | `schnitt50` zeitstabil, aber **Widerspruch** im Gesamtlauf | offen |
| **B6** | ⚠️ `turnover`s Abdeckung: **66 von 536**. Coin Metrics kennt nur 139 Assets; die 18 „gewinnbaren" sind Wrapped-Mengen und **nicht brauchbar** | **offen — nur über eine andere Quelle (CoinGecko) lösbar** (2.233) |
| **B7** | ⚠️⚠️ **Der Horizont**: Beiträge auf H20 belegt, bei H1/H2 6–7× kleiner. H2-Kalibrierung durchgemessen, Schwelle praktisch 0,000 | **bewusst nicht registriert — offene Nutzerentscheidung** (F-203) |
| **B8** | ⚠️ **R-R9**: jeder Beitragswechsel verlangt eine Neukalibrierung der Schwelle | steht bereit, greift bei Einbau |

## C — DIE KETTENPRÜFUNG (Plan vom 09.09.)

| # | Punkt | Stand |
|---|---|---|
| **C1** | K-1a — Beiträge auf der A1-Menge | ⚠️⚠️ **GEMESSEN 10.09.** — **kein** registrierter Beitrag trägt, bei keinem k. ⚠️ Aber es ist **kein Nullbefund**: bei k=2 ist selbst ein gepflanzter Effekt von 0,40 R nicht auflösbar (2.267, 2.267-kein-nullbefund) |
| **C2** | K-1b — auf unselektierter Menge | ✔ **gemessen** — übertragen sich (2.221) |
| **C3** | K-1c — andere Lagen | ⚠️ **teilweise**: Akkumulation nicht messbar (A2), Hebel ungültig (A1) |
| **C4** | K-2 — trägt die **Summe** mehr als der beste Einzelne? | offen |
| **C5** | K-3 — **trennt die Schwelle 0,080** oder kürzt sie nur? | offen — praktisch wichtigste Einzelfrage |
| **C6** | K-4/K-5 — **Ablation** je Trichterstufe, Komplementarität | offen |
| **C7** | K-6 — die **79 % „Einstieg nie erreicht"** | offen — größter unerklärter Posten |
| **C8** | K-7 — end-to-end gegen Zufall | offen, ⚠️ voraussichtlich nicht entscheidbar (n = 139) |
| **C9** | ⚠️ **P6 gegen F-212**: die Beiträge sind auf `frei` registriert (Markt-Frage), F-212 verlangt die selektierte Menge (Beitrags-Frage) | teilweise geklärt, für `funding` entschieden (2.230) |
| **C10** | ⚠️ Die **Watchlist ist zu klein**, um `turnover` und `oi_aenderung` dort zu prüfen (5 bzw. 21 Blöcke) | offen — Datenlage, nicht Beitragsfrage |

## D — DATENLAGE UND BETRIEB

| # | Punkt | Stand |
|---|---|---|
| **D1** | ⚠️ **CANTON** ist gehalten (`rolle=core`), hat aber **kein OHLC** — auch nicht in der Produktion | **offen, Nutzerentscheidung** |
| **D2** | ⚠️ **ASTER** (318 Tage) und **MON** (269) sind zu kurz für die Messbasis | offen |
| **D3** | ⚠️ **7 Klassenkollisionen** (BOND, C, DASH, DIA, MDT, STX, T) — `messreihen.symbol` ist PRIMARY KEY | offen, Messungen nicht betroffen |
| **D4** | ⚠️⚠️ **Es gibt keine Bestandshistorie** — `holdings` hat 55 Zeilen ohne Zeitachse, `portfolio_wert_historie` ist leer. Die K-1b-Frage konnte nur über einen **Stellvertreter** beantwortet werden | **offen — strukturell** |
| **D5** | ⚠️ `strategie` wird in den Signalen **nie gesetzt** | offen |
| **D6** | Läuft `refresh_prices_job` auf dem Notebook noch? | **offene Rückfrage an den Nutzer** |

## E — DIE GROSSE PLANUNG

| # | Punkt | Stand |
|---|---|---|
| **E1** | ⚠️⚠️⚠️ **Die umfangreiche Planung mit GUI, Funktionalitäten und Anwendungsfällen** (neue Assets, Assets fallen weg oder ändern sich) — ausdrücklich am **07.09.** verlangt | **offen, nie begonnen** |
| **E2** | Die fünf Krypto-Phasen (Grundlinie · Position mit These · Strategie setzen · Akkumulation · Hebel) | offen |
| **E3** | ⚠️ **Der Produktivgang** — nach Block I und II der Kettenprüfung erwägbar, nicht davor | offen |

## ✔ Was in den letzten zwei Tagen ERLEDIGT wurde

- Der **Messstandard** gesetzt (Nullregel, Trennschärfe, Leiter, Urteilsreihenfolge, Skala) — sechs Fehler
- Der **Nullbezug** gegen bekannte Wahrheit **gemessen** statt gewählt
- Der **Selbsttest** der Messanlage — erstmals überhaupt
- Die **Messmenge eingefroren** (`messmenge.V1`, 536 Symbole, 174 eingestellt)
- Die **Registrierungsbasis maschinenlesbar** (`bestand.messbasis`) — nach drei R-R11-Fehlern an einem Tag
- **R-R9 abgearbeitet** — Kalibrierung reproduziert ziffergenau
- `schnitt`s **Zeitstabilität gelöst** — Kollinearität, nicht Instabilität

---

## 09.09. — B10 und B11: der Buckel gehört BEIDEN, an derselben Stelle

### B10 — `schnitt`s Stufen auf derselben Basis wie `funding`

N-92 hatte gezeigt, dass `funding`s Live-Stufen auf **`frei`** entstehen,
wo die Fünftel ausgeglichen besetzt sind. `schnitt`s Buckel wurde auf der
**20-%-Menge** gemessen (1,5 gegen 29,7 Anker). **Die beiden waren nie
vergleichbar.**

| auf `frei` | Fünftel 0..4 | Besetzung | Spanne |
|---|---|---|---|
| **`schnitt`** | +1,28 / **+1,59** / +0,28 / −1,19 / −1,96 | 48/48/47/48/48 | 3,55 |
| **`funding`** *(live)* | +0,77 / **+1,40** / +0,22 / −0,64 / −1,75 | 30/29/30/29/30 | 3,15 |
| `zufall` | −0,17 / +0,07 / +0,09 / +0,11 / −0,10 | 51/50/50/50/51 | **0,28** |

✔ Der Buckel hat sich **verändert**: N-65 fand auf 20 % einen
ausgeprägten Hochpunkt in der **Mitte** (+9,49 bei Fünftel 2). Auf `frei`
sind nur **Fünftel 0 und 1 vertauscht**, danach fällt es sauber.

⚠️ Die Gegenprobe war nötig: bei `schnitt` gehen Median (+1,28) und
**Mittel (+62,39)** weit auseinander — schwere Ränder. Auch die Kontrolle
wird mit dem Mittel wild. **Der Median ist hier richtig.**

> ⚠️⚠️⚠️ **B10 ist damit keine Messfrage mehr, sondern eine
> Maßstabsfrage:** `schnitt` erfüllt die Monotonie-Vorgabe **genauso
> wenig wie `funding`** — und `funding` läuft live.

**Entweder** die Vorgabe gilt streng → dann müsste auch `funding` fallen.
**Oder** sie gilt nicht streng → dann ist `schnitt` registrierbar, mit
**100 % Abdeckung** und R-R9 im Gefolge. **Nutzerentscheidung.**

✔ Das Projekt hat diese Lage schon einmal benannt (2.161-massstab):
*„Einen Kandidaten an einer Hürde scheitern zu lassen, die die
Bestandsbeiträge nie nehmen mussten, wäre zweierlei Maß."*

### B11 — und der Nutzer hatte recht: `funding_extrem` gibt es schon

⚠️ Nutzerhinweis 09.09.: *„glaube zu Extremfunding gab es bereits eine
Bewertung."* Richtig — `funding_extrem` ist registriert. **Aber er misst
eine andere Achse:** den Abstand vom **eigenen** Normalzustand in MAD,
**vorzeichenlos**, je Symbol. B11 fragt nach der Form der
**Querschnitts-Rangskala**.

| | |
|---|---|
| **gegen** die These | `funding_extrem` zeigt im Gesamtlauf **WIDERSPRUCH**, und F-207: er verbessert die Live-Sperre **nicht** |
| **für** die These | der Knick sitzt bei `funding` **und** `schnitt` an **derselben** Stelle, auf `frei`, bei **zwei unabhängigen Datenquellen** |

⚠️ Das ist schwer als Zufall zu lesen — und wäre eine Aussage über den
**Markt**, keine Messschwäche.

---

## 09.09. — B10/B11: der Knick auf `frei` — ⚠️ ÜBERHOLT, siehe die Korrektur darunter

### Zwei Kriterien sind vorher gescheitert

| | warum |
|---|---|
| **Monotonie** als Hürde | reißt den Bestand mit — **sechs von acht** Kandidaten brechen sie, darunter **zwei live laufende** (`funding`, `oi_aenderung`) |
| **Stufenspanne** als Ersatz | lässt **alle acht** durch, auch `rsi` und `amihud`, die nicht tragen. Sie misst Spreizung, nicht Wirkung |

### Erst die richtige Frage hat entschieden — ohne neues Kriterium

**Ist der Knick stabil?** Gemessen als `d01 = Stufe 1 − Stufe 0`, mit
Band, gegen den Nullpunkt — und `d34` als Prüfstein, ob die Maschinerie
überhaupt arbeitet.

| | d01 (der Knick) | d34 (unstrittige Ordnung) |
|---|---|---|
| **`funding`** | +0,040 [−0,037 .. +0,116] **nicht trennbar** | **+0,066 [+0,019 .. +0,118] TRENNBAR** |
| **`oi_aenderung`** | +0,026 [−0,027 .. +0,083] **nicht trennbar** | **+0,052 [+0,007 .. +0,094] TRENNBAR** |
| `schnitt` | +0,019 nicht trennbar | nicht trennbar → **untermächtig** |
| `turnover` | −0,131 trennbar, Hälften **kippen** | nicht trennbar |
| `zufall` | ✔ nicht trennbar | ✔ nicht trennbar |

> ⚠️⚠️⚠️ **Bei den beiden Beiträgen mit nachgewiesener Messmacht ist der
> Knick NICHT trennbar, die unstrittige Ordnung schon.** Das ist ein
> Nullbefund **mit** Trennschärfe.

### ✔✔ B11 beantwortet

**„Das Extrem ist nicht der beste Fall" ist NICHT belegt.** Der
Unterschied zwischen Fünftel 0 und 1 ist Rauschen. Das passt zu
`funding_extrem`, der im Gesamtlauf Widerspruch zeigt und die Live-Sperre
nicht verbessert (F-207) — **zwei unabhängige Zugänge, dasselbe
Ergebnis**.

### ✔✔✔ B10 gelöst — ohne die Monotonie-Vorgabe aufzugeben

```
funding (registriert)   alt  +0,82  +1,30  +0,12  -0,54  -1,70
                        neu  +1,06  +1,06  +0,12  -0,54  -1,70   MONOTON

schnitt                 alt  +1,28  +1,59  +0,28  -1,19  -1,96
                        neu  +1,44  +1,44  +0,28  -1,19  -1,96   MONOTON
```

Werden die zwei Stufen zusammengelegt, die **gemessen nicht
unterscheidbar** sind, werden **beide** Tabellen monoton fallend.

⚠️ **Keine Anpassung an das gewünschte Ergebnis:** die Zusammenlegung ist
durch die Messung begründet und stand **vorab** im Skriptkopf als
Konsequenz — *„Dann wären Stufe 0 und 1 zusammenzulegen, nicht die
Beiträge zu verwerfen."*

---

## ⚠️⚠️⚠️ 09.09. KORREKTUR — der Abschnitt darüber gilt NICHT MEHR

**Anlass war die Nutzervorgabe** *„aber vorsicht funding wurde sehr
intensiv geprüft — schau nochmal in die doku plan und messungen damit wir
nichts zurück oder verbauen."* Sie war berechtigt: beim Öffnen von
`agent/wahrscheinlichkeit.py` stand direkt an der Tabelle eine Sperre.

> ⚠️⚠️ **WER DIESE TABELLE ÄNDERN WILL, MUSS AUF DER SELEKTIERTEN MENGE
> MESSEN.** Alles andere misst eine Menge, in der die Beiträge gar nicht
> wirken — und bekommt zuverlässig einen Nullbefund.

**N-92, N-93 und N-95 liefen alle auf `frei`.** Der Vorschlag war damit
nicht gedeckt.

### Was das Nachmessen ergeben hat (N-96, N-97)

| Menge | `d01` (der Knick) | `d34` (unstrittig) | Kontrolle |
|---|---|---|---|
| `frei` (536) | +0,0402 [−0,0369 .. +0,1159] **nicht trennbar** | **+0,0656 [+0,0191 .. +0,1180] trennbar** | ✔ stumm |
| 20 % Momentum | **+0,2069 [+0,0137 .. +0,4304] TRENNBAR** | +0,0786 nicht trennbar | ✔ stumm |
| 10 % | zu wenige Blöcke | zu wenige Blöcke | ⚠️ **feuert** (+0,0874) |
| Watchlist (43) | +0,0423, Band ±0,25 R | Besetzung 2,7/2,4 → **KEIN BEFUND** | ✔ stumm |

> ⚠️⚠️⚠️ **Es gibt keine Menge, auf der beides zusammenpasst.** Auf
> `frei` arbeitet der Aufbau (`d34` trägt) und der Knick ist null; auf
> 20 % trägt der Knick und `d34` nicht. **Damit ist das Zusammenlegen von
> Stufe 0 und 1 nicht belegt — und die Live-Tabelle bleibt unverändert.**

### ⚠️⚠️ Drei Nebenbefunde, die schwerer wiegen als die Ausgangsfrage

**1. Der Betriebsablauf ist zweistufig — und F-212 bildet ihn nach.**

```
agent/marktrang.raenge    Rang über die MESSBASIS (536), für uns nur ABGELESEN
agent/auswahl.waehle      k=2 aus der Watchlist nach 250-Tage-Entwicklung ≈ 4,7 %
```

F-212s „oberste 5 % nach Momentum" ist **kein Messkonstrukt**, sondern
eine Nachbildung genau dieser Auswahl. Damit ist der Widerspruch aus
**2.228 auflösbar**: `frei` ist die **Rang**menge, die Auswahl ist die
**Bewertungs**menge — zwei Rollen, kein Widerspruch.

**2. Die Live-Entscheidungsmenge sind k=2 Werte pro Tag.** Schon auf der
ganzen Watchlist (43) reicht die Besetzung nicht (2,7 bzw. 2,4 Anker je
Fünftel). Eine fünfstufige Tabelle lässt sich dort **nicht** beurteilen —
Datenlage, nicht Sorgfalt. Von 43 Werten liegen je Tag
**4,2 / 4,1 / ~11 / 2,7 / 2,4** in den Funding-Fünfteln; die Stufen
−0,54 und −1,70 tragen unter drei Werte pro Tag.

**3. „monoton" hieß nie streng monoton.**

```python
mono = all(werte[i] >= werte[i+1] - 0.02 for i in range(4))   # pruefe_funding_monoton.py:59
```

Die Prüfung vom 30.08. hat eine **Toleranz von 0,02 R**; die Inversion
betrug 0,002 R. Der Knick war **bekannt und bewusst durchgelassen**.
Zusammenlegen wäre also keine Fehlerkorrektur, sondern Kosmetik. ⚠️ Die
Toleranz steht in keiner Registrierung — dort heißt es schlicht „monoton
über fünf Fünftel" —, und es ist die **einzige** Monotonieprüfung im
System; `turnover` hat gar keine.

### ⚠️ Und ein eigener Fehler, den der Betriebscode gefangen hat

Der **erste** N-96-Lauf hat zuerst verengt und dann gerangt. Das erzeugt
Fünftel innerhalb der Kohorte — ein Merkmal, das die Anlage nie
berechnet (`marktrang`: *„DER RANG ENTSTEHT ÜBER DEN MARKT"*; `sammle`:
*„NACH dem Rang verengen, nie davor"*). Vorabtest auf Kunstdaten:
**0 % gemeinsame Mitglieder** in Fünftel 0. Bei `funding` blieb der
Schaden klein (+0,2317 gegen +0,2069), weil seine Momentum-Korrelation
+0,002 ist — der Fehler war real, seine Wirkung hier zufällig gering.

**Befunde 2.262 bis 2.266.**

### ⚠️⚠️ Was daraus folgt — und es ist eine Entscheidung

Es wäre ein **Eingriff in einen live laufenden Beitrag**: `funding`s
Stufen wechselten von +0,82/+1,30/… auf +1,06/+1,06/…. Das ändert die
Beitragslage und **löst R-R9 aus** — die Schwelle wäre neu zu
kalibrieren. **Nutzerentscheidung, keine stille Automatik.**

---

## ⚠️⚠️⚠️ 10.09. — K-1a GEMESSEN: die Beiträge sind dort, wo entschieden wird, nicht prüfbar

### Zuerst: was die A1-Menge wirklich ist

Am Betriebscode nachgelesen, nicht angenommen:

```
agent/marktrang.raenge    Rang über die MESSBASIS (536), für uns nur ABGELESEN
agent/auswahl.waehle      k = 2 nach 250-Tage-Entwicklung
agent/rollen_lauf.py:1269 `return`, wenn nicht gewählt — ⚠️ nur OHNE Bestand
```

✔ **A1 sperrt wirklich** (2.270). Gehaltene Positionen umgehen die Auswahl
ganz — deshalb ist K-1b eine echte zweite Frage, keine Variante.

⚠️ **14 von 43 Watchlist-Werten sind heute gar nicht wählbar** — ihnen
fehlt die Jahreshistorie (AIOZ, AKT, ASTER, BRETT, CANTON, CAT, GRIFFAIN,
HYPE, KAS, MON, MORPHO, PLUME, SUPRA, VSN). Über die ganze Historie sind
im Schnitt nur **14,0 Werte je Tag** wählbar, 2026 aber **37,5** (2.271).

### Das Ergebnis — Kontrolle 7 von 7 sauber

| Kandidat | k=2 | k=3 | k=5 | k=8 | k=13 | k=21 | alle |
|---|---|---|---|---|---|---|---|
| `funding` | −0,0264 | −0,0375 | −0,0216 | −0,0133 | −0,0040 | −0,0002 | +0,0151 |
| `turnover` | −0,0590 | −0,0414 | −0,0281 | −0,0194 | −0,0146 | −0,0121 | −0,0116 |
| `oi_aenderung` | −0,0012 | +0,0374 | +0,0040 | +0,0226 | +0,0104 | +0,0213 | +0,0220 |
| `schnitt` | **+0,8697** | **+0,4989** | +0,2107 | +0,1129 | +0,0412 | −0,0037 | −0,0313 |
| `zufall` ✔ | −0,0101 | −0,0047 | +0,0039 | +0,0046 | +0,0057 | +0,0061 | −0,0022 |

> ⚠️⚠️ **Kein registrierter Beitrag trägt — bei keinem k.** Aber das ist
> **kein Nullbefund**: bei k=2 findet die Anlage nicht einmal einen
> **gepflanzten** Effekt von 0,40 R, auch nicht bei der Kontrolle. Die
> Beiträge sind nicht widerlegt, sie sind dort **nicht prüfbar**.

### ⚠️⚠️⚠️ `schnitt`s scheinbarer Treffer ist die Kollinearität aus 2.242

Die Diagnose zeigt es in einer Zeile — **Anteil der Gewählten, den die
Regel sperrt** (definitionsgemäß 20 %):

| | k=2 | k=3 | k=5 | k=8 | k=13 | k=21 | alle |
|---|---|---|---|---|---|---|---|
| `schnitt` | **82,3 %** | 75,1 % | 65,7 % | 58,9 % | 48,8 % | 42,9 % | 34,3 % |
| `zufall` | 20,3 % | 20,0 % | 19,9 % | 20,0 % | 20,1 % | 19,9 % | 20,0 % |

`frei` trägt bei `schnitt` und k=2 im Schnitt **0,35 Anker je Tag** —
weniger als einen. Der Sperranteil fällt exakt spiegelbildlich zur
Wirkung. **A1 und `schnitt` messen dasselbe:** wer 250 Tage gestiegen
ist, steht über seinem eigenen Schnitt (2.268).

### ⚠️⚠️ Und ein Nebenbefund, der schwerer wiegt als die Ausgangsfrage

**Die registrierten Sperren feuern im Betrieb kaum:**

| | sperrt auf der Watchlist |
|---|---|
| `turnover` | **1,9 %** |
| `funding` | **13,2 %** |
| `oi_aenderung` | 20,4 % ✔ |
| `zufall` | 20,0 % ✔ |

Eine Sperre, die zwei von hundert Werten trifft, ist praktisch keine —
und sie erklärt, warum die Beiträge laut F-212 auf **1,5 % der Anker**
wirken. Ursache ist die Messbasis: `turnover` deckt 66 von 536 Symbolen
ab, und die Watchlist liegt in seiner Verteilung unten (2.269).

### ⚠️ Kein Widerspruch zu K-1w — aber auch keine Reproduktion

K-1w misst `funding` auf der Watchlist mit **+0,0886**, K-1a mit
**+0,0151**. Zwei Unterschiede, **beide meine**: anderer Schätzer
(gepoolt statt Tagesklammer) und andere Menge (nur A1-wählbare Symbole
statt aller 43). **2.229-funding steht unverändert** — K-1a hat es nicht
gemessen (2.272, R-R11).

### ⚠️⚠️⚠️ Das Muster: dreimal dieselbe Aussage

| | Sperre | trifft |
|---|---|---|
| **A1** | Band auf binären Daten 4× zu eng | **Hebel** |
| **A2** | Blockregel bei H90 bräuchte 22 Jahre | **Akkumulation** |
| **A8** | Tagesklammer bei k=2 → 0 verwertbare Tage | **die Live-Menge selbst** |

> **Die Messanlage reicht überall dort nicht hin, wo das System
> tatsächlich entscheidet.** Kein Messfehler, sondern eine Aussage über
> die Datenlage.

**Die Folge ist eine Nutzerentscheidung, keine Messung:** entweder die
Kette entscheidet auf einer **breiteren Menge** — dann wird sie messbar
—, oder es gilt ausdrücklich, dass die Bewertung nur auf einer
**Stellvertretermenge** validiert ist. Beides ist vertretbar;
stillschweigend das zweite zu tun, wäre es nicht (2.273).

---

# 10.09. — NUTZERVORGABE: KRYPTO ZUERST, MULTIASSET NACHGELAGERT

> *„lass Multiasset, nicht Krypto als nachgelagerte Aufgabe nach Krypto
> Produktivgang im Plan — zuerst muss Krypto sauber laufen."*

**Das ist eine Festlegung, keine Messfrage.** Sie ordnet alles um, was
bisher als „vier Klassen nach Datenlage gesperrt" gefuehrt wurde:

| | war | ist ab jetzt |
|---|---|---|
| **A-1** `schnitt` auf den vier Nicht-Krypto-Klassen | offener Messpunkt | **zurueckgestellt** — nach dem Krypto-Produktivgang |
| **A-2** G-6 in den anderen Klassen | offene Entscheidung | **zurueckgestellt** |
| **N-19-Messbasis** (4 Klassen) | aufgesetzt | bleibt stehen, wird **nicht weiter bespielt** |
| **G-6** sperrt vier Klassen nach Datenlage | „Luecke" | **kein Mangel mehr, sondern der gewollte Zustand** bis Krypto steht |

Was das fuer die Befundlage heisst: 2.152 („vier von fuenf Klassen sind
nach DATENLAGE gesperrt, nicht nach Bewertung — das ist eine Luecke, kein
Urteil") bleibt inhaltlich richtig, ist aber **keine offene Baustelle
mehr**. Die Luecke ist ab jetzt **beabsichtigt**.

---

# 10.09. — KORREKTUR MEINER DARSTELLUNG, und der Hebel-Strang richtiggestellt

## Was ich falsch dargestellt habe

**Der Hebel ist NICHT erledigt.** Ich habe ihn als „konzeptionell
abgeschlossen (Sizing-Frage)" gefuehrt. Die Nutzervorgabe lautet aber:

> *„Der Hebel MUSS dynamisch anfallen — wenn eine optimale
> Wahrscheinlichkeit fuer Chance und Risiko besteht."*
> *„die Wahrscheinlichkeit auf positives Chance-Risiko-Verhaeltnis soll
> den Hebel dynamisch erzeugen"*, Zielzone **2–5x**

`hebel = verlustanteil / stop_rel` erzeugt den Hebel aus der
**Volatilitaet**, nicht aus der **Wahrscheinlichkeit**. Das ist nicht
dasselbe, und die Vorgabe verlangt das zweite.

## Der Strang, der wirklich offen ist (F-220)

Der Mechanismus **ist gebaut**: kalibrierte Quote -> halbes Kelly ->
Hebel. Er scheitert an der Bewertung, nicht am Entwurf:

| Lage | halb-Kelly | Hebel |
|---|---|---|
| nur `funding`, bestes Fuenftel | 0,190 % | 0,76x |
| **beide, jeweils bestes Fuenftel** | 0,651 % | **2,60x** |
| bestes funding + mittleres turnover | 0,222 % | 0,89x |

> **Nur die eine beste Kombination erreicht die Zielzone 2–5x.** Und
> ausgerechnet die braucht `turnover` — der 66 von 536 Symbolen deckt.

**Damit ist der Hebel kein eigener Baustein, sondern derselbe Engpass wie
alles andere: die Bewertung ist zu schwach und zu duenn gedeckt.** Ein
dritter, breit deckender Beitrag loest Hebel und Abdeckung in einem Zug.

## „Fehlende Daten" — das war falsch. Die Daten SIND da.

Am 10.09. in `data/messdaten.db` nachgesehen statt behauptet:

| Klasse | Symbole | davon mit Volumen |
|---|---|---|
| **krypto** | **536** | **536** (>90 % der Tage) |
| aktien | 470 | 470 |
| themen_etf | 293 | 293 |
| rohstoffe | 35 | 35 |

785.038 von 785.040 Krypto-Zeilen tragen Volumen.

> **`turnover`s 66-Symbol-Grenze kommt NICHT von fehlenden Daten.** Sie
> kommt vom **Nenner**: Coin Metrics liefert die *Umlaufmenge* nur fuer 66
> Werte. Das Volumen selbst liegt fuer alle 536 vor.

## Und es gibt bereits einen Kandidaten, der den Nenner nicht braucht

**`volumenanteil`, relative Form** (Anteil gegen die eigenen 20 Tage) —
gemessen am 02.09. (F-170), aber **nie registriert**:

    volle Basis          +0,0231 R [+0,0093 .. +0,0368]
                         1.026.279 Anker · 578 Symbole · 84 Bloecke
    Zielmenge (512 ohne
    turnover)            +0,0246 R
    Asset-Anteil          1,4 %   (Regel 3 erfuellt; die ROHE Form fiel
                                   mit 69,8 % vorab durch)
    Form                  SPERRE, nicht Regler — belastbar allein Fuenftel 4

**Warum er noch nicht registriert ist:** A6 — seine Negativkontrolle lief
mit **EINER** Ziehung. Der Befund steht unter Vorbehalt, nicht gefallen.

> **84 Bloecke sind reichlich Macht.** Das ist der einzige Kandidat im
> System, der volle Abdeckung, geprueffte Form und ausreichende Datenlage
> zugleich hat.

---

# 10.09. — AKKUMULATION: die fachliche Entscheidung, benannt

> Nutzervorgabe: *„bei Akkumulation und Horizont muessen wir offenbar eine
> Aenderung vornehmen — hier musst du wissen, welche Aenderung die
> fachlich beste ist."*

## Die Entscheidung: **der Horizont bleibt H90. Das NULLMODELL aendert sich.**

**Warum nicht der Horizont:** H90 ist nicht gesetzt, sondern die Sache
selbst. Die Verbilligung fragt *„war es ein guter Kauftag"* — gemessen am
mittleren Kurs der folgenden Periode. Ein Quartal ist der Zeitraum, ueber
den akkumuliert wird; H20 beantwortete eine andere Frage.

**Warum das Nullmodell:** Der Befund vom 28.08. hat bei **H=90 auf 505
Reihen** sauber gemessen — mit dem **zirkulaeren Verschub** auf der
Kalenderachse, nicht mit dem Blockbootstrap:

| Zelle | Rang | Zufall 5–95 % | p | |
|---|---|---|---|---|
| **UNTER_SMA** (Primaerzelle) | +0,0283 | −0,0124 .. +0,0089 | **0,000** | traegt |
| TIEFPUNKT *(Positivkontrolle)* | +0,4242 | −0,0337 .. +0,0292 | 0,000 | Maschine intakt |
| WOCHENTAG *(Negativkontrolle)* | −0,0008 | −0,0007 .. +0,0007 | 0,978 | liegt auf null |
| DCA *(Rechenkontrolle)* | ±0,0000 | — | — | Pflicht |

**Und die Methodik sagt es bereits woertlich (2.77):** *„bei
ueberlappenden Ankern ist ein freier Placebo zu eng."* Der Verschub
erhaelt die **Gleichzeitigkeit des Marktes** — genau die Eigenschaft, die
bei H90 gebraucht wird.

## Der Fehler war meiner, nicht der des Entwurfs

K-1c hat die **Blockregel** angewandt, die fuer H20 gebaut ist. Bei H90
ist ein Block 270 Tage; 20 Bloecke braeuchten 22 Jahre. **Das ist keine
Aussage ueber die Akkumulation, sondern ueber die falsche Wahl des
Nullmodells.** A2 ist damit keine offene Entwurfsfrage mehr.

**Was zu tun ist:** `messnorm` bekommt eine zweite Nullkonstruktion
(`nullmodell="verschub"`), zugelassen fuer Lagen, in denen die Blockregel
strukturell unerreichbar ist. Dann K-1c Akkumulation neu. Der
Messstandard wird dadurch **nicht aufgeweicht** — Trennschaerfeleiter,
die vier Urteile und der Nullbezug bleiben; nur die Erzeugung der
Nullverteilung wechselt dort, wo Ueberlappung sie erzwingt.

---

# 10.09. — DIE REIHENFOLGE BIS ZUM KRYPTO-PRODUKTIVGANG

Alles Nicht-Krypto ist ab hier **nachgelagert** (Nutzervorgabe oben).

| # | Schritt | warum an dieser Stelle |
|---|---|---|
| **1** | **A1 beheben** — Fehlalarmquote der Barrieren-Anlage auf Nullwelten | Ohne sie ist `barriere` nicht messbar, und `barriere` ist die Zielgroesse **jeder** Hebel-Lage. Der Pruefstand steht seit dem 08.09. |
| **2** | **`volumenanteil` unter dem Messstandard nachmessen** | Der einzige Kandidat mit **voller Abdeckung** und geprueffter Form. Er ist der Engpass fuer den Hebel (2–5x braucht eine staerkere Bewertung) und schliesst zugleich `turnover`s Abdeckungsluecke |
| **3** | **Akkumulation: Nullmodell `verschub`, dann K-1c neu** | Fachlich entschieden, siehe oben. Danach hat die Akkumulation zum ersten Mal eine gemessene Grundlage |
| **4** | **Hebel: die Quote mit dem dritten Beitrag neu durchrechnen** | Erst jetzt beantwortbar: erreicht die Zielzone 2–5x mehr als die eine beste Lage? |
| **5** | **K-3 — trennt die Schwelle 0,080?** | R-R9: nach jedem Beitragswechsel ohnehin neu zu kalibrieren. Deshalb **nach** 2, nicht davor |
| **6** | K-2, K-4, K-5 | Rest von Block I und II — danach ist der Produktivgang laut E3 erwaegbar |

**Was sich gegenueber gestern aendert:** K-3 stand als naechster Schritt.
Das war falsch herum — ein Beitragswechsel loest R-R9 aus und macht jede
vorher gemessene Schwelle ungueltig. **Erst die Beitraege, dann die
Schwelle.**

---

# 10.09. — DIE LAGEN ZUSAMMENGEFUEHRT: Vorgabe gegen Code gegen Daten

> Nutzervorgabe 10.09.: *„Swing ist keine genutzte Strategie mehr; bei
> Krypto verbleiben KLASSEN: Core-Werte fuer Akkumulation (BTC, ETH,
> SOL) und SPOT und Hebel … Absicherung ist aktuell nur ueber 2
> Hedge-Positionen gegeben, keine in Krypto … Hebel Long: aktuell nur
> LONG beruecksichtigt und aktiviert, Short ist noch nicht gemessen und
> geplant — das kann man nachgelagert in den Plan aufnehmen."*

## ⚠️⚠️⚠️ ZUERST: WELCHE DATEN GELTEN — die Desktop-Kopie ist VERALTET

| Datenbank | juengster Stand | gilt fuer |
|---|---|---|
| `data/messdaten.db` | **2026-09-10**, 536 Symbole | ✔ **alle Messungen** — sie stehen |
| `data/tradinginfotool.db` | **2026-08-19** (Signale enden 2026-07-21) | ⚠️ **jede Aussage zum Betrieb ist veraltet** |

**Keine einzige Tabelle traegt September-Daten.** Die Produktion laeuft
auf dem Notebook; ihre Daten liegen auf dem Desktop nicht vor.

⚠️ **Was daraus folgt:** Zahlen wie „43 Werte in der Watchlist", „118
Signale", „`strategie` nie gesetzt" stammen aus dieser Kopie. Sie sind
als **Stand 19.08.** zu lesen, nicht als heutiger Betrieb. Die
Messbefunde sind davon NICHT betroffen.

## Die Zusammenfuehrung

| Nutzervorgabe | Code | Daten (Stand 19.08.) |
|---|---|---|
| **Core/Akkumulation: BTC, ETH, SOL** | `handelsauftrag.strategie_fuer()` liest den Schalter `dca_erlaubt` — **nur fuer `spot`** | ⚠️ `asset_dca_settings`: **BTC und ETH. SOL FEHLT** |
| **SPOT** | `instrument="spot"`, Vorgabe `einstieg` | ⚠️ `signals.strategie` bei **allen 118 NULL** |
| **Hebel** | `HEBEL_HANDELBAR_JE_GRUPPE = {"krypto": True}`; das Etikett wird aus der **Rechnung** abgeleitet (`ist_hebelgeschaeft`), nicht vorgewaehlt | `hebel_signals` 5 (alle 14.07.) · `hebel_triggers` 49 · `hebel_positions` **0** |
| **Swing nicht mehr genutzt** | ⚠️ steht weiter in `STRATEGIEN`, in `handelsauftrag` als Paar `hebel -> (einstieg, swing)`, in `rollen_lauf._REIHENFOLGE` und in `messnorm.ZIELGROESSE_JE_LAGE` | keine Daten |
| **Absicherung nur Hedge, keine in Krypto** | ✔ `INSTRUMENTE_JE_GRUPPE`: `krypto -> ("spot",)`, `hedge -> ("absicherung",)` | — |
| **Hebel: nur LONG aktiv, Short nachgelagert** | `config.yaml` S-6: *„Short beratend, Bitpanda fuehrt aktuell nur Long aus"* | ⚠️ `hebel_signals.richtung`: **4 SHORT, 1 LONG** — alle vom 14.07., also VOR der Einschraenkung |

## ⚠️ Zwei Begriffe fuer „Kern", und sie sind nicht dasselbe

`handelsauftrag.py` haelt es ausdruecklich fest:

    `rolle: core` (config.yaml)   13 Assets   steuert COOLDOWN und Budget
    `dca_erlaubt` (DB-Schalter)    3 Assets   steuert die STRATEGIE

Zehn Assets sind `core`, bekommen aber `einstieg`: AVAX, BNB, CANTON,
HYPE, LINK, MORPHO, NEAR, SEI, SUI, TAO. **Sie werden gehalten, aber
nicht aktiv aufgebaut.** Wer die Strategie aus `rolle` ableitet, bekommt
dreizehn statt drei — und Positionen ohne Stop, die nie dafuer vorgesehen
waren.

## Was daraus als AUFGABE folgt

| # | Punkt | Art |
|---|---|---|
| **L1** | ⚠️ **SOL fehlt im DCA-Schalter.** Die Vorgabe nennt BTC, ETH, SOL; gesetzt sind zwei. Ohne SOL laeuft der groesste Core-Wert nach `einstieg` — mit Stop und Trailing | **Nutzerentscheidung / Datenpflege** |
| **L2** | ⚠️ **`swing` aus der Messachse entfernen.** `ZIELGROESSE_JE_LAGE` fuehrt `("hebel","swing")` als eigene Lage. Eine Lage, die es nicht mehr gibt, erzeugt Messaufwand und falsche Abgleiche | Bau, klein |
| **L3** | ⚠️ **`strategie` wird nicht persistiert.** `strategie_fuer()` existiert, aber in `signals` steht durchgehend NULL. Solange das so ist, ist Akkumulation im Betrieb nicht nachweisbar (D5) | Bau |
| **L4** | **SHORT nachgelagert aufnehmen** — nicht gemessen, nicht geplant, aber die Datenstruktur traegt ihn bereits (`richtung`, `angefragte_richtung`) | Plan, nachgelagert |
| **L5** | ⚠️ **KORRIGIERT 10.09.** — der Portfoliowert ist **nicht** leer. `portfolio_wert_historie` läuft seit dem **08.05.**, 91 Zeilen (F-190/S1); leer ist nur die veraltete Desktop-Kopie. **Der echte Mangel ist ein Lesepfad:** N-40/K1 hat geprüft, dass `rollen_lauf`, `betraege` und `entscheidungsrechnung` die Tabelle **nicht lesen** — die einzigen Leser sind die Module der **alten** Kette | Bau, Vorbedingung K1 |
| **L6** | ⚠️ **Der Datenstand des Desktops muss im Abgleich sichtbar sein**, sonst werden veraltete Betriebszahlen wieder als aktuell gelesen | ✔ in `soll_ist.py` gebaut |

⚠️⚠️ **L5 ist neu und wiegt schwer:** N-40/K1 hat die Machbarkeit
geprueft und „klein, aber echt" notiert — *„fehlt der Wert und wir fallen
still auf einen Vorgabewert zurueck, driftet das Risiko unbemerkt."* Die
Tabelle ist leer. Der Hebel kann aus der Wahrscheinlichkeit nicht
erzeugt werden, solange das Kapital zur Laufzeit unbekannt ist — **auch
dann nicht, wenn die Bewertung traegt.**

---

# 10.09. — DER PORTFOLIOWERT: was er umfasst, und was er nicht umfasst

> Nutzerhinweis 10.09.: *„Der Portfoliowert bzw. ob wir mit echten Daten
> arbeiten sollen sollte geprüft werden — alles, nur Krypto,
> Prozentanteil, etc. — auch zum Portfoliowert sollte es zumindest etwas
> in der Dokumentation geben."*

**Es gibt etwas, und zwar mehr als gedacht.** Nachgelesen in
`agent/portfolio_historie.py`, `database/db.py:5033` und der
Fakten-Entscheidungsmappe.

## Was gezählt wird

| | |
|---|---|
| **Umfang** | ⚠️ **ALLE Assetklassen**, nicht nur Krypto — `get_wallet_transactions()` liefert die Krypto-Bewegungen (auch Staking, Boni, externe Einzahlungen), `get_trades()` die Käufe/Verkäufe **aller** Klassen und deckt damit Aktien/ETF/ETC ab |
| **`wert_eur`** | der Wert der **gehaltenen Assets, OHNE Cash** — eine bewusste Entscheidung, keine Vereinfachung |
| **`cash_eur`** | **getrennt** geführt: bei laufenden Werten der echte Betrag, bei rekonstruierten 0 |
| **`index_wert`** | ⚠️ **Z-3 rechnet auf `index_wert`, NICHT auf `wert_eur`** (Korrektur 07.08.) — das ist die prozentuale Bezugsgröße |
| **Läuft seit** | **08.05.**, 91 Zeilen (F-190/S1) |

## ⚠️ Warum Cash bewusst draußen ist

Der Cash-Bestand der Vergangenheit ist nicht rekonstruierbar. Würde man
den heutigen Betrag konstant über alle Tage mitführen, wäre er ein
gleichbleibender Summand — und ein konstanter Summand **dämpft jeden
prozentualen Rückschlag**: aus 15 % Assetverlust würden bei 10.000 EUR
Assets und 5.000 EUR Cash nur 10 % Gesamtverlust. Z-3 (Drawdown-
Notbremse) würde später auslösen, als sie soll — *„ein Messfehler, der
sich nach dem Kontostand des Erstellungstags richtet."*

## Die echten Zahlen, die in der Mappe stehen

    Portfolio (Gesamtkapital)            9.942 EUR
    Einsatz je Trade (spot/einstieg)       800 EUR
    Risiko je Trade = 15 % vom Einsatz     120 EUR  =  1,21 % des Kapitals
    Kelly f* (kalibriertes Potential)     0,67 %   =    67 EUR
    halbes Kelly                          0,34 %   =    33 EUR

    32 gleichzeitige Positionen · 7.779 von 9.942 EUR investiert (78 %)

> **Der heutige feste Verlustanteil ist Faktor 1,8 über vollem Kelly und
> 3,6 über halbem** — nicht Faktor 45, wie hier bis zum 05.09. stand
> (Nennerfehler: 15 % **vom Einsatz** gegen 0,34 % **vom Gesamtkapital**).

## ⚠️⚠️ Was daran offen ist — und es ist NICHT „keine Daten"

| # | Punkt | Art |
|---|---|---|
| **P-1** | ⚠️⚠️ **Die Rollen-Kette liest die Tabelle nicht.** N-40/K1 hat es geprüft: `rollen_lauf`, `betraege` und `entscheidungsrechnung` lesen `portfolio_wert_historie` **nicht** — die einzigen Leser sind die Module der **alten** Kette. Für `r × Kapital` fehlt also ein **Lesepfad**, nicht die Daten | Bau, klein |
| **P-2** | ⚠️ **Der Rückfall muss LAUT sein.** N-40: *„fehlt der Wert und wir fallen still auf einen Vorgabewert zurück, driftet das Risiko unbemerkt"* — fail-soft ist fail-silent | Bau, Pflicht |
| **P-3** | ⚠️ `mengen_json` zählt `quantity` **ohne** `staked_quantity` — sechs Werte fehlen. **Nicht repariert**, weil ein Fix `wert_eur`/`index_wert` springen ließe | **Nutzerentscheidung** |
| **P-4** | ⚠️ **Kelly gilt für EINE wiederholte, unabhängige Wette.** Gemessen sind **32 gleichzeitige Positionen**, 78 % investiert, in einem stark korrelierten Markt. Die Einzeltrade-Zahl ist damit nicht ohne Weiteres übertragbar | Messfrage, offen |
| **P-5** | ⚠️ **Bezugsgröße festlegen:** alles / nur Krypto / Anteil. Heute umfasst `wert_eur` **alle Klassen ohne Cash**. Für die Hebelrechnung in Krypto wäre zu klären, ob das Gesamtkapital oder der Krypto-Anteil die richtige Basis ist | **Nutzerentscheidung** |

⚠️ **P-5 ist die Frage aus dem Nutzerhinweis, und sie ist offen.** Die
Daten geben beides her — entschieden ist es nicht.

## ✔ Und SOL ist im Plan, mehrfach

Der Nutzerhinweis stimmt: `Anforderungen_Umbau_28_08.md:79` führt
**„Kern-Krypto | 3 (BTC, ETH, SOL) | spot **und** hebel"**, Zeile 338
**„spot × akkumulation nur wenn dca_erlaubt (BTC/ETH/SOL)"**, Zeile 357
**„BTC, ETH und SOL dürfen beides"**, und
`Ausloeser_und_Begruendungen_27_08.md:36` **„K1 — Kern (BTC, ETH, SOL)"**.

⚠️ **L1 bleibt trotzdem stehen** — im Schalter `asset_dca_settings` ist
SOL nicht gesetzt (Stand der Desktop-Kopie, 19.08.). Ob das am Notebook
anders ist, lässt sich hier nicht prüfen. **Der Plan ist richtig, die
Daten sind zu prüfen.**

---

# ✔ ENTSCHEIDUNGEN 10.09. — die Bezugsgröße und der Hebel

## ✔ P-5 ENTSCHIEDEN: Gesamtkapital ohne Cash

> *„Gesamtkapital ohne Cash als Bezugsgröße"*

Das ist genau `portfolio_wert_historie.wert_eur` — der Wert der
gehaltenen Assets über **alle** Klassen, ohne Cash. **Keine Änderung am
Datenmodell nötig**; die Größe existiert seit dem 08.05.

⚠️ Für den prozentualen Rückschlag bleibt `index_wert` die Basis (Z-3,
Korrektur 07.08.). Zwei Größen, zwei Aufgaben:

    wert_eur     die BEZUGSGROESSE fuer `r x Kapital`   (P-5, heute)
    index_wert   der DRAWDOWN-Massstab fuer Z-3         (07.08.)

## ⚠️⚠️⚠️ UND DIE HARTE AUFLAGE DAZU

> *„wichtig: Änderungen im Portfolio dürfen nicht die Bewertung
> blockieren, schon gar nicht still!"*

**Daraus folgt eine Architekturregel, und sie ist scharf zu trennen:**

| | braucht das Kapital? | was bei fehlendem/geändertem Wert gilt |
|---|---|---|
| **BEWERTUNG** (`potential.rechne`) | **NEIN** | ⚠️ **läuft weiter, immer.** Das Potential kommt aus den Markträngen; das Kapital kommt darin nicht vor |
| **DIMENSIONIERUNG** (`r × Kapital`) | ja | darf sich ändern — **aber laut** |

> **Ein fehlender oder geänderter Portfoliowert darf die Bewertung NIE
> erreichen.** Er darf höchstens die Positionsgröße beeinflussen, und
> auch das nur mit einer sichtbaren Meldung.

⚠️ **Das ist NICHT dasselbe wie beim Marktrang.** Dort gilt: fällt der
Abruf aus, liegt jedes Potential bei 0,000 und Stufe 11 sperrt — weil die
Beiträge selbst fehlen. Beim Portfoliowert fehlt **nichts, was die
Bewertung braucht**. Wer ihn in die Bewertung durchreicht, baut eine
Abhängigkeit, die es fachlich nicht gibt.

**Umsetzungsregel für P-1/P-2:**

    1  Der Lesepfad geht in die DIMENSIONIERUNG, nicht in die Bewertung.
    2  Faellt der Wert aus -> LAUTE Meldung, wie beim Marktrang-Totalausfall
       ("Das ist ein Datenausfall, kein ruhiger Tag").
    3  KEIN stiller Vorgabewert. Fail-soft ist fail-silent.
    4  Eine Pruefung in der Suite haelt offen, dass `potential.rechne`
       den Portfoliowert NICHT liest.

## ✔ P-4 ENTSCHIEDEN: der Hebel gilt dem EINZELNEN Asset

> *„der Markt ist korreliert, das ist ein Fakt. Der Hebel soll auf ein
> einzelnes Asset angewendet werden, wenn die Voraussetzungen passen und
> ein optimales Chance-Risiko-Verhältnis (Wahrscheinlichkeit) gegeben
> ist, dass der Hebel zum Einsatz kommen soll (2–5×)."*

⚠️ **Damit ist die Korrelationsfrage nicht weg, sondern verortet** — und
der Entwurf hat dafür bereits eine Stelle:

| | Aufgabe | Ebene |
|---|---|---|
| **K1** `r(q)` | die Wahrscheinlichkeit erzeugt das Risiko **dieses einen Trades** | Einzeltrade |
| **K3** Aggregat-Deckel | fängt ab, dass 32 gleichzeitige Positionen in einem korrelierten Markt **zusammen** zu viel Risiko tragen | Portfolio |
| **K4** kein Hebeldeckel | `hebel_max = 10` bleibt **Plausibilitätsgrenze**, kein Risikoinstrument | — |

> **Die Korrelation gehört in den Aggregat-Deckel, nicht in eine
> Schrumpfung des Einzeltrade-Kelly.** Wer sie im Einzeltrade
> einpreist, bestraft jeden Trade für ein Portfolio, das er nicht kennt.

⚠️ **Vorbedingung für K3 ist die Positionsführung für Hebel** — und
`handelsauftrag` benennt den Grund: *„Spot und Hebel sind nicht dasselbe
Objekt. Spot ist ein **Bestand**; Hebel ist ein **Trade** mit
Lebenszyklus, Finanzierung und Liquidationspreis. Beide können
gleichzeitig auf demselben Symbol bestehen."*

## ✔ UND DIE FRAGE, DIE SEIT WOCHEN OFFEN WAR, IST ENTSCHIEDEN

> *„OB Hebel ausschließlich aus SPOT zu Hebel entstehen soll oder eine
> eigene Bewertungsgruppe braucht, haben wir schon seit Wochen am Tisch
> — deine bisherigen Aussagen und die Literatur unterscheiden hier nicht,
> also bleibt die dynamische Entscheidung, wann und wie ein Hebel zum
> Einsatz kommt."*

**Entschieden: KEINE eigene Bewertungsgruppe für den Hebel.**

| | |
|---|---|
| **Was gilt** | Eine Bewertung, ein Potential. Der Hebel entsteht **dynamisch** daraus, wenn Chance/Risiko es hergibt |
| **Was damit erledigt ist** | H-2 / N-33 („bekommt die Bewertung eine Instrument-Achse?") — endgültig, als **Entscheidung**, nicht nur als Kategorienbefund |
| **Was daraus folgt** | ⚠️ Die Lage `hebel × einstieg` braucht **keine eigenen Beiträge**. Dass sie die Spot-Beiträge „erbt", ist damit **kein Mangel mehr, sondern der gewollte Zustand** |

⚠️⚠️ **Damit fällt eine Abweichung im SOLL/IST-Abgleich weg** — die
Meldung *„hebel × einstieg erbt die Spot-Beiträge"* war nach dem alten
Stand ein Befund; nach dieser Entscheidung ist sie die Umsetzung.

**Was NICHT wegfällt:** die Zielzone 2–5× wird heute nur von **einer**
Lage erreicht (F-220). Der Hebel entsteht dynamisch — aber er entsteht
fast nie. Das bleibt der Engpass, und er heißt weiterhin: die Bewertung
ist zu schwach.

---

# ⚠️⚠️⚠️ 10.09. — DIE HEBELDIAGNOSE IST KORRIGIERT: zu GROB, nicht zu schwach

> Nutzerfrage 10.09.: *„1. ein ,guter' Hebel kommt selten zum Einsatz —
> OK. 2. erkennen wir überhaupt gute Hebelchancen? Das ist die Frage und
> sollte durch Simulationen bewertet und ggf. kalibriert werden können."*

## Was ich drei Tage lang falsch gesagt habe

Ich habe **F-220** zitiert — *„nur EINE Lage erreicht 2,60×"* — und
daraus *„die Bewertung ist zu schwach"* gemacht.

| | |
|---|---|
| **F-220** | am **06.09. ZURÜCKGEZOGEN** |
| **Kalibrierungsfaktor 19,5 %** | am **05.09. GEFALLEN** (Verfügbarkeits-Artefakt) — und er wird **nirgends im Code angewandt**, die Produktion rechnet unkalibriert |

**Es gilt Befund 2.174-neu (08.09.)**, unkalibriert mit der heutigen
Beitragslage (Kapital 10.000, Einsatz 500, Stop 5 %, halbes Kelly,
CRV 2,0):

```
kein Beitrag                          0,00×
mittlere Lage                         1,02×
                                      ⚠️  hier liegt NICHTS
nur funding bestes                    3,90×   ← Zielzone
bestes funding + mittleres turnover   4,56×   ← Zielzone
nur turnover bestes                   9,45×
beide bestes                         13,35×
```

> **ZWEI Lagen liegen in der Zielzone 2–5×, und die Abstufung ist echt.**

## „Schwach" zerlegt — die Antwort auf beide Nutzerfragen

| | Frage | Stand |
|---|---|---|
| **NIVEAU** | reicht die Quote für 2–5×? | ✔ **ja**, zwei Lagen |
| **AUFLÖSUNG** | trifft sie die Zone *gezielt*? | ⚠️ **nein** — Sprung 1,02 → 3,90 |
| **TRENNSCHÄRFE** | steigt die **reale** Trefferquote mit der Quote? | ⚠️ **nie gemessen** |
| **DECKEL** | 13,35× braucht `hebel_max = 10` | ✔ vorhanden |

**Zu Frage 1** — ✔ bestätigt: von sechs Lagen erzeugen zwei einen
brauchbaren Hebel. **Seltenheit ist kein Mangel**, und ich habe sie
fälschlich als einen dargestellt.

**Zu Frage 2** — ⚠️ die Abstufung ist echt, aber **zu grob**. Ursache
(2.174-grenzen): die Beiträge sind **Fünftel**; fünf Stufen ergeben ein
Raster, das gröber ist als die Zielzone.

> **Wir erkennen „gut" gegen „nicht gut". Wir erkennen nicht „wie gut".**

## ⚠️⚠️ Und damit ordnet sich A1 neu ein

Die eigentliche Frage — *geht ein höherer Hebel mit einer höheren
**realen** Trefferquote einher?* — fragt nach **binären Ausgängen**. Genau
dort ist unser Band viermal zu eng, und die Kontrolle trägt (2.238).

**A1 ist damit keine Nacharbeit, sondern die Voraussetzung** — ohne sie
ist die Frage mit keiner Simulation beantwortbar.

## Zwei Wege für die Auflösung — beide offen, beide simulierbar

    feinere Stufung   mehr als fuenf Stufen je Beitrag
    stetige Form      Regler statt Fuenftel

⚠️ **Vorbehalt aus dem Bestand:** mehrere Beiträge haben sich als
**Schalter** erwiesen, nicht als Regler. Ob die Daten eine feinere
Auflösung überhaupt tragen, ist selbst eine Messfrage.

## ⚠️⚠️⚠️ Die Ursache meiner drei Fehlaussagen von heute

| # | falsch | Quelle | richtig |
|---|---|---|---|
| 1 | „Hebel konzeptionell abgeschlossen" | Memory-Eintrag | er schließt nur die **Instrument-Achse** |
| 2 | „`portfolio_wert_historie` ist LEER" | **veraltete Desktop-Kopie** | läuft seit 08.05., 91 Zeilen |
| 3 | „nur EINE Lage erreicht 2,60×" | Memory-Eintrag | F-220 zurückgezogen |

> **Ein Memory-Eintrag ist ein SCHNAPPSCHUSS vom Tag seiner Entstehung.
> Das Register wird ERZEUGT und ist aktuell. Beide sehen beim Lesen
> gleich verbindlich aus** — deshalb wiederholt sich der Fehler.

**Gebaut dagegen:** Kopfwarnungen in beiden Hebel-Memoryeinträgen, die
Datenstandsprüfung in `soll_ist.py`, und die stehende Vorgabe *„vor jeder
Aussage aus dem Memory im Register gegenprüfen"* (Befund 2.281).

---

# ✔✔✔ 10.09. — N-46 IST GELÖST, und zwar mit dem VORHANDENEN Werkzeug

Der Blocker stand seit dem 05.09.: *„Ein gültiger Nullpunkt für die
LÄNGS-Form … das ist die einzige Frage, die den Weg blockiert."* Die
Begründung lautete, die Tagesmischung tauge dort nicht.

## Gegen bekannte Wahrheit gemessen — 100 Nullwelten je Beharrlichkeit

| Beharrlichkeit | Verschub | Tagesmischung | Soll |
|---|---|---|---|
| **0,61** (wie `funding`) | 0,0 % | **1,0 %** | 2,5 % |
| **0,985** (wie `schnitt`) | 1,0 % | **4,0 %** | 2,5 % |

> ⚠️⚠️ **Beide Nullmodelle arbeiten. N-46s Prämisse ist damit widerlegt** —
> „die Tagesmischung taugt dort nicht" trifft nicht zu.

## Und die Fundquote entscheidet klar

Gepflanzt auf den **Längs**-Rang, 40 Welten je Sprosse:

| gepflanzt | 0,61 Versch. | 0,61 Tagesm. | 0,985 Versch. | 0,985 Tagesm. |
|---|---|---|---|---|
| 0,03 R | 25,0 % | **32,5 %** | 5,0 % | **20,0 %** |
| 0,05 R | 85,0 % | **97,5 %** | 25,0 % | **50,0 %** |
| 0,08 R | 100 % | 100 % | 70,0 % | **90,0 %** |
| 0,12 R | 100 % | 100 % | 97,5 % | 97,5 % |

**Sechs von acht Sprossen besser, zwei gleich, nirgends schlechter.**

⚠️ **Das ist exakt das `null_oben`-Muster vom 09.09.**: das konservativere
Modell hat weniger Fehlalarme und zahlt mit Fundkraft. Dort fiel die
Entscheidung genauso — für das Modell, das die **Sollquote trifft**.

> **Kriterium 4 des Vierfachtests (Regel 3 längs) ist nicht mehr
> blockiert — und damit auch nicht der Weg zu einem dritten Beitrag.**

## ⚠️⚠️⚠️ Der Nebenbefund wiegt schwerer als die Entscheidung: A9

Bei hoher Beharrlichkeit löst die Längs-Achse **erst ab 0,08 R** auf.
**Die echten Kandidaten liegen bei 0,02 bis 0,05 R.**

> **Damit ist N-46as Nebenbefund „kein Kandidat trägt längs" (2.277)
> KEINE Aussage über die Welt, sondern UNTERMACHT** — genau für die
> beharrlichen Größen wie `schnitt`, um die es geht. 2.277 ist abgelöst.

**Als Blocker A9 in den Abgleich aufgenommen**, damit ein „trägt nicht
längs" nicht beim nächsten Mal wieder als Befund gelesen wird.

## ⚠️ Zwei Selbstbefunde

**2.284 — mein Verschub-Bau war nicht nötig.** Ich habe ein Nullmodell
gebaut, um ein Problem zu lösen, das die Messung nicht bestätigt.
Ursache: ich habe N-46s Ausgangsbeobachtung **nie reproduziert**, sondern
auf ihr gebaut. **R-R11 verlangt die Reproduktion vor dem BAU, nicht nur
vor dem Widerruf.**

**2.285 — ein Vorbehalt zur Tagesmischung:** bei hoher Beharrlichkeit
feuert sie mit 4,0 % gegen ein Soll von 2,5 % — das 1,6-fache. Sie
**klammert** das Soll, während der Verschub durchgehend darunter liegt.
Für beharrliche Größen ist ein TRÄGT-Urteil damit etwas großzügiger, als
das Band verspricht.

---

# ✔✔✔ 10.09. — A2 GELÖST: die Akkumulation ist messbar, und `schnitt` trägt

## Der Weg war ein Methodenwechsel, keine Horizontänderung

K-1c scheiterte an der **Blockzahl** (6–10 statt 20), nicht am
Nullpunkt. Bei H90 bräuchten 20 Blöcke 5.400 Handelstage.

> **Ein Permutationstest braucht keine Blöcke**, weil der zirkuläre
> Verschub die Abhängigkeitsstruktur **erhält** statt sie zu
> zerschneiden. Genau deshalb funktioniert er bei H90.

⚠️ **N-46b hat das nicht gelöst** — dort ging es um den Nullpunkt der
Längs-Achse, hier fehlte das **Band**. Zwei verschiedene Probleme.

## Das Ergebnis — 518 Reihen, 400 Verschübe

| Kandidat | Vorsprung | Zufall 5–95 % | p | Symbole | Urteil |
|---|---|---|---|---|---|
| **`schnitt`** | **+0,0470** | [−0,0121 .. +0,0106] | 0,000 | **481** | ⚠️ **TRÄGT** |
| `turnover` | +0,0353 | [−0,0220 .. +0,0245] | 0,005 | **49** | ⚠️ trägt, dünn |
| `funding` | **−0,0230** | [−0,0105 .. +0,0093] | 0,000 | 291 | ⚠️⚠️ **UMGEKEHRT** |
| `oi_aenderung` | **−0,0178** | [−0,0075 .. +0,0076] | 0,000 | 119 | ⚠️⚠️ **UMGEKEHRT** |
| `zufall` ✔ | +0,0015 | [−0,0019 .. +0,0019] | 0,223 | 518 | trägt nicht |

**Kontrollen (R-R11 erfüllt, vor der ersten neuen Aussage):**
TIEFPUNKT +0,4245 gegen 28.08. +0,4242 · WOCHENTAG −0,0005 gegen −0,0008.

## ✔ `schnitt` ist der erste gemessene Beitrag für die Akkumulationslage

+0,0470 auf 481 von 518 Symbolen — **stärker als `UNTER_SMA` am 28.08.**
(+0,0283). Und es passt: 2.155 hält fest, dass `schnitt` und das
Akkumulationsmaß **dieselbe Größe** sind.

## ⚠️⚠️⚠️ Der Befund, der überrascht: zwei Beiträge laufen rückwärts

`funding` und `oi_aenderung` liegen **weit unter** dem Nullband, mit
**p = 0,000**. Ihr „gutes" Fünftel — wenig Funding, wenig OI-Aufbau —
ist für die Akkumulation systematisch der **schlechtere Kauftag**.

> **Das ist kein Nullbefund. Die Richtung ist belegt, nur andersherum.**

⚠️⚠️ Beide sind live als `strategien=("einstieg",)` deklariert und
wirken deshalb **nicht** auf die Akkumulation. **Nach diesem Befund ist
das ein Glück, kein Zufall** — würden sie dort greifen, liefen sie
rückwärts.

## ⚠️ Die Auflösung, eigens bestimmt

**0,0216 in Rangeinheiten.** A9s Grenze (0,08 R) gilt hier **nicht** —
`verbilligung` ist ein Perzentilrang mit Basisrate 0,500, keine
R-Größe. Eine Zahl aus der einen Skala in die andere zu tragen wäre
derselbe Fehler wie beim Kalibrierungsfaktor.

## ⚠️ Drei eigene Fehler, alle vor dem Lauf gefangen

1. **Stille Fehlausrichtung:** die Kauftage wurden über die Tagesliste
   aus `K.baue` gemappt — die beginnt später. Jetzt kommt die
   Datumszuordnung aus derselben Abfrage wie die Kurse.
2. **Symbolabhängiger Verschub:** ich zog den Startpunkt ab — der
   dokumentierte 28.08.-Fehler mit umgekehrtem Vorzeichen.
3. **Zu grobes Urteil:** nur TRÄGT/trägt nicht — `funding` wäre als
   Nullbefund ausgewiesen worden. Jetzt drei Stufen.

## Was daraus folgt

Die Lage `spot × akkumulation` hat zum ersten Mal einen **gemessenen
Beitrag**. ⚠️ Offen bleibt **L1** (SOL fehlt im DCA-Schalter) und die
Frage, ob `schnitt` dort als **Regler oder Schalter** registriert wird —
das ist Schritt 5 (FORM).

---

# 10.09. — DIE NAHT GEBAUT, UND DER VIERFACHTEST IST NICHT ERFÜLLBAR

## ✔ Die fachliche Bewertung (Nutzerauftrag): der Hebel kommt aus dem SPOT-Weg

> Nutzerfrage: *„1. Soll Hebel durch den SPOT-Weg? 2. Wäre eine saubere
> Trennung der Bewertungen technisch und fachlich sinnvoller, auch für
> zukünftige Änderungen?"*

**Zu 1: ja — aber nicht, weil es dieselbe Frage wäre.** Es gibt drei
belegte Unterschiede:

| | Spot | Hebel |
|---|---|---|
| Stop | keiner | ja, beendet den Trade |
| Zielgröße | `bewegung_r`, H20 | `barriere`, binär |
| Dauer | H20 | **2,0 Tage Median** (F-202) |
| Kosten | einmalig | **Finanzierung täglich** |

Entschieden wurde so aus drei Gründen: **①** eine eigene Hebelbewertung
ist heute **nicht messbar** (A1 — das Band ist auf binären Daten viermal
zu eng). **②** Das Aufteilen der Evidenz schwächt beide — zwei Beiträge,
die auf 1,5 % der Anker wirken. **③** `r(q)` → Kelly → Hebel braucht nur
**eine** Quote.

**Zu 2: ja, die Trennung ist sauberer — deshalb wurde die NAHT gebaut,
nicht die Trennung.**

`Beitrag` hat jetzt die vierte Achse `instrumente`, Vorgabe **leer =
alle**. Damit ist eine spätere Trennung eine **Daten**änderung statt
einer Codeänderung an jedem Aufrufer von `vermessen()`.

⚠️ **Der Grund, warum das nötig war:** die Antwort *„gilt für alle
Instrumente"* steckte bis heute in der **Abwesenheit eines Feldes** —
derselbe Fehler, den `assetklassen.hebel_handelbar()` schon einmal
behoben hat (*„eine Eigenschaft des Ablaufs statt des Assets"*).

**Bitgleich nachgewiesen:** Quote `0,37303333333333333` vor und nach dem
Umbau. **Vier Wächter** im Paket „Stufen", darunter einer, der festhält,
dass heute **kein** Beitrag eine Instrumentliste trägt — eine stille
Trennung würde auffallen.

### ✔ Und der Auslöser für die echte Trennung ist prüfbar

> Sobald **A1 behoben** und `barriere` messbar ist: messen, ob ein Beitrag
> auf `barriere` **anders** wirkt als auf `bewegung_r`. Trägt er dort
> anders, bekommt der Hebel seine eigene Bewertung — sonst nicht.

Eine Messfrage mit Datum, kein offener Vorbehalt.

---

## ⚠️⚠️⚠️ Der Vierfachtest ist in seiner Fassung vom 05.09. nicht erfüllbar

| Kandidat | 1 Abdeckung | Wirkung (N-73) | 2 Stabilität | 4 Regel 3 |
|---|---|---|---|---|
| **`schnitt`** | 100 % | ✔ **3 von 3 — robust** | ✔ stabil | ⚠️ untermächtig |
| `schnitt50` | 100 % | 2 von 3 | ✔ stabil | ⚠️ untermächtig |
| `vola` | 100 % | 1 von 3 | ✔ stabil | ⚠️ untermächtig |
| `amihud` | 100 % | 0 von 3 | ✔ stabil | ⚠️ untermächtig |
| `zufall` ✔ | 100 % | 0 von 3 | ✔ | ⚠️ |

**Kriterium 4 liefert bei ALLEN untermächtig — auch bei der Kontrolle.**
Das ist der vorab benannte Ausgang: ein Befund über die **Anlage**, nicht
über die Kandidaten. **A9 ist an echten Daten bestätigt.**

### ⚠️⚠️ Und Kriterium 4 ist FALSCH KONSTRUIERT — nicht auszusetzen, sondern richtig zu messen

Es prüft heute mit einem **Signifikanztest** auf der Längs-Achse, ob eine
Größe eine verkleidete Asset-Eigenschaft ist. Das richtige Maß steht seit
dem 02.09. in **Methodik 2.101** — die **Streuungszerlegung**:

```
zwischen    Varianz der Symbolmittel      → Asset-Eigenschaft
innerhalb   mittlere Varianz je Symbol    → Zeitpunkt-Aussage
Asset-Anteil = zwischen / (zwischen + innerhalb)

geeicht:  fester Wert je Symbol 95,9 %  ·  Zufall 0,1 %
          turnover 52 %  ·  volumenanteil roh 73 %, relativ 1 %
```

> ⚠️⚠️ **Das ist BESCHREIBEND, kein Signifikanztest — und deshalb von A9
> gar nicht betroffen.**

⚠️ Dazu: CLAUDE.md hält fest, dass **Regel 3 den Querschnittsvergleich
nicht verbietet**. Ein Signifikanztest auf der Längs-Achse verlangt mehr,
als die Regel fordert.

### ✔✔ `schnitt` ist der einzige robuste Kandidat — und N-73 ist das Anti-Hin-und-Her-Werkzeug

```
schnitt      3 von 3 Mengen   +0,1830 / +0,1858 / +0,0434   ✔ robust
schnitt50    2 von 3
vola         1 von 3          ← DAS Profil ist das Hin und Her
amihud       0 von 3
```

> **Ein Kandidat, der auf einer Menge trägt und auf zweien nicht, liefert
> je nach Messung „trägt" oder „trägt nicht".** Genau das ist über Wochen
> passiert. `schnitt` hat dieses Profil nicht.

⚠️ **Abgrenzung:** das hier gemessene Kriterium 2 fragt *erste gegen
zweite Hälfte* (N-68). S-7 hat am 07.09. eine **andere** Frage gestellt
(*„trägt er in den Fenstern ab 2022?"*). **Das „stabil" hebt S-7 nicht
auf.**

---

## Die offenen Punkte, die daraus NEU entstehen

| # | Punkt | Art |
|---|---|---|
| **V1** | ⚠️⚠️ **Kriterium 4 nach Methodik 2.101 neu messen** — Streuungszerlegung mit geeichter Skala statt Signifikanztest | Bau + Messung |
| **V2** | ⚠️⚠️ **`funding` und `turnover` durch N-73** — sie sind VOR N-73 auf `frei` registriert und nie über alle zulässigen Mengen geprüft. Sonst zweierlei Maß (N-2) | Messung, **vor** jeder Registrierung |
| **V3** | `volumenanteil` in `K.baue` bauen — er braucht eine **Querschnittsrechnung** (Anteil am Tagesgesamtumsatz), die eine Symbolschleife nicht sehen kann. Der Kandidat mit der besten Abdeckung | Bau |
| **V4** | ⚠️ `amihud` läuft **längs rückwärts** (−0,0445, Band ohne Null). Passt zu 2.166: er misst Ausführbarkeit, nicht Potential | offen, nachrangig |
| **V5** | Entscheidung über `schnitt` als dritten Beitrag — **erst nach V1 und V2**, und sie löst **R-R9** aus | **Nutzerentscheidung** |

## ✔ Was heute ERLEDIGT wurde

- **N-46a/b** — der Längs-Nullpunkt entschieden, N-46 als Blocker gefallen
- **A2/AKKU** — die Akkumulation ist messbar, `schnitt` trägt dort (p 0,000)
- **L2** — `swing` stillgelegt (nicht gelöscht), Kanarienvogel geprüft
- **L5** — korrigiert: der Portfoliowert ist nicht leer, es fehlt ein Lesepfad
- **P-4/P-5** — Bezugsgröße und Korrelationsverortung entschieden
- **Die Naht** — `Beitrag.instrumente`, bitgleich, vier Wächter

---

# ✔✔✔ 10.09. — V1: KRITERIUM 4 IST ERFÜLLBAR, und der Befund trifft den Bestand

## Das Ergebnis — Streuungszerlegung statt Signifikanztest

| Kandidat | roh | Lesart |
|---|---|---|
| `oi_aenderung` | **0,4 %** | ✔ Zeitpunkt |
| `schnitt50` | **6,9 %** | ✔ Zeitpunkt |
| `funding` | **15,7 %** | ✔ Zeitpunkt |
| `vola` | **16,5 %** | ✔ Zeitpunkt |
| **`schnitt`** | **25,4 %** | ✔ überwiegend Zeitpunkt |
| ⚠️ `turnover` | **51,2 %** | **überwiegend ASSET — und er läuft LIVE** |
| ⚠️ `amihud` | **70,7 %** | überwiegend ASSET |
| `zufall` ✔ | 0,1 % | ✔ |

**Skala geeicht:** FEST 99,9 % · ZUFALL 0,1 %, beide Arme auf der Menge
des Kandidaten. **R-R11 erfüllt:** `turnover` roh 51,2 % gegen die
registrierten 52 % aus F-170.

> **Der Deadlock ist aufgelöst.** Kriterium 4 ist mit dem richtigen
> Werkzeug messbar — und die meisten Kandidaten bestehen es **in der
> rohen Form**, ohne jede Umformung.

## ⚠️⚠️⚠️ Und der Befund trifft den BESTAND

`turnover` läuft **live** und ist zu **51,2 %** eine Asset-Eigenschaft —
er sagt zur Hälfte, *welches* Asset, nicht *wann*.

⚠️ Hätte ich nur die Kandidaten gemessen, wäre `turnover` mit 51 %
durchgelaufen, während ein neuer Kandidat mit demselben Wert gefallen
wäre. **Zweierlei Maß — der Fehler von N-2.**

## ⚠️⚠️⚠️ Meine eigene Lösung ist widerlegt — von der eigenen Gegenprüfung

Ich hatte die **relative Form** als Behandlungsvorschlag geführt, weil sie
alle Kandidaten unter 1,5 % bringt. Auf Kunstdaten mit **eingestelltem**
Asset-Anteil:

```
gebaut 10 % Asset  →  roh  7,6 %  →  relativ 0,0 %
gebaut 50 % Asset  →  roh 47,1 %  →  relativ 0,0 %
gebaut 90 % Asset  →  roh 88,9 %  →  relativ 0,0 %
```

**Die Standardisierung entfernt das Symbolmittel per Konstruktion.** Sie
senkt jede Größe auf null und beweist nichts.

⚠️ **Was daraus folgt, ist kein Nullbefund:** die relative Form bleibt ein
möglicher **Umbau** — aber der Nachweis muss dann über die **Wirkung** der
umgeformten Größe laufen. Beim Volumenanteil war genau das der Punkt:
relative Form **1,4 % Asset-Anteil UND +0,0231 R Wirkung**. Beides.

## ✔✔ `schnitt` steht jetzt bei drei von vier Kriterien

| | |
|---|---|
| **1 Abdeckung** | ✔ 100 % (536 von 536) |
| **2 Stabilität** | ✔ stabil (N-68-Form) |
| **4 Regel 3** | ✔ **25,4 % — überwiegend Zeitpunkt, roh** |
| **3 Unabhängig** | ⚠️ **steht noch aus** |

Dazu: der **einzige robuste** Kandidat über alle Mengen (3 von 3) und der
**erste gemessene Beitrag der Akkumulationslage** (+0,0470, p 0,000).

## Die offenen Punkte, aktualisiert

| # | Punkt | Stand |
|---|---|---|
| **V1** | Kriterium 4 nach 2.101 | ✔ **erledigt** — erfüllbar, `schnitt` besteht |
| **V2** | `funding`/`turnover` durch N-73 | offen, **vor** jeder Registrierung |
| **V3** | `volumenanteil` bauen | offen |
| **V4** | `amihud` längs rückwärts | offen, nachrangig |
| **V5** | Entscheidung über `schnitt` | offen — braucht V2 und Kriterium 3 |
| **V6** | ⚠️ **NEU: `turnover`s Asset-Anteil 51,2 %** — kein Grund zum Abschalten, aber ein offener Punkt am Bestand. Zu klären, ob eine andere FORM denselben Beitrag mit weniger Asset-Anteil **und erhaltener Wirkung** liefert | **offen** |
| **V7** | ⚠️ **NEU: Kriterium 3** (unabhängig von `funding`) — bei keinem Kandidaten gemessen | **offen** |

---

# 10.09. — V7/KRITERIUM 3: ein gedecktes Urteil, und es betrifft den Bestand

| Kandidat | ohne | echt | GEMISCHT | Urteil |
|---|---|---|---|---|
| **`turnover`** | +0,0639 ✔ | **2 von 5** | **0 von 5** | ✔ **unabhängig von `funding`** |
| `oi_aenderung` | +0,0126 ✔ | 2 von 5 | 3 von 5 | — ein Fach, Auflösungsgrenze |
| `vola` | +0,0325 ✔ | 0 von 5 | 0 von 5 | ⚠️ die **Schichtung** kostet |
| `schnitt` | +0,0314 | 2 von 5 | 0 von 5 | — auf `frei` = Marktfrage |
| `schnitt50` | +0,0097 | 2 von 5 | 1 von 5 | — dito |
| `zufall` ✔ | +0,0043 | 0 von 5 | 0 von 5 | ✔ Kontrolle stumm |

## ✔ `turnover` ist unabhängig von `funding` — erstmals unter der Norm

Zwei Fächer Unterschied (2 echt gegen 0 gemischt), über der Auflösung.
**Damit ist die Registrierungsaussage *„zu 92 % additiv zu Funding"*
erstmals unter dem Messstandard bestätigt.**

⚠️ Und die **Gegenkontrolle** ist der Grund, warum das Urteil trägt:
dieselbe Schichtung mit **gemischtem** Funding — gleiche Fächergröße,
keine Information. Ohne diesen Arm wäre jedes „trägt nicht mehr" wertlos.

## ⚠️⚠️ Für die Kandidaten ist Kriterium 3 nicht entscheidbar — aus drei verschiedenen Gründen

| | Grund |
|---|---|
| `vola` | trägt ohne Schichtung, aber in **0 von 5 Fächern — echt wie gemischt**. Die **Schichtung** kostet, kein Redundanzbefund |
| `schnitt`, `schnitt50` | tragen auf `frei` ohnehin nicht — das ist die **Marktfrage**, nicht ihre Beitragsmenge |
| `oi_aenderung` | 2 gegen 3 Fächer — **Auflösungsgrenze** |

⚠️ **Dieselbe Struktur wie bei Kriterium 4 vor V1 — aber nicht dieselbe
Ursache.** Dort war das *Werkzeug* falsch. Hier ist es richtig, es fehlt
die **Macht**: Schichtung × schmale Menge lässt zu wenige Anker. Ein
Dimensionierungsproblem, kein Konstruktionsfehler.

## ➔ Der Lösungsweg — V8: zwei Schichten statt fünf

> Nutzervorgabe: *„Kein Beitrag fällt ohne Grund, und wenn doch, müssen
> wir eine Lösung suchen."*

```
5 Fächer  →  30 Symbole je Tag
2 Fächer  →  75 Symbole je Tag
2 Fächer auf der 20-%-Beitragsmenge  →  ~25 je Tag  (Mindestquerschnitt 12)
```

**Das halbiert den Machtverlust UND erlaubt, die Kandidaten auf ihrer
Beitragsmenge zu messen statt auf `frei`** — beide Gründe aus 2.303
zugleich adressiert.

## ⚠️ Zwei eigene Fehler in diesem Lauf

**① Überdeutung, vom Ergebnis gefangen.** Der erste Lauf las
`oi_aenderung`s „2 gegen 3 Fünftel" als *„`funding` erklärt einen Teil
mit"*. Bei fünf Fächern ist **ein Fach die feinste unterscheidbare
Einheit**. Dieselbe Überdeutung wie beim Gleichstand in N-46b — dort hat
der Vorabtest sie gefangen, hier erst das Ergebnis.

**② Eine stille Verengung, vom Nutzer gefangen.** Ich hatte `schnitt50`
aus **Laufzeitgründen** herausgenommen. Sachlich steht er gut da: 100 %
Abdeckung, **6,9 % Asset-Anteil** (zweitbester Wert), stabil, und laut
2.222 die **einzige monotone Form** — genau das zählt beim Schritt FORM.
Nachgemessen, dasselbe Bild wie `schnitt`. ⚠️ **Die Kürzung war trotzdem
falsch — sie im Skriptkopf zu vermerken ist nicht dasselbe wie sie zu
begründen.**

---

# ⚠️⚠️⚠️ 10.09. — V8 WIDERLEGT MEINEN EIGENEN LÖSUNGSWEG

| Kandidat | ohne | echt | GEMISCHT | Urteil |
|---|---|---|---|---|
| `schnitt` | +0,1858 ✔ | 1 von 2 | 1 von 2 | — kein Unterschied |
| `schnitt50` | +0,0698 ✔ | 1 von 2 | 0 von 2 | — ein Fach |
| `vola` | +0,1332 ✔ | 1 von 2 | 0 von 2 | — ein Fach |
| `turnover` | +0,0639 ✔ | **2 von 2** | 1 von 2 | — ein Fach |
| `oi_aenderung` | +0,0126 ✔ | 2 von 2 | 2 von 2 | — kein Unterschied |
| `zufall` ✔ | +0,0163 | 0 von 2 | 0 von 2 | Vorfrage nicht bestanden |

## Mit zwei Fächern ist KEIN Urteil gedeckt — mit fünf war es eines

`turnover` hatte bei fünf Fächern **2 gegen 0**. Dieselben Daten liefern
bei zwei Fächern **2 gegen 1** — und das ist nur *ein* Fach Unterschied.

> ⚠️⚠️ **Nicht die Macht war der Engpass, sondern die ZÄHLMETRIK.**
> Weniger Fächer geben mehr Anker je Fach, aber die Zählung hat dann nur
> noch drei mögliche Werte (0, 1, 2). Meine Annahme in 2.307 war falsch.

## ✔ Was V8 trotzdem gelöst hat: die Vorfrage

Auf der **20-%-Menge** tragen `schnitt` (+0,1858), `schnitt50` (+0,0698)
und `vola` (+0,1332) **ohne Schichtung** — auf `frei` taten sie das
nicht. Der Mengenvorbehalt aus 2.306 ist ausgeräumt, und die Messung ist
überhaupt erst aussagekräftig geworden.

## ⚠️⚠️⚠️ Und das richtige Werkzeug lag die ganze Zeit vor

`messnorm_rand.pruefe_geschichtet` misst die Schichtung als **einen
Befund mit einem Band** — Nullpunkt, Trennschärfe und eine **eingebaute
Positivkontrolle** (`pflanze`), die dem Original fehlt:

```
marke=None   Median-Differenz wie im Original (MITTELWERT-Maßstab)
marke=2.0    Differenz der Randanteile        (RAND-Maßstab)
```

⚠️ **Ich habe es verworfen, weil der eine Aufrufer, den ich ansah,
`marke=2.0` übergab** — ich habe das Argument eines Aufrufers für die
Natur des Werkzeugs gehalten.

## ➔ V9 — der richtige Weg für Kriterium 3

**Eine stetige Kennzahl mit einem Band schlägt eine Zählung mit drei bis
sechs möglichen Werten** — genau der Unterschied, an dem V7 und V8
gescheitert sind. Die Gegenkontrolle (gemischtes Funding) bleibt; sie ist
von der Kennzahl unabhängig.

## ✔ Ein Kanarienvogel, der in V8 gegriffen hätte

`traegt_wirklich()` liest das **Urteil** statt der Eigenschaft `traegt`.
Bei zwei Fächern auf einer 20-%-Menge ist die Blockzahl knapp, und
`Befund.traegt` weiß nichts davon — Fehler 4 vom 08.09., an dem
`k1c_lagen_eigene_zielgroesse` schon einmal gescheitert ist.

---

# ✔✔✔ 10.09. — V2/N-73 AUF DEM BESTAND: die Zweierlei-Maß-Sorge ist beantwortet

| Beitrag | zulässige Beitragsmengen | trägt auf | |
|---|---|---|---|
| **`schnitt`** *(Kandidat)* | 10 %, 20 %, 50 % | **3 von 3** | ✔ |
| `funding` *(live)* | 10 %, 20 %, 50 % | **2 von 3** | ⚠️ nicht bei 20 % |
| `turnover` *(live)* | **nur 50 %** | 1 von 1 | ✔ aber dünn |
| `oi_aenderung` *(live)* | 20 %, 50 % | 2 von 2 | ✔ |
| `zufall` ✔ | 10, 20, 50 % | 0 von 3 | ✔ Kontrolle |

## ⚠️⚠️⚠️ `funding` besteht N-73 nicht — und das dreht die Frage um

Ein **live laufender** Beitrag trägt auf 2 von 3 Mengen (bei 20 % „nicht
trennbar"). Dasselbe Profil wie `schnitt50`.

> **`schnitt` besteht N-73 besser als jeder registrierte Beitrag.** Ihn
> an dieser Hürde zu messen ist **nicht unfair** — er nimmt sie sauberer
> als der Bestand.

⚠️ Die Hürde bleibt damit gültig. Sie ist für den **Bestand** neu zu
begründen, nicht für den Kandidaten zu senken.

## ⚠️⚠️ Eine Lesart, die der Bruch versteckt

`turnover` besteht mit **„1 von 1"** — aber nur, weil bei seiner
Abdeckung (66 von 536) **überhaupt nur eine** Beitragsmenge zulässig ist.

> **„1 von 1" ist eine SCHWÄCHERE Aussage als „3 von 3".** Der N-73-Bruch
> hängt daran, wie viele Mengen die Datenlage trägt — wer nur den Bruch
> liest, hält einen dünnen Beitrag für so robust wie einen breiten.

## ➔ Was daraus folgt — und es ist KEIN Abschalten

`funding` trägt auf 10 % und 50 %, nur bei 20 % nicht. Nach der
Nutzervorgabe fällt kein Beitrag ohne Grund, und ein Nichttragen auf
**einer von drei** Mengen ist ein Grund zum Nachsehen, keiner zum
Entfernen.

**V10 (offen):** hat die 20-%-Menge bei `funding` eine Besonderheit? Seine
Abdeckung ist 300 von 536 — die Momentum-Auswahl und die
Funding-Verfügbarkeit könnten sich überschneiden. Oder es ist Rauschen.

---

# ✔✔✔ 10.09. — V9: KRITERIUM 3 IST BEANTWORTET, und `schnitt` hat alle vier

| Kandidat | echt | GEMISCHT | Trennschärfe | Urteil |
|---|---|---|---|---|
| **`schnitt`** | +0,0388 | +0,0361 | 0,05 R | ✔ unabhängig |
| `schnitt50` | +0,0300 | +0,0311 | 0,05 R | ✔ unabhängig |
| `turnover` | +0,0442 | +0,0514 | 0,05 R | ✔ unabhängig |
| `oi_aenderung` | +0,0135 | +0,0128 | 0,05 R | ✔ unabhängig |
| `vola` | +0,0359 | +0,0348 | 0,05 R | ✔ unabhängig, aber nicht mehr trennbar |
| `zufall` ✔ | +0,0018 | +0,0005 | 0,05 R | trägt ungeschichtet nicht |

## Die Lesart gibt das Werkzeug selbst vor

> *„Bleibt es auch dort beim selben Wert, ist es die **Schichtung** — der
> Partner erklärt **nichts**."*
> — `pruefe_n1_schichtung_gegen_partner`

Und **„der Partner erklärt nichts" ist Unabhängigkeit** — genau das, was
Kriterium 3 fragt.

⚠️⚠️ `schnitt` fällt durch die Schichtung von **+0,1858 auf +0,0388** —
mit **bedeutungslosem** Partner auf **+0,0361**. Der Abfall ist ein
**Artefakt der Schichtung**, keine Redundanz.

## ✔✔ Warum V9 gelingt, wo V7 und V8 scheiterten

**Die Trennschärfe ist beziffert: 0,05 R in jeder Zeile.** Bei den
Zählmetriken gab es keine — ein „trägt nicht" war dort nie von
Untermacht zu unterscheiden. Eine **stetige Kennzahl mit Band und
Leiter** schlägt eine Zählung mit drei bis sechs möglichen Werten.

## ⚠️⚠️ Drei Anläufe, drei eigene Fehler — jeder von einer anderen Instanz gefangen

| | Fehler | gefangen von |
|---|---|---|
| **V7** | Zählmetrik zu grob; Kontrolle bekam „unabhängig" | dem **Vorabtest** |
| **V8** | mein Lösungsweg „weniger Fächer" machte die Metrik **gröber** | dem **Ergebnis** |
| **V9** | Werkzeug wegen eines Aufrufparameters verworfen; Vorfrage aus V7 nicht mitgenommen | dem **Ergebnis** (`zufall` bekam wieder ein positives Urteil) |

---

# ✔✔✔ `schnitt` HAT ALLE VIER KRITERIEN

```
1 ABDECKUNG    ✔ 100 %  (536 von 536)
2 STABILITÄT   ✔ stabil (N-68-Form)
3 UNABHÄNGIG   ✔ funding erklärt nichts        (V9)
4 REGEL 3      ✔ 25,4 % Asset-Anteil, roh      (V1)

N-73           ✔ 3 von 3 Mengen — BESSER als `funding` (2 von 3)
Akkumulation   ✔ trägt dort ebenfalls (+0,0470, p 0,000)
```

⚠️ **Die Registrierung ist eine NUTZERENTSCHEIDUNG und löst R-R9 aus** —
die Schwelle 0,080 wäre neu zu kalibrieren.

⚠️ Und bei `vola` bleibt: geschichtet nicht mehr trennbar (echter
Nullbefund, Trennschärfe 0,05 R), dazu N-73 mit 1 von 3. Er bleibt der
wackligste der Kandidaten.

---

# ⚠️⚠️⚠️ 10.09. — S-7 GEKLÄRT, und dabei fiel Kriterium 2 auf

## Zuerst: die Reproduktion (R-R11)

S-7 stammt vom 07.09., **vor** dem Messstandard. Reproduziert wurde er auf
**drei** Wegen, bevor irgendetwas gedeutet wurde:

| | S-7 (07.09.) | jetzt | |
|---|---|---|---|
| Wirkung `schnitt` ganz | +0,1623 | +0,1858 | 1,14× ✔ |
| Wirkung `schnitt` ab 2022 | +0,0414 | +0,0589 | 1,42× ✔ |
| Jahr 2019 · 2022 · 2023 | +0,45 · +0,019 · −0,050 | +0,52 · +0,022 · −0,047 | ✔ |
| Hälftenunterschied 20 % | +0,2238 | +0,1973 | ✔ |
| Hälftenunterschied 10 % | −0,0647 | −0,0805 | ✔ **auch die Drehung** |

## ⚠️⚠️ S-7 ist bestätigt — aber nur in seinem eigenen Wortlaut

> *„Es ist **unentschieden**."* — S-7, 07.09.

Ab 2022 lautet das Urteil auf **allen drei** Mengen **NICHT TRENNBAR**,
nicht „trägt nicht". Der Unterschied ist der Kern der Norm:

| | |
|---|---|
| `zufall` | bekommt in **jeder** Zeile ein „TRÄGT NICHT bis X" — **eine Aussage** |
| `schnitt` | bekommt ab 2022 dreimal „keine Aussage" |

⚠️ **Und S-7s Spalte „ab 2024" war nie gültig:** 962 Tage = **16 Blöcke**,
gefordert sind 20. Unter dem heutigen Standard ist das KEIN BEFUND.

## Der Mechanismus: die Bandbreite, nicht ein fehlender Effekt

Bei **gleicher** Blockzahl (25/25, ab 2022, 10 %):

```
schnitt   Wirkung +0,1221   Band 0,383   Signal/Band 0,32
funding   Wirkung +0,0542   Band 0,063   Signal/Band 0,86
```

> **`schnitt` hat die größere Wirkung und den schlechteren Schätzer.**

✖ Meine Erklärung „klumpig" ist **widerlegt** — von der eigenen Kontrolle:
das Kriterium gab auch `zufall` „klumpig", misst also das Jahresfenster.
Der Jahresverlauf zeigt statt Streuen einen **Niveauabfall** (2019–21 bei
+0,36…+0,57, ab 2022 −0,05…+0,17, `zufall` dort zehnmal kleiner).

---

# ⚠️⚠️⚠️ Und dabei fiel ein Fehler im Vierfachtest auf

`n102_vierfachtest.py:135` entschied Kriterium 2 so:

```python
"stabil": bool(d["unten"] <= 0.0 <= d["oben"])
```

**„Stabil" hieß dort nur: das Band schließt die Null ein.** Ein
Nicht-Verwerfen, als Haken ausgegeben — mit einer Richtung, die genau den
falschen Kandidaten belohnt:

> **Je breiter das Band, desto sicherer das ✔.**

⚠️ **Zweiter Fehler, gleiche Stelle:** N-73 war bei Kriterium 2 nie
angewandt. Im selben `main()`, zehn Zeilen auseinander, lief Kriterium 1
über **alle** zulässigen Mengen und Kriterium 2 über **eine**.

## Richtig gemessen — über alle Mengen, mit Trennschärfe

| Kandidat | 10 % | 20 % | 50 % | Kriterium 2 |
|---|---|---|---|---|
| **`schnitt`** | stabil bis 0,40 | **+0,1973 [+0,0717 .. +0,3892]** | stabil bis 0,10 | ✖ **FÄLLT** |
| `schnitt50` | stabil bis 0,20 | stabil bis 0,20 | stabil bis 0,05 | ✔ auf allen drei |
| `funding` | stabil bis 0,10 | stabil bis 0,10 | stabil bis 0,05 | ✔ |
| `oi_aenderung` | — | stabil bis 0,05 | stabil bis 0,02 | ✔ |
| `turnover` | — | — | stabil bis 0,10 | ✔ |
| `vola` | stabil bis 0,40 | **+0,2039 [+0,0760 .. +0,3912]** | stabil bis 0,10 | ✖ **FÄLLT** |
| `zufall` ✔ | stabil bis 0,05 | stabil bis 0,05 | stabil bis 0,02 | ✔ Kontrolle hält |

⚠️ **Bei `schnitt` ist es kein „nicht trennbar", sondern ein
NACHGEWIESENER Unterschied** — das Band schließt die Null aus, 20/20
Blöcke.

---

# ⚠️⚠️⚠️ 2.319 IST WIDERRUFEN — `schnitt` hat DREI Kriterien, nicht vier

```
1 ABDECKUNG    ✔ 100 %  (536 von 536)
2 STABILITÄT   ✖ FÄLLT — Unterschied nachgewiesen (20 %)
3 UNABHÄNGIG   ✔ funding erklärt nichts        (V9)
4 REGEL 3      ✔ 25,4 % Asset-Anteil, roh      (V1)
```

⚠️ **Der Widerruf ist zulässig, weil vorher reproduziert wurde** — dreifach.
R-R11 ist erfüllt.

## ✔✔ Die Lösung steht in derselben Tafel: `schnitt50`

> *„Kein Beitrag darf einfach fallen, konkrete Begründung erforderlich und
> ggf. Lösung suchen."* — Nutzervorgabe

Die Begründung steht oben. Die Lösung ist die **50er-Form** — auf allen
drei Mengen stabil, nach 2.222 die einzige **monotone** Form, und vom
Nutzer am 09.09. selbst zurückgeholt (*„Warum hast du schnitt50 einfach
herausgenommen?"*). ⚠️ **Bei ihm zu prüfen bleiben Kriterium 1 und N-73.**

## ✔✔ Kein laufender Beitrag ist betroffen

`funding`, `oi_aenderung` und `turnover` sind auf **allen** ihren
zulässigen Mengen stabil — mit Aussage, nicht mit „nicht trennbar". Dieser
Lauf ändert nichts am Betrieb. **Er verhindert eine Registrierung, die
sonst auf einem fehlerhaften Kriterium beruht hätte.**

## ⚠️ Offen daraus

| | |
|---|---|
| **V11** | `schnitt50` gegen Kriterium 1 und N-73 — der Ersatzweg |
| **V12** | `vola` und `schnitt` fallen fast mit derselben Zahl (+0,2039 / +0,1973). Gemeinsamer geometrischer Anteil? ⚠️ Hypothese, nicht gemessen |

---

# ⚠️⚠️⚠️ 11.09. — V11: kein dritter Beitrag, und 2.325 ist zu berichtigen

## `schnitt50` besteht N-73 nicht

| Menge | Wirkung | Band | Urteil |
|---|---|---|---|
| 10 % | +0,0846 | [+0,0172 .. +0,1491] | **TRÄGT** |
| 20 % | +0,0698 | [+0,0168 .. +0,1457] | **TRÄGT** |
| 50 % | +0,0156 | [−0,0217 .. +0,0740] | **TRÄGT NICHT bis 0,0213 R** |

| | |
|---|---|
| **Kriterium 1** | ✔ 536 Symbole = **100 %**, 251,6 Anker/Tag |
| **N-73** | ✖ **2 von 3** — schwächer als `schnitt` (3 von 3) |

⚠️ Bei 50 % ist es **kein** „nicht trennbar", sondern eine **echte
Aussage**. Die Messung konnte dort etwas finden und hat nichts gefunden.

✔ **Und der Widerspruch im Bestand ist aufgelöst:** 2.187 („abgelehnt auf
ALLEN Mengen") gegen 2.219 („widerspricht sich") — **2.219 hatte recht.**

## ⚠️⚠️ Teil C: ein Kandidat ohne Wirkung ist trivial stabil

```
Kandidat   Menge    Wirkung   Haelften  Anteil   Urteil
schnitt    20%      +0.1858   +0.1973    1.06    NICHT STABIL
funding    20%      +0.0582   +0.0520    0.89    STABIL BIS 0.20
schnitt50  20%      +0.0698   +0.0560    0.80    STABIL BIS 0.20
```

**Alle drei bewegen sich um 80–106 % ihrer eigenen Wirkung.** Der einzige
Unterschied ist der **Betrag**. Damit trennt Kriterium 2 nicht stabil von
instabil, sondern **groß von klein** — und `funding` läuft live.

---

# ⚠️⚠️⚠️ Der Auswahl-Test — und damit fällt die Zuschreibung aus 2.325

`entzerrte_reihe` hat seit dem 09.09. einen Parameter **`auswahl_saat`**,
gebaut für genau diese Frage. **Ich hatte ihn am 10.09. nicht gesetzt.**

> *„Mit `auswahl_saat` wird je Tag gleich viel gewählt, aber **zufällig**.
> Trägt die Instabilität dann nicht mehr, ist sie eine Eigenschaft der
> **Auswahl** und nicht von `schnitt`."*

| `schnitt`, 20 % | Hälftenunterschied | Trennschärfe |
|---|---|---|
| **Momentum-Auswahl** | **+0,1973** [+0,0717 .. +0,3892] | 0,20 |
| Zufallsauswahl, 3 Saaten | **+0,0380 / +0,0264 / +0,0310** | **0,05** |

⚠️⚠️ **Faktor 6 — und die naheliegende Gegenerklärung ist ausgeschlossen:**
unter Zufallsauswahl ist der Test **viermal schärfer**, nicht schwächer.
Ein Nullbefund bei höherer Auflösung.

⚠️ **Und unter demselben schärferen Test kippt ausgerechnet `funding`** —
1 von 3 Saaten: +0,0417 [+0,0036 .. +0,0785], Band schließt die Null aus.

## ⚠️ Was das NICHT heißt

**`schnitt` ist nicht rehabilitiert.** Der Vierfachtest ist auf der
**selektierten** Menge definiert (F-212) — dort fällt er an Kriterium 2,
und **2.319 bleibt abgelöst**. Was fällt, ist die *Zuschreibung*: es ist
nicht seine Eigenschaft, sondern die der Kollinearität.

## ⚠️⚠️⚠️ Der eigentliche Einwand ist ein anderer — und ein stärkerer

> `schnitt` korreliert mit **Spearman +0,704** mit dem 250-Tage-Momentum
> (2.158-redundanz), und seine Wirkung ist **zu vier Fünfteln ein
> Auswahl-Artefakt** (+0,1858 auf der Momentummenge → +0,0366 auf
> Zufallsmengen, 2.222).

**Ein Beitrag, der die bereits getroffene Auswahl wiederholt, bringt der
Kette wenig Neues** — und dieser Grund ist von Kriterium 2 völlig
unabhängig.

---

# ⚠️⚠️ BILANZ: es gibt keinen dritten Beitrag

| Kandidat | woran es liegt |
|---|---|
| `schnitt` | bildet zu 4/5 die **Auswahl** nach (2.335) |
| `schnitt50` | besteht **N-73 nicht** (2 von 3) |
| `vola` | fällt an Kriterium 2 **und** N-73 mit 1 von 3 |

Das deckt sich mit dem früheren Befund, dass die **Kursreihe als Quelle
erschöpft** ist (2.168-erschöpft): ein weiterer Beitrag braucht eine
**neue Quelle**.

## ⚠️ Zwei eigene Fehler, die dazugehören

| | |
|---|---|
| **Parameter übersehen** | `auswahl_saat` stand seit 09.09. im Code, samt Testvorschrift im Docstring. **Zweiter Fall dieser Art in zwei Tagen** — am 10.09. dasselbe bei V9 |
| **Falsch zitiert** | „`schnitt50` ist nach 2.222 die einzige monotone Form" — 2.222 sagt das nicht. Die Behauptung stammt aus `Anforderungen_Umbau_28_08.md` (O4/N2), gilt nur **längs**, ist vorstandardlich, N2 ist offen — und im Hebelzusammenhang führt die Fakten-Entscheidungsmappe `schnitt50` als **nicht monoton** |

---

# 📋 11.09. — DER KRYPTO-STAND JE STRATEGIE (Nutzerauftrag)

> *„gib mir für Krypto nach Strategie den aktuellen Stand ob und wie der
> Umbau erfolgen kann im Vergleich zum Plan und was das für die
> Produktivsetzung bedeutet"*

**Alles unten ist aus dem laufenden Code gelesen**, nicht aus dem Plan
erinnert — `agent/wahrscheinlichkeit.BEITRAEGE`, `agent/assetklassen.py`,
`agent/handelsauftrag.ERLAUBTE_PAARE`, `agent/rollen_lauf.py`.

⚠️ **Vorbehalt:** die Betriebsdatenbank am Desktop ist auf Stand
**19.08.** Jede Aussage über den *laufenden* Betrieb (Schalterstände,
Mailaufkommen, offene Positionen) ist am **Notebook** zu prüfen.

## Die fünf Lagen, die es in Krypto überhaupt gibt

| Instrument | Strategie | wer bekommt sie |
|---|---|---|
| `spot` | `einstieg` | **alle** Krypto-Werte — der Grundfall |
| `spot` | `akkumulation` | nur mit `asset_dca_settings.dca_erlaubt` |
| `hebel` | `einstieg` | nur mit `asset_hebel_settings.hebel_pruefung_erlaubt` |
| `hebel` | `swing` | ⛔ im Code übersprungen (Nutzerentscheidung 31.08.) |
| `absicherung` | `einstieg` | in Krypto **keine** (nur 2 Hedge-Positionen, nicht Krypto) |

## ⚠️⚠️ Was live PUNKTE gibt — zwei von acht

Von den acht registrierten Beiträgen haben nur **zwei** `zustand="traegt"`
und eine Stufentabelle:

```
Funding-Rang im Markt    (0,82 · 1,30 · 0,12 · −0,54 · −1,70)   strategien=('einstieg',)
Turnover-Rang im Markt   (3,15 · 0,83 · 0,22 · −1,79 · −2,40)   strategien=('einstieg',)
```

Die anderen sechs stehen auf `null` / `nie` / `enthalten` mit **0,0
Punkten** — darunter `Abstand zum eigenen 200-Tage-Schnitt` (`schnitt`).
**Er gibt live keine Punkte**, er erscheint nur als Merkmal im Text.

Dazu die **OI-Sperre** in `rollen_lauf.py`: greift nur bei
`strategie == "einstieg"` **und** nur ohne Bestand — beides gemessen
begründet.

---

## 1 · `spot` / `einstieg` — der einzige vollständige Weg

| | |
|---|---|
| **SOLL** | Bewertung aus tragenden Beiträgen, Schwelle, Sperren |
| **IST** | ✔ 2 tragende Beiträge · ✔ OI-Sperre · ✔ Schwelle 0,080 |
| **Lücke** | **keine strukturelle** |

⚠️ **Aber zwei Befunde über den Bestand, die in die Entscheidung gehören:**

- **V2 (2.312):** `funding` besteht **N-73 nicht** — 2 von 3 Mengen
- **V11 (2.334):** `funding` kippt unter dem schärferen Stabilitätstest
  in **1 von 3 Saaten**

**Beides ist kein Abschaltgrund** — aber es heißt, dass der Bestand
dieselbe Hürde nicht nimmt, an der Kandidaten scheitern.

➔ **Produktivfähig, wenn akzeptiert wird, dass es bei zwei Beiträgen
bleibt.**

---

## 2 · `spot` / `akkumulation` — messbar, aber nicht verdrahtet

⚠️⚠️ **Hier muss ich mich korrigieren.** Mein Satz von heute Vormittag
*„es gibt keinen dritten Beitrag"* galt der **Einstiegs**-Bewertung. Für
die Akkumulation sieht es anders aus.

| | |
|---|---|
| **SOLL** | eigene Bewertung für den Nachkauf — kein Stop, kein Trailing |
| **IST** | ⛔ **null** Beiträge. `funding` und `turnover` sind auf `einstieg` beschränkt — **zu Recht**: die Messung ankert auf einem Einstieg, über den Nachkauf sagt sie nichts |
| **Gemessen** | ✔ `schnitt` trägt: **+0,0470**, Nullband [−0,0121 .. +0,0106], **p 0,000**, 481 von 518 Symbolen, Kaufquote 19,3 % |

⚠️ **Und das Auswahl-Artefakt-Argument aus 2.335 trifft ihn hier NICHT:**
2.286 lief auf der **freien** Messmenge V1 (518 Reihen, H90,
`verbilligung`, Permutationstest) — nicht auf der Momentum-20-%-Menge.
Die zwei Befunde sind auf verschiedenen Mengen und beißen sich nicht.

**Offen:**
1. **FORM** — Regler oder Schalter (Schritt 13 im Ablauf)
2. **Registrierung** — löst R-R9 aus, aber **nur für diese Lage**
3. **L1** — `dca_erlaubt` führt am Desktop nur **BTC, ETH**; die
   Nutzervorgabe nennt **BTC, ETH, SOL**. ⚠️ Am Notebook zu prüfen

➔ **Ein überschaubarer Schritt von der Produktivsetzung entfernt.**

---

## 3 · `hebel` / `einstieg` — Signale ja, Hebelhöhe nein

| | |
|---|---|
| **SOLL** | Hebel **dynamisch** aus der Wahrscheinlichkeit, Zielzone **2–5×** |
| **IST** | erbt `funding` + `turnover` aus dem Spot-Weg (Entscheidung 10.09., bewusst) |
| **Blockiert** | **A9** · **A1** · **P-1** |

```
A9   die AUFLOESUNG: die Abstufung springt 1,02x -> 3,90x, weil die
     Beitraege Fuenftel sind (2.174-grenzen)
A1   das Band liegt auf binaeren Daten - blockiert die Trennschaerfe-Frage
P-1  die Rollen-Kette liest den Portfoliowert nicht
```

⚠️ **Der Engpass ist die Auflösung, nicht die Stärke** — zwei Lagen
erreichen die Zielzone, aber dazwischen gibt es nichts. Ein Hebel, der
von 1,02× auf 3,90× springt, ist keine Abstufung.

➔ **Signale sind bewertbar, die Hebelhöhe ist es nicht.** Der lange Weg.

---

## 4 · `hebel` / `swing` — stillgelegt, kein Handlungsbedarf

`assetklassen.py` überspringt sie an **einer** Stelle mit Begründung,
`messnorm.LAGEN_STILLGELEGT` führt sie mit Kanarienvogel. Nutzerhinweis
10.09.: *„Swing ist keine genutzte Strategie mehr."*

## 5 · `absicherung` — zurückgestellt

Vorgabe **KRYPTO-ZUERST** (10.09.). In Krypto gibt es keine
Absicherungsposition; die zwei Hedge-Positionen sind nicht Krypto.

---

# Was das für die Produktivsetzung heißt

| Stufe | was nötig ist | Aufwand |
|---|---|---|
| **A** `spot/einstieg` allein | **nichts** — steht | sofort |
| **B** **+** `spot/akkumulation` | FORM entscheiden · `schnitt` registrieren · SOL freischalten | überschaubar |
| **C** **+** `hebel` | A9 (Auflösung) · A1 (Band) · P-1 (Portfoliowert) | der lange Weg |

⚠️ **R-R9 greift nur lageweise:** `schnitt` für die Akkumulation zu
registrieren zwingt zur Neukalibrierung **dieser** Lage — nicht der
Einstiegs-Schwelle 0,080.

⚠️⚠️ **Was die Produktivsetzung NICHT löst** und vorher am Notebook zu
prüfen ist: das Mailaufkommen und der Wiederholungsanteil. Das sind
Betriebsbefunde, und die Desktop-Kopie ist vom 19.08. zu alt, um sie zu
beurteilen.
