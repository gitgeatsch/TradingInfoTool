# Vorabfestlegung 5 — ist `funding` ein zustandsabhängiger Schalter?

**23.09.2026, geschrieben VOR der Messung.** Nutzerauftrag: *„mach eine
genaue Vorbereitung, Recherche, Messstandards, prüfe welche Zustände
zulässig sind oder nicht (Monotonie, etc.) — **wir müssen hier erfolgreich
sein, sonst sind Monate an Arbeit verloren**."*

---

# § 1 Der Recherchestand — was **ist** gemessen

## 1.1 Was `funding` trägt, und wie

Aus `pruefe_funding_wirksamkeit.py` (30.08., 357.462 Anker, 2.417
Kalendertage, H20). **Die Regel:** *„kein Einstieg, dessen
Finanzierungsrate heute im obersten Fünftel des Marktquerschnitts liegt."*

| | |
|---|---|
| sperrt | **20,5 %** der Einstiege |
| Gesperrte | **−0,1776 R** |
| Übrige | −0,0943 R |
| **netto** | **+0,0234 R** [+0,0099 … +0,0381] |
| **B6** | ✔ beide Hälften (+0,0277 · +0,0191) |
| bei 90 % statt 80 % | +0,0154, zweite Hälfte fällt → die Grenze ist nicht beliebig |

**Vier Gegenproben, alle bestanden:** Momentum-Korrelation **−0,000** und
hält in jeder Schicht · Blocklänge 90–400 unverändert · hält auf den 151
ältesten Symbolen · hält in beiden BTC-Phasen.

## 1.2 Was **nicht** trägt — fünffach belegt

Die **Ordnung** über die Fünftel. `pruefe_funding_monoton.py` (30.08.):
*„monoton fallend? **NEIN** — kein stetiger Verlauf"*; gepoolt sind alle
fünf Fächer flach (−0,5041 / −0,4412 / −0,4885 / −0,5018 / −0,4867 über je
~71.000 Anker). Bestätigt durch N-56, 2.133/N23, 2.553, 2.554.

## 1.3 ⛔⛔ Zwei Korrekturen an meiner eigenen Darstellung

Beide in dieser Vorbereitung gefunden, **vor** der Messung:

### Korrektur 1 — der „Faktor 6,3" steht auf einer anderen Skala

`pruefe_funding_marktphase.py` ruft `M.je_tag_quer(teil)` — das ist die
**Merkmalsdifferenz** (unterstes minus oberstes Fünftel), **nicht** die
Regelwirkung. Die Zahlen +0,4308 / +0,0680 sind also **nicht** mit den
+0,0234 der Regel vergleichbar. R-R8 **B3** verlangt die Regel-Rechnung.

➔ **Die Marktphasen-Aussage muss auf der Regel-Skala neu gemessen werden.**

### Korrektur 2 — das Band steht auf **zwei Blöcken**

Dieselbe Datei ruft `urteil_tage(..., rng, 250)` — **Blocklänge 250** auf
431 Tagen, also **1,7 Blöcke**. Das Werkzeug warnt selbst: *„nur 2 Blöcke —
das Band deckt nicht"*.

➔ **Der Faktor 6,3 ist ein Hinweis, kein Befund.** Ich habe ihn als
„die wichtigste Zahl der Recherche" dargestellt; das war zu stark.

---

# § 2 ⚠️⚠️⚠️ Welche Zustände sind **zulässig** — sieben Kriterien

Abgeleitet aus R-R8 und den Fehlschlägen dieses Projekts. **Ein Zustand,
der eines davon verletzt, wird nicht gemessen.**

| # | Kriterium | Woher | Was hier daran scheitert |
|---|---|---|---|
| **Z1** | Die Grenze kommt aus der **Sache**, nicht aus der Verteilung | Vorabfestlegung 3 | Rangfünftel: die Grenze wandert mit der Tagesbesetzung |
| **Z2** | **Kein Massepunkt auf der Grenze** | heute gefunden | 0,0003 = Binance-Standardrate; 32,5 % Bindungen (2.551). Ein Median, der auf der Grenze klebt, kippt an einem Hauch |
| **Z3** | Der Zustand kommt in **beiden Historienhälften** vor | R-R8 **B6** | ⛔ **absolut: NEIN** — letzte Episode 2024-12-09 |
| **Z4** | **Häufigkeit** ausgewiesen und effektive Wirkung gerechnet | R-R8 **B4** | 18 % gegen 100 % — ohne das dreht sich die Rangfolge |
| **Z5** | **Monotonie** wird nur verlangt, wo eine **Ordnung** behauptet wird | 30.08. | funding hat keine → **Schalter**, und dort ist Monotonie gegenstandslos |
| **Z6** | Genug **unabhängige Episoden**, nicht nur Tage | heute gefunden | 428 Tage sind **15 Episoden**, eine davon trägt 45 % |
| **Z7** | **Kein Look-Ahead** in der Zustandsdefinition | Standard | ein rollendes Fenster darf nur zurückblicken |

## 2.1 Die Zulässigkeitsprüfung, gerechnet

| Definition von „überhitzt" | Tage | Episoden | 1. Hälfte | 2. Hälfte | letzte | **Z3** |
|---|---|---|---|---|---|---|
| **absolut** > Standardrate | 428 (17,8 %) | 15 | 294 / 10 Ep | 134 / 5 Ep | **2024-12-09** | ⛔ |
| **rollend** oberstes Fünftel/250 | 299 (12,5 %) | 13 | 124 / 8 Ep | **175 / 5 Ep** | **2026-08-29** | ✔ |
| **rollend** oberstes Zehntel/250 | 192 (8,0 %) | 12 | 67 / 6 Ep | 125 / 6 Ep | **2026-08-29** | ✔ |

> ⛔⛔ **Die absolute Definition — die, auf der der Faktor 6,3 steht — ist
> nach Z3 UNZULÄSSIG.** Sie kommt in den jüngsten 21 Monaten nicht vor.
> Eine Messung darauf wäre eine Aussage über eine vergangene Epoche.

✔ **Gewählt: rollend, oberstes Fünftel der letzten 250 Tage.** Sie erfüllt
Z1 (die Sache ist *„heiß relativ zum aktuellen Regime"*), Z2 (ein Rang
kennt keinen Massepunkt), Z3, Z7 (nur Rückblick) — und hat in der
**zweiten** Hälfte sogar **mehr** Tage als in der ersten.

⚠️ **Z6 bleibt die Schwachstelle: 13 Episoden.** Das ist die effektive
Stichprobe, nicht 299. Deshalb § 4.

---

# § 3 Die beiden Hypothesen

## Hypothese A — der Zustand des **Assets**

> *„Dieses Asset zahlt heute hoch / nicht hoch — daraus folgt eine
> Bewertung."*

**Stand: gemessen und belegt.** +0,0234 R netto, B6 erfüllt. Die
Dreiteilung (negativ / normal / hoch) ist **auf zwei Positionen
reduziert**: `normal minus negativ` +0,0132 [−0,0714 … +0,0943] trägt
nicht, und gepoolt ist das *niedrigste* Fünftel sogar das schlechteste.

➔ **A ist ein Zweistufen-Schalter. Er steht nicht zur Frage.**

## Hypothese B — der Zustand des **Marktes**

> *„Heute ist ein Tag, an dem Funding überhaupt etwas aussagt — oder
> nicht. Die Asset-Position zählt nur im ersten Fall."*

**Stand: nie auf der Regel-Skala gemessen.** Das ist die Messung.

---

# § 4 ⚠️⚠️ Die MACHBARKEITSSTUFE — sie läuft **zuerst**

**Die Lehre aus Vorabfestlegung 4:** dort kam die Positivkontrolle *nach*
dem Ergebnis, und das Urteil kippte von „Gleichstand" auf „nichts
entschieden". Diesmal steht sie **davor**.

> **Findet die Anlage auf der Hoch-Menge allein (299 Tage, 13 Episoden)
> einen gepflanzten Effekt — und ab welcher Stärke?**

| Ausgang | Folge |
|---|---|
| findet ab ≤ 0,10 R | ✔ **die Messung wird durchgeführt** |
| findet erst ab 0,20 R oder gar nicht | ⛔ **die Messung wird NICHT durchgeführt.** Die Datenlage reicht nicht; das Ergebnis wäre in jede Richtung wertlos |

⚠️⚠️ **Das ist kein Formalismus.** Genau diese Stufe hätte die vier
ergebnislosen Messungen des 23.09. verhindert.

---

# § 5 Die Messung

| | |
|---|---|
| **Werkzeug** | ⚠️ `messnorm.pruefe()` — **die eine Messung**, keine Nachbildung. Sie ruft `messe_regel_wirksamkeit.wirkung()`, dieselbe Funktion, mit der F-212 gerechnet wurde |
| **Frageart** | `beitrag` → Menge **selektiert** (F-212), und zusätzlich `markt` → Messuniversum als Gegenprobe |
| **Lage** | `spot × einstieg` → Zielgröße **`bewegung_r`** (`ZIELGROESSE_JE_LAGE`) |
| **Horizont** | H20, Blocklänge `_block(20)` = **60** — nicht 250 wie am 30.08. |
| **Nullpunkt** | Mittel über **40** Nullwelten, 90. Perzentil (Messstandard ab 09.09.) |
| **Trennschärfe** | gegen den Nullpunkt, Stärken bis 0,40 R, **5** Ziehungen |
| **Pflanzung** | ⚠️ **in die GEMISCHTE Welt**, nicht obendrauf — sonst misst die Kontrolle `Effekt + Pflanzung`. Die Norm macht das selbst; mein Werkzeug von heute tat es falsch |
| **Mehrfachtest** | drei Zustände = `hypothesen=3` |
| **B4** | Häufigkeit **und** effektive Wirkung je Signal werden ausgewiesen |

## 5.1 Die Stufen, in dieser Reihenfolge

| | | |
|---|---|---|
| **S0** | **Machbarkeit** (§ 4) | ohne ✔ endet es hier |
| **S1** | **R-R11 Reproduktion** — der 30.08.-Wert +0,0234 R auf dem heutigen Standard | ohne Reproduktion wird nichts umgestoßen |
| **S2** | **Hypothese B**: die Regelwirkung je Markt-Zustand (heiß / mittel / ruhig) | die eigentliche Frage |
| **S3** | **B6** — jeder Zustand in beiden Historienhälften | |
| **S4** | **B4** — Häufigkeit × Wirkung = effektiv je Signal | entscheidet über den Betriebsnutzen |

---

# § 6 Die Entscheidungsregel — vor der Messung

| Ergebnis | Entscheidung |
|---|---|
| **S0 fällt** | ⛔ **keine Messung.** Die Datenlage reicht nicht. Der Punkt wird als *nicht entscheidbar* geschlossen — und `funding` bleibt der belegte Zweistufen-Schalter aus A |
| **S1 fällt** (30.08. reproduziert nicht) | ⛔ **Stopp.** Dann steht die ganze funding-Registrierung zur Debatte, nicht die Form. Eigener Befund, keine Fortsetzung |
| S2 ✔ heiß **deutlich** über ruhig, **beide Hälften** (S3) | ✔ **B belegt.** Bauform: Zweistufen-Schalter A mit zustandsabhängigem Gewicht. Danach R-R9 (Schwelle) |
| S2 ✔, aber **S3 verletzt** | ⛔ **kein Umbau** (wie 2.553). B bleibt Hinweis |
| S2 Bänder **überlappen** | ➤ **B trägt nicht.** `funding` bleibt der Zweistufen-Schalter — und das ist dann ein **Ergebnis**, kein Patt |
| **S4**: effektiv je Signal **schlechter** als heute | ⛔ **kein Umbau**, auch wenn S2 und S3 tragen. B4 entscheidet über den Betrieb |

⚠️⚠️ **Diese Festlegung wird nicht nachverhandelt.** Insbesondere Zeile 1
und 2: ein Abbruch ist ein zulässiger Ausgang und wird als solcher
berichtet, nicht umgangen.

## 6.1 Was diese Messung ausdrücklich **nicht** entscheidet

- **Ob `funding` trägt.** Registriert, reproduziert (F-212: +0,0274).
- **Ob die Fünferleiter fällt.** Das ist fünffach belegt (§ 1.2) und
  unabhängig vom Ausgang hier.
- **Ob umgestellt wird.** Ein belegter Umbau braucht zusätzlich R-R9
  (Schwellenkalibrierung) und eine Betriebsprüfung am Notebook.

## 6.2 Die ehrliche Erfolgsaussicht

**Z6 ist das Risiko: 13 Episoden.** Wenn S0 fällt, ist das kein Scheitern
der Arbeit, sondern die Antwort *„diese Frage ist mit sechseinhalb Jahren
Krypto-Funding nicht zu beantworten"* — und die ist mehr wert als ein
Ergebnis auf zwei Blöcken.

⚠️ **Und dann trägt `funding` trotzdem.** A steht, mit +0,0234 R und
erfülltem B6. Die Monate Arbeit hängen nicht an B.

---

# ERGEBNIS — 23.09.2026

## ✔ S0 Machbarkeit bestanden — knapp

Auf der dünnen Heiss-Menge findet die Anlage gepflanzte **0,10 R**;
gefordert waren höchstens 0,10. **4 Blöcke.** Die Messung wird also
durchgeführt — und ein Nullergebnis wäre deutbar.

## ✔✔ S1 R-R11 reproduziert

| | |
|---|---|
| unbedingte Regel | **+0,02286 R** [+0,00998 … +0,03689] |
| Nullpunkt | +0,00893 |
| Basis | 2.151 Tage, **35 Blöcke** |
| 30.08. gemessen | +0,0234 |

**Die Registrierung steht.**

## ➤➤ S2 Der Zustand trägt — deutlich, und auf der **Regel**-Skala

| Zustand | Wirkung | Nullpunkt | Anteil | |
|---|---|---|---|---|
| **heiss** | **+0,08432 R** [+0,04964 … +0,12977] | +0,03167 | 13,7 % | ✔ |
| mittel | +0,01573 [+0,00746 … +0,08895] | +0,02803 | 55,9 % | ✖ |
| ruhig | +0,00823 [−0,00080 … +0,01964] | +0,01845 | 30,4 % | ✖ |

**Faktor 10** zwischen heiss und ruhig. Der Kern von Hypothese B ist
damit **belegt**.

## ⛔ S3 B6 nicht sauber prüfbar

| `heiss` | | |
|---|---|---|
| 1. Hälfte | +0,07018 [+0,06346 … +0,10949] | ✔ |
| 2. Hälfte | +0,09457 [+0,02898 … +0,16801], Null +0,03111 | ✖ |

⚠️ **Das ist ein Machtproblem, kein Wirkungsproblem:** die Wirkung ist in
der **zweiten** Hälfte **größer**; nur das Band ist breiter, weil je
Hälfte bloß **2 Blöcke** übrig bleiben. Nach § 6 heißt das **kein Umbau**
— so gebaut, so entschieden.

## ➤➤➤ S4 — die eigentliche Antwort, und sie hängt **nicht** an B6

| | Anteil | Wirkung | effektiv |
|---|---|---|---|
| **unbedingt (heute)** | 100,0 % | +0,02286 | **+0,02286** |
| nur `heiss` | 13,7 % | +0,08432 | **+0,01156** |
| nur `mittel` | 55,9 % | +0,01573 | +0,00879 |
| nur `ruhig` | 30,4 % | +0,00823 | +0,00250 |
| **Summe** | | | **+0,02286** ✔ |

✔ **Selbstkontrolle:** die Summe ergibt exakt die Gesamtwirkung.

> **Der Zustandsschalter wäre nur halb so gut** — er wirft die Wirkung der
> übrigen **86,3 %** der Tage weg.

Das ist **Arithmetik, nicht Statistik**: die Regelwirkung ist das über die
Tage gemittelte *„mit Regel minus ohne"*, und an einem Tag ohne Sperre ist
sie null.

## ✔✔✔ Ergebnis: die **unbedingte** Sperre ist die richtige Bauform

Hypothese B ist im praktischen Sinn **widerlegt** — obwohl ihr Kern
belegt ist. Das ist ein **Ergebnis**, kein Nullbefund.

### ⚠️⚠️ Die verallgemeinerbare Lehre

> **Ein Zustandsschalter lohnt nur, wenn ein Zustand die Wirkung
> UMKEHRT — nicht, wenn er sie bloß abschwächt.** Solange alle Zustände in
> dieselbe Richtung wirken, ist die unbedingte Regel zwangsläufig die
> beste, und keine Messung kann daran etwas ändern.

Das gilt für **jeden** künftigen Zustandsschalter und hätte diese Messung
vorab entscheidbar gemacht.

## ⛔ Drei Korrekturen, alle in der **Vorbereitung** gefunden

1. Der von mir als *„wichtigste Zahl der Recherche"* präsentierte
   **Faktor 6,3** stand auf der **Merkmals**-Skala (`je_tag_quer`) und war
   mit der Regelwirkung nicht vergleichbar — R-R8 **B3**.
2. Sein Band stand auf **1,7 Blöcken** (Blocklänge 250 auf 431 Tagen). Er
   war ein **Hinweis**, kein Befund.
3. Die **absolute** Zustandsdefinition, auf der alle 30.08.-Zahlen stehen,
   ist nach **Z3 unzulässig** — letzte Episode **2024-12-09**.

Befund **2.556-funding-zustandsschalter**.
