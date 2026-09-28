# Voranalyse K6 — die Hebelstufe aus der Liquidationsgefahr (28.09.2026)

**Nutzer:** *„ja, Voranalyse K6 schreiben — prüfen und gegenprüfen."*
Anlass: K1 Schritt 2b rechnet; K6 (erst **R**, nur Risiko) hängt an der
Kursbewegung und der ATR zum Einstieg, nicht am Ergebnis der Kombination —
darum lässt sich die Voranalyse jetzt schreiben.

---

## 0. ⚠️⚠️ ZUERST EIN KONFLIKT MIT DER ABSTIMMUNG

Unter K6 steht, am 27.09. abgestimmt: **„Wann: erst, wenn die Kombination
(Schritt 2) trägt."** Mein Vorschlag, K6 vorzuziehen, widerspricht dem. Der
Konflikt ist echt — und er hat einen fachlichen Kern (Abschnitt 5b): die
Liquidationsgefahr **aller** Anker ist nicht die Gefahr der Anker, die der
Einstieg **auswählt** (stehende Regel *unbedingte Messung nicht auf eine
Teilmenge übertragen*). **Zur Entscheidung als H0** (Abschnitt 3).

---

## 1. Was abgestimmt ist — und was schon gemessen ist

| | Stand |
|---|---|
| **K6** (27.09.) | Hebelstufe = **höchste Stufe (2x / 3x / 5x), deren vorhergesagte Liquidationswahrscheinlichkeit binnen der Haltedauer unter einer Grenze liegt**; vorhergesagt aus der **ATR zum Einstieg** und **Risikokurven** (volumenschub, oi_aenderung, ema_abstand_atr); **Grenze = Nutzerentscheidung** nach der Tabelle; Kalibrierung **vorwärts**; **zuerst R** (nur Risiko), R+S als Folgemessung |
| **K6a** (Gegenprüfung 27.09.) | ⚠️ q5 endet bei −5 % — das wirkt wie ein Stop; mit Stop bei −5 % liquidiert 2x–5x praktisch nie. K6 setzt **Halten ohne Stop** voraus → **beides** messen: ohne Stop über die Haltedauer (obere Grenze) und mit Stop (Sprungrisiko) |
| **K6b** | die Wartungsmarge 0,09 stammt aus vier Fällen; die Bitpanda-Doku nennt **4,76 % bis 9,09 %** → als **Band** mitführen |
| **K7** (27.09.) | Messbasis **Binance**; Liquidationskurs = **Binance-Markpreis**, das **Spot-Tief** daneben als Vergleich (Spot zählt Dochte: STX −70 % in einer Stunde, 2.667); Formel = **Bitpanda** (m = 0,09, Finanzierung 0,18 %/Tag); Abgleich an den **echten Positionen** (Kopie aus dem Notebook) |
| **2.667** | für die Liquidation zählt der **Prozent**abstand, und den sagt vor allem die **ATR** voraus: −12 % binnen 72 h im untersten ATR-Fünftel **5,8 %**, im obersten **26,9 %**; über die ATR hinaus trägt vor allem `volumenschub` |
| **2.669** | mit den eingestellten Paaren wird der Rand dicker: −27 % (3x) binnen 72 h im obersten Fünftel 2,94 → **3,44–3,69 %**, −45 % (2x) 0,43 → **0,61–0,71 %** — *der Boden fehlte* |

---

## 2. Ist-Stand am Code und an den Daten

**Die Formel** (`agent/krypto/hebel_risk_gate.estimate_liquidation_price`, Long):
`Liq = E · (1 − 1/L + t·f) / (1 − m)` — `L` Hebel, `t` Haltetage, `f` 0,18 %/Tag,
`m` Wartungsmarge. **Nachgerechnet** — der Abstand zum Einstieg:

| Stufe | m = 0,09, Tag 0 | 1 Tag | 3 Tage | 5 Tage | m = 0,0476, Tag 0 |
|---|---|---|---|---|---|
| **5x** | **12,09 %** | 11,89 % | 11,49 % | 11,10 % | 16,00 % |
| **3x** | **26,74 %** | 26,54 % | 26,15 % | 25,75 % | 30,00 % |
| **2x** | **45,05 %** | 44,86 % | 44,46 % | 44,07 % | 47,50 % |

✔ Die Orientierungswerte 12 / 27 / 45 % sind damit bestätigt (Tag 0, m = 0,09).
⚠️ Die Marge verschiebt 5x um **vier Prozentpunkte** — sie ist bei 5x die
wichtigste Unsicherheit.

**Die Daten:**

| | vorhanden? |
|---|---|
| Stundenkerzen mit Hoch/Tief, Bestand + Eingestellte | ✔ — `E2.kursreihen`, wie E2i. ⚠️ Der Bestand sind **Spot**-Kerzen (`api.binance.com`), bei den Eingestellten Spot, wo vorhanden, sonst **Terminmarkt**-Kerzen (Spalte `quelle`) — das *Spot-Tief* ist also bei einem Teil der Eingestellten schon ein Terminmarkt-Tief |
| ATR, volumenschub, ema_abstand_atr | ✔ aus den Kerzen (`E2.kursmerkmale`) |
| oi_aenderung | ✔ Terminmarkt, Bestand + Teil B der Eingestellten (83 % Abdeckung) |
| ⛔ **Binance-Markpreis** (stündlich) | **nicht geladen** — im öffentlichen Archiv (`data.binance.vision`, Terminmarkt, `markPriceKlines`, 1 h) vorhanden, auch für eingestellte Paare; Laden wie Teil B, langsam, mit Pausen |
| echte Positionen (188, 4 Liquidationen) | nur am **Notebook** (Desktop: 0 Zeilen) — braucht eine **Kopie** im Austauschordner (Ü4) |

---

## 3. Vorab festzulegen — H0 bis H10

| # | Frage | Empfehlung | warum |
|---|---|---|---|
| **H0** | ⚠️ **Wann** | **Jetzt bauen und auf allen Ankern messen** (das Risiko als solches, K6 R); die **Gültigkeit für die Anwendung** — auf den Ankern, die der Einstieg auswählt — wird **nach** K1 Schritt 2 nachgeprüft und ist **Pflicht**, bevor K6 verwendet wird. Die Abstimmung *„erst, wenn die Kombination trägt"* gilt damit für die **Verwendung**, nicht für die Messung | spart Zeit ohne Vorgriff; die Teilmengenregel bleibt gewahrt (5b) |
| **H1** | **Lehrer** | je Stufe das **Liquidationsereignis**: der tiefste Kurs binnen der Haltedauer unterschreitet den Liquidationspreis der Formel (m = 0,09, Finanzierung **je angefangene Stunde** mitgerechnet) | K6, K7 |
| **H2** | **Haltedauer** | Achse **24 / 72 / 120 h**, **ohne Stop** (obere Grenze, K6a); dazu **mit Stop bei −5 %** (die q5-Grenze) als Auskunft: wie oft liegt die Liquidation **vor** dem Stop (nur über einen Sprung in derselben Stunde)? | K6a — beides messen |
| **H3** | **Kurs** | **jetzt** das **Spot-Tief** (vorhanden, zählt Dochte → eher **zu viele** Liquidationen, also vorsichtig); **Markpreis nachladen** (H9) und danach als Hauptmaß, Spot-Tief als Vergleich | K7 — bis dahin liegt jede Zahl auf der **sicheren** Seite |
| **H4** | **Eingänge** der Vorhersage | **ATR zum Einstieg** (Grundmodell) · Kombination: ATR + volumenschub + oi_aenderung + ema_abstand_atr | K6 Wortlaut; 2.667 |
| **H5** | **Modell** | je Stufe × Haltedauer eine logistische Schätzung wie in 2b: **glatte Kurven**, Dämpfung per Kreuzvalidierung, wachsendes Fenster rollierend 2024-01 bis 2026-08, feste Teilung für die Nullwelt | Pflichtschritte 24 (Dämpfung aus den Daten) — dieselbe erprobte Mechanik |
| **H6** | **Kennzahlen** | (a) **Kalibrierung vorwärts**: vorhergesagte gegen eingetretene Liquidationsrate je Zehntel · (b) **Mehrwert über die ATR**: Log-Loss-Gewinn der Kombination gegen **ATR allein**, gegen die Nullwelt · (c) **die Tabelle je Grenze** (0,5 / 1 / 2 / 5 %): welche Stufe wie oft gewählt, **eingetretene** Liquidationsrate je gewählter Stufe, je Jahr und BTC-Drittel | K6: *Grenze durch den Nutzer nach der Tabelle*; *Kalibrierung vorwärts* |
| **H7** | **Nullwelt · Regeltest · Tor** | Zeitverschiebung der Risikoeingänge je Asset (40 Ziehungen); Zufallseingänge; **Auflösungs-Tor**: eine gepflanzte **Verdopplung** der Liquidationsrate im obersten Zehntel eines verschobenen Eingangs muss für **5x / 72 h** in ≥ 4 von 5 gefunden werden — sonst trägt nur die **ATR-Tabelle** | Pflichtschritte 17, 25 |
| **H8** | **Wartungsmarge** | Hauptrechnung **m = 0,09** (kalibriert, vorsichtig); **m = 0,0476** (unteres Ende der Doku) als Auskunft — wie stark hängt die gewählte Stufe daran? | K6b |
| **H9** | **Markpreis laden** | Binance `markPriceKlines` 1 h aus dem Archiv, Bestand + Eingestellte, eigene Datei, **nur lesend für die Messung**; Laden langsam mit Pausen, als eigener Schritt mit Prüfung (wie Teil B) — **Nutzerfreigabe für die Abrufe** | K7; *vorsicht bei API-Aufrufen* |
| **H10** | **Umfang** | nur **Long**; Mengen `unverzerrt:1..3` und `bestand`; die Hebelwerte des Betriebs als Auskunft (Namensgleichheit, 2.612) | Bewertung 1 ist *Bewegung nach oben*; Grundgesamtheit |

---

## 4. Das Kriterium — vorab

| # | Bedingung | bei Nein |
|---|---|---|
| **V0** | Auflösungs-Tor (H7) bestanden | nur die ATR-Tabelle, keine Risikokurven |
| **V1** | **kalibriert vorwärts**: je Zehntel mit ≥ 30 Liquidationen weicht die eingetretene Rate um höchstens ein Fünftel (relativ) oder 0,5 Prozentpunkte von der vorhergesagten ab; Steigung 0,7–1,3 — je Stufe, Hauptfall 72 h | **keine** Stufenregel aus diesem Modell |
| **V2** | **Mehrwert über die ATR**: Gewinn der Kombination minus Gewinn der ATR allein jenseits des Nullbands in ≥ 3 von 4 Mengen | es bleibt bei der **ATR allein** — die einfachere Regel |
| **V3** | **stabil**: V1 hält in jedem Jahr 2024/2025/2026 und jedem BTC-Drittel (eingetretene / vorhergesagte Rate zwischen 0,5 und 2) | *reden* — Risiko, das im Regime wechselt, braucht einen Aufschlag |
| **R** | Zufallseingänge im Nullband | nicht verwendbar |
| **T** | die **Tabelle je Grenze** wird ausgegeben — **keine** Grenze gesetzt | – |

---

## 5. ⚠️⚠️ PRÜFUNG UND GEGENPRÜFUNG DIESER VORANALYSE

### 5a. Gegen die stehenden Regeln

| Regel | Prüfung |
|---|---|
| Regel 2 keine Gebühren | ✔ die Finanzierung geht nur in den **Liquidationsabstand** ein (Mechanik, 7c), nicht in eine Bewertung |
| Regel 3 kein Asset-Rang | ✔ die Stufe folgt aus dem vorhergesagten Risiko **dieses** Ankers, nicht aus einer Rangliste |
| **kein Blocker** | ✔ ergibt keine Stufe unter der Grenze, heißt das **kein Hebel** — der **Einstieg** selbst wird nicht gesperrt (K6: Hebel aus dem Risiko, Einstieg aus der Chance) |
| Grenze | ✔ Nutzerentscheidung **nach** der Tabelle (K6) |
| Messstandard | ✔ Nullwelt, Regeltest, Tor, Kreuzvalidierung, vier Mengen |
| R-R11 | ✔ reproduziert zuerst E2i (2.667/2.669): Grundmodell *ATR-Fünftel, Spot-Tief, 12 / 27 / 45 %* muss dieselben Anteile ergeben |

### 5b. ⚠️⚠️ Die Teilmenge — der fachliche Kern des Konflikts aus Abschnitt 0

Der Einstieg wählt Anker aus, die **oben gestreckt** sind (2.675/2.676).
Solche Lagen haben **mehr** Bewegung — ihre Liquidationsgefahr kann höher
sein, als die ATR allein sagt. Eine Kalibrierung über **alle** Anker gilt
dort nicht automatisch (*unbedingte Messung nicht auf eine Teilmenge
übertragen*). ➤ **Gegenmittel:** schon jetzt als Auskunft die Kalibrierung
auf der Teilmenge *rsi oben gestreckt* (P90+, der belegte Rand); **Pflicht
vor der Verwendung:** dieselbe Prüfung auf der tatsächlichen Auswahl aus K1
Schritt 2.

### 5c. Fallen

| Falle | Gegenmittel |
|---|---|
| **2x ist selten** (0,6–0,7 % im obersten ATR-Fünftel binnen 72 h) — zu wenige Fälle für Kurven | für 2x gilt V1 nur, wo ≥ 30 Liquidationen je Zehntel liegen; sonst **ATR-Tabelle** als Auskunft |
| das Spot-Tief zählt Dochte | vorsichtige Seite (eher zu wenig Hebel); nach H9 mit dem Markpreis nachrechnen |
| **Bitpanda liquidiert an seinem Kurs** | K7 entschieden (Binance als Maßstab); der Abgleich an den echten Positionen (Kopie) prüft genau das |
| die Marge ist unsicher | H8 — die Tabelle zeigt, ob sich die gewählte Stufe bei m = 0,0476 ändert |
| die Haltedauer ist nicht festgelegt | Achse; die Positionsführung (Phase 5) legt sie fest |
| Speicher bei 120 h Vorausblick | Tiefstkurse je Reihe in einer eigenen Schleife (wie E2i), Merkmale je Reihe — nicht über den großen Lader |
| aktuelle Hebelstufen (2 / 3 / 5) | `hebel_neubau.HEBELSTUFEN`; weitere Stufen wären eine Zeile mehr, keine neue Messung |

### 5d. Gegen den abgestimmten Stand

| abgestimmt | hier |
|---|---|
| K6 Regel, Eingänge, Grenze, Kalibrierung, zuerst R | ✔ H1, H4, H6, V1 |
| K6 *Wann: erst, wenn die Kombination trägt* | ⚠️ **H0 — zur Entscheidung** |
| K6a Stop gegen Halten | ✔ H2 |
| K6b Marge als Band | ✔ H8 |
| K7 Markpreis vor Spot-Tief | ◐ H3/H9 — **erst** Spot-Tief (vorsichtig), Markpreis nach dem Laden |
| K7 Abgleich an echten Positionen | ⛔ **nicht hier** — braucht die Notebook-Kopie; bleibt eigener Schritt |

---

## 6. Was NICHT in diesen Schritt gehört

R+S (Signalstärke, Folgemessung) · Short · die Grenze selbst (Nutzer) ·
Positionsführung (Stop, Trailing, Ausstieg) · Positionsgröße · der Abgleich an
echten Positionen (K7, Notebook-Kopie) · Betrieb.

---

## 7. Umfang und Laufzeit

| Schritt | Aufwand |
|---|---|
| Werkzeug + R-R11 (E2i reproduzieren) + Tor | ~1 Stunde Rechenzeit |
| Messung, 3 Stufen × 3 Haltedauern × 4 Mengen, Nullwelt nur für den Hauptfall 72 h (5x, 3x) | ~1 bis 1,5 Stunden je Menge |
| Markpreis laden (H9) | ~1 bis 2 Stunden Abrufe mit Pausen, danach Nachrechnung |

---

## 8. ✔ ABGESTIMMT (28.09.2026) — H0 bis H10 wie empfohlen, H9 freigegeben

**Nutzer:** *„ja, H0 bis H10 wie empfohlen, H9 freigegeben."* Damit gilt die
Abstimmung *„erst, wenn die Kombination trägt"* für die **Verwendung** von K6;
gemessen wird jetzt, die Prüfung auf der Einstiegsauswahl bleibt **Pflicht**.
Zum Notebook: für K7 genügt vorerst die Sicherung vom 23.09. im Austauschordner
(`DB_Backups/tradinginfotool_2026-09-23_0221.db.gz`, die vier Liquidationen vom
Juli sind enthalten) — ein neuer Export erst, wenn K7 ansteht.

## 8a. Die Empfehlung, wie abgestimmt

| # | Empfehlung |
|---|---|
| **H0** | jetzt bauen und auf allen Ankern messen; Gültigkeit auf der Einstiegsauswahl **Pflicht** nach K1 Schritt 2, vor jeder Verwendung |
| **H1** | Liquidationsereignis nach der Bitpanda-Formel, Finanzierung je Stunde |
| **H2** | 24 / 72 / 120 h ohne Stop; mit Stop −5 % als Auskunft |
| **H3** | jetzt Spot-Tief (vorsichtig), nach H9 der Markpreis |
| **H4** | ATR allein · ATR + volumenschub + oi_aenderung + ema_abstand_atr |
| **H5** | Mechanik wie 2b (glatt, Kreuzvalidierung, wachsend) |
| **H6** | Kalibrierung, Mehrwert über ATR, Tabelle je Grenze |
| **H7** | Nullwelt, Regeltest, Tor (Verdopplung, 5x/72 h, ≥ 4 von 5) |
| **H8** | m = 0,09, dazu 0,0476 als Auskunft |
| **H9** | Markpreis aus dem Archiv laden — **Freigabe der Abrufe** |
| **H10** | Long, vier Mengen, Hebelwerte als Auskunft |
| **V0–V3, R, T** | wie Abschnitt 4 |

---

## 9. Umsetzung — festgehalten VOR dem ersten Lauf (28.09.2026)

| | |
|---|---|
| Werkzeug | `messe_k6_hebelstufe.py` (Mechanik aus `messe_k1_schritt2b_kombination.py`: glatte Kurven, Kreuzvalidierung) · Lader `hole_markpreis.py` |
| **rollierend je Quartal** | wachsend, nur Vergangenheit, auf die drei Monate danach angewandt — statt monatlich: 3 Stufen × 3 Haltedauern × 2 Modelle, je mit Kreuzvalidierung, wären ~10.000 Schätzungen je Menge |
| **Markpreis-Lücken** | ein Anker mit einer fehlenden Markpreis-Stunde im Fenster fällt heraus — sonst zählte die Lücke still als *nicht liquidiert* |
| Nullwelt-Versatz | ≥ 360 Gitteranker (= 90 Tage) je Asset |
| Reihenfolge | Werkzeugtest → R-R11 und Tor (Bestand, Spot-Tief) → vier Mengen mit dem Spot-Tief → nach dem Laden mit dem Markpreis (nie zwei Rechnungen zugleich) |

---

## 10. ✔ WERKZEUGTEST, R-R11 und TOR (28.09.2026, Bestand, Spot-Tief)

| | Ergebnis |
|---|---|
| **R-R11** E2i | ✔ **reproduziert**: 5x binnen 72 h ATR-Fünftel 1 / 5 **5,80 % / 26,90 %**, 24 h 1,04 % / 9,56 %; 3x 72 h 0,29 % / **2,94 %**; 2x 72 h 0,09 % / **0,43 %** — wie 2.667/2.669 |
| **Tor** (H7) 5x / 72 h | ✔ **bestanden, 5 von 5**: eine gepflanzte Verdopplung im obersten Zehntel eines verschobenen Eingangs gibt Mehrwert +6,6 bis +8,2 gegen die Grenze −1,3 (Nullwelt Mittel −1,35) → die **Risikokurven werden gemessen** |
| Werkzeugtest | alle Abschnitte liefern; 2x / 24 h hat in drei Quartalen zu wenige Liquidationen (erwartet) |

➤ Danach die vier Mengen mit dem Spot-Tief (`data/_vergleich/k6_spot__*.txt`).