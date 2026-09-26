# Vorabfestlegung 23 — der Ende-zu-Ende-Test vor der Verdrahtung

**26.09.2026**, vor der Messung · Frageart **`beitrag`** (selektierte
Menge, nach `messnorm.FRAGEARTEN`)

> **Nutzerauftrag:** *„vor der Verdrahtung hätte ich gerne einen
> ausführlichen Test ob unsere Bewertungen, Kalibrierung, bei echten Daten
> auch das Ergebnis liefert dass es soll"* · *„langsam und sorgsam — keine
> Fehler, prüfen und gegenprüfen"*

---

## ⛔ Warum alles bisher Gemessene den Test NICHT ersetzt

| Was gemessen ist | Was fehlt |
|---|---|
| 2.608 Einstieg, 2.620 Geometrie, 2.622 `q` | jeder Baustein **für sich** |
| B6 in beiden Fensterhälften | prüft, ob ein Befund **gilt** — nicht, ob eine auf A **kalibrierte** Tabelle auf B **trägt** |
| 35 von 44 Symbolen | die Ordnung je Asset — nicht die **Kette** |

⚠️⚠️ **Der entscheidende Mangel: alle Zahlen sind in-sample.** Die Bänder
wurden auf denselben Daten gebildet, auf denen sie gemessen wurden. Das
ist Kurvenanpassung, bis das Gegenteil gezeigt ist.

---

## Die Frage

> **Liefert die Kette — Signal → `q` → Kelly → Hebel → Trade → Ergebnis —
> auf Daten, die sie nie gesehen hat, das, was die Bausteine versprechen?**

## Die fünf Bedingungen

| # | Bedingung | Warum sie unverzichtbar ist |
|---|---|---|
| **1** | **Out-of-sample**: `q`-Tabelle auf der **ersten** Hälfte kalibrieren, auf der **zweiten** anwenden | Der einzige Test, der Kurvenanpassung ausschließt |
| **2** | **Ende-zu-Ende**, nicht Baustein für Baustein | Fehler entstehen an den **Übergängen** |
| **3** | Gegen die **15 liquiden** Symbole, nicht gegen 115 | Der Betrieb sieht eine andere Menge |
| **4** | **Mit Takt und Cooldown** | Sie sperren 69 % — sonst misst man eine Signalmenge, die es nie geben wird |
| **5** | **Positivkontrolle**: dieselbe Kette auf **Zufallssignalen** | Sonst weiß man nicht, ob das Ergebnis aus der Bewertung kommt oder aus der Geometrie |

---

## ⚠️⚠️ Die Fallen, die ich vorab benenne

### Falle 1 — die Tabelle darf die zweite Hälfte nicht kennen

Weder über die **Bandgrenzen** noch über die **Geometrie** noch über die
**Schwelle**. Alles, was aus 2.620 und 2.622 stammt, wurde auf der
**vollen** Menge bestimmt.

➤ **Deshalb wird die Geometrie MITKALIBRIERT**, nicht übernommen: auf der
ersten Hälfte neu bestimmt, auf der zweiten angewandt. Sonst schleicht sich
Wissen über die zweite Hälfte ein.

⚠️ Das macht den Test **strenger** als nötig — und genau das ist gewollt.

### Falle 2 — `q` und CRV gehören zusammen

Aus 2.622: die gemessene Quote mit dem angenommenen CRV zu mischen
überschätzt Kelly um 71 %. **Beide kommen aus derselben Kalibrierhälfte.**

### Falle 3 — der Erfolgsmaßstab muss vorher feststehen

Sonst sucht man hinterher den, der passt.

| Maßstab | vorab festgelegt |
|---|---|
| **Hauptgröße** | **geometrischer Ertrag** je Trade in der zweiten Hälfte |
| **Vergleich** | dieselbe Kette mit **Zufallsauswahl** gleicher Größe |
| **Bestanden** | geometrischer Ertrag **über** dem 90. Perzentil der Zufallskette |
| **Zusätzlich berichtet** | `q` erwartet gegen `q` eingetreten, Kelly erwartet gegen realisiert, Trefferquote, Verlustserie, Signale/Tag |

⭐ **Die schärfste Einzelprüfung: trifft das vorhergesagte `q`?** Wenn die
Tabelle für ein Band 48 % verspricht und in der zweiten Hälfte 41 %
eintreten, ist die Kalibrierung wertlos — **unabhängig vom Ertrag**.

### ⚠️⚠️ Falle 4 — Leckage über den Horizont

**Beim Schreiben des Werkzeugs aufgefallen, deshalb hier nachgetragen:**
Ein Anker am **Ende** des Kalibrierfensters sieht mit H = 72 h **drei Tage
in das Prüffenster hinein**. Seine Zielgröße stammt teilweise aus Daten,
die als „ungesehen" gelten sollen.

➤ **Zwischen Kalibrier- und Prüffenster bleibt eine Lücke von H Stunden.**
Ohne sie wäre der Test nicht out-of-sample, sondern nur fast.

⚠️ Das kostet Anker und ist trotzdem zwingend — eine Leckage von drei Tagen
würde genau den Effekt erzeugen, den der Test ausschließen soll.

### Falle 5 — ein einzelner Split ist Zufall

➤ **Nicht eine Teilung, sondern eine rollierende:** fünf Fenster, jeweils
auf dem Vorangegangenen kalibriert und auf dem Folgenden geprüft. So ist
das Ergebnis nicht von einem Schnittpunkt abhängig.

---

## Was VOR der Messung als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| `q` trifft (± Band) **und** geometrischer Ertrag über der Zufallskette, in der Mehrheit der Fenster | ✔ **die Kalibrierung trägt** — Verdrahtung vertretbar |
| `q` trifft, Ertrag nicht | ⚠️ die Ordnung stimmt, die **Höhe** nicht — brauchbar für eine Schwelle, **nicht für Kelly** (genau die Unterscheidung aus 2.558) |
| `q` trifft nicht | ⛔ **Kurvenanpassung.** Die Kalibrierung fällt, und die Verdrahtung ist gesperrt |

⛔ **Kein „im Großen und Ganzen".** Die Bedingung steht oben und wird nicht
nachträglich gelockert.

## Was der Test NICHT beantwortet

| # | |
|---|---|
| **1** | **Gebühren und Finanzierung** — bleiben draußen (Regel 2) |
| **2** | **Ausführbarkeit**, Slippage, Teilausführung |
| **3** | Ob die **LLM-Stufe** die Auswahl verändert — sie ist nicht Teil der Rechnung |
| **4** | Die **Verdrahtung** selbst — das ist Bau, nicht Messung |
| **5** | Nichts über **Short** |
