# Gesamtlage — der HEBELUMBAU, sortiert nach dem abgestimmten Plan

**24.09.2026.** Nutzervorgabe, wörtlich:

> *„Wir haben abgestimmt 1. eine Prüfung durch einen TAKT 2. Dann die
> Bewertungen für spot und hebel - ABER beide MÜSSEN etwas anderes bewerten
> (hinweis Spot ist ohnehin falsch) - JETZT geht es um den HEBELUMBAU nur
> HEBEL. Erst wenn parallel und gleichzeitig entweder Spot oder Hebel
> entschieden ist geht das Signal weiter zum nächsten Schritt in der
> Ablaufkette. Du kannst spot als Vergleich für den Einstieg nehmen -
> Wirkung vorher nachher - ABER vermessen und analysiert soll nur der
> Hebel werden."*

---

# § 1 Der Zielaufbau — in drei Sätzen

```
1. TAKT          ein Asset kommt zur Prüfung
                 (ein Durchgang, nicht zwei)

2. BEWERTUNG     Spot und Hebel werden PARALLEL bewertet
                 ⚠️ und zwar auf VERSCHIEDENE Fragen
                 → genau EINES gewinnt

3. KETTE         erst dann geht das Signal weiter
```

⚠️⚠️ **Der entscheidende Satz ist der mittlere:** *„beide MÜSSEN etwas
anderes bewerten"*. Nicht dieselbe Zahl zweimal, nicht dieselben Stufen —
**zwei verschiedene Fragen an dasselbe Asset.**

⚠️ **Und der Nutzerhinweis dazu: *„Spot ist ohnehin falsch"*** — Spot dient
hier als **Vergleichsmaßstab** (Wirkung vorher/nachher), nicht als Vorbild.

---

# § 2 Was der Hebel heute HAT — und was davon trägt

| | Stand |
|---|---|
| **Eigene Zelle in der Kette** | ⛔ **nein** — `zellen()` liefert 43, `rollen_lauf` verwirft sie. H-K1 war gebaut und ist auf Anweisung zurückgenommen |
| **Eigene Bewertung** | ⛔ **nein** — `funding` und `turnover` tragen `instrumente=("spot",)`. Gemessen 24.09.: Spanne bestes zu schlechtestes Fünftel = **0,0000** |
| **Eigene Dimension** | ⛔ **nein** — alles gemessen auf H20/Tagesbasis, der Hebeltrade liegt bei 6–72 h |
| **Eigene Positionsführung** | ✔ ja — Topf (3.000 €), Cooldown, `hebel_signals` |
| **Hebelhöhe aus der Bewertung** | ✔ gebaut (`hebel_aus_quote`), ⛔ auf unkalibrierter Grundlage |

> ⛔ **Der Hebel hat heute KEINE eigene Bewertung. Seine Quote steht
> konstant auf 0,3333 — exakt der Kelly-Nullstelle. Damit ist `Kelly = 0`
> und es entsteht NIE ein Hebel, in keiner Marktlage.**

---

# § 3 Was heute gemessen wurde — und für wen es gilt

| Messung | Befund | gilt für |
|---|---|---|
| **Gleichstandsregel** | kostet **+0,0003** — unschuldig (2.583) | beide |
| **Basisrate** | schwankt **10,7 → 60,7 %**, echt (Faktor 3,13), **nicht vorhersagbar** (2.585) | beide |
| **Zusammenspiel der Beiträge** | unabhängig (r = +0,035) → Addition zählt nichts doppelt | Spot |
| **Stufenhöhe** | Formel sagt **8,4 Pp** Spreizung, tatsächlich **4,0 Pp** → **Faktor 2 zu groß** | Spot |
| **Kalibrierung** | Steigung **+0,040** statt +0,333 (R-R11 reproduziert) | Spot |

⚠️⚠️ **Keine dieser Messungen hat den Hebel bewertet.** Sie betreffen das
Fundament (für beide) oder Spot (als Vergleich). ➤ **Das ist die Lücke.**

---

# § 4 ⭐ Was der Hebelumbau braucht — die Reihenfolge

| # | | Stand |
|---|---|---|
| **H-A** | ⭐ **Die Hebel-DIMENSION messen** — welcher Horizont, welche Stopweite? Vorabfestlegung 10 liegt fertig: 6/12/24/48/72 h, Zielgröße `ergebnis_r`, sechs Kandidaten aus den stündlichen Terminmarktgrößen | ⚠️ **bereit, ungemessen** · Daten liegen (3,24 Mio Kerzen) |
| **H-B** | **Die Hebel-STUFEN messen** — direkt gegen die Barrieren-Quote auf der in H-A gefundenen Dimension. Das ist N19-E, deine Entscheidung vom 06.09. | ⛔ nach H-A |
| **H-C** | **Die Beiträge für den Hebel freischalten** — `instrumente` erweitern, aber mit den **eigenen** Stufen aus H-B, nicht mit den Spot-Zahlen | ⛔ nach H-B |
| **H-D** | **Der Einstieg** — die Auswahlstufe rangt nach **250 Handelstagen** und sperrt im Hebel-Lauf 6 von 6. Vorabfestlegung 11 liegt fertig | ⚠️ **bereit, ungemessen** |
| **H-E** | **Die Zelle in der Kette** — Takt → beide Bewertungen parallel → eine gewinnt | ⛔ nach H-C, Bauform abzustimmen |
| **H-F** | **LLM und Mail** lagerichtig | ⛔ zuletzt |

⚠️ **H-A ist der Anfang und blockiert alles Weitere.** Ohne die Dimension
sind die Stufen nicht messbar, ohne Stufen gibt es keine Bewertung, ohne
Bewertung entsteht kein Signal.

---

# § 5 ⚠️ Was aus heute mitgenommen werden MUSS

| | |
|---|---|
| **Die Basisrate ist instabil** | H-B kalibriert gegen einen **beweglichen** Nullpunkt. Das muss in der Vorabfestlegung stehen, sonst ist es derselbe Fehler wie *„ein Maximum ist kein Nullpunkt"* |
| **Die Stufen überschätzen um Faktor 2** | wenn das für Spot gilt, ist es für den Hebel **vorab zu prüfen**, nicht zu übernehmen |
| **Die Merkmale sind unabhängig** | ✔ gute Nachricht — die Addition ist auch für den Hebel eine zulässige Bauform |
| **Spot ist der VERGLEICH** | Wirkung vorher/nachher, nicht Vorbild |

---

# § 6 Was ausdrücklich NICHT ansteht

- **Nicht** Spot reparieren (*„Spot ist ohnehin falsch"* — eigenes Thema).
- **Nicht** die Spot-Stufen dem Hebel geben. Alle drei Varianten, die ich
  dazu vorgeschlagen hatte, waren falsch gerahmt.
- **Nicht** Takt und Cooldown (Nebenthema, nach der Ablaufkette).
- **Nicht** P-3 (Trichterstufe 6) ohne Nutzerentscheidung — betrifft Spot mit.

---

# § 7 Der nächste Schritt

➤ **H-A: die Hebel-Dimension messen.** Vorabfestlegung 10 liegt fertig und
gegengeprüft, die Stundenbasis steht (3.244.186 Kerzen, 116 Symbole).

**Was sie beantwortet:** auf welchem Horizont und mit welcher Stopweite ein
Hebeltrade überhaupt eine Trefferquote über der Kelly-Nullstelle erreicht —
und welche der sechs stündlichen Größen dabei trennen.

⚠️ **Sie misst NUR den Hebel.** Spot läuft als Vergleichsarm mit, damit die
Wirkung vorher/nachher sichtbar ist — bewertet wird er nicht.
