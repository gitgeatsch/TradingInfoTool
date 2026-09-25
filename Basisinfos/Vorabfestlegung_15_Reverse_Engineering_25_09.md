# Vorabfestlegung 15 — Reverse Engineering der scharfen Anstiege

**25.09.2026, geschrieben VOR der Messung.** Nutzervorgabe, wörtlich:

> *„Es gibt Assets welche an einem Tag in 3 Stunden 20 oder mehr Prozent
> steigen — Dann mach reverse Engineering — Wie ist die LAGE bei diesen
> Assets wenn diese kurze und hohe Anstiege verzeichnen."*

Und die Einordnung, die dazugehört:

> *„Die Hebelgeometrie ist uninteressant da wir dies bereits kennen — erst
> wenn wir den Hebel Einstieg und die Bewertung für die Hebelhöhe kennen
> kommt die Geometrie ins Spiel"*

➤ **Diese Messung beantwortet den EINSTIEG und die BEWERTUNG. Die Geometrie
kommt danach.**

---

# § 1 ⭐ Die FORMWAHL — begründet

## 1.1 Warum FALL-KONTROLLE (reverse) und nicht Fünftel-Spanne

| | |
|---|---|
| **Fünftel-Spanne** (alles bisher) | fragt: *unterscheidet sich der Mittelwert der Fünftel?* Der Effekt wird über **alle** Anker gemittelt — auch über die 80 %, an denen nichts passiert. Gemessen: Streuung 0,19, Effekt 0,002–0,012, Nachweisgrenze 0,0102. **Effekt ≈ Fehler** |
| ⭐ **Fall-Kontrolle** | fragt: *wie sah die Lage VOR den Ereignissen aus, die den Trade getragen hätten?* Das Ereignis ist **extrem und selten**, der Kontrast damit **groß** — und die Prüfgröße ist eine **Häufigkeit**, nicht eine Mittelwertdifferenz |

⭐ **Der entscheidende Unterschied:** ein Merkmal kann im Mittel nichts
bewegen und trotzdem die **Extreme** ordnen. Eine Mittelwertmessung sieht das
per Konstruktion nicht.

## 1.2 Warum JETZT

| | |
|---|---|
| **Vorher nicht möglich** | die Stundenkurse liegen erst seit dem 24.09. vor (116 Symbole, 3,24 Mio Kerzen). Auf Tagesdaten ist „20 % in 3 Stunden" **unsichtbar** |
| **Alle Mittelwertwege sind ausgemessen** | funding, turnover, oi_aenderung auf `barriere`/H3: keiner trennt. Das ist nicht „noch eine Form derselben Frage", sondern eine **andere Frage** |
| ⚠️ **Und es ist KEIN fünfter Anlauf** | die vier funding-Anläufe vom 23.09. und die drei vom 25.09. waren alle **Mittelwertfragen auf Fünfteln**. Diese hier ist die erste Fall-Kontrolle des Projekts |

## 1.3 ⚠️ Was diese Form NICHT heilt

Sie macht die Daten nicht besser. Wenn die Ereignisse **nicht** vorhersagbar
sind, sagt sie das — und dann ist es ein Nullbefund auf einer **stärkeren**
Anlage, also ein härterer als alle vorigen.

---

# § 2 Das EREIGNIS — vorab definiert, nicht nach dem Sehen

**Ein Ereignis ist, was den Hebeltrade getragen hätte:** vom Einstieg
(Schlusskurs der Stunde `t`) wird ein **Ziel** erreicht, **bevor** ein
**Stop** fällt, innerhalb von `H` Stunden.

| | |
|---|---|
| **Stop** | **5 %** unter Einstieg — `GRENZEN['stop_min_relativ']`, die engste zulässige Weite. ⭐ Ein Hebeltrade braucht einen engen Stop; das ist keine Wahl, sondern die Bedingung dafür, dass überhaupt Hebel entsteht |
| **Ziel-Leiter** | **+10 % · +15 % · +20 %** (also CRV 2 / 3 / 4) |
| **Horizont-Leiter** | **3 · 6 · 12 · 24** Stunden |
| **Richtung** | LONG |

⚠️ **Die 20 % in 3 Stunden aus der Nutzervorgabe sind die härteste Zelle der
Leiter** — sie ist enthalten, aber nicht die einzige. Wer nur sie messen
würde, hätte keine Möglichkeit zu erkennen, ob ein Befund an der Schwelle
oder am Fenster hängt.

⚠️ **Reihenfolge innerhalb einer Stunde ist unbekannt** (auch die Stundenkerze
hat high und low). Wie in `barriere_je_reihe`: **Stop zuerst** prüfen — die
vorsichtige Annahme. Gemessen auf Tagesbasis kostete sie +0,0003 (2.583).

---

# § 3 ⭐ Die erste Frage kommt VOR der Bewertung: GIBT es die Ereignisse?

| | |
|---|---|
| **Häufigkeit** | Anteil der Anker mit Ereignis, je Zelle |
| **Breite** | auf **wie vielen Symbolen** treten sie auf — oder sind es drei Coins? |
| **Zeit** | je Jahr — oder war es nur 2021? |

⛔ **Liegt die Häufigkeit unter rund 0,1 % oder verteilt sie sich auf
weniger als 20 Symbole, ist die Bewertungsfrage nachrangig** — dann ist es
kein Geschäft, sondern eine Anekdote. Das wird **zuerst** ausgewiesen.

---

# § 4 Die LAGE — welche Merkmale, streng kausal

**Nur was zur Stunde `t` bekannt war.** Stündlich verfügbar:

| Quelle | Merkmale |
|---|---|
| `terminmarkt` (stündlich, 122 Symbole) | `oi_aenderung` · `konten_verh` · `top_konten_verh` · `top_summe_verh` · `taker_verh` |
| aus den Stundenkursen selbst | `vola` (realisiert) · `rsi` · `momentum_kurz` · `volumenanteil` |
| `funding_historie` (täglich) | `funding` — der Wert des **Vortags**, nie des laufenden Tages |
| **Kontrollen** | `zufall` (Negativ) · `momentum_kurz` (Positiv-Verdacht, s. § 6) |

⚠️ **Alle Merkmale werden als RANG innerhalb derselben Stunde gebildet** —
Querschnitt, nicht Niveau. Damit fällt die marktweite Bewegung heraus, die
sonst alles dominiert.

---

# § 5 Das MASS und die NORM

| | |
|---|---|
| ⭐ **Prüfgröße** | **Lift** = P(Ereignis \| oberstes Merkmalsfünftel) / P(Ereignis). Lift 2,0 heißt: in diesem Fünftel passiert es doppelt so oft |
| **warum Lift** | er ist genau das, was eine Hebelbewertung braucht — „wie viel wahrscheinlicher ist der Erfolg in dieser Lage". Eine Mittelwertdifferenz ist das nicht |
| **Nullpunkt** | Merkmalszuordnung **innerhalb jeder Stunde** mischen, **40** Ziehungen, **90. Perzentil** des Lifts (`messnorm.NULL_ZIEHUNGEN`, `NULL_PERZENTIL`) |
| ⚠️ **warum so gemischt** | Ereignisse **häufen sich** — ein marktweiter Schub trifft viele Symbole gleichzeitig. Ein naiver Binomialtest würde jede Häufung signifikant machen. Das Mischen **in** der Stunde erhält die Häufung und zerstört nur die Zuordnung |
| **Gewichtung** | Häufigkeit **gepoolt** über Anker (es ist ein Niveau), Rang **je Stunde** (es ist ein Querschnitt) — die Trennung aus der Regel vom 25.09. |
| **beide Hälften** | B6: erste gegen zweite Historienhälfte, getrennt ausgewiesen |

---

# § 6 Die VORHERSAGE — damit sie nachprüfbar ist

| Merkmal | Erwartung | Begründung |
|---|---|---|
| `momentum_kurz` | ⭐ **Lift > 1** | scharfe Anstiege setzen sich fort (Momentum-Literatur); wenn **irgendetwas** trägt, dann das. Dient als **Plausibilitätsanker** |
| `vola` | **Lift > 1** | ein 20-%-Sprung in 3 Stunden braucht Volatilität. ⚠️ **Aber er sagt nichts über die RICHTUNG** — das ist Geometrie, nicht Bewertung (F: `vola` ist Geometrie) |
| `oi_aenderung` | Lift > 1 | steigendes Open Interest zeigt Positionsaufbau |
| `funding` | **Lift < 1** im obersten Fünftel | hohes Funding = überhitzte Long-Seite; das ist die halbe Lehrmeinung, und sie ist auf `bewegung_r` belegt (23.09.) |
| `taker_verh` | offen | keine Vorhersage |
| `zufall` | **Lift = 1** | sonst ist der Lauf ungültig |

⚠️ **`vola` und `momentum_kurz` sind erwartete Treffer und deshalb die
schwächere Aussage.** Der interessante Fund wäre ein Merkmal, das **über
sie hinaus** trägt — das prüft § 7 Punkt 3.

---

# § 7 ⭐ Die ENTSCHEIDUNGSREGEL — vorab, wird nicht nachverhandelt

| # | Bedingung | Folge |
|---|---|---|
| **0** | Häufigkeit ≥ 0,1 % **und** ≥ 20 Symbole **und** in ≥ 3 Jahren | sonst: **Anekdote**, Rest nachrangig |
| **1** | `zufall` im Rauschen | sonst **Lauf ungültig** |
| **2** | Lift ≥ **1,5**, über dem Nullpunkt-Perzentil, auf ≥ 2 Zielschwellen **und** in beiden Hälften | ⭐ **das Merkmal ist eine Hebelbewertung** |
| **3** | Trägt es auch **bei festgehaltener `vola`** (innerhalb der Vola-Fünftel)? | sonst ist es **Volatilität mit anderem Namen** |
| **4** | Lift im Rauschen | kein Beitrag — und dann ist der Nullbefund **härter** als alle vorigen, weil die Anlage stärker ist |

---

# § 8 Was diese Messung **nicht** entscheidet

- **Nicht** die Hebel**höhe** in x — das ist die Umsetzung, und dafür braucht
  es erst einen Beitrag.
- **Nicht** die Geometrie (Stop, CRV, Klammer) — ausdrücklich nachgelagert.
- **Nicht** SHORT.
- **Nicht** Nicht-Krypto.
- ⚠️ **Nicht**, ob das Ereignis **handelbar** ist (Liquidität, Slippage,
  Ausführung in 3 Stunden). Eigene Frage, eigene Messung.

---

# § 9 ⚠️ Der Riegel auf den Daten

Vor jedem Lauf wird zugesichert:

| | |
|---|---|
| Zielgröße | nur **0.0 / 1.0** — sonst **Abbruch** (Befund 2.590) |
| Kausalität | jedes Merkmal aus Stunden **< t**, nachgewiesen an einem Verschiebungstest |
| Datenbank | nur `mode=ro`, **kein** Schreibzugriff |
