# Bestandsaufnahme: Positionsführung über alle Assetklassen

**Angelegt 26.08.2026.** Nutzervorgabe:

> *„Persönlich möchte ich einen sinnvollen Umbau, der funktioniert — also
> vorher prüfen, ob alles vorhanden ist: wie alle Anforderungen an Krypto,
> Hebel und Spot-Geschäfte lauten, auch über andere Assets. Doku lesen,
> Regelwerke, und dann ein sauberer Umbau für Krypto bzw. andere Assets
> berücksichtigen, sonst haben wir Lücken."*

⚠️ **Dies ist eine BESTANDSAUFNAHME, kein Konzept.** Sie sagt, was da ist und
was fehlt — nicht, was gebaut werden soll. Der Umbauplan folgt danach.

---

## 0. Der Anlass in drei Lücken

Die Untersuchung der Ausstiegsregel (N-11) hat drei zusammenhängende Lücken
freigelegt:

| | Lücke | belegt durch |
|---|---|---|
| **1** | **Position** hat keinen Stop, kein Ziel, keinen MFE, nur teilweisen Einstand | `holdings` hat 9 Spalten, keine davon trägt eine These |
| **2** | **Akkumulation** ist definiert, aber **nie gesetzt** | `strategie` = `akkumulation` kommt in **0** von 7.294 Signalen vor |
| **3** | **Verkauf** hängt an einer Regel, die phasenabhängig schadet | Frage A: AUF −0,043 R [−0,068; −0,018] |

**Sie hängen zusammen:** Weil es keine Position gibt, ist jeder Nachkauf ein
neues Signal; weil jedes Signal einen eigenen Stop trägt, entstehen fünf
Trailing-Stops für einen Bestand (**77 % Doppelungen**, Frage D).

---

## 1. Was heute existiert — an der Quelle geprüft

### 1.1 Die Bestandstabellen

| Tabelle | Zeilen | Spalten | Herkunft | trägt eine These? |
|---|---:|---:|---|---|
| `holdings` | 55 | 9 | **Bitpanda-Import** | ✘ |
| `hebel_positions` | 0 lokal / 188 im NB-Export | 15 | **Bitpanda-Import** (`importer/bitpanda_margin_positions.py`) | ✘ |
| `signals` | 5.296 | **133** | Rollen-Kette | ✔ vollständig |
| `hebel_signals` | 1.998 | 108 | Rollen-Kette | ✔ vollständig |

⚠️ **Der Bruch verläuft genau hier:** Die **Bestände sind real** (von der Börse
importiert), die **Thesen stehen in den Signalen**. Nichts verbindet beides zu
einer Position.

### 1.2 Was `holdings` weiß — und was fehlt

```
symbol · quantity · staked_quantity · updated_at · source
avg_buy_price_eur · avg_buy_price_manual_eur · avg_buy_price_tracked_qty
avg_buy_price_computed_at
```

⚠️ **Der Einstand gilt nur für einen Teil der Menge.** `avg_buy_price_tracked_qty`
sagt, für welche:

```
ETH:  gestakt 1,406  |  Einstand gilt für 0,537
SOL:  gestakt 8,884  |  Einstand gilt für 2,979
BTC:  frei    0,051  |  Einstand gilt für 0,162
```

⚠️ **Und `quantity` ist der FREIE Bestand** — gestaktes kommt additiv dazu
(Bitpanda bucht Stake-Transfers als Abgang, `rollen_eingabe.py:580-592`). Wer
`quantity > 0` filtert, zählt **9 Assets** fälschlich als frei.

### 1.3 Was `hebel_positions` weiß

```
symbol · richtung · status · eroeffnet_am · geschlossen_am
hebel_effektiv · positionswert_eur · kreditbetrag_eur · eigenkapital_eur
positionsmenge · liquidationspreis_geschaetzt_eur · quelle_tags_json
```

**Sie ist die einzige echte Positionsführung im System** — mit Eröffnung,
Schließung, Status und Liquidationspreis. ⚠️ **Aber auch sie trägt keinen Stop,
kein Ziel, keinen MFE und keinen Einstand für die These.** Der
Liquidationspreis ist ein **harter Zwangsausstieg**, kein Handelsstop.

### 1.4 Die Strategien — definiert, aber tot

`agent/betraege.py` legt Einsätze je **(Klasse, Strategie)** fest:

| Klasse | einstieg | swing | akkumulation |
|---|---:|---:|---:|
| spot | 800 € | *gestrichen 14.08.* | **250 €** |
| hebel | 1.000 € | 1.000 € | 1.000 € |
| aktien | 800 € | — | **400 €** |
| rohstoffe | 800 € | — | **400 €** |
| absicherung | 500 € | 500 € | 500 € |

Der Modulkopf sagt: *„Die Kette unterscheidet `einstieg`/`swing`/`akkumulation`
seit Paket 2 — **hier wird die Unterscheidung endlich benutzt.**"*

⚠️ **Sie wird nicht gesetzt.** Gemessen über 7.294 Signale:

| | `einstieg` | `None` | `swing` | **`akkumulation`** |
|---|---:|---:|---:|---:|
| spot_signals | 448 | 4.848 | 0 | **0** |
| hebel_signals | 0 | 1.998 | 0 | **0** |

**Die Akkumulationsbeträge sind festgelegt und unerreichbar.** Das ist **D1**
der Reparaturliste (*„Strategien swing/akkumulation nie benutzt — seit jeher"*)
und **S-1** (*„die Kette trägt `akkumulation` nicht"*).

### 1.5 Die drei Zeitskalen — und die fehlende vierte

`Konstruktion_Zeitskalen_06_08.md` benennt drei:

| | Skala | wirkt über | gesetzt durch |
|---|---|---|---|
| **A** | Regime | Wochen bis Monate | EMA20/50/200 |
| **B** | **Handelshorizont** | **0–5 Tage** | Vorgabe |
| **C** | Messhorizont | 7 und 14 Tage | Auswertungsparameter |

⚠️ **Der Handelshorizont ist mit 0–5 Tagen angesetzt — das ist die
Hebel-Zeitskala.** Für Spot, das längerfristig gehalten wird, existiert **keine
eigene Skala**. Das Dokument nennt die Folge selbst: *„Skala A gatet
Entscheidungen auf Skala B"* — ein Filter, der über die Lebensdauer eines
Trades nie umschaltet, ist *„kein Filter, sondern eine Konstante mit
Verfallsdatum."*

### 1.6 ⚠️ Der Grundsatz, der alles betrifft: Spot hat keinen Stop

`agent/betraege.py:94-96`, seit 13.08.:

> **„BEI SPOT OHNE STOP-ORDER IST DAS KEINE ORDER, SONDERN EINE RECHENGRÖSSE.**
> Der Nutzer hält Spot *‚aktuell auch ohne StopLoss'* — der Wert bestimmt dort
> nur die Größe, nicht eine Verkaufsanweisung."

**Das ist die Wurzel von Lücke 3.** Die Trailing-Regel wurde an Signalen
**mit** Barrieren gemessen (der Stop beendet den Trade). Bei Spot beendet er
nichts — er ist eine Zahl in einer Mail. „Stop unterschritten" heißt dort:
**es ist nichts passiert.**

---

## 2. Das Universum — was überhaupt verwaltet wird

| Assetklasse | Anzahl | Rolle | Bestand | Hebel möglich |
|---|---:|---|---:|---|
| **krypto** | 44 | `taktisch` | 24 | ✔ (24 von 44 freigeschaltet) |
| **etf** | 7 | `core` | teils | ✘ |
| **rohstoffe** | 4 | `core` | teils | ✘ |
| **aktien** | 2 | `core` | teils | ✘ |

Hauptgruppen bei den Nicht-Krypto: energie 3 · industriemetalle 3 · edelmetalle
2 · **absicherung 2** · aktien_sektoren 1 · agrarrohstoffe 1 · technologie_ki 1.

⚠️ **Zwei Rollen, zwei Logiken:** `taktisch` (44 Krypto) gegen `core` (13
übrige). Die Rollenunterscheidung existiert in den Stammdaten — **ob sie
irgendwo im Handelsablauf wirkt, ist offen und gehört geprüft.**

⚠️ **Die Absicherung ist eine eigene Kategorie mit eigenem Maßstab**
(`Konstruktion_Zeitskalen` 2b): SHORT-Absicherungen auf Nasdaq/S&P bemessen
sich am **abzusichernden Exposure**, nicht an einem Wunschbetrag. Ihre
Anlass-Sperrquote liegt bei **97,2 %** — dort ist der Fingerabdruck faktisch
eine Totalsperre.

---

## 3. Anforderungen je Geschäftsart — was dokumentiert ist

| | **SPOT** | **HEBEL** | **CORE (ETF/Rohstoff/Aktie)** | **ABSICHERUNG** |
|---|---|---|---|---|
| Vorteilsquelle | Rückkehr zum Mittel (H trägt, +0,15 R) | Drift/Momentum (⚠️ **zweimal gemessen, trägt nicht**) | nicht gemessen (2–7 Symbole, C1) | Exposure-Deckung |
| Haltedauer | längerfristig | Median **0,30 Tage** | nicht gemessen | offen |
| Stop | ⚠️ **keine Order** | real, + Liquidation | ⚠️ vermutlich wie Spot — **ungeprüft** | offen |
| Einsatz einstieg | 800 € | 1.000 € | 800 € | 500 € (Rückfall) |
| Einsatz akkumulation | 250 € | 1.000 € | 400 € | 500 € |
| Positionsführung | `holdings` | `hebel_positions` | `holdings` | `holdings` |
| Zeitskala | ⚠️ **fehlt** | B (0–5 T) | ⚠️ **fehlt** | ⚠️ **fehlt** |

---

## 4. Was bereits entschieden ist — und nicht neu erfunden werden darf

| | Festlegung | Quelle |
|---|---|---|
| **N-5** | Ein guter Trade = **Potential des Assets**, nicht Gebührendeckung | Zwischenstand |
| **N-6** | Kein Scharfschalten ohne Wirkungsnachweis | Zwischenstand |
| **N-8** | Anlass braucht **getrennte Fristen** für Spot und Hebel | Zwischenstand |
| **N-11** | Ausstiegsregel trifft Spot-Bestand, wofür sie nicht gemessen wurde | Zwischenstand |
| **D1 / S-1** | `swing`/`akkumulation` nie benutzt — **kein** Umbaufolge, seit jeher | Reparaturliste |
| **K3** | **Bestand passiert die Auswahl IMMER** — sonst schweigt die Verkaufsseite (21 von 24 fielen aus) | Abhängigkeitsprüfung |
| **§9.2** | Spot und Hebel haben **gegenläufige** Thesen — wer beide verlangt, sucht einen Wert, der zugleich gelaufen und zurückgeblieben ist | Konzept Einstiegsbewertung |
| — | Spot wird **ohne StopLoss** gehalten (Nutzerangabe 13.08.) | `betraege.py` |
| **C1** | Universum zu klein für Nicht-Krypto (2/4/7 Symbole) — **Code kann das nicht lösen** | Befundkarte 7.6 |

---

## 5. Die Lücken, geordnet nach Tragweite

| # | Lücke | Klassen | Größe |
|---|---|---|---|
| **L1** | **Keine Position mit These** — Stop/Ziel/MFE/Einstand fehlen | alle | 77 % Doppelungen |
| **L2** | **Akkumulation nicht angeschlossen** — Nachkauf = neues Signal | alle | 0 von 7.294 |
| **L3** | **Trailing phasenabhängig**, greift trotzdem immer | Spot + Hebel | −0,043 R in AUF |
| **L4** | **Keine Spot-Zeitskala** — Handelshorizont ist 0–5 Tage | Spot, Core | strukturell |
| **L5** | **Einstand nur teilweise bekannt** (`tracked_qty` < Bestand) | alle | 9 Assets nur gestakt |
| **L6** | **Rolle `taktisch`/`core` ohne erkennbare Wirkung** | alle | ungeprüft |
| **L7** | **Absicherung**: 97,2 % Anlass-Sperrquote | Hedge | faktisch aus |

---

## 6. Was diese Bestandsaufnahme NICHT klärt — die offenen Fragen an den Nutzer

1. **Woher soll der Stop einer gewachsenen Spot-Position kommen?** Es gibt
   keinen an der Börse, und der Einstand ist nur teilweise bekannt. Ohne Stop
   kein R — ohne R keine Trailing-Regel und **keine Trefferbilanz**.
2. **Was ist eine Position, wenn nachgekauft wird?** Eine mit neuem
   Durchschnittseinstand — oder mehrere Tranchen mit eigenen Thesen?
3. **Soll die Rolle `taktisch`/`core` den Ablauf steuern?** Heute steht sie in
   den Stammdaten und wirkt (soweit geprüft) nirgends.
4. **Gilt für Core-Assets dieselbe Logik wie für Spot-Krypto?** Bei 2–7
   Symbolen je Klasse ist nichts davon messbar (C1).

⚠️ **Ohne Antwort auf Frage 1 und 2 ist kein Umbau möglich, der nicht
später wieder aufgemacht werden muss.**

Verwandt: `Zielgroessen_und_Erfolgsmasse.md` 7a-N/7a-S · `Zwischenstand` N-8/N-11 ·
`Reparaturliste_Umbau_23_08.md` D1 · `Konstruktion_Zeitskalen_06_08.md` ·
`Konzept_Einstiegsbewertung_23_08.md` §9
