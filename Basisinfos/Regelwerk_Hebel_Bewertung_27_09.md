# Regelwerk: Bewertung von Einstieg und Hebel

**27.09.2026** · gehört zu `Plan_Hebel_fuenf_Phasen_27_09.md`, Phase 1
Faktenteil: `python hebel_neubau.py`

> **Nutzerauftrag:** *„Regelwerk zuerst — du bist komplett ohne Plan."*
> Und: *„Was ist mit turnover und funding, diese waren bereits gesetzt
> oder? Du hast recherchiert und noch immer keine Ahnung zum Einstieg und
> den Merkmalen."*

---

# ⭐⭐ NACHTRAG STAND 29.09.2026

| | |
|---|---|
| **K5** | ⛔ die Schwelle auf dem **Beitrag** (vorläufig seit 28.09.) ist nach 2c **nicht kalibriert** (T3, Steigung 0,42–0,55) und **nicht besser als rsi allein** (T2) — robust ist sie gegen die Rückkehr zur Mitte (T6). Nach der Vorabfestlegung **neu vorzulegen** (2.680) |
| **K7** | ✔ der **Binance-Markpreis** ist Hauptmaß für Bewertung 2 (2.679); m = 0,09 bleibt die vorsichtige Hauptrechnung — an echten Positionen bis 5x kein Fehlalarm; die echte Bitpanda-Marge ist **je Asset** verschieden (SUI 3,7–6,9 %, BTC 2–3,5 %) |
| **K6** | ◐ Bewertung 2: die **ATR zum Einstieg allein** ist das Risikomodell (2.681); 5x kalibriert, 3x nur geordnet — eine Grenze erst nach **H0** (Prüfung auf der Einstiegsauswahl) |
| **Rollen** | ✔ das Schema vom 25.09. **gilt** und ist geprüft: **A** Richtung entscheidet **OB** (vorher = OPTIMUM; während = Fortsetzung, eigener Einstiegstyp) · **B** Bewegungserwartung **WIE WEIT** · **C** Risikosperre mit der ATR **WIE VIEL HEBEL** — keine Summe, kein Blocker (`hebel_neubau.ROLLEN`) |
| **Black Swans** | nur als **Störfaktor** mit/ohne ausweisen, nie ein Modell, eine Schwelle oder einen Deckel daran ausrichten (Nutzer 29.09.) |
| **Normal** | das Phase-Normal ist größtenteils Rauschen — Bezug künftig das **geschrumpfte** Normal (2.683, 2.684) |
| **Anfahren** | die Tachonadel (Anstieg 24 h in eigener ATR) ist **kein Gewicht** auf A — sie ist selbst Fortsetzung; Mail **offen** (Nutzer: abstrakt, zu viel Information); rsi braucht keine Phasensperre (2.685) |
| **Pflichtablauf (3)** | ⚠️ ein Tor, das an der vorab gewählten Stufe fällt, wird als **Leiter** nachgemessen (neue Vorabfestlegung) — ein Urteil gilt nur oberhalb der gemessenen **Auflösung**; die Messform mit geschätztem Modell löst auf Teilmengen erst +0,08 auf (2.685) |
| **Kalibrierung** | A: auf dem Signal der Rolle, **nicht** kurz nachgeführt (2.683) · C/ATR: je Stufe (2.681) · B: nachgelagert (Einordnung Abschnitt 11) |
| **Pflichtablauf (2)** | ⚠️ Vergleich zweier Regeln: **Auswahlanteil angleichen** — sonst ist eine PBO- oder Monatsmittel-Zahl nicht auswertbar (F3 der K5-Folge) · ⚠️ vor einem neuen Ordnungsschema das **bestehende** im Standblatt suchen (29.09.) |
| **Pflichtablauf** | ⚠️ neue Falle, gefunden an K7: eine **Wahrheit aus einer Quelle** (hier `hebel_positions`) wird vor der Messung am **Buch** geprüft — der Importer teilte Teilschließungen als Vollschluss ein und übersah 3 von 7 Liquidationen |

---

# ⭐⭐ STAND 28.09.2026 — die abgestimmte Anwendungsebene gilt

Seit dem 27.09. abends ist mit dem Nutzer Punkt für Punkt die
**Anwendungsebene K1–K7** abgestimmt (*„ja, so eintragen“* je Punkt;
Volltext `Voranalyse_Kombination_Anwendungsebene_27_09.md`). Sie ersetzt
die Zielgrößen aus § 2. Der Stand im Code: `python hebel_neubau.py`
(`REGELWERK`, `BEITRAGSLAGE`, `NEUESTER_STAND`).

| # | abgestimmt | ersetzt |
|---|---|---|
| **K1** | **Wirkungskurve je Beitrag** — Regler, Optimum erlaubt, **fest** (nicht je Regime); roh und selbstbezogen (gegen die eigenen 30 Tage) nebeneinander; Summe der Kurven, Wechselwirkungen nur als Suche | Schalter mit einer Schwelle |
| **K2** | Urteil gegen die **PHASE** — eigenes Asset, eigene letzte 12 Monate, nur bekannte Ausgänge; Kontrollen Moment (Monat) und Tag; trägt der Markt viel → teilen in `_markt` (Kontext) und `_eigen` (Beitrag) = **W11** | Bezug *Asset im selben Monat* (meine Verschärfung, 2.666) |
| **K3** | Kontextfläche BTC-Rendite × Dominanz-Änderung, Zeitverschiebungs-Nullwelt | – |
| **K4** | Ereignis **q5**: +5 % vor −5 % binnen 24 h als Ausgangsbasis; Höhe × Fenster als Achse; ein späterer Erfolg zählt | *+X % in Y h* (gesetzt) |
| **K5** | ⭐ **geändert 28.09. (vorläufig):** Schwelle auf dem **Beitrag** — dem kalibrierten Vorsprung gegen das eigene Normal; das Normal ist Bezugspunkt, entscheidet nicht mit (2.678: eine Schwelle auf Normal + Kurven wählt das Normal, und das kehrt zur Mitte zurück). Höhe nach Tabelle durch den Nutzer; **3–5 Stufen**, symmetrisch mit Sperren. *Trägt auch das nicht, wird neu abgestimmt* | *nein / gut / sehr gut*; zuerst *Schwelle auf kalibriertem q* (27.09.) |
| **K6** | Hebelstufe = **höchste Stufe mit Liquidationswahrscheinlichkeit unter einer Nutzergrenze**; zuerst R (nur Risiko), R+S als Folgemessung | *MAE in ATR* |
| **K7** | Messbasis **Binance** (Nutzer: *echte Börse, Bitpanda ein Broker*), Markpreis vor Spot-Tief, Bitpanda-Formel m = 0,09, Abgleich an 4 echten Liquidationen | – |

**Dazu am 28.09. abgestimmt oder gemessen:**

| | |
|---|---|
| **Grundgesamtheit** | `--menge unverzerrt:<saat>` — der Bestand plus die **eingestellten** Paare aus demselben Rahmen (2.668/2.669). Ohne sie war jede Neubau-Messung überlebensverzerrt |
| **A4** (Nutzer) | *„wichtig zu unterscheiden, wie weit gestiegen — nur bestätigte Bewegung, also positiv, oder die Bewegung ist bereits gelaufen … sonst wird es ein Blocker“* → Randstufen je bisherigem Anstieg in eigener ATR |
| **Randkriterium** (Nutzer: *„so festlegen und neu rechnen“*) | vorab festgelegt und committet vor der ersten Rechnung (6a9638f) — § 6, Fassung 28.09. |
| **Regeltest** (Nutzer: *„darum muss die Regel dann auch in unseren Tests und Simulationen funktionieren“*) | jede Urteilsregel geht vor der Verwendung durch Zufallsmerkmale und eine gepflanzte Wirkung — § 6 |

**Die Beitragslage nach K1** (Befunde 2.671–2.675, Stand im Code):

| | |
|---|---|
| ✔ **trägt, unabhängig bestätigt** | rsi und momentum_kurz **oberer Rand** je Asset (4 von 4 Mengen, A4 bestätigt) · ema_abstand_atr selbstbezogen als **Kurve** (2.671) |
| ✔ **Altersachse gültig** (2.676) | keine Umkehr in irgendeinem Alter; der **24 h alte** Wert trägt am oberen Rand in Suche, Prüfzeit **und 2022** — auch bei ema_abstand, das mit dem aktuellen Wert 2022 kehrt. Ein 24 h alter Wert ist Lage **vor** der jetzigen Bewegung (OPTIMUM). ⛔ Die frühere Aussage *6 h alt trägt fast nichts* (2.675) war ein Lesefehler |
| ⭐ **kein Blocker** (Nutzer 28.09.) | Altersachse und A4 sperren nichts — *oben gestreckt* geht mit dem aktuellen und dem 24 h alten Wert als zwei **abgestufte** Beiträge in K1 Schritt 2 ein, A4 als abnehmendes Gewicht |
| ⚠️ **nur in der Suche** | funding_markt und konten_verh_markt **unterer Rand** (niedriges Funding, wenige Longs **marktweit**) — Kontext-Kandidat |
| ⛔ **fällt** | Sperre *viele Longs je Asset* (in der Prüfzeit nicht da) · ema_abstand oberer Rand als Rand (kehrt 2022) · Premium · Käuferanteil · taker_verh · Kontextfläche (2.670) · Dominanz-Sperren 2.601/2.665 (2.670/2.672) |

---

# ⚠️⚠️ STAND 27.09. ABENDS — was von diesem Blatt noch gilt

Dieses Blatt entstand am Mittag. Der Nachmittag hat es in wesentlichen
Punkten überholt (Befunde 2.654 bis 2.667). **Der Stand im Code:**
`python hebel_neubau.py` (Abschnitt NEUESTER STAND).

| | gilt noch | überholt |
|---|---|---|
| **Ablauf** (§ 1) | ✔ zwei Bewertungen zum Prüfzeitpunkt, **neutral**: ohne Zeit, ohne Geometrie, ohne Ertrag | – |
| **Bewertung 1** (§ 2) | Frage „kommt eine Bewegung nach oben?“ | ⛔ die **Zielgröße** (+X % in Y h) war **gesetzt, nicht gemessen**. Gemessen ist: der Bezug muss das **eigene Asset** sein (2.655); ein Lift allein zeigt vor allem **mehr Bewegung** (2.657) — entscheidend ist das Verhältnis Chance zuerst / Rückgang zuerst gegen das eigene Asset |
| **Bewertung 2** (§ 2) | Risiko → Hebelhöhe | ✔ die **Höhe** hält den Pflichtablauf (2.662): 14 von 16 Auswahlen, streng gegen das eigene Asset im Monat, auf Episoden, vorwärts in **jeder** BTC-Lage. ⚠️ Aber der Rückgang vor dem Hoch steigt mit — es ist die **Größe** der Bewegung, kein Vorteil. ⚠️⚠️ **Einheit offen:** gemessen in Prozent, § 2 definiert MAE in ATR, und vola_kausal ist die ATR selbst — vor Messung 2 zu entscheiden |
| **Karenz** (§ 2) | ✔ Achse, kein Filter | – |
| **Beitragslage** (§ 3) | – | ⛔ Richtung schwach für alle Kandidaten (2.655), untere Achse = Trailing-Effekt (2.656), keine Lage regimefest (2.659/2.660) |
| **Sperre** | ⭐ **viele Longs** (konten_verh hoch) — negativ in jedem Regime (2.660); Kandidat **funding hoch** (≥ 0,0016, Spiegel 0,43 — 2.663, ohne Pflichtablauf) | – |
| **funding** | ✔ trägt mit dem **Vortageswert** (2.663) — aber auf Stunden, der Pflichtablauf fehlt | ⛔ 2.651: die Hälfte des Lifts war **Vorgriff** (9,55 → 4,45) |
| **Datenfehler** 2.658 | ✔ gemessen ohne Wirkung auf die Urteile von 2.648/2.650 (2.664) | – |
| **Richtung** (2.665) | ✔ nur **funding** ist Lage vorher (Vortag negativ: q5 0,531 statt 0,490; hoch = Sperre) — **klein**; Such-/Prüf-Trennung fehlt | ⛔ Käuferanteil **begleitet** die Bewegung, `momentum_kurz` **ist** sie (kein Einstieg nach OPTIMUM); Premium ohne Befund |
| **funding auf 2022** (2.666) | ✔ **hält auf 2022** in derselben Größe (Mittel über 12 Startstunden +0,028, Suchzeitraum +0,025) und markiert zusätzlich die **Phase** des Assets | ⛔ die erste Fassung *das Vorzeichen dreht* war ein **Mitternachtseffekt** der Episodenregel — Tagesmerkmale künftig über Startstunden mitteln |
| **Höhe in ATR** (2.667) | ✔ für die Liquidation zählt Prozent, und die **ATR zum Einstieg** ist das Risikomaß (5x binnen 72 h: 5,8 % gegen 26,9 %); über die ATR hinaus trägt vor allem `volumenschub` | ⛔ die Prozent-Höhe von vola ist größtenteils die ATR selbst |
| **Nächste Messungen** (§ 5) | – | ⛔ ersetzt: neue Richtungsdaten (Käuferanteil, Premium-Index, BTC-Dominanz-Index) mit dem Pflichtablauf aus § 6 |

---

# ⛔ Der Fehler, der dieses Blatt nötig macht

Am 27.09. habe ich **sieben Kursmerkmale** gemessen — `ema_abstand_atr`,
`momentum_kurz`, `rsi`, `rsi_umkehr`, `rsi_aenderung`, `ema_lage`,
`ema_steigung`, `trendstruktur`, `bandenge`, `vola`.

**Die drei einzigen registrierten Träger des Systems habe ich nicht ein
einziges Mal geladen:**

| | Form | Zustand | Basis |
|---|---|---|---|
| **`funding`** | Regler | ✔ trägt | H20 · 2.369 Kalendertage · 290 Symbole · 6,3 Jahre |
| **`turnover`** | Regler | ✔ trägt | H20 · 2.636 Kalendertage · Richtung +0,00512 (stärkster der drei) |
| **`oi_aenderung`** | Schalter | ✔ trägt | H20 · 1.702 Kalendertage · 117 Symbole · 126.491 Anker |

⚠️ **Mein eigener Riegel hat sie mir aus dem Blick genommen.** `hebel_neubau.SPOT_QUELLEN`
sperrt `funding_fuenftel` und `turnover_fuenftel` — die **alten Beitragsstufen**.
E-3 gibt die **Rohgrößen ausdrücklich frei**. Ich habe die Sperre auf die
Rohgrößen ausgedehnt, ohne es zu merken.

---

# 1. Der Ablauf zum Prüfzeitpunkt

**Nutzervorgabe 27.09.:** *„1. Hebel-Einstieg zulässig? … 2. Hebelbewertung:
ist auch das Risiko gering und die Chance hoch."* Und: *„dann weiter in der
Kette wie heute."*

```
T1  Prüfzeitpunkt
    ├─ BEWERTUNG 1  Einstieg zulässig?     gut | sehr gut | nein
    ├─ BEWERTUNG 2  Hebelhöhe               2× | 3× | 5×
    └─ weiter in der Kette wie heute  ──►  Mail

T2  nach der Eröffnung — eine neue Hebelposition existiert
    └─ Stop · Trailing · Ausstieg            (Phase 5)
```

⚠️ **Beide Bewertungen sind neutral:** kein Kapital, keine Positionsgröße,
kein Ergebniswert, **keine Geometrie**.

---

# 2. Die zwei Bewertungen — und sie messen Verschiedenes

> **Das ist der Kern, und er hat mir bis heute gefehlt: Einstieg misst
> gegen die CHANCE, Hebel gegen das RISIKO. Zwei Zielgrößen, zwei
> Messungen — ein Merkmal kann in der einen tragen und in der anderen
> nicht.**

| | **BEWERTUNG 1 · Einstieg** | **BEWERTUNG 2 · Hebelhöhe** |
|---|---|---|
| **Frage** | Kommt eine Bewegung nach oben? | Wie weit geht es gegen mich, bevor es für mich geht? |
| **Zielgröße** | **Ereignis**: +X % in Y h — regelfrei | **MAE in ATR** — maximaler Rückgang |
| **Bezug** | das eigene Asset (**Lift**) | das eigene Asset |
| **Nullpunkt** | **Lift = 1** | eigener Durchschnitts-MAE |
| **Ergebnis** | nein / gut / sehr gut | 2× · 3× · 5× |
| **Richtung** | geringes Risiko → **höhere** Stufe | |

## ⚠️ Die Karenz für Bewertung 1 — eine ACHSE, kein Filter

**Nutzerdefinition:** *„OPTIMUM ist, wir kennen die Lage VOR der Bewegung.
Die Bewertung eines bereits gestiegenen Assets ist weder das Ziel noch ein
Optimum — dazu brauche ich kein System."*

⛔ **Bis 27.09. abends stand hier ein Filter:** *„qualifiziert sich nur,
wenn sein Lift eine Karenz von mindestens 3 Stunden überlebt"*. Der
Nutzer hatte ihn schon in 2.650 verworfen: *„bin mir nicht sicher, ob du
dies nur für die Messung als Annahme siehst oder wir gute Signale
kappen."* (E-9)

➤ **Bewertung 1 gilt bei k = 0** — das ist der Betriebsfall, im Betrieb
steigt man sofort ein. **Der Vorlauf (k > 0) wird daneben ausgewiesen**:
er sagt, ob ein Merkmal die Bewegung **vorhersagt** oder nur
**begleitet**. Das Optimum ist ein Träger **mit** Vorlauf; ein Träger
ohne ist brauchbar, aber kein Optimum. Keine der beiden Zahlen kappt die
andere.

---

# 3. Wo welcher Beitrag zählt — die Wahrheit steht im CODE

```bash
python hebel_neubau.py | sed -n '/WO WELCHER BEITRAG ZAEHLT/,/WAS \*OPTIMUM\*/p'
```

⛔ **Warum hier keine Tabelle mehr steht:** Bis 27.09. abends stand sie
**doppelt** — hier und in `hebel_neubau.BEITRAGSLAGE`. Nach 2.651 wurde
keine von beiden nachgezogen, und die Suite **erzwang** sogar den alten
Stand (2.652-beitragslage-nachgezogen). Jetzt nennt jeder Eintrag im Code
seinen Befund, und die Wache leitet die gemessenen Merkmale aus dem
Quelltext der Messskripte ab.

**Schnappschuss 27.09. abends** — nur zur Orientierung:

| | Bewertung 1 (Chance, k = 0) | Vorlauf | Bewertung 2 (Risiko, MAE) |
|---|---|---|---|
| **trägt** | `funding`* · `oi_aenderung` · `konten_verh` (2.651) · `momentum_kurz` · `rsi` (2.648) | **keiner** | `ema_abstand_atr` (2.642/2.647) |
| **fällt** | `turnover` · `oi_je_umsatz` · `volumenschub` · `taker_verh` · `top_*` (2.651) · `ema_abstand_atr` · `vola` · `bandenge` (2.648/2.650) | – | – |
| **ungemessen** | – | – | alle übrigen; `vola` als Spur |

\* `funding`: der Vorgriffsverdacht (2.652-vorgriff-funding) ist
**gemessen und bestätigt** (2.663). Mit dem Vortageswert halbiert sich der
Lift (9,55 → 4,45 auf +15 %/H12), 13 tragende Zellen werden 9. funding trägt
weiter — aber auf Stunden-Ankern, ohne Episoden, Vorwärtsrechnung und
Gegenprüfung. Die Tabelle oben ist ein Schnappschuss vom Abend **vor** der
Probe; die Wahrheit steht in `hebel_neubau.BEITRAGSLAGE`.

⚠️ **Vorher gemessen, nicht im Standblatt** (Kursmerkmale, abgeschlossen):
`rsi_umkehr` · `ema_lage` · `ema_steigung` · `trendstruktur` fallen
(2.645); `amihud` · `funding_extrem` · `long_bias` · `top_bias` ·
`taker_bias` laut Register ohne Beitrag.

---

# 4. Die Anordnung — Beitragssystem, kein Blocksystem

**Nutzervorgabe (E-4):** *„der HEBEL ist ein Beitragssystem und KEIN
Blocksystem."*

```
BEWERTUNG 1        Σ Beiträge auf die CHANCE   →  Schwelle  →  gut | sehr gut
BEWERTUNG 2        Σ Beiträge auf das RISIKO   →  Stufe     →  2× | 3× | 5×
```

⚠️ **Was aus dem alten Gerüst übernommen wird — und was nicht:**

| ✔ übernommen | ⛔ tot |
|---|---|
| **Registrierung**: ein Beitrag = ein Eintrag mit Wert, Zustand, Quelle, Begründung | `Basisrate = 1/(1+CRV)` — Geometrie **und** Kelly-Nullstelle |
| **Fünf Zustände** + `luecke`: traegt / enthalten / null / noch_nicht / nie | `Breakeven` mit Gebühren — Regel 2 |
| **Additive Verrechnung** — durch 2.302 **belegt** (turnover unabhängig von funding) | **Stufen je Fünftel** — Querschnittsrang (2.649) |
| | `Quote` als Ergebnis — setzt Barrieren voraus |

➤ **Die Stufengrundlage wechselt von *Fünftel* auf *absolute Schwelle in
eigenen Einheiten*.** `funding` und `turnover` müssen dafür neu gestuft
werden — die registrierten Stufen `(+0.82, +1.30, …)` hängen am Fünftel und
gelten nicht.

---

# 5. Was als Nächstes zu messen ist — die Reihenfolge steht im CODE

```bash
python hebel_neubau.py | sed -n '/DIE NAECHSTEN MESSUNGEN/,/^---/p'
```

**Schnappschuss 27.09. abends** (`hebel_neubau.NAECHSTE_MESSUNGEN`):

| # | Messung | Art | warum |
|---|---|---|---|
| **1** | **Vorgriffsprobe `funding`** auf Bewertung 1 | Probe | 2.651 reproduzieren, dann mit dem Vortageswert d−1 — vorgriffsfrei und die Form, die live beschaffbar ist (2.652-vorgriff-funding) |
| **2** | **Vorlauf bei H72 und H120** für die B1-Träger | Vorlauf | die Haltequote steigt mit dem Fenster (0,29 bei H6, 0,74 bei H48) — erreicht sie 0,8? |
| **3** | **Messung 2: Bewertung 2 (MAE)** für `funding`, `oi_aenderung`, `konten_verh` | neu | Bewertung 2 hat **einen** Träger; was mitläuft, entscheidet die Voranalyse (E5) |
| **4** | **`vola` in der Hebelhöhe** | neu | Register-Spur: *„über `hebel = verlustanteil / stop_rel` fällt daraus der Hebel"* |

⚠️ Messung 1 aus der früheren Fassung (*„funding, turnover, oi_aenderung
auf Bewertung 1"*) ist **gelaufen** — 2.651.

⚠️ **Und was NICHT mehr gemessen wird:** weitere Kursmerkmale aus der
EMA/RSI/ATR-Familie. Drei unabhängige Messungen (2.578, 2.645, 2.650) sagen
dasselbe — dort ist nichts.

---

# 6. Die Prüfpflicht

Jeder Befund ab 2.647 belegt **sechs** Prüfungen, bewacht von
`pruefe_pakete.py --paket Hebelneubau`:

**Nullwelt** (tagestreu) · **Zeitstabilität** (Kalenderjahre) ·
**Weglassprobe** · **Mehrfachtesten** (Bestes-von-N) · **Ebene** (A/B/C) ·
**je Asset**

Für Bewertung 1 kommt die **Karenz als Achse** dazu (Abschnitt 2): k = 0 und der Vorlauf werden beide ausgewiesen.

## ⭐⭐⭐ DER PFLICHTABLAUF für jede Hebel-Messung (27.09. abends)

Jeder Schritt steht hier, weil er heute **mindestens einmal gefehlt** hat —
und das Ergebnis dadurch falsch war. Keine Meldung eines tragenden
Befundes, bevor alle Schritte gelaufen sind.

| # | Schritt | was passiert war |
|---|---|---|
| 1 | **Bezug = das EIGENE Asset** (symboltreue Nullwelt); die tagestreue Nullwelt nur als Kontrolle | der Vergleich mit dem gleichen Tag misst die Auswahl zwischen Assets — der Nutzer vergleicht keine Assets (2.655) |
| 2 | **Kein Trailing, kein Stop, kein Ertrag aus einer Regel** in der Zielgröße der Bewertung; feste Barrieren, MFE/MAE oder Ereignisse | der Ertrag der unteren Achse kam aus der Trailing-Regel (2.656) |
| 3 | **Episoden statt Stunden**: Einstieg beim Erscheinen der Lage, je Asset höchstens einer in 24 h | Anker-Stunden täuschen Seltenheit und Menge vor (E2b) |
| 4 | **Absolut UND relativ**: Lift und P(Ziel zuerst), P(Rückgang zuerst), q gegen das eigene Asset und gegen die Gewinnschwelle | Lifts von 7 bis 10 waren vor allem mehr Bewegung (2.657) |
| 5 | **Bekanntheitszeitpunkt** jedes Merkmals prüfen: Tageswerte nur vom Vortag, Normierungen nur aus der Vergangenheit | funding-Tagessumme (2.652), vola-Median der ganzen Reihe (2.658) |
| 6 | **Stunden, nicht Zeilen**: Anker über Lücken der Stundenreihe ausschließen | 47 Symbole mit Lücken (2.658) |
| 7 | **Trennung**: Suche und Prüfung getrennt; Mehrfachtesten nur über die geprüfte Auswahl | Suche versprach +12 bis +21, die Prüfung hielt 0 bis +9 (2.657) |
| 8 | **Vorwärts rechnen** (E3): jeder Prüfmonat gegen die Schwellen der 12 Monate davor, Maßstab 2024 bis 2026; Auswertung je Quartal und je BTC-Lage — **regimefest** heißt in jedem Regime | eine Lage hing an einem Quartal (2.659) |
| 9 | **Gegenprüfung** (E3-Gegenprüfung): Selbstprobe, Merkmale 1 h älter, absichtlicher Vorgriff, Etikettentausch, Zufallslagen **in der Größe des Kandidaten** | ohne sie wären zwei Aussagen stehen geblieben (2.660) |
| 10 | **Erklärung ist kein Befund**: Namen beschreiben die Lage, nicht eine Deutung | *Squeeze* war eine Deutung (2.660) |

➤ Bewacht im Paket Hebelneubau: ein **positiver** Neubau-Befund ab 2.661
muss in seiner Basis die Vorwärtsrechnung und die Gegenprüfung nennen.

## ⭐⭐⭐ DER PFLICHTABLAUF — Fassung 28.09.2026 (K1 bis 2.676)

Die zehn Schritte oben gelten weiter. Geändert oder dazugekommen, jeweils
mit dem Anlass:

| # | Schritt | geändert, weil |
|---|---|---|
| 1 | **Bezug = die PHASE des eigenen Assets** (letzte 12 Monate, nur Ausgänge ≤ t − W); Kontrollen **Moment** (Asset im Monat) und **Tag** (alle Assets am Tag) | K2, Nutzer: der Monatsbezug nahm die Phase heraus (2.666) |
| 3 | **Feste Tagesanker 00/06/12/18 UTC** statt Episoden; ein Tagesmerkmal wird über die Startstunden gemittelt | der „Vorzeichenwechsel 2022“ war ein Mitternachtseffekt der Episodenregel (2.666) |
| 11 | **Grundgesamtheit** `unverzerrt:1..3` **und** `bestand` — ein Urteil muss in allen vier stehen; der Bestand bleibt bitgleich reproduzierbar | Überlebensverzerrung (2.668/2.669) |
| 12 | **Nullwelt = Zeitverschiebung**: je Asset für Merkmale je Asset, **gemeinsam für alle Assets** für Marktmerkmale — sonst z bis 118 | die Verschiebung je Asset zerstört die Gleichzeitigkeit (2.673) |
| 13 | **W11 — teilen, wenn der Markt trägt**: Tag/Phase < 0,5 → `_markt` gegen die gemeinsame, `_eigen` gegen die Nullwelt je Asset; das gilt **auch für die Ränder** | funding, premium, Long-Anteile sind überwiegend Markt (2.675) |
| 14 | **Kurve UND Rand**: das Kurvenurteil (S, Form Suche/Prüfung) und das **Randkriterium** stehen nebeneinander — Rand oben P90–P99 + > P99, unten < P1 + P1–P10; trägt, wenn jenseits der Grenze Bestes-von-(2 × Kurven) **und** gleiches Vorzeichen in Prüfzeit, ≥ 3/4 Jahren, ≥ 60 % der Assets **und 2022** (Moment-Bezug); positiv → Einstieg nur mit bestätigter Altersachse und A4, negativ → Sperre | einseitige Kurven scheiterten an der flachen Mitte (2.674); vorab festgelegt 6a9638f |
| 15 | **A4 und Altersachse** für jeden positiven Träger: Randstufen je bisherigem Anstieg in eigener ATR (*bestätigt oder gelaufen*), das Merkmal 6/12/24 h alt | Nutzer 28.09.; Lage **vor** der Bewegung (OPTIMUM) |
| 16 | **Positivkontrolle in eine WIRKUNGSLOSE Kopie** (zeitverschoben) — nie in ein schon starkes Merkmal | die erste Fassung pflanzte in funding und war wertlos (2.671) |
| 17 | ⭐ **REGELTEST vor der Verwendung**: Zufallsmerkmale (geglättet wie echte, je Asset **und** als Marktreihe) durch die Regel — Soll: fast nie *trägt*; dazu eine gepflanzte Wirkung bekannter Größe → die Auflösung | Nutzer 28.09.: *die Regel muss in unseren Tests und Simulationen funktionieren* (2.675: 0 von 40, Auflösung +0,02 je Asset, ~0,08 Markt) |
| 18 | **Bestätigung gegen den Versatz, nicht gegen null**: ein Vorzeichen in der Prüfzeit zählt erst, wenn es den Versatz der Zufallsränder klar übersteigt; bei Markträndern ist die Marktstreuung der Maßstab | die Prüfzeit liegt +0,01 über ihrem Normal, Marktränder streuen 0,035 (2.675) |
| 19 | **Simulation (Ebene 3)** vor jeder Verwendung im Betrieb: Signale mit der Regel gehen auf ungesehenen Monaten messbar anders aus als ohne | Nutzer 28.09. |
| 20 | **Über eine Achse dasselbe Maß an jedem Punkt**: wer ein Merkmal über Alter, Anstieg oder Zeitraum verfolgt, vergleicht an jedem Punkt **denselben** Rand (Stufen 10+11), nie eine Einzelstufe gegen den Rand | die Altersachse druckte nur die äußerste Stufe und wurde gegen den Rand gelesen (2.675 → 2.676) |
| 21 | **Uhrzeit prüfen** bei festen Ankern: T1 q5 je Ankerstunde, Rand **tagesbereinigt**; eine Periode über 24 h ist erst nach dieser Prüfung eine Aussage | die Nullwelt (Verschiebung um beliebige Stunden) zieht einen Uhrzeiteffekt nicht ab (2.676) |
| 22 | **Vollständigkeit am Inhalt**: ein Lauf gilt erst mit Schlusszeile und ohne Traceback — ein Exit-Code im Kettenprotokoll allein genügt nicht | `exit=$?` hinter `$(date …)` meldete immer 0 (2.676) |
| 23 | ⭐ **Kein künstlicher Blocker** (Nutzer 28.09.): Achsen wie Alter und A4 prüfen die **Gültigkeit** und liefern **Gewichte** — keine Schwelle *erst ab X*, kein Schnitt | Nutzervorgabe *keine Alles-oder-nichts-Schwelle* |
| 24 | **Anker sind nicht unabhängig** (vier je Tag, überlappende Fenster, ein Markttag für alle Assets): ein geschätztes Modell bekommt seine Dämpfung **aus den Daten** (zeitlich geblockte Kreuzvalidierung im Trainingsfenster), nie eine feste | die feste Dämpfung lernte Rauschen, Nullwelt −17 (2.677) |
| 25 | **Auflösung vor dem Urteil**: die Pflanzung muss eine Wirkung **in der Größe der gesuchten** sicher finden — sonst ist *trägt nicht* ein Befund über die Messform, nicht über den Beitrag | das Kurvenmodell fand erst +0,16, gesucht waren +0,03…+0,06 (2.677) |
| 26 | **Auswahl nach Bezug + Beitrag immer auch nach dem Beitrag allein** ausweisen, mit eigener Nullwelt; liegt die Nullwelt der Auswahl nicht bei 0, ist das ein Befund über den **Bezug** | die Auswahl nach Normal + Beitrag wählte das Phase-Normal, das zur Mitte zurückkehrt (2.678) |

⚠️ **Nicht mehr Pflicht:** Episoden (Schritt 3 alt) und die Karenz als
eigener Lauf — beide sind durch Tagesanker, Altersachse und A4 ersetzt.

## ⚠️⚠️ Der HEBEL-Messstandard — was vom Spot-Standard gilt, was nicht (27.09. abends)

**Nutzerauftrag:** *„beim Bauen Messstandards anwenden, wenn diese nicht
mehr auf den Hebelstandard angewendet werden können, melden bzw.
berücksichtigen und den Standard anpassen."*

⛔ **Befund 2.653-hebel-messstandard:** Die Hebel-Werkzeuge 2.647 bis
2.651 **drucken** `messnorm.standardzeile()` in den Kopf, **wenden aber
nichts daraus an**. Die Zeile verspricht *„gepflanzte Stärken bis 0,40 R,
Positivkontrolle 5 Ziehungen"* — keines der Werkzeuge pflanzt. Das
Werkzeugregister führt sie trotzdem als **NORM**, weil es nur
`import messnorm` zählt (14 von 60 NORM-Werkzeugen rufen direkt nichts
außer der Kopfzeile).

| Baustein | Spot-Standard (`messnorm`) | Hebel, wie gemessen (2.647–2.651) | Stand |
|---|---|---|---|
| **Zielgröße** | `bewegung_r` / `barriere` in R; `ZIELGROESSE_JE_LAGE[hebel] = barriere` | B1: **Ereignis** (+X % in Y h) als **Lift** je Asset; B2: **MAE in ATR** | ⚠️ `messnorm` widerspricht dem Regelwerk |
| **Nullpunkt** | Mittel der Nullwelten (40) | **Lift = 1** (eigenes Symbol); B2: eigener Durchschnitts-MAE | eigene Form, passt zur Frage |
| **Nullwelt** | 40 Ziehungen | tagestreu, 40 Ziehungen | ✔ gleichwertig |
| **Mehrfachtesten** | Band je Urteil | **Bestes-von-N**, 90. Perzentil der Maxima aus 40 Ziehungen — nominell rund **10 %** Fehlalarm je Lauf über **alle** Zellen, bevor Spiegelprobe und 60-%-Symbolregel greifen | ⚠️ Fehlalarmquote nicht selbst geprüft |
| **Richtung** | – | gerichtete **Spiegelprobe**, Schwelle 1,717 (2.603) | ✔ Hebel-eigen |
| **Zeitstabilität, Weglassprobe, je Asset** | Tagesklammer / Blöcke | je Kalenderjahr (≥ 10 erwartete Ereignisse), 7 von 7, Lift je Symbol, ≥ 60 % Symbole positiv, ≥ 30 Treffer je Symbol, ≥ 20 Symbole | ✔ Hebel-eigen |
| **Karenz / Vorlauf** | – | Achse, k = 0 Betriebsfall (E-9) | ✔ Hebel-eigen |
| **Horizont** | `HORIZONT_JE_LAGE[hebel] = 24 h` (2.646) | Fenster 6 bis 48 h gemessen, 72/120 h geplant — das Fenster ist eine **Achse** | ⚠️ ein fester Wert passt nicht |
| ⛔ **Positivkontrolle / Trennschärfe** | gepflanzte Stärken bis 0,40 R, Selbsttest 2.204 und 2.485 | **fehlt** — welcher Lift mit welcher Wahrscheinlichkeit gefunden wird, ist unbekannt | ⛔ **Lücke** |
| ⛔ **Bekanntheitszeitpunkt** | – | nicht geprüft — genau daran hängt 2.652-vorgriff-funding | ⛔ **Lücke** |
| ⛔ **Bewertung 2 (MAE)** | – | Nullwelt, Band und Stufung für MAE nicht festgelegt | ⛔ vor Messung 2 zu klären |

✔ **Stand 28.09. — drei der Lücken sind geschlossen, eine ist neu:**

| Baustein | geschlossen durch |
|---|---|
| ✔ **Positivkontrolle / Trennschärfe** | Pflanzung in eine wirkungslose Kopie (2.671); Auflösung je Asset **±0,02** (unverzerrt), ±0,04 (bestand); Marktmerkmale gröber als 0,04, Kontext 0,06–0,08 (2.670/2.673) |
| ✔ **Bekanntheitszeitpunkt** | Vortageswert für Tagesgrößen (2.663), Normierung nur aus der Vergangenheit, Anker am Ende eingestellter Reihen nur bei lückenlosem Rest (2.669) |
| ✔ **Fehlalarmquote** | Regeltest: 0 von 40 Zufallsrändern, je Asset und als Marktreihe (2.675) |
| ⚠️ **Zielgröße** | seit K4 **q5** gegen die Phase — `messnorm.ZIELGROESSE_JE_LAGE[hebel] = barriere` ist damit vereinbar, der Code-Standard ist aber nicht nachgezogen |
| ⚠️ neu: **Prüfzeit-Versatz** | +0,009/+0,013 je Asset — ein Vorzeichen in der Prüfzeit ist gegen ihn zu lesen (Schritt 18) |

➤ **Bis zur Anpassung im Code gilt:** Hebel-Befunde nennen die Prüfform
dieser Tabelle, **nicht** die `messnorm`-Kopfzeile. Die Anpassung selbst
(ein Hebel-Standard im Code, Positivkontrolle für den Lift, Prüfung des
Bekanntheitszeitpunkts, Einstufung im Werkzeugregister) ist ein eigenes
Paket mit Voranalyse.

