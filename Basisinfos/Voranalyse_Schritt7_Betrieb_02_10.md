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


#### 20.12.2 Der Markt über Marktphasen, Fassung 0.1d (03.10.2026; Nutzer: *„prüfe ob deine Fragen Entscheidungen für mich sind oder aus der Fachlichkeit beantwortet werden sollten. K-a ja, Prüfblock so schnell wie möglich kalibrieren"*)

**Einordnung der Fragen K-a bis K-c:**

| Frage | gehört | Antwort |
|---|---|---|
| K-a | dem Nutzer nur beim **Tempo** (so schnell wie möglich). Das **Einschalten** folgt aus P1 | sofort kalibrieren; eingeschaltet wird, wenn P1 besteht |
| K-b | der **Fachlichkeit**, als vorab festgelegte Folge | umgesetzt, siehe unten |
| K-c | der **Fachlichkeit**: durch P1 gemessen begründet | bleibt. Der Plan nennt die Gegenbewegung |

**Markt über Phasen** (`Basisinfos/Rechenkern_02_10/kalibrier_markt.py`, Beleg `kalibrierung_markt_phasen.txt`): ein Anker je Monat von 2025-01 bis 2026-08, drei Stimmen, 60 Aufrufe, Standard-DB unberührt.

| | stützt | neutral | uneinig |
|---|---|---|---|
| 2025 (nahe am Hoch) | 10 | – | 2 |
| 2026 (Angstphase) | 7 | 1 | – |
| gesamt | **85 %** | 5 % | 10 % |

⛔ **Der Markt unterscheidet nicht.** Er sagt in jeder Phase *stützt* und begründet es jeweils passend: 2025 *„intakter Aufwärtstrend nahe an den Höchstständen"*, 2026 *„extreme Furcht schafft günstige Voraussetzungen"*. Das ist eine Rechtfertigung im Nachhinein, keine Prüfung. Als Urteil ist es eine Konstante (R-T6).

**Fassung 0.1d (Folge K-b):**
- Der **Markt** steht nur als **Auskunft** in der Mail, mit Begründung und Gegengrund, aber **ohne Urteilswort**. Darunter steht ein Vermerk zum Grund. Das passt zur Nutzervorgabe *übergeordnete Kräfte gewichtet der Nutzer selbst*.
- Der **Entscheider** sieht nur noch den **Trader**, mit einem eigenen Prompt (*ein Prüfer*).
- Wache **48 von 48**.

⚠️ **Fachlicher Hinweis zum Rollenmodell:** Ein Entscheider, der nur den Trader sieht, hat keine eigene Information. Er kann ein **Echo** des Traders sein (R-R2). Der nächste Kalibrierlauf misst das mit dem **Echo-Maß**: Wie oft folgt der Entscheider der Richtung des Traders? **Vorab festgelegt:** Über 90 % heißt, er fügt nichts hinzu. Das Modell wäre dann faktisch M1 (Trader und Umfeld als Auskunft). Diese Änderung am **Rollenmodell entscheidet der Nutzer**, und zwar erst mit der Zahl.

**Nächster Kalibrierlauf** (bereit, ab 09:00 Ortszeit, wenn das Gemini-Kontingent zurückgesetzt ist): `KAL_JAHRE=2025,2026 KAL_OHNE_MARKT=1`, 40 Anker gleich verteilt auf beide Jahre, Trader und Entscheider mit je drei Stimmen, Wiederholung, Echo-Maß. Etwa 300 Aufrufe.


### 20.13 Vorbereitet, solange das Kontingent ruht (03.10.2026; Nutzer: *„bin unterwegs für heute und morgen, werden wir mit diesem auskommen. Bereite alles vor bzw. was wir sonst noch machen können"*)

| Baustein | Inhalt | Prüfung |
|---|---|---|
| **R-4 Schalter zum Anhalten der Spot-Kette** | `Basisinfos/regel0_betrieb.yaml: spot_kette_angehalten` (Vorgabe **false**, die Kette läuft). Mit **true** läuft die Rollen-Kette nicht. Angehalten wird im *umgestellt*-Zweig von `hebel_screening_job`, **vor** `fuehre_umlauf`. Der alte Weg (Budget-Allocator) übernimmt **nicht**, `aktiv_fuer` bleibt unberührt. Unlesbar bedeutet *läuft* (ein stiller Halt der Produktion wäre der schlimmere Fehler) | Wache: Vorgabe, unlesbar und Reihenfolge Zweig < Halt < Umlauf < alter Weg. ➤ **K-R4** am NB, wenn er gesetzt wird: Logzeile *Rollen-Kette ANGEHALTEN*, keine Zeile *Rollen-Kette krypto/spot*, kein Budget-Allocator |
| **Was bei einem Halt nicht mehr entsteht** (Stilllegungsprüfung) | Spot-Signale aller Gruppen, Spot- und Bestands-Verkaufsmails der Rollen-Kette, Lagebilder (alte Rolle A), Z.ai-Gegenprüfung, die **alte Führung echter Hebelpositionen**. Für REGEL0-Positionen gilt ohnehin der Ausstieg nach 24 h (O13) | Was **weiterläuft**: die REGEL0 (Nachlader, Rechnung, Mails, Charts, LLM-Block, denn dessen Markt-Erbauer liest Makro und Stimmung aus eigenen Jobs, nicht aus den Lagebildern), Hebel-Screening, Bitpanda-Abgleich, der Ausstiegsjob (Stop-Nachzieh-Sammelmail auf offenen Signalen), Backward-Tracking |
| **Zeitpunkttreue der Makroreihen** (vor N4) | ⚠️ `makro_historie_monat` führt den **laufenden** Monat (S&P als Teilmonat). In einer späteren Sicherung stünde für einen Anker vom 13.09. schon der Monatsschluss September, ein **Vorgriff** von bis zu einem Monat. Die Inflation ist harmlos: Sie bleibt leer, bis sie veröffentlicht ist. ➤ Der Markt-Erbauer nimmt Monatswerte nur noch aus **abgeschlossenen** Monaten, im Betrieb **und** im Rückspiel gleich. Beim Anker 13.09. sind es jetzt 1.185 statt 1.186 Monate | Wache: Nachweis am Verhalten, mit einem Monatswert aus der Zukunft in der Eingabe. Der Markt-Lauf über Phasen (85 % *stützt*) lief noch mit dem kleinen Vorgriff; an der Aussage *konstant* ändert das nichts |
| **Anker des Rückspiels eingefroren** | `ziehe_n4_anker.py`: aus 7.376 REGEL0-Einstiegen 2025–26 je **1.000** für die Entwicklungsmenge und die **unberührte** Bestätigungsmenge, je Jahr 500, 113 Symbole, disjunkt. Die 80 Kalibrieranker sind *gesehen* und stehen nur in der Entwicklungsmenge. Beleg `n4_anker_beleg.txt` mit SHA-256 | Der Kalibrierlauf sperrt die Bestätigungsmenge aus |
| **Kalibrierlauf P1 für 0.1d** (bereit) | ab 09:00 Uhr Ortszeit (Gemini-3.5-Kontingent): `KAL_ANKER=40 KAL_JAHRE=2025,2026 KAL_OHNE_MARKT=1 KAL_WIEDER=6 KAL_RATEN=0 KAL_DECKEL=330 python Basisinfos/Rechenkern_02_10/kalibrier_llm.py <NB-Sicherung> <ordner>`. Er misst P1-b bei Trader und Entscheider, P1-c, und das **Echo-Maß** (folgt der Entscheider dem Trader zu über 90 %, ist er ein Echo, und M1 liegt zur Nutzerentscheidung vor). Besteht P1, wird `mail_block: true` gesetzt | – |

#### 20.12.3 Kalibrierlauf P1 der Fassung 0.1d (04.10.2026; Beleg `Basisinfos/Rechenkern_02_10/kalibrierung_0_1d.txt`)

Der Lauf war als geplante Aufgabe für 09:10 eingerichtet. Diese Sitzung hing beim ersten Befehl, vermutlich an einer unbeantworteten Freigabe-Rückfrage, und rief Gemini nicht auf. Sie wurde angehalten, und der Lauf wurde in der Hauptsitzung gestartet. 40 Anker aus 2025 und 2026, gleich verteilt, die Bestätigungsmenge ausgesperrt. Trader und Entscheider mit je drei Stimmen, der Markt nicht gefragt (schon gemessen). 258 Aufrufe, Standard-DB unberührt.

| Prüfpunkt | Ergebnis | Ziel | |
|---|---|---|---|
| P1-a formgültig | 100 % (Trader, Entscheider) | ≥ 95 % | ✔ |
| P1-b Trader | 55 % *spricht dagegen*, 45 % *neutral*, **0 % *stützt*** | ≤ 70 % | ✔ |
| P1-b Entscheider | 57 % *Einwand*, 43 % *mit Vorbehalt* | ≤ 70 % | ✔ |
| **Echo-Maß** | **39 von 40 (98 %)**: Der Entscheider übersetzt nur (*spricht dagegen* → *Einwand*, *neutral* → *mit Vorbehalt*) | ≤ 90 % | ⛔ **Echo** |
| P1-c Wiederholung | 5 von 6 (83 %); mit 0.1c zusammen 13 von 15 (87 %) | ≥ 90 % | ⛔ knapp |
| Anonymität | 0 Funde | | ✔ |

**Folgen (vorab festgelegt):**
1. **Echo:** Der Entscheider fügt mit nur einem Eingang nichts hinzu. Vorschlag **M1**: Trader plus Umfeld als Auskunft, ohne Entscheider. Das spart 3 Aufrufe je Signal. ➤ **Nutzerentscheidung**, weil es das Rollenmodell ändert.
2. **P1-c knapp verfehlt:** anpassen und neu messen, mit **5 Stimmen beim Trader**. Ohne Entscheider kostet das 5 statt bisher 6 Aufrufe je Signal. Der Lauf mit 20 Ankern und 10 Wiederholungen läuft, Ergebnis in 20.12.4.
3. **Fachlicher Hinweis:** Der Trader sagt **nie *stützt***. Die REGEL0 kauft immer nach einem Rückgang, und die Lage des Werts sieht dann selten gut aus. Ob *spricht dagegen* gegen *neutral* den 24-h-Ausgang trennt, kann nur das Rückspiel sagen.

#### 20.12.4 Trader mit fünf Stimmen — P1 bestanden (04.10.2026; Beleg `kalibrierung_trader_5_stimmen.txt`)

Dieselben ersten 20 Anker wie 0.1d, nur der Trader, 5 Stimmen, 10 Wiederholungen. 150 Aufrufe, Standard-DB unberührt.

| Prüfpunkt | 3 Stimmen | **5 Stimmen** | Ziel |
|---|---|---|---|
| P1-a | 100 % | **100 %** | ✔ |
| P1-b größte Stufe | 55 % | **45 %** (9 dagegen, 9 neutral, 2 stützt) | ✔ |
| P1-c Wiederholung | 83 % | **90 % (9/10)** | ✔ knapp |
| P1-d | 0 Funde | 0 Funde | ✔ |

⚠️ **Vorbehalte:**
- Die 90 % liegen genau auf der Grenze, gemessen an nur 10 Wiederholungen.
- Derselbe Grenzfall kippt wie bei 3 Stimmen (JTO).
- Das Mehrheitsurteil hängt an der Stimmenzahl: Bei mehreren Ankern unterscheidet sich die Mehrheit aus 5 von der aus 3. In Grenzfällen bleibt Rauschen. Die Mail nennt die Einzelstimmen, wenn sie nicht einig sind.

**Stand vor dem Einschalten:**
- Der **Trader** besteht P1 mit 5 Stimmen.
- Der **Markt** steht nur als Auskunft (85 % konstant).
- Der **Entscheider** ist ein Echo (98 %).

➤ **Nutzerentscheidung M1** (ohne Entscheider). Danach Fassung **0.1e**: `stimmen: 5`, Entscheider aus (bei M1), dann `mail_block: true`, Wache, Suite, Push, NB-Pull.

#### 20.12.5 Fassung 0.1e in der Mail — M1 nur für diese Messung, Neuprüfung festgelegt (04.10.2026; E-53)

Nutzer 04.10.: *„Ja, nur für die aktuelle Messung und Bewertung. Halte im Plan fest, dass die LLM-Stufen und der Entscheider erneut fachlich und technisch geprüft werden, oder du sagst, wir können das jetzt noch optimieren. Was sagst du, ist alles gegengeprüft?"*

**Fassung 0.1e** (`Basisinfos/regel0_llm.yaml`, Vorgabe in `agent/regel0_llm.py` gleich):

| | 0.1d | **0.1e** |
|---|---|---|
| Stimmen je Rolle | 3 | **5** (P1-c 83 % → 90 %) |
| Entscheider | an, Eingang nur der Trader | **ausgesetzt** (Echo 39/40), nicht gestrichen: Prompt, Code und Wache bleiben |
| Block in der Mail | aus (Schatten) | **an**, als *Sofortfassung, ungemessen*; die Mail nennt den ausgesetzten Entscheider |
| Zeitgrenze je Signal | 90 s | **120 s**, aus der Messung: Trader mit 5 Stimmen im Mittel 27 s, höchstens 52 s, dazu der erste Markt des Tages (~25 s). Bei 90 s wären Grenzfälle mit weniger Stimmen entschieden worden als gemessen |
| Aufrufe je Signal | 6 (+ Markt einmal je Faktenstand) | 5 (+ Markt einmal je Faktenstand); Riegel unverändert (150 je Tag, 6 Signale und 600 s je Lauf) |

**Jetzt optimieren oder später prüfen? → später, mit dem Rückspiel.** Alles, was ohne Ausgang messbar ist, ist gemessen: Form, Verteilung, Wiederholung, Anonymität, Echo. Die offene Frage ist, ob das Trader-Urteil den 24-h-Ausgang der REGEL0-Handel **trennt**. Sie ist nur im Rückspiel (N4) zu beantworten. Jede Prompt- oder Stufenänderung vorher wäre Anpassen ohne Zielgröße: Man verbessert dann, wie gleichmäßig die Stufen verteilt sind, nicht ihren Wert. Und auf derselben Entwicklungsmenge wäre das Mehrfachtesten. Der Entscheider bekommt erst wieder eine Aufgabe, wenn er eine **zweite unabhängige Sicht** hat: Text (P-T), Funding oder ein Umfeld, das unterscheidet. Planpunkt **O22**.

**Was gegengeprüft ist — und was nicht:**

| | Stand |
|---|---|
| ✔ Kalibrierläufe P1 (0.1 bis 0.1e) | Belege in `Rechenkern_02_10/kalibrierung_*.txt`, jeder Lauf mit eigener Wegwerf-Ablage, Standard-DB unberührt |
| ✔ Echo-Auszählung | 39/40 Paare ausgezählt, nicht geschätzt |
| ✔ Bestätigungsmenge unberührt | Kalibrierlauf sperrt sie aus (Trockenlauf 0 von 6) |
| ✔ Zeitpunkttreue der Makroreihen | Wache (nur abgeschlossene Monate) |
| ✔ Riegel gegen Abfragestau | Wache: Tageslimit, Ausfallschwelle, Laufgrenze |
| ✔ Mailblock 0.1e | gerendert geprüft, Entscheider-Hinweis; bei fünf Stimmen die Auszählung (*neutral (4 von 5)*, ohne Mehrheit jede Stufe mit Zahl) |
| ✔ Wache Regel0Betrieb | 53/53 mit 0.1e (dazu R-4 am Seiteneffekt), der Entscheider bleibt über einen eigenen Katalog prüfbar |
| ✔ volle Suite | 3195 Prüfungen, 5 rot: die 4 bekannten und **neu** *Nennersperre: gesperrte Symbole ohne Sperre da*. Ursache ist das Datum, nicht 0.1e: `onchain_historie.db` (splycur) endet am 12.09., die Frischegrenze ist 21 Tage, seit 04.10. ist die Probe leer. Dieselbe Ursache wie die bekannte Zeile *Messbasis veraltet*; die Messbasen werden am Desktop von Hand nachgeladen |
| ◐ P1-c Wiederholung | 90 % auf **nur 10** Wiederholungen, genau auf der Grenze. Ein Grenzfall (JTO) kippt weiter |
| ◐ Trader sagt fast nie *stützt* | 2 von 20 — fachlich erklärbar (REGEL0 kauft nach Rückgang), aber ob das Urteil trennt, ist **ungemessen** |
| ◐ Markt-Phasenlauf | lief noch mit dem kleinen Vorgriff des laufenden Teilmonats (vor der Zeitpunkttreue); das Urteil *85 % gleich* ändert das kaum, nachgemessen ist es nicht |
| ⛔ Nutzen der Urteile | **nicht gemessen** — Rückspiel N4 / P2 fehlt. Bis dahin ist der Block Auskunft |
| ⛔ Betrieb am NB | K-LLM-1 offen: erstes Signal mit eingeschaltetem Block |
| ✔ R-4 (Spot-Kette anhalten) | **am Seiteneffekt** nachgewiesen (`Rechenkern_02_10/pruefe_r4.py`, Beleg `pruefe_r4.txt`, in der Wache als Unterprozess): `hebel_screening_job` mit Platzhaltern, Schalter an → Umlauf 0, alter Weg 0; Schalter aus → Umlauf 1, alter Weg 0; keine Fehlermeldung, Sperre freigegeben. Die Probe schlug zweimal fehl, bevor sie lief (fehlende Platzhalter): Sie **kann** fehlschlagen |

## 21. Prüfung der NB-Exporte 04.10. und die Ausstiegserinnerung nur bei offener Position (04.10.2026; E-55)

### 21.1 Die Exporte (Teilexport 16:30, NB-Export 16:33; Neustart 10:26 auf 2afdca4)

| Punkt | Ergebnis |
|---|---|
| Laufzeit seit Neustart | ✔ 1.701 Logzeilen, **9 Tracebacks = 3 Zeitüberschreitungen bei Z.ai** (Rolle G der Spot-Kette, P-8 abgefangen), sonst keine ERROR-Zeile |
| REGEL0-Datenbasis | ✔ vier Dateien je Stunde, 0 Fehler, Stand 13:00 UTC |
| REGEL0-Rechnung | ✔ 159–162 s je Stunde, frisch 635/635, 79 Signale, 4 mit Hebel-Schalter an |
| Mails | ✔ 4 Signalmails (u. a. QNT, NEAR, KAIA), 1 Erinnerung, 0 nicht zugestellt, 0 gesperrt |
| **K-LLM-1** | ◐ Prüfblock 0.1e lief bei allen drei Signalen nach dem Neustart: Trader 3× (stützt, neutral, spricht dagegen), Umfeld 2× (einmal wiederverwendet), **0 Fehler**, Trader im Mittel 22 s. gemini-3.5 am NB **25 Aufrufe** = 2 × 10 + 5, also genau 5 Stimmen je Rolle. ➤ Offen: dass Block und Chart **in der Mail** stehen, sieht nur der Nutzer |
| ⚠️ Anzeigefehler Teilexport | Die Zeile *Aufrufe 5* zählte **Zeilen** statt Aufrufe (richtig: 25). **Behoben** (Spalte `aufrufe`), an einer Wegwerf-Ablage geprüft (10 bei 2 Rollen × 5) |
| **K-SN-2** | ✔ Stop-Nachzieh-Sammelmail **genau einmal** 07:15 (75 Empfehlungen); der Neustart um 10:26 hat sie nicht wiederholt |
| K-ALARM-2 | ohne Anlass (keine Lücke > 45 min seit 02.10.) |
| Bitpanda-Abgleich | ✔ frisch (0,1 h), **keine offene Hebelposition** |
| ⚠️ Kontingent | Der Zähler am NB kennt nur die **eigenen** Aufrufe. Google zählt den Schlüssel gemeinsam: Die Kalibrierläufe am Desktop (04.10. rund 410 auf 3.5) stehen im NB-Zähler **nicht**. Das Tageslimit 150 des Prüfblocks schützt also nur vor dem eigenen Stau, nicht vor dem fremden. Folge, wenn es knapp wird: Der Block steht grau da (*keine Auskunft*), die Mail geht trotzdem. ➤ Für N4 (O24) mitzählen |
| Nebenbefund Spot | weiterhin Verkaufsvorschlags-Mails je Lauf; 07:15-Mail mit 75 Spot-Stops (O19) – angehalten mit O23, nicht Teil dieser Runde |

### 21.2 Ausstiegserinnerung nur bei offener Hebelposition (Nutzer: *„sofort ändern“*)

**Ist (bis 04.10.):** Jede Signalmail zog nach 24 h eine Erinnerung *„AUSSTIEG fällig“* nach, egal ob eine Position eröffnet war. Text: *„Gilt nur, wenn du die Position eröffnet hast.“* Am NB gab es am 04.10. **keine** offene Hebelposition; die eine Erinnerung war überflüssig. Bis zum 05.10. wären es drei weitere (QNT, NEAR, KAIA).

**Neu:**

| Positionsstand | Erinnerung |
|---|---|
| offene **LONG**-Hebelposition in diesem Asset (`hebel_positions` status *offen*, Bitpanda-Kürzel) | ✔ geht raus, mit Vermerk *offene Hebelposition … seit …* |
| Abgleich frisch, **keine** offene Position | ✖ **entfällt** – Zeitpunkt und Grund in der Ablage (`erinnerung_entfallen_am`, `erinnerung_grund`), sichtbar im Hebel-Tab und im Teilexport, **nie nachgeschickt** |
| Abgleich veraltet (≥ 1 h), nie gelaufen oder nicht lesbar | ✔ geht raus, mit Vermerk *Positionsstand unbekannt – vorsichtshalber verschickt* |

**Warum so:** Die Erinnerung ist bei echtem Geld die einzige Ausstiegsmeldung, solange die Positionsführung (O13) fehlt. Ein **falsches Weglassen** kostet, eine überflüssige Mail nicht. Deshalb entfällt sie nur bei **nachgewiesen** fehlender Position. ⚠️ Bekannte Grenze: Der Importer wertet eine Teilschließung als Vollschluss (2.679). Eine Restposition gälte dann als zu, und ihre Erinnerung entfiele. Das gehört zu O13.

**Code:** `agent/regel0_mail.position_stand` (Regel, rein), `versende(..., position=)` (EIN Positionsstand je Lauf), `scheduler/background._regel0_positionsstand` (nur lesend: `hebel_abgleich.frische`, `get_open_hebel_positions`), Ablage zwei Spalten, Hebel-Tab und Teilexport zeigen *entfallen*.

**Prüfung am Seiteneffekt:** `Rechenkern_02_10/pruefe_erinnerung_offen.py` (Wegwerf-Ablage, Versand ersetzt). Fälle A bis E, dazu *nie nachgeschickt*, *nicht doppelt*, *nie gelaufen = unbekannt*, *SHORT zählt nicht*, und gegen die **NB-Kopie** (03.10.): Abgleich dort veraltet → *unbekannt* → Mail mit Vermerk, wie verlangt. 11/11. In der Wache als Unterprozess; Regel0Betrieb 54/54.

**NB-Kontrolle K-ERIN** (nach Pull und Neustart): Die Erinnerungen QNT/NEAR/KAIA (fällig 05.10. ab etwa 11:00 Ortszeit) **entfallen**. Im Teilexport steht dann *Erinnerung entfallen: … keine offene Hebelposition*, im Log *… Erinnerung entfallen (keine offene Position)*. Eröffnest du eine Position, kommt ihre Erinnerung mit Vermerk.

### 21.3 Die offensichtlichen Fehler der REGEL0-Mails vom 04.10. — behoben (Nutzer: *„ja, zuerst die offensichtlichen Fehler prüfen und fixen“*)

Geprüft an den Mails QNT, NEAR, KAIA (Signal) und SEI (Erinnerung) aus `eMail_Beispiele`, Text- **und** HTML-Teil, dazu die Chart-Anhänge.

| # | Fehler | Ursache | Behoben |
|---|---|---|---|
| F1 | *„REGEL0-Mail ohne LLM“* — der Block **stand drin** (Text und HTML), aber am Ende eines `<pre>` ohne Umbruch: Zeilen über 200 Zeichen liefen am Handy aus dem Bild | `ui/formatting.render_detail_html` ohne `white-space` | `pre-wrap` + `overflow-wrap` (gilt für alle Mails; am breiten Bildschirm unverändert). Am Prüfstand bei 375 px: Seitenbreite 375, kein seitlicher Bildlauf |
| F2 | Chart 900 px breit → seitlicher Bildlauf am Handy | `api/email_notify` Bildstil ohne `max-width` | `max-width:100%; height:auto` |
| F3 | Dezimalpunkte: *261.168 USD*, *+0.0 %*, *0.0375 USDT* | `txt.replace(".", ",", 0)` — die **0 ersetzt nichts** | deutsche Schreibweise (`regel0_chart._zahl`) |
| F4 | **USD statt EUR**: kein Kurs, kein Liquidationskurs in EUR | der Bitpanda-Ticker lieferte nur USD in die Mail | `kurse_live` liefert auch **EUR**. Die Mail zeigt **KURS JETZT … EUR (Bitpanda)** und **LIQUIDATION 3x bei etwa … EUR (−26,7 %)** (Formel wie Messung und Chart). Ohne Ticker steht *nicht verfügbar*, kein erfundener Kurs. USD bleibt nur als *Messgrundlage der REGEL0* |
| F5 | **Chart QNT 3x zeigte die 5x-Liquidationslinie**, die gewählte 3x fehlte (lag unter dem Ausschnitt) | gezeichnet wurde jede Stufe im Ausschnitt | nur die **gewählte** Stufe; außerhalb des Ausschnitts als Hinweis am unteren Rand (*▼ Liquidation 3x bei … – unterhalb des Ausschnitts*). Die übrigen Stufen stehen im Kasten |
| F6 | Chart in USDT, Achse mit Dezimalpunkt, Signal-Linie ohne Legende | — | Chart in **EUR** (Binance × EUR/USD aus demselben Bitpanda-Abruf), deutsche Achse, Legende *Signal*. Im Hebel-Tab (ohne Ticker) bleibt es USDT und sagt das |

**Geprüft:** Prüfstand mit echten Desktop-Kursen (QNT, KAIA), Wegwerf-Ablage, Versand abgefangen, mit und ohne Ticker; Charts angesehen; HTML am Handy-Format (375 px) im Browser. Wache Regel0Betrieb 59/59, darunter fünf neue Zeilen *Mailfehler/Chartfehler 04.10.*.

**Bewusst NICHT jetzt** (das ist der Neuaufbau O25, M-a bis M-f, abgestimmt mit *„ja“*): Reihenfolge Handlung → Chart → Einschätzung → Begründung → Technik, Ortszeit zuerst, Fachbegriffe in die Fußzeile, echtes HTML statt `<pre>`, Hinweis auf die Spot-Mail zum selben Asset.

**Nebenbefund geprüft:** QNT 67,88 USD am 22.09. (Desktop) gegen 259,64 am 04.10. (NB) ist **echt**. Die Reihe steigt bis 24.09. auf 82, und Bitpanda und Binance zeigen am 04.10. unabhängig 261,17 bzw. 260,84.

### 21.4 O25: die REGEL0-Signalmail neu aufgebaut (04.10.2026; Nutzer: M-a bis M-f *ja*, *nicht die bisherige Form übernehmen*)

**Aufbau** (eine Gliederung `regel0_mail._signal_teile` für Text, HTML und das Detail im Hebel-Tab):

| Abschnitt | Inhalt |
|---|---|
| **1 · Was zu tun ist** | Einstieg *heute 14:00* (Schlusskurs der Stunde 13–14 Uhr) · **Kurs jetzt … EUR (Bitpanda)** · Hebel (vorläufig, wann endgültig) · Einsatz → Position · Ausstieg *morgen 14:00* · **Liquidation bei etwa … EUR** mit Gefahr binnen 24 h · Bitpanda-Hebelstufen prüfen |
| **2 · Chart** | in EUR, direkt nach der Handlung (HTML: das Bild an seinem Platz, `email_notify.html_mit_bildern`) |
| **3 · Einschätzung** | Regel (Signalstärke in Worten) · Trader in einer Zeile mit Stimmen *(5 von 5)* · Umfeld in einer Zeile *(nur Beschreibung)* · **M-f** *Achtung: die alte Spot-Kette hat am … zu … „NACHKAUFEN“ gemailt – ein anderes Geschäft* · Gefahr je Stufe |
| **4 · Begründung der Rollen** | je Rolle Urteil, Begründung, Gegengrund; darunter Fassung, Hinweise, Messstand (HTML gegliedert, Text wie bisher) |
| **5 · Technik** | UTC-Zeiten, Kurs zur Signalstunde in USD (Messgrundlage), Zuordnung, Vermerke, Regel mit v-dach, Startwerte, D2 |

**Technik:**
- `send_notification_email(..., html=)` bringt ein eigenes HTML mit, die übrigen Mails bleiben unverändert.
- `versende(..., spot=, senden_html=)`: Ohne diese beiden bleibt der alte Weg bestehen, alle Prüfskripte laufen weiter.
- `regel0_llm.mail_teile` liefert kurz, lang, detail und hinweise.
- `background._regel0_spot_hinweis` liest `signals` nur (Mailvermerk *zugestellt*, letzte 24 h, nicht Hebel).
- Jede Zutat darf scheitern, ohne die Mail aufzuhalten (P-8).
- Betreff unverändert, damit bestehende Mailfilter weiter greifen.
- Echte Umlaute im Mailtext.

**Geprüft:**
- Prüfstand mit echten Kursen und den echten Rollentexten der KAIA-Mail vom 04.10.; am Handy-Format (375 px) im Browser: kein seitlicher Bildlauf, Chart 351 px.
- `pruefe_o25.py` 12/12 am Seiteneffekt, auch der Spot-Hinweis gegen die NB-Kopie (vor 2 h → Hinweis, vor 30 h → keiner).
- `pruefe_s74` 19/19 (zwei Erwartungen bewusst auf *VORLÄUFIG/endgültig* nachgezogen), `pruefe_s75` 15/15, `pruefe_h17` 23/23, `pruefe_erinnerung_offen` 10/10.
- Wache Regel0Betrieb 60/60.
- Eigener Fehler unterwegs: Die erste Fassung der Prüfung erwartete *13:00* statt *14:00* Ortszeit. Die Prüfung rechnet die Ortszeit jetzt selbst aus.

**Grenze:** Der Spot-Hinweis sieht nur Spot-Mails **vor** der REGEL0-Mail. Kommt die Spot-Mail danach, steht in ihr kein Hinweis. Das gehört zu O24/O23 (die Spot-Kette ist angehalten und wird nicht mehr umgebaut).

**NB-Kontrolle K-MAIL-2:** Die nächste REGEL0-Signalmail sieht am Handy so aus wie oben. Fehlt das Bild an Platz 2 oder steht `{{BILD:0}}` sichtbar in der Mail, ist der Versandweg falsch.

## 22. S7-7 — Mindestbedingungen der Testwoche, VORSCHLAG zur Abstimmung (04.10.2026; Nutzer: *„Ja, S7-7-Vorschlag vorbereiten, prüfen und gegenprüfen“*)

### 22.1 Was „Schritt 8 Umstellung“ heute noch heißt

Der **Ersatz ist schon passiert**: Seit S7-4 (E-46, am NB seit 03.10.) kommen neue Hebel-Einstiege nur aus der REGEL0, der alte Hebelweg ist aus (F4: *„die neue Ablaufkette soll die alte sofort ersetzen“*). Schritt 8 ist damit nur noch die **Freigabe**:
- Vermerk TESTWOCHE aus.
- Die Fassung festgeschrieben: REGEL0.1, Prüfblock 0.1e, Mail O25 (E-43: versionierte Regeln).
- Start der Einstiegskette für M1.

⚠️ **Die Testwoche endet von selbst:** `testwoche_bis: 2026-10-10` in `regel0_betrieb.yaml`. Ab dem 11.10. fällt der Vermerk weg, **ohne** dass jemand freigegeben hat. ➤ Vorschlag S-2.

### 22.2 Gefunden beim Gegenprüfen am Code — verlorene Signalstunden

Jeder Stundenlauf legt **nur die Signalstunde davor** ab (`agent/regel0_rechnung.py:530`, `sh = jetzt - 1`). Ein Nachholen gibt es nicht. Daraus folgt:
- Ist die App über einen vollen Stundenwechsel hinaus weg (z. B. 10:00–12:30 UTC), sind die Signale der Stunden 9 und 10 **endgültig verloren**. Der Lauf nach dem Start rechnet nur Stunde 11.
  - ⚠️ **Berichtigt beim Bau (§22.6):** Der Lauf legt auch die Stunde jetzt−2 (*endgültig*) an, wenn sie fehlt (`regel0_stundenlauf`, INSERT OR IGNORE). Im Beispiel ist also nur Stunde 9 verloren, Stunde 10 wird aufgefangen, allerdings ohne Kurs, Börsenpaar und Faktor. Verloren geht ein Signal erst, wenn **zwei** Läufe hintereinander fehlen.
- Dasselbe gilt für ein Asset, dessen Kurs in dieser Stunde verspätet kommt (`frisch`).
- Kurze Neustarts schaden nicht: Der Job läuft 10 s nach dem Start und rechnet die Stunde davor.

Das ist **kein** Fehler der Regel, sondern des Betriebs. Gemessen ist die REGEL0 auf **jeder** Stunde. ➤ Vorschlag **N-1**: die verpassten Stunden bis 3 h zurück nachrechnen. Das passt zu `NICHT_AELTER_H = 3`: Ältere Signale werden ohnehin nicht mehr gemailt. Die Nachrechnung ist R-R11-gleich, denn dieselben Daten liefern dieselben Signale.

### 22.3 Die Bedingungen — Vorschlag

Ausgewertet wird an einer **Kopie** von `data/regel0_signale.db` am Desktop, ohne Seiteneffekt am NB. Das Werkzeug ist `Rechenkern_02_10/pruefe_testwoche.py`. Die Gegenprobe `pruefe_testwoche_gegenprobe.py` besteht 12/12: Jede Bedingung **kann** fehlschlagen, ein eingebauter Fehler macht genau seine Bedingung rot.

| # | Bedingung | Regel (vorab fest) | Quelle | Stand bis 04.10. |
|---|---|---|---|---|
| **T1** | jede Stunde gerechnet | 0 verlorene Signalstunden (außer einem Stillstand, den du angekündigt hast) | Ablage `lauf` | Teilexport: lückenlos 09–14 UTC; die ganze Woche erst mit der Kopie |
| **T2** | Frische | kein Lauf mit veralteten Assets | `lauf.veraltet` | 0 (Teilexport) |
| **T3** | Laufzeit | kein Lauf über 1.500 s (halbe Zeitgrenze); der Trainingslauf ist ausgenommen | `lauf.sekunden` | 159–162 s |
| **T4** | keine Fehler | kein Traceback aus `regel0_*`, Mail oder Nachlader; Nachlader-Fehler 0 | NB-Export, Teilexport | ✔ 04.10. (nur Z.ai der Spot-Kette) |
| **F1** | Signalmail vollständig | jedes Signal mit Schalter an und Stufe > 0 gemailt **oder** begründet gesperrt | `signal` | 4 gemailt, 0 gesperrt |
| **F2** | rechtzeitig | vor dem Schluss der Einstiegsstunde | `mail_signal_am` | ~9 min nach der Signalstunde |
| **F3** | Korrektur | weicht die endgültige Stufe ab, ist die Korrektur verschickt | `signal` | 0 Abweichungen |
| **F4** | Ausstieg | jede fällige Erinnerung verschickt **oder** als *entfallen* vermerkt (K-ERIN) | `signal` | ab 05.10. |
| **F5** | R-R11 am NB (**S7-6**) | die Signale der Woche zeilengleich mit der Nachrechnung am Desktop | Ablage + NB-Daten | offen; braucht die Kopie **und** die NB-Stundenkurse (USB) oder ein Nachladen von Hand am Desktop |
| **L1** | Prüfblock | zu jedem gemailten Signal eine Trader-Zeile (Urteil oder Grund); ≤ 150 Aufrufe je Tag | `pruefung` | ✔ 3/3, 25 Aufrufe |
| **K** | Mail am Handy | du bestätigst K-MAIL-2 (Aufbau O25 lesbar) | du | offen |

**Auskunft, keine Bedingung:**

| # | | Warum keine Bedingung |
|---|---|---|
| A1 | **Signalbilanz** (deine Vorgabe 01.10.): Summe über die Hebel-Liste gegen die Messung, **erwartet 19,5 je Woche** (26 Messbasis-Assets; CAT, XDC ohne Rate) | **Je Asset ist eine Woche nicht prüfbar** (erwartet 0,4–0,9 je Asset). Die Liste je Asset steht trotzdem da |
| A2 | Korrekturquote gegen B-9 (1,6 %), gesperrte Zuordnungen mit Grund | bei ~20 Signalen nicht unterscheidbar |
| A3 | **Ertrag** der Wochensignale (24 h, Liquidationen) | Streuung 5,6 % je Handel → bei ~20 Handeln ±2,5 % auf den Mittelwert. **Eine Woche sagt nichts über den Ertrag** (L-5). Geprüft wird nur, ob eine Liquidation vorkam, die nach der Stufe nicht hätte vorkommen dürfen |
| A4 | Urteile der Rollen gegen den Ausgang | erst im Rückspiel N4 |

### 22.4 Simulation (F4: *„ggf. weitere Simulationen zur Stabilität“*)

| | |
|---|---|
| **Monatswechsel** | Er liegt **nach** der Testwoche (01.11.) und kommt in der Woche nicht vor. Vorschlag: der Monatswechsel 31.08./01.09. am Desktop als Probelauf (`--ablage/--modelle` in Wegwerfordnern), dazu die Kontrolle **K-MONAT** am 01.11. |
| **Ausfall** | Stillstand > 1 h (K-ALARM-2): Mail *Stillstand*, danach T1 mit N-1 (Nachholen) |

### 22.5 Zur Abstimmung

| # | Frage | Vorschlag |
|---|---|---|
| **S-1** | Gelten T1–T4, F1–F5, L1 und K als Bedingungen, A1–A4 als Auskunft? | ja |
| **S-2** | Was am 10.10.? | Freigabe **nur mit deinem Ja** nach der Auswertung. Liegt die Auswertung bis dahin nicht vor oder fällt eine Bedingung, verlängere ich `testwoche_bis` und sage dir, warum. Nie still auslaufen lassen |
| **S-3** | Fällt eine Bedingung | Ursache beheben (bei kritischen Punkten auch unter der Woche, E-43, neue Version mit Vermerk). Die Woche wird um die betroffene Zeit verlängert, nicht neu gestartet. Eine **Regeländerung** (REGEL0 selbst) startet sie neu |
| **S-4** | **N-1** verpasste Stunden bis 3 h nachrechnen | ja, jetzt (Betrieb, keine Regeländerung; Prüfung R-R11-gleich) |
| **S-5** | Was du dafür tust | zum Ende der Woche einen Teilexport und die Kopie `data/regel0_signale.db` in den Austauschordner. Für F5 die vier REGEL0-Dateien per USB, oder ich lade die Desktop-Messbasis von Hand nach |

### 22.6 Abgestimmt und gebaut (Nutzer 04.10.: *„Ja, S-1 bis S-5 wie vorgeschlagen, prüfen und gegenprüfen“*; E-57)

**S-1:** Die Bedingungen und Auskünfte gelten wie in §22.3. Werkzeug `pruefe_testwoche.py`, Gegenprobe `pruefe_testwoche_gegenprobe.py` **14/14**.
- Beim Bau zwei Regeln berichtigt:
  - **T1:** Eine Signalstunde ist verloren, wenn weder der Lauf danach noch der übernächste lief noch sie nachgeholt wurde. Die erste Fassung zählte jede fehlende Laufstunde.
  - **F2:** *rechtzeitig* heißt spätestens 75 min nach Schluss der Signalstunde (zwei Läufe), siehe N-1 unten.

**S-2:** Die Testwoche endet **nur** mit `testwoche_freigegeben: true` in `regel0_betrieb.yaml`. Bis dahin bleibt der Vermerk TESTWOCHE auch nach dem 10.10. stehen, dann mit *Freigabe ausstehend*. Ich setze den Schalter erst nach deinem Ja.

**S-3:** Fällt eine Bedingung, wird die Ursache behoben und die Woche verlängert. Nur eine Änderung an der REGEL0 selbst startet sie neu.

**S-4 / N-1 Nachholen:**
- Der Stundenlauf rechnet die Signalstunden **jetzt−5 bis jetzt−3** nach, die kein Lauf abgelegt hat (`regel0_stundenlauf.verpasste_stunden`, `regel0_rechnung.bewerte(nachholen=)`).
  - Die Bewertung kommt aus demselben Fenster wie zur richtigen Zeit, die Stufe aus der ATR der Einstiegsstunde (wie *endgültig*).
  - Fehlt ein Modellpaket, wird die Stunde ausgelassen und im Lauf genannt.
- Neue Tabelle `nachgeholt` in der Ablage (für T1).
- Fehlende Zeilen werden jetzt **vollständig** angelegt: mit Kurs, Markt, Paar und Faktor. Bisher fehlten diese bei der aufgefangenen Stunde, und der Preisabgleich vor der Mail ging ins Leere.
- **Mail:** Beim Bau fiel auf, dass schon der freigegebene D1-Weg (E-46: vorläufig 0, endgültig > 0) etwa 5–10 min **nach** dem Einstieg mailt. Das bleibt so, die Mail sagt es jetzt: *⚠ dieser Einstieg ist seit … min vorbei*.
  - Keine Signalmail geht nur, wenn der Einstieg **länger als 1 h** vorbei ist (`VERPASST_NACH`). Das ist der Fall eines nach einem Ausfall nachgeholten Signals.
  - Stattdessen wird es als **verpasst** vermerkt: Spalte `mail_verpasst_am`, Hebel-Tab *verpasst (nachgerechnet nach Ausfall)*, Teilexport *Nachgeholt / verpasste Signale*.
  - Die Grenze folgt aus dem Takt, sie ist keine Wahl.
- **R-R11-Nachweis an echten Daten** (`pruefe_n1.py`, Beleg `pruefe_n1.txt`):
  - Stundenläufe am Desktop, einmal lückenlos, einmal mit 5 h Ausfall, an **drei** Zeitpunkten (19.08., 24.08., 23.09.).
  - Der Wiederanlauf legt **dieselben Signale mit derselben v̂ und endgültigen Stufe** ab: **182, 98 und 2 Signale**, davon 165, 75 und 2 in nachgerechneten Stunden.
  - Verloren ist genau die eine Stunde außerhalb des Fensters, und T1 nennt sie.
  - ⚠️ **Gefunden erst an vielen Signalen:** Der erste Nachweis lief auf nur 2 Signalen und war grün. Auf 182 Signalen zeigte sich, dass die Stunde **vor** dem Ausfall ihre **endgültige Stufe** nie bekam: Der Lauf sh+2 fiel aus, und das Nachholen übersprang sie, weil sie schon eine Zeile hatte.
    - **Behoben:** Zeilen der letzten 24 h ohne endgültige Stufe werden nachgerechnet.
    - Eine dadurch fällige **Korrektur**, deren Einstieg länger als 1 h vorbei ist, geht nicht als Mail raus. Sie wird vermerkt (`korrektur_verpasst_am`), F3 zählt sie als begründet.

**S-5 (dein Teil):** zum Ende der Woche ein Teilexport und eine Kopie von `data/regel0_signale.db` in den Austauschordner. Für F5 die vier REGEL0-Dateien per USB, oder ich lade die Desktop-Messbasis von Hand nach.

**Geprüft:**
- Wache Regel0Betrieb **64/64**, darunter neu: S-2, N-1 Stundenbestimmung, N-1 Mail, Gegenprobe Testwoche.
- `pruefe_s74` **20/20**:
  - neu: *nach dem geplanten Tag ohne Freigabe bleibt der Vermerk*, *mit Freigabe nicht*;
  - drei Wachzeilen mit fachlich falscher Testzeit (Mail **nach** dem Einstieg) auf 11:30 berichtigt.
- `pruefe_s75` 15/15, `pruefe_h17` 23/23, `pruefe_o25` 11/11, `pruefe_erinnerung_offen` 10/10.

**NB-Kontrolle K-N1** (nach Pull und Neustart): Im Teilexport steht die Zeile *Nachgeholt (N-1): 0 Signalstunden · verpasste Signale: 0*, solange kein Ausfall war. Wer es sehen will: die App einmal **über zwei volle Stundenwechsel** beenden. Dann sagt der Lauf danach *nachgeholt: …*, und die Stillstandsmail kommt (K-ALARM-2).

### 21.5 NB-Exporte 05.10. (Teilexport 05:53, NB-Export 06:00; Neustart 05:51 auf 3c8f9b1) und Concrete (CT)

| Punkt | Ergebnis |
|---|---|
| Betrieb | ✔ 71 h ohne Lücke, seit dem Neustart 0 Fehler. REGEL0 jede Stunde, 635/635 frisch, 0 veraltet. 105 Signale, davon 4 mit Hebel-Schalter an (alle gemailt am 04.10.) |
| **K-N1** | ⏳ noch nicht prüfbar: Der Neustart lag **2 min vor** dem Teilexport, der neue Code hatte noch keinen Stundenlauf (der nächste um 06:05). Erst dieser legt Tabelle `nachgeholt` und Spalte `mail_verpasst_am` an. Die Zeile *Nachgeholt* fehlt deshalb zu Recht. ➤ beim nächsten Teilexport |
| Laufzeit | 160–230 s je Lauf, je nach Last am NB (03.10. phasenweise ~205 s, seit dem Neustart am 04.10. 18:20 ~225 s, einmal 285 s). Grenze 1.500 s (T3): **Beobachtung**, kein Befund |
| Kontingent 04.10. | gemini-3.1 220, gemini-3.5 25 (der Prüfblock), Z.ai 21 |
| K-ERIN | fällig heute 10–12 UTC (QNT, NEAR, KAIA) |

**Concrete (CT): warum nicht automatisch aufgenommen?**
- Das ist so entschieden: **E13 (16.09.)**. Eine Bitpanda-Position ohne Watchlist-Eintrag kommt als Mail mit Name, Wert, Status und Aktion.
- Automatisch ergänzt werden nur Assets mit offener **Hebelposition** (`auto_add_unknown_hebel_symbols`, 16.07.).
- CT ist im Bitpanda-Katalog ein *token*. Bei Binance gibt es ein CT-Paar erst **seit 01.10.**, ob es derselbe Coin ist, ist nicht abgeglichen. Wert 56 EUR.

**Gefunden und behoben – die Mail kam bei jedem Neustart** (03.10. fünfmal, 05.10. wieder):
- Die Sperrfrist stand nur im Speicher (`background._melde_bitpanda_bestand`, `time.monotonic`). Die Mail verspricht aber *höchstens einmal am Tag*.
- Jetzt steht der Versand in `meta` (`bitpanda_meldung:<schlüssel>`) und gilt über Neustarts. Ist die Datenbank nicht lesbar, gilt der Speicher; die Meldung geht nie verloren.
- Geprüft am Seiteneffekt gegen die NB-Kopie (`Rechenkern_02_10/pruefe_bestandsmail_sperre.py` 4/4, darunter der Neustart), dazu eine Wachzeile in *BitpandaBestand*.

**Zur Abstimmung (Plan O26):** Sollen Bitpanda-Bestände automatisch in die Watchlist? Das ändert E13. Vorschlag: **jetzt nicht**, sondern mit dem Spot-Neubau (O23), weil:
1. Die Watchlist speist die **alte Spot-Kette**. Ein aufgenommenes Concrete bekäme sofort deren Verkaufs- und Nachkaufvorschläge, also genau den angehaltenen, falschen Ast.
2. Die REGEL0 braucht keine Watchlist: Sie rechnet über alle Binance-Assets, die Hebel-Freigabe steht in `asset_hebel_settings`.
3. Für Token ist die Zuordnung zur Kursquelle unsicher (vier Symbolwelten, 2.612). CT wäre auf Binance erst seit vier Tagen da, ohne Preisabgleich.

Bis dahin kommt die Mail **einmal am Tag**, wie versprochen.

### 22.7 F5 (S7-6) — das Werkzeug und die Kopie vom NB (05.10.2026; Nutzer: *„F5-Werkzeug bauen, prüfen und gegenprüfen“*, *„Kopierskript … in ein bestehendes integrieren?“*)

**Wenige Hebel-Signale sind kein Engpass für die Prüfungen.**
- Das NB bewertet jede Stunde **alle** 635 Assets. Seit 03.10. sind das 105 Signale, gemailt wurden nur die 4 mit Hebel-Schalter.
- F5 vergleicht **alle** Signale. Bis zum Wochenende sind es einige hundert.

**Werkzeug** `Rechenkern_02_10/pruefe_f5_rr11_nb.py`:
- Es nimmt eine Kopie der NB-Ablage und eine Kopie der NB-Daten (`stundenkurse.db`, `stundenkurse_alle.db`, ~1,3 GB).
- Je Laufstunde rechnet es am Desktop **denselben** Stundenlauf (`betrieb_lauf`) nach, in Wegwerfordnern, auf 4 Prozesse in zusammenhängenden Blöcken mit Überhang.
- Verglichen werden je Signal v̂, vorläufige und endgültige Stufe.
- **Mit** den NB-Modellpaketen (`--modelle`) prüft es den Rechenkern, **ohne** zusätzlich das Training. Maßstab sind gleiche Signale, nicht gleiche Bits (numpy-Fassung).

**Gegenprobe** (`--gegenprobe`, Beleg `pruefe_f5_gegenprobe.txt`) **5/5** an echten Daten vom 19.08.:
- Parallel = nacheinander auf **231 Signalen**.
- Je ein eingebauter Fehler (v̂, endgültige Stufe, fehlendes, erfundenes Signal) macht genau seine Zeile rot.

**Kopie vom NB, in den Teilexport eingebaut** (kein neues Skript für dich):
- `nb_teilexport_betriebsdaten.py` legt bei jedem Lauf Ablage und Modelle (~0,1 MB) nach `Austauschordner/Notebook_Analysedaten/regel0_kopie_<Gerät>/`, dazu `KOPIE_INFO.txt` mit Prüfsummen und Integritätsprüfung.
- Mit `--mit-kurse <Ordner>` kommen die Stundenkurse dazu, auf den **USB-Stick**, nie in den Drive.
- Kopiert wird nur lesend über die SQLite-Sicherung (`nb_kopie_regel0.py`). Das ergibt einen stimmigen Stand, auch während ein Stundenlauf schreibt. Ein Ziel im Projekt wird verweigert.
- Gegenprobe `pruefe_nb_kopie.py` **8/8**: Quelle unberührt, Kopie vollständig, stimmig auch bei einem Schreiber, Ziel im Projekt und in `data/` verweigert, echte Messbasis 346 MB in 3 s.

**Erste echte F5-Prüfung jetzt, nicht erst am Wochenende** (Nutzer: *„sollte man bereits eine erste Gegenprobe durchführen“*):
1. Am NB nach dem Pull: `python nb_teilexport_betriebsdaten.py --mit-kurse <USB>\regel0_kopie`
2. Den Stick an den Desktop. Ich rechne `pruefe_f5_rr11_nb.py <USB>\regel0_kopie\regel0_signale.db <USB>\regel0_kopie --modelle <USB>\regel0_kopie\regel0_modelle`.
3. Dauer am Desktop etwa 1–2 h für die Stunden seit 03.10. (4 Prozesse).

### 22.8 F5 erster Lauf an den echten NB-Daten — ZEILENGLEICH (05.10.2026)

- **Kopie:** vom NB über den Teilexport (`--mit-kurse`, Stick), 05:19 UTC. Integritätsprüfung ok, Modell-Prüfsumme `bf3e71daf909` wie am NB. Am Desktop lokal abgelegt, Prüfsummen gleich.
- **Nachrechnung:** `pruefe_f5_rr11_nb.py` mit den **Modellen des NB**, 4 Prozesse, Laufstunden **03.10. 04:00 bis 05.10. 05:00 (50)**. Beleg `Rechenkern_02_10/pruefe_f5_nb_0510.txt`.
- **Ergebnis: 103 von 103 Signalen gleich.** 0 nur am NB, 0 nur am Desktop, 0 v̂ anders, 0 vorläufige und 0 endgültige Stufe anders. ✔ **F5 für den bisherigen Teil der Testwoche erfüllt.**
- **Aussage:** Der Rechenkern am NB rechnet dieselben Signale wie die Messung am Desktop, auf allen Assets (nicht nur den 4 gemailten).
- **Nicht geprüft:** das Training am Monatswechsel. Die NB-Modelle wurden übernommen; ein Lauf ohne `--modelle` (Training am Desktop) folgt zum Wochenende mit, und K-MONAT kommt am 01.11.

### 22.9 NB-Export 05.10. 12:40 und K-MISFIRE (05.10.2026; Nutzer: *„prüfe den NB-Export zuerst“*, *„Ja zu 1 und 2“*)

**Betrieb:**
- 0 fehlende Stunden in 72 h.
- REGEL0 stündlich, 158–327 s, Nachlader fehlerfrei.
- 21 Traceback-Zeilen = 7 Z.ai-Zeitüberschreitungen der **alten** Kette (Rolle G), keine aus REGEL0.
- Gemini 125 Aufrufe.

**K-MISFIRE geklärt:**
- Am 05.10. um 09:18:34 starteten `staleness_watchdog` und `coingecko_quota_check` **1,07 s** zu spät. Das war Last, kein Standby.
- Ursache: Jobs ohne eigenes `misfire_grace_time` erben den APScheduler-Standard von **1 s**. Der Fix vom 19.07. galt nur den Sofort-Start-Jobs.
- Folge: ein ausgelassener Lauf und eine Fehlalarm-Mail, kein Datenverlust.

**Fix (Nutzer-Ja):**
- `scheduler/background.py` `_neuer_scheduler()`: `job_defaults` mit `misfire_grace_time` = 300 s für **alle** Jobs; eigene Werte bleiben.
- `_misfire_text()`: Die Mail nennt die geplante Zeit, die Verspätung und die Toleranz.
- Ein echter Ausfall von mehr als 300 s meldet sich weiter.

**Nachweis am echten APScheduler** (`Rechenkern_02_10/pruefe_misfire.py`, 6/6):
- Die Gegenprobe reproduziert den Fehler mit dem alten Aufbau.
- 2 s Verspätung laufen jetzt durch; 400 s sind weiter ein Misfire; eine eigene Toleranz bleibt.
- `build_scheduler` baut über den Helfer, nachgewiesen mit einem Sentinel vor jedem Datenbankzugriff.
- Wache Regel0Betrieb **66/66**.

**Weiter offen:**
- K-ERIN: 1 von 3 *entfallen* um 12:09 ✔; die zwei übrigen waren nach dem Export fällig.
- **Neu:** REGEL0 *veraltet 3* (633/636) seit dem Lauf um 09:00 UTC, unter der Meldegrenze. Welche Assets, zeigt der nächste Teilexport.
- Concrete: keine Mail mehr, nur noch die Log-Warnung.
- K-MAIL-2 beim Nutzer.

**Nachtrag Teilexport 05.10. 18:07** (nach Pull 95cfe08 und Neustart):
- ✔ **K-ERIN bestanden.** Alle drei Erinnerungen sind entfallen: QNT 10:09 UTC, NEAR und KAIA 12:09 UTC. Die Ablage führt UTC, das Log Ortszeit.
- **veraltet 3** = 1000000BOB, PROMPT, PUMPBTC. Sie sind auf Binance nicht mehr im Handel (Nachlader *nicht im Handel 3*), keiner steht auf der Hebel-Liste. Unbedenklich.
- **Signale:** Heute gab es 16 REGEL0-Signale, alle außerhalb der Hebel-Liste, also keine Hebelmail. Seit 03.10. kamen 4 Hebelmails (SEI, QNT, NEAR, KAIA) in rund 58 h. Bei 19,5 je Woche (§22) wären etwa 7 zu erwarten; P(≤ 4) ≈ 0,2, also im Rauschen. Weiter in der Testwoche beobachten (T1 der S7-7-Bedingungen).
- Der Nutzer bekommt derzeit nur Mails der alten Spot-Kette (Verkaufsvorschläge, NACHKAUFEN). Zum Schalter R-4 siehe Plan Hebel O24 (Wahl A/B).
- **K-MISFIRE-2:** ob nach dem Neustart noch eine Misfire-Mail kam, prüft der nächste NB-Export bzw. die Rückmeldung des Nutzers.

## 23. Voranalyse N4 — das Rückspiel des LLM-Prüfblocks (05.10.2026; Nutzer: *„Ja, Voranalyse N4 vorbereiten, prüfen und gegenprüfen“*)

**Ziel:** Trennt das Urteil des **Traders** (Fassung 0.1e, 5 Stimmen) den 24-h-Ausgang der REGEL0-Handel? Das ist bis heute **ungemessen** (§20.12.5). Bis zur Antwort bleibt der Block in der Mail **Auskunft**.

**Test, nicht Betrieb:** am Desktop, gegen eine NB-Sicherung, Wegwerf-Ablage, Standard-DB unberührt. Am NB ändert sich nichts.

**Was feststeht:**
- Anker eingefroren (§20.13, `ziehe_n4_anker.py`): Entwicklungsmenge 1.000, unberührte Bestätigungsmenge 1.000, je Jahr 500, SHA-256.
- Arme, Kontaminationsprobe und Messregel nach §20.5; Prüfpunkte P2, P2b und P3 nach §20.11.5.
- Schlüssel: Nutzerwahl **A**, zweiter kostenloser Schlüssel `GEMINI_API_KEY_2`, am 05.10. getestet (3.1 und 3.5 antworten). Seit E-67 ist die alte Kette aus, damit ist auch Schlüssel 1 bis auf den Prüfblock frei.

### 23.1 Umfang und Aufrufe

| Teil | Inhalt | Aufrufe |
|---|---|---|
| **K Kontaminationsprobe** (zuerst) | (a) 50 Anker, direkt gefragt: Asset oder Zeitraum erkannt? (b) 100 Anker **benannt** gegen anonym | ~550 |
| **T Trader** (Kern) | 1.000 Anker × 5 Stimmen | ~5.000 |
| **R Rauschboden** | 100 Anker wiederholt (A/A′), 100 Anker mit vertauschter Reihenfolge der Sätze | ~1.000 |
| **Regel-Arm, Zufall** | ohne LLM: dieselben Eingaben, deterministische Regel (Lage des Schlusses in der Spanne der letzten 20 Tage, gleiche Stufenquote) · Zufall mit gleicher Quote | 0 |
| M Markt (Auskunft) | einmal je Faktenstand: 283 Tage × 5 Stimmen | ~1.400 (wahlweise) |
| **Entscheider** | ⛔ **nicht** in N4: Er ist ein Echo (39/40, §20.12.3). Er bekommt erst mit einer zweiten unabhängigen Sicht wieder eine Aufgabe (O22) | 0 |

**Kontingent** (gemini-3.5-flash-lite, 500 je Tag und Schlüssel, Zurücksetzen um Mitternacht Pazifikzeit):
- **Schlüssel 2:** Deckel 480 je Tag.
- **Schlüssel 1:** Deckel 300 je Tag. Der NB-Prüfblock braucht höchstens 150; der NB-Zähler sieht die Desktop-Aufrufe nicht (§21.1). Bleibt zu wenig übrig, steht der Block in der Mail grau da (*keine Auskunft*), die Mail geht trotzdem.
- **Zusammen ~780 je Tag:** Kern (K+T+R) **~8,5 Tage**, mit Markt ~10 Tage. Die Bestätigung (P3) später, einmal: ~5.000 Aufrufe, ~6,5 Tage.

### 23.2 Prüfen und gegenprüfen — der Selbsttest der Messregel, bevor ein Aufruf fällt

`Rechenkern_02_10/n4_selbsttest_messregel.py`, Beleg `.txt`:
- echte Anker der Entwicklungsmenge mit ihrem **echten** 24-h-Ertrag (Mittel +0,30 %, Streuung 5,46 %);
- **simulierte** Urteile in der Verteilung der Kalibrierung (stützt 10 %, neutral 45 %, dagegen 45 %), mit gepflanzter Stärke k;
- je Jahr 200 Welten mit 200 Vertauschungen.

| gepflanzt (k) | Unterschied stützt − dagegen | **R1** vorab (Tag) | R2 (Woche) | R3 Saldo der Stimmen (Woche) |
|---|---|---|---|---|
| 0 (kein Effekt) | ±0,1 Pp | **6 % / 6 %** Fehlalarm | 4 % / 7 % | 5 % / 4 % |
| 0,10 | ~1,5 Pp | 20 % / 30 % | 40 % / 42 % | 36 % / 39 % |
| 0,20 | ~3,1 Pp | 46 % / 74 % | 88 % / 93 % | 88 % / 92 % |
| 0,30 | ~4,7 Pp | **82 % / 98 %** | 100 % | 100 % |

(je 2025 / 2026)

**Was das heißt:**
- ✔ **Die Messregel ist ehrlich:** Ohne Effekt meldet sie in rund 5–6 % der Fälle etwas, wie vorgesehen.
- ⚠️ **Sie ist schwach.** Mit 1.000 Ankern findet R1 einen Unterschied zwischen *stützt* und *spricht dagegen* erst ab rund **4–5 Prozentpunkten** je Handel verlässlich in beiden Jahren. Bei 3 Pp sind es nur rund 34 % (0,46 × 0,74).
- Ein **kleiner, aber nützlicher** Effekt um 1 Pp (die REGEL0 bringt im Mittel +0,30 %) bleibt mit hoher Wahrscheinlichkeit **unentdeckt**.
- Der Grund: Nur 10 % *stützt* (~50 je Jahr), und das Vertauschen innerhalb des Tages nimmt die Marktbewegung des Tages heraus. Das ist gewollt, denn der Trader soll das **Asset** beurteilen, nicht den Markttag. 9–11 % der Anker stehen allein an ihrem Tag.

**Folgen, von mir festgelegt (fachlich beantwortbar):**
- **R1 bleibt die Hauptregel** (vorab §20.5, Tagesklammer nach dem Messstandard). R2 und R3 werden **daneben ausgewiesen** (*Gewichtung ausweisen: Tagesklammer oder gepoolt*). Sie entscheiden nichts; das hält den Mehrfachtest klein.
- **Kein Ergebnis ist ein Ergebnis mit Mindestgröße:** Trägt R1 nicht, heißt das *kein Unterschied über ~4–5 Pp*, nicht *wertlos*. Kleinere Effekte misst nur die Vorwärtsmessung (Schatten N5, 12–15 Signale je Tag, nach ~3 Monaten n ≈ 1.000) oder eine größere Entwicklungsmenge (nicht vorgesehen, Kontingent).
- **Ausgewertet wird einmal**, wenn alle Teile fertig sind, ohne Zwischenblick. Das Werkzeug gibt vorher keine Trennzahlen aus.

### 23.3 Was gebaut wird (Werkzeug, Desktop, kein Betriebscode)

| | |
|---|---|
| Läufer `n4_rueckspiel.py` | baut auf `kalibrier_llm.py` auf: Wegwerf-Ablage, Bestätigungsmenge **ausgesperrt**, NB-Sicherung als Quelle |
| zwei Schlüssel | je Schlüssel **eigener** Zähler und Tagesdeckel (Pazifik-Tag). Wert nie ausgegeben |
| fortsetzbar | jedes Urteil sofort in die Ablage; Abbruch und Neustart setzen beim nächsten Anker fort (*lange Läufe selbst neu starten*) |
| Reihenfolge | K → T → R → (M). Fällt K durch, gilt P2b (*nur noch vorwärts*): T wird **nicht** begonnen, das Kontingent bleibt gespart |
| Auswertung `n4_auswertung.py` | läuft erst, wenn T vollständig ist (Sperre); R1 Haupt, R2/R3 daneben, Regel-Arm, Zufall, Rauschboden, Signalbilanz je Asset, je Jahr |
| Prüfung vor dem Start | Trockenlauf mit Platzhalter-Client (0 echte Aufrufe), Fortsetzen nach Abbruch, Sperre der Bestätigungsmenge, beide Zähler, Standard-DB unberührt |

### 23.4 Zur Abstimmung (nur, was bei dir liegt)

| | Frage | Empfehlung |
|---|---|---|
| **N4-1** | Umfang: **Kern** (K+T+R, ~8,5 Tage) oder **mit Markt** (+~1,5 Tage)? | **Kern.** Der Markt sagt über 2025/26 zu 85 % dasselbe (§20.12.2); ein Rückspiel würde das teuer bestätigen |
| **N4-2** | Start nach dem Bau und dem Trockenlauf, **ohne weitere Rückfrage**? | **Ja.** Ich melde den Start, den Tagesstand und das Ergebnis von K, bevor T beginnt |

### 23.5 Abgestimmt und gebaut (05.10.2026; Nutzer: *„N4-1 nur Kern, N4-2 Ja – bauen, prüfen und gegenprüfen“*)

**Vorgaben des Nutzers, wörtlich umgesetzt:**

| Vorgabe | Umsetzung |
|---|---|
| *„Wenn die Messung abbricht oder der Rechner neu startet, muss alles wieder funktionieren und es darf nichts verloren gehen“* | Ablage `data/_n4/n4_ablage.db` (synchronous=FULL), **jede Stimme sofort geschrieben**, Eingaben eingefroren, Fassung als Prüfsumme, Herzschlag-Sperre, Kontingent je Schlüssel in der Ablage. Nach einem Neustart: Doppelklick `n4_start.cmd`. ⛔ **Keine Windows-Aufgabe** (Nutzer: *„ich möchte das nicht einrichten“*); ich prüfe zu Beginn jeder Sitzung den Stand |
| *„den ersten Teil der Prüfung und Messungen immer sauber durchtesten“* | `n4_pruefe.py` P1–P10 mit Platzhalter-Client vor dem ersten Gemini-Aufruf (Ergebnis unten) |
| *„wenn sich bereits ein eindeutiges Ergebnis abzeichnet, Zeit in Anpassungen stecken statt weiter zu messen“* | **Zwischenentscheide** nach 250/500/750 Ankern, gegen bekannte Wahrheit geeicht (§23.6); Anpassungskatalog §23.7 |
| N4-1 *nur Kern* | K → T → R; Markt **später**, ggf. in Kurzform (Nutzer: *„die Marktmessung kann man nachziehen bzw. in kurzer Form andenken“*) |

**Werkzeuge** (`Basisinfos/Rechenkern_02_10/`): `n4_rueckspiel.py` (Läufer, `lauf`/`stand`), `n4_auswertung.py` (Entscheide, Endbericht erst nach T), `n4_pruefe.py` (P1–P10), `n4_sequenz_selbsttest.py` (Eichung), `n4_start.cmd`, `n4_stand.cmd`.

**Beim Bauen gefunden:**
- 3 Anker ohne Eingabe (ASR, BANANAS31, INIT: unter 30 Tageskerzen). Im Betrieb bekäme der Trader ebenfalls keine Eingabe; N4 bildet das nach (*fehlt*, kein Aufruf), statt abzubrechen.
- Der Zähler des Gemini-Clients schreibt in `data/_n4/client_zaehler.db`, nie in die Standard-DB.

### 23.6 Zwischenentscheide — geeicht, bevor ein Aufruf fällt

`n4_sequenz_selbsttest.py`: echte Anker in Läufer-Reihenfolge mit echtem Ertrag, simulierte Urteile mit Stärke k. Die Vorgabe vorab war: **falscher Abbruch bei einem Effekt, den N4 sicher findet (k = 0,3, ~4,7 Pp), höchstens 5 %**.

| Kandidat (Grenzen z bei 250/500/750) | falscher Abbruch bei k = 0,3 | Abbruch ohne Effekt | Ø Anker ohne Effekt |
|---|---|---|---|
| A (−0,5 / 0 / 0,5) | 4,7 % (300 Welten) → **5,3 % (1.000 Welten) ✗** | 77 % | 572 |
| B (−1 / −0,5 / 0) | 0,3 % | 58 % | 721 |
| C (0 / 0,5 / 1) | 10,3 % ✗ | 91 % | 459 |
| **D (−1 / 0 / 0,5)** gewählt | 1,3 % → **1,8 % (1.000 Welten) ✔** | **75 %** | 629 |

- **Gegenprüfung:** A lag mit 300 Welten knapp unter der Grenze; die Nachprüfung mit 1.000 Welten zeigte 5,3 %. Erst danach wurde D gebaut: das Risiko von A lag nur beim ersten Blick.
- **Zusätzlich:** frühes TRÄGT nur bei p < 0,001 in beiden Jahren (Haybittle-Peto); ohne Effekt kam das in keiner der Welten vor.
- **Was der Läufer am Entscheid ausgibt:** nur das Wort (*WEITER / STOP-ANPASSEN / STOP-TRÄGT-FRÜH*), keine Trennzahl. Die Zahlen stehen für die Nachvollziehbarkeit in der Ablage (Tabelle `entscheid`).

### 23.7 Anpassen — wie, was und warum (vorab festgelegt)

**Wann:** bei *STOP-ANPASSEN*, bei *TRÄGT NICHT* am Ende oder bei P2b.

**Schritt 1 — WORAN** (aus der Ablage, **ohne** neue Aufrufe):

| # | Befund | Hebel |
|---|---|---|
| W1 | *stützt* zu selten (unter 30 je Jahr) | Stufen: Saldo der Stimmen statt Mehrheit (R3), zwei Stufen statt drei |
| W2 | Rauschboden: A/A′ unter 80 % gleich | mehr Stimmen oder Saldo; Temperatur |
| W3 | vertauschte Reihenfolge ändert über 20 % | Form der Eingabe (Positionsbias) |
| W4 | **Regel-Arm trennt, Trader nicht** | Die Information ist in der Eingabe, das LLM nutzt sie nicht: **Aufgabe/Prompt** (die Wette *Gegenbewegung nach Rückgang*, P1-Lehre) |
| W5 | **weder Regel noch Trader trennen** | Die Information fehlt in der Eingabe: **neue Information** (Terminmarkt, Funding, Text). Nach §20.11.5 **nicht** weiter am Prompt feilen |
| W6 | Begründungen (Stichprobe 30) argumentieren mit Trend statt Gegenbewegung | Aufgabe/Prompt |
| W7 | trennt nur in einem Jahr | Regime, kein Prompt-Fehler → Auskunft je Phase |

**Schritt 2 — WAS:**
- **Ein** Hebel je neuer Fassung, der zum WORAN-Befund gehört.
- Begründung aus der Ursache, nie aus dem Wunschergebnis (E-63).

**Schritt 3 — WIE:**
- Fassung n+1 bekommt eine **neue Ablage**, der Versuchszähler läuft mit.
- Zuerst Kalibrierlauf P1 (50 Anker), dann wieder die Entwicklungsmenge.
- Die Bestätigungsmenge bleibt **unberührt** bis zur endgültigen Fassung (P3, einmal).

**Grenze:** Nach **drei** Fassungen ohne TRÄGT bleibt der Block **Auskunft**. Der nächste Hebel ist dann nur noch neue Information (O22); das entscheidet der Nutzer.

### 23.8 Prüfung des Läufers vor dem Start (`n4_pruefe.py`, Beleg `n4_pruefe.txt`)

```
OK    P1 Anker: 1.000, Pruefsumme wie Beleg, Reihenfolge fest  
OK    P1 Reihenfolge abwechselnd 2025/2026 (je Blick gleich stark)  
OK    P1 ein Anker der Bestaetigungsmenge in der Liste -> Abbruch  
OK    P2 ganzer Lauf mit 3 % Netz- und 3 % Formfehlern: fertig, lueckenlos, keine Doppel (142 s)  []  gestoppt=('ENTSCHEID_T500',)
OK    P2 Netzfehler nie als Stimme gespeichert, Formfehler als ungueltige Stimme (wie im Betrieb)  ungueltig 132
OK    P3 16 harte Abbrueche (Prozess getoetet), davon 11 MITTEN im Lauf, und Fortsetzen: fertig, lueckenlos, keine Doppel  [] N4 ist beendet (fertig 2026-10-05 20:44:54) - nichts zu tun.
OK    P3 Eingaben nur EINMAL eingefroren (1000 Zeilen), jeder Neustart nimmt dieselben (12 Starts)  
OK    P4 Deckel je Schluessel: erst Schluessel 2 (30), dann 1 (20), dann Ende ohne Warten  {(2, '2030-01-01'): 30, (1, '2030-01-01'): 20} leer=1 stimmen=50
OK    P4 naechster Pazifik-Tag: setzt fort, nichts doppelt  stimmen 100
OK    P4 Google meldet 'Tagesbudget leer' -> Schluessel als erschoepft vermerkt, Wechsel auf den anderen  [(1,), (2,)]
OK    P5 geaenderte Fassung -> der Laeufer verweigert  
OK    P6 zweiter Laeufer bei aktivem ersten -> tut nichts  Ein anderer Laeufer ist aktiv (Herzschlag juenger als 600 s) - nichts zu tun.
OK    P7 Platzhalter in die echte Ablage -> verweigert  
OK    P8 Orakel-Urteile -> Bericht TRAEGT (oder frueh STOP-TRAEGT)  [('ENTSCHEID_K', 'WEITER (Kontaminationsprobe bestanden)'), ('ENTSCHEID_T250', 'STOP-TRAEGT-FRUEH (beide Jahre p < 0,001) - weiter zur Bestaetigung')]
OK    P8 Zufalls-Urteile -> TRAEGT NICHT  [('ENTSCHEID_K', 'WEITER (Kontaminationsprobe bestanden)'), ('ENTSCHEID_T250', 'WEITER'), ('ENTSCHEID_T500', 'STOP-ANPASSEN (der Trader trennt erkennbar nicht) - Zeit in Anpassungen, §23.5')]
OK    P10 Start ohne Konsole (pythonw, wie die Windows-Aufgabe): Stimmen gespeichert, Protokoll geschrieben  stimmen 30
OK    P9 Standard-DB und Messbasen unberuehrt  ['tradinginfotool.db', 'stundenkurse.db', 'stundenkurse_alle.db']
ALLE BESTANDEN
```

### 23.9 Lauf: Kontaminationsprobe bestanden (06.10.2026)

- `ENTSCHEID_K` am 06.10. um 07:31: **WEITER (Kontaminationsprobe bestanden)**. Weder Asset noch Zeitraum wurden erkannt (Grenze Kürzel ≥ 2 oder Monat+Jahr ≥ 6), und *benannt* trennt nicht besser als *anonym*.
- Der Läufer ist danach selbst in T weitergegangen: 172 von 997 Ankern am 06.10. nachmittags, ungültige Stimmen 0.
- Der nächste Halt ist der Zwischenentscheid nach 250 Ankern. Ausgegeben wird dann nur das Wort, keine Zahl.
- ⚠️ Die Kennzahlen der Probe stehen nur im Lauf-Protokoll als Wort, nicht in der Ablage. Sie lassen sich mit `n4_auswertung.entscheide(c, "ENTSCHEID_K")` jederzeit nachrechnen, ohne Blick auf T.

### 23.10 Teilexport 07.10.2026 07:19 — Testwoche und alle offenen Hebel-Punkte (07.10.2026)

Nutzer 07.10.: *„Teilexport am NB erledigt, prüfe die Abdeckung und noch alle offenen Punkte beim Hebel.“*

**Betrieb laut Teilexport:**
- Stundenkurse 116/116 und 533/537 auf Stand, 0 Fehler.
- Rechnung stündlich (frisch 632/636, Laufzeit rund 200 s, Modell 2026-10).
- 146 Signale, 4 mit Hebel-Schalter an, 4 Signalmails, 1 Erinnerung, 3 entfallen (keine offene Position), nachgeholt 0.
- Keine offene Hebelposition.

**Testwoche an der Kopie** (`pruefe_testwoche.py`, 03.10. 04:00 bis 07.10. 05:00):

| | Ergebnis | Einordnung |
|---|---|---|
| T1 jede Stunde gerechnet | ✔ 98/98, verloren 0 | zugleich ein indirekter Nachweis für K-MISFIRE-2: keine Stunde verloren |
| **T2 Frische** | ⛔ 45 Läufe mit 3–4 *veralteten* Assets: 1000000BOB, PROMPT, PUMPBTC (seit 05.10. 09:00), dazu STG | **Befund:** Die vier stehen bei Binance-Futures auf **SETTLING** (abgewickelt, Abfrage 07.10.). Der Nachlader zählt sie richtig als *nicht im Handel*, `regel0_rechnung` (Zeile 572: `veraltet = aktiv − frisch`) als aktiv. ⇒ funktional harmlos (kein Signal ohne Daten), aber die Frischeprüfung meldet falsch. **Kleiner Fix in der Rechnung:** Status SETTLING/BREAK des Nachladers übernehmen. Voranalyse und Ja nötig |
| T3 Laufzeit | ✔ Median 201 s, höchstens 855 s | |
| F1–F4 Mails | ✔ vollständig, rechtzeitig (Median 9 min), keine Korrektur, Ausstieg 1 verschickt / 3 entfallen | |
| **L1 Prüfblock** | ⛔ 1 von 4 gemailten ohne Trader-Zeile | **kein Betriebsfehler:** SEI, gemailt **03.10. 11:10**, also **vor** dem Einbau des Prüfblocks (Fassung 0.1e, 04.10.). Die Regel sollte erst ab dem Pull von 0.1e gelten (`--von` anpassen) |
| A1/A2 | im Rahmen (4 beobachtet, 1,8 erwartet; Korrekturen 0) | Auskunft |

**Alle offenen Hebel-Punkte (Stand 07.10.):**

| # | Punkt | Stand | nächster Schritt |
|---|---|---|---|
| H1 | **Testwoche** bis ≥ 10.10. | läuft; T2 und L1 erklärt (oben) | am 10.10. letzte Auswertung, dann **Freigabe nur mit Nutzer-Ja** (`testwoche_freigegeben: true`) |
| H2 | **Fix T2** (SETTLING als *nicht im Handel*) | neu gefunden | Voranalyse, Ja, Bau, Prüfung an der Kopie |
| H3 | **XDC**: Hebel-Schalter an, aber **keine REGEL0-Daten** (Binance führt XDC nicht) | Teilexport: *kein Signal möglich* | Nutzer: Schalter aus **oder** Datenquelle (heute keine) |
| H4 | **N4 Rückspiel** (Kern K → T → R) | K bestanden; T 202/997, wartet auf das Kontingent (Pazifik-Tag, ~07:00 UTC) | Zwischenentscheid nach 250 melden; bei *keiner aktiv* über WMI neu starten |
| H5 | **F5 / S7-6** R-R11 am NB | 05.10. zeilengleich 103/103 | Wiederholung zum Wochenende, dazu ohne `--modelle` (Training) |
| H6 | **K-MAIL-2** | offen | Nutzerblick: nächste REGEL0-Mail am Handy |
| H7 | **K-ALARM-2** | ohne Anlass | beim nächsten Halt > 45 min |
| H8 | **K-MISFIRE-2** | indirekt ✔ (T1 98/98) | eine Misfire-Mail mit Toleranz 300 s wäre ein Befund |
| H9 | **O22** Stufen und Entscheider neu prüfen | nach N4 | mit dem N4-Ergebnis |
| H10 | **O13** Positionsführung REGEL0 + **Importer 2.679** (Teilschließungen, Liquidationen) | offen | spätestens Phase 2 |
| H11 | **O21** Selbstmessung (alle Signale), **D2** Hebelstufen je Asset | offen | nach der Testwoche |
| H12 | Concrete-Sperre (Bestand ohne Watchlist-Eintrag, O26) | 1 Mail am Tag | Nutzerentscheid O26 |
| ✔ | Schalter R-4 | **Wahl A gesetzt** (E-67, 05.10.) | — |

### 23.11 Voranalyse H2 (abgewickelte Assets) und H3 (XDC) — Nutzer 07.10.: *„Ja ok 1. und 2. Was ist der Fix konkret?“*

**H3 XDC — Hebel-Schalter aus (Nutzer-Ja 07.10.):**
- Der Schalter steht in der **Produktion** am NB (`asset_hebel_settings.hebel_pruefung_erlaubt`). Er wird nicht von hier geschrieben (CLAUDE.md: die Produktion beschreibt kein Prüfskript).
- **Bedienweg:** App am NB → Asset-Übersicht → Zeile **XDC** markieren → Knopf **„Hebel-Prüfung umschalten“** (`ui/app.py:405`).
- **Nachweis:** Im nächsten Teilexport steht XDC nicht mehr in der HEBEL-LISTE, und die Zeile *Hebel-Schalter AN, aber OHNE REGEL0-Daten* ist leer.

**H2 — was am Code los ist (gelesen 07.10.):**

| Stelle | Verhalten |
|---|---|
| `agent/regel0_rechnung.py:420` | `AKTIV_H = 48`: Ein Asset gilt als **aktiv**, solange seine letzte Stunde höchstens 48 h alt ist. Erst danach zählt es als *nicht im Handel*. So steht es dort mit Absicht (*kein Frischefehler*) |
| `:517–518, :571–572` | `aktiv` = letzte Stunde ≤ 48 h · `frisch` = letzte Stunde = jetzt−1 · **`veraltet = aktiv − frisch`** |
| `agent/regel0_nachlader.py:74` `_im_handel()` | fragt bei **jedem** Lauf Binance `exchangeInfo` ab und kennt den Status (TRADING gegen SETTLING/BREAK). Das Ergebnis geht nur als **Anzahl** in `_nachlader.nicht_im_handel`, nicht als Liste je Asset |

⇒ Ein Asset, das Binance abwickelt (PROMPT, PUMPBTC, 1000000BOB seit 05.10. ~08:00, dazu STG), bleibt bis zu **48 h** *aktiv, aber nicht frisch*, also *veraltet*, und fällt danach von selbst heraus.

**Wirkung im Betrieb: keine.**
- Für Assets ohne frische Stunde gibt es kein Signal (B-8, `:557`). Das ist richtig.
- Der Datenausfall-Alarm liest `price_cache`, nicht diese Zahl.
- Betroffen sind nur die **Berichte**: `lauf.veraltet` im Teilexport und die Testwochen-Bedingung **T2**.

**Zwei Wege:**

| | Was | Wo | Eingriff in den Betrieb | Empfehlung |
|---|---|---|---|---|
| **F-a** | **Die Prüfung T2 richtigstellen.** Ein veraltetes Asset ist nur dann ein Frischefehler, wenn es **danach wieder frisch** wird (echte Lücke) oder nach 48 h **noch** aktiv ist. Ein Asset, das veraltet bleibt, bis es nach 48 h herausfällt, ist eine **Abwicklung**. Es wird als Auskunft gelistet, nicht als Fehler. Dazu **L1** erst ab dem Einbau des Prüfblocks (Fassung 0.1e, 04.10.) werten | `Basisinfos/Rechenkern_02_10/pruefe_testwoche.py` (Desktop, nur lesend) | **keiner**, die Testwoche läuft unverändert weiter | ✔ **jetzt** |
| **F-b** | **Die Rechnung kennt den Handelsstatus.** Der Nachlader schreibt je Lauf die Liste der Assets, die nicht TRADING sind (z. B. Tabelle `_handel` in `stundenkurse_alle.db`). Die Rechnung zählt sie sofort als *nicht im Handel* statt 48 h als *veraltet* | `regel0_nachlader.py`, `regel0_rechnung.py` | ja: Pull und Neustart am NB, Betriebsprüfung | **nach** der Testwoche; nur für saubere Berichte, ohne Wirkung auf Signale |

⚠️ **Warum F-b nicht jetzt:** Ein Eingriff in den Betrieb mitten in der Testwoche würde sie unterbrechen. Den gleichen Nutzen für die Auswertung bringt F-a ohne Eingriff.

⚠️ **Vorabfestlegung:** T2 und L1 sind vorab festgelegte Bedingungen (§22). F-a ändert ihre **Auslegung** ⇒ nur mit Nutzer-Ja. Danach wird die Testwoche an der vorhandenen Kopie neu ausgewertet. Die alte Auswertung bleibt mit Begründung stehen.

### 23.12 F-a umgesetzt und N4 am Zwischenentscheid 250 gestoppt (07.10.2026)

Nutzer 07.10.: *„Ok, also keine wichtige Abweichung, alles ok? Dann umsetzen. Wie weit sind wir bei den 8,5 Tagen?“*

**F-a (Testwochen-Prüfung) umgesetzt** in `Rechenkern_02_10/pruefe_testwoche.py`:
- **T2:** Frischefehler ist nur eine echte Lücke (wieder frisch vor 46 h), eine Dauer über 49 h oder eine unterbrochene Folge. Eine Abwicklung im 48-h-Fenster ist Auskunft; *offen* bedeutet unter 49 h und noch nicht entscheidbar. Die alte Zahl steht dabei.
- **L1:** gewertet ab der ersten `pruefung`-Zeile (aus den Daten: 04.10. 09:09).
- **Selbsttest an einer Wegwerfkopie** mit gepflanzten Fällen: Lücke 4 h, Dauer 56 h und Unterbrechung werden **als Fehler erkannt**, eine Abwicklung über 47 h als Auskunft.
- **Neu ausgewertet an der Kopie vom 07.10.:** *SCHLUSS: alle Bedingungen erfüllt*. T2: 4 offen (1000000BOB, PROMPT, PUMPBTC seit 05.10. 09:00 / 44 h, STG 26 h). L1: 3 von 3 mit Trader-Zeile, SEI 03.10. als Auskunft.

**N4 — ENTSCHEID_T250 am 07.10. 07:28: STOP-ANPASSEN** (z gepoolt −2,38; p je Jahr 0,92 / 0,97). Beleg `Rechenkern_02_10/n4_bericht_T250.txt`. Die Regel *Kandidat D* hat damit gegriffen, wie vorab geeicht; T ist bei 249 Ankern beendet. Die 8,5 Tage entfallen: Es läuft nur noch der Rauschboden R_v (10 von 99), voraussichtlich fertig am 08.10.

| | 2025 | 2026 |
|---|---|---|
| Trader: Unterschied *stützt* − *dagegen* (24 h) | +1,54 Pp (Band +2,98) | **−6,01 Pp** (Band −2,26) |
| Regel-Arm (antizyklisch, gleiche Quote) | −1,16 Pp | −0,22 Pp |
| R3 Rangkorrelation Stimmen-Saldo | −0,148 | −0,143 |

- **Verteilung:** *spricht dagegen* 130, *neutral* 100, **stützt 16**, uneinig 3.
- **Rauschboden:** Wiederholung A/A′ 81 % gleich. Vertauschte Reihenfolge bisher 5 von 11 gleich (R_v läuft).

**WORAN nach §23.7, Schritt 1 (vorläufig, R_v noch offen):**

| # | trifft zu? | |
|---|---|---|
| **W1** *stützt* zu selten | **ja**: 16 von 249, etwa 8 je Jahr (Grenze 30) | |
| W2 Rauschboden < 80 % | nein, knapp (81 %) | |
| W3 vertauschte Reihenfolge ändert > 20 % | **vorläufig ja** (5/11 gleich) | Endurteil nach R_v |
| W4 Regel-Arm trennt, Trader nicht | nein | |
| **W5 weder Regel noch Trader trennen** | **ja** | ⇒ nach §20.11.5 **nicht** weiter am Prompt feilen. Der nächste Hebel ist **neue Information** (Terminmarkt, Funding, Text) = **O22, Nutzerentscheid** |
| W6 Begründungen mit Trend statt Gegenbewegung | offen | Stichprobe 30 aus der Ablage, ohne Aufrufe |
| W7 trennt nur in einem Jahr | nein | |

- ⚠️ **Auskunft, nicht vorab geprüft:** Die Rangkorrelation ist in **beiden** Jahren **negativ** (−0,15), und 2026 lagen *stützt*-Urteile **schlechter** als *dagegen*. Die Prüfung war einseitig angelegt; eine Umkehr ist damit **nicht** belegt (mehrere Blicke, keine Vorabfestlegung). Ob sie hält, wäre eine eigene Messung.
- **Folge für den Betrieb:** Der LLM-Block bleibt **Auskunft** in der Mail, wie bisher als *ungemessen* gekennzeichnet. Am Signal und an der Stufe ändert sich nichts. Die Messung bestätigt jetzt, dass er **nicht trennt**.

### 23.13 Auftrag: Wie wird der LLM-Block trennend? (07.10.2026; Nutzer, E-76)

Nutzer 07.10.: *„Ja, ich schalte später XDC ab, mach bitte eine Erinnerung. Zu LLM ja, jetzt keine Entscheidung, aber die Stufe bleibt, wenn wir eine positive Lösung erreichen; hier müssen wir analysieren, wie wir das schaffen.“*

**Festgehalten:**
- **XDC:** Der Nutzer schaltet am NB selbst ab. Die Erinnerung ist eingerichtet: geplante Aufgabe `erinnerung-xdc-hebelschalter`, 07.10. 19:00, einmalig. Kontrolle **K-XDC** im nächsten Teilexport.
- **LLM:** **keine Entscheidung jetzt.** Die **LLM-Stufe bleibt im Aufbau, wenn eine positive Lösung erreicht wird.** Bis dahin bleibt sie Auskunft in der Mail.
- **Auftrag:** analysieren, **wie** der Block trennend wird.

**Weg der Analyse (Vorschlag, je Schritt mit Ursache, E-63):**

| # | Schritt | Grundlage | Aufrufe |
|---|---|---|---|
| A1 | **WORAN abschließen:** W3 (Reihenfolge) nach R_v, **W6** Stichprobe von 30 Begründungen (argumentiert der Trader mit Trend statt Gegenbewegung?), dazu die **Ursache des Übergewichts *spricht dagegen*** (52 %) | Ablage N4 | keine |
| A2 | **Ist die Information überhaupt da?** Trennen Merkmale, die das LLM sieht oder sehen könnte, *innerhalb* der REGEL0-Signale? Gemessen direkt, ohne LLM: Terminmarkt (Open Interest, Long/Short, Taker), Funding, Markpreis-Prämie, Käuferanteil, Lage zum Tagesrang, BTC-Umfeld. Wenn keines trennt, kann auch ein LLM nicht trennen (W5) | Messbasis Desktop | keine |
| A3 | **Lösungswege, je zu einem A1/A2-Befund:** (a) **neue Information** in die Eingabe, nur was in A2 trennt; (b) **andere Aufgabe**: Vergleich zweier Signale (welches ist besser?) statt Ja/Nein, gegen die Schieflage zu *dagegen*; (c) Stufe als **Saldo** der Stimmen oder als Wahrscheinlichkeit statt Mehrheit (W1); (d) die P1-Lehre: die **Wette** des Plans (*Gegenbewegung nach Rückgang*) ausdrücklich in die Aufgabe | A1, A2 | — |
| A4 | **Messplan Fassung 2** vorab: eine neue Ablage, ein Hebel je Fassung, zuerst der Kalibrierlauf P1, dann die Entwicklungsmenge. Die **Bestätigungsmenge bleibt unberührt** bis zur endgültigen Fassung | §23.7 | Kontingent |

**Grenze (vorab §23.7):**
- Nach **drei** Fassungen ohne TRÄGT bleibt der Block Auskunft.
- ⚠️ Die negative Rangkorrelation (−0,15 in beiden Jahren) ist **kein** Lösungsweg. Ein umgekehrt gelesenes Urteil wäre eine nachträgliche Deutung. Es wäre höchstens als **vorab** festgelegte, zweiseitige Hypothese auf neuen Daten zu prüfen.
- **Reihenfolge:** A1 nach R_v (voraussichtlich 08.10.), A2 am Desktop ohne Kontingent, dann Vorlage A3/A4 an den Nutzer.

**Reihenfolge festgelegt (07.10.2026, E-77):** Nutzer: *„Ok, nur damit wir die Themen nicht vermischen: Ok, wenn du meinst, können wir Hebel A1 bzw. A2 angehen oder Spot weiter umbauen – was denkst du als Experte?“* · *„Ok, dann halte alles fest in Memory, Doku und Plan, danach A1 mit Prüfung und Gegenprüfung.“*
1. **Jetzt der Hebel:** A1 (WORAN abschließen) und A2 (Ist die Information da?), beides am Desktop, ohne Kontingent und ohne Eingriff am NB.
2. **Spot-Weiterbau O28 (W2–W7) erst nach der Testwoche (ab 10.10.)**, nach Abstimmung des Bauumfangs. Grund: Betriebscode am NB würde die Testwoche stören.
3. Die Themen bleiben getrennt (T-1..T-6).

### 23.14 A1 — WORAN: Der Trader urteilt nach TREND, die Wette ist GEGENBEWEGUNG (07.10.2026)

**Belege:**
- `Rechenkern_02_10/a1_woran.py` → `.txt` (Plan im Kopf des Skripts, vorab festgelegt; nur die Ablage, keine Aufrufe)
- Gegenprobe `a1_gegenprobe.py` → `.txt`: **16 von 16 gleich** (Urteile selbst gezählt, Zahlenzerlegung zweiter Weg an 10 Ankern, Rangkorrelation mit scipy, Trend-Anteil aus dem Rohtext)

**A1-a — welche Fakten der Trader als *dagegen* nimmt** (1.245 Stimmen, Belege je Fakt):

| Fakt-Typ | Belege | davon *dagegen* | als Gegengrund |
|---|---|---|---|
| **Trend lang (60 T, 200-T-Schnitt)** | 1.145 | **75 %** | 14 % |
| Widerstand | 486 | 55 % | 5 % |
| Umsatz-Höhe | 1.213 | 50 % | 8 % |
| Unterstützung | 966 | 47 % | **23 %** |
| Umsatz an Aufwärtstagen | 610 | 48 % | 2 % |
| Marktstruktur | 1.262 | 35 % | 12 % |
| Schwankung | 614 | 6 % | 9 % |

**A1-b/c — woran das Urteil hängt und ob dieselbe Zahl die Wette ordnet:**

| Eingabezahl | Urteil (Saldo) folgt der Zahl: rho 2025 / 2026 | **24-h-Ertrag** folgt der Zahl: rho 2025 / 2026 (p zweiseitig) |
|---|---|---|
| Marktstruktur *höhere Hochs* | **+0,50 / +0,47** | −0,04 / −0,08 (0,51 / 0,18) |
| Abstand zum 200-T-Schnitt | **+0,40 / +0,24** | +0,05 / +0,05 (0,25 / 0,24) |
| Umsatz-Faktor | **+0,41 / +0,26** | **−0,14 / −0,25** (0,45 / **0,05**) |
| 60-T-Änderung | +0,33 / +0,35 | +0,09 / +0,10 (0,93 / 0,30) |
| Anteil Umsatz an Aufwärtstagen | +0,29 / +0,39 | +0,07 / −0,15 (0,49 / 0,17) |

- **Drittel:** Bei tiefstem 60-T-Rückgang sagt der Trader **zu 71 % *dagegen*, *stützt* zu 1 %**. Bei *höheren Hochs* sagt er zu 10 % *dagegen*, sonst zu 65 %.
- **W6-Stichprobe (30 Begründungen):** durchgehend Trend-Logik. *„übergeordneter Aufwärtstrend … stützt“*, *„anhaltender Abwärtstrend und schwaches Volumen sprechen gegen eine Gegenbewegung“*.

**WORAN (endgültig bis auf W3):**

| | |
|---|---|
| **W6 ✔** | Der Trader **argumentiert mit Trend und Volumen**, obwohl die Aufgabe die Wette *Gegenbewegung nach Rückgang* ausdrücklich nennt (`geplant`). Er stützt, was **wie ein Aufwärtstrend aussieht**, und lehnt ab, was **tief gefallen** ist. Genau das sind aber die Fälle, für die die REGEL0 gebaut ist |
| **W5 ✔** | **Keine** der Eingabezahlen ordnet den 24-h-Ertrag in beiden Jahren (alle p > 0,05). Der Umsatz wirkt eher **umgekehrt** (höherer Umsatz, schlechterer Ertrag; 2026 p 0,05). Die Eingabe trägt die nötige Information **nicht** |
| **Mechanismus** | Das erklärt die **negative Rangkorrelation** aus dem Bericht: Der Trader belohnt Merkmale (Umsatz, Struktur), die den Ertrag nicht oder umgekehrt ordnen |
| W1 ✔ | *stützt* selten, weil fast alle REGEL0-Signale tief gefallen sind |
| W3 | offen, nach R_v |

**Folge für A3** (die Lösungswege, *nicht* umgesetzt):
1. **Am Prompt feilen hilft allein nicht** (W5): Selbst ein Trader, der die Wette richtig liest, hätte in diesen neun Fakten nichts Trennendes.
2. Der Weg geht über **A2**: Gibt es Information, die **innerhalb** der REGEL0-Signale trennt (Terminmarkt, Funding, Markpreis-Prämie, Käuferanteil, Liquidationen, Kapitulationsmerkmale)? Nur was dort trägt, gehört in die Eingabe.
3. **Zusätzlich** zu prüfen: Die neun Fakten selbst sind **trendlastig**. Für eine Umkehrwette fehlen Umkehr-Fakten ganz.

**K-XDC:** Nutzer 07.10.: *„XDC Hebel ist ausgeschaltet und gepullt“*. Die Erinnerung ist abgeschaltet. Nachweis im nächsten Teilexport.

### 23.15 A2 — Voranalyse und Messplan: welche Information, in welcher Form, in welcher Reihenfolge (07.10.2026, VOR der Messung)

Nutzer 07.10.: *„Ja, wir müssen den LLM-Rollen jene Informationen, die sie benötigen, in der korrekten Form und Reihenfolge übergeben.“*

**Teil 1 — Was innerhalb der REGEL0-Signale (Kern) schon gemessen ist** (Register, nicht neu messen; R-R11):

| Befund | Was trennt im Kern | Steht es in der LLM-Eingabe? |
|---|---|---|
| **2.704** Liquidität | **geringe** Liquidität (USD-Volumen 24 h) hat die **bessere** Chance, 4/4 Mengen, mit Richtung (Spiegel) | ⚠️ **verkehrt herum:** Die Eingabe sagt *Umsatz beim 0,3-fachen des 20-T-Schnitts*, und der Trader wertet das als **Schwäche** (A1: Urteil +0,41 auf den Umsatz, Ertrag −0,14/−0,25) |
| 2.691 / 2.692 | **Ruhe 48 h** davor hebt Chance und Potential (sie ist Teil der REGEL0); `ema_abstand_atr` oben und `volumenschub` oben heben das **Potential**, nicht die Chance | nein |
| 2.694 / 2.697 / 2.695 | Der Kern verliert im **Gegenwind** (Regime). Ruhe 72 h hilft im schwachen und schadet im starken Markt | nein (kein Umfeld in der Eingabe) |
| 2.695 | die Kurs-Vorgeschichte ist **ausgereizt** (Tiefe davor, Tempo fallen) | ⚠️ genau diese Trendfakten **dominieren** die Eingabe |
| 2.691 | `top_konten_verh` unten +0,06 Chance, fällt aber an der Breite | nein |

⇒ **Die bekannten Informationen fehlen in der Eingabe, und die eine, die drinsteht (Umsatz), ist so formuliert, dass der Trader sie umgekehrt liest.**

**Teil 2 — neue Kandidaten, noch nicht im Kern gemessen** (Umkehr-Information):

| # | Kandidat | Gedanke | Messbar am Desktop | **Im Betrieb am NB** |
|---|---|---|---|---|
| N-a | **Markpreis-Prämie** (Futures-Markpreis gegen Spot, stündlich) | Abschlag = Verkaufsdruck am Terminmarkt | `markpreis_alle` 411 | ✔ 411 (laufend) |
| N-b | **Kapitulation:** Umsatzspitze in den Stunden des Rückgangs, gegen den eigenen Schnitt | Ausverkauf vor der Wende | Stundenkurse 537 | ✔ |
| N-c | **Rückgewinn im Signal:** Abstand des Schlusses vom Stundentief (Docht) | Käufer bereits da | Stundenkurse | ✔ |
| N-d | **Fallgeschwindigkeit:** Rückgang in ATR über 6 h und 24 h | Übertreibung | Stundenkurse | ✔ |
| N-e | **BTC-Umfeld kurz:** BTC 24 h und 7 T zur Signalstunde | Gegenwind/Rückenwind (Teil 1) | ✔ | ✔ |
| N-f | **OI-Änderung 24 h, Funding, Long/Short** | Positionsabbau = Ende des Drucks | `terminmarkt_historie` 122, `funding_historie` 302 | ◐ **nur 40 Symbole** (Prod `open_interest_snapshot`) ⇒ nur Auskunft, solange die NB-Daten fehlen |
| N-g | Käuferanteil (Taker) | Druck der Marktkäufer | `richtung_historie` 116 | ✘ am NB ⇒ nur Auskunft |

**Messplan Teil 2 (vorab):**
- **Menge:** die REGEL0-Einstiege der Rechenkern-Messung (`messe_losfahren.py`, R-R11-Basis, Ruhe 48 h, s = 0,035), **Wahl auf 2024**, **Bestätigung einmal auf 2025-01..2026-08** in den vier Mengen (wie 2.691–2.704).
- **Zielgröße:** wie im Kern: Chance (q5) und 24-h-Ertrag, dazu Potential, Spiegel.
- **Zweiseitig** (oberes gegen unteres Drittel), Nullwelt im Tagesblock, die sechs Prüfungen.
- **Trägt:** Wahl 2024 und Bestätigung in **≥ 3 von 4** Mengen, gleiche Richtung, Spiegel besteht.
- ⚠️ Die Monate der N4-Anker (2025/26) überschneiden sich mit der Bestätigung. Das ist erlaubt: Gemessen werden **Merkmale**, keine LLM-Urteile. Die LLM-Bestätigungsmenge bleibt unberührt.

**Teil 3 — Form und Reihenfolge der Eingabe** (erst nach Teil 2, als Fassung 2 nach §23.7):

| Regel | Begründung |
|---|---|
| **F1** nur Fakten, die im Kern **gemessen tragen** (Teil 1 + Teil 2); die trendlastigen Fakten ohne Wirkung (2.695, A1) **raus** oder ans Ende | A1: Sie lenken ab und werden gegen die Wette gelesen |
| **F2** jede Zahl **relativ zur eigenen Geschichte** (Perzentil je Asset) **und** in ATR, neutral formuliert, ohne Wertwörter wie *schwach* oder *stark* | Umsatz *0,3-fach* wurde als Schwäche gelesen, obwohl gering = günstig (2.704) |
| **F3** **Reihenfolge:** zuerst die Wette, dann die Fakten in der Reihenfolge ihrer gemessenen Bedeutung, das Umfeld zuletzt. Eine Gegenprobe mit **vertauschter** Reihenfolge ist Pflicht | W3 (vorläufig 5/11 gleich) ⇒ es gibt einen Positionsbias |
| **F4** **keine gemessene Richtung verraten** (z. B. *geringe Liquidität war günstig*) | Sonst wiederholt das LLM die Regel (*Echo*, Entscheider 39/40). Dann wäre die Regel selbst besser und billiger |

⚠️⚠️ **Die Grundfrage, ehrlich gestellt:**
- Ein LLM bringt nur dann einen Mehrwert, wenn es etwas kann, das die Regel nicht kann: **Fakten gewichten und verbinden**, die einzeln schwach sind.
- Trennt in Teil 2 ein Merkmal **für sich**, gehört es zuerst **in die REGEL0** (billig, prüfbar, reproduzierbar). Das LLM muss dann zeigen, dass es **darüber hinaus** trennt (Regel-Arm als Vergleich, wie in N4).
- **Positive Lösung** (E-76) heißt deshalb: Die LLM-Stufe trennt **besser als die Regel mit denselben Fakten**. Nicht: Sie trennt überhaupt.

**Reihenfolge:**
1. Teil 2 messen (Desktop, ohne Kontingent).
2. Ergebnis und Zwischenfazit zur Abstimmung.
3. Bei Erfolg Fassung 2 der Eingabe (Teil 3) mit Kalibrierlauf P1 und dem Arm *vertauschte Reihenfolge*, eine neue Ablage.
4. W3 aus R_v fließt in F3 ein.

### 23.16 Messbares Minimum für die LLM-Stufe und Einschätzung, wie realistisch *besser* ist (07.10.2026; E-78)

Nutzer 07.10.: *„Ja, zur Grundfrage teilweise ok. Ja, Ziel wäre, dass das LLM besser trennt, aber als Minimum würde ich eher gleich oder etwas darüber ansetzen, also als Bestätigung oder Gegenmeinung. Was sagst du, wie realistisch ist es, dass das LLM besser ist?“*

**Das Minimum, messbar gefasst** (gilt für jede Fassung ab 2, gegen den **Regel-Arm mit denselben Fakten**, auf der Bestätigungsmenge):

| # | Bedingung | Warum |
|---|---|---|
| **M-1 nicht schlechter** | Unterschied (*stützt* − *dagegen*) im 24-h-Ertrag **nicht signifikant unter** dem des Regel-Arms (Nullwelt Tagesblock, je Jahr) | *gleich* |
| **M-2 kein Echo** | Das LLM stimmt in **höchstens 90 %** der Anker mit dem Regel-Arm überein | sonst ist es nur eine teure Kopie der Regel |
| **M-3 die Gegenmeinung trägt** | Wo LLM und Regel **uneins** sind, liegt das LLM **in mehr als 50 %** richtig (24-h-Ertrag), Binomialtest einseitig 5 % | *etwas darüber*: Die Abweichungen enthalten Information |
| *Ziel* | Unterschied **signifikant über** dem Regel-Arm | *besser* |

Zusätzlich als Auskunft das **linke Ende**: Fängt eine LLM-Gegenmeinung die großen Verluste (24 h unter −2 ATR, Liquidationsnähe) häufiger ab als die Regel?

**Einschätzung (Experte, keine Messung):**
- **Besser trennen mit Zahlenfakten: eher unwahrscheinlich**, grob jede vierte bis fünfte Chance.
  - Der Vorteil der REGEL0 ist klein, und das Rauschen ist groß.
  - Ein LLM bringt eigenes Rauschen mit (Wiederholung 81 % gleich).
  - Es bringt Lehrbuch-Vorurteile aus dem Training mit (Trend folgen, Volumen bestätigt). Sie widersprechen genau der Umkehr-Wette (A1).
  - Bei Zahlen ist eine Regel, die an Tausenden Fällen gemessen ist, fast immer genauer.
- **Gleichwertig als Bestätigung oder Gegenmeinung (M-1 bis M-3): realistisch**, etwa eine Chance von eins zu eins.
  - Das gilt, wenn Eingabe und Aufgabe stimmen (§23.15 F1–F4).
  - Am ehesten trägt das LLM bei **Ausnahmen**: widersprüchliche Lagen, Abwicklung, Datenfehler, Extremereignisse. Das ist das **linke Ende**, nicht der Durchschnitt.
- **Wo ein LLM wirklich mehr kann:** bei Information, die eine Regel nicht fassen kann (Text, Ereignisse). Die ist bewusst nicht vorgesehen (Nutzervorgabe: keine wertlosen News; übergeordnete Kräfte nur gewichten).

### 23.17 Weitere Information (Text, Ereignisse) für das LLM: wie bewerten, wie ausgeben (07.10.2026; E-79)

Nutzer 07.10.: *„Ok, dann kurze Korrektur bzw. Klarstellung: Du kannst gerne weitere Informationen für das LLM nutzen, wenn wir diese haben. Ich frage mich nur, wie wir dies bewerten und wie das LLM dies ausgeben soll, z. B. ein neuer Partner des Assets hat investiert – die Info selbst trägt nichts, es sei denn, es erfolgt ein Kursanstieg. Wie soll das tragen?“*

**Klarstellung festgehalten:** Weitere Information für das LLM ist **erlaubt**, wenn wir sie haben. Die frühere Einschränkung *keine wertlosen News* betraf den Spot-Strang und den Fall ohne Bewertung.

**Wie eine Nachricht *trägt*:**
- Eine einzelne Nachricht trägt **nie für sich**. Tragen heißt **statistisch**: Über viele Fälle laufen REGEL0-Signale **mit** einem bestimmten Ereignistyp **besser** (oder brechen seltener ein) als Signale **ohne**.
- Der Kursanstieg ist dabei die **Zielgröße**, nicht der Beweis im Einzelfall.
- Gemessen wird wie jedes andere Merkmal: Ereignisstudie innerhalb der REGEL0-Signale, Nullwelt, beide Jahre, Spiegelprobe, M-1 bis M-3.

**Was ein LLM hier leisten kann, was die Regel nicht kann:**
- Text lesen und **einordnen**: Ist die Meldung wesentlich, ist sie neu, und ist sie **schon eingepreist**? Eingepreist heißt: Der Kurs hat seit der Meldung schon reagiert.
- Beispiel *Partner investiert*:
  - trägt **nichts**, wenn es alt oder schon eingepreist ist;
  - **möglicherweise** etwas, wenn es frisch, wesentlich und noch nicht eingepreist ist und zugleich eine REGEL0-Gegenbewegung ansteht.

**Wie das LLM es ausgeben soll — feste Form statt Fließtext** (sonst nicht messbar):

```
ereignisse: [ { typ: Finanzierung | Partnerschaft | Börsenlisting | Delisting | Sicherheitsvorfall | Regulierung |
                     Token-Freigabe | Produkt | Rechtsstreit | sonstiges,
               richtung: +1 | 0 | -1,  wesentlichkeit: 1-3,
               neu_seit_stunden: n,  eingepreist: nein | teilweise | ja  (Kurs seit Meldung in ATR),
               quelle, zeitpunkt } ]
urteil: stützt | neutral | spricht dagegen     (nur aus den Ereignissen, getrennt vom Zahlen-Urteil)
```

- In der Mail steht es als **Fakt in Worten**, z. B. *„Partner X hat investiert (Finanzierung, wesentlich 2/3), vor 18 h gemeldet, Kurs seither +0,8 ATR, teilweise eingepreist“*.
- Die **Gewichtung** liegt bei dir (Vorgabe 01.10.), bis eine Messung zeigt, dass ein Ereignistyp trägt.

⚠️⚠️ **Die harte Grenze: Rückblickend ist Text NICHT ehrlich messbar.**
1. **Kontamination:** Eine Nachricht nennt Asset und Zeit. Das LLM kennt die Folgen oft aus dem Training, die Anonymisierung aus N4 (K-Probe) ist dann unmöglich.
2. **Zeitstempel:** Für 2024–2026 fehlt uns ein Nachrichtenarchiv mit verlässlichem Veröffentlichungszeitpunkt je Coin (freie Quellen sind lückenhaft oder brauchen einen Schlüssel).

⇒ **Text und Ereignisse lassen sich nur VORWÄRTS testen:**
- Ab Start wird je REGEL0-Signal die Ereignislage in der festen Form protokolliert (ohne Wirkung auf das Signal).
- Abgerechnet wird nach genug Fällen mit Ereignis, Richtwert **≥ 100 je Ereignistyp-Gruppe** (das sind eher Monate).
- Eine Datenquelle mit Zeitstempel ist vorher zu prüfen (Datenquellen-Inventar, E-75).

**Reihenfolge:**
1. A2 Teil 2 (Zahlen, rückblickend messbar).
2. Dann Fassung 2 der Eingabe.
3. Parallel als **eigener** Punkt die Voranalyse *Ereignisquelle und Vorwärtsprotokoll*.

### 23.18 A2 Teil 2 — Ergebnis: Keine der zwölf Zahlen trennt innerhalb der REGEL0-Signale (07.10.2026)

**Werkzeug:** `Rechenkern_02_10/a2_messung.py` (Beleg `a2_messung.txt`), Auslegung im Skriptkopf **vor** dem ersten Lauf festgelegt. **Gegenprobe** `a2_gegenprobe.py` mit eigenem Rechenweg: **37 von 37 gleich** (Grundraten aus der CSV, Merkmale an 20 Einstiegen per direkter SQL-Abfrage, Wahl-Unterschiede mit numpy, Nullwelt erhält die Werte je Tag, 200 Zufallsmerkmale → 11,5 % gewählt bei Soll 10 %, gepflanztes Merkmal gefunden). Abdeckung vorab: `a2_abdeckung.py` (Beleg `a2_abdeckung.txt`).

**Basis (R-R11):** die REGEL0-Einstiege der Kern-Befunde, `data/_vergleich/kern48jbz_einstiege_{bestand, unverzerrt_1..3}.csv`, 10.481 bis 11.177 Einstiege je Menge, davon 2024 1.873 bis 2.324. Eingestellte Assets kommen aus `eingestellt_historie.db` (24 bis 29 Assets, rund 1.380 Einstiege je unverzerrter Menge). Zielgröße wie im Kern: **Chance** = +5 % vor −5 % binnen 24 h, **Spiegel** = −5 % zuerst, Auskunft 24-h-Ertrag. Abdeckung der Merkmale 90 bis 100 %.

**Regel (vorab):** Wahl auf 2024 (oberes gegen unteres Drittel, Nullwelt 500 Vertauschungen im Tag, |Unterschied| über dem 90. Perzentil), Bestätigung 2025-01..2026-08 in jeder Menge (über dem 95. Perzentil der Null **und** Chance stärker als Spiegel), **trägt bei ≥ 3 von 4**.

| Merkmal | Wahl 2024 (Chance oben − unten) | Bestätigung 2025/26 | Urteil |
|---|---|---|---|
| N-a Markpreis-Prämie | −6,6 Pp, gewählt (unten besser) | 1/4 (bestand +2,5; die drei unverzerrten 0 oder umgekehrt) | trägt nicht |
| N-b Kapitulation (Umsatz 6 h) | −4,0 Pp | — | nicht gewählt |
| N-c Docht | −0,6 Pp | — | nicht gewählt |
| N-d Fall 6 h / 24 h in Tagesspannen | −4,3 / −4,3 Pp | — | nicht gewählt |
| N-e BTC 24 h / 7 T | −3,8 / +3,0 Pp | — | nicht gewählt |
| N-f OI 24 h | −4,5 Pp | — | nicht gewählt |
| N-f Konten Long/Short | −8,6 Pp, gewählt (unten besser) | **0/4** | trägt nicht |
| N-f Taker-Verhältnis | +2,3 Pp | — | nicht gewählt |
| N-f Funding Vortag | −15,6 Pp, gewählt (unten besser) | 1/4, in `unverzerrt_1` **umgekehrt** (−6,9 Pp) | trägt nicht |
| N-g Käuferanteil 6 h | +2,2 Pp | (2/4 über der Null, ohne Wahl) | nicht gewählt |

**Lesart:**
- **Drei von zwölf** wurden 2024 gewählt. Erwartet wären durch Zufall 1,2, und drei oder mehr kommen mit rund 11 % Wahrscheinlichkeit vor. **Keines** bestätigt sich in 2025/26.
- Die Messung war **nicht blind:** Die Nullwelt in 2025/26 liegt beim 95. Perzentil bei 0,5 bis 5 Pp. Ein Unterschied von 2 bis 3 Pp Chance wäre also erkannt worden. Die Weglassprobe (ohne die fünf häufigsten Assets) ändert nichts.
- Das bestätigt **W5 aus A1** mit neuen Zahlen: **Innerhalb** der REGEL0-Signale ordnet keine weitere Zahl die Chance. Die Regel hat die messbare Zahleninformation schon ausgeschöpft (Ruhe, Lage, Liquidität 2.704).

**Was daraus folgt (zum Ziel E-76 / E-78):**
1. **„Besser als die Regel“ ist über Zahlenfakten nicht zu erreichen.** Die Information dafür ist in den Daten nicht vorhanden. Damit ist die Einschätzung aus §23.16 gestützt.
2. **Das Minimum M-1 bis M-3 (gleich, Bestätigung oder Gegenmeinung) bleibt erreichbar**, aber nur über **Form und Aufgabe** (§23.15 F1–F4) mit dem **Bestand**:
   - Liquidität und Umsatz neutral formulieren, damit das LLM sie nicht verkehrt herum liest (2.704);
   - die trendlastigen Fakten heraus oder ans Ende;
   - die Wette (Gegenbewegung) zuerst.
   
   Damit argumentiert das LLM nicht mehr gegen die Wette. Ziel ist *gleich* (M-1), nicht *besser*.
3. **Die eigentliche Chance liegt bei Information, die keine Regel fassen kann:** Text und Ereignisse (E-79). Sie ist nur **vorwärts** testbar.
4. **Was NICHT folgt:**
   - kein Urteil über den Kern selbst (er trägt über der Nullwelt und verliert an den Kosten);
   - kein Urteil über diese Merkmale **außerhalb** der REGEL0, etwa als eigener Einstieg;
   - Funding bleibt an der Nachweisgrenze, wie schon dreimal gemessen;
   - die Hebel-Freigabe nach der Testwoche hängt **nicht** daran (das LLM ist Prüfung, nicht Entscheider).

**Zur Abstimmung:**
- **Fassung 2 als Minimum-Weg:** F1–F4 nur mit dem Bestand, dazu Kalibrierlauf P1, der Arm mit vertauschter Reihenfolge und eine neue Ablage. Prüfmaß: M-1 bis M-3 gegen den Regel-Arm. Kosten: Gemini-Kontingent über mehrere Tage, frühestens nach R_v und W3.
- **Parallel** die Voranalyse *Ereignisquelle und Vorwärtsprotokoll* (E-79).

### 23.19 Fassung 0.2 im Betrieb: die A2-Kandidaten als Trader-Eingabe, Vorwärtstest (07.10.2026; E-80)

Nutzer 07.10.: *„Ok, ja, bitte berücksichtigen, gleich die neuen Kandidaten und Quellen als LLM-Rollenbeitrag sofort einsetzen in Prod; messen und vorwärtsprüfen wird ohnehin schwer und dauert.“*

**Was gebaut ist** (`agent/regel0_llm.py`, `Basisinfos/regel0_llm.yaml`):

| Teil der Trader-Eingabe | Inhalt | Quelle am NB |
|---|---|---|
| `geplant` (zuerst) | der Plan mit der Wette, unverändert | — |
| `lage_zur_signalstunde` (neu) | Umsatz 24 h als **Klasse** (unter 1 / 1–5 / 5–20 / 20–100 / über 100 Mio. USD) · Kursänderung 6 h und 24 h in % und in Tagesspannen · Schluss der Signalstunde in % ihrer Spanne · Umsatz 6 h gegen den Median der 6-h-Umsätze der 30 Tage davor · Markpreis gegen Kassakurs · Bitcoin 24 h / 7 T · Terminmarkt: Funding, Anteil Long-Konten, Open Interest 24 h | Stundenkurse und Markpreis (`regel0_nachlader`, stündlich) · Terminmarkt aus `open_interest_snapshot` (Binance, rund 40 Werte, höchstens 2 h alt) |
| `lage_des_werts` (zuletzt) | der weite Rahmen wie bisher (Struktur, lange Sicht, Marken, Schwankung, Volumen) | Stundenkurse |

- **Prompt 0.2:** sagt, was die zwei Teile sind, ohne Richtung (F4): *„Gewichte die Angaben selbst; keine Angabe ist für sich ein Ausschluss.“*
- **Bewusst gegen F1** (E-80): Einzeln trennt keiner der Kandidaten (§23.18). Sie stehen drin, weil das LLM sie verbinden könnte, und das zeigt nur der Vorwärtstest.
- **Nicht enthalten:**
  - Käuferanteil (N-g, keine Quelle am NB);
  - Text und Ereignisse: **Es gibt noch keine angebundene Quelle mit Zeitstempel.** Das ist ein eigener Punkt (Datenquellen-Inventar vor dem Bau, E-75/E-79). Kandidat zum Prüfen: Binance-Ankündigungen (Listing, Delisting, Monitoring-Kennzeichen).
- **N4 bleibt unberührt:** Der Läufer lädt den eingefrorenen Katalog `regel0_llm_0_1e_n4.yaml`. Der Fingerabdruck ist unverändert (`15db113c7ee15894`), sonst bräche R_v beim Neustart ab.

**Prüfung** (`Rechenkern_02_10/f02_pruefstand.py`, Beleg `.txt`, **20/20**):
- N4-Fingerabdruck gleich; 0.1e-Eingabe an 10 eingefrorenen N4-Ankern bitgleich;
- die Zahlen des Betriebs gleich der A2-Messung an **60 zufälligen REGEL0-Einstiegen, 60/60 je Merkmal**;
- anonym an allen 60; 0,01 s je Signal.

Suite `--paket Regel0Betrieb` ohne rote Zeile, mit sechs neuen Prüfungen E-80:
- Fassungsriegel N4;
- Reihenfolge F3;
- neutrale Sätze;
- kein Satz ohne Wert;
- Terminmarkt nur Binance mit Lesegrenze;
- der Läufer lädt die eingefrorene 0.1e.

Mail am Seiteneffekt (`pruefe_o25.py`) **11/11**.

**Vorwärtstest (wie abgerechnet wird):**
- Je Signal steht die 0.2-Eingabe in `regel0_signale.db/pruefung` (Fassung, Eingabe, Urteil, Stimmen).
- Die Zahlen sind aus den Stundendaten jederzeit nachrechenbar (dieselbe Funktion `signal_werte`).
- Abgerechnet wird gegen M-1 bis M-3 (§23.16) und den Regel-Arm, frühestens ab etwa 100 Signalen mit Urteil.
- Dazu als Auskunft: Trennt das 0.2-Urteil anders als 0.1e auf denselben Monaten?

**NB-Kontrolle K-F02** (nächster Teilexport nach Pull und Neustart):
- `pruefung`-Zeilen mit Fassung `0.2-sofort`;
- Eingabe mit `lage_zur_signalstunde`;
- keine Zeile mit Fehler `keine Eingabe` oder `nicht anonym`;
- bei einem Wert aus `open_interest_snapshot` der Terminmarkt-Satz;
- Aufrufe je Tag ≤ 150.


### 23.20 N5 — Rückspiel der Fassung 0.2 auf den N4-Ankern statt Schatten im Betrieb (07.10.2026; E-81)

**Warum kein Schatten im Betrieb:**
- Nutzer 07.10.: *„Ja, Pull und App erledigt. Hinweis: Für Prüfungen sollten wir genug Kontingent haben, es sind seit Tagen keine Signalmails gekommen.“*
- Befund aus dem Teilexport 07.10.: 146 REGEL0-Signale vom 03.10. bis 07.10., davon nur **4 mit Hebel-Schalter AN**, alle gemailt. Kein Ausfall; der Prüfblock läuft nur bei gemailten Signalen.
- Nutzer: *„Bin unsicher, was gewinnen wir an tatsächlicher Erkenntnis – prüfe, ob es sich lohnt.“*
- Rechnung aus den N4-Daten (24-h-Ertrag Schwankung 4,7 %, Designeffekt 1,45):

  | Urteile | kleinster erkennbarer Unterschied stützt − dagegen |
  |---|---|
  | 100 | 4–7 Pp |
  | 1.000 | 1,3–2,2 Pp |
  | 2.000 | 1,0–1,5 Pp |

  Ein realistischer Effekt liegt bei 0,5–1 Pp. Der Schatten bräuchte dafür etwa 3 Monate; 100 Urteile in 5 Tagen zeigen nur ein grobes Versagen.
- Nutzer: *„Ja, prüfen und gegenprüfen“* zum Rückspiel.

**Was gebaut ist** (`Rechenkern_02_10/n5_rueckspiel.py`, `n5_auswertung.py`, `n5_start.cmd`, `n5_stand.cmd`):
- **Läufer:** derselbe wie N4 (Wiederanlauf, Herzschlag-Sperre, Fassungsriegel, Kontingent, Platzhalter). Die Abweichungen sind vorab im Kopf festgelegt.
- **Fassung und Anker:** Fassung 0.2 aus dem eingefrorenen Katalog `regel0_llm_0_2_n5.yaml`, ohne Terminmarkt (rückblickend keine Betriebsquelle). Dieselben 1.000 Anker in derselben Reihenfolge wie N4, damit der Vergleich gepaart ist.
- **Reihenfolge des Betriebs:** N4 friert die Eingabe alphabetisch ein; ohne Korrektur stünde der weite Rahmen **vor** der Lage zur Signalstunde.
- **Plan:**
  - K_a (50 Anker): Das Modell soll Wert und Monat raten, denn die Bitcoin-Angaben könnten das Datum verraten.
  - ENTSCHEID_K nur aus K_a. K_b entfällt: Es prüft das Wissen desselben Modells, und das war in N4 bestanden.
  - T: 1.000 Anker × 5 Stimmen mit den Zwischenentscheiden von N4 (250/500/750).
  - R_v: 100 Anker mit vertauschten Blöcken (F3). R_w entfällt, der Rauschboden ist in N4 gemessen.
- **Kontingent:** N4 und N5 werden **zusammen** gezählt (dieselben Schlüssel). Der NB-Prüfblock auf Schlüssel 1 behält seinen Teil.
- **Start:** erst, wenn N4 beendet ist (`--warte-auf-n4`). R_v aus N4 ist die Grundlage von W3.

**Auswertung (vorab, `n5_auswertung.py`):**
- **H** wie N4: Unterschied *stützt* − *dagegen* je Jahr über der Nullwelt im Tag.
- **V1** 0.2 gegen 0.1e gepaart, nur Auskunft.
- **Regel-Arm F** (*die Regel mit denselben Fakten*, §23.16): linear auf den Zahlen der Lage zur Signalstunde, geschätzt auf den REGEL0-Einstiegen 2024; die Anker 2025/26 liegen außerhalb. Der **Auswahlanteil ist angeglichen**: je Jahr gibt es genau so viele *stützt* und *dagegen* wie beim LLM.
- **Referenz je Jahr:** die bessere der beiden Regeln (F oder N4-Arm 20 T), wenn sie über null liegt; sonst der Zufall.
- **M-1 bis M-3 und Ziel** gegen diese Referenz (§23.16). Das Ziel verlangt zusätzlich, dass H in beiden Jahren über der Nullwelt liegt.

⚠️ **Korrektur VOR dem ersten Aufruf** (aus der Prüfung, P8):
- In der ersten Fassung war die Referenz immer Regel F. Ein **Zufalls-LLM erreichte damit das Ziel**, weil Regel F 2025/26 **unter dem Zufall** liegt (−5 bis −12 Pp; dieselbe Umkehr wie in A2).
- Eine schlechte Regel zu schlagen beweist nichts. Deshalb gilt jetzt die bessere Regel, mindestens der Zufall, und das Ziel verlangt zusätzlich H.

**Prüfung** `n5_pruefe.py` (Platzhalter, Wegwerf-Ablagen, Kopie der N4-Ablage): **12/12**
- dieselben Anker wie N4;
- Eingabe 0.2 bei 100 % der Anker, kein Terminmarkt-Satz;
- Reihenfolge des Betriebs vor dem Aufruf, R_v mit vertauschten Blöcken;
- Plan wie oben;
- Kontingent N4 + N5 zusammen: N4 hat 400/300 verbraucht, also bleiben N5 genau 80/0;
- ohne beendetes N4 kein Start, mit `--warte-auf-n4` Start nach dem Ende von N4;
- Fassung 0.2 in der Ablage, N4-Fingerabdruck unverändert;
- Riegel gegen die echte Ablage;
- Orakel: Ziel, H und M-3 erreicht. Zufall: Ziel und H nicht erreicht;
- Standard-DB, Messbasen und echte N4-Ablage unberührt.

⚠️ M-1 ist beim Zufall in einem Jahr rot (p 0,021): Das ist die erwartete Fehlalarmrate von 5 % je Jahr.

**Gegenprobe** `n5_gegenprobe.py` (eigener Rechenweg): **16/16**
- Mehrheiten selbst gezählt;
- Trennwerte und Referenz mit numpy;
- Auswahlanteil und Rangzuordnung von Regel F;
- Regel F über einen zweiten Schätzweg (Normalgleichungen, Rangkorrelation 1,000000);
- M-2 und M-3 mit `binom.sf`;
- an 10 Ankern ist die N5-Eingabe **gleich** der Eingabe, die der Betrieb zeigen würde (Inhalt und Reihenfolge).

**Ablauf und Kontingent:**
- N4 beendet R_v voraussichtlich am 08.10.; N5 übernimmt den Rest des Tages.
- Bis zum Blick 250: ~1.300 Aufrufe, also etwa 2 Tage. Ganz (1.000 Anker + R_v): ~5.550 Aufrufe, etwa 7,5 Tage.
- Kein Zwischenblick; der Bericht kommt erst am Zwischenentscheid oder am Ende.


### 23.21 Der Entscheider — richtig gedacht, aber ohne die nötige Information (07.10.2026; E-82)

Nutzer 07.10.: *„Wie kann der Entscheider immer wie der Trader entscheiden? Sollte der Entscheider nicht auf Basis der Marktdaten und Trader-Informationen die Entscheidung treffen, oder haben wir den Entscheider u. U. falsch angelegt?“*

**Wie er angelegt war (M3, §20.11):** Markt und Trader urteilen unabhängig. Der Entscheider bekommt beider **Ergebnisse** (Urteil, Belege, Gegengrund), keine Rohdaten, und fällt ein Gesamturteil *bestätigt / mit Vorbehalt / Einwand*. Am Signal ändert er nichts.

**Warum er nicht trug:**

| Fassung | Eingänge | Ergebnis | Ursache |
|---|---|---|---|
| 0.1c | Markt und Trader | 75 % *mit Vorbehalt* | Der Markt sagte über 2025/26 zu 85 % *stützt*, der Trader meist *dagegen*. Der Entscheider erbte die Konstanz des Markts |
| 0.1d | nur Trader | 39/40 gleich dem Trader | Ein Eingang bringt keine eigene Information: Echo |
| 0.1e | — | aus | — |

- Der Fehler lag in den **Eingängen**, nicht in der Idee.
- Die Markt-Sicht trug keine Information (vgl. 2.599: Der Marktzustand ist vorab nicht erkennbar).
- Wer nur zwei Urteile verrechnet, ist im Kern eine Zählregel. Ein LLM bringt erst dann etwas, wenn es **Inhalte** besser abwägt als die Zählregel.

**Nutzerhaltung (E-82):** *„Ich bin schon der Meinung, dass der Entscheider Sinn macht, jedoch muss dieser genau so konstruiert werden. Offenbar ist ‚der Markt stützt einen Handel‘ zu wenig und u. U. nicht die erforderliche Information. Gut, wenn es am Plan steht, dann weiter.“*

**Was daraus für den Neubau des Entscheiders folgt** (Plan O22, nach N5):
1. **Die Frage zuerst:** Welche Information braucht ein Gesamturteil über *diesen* Handel, die weder die REGEL0 noch der Trader hat? Zum Beispiel:
   - Umfeld als **Gegenwind / Rückenwind für die Gegenbewegung** (Regime; der Kern verliert im Gegenwind, 2.694/2.697), nicht als *„stützt den Handel“*;
   - Ausnahmen am linken Ende (Abwicklung, Datenfehler, Extremereignis);
   - später Ereignisse (E-79).
2. **Jede Eingangssicht muss für sich unterscheiden**, ehe der Entscheider sie bekommt: Eine konstante Sicht macht ihn zur Mitte oder zum Echo.
3. **Gemessen wie jede Rolle:** Rückspiel auf denselben Ankern gegen den Trader allein, eine Zählregel und den Zufall. Er bleibt nur, wenn er beide schlägt.
4. **Reihenfolge:** Erst zeigt N5, ob der Trader 0.2 trennt. Dann die Voranalyse *Information für den Entscheider*, dann das Rückspiel.


### 23.22 Ereignisquellen — Datenquellen-Inventar (07.10.2026; E-79, E-75)

**Werkzeug:** `Rechenkern_02_10/e79_quellen_inventar.py`, Beleg `.txt`. Nur lesende Abrufe öffentlicher Quellen ohne Schlüssel; gespeichert wird nichts.

| Quelle | erreichbar | Zeitstempel | Archiv rückwirkend | Asset zuordenbar | Ereignistyp | Urteil |
|---|---|---|---|---|---|---|
| **Binance-Ankündigungen** (CMS der Website: Kataloge Delisting 161, Listing 48, News 49) | ✔ ohne Schlüssel | **minutengenau** | Delisting **439 Meldungen seit 02/2022**, Listing bis 10/2023, News 1.950 seit 12/2022 (darunter 26 *Monitoring Tag*) | ◐ Kürzel oft nur im **Text**, nicht im Titel (*„Delist Multiple … Contracts“*) → Detailabruf je Meldung nötig | Delisting (Spot, Futures, Margin), Listing, Monitoring-Kennzeichen | ⭐ **beste Quelle** |
| **DefiLlama Hacks** (`api.llama.fi/hacks`) | ✔ | nur **Tag** | 1.295 seit 2011 | ◐ Protokollname, nicht Token → Zuordnung nötig | Sicherheitsvorfall | brauchbar, selten |
| DefiLlama Raises / Unlocks | ✘ **kostenpflichtig** (402) | — | — | — | Finanzierung, Token-Freigabe | entfällt |
| RSS Cointelegraph / CoinDesk | ✔ | ✔ | ✘ **nur die letzten ~1–2 Tage** | Titel | allgemein | nur **vorwärts** |
| GDELT (Pressearchiv) | ✘ heute 429 (Drossel) | ✔ | ✔ | Titel | allgemein | später erneut prüfen |

**Die wichtigste Erkenntnis:**
- Ein **strukturiertes Ereignis** mit Zeitstempel und Archiv ist **kein Text-Thema mehr**: *„Delisting angekündigt vor X Stunden“* ist ein Fakt wie eine Zahl.
- Es lässt sich **rückblickend ehrlich messen**, innerhalb der REGEL0-Signale wie A2. Ein LLM braucht es dafür nicht, und eine Kontamination gibt es nicht.
- Fachlich ist das genau das **linke Ende**: Eine angekündigte Abwicklung ist ein Rückgang, auf den **keine** Gegenbewegung folgt (vgl. H2: abgewickelte Futures im Betrieb).
- Das LLM bleibt für unstrukturierten Text (RSS), und der ist nur vorwärts testbar.

**Vorschlag (zur Abstimmung), Messung E-1 am Desktop:**
- Binance-Ankündigungen 2024–2026 laden: Delisting, Monitoring, Listing, mit Detailabruf für die Kürzel.
- Den REGEL0-Einstiegen (kern48jbz, vier Mengen) zuordnen: Ankündigung **vor** der Signalstunde (kein Vorgriff).
- Messen: Chance, Spiegel, 24-h-Ertrag und linkes Ende mit Ereignis gegen ohne, Nullwelt im Tag, je Jahr.
- Trägt es, gehört es zuerst **in die REGEL0 oder in die Hebelstufe** (billig, prüfbar), dann als Fakt in die Mail. Erst danach stellt sich die Frage, ob das LLM es braucht.
- Für den Betrieb wäre später ein Abrufer am NB nötig (öffentlich, ohne Schlüssel), erst nach der Messung.


### 23.23 E-1 — Binance-Ankündigungen in den REGEL0-Signalen: nach Vorabregel TRÄGT NICHT, aber das linke Ende ist sichtbar (07.10.2026)

Nutzer 07.10.: *„Ja, E-1 messen, prüfen und gegenprüfen.“*

**Werkzeuge** (Desktop, nur lesend, Ablage `data/_e1/`):
- `e1_lade_binance.py`: 2.008 Meldungen seit 06/2023; Zuordnungen: Token-Delisting 67, Futures-Delisting 69, Monitoring 55, Paar entfernt 696, Margin 445.
- `e1_messung.py`: Auslegung vorab im Kopf.
- `e1_gegenprobe.py`: **37/37** (Kürzel auf zweitem Weg, Fenster mit eigener Schleife, Unterschiede mit numpy, Nullwelt-Eichung 4,5 % bei Soll 5 %, gepflanztes Merkmal gefunden).

Zwei Korrekturen beim Prüfen, beide **vor** der Messung:
1. Der Lader brach bei einer gescheiterten Seitenabfrage ab (*„Seite leer“*) und hatte nur 150 statt 338 Delisting-Meldungen.
2. Monitoring-Meldungen stehen auch im Delisting-Katalog.

Dazu eine Korrektur der **Gegenprobe**: Sie schnitt Rohwörter wie `PORT3USDT` zu früh mit der Asset-Welt.

**Regel (vorab):**
- Hauptzielgröße ist der 24-h-Ertrag. Das Merkmal **SCHWER** = Token-Delisting (30 T) oder Futures-Delisting (30 T) oder Monitoring-Kennzeichen (180 T), angekündigt **vor** dem Ende der Signalstunde.
- Es trägt bei ≥ 3 von 4 Mengen über dem 95. Perzentil der Nullwelt (zweiseitig), mit gleichem Vorzeichen, mit Richtung und mit ≥ 30 Ereignis-Einstiegen.

| Menge | Einstiege mit SCHWER (Assets) | 24 h mit − ohne | Chance | Spiegel (−5 % zuerst) | Verlust ≥ 10 % | Urteil |
|---|---|---|---|---|---|---|
| bestand | 63 (6) | **+1,06 %** | +0,10 | +0,04 | ±0 | nicht über |
| unverzerrt_1 | 162 (25) | **−1,14 %** | +0,02 | **+0,18** | **+8,7 Pp** | über |
| unverzerrt_2 | 140 (24) | **−1,46 %** | +0,03 | **+0,11** | **+8,1 Pp** | über |
| unverzerrt_3 | 158 (22) | **−0,95 %** | +0,06 | **+0,14** | **+6,5 Pp** | nicht über (p 0,13) |

⇒ **Nach der Vorabregel trägt SCHWER NICHT** (2 von 4, Vorzeichen uneinheitlich).

**Einzelne Arten (nur Auskunft):**

| Art | Ergebnis |
|---|---|
| **Token-Delisting** | in den drei unverzerrten Mengen 24 h **−0,9 bis −6,1 %**, **Spiegel +42 bis +52 Pp**, **Verlust ≥ 10 % +15 bis +33 Pp**; aber nur **17–24 Einstiege** (unter der Mindestzahl 30) |
| Monitoring | 2/4 über, −1,0 bis −1,6 % in den unverzerrten Mengen |
| Futures-Delisting | zu wenige (≤ 8) |
| Paar entfernt, Margin | nichts (wie erwartet: Der Token bleibt handelbar) |

**Lesart:**
- **Warum *bestand* abweicht:** Die Menge enthält nur **überlebende** Assets. Dort gibt es nur Monitoring-Fälle von Werten, die *nicht* gestrichen wurden (6 Assets, PORTAL allein 26 von 63). Die eingestellten Werte, um die es geht, fehlen dort per Bau (Grundgesamtheit, Kapitel 120.3).
- ⚠️ Das ist eine **Erklärung nach der Messung**. Nach E-63 ist sie Beschreibung und kein Nachweis; eine Prüfung braucht **neue Daten**.
- **Was die drei unverzerrten Mengen beschreiben:** Nach einer Delisting- oder Monitoring-Ankündigung läuft die Gegenbewegung **seltener**, die −5 % kommen häufiger zuerst, und große Verluste sind deutlich häufiger. Am stärksten ist das beim Token-Delisting, das aber selten ist (etwa 0,2 % der Einstiege).
- **Signalbilanz:** SCHWER betrifft etwa **1,3–1,5 %** der REGEL0-Einstiege; in der Menge *bestand* 0,6 %.

**Was daraus folgt (zum Ziel):**
1. **Keine Sperre und keine Regel.** Die Vorabregel ist nicht bestanden, und das Token-Delisting liegt unter der Mindestzahl.
2. **Als FAKT in die Signalmail ist es gerechtfertigt:** *„Binance hat am … das Delisting / ein Monitoring-Kennzeichen angekündigt“*. Das ist Information, die du in laufenden Trades selbst gewichtest (Vorgabe 01.10.), und kein Auslöser. Es braucht einen Abrufer am NB (öffentlich, ohne Schlüssel), also einen eigenen kleinen Bau mit Voranalyse.
3. **Vorwärtsprotokoll:** Derselbe Abrufer hält je REGEL0-Signal fest, ob ein Ereignis vorlag. Damit wird die Erklärung oben an **neuen** Daten prüfbar.
4. **Für das LLM:** Ein strukturierter Fakt braucht kein LLM. Er gehört in die Mail und gegebenenfalls als Satz in die Trader-Eingabe (Fassung n+1), mit Messung.


### 23.24 Voranalyse: Binance-Ankündigung als FAKT in der Signalmail und Vorwärtsprotokoll (07.10.2026, vor dem Bau)

Nutzer 07.10.: *„Ja, Voranalyse vorbereiten, prüfen und gegenprüfen. Hinweis: Wäre ein LLM-Kandidat, oder?“*

**Ziel:**
- Steht bei einem REGEL0-Signal eine Delisting- oder Monitoring-Ankündigung von Binance im Fenster aus E-1, kommt **eine Zeile als Fakt** in die Mail. Sie löst nichts aus und ändert nichts.
- Für **alle** Signale wird festgehalten, ob ein Ereignis vorlag (Vorwärtsprotokoll). Damit wird die Beschreibung aus §23.23 an **neuen** Daten prüfbar (E-63).

**Ist-Stand am Code (gelesen):**

| Teil | Stelle | Was dazukommt |
|---|---|---|
| Mail | `agent/regel0_mail._signal_teile`: Abschnitt *Einschätzung* (`ein_z`), dort steht schon `("Achtung", spot)` | eine Zeile `("Binance", satz)`; in der *Technik* Titel und Link der Meldung |
| Mailversand | `regel0_mail.versende(..., spot=...)`: jeder Zusatz in `try/except`, ein Fehler ergibt eine Mail ohne Zusatz (P-8) | neuer Parameter `ankuendigung=` nach demselben Muster |
| Stundenjob | `scheduler/background._regel0_mails` reicht `spot=_regel0_spot_hinweis` durch | `ankuendigung=` aus der Ablage, **nur lesend** |
| Definitionen | `Rechenkern_02_10/e1_lade_binance.py` (Art, Kürzel), `e1_messung.FENSTER` | **ein** Modul `agent/binance_ankuendigungen.py` für Betrieb **und** Messung (wie `signal_werte` bei 0.2) |
| Abrufer | — | **eigener** Job (Lehre 14.09.: eigenes Sammeln nicht im Job eines Verbrauchers), stündlich vor dem REGEL0-Lauf. Je Lauf nur Seite 1 beider Kataloge und Details nur neuer Meldungen: wenige Abrufe |
| Ablage | `regel0_signale.db` (Ablage der REGEL0, **nicht** die Produktion) | Tabellen `ankuendigung` (Meldungen) und `signal_ereignis` (je Signal: Art, Zeitpunkt, Titel, oder *keins*) |
| Teilexport | `nb_teilexport_betriebsdaten.py` (Abschnitte REGEL0-…) | Abschnitt **BINANCE-ANKÜNDIGUNGEN**: letzter Abruf, Fehler, neue Meldungen, Zuordnungen, Signale mit Ereignis |

**Wortlaut (nur Fakt, keine Bewertung):**
- Token-Delisting: *„Binance hat am 18.03. angekündigt, den Handel am 01.04. einzustellen.“*
- Futures-Delisting: *„Binance stellt den Futures-Kontrakt am … ein (angekündigt am …).“* Das ist für den Hebel entscheidend, denn eine offene Position würde zwangsweise geschlossen.
- Monitoring: *„Binance führt den Wert seit 24.07. mit Monitoring-Kennzeichen.“*
- ⚠️ Die Beschreibung aus E-1 (*„häufiger große Verluste“*) kommt **nicht** in die Mail: Sie hat die Vorabregel nicht bestanden.
- Entfernte Handelspaare und Margin kommen **nicht** in die Mail: kein Effekt, nur Rauschen.

**Gegenprobe am echten Betrieb** (NB-Signale 03.–07.10. aus der Kopie vom 07.10.):
- Von 146 Signalen hätten **4** die Zeile bekommen (NOM, HEI, LSK, MOVR; alle Monitoring).
- Keines davon hatte den Hebel-Schalter an, gemailt worden wäre also keines.
- QNT (Schalter an) hatte nur Margin- und Paar-Meldungen und bekäme keine Zeile.

**Datenquelle am NB (E-75):**
- Erreichbarkeit der Binance-Website vom NB ist **noch nicht nachgewiesen**. Kontrolle **K-ANK-1** im ersten Teilexport nach dem Bau: Abruf ok, neue Meldungen, keine Fehlerserie.
- Fällt der Abruf aus, geht die Mail ohne Zeile, und der Export zeigt den Ausfall (*ein Schutz, den niemand ausführt, ist keiner*).

**Risiken:**

| Risiko | Gegenmittel |
|---|---|
| inoffizielle Website-Schnittstelle, kann sich ändern | Fehler und *Meldungen ohne Zuordnung* im Teilexport gezählt; Mail ohne Zeile |
| Falschzuordnung (kurze Kürzel wie `D`, `AI`) | Kürzel aus dem **Titel** bei Delisting und Monitoring, nur Werte unserer Asset-Welt; Gegenprobe gegen E-1 |
| Abfragestau | eigener Job, wenige Abrufe, Zeitgrenze; der REGEL0-Lauf liest nur die Ablage |
| Testwoche | Bau **nach** dem 10.10. |

**Prüfung (geplant):**
- Prüfstand am Seiteneffekt: Wegwerf-Ablage, Versand abgefangen, echte `config.yaml`; die Zeile nur bei SCHWER, Ausfall gibt Mail ohne Zeile.
- Abrufer gegen eine aufgezeichnete Antwort plus eine Live-Probe.
- **Gegenprobe:** Die Betriebsfunktion setzt an **allen** E-1-Einstiegen dieselben Merkmale wie `e1_messung`.
- Suite `Regel0Betrieb`: neue Prüfungen, kein Schreiben in die Produktion.

**LLM-Kandidat? (Nutzerhinweis) — ja, aber in dieser Reihenfolge:**
1. **Der Fakt selbst braucht kein LLM:** Er ist strukturiert und zeitgestempelt. In die Mail gehört er deterministisch, das ist billig, prüfbar und ohne Kontingent.
2. **Als Satz in der Trader-Eingabe ist er ein guter Kandidat (Fassung 0.3).** Gerade an **Ausnahmen** sollte ein LLM laut §23.16 am ehesten etwas bringen. Anonym formuliert, z. B.: *„Die Börse hat vor 5 Tagen angekündigt, den Handel dieses Werts in 9 Tagen einzustellen.“*
3. **Gemessen wird gezielt, denn N5 hat dafür zu wenige Fälle** (etwa 1,4 % der Anker):
   - Rückspiel auf allen REGEL0-Einstiegen mit Ereignis (etwa 150), **gepaart mit und ohne den Satz**, 5 Stimmen; etwa 1.500 Aufrufe, rund 2 Tage, nach N5.
   - Frage: Kippt das LLM durch den Satz, und **liegt es damit richtig**? Das ist M-3 auf diesem Teil.
   - Kontaminationsprobe für diese Untermenge, denn Delistings sind auffällige Ereignisse.
4. ⚠️ **Echo-Gefahr:** Das LLM wird bei *Delisting* fast immer *dagegen* sagen. Das wiederholt nur den Fakt. Wert hat es nur, wenn es **unterscheidet**, z. B. Monitoring ohne Folgen gegen Delisting mit Folgen.

**Zur Abstimmung:**
- **(a)** Bau nach der Testwoche: Abrufer, Ablage, Mailzeile, Vorwärtsprotokoll, Export-Abschnitt.
- **(b)** Das LLM-Rückspiel nach N5 als Kandidat für Fassung 0.3.


**Abgestimmt (07.10.2026, E-83):** Nutzer: *„Ja, a und b.“*
- (a) Bau ab dem 10.10. nach der Testwoche, mit Prüfstand, Gegenprobe gegen E-1 und Suite.
- (b) LLM-Rückspiel nach N5 als Kandidat für Fassung 0.3.


### 23.25 P1 Betriebsprüfung 08.10. — L1 rot: Der Prüfblock scheiterte im Mailversand an einer Sperre der Ablage (eigener Fehler aus E-57)

**Grundlage:** Teilexport 08.10. 05:54, voller Export 08.10. 06:32 (72 h Protokoll), Testwochen-Prüfung an der Kopie.

**Testwoche 03.10. 04:00 bis 08.10. 03:00:**
- T1 120/120, T2 ok (4 Abwicklungen als Auskunft), T3 Median 200 s;
- F1–F4 ok (5 Schalter-Signale gemailt, im Median 9 min nach Schluss der Stunde);
- A1/A2 im Rahmen;
- **⛔ L1: BEAMX (07.10. 19:00 UTC, gemailt 20:11) ohne Trader-Zeile.**

**Ursache, am Seiteneffekt nachgewiesen** (`Rechenkern_02_10/pruefe_sperre_pruefblock.py`: echter `versende` mit echtem `pruefe_signal`, Platzhalter-Client, Wegwerf-Ablage):
- `regel0_mail.versende` führt seit E-57 (05.10. 00:19, Commit 3c8f9b1) zuerst `UPDATE signal SET mail_verpasst_am …` aus. Committet wurde **nur bei rowcount > 0**.
- sqlite3 öffnet die Schreibtransaktion aber schon mit dem UPDATE. Die Ablage blieb gesperrt.
- Der Prüfblock schreibt über eine **eigene** Verbindung. Er wartete 30 s und scheiterte mit `database is locked`.
- Die Mail ging trotzdem raus, mit *Prüfung nicht verfügbar (OperationalError)* und ohne Zeile.
- Das NB-Protokoll passt genau dazu: 22:10:15 Markt-Eingabe, 22:11:06 Versand (51 s), kein Fehlereintrag, denn `versende` hielt nur den Typnamen fest.
- **Vor** der Korrektur: 34 s, `database is locked`, 0 Zeilen. **Nach** der Korrektur: 1 s, Markt- und Trader-Zeile (Fassung 0.2).
- Nicht die Ursache: Fassung 0.2 (nachgestellt, schreibt beide Zeilen), die Anonymitätsprüfung, die Zeitgrenze (Markt-Eingabe 1 s gegen die NB-Kopie).

**Warum die Suite es nicht fand:** Sie prüfte `pruefe_signal` **für sich** und `versende` mit einem Prüfblock-Ersatz, nie den **Weg** dazwischen (*„ein Test deckt die Funktion ab, nicht den Pfad“*).

**Korrektur** (`agent/regel0_mail.py`):
- `c.commit()` nach dem UPDATE gilt jetzt **immer**.
- Ein gescheiterter Prüfblock steht mit Grund im **Protokoll** (`REGEL0-Prüfblock … gescheitert: …`).
- Neue Suite-Prüfung `§23.25` im Paket `Regel0Betrieb`: der Prüfblock aus dem Mailversand mit Zeilen, ohne Fehler, unter 15 s. Die Probe schlug vor der Korrektur fehl.
- Suite `Regel0Betrieb` vollständig grün, Mail am Seiteneffekt 11/11.

**Was sonst gilt (Export):**
- K-XDC erledigt: XDC ist nicht mehr in der Hebel-Liste, *„Schalter an ohne Daten“* steht auf 0.
- REGEL0-Datenbasis und -Rechnung lückenlos.
- Protokoll ohne Störung im Hebel-Betrieb. Einzelne Netzfehler (Bitpanda 05.10. 23:04); `refresh_history` nach dem Neustart am 07.10. mit neuem Tagestakt (Auskunft).
- 0 offene Hebel-Positionen.

**Folge für die Testwoche:**
- L1 bleibt für BEAMX **rot**, das ist ein Fakt.
- Nach dem Pull kann L1 für die restlichen Signale zeigen, dass der Prüfblock arbeitet.
- Die Freigabe am 10.10. (Nutzer) bewertet L1 mit dieser Ursache: ein Fehler im **Prüfblock**, nicht in der REGEL0; die Mail ging rechtzeitig und vollständig raus.


### 23.26 O30 / P2 — Externe Recherche: Kandidaten für REGEL0-Beiträge und LLM-Information (08.10.2026)

**Vorher das Register (R-R11):**
- `funding` und `oi_aenderung` trugen im **Altbestand** (H20, vor dem Hebelneubau, nur als Vergleich).
- **Innerhalb** der REGEL0 trug keiner von beiden (A2, §23.18).
- `stablecoin_kapital` ist registriert, aber **nie gemessen**.
- Liquidationen, Orderbuch, Token-Freigaben, Nachrichten und Aufmerksamkeit: **nie gemessen**.

**Was die Literatur sagt (Kurzfassung, Quellen unten):**
- **Kurzfristige Gegenbewegung** (arXiv 2608.21888, 08/2026, 183 Binance-Paare, 15-Minuten-Kerzen, außerhalb der Stichprobe geprüft): In 90 % der Paare tritt eine Umkehr auf. Sie konzentriert sich **nach Bewegungen, die von aggressiven Taker-Aufträgen getrieben sind**, und wächst mit deren Intensität. Die **verbrauchte Orderbuch-Tiefe bedingt sie nicht**. Der Vorteil liegt bei 1,3 bp gegen 5 bp Kosten. ⇒ Das passt zur Wette der REGEL0, allerdings auf viel kürzerem Horizont.
- **Kleine, illiquide Werte kehren kurzfristig um** (Liu/Tsyvinski/Wu, schon §16.1). Das ist dieselbe Richtung wie 2.704 (geringe Liquidität günstiger).
- **Funding/OI:** Die Befunde sind widersprüchlich. Steigendes Funding folgt eher dem Kurs, als dass es ihn anführt (Richey May 2024); auf Marktebene zeigen sich Hinweise für BTC (SSRN 2026, Vorabdruck). ⇒ Das deckt sich mit A2: innerhalb der Signale nichts.
- **Token-Freigaben** (Keyrock 12/2024, über 16.000 Ereignisse): 90 % drücken den Kurs, die Wirkung beginnt etwa **30 Tage vorher**, und große Freigaben wirken stärker.
- **Negative Börsen-Ereignisse** (Ereignisstudie: Listing/Delisting/SEC) wirken stärker als positive. ⇒ Das stützt E-1/O29.
- **Aufmerksamkeit** (Google-Suchen, Twitter-Erwähnungen): Sie führt eher zu **Fortsetzung**, kaum zu Umkehr. ⇒ Das spräche bei der REGEL0 eher als Gegenwind.
- **Liquidationskaskaden:** keine Studie, die eine Umkehr danach außerhalb der Stichprobe misst; aus der Praxis heißt es *„kann überschießen, kann echte Neubewertung sein“*.

**Kandidatenliste** (nichts davon ist gemessen; Regel für P7: einzeln, vorab festgelegt, zweiseitig, innerhalb der REGEL0-Einstiege wie A2):

| # | Kandidat | Gedanke | Daten rückwirkend | im Betrieb am NB | Kosten | Erwartung |
|---|---|---|---|---|---|---|
| **K1** | **Taker-Verkaufsdruck im Fall**: Anteil der Marktverkäufe in den fallenden Stunden × Umsatzschub | Umkehr folgt aggressivem Fluss (2608.21888). Einzeln trugen Käuferanteil und Kapitulation in A2 nicht (`g_kauf6` war 2/4 über der Null, aber nicht gewählt); die **Verbindung** ist neu | ✔ `richtung_historie` (Desktop, 116 Symbole); für alle 537 aus dem Binance-Archiv (aggTrades oder Kerzen mit Taker-Anteil) | ✘ heute nicht; die Binance-Stundenkerzen liefern den Taker-Kaufumsatz **mit**, der Nachlader müsste ihn mitschreiben | frei | mittel |
| **K2** | **Orderbuch-Schieflage und -Tiefe** (Kaufseite gegen Verkaufsseite bei ±1/2 %, Tiefe gegen Umsatz) | Wer stützt den Kurs nach dem Fall? Literatur: Tiefe bedingt die 15-Minuten-Umkehr nicht; für 24 h offen | ✔ **frei**: Binance-Archiv `futures/um/daily/bookDepth` (alle 30 s, ±0,2–5 %, ab 2024 bis heute, auch kleine Werte wie BEAMX). Für die Einstiege ~4 GB Download | ✔ frei live (`/fapi/v1/depth`) | frei | niedrig bis mittel |
| **K3** | **Token-Freigabe** in den 30 T vor oder nach dem Signal | Keyrock: Druck ab 30 T vorher; wie E-1 ein Fakt mit Zeitstempel, das linke Ende | ✘ frei nicht (DefiLlama-Unlocks kostenpflichtig); Tokenomist, The Tie, Messari kostenpflichtig, Preise auf Anfrage | ✘ | **kostenpflichtig** | mittel (linkes Ende) |
| **K4** | **Liquidationsspitze** vor dem Signal (je Asset, marktweit) | Überschießen nach Zwangsverkäufen | ✘ frei nicht mehr (Binance-Archiv: 404); **CoinGlass Hobbyist 29 $/Monat** (nur privat, Historie je nach Intervall), Coin Metrics kostenpflichtig | ✔ frei **vorwärts** (Binance-Stream `!forceOrder@arr`) | 29 $/Monat oder nur vorwärts | unklar |
| **K5** | **Nachrichtenaufkommen** je Asset gegen den eigenen Schnitt | Aufmerksamkeit führt zu Fortsetzung, also möglicher Gegenwind für die Umkehr; als **Zahl** ohne LLM messbar, damit ohne Kontamination | ◐ freies Archiv *Free Crypto News* (cryptocurrency.cv, CryptoPanic-basiert, ab 2017, Zeitstempel und Ticker), **Abdeckung und Lizenz zu prüfen**; CoinDesk-Gratisstufe seit 05/2026 eingestellt; CryptoPanic kostenpflichtig | ◐ dasselbe Archiv vorwärts | frei (zu prüfen) | niedrig bis mittel |
| K6 | `stablecoin_kapital` | Zufluss in den Markt | ✔ DefiLlama (frei) | ✔ | frei | ⚠️ **Marktgröße, kein Beitrag je Asset** (stehende Regel) ⇒ nur als Achse oder Auskunft |
| — | Delisting/Monitoring | E-1 gemessen, O29 abgestimmt | | | | erledigt |

**Für das LLM** (E-79): Text ist rückblickend nicht ehrlich prüfbar. Die einzige freie Quelle mit Archiv ist K5. Für das Vorwärtsprotokoll eignet sich derselbe Dienst; RSS geht nur vorwärts. Für einen Bau ist das nicht reif; erst die Datenprobe K5.

**Vorschlag für P7 (nach der Freigabe, einzeln, Desktop):**
1. **K1** zuerst: Die Daten liegen am Desktop, die Literatur ist am stärksten, und es passt zur Wette. Vor einem Betrieb müsste der Nachlader den Taker-Anteil mitschreiben (E-75).
2. **K2** danach: frei und neu, aber ein größerer Download.
3. **K5** nur als **Datenprobe** (Abdeckung unserer Assets 2024–2026, Zeitstempel, Lizenz), noch keine Messung.
4. ⛔ **K3 entfällt, K4 nur vorwärts.** Nutzer 08.10.: *„Immer nur kostenfreie Angebote und Quellen nutzen ist eine Regel aktuell bei uns im Projekt.“* Für Token-Freigaben gibt es keine freie Quelle mit Historie. K4 Liquidationen bleibt als **freies Vorwärtsprotokoll** (Binance-Stream `!forceOrder@arr`) möglich, ein eigener kleiner Punkt nach P7.

**Quellen:**
- [arXiv 2608.21888](https://arxiv.org/abs/2608.21888) · [arXiv 2608.09576](https://arxiv.org/pdf/2608.09576)
- [Bitcoin intraday predictability (ScienceDirect)](https://www.sciencedirect.com/science/article/abs/pii/S1062940822000833)
- [Richey May Perps Primer 06/2024](https://richeymay.com/wp-content/uploads/2024/07/MktIntel_2024.06.10_Perps-1.pdf) · [SSRN 6725492](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6725492)
- [Keyrock-Unlocks (BeInCrypto)](https://beincrypto.com/keyrock-research-token-unlocks/) · [Tokenomist API](https://docs.tokenomist.ai/api-documents/csv-export) · [The Tie Unlock API](https://thetie.io/solutions/token-unlock-api)
- [CoinGlass Preise](https://coinglass.com/pricing) · [Binance Liquidation Streams](https://developers.binance.com/docs/derivatives/usds-margined-futures/websocket-market-streams/All-Market-Liquidation-Order-Streams) · [binance-public-data Issue 337](https://github.com/binance/binance-public-data/issues/337) · [Coin Metrics Liquidations](https://docs.coinmetrics.io/market-data/market-data-overview/liquidations/futures-liquidations)
- [Free Crypto News](https://mcpservers.org/servers/nirholas/free-crypto-news) · [CoinDesk-API-Alternativen (CoinStats)](https://coinstats.app/blog/top-coindesk-api-alternatives-for-crypto-data/)
- [Ereignisstudie Krypto-Ereignisse (RePEc)](https://ideas.repec.org/a/eme/sefpps/sef-08-2024-0521.html) · [Aufmerksamkeit, CFR Köln 25-02](https://www.cfr-cologne.de/download/workingpaper/cfr-25-02.pdf) · [Hoang/Vo, RePEc](https://ideas.repec.org/a/eee/beexfi/v44y2024ics2214635024001060.html)


### 23.27 Betrieb NB: 40 Geister-Watchdogs — Ursache und Korrektur (08.10.2026)

Nutzer 08.10.: *„Beim Beenden der App dürften immer wieder Prozesse hängen bleiben – prüfe dies, damit diese immer sauber beendet werden.“*

**Befund am NB** (Prozessliste, nur lesend):
- 40 Watchdog-Prozesse seit dem 20.09., alle von `explorer.exe` gestartet (Verknüpfung), **ohne Fenster**;
- dazu der neue Watchdog von 07:02 mit `main.py` als Kind.

**Ursache (in `pystray` und `monitor/watchdog.py` belegt):**
- *„Beenden“* ruft `icon.stop()`. Das setzt `icon.visible` nicht auf False.
- Die Schleife `while icon.visible` im Überwachungs-Thread (kein Hintergrund-Thread) lief endlos weiter und hielt den Prozess am Leben.
- Zuvor hatte der Watchdog seine PID-Datei gelöscht, die Sperre gegen Doppelstarts ließ den nächsten durch.
- ⇒ **Jedes „Beenden“ über das Tray hinterließ einen Geister-Watchdog.**
- ⚠️ Ein Geister-Watchdog prüfte weiter die Neustart-Anforderung der Fernsteuerung und hätte eine zweite `main.py` starten können.

**Korrektur** (`monitor/watchdog.py`):
- Die Schleife hängt an einem Ende-Ereignis.
- App normal geschlossen (Code 0): Der Watchdog endet mit. Bei einem Absturz bleibt er als Warnung stehen.
- PID-Datei: nur die eigene wird gelöscht.
- Zweiter Start: kein wartendes Fenster mehr, er endet sofort.

**Nachweis** `monitor/pruefe_watchdog_ende.py`: vor der Korrektur 1/5 (W1 zeigte genau den Geister-Watchdog), danach **5/5**. ⚠️ W5 schlug vorher an einer falschen Annahme der Probe fehl (PID 4 ist ohne Adminrechte nicht abfragbar). Das Verhalten des alten Codes bei W5 ist deshalb nur am Code belegt.

**NB-Ablauf** (die Korrektur wirkt erst beim nächsten Start des Watchdogs):
1. Die 40 alten beenden. Unkritisch: `main.py` ist das Kind des Watchdogs von 07:02.
2. Pull.
3. Das App-Fenster normal schließen. `main.py` endet sauber; der laufende Watchdog hat noch den alten Code und bleibt deshalb stehen.
4. Ihn beenden, dann über die Verknüpfung neu starten.

Kontrolle **K-WD-1**: Danach läuft genau ein Watchdog. Nach dem nächsten *„Beenden“* + Neustart ist es immer noch genau einer.


### 23.28 P3 — O29 vorgebaut, Schalter AUS (08.10.2026; E-83/E-84)

**Bedingung E-84 erfüllt:** P1 verlangte keine Änderung an dem, was O29 braucht (die Korrektur §23.25 betrifft den Mailversand, nicht die Einbaustelle). P2 (§23.26) ändert den Zuschnitt nicht.

**Gebaut:**

| Teil | Stelle |
|---|---|
| Modul | `agent/binance_ankuendigungen.py`: Regeln wie E-1, Abruf (Seite 1–2 beider Kataloge, Details nur neuer relevanter Meldungen), Fenster je Signal, Mailteile, Vorwärtsprotokoll |
| Schalter | `regel0_betrieb.yaml` `ankuendigung_aktiv: false` (Vorgabe AUS, je Lauf gelesen, kein Neustart nötig) |
| Job | `scheduler/background.binance_ankuendigungen_job`, stündlich zur Minute 58 (vor Nachlader :05 und Mailversand); nur mit Schalter **und** am Betriebsgerät (`betrieb_erlaubt`, wie der Nachlader) |
| Mail | `regel0_mail.versende(..., ankuendigung=)`: Zeile *Binance* in der Einschätzung, Titel und Link in der Technik; ein Fehler gibt eine Mail ohne Zeile (P-8) |
| Ablage | `regel0_signale.db`: `ankuendigung`, `ankuendigung_ereignis`, `ankuendigung_lauf`, `signal_ereignis` |
| Teilexport | Abschnitt **BINANCE-ANKÜNDIGUNGEN** (Schalter, Läufe, Fehler, Zuordnungen, Vorwärtsprotokoll) |

**Wortlaut (nur Fakt):**
- *„Binance hat am 03.08. angekündigt, den Handel am 17.08. einzustellen.“*
- *„Binance führt den Wert seit 24.07. mit Monitoring-Kennzeichen.“*
- *„Binance stellt den Futures-Kontrakt am … ein (angekündigt am …).“*

**Prüfung:**
- Prüfstand `o29_pruefstand.py` **10/10** am Seiteneffekt: Schalter AUS ohne Wirkung; Archiv-Antworten AN ergeben die richtigen Sätze; Margin/Paar ohne Zeile; Abruffehler gibt eine Mail ohne Zeile; Vorwärtsprotokoll für alle Signale; Job am Desktop übersprungen; echter Abruf (Live-Probe 100 Meldungen); Standard-DB unberührt.
- Gegenprobe `e1_betrieb_gegenprobe.py` **3/3**: Art und Kürzel an allen 2.008 Meldungen gleich E-1, Fenster an allen 43.183 Einstiegen gleich.
- Suite `Regel0Betrieb` 76/76 (3 neue O29-Prüfungen), Mail `pruefe_o25` 11/11.

⚠️ **Dabei gefunden: ein Umsetzungsfehler in E-1.**
- Das Ende des Monitoring-Kennzeichens („Kennzeichen entfernt“) griff in `e1_messung` **nie**. Die Meldung trägt das Kürzel nur im Titel, gesucht wurde in den Zuordnungen. 67 Einstiege waren so zu viel als Monitoring gezählt.
- Die Vorabregel bleibt; korrigiert ist ihre Umsetzung. Danach wurde E-1 neu gerechnet (Nachtrag §23.23).

**NB:** Ein Pull ist harmlos, der Schalter ist AUS. **Einschalten in P5** (nach der Freigabe), dann Kontrolle K-ANK-1.


**Nachtrag zu §23.23 (08.10.2026) — E-1 korrigiert neu gerechnet** (Monitoring-Ende jetzt über den Titel, wie vorab festgelegt):

| Menge | mit SCHWER | 24 h mit − ohne | Spiegel | Verlust ≥ 10 % | Urteil |
|---|---|---|---|---|---|
| bestand | 48 | +1,14 % (ohne PORTAL −0,30 %) | +0,07 | +0,5 Pp | nicht über |
| unverzerrt_1 | 145 | **−1,33 %** | +0,19 | **+9,9 Pp** | über |
| unverzerrt_2 | 123 | **−1,74 %** | +0,12 | **+9,5 Pp** | über |
| unverzerrt_3 | 140 | **−1,16 %** | +0,16 | **+7,5 Pp** | nicht über (p 0,07) |

- ⇒ **SCHWER trägt weiterhin NICHT** (2/4). Die Effekte in den unverzerrten Mengen sind etwas deutlicher als in der ersten Fassung.
- Monitoring allein: 3/4 über, scheitert aber am Vorzeichen (*bestand*).
- Die Folgen bleiben dieselben: keine Regel, nur der Fakt in der Mail und das Vorwärtsprotokoll (O29).
- Erste Fassung als Beleg: siehe Git-Verlauf von `e1_messung.txt`.

**H13 (neu, 08.10.2026, aus Spot §28.4):** `importer/bitpanda_margin_positions.auto_add_unknown_hebel_symbols` sucht das Bitpanda-Asset über das **Kürzel** (`find_listed_asset(pos.symbol)`). Bei Doppelbelegungen wie **BIO** (im Bitpanda-Katalog Aktie *und* Token) kann eine Hebel-Position dem falschen Asset zugeordnet werden. Heute ohne Folge, denn es gibt keine offene Hebel-Position. ➤ Zusammen mit O26 auf die Asset-ID umstellen; eine gemeinsame Zuordnungsregel für Hebel und Spot.


### 23.29 Betriebsprüfung 09.10. (Teilexport 06:46, Diagnose 06:52) — Testwoche bis 09.10. 04:00 an der Kopie, L1 rot aus neuem Grund

**Grundlage:**
- `nb_betriebsdaten_T440.txt`, Schluss *vollständig*.
- REGEL0-Kopie SHA-256 `4a19220fe4b64627` (277 Signale, 145 Läufe), lokal in den Scratchpad kopiert.
- `pruefe_testwoche.py --von "2026-10-03 04:00"`.
- 72-h-Protokoll aus der Diagnose (7.893 Zeilen).

| Bedingung | Ergebnis |
|---|---|
| T1 jede Stunde gerechnet | ✔ 145/145, verloren 0. **Damit ist auch die Neustart-Kontrolle vom 08.10. erledigt** |
| T2 Frische | ✔ Frischefehler 0 (Abwicklung im 48-h-Fenster: 1000000BOB, PROMPT, PUMPBTC, STG, Auskunft) |
| T3 Laufzeit | ✔ Median 198 s, höchstens 855 s |
| F1–F4 Mails | ✔ 9 von 9 gemailt, Median 9 min, Korrektur 0, Ausstieg 1 verschickt / 4 entfallen |
| **L1 Prüfblock** | ⛔ 8 gemailt, **2 ohne Trader-Zeile**: BEAMX 07.10. (Sperre der Ablage, §23.25, behoben) und **BNB 08.10. 16:00 (neu)** |
| A1 / A2 | im Rahmen (9 beobachtet, 5,4 erwartet; Korrekturen 0) |

**Befund BNB (Ursache am Code und an den Daten belegt):**
- `markt` brauchte **135,2 s** (5 Stimmen, Fassung 0.2); die Zeitgrenze des Prüfblocks liegt bei **120 s**.
- Danach wurde `trader` übersprungen: `regel0_llm.pruefe_signal`, Zeile 710–712 (*Zeitgrenze erreicht*) **ohne `_merke`**, also **ohne Zeile in der Ablage**.
- Die maßgebliche Rolle fiel damit **still** weg, weil die reine Auskunftsrolle zuerst lief und die Zeit verbrauchte.
- Sonst läuft `markt` in 8–10 s; BNB ist ein Ausreißer (Antwortzeit des Modells).

**Kein Befund:**
- NEAR 04.10. und ALGO 09.10. haben nur eine `trader`-Zeile, weil `markt` bei gleichen Fakten **mit Absicht wiederverwendet** wird (Zeile 702–706, keine neue Zeile). L1 zählt nur `trader`.
- **K-F02 ✔:** Alle `trader`-Zeilen der Fassung 0.2 (TURBO, ALGO, KAIA) enthalten `lage_zur_signalstunde` und den Terminmarkt-Satz. Keine Zeile *keine Eingabe* oder *nicht anonym*; Aufrufe 30 am 08.10. (≤ 150).
- **K-PRUEF-1:** Die Sperre ist behoben, es gibt keine Fehlerzeile mehr. Das erste gemailte Signal nach dem Pull (BNB) fiel aber aus dem **neuen** Grund; TURBO und KAIA danach sind vollständig.
- **Signal-Sprung:** 08.10. 22:00 bis 09.10. 03:00 UTC 80 Signale in 6 h (sonst 1–2 je Stunde): ein **marktweiter Rückgang**. Die REGEL0 löst je Asset aus, also viele zugleich; die *endgültigen* Stufen folgen eine Stunde später. Kein Fehler, aber die Signale dieser Nacht sind **gleichlaufend** (dasselbe Ereignis).
- **Offene Hebelposition BTC LONG 3×** seit 04:38 UTC (Eigenkapital 500 €, Kredit 1.000 €, Liquidation geschätzt 53.907): **kein** REGEL0-Signal zu BTC in der Ablage; Nutzerbestätigung erbeten.
- Protokoll: Fehler nur `yfinance … possibly delisted` für Aktien/ETFs im Bestand (VST, VVMX, IS0C, CEBS, X136, DBPK, EXH3, PLTR, BW, G2X, ROL, ^IXIC), nicht im Hebel-Pfad. Die Prüfblock-Zeilen stehen im Protokoll des eigenen REGEL0-Prozesses, nicht im Hauptprotokoll; Nachweis über die Tabelle `pruefung` (0 Fehlerzeilen).
- **K-WD-1:** Am Export **nicht prüfbar** (keine Prozessliste); Nutzerblick in den Task-Manager nötig.

**H14 (neu): Zeitgrenze im Prüfblock**, Vorschlag zur Abstimmung (Bau erst nach der Testwoche, eine NB-Änderung zur Zeit):
- (a) **`trader` zuerst**, `markt` danach (nur Auskunft);
- (b) jedes Überspringen **mit Zeile** ablegen (`_merke(... "Zeitgrenze erreicht")`), damit L1 und der Export es sehen;
- (c) die Zeitgrenze **je Rolle** statt gemeinsam.

**Nachtrag 09.10. — K-WD-1 ✔ und eine Lücke in der Hebelführung (H15):**
- Der Nutzer bestätigt: genau **ein** Watchdog läuft (K-WD-1 ✔), und BTC LONG 3× ist seine eigene Position (nicht aus der REGEL0).
- **Befund am Code:** `agent/hebelfuehrung.py` (Führung **echter** Positionen: Liquidationsabstand, Finanzierung, Stop, Empfehlung als Mail) wird **nur** in der alten Rollen-Kette aufgerufen (`rollen_lauf.py:981`).
- Diese Kette kehrt seit 05.10. vorher zurück (`scheduler/background.py:4478–4481`, `spot_kette_angehalten: true`, E-67; im 72-h-Protokoll 291-mal *Rollen-Kette ANGEHALTEN*).
- ⇒ **Seit 05.10. gibt es für echte Hebelpositionen keine Führung und keine Warnung.**
- Was weiter läuft:
  - der Abgleich mit Bitpanda (alle 15 min);
  - die Schätzung des Liquidationspreises (`_refresh_hebel_position_liquidation_prices`), nur als **Zahl** in der App;
  - die 24-h-Erinnerung der REGEL0, aber nur für Positionen **aus einem REGEL0-Signal**.
- BTC heute: Einstand 1.500 € / 0,02038541 = **73.582 €** je BTC, Liquidation geschätzt **53.907 €** (−26,7 %), kein Stop hinterlegt.
- Bei der Stilllegung am 05.10. wurde *wer liest/schreibt das noch* für die Hebelführung nicht erkannt. Das ist ein Verstoß gegen die Regel *Stilllegung: wer SCHREIBT das noch*.
- **H15 (Vorschlag zur Abstimmung):** Hebelführung von der alten Kette lösen, als eigener Job nach dem Abgleich.
  - (a) **Liquidationswächter:** Ereignis-Mail, sobald der Abstand zur Liquidation unter eine Grenze fällt. Ein Fakt zum Schutz der Position (RM-11), kein Einstiegssignal.
  - (b) Führungszeile je echter Position: Tage, Ergebnis, Finanzierung, Abstand.
  - (c) Plan aus dem REGEL0-Signal, wenn es eines gibt; sonst *eigene Position ohne Plan*.
  - Die Grenze für (a) wird als Fakt gesetzt und begründet, nicht optimiert.
  - Bau frühestens nach der Testwoche (10.10.), eine NB-Änderung zur Zeit. Reihenfolge zu O29 legt der Nutzer fest.

### 23.30 H15 gebaut — Hebelführung echter Positionen im Abgleich-Lauf (09.10.2026; E-88)

Nutzer 09.10.: *„Ja H15 zuerst, Warnung bei 15 % Abstand“* · *„wie immer prüfen, gegenprüfen und Doku“*.

**Voranalyse am Code:**
- `agent/hebelfuehrung.py` ist vollständig und rein (`lade`, `fuehre`, `neue_meldungen`, `vermerke`, `sammel_mail`), war aber **nur** in `rollen_lauf.py:981` verdrahtet.
- Einer Position **ohne Plan** (eigene Position) meldete es erst bei **erreichter** Liquidation, also zu spät.
- Der Kurs kommt aus `price_cache` (`positionsfuehrung.kurs_mit_stand`); der Stand des Kurses steht in der Mail.
- Die Positionen aktualisiert `sync_hebel_positions` im 15-Minuten-Lauf `hebel_screening_job`, danach `_refresh_hebel_position_liquidation_prices`.

**Gebaut (Entscheidungen, die fachlich zu treffen waren, offen ausgewiesen):**

| | |
|---|---|
| neue Empfehlung | **LIQUIDATION NAHE**: Abstand Kurs → geschätzte Liquidation unter der Schwelle, **auch ohne Plan**; Dringlichkeit direkt nach *LIQUIDATION ERREICHT* |
| Schwelle | `liquidations_warnung_abstand: 0.15` in `regel0_betrieb.yaml` (Nutzer), geprüft beim Laden (0 < x < 1) |
| Warnstufen | 15 / 10 / 5 % (Anteile der Schwelle). Jede **tiefere** Stufe meldet sofort, dieselbe Stufe höchstens **einmal am Tag** (Schlüssel `hebelfuehrung:<id>:<Empfehlung>:stufe<x>:<Tag>`) |
| wo | `scheduler.background._hebelfuehrung_lauf`, aufgerufen im Abgleich **nach** Abgleich und Liquidationspreisen und **vor** dem Halt der Rollen-Kette, also alle 15 min |
| wann gemailt | nur mit Schalter `hebelfuehrung_aktiv: true` und nur am **Betriebsgerät** (`regel0_nachlader.betrieb_erlaubt`), damit ein laufender Desktop nicht mailt; vermerkt nur bei **Zustellung** |
| Doppelmail | läuft die Rollen-Kette wieder, verhindert derselbe Schlüssel die zweite Mail (wer zuerst vermerkt, meldet) |
| Protokoll | je Lauf eine Zeile *„Hebelfuehrung: n offen · BTC <Empfehlung> Abstand x % · gemeldet m“* |
| Teilexport | Abschnitt *HEBELFUEHRUNG (H15) gemeldet* (Schlüssel aus `job_laeufe`, nur lesend) |

**Prüfung und Gegenprüfung:**
- `h15_pruefstand.py` **11/11**, am Pfad `_hebelfuehrung_lauf`, Wegwerf-DB, Ersatz-Versand:
  - kein Alarm über der Schwelle; Stufe 15 / 10 / 5 % je einmal;
  - dieselbe Stufe am selben Tag still; gescheiterter Versand → nicht vermerkt, beim nächsten Lauf gemeldet;
  - Liquidation erreicht; am nächsten Tag wieder meldepflichtig;
  - Schalter aus → kein Lauf; am Desktop übersprungen ohne Vermerk;
  - Mailtext mit Einstand, Liquidation, Abstand und *„Entscheidung liegt bei dir“*;
  - **Standard-DB unverändert** (Zeitstempel und Größe).
- `h15_gegenprobe.py` **6/6**, eigener Rechenweg:
  - Einstand 73.582,04 € = 1.500 / 0,02038541; Abstand = (Kurs − Liquidation) / Kurs;
  - Warnstufen in zweiter Umsetzung über 301 Werte, 0 Abweichungen;
  - Schlüssel je Stufe und Tag;
  - der alte Aufruf der Kette passt weiter und warnt mit der Vorgabe 15 %;
  - falsche Schalterwerte brechen ab;
  - der Exportabschnitt liest nur.
- Suite: Paket Regel0Betrieb **78/78** (2 neue Prüfungen H15: Prüfstand am Pfad; Aufruf vor dem Halt, Schalter, Schwelle), Register 15/15, Abbildung 10/10.

**Betrieb:**
- Wirksam mit dem nächsten Pull und Neustart am NB. Laut Nutzer **vor O29** und erst **nach** der Freigabe der Testwoche (10.10.), eine NB-Änderung zur Zeit.
- Danach gilt **Kontrolle K-H15-1** (Teilexport nach ~30 min):
  - im Protokoll je 15 min die Zeile *Hebelfuehrung: … BTC … Abstand …*;
  - keine Zeile *Hebelfuehrung: Lauf fehlgeschlagen*;
  - bei Abstand über 15 % keine Mail; der Exportabschnitt vorhanden.

### 23.31 NB-Prüfung 09.10.2026 nachmittags (Teilexport 14:15, Diagnose 14:36, Prod-Sicherung 12:35 UTC als Kopie)

**Testwoche** (`pruefe_testwoche.py` an der Kopie `regel0_signale.db` 12:15 UTC):
- T1–T3 und F1–F4 ✔.
  - 153/153 Laufstunden.
  - 17 Signale mit Schalter an, alle gemailt, im Median 10 min.
  - 0 Korrekturen; Ausstieg 1 verschickt / 4 entfallen.
- ⛔ **L1:** 2 gemailte Signale ohne Trader-Zeile, beide **bekannt**: BEAMX 07.10. (Sperre der Ablage, behoben) und BNB 08.10. 16:00 (Zeitgrenze, H14/O32 offen). Seit 08.10. **kein neuer Fall** (9 Signale am 09.10., alle mit Trader-Zeile).
- A1 im Rahmen (17 gegen 10,5 erwartet).
- ⇒ Die Freigabe ist **Nutzerentscheidung** (P5, ≥ 10.10.).

**K-BP-1 — Ursache gefunden:** *„Bestand passt nicht zusammen“* BTC und EURCV seit 06:45 UTC.

| | Spot-Wallet | Hebel-Wallet | Buchungen gesamt | `/portfolio` „meldet“ |
|---|---|---|---|---|
| BTC | 0,05496596 (shared-default) | 0,02038541 (margin-trading) | 0,07535137 | **0,02038541** = genau der Hebelteil |
| EURCV | +696,04291657 (shared-default) | −2.600 (margin-trading-credit = Hebel-Kredit BTC 1.000 + ETH 1.600) | −1.903,9571 | **−2.600** = genau der Kredit |
| ETH | 0,05685134 + Staking 0,48714122 | 0,89636371 (margin-trading) | — | Spot-Teil → Log *„ohne Hebel-Wallet gezählt“* ✔ |

- **Ursache:** `/portfolio` führt den Hebelteil als **eigene Zeile mit derselben Asset-ID**. `abgleich_neu` baut `positionen = {p.asset_id: p …}` und behält **nur die letzte Zeile**. Bei ETH war es zufällig die Spot-Zeile, bei BTC und EURCV die Hebel-Zeile.
- Die Werte stimmen auf 8 Nachkommastellen, eine Rohantwort von `/portfolio` liegt aber nicht vor ⇒ **Befund, am Code zu bestätigen**.
- **Wirkung:**
  - `holdings` BTC 0,05497 ist richtig: Es ist der letzte gute Stand, und der Spot hat sich nicht geändert.
  - EURCV steht veraltet bei 311,93 statt 696,04.
  - Die Warnmail wiederholt sich alle 6 h, solange ein Hebel offen ist.
  - Für den Betrieb unschädlich: kein Schreiben falscher Mengen.
- **K10** (*zählt `/portfolio` Hebel-Sicherheiten mit?*) ist damit beantwortet: **als eigene Zeile**.
- **Fix-Vorschlag (Desktop, Prüfstand, Nutzer-Ja, NB-Änderung erst nach H15):** Die Portfolio-Zeilen je Asset-ID **summieren**. Dann trifft die Summe die Buchungen gesamt (BTC 0,07535 / EURCV −1.903,96) und die bestehende E9-Prüfung *mit Hebel* greift. In `holdings` bleibt nur der Spot-Teil (Hebel-Wallets bleiben draußen, Modul-Kopf).

**Hebel offen (Kopie 12:30 UTC):**
- BTC 3x: Kurs 74.137 € · Liquidation geschätzt 53.954 € · **Abstand 27,2 %**.
- **ETH 5x:** Kurs 2.232,08 € · Liquidation geschätzt 1.962,26 € · **Abstand 12,1 %**.
  - Das liegt unter der H15-Schwelle 15 %. H15 hätte *LIQUIDATION NAHE* gemeldet; es ist am NB noch nicht aktiv (Push ausstehend).
  - Nutzer am 09.10. informiert.

**Bestand:** Seit 07:45 UTC sind ALGO, AVAX, NEAR, SOL, SUI und CT auf 0 (Verkäufe), CAT ist neu. Für die Spot-Abdeckung (§39.9) gilt damit eine kleinere Liste.

**KORREKTUR zu „Bestand: ALGO, AVAX … auf 0 (Verkäufe)“** (Nutzer 09.10.: *„diese sind gestaked und wie normale Spot-Positionen zu führen, Ausnahme ist nur ETH, dort dauert das Entstaken einige Tage“*):
- **Falsch gelesen.** Um 07:30 UTC wurde der freie Teil ins Staking umgebucht (Log *„Umbuchung frei/gestakt“*). `holdings.quantity` = frei = 0, `staked_quantity` = alles. Der Importer bucht **richtig**.
- Meine Quelle war die Zeile *BESTAND (Menge > 0)* des Teilexports (`nb_teilexport_betriebsdaten.py:234`). Sie zählt nur `quantity` und **verschweigt vollständig gestakte Werte**.
- **Ganzer Bestand (Kopie 12:35 UTC):**
  - **10 nur gestakt:** ALGO, AVAX, BNB, HYPE, NEAR, SEI, SOL, SUI, TAO, VSN.
  - ETH frei 0,0569 + gestakt 0,4871 (+ Hebel 0,8964).
  - Alle übrigen nur frei.
  - Dieselbe Lage war am 11.09. schon bekannt (P-3, `portfolio_historie` Portfoliowert zählt das Gestakte seither mit).
- **Leser, die heute noch nur `quantity` nehmen:**
  - Teilexport-Zeile 234;
  - `portfolio_historie` Rekonstruktion (Z. 467/483) und Hedge (Z. 1315, dort unkritisch);
  - `absicherung_fakten`, `krypto/analyst`, `krypto/risk_gate` (Rollen-Kette, seit 05.10. angehalten).
  - ⇒ Für den **Spot-Neubau** gilt: Bestand = **frei + gestakt**.
- **Folge für §39.9 (Abdeckung):** Die Bestandsliste stammte aus derselben Zeile. Es fehlten **BNB, HYPE, SEI, TAO, VSN** (CT ist inzwischen verkauft, CAT neu) → Abdeckung neu rechnen.
- **ETH:** Entstaken dauert Tage. Eine Verkaufshandlung muss das nennen (ETH ist Kern, betrifft B1 nicht; wichtig für jede künftige ETH-Handlung).

**Trennung Spot / Hebel — was die Wallets hergeben (Kopie 12:35 UTC):**

| Bitpanda-Wallet | gehört zu | Ablage im System |
|---|---|---|
| `shared-default` (frei), `staking-service` (gestakt) | **SPOT** | `holdings` (frei + gestakt) |
| `margin-trading` (Hebel-Menge), `margin-trading-credit` (Hebel-Kredit, EURCV) | **HEBEL** | `hebel_positions`, **nie** `holdings` |

Die Hebel-Wallets treffen die offenen Hebelpositionen:
- BTC 0,02038541 ≈ 1.500 € beim Einstieg;
- ETH 0,89636371 × 2.220 ≈ 1.990 € (Position 2.000 €);
- Kredit −2.600 € = 1.000 + 1.600 genau.

### 23.32 K-BP-1 Rohantwort `/portfolio` und Fix-Entwurf Trennung Spot/Hebel (09.10.2026)

Nutzer 09.10.: *„wir brauchen für die Positionsführung von SPOT und HEBEL eine klare Trennung, den Vorschlag von dir kann ich nicht bewerten“* · *„3. ja vorbereiten“*.

**Werkzeug:** `nb_bitpanda_portfolio_roh.py`.
- Ein einziger GET, ohne Projekt-Import: `api.bitpanda_public._hole` trägt `@track_api_health` und **schreibt** in die Produktions-DB.
- Keine DB, keine Mail, der Schlüssel nur aus `.env`.
- Am **Desktop** ausgeführt (dasselbe Bitpanda-Konto) → `nb_bitpanda_portfolio_roh_9900K.txt`. Ein NB-Lauf ist nicht nötig.
- ⚠️ Vor dem Lauf gefunden: Die EUR-Kennung war falsch eingesetzt und ist auf `api/bitpanda_public.EUR_WAEHRUNG_ID` korrigiert.

**Befund (09.10. ~16:00):** 52 Zeilen für 49 Assets. **BTC, ETH und EURCV je zwei Zeilen**, alle übrigen eine.

| | Zeile 1 | Zeile 2 |
|---|---|---|
| BTC | Spot 0,05496596 (verfügbar 0,05496596) | **Hebel 0,02038541** (verfügbar 0) |
| ETH | **Hebel 0,89636371** (verfügbar 0) | Spot 0,54399256 = frei 0,0569 + gestakt 0,4871 (verfügbar 0,0569) |
| EURCV | Spot 296,04 | **Kredit −2.600** |

- **Kein Feld kennzeichnet die Zeile** (Felder: asset_id, balance, available_balance, currency_balance, average_buy_price, invested_amount, total_return …).
- **Die Reihenfolge wechselt**: Bei BTC steht Spot zuerst, bei ETH der Hebel. Das erklärt, warum ETH glatt lief.
- *„verfügbar = 0“* kennzeichnet den Hebel **nicht**: Ein vollständig gestakter Spot-Wert (SOL, SUI …) hat ebenfalls verfügbar 0.
- EURCV Spot liegt inzwischen bei 296,04 (12:35 UTC: 696,04).

**Fix-Entwurf (zur Abstimmung, Bau am Desktop, NB nach H15):**
1. Je Asset werden die Wallets in zwei Gruppen summiert: **Spot = frei + gestakt**, **Hebel = margin-trading + margin-trading-credit**. Das macht `bestand_je_asset` schon.
2. Die `/portfolio`-Zeilen eines Assets werden **über die Menge zugeordnet**: Die Zeile, die Spot trifft, ist die Spot-Zeile; die Zeile, die Hebel trifft, ist die Hebel-Zeile. Das ist unabhängig von der Reihenfolge, ohne Raten.
3. **Spot-Kontrolle:** Die Spot-Zeile muss die Spot-Summe treffen → `holdings` (frei, gestakt). Trifft keine Zeile → Warnmail wie heute.
4. **Hebel-Kontrolle (neu, Hebel-Strang):** Die Hebel-Zeile muss die Hebel-Wallets treffen. Die Hebel-Menge × Einstand gehört zu einer offenen `hebel_positions`-Zeile; der Kredit gehört zur Summe `kreditbetrag_eur` der offenen Positionen. Eine Abweichung bedeutet: Position, die das System nicht kennt → Mail.
5. Der Hebel-Teil kommt **nie** in `holdings`, wie bisher.

### 23.33 H15-Korrektur vor dem Push (09.10.2026)

Nutzer 09.10.: *„ja H15 pushen, wenn alles geprüft und gegengeprüft wurde“*.

- ⛔ **Die ganze Suite fand 5 rote Prüfungen im Paket Hebelführung**, alle durch H15. Vor dem Commit c043475 lief nur das Paket Regel0Betrieb (Regel *Suite lesen, bevor committet wird* nicht eingehalten).
- **Ursache, ein echter Fehler:** `fuehre()` kehrte bei *LIQUIDATION NAHE* früh zurück (`if empfehlung in (LIQUIDIERT, LIQ_NAHE, KURS_FEHLT): return`). Damit **verdrängte die Warnung die konkreten Handlungen aus dem Plan**: *SCHLIESSEN* (Widerlegung erreicht) und *HEBEL SENKEN* (Liquidation vor dem Stop, mit Nachschussbetrag).
- **Korrektur (E-91: zuerst die Handlung):**
  - Rangfolge `DRINGLICHKEIT` = LIQUIDATION ERREICHT > SCHLIESSEN > HEBEL SENKEN > **LIQUIDATION NAHE** > KURS FEHLT > STOP NACHZIEHEN > HALTEN.
  - Der Plan wird auch bei Nähe gerechnet. SCHLIESSEN und HEBEL SENKEN gehen vor; die Warnstufe bleibt in `nahe_stufe` und als Grund in der Mail.
  - HALTEN und STOP NACHZIEHEN verdrängen die Warnung **nicht**.
  - Der Schlüssel trägt die Stufe jetzt bei **jeder** Empfehlung mit Warnstufe: Eine tiefere Stufe ist auch unter HEBEL SENKEN eine neue Meldung.
- **Prüfungen:**
  - Die drei Plan-Prüfungen auf Tag 0,2 rechnen ausdrücklich mit Schwelle 10 % (ihr Fall liegt bei 12,9 %; geprüft wird die Plan-Logik, nicht H15).
  - **Neu:** derselbe Fall mit 15 % → LIQUIDATION NAHE; HEBEL SENKEN vor der Warnung (Stufe bleibt); SCHLIESSEN vor der Warnung (Stufe 10 %, eigener Schlüssel).
- **Nachweis:**
  - Paket Hebelführung 35/35 · Prüfstand 11/11.
  - Gegenprobe **7/7**, neu G7: Rangfolge über 3.636 Fälle (Hebel 5/3/2x, drei Haltedauern, mit/ohne Widerlegung, mit/ohne Nachzug, Kurs 80–130), **alle sechs Empfehlungen erreicht, 0 Abweichungen**.
  - **Ganze Suite 3.225 Prüfungen, nur die 5 bekannten roten** (Datenstand am Desktop: Sperrsymbole, Messreihe je Bestand, Messbasis-Alter, Kernwert ohne Beitrag, Helfer-Symbole).
- **Erwartung nach Pull und Neustart am NB:** ETH 5x liegt bei rund 12 % Abstand → **sofort eine Mail *LIQUIDATION NAHE* (Stufe 15 %)**, danach je Tag und Stufe höchstens eine; BTC 3x (≈ 27 %) ohne Mail. K-H15-1 wie §23.30.

### 23.34 K-H15-1 nach Pull und Neustart (09.10.2026, Teilexport 17:51, Prod-Sicherung 16:00 UTC als Kopie)

| Kontrolle | Befund | |
|---|---|---|
| Mail *LIQUIDATION NAHE* ETH | vom Nutzer bestätigt; im Export `hebelfuehrung:2220:LIQUIDATION NAHE:stufe0.15:2026-10-09 · 15:14 UTC` — **genau einmal** | ✔ |
| BTC 3x ohne Mail | kein Eintrag (Abstand 27,1 %) | ✔ |
| Lauf alle 15 min | `job_laeufe` hebel_screening 15:59 UTC; nach 15:14 keine Wiederholung (Sperre je Tag und Stufe greift) | ✔ |
| Exportabschnitt *HEBELFUEHRUNG (H15) gemeldet* | vorhanden. Er zeigt auch alte Schlüssel der Rollen-Kette (Position 1387, *SCHLIESSEN* täglich 25.09.–01.10.) | ✔ |
| REGEL0 nach dem Neustart | Läufe 13:00/14:00/15:00 UTC, frisch 634/634, 15:00 mit 236 s | ✔ |
| Protokollzeile *„Hebelfuehrung: n offen …“* / kein *„Lauf fehlgeschlagen“* | steht im Log, nicht im Teilexport | ◐ mit dem nächsten Diagnose-Export nachweisen |

Stand 16:00 UTC: **ETH 5x Abstand 11,7 %** (Kurs 2.221,94 €, Liquidation 1.962,90 €) · BTC 3x 27,1 %. Die nächste Stufe (10 %) meldet H15 erneut.

### 23.35 K-BP-1 Importer-Fix gebaut — Trennung Spot/Hebel über die Menge (09.10.2026)

Nutzer 09.10.: *„Ja, Importer-Fix bauen, prüfen und gegenprüfen“*.

**Bau (`importer/bitpanda_bestand.py`):**
- `abgleich_neu` sammelt **alle** `/portfolio`-Zeilen je Asset. Vorher galt `{asset_id: Zeile}`, also gewann die letzte Zeile.
- Neue Funktion `spot_zeile(zeilen, b)` bestimmt die Spot-Zeile **über die Menge** der Wallets (Spot = frei + gestakt, Hebel = margin-trading + margin-trading-credit):

| Zeilen | passt, wenn | Spot-Zeile |
|---|---|---|
| keine | Wallets zusammen 0 | — |
| eine | ohne Hebel: trifft Spot · mit Hebel: **nur Hebel** bei Spot 0 (zuerst geprüft) / trifft Spot / trifft Spot + Hebel | die Zeile, bei *nur Hebel* keine |
| zwei | eine trifft Spot, die andere Hebel — Reihenfolge egal | die Spot-Zeile |
| mehr als zwei, unbekannte Wallet-Art | nie | — |

- In `holdings` kommen weiter **nur frei und gestakt** (E1). Die Meldung bei Nicht-Passen nennt jetzt Spot, Hebel, alle Zeilen und die Lesart.
- **Festlegung (fachlich):** Die Spot-Kontrolle prüft **Spot gegen Spot**. Fehlt die Hebel-Zeile, ist das eine Frage der Hebel-Kontrolle (Schritt B unten), nicht des Spot-Bestands.

**Prüfungen:**
- **Suite-Paket BitpandaBestand 18/18** (vorher 14). Die 4 neuen laufen mit den **echten Zahlen vom 09.10.**: kein Fehlalarm bei BTC/ETH/EURCV; EURCV 311,93 → 296,04, Kredit draußen; LINK mit unpassenden zwei Zeilen bleibt stehen und meldet; `spot_zeile` reihenfolgefrei, *nur Hebel*, > 2 Zeilen, unbekannte Wallet-Art.
- ⚠️ Gefunden **beim Bau**: Bei Spot 0 und nur der Hebel-Zeile griff zuerst *„mit Hebel-Wallet“*, die Hebel-Zeile wäre als Spot gelesen worden (bei einem Asset ohne Watchlist eine falsche Meldung *„Position ohne Watchlist“*). Behoben, *nur Hebel* wird zuerst geprüft.
- **Gegenprobe `kbp1_gegenprobe.py` 3/3:**
  - G1: die **echte Rohantwort** aus der Datei, alle drei passen, die Spot-Zeile trifft die Spot-Menge;
  - G2: zweite Umsetzung (alle Beschriftungen S/H/SH durchprobiert) gegen `spot_zeile` an **20.000 Zufallsfällen, 0 Abweichungen**. Die erste Fassung verlangte bei einer einzigen Spot-Zeile auch die Hebel-Zeile (968 Fälle), das ist die oben festgelegte Definitionsfrage;
  - G3: Der alte Fehler ist nachgestellt (*letzte Zeile gewinnt*: BTC und EURCV verworfen, ETH nicht), genau die Mails vom 09.10.

**Wirkung am NB (nach Pull):**
- Die Mails *„Bestand passt nicht zusammen“* für BTC und EURCV hören auf.
- EURCV wird auf den Spot-Teil fortgeschrieben.
- Im Log steht je Hebel-Asset *„Spot- und Hebel-Zeile getrennt (Spot x, Hebel y)“*.

**Schritt B (offen, eigene Abstimmung):** Hebel-Kontrolle — Hebel-Zeile/-Wallets gegen die offenen `hebel_positions` (Menge × Einstand ≈ Positionswert, Kredit = Summe `kreditbetrag_eur`). Sie würde nebenbei den bekannten Importerfehler bei Teilschließungen zeigen (Memory *IMPORTER teilt Hebelpositionen falsch ein*).

**Ganze Suite mit dem Fix:** 3.229 Prüfungen, rot die 5 bekannten **plus der H15-Prüfstand P10**.
- Ursache: P10 verlangte wörtlich *„13,0 %“*. Der Lauf nimmt aber die **echte Uhrzeit** gegen eine feste Eröffnung, und die Finanzierung schiebt die Liquidation stündlich näher. Nach einigen Stunden waren es 12,9 %.
- Ein Prüfstandsfehler, kein Betriebsfehler. Er hätte die Suite ab heute Abend dauerhaft rot gemacht.
- P10 rechnet jetzt den Abstand aus der Liquidation **derselben Mail** nach.
- Danach: Prüfstand 11/11 · Regel0Betrieb 78/78 · BitpandaBestand 18/18 · Hebelführung 35/35.
