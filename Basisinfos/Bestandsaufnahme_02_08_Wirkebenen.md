# Bestandsaufnahme 01.–02.08.: was wurde geändert, und wo wirkt es?

**Zweck:** Vorbereitung auf den 03.08. Die Änderungen der letzten zwei Tage
sind zahlreich (29 Commits) und lassen sich chronologisch nicht mehr
überblicken. Entscheidend ist nicht, WANN etwas gebaut wurde, sondern auf
WELCHER EBENE es wirkt — denn nur eine der vier Ebenen entscheidet darüber,
ob überhaupt ein Signal entsteht.

Ergänzt `Regler_Signal_Pipeline_Abhaengigkeiten.md` (Kopplungen zwischen den
Stufen) um die Frage: wie groß ist der Hebel des jeweiligen Elements?

---

## Die vier Wirkebenen

### Ebene 1 — Was das LLM zu sehen bekommt (Prompt/Fakten)

| Änderung | wann | Wirkung |
|---|---|---|
| `halte_kriterium` scharfgeschaltet | 01.08. | Exit-Prüfung bei gehaltenen Positionen |
| Regel 34 Exit-Abwägung (Krypto-Spot) | 01.08. | erzwingt explizite Verkaufsbegründung |
| Regel 34 auf Aktien/Rohstoffe/Themen-ETF | 01.08. | dieselbe Regel, 3 weitere Pipelines |
| Stop-Distanz-Regel (6 Analysten) | 02.08. | LLM soll Stop nicht zu eng setzen |
| Zonen-Validierung `von>bis` → Auto-Korrektur | 02.08. | schützt Stage-1-CRV-Formel vor falschen Werten |

**Messbarkeit:** indirekt. Prompt-Änderungen wirken auf das Verhalten, nicht
auf eine Zahl. Der Effekt ist nur über Vorher-Nachher-Verteilungen sichtbar —
und genau dort liegt der offene Regel-28-Verdacht (Task #601).

### Ebene 2 — Entscheidung: Signal oder kein Signal

**Das ist die einzige Ebene, die die Signalmenge bestimmt.**

| Gate | wann gebaut | greift bei (Messung 02.08.) |
|---|---|---|
| **CRV ≥ 2,0 (Z-2 konservativ)** | **Frühzeit** | **72,3 % (Hebel) / 78,5 % (Spot)** |
| Nur-Long-Richtungsfilter | Nutzer-Einstellung | 73 % der Hebel-Vetos |
| R-5.10 Konfidenzschwelle | 29.07. | 15 Spot-Fälle |
| RM-1b Enge-Stop 2,5 % | **02.08.** | 5,5 % / 0,5 % |
| RM-1c ATR-Untergrenze 0,75× | **02.08.** | ~0 % (Median-Stop 8–11 %) |
| Hebel-Cooldown-Bugfix | 01.08. | verhinderte Doppelsignale |

### Ebene 3 — Positionsgröße (wirkt NACH der Entscheidung)

| Änderung | wann | Wirkung auf Signalmenge |
|---|---|---|
| RM-1 exakt (gegen tatsächlichen Stop) | 02.08. | **keine** |
| RM-1d Ziel-Positionszahl N=5 | 02.08. | **keine** |
| RM-11 exakt (Hebel-Deckel) | 02.08. | **keine** |

Ausdrücklich in der Abhängigkeitsmatrix als "keine Kopplung" vermerkt. Diese
drei ändern kein `action` — sie korrigieren nur die Größe eines Signals, das
die Ebene-2-Gates bereits passiert hat.

### Ebene 4 — Messung und Sichtbarkeit (verändert das System nicht)

| Änderung | wann |
|---|---|
| Statistik-Modul (Wilson, Beitrags-Konzentration) | 02.08. |
| Statistik-Prüfungen in allen Aggregationen | 02.08. |
| tier-Handling gehärtet (Task #561) | 02.08. |
| Export-Lücke OHLC für Signal-Symbole | 02.08. |
| Positionsgröße im Export | 02.08. |
| `analyse_signal_blockade.py` | 02.08. |
| Methodik 2.5.6/2.5.7/2.5.8 | 02.08. |
| Abhängigkeitsmatrix (8 → 12 Einträge) | 02.08. |
| Dead-Loop-Synthese Maßnahmen 1+2 | 02.08. |
| CoinGecko-Kontingent-Analyse + Deckel | 01.08. |

---

## Der Befund aus dieser Aufstellung

**Von 29 Commits wirken zwei auf Ebene 2** (RM-1b, RM-1c) — zusammen auf
0,5–5,5 % der Signale. Alles andere liegt auf Ebene 1 (Verhalten), Ebene 3
(Größe) oder Ebene 4 (Sichtbarkeit).

**Das dominante Gate der Ebene 2 wurde in diesen zwei Tagen nicht berührt:**
das CRV-Gate filtert 72–79 % aller Signale — mehr als alle anderen Gates
zusammen, und rund 15-mal so viel wie die beiden neu gebauten.

Das erklärt, warum die Verbesserungen in den Zahlen nicht sichtbar werden:
Sie wirken nicht dort, wo entschieden wird. Es ist kein Kalibrierungsfehler
der neuen Regeln — sie kommen schlicht kaum zum Zug.

---

## Warum das CRV-Gate der nächste Schritt ist (Task #602)

Messung vom 02.08. (Hebel, Veto-Schatten gegen ausgeführt):

| | n | Median-CRV | Trefferquote | Break-even | Erwartungswert |
|---|---|---|---|---|---|
| CRV-vetot | 258 | 1,26 | 46,1 % | 44,3 % | **+0,042 R** |
| ausgeführt | 86 | 2,54 | 17,4 % | 28,2 % | **−0,382 R** |

Ohne das dominante Symbol (INJ, 14 %) steigt der EW der Vetoten auf +0,166 R.
Das Gate sortiert die Signale mit positivem Erwartungswert aus.

Ursache: Ein hohes CRV misst die Entfernung des Take-Profits, nicht die
Qualität des Trades. Der Literaturwert 2:1 ist eine **Konsistenzbedingung**
(Trefferquote und CRV gemeinsam), wurde aber als isolierte Eintrittsschwelle
übernommen. Zusätzlich verlangt die konservative Z-2-Rechnung faktisch 2,4:1.

---

## Abhängigkeiten einer CRV-Gate-Änderung — VOR jedem Eingriff prüfen

Der Nutzer-Hinweis "wir müssen aufpassen, wenn wir einzelne Bereiche isoliert
behandeln" trifft hier besonders zu. Betroffen wären mindestens:

1. **Prompt Regel 3/16** (alle 6 Analysten): Die Formel steht dort wörtlich,
   inklusive `take_profit.usd_von` und der Konsequenz "sonst HALTEN". Ändert
   sich das Gate, muss der Prompt mit — sonst rechnet das LLM gegen eine
   Vorgabe, die es nicht mehr gibt.
2. **`crv_knapp_schwelle_relativ: 0.2`** (Positionsgrößen-Deckel bei CRV <
   2,4) und **`crv_knapp_hebel_deckel: 3.0`**: beide sind relativ zu
   `CRV_MINIMUM` definiert und verschieben sich automatisch mit.
3. **Veto-Schatten-Population**: bereits in der Matrix vermerkt. Weniger
   CRV-Vetos heißt kleinerer Schatten-Nenner — Vorher-Nachher-Vergleiche der
   Schatten-Statistik brauchen eine neue Baseline.
4. **Z.ai-Vergleichspopulation**: Z.ai sieht nur die Gate-Überlebenden. Mehr
   Überlebende heißt andere Grundgesamtheit für jede Z.ai-Auswertung.
5. **Die vier Anteils-Deckel** (Konfidenz/Gegenszenario/technischer
   Konflikt/CRV-knapp) rechnen auf der von RM-1 exakt korrigierten Basis —
   mehr Signale heißt, dass RM-1d (Ziel-Positionszahl 5) erstmals real
   bindend wird. Bisher war das folgenlos, weil kaum Signale durchkamen.
6. **RM-1b/1c**: laufen VOR dem CRV-Check. Reihenfolge beibehalten, sonst
   wird ein Stop-Problem später als CRV-Problem etikettiert (der Grund, warum
   sie am 02.08. bewusst davor einsortiert wurden).

---

## Offene Punkte für den 03.08.

- **Task #600**: 10-Punkte-Katalog gegen frischen Export nach dem 06:00-Job
- **Task #602**: CRV-Befund an neu aufgelösten Fällen nachrechnen
- **Task #601**: Regel-28-Hypothese (Entscheidungsfreude-Sprung am 31.07.)
- Reihenfolge-Empfehlung: #602 zuerst — es ist der größte Hebel, und die
  anderen beiden liefern Kontext dafür.
