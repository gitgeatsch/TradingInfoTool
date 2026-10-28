# Konzept „Lagegerechte Handlung“ — die Signale in Schichten, die Handlung nach den Gegebenheiten (27.10.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Nutzer 27.10.2026:**
- *„… ich will die SIGNALE nicht verwerfen, sondern diese sollen über mehrere Schichten anders gelagert sein“*
- *„die Mischung von Strategien und Assetklassen soll ohnehin passieren – das kann man zwar planen, ist aber keine Systemfunktion per se“*
- *„beides im Konzeptblatt“* (Strategie-Mischung und Dashboard)
- *„… die Handlung aufgrund der passenden Gegebenheiten, das musst du primär als Ziel sehen – prüfen gegenprüfen und doku“*
- davor: *„… es macht keinen Sinn, die Messungen zu wiederholen, sondern du sollst mit mir andere Ansätze durchgehen … zuerst muss das Ganze in der Simulation und Messung funktionieren, bevor wir etwas bauen“*

**Status:** Konzept zur Abstimmung. **Kein Bau, keine Betriebsänderung.** Entscheidung E-165.

---

## 1. Das Ziel in einem Satz

> **Zu jedem Auslöser die Handlung, die zu den Gegebenheiten passt – und die Begründung je Schicht, warum sie passt.**

| | bisher | neu |
|---|---|---|
| **Frage** | *Trägt das Signal?* (ja/nein, eine feste Handlung: REGEL0 = Hebel long 24 h, fester Positionswert) | *Welche Handlung passt, wenn das Signal kommt?* (eine aus einem Katalog) |
| **Signal** | Urteil | **Anlass** für eine Prüfung, bleibt erhalten |
| **Lage, Umfeld, Asset** | Filter im Trichter (Blocker) oder Mailtext ohne Folge | **Schichten**, die die Handlung verschieben (Gewicht, kein Blocker) |
| **Mail** | viel Kontext, wenig Essenz | **eine Handlung**, dazu je Schicht ein Satz *dafür/dagegen* |

**Abgrenzung:** Die Mischung von Strategien und Anlageklassen ist **Planung**, keine Systemfunktion (§8). Das Dashboard ist eine **Ansicht** derselben Schichten (§7).

---

## 2. Ausgangslage — sortiert nach der Frage, die eine Handlung beantworten muss

Jede Handlung beantwortet vier Fragen: **Ob** (handeln überhaupt), **Welches** (Asset), **Wann** (Einstieg) und **Wie** (Instrument, Größe, Hebel, Haltedauer, Ausstieg). Unsere Messungen ergeben ein klares Muster:

| Frage | Stand | Beleg |
|---|---|---|
| **Ob** – steigt der Markt, welches Regime? | ⛔ nicht vorab erkennbar. Die Grenze ist die Zahl der Regimewechsel, nicht die Rechenzeit; selbst ein Orakel-Filter ist von Zufall nicht zu trennen | 2.599 · E-133 · E-126 |
| **Welches** – Auswahl des Assets | ◐ auf 12 Monate geordnet (Fortbestand, B4), auf 1 Monat und 24 h nicht belastbar | E-142 · E-154 |
| **Wann** – Einstieg je Asset | ⛔ die REGEL0 ist nicht robust (Plus nur aus der Reife-Regel am Datenbeginn) | E-139 · E-156 |
| **Extreme** – kurze, hohe Anstiege | ✔ `momentum_kurz` und `rsi` ordnen die Extreme (Fall-Kontrolle, Lift ≈ 1,9 unter der strengsten Kontrolle), obwohl sie im Mittel nichts bewegen | 2.648 · 2.597 |
| **Wie – Risiko** | ✔ **die ATR zum Einstieg sagt die Liquidationsgefahr je Hebelstufe allein voraus** (5x vorwärts kalibriert, 3x geordnet) | 2.681 |
| **Wie – Größe** | ◐ Größe ∝ 1/ATR: Richtung überall Bremse **ohne Ertragsverlust**, nach Plan nicht trennbar | E-158 (V-1) |
| **Wie – Ausstieg Spot** | ✔ L: ab ×3 die Hälfte verkaufen, +5,5 Pp gegen Halten, Rang 1,00 gegen Zufall · ◐ Nachlauf/Notbremse (−42 % → −4 % im E3-Korb) knapp **nicht** bestätigt | Spot §31.6–31.8 · §21.6 |
| **Kombination vieler Merkmale** | ⛔ trägt nicht, als gemeinsames Kurvenmodell (q, Richtung) und nach Mehrfachtest | 2.677 · 2.678 · 2.645 |
| **LLM als Urteil** | ⛔ kein messbarer Mehrwert; der Entscheider wurde Echo bzw. Mitte | E-125 · E-82 |

> **Das Muster: Die RICHTUNG ist kaum vorhersagbar, das RISIKO schon.**
> *„Er sagt die GRÖSSE, nie die RICHTUNG. Volatilität clustert …“* (Befundkarte, ATR)

Daraus folgt der Ansatz dieses Konzepts: **Die Gegebenheiten sollen vor allem das *Wie* bestimmen** – dort steckt messbare Information. Das *Ob* bleibt Fakt und Gewicht.

### 2a. Woher der Vorteil kommen soll — und warum die REGEL0 allein nicht reicht

**Nutzer 27.10.:** *„REGEL0 ist kein neuer Ansatz – was ist hier anders, wie entsteht ein Vorteil, und zwar für die Zukunft? Bei einem neuen Ansatz kann REGEL0 als Ausgangsbasis dienen, leistet alleine aber kaum etwas.“*

**Einverstanden:** Die REGEL0 ist hier nur **einer von mehreren Auslösern**. Ihr eigener Vorsprung ist nicht robust (E-139). Neu ist nicht der Auslöser, sondern **was nach ihm geschieht**. Vier mögliche Vorteilsquellen, geordnet nach der Wahrscheinlichkeit, dass sie auch **künftig** halten:

| # | Vorteilsquelle | Mechanismus | Warum es auch künftig halten könnte | ehrliche Erwartung |
|---|---|---|---|---|
| **V1** | **Risiko passend zur Lage** (Stufe und Größe nach ATR/DVOL) | gleicher Ertrag mit weniger Liquidationen und kleineren Rückgängen. **Mehr Ertrag je Risiko erlaubt bei gleichem Gesamtrisiko einen größeren Einsatz** – so wird ein Risikovorteil zum Ertragsvorteil | Volatilität clustert, ein **Mechanismus**, kein Muster; seit Jahrzehnten in allen Märkten belegt; bei uns 2.681 (ATR → Liquidationsgefahr) | am wahrscheinlichsten; V-1 zeigt die Richtung, war aber allein nicht trennbar |
| **V2** | **Gewinner laufen lassen** (Haltedauer 24 h bis 5 T und länger, geführt) | Asymmetrie T2: kurz bei Gegenwind, lang bei Rückenwind, **beendet durch die Führung** statt durch eine Regimeprognose | Trendfolge lebt seit einem Jahrhundert davon (Hurst/Ooi/Pedersen); bei uns 2024 H168 brutto +3,4 bis +4,3 % gegen H24 +1 % | **größtes Potential, größte Unsicherheit:** 2025–26 war es umgekehrt (§23.68); feste Stops retteten längeres Halten dort nicht (2.702). Wie gut die Führung trennt, ist die eigentliche Frage |
| **V3** | **Mehrere Auslöser, je mit der passenden Handlung** | die Extreme (`momentum_kurz`/`rsi`, 2.648) → kurz; Dominanz-Spitze (Spot §32.1) → Alt-Spot gestaffelt, 3–9 Wochen; Upbit-Listing → Mitnahme; REGEL0 → Prüffall | jeder Auslöser hat ein **eigenes Zeitmaß**. Bisher wurde jeder mit **einer** Handlung (Hebel 24 h) geprüft, das passte oft nicht | einzeln schwach; das Zusammenwirken ist nur über die Handlungswahl messbar, nicht additiv (E-142) |
| **V4** | **Nicht handeln bei mehreren Gegenwinden** | Verluste vermeiden, T3 | Bremsen sind belegt (E-129) | am nächsten am Marktfilter; bisher nicht entscheidbar (E-133), daher **getrennt** ausweisen |

**„Für die Zukunft“:** Ein Vorteil, der auf einem **Mechanismus** beruht (V1, die Führung in V2), hält eher als einer, der auf einem **Muster** der letzten drei Jahre beruht. Deshalb kommt V1 zuerst. Dazu kommt die Schicht **S7 Rückkopplung**: Jede Handlung wird im Betrieb weiter gemessen. Lässt eine Quelle nach, kommt eine **Fassung n+1** mit Ursachenbegründung, nie eine stille Nachjustierung.

**Spot-Strang** (Nutzer: *„beides“*): Der Kauf am festen Sparplan-Tag bleibt, weil REGEL0 als Kaufzeitpunkt nicht trug (E-132, Wartedrift). Die Leiter betrifft im Spot die **zusätzlichen** Handlungen (Alt-Spot nach Dominanz-Spitze, gestaffelt; Teilmitnahme L; Abbau B4). Der Sparplan selbst ist **Planung** (§8).

---

## 3. Was dauerhaft erfolgreiche Trader anders machen

**Belege von außen** (nicht im Projekt nachgemessen):

| Befund | Quelle |
|---|---|
| 97 % aller Personen, die mehr als 300 Tage im brasilianischen Terminmarkt daytradeten, verloren Geld | Chague, De-Losso, Giovannetti (2019), *Day Trading for a Living?*, SSRN 3423101 |
| Taiwan 1992–2006: Die Mehrheit verliert, aber eine **kleine Spitzengruppe** gewinnt auch im Folgejahr. Können gibt es also, nur selten | Barber, Lee, Liu, Odean (2014), *Journal of Financial Markets* 18 |
| Eine einfache Trendregel auf **67 Märkten** über ein Jahrhundert, positiv in den meisten großen Krisen; ihr Vorteil kommt aus der **Breite** | Hurst, Ooi, Pedersen (2017), *Journal of Portfolio Management* |
| Nach der Veröffentlichung deutlich schwächer (TSMOM Sharpe 1,41 → 0,41); belegt für Privatanleger sind Prämien, die man hält, und **Bremsen** | E-129 (Recherche R-A, 22.10.) |

**Was „Handlung nach den Gegebenheiten“ bei den Erfolgreichen heißt** – fast nie *„ich weiß, wohin es geht“*:

| # | Verhalten | Übersetzung ins System |
|---|---|---|
| T1 | **Größe und Instrument passen zum Risiko des Moments** | Schicht Ausführung: Hebelstufe aus der Liquidationsgefahr (K6, 2.681), Größe aus der Schwankung |
| T2 | **Asymmetrie:** Verlust begrenzt, Gewinn offen; Trefferquote oft unter 50 % | Stop/Ausstieg je Handlung festgelegt, Teilmitnahme (L) |
| T3 | **Nicht-Handeln ist eine Handlung** – in ungünstiger Lage kleiner oder gar nicht | „beobachten“ und „kleiner“ als eigene Stufen der Leiter (§5) |
| T4 | **Staffeln statt Alles-auf-einmal**, wenn der Zeitpunkt unsicher ist | Handlung „gestaffelt“ (2–3 Teile, an Auslöser gebunden, nie an den Takt) |
| T5 | **Viele kleine, wenig verbundene Wetten** | Grenze je Gruppe (BTC-Bindung), Mischung als Planung (§8) |
| T6 | **Prozess und Tagebuch:** Was habe ich warum getan, was kam heraus? | Schicht Rückkopplung: Messstand im Betrieb (O21), Tagebuch der eigenen Entscheidungen |

---

## 4. Das Schichtenmodell — wo die vorhandenen Signale liegen

**Bisher (Trichter):** Ein Signal läuft durch Filter um Filter, am Ende steht ja/nein und eine feste Handlung. Jeder Filter ist ein Blocker. Schwache Filter verketten ihr Rauschen, und am Ende passt die Handlung nicht zur Lage.

**Neu:** Ein Auslöser **eröffnet einen Prüffall**. Die Schichten sperren nicht, sie **verschieben die Handlung auf einer Leiter** (§5). Heraus kommt **eine** Handlung mit Begründung und Gegenargumenten je Schicht.

| # | Schicht | Frage | Vorhandene Bausteine | Rolle | Messstand |
|---|---|---|---|---|---|
| **S1** | **Umfeld** (Finanzsystem, Wirtschaft) | Rückenwind oder Gegenwind von außen? | Lagebild L1–L6 (Zinsen, Netto-Liquidität, Dollar, HY-Spread, Rezessionsampel), Termine | **Gewicht** auf Größe und Haltedauer, **nie Auslöser** | als Richtung nicht entscheidbar (E-133, E-135) |
| **S2** | **Kryptomarkt** | Wie unruhig, wie breit, wie gestimmt? | BTC-Trend, Breite, **L7 DVOL**, Funding, Dominanz, Season-Ampel | Gewicht; DVOL/ATR als **Risiko** | DVOL/F&G als Richtung nicht messbar (E-160); Risiko ✔ |
| **S3** | **Klasse und Gruppe** | Welche Instrumente sind zulässig, wie stark hängt es an BTC? | Kern BTC/ETH/SOL (immer zugelassen), Large/Alt, BTC-Bindung, Sektor | Zulassung und **Grenze je Gruppe** | Kern-Regel ✔ (K-4) |
| **S4** | **Asset** | Wie steht das Asset im Fortbestand, was belastet es? | B4-Fünftel, Verwässerung/Freigaben (P22c), Upbit-Listing, eigener Bestand | Gewicht; über **Monate** belegt | B4 12 M ✔ |
| **S5** | **Auslöser** | Wann wird geprüft? | REGEL0, Spot-Mitnahme B1, Upbit B3, B4-Stichtag, Liquidationsabstand H15 | **eröffnet den Prüffall** (Ereignis, nie Takt: Regel 1) | REGEL0 nicht robust (E-139); Extreme ordenbar (2.648) |
| **S6** | **Ausführung** | Wie viel, welche Hebelstufe, Stop, Haltedauer, gestaffelt? | K6 Hebelstufe aus Risiko, ATR-Stop, 24-h-Regel, H15 | **bestimmt das Wie** | ✔ ATR → Liquidationsgefahr (2.681) |
| **S7** | **Rückkopplung** | Was kam heraus – je Handlung, je Gegebenheit? | O21 Messstand im Betrieb, Hebel-Ergebnis zum Schlusskurs; **neu:** Tagebuch | Lernen **im Betrieb**, nie still nachjustieren | O21 läuft |

⚠️ **Fakt oder Bewertung (Prüffrage des Projekts):** Eine Schicht darf die Handlung nur dann **verschieben**, wenn ihre Wirkung auf das Ergebnis der Handlung **gemessen** ist (Bewertung). Ist sie nicht gemessen, steht sie als **Fakt** neben der Handlung, sichtbar, aber ohne Einfluss. Die Kennzeichnung je Zeile ist Pflicht (§7).

---

## 5. Handlungskatalog und Handlungsleiter

### 5.1 Der Katalog (Ausgangspunkt, Long-Seite wie bisher)

| Stufe | Handlung | Instrument |
|---|---|---|
| **H0** | beobachten (Fakt in die Mail nur, wenn eine Handlung folgt) | – |
| **H1** | Spot klein | Spot |
| **H2** | Spot gestaffelt (2–3 Teile, je Teil eigener Auslöser) | Spot |
| **H3** | Hebel niedrig (Stufe mit kleiner Liquidationsgefahr) | Hebel |
| **H4** | Hebel nach K6 (höchste Stufe unter der Nutzergrenze) | Hebel |

**Bestand:** halten · Teilmitnahme (L) · abbauen (B4) · in EURCV parken · Hebel schließen (H15).

**Eine Handlung ist der ganze Trade** (Nutzerfrage 27.10.): Der Auslöser (z. B. das REGEL0-Signal) gibt den **Einstiegszeitpunkt** vor. Die Leiter entscheidet **Instrument, Stufe, Größe und Haltedauer bzw. Ausstieg**. Das ist keine neue Einstiegssuche.

**Haltedauer als Achse der Leiter, 0–5 Tage und länger** (Nutzer 27.10.: *„für Hebel ca. 0–5 Tage oder sogar länger vorgesehen“*):
- **E-6** (27.09.) hat **24 h als Messfenster** gesetzt, weil sich gute und schlechte Einstiege bei 12–24 h am besten trennten (2.642). Ausdrücklich: *„H24 ist das Messfenster, nicht die Haltedauer“*.
- Zur **Betriebsregel** wurden die 24 h erst durch Schritt7 §23.68 (18.10.): Auf den REGEL0-Einstiegen 2025–26 kostete längeres Halten **netto** −0,32 bis −0,42 % je weiterem Tag. Das war
  - **netto**, mit 0,18 % je Tag Finanzierung, also Kosten, die nach Regel 2 nachgelagert gehören (⚠ **berichtigt in §5.3:** 2025–26 war längeres Halten **auch brutto** schlechter);
  - im Vorab-Urteil je Jahr *nicht unterscheidbar*;
  - **2024 umgekehrt** (H168 brutto +3,4 bis +4,3 % gegen H24 +0,95 bis +1,35 %);
  - gemessen auf Einstiegen, die heute als nicht robust gelten (E-139).
- ⇒ Die 0–5 Tage sind **nicht widerlegt**, ihr Vorzeichen **hängt am Regime**. Genau das ist eine Gegebenheit für die Leiter.
- Im gepaarten Vergleich (§6) wird je Einstieg **24 h / 48 h / 72 h / 5 T / länger** brutto gegeneinander gemessen, Finanzierung nachgelagert. Die Schichten S1/S2 sollen dabei entscheiden, wann länger gehalten wird.

### 5.2 Die Leiter: wie Schichten verschieben (**HYPOTHESEN**, nicht gemessen)

| Gegebenheit | Verschiebung | fachliche Begründung |
|---|---|---|
| S2/S6: Schwankung hoch (ATR, DVOL im oberen Teil des rollenden Jahres) | eine Stufe tiefer (H4 → H3 → H1) | gleiche Richtungsunsicherheit, mehr Liquidationsgefahr (2.681) |
| S1: Umfeld rot (Rezessionsampel, HY) | Größe kleiner, Haltedauer nicht länger | übergeordnete Kräfte **gewichten** (Nutzer 01.10.) |
| S3: Kern | Spot-Handlungen (H1/H2) zusätzlich zulässig | Kern immer zugelassen |
| S4: unteres B4-Fünftel | kein Spot-Aufbau; nur kurze Handlungen | Fortbestand schwach über Monate |
| S5: Auslöser an einem Extrem (Lift) | Handlung nach oben möglich, **Haltedauer kurz** | Extreme ordenbar (2.648); große Bewegungen kehren binnen 24 h um (Schritt7 §23.68, Vorwissen aus der Wucht-Messung zu 2.694) |
| S1/S2: Rückenwind (BTC über seinem 200-T-Schnitt, Breite gut, Umfeld nicht rot) | **Haltedauer länger**, beendet durch die Führung (nachgezogener Abstand, H15), höchstens ≈ 14 T | V2; 2024 umgekehrt zu 2025–26 (§23.68) |
| S1/S2: Gegenwind | Haltedauer 24 h | §23.68 (2025–26) |
| S5: Dominanz-Spitze (BTCDOM ≥ +8,7 % in 30 T) | Alt-Spot **gestaffelt**, 3–9 Wochen | Spot §32.1 (Lift 1,65 gegen die Basisrate, 56 % Fehlalarm) |
| mehrere Gegenwinde zugleich | H0 (beobachten) | T3 |

**Festgelegt mit dem Nutzer 27.10.:**
- **Beide Stränge**, mit der REGEL0 als ein Auslöser unter mehreren (§2a).
- **Nur Long**; Short bleibt wie heute eine nachträgliche Option.
- **Haltedauer** 24 h bis 5 T, dazu *länger, bis die Führung schließt*, höchstens etwa 14 T.
- **Leiterzeilen:** Der Nutzer korrigiert diesen Entwurf, danach folgt der Messplan vorab.

### 5.3 Herkunftsprüfung der Leiter und Festlegung 28.10.

**Nutzerfrage 28.10.:** *„woher hast du die Quellen bzw. Recherche?“* Die Leiter beruhte **nicht auf einer Recherche je Zeile**. Sie mischt drei Herkunftsarten: eigene Befunde, Fachliteratur (meist Aktien- und Terminmärkte, nicht Krypto) und **eigene Setzungen** (alle Schwellen wie „oberer Teil des Jahres“, „≈ 14 T“, „mehrere“). Je Zeile nachgeprüft:

| # | Zeile | Herkunft | Einschätzung | Daten NB | **Festlegung 28.10.** |
|---|---|---|---|---|---|
| L1 | Schwankung hoch → eine Stufe tiefer | eigener Befund **2.681** (ATR sagt Liquidationsgefahr voraus, 5x vorwärts kalibriert); Moreira/Muir (2017, *J. Finance* 72(4)): Risiko in unruhigen Phasen senken | stärkste Zeile; der Risikovorteil ist fast mechanisch, ein Vorteil **je Risiko** ist auch in der Literatur umstritten (Kritik: außerhalb der Stichprobe schwächer) | ATR ✔; DVOL nur BTC/ETH und in 2.681 **nicht** geprüft | **messen, nur mit ATR** |
| L2 | Umfeld rot → kleiner | Nutzervorgabe „gewichten“; **kein Beleg**; Liu/Tsyvinski (2021, *RFS* 34(6)): Krypto hängt kaum an Makrofaktoren | schwach; als Richtung nicht entscheidbar (E-133, E-135) | ✔ | **nur Fakt** in der Mail |
| L3 | Kern → Spot zusätzlich | Projektregel; 2.690: 72 h Spot besser als jeder Hebel | Zulassung, keine Hypothese | ✔ | **Regel** |
| L4 | unteres B4-Fünftel → kein Spot-Aufbau | eigener Befund (B4 12 M ✔) | stimmig, nur Spot und Monatshorizont | ✔ | **Regel**, Hebel unberührt (Regel 3) |
| L5 | Extrem → ~~Handlung nach oben~~, kurz halten | 2.648, 2.694 | ⚠️ **Fehler im Entwurf:** 2.648 sagt ein **Ereignis** voraus, ausdrücklich keine Handelsregel; die Umkehr binnen 24 h (2.694) spricht eher **gegen** eine höhere Stufe | ✔ | **„nach oben“ gestrichen**, „kurz halten“ messen |
| L6 | Rückenwind → länger halten, Führung beendet | Faber (2007, *J. Wealth Mgmt.*): 10-Monats-Schnitt als Trendfilter, über Anlageklassen; Liu/Tsyvinski: Krypto-Bewegungen setzen sich über **Wochen** fort, laut Folgestudie **nur in steigenden Märkten** | ⚠️ **Gegenbefund fehlte im Entwurf: 2.702**: 72 h mit nachgezogenem Stop 1,5 ATR 2025–26 in **0 von 4** Mengen besser (ohne Bedingung Rückenwind; offen, ob Haltedauer oder Stop schuld war). „14 T“ ist eine eigene Setzung | ✔ | **messen**, Haltedauer und Stop **getrennt** |
| L7 | Gegenwind → 24 h | §23.68 | ohne Bedingung „Gegenwind“ gemessen | ✔ | **messen**, als Gegenstück zu L6 |
| L8 | Dominanz-Spitze → Alt-Spot 3–9 W | eigener Befund (Spot §32/§33, Lift 1,65) | schwach; Schwelle 8,7 % aus der Rückschau; 16 Signale seit 2023 | ⚠️ **BTCDOM fehlt am NB** (frei nachladbar) | **in den Spot-Strang**, nicht in H-1 |
| L9 | mehrere Gegenwinde → beobachten | T3; „mehrere“ eigene Setzung | nur so gut wie L6/L7 | ✔ | ergibt sich aus L6/L7 |

**Nutzerantwort 28.10.:** *„streichen von nach oben etc. – unsicher bei allen Punkten“*, also die Festlegungen der letzten Spalte; das Urteil je Zeile **gibt die Messung**.

**Abhängigkeiten zwischen den Zeilen** (fehlten im Entwurf):
- **Vorrang:** L1 (Risiko) gilt immer. Widersprechen sich Zeilen bei der Haltedauer (z. B. Extrem und Rückenwind), gilt die **kürzere**.
- **Überschneidung:** Hohe Schwankung und Gegenwind treten oft gemeinsam auf. L1 und L7 werden getrennt ausgewiesen, sonst wird ein Effekt doppelt gezählt.
- **Gleichzeitige Positionen:** Altcoins hängen stark an BTC; fünf Hebelpositionen bei Rückenwind sind fast **eine** Wette → Grenze je Gruppe (T5).
- **Geprüft und nicht ergänzt:** Funding, OI und Volumen bringen zur Liquidationsgefahr nichts über die ATR hinaus (2.681); Funding als Richtung an der Nachweisgrenze.

**Berichtigung zu §5.1 (§23.68):** Längeres Halten war 2025–26 **auch brutto** schlechter, nicht nur netto: H24 brutto +0,30…+0,31 %, H168 brutto −0,51…−0,93 % (unverzerrte Mengen, `p62_ausstieg_vorpruefung.txt`). Die Finanzierung allein erklärt den Unterschied also nicht. 2024 war es umgekehrt.

**Vorprüfung 28.10. (Stufe 1, nur Zählung, kein Ergebnis angesehen):** Marktweiter Rückenwind als *BTC über seinem 200-T-Schnitt (Stand Vortag)*, `messdaten.db`:

| | Tage | Rückenwind | Wechsel |
|---|---|---|---|
| 2023 (ab 09) | 122 | 62 % | 1 |
| 2024 | 366 | 80 % | 10 |
| 2025 | 365 | 73 % | 17 (fast alle im März/Oktober, Flattern um die Linie) |
| 2026 (bis 08) | 243 | 5 % | 1 |

⇒ 2025–26 besteht im Kern aus **vier Phasen**: Rückenwind bis 09.03.25, Gegenwind bis 22.04.25, Rückenwind bis 03.11.25, Gegenwind bis 19.08.26. Mit Blöcken von max(15 T, 3 × 168 h) = 21 T sind das je Zustand nur **≈ 13–15 Blöcke** (unter 20: **kein Befund**). Über 2023-09 bis 2026-08 wären es ≈ 30 bzw. ≈ 21 Blöcke, aber die **unabhängigen** Fälle sind die **Phasen** (≈ 6–8), nicht die Blöcke. Der Zustand fällt mit der Epoche zusammen: Gemessen würde „2024 und Mitte 2025 gegen Ende 2025 bis 2026“, nicht der Rückenwind. Das ist dieselbe Lage wie bei ETF/DVOL/F&G (zu wenige Wechsel). ⇒ **L6 marktweit ist mit dieser Datenlänge nicht auflösbar.** Auflösbar wäre ein Rückenwind **je Trade** (eigener Trend des Assets), der am selben Tag zwischen Assets wechselt; dann fällt der Markt in der Differenz heraus (§6.1). Siehe §6.5.

⚠️ **Die Leiter ist eine Liste von Gewichten, keine Kette von Sperren** (Nutzer 28.09.: *„kein künstlicher Blocker“*). Welche Zeilen bleiben und wie stark sie verschieben, **entscheidet die Messung** (§6). Die Zeilen werden **vorab fachlich** festgelegt und nicht aus den Daten gesucht – sonst wäre es wieder Mehrfachtesten (2.645).

---

## 6. Zuerst Simulation und Messung — das Messdesign

### 6.1 Der methodische Hebel: der gepaarte Handlungsvergleich

> **Derselbe Auslöser, derselbe Zeitpunkt, alle Handlungen simuliert.**

Der Markt (Regime, Drift – zwölfmal größer als die Lage, 2.598) wirkt auf **alle** Handlungen eines Prüffalls gleichzeitig. In der **Differenz** zwischen den Handlungen fällt er großteils heraus. Messbar wird damit:

| messbar | nicht messbar (bleibt Fakt) |
|---|---|
| **Welche Handlung ist bei DIESER Gegebenheit besser?** (Wie) | Ob der Markt in den nächsten Wochen steigt (Ob, 2.599) |

Das ist der Unterschied zu allen bisherigen Messungen, die fast alle das *Ob* oder das *Wann* gefragt haben.

### 6.2 Die Arme

| Arm | Inhalt | Zweck |
|---|---|---|
| **A** | heute: feste Handlung (REGEL0: Hebel nach Stufe, fester Positionswert, 24 h) | Bezug; Stufe 0 reproduziert den REGEL0-Messstand (R-R11) |
| **B** | Leiter nach §5 (vorab festgelegt) | die Frage |
| **C** | **Zufallsleiter:** gleiche Anteile je Handlungsstufe, Zuordnung zufällig je **Tagesblock** | Nullwelt (geballte Signale: Tagesblock statt Stunde) |
| **D** | Orakel (Zuordnung mit Zukunftswissen) | Positivkontrolle: Kann der Aufbau einen Unterschied überhaupt sehen? (Lehre E-133) |

### 6.3 Zielgrößen und Regeln

- **Brutto zuerst**, Gebühren nachgelagert (Regel 2). Die Staffelung kostet mehr Gebühren, das wird **danach** geprüft.
- Hauptgrößen:
  - **Ergebnis je Einheit Risiko**;
  - **linkes Ende** (schlechteste 5 % der Tage);
  - **Liquidationen**;
  - **größter Rückgang**.
- Der Mittelwert ist Nebenbedingung: *kein Ertragsverlust*.
- **Messregelwerk:**
  - Messplan vorab committet;
  - Selbsttest **vor dem ersten Blick** (Fehlalarm, Auflösung durch Pflanzung, Ballung);
  - Block max(15 T, 3 × H), unter 20 Blöcken **kein Befund**;
  - Tagesklammer; je Epoche ausweisen;
  - zweiter Weg und Geltungsbereich (Prüfbericht E-141);
  - zweiseitig, wenn keine fachliche Richtung vorab steht.
- **Daten:** vorhanden (Stundenkurse und Markpreise aller Assets ab 2023, Lauf A ab 2019, Lagebild-Reihen, DVOL ab 2021-03). **Kein Download nötig** für die erste Stufe.

### 6.4 Ehrliche Erwartung

- **Vorläufer V-1** (nur eine Dimension, die Größe): Die Richtung war überall eine Bremse ohne Ertragsverlust, aber nach Plan nicht trennbar (E-158). Die Leiter verbindet mehrere Dimensionen (Instrument, Hebelstufe, Größe, Staffelung). Das kann stärker sein, muss es aber nicht.
- **Trägt B gegen C:** Die Leiter ist eine **Bewertung** und darf die Handlung verschieben.
- **Trägt B nicht:** Die Leiter bleibt als **Fakt-Ordnung** sichtbar (Risikodisziplin), ohne Anspruch auf Vorteil. Auch dann wäre die Mail klarer als heute.
- Das **Ob** beantwortet auch diese Messung nicht.

### 6.5 Erste Messung H-1 — Umfang (ENTWURF zur Abstimmung, 28.10.)

Drei Fragen, alle **je Trade** veränderlich, damit genug unabhängige Fälle entstehen:

| # | Frage | Gegebenheit je Einstieg (Stand vor dem Einstieg) | verglichen |
|---|---|---|---|
| **H-1a** (L1) | Hilft die Stufe nach Schwankung **je Risiko**? | ATR des Assets im rollenden Jahr (Drittel) | 5x / 3x / Spot, Liquidationen am Markpreis |
| **H-1b** (L6/L7) | Soll die Haltedauer am **Trend dieses Trades** hängen? | **offen, siehe unten** | 24 h / 72 h / 5 T, Stop getrennt (offene Frage aus 2.702) |
| **H-1c** (L5) | Lohnt bei einem Extrem eine **kurze** Haltedauer? | `momentum_kurz`/`rsi` am Extrem (2.648) | 6 h / 24 h / 72 h |

- **Einstiege:** REGEL0-Referenz, vier Mengen (wie p62, R-R11: H24 brutto muss p62 reproduzieren). Weitere Auslöser (V3) erst in H-2.
- **Arme** nach §6.2: A fest, B Leiter, C Zufallsleiter je Tagesblock, D Orakel.
- **Brutto**, Kosten nachgelagert; Zeitraum: Urteil 2025–26, 2024 und 2023-09 ff. als zweite Epoche ausgewiesen.
- **Marktweiter Rückenwind** (BTC über 200 T) nur als **Auskunft**: zu wenige Wechsel (§5.3).

**Offene Richtungsfrage für H-1b: Was heißt „Rückenwind je Trade“?**
- **a** eigener Trend des Assets: Kurs über seinem **50-T-Schnitt** (Stand Vortag). Wechselt häufig und zwischen Assets.
- **b** eigener Trend über den **200-T-Schnitt** (wie Faber, nur je Asset). Langsamer, weniger Wechsel.
- **c** Stärke gegen BTC über 30 T (relativer Trend).

Empfehlung **a**: Die Literatur findet die Fortsetzung in Krypto über **Wochen** (Liu/Tsyvinski), nicht über Monate; zugleich wechselt der Zustand oft genug für ein Urteil. **b** als zweiter Weg (Prüfbericht E-141). Weil die Zeilen vorab fachlich stehen müssen (2.645), wird **eine** Fassung als Hauptfrage festgelegt, die andere nur als zweiter Weg.

**Vor dem ersten Blick:** Vorprüfung der Fallzahlen je Zustand (Blöcke ≥ 20 je Epoche?), Selbsttest mit Ballung (Fehlalarm, Pflanzung, Positivkontrolle D).

**Festgelegt 28.10. (Nutzer: *„ja a … aber B und C finde ich nicht falsch“*):** **a** ist die Hauptfrage, **b** der zweite Weg (Bedingung für TRÄGT), **c** Auskunft. ⚠ **Berichtigung H-1a:** Die Hebel**stufe** hängt im Betrieb schon an der ATR (K6: höchste Stufe mit P(Liquidation 24 h) ≤ 2 %, `agent/regel0_rechnung.py` `hebelstufe`). H-1a misst deshalb die **Größe** nach Schwankung. **Vollständiger Messplan:** `Basisinfos/Messplan_H1_Lagegerechte_Handlung_28_10.md`.

**Abgleich mit dem Gesamtplan (28.10., Nutzerfrage; Messplan Fassung 2):**
- **H-1a gestrichen:** Sie ist **V-1** (E-157/E-158): Positionswert nach 1/ATR gegen fest, Ergebnis Bremse ohne Ertragsverlust, **nicht trennbar**. L1 ist damit beantwortet, die Stufe folgt der ATR (K6), die Größe bleibt fest.
- **Marktweiter Rückenwind** ist **L2-a** (E-151/E-153), nicht entscheidbar; nur Auskunft.
- **Neu und gemessen werden:** H-1b (Haltedauer nach dem Trend **dieses** Assets, Tagesklammer; kein Einstiegsfilter, daher kein Widerspruch zu E-153) und H-1c (kurz bei Extrem).
- **Einordnung in den Gesamtplan:** Nachträge 79/80 (E-155/E-156) hatten die **Einstiegssuche abgeschlossen** und vorgeschlagen, das **Fakten- und Führungssystem** weiterzuentwickeln. Das Konzept folgt dem: Es sucht keinen Einstieg, sondern die passende **Handlung** nach dem Einstieg.

---

## 7. Das Dashboard (Idee 2) — dieselben Schichten als Ansicht

| Ebene | Inhalt | Kennzeichnung |
|---|---|---|
| **S1–S2** Umfeld und Markt | Lagebild L1–L7, Phase, Breite, Funding, Dominanz | je Zeile **Fakt** / **gemessen** / **ungeprüft** |
| **S3** Abhängigkeiten | BTC-Bindung je Asset (rollend), Gruppen, die gemeinsam laufen, Klumpen im Bestand | Fakt |
| **S4** Asset | B4-Fünftel, Verwässerung/Freigaben, Listing, Funding/OI, Chart Woche/Tag | gemischt, je Zeile |
| **Bestand** | Wert, Liquidationsabstand, Haltedauer, Führung | Fakt |
| **Prüffall** | offene Auslöser mit Handlung nach Leiter, je Schicht *dafür/dagegen* | Bewertung nur, wenn §6 trägt |
| **LLM-Einordnung** | fasst den Prüffall zusammen, nennt **Widersprüche und Gegenargumente**, **Quelle je Satz** | Erklärung, **keine Prognose** |

**Leitplanken für das LLM** (aus den eigenen Lehren):
- **Erklärer, nicht Entscheider** (E-125).
- **Eine eigene, klare Frage** je Prüffall, z. B. *„Welche Fakten sprechen gegen diese Handlung?“*, statt *„stützt der Markt das?“*. Sonst entsteht Echo bzw. Mitte (E-82).
- Es kennt die Wette der Handlung.
- **Nur Fakten aus unseren Daten**, jede Aussage mit Quelle.
- Beim Rückspiel nur Modelle mit Wissensstand vor dem Prüfzeitraum (Kontamination).

**Ort:** Ausbau der Statusseite am NB (`remote/server.py`). Das erfüllt *„Information nie nur in die GUI“*. Die Mail trägt die Handlung und verweist auf den Prüffall. **Der Fakt-Teil braucht keine Messung**, weil er keinen Vorteil behauptet, und kann parallel zu §6 entstehen.

➤ **28.10. abends:** Bestandsaufnahme und Expertenkonzept für Fakten und LLM-Bewertung in `Voranalyse_Dashboard_LLM_28_10.md` (Aufgaben A1–A6, Prüfung je Aufgabe, Abstimmung §8).

---

## 8. Mischung von Strategien und Anlageklassen — Planung, keine Systemfunktion

**Nutzervorgabe:** planen ja, Systemfunktion nein. Das System **unterstützt** die Planung, es **ersetzt** sie nicht.

| Baustein | Rolle in der Mischung | Synergie |
|---|---|---|
| Kern halten + Sparplan (läuft) | Grundertrag | Basis für alles |
| Spot-Führung (L, B4, Upbit) | Ausstiegsdisziplin | begrenzt Altcoin-Verluste (2024+ Altindex −87 % gegen BTC) |
| Hebel nach Leiter (§5/§6) | kurze, risikogeführte Wetten | wenig mit dem Haltebestand verbunden, **wenn** klein und kurz |
| Rebalancing-Band zwischen Kern und EURCV/Gold | erntet Schwankung **ohne Vorhersage** | ruhigeres Gesamtvermögen |
| Prämien, die man hält (Staking-Lücke W2) | Zusatzertrag | unabhängig von Signalen (E-129) |

**Was das System dafür liefert** (Dashboard, Mail nur bei Handlung):
- **Ist gegen Plan:** Anteile je Klasse.
- **Klumpen:** wie viel des Bestands hängt an BTC?
- **Abweichung über ein Band:** Das ist eine Handlung (umschichten) und damit mailwürdig.

Das Band ist ein **Zustand**, kein Takt (Regel 1).

---

## 9. Gegenprüfung

### 9.1 Gegen die vier Regeln

| Regel | Prüfung | Ergebnis |
|---|---|---|
| 1 Takt nie Signalgeber | Auslöser sind Ereignisse (REGEL0, Mitnahme, Listing, Band); die Staffelung hängt an Auslösern | ✔ |
| 2 Gebühren nicht in die Bewertung | brutto zuerst, Kosten nachgelagert (§6.3) | ✔ |
| 3 kein Asset-Vorurteil, beim Hebel kein Asset-Rang | Die Hebelstufe kommt aus dem Risiko **dieses Trades** (K6). B4 verschiebt nur **Spot-Aufbau** und steht in der Mail als Information | ✔ – ⚠ die Leiterzeile „unteres B4-Fünftel“ darf den **Hebel** nicht verschieben, sonst wäre es Rang-Hebel |
| 4 Fakt keine Begründung | Nur gemessene Schichten verschieben, Fakten stehen daneben (§4) | ✔ |

### 9.2 Gegen frühere Befunde — wiederholt das Konzept eine Messung?

| Früher | Unterschied hier |
|---|---|
| K1 Kombination 2.677/2.678, A-Faktoren 2.645 | gefragt war **q / Richtung** (Ob/Wann). Hier ist die Frage die **Handlungswahl im gepaarten Vergleich** (Wie). Die Leiter wird vorab fachlich festgelegt, nicht gesucht |
| L2-a E-151/E-153 | marktweites Regime (BTC 200 T) für längeres Halten: nicht entscheidbar → L6 marktweit nur Auskunft; H-1b misst je Asset |
| F-1 Marktfilter E-133 | Filter = *ob handeln*. Hier verschiebt das Umfeld nur das *Wie*, H0 entsteht nur aus mehreren Gegenwinden. ⚠ Der H0-Anteil ist der Teil, der dem Marktfilter am nächsten kommt; er wird **getrennt** ausgewiesen |
| V-1 E-158 | ⚠ **dieselbe Messung wie L1/H-1a** (Größe nach 1/ATR), nicht nur ein Vorläufer: H-1a gestrichen (Messplan Fassung 2, 28.10.) |
| Trichter der alten Kette (stillgelegt E-164) | Schichten sind Gewichte, keine Sperren (§5.2) |
| Entscheider E-82, LLM E-125 | Das LLM erklärt, es urteilt nicht. Es bekommt eine eigene Frage |

### 9.3 Risiken

| Risiko | Gegenmittel |
|---|---|
| **Überanpassung** über viele Leiterzeilen | wenige Zeilen, vorab fachlich, ein Messplan, Nullwelt C, Selbsttest |
| **Kosten** durch Staffelung und Stufenwechsel | nachgelagerte Kostenprüfung je Handlung (Bitpanda-Kosten bekannt) |
| **Komplexität im Betrieb** | Bau erst nach einer tragenden Messung (§10); bis dahin Fakt-Dashboard |
| **Datenlänge** (REGEL0 ab 2023-09 reif, Lauf A ab 2019) | Epochen getrennt ausweisen; Lauf A als zweiter Weg |

### 9.4 Quellenprüfung

`Basisinfos/Rechenkern_02_10/p100_konzept_quellen.py` prüft maschinell, dass jede hier genannte Befund- und Entscheidungsnummer im Register bzw. in den Entscheidungen existiert (Ergebnis in E-165). Die Außenquellen in §3 sind per Websuche gegengelesen (27.10.). Die Taiwan-Studie belegt die **Beständigkeit** einer kleinen Spitzengruppe; eine genaue Quote wird hier bewusst **nicht** genannt, weil sie in der Gegenlesung nicht eindeutig bestätigt war.

**Berichtigung einer eigenen Aussage vom 27.10. im Chat:** *„Führung halbiert in der Messung den Verlust“* war zu stark. Die Nachlauf-/Notbremse-Führung ist **knapp nicht bestätigt** (Spot §21.6). Belegt ist die Teilmitnahme L (§31.6).

---

## 10. Projektform

| Schritt | Wo | Betrieb |
|---|---|---|
| 1. Leiter fachlich festlegen (mit dem Nutzer) | Konzept | unverändert |
| 2. Messung §6 (Messwerkzeug, Wegwerfpfade, keine Produktion) | bestehendes Projekt, `Rechenkern` | unverändert |
| 3. Fakt-Dashboard | Statusseite NB, parallel | nur Anzeige |
| 4. **Bauentscheid** Umbau oder neues Projekt | **erst nach 2.** | – |

**Tendenz für 4:** Ein eigenes Modul bzw. Projekt „Handlung“ mit sauberer Schichtung, das die vorhandenen Datenquellen nutzt. Die alte Kette ist ohnehin stillgelegt (E-164).

---

## 11. Zur Abstimmung

| # | Frage | Alternativen | Empfehlung |
|---|---|---|---|
| **F1** | Schichtenmodell und Handlungsleiter als Grundlage? | a ja · b nur Dashboard, keine Leiter · c anderer Zuschnitt | **a** |
| **F2** | Wie zur ersten Messung? | a Leiter §5.2 so messen · b nur Spot-Handlungen (H0–H2) zuerst · **c zuerst die Leiterzeilen gemeinsam fachlich festlegen (Trader-Sicht), dann Messplan H-1 vorab** | **c**, weil die Leiter vor der Messung stehen muss und deine fachliche Sicht dort hineingehört |
| **F3** | Dashboard? | a Fakt-Teil parallel auf der Statusseite, LLM-Teil später · b eigenes Projekt · c erst nach F2 | **a** |
