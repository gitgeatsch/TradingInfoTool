# Voranalyse: Neudimensionierung des Hebels

**26.09.2026** · überarbeitet nach zwei Nutzerkorrekturen ·
**nichts gebaut, nichts geändert**

> *„darum möchte ich auch, dass der Hebel neu dimensioniert wird und auch
> neu vermessen da dies bereits der dritte große Hebelumbau ist"*

---

## ⛔ Zwei eigene Fehler, die diese Fassung korrigiert

| # | Was ich schrieb | Was stimmt |
|---|---|---|
| **1** | *„Für den Hebel gibt es keine Positionsführung"* | `agent/hebelfuehrung.py`, 550 Zeilen seit 11.09. Ich hatte nach `positionsfuehrung.py` gesucht |
| **2** | *„Die Hebelkette hat nie produktiv gelaufen"* | **Sie läuft seit langem.** Ich hatte die Desktop-Kopie (118 Signale) statt der Produktion (**7.544**) gelesen und die stillgelegte Screening-Schiene mit der Rollen-Kette verwechselt |

> **Nutzerkorrektur:** *„die Kette läuft seit langem in Produktion — nur
> falsch."*

⚠️ Fehler 2 ist heute der **zweite** dieser Art — das Produktionsbackup lag
bereit. Stehende Regel: *„Nicht messbar ist keine Datenlage."*

---

## Was tatsächlich läuft (Notebook-Backup 23.09.)

| Instrument | Signale | Zeitraum |
|---|---|---|
| **spot** | **4.527** | 14.08. – 23.09. |
| (ohne) | 2.983 | 07.07. – 14.08. |
| **hebel** | **22** | 12.09. – 22.09. |
| absicherung | 12 | 15.08. – 09.09. |

⛔ Die **alte** Screening-Schiene (`hebel_screening`, `hebel_triggers`,
`hebel_signals`) steht seit dem **14.07.** still und ist per
`aktiv: false` abgeschaltet. Sie ist nicht die produktive Kette.

---

## ⭐⭐⭐ Das Symptom NACHKAUFEN — gemessen, und es ist nicht hebelspezifisch

Alle 22 Hebel-Signale tragen `action = NACHKAUFEN`, keines einen Einstieg.
**Das sieht nach einem Hebelfehler aus und ist keiner:**

| | |
|---|---|
| Grundrate KAUFEN bei Spot im September | **0,92 %** (13 von 1.413) |
| erwartete KAUFEN bei 22 Hebel-Signalen | **0,20** |
| **P(0 von 22)** | **81,6 %** |

➤ **0 von 22 ist völlig unauffällig.** Es gibt kein hebelspezifisches
NACHKAUFEN-Problem.

### ⛔⛔⛔ Das echte Symptom: die Einstiegsrate der GANZEN Kette ist eingebrochen

| Tag | KAUFEN | ERÖFFNEN | NACHKAUFEN | Einstiegsrate |
|---|---|---|---|---|
| 18.–21.08. | 4–9 | 134–150 | 10–25 | **61–73 %** |
| 22.08. | 35 | 54 | 33 | 57,8 % *(S6a läuft an)* |
| 23.08. | **43** | **0** | 67 | 22,4 % *(Umbenennung **funktioniert**)* |
| **24.08.** | **0** | 0 | 84 | **0,0 %** |
| 25.–27.08. | 1–3 | 0 | 101–115 | 0,7–1,8 % |
| September | 13 gesamt | 0 | 767 | **0,9 %** |

**Einbruch um Faktor 36**, und zwar **an einem einzigen Tag**.

⚠️ **S6a ist NICHT die Ursache.** Die Vokabular-Umstellung vom 22.08.
(ERÖFFNEN → KAUFEN) lief am 23.08. sauber: ERÖFFNEN auf 0, KAUFEN auf 43.
Erst **am 24.08.** fiel KAUFEN auf null, während NACHKAUFEN weiter stieg.

⛔ **Die Ursache ist nicht bestimmt.** Am 24.08. liegen 12 Commits; welcher
es ist, lässt sich durch Lesen nicht entscheiden. **Offene Spur, eigene
Untersuchung** — nicht geraten.

⭐⭐ **Und das ist derselbe Befund, den der Nutzer am 25.09. für Spot
gemeldet hat:** *„seit 2025 würde man nur im Verlust nachkaufen, keinen
Boden."* Er hat jetzt ein Datum und eine Größenordnung.

---

## Die Architekturvorgabe

> **Nutzervorgabe 26.09.:** *„Hebel und Spot sollen eine Prüfung werden —
> ein Eingang, zwei unterschiedliche Bewertungen — und nur eine Strategie
> soll in der Ablaufkette weiter verarbeitet werden, damit sparen wir
> Ressourcen. Das musst du bereits vorher mit mir dimensionieren, zuvor
> brauchen wir allerdings eine funktionierende Hebelbewertung."*

⭐ **Der Prompt ist dafür bereits gebaut.** `agent/rolle_trader.py:158`:

```python
_HANDELN = {"spot": _HANDELN_GEMEINSAM, "hebel": _HANDELN_GEMEINSAM}
```
> *„Ob daraus ein Spot-Kauf oder eine gehebelte Position wird, entscheidet
> die Rechnung nach deiner Antwort — nicht du."*

➤ Der **Eingang** ist bereits gemeinsam und **bitgleich**. Was fehlt, ist
die **Verzweigung danach**: heute laufen zwei getrennte Durchgänge
(`instrument='spot'` und `instrument='hebel'`), statt einen zu bewerten und
die bessere Strategie weiterzugeben.

⚠️ **Das passt zu 2.588** (Hebel und Spot teilen die Merkmale, eigene
Skala) — aber es wird **erst dimensioniert, wenn die Hebelbewertung
funktioniert**, wie vorgegeben.

---

## Die Reihenfolge

| # | | Art |
|---|---|---|
| **1** | ⭐ **Hebelbewertung zum Funktionieren bringen** — Neudimensionierung (unten) | Messung |
| **2** | **Architektur dimensionieren** — ein Eingang, zwei Bewertungen, eine Strategie | ⚠️ **mit dem Nutzer**, vor dem Bau |
| **3** | Verdrahtung, Test, Fehlerbehebung | Bau — *„wird auch noch aufwendig"* |
| **4** | Einstiegsrate-Einbruch vom 24.08. | eigene Untersuchung |

---

## Die Dimensionierungsgrößen

| Größe | laufender Wert | Status |
|---|---|---|
| **Horizont / Haltedauer** | ⛔ **`holding_duration` ist bei allen 22 Signalen leer** | vier Zahlen in Dokumenten, **keine** im Signal |
| **Stopweite** | `stop_min_atr` 2,0 | 2.431 widerlegt; gemessener Gipfel **8 %** |
| **Trailing-Auslöser** | `ausloese_r` 1,0 | ⛔ kollidiert mit meiner Messung (dort 0) |
| **Trailing-Abstand** | 1,0 R | ✔ = 1,0 ATR bei Weite 1,0 |
| **Hebelhöhe** | 2,0–5,0 | ⛔ tautologisch; 2.609 sperrt |
| **max. Hebel** | 10 | ✔ Börsengrenze |
| **Risiko je Trade** | 1 % | ✔ Nutzervorgabe |
| **CRV-Minimum** | 2,0 | setzt die Kelly-Null auf 0,3333 |
| **Prüftakt** | 15 Min | hängt an Ø 1,1 Tage — **Nutzer-Trades, keine Systemtrades** |
| **Cooldown** | 3,5 h | 2.461: **trägt nicht**, kostet 69 % |

### Woher die vier Haltedauern kommen

| Quelle | Wert | Was sie wirklich ist |
|---|---|---|
| `hebel_positionsformel.md` | Ø 1,1 Tage | **Bitpanda-Trades des Nutzers** |
| Befund 2.493 | Median 0,30 Tage, 188 Positionen | **Bitpanda-Trades des Nutzers** |
| Befund 2.513 | ~3 Handelstage | **Rechenannahme** |
| meine Messung | 72 h | **Setzung von mir** |

⚠️⚠️ **Keine beschreibt Systemtrades**, und im Signal steht **gar nichts**.
➤ Die Haltedauer ist eine **Entscheidung, die aus der Messung fallen
muss** — nicht aus einer dieser vier Quellen.

---

## Was die Neuvermessung beantworten muss

| # | Frage | Hängt zusammen mit |
|---|---|---|
| **1** | **Horizont** — Achse 2/6/12/24/48/72/120 h | Takt **und** Finanzierungskosten |
| **2** | **Stopweite** | bestimmt R — und damit alles, was in R gerechnet wird |
| **3** | **Trailing-Auslöser** 0 oder 1,0 R | eine Parameterachse, kein Neubau |
| **4** | **Hebelhöhe** aus Schiefe, Verlustserie, geometrischem Ertrag | 2.609; **nicht** aus `E[R]` allein |
| **5** | **Takt und Cooldown** — Kosten gegen Nutzen | 2.461; wirkt auf die fertige Signalmenge |

⚠️ **Reihenfolge nicht frei:** 1 und 2 bestimmen die Einheit R. Erst danach
sind 3 und 4 in stabiler Skala messbar. 5 zuletzt.

⭐ **Ein Lauf, eine Vorabfestlegung, eine Ankermenge** — damit die
Grundgesamtheit über alle Achsen dieselbe ist (stehende Regel).

---

## Drei Punkte, die der Nutzer entscheidet

| # | | mein Vorschlag |
|---|---|---|
| **1** | Haltedauer aus der Messung, mit dem Nutzer-Median 0,30 Tage als **Vergleichsmarke** statt Vorgabe? | ja |
| **2** | Bleibt `crv_minimum` bei 2,0? | Es setzt die Kelly-Null auf 0,3333 — 2.591: **nur** diese angenommene Basisrate erzeugt überhaupt Hebel |
| **3** | Darf der **Cooldown** zur Disposition stehen? | 2.461: trägt nicht, kostet 69 %. Entscheidung, keine Messung |

## Was NICHT folgt

| # | |
|---|---|
| **1** | ⛔ Nichts gebaut, nichts geändert |
| **2** | Die **Ursache** des Einstiegs-Einbruchs vom 24.08. ist **nicht bestimmt** |
| **3** | Die **Hebelhöhe** bleibt gesperrt, bis Frage 4 gemessen ist |
| **4** | Die **Architektur** wird nicht vor der funktionierenden Hebelbewertung angefasst |
| **5** | Nichts über **Short** |
