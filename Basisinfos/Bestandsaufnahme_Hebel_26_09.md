# Bestandsaufnahme vor dem Hebelbau — Stand 26.09.2026 abends

> **Nutzerauftrag:** *„erst festhalten, was von den Befunden des Tages
> tatsächlich baurelevant ist und was nur Zwischenschritt war — damit der
> Umbau nicht wieder chaotisch wird"* — dieselbe Forderung wie vor dem
> letzten Hebelumbau.
>
> **Danach:** Viertel 2–4 klären · dann finale Simulation mit
> Qualitätsbewertung und der Frage *„wie viele Signale hätte unser
> Hebel-Portfolio für 2026 bisher erzeugt?"*

---

## ⚠️ Warum es diese Aufnahme braucht

Am 26.09. sind **21 Befunde** entstanden (2.612 bis 2.632), bei
**28 Commits**. Geändert wurde dabei:

| | |
|---|---|
| Doku und Basisinfos | 31 Dateien |
| Mess- und Prüfwerkzeuge | 16 Dateien |
| **Produktivcode** | **1 Datei** — und das war nur die GUI-Parameteranzeige |

⛔ **Die Abzweigung lag nach 2.627.** Dort stand die Hebelhöhe bereits:
*folgt dem Risiko, nicht der Statistik* — über RM-11 und Verlustserie,
ausdrücklich **nicht** über Kelly. Danach hätte gebaut werden müssen.
Stattdessen wurde die Höhe in **2.630 noch einmal abgeleitet**, mit genau
dem Werkzeug, das 2.627 ausgeschlossen hatte, und daraus „die Kalibrierung
fällt" gefolgert. **2.632 hat das eingeholt** — über den Weg von 2.627
trägt die Höhe.

---

# 1. Was BAURELEVANT ist — die Werte für die Kette

| Größe | Wert | Befund |
|---|---|---|
| **Merkmal** | `ema_abstand_atr` = `(close − EMA48) / (ATR × close)` | 2.625 / 2.626 |
| **Richtung** | **invers** — der niedrigste Wert ist der beste | **2.625** |
| **Mindestschwelle** | `W ≤ −1,2881` — die **gerechnete** Kelly-Nullstelle, keine gesetzte Zahl | **2.632** |
| **Hebelhöhe** | ⛔ **KONSTANT** über der Schwelle — die Stufung nach Vierteln ist **nicht belegt** (siehe unten) | **2.633** |
| **Horizont** | **H24** | 2.628 |
| **Stop** | **1,00 ATR** (auch das Netto-Optimum nach Kosten) | 2.628 / 2.629 |
| **Trailing** | Auslöser **1,5 R**, Abstand **0,5 R** | 2.628 |
| **Deckel je Trade** | **RM-11** `max_safe_hebel(stop, 0,09)` — bindet bei diesen Stopweiten nirgends (5,76–6,19×) | 2.627 / 2.632 |
| **Datenquellen** | CoinGecko-Fallback trägt die Bewertung; gröbere Auflösung reicht, OHLC ist nicht nötig | 2.616 / 2.618 |
| **BTC** | gehört **dazu** — gemessen, nicht entschieden | 2.619 |
| **Zu ENTFERNEN** | **Z-2** (`crv_minimum` 2,0) — tautologisch, kann nie greifen | **2.623** |

## Was die Signalmenge ergibt

| | |
|---|---|
| Signale über der Schwelle | **10.531** über 1.748 Tage |
| je Tag | **6,02** |
| Tage mit mindestens einem Signal | **28,5 %** |

### ⭐ Wie viele Signale je Jahr — die Nutzerfrage

| Jahr | Signale | je Tag | Tage mit Signal | q | Ertrag |
|---|---|---|---|---|---|
| 2022 | 1.207 | 3,31 | 17,0 % | 64,5 % | +2,7174 % |
| 2023 | 1.172 | 3,21 | 21,4 % | 63,0 % | +1,0427 % |
| 2024 | 2.072 | 5,66 | 24,3 % | 52,9 % | +0,4690 % |
| 2025 | 4.281 | 11,73 | 37,8 % | 53,7 % | +1,5791 % |
| **2026** *(bis 26.09.)* | **1.797** | **6,68** | **48,0 %** | 54,4 % | **+0,5559 %** |

⚠️ **Die Menge schwankt um Faktor 3,6 zwischen den Jahren.** Ein
Portfolio, das 11,7 Signale je Tag bekommt, braucht eine Begrenzung —
die es heute nicht gibt.

## ⛔ Warum die Stufung NICHT gebaut wird — 2.633

Über die ganze Zeit sah sie gut aus: gestuft gegen flach **+0,001156**
[0,000218 … 0,002150], invers und zufällig beide schlechter. Die
**Weglassprobe je Kalenderjahr** kippt sie:

| ohne | Vorteil gestuft gegen flach | Band | |
|---|---|---|---|
| *(nichts)* | +0,001160 | 0,000244 … 0,002090 | ✔ |
| 2022 | +0,001293 | 0,000262 … 0,002360 | ✔ |
| 2023 | +0,001072 | −0,000014 … 0,002092 | – |
| 2024 | +0,001579 | 0,000584 … 0,002787 | ✔ |
| **2025** | **+0,000032** | **−0,001008 … +0,000963** | **⛔ nichts** |
| 2026 | +0,001511 | 0,000363 … 0,002581 | ✔ |

**2025 stellt 40,6 % aller Signale** bei nur 27,7 % der Tage. Je Jahr
tragen nur 2023 und 2025; **in 2026 ist die Ordnung sogar umgekehrt**
(Viertel 1 +0,23 %, Viertel 3 +0,93 %).

⚠️ **Der eigene Fehler dazu:** die Zeitstabilität fehlte in
Vorabfestlegung 27. 2.632 wurde eingetragen, **bevor** die Weglassprobe
lief — obwohl sie für jeden anderen Befund des Tages Standard war.
Gefunden wurde es nur, weil diese Bestandsaufnahme verlangt war.

## ✔✔✔ Was dagegen hält: die AUSWAHL

| Jahr | Signale | Ertrag | Nullband | Abstand | |
|---|---|---|---|---|---|
| 2022 | 1.207 | +2,7174 % | −1,1336 | **+3,85** | ✔ |
| 2023 | 1.172 | +1,0427 % | −1,2158 | **+2,26** | ✔ |
| 2024 | 2.072 | +0,4690 % | −1,7834 | **+2,25** | ✔ |
| 2025 | 4.281 | +1,5791 % | −1,4551 | **+3,03** | ✔ |
| 2026 | 1.797 | +0,5559 % | −1,5298 | **+2,09** | ✔ |

**Fünf von fünf Jahren**, und **jede** Weglassprobe trägt — auch die ohne
2025 (+1,0361 gegen −1,5760).

⭐ **Daraus die Bauentscheidung: Auswahl ja, Stufung nein.**

---

# 2. Was GELÄNDE war — nötig, aber kein Bauwert

| Befund | was es geklärt hat |
|---|---|
| **2.624** | 2.608 widerlegt — die Nullwelt war gepoolt statt tagestreu. **Ohne diesen Schritt wäre auf einer falschen Achse gebaut worden** |
| **2.617** | Beinahe-Widerlegung auf einem Kollider; die richtige Schichtung sagt das Gegenteil |
| **2.620** | der geometrische Ertrag entscheidet anders als der Kursertrag |
| **2.621** | längste Verlustserie 198–199, **über alle Stopweiten gleich** — sie lässt sich nicht wegkalibrieren |
| **2.622** | `q` ist kalibriert — ⚠️ seit 2.624/2.625 **hinfällig**, weil auf der falschen Achse gemessen |
| **2.629** | die Stopquoten-Obergrenze braucht keine gesetzte Zahl; bestätigt Stop 1,00 als Netto-Optimum |

---

# 3. Was UMWEG war

| Befund | |
|---|---|
| **2.630** | ⚠️ **teilweise.** Die stetige Kurve, ihre Monotonie im Abstand zum Nullpunkt, die out-of-sample-Bestätigung und die gemessene Korrelation **rho 0,3029** gelten und werden gebraucht — aber für die Frage *wie viel Kapital insgesamt*, nicht für die Hebelhöhe. Der Schluss „die Zielzone wird nur mit vollem Kelly erreicht" galt nur für den Kelly-Weg |
| **2.631** | ⚠️ **überholt.** Die Mindestschwelle ist jetzt gerechnet (2.632) statt aus acht Kandidaten gewählt. Was bleibt: Dürre 83 Tage, Lücke 71 Tage, **2026 deutlich schwächer** (+0,19 % gegen +2,65 %) |

---

# 4. Was NICHT zum Hebel gehört — Stammsatz, nach M1

**2.612** vier Symbolwelten ohne Brücke · **2.613** CANTON hat Daten ·
**2.614** der Katalog ist schon der halbe Stammsatz · **2.615** Katalog am
Notebook gefüllt

---

# 5. ⚠️ Was OFFEN bleibt — vor dem Produktivgang zu klären

| # | offener Punkt | Quelle |
|---|---|---|
| **1** | ⛔ **ERLEDIGT UND NEGATIV BEANTWORTET (2.633)** — nicht nur Viertel 2–4 ordnen unsauber, die ganze Stufung hängt an 2025. Gebaut wird mit **konstantem Hebel**. Offen bleibt, **welche Höhe** der konstante Hebel bekommt | 2.633 |
| **2** | **Wie viel Kapital insgesamt** gebunden wird — Positionszahl und Korrelation | 2.630 |
| **3** | **2026 ist schwächer** als die Vorjahre | 2.631 |
| **4** | **Gaps und Slippage** sind nicht modelliert | 2.627 |
| **5** | **Prüftakt und Cooldown** — vom Nutzer als vor dem Produktivgang wichtig benannt | Nutzervorgabe |
| **6** | **Verlustserie 198–199** — nicht wegkalibrierbar, muss in der Positionsführung getragen werden | 2.621 |
| **7** | ⭐ **Die Signalmenge ist nicht begrenzt** — 3,2 bis 11,7 je Tag. Ohne Deckel bekommt das Portfolio in einem Jahr wie 2025 mehr, als es tragen kann | 2.633 |

---

---

# 6. ⛔⛔⛔ Der Ist-Zustand im Code — und er erklärt alles

> **Der Hebel kann seit dem 24.09.2026 strukturell nie mehr entstehen —
> außer bei SHORT. Nicht wegen eines Filters, sondern weil die
> Hebel-Quote rechnerisch exakt auf der Kelly-Nullstelle liegt.**

## Die Rechenkette, an den echten Funktionen nachgerechnet

`agent/rollen_lauf.py:2190` ruft `potential.rechne(instrument="hebel")`.
Von den **acht** registrierten Beiträgen in `agent/wahrscheinlichkeit.py`
gilt für `instrument="hebel"` **kein einziger**:

| Beitrag | `instrumente` | `zustand` | gilt für Hebel? |
|---|---|---|---|
| Funding-Rang im Markt | `("spot",)` | trägt | ⛔ **nein** |
| Turnover-Rang im Markt | `("spot",)` | trägt | ⛔ **nein** |
| Abstand zum 200-Tage-Schnitt | `()` | null | ⛔ nein |
| Vorfilter H · Rangplatz · Lebendigkeit · Termine · Trichter | `()` | null/nie/enthalten | ⛔ nein |

➤ Zuschlag = 0 ➤ Quote = Basisrate `1/(1+CRV)` = **0,333333** ➤
`kelly = (q·(1+CRV) − 1)/CRV` = **exakt 0,0000000000** ➤
`agent/betraege.py:371` `if kelly <= 0:` greift ➤ `ist_hebel = False`.

## ⛔ Der Gegentest macht es unübersehbar

Dieselben Merkmale, **auf das beste Fünftel gesetzt**, nur das Etikett
gewechselt:

| `instrument` | Quote | Kelly | `ist_hebel` | Hebel |
|---|---|---|---|---|
| **`"spot"`** | 0,3513 | **+0,0270** | **True** | **3,12×** |
| **`"hebel"`** | 0,3333 | **±0,0000** | **False** | 1,00× |

⚠️⚠️⚠️ **Der Hebel entsteht nur, wenn man ihn als Spot rechnet.** Die
Instrumenttrennung selbst verhindert ihn.

## ⚠️ Und das war bekannt

Im Memory steht es seit dem 25.09. wörtlich: *„Hebel und Spot **teilen**
die Merkmale — eigene Skala, **keine eigene Bewertung**; meine Kapselung
hatte dem Hebel die Bewertung **genommen**"* und *„die vier Blocker der
Instrumenttrennung — `instrument` ist bei der Quotenrechnung immer
`spot`"*. **Es wurde nie gebaut.**

➤ Das erklärt die 0 Zeilen in `hebel_positions` und den Stillstand von
`hebel_signals` seit dem 10.08. **besser als der Cooldown** — es ist kein
Filterproblem, sondern ein Nullpunkt-Problem.

## ⛔ `ema_abstand_atr` gibt es im Produktivcode nicht

Geprüft über `agent/`, `scheduler/`, `indicators/`, `database/`, `api/`,
`ui/`, `monitor/` und `config.yaml` — **null Treffer**. Es existiert
ausschließlich in neun Messskripten im Repo-Wurzelverzeichnis.

## Der tote Weg — bestätigt

`agent/krypto/hebel_analyst.py` ➤ nur von `hebel_pipeline.py:35`
importiert ➤ dessen zwei Aufrufer sind beide zu (`budget_allocator` wird
für Krypto übersprungen, `ui/hebel_view.py:894` ist fail-closed).
`hebel_screening.aktiv: false`. **Befund 2.343 bestätigt.**

## Die laufenden Werte — gegen die gemessenen

| Größe | läuft heute | gemessen | Quelle |
|---|---|---|---|
| Hebel-Untergrenze | **2,0×** | 2,0× | `config.yaml:2098` `hebel_ab` |
| Hebel-Deckel | **5,0×** | ≤ RM-11 (5,8–6,2) | `config.yaml:2099` |
| Stop | **2,5 × ATR** (≈7,5–8 %) | **1,00 × ATR** | `entscheidungsrechnung.py:93` |
| Trailing-Auslöser | **1,0 R** | **1,5 R** | `krypto/ausstiegsregel.py:51` |
| Trailing-Abstand | **1,0 R** | **0,5 R** | `krypto/ausstiegsregel.py:52` |
| Horizont Hebel | **3 Tage** | **H24 = 1 Tag** | `messnorm.py:226` |
| Bewertungsschwelle | 0,060 R | — | `config.yaml:1837` |

⚠️ **Fünf von sieben laufenden Werten weichen von den gemessenen ab** —
und der Stop um Faktor 2,5.

## Die Dateien, die der Bau anfassen muss

| # | Datei | warum |
|---|---|---|
| **1** | `agent/marktrang.py` | `ema_abstand_atr` je Symbol berechnen und in denselben Eintrag legen wie die Fünftel |
| **2** | `agent/wahrscheinlichkeit.py` | den Beitrag mit **`instrumente=("hebel",)`** registrieren — **das ist der Kern**, ohne ihn bleibt Kelly null |
| **3** | `agent/rollen_lauf.py:2195-2198` | die Merkmalsliste ist hart aufgezählt und muss das neue Merkmal aufnehmen |
| **4** | `agent/betraege.py:322` | `hebelrechnung` — die Klammern `r_min/r_max/hebel_ab/hebel_grenze` |
| **5** | `Basisinfos/config.yaml` | Schwellen scharf schalten |
| **6** | `agent/entscheidungsrechnung.py:93` | Stop 2,5 → 1,00 ATR ⚠️ **wirkt auch auf Spot** |
| **7** | `agent/krypto/ausstiegsregel.py:51-52` | Trailing 1,0/1,0 → 1,5/0,5 |
| **8** | `agent/potential.py` | kommt ein Beitrag dazu, ändert sich `erreichbar_max` und damit die wirksame Schwelle |

⚠️ **Nicht anfassen, weil tot:** `hebel_analyst.py`, `hebel_pipeline.py`,
`hebel_screening.py`.
⚠️ **Nicht anfassen, weil fertig und nachgelagert:** `hebelfuehrung.py`,
`hebel_aggregat.py`, `hebel_abgleich.py`, `toepfe.py`, `ui/hebel_view.py`
— sie warten nur auf die erste eröffnete Position.

---

# 7. ⭐ Was das für die Reihenfolge bedeutet

| # | Schritt | warum zuerst |
|---|---|---|
| **1** | **Den Beitrag verdrahten** (`marktrang` → `wahrscheinlichkeit` mit `instrumente=("hebel",)` → `rollen_lauf`) | **Ohne ihn ist jede andere Änderung wirkungslos** — Kelly bleibt exakt null |
| **2** | Geometrie nachziehen (Stop, Trailing, Horizont) | ⚠️ Der Stop wirkt **auch auf Spot** — eigene Voranalyse nötig |
| **3** | Signalmenge deckeln | 3,2 bis 11,7 je Tag, heute ohne Grenze |
| **4** | Z-2 entfernen | tautologisch (2.623) |
| **5** | Simulation am Prüfstand | erst wenn 1–4 stehen |

⚠️ **Schritt 1 und 2 sind getrennt zu halten.** Wer beides zugleich
ändert, weiß hinterher nicht, welche Änderung gewirkt hat — und der Stop
greift in den laufenden Spot-Arm ein.
