# Voranalyse — die ANWENDUNGSEBENE: Beiträge kombinieren (27.09.2026)

> **Nutzer 27.09.:** *„Was mir reicht, steht nicht zur Diskussion, ich
> möchte ein funktionierendes System. [...] Das System basiert grundsätzlich
> darauf, dass ein Beitrag selbst schwach ist, aber in Kombination der Effekt
> stärker ist."* — und: *„Die nächste Phase gehen wir sorgsam gemeinsam
> durch."*

⚠️ **Dieses Blatt baut nichts.** Es legt den Ist-Stand, die offenen Fragen
und einen Prüfplan vor. Gebaut wird erst nach Abstimmung, Punkt für Punkt.

---

## 0. Auf welcher Ebene wir stehen

| Ebene | Frage | Stand |
|---|---|---|
| **1 Einzelbeitrag** | trägt ein Merkmal allein, gemessen über alle Assets gegen das eigene Asset? | ✔ gemessen, Pflichtablauf (2.662 bis 2.667) |
| **2 Kombination** | trägt die **Summe** der Beiträge je Asset und Zeitpunkt mehr als jeder allein? | ⛔ **nie gemessen** |
| **3 Anwendung** | ab welcher **absoluten** Summe kommt ein Signal, mit welcher Hebelstufe — und wie oft, mit welchem Ergebnis, je Asset? | ⛔ offen |

➤ Alle Aussagen bis heute sind Ebene 1. Ein schwacher Einzelbeitrag ist
ein **Kandidat** für Ebene 2, kein Misserfolg.

---

## 1. Ist-Stand — die Beiträge, die in die Kombination gehen könnten

Nur was den Pflichtablauf gehalten hat oder dort ausdrücklich als Sperre
belegt ist. Zahlen: Dq = Trefferverhältnis der Auswahl minus das des
eigenen Assets im selben Monat (q5: +5 % vor −5 % in 24 h).

### 1a. Richtung (Bewertung 1 — Einstieg)

| Beitrag | Wirkung | Belegt durch | Vorbehalt |
|---|---|---|---|
| `funding` Vortag **negativ** (≤ P5) | Dq **+0,025** (Mittel über 12 Startstunden), 2022 bestätigt **+0,028** | 2.665, 2.666 | klein; als **Phase** deutlich stärker (gegen das Asset im ganzen Zeitraum / den Markt) — ob es die Phase **vorhersagt**, ist ungemessen |
| `funding` Vortag **hoch** (≥ P95) | **Sperre**, Dq −0,045, 12 von 12 Startstunden negativ | 2.665, 2.666 | 2022 nicht prüfbar (4 Episoden) |
| `konten_verh` **hoch** (viele Longs) | **Sperre**, in allen Regimen negativ | 2.660 (E3, Gegenprüfung) | in E2f auf q5 jenseits des Bandes, aber vorwärts nicht stabil genug für *trägt* |

### 1b. Kontext (marktweit — für alle Assets zur selben Stunde gleich)

| Lage | Messung (Einzeltests, kein Bestes-von-N) | Nutzerhypothese 27.09. |
|---|---|---|
| BTC 24 h ↑ **und** Dominanz 24 h ↑ | q5 Dq **−0,020** (z −6,9) — die Sperre aus 2.601 in Stundendaten | *„eher schlecht"* ✔ passt |
| BTC 24 h ↑ **und** Dominanz 24 h ↓ | q5 −0,003 · q15 **+0,119** (z +8,5) | *„zwei positive Effekte"* — ✔ bei großen Bewegungen, ⛔ nicht bei ±5 % |
| BTC **seitwärts** und Dominanz ↓ | ⛔ **nicht getrennt gemessen** | *positiv* — offen |
| BTC 24 h ↓ | um null | – |

⚠️ Kontext ist nach stehender Vorgabe **kein Beitrag je Asset** — er kann
aber als **Bedingung** in die Kombination (Achse, 2.601).

### 1c. Risiko (Bewertung 2 — Hebelhöhe)

| Beitrag | Wirkung | Belegt durch |
|---|---|---|
| **ATR zum Einstieg** | das Risikomaß selbst: −12 % (≈ 5x) binnen 72 h im untersten Fünftel **5,8 %**, im obersten **26,9 %**; stabil 2022–2026 | 2.667 (E2i) |
| `volumenschub` hoch | mehr Bewegung **über** die ATR hinaus (+0,08 ATR) | 2.667 |
| `oi_aenderung` tief | weniger Bewegung (−0,09 bis −0,16 ATR) | 2.667 |
| `ema_abstand_atr` tief | Risikosperre (MAE in ATR, regelfrei) | 2.642, 2.647 |

### 1d. Nicht als Einstieg zugelassen

| Merkmal | warum |
|---|---|
| `kaeufer_24h` hoch | **begleitet** die Bewegung (12 h alt nur noch 30 %) — 2.665 |
| `momentum_kurz`, `rsi` hoch | **sind** die Vorbewegung — Nutzerdefinition OPTIMUM: *„ein bereits gestiegenes Asset ... dazu brauche ich kein System"* |
| Premium, Käuferanteil auf ±5 % | ohne tragende Wirkung — 2.665 |

---

## 2. Die Fragen, die vor dem Bau zu klären sind

Je Frage: was ich empfehle und warum. **Keine davon entscheide ich allein.**

| # | Frage | Empfehlung | Warum |
|---|---|---|---|
| **K1** | **Wie wird verrechnet?** | zuerst eine **Punktsumme**: jeder Beitrag in seiner belegten Lage +1 (Richtung) bzw. −1 (Sperre); Gewichte erst in einem zweiten Schritt | Gewichte aus denselben Daten sind Anpassung; eine Punktsumme hat keine freien Zahlen außer den Schwellen, die schon festliegen |
| **K2** | **Welcher Bezug?** | **beide** ausweisen: *Moment* (eigenes Asset im selben Monat) und *Phase* (eigenes Asset über den Kalibrierzeitraum) | 2.666: funding wirkt als Phase deutlich stärker; der Monatsbezug war meine Verschärfung, nicht deine Vorgabe. Für die Anwendung zählt, ob die Lage **jetzt** gut ist — egal, ob sie es als Moment oder als Phase ist, solange sie zum Prüfzeitpunkt **bekannt** ist |
| **K3** | **Wie geht der Kontext ein?** | als **Bedingung**: die Punktsumme getrennt je Kontextlage messen (BTC ↑/seitwärts/↓ × Dominanz ↑/↓) — deine Hypothese wird damit direkt geprüft | marktweit, also kein Beitrag je Asset; aber Regime zählt zwölfmal mehr als die Lage (2.598) |
| **K4** | **Zielgröße?** | q5 (±5 % in 24 h) als Hauptfrage, dazu die **Achse** 24 / 72 / 120 h und ±10 % | deine Vorgaben: 5 % ist *geringer Anstieg*, Hebel eher 1 Tag, bis 72–120 h |
| **K5** | **Ab wann ein Signal?** | eine **absolute** Punktschwelle, kein Rang — je Asset anwendbar | deine Vorgabe: *muss auch bei nur EINEM Asset funktionieren*; Regel 3 (kein Asset-Rang) |
| **K6** | **Hebelstufe?** | aus der **ATR zum Einstieg** und der Liquidationsnähe; die Beiträge aus 1c korrigieren | 2.667 — erst nach Ebene 2, und erst mit Markpreis statt Spot-Tief (siehe K7) |
| **K7** | **Markpreis-Daten laden?** | ja, **später** — erst wenn die Kombination trägt | Liquidation läuft am Markpreis; Spot-Dochte überzeichnen 3x/2x (2.667). Sonst wieder eine Ladung ohne Nutzen |

---

## 3. Der Prüfplan — Pflichtablauf plus zwei Lehren von heute

1. **Vorab festlegen** (im Kopf des Werkzeugs): Beitragsliste, Schwellen,
   Punktregel, Zielgrößen, Kriterium *trägt* — vor dem ersten Lauf.
2. **Kalibrierung nur aus der Vergangenheit** — rollierend 12 Monate;
   geprüft Monat für Monat 2024-01 bis 2026-08 (Maßstab) und auf 2022
   (unberührt, soweit die Daten reichen).
3. **Die Kombination gegen ihre Teile:** trägt die Summe **mehr** als der
   beste Einzelbeitrag? Das ist die eigentliche Frage von Ebene 2.
4. **Nullwelt** symboltreu; **Episoden**; **Bekanntheitszeitpunkt** je
   Beitrag.
5. **Gegenprüfung** P2 (1 h älter), P4 (Tausch), **P5 Zufallsbeiträge** —
   dieselbe Punktregel mit zufälligen Merkmalen statt der echten.
6. ⭐ **NEU (2.666):** für jedes **Tagesmerkmal** über die **Startstunden**
   mitteln — sonst misst eine Episodenregel nur Mitternacht.
7. **Je Asset** und **je Regime** ausweisen — *in jedem Regime funktionieren,
   wenn nicht, dann reden wir.*
8. **Ebene 3 nur, wenn Ebene 2 trägt:** Signalhäufigkeit je Asset, Ergebnis
   je Hebelstufe, Liquidationen.

---

## 4. Risiken und Fallen

| Falle | Gegenmittel |
|---|---|
| **Mehrfachtesten durch die Wahl der Kombination** — wer zehn Summen probiert, findet eine | die Punktregel wird **vorab** festgelegt; Varianten nur mit Bestes-von-N-Band und P5 |
| **Anpassung** der Gewichte an die Prüfdaten | K1: erst Punkte, keine Gewichte; Kalibrierung rollierend |
| **Wenige Beiträge** — Richtung hat heute nur funding (+/−) und eine Sperre | die Kombination kann nur zeigen, was da ist; trägt sie nicht, ist das ein Befund über die **Beitragslage**, nicht über das System |
| **Grundgesamtheit** — 115 Symbole mit Stundenkursen, nicht alle Hebelwerte (CANTON, FLOKI …) | die Messung gilt für diese Menge; der Stammsatz (S1–S6) bleibt eine eigene Aufgabe |
| **Live-Beschaffbarkeit** — funding im Betrieb nur als Einzelsatz, der Tageswert erst nach Tagesende | der Vortag ist live bekannt; gemessen wird die Form, die der Betrieb hat |
| **Betrieb zu früh** | Betriebsumstellung erst nach der ganzen Kette inklusive LLM-Rollen (Nutzervorgabe 27.09.) |

---

## 5. Was NICHT in diese Phase gehört

Betrieb am Notebook · LLM-Rollen · Positionsführung (Stop, Trailing,
Ausstieg) · Positionsgröße · Stammsatz/Neuaufnahme.

---

## 6. Zur Abstimmung

| # | Entscheidung | meine Empfehlung |
|---|---|---|
| K1 | Punktsumme zuerst, Gewichte später | ja |
| K2 | Moment **und** Phase ausweisen | ja |
| K3 | Kontext als Bedingung, deine Dominanz-Hypothese direkt mitprüfen | ja |
| K4 | q5 als Hauptfrage, Fenster als Achse | ja |
| K5 | absolute Punktschwelle je Asset | ja |
| K6/K7 | Hebelstufe und Markpreis erst nach Ebene 2 | ja |

➤ Danach der erste Schritt: **nur K3 allein** — der Kontext in allen sechs
Lagen, mit Nullwelt, vorwärts und Gegenprüfung. Er ist klein, prüft deine
Hypothese direkt und liefert die Bedingung, unter der die Kombination
gemessen wird.
