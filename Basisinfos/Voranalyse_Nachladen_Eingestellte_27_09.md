# Voranalyse — die Messbasis vervollständigen: eingestellte Paare und BTC ab 2021-12 (27.09.2026)

> **Auslöser:** Befund **2.668** — `stundenkurse.db` enthält nur heute
> gehandelte Paare, kein einziges eingestelltes; BTC erst ab 2023-09.
> Stehende Regel (CLAUDE.md, Kap. 120.3): *„Eingestellte Werte gehören dazu.
> Ohne sie ist jede Messung überlebensverzerrt, und der Boden der Verteilung
> fehlt."*
>
> **Nutzer 27.09.:** *„ja, Voranalyse für das Nachladen schreiben, prüfen und
> gegenprüfen."*

⚠️ **Dieses Blatt baut und lädt nichts.** Die Recherche dafür lief mit
rund 360 Listenabrufen (Pause 0,6 s) — `recherche_eingestellte_perps.py`,
Ergebnis in `data/_recherche_eingestellt.json`.

---

## 1. Ist-Stand am Code — woher die Verzerrung kommt

Die Verzerrung sitzt **eine Stufe früher**, als 2.668 sagt:

| Stufe | Werkzeug | Auswahl | Folge |
|---|---|---|---|
| 1 | `hole_terminmarkt_historie.messbasis_symbole` | **Zufallsstichprobe von 100** aus den Perpetuals mit Status `TRADING` **am Ziehtag** (∩ `messdaten.db`), plus die Krypto-Watchlist → 122 Symbole | wer vor dem Ziehtag eingestellt war, konnte nie gezogen werden |
| 2 | `hole_stundenkurse.symbole_und_spanne` + `handelbar()` | die Symbole aus Stufe 1, nur `TRADING` → 116 | 5 weitere fallen weg (XMR, KAS …) |
| 3 | `hole_richtungsdaten.py` (2.661) | die Symbole aus Stufe 2 | dieselbe Verzerrung |
| 4 | `funding_historie.db` | 302 Symbole, keines endet vor 2026-08 | ebenfalls nur Überlebende |

⚠️ **Die 22 Watchlist-Symbole sind keine Stichprobe** — du hast sie
ausgewählt, sie sind per Definition Überlebende. Für eine unverzerrte
Schätzung zählen nur die **100 Gezogenen** plus die Eingestellten.

---

## 2. Was es im Archiv gibt — gemessen, nicht geschätzt

| | Zahl |
|---|---|
| USDT-Perpetuals im Archiv (ohne Lieferverträge) | **864** |
| davon heute `TRADING` | 524 |
| davon heute nicht gehandelt | **340** (130 `SETTLING`, 210 nicht mehr gelistet) |
| davon mit ≥ 6 Monaten im Fenster 2021-12 bis 2026-08 | **171** |

Die 171 zerfallen in drei Arten, die **nicht** gleich behandelt werden dürfen:

| Art | Beispiele | Zahl (vorläufig) | Behandlung |
|---|---|---|---|
| **kein Krypto** — Aktien, ETFs, Rohstoffe, Indizes | AMZN, NVDA, TSLA, MSTR, COIN · EWJ, EWY · XAU, XAG, XPT, XPD, COPPER · DEFI, FOOTBALL, BLUEBIRD | ~21 | **ausgeschlossen** — eine andere Grundgesamtheit |
| **Umbenennung / Übergang** — dieselbe Wirtschaft unter neuem Ticker | EOS→A (2025-05), FTM→S (2025-01), MATIC→POL (2024-09), RNDR→RENDER (2024-07), MKR→SKY (2025-09), GAL→G (2024-08), KLAY→KAIA (2024-12), TOMO→VIC, DAR→D, AGIX/OCEAN→FET, LUNA→LUNA2 (Neustart nach dem Crash) | ~13 | **nicht als eingestellt zählen.** Ob der Nachfolger in unserer Menge ist und ob die alte Vorgeschichte fehlt, ist je Paar zu prüfen |
| **echt eingestellt** | FTT, SRM (FTX 2022), WAVES, OMG, REN, ANT, UNFI, BTCST, XEM, TROY … | ~135 | **nachladen** |

⛔⛔ **Zombie-Monate — ein zweiter Fund der Recherche:** nach der
Einstellung schreibt das Archiv weiter Monatsdateien. **FTMUSDT 2026-08:
744 Stunden, alle Kurse 0,7702, Volumen 0** (2024-12: echter Handel,
8,9 Mrd Volumen). Das echte Ende einer Reihe ist der **letzte Monat mit
Volumen**, nicht die letzte Datei. Die Zahl von 4.832 Symbol-Monaten ist
deshalb nur eine **Obergrenze**; die Reihenenden in der Recherche (*140 enden
2026*) sind wegen der Zombie-Monate **falsch** und werden erst beim Laden
richtig.

---

## 3. Was geladen würde

| Teil | Inhalt | Quelle (Archiv) | Abrufe (Obergrenze) |
|---|---|---|---|
| **A1 Kurse** | Stundenkerzen der ~135 eingestellten, **Spot** wo vorhanden (108 von 158 haben ein Spot-Archiv), sonst Terminmarkt | `spot/monthly/klines`, `futures/um/monthly/klines` | ~4.500 |
| **A2 Richtungsdaten** | Käuferanteil (Spalte 9 derselben Kerzen — **kein Zusatzabruf**), Premium-Index | `futures/um/monthly/premiumIndexKlines` | ~4.500 |
| **A3 funding** | Einzelsätze, zur Tagessumme verdichtet **wie** `hole_fremdreihen.py` | `futures/um/monthly/fundingRate` | ~4.500 |
| **A4 BTC** | Stundenkurse, Käuferanteil und Premium **2021-12 bis 2023-08**, `BTCDOMUSDT` 2021-12 bis 2022-12 | wie oben | ~80 |
| **B Terminmarkt** | OI, Konten-, Top-, Taker-Verhältnis (für `konten_verh`, `oi_aenderung`, `oi_je_umsatz`) | `futures/um/daily/metrics` — **Tagesdateien** | ~120.000 |

➤ **A** (rund 13.600 Abrufe): mit vier Arbeitern und 0,3 s Pause etwa
**30 bis 45 Minuten** — so schonend wie die Ladung vom 27.09. (2.661).
➤ **B** ist die Last: Tagesdateien, rund **4 bis 5 Stunden** mit vier
Arbeitern. Vorschlag: **erst A, messen, dann B** (siehe 5).

**Ablage:** eine **eigene Datei** `data/eingestellt_historie.db` mit denselben
Tabellen wie die bestehenden (stundenkurse, fluss, premium, funding, später
terminmarkt), dazu `_herkunft` (Markertabelle), `_geladen` (fortsetzbar) und
eine Tabelle **`symbole`**: Art (eingestellt / Umbenennung / kein Krypto),
Nachfolger, echtes Reihenende, Quelle (spot/um), Beleg.
⚠️ Die bestehenden Dateien bleiben **unverändert** — nur so lässt sich
jeder Befund bitgleich reproduzieren (R-R11). `messe_e2_beitraege.lade()`
bekommt einen Schalter `mit_eingestellten`.

⛔ **Nie:** `data/tradinginfotool.db` (Produktion). Der Lader verweigert
sie, wie `hole_richtungsdaten.py`. Das Notebook ist nicht betroffen — die
Datei ist Messbasis und bleibt am Desktop (wie `messdaten.db`).

---

## 4. Die Inhaltsprüfung — nicht nur laden, sondern prüfen, ob drin ist, was wir erwarten

Ein eigenes Prüfwerkzeug, wie `pruefe_richtungsdaten.py`:

| # | Prüfung | Soll |
|---|---|---|
| P1 | **Archiv gegen Bestand**: dieselbe Ladefunktion auf **drei heute gehandelte** Symbole anwenden und gegen `stundenkurse` / `funding_historie` halten | Kurse und Volumen **exakt** gleich; funding-Tagessumme gleich |
| P2 | **Zombie-Monate** erkennen: Stunden mit Volumen 0 und unverändertem Kurs am Reihenende | abgeschnitten, echtes Ende in `symbole` vermerkt |
| P3 | Zeitformat (Milli-/Mikrosekunden ab 2025), Doppelte, Lücken in Stunden | wie 2.661 |
| P4 | **Umbenennungen**: altes Ende = neuer Anfang (± 1 Monat), Nachfolger in unserer Menge? | je Paar belegt |
| P5 | **Kein Krypto** ausgeschlossen — Liste im Code, jede Zeile mit Grund | keine Aktie, kein Index in der Menge |
| P6 | Plausibilität: Käuferanteil ≤ Volumen, Premium-Größenordnung, der Absturz vor der Einstellung ist **echt** (Volumen vorhanden), nicht ein Dochtfehler | ausgewiesen |

---

## 5. Der Vergleich — mit gegen ohne

**Nach der Regel *„wer die Grundgesamtheit ändert, misst die Wirkung"*:**

1. **Reproduzieren (R-R11):** die Kernbefunde mit dem Schalter *aus* —
   müssen bitgleich herauskommen.
2. **Mit Eingestellten**, dieselben Werkzeuge, derselbe Stand:

| Befund | Werkzeug | braucht | nach A? |
|---|---|---|---|
| 2.662 Höhe (vola, volumenschub, oi_je_umsatz) | `messe_e2e_gegenpruefung_hoehe.py` | Kurse; oi_je_umsatz braucht B | ✔ teilweise |
| 2.665 / 2.666 Richtung (funding, Käuferanteil) | `messe_e2f_richtungsdaten.py`, `messe_e2h_startstunde.py` | Kurse, funding, Richtungsdaten | ✔ |
| 2.667 Liquidationsnähe | `messe_e2i_liquidationsnaehe.py` | Kurse | ✔ |
| 2.660 Sperre *viele Longs* | `messe_e3_gegenpruefung.py` | B | nach B |

3. **Die Zahl, die zählt:** wie viele Urteile kippen (trägt ↔ trägt nicht,
   Vorzeichen), wie weit verschieben sich die Werte — **je Befund**.

⚠️ **Gewichtung ausweisen** (stehende Regel): die 100 Gezogenen sind eine
Stichprobe aus den Überlebenden, die Eingestellten würden **vollständig**
geladen. Beides ungewichtet zu mischen, überzeichnet die Eingestellten.
Deshalb zwei Zahlen: **ungewichtet** und **gewichtet** (jedes gezogene
Symbol zählt mit dem Kehrwert seiner Ziehwahrscheinlichkeit; die Watchlist
zählt nicht zur Stichprobe).

---

## 6. Offene Fragen zur Abstimmung

| # | Frage | Empfehlung | Warum |
|---|---|---|---|
| **N1** | Alle ~135 echt eingestellten laden oder eine Stichprobe? | **alle**, gewichtet auswerten | eine Stichprobe von ~30 wäre zu klein für Aussagen je Jahr; gewichtet ist sie trotzdem unverzerrt |
| **N2** | A zuerst, B später? | **ja** | A deckt drei der vier Kernbefunde, B kostet das Zehnfache |
| **N3** | Anker kurz **vor** der Einstellung: heute fallen Anker weg, deren 72-h-Fenster über das Reihenende reicht — gerade dort liegt der Boden | Anker bis zum echten Ende **zulassen**, Ausgang am letzten echten Kurs (eine offene Position wird bei der Einstellung abgerechnet) | sonst fehlt der Absturz selbst, und die Verzerrung bliebe halb bestehen |
| **N4** | Umbenennungen: fehlt uns die **Vorgeschichte** des Nachfolgers (z. B. A erst ab 2025-05, EOS davor)? | je Paar prüfen und, wo es fehlt, die alte Reihe als **Vorgeschichte** anhängen (gekennzeichnet) | keine Überlebensverzerrung, aber eine Lücke in derselben Wirtschaft |
| **N5** | Spot oder Terminmarkt-Kurs, wenn beides fehlt/abweicht | **Spot** wo vorhanden, sonst Terminmarkt, Quelle je Stunde vermerkt | wie in 2.661; ⚠️ das **Volumen** ist zwischen den Quellen nicht vergleichbar (volumenschub ist assetintern, oi_je_umsatz nicht) |

---

## 7. ⚠️⚠️ PRÜFUNG UND GEGENPRÜFUNG DIESER VORANALYSE

**Prüfung — trägt der Plan die Regeln?**

| Regel | Prüfung |
|---|---|
| Produktion nie beschreiben | ✔ eigene Datei, Riegel gegen `tradinginfotool.db` |
| Messbasis ≠ Betrieb | ✔ Desktop, nicht Notebook; Betrieb unberührt (im Betrieb gibt es keine Eingestellten — die Regel verlangt sie für die **Messung**) |
| Grundgesamtheit ist keine Stellschraube | ✔ geändert wird sie mit Messung der Wirkung, beide Stände bleiben reproduzierbar |
| R-R11 | ✔ erst reproduzieren, dann mit/ohne |
| API schonend | ✔ Archiv statt API, Pausen, fortsetzbar |
| Inhalt prüfen, nicht nur laden (Nutzer) | ✔ Abschnitt 4, P1 gegen den Bestand |

**Gegenprüfung — wo kann der Plan selbst falsch sein?**

| # | Einwand | Antwort / Folge |
|---|---|---|
| G1 | *Sind die ~135 wirklich eingestellt?* Die Liste stammt aus dem heutigen Status; ein Paar kann eingestellt und **wieder** gelistet sein (TON?) | P4 prüft altes Ende und neuen Anfang; Wiederlistungen als eigene Art |
| G2 | *Die Einordnung Krypto / kein Krypto ist von Hand.* Eine vergessene Aktie verfälscht die Menge | Liste im Code mit Grund je Eintrag, dazu die Prüfung: kein Symbol mit Handel nur zu Börsenzeiten (Aktien-Perps haben Wochenendmuster) |
| G3 | *Zombie-Erkennung kann echtes Stillhalten treffen* (ein illiquider Coin ohne Umsatz) | abgeschnitten wird nur **am Reihenende** und nur bei Volumen 0 **und** konstantem Kurs über ≥ 72 h |
| G4 | *Die Gewichtung braucht die Ziehwahrscheinlichkeit* — die Zahl der möglichen Symbole am Ziehtag steht nur in der damaligen Ausgabe | aus dem Ziehtag rekonstruieren (Status und `messdaten`); geht das nicht genau, die Gewichtung als **Band** (untere/obere Annahme) ausweisen |
| G5 | *Das funding-Archiv könnte anders verdichtet sein* als `hole_fremdreihen.py` (API) | P1 hält die Tagessummen der drei Kontrollsymbole gegen den Bestand — exakt oder mit ausgewiesener Abweichung |
| G6 | *Die Eingestellten sind vor allem kleine, illiquide Werte* — mischt man damit eine andere Klasse hinein? | ja, und das ist der Punkt: genau diese fehlen heute. Im Vergleich getrennt ausweisen: Eingestellte allein, Überlebende allein, zusammen |
| G7 | *Der Abruf könnte das Archiv belasten* | Tagesdateien (B) erst nach Abstimmung; A in der Größe der Ladung vom 27.09. |
| G8 | *Die Recherche selbst* | ✔ Zahlen reproduzierbar mit `recherche_eingestellte_perps.py`; die Zombie-Monate an einer echten Datei belegt |

**Ergebnis:** der Plan hält die Regeln; offen sind die fünf Fragen N1–N5.
Zwei Funde aus der Prüfung stehen **vor** jeder Ladung fest: die
**Zombie-Monate** (Reihenende = letzter Monat mit Volumen) und die
**Umbenennungen** (nicht als eingestellt zählen).

---

## 8. ✔ UMSETZUNG UND VORAB FESTGELEGTER VERGLEICH (27.09.2026 abends)

**Nutzer:** *„N1 bis N5 wie empfohlen — bin mir nicht sicher, ob das hilft,
aber u. U. bringt es etwas. OK — prüfen und gegenprüfen."*

### 8a. Gebaut und geprüft, bevor die Vollladung lief

| | Stand |
|---|---|
| Lader `hole_eingestellte.py` | Einordnung aus dem **amtlichen** `underlyingType` (fand PAYP als Aktie, das die Namensliste übersehen hatte); 137 eingestellt, 5 Vorgeschichte (EOS→A, FTM→S, MATIC→POL, RNDR→RENDER, KLAY→KAIA), 7 Umbenennungen ohne Nachfolger in der Menge, 22 kein Krypto. ⚠️ **LUNA** und **NEIROETH** gelten als eingestellt — LUNA2 ist eine neue Kette, NEIRO ein anderer Token |
| Probelauf | 5 Paare, 0 Fehler; Zombie abgeschnitten: SRM 13.063 Stunden ab 01.12.2022, WAVES 19.007 ab 01.07.2024 |
| **P1 Archiv gegen Bestand** | ETH, SOL, LINK je 1.440 Stunden und 60 funding-Tage — **null Abweichungen** in Kurs, Käuferanteil, Premium und funding-Tagessumme |
| **Gegenprobe der Prüfung** | drei absichtlich eingebaute Fehler (ein Kurs +0,1 %, ein Zombie-Schwanz, eine Aktie in der Menge) — **alle drei erkannt** |
| P4 Übergang EOS → A | Verhältnis 0,974, keine Überlappung (die Vorgeschichte wird am Beginn des Bestands abgeschnitten) |
| Lader `messe_e2_beitraege` | Schalter `--menge`; ⚠️ **Gegenprobe:** mit `bestand` ist die Startstunden-Probe **bitgleich** zur gespeicherten Ausgabe (nur die neue Kopfzeile) |
| N3 | Anker bis zum echten Ende **nur**, wenn die Reihe vor dem Ladefenster endet (sonst ist das Ende unser Schnitt, keine Einstellung) |

### 8b. Der Ziehrahmen

Die 100 wurden am **01.09.2026** gezogen aus *Perpetual mit Status TRADING
∩ `messdaten.db`* — heute sind das **305**, die Ziehrate also **≈ 1 : 3**.
Der Rahmen am Ziehtag ist nicht gespeichert; 305 ist eine Näherung. Von den
Eingestellten liegen **117** im selben Rahmen (in `messdaten.db`). In
unserer E2-Menge sind **98 Gezogene und 17 Watchlist-Symbole**.

### 8c. Die drei Mengen

| Menge | Inhalt |
|---|---|
| `bestand` | wie bisher (115) — überlebensverzerrt |
| `mit` | Bestand + alle Eingestellten (+ Vorgeschichte) — überzeichnet die Eingestellten |
| `unverzerrt:<saat>` | nur die **98 Gezogenen** + die Eingestellten **aus demselben Rahmen** mit **derselben Ziehrate**, Saaten 1, 2, 3 — die Streuung über die Saaten wird ausgewiesen |

### 8d. Was verglichen wird — und was als *kippt* zählt (vorab)

| Befund | Werkzeug | kippt, wenn |
|---|---|---|
| 2.662 Höhe | `messe_e2e_gegenpruefung_hoehe.py` | eine der 14 tragenden Auswahlen nicht mehr trägt, oder eine nicht tragende trägt |
| 2.665 Richtung | `messe_e2f_richtungsdaten.py` | eine der vier tragenden Auswahlen nicht mehr trägt, oder eine neue trägt |
| 2.666 funding | `messe_e2h_startstunde.py` | das Mittel über die Startstunden das Vorzeichen wechselt oder um mehr als die Hälfte schrumpft |
| 2.667 Liquidationsnähe | `messe_e2i_liquidationsnaehe.py` | der Anteil −12 % binnen 72 h im obersten ATR-Fünftel um mehr als **2 Prozentpunkte** steigt |

Gerechnet wird je Werkzeug in der Reihenfolge `bestand` (Reproduktion) →
`mit` → `unverzerrt:1..3`, **nacheinander** (nie zwei große Läufe
gleichzeitig — 27.09.: Speicherabbruch). Terminmarkt-Merkmale
(oi_aenderung, konten_verh, oi_je_umsatz) haben für die Eingestellten noch
**keine Daten** (Teil B) — ihre Auswahlen vergleichen nur Symbole mit Daten;
das wird im Ergebnis ausgewiesen.

---

## 9. ✔ ERGEBNIS (28.09.2026) — Befund 2.669

| Befund | kippt? | Kern |
|---|---|---|
| 2.666 funding (Startstunden) | **nein** | negativ +0,025 / +0,026 / +0,025 / +0,025 (bestand / unverzerrt 1–3), 2022 bestätigt, Sperre −0,045 … −0,048 |
| 2.662 Höhe | 1 von 16 in 1 von 3 Saaten | vola P95 an der Tauschprobe P4 (Einzelziehung) — Werte eher stärker |
| 2.667 Liquidationsnähe | **nein** bei 5x (+1 Punkt), aber | **3x +17 bis +25 %, 2x +42 bis +65 %** — der Boden fehlte |
| 2.665 Richtung | Randurteile | Werte stabil; funding-Urteil 1/3, Sperre 0/3 (Jahre 2/4, Mitternachtsregel in E2f); Käuferanteil hoch 3/3; neu rsi hoch 3/3, Käuferanteil tief als Sperre 2/3 |
| Kontext | nein | BTC↑ und Dominanz↑ q5 −0,019 überall; BTC↑ und Dominanz↓ q15 +0,10 |

⛔⛔ **Die Prüfung P1–P6 hatte eine Lücke**, die erst der Vergleich zeigte:
N3 schaltete die Lückenprüfung ab (LUNA: Anker sahen ins neue LUNA,
50 Mio % Anstieg, 71 % der MFE-Summe) und Zombies mitten in Reihen blieben
stehen (FTT 6.575 h). Behoben, P7/P8 ergänzt, beide mit Gegenprobe.
Der erste Vergleichslauf wurde verworfen und ganz neu gerechnet.

➤ **Folge:** Messbasis für die Kombination ist `--menge unverzerrt`
(mehrere Saaten); der dickere Liquidationsrand gehört in K6.
