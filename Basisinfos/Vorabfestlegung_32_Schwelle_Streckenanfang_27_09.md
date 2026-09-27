# Vorabfestlegung 32 — die Schwelle auf Streckenanfängen

**27.09.2026**, vor der Messung · `messe_schwelle_anfang.py` ·
Frageart **`markt`**

> **Warum:** −1,2881 ist die Kelly-Nullstelle über **alle** Anker (2.632).
> Der Betrieb kauft aber nur **Streckenanfänge** (2.638) — dort liegt der
> Ertrag bei +0,3393 statt +1,2568 Prozent.

---

## Die Frage

> **Bei welcher Schwelle wird Kelly null, wenn nur Streckenanfänge zählen?**

## ⚠️ Das Zirkularitätsproblem — und wie es aufgelöst wird

Die Schwelle bestimmt, **wo eine Strecke anfängt**. Die Strecken bestimmen,
**welche Anker in die Rechnung gehen**. Beides hängt voneinander ab.

➤ **Auflösung:** für **jede** Kandidatenschwelle wird die Streckenmenge
**neu** abgegrenzt und Kelly darauf gerechnet. Jede Kandidatin wird für
sich konsistent behandelt; es gibt keine Iteration und keinen Startwert,
der das Ergebnis beeinflusst.

⚠️ **Das ist nicht dasselbe wie in 2.632.** Dort lief ein gleitendes
Fenster über die nach `W` sortierten Anker. Hier ist die Menge je
Schwelle eine andere — ein gleitendes Fenster wäre hier falsch.

## Der Aufbau

| | |
|---|---|
| Streckenanfang | erstes Unterschreiten der jeweiligen Schwelle, danach 24 h Sperre je Symbol |
| Kandidatenschwellen | −0,8 bis −2,6 in Schritten von 0,05 |
| je Schwelle | `q`, `CRV`, `kelly = (q(1+CRV)−1)/CRV`, Ertrag, Signale/Tag |
| Bezug | tagestreue Nullwelt, 40 Ziehungen |

## ⭐ Die zweite Frage — sie kommt vom Nutzer

> *„bedeutet das, wir benötigen für Binance und CoinGecko Beiträge zwei
> Bewertungen?"*

**Antwort aus 2.637: nein** — der Skalenfaktor 2,0832 macht beide Größen
vergleichbar. ⚠️ Aber dieser Faktor wurde auf **allen** Ankern bestimmt.
Diese Messung prüft mit: **fallen die Nullstellen von A und D-korrigiert
auf Streckenanfängen zusammen?**

| Ausgang | Folge |
|---|---|
| Nullstellen nahe beieinander | ✔ **eine** Bewertung, eine Schwelle — 2.637 gilt auch hier |
| Nullstellen weit auseinander | ⛔ dann doch **zwei** Schwellen, und der Faktor müsste je Betriebsfall neu bestimmt werden |

## ⚠️ Die Fallen

| # | |
|---|---|
| **1** | **Strecken je Schwelle neu abgrenzen** — nicht einmal bei −1,2881 und dann übertragen |
| **2** | ⭐ **Mehrfachtesten**: 37 Kandidatenschwellen sind 37 Ziehungen. Bestes-von-allen-Band |
| **3** | Die Kelly-Nullstelle ist **interpoliert**, nicht gerastert — sonst hängt sie an der Schrittweite |
| **4** | **Zeitstabilität und Weglassprobe** gehören dazu — sie haben heute schon einen Befund gekippt (2.633) |
| **5** | Regel 2: Gebühren und Finanzierung bleiben draußen |
| **6** | ⚠️ Bei tiefen Schwellen wird die Menge **dünn** (bei −1,8 nur 400 Anfänge). Eine Mindestzahl ist zu setzen und auszuweisen |

## Was vorher als Ergebnis gilt

| Ausgang | Folge |
|---|---|
| Nullstelle gefunden, zeitstabil, über dem Mehrfach-Band | ✔ **das ist die Betriebsschwelle** |
| gefunden, aber nicht zeitstabil | ⚠️ wie 2.633 — dann keine Schwelle, sondern ein Bereich |
| Kelly bleibt überall positiv | ⭐ dann begrenzt nicht die Bewertung, sondern die **Signalzahl** — und die Schwelle folgt aus der Kapazität |

## Was NICHT beantwortet wird

Gebühren · Gaps und Slippage · die Positionsgröße (2.639) · der
Horizont-Widerspruch
