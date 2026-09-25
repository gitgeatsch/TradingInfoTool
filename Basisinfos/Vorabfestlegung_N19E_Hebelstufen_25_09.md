# Vorabfestlegung 13 — N19-E: die Hebelstufen gegen `barriere`

**25.09.2026, geschrieben VOR der Messung.**
Nutzerauftrag: *„ja Vorabfestlegung für N19-E aufsetzen - prüfen und
gegenprüfen"*

**N19-E ist eine Nutzerentscheidung vom 06.09.2026, die nie umgesetzt
wurde.** Diese Vorabfestlegung holt sie nach.

---

# § 1 Die Frage

> **Welchen Punktwert bekommt jedes Fünftel von `funding` und
> `oi_aenderung`, wenn direkt gegen die HEBEL-Zielgröße gemessen wird?**

**Und ausdrücklich NICHT:** „tragen sie?" — das ist am 25.09. beantwortet
(`oi_aenderung` 3 von 3, `funding` 2 von 4 auf `barriere`/H3, Kontrolle
`zufall` 0 von 4).

---

# § 2 ⚠️ Warum überhaupt — der Zielgrößenbruch

Die heutigen Live-Stufen stammen aus einer Messung auf **`bewegung_r`** und
wurden **1:1** in Quotenpunkte übersetzt. Gemessen (2.580):

| Beitrag | vorhergesagt | tatsächlich | Faktor |
|---|---|---|---|
| `funding` | 5,744 | 1,715 | **0,30** |
| `turnover` | 8,643 | 3,000 | **0,35** |

**Unabhängig bestätigt am 25.09.** über die Wirkungen beider Läufe:

| | `bewegung_r` H20 | `barriere` H3 | Verhältnis |
|---|---|---|---|
| `oi_aenderung` frei | +0,0125 | +0,0047 | **2,7** |
| `funding` frei | +0,0248 | +0,0055 | **4,5** |

➤ **Die Skala ist eine andere. Die Stufen sind zu groß.**

## 2.1 ⚠️⚠️ Was das NICHT ist — Korrektur vom 25.09.

⛔ **Es ist KEIN Beleg für eine eigene Hebel-BEWERTUNG.**

`wahrscheinlichkeit.Beitrag` nennt den Auslöser wörtlich: *„sobald A1
behoben und `barriere` messbar ist, wird gemessen, ob ein Beitrag auf
`barriere` ANDERS wirkt als auf `bewegung_r`. Trägt er dort anders, bekommt
der Hebel seine eigene Bewertung — sonst nicht."*

**Gemessen: sie tragen auf BEIDEN.** `oi_aenderung` 3/3 hier wie dort.

⚠️ Ich hatte `turnover` als Gegenbeleg genommen (2/2 auf Spot, 0/2 auf
Hebel). **Das war falsch:** seine Wirkung liegt mit +0,0073 **unter der
Nachweisgrenze** (0,0094 bis 0,0180), und er hat mit **66 Symbolen** die
dünnste Datenlage. *Untermächtig ist nicht anders.*

➤ **Daraus folgt: dieselben Merkmale, dieselbe Bewertungsform — nur eine
eigene SKALA.** Genau das ist N19-E.

---

# § 3 Was gemessen wird

| | |
|---|---|
| **Kandidaten** | `funding` · `oi_aenderung` |
| **Zielgröße** | **`barriere`** — aus `messnorm.ZIELGROESSE_JE_LAGE[(hebel, einstieg)]`, nicht gewählt |
| **Horizont** | **3** — aus `messnorm.HORIZONT_JE_LAGE`, nicht gewählt |
| **Lage** | `Lage(hebel, einstieg, simuliert=True)` — die Markierung ist Pflicht |
| **Ausgabe** | je Kandidat **fünf Punktwerte** (Fünftel 0…4), in Quotenpunkten |

⛔ **`turnover` bleibt bei Spot** — nicht weil er dort nicht trüge, sondern
weil er auf `barriere` **nicht nachweisbar** ist. Das ist eine Datenlage,
kein Urteil (§ 2.1).

## 3.1 ⚠️ Die Schwelle: was ist H3 überhaupt?

| Horizont | entschiedene Trades | `barriere` brauchbar |
|---|---|---|
| **H3 = 72 h** | **52,6 %** | ✔ ja |
| 6 h | 2,9 % | ⛔ nein |

**Auf dem Normhorizont ist `barriere` tragfähig.** Die Zielgröße
`ergebnis_r` aus Vorabfestlegung 10 war nur für die **kürzeren** Horizonte
nötig und steht hier nicht zur Debatte.

---

# § 4 Die Norm

| | |
|---|---|
| **Frageart** | `beitrag` → **selektierte Menge** über `zulaessige_mengen()` |
| **Nullpunkt** | 90. Perzentil über 40 Ziehungen (aus `messnorm`, **nicht** eigene Konstante) |
| **Trennschärfe** | gegen denselben Bezug, Stärken bis 0,40 R |
| **Positivkontrolle** | `oi_aenderung` trägt bereits 3/3 — er ist sie |
| **Negativkontrolle** | `zufall` |
| **B5 Monotonie** | ⭐ **über alle fünf Fünftel** — eine Stufenleiter, die nicht monoton ist, ist keine |
| **B6** | beide Historienhälften |
| **out-of-sample** | ⭐ **Pflicht** — Stufen auf der ersten Hälfte schätzen, auf der zweiten prüfen |
| **R-R11** | ✔ erfüllt (25.09., `n78` Original) |
| **Register** | ✔ gelesen |

⚠️⚠️ **Das Werkzeug wird an `messnorm` gebunden**, nicht mit eigenen
Konstanten gebaut. Vier meiner Werkzeuge vom 24./25.09. haben **null**
`messnorm`-Verweise — genau der Altbestandsfehler, der jeden Befund unter
Vorbehalt stellt.

---

# § 5 ⭐ Die Entscheidungsregel — VOR der Messung

| Ergebnis | Entscheidung |
|---|---|
| ✔ **Stufen monoton, out-of-sample stabil, Kontrolle sauber** | **Sie werden die Hebelstufen.** Danach: R-R9 (Schwelle je Lage), dann die Kette |
| ⚠️ **Nicht monoton** | ⛔ **keine Stufenleiter** — dann trägt der Beitrag zwar, ist aber nicht abstufbar. Er würde ein **Schalter**, kein Regler |
| ⚠️ **In-sample ja, out-of-sample nein** | ⛔ Überanpassung, kein Befund |
| ⛔ **Trennschärfe reicht nicht** | nichts entschieden — Datendecke, wie bei `turnover` |
| ⛔ **Kontrolle trägt** | Lauf ungültig |

⚠️⚠️ **Wird nicht nachverhandelt.**

## 5.1 ⚠️ Die Grenze, die vorher benannt gehört

Die Wirkungen auf `barriere` liegen bei **+0,0047 bis +0,0106**. Die
Nachweisgrenze der Anlage lag in denselben Läufen bei **0,0088 bis
0,0209**.

➤ **Die Stufen werden klein sein, und ihre Bänder werden breit.** Eine
saubere Fünferleiter zu erwarten wäre unrealistisch; wahrscheinlicher ist
eine **grobe Zweiteilung** (oberstes Fünftel gegen Rest).

⚠️ **Das ist vorab gesagt, nicht hinterher als Enttäuschung.**

---

# § 6 Die Vorhersage

**Erwartung: `oi_aenderung` liefert eine monotone, aber flache Leiter;
`funding` nicht robust genug.**

**Begründung:** `oi_aenderung` trägt auf allen drei Mengen (3/3), `funding`
nur auf zweien. Und die Skala ist rund 4× kleiner als auf `bewegung_r` —
bei Stufen von heute 0,82 bis −1,7 Punkten blieben etwa **0,2 bis −0,4**.

---

# § 7 Was diese Messung **nicht** entscheidet

- **Nicht** die Kette (eigene Zelle, Takt, parallele Bewertung).
- **Nicht** die Schwelle — das ist R-R9, danach.
- **Nicht** `turnover` (Datenlage, § 2.1).
- **Nicht** die Basisrate (2.585: schwankt 10,7–60,7 %, nicht vorhersagbar).
- **Nicht** die kurzen Horizonte unter H3.
