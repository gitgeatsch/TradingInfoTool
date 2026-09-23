# Voranalyse M1 / Hebel — der Hebel ist heute ein Ein-Aus-Schalter

**23.09.2026.** Nutzerfokus: *„jetzt sind wir bei M1 Hebel."*
M1-Kriterium 2 lautet *„Hebel gemessen"*, offen ist laut 2.533 *„der
Faktor unter der JETZIGEN Schwelle"*.

⚠️ **Diese Voranalyse ist reine Vorwärtsrechnung** aus `betraege.py` und
den Vorgaben — keine Signale, keine Rückrechnung aus geklammerten Werten.
Damit ist sie **nicht** der zirkuläre Fehler, an dem der frühere Befund 2c
gescheitert ist.

---

## § 1 Ist-Stand am Code

`agent/betraege.py:322` `hebelrechnung()`:

```
kelly  = (q · (1+CRV) − 1) / CRV
halb   = kelly / 2
r      = clamp(halb, r_min, r_max)        ← DIE KLAMMER
risiko = r · Kapital
hebel  = (risiko / stop) / hebelnenner,   gedeckelt auf hebel_grenze
```

**Vorgaben** (`HEBEL_AUS_QUOTE_VORGABE`):

| | |
|---|---|
| `r_min` | 0,0050 |
| `r_max` | 0,0125 |
| `hebel_ab` | 2,0 |
| `hebel_grenze` | 5,0 |
| `hebelnenner_eur` | 500,0 |

---

## § 2 ⚠️⚠️⚠️ Der Befund: drei Schwellen, ein Prozentpunkt

Aus der Formel folgen **drei** Quotenschwellen, alle rechnerisch exakt:

| | Quote | was dort passiert |
|---|---|---|
| Kelly wird null | **0,3333** | darunter: **gar kein Hebel** |
| halbes Kelly erreicht `r_min` | **0,3400** | darunter: Quote **wirkungslos**, r klebt an r_min |
| halbes Kelly erreicht `r_max` | **0,3500** | darüber: Quote **wirkungslos**, r klebt an r_max |

> **Das steuernde Fenster der Quote ist 0,3400 bis 0,3500 — ein einziger
> Prozentpunkt.**

### Alle 25 Merkmalslagen (funding × turnover, krypto, Stop 8 %)

```
          tu=0    tu=1    tu=2    tu=3    tu=4
fu=0    0.3647= 0.3465✔ 0.3449✔ 0.3404✔ 0.3109⛔
fu=1    0.3695= 0.3513= 0.3497✔ 0.3452✔ 0.3157⛔
fu=2    0.3577= 0.3395~ 0.3379~ 0.3334~ 0.3039⛔
fu=3    0.3511= 0.3329⛔ 0.3313⛔ 0.3268⛔ 0.2973⛔
fu=4    0.3395~ 0.3213⛔ 0.3197⛔ 0.3152⛔ 0.2857⛔
```

| | Anteil |
|---|---|
| ⛔ **gar kein Hebel** | **44,0 %** |
| ~ Quote wirkungslos (unter `r_min`) | 16,0 % |
| ✔ **Quote steuert** | **20,0 %** |
| = an der Obergrenze geklemmt | 20,0 % |

➔ **In vier von fünf Merkmalslagen ist die Bewertung für den Hebel
wirkungslos** — entweder gibt es keinen Hebel, oder `r` klebt an einer
Klammergrenze.

---

## § 3 ⚠️⚠️ Warum das strukturell ist, nicht zufällig

Die **Basisrate ohne jeden Beitrag ist 0,3333** — und die Kelly-Nullstelle
bei CRV 2 liegt bei `1/(1+CRV)` = **0,3333**. Das ist **dieselbe Zahl**.

> **Ein Trade ohne Bewertung ist per Konstruktion exakt break-even.**
> Jeder Hebel entsteht damit **ausschließlich** aus dem Beitragszuschlag.

Und die Beiträge bewegen die Quote um rund **±3 Punkte**, bei einem
steuernden Fenster von **1 Punkt**.

➔ **Der Hebel ist deshalb kein stetiger Faktor aus der Bewertung, sondern
ein Schalter mit drei Rasten:** kein Hebel / Mindesthebel / Maximalhebel.

---

## § 4 Die Verbindung zur funding-Lage

`funding` allein bewegt die Quote um **3,0 Punkte** (0,3197 bis 0,3497) —
das **Dreifache** der Fensterbreite. Es entscheidet damit über die Raste.

Und dieser Beitrag:

| | |
|---|---|
| liegt **an der Nachweisgrenze** | 2.557, dritte Bestätigung (V2/N-73, V11) |
| wechselt **täglich** bei 17,58 % der Symbole die Kante | gemessen |
| ist auf der Hebel-Zielgröße `barriere` **nie gemessen** worden | alle Messungen liefen auf `bewegung_r` |

> ⚠️⚠️ **Damit steuert ein an der Nachweisgrenze liegender Beitrag einen
> Ein-Aus-Schalter.** Genau das ist die Falle, die der Nutzer beschrieben
> hat — nur sitzt sie nicht an der funding-Kante, sondern an der
> **Kelly-Klammer**.

Und es erklärt drei bestehende Befunde ohne neue Annahme:
2.517 (Median sprang 1,00 → 3,49), 2.534 (alle 21 Hebelsignale auf dem
Lückenrabatt), 2.533 (*„unter 0,060 ist der genaue Faktor offen"*).

---

## § 5 Die Handlungsoptionen — mit ihren Konsequenzen

| | Eingriff | Wirkung | Preis |
|---|---|---|---|
| **A** | `r_min` senken / `r_max` heben | breiteres Fenster, stetigerer Hebel | ⚠️ das sind **Risikogrenzen** (Kapitalanteil je Trade), keine Bewertungsgrößen. Ein Eingriff ändert das **Risiko**, nicht die Bewertung |
| **B** | CRV anheben | Kelly-Nullstelle sinkt unter 0,3333, mehr Lagen bekommen Hebel | ⚠️ CRV ist eine **Geometrie**frage (Ziel/Stop), keine Stellschraube für den Hebel |
| **C** | Quote anheben (stärkere/mehr Beiträge) | mehr Lagen im Fenster | ⛔ genau daran arbeiten wir seit Wochen — es gibt keinen dritten Beitrag (V11) |
| **D** | Anerkennen und **auslegen** | der Hebel bleibt dreistufig, wird aber **bewusst** so gebaut und dokumentiert | ⚠️ dann ist „dynamisch aus dem CRV" die falsche Beschreibung |

⚠️⚠️ **Keine dieser Optionen ist eine Messfrage.** Das ist eine
**Entwurfsentscheidung** — und sie gehört dem Nutzer vorgelegt, nicht von
mir gewählt.

---

## § 6 Was diese Voranalyse **nicht** sagt

- **Nicht**, dass die Hebelformel falsch ist. Sie ist konsistent; die
  Klammer ist eine bewusste Risikobegrenzung (H-5, RM-11).
- **Nicht**, dass `funding` abgeschaltet gehört. Der Punktwert
  reproduziert, der Beitrag trägt auf 2.151 von 2.401 Tagen.
- **Nicht**, wie oft die Lagen im **Betrieb** vorkommen. Die 25 Felder
  sind gleichgewichtet gezählt — die echte Häufigkeit je Feld ist
  **ungemessen** und wäre der nächste Schritt, falls eine Option gewählt
  wird.
