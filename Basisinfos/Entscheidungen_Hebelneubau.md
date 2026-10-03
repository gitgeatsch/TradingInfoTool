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
