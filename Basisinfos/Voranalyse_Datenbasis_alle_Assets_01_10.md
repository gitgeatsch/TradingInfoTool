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
