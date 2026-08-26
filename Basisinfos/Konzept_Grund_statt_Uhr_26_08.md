> ⚠⚠ **ÜBERHOLT am 26.08.2026 — ersetzt durch
> `Konzept_Potential_Krypto_26_08.md`.**
>
> Dieser Entwurf hat die **Handelsstrategie nicht berücksichtigt** und
> Annahmen als Fakten geführt. Drei Fehler, vom Nutzer benannt:
> **(1)** Bestand ohne gestakte Mengen gerechnet — 9 Assets fehlten;
> **(2)** „20 eröffenbar" gilt nur für Spot, **für Hebel sind es 44**
> (mit und ohne Bestand); **(3)** Spot (längerfristig) und Hebel (kurzfristig,
> häufig kritisch) brauchen **getrennte Horizonte** — ein Potentialmaß mit
> einem Horizont wäre für eine Seite immer falsch.
>
> Die Grundidee (Anlass = Potentialänderung statt Zeitablauf) bleibt und
> steht ausgearbeitet in der Vollfassung.

# Der GRUND je Asset — Konzept statt weiterer Messung

**Angelegt 26.08.2026.** Nutzervorgabe, seit dem 25.08. mehrfach wiederholt:

> *„Wann und wie erzeugen wir über einen GRUND — und der soll nicht der
> Scheduler sein — pro Asset, ob eine bestimmte Handlung die mit dem höchsten
> Potential ist. Fingerprint und Cooldown sind eigentlich nur Mittel zum
> Zweck."*

Und die Kritik, die dieses Dokument ausgelöst hat:

> *„Bevor wir einfach etwas ändern, brauchen wir Lösungen und ein Konzept.
> Aktuell habe ich das Gefühl, du hast dich wieder bei denselben Schritten
> verrannt."*

**Sie trifft zu.** Am 25./26.08. liefen sieben Messungen; jede endete mit
„trägt nicht" oder „nicht entscheidbar". Das ERÖFFNEN-Problem ist aber **kein
Messproblem** — die Kette hat keinen Auslöser außer der Uhr. Den kann man
nicht messen, den muss man bauen.

---

## 1. Die Lage in vier Zahlen

| | |
|---|---|
| Bewertungen an einem Tag (NB-Export 24.08.) | **108** — 95 Spot, 13 Hebel |
| davon mit Handlung | 81: NACHKAUFEN 59 · REDUZIEREN 27 · HALTEN 16 · VERKAUFEN 6 |
| davon **ERÖFFNEN** | **0** |
| Krypto-Assets, die überhaupt eröffenbar sind | **20 von 44** |

⚠️ **Das Universum ist nicht ausgeschöpft** — diese Vermutung wurde geprüft und
verworfen. Es gibt 20 Kandidaten. Das System sieht sie und eröffnet nicht.

*(Nebenbefund bei der Prüfung: 9 Assets stehen mit `quantity = 0` in
`holdings` und sind trotzdem im Bestand — vollständig gestakte Werte. Bitpanda
bucht Stake-Transfers als Abgang aus der Wallet. Wer `quantity > 0` filtert,
zählt sie fälschlich als frei. Der Produktionscode macht es seit 17.08.
richtig; meine erste Diagnose-Abfrage machte den Fehler erneut.)*

---

## 2. Warum es klemmt — die Diagnose in einem Satz

**Alle vier Stufen, die heute über „wird gefragt" entscheiden, sind
Mengenbegrenzer. Keine davon ist ein Grund.**

| Stufe | was sie fragt | ist das ein Grund? |
|---|---|---|
| **Scheduler** | „Ist die Frist abgelaufen?" | ✘ das ist die Uhr |
| **`anlass`** (Fingerabdruck) | „Sind die Fakten identisch zum letzten Mal?" | ✘ *„schon gefragt"* ist keine Qualitätsaussage |
| **`wiederholung`** (Cooldown) | „Ist genug Zeit vergangen?" | ✘ wieder die Uhr |
| **`auswahl`** (A1) | „Ist es unter den besten 2 nach 250-Tage-Rendite?" | ⚠️ eine **Reihung**, aber nach einer Größe, die **nachweislich nicht trägt** |

Der letzte Punkt ist der schwerste: A1 reiht nach dem Rangplatz, und der ist
gemessen — *innerhalb von H* trägt er sogar **negativ** (−5,8 gegen Schwelle
+1,8). Die einzige Stufe, die überhaupt etwas auswählt, wählt nach einem
widerlegten Kriterium.

Das Projekt kennt das als **CSTI-T** (Umbauplan 42.2): *„Die Praxis trennt
‚der Aufbau liegt vor' von ‚jetzt ist der Moment'. Unsere Kette kennt nur den
Aufbau; den Moment gibt die Uhr vor."*

---

## 3. Der Kernwechsel

> **Heute:** Anlass = *Zeit ist vergangen* (und die Fakten haben sich
> irgendwie geändert).
>
> **Konzept:** Anlass = **das Potential dieses Assets hat sich geändert** —
> unabhängig davon, wie lange es her ist.

Das ist kein neuer Filter. Es ist eine **Umkehrung der Frage**: nicht *„darf
ich fragen?"*, sondern *„gibt es etwas Neues zu entscheiden?"*

### Warum das den Zielkonflikt auflöst

Heute stehen zwei Ziele gegeneinander: **weniger Signale** (nicht jeder Trade
soll gemeldet werden) und **mehr Eröffnungen** (das System soll handeln). Mit
Mengenbegrenzern ist das ein Nullsummenspiel — jede Bremse, die Signale
reduziert, reduziert auch Eröffnungen.

Ein Potentialkriterium ist **kein** Nullsummenspiel: es kann gleichzeitig
weniger *und* bessere Anlässe erzeugen, weil es nach Inhalt aussortiert statt
nach Häufigkeit.

---

## 4. Die drei Bausteine

### B1 — Ein Potentialmaß je (Asset, Handlung)

**Was es sein muss:** eine Zahl, die sagt *„wie viel ist hier zu holen"*, und
die zwischen Handlungen vergleichbar ist (ERÖFFNEN gegen NACHKAUFEN gegen
NICHTS_TUN).

**Was vorhanden ist:**

| Baustein | liefert | Stand |
|---|---|---|
| `trichter.py` | Spannweite: Faktor × ATR × √Horizont, je Klasse kalibriert | ✔ trägt (Abweichungen 5 → 0) |
| `wahrscheinlichkeit.py` | Basisrate `1/(1+CRV)` + Beiträge | ✔ gebaut |
| `entscheidungsrechnung.py` | Ziel, Stop, Geometrie | ✔ gebaut |

**Was fehlt:** die Zusammenführung. Der Trichter sagt *wie weit*, die
Wahrscheinlichkeit sagt *wie oft* — **niemand multipliziert beides zu einem
Erwartungswert je Handlung.**

⚠️ **Und die Definitionsfalle, die dabei zu vermeiden ist:** nach N-5 ist ein
guter Trade über das **Potential des Assets** definiert, nicht über
Gebührendeckung. `wahrscheinlichkeit.rechne()` mischt heute beides
(`abstand_punkte = quote − breakeven` enthält den Gebührensatz). Als **Anzeige**
ist das richtig, als **Rangkriterium** wäre es die verworfene Definition. Das
Potentialmaß muss **gebührenfrei** ranken und die Geldrechnung daneben stellen.

### B2 — Der Anlass als Potentialänderung

**Heute:** `anlass.sperrt()` bildet einen Hash über Faktenblöcke. Ändert sich
irgendein Block, ist der Hash anders und es wird gefragt. Alles-oder-nichts.

**Gemessen:** Treiber der Änderungen sind `umschlag` (24.085 Fälle), `marken`
(16.653), `bestand` (4.074). ⚠️ **`umschlag` ist der mit Abstand häufigste
Auslöser — eine Größe, deren Kontext-Lesart nachweislich nicht trägt**
(Unterschied t = 0,85 gegen Placebo-Schwelle 1,65).

**Konzept:** Der Fingerabdruck bleibt, aber er wird **nach Potentialrelevanz
gewichtet**. Eine Änderung löst nur aus, wenn sie das Potentialmaß aus B1 um
mehr als eine Schwelle bewegt. Damit:

- verschwindet der Uhr-Charakter (keine Frist mehr nötig)
- verschwindet die Blindheit (`umschlag` allein löst nicht mehr aus)
- entsteht ein **Grund, der benennbar ist**: *„Das Potential von X ist von
  A auf B gestiegen, weil …"* — genau das, was heute in keiner Mail steht

### B3 — Reihung nach Potential statt nach Rendite

**Heute:** A1 wählt die besten k nach 250-Tage-Rendite, Bestand passiert immer.
Ergebnis: 116 von 116 Läufen dieselben zwei Symbole.

**Konzept:** dieselbe Mechanik, anderes Kriterium — **Rang nach
Potentialänderung** (B1 heute gegen B1 beim letzten Durchlauf). Wer sich am
stärksten bewegt hat, wird gefragt. Das ist per Konstruktion nicht statisch,
weil es eine Differenz ist und keine Niveaugröße.

⚠️ **Und die Konsequenz für den Bestand:** heute passiert Bestand **immer** —
deshalb sind 135 von 143 Urteilen Bestandsverwaltung. Wenn ERÖFFNEN
stattfinden soll, müssen Bestand und Nicht-Bestand **im selben Ranking**
konkurrieren. Eine Bestandsposition ohne Potentialänderung darf dann keinen
Platz belegen.

---

## 5. Was gemessen werden muss — und was nicht

Nach N-6 (kein Scharfschalten ohne Wirkungsnachweis) gilt für **jeden** dieser
Bausteine: erst simulieren, dann schalten. Aber die Messungen sind hier
**anderer Art** als die der letzten Tage:

| | Frage | Art |
|---|---|---|
| **M1** | Wie viele Anlässe erzeugt B2 gegenüber heute — und welche? | **Simulation auf vorhandenen Daten**, keine Prognose |
| **M2** | Wären die zusätzlichen Eröffnungen schlechter als die heutigen? | ⚠️ braucht Ausgänge → **erst nach Laufzeit** |
| **M3** | Ist die Reihung nach Potentialänderung stabiler als nach Rendite? | Simulation, heute machbar |

**M1 und M3 sind Trockenläufe** — sie zeigen, was die Kette *täte*, nicht ob
es gut wäre. Das ist der entscheidende Unterschied zu den H-Messungen: dort
war die Frage *„trägt es?"*, hier ist sie *„was passiert überhaupt?"*.

⚠️ **M2 ist die ehrliche Grenze.** Ob mehr Eröffnungen *bessere* Eröffnungen
sind, kann niemand vorab wissen — das Projekt hat keinen einzigen Regler, der
je gegen den Zufall bestanden hätte. **Der Anspruch dieses Konzepts ist
deshalb nicht „bessere Trades", sondern „begründete statt getaktete
Entscheidungen".** Wer mehr verspricht, verspricht etwas, das hier niemand
messen kann.

---

## 6. Reihenfolge

1. **B1 bauen** (Potentialmaß) — reine Zusammenführung vorhandener Bausteine,
   kein neuer Datenbedarf. Zuerst als **Anzeige** in der Mail, damit sichtbar
   wird, ob die Zahl plausibel ist, bevor sie etwas steuert.
2. **M1/M3 als Trockenlauf** — was täte B2/B3 auf den letzten Wochen?
   Vergleich zur tatsächlichen Historie.
3. **B2/B3 im Schatten** — mitlaufen lassen, nichts sperren, Abweichungen
   aufzeichnen (wie `vorfilter_schatten`, `auswahl_schatten`).
4. **Entscheidung** — erst wenn 1–3 zeigen, dass die Kette handlungsfähig
   wird, ohne unkontrolliert Signale zu erzeugen.

**Schritt 1 ist der einzige, der heute etwas baut.** Die anderen drei prüfen,
ob es wirkt — aber sie prüfen etwas, das existiert, statt eine weitere
Hypothese über die Kursreihe.

---

## 7. Was dieses Konzept ausdrücklich nicht behauptet

- **Es macht die Trades nicht besser.** Es macht sie begründet. Ob das zu
  besseren Ergebnissen führt, ist offen und mit heutigen Daten nicht messbar.
- **Es löst den Grundbefund nicht auf.** Ein Barrierensystem auf driftfreiem
  Pfad hat Erwartungswert null; daran ändert ein besserer Auslöser nichts.
  Die drei Wege dorthin bleiben **Drift · Nachrichten · Kosten**.
- **Es ersetzt H nicht.** H ist ausgereizt (vier Achsen geprüft, keine sagt
  wann es trägt) — aber es war ohnehin nie der Auslöser, sondern ein Filter.

**Was es leistet:** Es beendet den Zustand, dass die Uhr entscheidet, wann ein
Asset beurteilt wird — und dass das System bei 20 verfügbaren Kandidaten und
108 Bewertungen am Tag **null** neue Positionen eröffnet.

Verwandt: `Umbauplan_Gesamtsystem_12_08.md` Kap. 42.2 (CSTI-T, Z4) ·
`Befundkarte.md` §7.1 · `Zwischenstand_Gesamtprojekt_06_08.md` N-5/N-6 ·
`A1_Auswahl_Dimensionierung_23_08.md`
