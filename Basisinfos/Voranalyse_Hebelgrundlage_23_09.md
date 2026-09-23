# Voranalyse — woraus darf der Hebel kommen?

**23.09.2026.** Nutzerauftrag: *„bau die Voranalyse für eine andere
Hebelgrundlage, aber **nach der Zielvorgabe** — wir haben gerade ein
Problem oder?"*

---

## § 1 Ja — und zwar dieses

**Kein akutes Geldrisiko.** M1-Definition: *„Erst wenn M1 steht, wird
wieder Geld nach den Empfehlungen investiert."* M1 steht nicht.

**Das Problem ist die Freigabe.** M1-Kriterium 2 heißt *„Hebel gemessen"*.
Ohne die heutige Kette (2.557–2.562) wäre es abgehakt worden — auf einer
Grundlage, die in genau den Lagen, in denen der Hebel entsteht, belegt zu
hoch angesetzt ist.

| | |
|---|---|
| `q` **ordnet** richtig | belegt (Schwellenkalibrierung gegen den quotengleichen Zufall) |
| `q`s **Höhe** trägt den Hebel | und ist in den steuernden Lagen **−3,5 bis −4,0 Pp** daneben |
| die Signale entstehen | zu **100 %** in genau diesen Lagen (Lückenrabatt, 2.562) |
| ⚠️ **nicht belegt** | dass Kelly dort negativ ist — die Bänder lassen es offen |

➔ **M1-Kriterium 2 ist nicht erfüllt.** Das ist die Konsequenz, nicht der
laufende Betrieb.

---

## § 2 Die Zielvorgabe — sie entscheidet, was zulässig ist

> **Das System soll je Asset und Handlung eine neutrale, begründete Aussage
> über das POTENTIAL liefern — wie viel ist hier zu holen, verglichen mit
> allem anderen.**

und, für den Hebel präzisiert (Nutzer, 23.09.):

> *„Spot und Hebel haben denselben Eingang, trennen sich dann. Der Hebel
> soll, **wenn es ein optimales Chancen-Risiko-Verhältnis gibt**, dynamisch
> entstehen."*

### Was daraus als **Prüfstein** folgt

| # | Bedingung | woraus |
|---|---|---|
| **P1** | Der Hebel darf ein Asset **nicht entfernen** — sonst kann es nie einen erzeugen | Nutzervorgabe „derselbe Eingang" |
| **P2** | Er muss **stetig** sein — eine harte Kante macht aus minimalen Bewegungen alles oder nichts | Nutzerkritik 23.09. |
| **P3** | Er darf **kein Asset-Vorurteil** tragen | Regel 3 |
| **P4** | Seine Grundlage muss eine **Bewertung** sein, kein **Fakt** | Regel 4 |
| **P5** | Jede Größe, die ihn trägt, muss auf **ihrer eigenen Zielgröße** gemessen sein | R-R8 B1/B2 |

⚠️⚠️ **P5 ist der Prüfstein, an dem die heutige Lösung scheitert:** der
Hebel wird aus `q` gerechnet, `q` ist auf `barriere` definiert — und alle
Kalibrierungsmessungen zeigen, dass die **Höhe** dort nicht stimmt.

---

## § 3 Die Kandidaten — vier Wege, an P1–P5 gemessen

### A — `q` **kalibrieren** (den Versatz korrigieren)

Die gemessene Trefferquote je Merkmalslage an die Stelle der gerechneten
setzen, out-of-sample validiert.

| | |
|---|---|
| ✔ | P1–P4 erfüllt; die Architektur bleibt unverändert |
| ✔ | P5: es **ist** die Zielgröße, auf der `q` definiert ist |
| ⛔ | **Die Bänder sind ±3 Pp breit** (2.562) — die kalibrierte Quote wäre selbst unsicherer als das steuernde Fenster (1 Pp) |
| ⛔ | In-Sample-Gefahr: eine Lookup-Tabelle aus denselben Daten ist der Fehler, den 2.554 bereits getroffen hat |

### B — Den Hebel aus der **Geometrie** ableiten

`hebel_sicher(stop_rel)` gibt es bereits (`entscheidungsrechnung.py:460`):
der höchste Hebel, bei dem die Liquidation hinter dem Stop liegt (RM-11).
Er ist **reine Geometrie** — kein `q` nötig.

| | |
|---|---|
| ✔ | P1, P2 (stetig in `stop_rel`), P3 (kein Asset-Bezug) |
| ✔ | Belegt: die Stopweite ist gemessen (8 % Gipfel), RM-11 steht |
| ⛔ | **P4 verletzt.** Ein Liquidationsabstand ist ein **Fakt** über die Gegenwart, keine Aussage über das, was kommt. Als alleinige Grundlage wäre er genau der Verstoß, den Regel 4 benennt |
| ⛔ | Er sagt, **wie viel Hebel möglich** ist — nicht, **ob** er sich lohnt |

### C — **Kein Hebel**, bis die Kalibrierung steht

| | |
|---|---|
| ✔ | Ehrlich, sofort umsetzbar, kein Beleg nötig |
| ⛔ | Widerspricht der Nutzervorgabe „der Hebel soll dynamisch entstehen" |
| ⛔ | Verschiebt M1 auf unbestimmte Zeit |

### D — Die **Trennung**: `q` ordnet, die Geometrie skaliert

> **Der Hebel entsteht nur dort, wo `q` über der Schwelle liegt (die
> Ordnung, die belegt ist) — seine HÖHE kommt aber aus der Geometrie
> (`hebel_sicher`, Stop, CRV), nicht aus der absoluten Höhe von `q`.**

| | |
|---|---|
| ✔ | **P1** — kein Entfernen, `q` entscheidet nur über *ob* |
| ✔ | **P2** — die Geometrie ist stetig in `stop_rel` |
| ✔ | **P3** — kein Asset-Rang in der Höhe |
| ✔ | **P4** — die **Auslösung** bleibt eine Bewertung (`q` über Schwelle); der Fakt skaliert nur, er löst nicht aus |
| ✔ | **P5** — jede Größe wird dort verwendet, wo sie belegt ist: `q` für die **Ordnung**, die Geometrie für die **Höhe** |

⚠️⚠️ **D nutzt genau das, was gemessen ist, und nichts anderes.** Der
Befund der ganzen Kette lautet: *`q` ordnet richtig, seine Höhe nicht.*
D ist die Bauform, die daraus folgt.

---

## § 4 ⚠️ Was an D noch offen ist — und nicht geraten werden darf

| | |
|---|---|
| **1** | **Wie** skaliert die Geometrie? `hebel_sicher` ist eine **Obergrenze**, keine Vorgabe. Zwischen „möglich" und „gewählt" fehlt eine Regel |
| **2** | Das **Risikobudget** (`r_min`/`r_max`) käme dann woher? Heute aus halbem Kelly — ohne `q`-Höhe braucht es eine andere Herleitung |
| **3** | ⚠️ **Verliert man dadurch etwas?** Die Ordnung von `q` trägt (+0,200 auf der selektierten Menge) — ob ihre **Abstufung** einen Beitrag zur Hebelhöhe leistet, ist **ungemessen** |
| **4** | Die Nutzervorgabe **„optimales Chancen-Risiko-Verhältnis"** ist in D nicht abgebildet: das CRV ist heute eine **feste** Vorgabe (2,0), keine gemessene Größe je Lage |

➔ **Punkt 4 ist der wichtigste.** Die Zielvorgabe spricht von einem
*optimalen* CRV — heute ist es eine Konstante. Solange das so ist, kann
„der Hebel entsteht, wenn das CRV gut ist" gar nicht stattfinden.

---

## § 5 Mein Urteil — und wo die Grenze zur Entscheidung liegt

**D ist die einzige Bauform, die alle fünf Prüfsteine erfüllt und nur
Belegtes verwendet.** A hat das bessere Versprechen, aber die Datendecke
(±3 Pp gegen 1 Pp Fenster) steht dagegen. B allein verletzt Regel 4.
C wäre ehrlich, aber gibt das Ziel auf.

⚠️⚠️ **Das ist eine Entwurfsentscheidung, keine Messung** — und sie gehört
dem Nutzer vorgelegt, so wie 2.558 es schon festgehalten hat.

⚠️ **Was ich NICHT vorschlage:** D sofort zu bauen. Punkt 4 (das CRV als
Konstante) ist eine Lücke in der Zielvorgabe selbst, und sie zu übergehen
hieße, denselben Fehler zu machen wie heute früh — eine Bauform zu wählen,
bevor die Ursache gemessen ist.

**Der ehrliche nächste Schritt wäre deshalb nicht Bauen, sondern die
Frage: ist das CRV je Lage messbar?** Erst dann ist „optimales
Chancen-Risiko-Verhältnis" mehr als eine Formulierung.
