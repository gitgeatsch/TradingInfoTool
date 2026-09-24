# Vorabfestlegung 11 — P-1: das Rangfenster für den Hebel

**24.09.2026, geschrieben VOR der Messung.**

**Nutzeraufträge:** *„ja Vorabfestlegung für P-1 aufsetzen - prüfen und
gegenprüfen"* · *„wenn du keine Lösung über die Messung findest brauchen wir
eine Alternative"* · *„der HEBEL MUSS dynamisch aus der Bewertung entstehen"*

---

# § 1 Der Befund, der die Frage stellt

Im Durchlauf vom 24.09. fiel im Hebel-Lauf **alles** an einer Stufe:

```
gehoert zu den besten k der Gruppe   0   (6 verloren)
      1x Rang 2 von 7 nach der Entwicklung der letzten 250 Handelstage
```

**Die Auswahlstufe** (`agent/auswahl.py`):

| | |
|---|---|
| `RUECKBLICK_TAGE` | **250** Handelstage |
| `K_GROSS` | **2** — bei 43 Krypto-Symbolen kommen **2** durch |
| Begründung im Code | *„messe_drift 19.08.: **250/5** mit t = 3,20 bei empirischer Schwelle 3,05"* |

⚠️⚠️ **Das „250/5" ist der Kern:** der Rückblick wurde gegen einen
**5-Tage-Horizont** gemessen. Der Hebeltrade liegt bei **6–72 Stunden**
(0,25 bis 3 Tage). **Ob 250 dort trägt, ist nie gemessen worden.**

⚠️ Es ist damit **dieselbe Dimensionsverwechslung** wie bei H20 — und sie
sitzt an einer Stufe, die **vor** jedem Modellaufruf sperrt.

---

# § 2 ⚠️⚠️ Die Frage — genau gestellt

> **Über welchen Rückblick geordnet trennt eine Rangliste die künftige
> Entwicklung auf 6 bis 72 Stunden?**

**Und ausdrücklich NICHT:** „ist die Auswahl gut?" Eine Auswahl ist gut oder
schlecht **relativ zu einem Horizont**; ohne ihn ist die Frage nicht
beantwortbar.

## 2.1 Das Werkzeug steht — es wird erweitert, nicht neu gebaut

`messe_drift.py` (19.08.) beantwortet **genau diese** Frage und bringt die
Methodik mit:

| | |
|---|---|
| **Rangliste quer über die Symbole am selben Tag** | nicht der Mittelwert über die Klasse — *„Krypto steigt" ist keine Auswahl* |
| **Signifikanz über TERMINE, nicht Anker** | 32 Symbole an 733 Tagen sind keine 23.000 unabhängigen Fälle |
| **Newey-West** (Bartlett, Lag = Überlappung) | sonst ist jeder überlappende Vorwärtsertrag doppelt gezählt |

⚠️ **Stehende Regel:** *alte Werkzeuge laufen lassen, nicht nur Register
lesen.* Ein neues Werkzeug hier wäre die nächste Stelle, an der zwei
Rechnungen auseinanderlaufen.

---

# § 3 ⭐ R-R11 — die Reproduktion kommt ZUERST

> **Bevor irgendetwas über kurze Horizonte behauptet wird, muss die Messung
> `250/5` mit `t = 3,20` reproduzieren.**

| | |
|---|---|
| **Gelingt es** | die Anlage ist geeicht, die neuen Zahlen sind vergleichbar |
| ⛔ **Gelingt es nicht** | **Abbruch.** Dann ist die Stundenrechnung oder die Basis das Problem, und jede Aussage über 6 h wäre auf Sand gebaut |

⚠️ Reproduziert wird auf der **Tagesbasis**, mit der es gemessen wurde —
nicht auf der neuen Stundenbasis. Wer die Basis wechselt und ein anderes
Ergebnis bekommt, hat nichts widerlegt.

---

# § 4 Die Achsen

| | |
|---|---|
| **Rückblick** | 6 h · 24 h · 72 h · 168 h (1 Wo) · 720 h (30 T) · **250 Handelstage** (der heutige Wert, als Anker) |
| **Horizont** | **6 h · 12 h · 24 h · 48 h · 72 h** — dieselben wie Vorabfestlegung 10, plus **5 Tage** als R-R11-Anker |

⚠️ **Der heutige Wert läuft in JEDER Zeile mit.** Ohne ihn ist nicht zu
sagen, ob ein neues Fenster **besser** ist oder nur **anders**.

## 4.1 ⚠️ Der Suchpreis — die Korrektur kommt AUS DEM WERKZEUG

**6 Rückblicke × 6 Horizonte = 36 Zellen.**

⚠️⚠️ **Gegengeprüft am Code, und meine erste Fassung war falsch.** Sie
schrieb *Poisson* vor. `messe_drift.py:372` rechnet aber **BONFERRONI**:

```python
gr = NormalDist().inv_cdf(1 - 0.05 / (2 * len(RUECKBLICKE) * len(HORIZONTE)))
```

➤ **Bonferroni bleibt** — R-R11 verlangt dieselbe Methodik, sonst ist der
`250/5`-Anker nicht vergleichbar. Bonferroni ist zudem **strenger** als
Poisson; die Messung wird dadurch nicht leichter.

⚠️ Und: ein echter Effekt zeigt sich über **benachbarte** Zellen, nicht in
einer einzelnen.

## 4.2 ⚠️ Was das Werkzeug heute kann — und was fehlt

```python
RUECKBLICKE = (60, 120, 250)     # Tage — kein kurzer Rückblick
HORIZONTE   = (5, 20, 60)        # Tage — kürzester Horizont 5
```

➤ **Die Stundenachse ist eine echte Erweiterung, keine Umparametrierung.**
Zu bauen: Stundenauflösung, `_newey_west`-Lag in Stunden, und die Termine
je Zelle ausweisen.

---

# § 5 Die Zielgröße — zwei Arme, und der Grund dafür

| Arm | Zielgröße | wozu |
|---|---|---|
| **A — Reproduktion** | die Vorwärtsrendite, wie `messe_drift` sie rechnet | **R-R11** (§ 3). Ohne sie ist nichts vergleichbar |
| **B — die Sachfrage** | **`ergebnis_r`** aus Vorabfestlegung 10 | das ist, was der Trade **einbringt** |

⚠️⚠️ **Warum zwei:** Arm A misst, ob die Rangliste die **Kursentwicklung**
ordnet. Arm B misst, ob sie das **Handelsergebnis** ordnet. Das ist nicht
dasselbe — zwischen beiden liegen Stop, Ziel und die am 24.09. gemessene
Tatsache, dass bei kurzen Fenstern die **Mehrheit offen bleibt**.

⚠️ **Weichen A und B auseinander, gilt B** — und die Abweichung ist selbst
ein Befund, kein Fehler.

---

# § 6 Die Norm

| | |
|---|---|
| **Frageart** | `beitrag` → **selektierte Menge** (F-212) |
| **Bezug** | **Nullpunkt** aus 40 Nullwelten, 90. Perzentil |
| **Negativkontrolle** | `zufall` als Rangordnung — **Pflicht** |
| **Positivkontrolle** | 5 Ziehungen |
| **Beide Hälften** | B6 |
| **Überlappung** | **Newey-West**, Lag = Horizont. ⚠️ Bei Stundendaten in **Stunden**, und die Zahl der Termine wird ausgewiesen |
| **Abgrenzung** | **nur Krypto** |

## 6.1 ⚠️ Was mitläuft, weil es sonst niemand sieht

1. **Wie viele Symbole `k` durchlässt** — heute **2 von 43**. Diese Zahl ist
   eine eigene Stellgröße und wird **mitgemessen**, nicht angenommen.
2. **Die Belegung je Rang** — ein Rang aus zwölf Ankern ist keiner.
3. **Der Anteil ohne Historie** — wer 250 Tage verlangt, schließt junge
   Werte aus. Bei 6 h Rückblick fällt dieser Ausschluss weg, und **das
   allein** ändert die Grundgesamtheit. ⚠️ **Die Grundgesamtheit ist keine
   Stellschraube** — die Wirkung wird nach `messe_grundgesamtheit.py`
   beziffert.

---

# § 7 ⭐ Die Entscheidungsregel — VOR der Messung

| Ergebnis | Entscheidung |
|---|---|
| ⛔ **R-R11 fällt** | **Abbruch** — die Anlage, nicht die Frage |
| ✔ **Ein Rückblick trägt** über benachbarte Horizonte, Kontrolle sauber, über der Bonferroni-Schwelle | **Er wird der Rückblick für den Hebel** — je Instrument, nicht global |
| ⚠️ **Nur eine Zelle trägt** | **kein Befund** — Signatur eines Zufallstreffers |
| ⚠️ **250 bleibt der beste** | dann ist die Stufe richtig und P-1 **erledigt** — der Hebel scheitert woanders |
| ⛔ **KEIN Rückblick trägt** auf 6–72 h | ➤ **§ 8, der Rückfall** |
| ⚠️ **Trennschärfe reicht nicht** | nichts entschieden — Datendecke |
| ⛔ **Kontrolle trägt** | Lauf ungültig |

⚠️⚠️ **Wird nicht nachverhandelt.**

---

# § 8 ⭐⭐ DER RÜCKFALL — Nutzerauflage, hier vorab festgelegt

**Nutzervorgabe 24.09.:** *„wenn du keine Lösung über die Messung findest
brauchen wir eine Alternative."*

➤ **Die Alternative steht bereits im Code — als seine eigene Regel:**

> *„`aktiv=False` heißt: hier wird nicht ausgewählt (zu wenige Werte mit
> Historie). Dann passieren ALLE — **eine Stufe, die nichts entscheiden
> kann, darf nicht sperren**."* — `auswahl.waehle`

**Trägt für 6–72 h kein Rückblick, dann kann diese Stufe dort nichts
entscheiden — und darf nach ihrer eigenen Regel nicht sperren.**

| | |
|---|---|
| **Was gebaut würde** | `waehle(..., aktiv=False)` für `instrument == "hebel"` |
| ⚠️⚠️ **Gegengeprüft: das ist KEIN Schalter** | `auswahl.waehle()` hat **keinen** `instrument`-Parameter, und `rollen_lauf.py:571` ruft `_AW.waehle(reihen, symbole)` ohne einen. Der Rückfall braucht eine **Signaturerweiterung** plus den Aufrufer — meine erste Fassung hat das unterschlagen |
| **Warum das keine Willkür ist** | es ist **die im Modul formulierte Regel**, angewandt auf einen Fall, für den sie nie geprüft wurde |
| ⚠️ **Was es NICHT ist** | keine Absenkung der Ansprüche. Die Auswahl bleibt für **Spot** unverändert — dort ist sie mit `250/5` **belegt** |
| ⚠️ **Der Preis, benannt** | ohne Auswahl laufen **43 statt 2** Symbole in die nächste Stufe. Das kostet Modellaufrufe — ⚠️ **aber erst nach der Bewertung** (P-2), und die sperrt vorher |

**Zweite Alternative**, falls die erste zu weit geht: **`k` anheben** statt
abschalten (etwa 5 von 43 statt 2). ⚠️ Das wäre eine **gewählte Zahl ohne
Befund** und deshalb nur der zweite Platz.

---

# § 9 ⚠️⚠️ RANDBEDINGUNG — sie darf durch diese Messung NICHT verletzt werden

**Nutzervorgabe 24.09., wörtlich:** *„der HEBEL MUSS dynamisch aus der
Bewertung entstehen — vorgabe für den Experten."*

✔ **Am Code geprüft: das ist bereits so gebaut.**

```yaml
hebel_aus_quote:
  aktiv: true        # risiko = r(q) x Kapital,  r(q) = halbes Kelly
  hebel_ab: 2.0      # hebel = (risiko / Stop) / hebelnenner_eur
  hebel_grenze: 5.0  # unter hebel_ab wird es Spot
```

`entscheidungsrechnung.py:1033` — `hebel_noetig = risiko_eur / (betrag ×
stop_rel)`, und `risiko_eur` kommt aus **`r(q)`**, also aus der Bewertung.

⚠️ **Eine frühere Fassung dieses Blattes nannte `verlustanteil / stop_rel`.
Das ist der ALTE Risikobudget-Weg** (`dimensioniere()`, Zeile 1693) und
**nicht** der aktive. Korrigiert.

## 9.1 Was daraus für diese Messung folgt

| | |
|---|---|
| ⛔ **Diese Messung fasst den Hebel NICHT an** | sie betrifft die **Auswahl**, also welche Assets überhaupt bewertet werden |
| ⛔ **Kein Ergebnis darf den Hebel statisch machen** | eine feste Stufe „Rang 1 → Hebel 3x" wäre genau das, was die Vorgabe verbietet |
| ⚠️ **Die zwei offenen Punkte bleiben** | **P-9**: `q` ist nie kalibriert (steuerndes Fenster 1 Pp, funding bewegt 3) · **P-10**: die Stufen sind 1,47×/1,85× zu grob (N19) |

➤ ⚠️⚠️ **P-9 und P-10 sind die eigentliche Baustelle der Vorgabe aus § 9** —
der Hebel entsteht zwar aus der Bewertung, aber aus einer **unkalibrierten**.
Diese Messung macht das weder besser noch schlechter; sie räumt nur die
Stufe davor.

---

# § 10 Die Vorhersage, vor dem Lauf

**Erwartung: für 6–24 h trägt KEIN Rückblick; ab 72 h nähert sich das Bild
dem `250/5`-Befund an.**

**Begründung:** Momentum ist ein Effekt über Wochen. Auf sechs Stunden
dominiert Rauschen, und die Rangliste ordnet dann Zufall.

⚠️ **Wenn das stimmt, ist § 8 der wahrscheinliche Ausgang** — und das ist
kein Scheitern, sondern die Antwort: *eine Stufe, die auf diesem Horizont
nichts entscheiden kann, darf dort nicht sperren.*

**Gegenthese:** ein **kurzer** Rückblick (6–24 h) trägt auf kurzen
Horizonten — kurzfristige Umkehr statt Momentum. ⚠️ Dann wäre das
**Vorzeichen negativ**: der schlechteste Rang wäre der beste Kandidat. Das
ist zu prüfen und nicht wegzurunden.

---

# § 11 Was diese Messung **nicht** entscheidet

- **Nicht** den Hebel selbst (§ 9).
- **Nicht** P-2 (Bewertung vor Modellaufruf) — eine Architekturfrage.
- **Nicht** P-3 (Trichterstufe 6) — Nutzerentscheidung, betrifft auch Spot.
- **Nicht** die Auswahl für **Spot**. Dort gilt `250/5` weiter, belegt.
- **Nicht** M1.

---

# § 12 ⭐⭐ DIE BEWERTUNGSSTUFEN — eigene Messung, hier eingeordnet

**Nutzerauftrag 24.09.:** *„und die erforderlichen Bewertungsstufen gehören
auch noch gemessen"*

## 12.1 ⚠️ Zuerst die Unterscheidung, sonst misst man das Falsche

```python
HEBEL_STUFEN_VORGABE = (2.0, 3.0, 5.0, 10.0)
# Nutzerauskunft 15.09.: "der Einstieg ist meist 2x, 3x, 5x und 10x"
```

⛔ **Das sind NICHT die zu messenden Stufen.** Es sind die bei Bitpanda real
**einstellbaren** Hebel — extern vorgegeben, nicht wählbar. Sie zu messen
hieße, die Börse zu messen.

➤ **Zu messen ist die ABBILDUNG:**

> **Welches Bewertungsniveau rechtfertigt welche Hebelstufe?**

Die Kette heute:

```
Bewertung → q → Kelly → r = clamp(kelly/2, 0,005, 0,0125)
         → hebel = (r × Kapital / Stop) / 500
         → gerundet auf die nächste einstellbare Stufe
```

## 12.2 Was daran bereits gemessen ist — und was es sagt

| Befund | |
|---|---|
| **P-9** — `q` wurde **nie kalibriert** | steuerndes Fenster **1 Prozentpunkt**, `funding` bewegt **3**; in **44 %** der Merkmalslagen entsteht gar kein Hebel |
| **P-10 / N19** (06.09.) | die Umrechnung **überschätzt um Faktor 3**; die Stufen sind **1,47× / 1,85×** zu groß |
| **N19-E** | ⭐ **Nutzerentscheidung vom 06.09., nie umgesetzt**: die Stufen direkt gegen die **Barrieren-Quote** kalibrieren statt über `bewegung_r` zu übersetzen |

⚠️⚠️ **Der Befund liegt seit dem 06.09. vor und ist nie gebaut worden.**
Das ist die Antwort auf den Auftrag — es fehlt keine Messung, es fehlt die
**Umsetzung einer bereits getroffenen Entscheidung.**

## 12.3 ⚠️ Warum das eine EIGENE Vorabfestlegung braucht

| | |
|---|---|
| **P-1 (dieses Blatt)** | die **Auswahl** — welche Assets überhaupt bewertet werden |
| **Die Stufen (§ 12)** | die **Höhe** — wieviel Hebel eine Bewertung rechtfertigt |

⛔ **Zwei Fragen, zwei Messungen.** Sie zusammenzuwerfen hieße, zwei Dinge
gleichzeitig zu ändern — und dann ist keines mehr zuzuordnen.

➤ **Reihenfolge, und sie ist zwingend:**

| | |
|---|---|
| **1. P-1** | ohne sie kommt **kein Asset** in die Bewertung — heute 0 von 6 |
| **2. Die Stufen** | sie setzen voraus, dass überhaupt etwas bewertet wird |

⚠️⚠️ **Und P-9 kommt vor beiden.** Eine Stufe gegen ein **unkalibriertes**
`q` zu kalibrieren, kalibriert gegen Rauschen. Das ist derselbe Fehler wie
„Maximum als Nullpunkt" — man eicht an etwas, das keinen Bezug hat.

➤ **Aufgenommen als P-22, mit eigener Vorabfestlegung, nach P-1.**
