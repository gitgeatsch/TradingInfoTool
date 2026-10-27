# Konzept „Lagegerechte Handlung“ — die Signale in Schichten, die Handlung nach den Gegebenheiten (27.10.2026)

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
  - **netto**, mit 0,18 % je Tag Finanzierung, also Kosten, die nach Regel 2 nachgelagert gehören;
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
| S5: Auslöser an einem Extrem (Lift) | Handlung nach oben möglich | Extreme ordenbar (2.648) |
| mehrere Gegenwinde zugleich | H0 (beobachten) | T3 |

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
| F-1 Marktfilter E-133 | Filter = *ob handeln*. Hier verschiebt das Umfeld nur das *Wie*, H0 entsteht nur aus mehreren Gegenwinden. ⚠ Der H0-Anteil ist der Teil, der dem Marktfilter am nächsten kommt; er wird **getrennt** ausgewiesen |
| V-1 E-158 | Vorläufer mit einer Dimension; Ergebnis ehrlich als Erwartung genannt (§6.4) |
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
