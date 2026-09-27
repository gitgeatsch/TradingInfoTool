# Voranalyse — Stundendaten in den Betrieb

**27.09.2026** · vor dem Bau · Nutzerfrage *„ich dachte wir brauchen
nicht alle Stundendaten in der Produktion, jetzt doch?"*

---

# ⭐ Die Nutzerfrage war berechtigt — meine Schätzung war falsch

Ich hatte *„rund 1 Mio Zeilen pro Jahr"* geschrieben. Das unterstellt,
dass die **Historie** in den Betrieb muss. Sie muss nicht.

> **Der Betrieb braucht nur so viel Vergangenheit, wie die Berechnung des
> AKTUELLEN Werts verlangt — ein rollendes Fenster.**

## Und wie groß es sein muss, ist gemessen, nicht geschätzt

Für jedes Fenster `F` wurde EMA und ATR `F` Stunden **vor** dem Anker neu
gestartet und mit dem Wert aus voller Historie verglichen:

| Fenster | Auswahl identisch | mittlere Abweichung | 90. Perzentil | Korrelation |
|---|---|---|---|---|
| 1 Tag | 63,8 % | 0,1192 | 0,2494 | 0,9329 |
| 2 Tage | 78,3 % | 0,0468 | 0,1008 | 0,9873 |
| 3 Tage | 93,5 % | 0,0181 | 0,0390 | 0,9980 |
| 5 Tage | 98,6 % | 0,0025 | 0,0054 | 1,0000 |
| **7 Tage** | **100,0 %** | **0,0003** | 0,0007 | 1,0000 |
| 14 Tage | 100,0 % | 0,0000 | 0,0000 | 1,0000 |

⭐ **7 Tage reichen vollständig.** Das deckt sich mit der Theorie: der
Resteinfluss des Startwerts ist `(1 − 2/49)^F`, nach 168 Stunden noch
0,00091.

## Die tatsächliche Datenmenge

| | |
|---|---|
| 44 Kryptowerte × 24 h × **14 Tage** (7 + Puffer) | **rund 15.000 Zeilen** |
| zum Vergleich: `price_history_ohlc` heute | 116.644 Zeilen |
| Wachstum | **keines** — das Fenster rollt |

➤ **Rund ein Achtel dessen, was schon da ist.** Nicht 1 Mio.

---

# ⭐ Das Muster existiert im Projekt bereits

`baue_nb_umlaufmenge.py` macht seit dem 22.09. genau das für
`umlaufmenge_cg.db`:

| | |
|---|---|
| `TAGE = 14` | dieselbe Fenstergröße |
| Markertabelle **`_nur_betrieb`** | die Datei sagt selbst, dass sie keine Messbasis ist |
| Riegel im **Messleser** | `lade_reihen_aus_db` bricht ab — dort gehen 32 Messskripte durch |
| Desktop | volle Historie, 8,3 MB |
| Notebook | Betriebskopie, 368 KB |

⚠️ **Die stehende Regel gilt:** *Betriebskopie ist keine Messbasis.* Die
volle `stundenkurse.db` bleibt am **Desktop** und ist weiterhin die
Messbasis; der Betrieb bekommt **nur** das rollende Fenster, und zwar
mit derselben Marke und demselben Riegel.

---

# ⚠️ Die Abdeckungslücke — 16 von 44

| Quelle | Symbole | belegt durch |
|---|---|---|
| **Binance** (`interval=1h`) | **28 von 44** (64 %) | vorhanden in `stundenkurse.db` |
| **CoinGecko** (`market_chart`, stündlich bei `days` 2–90) | die restlichen **16** | 2.613 (Preisreihe für 15 von 15) · 2.618 (Bewertung trägt) |

**Ohne Stundendaten:** AIOZ, AKT, ASTER, BRETT, CANTON, CAT, EURCV,
FLOKI, GRIFFAIN, HYPE, KAS, MON, PLUME, SUPRA, VSN, XNO

⭐ **Die Lücke ist kein Rangproblem.** `ema_abstand_atr` ist eine
**absolute** Schwelle, kein Perzentil — die Grundgesamtheit verschiebt
die Werte der anderen nicht (das war der Grund, warum die Schwelle
absolut sein sollte). Die 16 bekämen schlicht **kein Hebelsignal**,
solange sie keine Stundendaten haben.

⚠️ Für CoinGecko gilt die **Stufe D** aus 2.616: ATR-Ersatz aus
mittlerer absoluter Stundenrendite × √24, **ohne** High/Low — gemessen
so gut wie grobes OHLC.

---

# Der Bauweg

| # | Schritt | Ort |
|---|---|---|
| **1** | Tabelle mit Stundenschlüssel + Marke `_nur_betrieb` | `database/models.py`, `database/db.py` |
| **2** | Binance-Lader `interval=1h`, 14-Tage-Fenster | `api/boersen_klines.py` (heute `interval: "1d"`, Z. 85) |
| **3** | CoinGecko-Lader für die 16 | `api/coingecko.py` bzw. neuer Fallback |
| **4** | Pruning: alles älter als 14 Tage löschen | im Lader |
| **5** | Job im Scheduler, **stündlich** | `scheduler/background.py`, Muster der bestehenden Intervall-Jobs mit Backoff |
| **6** | Frischeprüfung | `agent/datenfrische.py` |
| **7** | Riegel im Messleser | analog `lade_reihen_aus_db` |

⚠️ **Erst danach** kommt der eigentliche Schritt 1 (`marktrang.py` →
`wahrscheinlichkeit.py` → `rollen_lauf.py`).

## Leser und Schreiber

| Rolle | heute |
|---|---|
| Schreiber Tageskerzen | `api/boersen_klines.py` ← `scheduler/background.py` |
| Leser der Kurse | `agent/marktrang.py` (`price_history`, `price_history_ohlc`) |
| ⚠️ **Niemand** liest `stundenkurse.db` | bestätigt, null Treffer |

---

# Risiken

| # | Risiko | Gegenmittel |
|---|---|---|
| **1** | ⚠️ **CoinGecko-Kontingent** — der Betrieb nutzt es schon; 16 Symbole stündlich kommen dazu. Free Tier: 30 Anfragen/Minute | stündlich sind 16 Anfragen trivial, aber der bestehende Quota-Wächter (`COINGECKO_QUOTA_CHECK_INTERVAL_MINUTES`) muss sie kennen |
| **2** | **Binance-Erreichbarkeit vom Notebook** — ungeprüft, ob dort dieselben Endpunkte offen sind | vor dem Bau am Notebook prüfen |
| **3** | ⚠️ **Die 16 ohne Daten** bekommen kein Hebelsignal — darunter gehaltene Werte (ASTER, CANTON, MON) | bewusst entscheiden, nicht stillschweigend |
| **4** | **Betriebskopie darf nicht als Messbasis gelesen werden** | Marke `_nur_betrieb` + Riegel im Helfer, **nicht** in einer Textsuche (stehende Regel) |
| **5** | **Ein neuer stündlicher Job** im 24/7-Betrieb | Backoff-Muster der bestehenden Jobs übernehmen |
| **6** | ⚠️ Die Messung lief auf **Binance USDT**; CoinGecko liefert **USD** | 2.618 hat das gemessen (ATR-Verhältnis 0,9886) — aber nur auf 27 Symbolen und 90 Tagen |
| **7** | **Zeitzone** — Stundenschlüssel muss UTC sein, wie in der Messbasis | `%Y-%m-%d %H:00`; ein Formatfehler hat am 26.09. schon einmal still null Treffer erzeugt |

---

# ➤ Was offen ist, bevor gebaut wird

| # | |
|---|---|
| **1** | **Alle 44 oder nur die 28?** Mit Binance allein wäre der Bau deutlich kleiner — die 16 kämen später nach |
| **2** | ⚠️ **Der Horizont-Widerspruch** ist weiterhin offen: gemessen H24, Messnorm 3 Tage, real 0,30 Tage. Er ändert nichts an der Datenfrage, aber an dem, was die Bewertung beschreibt |
| **3** | Der **Tageszeiteffekt** aus 2.635 (Nullband −1,67 gegen +1,92) ist unerklärt |
