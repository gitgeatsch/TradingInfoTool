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
