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

Diese acht Punkte werden IMMER kurz durchgegangen, auch wenn der Anlass für den
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

---

## 3. Verwandte Dokumente

- [[Fakten_Entscheidungsmappe.md]] - Entscheidungsraster für Fakten/Prompt-Regeln
  selbst (was landet wie im LLM-Prompt), ergänzt diese Methodik (wie wird eine
  Änderung an diesen Fakten getestet und verifiziert).
- `Regelwerksmanual.md` - dokumentiert einzelne, bereits umgesetzte Regeln/Fixes
  inklusive ihres Verifikationsstands: ab jetzt mit der Stufen-Bezeichnung aus
  Abschnitt 0 statt einem unscharfen "erledigt".
