# Konzept: die Bewertungsstufe — und warum Schritt 1 nicht klein ist

**Angelegt 29.08.2026, zur Abstimmung. Nichts davon ist gebaut.**

**Nutzerauftrag:** *„mach Schritt 1 bis 3 … der 1. Schritt wird als klein
bezeichnet, ist aber vorher im Konzept zu bewerten und bevor wir bauen einen
abgestimmten Plan zur Zielerreichung."*

⚠️ **Der Auftrag war richtig, meine Einschätzung „klein" war es nicht.** Beim
Ausarbeiten sind zwei Grundsatzfragen aufgetaucht, die vor jedem Bau
entschieden sein müssen. Beide sind im Projekt bereits belegt — ich hatte sie
nicht verknüpft.

---

## 1. Die Frage, die alles davor entscheidet: **ist die Quote das richtige Maß?**

**Nein.** Und das steht seit dem 23.08. fest, Nutzervorgabe wörtlich:

> *„Wichtig für den ‚guten Trade' ist das POTENTIAL — also hohe
> Wahrscheinlichkeit, dass etwas unter bestimmten Bedingungen eintritt — und
> **nicht die reelle Zielerreichung**; diese ist immer außer Reichweite."*

**Die Begründung ist arithmetisch, nicht meinungsabhängig:**

```
Ziel        = CRV × Stopabstand
Basisrate   = 1/(1+CRV)          <- steht fest, BEVOR der Markt etwas tut
```

Ein Barrierensystem auf driftfreiem Pfad hat brutto Erwartungswert null — für
**jede** Geometrie (33,3 % theoretisch, 34,0 % gemessen über 19.891 Anker).

⚠️ **Wer „Ziel vor Stop" misst, misst die eigene Zielregel zurück.** Das
erklärt die Nullbefundserie: *„Nicht der Markt war leer — das Maß war blind."*

### Was das für unsere Bausteine heißt

| Baustein | betroffen? | warum |
|---|---|---|
| **Basisrate** `1/(1+CRV)` | ⚠️ **ist** die Blindheit | reine Konstruktion, keine Marktaussage |
| **Potential** `quote×CRV−(1−quote)` | ✔ **nicht blind** | es ist **null** bei reiner Basisrate und misst damit **ausschließlich die Beiträge** |
| **Vorfilter H, +4,5 Punkte** | ⚠️ **gemessen bei CRV 2,0** (`messe_marken.py:80`) | eine Aussage über „Ziel vor Stop", nicht über die Bewegung |

✔ **Wichtige Differenzierung:** H vergleicht zwei Arme mit **derselben**
Zielregel. Der Unterschied zwischen ihnen ist eine gültige Aussage — die
Blindheit betrifft die absolute Höhe, nicht den Vergleich.

⚠️ **Aber:** H sagt *„von hier aus wird das Ziel häufiger vor dem Stop
erreicht"* — nicht *„von hier aus bewegt sich der Kurs weiter"*. Für die
Zielvorgabe („wie viel ist hier zu holen") ist das die falsche Frage.

### Ist „Quote" überhaupt die richtige Bezeichnung?

**Nein — sie ist mehrdeutig und deshalb Teil des Problems.**

| heute | präzise | was gemeint ist |
|---|---|---|
| „Quote" | **Zielerreichungsquote** | Anteil der Fälle mit Ziel vor Stop |
| „Basisrate" | ✔ passt | was diese Quote per Geometrie ohnehin ist |
| „Potential" | ✔ passt | Erwartungswert in R, gebührenfrei |
| — fehlt — | **Bewegungserwartung** | wie weit sich der Kurs bewegt, barrierenfrei |

✔ **Das Werkzeug für die letzte Zeile existiert:** `agent/trichter.py`
(Kapitel 93, gebaut 19.08.) — „die übliche Kursbewegung auf 5/20/60
Handelstage, 80 % der Fälle, **Richtung offen**". Es steht bereits in jeder
Mail mit Einstiegszone.

⚠️ **In `wahrscheinlichkeit.py` ist der Trichter als Beitrag mit `0.0` Punkten
und dem Zustand „enthalten" geführt** — Begründung: *„er bestimmt die
Geometrie und damit die Basisrate."* Das ist richtig, **solange** die Basisrate
der Maßstab ist. Wird der Maßstab die Bewegung, ist der Trichter nicht mehr
„enthalten", sondern **die Grundlage**.

---

## 2. Die zweite Frage: **trägt die LLM-Kette überhaupt?**

**Ungemessen — und das Projekt hat sich selbst die Reihenfolge gegeben:**

> **„N-7 hat Vorrang vor N-6: ob ein Eingriff in die Kette sich lohnt, hängt
> davon ab, ob die Kette selbst trägt."**

**Was für die ALTE Kette gemessen wurde** (09.08.):

| | Richtungstreffer |
|---|---|
| LLM-Richtungswahl | **29,8 / 27,7 / 25,0 %** |
| „immer SHORT" | 74,0 / 80,9 / 87,5 % |
| EMA-200 | 61,8 / 61,7 / 63,5 % |

⚠️ *„Das LLM liegt hinter JEDER Regel."* Dazu Z.ai: **17× LONG in 2.469
Prüfungen**.

⚠️⚠️ **Seit dem Rollenumbau existiert KEINE vergleichbare Messung.** Der
Prompt ging von 34.611 auf 3.183 Zeichen, zwei Rollen statt einer, Z1 kam
dazu. Ob die heutige Kette den Zufall oder eine einfache Regel schlägt, ist
**unbeantwortet** — nicht „erfüllt".

**Was das für Schritt 1 bis 3 bedeutet:** Eine Bewertungsstufe, die entscheidet,
welche LLM-Urteile durchgehen, setzt voraus, dass die Urteile überhaupt Wert
haben. Ist das nicht so, filtert sie Rauschen nach Rauschen.

---

## 3. Was Stufe 11 (Entscheider) heute entscheidet — und was sie sollte

### Heute

```
basisrate = 1/(1+CRV)                              Geometrie
p         = geschrumpft(treffer, faelle, basisrate) Trefferbilanz
schwelle  = (1 + kosten_r)/(1 + CRV)                Gebühren
traegt    = p > schwelle                            -> wird nur gebucht
```

**Drei Befunde, alle gemessen:**

| | |
|---|---|
| ⚠️ **Die Trefferbilanz ist leer** | 2.313 Signale, davon 1.618 `nicht_anwendbar`, 335 `einstieg_nie_erreicht` — **nur 96 mit echtem Ergebnis**. Eine Zelle braucht **50**. `geschrumpft(0,0)` liefert exakt die Basisrate |
| ⚠️ **Der Maßstab sind die Gebühren** | bei 3 % Spot-Kosten verlangt sie 53,3 % statt 33,3 % — der am 25.08. verworfene Maßstab |
| ⚠️ **Sie wirkt nicht** | bucht „verloren", der Code läuft ohne `return` weiter |

✔ **In Summe: Sie vergleicht eine Zahl, die die Basisrate ist, mit einer
Schwelle, die die Gebühren sind — und tut nichts mit dem Ergebnis.**

### Was sie sollte

> **Stufe 11 beantwortet: „Ist die erwartete Bewegung groß genug, dass sich
> diese Handlung lohnt — unabhängig von Gebühren und Betrag?"**

| | heute | Ziel |
|---|---|---|
| **Eingang** | Trefferbilanz (leer) + Gebühren | **Bewegungserwartung** aus dem Trichter + gemessene Beiträge |
| **Maßstab** | Breakeven mit Gebühren | eine **Potentialschwelle**, gebührenfrei |
| **Wirkung** | zählt | **verwirft** — und der Grund steht in der Mail |

---

## 4. Wo Potential, Wahrscheinlichkeit und Wirtschaftlichkeit hingehören

**Die Trennung ist am Code gemessen** (CRV 2,0, Stop 5 %, Krypto, H erfüllt —
die Quote ist überall 0,3783, nur der Maßstab wechselt):

| Ebene | Satz | Breakeven | Abstand | Erwartungswert |
|---|---|---|---|---|
| **Potential** | **0,00 %** | 33,33 % | **+4,5 Punkte** | **+0,135 R** |
| **Messreferenz** | 0,30 % | 37,33 % | +0,5 Punkte | +0,015 R |
| **Wirtschaftlichkeit** | 1,50 % | 53,33 % | **−15,5 Punkte** | **−0,465 R** |

**Wo jede Ebene gilt:**

| Ebene | gilt für | gilt NICHT für |
|---|---|---|
| **Potential (0,00 %)** | Stufe 11 · Vorfilter H · Auswahl · jede Rangfolge | die Mail als alleinige Zahl |
| **Messreferenz (0,30 %)** | Vergleiche zwischen Signalen, Messläufe | Betrieb |
| **Wirtschaftlichkeit (1,50 %)** | ⚠️ **ausschließlich die Mail** — Ihre Auskunft | **jeden Filter, jede Rangfolge** |

⚠️ **Derselbe Trade ist gebührenfrei gut (+0,135 R) und mit Bitpanda-Satz
schlecht (−0,465 R).** Wer mit 1,50 % filtert, verwirft Trades, deren
Zeitpunkt richtig ist — er misst die Börse, nicht den Markt.

---

## 5. Punkt 4 im Gesamtkonzept: von „zählen" zu „filtern"

**Ihre Frage:** *„jetzt zählt er, soll er zukünftig aktiv schlechte Trades
filtern statt zählen, und wie machen wir das?"*

**Ja — aber in dieser Reihenfolge, und keine Stufe darf vorgezogen werden:**

| # | Schritt | Warum genau hier | Art |
|---|---|---|---|
| **V-0** | **N-7 messen:** trägt die heutige LLM-Kette? | Ohne diese Antwort filtert Stufe 11 Rauschen nach Rauschen. Das Projekt hat sich den Vorrang selbst gegeben | **Messung** |
| **V-1** | **Maß festlegen:** Bewegungserwartung statt Zielerreichung | Sonst baut Stufe 11 auf dem blinden Maß auf. Werkzeug (`trichter.py`) ist gebaut | ⚠️ **Ihre Entscheidung** |
| **V-2** | **Beiträge gegen das neue Maß neu messen** — beginnend mit H | H's +4,5 Punkte gelten für „Ziel vor Stop", nicht für „Bewegung" | **Messung** |
| **V-3** | **Schwelle festlegen:** ab welchem Potential wird gehandelt? | Keine Messfrage — eine Risikoentscheidung | ⚠️ **Ihre Entscheidung** |
| **V-4** | **Stufe 11 umstellen:** Potential statt Gebühren-Breakeven | erst jetzt sinnvoll | Bau, klein |
| **V-5** | **Stufe 11 scharf schalten:** verwerfen statt zählen | erst wenn V-1 bis V-4 stehen | Bau, klein |
| **V-6** | **Vorfilter H in Stufe 11 überführen** | er trägt schon +4,5 Punkte bei — es fehlt nur die Wirkung | Bau, klein |

⚠️ **V-4 bis V-6 sind zusammen etwa ein Tag. V-0 bis V-3 sind die Arbeit.**

⚠️ **Warum die Reihenfolge zwingend ist:** Jeder vorgezogene Bauschritt
verschärft einen bestehenden Fehler. Stufe 11 scharf zu schalten, solange ihr
Maßstab die Gebühren sind, würde nach genau der Definition filtern, die am
25.08. verworfen wurde.

---

## 6. Was ich zur Abstimmung brauche

| # | Frage | Vorschlag des Fachexperten |
|---|---|---|
| **A** | Wird **N-7** (trägt die LLM-Kette?) vor allem anderen gemessen? | ✔ **ja** — das Projekt hat sich den Vorrang selbst gegeben, und alles Weitere hängt daran |
| **B** | Wird das Maß von **Zielerreichung** auf **Bewegungserwartung** umgestellt? | ✔ **ja** — die Zielerreichung kann per Konstruktion nicht antworten |
| **C** | Bleibt **1,50 %** ausschließlich in der Mail? | ✔ **ja**, unverändert |
| **D** | Ab welchem Potential wird gehandelt? | ⚠️ **keine Empfehlung ohne V-2** — die Zahl hängt daran, was die neu gemessenen Beiträge tragen |

**Erst wenn A bis C entschieden sind, ist V-4 bis V-6 sinnvoll baubar.**

Verwandt: `Regelwerksmanual.md` R-A1 bis R-A18 und „Die sechs Stufen des
Ablaufs" · `feedback_potential_statt_zielerreichung` ·
`Zwischenstand_Gesamtprojekt_06_08.md` Nachtrag 25.08. (N-5 bis N-7) ·
`agent/trichter.py` (Kapitel 93)
