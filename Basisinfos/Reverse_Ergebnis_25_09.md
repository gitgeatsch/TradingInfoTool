# Reverse Engineering — Ergebnis und LAGE

**25.09.2026.** Befund **2.594-reverse-momentum-traegt-mit-richtung** ·
Vorabfestlegung 15 · Werkzeug `messe_reverse_scharfe_anstiege.py`

**116 Symbole · 3.237.922 Anker · 42.153 Stunden · 40 Nullziehungen · nur lesend**

---

# § 1 Was die Umkehrung der Fragestellung gebracht hat

| | bisher (Mittelwert) | jetzt (Fall-Kontrolle) |
|---|---|---|
| **Frage** | unterscheiden sich die Mittelwerte der Fünftel? | wie sah die **Lage vor den Ereignissen** aus? |
| **Prüfgröße** | Spanne q0−q4 | **Lift** = P(Ereignis \| oberstes Fünftel) / P(Ereignis) |
| **Nachweisgrenze** | 0,0102 bei Effekt 0,002–0,012 → **Effekt = Fehler** | Lift 1,9 gegen Nullband 0,99–1,02 |
| **Ergebnis** | ⛔ kein Beitrag trägt | ⭐ **zwei Beiträge mit Richtung** |

➤ **Ein Merkmal kann im Mittel nichts bewegen und trotzdem die Extreme
ordnen.** Das ist der ganze Unterschied — nicht die Datenlage.

---

# § 2 Die Häufigkeit — sie kommt vor der Bewertung

Ereignis: **Ziel erreicht, bevor ein 5-%-Stop fällt.**

| Ziel | H | Ereignisse | Anteil | Symbole | Urteil |
|---|---|---|---|---|---|
| +10 % | 3 h | 17.181 | **0,531 %** | 116 | ✔ |
| +15 % | 3 h | 6.030 | **0,186 %** | 114 | ✔ |
| **+20 %** | **3 h** | **2.833** | **0,087 %** | 109 | ⛔ **Anekdote** |
| +20 % | 6 h | 7.326 | 0,226 % | 111 | ✔ |

⚠️ **Die Nutzerbeobachtung trifft zu, ist aber selten:** „20 % in 3 Stunden"
gibt es 2.833 mal — nach der eigenen Vorabfestlegung zu wenig für ein
Geschäft. Gemessen wird deshalb auf +10 % und +15 %.

---

# § 3 ⭐ Die Spiegelprobe — sie war nötig

Dasselbe Ereignis **nach unten** (−Ziel bevor +5 %) trennt **Richtung** von
**Bewegung**. Bei **+15 % in 3 h**:

| Merkmal | Lift+ | Lift− | +/− | Stärke |
|---|---|---|---|---|
| `vola` | 3,317 | **1,679** | 1,975 | 3,317 |
| `momentum_kurz` | 3,082 | 1,255 | **2,456** | 3,082 |
| `rsi` | 2,711 | 1,216 | 2,229 | 2,711 |
| `oi_aenderung` | 2,249 | 1,325 | 1,697 | 2,249 |
| `volumenschub` | 2,154 | 1,249 | 1,725 | 2,154 |
| `funding` | 1,216 | **1,302** | 0,934 | ⚠️ nur Bewegung |
| `zufall` | 1,025 | 1,004 | 1,021 | ✔ im Nullband |

⚠️ **`vola` hat den höchsten Lift — und nach unten 1,679.** Ohne die
Gegenprobe hätte ich Volatilität als Bewertung ausgegeben.

⭐ **Und `funding` hat damit seine Antwort:** es erzeugt **Bewegung in beide
Richtungen, keine Richtung** (1,216 gegen 1,302). Das erklärt, warum es auf
`barriere` nie trug — und es widerspricht dem Spot-Beitrag auf
`bewegung_r`/H20 **nicht**, weil das eine andere Frage ist.

---

# § 4 ⭐⭐⭐ Die Dosis-Wirkung — das entscheidende Argument

Rang je **Stunde × Vola-Band**. Mehr Bänder = strenger. Ein Vola-Artefakt
**muss** gegen Lift 1 zerfallen, ein eigener Beitrag nicht.

## 4.1 Ziel +10 % in 3 h

| Merkmal | 1 Bd (100 %) | 3 Bd (75 %) | 5 Bd (66 %) | 8 Bd (58 %) | Urteil |
|---|---|---|---|---|---|
| `momentum_kurz` | 2,820 | 2,553 | 2,462 | **2,442** | ⭐ eigener Beitrag |
| `rsi` | 2,458 | 2,322 | 2,283 | **2,321** | ⭐ eigener Beitrag |
| `volumenschub` | 1,945 | 1,924 | 1,970 | **2,018** | ⭐ eigener Beitrag |
| `oi_aenderung` | 1,988 | 1,893 | 1,894 | 1,920 | hält, **nur Bewegung** |
| `top_konten_verh` | 0,527 | 0,595 | 0,637 | 0,723 | ⚠️ **zerfällt** 1,90→1,38 |
| `konten_verh` | 0,578 | 0,633 | 0,678 | 0,770 | ⚠️ **zerfällt** 1,73→1,30 |
| `taker_verh` · `funding` | | | | | ⚠️ zerfallen |
| `zufall` | 1,021 | 1,009 ✔ | 1,021 | 1,073 | ⚠️ **siehe 4.2** |

⛔ **Die drei inversen Konten-Merkmale fallen.** Im Teillauf (25 Symbole, 8
Ziehungen) standen sie als eigene Beiträge da — mit voller Ladung zerfallen
sie. **Dritte Ladungsabhängigkeit des Tages**, diesmal vor dem Befund
gefangen.

## 4.2 ⚠️ Diese Zelle ist nicht voll auswertbar

`zufall` liegt bei **1, 5 und 8 Bändern außerhalb** des Nullbands — ein
Fehlalarm dort, wo die Zellen dünn werden. Nach der eigenen Regel gilt die
Zelle damit nur eingeschränkt.

## 4.3 ✔ Ziel +10 % in 6 h — hier ist die Kontrolle sauber

`zufall` in **allen vier** Stufen im Nullband (0,996 / 0,989 / 0,998 / 1,022).

| Merkmal | 1 Bd | 8 Bd | Richtung (+/−) | Urteil |
|---|---|---|---|---|
| **`momentum_kurz`** | 2,335 | **1,937** | 1,616 | ⭐ eigener Beitrag |
| **`rsi`** | 2,049 | **1,893** | 1,512 | ⭐ eigener Beitrag |
| `volumenschub` | 1,579 | 1,608 | — | ⚠️ nur Bewegung |
| `oi_aenderung` | 1,654 | 1,542 | — | ⚠️ nur Bewegung |

➤ **In der Zelle mit sauberer Kontrolle bleiben genau zwei Merkmale.**

---

# § 5 ⚠️ Die drei Einschränkungen — sie gehören zum Befund

| # | |
|---|---|
| **1** | **`momentum_kurz` und `rsi` sind beide Preis-Momentum** und hoch korreliert. Wahrscheinlich **ein** Befund, nicht zwei. **Redundanz ungeprüft** |
| **2** | Es war ein **erwarteter** Treffer (Vorabfestlegung § 6: *„wenn irgendetwas trägt, dann das"*). Erwartete Treffer sind die schwächere Art Fund |
| **3** | ⚠️⚠️ **Der Lift ist keine Hebelhöhe.** Gemessen ist, wie oft das **Ziel vor** dem Stop fällt — **nicht**, wie oft der **Stop vor** dem Ziel fällt. Für Kelly braucht es beide, sonst gibt es kein `q` |

---

# § 6 ✔ Die vier Gegenprüfungen

| | |
|---|---|
| **Nullwelt** | die exakte hypergeometrische gegen 40 Permutationen: Abweichung **0,0012–0,0079** im 90. Perzentil → dieselbe Nullwelt, nur ohne Sortierung rechenbar |
| **Riegel** | Zielgröße nachweislich binär (gegen Befund 2.590) |
| **Kontrolle** | Nachweis, dass sie greift — Vola-Reststreuung **100 / 75 / 66 / 58 %** je Stufe |
| **`zufall`** | in jeder Tabelle, und er hat eine Zelle als unauswertbar entlarvt |

## 6.1 ⚠️ Drei eigene Fehler, von diesen Prüfungen gefunden

| Fehler | Wirkung |
|---|---|
| Nullpunkt **einseitig** geprüft | drei inverse Beiträge (Lift 0,53 = Stärke 1,89) galten als „Rauschen" |
| Kontrollprobe **gepoolt** gerechnet | meldete falsch, die Kontrolle greife kaum (84 % statt 75 %) |
| Vola-**Fünftel** statt Terzile | Zellen zu dünn, alles „zu dünn" |

---

# § 7 Was jetzt zu sondieren ist — nicht zu messen

⚠️ **Nutzervorgabe:** *„nach der Messung müssen wir die Lage sondieren und
langsam bewerten."* Deshalb hier nur die offenen Punkte, ohne Vorschlag:

| # | offener Punkt |
|---|---|
| **A** | **Redundanz** `momentum_kurz` gegen `rsi` — ein Befund oder zwei? |
| **B** | **Das Gegenstück**: P(Stop vor Ziel). Ohne es kein `q`, ohne `q` keine Hebelhöhe |
| **C** | Warum ist die Kontrolle in der 3-h-Zelle unsauber, in der 6-h-Zelle nicht? |
| **D** | Ist das Ereignis **handelbar**? Liquidität, Slippage, Ausführung — ungemessen |
| **E** | Die **Geometrie** bleibt zurückgestellt (Nutzerentscheidung), samt der offenen Frage nach dem echten Betriebsstop |
| **F** | Beide Hälften der Historie (B6) für den Lift — **ungemessen** |
