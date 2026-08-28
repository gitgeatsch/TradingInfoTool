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

## ⚠️ Der Befund, der alles andere überlagert: DER HEBEL IST STILLGELEGT

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

**L6 — nur ein tragender Beitrag im Potential.** Unverändert die einzige
Lücke, die kein Umbau schließt. Die drei Wege stehen oben in Abschnitt 4:
Fremdquellen (19.09. / 22.10.), Nachrichten, oder das Ziel neu fassen.
