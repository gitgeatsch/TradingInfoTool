# Der neue Hebel-Arm, Schritt 1: die lageneutrale Geometrie

**25.09.2026** · Werkzeug `messe_hebel_geometrie_neutral.py` ·
**116 Symbole · 3.237.922 Anker · nur lesend**

**Auftrag:** *„wir bauen den Hebel Arm vollständig neu. Wenn Hebel
funktioniert dann gehen wir zu den anderen Strategien."*

---

# § 1 Das Ergebnis in drei Sätzen

> ✔✔ **Die Geometrie ist jetzt lageneutral** — bei `k ≤ 1,0` ist der Stop in
> jedem Momentumfünftel gleich weit (Spanne 0,0039 ATR). Der alte fixe
> Prozentstop ist es nicht: **0,80 / 0,92 / 0,93 / 0,90 / 0,72 ATR.**
>
> ⭐⭐⭐ **Und dabei ist ein Messfehler in 2.595 aufgefallen, der das Urteil
> dreht:** dort wurde `E[R]` gegen **null** verglichen. Der richtige Bezug
> ist die **Drift**. Netto ist das oberste Momentumfünftel in **allen zwölf**
> Zellen das **beste** — nicht das schlechteste.
>
> ⚠️ **Was daraus NICHT folgt:** dass der Hebel trägt. Die Nettobeträge sind
> +0,0008 bis +0,0072 R. Das ist gemessen und über dem Nullband, aber es ist
> ein Zehntel dessen, was 2.595 an Lücke ausgewiesen hat.

**Belegt durch:** Nullband in **9 von 9** Zellen bestanden (Faktor 4,3–11,1) ·
Positivkontrolle **5 von 45** Nullziehungen = **11,1 %** gegen Soll 10,0 % ·
2.596 reproduziert auf **0,7 %** · Optional Stopping auf **5 Dezimalstellen**.

⚠️ **Eine Einschränkung vorweg, nicht versteckt:** die Auflösung liegt bei
**Anteil 0,50** echter Ordnung. Ein halb so stark ordnendes Merkmal würde
diese Anlage in 6 von 9 Zellen **nicht** von null unterscheiden (§ 6.3).

---

# § 2 ⚠️⚠️ Beide Abnahmeproben waren falsch gebaut — und die Gegenprüfung hat es gefunden

Das Werkzeug trat mit zwei Proben an. **Keine von beiden hätte etwas
geprüft.** Die Fehler wurden vor dem Urteil gefunden, nicht danach.

| Probe | Der Fehler | Die Korrektur |
|---|---|---|
| **1** | ⛔ **Tautologie.** `clip(k·ATR, …)/ATR` **ist** k, solange die Klammer nicht bindet. Eine Spanne nahe null war Arithmetik, kein Nachweis | **gepaarter FIX-Arm** — derselbe Anker, dieselbe Ankermenge, fixer Prozentstop. Er muss 2.596 reproduzieren (R-R11) |
| **2** | ⛔ **Falscher Nullpunkt.** `E[R]_alle ≈ 0` gilt nur driftfrei. 116 Kryptowerte über vier Jahre sind nicht driftfrei | gegen **`mean(RO)`** — die H-Stunden-Rendite in Stopabständen **ohne** Barrieren, auf derselben Menge |

⚠️⚠️ **Und ein dritter Fehler war meine eigene Erklärung.** Ich hatte das
negative `E[R]` der Stop-zuerst-Konvention zugeschrieben (2.583) und einen
Gleichstandszähler eingebaut, um es zu belegen. **Der Zähler hat die
Erklärung widerlegt:** Gleichstand 0,002 %, gedeckt wären damit 0,0004 R —
gemessen wurden 0,0037 bis 0,0182. **Faktor 10 bis 45 daneben.**

➤ **Eine Erklärung, die man messen kann, ist zu messen.** Sie stand schon
als Kommentar im Code, bevor sie geprüft war.

---

# § 3 ✔✔ PROBE 1 — und die Reproduktion von 2.596 (R-R11)

**Der Stop in ATR-Einheiten, je Fünftel nach `momentum_kurz`:**

| Geometrie | 0 | 1 | 2 | 3 | **4** | Spanne | Verhältnis 2/4 |
|---|---|---|---|---|---|---|---|
| **2.596** (alt, 5 % fix) | 0,753 | 0,858 | 0,868 | 0,839 | **0,674** | — | **1,288** |
| **FIX 5 %** (neu) | 0,8010 | 0,9167 | 0,9268 | 0,8961 | **0,7246** | 0,2023 ⚠️ | **1,279** |
| **FIX 8 %** (neu) | 1,2816 | 1,4667 | 1,4829 | 1,4338 | **1,1593** | 0,3236 ⚠️ | **1,279** |
| **k = 0,75 × ATR** | 0,7578 | 0,7597 | 0,7599 | 0,7599 | 0,7580 | **0,0021** ✔ | 1,003 |
| **k = 1,0 × ATR** | 1,0022 | 1,0040 | 1,0042 | 1,0043 | 1,0004 | **0,0039** ✔ | 1,004 |
| **k = 1,5 × ATR** | 1,4895 | 1,4972 | 1,4977 | 1,4971 | 1,4748 | 0,0229 ⚠️ | 1,016 |

**Drei Dinge stehen da:**

| | |
|---|---|
| ✔✔ **2.596 ist reproduziert** | Verzerrungsfaktor **1,279 gegen 1,288** — Abweichung **0,7 %**. Das Niveau liegt 7 % höher (anderes ATR-Maß), die **Struktur** hält exakt: U-Form, Gipfel in Fünftel 2, Minimum in Fünftel 4, und Fünftel 4 **unter** Fünftel 0 |
| ⭐ **Dosis-Wirkung** | 5 % und 8 % liefern **denselben** Faktor 1,279. Die Verzerrung ist rein multiplikativ — genau wie sie sein muss, wenn sie vom ATR kommt und nicht von der Stopgröße. Ein Artefakt hätte sich mit der Dosis verändert |
| ⚠️ **k = 1,5 fällt durch** | Spanne 0,0229 gegen die Grenze 0,02. Ursache ist die **Obergrenze 25 %**: sie bindet in volatilen Lagen häufiger und holt die Lageabhängigkeit durch die Hintertür zurück. ➤ **Nur k ≤ 1,0 ist verwendbar** |

---

# § 4 ✔✔ PROBE 2 — der Nullpunkt ist die Drift, nicht null

Eine Stoppregel auf einem Martingal ändert den Erwartungswert nicht
(*Optional Stopping*). Also muss `E[R]_alle` der barrierenfreien Rendite
folgen — und das tut es:

| k = 1,0 | `E[R]_alle` | Drift (Halten) | **Rest** | Gleichstand |
|---|---|---|---|---|
| CRV 4,0 · H6 | −0,00294 | −0,00295 | **+0,00001** | 0,000 % |
| CRV 3,0 · H6 | −0,00283 | −0,00295 | +0,00012 | 0,001 % |
| CRV 1,5 · H6 | −0,00266 | −0,00295 | +0,00029 | 0,002 % |
| CRV 4,0 · H24 | −0,00899 | −0,01189 | +0,00290 | 0,001 % |
| CRV 1,5 · H24 | −0,00875 | −0,01189 | +0,00314 | 0,008 % |

⭐⭐ **Die Übereinstimmung ist selbst eine Dosis-Wirkung.** Je weniger die
Barrieren binden (weites Ziel, kurzer Horizont), desto exakter gilt der Satz
— bei CRV 4,0 / H6 auf **fünf Dezimalstellen**. Der Rest ist durchgehend
**positiv** und wächst mit dem Horizont: das ist der **Stopschutz**, die
Barriere schneidet tiefe Fälle ab.

➤ **Damit ist die Barrierenrechnung nachgewiesen**, nicht bloß plausibel.
Ein Vorzeichenfehler, ein verschobener Index oder eine falsche Klammer hätte
diese Übereinstimmung nicht überlebt.

---

# § 5 ⭐⭐⭐ Die Folge: 2.595 hat am falschen Nullpunkt gemessen

**Dieselben Daten, k = 1,0 · CRV 1,5 · H6, je Fünftel nach `momentum_kurz`:**

| | 0 | 1 | 2 | 3 | **4** |
|---|---|---|---|---|---|
| **Drift (Halten)** | −0,0020 | −0,0014 | −0,0021 | −0,0031 | **−0,0062** |
| `E[R]` brutto | −0,0025 | −0,0015 | −0,0021 | −0,0029 | −0,0042 |
| ⭐ **`E[R]` NETTO** | −0,0005 | −0,0001 | −0,0000 | +0,0002 | **+0,0020** |
| `q` (bedingt) | 0,2163 | 0,1903 | 0,2061 | 0,2594 | **0,4210** |

## 5.1 Was die Driftzeile sagt

⚠️ **Das oberste Momentumfünftel hat die schlechteste Drift** — −0,0062 gegen
−0,0014 in Fünftel 1, **Faktor 4,4**. Nach einem kurzen scharfen Anstieg
fallen diese Werte im Schnitt am stärksten zurück.

➤ **Genau das hat 2.595 gemessen und als Urteil über die Handlung
ausgegeben.** Dort stand: *„`E[R]` wird im obersten Fünftel schlechter
(−0,0091 gegen −0,0056)"*, und daraus folgte *„die Lage trägt keinen Hebel"*.
Die Zahl war richtig. Der Bezug war es nicht: **verglichen wurde gegen null,
also gegen ein Halten, das es nicht gibt.**

## 5.2 ⭐ Und die Kelly-Nullstelle ist erstmals überschritten

`q4` = **0,4210** gegen die Nullstelle `1/(1+1,5)` = **0,4000**.

⚠️⚠️ **Die Einheiten stimmen diesmal** — und das ist nicht selbstverständlich:
beide Größen sind **bedingte** Quoten, gerechnet auf die **aufgelösten**
Anker. Derselbe Vergleich war in dieser Messreihe schon einmal als
Einheitenfehler gestellt worden (unbedingte Quote gegen bedingte Nullstelle).

➤ **Das gilt nur bei CRV 1,5 / H6.** Bei CRV 2,0 / 3,0 / 4,0 bleibt `q4`
unter der jeweiligen Nullstelle (0,2583 gegen 0,3333 · 0,1121 gegen 0,25 ·
0,0634 gegen 0,20).

⚠️ **Und Kelly reicht trotzdem nicht als Begründung:** bei H6 lösen nur rund
**7 %** der Anker auf. Die anderen 93 % tragen die Drift, und Kelly kennt
diesen dritten Ausgang nicht (2.586). **`E[R]` netto bleibt die Hauptgröße** —
und das sind +0,0020 R, nicht die 0,42 aus der Quote.

---

# § 6 ✔✔ Nullband, Trennschärfe, Positivkontrolle

**Die Nullwelt zieht das Fünftel zufällig**, behält aber die Stundenklammer
und die Fünftelgrößen. Sie beantwortet damit genau *„ordnet `momentum_kurz`
besser als ein Würfel?"* — nicht *„ist die Zahl groß?"*.

## 6.1 Das Nullband — alle neun Zellen trennen

**k = 1,0 · 40 Ziehungen je Zelle · Bezug = Mittelwert, Grenze = 90. Perzentil**

| CRV | H | Nullpunkt | 90. Perzentil | **gemessen** | Faktor |
|---|---|---|---|---|---|
| 1,5 | 6 | +0,00003 | +0,00023 | **+0,00207** | **10,2** |
| 1,5 | 12 | +0,00000 | +0,00042 | **+0,00347** | 8,3 |
| 1,5 | 24 | +0,00004 | +0,00049 | **+0,00505** | **11,1** |
| 2,0 | 6 | −0,00000 | +0,00015 | **+0,00152** | 9,7 |
| 2,0 | 12 | +0,00007 | +0,00038 | **+0,00263** | 8,3 |
| 2,0 | 24 | −0,00009 | +0,00063 | **+0,00394** | 5,6 |
| 3,0 | 6 | +0,00001 | +0,00026 | **+0,00108** | 4,3 |
| 3,0 | 12 | +0,00002 | +0,00027 | **+0,00167** | 6,6 |
| 3,0 | 24 | +0,00000 | +0,00044 | **+0,00282** | 6,5 |

✔✔ **Der Nullpunkt liegt in allen neun Zellen bei ≈ 0** (−0,00009 bis
+0,00007). Das ist die Selbstauskunft der Anlage: sie erzeugt aus einem
Würfel keinen Effekt.

## 6.2 ⭐⭐⭐ Die Positivkontrolle ist exakt geeicht — sichtbar erst in der Summe

Stufe 0,00 ist reiner Zufall und **darf nicht** trennen. Je Zelle 5
Ziehungen, also **45 insgesamt**:

| | |
|---|---|
| als „gefunden" gemeldet | **5 von 45** = **11,1 %** |
| Sollwert bei einem 90.-Perzentil-Band | **10,0 %** — per Konstruktion liegen 10 % darüber |
| 95-%-Schranke (binomial, 5 von 45) | rund 24 % → ✔ **geeicht** |

⚠️⚠️ **Und ein Ausweisungsfehler im Werkzeug, der dazugehört:** zwei Zellen
melden bei Stufe 0,00 eine Fundquote von 40 % und werden mit
`⚠️ FEHLALARM` markiert. Das ist **falsch etikettiert** — bei 5 Ziehungen
sind nur die Quoten 0/20/40/60/80/100 % möglich, und P(≥2 von 5 bei 10 %) =
8 % je Zelle, bei 9 Zellen also 0,7 erwartete Vorkommen. Beobachtet: 2.

➤ **Die Meldung urteilt je Zelle, wo nur die Summe aussagekräftig ist.** Die
Messung ist richtig, die Kennzeichnung ist zu hart. Kein Messfehler, aber er
gehört benannt, weil er sonst beim nächsten Lesen als Befund gilt.

## 6.3 ⚠️ Die Trennschärfe ist grob — die Zahl gehört ausgesprochen

**Anteil echter Ordnung, der in den Zufall gemischt wird → wo schlägt die
Anlage an? (Fundquote ≥ 80 % = aufgelöst)**

| Anteil | 0,00 | 0,05 | 0,10 | 0,25 | **0,50** | 1,00 |
|---|---|---|---|---|---|---|
| **Zellen aufgelöst (von 9)** | 0 | 0 | 0 | **3** | **9** | 9 |

| | |
|---|---|
| ✔ **Die Anlage findet den echten Effekt** | in **9 von 9** Zellen, Faktor 4,3–11,1 über dem Band |
| ⚠️ **Aber die Auflösung liegt bei Anteil 0,50** | ein **halb so geordnetes** Merkmal würde in 6 von 9 Zellen **nicht** gefunden |
| ⚠️ **Unter 0,25 ist die Anlage blind** | bei 0,05 und 0,10 löst **keine** Zelle auf |

➤ **Das heißt: dieser Befund steht, aber die Messform taugt nicht zum
Vergleich schwächerer Merkmale.** Wenn die A-Faktoren (Trendstruktur,
EMA-Lage, `rsi`-Änderung) gemessen werden und schwächer ordnen als
`momentum_kurz`, kann diese Anlage sie **nicht von null unterscheiden** —
dann braucht es mehr Anker je Zelle oder eine engere Frage, nicht mehr
Ziehungen.

⚠️ **Und der Vorbehalt, der bleibt:** ein Selbsttest prüft die **Anlage**,
nicht die **Daten**. Er sagt nichts darüber, ob die Messbasis kontaminiert
ist.

## 5.3 ⚠️⚠️⚠️ Die Einordnung, die den Fund kleiner macht — NIVEAU gegen QUERSCHNITT

**Nachgezählt über alle 60 Zellen: `E[R]` brutto ist in 0 von 60 positiv.**
Der beste Wert ist **−0,0034**, der schlechteste −0,0302.

➤ **Damit beantworten 2.595 und 2.597 zwei verschiedene Fragen, und beide
gelten:**

| Frage | Maßstab | Antwort |
|---|---|---|
| **Querschnitt** — *welche Lage ist besser als die andere?* | **Netto** (gegen die Drift) | ✔ das oberste Momentumfünftel, in allen 12 Zellen, über dem Nullband |
| **Niveau** — *soll überhaupt gehandelt werden?* | **Brutto** (gegen null) | ⛔ **nein, in 0 von 60 Zellen** |

⚠️⚠️ **Der Hebel braucht die NIVEAUfrage.** Ein Hebelgeschäft ist nicht die
Alternative zu *„diesen Wert halten"*, sondern zu *„kein Geschäft machen"* —
und gegen „kein Geschäft" ist der Maßstab **null**, nicht die Drift.

➤ **Mein Fund dreht also nicht das Hebelurteil, sondern nur die Aussage über
die Ordenbarkeit** — und die war mit 2.594 schon beantwortet. **2.595 behält
für die Hebelfrage recht.** Was fällt, ist allein seine *Begründung*
(*„`E[R]` wird in der besten Lage schlechter"* ist ein Driftbefund, kein
Lagebefund), nicht sein *Schluss*.

⚠️ Das ist genau die schon registrierte Regel **Niveau → gepoolt, Querschnitt
→ Klammer**, hier in anderer Gestalt: **wer den Maßstab wechselt, wechselt die
Frage.** Ich hatte die Nettogröße als Antwort auf die Hebelfrage gelesen; sie
ist es nicht.

## 5.4 ⭐ Und was die Driftzeile dafür aufwirft

Die Drift ist in **jedem** Fünftel und **jeder** Zelle negativ (−0,0014 bis
−0,0210). Auf dem Niveau trägt Long also nirgends — **und die Spiegelrichtung
ist damit die erste, die eine Niveauchance hat.**

⚠️⚠️ **Aber das ist noch kein Argument, sondern eine Frage:** eine über 116
Altcoins und vier Jahre durchgehend negative Drift ist ein Kandidat für
**Regimewette und Überlebensverzerrung**, nicht für einen Beitrag. Wer darauf
short geht, wettet auf das Fenster, nicht auf die Lage. ➤ Zu prüfen wäre die
Drift **je Jahr** und **je Symbolklasse**, bevor daraus irgendetwas folgt.

---

# § 7 ⛔ Was aus alldem NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Nicht, dass der Hebel trägt.** Netto +0,0008 bis +0,0072 R ist über dem Nullband, aber klein. Ob daraus eine Hebelhöhe wird, ist eine **eigene** Rechnung und nicht gestellt |
| **2** | ⛔ **Nicht, dass 2.594 falsch war.** Die Ordenbarkeit der Lage (Lift ~1,9) bleibt; sie wird hier **bestätigt**, nicht ersetzt |
| **3** | ⛔ **Nicht, dass `momentum_kurz` der richtige Faktor ist.** Es ist das Merkmal, mit dem die **Geometrie** geprüft wurde — weil 2.596 daran gemessen war. Die fachliche Anordnung `A ∧ B ∧ ¬C` ist unberührt |
| **4** | ⛔ **Nicht, dass k = 1,0 die richtige Stopweite ist.** Gemessen ist nur, dass k ≤ 1,0 **lageneutral** ist. Welches k das beste `E[R]` liefert, ist eine andere Frage |
| **5** | ⛔ **Nichts über Handelbarkeit.** Liquidität, Slippage und Ausführung sind nicht geprüft — bei 3,2 Mio Ankern über 116 Symbole ist das ein offener Vorbehalt, kein Nebenpunkt |
| **6** | ⚠️ **Die Drift ist ein Fensterbefund.** −0,003 bis −0,012 R über 2021-12 bis 2026-09. In einem anderen Marktfenster ist sie eine andere Zahl, und dann verschiebt sich der Nullpunkt mit |

---

# § 8 Welche Standards galten

| | |
|---|---|
| **gilt** | Bezug = Nullpunkt · 40 Ziehungen, 90. Perzentil · Trennschärfe gegen denselben Bezug · Positivkontrolle 5 Ziehungen · **R-R11** (2.596 reproduziert) · Dosis-Wirkung |
| **angepasst** | **Stunden**klammer statt Tagesklammer · Nullwelt durch **Zufallsfünftel** statt Permutation (erhält Stundenstruktur und Fünftelgrößen) · gepflanzte Stärke als **Anteil echter Ordnung** statt in R |
| **gilt nicht** | `HORIZONT_JE_LAGE` = 3 Tage · Produktionsgeometrie · **F-212 selektierte Menge** (keine stündliche Kette, also keine Trichterstufe 12) |
| ➤ **Frageart** | **`geometrie`** — Menge = Messuniversum. Dies ist **keine** Beitragsmessung |

---

# § 9 Offen

| # | |
|---|---|
| ⭐ **1** | **`E[R]` netto über k** — k = 0,75 gegen 1,0, welches trägt mehr? Beide sind lageneutral |
| ⭐ **2** | **Die A-Faktoren bauen** (Trendstruktur, EMA-Lage/-Steigung, `rsi`-Änderung, EMA-Abstand in ATR, Bandenge) und **auf NETTO** messen — nicht auf brutto |
| **3** | **Die Drift selbst als Merkmal prüfen:** wenn Fünftel 4 die schlechteste Drift hat, ist die Driftlage ordenbar — und dann ist sie ein Kandidat für **¬C** (Risikosperre) |
| **4** | **Ist die Netto-Größe im Betrieb überhaupt erreichbar?** Sie setzt voraus, dass man die Alternative „halten" tatsächlich hat. Bei einem Hebelgeschäft auf Termin ist das zu prüfen |
| **5** | Handelbarkeit (aus § 7.5) |
| ⛔ **6** | **Short** — ruht weiter, bis Long trägt |
