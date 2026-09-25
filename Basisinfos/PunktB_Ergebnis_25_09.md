# Punkt B — `q` aus beiden Seiten: Ergebnis

**25.09.2026.** Befund **2.595-lage-traegt-richtung-aber-kein-hebel** ·
Vorabfestlegung 16 · Werkzeug `messe_q_beide_seiten.py`

**116 Symbole · 3.239.314 Anker (voll) / 2.868.929 (ab 2023) · nur lesend**

---

# § 1 Das Ergebnis in zwei Sätzen

> ✔ **Die Lage sagt sehr wohl, WOHIN es geht** — `q` steigt von 0,1379 auf
> **0,2405**, Faktor 30 über dem Nullband. **H0 ist widerlegt.**
>
> ⛔ **Und sie reicht trotzdem nicht für einen Hebel** — `q4` bleibt weit unter
> der Kelly-Nullstelle 0,3333, und `E[R]` wird im obersten Fünftel
> **schlechter**.

---

# § 2 Die Zahlen — `momentum_kurz`, H6, Fenster voll

| Fünftel | 0 | 1 | 2 | 3 | **4** |
|---|---|---|---|---|---|
| **ZIEL %** | 1,238 | 0,733 | 0,757 | 0,989 | **3,227** |
| **STOP %** | 7,735 | 5,924 | 5,691 | 5,865 | **10,191** |
| Auflösung % | 8,973 | 6,657 | 6,448 | 6,854 | 13,418 |
| **q** | 0,1379 | 0,1101 | 0,1174 | 0,1443 | **0,2405** |
| **E[R]** | −0,0056 | −0,0017 | −0,0020 | −0,0033 | **−0,0091** |

| | |
|---|---|
| Spanne `q` | **+0,1026** gegen Nullband **0,0034** → Faktor **30** |
| Spanne `E[R]` | **−0,0035** gegen Nullband 0,0017 → trennt, aber **nach unten** |
| `q_alle` · `E[R]_alle` | 0,1634 · **−0,0043** |

## 2.1 ⭐ Die Arithmetik, warum es nicht reicht

**ZIEL steigt um Faktor 2,6** (1,238 → 3,227 %) — das reproduziert den Lift
2,34 aus 2.594 ✔. **Aber STOP steigt mit**, 7,735 → 10,191 %. Und der Stop
kostet **eine** Einheit, das Ziel bringt **zwei**:

```
3,227 × 2  −  10,191 × 1  =  −3,74 Prozentpunkte R
```

Für `q = 1/3` müsste ZIEL bei **5,10 %** liegen statt 3,23 %.
➤ **Es fehlen 58 % mehr Zieltreffer.**

---

# § 3 In allen sechs Zellen dasselbe Bild

| Fenster | H | q4 | E[R] Fünftel 0 → 4 | Spanne E[R] |
|---|---|---|---|---|
| voll | 3 | 0,2405 | −0,0016 → −0,0049 | −0,0034 |
| voll | 6 | 0,2405 | −0,0056 → −0,0091 | −0,0035 |
| voll | 12 | 0,2444 | −0,0127 → −0,0172 | −0,0045 |
| **ab 2023** | 3 | 0,2465 | −0,0004 → −0,0036 | −0,0032 |
| **ab 2023** | 6 | 0,2470 | −0,0037 → −0,0069 | −0,0032 |
| **ab 2023** | 12 | 0,2497 | −0,0100 → −0,0138 | −0,0038 |

✔ **Zur Nutzerfrage nach 2023: kein Regimebruch.** Dort ist es sogar minimal
**besser** (q4 höher, `E[R]` weniger negativ). Die vermutete
Marktveränderung wirkt hier nicht.

⚠️ **`rsi` wechselt auf `E[R]` das Vorzeichen** über die Zellen (−0,0029 bis
+0,0027) — dort nicht verlässlich. **`vola`** ist mit Spanne −0,0102 die
**schlechteste** Lage von allen: Volatilität kostet.

---

# § 4 ⭐ Die konstruktive Folge — gemessen, nicht geraten

Bei `q = 0,2405` rechnet sich ein Trade erst ab

```
CRV > (1 − q) / q = 3,16        statt der jetzigen 2,0
```

➤ **Damit ist die Geometrie doch der Hebel — aber jetzt mit einer Zahl statt
einer Vermutung.**

⚠️ **Der Zielkonflikt ist messbar und nicht trivial:** ein weiteres Ziel senkt
`q` (es ist schwerer zu erreichen). Ob es ein CRV gibt, bei dem `E[R]` im
obersten Fünftel **positiv** wird, ist offen — und `E[R]` ist genau die Größe,
die man darüber maximieren kann.

⚠️ Und der Rahmen: `E[R]_alle` ist in **allen** Zellen negativ (−0,0012 bis
−0,0096). Das deckt sich mit dem registrierten Befund, dass ein
Barrierensystem den Erwartungswert null hat — mit Auswahl also leicht
darunter.

---

# § 5 ✔✔✔ Test und Simulation — wie beauftragt

**Selbsttest gegen bekannte Wahrheit:** 300 Nullwelten, 20 Effektwelten je
Stärke, auf den **echten** Ausgängen.

| | |
|---|---|
| **Fehlalarm** | `q` **7,0 %** · `E[R]` **8,3 %** |
| **erwartet** | **10,0 %** — das Band *ist* das 90. Perzentil, also liegen per Konstruktion 10 % darüber |
| **obere 95-%-Schranke** | 12,8 % → ✔ geeicht, sogar etwas übervorsichtig |
| **Rückgewinnung** | gepflanzt 0,0100 / 0,0200 / 0,0400 / 0,1000 / 0,2000 → gemessen **0,0092 / 0,0203 / 0,0418 / 0,0983 / 0,2004** — **kein systematischer Versatz** |
| **Auflösung** | auf `q` ab Stärke **0,0100**; `E[R]` ist gröber |

## 5.1 ⚠️⚠️ Drei eigene Konstruktionsfehler, die der Selbsttest gefunden hat

| Fehler | Wirkung | Korrektur |
|---|---|---|
| Simulationswelten zogen die Ausgänge **neu** → **keine Tageskopplung** | Nullwelten streuten zu wenig, Fehlalarm **15 %** | die **echten** Ausgänge bleiben; gepflanzt wird nur durch **Umdrehen** der Richtung |
| Pflanzen zwang `q` auf einen **exakten** Zielwert | Nullwelt verlor jede Stichprobenstreuung (Band **0,00003**), die Eichung war bedeutungslos | **relativer** Versatz auf das beobachtete `q` |
| Sollwert **5 %** bei einem 90.-Perzentil-Band | **arithmetisch unerreichbar** | Sollwert aus der Binomialverteilung hergeleitet, 300 statt 100 Welten |

⚠️ **Ein Selbsttest prüft die Anlage, nicht die Daten.**

## 5.2 Ein Grenzfall, benannt

Bei **H12** liegt `zufall` auf `q` knapp außerhalb des sehr engen Bandes
(+0,0031 gegen 0,0018). Die echten Effekte sind dort +0,07, also Faktor 20 —
am Urteil ändert es nichts, aber es gehört gesagt.

---

# § 6 Welche Standards hier galten — und welche nicht

**Nutzervorgabe:** *„NUR jene Messstandards berücksichtigen die auch
Gültigkeit haben."* Vollständig in Vorabfestlegung 16 § 3. Kurz:

| | |
|---|---|
| **gilt** | Bezug = Nullpunkt · 40 Ziehungen, 90. Perzentil · `zufall` · B6 · Positivkontrolle · Trennschärfe als Prinzip |
| **angepasst** | gepflanzte Stärken **in q statt R** · **Stunden**klammer · Nullwelt direkt gezogen statt permutiert |
| **gilt nicht** | `HORIZONT_JE_LAGE` = 3 **Tage** · Produktionsgeometrie · **F-212 selektierte Menge** |
| ➤ **Frageart** | **`markt`**, Menge messuniversum |

⚠️ **F-212 trägt hier nicht**, weil es keine **stündliche** Kette gibt — also
keine Trichterstufe 12, auf die hin selektiert würde. Und die vorhandene
Auswahl rangt nach **250 Handelstagen**, was für einen 6-Stunden-Trade die
falsche Dimension ist (offen als **P-1**).

⚠️ **Folge:** in **2.594** stand „Hebel-Beitrag" — **richtiggestellt** zu
*Ordenbarkeit der Lage*, Frageart `markt`.

---

# § 7 Was jetzt offen ist

| # | |
|---|---|
| ⭐ **B'** | **`E[R]` über CRV** — gibt es ein Ziel/Stop-Verhältnis, bei dem die beste Lage positiv wird? Die erste Frage mit einer gemessenen Zahl davor (3,16) |
| **A** | Redundanz `momentum_kurz` × `rsi` — durch 2.595 entwertet, weil `rsi` auf `E[R]` ohnehin nicht trägt |
| **C** | Kontrolle bei 3 h unsauber (aus 2.594) |
| **D** | Handelbarkeit — Liquidität, Slippage, Ausführung |
| **F** | Geometrie und echter Betriebsstop |
| ⛔ **Short** | Planpunkt, **ruht** — tritt erst ein, wenn Long trägt |
