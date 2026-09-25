# H-A1 — die Basislinie des Hebeltrades

**24.09.2026.** Vorabfestlegung 10 · Plan Gesamtlage § 4, Schritt H-A.
⚠️ **Zwischenstand** — A2 (die Kandidaten) läuft noch.

---

# § 1 Die Zahlen

**25 Symbole, 173.575 Anker je Haltedauer, Takt 6 h, LONG, nur Krypto.**

| H | Ziel % | Stop % | offen % | **bedingte Quote** | Median `ergebnis_r` |
|---|---|---|---|---|---|
| **6 h** | 0,4 | 2,5 | **97,1** | **0,1361** | **+0,0000** |
| 12 h | 1,2 | 7,1 | 91,7 | 0,1459 | −0,0085 |
| 24 h | 3,4 | 16,5 | 80,1 | 0,1703 | −0,0334 |
| 48 h | 8,3 | 30,6 | 61,1 | 0,2126 | −0,1113 |
| 72 h | 12,7 | 39,9 | 47,4 | 0,2417 | −0,2502 |
| | | | | **Nullstelle 0,3333** | |

**Mit skaliertem Stop** (`× √(H/24)`) wird die Ausgangsverteilung
haltedauerneutral (Stop 13,4 % → 17,6 %), die Quote bleibt aber bei
0,1537 bis 0,1917 — ebenfalls **weit unter** der Nullstelle.

✔ **R-R11 hält:** bei 48 h gemessen 30,6 % Stop und 61,1 % offen —
2.582 (andere Stichprobe, Tagesbasis) sagte 29,5 % und 61,3 %.

---

# § 2 ⚠️⚠️⚠️ Der strukturelle Fund — die bedingte Quote ist die FALSCHE Größe

**Die Kelly-Nullstelle `1/(1+CRV)` = 0,3333 gilt für einen Random Walk bei
UNENDLICHEM Horizont.** Bei endlichem Horizont enden die meisten Trades
offen — und darunter sind die **langsamen Gewinner**, die zum Ziel gelaufen
wären.

➤ **Je kürzer das Fenster, desto stärker ist die bedingte Quote nach unten
verzerrt** — bei 6 h enden **97,1 %** offen, bewertet werden also **2,9 %**
der Trades, und zwar die schnellsten. Der nähere Stop (−1 R) wird dabei
überproportional zuerst erreicht.

## 2.1 Und daraus folgt ein Bruch in der Hebelrechnung

```python
kelly = (q * (1 + CRV) - 1) / CRV          # betraege.hebelrechnung
```

⚠️⚠️ **Diese Formel setzt einen BINÄREN Ausgang voraus** — gewinnen oder
verlieren. Der reale Hebeltrade hat **drei** Ausgänge, und der dritte ist
bei 6 h die Regel, nicht die Ausnahme.

| | |
|---|---|
| Was die Formel annimmt | `+CRV` mit Wahrscheinlichkeit `q`, sonst `−1` |
| Was tatsächlich passiert | `+CRV` (0,4 %) · `−1` (2,5 %) · **Zwischenstand (97,1 %)** |

➤ **Ein `q` aus 2,9 % der Fälle steuert die Hebelhöhe für 100 %.**

⚠️ **Das ist kein Messfehler — es ist ein Modellfehler.** Und er erklärt,
warum der Hebel auf kurzen Horizonten nie entsteht: `q` liegt dort
strukturell bei 0,14, die Nullstelle bei 0,33, also ist Kelly immer negativ.

## 2.2 ⚠️ Was daraus NICHT folgt

⛔ **Nicht**, dass der kurze Hebeltrade schlecht ist. Der Median von
`ergebnis_r` liegt bei 6 h bei **±0,0000** — der Trade ist dort praktisch
**fair**. Bei 72 h dagegen **−0,2502**.

➤ ⭐ **Je kürzer, desto weniger Verlust.** Das ist der Nutzerhinweis vom
24.09. (*„je kürzer desto geringer die Wahrscheinlichkeit in den Stop zu
laufen"*), jetzt gemessen — und er gilt, während die bedingte Quote das
Gegenteil suggeriert.

---

# § 3 ⚠️ Die offene Frage, die daraus entsteht

> **Auf welcher Größe soll die Hebelhöhe beruhen, wenn 97 % der Trades
> weder Ziel noch Stop erreichen?**

| Kandidat | |
|---|---|
| **heute** | `kelly = (q(1+CRV)−1)/CRV` aus der bedingten Quote — **misst 2,9 % der Fälle** |
| **Alternative** | Kelly aus Erwartungswert und Streuung von `ergebnis_r` — nutzt **alle** Anker |

⚠️⚠️ **Das ist eine ENTWURFSFRAGE, keine Messung** — und sie gehört dem
Nutzer vorgelegt. Diese Messung stellt sie, sie beantwortet sie nicht.

⚠️ Auf der **ungefilterten** Menge ist auch der Erwartungswert negativ
(−0,0018 bei 6 h bis −0,0191 bei 72 h). Ob eine **Teilmenge** darüber
liegt, ist genau die Frage von A2.

---

# § 4 Was A1 für den weiteren Weg bedeutet

| | |
|---|---|
| **H-B (Stufen)** | die Kandidaten müssten `q` um **rund 20 Punkte** heben, um die Nullstelle zu erreichen. Die gemessenen Beiträge bewegen **3** (funding). ⚠️ Über die bedingte Quote ist der Hebel nicht zu begründen |
| ⭐ **Neuer Weg** | über `ergebnis_r` beträgt die Lücke bei 6 h nur **0,0018** — das ist eine ganz andere Größenordnung |
| **H-D (Einstieg)** | unberührt |

---

# § 5 Stand

- ✔ **A1 gemessen**, R-R11 gehalten.
- ⏳ **A2 läuft** — sechs Kandidaten × fünf Haltedauern, Nullpunkt aus 200
  Welten mit **Stundenklammer**, Kontrolle `zufall`.
- ⛔ **Nichts committet, nichts am Betrieb geändert.**
