# Vorabfestlegung 31 — die Depot-Simulation

**27.09.2026**, vor der Messung · `simuliere_depot.py` ·
Frageart **`markt`**

> **Nutzerauftrag:** *„Optimal wäre auch noch eine saubere Simulation an
> Echtdaten, wie weit die Ergebnisse abweichen"*

---

## Was bisher fehlt

Gemessen sind der Ertrag **je Trade** (+1,2568 gegen +1,2864) und die
Überlappung der Auswahl (68,7 % / 55,4 %). Was ein **Depot** daraus
macht — mit **Kapazitätsgrenze**, über die Zeit, mit Verlustserien und
Rückgängen — ist offen.

⭐ Das beantwortet zugleich den offenen Punkt aus 2.633: die Signalmenge
schwankt zwischen **3,2 und 11,7 je Tag**, und es gibt heute **keinen
Deckel**.

## Die Frage

> **Wie weit weichen die Depotergebnisse ab, wenn ein Teil der Symbole
> ohne High/Low bewertet wird?**

## Der Aufbau

| | |
|---|---|
| Ablauf | chronologisch über alle Stunden; wer die Schwelle unterschreitet, kommt auf die Kandidatenliste |
| **Kapazität** | höchstens `N` Positionen gleichzeitig — bei Überhang **die besten** (niedrigstes `W`) |
| Sperre | ein Symbol nie zweimal gleichzeitig |
| Haltedauer | H24, Ergebnis aus dem Trailing (1,5 R / 0,5 R, Stop 1,00 ATR) |
| Konto | geometrisch: `ln(1 + einsatz · hebel · kursprozent)` |
| Hebel | **konstant** — die Stufung trägt nicht (2.633) |

## Die Varianten

| # | Bewertung | entspricht |
|---|---|---|
| **1** | alle mit **A** (echtes OHLC) | der Idealfall, alle 44 bei Binance |
| **2** | alle mit **D korrigiert** | der Fall, alle 44 über CoinGecko |
| **3** | ⭐ **36 % der Symbole mit D**, der Rest mit A | **der reale Betrieb** — 16 von 44 |
| **4** | Zufallsauswahl gleicher Größe | die Kontrolle |

⚠️ Variante 3 ist die eigentliche Frage. Welche Symbole auf D laufen,
wird **gelost** und über mehrere Ziehungen gemittelt — die echten 16
haben keine Stundendaten und können nicht simuliert werden.

## Kennzahlen

Endwert (geometrisch) · Zahl der Trades · Trefferquote · **längste
Verlustserie** · **größter Rückgang** · Ergebnis **je Jahr**

## ⚠️ Die Fallen

| # | |
|---|---|
| **1** | **Kapazität ändert die Menge.** Weniger Plätze heißt strengere Auswahl — der Vergleich muss bei **gleicher** Kapazität laufen |
| **2** | ⭐ **Keine Zukunft**: die Kandidatenwahl kennt nur `W` zum Zeitpunkt der Eröffnung, nie das Ergebnis |
| **3** | **Selbstprobe**: bei sehr großer Kapazität muss der mittlere Trade-Ertrag gegen den bekannten Wert laufen (+1,2568 für A). Läuft er davon, ist die Buchführung falsch |
| **4** | **Die Zufallskontrolle** muss deutlich schlechter sein — sonst misst man die Kapazitätsregel statt der Auswahl |
| **5** | Der Einsatz je Position ist ein **Maßstab**, kein Ergebnis — er trifft alle Varianten gleich |
| **6** | Regel 2: Gebühren und Finanzierung bleiben draußen. ⚠️ Für ein **Depot**ergebnis ist das eine echte Einschränkung und gehört ausgewiesen |

## Was vorher als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| Variante 3 liegt nahe an Variante 1 | ✔ die Mischung ist unbedenklich, alle 44 bauen |
| Variante 3 deutlich schlechter | ⚠️ die 16 kosten mehr, als der Einzeltrade-Vergleich zeigt |
| Variante 2 ≈ Variante 1 | bestätigt 2.637 auf Depotebene |

## Was NICHT beantwortet wird

Gebühren und Finanzierung · Gaps und Slippage · Steuern · ob die echten
16 dieselbe Datenqualität haben wie die simulierten
