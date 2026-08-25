# Messkonzept: Funktioniert die LLM-Kette? — und ein Messstandard, der das dauerhaft beantwortet

*Nutzervorgabe 25.08.2026: „mach das Messkonzept — u. U. müssen wir mit
Unschärfen leben bzw. mit einer Simulation die LLM-Ablaufkette prüfbar machen.
Hier würde ich sogar vorschlagen, einen **eigenen LLM-Messstandard bzw.
Standardprüfung** einzuführen, um dies vergleichbar zu machen — mit
Vorher-Nachher-Vergleichen."*

**Beantwortet N-7** aus dem Zwischenstand-Nachtrag vom 25.08.

---

## 0. Die Antwort auf Ihre Frage zur Produktion, gleich vorweg

> **Nein — die Produktion muss für Stufe 1 NICHT angehalten werden.**

Die entscheidende Messung läuft auf **Altdaten**, ohne einen einzigen
Modellaufruf. Die Datenlage habe ich an der Notebook-Produktionsdatenbank
geprüft (Backup 24.08., 16:15):

| | |
|---|---|
| Signale der neuen Kette (`quelle_kette='rollen'`) | **1.997** |
| davon aufgelöst | **1.783** |
| Symbole | **54** |
| Zeitraum | 14.08. – 24.08.2026 (10 Tage) |
| **Einstiege** (ERÖFFNEN 881 · NACHKAUFEN 271 · KAUFEN 140) | **1.292** |

**Das ist genug für eine belastbare Aussage** — und es liegt bereits vor.
Erst **Stufe 3** (Wiederholungsmessung mit echten Aufrufen) braucht Kontingent;
dort komme ich auf Sie zurück.

---

## 1. Die Frage — präzise, in drei Teilen

Die stehende Vorgabe lautet: *„Die LLM-Ebene muss den Zufall messbar
schlagen."* Für die **heutige** Kette ist das unbeantwortet. Zu klären ist:

| # | Frage | Vergleichsmaßstab |
|---|---|---|
| **F1** | Schlägt die LLM-Auswahl den **quotengleichen Zufall**? | Zufall, der **gleich viele** Einstiege zieht |
| **F2** | Schlägt sie eine **einfache Regel**? | Kurs über/unter EMA-200 |
| **F3** | Trägt das **Urteil** überhaupt bei — oder entscheidet die Vorauswahl? | dieselben Anker, Urteil weggelassen |

⚠️ **F3 ist die eigentlich wichtige Frage.** Seit A1 wählt der Rangplatz aus,
*welche* Werte beurteilt werden. Wenn die Kette trägt, könnte das an der
**Auswahl** liegen und nicht am **Urteil**. F1 und F2 allein könnten also ein
gutes Ergebnis zeigen, das dem LLM gar nicht gehört.

---

## 2. ⚠️ Das Erfolgsmaß — und warum es NICHT „Ziel vor Stop" ist

**Nutzervorgabe N-5 vom selben Tag:**

> „Ein guter Trade ist dann gegeben, wenn für dieses Asset eine bestimmte
> Handlungsempfehlung — Grund — eintritt. **NICHT** ob der Trade bei einer
> Börse wirtschaftlich ist — also Fokus auf das **Asset und das Potential**."

**Gemessen wird deshalb das POTENTIAL:**

| | |
|---|---|
| **Maß** | Bewegung über einen **festen Horizont**, barrierenfrei und **brutto** |
| **Horizonte** | 5 und 20 Handelstage (dieselben wie bei A1 — vergleichbar) |
| ⚠️ **NICHT** | „Ziel vor Stop" — fällt per Konstruktion auf `1/(1+CRV)` und misst unsere eigene Zielregel zurück |
| ⚠️ **NICHT** | Gebührendeckung / Breakeven — das ist Geldrechnung der Mail, nicht Bewertungsmaßstab (N-5) |
| **Marktbereinigt** | ja — der Mittelwert über eine Klasse *ist* der Markt und muss null ergeben |

**Die Marktbereinigung ist hier zwingend**, weil der Messzeitraum einen
**Regimewechsel** enthält (Markt drehte am 22.08., BTC +23 %). Ohne sie würde
gemessen, dass der Markt gestiegen ist — nicht, dass das Modell gut war.

---

## 3. Der Messstandard — Ihre Idee, ausgearbeitet

**Das Prinzip existiert im Projekt bereits**, im Kanarienvogel
(`agent/krypto/kanarienvogel.py`): eingefrorene Faktensätze, feste Grundlinie,
Prompt-Hash, gemessene Schwelle. Er beantwortet aber nur *„hat sich etwas
geändert?"* — nicht *„ist es gut?"*.

**Der Messstandard erweitert das Prinzip um die Qualitätsfrage:**

### 3.1 Die feste Prüfmenge („Goldanker")

| | |
|---|---|
| **Was** | eine **eingefrorene** Menge von Ankern: Symbol · Zeitpunkt · vollständiger Faktensatz · tatsächlicher Kursverlauf danach |
| **Größe** | 300–500 Anker, geschichtet über Symbole und Marktphasen |
| **Eingefroren** | die Menge ändert sich **nie** — sonst ist Vorher-Nachher wertlos |
| **Erweiterung** | nur durch **Anhängen** einer zweiten, getrennt ausgewiesenen Menge |

⚠️ **Warum eingefroren:** Ein Standard, dessen Prüfmenge mitwandert, misst
zwei Dinge gleichzeitig (Modelländerung + Ankeränderung) und trennt sie nie
wieder. Dieselbe Lehre wie bei der Grundlinie des Kanarienvogels.

### 3.2 Die Kennzahlen — immer dieselben

| Kennzahl | was sie sagt |
|---|---|
| **Potential-Abstand H5 / H20** | schlägt die Auswahl den Markt? |
| **gegen quotengleichen Zufall** | schlägt sie eine Ziehung mit gleicher Trefferzahl? |
| **gegen EMA-200-Regel** | schlägt sie eine triviale Regel? |
| **Vertragstreue** | Anteil formal gültiger Antworten |
| **Z1-Verstöße** | Zahlentreue (seit P1 an der Signalzeile) |
| **Streuung bei Wiederholung** | wie stabil ist das Modell bei identischer Eingabe? |

### 3.3 Die Grundlinie und der Vorher-Nachher-Vergleich

Jeder Lauf schreibt eine Zeile: **Datum · Modell · Prompt-Hash · alle
Kennzahlen**. Ein Vergleich ist damit ein Zeilenvergleich.

⚠️ **Der Prompt-Hash ist Pflicht.** Ändert er sich, ist ein Ausschlag erklärt
und die Grundlinie gehört neu gesetzt. Bleibt er gleich und das Verhalten
kippt, liegt es am Anbieter. Genau diese Trennung hat am 31.07. gefehlt und
Tage gekostet.

---

## 4. Die drei Stufen

### Stufe 1 — Altdaten, kein Modellaufruf *(sofort möglich)*

**Was:** Die 1.292 Einstiege der neuen Kette gegen die drei Vergleichsmaßstäbe
(F1–F3), Erfolgsmaß Potential, marktbereinigt, Cluster-Bootstrap über die 54
Symbole.

| | |
|---|---|
| **Kosten** | **null** — keine Aufrufe, kein Kontingent |
| **Produktion** | **läuft weiter** |
| **Werkzeug** | `messe_abstand_zum_zufall.py` liefert Bootstrap und CRV-je-Signal bereits; das Erfolgsmaß ist auf Potential umzustellen |
| **Ergebnis** | die Antwort auf N-7 für den Zeitraum 14.–24.08. |

### Stufe 2 — Die Goldanker einfrieren *(danach, kein Modellaufruf)*

Aus denselben Daten die feste Prüfmenge bilden und ablegen: Anker, Faktensätze,
Kursverlauf. **Das ist die Grundlage aller späteren Vergleiche** und kostet
ebenfalls nichts.

### Stufe 3 — Die Wiederholungsmessung *(braucht Kontingent)*

Dieselben eingefrorenen Faktensätze **erneut** durch die heutige Kette schicken
und mit dem damaligen Urteil vergleichen. Das misst **Modellstabilität** und
liefert die erste Grundlinie des Standards.

| | |
|---|---|
| **Aufrufe** | 300 Anker × 2 Rollen = **~600** |
| **Dauer** | bei ~30 s je Aufruf: **~5 Stunden** seriell |
| ⚠️ **Kontingent** | Gemini **500/Tag je Modell**, OpenRouter 1.000/Tag bei 20/min. **Reicht knapp — auf zwei Tage verteilen oder zwei Töpfe nutzen** |
| **Produktion** | ⚠️ **hier wird es eng.** Das Budget hängt am Schlüssel, nicht am Gerät — ein Messlauf nimmt der Produktion Kontingent weg |

> **Hier komme ich auf Ihr Angebot zurück:** Für Stufe 3 wäre es sinnvoll, die
> Produktion **für die Dauer des Laufs** anzuhalten — oder den Lauf nachts zu
> fahren, wenn ohnehin wenig läuft. **Für Stufe 1 und 2 nicht nötig.**

---

## 5. Positivkontrolle — Pflicht, nicht Kür

*Projektregel seit 93 B: ohne sie ist ein Nullbefund wertlos, weil er „nicht
hingesehen" heißen kann.*

**Aufbau:** Ein künstlicher Arm mit **bekanntem** Vorteil wird eingepflanzt —
z. B. eine Auswahl, die die Kursreihe kennt und die besten 20 % zieht.

| Ergebnis | Bedeutung |
|---|---|
| Der eingepflanzte Vorteil wird **gefunden** | die Messung sieht Effekte dieser Größe → ein Nullbefund beim LLM ist echt |
| Er wird **nicht** gefunden | die Messung ist zu schwach → ⚠️ **Ergebnis nicht interpretierbar**, Nachweisgrenze berichten |

**Zusätzlich der Negativarm:** eine Zufallsauswahl muss auf null herauskommen.
Tut sie das nicht, ist der Aufbau verzerrt.

---

## 6. ⚠️ Die Unschärfen — vollständig, vorab benannt

*Sie haben sie angesprochen; hier stehen sie, damit sie später nicht als
Ausrede dienen.*

| # | Unschärfe | Umgang |
|---|---|---|
| **1** | **Nur 10 Tage** Beobachtungszeitraum | Ergebnis gilt für diese Phase, nicht allgemein. **Muss so berichtet werden** |
| **2** | ⚠️ **Regimewechsel im Zeitraum** (Markt drehte am 22.08.) | Marktbereinigung **zwingend**; zusätzlich getrennt nach vorher/nachher auswerten |
| **3** | **Auflösungs-Asymmetrie** (#617): Verlierer laufen in den Stop, Gewinner bleiben offen | Potential über festen Horizont **umgeht das** — es braucht keine Auflösung |
| **4** | **Überlappende Anker** — 1.292 Einstiege auf 54 Symbolen sind keine unabhängigen Ziehungen | **Cluster-Bootstrap über Symbole**, nicht Binomialtest (Methodik 2.5) |
| **5** | **A1 verengt seit 23.08.** | Die Stichprobe umfasst beide Regime der Auswahl → getrennt ausweisen |
| **6** | **Das LLM ist nicht deterministisch** | Streuung bei Wiederholung ist eine **eigene Kennzahl** (Stufe 3), kein Störfaktor |
| **7** | ⚠️ **F3 ist schwer sauber zu trennen** | Auswahl und Urteil sind verkettet. Der Vergleich „dieselben Anker ohne Urteil" ist eine **Näherung**, keine saubere Zerlegung — und muss so heißen |

---

## 7. Was vorab festgelegt wird — bevor Daten gesehen werden

*Suchpreis: 300 abgesuchte Zellen = +20,5 Punkte Hürde, **eine vorab benannte
Frage = +10,2**. Deshalb hier, nicht später.*

> ### Die Hypothese
>
> **Die Einstiege der Rollen-Kette erreichen ein höheres marktbereinigtes
> Potential über 5 und 20 Handelstage als eine quotengleiche Zufallsauswahl
> aus denselben Kandidaten.**

| | |
|---|---|
| **Richtung** | vorab festgelegt: **besser**, nicht „anders" |
| **Primäres Maß** | Potential H20, marktbereinigt |
| **Sekundär** | H5; gegen EMA-200; F3 |
| **Schwelle** | empirische Placebo-Schwelle aus dem Projekt: **\|t\| ≥ 3,05** |
| **Alles Weitere** | explorativ, wird als solches gekennzeichnet |

---

## 8. Die drei Zustände des Ergebnisses

*Kein „ja/nein" — dieselbe Systematik wie 93 B:*

| | |
|---|---|
| **TRÄGT** | Effekt über der Schwelle, Positivkontrolle bestanden |
| **GEMESSEN, nichts gefunden** | mit **benannter Nachweisgrenze**: „Effekte unter X % hätten wir nicht gesehen" |
| **NICHT MESSBAR** | zu wenige Fälle → **es wird nicht interpretiert** |

⚠️ **Und ein Nullbefund wird als ZERLEGUNG abgelegt, nicht als „erledigt"** —
welcher Teil trägt nicht: die Auswahl, das Urteil, oder beides?

---

## 9. Was dieses Konzept NICHT beantwortet

| | |
|---|---|
| Ob die Kette **in anderen Marktphasen** trägt | 10 Tage, ein Regimewechsel |
| Ob ein **anderes Modell** besser wäre | dafür bräuchte es gepaarte Arme je Anbieter |
| Ob das Urteil **kausal** beiträgt | F3 ist eine Näherung (Unschärfe 7) |
| Ob die Kette **wirtschaftlich** ist | ⚠️ **bewusst nicht** — das ist nach N-5 nicht der Maßstab |

---

## 10. Vorschlag zur Reihenfolge

| Schritt | Kosten | Produktion |
|---|---|---|
| **1** Stufe 1 rechnen (Altdaten, F1–F3, Potential) | keine | läuft weiter |
| **2** Positivkontrolle | keine | läuft weiter |
| **3** Ergebnis bewerten — trägt die Kette? | — | — |
| **4** Goldanker einfrieren (Stufe 2) | keine | läuft weiter |
| **5** Stufe 3 nur, **wenn** Schritt 3 es rechtfertigt | ~600 Aufrufe | ⚠️ Absprache |

⚠️ **Schritt 3 ist ein echter Haltepunkt.** Zeigt Stufe 1, dass die Kette den
Zufall nicht schlägt, wäre es falsch, danach einen Messstandard für sie zu
bauen — dann steht eine andere Frage an.

---

# Nachtrag 25.08.: Das Zielbild — und warum die Teile einzeln gemessen werden müssen

*Nutzervorgabe, wörtlich: „**Nicht die Uhr soll der Auslöser werden**, sondern
bei der Bewertung eines Assets sollen die Informationen **in Zusammenhang
gebracht** werden, um eben nur einen Trade vorzuschlagen, der ‚wahrscheinlich'
gut ist — die Kunst dabei ist, dies umzusetzen. […] wir benötigen ein
Messkonzept, welches die **gesamte Kette und auch deren Teile unabhängig**
messen kann und muss, sonst werden die Ergebnisse verzerrt."*

## A. Das Zielbild — der Auslöser ist kein zusätzliches Signal

**Die Praxis (CSTI) trennt „der Aufbau liegt vor" von „jetzt ist der Moment"**,
und dem Projekt fehlt der zweite Teil: *„Unsere Kette kennt nur den Aufbau; den
Moment gibt die Uhr vor."*

⚠️ **Die naheliegende Antwort wäre ein separater Trigger. Die Nutzervorgabe
sagt etwas Besseres:**

> **Der Auslöser soll aus der ZUSAMMENFÜHRUNG entstehen, nicht daneben stehen.**
> Wenn die Bewertung eines Assets hoch genug ausfällt, *ist* das der Moment.

**Das ist genau, wofür `agent/wahrscheinlichkeit.py` gebaut wurde** — und der
Grund, warum es heute nicht trägt, lässt sich beziffern:

| | |
|---|---|
| Basisrate (CRV 2,0) | 33,3 % |
| **tragende Beiträge** | **genau einer** — Vorfilter H, +4,5 Punkte |
| Summe | 37,8 % |

Ein einzelner Beitrag von 4,5 Punkten kann nicht zwischen „jetzt" und „nicht
jetzt" trennen. **Die „Kunst der Umsetzung" ist deshalb keine Programmierfrage,
sondern eine Messfrage:** es braucht *mehrere* Beiträge, die (a) einzeln
tragen und (b) **voneinander unabhängig** sind.

⚠️ **Punkt (b) ist der, an dem so etwas scheitert.** Drei Größen, die
dasselbe messen, addieren sich zu einer Scheinsicherheit. Das Projekt hat den
Fall bereits gehabt: Marktphase, Driftband und Geometrie standen im Verdacht,
„dieselbe Größe unter drei Namen" zu sein (alle über den ATR) — geprüft in
Kapitel 103, und der Verdacht traf dort nicht zu. **Bei jedem neuen Beitrag ist
diese Prüfung zu wiederholen.**

## B. Warum Gesamtmessung allein verzerrt

Die Kette hat elf Stufen. Misst man nur das Endergebnis, ist **nicht
unterscheidbar**, ob ein Effekt der Auswahl, dem Lagebild, dem Urteil oder der
Geometrie gehört.

**Konkret und aktuell:** Seit A1 wählt der Rangplatz die Kandidaten aus, und
der Rangplatz **ist gemessen tragend** (+0,79 %, t 3,29). Ein gutes
Gesamtergebnis wäre also erklärbar, **ohne dass das LLM irgendetwas
beigetragen hat**. Wer das nicht trennt, schreibt dem Modell die Leistung der
Auswahl gut.

> **Das ist die Verzerrung, die Sie meinen — und sie geht in beide Richtungen:**
> ein schlechtes Gesamtergebnis könnte ein gutes Urteil verdecken, das von
> einer schlechten Geometrie zunichtegemacht wird.

## C. Zwei Arten von Teilmessung

### C1 — Zerlegung auf Altdaten *(kostenlos, sofort)*

**Prinzip: schichten statt weglassen.** Der Effekt eines Teils wird sichtbar,
indem man *innerhalb* konstanter anderer Teile vergleicht.

| Teil | wie isoliert | in der DB vorhanden |
|---|---|---|
| **Auswahl (A1)** | Vergleich **innerhalb desselben Rangplatzes** — trägt das Urteil noch, wenn der Rang konstant gehalten wird? | ✔ `auswahl_schatten` |
| **Urteil (Rolle BC)** | ERÖFFNEN gegen NICHTS_TUN **bei gleichem Rang und gleicher Marktphase** | ✔ `action` |
| **Geometrie** | dieselbe Aktion, verschiedene Stopabstände → trägt die Zonenwahl? | ✔ `entry/stop/take_profit` |
| **Z1-Treue** | Signale **mit** gegen **ohne** Zahlenverstoß | ✔ seit P1 (`z1_verletzt`) |
| **Z.ai-Gegenprüfung** | Übereinstimmung gegen Abweichung | ✔ `zai_stimmen` |
| **Entscheider** | „trägt sich" gegen „trägt sich nicht" — er zählt bereits, filtert nicht | ✔ Trichter |

⚠️ **Das ist der eigentliche Gewinn dieser Datenlage:** Fünf der sechs Teile
sind **ohne einen einzigen Modellaufruf** trennbar, weil die neue Kette ihre
Zwischenergebnisse mitschreibt. Genau dafür wurden `auswahl_schatten`,
`z1_verletzt` und die Trichterzählung gebaut.

### C2 — Ablation mit neuen Läufen *(kostet Kontingent)*

Für die Teile, die **vor** dem Urteil liegen und keine Spur hinterlassen —
einzelne **Faktenblöcke** und das **Lagebild**. Hier hilft nur: denselben Anker
einmal **mit** und einmal **ohne** den Block fragen.

⚠️ **Und hier die schwerste Warnung aus der eigenen Geschichte:**

| Ablationslauf | Einzeleffekte |
|---|---|
| bei **12** Ankern | **+0,281 / +0,182** |
| bei **28** Ankern | **+0,014 / −0,013** |

> **„Kleine Stichproben erzeugen zuverlässig Scheinbefunde in der erwarteten
> Richtung."** Der Effekt verschwand beim bloßen Verdoppeln.

**Konsequenz:** Ablation unter ~200 gepaarten Ankern je Arm ist nicht
interpretierbar. Bei 2 Rollen × 2 Armen × 200 Ankern sind das **800 Aufrufe**
je untersuchtem Block — das ist der Preis, und er muss vorab bekannt sein.
**Deshalb steht C2 hinter C1 und wird nur für Blöcke gefahren, die C1 als
verdächtig ausweist.**

## D. Die Unabhängigkeitsprüfung — Pflicht bei jedem neuen Beitrag

Bevor ein Beitrag in `wahrscheinlichkeit.BEITRAEGE` aufgenommen wird:

| Prüfung | Frage |
|---|---|
| **1 — Einzelwirkung** | Trägt er allein, über der Placebo-Schwelle? |
| **2 — Zusatzwirkung** | Trägt er **zusätzlich zu H**, oder nur, wo H ohnehin gilt? |
| **3 — Kollinearität** | Korreliert er mit einem bestehenden Beitrag? Sind es zwei Namen für dieselbe Größe? |
| **4 — Vorzeichenstabilität** | Gleiches Vorzeichen in beiden Marktphasen? |

⚠️ **Prüfung 2 hat schon einmal ein Vorzeichen gedreht:** Der Rangplatz trägt
*für sich* (+0,79 %, t 3,29), aber **innerhalb von H** schneidet das beste
Fünftel **5,8 Punkte schlechter** ab. Er steht deshalb zu Recht auf `null` —
und eine Ebene höher, als Auswahl. **Ohne Prüfung 2 wäre er als positiver
Beitrag eingebaut worden und hätte geschadet.**

## E. Was das für die Reihenfolge bedeutet

| Schritt | | Kosten |
|---|---|---|
| **1** | Gesamtkette: F1/F2 (Zufall, EMA-200) | keine |
| **2** | **Zerlegung C1** — sechs Teile einzeln, geschichtet | keine |
| **3** | Positivkontrolle für beide | keine |
| **4** | Bewertung: **wem gehört der Effekt?** | — |
| **5** | C2 nur für Teile, die Schritt 4 als unklar ausweist | ⚠️ ~800 Aufrufe je Block |

> ⚠️ **Schritt 2 ist der eigentliche Kern und war in der ersten Fassung dieses
> Konzepts zu schwach.** Dort stand die Teilfrage nur als „F3, eine Näherung".
> Sie ist keine Näherung, sondern mit den vorhandenen Daten sauber
> durchführbar — und ohne sie ist das Gesamtergebnis, wie Sie sagen, verzerrt.

## F. Und der Bezug zum Zielbild

Die Zerlegung beantwortet direkt, **welche Beiträge es für die Zusammenführung
überhaupt gibt**:

- Trägt das **Urteil** bei konstantem Rang? → dann ist es ein Beitrag
- Trägt die **Z1-Treue**? → dann ist sie ein Beitrag
- Trägt die **Z.ai-Übereinstimmung**? → dann ist sie ein Beitrag

**Jeder Teil, der die vier Prüfungen aus D besteht, wird ein Eintrag in
`wahrscheinlichkeit.BEITRAEGE` — mit Punkten statt mit `nie`.** Und erst wenn
dort mehrere unabhängige Beiträge stehen, kann die Zusammenführung das leisten,
was das Zielbild verlangt: **den Moment aus der Bewertung selbst bestimmen,
statt ihn von der Uhr zu nehmen.**
