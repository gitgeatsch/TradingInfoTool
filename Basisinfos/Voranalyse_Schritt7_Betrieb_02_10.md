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
