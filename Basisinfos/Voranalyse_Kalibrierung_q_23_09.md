# Voranalyse — trifft `q` die tatsächliche Trefferquote?

**23.09.2026.** Nutzerauftrag: *„mach die Voranalyse für die Kalibrierung
von q"* — mit der Warnung, die diese Voranalyse geprägt hat:

> *„Moment, zuerst in Detail-Recherche, wir haben q erst neu kalibriert
> glaube ich … **Vorsicht**."*

---

## § 1 Die Recherche — was **wirklich** kalibriert wurde

| Datum | was | betrifft `q`? |
|---|---|---|
| **22.09.** `KALIBRIERT_AM` | die **SCHWELLE** (`SCHWELLE_VORGABE = 0.060`) | ⛔ nein — R-R9 sagt **wo** geschnitten wird |
| **22.09.** S6 | die **turnover-Stufen** (Nennerwechsel) | ⛔ nein — die Punkte, nicht ihre Kalibrierung |
| **05.09.** N-37 / F-215 | *„liefert höheres Potential eine höhere Trefferquote?"* | ✔ ja — ⛔ **Artefakt** |
| **05.09.** N-42 / F-219 | Ersatzmessung, Faktor 19,5 % | ✔ ja — ⛔ **eingeordnet, ungültig** |

➔ **`q` wurde NIE gültig kalibriert.** Die Nutzererinnerung betraf die
Schwelle — und die Vorsicht war trotzdem richtig: ohne sie hätte ich
behauptet, die Frage sei nie gestellt worden. Sie wurde **zweimal**
gestellt.

⚠️⚠️ Die Begründung von N-37 ist wörtlich die heutige:

> *„Vorbedingung für jede Hebelabstufung: **Kelly ohne kalibriertes µ ist
> eine Formel ohne Eingabe.**"*

---

## § 2 Der Lauf von heute — ein Hinweis, **kein** Befund

`messe_bewertung_kalibrierung.py` heute erneut gefahren:

```
Steigung +0.040 Quote-Punkte je R  [+0.005 .. +0.078]
(bei perfekter Kalibrierung erwartet: +0.333)
```

| Potential | **tatsächlich** | **vorhergesagt** |
|---|---|---|
| −0,141 R | 30,5 % | 28,6 % |
| ±0,000 R | 31,6 % | 33,3 % |
| +0,085 R | **30,5 %** | **36,2 %** |

Zufallskontrolle bestanden (echt +0,040 gegen Zufallsspanne −0,046 …
+0,020). **Die Richtung ist echt, die Höhe ist es nicht** — Faktor **8,3**
zu flach.

### ⛔ Warum das nicht entscheidungsfähig ist

| | |
|---|---|
| lief auf **745.036** Ankern | die **FREIE** Menge |
| **F-212** | *„die Beiträge wirken auf **1,5 %** der Anker"* |
| Kontrolle 1 vergleicht gegen `turnover +0.33/+0.33/+0.33/−0.48/−0.48` | **zurückgenommene** Stufen |
| Werkzeug vom 05.09. | **vor** dem Messstandard — Altbestand |

➔ **Exakt der Fehler von N-56 / N-58**, der am 07.09. eine Live-Änderung
ausgelöst und am selben Tag zurückgenommen hat.

---

## § 3 ✔ Machbarkeit — gerechnet, vor der Messung

### 3.1 Die Menge

| Menge | Anker | Tage | out-of-sample (2. Hälfte) | **Blöcke** |
|---|---|---|---|---|
| frei | 745.036 | 2.955 | — | — |
| 50 % | 321.825 | 2.809 | 160.912 / 1.405 Tage | **23** |
| **20 %** | **128.451** | 2.710 | **64.225 / 1.355 Tage** | **22** |
| 10 % | 63.750 | 2.464 | 31.875 / 1.232 Tage | 20 |

⚠️ Der Werkzeugkopf nennt als Falle 4: *„bindend ist die **Blockzahl**
(~32), nicht die Ankerzahl."* Auf der selektierten Menge sind es **22** —
**weniger Macht als 2005.09.**, aber nicht wenig.

### 3.2 ⚠️ Eine Warnung im Werkzeugkopf ist VERALTET

Dort steht: *„seit dem 07.09. reicht das Potential nur bis +0,049 R"*.
**Heute nicht mehr** — nachgerechnet:

| | |
|---|---|
| niedrigstes Potential | **−0,1428 R** (funding 4, turnover 4) |
| höchstes | **+0,1086 R** (funding 1, turnover 0) |
| **Spanne** | **0,2514 R** = **111 %** der 05.09.-Spanne |

Ursache: der turnover-Stufenwechsel vom 22.09. hat die Spanne wieder
geweitet.

### 3.3 Das Signal-Rausch-Verhältnis

| | |
|---|---|
| erwartete Quotenänderung über die volle Spanne bei perfekter Kalibrierung | **8,4 Prozentpunkte** |
| gemessenes Band je Potentialstufe | rund **±2,5 Prozentpunkte** |

➔ **✔ MACHBAR.** Ein Signal von 8,4 Pp gegen ±2,5 Pp Rauschen ist
auflösbar — die Messung kann zwischen „kalibriert" und „Faktor 8 zu flach"
unterscheiden.

---

## § 4 Was zu bauen ist

`messe_bewertung_kalibrierung.py` kennt **keine** Auswahlmenge (im Code
nicht vorhanden). Nötig sind drei Änderungen, alle klein:

| | |
|---|---|
| **1** | `--menge` über `messnorm_auswahl.MENGEN` und `messe_beitrag_auf_auswahl._auswahl_maske` — **dieselben** Funktionen wie in F-212, keine Kopie |
| **2** | Kontrolle 1 gegen die **heutigen** Stufen vergleichen, nicht gegen eine eingefrorene Liste |
| **3** | Die veraltete `+0,049`-Warnung im Kopf durch den gerechneten Bereich ersetzen |

⚠️ Die Vorgabe bleibt `frei`, damit der alte Lauf reproduzierbar bleibt
(R-R11) — die selektierte Menge kommt als **Schalter** dazu.

---

## § 5 Die Fallen — die vier alten plus zwei neue

| | |
|---|---|
| **1** Zirkularität | Stufen auf der **ersten** Hälfte fitten, Kalibrierung auf der **zweiten** prüfen — das Werkzeug tut das bereits |
| **2** Form | Zielgröße ist `barriere` — und das ist hier **richtig**, denn `q` **ist** die Barrieren-Trefferquote |
| **3** Arithmetik | 33,3 % steht per Konstruktion fest; die Prüfgröße ist die **Steigung**, nicht „trägt/trägt nicht" |
| **4** Macht | bindend ist die **Blockzahl** — auf der selektierten Menge 22 |
| **5** ⚠️ NEU: Mengenwechsel | die selektierte Menge ist eine **andere Grundgesamtheit**. Die Wirkung ist auszuweisen, nicht stillschweigend hinzunehmen |
| **6** ⚠️ NEU: Stufenstand | die Stufen haben sich am 22.09. geändert. Ein Vergleich mit dem 05.09.-Lauf ist **kein** R-R11-Nachweis |

---

## § 6 Risiken und was **nicht** entschieden wird

### Wenn die Kalibrierung fällt

`kelly = (q(1+CRV) − 1)/CRV` rechnet mit `q`, **als wäre es die echte
Quote**. Ein systematisch zu hohes `q` ergibt einen systematisch zu
großen Hebel — **linear**.

⚠️ **Was dagegen schützt und heute schon greift:** `hebel_sicher`
(Liquidationsabstand, RM-11), der **Aggregat-Deckel** (H-5) und
`hebel_grenze` = 5,0. Ein Kalibrierungsfehler wird dadurch **gedeckelt**,
nicht beseitigt.

### Was diese Messung **nicht** entscheidet

- **Nicht**, ob die Beiträge tragen. Das ist getrennt gemessen.
- **Nicht**, ob die Schwelle stimmt. Die ist am 22.09. kalibriert und
  misst die **Ordnung**, nicht die Höhe — `messe_schwelle_quotengleich`
  vergleicht ausdrücklich gegen den **quotengleichen** Zufall.
- **Nicht**, wie der Hebel zu bauen wäre, falls `q` zu hoch liegt. Das
  wäre eine Entwurfsfrage — und sie gehört dem Nutzer vorgelegt.

### ⚠️⚠️ Die ehrliche Erwartung

Der Hinweis von heute (+0,040 statt +0,333) ist **stark** und die
Zufallskontrolle hält. Es ist wahrscheinlicher, dass sich die Größenordnung
bestätigt, als dass sie verschwindet.

**Dann steht eine Entscheidung an, keine Messung:** ein `q`, das die
Ordnung trifft, aber die Höhe nicht, ist für eine **Schwelle** brauchbar
und für **Kelly** nicht. Das ist derselbe Unterschied wie „Messform ≠
Bauform" — und er entscheidet, ob der Hebel überhaupt aus `q` kommen darf.
