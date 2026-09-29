# Voranalyse K6 R+S — Signalstärke und Extreme der Lage in der Hebelstufe (29.09.2026)

**Nutzer:** *„ja, K6 R+S Voranalyse schreiben — prüfen und gegenprüfen."* Dazu: *„Was ist das Zwischenfazit zu unserem
Ziel? Das musst du immer je Messung und Ergebnis festhalten und mit mir abstimmen."*

> **Urteil in einer Zeile:** K6 R+S soll klären, ob ein **stärkeres Signal** mehr Hebel rechtfertigt. Das wäre der
> erste Schritt von *„das Signal ist da“* zu *„so viel Potential, so viel Einsatz“*. Nebenbei prüft die Messung, ob die
> **Extreme der Lage** (funding sehr hoch, sehr viele Longs) das Liquidationsrisiko über die ATR hinaus erhöhen.

---

## 0. ⚠️⚠️ ZUERST: ich hatte „R+S“ still umgedeutet

| | |
|---|---|
| **abgestimmt 27.09.** (Anwendungsebene 2f) | **R+S** = *Risiko als Obergrenze, die **Signalstufe** darf darunter bleiben* — „lohnt nur, wenn starke Signale messbar **besser ausgehen**, nicht nur häufiger“. **S = Signalstärke** |
| **meine Fassung 29.09.** (Einordnung §12, hebel_neubau) | „K6 R+S — **Extreme der Lage** als Risikogewicht“ — das ist etwas **anderes**: ein weiterer **Risiko**eingang (R), keine Signalstärke |

➤ Beides ist fachlich sinnvoll, aber nur das erste ist abgestimmt. **Empfehlung (P1):** Beides in **einer** Messung, klar
getrennt: **Teil S** (die abgestimmte Bedeutung) als **Kern**, **Teil R2** (Lage-Extreme) als Nebenteil. Die
Bezeichnung in den Dokumenten ziehe ich nach deinem Ja nach.

---

## 1. Was bringt das für das Ziel? (vorab)

**Ziel:** *je Asset und Handlung eine begründete Aussage über das POTENTIAL; ein Signal, wenn ein bestimmtes Potential
erreicht ist.*

| wenn … | dann ist gewonnen | wenn nicht |
|---|---|---|
| **S trägt** (stärkeres rsi-Signal geht **besser** aus, und das Risiko bleibt kalibriert) | die **erste Abstufung nach Potential**: schwächeres Signal → weniger Hebel, stärkeres → bis zur Risikoobergrenze. Damit heißt Potential nicht nur *„ja/nein“*, sondern *„wie viel“* | der Hebel bleibt **allein** Sache des Risikos (ATR, 2.681); das Signal bleibt ja/nein |
| **R2 trägt** (Lage-Extreme erhöhen die Liquidationsgefahr über die ATR hinaus) | eine **genauere Obergrenze** (Rolle C) — weniger Hebel, wenn der Markt einseitig gehebelt ist | es bleibt die ATR allein — die einfachere Regel |
| **S2 = H0** (Risiko auf der rsi-Auswahl kalibriert) | die **Pflichtprüfung H0** ist für die Kandidatenregel *rsi allein* erledigt | die Hebeltabelle gilt für die Einstiege **nicht** — Aufschlag nötig |

⚠️ **Erwartung ehrlich:** Für **R2** bescheiden — schon die drei Risikokurven aus K6 brachten nichts über die ATR
(2.681). Für **S** gibt es einen Hinweis: die rsi-Kurve steigt bis ganz oben (+0,16 im obersten Bereich, 2.683 S7).

---

## 2. Was schon gemessen ist

| Befund | Ergebnis | für hier |
|---|---|---|
| **2.681** K6 R | die **ATR allein** sagt die Liquidationsgefahr voraus; 5x kalibriert, 3x geordnet, 2x zu selten; Risikokurven ohne Mehrwert; Tor (Verdopplung) 5 von 5 | Grundmodell und Mechanik — hier wiederverwendet |
| **2.683 S7** | rsi-Kurve **steigend** bis oben; funding sehr hoch −0,10, sehr viele Longs −0,25 (auf q5) | Hinweis für S und R2 |
| **2.663** | funding ≥ 0,0016 zeigt nach unten | R2 |
| **2.685** | rsi trägt in jeder Phase; die **geschätzte** Auswahl löst auf Teilmengen erst +0,08 auf — eine Auswahl mit **fester Richtung** ist feiner | S mit **fester** Richtung, Tor als **Leiter** vorab |
| **H0** (offen seit 2.681) | die Gefahr auf den Ankern, die der Einstieg auswählt — Pflicht vor jeder Verwendung | wird in S2 für *rsi allein* gemessen |

---

## 3. Ist-Stand am Code

| | |
|---|---|
| Werkzeug | `messe_k6_hebelstufe.py` — eigener Lader über die Kursreihen, Markpreis, Liquidation je Stufe × Haltedauer × Marge, `rsi_s` ist schon da (Auskunft *rsi oben*) |
| **fehlt für S** | die **Ausgänge q5** (+5 vor −5 %, 24 h) und das **Phase-Normal** (geschrumpft) — beides aus `messe_losfahren.py` übernehmbar (Spot-Hoch/-Tief wie E2) |
| **fehlt für R2** | `funding_vortag` (Tagessumme des **Vortags**, kein Vorgriff — `E2.funding_je_tag`) und `konten_verh` (24-h-Mittel; dieselbe Tabelle wie `oi`) |
| Abdeckung | funding/konten bei den Eingestellten nicht vollständig — wird im Werkzeugtest **gezählt**, Anker ohne Wert fallen im R2-Modell heraus (dieselben Anker für ATR allein und ATR + Lage) |

---

## 4. Teil S — Signalstärke (der Kern)

| | |
|---|---|
| **Signal** | rsi allein, **feste Richtung**: `rsi_s` (RSI gegen den eigenen 30-Tage-Median) über der Trainingsgrenze P90 |
| **Stärkeklassen** | fünf gleich große Klassen **innerhalb** des obersten Zehntels, Grenzen aus dem Training: P90–92 · 92–94 · 94–96 · 96–98 · 98–100 |
| **S1 Chance** | Dq auf q5 je Klasse gegen das **geschrumpfte** Normal; Urteil: **oberste minus unterste Klasse** |
| **S2 Risiko (= H0 für rsi allein)** | eingetretene Liquidationsrate je Klasse gegen die **ATR-Vorhersage** (beob./gesch.), Hauptfall 5x und 3x, 72 h, Markpreis, m = 0,09; mit/ohne 10./11.10. |
| **S3 Tabelle** | *wenn* S1 und S2 tragen: je Klasse die Stufe unter der Risikoobergrenze und das Ergebnis — **keine** Grenze gesetzt |

## 5. Teil R2 — Extreme der Lage als Risiko

| | |
|---|---|
| **Eingänge** | ATR (Grundmodell) · ATR + funding_vortag + konten_verh (glatte Kurven — sie erfassen die **Extreme**, ohne Schwelle) |
| **Maß** | wie 2.681: Mehrwert (Log-Loss) über die ATR allein gegen die Nullwelt (funding/konten je Asset verschoben) |
| **Black Swan** | 10./11.10.2025 nur **mit / ohne** (Anker, deren Fenster diese Tage berührt) — kein Modell, keine Schwelle daran |
| **Auskunft** | Liquidationsrate je Zehntel von funding und konten (die Kurve der Extreme) |

---

## 6. Die Kriterien — vorab

| # | Bedingung | bei Nein |
|---|---|---|
| **W0** | R-R11: ohne die neuen Teile reproduziert das Werkzeug **2.681** bitgleich (Markpreis, vier Mengen) | nicht weiter |
| **W1** | **Tor als Leiter** (Lehre 2.685): S gepflanzt +0,04 / +0,08 / +0,12 in der obersten Klasse (rsi verschoben) · R2 gepflanzte Verdopplung im obersten Zehntel von funding (verschoben), 5x/72 h · Auflösung = kleinste Stufe mit ≥ 4 von 5 | Urteil nur oberhalb der Auflösung, sonst *nicht auflösbar* |
| **S1** | oberste minus unterste Klasse über dem Nullband (rsi verschoben, 40 Ziehungen) **und** über der Auflösung, fest **und** rollierend, in ≥ 3 von 4 Mengen · Auskunft: steigt die Kurve **monoton**? | starke Signale gehen nicht messbar besser aus → **kein R+S**, der Hebel bleibt Risiko allein |
| **S1z** | Zeit: die oberste Klasse schlägt die unterste in **jedem** Jahr 2024/2025/2026 | nicht zeitstabil → kein R+S |
| **S2** | je Klasse beob./gesch. zwischen 0,5 und 2 (wie V3), 5x und 3x, 72 h, ≥ 3 von 4 Mengen | H0 für rsi allein **nicht** bestanden → die Hebeltabelle braucht einen Aufschlag auf der Auswahl |
| **R2** | Mehrwert von ATR + Lage über ATR allein jenseits des Nullbands in ≥ 3 von 4 Mengen, 5x/72 h und 3x/72 h — **mit und ohne** den 10./11.10. | es bleibt die ATR allein |
| **T** | Tabellen werden ausgegeben — **keine** Grenze gesetzt | – |

⚠️ **Mehrfachtesten:** S hat **eine** vorab benannte Differenz (oberste − unterste), R2 einen Modellvergleich.
⚠️ Dieselbe Prüfzeit wie seit 26.09. — ein *trägt* bleibt Kandidat bis zur Simulation und den Monaten ab 2026-09.

---

## 7. Zur Abstimmung (P1–P9)

| # | Punkt | Empfehlung | Warum |
|---|---|---|---|
| **P1** | Umfang | **S (Kern) und R2** in einer Messung, getrennt ausgewiesen | S ist die abgestimmte Bedeutung (Abschnitt 0); R2 ist billig mitzurechnen (derselbe Lader) |
| **P2** | Signal für S | rsi allein, **feste Richtung**, fünf Klassen im obersten Zehntel | 2.685: die geschätzte Auswahl ist auf Teilmengen zu grob |
| **P3** | Bezug S1 | **geschrumpftes** Normal, q5 | 2.684/2.685 |
| **P4** | Hauptfall | 5x und 3x, 72 h, **Markpreis**, m = 0,09 | 2.679/2.681 |
| **P5** | R2-Eingänge | funding_vortag + konten_verh (24 h) zur ATR; die alten Risikokurven **nicht** wieder | 2.681: sie brachten nichts |
| **P6** | Tor | **Leiter vorab** (S +0,04/+0,08/+0,12; R2 Verdopplung) | Lehre 2.685 |
| **P7** | Black Swan | 10./11.10. nur mit/ohne | Nutzer 29.09. |
| **P8** | H0 | S2 **ist** H0 für die Kandidatenregel *rsi allein*; wird K5 eine andere Regel, gilt H0 dort erneut | spart eine eigene Messung |
| **P9** | Werkzeug | `messe_k6_hebelstufe.py` um `--rs` erweitert; ohne Schalter **bitgleich** zu 2.681; vorab committet | reproduzierbar |

---

## 8. Prüfung und Gegenprüfung

| Prüfung | Ergebnis |
|---|---|
| gegen die Abstimmung | ⚠️ die Umdeutung von „S“ offengelegt (Abschnitt 0) — **zur Entscheidung P1** |
| schon gemessen? | S **nie** (Signalstärke gegen Ausgang **und** Risiko); R2 für funding/konten gegen die **Liquidation** nie (nur auf q5, 2.683) |
| Regel 3 kein Asset-Rang | ✔ die Stärke ist die **dieses** Trades (rsi gegen den eigenen Median), keine Rangliste |
| *Achsen sind Gewichte* | ✔ S senkt den Hebel bei schwächerem Signal, **sperrt** keinen Einstieg; R2 wirkt nur auf die Obergrenze |
| Regel 2 Gebühren | ✔ nur die Finanzierung im Liquidationsabstand (Mechanik, wie 2.681) |
| Vorgriff | funding als **Vortag**; konten 24-h-Mittel bis zur Ankerstunde; rsi bis zur Ankerstunde |
| Teilmengenregel | ✔ S2 misst genau auf der Auswahl (H0) |
| Fallzahl | oberstes Zehntel ≈ 25.000 Prüfanker (Markpreis, geschätzt aus 2.681) → rund 5.000 je Klasse; 2x bleibt zu selten (nur Auskunft) |
| Kalibrierung von A | S1 zeigt nebenbei, ob die rsi-Stärke **dosierbar** ist — die Grundlage für K5 (Schwelle, 3–5 Stufen) |
| Was folgt NICHT | kein Betrieb; die Grenze (Liquidationswahrscheinlichkeit) setzt der Nutzer; Positionsführung bleibt Phase 5 |

---

## 9. Offen, getrennt zu besprechen (Nutzer 29.09.)

**Die Tachonadel und die Mail.** *Kein Gewicht* heißt konkret: die Nadel ändert **nichts** an der Entscheidung — kein
Filter, kein Zu- oder Abschlag auf das Signal, keine Hebelstufe. Mein Vorschlag *„als Fakt in die Mail“* ist
**zurückgezogen**: Du hast recht: eine abstrakte Zahl, die nichts entscheidet, macht die Mail nur voller.
**Empfehlung:** nicht in die Mail. Der **Mailinhalt insgesamt** (*schon jetzt zu viel Information*) wird ein eigener
Abstimmungspunkt — nach K5, weil erst dann feststeht, was das Signal ausmacht.

---

## 10. Umfang

Werkzeug erweitern und vorab committen · W0 (R-R11 2.681) · Werkzeugtest · Tor-Leiter · vier Mengen mit dem Markpreis —
nacheinander, geschätzt **6–7 Stunden** (K6 brauchte 1–1,5 h je Menge; dazu S1 und die Leiter).
