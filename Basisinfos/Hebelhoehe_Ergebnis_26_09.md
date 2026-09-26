# Die Hebelhöhe — die Statistik liefert keine Obergrenze

**26.09.2026** · Befund 2.627 · auf der inversen Achse (2.626)

> **Nutzerhinweis, der den Rahmen klärt:** *„was hat die Kapitalbindung in
> unserem Projekt verloren im Bärenmarkt? … wir reden von Hebel und Lagen,
> nicht Regimes."*

---

## ⛔ Zuerst: eine Frage, die ich falsch eingeordnet hatte

Ich hatte die Kapitalbindung als „offene Flanke" des Hebels notiert. **Das
war eine Spot-Frage im Hebel-Kontext:**

| | Spot / Akkumulation | **Hebel** |
|---|---|---|
| Haltedauer | Monate | **6–24 Stunden** |
| Verhalten | nachkaufen, aufbauen | **Trade auf, Trade zu** |
| Kapitalbindung | wächst über die Zeit | **durch Deckel geregelt** — 3.000 EUR Topf, 1.000 je Position, 3 Trades |

➤ **Die „11 Monate Nachkauf"-Falle kann beim Hebel nicht entstehen.** Und
das Regime ist ohnehin nicht der Gegenstand: **2.599** hält fest, dass der
Marktzustand nicht vorab erkennbar ist, und Regel 3 sagt, wir bewerten
**Lagen**.

---

## Die Kennzahlen auf der inversen Achse

Auswahl: täglich beste 2 % nach niedrigstem `ema_abstand_atr`,
Trailing 1,0 ATR:

| H | Signale | **q** | CRV | Kelly | längste Verlustserie |
|---|---|---|---|---|---|
| **6** | 63.727 | **66,9 %** | 1,362 | **0,4253** | 67 |
| 12 | 63.708 | 65,5 % | 1,365 | 0,4025 | 69 |
| 24 | 63.683 | 59,9 % | 1,456 | 0,3241 | 117 |

⭐ Die Verlustserie ist **deutlich kürzer** als auf der alten Achse (199,
2.621) — bei rund 36 Signalen je Tag sind 67 Trades knapp zwei Tage.

---

## ⛔⛔ Warum die Trefferquote so hoch ist — und warum das täuscht

Verteilung der Ergebnisse bei H6:

| Bereich in R | Anteil |
|---|---|
| **Stop erreicht** (≤ −0,99) | **0,4 %** |
| −0,99 bis −0,5 | 3,3 % |
| −0,5 bis 0 | 27,9 % |
| **0 bis +0,5** | **57,3 %** |
| +0,5 bis +1 | 9,5 % |
| über +1 | 1,6 % |

**Median +0,1198 R · Mittel +0,1292 R**

➤ **Der Stop wird praktisch nie erreicht.** In sechs Stunden bewegt sich
der Kurs selten um 1 ATR — das ist eine **Tagesspanne**. Die meisten
Trades enden am **Horizontende** mit einem kleinen Gewinn.

### Und deshalb hat der geometrische Ertrag kein Maximum

| Hebel | geometrisch |
|---|---|
| 5 | +0,62954 % |
| 10 | +1,22735 % |
| 20 | +2,33067 % |
| 42 | +4,32483 % |
| **60** | **+5,46703 %** |

**Monoton bis Hebel 60.** Das ist **kein Befund, sondern ein Artefakt der
Stop-Annahme**: Die Trailing-Rechnung unterstellt, dass der Stop **immer
exakt bei −1 R greift**. Damit ist die Verlustseite künstlich
abgeschnitten — und ohne Verlustrisiko empfiehlt Kelly beliebig viel
Hebel.

⛔ **Was in dieser Rechnung fehlt:**

| | |
|---|---|
| **Gaps** | ein Kurssprung überspringt den Stop |
| **Liquidation** | RM-11 gemessen: bei Hebel 10 liegt sie **vor** dem Stop (0,0 Tage Reserve) |
| **Slippage** | bei 36 Signalen/Tag auf teils engen Werten |

---

## ⭐⭐ Die Antwort: die Höhe folgt aus dem Risiko, nicht aus der Statistik

| Hebel | Kontoverlust bei Stop | RM-11 (99. Vola-Perzentil, Stop 1,0 ATR) |
|---|---|---|
| 2 | 2 % | ✔ sicher |
| 3 | 3 % | ✔ sicher — 3,14 erlaubt |
| **5** | **5 %** | ⚠️ knapp, nur bis Vola-Median (6,52 erlaubt) |
| 10 | 10 % | ⛔ Liquidation **vor** dem Stop |

➤ **Die Zielzone 2–5× ist damit sachlich begründet** — nicht durch Kelly,
sondern durch **RM-11 und die Verlustserie**. Bei 67 Verlusten in Folge
wären es bei Hebel 5 mehrere Prozent Kontoverlust nacheinander; das
spricht für das **untere Ende** der Zone.

⚠️⚠️ **Was damit NICHT behauptet ist:** dass 2–5× optimal *gemessen* sei.
Gemessen ist, dass die Statistik hier **keine Obergrenze liefert** und die
Begrenzung deshalb aus RM-11 und der Verlustserie kommen muss. Das ist
eine andere Art von Antwort als „Kelly sagt X" — aber die ehrliche.

---

## Was daraus folgt

| # | |
|---|---|
| **1** | ⭐ **2.609 ist beantwortet**, aber anders als erwartet: die Hebelhöhe folgt **nicht** aus `E[R]` und auch nicht aus Kelly — sondern aus der Liquidationsgrenze |
| **2** | Die **Zielzone 2–5×** ist begründet, das untere Ende vorzuziehen |
| **3** | Die **Verlustserie** ist auf dieser Achse deutlich kürzer (67 gegen 199) |
| **4** | Die **Kapitalfrage** gehört zum Spot-Arm, nicht zum Hebel |

## Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Kein optimaler Hebel gemessen** — die Statistik liefert keine Obergrenze |
| **2** | **Gaps und Slippage sind nicht modelliert** — die Verlustseite ist im Modell zu freundlich |
| **3** | Die **Geometrie** (2.620) wurde für die alte Richtung dimensioniert; ob Stop 1,0 ATR und Trailing 1,5/0,5 für die inverse Achse optimal sind, ist **ungeprüft** |
| **4** | Gebühren und Finanzierung bleiben draußen (Regel 2) |
| **5** | Nichts über **Short** |
