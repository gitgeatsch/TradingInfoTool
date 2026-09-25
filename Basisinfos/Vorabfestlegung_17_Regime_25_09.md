# Vorabfestlegung 17 — Ist der Marktzustand vorab erkennbar?

**25.09.2026**, vor der Messung geschrieben · Schritt 3 des Hebel-Neubaus ·
Werkzeug `messe_regime_rollierend.py`

**Nutzerentscheidung:** *„Regime rollierend messen"* — nach 2.598, das den
Faktor 12 zwischen Regime und Lage gemessen hat.

---

# § 1 Die Fragestellung

> **Gibt es einen zum Zeitpunkt t VERFÜGBAREN Marktzustand, der `E[R]`
> brutto über null hebt?**

⚠️ **Betont: brutto.** Nach 2.597 § 5.3 ist das die **Niveau**frage, und nur
sie entscheidet über den Hebel. Netto (gegen die Drift) ist die
Querschnittsfrage und hier ausdrücklich **nicht** gestellt.

## 1.1 H0 und H1

| | |
|---|---|
| **H0** | Kein zum Zeitpunkt t verfügbarer Marktzustand ordnet `E[R]` brutto über dem Nullband. Das Regime ist nur **im Rückblick** erkennbar |
| **H1** | Mindestens ein Marktzustand ordnet `E[R]` brutto, und im besten Fünftel ist `E[R]` **> 0** |

⚠️⚠️ **H1 hat zwei Stufen, und nur die zweite trägt einen Hebel:**
*ordnen* (das Fünftel trennt) und *tragen* (`E[R] > 0`). 2.594 hat gezeigt,
dass Ordnen ohne Tragen möglich ist — das darf nicht wieder verwechselt
werden.

## 1.2 ⭐ Die Vorhersage, damit ein Treffer nachprüfbar ist

**Erwartet:** Marktbreite und Markt-Momentum ordnen (sie sind im Grunde die
Drift selbst, einen Schritt früher). **Offen und der eigentliche Test:** ob
die Ordnung über die **Zeitgrenze** hinweg hält — also ob der Marktzustand
*bis t* etwas über die Stunden *nach t* sagt.

⚠️ **Ein Treffer bei Marktbreite ist die schwächere Art Fund** (erwartet).
Ein Treffer bei Markt-Vola wäre die stärkere, weil dafür kein Mechanismus
vorgezeichnet ist.

---

# § 2 ⚠️⚠️⚠️ Das Konstruktionsproblem — und warum die übliche Nullwelt hier FALSCH wäre

Alle Regime-Merkmale sind **marktweit**: zu einer Stunde haben *alle* Symbole
denselben Wert. Daraus folgt zweierlei:

| | |
|---|---|
| **1** | Die **Stundenklammer funktioniert nicht.** Innerhalb einer Stunde ist der Wert konstant, es gibt kein Fünftel zu bilden. Gemessen wird **gepoolt** über alle Anker — was für die Niveaufrage richtig ist (registriert: Niveau → gepoolt) |
| **2** | ⛔⛔ **Die Nullwelt aus 2.597 wäre hier grob falsch.** Dort wurde das Fünftel je Anker zufällig gezogen. Hier hätte das ein absurd enges Band: 3,2 Mio Anker stammen von ~1.700 Tagen, und der Marktzustand bleibt über Tage nahezu gleich. Die **effektive** Stichprobe ist um Größenordnungen kleiner als `n` |

## 2.1 ⭐⭐⭐ Die richtige Nullwelt: ZYKLISCHE VERSCHIEBUNG

Das Regime-Merkmal wird als **Zeitreihe** gegen die Ausgänge verschoben.

| | |
|---|---|
| **Was erhalten bleibt** | die vollständige Autokorrelation **des Merkmals** und **der Ausgänge**, jede Randverteilung, jede Regimeperiode |
| **Was gebrochen wird** | allein der **Zusammenhang** zwischen beiden |
| **Verschiebung** | zufällig, aber mindestens **90 Tage**, damit kein Restzusammenhang bleibt |
| **Ziehungen** | 40, Bezug = Mittelwert, Grenze = 90. Perzentil (Messstandard) |

➤ **Das ist die einzige Nullwelt, die hier eine Aussage trägt.** Eine
ankerweise Permutation würde jedes Merkmal als Treffer ausweisen, auch
`zufall`.

## 2.2 Die eingebaute Gegenprobe dazu

⭐ **`zufall` als Merkmal wird mitgeführt** — aber als *autokorrelierte*
Zufallsreihe (gleitendes Mittel über 30 Tage einer Zufallsreihe), nicht als
weißes Rauschen. Ein weißes `zufall` würde hier nichts prüfen, weil es die
Struktur gar nicht hat, um fälschlich zu treffen.

---

# § 3 Die Merkmale — alle streng kausal, alle aus den Stundenkursen

| Merkmal | Bildung bis t | Was es misst |
|---|---|---|
| `breite` | Anteil der Symbole über ihrem eigenen 30-Tage-Mittel | Marktbreite |
| `markt_momentum` | Median der 7-Tage-Rendite über alle Symbole | Markttrend |
| `markt_vola` | Median des ATR über alle Symbole | Marktnervosität |
| `btc_trend` | BTC relativ zum eigenen 30-Tage-Mittel | Leitwert |
| `zufall` | autokorrelierte Zufallsreihe (s. § 2.2) | **Kontrolle** |

⚠️ **`btc_trend` ist kein Asset-Rang.** Regel 3 verbietet, den Hebel aus
einer Rangliste der Assets zu erzeugen. BTC steht hier als
**Marktindikator** für alle Symbole gleich, nicht als bevorzugtes Asset —
kein Symbol wird dadurch besser oder schlechter gestellt.

---

# § 4 Die Rückschau-gegen-kausal-Doppelung — die Lehre aus 2.598

⭐⭐ **Jede Ordnung wird in zwei Fassungen gerechnet:**

| Fassung | Fünftelgrenzen aus | Bedeutung |
|---|---|---|
| **Rückschau** | dem **ganzen** Fenster | ⛔ keine Strategie — kennt die Zukunft |
| **KAUSAL** | nur den Daten **bis t** (expandierendes Fenster) | ✔ eine echte Betriebsregel |

➤ **Nur die kausale Fassung darf in eine Bewertung.** In 2.598 hat genau
diese Doppelung den Symbolauswahl-Weg als Überanpassung entlarvt (Rückschau
+Faktor 4,5, kausal schlechter). ⚠️ **Ohne sie wäre sie durchgegangen.**

---

# § 5 Welche Standards hier gelten — und welche nicht

| | |
|---|---|
| **gilt** | Bezug = Nullpunkt (Mittelwert) · 40 Ziehungen, 90. Perzentil · Kontrollmerkmal `zufall` · Trennschärfe · Rückschau gegen kausal · Dosis-Wirkung über H · Abnahmeprobe |
| **angepasst** | Nullwelt = **zyklische Verschiebung** statt Permutation (§ 2.1) · **gepoolt** statt geklammert (§ 2, Punkt 1) · `zufall` **autokorreliert** statt weiß |
| **gilt nicht** | Stundenklammer · Tagesklammer · `HORIZONT_JE_LAGE` = 3 Tage · **F-212 selektierte Menge** (keine stündliche Kette) |
| ➤ **Frageart** | **`markt`** — Menge = Messuniversum. Es ist ausdrücklich **keine** `beitrag`-Frage: gemessen wird ein Marktzustand, kein Asset-Merkmal |

---

# § 6 Was diese Messung NICHT beantworten kann — vorab benannt

| # | |
|---|---|
| **1** | ⛔ **Nicht, ob ein Filter im Betrieb Geld verdient.** Gebühren und Finanzierung bleiben draußen (Regel 2) |
| **2** | ⛔ **Nicht die Lagefrage.** Ob innerhalb eines tragenden Regimes die Lage trennt, ist Schritt 4 und setzt einen Treffer hier voraus |
| **3** | ⚠️ **Nicht die Regimezahl.** Auch rollierend gemessen bleiben es faktisch **wenige** Regimewechsel im Fenster — die zyklische Verschiebung macht das Band ehrlich, sie schafft keine neuen Beobachtungen |
| **4** | ⚠️ **Nichts über künftige Regime.** Ein Filter, der 2021–2026 trägt, ist damit nicht auf 2027 übertragen |
| **5** | ⛔ **Nichts über Short** — ruht weiter |
