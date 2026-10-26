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

---

# E-12 · K7 zählt am BUCH je Symbol, nicht an den Importer-Positionen

**28.09.2026** · fachliche Entscheidung beim Bau von K7 (2.679).
⚠️ Sie **ändert kein Kriterium** (J5/J6) — sie korrigiert die Zähleinheit.

**Anlass:** 278 von 315 Schlussbuchungen sind Teilschließungen; der Importer schließt bei jeder ab. Nur 15 von 188 Positionen zahlen den summierten Kredit zurück. Das Buch je Symbol geht dagegen auf (Menge und Kredit exakt auf 0, 37 Abschnitte).

**Entscheidung:** Einheit ist der Abschnitt des Buchs (Kredit von 0 bis 0); er endet, sobald der Kredit unter 1 € fällt (Staubreste zählen sonst als Unterdeckung). Der Lauf auf den Importer-Positionen bleibt als ungültiger Beleg liegen.

---

# E-13 · Die Wahrheit über Liquidationen kommt aus der GEBÜHR, gerechnet mit dem Alter der Posten

**28.09.2026** · fachliche Entscheidung aus R1 der K7-Voranalyse; der Nutzer erinnert sich nicht.

**Anlass:** Mit dem Alter der Posten trifft das Gebührenmodell 0,30 + 0,18 × Tage die Teilschließungen auf −0,01 Punkte; sieben Schlüsse liegen bei +0,97 bis +1,05 (1-%-Zwangsgebühr), alle übrigen bei höchstens +0,01. Die Gebühr hängt nicht an den Kursreihen, die K7 vergleicht.

**Entscheidung:** K7 rechnet **beide** Fassungen — vorab (4 geführte) und korrigiert (7 aus der Gebühr) — und weist beide aus. Das Urteil (J6) ist in beiden gleich.

---

# E-14 · J10 nimmt die STUNDEN des 10./11.10.2025 heraus, nicht ganze Abschnitte

**28.09.2026** · Korrektur der eigenen ersten Umsetzung.

**Entscheidung:** Ein Crash-Fall **endet** am 10./11.10.; in der Ansicht *ohne* fallen diese Abschnitte weg und bei allen anderen die Stunden dieser zwei Tage. Die erste Fassung hatte TAO/87 und SUI/54 (begonnen am 10.10. abends, liquidiert am 22.10. und 03.11.) als Crash gezählt.

---

# E-15 · Markpreis: ein Monat mit mehr als 1 % Abstand zum Spot ist ein anderes Instrument

**28.09.2026** · Datenentscheidung beim Laden (H9).

**Anlass:** Unter Vorgängernamen läuft im Archiv ein anderer Kontrakt weiter (A←EOS, KAIA←KLAY, S←FTM, RENDER←RNDR, POL←MATIC). Die Monatsmediane |Markpreis/Spot − 1| haben eine Lücke zwischen 0,53 % und 1,15 %.

**Entscheidung:** Grenze 1 % je Monat, gesperrte Monate zählen als fehlend (`hole_markpreis.py --sperre`). Im Markpreis-Modus von K6 kommen Einstieg und Tief aus **derselben** Reihe.

---

# E-16 · Die Rollen wirken auf verschiedene Ausgaben — keine Gewichte auf das Signal

**29.09.2026** · fachliche Prüfung auf Nutzerauftrag (*du musst prüfen und gegenprüfen, ob der Vorschlag halten kann*).

**Befund:** B (Bewegungserwartung) ist richtungslos (2.655: Spiegel 1,02–1,07; vola fällt als Richtung) und vergrößert Anstieg **und** Rückgang (2.655/2.662), in ATR kaum (2.667). C (ema_abstand) setzt sich nach oben fort (2.655), aber mit größerem Rückgang (2.642).

**Entscheidung:** A entscheidet **ob** (Signal), B **wie weit** (Potential, Geometrie), C mit der ATR **wie viel Hebel** (Bewertung 2). Umgesetzt im bestehenden `ROLLEN`/`KANDIDATEN`.

---

# E-17 · *Losfahren aus dem Stand* zuerst — die früheren Messungen waren verdeckt

**29.09.2026** · Korrektur meiner eigenen Empfehlung (*zurückstellen*), auf Nutzerfrage.

**Begründung:** 2.650/2.657/2.665 liefen über alle Anker, auch die fahrenden; rsi verdeckt die Lage (2.682/2.683). Vor der Messung R-R11 auf 2.665 und 2.657.

---

# E-18 · Der Sweet Spot wird als KURVE über den bisherigen Anstieg gemessen

**29.09.2026** · Nutzeranalogie *0 auf 20* fachlich eingeordnet: Stand, Anfahren, Fahrt; die Achse ist der bisherige Anstieg in eigener ATR (A4) — als Kurve, keine vorgegebene Schwelle.

---

# E-19 · PBO nur bei angeglichenem Auswahlanteil

**29.09.2026** · eigener Fehler in F3 der K5-Folge: die Varianten hatten verschiedene Anteile; die PBO-Werte (0,03–0,64) sind nicht auswertbar. Jede künftige PBO-Rechnung wählt je Variante denselben Anteil.


---

# E-20 · Beitrag, Kontext, Gewicht, Sperre — prüfbare Begriffe

**29.09.2026** · Nutzer *„präziser werden … mehrere Messungen, um das zu belegen"*, P1–P8 abgestimmt. **Beitrag** je Asset verschieden · **Kontext** für alle gleich, verschiebt alle Anker · **Gewicht** verändert, wie viel ein Beitrag wert ist (Zuwachs im selben Zustand) · **Sperre** nur bei Umkehr. Der Wirkort (A / C / D) wird gemessen.

---

# E-21 · Urteil ab 2024, 2022 nur Gegenprobe

**29.09.2026** · Nutzer *„der Markt hat sich seit 2021 massiv geändert … Fokus ab 2023 bzw. 2024"*. Fallzahl wird **nie** mit alten Jahren aufgefüllt; 2022 prüft nur, ob eine Regel dort **kippt**.

---

# E-22 · Das Wetter bleibt Auskunft (Abbruchregel)

**29.09.2026** · W2 (2.686): als Gewicht ab 2024 nicht nachweisbar (+0,029, Nullwelt P90 +0,112). Nach der vorab festgelegten Abbruchregel die letzte Wettermessung (Nutzer: *keine Messungen ohne Nutzen*).

---

# E-23 · Die Schwelle gehört auf die Summe — Kern zuerst

**29.09.2026** · Nutzer: *„wie können wir das festlegen, ohne die LAGE der ANDEREN Beiträge zu kennen?"* K5 ist zurückgestellt, bis die Summe steht. Stattdessen der **Kern** (Bewertung 1 = rsi, Bewertung 2 = ATR) Ende zu Ende als Test: Schritt 1 Bestätigung (2.688), Schritt 2 H0 (2.689), Schritt 3 Simulation.

---

# E-24 · Zahlen werden gemessen, nicht gewählt

**29.09.2026** · Nutzer: *„deine Wahl ist wie immer keine Wahl"*. Schwellen und Parameter per **vorab festgelegter Regel** auf dem Wahlzeitraum, **einmal** auf ungesehener Zeit bestätigt (so s = +0,035). Der Nutzer entscheidet nur Ziel, Risikobereitschaft (Veto) und Betrieb.

---

# E-25 · Fällt ein Schritt: Lösung, nicht *widerlegt*

**29.09.2026** · Nutzer: *„an der Messung herumschrauben NEIN — aber Fehler oder eine Aussage zum Ergebnis und mögliche Lösungen JA, MUSS."* Fehler prüfen, Annahmen **messen**, Aussage zum Ergebnis, Lösung als neue Vorabfestlegung.

---

# E-26 · Chance und Risiko im selben Fenster — das Fenster ist eine Achse

**29.09.2026** · Nutzer: *„Hebel ist kurz, schnell, hoch — hier entscheiden Stunden … es geht um das ZEITFENSTER."* H0 über 6 / 12 / 24 h (2.689). Befund: der Kern ist ein **Tageshandel** (+5 % im Median nach 19–20 h) — Haltedauer und Ziel werden in Schritt 3 gemessen.

---

# E-27 · Die Liquidationsgrenze wird in der Simulation gemessen (Vorschlag)

**29.09.2026** · Nutzer: *„ich stelle das Risiko über den Hebel ein … ich hoffe, das ergibt sich aus der Messung für Schritt 3."* Vorschlag für die Voranalyse Schritt 3: jede Grenze (0,5 / 1 / 2 / 5 %) simulieren, gewählt nach vorab festgelegter Regel (größtes Kontowachstum nach Kosten, bei Gleichstand die vorsichtigere); das Risikomodell bleibt nur aus der Liquidation kalibriert; Nutzer-Veto möglich.


---

# E-28 · Bewertung 1 = Ereignis + Potential-Summe; die Chance ist Auskunft, der Spiegel ist Pflicht

**30.09.2026** · Nutzer-Ja zu L4 Q1 (`Voranalyse_L4_Summe_30_09.md`).
- **Warum:** Die Glieder, die tragen (ema_abstand_atr, volumenschub, Ruhe 48 h), heben das **Potential** und nicht die Chance (2.692). Auf der Chance summiert fielen sie heraus.
- **Die Form:** Der Kern bleibt das **Ereignis** (*ob*), die **Summe** misst das erwartete Potential (*wie weit*, Rolle B), und die Schwelle wird per Regel gemessen.
- **Die Absicherung:** das Regelwerk 2.657/2.662, *mehr Potential ist oft nur mehr Bewegung*. Das Potential zählt nur, wenn der **Spiegel** hält: Das Ereignis oben muss stärker zunehmen als das Ereignis unten (L4-5, vor der Rechnung festgelegt).


**Nachtrag 30.09. (2.693):** Die Bedingung ist **nicht erfüllt**. Der Spiegel fällt in 4 von 4 Mengen. E-28 greift damit **nicht**,
und Bewertung 1 bleibt **Ereignis (Kern + Ruhe 48 h) + Chance**. Die Potential-Glieder (Wucht) sind Rolle B und gehen in die
Positionsführung und die Hebelstufe. Es ist keine neue Entscheidung nötig: E-28 hatte diese Bedingung von Anfang an.


---

# E-29 · Spiegelprobe ist Pflicht bei jedem Potential- oder Bewegungsmaß

**30.09.2026** · Aus 2.693. Die Wucht hob das Potential in 4/4 Mengen, und erst der Spiegel (+5 % binnen 24 h gegen −5 % binnen
24 h) zeigte, dass es **mehr Bewegung in beide Richtungen** ist. Das Maß *Rückgang vor dem Hoch* sieht den Rückgang nach dem Hoch
nicht. ➤ Ab jetzt läuft der Spiegel bei jeder Messung mit, die Potential, MFE oder eine Bewegungsgröße hebt, als **Urteilsbedingung**.

---

# E-30 · Urteil auf den unverzerrten Mengen; bestand ist Auskunft, wenn die Mengen auseinanderlaufen

**30.09.2026** · Aus 2.694. Nur bestand gewann (×1,23), die drei unverzerrten Mengen verloren (×0,63..×0,68). Der Rohvorteil liegt in
bestand fast doppelt so hoch, weil dort die **eingestellten** Paare fehlen (2.668/2.669). ➤ Die Regel ≥ 3/4 bleibt. Laufen bestand
und unverzerrt auseinander, gilt das Urteil der **unverzerrten** Mengen, und bestand wird als überlebensverzerrt ausgewiesen.

---

# E-31 · Untere Grenzen in v̂ gelten nur in der Menge, auf der sie gemessen sind

**30.09.2026** · Aus 2.695. Der Vorsprung v̂ kommt je Menge aus eigenen rollierenden Modellen und eigenem geschrumpftem Normal. Die
Kanten der *Tiefe davor* aus bestand 2024 trennten in unverzerrt:1 **335 gegen 5.326** Einstiege. ➤ Kandidaten, die aus v̂
abgeleitet sind, bekommen Kanten **je Menge** (auf deren 2024) oder werden nur in bestand beurteilt. Die Kern-Schwelle s ist kaum
berührt (Einstiege je Menge 10.534–11.844). Für den Betrieb heißt das: dieselbe Grundgesamtheit wie in der Messung.

---

# E-32 · Begriff „Kern-Short“ (Nutzer 30.09.)

**30.09.2026** · Nutzer: *„bitte abgrenzen zur Short-Strategie Krypto, damit keine Verwechslung passiert."* ➤ Der Messarm W3 heißt
ausschließlich **Kern-Short**. Er ist **nicht** die SHORT-Richtung der heutigen Betriebssignale und **nicht** die Absicherung mit
Short-Produkten (`agent/absicherung_fakten.py`). Beide bleiben unberührt. Den Namen *Short-Strategie* verwendet der Neubau nicht.


---

# E-33 · REGEL0 als festgeschriebene Ausgangslage; A und B, nicht C/D/E (Nutzer 30.09.)

**30.09.2026** · Nutzer: *„A und B sind Optionen, die ohnehin sinnvoll sind. C, D, E sehe ich aktuell gar nicht als Option für unseren
Umbau … eine REGEL0 mit allen korrekten Parametern festschreiben und mit allen zur Verfügung stehenden Mitteln das Regelwerk
optimieren und ausreizen."*
- **REGEL0** ist der Nullstand. Jede Optimierung wird gegen REGEL0 gemessen (R-R11: erst reproduzieren).
- Der Entwurf steht in `Basisinfos/REGEL0_Hebel_Entwurf_30_09.md` und wird erst nach Nutzer-Ja festgeschrieben.
- Der Vorwärtstest (M1-2 Teil B) ist zurückgestellt. Die Regel K_IG < 1 bleibt eingefroren, aber ohne laufenden Auftrag.


---

# E-34 · Optionen R und L; Einordnung zur Produktion (Nutzer 30.09. abends)

**30.09.2026** · Nutzer: *„Ja, R und L in den Plan aufnehmen."* Dazu:
- *„Die Konzentrationen sind marktgetrieben … in der Praxis irrelevant. Es wird eine von mir selektierte Assetliste gehebelt. Die Anzahl
  und Auswahl der Signale nehme ich vor."* ➤ Die **Ballung** der Signale und der **Rückgang** des Simulationskontos, das *jedes* Signal
  gleichzeitig handelt, sind **kein** Grund gegen den Einsatz. Das ist eine Eigenschaft der Messanlage und nicht des Betriebs. Mein Punkt 2 aus der
  Einschätzung zur Produktionsreife ist **zurückgenommen**.
- *„Der Beleg kann nur in Produktion erfolgen … aktuell haben wir ein nicht funktionierendes System — wenn dieses durch ein ‚nicht 100
  Prozent optimales' ersetzt wird, ist es ein Erfolg. Das bedeutet nicht, dass es sofort eingesetzt werden soll, aber die
  Rahmenbedingungen lassen es nicht zu, es zu perfektionieren."* ➤ Der Maßstab ist **besser als heute und ehrlich belegt**, nicht perfekt.
- **Messbar nachzuziehen (Vorschlag):** REGEL0 auf der **Hebel-Assetliste des Nutzers** (`asset_hebel_settings`, nur lesend), damit die
  Grundgesamtheit dem Betrieb entspricht.

- **Nachtrag (Nutzer 30.09. spät):** *„Bei 3. zu den Mindestbedingungen reden wir noch einmal, wenn wir zu diesem Schritt kommen. Ich denke,
  wir können und müssen die bestehende Hebel- und Spot-Achse (laut Plan) ersetzen, ein Parallelbetrieb wird schwierig. Nach der
  Assetliste gehen wir nach deinem korrigierten Plan und REGEL0 (auf REGEL1 etc.) vor."* ➤ Der Schattenbetrieb ist **nicht** gesetzt.
  Die Mindestbedingungen werden beim Schritt Betrieb abgestimmt.


---

# E-35 · Labor-only ist FAIL — die Betriebsprüfung gehört in jeden Schritt (Nutzer 30.09.)

**30.09.2026** · Nutzer: *„Wenn wir eine Lösung haben, die nur am Desktop im Labor funktioniert, ist es ein FAIL."*
➤ Eine Regel ist erst dann fertig, wenn sie **am Notebook** mit den dort verfügbaren Daten, derselben Grundgesamtheit und ohne
Handgriff am Desktop dieselben Signale erzeugt. Jede Voranalyse und jede REGELn bekommt die Betriebsprüfung B1–B9
(`Plan_Hebel_fuenf_Phasen_27_09.md` (Abschnitt PLAN UND VORGEHEN AB 30.09.)). Ein monatliches Training am Desktop mit Übergabe von Hand ist ebenfalls FAIL.


---

# E-36 · REGEL0 festgeschrieben (Nutzer 01.10.2026)

**01.10.2026** · Nutzer: *„Ja, REGEL0 festschreiben, prüfen und gegenprüfen."*
- **REGEL0** = Kern (rsi-Ersteintritt s = +0,035, Ruhe 48 h, Einstieg 1 h später, eigenes Normal ab 240 h, J) · Hebel (ATR, Grenze 2 %, Markpreis) · Erfolgsmessung (24 h ohne Ziel und Stop, Bitpanda-Kosten).
- Die Grundlage: 2.688–2.699, der Showstopper Mindesthistorie behoben (2.698), die Schwelle auf der vollständigen Menge bestätigt (2.699).
- Festgeschrieben im Dokument `REGEL0_Hebel_Entwurf_30_09.md` (Dateiname historisch) und im Code `hebel_neubau.REGEL0`. Die Wache prüft die Referenzzahlen gegen die Belege.

**Nachtrag 25.10.2026 (E-141, Prüfbericht):** Die Tagesblock-Bedingung B6 prüfte gegen 0 statt gegen den Versatz (E-11). Gegen das Nullmittel hätten unverzerrt:2 und :3 nicht bestanden (2 von 4). Die REGEL0 war damit schon bei der Festschreibung nicht voll bestätigt; heute ist sie durch E-139 überholt.

---

# E-37 · BTC in die REGEL0 aufgenommen (Nutzer 01.10.2026)

**01.10.2026** · Nutzer: *„Ja, BTC aufnehmen."* Grundlage 2.701: technisch sauber (die übrigen bitgleich), statistisch nicht nachweisbar (~30 Signale je Jahr),
wirtschaftlich unschädlich (Konto um null, keine Liquidation).
- BTC ist **handelbares Asset** der REGEL0, mit dem Vermerk **nicht nachgewiesen, unschädlich**.
- Modell, Marktmitte und ATR-Training bleiben **ohne** BTC (`--mit-btc`). Die REGEL0-Referenz gilt ab jetzt mit BTC (`hebel_neubau.REGEL0`, Belege `Basisinfos/BTC_01_10/`).


---

# E-38 · A abgeschlossen (nicht bestätigt), weiter mit B (Nutzer 01.10.2026)

**01.10.2026** · Nutzer: *„deine Empfehlung – A, dann B, und eigentlich kannst du, wenn es passt, die Ursache für die Verluste behandeln – aber du bist hier der Experte."*
Dazu: *„die Minus-Trades und die Marktphasen sind ohnehin ein eigenes Thema und können nicht vollends durch eine einfache mathematische Rechnung gelöst werden."*
- **A ist abgeschlossen** (2.702, 0/4). Keine weitere Ursachenmessung zu A auf 2025–26. Die REGEL0 bleibt 24 h ohne Stop.
- **Nächster Schritt B** (M1-3 Kern stabilisieren), Entwurf `Voranalyse_B_Kern_stabilisieren_01_10.md`. Die Ursache der Verluste geht als **Auskunft** (Teil 0) hinein, wo sie zu B passt.
- **Marktphasen** (Regime, Verlusthandel im Gegenwind) bleiben ein **eigenes Thema** (R), nicht durch eine einfache Rechnung zu lösen.

---

# E-39 · B vorläufig geschlossen, weiter mit L (Nutzer 01.10.2026)

**01.10.2026** · Nutzer: *„Zu B: ja, vorläufig schließen. Die 2x als max. Hebel ist eigenartig, lassen wir es so stehen. Ja, Voranalyse L."*
- **B** (2.703) ist **vorläufig geschlossen**. F0 bleibt. Das Springen des Signalangebots bleibt eine bekannte Eigenschaft und ist kein Verlusttreiber.
- **Stufe 2x** (nur bei sehr hoher ATR gewählt, in 4/4 Mengen roh negativ, 25–98 Handel): Die Beobachtung bleibt **stehen**, es gibt **keine** Regel daraus.
- **Nächster Schritt L** (Liquidität). Vor dem Entwurf gibt es ein Gespräch über die offenen Grundfragen.


---

# E-40 · Datenbasis: alles halten, was Binance stündlich führt (Nutzer 01.10.2026, O11)

**01.10.2026** · Nutzer: *„Wir benötigen die notwendige Datenbasis … eine Selektion auf bestimmte Assets ist nicht sehr sinnvoll"* ·
*„wir nehmen alles, was es gibt, vor allem, wenn es im Bestand ist"* · *„Ja wie empfohlen"* (Frage 4) · *„AIOZ und XDC nehmen wir aktuell in Kauf"*.
- **Alles halten statt nach Listen nachladen:** alle Krypto-Assets mit Binance-Stundenkursen (Spot oder Futures, je Asset die **längere** Historie), in **eigenen**
  Dateien `data/stundenkurse_alle.db` und `data/markpreis_alle.db`. Die Messbasis bleibt unberührt.
- **Futures nur als Kursquelle**, gehandelt wird bei Bitpanda. Gleichwertigkeit gemessen (2.705).
- **Zuordnung Bitpanda → Binance** in **einer** Tabelle `Basisinfos/symbol_zuordnung.csv` (nur Ausnahmen) mit Preisprüfung. Eine **Kollision** (anderer Coin unter gleichem Kürzel)
  wird **gesperrt** (2.707).
- **Frage 4: bewerten, nicht trainieren** (wie BTC E-37). Das Modell, die Marktmitte und das ATR-Training bleiben bei der Messbasis (116), damit die REGEL0 für alle bisherigen Assets **bitgleich** bleibt.
  Die neuen Assets tragen nachweislich (2.706).
- Die **Lernmenge per Regel** (O12) ist ein eigener, späterer Schritt (Nutzer: *„die müssen wir stabil über die Zeit hinbekommen"*).

# E-41 · Nächster Schritt: Schritt 7, die Betriebsvorbereitung am Notebook (Nutzer 02.10.2026)

**02.10.2026** · Nutzer: *„Ja, 1. wie von dir empfohlen."* Die Alternativen O12 (Lernmenge per Regel) und die umgekehrte Liquidität als Gewicht (2.704) bleiben offen.
- Inhalt: Stundenkurse und Markpreise am Notebook (Historie übertragen, dann laufend nachladen), Monatstraining als Job, R-R11 am Notebook gegen die REGEL0-Belege,
  täglicher Katalog- und Preisabgleich mit Meldung, Mail, Mindestbedingungen (Nutzer: *„reden wir, wenn wir zu diesem Schritt kommen“*).
- Zuerst eine **Voranalyse** zur Abstimmung (Ist-Stand am Notebook, Leser und Schreiber, Risiken). Gebaut wird nach dem Ja.


---

# E-42 · Schritt 7: Umfang, Rollen, Datenübertragung, Betriebsparameter (Nutzer 02.10.2026)

**02.10.2026** · Nutzer: *„Ja, F1 bis F2 wie vorgeschlagen"* · *„rascher Einsatz am NB, würde eine fertige und geprüfte Datei auf das NB per USB kopieren"* ·
*„Dateien sind am NB und korrekt"* · *„Ja, so eintragen, Fortsetzung als REGEL1-Kandidat aufnehmen – die Themen Positionsführung und Ausstieg sind ohnehin im Plan
zu berücksichtigen – nur echte offene Positionen."*
- **F1:** Die REGEL0 ersetzt **nur den Hebel**. Die Rollen-Kette schlägt keinen Hebel mehr vor, ihre Spot-Entscheidungen laufen weiter.
- **F2:** Die REGEL0 **löst aus**, die LLM-Rollen prüfen und kommentieren nur.
- **F3:** Die Historie (vier Datenbanken, 2,7 GB) kam **per USB** ans Notebook, mit SHA-256-Prüfsummen auf beiden Seiten (`pruefe_uebertragung.py`). Laufend lädt ein **eigener Nachlader** im Betrieb.
- **Betriebsparameter der REGEL0** (ohne neue Zahl): Prüfzeitpunkt jede volle Stunde, alle Assets. **Kein eigener Cooldown**, die Ruhe 48 h wirkt je Asset (gemessen mindestens 49 h, Median 6,8 Tage).
- **REGEL1-Kandidaten** (O13): Fortsetzung als Einstiegstyp · Positionsführung und Ausstieg **nur für echte offene Positionen**.
- **F4** (Mindestbedingungen, versionierte Regeln, offene Punkte 4–7) ist noch im Gespräch.


---

# E-43 · Schritt 7, F4 Punkt für Punkt (Nutzer 02.10.2026)

**02.10.2026** · Nutzer: *„Punkte 1 bis 5 müssen wir Schritt für Schritt durchgehen. 1. Ja, aber bei kritischen Punkten ist eine Änderung unter der Woche auch zulässig.
2. Ja, als START in der ersten Phase für M1 der Einstiegskette – die echten und korrekten Ausstiegsmails und Regeln über die Positionsführung müssen nachgelagert korrekt
umgesetzt werden. 3. Hier gibt es schon Deckel und Altbestand, das müssen wir analysieren und festlegen. 4. Ja, aber nicht bei allen Assets, ist zu vernachlässigen.
5. Wieder ein eigener großer Punkt, ich möchte die alte und falsche SPOT-Kette nach dem Hebel ersetzen, und somit kann diese vorerst stillgelegt werden. Du musst nur
einplanen, dass die Einstiege gleichzeitig geprüft werden, aber später eigenständig bewertet werden – je Strategie ein eigener Pfad für die Ablaufkette."*
- **1 Versionierte Regeln:** Live läuft eine festgeschriebene Fassung, gewechselt wird zu festgelegten Zeitpunkten mit Freigabe. **Ausnahme:** Kritische Punkte dürfen auch unter der Woche geändert werden (neue Version, Vermerk).
- **2 Ausstieg (Start M1):** Ausstiegszeit in der Einstiegsmail und eine Erinnerung nach 24 h. Die echten Ausstiegsmails und Regeln zur Positionsführung kommen nachgelagert (O13).
- **3 Positionsgröße:** offen. Bestehende Deckel und Altbestand werden **analysiert**, dann festgelegt.
- **4 Hebelstufen 2/3/5x:** gedeckelt auf das, was das Asset bei Bitpanda erlaubt. Dass nicht jedes Asset alle anbietet, ist vernachlässigbar.
- **5 Spot:** Die alte Spot-Kette wird **nach dem Hebel ersetzt** und kann **vorerst stillgelegt** werden. **Architektur:** gemeinsame stündliche Einstiegsprüfung, **je Strategie ein eigener Bewertungspfad und eine eigene Ablaufkette** (Hebel = REGEL0, Spot später eigene Regel).


---

# E-44 · Positionsgröße der REGEL0: Startwerte, jederzeit anpassbar (Nutzer 02.10.2026)

**02.10.2026** · Nutzer: *„Müssen wir dies final festlegen? Kapitalschutz ist meine Angelegenheit und sollte nicht im Mittelpunkt stehen. Wenn das System funktioniert,
kann man nachschärfen."* · *„Mach einen Vorschlag für je Trade von 300 bis 800 Euro max. Einsatz, für max. 4 Trades gleichzeitig"* · *„Ja, so als Startwerte eintragen …
baue es so, dass dies einfach und flexibel angepasst werden kann bei Bedarf."*
- **Gleicher Positionswert je Trade 1.500 €.** Der Einsatz folgt aus der Hebelstufe der REGEL0: 5x → 300 €, 3x → 500 €, 2x → 750 €, begrenzt auf 300–800 €.
- **Richtwert 4 gleichzeitig, keine Sperre:** Ab dem fünften Trade vermerkt die Mail *Richtwert erreicht*, das Signal kommt trotzdem (gemessen: 41 % der Signale der Hebel-Liste kamen bei schon 4 offenen und waren nicht schlechter).
- Der alte **Gesamtdeckel** (3 % Risiko bis zum Stop) gilt für die REGEL0 nicht (sie hat keinen Stop).
- **Anpassbar** in `Basisinfos/regel0_betrieb.yaml` (bewusst nicht in `config.yaml`, die am Notebook lokal abweicht), Rechnung `agent/regel0_groesse.py`, bewacht von `pruefe_pakete.py --paket Regel0Betrieb` (prüft das Verhalten, nicht die Werte).

# E-45 · S7-2 Betriebsrechnung: Teil 0, Grundgesamtheit, ein Rechenkern, Signalkreis (Nutzer 02.10.2026)

**02.10.2026** · Nutzer: *„Ja F-a bis F-d wie vorgeschlagen, prüfen und gegenprüfen – das Thema Einstiege und Anzahl der Signale müssen wir als eigenen und
längeren Punkt behandeln – aktuell sind es nicht so viele Assets mit Hebelschalter, denke ich. Aber das solltest du über den NB-Export ohnehin feststellen können."*
- **F-a Teil 0:** Die Wirkung des Vorgriffs in der Schrumpfung (B-1) wird **gemessen**, mit der kausalen Fassung K (Vormonat) und der vorab festgelegten Regel aus
  `Voranalyse_Schritt7_Betrieb_02_10.md` §12.3.
- **F-b Grundgesamtheit:** Der Betrieb trainiert auf **bestand** (die 116 der Messbasis), bewertet werden zusätzlich BTC und die Listen. Das gilt bis O12.
- **F-c:** S7-2 und S7-3 sind **ein Rechenkern** (`agent/regel0_rechnung.py`).
- **F-d Signalkreis:** Signale kommen nur für Assets mit **eingeschaltetem Hebel-Schalter**. Bewertet werden alle mit Daten, als Auskunft.
  NB-Export 02.10. 12:42: **25 von 44** Einträgen an (Opt-in, ohne Eintrag = aus).
- **Eigener, längerer Punkt O18:** Einstiege und Signalanzahl. Er wird **nicht** in S7-2 entschieden.
- **Nachtrag 02.10. (Teil 0, 2.708):** Die Regel aus F-a ist in **4 von 4** Mengen erfüllt (3 bitgleich, unverzerrt:3 98,7 %, Betriebsreferenz bitgleich).
  Damit gilt **REGEL0.1** (kausale Schrumpfung aus dem Vormonat) als Fassung für den Betrieb. Das ist **keine neue Nutzerentscheidung**, sondern die Folge der vorab
  festgelegten Regel.

# E-46 · S7-4: die REGEL0 in der Mail, der alte Hebelweg aus (Nutzer 03.10.2026)

**03.10.2026** · Nutzer: *„Ja S7-2b so vorbereiten … aber ich möchte sehr rasch in Produktion damit, am besten sofort"* und *„Ja D1 bis D4 wie vorgeschlagen,
prüfen und gegenprüfen"*.
- **D1 (B-9):** Die Signalmail kommt **sofort** mit der **vorläufigen** Stufe. Weicht die endgültige ab (rund 1,6 %), folgt eine kurze **Korrektur**.
- **D2:** Die Hebelstufen je Asset bei Bitpanda sind noch nicht als Daten da. Die Mail nennt die REGEL0-Stufe mit dem Hinweis, das Bitpanda-Angebot zu prüfen.
- **D3:** **kein** Kommentar der LLM-Rollen in dieser Fassung (F2 kommt in der zweiten).
- **D4:** **Testwoche** bis 10.10. als Vermerk in Betreff und Text (E-43). **O18** behoben: Die Migration der Hebel-Schalter läuft nur einmal, ohne Eintrag gilt *aus*.
- Mit S7-4 gilt F1 vollständig: **Neue Hebel-Einstiege kommen nur noch aus der REGEL0.** Schalter `alter_hebelweg_aus` in `Basisinfos/regel0_betrieb.yaml`.

---

# E-47 · S7-5: neue Listings, Preisabgleich, gesperrte Kürzel (Nutzer 03.10.2026)

**03.10.2026** · Nutzer: *„Ja F-1 bis F-5 wie vorgeschlagen, prüfen und gegenprüfen"* (`Voranalyse_Schritt7_Betrieb_02_10.md` §16).
- **F-1:** S7-5a bis S7-5d werden gebaut. Neu gelistete Binance-Paare kommen am NB **täglich** in `stundenkurse_alle.db`/`markpreis_alle.db`, nie in die Messbasis. Vor jeder Signalmail werden die Kurse von Bitpanda und Binance verglichen, ab 5 % geht keine Mail raus. Gesperrte Kürzel gelten für alle Mengen. Der Teilexport zeigt, was nicht gemailt wurde.
- **F-2:** Ist der Ticker nicht erreichbar, geht die Mail **trotzdem** raus, mit dem Vermerk *Kurs nicht gegengeprüft*.
- **F-3:** Tokenisierte Aktien und Wrapped Token **bleiben** in der Datenbasis, ohne Aufzählungsliste. In der Signalbilanz werden sie getrennt ausgewiesen.
- **F-4:** Die Neuaufnahme läuft täglich, ab 02:00 UTC im Stundenjob, vor dem Nachladen.
- **F-5:** S7-5 kommt ans NB **nach** den Kontrollen K-S7-3/K-S7-4. Am 03.10. ist K-S7-3 bestanden und K-S7-4 fehlerfrei; die erste REGEL0-Mail steht noch aus.
- Gegenprüfung `Basisinfos/Rechenkern_02_10/pruefe_s75.py` 15/15. Wache `--paket Regel0Betrieb` 26/26.

---

# E-48 · Stop-Nachzieh-Sammelmail: Spot-Positionsführung, bleibt an, kein Doppelversand (Nutzer 03.10.2026)

**03.10.2026** · Nutzer: *„ok zu SN1 bis 4 — Abschalten nicht zwingend notwendig, da geringe Anzahl an Mails kommt, und dann vergisst man den Punkt nicht"* (`Voranalyse_Schritt7_Betrieb_02_10.md` §18).
- Die Mail betrifft heute **nur den Spot-Bestand** (67 von 67 Empfehlungen Spot LONG, keine Hebel). Sie wird unter **O14 Spot-Positionsführung** neu entworfen: je Position, nur echter Bestand, Regel nach heutigem Standard.
- Sie bleibt bis dahin **an** und wird nicht verdichtet.
- Der **doppelte Versand** an Neustart-Tagen ist behoben: Nachgeholt wird nur, wenn die Uhrzeit heute schon vorbei ist (`nachholen_jetzt`).

---

# E-49 · Der Hebel-Tab zeigt die REGEL0 (Nutzer 03.10.2026)

**03.10.2026** · Nutzer: *„In der GUI gibt es einen Hebel-Tab, diesen sollte man wiederverwenden, wenn möglich"* und *„Ja H-1 bis H-4 wie vorgeschlagen, prüfen und gegenprüfen"* (`Voranalyse_Schritt7_Betrieb_02_10.md` §17).
- **H-1:** Die REGEL0-Signale kommen in **dieselbe** Liste (These *REGEL0 24 h*). Das Detail ist derselbe Text wie die Mail, dazu der Mailstand. Die Ablage wird nur gelesen.
- **H-2:** *Jetzt analysieren* ist **gesperrt**, solange der alte Hebelweg aus ist, sonst entstünde von Hand ein Parallelbetrieb (F1).
- **H-3:** Bei offenen Positionen steht der REGEL0-Vermerk mit Ausstiegszeit. Das ist eine Brücke bis O13.
- **H-4:** Der Tab geht mit dem nächsten Pull ans NB. Die Oberfläche berührt weder die Rechnung noch die Mails.
- Gegenprüfung `pruefe_h17.py` 23/23. Wache `--paket Regel0Betrieb` 33/33.

---

# E-50 · Die LLM-Ebene der REGEL0 wird NEU gebaut (Nutzer 03.10.2026)

**03.10.2026** · Nutzer: *„Lege den LLM Block so an, dass wir diesen analog zur deterministischen Komponente neu konstruieren und die alte ab sofort vollständig ersetzen"* und *„sofortiger Umbau, testen, analysieren und simulieren - dann in Produktion mit eMail und Charts. Diesen Bereich können wir nicht so einfach bauen wie die REGEL0: 1. zuerst prüfen, welche Informationen jede Rolle erhalten soll, um einen sinnvollen Beitrag zu liefern, 2. wie soll dies in den Prompt - hier gab es bereits Erkenntnisse aus dem 1. Bau, 3. weitere tragende Beiträge werden nachgelagert eingebaut. Spot kann vorerst so bleiben, wenn es einfacher ist - ich brauche diesen nicht."*
- Die LLM-Ebene der REGEL0 wird **neu gebaut**. Übernommen werden die Befunde des ersten Baus, nicht der Prompt-Code. Sie löst §19 L-a bis L-f ab.
- Reihenfolge:
  1. Information je Rolle.
  2. Prompt aus den Erkenntnissen des ersten Baus.
  3. Bau im Schatten, testen und simulieren: Rückspiel mit anonymer Eingabe samt Kontaminationsprobe, gegen eine Regel auf denselben Eingaben und gegen den Zufall.
  4. Produktion mit Mail und Charts.
  5. Weitere tragende Beiträge nachgelagert, etwa Text.
- **Spot bleibt** auf der alten Rollen-Kette, bis O14 sie ablöst. Der Nutzer braucht ihn nicht.

---

# E-51 · Das Rollenmodell M3 als Startfassung des LLM-Neubaus (Nutzer 03.10.2026)

**03.10.2026** · Nutzer: *„Ja N-a bis N-h wie vorgeschlagen"*, *„Ja R-1 bis R-4 wie vorgeschlagen, prüfen und gegenprüfen. Wichtig: Das Rollenmodell soll beim Testen und Simulieren u. U. noch einmal geprüft und angepasst werden können"* (`Voranalyse_Schritt7_Betrieb_02_10.md` §20, §20.10, §20.11).
- **N-a bis N-h:**
  - Nur Information, die live für alle REGEL0-Assets und für 2025–26 in derselben Form vorliegt. Das sind Umfeld und Kurs-/Volumenstruktur.
  - Aus der REGEL0 bekommen die Rollen nur den geplanten Handel, nicht deren Bewertung.
  - Rückspiel mit Kontaminationsprobe und Vergleichsarmen.
  - Der Mail-Block geht in jedem Fall mit Messstand in die Produktion. Die Charts kommen sofort.
  - P-T (Text) und Funding nachgelagert, Modell gemini-3.5-flash-lite.
- **R-1:** Rollenmodell **M3**.
  - Markt und Trader unabhängig voneinander.
  - Der LLM-Entscheider gibt das **Gesamturteil** über den REGEL0-Handel aus den Ergebnissen der beiden. Er kippt nichts.
  - Der Gegenprüfer mit Fremdquellen kommt nachgelagert.
- **R-2:** Der Markt wird nur bei geänderten Fakten neu gefragt.
- **R-3:** Rückspiel mit fest n = 1.000 je Rolle, ohne Aufstocken.
- **R-4:** Die Spot-Kette wird vor dem Rückspiel mit einem **eigenen** Schalter angehalten, nicht über `aktiv_fuer`. Ich gebe vorher Bescheid.
- **M3 ist eine Startfassung.**
  - Das Modell steht als Rollenkatalog in einer Konfigurationsdatei, Anpassen ist eine neue Fassung.
  - Die Einstiege werden vorab in eine **Entwicklungsmenge** und eine **unberührte Bestätigungsmenge** geteilt.
  - Prüfpunkte P1 bis P4 mit vorab festgelegten Folgen. Eine Änderung am Rollenmodell selbst entscheidet der Nutzer.

---

# E-52 · Sofortfassung des LLM-Blocks geht vor der Messung in die Produktion (Nutzer 03.10.2026)

**03.10.2026** · Nutzer: *„Ok, Charts und N1 bauen, prüfen und gegenprüfen. Zur Dauer: Hier brauchen wir eine Sofortlösung (Simulation etc.), mit dieser gehen wir in die Produktion, und die adaptierte und gemessene Lösung muss später final kommen."* Nachgereicht: *„optimal wäre dann ein selbstjustierendes System."*
- Die **Sofortfassung** (Rollenmodell M3, Fassung `0.1-sofort`) geht nach dem Bau (N1, N2) und einem **Kalibrierlauf mit Simulation** in die Mail. Der Kalibrierlauf prüft P1: Antworten formgültig, Stufenverteilung, Wiederholung, Anonymität, Ende zu Ende in der gerenderten Mail.
- In der Mail steht sie ausdrücklich als **Sofortfassung, ungemessen**.
- Die **gemessene Fassung** ersetzt sie später, nach Rückspiel (N4) und Bestätigung (P3).
- Die **Charts** kommen sofort.
- *Selbstjustierend:* als Planpunkt aufgenommen (O21), zur fachlichen Prüfung. Siehe dort.

# E-53 · Fassung 0.1e: Trader mit fünf Stimmen, Entscheider ausgesetzt, Block in der Mail (Nutzer 04.10.2026)

**04.10.2026** · Nutzer: *„Ja, nur für die aktuelle Messung und Bewertung. Halte im Plan fest, dass die LLM-Stufen und der Entscheider erneut fachlich und technisch geprüft werden."*
- **M1 vorläufig:** Der Entscheider ist ausgesetzt, weil er mit nur dem Trader als Eingang ein Echo war (39 von 40). Er ist nicht gestrichen: Prompt, Code und Wache bleiben, der Rollenkatalog schaltet ihn.
- **5 Stimmen** je Rolle (P1-c 90 %), Zeitgrenze je Signal **120 s** (aus der Messung), der Block steht **in der Mail** als *Sofortfassung, ungemessen*.
- **Neuprüfung festgelegt (O22):** Die Urteilsstufen und der Entscheider werden mit dem Rückspiel N4 erneut fachlich und technisch geprüft. Vorher wird nicht optimiert, weil ohne Ausgang keine Zielgröße da ist (Voranalyse_Schritt7 §20.12.5).

# E-54 · Spot-Neubau analog dem Hebel – zuerst nur Voranalyse und Analyse (Nutzer 04.10.2026)

**04.10.2026** · Nutzer: *„Ich würde gerne den Spot-Ast neu umbauen, analog dem Hebelablauf"* und dann *„Ok, ja, vorerst nur eine Voranalyse und Analyse, damit wir die Grundlage aus fachlicher und technischer Sicht haben. Trage dies in die Planung ein."*
- Plan O23 (Inhalt V-1 bis V-6), Dokument `Voranalyse_Spot_Neubau_04_10.md`. Gebaut wird erst nach Abstimmung. Am Betrieb kommt Spot **nach** der Hebel-Umstellung (Schritt 8): Der Hebel hat Vorrang.
- Nur lesend und deterministisch am Desktop, parallel zum LLM-Rückspiel N4 (das hängt am Kontingent, nicht an der Rechenzeit).
- Die alte Spot-Kette läuft unverändert weiter. Ob sie angehalten wird, ist offen beim Nutzer.

# E-55 · Halt bei Spot; zuerst Hebel (Mails und LLM); Ausstiegserinnerung nur bei offener Hebelposition (Nutzer 04.10.2026)

**04.10.2026** · Nutzer: *„So, wir machen nun Halt bei Spot. Notiere alles bisher Vorgeschlagene in den jeweiligen Dokumentationen und im Plan, mit dem Hinweis, dass eine Totalüberarbeitung, die Machbarkeit und die offenen Punkte behandelt werden müssen. Zuerst kümmern wir uns darum, dass die Hebelfunktion – E-Mails und LLM – sauber funktioniert.“* *„Einen Punkt werden wir sofort ändern: Ausstiegsmails von nicht offenen Hebelpositionen.“*
- **Spot (O23) ist angehalten.** Die Voranalyse und alle Vorschläge stehen als **notiert, nicht abgestimmt** in `Voranalyse_Spot_Neubau_04_10.md`. Vor einer Wiederaufnahme: Totalüberarbeitung, Machbarkeit, offene Punkte. Die alte Spot-Kette läuft weiter (O24 regelt den rechtzeitigen Stopp ihrer LLM-Aufrufe).
- **Vorrang:** Die Hebelfunktion – REGEL0-Mails und LLM-Prüfblock – muss sauber laufen.
- **Ausstiegserinnerung (REGEL0, 24 h):** Sie geht nur noch, wenn bei Bitpanda eine **offene LONG-Hebelposition** in diesem Asset besteht. Fachliche Ausgestaltung (meine Entscheidung, Begründung in Voranalyse_Schritt7 §21):
  - Ist der Positionsstand **unbekannt** (Bitpanda-Abgleich veraltet ≥ 1 h, nie gelaufen, nicht lesbar), geht sie **mit Vermerk** raus. Eine fehlende Ausstiegsmeldung bei echtem Geld wiegt schwerer als eine überflüssige Mail.
  - Eine entfallene Erinnerung wird als **Fakt** abgelegt (Zeitpunkt und Grund) und **nie nachgeschickt**.

# E-56 · Neuer Aufbau der REGEL0-Signalmail (O25, M-a bis M-f; Nutzer 04.10.2026)

**04.10.2026** · Nutzer zu den Mails des Tages: *„die Infos sind nicht optimal gruppiert – USD statt Euro“*, *„nein, nicht die bisherige Form übernehmen“*, zum Vorschlag M-a bis M-f mit Spot-Hinweis: *„ja, zuerst die offensichtlichen Fehler prüfen und fixen“*.
- **Zuerst** die offensichtlichen Fehler behoben (§21.3, 335470a): Umbruch, Bildbreite, deutsche Zahlen, EUR, die falsche Liquidationslinie.
- **Dann** der Neuaufbau (§21.4): Handlung → Chart → Einschätzung → Begründung → Technik; alles Handlungsrelevante in **EUR und Ortszeit**; Fachbegriffe nur in der Technik; echtes HTML; Hinweis, wenn die alte Spot-Kette zum selben Asset gemailt hat.
- Der **Betreff bleibt**, damit Mailfilter weiter greifen. Die Korrektur- und die Erinnerungsmail sagen die Zeit ebenfalls zuerst in Ortszeit.

# E-57 · S7-7 Mindestbedingungen der Testwoche, Freigabe nur mit Ja, verpasste Stunden nachrechnen (Nutzer 04.10.2026)

**04.10.2026** · Nutzer: *„Ja, S-1 bis S-5 wie vorgeschlagen, prüfen und gegenprüfen.“* (Voranalyse_Schritt7 §22)
- **S-1 Bedingungen:**
  - T1 jede Stunde gerechnet, T2 Frische, T3 Laufzeit, T4 fehlerfrei;
  - F1 Signalmail vollständig, F2 rechtzeitig, F3 Korrektur, F4 Ausstieg, F5 R-R11 am NB;
  - L1 Prüfblock; K Mail am Handy;
  - **Auskunft** A1–A4: Signalbilanz-Summe (erwartet 19,5 je Woche, je Asset nicht prüfbar), Korrekturquote, Ertrag (in einer Woche nicht entscheidbar), Urteile der Rollen.
- **S-2 Freigabe nur mit Ja:** Schalter `testwoche_freigegeben` (Vorgabe false). Die Testwoche läuft nie still aus.
- **S-3 Fällt eine Bedingung:** beheben (kritische Punkte auch unter der Woche, E-43) und die Woche verlängern. Eine Änderung an der REGEL0 selbst startet sie neu.
- **S-4 N-1:** verpasste Signalstunden bis 3 h zurück nachrechnen, R-R11-gleich.
  - Fachlich ergänzt beim Bau: Ist der gemessene Einstieg **mehr als 1 h** vorbei, geht keine Signalmail, sondern der Vermerk *verpasst*.
  - Der freigegebene D1-Weg (Mail wenige Minuten nach dem Einstieg) bleibt und nennt die Verspätung.
- **S-5:** Am Ende der Woche liefert der Nutzer Teilexport und Ablage-Kopie, für F5 die Daten.

# E-58 · Bitpanda-Bestand ohne Watchlist-Eintrag: automatische Aufnahme erst mit dem Spot-Neubau (Nutzer 05.10.2026)

**05.10.2026** · Nutzer: *„Ja O26 wie vorgeschlagen, mit Spot-Neubau – ist ok, d.h. ich muss das Asset manuell aufnehmen?“*
- E13 (16.09.) gilt weiter: Eine Position ohne Watchlist-Eintrag kommt als Mail, **höchstens einmal am Tag**. Seit 05.10. gilt das auch über Neustarts.
- Die automatische Aufnahme kommt mit O23 (Spot-Neubau). Bis dahin: **von Hand**, wenn das Asset im System sein soll. Folgen: Es zählt im Portfoliowert, und die alte Spot-Kette analysiert es. Die REGEL0 braucht die Watchlist nicht.
- Option auf Ja: eine Liste *bewusst nicht beobachtet*, die die Mail je Asset abstellt.

# E-59 · Spot M-0 Machbarkeit parallel zum Hebel, sauber getrennt (Nutzer 05.10.2026)

**05.10.2026** · Nutzer: *„Ja, Spot M-0 Machbarkeit parallel starten, aber so, dass beide Themen Spot und Hebel sauber getrennt bleiben und alles dokumentiert, in die Zentraldokumente nachgezogen und in den Hauptplan eingetragen wird.“*
- **Trennung T-1 bis T-6** (Voranalyse_Spot §7.1): getrennte Dokumente, kein Betriebscode für Spot, getrennte Commits (`Spot M-…:` / `Hebel:`), Hebel hat Vorrang, Spot misst nur am Desktop ohne LLM-Kontingent, getrennter Memory-Abschnitt.
- **M-0** prüft nur, ob ein Spot-Pfad überhaupt nachweisbar trägt: M-0a Welches, M-0b Ob, M-0c L3. Regeln und Folgen sind **vor** der Messung festgelegt (§7.2, §7.3).
- Zur Beschleunigung von N4 (zweiter Gemini-Schlüssel) erinnere ich am Abend.

# E-60 · Spot wird neu angelegt: Klima und echte Bodenbildung (Nutzervorgabe 05.10.2026)

**05.10.2026** · Nutzer: *„Ok, Spot muss anders angelegt werden. BTC und Altcoins hatten gerade eine Trendwende, d. h. es ist erforderlich, das Wetter bzw. Klima für eine echte Bodenbildung zu erkennen.“*
- Spot fragt zuerst nach dem **Klima** und dem **Boden** (wann), nicht nach dem Querschnitt (welches). M-0 hat für das Welches nichts gefunden (§7.4).
- Vorschlag: Klima → Bodenbildung (Ereignisstudie, beschreibend) → Aufbau. Die Voranalyse kommt auf Ja, getrennt vom Hebel (E-59).

# E-61 · Spot K-1 bis K-5 als vorläufige Hypothesen (Nutzer 05.10.2026)

**05.10.2026** · Nutzer: *„Ja, lege diese als vorläufige Hypothesen fest, abhängig von den Ergebnissen.“*
- K-1 (2018–2022 bestimmen, 2026 testen), K-2 (CoinMetrics), K-3 (A Zone · B Wende · C Klima als Fakt-Ampel), K-4 (echter Boden 45 %/180 T/+50 %), K-5 (Erfolg gegen DCA mit gleichem Kapital) gelten **vorläufig**.
- Die Messung entscheidet. Eine Änderung wird **Fassung 2 mit Begründung**; Fassung 1 bleibt Maßstab (Voranalyse_Spot §8.6).

# E-62 · Spot Fassung 2: die Zone als Aufbaufenster (Nutzer 05.10.2026)

**05.10.2026** · Nutzer: *„Ja, der Vorschlag hört sich vernünftig an“* · *„Ja, prüfen und gegenprüfen.“*
- Nach §8.7: H4 Wende trug nicht, die Zone zeigte sich vorn, aber mit Vorgriff in der Vergleichsbasis.
- **Fassung 2** (Voranalyse_Spot §8.8):
  - Zone gegen alle Tage, zweiseitig;
  - fallendes Messer je Episode;
  - Aufbau gegen DCA (H5);
  - BTC als Wiederholung, ETH als teilweise unabhängige Menge, ab 2023 als Auskunft;
  - Kauf zu t+1.
- **Gemessen wird erst nach dem Ja zum Plan.** Die Folgen sind vorab festgelegt.

# E-63 · Hypothesen nicht starr, Fassung n+1 mit Begründung (Nutzer 05.10.2026)

**05.10.2026** · Nutzer (Ja zu Fassung 2): *„Ja, wir müssen an einem Punkt starten. Sollten wir während der Messungen zur Erkenntnis gelangen, dass die Annahmen und Hypothesen geändert werden müssen, dies bitte berücksichtigen. Nicht, dass wir starr an diesen festhalten.“*
- **Regel:** Zeigt eine Messung, *woran* eine Annahme scheitert, wird sie geändert (**Fassung n+1**).
- **Voraussetzungen:**
  - eine Begründung aus der Ursache, nie aus dem Wunschergebnis;
  - die alte Fassung und ihr Ergebnis bleiben stehen;
  - die Zahl der Blicke auf dieselbe Menge wird ausgewiesen;
  - auf derselben Menge ist eine Fassung n+1 **Beschreibung**, der Test kommt aus neuen Daten.
- **Ersetzt** in §8.8 die Folge *„kein neuer Anlauf auf derselben Menge“*: Ein Anlauf ist erlaubt, zählt aber nicht als Nachweis.

# E-64 · Spot Fassung 3: gewichten statt warten, Klima aus BTC, je Marktepoche (Nutzer 05.10.2026)

**05.10.2026** · Nutzer: *„Ja, da die ersten Jahre und ab 2024 markttechnisch doch etwas anders sind, müssen wir dies berücksichtigen, es gab nur wenige echte Zyklen.“*
- **Fassung 3** (Voranalyse_Spot §8.10):
  - Kaufmenge am Zuflusstag = Bargeld × (1 − q). q ist das Klima aus BTC (MVRV, Drawdown, 200 Wochen), Perzentile wachsend.
  - Gilt für BTC und ETH.
  - Epochen E1 2017–2020 · E2 2021–10.01.2024 · E3 ab ETF-Start 11.01.2024.
- **Gemessen wird erst nach dem Ja zum Plan.** Dritter Blick auf dieselben Daten, also Beschreibung; der Test ist eine laufende Mitschrift.

# E-65 · Spot nach dem Muster des Hebels — SPOT-REGEL0 (Nutzer 05.10.2026)

**05.10.2026** · Nutzer: *„Ja, die Punkte erscheinen sinnvoll, die Ausstiegsfrage für Spot (aktuelle Hebelplanung) steht ohnehin an. Unabhängig davon ist eine Mitschrift für langfristige Beobachtung sinnvoll, aber für unser Konzept und Vorhaben ungeeignet. Wir brauchen jetzt sinnvolle Lösungen, Tests und Simulationen, welche uns weiterbringen, analog des gerade umgebauten Hebels.“*
- (a) Die Klima-Ampel kommt als Fakt in die Mail, gebaut in S7.
- (b) Der Ausstieg wird mitgemessen.
- ✗ (c) Keine Mitschrift.
- **Spot wird als Ereignis je Asset auf Tagesbasis gebaut**, Schritte S1–S8 wie beim Hebel (Voranalyse_Spot §9). Das Klima wird Achse auf den Ereignissen.
- Stufe 1 wird vorab festgelegt (§9.3). **Gemessen wird nach dem Ja.**

# E-66 · Spot: G1 zuerst, offen abgestimmt — Altcoin-Spot gegen Akkumulation der Kernwerte (Nutzer 05.10.2026)

**05.10.2026** · Nutzer: *„Spot-Thema müssen wir offen diskutieren und abstimmen – das geht nicht in ein paar Zeilen: Was soll Spot zur Akkumulation der Kernwerte BTC etc. unterscheiden? Also ein Vergleich, ob die aktuelle Akkumulation überhaupt Sinn ergibt oder wir darauf aufsetzen können – eher nicht. G1 ist der erste Punkt, an dem wir starten werden und diese fachlich und technisch bewerten müssen, damit wir überhaupt etwas festlegen können. Der Zeithorizont geht von ein paar Monaten eher über 1–2 Jahre bei Altcoins Spot, und Akkumulation kann über mehrere Zyklen gehen (mit Teilverkauf, Kernwerte).“*
- **Keine Festlegung vor der Bewertung von G1.** SPOT-REGEL0 (§9) und seine Stufe 1 **ruhen**.
- **Horizonte (Nutzervorgabe):**
  - Altcoin-Spot: einige Monate bis eher 1–2 Jahre;
  - Akkumulation der Kernwerte: über mehrere Zyklen, mit Teilverkauf.
- **Die Nutzereinschätzung zur heutigen Akkumulation:** *eher nicht* tragfähig, um darauf aufzusetzen. Zu prüfen ist das im Vergleich.
- Die Diskussionsgrundlage steht in Voranalyse_Spot §10. Anschluss an den Richtungsentscheid vom 24.09. (drei Geschäfte: Hebel, Akkumulation, Spot).

# E-67 · Schalter A gesetzt, Krypto vor Multiasset, Spot-Regelwerk breiter (Nutzer 05.10.2026)

**05.10.2026** · Nutzer: *„Schalter A setzen, dann mit D1 und D2 starten. Wichtig: Wenn wir alles anhalten, brauchen wir Alternativen. Zuerst bauen wir Krypto fertig, dann die Multiasset-Schiene. Deine Anmerkung zu BTC und Altcoins finde ich gut – aber meines Erachtens ist das ein Auftrag für das Regelwerk: Welche Spotwerte, mit welcher Diversifikation bringen mehr Rendite und schlagen BTC. Schwierig – OB und WIEVIEL Rendite über Altcoins möglich ist, hängt am Zeitpunkt des Kaufes; meistens ist antizyklisch kaufen und auch korrekt verkaufen zielführend, manchmal können kurzfristige Einstiege kurz nach dem Bärenmarkt oder bei Korrekturen die bessere Wahl sein. Ich denke, wir müssen etwas breiter denken, wie wir die Probleme angehen können.“*
- **`spot_kette_angehalten: true`** (`regel0_betrieb.yaml`): Die alte Rollen-Kette läuft in **allen** Gruppen nicht mehr. REGEL0 läuft weiter, nachgewiesen mit `pruefe_r4.py`.
  - Die Wachzeile R-4 verlangte bis dahin den Stand *aus* und hätte ihn eingefroren. Sie prüft jetzt das Verhalten.
- **Reihenfolge:** zuerst **Krypto** fertig (Hebel, Akkumulation, Spot), **danach** die Multiasset-Schiene (Aktien, Rohstoffe, ETF, Absicherung).
- **Alternativen** für das Angehaltene: Plan Hebel **O27**, Voranalyse_Spot §11.6.
- **Auftrag ans Regelwerk:** Welche Spotwerte schlagen BTC, mit welcher Diversifikation? Der Zeitpunkt (antizyklisch oder früh nach Bärenmarkt und Korrektur) und der Verkauf gehören dazu. Breiter denken: das Schichtenmodell in Voranalyse_Spot §11.
- Weiter mit **D1** (Kernwerte und Gewichte) und **D2** (Teilverkauf).

# E-68 · Kernwerte BTC, ETH, SOL; Teilverkauf für den nächsten Boden und Entnahme (Nutzer 06.10.2026)

**06.10.2026** · Nutzer: *„D1 – BTC, ETH und Solana. D2 – ja b und d jedenfalls, a und c eher später, denke ich. Messplan für alle relevanten Fälle.“*
- **D1:** Kern = **BTC, ETH und SOL**. Mein Vorschlag, SOL in den Spot zu geben, ist abgelehnt. Die Gewichte werden gemessen (D1-M).
- **D2:** Teilverkauf für **(b)** Geld für den nächsten Boden und **(d)** Entnahme. (a) Risiko senken und (c) Umschichten in Altcoins kommen später.
- Messplan für alle relevanten Fälle vorab (Voranalyse_Spot §12). Gemessen wird nach dem Ja.

# E-69 · Aufbau 70/20/10 mit Ausgleich über die Raten; K1 als Hinweis in der Klima-Ampel (Nutzer 06.10.2026)

**06.10.2026** · Nutzer: *„1 ja“* (Aufbau) · *„ja, K1 als Hinweis in die Klima-Ampel aufnehmen“*
- **Aufbau der Kernwerte:**
  - BTC/ETH/SOL **70/20/10**, monatlich gleicher Betrag.
  - **Ausgleich über die Raten** (R1): kein Verkauf, steuerneutral.
  - Grundlage: Voranalyse_Spot §12.6.
- **Teilverkauf (b) und Entnahme (d):** **kein automatischer Verkauf**.
  - Die **Klima-Ampel** bekommt den Hinweis **K1** (§12.9/§12.10): *„Die starke Überhitzung kippt (q war über 0,90 und fällt unter 0,85 / 0,75 / 0,65) – Teilverkauf erwägen“*, samt der gemessenen Wirkung und dem Vorbehalt *ein Ereignis (2021)*.
  - Ebenso der Hinweis für den **Rückkauf** in der Zone (q ≤ 0,20 / 0,10 / 0,05).
  - Verkauf, Rückkauf und Entnahme entscheidet der Nutzer.
- **Gebaut wird mit dem Spot-Betrieb (S7, O27).** Bis dahin kein Betriebscode (T-2).

# E-70 · Altcoin-Spot: antizyklisch am Boden kaufen und Positionen führen, direkt messen (Nutzer 06.10.2026)

**06.10.2026** · Nutzer: *„hier kann und soll nicht die Kernwert-Berechnung angewendet werden, meines Erachtens. Antizyklisch – Bodenkauf ist erforderlich, dann sollte eine massive Outperformance möglich sein; eigentlich müssen die Spot-Positionen auch geführt werden. Versuche für die Altcoins auch alternative Ansätze, wie wir damit sinnvoll umgehen können.“*
- §14.6 maß die **Grundrate** (Kauf zu jedem Zeitpunkt, ungeführt), nicht die Strategie. Die Zulassungsregel §14.3 entfällt für diese Fassung (E-63).
- Gemessen werden (Voranalyse_Spot §15):
  - der **Bodenkauf je Coin**, mit und ohne Wende;
  - der **Markt-Boden-Korb**;
  - die **Führung**: gestaffelt, Nachlauf, Zeit.
- Maßstab: BTC an denselben Tagen und eine Nullwelt. Gemessen wird nach dem Ja.

# E-71 · Altcoins: Ziel sind ASYMMETRISCHE Chance-Risiko-Verhältnisse, nicht der Durchschnitt (Nutzer 06.10.2026)

**06.10.2026** · Nutzer: *„Altcoins sind mehr als 2 Jahre gefallen und sollten einen gewissen Boden erreicht haben, und je nach Wirtschaftslage kann es auch wieder eine massive Altseason geben. Offenbar haben wir aber keine Lösung zur Thematik, wie wir die Altcoin-Diamanten finden. Ziel sollte sein, aus den unsicheren Assets jene zu identifizieren, welche ein ausgewogeneres bzw. möglichst asymmetrisches Chance-Risiko-Verhältnis aufzeigen.“*
- Zielgröße für Altcoins ist das **rechte gegen das linke Ende** je Asset (Voranalyse_Spot §19), nicht Mittel/Median gegen BTC. Ein negativer Median ist bei Diamanten-Suche kein Ausschluss.
- §14–§18 bleiben gültig für die alte Frage. A1–A6 ruhen bis zur Asymmetrie-Messung.

# E-72 · Asymmetrie: Spiegelprobe bewegungsgleich, voller Plan, Maßstab A/B/C vorab (06.10.2026; Nutzer delegiert: „du entscheidest jetzt“)

**06.10.2026** · Nutzer: *„Denke, wir sollten alle Möglichkeiten prüfen und gegenprüfen, du entscheidest jetzt. Wichtig wäre die Zielerreichung, und hier bin ich nicht sicher, ob das ein schlechter Newsletter wird oder echte Systemfunktionalität.“*
- Die Spiegelprobe *Verhältnis ≥ 1,717* (Hebel-Eichung 2.603) ist für die Asymmetrie-Messung ersetzt durch die **bewegungsgleiche Spiegelprobe** (Voranalyse_Spot §19.4). Begründung: Selbsttest (b) an 1,717 gescheitert, die feste Schwelle trennt bei 12-Monats-Fenstern nicht. Die neue Probe hatte 0 von 200 Fehlalarmen in beiden Epochen und eine Fundquote von 100 %.
- Der Maßstab *Systemfunktion / Hinweis / Newsletter* (§19.5) ist **vor** dem Ergebnis festgelegt.

# E-73 · Spot-Altcoins: Fazit §22 und W1–W7 festgehalten, VORLÄUFIG — kein Bau vor einem verständlichen Beispiel (06.10.2026)

**06.10.2026** · Nutzer: *„Ja – halte vorerst alles fest in der Doku und dem Gesamtplan. Ich kann mir noch immer nicht vorstellen, was das System leistet oder leisten soll.“*
- W1–W7 (Voranalyse_Spot §22.3) stehen als **Arbeitsstand** in Doku und Plan, **nicht** als Freigabe:
  - Watchlist als Auskunft ohne Geld mit Vorwärtsprotokoll;
  - kurze Liste;
  - keine Leistungsfilter;
  - Nachlauf-Marke als Hinweis;
  - Allokation nach 6 Monaten;
  - Bau-Voranalyse NB;
  - weitere Messungen.
- **Vor jedem Bau:** eine konkrete Beschreibung, was das System leistet. Als Beispiel des Mailabschnitts aus echten Daten und als Ablauf: was der Nutzer jeden Monat bekommt und was er damit tut (Voranalyse_Spot §22.4).

# E-74 · Spot-Altcoins: zwei Ebenen (Fortbestand vor Gelegenheit), Smallcaps wieder in der Liste, QNT als Fallbeispiel (06.10.2026)

**06.10.2026** · Nutzer: *„Ja – Quant sollte hier das Beispiel eines optimalen Kaufs am Boden und eines massiven Anstiegs als Beispiel darstellen. Bitte nimm die Smallcaps nun doch zur Liste hinzu, da Quant zu den Smallcaps zählt. Zu deinem Vorschlag – ja, finde ich gut. Das Strukturprofil werden wir noch besser gruppieren, ist aber ein guter Anfang, finde ich.“*
- **Zwei Ebenen** (Voranalyse_Spot §23.6): 1 Fortbestand (Strukturprofil, Fakten, vom Nutzer gewichtet), 2 Gelegenheit (gemessene Watchlist).
- **Smallcaps wieder in der Rangliste.** Der Entscheid *nur H/M* (§23.5) ist aufgehoben. ⚠️ Gemessen senkt die Auswahl bei S das Absturzrisiko nicht (§23.2); das wird in der Mail ausgewiesen.
- **QNT** ist das Fallbeispiel *Kauf am Boden, massiver Anstieg* (§23.7). Das Strukturprofil muss es erkennen können.
- **Voranalyse Strukturprofil** wird gestartet (§24); die Gruppierung wird später verfeinert.

# E-75 · Spot-Altcoins: Mailaufbau bestätigt; ohne Datenquellen und Abdeckungsprüfung kein Bau (07.10.2026)

**07.10.2026** · Nutzer: *„Ok, ja, Aufbau der Mail ist ok – gib mir ein echtes Beispiel der E-Mail aus. Prüfe die Datenquellen, wir haben bereits einiges angebunden; lies dich ein, was wir haben und was wir benötigen. Ohne Datenquellen und Abdeckungsprüfung bringt das System nichts. Ich bin unterwegs bis abends – schreibe alles Relevante ins Memory, Zentraldokumente und Regelwerke, dann trage alles in den Gesamtplan ein, damit nichts verloren geht.“*
- Der **Aufbau der Mail** (§26) ist bestätigt. Das echte Beispiel liegt als HTML vor (§27.1).
- **Stehende Regel:** Vor jedem Bau stehen ein **Datenquellen-Inventar** und eine **Abdeckungsprüfung** je Bedarf, mit Nachweis am NB. Ergebnis 07.10. in §27.3: Kern weitgehend da; Stammdatei (Allzeithoch, Erstdatum) und drei Abrufe fehlen (CoinGecko-Profil, DefiLlama-Gebühren, CoinMetrics); der Bestand außerhalb von Binance ist die größte Lücke.

# E-76 · LLM-Block: keine Entscheidung jetzt, die Stufe bleibt bei positiver Lösung; Analyse, wie er trennend wird (07.10.2026)

**07.10.2026** · Nutzer: *„Ja, ich schalte später XDC ab, mach bitte eine Erinnerung. Zu LLM ja, jetzt keine Entscheidung, aber die Stufe bleibt, wenn wir eine positive Lösung erreichen; hier müssen wir analysieren, wie wir das schaffen.“*
- N4 hat am Zwischenentscheid 250 *STOP-ANPASSEN* ergeben (Schritt7 §23.12).
- Der Block bleibt **Auskunft**. Die **Stufe bleibt im Aufbau**, sobald eine Fassung nach §23.7 trägt.
- Weg der Analyse A1–A4 in Schritt7 §23.13. Erst WORAN und die Frage, ob die Information überhaupt da ist; dann **ein** Hebel je Fassung, höchstens drei Fassungen.

# E-77 · Reihenfolge: Hebel A1/A2 jetzt, Spot-Bau O28 nach der Testwoche (07.10.2026)

**07.10.2026** · Nutzer: *„Ok, nur damit wir die Themen nicht vermischen: Ok, wenn du meinst, können wir Hebel A1 bzw. A2 angehen oder Spot weiter umbauen – was denkst du als Experte?“* · *„Ok, dann halte alles fest in Memory, Doku und Plan, danach A1 mit Prüfung und Gegenprüfung.“*
- Empfehlung angenommen: A1/A2 am Desktop (Vorrang Hebel, E-59). Der Spot-Betriebscode wartet bis nach der Testwoche (≥ 10.10.) und der Abstimmung O28.

# E-78 · LLM-Stufe: Ziel *besser als die Regel*, Minimum *gleich oder etwas darüber* als Bestätigung oder Gegenmeinung (07.10.2026)

**07.10.2026** · Nutzer: *„Ja, zur Grundfrage teilweise ok. Ja, Ziel wäre, dass das LLM besser trennt, aber als Minimum würde ich eher gleich oder etwas darüber ansetzen, also als Bestätigung oder Gegenmeinung. Was sagst du, wie realistisch ist es, dass das LLM besser ist?“*
- **Ziel:** Das LLM trennt besser als die Regel mit denselben Fakten.
- **Minimum für das Bleiben der Stufe:** gleich oder etwas darüber, in der Rolle **Bestätigung oder Gegenmeinung**. Messbar gefasst in Schritt7 §23.16 (M-1 bis M-3).
- A2 Teil 2 wird gemessen (Nutzer-Ja).

# E-79 · Weitere Information (Text, Ereignisse) für das LLM erlaubt; bewertet nur statistisch und nur vorwärts (07.10.2026)

**07.10.2026** · Nutzer: *„Ok, dann kurze Korrektur bzw. Klarstellung: Du kannst gerne weitere Informationen für das LLM nutzen, wenn wir diese haben. Ich frage mich nur, wie wir dies bewerten und wie das LLM dies ausgeben soll, z. B. ein neuer Partner des Assets hat investiert – die Info selbst trägt nichts, es sei denn, es erfolgt ein Kursanstieg. Wie soll das tragen?“*
- Erlaubt, wenn vorhanden. Ein Ereignis trägt nur **statistisch**: Signale mit dem Ereignistyp laufen besser als ohne.
- Ausgabe in **fester Form** (Typ, Richtung, Wesentlichkeit, Neuheit, eingepreist), in der Mail als Fakt in Worten.
- **Nur vorwärts testbar** (Kontamination, fehlende Zeitstempel). Schritt7 §23.17.

# E-80 · LLM Fassung 0.2: die A2-Kandidaten sofort als Trader-Eingabe in den Betrieb, vorwärts prüfen (07.10.2026)

**07.10.2026** · Nutzer nach A2 (§23.18): *„Ok, ja, bitte berücksichtigen, gleich die neuen Kandidaten und Quellen als LLM-Rollenbeitrag sofort einsetzen in Prod; messen und vorwärtsprüfen wird ohnehin schwer und dauert.“*
- Fassung **0.2-sofort**: Der Trader bekommt zuerst den Plan, dann die **Lage zur Signalstunde** (N-a bis N-f, neutral, ohne gemessene Richtung), den weiten Rahmen zuletzt (F3). Die Definitionen sind dieselben wie in A2 (Gegenprobe 60/60 gleich).
- **Bewusst gegen F1:** Einzeln trennt keiner der Kandidaten. Sie stehen drin, weil das LLM sie **verbinden** könnte; das zeigt nur der Vorwärtstest. Abgerechnet wird mit M-1 bis M-3.
- Am NB nicht verfügbar: Käuferanteil (N-g); Terminmarkt nur für rund 40 Werte. **Text- und Ereignisquellen gibt es noch keine.** Das ist ein eigener Punkt (Datenquellen-Inventar, E-75/E-79).
- N4 bleibt auf der **eingefrorenen 0.1e** (`regel0_llm_0_1e_n4.yaml`, Fingerabdruck unverändert). Schritt7 §23.19.


# E-81 · Fassung 0.2 rückblickend prüfen (N5) statt Schatten im Betrieb (07.10.2026)

**07.10.2026** · Nutzer: *„Bin unsicher, was gewinnen wir an tatsächlicher Erkenntnis – prüfe, ob es sich lohnt.“* → Vorlage: Der Schatten liefert in Wochen nur ein grobes Versagen; ein Rückspiel auf den 1.000 N4-Ankern beantwortet die Frage in Tagen, gepaart gegen 0.1e. Nutzer: *„Ja, prüfen und gegenprüfen.“*
- N5 nach dem Ende von N4: Kontaminationsprobe K_a, T mit Zwischenentscheiden, R_v mit vertauschten Blöcken. Kontingent mit N4 zusammen gezählt.
- Vergleich gegen die **bessere Regel, mindestens den Zufall**. Diese Korrektur wurde vor dem ersten Aufruf aus der Prüfung gewonnen: Regel F liegt 2025/26 unter dem Zufall. Schritt7 §23.20.


# E-82 · Der Entscheider bleibt vorgesehen, muss aber eigene Information bekommen (07.10.2026)

**07.10.2026** · Nutzer: *„Ich bin schon der Meinung, dass der Entscheider Sinn macht, jedoch muss dieser genau so konstruiert werden. Offenbar ist ‚der Markt stützt einen Handel‘ zu wenig und u. U. nicht die erforderliche Information. Gut, wenn es am Plan steht, dann weiter.“*
- Der Entscheider fiel 0.1c bis 0.1e nicht an der Idee, sondern an den Eingängen: Die Markt-Sicht war konstant (85 % *stützt*), mit nur dem Trader war er ein Echo (39/40).
- Neubau nach N5 (Plan O22):
  - erst die Information bestimmen, die ein Gesamturteil braucht (z. B. Gegenwind/Rückenwind für die Gegenbewegung statt *„stützt“*);
  - jede Eingangssicht muss für sich unterscheiden;
  - gemessen gegen den Trader allein, eine Zählregel und den Zufall.
- Schritt7 §23.21.


# E-83 · Binance-Ankündigung: als Fakt in die Signalmail (Bau nach der Testwoche) und als LLM-Kandidat 0.3 (Rückspiel nach N5) (07.10.2026)

**07.10.2026** · Nutzer: *„Ja, a und b, halte alles fest in den Dokumenten und Plänen.“*

**(a) Bau ab dem 10.10. (nach der Testwoche):**
- Bestandteile:
  - eigener Abrufer-Job;
  - ein Modul `agent/binance_ankuendigungen.py` für Betrieb und Messung;
  - Ablage in `regel0_signale.db` (`ankuendigung`, `signal_ereignis`);
  - Mailzeile *„Binance“* in der Einschätzung, nur bei Token- oder Futures-Delisting oder Monitoring, **nur Fakt**;
  - Vorwärtsprotokoll für alle Signale;
  - Abschnitt im Teilexport.
- Kontrolle K-ANK-1.

**(b) LLM-Kandidat für Fassung 0.3:**
- gezieltes, **gepaartes** Rückspiel (mit und ohne den anonymen Satz) auf den rund 150 REGEL0-Einstiegen mit Ereignis, nach N5;
- dazu die Kontaminationsprobe der Untermenge;
- abgerechnet nach M-3: Ändert das LLM sein Urteil, und liegt es damit richtig?

Schritt7 §23.24.


# E-84 · O29 vorbauen mit Schalter AUS (Paket P3), unter einer Bedingung (07.10.2026)

**07.10.2026** · Nutzer: *„Ja, O29 so vorbauen mit Schalter aus - wenn es Sinn macht und sich nichts mehr ändert.“*
- Ergänzt E-83: Der Bau darf **vor** dem 10.10. fertig werden, ist aber per Schalter `ankuendigung_aktiv: false` **unwirksam**. Eingeschaltet wird erst nach der Freigabe in P5.
- **Bedingung vor dem Start von P3:**
  1. P1 (NB-Prüfung) verlangt keine Änderung an `regel0_mail`, `_regel0_mails` oder der Ablage;
  2. P2 (O30) ändert den Zuschnitt von O29 nicht, z. B. durch eine bessere Quelle oder weitere Ereignisarten.
- Trifft eines davon zu, wird zuerst der Zuschnitt abgestimmt.


# E-85 · Spot: Einstieg je Asset UND Führung je Bestand; der Newsletter bleibt daneben (08.10.2026)

**08.10.2026** · Nutzer:
- *„Ein Newsletter 1× pro Monat ohne konkrete Handlungen, nur Rangfolgen mit Informationen, das ist nicht das eigentliche Ziel für den Einstieg – weil es somit keinen gibt.“*
- *„Den Newsletter-Plan nicht gänzlich verwerfen, sondern prüfen, wie wir zusätzlich sinnvolle Spot-Einstiege bewerten können.“*
- *„Der optimale Einstieg je Asset ist nur ein Teil des Paketes. Analog Hebel brauchen wir je Bestand eine Führung bzw. optimalen Ausstieg … diese Anstiege sind meist nicht dauerhaft.“*

**Festgelegt:** O31 hat zwei Teile.
- **Teil A Einstieg:** gemessen 08.10., nicht entscheidbar (Spot §29.4–§29.6).
- **Teil B Führung/Ausstieg je Bestand:** Fragen B-1 bis B-9 in Spot §29.7. Es gilt das bestehende Schema S-B/M-5/O14/O19, die Trailing-Altregel vom 04.08. wird abgelöst.
- Die Monatsübersicht (O28) bleibt daneben, als Information und nicht als Handlung.

**Korrektur der Prüfanlage (§29.5):** Ein Spot-Urteil braucht mindestens **20 Einstiege an 6 Stichtagen**. Erst dann hält die Anlage ihr Soll.


# E-86 · Spot: Zwei-Rollen-Modell (Season-Option L / Ausbruch K), Altbestand per Vorschlag je Coin (08.10.2026)

**08.10.2026** · Nutzer: *„ja finde ich nicht schlecht“* (grundsätzlich Ja mit Vorbehalt) und: *„gehe ich recht in der Annahme, dass der Altbestand nicht in die Rollen fällt – oder ist das die Übersicht mit Vorschlag?“*

**Festgelegt:**
- Zwei Rollen, beim Kauf festgelegt, kein späterer Wechsel.
  - **L:** Fortbestand-Auswahl, kein Nachlauf, Staffel, kleines Budget.
  - **K:** Erkennung (Teil C), Marke.
- Der Altbestand bekommt je Coin einen Rollen-Vorschlag des Systems; der Nutzer entscheidet. Dritte Möglichkeit *geplanter Abbau*. Die Führung startet am festen Starttag, der Einstand ist nur Anzeige.
- Teil B wird je Rolle gemessen. Spot §30.9.

**Vorbehalt des Nutzers:** Spot ist groß. Das Modell ist Grundlage, nicht Endstand.


# E-87 · Spot: Season-Ampel (L bedingt) ja, aber kalibrieren; Reihenfolge Ampel → K-H1 (H und M) → C2 Listings (08.10.2026)

**08.10.2026** · Nutzer: *„1. Ja, L-Vorschlag – aber noch kalibrieren und messen (gut, schlecht, Grenzen, Übergänge, Start Altseason ca.). 2. Werden nur Highcaps bewertet? Was ist mit Midcaps und dem Bestand mit Smallcaps? 3. Ja, wenn die Reihenfolge stimmt.“*

**Festgelegt:**
- Die Ampel wird sichtbar (App, jede Spot-Mail, Ereignis-Mail bei Zustandswechsel), aber erst nach der **Kalibrierung** §36.3.
- Die Klasse gilt nur für den **K-Einstieg**: H Hauptprüfung, M eigene Prüfung, S über C2. Führung, Rolle und Preis gelten für **jeden** Bestand.
- Die 11 Krypto-Bestände außerhalb des Binance-Spot-Universums werden über Prod-Kurse und O26 eingebunden.
- Reihenfolge §36.2. Der Hebel hat Vorrang (P5 am 10.10.).


# E-88 · H15: Hebelführung echter Positionen zuerst, Warnung bei 15 % Abstand zur Liquidation (09.10.2026)

**09.10.2026** · Nutzer: *„Ja H15 zuerst, Warnung bei 15 % Abstand“* (Anlass: die Führung echter Hebelpositionen lief seit dem Halt der Rollen-Kette am 05.10. nicht; offene BTC LONG 3× des Nutzers ohne Führung und Warnung, Schritt7 §23.29).

**Festgelegt:**
- H15 vor O29.
- Warnschwelle 15 % Abstand Kurs → geschätzte Liquidation, Stufen 15 / 10 / 5 % (fachlich gesetzt, §23.30).
- Ein Fakt zum Schutz der Position (RM-11), kein Handelssignal; Entscheidung und Handlung beim Nutzer.
- Wirksam erst nach der Freigabe der Testwoche, eine NB-Änderung zur Zeit.


# E-89 · Spot §39 Block A abgestimmt (09.10.2026)

**09.10.2026** · Nutzer: *„A1 (a) – für K brauchen wir vorher eine Lösung, welche funktioniert, A2 – OK, A3 – wie und wo trage ich die Rolle ein, welche gibt es u. U. eine Default-Rolle ab Start, A4 – bin ich nicht glücklich, hier sollten wir soweit möglich eine Lösung finden, A5 – JA, A6 ja mit B1.“*

**Festgelegt:**
- **A1:** gemeinsamer Starttag für den Altbestand; Rollen Kern / L / Abbau; K erst mit funktionierender Lösung.
- **A2:** Rollen-Vorschlag je Coin, der Nutzer entscheidet.
- **A5:** erledigt.
- **A6:** O19 für Spot abschalten gleichzeitig mit B1.

**Offen:**
- A3 (Eintrag, Rollenliste, Default: Vorschlag §39.2 zur Abstimmung).
- A4 → **Auftrag K-Lösung** (§39.3, Kandidaten K-1 bis K-4).


# E-90 · Spot-Rollen: Kern fest, alle übrigen Krypto-Bestände automatisch L, kein Pflichteintrag (09.10.2026)

**09.10.2026** · Nutzer: *„A3 ja so“* und *„… finde ich es aktuell nicht sinnvoll, manuell einzutragen, oder?“*, Expertenmeinung zugestimmt (§39.4).
- Kern BTC/ETH/SOL fest, alle anderen Krypto-Bestände L (Default).
- Abbau nur als Vorschlag mit Preis gegen BTC.
- Der Rollen-Dialog kommt erst mit K (Stufe 2).
- Ersetzt den Default *offen* aus §39.2.


# E-91 · Spot Block B abgestimmt + Handlungsgrundsatz: jede Mail eine Handlung (09.10.2026)

**09.10.2026** · Nutzer: *„B1 ja mit Prüfung, B2 ja, B3 ja, B4 ja. Hinweis: Wir bewegen uns wieder auf den NEWSLETTER-Weg zu … ohne konkrete Ableitung auf eine Handlung finde ich diese nicht sinnvoll. Bei 30+ Assets ist das nur Arbeit.“*

- **B1** Mitnahme ×3: Übertragbarkeit auf den ganzen Bestand gemessen (Spot §39.6): **trägt** (+4,87 Pp, Rang 1,00, Gegenprobe 4/4) → gilt für den ganzen L-Bestand.
- **B2 bis B4 ja.**
- **Grundsatz:** Mail nur mit Handlung (Coin, Handlung, Frist, gemessene Begründung mit Belegstufe); der Rest im App-Tab.
- **Vorschlag zur Bestätigung** (§39.7):
  - C2 Monatsmail entfällt.
  - Futures-Start und Delisting bekommen keine eigene Mail.
  - B4 wird zur **Abbau-Reihenfolge** aus dem unteren Watchlist-Fünftel.


# E-92 · Hebelführung: Handlung vor Warnung (09.10.2026)

**09.10.2026** · Nutzer: *„ja H15 pushen, wenn alles geprüft und gegengeprüft wurde“*. Die ganze Suite fand vor dem Push 5 rote Prüfungen.

- **Fachliche Entscheidung (eigene, nach E-91 *zuerst die Handlung*):** *LIQUIDATION NAHE* ist eine Warnung und steht **hinter** den konkreten Handlungen aus dem Plan (SCHLIESSEN, HEBEL SENKEN mit Nachschussbetrag). Die Warnstufe bleibt im Grund und im Mailschlüssel.
- HALTEN und STOP NACHZIEHEN verdrängen die Warnung nicht.
- Rangfolge: LIQUIDATION ERREICHT > SCHLIESSEN > HEBEL SENKEN > LIQUIDATION NAHE > KURS FEHLT > STOP NACHZIEHEN > HALTEN.
- Nachweis: Schritt7 §23.33 (Gegenprobe G7, 3.636 Fälle). Am NB seit 09.10. abends (`e186281`).


# E-93 · Bitpanda-Abgleich: Spot und Hebel klar getrennt; Bestand = frei + gestakt (09.10.2026)

**09.10.2026** · Nutzer:
- *„wir brauchen für die Positionsführung von SPOT und HEBEL eine klare Trennung“*
- *„diese sind gestaked und wie normale Spot-Positionen zu führen, Ausnahme ist nur ETH, dort dauert das Entstaken einige Tage“*
- *„Ja, Importer-Fix bauen, prüfen und gegenprüfen“* · *„Ja, jetzt pushen“*

- **Trennung nach Bitpanda-Wallet-Art:**
  - **Spot** = `shared-default` + `staking-service` (+ Börse) → `holdings`.
  - **Hebel** = `margin-trading` + `margin-trading-credit` → `hebel_positions`, **nie** `holdings`.
- `/portfolio` liefert bei offenem Hebel zwei Zeilen je Asset ohne Kennzeichen (Rohantwort 09.10.). Die Zuordnung läuft **über die Menge**, ohne Raten (`spot_zeile`).
- **Festlegung (eigene):** Die Spot-Kontrolle prüft **Spot gegen Spot**. Eine fehlende Hebel-Zeile ist Sache der Hebel-Kontrolle (Schritt B, offen, eigene Abstimmung).
- **Bestand = frei + gestakt.** Gestakte Werte werden wie Spot geführt; ETH-Handlungen nennen die Entstake-Dauer. Leser, die nur `quantity` zählen: Plan O37.
- Nachweis: Schritt7 §23.31/§23.32/§23.35. Am NB seit 09.10. abends (`0995cc3`).


# E-94 · Testwoche der REGEL0 freigegeben (10.10.2026)

**10.10.2026** · Nutzer, nach der Lebenszyklus- und Fachprüfung (Schritt7 §23.36/§23.37):
- *„haben wir alles im Detail geprüft – Aufnahme neuer Assets, Änderung, Wegfall, Staking, Unstaking …?“*
- dann *„emails sind am handy sehr gut zu lesen“* und *„Ja, Freigabe jetzt setzen und pushen“*.

- `testwoche_freigegeben: true`. Der Vermerk TESTWOCHE entfällt, Signale und Stufen bleiben.
- **Ausdrücklich mit:** Die REGEL0 ist technisch geprüft, nach Kosten nicht als gewinnbringend belegt. Einsätze klein; das Vorwärtsprotokoll entscheidet.
- Offen bleiben: L1/H14 (Prüfblock), O36 Schritt B (Hebel-Importer), O38 (tokenisierte Aktien im Zusatzuniversum), Unstaking nicht live beobachtet.

# E-95 · Statusseite als Lagebild des neuen Systems (P9/P9b/P9c, 10./11.10.2026)

**10.10.2026** · Nutzer: *„P9 Statusseite starten“*, *„1. ja O29 einschalten 2. ja 3. ja – so aufsetzen, dass es nie veraltet“*, nach dem Bau *„Alle Karten gefüllt, nichts fehlt“*.
- **Abgestimmt:** neue Karten Kontrollen, Hebel (H15), REGEL0 heute, Betrieb, Schalter + Bestand, Kontingente je Verbraucher, Parameter (neu); entfallen ALTE KETTE, A/B/C, Regime, Parameter alt; Multi-Asset eingeklappt. Eine Quelle mit dem Teilexport (`agent/betriebslage.py`).
- **Eigene Festlegungen (fachlich, berichtet):** Z-3 bleibt (Job `portfolio_wert` lebt, Grundfunktion) · Kontrollen-Datei `nb_kontrollen.yaml` mit vier Sicherungen · Fristen je Karte nach der Datenänderung (P9c: Hebel/Kontingente/Rollen 300 s, Betrieb/Schalter 60 s) · `db.get_latest_prices` über den Index, **bitgleich** (P9b) · O44 Liquidationsmarge aus `config.yaml`.
- Nachweis: Plan_Asset_Lebenszyklus G-P/G-Q/G-R; Schritt7 §23.40–§23.42. K-ST-1 ✔, K-ST-3 offen.

# E-96 · Thesen pausiert (P10/O42, 11.10.2026)

**11.10.2026** · Nutzer: *„Ja, P10 mit beiden Jobs bauen, prüfen und gegenprüfen – wichtig beim Umbau der jeweiligen Bereiche dies berücksichtigen“*.
- Schalter `thesen_pausiert` (regel0_betrieb.yaml): `kategorie_synthese` **und** `kategorie_vorschlaege` ruhen (kein LLM, kein Netz, keine Auto-Thesen). Daten bleiben.
- **Regel für O39:** beim Umbau jedes Multi-Asset-Bereichs den Schalter mitbedenken; vor dem Wiedereinschalten die Kandidaten prüfen (Beobachtungstage laufen weiter).
- Korrigierte Planannahme: Synthese nutzt Gemini 3.1, nicht den Prüfblock-Topf 3.5. Nachweis: Plan G-S, Schritt7 §23.43. K-TH-1 offen.

# E-97 · NB-Änderungen bündeln (11.10.2026)

**11.10.2026** · Nutzer: *„wir sollten mehr Punkte gleichzeitig am NB pullen, sonst dauert die Wartezeit zur Prüfung immer eine Stunde“*.
- Ersetzt *„eine NB-Änderung zur Zeit“*. Fertig Geprüftes geht in **einen** Pull + Neustart; jede Änderung behält eine eigene Kontrolle mit eindeutigem Merkmal; **eine** Diagnose für alle.
- **Allein** bleibt, was die Produktions-DB umschreibt oder Signale/Hebelhöhe/Mails eines laufenden Handels verändert.
- Eingetragen: Plan_Hebel (Paketplan, Regeln), Memory `feedback_nb_aenderungen_buendeln`.

# E-98 · Bündel P11 + O45: Wallet-Abgleich und Charts (11.10.2026)

**11.10.2026** · Nutzer: *„ja Bündelung ist ok – nur Hinweis zu RSI und MACD – das sollen schon Charts sein“*, Auswahl **Woche + Tag**.
- **P11:** lesende Wache, Bitpanda-Hebel-Wallets gegen `hebel_positions` (O36 Schritt B). Der Importer-Fix kommt als P11b getrennt (Schreiber).
- **O45:** Wochen- und Tageschart (Kerzen, RSI 14, MACD 12/26/9) als Bilder in der REGEL0-Signalmail und der H15-Mail. Die Spot-Mails folgen mit ihrem Bau.
- **Eigene Festlegungen (fachlich, berichtet):**
  - O45 im Bündel trotz Mailänderung, weil additiv, mit P-8 und eigener Kennung – vom Nutzer bestätigt;
  - Woche Mo–So UTC wie Binance;
  - nur abgeschlossene Kerzen, nach der Uhr;
  - gezeigt werden 104 Wochen bzw. 180 Tage;
  - Umrechnung in EUR über `eur_je_usd`;
  - Meldung erst nach zwei Läufen (Zeitversatz 15/30 min), Sperre 6 h.
- Nachweis: Plan G-T/G-U, Schritt7 §23.44.

# E-99 · Neuer Hebel-Tab (P12, 11.10.2026)

**11.10.2026** · Nutzer: *„1. bis GUI-4 doppelt lassen 2. aus der GUI entfernen“*.
- Der Hebel-Schalter steht bis GUI-4 im Hebel-Tab **und** in der Watchlist, über denselben Schreibweg.
- Der alte Hebel-Tab (Altlisten, gesperrte Analyse, Signal-Historie der alten Kette) ist aus der GUI genommen; der Code bleibt.
- **Eigene Festlegungen (fachlich, berichtet):**
  - neuer Tab als eigene Datei (die Prüfungen auf die alte bleiben gültig);
  - Filter *nur Schalter an* über den Schalter **zum Signalzeitpunkt**;
  - H15 nur bei sichtbarem Unterreiter, höchstens alle 60 s;
  - Vorgabe-Filter *7 Tage + nur Schalter an*.
- Nachweis: Plan G-V/G-W, Schritt7 §23.45.

# E-100 · Spot B1 Mitnahme ×3 gebaut (P14, 11.10.2026)

**11.10.2026** · Nutzer: *„Ja, B1 jetzt bauen, prüfen und gegenprüfen“*. Die Konzeptprüfung *„auf Herz und Nieren“* findet **vor** B3/B4/C1 statt (Vorschlag §41.7, mit dem Bauauftrag angenommen).
- Regel wie gemessen (§31, Übertragbarkeit §39.6: trägt auf dem ganzen Bestand). Kreis = alle Krypto-Bestände ohne Kern/Stablecoins (E-90), Starttag Altbestand = Inbetriebnahme (A1 a).
- **Eigene Festlegungen (fachlich, berichtet):**
  - eine Kursquelle für alle Bestände (`price_history_ohlc`, Dollar, ohne rekonstruierte Zeilen);
  - Sprung ≥ 2 × → *zu prüfen*;
  - Auslösung älter als 3 T → *verpasst*;
  - Treffer am letzten Fenstertag → keine Mitnahme (wie die Messung);
  - Job 07:10;
  - Schalter aus, bis du einschaltest;
  - Kosten D6 nur als Information, ohne Klassen-Schätzung.
- Nachweis: Spot §41.8, Schritt7 §23.46.

# E-101 · Spot B4 Abbau-Reihenfolge trägt in Dollar — Bau freigegeben (11.10.2026)

**11.10.2026** · Nutzer: *„B4 ja“*.
- B4-Vormessung (Spot §43): unteres Fünftel −12,5 Pp Dollar in 12 M gegen Zufall der Klasse (beständige Nullwelt, Rang 0,000), in jeder Klasse und jedem Jahr negativ; Gegenprobe 4/4.
- Der Selbsttest scheiterte zuerst an **meinem** Planparameter (40 Ziehungen: 5 % rechnerisch unerreichbar). Korrigiert wiederholt (200 × 1.000): **4,5 %**, bestanden.
- Bau nach §39.7 mit Belegstufe in Dollar. Vorher B4-Voranalyse mit Universum NB (§42.1) und D3.

# E-102 · Spot: Einstieg je Asset mit freien Daten nicht belegbar — Befund (12.10.2026)

**12.10.2026** · Messung U2/U1 (Spot §46.4–46.6, Nutzer 11.10.: *„Messung U2/U1 laufen lassen, prüfen und gegenprüfen“*).
- Gebühren-Wachstum gegen Kurs (U2) **schadet** absolut (−4,6 Pp gegen BTC in 30 T), ist gegen Zufall derselben Klasse nicht besser (Rang 0,82).
- Stablecoins je Kette (U1) **trägt nicht** (−4,0 Pp, Rang 0,97).
- Die Anlage löst +3 Pp in ≥ 90 % auf: Es fehlt der Effekt, nicht die Auflösung.
- Zusammen mit §35, §37, §38, §40, §44, §45: **Mit freien Daten ist ab 2024 kein Einstieg je Asset belegbar.**
- Folge (vorab): Der Spot-Kauf bleibt eine Marktlage-Entscheidung (Ampel C1) mit geordneter Kandidatenliste (A3); die Führung (B1, B3, B4) trägt.
- O46 erledigt; U7, U3, U6 nur noch als Beobachtung, keine Messrunde vor dem Bau der Führung.

# E-103 · Bündel P15 Bestand-Tab + P16 Spot B3 Upbit gebaut (12.10.2026)

**12.10.2026** · Nutzer: *„Ja, den Ausbau eindeutig kennzeichnen, damit man nicht über den alten Code stolpert“*.
- **P15:** Tab *Bestand* ersetzt *Portfolio*. Der Knopf *Letzte Bewertung* (Rollen-Kette, angehalten seit 05.10.) ist **ausgebaut**. Abgelöster Code ist in `portfolio.py`, `letzte_bewertung.py`, `app.py` und im Inventurblatt gekennzeichnet; die Suite wacht darüber.
- **P16:** Upbit-KRW-Listing eines L-Bestands → Mail *„X verkaufen“* (ganze Position, ≤ 6 h). Regel wie gemessen (Teil 0: 137 gleich). Schalter `spot_upbit_aktiv` **aus**, bis du einschaltest.
- **Eigene Festlegungen (fachlich, berichtet):**
  - Startmarke beim ersten Lauf;
  - Zuordnung nur über `symbol_zuordnung` Faktor 1;
  - Futures-Start erst mit P18;
  - der Hinweis *außerhalb* richtet sich nach Binance-**Spot** — das korrigiert auch B1 (Fund der Gegenprobe G4).
- Nachweis: G-Z, Spot §47.6, Schritt7 §23.47.

# E-104 · Makro-Umfeld gemessen: nicht entscheidbar; Nullwelt N1 ersetzt (14.10.2026)

**14.10.2026** · Nutzer: *„JA – finde ich gut“* (Messplan §51.5, gemeinsame Makro-Grundlage, Urteil nur Krypto) · *„ja starten“* (Hauptmessung).
- **Ergebnis:** Kein Kanal ist für BTC oder Altcoins belegt (0 von 60). Das Urteil lautet *nicht entscheidbar*, weil die Auflösung nicht reicht (gepflanzt +42 % nur in 23 % gefunden). Beste Kandidaten: Netto-Liquidität kurz und Dollar kurz.
- **Eigene fachliche Festlegungen (berichtet):**
  - Die Nullwelt N1 aus dem Plan (zirkuläre Verschiebung) ist **verworfen**, weil ihr Selbsttest fiel (9 statt 0,8 Fehlalarme).
  - Ersatz ist die Surrogat-Nullwelt N2 (gemeinsame Phasen-Randomisierung der Kanäle). Sie ist bei BTC selbst noch zu großzügig; das stützt das Urteil *nicht belegt*, weil eine strengere Nullwelt nur weniger findet.
  - Das Urteil selbst (Bonferroni, Epochen, Spiegelprobe) ist **unverändert**.
  - Gegenprobe 7/7 (Mittelrang).
- **Folge (vorab):** Das Umfeld wird Fakt-Anzeige, kein Gewicht, kein Auslöser, kein Blocker. Die Kandidaten werden vorwärts beobachtet.
- **Gold:** Die Nutzerthese *Vertrauen in Fiat* ist mit den neun Kanälen nicht abgebildet. Vorschlag K10 als Auskunft, zur Abstimmung.
- Nachweis: Spot §51.7, Regelwerksmanual R-R14.

# E-105 · Währung des Vergleichs und Maßstab gewinnbringend (14.10.2026)

**14.10.2026** · Nutzer: *„für mein Fiat Euro als Vergleich, für den Markt Dollar“* · *„gewinnbringend wäre u. U. bereits, wenn man die Inflation schlägt, also nicht investiert ist“*.
- **Entschieden:** Gemessen wird in **Dollar**, bilanziert für den Nutzer in **Euro**. K10 *Vertrauen in Fiat* kommt als Messplan Fassung 2 (Markt in Dollar, Euro-Kaufkraft als Auskunft).
- **Eigene fachliche Festlegungen (berichtet):**
  - Inflation = HICP Euroraum. Risikolos = €STR, beides frei bei FRED.
  - Bilanz in log-Ertrag, denn das ist der geometrische Ertrag und enthält den Schwankungsabschlag.
  - Kosten in der Bilanz, nicht in der Bewertung (Regel 2). Steuern sind Auskunft.
- **Vorschlag, offen:**
  - *gewinnbringend* = schlägt H1 Inflation;
  - *lohnt als Auswahl* = schlägt zusätzlich BTC;
  - Rückgang und Schwankung als Auskunft.
- Nachweis: Spot §51.8.

# E-106 · Thesen und Maßstab geprüft: H-SEL-B nicht erfüllt, Maßstab Fassung 2, Umdenken vorgeschlagen (14.10.2026)

**14.10.2026** · Nutzer: *„Ja – prüfen wir diese Thesen und den Maßstab … sonst müssen wir umdenken“*.
- **K10:** Die Vorprüfung schließt die lange Messung aus. Als Fakt bleibt der Bruch Gold ~ Realzins (Beta −0,38 → +0,20).
- **Inventur** (Euro, nach Kosten, ab 2024): Keine geprüfte Regel schlägt die Inflation.
  - Universum −56 % je 12 M, beste Auswahl −49 %, Rang gegen Zufall 0,94;
  - Führung X2 −12 %; B4 sicher schlechter als Zufall.
- **Eigene fachliche Festlegung (berichtet):** Maßstab **Fassung 2** = Beleg gegen eine gleich große Zufallsauswahl + Bilanz H1/H2/H3 als Fakt. Grund: Eine Hürde allein belegt keine Auswahlfähigkeit. 12 M ab 2024 sind nur 20 überlappende Fenster.
- **Zur Entscheidung (Umdenken):**
  - U-A Altcoins: Schutz statt Auswahl;
  - U-B Anteil statt Auswahl (als Fakt mit Hürden-Bilanz);
  - U-C H-SEL-B Fassung 2 als Ausschluss, S2 Angebot zuerst.
- Nachweis: Spot §51.10, `p50_inventur.py`, `p51_k10.py`.

# E-107 · Ordnung × Regime gemessen: Schutz belegt, kein Regimeschalter (15.10.2026)

**15.10.2026** · Nutzer: *„ja machen wir so“* (Messplan §52.1 vorab, danach U-C).
- **Ergebnis:**
  - 0 von 24 Prüfungen kehren um, 0 von 12 Interaktionen sind auffällig.
  - Das untere Fünftel (B4) ist bei der typischen Münze in 4 von 6 Regimezellen sicher schlechter als Zufall.
  - Das obere Fünftel liegt überall gleichgerichtet, ist aber nicht belegt.
  - Das Niveau hängt stark am Regime: E3 Altcoins −35 % gegen BTC +24 % je 12 M.
- **Eigene fachliche Festlegungen (berichtet):** B4 bekommt **keinen** Regimeschalter (kein Umkehrbefund). Das Niveau je Regime wird Fakt-Anzeige (U-B). Selbsttest bestanden (3 von 4.800), Gegenprobe 28/28.
- **Nächster Schritt:** U-C S2 Angebot, zuerst Datenquellen-Inventar und Abdeckung (Regel *Datenquellen vor dem Bau*).
- Nachweis: Spot §52.2.

# E-108 · U-C S2 Angebot: Datenlage und Vorprüfung (15.10.2026)

**15.10.2026** · Nutzer: *„ja machen wir so“* (U-C nach Ordnung × Regime).
- **Datenquellen:** Ab 2024 gibt es keine freie Quelle (CoinGecko und Coinpaprika nur 365 T, CoinMetrics ohne die neuen Token, DefiLlama-Freigabepläne kostenpflichtig). Möglich ist der Querschnitt 09/2025 bis 09/2026.
- **Vorprüfung:**
  - Die stärkste Verwässerung liegt bei −7,4 log-Pp in 90 T (p 0,0005), die geringste bei +6,4 (p 0,002), jeweils in 6 von 6 Monaten.
  - Weder Alter noch Kursbewegung erklären es. Der Selbsttest ist bestanden.
- **Eigene fachliche Festlegungen (berichtet):**
  - Kein Urteil und keine Regel vor einem zweiten Regime; volle Messung ab 10/2027.
  - Die Datenhaltung läuft über die NB-Fortschreibung und den Desktop-Vollabruf vor 09/2027.
- **Vorschlag, offen:** *Verwässerung 90 T* als Fakt im Mouseover (Paket mit Voranalyse, am NB ab ~12/2026).
- Nachweis: Spot §53.

# E-109 · P22 Verwässerung als Fakt gebaut (15.10.2026)

**15.10.2026** · Nutzer: *„Ja, hätte gerne immer die Verwässerung auch beim Kauf … P22 bauen, prüfen und gegenprüfen.“*
- **Gebaut:** Faktenzeile in B4, B1, B3 und REGEL0 (Kauf), Statusseite, Teilexport. B4-Regel bitgleich. Prüfstand 9/9, Suite 6/6.
- **Eigene fachliche Festlegungen (berichtet):**
  - Fünftel mit Mittelrang wie in der Messung.
  - Zwischen den Stichtagen gilt der Wert **heute**, eingeordnet an den Grenzen des letzten Stichtags (Grund: TAO sprang in drei Wochen von 0 auf +18 %).
  - Keine eigene Mail.
  - „Beim Kauf“ = REGEL0, weil es eine Spot-Kaufmail nicht gibt (E-102).
  - Diagnose: zwei Lesefehler der Mengendatei behoben.
- **Offen, zur Entscheidung:** USB-Ergänzung, P22c Freigabe-Rhythmus als Fakt, P22b Coins außerhalb Binance.
- Nachweis: Spot §54.6/54.7, Schritt7 §23.49.

# E-110 · Ergänzung der NB-Mengendatei und P22c Freigabe-Rhythmus gebaut (15.10.2026)

**15.10.2026** · Nutzer: *„Ja, USB-Ergänzung bauen, P22c danach.“*
- **Ergänzung:** Übertragung über den Drive-Austauschordner statt USB (öffentliche Daten, keine Geheimnisse; USB bleibt möglich). Am NB fügt der Einspieler nur ältere Tage in die markierte Betriebskopie ein und sichert vorher. Prüfstand 7/7.
- **P22c:** Rhythmus der Freigaben als Fakt der Vergangenheit mit der rückgeprüften Trefferquote. Prüfstand 6/6.
- **Eigene fachliche Festlegungen (berichtet):**
  - Die Mail nennt die mit dem laufenden Code reproduzierte Quote (wöchentlich 77 % statt 74 % aus p55; Mindestlänge 30 T).
  - Kein Satz ohne laufenden Rhythmus.
  - „Fällig gewesen“ ab 3 T Überschreitung.
- Nachweis: Spot §54.8, §55; K-UE-1.

# E-111 · P22b Variante B gebaut; Feature-Wunsch O51 (15.10.2026)

**15.10.2026** · Nutzer:
- *„Ja, Variante B bauen, prüfen und gegenprüfen.“*
- *„Merke dir noch ein Feature für die neue oder alte Watchlist: Assets wieder entfernen und nicht nur ausmustern.“*

**Gebaut:** Coins außerhalb Binance stehen in einer eigenen Zusatztabelle. Nur die Verwässerung liest sie; B4-Klassen und turnover bleiben bitgleich. Der NB-Job holt die Historie selbst.

**Eigene fachliche Festlegungen (berichtet):**
- Stablecoins werden an der Kursruhe erkannt (dieselbe Regel wie B4), Cash-Äquivalente der Watchlist sind ausgenommen.
- Ein Abruffehler ist kein Urteil.
- Höchstens 20 Erstabrufe je Lauf.
- Die Hauptreihe hat Vorrang vor dem Zusatz.

**O51:** Watchlist-Assets entfernen statt nur ausmustern. Gemerkt, Voranalyse folgt.

Nachweis: Spot §57.1, Schritt7 §23.50, K-UZ-1.

# E-112 · Flughöhe: Termin als Fakt, Reihenfolge, W1 (a) (15.10.2026)

**15.10.2026** · Nutzer:
- *„Makro-Regime ist grundsätzlich für alle Assets relevant und sollte eine Rolle spielen.“*
- *„CPI … als Terminangabe relativ sinnfrei ohne Werte.“*
- *„W1 – warum sollten wir den Prüfblock jetzt aus der Mail entfernen?“*
- *„Entscheide du.“*

**Eigene Festlegungen (berichtet):**
- **Reihenfolge:** zuerst *Termin mit Wert* (Hebel), dann *Makro als Risiko-Bremse*; O51, W1 und die Terminzeile gebündelt zum nächsten NB-Pull.
- **W1:** Variante (a). Der Prüfblock bleibt, markiert *„gemessen: trennt nicht – nicht danach handeln“*. Er löst nichts aus, und die Messung im Betrieb läuft weiter.
- **Makro:** nicht über die Richtung, sondern als Risiko-Bremse (ungleich: nur kleiner, nie größer). Die Stärke kommt aus der Messung.
- **Ergebniserwartung durch ein LLM:** abgeraten. Die Prognosequellen werden nur auf eine freie Historie geprüft.
- **Termin** (Vorprüfung §23.53): als Fakt mit gemessenem Ausschlag in die REGEL0-Mail, **nicht** als Gewicht. Bau nach Ja.

Nachweis: Schritt7 §23.53, Plan O51–O53.

# E-113 · Bündel O52/O51/W1 gebaut; Entfernen nur ohne Bestand (15.10.2026)

**15.10.2026** · Nutzer:
- *„OK“*.
- *„Assets entfernen – ja, nur für Assets, welche nicht im Bestand sind und aus der Beobachtung fallen sollen.“*
- *„Du hast ein DB-Backup, wenn dir Daten fehlen.“*

**Festlegungen:**
- **Entfernen:** gesperrt bei Bestand (frei + gestakt) und bei offener Hebelposition. Ist die DB nicht lesbar, wird ebenfalls gesperrt.
- **Gelöscht wird nichts:** Signale, Kurse und Historie bleiben, und erneutes Hinzufügen hebt das Entfernen auf.
- Die Terminzeile ist ein **Fakt mit Messwert, kein Gate**. Das Fenster beginnt 2 h vor dem Einstieg, weil der gemessene Ausschlag 2 h dauert.
- **Fehler behoben (berichtet):** FRED lieferte bisher nie einen künftigen Termin.
- **Backup:** Die NB-Sicherungen im Austauschordner werden nur als Wegwerf-Kopie auf D: gelesen und danach gelöscht.

Nachweis: Schritt7 §23.54, Plan O51/O52, K-TM-1.

# E-114 · O54 Makro-Lage: Statusseite oben + jede Handlungsmail (15.10.2026)

**15.10.2026** · Nutzer:
- *„Ja zu O54 auf der Statusseite als Bereich oben“*;
- *„was ist mit der GUI im Bereich Regime, was ist hier geplant?“*

**Gebaut:**
- Makro-Lage lang/kurz als **Fakt**, dieselbe Rechnung wie die Messung §51.7, kein Gate.
- Ganz oben auf der Statusseite und als Zeile in REGEL0 und B1/B3/B4.

**GUI:** Der Reiter *Regime* zeigt die alte Kette (Stand 14.08.); sein Override wirkt auf nichts. Geplant (10.10., Ja) ist *Markt (Krypto)* in GUI-Stufe 2. Die Makro-Lage kommt dort als Abschnitt hinzu.

**Berichtet:**
- Fehler im eigenen Bau: Ein zu kurzer Abruf zeigte *kurz Gegenwind*, richtig ist *neutral*.
- Gefunden im Prüfstand, vor dem Commit.

Nachweis: Schritt7 §23.57/§23.58, K-ML-1.

# E-115 · P11c Hebelführung folgt dem Wallet-Abgleich; P11b als Nächstes (16.10.2026)

**16.10.2026** · Nutzer:
- *„die Hebelführung funktioniert nicht korrekt, ETH ist bereits geschlossen und BTC verringert worden“*;
- *„Ja, Schritt 1 bauen“*;
- *„ETH wurde vorgestern in der Nacht ausgestoppt und BTC gestern Nachmittag“*.

**Gebaut:** Die Hebelführung (Mail, Statusseite, GUI, Deckel) führt die Positionen gegen die Bitpanda-Wallets. Laut Wallet geschlossene werden nicht mehr gemeldet; abweichende Mengen kommen aus dem Wallet.

**Eigene Festlegungen (berichtet):**
- Korrigiert wird **nur bei frischem Wallet-Stand**, also nie gegen eine eben eröffnete Position, die das Wallet noch nicht kennt.
- Der **Kredit** kommt aus dem Wallet, wenn nur eine Position offen bleibt, sonst anteilig.
- Der **Einstand** bleibt der gespeicherte.
- Die gespeicherten Positionen werden **nicht** verändert; die Datenkorrektur gehört zu P11b.

**Nächster Schritt:** Voranalyse P11b. Bitpanda führt jede Eröffnung als eigene Teilposition (Rohbuchungen 14./15.10.).

Nachweis: Schritt7 §23.59, K-HF-W1.

# E-116 · P11b Hebelpositionen als Buch je Symbol gebaut (16.10.2026)

**16.10.2026** · Nutzer: *„Ja, mach noch zur Sicherheit eine Prüfung, ob alle Stellen im Code und laut Doku abgedeckt sind“* · *„prüfen und gegenprüfen und Doku“*.

**Gebaut:** `hebel_positions` wird aus dem Buch je Symbol der neuen Bitpanda-Schnittstelle gefüllt, eine Zeile je Lebenszyklus. Die alten 191 Zeilen sind gesichert (`hebel_positions_alt_bis_16_10`); der alte Importer läuft nur noch, solange nicht umgestellt ist.

**Eigene Festlegungen (berichtet):**
- Das ganze Buch wird bei jedem Lauf neu durchgerechnet (deterministisch, ohne Zustandsfehler).
- Geschlossene Zeilen tragen die Werte vor dem letzten Abgang.
- Der Status heißt `liquidiert`, weil er ausdrücklich von Bitpanda kommt; die alten Zeilen behalten `wahrscheinlich_liquidiert`.
- Eine unvollständige erste Historie stellt **nicht** um.

Nachweis: Schritt7 §23.60/§23.61, K-HB-1, Paket Hebelbuch.

# E-117 · W3 Regime kurz als Gewicht für REGEL0: Vorprüfung NEIN, bleibt Auskunft (16.10.2026)

**16.10.2026** · Nutzer: *„ja alle vier Zeilen sind in der Mail, weiter mit W3“*.

**Eigene Festlegungen (berichtet):**
- **Keine neue Vollmessung.** BTC 24/72/120 h (2.670) und 30 T (2.686) sind schon gemessen; dazu gilt die Abbruchregel vom 29.09. (W2 ist die letzte Wettermessung). 7 T liegt dazwischen.
- **Stattdessen eine Vorprüfung als Auskunft**, vorab festgelegt und committet (§23.62): ein Merkmal (BTC 7 T), vier Mengen, zweiseitig, Tagesblock.
- **Ergebnis:** 0 von 4 Mengen über der Weiter-Schwelle ⇒ **NEIN**. Das Vorzeichen wechselt von 2025 auf 2026 (Gegenprobe 3/3 gleich). Keine Umkehr ⇒ keine Sperre.
- **Berichtigt:** Die z-Werte in §23.52 waren naiv (−5,2 / +3,6). Mit Tagesblöcken sind es −1,8 / +1,3.
- **Folge:** Flughöhe Ebene 2 bleibt **Auskunft**. REGEL0 unverändert, keine Mail-Zeile, kein NB-Pull. Weiter mit P19 und der Hauptlinie.

Nachweis: Schritt7 §23.62, `p60_w3_vorpruefung.txt`, `p60_gegenprobe.txt`.

# E-118 · P19 Season-Ampel als Fakt gebaut, Marktscan ruht (17.10.2026)

**17.10.2026** · Nutzer: *„ok weiter mit P19 – hast du alles geprüft und gegengeprüft?“*. Abgestimmt war der Bauumfang am 14.10. (*„Ja passt vorerst“*, Spot §49.3).

**Stand-Prüfung vor dem Bau** (Spot §49.5): Voranalyse und Gegenprobe gelten weiter. Neu: DefiLlama ändert die Stablecoin-Reihe rückwirkend (Stand an 8 Tagen anders, Stufe an keinem). Die Makro-Lage (O54) holt M2 und die Netto-Liquidität schon am NB.

**Eigene Festlegungen (berichtet):**
- Die Stablecoin-Reihe wird je Lauf ganz geholt. Ein Wechsel zählt nur gegen die zuletzt **gemeldete** Stufe, sodass eine Revision keinen Scheinwechsel erzeugt.
- FRED über `makro_lage.hole_reihe` statt eines eigenen fredgraph-Nachladers.
- GUI nach dem abgestimmten Zielbild G2: Reiter **Spot** und **Markt (Krypto)**; *Regime* bleibt bis GUI-5.
- Mail-Zeile ohne Netto-Liquidität (steht als K2 schon in der Makro-Zeile).
- Mail beim Stufenwechsel gebaut, Schalter `season_ampel_aktiv` **aus**, bis O47 Schritt 2 vorliegt (§49.4). Mit Schalter aus wird ein Wechsel protokolliert und beim Einschalten **nicht** nachgeholt.
- **O43:** `marktscan.aktiv: false` (Nutzer 10.10.: *„JA“*).

Nachweis: Spot §49.5/§49.6, `p19_pruefstand.txt` 12/12, `p19_bau_gegenprobe.txt` 3/3, `p18_pruefstand.txt` 13/13, Paket SeasonAmpel; K-SP-4, K-GUI-7, K-MS-1.

# E-119 · P11d: 'nachgeholt' ist kein Fehler – eigener Betreff (17.10.2026)

**17.10.2026** · Nutzer: *„ja P11d noch bauen und mit in den Pull“*.

**Gebaut:**
- Der Stundenlauf gibt die **Art** der Meldung mit aus (`veraltet_gemeldet`, `nachholen_ausgelassen`, `nachgeholt_signale`).
- Hat die Rechnung nach einer Unterbrechung **nur** Stunden nachgeholt, heißt die Mail *„REGEL0 nachgeholt (n Std.) – Rechnung erfolgreich“* und nennt Stunden und Signale.
- **Datenbasis veraltet** oder eine **nicht nachholbare** Stunde bleiben *„Job 'regel0_rechnung' fehlgeschlagen“*, auch gemischt mit *nachgeholt*.
- Der Spam-Schutz gilt je Art getrennt: Eine Nachgeholt-Mail hält einen echten Fehler nicht zurück.

**Eigene Festlegung (berichtet):** Die Mail bleibt, wie geplant, aber als Auskunft. Die Handlung bei einem Stillstand kommt aus der Stillstandsmail (K-ALARM-2).

Nachweis: `p11d_pruefstand.txt` 7/7 (darunter der echte Fall vom 16.10. 18:30), `p11d_gegenprobe.txt` (66 NB-Läufe, 0 Abweichungen); Paket Nachgeholt; K-NG-1.

# E-120 · O21 Stufe 1 gebaut: Messstand im Betrieb, Zeile sofort in der Signalmail (17.10.2026)

**17.10.2026** · Nutzer: *„ja A1 bis A6 bauen, finde die Zeile für den Messstand sollte sofort vorhanden sein“*.

**Gebaut:** laufende Ergebnismessung jedes REGEL0-Signals (gleiche Rechnung wie die Messung), Messstand mit Spanne über Tage, echte Trades gegen ihr Signal, Prüfblock gegen den Ausgang; Statusseite, Teilexport, Diagnose; **Zeile *Messstand im Betrieb* in jeder REGEL0-Signalmail**.

**Eigene Festlegungen (berichtet):**
- **Befund und Anzeige auf dem 99-%-Band**, Befund erst ab 10 Tagen. Grund: Selbsttest – mit 95 % meldete der Befund bei einem Betrieb genau wie die Messung zu oft eine Abweichung (10 T 12,5 %); mit 99 % höchstens 4,9 %.
- Die Zeile nennt immer Signale, **Tage**, Spanne und den Satz *„ob der Vorteil die Kosten (0,48 %) schlägt, ist so erst nach Jahren entscheidbar“*, damit sie nicht genauer wirkt, als sie ist.
- Label *Messstand im Betrieb* (nicht *Messstand* – so heißt die Zeile des Prüfblocks).
- Echte Trades nur als Fakt (Signal, Verzug, Haltedauer); das Ergebnis in EUR ist Stufe 1b.

Nachweis: Schritt7 §23.64/§23.65, `o21_pruefstand.txt` 9/9, `o21_gegenprobe.txt`, Paket Messstand; K-O21-1.

# E-121 · M1 und B1/B2: gemailte Signale zuerst, Hebel-Ergebnis in EUR in der Mail – Wert zum Schlusskurs, nie „realisiert“ (17.10.2026)

**17.10.2026** · Nutzer: *„ja M1 und B1/B2 bauen, EUR-Ergebnis auch in die Mail – bei Hebel Vorsicht … der Verlust wird in Ö erst bei Verkauf in Fiat realisiert“* und das Bild *EURCV Gesamtverlust −50,64 %*.

**Gebaut:** Messstand mit den gemailten Signalen zuerst (M1); je echtem Hebel-Trade Eigenkapital, Wert zum Schlusskurs, Gebühr und Ergebnis in EUR mit den Wachen P1–P4 (B1); Statusseite, Teilexport und eine zweite Zeile *Deine Hebel-Trades* in der REGEL0-Signalmail (B2).

**Eigene Festlegungen (berichtet):**
- Das Ergebnis heißt **„Ergebnis zum Schlusskurs“**; das Wort *realisiert* kommt nicht vor, eine steuerliche Einordnung auch nicht.
- Die Zeile sagt, warum Bitpanda das Minus beim **EURCV** zeigt: Das Eigenkapital ging als EURCV hinaus, der Rest kam als Coin zurück.
- Ein Zyklus, dessen Buchungen die Wachen verletzen, bekommt **kein** Ergebnis (*NICHT berechnet*).

Nachweis: Schritt7 §23.66/§23.67, `o21_pruefstand.txt` 13/13, Paket Messstand; K-O21-2.

# E-122 · Spot-Mails: „verkaufen oder in EURCV tauschen“ (17.10.2026)

**17.10.2026** · Nutzer: *„ja zu deinem Vorschlag zum Verkauf“* (er tauscht oft in EURCV statt in Fiat zu verkaufen).

**Gebaut:** B1, B3 und B4 nennen beide Wege, *verkaufen oder in EURCV tauschen*, mit dem Satz, dass die Wahl beim Nutzer liegt und gemessen der Ausstieg aus dem Coin ist. Die Regeln sind unverändert, eine steuerliche Aussage gibt es nicht.

Nachweis: Spot §58; P14 10/10, P16 12/12, P18 13/13; K-SP-5.

# E-123 · E1–E3: Haltedauer als gemessener Fakt in der Positionsführung (18.10.2026)

**18.10.2026** · Nutzer: *„ja E1 bis E3 bauen“*.

**Gebaut:**
- **E1:** Die 24-h-Ausstiegserinnerung nennt den Fakt aus §23.68 und die Liquidationsnähe der Stufe.
- **E2:** Ist die Position 72 h nach dem Einstieg noch offen, kommt **einmal** eine zweite Erinnerung mit Haltedauer, H15-Führung und Fakt.
- **E3:** Die Hebelführung (H15-Mail, Statusseite, Diagnose) nennt je offener Position *„seit n h offen (Regel 24 h)“* mit dem zugehörigen REGEL0-Signal oder *„eigene Entscheidung“*.

**Eigene Festlegungen (berichtet):**
- Fakt, kein Gate.
- E2 nur nach verschickter erster Erinnerung.
- E2 entfällt endgültig bei keiner offenen Position oder wenn die Position schon vor dem Signal offen war.
- Zuordnung wie `trades()`, sekundengenau.

Nachweis: Schritt7 §23.69; `e123_pruefstand.txt` 39/39, `e123_gegenprobe.txt` 15/15 (echte NB-Kopien); Paket Haltedauer; K-HD-1.

# E-124 · Season-Ampel: Mail beim Stufenwechsel eingeschaltet, Vorbehalt „zwei Zyklen“ (18.10.2026)

**18.10.2026** · Nutzer: *„ja E-124 umsetzen“*, nach O47 (Spot §59).

**Grundlage:** Der Holdout 2017/18 trägt (Season-Klima 76 % Season-Wochen, kalt 0 %, Ruhe im Absturz 2018). Einschränkungen:
- Der Beginn wird nicht genau vorab erkannt (2016/17: 19 T danach).
- Die Trennung kommt vor allem aus dem Regime.
- B3 trägt vor 2021 nichts Eigenes bei.

**Umgesetzt:**
- Schalter `season_ampel_aktiv` an (`regel0_betrieb.yaml`).
- Vorbehalt *„geprüft an zwei Zyklen (2017/18, 2020/21) – trennt Season-Phase und Bärenmarkt, erkennt den Beginn nicht genau vorab“* in Zeile, Mail, Statusseite und Reiter.
- §36.4 K4 berichtigt.

**Nicht:** keine Ampel in den REGEL0-Mails (für den Hebel nicht messbar, §59.12).

Nachweis: Spot §59.14; `p19_pruefstand.txt` 14/14, `p19_bau_gegenprobe.txt` 3/3; K-SP-6.

# E-125 · Bilanz der LLM-Komponente: kein messbarer Mehrwert auf allen geprüften Wegen (21.10.2026)

**21.10.2026** · Nutzer: *„Die LLM-Komponente sollte einen Mehrwert liefern – was wir offenbar nicht schaffen … Wenn sich das als Deadend herausstellt, brauchen wir das System so nicht weiterverfolgen. Halte alle Ergebnisse fest. Danach Recherche Grid-Trading.“*

**Festgehalten:** `Bilanz_LLM_Komponente_21_10.md`. Elf geprüfte Wege, keiner trägt:
- Urteil über Zahlen (N4, N5, A2);
- Entscheider;
- Regime als Gewicht;
- Ereignisse als Fakt (E-1);
- Asset-Nachrichten (L-C);
- Marktnachrichten (L-C2).

Der Engpass ist die **Information**, nicht das Modell. Dazu kommt ein Kontaminationsbefund: Gemini kennt 2025. Daraus folgt ein Vorbehalt für N4/N5.

**Betrieb:** unverändert, der Prüfblock bleibt markiert *„trennt nicht“*. Die Entscheidung über die Komponente und das System liegt beim Nutzer.

**Nächster Schritt:** Recherche Grid-Trading (BTC und ein Altcoin).

# E-126 · Börse und M-A: Fusion ist steuereinfach; die Trendallokation BTC ↔ EURCV trägt nicht (21.10.2026)

**21.10.2026** · Nutzer: *„recherchiere ob FUSION auch steuereinfach ist“* · *„ja M-A Voranalyse starten, Messplan vorab festlegen“* · *„ja Messplan so festlegen, prüfen gegenprüfen und doku“*

**Börse (Fakt, Bitpanda-FAQ *Tax Withholding in Austria*):**
- **„Bitpanda Fusion Trades“** stehen dort unter dem **automatischen KESt-Abzug**.
- Fusion hat *„One balance. One account.“*, eine API mit Handelsrecht und Gebühren von 0,25 % bis 0,02 % je nach Volumen der letzten 30 Tage.
- Krypto→Krypto-Tausch (auch in einen Stablecoin) ist laut FAQ *„tax-free at execution“*.
- Andere steuereinfache Anbieter (Coinfinity, 21bitcoin) bieten praktisch nur BTC; bei Bybit EU sind die Angaben widersprüchlich.
- ⇒ Für ein Grid braucht es **keine neue Börse**.

**M-A** (Spot §60, Messplan vorab c18e23f2):
- Getestet: R2, 10-Monats-Schnitt, BTC ↔ EURCV, in EUR, Teil A 2011–2016 und Teil B 2017–2026.
- Ergebnis: **trägt nicht**; S1–S4 alle nein, Gegenprobe 7/7.
- Kern ist das Verspätungsproblem aus F1:
  - Ausstieg 54–158 T nach dem Hoch (−28 bis −81 %), Wiedereinstieg 50–199 T nach dem Tief (+30 bis +176 %);
  - die Monate draußen waren im Mittel positiv;
  - schnelle Abstürze blieben ganz unberührt.
- Der Rückgang ist kleiner, aber nicht besser als bei zufällig verschobenen Phasen. Teil A kostet Ertrag (0,735).

**Betrieb:** unverändert. **Gesamtbild:** Der Regimewechsel liefert bei BTC weder schnell (2.599) noch langsam (§60) einen Zeitpunkt.

# E-127 · Grid-Trading endet an der Größe: die Rückkehr zur Mitte ist rund zehnmal zu klein für die Gebühr (22.10.2026)

**22.10.2026** · Nutzer: *„ok, können eine kurze Prüfung machen für W-A, dann müssen wir u. U. zurück zu Alternativen oder Bestehendes noch einmal analysieren.“*

**Ergebnis** (`Recherche_Grid_Trading_21_10.md` §9 bis §9.4):
- Gemessen wurde die Varianz-Ratio der Stundenrenditen 2023-09 bis 2026-08: VR(24) BTC 0,952 · ETH 1,030 · SOL 0,918 · LINK 0,940.
- Eine eingepflanzte Rückkehr dieser Stärke bringt einem Gitter **rund 0,02–0,03 % je Ausführung**. Die Fusion-Gebühr liegt bei 0,25 %.
- Selbst bei zehnfacher Stärke (VR 0,55) wären es nur 0,18 %.
- ⇒ **Grid wird nicht weiterverfolgt.** Stufe 2 (1-Minuten-Daten) entfällt.

**Zwei Fehler der Messanlage**, beide vom Selbsttest gefunden, bevor ein Ergebnis bewertet wurde:
- Die Umordnungs-Nullwelt fixierte das Monatsende (Fassung 1 ungültig).
- Die Nullwelt mit Monatsdrift war auf das echte Ende zentriert (Fassung 2 gesperrt).
- Fassung 2b ist unverzerrt, aber für den Rang zu unscharf. Das Urteil kam deshalb über die Auflösung.

**Betrieb:** unverändert.

**Nachtrag 25.10.2026 (E-141, Prüfbericht):** Präzisierung: Fassung 1 war gesehen, bevor ihr Selbsttest lief (Gegenprobe G3). Das Urteil über die Auflösung war nicht vorab geplant; es ist robust, weil selbst die zehnfache Stärke nicht reicht.

# E-128 · Bestandsaufnahme A1: innerhalb der bestehenden Ansätze ist kein Weg offen (22.10.2026)

**22.10.2026** · Nutzer: *„ja A1 Bestandsaufnahme starten … mit Alternativen meine ich nicht nur Anpassungen der bestehenden Strategien, sondern auch neue Ansätze … aber mach zuerst die Prüfung A1.“*

**Ergebnis** (`Bestandsaufnahme_brutto_netto_22_10.md`):
- **Vor** Kosten trägt als Ertrag nur die REGEL0: unverzerrt +0,30 % je Handel gegen 0,48 % Kosten, also eine Lücke von rund 0,18 Pp.
- Keiner der Hebel schließt sie, auch nicht zusammen und auch nicht als Obergrenze in der Rückschau:
  - Fusion ohne Hebel kostet 0,50 %;
  - 12 h halten gibt −0,07..−0,11 Pp, selbst bei stündlicher Finanzierung;
  - die Sperre bei Signalflut bestenfalls −0,04 Pp;
  - beides zusammen −0,03..−0,08 Pp;
  - Informationsmonate (K_IG) und Wucht sind schon gemessen, schwach bzw. ohne Richtung.
- Die Tagesblock-Unsicherheit (±0,5 Pp) ist größer als die Lücke.
- Netto trägt nur **Mitnahme ×3** (Spot), als Schadensbegrenzung. Gegenprobe 4/4.

**Folge:** Es werden keine Anpassungen an bestehenden Strängen weiterverfolgt. Der nächste Schritt sind **neue Ansätze** (Nutzerauftrag). **Betrieb:** unverändert (REGEL0 als Vorwärtsprotokoll mit kleinen Einsätzen).

# E-129 · Recherche neue Ansätze (R-A): Belegt sind Prämien und Bremsen, kein Vorhersage-Vorteil (22.10.2026)

**22.10.2026** · Nutzer: *„ja R-A Recherche starten, prüfen, gegenprüfen und Doku – … bitte im Detail durchplanen und analysieren“*.

**Ergebnis** (`Recherche_Neue_Ansaetze_22_10.md` §5–§7; vier Recherchen, Gegenprüfung 12 Aussagen an Primärquellen, eigene Gegenrechnung):
- **Kein** Ansatz liefert einem Privatanleger einen nachweisbaren Rendite-Vorteil nach Veröffentlichung und Kosten.
  - Krypto-Carry: Prämie seit 2025 eingebrochen, bei Bitpanda nicht umsetzbar.
  - Trendfolge: TSMOM Sharpe 1,41 → 0,41 nach Veröffentlichung.
  - Faktoren nach Veröffentlichung etwa halbiert, über ETFs ≈ 0.
  - Kalendereffekte verschwunden.
  - Paarhandel und Liquiditätsgabe negativ.
- **Belegt** sind:
  - Prämien, die man **hält** (Aktien, Anleihen, Krypto-Beta, Staking);
  - **Bremsen für Rückgänge** (Trendfilter über mehrere Anlageklassen, Volatilitätssteuerung, Diversifikation);
  - niedrige Kosten und wenig Steuerreibung.
- **Engere Wahl:**
  - W1 Multi-Asset-Grundportfolio mit Trendfilter (Risiko, nicht Rendite);
  - W2 Staking-Lücke im Bestand (Fakt);
  - W3 Carry nur beobachten.
- **Nebenbefund:** Die Bitpanda-Margin-Finanzierung wird alle 4 h berechnet (Kostendokument v4.0.0). Damit ist die offene Faktfrage aus E-128 geschlossen, das Urteil bleibt.

**Zur Abstimmung:** Die Wirkung liegt im **Aufbau und in der Führung eines Portfolios**, nicht in Signalen. Das ist eine Änderung der Systemaufgabe. **Betrieb:** unverändert.

# E-130 · REGEL0-Kosten: trägt auf Kraken-Perps (Rückschau), auf Bitpanda nur der Limit-Einstieg mit Vorbehalt (23.10.2026)

**23.10.2026** · Nutzer: *„ja P-A Voranalyse starten, prüfen, gegenprüfen und Doku – ich hätte gerne noch REGEL0 weiter optimiert, bis wir auch auf BP tragen.“*

**Ergebnis** (`Voranalyse_REGEL0_Kosten_23_10.md` §3–§5, Plan vorab 82a1fe89, Gegenprobe 4/5 mit einem inhaltlichen Fehlschlag):
- **P-A Kraken Pro** (Taker 0,05 %, belegt):
  - netto **+0,18 bis +0,28 %** je Handel unverzerrt, positiv in jedem Jahr;
  - Abdeckung 47 % (API-Liste, Kriterium ≥ 50 % knapp verfehlt);
  - nicht steuereinfach, ESMA-Hebelfrage offen.
- **P-O Bitpanda:**
  - Haltedauer im 4-h-Takt und Auswahl nach Schwankung tragen nicht.
  - Der **Limit-Einstieg 1 % unter dem Schluss** liegt über 2025–26 bei +0,11 Pp, **2026 aber negativ** (3 von 4 Mengen).
  - Offene Faktfrage: Gibt es Limit-Orders bei Bitpanda-Margin?

**Betrieb:** unverändert. **Zur Abstimmung:** welcher Messplan (Wahl 2024, Bestätigung je Jahr).

**Nachtrag 25.10.2026 (E-141, Prüfbericht):** **Berichtigt:** „trägt auf Kraken-Perps“ beruht auf Punktwerten. Das Tagesblock-Band (unverzerrt −0,35 bis +0,79 %) schließt die Null ein, und die Abdeckung von 47 % liegt unter dem eigenen Kriterium von 50 %. Richtig ist **nicht entscheidbar**; nach E-139 ohne Grundlage.

# E-131 · M-L: Der Limit-Einstieg trägt auf Bitpanda nicht – REGEL0 schlägt den Markt, aber der Markt fiel (23.10.2026)

**23.10.2026** · Nutzer: *„ja Messplan M-L so festlegen, prüfen, gegenprüfen und Doku“*; Nutzer-Fakt: Bitpanda-Hebel ohne Limit-Kauf, Spot mit Limit.

**Ergebnis** (`Voranalyse_REGEL0_Kosten_23_10.md` §7–§7.2, vorab e6e30261, Fassung 1b nach Selbsttest bacc11d4, Gegenprobe 3/3):
- Auf 2024 gewählt wurde ein Limit 0,5 % unter dem Kurs.
- Bestätigung unverzerrt: 2025 ≈ 0 (−0,05 bis +0,05 %), **2026 −0,21 bis −0,27 %** je Handel.
- Das gilt auf allen Basen (Hebel, Hebel mit Schlupf, Fusion-Spot). ⇒ **trägt nicht**.

**Befund:**
- REGEL0 liegt gegenüber Zufallsstunden derselben Coins um **+0,6 Pp (2025) bzw. +0,3 Pp (2026)** vorn (Rang 1,00).
- Die Altcoins fielen aber im Mittel um −0,28 bzw. −0,13 % je 24 h. **Drift plus Kosten** zehren den Vorsprung auf.

**Betrieb:** unverändert.

**Nachtrag 25.10.2026 (E-141, Prüfbericht):** **Berichtigt:** Der Befund „REGEL0 schlägt den Markt um +0,6/+0,3 Pp, Rang 1,00“ beruht auf einer Nullwelt, die nicht tagestreu ist (30 % Fehlalarm, E-139). Je Tag gewichtet ist der Vorsprung negativ. Das Urteil „trägt nicht“ bleibt.

# E-132 · E-A: REGEL0 als Kaufzeitpunkt geplanter Spot-Käufe trägt nicht; 4-Jahres-Zyklus nur als Fakt (23.10.2026)

**23.10.2026** · Nutzer: *„ja E-A Messplan festlegen, prüfen, gegenprüfen und Doku, auf BP“*, mit vier Hinweisen (Vorwissen, BP, Zeiträume und Zyklen, Regimewechsel).

**Ergebnis** (`Voranalyse_Einstieg_EA_23_10.md`; vorab 4241f1e0, Fassung 1b nach Selbsttest 5d864b99, Ergebnis 5cc2acf0):
- Auf 2024 gewählt wurde ein Fenster von 7 Tagen.
- Gegen Zufallsstunden im selben Fenster liegt REGEL0 2025 auf Rang **0,00**, 2026 auf Rang **1,00**. Das gilt für Kern und Altcoins; die Gegenprobe mit gleicher Wartezeit (G5) bestätigt es.
- Im steigenden Regime liegt der Rang bei 0,03, im fallenden bei 0,99.
- Der Kaufvorteil ist Wartedrift. ⇒ **trägt nicht**; der Kauf am festen Tag bleibt.
- **Vorwissen bestätigt:** M-0c L3 (REGEL0 als Spot-Handel trägt nicht, der Vorsprung ist nach 72 h weg).

**Zyklus** (§6):
- Der Zeitplan hält bisher, die Form weicht ab (−54 %, 8,8 Monate, Boden nicht bestätigt).
- Das Halving als Ursache ist nicht belegt.
- ⇒ Nur als **Fakt** in die Mail, nie als Auslöser (Regel 1).

**Bilanz REGEL0 auf Bitpanda:** Kosten, Auswahl, Limit und Timing geplanter Käufe sind geprüft, und nichts trägt. Getragen hat das Signal nur als 24-h-Handel bei niedrigen Kosten (Kraken, E-130).

**Betrieb:** unverändert.

**Nachtrag 25.10.2026 (E-141, Prüfbericht):** **Berichtigt:** Die Nullwelt war nicht tagestreu, dazu kommt Pseudo-Replikation über die vier Mengen. Die Ränge 0,00/1,00 und Regime 0,03/0,99 sind überzeichnet; „Wartedrift“ und „kippt mit dem Regime“ gelten nur als Tendenz. Das Urteil „trägt nicht“ bleibt.

# E-133 · F-1 Marktfilter für REGEL0: mit 2024–26 nicht entscheidbar – selbst perfektes Timing ist nicht von Zufall zu trennen (23.10.2026)

**23.10.2026** · Nutzer: *„ja F-1 Messplan festlegen … wir sollten breiter denken … die größte Bremse ist offenbar der Gesamtmarkt … Makro und traditionelle Märkte (Nasdaq, Zinsen, Anleihen)“*.

**Ergebnis** (`Voranalyse_REGEL0_Marktfilter_23_10.md`, vorab 590bcdac):
- Sechs Filter aus dem bestehenden Schema: Makro Gesamt kurz/lang, Netto-Liquidität, Dollar, Nasdaq 200 T, BTC 200 T.
- Der **Selbsttest sperrt**: Fehlalarm 0/200 ✔, aber die Positivkontrolle (Orakel-Filter mit Zukunftswissen) erreicht nur Rang 0,92–0,94.
- Verbesserung des Orakels +0,93 Pp gegen P99 der Zufallsfilter +1,43 Pp: 22 Zustandsstrecken in 20 Monaten, Tagesnetto ±5 %.
- ⇒ **nicht entscheidbar**; die Filter sind nicht angesehen.

**Der Nutzerhinweis bleibt richtig:** Der Gesamtmarkt ist die größte Stellschraube (2.598, E-131). Nachweisbar wird er nur mit **mehr Jahren REGEL0-Handel** (Signale 2019–2023 nachrechnen, Download nötig).

**Betrieb:** unverändert.

# E-134 · H-A Voranalyse: Die REGEL0-Historie zu verlängern lohnt für große Markteffekte; Marktphasen auf zwei Ebenen; Indikator-Atlas vorgeschlagen (23.10.2026)

**23.10.2026** · Nutzer: *„ja H-A Voranalyse starten …“*, Hinweise: übergeordnete und kleinere Marktphasen unterscheiden; rückwirkend prüfen, welche Indikatoren in welchen Phasen relevant waren.

**Ergebnis** (`Voranalyse_REGEL0_Historie_23_10.md`, Gegenprobe 4/4):
- **Auflösung:** Mit 2020-06 bis 2026-08 statt 2024–26 steigt die Fundquote für einen Markteffekt von 1,0 Pp von 31 % auf 84 %. 0,5 Pp bleiben schwach (12 % → 30 %).
- **Machbar:**
  - Der Erzeuger `regel0_rechnung --ordner` arbeitet auf einem eigenen Datenordner.
  - ⚠️ Das Monatsmodell lernt fest ab 2023-01; für die Monate vor 2024 braucht es eine dokumentierte Regel. 2024–26 muss bitgleich bleiben.
  - Der Download umfasst grob 0,5–0,7 GB, frei, und braucht ein Ja.
- **Marktphasen BTC:**
  - übergeordnet 6 (4 Zyklus-Bärenmärkte, 2 Einbrüche im Bullenmarkt; der jetzige läuft noch);
  - kleiner 86 Wendepunkte 2013–2026 (24 ab 2020-06, 8 in 2024–26).

**Vorschlag V-1:** erst der **Indikator-Atlas** (Vorlauf je Indikator vor den Wendepunkten, Nullwelt Zufallsdaten, Stabilität 2013–19 gegen 2020–26), dann die REGEL0-Historie und F-1 Fassung 2 nur mit den Atlas-Kandidaten.

**Betrieb:** unverändert.

**Nachtrag 25.10.2026 (E-141, Prüfbericht):** **Berichtigt:** Die Fundquote 31 → 84 % hat ein Streuband von etwa ±9 Pp (Gegenprobe 40 → 77 %). Die Annahme „die REGEL0 feuert 2020–22“ ist durch E-136 widerlegt.

# E-135 · Indikator-Atlas: Geldausweitung ist keine Voraussetzung; kein Makrokanal läuft den BTC-Wenden voraus; Rezession ist die stärkste Größe (23.10.2026)

**23.10.2026** · Nutzer: *„ja V-1“*, mit seinen Gedanken: Geldausweitung als Voraussetzung? Rezession? Wie lange Ausweitung und Bullenmarkt? Die aktuelle Lage (Anleihen, Währungen, KI, Krisen) gesondert messen und recherchieren.

**Ergebnis** (`Messplan_Indikator_Atlas_23_10.md`, vorab ec7ce185; Selbsttest T1 bestanden; Gegenprobe 5/5):
- **T1:** einziger Kandidat **Fear & Greed** (Vorlauf 69 %/46 % und 50 %/31 %, Rang 0,97 in beiden Hälften; zum Teil aus dem Kurs berechnet). Die Makrokanäle K1–K9 und gesamt zeigen keinen Vorlauf. Nasdaq-Trend und Stablecoins laufen nach (Rang 0,00).
- **T2:** Geldausweitung ist für BTC **keine Voraussetzung** (Ränge 0,37–0,89). Der Zyklus 2022–25 (× 7,9) lief bei schrumpfenden Notenbank-Bilanzen. Ein Niveau-Unterschied bleibt bei der Netto-Liquidität (+37 % gegen +17 % über 90 T).
- **T3:**
  - Auch beim Nasdaq ist Geldausweitung keine Voraussetzung (reales M2: 82 % gegen 80 % Bullenmarkt-Monate).
  - Rezessionen kosteten den Nasdaq jedes Mal 24–68 %.
  - Die Zinskurve invertierte 2022–24 zum ersten Mal seit 1976 ohne folgende Rezession; Sahm 0,00.
- **T4:** Anleihen teilweise kritisch (10J 5,31 %, höchster Stand seit 2002), Währungen nur beim Yen und in Schwellenländern. KI-Investitionen teilweise (freier Cashflow −24 %, aber Gewinne +30 %). 2026 gibt es keine Geldflut; der Auslöser ist ein Ölschock. BTC löst sich 2026 vom Nasdaq (−26 % gegen +14 %).

**Folge:** Kandidat vorhanden ⇒ zur Abstimmung: REGEL0-Historie 2020–23 (Download-Ja) und F-1 Fassung 2 mit Fear & Greed; dazu das Lagebild Gesamtmarkt als Fakt. **Betrieb:** unverändert.

**Nachtrag 25.10.2026 (E-141, Prüfbericht):** **Berichtigt:**
- (a) „Nasdaq und Stablecoins laufen nach“ ist falsch; die Nachlauf-Ränge 0,05/0,07 und 0,00/0,33 zeigen keinen Nachlauf.
- (b) Fear & Greed ist ein Grenzfall: erste Hälfte n = 13, Rang in der Gegenprobe 0,955.
- (c) „Geldausweitung ist keine Voraussetzung“ ist eine Beschreibung (Zyklus 2022–25 bei schrumpfenden Bilanzen), kein Messbefund; sie folgt nur aus dem Nicht-Verwerfen.

# E-136 · F-1 Fassung 2 abgebrochen: Die REGEL0 feuert 2020–22 nicht, und ihr Ergebnis 2024–26 hängt an der Länge der Datenreihen (24.10.2026)

**24.10.2026** · Nutzer: *„E1 A“* (vorgelegt: A abbrechen und Ursache messen · B formal zu Ende messen · C Plan nur 2023–26).

**Grundlage:** `Voranalyse_REGEL0_Historie_23_10.md` §6 (Plan 6623eab2), §6.1 (Auslegung 0516af21), §7. Historie 2019-06 bis Datenbeginn: Binance-Archiv, vollständig gegen REST abgeglichen.

**Befunde:**
- **Befund 1:** REGEL0 0.1 erzeugt 2020-07 bis 2022-12 **keinen** Einstieg.
  - 2022 liegt v-dach selbst im 99,9. Perzentil bei −0,43 %.
  - Die Treffer 2021 sind Datenlücken.
  - Kriterium (2) des Plans war damit nicht erfüllbar, deshalb blieb der Filter ungesehen.
- **Befund 2:** Mit der Vorgeschichte ab 2019 ergibt dieselbe Regel 2024–26 **−0,34 %** statt **+0,15 %** je Handel nach 0,48 %.
  - Nur 37,5 % der Einstiege sind gleich.
  - Die Verschiebung zeigt sich bei alten wie bei jungen Assets.
- **Gegenprobe 3/3** (`p80`).

**Entscheidung:**
- F-1 Fassung 2 ist **abgebrochen**; Fear & Greed bleibt Fakt (L6).
- **Betrieb unverändert:** REGEL0 als Vorwärtsprotokoll, mit dem Vorbehalt **„Ergebnis nicht robust gegen die Datenlänge“**. Er widerlegt die Regel nicht (R-R11), aber das Plus der Referenz hängt am Sammelbeginn je Symbol, also an der Grundgesamtheit.
- **Nächster Schritt:** Voranalyse Robustheit REGEL0. Je Baustein (Reife/Reihenbeginn, Normal, Schrumpfung, Trainingsmenge) einzeln messen, welcher den Unterschied macht.

# E-137 · Lagebild Gesamtmarkt L1–L6 als Fakt gebaut; Rezessionsampel rot nur bei Kurve UND Sahm (24.10.2026)

**24.10.2026** · Nutzer: *„E2 alle“* · *„E3 ja“* · *„E4 alle“*, mit der Frage, welche Indikatoren herangezogen wurden und warum sie fachlich die relevantesten sind (Antwort: `Voranalyse_Lagebild_Gesamtmarkt_23_10.md` §2 und §6).

**Gebaut** (§6):
- **Zeilen:** L1 Rezessionsampel, L2 Reifegrad (Nasdaq, BTC), L3 Geld, L4 Zinsen und Anleihen, L5 Öl, L6 Fear & Greed.
- **Technik:** als Erweiterung von O54 `makro_lage`, mit eigenem Fehlerpfad.
- **Orte:**
  - Statusseite (Makro-Karte);
  - eine Zeile in REGEL0-, B1-, B3-, B4- und Season-Ampel-Mails;
  - GUI *Markt (Krypto)*;
  - Diagnose;
  - Log.

**Prüfung:**
- Prüfstand `p81` 8/8, R-R11 zu p73;
- Statusseite im Browser gegen eine Kopie;
- Suite-Paket `Gesamtmarkt`.

**Ehrlich mitgeführt:** ROT kam 1982–2026 bei allen 5 Rezessionen, aber 1–3 Monate **nach** deren Beginn; dazu ein Fehlalarm 2024. Es bestätigt also, es warnt nicht vor.

**Kein Gate, kein Gewicht.** **NB:** K-GM-1 im nächsten Bündel.

**Nachtrag 24.10.2026:**
- Nutzer: *„ja HY-Aufschlag“*.
- L4 trägt den High-Yield-Aufschlag (FRED `BAMLH0A0HYM2`, nur ~3 Jahre verfügbar, deshalb nur Fakt).
- Prüfstand p81 8/8.

# E-138 · Voranalyse Robustheit REGEL0: Die Abhängigkeit sitzt im Querschnitt und an den Signaltagen; das Plus der Referenz war nie von null zu trennen (24.10.2026)

**24.10.2026** · Nutzer: *„Voranalyse Robustheit starten, prüfen gegenprüfen und doku“*. Grundlage: `Voranalyse_REGEL0_Robustheit_24_10.md`; `p82`, `p82b`, Gegenprobe `p82_gegenprobe` (zwei Aussagen berichtigt, alle drei tragend).

**Befunde:**
- **Datenbeginn:** Die Messbasis beginnt dort, wo die Terminmarktdaten beginnen (2021-12, jüngere Futures später). BTC, BNB, SOL, AVAX und XLM stehen erst ab 2023-09 drin, obwohl Binance sie seit 2019/20 führt. Das ist keine Wahl für die REGEL0.
- **Querschnitt:** Auch 23 Symbole mit streng gleicher Kursreihe haben nur 36 % gleiche Einstiege. Die Abhängigkeit kommt also aus Monatsmodell bzw. Schrumpfung:
  - Die Trainingsmenge ist Anfang 2024 lang um 45 % größer.
  - τ² ist in der Referenz in 32 von 33 Monaten 0.
- **Signaltage:** Rund 99 % der Differenz liegen an Tagen mit mehr als 20 Signalen. An ruhigen Tagen verlieren beide Fassungen (−2,0 % bzw. −0,5 % je Handel).
- **Rauschen:**
  - Das Plus der Referenz (+0,153 %) war nie von null zu trennen, Band [−0,23; +0,59].
  - Die Differenz ist je Handel deutlich, Band [−0,88; −0,17].
  - Je Tag gleich gewichtet sind es nur −0,15 % (t = −1,2).

**Folge:** Messplan R Fassung 1 zur Abstimmung (§5):
- R1 gemeinsamer Datenbeginn an sechs Startdaten;
- R2 Zerlegung in vier Bausteine, die alle zusammen die Referenz nachbilden müssen;
- Hauptgröße ist der Vorsprung gegen Zufallsstunden derselben Coins, je Handel und je Tag;
- Selbsttest vor dem ersten Blick.

**Betrieb unverändert.**

# E-139 · Messplan R: Die REGEL0 ist NICHT robust; ihr Vorsprung entsteht allein aus der Reife-Regel am Datenbeginn (24.10.2026)

**24.10.2026** · Nutzer: *„ja Messplan R festlegen, prüfen gegenprüfen und doku“*.

**Grundlage:** `Voranalyse_REGEL0_Robustheit_24_10.md` §5, §5.1 (vorab de529dc4), §6; `p83_robustheit_r.py`, Gegenprobe `p83_gegenprobe.py`.

**Selbsttest:** Der Rang gegen Zufallsstunden (p69) hat bei geballten Signalen 30 % Fehlalarm. Deshalb gilt der Tagesblock-Rang (Fehlalarm 1 %/0 %, Erkennung 81 %/97 %).

**Ergebnis:**
- **R1:** Kriterium (1) 0 von 6, Kriterium (2) 0 von 6 ⇒ **nicht robust**.
  - Z1 je Handel ist bei echtem Datenbeginn +0,12 bis +0,39 % (Rang 0,70–0,93).
  - Je Tag ist Z1 überall negativ, auch in der Referenz (−0,24 %).
- **R2:** **B1 Reife** allein bildet die Referenz zu 99,9 % nach; B2 bis B4 allein nicht.
- **Gegenprobe:** G1 und G3 bestanden. G2 kippt einen Teilrang an der Grenze, das Urteil bleibt.

**Folge:**
- Die REGEL0 0.1 hat **keinen belegten Vorsprung**.
- Ihr gemessenes Plus hängt an der Reife-Regel ab dem Beginn der Terminmarktdaten.
- **Betrieb unverändert bis zur Nutzerentscheidung über die weiteren Schritte.**

**Nachtrag 25.10.2026 (E-141, Prüfbericht):** **Geltungsbereich:** Das Urteil gilt für die Menge *bestand*; die unverzerrten Mengen sind nicht nachgerechnet. Der „Vorsprung der Referenz“ gilt nur je Handel (je Tag −0,24 %). Je Handel allein wäre Kriterium (2) 6 von 6; das 0 von 6 kommt aus der vorab festgelegten Je-Tag-Bedingung.

**Nachtrag 25.10.2026 (E-143, Abgleich mit dem Mess-Regelwerk):** Der Tagesblock-Rang in `p83` nutzte 7-Tage-Blöcke. Die Norm verlangt max(15 T, 3 × Horizont) = 15 Tage. Die Gegenprobe G2 mit 14-Tage-Blöcken gab dasselbe Urteil (nicht robust). Ein Teilrang lag an der Grenze (Start 2023-01 je Handel 0,932 → 0,956), das Gesamturteil hängt aber an der Je-Tag-Bedingung (Ränge ≤ 0,17). Das Urteil bleibt; die Abweichung ist vermerkt.

# E-140 · REGEL0 im Betrieb vorerst unverändert; Richtung nach Gesamtbilanz R-3 (25.10.2026)

**25.10.2026** · Nutzer: *„also mit regel0 welche wir für hebel benötigen ist nicht geeignet und gemessen, hier bleibt nur vorerst alles so zu belassen. Frage 2 musst du mir genauer beschreiben - sehe hier eher eine kombination. R3 benötigen wir ohnehin“*.

**Vorgelegt war Frage 1:**
- A: weiterlaufen mit Fakt-Zeile „Vorsprung nicht belegt“;
- B: Signalmails abschalten;
- C: unverändert.

**Entschieden:** **C, vorerst unverändert.**
- Die REGEL0 ist als Hebel-Signalgeber gemessen und **nicht geeignet** (E-139).
- Die Mails laufen weiter wie bisher; der Befund steht im Regelwerksmanual und in der Spezifikation.

**Frage 2 (Richtung):** Der Nutzer sieht eher eine **Kombination** und braucht die genauere Beschreibung. **R-3 (Gesamtbilanz)** wird ohnehin gebraucht und kommt zuerst. Die Gliederung wird vorab abgestimmt.

# E-141 · Prüfbericht vor der Gesamtbilanz: Formal sauber, acht inhaltliche Stellen berichtigt, zwei frühere „trägt“ halten nicht (25.10.2026)

**25.10.2026** · Nutzer: *„… zuvor prüfe aber ob Fehler und wo Fehler passiert sind, wurden alle Prüfregeln eingehalten?“*. Grundlage: `Bilanz_Gesamt_25_10.md` Teil A. Drei unabhängige Prüfaufträge; jeder urteilsrelevante Hinweis ist an der Quelle nachgeprüft.

**Formal eingehalten:**
- Vorab-Commits vor jeder Ergebnisdatei;
- die Produktions-DB nie beschrieben;
- Nutzer-Ja vor jedem Bau und Download;
- Selbsttest vor dem ersten Blick seit 22.10.

**Inhaltlich berichtigt** (Nachträge an den Einträgen):
- E-36: B6 gegen 0 statt gegen den Versatz, 2 von 4 Mengen;
- E-130: „trägt“ → nicht entscheidbar;
- E-131/E-132: Nullwelt nicht tagestreu;
- E-134: Streuband;
- E-135: Nachlauf falsch, F&G Grenzfall, T2 nur beschreibend;
- E-139: Geltungsbereich *bestand*;
- E-127: Präzisierung.

**Neue stehende Regeln** (Bilanz A.6):
- Tagesblock-Rang bei Ballung;
- „trägt“ braucht das Band;
- Gegenprobe = zweiter Weg;
- Zwischenfassungen committen;
- Geltungsbereich im Urteilssatz.

# E-142 · Voranalyse Vorsprungs-Atlas: Der Auswahl-Vorsprung wirkt über Monate; im 24-h-Einstieg ist er zehnmal kleiner als messbar (25.10.2026)

**25.10.2026** · Nutzer:
- *„wir müssen den Vorsprung ausbauen und das ist unabhängig von den Kosten“*
- *„der Drift muss über die besseren assets und optimale Einstiege ausgeglichen werden“*
- *„ja Voranalyse Vorsprungs-Atlas starten, prüfen gegenprüfen und doku“*

**Grundlage:** `Voranalyse_Vorsprungs_Atlas_25_10.md`; `p85_atlas_voranalyse.py`, Gegenprobe `p85_gegenprobe.py` 3/3.

**Befunde:**
- **Hauptgröße** jeder weiteren Suche ist der Vorsprung gegen die Drift **ohne Kosten**; die Kosten kommen als spätere Prüfung.
- Die Auswahl (Watchlist-Ordnung) ist **belegt** (Spot §25.6, B4), aber **langsam**:
  - oberes Fünftel +12,1 Pp über 12 M ⇒ anteilig nur 0,03 Pp je 24 h;
  - messbar wären ab 0,29 Pp je Handel bzw. 0,77 Pp je Tag.
- Eine **additive** Kombination mit REGEL0-Einstiegen ist damit nicht nachweisbar, nur ein **Zusammenwirken**.
- Auch der beste Auswahl-Korb verlor gegen BTC (−7 % / −26 % in 12 M). Der Drift-Ausgleich ist eine Frage der **Monatsebene**.
- **Machbarkeit:**
  - R-R11 der Auswahl auf 19.610 Ankern gleich;
  - 95 % der Einstiege haben einen Wert (BTC/ETH/SOL nicht).
- **Eigener Fehler vor der Bewertung behoben:** Die Zufallseinteilung lief erst je Einstieg statt je Coin und Stichtag.

**Folge:** Messplan A Fassung 1 zur Abstimmung:
- A1 Zerlegung auf der Monatsebene (Auskunft);
- A2 Zusammenwirken Auswahl × Einstieg (ein Test, Referenz und Lauf A, Bestätigung 2023);
- Abbruchregel.

**Betrieb unverändert.**

# E-143 · Messplan A Teil A1: Die Auswahl schlägt ihre Gruppe (belastbar, 1 M); die Top 30 kommen BTC am nächsten; gegen BTC nichts belegt (25.10.2026)

**25.10.2026** · Nutzer:
- *„ja Messplan A festlegen, prüfen gegenprüfen und doku - immer alle Teilergebnisse mit mir Abstimmen …“*
- *„Vergleiche auch ob die top 100 Altcoins oder u.U. top 50 ggf. anders als der Gesamtmarkt gesehen werden kann.“*
- *„gehe auch vorher in unser mess Regelwerk damit wir hier keine Abweichungen haben“*

**Grundlage:** `Voranalyse_Vorsprungs_Atlas_25_10.md` §6 (vorab a5825547), §6.4 (ec3f83e4), §6.5, §7; `p86_a1_zerlegung.py`, Gegenprobe `p86_gegenprobe.py` 3/3.

**Mess-Regelwerk (§6.5):** vier Abweichungen vor der Bewertung behoben:
- Blocklänge nach `messnorm._block`;
- unter 20 Blöcken KEIN BEFUND;
- Urteilsstufen und Nullpunkt in A2;
- zirkuläre Blöcke.

Dazu ein Nachtrag zu E-139 (7- statt 15-Tage-Blöcke, Urteil bleibt).

**A1 (Auskunft):**
- **Belastbar** (1 M, 2019–2026): oberes Fünftel − Gruppe **Top 30 +3,5 Pp/M [+0,7; +7,5]**, Gesamt +1,5 [+0,3; +2,9]. Gegen BTC ist in keiner Gruppe etwas belegt.
- **Beschreibend ab 2024:** Je enger die Gruppe, desto kleiner der Drift (12 M gegen BTC: Gesamt −73, Top 100 −63, Top 50 −55, Top 30 −44 Pp).
  - Das obere Fünftel der Top 30 liegt nahe BTC (−11 Pp / 12 M, +2,4 Pp / M).
  - Kleinwerte ohne Auswahlwirkung (S +1,7).
  - Season-Ampel: in *kalt* verlieren Altcoins gegen BTC.
  - BTC-Volatilität seit 2023 etwa halb so hoch.

**Folge:**
- Abstimmung über A1, danach A2 (Auswahl × Einstieg) mit dem berichtigten Plan.
- Zusätzlich zu prüfen ist eine Fassung „Top 30, oberes Fünftel“ (Nutzer entscheidet).
- **Betrieb unverändert.**

# E-144 · Messplan A Teil A2: Auswahl × Einstieg trägt nicht bis 0,50 Pp; die Auswahl verbessert den Coin, nicht den Zeitpunkt (25.10.2026)

**25.10.2026** · Nutzer: *„… u.U. können wir dies auf Assetebene für das bestehende Portfolio nutzen und somit selektiv nur bestimmte Krypto Assets für Regel0 bzw. das System nutzen. warten wir auf die Ergebnisse“*.

**Grundlage:** `Voranalyse_Vorsprungs_Atlas_25_10.md` §6.3, §6.5, §6.6 (Fassung 1b, 85cb6098), §8; `p87_a2_auswahl_einstieg.py`, Gegenprobe `p87_gegenprobe.py` 3/3.

**Ablauf:**
- **Selbsttest Fassung 1 nicht bestanden:** Die Je-Tag-Rechnung verglich verschiedene Markttage (Nullpunkt +0,30 Pp, Fehlalarm 6 %, Erkennung 65 %).
- **Fassung 1b** rechnet je Tag als Tagesklammer und hat den Selbsttest bestanden (3 %/4 %, 99 %/83 %).

**Ergebnis:**
- D (oberes Fünftel − übrige, 24 h, ohne Kosten): Referenz +0,12/+0,03 Pp, Lauf A +0,07/+0,29 Pp; Ränge 0,53–0,89. Stufe **TRÄGT NICHT BIS 0,50 Pp**.
- 2023: KEIN BEFUND (10 Blöcke).
- Auskunft 30 T: +2,4/+2,9 Pp je Handel.

**Ursachen:**
1. Die Auswahl wirkt über Monate.
2. Der REGEL0-Zeitpunkt ist in guten Coins nicht besser.
3. 2023 ist zu klein; das war ein eigener Planungsfehler, die 20-Blöcke-Regel war nicht geprüft.

**Lösungsvorschläge zur Abstimmung:**
- **L-1 Auswahl als Asset-Filter auf Monatsebene** (Spot/Bestand, Top 30 bzw. oberes Fünftel), entspricht der Nutzeridee;
- L-2 REGEL0 nur auf gefilterte Coins (kein Vorteil belegt);
- L-3 nicht möglich.

**Betrieb unverändert.**

# E-145 · Voranalyse L-1/L-2: Kein Bestand im oberen Fünftel; Hebel nur für den Kern messbar; 2024–26 durchweg „kalt“ (25.10.2026)

**25.10.2026** · Nutzer: *„ja L-1 Voranalyse starten … auch L-2 wir brauchen auch für Hebel eine Lösung, diese kann nicht wie spot sein, auch auf mein bestehendes Portfolio prüfen und eine andere Haltedauer prüfen …“*

**Grundlage:** `Voranalyse_L1_L2_Asset_Filter_Hebel_25_10.md`; `p88_l1_l2_voranalyse.py`, Gegenprobe `p88_gegenprobe.py` 3/3.

**Befunde:**
- **Bestand:**
  - Von 31 Krypto-Werten liegen 10 in den Top 30, **keiner im oberen Fünftel**.
  - Vier liegen im unteren (SUI, TAO, KAIA, TURBO).
  - Elf liegen außerhalb der Binance-Messbasis; ihre Fünftel gibt es nur am NB.
- **L-1:**
  - Der Filterwechsel kostet 0,04–0,10 %/Monat.
  - Nach der Norm ist 30 T ab 2024 KEIN BEFUND, 7 T ab 2024 dagegen messbar.
  - Gegen BTC ist erst ab 2–3 Pp/Woche etwas erkennbar.
  - Unberührt sind die CMC-Wochen 2017–2019 (Top 200 mit eingestellten Coins).
- **L-2:**
  - Kosten 0,48/0,84/1,56/5,70 % für 24 h/72 h/7 T/30 T.
  - Messbar ist nur der Kern (276 Einstiege, MDE 0,62/1,94 Pp); die Top-30-Auswahl hat zu wenige Einstiege.
  - Die Season-Ampel stand 2024–26 zu 100 % auf „kalt“.

**Vorschläge zur Abstimmung:**
- Messplan L-1 (CMC-Holdout 2017–19, Brücke zuerst, 7 T Wochen-Stichtage, gegen die Gruppe und gegen BTC);
- Messplan L-2 RegelXY (REGEL0 nur Kern, 72/168 h, netto, Selbsttest);
- NB-Export der B4-Fünftel für die elf Werte außerhalb von Binance.

**Betrieb unverändert.**

# E-146 · L-1: Brücke CMC→Binance hält nicht (Datenlänge); L-2: Kern länger halten trägt 2024–26 nicht, 2023 stark positiv (25.10.2026)

**25.10.2026** · Nutzer:
- *„Messplan L1 und L2 zur Prüfung ok“*
- *„vorsicht - btc und eth und sol sollen auch regel0 und hebel nutzen können“* → festgelegt §8.0: Der Kern ist immer zugelassen.
- *„prüfe welche Regel für kern zählt“* → §8.4: Die Kern-Regel E-69 (Aufbau 70/20/10, K1/Rückkauf) ist **beschlossen, aber nicht gebaut**.

**Grundlage:** `Voranalyse_L1_L2_Asset_Filter_Hebel_25_10.md` §8 (vorab 43772659), §8.5 (Fassung 1b d33c1cee), §9; `p89`, `p89b`, `p90`, Gegenprobe `p90_gegenprobe` 3/3.

**L-1 Brücke:**
- Mittel 0,68 (Soll 0,8); oberes Fünftel zu 55 % gleich; ab 2024 0,80–0,84.
- Ursache: Alle drei Merkmale hängen am Beobachtungsbeginn der Quelle (Datenlänge).
- Keine Bestätigung. Lösungen L1-a (Brücke „gleiche Historie“) / L1-b (CoinMetrics-Langhistorie) / L1-c.

**L-2:**
- Selbsttest Fassung 1 sperrte (Auflösung bei 72/168 h, eigener Planungsfehler); Fassung 1b mit Auflösungskurve bestanden.
- 2024–26: **TRÄGT NICHT BIS 1,0 / 2,0 / 2,0 Pp**; netto 72/168 h negativ, gepaart −0,3 bis −0,6 Pp gegen 24 h.
- 2023 (Aufwärtsjahr): +1,5 % / +4,0 % je Handel, KEIN BEFUND (zu wenige Blöcke).
- Das Vorzeichen hängt am Regime.
- Lösung L2-a: Regime-Hebel auf dem Kern, geprüft auf langer Historie 2019–2026.

Die **Diagnose** bekommt `spot_b4_fuenftel` (K-B4-D1).

**Betrieb unverändert.**

**Nachtrag 25.10.2026 zu E-146 (Nutzer: *„Bewertung soll vorerst neutral erfolgen … Gebühren nachgelagert“*):**
- L-2 hatte netto nach Kosten als Hauptgröße. Das war ein **eigener Fehler** gegen Regel 2.
- Neutral bewertet (Voranalyse L1/L2 §9.3) ist der Vorsprung auf dem Kern bei keiner Haltedauer belegt (TRÄGT NICHT BIS 1,0 / 2,0 / 2,0 Pp).
- Längeres Halten hebt den Ertrag vor Kosten nur in Aufwärtsphasen (Drift, kein Vorsprung).
- Künftig sind Kosten ein nachgelagerter Schritt.

# E-147 · L1-a hält nicht (Binance- und CMC-Wert sind zwei Fassungen); L2-a messbar nur für R1 und nahe an E-126; Kern-Regel baubar aus bestehendem Schema (25.10.2026)

**25.10.2026** · Nutzer: *„ja L1-a, L2-a und Kern-Regel Voranalyse starten - was ist mit den andern Werten also den aussichtsreichsten TOP Werten, diese wollen wir auch hebeln bzw. wenn die Strategie für Kern funktionieren sollte wäre dies auch eine Variante für andere Hebelpositionen oder?“*

**L1-a** (vorab 2d0c00cc, Voranalyse L1/L2 §9.4/§9.5, `p89c`, `p89d`):
- Brücke Fassung 2 (≥ 730 T in beiden Quellen): 0,705 (Soll 0,8), oberes Fünftel 51 % ⇒ **hält nicht**.
- Ursache: F8 ist bei Binance das Alter seit der Listung, bei CMC seit dem ersten Top-200-Erscheinen; F2 hängt an Wochen- gegen Tageskursen und an der Listung. F1 stimmt ab 2022 (0,84–0,91).
- Vorschlag **L1-c**: CMC als eigene Messbasis, zuerst A1 auf CMC 2019–26 reproduzieren.

**L2-a** (`Voranalyse_L2a_Regime_Hebel_Kern_25_10.md`, `p91`):
- Auf der langen Historie (ab 2015) reicht die Auflösung (Orakel Rang 1,000); auf 2024–26 allein nicht (E-133).
- Fehlalarm sauber nur für **R1** BTC > 200-T-Schnitt (2 / 6 / 5 %); R2 grenzwertig, R3 3 Strecken, R4 Fehlalarm 10 %.
- ⚠️ R1 ist nahe an **E-126 M-A** (trägt nicht). Messplan-Vorschlag mit Schritt 0 = Reproduktion von E-126.
- **Top-Werte hebeln:** als **Stufe 2**, nur wenn Stufe 1 trägt (Top 30 und Top 30 im oberen Fünftel, gegen den Kern im selben Regime).

**Kern-Regel** (`Voranalyse_Kern_Regel_Bau_25_10.md`):
- Baubar aus dem bestehenden Schema: `api/onchain` (CoinMetrics), Job `externe_reihen`, `k3_gewichten.klima`.
- Heute q = 0,38 (Desktop-Stand 04.10.); K1 seit 2021 nicht scharf.
- Offene Nutzerfragen K-1 bis K-4 (Monatsrate, Tag, Altbestand, Kern aus der alten Spot-Kette); Bauumfang B-1 bis B-3.

**Betrieb unverändert.**

# E-148 · Kern-Regel nur K-4 (Kern aus der alten Spot-Kette); L1-c und L2-a vorab festgelegt (26.10.2026)

**26.10.2026** · Nutzer: *„bin noch nicht bei 70/20/10 verhältnis - aktuell einmal pro monat einen kleinen betrag pro asset, (b) nur K-4, weiter mit L1-c und L2-a“*

- **Kern-Regel:** Variante (b). Die Regel wäre ein Sparplan, den der Nutzer schon selbst führt (monatlich je Asset ein kleiner Betrag, noch nicht 70/20/10). **Nicht gebaut:** Raten-Mail, Ausgleich über die Raten, Klima-Ampel/K1 im Betrieb (B-1/B-2 entfallen). **Gebaut wird nur K-4:** BTC/ETH/SOL aus der alten Spot-Kette nehmen — zuerst die Liste, was dabei wegfällt (Rücksprache vor dem Entfernen). REGEL0 und Hebel bleiben für den Kern unberührt (§8.0).
- **L1-c:** Messplan vorab (Voranalyse L1/L2 §9.6). Vorab-Befund: 1 M auf 2017–19 hätte nur ~10 Blöcke (KEIN BEFUND per Regel) → Bestätigung auf 7 T wie §8.1; Schritt 0 = A1 auf CMC nachrechnen.
- **L2-a:** Messplan vorab (Voranalyse L2-a §7), Schritt 0 = E-126 auf dem Prüfstand nachrechnen.

**Betrieb unverändert.**

# E-149 · Teilergebnisse 26.10.: L2-a Schritt 0 Halt geklärt (E-126 reproduziert, eigene Größe unscharf); L1-c Schritt 0 nicht reproduziert (A1-Top-30 nicht robust); K-4 ist Absicherung (26.10.2026)

**Grundlage:** vorab 65c5a2a9 · `p93`, `p93b`, `p92`, `p92b` · Bestandsaufnahme K-4 (Voranalyse Kern-Regel §7).

**L2-a:**
- Schritt 0 ergab „TRÄGT“ (Rang 0,961) ⇒ Halt nach Plan, Stufe 1 nicht angesehen.
- Klärung: E-126 reproduziert (draußen +0,9 % EUR, Rang 0,86). Mein Schritt 0 maß eine andere Größe (an gegen alle; in vier Fassungen positiv, Rang 0,91–0,96, nur USD-B über der Schwelle). Eigener Planungsfehler.
- Lösung zur Abstimmung: Schritt 0 Fassung 1b auf E-126s Größen (erfüllt), dann Stufe 1.

**L1-c:**
- Top 30 auf CMC +2,3 Pp [−0,3; +5,2] gegen A1 +3,5 [+0,7; +7,5] ⇒ nicht reproduziert, keine Bestätigung.
- Ursache, erster Schritt: Es liegt nicht am Wert (Binance-Fünftel auf CMC-Erträgen −0,0 Pp), sondern an Gruppe, Ertrag oder Coin-Menge.
- ⚠️ Der Top-30-Vorsprung aus E-143 ist damit **nicht robust** gegen die Abgrenzung.

**K-4:** Spot erzeugt heute keine Kern-Kaufvorschläge (Kette angehalten, B1/B3/B4 ohne Kern). K-4 = Absicherung. Fallstrick: Fällt `regel0_betrieb.yaml` aus, läuft die Kette wieder. Vorschlag: zentrale Konstante + Ausschluss nur in den Spot-Zellen.

**Betrieb unverändert.**

# E-150 · Nutzer 1a, 2a, 3a: L2-a Schritt 0 Fassung 1b + Stufe 1; L1-c Ursache zu Ende messen; K-4 bauen (26.10.2026)

**26.10.2026** · Nutzer: *„1a, 2a, 3a - prüfen gegenprüfen und doku“*
- **1a:** Schritt 0 Fassung 1b vorab (Voranalyse L2-a §9), danach Stufe 1 nach §7.
- **2a:** Ursachenmessung V0–V4 vorab (Voranalyse L1/L2 §9.8).
- **3a:** K-4 bauen: zentrale Konstante KERN, Ausschluss nur in den Spot-Zellen der Rollen-Kette, Bestandszeilen bleiben, REGEL0/Hebel unberührt, Suite-Prüfung, NB-Kontrolle im nächsten Bündel.

# E-151 · L2-a nicht entscheidbar (Selbsttest: zu wenige Regimewechsel); L1-c-Ursache: Vorgriff im Marktwert-Rang, A1-Top-30 ohne ihn NICHT TRENNBAR; Berichtigung E-149 (26.10.2026)

**L2-a** (Voranalyse L2-a §10):
- Schritt 0 Fassung 1b reproduziert (+0,87 % gegen +0,9 %).
- Selbsttest nicht bestanden: Fehlalarm BTC 6 %, ETH 9 %; Auflösung erst bei +3 Pp je Woche, die plausible Größe liegt bei ~0,65 Pp.
- Echtes Ergebnis nicht angesehen. Ursache: 72 Regimewechsel in 12 Jahren.
- Vorschlag (a): festhalten, Hebel bleibt bei REGEL0, R1 nur als Fakt.

**L1-c** (Voranalyse L1/L2 §9.9, `p92c`):
- Ursache ist die **Gruppe**, nicht Coin-Menge oder Ertrag.
- Unser Marktwert-Rang nimmt vor dem 21.09.2025 die **heutige** Umlaufmenge: ENA 2024-06 12,2 statt 1,4 Mrd, Rang 9 statt 61.
- Mit zeitrichtigem CMC-Rang: A1-Top-30 +1,9 Pp [−1,7; +6,5] ⇒ **nicht trennbar**.
- Lösung: CMC-Rang in den Messungen.

**Berichtigung E-149:** Die Aussage *„Es liegt nicht am Wert, selbst die Binance-Auswahl zeigt −0,0“* beruhte auf einem eigenen Zeitversatz: Der CMC-Ertrag begann bis zu 6 T **vor** dem Stichtag. Richtig ausgerichtet bleibt A1 auf CMC-Erträgen erhalten (+3,6).

**Betrieb unverändert** (dort ist die Umlaufmenge aktuell).

# E-152 · K-4 gebaut: keine Spot-Kauffrage der alten Kette für BTC/ETH/SOL, Hebel und REGEL0 unberührt (26.10.2026)

**26.10.2026** · Nutzer: *„3a - prüfen gegenprüfen und doku“*
- **Gebaut:** `agent/kernwerte.py` (eine Liste); `assetklassen.zellen()` sperrt die Spot-Zellen des Kerns mit Grund; `rollen_lauf.paare_aus_zellen()`: kein Rückfall auf `strategie_fuer` für den Kern, der Kern-Einstieg ist immer taktisch.
- **Unberührt:** `asset_hebel_settings`, REGEL0, Watchlist-Einträge, Anzeige von Bestand und G/V.
- **Prüfung:** Suite-Paket `Kernwerte` 10/10 mit Mutationsprobe. Sie fand eine zu schwache Prüfung, die ersetzt wurde.
- **Betrieb:** Die Kette ist angehalten, sichtbar ändert sich nichts. NB-Kontrolle K-K4-1 nach dem nächsten Pull (gebündelt).

# E-153 · L2-a festgehalten; zeitrichtiger Marktwert-Rang in den Messungen und A1 neu VORAB (26.10.2026)

**26.10.2026** · Nutzer: *„1 ja, 2 ja - prüfen gegenprüfen und doku“*
- **L2-a festgehalten:** Der Hebel bleibt bei REGEL0 (E-36/E-140). Die Marktphase BTC über/unter dem 200-T-Schnitt ist Fakt im Lagebild, kein Auslöser. Mit unseren Daten nicht entscheidbar, weil es nur 72 Regimewechsel in 12 Jahren gibt (E-151). Kein weiterer Trendfilter.
- **Zeitrichtiger Rang:** Bau und Messplan A1 neu vorab (Voranalyse Vorsprungs-Atlas §9). `mk_messung.RANG_QUELLE` hat die Vorgabe `"cmc"`, `"eigen"` dient nur dem Nachrechnen.

**Betrieb unverändert.**

# E-154 · Zeitrichtiger Marktwert-Rang gebaut; A1 neu: Der Top-30-Vorsprung war der Datenvorgriff, die Auswahl ist auf 1 Monat nirgends belastbar (26.10.2026)

**Grundlage:** vorab 04d010cd · `mk_messung.RANG_QUELLE` (Vorgabe `"cmc"`) · `p94`, Gegenprobe `p86_gegenprobe` mit beiden Rängen.

**Bau:**
- B1 bitgleich (alter Rang rechnet A1 nach).
- B2 Rangkorrelation zu CMC 0,997 (bisher 0,899).
- B3 ENA/TIA/WLD berichtigt.
- B4: 8,2 % der Anker in anderer Klasse, 2021 17 %.

**A1 neu, 1 M:** Top 30 **+1,4 Pp [−1,1; +4,3]** (war +3,5 [+0,7; +7,5]) ⇒ **nicht trennbar**. Gesamt +1,2 [+0,0; +2,3], Gegenprobe [−0,1; +2,4] ⇒ nicht belastbar. Alle Gruppen positiv, keine trennbar.

**Ersetzt E-143** (R-R11 erfüllt: Reproduktion bitgleich plus genau ein getauschter Bestandteil).

**Bleibt:** Die B4-Ordnung des Fortbestands auf 12 M (Fünftel E3 −19,4 bis +11,4).

**Nachtrag zu E-142, E-144, E-145:** Sie rechneten mit dem alten Rang (Vorgriff). Ihre Urteile „nicht trennbar / trägt nicht“ sind davon nicht nach oben verzerrt. Sie gelten mit Vorbehalt und werden nur auf Wunsch neu gerechnet.

**Betrieb unverändert.** `spot_abbau` rechnet zeitrichtig mit der CoinGecko-Historie ab 21.09.2025.
