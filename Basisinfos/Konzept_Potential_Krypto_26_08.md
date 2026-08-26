# Das Potential als Auslöser — Konzept für Krypto (Spot und Hebel)

**Angelegt 26.08.2026.** Ersetzt den zu knappen Entwurf
`Konzept_Grund_statt_Uhr_26_08.md`, der die Handelsstrategie nicht
berücksichtigt hat.

> **Der Satz, um den es geht (Nutzer, 26.08.):**
> *„Wenn ein Asset (inkl. Markt etc.) ein bestimmtes ‚Potential' erreicht,
> soll ein Handelssignal kommen. **Wir scheitern ausschließlich am Potential,
> weil wir nur messen.** Der Ablauf sollte sich an einem Handel in der Praxis
> anlehnen — alle Indikatoren bewerten: Markt, Finanz, Makro, Asset — und
> durch alle Rollen, die wir gebaut haben, am Ende eine saubere
> Handlungsentscheidung ergeben."*

---

## 0. Die Diagnose in einem Satz — und warum sie unbequem ist

**Das Projekt hat zwei Jahre lang gefragt „trägt dieser Indikator gegen den
Zufall?" und nie gefragt „wie viel ist bei diesem Asset gerade zu holen?".**

Das sind verschiedene Fragen. Die erste ist eine Aussage über eine *Regel* und
verlangt Signifikanz. Die zweite ist eine Aussage über einen *Einzelfall* und
verlangt nur, dass sie **ordnet** — dass sie Assets und Handlungen in eine
Rangfolge bringt, die besser ist als das Alphabet.

Ein Trader in der Praxis rechnet keine Blockpermutation. Er schaut auf Markt,
Makro, Positionierung und das Asset selbst, bildet daraus ein Urteil *„hier
sind 15 % drin, dort 3 %"* — und handelt das Erste. Er weiß, dass er sich oft
irrt. Er braucht keine Signifikanz, er braucht eine **Reihenfolge**.

⚠️ **Das ist kein Freibrief.** Ein Potentialmaß, das nicht ordnet, ist
wertlos, und das muss geprüft werden. Aber die Prüfung lautet *„ordnet es
besser als Zufall?"* — nicht *„schlägt jeder Bestandteil einzeln seine
Blockpermutation?"*. An der zweiten Frage ist alles gescheitert.

---

## 1. Korrigierte Faktenlage

⚠️ Der Vorentwurf enthielt Annahmen als Fakten. Was jetzt geprüft ist:

| | Stand 24./26.08. | Quelle |
|---|---|---|
| Krypto in der Watchlist | **44** (alle Rolle `taktisch`) | `config.get_watchlist()` |
| Bestand (frei **+ gestakt**) | **24** von 44 | `holdings`, `quantity + staked_quantity > 0` |
| davon **nur** gestakt | 9 | ⚠️ mit `quantity > 0` allein zählt man sie fälschlich als frei |
| Spot **eröffenbar** | 20 | 44 − 24 |
| **Hebel geprüft** | **24 von 44** (`hebel_pruefung_erlaubt = 1`) | NB-Export `hebel_pruefung_toggles` |
| Hebel abgeschaltet | 19 + 1 ohne Zeile | Opt-in seit 15.08.: **keine Zeile = AUS** |
| Bewertungen an einem Tag | **108** (95 Spot, 13 Hebel), 81 mit Handlung | NB-Export 24.08. |
| davon **ERÖFFNEN** | **0** | ebenda |

**Zwei Nutzerklarstellungen, die den Rahmen setzen:**

1. *„Hebel kann und soll als kurzfristige Strategie über **alle** Assets der
   Watchlist möglich sein — **mit und ohne Bestand**."* Für Hebel ist die
   eröffenbare Menge also **44**, nicht 20. Spot und Hebel haben verschiedene
   Grundgesamtheiten.
2. *„Grundsätzlich haben beinahe alle Assets Hebel-Potential — **die
   Einschränkung resultiert aus der Anzahl der Signale**."* Die 19
   abgeschalteten sind damit **keine fachliche Aussage**, sondern eine
   Mengenbremse.

⚠️ **Punkt 2 ist der Beleg für die Kernthese dieses Konzepts.** Weil es kein
Kriterium gibt, das nach *Qualität* aussortiert, wurde nach *Menge*
aussortiert — und zwar durch Abschalten ganzer Assets. Ein funktionierendes
Potentialmaß macht diese Bremse überflüssig: dann steuert das Potential, und
alle 44 können wieder eingeschaltet werden.

---

## 2. Der Praxis-Ablauf als Vorbild

So entsteht eine Handelsentscheidung in der Praxis — und so ist die Kette
**bereits gebaut**, nur ohne Verdichtung am Ende:

| Schritt in der Praxis | Frage | im System |
|---|---|---|
| **1. Umfeld** | Ist überhaupt Handelswetter? | **Rolle A** — `marktlage.py` |
| **2. Auswahl** | Welche Assets kommen in Frage? | `auswahl.py` (A1) — heute nach 250-T-Rendite |
| **3. Aufbau** | Was zeigt das Asset selbst? | **Rolle BC** — `lagebeschreibung.py` |
| **4. Gegenprobe** | Was sagt die Positionierung? | **Rolle G** — `positionierung.py` |
| **5. Geometrie** | Wo Einstieg, Stop, Ziel? | `entscheidungsrechnung.py`, `trichter.py` |
| **6. Größe** | Wie viel Kapital? | `betraege.py`, `wahrscheinlichkeit.py` |
| **7. Entscheidung** | Handeln oder nicht? | `entscheider` |
| ⚠️ **fehlt** | **Wie viel ist hier zu holen — im Vergleich zu allem anderen?** | **niemand** |

**Schritt 7 entscheidet heute binär pro Asset, ohne Vergleich.** Deshalb kann
er nur mit Schwellen arbeiten („CRV ≥ 2,0", „Konfidenz ≥ 60") — und Schwellen
erzeugen entweder zu viele Signale oder gar keine. Das ist der Grund, warum
zwischen „Signalflut" und „null Eröffnungen" nichts liegt.

---

## 3. Was schon da ist — das Rollen-Inventar

**Alle vier Ebenen, die Sie nennen, existieren.** Sie sind nur nicht
verdichtet:

### Ebene MARKT + MAKRO → Rolle A (`marktlage.py`)

| Block | Inhalt |
|---|---|
| `beschreibe_lange_sicht` | SPX-Trendabweichung in Std (seit 1927), CPI YoY, 240-Monats-Perzentil |
| `beschreibe_makro` | Netto-Liquidität (WALCL−TGA−RRP), Zinskurve 10J−kurz, 12-Wochen-Δ |
| `beschreibe_trend` | 250-T- und 60-T-Rendite, Lage in der Jahresspanne, je Leitmarkt |
| `beschreibe_volatilitaet` | ATR relativ + Perzentil (250) |
| `beschreibe_liquiditaet` | Amihud-Illiquidität + Perzentil |
| `beschreibe_stimmung` | Fear & Greed-Perzentil (im Kryptoblock) |
| `gleichlauf` | wie stark die Leitmärkte gemeinsam laufen |

### Ebene ASSET → Rolle BC (`lagebeschreibung.BLOCK_REIHENFOLGE`)

`bestand` · `fundamental` · `verlauf` · `marken` · `hebelgeometrie` ·
`referenz` · `volumen` · `umschlag` · `finanzierung` · `luecken`

### Ebene FINANZ/POSITIONIERUNG → Rolle G (`positionierung.py`)

Open Interest über drei Börsen · **OI-Divergenz** · Funding-Perzentil ·
Long-Konten-Anteil · BTC-Netto-Börsenfluss · Stablecoin-Angebot · DVOL/Skew

⚠️ **Und das ist frisch gemessen (25.08.):** `oi_aenderung` (ρ 0,034),
`oi_divergenz` (0,195) und `funding_rate` (0,250) sind **eigene Kanäle** —
sie tragen Information, die **nicht** in der Kursreihe steht. Das ist die
erste Familie im ganzen Projekt, auf die das zutrifft.

**Fazit:** Es fehlt kein Fakt. Es fehlt die **Zusammenführung**.

---

## 4. Das Potentialmaß — Definition

### 4.1 Was es ist

> **Potential P = erwartete Bewegung × Wahrscheinlichkeit, sie mitzunehmen —
> je (Asset, Handlung, Zeithorizont).**

Konkret, aus vorhandenen Bausteinen:

```
P(Asset, Handlung, Horizont)
    =  Spannweite(Asset, Horizont)      # trichter.py: Faktor × ATR × √t
     × Erreichbarkeit(Geometrie)        # wahrscheinlichkeit.py: Basisrate + Beiträge
     × Umfeldfaktor(Markt, Makro)       # Rolle A, verdichtet
     × Positionierungsfaktor            # Rolle G, verdichtet
```

**Warum diese vier und keine mehr:** Es sind genau die vier Ebenen, die Sie
genannt haben, und für jede existiert bereits ein Modul. Nichts muss neu
erhoben werden.

### 4.2 Was es **nicht** ist

- **Keine Prognose.** P sagt nicht „das Asset steigt". Es sagt „hier ist mehr
  zu holen als dort" — eine **Ordnung**, kein Punktwert.
- **Keine Gebührenrechnung.** Nach N-5 gilt: ein guter Trade ist über das
  **Potential des Assets** definiert, nicht über Gebührendeckung. P rankt
  **gebührenfrei**; die Geldrechnung steht **daneben** in der Mail. ⚠️
  `wahrscheinlichkeit.rechne()` mischt beides heute
  (`abstand_punkte = quote − breakeven` enthält den Satz) — als Anzeige
  richtig, als Rangkriterium wäre es die verworfene Definition.
- **Kein Ersatz für die Rollen.** P ordnet, **wen** die Rollen beurteilen.
  Das Urteil selbst fällt weiter im LLM.

### 4.3 Die ehrliche Schwäche

Zwei der vier Faktoren sind **nicht** gegen den Zufall belegt: der
Umfeldfaktor (Marktphase trägt nicht, Kap. 114) und der
Positionierungsfaktor (nie gemessen, frühestens ab 22.10.2026).

**Das ist hinnehmbar, solange P nur ordnet und nicht sperrt** — und es ist der
Grund, warum P zuerst als **Anzeige** läuft. Wer aus einer ungeprüften Zahl
sofort eine Sperre macht, wiederholt den Fehler von A1.

---

## 5. Spot und Hebel sind zwei Systeme

Ihre Vorgabe: *„Hebel häufig kritisch, Spot längerfristig (meist)."* Das ist
in den Daten belegt und muss **jede** Größe des Konzepts trennen:

| | **SPOT** | **HEBEL** |
|---|---|---|
| Grundgesamtheit | 20 eröffenbar (44 − 24 Bestand) | **44** (Bestand irrelevant) |
| Haltedauer (gemessen) | längerfristig | Median **0,30 Tage**, 75 % unter 1 Tag |
| Betriebshorizont für P | **120 Handelstage** | **5–20 Handelstage** |
| Kostenlast | Kauf + Verkauf | + Finanzierung 0,03 %/Tag |
| Was P dominiert | Spannweite (Trichter) | Erreichbarkeit + Timing |
| Anlass-Frist | Tage | **Stunden** |
| Risiko bei Fehlurteil | Buchverlust | **Liquidation** |

⚠️ **Heute läuft für beide dieselbe Anlass-Frist** — das ist N-8 und war schon
vor diesem Konzept offen. Ein Potentialmaß mit einem einzigen Horizont wäre
für eine der beiden Seiten immer falsch.

**Konsequenz:** P wird **zweimal** gerechnet, mit verschiedenem Horizont und
verschiedener Kostenannahme. Ein Asset kann für Hebel hohes und für Spot
niedriges Potential haben — genau so, wie es in der Praxis ist.

---

## 6. Wann wird was geprüft

Heute: die Uhr fragt alle 15 Minuten (Hebel) bzw. alle 3,5 Stunden (Spot), und
`anlass`/`wiederholung` bremsen hinterher. **Künftig entscheidet die
Potentialänderung, wer beurteilt wird:**

### 6.1 Der Takt bleibt, seine Rolle ändert sich

Der Scheduler wird **Datensammler**, nicht Auslöser. Er rechnet P für alle
44 Assets — das kostet **keinen Modellaufruf**, weil alle vier Faktoren
deterministisch sind.

### 6.2 Die Beurteilung wird nach ΔP vergeben

| Gruppe | wann beurteilt |
|---|---|
| **Bestand** (24) | wenn ΔP für **Halten gegen Reduzieren** die Schwelle reißt — **nicht mehr automatisch** |
| **Spot, kein Bestand** (20) | wenn P für ERÖFFNEN unter den besten k liegt **und** ΔP die Schwelle reißt |
| **Hebel** (alle 44) | eigenes Ranking, eigener Horizont, eigene Schwelle |

⚠️ **Der Bruch mit heute:** Bestand passiert derzeit *immer* — deshalb sind
135 von 143 Urteilen Bestandsverwaltung. Wenn Bestand und Nicht-Bestand im
**selben** Ranking konkurrieren, kann eine ruhige Bestandsposition keinen
Platz mehr belegen.

### 6.3 Der Grund wird benennbar

Heute steht in der Mail: *„Cooldown abgelaufen"* oder *„Rang 2 von 41"*.
Künftig: *„Potential für ERÖFFNEN von 4,2 auf 11,8 gestiegen — Treiber:
Widerstand über dem Kurs gefegt (Asset) und Funding vom 88. auf das 12.
Perzentil gefallen (Positionierung)."*

**Das ist der GRUND, nach dem Sie seit Tagen fragen.** Er entsteht nicht durch
ein neues Modul, sondern dadurch, dass P zerlegbar ist: jeder der vier
Faktoren liefert seinen Beitrag zur Änderung mit.

---

## 7. Der neue Ablauf, Schritt für Schritt

```
 [1] Scheduler          alle 44 Assets, deterministisch, kein Modellaufruf
      |                 P_spot(120 T) und P_hebel(5-20 T) je Asset
      v
 [2] ΔP-Vergleich       gegen den letzten gespeicherten Stand
      |                 -> wer hat sich am stärksten bewegt?
      v
 [3] Ranking            Bestand und Nicht-Bestand gemeinsam, je Instrument
      |                 -> die besten k, ODER alle über der ΔP-Schwelle
      v
 [4] ROLLE A            Lagebild (einmal je Lauf, nicht je Asset)
      v
 [5] ROLLE BC           Befund + Handlungsempfehlung  <- Modellaufruf
      v
 [6] ROLLE G            Gegenprüfung Positionierung   <- Modellaufruf
      v
 [7] Z1                 Treue zur Eingabe
      v
 [8] Geometrie          Einstieg, Stop, Ziel, Größe
      v
 [9] Entscheider        handeln / nicht handeln  + GRUND aus [2]
```

**Was sich gegenüber heute ändert:** nur die Stufen [1]–[3]. Die Rollen [4]–[7]
bleiben **unverändert** — sie bekommen nur andere Assets vorgelegt und einen
Grund mitgeliefert.

**Was wegfällt:** `wiederholung` (Cooldown) wird überflüssig, weil ΔP von
selbst nicht auslöst, wenn sich nichts geändert hat. `anlass` bleibt als
**Sicherung** gegen identische Eingaben, verliert aber seine steuernde Rolle.

---

## 8. Was gemessen werden muss — und was ausdrücklich nicht

Nach N-6 gilt: kein Scharfschalten ohne Wirkungsnachweis. Aber die Prüfungen
sind hier **anderer Art** als die der letzten Wochen:

| | Frage | Art | wann |
|---|---|---|---|
| **M1** | Wie viele Beurteilungen erzeugt ΔP — und welche Assets? | Trockenlauf auf vorhandenen Daten | sofort |
| **M2** | Ordnet P besser als das Alphabet? Als die 250-T-Rendite? | Rangkorrelation gegen die tatsächliche Folgebewegung | sofort, vorläufig |
| **M3** | Sind die zusätzlichen Eröffnungen besser? | braucht Ausgänge | **erst nach Laufzeit** |
| **M4** | Trägt der Positionierungsfaktor? | Wirkungsmessung | **ab 22.10.2026** |

⚠️ **M2 ist der Kern und der Unterschied zu allem bisher.** Die Frage lautet
nicht *„schlägt P seine Blockpermutation?"*, sondern *„bringt P die Assets in
eine bessere Reihenfolge als das, was wir heute benutzen?"* — gemessen gegen
**A1s 250-Tage-Rendite** als Bezugsgröße, nicht gegen Zufall.

**Das ist eine niedrigere, aber ehrlichere Hürde:** A1 ist heute im Betrieb.
Wenn P besser ordnet als A1, ist es eine Verbesserung — auch wenn beide keine
Signifikanz erreichen.

---

## 9. Reihenfolge und Aufwand

| | Schritt | Aufwand | Risiko |
|---|---|---|---|
| **1** | **P rechnen und in der Mail anzeigen** — beide Instrumente, mit Zerlegung nach den vier Faktoren | mittel, kein neues Datum | **null** (Anzeige) |
| **2** | **M2**: ordnet P besser als A1? | ein Messlauf | null |
| **3** | **M1**: Trockenlauf ΔP gegen die letzten Wochen | ein Messlauf | null |
| **4** | ΔP-Ranking im **Schatten** (wie `auswahl_schatten`) | klein | null |
| **5** | Entscheidung: ΔP übernimmt von `wiederholung` | — | **hoch** — erst nach 1–4 |

**Schritt 1 ist der einzige, der etwas baut.** Er ist auch der, der sofort
etwas ändert: Sie sehen in jeder Mail, welches Potential das System einem
Asset zuschreibt und **woraus es sich zusammensetzt** — und können beurteilen,
ob die Zahl plausibel ist, bevor sie irgendetwas steuert.

---

## 10. Was dieses Konzept nicht behauptet

- **Es macht die Trades nicht nachweislich besser.** Es macht sie
  **vergleichbar** und die Auswahl **begründet**. Ob daraus bessere Ergebnisse
  folgen, ist mit heutigen Daten nicht messbar — und wer das verspricht,
  verspricht Unmessbares.
- **Es hebt den Grundbefund nicht auf.** Ein Barrierensystem auf driftfreiem
  Pfad hat Erwartungswert null. Die drei Wege bleiben **Drift · Nachrichten ·
  Kosten**. P ordnet innerhalb dieser Grenze — es verschiebt sie nicht.
- **Zwei seiner vier Faktoren sind ungeprüft** (Umfeld, Positionierung). Das
  ist offen ausgewiesen und der Grund für die Anzeige-Stufe.

**Was es leistet:** Es beendet den Zustand, dass die Uhr entscheidet — und den
Zielkonflikt, dass Signalmenge nur durch Abschalten ganzer Assets zu
begrenzen ist.

Verwandt: `Umbauplan_Gesamtsystem_12_08.md` Kap. 42.2 (CSTI-T, Z4) ·
`Konzept_Positionierung_25_08.md` · `A1_Auswahl_Dimensionierung_23_08.md` ·
`Zwischenstand_Gesamtprojekt_06_08.md` N-5/N-6/N-8
