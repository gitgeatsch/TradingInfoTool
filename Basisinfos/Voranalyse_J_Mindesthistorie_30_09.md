# Voranalyse J — der SHOWSTOPPER Mindesthistorie beheben (30.09.2026)

**Auftrag (Nutzer 30.09.):** *„Ja, Voranalyse schreiben, prüfen und gegenprüfen."* Vorher: *„Die erforderliche Mindesthistorie ist
eigentlich ein Showstopper und keine Schwäche, und war so nicht geplant und gewünscht, vor allem wenn man unsere Datenlage
berücksichtigt."*
**Grundanforderungen:** *„das System muss auch bei nur EINEM Asset funktionieren"* (2.608) · *„10 Tage Historie, nicht Jahre"* (2.610).

> **Urteil in einer Zeile:** Wir ersetzen die harte 12-Monats-Bedingung durch die **schon vorhandene Schrumpfung**. Ein Asset
> ohne eigene Historie startet auf dem **Marktnormal** und wächst hinein. Für reife Assets bleibt alles **bitgleich**, und es wird
> gemessen, ob die neu hinzukommenden Einstiege tragen.

---

## 1. Wo überall Historie verlangt wird — am Code geprüft

| Stelle | verlangt | Wirkung | in J |
|---|---|---|---|
| ⛔ **eigenes Normal** `normal()` | `st − st[0] ≥ 8.760 h` **und** > 1.000 Stunden | kein NA/NB, damit kein QN, QS, QSh, v̂ und kein Signal | ➤ **ersetzen** |
| Offset `OFF = logit(NA, NB)` | dasselbe Normal | Das Asset ist nicht im **Training** des rsi-Modells | bleibt so: Das Modell lernt weiter nur aus reifen Assets (R-R11) |
| geschrumpftes Normal QS/QSh | ≥ 500 Anker je Monat (quer über alle Assets) | unkritisch | Marktmitte und τ² weiter nur aus reifen Assets |
| rsi-Monatsabstand `rsi_s` | 720 h Fenster, **mindestens 240 h** (10 Tage) | echte Mindestanforderung des Signals | bleibt, **das ist die neue Mindesthistorie** |
| ATR, Vola-Median | ATR 14 h, Median 240 h | echte Anforderung von Bewertung 2 | bleibt |
| Ruhe 48 h | ≥ 40 gültige Stunden | Teil der Regel | bleibt |
| Lader der Messbasis | > 2.000 Stunden Gesamtreihe (etwa 83 Tage) | Auswahl der **Messbasis**, keine Regel. Sehr neue Listings fehlen in der Messung | Auskunft. Im Betrieb gilt die Regel ab 10 Tagen |

---

## 2. ⚠️ Gegenprüfung — der Showstopper trifft auch die GRUNDLAGE der REGEL0

Von den **116** Symbolen in bestand beginnen die Stundendaten bei **49 erst ab 2023-09 oder später**, darunter SOL, AVAX, BNB, INJ, APT, IMX, XLM
und QNT (Datenbeginn 2023-09-01, keine echten Neulistungen). Mit 12 Monaten Vorlauf fehlten sie **bis in den Herbst 2024**, also in großen
Teilen des Jahres, auf dem die Schwelle s = +0,035 **gewählt** wurde. Die Wahl-Grundgesamtheit 2024 war damit um bis zu 40 % kleiner als
gedacht, und zwar ausgerechnet ohne mehrere große Assets.

➤ **Folge:** J ist die Voraussetzung dafür, dass die REGEL0 **richtig** ist. Das ist mehr als eine Erweiterung.

---

## 3. Der Lösungsweg — nur die bestehende Formel, keine neue Zahl

Heute (je Monat, über die Assets mit Normal):
QSh = mitte + B · (QN − mitte), mit B = τ² / (τ² + Rauschen) und Rauschen = q(1−q) / max(Rate · **365**, 5).

| | Änderung |
|---|---|
| **eigenes Normal** | aus der **vorhandenen** Historie, höchstens 12 Monate, sobald mindestens **240 h** vorliegen (dieselbe Grenze wie `rsi_s`, nicht gewählt) |
| **Rauschen** | Rate · **min(365, Tage eigener Historie)**. Das ist die tatsächliche Zahl der Beobachtungen. Für reife Assets ist das **genau 365**, also **bitgleich** |
| **mitte, τ²** | weiter **nur aus reifen Assets** geschätzt, also bitgleich. Junge Assets werden daran geschrumpft |
| unter 240 h | kein Signal, weil auch `rsi_s` fehlt |
| rsi-Modell | Training unverändert (nur reife Assets, also bitgleich). Der **Beitrag** wird für junge Assets mit demselben Monatsmodell berechnet |

➤ Ein junges Asset hat anfangs wenige eigene Ereignisse, also viel Rauschen, B nahe 0 und damit QSh ≈ **Marktmitte**. Mit jedem Monat wächst
sein eigener Anteil. Das ist genau *„auf dem Marktnormal starten und hineinwachsen“*.

---

## 4. Die Messung — vorab festgelegt

**Zwei Gruppen von Einstiegen** (Kern REGEL0: s = +0,035, Ruhe 48 h, Einstieg 1 h später):
- **reif**: Stunden, zu denen das Asset ≥ 12 Monate Historie hat. Sie müssen **bitgleich** zu REGEL0 sein (R-R11)
- **neu**: Stunden, die bisher durch die 12-Monats-Bedingung gesperrt waren (junge Listings **und** die Datenbeginn-Fälle von 2023-09)

⭐ **Die neuen Einstiege sind vollständig ungesehen**, auch in 2024. Sie wurden nie ausgewertet. Deshalb zählt **2024–2026**.

| # | Kriterium für die neuen Einstiege | Art |
|---|---|---|
| **J1** | Chance Dq > 0 in **jedem Jahr** 2024, 2025 und 2026 (wo mindestens 100 Einstiege) | Urteil |
| **J2** | über dem **P90 der Nullwelt** (rollierende Modelle auf verschobenem rsi, 40 Ziehungen) | Urteil |
| **J3** | **Tagesblock** untere Grenze > 0 · **Spiegel** > 0 (E-29) · je Asset ≥ 60 % (Assets mit ≥ 20 neuen Einstiegen) | Urteil |
| **J4** | ≥ **3 von 4** Mengen, bei Auseinanderlaufen gilt unverzerrt (E-30) | Urteil |
| J5 | *neu* gegen *reif*: Chance, Rohvorteil je Handel (Simulation REGEL0), Hebelstufe, Liquidationen | Auskunft |
| J6 | wie viele Einstiege und Assets kommen hinzu, je Jahr. Nach Alter der Historie (10 Tage bis 3 Monate, 3–6, 6–12) | Auskunft: Ab wann trägt es? |

**Bestanden** (J1–J4): J wird **Teil der REGEL0**, und die REGEL0 wird mit J festgeschrieben.
**Nicht bestanden:** Lösungspflicht (E-25). Denkbar sind eine längere Mindestzeit, begründet über J6, oder ein Hinweis *„junges Asset, Bewertung auf Marktnormal“* in der Mail.

---

## 5. Was danach offen ist — ehrlich

- **Die Schwelle s = +0,035** wurde auf der zu kleinen Grundgesamtheit 2024 gewählt (Abschnitt 2). Nach J ist zu prüfen, ob die Wahlregel auf der
  **vollständigen** 2024-Menge dieselbe Stufe wählt. Das ist ein kleiner Lauf (Wahl 2024), R-R11 gegen 2.687/2.688. Wählt sie eine andere
  Stufe, wird das der erste Schritt zur REGEL1 und kommt zur Abstimmung.
- Die **Simulation** der REGEL0 (Referenzzahlen) wird mit J auf der vollständigen Menge neu gerechnet. Die alten Zahlen bleiben als Vergleich.

---

## 6. Umfang

Werkzeug: `normal()` und die Schrumpfung in `messe_losfahren.py` bekommen den Schalter `--junge` (ohne Schalter bitgleich wie bisher) und die
Gruppenmarke *neu/reif*. Der Export der Einstiege bekommt dieselbe Marke, damit die Simulation beide Gruppen trennt. Ablauf: Funktionstest →
**R-R11** (reif bitgleich) → **Commit** → 4 Mengen Kern (je etwa 8 Minuten) und Simulation (je etwa 12 Minuten) → **Stopp und Bericht**.

---

## 7. Zur Abstimmung (J-a bis J-d)

| # | Vorschlag |
|---|---|
| **J-a** | Lösungsweg Abschnitt 3: das eigene Normal aus der vorhandenen Historie ab 240 h, das Rauschen aus der tatsächlichen Beobachtungszahl, mitte, τ² und rsi-Modell nur aus reifen Assets |
| **J-b** | Messung Abschnitt 4: J1–J4 als Urteil auf den **neuen** Einstiegen 2024–26, J5/J6 als Auskunft, reif bitgleich |
| **J-c** | Bestanden, dann wird J Teil der REGEL0. Danach die Prüfung der Schwellenwahl auf der vollständigen 2024-Menge (Abschnitt 5) |
| **J-d** | erst dann die Messung auf deiner **Hebel-Liste**, mit den jungen Assets |

---

## 8. ✔ ABGESTIMMT (30.09.2026) — J-a bis J-d; Umsetzung und Gegenprüfung VOR dem Lauf

**Nutzer:** *„Ja, mit J beginnen, prüfen und gegenprüfen."* Dazu die Einordnung zum Betrieb: Übertragung und laufende Datenanbindung
sind **kein Showstopper**, sondern eine Bauaufgabe (Plan, Schwäche S2).

**Umsetzung** (`messe_losfahren.py --junge`, ohne den Schalter bitgleich wie bisher):
- `normal()` lässt das eigene Normal ab **240 h + Fenster** zu. `REIF` merkt die alte 12-Monats-Bedingung.
- `BASIS &= REIF`: Das Training, die Suche/Prüfung und die Marktmitte bleiben auf reifen Stunden.
- Junge Stunden werden an **derselben** Marktmitte und τ² geschrumpft. Das Rauschen ergibt sich aus Rate × min(365, Tage der Historie).
- Die Auswertung J1–J6 steht mit `--bestaetigen 0.035` für die Jahre 2024–2026. Der Export mit `--junge` schreibt `kern48j_einstiege_<m>.csv` und die Gruppenmarke `kern48j_gruppe_<m>.csv`, die Simulation liest `--gruppe` (J5).

**Gegenprüfung (Probe, bestand, 8 Monate):**
1. v̂ ist auf allen reifen Stunden **bitgleich** (Diagnose `--debug-vh` an EDU).
2. ⚠️ **Randfälle an der 12-Monats-Grenze:** 3 Einstiege (EDU, STX, SUI) entstehen erst durch J. Das Signal kam kurz nach der Grenze, und ohne
   J hatte das Ruhefenster davor weniger als 40 gültige Stunden. Das ist die **gewollte** Wirkung und kein Fehler. ➤ *Reif* ist deshalb auf Einstiegsebene
   präzisiert: Auch das **ganze Ruhefenster** muss reif sein (`reif_e`). Diese Randfälle zählen zu *neu*.
3. ✔ **R-R11:** Die reifen Einstiege sind mit `--junge` **zeilengleich** zum Export ohne `--junge` (462 von 462, inklusive der Ausgänge t_u und t_d).
4. Behoben: Bei einem frei gewählten Zielnamen (`--ziel`, nur in Tests) überschrieben die Wucht- und Gruppendatei die Einstiegsdatei. Die echten Dateinamen waren nie betroffen.


---

## 9. ERGEBNIS (4 Mengen) — Befund 2.698: ✔ J BESTANDEN

Belege `Basisinfos/J_30_09/` (`kern__`, `export__`, `sim__<menge>.txt`, `_kette.log`).

| | bestand | unverzerrt:1 | unverzerrt:2 | unverzerrt:3 |
|---|---|---|---|---|
| Einstiege gesamt / davon **neu** | 9.905 / 2.094 (21,1 %) | 10.337 / 1.836 (17,8 %) | 9.670 / 1.954 (20,2 %) | 9.956 / 1.930 (19,4 %) |
| Assets mit neuen Einstiegen | 74 | 72 | 74 | 74 |
| R-R11 reif 2025–26 (REGEL0) | 6.326 / +0,1037 (6.328 / +0,1039) | 7.119 / +0,0776 | 6.461 / +0,0696 | 6.780 / +0,0783 |
| **J1** Chance neu 2024 / 2025 / 2026 | +0,091 / +0,069 / +0,204 | +0,111 / +0,050 / +0,183 | +0,135 / +0,060 / +0,174 | +0,127 / +0,051 / +0,194 |
| **J2** neu gesamt · Null-P90 | +0,090 · +0,028 | +0,081 · +0,023 | +0,091 · +0,032 | +0,086 · +0,027 |
| **J3** Tagesblock · Spiegel · je Asset | +0,033 · ✔ · 85 % | +0,019 · ✔ · 80 % | +0,024 · ✔ · 81 % | +0,031 · ✔ · 85 % |
| Urteil | ✔ | ✔ | ✔ | ✔ |
| J5 Chance neu / reif | +0,090 / +0,117 | +0,081 / +0,097 | +0,091 / +0,090 | +0,086 / +0,096 |
| **J6** nach Alter: 10 T–3 M · 3–6 M · 6–12 M | +0,046 · +0,082 · +0,113 | +0,074 · +0,109 · +0,076 | +0,059 · +0,091 · +0,104 | +0,062 · +0,101 · +0,091 |
| **Simulation** Rohvorteil neu / reif | +0,64 % / +0,57 % | +0,48 % / +0,29 % | +0,42 % / +0,31 % | +0,50 % / +0,31 % |
| Rohvorteil gesamt (REGEL0 ohne J) | +0,58 % (+0,57) | +0,32 % (+0,29) | +0,33 % (+0,31) | +0,34 % (+0,31) |
| Hebelkonto gesamt (REGEL0 ohne J) | +0,263 (+0,204) | −0,488 (−0,466) | −0,454 (−0,417) | −0,406 (−0,382) |
| Liquidationen neu / reif | 0,32 / 0,21 % | 0,72 / 0,53 % | 0,65 / 0,49 % | 0,72 / 0,30 % |

➤ **J besteht in 4 von 4 Mengen** (J1–J4). Die neuen Einstiege tragen in **jedem Jahr**, schon ab **10 Tagen Historie**, und sind wirtschaftlich
**nicht schlechter** als die reifen. In den unverzerrten Mengen liegt ihr Rohvorteil sogar höher.

**Prüfung und Gegenprüfung:**
1. **R-R11:** Die reifen Einstiege sind zeilengleich zur REGEL0, bis auf **2–3 Randfälle je Menge** an der 12-Monats-Grenze (in bestand geprüft: BNB und SXT gelten
   als *neu*, IO entfällt, weil in den Stunden vor der Grenze schon ein Signal lag). Das ist erklärt und gewollt.
2. Die neuen Einstiege sind **vollständig ungesehen** (nie ausgewertet), auch in 2024. Das ist der sauberste Beleg des ganzen Tages.
3. In den **ersten 3 Monaten** ist die Chance etwas kleiner (+0,05..+0,07), aber positiv. Das passt dazu, dass das Normal dort noch nahe am Markt liegt.
4. ⚠️ **Liquidationen** der neuen etwas höher. Junge Assets sind unruhiger. Das ist ein Hinweis für **L** (Liquidität in Bewertung 2).
5. Das Hebelkonto verliert in unverzerrt etwas mehr, weil **mehr Handel** zur selben Kostenlücke stattfinden. Das ist die bekannte Schwäche S3, keine von J.

➤ **Folge:** J wird **Teil der REGEL0**. Nächster Schritt nach Plan: die **Schwellenwahl** auf der vollständigen 2024-Menge.

---

## 10. SCHRITT 2 — die Schwellenwahl auf der vollständigen 2024-Menge (vorab festgelegt, Nutzer-Ja 30.09.)

**Nutzer:** *„Ja, Schwellenwahl starten, prüfen und gegenprüfen."*

Die Schwelle s = +0,035 wurde mit **24 h Ruhe ohne J** gewählt (2.687/2.688). Die Ruhe 48 h kam später (2.691). Die Wahlregel bleibt **unverändert**:
Raster +0,010..+0,050, größter Abstand *echt − P90 Nullwelt*, bei Gleichstand (< 0,005) die niedrigere Stufe, nur 2024, Menge bestand.

| Lauf | Form | Zweck |
|---|---|---|
| **W0** | Ruhe 24 h, ohne J | **R-R11**: muss bitgleich zu 2.687 wählen (Stufe 0,02 = +0,0928, 0,04 = +0,0759, gewählt +0,035) |
| **W1** | Ruhe 24 h, mit J | Wirkung der vollständigen Menge allein |
| **W2** ⭐ | **Ruhe 48 h, mit J** | die REGEL0-Form, **entscheidend** |

**Folge:** Wählt W2 **+0,035**, wird die REGEL0 festgeschrieben. Wählt W2 eine **andere** Stufe, wird das vorgelegt, denn die neue Stufe braucht eine
eigene einmalige Bestätigung auf 2025–26 (Nutzer-Ja).

