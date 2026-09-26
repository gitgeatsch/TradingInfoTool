# Die Fallback-Stufen — Entwurf

**26.09.2026** · Nutzerauftrag: *„wir benötigen auch eine fallback lösung
wenn eine Bewertung nicht oder nur zum Teil gedeckt ist"* · **Entwurf,
nichts gebaut**

Gründet auf 2.616 (die Auflösung trägt), 2.613 (CoinGecko liefert),
2.612/2.614/2.615 (die Symbolwelten).

---

## ⚠️ Zwei Vorgaben, die den Entwurf bestimmen

> **Nutzervorgabe 26.09.:** *„Eine Signal ist keine Position und die
> Entscheidung zur Kapitalallokation ist meine."*

➤ Der Fallback **entscheidet nichts** über Positionen. Er sagt, **auf
welcher Grundlage** eine Bewertung steht — die Verwendung bleibt beim
Nutzer.

> **Nutzervorgabe 26.09.:** *„btc ist nicht nur ein Asset sondern das eine
> Asset im Kryptomarkt mit Sonderstellung, de facto eine eigene Klasse."*

➤ BTC ist in **allen** Messungen ausgeschlossen (`if sym == "BTC":
continue`) und hat **immer volle Datenlage**. Die Fallback-Stufen
betreffen **nur** die übrigen Werte. Siehe Abschnitt am Ende.

---

## Das bestehende Prinzip — und warum es hier NICHT passt

Das System hat bereits einen Fallback für fehlende Datenlage
(`agent/potential.py:219`, Nutzerentscheidung 31.08.):

```python
schwelle = Vorgabe × (erreichbar_max / erreichbar_voll)
```

*„Wer nur einen Beitrag hat, muss denselben ANTEIL seiner Spanne schaffen
wie einer mit zweien."*

⚠️⚠️ **Das lässt sich hier nicht übernehmen, und der Unterschied ist
wesentlich:**

| | Beiträge (31.08.) | Auflösung (hier) |
|---|---|---|
| Was fehlt | ein **Summand** — die erreichbare Spanne wird kleiner | **nichts** — dieselbe Größe, nur verrauschter |
| Wirkung auf die Skala | Skala schrumpft → Schwelle muss mit | Skala **bleibt** (nach der √(24/takt)-Korrektur: 1,00 / 1,02 / 1,05) |
| Richtige Anpassung | **Schwelle senken** | ⛔ **Schwelle NICHT senken** — das ließe nur mehr schlechte Signale durch |

➤ **Die richtige Anpassung ist die Erwartung, nicht die Schwelle.**
Gleiche Schwelle, gleiche Auswahl — aber **ausgewiesen kleinere Wirkung**.

⚠️ **Eine Ausnahme:** Stufe D hat eine **andere Skala** (ATR-Median
0,48×), weil eine Renditebasis systematisch kleiner ist als eine
Spannenbasis. Dort ist die Schwelle **umzurechnen** — gemessen erreicht
sie dieselbe Signalzahl bei **1,992** statt 1,0.

---

## Die Stufen

| Stufe | Grundlage | Quelle | Wirkung | Schwelle | Abdeckung |
|---|---|---|---|---|---|
| **1 — voll** | 1-h-OHLC | Binance | **100 %** *(+0,6611 %)* | 1,000 | 28 von 43 |
| **2 — gut** | 4-h-OHLC | CoinGecko `…/ohlc` | **67 %** *(+0,4452 %)* | 1,021 | +15 |
| **3 — brauchbar** | ⭐ stündliche **Preisreihe**, kein High/Low | CoinGecko `market_chart` | **65 %** *(+0,4296 %)* | **1,992** | +15 |
| **4 — grob** | Tages-OHLC | vorhanden | **51 %** *(+0,3357 %)* | 1,261 | +13 |
| **5 — keine** | — | — | ⛔ **keine Bewertung** | — | CANTON-Fall |

⭐⭐ **Stufe 3 schlägt Stufe 2 in der Praxis**, obwohl sie minimal
schwächer misst: CoinGecko liefert die Preisreihe für **15 von 15**, das
grobe OHLC ebenfalls — aber die Preisreihe ist **stündlich**, das OHLC
nur 4-stündig. Bei fast gleicher Wirkung (65 % gegen 67 %) ist die
feinere Zeitachse der Vorteil.

⚠️ **Die Prozente sind gemessen** (2.616, 3,18 Mio Anker), aber sie gelten
für **aggregierte** Kerzen aus Binance-Daten. Dass CoinGecko dieselben
Werte liefert, ist **ungemessen** — das ist die erste Prüfung vor jedem
Einsatz.

---

## Was der Entwurf vorsieht

| # | |
|---|---|
| **1** | **Jede Bewertung trägt ihre Stufe mit** — als Feld, nicht als Fußnote. Ohne Stufe keine Bewertung |
| **2** | **Die Schwelle bleibt**, außer bei Stufe 3 (eigene Skala, Faktor gemessen) |
| **3** | **Die erwartete Wirkung wird mit dem Stufenfaktor ausgewiesen** — 100 / 67 / 65 / 51 % |
| **4** | **Stufe 5 erzeugt kein Signal**, sondern eine **Meldung**: „Asset X ist bewertbar, sobald Kurse vorliegen" — heute stumm |
| **5** | **Die Stufe steht in der Mail**, damit der Nutzer sie bei der Allokation berücksichtigen kann — nicht damit das System entscheidet |

⛔ **Was der Entwurf NICHT vorsieht:** dass die Stufe eine Position
verhindert, verkleinert oder vergrößert. Das ist Allokation und damit
Nutzerentscheidung.

---

## ⭐ BTC — die eigene Klasse

> *„der Trend wird meist durch btc getragen und ist kein Fehler sondern
> leider Teil des Markts"*

Das ordnet zwei Dinge ein, die heute schon so sind:

| | |
|---|---|
| **BTC ist aus der Messbasis ausgeschlossen** | `if sym.upper() == "BTC": continue` in allen Messwerkzeugen. Richtig, denn BTC ist nicht ein Wert unter 116, sondern der **Bezug** |
| **Die Signalhäufung ist Marktstruktur** | Viele Signale an guten Tagen, wenige oder keine im Bärenmarkt — das ist **erwartet** (2.617), kein Artefakt und kein Mangel |
| **BTC hat immer Stufe 1** | volle Datenlage in jeder Quelle. Der Fallback betrifft BTC nie |

⚠️ **Offene Frage, die daraus folgt:** Wenn BTC de facto eine eigene
Klasse ist — **braucht es eine eigene Bewertung?** Heute wird es wie ein
Altcoin bewertet, nur eben aus der Messbasis herausgenommen. Das ist eine
Inkonsequenz: entweder es ist der Bezug (dann keine eigene Bewertung),
oder es ist eine Klasse (dann eine eigene). **Nicht entschieden.**

---

## Die Reihenfolge, die ich vorschlage

| # | Schritt | Warum zuerst |
|---|---|---|
| **1** | **CoinGecko gegen Binance messen** — liefern Preisreihe und 4-h-OHLC dieselben Werte wie die aggregierten? | Ohne das sind die 67 % und 65 % **Annahmen**. Messbar an den 28 Symbolen, die beides haben |
| **2** | **Stammsatz bauen** (2.614: `bitpanda_katalog` ist die halbe Miete) | Ohne ihn entscheidet Namensgleichheit still, welches Asset Daten bekommt |
| **3** | **Lader auf den Stammsatz umstellen** | Behebt nebenbei den Spot/Futures-Fehler (2.611) |
| **4** | **Stufe als Feld** in die Bewertung | Erst wenn 1–3 stehen, hat sie einen Wert |

⚠️ **Schritt 1 ist keine Formalie.** Fällt er negativ aus, sind die
Stufen 2 und 3 nicht das, wofür ich sie halte — und der Fallback müsste
über eine andere Quelle laufen.

## Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Nichts davon ist gebaut** — Entwurf zur Abstimmung |
| **2** | Die **Hebelhöhe** bleibt gesperrt (2.609: Median negativ, Verteilung schief) |
| **3** | Warum das **höchste ATR-Fünftel** nicht trägt, ist offen (2.617) |
| **4** | Ob BTC eine **eigene Bewertung** braucht, ist **nicht entschieden** |
| **5** | Nichts über **Short** |
