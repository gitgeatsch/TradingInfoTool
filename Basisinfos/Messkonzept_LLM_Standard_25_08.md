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
