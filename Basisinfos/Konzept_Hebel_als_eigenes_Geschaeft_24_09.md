# Konzept — Spot, Hebel und Akkumulation als DREI Geschäfte

**24.09.2026.** Nutzerentscheidung: *„Spot bleibt vorerst als eigener
offener Punkt. Und Hebel muss neu gedacht werden."* · Auftrag:
*„bevor wir irgendetwas anfassen muss ein tragfähiger Plan stehen."*

Erweitert auf Nutzerhinweis: *„könntest du die Architekturfrage gleich
für alle drei beantworten — Spot, Hebel und Akkumulation"*.
Reihenfolge nach Nutzervorgabe: **1. Hebel · 2. Akkumulation · 3. Spot.**

Grundlage: 2.571 (Horizont), 2.574 (vier Blocker), 2.576 (B0).

> ⛔ **Dieses Dokument baut nichts. Es beantwortet die zwei Fragen, die
> vor dem Bauen zu klären sind — am Code geprüft, nicht geschätzt.**

---

# § 1 Der Befund, aus dem alles folgt

> **Der Hebel wird heute nicht gesucht. Er fällt an.**

| | |
|---|---|
| Die Kette läuft als | `spot × einstieg` (2.548) |
| `instrument` ist für Krypto | **immer `spot`** — Quelltext `rollen_lauf.py:2424` |
| Das Etikett `hebel` entsteht | **nachträglich** aus der Geometrie (2.174) |
| Eine eigene Hebelschiene | gab es: `agent/krypto/hebel_analyst.py`, `hebel_screening.py` — **seit 10.08. still**, begründet stillgelegt (2.343), **nicht ersetzt** |

**Vorhanden ist die Hebel-AUSFÜHRUNG** (`hebel_abgleich`, `hebel_aggregat`,
`hebelfuehrung`). **Es fehlt die Hebel-ENTSTEHUNG.**

➤ **Null Hebelsignale sind keine Datenlücke, sondern die logische Folge:**
wer nur nach Spot sucht, findet Hebel als Zufallsprodukt.

---

# § 2 ⚠️⚠️⚠️ FRAGE 1 — für ALLE DREI: Spot, Hebel, Akkumulation

## 2.0 Zuerst: die drei liegen **nicht auf derselben Achse**

Das ist der Grund, warum eine Antwort „für Hebel" zu kurz greift:

| Geschäft | Lage | Achse |
|---|---|---|
| Spot-Einstieg | `spot × einstieg` | — |
| **Akkumulation** | `spot × ` **`akkumulation`** | **Strategie** |
| **Hebel** | **`hebel`** ` × einstieg` | **Instrument** |

➤ `INSTRUMENTE_JE_GRUPPE` allein reicht deshalb **nicht**. Die Einheit ist
die **Lage** — das Paar `(instrument, strategie)`, genau wie in
`ERLAUBTE_PAARE`, `ZIELGROESSE_JE_LAGE` und `HORIZONT_JE_LAGE`.

## 2.1 ⚠️⚠️ Und jetzt der Befund, der alle drei erklärt

**Wie entsteht jede Lage heute?**

| Lage | entsteht aus | Zielgröße | Horizont | Signale |
|---|---|---|---|---|
| `spot × einstieg` | **Vorgabe** — der Rückfall für alles | `bewegung_r` | 20 | **3.513** |
| `spot × akkumulation` | ✔ **Nutzerschalter je Asset** (`asset_dca_settings.dca_erlaubt`) | `verbilligung` | 90 | **0** |
| `hebel × einstieg` | ⛔ **der Geometrie, nachträglich** (2.174) | `barriere` | 3 | **0** |

> **Die Akkumulation ist eine gewollte Lage. Der Hebel ist ein Ergebnis.
> Das ist der Unterschied — und er ist die ganze Architekturfrage.**

`handelsauftrag.strategie_fuer()` sagt es selbst: *„DIE ZUORDNUNG KOMMT AUS
DEM SCHALTER DES NUTZERS, nicht aus einer Liste im Code."* Für die
Akkumulation **steht die Lage vor dem Lauf fest.** Beim Hebel entsteht sie
danach.

## 2.2 ➤ Daraus die eine Regel, die für alle drei gilt

> ## **Die Lage ist EINGANG, nicht AUSGANG.**

| | heute | soll |
|---|---|---|
| Akkumulation | ✔ **erfüllt** (Schalter) | — |
| Hebel | ⛔ verletzt (Geometrie entscheidet) | Lage vor dem Lauf |
| Spot | ⚠️ **Rückfall** — alles, was nicht anders markiert ist | eigene Absicht |

⚠️⚠️ **Die Akkumulation ist damit das VORBILD, nicht der Problemfall.**
Ihre null Signale haben eine **andere** Ursache: nicht die Lage, sondern
der **Weg** dorthin (2.540). Sie hat die Architektur, aber nicht die Kette.

➤ **Der Hebel hat weder noch.** Deshalb ist er zuerst dran.

## 2.3 Die Asymmetrie hat einen Namen

Die Kette unterscheidet **je Symbol** schon heute die **Strategie**:

```python
def _strategie_fuer(aktion, hat_bestand):
    ... "akkumulation" / "ausstieg" / "fuehrung" / "einstieg"
```

Ein Wert im Bestand wird als `fuehrung` geführt, ein Verkauf als `ausstieg`.
**Das Instrument dagegen steht fest.**

> ⚠️ **Die Kette ist also nicht monolithisch — sie kann Lagen. Sie kann nur
> keine INSTRUMENTE.** Das ist eine Asymmetrie ohne fachlichen Grund.

## 2.4 Und die Norm kennt die Lage bereits

| Baustein | Stand |
|---|---|
| `messnorm.ZIELGROESSE_JE_LAGE` | ✔ spot→`bewegung_r`, hebel→`barriere` |
| `messnorm.HORIZONT_JE_LAGE` | ✔ seit 24.09. (spot 20, hebel 3) |
| `Beitrag.instrumente` + `_gilt()` | ✔ gebaut, **ungenutzt** |
| `handelsauftrag.ERLAUBTE_PAARE` | ✔ `hebel: (einstieg, swing)` |

➤ **Die MESSUNG ist lagerichtig. Der BETRIEB ist es nicht.** Genau dort
verläuft die Bruchlinie.

---

# § 3 ⚠️⚠️⚠️ FRAGE 2 — Geht es ohne massiven Umbau? **Ja. Die Struktur existiert schon.**

## 3.1 Der Fund

`agent/assetklassen.py:61` und `:167`:

```python
INSTRUMENTE_JE_GRUPPE = {
    "krypto": ("spot",),          # ← ein TUPEL
    "hedge":  ("absicherung",),
}
...
for instrument in INSTRUMENTE_JE_GRUPPE.get(g, ("spot",)):   # die Kette ITERIERT
```

> **Die Kette ist gebaut, um mehrere Instrumente je Gruppe zu führen. Für
> Krypto steht dort ein einziger Eintrag.**

➤ **`("spot", "hebel")` ist keine Architekturänderung, sondern das
Benutzen einer vorhandenen Schleife.**

## 3.1a ⚠️ Aber die Schleife muss über LAGEN laufen, nicht über Instrumente

Sonst bleibt die **Akkumulation** außen vor (§ 2.0). Die saubere Form:

```python
LAGEN_JE_GRUPPE = {
    "krypto": (("spot", "einstieg"), ("spot", "akkumulation"),
               ("hebel", "einstieg")),
    "hedge":  (("absicherung", "einstieg"),),
}
```

✔ Die Paare sind **schon geprüft** — `ERLAUBTE_PAARE` kennt sie, und
`pruefe_auftrag()` wirft bei einem unvorgesehenen Paar.

⚠️⚠️ **Zwei Arten von Strategie, die nicht vermischt werden dürfen:**

| | Beispiel | Herkunft | bleibt |
|---|---|---|---|
| **Absicht** | `einstieg`, `akkumulation` | gewollt — Schalter oder Lagenliste | ➤ **gehört in die Schleife** |
| **Anlass** | `fuehrung`, `ausstieg` | folgt aus dem **Bestand**, je Symbol | ✔ **bleibt dynamisch** — `_phase_fuer()` ist dort richtig |

⛔ **Wer beides in eine Liste zwingt, bricht die Verkaufsseite.** Ein
gehaltener Wert muss weiter zur `fuehrung` werden können, egal welche
Lage der Lauf trägt.

## 3.2 Warum das bisher zu teuer war — und warum das nicht mehr gilt

Der zweite Lauf wurde mit **S6b** entfernt. Der bekannte Einwand ist das
**LLM-Kontingent**: 500/Tag je Modell, Betrieb im Mittel 245, Spitze 565
(2.459). Verdoppeln geht nicht.

✔✔ **Gemessen am 24.09. — und das ändert die Lage:**

```
prompt_fuer("spot", "einstieg") == prompt_fuer("hebel", "einstieg")   →  True
_HANDELN["spot"] is _HANDELN["hebel"]                                 →  dieselbe Konstante
```

**Der LLM-Prompt ist für Spot und Hebel bitgleich.** Unterschieden wird
nur die **Absicherung**.

➤ **Die teure Ressource muss NICHT verdoppelt werden.** Dieselbe Frage
zweimal zu stellen wäre nicht nur teuer, sondern sinnlos — die Antwort
ist dieselbe. Sie wird **einmal geholt und je (Symbol, Tag) geteilt.**

⚠️⚠️ **Das ist zugleich ein Mangel, der ins Konzept gehört:** das LLM weiß
nicht, ob es einen Trade über 20 Tage oder über 0,3 Tage beurteilt. Der
eigene Docstring warnt davor — *„er würde einen Hebel-Trade wie einen
Spot-Trade bewerten"* — und genau das passiert. **Aber es ist ein Thema
für Block L-ROLLEN, kein Blocker für die Architektur.**

## 3.3 Was billig ist und was teuer — die Schnittlinie am Code

| Zeile | Stufe | je Lage nötig? | Kosten |
|---|---|---|---|
| 1303–1376 | auftrag, fakten, lagebild | nein — dieselbe Kursreihe | teuer (Daten) |
| 1499–1555 | anlass, auswahl | **offen** (§ 5) | mittel |
| **1593–1613** | **terminmarkt** | ⚠️ **JA — heute lagefremd** | billig |
| 1624–1652 | wiederholung | ✔ kennt `instrument` bereits | billig |
| **1734–1778** | **urteil (LLM)** | **nein — Prompt bitgleich** | ⛔ **teuer** |
| 1941–2073 | aktion | nein | billig |
| 2130–2604 | Quote, Geometrie, Bewertung, Entscheider | **ja** | billig |

➤ **Alles Lageabhängige ist billig. Das einzig Teure ist lageunabhängig.**
Günstiger könnte die Schnittlinie nicht liegen.

---

# § 4 Die drei Wege, fachlich bewertet

| | Weg | Aufwand | Urteil |
|---|---|---|---|
| **A** | Zwei volle Läufe | gering im Code | ⛔ **scheitert am LLM-Kontingent**, wenn der Vorlauf nicht geteilt wird |
| **B** | Eine Kette, Verzweigung ab Stufe 9 | **hoch** | ⚠️ `Durchlauf` zählt je `(symbol, stufe)` — für zwei Spuren müsste der **Trichterzähler** umgebaut werden. Das ist der massive Umbau, den du vermeiden willst |
| **C** | Kette zu 100 % auf Hebel | gering im Code | ⛔ **siehe § 4.1** |
| **✔ D** | **`INSTRUMENTE_JE_GRUPPE` nutzen + Vorlauf teilen** | **gering** | ✔ **empfohlen** |

## 4.1 ⚠️ Weg C — die Auswirkungen, die du nicht kennst

Du hast selbst gesagt, du kennst sie nicht. Hier sind sie:

| | |
|---|---|
| **Der Bestand ist Spot** | `fuehrung` und `ausstieg` laufen über `spot`. Eine reine Hebelkette **beurteilt das vorhandene Portfolio nicht mehr** — keine Verkaufs-, Nachkauf- oder Haltesignale. Der Code warnt an der Auswahl-Stufe wörtlich: *„Ohne diese Ausnahme fällt die gesamte Verkaufsseite aus der Kette."* |
| **Die Akkumulation fällt weg** | BTC/ETH/SOL laufen als `spot × akkumulation` |
| **Alles auf eine nie erprobte Karte** | `hebel` hat **null Signale** in der Produktion; jede Hebelaussage trägt `simuliert=True` |
| **Die Absicherung** | unberührt — eigene Gruppe `hedge` |

✔ **C hat aber einen echten Vorteil, und der zählt:** volle Konsistenz. Ein
Horizont, eine Zielgröße, keine Lage-Verwechslung. Die Fehler dieser Woche
(2.571, 2.574, 2.576) wären strukturell unmöglich.

➤ **Weg D gibt diesen Vorteil auch** — denn dort hat **jede Lage ihren
eigenen, in sich konsistenten Lauf**. Nur eben zwei davon statt einem.

## 4.2 Warum D und nicht B

B verzweigt **innerhalb** eines Laufs. Das verlangt, dass jede Stufe, jeder
Zähler und jedes Protokoll zwei Zustände trägt — und genau dort entstehen
die stillen Fehler, die dieses Projekt teuer bezahlt hat.

D lässt **jeden Lauf für sich einfach bleiben.** Geteilt wird nur, was
nachweislich identisch ist (Kursreihe, Lagebild, LLM-Antwort).

> **Die Lage wird zum Parameter, nicht zur Verzweigung.**

---

# § 5 ⚠️ Was D NICHT löst — die vier offenen Ebenen

D macht den Hebel zu einem **eigenen Lauf**. Es sagt nicht, **wonach er
sucht**. Das bleibt offen und ist der eigentliche Inhalt von
*„Hebel neu denken"*:

| Ebene | Frage | Stand |
|---|---|---|
| **Anlass** | Wodurch entsteht ein Hebeltrade? | ⛔ **die Kernlücke** — heute: die Spot-Auswahl |
| **Auswahl** | Welche Assets? Liquidität und Bewegung statt Rang? | ⛔ offen |
| **Trichter** | Stufe 6 ist auf **H20/`bewegung_r`** gemessen (F-168) und greift ohne Instrumentbedingung | ⛔ **belegt lagefremd** |
| **Takt** | Median-Haltedauer **0,3 Tage** gegen eine **tägliche** Messbasis. Terminmarkt liegt **stündlich** vor | ⚠️ **ungeprüfte Hypothese** |

⚠️⚠️ **Die Trichterfrage löst sich mit D teilweise von selbst:** im
Hebel-Lauf ist `instrument` echt `hebel`, also kann Stufe 6 lageabhängig
entscheiden — ohne Sonderlogik, nur mit einer Bedingung.

⚠️ **Die Anlassfrage löst sich NICHT von selbst.** Ein zweiter Lauf, der
dieselbe Spot-Auswahl bekommt, findet dieselben Assets.

---

# § 6 Die Reihenfolge — und diesmal stimmt sie

Diese Woche wurde zweimal gemessen, bevor die Frage richtig stand
(2.573 auf einer Menge, die es nicht gibt; B0 in der falschen
Reihenfolge). **Deshalb hier: Trichter vor Beitrag, Messung vor Bau.**

## 6.0 ⭐ Die Reihenfolge der drei Geschäfte — **Nutzervorgabe 24.09.**

> **1. Hebel · 2. Akkumulation · 3. Spot**
> *(„Spot wird der größte Brocken, wenn es funktionieren soll")*

✔ **Fachlich stimmig, und zwar aus drei unabhängigen Gründen:**

| | |
|---|---|
| **Hebel zuerst** | er hat als einziger **weder** Architektur **noch** Weg (§ 2.2). Und die Lagenschleife wird an ihm gebaut — die Akkumulation erbt sie dann |
| **Akkumulation danach** | sie hat die **Architektur schon** (Schalter) und braucht nur den Weg (2.540). Der kleinste Schritt von den dreien |
| **Spot zuletzt** | er ist der **Rückfall für alles**. Ihn anzufassen berührt 3.513 Signale, die Verkaufsseite und M1-Kriterium 1. Zuletzt ist die einzig vertretbare Stelle |

⚠️⚠️ **Und es gibt einen vierten Grund, der stärker ist als die anderen
drei:** der Hebel hat **null Signale**. Was dort schiefgeht, kostet nichts.
Ein Fehler in Spot trifft den laufenden Betrieb.

➤ **Der Hebel ist die risikoärmste Stelle, um die Lagenarchitektur zu
bauen — und zugleich die, die sie am dringendsten braucht.**

## 6.1 Die Schritte

| | Schritt | Art |
|---|---|---|
| **0** | **Dieses Konzept abstimmen** | Entscheidung |
| **1** | **F-168 spiegelbildlich messen** — die OI-Sperre auf `hebel × einstieg`, H3, `barriere`. Trägt sie dort auch, oder **negativ**? | **Messung** |
| **2** | **Die Lage `absicherung` als Vorbild prüfen** — sie läuft bereits als eigenes Instrument über dieselbe Kette. Was funktioniert dort, was nicht? | Voranalyse |
| **3** | **Den geteilten Vorlauf nachweisen** — dass Kursreihe, Lagebild und LLM-Antwort je (Symbol, Tag) wirklich identisch sind | **Messung am Seiteneffekt** |
| **4** | Erst dann: die Lagenschleife, zunächst mit `("spot","einstieg")` + `("hebel","einstieg")` | Bau |
| **5** | Anlass und Auswahl für den Hebel — der eigentliche Inhalt | offen |
| **6** | **Akkumulation** in die Lagenschleife — sie erbt die Architektur, offen bleibt ihr **Weg** (2.540) | danach |
| **7** | **Spot neu denken** — der größte Brocken, mit voller Betriebswirkung | zuletzt |

⚠️ **Schritt 1 berührt `spot × einstieg` NICHT** und lässt M1-Kriterium 1
unangetastet.

⚠️⚠️ **Schritt 2 ist der wichtigste und billigste:** `absicherung` ist der
lebende Beweis, dass die Kette ein zweites Instrument führen kann. Was
dort schiefgeht, ginge beim Hebel genauso schief.

---

# § 7 Was das für M1 heißt

| | |
|---|---|
| **Kriterium 1** Spot | ✔ gemessen — ⚠️ aber **eigener offener Punkt** (Nutzerentscheidung 24.09.), Wirksamkeit unbelegt |
| **Kriterium 2** Hebel | ⛔ **nicht erfüllbar**, solange der Hebel kein eigenes Geschäft ist |

> ⚠️⚠️ **M1 in seiner heutigen Definition ist damit kein Nahziel mehr.**
> Es heißt *„dann wird wieder investiert"* — und sollte nicht an einer
> Definition hängen, die von den Befunden überholt wurde.

➤ **Drei Wege, Nutzerentscheidung:** M1 auf Spot beschränken · M1
verschieben, bis der Hebel steht · M1 neu fassen.

⛔ **Keiner davon wird nebenbei entschieden.**
