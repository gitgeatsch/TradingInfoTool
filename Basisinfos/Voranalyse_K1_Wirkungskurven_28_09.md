# Voranalyse K1 Schritt 1 — die Wirkungskurven je Beitrag (28.09.2026)

> **Abgestimmt (K1, 27.09.):** je Beitrag eine **feste Wirkungskurve** über den
> ganzen Wertebereich (Regler, kein Schalter; ein Optimum ist erlaubt);
> Merkmal **roh und selbstbezogen** (gegen die eigenen letzten 30 Tage)
> nebeneinander; geurteilt wird über die **ganze Kurve** (K1d), nicht je Stufe;
> Urteil gegen die **Phase** (K2), Kontrollen Moment und Tag; trägt der Markt
> viel, wird das Merkmal in `_markt` und `_eigen` geteilt.
>
> **Nutzer 28.09.:** *„K1 Schritt 1 Voranalyse — prüfen und gegenprüfen wie
> immer."*

⚠️ **Dieses Blatt baut und misst nichts.** Die Zahlen sind Zählungen zur
Datenlage.

---

## 1. Was die bisherigen Schritte für K1 gelehrt haben

| Lehre | aus | Folge für die Kurven |
|---|---|---|
| Schwellen-Urteile kippen an der Kriteriengrenze, die **Werte** bleiben | 2.669 | genau deshalb Kurven statt Schwellen |
| Tagesmerkmale hängen an der **Startstunde** der Episoden | 2.666 | feste Tagesanker 00/06/12/18 UTC (wie K3) |
| Eine Nullwelt, die gleichzeitige Assets als unabhängig zählt, ist zu optimistisch | 2.670 | **Zeitverschiebung je Asset** (K2a) |
| Die Anlage hat eine **Auflösungsgrenze** — beim Kontext 0,06 bis 0,08 | 2.670 | Positivkontrolle ist Pflicht, bevor *trägt nicht* gilt |
| Käuferanteil **begleitet**, momentum **ist** die Bewegung | 2.665 (E2g) | Fortsetzungsprobe je Kurve |
| Die Messbasis war überlebensverzerrt | 2.668 / 2.669 | `--menge unverzerrt` — aber siehe 2 |

---

## 2. ⛔ Datenlage — ein Loch, das vor der Messung zu schließen ist

Gezählt auf `unverzerrt:1`, 515.487 Tagesanker 2023-01 bis 2026-08, davon
**19,9 %** auf eingestellten Paaren:

| Merkmal | Wert vorhanden: Bestand | Eingestellte |
|---|---|---|
| Kursmerkmale (ema_abstand_atr, momentum_kurz, rsi, bandenge, vola, volumenschub) | 100 % | 100 % |
| funding_vortag | 100 % | 93,1 % |
| Käuferanteil, Premium | ✔ | ✔ (2.669) |
| **Terminmarkt** (oi_aenderung, konten_verh, taker_verh, top_konten_verh, top_summe_verh, oi_je_umsatz) | 96 % | **0 %** |

⛔ Eine Kurve für **konten_verh** (die Sperre *viele Longs*) stünde damit
wieder **nur auf Überlebenden** — genau der Fehler aus 2.668.

✔ **Das Archiv hat die Daten**: `futures/um/daily/metrics` gibt es auch für
eingestellte Paare (WAVESUSDT ab 2021-12-01), im selben Format, das
`hole_terminmarkt_historie.py` liest. Umfang: rund **99.000 Tagesdateien**
(Tage mit echtem Handel der Eingestellten) — mit vier Arbeitern und Pausen
geschätzt **6 bis 9 Stunden**.

---

## 3. Der Aufbau — vorab festzulegen

| # | Punkt | Vorschlag | Warum |
|---|---|---|---|
| **W1** | Kandidaten (Richtung) | funding_vortag · konten_verh · top_konten_verh · taker_verh · oi_aenderung · kaeufer_1h / 6h / 24h / rel · premium_jetzt / 24h · momentum_kurz · rsi · ema_abstand_atr · bandenge — **15 Merkmale** | alle mit kausalem Wert; Höhe/Risiko (vola, volumenschub, ATR) gehört zu Bewertung 2, nicht hierher |
| **W2** | Formen | **roh** und **selbstbezogen** = Wert minus Median der eigenen letzten 30 Tage (720 h, nur Vergangenheit) → **30 Kurven** | K1 |
| **W3** | Stufen | **12**: zehn Dezile plus die Ränder **P1** und **P99** als eigene Stufen; Grenzen aus der **Suche** (absolute Werte, gepoolt) | 20 Stufen hätten je Stufe ~8.800 Anker; die bisherigen Funde liegen an den Rändern (P5/P95) — die Ränder brauchen eigene Stufen |
| **W4** | Lehrer | q5 (+5 vor −5 %, 24 h) urteilt; Achse 3/5/10 % × 24/72/120 h zeigt die Form | K4 |
| **W5** | Bezug | **Phase**: eigenes Asset, letzte 12 Monate, nur bekannte Ausgänge (≤ t − Fenster); Kontrolle **Moment** (Monat) und **Tag** (andere Assets am selben Tag) | K2 |
| **W6** | Anker | feste Tagesanker 00/06/12/18 UTC | 2.666 |
| **W7** | Nullwelt | **Zeitverschiebung je Asset**: die Merkmalsreihe jedes Assets kreisförmig um ≥ 60 Tage gegen seine Ausgänge verschoben, 40 Ziehungen | K2a; erhält die Selbstähnlichkeit des Merkmals und die Markttage der Ausgänge |
| **W8** | **Urteil über die ganze Kurve** (K1d) | Kennzahl **S** = Σ Anker je Stufe × Dq²; gegen die Nullwelt, **Bestes-von-30** (90. Perzentil); dazu die **Form**: Rangkorrelation des Stufenprofils Suche gegen Prüfung ≥ 0,5 | ein Test je Kurve; S erkennt auch eine Kurve mit Optimum in der Mitte |
| **W9** | Such-/Prüf-Trennung | Suche 2023-01 bis 2024-12, Prüfung 2025-01 bis 2026-08, 2022 als Kontrolle (Moment) | wie K3 |
| **W10** | **Kurve trägt** | S jenseits der Grenze (Suche) **und** Formkorrelation ≥ 0,5 **und** die Randstufen (P1, P99) haben in der Prüfung dasselbe Vorzeichen **und** ≥ 3 von 4 Jahren gleiche Form **und** ≥ 60 % der Assets mit positiver Profilkorrelation | vorab, nicht nachgestellt |
| **W11** | Teilung Markt / eigen (K2) | schrumpft das Profil gegen die Tages-Kontrolle um **mehr als die Hälfte**, werden `_markt` (Median aller Assets zur Stunde) und `_eigen` (Asset minus Median) als eigene Kurven nachgemessen | K2 |
| **W12** | Fortsetzungsprobe (E2g) | je tragender Kurve: Altersachse (Merkmal 6 / 12 / 24 h alt) und Schichtung nach der eigenen 24-h-Rendite | OPTIMUM: *Lage vorher*, nicht *schon gestiegen* |
| **W13** | Menge | `unverzerrt:1..3` urteilt, `bestand` als Vergleich | 2.669 |

---

## 4. ⚠️⚠️ PRÜFUNG UND GEGENPRÜFUNG DIESER VORANALYSE

**Prüfung — gegen Regeln und Abstimmung**

| Regel / Entscheidung | Prüfung |
|---|---|
| K1 (Kurve, roh + selbstbezogen, ganze Kurve) | ✔ W2, W3, W8 |
| K2 (Phase, Moment, Tag, Teilung) | ✔ W5, W11 |
| K4 (q5, Achse) | ✔ W4 |
| Regel 3 (kein Asset-Rang) | ✔ die Stufen sind **absolute Werte** (Grenzen aus der Suche, gepoolt); geurteilt gegen das **eigene** Asset |
| Regel 4 (Fakt keine Begründung) | ✔ ein Wert wirkt nur über seine **gemessene** Kurve |
| Grundgesamtheit | ⛔ **nicht erfüllt** für die sechs Terminmarkt-Merkmale, solange Teil B fehlt (Abschnitt 2) |
| Pflichtablauf § 6 | ✔ Such-/Prüf-Trennung, Nullwelt, Bekanntheitszeitpunkt, Gegenprüfung, Startstunden, Stunden statt Zeilen |

**Gegenprüfung — wo der Plan selbst falsch sein kann**

| # | Einwand | Folge |
|---|---|---|
| **G1** | **Vorgriff im Phasen-Normal** | wie K3: Normal nur aus Ausgängen ≤ t − Fenster; Probe mit absichtlichem Vorgriff |
| **G2** | **Vorgriff im Selbstbezug:** der 30-Tage-Median darf nur Vergangenheit enthalten, und bei **funding_vortag** nur Tage bis zum Vortag | Median über [t − 720 h, t − 1 h]; für funding über abgeschlossene Tage |
| **G3** | **Überlebende bei den Terminmarkt-Merkmalen** | Teil B vorher laden (A1), sonst diese sechs Kurven nur mit Vorbehalt |
| **G4** | **Auflösung** — wie groß muss eine Kurve sein, damit S sie findet? | **Positivkontrolle**: eine lineare Wirkung bekannter Stärke (Dq von −d bis +d über die Stufen) in echte Ausgänge pflanzen, d = 0,01 / 0,02 / 0,04 / 0,08 — erst dann gilt *trägt nicht* als Aussage über das Merkmal |
| **G5** | **Gepoolte Stufen** werden von volatilen Assets dominiert — ein ruhiges Asset erreicht die Ränder selten | die **selbstbezogene** Form behebt das; zusätzlich je Asset ausweisen, wie viele Anker in P1/P99 liegen |
| **G6** | **Mehrfachtesten**: 30 Kurven × Achse | geurteilt nur auf q5/24 h mit Bestes-von-30; die Achse urteilt nicht |
| **G7** | **Korrelierte Beiträge** (funding und konten_verh; die drei Käuferfenster) | Schritt 1 misst einzeln; die **Korrelationsmatrix** wird mitgeliefert, damit Schritt 2 (gemeinsam schätzen, K1a) weiß, was doppelt zählt |
| **G8** | **Die Zeitverschiebung je Asset** zerstört die Gleichzeitigkeit zwischen Assets — ein Merkmal, das nur als **Markt** wirkt, wird dann gegen eine zu breite Nullwelt gehalten | genau das fängt die Tages-Kontrolle (W11) ab; die Positivkontrolle (G4) prüft die Anlage selbst |
| **G9** | **Form Suche gegen Prüfung** bei einer flachen Kurve ist Zufall — eine Korrelation von 0,5 zwischen zwei Rauschprofilen kommt vor | das Formkriterium gilt **nur zusammen** mit S jenseits der Grenze (W10), nie allein |
| **G10** | **Fortsetzung**: momentum, rsi, Käuferanteil messen die Bewegung selbst | W12; wie mit einer begleitenden Kurve umzugehen ist, entscheidest du (A4) |

**Ergebnis der Prüfung:** Der Plan hält Regeln und Abstimmung **bis auf die
Grundgesamtheit der Terminmarkt-Merkmale** (G3) — das ist vor der Messung zu
entscheiden. G1, G2 und G4 sind Pflichtteile des Baus.

---

## 5. ✔ Abgestimmt (28.09.2026) — A1 bis A4 wie empfohlen

| # | Frage | Empfehlung |
|---|---|---|
| **A1** | **Teil B laden** (Terminmarkt der Eingestellten, ~99.000 Tagesdateien, 6–9 h mit Pausen) — und in der Zeit die **elf** Merkmale (22 Kurven) mit vollständigen Daten messen (funding, Käuferanteil ×4, Premium ×2, momentum, rsi, ema_abstand_atr, bandenge)? | **ja** — sonst stehen konten_verh und oi auf Überlebenden |
| **A2** | **12 Stufen** (Dezile + P1 + P99) statt 20? | ja |
| **A3** | W1–W13 so festlegen? | ja |
| **A4** | **Begleitende Kurven** (die Fortsetzungsprobe zeigt: es misst die Bewegung selbst) — dürfen sie als **Sperre** in die Kombination (*schon gefallen → nicht einsteigen*), aber **nicht** als Einstieg? | **ja, nur als Sperre** — deine OPTIMUM-Regel schließt den Einstieg aus, eine Sperre kauft nichts *nachdem es schon gestiegen ist* |

**Nutzer 28.09.:** *„ja, A1 bis A4 wie empfohlen, committen, dann laden und
messen — zu A4 ja: hier wäre wichtig zu unterscheiden, wie weit gestiegen —
nur ‚bestätigte' Bewegung, also positiv, oder die Bewegung ist bereits
gelaufen. Nicht so einfach, sonst wird es ein Blocker."*

### ⭐ A4 präzisiert — W12 wird eine Kurve über den bisherigen Anstieg

*Begleitend* ist **kein Pauschalurteil**. Für jede Kurve, die die
Fortsetzungsprobe nicht besteht, wird zusätzlich gemessen:

| | |
|---|---|
| **Achse** | bisheriger Anstieg des Assets in den letzten 24 h **in eigener ATR**: < 0 · 0–0,5 · 0,5–1 · 1–2 · 2–3 · > 3 ATR |
| **je Bereich** | Dq der Kurve (Randstufen P95/P99 und P1/P5) gegen die Phase |
| **„bestätigt"** | die Bereiche, in denen die Lage **noch positiv** trägt — dort ist sie **als Einstieg erlaubt** |
| **„gelaufen"** | die Bereiche, in denen sie kippt — dort **nur als Sperre** |
| **die Grenze** | wird **gemessen** (wo kippt das Vorzeichen?), nicht gesetzt; vorwärts und in der Prüfzeit bestätigt |

➤ So bleibt die OPTIMUM-Regel (*nicht kaufen, was schon gelaufen ist*)
erhalten, ohne eine bestätigte, frühe Bewegung zu blockieren.

---

## 6. ✔ ERGEBNIS Gruppe voll und Teilung (28.09.2026) — Befunde 2.671, 2.673

| | Ergebnis |
|---|---|
| **Auflösung** (Positivkontrolle, gültige Fassung) | Beiträge je Asset: **±0,02** (unverzerrt), ±0,04 (bestand) · Marktmerkmale: gröber als **0,04** |
| **trägt** | **ema_abstand_atr selbstbezogen** — 3 von 4 Mengen, monoton (−0,04 … +0,055), asset-eigen (Tag/Phase 2,6–3,3), Lage vorher (Altersachse 94–130 %) |
| **A4 bestätigt/gelaufen** | obere Randstufe: 0–0,5 ATR +0,085…0,090 · 0,5–2 ATR +0,045…0,059 · 2–3 ATR +0,02…0,03 · > 3 ATR kommt nicht vor — **bestätigt bis ~2 ATR** |
| ohne Befund | Käuferanteil (alle Formen), momentum_kurz, rsi (nur im Bestand), bandenge, Premium |
| **Markt-Timing** | funding, Premium: geteilt — _eigen trägt nicht, _markt mit der gemeinsamen Nullwelt nicht nachweisbar (2.673) |
| offen | Terminmarkt-Gruppe (konten_verh, top_konten_verh, taker_verh, oi_aenderung) — nach Teil B |

⛔ Zwei eigene Fehler, beide vor der Deutung gefunden: die erste
Positivkontrolle pflanzte in ein schon starkes Merkmal (wertlos); die
Zeitverschiebung **je Asset** ist für Marktmerkmale die falsche Nullwelt
(z bis 118) — für _markt gilt die **gemeinsame** Verschiebung.

## 7. ✔ ERGEBNIS Terminmarkt-Gruppe (28.09.2026) — Befund 2.674

| | Ergebnis |
|---|---|
| Teil B | 142 Paare, 87.862 Tage, 0 Fehler; P1 ohne Abweichung; Abdeckung der Eingestellten 0 → 83 % |
| **viele Longs, Marktanteil** | über der **gemeinsamen** Nullwelt in **allen 4 Mengen** (z 2,6–4,7 gegen 2,2–2,4); marktweit wenige Longs +0,14…+0,39, viele −0,13…−0,25 — formal nicht tragend (Form −0,10…+0,50) |
| **viele Longs, Asset-Anteil** | oberer Rand −0,09…−0,14 in allen 4 Mengen (z 8,8–15,5), Mitte flach — eine **Sperre je Asset**; bestätigt 2.660 |
| oi_aenderung | trägt in 1–2 von 4 Mengen, nicht monoton, teils begleitend — nicht belastbar |
| taker_verh | ohne Befund |

⚠️⚠️ **Zur Entscheidung:** das Formkriterium (Rangkorrelation über alle
12 Stufen) lässt einseitige Kurven an der flachen Mitte scheitern. Eine
Änderung gilt nur **für die nächste Messung**, nie rückwirkend.

---

## 8. ⭐ VORABFESTLEGUNG RANDKRITERIUM (28.09.2026) — committet VOR jeder Randrechnung

**Nutzer:** *„Randkriterium für nächste Messungen ja — falls erforderlich
müssen wir wichtige Messungen erneut durchführen. Wenn du die Ränder sauber
einordnen kannst und die Wirkung nachgewiesen ist, würde ich das so sehen."*
Und: *„wir haben einen Kuchen, den wir vermessen können, mehr gibt es nicht
... 1 Meter bleibt 1 Meter auch nach 10 Messungen."*

➤ Einverstanden — das Risiko liegt nicht im Nachmessen, sondern im **Maßband**,
das man nach dem Ergebnis wählt. Deshalb: festgelegt und committet **vor**
dem ersten Lauf, Grenze über **alle** Ränder, und **2022** als unberührte
Bestätigung.

| | Festlegung |
|---|---|
| **Rand** | oben = Stufen P90–P99 und > P99, unten = < P1 und P1–P10 |
| **Kennzahl** | Dq des Rands gegen die Phase (Anker-gewichtet) |
| **Nullwelt** | dieselbe wie für die Kurve — je Asset, bei Marktmerkmalen **gemeinsam**; Grenze **Bestes-von-(2 × Kurven)**, zweiseitig, 90. Perzentil |
| **Rand trägt** | jenseits der Grenze (Suche) **und** gleiches Vorzeichen in der Prüfung **und** ≥ 3 von 4 Jahren **und** ≥ 60 % der Assets **und** gleiches Vorzeichen **2022** (Moment-Bezug, von der Kurvenmessung unberührt) |
| **Rolle** | positiv → Einstieg, nur mit Altersachse und A4 *bestätigt*; negativ → Sperre |
| **neu gerechnet** | alle K1-Gruppen (voll, termin; teilung und termin_teilung je `--nur-eigen` und `--nur-markt --gemeinsam`) auf `unverzerrt:1..3` und `bestand` |
| **unverändert** | das Kurvenurteil W10 bleibt daneben stehen — das Randkriterium **ergänzt**, es ersetzt nicht |

**Nutzer 28.09.:** *„ja korrekt — darum muss die Regel dann auch in unseren
Tests und Simulationen funktionieren."*

| Pflicht | Wann |
|---|---|
| **Regeltest Zufall:** Zufallsmerkmale (geglättet wie echte) durch das Randkriterium — es darf fast nie *trägt* melden | direkt nach der Neuberechnung |
| **Regeltest Pflanzung:** ein Randeffekt bekannter Größe in einer wirkungslosen Kopie — ab welcher Größe findet das Kriterium ihn sicher? | direkt nach der Neuberechnung |
| **Simulation (Ebene 3):** ein tragender Rand muss in der Erfolgsrechnung wirken — Signale mit der Regel gehen auf ungesehenen Monaten messbar anders aus als ohne | vor jeder Verwendung im Betrieb |

---

## 9. ✔ ERGEBNIS RANDKRITERIUM (28.09.2026) — Befund 2.675, löst 2.673 und 2.674 ab

24 Läufe (alle Gruppen × 4 Mengen), alle fehlerfrei. **R-R11:** kein
Kurvenurteil hat sich geändert (16 Läufe zeilengleich, in den 8
`_eigen`-Läufen nur z anders — andere Ziehfolge der Nullwelt).

### 9a. Der Regeltest — die Regel funktioniert in unseren Tests

| | je Asset | als Marktreihe (gemeinsame Nullwelt) |
|---|---|---|
| **Zufall** (10 geglättete Merkmale × roh/selbst = 40 Ränder) | **0 von 40** (beide Mengen) | **0 von 40** (beide Mengen) |
| **Pflanzung** gefunden ab | **+0,02** (5 von 5), +0,01 in 1–2 von 5 | erst **~0,08** (3 von 5 bestand, 0 von 5 unverzerrt:1) |
| Streuung Dq Prüfzeit / 2022 | 0,005 / 0,007–0,010 | **0,034–0,038 / 0,035** |
| Versatz der Prüfzeit | **+0,009 / +0,013** | ≈ 0 (im Rauschen) |

⚠️⚠️ **Gegenprüfung, nachträglich — ändert kein Urteil, ordnet ein:** die
Prüfzeit liegt insgesamt über ihrem 12-Monats-Normal. *Gleiches Vorzeichen
in der Prüfung* winkt positive Ränder je Asset damit fast umsonst durch.
Bei Markträndern sind Prüfzeit und 2022 fast ein Münzwurf, und die
Asset-Bedingung sagt dort nichts (alle Assets sehen dieselben Markttage).
Ein Einstieg gilt hier deshalb nur als **unabhängig bestätigt**, wenn Dq
Prüf den Versatz klar übersteigt.

### 9b. W11 gilt auch für die Ränder (vorab festgelegt)

Tag/Phase < 0,5 → geteilt beurteilen. **Überwiegend Markt:** funding
(0,02–0,31), premium (0,08–0,37), konten_verh/top_konten_verh (0,07–0,18)
— ihre Ränder in *voll* und *termin* stehen auf der falschen Nullwelt.
**Asset-eigen:** rsi, momentum_kurz, ema_abstand_atr (2,6–18,5),
oi_aenderung (0,8–0,9).

### 9c. Die Urteile

| Rand | Mengen | Suche | Prüfzeit | 2022 | Einordnung |
|---|---|---|---|---|---|
| **rsi** roh + selbst **oben** | **4/4** | +0,043…+0,057 (z 5,2–9,6) | **+0,038…+0,054** | +0,002…+0,012 | ✔ trägt, bestätigt · A4 bestätigt |
| **momentum_kurz** selbst **oben** (roh 3/4) | **4/4** | +0,029…+0,036 | **+0,022…+0,035** | +0,007…+0,013 | ✔ trägt, bestätigt · A4 bestätigt |
| funding_vortag_**markt** roh **unten** | 4/4 | **+0,10…+0,14** (z 4,1–6,3) | +0,024…+0,032 | +0,031…+0,040 | ⚠ nur in der Suche nachgewiesen |
| konten_verh_**markt** roh unten | 3/4 | +0,09…+0,11 | +0,026…+0,028 | +0,06…+0,07 | ⚠ nur in der Suche |
| oi_aenderung unten | 3/4 | +0,033…+0,036 | +0,011…+0,015 = Versatz | +0,01 | ⚠ ohne unabhängige Bestätigung |
| ema_abstand_atr selbst oben | 0/4 | +0,051…+0,054 | +0,050…+0,063 | **−0,014…−0,020** | ⛔ kehrt 2022 — Vorbehalt *jedes Regime* |
| viele Longs **je Asset** (konten_verh_eigen oben) | 0/4 | −0,044…−0,052 | +0,004…+0,026 = Versatz | −0,017…−0,030 | ⛔ in der Prüfzeit nicht zu sehen (löst 2.674 ab) |
| viele Longs Markt oben | 0/4 | — | — | — | ⛔ gegen die gemeinsame Nullwelt z −0,3…−1,3 |
| Premium (markt, eigen) | ≤ 2/4 | | | | ⛔ sporadisch |
| Käuferanteil, taker_verh, bandenge | ≤ 1/4 | | | | ohne Befund |

⚠️⚠️ **Altersachse ungeklärt — in allen vier Mengen gleich, bei rsi,
momentum UND ema_abstand:** der obere Rand trägt mit dem **aktuellen**
Wert (+0,03…+0,06) und mit dem **24 h alten** (+0,07…+0,15), der **6 h
alte** dagegen fast nicht (−0,025…+0,033). Die Vorabfestlegung verlangt
für die Rolle *Einstieg* eine bestätigte Altersachse → **die Rolle ist
offen**, bis das geklärt ist.

⚠️ momentum korreliert mit rsi und ema_abstand (Rang +0,56…+0,62): das
ist **eine** Information *oben gestreckt*, nicht drei — in K1 Schritt 2
gemeinsam zu schätzen.

### 9d. Was daraus folgt

| | |
|---|---|
| für K1 Schritt 2 | je Asset *oben gestreckt* (rsi/momentum/ema_abstand gemeinsam), als Kontext-Kandidat funding_markt unten |
| vorher | die Altersachse klären — warum trägt der 6 h alte Wert nicht? |
| ⛔ nicht | eine Sperre *viele Longs je Asset* — in der ungesehenen Zeit nicht vorhanden |
| vor jedem Betrieb | Simulation Ebene 3 |
