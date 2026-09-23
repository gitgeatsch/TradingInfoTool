# Vorabfestlegung 6 — die Kante ist nicht das Problem, die Schwankung ist es

**23.09.2026, geschrieben VOR der Messung.** Nutzerkritik, die sie
auslöst:

> *„Ein Schalter ist für mich per Definition eine **Falle**, da minimale
> Bewegungen alles oder nichts bedeuten. Das finde ich für ein System,
> das mit unterschiedlichen Gegebenheiten und Lagen funktionieren soll,
> kritisch."*

und die Nachfrage, die diese Vorabfestlegung gerettet hat:

> *„Du hast mir heute bereits die Rampe als Anwendung gebracht und diese
> kritisiert — was war das und warum, damit wir hier nicht wieder einen
> solchen Fehler machen?"*

---

# § 1 Das Ziel — es entscheidet die zulässige Bauform

**Nutzervorgabe:** Spot und Hebel teilen den **Eingang**; der Hebel
entsteht **danach**, dynamisch, wenn das Chancen-Risiko-Verhältnis es
hergibt.

> ⛔ **Daraus folgt eine harte Anforderung: ein Beitrag, der ein Asset
> ENTFERNT, zerstört die Hebel-Dynamik.** Was gesperrt ist, kann nie einen
> Hebel erzeugen — es ist weg, bevor die CRV-Rechnung stattfindet.

⚠️ **Damit ist meine eigene Empfehlung vom selben Tag widerlegt.** Ich
hatte argumentiert: *„gemessen ist eine Sperre → also sollte eine Sperre
laufen"*. Richtig ist: die Messung **misst** eine Sperre, weil das die
einfachste Wirksamkeitsprüfung ist. Der **Betrieb** braucht einen stetigen
Beitrag auf die Quote.

---

# § 2 ⛔ Warum die RAMPE nicht gebaut wird

## 2.1 Sie wäre derselbe Fehler gewesen

| | behauptet | Stand |
|---|---|---|
| **5-Stufen-Tabelle** (live) | Ordnung über die **ganze** Spanne | ⛔ **widerlegt** (V4, N-56, 2.133, 2.553, 2.554) |
| **Rampe** (mein Vorschlag) | Ordnung im **oberen** Bereich | ⚠️ **ungemessen** |

Gemessen ist nur ein **Zweiklassenvergleich** (`normal minus hoch`
+0,2331 R; Sperre +0,0234 R). **Keine Messung sagt, dass innerhalb der
hohen Werte höher schlechter ist.** „Widerlegt" und „ungemessen" sind
verschieden — **unbelegt** sind beide, und das ist der Maßstab.

## 2.2 Und die Daten schließen sie aus

Spreizung **innerhalb** des obersten Fünftels, über 2.386 Tage:

| | |
|---|---|
| (höchster − niedrigster) / Median | **0,60-fach** (Median) |
| Anteil Werte **identisch** mit dem kleinsten | **69,2 %** (Median), **97,9 %** (75. Perzentil) |

➔ **An der Hälfte der Tage sind 69 % des obersten Fünftels derselbe
Wert.** Eine Rampe hätte dort nichts zu differenzieren. Der Rang wirft
keine Information weg — es ist keine da.

---

# § 3 ⛔ Und auch die absolute Grenze ist nicht die Lösung

Zweite These, ebenfalls **gefallen** (366.871 Symbol-Tagespaare):

| Wechsel von Tag zu Tag | |
|---|---|
| über die **Rang**kante 0,80 | 17,58 % |
| über die **absolute** Grenze | **18,21 %** — *mehr* |
| Rangwechsel **ohne** eigene Änderung des Symbols | nur **18,2 %** aller Rangwechsel |

> **82 % der Wechsel sind echte eigene Bewegungen.** Die Instabilität
> kommt **nicht** von der Rangbildung. Keine Grenzverschiebung hilft.

---

# § 4 ➤ Die Ursache, gemessen: die EINGANGSGRÖSSE schwankt

| Glättung | Kantenwechsel |
|---|---|
| 1 Tag (heute) | **17,54 %** |
| 3 Tage | 10,07 % |
| **7 Tage** | **5,85 %** |
| 14 Tage | 3,55 % |

## Warum das fachlich und nicht nur technisch richtig ist

Funding wird **alle acht Stunden** abgerechnet. Ein Tageswert ist ein
**Momentwert**; die ökonomisch gemeinte Größe — *„zahlt die Long-Seite
hier dauerhaft drauf?"* — ist ein **Niveau über Tage**.

➔ Die Glättung ist damit keine Glättung des **Urteils**, sondern die
Korrektur der **Größe**. Sie behauptet **keine Ordnung** und verletzt
keine der fünf Formmessungen.

⚠️⚠️ **Sie ist zugleich der Verdacht, dass die heutige Größe falsch
gebaut ist** — sie nimmt den Momentwert, nicht das Niveau. Das wäre ein
**B1-Verstoß** nach R-R8 („richtige FORM"), also derselbe Fehler, den die
Durchsicht vom 30.08. bei TVL und aktiven Adressen gefunden hat.

---

# § 5 Die Messung

| | |
|---|---|
| **Werkzeug** | `messnorm.pruefe()` — **die eine Messung**, keine Nachbildung |
| **Lage / Zielgröße** | `spot × einstieg` → `bewegung_r` |
| **Horizont** | H20, Blocklänge 60 |
| **Kandidaten** | Glättung über **1** (= heute), **3**, **7**, **14** Tage |
| **Mehrfachtest** | vier Fenster = `hypothesen=4` |
| ⚠️ **Look-Ahead** | die Glättung mittelt `[t-n+1 … t]` — nur **Rückblick** |
| **B6** | jedes Fenster in beiden Historienhälften |
| **zweite Zielgröße** | die **Kantenstabilität** (Wechselquote) — sie ist gerechnet, nicht geschätzt |

## 5.1 Die Stufen

| | | |
|---|---|---|
| **S0** | **Machbarkeit** — findet die Anlage auf jeder Kandidatenmenge gepflanzte ≤ 0,10 R? | ohne ✔ endet es |
| **S1** | **R-R11** — Glättung 1 Tag muss **+0,0234 R** reproduzieren | ohne Reproduktion wird nichts umgestoßen |
| **S2** | die Wirkung je Glättungsfenster | die Frage |
| **S3** | **B6** je Fenster | |
| **S4** | Wirkung **gegen** Kantenstabilität — beides zusammen | die Entscheidung |

---

# § 6 Die Entscheidungsregel — vor der Messung

| Ergebnis | Entscheidung |
|---|---|
| **S0 fällt** | ⛔ keine Messung, Punkt geschlossen |
| **S1 fällt** | ⛔ **Stopp** — dann steht die Registrierung zur Debatte, nicht die Glättung |
| Ein Fenster n > 1 ist **belegt besser** als n = 1 **und** B6 ✔ | ✔ **Umbau auf dieses Fenster.** Danach R-R9 + Betriebsprüfung |
| Alle Fenster **gleichwertig** (Bänder überlappen), B6 ✔ bei n = 1 | ➤ **Die Glättung kostet nichts und bringt Stabilität.** Dann ist die Wahl **konstruktiv** — und sie wird ausdrücklich als solche berichtet, nicht als Messergebnis |
| Ein Fenster n > 1 ist **belegt schlechter** | ⛔ **kein Umbau.** Der Effekt steckt im Momentwert; die Kantenkritik bleibt dann **offen und unlösbar** — und das wird so gesagt |
| B6 verletzt beim Gewinner | ⛔ kein Umbau |

⚠️⚠️ **Diese Festlegung wird nicht nachverhandelt.** Insbesondere Zeile 4:
ein Gleichstand ist **kein** Beleg für die Glättung. Er erlaubt sie nur.

## 6.1 ⚠️ Die Lehre, die diese Vorabfestlegung überhaupt erst möglich machte

Ich habe an **einem Tag drei** Bauformen vorgeschlagen — Schalter,
Zustandsschalter, Rampe. **Jede war eine Antwort auf ein Symptom, keine
auf die Ursache**, und jede hätte gebaut werden sollen, bevor gemessen
war, *woran* es liegt.

> **Erst die Ursache messen, dann die Form wählen.** Die Nutzerfrage
> *„was war das und warum"* hat genau das erzwungen — und in vier
> Messungen fielen **beide** meiner Thesen (Rampe, absolute Grenze),
> bevor eine Zeile Code entstand.

## 6.2 Was diese Messung **nicht** entscheidet

- **Ob `funding` trägt.** Registriert, reproduziert, B6 erfüllt.
- **Die Form der Fünferleiter.** Fünffach widerlegt, unabhängig hiervon.
- **Die Anwendung bei Hebel und Akkumulation.** Andere Zielgrößen
  (`barriere`, `verbilligung`), beide ungemessen — eigene Punkte.

---

# ERGEBNIS — 23.09.2026: ⛔ bei S1 gestoppt

## ✔ S0 Machbarkeit — auf **allen** vier Fenstern bestanden

Gepflanzte **0,05 R** gefunden, gefordert ≤ 0,10. Die Kantenstabilität
bestätigt die Voruntersuchung:

| Fenster | Kantenwechsel |
|---|---|
| n=1 (heute) | 17,60 % |
| n=3 | 10,18 % |
| n=7 | 5,96 % |
| n=14 | 3,61 % |

## ⛔⛔ S1 — die Reproduktion fällt, **knapp**

| | |
|---|---|
| Wirkung | **+0,02425 R** [+0,01288 … +0,04285] |
| Nullpunkt | **+0,01364** |
| fehlend | **0,00076** |

⚠️ **Der Punktwert reproduziert einwandfrei** (+0,02425 gegen registriert
+0,0234 — 3,6 % Abweichung). Zur Frage steht allein die **Trennbarkeit**.

### Die Ursache, gemessen statt vermutet

| Menge | Wirkung | Nullpunkt | |
|---|---|---|---|
| alle 2.401 Tage | +0,02425 | +0,01364 | ⚠️ |
| ab 2020-10-11 (2.151) | +0,02286 | +0,00896 | ✔ trägt |
| **nur die ersten 250** | +0,03622 | **+0,03770** | ⚠️ Nullpunkt **vierfach** |

Die frühe Kryptozeit ist so verrauscht, dass sie das Gesamturteil kippt.

⚠️⚠️ **Eine Mengenwahl ist hier keine Lösung.** Die Menge ab 2020-10-11 zu
nehmen, *weil* sie das gewünschte Ergebnis liefert, wäre genau der
Verstoß, den *„die Grundgesamtheit ist keine Stellschraube"* verbietet.

## ⚠️⚠️⚠️ Und das ist die **dritte** Bestätigung derselben Lage

| | |
|---|---|
| **10.09.** V2/N-73 | *„besteht die Hürde NICHT"* — 2 von 3 Beitragsmengen; bei 20 % **nicht trennbar** |
| **11.09.** V11 | *„kippt in 1 von 3 Saaten"* |
| **23.09.** S1 | auf der vollen Menge nicht trennbar |

> **`funding` liegt an der Nachweisgrenze — und das ist seit dem 10.09.
> registriert.**

## ➤ Was daraus folgt

**Die Formfrage ist nachrangig.** Solange die Registrierung selbst an der
Grenze liegt, ist jede Verfeinerung ihrer Form eine **Verfeinerung von
Rauschen**. § 6 Zeile 2 hat das vorweggenommen.

⚠️ **Was NICHT folgt:** dass `funding` gefallen wäre. Der Punktwert
reproduziert in jeder Menge, der Beitrag trägt auf **2.151 von 2.401**
Tagen, und die vier Gegenproben vom 30.08. stehen unverändert. Was fehlt,
ist die Trennbarkeit auf der vollen Menge unter einem Standard, der
**nach** der Registrierung gesetzt wurde.

Befund **2.557-funding-an-der-nachweisgrenze**.
