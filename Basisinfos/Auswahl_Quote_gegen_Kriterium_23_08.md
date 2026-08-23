# Quote oder Kriterium — und eine Richtigstellung an meiner eigenen Formulierung

*Nutzereinwand 23.08.: „Aus hunderten von Signalen pro Tag wird nun 1 oder 0,
und die Auswahl wird auf 2 Coins festbetoniert — für eine Zeit? Ohne Rücksicht
auf Strategie und Bestand? … Meine Vorstellung ist: die zu handelnden Assets
werden laufend gemessen, **ALLE**, und selektiv sollen jene Coins zum Zug
kommen, welche das **höchste Potential** aufweisen. Warum werden 2 Coins für x
Stunden gewählt — ist der falsche Grund. Korrekt wäre: **weil aus aktueller
Sicht jener Coin mit dieser Strategie das höchste Potential hat.**"*

---

## 1. ⚠️ Zuerst die Richtigstellung — der Schock geht auf meine Formulierung zurück

**Die Auswahl ist NICHT festbetoniert und NICHT zeitgebunden.**

`auswahl.waehle()` läuft **bei jedem Umlauf neu**, also alle 15 Minuten, über
**alle** Symbole der Gruppe. Steigt ein Wert auf, ist er im nächsten Lauf
dabei — es gibt keine Sperrfrist auf die Auswahl.

> **Der Grund lautet also schon heute genau so, wie Sie ihn verlangen:** *dieser
> Wert steht aus aktueller Sicht vorn* — nicht *„er wurde vor drei Stunden
> gewählt"*.

**Was ich geschrieben hatte** — *„es sind immer dieselben zwei, bis sich der
Rang ändert"* — ist zwar wahr, aber es klingt nach einer Sperre. Es ist keine:
es ist eine **Eigenschaft der Messgröße**. Eine 250-Tage-Rendite ändert ihre
Rangfolge langsam. **Das ist ein Argument über die Größe, nicht über die
Mechanik**, und ich hätte es so schreiben müssen.

---

## 2. Wo Sie recht haben — drei Punkte, und alle drei sitzen

### 2.1 ⚠️ Die Quote ist die falsche Konstruktion — und ich habe sie selbst benannt

In `A1_Auswahl_Dimensionierung_23_08.md` §2 steht von mir:

> *„Eine reine Rangauswahl unterstellt lautlos: es wird gekauft. Das ist die
> versteckteste Annahme von allen."*

**Und dann habe ich genau diese Konstruktion gebaut.** Eine Quote lässt immer
`k` durch — auch wenn keiner taugt — und sperrt den Dritten aus, auch wenn er
genauso gut ist.

### 2.2 Strategie und Bestand fehlen vollständig

Die Auswahl kennt **weder** die Strategie **noch** den Bestand. *„Dieser Coin
**mit dieser Strategie**"* ist nicht gebaut — und derselbe Wert kann für einen
Spot-Einstieg taugen und für einen gehebelten nicht.

### 2.3 ⚠️ Ihr stärkster Punkt: der Rang misst die **Vergangenheit**, nicht das **Potential**

Sie sagen *„höchstes Potential"*. Gebaut habe ich *„höchste Rendite der letzten
250 Tage"*. Dass das prognostisch etwas trägt, ist gemessen — **aber es ist
nicht dasselbe Wort und nicht dieselbe Größe.**

> **Das eigentliche Potentialmaß ist der Trichter** (Kapitel 93, „wie weit,
> nicht wohin") — und er geht in die Auswahl **gar nicht ein**. Er steht als
> Satz in der Mail.

---

## 3. Also gemessen: Quote gegen Kriterium

`messe_auswahl_kriterium.py`, 40 Symbole, 2017–2026, barrierenfrei und brutto:

**Horizont 20 Handelstage**

| Verfahren | keiner | im Schnitt durch | max | Auswahl | Markt | Abstand | t |
|---|---:|---:|---:|---:|---:|---:|---:|
| **quote_1** | 0 % | 1,0 | 1 | **+6,38 %** | +1,82 % | **+4,55 %** | 4,21 |
| **quote_2** | 0 % | 2,0 | 2 | +4,57 % | +1,82 % | **+2,74 %** | **4,52** |
| kriterium_median | 0 % | **9,6** | 20 | +2,60 % | +1,82 % | +0,78 % | 2,44 |
| kriterium_positiv | **12 %** | 5,3 | 14 | +2,37 % | +2,41 % | **−0,04 %** | −0,03 |
| kriterium_fuenftel | 12 % | 3,0 | 8 | +2,44 % | +2,41 % | +0,02 % | 0,02 |

### 3.1 ⚠️ Die unbequeme Antwort: der Vorteil IST die Spitze

Ohne absolute Bedingung fällt der Abstand **monoton** mit der Zahl der
Gewählten: 1 → **+4,55 %**, 2 → +2,74 %, 9,6 → +0,78 %.

> **Man kann nicht gleichzeitig breit auswählen und den gemessenen Vorteil
> behalten.** „Alle mit Potential durchlassen" heißt hier: **rund ein Viertel
> der Gruppe**, und der Vorsprung schrumpft auf ein Sechstel.

### 3.2 ⚠️ Und die absoluten Kriterien tragen gar nicht — aus demselben Grund wie heute früh

`kriterium_positiv` und `kriterium_fuenftel` liegen bei **t ≈ 0**. Der Grund
steht in ihrer eigenen Zeile: an den Terminen, an denen überhaupt jemand
qualifiziert, ist **der Markt selbst besser** (+2,41 % statt +1,82 %).

> **Der Filter wählt gute ZEITEN, nicht gute WERTE** — dieselbe Verwechslung
> wie „Quote gegen Timing" bei der Akkumulation. Was wie Auswahl aussieht, ist
> Marktzustand.

---

## 4. Die Deadloop-Sorge — gemessen, und sie trifft nicht

| | Termine ohne jede Auswahl |
|---|---|
| Quote (k = 1 oder 2) | **0 %** |
| Kriterium mit absoluter Bedingung | **12 %** |

**Weder das eine noch das andere sperrt zu.** ⚠️ Und der Unterschied zum alten
Deadloop ist grundsätzlich: dort ließ ein Tor **nichts** durch aus einem Grund,
der **nichts mit Qualität zu tun hatte** (ein kaputter Prompt). Hier ist die
Zahl bekannt, benannt und begründet.

---

## 5. Die Signalzahl — meine eigene Angabe war zu niedrig

| | |
|---|---|
| Beurteilungen je Tag, Krypto, heute | 85–150 (gemessen) |
| **nach A1** | **≈ 13,7** (2 Werte × 24 h / 3,5 h Cooldown) |
| Handlungsquote der Rollen-Kette | **15 %** (dokumentiert, gegen 1,8 % vor dem Umbau) |
| **erwartete Krypto-Signale je Tag** | **≈ 2**, plus die übrigen Gruppen |

⚠️ **Nicht „1 oder 0"** — ich hatte „rund jedes zehnte" geschrieben, dokumentiert
sind **15 %**. Und es waren auch vorher nie *hunderte Signale*: es waren
hunderte **Beurteilungen**, aus denen wenige Signale wurden — viele davon
**Wiederholungen desselben Werts**. Genau das war Ihr ursprünglicher Einwand.

---

## 6. Was daraus folgt — mein Vorschlag

| | was | warum |
|---|---|---|
| **K1** | ⚠️ **Den Trichter in die Auswahl bringen** — das eigentliche Potentialmaß, je Klasse geeicht, statt allein der Rückblicksrendite | Ihr Punkt 2.3. Das Maß ist gebaut und wird nicht benutzt |
| **K2** | **Auswahl je Strategie** — dieselbe Gruppe, zwei Ranglisten: Drift kurz (Hebel) und Rückkehr zum Mittel lang (Spot) | Ihr Punkt 2.2 |
| **K3** | **Bestand getrennt behandeln** — ein gehaltener Wert stellt die Halte-/Verkaufsfrage, nicht die Einstiegsfrage | Ihr Punkt 2.2 |
| **K4** | **Quote als Obergrenze, Kriterium als Bedingung** — nicht „genau 2", sondern „wer die Bedingung erfüllt, höchstens 2" | Ihr Punkt 2.1; die Quote verschwindet nicht, sie hört auf zu **erzwingen** |

⚠️ **K4 ist der einzige Punkt, an dem ich widerspreche, wenn er allein stünde:**
die Messung sagt, dass ein reines Kriterium den Vorteil verschenkt. Als
**Obergrenze** über einer Bedingung behält es beides — es zwingt nichts durch
und lässt nicht zu viele durch.
