# Was vor Schritt 1 liegt — der übergeordnete Plan, durchgesehen

*Nutzerfrage 23.08.: „sollen wir vor Schritt 1 noch wichtige und essentielle
Themen aus dem übergeordneten Plan abarbeiten, sonst bleibt etwas wichtigeres
liegen?"*

> Durchgesehen: `Zwischenstand_Gesamtprojekt_06_08.md` (8c/8d/8e),
> `Reparaturliste_Umbau_23_08.md`, `Machbarkeit_S1_Gegenpruefung_23_08.md`,
> `Konzept_Einstiegsbewertung_23_08.md`. **Jede Zeile mit ihrem Beleg.**

---

## 0. Der wichtigste Punkt steht nicht auf einer Liste

> ⚠️ **A1a–A1d, S-2 und der Schatten sind gebaut — und laufen nirgends.**
> Die Produktion arbeitet mit dem Stand von vorher.

**Solange nicht ausgerollt wird:**

| | |
|---|---|
| der Schatten | sammelt **nichts** — und er ist die einzige Basislinie für die LLM-Ebene |
| die Signalflut | geht weiter (41 Beurteilungen je Umlauf statt 2) |
| jede weitere Messung | läuft auf Daten der **alten** Kette |

**Die Ausroll-Checkliste steht fertig in 8e.3** — `git fetch` vor dem Push, als
**ein** Paket, `pruefe_abdeckung.py` auf dem Notebook.

⚠️ **Und die Reihenfolge dabei:** kurz stoppen, ziehen, starten — **nicht
gestoppt lassen**. Der Schatten füllt sich ausschließlich aus echten Läufen.

---

## 1. Essenziell und offen — nach Gewicht

| # | was | warum jetzt | Beleg |
|---|---|---|---|
| **1** | **Ausrollen** | siehe oben — ohne das ist alles Gebaute wirkungslos | 8e.3 |
| **2** | **B1/B2 — die Verkaufsseite** | `facts_json` ist ein **17-Zeichen-Stummel** bei HALTEN/REDUZIEREN/VERKAUFEN, `familien=None`. ⚠️ **Durch A1 wird das wichtiger, nicht unwichtiger:** wenn je Umlauf nur noch 2 Werte beurteilt werden, ist der **Bestand** der größere Teil des Geschehens | Reparaturliste B1/B2 |
| **3** | **P1 — Z1s Urteil speichern** | dieselbe Fehlerart wie das gerade behobene S-2: läuft, geht in die Mail, **landet nicht in der Zeile** — und kann deshalb nie gegen Ergebnisse gemessen werden. Klein | Konzept §2.3, 8e C |
| **4** | **Nachrichten — Stufe 0 (Sammlung)** | laut 8e die **einzige unerprobte Kategorie**. ⚠️ **Und die Uhr läuft gegen uns:** wie bei TVL (auswertbar erst ab 18.09.) bestimmt der Sammelbeginn den Auswertungstermin | 8e „Grundsätzlich offen" |

**Erst danach ist Schritt 1 sinnvoll** — der gemeinsame Unterbau setzt dann auf
einer Kette ohne bekannte Löcher auf und hat echte Daten zum Rechnen.

---

## 2. Wichtig, aber nach dem Ausrollen

| # | was | Einordnung |
|---|---|---|
| **S-1** | die Kette trägt `akkumulation` nicht | ⚠️ **„hart" ist es für S1, nicht für den Betrieb.** Solange keine Vorteilsquelle zugewiesen wird, entsteht auch kein Akkumulationssignal — der stille ATR-Stop kann heute gar nicht auftreten. Es blockiert die *nächste* Stufe, nicht die laufende |
| **S-4** | H barrierenfrei fassen | Kern der Messumstellung, gehört zu Schritt 1 |
| **A6** | Mail-Betreff hängt am Lauf | kosmetisch — **aber falsch, sobald die Rechnung wieder einen Hebel ergibt** |
| **B3** | keine Z.ai-Zweitmeinung auf der Verkaufsseite (0 von 561) | folgt sinnvoll auf B1/B2 |

---

## 3. Klären, nicht bauen — billig und überfällig

| # | was | warum es keine Bauarbeit ist |
|---|---|---|
| **D2** | 5 Module ohne Aufrufer (`szenario_*`, `marktbreite`) | entweder anschließen oder ausbauen — beides ist eine Entscheidung, keine Konstruktion |
| **D3** | 27 config-Schlüssel liest niemand | ein Regler, den niemand liest, ist eine Falle: er sieht nach Steuerung aus |
| **Q5** | OD7L ohne Futures-Referenz | ⚠️ passt zum heutigen Fund: **alle vier Rohstoffsymbole haben null eigene Kerzen** |

---

## 4. Nutzerentscheidungen — sie warten auf Sie, nicht auf mich

| # | was | Stand |
|---|---|---|
| **C1** | Einsatz 800 € (vorläufig) | dokumentiert, Bedingung fürs Anheben ist **messbar** formuliert |
| **C2** | Risiko je Trade schwankt um **Faktor 9** | ⚠️ das schwerste offene Stück der Geldrechnung |
| **C3** | CRV-Abstufung: geeicht (`voll_ab` 3,0), **aber ausgeschaltet** (`spreizung` 1,0) | Einschalten ändert Positionsgrößen |
| **S6d** | Hebeldeckel wirkt umgekehrt | Deckel müsste am `verlustanteil` greifen |

---

## 5. ⚠️ Was ich ausdrücklich NICHT vorziehen würde

| | warum nicht |
|---|---|
| **die offenen Messungen M1–M4** | sie kosten Kontingent und Stunden und klären **Einzelerklärungen**, nicht die Tragfähigkeit. 8d hat sie am 11.08. bewusst abgestuft |
| **die Marktbreite reparieren** | sie wirkt **invers** und ist für 4 von 5 Klassen arithmetisch nicht berechenbar — sie gehört gestrichen, nicht repariert |
| **HORIZONT_KERZEN = 20 herleiten** | betrifft die **Barrieren**auswertung, und genau die ist als Erfolgsmaß ersetzt (Konzept §11) |

---

## 6. Meine Empfehlung in einem Satz

> **Ausrollen, dann die Verkaufsseite, dann Z1 speichern, dann Nachrichten
> sammeln — und erst dann den gemeinsamen Unterbau.**

Begründung: Punkt 1 macht das Gebaute erst wirksam, Punkt 2 ist durch A1 gerade
**gewichtiger geworden**, Punkt 3 ist klein und verhindert einen Fehler, den wir
heute schon einmal behoben haben, und Punkt 4 hat eine **Frist, die von selbst
läuft**.
