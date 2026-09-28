# Voranalyse K1 Schritt 2 — die Kombination: Kurven gemeinsam schätzen (28.09.2026)

**Nutzer:** *„Weiter mit der Voranalyse K1 — prüfen und gegenprüfen."*
Dazu die stehenden Vorgaben: *„ein Beitrag ist selbst schwach, in
Kombination stärker"* · *„was mir reicht, steht nicht zur Diskussion — ich
möchte ein funktionierendes System"* · *„die Regel muss auch in unseren Tests
und Simulationen funktionieren"* · *„Bewegung und Altersachse kein
künstlicher Blocker"*.

**Abgestimmt ist schon** (Voranalyse Kombination 27.09., K1 Schritt 2 und
die Korrekturen 7b): die Kurven werden **gemeinsam** geschätzt (K1a, sonst
zählt gemeinsame Information doppelt), auf der **Log-Odds**-Skala addiert
(K1b), **rollierend** nur aus der Vergangenheit kalibriert, und die Frage
ist: **trägt die Kombination mehr als der beste Einzelbeitrag?** Offen ist,
**womit** und **woran gemessen** — das legt diese Voranalyse vorab fest.

---

## 0. Auf welcher Ebene wir stehen

| Ebene | Frage | Stand |
|---|---|---|
| 1 | trägt ein Beitrag einzeln? | ✔ K1 Schritt 1 (2.671–2.676) |
| **2** | **trägt die Kombination — und mehr als ihr bester Teil?** | ➤ **dieser Schritt** |
| 3 | wirkt die Regel in der Erfolgsrechnung (Simulation)? | danach, nur wenn Ebene 2 trägt |

⚠️ **Die Bewertung bleibt neutral**: das Modell liefert je Anker ein **q**
(Wahrscheinlichkeit, dass +5 % vor −5 % kommt). Keine Geometrie, kein
Ertrag, keine Schwelle — die Schwelle wählt der Nutzer **nach** der Tabelle
(K5), die Hebelstufe kommt aus dem Risiko (K6).

---

## 1. Ist-Stand — was in die Kombination gehen kann

Aus den Befunden, nicht aus der Erinnerung (`python hebel_neubau.py`):

| Beitrag | Art | Beleg | geht ein? |
|---|---|---|---|
| **rsi**, **momentum_kurz**, **ema_abstand_atr** — *oben gestreckt* | je Asset | oberer Rand trägt in 4/4 Mengen, A4 bestätigt, Altersachse gültig (2.675/2.676); korreliert +0,56…+0,62 | ✔ gemeinsam |
| dieselben, **24 h alt** | je Asset | trägt in Suche, Prüfzeit **und 2022** (2.676) | ✔ als eigener Eingang |
| **funding_vortag_markt** | Markt | unterer Rand, 4/4 Mengen, **nur in der Suche** nachgewiesen (2.675) | ✔ Kontext-Kandidat |
| **konten_verh_markt** | Markt | unterer Rand, 3/4 Mengen, nur in der Suche | ✔ Kontext-Kandidat |
| **bisheriger Anstieg** (24 h in eigener ATR, A4) | je Asset | Gewicht nimmt mit dem Anstieg ab (2.671/2.676) | ✔ als eigene Kurve — **kein Schnitt** |
| oi_aenderung | je Asset | unterer Rand 3/4, **ohne unabhängige Bestätigung** | ◐ nur in Variante B |
| Premium, Käuferanteil, taker_verh, bandenge, Kontextfläche, die `_eigen`-Teile, *viele Longs je Asset*, das Alter 48 h | – | ohne Befund oder gefallen | ⛔ nein |

**Am Code:** `messe_k1_wirkungskurven.py` hat Lader, Phase-Normal,
Stufengrenzen, Selbstbezug und Nullwelten — die neue Messung nutzt
dieselben Bausteine (eigenes Werkzeug `messe_k1_schritt2_kombination.py`,
Loader aus `messe_e2_beitraege`). ⚠️ `sklearn`/`statsmodels` sind **nicht**
installiert, `scipy` ja — die logistische Schätzung wird mit
`scipy.optimize` gebaut (keine neue Bibliothek, kein Download).

---

## 2. Vorab festzulegen — C1 bis C8

| # | Frage | Empfehlung | warum |
|---|---|---|---|
| **C1** | **Eingänge** | **Variante A** (Hauptmodell): rsi, momentum_kurz, ema_abstand_atr **selbstbezogen**, je **aktuell und 24 h alt** (6), dazu funding_vortag_markt und konten_verh_markt **roh** (2) und der bisherige Anstieg (1) = **9 Kurven**. **Variante B**: A plus oi_aenderung roh | die Form *selbst* gewinnt bei allen drei in der **Suche** (Rand +0,054/+0,036/+0,057 gegen roh +0,037/+0,030/+0,046) — gewählt ohne Blick auf die Prüfzeit. Zwei Varianten = Bestes-von-2 |
| **C2** | **Modellform** | logistisch additiv: `logit q = logit(q_Phase) + b0 + Σ Kurve_j(Stufe von x_j)`; je Kurve die **12 Stufen** aus Schritt 1, Grenzen aus dem **Trainingsfenster**; kleine feste L2-Dämpfung auf den Stufengewichten (vorab, nicht nachgestellt); `b0` frei | K1b (Log-Odds, q bleibt in 0…1), K1 (Regler mit Optimum, keine Schalter), Stufen wie in Schritt 1 — vergleichbar |
| **C3** | **Kalibrierung** | **rollierend**: für jeden Monat 2024-01 bis 2026-08 auf den **12 Monaten davor** geschätzt (nur Ausgänge ≤ t − 24 h), dann auf den Monat angewandt. **Zusätzlich** fest: Suche 2023–2024 → Prüfung 2025-01 bis 2026-08, für die Nullwelt | K5 *Kalibrierung vorwärts*; Prüfplan § 3.2; die feste Teilung ist billig genug für 40 Nullwelten |
| **C4** | **Lehrer** | q5 (+5 vor −5, 24 h), nur Anker mit Treffer, gegen das Phase-Normal (wie Schritt 1); **K4b**: dieselbe Rechnung auf **72 h** als Auskunft — das Vorzeichen des Gewinns darf dort nicht drehen | K4 abgestimmt; 120 h bräuchte einen Lader mit 120 h Vorlauf (Speicher) — deshalb 72 h |
| **C5** | **Nullwelt** | Zeitverschiebung: je Ziehung **alle** Asset-Eingänge eines Assets um **denselben** Versatz (ihr Zusammenhang bleibt), die Markteingänge **gemeinsam** für alle Assets; 40 Ziehungen, **identisch** geschätzt und ausgewertet | E-10; nur so bleibt die Korrelation der Eingänge, und die Zuordnung zu den Ausgängen fällt |
| **C6** | **Regeltest** | dasselbe Modell mit **Zufallseingängen** derselben Art (6 geglättete je Asset, 2 Marktreihen, 1 Zufallsanstieg) — der Gewinn muss **im Nullband** liegen; dazu eine **Pflanzung** (+0,02 und +0,04 auf den oberen Rand einer verschobenen Kopie): ab welcher Größe erkennt die Kombination sie? | Nutzer 28.09.: *die Regel muss in unseren Tests funktionieren* |
| **C7** | **Gegenprüfungen** | (a) **Doppelzählung**: Summe der einzeln geschätzten Kurven gegen die gemeinsame Schätzung; (b) **Eingänge 1 h älter** (P2); (c) **je Asset**, **je Jahr**, **je BTC-Drittel**; (d) **2022** mit Moment-Bezug als Auskunft; (e) vier Mengen | K1a, Pflichtablauf § 6, *in jedem Regime* |
| **C8** | **kein Blocker** | Ergebnis ist ein **stetiges q** je Anker; keine Stufe, keine Sperre, keine Schwelle in diesem Schritt. Die **K5-Tabelle** (je mögliche Schwelle: Signale je Monat und Asset, tatsächliches q, je Regime) wird **ausgegeben**, nicht entschieden | Nutzervorgabe 28.09.; K5: *Höhe durch den Nutzer nach der Tabelle* |

---

## 3. Das Kriterium *trägt* — vorab

**Kennzahl G** = mittlerer **Log-Loss-Gewinn** je Anker auf **ungesehenen**
Monaten gegenüber dem Phase-Normal mit freiem `b0` (also gegen *„dieses Asset
läuft wie immer"*). Dazu als lesbare Größe die **Spanne des q**: tatsächliches
q im obersten und untersten Zehntel des geschätzten q.

| # | Bedingung | Ergebnis bei Nein |
|---|---|---|
| **T1** | G der Kombination **jenseits der Nullwelt** (90. Perzentil, Bestes-von-2 Varianten) in **allen vier** Mengen | die Kombination trägt nicht — ein Befund über die **Beitragslage**, nicht über das System |
| **T2** | **mehr als der beste Einzelbeitrag**: G(Kombination) − max G(einzelne Familie) jenseits **seines** Nullbands in ≥ 3 von 4 Mengen | Kombination = ihr bester Teil — dann nur dieser weiter |
| **T3** | **kalibriert**: auf ungesehenen Monaten Steigung der Kalibrierungsgeraden 0,7–1,3 und in jedem Zehntel mit ≥ 1.000 Ankern \|beobachtet − geschätzt\| ≤ 0,02 | **keine Schwelle** (K5-Pflicht) — erst nachkalibrieren |
| **T4** | **in jedem Regime**: G > 0 in jedem Jahr 2024/2025/2026 und jedem BTC-Drittel | *„wenn nicht, dann reden wir"* — kein stilles Weitermachen |
| **T5** | **je Asset**: ≥ 60 % der Assets (≥ 200 Anker) mit G > 0 | wirkt nur für wenige — Klumpenfrage |
| **R** | **Regeltest**: G der Zufallseingänge im Nullband; Pflanzung gefunden ab einer benannten Größe | die Regel ist nicht verwendbar |

⚠️ **Die Prüfzeit hat einen Versatz** (+0,009/+0,013, 2.675). `b0` wird im
rollierenden Fenster mitgeschätzt und fängt ihn nur **verzögert** — die
Kalibrierung (T3) wird deshalb **mit und ohne** Monatsversatz ausgewiesen,
damit ein Regimeeffekt nicht als Modellfehler oder als Modellgewinn gelesen
wird.

---

## 4. ⚠️⚠️ PRÜFUNG UND GEGENPRÜFUNG DIESER VORANALYSE

### 4a. Gegen die stehenden Regeln

| Regel | Prüfung |
|---|---|
| 1 Takt ist kein Signalgeber | ✔ q hängt nur an der Lage; die Anker 00/06/12/18 sind **Messpunkte**; der Uhrzeiteffekt ist klein (2.676) und wird je Ankerstunde ausgewiesen |
| 2 keine Gebühren | ✔ q5 ist eine Reihenfolge, keine Rendite |
| 3 kein Asset-Rang | ✔ Urteil gegen das **eigene** Normal; die Stufengrenzen sind absolute Werte je Merkmal; kein Querschnittsrang |
| 4 Fakt ist keine Begründung | ✔ *gestiegen* wirkt nur über seine gemessene Kurve (A4) |
| Grundgesamtheit | ✔ `unverzerrt:1..3` **und** `bestand` |
| kein Blocker | ✔ C8 — stetiges q, keine Schwelle |
| Regeltest | ✔ C6 |
| R-R11 | ✔ Schritt 2 stößt keinen Befund um; die Einzelkurven sind in Schritt 1 registriert |

### 4b. Fallen — und was dagegen steht

| Falle | Gegenmittel |
|---|---|
| **Leck über die Stufengrenzen** — Grenzen aus der ganzen Zeit kennen die Zukunft | Grenzen **je Trainingsfenster** (C2); in der festen Teilung aus der Suche |
| **Leck über das Normal** | das Phase-Normal nutzt nur Ausgänge ≤ t − 24 h (G1 aus Schritt 1 geprüft) |
| **überlappende Anker** — vier Anker je Tag mit 24-h-Fenstern sind nicht unabhängig | Urteil gegen die **Nullwelt**, nicht gegen einen Standardfehler |
| **Überanpassung** — 9 Kurven × 11 Gewichte ≈ 100 Parameter | rund 90.000 Anker je 12-Monats-Fenster (Suche: 176.000 in zwei Jahren), feste Dämpfung, Urteil nur auf **ungesehenen** Monaten |
| **Marktkurven haben wenige Fälle** (so viele wie Markttage) | gemeinsame Verschiebung (C5); ihre Einzelwirkung wird zusätzlich ausgewiesen — trägt die Kombination nur durch sie, ist das zu sagen |
| **aktuell und 24 h alt hängen zusammen** | gemeinsame Schätzung verteilt die Wirkung; (a) zeigt, wie viel eine Summe doppelt zählen würde |
| **junge Listings** haben kein 12-Monats-Normal (K2b) | sie fallen in diesem Schritt heraus — für den Betrieb bleibt eine Regel offen (K2b) |
| **Hebel-Teilmenge** (Ü3: 43 bei Bitpanda) | als **Auskunft** über Namensgleichheit — mit dem Vorbehalt der fehlenden Symbolbrücke (2.612) |
| **Speicher** — ein Tageszeit-Lauf brach am 28.09. ab | Anker-Teilmenge statt voller Stundenreihe im Modell; Vollständigkeit **am Inhalt** prüfen, Exit-Code korrekt sichern |

### 4c. Gegenprüfung — hält der Vorschlag den abgestimmten Stand?

| abgestimmt | hier |
|---|---|
| K1 *Summe der Kurven, rollierend* | ✔ C2/C3 — als **gemeinsame** Schätzung (K1a) auf Log-Odds (K1b) |
| K1 *roh und selbst nebeneinander, die bessere nach vorab festgelegtem Kriterium* | ✔ C1 — Kriterium: Rand in der **Suche** |
| K1 Schritt 3 *Wechselwirkungen* | ⛔ **nicht hier** — A4 geht additiv ein; *oben gestreckt wirkt schwächer, wenn schon gestiegen* ist eine Wechselwirkung und gehört in Schritt 3 |
| K2 Phase, Kontrollen | ✔ Offset = Phase-Normal; Moment/Tag als Auskunft |
| K3 Kontext ohne Gewicht (2.670) | ✔ die Kontextfläche geht nicht ein; nur die zwei Marktkurven |
| K4 q5, 72/120 h | ✔ 24 h Urteil, 72 h Auskunft; ⚠️ 120 h nicht — benannt |
| K5 Schwelle durch den Nutzer nach Tabelle | ✔ C8 — Tabelle ja, Schwelle nein |
| K5b 3–5 Stufen | ⛔ nicht hier — erst nach der Tabelle |
| K6/K7 | ⛔ nicht hier |

---

## 5. Was NICHT in diesen Schritt gehört

Wechselwirkungen (Schritt 3) · Schwellenwahl und Stufenzahl (K5/K5b, durch den
Nutzer nach der Tabelle) · Hebelstufe (K6) · Markpreis (K7) · Simulation
(Ebene 3) · Betrieb.

---

## 6. Umfang und Laufzeit

Je Menge: rollierend 32 Schätzungen × 2 Varianten + Einzelfamilien, feste
Teilung mit 40 Nullwelten, Regeltest, Gegenprüfungen — geschätzt **20 bis 40
Minuten** je Menge, die vier Mengen **nacheinander**. Zuerst ein
**Werkzeugtest** auf dem Bestand, der die Mechanik prüft (Alter 0/Einzelkurve
gegen Schritt 1 zeilengleich, Zufall im Nullband) — ohne inhaltliche
Zwischenmeldung (*kleine Läufe täuschen*).

---

## 7. Zur Abstimmung

| # | Empfehlung |
|---|---|
| **C1** | Variante A: rsi/momentum/ema_abstand selbst, je aktuell und 24 h alt; funding_markt, konten_verh_markt; bisheriger Anstieg — Variante B plus oi_aenderung |
| **C2** | logistisch additiv auf Log-Odds, 12 Stufen je Kurve, Grenzen je Trainingsfenster, feste kleine Dämpfung |
| **C3** | rollierend 12 Monate, geprüft 2024-01 bis 2026-08; feste Teilung für die Nullwelt |
| **C4** | q5/24 h als Urteil, 72 h als Auskunft |
| **C5** | Zeitverschiebung je Asset (alle Asset-Eingänge gemeinsam) und gemeinsam für den Markt, 40 Ziehungen |
| **C6** | Regeltest Zufall und Pflanzung |
| **C7** | Doppelzählung, 1 h älter, je Asset/Jahr/BTC-Drittel, 2022, vier Mengen |
| **C8** | stetiges q, die K5-Tabelle als Ausgabe — keine Schwelle |
| **T1–T5, R** | wie Abschnitt 3 |

---

## 8. ✔ ABGESTIMMT (28.09.2026) — C1 bis C8 wie empfohlen, dazu zwei Nutzerfragen

**Nutzer:** *„ja, C1 bis C8 wie empfohlen, committen, dann bauen und messen,
prüfen und gegenprüfen — 1. sind die aktuell in Frage kommenden Beiträge auch
für das Notebook geprüft? Datenquellen, Auslastung (sollte kein Thema sein,
aber sicher ist sicher). 2. Ist klar, wie die Beiträge wirken sollen, bzw. ist
das Wechselwirkungsthema ein eigener Punkt, den wir jedenfalls prüfen
sollten?"*

### 8a. Frage 1 — die Beiträge am Notebook: geprüft am Betriebscode

⚠️ **Bisher nicht geprüft** — jetzt am **Code** (gleich auf beiden Geräten),
nicht am Notebook selbst (Regel: Prüfungen gegen eine Kopie).

| Eingang | Messung (Desktop) | Betrieb heute (Code) | Lücke |
|---|---|---|---|
| rsi, momentum_kurz, ema_abstand_atr, ATR, **24 h alter Wert**, bisheriger Anstieg | **Stundenkerzen** (`stundenkurse.db`) | ⛔ nur **Tageskerzen** (Kraken, Rückfall Binance/Bybit, `api/boersen_klines.py`) — kein Stundensammler (Plan Phase 1, Punkt 6: *geplant, nicht gebaut*, 2.635/2.636) | **ein Stundensammler** — und für das **Phase-Normal** (K2) 12 Monate Stundenhistorie je Asset |
| selbstbezogene Form | 720 h Vorlauf | – | im Sammler enthalten (30 Tage) |
| **funding_vortag_markt** | Tagessumme des Vortags, **Median über alle Assets der Menge** | aktueller Satz über `premiumIndex` (**ein** Abruf für alle 885 Paare) alle 15 min | Vortagessumme aus der funding-Historie beschaffbar; ⚠️ **Grundgesamtheit des Medians** |
| **konten_verh_markt** | Median über alle Assets der Menge (~125, mit Eingestellten) | `long_account_pct` je Asset alle 15 min, aber nur für die **Kryptowerte der Kette** (Watchlist, 43 Hebelwerte) | ⚠️⚠️ **Grundgesamtheit**: ein Median über 43 ist ein anderer Wert als über 125 — *die Grundgesamtheit ist keine Stellschraube* |
| Symbolzuordnung | Binance-Symbole | Bitpanda-Ticker | Stammsatz (2.612) |
| **Auslastung** | – | Stundenkerzen: rund 43 Abrufe je Stunde (1.000 Kerzen je Abruf) · funding 1 Abruf · Long-Anteil läuft schon (43 je 15 min) · das Modell selbst ist im Betrieb ein **Tabellennachschlag** (Gewichte werden am Desktop geschätzt) | ✔ **kein Thema** |

➤ **Folge für diese Messung:** nichts blockiert sie — sie läuft auf der
Messbasis am Desktop. ⭐ **Aber eine Gegenprüfung kommt dazu** (C7 f): die
Marktkurven zusätzlich mit dem Median **nur über die Hebelwerte des
Betriebs** (43, über Namensgleichheit — Vorbehalt 2.612) — wie weit weicht
er ab, und trägt die Kombination damit noch? So ist die Grundgesamtheit
**gemessen**, bevor sie im Betrieb gewählt wird.

➤ **Folge für den Betrieb** (nicht jetzt, nach der ganzen Kette): ein
Stundensammler mit 12 Monaten Vorlauf, die funding-Vortagessumme, eine
Entscheidung über die Grundgesamtheit der Marktmediane, der Stammsatz. Als
Voraussetzungen in den Plan aufgenommen.

### 8b. Frage 2 — wie die Beiträge wirken, und die Wechselwirkungen

**Wie sie wirken (Schritt 2):** jeder Beitrag hebt oder senkt die
**Log-Odds** von q über **seine** Kurve — ein Regler je Stufe, gemeinsam
geschätzt, damit nichts doppelt zählt. Gleiche Lage → gleicher Beitrag,
**unabhängig** davon, was die anderen Beiträge zeigen. Das ist die Annahme
*additiv* — und genau sie ist zu prüfen.

**Die Wechselwirkungen sind ein eigener Punkt** — K1 Schritt 3, am 27.09.
abgestimmt (*Suchgerät im Suchzeitraum, Funde als lesbare Regeln auf
ungesehenen Daten prüfen*). ✔ **Ja, er ist jedenfalls zu prüfen**, und die
Kandidaten sind heute schon benennbar — sie werden **vorab** festgelegt,
statt nur offen gesucht:

| # | Wechselwirkung | warum sie naheliegt |
|---|---|---|
| **W1** | *oben gestreckt* × **bisheriger Anstieg** (A4) | A4 zeigte: bei 2–3 ATR schwächer — wirkt der Rand weniger, **weil** schon viel gelaufen ist? |
| **W2** | **aktueller** × **24 h alter** Wert | *beide hoch* (bestätigte Lage) gegen *nur jetzt hoch* — mehr als die Summe? |
| **W3** | Beitrag × **Kontext** (funding_markt, BTC-Lage) | wirkt *oben gestreckt* in einem überhitzten Markt anders? |
| **W4** | Beitrag × **Volatilität** (ATR zum Einstieg) | ±5 % ist für ruhige Assets selten (K4a) |

⭐ **In Schritt 2 schon eine Vorprüfung** (C7 g, nur Auskunft, ändert
kein Urteil): ist das additive Modell in den Zellen von W1/W2 **systematisch
daneben** (beobachtetes gegen geschätztes q je Zelle, ungesehen)? Wo ja, ist
das der Hinweis für Schritt 3 — gemessen, nicht vermutet.

⚠️ **Kein Blocker auch hier:** eine gefundene Wechselwirkung wird eine
**Kurve mehr** (ein Gewicht je Zelle), keine Sperre.

### 8c. Was sich an der Festlegung dadurch ändert

| | |
|---|---|
| C1–C8, T1–T5, R | **unverändert** |
| C7 | **(f)** Marktmedian nur über die Hebelwerte · **(g)** Vorprüfung W1/W2 — beide **Auskunft**, festgelegt **vor** der Messung |

---

## 9. ⛔ WERKZEUGTEST (28.09.2026) — die vorab festgelegte Dämpfung ist zu schwach, die Marktkurven zu fein

Der Werkzeugtest (Bestand, 3 Nullwelten, 3 Monate) prüfte nur die Mechanik —
und fand, dass sie **so nicht trägt**. Inhaltlich wird daraus nichts gewertet.

| Befund | Beleg |
|---|---|
| die **Nullwelt** liegt im Mittel bei **−17** statt nahe 0 | Werkzeugtest, feste Teilung |
| die **Kalibrierung** ist unbrauchbar (Steigung 0,01; geschätzt 0,15 gegen beobachtet 0,39) | Werkzeugtest |
| die **Marktkurven** mit 12 Stufen verlieren auf ungesehener Zeit stark (konten_markt rollierend −74) | Werkzeugtest |

**Ursache, geprüft NUR innerhalb der Suche** (2023 schätzen → 2024 anwenden;
die Prüfzeit 2025/26 bleibt unberührt, damit nichts nach dem Ergebnis gewählt
wird) — Gewinn auf 2024 in tausendstel nat, bestand / unverzerrt:1:

| Dämpfung | ema_abstand allein | rsi allein | Kombination ohne Markt | Kombination, Markt in Dritteln |
|---|---|---|---|---|
| 20 (vorab) | +1,28 / +1,76 | +0,91 / +1,37 | −1,21 / −0,17 | −6,92 / −9,62 |
| 200 | +1,95 / +2,13 | +1,32 / +1,64 | +0,75 / +1,15 | −0,47 / −4,37 |
| 2.000 | +0,95 / +1,21 | +0,65 / +0,89 | +1,28 / +1,63 | +6,92 / +4,42 |
| 20.000 | +0,14 / +0,20 | +0,09 / +0,14 | +0,26 / +0,39 | +2,43 / +2,53 |

| | Lehre |
|---|---|
| 1 | **Die Anker sind nicht unabhängig** — vier je Tag mit überlappenden 24-h-Fenstern, alle Assets am selben Markttag. Die Schätzung zählt jeden Anker voll und lernt Rauschen; eine **feste** Dämpfung kann das nicht für jedes Modell richtig treffen |
| 2 | Die nötige Stärke **hängt am Modell**: eine Familie verträgt ~200, die Kombination braucht ~2.000 |
| 3 | Ein Marktwert gilt für alle Assets einer Stunde — mit 12 Stufen stehen hinter einer Stufe nur ~30 Markttage (dieselbe Lage wie K3a) |
| 4 | ⚠️ Die Tabelle zeigt die **Empfindlichkeit** — aus ihr wird die Dämpfung **nicht gewählt** |

### 9a. ✔ ABGESTIMMT 28.09. (Nutzer: *ja, Ä1 bis Ä3 wie empfohlen, committen, dann messen*) — festgelegt VOR der Messung

| # | Änderung an C2 | warum |
|---|---|---|
| **Ä1** | **Dämpfung je Modell und Trainingsfenster selbst bestimmt**: zeitlich geblockte Kreuzvalidierung **innerhalb** des Fensters (4 Blöcke), Gitter 20 / 200 / 2.000 / 20.000, das beste nach Log-Loss auf dem ausgelassenen Block. Jede Familie und jede Kombination bekommt ihre eigene | nur Vergangenheit, kein Blick auf die Prüfzeit; im Betrieb genauso anwendbar; T2 vergleicht dann fair (jedes Modell in seiner besten Form) |
| **Ä2** | **Marktkurven in Dritteln** | Fallzahl = Markttage; derselbe Schritt wie K3a (5 × 5 → 3 × 3) |
| **Ä3** | die **Nullwelt** bekommt dieselbe Kreuzvalidierung je Ziehung | sonst wäre sie mit einer fremden Dämpfung zu weit oder zu eng |
| — | C1, C3–C8, T1–T5, R | **unverändert** |

**Preis:** rund 13 Schätzungen statt einer je Modell — etwa **1,5 bis 2 Stunden
je Menge**, **6 bis 8 Stunden** für alle vier, nacheinander (auch über Nacht).
Ein Werkzeugtest geht voraus.

**Zweiter Werkzeugtest (28.09.):** Mechanik in Ordnung - Nullwelt im Mittel -0,67 (vorher -17), 90. Perzentil +0,08, Zufall im Nullband, die Kreuzvalidierung waehlt 2.000 fuer die Kombination. Die Pflanzung fand +0,02 und +0,04 nicht; die Leiter ist deshalb nach dem Messstandard auf +0,08 und +0,16 verlaengert - das beschreibt nur die Aufloesung, T1-T5 unveraendert. Festgelegt VOR den vier Laeufen.
