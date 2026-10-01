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
