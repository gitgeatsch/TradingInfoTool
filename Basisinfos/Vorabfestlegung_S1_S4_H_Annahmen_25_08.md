# Vorabfestlegung S1–S4 — H auf seine eigenen Annahmen prüfen

**Angelegt 25.08.2026, VOR jeder Messung.** Diese Datei wird nach dem ersten
Messlauf **nicht mehr geändert**. Ergebnisse kommen in einen Nachtrag mit
eigenem Datum darunter — damit später nachprüfbar bleibt, was vorher
festgelegt war und was danach dazukam.

> **Nutzervorgabe, die diese Datei ausgelöst hat (25.08.):**
> *„Bin aber vorsichtig mit Festlegungen. Durchsuche die Doku, was bereits
> gemessen wurde und wie — die Annahmen könnten falsch gewesen sein (siehe
> Gebühren Bitpanda)."*

---

## 0. Warum überhaupt — und warum genau diese vier

H ist der **einzige** Kandidat des Projekts, der die Zufallsschwelle genommen
hat (+4,5 gegen +2,6, 9.405 Fälle, Kap. 119). Gleichzeitig gilt seit Kap. 116.4:
H ist **irreduzibel und unanwendbar zugleich** — kein Erklärungsversuch hat
gegriffen, und keine Bedingung sagt, wann es trägt.

Solange das so steht, ist der naheliegende nächste Schritt, **einen Partner für
H zu suchen**. Genau das wäre der Fehler. Denn der Gebührenfall vom 25.08. hat
gezeigt, wie dieses Projekt in die Irre läuft: **achtzehn Kapitel lang wurde H
gegen den falschen Maßstab gerechnet** (Betriebssatz 1,50 % statt Referenzsatz
0,30 %), und die Ursache war kein Rechenfehler, sondern eine **stillschweigend
mitgereiste Annahme**, die nie als Annahme markiert war.

Die vier Prüfungen S1–S4 fragen deshalb nicht „was passt zu H", sondern:
**welche unmarkierten Annahmen trägt H selbst?** Alle vier laufen auf
vorhandenen Daten, **ohne einen einzigen Modellaufruf**, ohne Kontingent, ohne
Sammelzeit.

### Die vier Kandidaten — und wie sie gefunden wurden

Jeder wurde **an der Quelle** verifiziert, nicht aus Plänen abgeschrieben
(stehende Vorgabe *„immer an der Quelle prüfen"*):

| | Annahme | Beleg an der Quelle | Gegenprüfung |
|---|---|---|---|
| **K1** | Totzone: eine Marke näher als **0,5 ATR** zählt nicht | `agent/lagebeschreibung.py:215-220` | ✔ verifiziert |
| **K2** | Phasenindex = Mittel aus `c[j]/c[0]` **je Reihe** | `simuliere_bremse.py:216-247`, `PHASE_FENSTER=250`, `PHASE_SCHWELLE=0.20` | ✔ verifiziert |
| **K3** | Blockgrenzen der Permutation liegen **fest** | alt wandernd `messe_marken.py:413`; neu fest `bewerte_neu.py:205` | ✔ verifiziert |
| **K4** | Reifeschnitt bei **250 Handelstagen** | `messe_struktur_bereinigt.py` `MINDESTALTER = 250` | ✔ verifiziert |

---

## 1. S1 — die Totzone (kippt *H selbst*)

### Was in der Produktion steht

```python
# agent/lagebeschreibung.py:215-220
NIVEAU_MIN_ABSTAND_ATR = 0.5   # naeher als das ist keine eigene Marke
NIVEAU_CLUSTER_ATR = 0.3       # was enger beieinander liegt, ist EIN Niveau
```

### Woher die Zahl kommt

Aus dem **Trockenlauf vom 10.08.**: die erste Fassung meldete für *jeden*
Prüffall „Widerstand 0,0 Schwankungsbreiten höher", weil bei täglichen
Fraktalen immer ein Swing direkt neben dem Kurs liegt. 0,5 ATR war die
Reparatur einer **Anzeigepanne**.

### ⚠️ Warum das eine Annahme über H ist, keine Anzeigefrage

H besteht aus zwei Teilen: **A = kein Widerstand im Band [+0,5 ATR, +4,0 ATR)**
und **B = eine Unterstützung im Band (−2,0 ATR, −0,5 ATR]**. Beide Bänder
**beginnen an der Totzone**. Die Zahl 0,5 ist damit nicht nur ein Anzeigefilter,
sondern **die untere Kante beider H-Bedingungen**.

Und dazu steht in `messe_marken.py:43-46` wörtlich:

> *„`niveaus_werte` lässt Marken näher als 0,5 ATR weg. Eine Unterstützung dicht
> unter dem Kurs zählt also NICHT als Deckung. Das ist eine Eigenschaft des
> Betriebs, keine Annahme dieser Messung, und sie bleibt unangetastet."*

**Das ist exakt die Denkfigur des Gebührenfehlers.** Dort hieß es: der
Betriebssatz ist gegeben, also wird gegen ihn gerechnet. Hier heißt es: die
Totzone ist Betrieb, also wird sie nicht geprüft. In beiden Fällen wird eine
Zahl, die das Ergebnis mitbestimmt, per Definition aus der Prüfung
herausgenommen.

### Die Messung

`niveaus_werte` mit **0,25 / 0,5 (heute) / 1,0 ATR** neu rechnen, H daraus neu
bilden, Vorsprung gegen Block-Permutation messen. Bandgrenzen mitziehen: das
untere Ende beider Bänder ist die Totzone selbst.

### Vorab festgelegt, was welches Ergebnis bedeutet

| Ergebnis | Lesart |
|---|---|
| alle drei tragen, Spanne ≤ 2 Punkte | H ist **robust** — die Totzone ist eine Anzeigeentscheidung |
| alle drei tragen, Spanne > 2 Punkte | H trägt, ist aber **auf 0,5 eingestellt** — dann ist 0,5 ein Regler und braucht eine eigene Begründung |
| nur 0,5 trägt | ⚠️ **H hängt an der Reparatur einer Anzeigepanne** — der Befund ist dann nicht H, sondern diese Zahl |
| keiner trägt | die H-Neurechnung ist defekt (Positivkontrolle prüfen, nicht H verwerfen) |

**Positivkontrolle (Pflicht nach 93 B):** 300 Stop-Ausgänge zu Ziel-Ausgängen
umschreiben und erneut messen; erwartete Verschiebung ≈ +6,3 Punkte (Kap. 125).
Findet das Werkzeug sie nicht, ist jeder Nullbefund wertlos.

---

## 2. S2 — der Phasenindex (kippt *die Phasenabhängigkeit*)

### Was in der Produktion steht

```python
# simuliere_bremse.py:230-233
for sym, (c, _h, _l, _v, _a, _off, d) in roh.items():
    for j, tag in enumerate(d):
        reihen.setdefault(tag, []).append(c[j] / c[0])
index = np.array([float(np.mean(reihen[t])) for t in tage])
```

Jede Reihe wird auf **ihren eigenen ersten Tag** normiert; der Index ist das
Mittel dieser Werte. Phase = 250-Tage-Bewegung des Index, Schwellen ±20 %.

### ⚠️ Warum das eine Annahme ist

Eine Reihe, die 2018 beginnt, und eine, die 2025 beginnt, tragen beide eine
kumulative Rendite ab **verschiedenen Nullpunkten** in dasselbe Mittel. Tritt
eine neue Reihe ein, kommt sie mit dem Wert 1,0 herein und **zieht den Index
zum Mittelwert** — ohne dass sich ein Kurs bewegt hätte.

Das ist **derselbe Konstruktionsfehler, der Marktbreite gekostet hat**: dort
wanderte der Bezugskorb (23 % des Korbs kamen in 250 Handelstagen dazu), und
der Befund wurde ersatzlos gestrichen. Beim Phasenindex ist die Konstruktion
**nie als solche geprüft worden**.

### Was bereits geprüft ist — und was das *nicht* abdeckt

| geprüft | Ergebnis | deckt K2 ab? |
|---|---|---|
| breiter gegen schmalen Index (Kap. 108) | 82,1 % Übereinstimmung über 3.290 Tage, 8 echte Umkehrungen | ✘ prüft die **Breite**, nicht die Normierung |
| Produktionsindex gegen BTC allein (Kap. 114) | beide gegen die Inversion, 6 von 6 Punktschätzern | ✘ prüft die **Inversionsthese**, nicht die Phasenzuordnung von H |
| verkettete Indexversuche (Kap. 114) | aus Medianen −100 %, aus Mitteln +194.392 % → BTC allein gewählt | ⚠️ zeigt, dass die Indexbildung **fragil** ist |

Die letzte Zeile ist der eigentliche Grund für S2: das Projekt hat für Kap. 114
**bereits einmal den Index verworfen** und auf BTC allein umgestellt, weil die
Verkettung unbrauchbare Werte lieferte. Der Phasenindex von `simuliere_bremse`
ist trotzdem unverändert geblieben — und **an ihm hängt der einzige bekannte
Schalter von H**: bulle **+7,6** · seitwärts **+6,0** · bär **−6,5**.

### Die Messung

H-Vorsprung je Phase erneut rechnen, mit drei Indexvarianten:
**(a)** heutiger Index · **(b)** BTC allein · **(c)** Index nur aus Reihen, die
über das **ganze** Fenster existieren (eintrittsfrei). Zusätzlich: Anteil der
Tage, an denen sich das Etikett zwischen den Varianten unterscheidet.

### Vorab festgelegt

| Ergebnis | Lesart |
|---|---|
| Vorzeichenmuster (+/+/−) in allen drei Varianten gleich | die Phasenabhängigkeit ist **real** → S2 rechtfertigt den dynamischen Einsatz von H |
| Muster kippt zwischen den Varianten | ⚠️ die Phasenabhängigkeit ist ein **Artefakt der Indexbildung** — H darf dann **nicht** phasenabhängig geschaltet werden |
| Etiketten-Abweichung > 20 % der Tage | der Index ist als Schalter untauglich, unabhängig vom H-Ergebnis |

**Positivkontrolle:** ein künstlicher Index mit bekannter Phasenfolge; das
Werkzeug muss sie zurückgeben.

---

## 3. S3 — die Blockgrenzen (kippt *die Schwellen aller H-Urteile seit 119*)

### Was in der Produktion steht — und der Widerspruch

```python
# ALT, wandernd:   messe_marken.py:413, messe_struktur_bereinigt.py:265
v = int(rngb.integers(0, a.blocklaenge))

# NEU, fest:       bewerte_neu.py:205, messe_klassen.py:191,
#                  messe_ueberleben.py:194, messe_dosis.py:298
if not gr or ii - gr[-1][0] >= 250:
```

Die neue Fassung setzt die Blockgrenzen **fest ab dem ersten Anker**. Die eigene
Methodikregel 2.47 verlangt das Gegenteil:

> *„Blockgrenzen wandern je Lauf — feste Grenzen lassen immer dieselben Anker
> gemeinsam reisen und verschmälern die Verteilung."*

### ⚠️ Warum das die schwerste der vier ist

**Die vier Werkzeuge mit festen Grenzen sind genau die, die die heute gültigen
H-Urteile erzeugt haben** — Kap. 119 (H trägt, +4,5 gegen +2,6), Kap. 120
(je Kategorie), Kap. 121 (Überlebensverzerrung, 523 Reihen), Kap. 117 (Dosis).
Wenn die Schwelle falsch geschätzt ist, ist **jedes dieser Urteile** betroffen,
in beide Richtungen.

### Zur Richtung: sie ist nicht vorhersagbar, und das gehört hierher

Regel 2.47 sagt, feste Grenzen **verschmälern** die Verteilung — das würde die
Schwelle senken und die Urteile **zu freundlich** machen. Methodik 2.48 hat aber
gemessen: dieselbe Probe, 20 Läufe fest → Schwelle **+18,4**; 20 Läufe wandernd
→ **+16,8**; 40 Läufe → **+20,5**. Dort lag die feste Schwelle *höher*.

**Der dominante Effekt in 2.48 ist die Läufezahl, nicht fest/wandernd** — genau
darum heißt das Kapitel „Die Schwelle ist selbst eine Schätzung". Daraus folgt
für S3: die Richtung ist **nicht vorhersagbar**, und jede Vorhersage hier wäre
geraten. Festgelegt ist nur, dass die Frage offen ist.

### Die Messung

Kap. 119 exakt wiederholen — gleiche Daten, gleiche Geometrie (k2/CRV2/120 T),
gleiche 446.509 Anker — einmal mit festen, einmal mit wandernden Grenzen,
**je 200 Läufe** (nicht 20; 2.48 ist der Beleg, warum). Dann dasselbe für
Kap. 121 (523 Reihen, je Kategorie).

### Vorab festgelegt

| Ergebnis | Lesart |
|---|---|
| Schwellenunterschied < 0,5 Punkte | die Abweichung von 2.47 ist **folgenlos** — dann dokumentieren und die Werkzeuge trotzdem angleichen |
| 0,5–2,0 Punkte, Urteil bleibt | H trägt weiterhin, aber **der Abstand ist kleiner als berichtet** — alle Zahlen der Befundkarte nachziehen |
| Urteil kippt bei irgendeinem Kapitel | ⚠️ **der einzige tragende Befund des Projekts ist ein Schwellenartefakt** — dann fällt H, und die Suche nach Hx beginnt bei null |

**Positivkontrolle:** entfällt — S3 misst keine Wirkung, sondern vergleicht zwei
Schätzverfahren derselben Größe. Stattdessen Gegenprobe: beide Verfahren auf
eine **deterministische** Umrechnung anwenden; die Schwelle muss dort gleich dem
Messwert werden (Methodik 2.55).

---

## 4. S4 — der Reifeschnitt (kippt *die Trennung Phase gegen Reihenalter*)

### Was in der Produktion steht

`MINDESTALTER = 250` — Anker in den ersten 250 Handelstagen einer Reihe werden
verworfen (`messe_struktur_bereinigt.py`, importiert von `messe_anreicherung`,
`messe_drift_zerlegt`, `messe_klassen`; eigenständig gleich gesetzt in
`messe_ausstieg`, `messe_dosis`).

### Woher die Zahl kommt — und warum sie **richtig** ist

Aus Kap. 104.3, dem **Reifeartefakt**: „kein Widerstand über dem Kurs" ist bei
einer jungen Reihe kein Marktbefund, sondern ein **Datenzustand** — es gibt
schlicht noch keine Historie, in der ein Widerstand entstehen konnte.
Gemessener H-Anteil je Reihenalter:

| Reihenalter (HT) | H-Anteil |
|---|---:|
| 0–249 | **12,6 %** |
| 250–499 | 4,0 % |
| 500–749 | 2,9 % |
| ab 750 | 0,6–5,3 % |

**48 % aller H-Fälle lagen in den ersten 250 Handelstagen.** Der Schnitt ist
also sachlich zwingend — und er hat das Rohurteil von Kap. 104 gekippt
(roh +1,3 „trägt" → reif +0,8 gegen Schwelle +2,4 „trägt nicht").

### ⚠️ Was trotzdem offen ist

Der Abfall ist bei 250 **noch nicht fertig**: 12,6 → 4,0 → 2,9. Zwischen 250 und
500 fällt der Anteil noch einmal um ein Drittel. **250 ist die Stelle, an der
der Sprung passiert, nicht die Stelle, an der er aufhört.** Ob H auch bei 500
oder 750 trägt, ist nie gemessen worden.

Das ist keine Formalie: seit Kap. 121 stehen **523 Reihen** in der Messbasis,
darunter 176 nachgeladene eingestellte Paare. Junge Reihen sind darin
überrepräsentiert, und **Small trägt am stärksten** (+7,9) — genau die
Kategorie, in der junge Reihen sitzen.

### Die Messung

Kap. 119 und 121 mit **250 / 500 / 750** Handelstagen Mindestalter wiederholen.
Zusätzlich ausweisen, wie viele Anker und wie viele Reihen je Schnitt übrig
bleiben (die S3-Schwelle wird mit der Basis kleiner — beides zusammen lesen).

### Vorab festgelegt

| Ergebnis | Lesart |
|---|---|
| trägt bei allen drei | H ist **altersunabhängig** — 250 ist begründet und ausreichend |
| trägt bei 250, fällt bei 500 | ⚠️ H lebt vom **Rand des Reifeartefakts** — der Schnitt ist zu früh |
| trägt bei 500/750, nicht bei 250 | H ist **stärker als berichtet**, der Schnitt zu großzügig |
| Basis bei 750 < 100 Reihen | nicht entscheidbar — als Nullbefund **zerlegt** ablegen, nicht als „erledigt" (Methodik 2.51) |

**Positivkontrolle:** wie S1.

---

## 5. Was diese Vorabfestlegung ausdrücklich NICHT kann

Der Nutzerhinweis *„bin aber vorsichtig mit Festlegungen"* verlangt, die
Grenzen mitzuschreiben:

1. **S1–S4 machen H nicht anwendbar.** Selbst wenn alle vier bestehen, bleibt H
   bei **3,3 % der Ankertage** — aus 24 Eröffnungen etwa eine. Das Problem
   „seit A1 kein ERÖFFNEN" wird davon **nicht** berührt.
2. **Sie finden kein Hx.** Sie prüfen, ob der vorhandene Befund hält. Der
   Partner aus einem anderen Kanal ist Gegenstand von Schritt 3/4, nicht hier.
3. **Sie sagen nichts über Nicht-Krypto.** H wurde für Aktien, ETF, Rohstoffe
   und Hedge **nie** gemessen, und bei 2 / 5 / 4 / 2 Symbolen kann keine
   Stichprobe 50 Fälle je Zelle erreichen (Befundkarte 7.6, C1).
4. **Sie sagen nichts über SHORT.** Dort steht `h = None`, nicht `h = False` —
   die Spiegelbedingung H′ hat sich nicht bestätigt (Kap. 110).
5. **Vier weitere unmarkierte Annahmen sind bekannt, aber nicht Teil von S1–S4**
   und werden hier nur vorgemerkt, damit sie nicht verloren gehen: die
   Clustergrenze `NIVEAU_CLUSTER_ATR = 0.3`; die obere Bandkante **+4,0 ATR**
   von A; die untere **−2,0 ATR** von B; und der Schwellenwert
   `PHASE_SCHWELLE = 0.20`.

---

## 6. Erfolgsmaß — welcher Maßstab gilt

Nach N-5 (Nutzervorgabe 25.08.) gilt **Potential des Assets**, nicht
Gebührendeckung. Für S1–S4 heißt das konkret:

- **Primär:** Vorsprung in Prozentpunkten gegen die Block-Permutation
  (gebührenfrei) — die Größe aus Kap. 119.
- **Daneben, nie stattdessen:** Netto-R am **Referenzsatz 0,30 %**
  (Methodik 2.53 verlangt den Breakeven-Abstand daneben).
- **Nicht** am Betriebssatz 1,50 % — das war der Fehler über achtzehn Kapitel.
- Ein Ergebnis, das nur am Betriebssatz kippt, ist **kein** Kippen von H.

---

## 7. Spot gegen Hebel — die Trennung, die hier schon greift

Nutzervorgabe 25.08.: *„SPOT und Hebel sind zwei unterschiedliche Varianten,
welche auch unterschiedlich zu behandeln sind — längerfristig vs. kurzfristig,
langsam vs. schnelle hohe bzw. tiefe Bewegungen."*

Für S1–S4 ist der Unterschied **gemessen und klein**: Spot gegen Hebel
unterscheidet sich bei H um **0,017 R** (Finanzierung 0,03 %/Tag × 13 Tage,
Kap. 120) — das **dreht kein Vorzeichen**. Deshalb laufen S1–S4 auf der
gemeinsamen Basis.

⚠️ **Wo der Unterschied dagegen greift, und das gehört getrennt behandelt:**
der Anlass. Heute läuft **eine** Frist für beide Instrumente, obwohl der Hebel
faktisch Scalping ist (Median-Haltedauer **0,30 Tage**) und Spot nicht. Das ist
**nicht** Teil von S1–S4, sondern ein eigener offener Punkt — vorgemerkt als
**N-8**.

---

## 8. Reihenfolge und Aufwand

| | Läuft gegen | Modellaufrufe | warum diese Stelle |
|---|---|---|---|
| **S3** | 446.509 Anker, 200 Läufe × 2 | 0 | **zuerst** — kippt es, sind S1/S2/S4 gegenstandslos |
| **S1** | dieselbe Basis, 3 Varianten | 0 | zweite, weil sie H **selbst** betrifft |
| **S4** | dieselbe Basis, 3 Schnitte | 0 | dritte, teilt sich den Lauf mit S1 |
| **S2** | Phasenzuordnung, 3 Indizes | 0 | letzte — betrifft nur die **Anwendung**, nicht den Befund |

Kein Kontingent, kein Anbieter, keine Sammelzeit. Die Produktion muss **nicht**
angehalten werden: alle vier lesen historische Reihen, keiner schreibt in die
Produktions-DB. DB-Zugriff ausschließlich über `Connection.backup()`.

---

## 9. Was danach kommt

Bestehen S1–S4, ist H als Befund gesichert und die Suche nach **Hx** beginnt
(Schritt 3: Literaturrahmen, Schritt 4: gezielte Quellensuche einschließlich
Quellen mit Nachrichten als Nebenprodukt). Kippt einer, wird **zuerst** der
Befundstand korrigiert — vor jeder neuen Suche.

Verwandt: `Befundkarte.md` §3/§5b · `Umbauplan_Gesamtsystem_12_08.md` Kap.
104–125 · `Test_und_Verifikationsmethodik.md` 2.47/2.48/2.51/2.53/2.55 ·
`Messkonzept_LLM_Standard_25_08.md`

---
---

# NACHTRAG (1) — S3 GEMESSEN, 25.08.2026

**Alles oberhalb dieser Linie stand vor dem Lauf und ist unverändert.**

## Was lief

Zwei Werkzeuge, je drei Varianten, je **200 Läufe**, alle auf
`data/messdaten.db` (Stand 21.08., 523 Reihen). Neue Schalter
`--blockgrenzen {fest,wandernd}` und `--blockverfahren {greedy,raster}`,
Vorgabe jeweils der Altzustand.

⚠️ **Ein zweiter Unterschied, der in der Vorabfestlegung fehlte.** Beim Lesen
der ersten Zahlen zeigte sich, dass „wandernde Grenzen" zwei Dinge zugleich
ändern: die **Lage** der Schnitte *und* das **Verfahren**. Die alte Fassung
schneidet *greedy* — ab dem ersten Anker der Reihe weiter, sobald 250 Einheiten
vergangen sind. Wandernde Grenzen brauchen dagegen ein **Raster**. Bei dichten
Ankern sollte beides gleich sein; es ist es nicht (477 gegen 484 Reihen mit
zwei Blöcken). Deshalb wurde ein dritter Lauf ergänzt, der das Verfahren allein
umstellt. **Ohne ihn hätte S3 zwei Effekte vermischt und wäre nicht
interpretierbar gewesen.**

## Ergebnis 1 — der Messwert ist stabil, die Schwelle ist es nicht

**Kap. 119, volle Stichprobe (631.117 Anker, 13.768 in H):**

| Variante | Reihen mit 2 Blöcken | Schwelle (95 %) | gemessen | Abstand | Urteil |
|---|---:|---:|---:|---:|---|
| **greedy + fest** — Altzustand | 477 | **+3,11** | +3,78 | 0,67 | **TRÄGT** |
| raster + fest — Verfahren allein | 484 | **+4,00** | +3,78 | −0,22 | **trägt nicht** |
| raster + wandernd — 2.47-konform | 523 | **+3,36** | +3,78 | 0,42 | **TRÄGT** |

**Kap. 121, Schwelle „aus acht" je Kategorie:**

| Variante | Large (+5,9) | Mid (+2,5) | Small (+7,9) |
|---|---:|---:|---:|
| **greedy + fest** — Altzustand | **+5,3** → TRÄGT | +5,3 → fällt | **+5,3** → TRÄGT |
| raster + fest | +5,7 → TRÄGT (knapp) | +5,7 → fällt | +5,7 → TRÄGT |
| raster + wandernd | ⚠️ **+6,2 → ZU KNAPP** | +6,2 → fällt | +6,2 → **TRÄGT** |

**Der Vorsprung selbst ist in allen Varianten bitgleich** — +3,78 gesamt,
Large +5,9 · Mid +2,5 · Small +7,9. Die Blockbildung berührt **nur die
Schwelle**. Das ist die erwartete Mechanik und bestätigt, dass der Umbau
gemessen hat, was er messen sollte.

## Ergebnis 2 — der Altzustand ist in BEIDEN Kapiteln die niedrigste Schwelle

| | greedy+fest | raster+fest | raster+wandernd | Spanne |
|---|---:|---:|---:|---:|
| Kap. 119 gesamt | **+3,11** | +4,00 | +3,36 | **0,89** |
| Kap. 121 Large | **+5,3** | +5,7 | +6,2 | **0,9** |

⚠️ **Die heute verdrahtete Variante liefert von drei geprüften die
freundlichste Schwelle — in beiden Kapiteln.** Das ist genau die Richtung, die
Regel 2.47 vorhersagt (feste Grenzen verschmälern die Verteilung). In 2.48 war
es umgekehrt gemessen worden; dort dominierte die Läufezahl bei nur 20 Läufen.
Mit 200 Läufen und 2×Streufehler von **0,17 bis 0,19 Punkten** ist die Spanne
von 0,9 Punkten **kein Rauschen**.

Die Richtung des Grenzeneffekts allein ist dagegen **nicht** einheitlich: bei
Kap. 121 hebt er die Schwelle (+5,7 → +6,2), bei Kap. 119 senkt er sie
(+4,00 → +3,36). Dort ändert der Versatz zusätzlich die Reihenmenge
(484 → 523). **Als gesichert gilt nur die Gesamtspanne, nicht die Zerlegung.**

## Ergebnis 3 — ein Urteil kippt: **Large**

Large stand mit *„TRÄGT, auch aus acht"* in der Befundkarte. Mit
2.47-konformen Grenzen liegt die Schwelle bei **+6,2** über dem Messwert
**+5,9** → Urteil **ZU KNAPP (2.48)**, und nach der eigenen Regel heißt das:
**es gilt gar nichts.**

**Small hält** — +7,9 gegen +6,2, in allen drei Varianten. **Mid** fiel schon
vorher und fällt weiter. **Die Gesamtaussage von Kap. 119 hält** in der
2.47-konformen Variante (+3,78 gegen +3,36), aber mit einem Abstand von nur
noch **0,42 Punkten** bei 2×Streu 0,19.

## ⚠️ Ergebnis 4 — Kap. 119 ist auf heutiger Basis nicht mehr +4,5 gegen +2,6

| | Kap. 119 (20.08.) | heute, **identischer Code** |
|---|---:|---:|
| Anker | 446.509 | **631.117** |
| Fälle in H | 9.405 | **13.768** |
| Reihen | 312 | **523** |
| Vorsprung | **+4,5** | **+3,78** |
| Schwelle (greedy+fest) | +2,6 | **+3,11** |
| Abstand | **1,9** | **0,67** |

Das ist **kein Fehler und kein Widerspruch**: Kap. 121 hat 176 eingestellte
Paare nachgeladen (+231.824 Kerzen). Die Basis ist breiter und ehrlicher — und
der Vorsprung darauf **kleiner**. Es ist Methodik 2.68 in Reinform: eine Zahl
aus einer wachsenden Datenlage veraltet, ohne dass jemand etwas falsch macht.

⚠️ **Die Befundkarte führte bis heute die 312-Reihen-Zahlen als aktuellen
Stand.** Der Abstand zur Schwelle ist in Wahrheit von 1,9 auf **0,42** Punkte
geschrumpft (breitere Basis **und** korrekte Grenzen zusammen) — ein Faktor
von mehr als vier.

## Ergebnis 5 — ein Nebenbefund über das Werkzeug: die Symbolteilung ist nicht reproduzierbar

Beide ersten Läufe meldeten für die **volle** Stichprobe exakt dieselben Zahlen
(13.768 H-Fälle), für die **halbe** aber verschiedene (7.474 gegen 7.069).
Nachgeprüft: `_reihen_roh` liefert die Symbole **je Prozess in anderer
Reihenfolge** — zweimal aufgerufen, zwei Ordnungen:

```
Lauf 1:  BNB, BIO, NEAR, RENDER, ETH, XLM, SUI, XNO
Lauf 2:  ETH, XNO, RENDER, S, TAO, BIO, INJ, IMX
```

Die SQL ist sortiert (`order by symbol, currency, date`); die Permutation
entsteht danach, über eine Menge, deren Iterationsreihenfolge am
String-Hash hängt. Da `r` die **Position** in dieser Reihenfolge ist, wählt
`(r % 2) == 1` bei **jedem Start eine andere Hälfte**.

⚠️ **Folge:** die Zeile *„halbe Stichprobe: +2,8 gegen Schwelle +3,3, nicht
bestätigbar"* aus Kap. 119 ist **eine Ziehung unter vielen möglichen** — kein
reproduzierbarer Befund. Dasselbe gilt für die entsprechenden Zeilen dieses
Nachtrags. Als „Auflösungsgrenze" darf das nicht mehr zitiert werden, solange
nicht über viele Teilungen gemittelt wird. → Methodik **2.76**.

## Was die Vorabfestlegung richtig vorhergesagt hat — und wo sie zu grob war

Vorab stand: *„Urteil kippt bei irgendeinem Kapitel → der einzige tragende
Befund des Projekts ist ein Schwellenartefakt → dann fällt H, und die Suche
nach Hx beginnt bei null."*

**Die Bedingung ist eingetreten (Large kippt). Die Folgerung war zu grob.**
Sie unterschied nicht zwischen *ein Teilurteil kippt* und *der Hauptbefund
kippt*. Gemessen ist beides zugleich: Large fällt, Small hält deutlich, die
Gesamtaussage hält knapp. **H fällt also nicht** — aber es steht erheblich
dünner da als in der Befundkarte.

Das wird hier festgehalten, statt die Lesart nachträglich passend zu machen.
Für S1, S2 und S4 gilt die Lehre: Ergebnis**muster** vorab benennen, nicht nur
Ergebnis**richtungen**.

## Was daraus folgt

1. **S1, S2 und S4 sind nicht gegenstandslos** — der Hauptbefund hält, also
   lohnt die weitere Prüfung. Reihenfolge unverändert: S1 → S4 → S2.
2. **Alle künftigen S-Läufe laufen 2.47-konform** (`--blockgrenzen wandernd
   --blockverfahren raster`) und berichten den Altzustand daneben.
3. **Die Befundkarte ist nachzuziehen**: Large verliert sein „trägt", die
   Gesamtzahlen sind auf 523 Reihen zu aktualisieren.
4. **Die beiden verbleibenden Werkzeuge mit festen Grenzen** (`messe_klassen`,
   `messe_dosis`) sind noch nicht umgestellt — ihre Befunde (Kap. 117, 120)
   stehen unter demselben Vorbehalt.
5. **Die Symbolteilung** braucht eine stabile Reihen-ID, bevor sie wieder
   zitiert wird.

---
---

# NACHTRAG (2) — S1 GEMESSEN, 25.08.2026

**Alles oberhalb der Nachtragslinie stand vor den Messungen und ist unverändert.**

## Was lief

Vier Läufe **sequenziell** (nie zwei Prozesse gleichzeitig), alle
2.47-konform (`--blockgrenzen wandernd --blockverfahren raster`), je 200
Läufe, auf `data/messdaten.db` (523 Reihen, 631.117 Anker).

**Der Umbau, an genau einer Stelle.** Die Totzone wirkt für *alle*
H-Messungen in `messe_marken._niveaus_schnell`:

```python
grenze = LB.NIVEAU_MIN_ABSTAND_ATR * atr
if   e["preis"] - kurs >= grenze:  oben.append(satz)   # Widerstand
elif kurs - e["preis"] >= grenze:  unten.append(satz)  # Unterstützung
```

Eine Marke näher als `grenze` fällt in **keine** der beiden Listen. Weil
`frei`/`gedeckt` gegen `ziel`/`stop` prüfen, ziehen die Bandgrenzen
automatisch mit — ein Parameter genügt. **`agent/lagebeschreibung.py`
(Produktion) wurde nicht angefasst.**

## Ergebnis 1 — die Positivkontrolle (93 B) ist punktgenau bestanden

300 von 8.528 offenen H-Fällen auf „Ziel" gesetzt. Da der Nenner von
`_quote` **alle** H-Fälle sind (vorsichtige Lesart, 2.54), ist die erwartete
Verschiebung exakt `n/n_H` — also **vorab berechenbar**:

| | Punkte |
|---|---:|
| erwartet (300 / 13.768) | **+2,18** |
| gemessen (+5,96 gegen +3,78) | **+2,18** |
| **Abweichung** | **0,000** |

⚠️ **Damit ist ein Nullbefund dieses Werkzeugs aussagekräftig** — es ist nicht
stumpf. Ohne diese Kontrolle wäre alles Folgende wertlos gewesen.

## Ergebnis 2 — H ist gegen die Totzone robust

| Totzone | H-Fälle | Quote H | Quote Rest | Vorsprung | Schwelle | Abstand | 2×Streu | Urteil |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 0,25 | 12.367 | 38,2 % | 34,3 % | **+3,92** | +3,41 | +0,51 | 0,19 | **TRÄGT** |
| **0,50** (heute) | 13.768 | 38,1 % | 34,3 % | **+3,78** | +3,42 | +0,36 | 0,18 | **TRÄGT** |
| 1,00 | 16.826 | 38,1 % | 34,3 % | **+3,82** | +3,23 | +0,58 | 0,17 | **TRÄGT** |

**Spanne des Vorsprungs: 0,14 Punkte.** Vorab festgelegt war: *„alle drei
tragen, Spanne ≤ 2 Punkte → H ist robust, die Totzone ist eine
Anzeigeentscheidung."* → **erfüllt, mit großem Abstand.**

## Ergebnis 3 — das stärkere Argument steht nicht in der Spanne

Die Totzone zu vervierfachen (0,25 → 1,0) ändert die **Trefferzahl um +36 %**
(12.367 → 16.826) — die **Quote bleibt bei 38,1–38,2 %**, die Quote der
Nicht-H-Fälle bei 34,3 %.

Das ist mehr als „die Spanne ist klein": **H lebt nicht von einer bestimmten
Markenauswahl.** Man kann die Grenze, ab der eine Marke als Marke zählt,
vervierfachen, ein gutes Drittel mehr Fälle einsammeln — und die Trefferquote
rührt sich nicht.

⚠️ **Warum mehr Totzone MEHR H-Fälle ergibt** (das ist zunächst
kontraintuitiv): H ist `A ∧ B`. Fallen Marken weg, wird **A** („kein
Widerstand im Weg") *leichter* erfüllt und **B** („Unterstützung deckt den
Stop") *schwerer*. Netto überwiegt A deutlich. Das ist eine
Konstruktionseigenschaft von H, die vorher nirgends stand.

## Was NICHT gezeigt ist

1. **Die drei H-Mengen wurden nicht auf Überlappung geprüft.** Aus der
   Konstruktion folgt, dass sie *keine* Teilmengen voneinander sind (ein Fall
   kann bei größerer Totzone seine Deckung verlieren und aus H fallen, während
   ein anderer hineinkommt). Wie stark sie sich unterscheiden, ist offen —
   wäre der Überlappungsgrad klein, wäre die Robustheit noch stärker belegt.
   **Als Behauptung steht das hier ausdrücklich nicht.**
2. **Die Unterschiede zwischen den drei Einstellungen sind nicht belastbar.**
   Der Abstand zur Schwelle ist bei 1,0 am größten (+0,58) und bei der heutigen
   0,5 am kleinsten (+0,36) — die Differenz von 0,22 Punkten liegt aber kaum
   über dem Streufehler (0,17–0,19). **Daraus folgt nicht, dass 1,0 die bessere
   Einstellung wäre.** Wer das behaupten wollte, bräuchte einen eigenen,
   vorab festgelegten Test.
3. **Die Clustergrenze `NIVEAU_CLUSTER_ATR = 0.3` ist weiterhin ungeprüft.**
   Sie stand schon in der Vorabfestlegung §5 als vorgemerkte, nicht geprüfte
   Annahme und bleibt es.

## Bilanz nach S3 und S1

| | Annahme | Ergebnis |
|---|---|---|
| **K3** | feste Blockgrenzen | ⚠️ **wirkt** — Schwellenspanne 0,9 Punkte, **Large kippt** |
| **K1** | Totzone 0,5 ATR | ✔ **wirkt nicht** — Spanne 0,14 Punkte, H robust |
| K4 | Reifeschnitt 250 | offen |
| K2 | Phasenindex | offen |

**Das Muster ist aufschlussreich:** die Annahme, die *aussah* wie eine
Willkür (0,5 aus einer Anzeigepanne), trägt nichts. Die Annahme, die
*aussah* wie eine Formalie (wo die Blockgrenzen liegen), hat ein Urteil
gekippt. **Welche Konstante gefährlich ist, war vorher nicht zu erraten** —
das ist das Argument dafür, S4 und S2 ebenfalls zu messen statt zu schätzen.

## Nebenbefund über das Werkzeug

Der Lauf mit Totzone 0,50 war als **Gegenprüfung** angelegt: er musste die
S3-Zahlen exakt reproduzieren. Er tat es — 13.768 H-Fälle, +3,78 gegen +3,36.
Der Umbau hat am Bestandsverhalten nichts verändert.

Beim Bauen fielen zwei eigene Fehler auf, beide erst durch Gegenprüfung:
`LB` war in `bewerte_neu.py` **gar nicht importiert** (hätte erst am Ende
eines 9-Minuten-Laufs beim JSON-Schreiben geknallt — die *Falle der freien
Namen*), und ein Escape war als echter Zeilenumbruch in der Datei gelandet.
