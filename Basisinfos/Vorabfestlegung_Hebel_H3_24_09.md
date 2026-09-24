# Vorabfestlegung 7 — 2.490 auf dem Hebel-Horizont

**24.09.2026, geschrieben VOR der Messung.** Nutzerauftrag: *„Schritt 2
aufsetzen — vorher detaillierte Recherche, Voranalyse, Planung, messen,
testen, simulieren."* Schritt 2 aus
`Basisinfos/Konzept_Spot_und_Hebel_trennen_24_09.md`.

---

# § 1 Die Frage — **wortgleich** von 2.291 übernommen

> *„sobald A1 behoben und `barriere` messbar ist, wird gemessen, ob ein
> Beitrag auf `barriere` **anders** wirkt als auf `bewegung_r`. Trägt er
> dort anders, bekommt der Hebel seine eigene Bewertung — sonst nicht."*

⚠️⚠️ **Die Regel wird nicht neu formuliert.** Sie stand seit dem 10.09.
vorgemerkt, also vor A1 — kein Suchpreis. Wer sie umformuliert, weil das
erste Ergebnis nicht passt, erzeugt genau den.

**Was sich gegenüber 2.490 ändert, ist genau eine Größe: der HORIZONT.**

| | 2.490 (20.09.) | hier |
|---|---|---|
| Zielgröße | `barriere` | `barriere` |
| Lage | `hebel × einstieg` | `hebel × einstieg` |
| Fenster | ab 2023-01-01 | ab 2023-01-01 |
| **Horizont** | **H20** | **H3** |
| Blocklänge | 60 | **15** (`messnorm._block`) |

---

# § 2 Recherche — warum H3 und nicht H20

| | |
|---|---|
| Median-Haltedauer echter Hebelpositionen | **0,30 Tage** (188 Positionen, 2.493) |
| Betrieb rechnet mit | **rund 3 Handelstagen** (2.513-horizont) |
| Alle drei Live-Beiträge registriert auf | **H20** (2.514) |
| `messnorm.HORIZONT_JE_LAGE` seit 24.09. | `('hebel','einstieg') = 3` (2.572) |

⚠️ **2.490 hat die Zielgröße gewechselt, den Horizont nicht** — deshalb
beantwortet es die Frage von 2.291 nicht, die es beantworten sollte
(2.571).

---

# § 3 ✔ Machbarkeit — gerechnet, vor der Messung

| H | Blocklänge | Tage | **aufgelöst** | Anker/Tag | **Blöcke** |
|---|---|---|---|---|---|
| **3** | **15** | 2.184 | **53,7 %** | 87,3 | **145,6** |
| 5 | 15 | 2.326 | 70,9 % | 108,6 | 155,1 |
| 20 (= 2.490) | 60 | 2.396 | 96,9 % | 144,5 | 39,9 |

➤ **H3 ist messbarer als H20**, nicht schlechter: **145,6 Blöcke** gegen
39,9, weil die Blocklänge mit dem Horizont schrumpft.

## ⚠️⚠️ Der Vorbehalt, der dazugehört: die Auflösung **ist** eine Auswahl

Bei H3 fallen **46,3 %** der Anker heraus (bei H20 nur 3,1 %) — sie
erreichen weder Ziel noch Stop im Fenster.

**Und diese Auswahl ist nicht zufällig.** N-52 hat gemessen: *„ruhige
Assets lösen ihre Barrieren öfter auf"* — die Auflösungsquote hängt an
`vola` (+3,1 Punkte). Am 24.09. bestätigt: bei H5 lösen 64,3 % der
ruhigsten und nur 47,9 % der volatilsten Anker auf.

➤ **Die H3-Menge ist also vola-verzerrt.** Das ist kein Grund, nicht zu
messen — aber jedes Ergebnis gilt für *„Anker, die in 3 Tagen auflösen"*,
nicht für alle. **Der Anteil wird bei jedem Kandidaten ausgewiesen.**

---

# § 4 Die Planung

| | |
|---|---|
| **Werkzeug** | `k1c_hebel_barriere.py` — dasselbe wie 2.490, keine Nachbildung |
| **Änderung** | genau eine: `--horizont` ergänzen (heute importiert es `HORIZONT` fest aus `messe_alle_kandidaten`) |
| **Vorgabe** | bleibt **20**, damit ein Aufruf ohne Argument 2.490 weiter bitgleich reproduziert (R-R11) |
| **Menge** | `--menge 20%` — die **selektierte** (F-212). ⚠️ 2.490 lief auf `frei`, und der Befund weist selbst aus, dass das die Kontrolle kippt |
| **Kandidaten** | `funding`, `turnover`, `oi_aenderung`, `schnitt`, `zufall` — unverändert |
| **Saat** | Vorgabe 20260909, plus Saatprobe |

## 4.1 Was zusätzlich mitläuft

1. **R-R11 zuerst:** derselbe Lauf mit `--horizont 20` muss 2.490
   reproduzieren. Ohne das wird nichts umgestoßen.
2. **Die Kontrolle `zufall`** muss auf H3 sauber bleiben — 2.490 ist
   genau daran fast gescheitert (auf `frei` trug sie).
3. **Der Auflösungsanteil** je Kandidat.
4. **Die Warnung aus 2.572** darf bei `--horizont 3` **nicht** erscheinen
   und bei `--horizont 20` **schon** — das ist die Gegenprobe, dass die
   Norm greift.

---

# § 5 Die Entscheidungsregel — vor der Messung

| Ergebnis auf H3 | Entscheidung |
|---|---|
| **R-R11 fällt** (H20 reproduziert 2.490 nicht) | ⛔ **Stopp.** Dann ist das Werkzeug das Problem, nicht der Horizont |
| **Ein Beitrag trägt auf `barriere`/H3**, Kontrolle sauber | ✔ **Der Hebel bekommt seine eigene Bewertung** — wortgleich nach 2.291. Danach: eigene Stufen, eigene Schwelle (R-R9), Betriebsprüfung |
| **Keiner trägt**, Kontrolle sauber, Trennschärfe ausreichend | ⛔ **2.490 gilt weiter** — dann war der Horizont nicht die Ursache, und der Hebel bekommt keine eigene Bewertung |
| **Keiner trägt, aber die Trennschärfe reicht nicht** | ⚠️ **nichts entschieden** — Datendecke, kein Nullbefund |
| **Die Kontrolle `zufall` trägt** | ⛔ **Lauf ungültig** (wie 2.490 auf `frei`) |

⚠️⚠️ **Diese Festlegung wird nicht nachverhandelt.** Insbesondere Zeile 3:
ein Nullbefund ist hier **das erwartete Ergebnis**, nicht das Scheitern
der Arbeit.

## 5.1 Die Vorhersage, vor dem Lauf (Methodik 2.80)

**Erwartung: die Beiträge tragen auf H3 NICHT.** Begründung: sie fallen
auf kurzen Horizonten stark ab (2.514: `funding` von 2,48 auf 0,23
Punkte, **Faktor 11**), und das Barrierensystem hat brutto
Erwartungswert null.

**Gegenthese:** sie tragen — dann wäre der Hebel begründbar steuerbar,
und 2.490 war ein Horizont-Artefakt.

⚠️ **Ein Nullbefund ist hier die Regel, kein Ausreißer** — so stand es
schon im Kopf von `k1c_hebel_barriere.py` am 09.09.

---

# § 6 Was diese Messung **nicht** entscheidet

- **Nicht**, ob ein Hebel wirtschaftlich wäre. `barriere` ist *„blind für
  wieviel ist zu holen"* — gemessen wird nur die **Trefferquoten­verschiebung**.
- **Nicht**, welche Geometrie richtig ist. Das ist die Frage aus
  Konzept-Schritt 3.
- **Nicht**, ob M1 ohne Hebel definierbar ist. Das bleibt beim Nutzer.

---

# ERGEBNIS — 24.09.2026

## ✔✔ R-R11 zuerst: bitgleich reproduziert

Mit der Vorgabe H20 kommen **exakt** die Zahlen von 2.490: funding +0,0013 ·
turnover +0,0028 · oi_aenderung +0,0030 [+0,0001 … +0,0067] · schnitt
+0,0023 · zufall −0,0009. **Der neue Schalter ändert bei der Vorgabe nichts.**

## ➤➤➤ Das Ergebnis auf H3

| Kandidat | Menge | Wirkung | Band | Blöcke | Urteil |
|---|---|---|---|---|---|
| `funding` | 20 % | +0,0002 | | 78 | trägt nicht |
| `turnover` | 50 % | +0,0040 | [−0,0004 … +0,0085] | 58 | trägt nicht |
| **`oi_aenderung`** | 50 % | **+0,0069** | **[+0,0031 … +0,0108]** | **76** | **✔ TRÄGT** |
| `schnitt` | 10 % | +0,0066 | | 51 | nicht trennbar |
| **`zufall`** | 10 % | −0,0034 | | 81 | ✔ **Kontrolle sauber** |

✔ **Saatprobe bestanden:** drei Saaten, vier Nachkommastellen identisch.

## ⚠️⚠️ Was genau belegt ist — die Unterscheidung zählt

**Belegt:** auf H3 ist die Wirkung von `oi_aenderung` von der **Null** und
von der **Trennschärfe** zu trennen — auf H20 nicht (dort +0,0030 gegen
eine Trennschärfe von 0,0098). **Das ist ein Urteilsunterschied.**

⛔ **Nicht belegt:** ein **Wirkungs**unterschied. Die Bänder überlappen
([+0,0031 … +0,0108] gegen [+0,0001 … +0,0067]).

➤ Die Bedingung von 2.291 fragt nach dem **Urteil** — *„trägt er dort
anders"* — und das tut er.

## ✔ Entscheidung nach § 5

> **Der Hebel bekommt seine eigene Bewertung.**

2.490 ist damit nicht falsch, aber **überholt**: es hat die Frage auf dem
Spot-Horizont gestellt.

## ⚠️ Drei Vorbehalte

1. **Die Auflösung ist eine Auswahl:** bei H3 fallen **48,3 %** der Anker
   heraus (H20: 3,1 %), und sie ist **vola-verzerrt**. Jedes Ergebnis gilt
   für *„Anker, die in 3 Tagen auflösen"*.
2. `oi_aenderung` ist als **Schalter** geführt (F-168) — die Bauform ist
   vorgezeichnet, aber die Stufen sind auf H20 kalibriert.
3. `barriere` ist blind für *„wieviel ist zu holen"* — gemessen ist die
   **Trefferquotenverschiebung**, nicht die Wirtschaftlichkeit.

## ✔ Nebenbefund: es gibt **zwei** Messanlagen

`messnorm.pruefe` und `messnorm_auswahl.pruefe_auswahl` rechnen unabhängig
— die zweite ruft die erste **nicht**. Meine Horizontwarnung aus 2.572
stand nur in der ersten und hätte **genau die Hebelläufe verfehlt**.
Behoben: `messnorm.warne_horizont`, beide Anlagen rufen sie. Nachgewiesen:
H20 → fünf Warnungen, H3 → keine.

Befund **2.573-hebel-eigene-bewertung**.
