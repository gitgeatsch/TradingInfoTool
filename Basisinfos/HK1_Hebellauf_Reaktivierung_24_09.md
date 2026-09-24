# H-K1 — den Hebel-Lauf reaktivieren

**24.09.2026.** Nutzerauftrag: *„wir machen jetzt und zuerst den Hebel
Einstieg von Anfang bis zum Ende — Ganze Ablaufkette mit LLM — getestet und
simuliert."*

⚠️⚠️ **Nutzerwarnung, wörtlich:** *„es gab den Hebel bereits als eigenen
Ablauf diesen hast du zurückgebaut — das wird eine Operation der Operation …
bitte vorsichtig und langsam und genau arbeiten"*

➤ **Berechtigt.** Der Rückbau war **S6b am 22.08.2026** (nicht in dieser
Sitzung) — was ihn **älter und breiter** macht, nicht harmloser. Dieses Blatt
ist die vollständige Spurensuche, bevor irgendetwas committet wird.

---

# § 1 Der Befund, der den Auftrag auslöste

**Die Ablaufkette erzeugt heute keinen Hebel-Einstieg.**

`assetklassen.zellen()` liefert **43 × `krypto × hebel × einstieg`**.
`rollen_lauf.py` warf sie eine Zeile später weg:

```python
if _z["strategie"] not in _vorhandene:    # nur die STRATEGIE
    _vorhandene.append(_z["strategie"])   # das INSTRUMENT fiel weg
```

Für LINK setzt `spot × einstieg` die Strategie „einstieg"; `hebel × einstieg`
bringt dieselbe — **wird verworfen**. Kein eigener Modellaufruf, kein eigenes
Signal, keine eigene Mail.

**Begründung im Code, datiert:** F-163, 01.09. — *„gebührenfrei liefert
`hebel × einstieg` dasselbe Potential wie `spot × einstieg`, es wäre also ein
ZWEITES, identisches Signal."*

## 1.1 Warum diese Begründung entfallen ist

| seit 24.09. | |
|---|---|
| **Kapselung** | Befund 2.579 — der Hebel hat eine eigene Bewertungsachse |
| **Drei Geschäfte** | Richtungsentscheid — eigene Positionsführung |
| **Eigene Dimension** | Vorabfestlegung 10 misst **6–72 Stunden**, Spot **H20 Tage** |

➤ **Zwei Dimensionen sind kein zweites identisches Signal.**

---

# § 2 Der Eingriff — zwei Stellen

| | Datei | Änderung |
|---|---|---|
| **E1** | `agent/assetklassen.py` | `INSTRUMENTE_JE_GRUPPE["krypto"] = ("spot", "hebel")` |
| **E2** | `agent/rollen_lauf.py` | Zellensammlung filtert auf das **Lauf-Instrument** |

**E2 ist nicht optional:** ohne ihn führt der Hebel-Lauf für BTC auch
`akkumulation` — und `hebel × akkumulation` steht **nicht** in
`ERLAUBTE_PAARE`. `handelsauftrag.pruefe()` würde dort werfen, zu Recht.

⚠️ Der Filter steht **vor** der Sperrzählung, sonst bekäme jede gesperrte
Zelle bei zwei Läufen zwei Zeilen und die Sperrmenge wäre verdoppelt (B5).

---

# § 3 ⭐ Die Spurensuche — alle zehn S6b-Stellen, einzeln gelesen

> **Das Ergebnis ist besser als befürchtet: S6b hat konsequent auf
> „die SACHFRAGE statt das Lauf-Etikett" umgestellt, nicht auf
> „Hebel gibt es nicht".** Genau das macht die Reaktivierung tragfähig.

| # | Stelle | umgestellt auf | mit zwei Läufen |
|---|---|---|---|
| 1 | `empfehlung_vertrag:226` | Richtungspflicht **instrumentunabhängig** | ✔ bleibt richtig |
| 2 | `signal_abbildung:609` | Spalte folgt dem **Ergebnis** (`hebel > 1.0`) | ⚠️ **siehe § 4** |
| 3 | `lagebeschreibung:531` | Rate an alle mit `hebel_handelbar(klasse)` | ✔ — der benannte **Preis entfällt** sogar |
| 4 | `trefferbilanz:210` | Kostentier folgt dem **Hebelwert** | ✔ bleibt richtig |
| 5 | `positionsfuehrung:177` | liest **beide** Tabellen | ✔ — S6b nannte den Fall selbst: *„es kehrt zurück"* |
| 6 | `entscheidungsrechnung:915` | `hebel_handelbar`, Rückfall Instrument | ✔ bleibt richtig |
| 7 | `entscheidungsrechnung:1009` | Etikett aus der **Zahl** | ⚠️⚠️ **REGRESSION — § 4** |
| 8 | `entscheidungsrechnung:1235` | `etikett != "hebel"` | ✔ bleibt richtig |
| 9 | `betraege:63` | **eine** Zahl je Gruppe × Strategie | ⚠️ **offene Entscheidung — § 5** |
| 10 | `pruefe_pakete:6695` | prüft **beide Welten** | ⚠️ **wird rot — § 6** |

---

# § 4 ⚠️⚠️ DIE EINE ECHTE REGRESSION

`entscheidungsrechnung.py:1009` sagt im Klartext, warum:

> *„Das Instrument war der verlässliche Marker, **WEIL ES ZWEI LÄUFE GAB.**
> [...] weil ein echter Hebel-Trade, dessen sicherer Faktor auf 1,0 fällt
> (KAITO 9,9 %, CAT 17,4 % Stop), sonst **als Spot in der Datenbank
> landete**."*

**Der Fall, der zurückkehrt:** ein Signal aus dem Hebel-Lauf, dessen
`max_safe_hebel()` auf 1,0 gedrückt wird, bekommt das Etikett `spot`. Folgen:

| | |
|---|---|
| `toepfe.sql_bedingung` | trennt an `hebel IS NOT NULL` → **fällt aus dem Hebel-Topf** |
| Der Topf ist ein **Risikodeckel** | Nutzerentscheidung 13.08.: *„gesamt 3.000 EUR, eine Position vorerst 1.000"* — der Hebel ist die einzige Position, die **mehr verlieren kann als ihren Einsatz** |
| `wiederholung` | fällt aus dem **Hebel-Cooldown** |
| Die Mail | trägt trotzdem den Betreff **„EROEFFNEN (Hebel)"** |

⛔ **Eine 3.000-EUR-Obergrenze, die nichts sieht.**

➤ **Zu entscheiden, nicht zu raten:** soll bei zwei Läufen das Instrument
wieder mitentscheiden (`etikett = "hebel" wenn hebel nötig ODER Lauf ist
hebel`), oder bleibt es beim Wert? **Nutzerentscheidung.**

---

# § 5 ⚠️ Die offene Frage aus `betraege.py`

Vor S6b: **800 EUR (spot) / 1.000 EUR (hebel)**. S6b schrieb: *„technisch
nicht mehr darstellbar, es gibt genau eine Zahl je Gruppe und Strategie."*

➤ **Mit zwei Läufen ist sie wieder darstellbar.** Das ist aber eine
**Nutzerentscheidung über Geld**, kein Automatismus — und sie wird hier
**nicht** beiläufig mitgemacht.

---

# § 6 ⚠️ Die Suite-Prüfung, die nachgezogen werden muss

`pruefe_pakete.py:6695` prüft **beide Welten** — vorbildlich. Aber die erste
prüft die Ein-Lauf-Welt aus dem **Ist-Zustand** heraus:

```python
pruefe(P, "EIN Lauf je Gruppe: das Urteil sperrt, egal in welchem Topf", ...)
_echt28 = dict(_AK28.INSTRUMENTE_JE_GRUPPE)
_AK28.INSTRUMENTE_JE_GRUPPE["krypto"] = ("spot", "hebel")   # zweite Welt
```

➤ **Mit E1 prüft die erste jetzt die falsche Welt und wird rot.** Sie muss
**beide** Welten ausdrücklich setzen statt eine anzunehmen — genau die
stehende Regel *„eine Prüfung, die Zustände aufzählt, veraltet still"*.

⚠️ **Das ist keine Regression, sondern der Beweis, dass E1 wirkt.**

---

# § 7 Was der erste Durchlauf zeigt

`python simuliere_kette.py --gruppe krypto`, nach E1+E2:

```
### krypto/spot    5 Symbole, 2 Modellaufrufe
### krypto/hebel   7 Symbole, 0 Modellaufrufe    ← der Lauf EXISTIERT
ABDECKUNG:  gelaufen krypto/spot · gelaufen krypto/hebel
```

✔ **Der Hebel-Lauf läuft.** ⛔ **Aber es kommt nichts durch:**

```
gehoert zu den besten k der Gruppe   0   (6 verloren)  <- hier
      1x Rang 2 von 7 nach der Entwicklung der letzten 250 Handelstage
```

➤ ⚠️⚠️ **Die Auswahl rangt nach 250 HANDELSTAGEN — für einen Hebeltrade auf
6–72 STUNDEN.** Dieselbe Dimensionsverwechslung, die schon bei H20 den Hebel
zerlegt hat. **Das ist der nächste Punkt, und er ist eine Messfrage,
kein Bau.**

---

# § 8 Stand und was NICHT passiert ist

| | |
|---|---|
| **Committet** | ⛔ **nichts.** Kein Push, Betrieb unberührt |
| **Simulation** | lief auf einer **Kopie** im Scratchpad |
| **Bewertung** | ⛔ **nicht angefasst** — der Umbau ist am 24.09. abgesagt (B0). Der Hebel bekommt eine eigene ZELLE, keine eigene BEWERTUNG |
| **Cooldown/Takt** | ⛔ nicht angefasst — die Trennung schaltet sich über `INSTRUMENTE_JE_GRUPPE` von selbst ein, mehr nicht |
| **Offen** | § 4 (Etikett), § 5 (Beträge), § 6 (Suite), § 7 (Auswahl-Dimension) |
