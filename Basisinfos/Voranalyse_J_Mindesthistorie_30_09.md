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

