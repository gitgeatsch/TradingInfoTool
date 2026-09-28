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

---

## 7. ✔ ABGESTIMMT (28.09.2026) — J1 bis J10 wie empfohlen

**Nutzer:** *„ja, J1 bis J10 wie empfohlen, bauen und messen."* Werkzeug
`messe_k7_abgleich.py`, Beleg `Basisinfos/K7_Abgleich_28_09/`.

---

## 8. ⛔ ZUERST EIN FEHLER IN DER QUELLE: der Importer teilt die Positionen falsch ein

Der erste Lauf rechnete auf den **188 Positionen** aus `hebel_positions` und
ist **ungültig** (`k7_abgleich_UNGUELTIG_importerpositionen.txt`).

| | |
|---|---|
| **Befund** | `importer/bitpanda_margin_positions.py` schließt bei **jeder** Schlussbuchung die Position ab. Aber **278 von 315** Schlussbuchungen sind **Teilschließungen**, der Kredit bleibt stehen. Nur bei **15 von 188** Positionen war die Rückzahlung gleich dem summierten Kredit (118 weniger, 55 mehr) |
| **Das Buch dagegen geht auf** | je Symbol laufen Menge **und** Kredit exakt auf 0 zurück (größter Restkredit 0,45 €), in **37 Abschnitten** (Kredit von 0 bis 0) |
| **Vor der Liquidation** | TAO/87: Importer 15,90 TAO / 4.619 € Kredit, Buch **19,62 TAO / 5.761 €** · SUI/54: 4.054 / 6.545 €, Buch **4.219 / 6.869 €** |
| **Folge im Betrieb** | ⚠️ Hebel, Kredit und Eigenkapital je Position in `hebel_positions` sind bei den meisten Positionen falsch; die Liquidationserkennung rechnet die Haltedauer ab einem falschen Beginn (2.493 hat genau diese Gebühren gemessen). **Nicht angefasst**, Produktionscode, eigener Punkt |
| **Einheit ab jetzt** | der **Abschnitt** des Buchs; Frage und Kriterien J5/J6 unverändert |

Zweiter eigener Fehler, am Seiteneffekt gefunden: **Staubreste** (18.11. SUI:
0,1 Stück gegen 0,26 € Kredit) hielten einen Abschnitt offen und sahen aus wie
eine Unterdeckung um das Doppelte. Jetzt endet ein Abschnitt, sobald der Kredit
unter 1 € fällt. **J10** zuerst falsch umgesetzt (ganze Abschnitte statt der
Stunden) und korrigiert: Crash-Fall = endet am 10./11.10.; in der Ansicht *ohne*
fallen die Stunden dieser zwei Tage heraus.

---

## 9. Ergebnis

| Prüfung | |
|---|---|
| P0 Sicherung unverändert | ✔ |
| P2 Buch geht auf | ✔ 37 Abschnitte, 4 Liquidationen beenden je einen |
| P3 Formel = K6 `liq_schwelle` bei einem Kauf | ✔ 3,3·10⁻¹⁶ |
| Probe von Hand | ✔ TAO/75 (ein Kauf) und TAO/77 (zwei Käufe) nachgerechnet |

| m = 0,09 | Markpreis | Spot-Tief |
|---|---|---|
| Treffer | **4 von 4** | 4 von 4 |
| Zeitfehler | LINK 9 h · TAO/77 Schlussstunde · TAO/87 23 h · SUI 107 h **zu früh** | gleich |
| Fehlalarme | **6 von 30** | 6 von 30 |
| bei m = 0,0476 | 3 von 4 (TAO/87 fehlt), **1** Fehlalarm | 3 von 4, **2** Fehlalarme |

| | |
|---|---|
| **J6 Kursreihe** | ✔ der **Markpreis** wird Hauptmaß für K6 (nirgends schlechter, bei 0,0476 ein Fehlalarm weniger). Ehrlich: an diesen Fällen sind beide Reihen **fast gleich**, auch im Crash (TAO-Markpreis fiel um 21 Uhr bis 135 $, das Spot-Tief bis 140 $) |
| **J6 m = 0,09** | ⛔ **hält nach der Regel nicht**: kein einzelnes m passt zu allen Fällen (Liquidationen brauchen m ≥ 0,076, fehlalarmfrei nur m < 0,045) |
| **aber: wo die Fehlalarme liegen** | **alle 6** in Büchern mit **6,6x bis 8,2x** nach dem letzten Kauf, also **über dem K6-Deckel 5x**. Im Bereich 2x–5x **kein** Fehlalarm |
| **Richtung** | m = 0,09 liquidiert **zu früh**, nie zu spät. Das ist die sichere Seite |
| **Auflösung** | der Umrechnungsfaktor Bitpanda/Binance streut 0,852–0,877 (±1,5 %). Ein genaueres m als etwa ±0,02 kann Binance für Bitpanda **nicht** liefern. Je Symbol (nachträglich, nur Auskunft): SUI 0,037–0,069 vereinbar, LINK vereinbar, TAO knapp nicht (0,076 gegen 0,071) |
| **J3 Ausführung** | Bitpanda führt **unter** der Formelgrenze aus: im Crash 6–7 %, in der Ruhe 2–3 %. Marge zur Ausführung TAO/87 7,25 %, SUI/54 6,24 % (die Kalibrierung vom 19.07. mit 8,4 / 6,75 % stand auf dem zu kleinen Importer-Buch) |
| **J7 Nullwelt** | verschoben lösen die Liquidationen in **46 %** aus (echt 100 %), die Gegenfälle in **27 %** (echt 20 %). TAO/87 hätte fast überall ausgelöst (39 von 40), das Buch war so hoch gehebelt |
| **J10 ohne 10./11.10.** | die Ruhefälle TAO/87 und SUI/54 bleiben getroffen; 5 von 28 Fehlalarmen, alle ≥ 6,6x |

### ⚠️ R1 bestätigt: zwei vermutlich übersehene Liquidationen

| Buch | Schluss | Ausführung zur Formelgrenze | Gebühr gegen Modell |
|---|---|---|---|
| **AVAX** (8 Käufe, bis 7,6x) | 10.10. **21:14**, in einem Zug | **−2,3 %** | 2,09 % gegen 3,30 % |
| **MORPHO** (17 Käufe, bis 9,4x) | 10.10. **21:00**, in einem Zug | **−3,8 %** | 2,26 % gegen 1,64 % (**+0,62**, knapp unter der Schwelle 0,7) |

Beide im selben Crash-Fenster wie TAO/77 (21:16). **Nur der Nutzer kann das
beantworten.** Bis dahin zählen sie als Gegenfall, AVAX damit als Fehlalarm.

### Was daraus folgt, und was NICHT

| folgt | folgt nicht |
|---|---|
| K6 rechnet mit dem **Markpreis** als Hauptmaß weiter | kein neues m. Die Daten lösen m nur auf etwa ±0,02 auf |
| m = 0,09 bleibt in K6 als **vorsichtige** Wahl, 0,0476 als Auskunft (H8), ab jetzt **begründet**: im Bereich bis 5x an echten Daten kein Fehlalarm | keine Aussage über 10x (dort sind es 6 von 6 Fehlalarmen) |
| der Importer braucht eine eigene Voranalyse (Buch statt Position) | keine Änderung am Betrieb aus K7 |

---

## 10. ⭐ Nachtrag: die Wahrheit aus den Gebühren — 7 Liquidationen, nicht 4 (Befund 2.679)

**Nutzer:** *„ich kann mich leider nicht erinnern, wie viele tatsächlich
liquidiert wurden."* Die Screenshots bestätigen die Buchungen auf die Stelle
(AVAX 6,2060 Stück = 126,64 €, MORPHO 113,9113 = 139,11 €), tragen aber dasselbe
Etikett *Margin Trading Close* wie ein normaler Schluss. Entschieden hat die
**Schlussgebühr**:

| | |
|---|---|
| **Modell mit dem Alter der Posten** (statt ab dem ersten Kauf) | trifft die 278 Teilschließungen auf **−0,01** Punkte (80 % zwischen −0,08 und 0,00) |
| **Sieben Schlüsse** | **+0,97 bis +1,05**: Bitpandas 1-%-Zwangsgebühr |
| **alle 308 übrigen** | höchstens **+0,01**, dazwischen **nichts** |
| **die sieben** | LINK/5, TAO/77, TAO/87, SUI/54 (geführt) · **AVAX** 10.10. 21:14 · **MORPHO** 10.10. 21:00 · **TAO 21.11.2025 07:00** (übersehen) |
| **Rest an den Nutzer** | bei den sieben 0,6–6 % der Menge, normale Vollschließungen Median **24,7 %** |

⚠️ Die Gebühr hängt **nicht** an den Kursreihen, die K7 vergleicht. Die
korrigierte Wahrheit ist deshalb nicht zirkulär. Beide Fassungen laufen:
`--wahrheit gefuehrt` (vorab, 4) und `--wahrheit gebuehr` (7).

| m = 0,09 | vorab (4) | Gebühr (7; MORPHO ohne Markpreis → 6) |
|---|---|---|
| Treffer Markpreis | 4 von 4 | **6 von 6** |
| Fehlalarme Markpreis | 6 von 30 | **5 von 28**, alle 6,6x–8,2x |
| m = 0,0476, Markpreis | 3 von 4, 1 Fehlalarm | 5 von 6, **0** Fehlalarme |
| Spot-Tief | gleich / 1 Fehlalarm mehr bei 0,0476 | gleich / 1 Fehlalarm mehr bei 0,0476 |

**Urteil unverändert:** Der Markpreis wird Hauptmaß. m = 0,09 hält nach der
Regel nicht, liquidiert aber nur zu früh, und bis 5x kommt kein Fehlalarm vor.
Die Liquidationserkennung des Importers übersah **3 von 7**. Sie gehört in die
eigene Voranalyse zum Importer.

---

## 11. Nachtrag: ein Bitpanda-Liquidationspreis aus der App (offene BTC-Position, 28.09. abends)

**Nutzer:** Screenshots der Bitpanda-App und der eigenen Hebel-Tabelle,
*„nein, kein Teilverkauf"*, *„wir waren noch vorsichtiger"*.

⛔ **Erste Fassung falsch** (Commit 26c821a): Ich hatte die 2,83x als
**aktuellen** Hebel gelesen und den Kredit aus dem heutigen Wert abgeleitet
(1.072 €). App und Tabelle zeigen den Hebel **beim Einstieg** (Positionswert /
Eigenkapital). Daraus folgte eine zu hohe Marge (5,8 %) und ein zu kleiner
Abstand unserer Anzeige (3,5 %).

| | |
|---|---|
| App | 0,02255012 BTC, Wert jetzt 1.657,76 €, **2,83x** (beim Einstieg), Performance −52,51 € = **−8,75 % auf 600 € Eigenkapital**, Liquidationspreis **≈ 50.466,83 €** |
| Tabelle (unser Betrieb) | Eigenkapital 600,00 €, eröffnet 23.09.2026, Liq.-Preis **54.393,76 €** |
| nachgerechnet | Positionswert beim Einstieg 2,83 × 600 = **1.698 €**, Kredit **1.098 €**, Einstieg ≈ 75.300 €; unsere Formel 75.300 × (1 − 1/2,83 + 5,9 Tage × 0,18 %) / 0,91 ≈ **54.390 €** ✔ |
| **Abstand** | unsere Anzeige liegt **7,8 % über** Bitpanda, die **vorsichtige** Seite |
| **Bitpandas Marge für BTC** | 1 − Kredit / (Menge × Liquidationspreis): **≈ 3,5 %** ohne Finanzierung, **≈ 2 %**, wenn die aufgelaufene Finanzierung (≈ 18 €) mitzählt, also **unter** dem Doku-Band 4,76–9,09 % |
| Importer | ohne Teilverkauf stimmen Position und Buch überein, die Betriebsanzeige ist hier richtig |

Das passt zu 2.679: Die Marge ist **je Asset** verschieden (SUI 3,7–6,9 %, BTC
2–3,5 %) und liegt **unter** 9 %. m = 0,09 ist vorsichtig, bei BTC deutlich. Es
ist ein einzelner Punkt, keine Kalibrierung. Für K6 heißt das: Das Band aus H8
(0,0476 als Auskunft) reicht nach unten womöglich nicht. Das ist eine Frage
für die K6-Auswertung, keine Änderung jetzt.
