# Voranalyse — Datenbasis: alle abrufbaren Krypto-Assets stündlich (01.10.2026)

**Auftrag (Nutzer 01.10.):** *„Ja, wir benötigen die notwendige Datenbasis. Eine Selektion auf bestimmte Assets ist nicht sehr sinnvoll, es
sollen ja u. U. welche hinzu- oder wegkommen."* — dann: *„Die Ausnahmen waren nur als unwichtiger deklariert, wir nehmen alles, was es gibt,
vor allem, wenn es im Bestand ist. 1. … das selektive Nachladen macht auch Probleme, oder ist das kein Problem? Dachte, wir halten alle Daten.
Bewerte du, was am stabilsten und ressourcenschonendsten ist. 2. Ja, auch das Symbol-Mapping muss stabil sein … 3. Bitte bewerten. Die Lücke
AIOZ und XDC nehmen wir aktuell in Kauf. Prüfen und gegenprüfen."*

> **Urteil in einer Zeile:** Wir halten **alle** stündlichen Kurse, die Binance anbietet (503 Spot + 165 nur als Futures), statt nach Listen nachzuladen.
> Eine **Zuordnungstabelle mit automatischer Preisprüfung** verbindet Bitpanda und Binance. Futures-Kurse werden für Assets ohne Spot erst verwendet, wenn
> eine vorab festgelegte Prüfung zeigt, dass sie für die REGEL0 gleichwertig sind.

---

## 0. Ziel, Stand, Test oder Betrieb

| | |
|---|---|
| **Ziel** | Jedes Asset, das du hältst, beobachtest oder hebeln willst, bekommt ein Signal, sofern es irgendwo stündlich abrufbar ist |
| **Stand** | 116 Assets stündlich am Desktop (Messbasis vom 24.09., aus der Terminmarkt-Liste). Von 58 Assets aus Watchlist, Bestand und Hebel-Liste bekommen nur 28 ein Signal (2.704) |
| **Test oder Betrieb** | Betriebsvorbereitung (B1, B6). Die Bewertung bleibt unverändert, siehe Frage 4 |

**Gemessen am 01.10. (Binance, öffentliche Schnittstelle, nur lesend):**

| | |
|---|---|
| Spot USDT im Handel | **503** |
| Futures-Perpetual USDT im Handel | 528, davon **165 nur als Futures** (nach Abzug des Präfixes 1000) |
| Gewicht je Abruf (1.000 Stunden) | 2 (Grenze 1.200 je Minute). Antwort rund 180 KB |
| Deine fehlenden Assets | Spot: HYPE, ASTER, FLOKI, XNO, PLUME, CAT (als 1000CAT) · nur Futures: AKT, GRIFFAIN, KAS, MON, BRETT, CANTON (als CC) · **nicht bei Binance: XDC, AIOZ, VSN, SUPRA** |

---

## 1. Frage 1 — alles halten oder nach Listen nachladen? (Bewertung)

| | **Alles halten** (empfohlen) | Nach Listen nachladen |
|---|---|---|
| Regel | eine: *alles, was Binance stündlich führt* | hängt an Watchlist, Bestand, Hebel-Liste |
| Neues Asset in deiner Liste | Die Historie ist **schon da**, das Signal kommt sofort | Erst Nachladen. Ohne Rückwärtsladen ist das Asset **10 Tage blind** (J braucht 240 h) |
| Bewegliche Teile | keine Auslöser | Auslöser je Listenänderung, Rückwärtsladen, Lücken bei Fehlern |
| Speicher Desktop | etwa **2 GB** (heute 346 MB für 116) | weniger |
| Notebook | Betriebskopie mit begrenztem Fenster (wie `messdaten.db`), etwa 0,5–1 GB bei 60 GB frei | weniger |
| Laufende Abrufe | etwa **670 je Stunde**, Gewicht ~1.340, also knapp über 1 % der Grenze | weniger |
| Erstbefüllung | etwa 27.000 Abrufe, rund 1–2 h am Desktop, einmalig | je Asset |

➤ **Bewertung:** **Alles halten** ist stabiler: eine Regel, keine Auslöser, kein blindes Fenster. Die Kosten sind gering, nämlich Speicher und ein Abruf je Asset und Stunde.
Selektives Laden spart wenig und bringt genau die Fehlerquellen, die du befürchtest.

---

## 2. Frage 2 — die Zuordnung Bitpanda ↔ Binance stabil machen

Eine **Tabelle als einzige Stelle**, versioniert im Projekt:

| Bitpanda | Binance | Markt | Faktor | Prüfung |
|---|---|---|---|---|
| (Vorgabe) gleiches Kürzel | gleiches Kürzel | Spot, sonst Futures | 1 | automatisch |
| CANTON | CC | Futures | 1 | automatisch |
| CAT | 1000CAT | Spot | 1/1000 | automatisch |

**Was sie stabil macht, ist die automatische Preisprüfung** (täglich): Binance-Kurs × Faktor gegen den Kurs aus deiner Bitpanda- bzw. CoinGecko-Quelle.
Weichen sie um mehr als ±5 % ab, wird die Zuordnung **gesperrt** und gemeldet. Das fängt die gefährlichen Fälle ab, in denen
**dasselbe Kürzel ein anderer Coin** ist (Binance kennt Kürzel wie `S`, `W`, `A`, `B`, `4`), und Umstellungen wie 1000er-Kontrakte. Mit Namensgleichheit allein (2.612)
wäre das nicht gesichert.

---

## 3. Frage 3 — Futures-Kurse für Assets ohne Spot (Messung, vorab festgelegt)

**Prüfling:** Assets, die es bei Binance als Spot **und** als Futures gibt, aus der Messbasis. 20 Assets, gleichmäßig über die Liquidität gezogen (Saat fest),
2025-01 bis 2026-08, stündlich. Spot aus `stundenkurse.db`, Futures-Kurse (Last Price) frisch von der öffentlichen Schnittstelle.

**Gleichwertig, wenn alle vier gelten** (Median über die Assets, dazu das schlechteste Asset als Auskunft):

| Größe | Kriterium | warum |
|---|---|---|
| Stundenrendite, Korrelation | ≥ 0,99 | dieselbe Bewegung |
| rsi 14 (Stunden) | Median \|Δ\| ≤ 1,0 Punkte, P95 ≤ 3,0 | rsi ist der Kern |
| ATR relativ (24 h) | Verhältnis Futures/Spot im Median 0,95–1,05 | ATR steuert die Hebelstufe |
| Rendite 24 h | Median \|Δ\| ≤ 0,10 Prozentpunkte | Erfolgsmessung |

Gegenprüfung: Ein Asset wird von Hand an drei Stunden gegen die Rohwerte geprüft. ⚠️ **Grenze der Prüfung:** Assets, die es **nur** als Futures gibt, sind oft jünger
und dünner. Die Gleichwertigkeit gilt für die Datenart, nicht für jedes einzelne Asset.

---

## 4. ⚠️ Frage 4 (offen, Nutzerentscheidung) — trainieren oder nur bewerten?

Mit allen 668 Assets wird die Frage wichtiger als vorher:

| | |
|---|---|
| **Bewerten, nicht trainieren** (Empfehlung, wie BTC E-37) | Das rsi-Modell, die Marktmitte und die v̂-Skala kommen weiter aus den 116. Die REGEL0 bleibt für alle bisherigen Assets **bitgleich**, und die neuen bekommen ihr Signal mit demselben Modell |
| Training auf alle erweitern | Ändert die **Grundgesamtheit** und damit jeden Wert (CLAUDE.md: *keine Stellschraube*). Nur als **eigene Messung** mit Wirkungsprüfung, Wahl und Bestätigung |

---

## 5. Ablauf

1. Frage 3 messen (diese Voranalyse, ohne weiteren Eingriff) → Bericht
2. Nach deinem Ja (und Frage 4): Zuordnungstabelle und Preisprüfung bauen, Lader auf *alles* erweitern, Erstbefüllung am Desktop
3. R-R11: Die 116 bisherigen Reihen bleiben **zeilengleich**, die REGEL0-Belege bleiben gleich
4. Signalbilanz je Asset neu: Wie viele der 58 bekommen jetzt Signale?
5. Notebook: Betriebskopie und laufendes Nachladen gehören zu Schritt 7 (Bauaufgabe S2)

---

## 6. ERGEBNIS Frage 3 — Futures-Kurse sind gleichwertig (Beleg `Datenbasis_01_10/futures_gegen_spot.txt`)

> **Urteil in einer Zeile:** ✔ **Alle vier Kriterien erfüllt.** Futures-Kurse dürfen für Assets ohne Spot verwendet werden, mit Vermerk.

| Größe (Median über 20 Assets) | gemessen | Kriterium |
|---|---|---|
| Stundenrendite, Korrelation | **0,9926** | ≥ 0,99 ✔ |
| rsi 14, Median \|Δ\| / P95 | **0,43 / 2,42** Punkte | ≤ 1,0 / ≤ 3,0 ✔ |
| ATR relativ Futures/Spot | **1,032** | 0,95–1,05 ✔ |
| Rendite 24 h, Median \|Δ\| | **0,061** Pp | ≤ 0,10 ✔ |

- **Je Asset:** Große Werte sind nahezu identisch (ETH 0,9999, HBAR 0,9997, LINK 0,9982). Dünnere weichen mehr ab (IOST 0,978, IO 0,980): Bei 6 von 20 liegt die rsi-P95 über 3 Punkten (bis 4,8).
- **Die Richtung der Abweichung ist ungefährlich:** Die ATR ist auf Futures **etwa 3 % höher**. Die Hebelstufe wird dadurch eher **vorsichtiger**, nicht kühner.
- ✔ **Gegenprüfung von Hand** (LINK, drei Stunden): Stunden deckungsgleich (UTC), Schluss −0,07..−0,09 % (Basis). ⚠️ Im Absturz vom 10.10.2025 war das Futures-Tief **weniger tief** (8,16 gegen 7,90). In Extremstunden können die Dochte auseinanderlaufen.
- ⚠️ **Grenze:** Assets, die es nur als Futures gibt, sind meist jünger und dünner, dort ist eher mit der größeren Abweichung zu rechnen. ➤ Ihr Signal trägt in der Mail den Vermerk **„Kurs aus Futures“**.

---

## 7. ✔ UMGESETZT (Nutzer 01.10.: *Ja wie empfohlen, prüfen und gegenprüfen*) — Befund 2.705

| | |
|---|---|
| **Daten** | `data/stundenkurse_alle.db`: **537** Assets ab 2023, 8,36 Mio Kerzen, 898 MB, ohne Fehler. Die Messbasis `stundenkurse.db` ist **unberührt** (Dateidatum unverändert) |
| **Quelle je Asset** | **356 Spot, 181 Futures.** Je Asset gilt **eine** Quelle, und zwar der Markt mit der **längeren** Historie. 18 Assets wechselten deshalb zu Futures, z. B. **HYPE**: Spot erst ab 24.09.2026 (173 h, zu kurz für J), Futures ab 30.05.2025 |
| **Zuordnung** | `Basisinfos/symbol_zuordnung.csv` (CANTON → CC, CAT → 1000CAT). Preisprüfung `pruefe_symbol_zuordnung.py`: **40/40 OK, 0 gesperrt**, größte Abweichung 1,24 %. CAT lag schon in der Messbasis (als 1000CAT) und hatte Signale, die bisher unter *CAT* nicht gefunden wurden |
| **Bewertung** | `messe_losfahren.py --zusatz`: Die neuen Assets werden bewertet, aber **nicht trainiert** (wie BTC). ✔ **R-R11:** Die 10.000 REGEL0-Einstiege sind **zeilengleich** |

**Signalbilanz** (Beleg `Datenbasis_01_10/signalbilanz_zusatz__bestand.txt`): **40 statt 29** von 58 Assets bekommen Signale, 2.418 → 3.150 Signale 2024–26.

| neu | 2024 | 2025 | 2026 (bis Aug.) |
|---|---|---|---|
| AKT · BRETT · FLOKI · KAS · XNO | 4–29 | 36–44 | 27–32 |
| GRIFFAIN · HYPE · PLUME | 0 | 19–38 | 26–29 |
| ASTER · CANTON · MON (jung) | 0 | 2–4 | 26–33 |

Ohne Signal bleiben AIOZ, XDC, VSN, SUPRA (nicht bei Binance), EURCV (Stablecoin) und 13 Aktien/ETFs aus dem Bestand.

**Gegenprüfung:** R-R11 zeilengleich. Die Zählung je Asset stimmt mit der Exportdatei überein. Die Preisprüfung läuft je Zuordnung gegen CoinGecko. Beim Prüfen gefunden und behoben:
(1) Die Signalbilanz zählte nur Assets mit Signalen *vorher*, die neuen standen deshalb unter *ohne Signal*. (2) Die Preisprüfung suchte CAT nur unter dem Bitpanda-Kürzel.

⚠️ **Was damit NICHT gesagt ist:**
1. **Ob die REGEL0 für die neuen Assets trägt.** Sie werden mit demselben Modell bewertet. Ein Nachweis wie bei BTC (2.701) steht aus, mit dem Vermerk *nicht nachgewiesen*
2. **Handel:** Für Hebelstufe und Liquidation fehlen den neuen Assets die **Markpreise** (`markpreis_historie.db`). Das ist der nächste Bauschritt
3. **Bestand:** Er stammt noch aus der Desktop-Kopie (19.07.). Der NB-Teilexport nach `git pull` liefert den aktuellen Stand

---

## 8. Markpreise und Nachweis für die neuen Assets — Vorab-Festlegung (Nutzer 01.10.: *Ja, so vorgehen, prüfen und gegenprüfen*)

**Markpreise:** `hole_markpreis.py --zusatz` lädt die Binance-Markpreise (Monatsarchive ab 2023-01) in die **eigene** Datei `data/markpreis_alle.db`, nie in die Messbasis.
Die Sperre gegen fremde Instrumente (`--sperre --zusatz`, Grenze 1 % je Monat) misst gegen `stundenkurse_alle.db`. Zuerst laden die 11 Assets deiner Listen,
die übrigen 526 folgen im Hintergrund (alles halten).

**Nachweis wie BTC (2.701)**, die Gruppe **NEU** = die 11 bewerteten Assets (AKT, ASTER, BRETT, CANTON/CC, FLOKI, GRIFFAIN, HYPE, KAS, MON, PLUME, XNO), REGEL0 unverändert (s +0,035, Ruhe 48 h, J, BTC), 2024–2026:

| | Kriterium | Art |
|---|---|---|
| N-1 | Chance Dq > 0 in jedem Jahr mit ≥ 30 NEU-Einstiegen | Urteil |
| N-2 | gesamt über dem P90 der Nullwelt (rollierende Modelle auf verschobenem rsi, 40 Ziehungen) | Urteil |
| N-3 | Tagesblock untere Grenze > 0 und Spiegel > 0 je Jahr | Urteil |
| N-4 | ≥ 3 von 4 Mengen | Urteil |
| N-5 | Simulation (REGEL0-Erfolgsmessung): Handel, Rohvorteil je Handel gegen 0,48 %, Hebelkonto, Hebelstufe, Liquidationen | Auskunft |
| je Asset | Einstiege und Dq je neuem Asset | Auskunft, **kein** Urteil je Asset (zu wenige Fälle) |

**R-R11:** Die übrigen Einstiege sind zeilengleich zur REGEL0 (je Menge), und das Konto der übrigen ist in der Simulation **bitgleich** zur REGEL0-Referenz.
Die neuen Assets sind **nicht** im ATR-Training (`messe_k6_hebelstufe.py --zusatz`).

**Folge:** Besteht NEU, erhalten die neuen Assets denselben Status wie die übrigen. Besteht NEU **nicht**, gilt wie bei BTC *nicht nachgewiesen*. Die Lösungspflicht
(E-25) gilt: Fehlt ein Beleg dagegen, entscheidest du über die Aufnahme.

---

## 9. ERGEBNIS Nachweis NEU (Befund 2.706)

> **Urteil in einer Zeile:** ✔ **Die REGEL0 trägt auch für die 11 neuen Assets, in 4 von 4 Mengen.** In der Simulation verhalten sie sich wie die breite
> Menge: Der Vorteil je Handel liegt knapp unter den Kosten. Die bisherigen Assets bleiben **bitgleich**.

| | bestand | unverzerrt:1 | unverzerrt:2 | unverzerrt:3 |
|---|---|---|---|---|
| NEU-Einstiege 2024 / 2025 / 2026 | 102 / 304 / 326 | 69 / 324 / 355 | 68 / 327 / 325 | 67 / 316 / 361 |
| N-1 Chance je Jahr | +0,17 · +0,02 · +0,14 ✔ | +0,25 · +0,01 · +0,11 ✔ | +0,24 · +0,01 · +0,11 ✔ | +0,20 · +0,01 · +0,11 ✔ |
| N-2 gesamt gegen Nullwelt-P90 | +0,085 gegen +0,053 ✔ | +0,076 gegen +0,041 ✔ | +0,069 gegen +0,055 ✔ | +0,069 gegen +0,048 ✔ |
| N-3 Tagesblock untere Grenze, Spiegel | +0,020, alle Jahre + ✔ | +0,013 ✔ | +0,007 ✔ | +0,009 ✔ |
| **N-5** Handel · Rohvorteil · Hebelkonto · Liq. | 550 · +0,40 % · −0,018 · 0,37 % | 586 · +0,36 % · −0,024 · 0,17 % | 563 · +0,30 % · −0,025 · 0,18 % | 584 · +0,27 % · −0,049 · 0,34 % |
| ✔ R-R11 Konto der übrigen = Referenz | +0,2708 | −0,4887 | −0,4592 | −0,4065 |

**Je Asset** (Auskunft, kein Urteil, 28–104 Einstiege): KAS (+0,16..+0,23) und CANTON (+0,12..+0,22) durchweg stark, ASTER und FLOKI meist gut,
GRIFFAIN in 3 von 4 Mengen negativ, HYPE gemischt (−0,09..+0,07).

**Was das heißt:**
1. Die neuen Assets bekommen **gleichwertige** Signale. Sie haben jetzt denselben Status wie die übrigen.
2. 2025 ist bei ihnen schwach (+0,01..+0,02), wie bei der ganzen Menge im Gegenwind.
3. Wirtschaftlich gilt dasselbe wie für die breite Menge: Der Vorteil je Handel liegt unter den Kosten (2.703). Die Auswahl und die Kosten bleiben die Hebel.
4. **XNO** hat **keinen Markpreis** (Binance führt dafür keine Futures). Signale ja, Hebelstufe nein. Auf deiner Hebel-Liste steht es nicht.
5. ⚠️ In den Belegdateien steht in den Zeilen B-1/B-2 noch *BTC*, gemeint ist die Gruppe NEU. Die Beschriftung ist im Werkzeug inzwischen korrigiert, die Zahlen sind unverändert.

**Markpreise der übrigen 526 Assets:** laden im Hintergrund (vier Arbeiter, gut die Hälfte erledigt). Danach folgen Zusammenführung und Sperre.

---

## 10. Bitpanda-Katalog gegen Binance — Vorab-Festlegung (Nutzer 01.10.: *Ja, Bitpanda-Katalog prüfen, prüfen und gegenprüfen*)

**Quelle:** der öffentliche Bitpanda-Ticker (880 Einträge, USD-Kurse), ohne Edelmetalle (XAU, XAG, XPT, XPD) und Stablecoins. Binance: Spot- und Futures-Ticker (USDT).
Das ist eine einmalige Prüfung und später ein Baustein für den täglichen Betriebsjob.

**Regel je Bitpanda-Symbol** (Abweichung = Binance-Kurs / Faktor gegen Bitpanda-Kurs):

| Ergebnis | Bedingung | Folge |
|---|---|---|
| **gleich** | dasselbe Kürzel (Spot, sonst Futures), Abweichung ≤ 5 % | keine Zeile nötig (Vorgabe) |
| **Faktor-Ausnahme** | Treffer erst mit Präfix 1000 / 1000000 / 1M, Abweichung ≤ 2 % | Zeile wird **automatisch** in `symbol_zuordnung.csv` eingetragen |
| **Kollision** | dasselbe Kürzel gibt es bei Binance, der Kurs weicht aber > 5 % ab, und kein Präfix passt | Zeile mit Markt **gesperrt**, es entsteht **kein** Signal (anderer Coin unter gleichem Kürzel) |
| **ohne Binance** | kein Kürzel passt | nur Meldung. Gibt es **genau einen** Binance-Coin mit Kurs ±1 %, wird er als **Kandidat** (umbenannt?) genannt, aber **nicht** eingetragen (von Hand bestätigen) |

**Gegenprobe, die bestehen muss:** CAT muss als Faktor-Ausnahme 1000CAT erkannt werden, und CC (so heißt Canton bei Bitpanda) als *gleich* über Futures.
Die bekannten 40 Zuordnungen aus der Preisprüfung dürfen **nicht** als Kollision erscheinen.

---

## 11. ERGEBNIS Bitpanda-Katalog (Befund 2.707) — Belege `Datenbasis_01_10/bitpanda_katalog.txt`, `zuordnung_pruefung.txt`, `signalbilanz_zusatz__bestand.txt`

| Ergebnis (864 Krypto-Assets bei Bitpanda) | Anzahl | Folge |
|---|---|---|
| gleich | **433** | alle mit Stundenkursen bei uns, keine Zeile nötig |
| Faktor-Ausnahme | 1 | CAT → 1000CAT (war schon eingetragen) |
| **Kollision** (anderer Coin unter gleichem Kürzel) | **5** | **LIT, NEIRO, ONE, QUICK, ZK**, als **gesperrt** eingetragen. Keines davon steht in deinen Listen |
| ohne Binance | 425 | nur Meldung |

- ✔ **Gegenprobe:** CAT als Faktor-Ausnahme und CC (so heißt Canton bei Bitpanda) als *gleich* über Futures erkannt.
- ⚠️ **Beim Gegenprüfen gefunden:** Der erste Lauf zählte **108** Kollisionen, weil der Binance-Ticker auch **eingestellte** Paare mit altem Kurs führt (MKR, FTM, EOS, OCEAN …). Korrigiert: Es zählen nur Paare im Handel.
- ⚠️ **Die Suche nach umbenannten Kürzeln über Kursgleichheit ist unbrauchbar.** Sie paart fremde Coins (z. B. AIOZ mit einem chinesischen Meme-Kürzel). Sie bleibt Auskunft, eingetragen wird daraus nie etwas.
- **Gesperrt wirkt überall:** Die Bewertung (`messe_e2_beitraege._zusatz`), die Signalbilanz und die Preisprüfung beachten die Sperre.
- **Krypto oder nicht** entscheidet jetzt der Bitpanda-Krypto-Ticker, nicht mehr die Watchlist (BW, G2X, ROL im Bestand sind Aktien/ETFs).

**Mit den Betriebslisten** (NB-Teilexport 01.10. 19:26: Watchlist 45, Bestand 36, Hebel-Liste 25, zusammen 60):
**40 Assets bekommen Signale.** Ohne Binance bleiben **AIOZ, SUPRA, VSN, XDC** und der Stablecoin EURCV. Dazu kommen 15 Aktien/ETFs.

**Im Betrieb (Schritt 7):** `pruefe_bitpanda_katalog.py` und `pruefe_symbol_zuordnung.py` laufen täglich im Betriebsjob, eine Abweichung wird gemeldet.
