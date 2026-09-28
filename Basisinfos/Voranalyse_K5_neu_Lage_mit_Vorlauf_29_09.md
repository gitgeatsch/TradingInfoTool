# Voranalyse K5 neu — Lage mit Vorlauf und rsi jetzt (29.09.2026)

**Nutzer:**
- *„ja, Voranalyse schreiben — prüfen und gegenprüfen"*
- *„zeitversetzt zum Prüfzeitpunkt schauen wir in die Vergangenheit & RSI (und dies mit den richtigen Beiträgen) — das könnte klappen"*
- *„wir bekommen auf einer Seite Rauschen weg, aber der Zeitfaktor ist ein weit größeres Problem als normales Rauschen"*

> **Urteil in einer Zeile:** Die Frage ist **neu und messbar**: Der Vorlauf der
> Terminmarkt-Beiträge wurde nie gemessen, nur die Karenz. Technisch ist sie
> **einfacher** als 2c. Die größte Gefahr ist aber nicht das Rauschen,
> sondern die **Zeit**: Der Effekt schwankt zwischen den Jahren um den Faktor
> 5 und dreht 2022. Deshalb wird die Zeitstabilität hier ein **Kriterium**,
> keine Auskunft.

---

## 1. Ausgangslage

| | |
|---|---|
| **K5** (27.09.) | Schwelle auf kalibriertem q = Normal + Kurven. ⛔ 2.678: Wer so auswählt, wählt das Phase-Normal, und das kehrt zur Mitte zurück |
| **K5 geändert** (28.09., vorläufig) | Schwelle auf dem **Beitrag**. Nutzer: *„wenn das auch nicht klappt, müssen wir wieder abstimmen"* |
| **2.680** (29.09.) | Die Beitragsauswahl ist **robust** (T6 in jedem Drittel des Normals, T4, T5), aber **nicht mehr als rsi allein** (T2) und **nicht kalibriert** (T3). Das Modell dämpft rsi mit ab (Dämpfung 20.000 statt 2.000); einzeln geschätzt und addiert ist besser als gemeinsam |
| **Abstimmung im Gespräch** | L2 *nur rsi, bestätigt* **verworfen**: Wer auf die Bestätigung wartet, wählt späte Zeitpunkte, und die Beiträge mit Vorwissen haben ihre Wirkung dann schon abgegeben (Nutzer). Stattdessen **zwei Rollen, zwei Zeitpunkte** |

### 1a. ⚠️ Karenz ist nicht Vorlauf — was schon gemessen ist

| | Merkmal von | Einstieg | Ereignis zählt ab | gemessen |
|---|---|---|---|---|
| **Karenz** | t | t | t + k | 2.650 (Kursmerkmale: bei k ≥ 3 h **null** von 11), 2.651 (Terminmarkt: Haltequote bei 24 h **0,29–0,74**, unter der Schwelle 0,8) |
| **Altersachse** | t − L | **t** | t | 2.676, **nur Kursmerkmale**: der 24 h alte rsi-Wert trägt in Suche, Prüfzeit und 2022 |
| **Vorlauf der Lage** (hier) | t − 24 … t − 72 h | **t** | t | ⛔ **nie gemessen** für funding, oi_aenderung, konten_verh |

➤ Der Unterschied ist entscheidend. Bei der Karenz bleibt der Einstieg bei t,
und eine Bewegung zwischen t und t + k zählt nicht mit. Beim Vorlauf steigt man
**jetzt** ein, und die Frage lautet: *Sagt eine Lage, die sich vor 1–3 Tagen
aufgebaut hat, die Bewegung ab jetzt voraus?* Das ist das OPTIMUM des Nutzers:
die Lage **vor** der Bewegung.

---

## 2. ⚠️⚠️⚠️ DER ZEITFAKTOR — der Hinweis des Nutzers, an den Daten geprüft

**Nutzer:** *„der Zeitfaktor ist ein weit größeres Problem als normales Rauschen."*
**Er hat recht**, und zwar gemessen, nicht vermutet:

| Beleg | Zahl | Quelle |
|---|---|---|
| Dasselbe Signal je Jahr | 2024 +0,05 · 2025 **+0,02** · 2026 **+0,10**, also Faktor 5 | 2.680 T4 |
| K5-Tabelle, Beitrag ≥ +0,04 | 2024 **−0,12** · 2026 **+0,10**, Vorzeichen gedreht | 2.680 |
| 2022 (unberührt) | oben **−0,012 bis −0,023**, die Auswahl kehrt | 2.680, 2.676 |
| Die Prüfzeit liegt über ihrem Normal | Zufallsränder +0,009 / +0,013 | E-11 |
| Regime gegen Lage | das Regime wiegt **zwölfmal** so viel wie die Lage | 2.598 |
| Marktzustand vorab erkennbar? | **nein**: btc_trend 1,09 gegen eine Zufallsreihe mit 1,04 | 2.599 |

➤ **Einordnung:** Das Signal selbst ist +0,03 bis +0,06. Die Schwankung
zwischen den Jahren ist **gleich groß oder größer**. Rauschen mittelt sich mit
mehr Daten heraus, **die Zeit nicht**: Mehr Anker aus demselben Jahr helfen
nicht, wenn das nächste Jahr anders ist. Dazu kommt beim Vorlauf eine zweite
Zeitfrage: Der **Abstand** zwischen Lage und Bewegung kann selbst schwanken
(einmal 24 h, einmal 60 h).

**Was daraus für diese Messung folgt (Z1–Z6, eingebaut in Abschnitt 4):**

| # | Gegenmittel |
|---|---|
| **Z1** | Zeitstabilität ist ein **Kriterium**: in jedem Jahr 2024/2025/2026 **und** 2022 kein gedrehtes Vorzeichen |
| **Z2** | Die Lage geht als **Zeitfenster** ein (Mittel über 0–24, 24–48, 48–72 h), nicht als Punktwert zu einer Stunde, damit ein schwankender Abstand nicht alles entscheidet |
| **Z3** | Die Fenstergewichte werden **je Jahr** ausgewiesen. Wechselt das tragende Fenster zwischen den Jahren, ist der Vorlauf nicht stabil |
| **Z4** | Die Nachkalibrierung (L3) wird mit **zwei Gedächtnislängen** geprüft (3 und 12 Monate). Eine kurze folgt dem Regime schneller, rauscht aber mehr. Gewählt wird vorab die Regel: *die kürzere, wenn sie in keinem Jahr schlechter kalibriert* |
| **Z5** | Der **Versatz** (E-11) ist Maßstab: Eine Bestätigung in der Prüfzeit muss ihn klar übersteigen |
| **Z6** | ⭐ Die **echte ungesehene Zeit**: Die Regel wird eingefroren und auf den Monaten ab 2026-09 geprüft, sobald sie da sind. Nur neue Zeit beantwortet die Zeitfrage endgültig. Die Prüfzeit 2025/26 ist schon gesehen |

---

## 3. Das Konzept — was zum Prüfzeitpunkt gerechnet wird

Zum Prüfzeitpunkt **t** (der normale Takt), je Asset, **ohne Warten und ohne
mitgeführten Zustand**:

| Rolle | Beitrag | Werte | Quelle |
|---|---|---|---|
| **Auslöser** | rsi (gegen das eigene Asset) | jetzt und 24 h alt (wie 2c) | Kurs |
| **Lage** | funding (Vortag, täglich) | Tag −1, −2, −3 | Terminmarkt |
| **Lage** | oi_aenderung | Mittel 0–24 · 24–48 · 48–72 h | Terminmarkt, stündlich |
| **Lage** | konten_verh | Mittel 0–24 · 24–48 · 48–72 h | Terminmarkt, stündlich |

**Rechnung:**
1. Wie in 2b/2c: Log-Odds, Offset = Phase-Normal, glatte Kurven.
2. **Jede Familie einzeln** geschätzt, mit eigener Dämpfung aus der Kreuzvalidierung. So wird rsi nicht mitgedämpft (2.680).
3. Die Familien werden mit **einem Gewicht je Familie** addiert, geschätzt im Training. Das ist das *„aufeinander kalibrieren"* des Nutzers, mit wenigen Zahlen statt vielen.
4. **Schwelle auf dem Beitrag** (K5), **nachkalibriert** (L3): Die Übersetzung *geschätzter Beitrag → beobachteter Vorsprung* entsteht rollierend aus der Vergangenheit.

➤ **rsi ist ein Summand, keine Pflicht.** Eine starke Lage kann auch bei
mittlerem rsi über die Schwelle kommen. Ob das **in den Daten** passiert, wird
gemessen (T7). Sonst wäre das System in der Wirkung ein rsi-System, also
Fortsetzung einer Bewegung, und das widerspricht OPTIMUM.

---

## 4. Die Vorschläge zur Abstimmung (V1–V10)

| # | Punkt | Vorschlag | Warum |
|---|---|---|---|
| **V1** | **Auslöser** | rsi-Familie (jetzt, 24 h) wie 2c; A4 und Alter **ausgewiesen, nicht gesperrt** | 2.680 T2: rsi allein trägt am besten; kein Blocker (Nutzer 28.09.) |
| **V2** | **Lage** | **drei** Beiträge: funding (Vortag), oi_aenderung, konten_verh | die drei, die bei k = 0 tragen (2.651/2.663); mehr hieße mehr Mehrfachtesten. Käuferanteil und Premium nicht: sie **begleiten** die Bewegung (2.665) |
| **V3** | **Form des Vorlaufs** | **Fenster** statt Punktwert (Z2); die drei Fenster gehen zusammen als eine Familie ein, gewichtet von den Daten, **ohne** Auswahl des besten Fensters | keine Bestes-von-9-Suche über die Abstände; das tragende Fenster wird **ausgewiesen**, nicht gewählt |
| **V4** | **Rechnung** | Familien einzeln, eigene Dämpfung, dann **ein Gewicht je Familie** (Abschnitt 3); Gitter bis 2.000.000, Randwahl ausgewiesen | gegen die Verwässerung aus 2.680 |
| **V5** | **Zielgröße und Bezug** | q5 (K4), Phase-Normal (K2), unverändert; Mengen bestand + unverzerrt:1–3 | abgestimmt |
| **V6** | **Nachkalibrierung** | monotone Übersetzung Beitrag → beobachteter Vorsprung, rollierend aus dem Training; Gedächtnis 3 und 12 Monate (Z4); die K5-Tabelle auf dem **nachkalibrierten** Wert | behebt T3 auf die übliche Weise; Stufen bleiben **feste Werte**, gültig auch für ein einzelnes Asset |
| **V7** | **Zeitfaktor** | Z1–Z6 als Kriterien und Pflichtausgaben | Nutzerhinweis, Abschnitt 2 |
| **V8** | **Prüfstand** | Nullwelt Zeitverschiebung je Asset (die Lage-Fenster **mit** verschoben), 40 Ziehungen; **Regeltest** mit Zufallsbeiträgen; **Tor**: gepflanzt +0,02/+0,04 auf einem Lage-Beitrag, muss bei +0,04 in ≥ 4 von 5 gefunden werden | Pflichtablauf 11–26 |
| **V9** | **Bekanntheitszeitpunkt** | je Beitrag festgelegt: funding erst als **Vortag** (2.663), Terminmarkt-Stunden erst nach Stundenschluss; Prüfung *1 h älter* als Gegenprobe | Vorgriff hat funding schon einmal verdoppelt |
| **V10** | **Machbarkeit am Notebook** | eigener Abschnitt 6, **vor** jeder Umsetzung zu klären; für die Messung wird nichts vom Notebook gebraucht | Nutzerfrage |

---

## 5. Das Kriterium — vorab

| # | Bedingung | bei Nein |
|---|---|---|
| **T0** | Tor (V8) bestanden | kein Urteil |
| **T1** | R-R11: *rsi allein* aus 2c bitgleich reproduziert (bestand +0,0808) | nicht weiter rechnen |
| **T2** | ⭐ **Lage bringt etwas dazu**: Dq(rsi + Lage) − Dq(rsi allein), beide nach dem eigenen Beitragszehntel, jenseits des Nullbands in ≥ 3 von 4 Mengen, fest **und** rollierend | Lage mit Vorlauf trägt nicht; es bleibt **rsi allein**, und das wird mit der OPTIMUM-Frage vorgelegt |
| **T3** | **kalibriert** nach der Nachkalibrierung: Steigung 0,7–1,3 und oberstes Zehntel \|geschätzt − beobachtet\| ≤ 0,02 | K5 wird neu vorgelegt |
| **T4** | ⭐ **Zeit (Z1)**: Dq der Auswahl > 0 in **jedem** Jahr 2024/2025/2026 **und** in 2022, jede BTC-Lage | *trägt nicht zeitstabil*: vorlegen, nicht verwenden |
| **T5** | ≥ 60 % der Assets mit Dq > 0 | Klumpen |
| **T6** | in jedem Drittel des Normals positiv (wie 2c) | Rückkehr zur Mitte |
| **T7** | ⭐ **Auskunft OPTIMUM**: Dq der Auswahl **ohne** rsi (nur Lage) und der Anteil der Signale, bei denen rsi **nicht** im oberen Drittel liegt | – (sie zeigt, ob das System in der Wirkung ein rsi-System ist) |
| **Z3** | Auskunft: welches Fenster je Jahr trägt | – |
| **R** | Zufallsbeiträge im Nullband | nicht verwendbar |

⚠️ **Dritter Blick auf dieselbe Prüfzeit:** Die Lage-Beiträge **mit Vorlauf**
sind neu, rsi allein nicht. Ein *trägt* bleibt deshalb ein **Kandidat** bis
Z6 (neue Monate) und die Simulation (Ebene 3).

---

## 6. Machbarkeit am Notebook (V10) — Ist-Stand

| | |
|---|---|
| **Messung** | alles am Desktop: `terminmarkt_historie.db` stündlich 2021-12 bis 2026-09 (oi, konten_verh, taker_verh …), `funding_historie.db` **täglich** 2019-09 bis 2026-08 |
| **Betrieb heute** | ruft `openInterestHist` (period 1d), `globalLongShortAccountRatio` und `fundingRate` schon ab (`agent/marktrang.py`, `api/derivatives.py`) und **speichert** Terminmarkt-Werte bei jedem Screening in `open_interest_snapshot` (444.582 Zeilen in der Sicherung vom 23.09.: OI je Börse, funding, Long-Anteil) |
| **Option A** | die letzten 72 h aus der **eigenen** Tabelle; keine zusätzlichen Abrufe |
| **Option B** | zum Prüfzeitpunkt aus der Binance-Historie (dieselben Schnittstellen mit period 1h, etwa 2 Abrufe je Asset; nach meinem Kenntnisstand reichen sie rund 30 Tage zurück — **zu verifizieren**) |
| ⚠️⚠️ **Pflicht vor jeder Umsetzung** | **dieselbe Größe wie in der Messbasis**: `open_interest_snapshot` mischt Börsen (Binance, OKX, Bybit) und hat einen eigenen Takt; die Messbasis ist Binance stündlich. Abgleich an einer Kopie (Regel *Betrieb und Messung dieselbe Grundgesamtheit*) |
| **Wann** | erst nach der ganzen Kette (Betriebsumstellung). Jetzt nichts am Notebook |

---

## 7. Prüfung und Gegenprüfung dieser Voranalyse

| Prüfung | Ergebnis |
|---|---|
| Ist die Frage schon beantwortet? | **Nein.** Die Karenz (2.650/2.651) ist eine andere Frage; die Altersachse (2.676) gibt es nur für Kursmerkmale (1a) |
| Widerspricht es einer Nutzerentscheidung? | K5 bleibt *Schwelle auf dem Beitrag* (28.09.), jetzt nachkalibriert; A4 bleibt ein Gewicht (28.09.); kein Blocker |
| Regel 3 (kein Asset-Rang) | ✔ feste Schwellenwerte, gültig bei einem einzelnen Asset |
| *Nicht den Markt messen* | ✔ die Lage-Beiträge haben je Asset verschiedene Werte |
| Mehrfachtesten | 3 Beiträge × 3 Fenster, **ohne** Auswahl des Fensters (V3); Nullwelt Bestes-von-2 für die Varianten |
| Vorgriff | V9: funding als Vortag, Stundenwerte nach Schluss, Gegenprobe 1 h älter |
| Fehleranfälligkeit (Nutzer) | technisch dieselbe Rechnung wie 2c, **mehr Spalten, weniger gemeinsame Parameter**; die Fenster entstehen aus vorhandenen Stundenreihen |
| Der Zeitfaktor (Nutzer) | T4 ist ein **Kriterium** mit 2022; Z6 (neue Monate) ist die eigentliche Antwort und wird ausdrücklich eingeplant |
| Was folgt NICHT | kein Betrieb; kein Hebel; keine Aussage über Short |

---

## 8. Umfang und Reihenfolge

1. **Abstimmung** V1–V10
2. Werkzeug `messe_k5_lage_vorlauf.py` (Datenaufbereitung aus 2c übernommen, die neuen Fenster dazu), vorab committet
3. Tor und R-R11 (bestand), dann vier Mengen, **nach** K6 mit dem Markpreis (nie zwei große Rechnungen zugleich)
4. Befund, Vorlage — und die Regel für Z6 einfrieren
