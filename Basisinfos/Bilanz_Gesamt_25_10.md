# Gesamtbilanz R-3 — TradingInfoTool (Stand 25.10.2026)

**Wozu:** Nutzer 25.10.: *„ja R-3 so schreiben, prüfen gegenprüfen und doku – lege mir das Ergebnis als docx Datei auf den Desktop, zuvor prüfe aber ob Fehler und wo Fehler passiert sind, wurden alle Prüfregeln eingehalten?“*

**Aufbau:**
- **Teil A** ist der Prüfbericht: Wo sind Fehler passiert, und wurden die Prüfregeln eingehalten?
- **Teil B** ist die Gesamtbilanz aller Ansätze, gegliedert wie am 25.10. abgestimmt.

**Wie geprüft wurde:**
- Drei unabhängige Prüfaufträge:
  - eine Bilanztabelle aus E-1 bis E-140 und den Registern;
  - ein Audit der Prüfregeln für E-126 bis E-140 über git-Log, Zeitstempel, Pläne und Skripte;
  - die Suche nach früheren Urteilen mit einer Nullwelt, die die Tagesballung nicht kennt.
- Jeder Hinweis, der ein Urteil berührt, ist von mir an der Quelle **nachgeprüft**; das ist je Zeile vermerkt.
- Zahlen-Stichprobe gegen die Entscheidungen: 6 von 6 gleich.

---

# Teil A — Prüfbericht

## A.1 Die Prüfregeln

| # | Regel | Quelle |
|---|---|---|
| R1 | Messplan und Auslegung **vorab committet**, vor dem ersten Lauf | Messstandard, Praxis „VORAB“ |
| R2 | **Selbsttest vor dem ersten Blick** bei jeder neuen Nullwelt; bei geballten Signalen mit Zufallsregeln, die die Ballung behalten | Memory-Regeln 22.10. und 24.10. |
| R3 | **R-R11:** erst reproduzieren, dann eine Größe ändern | CLAUDE.md |
| R4 | **Gegenprobe auf einem zweiten Weg**, nicht dieselbe Rechnung noch einmal | Nutzer „prüfen, gegenprüfen“ |
| R5 | **Gewichtung ausweisen** (je Handel **und** je Tag); Unsicherheit über Tage; Nullwelt tagestreu | Memory 16.10.; sechs Prüfungen Nr. 1 (27.09.) |
| R6 | **zweiseitig**, wo keine fachliche Richtung besteht; den anderen Rand nicht nachträglich deuten | Memory |
| R7 | **Nicht-Verwerfen ist kein Haken**; bei zu wenig Auflösung heißt das Urteil „nicht entscheidbar“ | Memory, Manual |
| R8 | **Produktions-DB nie beschreiben** | CLAUDE.md |
| R9 | **Nutzer-Ja** vor Bau, Betriebsänderung und Download; Voranalyse vor jedem Schritt | CLAUDE.md, Memory |
| R10 | **Sechs Prüfungen** vor einem Hebel-Befund (tagestreu, Kalenderjahre, Weglassprobe, Mehrfachtesten, Ebene, je Asset) | Memory 27.09. |
| R11 | **Grundgesamtheit** in Betrieb und Messung gleich | CLAUDE.md |
| R12 | **Doku-Pflichtliste** | Zentraldokumente |

## A.2 Das Ergebnis in Kürze

- **Formal sauber:**
  - Jeder Messplan ist **vor** seiner Ergebnisdatei committet.
  - Die Produktions-DB wurde **nie** beschrieben.
  - Jeder Bau, jeder Download und jede Betriebsentscheidung hatte dein Ja.
  - Seit dem 22.10. lief der Selbsttest konsequent vor dem ersten Blick; er hat fünfmal Fehler der Messanlage gefunden, bevor sie ein Urteil verfälschen konnten.
- **Inhaltlich gibt es acht Stellen, an denen bestehende Regeln verletzt oder Urteile zu stark formuliert wurden.** Vier davon waren bisher nicht dokumentiert (A.3). Keine davon kehrt ein „trägt nicht“ in ein „trägt“ um. **Zwei frühere „trägt“ halten der Prüfung nicht stand:**
  - die Festschreibung der REGEL0 vom 29.09. (E-36);
  - „REGEL0 trägt auf Kraken“ (E-130).
- **Der wichtigste Einzelfehler** ist eine Nullwelt aus Zufallsstunden, die die **Tagesballung** der REGEL0 nicht kennt. Gegen diese Nullwelt melden Zufallsregeln in 30 % der Fälle fälschlich „trägt“. Die Regel, die das verbietet („Nullwelt tagestreu“), gilt seit dem 27.09. und wurde in E-131 und E-132 trotzdem nicht angewendet.

## A.3 Verstöße und zu starke Urteile (von mir an der Quelle nachgeprüft)

| # | Wo | Was | Regel | Wirkung aufs Urteil | Stand |
|---|---|---|---|---|---|
| 1 | **E-36 / 2.688** Festschreibung REGEL0 (29.09.) | Das Tagesblock-Kriterium B6 prüfte „untere Grenze > 0“ statt gegen den Prüfzeit-Versatz (E-11 vom 28.09. verlangt das). Untere Grenzen +0,0199 / +0,0156 / **+0,0057** / **+0,0106** gegen das Nullmittel +0,0168 / +0,0131 / **+0,0156** / **+0,0127** ⇒ **2 von 4 Mengen** hätten nicht bestanden. Die Ruhe 48 h wurde ganz ohne Tagesunsicherheit übernommen | R5, E-11 | Die REGEL0 war schon bei der Festschreibung **nicht voll bestätigt**. Heute durch E-139 überholt | nachgeprüft (`messe_losfahren.py` B6; `Kern_29_09/best__*.txt`) — **neu** |
| 2 | **E-130** „REGEL0 trägt auf Kraken-Perps“ | Das Urteil beruht auf **Punktwerten** je Jahr. Das selbst ausgewiesene Tagesblock-Band (unverzerrt −0,35 bis +0,79 %) schließt die Null ein. Die Abdeckung (47 %) liegt unter dem eigenen Kriterium (50 %). Gerechnet wurde nur je Handel | R5, R7 | richtig wäre **„nicht entscheidbar“**; nach E-139 ohnehin ohne Grundlage | nachgeprüft (Voranalyse Kosten Z. 72/106) — **neu** |
| 3 | **E-131** Befund „REGEL0 schlägt den Markt um +0,6/+0,3 Pp, Rang 1,00“ | Die Nullwelt war **nicht tagestreu** (30 % Fehlalarm, E-139). Je Tag gewichtet ist der Vorsprung negativ. E-132 und E-133 zitieren den Befund weiter | R5, R10 Nr. 1 | Das **Urteil** „trägt nicht“ bleibt; der **Befund** ist zu stark | vermerkt in E-139; in E-131 selbst fehlte er — **jetzt berichtigt** |
| 4 | **E-132** E-A Kaufzeitpunkt | derselbe Nullwelt-Typ, dazu **Pseudo-Replikation**: Die vier Mengen teilen sich dieselben Coin-Monate (108 bzw. 72 Fälle). Die Ränge 0,00/1,00 und Regime 0,03/0,99 sind überzeichnet | R5, R2 | Das Urteil „trägt nicht“ bleibt; „Wartedrift, kippt mit dem Regime“ ist nur eine Tendenz | aus dem Audit, Mechanismus wie Nr. 3 — **neu** |
| 5 | **E-135** Indikator-Atlas | (a) **„Nasdaq und Stablecoins laufen nach“ ist falsch.** Die Nachlauf-Ränge 0,05/0,07 und 0,00/0,33 zeigen keinen Nachlauf, das war eine Deutung des anderen Rands. (b) **Fear & Greed ist ein Grenzfall:** erste Hälfte nur n = 13 (2018–19), Rang in der Gegenprobe 0,955. (c) „Geldausweitung keine Voraussetzung“ folgt aus dem **Nicht-Verwerfen**, ohne Positivkontrolle; tragfähig ist nur die Beschreibung (Zyklus 2022–25 lief bei schrumpfenden Notenbank-Bilanzen) | R6, R7 | Der Kandidat F&G war schwächer als dargestellt (F-1 Fassung 2 ist ohnehin abgebrochen). Das Lagebild zeigt F&G nur als Fakt, daran ändert sich nichts | nachgeprüft (`p75_atlas_t1_krypto.txt` Z. 17–20, `p75_gegenprobe.txt`) — **neu** |
| 6 | **E-139** Messplan R | **Geltungsbereich zu weit:** Geprüft wurde nur die Menge *bestand*; die +0,30 % unverzerrt aus E-128 sind nicht nachgeprüft. Der „echte Vorsprung der Referenz“ gilt nur je Handel (je Tag −0,24 %). Je Handel allein wäre Kriterium (2) 6/6; das 0/6 kommt aus der vorab festgelegten Je-Tag-Bedingung. Das ist korrekt, war aber nicht hervorgehoben | R3, R12 | Das Urteil bleibt; der Wortlaut lautet jetzt „für die Menge *bestand*“ | **jetzt berichtigt** |
| 7 | **E-134** Voranalyse Historie | Die Fundquote 31 → 84 % ist ohne Streuband angegeben (Gegenprobe: 40 → 77 %, also etwa ±9 Pp). Die Grundannahme „die REGEL0 feuert 2020–22“ ist durch E-136 widerlegt, im Eintrag aber nicht nachgetragen | R4 | Die Begründung für den Download war zu optimistisch | **jetzt berichtigt** |
| 8 | **E-127** Grid Fassung 1 | Der Selbsttest kam erst **nach** dem ersten Blick (in der Gegenprobe G3). Das Urteil über die Auflösung war nicht vorab geplant | R1, R2 | Das Urteil „Grid endet“ ist robust: Selbst die zehnfache Stärke reicht nicht | dokumentiert; der Wortlaut „bevor ein Ergebnis bewertet wurde“ wird präzisiert |

## A.4 Schwächen im Vorgehen, ohne Wirkung auf ein Urteil

- **Je-Tag-Zahl fehlte** in E-128, E-130, E-131 und E-136, obwohl 99 % der Differenz an Tagen mit vielen Signalen liegen (E-138).
- **Gegenproben, die nur nachrechnen:** E-126 G1, E-128, E-131, E-135 G1. Echte zweite Wege waren E-127 G4, E-132 G5, E-138 G2 und E-139 G1/G2.
- **Nicht reproduzierbar:**
  - Die Zwischenfassungen p69 und p70 Fassung 1 sowie Grid Fassung 2 sind nur als Ausgabe erhalten.
  - Für die M-L-Ursachensimulation und die E-133-Tabelle „Ursache nachgerechnet“ gibt es kein Skript.
- **Auslegungen nur im Skriptkopf** (E-126), nicht als eigener Commit vor dem Lauf.
- **E-136 G2** hatte keinen ersten Weg im Repository; bestätigt wurden die Werte erst durch p82/p83.
- **Grundgesamtheit (R11):** Ob der Betrieb am Notebook dasselbe `st0` (Reihenbeginn) hat wie die Desktop-Referenz, ist nicht geprüft. Nach E-139 ist das die Größe, an der alles hängt.
- **Doku-Lücken:**
  - `hebel_neubau.py` (NEUESTER_STAND), `Regelwerk_Hebel_Bewertung_27_09.md`, `UEBERGABE_Hebelneubau_27_09.md` und `bestand.py` (Register) stehen auf dem 02.–16.10.;
  - §23.x in Schritt7 fehlt für das Betriebspaket E-137;
  - der rote Suite-Lauf „Makro“ (NFCI-Revision) stand nur im Memory.
- **Kosmetisch:** doppelter Punkt „Stand 24.10..“ in den Spot-Mails.

## A.5 Eigene Fehler dieser Serie, dokumentiert und behoben (21.–25.10.)

| Fehler | entdeckt | Wirkung |
|---|---|---|
| Grid: Umordnungs-Nullwelt fixiert das Monatsende; die Nullwelt mit Monatsdrift war auf das echte Ende zentriert | Selbsttest (Fassung 1 erst nach dem Blick) | ohne Selbsttest wäre „Trend“ falsch gemeldet worden |
| M-L: zweiseitiges Selbsttest-Kriterium falsch geeicht | Selbsttest vor dem Blick | keine |
| E-A: Zielgröße durch Konvexität verzerrt (+0,52 %) | Selbsttest vor dem Blick | keine |
| Atlas T2: Nullwelt verglich den Anteil statt der Differenz | vor der Bewertung | nur eine Auskunftszeile |
| Gegenproben-Fehler (Suchmuster `%%`, Erwartung „13 + 1“) | in der Gegenprobe | keine |
| `a1_gegenprobe.py` überschrieben | danach | aus git wiederhergestellt |
| Zählfehler 6 statt 9 Halbjahre im Messplan | vor dem Lauf | ausgelegt (6 von 9) |
| Abgeschnittene Binance-Archivkerzen | vor der Messung | per REST ersetzt |
| τ² „in allen Monaten“ (gerundet; richtig 32/33) und Gewichtung nur je Handel | Gegenprobe | berichtigt |
| Planschwäche R: Starts bis 2021-12 identisch | danach | vermerkt |

## A.6 Was daraus für die Messanlage folgt (ab sofort Regel)

1. Bei **jedem** Signal mit Tagesballung: Rang über **Tagesblöcke** und Selbsttest mit Zufallsregeln, die die Ballung behalten. Ergebnis **je Handel und je Tag**.
2. **„Trägt“ verlangt das Band**, nicht den Punktwert; schließt das Band die Null ein, heißt das Urteil „nicht entscheidbar“.
3. **Gegenprobe = zweiter Weg.** Eine Nachrechnung derselben Formel zählt nicht als Gegenprobe.
4. **Zwischenfassungen committen**, bevor sie überschrieben werden.
5. **Geltungsbereich nennen** (Menge, Zeitraum, Gewichtung) in jedem Urteilssatz.

---

# Teil B — Gesamtbilanz

## B.1 Ziel und Maßstab

> **Das System soll je Asset und Handlung eine neutrale, begründete Aussage über das POTENTIAL liefern. Wenn ein Asset ein bestimmtes Potential erreicht, soll ein Handelssignal kommen.**

**Maßstab:**
- „Trägt“ heißt: nach Kosten, gegen eine geeichte Nullwelt, über Kalenderjahre stabil, mit Band statt Punktwert.
- **Fakt** heißt: beschreibt die Gegenwart und löst nichts aus.

## B.2 Alle Ansätze im Überblick (Status nach Teil A berichtigt)

Status: **T** trägt · **TN** trägt nicht · **NE** nicht entscheidbar · **F** Fakt gebaut · **O** offen

### Hebel / REGEL0

| Ansatz | Ergebnis | Status | E |
|---|---|---|---|
| Einzelmerkmale (rsi, ema, Bandenge, Trend, Marktmerkmale, Kontext) | einzeln nicht trennbar, kombiniert E[R] ≈ 0 | TN | E-7, E-10/11 |
| Kern rsi-Ersteintritt + ATR | „trägt 4/4“ vor Kosten (29.09.); gegen den Versatz nur 2/4 (A.3 Nr. 1) | TN (berichtigt) | E-26, E-36 |
| Hebelkonto mit Kosten 0,48 % | verliert in 4/4 Mengen | TN (Kosten) | 2.690, E-39 |
| Positionsführung, Stabilisierung, Mindestliquidität, Short, Richtung | je nicht bestanden | TN | E-32, E-38, E-39, E-41 |
| ATR für die Hebelstufe | trägt die Liquidationsgefahr | T (Schutz) | 2.681 |
| Halten über 24 h | kostet netto 0,3–0,4 % je Tag | F | E-123 |
| A1: alle Hebel gegen die Kostenlücke | keiner schließt sie | TN | E-128 |
| Kraken Pro | Band schließt 0 ein, Abdeckung 47 % | **NE (berichtigt)** | E-130 |
| Limit-Einstieg, Haltedauer 4 h, Auswahl nach Schwankung | tragen nicht | TN | E-130, E-131 |
| Marktfilter F-1 | selbst ein Orakel ist nicht von Zufall zu trennen | NE | E-133 |
| **Robustheit (Messplan R)** | **nicht robust**; das Plus entsteht allein aus der Reife-Regel am Datenbeginn; je Tag überall negativ (Menge *bestand*) | **TN** | E-136, E-138, E-139 |

### Spot

| Ansatz | Ergebnis | Status | E |
|---|---|---|---|
| Kaufzeitpunkte (Klima, Boden, Momentum, Zyklus, Makro, MACD, Listings) | schlagen regelmäßiges Kaufen bzw. BTC nicht | TN | E-59–E-64, Spot §14–40 |
| Altcoin-Spot gegen Akkumulation | Korb ab 2024 −57 % gegen BTC | TN | Spot §10.8 |
| Regelmäßiges Kaufen BTC/ETH/SOL 70/20/10 | nicht zu schlagen | Grundlage | E-68/69 |
| Watchlist-Ordnung des Fortbestands | ordnet in der Klasse (E3 +13,9 Pp), findet Ausbrüche nicht | T (Ordnung) | E-71–E-74 |
| **B1 Mitnahme ×3** | +4,87 Pp, Rang 1,00 | **T (Schadensbegrenzung)**, an | E-91, E-100 |
| **B4 Abbau unteres Fünftel** | −12,5 Pp gegen Zufall, Rang 0,000 | **T (Schadensbegrenzung)**, an | E-101, E-107 |
| B3 Upbit-Listing | gebaut wie gemessen | F/an | E-103 |
| Einstieg je Asset (U1/U2, O31) | mit freien Daten nicht belegbar | TN/NE | E-85, E-102 |
| Inventur gegen Inflation | keine Regel schlägt die Inflation | TN | E-105/106 |
| Trendallokation BTC ↔ EURCV | verspätet an beiden Enden | TN | E-126 |
| E-A REGEL0 als Kaufzeitpunkt | trägt nicht (Ränge überzeichnet, A.3 Nr. 4) | TN | E-132 |
| **Season-Ampel** | Holdout 2017/18 trägt; Season-Klima 76 % gegen kalt 0 % | **F + Mail** | E-124 |
| Verwässerung, Freigabe-Rhythmus | Vorprüfung deutlich (p 0,0005); Urteil frühestens 10/2027 | F | E-108–E-110 |

### LLM

| Ansatz | Ergebnis | Status | E |
|---|---|---|---|
| elf Prüfwege (Trader, Entscheider, N4, N5, A2, Ankündigungen, Nachrichten L-C/L-C2 …) | keiner trägt; „Information ist der Engpass, nicht das Modell“; Gemini kennt 2025 | TN | E-125 |

### Makro / Markt / Lagebild

| Ansatz | Ergebnis | Status | E |
|---|---|---|---|
| Makro-Umfeld, 9 Kanäle | nicht entscheidbar | F (O54) | E-104, E-114 |
| Indikator-Atlas | kein Makrokanal läuft vor; F&G Grenzfall; Nachlauf **nicht** belegt (berichtigt) | F | E-135 |
| Rezession als Größe für Aktien | Nasdaq jedes Mal −24 bis −68 % | F | E-135 |
| **Lagebild L1–L6 + HY** | Rezessionsampel bestätigt, warnt nicht vor | **F** | E-137 |
| Recherche neue Ansätze | kein Rendite-Vorteil nach Kosten belegt; belegt sind Prämien und Bremsen | TN (Rendite) | E-129 |

### Grid, Börse, Kosten

| Ansatz | Ergebnis | Status | E |
|---|---|---|---|
| Grid | Rückkehr zur Mitte rund zehnmal zu klein für die Gebühr | TN | E-127 |
| Fusion | steuereinfach, aber ohne Hebel 0,50 % je Runde | F | E-126/128 |
| Cash-and-Carry, Carry | bei Bitpanda nicht umsetzbar; Prämie eingebrochen | TN | E-129 |

## B.3 Was belegt trägt, und wofür

| Baustein | Wofür | Beleg |
|---|---|---|
| B1 Mitnahme ×3 | **Schadensbegrenzung** (einziges netto Belegtes) | E-91, E-100 |
| B4 Abbau-Reihenfolge | **Schadensbegrenzung** | E-101, E-107 |
| Watchlist-Ordnung | **Ordnung/Information**, kein Kaufsignal | E-71–E-74 |
| ATR-Hebelstufe | **Schutz** vor Liquidation | 2.681 |
| Season-Ampel | **Fakt/Gewicht** für das Altcoin-Klima | E-124 |
| Lagebild, Rezessionsampel, Termin, Verwässerung, Haltedauer | **Fakten** | E-113, E-123, E-109, E-137 |
| Regelmäßiges Kaufen der Kernwerte | **Grundlage** | E-68/69 |
| Extern belegt: gehaltene Prämien, Bremsen für Rückgänge, niedrige Kosten | **Portfolio**, bei uns nicht gemessen | E-129 |

⚠️ **Kein Einstiegssignal mit belegtem Vorsprung**, weder für Hebel noch für Spot.

## B.4 Woran es scheitert

| Ursache | Beispiele |
|---|---|
| **Kosten über dem Vorteil** | 2.690, E-128, E-127 |
| **negative Drift der Altcoins** | E-131, E-106, E-107 |
| **Signal zu schwach oder nicht isolierbar** | E-7, E-22, E-117, E-102, LLM A2 |
| **mehr Bewegung statt Richtung** | E-28, vola |
| **Auflösung, Fallzahl, Rauschen** | E-104, E-133, E-37, O21 Stufe 2 |
| **Verspätung**, Zeitpunkt nicht vorab erkennbar | E-126, E-137, E-124 |
| **Regimeabhängigkeit** | E-117, E-130 (2026), E-132 |
| **Datenlage, Grundgesamtheit, Überlebensverzerrung** | E-30, **E-136/E-139** |
| **LLM: Information und Kontamination** | E-125 |
| **beim Broker nicht umsetzbar** | E-129, E-131, E-130 |
| **nach der Veröffentlichung verschwunden** (extern) | E-129 |
| **Fehler der Messanlage** (vom Selbsttest gefunden) | E-104, E-127, E-139 |

## B.5 Was wir über die Messanlage gelernt haben

- **Tagesballung:** Signale, die sich an Markttagen ballen, brauchen Tagesblöcke. Sonst sind Ränge bis zu sechsmal zu optimistisch (30 % statt 5 % Fehlalarm).
- **Datenbeginn:** Eine Reife-Regel („ein Jahr ab Reihenbeginn“) macht das Ergebnis vom Sammelbeginn abhängig. Unser Sammelbeginn folgte den Terminmarktdaten, nicht dem Kurs.
- **Quelle:** Archivdaten sind nicht fehlerfrei (abgeschnittene Kerzen); ein Abgleich mit der Quelle des Bestands ist Pflicht.
- **Revisionen:** FRED (NFCI) und DefiLlama ändern Werte rückwirkend; Prüfungen auf exakte Gleichheit fallen dann fälschlich.
- **Selbsttest wirkt:** Er fand Fehler in Grid, M-L, E-A, F-1 und R, jedes Mal **bevor** ein falsches Urteil entstand, mit einer Ausnahme (Grid Fassung 1).

## B.6 Offene Spuren mit Aussicht

| Spur | was | Aufwand | Risiko |
|---|---|---|---|
| **R-1 neue Reife-Fassung** | Das Modell lernt bewusst ohne die großen etablierten Coins; vorab registriert, Test auf 2020–23 (unberührt) | 1–2 Tage | aus dem Ergebnis abgeleitet, geringe Aussicht |
| **K-b marktweite Tage** | ein Signal auf den Markt (BTC/ETH) an Tagen mit breiter Bewegung, nur wenn Ampel und Lagebild nicht dagegen stehen | 2–3 Tage Voranalyse | 2024–26 ist gesehen; Test nur auf 2020–23; die Definition „breiter Tag“ darf nicht aus der REGEL0 kommen |
| **R-2 Risikosteuerung des Bestands** | wie viel Krypto bzw. Altcoins, wann bremsen (Ampel, Lagebild, B1/B4, Bremsen aus R-A) | Voranalyse 1 Tag | belegt ist Schadensbegrenzung, kein Rendite-Vorsprung |
| **Geltungsbereich E-139** | die unverzerrten Mengen nachrechnen (eingestellte Paare) | 0,5 Tag | bestätigt vermutlich nur |
| **Grundgesamtheit NB** | `st0` am Notebook gegen den Desktop prüfen | gering | Faktfrage |
| Entscheider (O22) | bräuchte **eigene** Information | offen | E-125 |

## B.7 Bausteine für eine Kombination (Grundlage für Frage 2, ohne Entscheidung)

| Baustein | Belegstand | mögliche Rolle |
|---|---|---|
| Season-Ampel | trägt auf dem Holdout (zwei Zyklen) | Gewicht für den Altcoin-Anteil |
| Lagebild / Rezessionsampel | Fakt; ROT bestätigt eine Rezession | Gewicht für das Gesamtrisiko |
| B1 Mitnahme, B4 Abbau, Führung | Schadensbegrenzung belegt | Ausstieg und Abbau |
| ATR-Hebelstufe | Schutz belegt | Größe einer Hebelposition |
| REGEL0-Signaltage | Plus nur an marktweiten Tagen, aber **nicht robust** | allenfalls Hinweis auf einen Markttag (K-b) |
| Regelmäßiges Kaufen | Grundlage | Einstieg Spot |
| Einstiegsgeber je Asset | **keiner belegt** | Lücke |

## B.8 Was heute im Betrieb läuft

- **REGEL0-Hebelmails:** unverändert (E-140), mit Fakt-Zeilen für Makro, Lagebild, Termin, Verwässerung, Messstand und Hebel-Trades. Der LLM-Block ist markiert „trennt nicht“.
- **Spot:**
  - B1 Mitnahme, B3 Upbit, B4 Abbau;
  - Season-Ampel-Mail bei Stufenwechsel;
  - Hebelführung H15.
- **Statusseite:** Makro und Lagebild oben, Season-Ampel, Messstand, Hebel, Betrieb.
- **Ruhend:** Marktscan, Thesen-Jobs, alte Spot-Kette, alter Hebelweg.
- **Am Notebook noch offen:** K-GM-1 (Lagebild) und die übrigen Kontrollen im nächsten Bündel.
