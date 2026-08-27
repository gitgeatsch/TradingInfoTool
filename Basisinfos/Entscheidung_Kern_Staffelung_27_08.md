# Entscheidung: die Kern-Staffelung — Form, Bezug, Betrag

**Angelegt 27.08.2026.** Ergebnis einer Kette von Messungen und
Gegenprüfungen; alle Entscheidungen vom Nutzer getroffen.

⚠️ **Diese Datei beschreibt eine ENTSCHEIDUNG, keinen gebauten Zustand.**
Umgesetzt ist davon **nichts**. Was gebaut ist, steht in Abschnitt 6.

---

## 1. Die Entscheidungen in einer Tabelle

| | Festlegung | Begründung |
|---|---|---|
| **Kern-Assets** | **BTC, ETH, SOL** | Nutzervorgabe; der GUI-Schalter nennt seit Wochen genau diese drei |
| **Strategie** | **`akkumulation`** | vorhanden in `handelsauftrag.py`, nie gesetzt |
| **Auslöser** | **Zeittakt**, nicht Ereignis | Nutzerentscheidung: *„Staffelung wie in akkumulation beschrieben, das passt zur Praxis"* |
| **Takt** | 14 Tage *(Vorschlag)* | ⚠️ nicht gemessen, nur der Simulation entnommen |
| **Größenform** | **begrenzt: Faktor 0,25 … 1,0** | respektiert die Dämpfer-Bauform: *„eine Überexposition können sie nicht erzeugen"* |
| **Bezug** | **Mittel aus BTC-Lage und eigener Lage** | über beide Zeiträume robust; einzeln je Zeitraum wechselnd |
| **Steilheit** | **2,0** | ⚠️ gesetzt, mit Empfindlichkeitsprüfung belegt (Abschnitt 4) |
| **Grundbetrag** | **300 €** | Nutzerfestlegung 27.08.: *„grundbetrag bis 300 ist ok"* |
| **Name** | ⚠️ **NICHT `k`** — Vorschlag `lage_steilheit` | drei Größen im Projekt heißen bereits `K`, alle mit Wert 2 |
| **Ort** | Eintrag in `agent/daempfer.py` | dort steht die Größenanpassung bereits |

**Die Formel:**

    abstand   = Mittel( Kurs/SMA200 - 1  je Asset,  dasselbe fuer BTC )
    faktor    = clip(1 - 2,0 * abstand,  0,25,  1,0)
    tranche   = 300 EUR * faktor

---

## 2. Was die Regel praktisch tut

⚠️ **Sie ist zu 65 % geklemmt** — und das ist keine Schwäche, sondern ihre
eigentliche Beschreibung:

| | Anteil der Tage |
|---|---:|
| Faktor = 1,0 (Kurs **unter** dem Schnitt) | **47,6 %** |
| frei dazwischen | 35,3 % |
| Faktor = 0,25 (sehr teuer) | 17,1 % |

> **In Worten: „voller Betrag, außer es ist teuer."**

| Lage | Abstand | Faktor | Tranche |
|---|---:|---:|---:|
| sehr günstig | −32 % | 1,00 | **300 €** |
| Median | +3 % | 0,94 | 281 € |
| sehr teuer | +64 % | 0,25 | **75 €** |

Mittlerer Faktor **0,747** → mittlere Tranche rund **224 €**.
⚠️ **Das sind etwa 10 % weniger als starres DCA mit 250 €.** Wer denselben
Einsatz wollte, bräuchte rund 335 € Grundbetrag; der Nutzer hat 300 € als
Obergrenze gesetzt.

---

## 3. Was gemessen wurde — und was die Messung trägt

**Aufbau:** `simuliere_staffelung.py`, Kursreihen aus `messdaten.db`,
BTC/ETH/SOL, alle möglichen Startpunkte (2.812 bzw. 796), Takt 14 Tage.
**Erfolgsmaß: Endvermögen je eingesetztem Euro** — das Maß, das
`handelsauftrag.py` der Akkumulation ausdrücklich zuweist
(*„Durchschnittskurs und Endvermögen statt Ziel vor Stop"*).

⚠️ **Und das ist der Grund, warum diese Messung nicht an N-10 scheitert:**
Sie braucht weder Barriere noch Trefferquote. Alle bisherigen Nullbefunde
hingen an „Ziel vor Stop", das per Konstruktion auf die Basisrate fällt.

### 3.1 Die begrenzte Form (die getroffene Entscheidung)

| Symbol | Median gegen fest | 5. Perzentil gegen fest | Einsatz |
|---|---:|---:|---:|
| BTC | +2,5 % | +3,1 % | −11 % |
| ETH | +6,7 % | +7,1 % | −14 % |
| SOL | +4,1 % | +7,2 % | −9 % |

**Positiv über alle drei Symbole und beide Zeiträume.**

⚠️ **Der Vorteil im 5. Perzentil ist durchgehend GRÖSSER als im Median.**
Das ist die wichtigste Eigenschaft: **die Regel mindert Risiko, sie steigert
nicht primär Rendite.** Sie wirkt dort am stärksten, wo der feste Betrag am
meisten verliert — wenn man sonst überwiegend teuer gekauft hätte.

### 3.2 Was verworfen wurde

| | Variante | Warum verworfen |
|---|---|---|
| **V3** | „nie teurer als zuletzt" | ⚠️ **verstummt vollständig** — bei BTC und ETH kam über den ganzen Zeitraum keine einzige gültige Simulation mit ≥ 20 Käufen zustande. Nutzereinwand belegt |
| **frei bis 2,5** | Faktor darf verstärken | doppelter Vorteil, ⚠️ bricht aber mit *„Dämpfer können keine Überexposition erzeugen"* — und setzt in Tiefphasen bis 625 € je Tranche ein |
| **D** | max 1,0 mit angehobenem Grundbetrag | ⚠️ **im normierten Maß identisch mit der begrenzten Form** — die Skalierung kürzt sich heraus. Und die Out-of-sample-Kalibrierung überschoss (mittlerer Faktor 0,74 vorher gegen 0,89 in der Testperiode → +20 % Einsatz statt ±0) |

---

## 4. Die Gegenprüfungen — und was sie eingeschränkt haben

### 4.1 Endzeitpunkt (die schwerste Einschränkung)

Dieselbe Rechnung mit sechs verschiedenen Endzeitpunkten, freie Form:

| Ende | BTC | ETH | SOL |
|---|---:|---:|---:|
| 2021-11 | +17,1 % | +22,5 % | — |
| **2022-11** | +1,9 % | ⚠️ **−4,8 %** | +12,5 % |
| **2023-10** | +6,3 % | ⚠️ **−8,6 %** | ⚠️ **−6,6 %** |
| 2024-12 | +14,4 % | +10,5 % | +11,0 % |
| 2026-08 | +10,2 % | +7,8 % | +6,4 % |

⚠️ **In 3 von 17 Zellen ist die Anpassung schlechter als der feste Betrag.**
Sie ist ein **Hebel auf die Rückkehr zum Mittel**: Sie kauft mehr, wo es
billig ist. Kommt die Erholung, gewinnt sie; bilanziert man im Tief, verliert
sie. **Für einen Kern, der über Jahre gehalten wird, ist das vertretbar — für
einen Trade wäre es das nicht.**

### 4.2 Steilheit

| Steilheit | BTC | ETH | SOL | Anteil **stetig** |
|---:|---:|---:|---:|---:|
| 1,0 | +5,5 % | +4,0 % | +3,9 % | 94 % |
| **2,0** | +10,2 % | +7,8 % | +6,4 % | **84 %** |
| 3,0 | +13,6 % | +10,4 % | +6,7 % | 75 % |
| 5,0 | +16,7 % | +12,4 % | +7,2 % | 56 % |
| 10,0 | +16,0 % ↓ | +12,3 % ↓ | +8,0 % | ⚠️ **27 %** |

**Die Monotonie läuft bei ~5 aus** — es gibt ein Plateau, kein unbegrenztes
Wachstum. Der Verdacht „je extremer desto besser = Artefakt" ist entkräftet.

⚠️ **Der Grund für 2,0 ist nicht der beste Median, sondern die Stetigkeit.**
Der gemessene Befund lautet: *„der Marktzustand gehört als **stetige** Größe
hinein, **nie als Schalter**"*. Bei Steilheit 5 ist bereits ein Drittel
geklemmt; der Charakter kippt zum Schalter.

### 4.3 Der Bezug — nicht entschieden, deshalb das Mittel

| | 2018–2026 | ab 2024 |
|---|---|---|
| BTC-Lage (ETH) | +7,1 % | +6,0 % |
| eigene Lage (ETH) | +8,8 % | ⚠️ **+11,0 %** |
| BTC-Lage (SOL) | **+4,0 %** | +8,4 % |
| eigene Lage (SOL) | +1,3 % | +8,8 % |

Für **BTC sind beide identisch** — das war die Rechenkontrolle, und sie ist
bestanden. Für ETH und SOL wechselt die bessere Wahl je Zeitraum. **Das
Mittel ist nie das Beste, aber nie das Schlechteste** — und es korrelieren
ETH/BTC nur mit 0,84, SOL/BTC mit 0,69 (mittlere Differenz 41,8 %), die Wahl
ist also nicht folgenlos.

⚠️ **Damit weicht der Bezug von der ursprünglichen Nutzerwahl (a: BTC-Lage)
ab.** Grund: Die Prüfung „nur 2024 bis heute" auf Nutzervorgabe zeigte die
eigene Lage vorn. Das Mittel ist der Kompromiss aus beiden Befunden.

---

## 5. ⚠️ Die Fallstricke, die dabei aufgedeckt wurden

**Der Nutzer hat sie angefordert** (*„das K ist in mehreren Bereichen zentral —
prüfe detailliert, ob wir hier nicht wieder einen Fallstrick haben"*), und sie
waren da:

| | Bereits belegt im Projekt | Bedeutung |
|---|---|---|
| `messe_marken.py:79` | `K = 2.0` | **Stopabstand in ATR** |
| `agent/auswahl.py:72` | `K_GROSS = 2` | **Anzahl ausgewählter Symbole (A1)** |
| `messe_geometrie.py` | `K_WERTE` 1,5–4,0 | Stopabstände |
| `trichter.py` | `FAKTOR_JE_KLASSE` | Trichterweiten |

**Drei Größen heißen bereits `K`, alle mit dem Wert 2.** Und für A1s `k` ist
laut Memory offen, ob es begründbar ist — ein Streit, der mit dieser Größe
nichts zu tun hat. **Deshalb: nicht `k` nennen.**

**Und der schwerere Fund:** `agent/daempfer.py` ist bereits die
Positionsgrößen-Anpassung — mit gemessenen Einträgen (CRV-Abstufung:
SQN +0,63 → +1,36, Rückschlag 36,3 → 27,1 R), stillgelegten (Konfidenz,
Regime-Konflikt) und einer Aufnahmeregel. **Die neue Größe gehört dort hinein,
nicht daneben.**

---

## 6. Was davon gebaut ist — und was fehlt

| | Baustein | Status |
|---|---|---|
| Kern-Assets festlegen | GUI-Schalter | ✔ **vorhanden**, BTC/ETH/SOL |
| Schalter wird geprüft | `asset_schalter.py:119` | ✔ vorhanden |
| Strategie `akkumulation` | `handelsauftrag.py` | ✔ definiert |
| Betrag je Strategie | `betraege.py` | ✔ vorhanden (250 €, wäre auf 300 zu ändern) |
| Größenanpassung | `daempfer.py` | ✔ Rahmen vorhanden |
| **`strategie = "akkumulation"` setzen** | — | ⚠️ **niemand — das ist die eine Lücke** |
| **Der Lage-Faktor** | — | ⚠️ **nicht gebaut** |
| **Zeittakt für den Kern** | — | ⚠️ **nicht gebaut** |

⚠️ **Solange `strategie` in 0 von 7.294 Signalen auf `akkumulation` steht,
greift nichts davon** — auch der vorhandene Schalter nicht.

---

## 7. Was offen bleibt

| # | Offen | Anmerkung |
|---|---|---|
| **1** | Takt 14 Tage | ⚠️ nicht gemessen, nur angenommen |
| **2** | Teilverkauf bei Extreme Greed | Daten vorhanden (3.125 Tage), Wirkung ungemessen |
| **3** | Auslöser für **zyklisch** und **taktisch** | diese Entscheidung betrifft nur den Kern |
| **4** | „Boden gehalten" | ⚠️ **für den Kern nicht mehr nötig** — siehe `Definition_Boden_gehalten_27_08.md`; bliebe allenfalls für die taktische Stufe |
| **5** | Position je Symbol statt je Signal | ⚠️ **muss vor dem Scharfschalten kommen** — sonst erzeugt jeder Takt ein weiteres Signal auf denselben Bestand (77 % Doppelungen) |

Verwandt: `Bestandsaufnahme_Positionsfuehrung_26_08.md` ·
`Definition_Boden_gehalten_27_08.md` · `agent/handelsauftrag.py` ·
`agent/daempfer.py` · `simuliere_staffelung.py`
