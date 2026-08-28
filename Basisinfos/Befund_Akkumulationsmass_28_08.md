# Das Akkumulations-Signalmaß — es trägt, aber nicht bei den Kernwerten

> ⚠️⚠️ **DIE ENTSCHEIDENDE EINSCHRÄNKUNG, gefunden auf Nutzeraufforderung
> *„wie immer mit Gegenprüfung"* — sie steht hier oben, weil sie den
> praktischen Wert des Befundes bestimmt:**
>
> Das Maß trägt über **505 Krypto-Reihen** und übersteht alle sieben
> Kontrollen. **Für BTC, ETH und SOL trägt es nicht.**
>
> | | Rang | p |
> |---|---|---|
> | 505 Reihen | **+0,0283** | 0,000 |
> | BTC | −0,0251 | 0,723 |
> | ETH | −0,0308 | 0,810 |
> | SOL | −0,0291 | 0,855 |
>
> **Und es ist nicht n=3-Rauschen:** Die Streuung je Symbol ist 0,0397, die
> Kernwerte liegen **2,39 Standardfehler** unter dem Mittel. Nur **14,3 %**
> aller 505 Symbole haben einen negativen Vorsprung — **alle drei Kernwerte
> sind darunter.**
>
> ⚠️ **Es liegt nicht an der Kursentwicklung:** nach Gesamtentwicklung in
> Fünftel geteilt, ist der Vorsprung **konstant** (+0,024 · +0,026 · +0,032 ·
> +0,027 · +0,033, alle p < 0,005). Die Kernwerte sind auch innerhalb ihres
> eigenen Fünftels die Ausnahme.
>
> **Folge:** `spot × akkumulation` ist heute genau auf BTC/ETH/SOL
> freigeschaltet — also auf die drei Werte, für die dieses Maß **keine**
> Begründung liefert. Das ist eine **Entscheidung**, keine Messfrage
> (Abschnitt 9).



**Gemessen 28.08.2026**, `messe_akkumulationsmass.py`, 505 lückenlose
Krypto-Reihen, Kalenderachse 2017-08-17 .. 2026-08-21 (3.292 Tage).

**Auftrag**, Nutzerpriorisierung vom 28.08.: *„1. für Akkumulation eine
Begründung, also echtes Signalmaß zu finden — dieses steht nicht in Konkurrenz
zu ‚normalem' Spot und Hebel und ist somit relativ einfach."*

---

## 1. Was gefehlt hat — und was schon da war

Für `einstieg` steht eine Zahl in der Mail. Für `akkumulation` nicht, aus
einem strukturellen Grund:

```
akkumulation → kein Stop → kein CRV → keine Basisrate → kein H
```

✔ **Aber das Maß existierte bereits** — es war nur nie **je Tag** ausgedrückt.
Der Tagewahl-Befund vom 23.08. sagt: antizyklische Tagewahl schlägt ihren
quotengleichen Zufall. Das ist eine Aussage über eine **Regel über Fenster**.

| | Aussage | Ebene |
|---|---|---|
| vorhanden (23.08.) | „UNTER_SMA-Tage sind im Mittel bessere Kauftage" | Fenster |
| **gefehlt** | „**dieser** Tag ist um X % besser" | **Tag** |

⚠️ **Der Fenstervorsprung entsteht aus 104 Käufen — daraus folgt nicht, dass
der einzelne Tag besser ist.** Deshalb wurde das Tagesmaß direkt gemessen und
nicht abgeleitet.

---

## 2. Die Zielgröße — und warum sie kein Fakt ist

`handelsauftrag.py` gibt der Akkumulation ausdrücklich ein anderes
Erfolgsmaß: *„Durchschnittskurs und Endvermögen statt Ziel vor Stop"*. Direkt
rechenbar:

```
V(t,H) = Mittel(Kurs[t+1 .. t+H]) / Kurs(t) − 1        "Verbilligung"
```

✔ **V ist zum Zeitpunkt t unbekannt.** Genau das unterscheidet es vom
Vorschlag, den der Nutzer verworfen hat: *„ein Kurs unter dem eigenen Einstand
ist kein Signal oder Bewertung, sondern ein Fakt."* „Unter Einstand" ist heute
ablesbar — V ist eine Erwartung.

**Gemessen wird ausschließlich der Perzentilrang von V innerhalb der eigenen
Reihe.** Die Basisrate ist damit **exakt 0,500 per Konstruktion** — der Drift
kann nicht als Signal durchgehen, und keine einzelne Reihe kann dominieren.

---

## 3. ⚠️ Der erste Lauf hat sich selbst widerlegt

**Er wäre als Ergebnis durchgegangen, wenn die Kontrollen nicht mitgelaufen
wären.** Zwei Konstruktionsfehler, beide nachgewiesen, keiner ein Marktbefund:

| Alarm | Wert | sollte sein |
|---|---|---|
| Negativkontrolle WOCHENTAG | **−10,6 %** | 0 |
| Nullverteilung | **±47,5 %** | eng |

**(1) V ist extrem schief, der Mittelwert unbrauchbar.** Über alle Reihen:
Median der Reihen-Mittelwerte −0,0 %, 95. Perzentil +21,5 % — und Maximum
**+10.732,9 %**. ⚠️ **Eine einzige Reihe bestimmte das Ergebnis.**

**(2) Die Reihen waren nicht kalendarisch ausgerichtet.** Nur 347 von 523
enden am selben Tag; der Verschub `d % len(m)` war je Symbol ein anderer —
genau die Gleichzeitigkeit, die der eigene Kopftext forderte, war **nicht**
hergestellt.

⚠️ **(3) UND DIE ERSTE KORREKTUR WAR SELBST FALSCH.** Sie addierte den
Startpunkt des Symbols hinzu (`(d + eigen) % len(m)`) — damit verschob sich
jede Reihe wieder um einen **anderen** Betrag. Nachgewiesen an zwei Reihen mit
verschiedenem Startpunkt. Bei lückenlosen Tagesreihen **ist** ein Verschub um
d Indizes bereits ein Verschub um d Kalendertage; der Zuschlag war der Fehler.

**Was die Korrektur kostete — in der ehrlichen Richtung:** Die Nullverteilung
wurde **2,7-mal breiter** (−0,0124 .. +0,0089 statt −0,0033 .. +0,0047), weil
die Gleichzeitigkeit des Marktes jetzt erhalten bleibt. **Ein Befund ist daran
gestorben:** RUECKGANG fiel auf H=90 von p 0,000 auf **p 0,060**. Der
Hauptbefund hielt unverändert.

---

## 4. Das Ergebnis — Schalter

**H = 90 Tage, 505 Reihen.** Nullhypothese ist ein **zirkulärer Verschub** auf
der Kalenderachse, für jedes Symbol derselbe (Methodik 2.77: bei
überlappenden Ankern ist ein freier Placebo zu eng).

| Zustand | Kauftage | Rang | Zufall 5–95 % | p | Höhe | |
|---|---|---|---|---|---|---|
| **UNTER_SMA** | 68,5 % | **+0,0283** | −0,0124 .. +0,0089 | **0,000** | **+1,62 %** | ✔ trägt |
| RUECKGANG | 88,9 % | +0,0045 | −0,0062 .. +0,0048 | **0,060** | +0,11 % | ⚠️ trägt **nicht** |
| DCA *(Rechenkontrolle)* | 100 % | **+0,0000** | ±0,0000 | — | 0,00 % | ✔ Pflicht |
| TIEFPUNKT *(Positivkontrolle)* | 4,5 % | **+0,4242** | −0,0337 .. +0,0292 | 0,000 | +52,62 % | ✔ Maschine intakt |
| WOCHENTAG *(Negativkontrolle)* | 14,3 % | **−0,0008** | −0,0007 .. +0,0007 | 0,978 | −0,05 % | ✔ liegt auf null |

**Die vorab benannte Primärzelle trägt.** Der beobachtete Wert liegt das
Sechsfache des 95-Perzentils außerhalb der Nullverteilung.

---

## 5. ⚠️ Die stetige Form ist die stärkere — und sie ist monoton

Der Schalter feuert an **68,5 % aller Tage** — als Auslöser sagt er fast nie
nein. Und er mischt Ungleiches: ganz tief unten (+0,096) mit knapp unter dem
Schnitt (−0,065), Ergebnis +0,028.

**Abstand zum eigenen 200-Schnitt, H = 90:**

| Abstand | Anteil | Rang | 1. Hälfte | 2. Hälfte | **Höhe** |
|---|---|---|---|---|---|
| **unter −40 %** | 19,8 % | **+0,0960** | +0,2020 | +0,0879 | **+6,06 %** |
| −40 .. −25 % | 19,8 % | +0,0197 | +0,0922 | +0,0179 | +2,18 % |
| −25 .. −15 % | 12,8 % | −0,0305 | +0,0346 | −0,0205 | −1,17 % |
| −15 .. −7,5 % | 8,6 % | −0,0605 | +0,0159 | −0,0472 | −3,81 % |
| −7,5 .. 0 % | 7,8 % | −0,0651 | +0,0014 | −0,0493 | −4,64 % |
| 0 .. +7,5 % | 6,6 % | −0,0755 | −0,0239 | −0,0408 | −5,49 % |
| +7,5 .. +15 % | 4,9 % | −0,0822 | −0,0232 | −0,0401 | −6,05 % |
| +15 .. +30 % | 6,5 % | −0,0895 | −0,0446 | −0,0407 | −6,33 % |
| **über +30 %** | 13,2 % | **−0,1508** | −0,1315 | −0,1285 | **−11,79 %** |

✔ **Monoton über alle neun Bänder**, ohne Ausnahme, in beiden Kalenderhälften
gleichgerichtet.

⚠️ **Und damit ist der Buckel vom 27.08. widerlegt — in die Gegenrichtung.**
Dort hieß es: *am besten leicht unter dem Schnitt (+5,6), schlechter ganz tief
unten (−4,4)*. Hier ist ganz tief unten **das beste** Band und knapp darunter
eines der schlechtesten. **Kein Widerspruch, sondern zwei Erfolgsmaße:** dort
Zielerreichung, hier Verbilligung. Die beiden haben verschiedene Kennlinien —
das ist selbst ein Befund und stützt
[[feedback-potential-statt-zielerreichung]].

✔ **Die bestehende Ausschlussregel wird unabhängig bestätigt:** über +30 %
über dem Schnitt ist mit −11,8 % das mit Abstand schlechteste Band.

**Der zweite Horizont bestätigt, H = 365 Tage, 413 Reihen** (Schalter
UNTER_SMA **+0,0514**, p 0,000):

| Abstand | Rang | 1. Hälfte | 2. Hälfte | Höhe |
|---|---|---|---|---|
| **unter −40 %** | **+0,0922** | +0,1725 | +0,0675 | **+5,39 %** |
| −40 .. −25 % | +0,0483 | +0,0646 | +0,0516 | +3,58 % |
| −25 .. −15 % | +0,0079 | +0,0245 | +0,0279 | +1,96 % |
| −15 .. −7,5 % | −0,0185 | +0,0102 | +0,0054 | −1,54 % |
| −7,5 .. 0 % | −0,0446 | −0,0086 | −0,0164 | −2,40 % |
| 0 .. +7,5 % | −0,0584 | −0,0174 | −0,0281 | −3,26 % |
| +7,5 .. +15 % | −0,0800 | −0,0048 | −0,0484 | −5,09 % |
| +15 .. +30 % | −0,1051 | −0,0381 | −0,0845 | −7,40 % |
| **über +30 %** | **−0,1808** | −0,0976 | −0,1980 | **−15,77 %** |

✔ **Ebenfalls monoton über alle neun Bänder.** Der Effekt ist auf dem längeren
Horizont **stärker**, nicht schwächer — was zu einer Strategie passt, die
ausdrücklich lange läuft.

---

## 6. Die Gegenprüfungen — sieben bestanden, eine nicht

Am 27.08. starben **vier von fünf** Befunden hier. Dieser überlebt sieben — und fällt bei der achten, der Anwendungsfrage:

| Prüfung | Frage | Ergebnis | |
|---|---|---|---|
| **Überlebende** | wirkt es nur bei Reihen, die überlebt/gestiegen sind? | H=90: gefallen **+0,0282** (417 Reihen) ≈ gestiegen **+0,0291** (53). ⚠️ H=365 **kehrt es um**: gefallen **+0,0544** (p 0,000), gestiegen nur +0,0257 (p 0,062, Höhe −0,08 %) | ✔✔ |
| **Marktphase** | kippt es mit der Kalenderhälfte? | 1. Hälfte +0,0796, 2. Hälfte +0,0236 — **gleiches Vorzeichen** | ✔ |
| **Jensen / Log** | ist es Arithmetik statt Markt? | Log-Maß **identisch** (+0,0964 gegen +0,0960) | ✔ |
| **Saat** | hängt es an der Zufallssaat? | identisch (+0,0283) | ✔ |
| **Rechenkontrolle** | DCA muss exakt 0 sein | **+0,0000** | ✔ |
| ⚠️ **Kernwerte** | gilt es für BTC/ETH/SOL? | **nein** — −0,025 / −0,031 / −0,029, alle p > 0,7 | ✖ |
| ⚠️ **Kursentwicklung** | erklärt der Anstieg den Ausfall? | **nein** — alle fünf Fünftel +0,024..+0,033, p < 0,005 | ✖ |
| **Positivkontrolle** | erkennt die Maschine echte Information? | TIEFPUNKT **+0,4242** von max ~+0,5 | ✔ |
| **Negativkontrolle** | ist die Nullverteilung zu eng? | WOCHENTAG **−0,0008** bei Null ±0,0008 | ✔ |

**Warum diese Messung nicht an der Investitionsquote stirbt** — der Fehler,
der jede bisherige Akkumulationsmessung getötet hat (11.08., 23.08., 27.08.:
*„der antizyklische Vorteil ist vollständig durch die Investitionsquote
erklärt"*): dort wurden **Regeln über Reihen** verglichen, hier **Tage gegen
Tage**. Die Quote kürzt sich per Konstruktion heraus.

---

## 7. ⚠️ Was der Befund NICHT sagt

| Einschränkung | |
|---|---|
| **Delistete Währungen fehlen** | Die Datenbank enthält nur, was **heute** existiert. Eine Währung, die auf null ging, ist gar nicht da. ⚠️ **Mit diesen Daten nicht wegzumessen.** Stark entlastend, aber kein Beweis: auf H=365 ist der Effekt bei den **gefallenen** Reihen doppelt so groß wie bei den gestiegenen — bei einem Überlebensartefakt müsste es umgekehrt sein |
| **Der Effekt schrumpft** | unterstes Band 1. Hälfte +0,2020 → 2. Hälfte +0,0879, **Faktor 2,3** |
| **Nur Krypto** | Aktien, ETF, Rohstoffe ungemessen |
| **Bänder sind nicht unabhängig** | sie teilen sich dieselben Reihen |
| **Keine Kosten** | richtig so — das Potential ist gebührenfrei (N-5), die Wirtschaftlichkeit steht getrennt in der Mail |
| **Es ist kein Alpha-Nachweis** | es sagt, **wann** innerhalb einer Akkumulation gekauft wird — nicht, **ob** akkumuliert werden soll |

---

## 8. Was daraus für die Mail folgt

Die Akkumulation kann ab jetzt eine Begründung tragen, die **kein Fakt** ist:

```
Akkumulation <Wert> — Verbilligung
  Lage:      -43 % zum eigenen 200-Tage-Schnitt
  Erwartung: +6,1 % guenstiger als ein beliebiger Tag dieser Reihe
             (Median ueber 90 Tage, 505 Reihen, Rang +0,096 gegen 0,500)
  Grenze:    ueber +30 % zum Schnitt kehrt sich das auf -11,8 % um
```

⚠️ **Was hier NICHT stehen darf:** ein Prozentwert ohne den Vergleich. „+6,1 %
Verbilligung" allein wäre wieder der Drift. Die Aussage lebt ausschließlich
von *„gegenüber einem beliebigen Tag derselben Reihe"*.

⚠️⚠️ **UND DIESER SATZ DARF HEUTE FÜR BTC, ETH UND SOL NICHT ERSCHEINEN** —
das sind die einzigen drei Werte, für die Akkumulation freigeschaltet ist, und
genau bei ihnen ist der Vorsprung negativ. Ein Werkzeug, das die Zahl
unbesehen für jedes Symbol druckt, würde für den Kern eine Begründung
erfinden, die dort nicht gemessen ist.

---

## 9. ⚠️ Die Entscheidung, die daraus folgt — sie ist keine Messfrage

Der Befund und die Freischaltung passen nicht zusammen:

| | gemessen | freigeschaltet |
|---|---|---|
| trägt | **502 andere Krypto-Reihen** | — |
| trägt **nicht** | — | **BTC, ETH, SOL** |

**Drei Wege, und keiner ist durch weiteres Messen zu entscheiden:**

| | Weg | Preis |
|---|---|---|
| **A** | Akkumulation auf Werte ausweiten, für die das Maß trägt | ⚠️ widerspricht der Nutzerentscheidung *„BTC und ETH kommen als Core-Assets in Frage mit sehr langfristiger Haltedauer"* — dort geht es um Überleben, nicht um Verbilligung |
| **B** | Kern weiter akkumulieren, aber **ohne** Verbilligungssatz in der Mail | ✔ ehrlich; der Kern läuft dann auf festem Takt **ohne Begründungsanspruch** — genau das, was die Vorabfestlegung für diesen Fall vorsah |
| **C** | nur die **Ausschlussseite** für den Kern nutzen (> +30 % über dem Schnitt) | die Ausschlussregel ist unabhängig belegt (3/3 Jahre, −11,2 Punkte) und **braucht die Kaufseite nicht** |

**Was der Fachexperte empfiehlt: B und C zusammen, A nicht.**

Der Kern wird akkumuliert, weil der Nutzer ihn für **überlebensfähig** hält —
das ist eine Anlageentscheidung, keine Timing-Aussage, und sie braucht kein
Signalmaß. Was sie braucht, ist die **Bremse nach oben**: nicht in eine
Übertreibung hineinkaufen. Genau die ist belegt, und zwar auch bei den
Kernwerten (dort ist das Band über +30 % mit 24,5 % der Tage das mit Abstand
häufigste — die Bremse hat dort **mehr** zu tun als anderswo).

⚠️ **A wäre der Fehler:** das Maß trägt bei kleinen, eingebrochenen Werten am
stärksten — und *„tief gefallene fallen weiter"* ist am 27.08. bereits als
Asset-Aussage verworfen worden. Eine Akkumulation auf 502 kleine Werte
auszuweiten, weil dort die Rückkehr zum Mittel messbar ist, würde
Überlebensrisiko gegen Timing-Vorteil tauschen. **Das ist kein guter Tausch,
und es ist auch nicht gemessen** — delistete Währungen fehlen in den Daten
vollständig.

Verwandt: `Gesamtplan_Wo_wir_stehen_28_08.md` Abschnitt 6 (dort stand dieser
Punkt noch als offen) · `Befund_Lage_27_08.md` · `Kombinationsmatrix_27_08.md`
