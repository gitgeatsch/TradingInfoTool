# Voranalyse A — Positionsführung als erste Optimierung der REGEL0 (ENTWURF 01.10.2026, zur Abstimmung)

**Auftrag:** Nutzer 30.09. (E-33): *„A und B sind Optionen, die ohnehin sinnvoll sind"*, und 01.10.: *„wie können wir in der Zwischenzeit
weitermachen bzw. parallel du eigenständig Punkte abarbeiten kannst"*. ⚠️ **Das ist nur ein Entwurf.** Es wird nichts gemessen und nichts gebaut,
bevor du Ja sagst.
**Vorher:** REGEL0 festgeschrieben (E-36), Erfolgsmessung 24 h ohne Ziel und ohne Stop. 2.690: Ein festes Ziel kappt die Gewinner. 2.693/2.694: Die Wucht
bringt +5,9 % Hoch binnen 24 h, das bis zum Ausstieg wieder verloren geht. 2.700: Auf deiner Liste ist die REGEL0 schon positiv.

> **Urteil in einer Zeile:** Wir lassen den **Einstieg unverändert** (REGEL0) und messen nur den **Ausstieg**, einen nachgezogenen
> Stop in eigener ATR. Die Frage: Holt er einen Teil des Hochs, das heute nach 24 h wieder weg ist?

---

## 0. Ziel, Stand, Test oder Betrieb

| | |
|---|---|
| **Ziel** | den **Vorteil je Handel** erhöhen, ohne das Signal anzufassen. Das greift S3 an (Rohvorteil unter den Kosten auf allen Assets) |
| **Stand** | Die REGEL0 hält 24 h ohne Stop. In der Wahl 2024 (2.690) war *ohne Ziel* besser als +3 %/+5 %, aber ein **Stop** wurde nie gemessen (bewusst, K6a: *der Stop gehört zur Positionsführung*) |
| **Test oder Betrieb** | Test, Ebene B (Erfolgsmessung). Die **Bewertung bleibt neutral** und unberührt, die Positionsführung ist Phase 5 (Nutzer 30.09.) |

---

## 1. Die Messung — Vorschlag

| | |
|---|---|
| Einstiege | **REGEL0**, fest: `kern48j_einstiege_<m>.csv` |
| Hebelstufe | REGEL0: ATR-Modell, Grenze 2 %. ⚠️ Die Liquidationsgefahr hängt an der **Haltedauer** H, und das Modell gibt es für H = 24 / 72 / 120 h |
| **Achse Stop** | nachgezogener Stop: Abstand **k × ATR** unter dem höchsten Markpreis-Hoch seit dem Einstieg, mit k ∈ {1,0; 1,5; 2,0; 3,0} |
| **Achse Haltedauer** | höchstens H ∈ {24, 72} h, dann Zeitausstieg |
| Referenzzelle | *ohne Stop, 24 h* = REGEL0. Sie muss **bitgleich** zur Referenz sein (R-R11) |
| Reihenfolge in einer Stunde | Liquidation vor Stop vor neuem Hoch, also vorsichtig: Ein neues Hoch derselben Stunde hebt den Stop erst ab der nächsten |
| Kosten | wie REGEL0. Der Stop-Ausstieg kostet dieselbe Gebühr, die Finanzierung läuft bis zum Ausstieg |
| **Wahl** | auf **2024** per Regel: größtes Kontowachstum, bei Gleichstand (< 1 % Endwert) die **einfachere** Zelle (ohne Stop vor mit Stop, dann größeres k, dann kürzeres H) |
| **Bestätigung** | einmal 2025–26 in 4 Mengen, Kriterien S1–S5 wie 2.690/2.694, dazu *besser als REGEL0* in ≥ 3/4 Mengen |
| Auskunft | dieselbe gewählte Zelle auf deiner **Hebel-Liste** (2.700) |

9 Zellen (4 × 2 + Referenz) auf 2024. Das ist wenig Mehrfachtesten, und die Bestätigung erfolgt einmal.

---

## 2. Prüfung und Gegenprüfung

| | |
|---|---|
| R-R11 | Die Referenzzelle trifft die REGEL0 (Hebelkonto, Rohvorteil, Handel) |
| Nullwelt | zeitverschobene Einstiege mit derselben Stop-Regel. Der Stop allein darf im Zufall nicht tragen |
| Zeitstabilität | 2025 und 2026 getrennt, Juli–Dezember 2025 |
| Spiegel | der Stop verändert die Verteilung. Ausgewiesen werden Gewinn- und Verlusthandel getrennt |
| Vorgriff | Der Stop nutzt nur Hochs **nach** dem Einstieg, stündlich |

---

## 3. ⚠️ Betriebsprüfung (E-35) — schon jetzt zu klären

| # | Frage | warum |
|---|---|---|
| A-B1 | Kann Bitpanda einen **nachgezogenen Stop** für Hebelpositionen, oder muss das System ihn stündlich nachführen? | Ohne das ist die Regel im Betrieb nicht ausführbar. Das ist eine **Nutzerfrage** |
| A-B2 | Stündliche Markpreise am Notebook live | Das ist dieselbe Datenanbindung wie für die REGEL0 (Schritt 7) |

---

## 4. Zur Abstimmung (später)

| # | Vorschlag |
|---|---|
| **A1** | Stop in ATR mit k ∈ {1,0; 1,5; 2,0; 3,0} × H ∈ {24, 72}, Referenz REGEL0 |
| **A2** | Wahl 2024 per Regel, einmal bestätigt, ≥ 3/4 Mengen und besser als REGEL0 |
| **A3** | Die Antwort zu A-B1 (Bitpanda) von dir, bevor A in den Betrieb geht |

---

## 5. ✔ ABGESTIMMT (Nutzer 01.10.2026) — mit der Antwort zu A-B1; Vorab-Festlegung VOR dem Bau

**Nutzer:** *„Ja, BTC aufnehmen, weiter mit A, prüfen und gegenprüfen. Zu deiner Frage: BP bietet keinen Trailing-Stop als Funktion an, das muss ich
händisch erledigen, soweit mir bekannt."*

➤ **Folge für die Messung (E-35, Betriebstauglichkeit):** Der Stop wird im Betrieb **vom System stündlich berechnet und gemeldet**, und der Nutzer schließt **von
Hand**. Gemessen wird deshalb der Ausstieg **mit Ausführungsverzug**:

| | festgelegt |
|---|---|
| Einstiege | REGEL0 mit BTC (`kern48jb_einstiege_<m>.csv`), Hebel REGEL0 (ATR, Grenze **2 %**, unverändert) |
| Stop-Linie | höchstes Markpreis-Hoch seit dem Einstieg (bis zur **Vor**stunde) minus **k × ATR** zum Einstieg (Tages-ATR, relativ) |
| Auslösung | erste Stunde, deren Markpreis-Tief die Linie erreicht |
| **Ausstieg (Urteil)** | **Verzug v = 1 h**: zum Markpreis-Schluss der Stunde **nach** der Auslösung (Meldung, dann Handgriff) |
| Ausstieg (Auskunft) | v = 0 an der Linie (Obergrenze, nicht erreichbar), dazu in der Bestätigung v = 2 und 4 h (Empfindlichkeit) |
| Liquidation | hat Vorrang, auch während des Verzugs |
| Achsen | k ∈ {ohne, 1,0, 1,5, 2,0, 3,0} × H ∈ {24, 72} (Zeitausstieg nach H) |
| **Wahl 2024** (bestand) | nur die v = 1-Zellen: größtes Hebelkonto, bei Gleichstand (< 1 % Endwert) die einfachere Zelle (ohne Stop vor mit Stop, dann größeres k, dann kürzeres H) |
| R-R11 | Die Zelle *ohne Stop, 24 h* muss die bisherige Rechnung (24 h, ohne Ziel) **bitgleich** treffen |
| **Bestätigung** | einmal 2025–26, 4 Mengen: S1–S5 wie 2.690/2.694, dazu **besser als die REGEL0-Referenz** (Hebelkonto) in ≥ 3/4 Mengen |
| Auskunft | die gewählte Zelle auf deiner Hebel-Liste |

⚠️ **Betrieb:** Die Meldung *„Stop erreicht“* gehört in die Mail (Phase 5). Verkaufen musst du selbst, deshalb gibt es den Verzug. Ein Verzug von mehreren Stunden (nachts) zeigt die Empfindlichkeit.

**Umsetzung und Funktionstest (vor dem Lauf):** `messe_k6_hebelstufe.py --stop-wahl` (Wahl 2024) bzw. `--stop H,k,v` (Bestätigung, dazu Auskunft v = 0/2/4
und die REGEL0-Zelle im selben Lauf). Probe (3 Monate) technisch sauber. ✔ **R-R11:** *ohne Stop, 24 h* = bisherige Rechnung bitgleich (+0,0743).
⚠️ Beobachtung in der Probe (Inhalt nicht gewertet): Der Ausstieg **genau an der Linie** (v = 0) war schlechter als mit 1 h Verzug. Nach einem Stop-Treffer erholt sich der Kurs
innerhalb der Stunde oft wieder. v = 0 ist also **keine** Obergrenze. Es bleibt Auskunft, das Urteil fällt auf v = 1.

---

## 6. WAHL 2024 (bestand) — gemessen 01.10.2026 früh, Beleg `Basisinfos/A_01_10/wahl__bestand.txt`

> **Urteil in einer Zeile:** Die Regel wählt **72 h · Stop 1,5 ATR · Verzug 1 h**, Hebelkonto 2024 **+0,287** gegen REGEL0 **+0,250** (×1,33 gegen ×1,28).
> Der Abstand ist klar (Zweite +0,270, mehr als 1 %). ⚠️ Der Gipfel ist aber **schmal**, und der Rückgang steigt von 0,189 auf 0,279.

| H | Ausstieg (v = 1 h) | Konto log | Rückgang | Ø Hebel | Spot |
|---|---|---|---|---|---|
| 24 | **ohne Stop = REGEL0** | **+0,250** | 0,189 | 3,34 | +0,143 |
| 24 | Stop 1,0 / 1,5 / 2,0 / 3,0 ATR | +0,247 / +0,257 / +0,270 / +0,264 | 0,159 / 0,174 / 0,182 / 0,190 | 3,34 | +0,130 / +0,140 / +0,145 / +0,144 |
| 72 | ohne Stop | +0,192 | **0,400** | 2,53 | +0,221 |
| 72 | Stop 1,0 / **1,5** / 2,0 / 3,0 ATR | +0,244 / **+0,287** / +0,240 / +0,179 | 0,196 / **0,279** / 0,346 / 0,400 | 2,53 | +0,192 / **+0,234** / +0,226 / +0,211 |

**Prüfung:**
- ✔ **R-R11:** *ohne Stop, 24 h* über den neuen Stop-Pfad = bisherige Rechnung, **bitgleich** (+0,2498).
- ✔ **Wiederholung:** Ein zweiter Lauf mit Spur ist zeilengleich.
- ✔ **Liquidation hat Vorrang:** Mit Verzug liegt die Liquidationsquote über der ohne Verzug (0,09 % gegen 0,00 % bei 1,0 ATR/24 h), mit wachsendem k nähert sie sich *ohne Stop* (0,37 %).
- ℹ️ 2204 statt 2188 Handel bei 72 h: Das ATR-Modell hat für 2x bei 24 h nicht überall eine Schätzung, deshalb entfallen bei 24 h 16 Einstiege. Das ist dieselbe Regel wie in der REGEL0, nicht neu.

**Gegenprüfung (unabhängig nachgerechnet):** `pruefe_a_stop_unabhaengig.py` rechnet die Spot-Rendite aller 21 Zellen direkt aus den Rohdaten nach: eigene ATR, über die **Stunde** statt den Zeilenindex adressiert, eigene Linie und eigener Ausstieg.
- ✔ **400 von 400** Einstiegen in **21 von 21** Zellen gleich (größte Abweichung 5·10⁻¹¹, Rundung der Spur). Beleg `gegenpruefung__bestand.txt`.
- ✔ **Die Prüfung kann fehlschlagen:** Mit Vorgriff aufs Hoch der laufenden Stunde (`--gegenprobe`) weicht sie in **allen Stop-Zellen** ab, die Zellen ohne Stop bleiben gleich. Beleg `gegenprobe_vorgriff__bestand.txt`.

**Was die Zahlen sagen (Auskunft, kein Urteil):**

| | |
|---|---|
| **Die Haltedauer trägt, der Stop macht sie tragbar** | 72 h ohne Stop bringt Spot mehr (+0,221 gegen +0,143), mit Hebel aber Rückgang 0,400. Der Stop halbiert fast den Rückgang und hebt das Konto |
| **Der Gipfel ist schmal** | Bei 72 h liegen die Nachbarn 1,0 und 2,0 ATR auf REGEL0-Höhe (+0,244 / +0,240). Bei 24 h ist es breiter: 1,5 bis 3,0 ATR liegen alle über REGEL0. Bei 10 Zellen ist ein Gewinn von +0,037 log aus der Auswahl allein nicht auszuschließen. Deshalb gibt es die **einmalige Bestätigung** |
| **Verzug 1 h ist besser als Ausstieg an der Linie** | in **allen** k und H. Nach dem Stop-Treffer erholt sich der Kurs in der Stunde danach im Mittel. Für den Handgriff ist das günstig: Der Verzug kostet nichts. Er heißt aber auch, dass ein Teil der Stop-Treffer Rücksetzer im laufenden Rückkehrhandel sind |
| **Vergleich (vor dem Neubau, keine Grundlage)** | 2.628 (26.09.) fand Trailing 1,5 ATR auf einer anderen Auswahl. Das ist gleiche Größenordnung, aber kein Beleg |

**Betrieb (E-35):** 72 h heißt, dass bis zu drei Tage gleichzeitig Positionen offen sind und der Stop stündlich gemeldet wird, auch nachts. Die Auskunft v = 2/4 in der Bestätigung zeigt, was ein späterer Handgriff kostet.

➤ **Zur Abstimmung:** Bestätigung 2025–26 in 4 Mengen mit `--stop 72,1.5,1` (Kriterien S1–S5, besser als REGEL0 in ≥ 3/4 Mengen), Auskunft v = 0/2/4. Danach Auskunft auf der Hebel-Liste.

---

## 7. ⛔ BESTÄTIGUNG 2025–26 (4 Mengen) — Befund 2.702, gemessen 01.10.2026

> **Urteil in einer Zeile:** **Nicht bestätigt, 0 von 4.** Die Zelle 72 h · Stop 1,5 ATR · Verzug 1 h verliert 2025–26 in allen Mengen deutlich
> gegen die REGEL0. **Die REGEL0 bleibt unverändert** (24 h, ohne Stop).

| | bestand | unverzerrt:1 | unverzerrt:2 | unverzerrt:3 |
|---|---|---|---|---|
| ✔ R-R11 REGEL0-Zelle im selben Lauf = Referenz | +0,2708 / +0,583 % | −0,4887 / +0,325 % | −0,4592 / +0,331 % | −0,4065 / +0,345 % |
| **A: Konto log 2025–26** | **−1,62** | **−2,01** | **−1,93** | **−1,99** |
| besser als REGEL0 | ⛔ | ⛔ | ⛔ | ⛔ |
| S1 je Jahr (2025 · 2026) | −1,31 · −0,32 ⛔ | −1,36 · −0,65 ⛔ | −1,41 · −0,52 ⛔ | −1,26 · −0,73 ⛔ |
| S2 über der Nullwelt-P90 | ✔ (−2,01) | ✔ (−2,30) | ✔ (−2,14) | ✔ (−2,26) |
| S4 Hebel gegen Spot | ⛔ | ⛔ | ⛔ | ⛔ |
| Rohvorteil je Handel (REGEL0 → A) | +0,58 → −0,24 % | +0,33 → −0,31 % | +0,33 → −0,29 % | +0,35 → −0,35 % |
| Verzug 0 / 1 / 2 / 4 h | −1,49 / −1,62 / −1,66 / −1,77 | −1,66 / −2,01 / −2,16 / −2,31 | −1,57 / −1,93 / −2,14 / −2,30 | −1,73 / −1,99 / −2,05 / −2,21 |

**Prüfung und Gegenprüfung:**
- ✔ **R-R11:** Die REGEL0-Zelle im selben Lauf trifft in 4 von 4 Mengen die festgeschriebene Referenz.
- ✔ **Unabhängig nachgerechnet:** unverzerrt:1 mit Spur, der Lauf ist zeilengleich. `pruefe_a_stop_unabhaengig.py` ergibt **404 von 404** Einstiegen 2025–26 in allen 5 Zellen gleich, auch am Reihenende eingestellter Paare. Beleg `gegenpruefung__unverzerrt_1.txt`.
- ℹ️ **Fehler im Prüfskript selbst gefunden und behoben:** Es las bei Paaren mit Vorgeschichte (z. B. `A`) nur die neue Reihe. Danach stimmte alles, auch 2024 erneut.

**Was das heißt:**

| | |
|---|---|
| **Die Einstiege tragen weiter** | S2 4/4: Über der Nullwelt derselben Stop-Regel. Gescheitert ist die **Ausstiegsform**, nicht das Signal |
| **Die Wahl lag auf einem Aufwärtsjahr** | 2024 belohnte langes Halten, 2025–26 bestraft es. Schon in der Wahl war der Gipfel schmal (Abschnitt 6) |
| **Der Verzug ist NICHT kostenlos** | 2024 war 1 h Verzug besser, 2025–26 ist der Ausstieg an der Linie besser, und jede weitere Stunde kostet. Die Lehre aus Abschnitt 6 hält also **nicht** |
| **Nicht getrennt** | Ob die **Haltedauer 72 h** oder der **Stop selbst** scheitert, sagt diese Messung nicht. Bestätigt wurde nur die gewählte Zelle |
| **Betrieb** | Kein Trailing-Stop von Hand nötig. Die REGEL0 bleibt 24 h ohne Stop |

➤ **Zur Abstimmung** (Nutzer): wie mit A weiter, siehe Arbeitsstand.
