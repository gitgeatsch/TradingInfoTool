# Fachliche Entscheidungen im Hebelneubau

**Ab 27.09.2026.** Nutzervorgabe: *„ich kann diese Unterscheidungen nicht
mehr treffen — du musst hier fachlich und technisch korrekt vorgehen."*

> Dieses Blatt hält **jede fachliche Entscheidung** fest, die ich selbst
> treffe, mit Begründung und Datum. Es ist die Gegenleistung für das
> Vertrauen: nichts wird stillschweigend festgelegt.

---

## Die Grenze

| Ich entscheide | Der Nutzer entscheidet |
|---|---|
| Zielgröße, Messform, Nullwelt, Prüfungen | **Risikoappetit** — Hebel 2–5×, Risikobudget `r_min`/`r_max` |
| Reihenfolge der Messungen | **welche Assets** gehandelt werden |
| was gebaut wird und wie | **Produktivgang** |
| welcher Befund gilt und welcher fällt | **wann Schluss ist** |

⚠️ Wenn eine Frage in beide Spalten passt, lege ich sie vor — aber mit
einer **Empfehlung**, nicht als offene Wahl.

---

# E-1 · Die Zielgröße der Messung ist `E[R]`

**27.09.2026** · Messung: `messe_zielgroesse_vergleich.py`

| Zielgröße | Effekt (Cohens d) |
|---|---|
| **`E[R]` (CRV 1,5)** | **+0,402** |
| symmetrische Barriere ±1 ATR | +0,264 |
| MAE allein | +0,264 |
| MFE/MAE | +0,168 |

**Entscheidung:** `E[R]` — sie ordnet **138 % schärfer** als MFE/MAE.

**Begründung:** `E[R]` unterscheidet **drei Ausgänge** (Ziel, Stop, offen)
und bewertet den offenen Fall mit dem Zwischenstand. MFE/MAE wirft diese
Information weg. Das deckt sich mit **2.586**.

⚠️ **Was ich dabei korrigiere:** Ich hatte MFE/MAE empfohlen, weil sie
regelfrei ist. Das war ein Umweg — die Regelfreiheit nützt nichts, wenn
die Größe schlechter ordnet.

⚠️ **Der Preis, ausgewiesen statt versteckt:** `E[R]` enthält das CRV 1,5
als Regelparameter. Es wird in jeder Messung mitgenannt.

---

# E-2 · `E[R]` ist als **Zielgröße** erlaubt, als **Bewertungseingang** nicht

**27.09.2026** · Präzisierung zu 2.641

Ich hatte in 2.641 „kein Ertrag in der Bewertung" geschrieben und daraus
geschlossen, auch die **Messung** dürfe `E[R]` nicht verwenden. **Das war
zu weit gegriffen.**

| Ebene | `E[R]` |
|---|---|
| **B — Erfolgsmessung** („trägt dieses Merkmal?") | ✔ **erlaubt, und die beste Wahl** |
| **A — Bewertung** (im Betrieb, „wie gut ist diese Lage?") | ⛔ **verboten** |

**Der verbotene Fall war die Rückwärtsoptimierung** — eine Schwelle aus
der Kelly-Nullstelle ableiten (2.632/2.640, abgelöst). Nicht die
Zielgröße einer Messung.

---

# E-3 · Der Riegel sperrt alte **Messwerte**, nicht die **Rohgrößen**

**27.09.2026** · Nutzerpräzisierung: *„die alten — damit meinte ich die
Ergebnisse und Messungen der alten Regelwerke VOR dem Umbau. Spot und
Hebel war vorher ein Ablauf; Hebel ist nun ganz anders gebaut, mit
teilweise **denselben Beiträgen**."*

| gesperrt | frei |
|---|---|
| `funding_fuenftel`, `turnover_fuenftel` als **registrierte Beitragsstufen** (gemessen auf H20 / `bewegung_r`) | `funding`, `oi_aenderung`, `taker_verh` … als **Rohgrößen**, neu zu messen auf der Hebel-Lage |
| Kelly und `hebelrechnung` als **Bewertungseingang** | `E[R]` als **Zielgröße der Messung** (E-2) |

⚠️ **Mein erster Riegel war zu scharf** und hätte den Terminmarkt
komplett ausgesperrt — und der Terminmarkt *ist* die Hebelbörse.

---

# E-4 · Das Hebelsystem ist ein **Beitragssystem**

**27.09.2026** · Nutzerwarnung: *„der HEBEL ist ein Beitragssystem und
KEIN Blocksystem."*

⚠️ **Der Neubauplan vom 25.09. schreibt `A ∧ B ∧ ¬C` — „keine Summe,
kein gemeinsames Fünftel". Das ist Block-Logik.** Hier steht Aussage
gegen Aussage.

**Entscheidung:** Die **Nutzervorgabe gewinnt** — gebaut wird ein
Beitragssystem mit Stufen je Fünftel, wie `funding_fuenftel` es
vormacht. `A ∧ B ∧ ¬C` bleibt die **Testform** der Messung (die Rollen
werden getrennt geprüft), nicht die **Bauform** des Systems.

**Begründung:** Ein Blocksystem kann keine Hebelhöhe erzeugen — es sagt
nur ja oder nein. Die Vorgabe *„je besser das Chance-Risiko-Verhältnis,
desto höher der Hebel"* verlangt eine **stetige** Größe. Und
`messe_a_faktoren.py` gibt bereits alle **fünf Fünftelwerte** aus, ist
also auf Beiträge ausgelegt.

---

# E-5 · Rolle A wird nicht neu gebaut

**27.09.2026**

`messe_a_faktoren.py` (26.09.) enthält alle sieben Faktoren bereits:
`rsi_aenderung`, `rsi_umkehr`, `ema_lage`, `ema_steigung`,
`ema_abstand_atr`, `bandenge`, `trendstruktur`.

**Entscheidung:** vorhandenes Werkzeug laufen lassen statt neu bauen.

⚠️ **Es hat keinen Befund** — gebaut, aber nie ausgewertet. Das wird
nachgeholt.

---

# E-6 · Der Horizont für den Hebel ist **24 Stunden**

**27.09.2026** · Befund 2.646 · Nutzervorgabe: *„alte Festlegungen zum
Vergleich ja, aber **dimensionieren und Festlegungen für NEUEN Hebel**"*

⛔ **Der Mangel:** `HORIZONT_JE_LAGE` führte Zahlen **ohne Einheit**. Spot
in Handelstagen (20/90), Hebel mit `3` — gemeint waren 3 Handelstage
= 72 Stunden. **Alle Hebelmessungen laufen auf Stundenkerzen mit H6 und
H24.** `warne_horizont` schlug nie sinnvoll an, weil die Einheit fehlte.

**Entscheidung:** `("hebel","einstieg")` und `("hebel","swing")` auf
**24 Stunden**, und eine eigene Tabelle `HORIZONT_EINHEIT_JE_LAGE`.

**Begründung:** gemessen in 2.642 über sechs Fenster (6–120 h),
Zielgröße MFE/MAE in ATR, Maß Cohens d. Optimum bei H12–H24; d(MAE)
fällt von 0,521 auf 0,264 bei H120. Gewählt ist die obere Kante.

**Die alten Werte bleiben als Vergleich im Quelltext:**

| | |
|---|---|
| 3 Handelstage = **72 h** | Betriebsannahme (2.513) |
| 0,30 Tage = **7,2 h** | reale Median-Haltedauer, 188 Positionen (2.493) |
| H3 = **3 h** | Auflösungsmedian der Messgeometrie (2.591) |

⚠️ **H24 ist das Messfenster, nicht die Haltedauer.** Die
Positionsführung darf weiter 0–5 Tage laufen.

---

# E-7 · Die A-Faktoren tragen nicht — der Neubau braucht etwas anderes

**27.09.2026** · Befund 2.645

Einzeln: kein Merkmal von null zu trennen (Effekt 10–60× kleiner als der
Tagesfehler). In Kombination: das Band war um **Faktor 1,9 zu lax**; mit
Bestes-von-32 halten 2 von 6, beide mit `E[R]` ≈ 0. Zeitstabil ist
**keine** (höchstens 3 von 5 Jahren).

⭐ **Was bleibt:** 20 Treffer bei 64 Versuchen gegen 6,4 erwartete
(p < 0,0001) — **Signal ist da, aber nicht in einzelnen Zellen
isolierbar**.

**Entscheidung:** Rolle A gilt mit den vorhandenen Merkmalen als
**nicht lösbar**. Was als Nächstes zu prüfen ist, lege ich dem Nutzer
vor — es ist eine Richtungsfrage, keine Messfrage.
