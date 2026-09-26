# Voranalyse Stammsatz — was da ist, was fehlt, wer führt

**26.09.2026** · Nutzerauftrag: *„Stammsatz bauen - Voranalyse zuerst
prüfen und gegenprüfen"* · **nichts gebaut**

Vier Nutzerfragen, alle am Code bzw. gemessen beantwortet:
*„haben coingecko und binance das gleiche format bzw. hast du
umgerechnet? … deine Zahlen zur Auswahl sind auch unterschiedlich - kann
das vernachlässigt werden - wer ist führend also primär binance? prüfe den
code ich glaube beide schienen sind bereits im code vorhanden."*

---

## Frage 1 — dasselbe Format? Habe ich umgerechnet?

⛔ **Nein, ich habe nicht umgerechnet.** Das ist ein Mangel in 2.618.

| Quelle | Paar | Währung |
|---|---|---|
| `hole_stundenkurse.py:145` | `"%sUSDT" % symbol` | **USDT** |
| CoinGecko `market_chart` | `vs_currency=usd` | **USD** |

**Gemessen** (Tether über dieselben 90 Tage, 2.161 Stundenwerte):

| | |
|---|---|
| Median | **0,999387** USD |
| Spanne | 0,998507 – 1,000243 |
| \|Abweichung von 1,0\| | **0,0613 %** (Median) · 0,0912 % (90. Perzentil) |
| Anteil an den gemessenen 0,3913 % | **0,06 von 0,39 Pp — 16 %** |

⭐⭐ **Und der wichtigere Teil: für die Bewertung ist die Währung fast
irrelevant**, weil das Merkmal **skaleninvariant** ist:

```
ema_abstand_atr = (close − EMA(close)) / (ATR × close)
```

Ein **konstanter** Umrechnungsfaktor kürzt sich hier vollständig heraus —
Zähler und Nenner tragen ihn gleichermaßen. Übrig bleibt nur die
**Schwankung** des Faktors, und die liegt bei 0,06 %.

➤ **Vernachlässigbar — aber es gehört in den Stammsatz als Feld
`waehrung`**, damit niemand später USDT- und USD-Reihen ohne Vermerk
nebeneinanderlegt. Genau das ist am 03.08. mit den Vier-Tage-Kerzen
passiert (siehe Frage 4).

---

## Frage 2 — die unterschiedlichen Auswahlzahlen

Überlappung der Auswahl: **66,9 %** in 2.616, **53,9 %** in 2.618. Sauber
zerlegt, **im gleichen 90-Tage-Fenster**, 56.376 Anker aus 27 Symbolen:

| Anteil | **Methode allein** *(beide aus Binance)* | **Methode + Quelle** *(2.618)* | reiner Quelleneffekt |
|---|---|---|---|
| 1 % | **69,3 %** | 53,9 % | **−15,4 Pp** |
| 2 % | 75,8 % | 61,9 % | −13,9 Pp |
| 5 % | 85,2 % | 75,4 % | −9,8 Pp |

Rangkorrelation **0,9967** (Methode) gegen **0,9413** (Methode + Quelle).

➤ Der Quelleneffekt kostet **10–15 Prozentpunkte** Überlappung. Das ist
**nicht nichts** — aber der Ertrag trägt trotzdem (2.618: alle drei
Schärfegrade über dem Nullband).

### ⭐⭐ Warum es trotzdem vernachlässigt werden kann

**Weil die Bewertung eine absolute Schwelle ist und kein Perzentil**
(2.608, Nutzerkorrektur vom selben Tag). Es gibt **keinen
Querschnittsvergleich** zwischen Symbolen — jedes wird für sich bewertet.

⚠️⚠️ **Wäre es ein Rang, wäre es ein Problem:** dann läge ein
Binance-bewertetes Symbol gegen ein CoinGecko-bewertetes in derselben
Rangliste, und der Quelleneffekt von 10–15 Pp ginge direkt in die
Reihenfolge ein. Das wäre die registrierte Regel *„Die Grundgesamtheit ist
keine Stellschraube"* — nur über die Quelle statt über die Menge.

➤ **Die Perzentil-Korrektur zahlt sich hier ein zweites Mal aus.**

---

## Frage 3 — wer ist führend?

⚠️ **Nicht Binance — und es hängt von der Schiene ab.** Beides steht schon
im Code:

| Schiene | Tabelle | Rangfolge | Auflösung | Währung |
|---|---|---|---|---|
| **Tageskerzen** | `price_history_ohlc` | **Kraken → Binance/Bybit** | 1 Tag | je Börse |
| **Stundenkurse** | `stundenkurse.db` | **nur Binance** | 1 Stunde | **USDT** |
| **Tagespreise** | `price_history` | CoinGecko | 1 Tag | USD |

> `scheduler/background.py:321`: **„DAMIT GILT DIE RANGFOLGE: Kraken →
> Binance/Bybit. Genau EINE Quelle je Symbol."**

⭐ Die Hebel-Messbasis (2.608 ff.) hängt **allein an der zweiten Schiene** —
Binance-Stundenkurse in USDT. Dort gibt es heute **keine** Rückfallquelle.

---

## Frage 4 — sind beide Schienen im Code?

✔ **Ja, und mehr als das: zwei CoinGecko-Wege sind bereits verworfen.**

| Modul | Zustand |
|---|---|
| `api/history.py` | ✔ **aktiv** — CoinGecko `market_chart`, schreibt `price_history` |
| `api/boersen_klines.py` | ✔ **aktiv** — Binance **und Bybit**, Rückfall seit 12.08. |
| `api/kraken_history.py` | ✔ **aktiv** — führend bei Tageskerzen |
| `api/coingecko_ohlc_fallback.py` | ⛔ **abgelöst 12.08.** |
| `api/yfinance_krypto_fallback.py` | ⛔ **abgelöst 11.08.** |

### ⛔⛔ Und das ändert den Fallback-Entwurf

> `api/coingecko_ohlc_fallback.py`: *„ABGELÖST AM 12.08.2026. Dieser
> Endpunkt liefert über `/ohlc` GAR KEINE Tageskerzen. Gemessen wurden
> **Vier-Tage-Kerzen**, die neben Krakens Tageskerzen in derselben Tabelle
> lagen — jeder ‚20-Tage'-Indikator rechnete dort über 80 Kalendertage."*

⚠️⚠️ **Das ist exakt das Problem, das ich heute wiederentdeckt habe** — nur
eine Ebene tiefer: 4-**Stunden**-Kerzen statt 4-**Tage**-Kerzen. **Meine
„Stufe 2" ist der Weg, der am 12.08. schon verworfen wurde**, und der
Grund steht seit sechs Wochen im Modulkopf.

➤ **Stufe 2 entfällt.** Der Fallback läuft über **Stufe 3** (Preisreihe
ohne High/Low) — die ist ohnehin fast gleichwertig (65 % gegen 67 %) und
hat die feinere Zeitachse.

⚠️ Und die Lehre ist eine registrierte: *„Alte Werkzeuge laufen lassen,
nicht nur Register lesen."* Der Befund stand im Code, nicht im Register.

---

## Der Entwurf, angepasst

```sql
CREATE TABLE asset_stamm (
    asset_id        TEXT PRIMARY KEY,   -- ✔ aus bitpanda_katalog
    symbol_intern   TEXT NOT NULL,      -- config.yaml / holdings
    symbol_bitpanda TEXT,               -- ✔ aus bitpanda_katalog (CC ≠ CANTON)
    name            TEXT,               -- ✔ vorhanden
    gruppe          TEXT,               -- ✔ vorhanden (coin/token/equity_stock…)
    isin            TEXT,               -- ✔ vorhanden
    coingecko_id    TEXT,               -- aus 3 Tabellen zusammenziehen (74 %)
    binance_spot    TEXT,               -- ⛔ NEU, gegen api/v3/exchangeInfo
    binance_futures TEXT,               -- ⛔ NEU, gegen fapi/v1/exchangeInfo
    kraken_pair     TEXT,               -- aus api/kraken.py
    kraken_futures  TEXT,               -- aus KRAKEN_FUTURES_SYMBOL_MAP
    bybit_symbol    TEXT,               -- aus api/boersen_klines.py
    waehrung_stunde TEXT,               -- ⭐ NEU: USDT bei Binance, USD bei CG
    aktiv           INTEGER,
    geprueft_am     TEXT)
```

⭐ **`waehrung_stunde` ist neu gegenüber dem ersten Entwurf** — aus Frage 1.
Vernachlässigbar für die Bewertung, aber nicht für die Nachvollziehbarkeit.

### Die Reihenfolge

| # | Schritt | Prüfung, die dazugehört |
|---|---|---|
| **1** | Tabelle anlegen, aus `bitpanda_katalog` + den drei Maps + `price_cache` befüllen | **kein Rateschritt** — nur übernehmen, was belegt ist; Lücken bleiben `NULL` |
| **2** | Binance-Paare gegen **beide** `exchangeInfo` auflösen | behebt den Spot/Futures-Fehler (2.611) |
| **3** | Suite-Prüfung: **jedes gehaltene Asset hat einen vollständigen Stammsatz** | CANTON fällt auf, bevor Kapital gebunden ist |
| **4** | Lader auf den Stammsatz umstellen | ⚠️ **erst danach** — vorher ändert sich die Grundgesamtheit der Messbasis |

⚠️⚠️ **Schritt 4 berührt die Messbasis.** Kommen Symbole hinzu, ist die
Wirkung zu messen (`messe_grundgesamtheit.py`, vier Sekunden) — die
stehende Regel gilt.

## Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Nichts gebaut** — Voranalyse zur Abstimmung |
| **2** | Ob `bitpanda_katalog` am Desktop angelegt werden soll, ist offen — heute existiert er nur am Notebook (2.615) |
| **3** | Die **Hebelhöhe** bleibt gesperrt (2.609) |
| **4** | Nichts über **Short** |
