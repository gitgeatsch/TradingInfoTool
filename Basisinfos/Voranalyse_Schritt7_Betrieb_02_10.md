# Voranalyse Schritt 7 — die REGEL0 in den Betrieb am Notebook (ENTWURF 02.10.2026, zur Abstimmung)

**Auftrag:** Nutzer 02.10. (E-41): *„Ja, 1. wie von dir empfohlen"* · *„Ja, Schritt 7 – prüfen und gegenprüfen"*.
⚠️ **Das ist nur ein Entwurf.** Gebaut wird erst nach deinem Ja, und am Betrieb ändert sich vorher nichts.

> **Urteil in einer Zeile:** Machbar ist es, und die Last ist klein. Die eigentliche Arbeit liegt in drei Dingen: Das Notebook muss
> **stündliche Kurse** selbst laden, die REGEL0 braucht eine **schlanke Betriebsrechnung** statt der Messwerkzeuge, und sie muss
> **in die Rollen-Kette** eingehängt werden, ohne dass der alte Hebelweg parallel weiterläuft. Vier Fragen dazu entscheidest du.

---

## 0. Ziel, Stand, Test oder Betrieb

| | |
|---|---|
| **Ziel** | Die REGEL0 erzeugt am Notebook **dieselben Signale wie in der Messung** (E-35: Labor-only ist FAIL), ohne Handgriff am Desktop |
| **Stand** | Die REGEL0 läuft nur am Desktop in Messwerkzeugen. Das Notebook hat **keine stündlichen Kurse** (Teilexport 01.10.) |
| **Test oder Betrieb** | **Betrieb.** Die Umstellung selbst ist Schritt 8, nach der ganzen Kette und deinen Mindestbedingungen |

---

## 1. Ist-Stand des Betriebs — am Code kartiert (02.10.)

| | heute |
|---|---|
| **Wer Signale erzeugt** | Seit dem 15.08. ausschließlich die **Rollen-Kette** (`scheduler/rollen_job.py` → `agent/rollen_lauf.py`). Spot und Hebel kommen aus **einem** Lauf und landen in `signals` (`quelle_kette='rollen'`). Der Job `hebel_screening` läuft alle 15 min und stößt die Kette an |
| **Woher der Hebel kommt** | aus der Quote `potential.rechne(instrument="hebel")`, danach `betraege.hebelrechnung` (halbes Kelly → Risiko → Hebel). Unter 2,0 wird Spot daraus, der Deckel liegt bei 5,0, dazu der Aggregat-Deckel. Das ist die **„Hebel- und Spot-Achse“**, die ersetzt werden soll |
| **LLM-Rollen** | A Lagebild (nur Kontext) · **BC Trader entscheidet die Aktion** (nicht Hebel und Größe) · G Einwand (nur Mailtext) · Z1 deterministische Zählung. Anbieter Gemini, OpenRouter, Groq, Z.ai |
| **Mail** | `agent/signal_mail.py::baue_mail`, Versand über `rollen_job.baue_versand` |
| **Stündliche Daten** | **keine** Stundenkerzen. Es gibt nur Tageskerzen (Kraken/Binance 1d) und 15-Minuten-Schnappschüsse (`price_cache`, `open_interest_snapshot`) |
| **Messdateien im Betrieb** | ✔ Keine REGEL0-Datei wird vom Produktionspfad gelesen (`stundenkurse*.db`, `markpreis*.db`, `messe_losfahren`, `hebel_neubau`). Die Trennung hält |
| **alte Hebel-Kette** | `hebel_screening.aktiv: false` seit 12.09., die Tabellen `hebel_triggers` und `hebel_signals` sind still |

**Nebenbefund (nicht Teil von Schritt 7, als eigene Aufgabe vorgeschlagen):** Die Rollen-Kette prüft den Mail-Schalter `benachrichtigung.aktiv`, die Konfiguration führt ihn als
`benachrichtigung.email.aktiv`. Ein Abschalten der Mails würde dort vermutlich nicht greifen.

---

## 2. Last — gemessen, nicht geschätzt

| Lauf am Desktop (i9-9900K, 34 GB) | Zeit | Spitze Arbeitsspeicher |
|---|---|---|
| REGEL0-Export, alle Monate 2024–26, mit den neuen Assets (`messe_losfahren.py`) | 152 s | **2,50 GB** |
| Simulation mit Hebelstufe (`messe_k6_hebelstufe.py`) | 577 s | 1,26 GB |
| **Lastprobe** `nb_lastprobe.py` (Zufallsreihen, 650 Assets × 1 Jahr, dieselben Bausteine) | **18 s** | **0,79 GB** |
| davon Monatstraining (6 Stufen × 4 Blöcke, 250.000 Anker) | 15,6 s | |
| davon **eine Stunde bewerten** (650 Assets) | **< 0,01 s** | |

✔ Der Export ist **reproduzierbar**: Ein zweiter Lauf ergab 10.733 Einstiege, zeilengleich zur gespeicherten Datei.

➤ **Folge:** Die **Messwerkzeuge** sind für den Betrieb zu schwer (2,5 GB, Minuten), weil sie bei jedem Lauf alle Jahre neu rechnen. Der **Betrieb** braucht das nicht.
Einmal im Monat wird trainiert (Sekunden), jede Stunde wird nur die neue Stunde bewertet (Millisekunden). Die Probe am Notebook (Abschnitt 6, F5) liefert das
Verhältnis zum Desktop. Damit lassen sich die echten Zeiten umrechnen.

**Daten:** etwa 1.300 Abrufe je Stunde (Kurse und Markpreise), rund 1 % des Binance-Limits. Speicher 2–3 GB bei 60 GB frei.

---

## 3. Was die REGEL0 am Notebook braucht (B1–B9 aus dem Plan)

| | Bedarf | Stand | Bauaufgabe |
|---|---|---|---|
| B1 | stündliche Kurse: Messbasis (116 ab 2021-12) und alle übrigen (537 ab 2023) | ⛔ fehlen | **S7-1** Lader am Notebook: erst die Historie, dann stündlich nachladen (dieselben Lader wie am Desktop) |
| B4 | Markpreise (Liquidation, Hebelstufe) | ⛔ fehlen | **S7-1** Historie aus den Monatsarchiven, laufend über die Live-Schnittstelle. ⚠️ Prüfen, dass Archiv und Live **dieselben** Werte liefern |
| B2 | Monatstraining rsi-Modell (Messbasis, ab 2023, reife Stunden) | ⛔ nur im Messwerkzeug | **S7-2** schlanke **Betriebsrechnung** und **S7-3** Monatsjob, der das Modell speichert |
| B3 | ATR-Modell der Hebelstufe | ⛔ nur im Messwerkzeug | S7-2 / S7-3 |
| B8 | eigenes Normal je Asset (J ab 240 h, Schrumpfung zur Marktmitte) | ⛔ | S7-2 |
| B5 | dieselbe **Grundgesamtheit** (Training auf genau den 116) | ⚠️ muss am Notebook **identisch** entstehen | S7-1 mit Prüfung: Symbolliste und Zeilenzahl gegen die Desktop-Kopie |
| B6 | Zuordnung Bitpanda → Binance | ✔ `symbol_zuordnung.csv` per `git pull` | **S7-5** täglicher Katalog- und Preisabgleich mit Meldung |
| B7 | Assets ohne Daten | ✔ bekannt (AIOZ, SUPRA, VSN, XDC) | Meldung in der Mail |
| B9 | Mail, LLM-Rollen, Importer | ⛔ kennen die REGEL0 nicht | **S7-4** Einhängen in die Rollen-Kette (F1, F2) |
| — | scipy am Notebook | ✔ installiert | — |

---

## 4. Bauplan nach deinem Ja — jeder Schritt mit eigener Prüfung

| # | Schritt | Prüfung (muss fehlschlagen **können**) |
|---|---|---|
| **S7-1** | Datenbasis am Notebook: Historie laden (Kurse, Markpreise), dann stündliche Jobs | Kopie in den Austauschordner, **am Desktop** gegen die eigene Datei vergleichen (CLAUDE.md: Prüfungen gegen eine Kopie): Symbole, Zeilen, Stichprobe Kurse zeilengleich |
| **S7-2** | **Betriebsrechnung** `regel0_betrieb` (neu, schlank): Normal, rsi, v̂, Ersteintritt mit Ruhe, Hebelstufe | **R-R11 am Desktop:** über 2024–26 nachgerechnet muss sie die Einstiege der Messung **zeilengleich** treffen (`kern48jbz_einstiege_bestand.csv`) und dieselbe Hebelstufe je Handel liefern |
| **S7-3** | Monatstraining als Job (rsi- und ATR-Modell speichern) | dieselben Modelle wie die Messung (Parameter bitgleich), am Notebook trotz anderer numpy-Version (Abweichung ausweisen, Signale gleich) |
| **S7-4** | Einhängen in die Rollen-Kette nach F1/F2, der alte Hebelweg wird abgeschaltet | Funktionstest am Prüfstand mit echter `config.yaml` (Memory-Regel), Mail per diff, LONG **und** SHORT |
| **S7-5** | täglicher Abgleich: Katalog und Zuordnung, Meldung bei Sperre oder neuer Ausnahme | Gegenprobe: eine absichtlich falsche Zuordnung muss gemeldet werden |
| **S7-6** | **R-R11 am Notebook:** Die Signale einer vergangenen Woche nachrechnen und als Kopie gegen den Desktop halten | zeilengleich |
| **S7-7** | Deine **Mindestbedingungen** (F4) prüfen, dann **Schritt 8 Umstellung**: Pull, Neustart, Export nach etwa 30 Minuten | NB-Teilexport |

⚠️ **Die Produktions-DB beschreibt nur der Betrieb selbst** (Signale wie heute). Kein Prüf- oder Messskript schreibt hinein. Jede Prüfung bekommt einen Wegwerfpfad.

---

## 5. Risiken

| Risiko | Gegenmittel |
|---|---|
| Andere **Grundgesamtheit** am Notebook (fehlende Symbole oder Stunden) | S7-1 prüft Symbolliste und Zeilen gegen die Desktop-Kopie, bevor trainiert wird |
| **numpy 2.5.1** statt 2.4.6 | S7-3 weist die Abweichung der Modellparameter aus. Maßstab sind gleiche **Signale** |
| **Markpreis live ≠ Archiv** | S7-1 vergleicht beide für einen gemeinsamen Monat |
| Binance fällt aus oder liefert verspätet | Der bestehende Wächter für veraltete Daten wird auf die Stundenkurse erweitert. Ohne frische Stunde gibt es kein Signal und eine Meldung |
| **Parallelbetrieb** von altem und neuem Hebelweg | ausgeschlossen: S7-4 schaltet den alten Hebelvorschlag ab (F1) |
| Mailflut | erwartet: 40 Assets × 2–4 Signale im Monat, also **etwa 3–5 Signale am Tag** |
| Die letzte Kerze ist beim Laden noch offen | gelöst wie am Desktop: Neustart bei `MAX(stunde)`, Überschreiben erlaubt |

---

## 6. ⚠️ Zur Abstimmung — vier Fragen und eine Bitte

| # | Frage | Vorschlag |
|---|---|---|
| **F1** | **Umfang:** Ersetzt die REGEL0 nur den **Hebel** oder auch den **Spot**? | ➤ **nur den Hebel.** Die Rollen-Kette darf dann keinen Hebel mehr vorschlagen, ihre **Spot**-Entscheidungen laufen weiter wie heute. Gründe: Die REGEL0 ist ein Tageshandel mit Hebel, ihr Spot-Konto liegt um null, und der Spot-Arm ist ein eigenes Thema |
| **F2** | **LLM-Rollen:** Heute entscheidet Rolle BC die Aktion. Bei der REGEL0? | ➤ Die REGEL0 **löst aus** (deterministisch), die LLM-Rollen **prüfen und kommentieren** nur (Einwand, Lagebild als Mailtext). So steht es auch im Memory: *LLM ist Prüfung, nicht Entscheider* |
| **F3** | **Historie ans Notebook:** übertragen (USB, ~2,5 GB) oder vom Notebook selbst laden? | ➤ **selbst laden**, mit denselben Ladern (1–3 h einmalig), danach gegen die Desktop-Kopie prüfen. So hängt der Betrieb nie am Desktop (E-35) |
| **F4** | **Mindestbedingungen** vor der Umstellung (du wolltest an diesem Schritt reden) | Vorschlag zum Besprechen: (a) R-R11 am Notebook zeilengleich, (b) eine **Probewoche**, in der die REGEL0-Signale als **„Probe“** markiert mailen und der alte Hebelweg schon aus ist (kein Parallelbetrieb), (c) danach die Freigabe durch dich |
| **F5** (Bitte) | Am Notebook nach `git pull`: `python nb_lastprobe.py` | Das Ergebnis landet direkt im Austauschordner (`nb_lastprobe_T440.txt`) und gibt das Verhältnis zum Desktop |

---

## 7. Abstimmung (Nutzer 02.10.2026)

**Nutzer:** *„Ja, F1 bis F2 wie vorgeschlagen, F3 und 4 besprechen wir. F3: rascher Einsatz am NB, würde eine fertige und geprüfte Datei auf das NB per USB kopieren,
es sei denn, du sagst, die Lader sind sicherer. F4 wird etwas aufwändiger, aber es soll die neue Ablaufkette die alte sofort ersetzen – eine Woche testen und optimieren,
ggf. weitere Simulationen zur Stabilität und fachlichen Funktionalität."*

| | |
|---|---|
| ✔ **F1** | Die REGEL0 ersetzt **nur den Hebel**. Die Rollen-Kette schlägt keinen Hebel mehr vor, ihre Spot-Entscheidungen laufen weiter |
| ✔ **F2** | Die REGEL0 **löst aus**, die LLM-Rollen prüfen und kommentieren nur (Mailtext) |
| ◐ **F3** | im Gespräch: USB-Kopie der geprüften Dateien (Nutzer) |
| ◐ **F4** | im Gespräch: sofortiger Ersatz, eine Woche testen und optimieren, dazu Simulationen zu Stabilität und Funktion |

**Beim Prüfen von F3 gefunden:** Der Messbasis-Lader `hole_stundenkurse.py` leitet Symbole und Zeitspannen aus `terminmarkt_historie.db` ab. Am Notebook liegt davon
**nur die Symbolliste** (12 KB, Sollzustand). Er wäre dort also **nicht** lauffähig. Für das laufende Nachladen braucht der Betrieb ohnehin einen **eigenen Nachlader**.

