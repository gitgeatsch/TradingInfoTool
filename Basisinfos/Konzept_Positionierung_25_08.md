# Terminmarkt-Positionierung — der erste Kandidat außerhalb des ATR-Kanals

**Angelegt 25.08.2026.** Auftrag: *„die ganze Familie messen, nicht nur die
OI-Divergenz — vorerst nicht zu sehr einengen."*

---

## 0. Zusammenfassung in vier Sätzen

Die Wirkungsmessung ist **heute nicht durchführbar** — die Datenlage reicht
37 Tage, der Betriebshorizont ist 120 Handelstage. Was heute geht und vor
jeder Sammelzeit stehen muss, ist die **Vorbedingung**: trägt die
Positionierung Information, die nicht schon in der Kursreihe steht? **Drei
von vier Größen tun das** — und damit ist es der erste Kandidat des Projekts,
der nicht der ATR-Kanal in neuer Verkleidung ist. Die Wirkungsmessung wird ab
**22.10.2026** (Horizont 20) bzw. **11.03.2027** (Betriebshorizont 120)
möglich, **wenn die Sammlung durchläuft.**

---

## 1. ⚠️ Eine Korrektur vorweg

In der Bestandsaufnahme vom 25.08. stand, `open_interest_snapshot` werde
*„seit Monaten im 15-Minuten-Takt befüllt"* und sei *„messbar heute, ohne
Sammelzeit"*. **Das war nicht an der Quelle geprüft.** Gemessen:

| | |
|---|---|
| Desktop-Kopie `tradinginfotool.db` | **227 Zeilen**, 14.–19.07.2026, dann nichts |
| NB-Export `oi_historie` | **184.584 Zeilen**, 39 Symbole, 4 Börsen — aber **37 Tage** |
| Produktion (Notebook) | läuft, letzter Erfolg **24.08.2026** |

Die Sammlung läuft also — aber sie läuft **erst seit dem 14.07.2026**.

---

## 2. Warum die Wirkung heute nicht messbar ist

Ein Anker braucht bis zu 120 Handelstage bis zu seinem Ausgang. Gerechnet:

| Horizont | Anker mit aufgelöstem Ausgang | |
|---:|---:|---|
| 5 HT | 1.053 | dünn |
| 10 HT | 936 | dünn |
| 20 HT | 390 | zu wenig |
| 60 HT | **0** | unmöglich |
| **120 HT** (Betrieb) | **0** | unmöglich |

⚠️ **Und die härtere Grenze:** alle Anker liegen in **einem 41-Tage-Fenster**.
Eine Marktphase, keine Blockstruktur, keine Zeitteilung. Ein Ergebnis wäre
hier nicht „dünn", es wäre **nicht interpretierbar** — genau der Fehler, den
das Projekt bei Kapitel 105 schon einmal gemacht hat („Phasenprobe
ausgefallen, nicht bestanden").

---

## 3. Was heute geht: die Kanalprüfung

**Die teure Lektion, die dahintersteht.** Der ATR-Kanal trat **fünfmal unter
neuem Namen** auf — Kap. 100 (Marktphase), 101 (Geometrie), 102/113 (Drift),
111 (Hochabstand), 116 (Liquidität). Jedes Mal sah es nach einem neuen
Merkmal aus, jedes Mal war es dieselbe Größe. **Wer das nicht vorher prüft,
sammelt Monate und misst am Ende die Volatilität.**

`pruefe_positionierung_kanal.py`, 585 auswertbare (Symbol, Tag)-Punkte aus 28
Symbolen:

### 3.1 Variieren die Größen überhaupt?

| Größe | n | Median | 10 % | 90 % |
|---|---:|---:|---:|---:|
| `oi_aenderung` | 558 | +0,00035 | −0,03825 | +0,04539 |
| `oi_divergenz` | 542 | 0,04705 | 0,01669 | 0,12545 |
| `funding_rate` | 453 | 0,00000 | −0,00010 | +0,00002 |
| `long_anteil` | 585 | 57,85 | 45,56 | 70,12 |

Alle vier variieren — anders als `regime` und `optionsmarkt_skew`, die über
1.022 Fälle **konstant** waren und deshalb nichts tragen konnten.

### 3.2 Die Kernfrage: Rangkorrelation zu den Kursgrößen

| Größe | ATR relativ | Umsatz rel. | Rendite | max \|ρ\| | Urteil |
|---|---:|---:|---:|---:|---|
| **`oi_aenderung`** | −0,016 | +0,024 | −0,034 | **0,034** | **EIGENER KANAL** |
| **`oi_divergenz`** | +0,195 | +0,158 | −0,054 | **0,195** | **EIGENER KANAL** |
| **`funding_rate`** | −0,250 | −0,013 | +0,101 | **0,250** | **EIGENER KANAL** |
| `long_anteil` | **−0,561** | +0,129 | +0,107 | 0,561 | teilweise überlappend |

**Vorab festgelegte Schwellen:** < 0,3 = eigener Kanal · 0,3–0,6 = teilweise
überlappend, später gegen die Kursgröße zu bereinigen · ≥ 0,6 = der ATR-Kanal
zum sechsten Mal, erledigt.

⚠️ **`oi_aenderung` mit max \|ρ\| = 0,034** ist praktisch unkorreliert zu
allem, was aus der Kursreihe kommt. Das gab es in diesem Projekt noch nicht.

⚠️ **`long_anteil` korreliert −0,561 mit dem ATR.** Nicht erledigt, aber die
Wirkungsmessung muss dort später gegen die Volatilität bereinigt werden.

### 3.3 Was diese Prüfung ausdrücklich NICHT sagt

Sie sagt **nichts über Wirkung**. Ein eigener Kanal zu sein ist die
**Vorbedingung** dafür, nicht der Nachweis. Wer aus einem niedrigen ρ eine
Handelsregel ableitet, hat nichts gemessen. Alle bisherigen Nullbefunde des
Projekts waren Größen, die durchaus variierten und durchaus eigenständig
waren — und trotzdem nicht trugen.

---

## 4. Termine — ab wann die Wirkung messbar wird

Ziel: **2.000 aufgelöste Anker.** Unterhalb davon war in diesem Projekt keine
Messung belastbar.

| Horizont | nötige Ankertage | messbar ab |
|---:|---:|---|
| 5 HT | 52 | **01.10.2026** |
| 10 HT | 52 | 08.10.2026 |
| **20 HT** | 52 | **22.10.2026** |
| 60 HT | 52 | 17.12.2026 |
| **120 HT** (Betriebshorizont) | 52 | **11.03.2027** |

⚠️ **Auch dann bleibt der Vorbehalt der Marktphase.** Bis zum 22.10. liegen
etwa drei Monate vor; ob darin ein Regimewechsel steckt, entscheidet, ob das
Ergebnis mehr ist als eine Momentaufnahme. Ein erster Blick mit Horizont 20
wäre **vorläufig**, nicht abschließend.

---

## 5. Was jetzt zu tun ist

1. **Die Sammlung sicherstellen.** Sie läuft am Notebook (letzter Erfolg
   24.08.), am Desktop endete sie am 19.07. Ohne durchgehende Sammlung
   verschieben sich alle Termine.
2. **Nichts scharf schalten.** Es gibt keinen Wirkungsnachweis — und nach
   N-6 auch keine Grundlage für einen Eingriff.
3. **Termin 22.10.2026 vormerken** für den ersten vorläufigen Blick
   (Horizont 20), **11.03.2027** für den Betriebshorizont.
4. **`long_anteil` gesondert behandeln:** bei der Wirkungsmessung gegen den
   ATR bereinigen, sonst misst man die Volatilität.
5. **Die 11 Symbole ohne Kursreihe** in `messdaten.db` prüfen — 236 von 833
   Punkten fielen deshalb weg. Für die spätere Messung ist das relevant.

---

## 6. Einordnung

Das Projekt hat seit Monaten einen Grundbefund: *aus der Kursreihe allein ist
für dieses Barrierensystem keine Regel zu gewinnen, die außerhalb ihrer
eigenen Daten trägt.* Alle bisherigen Kandidaten kamen aus dieser einen
Quelle — deshalb tauchte der ATR-Kanal fünfmal auf.

**Die Terminmarkt-Positionierung ist die erste Familie, die nachweislich
woanders herkommt.** Das macht sie nicht wirksam. Es macht sie zur ersten,
bei der das Sammeln überhaupt eine Chance hat, etwas Neues zu finden.

Verwandt: `Befundkarte.md` §7.1 · `Konzept_Nachrichten_24_08.md` ·
`Vorabfestlegung_S1_S4_H_Annahmen_25_08.md` (warum H ausgereizt ist)
