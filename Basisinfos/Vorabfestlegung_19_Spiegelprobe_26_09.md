# Vorabfestlegung 19 — Womit trennt man Richtung von Bewegung?

**26.09.2026**, vor der Messung geschrieben · `pruefe_spiegelprobe.py`
**Nutzerauftrag:** *„vorher noch eine Recherche zu den Messstandards und
Regelwerken — mache eine Fragestellung und Hypothese, sauber konstruieren,
testen und simulieren."*

---

# § 1 Was die Recherche ergeben hat

**Der Messstandard** (`messnorm.standardzeile()`) regelt Nullpunkt,
Nullwelten, Trennschärfe und Positivkontrolle — **zur Spiegelprobe sagt er
nichts**. Es gibt keine Konstante dafür.

**Die Regel steht in Befund 2.594** und lautet wörtlich:

> *„Wer ein gerichtetes **EREIGNIS** misst („Kurs steigt um X"), muss auch
> das gespiegelte messen („Kurs fällt um X"). Ein Merkmal, das auf beiden
> Seiten gleich trägt, misst BEWEGUNG, nicht RICHTUNG."*
> **Schwelle:** Verhältnis ≥ 1,30 oder ≤ 0,77.

Die zugehörigen Messwerte:

| Merkmal | Lift hoch | Lift runter | Verhältnis | Urteil damals |
|---|---|---|---|---|
| `vola` | 3,317 | 1,679 | 1,975 | „teilweise Richtung" |
| `momentum_kurz` | 3,082 | 1,255 | 2,456 | Richtung |
| `funding` | 1,216 | 1,302 | 0,934 | nur Bewegung |

## 1.1 ⛔ Zwei Mängel, die dabei sichtbar werden

| # | |
|---|---|
| **1** | ⛔ **Ich habe die Regel auf `E[R]` angewandt statt auf ein EREIGNIS.** Long- und Short-`E[R]` sind auf denselben Ankern **strukturell** gegenläufig — egal was das Merkmal misst. Nachgewiesen: ein garantiert richtungsfreies Merkmal liefert dasselbe Vorzeichenmuster wie ein reines Richtungsmerkmal |
| **2** | ⚠️ **Die Schwelle 1,30 ist nicht geeicht.** Ein garantiert richtungsfreies Merkmal (\|künftige Bewegung\|) erreicht auf echten Daten ein Verhältnis von **2,57** und würde nach dieser Schwelle als „Richtung" durchgehen |

⚠️ **Und Mangel 2 lässt sich auf echten Daten nicht beheben:** ein Merkmal,
das garantiert *nur* Bewegung misst, gibt es dort nicht. Große Kryptobewegungen
sind häufiger nach oben, also steckt in jedem Bewegungsmaß Richtung.

---

# § 2 Die Fragestellung

> **Welche Prüfgröße trennt RICHTUNG von BEWEGUNG zuverlässig — und ab
> welcher Schwelle?**

## 2.1 H0 und H1

| | |
|---|---|
| **H0** | Keine der geprüften Größen trennt die beiden Fälle in der Simulation mit einer Fehlerquote unter 10 % |
| **H1** | Mindestens eine trennt, und ihre Schwelle lässt sich aus der Simulation **ablesen** statt zu setzen |

## 2.2 Die Kandidaten

| Prüfgröße | Rechnung |
|---|---|
| **V** Verhältnis der Lifts | `Lift_hoch / Lift_runter` — die registrierte Fassung |
| **G** Gegenlift unter 1 | ist `Lift_runter < 1`? |
| **D** Differenz | `Lift_hoch − Lift_runter` |
| **S** Summe über 2 | `(Lift_hoch + Lift_runter) / 2` — der **Bewegungs**anteil |
| **Q** Quotient aus D und S | Richtungsanteil relativ zum Bewegungsanteil |

⭐ **Vorhersage, damit ein Treffer nachprüfbar ist:** **S** misst den
Bewegungsanteil und muss bei beiden Fällen ähnlich sein; **D** und **Q**
sollten trennen. **V** wird nach § 1.1 voraussichtlich **nicht** sauber
trennen — genau das ist zu prüfen.

---

# § 3 Die Simulation — hier ist die Wahrheit bekannt

Auf echten Daten gibt es keinen garantiert richtungsfreien Testfall (§ 1.1).
Deshalb werden Kursreihen **erzeugt**, bei denen Bewegungs- und
Richtungsanteil **gesetzt** sind:

```
    r(t) = drift(gruppe) + sigma(gruppe) * z(t)        z ~ N(0,1)
```

| Welt | drift | sigma | Wahrheit |
|---|---|---|---|
| **BEWEGUNG** | **0 für alle Gruppen** | variiert über die Gruppen | das Merkmal ordnet **nur** die Schwankung |
| **RICHTUNG** | variiert über die Gruppen | **gleich für alle** | das Merkmal ordnet **nur** die Drift |
| **GEMISCHT** | variiert | variiert | beides, in bekanntem Verhältnis |

Das Merkmal ist jeweils die **Gruppennummer** — es ordnet also per
Konstruktion exakt das, was variiert wurde, und nichts sonst.

⚠️ **Die Barrierengeometrie ist dieselbe wie im Betrieb** (`k × ATR`,
geklammert, Stop zuerst) — sonst würde die Eichung für eine andere Geometrie
gelten als die Anwendung.

## 3.1 Was die Simulation NICHT kann

| # | |
|---|---|
| **1** | ⛔ Sie prüft die **Prüfgröße**, nicht die Daten. Ob ein echtes Merkmal Richtung hat, sagt sie nicht |
| **2** | ⚠️ Normalverteilte Renditen haben **keine fetten Ränder** und kein Vola-Clustering. Eine Schwelle aus der Simulation ist deshalb eine **untere** Abschätzung der Trennschärfe |
| **3** | ⚠️ Die Gruppen sind **gleich groß** und **zeitlich stabil** — echte Merkmale wechseln die Gruppe |

---

# § 4 Die Abnahmeproben

| | |
|---|---|
| **A1** | In der **BEWEGUNG**-Welt darf die gewählte Prüfgröße in höchstens **10 %** der Ziehungen „Richtung" melden |
| **A2** | In der **RICHTUNG**-Welt muss sie in mindestens **80 %** „Richtung" melden (Fundquote analog Messstandard) |
| **A3** | ⭐ **Dosis-Wirkung:** über die gemischten Welten muss die Prüfgröße **monoton** mit dem gesetzten Richtungsanteil steigen. Eine Größe, die springt, ist kein Maß |
| **A4** | Die Schwelle wird aus der Simulation **abgelesen** (Trennpunkt zwischen den Verteilungen), nicht gesetzt |

---

# § 5 Was danach passiert — und was nicht

✔ **Neu bewertet werden** die heutigen Kandidaten: `rueckstand_*` (2.601),
`ema_lage`, `trendstruktur`, `ema_abstand_atr`, `rsi ∧ vola unten`.

⚠️⚠️ **Korrigiert wird nur, was sicher ist.** Nutzervorgabe: *„korrigiere die
Doku aber nur dort wo es sicher ist."* Konkret:

| | |
|---|---|
| ✔ **sicher korrigierbar** | die Aussage *„Spiegelprobe auf `E[R]`"* — sie ist nachweislich falsch konstruiert, unabhängig vom Ergebnis |
| ⚠️ **erst nach der Messung** | die Urteile *„Bewegung ohne Richtung"* bei den einzelnen Merkmalen |
| ⛔ **NICHT angefasst** | 2.594 selbst. Dort wurde auf **Ereignissen** gemessen, also richtig. Nur die **Schwelle** 1,30 steht zur Prüfung, nicht der Befund |
| ⛔ **NICHT angefasst** | der zweite Teil von 2.601 (`rueckstand` trägt nur 13 % über `beta`) — das war die `beta`-Kontrolle und von der Spiegelprobe unberührt |
