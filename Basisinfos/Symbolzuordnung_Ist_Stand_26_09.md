# Die Symbolzuordnung — Ist-Stand und was für den Stammsatz fehlt

**26.09.2026** · Befunde 2.612, 2.613, 2.614 · Voranalyse, **nichts gebaut**

> **Nutzerbefund:** *„Es müssen Bitpanda Symbole mit den Datenquellen —
> binance, Coingecko etc sauber zusammengeführt werden sonst können wir
> auch keine neuen Assets ohne probleme aufnehmen."*

---

## ⭐⭐ Der halbe Stammsatz existiert schon

```sql
CREATE TABLE bitpanda_katalog (
    asset_id TEXT PRIMARY KEY,   -- ⭐ der stabile Schlüssel
    symbol   TEXT NOT NULL,
    name     TEXT,
    gruppe   TEXT,
    isin     TEXT,
    geholt_am TEXT NOT NULL)
```

| | |
|---|---|
| **Quelle** | `api.public.bitpanda.com/v1/assets` (die **neue** Schnittstelle) |
| **Umfang** | 14.052 Einträge über 141 Seiten |
| **Takt** | höchstens einmal täglich (`KATALOG_HOECHSTALTER_STUNDEN = 24`) |
| **Aufrufer im Betrieb** | **eine** Stelle: `importer/bitpanda_bestand.py:276` |
| **Angelegt** | 16.09.2026, Schritt 61 Stufe 1.1 |

⭐⭐ **Sein Docstring benennt exakt das Problem aus 2.612:**

> *„DER SCHLÜSSEL IST `asset_id`, NICHT DAS SYMBOL: **1.625 Symbole
> kommen im Katalog mehrfach vor** (ROL steht als Aktie zweimal, in alter
> und neuer Gruppe)."*

➤ **Die stabile ID ist bereits da** — sie wird nur für den
Bestandsabgleich genutzt, nicht als Anker für die Datenquellen. Eine
**ISIN** führt der Katalog ebenfalls.

✔✔ **NACHGEZOGEN am selben Tag, gegen das Produktionsbackup** (Nutzerhinweis
*„du hast ein DB backup und den NB export oder?"*): **Der Katalog ist am
Notebook gefüllt** — 14.054 Einträge, Stand 22.09. 19:57, Abgleich 23.09.
01:57. Am Desktop existiert die Tabelle nicht, weil der Importer hier nie
lief. Einzelheiten im Abschnitt **„Was das Produktionsbackup zeigt"**.

⚠️ Das war genau der Fehler, vor dem die eigene Regel warnt: *„Nicht
messbar ist keine Datenlage — die Produktionssicherung liegt im
Austauschordner, VOR dem Satz nachsehen."* Beide Quellen lagen bereit.

---

## Das Listungsfeld — ein Laufzeitwert, kein Stammdatum

| | |
|---|---|
| **Berechnet** | je Lauf über `is_listed(symbol, bitpanda_assets, name=…)` gegen die frisch geholte Assetliste |
| **Wo** | `agent/aktien/pipeline.py:263` · `agent/hedge/pipeline.py:770` · `agent/krypto/marktscan.py:555` |
| **Persistiert** | nur in `marktscan_candidates.bitpanda_gelistet` |
| **Dauerhaft in der DB** | allein die **Ausnahme**: `asset_bitpanda_override.bitpanda_gelistet_override` — derzeit **0 Zeilen** |
| **Zentrale Auswertung** | `agent/asset_schalter.ist_handelbar` (Zeile 178) |

Die beiden Regeln dort sind bewusst gesetzt und bleiben:

| | |
|---|---|
| **Der Override schlägt das Listing** | *„die Listing-Abfrage kennt nicht jeden Sonderfall, der Nutzer schon"* |
| **`None` gilt als handelbar** | *„Eine Empfehlung wegen einer fehlgeschlagenen API-Abfrage zu unterdrücken wäre ein stiller Ausfall"* |

---

## Die vier Brücken, die es gibt — alle hartkodiert oder verstreut

| Brücke | Ort | Umfang |
|---|---|---|
| `BITPANDA_SYMBOL_OVERRIDES` | `api/bitpanda.py:54` | **genau 1 Eintrag**: `CANTON → CC` |
| `BITPANDA_NON_CRYPTO_WALLET_SYMBOL_OVERRIDES` | `api/bitpanda.py:290` | Aktien/ETF |
| `KRAKEN_FUTURES_SYMBOL_MAP` | `api/kraken.py:95` | ~17+ Paare, **nur Kraken** |
| `coingecko_id` | `price_cache`, `price_history`, `marktscan_candidates` | 74 %, **drei Tabellen** |
| **Binance Spot / Futures** | — | ⛔ **nichts** |

⚠️⚠️ **Und der eine vorhandene Override wird nicht befahren.**
`CANTON → CC` steht seit dem 09.07. im Code. Geprüft: **weder unter
`CANTON` noch unter `CC`** gibt es einen einzigen Kurspunkt in einer der
vier Kursdatenbanken. Der Override wirkt auf die **Listungsprüfung**,
nicht auf die **Kursbeschaffung**.

---

## ⭐⭐⭐ CANTON hat Kursdaten — meine Aussage war falsch

⛔ Ich hatte „null Kursdaten in jeder Quelle" gemeldet und dabei **nur die
eigenen Datenbanken** durchsucht, nicht die Quelle.

**Live geprüft am 26.09.:**

| | |
|---|---|
| CoinGecko-ID `canton-network` | ✔ gültig · Name **Canton** · Symbol **CC** |
| Kurs | 0,1359 USD |
| **Marktkapitalisierung** | **5,39 Mrd USD** |
| Volumen 24 h | **56,8 Mio USD** |
| erste Daten | 2026-06-28 (rund drei Monate) |
| Binance Spot | ⛔ **nicht handelbar** — daher keine Stundenkurse |

➤ Es ist kein Kleinstwert, sondern ein **hochliquider, gehaltener
Kernwert**, für den Daten frei verfügbar sind.

### ⚠️⚠️⚠️ Was CoinGecko liefert — und was NICHT

⛔ **Vor dem Commit selbst bemerkt, deshalb steht es hier vorn:**
`market_chart` liefert **Preispunkte, kein OHLC**. Die Bewertung braucht
**ATR**, also **High und Low**.

| Endpunkt | `days=30` | Auflösung |
|---|---|---|
| `market_chart` | 2.160 Punkte (bei 90 Tagen) | **stündlich**, aber nur **ein** Preis |
| `…/ohlc` | **180 Kerzen** | ⛔ **4 Stunden** (30 × 24 / 180 = 4) |

➤ Die Zahl 2.160 gilt für eine Reihe, aus der sich **EMA und Momentum**
rechnen lassen — **nicht für die ATR**. Was tatsächlich in stündlicher
OHLC-Auflösung zu bekommen ist, ist **ungeprüft**, und davon hängt ab, ob
die Lücke über CoinGecko überhaupt schließbar ist.

### Was der Vergleich trotzdem zeigt

`market_chart?days=90` liefert **2.160 Preispunkte** — also **stündliche
Auflösung**. Das ist keine Eigenschaft des Coins, sondern der
Schnittstelle: CoinGecko gibt bei `days` zwischen 2 und 90 grundsätzlich
Stundenwerte.

| | Stunden |
|---|---|
| Bedarf der Bewertung (2.610) | **240** |
| CoinGecko liefert | **2.160** |
| Verhältnis | **9×** |

**Stichprobe, alle mit 2.160–2.161 Punkten:**

| Symbol | CoinGecko-ID | Punkte | Marktkap. |
|---|---|---|---|
| CANTON | `canton-network` | 2.160 | 5.393 Mio |
| ASTER | `aster-2` | 2.160 | 1.984 Mio |
| AKT | `akash-network` | 2.161 | 210 Mio |
| AIOZ | `aioz-network` | 2.161 | 157 Mio |

⛔⛔ **Zwei Einschränkungen, die dazugehören:**

| # | |
|---|---|
| **1** | Die Stichprobe umfasst **vier** Symbole, nicht 15. Der Lauf brach bei **HTTP 429** ab — ich hatte mit rund 27 Anfragen/Minute zu nah an der Grenze gearbeitet, und **das Kontingent gehört dem laufenden Betrieb**. Die übrigen elf sind **nicht geprüft** |
| **2** | **XNO hat keine CoinGecko-ID** — trotz 1.665 Tageskursen in der Datenbank. Ein echter Sonderfall |

⚠️ **90 Tage sind ein rollendes Fenster.** Für die **Messung** taugt das
nicht, für die **Anwendung** (10 Tage Bedarf) reicht es neunfach — genau
die Trennung aus 2.610.

---

---

## ⭐⭐⭐ Was das Produktionsbackup zeigt (2.615)

Gemessen gegen `DB_Backups/tradinginfotool_2026-09-23_0221.db.gz`
(561 MB entpackt) — ⚠️ **in einer Wegwerfdatei im Scratchpad, mit
`mode=ro`, nie gegen die Produktionsdatei**, und nach der Messung
gelöscht.

### Alle 15 „Fehlenden" stehen im Katalog — jedes mit `asset_id`

| Ticker | `asset_id` | Name | Gruppe |
|---|---|---|---|
| **CC** | `1f0c940a-db04-…` | **Canton** | token |
| ASTER | `1f097a29-a969-…` | Aster | token |
| MON | `1f0c9240-9c4f-…` | Monad | token |
| **XNO** | `050e9adf-d825-…` | **Nano** | coin |
| AIOZ, AKT, BRETT, FLOKI, GRIFFAIN, HYPE, KAS, PLUME, SUPRA, VSN | | alle vorhanden | |

⭐ **CANTON gibt es im Katalog nicht** — Bitpanda führt **CC**, genau wie
der Override seit dem 09.07. sagt. ⭐ **XNO heißt „Nano"** — daher fehlte
die CoinGecko-ID unter dem Ticker; die ID ist schlicht `nano`.

### Die Mehrdeutigkeit — gemessen, nicht behauptet

| | |
|---|---|
| Symbole im Katalog | 12.402 |
| davon **mehrdeutig** | **1.625** |
| relevante Symbole (gehalten oder Watchlist) | 48 |
| ⛔ davon **mehrdeutig** | **11** — davon **5 gehalten** |

| Ticker | Bedeutung 1 | Bedeutung 2 (und 3) |
|---|---|---|
| **ETH** *(gehalten)* | Ethereum *(coin)* | **Eurotech SpA** *(equity_stock)* |
| **LINK** *(gehalten)* | Chainlink *(coin)* | **LINK Mobility Group** *(equity_stock)* |
| **QNT** *(gehalten)* | Quant *(token)* | **Quantinuum Inc** *(equity_stock)* |
| **BIO** *(gehalten)* | Bio Protocol *(token)* | **Bio-Rad Laboratories** *(stock)* |
| **CAT** | Simon's Cat *(token)* | Caterpillar Inc · Caterpillar |
| **HYPE** | Hyperliquid *(coin)* | iShares EUR High Yield Corp Bond ETF |
| BNB, SUI, ALGO, SEI, ROL | | |

### ✔✔ Und die Entwarnung — weil gemessen statt gewarnt

**Alle elf sind in `price_cache` korrekt aufgelöst.** ETH → `ethereum`
(1.790,56 USD), LINK → `chainlink` (7,99), CAT → `simon-s-cat`,
QNT → `quant-network`. **Keine einzige Fehlzuordnung.**

➤ **Die Gefahr ist latent, nicht akut.** Der Bestand stimmt. Aber bei
einer **Neuaufnahme** entscheidet niemand ausdrücklich, welches der
gleichnamigen Assets gemeint ist — und `holdings` führt **nur `symbol`**,
keine `asset_id`. Die Auflösung passiert beim Import und wird **nicht
festgehalten**.

---

## ⭐⭐ Was CoinGecko wirklich liefert — alle 15 geprüft

⚠️ **Korrektur meiner eigenen Warnung:** Der erste Lauf lief **ohne
Schlüssel** direkt über `urllib` und traf das **anonyme** Limit
(30/Minute). Das Projekt hat einen Demo-Key (`COINGECKO_API_KEY`,
`x-cg-demo-api-key`, **100/Minute**), und die Betriebszählung ist
**monatlich** (4.113 im September). **Das Projektkontingent blieb
unberührt** — meine Warnung war falsch.

Mit Schlüssel nachgezogen, **alle 15**:

| | Ergebnis |
|---|---|
| **Stündliche Preisreihe** (`market_chart?days=90`) | ✔ **15 von 15**, je 2.160–2.161 Punkte |
| **OHLC** (`ohlc?days=30`) | ⛔ **180 Kerzen bei allen** = durchgängig **4-Stunden-Takt** |

➤ Das ist keine Eigenheit einzelner Werte, sondern **die Regel der
Schnittstelle**.

⚠️⚠️ **Die Bilanz:** Die **Preisreihe reicht** — daraus lassen sich EMA
und Momentum rechnen. Das **OHLC reicht nicht** in der Auflösung der
Messbasis, und die **ATR braucht High/Low**.

➤ **Die offene Messfrage:** Ist eine ATR aus **4-Stunden-Kerzen** mit der
aus **1-Stunden-Kerzen** vergleichbar? Das ist **messbar** — an den 28
Symbolen, die **beide** Auflösungen haben. Bevor eine zweite Stundenquelle
dazukommt, ist das zu klären: eine gemischte Auflösung ist eine gemischte
Grundgesamtheit.

---

## Was der Stammsatz bräuchte

| Feld | Woher |
|---|---|
| `asset_id` (PK) | ✔ **existiert** — `bitpanda_katalog` |
| `symbol_bitpanda`, `name`, `gruppe`, `isin` | ✔ **existiert** |
| `symbol_intern` | aus `config.yaml`, plus `BITPANDA_SYMBOL_OVERRIDES` |
| `coingecko_id` | aus den drei vorhandenen Tabellen zusammenziehen (74 %) |
| `binance_spot` | ⛔ **neu** — gegen `api/v3/exchangeInfo` auflösen |
| `binance_futures` | ⛔ **neu** — gegen `fapi/v1/exchangeInfo` auflösen |
| `kraken_futures` | aus `KRAKEN_FUTURES_SYMBOL_MAP` |

➤ Die drei hartkodierten Maps würden zu **Startdaten**, nicht zu Code.

## Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Nichts davon ist gebaut.** Das ist eine Voranalyse |
| **2** | ✔ **ERLEDIGT** - alle 15 geprüft: Preisreihe ja, OHLC nur im 4-Stunden-Takt |
| **3** | ✔ **ERLEDIGT** - der Katalog ist am Notebook gefüllt (14.054 Einträge, Stand 22.09.) |
| **4** | Eine zweite Stundenquelle neben Binance ändert die **Grundgesamtheit** der Messbasis — das ist nach der stehenden Regel **zu messen**, bevor sie dazukommt |
| **5** | ⛔ **Der Kernpunkt:** CoinGecko-Stundenkurse sind **nicht OHLC** — `market_chart` liefert nur Preispunkte, und `…/ohlc` gibt bei allen 15 nur **4-Stunden-Kerzen**. Die ATR braucht High/Low. ➤ **Offene Messfrage:** ist eine ATR aus 4-h-Kerzen mit der aus 1-h-Kerzen vergleichbar? Messbar an den 28 Symbolen, die beide Auflösungen haben |
| **6** | ⚠️ Die Mehrdeutigkeit ist **latent**, nicht akut — alle 11 sind heute korrekt aufgelöst. Das Risiko liegt in der **Neuaufnahme**, nicht im Bestand |
