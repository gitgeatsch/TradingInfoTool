# REGEL0 — die festgeschriebene Ausgangslage des Hebel-Neubaus (ENTWURF 30.09.2026, zur Abstimmung)

**Nutzer 30.09.2026:** *„Offenbar haben wir einen stabilen Stand bzw. eine Ausgangslage, welche in eine REGEL0 mit allen
korrekten Parametern festgeschrieben werden muss, und mit allen uns zur Verfügung stehenden Mitteln das Regelwerk optimieren und
ausreizen."* Dazu: *„A und B sind Optionen, die ohnehin sinnvoll sind. C, D, E sehe ich aktuell gar nicht als Option für unseren Umbau."*

> **Zweck:** REGEL0 ist der **Nullstand**. Jede weitere Optimierung wird **gegen REGEL0** gemessen (R-R11: erst REGEL0 bitgleich
> reproduzieren, dann ändern). ⚠️ **Entwurf:** Die Parameter stammen aus den Befunden. Festgeschrieben wird REGEL0 erst nach deinem Ja.

---

## 1. Grundgesamtheit und Daten

| | REGEL0 | Befund |
|---|---|---|
| Messbasis | Binance-Stundenkurse und Terminmarkt, **mit den eingestellten Paaren** (`--menge unverzerrt`) | 2.668/2.669 |
| Zeitraum | Wahl **2024**, Bestätigung einmal **2025-01..2026-08**, 2022 nur Gegenprobe | E-21 |
| Urteil | ≥ 3 von 4 Mengen (bestand, unverzerrt:1–3). Laufen sie auseinander, gilt **unverzerrt** | E-30 |
| Grundgesamtheit | Betrieb und Messung brauchen **dieselbe**, weil die v̂-Skala an der Menge hängt | E-31, CLAUDE.md |

## 2. Bewertung 1 — der Einstieg (Rolle A, *ob*)

| Parameter | REGEL0 | Befund |
|---|---|---|
| Beitrag | **rsi**: rollierendes Kurvenmodell (Form b, 12 Stufen, `rsi_s` und `rsi_s24`), **monatlich** neu geschätzt, Training ab 2023-01 bis Monatsbeginn −24 h | 2.683/2.684, 2.688 |
| Dämpfung | Kreuzvalidierung über 4 Zeitblöcke, Raster `GITTER_NEU` (20 … 2.000.000) | M1-1 ⚠️ grob, siehe B |
| Vorsprung | v̂ = expit(logit(QSh) + Beitrag) − QSh, **QSh** = geschrumpftes Normal (stündlich) | 2.684 |
| **Ereignis** | **Ersteintritt**: erste Stunde mit **v̂ ≥ +0,035** | 2.687/2.688 (per Regel auf 2024) |
| **Ruhe davor** | **48 h** unter der Schwelle (≥ 40 gültige Stunden) | 2.691/2.692/2.694 |
| Einstieg | **1 h** nach dem Signal, nicht in den ersten 24 h eines Monats | 2.688 |
| Zielgröße (Maß) | q5: +5 % vor −5 % binnen 24 h, gegen das geschrumpfte Normal | K4 |
| **nicht** Teil von REGEL0 | Stärke (ordnet nicht, 2.691) · Wucht als Einstieg (Bewegung, 2.693) · Tempo, Tiefe, Ruhe 72 h (2.695) · Kern-Short (Spur, 2.696) · K_IG-Kontext (Auskunft, 2.697) | |

## 3. Bewertung 2 — der Hebel (Rolle C, *wie viel*)

| Parameter | REGEL0 | Befund |
|---|---|---|
| Risikomodell | **ATR zum Einstieg**, rollierend geschätzt, die Liquidationsgefahr je Stufe | 2.667/2.681 |
| Stufen | 2x / 3x / 5x. Gewählt wird die **höchste** Stufe mit geschätzter Liquidationswahrscheinlichkeit binnen H **≤ Grenze**, sonst kein Handel | K6, 2.681 |
| **Grenze** | **2 %** (per Regel auf 2024) | 2.690 |
| Kurs | **Markpreis**, Bitpanda-Liquidationsformel mit m = 0,09 | 2.679 |
| Prüfung auf den Einstiegen | vorsichtig, kein Aufschlag | 2.689 |

## 4. Erfolgsmessung (nicht Bewertung) — die Referenz für jede Optimierung

| | REGEL0 | Befund |
|---|---|---|
| Geometrie | **24 h** halten, **ohne** Ziel, **ohne** Stop | 2.690 (per Regel auf 2024) |
| Kosten | 0,30 % + 0,18 %/Tag auf den **Positionswert**, +1 % bei Liquidation (am Bitpanda-Buch geprüft) | 2.690 |
| Konto | f = 1 % je Handel, log-Wachstum | 2.690 |
| Pflichtprüfungen | Nullwelt, je Jahr, Spot-Vergleich, mit/ohne 10./11.10.2025, **Spiegel** bei Potential-Maßen | E-29 |

## 5. Die Referenzzahlen — REGEL0 muss sie bitgleich treffen (R-R11)

| | bestand | unverzerrt:1 | unverzerrt:2 | unverzerrt:3 |
|---|---|---|---|---|
| Einstiege 2024 / 2025–26 | 1.486 / 6.328 | – / 7.121 | – / 6.463 | – / 6.782 |
| Chance Dq 2024 / 2025–26 | +0,1615 / +0,1039 | – / +0,0774 | – / +0,0697 | – / +0,0781 |
| Hebelkonto 2025–26 (log) | +0,2038 | −0,4662 | −0,4166 | −0,3824 |
| Rohvorteil je Handel | +0,573 % | +0,294 % | +0,311 % | +0,309 % |

Aufruf: `messe_losfahren.py --kern --export 0.035 --ruhe 48` und `messe_k6_hebelstufe.py --kurs mark --einstiege kern48_einstiege_<m>.csv --simulation 24,ohne,0.02`.

## 6. Bekannte Schwächen von REGEL0 — der Optimierungsauftrag

| | Schwäche | Weg |
|---|---|---|
| 1 | Vorteil je Handel (+0,29..+0,31 %) **unter den Kosten** (0,48 %) | **A** Positionsführung (W4): nachgezogener Stop oder Ziel, die Wucht als Bewegungsgröße (Rolle B) |
| 2 | Das Signalangebot **springt**, weil die Dämpfungswahl im groben Raster kippt | **B** Kern stabilisieren (M1-3) |
| 4 | ✔ **BEHOBEN (2.698, J):** ~~Showstopper~~ **Mindesthistorie 12 Monate** für das eigene Normal (`JAHR_H = 8760`, im Code `normal()`). Junge Assets bekommen im **ersten Jahr kein Signal**, obwohl rsi, Ruhe und ATR nur Tage brauchen. Auf der Hebel-Liste sind **12 von 28** Assets jung (TAO, ONDO, RENDER, MORPHO, KAIA, S, W, BIO, TURBO, IO, VIRTUAL, KAITO). Nutzer 30.09.: *„Das System braucht keine Historie, um bei der Prüfung den Einstieg zu bewerten, oder?“* (vgl. 2.610) | **J** junge Assets: das Normal anfangs aus dem **Markt**, mit wachsender eigener Historie überblendet (die Schrumpfung gibt es schon), gemessen gegen REGEL0 |
| 3 | im Gegenwind **stumpf** (Modell flach) | innerhalb von A und B zu lösen, zum Beispiel ob die Stabilisierung das Regime anders abbildet |

➤ **Ablauf der Optimierung (Vorschlag):** Jede Änderung wird **einzeln** gegen REGEL0 gemessen, mit Voranalyse, Wahl 2024 und einmaliger
Bestätigung. Was trägt, wird **REGEL1** usw., und jede Stufe wird mit ihren Referenzzahlen festgeschrieben.

---

## 7. Zurückgestellt (Nutzer 30.09.: *„aktuell gar nicht als Option für unseren Umbau"*)

C Vorwärtstest ab 2026-09 (die Regel K_IG < 1 bleibt eingefroren, aber kein laufender Prüfauftrag) · D neue Datenquellen · E Börse/Kosten.


---

## 8. ⛔ SHOWSTOPPER vor der Festschreibung — die Mindesthistorie (Nutzer 30.09.)

**Nutzer:** *„Die erforderliche Mindesthistorie ist eigentlich ein Showstopper und keine Schwäche, finde ich, und war so nicht geplant
und gewünscht, vor allem wenn man unsere Datenlage berücksichtigt."*

➤ **Folge:** REGEL0 wird **erst nach der Behebung** festgeschrieben. Die 12-Monats-Bedingung ist kein *korrekter Parameter* (E-33),
denn sie widerspricht der Grundanforderung *„muss auch bei nur EINEM Asset funktionieren“* (2.608) und *„10 Tage Historie, nicht
Jahre“* (2.610).

**Wo sie sitzt (Code):** `normal()` verlangt `st - st[0] >= JAHR_H` (8.760 h) und mehr als 1.000 Stunden. Ohne das gibt es kein eigenes
Normal, also kein QSh, kein v̂, kein Signal.

**Lösungsweg — auf dem Bestehenden, ohne neue Zahl:**

| | |
|---|---|
| Schrumpfung (besteht) | je Monat QSh = Marktmitte + B × (eigenes Normal − Marktmitte), mit B = τ² / (τ² + Rauschen). Je weniger eigene Ereignisse, desto mehr Rauschen und desto näher an der **Marktmitte** |
| **Änderung** | Das eigene Normal wird aus der **vorhandenen** Historie gerechnet (höchstens 12 Monate). Das Rauschen wird aus der **tatsächlichen** Zahl eigener Ereignisse bestimmt. Ohne eigene Historie ist QSh = Marktmitte. Ein junges Asset startet so auf dem **Marktnormal** und wächst mit seiner Historie hinein |
| Mindesthistorie danach | nur noch, was das **Signal** braucht: rsi-Monatsabstand (10 Tage), ATR (etwa 14 Tage). Abgeleitet, nicht gewählt |
| **R-R11** | Marktmitte, τ² und das rsi-Modell werden weiter **nur aus den reifen Assets** geschätzt. Für Assets mit ≥ 12 Monaten ändert sich damit **nichts**, und die Referenzzahlen der REGEL0 bleiben bitgleich. Junge Assets kommen **zusätzlich** hinzu |
| Messung | Kern-Einstiege junger Assets in ihrem ersten Jahr: Chance gegen ihr Normal, Spiegel, Nullwelt, je Jahr, Rohvorteil in der Simulation. **Kriterium:** nicht schlechter als die reifen Assets (Dq > 0 in beiden Jahren, über der Nullwelt) |


---

## 9. ✔ J ist Teil der REGEL0 (Befund 2.698)

| Parameter | REGEL0 mit J |
|---|---|
| **eigenes Normal** | aus der **vorhandenen** Historie (höchstens 12 Monate), ab **240 h**. Geschrumpft an derselben Marktmitte und τ², das Rauschen aus Rate × min(365, Tage der Historie). Ohne eigene Historie: Marktmitte |
| Training des rsi-Modells, Marktmitte, τ² | weiter **nur aus reifen** Stunden (≥ 12 Monate), damit bitgleich |
| **Mindesthistorie der Regel** | **10 Tage** (rsi-Monatsabstand, 240 h) |
| Wirkung | +18–21 % Einstiege auf 72–74 zusätzlichen Assets, tragen in 4/4 Mengen |

**Referenzzahlen mit J** (ersetzen Abschnitt 5 nach der Festschreibung):

| | bestand | unverzerrt:1 | unverzerrt:2 | unverzerrt:3 |
|---|---|---|---|---|
| Einstiege 2024–26 | 9.905 | 10.337 | 9.670 | 9.956 |
| Rohvorteil je Handel 2025–26 | +0,583 % | +0,324 % | +0,331 % | +0,343 % |
| Hebelkonto 2025–26 (log) | +0,2634 | −0,4877 | −0,4543 | −0,4058 |

Aufruf: `messe_losfahren.py --kern --ruhe 48 --junge --export 0.035` und `messe_k6_hebelstufe.py --kurs mark --einstiege kern48j_einstiege_<m>.csv --simulation 24,ohne,0.02`.
⚠️ Vor der Festschreibung offen: Schritt 2 im Plan, die **Schwellenwahl auf der vollständigen 2024-Menge**.
