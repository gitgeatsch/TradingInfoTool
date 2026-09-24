# P-9 auf der Stundenbasis — der Befund

**24.09.2026.** Nutzerauftrag: *„zuerst P-9 - prüfen und gegenprüfen"* ·
*„ja Stundenbasis zuerst - prüfen und gegenprüfen"*

⚠️ **Nichts committet, nichts am Betrieb geändert.**

---

# § 1 Was gefragt war

`q` ist die Barrieren-Trefferquote, aus der über Kelly der **ganze Hebel**
entsteht. Die Vermutung: die Regel *„bei Gleichstand gewinnt der Stop"*
(`messe_zielregel.py`) drückt `q` systematisch — auf Tagesdaten ist die
Reihenfolge innerhalb des Tages unbekannt.

Seit dem 24.09. liegen **3.244.186 Stundenkerzen** vor. Dort ist sie
auflösbar.

---

# § 2 ⛔ Die Vermutung ist widerlegt

**Voller Lauf, 536 Krypto-Reihen, 649.160 Anker:**

| | |
|---|---|
| entschiedene Anker | **644.336** |
| davon **Gleichstand** | **4.071 = 0,63 %** |
| stündlich aufgelöst | **207 Ziel · 195 Stop · 21 auch stündlich unklar** |
| Wirkung auf `q` | **+0,0003** |

➤ **48,9 % gegen 46,1 % — das ist die Signatur von Zufall, nicht von
Verzerrung.** Die vorsichtige Annahme war über Jahre praktisch kostenlos.

⚠️ **Einschränkung, benannt:** 3.648 der 4.071 Fälle (89,6 %) liegen **vor
2021-12** und sind mangels Stundendaten nicht bewertbar. Die Aussage steht
auf **402** aufgelösten Fällen.

## 2.1 ✔ Beide Gegenprüfungen grün

| | |
|---|---|
| **A — der Schalter ist unschädlich** | 649.160 Zeilen, **0 Abweichungen** in allen gemeinsamen Schlüsseln. `messe_zielregel.ergebnisse()` hat 44 Aufrufer; sie rechnen bitgleich weiter (R-R11) |
| **B — die Stundenrechnung stimmt** | **78 von 78** eindeutigen Ankern: Stunde und Tag nennen dieselbe Barriere zuerst |

⚠️ **B wurde einmal falsch gebaut und vor dem Lauf korrigiert:** die erste
Fassung prüfte am **Ankertag**. Der Einstieg ist dessen *Schlusskurs* — die
Kerzen davor können die Schwelle längst berührt haben. Geprüft wird am
**Entscheidungstag**.

---

# § 3 ⭐⭐⭐ DER EIGENTLICHE FUND — `q` IST KEINE KONSTANTE

**Trefferquote je Jahr, CRV 2,0, Stop −1 R:**

| Jahr | Anker | Quote | |
|---|---|---|---|
| 2018 | 1.475 | 29,0 % | |
| 2019 | 8.941 | 31,6 % | |
| 2020 | 28.582 | **42,6 %** | ⭐ |
| 2021 | 62.856 | 39,5 % | |
| 2022 | 100.031 | 34,6 % | |
| 2023 | 114.419 | **40,2 %** | |
| 2024 | 124.412 | 35,0 % | |
| **2025** | 128.819 | ⛔ **26,4 %** | **unter der Nullstelle** |
| **2026** | 74.801 | ⛔ **30,9 %** | **unter der Nullstelle** |
| **alle** | **644.336** | **34,4 %** | |

> **Die Quote schwankt um 16 Prozentpunkte — und die letzten beiden Jahre
> liegen UNTER der Kelly-Nullstelle von 33,3 %.**

## 3.1 ⚠️⚠️ Warum das der härteste Punkt ist

```python
def basisrate(crv: float) -> float:
    """Trefferquote eines Barrierensystems auf driftfreiem Pfad."""
    return 1.0 / (1.0 + float(crv))          # = 0,3333 bei CRV 2
```

`q = basisrate + punkte/100` — die Bewertung **addiert** auf eine
**Konstante**.

| | |
|---|---|
| 2020 | die Konstante ist **9,3 Punkte zu niedrig** |
| **2025** | die Konstante ist ⛔ **6,9 Punkte zu HOCH** |

➤ **In 2025 hätte die Formel Hebel erzeugt** (0,3333 + Punkte > Nullstelle),
während die tatsächliche Quote bei **26,4 %** lag. Der Hebel wäre auf einem
strukturellen Verlustgeschäft aufgebaut worden — **und niemand hätte es
gemerkt**, weil beide Seiten für sich stimmig aussehen.

⚠️ **Der Mittelwert 34,4 % verdeckt genau das.** Über alle Jahre ist Kelly
positiv (+0,0159). Im aktuellen Regime ist er negativ.

---

# § 4 Die drei Schichten von P-9 — sauber getrennt

| # | | Stand |
|---|---|---|
| **1** | `basisrate` **ist** die Kelly-Nullstelle → ohne Beitrag per Konstruktion break-even | ⚠️ bekannt (2.558) |
| **2** | Die Beiträge heben `q` um **+0,040** statt **+0,333** — Faktor 8,3 zu flach | ⚠️ bekannt (2.558), **heute bitgleich reproduziert** |
| **3** | ⭐ **Die tatsächliche Basisrate schwankt um 16 Punkte und liegt seit 2025 unter der Nullstelle** | ⛔ **NEU, 24.09.** |

**Schicht 3 ist neu und sie ist die härteste** — sie sagt, dass selbst eine
*perfekt* kalibrierte Bewertung im aktuellen Regime gegen eine negative
Basisrate anrechnen müsste.

---

# § 5 ⚠️ Ein Widerspruch, der offen bleibt

| Lauf | entschiedene Anker | `q` |
|---|---|---|
| `messe_bewertung_kalibrierung` | 274.079 | **31,3 %** |
| dieser Lauf | 644.336 | **34,4 %** |

Beide laden **dieselben** Reihen über `B.lade()`. Der Unterschied ist der
**Potentialfilter** — die Kalibrierung braucht Anker mit funding-,
turnover- und vola-Daten.

➤ **Auf genau den Ankern mit Merkmalsdaten ist die Quote 3,1 Punkte
schlechter.** Ob das der Zeitraum ist (Merkmale gibt es erst ab 2020) oder
eine Eigenschaft der Abdeckung, ist **nicht geklärt**. Eine Vermutung wäre
hier keine Erklärung.

⚠️ Der Jahresvergleich schließt den reinen Zeitraumeffekt **nicht** aus:
„ab 2021" ergibt 34,06 %, also fast den Gesamtwert.

---

# § 6 ⚠️ Was diese Messung NICHT sagt

- **Nicht**, dass der Hebel unmöglich ist. Sie sagt, dass die **Basisrate**
  keine Konstante ist.
- **Nicht**, dass die Jahreszahlen unabhängig sind — die Fenster
  überlappen (60 Tage). Die effektive Blockzahl ist kleiner als die
  Ankerzahl; bei 16 Punkten Spanne ist der Befund davon aber kaum bedroht.
- **Nicht**, wie zu reagieren wäre. Eine zustandsabhängige Basisrate wäre
  ein **Entwurf**, keine Messung — und er gehört dem Nutzer vorgelegt.
- **Nicht** P-1, P-22 oder die Kette.

---

# § 7 Geändert wurde

| Datei | |
|---|---|
| `messe_zielregel.py` | `ergebnisse(..., mit_gleichstand=False)` — Vorgabe **bitgleich**, per Gegenprüfung A nachgewiesen |
| `messe_gleichstand_stundenbasis.py` | **neu** — das Messwerkzeug, mit beiden Gegenprüfungen fest eingebaut |

⛔ **Nicht committet.** Kein Betriebscode berührt.
