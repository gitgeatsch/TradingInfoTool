# Die Kalibrierung von `q` — das fehlende Stück der Hebelerzeugung

**26.09.2026** · Befund 2.622 · löst **2.558** (*„der Hebel hängt an einem
`q`, das nie kalibriert wurde"*)

> **Nutzerhinweis, der darauf führte:** *„oder war das `q`?"*
> — nach zwei Tagen an derselben Frage.

---

## ⛔ Zuerst: was ich fast gebaut hätte

Ich war dabei, eine „neue Hebelformel" aus Trefferquote und CRV zu
entwickeln. Dieselbe Formel steht seit langem im Code:

```python
# agent/betraege.py:365
kelly = (q * (1.0 + c) - 1.0) / c
```

`hebelrechnung()` liefert bereits `kelly`, `kelly_halb`, `r`, `klammer`,
`hebel_roh`, `hebel` (gedeckelt), `ist_hebel`, `grenze_greift` und die
Herleitungssätze für die Mail — samt der Regel *„Ohne positive Erwartung
kein Hebel"*.

➤ **Die Hebelerzeugung ist gebaut. Es fehlte nur ihr Eingang.**

---

## Wie `q` heute entsteht — und warum daraus kein Hebel wird

`agent/rollen_lauf.py:2190`:

```python
_hq_quote = _PTq.rechne(crv=2.0, instrument="hebel",
    merkmale={funding_fuenftel, turnover_fuenftel, schnitt_fuenftel}).quote
```

und darin (`agent/potential.py`, `agent/wahrscheinlichkeit.py:73`):

```python
q = basisrate(crv) + Beitragspunkte/100
basisrate(2.0) = 1/(1+2.0) = 0.3333
```

⛔⛔ **`1/(1+CRV)` IST die Kelly-Nullstelle.** Kelly ist damit **per
Konstruktion null**; der Hebel kann nur aus Beitragspunkten entstehen:

| Beitragspunkte | `q` | Kelly | halbes Kelly |
|---|---|---|---|
| +0,00 Pp | 0,3333 | **0,00000** | 0,00000 |
| +1,00 Pp | 0,3433 | 0,01500 | 0,00750 |
| **+3,34 Pp** | 0,3667 | 0,05010 | **0,02505** |

**Es bräuchte +3,34 Prozentpunkte, damit halbes Kelly überhaupt 2,5 %
erreicht.** Die registrierten Beiträge liegen bei Bruchteilen davon
(`funding` +0,0234 R).

### ⭐⭐⭐ Der Denkfehler steht im Docstring selbst

> `basisrate()`: *„Trefferquote eines **Barrierensystems** auf **driftfreiem
> Pfad**."*

Das ist ein **Nullmodell** — und es gilt für ein **Barrierensystem** mit
festem Ziel und festem Stop. **Die neue Geometrie ist ein
Trailing-System.** Dort gilt es nicht.

➤ Die Basisrate als **Startwert** zu nehmen und Beiträge draufzurechnen
unterstellt, die Realität entspreche dem driftfreien Nullmodell. **Sie tut
es nicht.**

⚠️ Und das erklärt **2.591** nachträglich: dort stand, *nur* die
angenommene Basisrate 0,3333 erzeuge Hebel, jede gemessene nicht. Richtig
war die Beobachtung — die Deutung nicht. Nicht die Messungen waren zu
schwach, sondern das Nullmodell war das falsche.

---

## ⭐ Die gemessene Kalibrierung

**3.181.434 Anker · 1.746 Tage · Geometrie H72 / Stop 1,0 ATR / Trailing
1,5 / 0,5** (aus 2.620), Bänder von `ema_abstand_atr`:

| Band | Signale | **`q`** | **CRV** | Kelly | halbes Kelly |
|---|---|---|---|---|---|
| 0,3–0,5 | 348.414 | 42,8 % | 1,349 | 0,0040 | 0,0020 |
| 0,5–0,7 | 174.408 | 43,8 % | 1,391 | 0,0340 | 0,0170 |
| 0,7–0,9 | 72.715 | 46,4 % | 1,440 | 0,0918 | 0,0459 |
| 0,9–1,1 | 25.435 | 47,9 % | 1,483 | 0,1277 | 0,0638 |
| **1,1–1,3** | 7.959 | **48,0 %** | **1,516** | **0,1370** | **0,0685** |
| 1,3–1,6 | 2.528 | 45,3 % | 1,562 | 0,1028 | 0,0514 |
| 1,6–2,0 | 444 | 40,5 % | 1,534 | 0,0171 | 0,0086 |

⭐ **Monoton bis Band 1,1–1,3, danach fällt Kelly.** Das CRV steigt zwar
weiter (bis 1,564), aber die Trefferquote bricht ein — und das überwiegt.

⚠️ **Gemessen in BÄNDERN, nicht kumulativ.** Ein kumulativer Schnitt
(„alle ≥ Schwelle") mittelt die besseren Lagen mit ein und beantwortet
nicht die Frage, die für **ein einzelnes Asset** zählt.

---

## Die Gegenprüfungen

| Prüfung | Ergebnis |
|---|---|
| **B6** — beide Fensterhälften | ✔ **5 von 6 Bändern** in beiden positiv. Nur 0,3–0,5 kippt (Kelly +0,029 / −0,022) — es liegt ohnehin nahe null |
| **Je Asset** — trägt die Ordnung symbolweise? | ✔ **35 von 44 Symbolen**. Zufall wäre 22, das sind **3,9 Sigma** |

⭐⭐ Die zweite Prüfung beantwortet die stehende Nutzervorgabe *„wir messen
nicht den Markt"*: Die Ordnung gilt **je Asset**, nicht nur im
Marktdurchschnitt. `ema_abstand_atr` ist ohnehin eine reine Asset-Größe —
Kurs gegen eigenen EMA, geteilt durch eigene ATR, **kein Querschnitt,
kein Rang**.

⚠️ Die **Eichung** braucht viele Assets — wie ein Thermometer an vielen
Orten geeicht wird. Die **Anwendung** braucht nur eines.

---

---

## ✔✔ Am Betrieb gegengeprüft, nicht nur am Code

> **Nutzerwarnung 26.09.:** *„du musst immer prüfen zwischen doku und code
> aus unterschiedlichen Umbauten."*

Aus den 22 echten Hebel-Signalen der Produktion (Notebook-Backup 23.09.)
lässt sich `q` zurückrechnen — `potential_r = q·CRV − (1−q)`:

| Symbol | `potential_r` | **q** | über 1/3 | Kelly | Hebel live |
|---|---|---|---|---|---|
| BNB | 0,0942 | 0,3647 | **3,14 Pp** | 0,04710 | 5,00 |
| **9 von 12** | **0,0390** | **0,3463** | **1,30 Pp** | 0,01950 | 2,26–2,92 |
| BNB (älter) | 0,0246 | 0,3415 | 0,82 Pp | 0,01230 | 3,52 |

✔ **Doku, Code und Betrieb stimmen überein.** Die Diagnose trägt durch.

### ⛔⛔ Und der Betrieb zeigt etwas Zusätzliches

**Neun von zwölf Signalen haben exakt denselben `potential_r`.** Das `q`
**differenziert heute praktisch nicht zwischen Assets** — die drei
Beiträge liefern fast überall denselben Wert.

➤ Die Spanne der Hebel (2,26–5,00) entsteht damit **nicht aus der
Bewertung**, sondern aus der Klammer `r_min`/`r_max` und dem Stopabstand.
Das bestätigt 2.558 (*„steuerndes Fenster 1 Prozentpunkt"*) am
Betriebsdatensatz.

| | q | CRV | Kelly |
|---|---|---|---|
| **Betrieb heute** | 0,3463 | 2,00 | 0,01950 |
| **gemessen** Band 1,1–1,3 | 0,4800 | 1,516 | 0,13699 |
| | | | **Faktor 7,0** |

---

## ⚠️⚠️ Vier Warnungen vor der Übernahme

| # | |
|---|---|
| **1** | **`q` und CRV gehören zusammen.** Die gemessene Quote mit dem angenommenen CRV 2,0 zu mischen ergäbe Kelly 0,219 statt 0,128 — **71 % Überschätzung**. Beide aus derselben Messung oder gar nicht |
| **2** | **Das gemessene CRV ist 1,48–1,52, nicht 2,0.** Damit unterschreitet die reale Geometrie `crv_minimum` (Z-2) — **das Gate würde genau die Signale ablehnen, die tragen**. Zu klären, bevor etwas verdrahtet wird |
| **3** | **Die Eichung gilt nur für diese Geometrie** (H72 / Stop 1,0 / Trailing 1,5/0,5) und diesen Zeitraum. Ändert sich die Geometrie, ändert sich `q` |
| **4** | **Über Band 1,3 fällt Kelly.** Der Hebel darf dort **nicht** weiter mitsteigen — ein Deckel ist nötig, keine Extrapolation |

---

## ⭐⭐ Sichtbar gemacht — dieselbe Vorgabe wie am 07.09.

> **Nutzervorgabe 26.09.:** *„Bitte diese beiden zentralen werte sauber in
> code Doku und Übersicht etc. anzeigen."*

Das ist **wortgleich** die Vorgabe, die am 07.09. für die Bewertungsschwelle
galt und im Code festgehalten ist:

> *„so einen Parameter vergesse ich in Kürze und du auch — **die Doku reicht
> bei so einer zentralen Einstellung nicht**."*
> *„⚠️ NUR DIE ÜBERSICHTSSEITE UND DIE GUI FEHLTEN NOCH … nachdem der
> Nutzer denselben Punkt erneut ansprach (**„aktuell ist es nur code"**)."*

⛔ **Für `q` war sie nie umgesetzt.** Es stand weder in `config.yaml` noch
in der Mail noch in der GUI — obwohl es die **Höhe jedes Hebels** bestimmt.

✔ **Jetzt in `agent/krypto/regelwerk_parameter.py`**, direkt hinter der
Bewertungsschwelle:

| Bezeichnung | Wert | Kategorie |
|---|---|---|
| Bewertungsschwelle (Potential in R) | 0,060 | b) Risikotoleranz |
| **Trefferquote q — Basisrate (Eingang der Hebelrechnung)** | **0,3333** | c) gemischt |

⚠️ **Angezeigt wird die Basisrate, nicht das fertige `q`** — sie ist der
Startwert, das `q` entsteht erst je Signal aus ihr plus den Beiträgen.

⚠️ **Sie wird aus `CRV_MINIMUM` gerechnet, nicht abgeschrieben.** Ändert
sich das CRV, zieht die Anzeige von selbst nach — dieselbe Lehre wie 2.546
(*eine zweite Zahl läuft auseinander*).

### ⚠️⚠️ Auflage für die Umstellung

Wird `q` von der Konstruktion auf die Messung umgestellt, gehört es
**genauso** behandelt wie die Schwelle: **`config.yaml`, Herleitung in der
Mail, GUI-Übersicht.** Nicht nur in den Code.

---

## Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ **Nichts gebaut, nichts geändert** — die Kalibrierung ist gemessen, nicht verdrahtet |
| **2** | Die **Abbildung Kelly → 2–5×** ist offen. `hebelrechnung()` macht sie über `r_min`/`r_max` und `hebelnenner_eur` — ob die Parameter zur neuen Kelly-Spanne passen, ist **ungeprüft** |
| **3** | Der **Einbruch der Einstiegsrate am 24.08.** bleibt unaufgeklärt |
| **4** | Nichts über **Short** |
