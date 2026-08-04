# Bestandsaufnahme: was wurde geändert, und wo wirkt es?

**Laufendes Dokument.** Abschnitt 1 deckt den 01.–02.08. ab, Abschnitt 2 den
03.–04.08. Fortschreiben statt eine zweite Datei anlegen — genau die
Unübersichtlichkeit, gegen die dieses Dokument gebaut wurde, entsteht sonst
zwischen den Dateien neu.

**Zweck:** Die Änderungen sind zahlreich und lassen sich chronologisch nicht
mehr überblicken. Entscheidend ist nicht, WANN etwas gebaut wurde, sondern auf
WELCHER EBENE es wirkt — denn nur eine der vier Ebenen entscheidet darüber,
ob überhaupt ein Signal entsteht.

**Für den schnellen Einstieg:** Abschnitt 2 am Ende enthält das
Kennzahlen-Panel mit den Ausgangswerten vom 04.08. — daran ist jede künftige
Änderung messbar.

---

# Abschnitt 1 — 01.–02.08.

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

---
---

# Abschnitt 2 — 03.–04.08.

## Der Befund in einem Satz

**Elf Commits, und KEINER wirkt auf Ebene 2.** Alles liegt auf Ebene 4
(Messung und Sichtbarkeit). Volumen und Trefferquote haben sich um null Punkte
bewegt.

Das ist die Fortsetzung des 02.08.-Befundes ("von 29 Commits wirken zwei auf
Ebene 2") — nur diesmal war es **beabsichtigt**: Die Messung selbst war falsch,
und zwar um 0,30 R. Ohne korrigierten Maßstab wäre jede Ebene-2-Änderung
unbeurteilbar gewesen.

## Was auf Ebene 4 gebaut wurde

| Commit | Änderung | Wirkung |
|---|---|---|
| `a8ddbaa` | Basislinie nur noch aus dem Signalfenster | Vorzeichen kippt, 0,30 R |
| `1cb9451` | Systemgüte auf Population A (nur echte Trades, Mark-to-Market) | Auflösungsasymmetrie gelöst |
| `8ed9523` | CRV-Breakeven-Bänder (Population B) | neue Messgröße |
| `0d5cdbb` | Bänder in den Notebook-Export | sichtbar |
| `7e1928a` | Competing-Risks-Schätzer + Assetklassen-Trennung | 759 statt 455/153 Signale |
| `a9f1e32` | Vergleich gegen Basislinie statt gegen Formel | Vorzeichenfehler behoben |
| `18a69d1` | Bugfix: Einstiegstag wurde mitsimuliert | Basislinie war zu niedrig |
| `875f0f5` | CoinGecko-OHLC für Krypto ohne Kraken-Listing | Datenlücke #614 |
| `2c4640a` | Kontingent-Schutz für den Rückfall | verhindert Mehrfachabrufe |
| `b04d0f7` | entartetes Konfidenzintervall gilt nicht als belastbar | Randfall-Fehler |

**#617 ist damit geschlossen.** Beide Blocker gelöst, keine Sperre offen.

## Warum die Richtung mehrfach wechselte

Nachvollziehbar aufgeschrieben, weil der Verlauf sonst nicht rekonstruierbar ist:

| # | Annahme | warum verworfen |
|---|---|---|
| 1 | Basislinie als Fakt ins LLM (#617-Auftrag) | #618: CRV-Breakeven ist der sauberere Maßstab |
| 2 | CRV-Breakeven als Leitgröße | dreht ab CRV 2,5 das Vorzeichen — Horizont-Trunkierung |
| 3 | Nur-Long ist der größte Volumen-Hebel (51,5 %) | **reale Broker-Vorgabe**, keine Regel und kein Hebel |
| 4 | HALTEN-Neigung ist der Hebel (36 %) | zerfällt in "gar keine Zonen" (29,1 %) und "Zonen + HALTEN" (6,8 %) |
| 5 | Filter lockern bringt mehr Signale | **jede** messbare Ablehnung ist schlechter als das Durchgelassene |
| 6 | Screening-Score kalibrieren | Schritt 1 ergab: **diskriminiert nicht** |

**Das Ergebnis dieser sechs Wenden ist kein Rückschritt, sondern eine
Eingrenzung:** Die Filter arbeiten richtig. Mehr Signale kommen deshalb nicht
aus gelockerten Filtern, sondern nur aus **besseren Kandidaten** und **besseren
Zonen**. Das ist die Nutzer-Vorgabe "bessere Daten und gezielte Selektion" plus
"bessere Auswahl durch das LLM" — und sie ist jetzt messtechnisch belegt, nicht
nur plausibel.

## Sechs Fehler derselben Familie

An zwei Tagen sechsmal dieselbe Ursache: **Signal- und Basislinienseite ungleich
behandelt.** Jedes Mal sah das Ergebnis plausibel aus.

| | Fehler |
|---|---|
| 1 | Basislinie über 2 Jahre, Signale über 3 Wochen |
| 2 | Basislinie zählt Unaufgelöste mit, Signale nicht |
| 3 | Bänder gegen horizontlose Formel statt gegen Basislinie |
| 4 | Basislinie ab Einstiegstag simuliert (Entry = Schlusskurs) |
| 5 | Perzentil über LONG+SHORT, Auswertung getrennt |
| 6 | entartetes Intervall [0,0–0,0] galt als belastbar |

**Stehende Prüffrage:** *Werden beide Seiten des Vergleichs wirklich gleich
behandelt?* Gehört vor jede Auswertung.

**Widerrufene Befunde — nicht wiederbeleben:**
- "CRV ≥ 4,0 ist das schlechteste Band" — Trunkierungs-Artefakt
- "Gate-Senkung unter 2,0 ist gemessen erledigt" — war Wilson-Artefakt, Frage ist offen
- "36 % Auflösungsquote belegt Selektion" — Nenner enthielt 94 Nicht-Trades, ehrlich sind 58 %

---

## Das Kennzahlen-Panel: woran Fortschritt sichtbar wird

**Das fehlte bisher.** Ohne definierte Ausgangswerte ist jede künftige Änderung
wieder unbeurteilbar. Alle Werte aus dem Notebook-Export vom **04.08. 06:35**.

### A — Volumen (Ziel: mehr)

| Kennzahl | Quelle im Export | Stand 04.08. |
|---|---|---|
| handelbare Hebel-Signale / 7 Tage | `hebel_signals`: kein Veto, `action != HALTEN`, Zonen vorhanden | **15** |
| Anteil "gar keine Zonen erarbeitet" | `hebel_signals`: `take_profit_usd_von is None` | **29,1 %** |
| Anteil "Zonen erarbeitet, LLM wählt HALTEN" | kein Veto, `action == HALTEN`, Zonen vorhanden | **6,8 %** |
| Anteil Gate-/Veto-gestoppt | `risk_veto = 1`, ohne Nur-Long | **9,6 %** |
| Trichter Kandidaten → LLM-Call | `rohdaten_fuer_backtest.hebel_triggers_kandidaten` | 2.543 LONG → **1.159** |
| Trichter LLM-Call → handelbar | dieselbe Quelle | **147 (12,7 %)** |

### B — Qualität (Ziel: besser)

| Kennzahl | Quelle im Export | Stand 04.08. |
|---|---|---|
| Signalbeitrag hebel/real | `systemguete.hebel.real.signalbeitrag_r` | **+0,257** |
| Signalbeitrag krypto/real | `systemguete.krypto.real.signalbeitrag_r` | **+0,272** |
| Expectancy hebel/real | `systemguete.hebel.real.expectancy_r` | −0,104 |
| SQN hebel/real | `systemguete.hebel.real.sqn` | −0,65 |
| Auflösungsquote hebel/real | `systemguete.hebel.real.aufloesungsquote` | 76,4 % |
| Bandabstand Hebel h7, CRV 2,0–2,5 | `crv_breakeven_baender.hebel_h7_mit_halten` | **+28,6 pp** |
| Bandabstand Hebel h7, CRV < 2,0 | dieselbe Quelle | +20,4 pp |
| belastbare Bänder (von 5) | `belastbar` | **2** |

### C — Datengüte (Voraussetzung für A und B)

| Kennzahl | Quelle im Export | Stand 04.08. | Ziel |
|---|---|---|---|
| Symbole ohne Kursreihe | `preishistorie_signal_symbole.symbole_ohne_ohlc` | **11** | 4 (nur Wertpapiere/Stablecoin) |
| auswertbarer Anteil der Kandidaten | abgeleitet | **71,9 %** | > 95 % |
| CoinGecko-Verbrauch / Tag | `coingecko_kontingent.taeglich_verlauf` | 84–310 (Limit 322) | < 322 |
| Job-Fehlschläge / Tag | `job_fehlschlaege` | 26, davon 19 "database is locked" | 0 |

### Wie das Panel zu benutzen ist

1. **Vor** einer Änderung die betroffenen Zeilen notieren.
2. **Nach** dem Live-Lauf gegen dieselben Zeilen vergleichen.
3. Eine Änderung auf Ebene 1 oder 2 muss sich in **A oder B** zeigen — sonst
   wirkt sie nicht dort, wo entschieden wird (der Befund vom 02.08.).
4. Bewegt sich nur C, war es Datenpflege — wertvoll, aber kein Fortschritt am Ziel.

**Wichtig:** A und B können gegenläufig sein. Am 04.08. gemessen: Jede
Lockerung eines Filters erhöht A und senkt B (durchgelassen +0,784 R gegen
LLM-HALTEN +0,360 gegen Veto +0,235). **Gleichzeitiger Fortschritt in A und B
ist deshalb der einzige gültige Erfolgsnachweis** — nicht A allein.

---

## Wo wir am Ziel stehen

**Ziel:** mehr Signale UND bessere Trefferquote, über bessere Daten und
gezielte Selektion plus bessere Auswahl durch das LLM.

| | Stand |
|---|---|
| **Messebene** | fertig und live verifiziert. Der Maßstab trägt. |
| **Datengüte** | Lücke erkannt und geschlossen, **Wirkung noch nicht im Export** |
| **Volumen** | unverändert — 15 handelbare Hebel-Signale in 7 Tagen |
| **Qualität** | unverändert — Signalbeitrag stabil positiv, aber nichts wurde geändert |

**Nächster Schritt: Komplementarität von Screening-Score und LLM-Konfidenz.**
Sind Signale mit hohem Score UND hoher Konfidenz besser als mit einem allein?
Wenn nein, ist eine der beiden Stufen redundant. Nie gemessen — und es
entscheidet, ob die zweistufige Architektur überhaupt trägt.

Danach in dieser Reihenfolge:
1. `score_gesamt` aus dem Fakten-JSON (diskriminiert nicht, steht ohne Regel drin)
2. Ausstieg: +0,43 R mechanisch gegen −0,30 R verwaltet — größter Qualitätshebel
3. Cron-Staggering 06:30 (drei Jobs auf derselben Minute → SQLite-Sperren)
4. Hypothese prüfen: Cooldown-Filter läuft vor der Score-Sortierung
