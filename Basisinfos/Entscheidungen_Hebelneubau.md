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

---

# E-8 · Spot im Umbau — was gilt, und mehr nicht

**27.09.2026** · Nutzervorgaben wörtlich, in zwei Nachrichten:

> *„Spot Quellen sind nicht irrelevant für sich, sondern diese wurden für
> H20 optimiert und vermessen – d.h. nur die Anwendung ist auf Hebel zu
> dimensionieren – kurzer intensiver Handel. […] Auch Spot muss später
> neu gebaut werden, wenn Hebel in der ganzen Ablaufkette funktioniert.
> Ein Detail: die Prüfung für Spot und Hebel soll weiterhin gleichzeitig
> erfolgen (aber zwei unterschiedliche Prüfungen, ein Gewinner) – mehr
> gibt es zu Spot im ganzen Umbau nicht zu sagen."*
>
> *„Wichtige Korrektur: Spot in der heutigen Form ist für Hebel tot."*

| | gilt |
|---|---|
| **Spot-Quellen** | **nicht irrelevant** — für H20 optimiert und vermessen. Nur die **Anwendung** wird auf den Hebel dimensioniert (kurzer, intensiver Handel) |
| **Spot in der heutigen Form** (Code und Produktion) | für den Hebel **tot** |
| **Spot später** | wird selbst **neu gebaut**, wenn der Hebel in der ganzen Ablaufkette funktioniert |
| **Prüfzeitpunkt** | Spot und Hebel werden **gleichzeitig** geprüft — **zwei unterschiedliche Prüfungen, ein Gewinner** |

⚠️ **Das korrigiert einen Satz im Hauptplan:** *„`funding` und `turnover`
… Spot-Quellen, hier irrelevant"*. Irrelevant sind die Spot-**Messwerte**
(Riegel, E-3), nicht die **Quellen**.

⚠️ **Folge für das Standblatt:** `BEITRAGSLAGE` führt je Merkmal die
Spot-Vermessung als Information (`spot`) und fragt beim Betrieb nach der
**Quelle**, nicht nach dem heutigen Sammler — Nutzerhinweis 27.09.:
*„der aktuelle Betriebscode ist veraltet."* (2.652-beitragslage-nachgezogen)

---

# E-9 · Die Karenz ist eine Achse — Regelwerk und Code ziehen nach

**27.09.2026** · Nutzerentscheidung E1/E2 der Voranalyse zur Beitragslage.

Die Achsenregel stand seit 2.650 fest (Nutzereinwand: *„bin mir nicht
sicher, ob du dies nur für die Messung als Annahme siehst oder wir gute
Signale kappen"*). Das Regelwerk (§ 2) und `REGELWERK` im Code führten
trotzdem weiter einen **Filter** („muss mindestens 3 Stunden Karenz
überleben").

**Entscheidung:** Bewertung 1 gilt bei **k = 0** (Betriebsfall). Der
**Vorlauf** (k > 0) ist ein **eigenes Feld** je Merkmal — er zeigt das
Optimum („Lage **vor** der Bewegung"), ohne einen Träger beim
sofortigen Einstieg zu kappen.

---

# E-10 · Marktmerkmale gegen die GEMEINSAME Nullwelt — und W11 auch für die Ränder

**28.09.2026** · fachliche Entscheidung, gemessen begründet (2.673, 2.675).

**Anlass:** gegen die Zeitverschiebung **je Asset** kam der Marktanteil von
funding mit z 40 bis 118 heraus. Die Verschiebung je Asset zerstört die
**Gleichzeitigkeit** — alle Assets sehen am selben Tag dieselbe
Marktlage, und genau die trägt das Merkmal. Die Nullwelt war damit zu eng,
nicht das Merkmal zu stark.

**Entscheidung:**

| | |
|---|---|
| Merkmal **je Asset** (Tag/Phase ≥ 0,5) | Zeitverschiebung je Asset |
| **Marktmerkmal** (`_markt`, zur selben Stunde für alle gleich) | **gemeinsame** Verschiebung — derselbe Versatz für alle Assets (die K3-Methode) |
| Merkmal mit Tag/Phase **< 0,5** | nach W11 geteilt — und zwar für die **Kurve und für die Ränder**. Die Ränder in *voll* und *termin* (funding, premium, konten_verh, top_konten_verh) zählen nicht; es gelten die `_markt`- und `_eigen`-Läufe |

⚠️ **Was daraus folgt:** Marktmerkmale haben nur so viele unabhängige
Fälle, wie es **Markttage** gibt. Ihre Auflösung ist grob (~0,08 am Rand,
Regeltest 2.675) — ein Marktsignal ist nur nachweisbar, **weil** es groß
ist. Die Asset-Bedingung (≥ 60 % der Assets) sagt bei ihnen nichts.

---

# E-11 · Eine Bestätigung zählt gegen den VERSATZ, nicht gegen null

**28.09.2026** · fachliche Entscheidung aus dem Regeltest (2.675).
⚠️ Sie **ändert kein vorab festgelegtes Urteil** — sie ordnet es ein.

**Anlass:** Zufallsränder haben in der Prüfzeit ein Dq von **+0,009**
(unverzerrt:1, 37 von 40 positiv) bzw. **+0,013** (bestand, 40 von 40),
Streuung 0,005. Die Prüfzeit liegt insgesamt über ihrem 12-Monats-Normal.
*Gleiches Vorzeichen in der Prüfung* ist damit für einen **positiven**
Rand fast umsonst zu haben — und für eine **Sperre** schwerer.
Bei Markträndern streuen Prüfzeit und 2022 mit 0,034 bis 0,038.

**Entscheidung:** ein Träger heißt **unabhängig bestätigt**, wenn sein Dq
in der Prüfzeit den Versatz der Zufallsränder **klar** übersteigt (je
Asset um ein Mehrfaches der Streuung 0,005; am Markt gemessen an 0,035).
Sonst: *trägt nach der Regel, ohne unabhängige Bestätigung*. So steht es
bei oi_aenderung, funding_markt und konten_verh_markt.

➤ **In die nächste Vorabfestlegung** gehört das als Bedingung, nicht als
Nachtrag: der Versatz wird im selben Lauf mitgerechnet (Zufallsmerkmale
laufen mit), die Prüfzeit-Bedingung lautet *über dem Versatz*.