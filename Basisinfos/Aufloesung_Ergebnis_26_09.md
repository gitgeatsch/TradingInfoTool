# Hält die Bewertung eine gröbere Auflösung? — ja, mit Verlust

**26.09.2026** · Befunde 2.616, 2.617 · `messe_aufloesung_und_fallback.py`
· Vorabfestlegung 21

> **Nutzerauftrag:** *„ja messen - prüfen und gegenprüfen - wir benötigen
> auch eine fallback lösung wenn eine Bewertung nicht oder nur zum Teil
> gedeckt ist."*

---

## Das Ergebnis

**3.181.434 Anker · 1.746 Tage · 116 Symbole**, gleicher Auswahlanteil
über alle Stufen, Maßstab **Kursprozent** (der einzige, der nicht von der
ATR abhängt):

| Stufe | ATR-Quelle | Kurs % | Verlust zu A | Rangkorr. | Überlappung | |
|---|---|---|---|---|---|---|
| **A** | 1-h-OHLC *(Binance, heute)* | **+0,6611** | — | — | — | ✔ |
| **B** | 4-h-OHLC *(= CoinGecko)* | **+0,4452** | **−33 %** | **0,9976** | 69,4 % | ✔ |
| **C** | Tages-OHLC | +0,3357 | −49 % | 0,9851 | 43,7 % | ✔ |
| **D** | ⭐ **nur Schlusskurse, kein High/Low** | **+0,4296** | **−35 %** | 0,9965 | 66,9 % | ✔ |

**Alle vier liegen über dem Nullband.** Die Auflösung kostet, sie
zerstört die Bewertung aber nicht.

⭐⭐ **Der entscheidende Fund für den Fallback: Stufe D ist so gut wie B.**
Eine ATR-Ersatzgröße **ganz ohne High und Low** — gerechnet aus der
mittleren absoluten Stundenrendite × √24 — verliert 35 %, das grobe OHLC
33 %. **CoinGecko liefert die Preisreihe für 15 von 15** (2.613). Die
Lücke ist damit schließbar, **ohne** auf 4-Stunden-OHLC angewiesen zu sein.

⚠️ Der √24-Faktor ist **nicht angepasst**, sondern hergeleitet (Irrfahrt).
Ein auf das Ergebnis kalibrierter Faktor wäre genau das, was die Messung
prüfen soll.

---

## Die zwei Fallen, die die Konstruktion bestimmt haben

### ⚠️ Falle 1 — `R` steht **in** ATR

`R = (Ausstieg − Einstieg) / (Weite × ATR)`. Ändert sich die ATR, ändert
sich der **Nenner**. Ein gleiches `E[R]` wäre dann kein Beleg für
Gleichheit, sondern nur andere Skalierung — der Fehler aus 2.607.

➤ Deshalb entscheidet **nur der Kursprozent-Arm**. `E[R]` steht daneben,
weil es die **Hebel**frage beantwortet.

### ⚠️⚠️ Falle 2 — ein Skalenfehler, im Probelauf gefunden

`atr_tag_relativ` rechnet die mittlere **Stunden**spanne **× √24** auf
Tagesmaß hoch. Meine groben Stufen taten das zunächst nicht:

| | Rechnung | Faktor |
|---|---|---|
| A | 1-h-Spanne × √24 | 4,90 |
| B *(falsch)* | 4-h-Spanne, **ohne Faktor** | ≈ 2,0 |

2,0 / 4,90 = 0,41 — genau die gemessenen **0,42×**. Folge: dieselbe
Schwelle 1,0 erzeugte **0,90 gegen 18,38 Signale je Tag**. Ich hätte die
**Härte der Auswahl** verglichen statt der **Ordnung**.

✔ **Behoben zweifach:** der Faktor `√(24/takt)` ergänzt (ATR-Median jetzt
A 1,00× / B 1,02× / C 1,05×), **und** der Vergleich läuft über den
**gleichen Auswahlanteil** statt über dieselbe Schwelle.

---

## Die Gegenprüfungen

| # | Prüfung | Ergebnis |
|---|---|---|
| **P1** | Grenzfall `takt=1` bitgleich mit `atr_tag_relativ` | ✔ **JA** |
| **P2** | Nullwelt je Stufe, 40 Ziehungen | ✔ alle vier über Band |
| **P3** | Ankermenge in **allen** Stufen identisch | ✔ 3.181.434 |
| **P5** | Rangkorrelation zu A | ✔ 0,985–0,998 |

⚠️ **P4 (gepaarter Tagesvergleich) meldete für alle drei Stufen einen
Unterschied** — aber auf der **Tagesklammer**, und die beantwortet eine
andere Frage (siehe unten).

### Falle 2 aufgelöst: es ist die **Auswahl**, nicht der Stop

| | `E[R]` |
|---|---|
| Auswahl A + Stop A | +0,1212 |
| Auswahl A + Stop B | +0,1238 |

➤ Differenz **+0,0026** — die Stopweite allein ändert fast nichts. Der
Unterschied zwischen den Stufen entsteht daran, **wer ausgewählt wird**.

---

## ⛔ Ein eigener Fehler, der fast als Befund durchgegangen wäre

Ich hatte gemeldet: *„das kippt 2.608 — in jeder Schicht ist die Bewertung
schlechter als der Tagesdurchschnitt"*:

| Signale/Tag | ALLE % | Signal % | Differenz |
|---|---|---|---|
| 1 | −0,34 | −4,34 | −4,00 |
| 26–100 | +1,25 | +0,99 | −0,26 |

⚠️⚠️ **Das war methodisch falsch.** *„Anzahl Signale am Tag"* ist **keine
Vorbedingung, sondern eine Folge der Auswahl** — ein **Kollider**. Darauf
zu konditionieren erzeugt Scheinzusammenhänge. Ein Tag mit einem einzigen
Signal ist ein Tag, an dem ein Asset steigt, während alles fällt — eine
strukturell andere Lage, keine Stichprobe derselben.

### ✔ Die richtige Schichtung: nach ATR (einer **Vor**bedingung)

| ATR-Fünftel | ALLE % | Signal % | `E[R]` | |
|---|---|---|---|---|
| 1 *(niedrig)* | +0,0944 | **+0,4632** | +0,1313 | ✔ trägt |
| 2 | +0,0715 | **+1,3089** | +0,2464 | ✔ trägt |
| 3 | −0,0886 | **+1,1646** | +0,1758 | ✔ trägt |
| 4 | −0,2652 | **+0,7882** | +0,0961 | ✔ trägt |
| 5 *(hoch)* | −0,0867 | −0,1703 | −0,0008 | ⛔ unter Band |

➤ **4 von 5 Fünfteln tragen**, mittlere Differenz **+0,7658
Prozentpunkte** zugunsten der Bewertung. Die ATR-Auswahl ist zudem kaum
verzerrt (Median 1,05× gegenüber allen Ankern).

⚠️ **Im höchsten ATR-Fünftel trägt sie nicht** — das ist offen und
gehört gemessen, nicht wegerklärt.

---

## ⭐⭐⭐ Die Gewichtungsfrage — und warum sie nicht meine ist

Dieselben 20.272 Signale:

| | Kurs % | `E[R]` |
|---|---|---|
| **gepoolt** (je Anker) | **+0,6611** | **+0,1212** |
| **Tagesklammer** (je Tag) | **−1,5913** | **−0,1570** |

**Das Vorzeichen dreht.** Signale je Tag: Median 7, Mittel 18,2, Maximum
620; an 1.112 von 1.746 Tagen gibt es überhaupt eines.

> **Nutzereinordnung 26.09.:** *„Eine Signal ist keine Position und die
> Entscheidung zur Kapitalallokation ist meine. Es ist klar dass an sehr
> guten Tagen auch mehr Signale kommen und im Bärenmarkt u.U. wenige oder
> keine."*

✔✔ **Damit ist die Frage entschieden, und zwar richtig:**

| | |
|---|---|
| **Die Tagesklammer unterstellt eine Allokation** — dass jeden Tag gleich viel Kapital arbeitet. Das ist eine **Entscheidung des Nutzers**, keine Eigenschaft der Bewertung |
| **Ein Signal ist keine Position.** Die Bewertung sagt, wo Potential ist; ob und wie groß daraus eine Position wird, ist die nächste, getrennte Frage |
| **Die schwankende Signalzahl ist erwartetes Verhalten**, kein Mangel — in der Breite viele, im Bärenmarkt wenige oder keine |

➤ **Für die Bewertungsfrage gilt gepoolt.** Die Tagesklammer bleibt als
Zahl ausgewiesen, weil sie für die Allokationsentscheidung gebraucht wird
— sie widerlegt die Bewertung nicht.

---

## Was daraus folgt

| # | |
|---|---|
| **1** | Die Bewertung **überlebt gröbere Auflösung** — B und D verlieren rund ein Drittel, tragen aber |
| **2** | ⭐ **Stufe D ist der Schlüssel zum Fallback**: keine High/Low nötig, und die Preisreihe gibt es für alle 15 Fehlenden |
| **3** | Der Unterschied kommt aus der **Auswahl**, nicht aus der Stopweite |
| **4** | Bei ATR-Kontrolle trägt die Bewertung in **4 von 5** Fünfteln |

## Was NICHT folgt

| # | |
|---|---|
| **1** | Ob **CoinGecko**-4h-Kerzen den hier **aggregierten** entsprechen — eigene Frage, **ungemessen** |
| **2** | Ob CoinGeckos Preisreihe dieselben Schlusskurse trägt wie Binance — **ungemessen** |
| **3** | Warum das **höchste ATR-Fünftel** nicht trägt — offen |
| **4** | Die **Hebelhöhe** bleibt gesperrt (2.609: Median negativ, Verteilung schief) |
| **5** | Nichts über **Short** |
