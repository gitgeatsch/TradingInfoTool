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

