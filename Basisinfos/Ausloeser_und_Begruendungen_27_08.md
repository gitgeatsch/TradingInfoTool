# Auslöser und Begründungen — alle Stufen, beide Seiten

**Angelegt 27.08.2026.** Nutzervorgabe:

> *„Die Auslöser müssen sorgsam ausgewählt und spezifiziert werden, denn diese
> sollen dann **nicht immer bei Signal auslösen**, sondern dann, wenn eine
> **Begründung** vorhanden ist — und dies nur, wenn ein **hohes Potential /
> Wahrscheinlichkeit** gegeben ist. Das ist auch der Nutzen und das ZIEL."*

Und die harte Randbedingung:

> ⚠️ *„**DER TAKT SOLL NIE SIGNALGEBER SEIN!**"*

---

## 0. Die Bauform, die daraus folgt

Ein Signal entsteht aus **drei** Bedingungen, die alle erfüllt sein müssen:

    1. MESSFENSTER    der Takt erlaubt eine Prüfung   (begrenzt, erzeugt nichts)
    2. AUSLÖSER       ein benennbares Ereignis        (die Begründung)
    3. POTENTIAL      die Wahrscheinlichkeit trägt    (die Selektion)

⚠️ **Der Takt steht bewusst an erster und schwächster Stelle.** Er kann ein
Signal nur *verhindern*, nie *erzeugen*. Heute ist es umgekehrt: der Cooldown
läuft ab, der Fingerabdruck hat sich geändert, und daraus wird ein Signal —
das ist der Zustand, den diese Datei ablöst.

**Die Begründung ist nicht schmückendes Beiwerk, sondern der Auslöser selbst
in Worten.** Wo sich kein Satz formulieren lässt, gibt es keinen Auslöser.

---

## 1. Die Kaufseite

### K1 — Kern (BTC, ETH, SOL): die Lage ist günstig

| | |
|---|---|
| **Bedingung** | Lage ≤ unteres Drittel der letzten 252 Handelstage |
| **Lage** | Mittel aus (Kurs/SMA200 − 1) des Assets und desselben für BTC |
| **Begründung** | *„BTC steht 8 % unter seinem 200-Tage-Schnitt — im unteren Drittel des letzten Jahres"* |
| **Größe** | 300 € × clip(1 − 2,0 × Lage; 0,25; 1,0) |
| **Datenlage** | ✔ **gemessen** — 3.092 Tage BTC, 2.002 SOL |
| **Häufigkeit** | ~70 Signale/Jahr je Asset bei 2-Tage-Messtakt |

⚠️ **Die Schwäche, die bleibt:** Die längste Pause beträgt **376 Tage**. Ein
Lage-Auslöser hat immer lange Pausen, weil Märkte trendieren — das ist die
unvermeidliche Folge davon, dass der Takt nicht auslösen darf.

⚠️ **Und `A1` (Lage < 0 absolut) ist verworfen:** 2022 hätte er an **100 %**
aller Messtage ausgelöst, 2024 an 19,7 %. Die relative Fassung liegt zwischen
15 % und 63 % — noch klumpig, aber brauchbar.

### K2 — Taktisch: Weg frei, Stop gedeckt

| | |
|---|---|
| **Bedingung** | kein Widerstand bis zum Ziel **und** Unterstützung 0,5–2,0 ATR darunter |
| **Begründung** | *„Kein getestetes Niveau bis zum Ziel; Unterstützung bei X liegt 1,2 ATR darunter"* |
| **Datenlage** | ✔ **gemessen** (+4,5 Punkte gegen Zufallsschwelle +2,6, 523 Reihen) |
| ⚠️ **Status** | **Schatten bis ~19.09.2026** — markiert, sperrt nicht |
| **Häufigkeit** | 3,3 % der Ankertage |

### K3 — Zyklisch: ⚠️ LÜCKE

„Nachkauf an einem starken Level" ist **nicht spezifiziert**. Drei Kandidaten,
alle ungemessen:

| | Kandidat | Bewertung |
|---|---|---|
| a | dieselbe Lage-Regel wie K1, strengerer Schnitt (unteres Fünftel) | ✔ nutzt Gemessenes, nur andere Schwelle |
| b | „Boden gehalten" (`Definition_Boden_gehalten_27_08.md`) | ⚠️ nicht gebaut, nicht gemessen |
| c | K2 mit gelockerten Grenzen | ⚠️ verwässert einen gemessenen Filter |

**Vorschlag: (a)** — dieselbe Mechanik, andere Schwelle. Das erspart einen
zweiten Baustein und ist mit derselben Messung belegt.

### K4 — Core-Klassen (Aktien 2, Rohstoffe 4, ETF 7): ⚠️ LÜCKE

⚠️ **Und sie ist nicht durch Code zu schließen (C1).** Bei 2–7 Symbolen je
Klasse ist keine Messung möglich. Ehrliche Optionen: dieselbe Regel wie Krypto
übernehmen (ungeprüft) oder die Klassen ausdrücklich als **unbewertet**
führen.

---

## 2. Die Verkaufsseite — der eigentliche Engpass

⚠️ **Der Ausgangspunkt ist ein Nullbefund:** O-29 hat gemessen, dass **kein
Merkmal Verkaufen von Halten trennt** (alle p > 0,47) — und dass verkauft
werden die **besseren** Positionen. Was hier steht, ist deshalb **fachlich
hergeleitet, nicht gemessen**, und muss vor dem Scharfschalten geprüft werden.

**Die gute Nachricht ist die Datenlage:** von 266 offenen Signalen tragen
**262 einen Widerlegungspreis** und **258 eine Take-Profit-Zone**.

### V1 — These gebrochen (alle Stufen)

| | |
|---|---|
| **Bedingung** | Kurs unterschreitet den Widerlegungspreis des **jüngsten** Signals |
| **Begründung** | *„Das Modell hat am 23.08. gesagt: unter 42,10 € trägt die These nicht mehr. Der Kurs steht bei 40,80 €."* |
| **Datenlage** | ✔ **262 von 266** Signalen tragen den Preis |
| **Warum der jüngste** | er beurteilt die aktuelle Lage; ältere Thesen sind überholt |

⚠️ **Für `akkumulation` ist das laut `handelsauftrag.py` das EINZIGE
Ausstiegskriterium** — *„wo Einstieg und Swing einen Stop haben, hat die
Akkumulation nur die Frage: wann trägt die Erwartung nicht mehr"*.

⚠️ **Und ein Vorbehalt aus der Quelle:** `umgeworfen_durch` ist Prosa. Der
Kurs darin ist prüfbar, eine Zusatzbedingung wie *„bei steigendem Volumen"*
nicht. Deshalb wird der Satz **gezeigt**, nicht stillschweigend als erfüllt
behandelt.

### V2 — Ziel erreicht (taktisch, zyklisch)

| | |
|---|---|
| **Bedingung** | Kurs erreicht die Take-Profit-Zone |
| **Begründung** | *„Ziel bei 51,00 € erreicht — geplant war ein CRV von 2,1"* |
| **Datenlage** | ⚠️ **258 von 266 tragen die Zone — aber sie wird NICHT gegen den Kurs geprüft.** `take_profit` kommt nur in `backward_tracking` vor, also **rückblickend zur Erfolgsmessung**. Als Auslöser ist V2 **nicht gebaut** |
| ⚠️ **Nicht für den Kern** | dort gibt es per Definition kein nahes Ziel |

### V3 — Überbewertung (Kern, zyklisch): Teilverkauf

| | |
|---|---|
| **Bedingung** | Lage ≥ oberes Fünftel der letzten 252 Tage **und** Fear-&-Greed > 75 |
| **Begründung** | *„SOL steht 48 % über seinem 200-Tage-Schnitt, im obersten Fünftel des Jahres, bei Extreme Greed (81)"* |
| **Größe** | ein Drittel (`TEIL_ANTEIL`, vorhanden) |
| **Datenlage** | ⚠️ **Daten vorhanden** (3.125 F&G-Tage), **Wirkung ungemessen** |

**Warum zwei Bedingungen:** Extreme Greed allein ist ein Marktzustand, die
Lage allein eine Kursaussage. Erst zusammen sagen sie *„dieser Wert ist teuer,
und die Stimmung trägt es"*. Extreme Greed hat **64 Phasen in 8,5 Jahren,
Median 1 Tag** — es ist ein Ereignis, kein Dauerzustand, und damit als
Auslöser tauglich (anders als Fear mit bis zu 151 Tagen am Stück).

### V4 — Klumpenrisiko (alle Stufen): Teilverkauf

| | |
|---|---|
| **Bedingung** | Position > Zielanteil × Faktor (z. B. 2×) |
| **Begründung** | *„LINK ist auf 10,3 % des Bestands gewachsen; Zielanteil für zyklische Werte ist 5 %"* |
| **Datenlage** | ✔ **direkt rechenbar** aus `positionsfuehrung` |
| ⚠️ **Fehlt** | die **Zielallokation** — sie ist eine Nutzerentscheidung, keine Messung |

**Der heutige Stand, gemessen (29 Positionen, 13.198 €):**

| | Anteil |
|---|---:|
| BTC | **26,1 %** |
| ETH | 15,2 % |
| LINK | 10,3 % |
| Median-Position | ⚠️ **1,1 %** |
| bei Gleichgewicht | 3,4 % |

⚠️ **Die Konzentration auf den Kern ist bei einer Core-Satellite-Struktur
richtig.** Das eigentliche Auffällige ist die Gegenseite: die halbe Watchlist
steht mit Kleinstpositionen um 145 € im Bestand — zu klein, um zu wirken, zu
viele, um sie zu verfolgen.

### V5 — Vollverkauf: ⚠️ bewusst KEIN eigener Auslöser

Ein Vollverkauf entsteht **nur** aus V1 (These gebrochen) und dort **nicht für
den Kern**. Ein eigener Auslöser „alles verkaufen" existiert nicht — er wäre
eine Prognose, und Prognosen trägt dieses System nicht.

---

## 2b. ⚠⚠ SCHIEFSTAND: die Spot-Verkaufs-Roadmap gilt als erledigt — sie ist verloren

**Nutzerhinweis 27.08.:** *„schau in der Doku bei Verkauf und Ausstieg —
denke hier haben wir auch einen Schiefstand."* Er trifft zu.

Am 01.08. wurde eine **fünfstufige Roadmap** gegen die Spot-Verkaufs-Lücke
umgesetzt — Anlass: **0 von 1.142** Krypto-Spot-Signalen waren je VERKAUFEN
(98,2 % HALTEN). Root Cause laut vier parallelen Recherche-Agenten: **kein
Gate-Problem, sondern Prompt-Bias**. Der Memory-Eintrag sagt:
*„ROADMAP VOLLSTÄNDIG ABGESCHLOSSEN"*.

⚠️ **Alle vier umgesetzten Schritte hängen an `agent/krypto/analyst.py`
(Regeln 7/17/27/33) und am `budget_allocator` — also an der ALTEN Kette.**

| Schritt | laut Doku | tatsächlich in der Rollen-Kette |
|---|---|---|
| 1 `halte_kriterium` scharfschalten | umgesetzt + committet | ⚠️ **wird nicht mehr gefüllt — 1 von 266** |
| 2 VERKAUFEN-vs-HALTEN-Abwägung (Regel 27) | erledigt | ⚠️ **kein Treffer** |
| 3 Ausweitung auf Aktien/Rohstoffe/ETF | erledigt | ⚠️ betraf die alten Pipelines |
| 4 Z.ai-Re-Evaluierung | erledigt | ⚠️ hängt am `budget_allocator`, der für Rollen-Klassen **übersprungen** wird |

**Was das NICHT heißt:** Die Rollen-Kette verkauft durchaus — REDUZIEREN und
VERKAUFEN kommen vor, anders als die 0 von 1.142 der alten Kette. **Das
Problem wurde gelöst, nur anders als dokumentiert.** Die benannten Bausteine
existieren nicht mehr; was heute verkauft, ist die Ausstiegsrechnung und das
LLM-Urteil.

⚠️ **Der Schaden ist die Doku, nicht der Betrieb:** Wer die Roadmap liest,
hält `halte_kriterium` für scharf und plant darauf. Genau das ist mir beim
ersten Entwurf dieser Datei passiert — V2 stand als „vorhanden".


---

## 3. Die Potential-Schwelle — die Selektion

⚠️ **Ein Auslöser allein erzeugt noch kein Signal.** Nach der Nutzervorgabe
kommt es nur, *„wenn ein hohes Potential / Wahrscheinlichkeit gegeben ist"*.

**Der Rahmen existiert:** `wahrscheinlichkeit.rechne()` liefert `quote` =
Basisrate aus der Geometrie plus gemessene Beiträge.

⚠️ **UND HIER GILT DIE ZWEI-EBENEN-TRENNUNG (Nutzervorgabe 27.08.):**

| Ebene | Größe | Gebühren | wofür |
|---|---|---|---|
| **Bewertung** | `quote` | ⚠️ **keine** | Auslöser, Rangfolge, Selektion |
| **Wirtschaftlichkeit** | `abstand_punkte`, `erwartungswert_r` | BP-Satz 1,50 % | die Auskunft an den Nutzer |

**Geprüft am 27.08.:** Heute filtert **keine** Stelle nach der
gebührenbehafteten Größe. ⚠️ Aber nur, weil die ganze Ebene nichts entscheidet
(*„sie sperren nichts"*). **Sobald `quote` zum Rangkriterium wird, muss die
Trennung im Code verankert sein, nicht in der Absicht.**

⚠️ **Was heute fehlt, damit die Schwelle wirken kann:** Von vier registrierten
Beiträgen **trägt genau einer** (Vorfilter, +4,5 Punkte) — und der ist bis
19.09. im Schatten. Eine Selektion auf dieser Basis wäre eine Selektion nach
einem einzigen Merkmal.

---

## 4. Die Matrix — Stand

| Stufe | KAUFEN | TEILVERKAUF | VERKAUFEN | HALTEN |
|---|---|---|---|---|
| **Kern** | ✔ K1 *gemessen* | ⚠️ V3 *Daten da, Wirkung offen* · ✔ V4 *rechenbar* | ✘ per Definition nie | Rest |
| **Zyklisch** | ⚠️ K3 *Lücke, Vorschlag (a)* | ⚠️ V3 · ✔ V4 | ✔ V1 *262/266* | Rest |
| **Taktisch** | ✔ K2 *gemessen, Schatten* | ✔ V4 | ✔ V1 · ⚠️ V2 *Daten da, Prüfung fehlt* | Rest |
| **Core-Klassen** | ⚠️ K4 *C1, nicht lösbar* | ✔ V4 | ✔ V1 | Rest |
| **Hedge** | ⚠️ Exposure *nie definiert* | ⚠️ Lücke | ⚠️ Lücke | 97,2 % gesperrt |

**Von 20 Zellen sind jetzt 11 besetzt** (vorher vier), davon **vier gemessen**,
sechs rechenbar-aber-ungemessen und **eine (V2) nur als Datenfeld ohne
Prüfung**. **Die Verkaufsseite ist damit erstmals
besetzt** — auf Datenlage, nicht auf Messung.

---

## 5. Was vor der Umsetzung zu entscheiden ist

| # | Frage | Wer |
|---|---|---|
| **1** | **Zielallokation je Stufe** (Kern x %, zyklisch y %, taktisch z %) | ⚠️ **Nutzer** — keine Messfrage |
| **2** | K3: Vorschlag (a) — Lage-Regel mit strengerem Schnitt? | Nutzer |
| **3** | Core-Klassen: Krypto-Regel übernehmen oder als unbewertet führen? | Nutzer |
| **4** | Hedge: Exposure-Auslöser definieren oder Klasse ruhen lassen? | Nutzer |
| **5** | Potential-Schwelle: ab welcher `quote` darf ein Auslöser feuern? | ⚠️ erst sinnvoll, wenn mehr als ein Beitrag trägt |
| **6** | Die vielen Kleinstpositionen (Median 145 €) — auflösen? | Nutzer |

⚠️ **Ohne 1 kann V4 nicht rechnen, ohne 5 wirkt die Selektion nicht.** Alles
Übrige ließe sich mit dem Vorhandenen bauen.

Verwandt: `Entscheidung_Kern_Staffelung_27_08.md` ·
`Bestandsaufnahme_Positionsfuehrung_26_08.md` · `agent/positionsfuehrung.py` ·
`agent/wahrscheinlichkeit.py` · `agent/handelsauftrag.py`
