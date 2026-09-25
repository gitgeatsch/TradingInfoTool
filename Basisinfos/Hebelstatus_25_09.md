# HEBELSTATUS — wo wir stehen, und wo es weitergeht

**25.09.2026.** Nutzerauftrag: *„nach der nächsten größeren runde brauchen
wir einen Status wie wir bei der Hebelfrage stehen und weitermachen ohne
falsch abzubiegen."*

---

# § 1 Das Ergebnis der `barriere`-Messung

**Werkzeug:** `n78_terminmarkt_kanaele.py --lage hebel` — das Original mit
einem Schalter. Lage `hebel × einstieg`, Zielgröße **`barriere`**, Horizont
**3**, `simuliert=True`. Alles von `messnorm` erzwungen, nichts gewählt.

## 1.1 ✔ Die Positivkontrolle hält — die Zielgröße funktioniert

| Kandidat | 20 % | 50 % | frei | |
|---|---|---|---|---|
| **`oi_aenderung`** | +0,0106 | +0,0072 | +0,0047 | ⭐ **3 von 3 — TRÄGT** |
| `funding` | +0,0081 | **+0,0075** | **+0,0055** | 2 von 4 |
| `turnover` | — | +0,0073 | +0,0073 | 0 von 2 |
| **`zufall`** | −0,0004 | −0,0053 | −0,0020 | ✔ **0 von 4** |

⭐⭐ **Das ist der entscheidende Teil.** `oi_aenderung` trägt auf `barriere`
**robust über alle drei Mengen**. Damit ist bewiesen: **die Anlage findet
auf dieser Zielgröße etwas, wenn etwas da ist.** Ein Nullbefund bei den
offenen Kandidaten ist jetzt interpretierbar — vorher wäre er es nicht
gewesen.

## 1.2 ⛔ Keiner der offenen Kandidaten trägt

| Kandidat | Ergebnis |
|---|---|
| `oi_je_umsatz` | 1 von 3 (nur 20 %) — **nicht robust** (N-73) |
| `long_bias` | **0 von 3** |
| `top_bias` | **0 von 3** |
| **`taker_bias`** | **0 von 3** — und er war *„der aussichtsreichste der vier"* |

➤ ⛔ **Die `barriere`-Spur ist gemessen. Sie ist leer.**

Das war die **letzte im Kandidatenregister offen geführte Hebelspur**:
*„gegen `bewegung_r` gefallen, also gegen die SPOT-Frage. Die HEBEL-Frage
ist `barriere` — dagegen ist er NIE gemessen."* **Jetzt ist er es.**

---

# § 2 ⭐⭐⭐ Der eigentliche Fund — und er dreht die Richtung

> **Die Beiträge, die auf der HEBEL-Zielgröße tragen, sind die, die es
> schon gibt.**

| | auf `barriere` | Status im Betrieb |
|---|---|---|
| `oi_aenderung` | ⭐ **3 von 3** | registriert (Schalter, H-4c) |
| `funding` | 2 von 4 | **live** |

⚠️⚠️ **Und genau diese nimmt meine eigene Kapselung dem Hebel weg.**

Am 24.09. habe ich `funding` und `turnover` auf `instrumente=("spot",)`
gesetzt — als Umsetzung der Vorgabe *„Hebel kann von Spot nichts erben"*.
Gemessen am 25.09.: Spanne bestes zu schlechtestem Fünftel für
`instrument="hebel"` = **0,0000**. Die Hebelquote steht konstant auf
0,3333, der Kelly-Nullstelle.

➤ **Der Hebel hat keine Bewertung — nicht weil es keine gäbe, sondern weil
ich ihm die vorhandene weggenommen habe.**

## 2.1 ⚠️ Was daraus NICHT folgt

⛔ **Nicht**, die Spot-Stufen einfach freizuschalten. Sie sind auf
`bewegung_r`/H20 gemessen; auf `barriere`/H3 sind die Wirkungen **eine
Größenordnung kleiner** (+0,0055 gegen +0,0248 bei `funding`). Eine
Übernahme wäre der Faktor-3-Fehler aus N19, nur andersherum.

✔ **Sondern:** die Merkmale gelten für beide, die **Stufen** werden für den
Hebel **eigen gemessen** — gegen `barriere`, auf H3. Das ist N19-E, deine
Entscheidung vom 06.09.

---

# § 3 Wo wir stehen — die ehrliche Bilanz

| | |
|---|---|
| ✔ **Die Hebel-Zielgröße funktioniert** | `oi_aenderung` 3/3, `zufall` 0/4 |
| ✔ **R-R11 gehalten** | `long_bias` 0/3, `top_bias` 0/2 auf `bewegung_r` reproduziert |
| ✔ **N-17b reproduziert** | `long_bias × top_bias` +0,954 gegen +0,955 |
| ⛔ **Der Terminmarkt ist ausgemessen** | vier Kandidaten, zwei Zielgrößen, alle zulässigen Mengen, Positivkontrolle hält |
| ⭐ **Aber zwei vorhandene Beiträge tragen auf `barriere`** | und dem Hebel fehlen sie nur, weil die Kapselung sie sperrt |
| ⛔ **Die Basisrate schwankt** (2.585) | 10,7 – 60,7 %, nicht vorhersagbar — das bleibt |
| ⚠️ **Die bedingte Quote ist bei 6 h strukturell verzerrt** | 97 % enden offen; die Kelly-Formel setzt zwei Ausgänge voraus, real sind es drei |

---

# § 4 ⭐ Wie es weitergeht — ohne falsch abzubiegen

## Der Weg, der jetzt offen ist

```
H-1   funding + oi_aenderung fuer `hebel` freischalten
      ABER mit eigenen Stufen, gemessen gegen `barriere` auf H3
      (= N19-E, Nutzerentscheidung 06.09., nie umgesetzt)

H-2   Die Schwelle je Lage nachziehen (R-R9) - zwei Zielgroessen
      heissen zwingend zwei Schwellen

H-3   Die Kette: eigene Zelle, beide Bewertungen parallel, eine gewinnt
```

## ⚠️ Die drei Abzweigungen, die falsch wären

| ⛔ | warum |
|---|---|
| **Spot-Stufen übernehmen** | Größenordnung passt nicht (+0,0055 gegen +0,0248) — N19-Fehler |
| **Weitere Terminmarkt-Kandidaten suchen** | die Quelle ist ausgemessen; die Positivkontrolle belegt, dass es nicht an der Anlage liegt |
| **Den Hebel aus der bedingten Quote rechnen** | bei 6 h stammt sie aus 2,9 % der Fälle; die Formel setzt zwei Ausgänge voraus, real sind es drei |

## ⚠️ Was vorher noch zu klären ist

| | |
|---|---|
| **O-5** | 2.585 nachziehen (90. Perzentil, Trennschärfe) — dort *ist* der Nullbefund die Aussage |
| **O-4** | die vier Werkzeuge an `messnorm` binden |
| **O-3** | der Querschnitt: 18 Symbole → Terzile statt Fünftel? |
| **O-6** | `messe_zusammenspiel_beitraege`: Urteil ohne Nullpunkt — zurücknehmen |

---

# § 5 Die eine Frage, die dem Nutzer gehört

> **Die Kapselung vom 24.09. hat dem Hebel seine Bewertung genommen. Soll
> sie gelockert werden — Merkmale für beide, Stufen getrennt gemessen?**

Das ist die Umsetzung deiner Vorgabe *„beide MÜSSEN etwas anderes
bewerten"*: **dieselben Merkmale, verschiedene Stufen, verschiedene
Zielgrößen.** Nicht „Hebel erbt von Spot", sondern „Hebel misst dasselbe
Merkmal auf seiner eigenen Frage".

⚠️ **Eine Entwurfsentscheidung, keine Messung** — sie gehört dir.
