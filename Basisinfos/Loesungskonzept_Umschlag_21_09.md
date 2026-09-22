# Lösungskonzept `umschlag` — Stand 21.09.2026

> **Auftrag (Nutzer, 21.09.):** *„wir brauchen einen Ersatz für die
> aktuelle Turnover Situation"* — nachdem die Abdeckung als das
> eigentliche Problem erkannt war.

---

## 1. Das Problem in einem Satz

> **`turnover` ist auf 59 Symbolen kalibriert und wird auf 537
> angewandt.** Bei 80 % der Spot-Signale und 94 % der Hebelsignale fehlt
> der Wert.

⚠️ **R-R8/B4 verlangt, die Häufigkeit zu *nennen* — nicht, dass sie
ausreicht.** Eine Mindestgrenze gibt es im ganzen Regelwerk nicht. Das
ist die Lücke, durch die das gerutscht ist.

---

## 2. Die drei Größen — und warum nur eine trägt

| | Nenner | Symbole | Historie | Lage |
|---|---|---:|---|---|
| **`umschlag_gesamt`** | Gesamtausgabe (Coin Metrics `SplyCur`) | **59** | 2.636 Tage | ⚠️ **live** — kalibriert, aber schmal |
| **`umschlag_frei`** | freier Umlauf (CoinGecko) | 375 | **365 Tage** | ⛔ nicht robust, B6 fällt |
| **`umschlag_naeherung`** | **heutige Menge rückwärts konstant** | **366** | **2.956 Tage** | ✔ **trägt** |

⚠️ **Eine Umrechnung zwischen `gesamt` und `frei` gibt es nicht** — das
Verhältnis ist je Coin verschieden (Median 25 %, XLM 67 %), ein Wechsel
verschiebt 76,7 % aller Fünftel.

---

## 3. Der Gedanke hinter der Näherung

```
turnover = Volumen / (Preis × Menge)
              ↑         ↑        ↑
           volle     volle    fehlt für 476 Symbole
          Historie  Historie   → heutige Menge konstant ansetzen
```

**Der Engpass war nie die Größe und nie die Quelle — es war die eine
fehlende Zahl.** Preis und Volumen liegen seit Jahren für 505
Kryptoreihen vor.

⚠️ **Diese Option stand seit dem 13.09. im Register** (2.417-naeherung:
*„Als Ausweitung auf Symbole, für die es gar keine gibt, bleibt sie
offen"*) und wurde acht Tage nicht verfolgt.

---

## 4. Was gemessen ist

### Wirkung (`bewegung_r`, Fenster ab 2023, alle zulässigen Mengen)

| Arm | Symbole | trägt auf |
|---|---:|---|
| **ECHT** — echte Menge, *Maßstab* | 44 | 6 von 6 |
| **NAEH-GEM** — Näherung, *dieselben* Symbole | 47 | 5 von 6 |
| **NAEH-VOLL** — Näherung, alle | **366** | **14 von 15** |

**Auf H5 und H20 trägt sie auf allen fünf Mengen** — die
Vorabfestlegung ist erfüllt.

### Die Zerlegung — der Kern

| | Median |
|---|---|
| **Näherungsfehler** (NAEH-GEM − ECHT) | **−0,0008 R** — praktisch null |
| **Mengengewinn** (NAEH-VOLL − NAEH-GEM) | **+0,0022 R** |

⚠️ Ohne den mittleren Arm wäre beides nicht zu trennen.

### Und auf `barriere`, wo bisher nichts trug

| Arm | trägt auf |
|---|---|
| ECHT | **0 von 6** |
| NAEH-GEM | **0 von 6** |
| **NAEH-VOLL** | **8 von 15** |

Mengengewinn dort **+0,0124 R** — fünfmal so groß. 2.490-barriere-niemand
galt für die 44 Symbole der alten Quelle.

### Weitere Prüfungen

| | |
|---|---|
| **Statistische Macht** | **90 Blöcke** statt 23 |
| **Regel 3** (ICC) | ✔ **54,5 %** gegen 63,1 % beim Original — *kein* zusätzlicher Asset-Festwert |
| **R-R8/B3** | ✔ erfüllt — sechs von sechs Gegenproben identisch |
| **Monotonie** (Vorabfestlegung 01.09.) | ✔ auf **H5** (+0,37 · +0,33 · +0,33 · +0,02 · −1,05) |
| **R-R8/B6** | ✔ **erfüllt** — die **Wirkung** trägt in beiden Hälften (+0,0179 / +0,0164, je 45 Blöcke) |
| **Saatprobe** | ✔ alle 5 Zellen, 5/5 Bootstrap **und** 4/4 Nullwelt |

---

## 5. ⚠️ Die Form ist eine andere: Schalter, nicht Regler

| Tabelle | Spanne 0–3 | Sprung 3→4 | Anteil |
|---|---:|---:|---:|
| `umschlag_naeherung` H5 | 0,35 | **1,07** | **75 %** |
| `umschlag_naeherung` H3 | 0,27 | 0,79 | 75 % |
| `umschlag_gesamt` H20 *(live)* | **4,96** | 0,65 | **12 %** |
| `funding` H20 *(live)* | 2,03 | 1,08 | 35 % |

➤ **Bei der Näherung trägt die Ordnung der Fünftel 0–3 praktisch nichts.**
Das ist die Form einer **Sperre** — dieselbe, die F-170 für den
`volumenanteil` fand (*„SPERRE, kein Regler — belastbar allein
Fünftel 4"*).

⚠️ **Und das bestätigt B6 unabhängig:** was über beide Hälften stabil
bleibt, ist **Fünftel 4** (−0,91 und −1,20). Die Unordnung betrifft nur
die vier oberen, die alle nahe null liegen.

---

## 6. Was daraus folgt — und was nicht

### ✔ Was die Näherung kann

| | |
|---|---|
| **Abdeckung** | 59 → **366** Symbole |
| **Fensterlänge** | 365 → **2.956** Tage, damit auch H20 |
| **`barriere`** | erstmals eine Größe, die dort trägt |
| **Als Sperre** | belegt, mit B3 nachgewiesen |

### ⛔ Was sie nicht kann

| | |
|---|---|
| **Die Stufentabelle ersetzen** | andere Form — 75 % gegen 12 % im obersten Fünftel |
| **Als REGLER auftreten** | die Form ist in der ersten Hälfte Zickzack — aber `umschlag_gesamt` ebenso |
| **Den Näherungsfehler über die volle Historie belegen** | Mengendrift nur über 365 Tage bekannt |

---

## 7. ⛔ KORREKTUR 21.09. — die Sperre fällt an B4

**Nutzereinwand:** *„als Sperre registrieren — kann ich so nicht
entscheiden. Dazu brauche ich die Entscheidungsgrundlage."* **Berechtigt.**
Gemessen war die *statistische* Wirkung, nicht die **Folge im Betrieb**.

### An den echten Signalen nachgemessen (2.550 Einstiege, 41 Symbole)

| | Signale | Anteil |
|---|---:|---:|
| hätten mit Näherung einen Wert | **1.605** | **62,9 %** |
| haben heute einen Wert | 500 | 19,6 % |
| ⚠️ **würde die Sperre treffen** | **20** | **0,8 %** |

Betroffen: **TURBO** (13) und **BEAMX** (7). Der Grund: unsere
Watchlist-Werte liegen selten im obersten Umschlag-Fünftel des Marktes —
die Momentum-Auswahl sortiert sie vorher aus.

### ➤ Damit fällt die Sperre an R-R8/B4

```
Wirkung  +0,0172 R  ×  Häufigkeit 0,8 %  =  effektiv +0,00014 R
```

⚠️ **Meine Empfehlung war voreilig.** Sie stand auf der **Messmenge**
(366 Symbole, dort trägt die Sperre), nicht auf der **Betriebsmenge**
(41 Symbole, dort trifft sie fast nichts).

### ✔ Was statt dessen zählt — und es ist mehr, nicht weniger

| Signale auf **gesenkter** Schwelle | |
|---|---|
| heute | **80,4 %** |
| mit Näherung | **37,1 %** |

**Das halbiert die Fälle, in denen die Datenlücke die Latte senkt.**

⛔ **Was dafür fehlt:** die Wirkung der Näherung **als Regler** ist
**nicht gemessen** — `messnorm` rechnet mit `oben_sperren=True`, also
die *Sperr*wirkung. Die Stufentabelle auf H5 existiert, ihre
Reglerwirkung nicht.

---

## 8. Der Vorschlag — Stand nach der Korrektur

| # | Schritt | Lage |
|---|---|---|
| **1** | ~~als **Sperre** registrieren~~ | ⛔ **VERWORFEN 21.09.** — fällt an B4: trifft nur **0,8 %** der Signale, effektiv +0,00014 R |
| **1b** | Die **Abdeckung** nutzen — Signale mit Wert von 500 auf 1.605 | ⚠️ **dafür fehlt die REGLER-Wirkung**, gemessen ist nur die Sperrwirkung |
| **2** | `umschlag_gesamt` als Regler **belassen**, wo er Daten hat | keine Änderung |
| **3** | Die **Schwellenfrage** getrennt behandeln | unabhängig von 1 und 2 |

✔✔✔ **Zu Schritt 1 — die offene Frage ist beantwortet.** Ich hatte
gemeldet, B6 falle. **Das war die falsche Frage:** R-R8/B6 sagt
*„fällt durch, wenn **der Befund** nur in der ersten Hälfte trägt"* —
und der Befund einer **Sperre** ist die **Wirkung**, nicht die Form
(die Stufen werden dort gar nicht angewandt).

Nachgemessen (H5, `bewegung_r`, frei):

| | Wirkung | Blöcke | |
|---|---|---:|---|
| ganz | +0,0172 | 90 | TRÄGT |
| **1. Hälfte** | **+0,0179** | 45 | ✔ TRÄGT |
| **2. Hälfte** | **+0,0164** | 45 | ✔ TRÄGT |

➤ **Alle sechs R-R8-Bedingungen sind für die Sperrform erfüllt.**
Die Formfrage bleibt eine **Regler**-Frage — dort fällt
`umschlag_gesamt` genauso.

⚠️ **Was ich nicht empfehle:** einen Nennerwechsel. Weder `frei` noch
`naeherung` ersetzen die registrierte Tabelle; sie sind eine **zweite
Größe mit anderer Form**, kein Ersatz für die erste.

---

## Belege

Befunde **2.515-naeherung-traegt**, **-form-schalter**, **-b3-erfuellt**, **-b6-erfuellt**, **-saatprobe** ·
2.417-naeherung · 2.505-* · F-170 · F-212 · R-R8

Werkzeuge: `phase4_c_naeherung_konstante_menge.py` ·
`phase4_c_naeherung_als_sperre.py` ·
`rechne_turnover_beitrag.py --umschlag naeherung` ·
`phase4_c_stufen_beide_haelften.py` · `phase4_c_saatprobe_freefloat.py`
