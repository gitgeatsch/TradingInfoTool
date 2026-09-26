# Vorabfestlegung 20 — Die Selektion: gute Einstiege statt guter Fünftel

**26.09.2026**, vor der Messung · `messe_selektion.py` · Frageart **`markt`**

**Nutzervorgabe, wörtlich:**

> *„wir suchen einen Einstieg mit einer **Zeitpunktmessung** — diese KANN nur
> die **Ausgangslage MESSEN** und nicht den ERTRAG über die ZEIT
> voraussagen. Was suchen wir? GUTE Einstiege mit OPTIMALEN Voraussetzungen
> für eine **schnelle hohe Bewegung nach oben** — das ist **SELEKTION** der
> besten Ausgangslagen mit den besten Ergebnissen innerhalb von **1–5
> Tagen**."*

> *„GUTE Lagesignale & hohe kurze Anstiege sind eher **selten** bzw. können
> **nach unten skalieren** (kleinerer Hebel, das wäre die Abstufung)."*

---

# § 1 Was bisher falsch gemessen wurde

| | bisher (2.595 – 2.604) | **hier** |
|---|---|---|
| **Menge** | Fünftel = **20 %**, rund 575.000 Anker | **Spitze**: 5 % / 1 % / 0,1 % |
| **Horizont** | 6 und 24 Stunden | **1, 2, 3, 5 Tage** |
| **Zielgröße** | `E[R]` bei **festem** Ausstieg | **MFE** (max. Aufwärtsbewegung) **und** Ereignis |
| **Frage** | „ordnet das Merkmal die Menge?" | **„wie gut ist die Spitze?"** |

⚠️⚠️ **Ein Mittelwert über 20 % der Anker kann eine Spitze von 1 % nicht
zeigen** — sie verschwindet darin. Genau das steht schon registriert
(2.594): *„Ein Merkmal kann im Mittel nichts bewegen und trotzdem die
Extreme ordnen."* Ich bin danach wieder auf Mittelwerte umgestiegen.

⭐ **Und die Zielgröße folgt aus der Nutzerlogik:** wenn die Positionsführung
per **Trailing** erfolgt, entscheidet nicht, ob eine vorher festgelegte
Schwelle zuerst berührt wird, sondern **wie weit der Kurs maximal ins Plus
läuft**. Das ist MFE.

---

# § 2 Fragestellung und Hypothesen

> **Gibt es Ausgangslagen, deren schärfste Auswahl innerhalb von 1–5 Tagen
> eine deutlich höhere Aufwärtsbewegung zeigt als der Markt — und wächst
> dieser Vorsprung mit der Schärfe?**

| | |
|---|---|
| **H0** | Die Spitze eines Merkmals unterscheidet sich in MFE und Trefferquote nicht von einer Zufallsauswahl **gleicher Schärfe** |
| **H1a** | Sie unterscheidet sich — und der Vorsprung **wächst monoton mit der Schärfe** |
| **H1b** | ⭐ **Die Hebelabstufung ist ablesbar**: aus dem Vorsprung je Schärfegrad folgt, wie viel Hebel eine Lage verträgt |

## 2.1 ⭐ Warum H1a die eigentliche Prüfung ist

Ein echter Beitrag muss mit der Selektion **besser** werden — das ist die
Dosis-Wirkung. Bleibt der Vorsprung über 5 %, 1 % und 0,1 % gleich, ist die
Spitze nicht besser als der Durchschnitt des Fünftels, und die
Selektionsidee trägt nicht.

⚠️ **Gegenhypothese, die genauso plausibel ist:** Die Spitze eines
Momentum-Merkmals ist die **überhitzte** Lage — dort könnte die Bewegung
bereits gelaufen sein. Dann fällt der Vorsprung mit der Schärfe. **Beide
Richtungen sind verwertbar**, die fallende als Sperre.

---

# § 3 Die Zielgrößen — beide, wie vom Nutzer entschieden

| Größe | Rechnung | liest sich als |
|---|---|---|
| **MFE** | `max(high[t+1 … t+H]) / close[t] − 1`, geteilt durch ATR | wie weit maximal ins Plus, in ATR |
| **MAE** | `min(low[t+1 … t+H]) / close[t] − 1`, geteilt durch ATR | ⭐ wie weit vorher ins Minus — **die Spiegelprobe** |
| **MFE/MAE** | Verhältnis | ⭐ die Trailing-Größe: lohnt sich das Mitgehen? |
| **Ereignis** | `MFE ≥ 2 ATR` ohne vorher `MAE ≤ −1 ATR` | Trefferquote, direkt lesbar |

⚠️ **MAE ist hier die natürliche Spiegelprobe** und nicht nachgerüstet: ein
Merkmal, das MFE **und** MAE gleich stark erhöht, misst Bewegung. Das ist
dieselbe Logik wie 2.603, aber auf der passenden Größe.

⭐ **Das Ereignis verlangt die Reihenfolge** — erst das Ziel, nicht vorher
der Rücklauf. Sonst zählte ein Trade, der zuerst ausgestoppt worden wäre.

---

# § 4 Die Achsen

| Achse | Werte |
|---|---|
| **Schärfe** | 20 % (Fünftel, als Anschluss) · **5 %** · **1 %** · **0,1 %** |
| **Horizont** | **24 h (1 Tag)** · 48 h · 72 h · **120 h (5 Tage)** |
| Merkmale | die neun mit belegter Richtung (2.603) + `rsi_umkehr` + Kontrollen |
| Kontrollen | `zufall` und `vola` |

⚠️ Bei 0,1 % und 2,9 Mio Ankern bleiben rund **2.900** Anker je Merkmal —
das ist dünn, und die Nullwelt wird entsprechend breit. **Das ist der Preis
der Schärfe und wird ausgewiesen, nicht versteckt.**

---

# § 5 Welche Messstandards gelten

| | |
|---|---|
| **gilt** | Bezug = **Nullpunkt** (Mittelwert der Nullwelten) · 40 Ziehungen, 90. Perzentil · Trennschärfe gegen denselben Bezug · Positivkontrolle 5 Ziehungen · **Stundenklammer** (Querschnitt: welches Asset jetzt) · **B6** · **Dosis-Wirkung** über die Schärfe · Spiegelprobe (hier: MAE) |
| **angepasst** | Nullwelt = **Zufallsauswahl gleicher Schärfe** statt Fünftelpermutation — sonst enthielte sie die Verkleinerung der Menge nicht · gepflanzte Stärken als Anteil echter Ordnung |
| **gilt nicht** | `HORIZONT_JE_LAGE` = 3 Tage als **Vorgabe** (der Horizont ist hier eine **Achse**) · Produktionsgeometrie · F-212 |
| ➤ **Frageart** | **`markt`** — Menge = Messuniversum. Es ist **keine** `beitrag`-Frage: gemessen wird, ob eine Auswahl besser ist, nicht ob ein Merkmal die Kette verbessert |

---

# § 6 Test und Simulation an Echtdaten

**Nutzervorgabe:** *„dann testen und simulieren an Echtdaten."*

| | |
|---|---|
| **Selbsttest** | gepflanzte Ordnung in Stufen (0,00 / 0,25 / 0,50 / 1,00) auf den **echten** Ausgängen — Stufe 0,00 ist die Positivkontrolle und darf nicht treffen |
| **Nullwelt** | 40 Zufallsauswahlen **gleicher Schärfe**, Bezug = ihr Mittelwert |
| **B6** | erste gegen zweite Hälfte, beide müssen dasselbe Vorzeichen zeigen |
| ⭐ **Abnahmeprobe** | über alle Schärfegrade muss die Kontrolle `zufall` **flach** bleiben. Steigt sie mit der Schärfe, ist die Nullwelt falsch gebaut |

---

# § 7 Was diese Messung NICHT beantwortet

| # | |
|---|---|
| **1** | ⛔ **Nicht den Ertrag.** Sie misst die **Ausgangslage**. Was daraus wird, entscheidet die Positionsführung — ausdrücklich Nutzerpunkt |
| **2** | ⛔ **Nicht die Handelbarkeit.** Bei 0,1 % Schärfe sind es ~3 Signale pro Tag; ob sie ausführbar sind, ist ungeprüft |
| **3** | ⚠️ **Nicht die Hebelhöhe selbst.** Die Abstufung (H1b) ist ein **Verhältnis** zwischen Schärfegraden, keine Zahl in Hebelstufen |
| **4** | ⛔ **Nichts über Short** |
| **5** | ⚠️ **Die 2-ATR-Schwelle des Ereignisses ist gesetzt.** Deshalb läuft MFE als stetige Größe daneben — sie braucht keine Schwelle |
