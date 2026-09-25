# Vorabfestlegung 16 — Punkt B: `q` aus **beiden** Seiten

**25.09.2026, geschrieben VOR der Messung.** Nutzerauftrag:

> *„B messen — prüfen und gegenprüfen, zuerst validiere die aktuelle Prüfung
> ob alles nach unseren Standards erfolgt ist und keine groben Fehler
> vorliegen. [...] Die Messung ist wichtig bereite diese sauber auf mit test
> und simulation. [...] der Markt hat sich seit 2023 etwas verändert — mach
> eine zusatz Prüfung für 2023 (nur ein Beispiel) bis heute."*

⚠️ **Die Validierung ist erfolgt und hat vier grobe Mängel an Vorabfestlegung
15 gefunden** (Trennschärfe, Positivkontrolle, B6, Frageart — alle fehlten).
Diese Vorabfestlegung führt sie ausdrücklich, damit der Fehler nicht dritte
Runde bekommt.

---

# § 0 ⭐ FRAGESTELLUNG und HYPOTHESE — vorab festgelegt

## 0.1 Die Fragestellung, in einem Satz

> **Hebt eine Lage, die `momentum_kurz` bzw. `rsi` benennt, die BEDINGTE
> Trefferquote `q` eines Long-Trades (Stop 5 %, Ziel 10 %) über die
> Kelly-Nullstelle 0,3333 — oder hebt sie nur die HÄUFIGKEIT, mit der
> überhaupt eine der beiden Marken fällt?**

## 0.2 Die beiden Hypothesen

| | |
|---|---|
| **H1** | `q` im obersten Fünftel liegt **über 0,3333**, in beiden Historienhälften und beiden Zeitfenstern. ➤ Die Lage sagt, **wohin** es geht — ein Hebel ist gerechtfertigt |
| **H0** | `q` bleibt **unverändert**; der Lift 1,9 aus 2.594 entstand allein aus einer **höheren Auflösungsrate**. ➤ Die Lage sagt nur, **wann** etwas passiert — kein Hebel |

## 0.3 ⭐ Woran H0 zu erkennen ist — der direkte Test

⚠️ **H0 ist nicht einfach „kein Effekt", sondern eine eigene, prüfbare
Aussage.** Sie ist bestätigt, wenn beides zugleich gilt:

| | |
|---|---|
| **1** | die **Auflösungsrate** (ZIEL+STOP)/alle ist im obersten Fünftel **deutlich höher** |
| **2** | `q` ist dort trotzdem **unverändert** |

➤ Deshalb wird die **Auflösungsrate je Fünftel mitgeführt**, nicht nur `q`.
Ohne sie könnte H0 nicht von „gar kein Effekt" unterschieden werden.

## 0.4 ⭐⭐⭐ Die Vorhersage — zwei Mechanismen ziehen GEGENEINANDER

⚠️ **Korrektur meiner ersten Fassung, noch vor dem Lauf.** Dort stand nur
*„q4 zwischen 0,36 und 0,40"*, gestützt auf die Spiegelprobe. Das war
**einseitig** und hat einen eigenen Befund desselben Tages übersehen.

| Richtung | Mechanismus | Stärke des Arguments |
|---|---|---|
| **für H1** | die Spiegelprobe (2.594) zeigt echte Asymmetrie: Lift+ **2,34** gegen Lift− **1,26** | ⚠️ das gespiegelte Ereignis ist der **Short-Gewinn**, nicht der **Long-Verlust** — verwandt, nicht gleich |
| **gegen H1** | **2.592**: die Quote fällt **monoton** mit dem Auflösungsanteil — 0,5526 / 0,5306 / 0,3751 / 0,1972 / **0,0757**. Und `momentum_kurz` erhöht die Auflösung mit hoher Wahrscheinlichkeit | ⭐ **gemessen**, nicht vermutet — und der Mechanismus ist zwingend: der Stop liegt **eine** Einheit entfernt, das Ziel **zwei** |

➤ **Netto ist der Ausgang offen.** Das ist keine Verlegenheit, sondern der
Grund, warum diese Messung zählt. Eine einseitige Vorhersage wäre hier
schlechte Arbeit.

**Festgelegte Bandbreite:** `q4` zwischen **0,26 und 0,40**. Ein Wert unter
`q_alle` wäre ein **eigener Befund** (die Lage wäre dann *schlechter* als der
Durchschnitt, obwohl sie das Ziel häufiger erreicht) — und er würde die
2.592-Mechanik bestätigen.

---

## 0.5 ⭐⭐⭐ Die HAUPTGRÖSSE ist nicht `q` — Einwand gegen die eigene Anlage

⚠️⚠️ **Die Kelly-Formel setzt ZWEI Ausgänge voraus, der reale Trade hat
DREI.** Das ist gemessen (2.586: bei 6 h enden 97,1 % offen). Und ein `q`,
das auf Auflösung **bedingt**, rechnet im obersten Fünftel auf einer
**anderen Teilmenge** als im untersten — derselbe Auswahlfehler wie in 2.592,
nur eine Ebene tiefer.

| Rang | Größe | warum |
|---|---|---|
| ⭐ **1** | **Dreierprofil je Fünftel**: Anteile ZIEL / STOP / OFFEN | zeigt **unbedingt**, was sich verschiebt — und trennt H0 von H1 direkt |
| ⭐ **2** | **Erwartungswert in R**: `E[R] = (ZIEL·CRV − STOP·1 + OFFEN·r_offen) / n` | braucht **keine** Bedingung und beantwortet die Frage, die zählt: rechnet sich ein gehebelter Trade in dieser Lage? |
| **3** | `q` bedingt | bleibt dabei — nur sie ist mit der Kelly-Nullstelle vergleichbar |

⚠️ `r_offen` ist der **tatsächliche** Stand des offenen Ankers am Ende des
Horizonts, in Stopabständen gerechnet — **nicht** null und **nicht**
geschätzt. Ein offener Trade hat ein Ergebnis, es ist nur nicht an einer
Marke entstanden.

⚠️ **Regel 2 bleibt gewahrt:** in `E[R]` stehen **keine** Gebühren und
**keine** Finanzierung. Es ist eine Bewertung, keine Abrechnung.

---

# § 1 Die Frage — und warum sie alles entscheidet

Befund 2.594 hat gemessen, wie oft das **Ziel vor** dem Stop fällt. Für die
Hebelhöhe braucht es die **Gegenseite**:

```
q = P(Ziel vor Stop) / [ P(Ziel vor Stop) + P(Stop vor Ziel) ]
```

| | |
|---|---|
| **Kelly** | `kelly = (q(1+CRV) − 1) / CRV`, Nullstelle `q₀ = 1/(1+CRV)` |
| **Hier** | Stop 5 %, Ziel 10 % → **CRV 2,0** → **q₀ = 0,3333** |

⭐ **Die eine Frage:** liegt `q` im obersten Momentum-Fünftel **über 0,3333**?

⚠️⚠️ **Der ernste Fall, der den Befund kippt:** hebt `momentum_kurz` **beide**
Seiten gleich — weil in dieser Lage einfach *mehr* passiert —, dann bleibt `q`
unverändert und es entsteht **kein Hebel**, trotz Lift 1,9. Das wäre dasselbe
Muster wie bei `vola`, nur eine Ebene tiefer.

---

# § 2 ⭐ Die drei Ausgänge — sauber getrennt

Je Anker, innerhalb `H` Stunden, **Stop zuerst geprüft** (die vorsichtige
Annahme, 2.583):

| Ausgang | |
|---|---|
| **ZIEL** | +10 % erreicht, bevor −5 % fällt |
| **STOP** | −5 % erreicht, bevor +10 % fällt |
| **OFFEN** | keines von beiden in `H` |

| Größe | Formel | wofür |
|---|---|---|
| `q_bedingt` | ZIEL / (ZIEL + STOP) | ⭐ **gegen die Kelly-Nullstelle** — sie gilt für den Pfad ohne Zeitgrenze |
| `q_unbedingt` | ZIEL / alle | die Häufigkeit; **nicht** gegen 0,3333 zu stellen |
| `anteil_offen` | OFFEN / alle | gehört ausgewiesen, nicht verschwiegen |

⚠️ Der Einheitenfehler „unbedingt gegen die Nullstelle" ist mir heute schon
einmal unterlaufen (2.591). Beide Größen werden **getrennt** ausgewiesen.

---

# § 3 ⭐⭐⭐ Welche Standardelemente hier GELTEN — und welche NICHT

**Nutzervorgabe:** *„NUR jene Messstandards berücksichtigen die auch
Gültigkeit haben denn ich glaube wir messen anders und müssen dies korrekt
adaptieren."* — **Richtig.** `messnorm.standardzeile()` ist für
**R-Effekte auf `bewegung_r` mit Tagesklammer** gebaut. Hier wird eine
**Quotendifferenz auf einer binären Zielgröße mit Stundenklammer** gemessen.
Deshalb Element für Element:

## 3.1 ✔ Was unverändert gilt — das Prinzip trägt

| Element | warum es überträgt |
|---|---|
| **Bezug = Nullpunkt** | *„ein Maximum ist kein Schätzer"* gilt unabhängig von der Einheit. Verglichen wird gegen eine Welt **ohne** Effekt, nie gegen null |
| **40 Ziehungen, 90. Perzentil** | eine Konvention über die **Strenge**, nicht über die Größe. Überträgt sich unverändert |
| **Negativkontrolle `zufall`** | prüft die Anlage, nicht die Größe. Gilt |
| **B6 beide Hälften** | eine Aussage über **Stabilität**. Gilt, und bleibt Ausschlusskriterium |
| **Positivkontrolle** | *„findet die Anlage, wofür sie gebaut ist?"* — gilt, nur das Gepflanzte wechselt die Einheit |
| **Trennschärfe gegen denselben Bezug** | das **Prinzip** gilt: man muss die eigene Auflösung kennen |

## 3.2 ⚠️ Was ANGEPASST gilt — dieselbe Frage, andere Einheit

| Element | Norm | **hier** | Begründung |
|---|---|---|---|
| **gepflanzte Stärken** | bis **0,40 R** | **0,0025 … 0,40 in q** | *R* ist auf einer Quote bedeutungslos. Und die Norm-Leiter **beginnt bei 0,02** — auf `q` (Bereich 0–1, Nullstelle 1/3) wäre das eine Spanne von 4 Prozentpunkten, mehr als der ganze erwartete Bereich. Die Verlängerung nach unten folgt aus der **Skala**, nicht aus einem Ergebnis |
| **Klammer** | **Tages**klammer | **Stunden**klammer | die Basis ist stündlich. Der Zweck — die Kopplung innerhalb eines Termins erhalten — ist derselbe |
| **Nullwelt** | durch **Permutation** | **exakt hypergeometrisch** | dieselbe Nullwelt, nur direkt gezogen. ⚠️ **Nachgewiesen**, nicht behauptet: gegen 40 Permutationen geprüft, Abweichung 0,0012–0,0079 im 90. Perzentil (2.594) |
| **Statistik der Zielgröße** | `barriere` → **mittel** | **gepoolte Quote** | bei einer binären Größe *ist* der Mittelwert die Quote. ⚠️ Aber **gepoolt über Anker**, nicht über Termine — ein Trade entsteht je Anker (Regel vom 25.09.) |

## 3.3 ⛔ Was hier NICHT gilt — und warum

| Element | Norm | warum es hier nicht trägt |
|---|---|---|
| **`HORIZONT_JE_LAGE[(hebel,einstieg)] = 3`** | 3 **Tage** | die Zuordnung gehört zur **Tages**kette. Hier sind es 3–12 **Stunden**. ⚠️ Das ist eine **Abweichung und wird ausgewiesen**, kein stiller Bruch |
| **`ZIELGROESSE_JE_LAGE` → `barriere`** | Produktionsgeometrie | die Zielgröße **ist** eine Barriere ✔ — aber mit **eigener** Geometrie (5 % / 10 %). Ausgewiesen |
| ⭐ **`beitrag` → selektierte Menge (F-212)** | Pflicht | ⚠️⚠️ **Die Begründung von F-212 trägt hier nicht:** sie lautet, Beiträge wirkten erst an **Trichterstufe 12** einer Kette, die elf Stufen vorher gefiltert hat. **Eine stündliche Kette gibt es nicht** — es gibt keine Stufe 12, auf die hin selektiert würde. Und die vorhandene Auswahl rangt nach `momentum250`, also **250 Handelstagen** — für einen 6-Stunden-Trade ist das die falsche Dimension, und genau das ist als **P-1** schon offen |
| | | ➤ **Deshalb ist die Frageart hier `markt`**: *„Trägt diese Größe im Markt?"*, Menge = **messuniversum**. Das ist mengenrichtig, und es ist **keine Ausrede** — es ist die Feststellung, dass die `beitrag`-Frage erst gestellt werden kann, wenn es einen stündlichen Kettenpfad gibt |
| | | ⚠️ **Folge für 2.594:** dort steht „Beitrag" im Titel. Als **`markt`**-Befund gilt er; als **`beitrag`** ist er **noch nicht belegt**. Das gehört korrigiert |

## 3.4 Die Elemente dieses Laufs, abschließend

| # | |
|---|---|
| **1** | Nullpunkt: 40 Ziehungen, Zuordnung **innerhalb der Stunde** gemischt, Band **zweiseitig** (10./90.) |
| **2** | Trennschärfe: gepflanzte Leiter in **neutralisierte** Menge, zentriert, Stärken **in q** |
| **3** | Positivkontrolle: gepflanzter Effekt, der gefunden werden **muss** |
| **4** | `zufall` in **jeder** Tabelle |
| **5** | B6 beide Hälften — Ausschlusskriterium |
| **6** | Frageart **`markt`**, Menge **messuniversum** — begründet in 3.3 |
| **7** | `q` **gepoolt** über Anker, Rang **je Stunde** |
| **8** | ⭐ **Auflösungsrate je Fünftel** — der direkte Test auf H0 (§ 0.3) |
| **9** | Riegel: ZIEL und STOP schließen sich aus; Merkmale streng kausal |

---

# § 4 ⭐⭐ TEST UND SIMULATION — Nutzerauftrag, eigener Abschnitt

**Ein Selbsttest gegen bekannte Wahrheit**, wie am 08.09. für die
Mittelwertanlage (2.204). Die Anlage wird auf **künstlichen** Welten geprüft,
in denen die Wahrheit bekannt ist:

| Welt | Aufbau | Erwartung |
|---|---|---|
| **Nullwelten** (100) | `q` je Fünftel **gleich**, nur Rauschen | ⭐ **Fehlalarmquote ≤ 5 %** (einseitig, Band 10./90.) |
| **Effektwelten** (je 20 pro Stärke) | `q` mit **bekanntem** Aufschlag im obersten Fünftel: 0,005 / 0,01 / 0,02 / 0,05 / 0,10 | ⭐ **Fundquote** je Stärke → die tatsächliche Auflösung |
| **Rückgewinnung** | der gepflanzte Aufschlag gegen den **gemessenen** | Abweichung ausgewiesen; systematischer Versatz ist ein **Befund** |

⚠️ **Die Welten tragen die echte Struktur:** Stundenbesetzung und
Ereignishäufigkeit werden aus den echten Daten übernommen, nur die
**Zuordnung** ist gepflanzt. Eine Simulation mit gleichverteilten Stunden
würde die Tageskopplung wegzaubern und die Anlage zu gut aussehen lassen.

⚠️ **Ein Selbsttest prüft die ANLAGE, nicht die DATEN.** Er sagt nichts
darüber, ob die Messbasis in Ordnung ist (dieselbe Einschränkung wie 2.204).

---

# § 5 ⭐ Die ZEITFENSTER — Nutzerhinweis

> *„der Markt hat sich seit 2023 etwas verändert — mach eine zusatz Prüfung
> für 2023 (nur ein Beispiel) bis heute"*

| Fenster | |
|---|---|
| **voll** | 2021-12-01 bis 2026-09-24 |
| ⭐ **ab 2023-01-01** | das Nutzerfenster |
| **B6-Hälften** | des jeweiligen Fensters |

⚠️ **Ein Fensterwechsel ändert die Grundgesamtheit** (stehende Regel). Die
Ankerzahl je Fenster wird ausgewiesen, und ein Unterschied zwischen den
Fenstern ist **ein Befund über die Zeit**, nicht ein Grund, sich das bessere
auszusuchen.

⚠️ Und: *„2023 ist nur ein Beispiel"* — deshalb wird `q` **je Jahr**
mitgeführt, damit sichtbar ist, ob 2023 wirklich der Bruch ist oder ein
willkürlicher Schnitt.

---

# § 6 Was gemessen wird

| | |
|---|---|
| **Kandidaten** | `momentum_kurz`, `rsi` (die zwei Überlebenden), plus `vola` als **Gegenprobe** (sie hat Lift, aber soll `q` NICHT heben) und `zufall` |
| **Redundanz** | ⭐ Punkt A gleich mit: Korrelation `momentum_kurz` × `rsi`, und `q` im **Schnitt** beider obersten Fünftel gegen jedes einzeln |
| **Geometrie** | Stop 5 %, Ziel 10 % (CRV 2). ⚠️ **Nicht** die Produktionsgeometrie — ausgewiesen, nicht stillschweigend |
| **Horizonte** | 3 / 6 / 12 / 24 Stunden |
| **Vola-Kontrolle** | Dosis-Wirkung 1 / 3 / 5 Bänder (8 fiel aus: dort war `zufall` außerhalb des Bands) |

---

# § 7 ⭐ Die ENTSCHEIDUNGSREGEL — vorab, wird nicht nachverhandelt

| # | Bedingung | Folge |
|---|---|---|
| **0** | Selbsttest: Fehlalarmquote ≤ 5 % **und** Positivkontrolle gefunden | sonst **Anlage blind, Lauf ungültig** |
| **1** | `zufall` im Nullband, in jeder Stufe | sonst **Zelle ungültig** |
| **2** | `q` im obersten Fünftel **> 0,3333**, außerhalb des Nullbands, **und** die Spanne über der gemessenen Auflösung | ⭐ **Hebel gerechtfertigt** |
| **3** | hält in **beiden** Hälften **und** in **beiden** Zeitfenstern | sonst: **Regimeabhängig** — eigener Befund, kein Hebel |
| **4** | hält bei festgehaltener `vola` (Dosis-Wirkung) | sonst **Volatilität** |
| **5** | `q` steigt **nicht** über 0,3333, obwohl der Lift hoch ist | ⛔ **Punkt B kippt 2.594 als Hebelbefund** — die Lage sagt *wann etwas passiert*, nicht *in welche Richtung es ausgeht* |
| ⭐ **5a** | **`E[R]` im obersten Fünftel > 0** und außerhalb des Nullbands | ⭐ **das ist das eigentliche Kriterium** — es braucht keine Bedingung und keine Zwei-Ausgangs-Annahme |
| **5b** | `E[R]` ≤ 0, aber `q` > 0,3333 | ⚠️ **Widerspruch, der aufzulösen ist** — dann trägt die Annahme „zwei Ausgänge", und der Befund gilt nur unter ihr |
| **6** | `vola` hebt `q` genauso stark | ⛔ die Trennung Richtung/Bewegung war unzureichend |

---

# § 8 Die Vorhersage

**Erwartung: `q` steigt, aber weniger als der Lift vermuten lässt.**

**Begründung:** die Spiegelprobe zeigt Lift+ 2,34 gegen Lift− 1,26 — eine
echte Asymmetrie, also sollte `q` steigen. Aber das gespiegelte Ereignis ist
der **Short-Gewinn**, nicht der **Long-Verlust**; die beiden sind verwandt,
nicht gleich. ⚠️ **Ein Teil der Asymmetrie kann daher verschwinden.**

Zahl: `q` im obersten Fünftel **0,36 bis 0,40** gegen eine Basis von rund
0,28 bis 0,33.

---

# § 9 Was diese Messung **nicht** entscheidet

- **Nicht** SHORT. ⭐ **Nutzervorgabe:** *„den hinweis zu Short kannst du in
  den Plan eintragen wenn dies bei Long passen sollte"* → wird als Planpunkt
  eingetragen, sobald LONG trägt. Nicht mitgemessen.
- **Nicht** die Handelbarkeit (Liquidität, Slippage, Ausführung).
- **Nicht** die Geometrie (Punkt F) — zurückgestellt.
- **Nicht** die Hebel**höhe in x**. Die folgt aus `q`, braucht aber die
  Klammer, und die ist eine Nutzerentscheidung.
