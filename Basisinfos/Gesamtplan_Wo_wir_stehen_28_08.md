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
