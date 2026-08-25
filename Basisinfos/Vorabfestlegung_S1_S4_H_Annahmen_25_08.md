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
