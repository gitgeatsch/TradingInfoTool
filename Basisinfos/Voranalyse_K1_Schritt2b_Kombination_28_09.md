# Voranalyse K1 Schritt 2b — die Kombination, zweiter Anlauf (28.09.2026)

**Nutzer:** *„ja committen und pushen, dann Voranalyse schreiben — prüfen und
gegenprüfen."*

**Anlass:** Befund **2.677** — die Kombination als gemeinsames Kurvenmodell
trägt nicht, **aber** die Messform war zu grob: eine gepflanzte Wirkung wurde
erst ab +0,16 sicher gefunden, gesucht sind +0,03 bis +0,06. Die Wirkung ist
da (wo *oben gestreckt*, liegt q ungesehen +0,07 bis +0,10 über der Schätzung).
Das ist **keine Nachbesserung** der verworfenen Messung, sondern eine **neue
Vorabfestlegung** — sie wird ganz neu gerechnet und steht für sich.

---

## 1. Was 2.677 lehrt — und was davon hier eingeht

| # | Lehre | Folge hier |
|---|---|---|
| 1 | der **Marktmedian** steht im Modell für die **Zeit** (Gewinn in der Schätzung +19, auf dem Folgejahr −0,1) | **nur Asset-Beiträge** (E1) |
| 2 | 12 Stufen × 9 Kurven aus 12 Monaten sind nicht zu schätzen — die Kreuzvalidierung wählt fast immer die stärkste Dämpfung | **weniger freie Parameter** (E2), **wachsendes** Fenster (E3) |
| 3 | ⚠️⚠️ **das Gütemaß hatte zu wenig Kraft**: der Log-Loss über **alle** Anker verdünnt eine Wirkung, die nur ~10 % der Anker betrifft — gepflanzte +0,04 ergeben rund **0,3** tausendstel nat, so viel wie das Rauschen der Nullwelt | Hauptmaß wird die **Auswahl** (E5): wie viel besser ist q im obersten Zehntel des geschätzten q? |
| 4 | die Anker sind nicht unabhängig — Dämpfung aus den Daten | bleibt (Ä1, Pflichtschritt 24) |
| 5 | vor jedem Urteil muss die Messform die gesuchte Größe **auflösen** | wird ein **Tor vor der Messung** (E7, Pflichtschritt 25) |

---

## 2. Vorab festzulegen — E1 bis E9

| # | Frage | Empfehlung | warum |
|---|---|---|---|
| **E1** | **Eingänge** | **Variante A:** rsi, momentum_kurz, ema_abstand_atr **selbstbezogen**, je **aktuell und 24 h alt** (6), dazu der **bisherige Anstieg** (24 h in ATR). **Variante B:** A plus oi_aenderung roh. **Keine Marktkurven** | die Marktkurven trugen nicht (2.677, 1); die Asset-Familien trugen einzeln (rsi +1,0 bis +1,2 in allen vier Mengen); der 24 h alte Wert trägt in jedem Zeitraum (2.676) |
| **E2** | **Form der Kurven** | **(b) glatte Kurve**: die 12 Stufen aus Schritt 1, aber **benachbarte Stufen gleichen sich an** (Glättungsstrafe auf die Differenz der Nachbarn, Stärke per Kreuzvalidierung). **Rückfall (a)**, nur wenn (b) das Auflösungs-Tor (E7) nicht besteht: **Ränder in 5 Stufen** (< P1, P1–P10, **Mitte als Bezug**, P90–P99, > P99). Der bisherige Anstieg in seinen A4-Klassen (< 0, 0–1, 1–2, ≥ 2 ATR) | ⚠️ **K1 ist entschieden**: *„A ist komplett starr … kein Übergang, keine Schwelle"* — also Kurven, keine Schalter. (b) behält die Kurve und das Optimum und braucht doch viel weniger Freiheit (die flache Mitte kostet fast nichts). (a) ist die Form, die Schritt 1 belegt, aber gröber — darum nur als festgelegter Rückfall |
| **E3** | **Fenster** | **wachsend**: jeder Monat 2024-01 bis 2026-08 auf **allen** Ankern davor (ab 2023-01, nur bekannte Ausgänge); dazu die **feste Teilung** Suche → Prüfung für die Nullwelt | 12 Monate reichten nicht (2.677, 3); wachsend bleibt Vergangenheit |
| **E4** | **Lehrer** | q5 (+5 vor −5 %, 24 h) gegen das Phase-Normal, wie bisher; 72 h als Auskunft | K4 |
| **E5** | ⭐ **Hauptmaß** | **Dq der Auswahl**: q im **obersten Zehntel** des geschätzten q minus Phase-Normal, auf ungesehenen Ankern. Die Zehntel-Grenze kommt aus dem **Trainingsfenster** (ein fester q-Wert, kein Rang am Tag). Dazu gespiegelt das **unterste Zehntel** (Sperre). Log-Loss und Kalibrierung als Nebenmaße | das ist die **Anwendung** (wer auswählt, bekommt …); die Wirkung sitzt am Rand; *Auswahlanteil angleichen* ist stehende Regel — beide Seiten 10 % |
| **E6** | **Nullwelt** | wie 2.677: Zeitverschiebung je Asset (alle Eingänge gemeinsam), 40 Ziehungen, dieselbe Kreuzvalidierung in jeder Ziehung | E-10, Ä3 |
| **E7** | ⭐⭐ **Auflösungs-Tor — VOR der Messung** | im Werkzeugtest (Bestand, feste Teilung): gepflanzt **+0,04** auf den oberen Rand **eines** verschobenen Eingangs muss in **≥ 4 von 5** Ziehungen jenseits der Grenze liegen. Besteht (b) nicht → (a); besteht auch (a) nicht → **keine Messung**, sondern ein Befund *„die Datenlage löst +0,04 nicht auf"* | Pflichtschritt 25; das Tor nutzt nur **gepflanzte** Wirkung auf wirkungslosen Kopien — kein Blick auf die echte Prüfzeit |
| **E8** | **Gegenprüfungen** | (a) Zufallseingänge (Regeltest) · (b) Summe der einzeln geschätzten Familien gegen gemeinsam · (c) 1 h älter · (d) je Asset, Jahr, BTC-Drittel · (e) 2022 mit Moment-Bezug · (f) nur die Hebelwerte des Betriebs (Namensgleichheit, Auskunft) · (g) Zellen W1/W2 (Hinweis für Schritt 3) · (h) vier Mengen | wie 2.677, ohne die entfallene Marktfrage |
| **E9** | **kein Blocker** | stetiges q; die **K5-Tabelle** als Ausgabe, keine Schwelle | C8, Nutzervorgabe |

---

## 3. Das Kriterium *trägt* — vorab

| # | Bedingung | bei Nein |
|---|---|---|
| **T0** | das **Auflösungs-Tor** (E7) ist bestanden | kein Urteil über die Beiträge |
| **T1** | **Dq der Auswahl** (oberstes Zehntel, Variante A oder B) jenseits der Nullwelt (90. Perzentil, Bestes-von-2) in der festen Teilung — in **allen vier** Mengen; rollierend > 0 | die Kombination trägt nicht |
| **T2** | **mehr als der beste Teil**: Dq der Auswahl der Kombination minus Dq der Auswahl der besten **Einzelfamilie** jenseits seines Nullbands, in ≥ 3 von 4 Mengen. ⚠️ Für diesen **Vergleich** ist die Auswahl bei **jedem** Modell das oberste Zehntel **seiner eigenen** Schätzungen im Test — sonst wählte jedes Modell einen anderen Anteil (Regel *Auswahlanteil angleichen*); die Grenze aus dem Training (E5) bleibt das Maß der **Anwendung** und wird mit ihrem tatsächlichen Anteil ausgewiesen | die Kombination ist ihr bester Teil |
| **T3** | **Rangordnung kalibriert**: innerhalb jedes Monats die Zehntel des geschätzten q gegen das beobachtete q, Steigung 0,7–1,3 (rollierend) · die **Niveau**-Kalibrierung wird ausgewiesen; eine **Schwelle** (K5) nur, wenn auch sie hält | Rangfolge ohne Maß — keine Schwelle |
| **T4** | Dq der Auswahl > 0 in jedem Jahr 2024/2025/2026 und jedem BTC-Drittel (rollierend) | *reden* |
| **T5** | ≥ 60 % der Assets (mit ≥ 50 Auswahlankern) mit Dq der Auswahl > 0 | Klumpen |
| **R** | Zufallseingänge im Nullband | die Regel ist nicht verwendbar |
| **S** | *Auskunft:* das unterste Zehntel — ist es eine Sperre (Dq < 0 in jeder Menge)? | – |

---

## 4. ⚠️⚠️ PRÜFUNG UND GEGENPRÜFUNG DIESER VORANALYSE

### 4a. Gegen die stehenden Regeln und Entscheidungen

| Regel | Prüfung |
|---|---|
| **K1** *Kurven, keine Schalter* | ✔ (b) ist eine Kurve mit Übergang und Optimum; (a) ist ein **festgelegter Rückfall** mit 5 Stufen, keiner mit 2 — und nur, wenn (b) nicht auflöst |
| **kein Blocker** | ✔ q bleibt stetig; das oberste Zehntel ist ein **Maß**, keine Schwelle im Betrieb |
| Regel 3 kein Asset-Rang | ✔ die Zehntel-Grenze ist ein **fester q-Wert** aus dem Trainingsfenster, kein Rang unter den Assets eines Tages |
| Regel 1, 2, 4 | ✔ wie 2.677 |
| *Auswahlanteil angleichen* | ✔ Kombination und Einzelfamilie werden bei **demselben** Anteil (10 %) verglichen |
| Grundgesamtheit | ✔ vier Mengen |
| R-R11 | ✔ 2.677 wird nicht umgestoßen, sondern steht: *die Kurvenform trägt nicht*. 2b beantwortet eine andere Frage (andere Form, anderes Maß) |

### 4b. ⚠️⚠️ Was diese Messung NICHT unabhängig beantworten kann

**Die Prüfzeit ist nicht mehr unberührt.** Welche Beiträge hier eingehen,
wurde in Schritt 1 mit der Suche **gefunden** und mit der Prüfzeit
**bestätigt** (2.675/2.676). Für die Frage *„tragen diese Beiträge?"* ist
die Prüfzeit damit schon gesehen — **T1 ist optimistisch**. Unbeeinflusst
bleibt die Frage von Ebene 2 — *„trägt die Kombination mehr als ihr bester
Teil?"* (T2) —, denn auch die Einzelfamilien sind dieselben. **Unabhängig**
bestätigen können nur: 2022 (Moment-Bezug, E8 e), die **Simulation**
(Ebene 3) und **neue** Monate im Betrieb.

### 4c. Fallen

| Falle | Gegenmittel |
|---|---|
| die Glättung verwischt ein echtes Optimum (rsi > P99 flacher als P90–P99) | Glättungsstärke per Kreuzvalidierung; die geschätzte Kurve wird ausgegeben und mit Schritt 1 verglichen |
| das Tor wird zur Suche nach der passenden Form | die **Reihenfolge** (b) → (a) → kein Urteil ist vorab fest; nur zwei Formen; das Tor sieht nur gepflanzte Wirkung |
| das oberste Zehntel ist wenige Anker je Monat | Urteil gepoolt über die ungesehene Zeit; je Monat nur Auskunft |
| die Grenze aus dem Training wählt im Test **nicht** 10 % (Schätzungen im Training streuen stärker) | der tatsächliche Anteil wird ausgewiesen; der **Vergleich** T2 nutzt das Zehntel der eigenen Testschätzungen — derselbe Anteil für jedes Modell. ⚠️ Das kennt die Verteilung der Schätzungen im Test, **nicht** deren Ausgänge |
| aktuell und 24 h alt hängen zusammen | gemeinsame Schätzung; (b) Summe der Einzelfamilien als Vergleich |
| **Betrieb**: Stundenkerzen fehlen dort (Voranalyse Schritt 2, 8a) | unverändert eine Voraussetzung für später, kein Hindernis für die Messung |

---

## 5. Was NICHT in diesen Schritt gehört

Marktkurven (später als Kontext) · Wechselwirkungen (Schritt 3; W1/W2 nur als
Hinweis) · Schwellenwahl und Stufenzahl (K5/K5b) · Hebelstufe (K6) · K7 ·
Simulation · Betrieb.

---

## 6. Umfang und Laufzeit

Weniger freie Parameter als in 2.677 — etwa **10 bis 15 Minuten je Menge**.
Zuerst der **Werkzeugtest mit dem Auflösungs-Tor** (Bestand, 5 Pflanzungen
je Stärke): er entscheidet, ob (b) oder (a) gerechnet wird — oder gar nicht.

---

## 7. ✔ ABGESTIMMT (28.09.2026) — E1 bis E9 wie empfohlen

**Nutzer:** *„ja, E1 bis E9 wie empfohlen, dann bauen und messen, prüfen und
gegenprüfen."* Festgelegt **vor** dem Bau; die Prüfsummen von Voranalyse und
Werkzeug stehen vor dem ersten Lauf im Messprotokoll
(`Basisinfos/K1_Schritt2b_28_09/vorab_pruefsummen.txt`).

## 7a. Die Empfehlung, wie abgestimmt

| # | Empfehlung |
|---|---|
| **E1** | nur Asset-Beiträge: rsi, momentum, ema_abstand selbst, je aktuell und 24 h alt, bisheriger Anstieg; B plus oi_aenderung |
| **E2** | (b) glatte 12-Stufen-Kurve; Rückfall (a) Ränder in 5 Stufen, nur wenn (b) das Tor nicht besteht |
| **E3** | wachsendes Fenster; feste Teilung für die Nullwelt |
| **E4** | q5/24 h, 72 h Auskunft |
| **E5** | Hauptmaß Dq der Auswahl (oberstes Zehntel, Grenze aus dem Training), gespiegelt das unterste |
| **E6** | Nullwelt wie 2.677 |
| **E7** | Auflösungs-Tor: +0,04 in ≥ 4 von 5, sonst (a), sonst kein Urteil |
| **E8** | Gegenprüfungen (a)–(h) |
| **E9** | stetiges q, K5-Tabelle, keine Schwelle |
| **T0–T5, R, S** | wie Abschnitt 3 |

---

## 8. ✔ AUFLÖSUNGS-TOR (E7) — Form (b) bestanden (28.09.2026, Bestand, 40 Nullwelten)

| gepflanzt auf P90+ von rsi_s (verschobene Kopie) | Dq der Auswahl (5 Ziehungen) | gefunden |
|---|---|---|
| +0,02 | −0,003 … −0,020 | 2 von 5 |
| **+0,04** | −0,003 … −0,010 | **5 von 5** |
| +0,08 | +0,034 … +0,087 | 5 von 5 |

Nullwelt: Mittel **−0,0163**, Streuung 0,0054, 90. Perzentil −0,0110. ➤ **Form (b)
wird gemessen** (vorab festgelegte Reihenfolge).

⚠️⚠️ **Gegenprüfung des Tors — die Nullwelt liegt nicht bei 0:** ohne jede
Wirkung hat das oberste Zehntel des geschätzten q ein **schlechteres** q als
sein Normal. Ausgewählt wird nach dem **ganzen** q (Normal plus Beiträge);
ohne echte Beiträge wählt das Modell die Anker mit dem höchsten
**Phase-Normal** — und dort kehrt das q zur Mitte zurück (das Normal
überschätzt Assets, die zuletzt gut liefen). Eine gepflanzte +0,04 hebt die
Auswahl darum nur um rund +0,011 über die Nullwelt: der Normal-Anteil
verdünnt sie.

➤ **Die vorab festgelegten Urteile bleiben gültig** — jede Zahl wird gegen
dieselbe Nullwelt gelesen, die diesen Effekt enthält. ➤ **Nachträglich
ergänzt, ändert kein Urteil:** die **Auswahl nach dem Beitrag allein** (ohne
Normal), mit eigener Nullwelt, fest und rollierend — sie beantwortet sauberer,
ob die **Beiträge** besser auswählen. ➤ **Nebenbefund für K2:** das
12-Monats-Normal kehrt bei hohen Werten zur Mitte zurück — eine gedämpfte
Form des Normals wäre eine eigene Messung.