# Die stetige Hebelkurve — Ergebnis

**26.09.2026** · Befund **2.630** · `messe_hebelkurve_stetig.py` ·
Vorabfestlegung 26

> **Der Nutzereinwand, der sie ausgelöst hat:** *„hier ist es etwas
> stufenartig und nicht regelmäßig — Warum nicht −1,3?"* und *„eigentlich
> sollte das System entscheiden ob −1,0 jetzt besser ist und den Hebel so
> anwenden, also ich habe mir das so vorgestellt, dass eben das Risiko mit
> der Qualität steigt, also der Hebel"*

**Beides trifft zu.** Die Bandgrenzen −2,0 / −1,5 / −1,2 / −1,0 waren von
mir **gesetzt**, nicht gemessen — vier Stellschrauben, und auf *„warum
nicht −1,3"* gibt es keine nicht-willkürliche Antwort.

---

## Was die Bandmessung trotzdem belegt

Sie fällt nicht, sie wird **ersetzt**. Was sie gezeigt hat, gilt: die
**Ordnung ist da**.

| Prüfung | Ergebnis |
|---|---|
| Ertrag fällt von oben nach unten | **5 von 5 Jahren** (rho −1,00 in 2022/23/24, −0,80 in 2025/26) |
| starkes Band schlägt schwaches je Symbol | **54 von 63** · p = 3,1·10⁻⁹ |
| dasselbe über vier Zeitblöcke | **4 von 4** |

## Die Kurve — ohne eine einzige Bandgrenze

21 Stützstellen auf **Perzentilen** von `ema_abstand_atr`, je 4.000 Anker
gleitend, `q` und `CRV` je Fenster, Kelly aus derselben Formel wie
`agent/betraege.py:365`.

### ⚠️ Der rohe Kelly ist NICHT monoton

**rho −0,270, p 0,236.** Er ist **U-förmig**: bei `W` +0,47 steigt er
wieder auf +0,0263 — das ist die **Momentum-Seite**.

⭐ Der Grund: **der Nullpunkt ist nicht null.** Die tagestreue Nullwelt
liegt bei `W` −1,55 bei Kelly **−0,5703**, weil die scharfen Lagen auf
Crashtagen liegen. Dasselbe Prinzip wie bei `E[R]`: *der Nullpunkt ist
die Drift, nicht null.*

### ✔✔✔ Im Abstand zum Nullpunkt ist sie praktisch perfekt monoton

**rho −0,9987, p 4,9·10⁻²⁶ · 19 von 20 Schritten fallend**

| Perzentil | `W` | Kelly echt | Nullpunkt | **Überschuss** |
|---|---|---|---|---|
| 0,08 % | −1,551 | +0,0859 | −0,5703 | **+0,6562** |
| 0,20 % | −1,381 | +0,0562 | −0,4845 | **+0,5407** |
| 0,50 % | −1,211 | −0,0056 | −0,5280 | **+0,5224** |
| 1,00 % | −1,076 | −0,0563 | −0,5135 | **+0,4572** |
| 3,00 % | −0,851 | −0,0374 | −0,4024 | **+0,3650** |
| 10,0 % | −0,573 | −0,0241 | −0,2337 | **+0,2096** |
| 30,0 % | −0,251 | −0,0170 | −0,0818 | **+0,0648** |
| 50,0 % | −0,037 | −0,0031 | +0,0129 | **−0,0160** |
| 90,0 % | +0,474 | +0,0263 | +0,1844 | **−0,1581** |

18 von 21 Stützstellen liegen **über ihrem eigenen Nullband**.

⭐ **Das ist genau die stetige Hebelkurve, die Sie beschrieben haben.**

⚠️ **Für die HÖHE zählt trotzdem der rohe Kelly** — das Konto wächst
absolut, nicht gegen eine Nullwelt. Der Überschuss belegt, **dass** die
Achse ordnet, nicht wie hoch gehebelt werden darf.

## ✔ Out-of-sample in beide Richtungen

| Richtung | Schwelle | n | q | Kelly | Ertrag | Nullband |
|---|---|---|---|---|---|---|
| 1. Hälfte → 2. | −1,231 | 10.259 | 53,9 % | +0,0503 | **+1,1296 %** | −1,260 ✔ |
| 2. Hälfte → 1. | −1,396 | 1.747 | 58,9 % | +0,0657 | **+0,7474 %** | −2,937 ✔ |

⚠️ Die beiden Schwellen weichen voneinander ab (−1,231 gegen −1,396) —
**die Kalibrierung streut**.

## ⛔⛔ Gleichzeitige Trades sind NICHT unabhängig

Das war die ungeprüfte Annahme in meiner Formel `hebel = kelly/teiler ·
N/s`. Gemessen als Intraklassen-Korrelation der R-Ergebnisse am selben
Kalendertag:

| Auswahl | Tage | Trades | je Tag | rho | effektiv N |
|---|---|---|---|---|---|
| `W ≤ −1,50` | 247 | 3.372 | 18,3 | 0,3521 | 2,58 |
| `W ≤ −1,20` | 622 | 16.940 | 33,0 | 0,4029 | 2,38 |
| *gemischte Tage (Bias)* | | | | *0,0492* | |

⭐ **rho nach Biasabzug: 0,3029.** Damit entsprechen `N` gleichzeitige
Positionen nur `N/(1+(N−1)·rho)` unabhängigen — und das strebt gegen
**1/rho = 3,30**. ⛔ **Mehr Positionen bringen ab da nichts mehr, weil
sie dasselbe wetten.**

## ⛔⛔⛔ Die Kalibrierung fällt

Schärfste Stützstelle: `W` **−1,551** · Kelly **+0,0859** · Stop
**8,36 %** · RM-11 **6,02×**

| Kelly-Teiler | 1 Pos. | 2 Pos. | 3 Pos. | 5 Pos. | 8 Pos. | Grenzwert |
|---|---|---|---|---|---|---|
| *(effektiv N)* | 1,00 | 1,54 | 1,87 | 2,26 | 2,56 | **3,23** |
| **voll** (1/1) | (1,03) | (1,58) | (1,92) | **2,32×** | **2,63×** | **3,32×** |
| **halb** (1/2) | (0,51) | (0,79) | (0,96) | (1,16) | (1,32) | (1,66) |
| **viertel** (1/4) | (0,26) | (0,39) | (0,48) | (0,58) | (0,66) | (0,83) |

*Klammern = unter der Zielzone 2–5×, also kein Hebel.*

⛔ **Halbes Kelly erreicht die Zielzone nie.** Volles Kelly erst ab
5 Positionen.

### Die gerechnete Schwelle

| Risikoniveau | Schwelle `W` | Signale | je Tag | Tage % | Ertrag |
|---|---|---|---|---|---|
| **voll / 5** | **−1,531** | 2.850 | 1,63 | 13,0 % | **+2,5418 %** |
| voll / 3 · halb / 3 · halb / 5 · viertel / 5 | — | | | | *Zielzone nie erreicht* |

### Die Lücke ist beziffert

| Stellschraube | ist | nötig für halb/5 bei 2,0× | Faktor |
|---|---|---|---|
| **Kelly** | 0,0859 | 0,1479 | **1,72×** |
| **Stopweite** | 8,36 % | 4,86 % | **0,58×** |
| Korrelation rho | 0,3029 | *auch bei 0 nur 2,57×* | — |

⚠️ **Die Korrelation allein erklärt die Lücke nicht.** Der Kelly selbst
ist zu klein.

---

## Was daraus folgt — und was nicht

| | |
|---|---|
| ✔ | Die **Schwelle** ist keine Wahl mehr, sie fällt aus der Kurve |
| ✔ | Die Kurve ist **stetig und monoton** — kein Band, keine Stufe |
| ⭐ | Was entschieden werden **muss**, ist das **Risikoniveau** (Kelly-Teiler × Positionszahl); daraus folgt die Schwelle |
| ⛔ | **Nicht gezeigt** ist, dass volles Kelly vertretbar wäre — es hat bekannt ruinöse Verlustserien, und die **115 Perioden lange Verlustserie** aus der Mindestschwellenmessung steht dem entgegen |
| ⛔ | Gebühren und Finanzierung sind **nicht** eingerechnet (Regel 2) |
| ⚠️ | Gaps und Slippage fehlen weiterhin (offen aus 2.627) |

## Nachrechnen

```bash
python messe_hebelkurve_stetig.py
```
