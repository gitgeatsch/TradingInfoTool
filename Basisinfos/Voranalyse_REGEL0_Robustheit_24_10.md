# Voranalyse Robustheit der REGEL0 (24.10.2026)

**Wozu:** Die REGEL0 0.1 ergibt mit Kursdaten ab 2019 für 2024–26 −0,34 % statt +0,15 % je Handel nach Kosten (E-136). Zu klären ist:
- Ist der **Vorsprung** der REGEL0 robust gegen den Datenbeginn?
- Welcher Baustein trägt die Abhängigkeit?

Nutzer 24.10.: *„Voranalyse Robustheit starten, prüfen gegenprüfen und doku“*. Hier wird **nicht** gemessen, ob eine Variante trägt. Das macht erst der Messplan (§5), nach Ja.

Werkzeuge:
- `p82_robustheit_voranalyse.py` (Mechanismus, Rauschen);
- `p82_gegenprobe.py` (zweiter Weg);
- Ausgaben jeweils als `.txt` daneben.

## 1. Was wir schon wissen

| Wissen | Quelle |
|---|---|
| Die Schwelle s = +0,035 ist **auf 2024 gewählt** („per Regel auf 2024“); 2025–26 waren die Prüfjahre | `REGEL0_Hebel_Entwurf_30_09.md`, 2.687–2.699 |
| Das Monatsmodell lernt ab **2023-01** bis Monatsbeginn −24 h, nur aus **reifen** Stunden (≥ 1 Jahr Historie, > 1.000 Anker) | `agent/regel0_rechnung.rechne` |
| Der **Datenbeginn je Symbol** in der Messbasis folgt den **Terminmarktdaten** (`hole_stundenkurse.py` leitet die Zeitspannen aus `terminmarkt_historie.db` ab; Binance-Terminmarkt ab 2021-12, jüngere Futures später). Er ist **keine** Wahl für die REGEL0 | `hole_stundenkurse.py` |
| Messbasis nie erweitern: `kursreihen()` nimmt jedes Symbol auf, das ändert die Grundgesamtheit | `MEMORY_SYNC_STRATEGY.md`, CLAUDE.md |
| Vor Kosten trägt nur die REGEL0 (+0,30 % unverzerrt); die Unsicherheit (±0,5 Pp) ist größer als die Kostenlücke | E-128 |
| Die REGEL0 schlägt Zufallsstunden derselben Coins um ≈ +0,6 (2025) bzw. +0,3 Pp (2026) | E-131, `p69_ml_limit.py` (Nullwelt) |

## 2. Mechanismus: welche Bausteine am Datenbeginn hängen (Code gelesen)

| Baustein | hängt am Datenbeginn über | Querschnitt? |
|---|---|---|
| **Reife** (`REIF`) | `st − st0 ≥ 1 Jahr` mit `st0` = erster Anker der Reihe | nein (je Asset), wirkt aber über BASIS auf beide Querschnittsbausteine |
| **eigenes Normal** (`NA`/`NB`) | Jahresfenster bis t−24 h; junge Reihen ab 240 h (J) | nein |
| **Schrumpfung** (`QSh`) | Marktmitte und τ² aus den **reifen** Assets des Vormonats | **ja** |
| **Monatsmodell** (`Ch`) | Trainingsmenge = reife Gitterstunden ab 2023-01 | **ja** |
| rsi-Anfang, Vorlauf 240 h | nur die ersten Wochen einer Reihe | nein |

## 3. Diagnose (`p82`, nur Mechanismus)

### 3.1 Datenbeginn

| Gruppe | Symbole |
|---|---|
| (a) Messbasis ab 2021-12, Binance hatte früher Kurse | 34 |
| (b) Messbasis später, Binance früher (z. B. **BTC, BNB, SOL, AVAX, XLM** erst ab 2023-09 statt 2019/20) | 29 |
| (c) ohne frühere Kurse; davon **23 streng gleich** (bei den übrigen hat der Lückenschluss einige Tage im ersten Monat ergänzt) | 64 |

### 3.2 Querschnitt je Monat (Referenz gegen lang)

| Monat | reife Assets | Trainingsanker (Treffer) | Querschnitt Schrumpfung |
|---|---|---|---|
| 2023-04 | 39 / 56 | 11.629 (6.450) / 17.079 (9.391) | 38 / 55 |
| 2024-01 | 40 / 60 | 54.834 (20.650) / 79.320 (30.468) | 40 / 60, Mitte 0,510 / 0,527 |
| 2024-07 | 49 / 65 | 87.953 / 124.284 | 49 / 64 |
| 2025-01 | 69 / 72 | 130.306 / 173.482 | 68 / 72 |
| 2026-07 | 114 / 114 | 322.723 / 370.491 | 113 / 113 |

- Die Referenz lernt 2023 aus 36–40 reifen Assets, lang aus 54–60. Die Trainingsmenge Anfang 2024 ist lang um **45 %** größer, Mitte 2026 noch um 15 %.
- **τ² = 0** (volle Schrumpfung auf die Marktmitte) in der Referenz in **32 von 33** Monaten, lang in 23 von 33. Das eigene Normal zählt in der Referenz also fast nie.

### 3.3 Herkunft der geänderten Einstiege

- Die geänderten Einstiege verteilen sich auf alle drei Gruppen wie die gemeinsamen.
- ⚠️ **Auch die 23 Symbole mit streng gleicher Kursreihe** haben nur **36 %** gleiche Einstiege (801 gemeinsam, 752 nur lang, 663 nur Referenz).
- ⇒ Die Abhängigkeit kommt aus dem **Querschnitt** (Monatsmodell, Schrumpfung), nicht aus der eigenen Reihe.

### 3.4 Wo die Differenz sitzt (netto je Handel nach 0,48 %)

| Signale am Tag | Tage | Referenz | lang | Anteil an der Differenz |
|---|---|---|---|---|
| 1–5 | 282 | −1,97 % | −1,60 % | −3 % |
| 6–20 | 241 | −0,50 % | −0,57 % | 4 % |
| 21–60 | 172 | +0,31 % | −0,31 % | 61 % |
| > 60 | 46 | +0,76 % | +0,08 % | 38 % |

⇒ Das Plus der REGEL0 entsteht **nur an marktweiten Signaltagen**. Welche Coins sie dort nimmt, hängt am Querschnitt; an ruhigen Tagen verlieren beide Fassungen deutlich.

### 3.5 Rauschen (Tagesblöcke, 2.000 Ziehungen)

| | je Handel | 95-%-Band | Anteil > 0 |
|---|---|---|---|
| Referenz | +0,153 % | [−0,23; +0,59] | 78 % |
| lang | −0,340 % | [−0,82; +0,14] | 9 % |
| Differenz | −0,493 % | [−0,88; −0,17] | 0 % |

- Das Plus der Referenz war **nie von null zu trennen**.
- Die Differenz ist **je Handel gewichtet** deutlich. **Je Tag gleich gewichtet** sind es nur −0,15 % (t = −1,2, Gegenprobe G2). Auch das zeigt: Sie sitzt an Tagen mit vielen Signalen.

## 4. Gegenprobe (`p82_gegenprobe.py`)

| | Ergebnis |
|---|---|
| G1 τ² aus der eigenen Ausgabe des Erzeugers | Referenz 32 von 33, lang 23 von 33. ⚠️ Meine erste Aussage „in allen Monaten“ war falsch (auf 4 Stellen gerundet) und ist oben berichtigt |
| G2 Rauschen über Einzeltage | Referenz [−0,28; +0,57] (schließt 0 ein) · Differenz [−0,87; −0,17] je Handel · ⚠️ je Tag gleich gewichtet −0,15 %, t = −1,2; ergänzt in §3.5 |
| G3 Kursreihen der Gruppe c | 23 Symbole streng gleich und zeilengleich in beiden Dateien. Die Aussage „Querschnitt“ ist an ihnen belegt (§3.3) |

Damit stehen die drei tragenden Aussagen, zwei davon in der berichtigten Form.

## 5. Messplan R Fassung 1 — VORAB FESTGELEGT 24.10.2026 (Nutzer: *„ja Messplan R festlegen“*)

**Frage:** Ist der Vorsprung der REGEL0 gegen den Markt derselben Coins robust gegen den Datenbeginn, und welcher Baustein trägt die Abhängigkeit?

**Teil R1 — gemeinsamer Datenbeginn:**
- Alle Symbole werden ab demselben Start S geladen: 2019-06 · 2020-06 · 2021-06 · 2021-12 · 2022-06 · 2023-01.
- Technisch über `lade_reihen(…, ab=S)` auf `data/_hist`; das ist schon im Erzeuger vorhanden, Betriebscode unverändert.
- Dazu kommt die Referenz (gemischter Beginn). Monate 2024-01 bis 2026-08, Lernbeginn 2023-01 wie im Betrieb.

**Teil R2 — Zerlegung:** Auf S = 2019-06 wird je ein Baustein auf den Referenzstand zurückgesetzt:
- B1 Reife (`erster_anker` = Referenzbeginn, schon ein Parameter von `rechne`);
- B2 Trainingsmenge nur aus Ankern ab dem Referenzbeginn;
- B3 Querschnitt der Schrumpfung ebenso;
- B4 eigenes Normal ebenso.

B2 bis B4 laufen über eine Quelltextkopie wie in `p78`, mit R-R11 der Kopie. **Alle vier zusammen** müssen die Referenz zu ≥ 90 % der Einstiege nachbilden. Sonst gibt es einen fünften Baustein, und die Zerlegung wird als unvollständig ausgewiesen.

**Zielgrößen:**
- **Z1 (Urteil):** Vorsprung gegen Zufallsstunden derselben Coins im selben Jahr (Nullwelt wie `p69`, Kosten fallen heraus), je Handel und **je Tag gleich gewichtet**, beides ausgewiesen;
- **Z2 (Auskunft):** netto je Handel nach 0,48 %;
- **Z3 (Auskunft):** Anteil gleicher Einstiege mit der Referenz;
- **Auskunft:** Aufteilung nach Signaltagen wie §3.4.

**Selbsttest vor dem ersten Blick:**
- (a) 100 Zufallsregeln (Einstiege = Zufallsstunden derselben Coins, gleiche Zahl je Coin und Jahr) durch Z1: Fehlalarm (Rang ≥ 0,95) ≤ 5 %;
- (b) gepflanzter Vorsprung +0,5 Pp auf die Referenz-Einstiege: erkannt (Rang ≥ 0,95) in ≥ 80 %.

**Robust, wenn:**
- (1) Z1 > 0 mit Rang ≥ 0,95 in **mindestens 5 der 6** Startdaten, je Handel **und** je Tag;
- (2) Z1 > 0 in 2025 **und** 2026 getrennt in mindestens 4 der 6.

**Folgen:**
- **robust:** Der Vorsprung gegen den Markt ist echt. Das Kostenproblem bleibt (E-128, E-131). Weitere Optimierung nur auf einer Fassung, die nicht am Datenbeginn hängt (aus R2).
- **nicht robust:** Die REGEL0 hat keinen belegten Vorsprung. Die Signalmail bekommt dazu einen Fakt-Vermerk, und die REGEL0-Optimierung endet. Wie es mit der REGEL0 weitergeht, entscheidest du.

**Aufwand:** ~1 h Rechenzeit, kein Download, keine Betriebsänderung.

⚠️ Nur die Menge *bestand*. Für die eingestellten Paare liegt keine Historie vor 2021 vor; das wird als Einschränkung ausgewiesen.

### 5.1 Auslegung vor dem ersten Lauf (24.10.2026, vor jeder Rechnung einer Variante)

| # | Offene Stelle | Auslegung |
|---|---|---|
| 1 | Z1 „Vorsprung gegen Zufallsstunden derselben Coins im selben Jahr“ | **je Einstieg:** Ertrag 24 h (Schluss zu Schluss, ohne Kosten) **minus die Drift von Coin und Jahr**. Die Drift ist das Mittel aller gültigen Stunden des Coins in diesem Jahr, also genau der Erwartungswert der Nullwelt aus `p69` (ohne Limit). Z1 = Mittel über die Einstiege, je Handel (Gewicht 1) und je Tag (Gewicht 1/Handel am Tag) |
| 2 | ⚠️ **Rang** | Die Nullwelt aus `p69` streut ihre Stunden über das Jahr; die REGEL0 ballt ihre Handel an Signaltagen (§3.4). Ein Rang gegen diese Nullwelt kennt das Rauschen der Ballung nicht. **Deshalb entscheidet der Selbsttest (a), welcher Rang gilt:** zuerst der Rang wie `p69` (1.000 Ziehungen). Liegt sein Fehlalarm in (a) über 5 %, gilt der **Tagesblock-Rang**: Anteil von Z1 > 0 über 1.000 Ziehungen von 7-Tage-Blöcken (wie §3.5) |
| 3 | Selbsttest (a) | 100 Zufallsregeln, **die die Tagesballung der Referenz behalten**. Die Tage der Referenz (mit ihrer Zahl und ihren Coins) werden innerhalb des Jahres zufällig auf andere Tage gelegt; je Einstieg eine zufällige gültige Stunde dieses Coins am neuen Tag. Fehlalarm = Rang ≥ 0,95, je Handel und je Tag; Soll je ≤ 5 % |
| 4 | Selbsttest (b) | dieselben 100 Zufallsregeln, je Einstieg +0,5 Pp gepflanzt: erkannt (Rang ≥ 0,95) in ≥ 80 %, je Handel und je Tag |
| 5 | Kriterium (2) | gilt für **beide** Gewichtungen |
| 6 | R-R11 | (i) Z2 netto der Referenz 2025/2026 = `p69` „ohne Limit“ (+0,132 / −0,021 %) · (ii) S = 2019-06 ergibt zeilengleich `einstiege_A.csv` (die Daten beginnen 2019-06-11) · (iii) die Quelltextkopie für R2 mit allen Schaltern aus ergibt auf `data/_hist` zeilengleich `einstiege_A.csv` |
| 7 | „Referenzbeginn je Symbol“ (R2) | der erste Anker der Symbols in der Referenz (`data/`). Gezählt werden Anker mit Stunde ≥ diesem Wert |
| 8 | Kurse | für alle Varianten aus `data/_hist`; für 2024–26 gleich den Kursen der Messbasis |
| 9 | Werkzeug | `p83_robustheit_r.py` (`--selbsttest`, dann die Messung) |
