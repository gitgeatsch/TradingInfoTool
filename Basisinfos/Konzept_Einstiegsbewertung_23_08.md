# Konzept — die Einstiegsbewertung: Vorfilter, Kette, nachgelagerter Filter

*Nutzerfrage 23.08.: „wie stellst du dir den Gesamtplan und die Funktionalität
der Einstiegsbewertung vor — bleiben wir bei einem reinen Vorfilter, oder ist
ein nachgelagerter Filter erforderlich, der die gesamte Entscheidungskette
bewerten kann? Nach Möglichkeit soll er die Vorarbeit fortsetzen und keine
neuen Baustellen aufmachen."*

> **Alles hier ist gemessen oder am Code gelesen.** Was ich vorschlage, steht
> als Vorschlag da; was gemessen ist, mit seiner Zahl.

---

## 0. Die kurze Antwort

| | |
|---|---|
| **Brauchen wir einen nachgelagerten Filter?** | **Ja** — und **er ist gebaut**: `wahrscheinlichkeit.py` |
| **Warum reicht ein Vorfilter nicht?** | Vor der Kette weiß niemand, was das Modell sagen wird. Ihre eigene Vorgabe — *„jede Entscheidung braucht eine Begründung"* — ist **nur nach der Kette** prüfbar |
| **Neue Baustelle?** | **Eine**, und das Konzept verlangt sie: **Z1s Urteil wird nirgends je Signal gespeichert** |
| **Was fehlt sonst?** | keine Bauteile — **Belege**. 46–66 aufgelöste Fälle sind die Obergrenze jeder Aussage |

---

## 1. Zuerst: NICHTS_TUN braucht Gründe, und die drei sind verschieden

**Ihre Beispiele, sortiert:**

| | Fall | woran erkennbar |
|---|---|---|
| **N1** | **Bestand vorhanden** → halten oder verkaufen ist die Frage, nicht kaufen | `holdings` / `hebel_positions` |
| **N2** | **Nichts hat sich geändert** — die vorige Empfehlung gilt weiter | ⚠️ **`anlass_beobachtung` — existiert, 45.479 Zeilen** |
| **N3** | **Unklare Indikatorenlage** → besser abwarten | offen, siehe 1.2 |

### 1.1 N2 ist bereits gebaut — und ist die belastbarste Zahl der Kette

`anlass.fingerabdruecke()` hasht **den fertigen Faktentext**, nicht die
Rohdaten:

> *„Wer den Kurs hashen würde, bekäme bei jedem Tick einen neuen Abdruck; der
> Text sagt ‚1.093 EUR wert' und ändert sich erst, wenn es der Leser merkt."*

**Gemessen: 45.479 Beobachtungen, davon 13.898 mit „hätte gesperrt" (31 %).**
Das ist genau Ihr N2 — *„es hat sich seit der letzten Empfehlung nichts
geändert"* —, und es ist die einzige Stufe der Kette mit Masse.

⚠️ **Schwäche, gemessen:** ein Hash ist alles oder nichts. Ändert sich
irgendeine Zahl in irgendeinem Block, gilt das Signal als neu. Deshalb nur
31 %. **`bloeckeabdruecke()` und `geaenderte_bloecke` liegen seit dem 16.08.
bereit** — die blockweise Auswertung ist vorbereitet und nicht benutzt.

### 1.2 ⚠️ N3 ist der gefährliche Fall — und das Projekt hat es schon einmal bezahlt

**Der Fachstandard** für „ich weiß es nicht" ist die **Abstention** (reject
option, Chow): ein Verfahren darf sich enthalten, wenn seine Sicherheit unter
einer Schwelle liegt.

⚠️ **Das Projekt hat genau das schon einmal versucht** (Fakten-Entscheidungs­-
mappe):

> *„Ein Mehrdeutigkeits-Label wäre strukturell eine ‚Unknown'-Option — die
> löst laut Literatur Abstention aus, und **genau dieser Mechanismus drückte
> hier die ERÖFFNEN-Quote von 93 % auf 3 %**."*

**Daraus folgt eine Bauregel, kein Verbot:**

> **Der Grund „unklare Lage" darf dem Modell nicht als Wahlmöglichkeit
> angeboten werden — er muss nach der Antwort deterministisch abgeleitet
> werden.**

Das ist genau die Aufgabe eines **nachgelagerten** Filters, und es ist das
erste Argument dafür, dass ein Vorfilter allein nicht reicht.

### 1.3 Was heute stattdessen passiert

| | |
|---|---|
| `facts_json` bei HALTEN / REDUZIEREN / VERKAUFEN | **17 Zeichen** — `{"asset": "IO"}` |
| Z.ai-Zweitmeinung auf der Verkaufsseite | **0 von 561** |
| Merkmalsfamilien bei REDUZIEREN | **10 von 75** |

**561 Nichthandlungen ohne nachvollziehbare Begründung.** Nach Ihrem
Grundsatz ist das der Kern des Problems, nicht ein Nebenschauplatz.

---

## 2. Vorfilter oder nachgelagerter Filter? — Beide, und beide existieren

### 2.1 Die drei Stellen, an denen bewertet werden kann

| Stelle | Modul | Zustand | was sie kann |
|---|---|---|---|
| **vor** der Kette | `vorfilter.py` (H) | ✔ gebaut, **Schatten** | Geometrie: Weg frei, Stop gedeckt |
| **in** der Kette | `rollen_gate` / `trichter` | ✔ läuft | Durchlässigkeit je Stufe |
| **nach** der Kette | **`wahrscheinlichkeit.py`** | ✔ **gebaut**, zeigt nur an | die Beiträge zusammenführen |

⚠️ **Der nachgelagerte Filter existiert also. Sein Modulkopf zitiert Ihren
Einwand von damals wörtlich** — *„das System kann diese Informationen nicht
SELBST in Zusammenhang bringen"*.

### 2.2 ⚠️ Aber er ist heute ein Vorfilter im Kostüm

**Seine fünf Beiträge, gemessen:**

| Beitrag | Zustand | Punkte | woher |
|---|---|---:|---|
| **Vorfilter H** | **trägt** | **+4,5** | vor der Kette |
| Rangplatz | null | 0,0 | vor der Kette |
| Trichter | enthalten | 0,0 | vor der Kette |
| Lebendigkeit | noch nicht | 0,0 | vor der Kette |
| Termine | nie | 0,0 | – |

> **Alle fünf stammen von *vor* der Kette.** Nichts, was das Modell, Z1 oder
> Z.ai beigetragen haben, geht ein.

**Damit beantwortet sich Ihre Frage:** ein reiner Vorfilter ist das, was wir
heute *haben* — und er kann Ihre Begründungspflicht nicht erfüllen, weil er
die Entscheidung nicht kennt, die er begründen soll.

### 2.3 Was ein nachgelagerter Filter bewerten könnte — gemessen

| Größe | gefüllt | **aufgelöst** | Zustand |
|---|---:|---:|---|
| `unabhaengige_faktoren` (Faktorzahl) | 1.656 | **66** | ⚠️ **Wiederholung der Entscheidung** — 3 = 82 % Einstieg, 2 = 0 % |
| `umgeworfen_preis_eur` (Widerlegungspreis) | 1.651 | **66** | die einzige Zahl, die dem Modell gehört — **nie ausgewertet** |
| `belege_json` | 1.611 | 54 | **nie gegen Ergebnisse ausgewertet** |
| `zai_gegenpruefung_urteil` | 836 | 46 | Anbieter nicht vom Zufall unterscheidbar (geclustert) |
| **Z1-Urteil** (Treue zur Eingabe) | **0** | **0** | ⚠️ **wird nirgends gespeichert** |

⚠️ **Z1 ist die einzige deterministische, kostenlose Prüfung der Kette** —
Zahlendeckung, Richtungstreue, Zuspitzung, Leerlauf. Sie läuft, geht in die
Mail und in die Zählung, und **landet nicht in der Signalzeile**. Sie kann
deshalb nie gegen Ergebnisse gemessen werden.

> **Das ist die eine Baustelle, die das Konzept verlangt** — und sie ist
> klein: ein Feld mehr in `felder_aus_entscheidung`.

---

## 3. ⚠️ Die harte Grenze: 66 Fälle

**Alles, was ein nachgelagerter Filter je belegen könnte, steht auf 66
aufgelösten Signalen** (42 Ziel, 24 Stop — Stand vor E1/E2; danach weniger).

| | |
|---|---:|
| Rollen-Signale gesamt | 1.656 |
| davon `nicht_anwendbar` | 1.428 |
| **aufgelöst** | **66** |

**Daraus folgt die Reihenfolge des Plans, nicht aus einer Vorliebe:**

> **Erst aufzeichnen, dann messen, dann entscheiden lassen.** Wer jetzt einen
> Beitrag in die Wahrscheinlichkeit einträgt, trägt eine Vermutung ein — und
> das Modul ist ausdrücklich dagegen gebaut („eine Zahl zu bauen hätte
> Sicherheit vorgetäuscht, wo keine war").

---

## 4. Der Plan

### Stufe 1 — Aufzeichnen, was heute verlorengeht *(die einzige Bauarbeit)*

| | was | Aufwand |
|---|---|---|
| **P1** | **Z1-Urteil je Signal speichern** — Zahlendeckung, Richtungstreue, Zuspitzung, Leerlauf | klein |
| **P2** | **Verkaufsseite: den Faktenstummel ersetzen** (B1/B2) — beide Schreibpfade, `familien` mit | klein |
| **P3** | **NICHTS_TUN bekommt seinen Grund** — N1/N2/N3 **deterministisch abgeleitet**, nicht vom Modell erfragt | mittel |

⚠️ **P3 ist der Punkt, an dem Ihre Begründungspflicht technisch wird.** Der
Grund wird *nach* der Antwort bestimmt: Bestand ja/nein (N1), Fingerabdruck
unverändert (N2), sonst N3. **Keine neue Frage an das Modell.**

### Stufe 2 — Messen, was trägt

| | was | wann möglich |
|---|---|---|
| **M1** | Widerlegungspreis gegen Ergebnis | jetzt (66 Fälle, zu wenig) |
| **M2** | Z1-Urteil gegen Ergebnis | **erst nach P1** |
| **M3** | Belege gegen Ergebnis | jetzt (54) |
| **M4** | Verkaufsseite überhaupt | **erst nach P2** |

⚠️ **Jede dieser Messungen braucht mehr Fälle, als heute existieren.** Das ist
kein Argument gegen sie, sondern der Grund, jetzt mit dem **Aufzeichnen** zu
beginnen: jeder Tag ohne P1/P2 ist ein Tag, der später fehlt.

### Stufe 3 — Entscheiden lassen

Erst wenn ein Beitrag seinen gemessenen Wert hat, kommt er in
`wahrscheinlichkeit.BEITRAEGE` — **mit Zustand `trägt`**, wie H heute.

**Und erst dann** bekommt die Wahrscheinlichkeit eine Schwelle und darf
auswählen — an der Stelle, an der heute die **Uhr** entscheidet.

---

## 5. Was das für Spot gegen Hebel heißt

**Ihr Eindruck, dass es „eher die Dimensionierung betrifft", trifft zu — und
die Arithmetik sagt, warum:**

```
hebel_noetig = verlustanteil / stop_rel        Kosten_R = 2 × Gebühr / stop_rel
```

**Der Stopabstand entscheidet beides** — Hebel *und* Kostenhürde, in
entgegengesetzte Richtung. Bei Referenz 0,30 %:

| | Stop | Hebel | Hürde über der Basisrate |
|---|---|---|---:|
| **SPOT — Bodenbildung oder Tod** | weit | 1,0 | **+0,8 Punkte** |
| **HEBEL — kurzfristige Chance** | eng | > 1 | **+8,0 Punkte** |

⚠️ **Und der Fachstandard sagt, dass die Antwort je Instrument gegenläufig
ist** (Entscheidungslog 03.08., gemessen):

| | Gate (ja/nein) | Größe |
|---|---|---|
| **Hebel** | **SQN +3,25** | +1,25 |
| **Spot** | +0,63 | **+1,36** |

> **Beim Hebel ist ein GATE überlegen, bei Spot die GRÖSSE.** Das ist genau
> Ihre Unterscheidung: eine kurzfristige Chance nimmt man oder nicht; eine
> Bodenbildung baut man in Größen auf.

**Damit hat der nachgelagerte Filter zwei verschiedene Aufgaben je
Instrument** — und das ist kein Sonderfall, sondern eine gemessene Eigenschaft:

| | Aufgabe des Filters |
|---|---|
| **Hebel** | **ja oder nein** — mit einer Schwelle |
| **Spot** | **wie groß** — über die CRV-Abstufung (geeicht, aber **aus**) |

---

## 6. Was ich NICHT vorschlage

| | warum |
|---|---|
| die Wahrscheinlichkeit jetzt entscheiden lassen | nur **ein** Beitrag trägt (H); die anderen wären Vermutungen |
| H scharf schalten | erst muss der Schatten zeigen, wie oft H auf der **Watchlist** zutrifft — Kapitel 124: auf 29 Symbolen **nicht bestätigbar** |
| die CRV-Abstufung einschalten | geeicht, aber das Einschalten ändert Positionsgrößen — Ihre Entscheidung |
| den Cooldown abschaffen | Ihre Vorgabe: er **steuert**, er entscheidet nur nicht |
| einen zweiten Filter bauen | ⚠️ **es gibt ihn** — er ist nur unterernährt |
