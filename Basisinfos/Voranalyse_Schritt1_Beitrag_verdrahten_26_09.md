# Voranalyse Schritt 1 — den Hebel-Beitrag verdrahten

**26.09.2026** · vor dem Bau · Nutzerauftrag *„mit Schritt 1 beginnen —
Voranalyse zuerst prüfen und gegenprüfen"*

> **Vorhaben:** `ema_abstand_atr` in `marktrang.py` berechnen, in
> `wahrscheinlichkeit.py` mit `instrumente=("hebel",)` registrieren, in
> `rollen_lauf.py:2195` in die Merkmalsliste aufnehmen.

---

# ⛔⛔⛔ Der Showstopper: der Betrieb hat keine Stundendaten

| | |
|---|---|
| **Gemessen wurde auf** | `data/stundenkurse.db` — 116 Symbole, **stündliche** Kerzen, EMA über **48 Stunden**, ATR aus Stundenspannen |
| **Der Betrieb hat** | `price_history` und `price_history_ohlc`, beide mit `date` als `YYYY-MM-DD` — **Tagesauflösung** |
| **Liest der Betrieb `stundenkurse.db`?** | ⛔ **Nein.** Volltextsuche über `agent/`, `scheduler/`, `database/`, `api/`, `indicators/`, `ui/`, `monitor/` — **null Treffer** |
| **Gibt es irgendeine stündliche Kursreihe?** | ⛔ **Nein.** Alle 31 Tabellen der Produktions-DB geprüft: die einzigen feineren Zeitstempel sind Abrufstempel (`discovered_at`, `screened_at`, …), keine Kursreihe |

⭐ `OhlcPoint` ist ausdrücklich *„echte **Tages**kerze von Kraken"*,
`date: 'YYYY-MM-DD', UTC-Tagesbucket` (`database/models.py:683`).
`api/boersen_klines.py:85` ruft Binance mit `"interval": "1d"`.

## ⚠️ Und 2.616 beantwortet das NICHT — gegengeprüft

2.616 (*„die Bewertung überlebt eine gröbere Auflösung"*) sieht so aus,
als wäre die Frage geklärt. Ist sie nicht. Im Quelltext von
`messe_aufloesung_und_fallback.py`:

| Zeile | was dort steht | Folge |
|---|---|---|
| `:217` | `e = ema(cc, EMA_L)` mit `EMA_L = 48` | die EMA läuft auf den **stündlichen** Schlusskursen |
| `:130-134` | die grobe ATR wird *„zurück auf Stunden, kausal versetzt"* | das Raster bleibt **stündlich** |
| `:222` | `gu[:VORLAUF] = False`, `VORLAUF = 240` | 240 **Stunden** Vorlauf, Anker = jede Stunde |

➤ **Gröber wurden nur die Kerzen (High/Low/Close), nicht die Anker und
nicht die EMA.** Die Messung sagt: *wenn die ATR aus 4-h- oder
Tageskerzen kommt, trägt die Bewertung noch* — sie sagt **nicht**, dass
sie mit einem Anker pro Tag und einer Tages-EMA trägt.

⚠️ Dasselbe gilt für 2.618 (CoinGecko): dort wurden `market_chart`-Daten
im **Stundenraster** verglichen (Schlüssel `%Y-%m-%d %H:00`).

---

# ⭐ Zweiter Fund: die Sperre ist KEIN Versehen

Mein Befund 2.634 sagt, die Instrumenttrennung verhindere den Hebel. Das
stimmt — aber der **Grund ist richtig**, und das steht im Code:

> *„K2 (24.09.2026): **die Lage, auf der dieser Beitrag gemessen wurde —
> und nur sie.** Bis heute stand hier nichts, und `instrumente=()` heißt
> ‚gilt überall'. Damit erbte die Hebelquote diesen Beitrag automatisch
> mit — nicht durch eine Entscheidung, sondern durch einen Vorgabewert.
> Gemessen wurde er auf H20 und `bewegung_r`, also auf der **Spot**-Lage;
> der Hebel hält im Median 0,30 Tage und wird auf `barriere` beurteilt."*
> — `agent/wahrscheinlichkeit.py:412-428`

⭐ **Die Sperre ist also korrekt.** Was fehlt, ist nicht ihre Aufhebung,
sondern ein **Ersatz**: der erste Beitrag, der auf der **Hebel**-Lage
gemessen wurde. Genau das soll `ema_abstand_atr` sein.

⚠️ **2.634 ist in diesem Punkt zu scharf formuliert** und gehört
präzisiert: nicht *„die Trennung verhindert den Hebel"*, sondern *„die
Trennung hat die geerbten Beiträge korrekt entzogen, und es kam nie
einer nach"*.

---

# ⚠️ Dritter Fund: der Horizont widerspricht sich dreifach

| Quelle | Wert |
|---|---|
| **gemessen** (2.628, 2.630–2.633) | **H24** = 1 Tag |
| **Messnorm** `messnorm.py:226` `("hebel","einstieg")` | **3 Tage** |
| **real** (2.493) | Median **0,30 Tage** |

⚠️ Drei Zahlen für dieselbe Größe. Vor dem Bau zu klären — sonst
beschreibt die Bewertung einen anderen Trade als den, der läuft.

---

# Der Bauweg selbst — falls die Datenfrage geklärt ist

## Die Struktur steht bereit

`agent/wahrscheinlichkeit.py:85` `class Beitrag` kennt zwei Bauformen:

| Bauform | wann |
|---|---|
| **Schalter** | `punkte` gesetzt, `stufen` leer — trifft zu oder nicht |
| **Abgestuft** | `stufen` gesetzt (ein Wert je Fünftel), `punkte` bleibt 0,0 |

➤ `ema_abstand_atr` wäre **abgestuft**, wie Funding und Turnover:

```python
Beitrag(
    name="Abstand zur eigenen EMA, in ATR",
    zustand="traegt", punkte=0.0, merkmal="ema_abstand_fuenftel",
    stufen=(...), klammer="tag",
    instrumente=("hebel",),        # <- der Kern
    strategien=("einstieg",), klassen=("krypto",))
```

⚠️ **Die `stufen` fehlen noch.** Gemessen ist eine **Schwelle**
(W ≤ −1,2881), kein Fünftel-Profil. Die Umsetzung in fünf Stufenwerte ist
eine eigene Ableitung — und genau dort lauert wieder die Falle der
gesetzten Grenzen.

## Leser und Schreiber

| Rolle | Ort |
|---|---|
| **Schreiber** der Merkmale | `agent/marktrang.py:1242 ff.` — baut `marktraenge[symbol]` |
| **Leser** für den Hebel | `agent/rollen_lauf.py:2195-2198` — **hart aufgezählte** Liste |
| **Leser** für Spot | `agent/rollen_lauf.py:2603-2606` — zweite, getrennte Liste |
| Verbraucher | `agent/wahrscheinlichkeit.py:754 rechne()` → `agent/potential.py:380` |
| Nachgelagert | `agent/betraege.py:322 hebelrechnung()` |

⚠️ **Zwei hart aufgezählte Merkmalslisten** (`:2195` und `:2603`) — wer
nur eine ändert, erzeugt einen stillen Unterschied zwischen Hebel und
Spot.

## Risiken

| # | Risiko | Gegenmittel |
|---|---|---|
| **1** | ⛔ **Datenlage** — ohne Stundendaten ist die gemessene Größe nicht baubar | vor dem Bau zu entscheiden (siehe unten) |
| **2** | `erreichbar_max` in `agent/potential.py` ändert sich, wenn ein Beitrag dazukommt → **die wirksame Bewertungsschwelle verschiebt sich, auch für Spot** | vorher rechnen, nicht nachher messen |
| **3** | Die Fünftel-Stufen sind eine **neue Ableitung** aus einer Schwellenmessung | eigene Vorabfestlegung, keine gesetzten Grenzen |
| **4** | Die zweite Merkmalsliste (`:2603`, Spot) darf sich **nicht** mitändern | getrennt prüfen, Bitgleichheitstest auf der Spot-Quote |
| **5** | `marktrang.py` müsste eine **neue Datenquelle** anbinden | eigener Schritt, nicht mit der Registrierung vermischen |
| **6** | Signalmenge 3,2–11,7/Tag **ohne Deckel** | Schritt 3 des Bauplans, vor Produktivgang |

---

# ➤ Die Entscheidung, die vor dem Bau steht

| Weg | was zu tun ist | Risiko |
|---|---|---|
| **A — Stundendaten in den Betrieb holen** | `boersen_klines.py` von `interval=1d` auf `1h`, neue Tabelle mit Stundenschlüssel, Lader im Scheduler. Dann bleibt **jede** Messung von heute 1:1 gültig | Datenmenge (~1 Mio Zeilen/Jahr für 116 Symbole), neuer Lader, neue Frischeprüfung |
| **B — auf Tagesbasis neu messen** | dieselbe Achse mit **einem Anker pro Tag**, Tages-EMA und Tages-ATR. Ergebnis offen — 2.616 Stufe C verlor bereits 49 % bei bloß gröberen Kerzen | eine weitere Messung; bei negativem Ausgang war der ganze Tag umsonst |
| **C — erst B messen, dann entscheiden** | eine Messung (~15 min) beantwortet, **ob** A nötig ist | die Messung selbst |

⭐ **Empfehlung: C.** Weg B ist keine Ausweichmessung — er beantwortet
genau die Frage, die über den Bauumfang entscheidet. Fällt er positiv
aus, ist Schritt 1 klein. Fällt er negativ aus, ist A unvermeidlich und
man weiß es, bevor Code entsteht.

⚠️ **Ohne diese Klärung ist Schritt 1 nicht baubar** — man würde ein
Merkmal registrieren, das im Betrieb nicht berechenbar ist.
