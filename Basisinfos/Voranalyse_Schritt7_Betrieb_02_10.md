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


### Nachtrag 02.10. — F3 erledigt, Betriebsparameter, REGEL1-Kandidaten (E-42)

- ✔ **F3:** Das USB-Paket (L:\ClaudeSync\Schritt7_Datenbasis, 823 MB gepackt) wurde vom Stick ausgepackt und am Desktop gegengeprüft. **Am Notebook ausgepackt und geprüft: korrekt** (Nutzer).
  Die vier Dateien liegen dort **ungenutzt**, bis die Betriebsrechnung gebaut ist (kein Leser im Produktionspfad).
- ✔ **Prüfzeitpunkt und Cooldown** stehen in der REGEL0 (Dokument und `hebel_neubau.REGEL0`): stündlich, alle Assets, kein eigener Cooldown, Ruhe 48 h je Asset (gemessen mindestens 49 h).
- ✔ **REGEL1-Kandidaten** im Plan (O13): Fortsetzung; Positionsführung und Ausstieg nur für echte offene Positionen.
- ◐ **F4 offen:** versionierte Regeln (Vorschlag: live eine festgeschriebene Fassung, Wechsel nur zu festgelegten, freigegebenen Zeitpunkten, nie mitten in einer Testwoche) und die Punkte 4–7 (Ausstiegserinnerung, Positionsgröße, Bitpanda-Stufen, Spot gegen Hebel auf demselben Asset).


### Nachtrag 02.10. — F4 Punkt für Punkt (E-43)

| | |
|---|---|
| ✔ 1 | versionierte Regeln, kritische Punkte auch unter der Woche änderbar (neue Version, Vermerk) |
| ✔ 2 | Start M1: Ausstiegszeit in der Einstiegsmail und Erinnerung nach 24 h. Echte Ausstiegsmails und Positionsführung folgen (O13) |
| ◐ 3 | **Positionsgröße:** Deckel und Altbestand analysieren (O15), ➤ nächster Punkt |
| ✔ 4 | Hebelstufe gedeckelt auf das, was das Asset bei Bitpanda erlaubt |
| ◐ 5 | Spot-Kette nach dem Hebel ersetzen und vorerst stilllegen. **Je Strategie ein eigener Pfad** (O14). ⚠️ Das ändert F1: Statt *Spot läuft weiter wie heute* wird die Spot-Kette nach dem Hebel stillgelegt. Bis dahin läuft sie wie heute |

### Nachtrag 02.10. — Lastprobe am Notebook, Spot präzisiert, Punkt 3 begonnen

**Lastprobe T440** (Nutzer, gleiche Prüfsumme 0,991801 wie am Desktop, trotz numpy 2.5.1):

| | Desktop | Notebook | Faktor |
|---|---|---|---|
| gesamt | 17,9 s | 63,0 s | 3,5 |
| Monatstraining (Probe) | 15,6 s | 56,0 s | 3,6 |
| eine Stunde bewerten | < 0,01 s | < 0,01 s | — |
| Spitze Arbeitsspeicher | 0,79 GB | 0,79 GB (9,5 % des freien) | — |

➤ Die echte REGEL0 braucht im Monatstraining am Desktop etwa 2,1 s je Monat, am Notebook also **rund 8 s**. Die stündliche Bewertung ist vernachlässigbar. **Die Rechenlast ist kein Engpass.**
⚠️ Betriebsbereit ist damit die **Rechenleistung**, nicht die REGEL0 (Betriebsrechnung, Nachlader und Einhängen fehlen noch).

**Spot (Nutzer):** *„es muss nicht sofort sein – es geht um die Frage, wann der korrekte Zeitpunkt ist, wenn der Hebel läuft, die alte Kette Spot an die neuen Anforderungen
anzupassen – deine Frage Spot oder Hebel Signal ist obsolet, da die Spot-Signale keine Bedeutung mehr für den echten Handel haben und nur Last erzeugen."* → O14 präzisiert.

**Punkt 3 Positionsgröße (O15) begonnen:** Die Deckel im Code werden kartiert. Der NB-Teilexport ist um den **Altbestand** erweitert (Hebelpositionen je Status, offene Positionen mit Hebel,
Wert und Eigenkapital, Portfoliowert der letzten 3 Tage), nur lesend.

---

## 8. Punkt 3 — Positionsgröße (O15): Analyse zur Entscheidung

### 8.1 Wie die Kette die Größe heute rechnet (Code kartiert, Werte aus dem NB-Teilexport 02.10.)

| | heute | Wert am Notebook |
|---|---|---|
| Einsatz je Hebeltrade | fest | **500 €** (`hebel_aus_quote.hebelnenner_eur`) |
| Risiko je Trade | halbes Kelly aus der alten Trefferquote, geklemmt | **0,5–1,25 %** des Kapitals (`r_min`, `r_max`) |
| Hebel | Risiko / Stopabstand / 500, Spot unter 2x, höchstens 5x | `hebel_ab` 2,0 · `hebel_grenze` 5,0 |
| **Gesamtdeckel** | alle offenen Hebelrisiken (Verlust bis zum Stop) zusammen | **3 %** des Kapitals (`aggregat_anteil`) |
| Kapitalbasis | Wert des Spot-Bestands **ohne** Cash und ohne Hebelpositionen | 20.868 € (Cash 3.874 €) am 01.10. |
| Töpfe | nur Information in der Mail, **keine** Blockierung | Spot 4.000 € · Hebel 3.000 € |
| Altbestand | zählt nur zum Gesamtdeckel. Keine Sperre gegen eine zweite Position im selben Asset | **keine offene Hebelposition** (185 geschlossen, 4 wahrscheinlich liquidiert) |

⚠️ **Der Gesamtdeckel passt nicht zur REGEL0.** Er misst das Risiko **bis zum Stop**, die REGEL0 hat aber keinen Stop. Ihr Risiko je Handel ist der **ganze Einsatz** (Liquidation).
Bei einem Einsatz von 1 % des Kapitals erlaubte er nur **drei** gleichzeitige Positionen.

### 8.2 Wie viele REGEL0-Positionen gleichzeitig offen sind (gemessen 2025–26)

| | alle bewerteten Assets | **deine Hebel-Liste** |
|---|---|---|
| Signale je Tag | 13,9 | **2,6** |
| gleichzeitig offen: Mittel · P95 · P99 · Maximum | 13,8 · 58 · 86 · 112 | **2,5 · 11 · 17 · 23** |

Die Signale kommen in **Ballungen** (marktweite Bewegungen).

**Sind Signale in einer Ballung schlechter?** Die Antwort ist **widersprüchlich**. Über die 116 Assets sind die **vereinzelten** am schlechtesten (Rohvorteil −0,59 %), auf deiner Liste die **in der Ballung**
(11–20 offen: −0,84 % gegen +1,05 % bei 0–2). Die Jahre sind schon gesehen, es ist also nur Auskunft. ➤ **Ein Deckel bringt keinen nachgewiesenen Qualitätsgewinn.** Er ist **Kapitalschutz**, kein Signalfilter (Nutzerregel 01.10.).

### 8.3 Varianten — gebundener Einsatz bei 2,5 / 11 / 23 gleichzeitig offenen Positionen (Hebel-Liste)

| Variante | Einsatz je Handel | gebunden im Mittel · P95 · Maximum | Bemerkung |
|---|---|---|---|
| **A** wie gemessen | **1 %** des Kapitals (bei 24.700 € inkl. Cash ≈ 250 €) | ≈ 620 € · 2.700 € · 5.700 € | entspricht der REGEL0-Erfolgsmessung (2.700: auf der Liste ×1,14..×1,23, Rückgang 8 %) |
| **B** wie heute | fest **500 €** | ≈ 1.250 € · 5.500 € · 11.500 € | doppelte Größe, Gewinne und Rückgänge etwa doppelt. Ab P95 über dem Hebeltopf |
| **C** aus dem Hebeltopf | Topf 3.000 € / 11 (P95) ≈ **270 €** | ≈ 680 € · 3.000 € · 6.200 € | Der Topf reicht in 95 % der Stunden |

Der höchstmögliche Verlust je Handel ist bei der REGEL0 etwa der **Einsatz** (Liquidation) plus Gebühren.

### 8.4 Zur Entscheidung

| # | Frage |
|---|---|
| **G1** | **Kapitalbasis:** Hebeltopf (3.000 €), Gesamtvermögen inkl. Cash, oder ein fester Betrag? |
| **G2** | **Einsatz je Handel:** A, B oder C? |
| **G3** | **Wenn der Topf voll ist** (Ballung): Signal trotzdem mailen mit Vermerk *Topf voll* (keine Blockierung, wie 19.08. für die Töpfe entschieden), oder in Reihenfolge des Eintreffens nur bis zum Topf? |
| **G4** | Den alten **Gesamtdeckel** (3 % Risiko bis zum Stop) für die REGEL0 durch einen Deckel auf den **gebundenen Einsatz** ersetzen? |


### 8.5 ✔ Startfestlegung (E-44, Nutzer 02.10.)

Nicht final, sondern **Startwerte**, die im Betrieb nachgeschärft werden. Der Kapitalschutz liegt beim Nutzer.

| | Startwert | anpassen in |
|---|---|---|
| Positionswert je Trade | **1.500 €** (gleich groß im Markt) | `Basisinfos/regel0_betrieb.yaml` → `positionswert_eur` |
| Einsatz | Positionswert / Hebelstufe: **5x 300 € · 3x 500 € · 2x 750 €**, begrenzt auf **300–800 €** | `einsatz_min_eur`, `einsatz_max_eur` |
| gleichzeitig | **Richtwert 4**, keine Sperre, nur Vermerk in der Mail | `richtwert_gleichzeitig`, `sperre_ab_richtwert` |

**Gemessen zur Entscheidung (Hebel-Liste 2025–26, in Reihenfolge des Eintreffens):** Bei höchstens 4 gleichzeitig passen **59 %** der Signale. Die 41 % darüber hatten
**mehr** Vorteil je Handel (+0,91 % gegen +0,70 %). Bei 6 passen 75 %, bei 8 passen 85 %. Auf der Liste kamen nur die Stufen 3x und 5x vor. ⚠️ Die neuen Assets (HYPE, GRIFFAIN …) fehlen in dieser
Nachrechnung, mit ihnen werden die Ballungen etwas häufiger.

**Gebaut und geprüft:** `agent/regel0_groesse.py` (reine Rechnung) und `pruefe_pakete.py --paket Regel0Betrieb`, 8/8 grün. Geprüft wird das **Verhalten**: Die Rechnung folgt der Datei
(Wegwerfdatei mit anderen Werten), sperrt nicht ohne Sperre, und ein Tippfehler oder min über max **bricht ab**.

---

## 9. S7-1 — Der Nachlader (gebaut und geprüft 02.10.2026)

**Nutzer:** *„Ja, prüfen und gegenprüfen, dann Doku."*

**Was er tut:** `agent/regel0_nachlader.py` hält die vier Dateien der REGEL0-Datenbasis aktuell. Je Asset lädt er **ab der letzten gespeicherten Stunde** nach, holt diese
Stunde neu und überschreibt sie. Gespeichert werden **nur abgeschlossene Stunden**. Paare, die nicht mehr gehandelt werden, überspringt er, ihre Historie bleibt.
Die Abfragen laufen **parallel** (8 gleichzeitig), geschrieben wird nacheinander. Das Binance-Gewicht wird an den Antwortköpfen überwacht.
Symbole und Märkte kommen **aus den Dateien selbst**, nicht aus `terminmarkt_historie.db` (am Notebook nur Symbolliste).

| Datei | Quelle | Symbole |
|---|---|---|
| `stundenkurse.db` | Spot-Kerzen | aus der Datei (116) |
| `stundenkurse_alle.db` | Spot oder Futures je `_quelle` | 537 |
| `markpreis_historie.db` · `markpreis_alle.db` | Markpreis live (`markPriceKlines`), Paar und Faktor aus der letzten Zeile | 253 · 411 |

**Schutz:** Er schreibt nur in diese vier Dateien und verweigert jede andere, auch `tradinginfotool.db`. Bewacht wird das von `pruefe_pakete.py --paket Regel0Betrieb` (9/9).

**Gegenprüfung** auf Wegwerfkopien (Beleg `Datenbasis_01_10/gegenpruefung_nachlader.txt`): Für 6 Assets aus allen vier Dateien (BTC, 1000CAT, HYPE, CC, FLOKI, ASTER) wurden die
letzten 48 gespeicherten Stunden gelöscht und vom Nachlader neu geholt.

| | Ergebnis |
|---|---|
| Messbasis (Spot) | ✔ Stunde für Stunde gleich |
| **Markpreise, Monatsarchiv gegen Live-Schnittstelle** | ✔ **gleich**. Das in Abschnitt 5 genannte Risiko ist ausgeräumt |
| `stundenkurse_alle.db` | ✔ gleich bis auf die **letzte** Stunde, die beim Laden am 01.10. **noch offen** war. Nachgeprüft: das gilt bei **535 von 537** Assets. Der Nachlader ersetzt sie beim ersten Lauf durch die abgeschlossene |
| nur abgeschlossene Stunden gespeichert | ✔ |
| zweiter Lauf holt nichts doppelt | ✔ |
| Produktionsdatei verweigert | ✔ |

**Last** (Desktop, Wegwerfkopie):

| Lauf | Dauer | Arbeitsspeicher | Fehler |
|---|---|---|---|
| **erster Lauf** (holt etwa einen Monat nach, wie am Notebook) | 785 s (nacheinander) | 0,17 GB | 0 |
| normaler Stundenlauf, **nacheinander** | 766 s ⛔ zu langsam für den Stundentakt | 0,17 GB | 0 |
| normaler Stundenlauf, **parallel** | **59 s** | 0,17 GB | 0 |

Übersprungen, weil nicht mehr im Handel: 141 Markpreis-Reihen eingestellter Paare der Messbasis (erwartet) und 12 Futures, die Binance seither eingestellt hat.

➤ **Nächster Schritt S7-1b:** den Nachlader am Notebook als **Stundenjob** einhängen (etwa 5 Minuten nach jeder vollen Stunde). Danach am Notebook `git pull` und
Neustart. Die Kontrolle läuft über den Teilexport (die letzte Stunde je Datei rückt vor). Das ist eine Änderung am Betrieb und braucht dein Ja.

## 10. S7-1b — Der Stundenjob (gebaut und geprüft 02.10.2026)

**Nutzer:** *„Ja, prüfen, gegenprüfen und Doku."*

**Was gebaut ist:** `scheduler/background.py` → `regel0_nachlader_job`, eingehängt in `build_scheduler` als Job `regel0_nachlader`.

| | |
|---|---|
| **Takt** | jede Stunde um **:05 UTC** (Binance schließt die Kerze um :00; E-42 *Prüfzeitpunkt nach Kerzenschluss*) |
| **nach einem Neustart** | **sofort** (50 s nach dem Start, Index 10 der gestaffelten Sofortstarter), sonst fehlten bis :05 alle Stunden der Ausfallzeit |
| **ein Lauf zugleich** | dauert ein Lauf länger als eine Stunde (erster Lauf nach langem Ausfall), überspringt APScheduler den nächsten, **ohne Mail** |
| **Standby** | ein Lauf, der bis zu 30 min zu spät kommt, wird **einmal** nachgeholt (`coalesce`); der Nachlader setzt ohnehin an der letzten Stunde je Symbol an |
| **Fehlermail** | nur wenn der **ganze** Lauf scheitert (z. B. Binance nicht erreichbar), mit dem üblichen 60-min-Spamschutz. Fehler einzelner Symbole werden gezählt (`_nachlader`) und beim nächsten Lauf ohne Lücke nachgeholt |

**⚠️⚠️ Nur am Betriebsgerät.** Am Desktop liegen unter **denselben Namen die Messbasen**. Die ändern sich nur von Hand (`hole_*.py`), sonst ist keine Messung
reproduzierbar (R-R11). Der Helfer `regel0_nachlader.betrieb_erlaubt` erkennt das Gerät **am Datenzustand, nicht am Gerätenamen**: `terminmarkt_historie.db` trägt
die Marke `_nur_symbolliste`. Das ist laut CLAUDE.md der Sollzustand am Notebook, am Desktop ist die Datei voll. Außerdem müssen alle vier Dateien vorhanden sein.
**Im Zweifel nein.** Am Desktop ist das Ablehnen der Normalfall: eine Logzeile, keine Mail. Der Aufruf von Hand auf einer Kopie (`--ordner`) ist davon nicht betroffen.

**Gegenprüfung** (Wegwerfordner, `data/` nur lesend; Beleg `Datenbasis_01_10/gegenpruefung_stundenjob.txt`): **20 von 20 Punkten bestanden.**

| | Ergebnis |
|---|---|
| Desktop `data/` | ✔ verweigert (*volle Messbasis*) |
| Nachbau Notebook (Marke gesetzt, 6 Assets in allen vier Dateien) | ✔ erlaubt. Der **Job selbst** brachte alle vier Dateien bis zur letzten **abgeschlossenen** Stunde, in 5 s, ohne Fehlermail |
| Nachbau Desktop (volle `terminmarkt_historie.db`) | ✔ **kein Schreibzugriff**, die SHA-256 aller Dateien ist vor und nach dem Job gleich |
| fehlende `terminmarkt_historie.db` · eine der vier Dateien fehlt | ✔ verweigert |
| ganzer Lauf scheitert (Netz) · Nachlader verweigert (`SystemExit`) | ✔ Fehlermail, der Scheduler-Faden läuft weiter |
| Einhängen | ✔ aus dem Quelltext gelesen: cron, Minute 5, UTC, Sofortstart. Mit echtem APScheduler 3.11 angelegt: `cron[minute='5']`, coalesce, max 1, grace 1800 |

**Wache:** `pruefe_pakete.py --paket Regel0Betrieb` hat jetzt 11 Prüfungen. Neu ist erstens, dass der Desktop-Zustand **nicht beschrieben** wird. Das ist am Seiteneffekt
nachgewiesen: Der Nachlader wird dort gar nicht erst aufgerufen. Die **Gegenprobe** mit entfernter Sperre wird rot (2 Aufrufe statt 1). Neu ist zweitens, dass der Job
eingehängt ist.

**Kontrolle am Notebook:** Der Teilexport (`nb_teilexport_betriebsdaten.py`) hat einen neuen Abschnitt **REGEL0-DATENBASIS**. Er zeigt, ob der Job schreiben darf und
warum. Je Datei zeigt er den Stand, wie viele Symbole ihn erreichen, und die letzten drei Läufe.

⚠️ **Die Frische überwacht noch niemand außer dem Teilexport.** Das ist Absicht: Heute **liest** im Betrieb noch niemand diese Dateien. Die Prüfung gehört an den
**Leser**, also an S7-2. Die Betriebsrechnung muss vor jeder Bewertung das Alter der letzten Stunde prüfen und bei veralteten Daten **kein** Signal geben, sondern melden.
Das wird dort gebaut und hier nicht vergessen (Plan, Schritt 7, S7-2).

**Erwartung am Notebook:** Der erste Lauf holt bei den Markpreisen ab dem 31.08. nach, bei der Messbasis ab dem 24.09. Am Desktop dauerte das 13 min. Am Notebook
rechne ich mit **15–30 min**, weil die Abfragen vom Netz abhängen, nicht von der Rechenleistung. Danach braucht ein Stundenlauf etwa 1–4 min. Die Binance-Last teilt
er sich mit `betriebsreihen` und `terminmarkt`; die Bremse hält ihn unter 70 % des Minutengewichts.

**Am Notebook zu tun:**
1. `git pull`
2. App neu starten
3. nach etwa 1–2 Stunden: `python nb_teilexport_betriebsdaten.py`. Im Abschnitt REGEL0-DATENBASIS muss *schreibt* stehen, der Stand muss bei der letzten vollen
   Stunde liegen, und es muss mindestens zwei Läufe ohne Fehler geben.


## 11. ⭐ ALLES, WAS IN SCHRITT 7 NOCH OFFEN IST — Stand 02.10.2026, nach dem NB-Pull von 6cfd240

**Nutzer:** *„Schreibe alles, was noch offen ist, in die zentralen Dokumente und den Plan."* Diese Liste ist der **Zustand**. Erledigtes wird hier abgehakt,
nicht gelöscht.

### A. Betriebskontrolle jetzt (nach dem Pull 02.10., App neu gestartet)

| # | Kontrolle | wann | bestanden, wenn |
|---|---|---|---|
| **K-S7-1** | Teilexport `python nb_teilexport_betriebsdaten.py` | 1–2 h nach dem Start | Abschnitt REGEL0-DATENBASIS: *schreibt*; Stand je Datei = letzte volle Stunde (UTC); mindestens 2 Läufe mit Fehler 0; „nicht im Handel" bei den Markpreisen etwa 141 und 12 (erwartet) |
| **K-S7-2** | **NB-Export** `extract_notebook_diagnose.py` (schlank, **nicht** `--voll`). Stehende Regel: jede Änderung mit Laufzeitcode wird im Betrieb auf Fehler geprüft | **nach** dem ersten Lauf (Logzeile `REGEL0-Nachlader: fertig in …`), etwa 45–60 min nach dem Start. Nicht während des ersten Laufs, weil der Upload sonst mit dem Nachholen um die Leitung konkurriert | kein ERROR/Traceback aus `regel0_nachlader` oder `background`; keine Mail *Job 'regel0_nachlader' fehlgeschlagen*; die anderen Binance-Jobs (`terminmarkt`, `hebel_screening`, `betriebsreihen`) **ohne neue** Zeitüberschreitungen oder Jobfehler während des Nachholens; ein einzelnes *maximum number of running instances* ist zulässig |

### B. Die Bauschritte von Schritt 7 (je mit Voranalyse und Nutzer-Ja)

| # | Inhalt | offen dabei |
|---|---|---|
| ✔ S7-1 | Nachlader | — |
| ✔ S7-1b | Stundenjob | Kontrolle K-S7-1/K-S7-2 |
| ➤ **S7-2** | **Betriebsrechnung** `regel0_betrieb`: Normal, rsi, v̂, Ersteintritt mit Ruhe 48 h, J (240 h), Hebelstufe aus dem ATR-Modell (P(liq) ≤ 2 %). Training auf den **116** der Messbasis (Grundgesamtheit), bewertet werden auch die übrigen (`--zusatz`, *bewertet, nicht trainiert*) | **R-R11:** zeilengleich zu `kern48jbz_einstiege_bestand.csv`, dieselbe Hebelstufe je Handel. ⚠️⚠️ **Frischeprüfung am Leser:** Ist die letzte Stunde veraltet, kommt **kein** Signal, sondern eine Meldung (heute überwacht nur der Teilexport die Frische) |
| S7-3 | Monatstraining als Job (rsi- und ATR-Modell speichern) | dieselben Parameter wie die Messung; die Abweichung durch numpy 2.5.1 ausweisen, Maßstab sind gleiche **Signale** |
| S7-4 | **Einhängen in die Rollen-Kette** (F1/F2): den alten Hebelvorschlag **abschalten** (kein Parallelbetrieb); LLM-Rollen prüfen und kommentieren nur | Mailblock: Einstieg, Hebelstufe **gedeckelt auf das Bitpanda-Angebot** (⚠️ **Quelle der Bitpanda-Stufen je Asset klären**), Einsatz aus `regel0_betrieb.yaml`, **Ausstiegszeit** plus **Erinnerung nach 24 h** (E-43), Richtwert-Vermerk, Vermerke *Kurs aus Futures*, *gesperrt*, *BTC nicht nachgewiesen*, **Regelversion** (E-43). Prüfstand mit echter `config.yaml`, Mail per diff, LONG **und** SHORT |
| S7-5 | täglicher Abgleich: Bitpanda-Katalog und Zuordnung (`pruefe_bitpanda_katalog.py`, `pruefe_symbol_zuordnung.py`), Meldung bei Sperre oder neuer Ausnahme | ⚠️⚠️ **LÜCKE (gefunden 02.10.):** E-40 heißt *alles, was Binance stündlich führt*. Der Nachlader führt aber nur fort, was **schon** in den Dateien steht. **Neu gelistete Binance-Paare kommen nicht dazu.** S7-5 muss sie am Notebook aufnehmen: Historie ab dem Listing, `_quelle`, Markpreis. Nie in die Messbasis `stundenkurse.db` (Grundgesamtheit). Gegenprobe: eine absichtlich falsche Zuordnung muss gemeldet werden |
| S7-6 | R-R11 **am Notebook**: die Signale einer vergangenen Woche nachrechnen, als Kopie gegen den Desktop halten | zeilengleich |
| S7-7 | **Mindestbedingungen** (O7, F4: sofortiger Ersatz, eine Woche testen und optimieren, dazu Simulationen zu Stabilität und Funktion), dann **Schritt 8 Umstellung** | mit dem Nutzer festlegen, bevor S7-7 beginnt |

### C. Fachlich offen, nach der Umstellung (im Plan unter Offene Punkte)

O12 Lernmenge per Regel · O13 Fortsetzung und Positionsführung **echter** Positionen, dazu der Importer-Fehler (2.679) · O14 Spot-Kette anpassen oder stilllegen
(nicht sofort) · R Regime-Kontext mit O10 · Käuferanteil auf dem Kern · Liquidität als **Gewicht** (2.704) · O9 Messmenge nach Größenklassen (später) · Assets ohne
Binance-Daten (AIOZ, SUPRA, VSN, XDC; Aktien und ETFs sind nicht Teil der REGEL0)

### D. Nebenbefunde und Altlasten — nicht vergessen

| | |
|---|---|
| **Mail-Schalter** | `benachrichtigung.aktiv` gegen `benachrichtigung.email.aktiv`: als eigene Aufgabe vorgeschlagen, nicht erledigt |
| alte NB-Kontrollen | ✔ **keine offen** — die Liste ist seit 23.09. leer (K5, K14 bestätigt, K6 nie fällig, K11a am Prüfstand belegt, K13 erledigt). ⚠️ Der Memory-Index nannte sie noch als offen und wurde hier zuerst ungeprüft übernommen (korrigiert 02.10.) |
| ⛔ **Alarmmails kommen nie an** (gefunden im NB-Export 02.10.) | `_melde_laufzeitluecke` (Stillstand) und `_melde_datenausfall` (*alle Kurse veraltet*) holen den Empfänger über `config.get_config()`. Die Funktion **gibt es nicht** (nur `load_config`), also ist der Empfänger `None`. Und selbst mit ihr wäre es das ganze `email`-Bündel statt `email.empfaenger`. Am NB um 07:29 belegt: Stillstand 2,1 h, Mail *fehlgeschlagen* (`'NoneType' object has no attribute 'strip'`). Beide melden trotzdem *gesendet* (Rückgabewert nicht geprüft). Besteht seit f92205f (20.09.); K25 *beim nächsten echten Ausfall muss eine Mail kommen* war damit nie erfüllt. ✔ **REPARIERT 02.10.** (Nutzer: *Ja, Reparatur durchführen*): beide über den bestehenden Helfer `_sende_hinweismail` (Schlüssel `email.empfaenger`, Schalter `email.aktiv`, *gesendet* nur bei echtem Versand; die Sperrfrist der Datenausfallmail beginnt nur nach echtem Versand). Wache `--paket Alarmmail` 4/4 am Seiteneffekt (was kommt beim Versand als Empfänger an?), Gegenprobe gegen die alte Fassung **4/4 rot** (Empfänger `None`, Rückgabe *gesendet*). Die übrigen 20 Mailstellen lesen den Empfänger richtig. Der Stillstand 02.10. 05:24–07:29 war ein **geplanter** Halt (Nutzer: *App beendet und verzögert gestartet*), die Mail wäre richtig gewesen. ➤ Kontrolle K-ALARM nach dem Pull |
| Grundgesamtheit `schnitt` am NB | 398 statt 517 Symbole, **vor** einer Freischaltung von `schnitt` zu entscheiden (CLAUDE.md) |
| CLAUDE.md | wird nicht über git verteilt; ans Notebook nur über den Drive-Abgleich, wenn der Nutzer will |
| Suite | 4 bekannte rote Zeilen (Datenstand am Desktop) |

### Ergebnis der Kontrollen am Notebook (02.10.2026, Teilexport 12:38, NB-Export 12:42, Neustart 11:33)

| # | Ergebnis |
|---|---|
| ✔ **K-S7-1** | *schreibt* (Betriebsgerät erkannt). Stand aller vier Dateien 09:00 UTC = letzte abgeschlossene Stunde zum Zeitpunkt 10:38 UTC. 116/116 · 537/537 · 112/253 · 399/411 Symbole auf Stand, der Rest sind genau die 141 und 12 nicht mehr gehandelten Paare. 2 Läufe, 0 Fehler |
| ✔ **K-S7-2** | seit dem Neustart **0 Tracebacks, 0 ERROR-Zeilen** (die 22 Tracebacks im 72-h-Fenster liegen alle davor). Erster Lauf **186 s** (am Desktop 785 s nacheinander), Stundenlauf **101 s**, 0 Symbolfehler. Keine Jobfehlermail. Terminmarkt auch während des Nachholens 40 von 44 (wie vorher; ohne Börse SUPRA, CANTON, VSN, XNO). Warnungen dieselben Muster und Häufigkeiten wie gestern im selben Fenster |
| Hinweis | neu seit heute: Bitpanda-Bestand **Concrete (CT)** ohne Watchlist-Eintrag (Mail 11:34). Eine Bestandsfrage beim Nutzer, kein Fehler |
| ⛔ Nebenbefund | Stillstandsmail 07:29 nicht zugestellt — siehe Abschnitt D, *Alarmmails kommen nie an* |

➤ **S7-1/S7-1b sind im Betrieb bestätigt.** Die REGEL0-Datenbasis läuft am Notebook stündlich und ohne Desktop-Handgriff (E-35).

### Kontrolle nach dem Pull der Alarmmail-Reparatur

| # | Kontrolle | bestanden, wenn |
|---|---|---|
| **K-ALARM-1** | nächster NB-Export nach Pull und Neustart | keine Zeile *Stillstandsmail NICHT zugestellt* / *Datenausfall-Meldung NICHT zugestellt*, keine neue *E-Mail-Benachrichtigung fehlgeschlagen* |
| **K-ALARM-2** | der nächste Halt über 45 min (geplant oder nicht) | die Mail *… STUNDEN STILLSTAND - die Anwendung war weg* kommt an. Wer es sofort wissen will: die App einmal **länger als 45 min** beendet lassen |


---

## 12. VORANALYSE S7-2 — die Betriebsrechnung (02.10.2026, zur Abstimmung)

**Ziel:** Am Notebook entstehen stündlich **dieselben** REGEL0-Einstiege und Hebelstufen wie in der Messung. Nur dann gilt der gemessene Beitrag für das,
was läuft (E-31, E-35).

**Stand:** Die Datenbasis läuft am NB (S7-1/S7-1b bestätigt). Gerechnet wird dort noch nichts.

**Test oder Betrieb:** Gebaut und geprüft wird am Desktop gegen die Messbelege (R-R11). Erst danach kommt der Betrieb (S7-4).

### 12.1 Ist-Stand: wie die Messung rechnet (am Code nachgesehen)

| Schritt | wo | was |
|---|---|---|
| Menge | `messe_e2_beitraege.py:123-172`, `:176-202` | *bestand* = `stundenkurse.db`, Symbole mit mehr als 2.000 Zeilen (116 mit BTC), **sortiert nach Zeilenzahl**. Mit `--zusatz` kommen die Assets aus deinen Listen (Watchlist, Bestand, Hebel-Liste) dazu, die nicht in der Messbasis liegen, aus `stundenkurse_alle.db`. Sie werden **bewertet, nicht trainiert**. *unverzerrt:1–3* zieht 100 von 305 eingestellten Paaren aus **`data/eingestellt_historie.db`** (950 MB, **nur am Desktop**) |
| Anker | `messe_e2_beitraege.py:356-372` | eine Stunde zählt nur mit **240 h lückenlosem Vorlauf und 72 h lückenloser Zukunft** |
| Merkmale | `messe_e2_beitraege.py:233-264` | rsi über **14 Zeilen** (einfache Summe, nicht Wilder), ATR über **24 Zeilen** von (H−T)/C × √24 |
| rsi_s, rsi_s24 | `messe_losfahren.py:166-195` | rsi minus Median der letzten 720 h (mindestens 240 Werte), dazu derselbe Wert 24 h früher |
| eigenes Normal | `messe_losfahren.py:122-138` | Mittel der Ausgänge q5 im Fenster [t−1 Jahr, t−24 h]. Reif nach 12 Monaten; mit J (`--junge`) ab 240 h |
| Schrumpfung (QSh) | `messe_losfahren.py:368-393` | Marktmitte, tau2 und Schrumpfungsfaktor je Asset **je Monat**, aus den Gitterstunden (0/6/12/18 UTC) der reifen Messbasis |
| Monatsmodell | `messe_losfahren.py:401-415`, `messe_k1_schritt2b_kombination.py:109-212` | Kurvenmodell Form b (12 Stufen) auf rsi_s und rsi_s24. Training ab 2023-01 bis Monatsbeginn −24 h, nur Stunden mit Treffer. Dämpfung per Kreuzvalidierung über 4 Zeitblöcke, Raster GITTER_NEU. Rechnet mit `scipy` (L-BFGS-B, sparse) |
| Einstieg | `messe_losfahren.py:421-455` | Bedingungen: (1) v̂ = expit(logit(QSh) + Beitrag) − QSh ≥ +0,035; (2) in den 48 h davor keine Stunde darüber und mindestens 40 gültige; (3) nicht in den ersten 24 h eines Monats. **Einstieg eine Stunde später** |
| Einstiegspreis | `messe_e2_beitraege.py:265-300` | **Schlusskurs** der Einstiegsstunde |
| Hebelstufe | `messe_k6_hebelstufe.py:81-89`, `:238-290`, `:555-570`, `:673-677` | ATR-Modell **je Quartal** neu (Form b, Standard-Dämpfung), Ziel *erste Liquidation binnen H* am **Markpreis** (gesperrte Monate ausgelassen), Marge 0,09. Gewählt wird die höchste Stufe von 2/3/5 mit P(Liquidation in 24 h) ≤ 2 % |
| Belege | `data/_vergleich/` | `kern48jbz_einstiege_bestand.csv`: **10.732 Einstiege, 127 Assets** (116 plus 11 aus deinen Listen), 2024–2026. `kern48jb_*` ist eine echte Teilmenge davon (die 116 sind bitgleich). ⚠️ Die **Hebelstufe je Handel steht in keiner Datei**: `b0_spur_bestand.csv` hat nur 2025–26 und keine Zusatz-Assets |

### 12.2 ⚠️ Wo Messung und Betrieb auseinanderlaufen — acht Befunde

| # | Befund | Folge für den Betrieb |
|---|---|---|
| **B-1** ⛔ | **Die Schrumpfung greift innerhalb des Monats vor.** Marktmitte, tau2 und der Mittelwert je Asset kommen aus **allen** Gitterstunden des laufenden Monats (`messe_losfahren.py:369-393`). Eine Stunde am 10. nutzt also Werte vom 11. bis zum 31. Im Betrieb kennt man nur die Stunden bis jetzt | **So nicht zeilengleich nachbaubar.** Die Wirkung ist zu **messen**, nicht anzunehmen. Weil das Normal über ein Jahr läuft und sich langsam ändert, erwarte ich eine kleine Wirkung. Das ist eine Vermutung, kein Befund ➤ **Teil 0** |
| **B-2** | **Grundgesamtheit des Trainings.** Am NB liegen die 116 der Messbasis. *unverzerrt* braucht `eingestellt_historie.db` und ist eine **Zufallsziehung**, also keine Betriebsform | Betrieb = **bestand**: Training auf den 116, bewertet werden dazu BTC und deine Listen. Referenz ist `kern48jbz_einstiege_bestand.csv`. Eine andere Lernmenge entscheidet **O12**, und dann ziehen beide Seiten nach |
| **B-3** | **Die Ankermaske verlangt 72 h Zukunft.** Live hat keine Stunde eine Zukunft | Die Betriebsrechnung nimmt **jede lückenlose abgeschlossene Stunde**. Rückwirkend sind das dieselben Stunden wie in der Messung; Abweichungen gibt es nur an Datenlücken. Sie werden **ausgewiesen** |
| **B-4** | **Reihenfolge der Symbole** nach Zeilenzahl. Am NB wachsen die Dateien stündlich, die Reihenfolge kann kippen | feste Reihenfolge (alphabetisch). Die Modellparameter können sich dadurch an späten Nachkommastellen verschieben. Die Toleranz wird vorab festgelegt (12.4) |
| **B-5** | **Die Referenz für die Hebelstufe je Handel fehlt** | einmal am Desktop erzeugen: `messe_k6_hebelstufe.py … --zusatz --spur-regel0 <csv> --spur-alle`, nur lesend, rund 15 min |
| **B-6** | **Die Messung endet 2026-08.** Monats- und ATR-Modell gibt es nur bis August, die Monatsanfänge im Code nur bis 2027 | Ohne Monatstraining gibt es im Oktober kein Signal ➤ **S7-2 und S7-3 gehören zusammen**: ein Rechenkern mit Training und Bewertung |
| **B-7** | **Geometrie.** Signal zur Stunde s, bekannt ab s+1:00. Einstieg in der Messung zum **Schluss von s+1**, also um s+2:00 UTC. Die Mail kommt etwa um s+1:10 | Die Mail nennt den **Messeinstieg** (Uhrzeit und Schlusskurs) und den **Ausstieg 24 h danach**. Wer früher einsteigt, handelt eine **andere** Geometrie als gemessen (*Messgeometrie ist nicht Betrieb*) |
| **B-8** | **Frische.** Fehlt einem Asset die letzte Stunde, rechnet die Messung dort gar nicht | **kein Signal**, wenn die letzte abgeschlossene Stunde fehlt. Fehlt sie bei vielen Assets, kommt eine **Meldung**, kein stilles Nichts |

### 12.3 TEIL 0 — die Wirkung von B-1 messen, vor dem Bau und vorab festgelegt

| | |
|---|---|
| **Frage** | Wie viel von der REGEL0 hängt am Vorgriff innerhalb des Monats? |
| **kausale Fassung K** | Marktmitte, tau2 und Schrumpfungsfaktor je Asset kommen aus dem **Vormonat** und werden mit dem Monatstraining einmal berechnet. Ein Asset ohne Vormonat (jung oder neu) nimmt seine Gitterstunden des laufenden Monats **bis zur Stunde t** |
| **Messung** | `messe_losfahren.py` bekommt den Schalter `--normal kausal`. Ohne Schalter bleibt das Ergebnis **bitgleich**, das wird geprüft. Dann laufen Einstiege und Simulation in allen **4 Mengen**, dazu die Signalbilanz je Asset für deine Listen aus dem NB-Teilexport. Etwa 1–1,5 h am Desktop |
| **Regel, vorab** | ✔ **K wird REGEL0.1** (neue Version nach E-43, Referenz für den Betrieb), wenn in mindestens 3 von 4 Mengen gilt: (1) die Einstiege sind zu **≥ 95 %** gleich, und (2) der Rohvorteil je Handel ändert sich um **≤ 0,05 Prozentpunkte**. ⛔ Sonst wird das Ergebnis **vorgelegt**. Dann hat der Vorgriff zum gemessenen Ergebnis **beigetragen**, und die REGEL0-Zahlen gelten nur mit Vorbehalt |
| **Pflichten** | Nullwelt, je Jahr, mit und ohne 10./11.10.2025, Spiegel (E-29), **Signalbilanz je Asset** vorher und nachher |

### 12.4 Bau nach Teil 0: der Rechenkern `agent/regel0_rechnung.py` (S7-2 zusammen mit S7-3)

| Teil | Inhalt |
|---|---|
| **Daten** | nur lesend (`mode=ro`) aus den vier REGEL0-Dateien, nie aus der Produktion |
| **Monatsjob** (S7-3) | am 1. jedes Monats: rsi-Modell wie 12.1, Schrumpfung nach K, zu jedem Quartalsbeginn zusätzlich das ATR-Modell. Abgelegt als **Modelldatei je Monat** (`data/regel0_modell_<JJJJ-MM>`), mit Prüfsumme und Regelversion |
| **Stundenlauf** (S7-2) | nach dem Nachlader, für jedes Asset: Merkmale, Normal und v̂, dann Ersteintritt mit Ruhe 48 h, Hebelstufe aus dem ATR-Modell am Markpreis und die Frischeprüfung B-8. Ergebnis je Signal: Asset, Signalstunde, **Messeinstieg (Uhrzeit, Kurs)**, Ausstieg 24 h später, v̂, Stufe, P(Liquidation), Vermerke (*Kurs aus Futures*, *nicht trainiert*, *BTC nicht nachgewiesen*) |
| **Nachrechnungsmodus** | derselbe Code rückwirkend über 2024-01 bis 2026-08, für R-R11 |
| **R-R11-1** | Einstiege **zeilengleich** zur Referenz, erst in der Fassung *wie Messung*, dann in K. Gegenprobe: mit Schwelle 0,034 **muss** die Prüfung abweichen |
| **R-R11-2** | Hebelstufe je Handel gleich der Referenz aus B-5 |
| **R-R11-3** | Abweichung der Modellparameter ausgewiesen (Reihenfolge B-4, später die numpy-Version am NB). Maßstab sind gleiche **Signale** |
| **Last** | am Desktop gemessen und hochgerechnet (Faktor 3,5), danach am NB bestätigt |
| **Wache** | `--paket Regel0Betrieb` prüft: Der Rechenkern liest nur. Die Frischeprüfung greift (eine veraltete Wegwerfdatei ergibt kein Signal). Die Nachrechnung stimmt mit dem Beleg |

⚠️ Bis dahin geht **nichts** an die Mail oder in die Produktion. Das ist erst S7-4.

### 12.5 Zur Abstimmung

| # | Frage | Vorschlag |
|---|---|---|
| **F-a** | Teil 0 wie in 12.3 festgelegt messen? | ➤ **Ja**. Ohne die Messung wäre die Betriebsform eine Annahme |
| **F-b** | Grundgesamtheit im Betrieb = **bestand** (Training auf den 116, bewertet werden BTC und deine Listen), bis O12 entscheidet? | ➤ **Ja**. Die Daten liegen am NB, die Referenz gibt es, und eine Zufallsziehung ist keine Betriebsform |
| **F-c** | S7-2 und S7-3 als **einen** Rechenkern bauen? | ➤ **Ja** (B-6) |
| **F-d** | **Für welche Assets** sollen Signale kommen? Die Messung bewertet die 116 der Messbasis **und** deine Listen. Der heutige Betrieb prüft den Hebel nur bei eingeschaltetem Hebel-Schalter (`asset_hebel_settings`, heute 25) | ➤ **Signal nur bei eingeschaltetem Hebel-Schalter.** Bewertet werden alle mit Daten (Auskunft, z. B. für die Signalbilanz). So bleibt die Auswahl bei dir. **Gemessen** auf der Referenz: Die 25 der Hebel-Liste (24 mit Daten, XDC fehlt) hatten 2025 **2,4** und 2026 **2,8** Einstiege am Tag. Alle 127 hätten **13–15** am Tag. Wie viele davon nach der Hebelstufe handelbar sind, zeigt erst B-5 |

### 12.6 Abstimmung (Nutzer 02.10.2026, E-45)

✔ **F-a bis F-d wie vorgeschlagen.** Signalkreis = Hebel-Schalter an: laut NB-Export 02.10. 12:42 sind es **25 von 44** (Opt-in, ohne Eintrag = aus).
Einstiege und Signalanzahl werden ein **eigener, längerer Punkt (O18)**.
⚠️ **Nebenbefund dabei:** `_migrate_hebel_schalter_geradeziehen` (`database/db.py:1643`) läuft bei **jedem** Start und setzt Krypto-Assets der Watchlist **ohne**
Eintrag auf *an*. Den Eintrag schreibt nur der Schalter der Oberfläche (`ui/app.py:982`). Ein neu aufgenommenes Asset wird beim nächsten Neustart also still
eingeschaltet, gegen das Opt-in vom 15.08. Drei Leser nehmen ohne Eintrag ebenfalls *an* an (`db.py:2062`, `:3877`, `:5279`). → O18, spätestens mit S7-4.

### 12.7 ERGEBNIS TEIL 0 (02.10.2026, Befund 2.708) — ✔ bestanden, Fassung 0.1 gilt

| Menge | Ergebnis |
|---|---|
| bestand · unverzerrt:1 · unverzerrt:2 | Einstiege **bitgleich**, also auch Konto und Rohvorteil |
| unverzerrt:3 | **98,7 %** gleich. Alle 161 Abweichungen liegen im **Januar 2026**. Rohvorteil +0,350 % gegen +0,345 % (+0,005 Pp), Nullwelt ✔ |
| **Betriebsreferenz** `kern48jbz` (127 Assets) | **bitgleich**. Die Signalbilanz je Asset ist unverändert |
| Gegenprobe | **ohne** Schalter bitgleich zur Referenz; der Zweig wirkt nachweislich (|ΔQSh| bis 0,079) |

➤ Nach der vorab festgelegten Regel sind **4 von 4** Mengen erfüllt: **REGEL0.1 gilt.** Der Rechenkern rechnet die kausale Fassung, und R-R11 wird
**zeilengleich** gegen `kern48jbz_einstiege_bestand.csv` geprüft (= `kern48jbzk_…`).

⭐ **Für den Bau vereinfacht sich B-1:** τ² ist in 31 von 33 Monaten null. Die Schrumpfung braucht im Betrieb also im Wesentlichen die **Marktmitte des Vormonats**,
die einmal im Monat mit dem Training berechnet wird. Beleg: `Basisinfos/Teil0_02_10/`.

**Nächster Schritt:** B-5, die Referenz der Hebelstufe je Handel erzeugen. Danach der Bau des Rechenkerns (12.4).

---

## 13. DER RECHENKERN — gebaut und geprüft (02.10.2026, S7-2 mit S7-3; Nutzer: *„Ja, B-5 und Rechenkern, prüfen und gegenprüfen"*)

**Was gebaut ist:** `agent/regel0_rechnung.py`. Er rechnet die **REGEL0.1** und nimmt die Rechenbausteine **direkt aus den Messmodulen**
(`E2._rsi14`, `E2.ergebnisse`, `E2._atr`, `K2.Modell`/`K2.fit_cv`, `liq_schwelle`). Gleichheit ist damit eingebaut, nicht nachgebaut.
Er liest nur (`mode=ro`), schreibt nichts in die Produktion und fragt kein Netz ab.

| Teil | Funktion |
|---|---|
| Daten | `lade_reihen` (Messbasis + Zusatz-Assets, optional ab einer Stunde), `betriebs_zusatz` (alle aus `stundenkurse_alle.db`, ohne die gesperrten: 519) |
| Einstieg | `anker` (Ankermaske wie die Messung; im Betrieb ohne Zukunft), `rechne` (Normal mit J, Schrumpfung kausal, Monatsmodell, Ersteintritt mit Ruhe 48 h) |
| Hebelstufe | `hebel_anker`, `hebel_modelle` (je Quartal, im Betrieb nur abgeschlossene 120-h-Fenster, B-10), `hebelstufe` (höchste Stufe mit P ≤ 2 %; **ohne ATR keine Stufe**) |
| Monatsjob (S7-3) | `trainiere_monat` → Paket mit rsi-Modell des Monats und des Vormonats, ATR-Modellen des Quartals, erstem Anker je Asset; `speichere_paket`/`lade_paket` mit **Prüfsumme und Regelversion** |
| Stundenlauf (S7-2) | `bewerte`: 460-Tage-Fenster, bewertet die jüngste abgeschlossene Stunde. *Neu*: Signale mit **vorläufiger** Stufe (ATR der Signalstunde). *Endgültig* eine Stunde später mit der Stufe aus der ATR der Einstiegsstunde. Dazu die **Frische** je Asset |

**Gegenprüfung** (Belege `Basisinfos/Rechenkern_02_10/`):

| # | Prüfung | Ergebnis |
|---|---|---|
| B-5 | Referenz der Hebelstufe je Einstieg (`--spur-stufen`) | ✔ Kennzahlen gleich dem 01.10. (7.922 Handel, Konto +0,2524, Rohvorteil +0,570 %), 10.222 Stufen: 3x 7.634 · 5x 2.523 · 2x 25 · keine 40 |
| R-R11-1 | Einstiege der Nachrechnung 2024-01 bis 2026-08 | ✔ **zeilengleich** zur Betriebsreferenz (10.732, 127 Assets) · Gegenprobe Schwelle 0,034: 2.939 abweichend |
| Live | 20 vergangene Zeitpunkte, nur Kerzen bis T−1, Ankermaske ohne Zukunft | ✔ **20 von 20** Signale gleich, v̂ zur jüngsten Stunde **0,0** Abweichung (2.231 Werte) |
| R-R11-2 | Hebelstufe je Einstieg | ✔ P(Liquidation) bis 5·10⁻¹³ gleich, **alle 10.222 Stufen zeilengleich** · Gegenprobe Grenze 0,019: 155 anders |
| B-10 | Training des ATR-Modells wie im Betrieb (nur abgeschlossene 120-h-Fenster) | ✔ **99,84 %** gleiche Stufen (17 von 10.732), vorab ≥ 99 % |
| Monatsjob | Pakete 2026-03 und 2026-04 (Quartalsbeginn) nur aus den Daten zum Monatsbeginn, alle 650 Assets | ✔ rsi-Modelle **exakt** gleich der Nachrechnung, ATR-Modelle exakt gleich der Betriebsform · verändertes Byte wird erkannt |
| Stundenlauf | 7 Zeitpunkte, davon Monats- und Quartalsgrenze, alle Assets | ✔ neue Signale 7/7, endgültige Stufe 7/7, v̂ 0,0 Abweichung |
| Frische | einem Signal-Asset fehlt die jüngste Stunde | ✔ kein Signal, steht unter *veraltet* |
| Wache | `--paket Regel0Betrieb` 15/15: liest nur, Modelldatei geschützt, ohne ATR keine Stufe, **R-R11-1 zeilengleich** (nur mit voller Messbasis, am NB übersprungen) | ✔ |

⚠️ **Zwei eigene Fehler beim Bauen, beide durch die Gegenprüfung gefunden:** (1) In `bewerte` hätte an der Monatsgrenze das rsi-Modell des falschen Monats gegriffen.
Behoben: Das rsi-Modell kommt aus dem Monat der Signalstunde, das ATR-Modell aus dem Quartal der Einstiegsstunde. (2) `atr_je_stunde` übersprang die
gekürzte Reihe des Stundenlaufs (Mindestlänge 500). Die fehlende ATR ordnete das Modell **still** einer Klasse zu (NEO 3x statt 5x). Behoben, und
`hebelstufe` gibt ohne ATR jetzt ausdrücklich **keine** Stufe. Die Wache prüft das.

**Last** (Desktop): Stundenlauf über alle rund 650 Assets **124 s**, am NB also rund **7 min**. Dazu kommen der Nachlader mit etwa 1,5 min und der Monatsjob mit etwa 4,5 min am Desktop (NB rund 15 min, einmal im Monat).

**B-9 gemessen** (Auskunft für S7-4, `b9_vorstufe.txt`): Die vorläufige Stufe (ATR der Signalstunde) gleicht der endgültigen in **98,37 %** der Einstiege.
88-mal ist sie **höher** (fast immer 5x statt 3x), 87-mal tiefer. ➤ **Für S7-4 zu entscheiden:** Was nennt die Mail, wenn sie sofort kommt?

**Was NICHT gebaut ist:** das Einhängen am Notebook (Monatsjob und Stundenlauf als Jobs, Ablage der Signale) und die Mail. Das ist eine **Betriebsänderung**
und braucht dein Ja (**S7-2b**). Danach kommt S7-4.

---

## 14. S7-2b — der Rechenkern im Betrieb eingehängt (02.10.2026; Nutzer: *„Ja, S7-2b so vorbereiten, prüfen und gegenprüfen, aber ich möchte sehr rasch in Produktion damit, am besten sofort"*)

**Was gebaut ist:**

| Teil | |
|---|---|
| `agent/regel0_stundenlauf.py` | der Betriebslauf als **eigener Prozess** (`python -m agent.regel0_stundenlauf --betrieb`). Ablauf: (1) Fehlen die Monatspakete, die der Lauf braucht, werden sie trainiert (`data/regel0_modelle/`, Prüfsumme und Regelversion). (2) Bewerten. (3) Ablegen in **`data/regel0_signale.db`**: ein neues Signal mit der **vorläufigen** Stufe, eine Stunde später mit der **endgültigen**. Dazu der **Hebel-Schalter** des Assets, aus der Produktion **nur gelesen**, und je Lauf die Frische |
| `scheduler/background.py` | der Stundenjob `regel0_nachlader` startet den Betriebslauf **nach** dem Nachladen, mit 50 min Zeitgrenze. Seine Ergebniszeile `REGEL0-ERGEBNIS {...}` kommt ins Log. Rückgabe ≠ 0, Zeitgrenze oder veraltete Datenbasis (> 10 % der aktiven Assets ohne die jüngste Stunde) → **Fehlermail** |
| Rechenkern | bleibt **rein lesend**. Er lädt jetzt **je Asset** (`lade_reihen_iter`): Die Rohzeilen aller Assets auf einmal kosteten **1,5 GB** |
| Teilexport | Abschnitt **REGEL0-RECHNUNG**: Modelldateien mit Prüfsumme, letzte Läufe, Signale mit Stufen und Schalter |
| Wache | `--paket Regel0Betrieb` **19/19**: Der Stundenjob startet den eigenen Prozess mit Zeitgrenze, die Ablage legt genau `regel0_signale.db` an, an der Monatsgrenze werden beide Pakete verlangt |

⚠️ **Nicht in der Mail, nicht in der Produktion.** Die Signale liegen in der eigenen Ablage. In die Mail kommen sie mit **S7-4**.

**Gegenprüfung** (Wegwerfordner, Daten nur gelesen; Belege `Basisinfos/Rechenkern_02_10/pruefung_stundenlauf.txt`, `pruefung_betrieb.txt`):

| | Ergebnis |
|---|---|
| fehlendes Monatspaket wird im Lauf trainiert und mit Prüfsumme abgelegt, beim zweiten Lauf nicht neu | ✔ |
| neue Signale = Referenz-Einstiege, vorläufige Stufe gesetzt, endgültige leer | ✔ (KAS am 27.08. 21:00) |
| eine Stunde später endgültige Stufe = Betriebsform B-10 | ✔ |
| zweiter Lauf zur selben Stunde: keine Doppel | ✔ |
| **kein Seiteneffekt**: alle `data/*.db` und die Produktion unverändert, die Ablage legt nur ihre Datei an | ✔ |
| Stundenjob: Erfolg ohne Mail, Meldung, Fehler und Zeitgrenze je mit Fehlermail | ✔ |
| nach dem Umbau auf Laden je Asset: Modelle, Signale, Stufen und v̂ unverändert (7/7, Abweichung 0,0) | ✔ |

⛔ **Vorfall beim Bauen, behoben:** Eine Prüfung der Suite rief den Stundenjob in einem nachgebauten Notebook-Zustand auf. Der neue Prozessstart war dort
nicht abgefangen und startete einen **echten** Betriebslauf im Datenordner des Desktops. Danach lagen `data/regel0_signale.db` und ein Oktober-Paket am Desktop
(in den Scratchpad verschoben, nicht gelöscht). **Zwei Sperren:** (1) Die Wache fängt den Start ab und prüft nur, dass er erfolgt. (2) Der Betriebslauf
**verweigert sich selbst** außerhalb des Betriebsgeräts (dieselbe Sperre wie beim Nachlader), sofern Ablage und Modelle nicht ausdrücklich als Wegwerfordner
angegeben sind. Bewacht von `--paket Regel0Betrieb` (19/19): Rückgabe 3 und keine Spur im Datenordner. Genau dafür gilt *eine Prüfung hat keinen Seiteneffekt*.

**Last nach dem Umbau** (Desktop): Spitzenspeicher **0,99 GB statt 2,48 GB**, Stundenlauf **52–65 s** (vorher 118 s), Monatspaket 150–180 s.
Am Notebook ist mit rund **3–4 min** je Stunde zu rechnen, dazu einmal je Monat rund **10 min** für das Training. ⚠️ Das Notebook hat 8,3 GB, bei der
Lastprobe waren **1,8 GB frei**. Der Lauf läuft deshalb als eigener Prozess, damit sein Speicher danach wieder frei ist. Der Speicher am NB ist beim ersten
Lauf zu **kontrollieren** (K-S7-3).

**Am Notebook zu tun:**
1. `git pull`, dann die App neu starten. Der erste Lauf trainiert das Paket für **Oktober** (rund 10 min) und rechnet dann die erste Stunde.
2. Nach etwa 1–2 Stunden den Teilexport laufen lassen. Bestanden ist **K-S7-3**, wenn im Abschnitt REGEL0-RECHNUNG ein Paket `2026-10` mit Prüfsumme steht,
   es mindestens zwei Läufe mit *frisch* nahe *aktiv* gibt und keine Meldung kommt.
3. Danach den NB-Export (schlank). Bestanden ist er, wenn keine ERROR- oder Traceback-Zeile von `regel0` darin steht und keine Mail *Job 'regel0_rechnung'
   fehlgeschlagen* kam. Die anderen Jobs dürfen keine neuen Zeitüberschreitungen zeigen. Dazu die Zeile `REGEL0-ERGEBNIS` mit `sekunden`.

---

## 15. S7-4 — die REGEL0 geht in die Mail, der alte Hebelweg ist aus (03.10.2026; E-46, Nutzer: *„Ja D1 bis D4 wie vorgeschlagen, prüfen und gegenprüfen"*)

**Voranalyse am Code (kurz):**

| Frage | Befund |
|---|---|
| Wo entsteht heute ein Hebel? | **Nur** in der Rollen-Kette, in `_ein_asset` (`agent/rollen_lauf.py`): Das Etikett „Hebel" kommt aus r(q) oder der Geometrie, ein SHORT ist immer Hebel. Das alte Hebel-Screening ist am NB aus (`hebel_screening.aktiv=false`). In 72 h gab es **keine** Hebelmail |
| Warum nicht `hebel_handelbar` abschalten? | Den Schalter liest auch die **Führung echter Hebelpositionen** (`rollen_lauf.py:977`) und die Lagebeschreibung der Prompts. Abgeschaltet wird gezielt dort, wo ein **neuer Einstieg** Hebel wird |
| Wohin mit den Mails? | Der Stundenjob der App liest die Ablage `regel0_signale.db` und schickt über `_sende_hinweismail`. Der Rechenprozess selbst schickt nichts |
| O18 | Die Migration der Hebel-Schalter lief bei **jedem** Start und schaltete neue Watchlist-Assets still ein. Drei Leser nahmen ohne Eintrag *an* an |

**Gebaut:**

| Teil | |
|---|---|
| `Basisinfos/regel0_betrieb.yaml` | `alter_hebelweg_aus: true` (F1, im Zweifel AN) · `testwoche_bis: "2026-10-10"` (D4) |
| `agent/rollen_lauf.py` | in `_ein_asset`: Wird ein neuer Einstieg Hebel, wird er **Spot**. Ein **SHORT** geht verloren, denn Spot kann bei Bitpanda nicht short. Die Rechnung bekommt `hebel_handelbar=False`. Die taktische Zelle der Kern-Assets entfällt (sie besteht nur mit Hebel, Entscheidung 01.09.). **Spot und die Hebelführung echter Positionen bleiben unverändert** |
| `agent/regel0_ablage.py` | die EINE Stelle für `regel0_signale.db`, neu mit Kurs, Kursquelle und Mailspalten |
| `agent/regel0_mail.py` | **Signalmail** (Schalter an, Stufe > 0, Einstieg nicht älter als 3 h): Asset (Bitpanda-Name), Signal, **Einstieg** zum Schluss der Folgestunde und **Ausstieg** 24 h danach (UTC und Ortszeit), Hebel **vorläufig** (D1) mit Liquidationsgefahr je Stufe, **Bitpanda-Hinweis** (D2), Einsatz aus `regel0_betrieb.yaml` mit Richtwert-Vermerk, Kurs zur Signalstunde, Vermerke (Futures, nicht trainiert, BTC), Regelversion. **Korrektur** nur, wenn die endgültige Stufe abweicht (auch *kein Handel*). **Erinnerung**, wenn die 24 h um sind. Kein LLM-Kommentar (D3). **TESTWOCHE** in Betreff und Text bis 10.10. (D4). Vermerkt wird nur ein echter Versand, sonst neuer Versuch in der nächsten Stunde |
| Stundenjob | `regel0_nachlader_job` → Rechnung (eigener Prozess) → `_regel0_mails()`; die Mails laufen auch, wenn die Rechnung scheiterte |
| O18 | Die Migration läuft **einmal** (Marke `hebel_schalter_geradegezogen` in `meta`). Ohne Eintrag gilt **aus**, auch in den beiden Abfragen und in der Oberfläche |
| Paket B1 | prüft den **alten** Hebelweg und läuft deshalb sichtbar mit Schalter **aus** (`B1_ALTER_HEBELWEG_AUS`). So bleibt der alte Code geprüft, falls der Schalter je zurückgestellt wird |
| Teilexport | zeigt die Mails je Signal |

**Gegenprüfung** (`Basisinfos/Rechenkern_02_10/pruefe_s74.py` gegen die NB-Sicherung vom 02.10. 16:37, Beleg `pruefung_s74.txt`):

| | |
|---|---|
| A Mails (gestellte Signale, Versand abgefangen) | nur Schalter an, Stufe > 0 und frisch · Testwoche · Einstieg und Ausstieg wie gemessen · vorläufig, Bitpanda-Hinweis, Einsatz · Zusatz-Asset mit Bitpanda-Namen und Futures-Vermerk · kein Doppel · Korrektur nur bei Abweichung · späte Signalmail, wenn die Stufe erst endgültig > 0 wird · gescheiterter Versand wird wiederholt · Richtwert-Vermerk · Erinnerung, kein Doppel, verfällt nach 6 h · nach der Testwoche kein Vermerk |
| B Ende zu Ende | echter Stundenlauf (ETH am 12.08. 12:00, alle Assets) → Ablage → Mails genau für die Signale mit Schalter an (Schalter aus der NB-Sicherung) |
| C Rollen-Kette | Paket B1 mit Schalter **aus**: der Hebel-Lauf erzeugt wie bisher eine Hebelmail (Gegenprobe) · mit Schalter **an**: **keine** Hebelmail |
| D O18 | Der erste Lauf setzt die Marke, ein danach neues Watchlist-Asset bleibt ohne Eintrag = **aus**. Gegenprobe: ohne Marke wäre es still eingeschaltet worden |

⚠️ **Zwei Befunde beim Prüfen:** (1) `pruefstand_hebelmail.py` liefert gegen die NB-Sicherung **keine** Signale: SOL wird akkumuliert, LINK und NEAR scheitern an *Risikobudget fehlt*. Als Gegenprobe taugt er so nicht, deshalb Paket B1. (2) In B1 fiel mit Schalter an auch die „Spot"-Mail weg. Sie war die **taktische Hebel-Zelle** von ETH; die Akkumulationszelle verliert in **beiden** Stellungen am Entscheider. **Spot ist nicht betroffen.**

⚠️ **Für dich wichtig (O13):** Die alte **Hebelführung** echter Positionen bleibt an. Eröffnest du eine REGEL0-Position bei Bitpanda, kann sie dafür Mails nach dem **alten** Plan schicken (z. B. *Stop nachziehen*). Die REGEL0 hat aber keinen Stop: Es gilt die Ausstiegszeit aus der REGEL0-Mail. Die Führung für REGEL0-Positionen kommt mit O13.

**Am Notebook zu tun (nach dem Commit):**
1. `git pull`, dann die App neu starten. Der Schalter ist sofort an: Ab dann schlägt die Rollen-Kette keinen Hebel mehr vor.
2. Kontrolle **K-S7-3** (Teilexport, REGEL0-RECHNUNG) wie in §14, dazu **K-S7-4**:
   - Kommt ein Signal für ein Asset mit Hebel-Schalter an, muss die Mail *[TESTWOCHE] REGEL0 Hebel LONG …* kommen.
   - Der Teilexport zeigt bei diesem Signal *Mail <Zeit>*.
   - Eine Stunde später kommt höchstens eine Korrektur, nach 24 h die Erinnerung.
   - Im NB-Export: keine Zeile *REGEL0-Mails: … nicht zugestellt*, keine Fehlermail für `regel0_mails`.
3. Erwartung: Bei 25 Assets mit Hebel-Schalter sind es nach der Referenz **rund 2–3 Signale am Tag**. Davon sind fast alle handelbar (3x/5x).


---

## 16. VORANALYSE S7-5 — neue Listings, Zuordnung und Abgleich im Betrieb (03.10.2026, zur Abstimmung)

**Nutzer:** *„Ja, Voranalyse S7-5 starten, prüfen und gegenprüfen."*

**Ziel:** Am Notebook kommt **jedes** neue Binance-Krypto-Asset automatisch in die Datenbasis (E-40: *alles, was es gibt*). Und eine REGEL0-Mail geht **nie**
für einen falschen Coin raus.

**Stand:** Die Datenbasis wächst nur zeitlich. Der Nachlader führt fort, was schon in den Dateien steht. Abgeglichen wird nur am Desktop und von Hand.

**Test oder Betrieb:** Gebaut und geprüft wird am Desktop auf Wegwerfkopien. Die Änderung am Betrieb kommt erst nach den Kontrollen K-S7-3/K-S7-4 und mit deinem Ja.

### 16.1 Ist-Stand (am Code)

| | |
|---|---|
| **Auswahlregel** | `hole_stundenkurse_alle.universum()` (`:61-94`) ist EINE Regel: (1) jedes Spot-Paar in USDT im Handel ohne Stablecoins, Fiat und Edelmetall (`OHNE`); (2) dazu jedes USDT-Perpetual mit `underlyingType = COIN`, dessen Basis es nicht als Spot gibt; (3) je Asset der Markt mit der **längeren** Historie ab 2023; (4) ohne die Messbasis. Die Funktion lässt sich im Betrieb unverändert nutzen |
| **Nachlader** | Er lädt je Datei nur Symbole, die schon darin stehen (`agent/regel0_nachlader.py`). ⛔ **Ein neu gelistetes Paar kommt nie dazu** |
| **Markpreis** | `hole_markpreis.py` lädt Monatsarchive (data.binance.vision) und sperrt Monate mit fremdem Instrument (`_abweichung`, Markpreis gegen Spot). Für ein **neues** Listing reicht die Live-Schnittstelle, die der Nachlader schon benutzt (gegengeprüft: Archiv = live) |
| **Zuordnung** | `Basisinfos/symbol_zuordnung.csv` (im Repo). Ausnahmen CANTON→CC, CAT→1000CAT, **gesperrt** LIT, NEIRO, ONE, QUICK, ZK: Bitpanda führt dort einen **anderen Coin** als Binance. `pruefe_bitpanda_katalog.py` und `pruefe_symbol_zuordnung.py` gibt es nur zum Aufruf von Hand, mit `--eintragen` schreibend in die Repo-Datei |
| **Bitpanda-Ticker** | öffentlich, USD-Kurse aller Bitpanda-Krypto-Assets (`api.bitpanda.com/v1/ticker`). Damit lässt sich je Asset prüfen, ob der Binance-Kurs zum Bitpanda-Coin gehört |

### 16.2 ⚠️ Befunde

| # | Befund | Folge |
|---|---|---|
| **N-1** ⛔ | **Neue Listings fehlen.** E-40 heißt *alles, was Binance führt*. Ein heute gelistetes Paar bekäme aber nie Daten und damit nie ein Signal | Neuaufnahme im Betrieb (S7-5a) |
| **N-2** ⛔ | **ZK steht in der Messbasis** (19.901 Stunden), ist aber für Bitpanda **gesperrt** (anderer Coin unter gleichem Kürzel). Gesperrt wird bisher nur bei den Zusatz-Assets. Der Stundenlauf ordnet das Binance-ZK dem Bitpanda-Namen „ZK" zu. Wäre der Hebel-Schalter von Bitpanda-ZK an, käme eine Mail für den **falschen Coin**. Heute ist ZK nicht unter deinen 25, es passiert also nichts | Sofortpunkt (S7-5c) |
| **N-3** | **Eine Zuordnung kann sich ändern**: Umbenennung, Umstellung auf 1000er-Paar, ein neues Bitpanda-Asset mit gleichem Kürzel wie ein anderer Binance-Coin. Bisher fällt das nur beim Abgleich von Hand auf | Preisabgleich zur Mail (S7-5b) |
| **N-4** | **Tokenisierte Aktien und Wrapped Token** (ARMB, COINB, NOKB, QCOMB, SOXLB, WDCB, alle seit Juli 2026; WBTC) kamen über die Spot-Regel herein. Binance kennzeichnet sie **nicht** (gleiche Felder wie BTC). Mails lösen sie nicht aus (kein Hebel-Schalter), sie stehen aber in Auskunft und Signalbilanz | Frage F-3 |
| **N-5** | **Die Repo-Datei am NB beschreiben** hieße beim nächsten `git pull` ein Konflikt. Das kennen wir von der `config.yaml` | Am NB wird **nichts** in die Zuordnung geschrieben, die Sicherung läuft über den Kurs (S7-5b) |
| **N-6** | Assets mit Hebel-Schalter **ohne REGEL0-Daten** (heute XDC) bekommen still nie ein Signal | täglich ausweisen (S7-5d) |

### 16.2b Gegenprüfung der Befunde (03.10.2026, öffentliche Daten, nur gelesen)

| Aussage | gemessen |
|---|---|
| N-1 neue Listings | Die Regel ergibt heute **537** Assets, genau die in der Datei. Seit der Erstbefüllung am 01.10. kam **noch keines** dazu. Die Lücke ist real, sie hat heute aber noch keinen Fall |
| N-2/N-3 der Kursabgleich trennt | ZK **+101,6 %**, LIT +428 %, NEIRO −70 %, ONE +25 %, QUICK −100 % gegen BTC −0,1 % und ETH −0,1 %. Die Grenze von 5 % liegt weit zwischen *gleich* und *anderer Coin* |
| gesperrte Kürzel auf der Hebel-Liste (NB) | keines - es passiert heute also nichts |
| Erreichbarkeit | Bei `universum()` liefen 2 von 3 Versuchen am Desktop in Zeitgrenzen (viele Einzelabfragen). ➤ Der Tageslauf braucht eine **Wiederholung**, und er darf **nie halb** anlegen: Ein Asset wird erst eingetragen, wenn seine Historie vollständig geladen ist |

### 16.3 Bauplan nach deinem Ja (je mit eigener Prüfung)

| # | Was | Prüfung (muss fehlschlagen **können**) |
|---|---|---|
| **S7-5a** | **Neuaufnahme**, täglich am NB (z. B. 02:30 UTC, im Stundenjob nach dem Nachlader): `universum()` gegen die Dateien. Jedes **neue** Asset wird ab Listing (frühestens 2023) in `stundenkurse_alle.db` mit `_quelle` geladen, bei Futures auch der Markpreis in `markpreis_alle.db`. Nie in die Messbasis (Grundgesamtheit). Bewertet, nicht trainiert. Ein eingestelltes Paar bleibt, wie heute | Wegwerfkopie: ein vorhandenes Asset herausnehmen. Die Neuaufnahme muss es als neu erkennen und **zeilengleich** wieder laden |
| **S7-5b** | **Preisabgleich vor jeder Signalmail**: Bitpanda-Ticker (USD) gegen den Binance-Kurs der Signalstunde (mit Faktor). Abweichung > 5 % → **keine** Mail, Vermerk in der Ablage, Fehlermail *Zuordnung zweifelhaft*. Ein Aufruf je Mailrunde. Das fängt N-2, N-3 und neue Kollisionen genau dort, wo sie schaden | gestellter Ticker mit falschem Kurs → keine Mail; echter Kurs → Mail |
| **S7-5c** | **Gesperrte Kürzel gelten für alle Mengen**, auch für die Messbasis. Ein Binance-Symbol, dessen Bitpanda-Kürzel gesperrt ist, bekommt keinen Bitpanda-Namen und damit keine Mail | ZK-Signal (Live-Probe 18.06.2026) → in der Ablage ohne Bitpanda-Namen, keine Mail |
| **S7-5d** | **Täglicher Abgleich als Auskunft** (Teilexport, Log): neu aufgenommene Assets, Hebel-Schalter-Assets ohne Daten, Zuordnungen mit Abweichung. **Kein** Schreiben in die Repo-Datei. Die Pflege der Zuordnung bleibt am Desktop | Ausgabe mit gestelltem Zustand |

**Last:** Neue Listings gibt es wenige je Woche, mit kurzer Historie, also Sekunden. Der Ticker ist ein Abruf je Stunde mit Mail. Der Rechenkern bleibt unverändert.
Ein neues Asset hat erst nach 240 h ein eigenes Normal (J). Vorher gibt es kein Signal, das ist richtig so.

### 16.4 Zur Abstimmung

| # | Frage | Vorschlag |
|---|---|---|
| **F-1** | S7-5a bis S7-5d so bauen? | ➤ **Ja.** |
| **F-2** | S7-5b: Ist der **Bitpanda-Ticker nicht erreichbar**, was dann? | ➤ Die Mail geht **trotzdem** raus, mit dem Vermerk *Kurs nicht gegengeprüft*. Die Mail ist Information und kein Auftrag, ein Ausfall des Tickers soll dir kein Signal nehmen |
| **F-3** | **Tokenisierte Aktien und Wrapped Token** (N-4): aufnehmen oder ausschließen? | ➤ **Vorerst belassen.** Mails sind unmöglich (kein Hebel-Schalter), und eine Regel ohne Aufzählung gibt es nicht. Eine Liste veraltet still (stehende Regel 4). In der **Signalbilanz** weise ich sie getrennt aus. Neu prüfen, wenn Bitpanda solche Token anbietet |
| **F-4** | Zeitpunkt der Neuaufnahme | ➤ **Täglich**, im Stundenjob um 02:05 UTC. Ein neues Asset braucht ohnehin 10 Tage bis zum ersten Signal, stündlich bringt nichts |
| **F-5** | Wann ans Notebook? | ➤ Nach den Kontrollen K-S7-3/K-S7-4, also wenn die laufende Kette bestätigt ist. **S7-5c** (ZK) ist klein und schützt sofort, das kann gleich mit |


### 16.5 Abstimmung und Bau (Nutzer 03.10.2026: *„Ja F-1 bis F-5 wie vorgeschlagen, prüfen und gegenprüfen"*)

| Teil | gebaut |
|---|---|
| **S7-5a** | `agent/regel0_nachlader.neuaufnahme`: `universum()` mit 3 Versuchen. Jedes neue Asset bekommt die ganze Historie ab dem Listing (frühestens 2023), Kerzen und `_quelle` in **einer** Transaktion. Den Markpreis holt sie über die Live-Schnittstelle, mit Paar und Faktor wie die Erstbefüllung (eigenes Paar, sonst 1000er). Jeder Lauf wird in `_neuaufnahme` vermerkt. Der Stundenjob ruft sie einmal je Tag ab 02:00 UTC auf (`neuaufnahme_faellig`, nachgeholt), **vor** dem Nachladen. Ein Fehlschlag meldet sich und hält das Nachladen nicht auf |
| **S7-5b** | `agent/regel0_mail.abgleich`: Vor jeder Signalmail werden Bitpanda- und Binance-Ticker **zum selben Moment** verglichen (Faktor aus der Zuordnung). Ab 5 % geht **keine** Mail raus; stattdessen wird es in der Ablage vermerkt und kommt **einmal** die Mail *REGEL0 Zuordnung zweifelhaft*. Ist der Ticker weg, geht die Mail mit *Kurs nicht gegengeprüft* raus (F-2). Die Mail nennt den Abgleich |
| **S7-5c** | `regel0_stundenlauf._binance_zu_bitpanda`: Gesperrte Kürzel bekommen **für jede Menge** keinen Bitpanda-Namen (ZK) |
| **S7-5d** | Teilexport: Neuaufnahme (letzte 3 Läufe), Signale *nicht gemailt wegen Zuordnung*, **Hebel-Schalter an ohne REGEL0-Daten** (Desktop heute: AIOZ, SUPRA, VSN). Am NB wird nichts in die Repo-Datei geschrieben |
| F-3 | Die tokenisierten Aktien und WBTC bleiben in der Datenbasis. In der Signalbilanz stehen sie ohnehin nicht, die zählt nur Watchlist, Bestand und Hebel-Liste |

**Gegenprüfung** (`Basisinfos/Rechenkern_02_10/pruefe_s75.py`, Beleg `pruefung_s75.txt`): **15 von 15.**

- **Neuaufnahme:** Die herausgenommenen Assets HYPE (Futures) und FLOKI (Spot, Markpreis 1000FLOKI) werden als neu erkannt. Die Kerzen sind **zeilengleich** zur echten Datei (11.742 und 29.878).
- **Markpreise:** auf allen gemeinsamen Stunden **wertgleich**. Zusätzlich nur der **29.06.2026**, den das Monatsarchiv nicht hat (siehe unten).
- **Zweiter Lauf:** nichts Neues.
- **Alles oder nichts:** Ein gescheiterter Abruf (PLUME) hinterlässt nichts, und der nächste Lauf holt ihn nach.
- **Fälligkeit:** einmal am Tag, ab 02:00 UTC.
- **Messbasis:** wird nie beschrieben.
- **Abgleich:** Bei einer Kollision geht keine Mail raus, es kommt eine Meldung, und die nur einmal. BTC und CAT (Faktor 1000) gehen durch. Ohne Ticker kommt der Vermerk.
- **ZK:** Der echte Stundenlauf am 18.06.2026 mit Bitpanda-ZK-Schalter an legt ZK **ohne** Bitpanda-Namen ab, keine Mail.
- **Wache:** `--paket Regel0Betrieb` mit 4 Prüfungen zu S7-5.

⚠️ **Befund nebenbei:** Das Binance-**Monatsarchiv** der Markpreise hat eine **Lücke am 29.06.2026** (24 Stunden, alle geprüften Symbole). Die Live-Schnittstelle hat den Tag. Für die REGEL0 ist das unschädlich: Messung und Betrieb lesen dieselbe Datei, und Markpreise neuer Assets gehen nicht ins Training. Die erste Prüfung hatte das als *24 Stunden zu wenig* gelesen. Tatsächlich hatte die Neuaufnahme 24 Stunden **mehr**, und das Kriterium wurde entsprechend gefasst.

---

## 17. VORANALYSE — der Hebel-Tab der Oberfläche zeigt die REGEL0 (03.10.2026, zur Abstimmung)

**Nutzer:** *„In der GUI gibt es einen Hebel-Tab, diesen sollte man wiederverwenden, wenn möglich. Zeigt Signale und offene Positionen an."*

**Ist-Stand** (`ui/hebel_view.py`):

| | |
|---|---|
| Liste oben | Sie führt **zwei** Quellen zusammen, je (Symbol, Richtung) gewinnt die jüngere (`:257-282`): `hebel_signals` (alte Hebelkette) und `signals` mit Hebel (Rollen-Kette). Dazu kommen die wartenden **Kandidaten** des alten Screenings (`hebel_triggers`). Filter: 2 Tage oder alle, *handelbar* blendet SHORT aus, abgeschaltete Assets ohne offene Position sind ausgeblendet |
| Liste unten | **offene echte Positionen** (`hebel_positions`): Hebel, Eigenkapital, eröffnet, Liquidationspreis |
| Detail rechts | Text der Empfehlung, Charts der Liquiditätszonen und der Stabilität, Signal-Historie |
| ⚠️ Knopf *Jetzt analysieren* | erzeugt per LLM ein Signal auf dem **alten** Hebelweg. Mit `alter_hebelweg_aus` ist dieser Weg in der Kette aus, über den Knopf ließe er sich von Hand wieder anstoßen |

**Was fehlt:** Die REGEL0-Signale stehen nur in `data/regel0_signale.db` und in der Mail. Der Tab bliebe auf der Signalseite leer, weil der alte Weg keine neuen Signale mehr erzeugt.

**Vorschlag** (eine Quelle mehr, kein Umbau des Tabs):

| | |
|---|---|
| **Liste** | Die REGEL0-Signale als **dritte Quelle**, gelesen nur über `mode=ro`: Bitpanda-Name, LONG, Status (*Einstieg dd.mm. HH:MM* · *läuft bis …* · *Ausstieg fällig* · *kein Handel* · *nicht gemailt (Zuordnung)*), Hebel (endgültig, sonst vorläufig mit Vermerk), These *REGEL0 24 h*, Zeitpunkt. Es gelten dieselben Filter (2 Tage, Schalter) |
| **Detail** | **derselbe Text wie die Mail** (`regel0_mail.signal_mail`, eine Quelle), dazu der Mailstand (gemailt, Korrektur, Erinnerung, Abgleich) |
| **Positionen** | unverändert. Zusätzlich der Vermerk *REGEL0, Ausstieg …*, wenn für das Asset in den 24 h vor der Eröffnung ein REGEL0-Signal kam. Das ist eine Brücke bis O13 |
| **Knopf** | ist der alte Weg aus, ist er **gesperrt**, mit dem Hinweis *alter Hebelweg aus (REGEL0, E-46)*. Die alten Zeilen bleiben als Historie sichtbar |
| **Prüfung** | Die Zeilen entstehen in einer reinen Funktion (Ablage → Anzeigezeilen), die die Suite prüft. Die Oberfläche zeichnet nur. Dazu ein Rauchtest der Ansicht mit einer Wegwerfablage |

**Zur Abstimmung:**

| # | Frage | Vorschlag |
|---|---|---|
| **H-1** | REGEL0-Signale in **derselben** Liste (mit These *REGEL0*) statt in einer eigenen? | ➤ **Ja.** So bleibt ein Ort für Hebel, wie bisher |
| **H-2** | Den Knopf *Jetzt analysieren* sperren, solange der alte Weg aus ist? | ➤ **Ja.** Sonst entstünde von Hand ein Parallelbetrieb (F1) |
| **H-3** | Bei den offenen Positionen den REGEL0-Vermerk mit Ausstiegszeit zeigen? | ➤ **Ja** (Brücke bis O13) |
| **H-4** | Wann ans NB? | ➤ **Zusammen mit S7-5**, nach den Kontrollen K-S7-3/K-S7-4. Die Oberfläche berührt die Rechnung nicht |

### 17.1 Abstimmung und Bau (Nutzer 03.10.2026: *„Ja H-1 bis H-4 wie vorgeschlagen, prüfen und gegenprüfen"*, E-49)

| Teil | gebaut |
|---|---|
| **Anzeigemodul** | `agent/regel0_ansicht.py`, reine Funktionen von der Ablage zu den Anzeigezeilen. Die Oberfläche zeichnet nur. Die Ablage wird mit `mode=ro` geöffnet und **nie angelegt**; fehlt sie, gibt es keine Zeilen |
| **H-1** | Die REGEL0-Signale sind die **dritte Quelle** der Liste, je Asset das jüngste. Es ersetzt eine alte Zeile desselben (Asset, LONG) nur, wenn es jünger ist, dieselbe Regel wie zwischen den beiden alten Ketten. Spalten: Bitpanda-Name, LONG. Der Status ergibt sich aus den Zeiten des Signals: *Einstieg …*, *läuft bis …*, *Ausstieg fällig* (bis 6 h danach), *beendet …*, *kein Handel* oder *nicht gemailt (Zuordnung)*. Der Hebel ist endgültig oder *vorläufig*, die These *REGEL0 24 h*. Es gelten die Filter des Tabs: Ohne Hebel-Schalter oder ohne Bitpanda-Namen fällt eine Zeile weg, außer es gibt eine offene Position. *2 Tage* blendet nur Beendetes aus, das älter ist. Das **Detail** ist derselbe Text wie die Signalmail (`regel0_mail.signal_mail`), dazu der **Mailstand**: Signalmail, Korrektur, Erinnerung, Abgleich, Regelversion. *Signal-Historie* zeigt die alten Hebelsignale desselben Assets |
| **H-2** | `_alte_analyse_hinweis` fragt **zuerst** `regel0_ansicht.knopf_hinweis()`. Solange `alter_hebelweg_aus` an ist, ist der Knopf gesperrt, mit dem Hinweis *alter Hebelweg aus (REGEL0, E-46)*; ist der Schalter unlesbar, bleibt er ebenfalls gesperrt. Erst danach greift die Kettenregel |
| **H-3** | In der Positionsliste gibt es eine neue Spalte **REGEL0**: *REGEL0, Ausstieg …*, wenn für das Asset in den 24 h vor der Eröffnung ein REGEL0-Signal mit Stufe > 0 feststand (nur LONG), sonst *-* |
| **H-4** | Geht mit dem nächsten Pull ans NB |

**Gegenprüfung** (`Basisinfos/Rechenkern_02_10/pruefe_h17.py <NB-Sicherung>`, Beleg `pruefung_h17.txt`): **23 von 23.** Grundlage ist eine Wegwerf-Ablage mit jedem Status. Dazu kommt eine Kopie der NB-Sicherung vom 03.10. 05:20 mit zwei Wegwerf-Positionen: am NB ist heute keine Hebelposition offen. Darauf läuft der echte Tab in einem unsichtbaren Fenster.

- **Liste:** Jeder Status wird erkannt. Die Liste trägt genau die sichtbaren Zeilen, Status und Hebel gleich den reinen Funktionen. Bei *Alle* ist auch das Beendete da.
- **Detail und Historie:** Das Detail ist der Mailtext, der Knopf ist aus. *Signal-Historie* stolpert nicht über eine REGEL0-Zeile.
- **Positionsvermerk:** bei der Position mit Signal ja, bei der ohne nein.
- **Zusammenführung, beide Richtungen:** Die alte Rollen-Hebelzeile von ETH (26.09.) bleibt gegen ein älteres REGEL0-Signal stehen und weicht einem jüngeren.
- **Knopf:** gesperrt mit Schalter an; die Gegenprobe mit Schalter aus fällt auf die Kettenregel zurück.
- **Ohne Ablage:** keine Zeile, kein Absturz.
- **Seiteneffekte:** Die Ablage bleibt **bytegleich**, die Standard-DB unberührt.

**Suite:** Die Wache `--paket Regel0Betrieb` hat 7 neue Prüfungen, darunter *der Tab liest nur* und eine Gegenprobe zu H-2; sie steht jetzt bei 33 von 33.

---

## 18. VORANALYSE — die Stop-Nachzieh-Sammelmail (03.10.2026, zur Abstimmung)

**Nutzer:** *„Prüfe die alten Stop-Nachzieh-Mails (Sammelmail). Diese ist veraltet bzw. benötigen wir diese nur mehr für den Bestand und sollte eher nachgelagert unter dem Thema Spot-Positionsführung fallen, oder?"*

**Ist-Stand am Code:** `scheduler/background.ausstiegs_job` läuft täglich um 07:15, nach dem Backward-Tracking. Er macht drei Dinge:

1. Er protokolliert die Führung (`agent/fuehrung_protokoll`).
2. Er zieht die Ausstiege nach (`agent/ausstieg_verfolgung`).
3. Er verschickt `_sende_ausstiegs_email`.

Die Auswahl trifft `backward_tracking.compute_ausstiegs_empfehlungen`. Sie wählt alle **offenen Signale** aus `signals` und `hebel_signals`, die je über 1,0 R standen (Trailing ab 1,0 R, Abstand 1,0 R; Regel vom 04.08.). Abgeschaltet wird sie in `config.yaml` über `risiko.ausstieg_trailing_ausloese_r = 0`.

**Gemessen am NB-Export vom 03.10. 07:20** (67 Empfehlungen von 179 geprüften Signalen):

| | |
|---|---|
| Hebel | **0** — die Mail betrifft heute nur **Spot** |
| Richtung | 67 LONG, 0 SHORT |
| Ursprung | 63 NACHKAUFEN, 4 KAUFEN — also die Spot-Bestandskette |
| im Bestand | 61 Zeilen; **6 nicht** (PLTR, nur Signalverfolgung, fiktiv) |
| ⚠️ Zeilen je Position | **eine je SIGNAL, nicht je Position**: 67 Zeilen für **15** Symbole, davon HYPE 16, BRETT 16, BIO 7. Für dieselbe Position stehen also mehrere, leicht verschiedene Stops in der Mail |
| ⚠️ doppelter Versand | an Neustart-Tagen kommt die Mail **zweimal** (01.10.: 07:13 und 07:15; 03.10.: 06:27 und 07:15). Ursache: Der Nachholer (`_nachholen`, 16.08.) setzt bei einem Start **vor** 07:15 den Lauf sofort an, und der Cron feuert um 07:15 trotzdem. Dasselbe gilt für die anderen nachgeholten Tagesjobs. Dort ist ein zweiter Lauf harmlos, hier ist es eine zweite Mail |
| Grundlage | Die Trailing-Regel vom 04.08. (495 echte Signale, eine Marktphase) stammt aus dem **Altbestand vor dem Hebelneubau** (*als Vergleich gültig, als Grundlage nicht*). Für die REGEL0 gilt ein eigener Ausstieg (24 h). Die Positionsführung A ist dort nicht bestätigt (2.702) |

**Einordnung:** Ja, die Mail ist **Spot-Bestandsführung** und gehört zu **O14** (Spot-Kette ersetzen) als Teil *Spot-Positionsführung*. Für den Hebel hat sie heute keine Aufgabe mehr: Der alte Hebelweg ist aus (E-46), und echte Hebelpositionen gehören zu **O13** (2). ⚠️ Sie ist aber **nicht folgenlos stillzulegen**: Am selben Job hängen das Führungsprotokoll und die Ausstiegsverfolgung, und beide sind Messreihen (Befund 2.401, *Stilllegung: wer SCHREIBT das noch*). Abschalten hieße deshalb, nur die Mail abzuschalten, nicht den Job.

**Zur Abstimmung:**

| # | Frage | Vorschlag |
|---|---|---|
| **SN-1** | Die Sammelmail fachlich unter **O14 Spot-Positionsführung** führen, nicht unter Schritt 7? | ➤ **Ja.** Beim Ersatz der Spot-Kette wird sie neu entworfen: je **Position** statt je Signal, nur echter Bestand, Regel aus einer Messung nach heutigem Standard |
| **SN-2** | Bis dahin den **doppelten Versand** beheben? Nachgeholt wird nur, wenn die Uhrzeit des Jobs heute schon vorbei ist. Das gilt für alle Tagesjobs mit Nachholer, samt Prüfung | ➤ **Ja**, ein kleiner, eigener Schritt. Er ändert keine Bewertung |
| **SN-3** | Bis dahin die Mail auf **eine Zeile je Position** verdichten (höchster MFE je Symbol) und Nicht-Bestand weglassen? | ➤ **Nein, jetzt nicht.** Das wäre schon ein Teil der Neugestaltung unter O14. Heute reicht es, beim Lesen zu wissen: mehrere Zeilen je Symbol sind dieselbe Position |
| **SN-4** | Oder die Mail bis O14 **ganz abschalten** (nur die Mail; Protokoll und Verfolgung laufen weiter)? | ➤ deine Wahl als Nutzer der Mail. Fachlich spricht nichts dagegen, sie ist Information, kein Signal |

### 18.1 Abstimmung und Bau (Nutzer 03.10.2026: *„ok zu SN1 bis 4 — Abschalten nicht zwingend notwendig, da geringe Anzahl an Mails kommt, und dann vergisst man den Punkt nicht"*)

| # | entschieden |
|---|---|
| SN-1 | Die Sammelmail gehört zu **O14 Spot-Positionsführung** und wird dort neu entworfen (je Position, nur echter Bestand, Regel nach heutigem Standard) |
| SN-2 | ✔ **gebaut:** Der doppelte Versand ist behoben, siehe unten |
| SN-3 | Die Mail wird jetzt **nicht** verdichtet, das gehört zum Neuentwurf |
| SN-4 | Die Mail bleibt **an**. Es kommen nur wenige, und so bleibt der Punkt sichtbar |

**SN-2 im Code:** `scheduler/background.nachholen_jetzt(zuletzt, jetzt, stunde, minute)` ist die eine Stelle, an der entschieden wird. Nachgeholt wird nur, wenn der Job heute noch nicht lief **und** seine Uhrzeit heute schon vorbei ist, sonst feuert der Cron selbst. `_nachholen` bekommt die Uhrzeit seines Crons mit. Das betrifft alle vier Tagesjobs mit Nachholer: Kursreihen 05:30, Backward-Tracking 06:00, Portfoliowert 06:30, Ausstieg 07:15.

**Gegenprüfung** (`Basisinfos/Rechenkern_02_10/pruefe_sn2.py`, Beleg `pruefung_sn2.txt`): Der echte `build_scheduler` läuft auf einer Wegwerf-DB, die Uhr wird gestellt, der Scheduler wird nicht gestartet.

| Start | nachgeholt | zur Uhrzeit |
|---|---|---|
| 06:22 | Kursreihen, Backward-Tracking | Portfoliowert 06:30, Ausstieg 07:15 |
| 07:30 | alle vier, in der alten Reihenfolge (Versatz 10/30/120/240 s) | — |
| 04:00 | keiner | alle vier |

Die **Gegenprobe** mit dem alten Verhalten reproduziert den NB-Fall: Bei einem Start um 06:22 käme der Ausstieg **um 06:26 und um 07:15**. Die Standard-DB bleibt unberührt.

**Suite** (Paket 15): Das Verhalten wird an fünf Zeitpunkten geprüft. Dazu kommt die Uhrzeit jedes Nachholers gegen die seines Crons, aus dem Quelltext abgeleitet, und eine Gegenprobe.

➤ **Kontrolle K-SN-2** nach Pull und Neustart **vor 07:15**: Im NB-Log gibt es an diesem Tag **genau eine** Zeile *Stop-Nachzieh-Empfehlung(en)*.


---

## 19. VORANALYSE — der LLM-Prüfblock zur REGEL0-Mail (03.10.2026, zur Abstimmung; M1-Kriterium 4)

**Auftrag:** Nutzer: *„Ja, Voranalyse LLM-Prüfblock starten, prüfen und gegenprüfen"*. Der Rahmen steht fest:

- **F2 (E-42):** Die REGEL0 löst aus, die LLM-Rollen prüfen und kommentieren nur.
- **D3 (E-46):** Die erste Fassung der Mail hat keinen Kommentar.
- **M1-Kriterium 4:** *gepaarter Versuch auf denselben Ankern: neue Fassung (mit gemessener Bewertung gefüttert) gegen die heutige Rolle gegen gleich großen Zufall; produktiv geht die gemessene Fassung.*
- Dazu die stehenden Regeln: *LLM ist Prüfung, nicht Entscheider (Mailinfo-Block)* und *erst festhalten, was jede Rolle WIRKLICH bekommt*.

**Belege:** Alle Zahlen dieses Abschnitts rechnet `Basisinfos/Rechenkern_02_10/voranalyse_llm_fakten.py <NB-Sicherung>` nach (Beleg `voranalyse_llm_fakten.txt`, NB-Sicherung 03.10. 05:20, nur gelesen). Die Zuordnung der Einwände habe ich in zwei Reihenfolgen gegengeprüft, beide Male 84 %.

### 19.1 Was die Rollen HEUTE bekommen (am Code und an den Betriebsdaten)

| Rolle | Modul · Modell · Prompt-Stand | wann | Eingabe, wie sie WIRKLICH ankommt | Ausgabe | Wirkung heute |
|---|---|---|---|---|---|
| **A Marktanalyst** | `agent/rolle_analyst.py` · gemini-3.1-flash-lite · `2026-08-12b` | einmal je Durchgang, höchstens alle 3 h neu (`LAGEBILD_HALTBAR_STUNDEN`); 376 Lagebilder seit 14.08. | **kein einzelnes Asset**. Je Leitmarkt (US-Aktien, Krypto über Bitcoin, Rohstoffe) Sätze zu Trend, Schwankung, Handelbarkeit, Inflation, Liquidität, Zinskurve, dazu die Anlegerstimmung zu Bitcoin; relativ zur eigenen Vergangenheit (Perzentile) | `lage` (2–3 Sätze), `klassen` je Klasse *günstig/gemischt/ungünstig* mit Halbsatz, `belege` | geht als `marktlage_beurteilung` in die Eingabe von Rolle BC; Tabelle `lagebilder` |
| **BC Händler** | `agent/rolle_trader.py` · gemini-3.1-flash-lite (408 von 422 seit 26.09.) · `2026-09-11a` | je Asset der Rollen-Kette (Spot), Takt 15 min; 422 Signale seit 26.09. | Faktentext aus `rollen_eingabe` (`facts_json`, rund 2.800 Zeichen): Auftrag, Bestand mit Einstand, Marktstruktur, Kurs 5/20/60 Tage, Widerstand/Unterstützung in Schwankungsbreiten, Hebelabstände, Umsatz auf Aufwärtstagen, Umschlag, dazu das Lagebild von A. **Kein Wort zur REGEL0** (rsi, v̂, Hebelstufe, 24 h) | Aktion (KAUFEN/NACHKAUFEN/REDUZIEREN/VERKAUFEN/NICHTS_TUN), Richtung, Belege, unabhängige Faktoren, Begründung, Gegengrund, *umgeworfen durch* | **entscheidet die Spot-Aktion**; die Entscheiderstufe verwirft danach deterministisch (105 von 422). Den Hebel schlägt sie seit E-46 nicht mehr vor |
| **G Gegenprüfer** | `agent/zweite_meinung.rolle_g` · Z.ai glm-4.5-flash | je Signal mit Mail, im Nebenfaden, höchstens 2 gleichzeitig, rund 34 s; 17–33 Aufrufe je Tag | **nur** `geplant: {aktion, richtung}` und die **Positionierung** des Assets als Sätze (`positionierung.saetze`): offene Kontrakte, Finanzierungsrate als Perzentil, Anteil der Long-Konten, Börsenfluss (Bitcoin-weit). Ohne Terminmarktdaten (Aktien, ETF, Rohstoffe) wird **nicht** gefragt. Grundlage für **40** Symbole | `einwand` ja/nein/unklar und ein Satz mit Zahl | **nur Mail und Zeile**, kippt nichts (P-8). Seit 26.09. 133 Urteile: 42 ja, 88 nein, 3 unklar |
| Z1 (kein Sprachmodell) | `agent/gegenpruefer_rollen.py` | je Antwort | die Antwort gegen ihre eigene Eingabe | Zahlendeckung, Richtungstreue, Zuspitzung, Leerlauf | zählt, verwirft nicht |

➤ **Für die REGEL0 wird heute KEINE Rolle gefragt.** Die Signalmail kommt aus `agent/regel0_mail.py` ohne LLM (D3).

### 19.2 Befunde

| # | Befund | Folge |
|---|---|---|
| **L-1** | Keine Rolle kennt die REGEL0. Was 2.398 für die alte Bewertung festhielt, gilt hier wieder: Prompt und Fakten nennen weder rsi-Ersteintritt noch v̂, Hebelstufe oder 24-h-Ausstieg | Eine Prüfung braucht eine **neue Fassung**, die weiß, was sie prüft. Das ist der Arm *neue Fassung* aus M1-4 |
| **L-2** | Die Konstruktionsbedingung R-R2 (der Prüfer hat Information, die dem Urteilenden fehlt) ist **erfüllbar**: Die REGEL0 nutzt nur rsi/Normal und ATR. A (Leitmärkte), G (Terminmarkt) und der Faktentext von BC tragen andere Information | Formal geht jede der drei. ⚠️ **Aber:** Genau diese Information ist deterministisch schon geprüft und trug auf dem Kern nicht: A/B/L ohne Verbesserung (2.702–2.704), der Marktzustand ist nicht vorab erkennbar (2.599), `funding` liegt an der Nachweisgrenze, `long_bias` trägt auf keiner Menge (Kandidatenblatt). Die **Erwartung** an einen messbaren Beitrag ist **gering** |
| **L-3** | ⚠️ **G stützt sich fast nur auf zwei Zahlen:** Von 692 Einwänden seit 20.08. nennen **84 %** den Anteil der Long-Konten oder die Finanzierungsrate | Das ist eine **messbare Erklärung**: Ob extreme Long-Konten- oder Finanzierungswerte die REGEL0-Einstiege trennen, lässt sich deterministisch auf vorhandenen Daten prüfen (Vorprüfung V-1). Trennen sie nicht, kann G kaum tragen. Trennen sie, gehört das als Regel in die REGEL1 und nicht in ein Sprachmodell |
| **L-4** | ⚠️ **Rolle A ist auf gleichen Fakten nicht stabil:** Von 79 mehrfach gefragten Faktenständen bekamen 22 verschiedene Krypto-Einstufungen; nur **84 %** der Wiederholungspaare sind gleich. Die Einstufung ist fast konstant (*gemischt* 272, *ungünstig* 102, *günstig* 2 von 376) | Als Auskunft brauchbar, als Prüfsignal schwach: 16 % Eigenrauschen bei einem Feld, das zu 72 % *gemischt* sagt |
| **L-5** | ⚠️⚠️ **Eine Vorwärtsmessung braucht Monate bis Jahre.** Der 24-h-Ertrag eines REGEL0-Einstiegs streut mit **5,6 %** (Mittel +0,29 %). Einen Unterschied von **1 Prozentpunkt** zwischen *Einwand ja* und *nein* findet man (80 % Macht) nach rund **1.000** Handeln. Auf allen Assets sind das **82 Tage**, auf den Assets mit Hebel-Schalter an (2,2 Einstiege je Tag) **392 Tage**. Für **0,5** Prozentpunkte sind es 329 bzw. 1.569 Tage. ⚠️ G kann nur auf den **40** Symbolen mit Terminmarktdaten fragen: Das sind **2,7** Einstiege je Tag, also rund **340 Tage** für 1 Prozentpunkt | Der gepaarte Versuch aus M1-4 ist vorwärts **nicht vor M1** entscheidbar. Die deterministische Vorprüfung V-1 dagegen hat auf der Messbasis (Terminmarkt 122 Symbole bis 02.09.) alle **7.376** Einstiege und löst damit rund **0,6** Prozentpunkte auf |
| **L-6** | ⚠️ **Ein historischer Rückspielversuch ist kontaminiert:** Die REGEL0-Einstiege 2024–2026 liegen im Zeitraum, den die Modelle aus dem Training kennen können (Zielgrößen §3b: *nur Vorwärtsmessung zählt*). Der Wissensstand von gemini-3.1-flash-lite und glm-4.5-flash ist **nicht** belegt, nur vermutbar | Ein Rückspiel nur mit **anonymer** Eingabe (kein Name, kein Datum, keine absoluten Kurse). Die Eingabe von G kommt dem nahe (Perzentile), die von BC nicht (Name, Euro-Kurse). Dazu fehlt ein historischer Nachbau von `positionierung.lage` zum Zeitpunkt t |
| **L-7** | Kosten und Zeit sind **kein** Engpass: 2–3 Signalmails je Tag ergeben 2–3 zusätzliche Z.ai-Aufrufe (heute 17–33). Das Lagebild von A liegt ohnehin vor und kostet **keinen** Aufruf. G braucht rund 34 s, höchstens 75 s | Die Mail kann auf G warten, mit Deckel. Kommt nichts, geht sie ohne Block raus (P-8) |

### 19.3 Vorschlag

| Schritt | Was | Warum so |
|---|---|---|
| **V-1** Vorprüfung, Desktop, Minuten | Auf den REGEL0-Einstiegen 2025–26 (Spur `b0_spur_*`, Messbasis Terminmarkt und Funding) wird deterministisch gemessen, ob **extremer Long-Konten-Anteil** oder **extreme Finanzierungsrate** zur Einstiegsstunde den 24-h-Ertrag trennen. Messregel nach Messstandard: tagestreue Nullwelt, Band 5./95. Perzentil, je Jahr, Spiegelprobe | L-3: Das ist fast alles, worauf G urteilt. Die Antwort sagt, ob G **überhaupt** etwas tragen **kann**, und das ohne einen Modellaufruf. *Eine Erklärung, die man messen kann, ist zu messen* |
| **P-1** Mailblock (Fassung 0.2 der Mail) | Am Ende der Signalmail steht ein Block **PRÜFUNG (Auskunft, ungemessen, löst nichts aus)**. Er hat drei Teile: (a) **Umfeld Krypto (Rolle A):** das jüngste Lagebild, höchstens 3 h alt, mit Einstufung, Halbsatz und dem Vermerk *bei gleichen Fakten in 84 % gleich*. Kein Zusatzaufruf. (b) **Terminmarkt (Rolle G, neue Fassung):** ein Aufruf je Signalmail, nur für Assets mit Terminmarktdaten. Der Prompt weiß, was geprüft wird: *REGEL0: LONG, Hebel n×, Ausstieg nach 24 h, kein Stop*. Ausgabe: Einwand und Satz. Die Mail wartet darauf höchstens 90 s. (c) **Kein Händler (BC)** | D3 wird damit abgelöst. Der Block ist **Information** (Regel 3: *in der Mail erwünscht, samt Bewertungsgründen*). Er bleibt ausdrücklich ungemessen (2.459-ungemessen) |
| **P-2** Schattenmessung für M1-4 | Für **jedes** REGEL0-Signal eines Assets mit Terminmarktdaten, egal wie der Hebel-Schalter steht, laufen G **alt** (nur Aktion/Richtung) und G **neu** (mit REGEL0) und als drittes ein **Zufallsarm** in Python mit gleicher Einwandquote. Alles wird in der REGEL0-Ablage gespeichert. Der Ausgang (24 h) kommt aus den Stundenkursen. **Messregel vorab festgelegt:** Zielgröße 24-h-Ertrag ohne Hebel, Vergleich *Einwand ja* gegen *nein*, Nullwelt durch Vertauschen der Einwände innerhalb des Monats, Band 5./95. Perzentil. Ausgewertet wird **einmal**, wenn n = 1.000 erreicht ist. Monatlich gibt es nur einen Zwischenstand als Auskunft, ohne Entscheidung (Mehrfachtesten) | Das ist der gepaarte Versuch aus M1-4, vorwärts und damit ohne Vorwissen. Die Menge ist größer als die gemailten Signale, aber auf 40 Symbole begrenzt: **rund ein Jahr** bis n = 1.000 (L-5). Kürzer wird es nur, wenn die Positionierung für **alle** Futures-Assets live geholt wird. Das ist eine eigene Entscheidung über die Datenbasis (L-f). Kosten: rund 2 Z.ai-Aufrufe je Signal, also 5–6 je Tag |
| zurückgestellt | **BC für die REGEL0** und das **historische Rückspiel** | BC ist als Entscheider gebaut. Als Prüfer wäre sie eine neue Rolle, und ihr Faktentext trägt Name und Euro-Kurse (L-6). Das Rückspiel braucht eine anonyme Eingabe und einen Nachbau der Positionierung zum Zeitpunkt t. Beides erst nach V-1 und nur, wenn V-1 etwas findet |

**Zwischenfazit zum Ziel:** Ein Sprachmodell kann der REGEL0 **keine neue Information** liefern. Es kann die Information, die die REGEL0 nicht nutzt (Umfeld, Terminmarkt), in Worte fassen und abwägen. Ob diese Abwägung das **Potential** besser trennt, ist offen. Die deterministische Seite derselben Information trug bisher nicht. Deshalb kommen zuerst die billige Vorprüfung (V-1) und der Block als **Auskunft** (P-1). Dazu läuft die Messung, die M1-4 verlangt (P-2). Sie ist vorwärts nur langsam entscheidbar, deshalb sagt V-1 vorab, ob sich das Warten lohnt.

### 19.4 Zur Abstimmung

| # | Frage | Vorschlag |
|---|---|---|
| **L-a** | V-1 jetzt messen (deterministisch, Desktop, ohne Modellaufruf)? | ➤ **Ja** |
| **L-b** | P-1 so bauen: Umfeld (A, ohne Zusatzaufruf) und Terminmarkt (G neu, ein Aufruf), Mail wartet höchstens 90 s, kein Händler? | ➤ **Ja**, nach V-1. Fällt V-1 leer aus, bleibt G im Block trotzdem eine Auskunft, aber mit diesem Vermerk |
| **L-c** | P-2 mit der vorab festgelegten Messregel starten, Auswertung einmal bei n = 1.000? | ➤ **Ja**. Auf den 40 Terminmarkt-Symbolen dauert das rund ein Jahr. Ob P-2 sich lohnt, zeigt schon V-1: Trennen die Zahlen selbst nicht, ist kaum zu erwarten, dass ein Modell auf denselben Zahlen besser trennt |
| **L-f** | Die Positionierung (offene Kontrakte, Finanzierung, Long-Konten) für **alle** Futures-Assets stündlich holen, damit P-2 schneller entscheidbar wird? | ➤ **Nein, vorerst nicht.** Erst wenn V-1 einen Beitrag findet. Sonst wäre es eine neue Datenquelle für eine Prüfung mit geringer Erwartung |
| **L-d** | BC und das historische Rückspiel zurückstellen? | ➤ **Ja** (Begründung oben) |
| **L-e** | ⚠️ **M1-Kriterium 4 lesen als:** *Block gebaut und als ungemessen ausgewiesen, Schattenmessung läuft mit fester Regel; das Urteil folgt bei n = 1.000*? Wörtlich verlangt M1-4 ein **Ergebnis** vor M1, und das ist nach L-5 vor M1 nicht erreichbar | ➤ **deine Entscheidung**, denn M1 ist deine Definition. Ohne diese Lesart steht M1 rund ein Jahr auf diesem einen Kriterium |

### 19.5 Abstimmung (Nutzer 03.10.2026, E-50)

L-a bis L-f sind **abgelöst**: Die LLM-Ebene der REGEL0 wird **neu gebaut**. Zuerst kommt die Information je Rolle, dann der Prompt aus den Erkenntnissen des ersten Baus, dann Schatten, Rückspiel und Simulation, dann Produktion mit Mail und Charts. Spot bleibt auf der alten Kette. Die Befunde L-1 bis L-7 gelten weiter und gehen in den Neubau ein (Plan O20, Voranalyse §20).


---

## 20. VORANALYSE — der LLM-Neubau für die REGEL0 (03.10.2026, E-50, Plan O20; zur Abstimmung)

**Nutzer 03.10.:** *„Sofortiger Umbau, testen, analysieren und simulieren, dann in Produktion mit eMail und Charts. Diesen Bereich können wir nicht so einfach bauen wie die REGEL0: 1. zuerst prüfen, welche Informationen jede Rolle erhalten soll, um einen sinnvollen Beitrag zu liefern, 2. wie soll dies in den Prompt, 3. weitere tragende Beiträge nachgelagert."* Und: *„Nur Informationen nutzen, welche ausreichend abgedeckt sind. Nimm in die Bewertung mit, ob und welche Informationen die LLM-Rollen aus der REGEL0 erhalten sollten oder sogar müssen. Die LLM-Rollen sollen als Gegenprüfung zur deterministischen Komponente dienen, aber falls möglich einen Vorteil über die LLM-Texte und Verarbeitung über KI liefern, oder auch nur reine Bestätigung, dass der Trade gut ist."*

**Grundlage:** das Verzeichnis der Erkenntnisse aus dem ersten Bau. Ein Rechercheagent hat es erstellt (A1–A35, B1–B25, C1–C32, D1–D16, E1–E18, F1–F20, G1–G33, H1–H19, je mit Fundstelle und Status *gemessen / recherchiert / angenommen*). Die tragenden Fundstellen habe ich selbst an der Quelle gegengeprüft: R-R2/R-R3 (RWM:4603–4629), der Einbruch von 93 % auf 3 % (RWM:516), *LLM gegen Regel* (AD:812–837), R-T1 bis R-T12 (RWM:3590–3689), das Gemini-Kontingent von 500 je Tag und Modell (Memory), 2.457-w1 und 2.566. Dazu gelten die Befunde L-1 bis L-7 aus §19.

⚠️ **Namen:** A, B und C sind im Hebel-Neubau **deterministische** Rollen (Richtung, Bewegung, Sperre; 2.643, 2.648). Die neuen LLM-Rollen bekommen deshalb **eigene Namen**: **P-U** (Prüfer Umfeld), **P-A** (Prüfer Asset), **P-T** (Prüfer Text). Die alten Namen Marktanalyst, Händler und Gegenprüfer bleiben der Spot-Kette.

### 20.1 Was „ausreichend abgedeckt" heißt — und was danach übrig bleibt

**Kriterium (Vorschlag):** Eine Information darf in eine Rolle, wenn sie **(a)** am NB **live für alle REGEL0-Assets** vorliegt **und (b)** für 2025–26 **in derselben Form** als Historie. (a) bedeutet: Betrieb und Messung haben dieselbe Grundgesamtheit. (b) braucht das Rückspiel. Was nur für einen Teil der Assets vorliegt, ändert die Eingabe von Signal zu Signal, und eine Messung mischt dann zwei Rollen (Lehre A5/G22: *Rolle A bekam am NB 12 statt 15 Aussagen*).

| Information | live am NB | Historie 2025–26 | abgedeckt? |
|---|---|---|---|
| **Kurs und Volumen stündlich**, daraus Struktur: Verlauf 5/20/60 Tage, Marken in ATR, Volumen relativ zur eigenen Vergangenheit, Lage zu langen Schnitten | ✔ **537** Assets (`stundenkurse_alle`) | ✔ ab 2023, dieselbe Datei | ✔ **ja** |
| **Marktumfeld**: Leitmärkte (BTC, US-Aktien, Rohstoffe), Makro (Netto-Liquidität, Zinskurve, Inflation), Fear & Greed; für alle Assets **dasselbe** | ✔ (`marktlage.py`, aus der Datenbank) | ✔ (Makrohistorie in der Datenbank, nie live gelesen, A3) | ✔ **ja** |
| Markpreis gegen Kassakurs (Basis) | 411 von 537 | ✔ 411 | ✗ (77 %) |
| Funding | nur Watchlist; **alle** Futures-Paare wären mit **einem** Binance-Abruf live zu haben | 302 Symbole, nur **täglich** (Tageswert an einem Stundenanker ist Vorgriff) | ✗ heute; ◐ mit Ausbau |
| Terminmarkt (offene Kontrakte, Long-Konten) | **40** Symbole | 122 Symbole bis 02.09. | ✗ |
| Käuferanteil, Premium, BTC-Dominanz stündlich | fehlt am NB | 116 Symbole | ✗ |
| Umlaufmenge (Umschlag) | Betriebskopie, nur Teil | Teil | ✗ |
| **Nachrichtentext** (Börsenmeldungen, Delistings, Token-Freigaben, Hacks) | **keine** Quelle angebunden | — | ✗ heute |

➤ **Abgedeckt sind heute genau zwei Informationsarten:** das **Marktumfeld** und die **eigene Kurs- und Volumenstruktur** des Assets. Die heutige Rolle G (Gegenprüfer) fällt damit heraus: Ihre Grundlage (Terminmarkt) gibt es für 40 von 537 Assets.

⚠️ **Ehrlich dazu:** Beide Informationsarten sind **deterministisch schon geprüft** und trugen auf dem Kern **nicht**: A/B/L ohne Verbesserung (2.702–2.704), der Marktzustand ist nicht vorab erkennbar (2.599), die Dominanzsperren wurden umgestoßen (2.670/2.672). Ein Sprachmodell bekommt dieselben Zahlen nur in Worten. Sein möglicher Vorteil ist allein die **Abwägung** mehrerer Angaben gegeneinander, die keine einzelne Formel abbildet. Ob es diesen Vorteil gibt, sagt nur die Messung.

### 20.2 Was die Rollen aus der REGEL0 bekommen MÜSSEN, DÜRFEN und NICHT DÜRFEN

| | was | warum |
|---|---|---|
| **MUSS** | **der geplante Handel:** LONG, Hebel n×, Einstieg zum Schluss der Folgestunde, **Ausstieg nach 24 h, ohne Stop und Ziel** | Ohne ihn prüft die Rolle nichts Bestimmtes (L-1). Ohne den **Horizont** beurteilt sie einen anderen Handel. Ein *Einstieg* ohne 24 h wird als Swing gelesen (*Messgeometrie ist nicht Betrieb*) |
| **DARF** | der **Hebel** als Teil des Plans (*gehebelt, also teuer, wenn es schiefgeht*) | Damit ist die Frage richtig gestellt. Gefragt wird **nicht** nach der Höhe: Der Hebel ist ein Risikoparameter und gehört nicht dem Modell (C11, R-A2) |
| **NICHT** | v̂, Schwelle, rsi-Ersteintritt, Normal, Liquidationsgefahr je Stufe, historische Trefferquote oder Erwartung der REGEL0 | (1) **Selbstauskunft des Systems (R-T4):** Ein Systemgüte-Fakt verschob gemessen −8,86 Konfidenzpunkte und drückte die LONG-Wahl von 56 % auf 44 % (B6). (2) **Anker (C12):** Ein vorgegebenes Urteil verankert das Modell, und keine Gegenmaßnahme half. (3) **R-R2:** Das ist die Information der REGEL0 selbst. Eine Prüfung darauf ist ein **Echo**, und eine *Bestätigung* wäre eine Selbstbestätigung. Die Zahlen stehen getrennt im **deterministischen Teil der Mail**, du siehst beide nebeneinander |

➤ **Daraus folgt der Sinn einer „Bestätigung":** Sie ist nur dann eine, wenn die Rolle **unabhängig** von der REGEL0 urteilt, also auf Information, die die REGEL0 nicht nutzt, und ohne deren Urteil zu kennen. Genau so lässt sie sich auch **messen**: Trennt *stützt* gegen *spricht dagegen* den 24-h-Ausgang der REGEL0-Handel?

### 20.3 Die Rollen

| Rolle | Frage | Eingabe | Aufruf | Abdeckung |
|---|---|---|---|---|
| **P-U Prüfer Umfeld** | *Spricht das Marktumfeld für oder gegen einen gehebelten 24-h-LONG in Krypto?* | Leitmärkte, Makro, Fear & Greed als Sätze nach R-T1 bis R-T12. Die Datenschicht von `marktlage.py` wird übernommen, sie ist gemessen und gegengeprüft (Befunde, kein Prompt-Code). **Kein** Asset, **kein** REGEL0-Wert | **einmal je Stunde**, für alle Signale dieser Stunde wiederverwendet | ✔ 100 % |
| **P-A Prüfer Asset** | *Spricht die eigene Kurs- und Volumenlage DIESES Werts für oder gegen den geplanten 24-h-LONG?* | **anonym:** kein Name, kein Datum, keine absoluten Kurse. Verlauf 5/20/60 Tage, Marken (Widerstand und Unterstützung in ATR, mit Zahl der Berührungen), Lage zu den Schnitten, Volumen relativ zur eigenen Vergangenheit, Schwankung als Perzentil. **Kein** rsi und **kein** Normal (das nutzt die REGEL0), **kein** Umfeld (das hat P-U, A12-Lehre: eine Rolle, ein Eingang) | je Signal | ✔ 100 % |
| **P-T Prüfer Text** | *Gibt es eine Meldung, die gegen diesen Handel spricht?* (Delisting, Hack, Token-Freigabe, Umstellung) | Nachrichtentext. Das ist die **einzige** Information, bei der ein Sprachmodell **grundsätzlich** mehr kann als eine Regel | je Signal | ✗ heute. **Nachgelagert** (deine Nummer 3), siehe 20.7 |

**Ausgabe beider Rollen:**
- **Urteil in drei Stufen:** *stützt den Handel*, *neutral* oder *spricht dagegen*.
- **Beleg mit Zahl.**
- **Stärkster Gegengrund** in einem eigenen Feld (C18).

*Neutral* ist dabei ein **Urteil** über vorhandene Angaben (*„ein Teil spricht dafür, ein Teil dagegen"*). Es ist **keine** „unklar"-Option. Eine solche führte gemessen zur Enthaltung (C5: 93 % auf 3 %). Wie oft *neutral* kommt, zeigt die Messung. Liegt es über 70 % (wie *gemischt* bei der heutigen Rolle A), unterscheidet die Rolle nichts (R-T6).

### 20.4 Der Prompt — was aus dem ersten Bau übernommen wird (Auszug; vollständig im Verzeichnis)

| Regel | Beleg |
|---|---|
| Fakten als **Sätze** mit **Fenster**, **relativ**, Perzentil **mit** Einordnungswort aus **denselben** Grenzen; **keine** Werturteile, Etiketten, konstanten Felder oder rohen Zahlenreihen; der Prompt **rechnet nicht vor** | R-T1 bis R-T12; einordnung −4,60 Punkte und −16 pp LONG (B4); regime 1.022 von 1.022 *baer* (B8); Volumen-Perzentil erfunden nach Umbenennung (B18) |
| **Keine** Konfidenz, **kein** Betrag, **kein** Hebel, **kein** Stop, **keine** Rechnung vom Modell; **keine** Vorsichtssprache | C1 (77,5 % gegen 33,3 %), C9/C10, C11, R-A4 |
| Gefragt wird **nur, was die Fakten tragen**. Prompt, Schema, Vorlage und Validator **wandern gemeinsam** | G1–G4 (Betragsfrage, Marktbreite, W4, W5) |
| **Ausführungsbeschränkung nicht in den Prompt** | C29 (93 % → 3 %) |
| **Persona:** keine. Neutrale Rahmung, wie bei Z.ai entschieden (C26). Beim Händler nie gemessen (C25) | |
| **Reihenfolge:** Belege → Urteil → Gegengrund. **Positionsbias** prüfen, mit vertauschter Reihenfolge der Sätze als eigenem Arm | B11–B13 (Z.ai U-Kurve) |
| **JSON:** Gemini mit `json_object` (ein striktes Schema kostete 16 pp), Z.ai mit `json_object`. Das Schema wird aus den Validator-Konstanten **abgeleitet** | D5–D7, D10 |
| **Validierung:** Formfehler korrigieren, Sinnfehler ablehnen, alles vermerkt. Das Urteil wird **nie geraten**. Ausfall ist **nicht** Zustimmung (grau in der Mail) | D1–D3, D15, G20 |
| **Temperatur 0** und Wiederholungsprobe. Der Nichtdeterminismus bleibt auch bei t = 0 | E13, E14, L-4 (84 %) |
| **Modell an der Quelle festhalten** (Messung auf 3.5, Betrieb auf 3.1: *ein Befund überträgt sich nicht*), Prompt-Hash an jeder Zeile, Kanarienvogel gegen Drift | E1, E9 (Mistral-Bruch 31.07.), E16 |
| **Ende zu Ende nachweisen:** im gerenderten Faktentext und in der fertigen Mail (*Rolle G lief nie, 853 grüne Prüfungen*) | G14, Regel 10 |

### 20.5 Messung — „wirken die neuen Aufrufe?"

| | |
|---|---|
| **Anker** | die REGEL0-Einstiege 2025–26 auf **allen** Assets der Datenbasis. Je Rolle werden **1.000–1.500** zufällig und vorab gezogen. Die Stichprobe ist eingefroren |
| **Arme** | (1) **neue Rolle**, (2) **Regel auf denselben Eingaben** (für P-A z. B. Verlauf 20 Tage und Lage zur Marke, für P-U der gerechnete Gleichlauf; F6: *das LLM lag hinter jeder Regel*), (3) **Zufall** mit gleicher Stufenquote, (4) **Rauschboden:** Wiederholung derselben Eingabe (A/A′) und vertauschte Reihenfolge |
| **Kontaminationsprobe** | (a) Erkennt das Modell aus der anonymen Eingabe Asset oder Zeitraum? Gefragt wird direkt, an 50 Ankern. (b) Trennt eine **benannte** Fassung an 100 Ankern besser als die anonyme? Fällt eine der beiden Proben durch, gilt nur die Vorwärtsmessung |
| **Zielgröße** | 24-h-Ertrag ohne Hebel, wie in der REGEL0-Spur |
| **Messregel (vorab)** | Unterschied *stützt* gegen *spricht dagegen*. Nullwelt durch Vertauschen der Urteile **innerhalb des Tages** (tagestreu), Band 5./95. Perzentil, **je Jahr** (2025 und 2026 getrennt), dazu die Signalbilanz je Asset. **Trägt** heißt: über dem Band in **beiden** Jahren **und** besser als der Regel-Arm. Ausgewertet wird **einmal**, ohne Zwischenblick |
| **Kalibrierlauf** | 50 Anker vorher: Antworten formgültig, Stufenverteilung, Laufzeit (F16) |
| **Budget und Modell** | Gemini 500 je Tag **und Modell**. Die Spot-Kette braucht auf **gemini-3.1-flash-lite** zurzeit **320–450** je Tag (am 30.09. 453), dort ist kaum Luft. **gemini-3.5-flash-lite** ist fast frei (rund 460 je Tag). ➤ Die neuen Rollen laufen in Messung **und** Betrieb auf **3.5**, ein Befund überträgt sich nicht zwischen Modellen (E1). Je Rolle etwa 1.500 Aufrufe plus Wiederholung, also rund **4 Tage** je Rolle, mit Deckel unter dem Limit, damit der Betrieb nichts merkt |
| **danach vorwärts** | Schatten auf **allen** live entstehenden REGEL0-Signalen (12–15 je Tag). Er bestätigt das Rückspiel, nach rund 3 Monaten n ≈ 1.000 |

### 20.6 Produktion — Mail und Charts

| | |
|---|---|
| **Mail** | Ein Block **PRÜFUNG** unter dem deterministischen Teil: je Rolle Stufe, Beleg und Gegengrund, dazu der **Messstand** der Rolle (*„trennt in 2025 und 2026, n = …"* oder *„trennt nicht, n = …"*). Ausfall erscheint grau. Die Mail wartet höchstens 90 s, sonst geht sie ohne den Block raus (P-8) |
| **Charts** | Eingebettet als Bild, die Technik besteht schon (`send_notification_email(inline_images=…)`, seit der Grafik zu den Liquiditätszonen). Gezeigt werden: Stundenkurs der letzten 5 Tage mit **Einstieg** und **Ausstieg nach 24 h**, Liquidationsgrenze je Stufe und die Marken aus P-A. **Dasselbe Bild im Hebel-Tab** (eine Quelle) |
| **Signalwirkung** | **keine.** Die REGEL0 löst aus (F2). Ein Filter aus einer Rolle wäre eine REGEL1 und bräuchte eine eigene Messung mit Signalbilanz |

### 20.7 Nachgelagert (deine Nummer 3)

1. **P-T Text:** eine Quelle mit voller Abdeckung suchen, z. B. die Börsenmeldungen von Binance (alle Binance-Assets). 2.566 hat **nicht** Nachrichtentext gemessen, sondern Systemfakten im Prompt. Nachrichtentext ist also **ungeprüft**, nicht widerlegt. ⚠️ Er nennt das Asset beim Namen. Ein Rückspiel ist damit kontaminiert, gemessen werden kann nur vorwärts. Meldungen sind zudem selten.
2. **Funding für alle Futures-Paare** (live ein Abruf, Historie je Paar) und dann eine Prüfung, ob es in P-A gehört (R-R4: Aufnehmen ist ein Tausch).
3. Weitere tragende Beiträge aus der deterministischen Seite, sobald sie gemessen sind.

### 20.8 Bauplan

| Schritt | Inhalt |
|---|---|
| **N1** | Faktentexte P-U und P-A aus den Betriebsdaten, **ein Erbauer** für Betrieb und Rückspiel. Wächter: Werturteile, Konstanten, Perzentil-Einordnung, Zahlenprüfung, Anonymität |
| **N2** | Prompt, Schema und Validator zusammen, mit Version |
| **N3** | Kalibrierlauf (50), Stabilität (A/A′), Kontaminationsprobe |
| **N4** | Rückspiel 1.000–1.500 je Rolle, vier Arme, Messregel vorab, eine Auswertung |
| **N5** | Schatten live auf allen Signalen, Ende zu Ende in der gerenderten Mail |
| **N6** | Produktion: Mailblock und Charts, Hebel-Tab mit demselben Bild |
| **N7** | nachgelagert: P-T, Funding, weitere Beiträge |

### 20.9 Zur Abstimmung

| # | Frage | Vorschlag |
|---|---|---|
| **N-a** | Abdeckungskriterium: *live für alle REGEL0-Assets und in derselben Form für 2025–26*? Damit bleiben **Umfeld** und **Kurs-/Volumenstruktur** | ➤ **Ja** |
| **N-b** | Zwei Rollen **P-U** (Umfeld, einmal je Stunde) und **P-A** (Asset, anonym, je Signal); die heutige Rolle G entfällt für die REGEL0 mangels Abdeckung | ➤ **Ja** |
| **N-c** | Aus der REGEL0 bekommen die Rollen **nur den geplanten Handel** (LONG, Hebel, Ein- und Ausstieg 24 h), **nicht** deren Bewertung | ➤ **Ja**, sonst ist die Bestätigung eine Selbstbestätigung |
| **N-d** | Messung: Rückspiel mit Kontaminationsprobe, vier Arme, Messregel vorab, danach Schatten | ➤ **Ja** |
| **N-e** | **In die Produktion** geht der Block **in jedem Fall**, als Auskunft mit dem Messstand. *Trägt* er, steht dort *trennt*. *Trägt* er nicht, steht dort *trennt nicht*, und der Block wird zur reinen Beschreibung | ➤ **deine Entscheidung**. Mein Rat: ja, mit Messstand. Du wolltest ausdrücklich auch die *reine Bestätigung*, und der Vermerk verhindert, dass sie mehr wiegt, als sie trägt |
| **N-f** | Charts in der Mail und im Hebel-Tab: Kurs 5 Tage, Ein- und Ausstieg, Liquidationsgrenze je Stufe, Marken | ➤ **Ja**, als eigener Baustein. Er kann **sofort** gebaut werden, weil er nicht von der Messung abhängt |
| **N-g** | P-T (Text) und Funding nachgelagert | ➤ **Ja** |
| **N-h** | Die neuen Rollen laufen auf **gemini-3.5-flash-lite** (Messung und Betrieb gleich, dort ist das Kontingent frei) | ➤ **Ja** |


### 20.10 Abstimmung N-a bis N-h und PRÜFUNG DES ROLLENMODELLS (Nutzer 03.10.2026, Hauptentscheidung)

**Nutzer:** *„Ja N-a bis N-h wie vorgeschlagen, prüfen und gegenprüfen. Nur das neue Rollenmodell solltest du noch einmal fachlich und technisch prüfen. Wir hatten drei Rollen: Markt, Trader und Entscheider. Dies noch einmal sauber prüfen und gegenprüfen, es ist eine Hauptentscheidung."*

**N-a bis N-h sind abgestimmt.** Offen bleibt allein das Rollenmodell, das bisher in N-b stand.

#### 20.10.1 Woher die drei Rollen kommen (an der Quelle gelesen)

| Stand | Markt | Trader | Entscheider | Gegenprüfer |
|---|---|---|---|---|
| **Entwurf 10.08.** (`Rollenkonzept_Entwurf_10_08.md` §3) | **A Analyst**: einmal je Durchgang, kein Asset, Ausgabe Neigung | **B Trader**: je Asset, Aufbau und Belege, **sieht die Marktlage als Ergebnis, nicht als Rohdaten** | **C Entscheider**: Aktion und Vertrag | — |
| **10.08.** Zusammenlegung | A | **BC in EINEM Aufruf**. Nutzer: *5-faches Kontingent nicht tragbar*. Begründung: B und C *„widersprechen nicht, sie sind zwei Schritte derselben Aufgabe"*. Der ernste Einwand ist **Hedging** und gilt als **messbarer Zustand** | | — |
| **16./17.08.** R-R1 (verbindlich) | **A Marktanalyst** | **BC Händler** | | **G Gegenprüfer**: *„Spricht etwas AUSSERHALB unserer Kursdaten dagegen?"*, nur Fremdquellen, kann **nur einwenden**, nie befürworten |
| **Betrieb seit August** | A | BC schlägt die Aktion vor | die Stufe `entscheider` ist **deterministisch** (*„Trefferquote schlägt den Breakeven"*, `rollen_gate.py:125`) | G |
| **REGEL0 (E-42 F2, E-46)** | — | — | **die REGEL0 löst aus**, deterministisch | — |

➤ **Der Entscheider war im Betrieb nie ein Sprachmodell.** Mit der REGEL0 ist die Entscheidung über das Signal **deterministisch und gemessen**, und F2 hält das fest. Ein LLM-„Entscheider" kann deshalb nur eines sein: ein **Gesamturteil** über den REGEL0-Handel in der Mail. Genau das ist die *Bestätigung*, die du willst.

#### 20.10.2 Vier Modelle im Vergleich

| | **M1** (mein Vorschlag in §20) | **M2** Kette wie 10.08. | **M3** drei Rollen, Markt und Trader **unabhängig** | **M4** zwei Rollen + Regel |
|---|---|---|---|---|
| Aufbau | Markt, Trader, kein Gesamturteil | Markt → Trader (sieht das Markt-Ergebnis) → LLM-Entscheider | Markt ‖ Trader → **LLM-Entscheider** (sieht beide **Ergebnisse**, keine Rohdaten) | Markt ‖ Trader → **Zählregel** fasst zusammen |
| beantwortet *„ist der Trade gut?"* | ✗, du fasst selbst zusammen | ✔ | ✔ | ◐ mechanisch |
| R-R2 (ein Eingang je Rolle) | ✔ | ⚠️ Trader trägt den Markt mit | ✔ Markt und Trader exklusiv, der Entscheider **verbindet** nur, wie C am 10.08. | ✔ |
| **Messbarkeit** | Trader messbar, Markt nur Auskunft | ⚠️ **Trader nicht mehr sauber messbar.** Der Markt ist ein Marktzustand, für alle Assets in der Stunde gleich, und nach stehender Regel **kein Beitrag je Asset**. Effektiv zählt nur die Zahl der Regimewechsel (2.599). In der Kette färbt er den Trader und vermischt beide | ✔ **Trader rein messbar** (Querschnitt, stundentreue Nullwelt). Beim Entscheider zeigt der Vergleich mit dem Trader allein, ob er etwas hinzufügt | ✔ |
| Synthese-Regel (Memory: *ganzheitliches LLM-Urteil nicht durch Zählregel überschreiben*) | — | ✔ | ✔ | ⛔ **verletzt** als Produktionsurteil. Zulässig nur als **Vergleichsarm** der Messung |
| Fehlerrisiko | gering | Kette: A12 *(die Einstufung von A kam beim Händler nie an)*, 2.457-w8 *(fällt A aus, fällt die Gruppe aus)* | **Hedging** im Entscheider (C18) → eigenes Feld für den Gegengrund. **Anker** auf dem Trader-Urteil → Messarm *Trader allein*. Ausfall des Markts ergibt *keine Auskunft* (grau), **kein Abbruch** | gering |
| Aufrufe je Signal | 1 (+ Markt je Stunde) | 2 (+ Markt) | 2 (+ Markt) | 1 (+ Markt) |
| Laufzeit bis zur Mail | ~5 s | ~10–15 s | ~10–15 s (Median Gemini 5,5 s je Aufruf, RWM:3392) | ~5 s |

#### 20.10.3 Ergebnis der Prüfung — Empfehlung **M3**, mit dem Gegenprüfer als vierter Rolle (nachgelagert)

| Rolle | Frage | Eingabe | darf NICHT | Aufruf |
|---|---|---|---|---|
| **Markt** | *Spricht das Umfeld für oder gegen einen gehebelten 24-h-LONG in Krypto?* | Leitmärkte, Makro, Fear & Greed (Datenschicht `marktlage.py`) und der Plan **ohne** Asset | ein Asset beurteilen | **neu nur, wenn sich die Fakten ändern** (Prüfsumme). Gleiche Fakten bekommen dasselbe Urteil, gegen die gemessenen 16 % Eigenrauschen (L-4) |
| **Trader** | *Spricht die eigene Kurs- und Volumenlage DIESES Werts für oder gegen den geplanten Handel?* | **anonym**: Verlauf, Marken in ATR, Schnitte, Volumen relativ, Schwankung als Perzentil. Dazu der Plan | den Markt sehen (bleibt exklusiv und messbar), rsi/Normal sehen (Eingang der REGEL0) | je Signal |
| **Entscheider** (Gesamturteil, **entscheidet nicht über das Signal**) | *Bestätigst du diesen REGEL0-Handel?* Antwort *bestätigt / mit Vorbehalt / Einwand*, dazu Begründung und stärkster Gegengrund (getrennte Felder) | der Plan und die **Ergebnisse** von Markt und Trader (Stufe, Belege, Gegengrund), **keine Rohdaten**, **keine REGEL0-Bewertung** | das Signal kippen (F2), Hebel oder Größe wählen | je Signal, **eigener Aufruf** nach den beiden. Fehlt eine Rolle, urteilt er mit dem Vermerk *Markt fehlt* |
| **Gegenprüfer** (nachgelagert, N7) | *Spricht etwas AUSSERHALB unserer Kursdaten dagegen?* (R-R1) | **nur Fremdquellen**: Text (Meldungen), später Positionierung, sobald voll abgedeckt | befürworten (er ist einseitig), die anderen Rollen sehen (R-R2) | je Signal |

**Warum M3 und nicht M1:** M1 lässt dir das Zusammenfassen. Du hast aber ausdrücklich ein **Urteil über den Trade** verlangt (*„reine Bestätigung, dass der Trade gut ist"*). Das liefert nur ein Gesamturteil, und ein ganzheitliches Urteil gehört nach der stehenden Regel einem Sprachmodell, nicht einer Zählregel.

**Warum M3 und nicht M2:** In M2 liest der Trader das Markt-Ergebnis mit. Dann ist er nicht mehr der **messbare Beitrag je Asset**, weil ein Marktzustand ihn färbt, der für alle Assets gleich ist. Der Entwurf vom 10.08. wollte die Marktlage beim Trader. Mit einem eigenen Entscheider zieht diese Verbindung **eine Stufe weiter**, zu ihm, wie C am 10.08.

**Warum nicht M4 in der Produktion:** Eine Zählregel als *Gesamturteil* wäre die *„zweite, primitivere Bewertung"*, die die Synthese-Regel verbietet. Sie bleibt aber der **Vergleichsarm**: Der Entscheider muss sie schlagen, sonst trägt er nichts.

#### 20.10.4 Gegenprüfung — was das Modell kosten und kippen könnte

| Prüfpunkt | Ergebnis |
|---|---|
| **Kontingent** | Live: Markt nur bei geänderten Fakten (wenige je Tag), Trader und Entscheider je 12–15 Signale, also **~30–40 Aufrufe je Tag** auf gemini-3.5-flash-lite (frei ~460). ✔ |
| **Rückspiel** | Trader 1.500 + Entscheider 1.500 + Wiederholungen ~600 + Markt je verschiedenem Faktenstand (~600 Tage) ≈ **4.200 Aufrufe ≈ 9–10 Tage** bei 460 je Tag. Mit n = 1.000 je Rolle rund **7 Tage**. ⚠️ Das ist länger als in §20.5 genannt (dort für eine Rolle) |
| **Messarme Entscheider** | (1) LLM-Entscheider, (2) **Zählregel** auf denselben zwei Stufen, (3) **Trader allein**, (4) Zufall, (5) Rauschboden. *Trägt* heißt: über dem Band in beiden Jahren **und** besser als (2) **und** (3) |
| **Messarme Trader** | wie §20.5: Regel auf denselben Eingaben, Zufall, Rauschboden, vertauschte Reihenfolge |
| **Markt** | **nicht** als Beitrag messbar (Marktzustand). Gemessen werden nur Stabilität und Stufenverteilung. In der Mail steht er als **Auskunft** mit dem Vermerk |
| **Anonymität** | Der Entscheider sieht Belege mit relativen Zahlen, ohne Namen und ohne Datum. ✔ (Kontaminationsprobe gilt mit) |
| **Ausfall** | Fällt der Markt aus, folgt *keine Auskunft* und der Entscheider urteilt mit Vermerk. Fällt der Trader aus, entfällt der Entscheider, und die Mail geht ohne Block raus (P-8). **Kein** Abbruch der Mail (Lehre 2.457-w8) |
| **Namen** | Im Code `regel0_llm_markt`, `regel0_llm_trader`, `regel0_llm_entscheider`, damit nichts mit der deterministischen Stufe `entscheider` der Spot-Kette verwechselt wird (`rollen_gate.py`) |

#### 20.10.5 Zur Abstimmung

| # | Frage | Vorschlag |
|---|---|---|
| **R-1** | **Rollenmodell M3**: Markt und Trader unabhängig, dazu ein LLM-Entscheider als **Gesamturteil** über den REGEL0-Handel (er kippt nichts), der Gegenprüfer mit Fremdquellen nachgelagert. Das ersetzt N-b | ➤ **Ja** |
| **R-2** | Der Markt wird nur bei **geänderten Fakten** neu gefragt | ➤ **Ja** |
| **R-3** | Rückspiel mit **fest** n = 1.000 je Rolle, ausgewertet **einmal** | ➤ **Ja.** Das reicht für 1 Prozentpunkt (L-5). ⚠️ **Kein Aufstocken nach einem Zwischenblick.** Ich hatte es zuerst vorgeschlagen, es wäre aber Mehrfachtesten (F19: kleine Stichproben erzeugen Scheinbefunde in die erwartete Richtung) |
| **R-4** | **Spot-Kette zum Rückspiel stilllegen** (siehe 20.10.6), mit einem **eigenen** Schalter, der **nicht** auf den alten Weg zurückfällt | ➤ **Ja**, ich sage Bescheid, bevor N4 startet |

#### 20.10.6 Nutzerhinweis: Stilllegung der Spot-Kette für die LLM-Ressourcen

**Nutzer:** *„Wenn wir LLM-Ressourcen benötigen, wäre eine Stilllegung der aktuellen Kette sogar ein Vorteil. Wenn nicht, gib Bescheid, wenn es so weit ist, dass ich die Produktion für LLM-Tests stoppe."*

| | |
|---|---|
| **Brauchen wir sie?** | **Ja, für das Rückspiel (N4).** Das Kontingent hängt am **Schlüssel**, nicht am Gerät: Ein Lauf am Desktop verbraucht das Budget des NB (Memory *gemini_limits*). Die Spot-Kette braucht auf gemini-3.1-flash-lite 320–450 Aufrufe je Tag. Ist 3.1 erschöpft, weicht sie auf **3.5** aus (30.09.: 39 Aufrufe). Das ist genau das Modell, auf dem wir messen. Ein Rückspiel mit vollem Tempo auf 3.5 könnte damit die Spot-Kette lahmlegen, und eine laufende Spot-Kette die Messung |
| **Wirkung** | Ohne Spot-Kette ist 3.5 **ganz** frei (500 je Tag). Das Rückspiel (~4.200 Aufrufe) ist dann in **rund 9 Tagen** sicher durch, ohne Deckel-Rechnerei und ohne Störung. Ein zweites Modell zu nehmen, um es schneller zu machen, ist **nicht** zulässig (E1: ein Befund überträgt sich nicht zwischen Modellen) |
| ⚠️ **Wie NICHT** | `rollen_kette.aktiv_fuer` leeren. Dann **übernimmt der alte Weg wieder** (`rollen_job.py:48-63`, *„der dokumentierte Rückfallweg"*), mit Budget-Allocator und alter Pipeline. Das wäre das Gegenteil einer Stilllegung |
| **Wie** | ein **eigener Schalter** in `Basisinfos/regel0_betrieb.yaml`, der die Spot-Rollen-Kette anhält, ohne den alten Weg freizugeben. Vorher die Prüfung *Stilllegung: wer schreibt das noch?*: Bestandsmails, Stop-Nachzieh-Sammelmail (sie hängt an **offenen** Signalen und läuft weiter), Führungsprotokoll, Ausstiegsverfolgung, Hebel-Tab. Die REGEL0 und ihre Mails sind davon **nicht** berührt |
| **Wann** | **vor N4** (Rückspiel). N1 bis N3 (Erbauer, Prompt, Kalibrierlauf mit 50 Ankern) gehen ohne Stilllegung. ➤ **Ich gebe Bescheid**, bevor N4 startet, mit der fertigen Prüfung, was stillsteht |


### 20.11 Abstimmung R-1 bis R-4 und das ROLLENMODELL M3 zum Nachlesen (Nutzer 03.10.2026)

**Nutzer:** *„Ja R-1 bis R-4 wie vorgeschlagen, prüfen und gegenprüfen. Wichtig: Das Rollenmodell soll beim Testen und Simulieren u. U. noch einmal geprüft und angepasst werden können. Ich kann zum aktuellen noch zu wenig sagen, u. U. kannst du mir das noch in der Voranalyse fachlich und technisch sauber vorlegen."*

**R-1 bis R-4 sind abgestimmt (E-51).** M3 ist damit die **Startfassung**, keine endgültige. Unten steht, wie das Modell arbeitet, an einem Beispiel, wo es angepasst werden kann und nach welchen Regeln das geschieht.

#### 20.11.1 Der Ablauf in einem Bild

```
REGEL0 (deterministisch, gemessen)  ── löst aus: Asset X, LONG, Hebel 3×, Einstieg 14:00, Ausstieg +24 h
        │
        ├──► DER PLAN (für alle Rollen gleich): "gehebelter LONG, Hebel 3×, Ausstieg nach 24 h, kein Stop, kein Ziel"
        │
        ├──► MARKT      Eingabe: Leitmärkte, Makro, Stimmung            (für alle Assets gleich)
        │               Ausgabe: stützt | neutral | spricht dagegen  + Beleg + Gegengrund
        │               neu nur, wenn sich seine Fakten ändern
        │
        ├──► TRADER     Eingabe: NUR die eigene Kurs-/Volumenlage von X, anonym
        │               Ausgabe: stützt | neutral | spricht dagegen  + Beleg + Gegengrund
        │
        └──► ENTSCHEIDER  Eingabe: der Plan + die ERGEBNISSE von Markt und Trader (keine Rohdaten)
                          Ausgabe: bestätigt | mit Vorbehalt | Einwand  + Begründung + stärkster Gegengrund
                               │
                               ▼
        MAIL: der deterministische Teil (wie heute) + Block PRÜFUNG (drei Urteile + Messstand) + CHART
        ⚠️ Kein Urteil ändert das Signal (F2). Die REGEL0 hat schon entschieden.
                          (nachgelagert: GEGENPRÜFER mit Fremdquellen, nur Einwand)
```

#### 20.11.2 Jede Rolle fachlich: was sie kann und was nicht

| | **Markt** | **Trader** | **Entscheider** |
|---|---|---|---|
| **Zweck in einem Satz** | Sagt, ob das **Umfeld** einen gehebelten Kurzzeit-LONG trägt | Sagt, ob **dieser Wert** in seiner eigenen Lage einen solchen Handel trägt | Wägt beide Urteile **gegeneinander ab** und sagt, ob er den Handel bestätigt |
| **Was er sieht, die REGEL0 aber nicht** | Leitmärkte, Makro, Fear & Greed | Marken, Verlauf über Wochen, Volumen, Lage zu den Schnitten | nichts Neues. Er **verbindet** zwei Sichten, die die REGEL0 beide nicht hat |
| **Was er NICHT sieht** | kein Asset, keine REGEL0-Zahl | keinen Markt, keinen Namen, kein Datum, kein rsi, keine REGEL0-Zahl | keine Rohdaten, keine REGEL0-Zahl |
| **Warum so getrennt** | Ein Marktzustand ist für alle Assets gleich. Er darf den Trader nicht färben, sonst ist der Trader nicht mehr messbar | Nur so ist er der **messbare Beitrag je Asset** (Querschnitt in derselben Stunde) | Ein ganzheitliches Urteil gehört einem Modell, nicht einer Zählregel (Synthese-Regel). Ob es mehr leistet als eine Zählregel, misst der Vergleichsarm |
| **Messbar als** | **nur Auskunft** (Stabilität, Verteilung). Als Beitrag nicht, weil er ein Marktzustand ist | **Beitrag:** trennt *stützt* gegen *spricht dagegen* den 24-h-Ausgang? | **Beitrag über dem Trader:** trennt er besser als der Trader allein und als die Zählregel? |
| **Bekannte Gefahr** | 16 % Eigenrauschen bei gleichen Fakten (L-4). Dagegen hilft, ihn nur bei geänderten Fakten neu zu fragen | Positionsbias (Reihenfolge der Sätze). Dagegen der Arm mit vertauschter Reihenfolge | **Anker** auf dem Trader-Urteil, **Hedging** (*„ja, aber …"*). Dagegen das eigene Feld für den Gegengrund und der Arm *Trader allein* |

#### 20.11.3 Ein Beispiel, wie es in der Mail aussähe (⚠️ ausgedacht, keine Messwerte)

```
PRÜFUNG DURCH DIE ROLLEN  (Auskunft - löst nichts aus; Messstand: noch nicht gemessen)

  Markt        neutral          Fear & Greed im 74. Perzentil (hoch), US-Aktien 1,6 Std.-Abw. über Trend;
                                Gegengrund: die Netto-Liquidität sinkt seit 26 Wochen
  Trader       stützt           Kurs 0,4 ATR über der Unterstützung (9-mal berührt), Volumen der letzten
                                20 Tage im 71. Perzentil; Gegengrund: nächster Widerstand nur 0,9 ATR höher
  Entscheider  mit Vorbehalt    Der Wert steht gut, das Umfeld trägt nicht mit; der Widerstand nahe dem
                                Einstieg begrenzt den 24-h-Spielraum

  [Chart: Stundenkurs 5 Tage, Einstieg ▲, Ausstieg nach 24 h ▼, Liquidationsgrenze 3×, Marken]
```

Darüber steht wie heute der deterministische Teil: Asset, Einstieg, Ausstieg, Hebel, Einsatz, Liquidationsgefahr. **Beides steht getrennt**, und du siehst, was gerechnet und was beurteilt ist.

#### 20.11.4 Technisch: wie das Modell gebaut wird, damit es anpassbar bleibt

| Baustein | Inhalt |
|---|---|
| **Rollenkatalog** `Basisinfos/regel0_llm.yaml` (neu) | je Rolle: an/aus, Modell, Prompt-Fassung, **Satzbausteine** der Eingabe (einzeln zuschaltbar), Eingänge des Entscheiders (welche Ergebnisse er sieht). Eine Änderung hier ist **eine neue Fassung** mit Nummer |
| **Ein Erbauer** je Rolle (`agent/regel0_llm_*.py`) | baut die Eingabe aus den Betriebsdaten, **derselbe Code** für Betrieb und Rückspiel. Es gibt also keine zweite Messgeometrie |
| **Ablage** `regel0_signale.db`, neue Tabelle `pruefung` | je Signal und Rolle: Fassung, Prompt-Prüfsumme, Eingabe-Prüfsumme, Eingabetext, Antwort, Urteil, Laufzeit, Fehler. Jedes Urteil ist damit einer Fassung zuordenbar |
| **Wächter** (Suite) | keine Werturteile, keine konstanten Felder, Perzentil mit Einordnung, **Anonymität** (kein Name, kein Datum, kein absoluter Kurs), **kein Satzbaustein in zwei Rollen** (R-R2), Schema = Validator |
| **Rückspiel** | ein eigener Lauf, der dieselben Erbauer auf den REGEL0-Einstiegen 2025–26 anwendet. Er schreibt nur in eine **Wegwerf-Ablage** |
| **Schalter** | Mail-Block an/aus, je Rolle an/aus, **Spot-Kette angehalten** (eigener Schalter, nicht `aktiv_fuer`) |

➤ **Anpassen heißt dann:** einen Baustein zu- oder abschalten, eine Rolle an- oder ausschalten, die Eingänge des Entscheiders ändern, oder zur Kette M2 oder zu den zwei Rollen M1 wechseln. Alles das ist eine **Zeile im Rollenkatalog**, kein Umbau.

#### 20.11.5 Wann geprüft und angepasst wird, und nach welchen Regeln (vorab festgelegt)

⚠️ **Die Gefahr beim Anpassen:** Wer nach dem ersten Ergebnis die Rollen ändert und **auf denselben Ankern** erneut misst, findet irgendwann zufällig eine Fassung, die trägt (Mehrfachtesten, F19). **Deshalb werden die REGEL0-Einstiege 2025–26 vorab geteilt:**

| Menge | Zweck |
|---|---|
| **Entwicklungsmenge** (1.000 je Rolle) | hier wird gemessen und angepasst, so oft wie nötig. Jeder Versuch wird gezählt (Versuchszähler) |
| **Bestätigungsmenge** (1.000 je Rolle, **unberührt**) | hier wird **einmal** gemessen, mit der **endgültigen** Fassung. Nur dieses Ergebnis steht in der Mail als Messstand |

| Prüfpunkt | Was geprüft wird | Folge, vorab festgelegt |
|---|---|---|
| **P1 nach dem Kalibrierlauf** (50 Anker, N3) | Antworten formgültig (≥ 95 %)? Je Rolle **keine Stufe über 70 %** (der heutige Marktanalyst sagt zu 72 % *gemischt* und unterscheidet damit nichts)? Wiederholung gleich (≥ 90 %, gemessen beim heutigen Marktanalysten: 84 %)? Anonym (0 Treffer, wenn das Modell Asset oder Zeitraum nennen soll)? | Fällt ein Punkt durch: Eingabe oder Prompt der Rolle anpassen (neue Fassung) und P1 wiederholen. Erst dann folgt das Rückspiel |
| **P2 nach dem Rückspiel** (Entwicklungsmenge, N4) | Trägt der **Trader**? Trägt der **Entscheider** über Trader und Zählregel? | **T ✔, E ✔:** M3 bleibt. **T ✔, E ✗:** Der Entscheider fällt weg oder wird reine Beschreibung, das ergibt M1. **T ✗, E ✔:** Verdacht auf Zufall, der Entscheider wird erst vorwärts bestätigt. **T ✗, E ✗:** Der Block bleibt **Auskunft** mit *trennt nicht* (N-e). Es wird nicht weiter am Prompt gefeilt, der nächste Hebel ist **neue Information** (Gegenprüfer mit Text) |
| **P2b Kontaminationsprobe** | Erkennt das Modell Asset oder Zeitraum? Trennt die benannte Fassung besser? | Fällt sie durch: **nur noch vorwärts** messen (Schatten, N5) |
| **P3 Bestätigung** (unberührte Menge) | die **endgültige** Fassung, einmal | Dieses Ergebnis ist der Messstand in der Mail |
| **P4 nach 3 Monaten Schatten** (N5) | Verteilung und Trennung live wie im Rückspiel? | Abweichung bedeutet Drift. Kanarienvogel und Ursache prüfen, bevor etwas geändert wird |

**An jedem Prüfpunkt lege ich dir das Ergebnis vor**: was gemessen wurde, was die vorab festgelegte Folge ist, und ob ich eine Änderung am Rollenmodell vorschlage. Eine Änderung am Rollenmodell selbst (M3 → M1, M2 oder eine neue Rolle) entscheidest **du**.

#### 20.11.6 Was das kostet, wenn angepasst wird

| | Aufrufe | auf gemini-3.5, Spot-Kette angehalten (500 je Tag) |
|---|---|---|
| Kalibrierlauf je Fassung | ~200 | < 1 Tag |
| Rückspiel Entwicklungsmenge | ~4.200 | ~9 Tage |
| jede weitere Fassung (nur die geänderte Rolle) | ~1.500–2.500 | 3–5 Tage |
| Bestätigung (einmal) | ~4.200 | ~9 Tage |

⚠️ **Ehrlich:** Mit Anpassungen sind es eher **3–5 Wochen** bis zur gemessenen Fassung in der Mail. **Vorher** kann der Block schon **live im Schatten** mitlaufen (N5), und die **Charts** gehen sofort in die Mail, weil sie von keiner Messung abhängen.


### 20.12 BAU der Sofortfassung, Charts und Kalibrierlauf P1 (03.10.2026; E-52)

**Nutzer:** *„Ok, Charts und N1 bauen, prüfen und gegenprüfen. Zur Dauer: Hier brauchen wir eine Sofortlösung (Simulation etc.), mit dieser gehen wir in die Produktion, und die adaptierte und gemessene Lösung muss später final kommen."* Dazu *„optimal wäre dann ein selbstjustierendes System"* (→ Plan O21) und *„berücksichtige auch die Erfahrungen der Quellenabfrage für die LLM-Kette, damit es keinen Ressourcen- und Abfragestau gibt"*.

#### Gebaut

| Baustein | Inhalt |
|---|---|
| **Charts** (N-f), `agent/regel0_chart.py` | Stundenkurs 5 Tage, Signal, Einstieg ▲, Ausstieg nach 24 h, Liquidationsgrenze je Stufe mit Preis und Abstand in %. Die Achse folgt dem Kurs, Zeiten in Ortszeit. **Dasselbe Bild** in der Signalmail (eingebettet über `inline_images`) und im Hebel-Tab. Die Liquidationsformel ist dieselbe wie in der Messung (`messe_k6_hebelstufe.liq_schwelle`, Marge 0,09, Finanzierung 0,0018), eine Wache hält beide gleich. `regel0_mail.versende` hat jetzt optional `bild` und `pruefung`. Scheitert eines davon, geht die Mail trotzdem raus (P-8) |
| **Rollenkatalog** `Basisinfos/regel0_llm.yaml` | Fassung, Modell gemini-3.5-flash-lite, Temperatur 0, Rollen an/aus, Satzbausteine des Traders, Eingänge des Entscheiders, Zeitgrenzen und Riegel |
| **LLM-Ebene** `agent/regel0_llm.py` | **Markt:** Datenschicht `marktlage` (Leitmärkte, Makro, Stimmung), alles aus **einer** Datenbank, neu nur bei geänderten Fakten (Prüfsumme). **Trader:** anonym, 24-h-Kerzen bis zur Signalstunde, Bausteine aus `lagebeschreibung`. **Entscheider:** nur die Ergebnisse. Validierung: das Urteil wird **nie geraten**, Belege gekürzt, Zahlendeckung gezählt. Anonymitätswächter (Name, Jahr, Kurs). Mailblock *SOFORTFASSUNG, UNGEMESSEN*. Ein Ausfall erscheint als *keine Auskunft* |
| **Kein Ressourcen- und Abfragestau** (`Umlauf`) | **kein** Nebenfaden, alles nacheinander im Stundenjob. **Derselbe** Gemini-Client wie die Spot-Kette (eine Minutendrossel, Tagesbudget je Modell). Eigenes **Tageslimit 150** (in der Ablage gezählt, kein Schreiben in die Produktion), **höchstens 6 Signale je Lauf**, **600 s je Lauf**, **90 s je Signal**. Nach **3 Fehlern in Folge** fragt der Lauf nicht mehr. Ein Kontingent, das schon erschöpft ist, wird vorher erkannt. Lehren: 2.454-gemini (34× HTTP 503), G19 (Warteschlange länger als der Hauptfaden), `zweite_meinung.AUSFALL_SCHWELLE` |
| **Ablage** | Tabelle `pruefung` in `regel0_signale.db`: je Signal und Rolle Fassung, Prompt- und Eingabe-Prüfsumme, Eingabe, Antwort, Urteil, Laufzeit, Fehler, ungedeckte Zahlen, Pazifik-Tag |
| **Verdrahtung** | `_regel0_mails`: **ein** Umlauf je Stundenlauf. Der Gemini-Client kommt aus `build_scheduler` (`_regel0_llm_client_ref`). Der Prüfblock gilt nur für die **Signal**mail. Der Hebel-Tab zeigt Prüfblock und Chart im Detail (nur gelesen) |
| **Teilexport** | Abschnitt *REGEL0-PRUEFUNG (LLM)*: Aufrufe je Tag, Urteile je Rolle, Ausfälle, Laufzeit |
| **Wache** `--paket Regel0Betrieb` | **45 von 45**. Neu: Chart = Messformel; Mail mit Bild und Block, beides darf scheitern; Rollenkatalog; nur der Plan aus der REGEL0; Trader anonym ohne rsi und ohne Markt (mit Gegenprobe); das Urteil wird nie geraten; Markt wird wiederverwendet; Abbruch nach 3 Fehlern; Mailblock *ungemessen*; Verdrahtung |
| **Kalibrierlauf** `Basisinfos/Rechenkern_02_10/kalibrier_llm.py` | 50 REGEL0-Einstiege 2026 (Spur, feste Saat), **echte** Aufrufe auf gemini-3.5, Deckel 260. Prüft P1-a bis P1-e und schreibt eine HTML-Mailvorschau. Er schreibt **nicht** in die Standard-DB (Wegwerf-DB, am Seiteneffekt geprüft) |

#### Kalibrierlauf P1 der Fassung 0.1 — ⛔ NICHT bestanden (nach 10 von 50 Ankern angehalten, um das Kontingent zu schonen)

| Rolle | Verteilung (10 Anker) | P1-b (keine Stufe über 70 %) |
|---|---|---|
| Trader | 9× *spricht dagegen*, 1× *neutral* | ⛔ 90 % |
| Entscheider | 8× *Einwand*, 2× *mit Vorbehalt* | ⛔ 80 % |
| Markt | 5× *spricht dagegen*, 4× *neutral*, 1× *stützt* | ✔ 50 % |

Laufzeit je Aufruf: Trader 5,8 s, Markt 6,2 s, Entscheider 1,1 s. Alle Antworten waren formgültig.

⛔ **Die Ursache ist fachlich, aus den Begründungen gelesen:** Die REGEL0 kauft **nach einem Rückgang** (rsi-Ersteintritt), sie setzt also auf eine **Gegenbewegung**. Die Rollen wussten das nicht und beurteilten einen **Trendhandel**: *„steht im Widerspruch zum intakten Abwärtstrend"*. Die Gegenbewegung nannten sie selbst nur als *Gegengrund* (*„Short Squeeze"*, *„Kontraindikator"*). Dazu kommt ein **Echo** (R-R2): Verlauf über 5 und 20 Tage und Abstand zum 20/50-Tage-Schnitt sind fast dieselbe Information wie der rsi, nur mit umgekehrtem Vorzeichen gelesen.

#### Fassung 0.1b (die vorab festgelegte Folge von P1: anpassen, neue Fassung, P1 wiederholen)

| | 0.1 | 0.1b |
|---|---|---|
| Plan | *gehebelter Kauf, ohne Stop und ohne Kursziel* | *Kauf auf eine **Gegenbewegung nach einem Rückgang**, Hebel n-fach, 24 h; Hebel und Risiko werden gesondert gerechnet; zu beurteilen ist nur, ob die Gegenbewegung in diesen 24 Stunden trägt* |
| Trader-Bausteine | Struktur, Verlauf 5/20/60, Marken, Schnitte 20/50/200, Schwankung, Volumen | Struktur, **lange Sicht** (60 Tage, 200-Tage-Schnitt), Marken, Schwankung, Volumen. **Ohne** die rsi-Spiegel |
| Frage | *stützt die Lage den Handel?* | *spricht die Lage dafür, dass **die Gegenbewegung** in 24 h trägt?* |

⚠️ **Das erweitert N-c leicht:** Aus der REGEL0 kommt jetzt auch, **worauf** der Handel setzt. Das gehört zum Plan, wie der Horizont. Es ist keine Zahl und keine Güte der REGEL0. Zur Bestätigung beim Nutzer.

**Zwischenstand 0.1b nach 10 Ankern:** Markt 6× *stützt*, 4× *neutral*. Trader 8× *spricht dagegen*, 2× *neutral*. Entscheider 5× *Einwand*, 5× *mit Vorbehalt*. ➤ Der Markt unterscheidet jetzt. Der **Trader bleibt fast konstant** und fällt P1-b voraussichtlich wieder. Das volle Ergebnis steht unten (20.12.1), sobald der Lauf fertig ist.

#### ⚠️ Fund nebenbei: Makro am Desktop und am NB verschieden

`rollen_eingabe.baue_lagebild_eingabe` liest Stimmung und Makro **immer** aus dem Standardpfad. Im Rückspiel kamen so Kurse aus der NB-Kopie und Makro aus der Desktop-DB. Die Werte unterscheiden sich deutlich, zum Beispiel Fear & Greed im 90. gegen das 68. Perzentil am selben Tag. Im **Betrieb am NB** ist das unschädlich (eine Datei). Der LLM-Erbauer liest jetzt **alles aus einer** Datenbank. ➤ **Für das Rückspiel (N4) zu prüfen:** Enthalten die Makroreihen nur Werte, die zum Ankerdatum schon bekannt waren? *1.186 gegen 1.184 Monate* ist nicht von selbst erklärt.

#### Nächste Schritte

1. Ergebnis 0.1b auswerten. Bleibt der Trader konstant, folgt der nächste Schritt nach P1: die Eingabe des Traders weiter auf das ausrichten, was **eine Gegenbewegung** trägt oder bricht. Das sind etwa Marken unter dem Kurs, Volumen im Rückgang und die Struktur. Danach P1 erneut.
2. Sobald P1 bestanden ist: volle Suite, Commit, NB-Pull, Kontrolle **K-LLM-1** (erste Signalmail mit Block und Chart, Teilexport *REGEL0-PRUEFUNG*).
3. Vor N4: Schalter zum Anhalten der Spot-Kette (R-4), Prüfung der Makroreihen auf Zeitpunkttreue, Teilung in Entwicklungs- und Bestätigungsmenge.


#### 20.12.1 Ergebnis P1 über drei Fassungen (03.10.2026; Belege `Basisinfos/Rechenkern_02_10/kalibrierung_0_1b.txt`, `kalibrierung_0_1c.txt`)

| Prüfpunkt | 0.1 (10 Anker) | 0.1b (50) | **0.1c (20)** | Ziel |
|---|---|---|---|---|
| P1-a formgültig | 100 % | 100 % | **100 %** | ≥ 95 % ✔ |
| P1-c Wiederholung gleich | – | 65 % (15/23) | **89 % (8/9)** | ≥ 90 % ◐ |
| P1-b Trader, größte Stufe | 90 % dagegen | 60 % dagegen | **70 % dagegen** | ≤ 70 % ✔ knapp |
| P1-b Entscheider | 80 % Einwand | 60 % mit Vorbehalt | **75 % mit Vorbehalt** | ⛔ |
| P1-b Markt (über verschiedene Tage) | 50 % | 72 % stützt | **82 % stützt** | ⛔ |
| P1-d Anonymität | – | 0 Funde, 0 von 12 erkannt | (nicht wiederholt) | ✔ |

**0.1c = Selbstkonsistenz:** drei Aufrufe je Rolle, das Mehrheitsurteil zählt, ohne Mehrheit steht *uneinig* (wird nie geraten). Der Entwurf vom 10.08. hatte das gestrichen, mit der Bedingung, es zu messen, wenn eine Rolle schwankt. Die Bedingung war mit 65 % erfüllt.

**Einordnung:**
- Die Mehrheit **stabilisiert** (65 % → 89 %), **verdichtet** aber auf die häufigste Antwort.
- **Markt:** Die Anker 2026 (Februar bis August) stammen aus **einer** langen Angstphase. Der Markt liest die Furcht als Chance auf eine Gegenbewegung und sagt fast immer *stützt*. Für einen **Marktzustand** kann das richtig sein. P1-b ist für ihn erst über **mehrere Marktphasen** prüfbar (z. B. 2025 dazunehmen).
- **Entscheider:** Er vereint einen fast immer positiven Markt mit einem überwiegend negativen Trader und landet deshalb meist bei *mit Vorbehalt*. Er erbt also die Konstanz des Markts.
- **Die eigentliche Information** steckt im **Trader**-Urteil und in den Begründungen und Gegengründen.

**Stand und Vorgehen (bis zur Nutzerentscheidung):**
- `mail_block: false`, **`schatten: true`**. Der Block wird bei jeder Signalmail **berechnet und in der Ablage gespeichert**, steht aber **nicht** in der Mail. So sammeln wir ab dem Pull echte Live-Urteile. Einschalten ist eine Zeile im Rollenkatalog.
- Die **Charts** gehen sofort in die Mail, weil sie von keiner Messung abhängen.
- Wache **47 von 47** (neu: Mehrheitsregel, Schatten ändert die Mail nicht).
- **Kontingent:** 3.5 am 03.10. mit rund 415 von 500 Aufrufen nahezu erschöpft. Weitere Kalibrierläufe gehen ab 09:00 Uhr Ortszeit (Pazifik-Mitternacht).

**Zur Entscheidung beim Nutzer:**

| # | Frage | Vorschlag |
|---|---|---|
| **K-a** | Block **jetzt** in die Mail (Fassung 0.1c, *ungemessen*), obwohl P1-b bei Markt und Entscheider nicht erfüllt ist? | ➤ **Erst Schatten, dann einschalten.** Nach einem Kalibrierlauf mit Ankern aus **2025 und 2026**: Unterscheidet der Markt über Phasen, ist er kein Defekt |
| **K-b** | Den Entscheider in 0.1d nur auf den **Trader** stützen und den Markt als Auskunft daneben stellen? | ➤ prüfen, wenn K-a zeigt, dass der Markt auch über Phasen konstant bleibt |
| **K-c** | Die Rollen kennen jetzt auch, **worauf** der Plan setzt (*Gegenbewegung nach Rückgang*). Ist das als Teil des Plans in Ordnung (Erweiterung von N-c)? | ➤ **Ja.** Ohne diese Angabe beurteilten die Rollen einen anderen Handel |
