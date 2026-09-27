# Bauplan Hebel — Stand 27.09.2026

> **Nutzerauftrag:** *„vorher alles in die Doku und Plan, damit du nichts
> vergisst"*

Dies ist die **einzige Liste**, die vor dem Bau gelesen werden muss.
Vorgänger: `Bestandsaufnahme_Hebel_26_09.md` (was baurelevant ist),
`Voranalyse_Schritt1_Beitrag_verdrahten_26_09.md`,
`Voranalyse_Stundendaten_27_09.md`.

---

# 1. Die Werte, die gebaut werden — alle gemessen

| Größe | Wert | Befund |
|---|---|---|
| **Merkmal** | `ema_abstand_atr` = `(close − EMA48h) / (ATR × close)` | 2.625/2.626 |
| **Richtung** | **invers** — niedrigster Wert ist der beste | 2.625 |
| **EMA-Länge** | **48 Stunden** (nicht 50 Tage — dort fällt MFE/MAE auf 1,00) | **2.606** |
| **Mindestschwelle Binance** | **W ≤ −1,65** — auf Streckenanfängen, erste zeitstabile; 0,42 Signale/Tag, +2,4701 % | **2.640** |
| **Mindestschwelle CoinGecko** | **W ≤ −2,20** — 0,55 strenger, sonst feuert sie 2,29× so oft bei 38,6 % weniger Ertrag; 0,29 Signale/Tag, +2,6614 % | **2.640** |
| **Hebelhöhe** | ⛔ **KONSTANT** — die Stufung nach Vierteln ist **nicht belegt** | **2.633** |
| **Horizont** | H24 ⚠️ *(Widerspruch, siehe § 4)* | 2.628 |
| **Stop** | **1,00 ATR** (auch Netto-Optimum nach Kosten) | 2.628/2.629 |
| **Trailing** | Auslöser **1,5 R**, Abstand **0,5 R** | 2.628 |
| **Deckel je Trade** | RM-11, bindet bei diesen Stopweiten nirgends (5,76–6,19×) | 2.627/2.632 |
| **Datenfenster** | **7 Tage** gemessen ausreichend (100 % gleiche Auswahl), **14 Tage** mit Puffer | **2.636** |
| **Skalenfaktor** für Quellen ohne OHLC | **2,0832** (Kehrwert 0,4800 = bekannte Methodendifferenz) | **2.637** |
| **CoinGecko-Takt** | **2 Stunden**, gebündelt über `simple/price` | 2.636/2.637 |
| **Zu ENTFERNEN** | **Z-2** (`crv_minimum` 2,0) — tautologisch | 2.623 |

## Was die Daten kosten

| | |
|---|---|
| Betriebsfenster | 44 × 24 h × 14 Tage ≈ **15.000 Zeilen**, rollend konstant |
| Binance | 28 Symbole, kein Schlüssel, Gewicht 2 bei Limit 1.200/min, **am NB belegt erreichbar** |
| CoinGecko | 16 Symbole, gebündelt alle 2 h = +12 Anfragen/Tag → **62 %** Auslastung (heute 58 %) |

---

# 2. Die Reihenfolge — sie ist zwingend

| # | Schritt | warum hier |
|---|---|---|
| **0** | **Depot-Simulation** A gegen D-korrigiert | ⭐ *läuft gerade* — wie weit weichen die Ergebnisse ab, mit Kapazitätsgrenze und über die Zeit |
| **1** | **Stundendaten in den Betrieb**: Tabelle mit Marke `_nur_betrieb`, Binance-Lader (`interval=1h`), CoinGecko-Lader gebündelt, Pruning 14 Tage, stündlicher Job, Frischeprüfung, **Riegel im Messleser** | Ohne sie ist alles Weitere wirkungslos — auf Tagesbasis trägt die Achse **nicht** (2.635) |
| **2** | **Beitrag verdrahten**: `marktrang.py` rechnet `ema_abstand_atr` → `wahrscheinlichkeit.py` registriert ihn mit **`instrumente=("hebel",)`** → `rollen_lauf.py:2195` nimmt ihn auf | **Ohne ihn bleibt Kelly exakt 0,0** (2.634) |
| **3** | **Geometrie nachziehen** (Stop, Trailing, Horizont) | ⚠️ **getrennt halten** — der Stop sitzt in `entscheidungsrechnung.py:93` und wirkt **auch auf Spot** |
| **4** | **Signalmenge deckeln** | 3,2–11,7/Tag, heute ohne Grenze (2.633) |
| **5** | **Z-2 entfernen** | tautologisch (2.623) |
| **6** | **Prüftakt und Cooldown** prüfen | Nutzervorgabe: vor dem Produktivgang wichtig |

## ⛔⛔⛔ Zwei Befunde vom 27.09. abends, die vor allem anderen stehen

| | |
|---|---|
| **2.638** | **Der Betrieb kauft den Streckenanfang, die Messung mittelt die ganze Strecke.** Ein Symbol liegt im Schnitt 3,4 Stunden am Stück unter der Schwelle; nur 29,1 % der Anker sind Anfänge. Anfänge +0,3393 %, übrige +1,6334 % — Faktor 4,8. ✔ Die **Trennschärfe bleibt** (+2,78 gegen +2,83), nur der absolute Ertrag fällt. ⚠ **Alle bisherigen Ertragszahlen beschreiben einen Handel, den der Betrieb so nicht führen kann** |
| **2.639** | **Das Depot verliert Geld bei jeder realistischen Kapazität.** Kapazität 2/3/5 → Wachstum −0,96 / −0,74 / −0,63 bei positivem Ertrag je Trade. Das bestätigt Kelly 0,0859 aus 2.630 unabhängig: der Kontoanteil darf ~8,6 % sein, nicht 50 %. ✔ Der CoinGecko-Unterschied ist dagegen klein (−0,06 Pp) |


## Die Dateien, die angefasst werden

| Datei | wofür | Schritt |
|---|---|---|
| `database/models.py`, `database/db.py` | Stundentabelle + Marke | 1 |
| `api/boersen_klines.py:85` | `interval` 1d → 1h | 1 |
| `api/coingecko.py:184` | gebündelter Abruf für die 16 | 1 |
| `scheduler/background.py` | stündlicher Job, Backoff-Muster | 1 |
| `agent/datenfrische.py` | Frischeprüfung | 1 |
| `agent/marktrang.py:1242 ff.` | Merkmal berechnen | 2 |
| `agent/wahrscheinlichkeit.py:317 ff.` | Beitrag registrieren | 2 |
| `agent/rollen_lauf.py:2195-2198` | Merkmalsliste (hart aufgezählt) | 2 |
| `agent/betraege.py:322` | `hebelrechnung`, Klammern | 2 |
| `Basisinfos/config.yaml` | Schwellen scharf schalten | 2 |
| `agent/entscheidungsrechnung.py:93` | Stop 2,5 → 1,00 ATR ⚠️ **wirkt auf Spot** | 3 |
| `agent/krypto/ausstiegsregel.py:51-52` | Trailing 1,0/1,0 → 1,5/0,5 | 3 |

⚠️ **Nicht anfassen, weil tot:** `hebel_analyst.py`, `hebel_pipeline.py`,
`hebel_screening.py` (2.343 bestätigt).
⚠️ **Nicht anfassen, weil fertig:** `hebelfuehrung.py`, `hebel_aggregat.py`,
`hebel_abgleich.py`, `toepfe.py`, `ui/hebel_view.py` — sie warten nur auf
die erste eröffnete Position.

---

# 3. ⚠️ Die Fallen, die schon einmal zugeschnappt sind

| # | Falle | wo sie zuschnappte |
|---|---|---|
| **1** | **Gesetzte statt gemessene Grenzen** | Bandgrenzen −2,0/−1,5/−1,2 (26.09.) — der Nutzer fand es: *„warum nicht −1,3?"* |
| **2** | **Weglassprobe je Jahr fehlt** | 2.632 wurde eingetragen, bevor sie lief; sie kippte ihn (2.633) |
| **3** | **Gepoolte statt tagestreue Nullwelt** | kippte 2.608 vollständig (2.624) |
| **4** | **Kelly für die Hebelhöhe** | beantwortet die Kapitalfrage, nicht die Höhe dieses Trades (2.630 → 2.632) |
| **5** | **Ein Befund, der eine andere Frage beantwortet** | 2.616 schien die Auflösungsfrage zu klären — dort blieben die Anker stündlich (2.635) |
| **6** | **Zwei Merkmalslisten** `rollen_lauf.py:2195` (Hebel) und `:2603` (Spot) | wer nur eine ändert, erzeugt einen stillen Unterschied |
| **7** | **`erreichbar_max`** in `potential.py` verschiebt sich, wenn ein Beitrag dazukommt → **die Spot-Schwelle ändert sich mit** | vorher rechnen, nicht nachher messen |
| **8** | **Zeitformat** | `%Y-%m-%dT%H` statt `%Y-%m-%d %H:00` ergab still null Treffer (26.09.) |
| **9** | **Die letzte Periode ist nicht abgeschlossen** | CoinGecko liefert als letzten Punkt den Zwischenstand (03:28 statt 03:00) |
| **10** | **Betriebskopie ist keine Messbasis** | Marke **in** der Datei, Riegel im **Helfer**, nicht in einer Textsuche |

---

# 4. ⛔ Offene Punkte — keiner davon darf verloren gehen

| # | offen | Quelle |
|---|---|---|
| **1** | ⚠️ **Der Horizont widerspricht sich dreifach**: gemessen **H24**, Messnorm `messnorm.py:226` **3 Tage**, real Median **0,30 Tage** (2.493). Solange das offen ist, beschreibt die Bewertung womöglich einen anderen Trade als den, der läuft | Voranalyse 26.09. |
| **2** | ✔ **TEILWEISE BEANTWORTET (2.639):** bei Kapazität 2–5 ist das Wachstum **negativ** — der Kontoanteil muss bei rund 8,6 % liegen (Kelly 0,0859), nicht bei 20–50 %. Offen bleibt die genaue Höhe. — **Welche Höhe** bekommt der konstante Hebel? ⭐ Das ist **dieselbe Frage** wie „wie viel Kapital insgesamt" — bei konstantem Hebel entscheidet nur das Produkt aus Einsatz und Hebel | 2.630/2.633 |
| **3** | **Signalmenge ohne Deckel**: 3,2 bis 11,7 je Tag, Faktor 3,6 zwischen den Jahren | 2.633 |
| **4** | **Gaps und Slippage** sind nicht modelliert | 2.627 |
| **5** | **Verlustserie 198–199** — über alle Stopweiten gleich, nicht wegkalibrierbar | 2.621 |
| **6** | ⭐ **Tageszeiteffekt unerklärt**: das Nullband springt von −1,6736 (zufällige Stunden) auf +1,9170 (Anker um 00:00 UTC) — 3,6 Pp für eine **Zufalls**auswahl. Effekt oder Artefakt der Tagesgrenze? | 2.635 |
| **7** | **2026 ist schwächer** als die Vorjahre | 2.631 |
| **8** | Wie wird die **Schwelle in Fünftel-Stufen** übersetzt? Gemessen ist eine Schwelle, der `Beitrag` will `stufen` | Voranalyse 26.09. |
| **9** | Haben die **16 CoinGecko-Symbole** dieselbe Datenqualität wie die 27 aus 2.618? | 2.637 |
| **10** | **Prüftakt und Cooldown** vor dem Produktivgang | Nutzervorgabe |
| **11** | **LLM-Prompts** für Spot und Hebel trennen? | zurückgestellt |
| **12** | Architektur *„ein Eingang, zwei Bewertungen, eine Strategie"* | mit Nutzer zu dimensionieren |

---

# 5. Was NICHT mehr offen ist

| | |
|---|---|
| ✔ | Die Achse trägt — 5 von 5 Jahren, jede Weglassprobe (2.626/2.633) |
| ✔ | Die Schwelle ist **gerechnet**, nicht gewählt (2.632) |
| ⛔ | Die **Stufung** trägt **nicht** — sie hing an 2025 (2.633) |
| ✔ | Der Betrieb braucht **kein** Archiv, nur 7–14 Tage (2.636) |
| ✔ | Binance ist **am Notebook** erreichbar (2.636) |
| ✔ | Quellen **ohne OHLC** sind über den Faktor 2,0832 angleichbar (2.637) |
| ✔ | Das CoinGecko-Kontingent reicht **gebündelt** (2.636/2.637) |
| ⛔ | Auf **Tagesbasis** trägt nichts (2.635) |
| ⛔ | Der Hebel kann heute **gar nicht entstehen** — Kelly exakt 0,0 (2.634) |
