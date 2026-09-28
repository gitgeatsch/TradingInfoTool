# Voranalyse K7 — der Abgleich an den echten Positionen (28.09.2026)

**Nutzer:** *„ja, 1 und 2 wie empfohlen — prüfen und gegenprüfen."*
(2 = Voranalyse K7, parallel zu K6 und K1 Schritt 2c.)

> **Urteil in einer Zeile:** Der Abgleich ist machbar und schärfer als
> geplant: nicht 4 Fälle, sondern **4 Liquidationen und 184 Gegenfälle**, und
> jeder Kauf lässt sich einzeln nachspielen. Aber er muss **jeden Kauf
> nachspielen** (nur 47 von 188 Positionen sind ein einziger Kauf), und die
> vier Liquidationen sind **keine unabhängige** Prüfung von m = 0,09. Die
> 184 Gegenfälle sind es.

---

## 1. Was abgestimmt ist

| | |
|---|---|
| **K7** (27.09.) | Messbasis **Binance** (Nutzer: *„Binance ist eine echte Börse, BP ein Broker“*); Liquidationskurs = **Binance-Markpreis**, das **Spot-Tief** daneben; Formel = **Bitpanda** (m = 0,09, Finanzierung 0,18 %/Tag); **Abgleich an den echten Positionen** |
| **H3/H9** (K6, 28.09.) | erst Spot-Tief (vorsichtig), nach dem Laden der Markpreis als Hauptmaß |
| **K6b** | m = 0,09 als Hauptrechnung, 0,0476 (unteres Ende der Bitpanda-Doku) als Auskunft |

**Die Frage an K7:** *Hätten Binance-Markpreis und Spot-Tief mit der
Bitpanda-Formel dieselben Liquidationen ausgelöst wie in echt, zur selben
Zeit, und keine, die es nicht gab?* Das Ergebnis entscheidet, welche Kursreihe
K6 als Hauptmaß nimmt und ob m = 0,09 hält.

---

## 2. Datenlage (erhoben, nicht gemessen)

Nur **gelesen**: Sicherung vom 23.09. 02:21 (entpackte Kopie im Scratch-Ordner,
`immutable=1`) und `Notebook_Analysedaten/bitpanda_transaktionen.json`
(03.08.). Die Produktionsdatei wurde nicht berührt.

| | |
|---|---|
| **Positionen** | 188, alle **Long**, eröffnet 22.09.2025 bis 22.07.2026 · **184 geschlossen**, **4 `wahrscheinlich_liquidiert`** |
| **Liquidationen** | LINK (id 5, 07.–11.10.2025, 4,06x) · TAO (id 77, 10.10.2025, 5,0x, **Crash-Abend**) · TAO (id 87, 21.–22.10.2025, 7,03x) · SUI (id 54, 28.10.–03.11.2025, 4,57x) |
| **Zwei Crash-, zwei Ruhefälle** | **Nutzer 28.09.:** *„ja, das war am 10. Oktober, da ist der gesamte Markt gestürzt, das kommt hin.“* → TAO/77 (10.10. abends) und LINK (11.10.) sind **Crash**-Fälle; TAO/87 und SUI sind die **ruhigen**, an denen m am 19.07. zurückgerechnet wurde. Im Crash sind die Dochte am tiefsten, dort unterscheiden sich **Markpreis und Spot-Tief** am stärksten, und der Ausführungspreis kann weit **unter** dem Auslöser liegen (Lücke). Getrennt ausweisen (J5) |
| **Symbole** | TAO 84 · LINK 37 · SUI 35 · ETH 16 · BTC 10 · sechs weitere je 1 |
| **Hebel** | 1,0x bis **10,0x**, Median **5,64x**; 130 Positionen ≥ 5x |
| **Haltedauer** | Median **7,2 h**, 10 % unter 0,5 h, 90 % unter 78 h, längste 401 h |
| **Kursreihen** | für **186 von 188** liegen Spot-Stunden **und** Markpreis im Haltefenster · ohne Markpreis: CC, HYPE (je 1 Position) |
| **⚠️ Nachkäufe** | **47** Positionen haben einen Kauf, 33 zwei, 24 drei, **84 vier und mehr** · die Liquidationen: LINK **6**, SUI **34**, TAO/77 **2**, TAO/87 **13** Käufe |
| **Buchungen** | 3.908 Margin-Buchungen: open 1.834 · borrow 814 · close 630 · repay 315 · fee 315 · **jeder Kauf und jeder Schluss mit Zeitstempel auf die Sekunde**, 2.149 davon mit Bitpanda-Kurs |
| **Schlusspreis** | das Schlussereignis trägt den **Bitpanda-Ausführungspreis** (Rückzahlungsbuchung mit Kurs) — bei einer Liquidation ist das der Preis, zu dem Bitpanda glattgestellt hat |

### 2a. Der Markpreis — geladen, geprüft, und zweimal korrigiert

| | |
|---|---|
| **Geladen** | 253 Symbole, **6,58 Mio. Stunden** (2021-12 bis 2026-08), Bestand und Eingestellte, 0 Fehler |
| **⛔ Erste Kontrolle fiel durch — an meiner Prüfung** | (1) sie wählte **DOGE**, das nicht in der Messbasis liegt; (2) sie verglich das Markpreis-Tief mit dem Spot-Tief **als Niveau**. Der Markpreis liegt aber **gleichbleibend −0,05 %** neben dem Spot. Bei BTC lag sein Tief darum in 96,6 % der Stunden *unter* dem Spot-Tief. Gemessen war der **Aufschlag**, nicht der Docht |
| **Neu gefasst** | Symbole aus den Daten abgeleitet (alle 116 des Bestands); der Docht **je Reihe** gegen den Schluss der Vorstunde **derselben** Reihe; dazu eine Zeitlageprüfung (±1 h) |
| **⛔ Die neue Kontrolle fiel durch — diesmal an den Daten** | **KAIA 29,8 %, S 39,7 %, A 46,4 %** Abweichung. Unter dem Namen des Vorgängers läuft im Archiv ein **anderer Kontrakt** weiter, während der Spot schon das neue Token ist: A ← EOSUSDT, KAIA ← KLAYUSDT, S ← FTMUSDT, RENDER ← RNDRUSDT (Übergang), POL ← MATICUSDT (ab 2025-10) |
| **Sperre** | die Monatsmediane haben eine **Lücke**: kein Monat liegt zwischen **0,53 % und 1,15 %** → Grenze **1 % je Monat**; **82** Symbol-Monate gesperrt (anderes Instrument), dazu 1.412 ohne Spot-Vergleich, fast alle außerhalb der Spot-Reihen. Tabelle `_abweichung` in der Markpreis-Datei, `hole_markpreis.py --sperre` |
| **✔ Kontrolle bestanden** | Niveau unter 0,2 % in **108 von 110** Symbolen · Zeitlage **110 von 110** · Docht des Markpreises flacher in **56,8 %** der Stunden (Median der Symbole), bei den tiefsten 1 %: **6,08 % gegen 6,40 %** im Mittel |

⚠️ **Folge für K6 (Markpreis-Lauf):** Das Werkzeug nimmt dort den
**Spot-Schluss als Einstieg** und das **Markpreis-Tief als Auslöser**, zwei
Reihen. Der Aufschlag steht dann als Fehler in der Liquidationsdistanz.
**Wird vor dem Markpreis-Lauf korrigiert:** Einstieg und Tief aus **derselben**
Reihe, gesperrte Monate wie fehlende Stunden (der Anker fällt heraus). Die
Spot-Läufe sind davon nicht betroffen.

---

## 3. ⚠️⚠️ Drei Richtigstellungen, bevor gemessen wird

| # | | Folge |
|---|---|---|
| **R1** | **Die Wahrheit ist selbst abgeleitet.** Bitpanda kennzeichnet Liquidationen nicht; `wahrscheinlich_liquidiert` heißt: die Schlussgebühr liegt **mehr als 0,7 Prozentpunkte** über `0,30 + 0,18 × Tage` — nahe an Bitpandas dokumentierter **1 %**-Zwangsgebühr. 2.493 fand den wahren Achsenabschnitt bei **0,38**, der Abstand zur Schwelle schrumpft damit auf rund **0,62** | eine **Gegenfall-Liquidation** (Formel löst aus, Status sagt *geschlossen*) muss man sich **einzeln ansehen**: war es ein eigener Verkauf knapp vor der Grenze, oder eine übersehene Liquidation? |
| **R2** | **m = 0,09 ist an zwei der vier Fälle nachgerechnet** (`hebel_risk_gate.py`, 19.07.: SUI implizit **6,75 %**, TAO/87 **8,4 %**; 0,09 knapp darüber) | die vier Liquidationen können m **nicht bestätigen**, nur die **Kursreihe** vergleichen. m prüfen können nur die **184 Gegenfälle**: bei zu kleinem m hätte die Formel dort **zu spät** ausgelöst — nie beobachtbar; bei zu großem m **Fehlalarme** |
| **R3** | **Liquidiert hat Bitpanda an seinem eigenen Kurs**, nicht an Binance | K7 misst, wie gut **Binance** den Bitpanda-Ausgang **abbildet**, nicht Bitpandas Mechanik. Der Umrechnungsfaktor EUR/Bitpanda ↔ USDT/Binance wird je Kauf **gemessen**, nicht angenommen |

---

## 4. Die Vorschläge zur Abstimmung (J1–J9)

| # | Punkt | Vorschlag | Warum |
|---|---|---|---|
| **J1** | **Nachkäufe** | jede Position **Kauf für Kauf nachspielen**: nach jedem Kauf Menge Q, Kredit K und aufgelaufene Finanzierung F neu; Liquidation, sobald `Tief ≤ (K + F) / (Q · (1 − m))` | das ist die Bitpanda-Formel ohne Vereinfachung (bei einem Kauf wird daraus genau `E·(1 − 1/L + t·f)/(1 − m)`). Mit dem **Endhebel ab dem ersten Kauf** wären 141 von 188 Positionen falsch gerechnet, SUI mit 34 Käufen völlig |
| **J2** | **Umrechnung** | je Kauf der Faktor Bitpanda-Kurs (EUR) / Binance-Kurs (USDT) derselben Stunde; die Liquidationsgrenze wird mit dem **mengengewichteten** Faktor in USDT übersetzt; Streuung des Faktors ausweisen | Wechselkurs und Broker-Aufschlag in einem, **gemessen**. Die Drift des Wechselkurses während der Haltedauer (Median 7 h) bleibt als Unsicherheit stehen und wird genannt |
| **J3** | **Kursreihen** | drei nebeneinander: **Binance-Markpreis-Tief** (Hauptmaß laut K7), **Binance-Spot-Tief**, und als Anker der **Bitpanda-Ausführungspreis** am Schluss | der Ausführungspreis ist der einzige Bitpanda-Kurs **zur Liquidation**, er begrenzt den Auslöser von unten |
| **J4** | **Stundenfenster** | gezählt ab der Stunde **nach** dem ersten Kauf bis zur Stunde **vor** dem Schluss; Kaufstunde und Schlussstunde **gesondert** ausgewiesen | in einer Stunde ist die Reihenfolge von Tief und Buchung unbekannt, sonst zählte ein Tief **vor** dem Kauf |
| **J5** | **Kriterien, vorab** | je Kursreihe und m ∈ {0,09; 0,0476}: **Treffer** (von 4: Grenze bis zur Schlussstunde erreicht) · **Zeitfehler** (Stunden zwischen erstem Erreichen und dem echten Schluss) · **Fehlalarme** (von den Gegenfällen: Grenze **vor** dem Schluss erreicht) · dazu das **m-Intervall**, das mit allen Fällen vereinbar ist | vier Zahlen je Reihe, keine davon ein Urteil über m allein (R2); **Crash- und Ruhefälle getrennt**, weil im Crash die Reihe entscheidet, in der Ruhe die Marge |
| **J6** | **Entscheidungsregel, vorab** | der **Markpreis** wird Hauptmaß für K6, wenn er **alle 4** trifft, den **kleineren oder gleichen** Zeitfehler hat und **nicht mehr** Fehlalarme als das Spot-Tief; sonst werden beide Reihen mitgeführt und dir vorgelegt. **m = 0,09 hält**, wenn es im vereinbaren Intervall liegt | beides vor dem Blick auf die Zahlen festgelegt |
| **J7** | **Nullwelt** | dieselben Positionen auf **verschobene** Zeitfenster gelegt (je Position ±7 bis ±60 Tage, 40 Ziehungen): wie oft löst die Formel dort aus? | zeigt, ob die 4 Treffer mehr sind als *ein Hebel ≥ 4x liquidiert irgendwann ohnehin* |
| **J8** | **Grenzen der Aussage** | vier Liquidationen sind **kein statistischer Nachweis**, sondern ein **Abgleich**; die Gegenfälle (184) tragen die Hauptlast. Zwei Positionen ohne Markpreis (CC, HYPE) fallen heraus | Ehrlichkeit über die Fallzahl |
| **J9** | **Werkzeug** | `messe_k7_abgleich.py`: liest die Sicherungskopie (`immutable=1`) und die Buchungsdatei, **schreibt nichts** außer seiner Ausgabe; Laufzeit Sekunden, läuft **neben** K6/2c; der Pfad auf die Sicherung ist **Pflicht**, eine Vorgabe auf die Standard-DB gibt es nicht | Regel *Standard-DB nie beschreiben*, am Seiteneffekt geprüft |

| **J10** | **Der 10.10.2025 gesondert** | **Nutzer 28.09.:** *„der 10. war ein Black Swan — für Sekunden waren einige Assets zum Teil gegen null.“* → in K7 **und** in der K6-Auswertung eine Auskunft **mit und ohne** den 10./11.10.2025 (nur Auskunft, kein neues Kriterium): wie viel der Liquidationsrate, besonders bei **2x/3x**, stammt aus diesem einen Tag, getrennt nach Spot-Tief und Markpreis | ein Sekundendocht gegen null steht im **Spot-Tief** der Stunde voll drin und liquidiert **jede** Stufe; der Markpreis (geglätteter Index) zeigt ihn kaum. Ein einziger Tag kann so die seltenen 2x-Ereignisse (0,4–0,7 % binnen 72–120 h) tragen. ⚠️ Herausnehmen wäre falsch, denn Black Swans gibt es, und genau davor soll der Hebel schützen. Aber man muss **sehen**, ob die Tabelle auf einem Tag steht |

---

## 5. Gegenprüfung dieser Voranalyse

| Prüfung | Ergebnis |
|---|---|
| Liegt schon eine Messung dazu vor? | **teilweise**: 2.493 hat die **Gebühren** der 188 Positionen gemessen (Rate hält, Achsenabschnitt 0,38); die Kalibrierung vom 19.07. rechnete zwei Fälle am **Bitpanda**-Kurs zurück. Einen Abgleich mit **Binance-Reihen** und **Gegenfällen** gibt es nicht |
| Wirkt K7 auf etwas, das läuft? | auf **K6 mit dem Markpreis** (Hauptmaß, m); **nicht** auf die K6-Spot-Läufe, **nicht** auf 2c |
| Wechselwirkung mit K6 H0 | K6 misst auf **allen** Ankern; die echten Positionen sind eine **ausgewählte** Menge (dein Einstieg). Sie sind darum auch ein erster Blick auf H0, aber nur ein Blick, bei 188 Positionen in 10 Monaten und drei Symbolen |
| Fakt oder Bewertung? | K7 ist ein **Fakt**-Abgleich (*hätte die Formel ausgelöst?*), keine Bewertung. Er darf keine Hebelhöhe festlegen, nur **Kursreihe** und **m** prüfen |
| Was folgt NICHT | kein Urteil über deine Handelsentscheidungen; keine Aussage, ob die Positionen gut waren; nichts über Short (es gibt keine) |

---

## 6. Umfang und Reihenfolge

1. **Abstimmung** J1–J9
2. Werkzeug bauen, Probelauf an **einer** Position mit einem Kauf, von Hand nachgerechnet
3. Lauf, Befund, Vorlage — parallel zu K6/2c möglich (Sekunden, kein Speicherbedarf)
4. K6-Werkzeug auf *eine Reihe für Einstieg und Tief* umstellen (siehe 2a), **dann** der K6-Markpreis-Lauf
