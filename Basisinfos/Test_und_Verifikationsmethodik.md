# Test- und Verifikationsmethodik

**Zweck:** Dauerhafter Standard, kein einmaliges Protokoll. Bisher wurden Tests und
Notebook-Export-Analysen bei jeder Änderung neu und unterschiedlich tief erfunden -
das macht Ergebnisse über die Zeit nicht vergleichbar und lässt leicht Unschärfe in
Status-Angaben wie "erledigt" entstehen (siehe Abschnitt 0, Auslöser dieses
Dokuments). Ziel: eine feste, wiederholbare Vorgehensweise für (A) synthetische
Tests hier am Gerät und (B) die Analyse echter Notebook-Exporte, inklusive
Lerneffekt über die Zeit.

Stand: 2026-07-28. Bei Bedarf ergänzen, nicht neu erfinden.

---

## 0. Status-Vokabular (Grundlage für alles Weitere)

Auslöser: eine Änderung wurde in der Fakten-Entscheidungsmappe als "ERLEDIGT"
bezeichnet, obwohl sie noch nicht committet war - Nutzer-Nachfrage machte deutlich,
dass "erledigt"/"umgesetzt" ohne feste Bedeutung missverständlich ist. Ab sofort
gilt für jede Änderung genau eine dieser fünf Stufen, immer explizit benannt:

1. **Geschrieben** - Code/Text existiert lokal, noch nicht geprüft.
2. **Verifiziert** - synthetische Tests bestanden (siehe Abschnitt 1). Sagt NUR
   etwas über interne Konsistenz aus, nichts über reale Wirkung.
3. **Committet/gepusht** - dauerhaft im Git-Verlauf, erreicht das Notebook nach
   einem Pull.
4. **Deployed** - Notebook hat gepullt und (falls nötig) neu gestartet, Code läuft
   tatsächlich.
5. **Im Betrieb bestätigt** - echte Signale sind gelaufen, das erwartete Verhalten
   wurde im Notebook-Export beobachtet (siehe Abschnitt 2).

Bei jeder Status-Angabe (in Chat, Regelwerksmanual, Memory) diese Stufe explizit
nennen, nicht nur "erledigt" schreiben. Stufe 5 ist bei reinen LLM-Kontext-Änderungen
(kein Gate, keine harte Regel) oft nicht sauber isolierbar - das ehrlich benennen,
statt sich eine Wirkung einzureden (siehe Abschnitt 2.2, "Vorher-Hypothese").

---

## 1. Synthetischer Test-Standard (isolierter Intensivtest, Desktop)

### 1.1 Änderungsklassen und Mindest-Testtiefe

| Klasse | Beispiel | Mindest-Standard |
|---|---|---|
| **1 — reiner Prompt-/Text-Fakt** | neue SYSTEM_PROMPT-Regel ohne neue Logik | Modul-Import + `py_compile`-Check + Regelnummerierung/Schema-Konsistenz-Check (keine Lücke/Duplikat in den durchnummerierten Regeln, JSON-Schema-Kommentare zeigen auf die richtige Regelnummer) |
| **2 — deterministische Logik** | neue Gate-Formel, neue Schwelle, neue Risikofaktor-Berechnung | Benannte Testfälle nach festem Muster (siehe 1.2), MINDESTENS: Regressionsfall (altes Verhalten unverändert), Positivfall (neue Logik greift korrekt), Grenzfall (Schwellenwert exakt getroffen, Nullwerte, `None`), Kombinationsfall (Zusammenspiel mit mindestens einem bestehenden Veto/Deckel) |
| **3 — DB-Schema** | neue Spalte/Tabelle, neue Migration | Zusätzlich zu Klasse 2: Migrations-Test (frische In-Memory-DB + Migration; zusätzlich eine "Alt-Zeile" ohne die neuen Spalten einfügen, Migration erneut laufen lassen - keine Exception, sinnvolle NULL-Defaults) |
| **4 — UI-Änderung** | neue Spalte/Dialog/Toggle | Zusätzlich zu Klasse 2 (falls Logik dahinter): Tk-Smoke-Test (Fenster öffnet ohne Exception, neues Element sichtbar, Interaktion löst erwartete Aktion aus) |

Faustregel: die Klasse richtet sich nach der RISKANTESTEN betroffenen Ebene, nicht
nach der Summe. Eine Aenderung, die sowohl einen Prompt-Text als auch eine DB-Spalte
betrifft, ist Klasse 3.

### 1.2 Format synthetischer Testfälle

Wie bereits in dieser und vorherigen Sitzungen praktiziert (fortführen, nicht neu
erfinden): In-Memory-SQLite (`sqlite3.connect(":memory:")`, `conn.row_factory =
sqlite3.Row`, `database.db.init_db(conn)`), direkte Dataclass-Konstruktion
(`Signal`/`HebelSignal` mit nur den fuer den Testfall relevanten Feldern), benannte
Fälle als T1, T2, T3... mit je einer Zeile Beschreibung, was geprüft wird und warum.
KEIN Zugriff auf die Produktions-DB (siehe
[[feedback_desktop_kein_produktivstart]] - gilt unveraendert).

### 1.3 Protokoll-Format (neu, ab jetzt verbindlich)

Jeder Testlauf für Klasse 2-4 bekommt ein kurzes, einheitliches Ergebnis-Protokoll,
das in die jeweilige Commit-Beschreibung bzw. den Regelwerksmanual-Nachtrag
übernommen wird:

```
Verifikation [Datum]:
  Betroffene Datei(en): ...
  Änderungsklasse: 1/2/3/4
  Testfälle: T1 <Kurzbeschreibung> - PASS/FAIL
             T2 ... - PASS/FAIL
             ...
  Regressionscheck (Imports aller betroffenen Module): PASS/FAIL
  Gesamturteil: verifiziert (Stufe 2) / nicht bestanden (Ursache: ...)
```

Für Klasse 1 genügt eine Kurzfassung ("Modul-Import OK, Regelnummerierung 1-N ohne
Lücke, Compile-Check OK").

### 1.4 Lücke gefunden und geschlossen (2026-07-31): `py_compile`/`ast.parse` reicht NICHT für Funktionsumbenennungen

**Auslöser:** nach dem Selbst-Halten-Schatten-Feature (siehe Regelwerksmanual-
Nachtrag) lief `extract_notebook_diagnose.py` am Notebook mit `NameError:
name '_richtung_aus_veto_zonen' is not defined`. Die Funktion war im selben
Commit zu `_richtung_aus_zonen()` umbenannt worden - `python -m py_compile`
UND ein reiner `ast.parse()`-Check waren beide grün, weil beide nur Syntax
prüfen, nicht ob ein referenzierter Name zur Laufzeit existiert. Der
verbliebene Aufruf lag in `compute_zai_richtung_performance_schatten()` -
einer bereits BESTEHENDEN Funktion (28.07.), die beim Umbenennen nicht als
Aufrufer erkannt wurde, weil sie nicht Teil des aktuell bearbeiteten
Funktions-Sets war.

**Lehre 1 - bei jeder Funktions-/Symbol-Umbenennung:** `grep -rn "<alter_name>"`
über das GESAMTE Repository (nicht nur die Datei, die gerade bearbeitet wird)
VOR dem Abschluss der Änderung, nicht danach. Ein "einziger Aufrufer" ist eine
Annahme, keine verifizierte Tatsache, bis der Grep sie bestätigt hat.

**Lehre 2 - `py_compile`/`ast.parse` deckt nur Syntaxfehler ab, keine
Laufzeit-Namensauflösung.** Ein `NameError` in einer Funktion, die im
Testlauf nie AUFGERUFEN wird, bleibt für beide Checks unsichtbar. Für
Skripte mit einem klaren Einstiegspunkt (`extract_notebook_diagnose.py::
main()`, ähnliche Batch-/Export-Skripte) gehört ab jetzt zur Klasse-2/3-
Mindesttiefe zusätzlich ein **End-to-End-Smoke-Test des Einstiegspunkts**
gegen eine frische temp-SQLite-Datei (DB_PATH umgebogen, NIE Produktiv-DB,
siehe [[feedback_desktop_kein_produktivstart]]) - nicht nur ein Test der
einzelnen neu geschriebenen Funktionen. Der reine `import`-Test allein reicht
ebenfalls nicht (Python löst Namen erst bei Funktionsaufruf auf, nicht beim
Modul-Import).

---

## 2. Notebook-Export-Analyse-Standard (Realitätscheck + Lerneffekt)

### 2.1 Fester Kennzahlen-Katalog (bei JEDEM neuen Export durchgehen, nicht nur die gerade interessierende Frage)

1. LLM-Budget/Calls heute je Provider (`llm_calls_heute`)
2. Signal-Volumen je Pipeline (`signal_volumen_heute`)
3. Provider-Performance (Win-Rate/Ø realisiertes CRV) je Assetklasse
   (`provider_performance`)
4. Konfidenz-Kalibrierung je Band (`konfidenz_kalibrierung`)
5. Z.ai-Richtungs-/Konsistenz-Abgleich (`zai_gegenpruefung_verlauf`,
   `zai_richtung_performance`)
6. Gate-Veto-Häufigkeit - insbesondere NEUE oder sich häufende Muster
   (`gate_veto_haeufigkeit`)
7. App-Neustart-Häufigkeit / Log-Auffälligkeiten (`log_auszug` auf
   "Added job"/"Traceback"/"CRITICAL" durchsuchen)
8. Wartezeit bis Auflösung je Outcome-Status (Median/Mittelwert, getrennt nach
   gleichem Kalendertag wie Erstellung vs. späterem Tag - siehe
   [[project_zai_gegenpruefungslogik]] für die Methodik, warum diese Trennung
   nötig ist)
9. Stop-Loss-MFE-Analyse (`compute_sl_mfe_analyse()`) - Quote der SL-Fälle mit
   zwischenzeitlich positivem MFE trotz spätem Stop (siehe Abschnitt 2.6)
10. Fazit-Selbsteinschätzung-Verteilung (`fazit_folgen`: ja/nein/mit_vorbehalt)
    je Assetklasse UND Aktionstyp (echter Trade vs. HALTEN) - insbesondere ob
    "ja"/"nein" inzwischen auch bei echten Trade-Empfehlungen (ERÖFFNEN/KAUFEN)
    auftreten, nicht nur bei HALTEN, und ob `selbst_halten_outcome_status`
    inzwischen erste aufgelöste Fälle zeigt (siehe Abschnitt 2.9).

Diese zehn Punkte werden IMMER kurz durchgegangen, auch wenn der Anlass für den
Export etwas anderes war - Auffälligkeiten ausserhalb der eigentlichen Fragestellung
nicht ignorieren (siehe z.B. den ISOC/X136-Ticker-Fund, der nebenbei beim
Durchgehen von Punkt 6 auffiel).

### 2.1a Export-Vollständigkeits-Check vor jeder NEUEN Fragestellung (verbindlich)

Auslöser: wiederholt aufgetreten (29.07. Konfidenz-CRV/SL-Korrelation, 30.07.
Z.ai-6-Pipelines-Assetklassen-Zuordnung, 30.07. ATR-Perzentil-Veraltungs-Check)
- bevor eine Frage beantwortet wird, die NICHT bereits vom festen
Kennzahlen-Katalog (2.1) abgedeckt ist, aktiv prüfen, ob
`extract_notebook_diagnose.py` die dafür nötigen Rohdaten überhaupt exportiert
- nicht stillschweigend mit vorhandenen, aber eigentlich unpassenden Daten
behelfen oder die Frage unbeantwortet lassen.

**Vorgehen:**
1. Export-Top-Level-Keys durchsehen (`data.keys()`) - existiert bereits eine
   passende Sektion?
2. Falls eine verwandte, aber zu enge Sektion existiert (z.B. eine Preishistorie
   nur für eine Teilmenge Symbole): pruefen, ob sie fuer die konkrete Frage
   ausreicht, oder ob sie strukturell den falschen Ausschnitt liefert.
3. Falls nötig: eine neue, MINIMALE Export-Funktion nach dem etablierten Muster
   ergänzen (eigene `_xxx(conn) -> dict`-Funktion, reine Lesefunktion/Aggregation,
   in `main()` eingehängt) - keine Sonderlösung nur für diese eine Frage, sondern
   eine wiederverwendbare Sektion (siehe z.B. `_preishistorie_ueberholte_symbole()`,
   `_deribit_cross_check_verlauf()` als Referenzmuster).
4. Skript-Änderung dem Nutzer explizit zur Bestätigung vorlegen (siehe
   `Basisinfos/Fakten_Entscheidungsmappe.md`-Konvention: Code-Änderungen brauchen
   Bestätigung), dann am Notebook laufen lassen + zurücksynchronisieren lassen,
   bevor die eigentliche Analyse fortgesetzt wird.

Bewusst NICHT: aus fehlenden Daten eine Vermutung machen und diese als Befund
ausgeben - fehlende Exportabdeckung ist ein Blocker für die Fragestellung, kein
Grund für eine ungeprüfte Annahme.

### 2.2 Vorher-Hypothese (Lerneffekt-Kern)

Bei jeder Änderung, deren Wirkung im Betrieb beobachtet werden soll: VOR dem
nächsten Export kurz notieren (in der jeweiligen Memory-Datei oder im
Regelwerksmanual-Nachtrag), WAS konkret erwartet wird. Beim nächsten Export dann
ehrlich prüfen, ob das eingetreten ist - nicht die Beobachtung nachträglich passend
interpretieren.

**Wichtige Einschränkung:** bei reinen LLM-Kontext-Ergänzungen ohne Gate (z.B. die
FOMC-Regel) ist ein hartes Vorher/Nachher-Signal oft NICHT sauber isolierbar - das
LLM-Verhalten ist nicht deterministisch reproduzierbar, und ein einzelner
beobachteter Fall beweist nichts. In diesem Fall ehrlich vermerken: "keine
belastbare Erfolgsmessung möglich, nur qualitative Beobachtung" statt eine
Scheingenauigkeit vorzutäuschen. Ein hartes Vorher/Nachher-Signal ist nur bei
Klasse-2/3-Änderungen (deterministische Logik) realistisch erwartbar.

### 2.2a Mehrtägige Beobachtung vor Vollabschluss neuer Bausteine/Features (Nachtrag 30.07.)

Auslöser: sowohl beim Konfidenz-Prompt-Fix als auch bei den Krypto-
Relativwert-Bausteinen (Signal-Stabilität/ATR-Perzentil/BTC-Relativwert,
siehe [[project_krypto_relativwert_bausteine]]) wurde ein neues Feature
NICHT direkt nach der synthetischen Verifikation als abgeschlossen
markiert, sondern bewusst offengehalten, bis mehrere Tage echter
Produktionsdaten vorlagen - bisher nur informell in einzelnen
Projekt-Memories festgehalten, nicht als Standard benannt.

**Ab sofort als Standard-Praxis, wenn ein neuer Fakt/eine neue Kennzahl
das LLM-Verhalten beeinflussen oder eine Entscheidungsgrundlage liefern
soll (nicht bei reinen UI-/Kosmetik-Änderungen):**

1. Nach Stufe 3 (Committet/gepusht) und Stufe 4 (Deployed) NICHT sofort
   Stufe 5 ("Im Betrieb bestätigt") behaupten, auch wenn ein erster
   Export unauffällig aussieht - ein einzelner Tag kann Zufallsrauschen
   nicht von echtem Verhalten unterscheiden.
2. Mindestens 3-5 reale Produktionstage abwarten (kein festes Datum,
   abhängig von Signalfrequenz - bei seltenen Pipelines ggf. länger).
3. Dann eine gezielte Plausibilitätsprüfung der realen Werte durchführen
   (siehe 2.7 für den Fall scheinbar eingefrorener Kennzahlen) - erst
   danach gilt das Feature als vollständig abgeschlossen (Stufe 5).
4. Der Nutzer-Grundsatz "nicht nur beobachten, sondern aktiv gegenprüfen"
   gilt auch hier - reines Abwarten ohne späteren Plausibilitätscheck
   reicht nicht.

### 2.3 Lern-Log

Kurze, stichwortartige Zusammenfassung nach jeder tieferen Export-Analyse: "was
haben wir bei diesem Export gelernt, das wir beim letzten nicht wussten" - als
Memory-Eintrag (Typ `project`), nicht nur im Chat-Verlauf, damit es durchsuchbar
bleibt und nicht verloren geht. Format wie bereits etabliert (siehe z.B.
[[project_notebook_quickcheck_2026-07-27]]).

### 2.4 Kein fester Rhythmus, aber feste Tiefe

Der Nutzer holt Notebook-Exporte unregelmäßig, je nach Bedarf - das bleibt so, kein
Vorschlag für einen festen Zeitplan. Aber unabhängig vom Anlass gilt: einmal
angefangen, wird der volle Katalog aus 2.1 durchgegangen, nicht nur die ursprünglich
gestellte Frage.

### 2.5 Symbol-/Konzentrations-Check vor jeder Muster-Interpretation (verbindlich)

Auslöser: die R-5.10-Analyse (29.07., siehe
[[project_r510_konfidenz_veto_analyse_29_07]]) zeigte eine naiv alarmierende Zahl
(n=80, 55% Win-Rate, +0,64 CRV bei konfidenz-vetoten Spot-Signalen), die sich bei
genauerem Hinsehen als Artefakt einer Handvoll gut laufender Symbole entpuppte (5
Symbole = 29/29 Treffer, ohne sie nur noch 29,4% WR bei den restlichen 51). Eine
zweite, strukturell ähnliche Prüfung am selben Tag (Hebel-Konfidenz-Bänder) ergab
dagegen ein robustes Ergebnis - der Unterschied wurde erst durch diesen Check
sichtbar.

**Ab sofort verbindlich, bevor eine Win-Rate/CRV-Kennzahl aus Veto-Schatten-,
Provider-Performance- oder Konfidenz-Band-Daten als "Muster"/"Erkenntnis"
interpretiert oder gar in eine Handlungsempfehlung übersetzt wird:**

1. Anzahl unterschiedlicher Symbole in der Stichprobe ermitteln (nicht nur Gesamt-n).
2. Win-Rate/CRV zusätzlich OHNE die 3-5 häufigsten Symbole berechnen.
3. Bewegt sich die Kennzahl dabei deutlich (>10 Prozentpunkte WR oder Vorzeichenwechsel
   beim CRV), gilt der Befund als NICHT robust - vermutlich Symbol-/Rally-Artefakt,
   nicht als Kalibrierungslücke behandeln, keine Schwellenwert-Änderung darauf stützen.
4. Bleibt die Kennzahl stabil, gilt der Befund als robust und kann als echte
   Erkenntnis dokumentiert und diskutiert werden.

**Nachgeschärfte Mindestschwelle (Nachtrag 29.07., externe Recherche zu
Backtest-Overfitting - Bailey/Lopez de Prado, "The Probability of Backtest
Overfitting"; Harvey/Liu/Zhu zu Multiple-Testing bei Handelsstrategien):**
ein aus einem Backtest abgeleitetes Muster wird NIE operationalisiert (kein
Gate, kein Deckel, keine Schwellenwert-Änderung), solange (a) n < 50 ODER
(b) ein einzelnes Symbol > 20-25% der Fälle stellt. Bei geclusterten
Beobachtungen (mehrere Signale desselben Symbols aus derselben
Marktbewegung) ist die EFFEKTIVE Stichprobengröße die Anzahl distinkter
Symbole, nicht die Roh-Zeilenzahl - analog zu "clustered standard errors"
in der Ökonometrie. Jede Analyse-Zusammenfassung weist deshalb IMMER beide
Zahlen aus: Roh-n UND Anzahl distinkter Symbole.

Zusätzlich: informell nacheinander getestete Hypothesen (z.B. "Deckel bauen"
→ "Gegenteil scheint zu gelten" → "Kontrolle zeigt Artefakt") sind ein
Multiple-Testing-Szenario - ein gefundener Effekt gilt bei jeder
Zwischenstufe zunächst nur als hypothesengenerierend, nicht als bestätigt,
bis er nach unabhängiger Replikation (neuer Zeitraum/neue Symbole) noch
Bestand hat.

Diese Prüfung wird in Abschnitt 3 der jeweiligen Analyse-Zusammenfassung (Chat oder
Memory) kurz mit ausgewiesen (Roh-n, Anzahl Symbole, WR mit/ohne Top-N), nicht nur das
Endergebnis genannt.

### 2.5.1 Klarstellung: was der Check NICHT bedeutet (Nachtrag 29.07.)

Auslöser: Nutzer-Nachfrage, ob eine bewusst schmale Watchlist (z.B. nur BTC/ETH/SOL)
das System damit faktisch unbenutzbar macht, und ob die Handelslogik überhaupt von
Diversifikation abhängen sollte (Gegenbeispiel des Nutzers: bei Hebel laufen aktuell
sowohl BTC als auch ein Memecoin - an fehlender Asset-Vielfalt kann und sollte es
also nicht liegen).

**Der eigentliche Maßstab ist Unabhängigkeit der Beobachtungen, nicht Anzahl der
Symbole.** Symbol-Vielfalt ist nur der aktuell nächstliegende PROXY dafür, weil die
bisherigen Datenmengen ihre scheinbare Größe oft aus wiederholtem
Cooldown-Re-Signalisieren DESSELBEN Coins während EINER zusammenhängenden
Marktbewegung beziehen (viele DB-Zeilen, aber wenige echte, unabhängige
Marktereignisse dahinter). Daraus folgt:

- **Eine schmale, bewusst gewählte Watchlist (wenige Symbole) ist für sich genommen
  KEIN Konzentrationsproblem.** Dieselben 2-3 Symbole über einen langen Zeitraum
  hinweg, der mehrere echte, unterschiedliche Marktphasen (Bulle/Bär/Seitwärts)
  abdeckt, liefern genauso unabhängige Datenpunkte wie viele verschiedene Symbole -
  nur über die Zeit-Achse gestreut statt über die Symbol-Achse. Das Betriebs-System
  selbst braucht keine Symbol-Vielfalt, um zu funktionieren.
- **Die Handelslogik/Regeln sollen asset-agnostisch funktionieren** (BTC und ein
  Memecoin gleichermaßen abgedeckt) - der Check unterstellt nicht das Gegenteil. Er
  prüft nur, ob eine KONKRETE Kennzahl (z.B. "46% Win-Rate bei Regel X") tatsächlich
  die generelle Wirkung der Regel zeigt, oder ob sie nur "diese 3 Symbole liefen in
  dieser einen Woche gut" beweist - was bei einer Schwellenwert-Änderung fälschlich
  auf ALLE künftigen Symbole/Situationen verallgemeinert würde.
- **Bei einer schmalen Watchlist ist der Symbol-Check durch einen
  Zeitfenster-Unabhängigkeits-Check zu ERSETZEN bzw. zu ergänzen:** sind die
  Gewinn-/Verlust-Fälle über mehrere klar unterschiedliche Marktphasen verteilt, oder
  stammen sie praktisch alle aus einer einzigen zusammenhängenden Bewegung? Gleiches
  Prinzip, andere Achse.
- Die ">10 Prozentpunkte"-Schwelle aus 2.5 ist bereits genau dafür gebaut, "ab
  welcher Menge kein Problem mehr" zu beantworten: nicht als feste Symbolanzahl,
  sondern als Test, ob der Effekt beim Entfernen der dominantesten paar Symbole
  verschwindet oder stabil bleibt.

### 2.5.2 Zweites Fallbeispiel: R-5.10-Konfidenzschwelle (Nachtrag 30.07.)

Auslöser: eine Live-Test-Untersuchung zu moeglichem LLM-Inaktivitaets-Bias
(Aktien/Rohstoffe/Themen-ETF, siehe Memory
[[project_llm_optimierung_abdeckung_pruefung]]) fuehrte zur echten Ursache
des Symptoms: dem R-5.10-Konfidenzschwellen-Veto in `risk_gate.py::
post_check()`. Eine erste Veto-Schatten-Auswertung fuer Krypto-Spot
(n=106 aufgeloest, Win-Rate 41,5%, Ø realisiertes CRV +0,222) sah auf den
ersten Blick belastbar aus (n>=50 erfuellt) und fuehrte zu einer
config.yaml-Aenderung (Konfidenzschwelle -5 Prozentpunkte je Regime,
NUR Krypto-Spot).

**Der in 2.5 vorgeschriebene Symbol-Konzentrations-Check wurde bei dieser
ersten Auswertung uebersprungen** - erst beim nachtraeglichen Dokumentieren
angewendet. Ergebnis: Top-5-Symbole (AKT, CAT, GRIFFAIN, KAITO, S) stellen
39,6% der Faelle; ohne sie faellt die Win-Rate auf 32,8% und das Ø
realisierte CRV **kippt im Vorzeichen** von +0,222 auf -0,242 - exakt die
in 2.5 als disqualifizierend definierte Bedingung. Die config.yaml-Aenderung
wurde noch am selben Tag zurueckgenommen.

**Lehre:** der Check muss VOR jeder Operationalisierung angewendet werden,
nicht erst beim Dokumentieren danach - sonst wird eine bereits live gesetzte
Aenderung auf nicht belastbarer Evidenz entdeckt, statt gar nicht erst
gesetzt zu werden. Zweiter unabhaengiger Beleg (nach dem 29.07.-Fall in
2.5), dass genau dieses Muster - Konfidenzschwellen-Vetos, Krypto-Spot,
scheinbar okay-grosses n - anfaellig fuer Symbol-/Rally-Artefakte ist.

Zusaetzlich bei derselben Gelegenheit festgestellt: die parallele
CRV<2,0-Veto-Teilauswertung (Krypto-Spot, n=18, urspruenglich als
"Veto arbeitet korrekt" eingeordnet) unterschreitet die n>=50-Mindestschwelle
unabhaengig von der Konzentration (hier gut verteilt) - beide
Krypto-Spot-Fragen bleiben damit offen, keine der beiden gilt als bestaetigt.

### 2.5.3 Drittes Fallbeispiel: Marktscan-Score-Schwellen-Kalibrierung - Konzentration als Signal statt nur als Störfaktor (Nachtrag 30.07.)

Auslöser: die Frage, ob `score_kaufkandidat_ab=70`/`score_watchlist_wuerdig_ab=50`
(beide VORLAEUFIG) gut kalibriert sind. Ein Backtest gegen echte Notebook-Daten
scheiterte am Symbol-Konzentrations-Check (2.5) - wenige Coins wurden immer
wieder als Kandidat entdeckt, eine klassische Schwellen-Kalibrierung wäre auf
dieser Basis nicht belastbar gewesen.

**Der entscheidende Perspektivwechsel:** statt die Konzentration nur als
Störfaktor zu behandeln (der eine Frage unbeantwortbar macht), wurde sie
selbst zur Fragestellung - "warum wird derselbe Coin so oft wiederentdeckt,
und sagt DAS etwas über die künftige Performance aus?" Ein eigens dafür
konstruierter Backtest (Streak-Position vs. Forward-Return, siehe Memory
[[project_krypto_relativwert_bausteine]] und Regelwerksmanual-Nachtrag
"Marktscan-Reifegrad-Scoring") bestätigte sauber (n=70 Coins mit ≥4
Tages-Sichtungen, OHNE Konzentrationsproblem in diesem spezifischen Test):
Win-Rate fällt monoton von 57% (3. Sichtung) auf 36% (5. Sichtung).

**Lehre:** wenn der Symbol-Konzentrations-Check eine urspüngliche
Fragestellung disqualifiziert, lohnt sich die Nachfrage, ob die Konzentration
selbst (die Wiederholung) ein eigenständiges, bisher ungenutztes Signal ist -
statt die Frage nur als "nicht beantwortbar" zu verwerfen. Bei der später
gebauten Erfolgsmessung (Marktscan Teil 2) drehte sich diese Konzentration
sogar zu einem PRAKTISCHEN Vorteil um: wenige distinkte Coins bedeuten
günstigere gebündelte `get_simple_prices()`-Abrufe (ein API-Call für mehrere
offene Messungen desselben Coins) statt vieler Einzelabrufe.

### 2.6 Mehrebenen-Erfolgsmessung: striktes Outcome vs. MFE/Mindestziel (Nachtrag 30.07.)

Auslöser: Nutzer-Frage, ob und wie Erfolgsquoten auf mehreren Ebenen geprüft
werden - neben dem strikten `outcome_status` (TP/SL/Liquidation/abgelaufen)
tracken wir bereits zwei weichere Zwischenebenen (`outcome_max_realisiertes_
crv`/MFE, `outcome_mindestziel_erreicht_am`), die bisher nie systematisch
gegen den strikten Outcome verschnitten wurden.

**Kernidee:** eine reine Win/Loss-Quote vermischt zwei grundverschiedene
Fehlerbilder - "Richtung war komplett falsch" und "Richtung war
zwischenzeitlich richtig, aber zu eng gestoppt/schlechte Positionsführung".
Diese zwei Fälle brauchen unterschiedliche Fixes (Prompt-/Fakten-Korrektur
vs. Stop-Platzierung) und sollten nie in einer einzigen Kennzahl verschwinden.

**Konkrete Prüfung (`compute_sl_mfe_analyse()`, `agent/krypto/
backward_tracking.py`):** von allen Signalen mit `outcome_status ==
stop_loss_erreicht`, welcher Anteil zeigt trotzdem einen positiven MFE-Wert
(der Kurs lief zwischenzeitlich profitabel, bevor er zurückdrehte)? Ein
erster Blick auf echte Daten (30.07., Hebel, n=23 mit MFE-Daten von 57
SL-Fällen) zeigte 87% mit positivem MFE, 9 davon erreichten sogar das
Mindestziel vor dem Stop - bestätigt aus einem neuen Blickwinkel den
bereits behobenen Enge-Stop-Loss-Befund vom 28.07. (siehe
[[project_enge_stop_loss_backtest_und_massnahmen]]), OHNE dass neue Daten
gesammelt werden mussten - reine Verschneidung bereits vorhandener Felder.

**Wichtig, gleiche Einschränkung wie überall in diesem Dokument:** diese
weichere Ebene hat NICHT automatisch mehr Fälle als die strikte (im
konkreten Fall eher weniger: 22-36 vs. 71 Hebel-Signale insgesamt) - der
Wert liegt nicht in der Stichprobengröße, sondern in der zusätzlichen
Trennschärfe. Symbol-Konzentrations-Check (2.5) gilt hier genauso -
`compute_sl_mfe_analyse()` weist `anzahl_distinkte_symbole_bei_positivem_
mfe`/`haeufigstes_symbol_anteil_pct` deshalb immer mit aus.

**Allgemeine Lehre:** bei jeder neuen Kalibrierungsfrage aktiv prüfen, ob
bereits vorhandene "weichere" Felder (MFE, Mindestziel, Richtungstreffer)
eine zusätzliche Ebene liefern koennten, BEVOR neue Datenerhebung als
einzige Option angenommen wird - oft steckt die zusätzliche Trennschärfe
schon in Feldern, die nur noch nie in dieser Kombination ausgewertet wurden.

### 2.7 Plausibilitätsprüfung bei scheinbar eingefrorenen Kennzahlen (Nachtrag 30.07.)

Auslöser: die ATR-/Volatilitäts-Perzentil-Kennzahl (Baustein 2 der
Krypto-Relativwert-Bausteine) zeigte bei BTC/ETH/LINK/TAO/VIRTUAL/HYPE/INJ
über 5 Beobachtungstage einen konstanten bzw. fast konstanten Wert (BTC
durchgehend 0) - auf den ersten Blick ein Verdacht auf eingefrorene/veraltete
Eingabedaten. Eine erste Prüfung bestätigte tatsächlich veraltete
`price_history_ohlc`-Daten - aber nur auf der DESKTOP-Kopie, nicht auf dem
eigentlichen Notebook-Produktivsystem (siehe `_ohlc_aktualitaet_je_symbol()`,
Abschnitt 2.1a). Die Kennzahl selbst blieb aber auch mit nachweislich
frischen Notebook-Daten unverändert - der ursprüngliche Verdacht war damit
nicht erledigt, nur die naheliegendste Erklärung widerlegt.

**Der entscheidende Schritt: ein Kontrollgruppen-Vergleich, keine Einzelwert-
Betrachtung.** Andere Symbole (KAIA, KAITO, NEAR, ONDO) im selben Export,
mit derselben Berechnungslogik, zeigten im selben Zeitraum deutliche
Bewegung. Diese Symbole waren unabhängig bereits als Teil einer
Altcoin-Rally dokumentiert (siehe
[[project_r510_konfidenz_veto_analyse_29_07]]) - die Bewegung korreliert
also mit einem bekannten, unabhängig bestätigten Marktereignis. Die
"eingefrorenen" Symbole (BTC/ETH/Majors) hatten im selben Fenster
schlicht kein vergleichbares Volatilitätsereignis - bei einer langsam
geglätteten Kennzahl (hier: Wilder-ATR) ist ein über Tage konstanter
Perzentilrang bei ruhigem Markt der ERWARTBARE Fall, kein Bug.

**Verbindliches Vorgehen, bevor eine über mehrere Tage konstante/kaum
wechselnde Kennzahl als Fehler eingestuft wird:**

1. Datenaktualität an der Quelle prüfen (siehe 2.1a) - aber NICHT bei einer
   Desktop-Kopie stehenbleiben, wenn die eigentliche Produktionsumgebung
   (Notebook) unabhängig prüfbar ist.
2. Kontrollgruppe bilden: zeigen andere Symbole/Fälle mit derselben
   Berechnungslogik im selben Zeitraum Bewegung? Wenn ja, ist die
   Berechnungslogik selbst funktionsfähig - die Frage verschiebt sich von
   "ist die Funktion kaputt" zu "warum bewegt sich DIESES Symbol nicht".
3. Prüfen, ob die bewegungslosen bzw. bewegten Fälle mit einem unabhängig
   bekannten Markt-/Datenereignis erklärbar sind (hier: die Altcoin-Rally-
   Gruppe aus einer anderen Analyse). Eine Erklärung, die bereits aus
   einem anderen, unabhängigen Fund stammt, ist deutlich belastbarer als
   eine neu erfundene Ad-hoc-Begründung.
4. Erst wenn weder Datenaktualität noch ein Kontrollgruppen-Unterschied
   noch ein bekanntes Marktereignis eine Erklärung liefern, gilt der
   Verdacht auf einen echten Bug als bestätigt.

**Allgemeine Lehre:** ein konstanter Wert ist nicht automatisch ein
Fehlersignal - bei langsam geglätteten Kennzahlen (Wilder-Glättung,
gleitende Durchschnitte, Perzentilränge über lange Historien) ist
Konstanz bei fehlendem zugrundeliegendem Ereignis der Normalfall. Der
Fehlerverdacht entsteht oft erst durch fehlenden Kontrollgruppen-Vergleich.

### 2.8 Methodik-Vorlage: rechnerische Herleitung einer neuen Schwelle statt Schätzung (Nachtrag 30.07., Marktscan-CRV=0,8)

Auslöser: für die Marktscan-Erfolgsmessung wurde ein neuer, eigenständiger
CRV-Schwellenwert gebraucht (getrennt von `backward_tracking.
richtungstreffer_mindest_crv=1,0`, da Marktscan-Kandidaten ein anderes
Volatilitätsprofil haben als Watchlist-Assets). Statt eine Zahl zu schätzen
oder den bestehenden Wert unreflektiert zu übernehmen, wurde die Schwelle
rechnerisch aus echten Daten hergeleitet - als wiederverwendbare Vorlage für
künftige Schwellen-Kalibrierungen hier festgehalten:

1. **Referenzgröße bestimmen**: Ø absolute Tagesbewegung der betroffenen
   Grundgesamtheit berechnen (hier: 13,9% für Marktscan-Kandidaten, deutlich
   höher als bei etablierten Watchlist-Assets - die Volatilitätsprofile
   unterscheiden sich, ein pauschal übernommener Wert wäre nicht passend
   gewesen).
2. **Forward-Return-Verteilung ermitteln**: an mehreren Zeit-Horizonten
   prüfen (hier 12-24h UND 3 Tage), an welchem Perzentil (P70-P75) sich ein
   sinnvoller Ziel-Move ablesen lässt. Wenn die Verteilungen an
   verschiedenen Horizonten nahezu identisch sind (hier: P70 +9,1% vs.
   +7,5%), reicht EIN Schwellenwert für mehrere Anwendungsfälle (schnelle
   UND mehrtägige Erfolge) - keine Notwendigkeit, zwei getrennte Regeln zu
   bauen.
3. **CRV-Äquivalent berechnen**: Ziel-Move ÷ Referenzgröße aus Schritt 1
   ergibt eine Bandbreite (hier 0,65-0,94 aus P70-P75), Empfehlung = Mitte
   der Bandbreite (hier 0,8).
4. **Nutzer-Bestätigung einholen**, bevor der Wert operationalisiert wird -
   eine rechnerisch hergeleitete Zahl ersetzt nicht die fachliche
   Freigabe, sie macht sie nur informierter.

**Allgemeine Lehre:** wann immer ein neuer Schwellenwert für eine andere
Grundgesamtheit als eine bereits bestehende Regel gebraucht wird (anderes
Volatilitätsprofil, andere Zeithorizonte, andere Assetklasse), lohnt sich
dieselbe 4-Schritte-Herleitung, statt einen bestehenden Wert unreflektiert
zu kopieren ODER eine neue Zahl zu schätzen. Dieselbe Methodik gilt
spiegelbildlich auch für zeitbasierte Schwellen (siehe die parallel
hergeleiteten Werte `watchlist_heiss_fenster_stunden=48` und
`schnellerfolg_anteil_max=0,5` im selben Marktscan-Nachtrag - beide aus
beobachteten Verteilungen abgeleitet, nicht geschätzt).

### 2.9 Fazit-Selbsteinschätzung (`eigene_einschaetzung.folgen`) — offener Kalibrierungs-Beobachtungspunkt (Nachtrag 01.08.)

Auslöser: Nutzer-Beobachtung, noch nie ein Signal gesehen zu haben, bei dem
Mistral im `eigene_einschaetzung.kurzfazit`/`folgen` der eigenen Empfehlung
mit "ja" zustimmt (siehe BEAMX-Signal, `fazit_folgen="mit_vorbehalt"`, dazu
Z.ai mit abweichender eigener Richtungseinschätzung SHORT).

**Befund (kompletter Notebook-Export, seit Einführung des Features 25.07.):**

- Hebel: **0 von 572** Signalen mit `fazit_folgen="ja"` - in der gesamten
  Historie noch nie. 508 "mit_vorbehalt" (88,8%), 64 "nein" (11,2%).
- Spot: nur 34 von 761 (4,5%) "ja", Rest "mit_vorbehalt" (95,5%). Nie "nein".
- Gilt für Mistral UND Gemini gleichermaßen (Gemini-Hebel: 8 von 9 ebenfalls
  "mit_vorbehalt") - kein reiner Mistral-Artefakt.
- Widerspricht direkt Regel 26/32 in `hebel_analyst.py`/`analyst.py` ("'mit
  vorbehalt' ist... KEIN bequemer Standardfall... 'ja' und 'nein' sind
  gleichwertige, vollständige Antworten").

**Kreuztabelle `original_action` × `fazit_folgen` klärt das Muster auf:**
für eine ECHTE Trade-Empfehlung (ERÖFFNEN/KAUFEN) ist es praktisch IMMER
"mit_vorbehalt" (Hebel: 220/220 = 100%, Spot: 22/24 = 92%) - "ja"/"nein"
treten fast ausschließlich bei HALTEN-Entscheidungen auf. Nicht durch
Z.ai-Widerspruch erklärbar: selbst wenn Z.ai der Richtung zustimmt
(`zai_uebereinstimmung="ja"`), bleibt das Hebel-Fazit in 122 von 123 Fällen
trotzdem "mit_vorbehalt" - die Hedging-Tendenz ist vom Ergebnis der eigenen
Gegenprüfung unabhängig.

**Backtest-Versuch (01.08.) - aktuell NICHT durchführbar:** von allen 71
"ja"/"nein"-Fällen (64 Hebel-nein + 34 Spot-ja, teils mit Aktions-Überlappung)
hat **keiner** einen aufgelösten `selbst_halten_outcome_status` (siehe
Regel 28, `ist_reines_llm_halten`) - alle `None` oder `nicht_anwendbar`
(Zonen fehlten oder das Feature ist erst seit 31.07. aktiv). Die paar echten
KAUFEN/VERKAUFEN-"ja"-Fälle bei Spot (n=2+2) sind zusätzlich zu wenige und
ebenfalls ohne aufgelösten `outcome_status`. Ein Vergleich "war das Hedging
gerechtfertigt" (CRV/Win-Rate "ja" vs. "mit_vorbehalt") ist damit strukturell
unmöglich, solange keine "ja"/"nein"-Fälle aufgelöst sind.

**Bewusst NICHT sofort gefixt:** eine Prompt-Nachschärfung würde das gleiche
Risiko bergen wie beim Action-Bias-Fund (Regel 27, siehe Regelwerksmanual-
Nachtrag "Regelwerk-Audit Stufe 3, Punkt 4") - ein zu forscher Zwang zur
einen Seite kann den gegenteiligen Bias erzeugen. Erst beobachten, dann ggf.
gezielt nachschärfen.

**Wiedervorlage (kein festes Datum, siehe 2.2a "Mehrtägige Beobachtung"):**
sobald `selbst_halten_outcome_status` erste aufgelöste Fälle zeigt (die
Selbst-Halten-Schatten-Verfolgung braucht Wochen, um genug Fälle zu sammeln),
den Backtest "Fazit-Kategorie vs. tatsächliches Outcome" wiederholen - dabei
Symbol-Konzentrations-Check (2.5) UND Mindestschwelle n≥50 (2.5) beachten,
da die Stichprobe bei "ja"/"nein" absehbar klein bleiben wird.

### 2.10 Z.ai-"Gegenprüfung wäre richtiger"-These — geprüft und über LONG/SHORT-Symmetrietest WIDERLEGT (Nachtrag 01.08.)

Auslöser: Anschlussfrage an 2.9 - Mistrals LONG-Empfehlungen performen
schlecht (18,6% Trefferquote, n=59 aufgelöst) UND Z.ai widerspricht ihnen in
88% der Fälle mit klarer Richtung (n=8 von 17 mit Z.ai-Wert). Erste
Interpretation: Z.ai als informelles Meta-Label/Gegen-Check nutzen. **Vom
Nutzer explizit hinterfragt ("nicht bei halber Strecke halt machen") -
Symmetrietest gefordert:** wie performen Mistrals SHORT-Empfehlungen, und
folgt Z.ai dort ebenfalls konsequent der jeweils anderen Seite?

**Ergebnis, WIDERLEGT die Gegenprüfungs-These:**

| Richtung | n aufgelöst | Trefferquote |
|---|---|---|
| Mistral LONG | 59 | 18,6% |
| Mistral SHORT | 9 (dedupliziert nach Symbol+Tag: bleibt 9) | **0,0%** |

SHORT performt nicht besser als LONG, sondern schlechter - widerspricht der
Annahme "mit dem Bär-Trend gehen wäre richtig gewesen". Zusätzlich:
`zai_eigene_richtung` über ALLE 1336 Hebel-Signale (469 mit Wert) ist
SHORT=246, NEUTRAL=222, **LONG=1** - Z.ai sagt praktisch nie LONG. Das
erklärt die scheinbare Korrelation als Scheinzusammenhang: beide Größen
(Mistral-LONG-Fehlschläge, Z.ais Dauer-Bär-Haltung) hängen unabhängig
voneinander mit dem anhaltenden Bär-Regime zusammen, ohne dass Z.ai
tatsächlich prädiktive Fähigkeit zeigt - der Beweis: wenn Z.ai Recht hätte,
müssten SHORT-Trades (die praktisch immer mit Z.ais Dauerhaltung
übereinstimmen) gut performen. Sie performen am schlechtesten von allen.

**Schlussfolgerung:** das Problem ist RICHTUNGS-UNABHÄNGIG (LONG und SHORT
beide schlecht, SHORT sogar schlechter) - kein Beleg für eine falsche
Richtungswahl, sondern für einen anderen, richtungsneutralen Faktor. Damit
gehört diese Spur NICHT zu einer neuen Meta-Labeling-/Gegenprüfungs-Regel,
sondern zurück zum bereits bestehenden, noch ungelösten Thema in
[[project_enge_stop_loss_backtest_und_massnahmen]] (~77% des CRV-Band-
Einbruchs weiterhin unerklärt) - dort wurde am selben Tag ein neuer,
konkreter Kandidat gefunden (Breakeven-/Teilgewinn-Lock, siehe dortiger
Nachtrag 01.08.). Die Fazit-Vorbehalt-Beobachtung aus 2.9 bleibt davon
unberührt gültig (eigenständiger Befund).

**Methodischer Punkt für künftige Analysen:** eine auffällige Korrelation
zwischen zwei Kennzahlen ist erst dann ein Kausal-/Prädiktivitäts-Beleg, wenn
sie den Symmetrietest übersteht (hier: Spiegelfall SHORT statt nur LONG
geprüft) - sonst bleibt offen, ob beide Größen nur einen gemeinsamen Dritt-
faktor (hier: Bär-Regime) widerspiegeln.

---

## 3. Verwandte Dokumente

- [[Fakten_Entscheidungsmappe.md]] - Entscheidungsraster für Fakten/Prompt-Regeln
  selbst (was landet wie im LLM-Prompt), ergänzt diese Methodik (wie wird eine
  Änderung an diesen Fakten getestet und verifiziert).
- `Regelwerksmanual.md` - dokumentiert einzelne, bereits umgesetzte Regeln/Fixes
  inklusive ihres Verifikationsstands: ab jetzt mit der Stufen-Bezeichnung aus
  Abschnitt 0 statt einem unscharfen "erledigt".
