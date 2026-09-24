# Vorabfestlegung 12 — P-9 Schicht 3: ist die Basisrate VORHERSAGBAR?

**24.09.2026, geschrieben VOR der Messung.**
Nutzerauftrag: *„dann Schicht 3 zu Ende messen"*

---

# § 1 Was gemessen ist — und was daran noch fehlt

**Befund 2.584 (heute):** die Barrieren-Trefferquote schwankt je Jahr
zwischen **26,4 %** und **42,6 %**; 2025 und 2026 liegen **unter** der
Kelly-Nullstelle von 33,3 %.

⚠️⚠️ **Das allein ist nutzlos.** Eine Größe, die schwankt, aber nicht
**vorher** bekannt ist, kann man nicht verwenden — man weiß erst
hinterher, dass 2025 schlecht war.

> **Die Frage ist deshalb nicht „schwankt sie?" — das ist beantwortet —
> sondern: IST DIE SCHWANKUNG AUS ZUM ZEITPUNKT BEKANNTEN GRÖSSEN
> VORHERSAGBAR?**

| | |
|---|---|
| **vorhersagbar** | die Basisrate kann zustandsabhängig gerechnet werden, und `q` bekommt ein tragfähiges Fundament |
| ⛔ **nicht vorhersagbar** | dann bleibt sie eine **Warnung**, kein Baustein — und der Hebel steht auf einer Größe, die niemand kennen kann |

---

# § 2 ⚠️ Die erste Falle: ist die Schwankung überhaupt echt?

Die Jahreszahlen stammen aus **überlappenden** 60-Tage-Fenstern. 128.819
Anker in 2025 sind **nicht** 128.819 unabhängige Fälle.

➤ **Vor jeder Vorhersagefrage wird die Schwankung gegen den Zufall
gestellt:**

| | |
|---|---|
| **Blockbildung** | nicht überlappende Fenster von **60 Tagen** — ein Anker und sein Vorwärtsfenster liegen dann ganz in einem Block |
| **erwartete Blockzahl** | rund **48** über 2018–2026 |
| **Nullhypothese** | die Quote je Block streut nur binomial um einen festen Wert |
| **Prüfgröße** | Streuung der Blockquoten **gegen** die binomial erwartete |

⛔ **Übersteigt sie die binomiale Erwartung nicht, ist Schicht 3 ein
Artefakt der Überlappung und der Befund 2.584 zu entschärfen.**

⚠️ Dann fällt auch die Vorhersagefrage weg — man sagt nichts vorher, was
nur Rauschen ist.

---

# § 3 Die Kandidaten — jeder mit Hypothese, keiner blind

**Alle werden aus Größen gebildet, die am Ankertag BEKANNT sind.**

| # | Kandidat | Hypothese | Richtung |
|---|---|---|---|
| **V1** | ⭐ die **Quote des Vorblocks** | Persistenz — Regime halten an | **positiv** |
| **V2** | realisierte **Marktvolatilität** (BTC, 60 Tage) | hohe Vola → beide Barrieren öfter erreicht; der Stop liegt näher, also **schadet** sie | **negativ** |
| **V3** | **BTC-Trend** über 60 Tage | in Aufwärtsphasen wird das Ziel öfter zuerst getroffen | **positiv** |
| **V4** | **Streuung über die Symbole** im Vorblock | laufen die Werte auseinander, gibt es mehr Gewinner | offen |
| **KON** | `zufall` | **Kontrolle** — muss null ergeben | null |

⚠️ **V1 ist der wichtigste und der billigste.** Trägt er, ist die Lösung
einfach: die Basisrate folgt der zuletzt gemessenen. Trägt er nicht, ist
das schon fast die Antwort auf die ganze Frage.

## 3.1 ⚠️ Der Suchpreis

**4 Kandidaten**, rund **48** Blöcke. Das ist **wenig**.

⚠️⚠️ **KORRIGIERT am 24.09., noch vor dem Urteil.** Die erste Fassung nannte
**r = 0,30** und rechnete sie aus allen 48 Paaren. Das ist falsch: geprüft
wird **out-of-sample**, und dort sind es nur **24**.

| Menge | n | Standardfehler | 5 % | **mit Bonferroni(4)** |
|---|---|---|---|---|
| alle Paare | 48 | ±0,149 | 0,292 | 0,373 |
| ⭐ **out-of-sample** | **24** | **±0,218** | 0,428 | ⭐ **0,546** |

➤ **Es gilt 0,546.** Der Fehler hätte V4 (r_oos = 0,305) als „trägt"
ausgewiesen — genau die Sorte Befund, die dieses Projekt schon zweimal
zurücknehmen musste.

⚠️ **Zweite Bedingung: STABILITÄT.** Ist `r_oos` ein Vielfaches von
`r_gesamt`, muss die erste Hälfte gegenläufig sein — das ist Instabilität,
kein Effekt. Grenze: **Faktor 2**.

---

# § 4 Die Norm

| | |
|---|---|
| **Frageart** | `zaehlung` für § 2, `beitrag` für § 3 |
| **out-of-sample** | ⭐ **Pflicht** — die Vorhersage wird auf der **zweiten** Hälfte geprüft, die Beziehung auf der ersten geschätzt |
| **Negativkontrolle** | `zufall` |
| **Beide Hälften** | B6 |
| **Abgrenzung** | nur Krypto |
| **Zielgröße** | die **Barrieren-Trefferquote** je Block, CRV 2,0 — dieselbe Größe wie in 2.584 |

⚠️ **Kein Bootstrap über Anker.** Die Einheit ist der **Block**, und davon
gibt es 48. Wer über 644.336 Anker bootstrappt, misst eine Sicherheit, die
es nicht gibt — derselbe Fehler wie „32 Symbole an 733 Tagen sind keine
23.000 Fälle".

---

# § 5 ⭐ Die Entscheidungsregel — VOR der Messung

| Ergebnis | Entscheidung |
|---|---|
| ⛔ **§ 2 fällt** (Streuung nicht über binomial) | **2.584 wird entschärft** — die Schwankung ist Überlappungsartefakt. Schicht 3 entfällt |
| ✔ **V1 trägt** out-of-sample, Kontrolle sauber | **Die Basisrate wird nachgeführt** statt fest gerechnet. Bauform danach, nicht jetzt |
| ✔ **V2/V3/V4 trägt**, V1 nicht | Hinweis auf einen **Zustand**, nicht auf Persistenz — eigene Vorabfestlegung nötig |
| ⚠️ **Nur in-sample, nicht out-of-sample** | ⛔ **kein Befund** — das ist die klassische Überanpassung |
| ⛔ **Keiner trägt**, Streuung ist echt | ➤ **§ 6** |
| ⛔ **Kontrolle trägt** | Lauf ungültig |

⚠️⚠️ **Wird nicht nachverhandelt.**

---

# § 6 ⭐⭐ Wenn nichts trägt — was DANN gilt

**Das ist der wahrscheinlichste Ausgang** (§ 7), und er wird hier vorab
festgelegt, damit er später nicht als Enttäuschung umgedeutet wird.

> **Eine Basisrate, die echt schwankt und nicht vorhersagbar ist, darf
> nicht als Konstante verwendet werden, die so tut, als wäre sie bekannt.**

| | |
|---|---|
| ⛔ **Was NICHT folgt** | den Festwert 0,3333 durch einen anderen Festwert zu ersetzen. Der Mittelwert 34,4 % wäre in 2025 genauso falsch — nur anders |
| ✔ **Was folgt** | die **Unsicherheit** gehört in die Rechnung. Ein `q` mit unbekanntem Fundament rechtfertigt einen **kleineren** Hebel, nicht denselben |
| ⚠️ **Und das ist eine ENTWURFSFRAGE** | keine Messung. Sie wird dem Nutzer **vorgelegt**, nicht entschieden |

⚠️ **Der Zusammenhang mit P-22:** Hebelstufen gegen eine Bewertung zu
kalibrieren, deren Fundament um 16 Punkte wandert, kalibriert gegen einen
beweglichen Nullpunkt — derselbe Fehlertyp wie *„ein Maximum ist kein
Nullpunkt"* (08.09.).

---

# § 7 Die Vorhersage, vor dem Lauf

**Erwartung: § 2 hält (die Schwankung ist echt), aber V1 trägt nicht.**

**Begründung:** 16 Prozentpunkte Spanne sind für reines Binomialrauschen
bei mehreren tausend Ankern je Block zu viel. Persistenz über 60-Tage-Blöcke
hinweg wäre dagegen eine Form von Vorhersagbarkeit, die dieses Projekt in
acht Messungen über 8.441 Fälle **nie** gefunden hat (10.08.: *kein
Verfahren schlägt die Basisrate*).

**Gegenthese:** V2 (Marktvolatilität) trägt, weil sie die Geometrie direkt
berührt — bei hoher Vola wird der nähere Stop überproportional zuerst
getroffen. Das ist **kein** Markturteil, sondern Mechanik, und genau deshalb
der plausibelste der vier.

---

# § 8 Was diese Messung **nicht** entscheidet

- **Nicht** die Bauform einer zustandsabhängigen Basisrate (§ 6).
- **Nicht** P-1, P-22 oder die Kette.
- **Nicht** den offenen Widerspruch 34,4 % gegen 31,3 % (Potentialfilter) —
  eigener Punkt.
- **Nicht** M1.
