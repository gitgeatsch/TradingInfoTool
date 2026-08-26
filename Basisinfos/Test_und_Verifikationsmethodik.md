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
   (`gate_veto_haeufigkeit`). **NACH MUSTER lesen, nicht nach Rohtext**
   (`*_reason_muster`, seit 2026-08-10): die Pipelines bauen ihre Gründe mit
   eingesetzten Werten, dadurch zerfällt EIN Grund in beliebig viele Töpfe.
   Am 10.08. an echten Daten: **722 Rohtexte → 5 Muster**, und die Rangfolge
   kippte vollständig — `CRV <zahl> unter Minimum <zahl>` kam auf **804**
   Fälle, während die Rohansicht als Spitzenzeile *15* zeigte und damit den
   mit Abstand häufigsten Blocker verbarg (das Nur-Long-Veto lag bei 323).
   Ursache: die Anzeige sortiert nach Häufigkeit und schneidet ab — ein auf
   viele Einzeltexte verteilter Grund verschwindet unter der Schnittkante.
   Die Rohzählung bleibt daneben bestehen, wenn der genaue Wert die Frage ist.
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

11. **Z-3-Drawdown-Status** (`z3_status` auf oberster Ebene,
    `portfolio_wert_historie` unter `rohdaten_fuer_backtest`) — hat die
    Notbremse gemeldet, und **stimmt der Wert**? Erstauslösung 05.08. mit 16,7 %.
    Der Alarm ist nur so viel wert wie die Reihe darunter: `index_wert` prüfen,
    nicht `wert_eur`, und auf verworfene FX-Ableitungen im Log achten (05.08.:
    586 Tage verworfen).
12. **Ausstiegsempfehlungen** (`ausstiegs_empfehlungen`) — wie viele offene
    Signale stehen über der Auslöseschwelle, und wie viel R liegt ungesichert?
    Am 05.08.: 15 von 28, darunter SOL mit 10,63 R MFE.
13. **Score-Komponenten** (`hebel_triggers_alle` mit `score_details_json`,
    unter `rohdaten_fuer_backtest`) —
    OHNE `ist_kandidat`-Filter auswerten, sonst misst man im beschnittenen
    Wertebereich. Stand 04.08.: keine Komponente trägt.
14. **Makro-/OI-Historie** (`macro_historie`, `oi_historie`, beide unter
    `rohdaten_fuer_backtest`) — Reichweite
    prüfen: beginnt erst Juli 2026, während die Kurshistorie 748 Tage umfasst.
    Wer beides mischt, verkürzt sein Fenster unbemerkt.
15. **Watchlist-Stammdaten** (`watchlist_stammdaten`) — Voraussetzung für jede
    Aufschlüsselung der Spot-Familie nach Assetklasse. Fehlt der Block, ist
    jede Spot-Auswertung ein Mischtopf (Fehler vom 29.07.).

16. **Durchlässigkeit der Rollen-Kette** (`rollen_kette`, neu 13.08.2026) — je
    Lauf: wie viele Symbole hinein, und **an welcher der acht Stufen** sie
    verloren gehen. **Der aussagekräftigste Wert des ganzen Katalogs**, weil er
    eine Frage beantwortet, die keine andere Kennzahl stellt: alle Punkte 1–15
    messen *aufgelöste* Signale, dieser misst, ob überhaupt eines entsteht. Ein
    Lauf mit 45 hinein und 0 heraus sah bis heute identisch aus, egal ob es am
    Ankertag, am Urteil, an der Geometrie oder an der Rechnung scheiterte.

    Drei Muster sind zu melden: **viele Urteile, null Aktionen** (der Deadloop
    ist zurück) · **Einstiege gerechnet, keiner trägt sich** (Rechenproblem,
    nicht Modellproblem) · **die Faktorzahl nimmt nur zwei Werte an** (sie ist
    dann die Entscheidung noch einmal, Umbauplan Kap. 15). `Punkt 4
    (Konfidenz-Kalibrierung) betrifft nur noch die ALTE Kette` — die neue
    erhebt keine Konfidenz mehr.

Diese sechzehn Punkte werden IMMER kurz durchgegangen, auch wenn der Anlass für den
Export etwas anderes war - Auffälligkeiten ausserhalb der eigentlichen Fragestellung
nicht ignorieren (siehe z.B. den ISOC/X136-Ticker-Fund, der nebenbei beim
Durchgehen von Punkt 6 auffiel).

**Zwei Zugriffsfallen, die bei JEDER Auswertung dieser Blöcke gelten:**

- **`preishistorie_je_symbol` führt EUR- und USD-Zeilen verschachtelt.** Ohne
  Währungsfilter misst man den EUR/USD-Kurs (15,08 % = ln(1/0,86)) als
  „Tagesvolatilität" — für jedes Symbol nahezu gleich. Immer auf eine Währung
  filtern; die Produktion tut es (`lade_kursreihen()` filtert USD).
- **Mehrere Quellen führen dasselbe Symbol mit unterschiedlicher Länge.**
  `preishistorie_signal_symbole` deckt nur den Signalzeitraum ab,
  `preishistorie_ueberholte_symbole` reicht weiter. Wer die erste Fundstelle
  nimmt statt der längsten, misst mit einem Bruchteil der Historie (05.08.:
  2 statt 183 AUF-Tage gemeldet).

### 2.1b Bekannte BRUCHSTELLEN in den Daten (vor jedem Zeitvergleich prüfen)

Ein Vergleich über eine dieser Grenzen hinweg mischt zwei verschiedene
Populationen oder zwei verschiedene Messverfahren. Das ist am 05.08. mehrfach
passiert und hat einen ganzen Arbeitstag gekostet — die Frage „warum kommen so
wenige Signale" war deshalb tagelang nicht beantwortbar.

| Datum | Was sich änderte | Folge für Auswertungen |
|---|---|---|
| **28.07. 17:37 UTC** | Nur-Long-Veto feuert erstmals (`c8dd982`) | 313 SHORT-Vorschläge liegen ab hier als `action=HALTEN` in der DB. Wer HALTEN zählt, zählt sie mit. |
| **31.07. 07:01 UTC** | `original_action` eingeführt (`b9a464b`) | **Davor bei JEDEM Signal leer**, unabhängig von der Entscheidung. Über diese Grenze hinweg damit zu filtern misst die Feldeinführung, nicht das Verhalten. Stattdessen `risk_veto_reason` (seit 14.07. befüllt). |
| **31.07. 06:39 UTC** | `ist_reines_llm_halten` eingeführt (`350918a`) | Für ältere Signale immer `false`. |
| **31.07. ~12:00 UTC** | **Mistral ändert sein Verhalten** (anbieterseitig, Modellname unverändert) | Konfidenz-Mittel 54,1 % → 68,3 %, selbst gewähltes HALTEN 35–51/Tag → 2–6/Tag. Nachgewiesen durch Replay mit bitgleichem Juli-Prompt: 68,0 % statt 55,4 %. **Keine Auswertung über diesen Tag hinweg ohne Zeitschnitt.** |
| **02.08. 23:46** | Ausführungspreis auf Zonen-Grenze statt Tages-Extremwert (`d16242e`) | Realisiertes CRV vor/nach nicht direkt vergleichbar. |
| **04.08. 06:21** | CoinGecko-OHLC-Rückfall für Krypto ohne Kraken (`875f0f5`) | Datenquelle der Outcome-Prüfung wechselt für einzelne Symbole. |
| **05.08.** | **Nur-Long-Umbau**: Veto und beide Vorfilter entfernt | SHORT-Signale laufen ab jetzt in den **regulären** Outcome-Pfad statt in den Veto-Schatten, und SHORT-Kandidaten erreichen erstmals das LLM. Beide Populationen ändern sich gleichzeitig. |

**Regel:** vor jedem Vorher/Nachher-Vergleich diese Tabelle durchgehen. Liegt
eine Grenze im Fenster, entweder den Zeitraum begrenzen oder den Effekt der
Grenze getrennt ausweisen. Ein Trennpunkt darf ausserdem nie nach Sichtung der
Daten gewählt werden — dann gilt Max-Statistik über alle Trennpunkte
(`datiere_einbruch.py`), sonst ist der p-Wert wertlos.

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

### 2.5.4 Viertes Fallbeispiel: R-5.10 erneut geprüft bei 1,4x größerer Stichprobe - Konzentration gesunken, Vorzeichenwechsel bleibt (Nachtrag 01.08.)

Auslöser: eine allgemeine "Detailanalyse aller Messpunkte" gegen einen
frischen Notebook-Export zeigte fuer den Krypto-Spot-Konfidenzschwellen-Veto
(R-5.10) eine deutlich groessere Stichprobe als beim 2.5.2-Fund (n=148 statt
n=106) mit Ø realisiertem CRV +0,334 - auf den ersten Blick eine noch
belastbarere Bestaetigung des scheinbar positiven Befunds.

**Symbol-Konzentrations-Check diesmal VOR jeder Interpretation angewendet**
(gelernte Lehre aus 2.5.2): die Verteilung ist tatsaechlich breiter als beim
ersten Fund - 22 Symbole, groesster Anteil nur 8,1% (AIOZ/IO je n=12), keine
Top-5-Haeufung wie beim 39,6%-Befund von 29.07./30.07. Auf den ersten Blick
sieht das nach einem entschaerften Konzentrationsproblem aus.

**Der Vorzeichenwechsel bleibt trotzdem bestehen, ausgeloest durch ein
EINZELNES Symbol statt einer Gruppe:** AIOZ allein (n=12, 8% der Faelle,
100% Take-Profit-Quote, Ø CRV +4,71) traegt den gesamten positiven
Gesamtdurchschnitt. Ohne AIOZ faellt n=136 verbleibender Faelle auf Ø CRV
**-0,052** - Vorzeichenwechsel, identisch disqualifizierend wie beim
2.5.2-Fund. Zusaetzlich: von allen 148 Einzel-Outcomes sind 91 (61,5%)
negativ, nur 57 (38,5%) positiv - der positive Mittelwert ist eine
Ausreisser-getriebene Verzerrung, kein Mehrheitsmuster.

**Lehre:** eine breitere prozentuale Verteilung (keine Top-5-Gruppe >10
Prozentpunkte) reicht allein nicht aus, um den Konzentrations-Check als
bestanden zu werten - ein einzelner Ausreisser mit extremem CRV kann
denselben Vorzeichenwechsel-Effekt auslösen wie eine Gruppen-Häufung. Die
2.5-Pruefung sollte daher immer BEIDES ansehen: prozentuale Verteilung UND
"was passiert beim Entfernen des staerksten Einzelwerts". Die am 30.07.
getroffene Entscheidung, den Krypto-Spot-R-5.10-Override nicht zu setzen,
bleibt bei 1,4x groesserer Stichprobe bestaetigt - keine Revision noetig.

### 2.5.5 Beitrags-Konzentration zusaetzlich zur Anzahl-Konzentration (Nachtrag 02.08.)

Der Check aus 2.5 prueft, wie sich die Faelle **nach Anzahl** auf Symbole
verteilen. Am 02.08. hat ein Befund diese Pruefung glatt bestanden und war
trotzdem ein Artefakt: Spot-R-5.10-Veto-Schatten, n=156, Oe CRV +0,25,
groesstes Symbol nur **7,7 %** der Faelle. Beim Entfernen genau dieses
Symbols (AIOZ, 12 von 156) drehte der Erwartungswert auf -0,12.

Ursache: die **fuenf groessten Gewinner trugen 32,0 von 39,7 der
Gesamtsumme** - 81 % des Ergebnisses aus 3 % der Faelle. Anzahl-Konzentration
und Beitrags-Konzentration sind zwei verschiedene Dinge; bei schiefen
Verteilungen (Median ueberall bei -1,0, wenige grosse Gewinner) sagt die
erste nichts ueber die zweite.

**Verbindlich ergaenzt:** bei jeder Mittelwert-basierten Kennzahl zusaetzlich
ausweisen, welchen Anteil die 3-5 groessten Einzelwerte an der Gesamtsumme
haben, und den Mittelwert ohne sie erneut rechnen. Kippt das Vorzeichen, ist
der Befund nicht belastbar - unabhaengig davon, wie gut die Anzahl-Verteilung
aussieht.

**Robusterer Ausweg:** wo moeglich auf **Trefferquoten statt Mittelwerte**
umstellen und gegen die mathematisch noetige Break-even-Quote `1/(1+CRV)`
pruefen. Eine Trefferquote ist ein Zaehler und damit ausreisser-robust; ein
einzelner Extremgewinn kann sie nicht verzerren. Genau dieser Wechsel hat am
02.08. den einzigen belastbaren Befund des Tages sichtbar gemacht, nachdem
drei Mittelwert-Befunde gefallen waren.

### 2.5.6 Externe Recherche VOR dem Bestaetigungsversuch, nicht danach (Nachtrag 02.08.)

Nutzer-Vorgabe nach einem Tag mit fuenf revidierten Befunden: wenn bei einem
Muster Unsicherheit besteht, **zuerst kurz extern recherchieren, ob es
theoretisch ueberhaupt plausibel ist** - erst dann an den eigenen (duennen)
Daten zu bestaetigen versuchen.

Zwei belegte Faelle vom selben Tag:

- **Zu spaet recherchiert:** die Break-even-Formel `1/(1+CRV)` kam erst,
  nachdem mehrere Mittelwert-Auswertungen bereits gefallen waren. Frueher
  angewandt haette sie mindestens einen Fehlschluss erspart, weil sie den
  robusteren Messansatz (Trefferquote statt Mittelwert) sofort nahegelegt
  haette.
- **Rechtzeitig recherchiert:** beim ADX-Befund ergab die Recherche, dass die
  ueblichen Schwellen (20/25/30) **marktabhaengig und nicht absolut** sind.
  Sie stammen aus Forex/Aktien; fuer Krypto sind sie ungeprueft. Ohne diesen
  Hinweis waere die geplante Konfirmation mit denselben willkuerlich
  uebernommenen Grenzen gerechnet worden - und haette eine moeglicherweise
  falsch gesetzte Schnittstelle zweimal bestaetigt.

### 2.5.8 Stille Degradierung: der gefaehrlichste Codefehler dieses Projekts

Zwei Muster aus Task #561 (02.08.), beide liefern im Fehlerfall **plausibel
aussehende falsche Zahlen** statt zu scheitern:

**Optionaler Parameter mit Sammel-Fallback.** `watchlist=None` liess zehn
Aggregationen alle Assetklassen in einen Topf werfen - kein Fehler, keine
Warnung, nur ein Ergebnis, das nach Krypto-Daten aussah. Am 29.07. real
passiert und erst bei einer Auswertung aufgefallen.

**Else-faellt-auf-X.** `table = "signals" if tier == "spot" else
"hebel_signals"` - jeder unerwartete Wert landet im Else-Zweig. Wenn X eine
echte Alternative ist (nicht "unbekannt"), wird aus einem Tippfehler ein
stilles Vertauschen von Datenquellen.

**Regel:** Wo ein Fallback eine ECHTE Alternative ist und kein Fehlerzustand,
gehoert an seine Stelle eine explizite Pruefung mit `raise`. Ein Absturz beim
Entwickeln ist harmlos; eine falsche Zahl in einer Auswertung wird geglaubt.
Wo ein Fallback wirklich noetig ist, muss er sich mindestens im Log melden -
mit dem Namen der aufrufenden Funktion, sonst ist die Warnung nicht zuordenbar.

**Beim Massenersetzen:** die erwartete Trefferzahl als `assert` ins
Aenderungsskript schreiben. In diesem Fall fingen zwei solche Assertions je
eine falsche Zaehlung ab, bevor etwas geschrieben wurde - und die
Gegenpruefung fand, dass der erste Durchgang nur 10 von 24 Stellen erfasst
hatte, weil `grep | head` den Rest abgeschnitten hatte.

### 2.5.7 Indikator-Befunde: Basislinie je Bucket ist PFLICHT

Ein Befund der Form "bei hohem X laufen unsere Signale besser" ist erst dann
ein Regelkandidat, wenn die MECHANISCHE BASISLINIE JE X-BUCKET danebensteht -
also: wie oft trifft ein Zufallseinstieg das Ziel bei diesem Indikatorniveau?
Ohne diesen Vergleich misst man Marktphasen und haelt sie fuer Signalqualitaet.

Werkzeug: `agent/krypto/statistik.py::basislinie_je_indikator_bucket()`.

**Lehrbeispiel ADX (02.08.), warum das keine Formalie ist:** der Befund sah
durch ALLE uebrigen Pruefungen gut aus - monoton steigende Trefferquote,
plausible Theorie, Literaturdeckung, scheinbar an einem zweiten Datensatz
repliziert. Er fiel erst hier:

| ADX | Zufallseinstieg (n=1.298) | Signale (n=74) |
|---|---|---|
| unter 15 | 19,9% | 8,8% |
| 15-20 | 25,6% | 18,5% |
| 20-25 | 30,2% | 23,1% |
| ab 25 | 31,1% | - |

Der Zufallseinstieg wird in Trendphasen um 11,1 Prozentpunkte besser. Genau
dieser Anstieg war als "Signalqualitaet" gelesen worden. Ein ADX-Gate haette
nur in Phasen gefiltert, in denen ohnehin alles besser laeuft - und selbst der
beste Bucket hat einen Erwartungswert von -0,068 R.

Zuvor waren schon zwei andere Pruefungen faellig gewesen: die spektakulaeren
oberen Werte des Ausgangsbefunds ("69,2%", "100%") stammten aus Buckets mit
n=1, und die Aussage haing an der Bucket-Wahl (Grenze 20: +13,6pp, Grenze 22:
+8,8pp, Grenze 25: +35,1pp bei n=2).

**Zweitens: Simulation schlaegt Warten.** Die Frage war zunaechst auf "in
einigen Wochen mit mehr Signalen entscheiden" vertagt. Die Basislinie
beantwortete sie sofort mit 3.385 Tagesbalken statt 76 Signalen - besser, als
die Datenlage nach vier Wochen Warten gewesen waere. Wo eine mechanische
Simulation moeglich ist, ist Abwarten die schlechtere Option.

**Drittens - und hier zeigte sich die Regel selbst als unvollstaendig:** aus
derselben Auswertung schien hervorzugehen, dass die Signale in JEDEM
ADX-Bucket unter dem Zufallseinstieg liegen. Bei sauberer Nachmessung loeste
sich das auf. Daraus die entscheidende Ergaenzung:

**Die Basislinie muss MATCHED sein - in Parametern UND Richtung.**

Die erste Messung verglich Signale gegen eine Basislinie mit 6,7% Stop und
CRV 2,0. Die Signale selbst fahren aber 3,2% Median-Stop und CRV 3,50 - das
ist eine voellig andere Strategie, mit Break-even bei 22% statt 33%. Der
"Abstand" war der Unterschied zwischen zwei Strategien, nicht zwischen Signal
und Zufall.

Richtungsgetrennt und mit den Parametern der jeweiligen Signalgruppe
gerechnet:

| Richtung | Signale | Zufall (matched) | Differenz |
|---|---|---|---|
| LONG (n=55) | 16,4% [9-28%] | 16,0% [15-17%] | +0,3pp |
| SHORT (n=14) | 14,3% [4-40%] | 21,3% [20-23%] | -7,0pp, Intervalle ueberlappen |

Der Abstand ist null. Die Signale sind bei LONG genauso gut wie ein
Zufallseinstieg - nicht schlechter, aber auch nicht besser; beide liegen
unter dem Break-even von 22%. SHORT bleibt mit n=14 unbeurteilbar.

**Checkliste fuer jeden Basislinien-Vergleich:** gleiche Richtung, gleicher
Stop-Abstand, gleiches CRV, gleicher Zeitraum. Fehlt eine dieser vier
Bedingungen, misst man etwas anderes als Signalqualitaet - und zwar mit
Zahlen, die ueberzeugend aussehen.

**Konsequenz fuer uebernommene Standardwerte:** jede aus der Literatur
uebernommene Schwelle ist zunaechst eine **Hypothese**, kein Parameter. Vor
der Verwendung als Auswertungsgrenze auf Sensitivitaet pruefen (verschiebt
man sie leicht, bleibt der Effekt?) - sonst misst man die Bucket-Wahl statt
des Effekts.

**Vorgelagerte Regel - erst im eigenen Code, dann extern:** die
Break-even-Formel `1/(1+CRV)` wurde am 02.08. per Web-Recherche "gefunden",
obwohl sie seit 2026-07-29 in `backward_tracking.py::compute_baseline_
vergleich()` implementiert und im Docstring erklaert war ("bei CRV_MINIMUM=2.0
liegt Break-even bei 33,3%"), inklusive exaktem Binomialtest. Vor jeder
externen Recherche also zuerst die eigene Codebasis und die Basisinfos-
Dokumente durchsuchen - sonst wird Vorhandenes teuer nachgebaut oder, schlimmer,
in einer zweiten Variante dupliziert.

**Quellen mitfuehren (Nutzer-Vorgabe 02.08.):** Rechercheergebnisse ohne
Quellenangabe sind spaeter nicht nachpruefbar und nicht widerlegbar - die
Recherche vom 29.07. steht in
`reference_externe_recherche_konfidenz_crv_risikofaktoren_29_07` (Memory)
ohne eine einzige URL und ist damit nur noch "haben wir mal gelesen".
Deshalb ab sofort: jede externe Quelle, auf die sich eine Entscheidung
stuetzt, mit Link und Zugriffsdatum festhalten - hier im Dokument, wenn sie
eine Regel begruendet, sonst in der zugehoerigen Memory.

Quellen der Recherchen vom 02.08.:

- Break-even-Trefferquote je Chance-Risiko-Verhaeltnis (`1/(1+CRV)`; bei CRV
  2,0 = 33,3%), Zusammenhang Trefferquote/CRV und Expectancy-Formel:
  - https://traderssecondbrain.com/guides/win-rate-vs-risk-reward
  - https://www.luxalgo.com/blog/win-rate-and-riskreward-connection-explained/
  - https://fxnx.com/en/blog/the-1-2-risk-reward-rule-why-it-s-the-minimum-for-forex
- ADX-Schwellen (20/25/30) als Trendstaerke-Indikator, Einstiegs-Timing sowie
  die hier entscheidende Warnung, dass diese Schwellen **marktabhaengig und
  nicht absolut** sind und ADX durch Doppelglaettung traege ist und nahe der
  Schwelle flackert:
  - https://blog.traderspost.io/article/adx-indicator-trading-systems
  - https://fxnx.com/en/blog/adx-indicator-strategy-the-gatekeeper-to-profitable-trends
  - https://capital.com/en-int/learn/technical-analysis/average-directional-index

Einordnung der Quellenguete: es handelt sich um Trading-Fachportale, nicht um
begutachtete Literatur. Fuer mathematische Identitaeten (Break-even-Formel)
unkritisch - die ist herleitbar und wurde hier auch unabhaengig nachgerechnet.
Fuer die ADX-Aussagen dienten sie als **Plausibilitaets- und Warnhinweis**,
nicht als Beleg; der Beleg kam aus den eigenen Daten (Sensitivitaetspruefung
plus Replikation an einem zweiten Datensatz).

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

**Nachtrag 05.08.: Schritt 2 kann die ganze Aufgabe beenden — und das ist ein
Ergebnis, kein Scheitern.** Beauftragt war die Neukalibrierung der
Konfidenz-Schwellen nach dem Mistral-Drift. Schritt 2 (Verteilung ermitteln)
ergab, dass Konfidenz überhaupt keine Information über das Ergebnis trägt —
acht Messungen, kein Intervall schließt null aus. Damit entfällt Schritt 3:
eine Schwelle für eine Größe herzuleiten, die nicht diskriminiert, verschiebt
nur eine Zahl.

Die allgemeine Lehre: **vor jeder Schwellen-Kalibrierung zuerst prüfen, ob die
zugrundeliegende Größe überhaupt trennt.** Wer direkt zu Schritt 3 springt,
produziert eine sauber hergeleitete Zahl für ein Kriterium ohne Aussagekraft —
und der gepflegte Herleitungsweg lässt sie glaubwürdiger aussehen, als sie ist.
Dasselbe Muster liegt dem Screening-Score-Befund zugrunde (04.08., „Score
diskriminiert nicht") und dem ADX-Befund in 2.5.2.

Zweitens: bleibt die Größe trotzdem im System (weil sie etwas anderes steuert,
hier die Signal-MENGE), gehört das ausdrücklich benannt und als
Nutzer-Entscheidung markiert statt als hergeleitete Zahl ausgegeben.

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

### 2.11 Positionsgrößen-Empfehlung: Befolgungsgrad als eigener Messpunkt (Nachtrag 04.08., #606)

**Das Problem hinter der Messung.** Die Positionsgrößen-Untersuchung vom 04.08.
ergab für Krypto-Spot einen Vorteil von +0,055 R je Signal (gepaart, mit
Konfidenz-Kopplung +0,073 R) für fractional Kelly auf das CRV. Dieser Vorteil
entsteht **rechnerisch dadurch, dass die Größen variieren** — ein Signal mit
CRV 4,0 wird größer gekauft als eines mit CRV 2,2.

**Der Einsatz wird bisher aber von Hand gesetzt** (100–500 EUR, siehe
`project_positionsgroessen_praxis_entkopplung`). Bleibt das so, tritt der
gemessene Vorteil **nie ein** — die Verbesserung wäre nachgewiesen und
folgenlos zugleich.

**Daraus folgt ein Messpunkt, den es vorher nicht gab:** Es genügt nicht, die
empfohlene Größe zu berechnen. Es muss auch **gemessen werden, ob ihr gefolgt
wurde**. Deshalb werden ab #606 beide Zahlen je Signal gespeichert (empfohlene
Größe und RM-1-Obergrenze), damit das Backward-Tracking später den
Befolgungsgrad und dessen Ergebnis auswerten kann.

**Verallgemeinerung für künftige Regeln:** Wo eine Messung eine Verbesserung
zeigt, die eine Verhaltensänderung voraussetzt, gehört die Verhaltensänderung
selbst zum Messgegenstand. Sonst misst man eine Wirkung, die im Betrieb nie
eintritt — eine Variante der stillen Degradierung aus 2.5.8, nur eine Ebene
höher: nicht der Code degradiert, sondern die Annahme über seine Verwendung.

**Vorbehalt zur Datenlage, der mitgeführt gehört:** die +0,055 R stammen aus
einem 17-Tage-Fenster mit begrenzter Signalzahl. Statistisch belastbar, aber
nicht in Stein. Deshalb wird die Kelly-Zahl als Empfehlung **neben** der
sichtbaren RM-1-Obergrenze ausgewiesen und nicht als alleinige Vorgabe — die
Spanne bleibt sichtbar und einordenbar.

### 2.12 Sieben Messfallen aus einem Tag (Nachtrag 04.08.2026)

Alle sieben sind an einem einzigen Arbeitstag aufgetreten, sechs davon in
eigener Arbeit und vor dem Deploy gefunden. Sie sind hier festgehalten, weil
jede von ihnen ein *plausibles Ergebnis* erzeugt hat — keine Fehlermeldung,
kein Absturz. Genau das macht sie gefährlich.

**1. Gegen den ZWECK messen, nicht gegen das Ergebnis.**
Ich habe die Z.ai-Gegenprüfung — einen *Konsistenzprüfer* — gegen
Handelsergebnisse gestellt und geschlossen, sie trage nichts bei. Sie sagt
aber gar nichts über Ausgänge, sondern nur, ob eine Begründung den Fakten
widerspricht. **Vor jeder Bewertung eines Bausteins nachlesen, wofür er
gebaut wurde.** Ein Rechtschreibprüfer sagt Kurse nicht vorher, und das ist
kein Mangel.

**2. Kein Mittelwert über einen Zeitraum, in dem es das Feature nicht gab.**
„Z.ai-Abdeckung 40,7 %" war ein Artefakt: vor dem Rollout 2,6 %, danach
96,5 %. **Bei jeder Abdeckungs- oder Quotenangabe zuerst nach Datum
aufschlüsseln.** Kosten: zehn Sekunden.

**3. Anpassungsverfahren brauchen den Arm „gar keine Anpassung".**
Die Frage „welche Fensterlänge ist die beste?" liefert immer eine Antwort.
Erst der feste Vergleichsarm zeigte, dass **kein** Fenster den festen Wert
schlägt — die Anpassung selbst war der Fehler, nicht ihre Parametrierung.

**4. LLM-Prompt-Änderungen brauchen einen Rauschboden.**
Ein LLM antwortet auf denselben Prompt nie zweimal gleich. Zwei Arme (mit /
ohne) finden deshalb bei *jeder* Änderung eine „Wirkung". Drei Arme sind
Pflicht: A1, A2 (identisch zu A1) und B. Nur was über A1↔A2 hinausgeht,
ist Wirkung.

**5. Absolute Preisfelder sind Symbol-Kennungen.**
`entry_usd_von` und Geschwister haben eine Intraklassen-Korrelation von
0,998–1,000 — BTC kostet fünfstellig, KAIA Cent. Eine Merkmalssuche darauf
findet „Symbol X war gut", verkleidet als Regel. **Vor jeder Merkmalssuche
die ICC prüfen**, nicht nur eine Namensliste pflegen: die Liste ist nie
vollständig.

**6. Währungsfilter bei Kursreihen aus dem Export.**
`preishistorie_je_symbol` führt EUR- und USD-Zeilen **verschachtelt**. Ohne
Filter misst man die Sprünge dazwischen: 15,08 % = ln(1/0,86) = der
EUR/USD-Kurs, ausgewiesen als „Tagesvolatilität", für jedes Symbol nahezu
gleich. Aufgefallen ist es nur daran, dass die „Verteilung" keine war.
**Eine unplausibel enge Streuung ist ein Messfehler-Signal.**
Die Produktion ist nicht betroffen (`lade_kursreihen()` filtert auf USD).

**7. Skripte aus dem Scratchpad sind keine Module.**
Eine übernommene Datei stand als Modulcode da und startete bei **jedem
Import** einen Lauf über 12.421 Einstiege. `py_compile` und `ast.parse` waren
grün — siehe schon 1.4. **Der Import-Regressionscheck gehört vor jeden
Deploy**, und er misst auch die Import-*Dauer*, nicht nur den Erfolg.

**Übergreifend:** Fünf der sieben Fehler wurden von einem Prüfstand gefunden,
nicht von echten Daten. Der Aufwand für synthetische Prüfstände mit bekannter
Wahrheit hat sich an diesem einen Tag mehrfach zurückgezahlt.

---

## 2.13 Werkzeugkasten — welches Skript WANN (Nachtrag 2026-08-06)

**Warum dieser Abschnitt existiert.** Am 04.08. stellte sich heraus, dass
**drei Mess-Funktionen null externe Aufrufer hatten** — gebaut, dokumentiert,
verifiziert, nie angeschlossen (`compute_baseline_vergleich`,
`compute_sl_mfe_analyse`, `compute_zai_uebereinstimmung_baseline`). Ich habe
stundenlang von Hand nachgerechnet, was fertig im Code lag. Inzwischen stehen
**56 Analyse- und Prüfskripte** im Projektstamm — ohne Index findet niemand das
richtige, und der nächste Nachbau ist nur eine Frage der Zeit.

Sortiert ist nach **Auslöser**, nicht nach Funktion: die Frage im Kopf ist
immer „ich will X wissen", nie „welches Skript gibt es".

### Routine — bei JEDEM neuen Export, ohne Anlass

| Skript | Beantwortet |
|---|---|
| `pruefe_export_standard.py` | Der feste Katalog aus 2.1, seit 13.08. **16 Punkte** — neu Punkt 16, die Durchlässigkeit der Rollen-Kette. **Sind die Kennzahlen auffällig?** Meldet Abweichungen, nicht Vollständigkeit. |
| `pruefe_export_vollcheck.py` | **Stimmt das, was wir glauben gebaut zu haben?** Wirken die Fixes im Betrieb, läuft Backward-Tracking/Schatten-Messung/Monitoring, hängen Signale, fehlen Daten. Seit 13.08. auch C6 (Durchlässigkeit je Lauf) und D6–D8 (kommen die sieben Felder der neuen Kette mit). |

> **Beide sind nötig, sie überlappen nicht.** Der Nur-Long-Umbau hätte in jedem
> Kennzahlen-Katalog unauffällig ausgesehen — er berührt die Kennzahlen gar
> nicht. Umgekehrt findet der Vollcheck keine schleichende Kennzahlen-Drift.

### Nach jedem Lauf der Rollen-Kette (neu 14.08.2026)

| Skript | Beantwortet | Auslöser |
|---|---|---|
| `messe_verkaufsseite.py` | **Ist die Verkaufsseite ein Befund oder ein Münzwurf?** (O-29) Kreuztabelle Aktion × Bestand, dann AUC und Permutationstest über die gemessenen Merkmale. Kein Modellaufruf, feste Saat. | nach jedem Lauf — die Stichprobe wächst, und erst mit ihr bekommt der Test Trennschärfe |
| `messe_begruendungen.py` | **Welche unserer Faktenblöcke tragen?** Ordnet jeden Beleg dem Block zu, aus dem er stammt (`lagebeschreibung.geteilt()`), schlüsselt **je Instrument** auf (Belege je Zeile) und hält die Ausgänge dagegen. Weist den `unbekannt`-Anteil aus — steigt er, ist die **Zuordnung** veraltet, nicht die Datenlage schlecht. | nach jedem Lauf für die Verteilung; die Erfolgsspalte erst, sobald Signale **mit** `belege_json` aufgelöst sind |

> **Warum eigenständig und nicht im Export.** Beim Bauen war mein erster
> Reflex, sie in `extract_notebook_diagnose.py` einzuhängen — „Auswertungen
> laufen über den Export". Das ist die falsche Richtung: 2.1a stellt **Rohdaten**
> bereit (hier `belege_json`, dort ergänzt), 2.13 führt die **Auswertungen** als
> Skripte mit Auslöser. Der Export ist ein BASIS-Werkzeug, das andere
> importieren — würde er selbst zwei Analyseskripte importieren, hinge die
> Datenbeschaffung an ihren Fehlern.

> **Beide Skripte nennen ihre eigene Grenze.** `messe_verkaufsseite.py` druckt
> aus, dass „nicht unterscheidbar" nicht „zufällig bewiesen" heißt;
> `messe_begruendungen.py` trennt Verteilung von Erfolg, solange keine Zeile
> mit Belegen aufgelöst ist. Prüfungen in `pruefe_pakete.py` halten beide Sätze
> fest, damit sie niemand wegkürzt.

### Vier BASIS-Werkzeuge — importieren statt nachbauen

Zwei Implementierungen derselben Simulation laufen garantiert auseinander
(Lehre vom 03.08.). Wer eine dieser Fähigkeiten braucht, **importiert**:

| Basis | Liefert | wird importiert von |
|---|---|---|
| `analyse_crv_gate_survivorship.py` | `zonen()`, `simuliere()`, `basislinie()`, `kennzahlen()` — die survivorship-freie Simulation gegen echte Preisreihen | 3 Skripten |
| `backtest_llm1_historisch.py` | historischer LLM1-Lauf gegen echte Faktensätze | **12 Skripten** |
| `datiere_einbruch.py` | Trennpunkt-Suche per Max-Statistik + Block-Permutation | 8 Skripten |
| `extract_notebook_diagnose.py` | der Export selbst, inkl. `_db_backup()` | 2 Skripten |

### Vor jeder Auswertung, die den Pfad-Bewerter benutzt

| Skript | Auslöser |
|---|---|
| `pruefe_pfad_bewerter.py` | **Nach jeder Änderung an `simuliere_signal()`, `_zonen_absolut()`, `gap_bewusster_fill()` oder an der OHLC-Beschaffung — und vor jeder Auswertung, die auf dem Bewerter aufsetzt.** Fährt das Abnahmekriterium aus Mappe Kapitel 9 Stufe 1: reproduziert der Bewerter die bekannten Ausgänge? Läuft gegen eine **Kopie** der Produktions-DB (`--db`), nie gegen eine laufende Instanz. Enthält Leerlauf-Wache, Negativkontrolle (Start 180 Tage früher) und trennt *ungemessen* von *widerlegt*. |

**Ergebnis des Erstlaufs (2026-08-09) — Stufe 1 gilt damit als bestanden:**

| | n | reproduziert | |
|---|---|---|---|
| dichte Kursreihen (≤ 1,5 Tage je Balken) | 82 | **82** | **100,0 %** |
| dünne Kursreihen (> 1,5 Tage) | 18 | 15 | 83,3 % |
| **gesamt** | **100** | **97** | **97,0 %** |
| Negativkontrolle (Start 180 Tage früher) | 104 | 49 | 47,1 % |

Dazu 6 zensierte Fälle — die Reihe zeigt bis zu ihrem Ende keine Barriere. Das
ist **ungemessen, nicht widerlegt** und geht in keine Quote ein.

> **Die Grenze des Bewerters ist damit benannt und liegt nicht in seiner Logik,
> sondern in der Balkendichte.** Er nimmt Tageskerzen an; „Stop schlägt Ziel am
> selben Tag" ist auf einem Vier-Tage-Balken ein Münzwurf. Neun Symbole mit je
> 23 Punkten sind betroffen (BRETT, CANTON, EURCV, IO, KAIA, KAITO, SUPRA, VSN,
> XNO). Entscheidung 09.08.: **kennzeichnen statt ausschließen** —
> `simuliere_signal()` liefert `balkenabstand_median` mit, jede Auswertung
> berichtet getrennt. Ausschließen hätte 16,8 % der unaufgelösten Hebel-Signale
> aus Stufe 2 entfernt, also genau die Fälle, wegen derer die Stichprobe
> verbreitert wird.

**Zwei Lehren aus dem Lauf selbst:**

1. **Die erste Negativkontrolle war unbrauchbar.** Stop und Ziel zu vertauschen
   ergab 83,0 % gegen 91,5 % — scheinbar ein Einbruch, tatsächlich ein
   Artefakt: der getauschte „Stop" eines LONG liegt über dem Einstieg und wird
   an Tag 0 getroffen, und 87 der 106 bekannten Ausgänge lauten
   `stop_loss_erreicht`. Die kaputte Variante stimmte aus dem falschen Grund
   zu. Erst der Datums-Versatz trennt (47,1 %). *Eine Kontrolle, die aus
   Versehen richtig liegt, ist keine.*
2. **Zensierte Ergebnisse zunächst als Abweichung gezählt** — das drückte das
   Ergebnis von 97,0 auf 91,5 % und hätte drei Datenlücken als
   Reproduktionsfehler ausgewiesen. Dieselbe Familie wie Punkt 3 des
   Nachtrags 09.08.

### Bei Verdacht auf Dauerlast

| Skript | Auslöser |
|---|---|
| `teste_status_cache.py` | **Nach jeder Änderung an `remote/status.py`s Zwischenspeicher, am Abruftakt in `remote/server.py` oder wenn ein neuer `_get_*`-Getter dazukommt.** Sichert, dass die Statusseite ihre teuren Aggregate nicht je Abruf neu rechnet. Vier Prüfungen, **jede mit Gegenprobe gegen den kaputten Zustand**: Cache greift (ohne ihn 5 statt 1 Berechnung), Frist läuft ab, zehn gleichzeitige Abrufe rechnen **einmal** (ohne Sperre zehnmal), und die Fehler-Pause verhindert den Neustart-Kreis (ohne sie ein Versuch je Abruf). |

> **Der Vorfall dahinter (09.08.).** Das Notebook stand dauerhaft bei ~94 % CPU,
> `python.exe` allein bei 70,9 %, dazu 1,0 MB/s Dauer-Leselast — **ohne einen
> einzigen Fehler im Log**, weil es normale Lesezugriffe waren. Die Seite ruft
> alle 2,0 s ab, ein Abruf kostete gemessen 1,39 s am Desktop. Auf dem Notebook
> reicht Faktor 1,5, damit die Anfragen überlappen und sich gegenseitig weiter
> verzögern. Nach dem Fix: **0,117 s, 92 % weniger** — trägt bis Faktor 10.
>
> **Die Lehre ist nicht der Cache, sondern die Suchrichtung.** Zwei meiner
> Hypothesen waren falsch und wurden durch Messung widerlegt (Drive-Sync: 0,1 %
> CPU laut Task-Manager; Systemgüte-Neuberechnung: 2,2 s, bei Stundentakt unter
> 2 %). Erst die Frage *„was passiert bei jedem Abruf, und wie oft wird
> abgerufen?"* führte hin. **Dauerlast ohne Logspur ist normale Arbeit in zu
> hoher Frequenz, nicht ein Defekt** — und die Frequenz steht im Frontend, nicht
> im Backend.
>
> Dasselbe Muster ist in derselben Datei schon zweimal dokumentiert: der
> `_safe()`-Docstring nennt *„264 Fehlschläge in ~9 Minuten … weil die Seite alle
> paar Sekunden pollt"*, der Systemgüte-Cache *„damit überlappten sich die
> Anfragen, der Server kam nicht mehr hinterher"*. Beide Male wurde der
> Einzelfall behoben, nicht die Klasse.

### Nach jeder Änderung an Zonen, Schwellen oder Outcome-Trackern

| Skript | Auslöser |
|---|---|
| `teste_zonen_kante.py` | **Nach jeder Änderung an `_zonen_absolut()`, `_zonen_schwelle()`, `_threshold()` oder an einem der sechs Outcome-Checker.** Sichert, dass Gate und Bewertung dieselbe Zonenkante nehmen — getrennt für SHORT und LONG, mit Gegenprobe gegen die alte Konvention. Prüft außerdem, dass **beide** Tracker-Dateien umgestellt sind. |
| `korrigiere_short_zonenkante.py` | Einmalig, nach dem Umstellen der Kante: rechnet gespeicherte SHORT-Ausgänge über die **produktiven** Checker neu. Trockenlauf ist der Standard, `--anwenden` verlangt zusätzlich `--backup-vorhanden`. |

> **Der Defekt (09.08.).** Eine Preiszone hat zwei Kanten. `_zonen_absolut()` —
> Quelle des CRV, das über die Mindestgrenze 2,0 entscheidet — spiegelt bei
> SHORT auf `_bis` (Stop weiter weg, Ziel näher, beides konservativ). Die
> Outcome-Tracker nahmen für **beide** Richtungen `_von`. Ein Trade wurde damit
> nach der einen Rechnung genehmigt und nach einer anderen bewertet: NEAR
> id=407 hatte ein CRV von 0,72 und bekam **+6,00 R** gutgeschrieben.
>
> **Bei LONG fallen beide Konventionen zusammen** — deshalb ist es über Wochen
> nicht aufgefallen, und deshalb hat auch die Pfad-Bewerter-Abnahme mit 97 %
> nichts gemerkt: die aufgelöste Grundmenge ist überwiegend LONG.
>
> Wirkung der Korrektur: 29 Zeilen, Summe **−43,17 → −59,22 R**. Fünf ändern den
> Status, vier davon von Stop-Loss auf Take-Profit. **Die alte Konvention hat den
> Veto-Schatten-Arm geschmeichelt** — also ausgerechnet die Population, die
> beantworten soll, was das Gate gekostet hat.

**Zwei methodische Lehren aus diesem Fix:**

1. **Der Trockenlauf hat den unvollständigen Fix gefunden, nicht der Test.** Nach
   der ersten Runde meldete er 5 Änderungen statt der erwarteten Größenordnung —
   `hebel_backward_tracking.py` hat **drei** Checker, umgestellt war einer. Ein
   Trockenlauf gegen echte Daten gehört vor jedes Schreiben, gerade wenn man die
   erwartete Größenordnung vorher ausgerechnet hat.
2. **Zwei unabhängige Rechenwege haben sich bestätigt.** Die Vorab-Simulation
   über `simuliere_signal` schätzte −15,22 R, die produktiven Checker lieferten
   −16,05 R. Solche Konvergenz ist die billigste verfügbare Kontrolle.

### Nach jedem Eingriff an Kursreihen, Tickern oder Symbolzuordnungen

| Skript | Auslöser |
|---|---|
| `pruefe_outcome_plausibilitaet.py` | **Nach jeder Symboltrennung, Ticker-Änderung oder Reihen-Rekonstruktion — und routinemäßig bei jedem Export.** Rechnet aus dem gespeicherten R-Wert den Ausstiegspreis zurück und prüft, ob er in der Spanne liegt, die die Kursreihe überhaupt hergibt. Findet damit Ergebnisse, die gegen eine **andere** Reihe entstanden sind. Trockenlauf ist der Standard. |

> **Warum ein datumsbasiertes Kriterium hier nicht reicht.** `OD7C` #2361 trug
> **+20,37 R** — Einstieg 34,63, bewertet gegen die Kupfer-Futures-Reihe bei
> ~6,30. Es gab dafür bereits zwei Reparaturen, und **keine hat gegriffen**:
> die Plausibilitätsschranke vom 06.08. sitzt im *Simulations*-Pfad, nicht im
> Live-Tracker; und `korrigiere_rohstoff_outcome.py` prüft `geprueft_am <
> 2026-08-06`, während dieses Feld inzwischen auf dem 08.08. steht.
>
> **Ein Kriterium, das auf einem Datum beruht, veraltet mit dem Datum.** Die
> Rückrechnung des Ausstiegspreises prüft sich dagegen selbst und findet auch
> den nächsten Fall dieser Familie. Gemessen: 2 Treffer unter 820 Zeilen, keine
> Fehlalarme — und gegen drei absichtlich verdorbene Zeilen alle drei gefunden.
>
> **Die Ursache ist geschlossen:** `lade_ohlc_auf_signal_skala()` bringt die
> Schranke jetzt auch in den Live-Pfad, an allen **sechs** Checkern beider
> Tracker-Dateien. Geprüft von `teste_simuliere_signal_zeilentypen.py` (C1–C5),
> inklusive der Zählung, dass wirklich alle sechs sie benutzen — dieselbe Falle
> wie bei der Zonenkante, wo zunächst nur einer von drei umgestellt war.

### Vor jeder Einführung oder Rücknahme eines Fakts

| Skript | Auslöser |
|---|---|
| `bewerte_fakt_wirkung.py` | **Der Nachweisrahmen aus Mappe Kapitel 9, Stufe 3.** Drei Arme (A1/A2 identisch, B ohne den Fakt), und — das ist das Neue — **alle drei werden gegen die echte Kurshistorie bewertet**. Entscheidungsregel und Mindest-n stehen als Parameter fest, bevor der Lauf startet. |
| `teste_nachweisrahmen.py` | Nach jeder Änderung am Rahmen. Fährt ihn gegen ein Modell mit **bekanntem** Verhalten — neun Lagen, die er unterscheiden können muss. |
| `pruefe_nachweis_robustheit.py` | **Nach jedem abgeschlossenen Lauf, vor jeder Interpretation.** Fährt dieselbe Auswertung über sieben Schnitte (ohne den größten Tag, Tages-Deckel, je Richtung, zwei Horizonte) und stellt die Urteile nebeneinander. Kein einziger neuer Aufruf. Stimmen alle überein, ist der Befund robust; kippt einer, gehört genau der in die Ergebnisdarstellung. |
| `werte_fakt_nachweis_neu_aus.py` | Einzelner Schnitt aus dem gespeicherten Protokoll — `--ohne-tag`, `--deckel-je-tag`, `--nur-richtung`, `--horizont`. Ein Messlauf kostet 800 Aufrufe, eine Neuauswertung Sekunden. |
| `pruefe_nachweis_grundmenge.py` | **Vor** dem Lauf: zehn Fragen an die Grundmenge, alle unabhängig vom Ergebnis beantwortbar. Trägt der Fakt Inhalt? Ändert das Entfernen den Prompt wirklich? Liegt ein Datum im Faktensatz nach seinem Zeitstempel (Lookahead)? Streut die Stichprobe über Zeit und Symbole? |
| `laufe_fakt_nachweis.py` | Der eigentliche Lauf gegen echte Faktensätze. **Immer zuerst mit `--trocken`** — der Trockenlauf hat schon zwei eigene Fehler gefunden. Speichert jede Rohantwort, teilt die A-Arme über mehrere Fakten, bricht unter 30 brauchbaren Fällen ab, ohne einen Aufruf abzusetzen. |

> **Der gepaarte Vergleich ist nicht optional.** Die erste Fassung des Rahmens
> verglich zwei Einzelzahlen — den Abstand der A-Mittelwerte gegen den Abstand
> B↔A. Beide sind *eine* Ziehung. Im Trockenlauf mit einem Modell **ohne jede
> Fakt-Abhängigkeit** meldete das prompt „TENDENZ: Fakt verschlechtert das
> Ergebnis" (−0,078 R gegen 0,067 R). Ein Fehlalarm aus reinem Münzwurf,
> dieselbe Familie wie „Tendenz auf n=1".
>
> Seit der Umstellung auf **gepaarte Differenzen je Fall plus
> Bootstrap-Intervall** lautet dasselbe Urteil korrekt *im Rauschen* (+0,014 R,
> [−0,088; +0,112] über 48 gepaarte Fälle). Beide Arme haben denselben
> Faktensatz gesehen — nur dann ist ihre Differenz eine Aussage über den Fakt
> und nicht über die Fallauswahl.
>
> **Und der zweite Trockenlauf-Fund:** ein falscher Preisschlüssel im
> Testmodell (`aktuell_usd` statt `usd`) ließ die Plausibilitätsschranke fast
> alles verwerfen — 16 statt 97 bewertbare Fälle. Wäre der echte Lauf so
> gestartet, hätte er eine viel zu kleine Stichprobe geliefert und wäre für
> nichts verbrannt worden.

**Was Stufe 3 gegenüber `messe_prompt_nebeneffekte.py` hinzufügt.** Jenes misst
seit dem 04.08. sauber, *ob* ein Fakt das Verhalten ändert — Uneinigkeit,
Konfidenz, Stop-Abstand, CRV. Das sind **Stellgrößen**. Der Befund vom 05./06.08.
lautete „das Modell wählt engere Stops"; ob engere Stops hier besser sind, sagt
er nicht. Der Rahmen schließt das: jede Arm-Antwort geht durch den abgenommenen
Pfad-Bewerter, verglichen wird in **R**.

**Vier Regeln, die vor dem Lauf feststehen** und mit dem Ergebnis ausgegeben
werden — eine Entscheidungsregel, die man nach dem Blick auf die Zahlen wählt,
ist keine:

1. **ERÖFFNEN-Wächter mit Vorrang** vor jeder Ergebnisbilanz (Einbruch ≥ 10 pp
   ⇒ disqualifiziert, unabhängig vom R).
2. **Rauschboden** aus A1↔A2; nur was darüber liegt, zählt.
3. **Mindest-n 5** je Arm für das Wort „Tendenz" — darunter lautet das Urteil
   *ungemessen*, ausdrücklich **kein** Negativbefund.
4. **Maßstab ist CRV-Breakeven** `1/(1+CRV)`, nicht der Münzwurf.

Transportfehler zählen getrennt und stehen in **keinem** Nenner; Formfehler
zählen als HALTEN, weil die Pipeline sie real so behandelt.

> **Zwei Funde beim Bau, beide durch die Gegenprobe erzwungen:**
>
> 1. **`messe_prompt_nebeneffekte._zonen_kennwerte()` verwirft jeden
>    SHORT-Vorschlag stillschweigend** — es rechnet `risiko = entry − stop` und
>    gibt bei SHORT `(None, None)`. Die bisherige Drei-Arm-Messung ist damit auf
>    der halben Richtungsachse blind. Der neue Rahmen leitet die Richtung aus der
>    Zonenlage ab und spiegelt die Kanten wie `_zonen_absolut()`.
> 2. **Mein eigener erster Selbsttest bestand degeneriert.** Das nachgebildete
>    Modell war deterministisch, der Rauschboden also exakt 0,000 R — und
>    „im Rauschen" ist bei Rauschen 0 und Wirkung 0 trivial wahr. Dieselbe Falle
>    wie bei `temperature=0,0`. Erst ein Modell mit reproduzierbarer Streuung
>    prüft die Grenze wirklich (Fall I: Rauschen 0,605 R gegen Wirkung −0,484 R
>    ⇒ im Rauschen; 0,080 gegen −4,011 ⇒ Tendenz).

### Bei Verdacht auf Datenfehler

| Skript | Auslöser |
|---|---|
| `pruefe_fx_ableitung.py` | Verworfene FX-Ableitungen im Log, oder EUR/USD-Werte, die nicht zusammenpassen. Rankt die Ausreißer **und** unterscheidet Veraltung von Illiquidität (Renditekorrelation + sd-Verhältnis + Volumen). |
| `backtest_ueberholt_erkennung.py` | Zweifel an der Überholt-Logik. |
| `teste_rekonstruktion_verdrahtung.py` | Nach jeder Änderung an den Rohstoff- oder Hedge-Pipelines. Prüft die Symboltrennung, den Ankertag, `quelle`, den Volatilitäts-Drag und den TA-Lesepfad — gegen eine temporäre DB, offline (yfinance gemockt). |
| `teste_schwerpunkte.py` | Nach jeder Änderung an den manuellen Schwerpunkten oder der Gleichzeitigkeits-Moderation. Bildet den **Konfliktfall** nach: mehr reife Kandidaten als Plätze, ein gesetzter Schwerpunkt darunter — er muss durchkommen. |
| `teste_wartende_vorschlaege.py` | Nach jeder Änderung an den Persistenzschwellen, der Reife-Logik oder der Vorschau auf wartende Themen-Vorschläge. Prüft die Reifedaten je Mechanismus (7/14/30 Tage), den **Engpass-Tag** (wie viele werden am selben Tag reif) und dass Klartext-Namen neben den stabilen IDs stehen. |
| `teste_richtgroesse_weich.py` | **Nach jeder Änderung an der Richtgröße, an `_bestimme_gesperrte_fall_a_kandidaten()` oder an der Handelbarkeits-Prüfung.** Der Kern ist B2/C1: neun reife Kandidaten bei sechs aktiven Thesen — nichts wird zurückgestellt, **und die siebte These entsteht auch wirklich** (aufrufende Funktion, nicht nur der Helfer). |
| `teste_themenfeld_erfolg.py` | **Nach jeder Änderung an `compute_themenfeld_erfolg()`, an den Kategorie-Assets oder an der Treffer-Schwelle.** Kursreihen werden simuliert, nicht abgewartet — sonst wäre nur der Nicht-Messbar-Zweig getestet. Deckt Treffer, Fehlschlag, `meiden` als Umkehr, `unentschieden`, `neutral` ohne Urteil, die Absicherungs-Ausnahme und alle drei Diagnose-Zweige ab. |
| `teste_provider_sperre.py` | **Nach jeder Änderung an der LLM-Fallback-Kette, an den Fehlerklassen oder an der Probefrist.** Kern ist C1: die Sperre muss schon VOR dem ersten Versuch eines neuen Laufs greifen — ein reiner In-Lauf-Breaker hätte am 07.08. fast nichts verhindert. A4 sichert die Gegenrichtung: ein 429 darf NICHT dauerhaft sperren. |
| `teste_kostenmodell_je_klasse.py` | **Nach jeder Änderung an `kosten_in_r()`.** Prüft die strukturelle Trennung: bei den börsengehandelten Klassen müssen die Kosten mit der Positionsgröße **fallen**, bei Krypto und Hebel **nicht**. Plus Hedge-ETP-Gebühr über die Haltedauer und die Ehrlichkeit der `belegt`-Kennzeichnung. |
| `teste_themen_und_steckbrief.py` | Nach jeder Änderung an `kategorien.yaml`, den Themen-Brücken oder dem Asset-Steckbrief. Prüft insbesondere, dass **Lücken erlaubt bleiben** — fehlende Angaben fallen weg statt geraten zu werden. |
| `pruefe_fakten_rollout.py` | **Nach jeder Fakten- oder Regeländerung an einer Pipeline.** Vergleicht die `build_facts()` aller sechs Pipelines und meldet jeden Fakt, der nur in einer Teilmenge existiert — plus zehn Mechanismen auf Pipeline-Ebene. Fällt **kein Urteil**: viele Unterschiede sind richtig, das Skript stellt die Frage, ob sie *entschieden* wurden. Begründete Fälle gehören in `BEGRUENDETE_UNTERSCHIEDE`. |
| `pruefe_aufruf_signaturen.py` | **Nach jedem neuen Parameter an einer Funktion mit mehreren Aufrufern.** AST-Durchlauf über alle Dateien: findet Aufrufe, die Argumente übergeben, die die Zielfunktion nicht kennt. Am 06.08. hätte er den `crv_baender`-Fehler vor dem Deploy gefunden — und belegt hinterher, dass es der einzige seiner Art war. |
| `teste_hedge_risikofaktoren.py` | Nach jeder Änderung an der Hedge-Pipeline oder am Hedge-Prompt. Prüft die sieben Risikofaktoren auf **umgekehrte Wirkrichtung** und die Zonenwache am echten DBPK-Fall vom 06.08. (Stop über Entry) mit dem korrekten 3QSS-Fall als Gegenprobe. |
| `teste_hedge_wirksamkeit.py` | Nach jeder Änderung am Hedge-Erfolgsmaß oder am Tier-Split. Rechnet einen konstruierten Fall mit **bekannter Antwort** (perfekt gegenläufige Absicherung nimmt einen 29,36-%-Einbruch heraus) und prüft die Messbarkeits-Wache. |
| `teste_tageswert_abdeckung.py` | Nach jeder Änderung an `schreibe_tageswert()` oder am Portfolio-Wert-Job. Prüft Bezugstag (Vortag) und Abdeckungswache inkl. der beiden echten Betriebsfälle (3,0 % und 42,4 %) und der Schwelle bei genau 80 %. |
| `teste_email_darstellung.py` | Nach jeder Änderung an den Mailtexten, `render_detail_html()` oder `send_notification_email()`. Baut echte Mails **mit und ohne Bild**, dekodiert den HTML-Teil und prüft Farbe, `color-scheme`-Meta und alle vier Risikofaktoren-Fälle. |
| `teste_simuliere_signal_zeilentypen.py` | Nach jeder Änderung an `simuliere_signal()` oder an etwas, das DB-Zeilen entgegennimmt. Lädt die Reihen über `lade_kursreihen()` statt sie nachzubauen — genau die Lücke, durch die am 06.08. ein `.get()` auf `sqlite3.Row` in die Produktion kam. |
| `teste_migration_und_filter.py` | Nach jeder Änderung an `init_db()` oder der Portfolio-Bewertung. Prüft die einmalige Umzugs-Migration auf Idempotenz und Datenerhalt sowie den Plausibilitätsfilter inkl. Grenzfällen (Faktor 2,99/3,01, veraltete Reihe). |

> **Beide laufen ausschließlich gegen temporäre Datenbanken** — sie setzen
> `db.DB_PATH` um und prüfen das per Assert nach. Auf dem Desktop unbedenklich.

> **Die Frage, die am 06.08. gefehlt hätte:** *was hat diesen Fehler bisher
> unsichtbar gehalten?* Der Scheinwert von 51.000 EUR unter OD7H war nur
> deshalb folgenlos, weil ein zweiter Defekt (FX-Ableitung) alle USD-Symbole
> aus der Bewertung warf. Den FX-Defekt allein zu beheben hätte den Schaden
> erst freigesetzt. **Vor jedem Einzelfix prüfen, was ihn bisher gedeckelt
> hat.**

### Vor jeder Aussage über Signalqualität, Gates oder Stop/CRV

| Skript | Auslöser |
|---|---|
| `messe_stop_abstand_baender.py` | Jede Frage, in der der **Stop-Abstand mitvariiert**. Kein Auflösungs-Filter, Basislinie je Band, Block-Bootstrap. |
| `pruefe_sprung_bei_crv4.py` | Verdacht auf eine **konfundierte Kennzahl** — Vorlage für „Effekt innerhalb gleicher Stratum-Breite kontrollieren". |
| `analyse_crv_gate_vs_positionsgroesse.py` | Gate oder Positionsgröße? |

### Vor jeder Prompt- oder Fakten-Änderung

| Skript | Auslöser |
|---|---|
| `messe_prompt_nebeneffekte.py` | **Dreiarm-Design mit Rauschboden** (A1/A2 identisch + B). Pflicht vor jeder Prompt-Aussage. |
| `messe_regimephasen_llm.py` + `teste_regimephasen.py` | **Jede Frage der Form „liegt es am Modell oder am Markt?"** — siehe eigener Abschnitt 2.15 unten. |
| `pruefe_llm_stabilitaet.py` | **Vor jedem Messlauf über mehr als ~50 Aufrufe.** Bitgleiche Eingabe mehrfach — sagt vorher, welche Effektgröße überhaupt nachweisbar ist. Abschnitt 2.16. |
| `pruefe_regimephasen_vorflug.py` | **Vor jedem Lauf mit einem neu gebauten oder länger ungenutzten Client.** Schemabau, Anbieterweiche mit Gegenkontrolle, Faktensatz, Promptgröße, echter Aufruf, `_validate_hebel()`, Messfelder, Modellrotation. |
| `messe_kettennaht_eingriffe.py` | **Fragen der Form „welcher eingespeiste Fakt würgt das Verhalten ab?"** — faktorielle Arme mit A1/A2-Rauschboden, additiv statt subtraktiv (der historische Faktensatz enthält die Produktionsfakten nicht). |
| `backtest_llm1_historisch.py` | Misst **RICHTIGKEIT**, nicht nur Veränderung. Hat am 04.08. einen bereits gemeldeten Befund widerrufen. |
| `teste_kosten_fakt.py`, `teste_regel28_echt.py` | Test an **echten** Faktensätzen aus dem Betrieb statt rekonstruierten. |
| `agent/krypto/kanarienvogel.py` | **Gebaut, NICHT aktiviert.** Provider-Drift-Replay gegen eingefrorene Faktensätze. Aktivieren = eine Zeile. Auslöser: ein zweiter unerklärter Verhaltenssprung. |

### Einmalig, abgeschlossen — nicht routinemäßig laufen lassen

Der Rest der 43 (`messe_halten_ursache*`, `teste_richtung_*`,
`pruefe_short_ursache`, `analyse_score_komponenten`, `backtest_regeln_29_07`,
`messe_fensterlaenge_selbstjustierung`, …) gehört zu abgeschlossenen
Untersuchungen. Sie sind **Belege**, keine Werkzeuge — vor dem Wiederverwenden
prüfen, ob ihre Annahmen noch gelten. Mehrere ruhen auf Populationen oder
Messgrößen, die inzwischen widerlegt sind.

> **Regel für neue Skripte:** wer eines baut, das mehr als einmal laufen soll,
> trägt es hier ein. Sonst ist es in zwei Wochen unauffindbar und wird
> nachgebaut — mit abweichender Logik.

---

## 2.17 Vorhersagbarkeit prüfen, BEVOR aufbereitet wird (Nachtrag 2026-08-10)

**Die Reihenfolge, die am 10.08. gefehlt hat.** Ein Merkmal wird erst dann in
den Faktensatz aufgenommen, wenn geprüft ist, dass es Vorhersagekraft hat —
nicht, weil die Praxisliteratur es nennt. Beides ist nötig: die Literatur sagt,
*worauf* zu schauen ist; nur eine Messung sagt, ob es *bei unseren Daten* trägt.

**Das Verfahren, ohne Kontingentbedarf:**

| Skript | Frage |
|---|---|
| `pruefe_analogie.py` | trägt die Analogie auf den Messlauf-Ankern? |
| `pruefe_analogie_gross.py` | dasselbe auf Tausenden Fällen, vektorisiert, Bootstrap |
| `pruefe_trader_merkmale.py` | Trader-Merkmale gegen alte, Regression, walk-forward |

**Drei Zusicherungen, die jedes solche Skript braucht** — alle drei sind am
10.08. zuerst verletzt gewesen:

1. **Keine stille Teilmenge.** `pruefe_analogie.py` wertete 32 von 80 Ankern
   aus, weil die Merkmalstabelle grundlos bei Index 250 begann. Die Auswahl war
   nicht zufällig, sondern systematisch die späten Anker — erkennbar daran,
   dass die Basisrate auf 0,6478 statt 0,6272 lag. **Fehlende Fälle immer
   zählen und ausgeben.**
2. **Kausalität am Auflösungsdatum, nicht am Beginndatum.** Ein Vergleichsfall
   von vor fünf Tagen löst sich erst in fünfzehn Tagen auf; ihn mitzuzählen
   heißt, die Zukunft zu befragen. Jede Tabelle führt deshalb ein Feld
   `bekannt_ab`.
3. **Das Urteil muss in beide Richtungen prüfen.** Die erste Fassung testete
   nur `Obergrenze < 0` und hätte ein gesichert *schlechteres* Ergebnis als
   „kein Befund" ausgegeben. Drei Fälle, nicht zwei: besser, schlechter,
   unentschieden.

**Und die Gegenprobe, die am meisten sagt:** ein Nachbarschaftsverfahren über
mehrere k laufen lassen. Nähert sich das Ergebnis mit wachsendem k der
Basisrate *von unten* an, trägt die Ähnlichkeit nichts — das Verfahren wird
genau in dem Maß besser, in dem es aufhört, Nachbarschaft zu benutzen.

Befund und Zahlen: `Arbeitsstand_Deadloop_09_08.md` Abschnitt 6.

## 2.16 Anbieter-Stabilität — was gemessen ist und was NICHT gemessen wird (Nachtrag 2026-08-09)

**Werkzeug:** `pruefe_llm_stabilitaet.py`. Auslöser: **vor jedem Messlauf über
mehr als ~50 Aufrufe.** Fährt denselben Anker mehrfach mit bitgleicher Eingabe
und misst Richtungsdreher, Konfidenz-Streuung, Fazit-Dreher und Dauer.

**Warum vor und nicht nach dem Lauf:** ein Effekt, der kleiner ist als die
Streuung bei identischer Eingabe, ist nicht nachweisbar — egal wie viele Anker
man nachlegt. Diese Messung sagt vorher, welche Effektgröße überhaupt
erreichbar ist.

### Der Bezugswert

`nvidia/nemotron-3-super-120b`: **4 Richtungsdreher von 34 Paaren = ~12 %** bei
identischer Eingabe (08.08.). Der Rauschpegel produzierte damit mehr Dreher als
der eigentliche Formatvergleich (3 von 36).

**Stichprobengröße ist hier die Falle.** Eine Probe mit 3 Ankern × 5
Wiederholungen ergab 0 Dreher — das widerlegt die 12 % **nicht**, denn bei
einer echten Quote von 12 % ist „0 von 15" mit rund 15 % Wahrscheinlichkeit
reiner Zufall. Wer die Quote prüfen will, braucht eine Größenordnung mehr Paare.

### Was NICHT nochmal gemessen wird — und warum

**OpenRouter unter `json_object` ist erledigt, nicht offen.** Gemessen am
09.08.: Formgültigkeit 36/38 und 18/20 gegen **38/38 und 20/20** unter striktem
`json_schema`. Die Entscheidung steht in `agent/llm_schema.py`
(`_STRIKT_FUER_MODULE`), und wir würden die schlechtere Variante nie fahren.

> **Ein Test einer Konfiguration, die wir ausschließen, erzeugt Zahlen und
> keine Entscheidung.** Nutzer-Einwand 09.08., und er ist richtig: die Frage
> „wäre die Instabilität unter `json_object` anders?" ändert nichts an dem, was
> wir tun.

**Die offene Lücke, ehrlich vermerkt statt geschlossen:** die 12-%-Messung vom
08.08. hält fest, dass beide Arme *dasselbe* Format hatten — aber **nicht,
welches**. Ob die Richtungsinstabilität unter striktem Schema genauso groß ist,
ist damit formal ungemessen. Das bleibt als Vorbehalt stehen; es zu schließen
wäre nur dann Arbeit wert, wenn eine Entscheidung davon abhinge.

### Fairness zwischen Anbietern

Jeder Anbieter läuft mit dem Format, das **für ihn entschieden** wurde
(OpenRouter strikt, Gemini und Z.ai `json_object`) — nicht mit demselben. Ein
Vergleich unter gleichem Format wäre ein Laborvergleich, den wir im Betrieb nie
fahren.

---

## 2.15 Marktphasen-Simulation — das Verfahren gegen „Modell oder Markt?" (Nachtrag 2026-08-09)

**Anlass:** Nutzer-Vorgabe 09.08., wörtlich — *„simuliere einfach eine andere
Marktphase aus der Historie und wie die LLMs damals reagiert hätten"*.

### Warum es diese Messung geben muss

Ausnahmslos jedes Signal der Datenbank trägt `regime = "baer"` (1.391 Hebel,
2.223 Spot, gemessen 06.08.). **Aus Produktionsdaten ist deshalb nie trennbar,
ob ein Befund am Modell oder an der Marktphase liegt** — es gibt nur eine
Phase. Jede Frage dieser Form ist mit Betriebsdaten unbeantwortbar und muss
simuliert werden.

Die Kursreihen reichen bis 2024-07 zurück und enthalten alle drei Phasen:
bulle 35,1 %, bär 36,0 %, gemischt 28,8 % der Tage.

### Abgrenzung zu den bestehenden Regime-Messungen — sie widersprechen sich nicht

| Skript | ändert | Befund |
|---|---|---|
| `messe_regimewechsel_trockenlauf.py` | nichts, rechnet Gates nach | krise_extrem bricht den Durchlass auf 1/14 |
| `teste_regime_llm.py` | nur **Label + Profil**, gleiche Marktdaten | **kein messbarer Effekt** (0,10–0,32× Rauschboden, n=19) |
| `messe_regimephasen_llm.py` | **die Marktdaten selbst**, Label passend dazu | offen |

Die ersten beiden fragen „macht das Wort im Prompt einen Unterschied?". Das
neue fragt „macht der Markt einen Unterschied?". **CC2 wiederholt dabei
absichtlich den Aufbau von `teste_regime_llm.py` auf einer neuen Stichprobe** —
hält der Null-Befund von 06.08. dort nicht, ist das ein Widerspruch und gehört
gemeldet, nicht verrechnet.

### Die vier Gegenprüfungen, ohne die der Lauf nichts wert ist

| | prüft | Abbruch bei |
|---|---|---|
| **CC1 Reproduktion** | trifft der BÄR-Arm die Produktion? (82,7 % SHORT, Stop-Median 8,25 %) | ja — trifft er nicht, misst der Aufbau nicht das System |
| **CC2 Label gegen Daten** | Bullen-Anker mit erzwungenem `baer`-Label | nein, aber Widerspruch zu 06.08. gehört berichtet |
| **CC3 Rauschboden** | dieselben Anker zweimal; `nemotron` dreht bei identischer Eingabe in ~12 % die Richtung | jeder Armunterschied darunter ist kein Befund |
| **CC4 Konzentration** | trägt ein einzelnes Symbol den Armunterschied? | — |

### Zwei Konstruktionsfallen, die hier konkret zugeschlagen haben

**1. Der degenerierte Wächter.** Der erste Trockenlauf meldete CC3 mit „0 %
Richtungsdreher" — weil der Mock deterministisch antwortete. Der Wächter hatte
nichts geprüft und sah trotzdem gut aus. Derselbe Fehler war zwei Tage zuvor
schon einmal passiert (Nachweisrahmen, Rauschboden 0 → „IM RAUSCHEN" bestand
trivial). **Ein Mock muss die Eigenschaft nachbilden, die der Wächter messen
soll**, sonst prüft der Selbsttest den Selbsttest.

**2. Der Stichproben-Alias.** Die erste Fassung der Ankerwahl sortierte alle
Kandidaten nach (Datum, Symbol) und lief mit fester Schrittweite darüber. Bei
mehreren Symbolen pro Tag trifft eine feste Schrittweite dann **systematisch
immer dasselbe Symbol**. Gefunden hat das nicht der Test, sondern seine
Gegenkontrolle D1g („die übrigen Symbole kommen auch an"). Ohne sie wäre eine
stille Symbolverzerrung in den echten Lauf gegangen, und CC4 hätte sie als
„Konzentration" gemeldet, ohne die Ursache zu zeigen.

### Was am Faktensatz überschrieben werden muss — und warum

`baue_historische_fakten()` setzt `regime.wert` auf `"nicht rekonstruierbar"`.
Das ist für diesen Lauf **falsch**: eine „Unknown"-Option löst laut `regime.py`
Abstention aus — *„genau der Mechanismus, der bei uns die ERÖFFNEN-Quote von
93 % auf 3 % gedrückt hat"*. Ein Arm mit „unbekannt" misst also den
Abstention-Reflex, nicht die Marktphase.

### Was NICHT gemessen wird, und warum

Die vier Primärgrößen (ERÖFFNEN-Quote, LONG-Anteil, Anteil CRV ≥ 2,0,
Stop-Abstand) sind **reine Verhaltensgrößen** — sie hängen an dem, was das
Modell ausgibt, nicht daran, wie wir den späteren Verlauf bewerten. Das ist
Absicht: das statische Halten bis zur Barriere wurde am 06.08. als falsches
Instrument verworfen (`Konstruktion_Zeitskalen_06_08.md` V3), live läuft seit
05.08. der Trailing-Stop ab +1R. Ergebnisgrößen (`ausgang`, `r`) werden
mitgeschrieben, aber ausdrücklich **nachrangig** und mit diesem Vorbehalt.

---

## 2.14 Externe Methodenlage — wie die Fachliteratur unsere Probleme löst (Nachtrag 2026-08-09)

**Anlass:** Nutzer-Vorgabe, *„eine Detailrecherche wie die aktuelle Lehrmeinung
bzw. moderne Methoden mit unseren Problemen umgehen"*. Sortiert nach unseren
Problemen, nicht nach Autoren — und mit der ehrlichen Angabe, was wir davon
schon haben, was fehlt, und was wir bewusst nicht brauchen.

### A. Unser Problem: 17 bis 33 Symbole, und daraus ein Vertrauensintervall

**Was wir tun:** Cluster-Bootstrap über Symbole (seit 09.08.), weil die
Beobachtungen innerhalb eines Symbols korreliert sind.

**Was die Literatur sagt — und es ist eine Warnung an uns.** Cameron, Gelbach
und Miller zeigen, dass Cluster-Verfahren „presume the number of clusters is
large" und dass Standardtests bei **fünf bis dreißig Clustern über-ablehnen**.
Genau in dieser Spanne liegen wir (17 bis 41). Der empfohlene Ausweg ist der
**Wild Cluster Bootstrap-t**: statt ganze Cluster neu zu ziehen, werden ihre
Residuen mit einem zufälligen Vorzeichen multipliziert und die Teststatistik
unter der Nullhypothese neu gerechnet. Damit sinken Ablehnungsraten von 10 %
auf die nominellen 5 %.

> **Folge für uns:** unser jetziges Intervall ist eher zu ENG. Ein Befund, der
> knapp signifikant aussieht, ist es vermutlich nicht. Das ist die richtige
> Fehlerrichtung für Vorsicht, aber es gehört benannt — und der Wild-Variante
> gehört der Vorzug, sobald ein Ergebnis an der Grenze entscheidet.

### B. Unser Problem: viele Varianten probiert, die beste behalten

**Was wir tun:** Methodik 2.5 verlangt bereits, dass informell nacheinander
getestete Hypothesen als Multiple-Testing gelten.

**Was die Literatur ergänzt:** Bailey und López de Prado formalisieren das im
**Deflated Sharpe Ratio** — er korrigiert die Kennzahl um Selektionsverzerrung,
Stichprobenlänge und Nicht-Normalität, indem er berücksichtigt, dass der Sieger
aus einer Menge von Versuchen stammt, nicht isoliert gemessen wurde. Dazu die
**Probability of Backtest Overfitting**: die Wahrscheinlichkeit, eine
überangepasste Strategie zu wählen, wächst rasch mit der Zahl der Versuche.

> **Folge für uns:** wir zählen unsere Versuche nicht. Wenn wir zwanzig Fakten
> nacheinander durch den Nachweisrahmen schicken, ist der beste davon per
> Konstruktion geschmeichelt. Ein **Versuchszähler je Fragestellung** wäre der
> billigste wirksame Schutz — noch nicht gebaut.

### C. Unser Problem: überlappende Beobachtungsfenster

Unsere Signale überlappen: dasselbe Symbol, Fenster von 7 bis 14 Tagen, oft
mehrere Signale in derselben Woche. Zwei Beobachtungen teilen sich damit einen
Teil ihres Kursverlaufs.

**Der Standard dafür ist Purging und Embargo** (López de Prado): Trainingsdaten,
deren Label-Fenster in den Testbereich hineinreichen, werden entfernt, und ein
Band nach dem Testintervall wird zusätzlich gesperrt. **Combinatorial Purged
Cross-Validation (CPCV)** erzeugt daraus viele chronologie-treue Aufteilungen
und liefert eine **Verteilung** von Ergebnissen statt einer einzigen Zahl.

> **Folge für uns:** unser Drei-Arm-Verfahren ist davon nicht betroffen — es
> vergleicht gepaart auf demselben Fall, die Überlappung kürzt sich heraus.
> Betroffen ist alles, was Signale als unabhängige Beobachtungen zählt, also
> jede Trefferquote und jede Basislinie. Das erklärt zusätzlich, warum unsere
> Intervalle eher zu eng sind.

### D. Unser Problem: „noch nicht genug n" — und dann doch hinschauen

Das Muster zieht sich durch das ganze Projekt: eine Frage wartet auf n≥50, in
der Zwischenzeit wird trotzdem hingesehen, und jeder Blick erhöht still die
Fehlerwahrscheinlichkeit.

**Die moderne Antwort sind E-Werte und anytime-valid inference.** E-Werte sind
nichtnegative Statistiken mit Erwartungswert höchstens eins unter der
Nullhypothese; die zugehörigen E-Prozesse bleiben **unter beliebigem Peeking
gültig**. Dieselbe Schwelle kontrolliert den Fehler erster Art, egal wann und
wie oft man hinsieht — man darf jederzeit stoppen, ohne die Stichprobengröße
vorher festzulegen.

> **Folge für uns:** das passt exakt auf unsere Lage — Signale tropfen mit rund
> 1,2 pro Tag ein, und die Frage „reicht es schon?" stellt sich dauernd. Ein
> E-Wert-Prozess je offener Frage würde das Warten auf feste n-Schwellen
> ersetzen. **Der aussichtsreichste noch nicht gebaute Baustein dieser Liste.**

### E. Unser Problem: das LLM antwortet auf identische Eingaben verschieden

Gemessen: 8 bis 12 % Richtungsdreher bei identischer Eingabe.

**Die Literatur bestätigt, dass das nicht wegkonfigurierbar ist.** Nichtdeterminismus bleibt selbst bei Temperatur 0 bestehen — Batch-Reihenfolge auf
der GPU, Attention-Kernel, Fließkomma-Nichtassoziativität und Lastverteilung
zwischen Rechenzentren tragen dazu bei. Temperatur 0 ist eine Heuristik, keine
Garantie.

**Der etablierte Umgang ist Self-Consistency:** mehrfach abfragen und die
häufigste Antwort nehmen. Das reduziert die Streuung und kostet Aufrufe.
Bemerkenswert für uns: Eingaben **nahe der Entscheidungsgrenze** streuen
deutlich stärker als eindeutige — die Instabilität ist also selbst ein Signal
für „knapper Fall".

> **Folge für uns:** ein Mehrheitsentscheid aus drei Abfragen würde die
> Richtungsdreher dämpfen und verdreifacht die Kosten. Der billigere Weg: die
> **Uneinigkeit als Fakt behandeln** — dreht das Modell bei Wiederholung, ist
> der Fall knapp, und knappe Fälle gehören nicht gehandelt. Das wäre ein Gate
> aus einer Größe, die wir schon messen können.

### F. Unser eigentliches Problem: schlägt die Ebene den Zufall?

**Der Stand der Forschung ist ernüchternd und entlastet uns zugleich.**
Aktuelle Benchmarks für LLM-Handelsagenten (StockBench, Agent Market Arena,
InvestorBench, DeepFund) kommen übereinstimmend zu dem Schluss, dass Agenten
passive Vergleichsmaßstäbe **nicht** zuverlässig schlagen; über zehn führende
Modelle hinweg stammen die kumulierten Renditen aus Markt- und Stilexposition,
**nicht aus Selektions-Alpha**.

> **Folge für uns:** unser gemessener Abstand von −7 bis −10 pp gegen den
> CRV-Breakeven ist kein Zeichen dafür, dass wir etwas besonders falsch gebaut
> hätten. Er entspricht dem, was die Literatur für diese Aufgabenklasse
> berichtet. Das ist kein Trost, aber es verschiebt die richtige Frage: nicht
> *„wie machen wir das LLM besser"*, sondern *„wofür ist es überhaupt das
> richtige Werkzeug"*.

### G. Die Antwort der Literatur auf genau diese Lage: Meta-Labeling

López de Prado trennt **Richtung** (die Seite) von **Ausführung** (ob und wie
groß). Ein primäres Modell erzeugt die Richtung; ein sekundäres Modell sagt
**nicht** die Richtung voraus, sondern ob die Vorhersage des primären Modells
genommen werden soll. Es tauscht Recall gegen Precision, hebt den F1-Wert und
senkt Fehlsignale und Transaktionskosten.

> **Warum das auf uns besonders gut passt — und die Messlage es stützt:**
>
> 1. Wir haben bereits ein primäres Modell: den Trigger-/Screening-Zweig.
>    Gemessen erreicht der naive `trendfolge`-Zweig **18,5 %** bei n=81 — über
>    der Gesamtquote von 16,0 %. Die Mechanik ist also nicht das Schwächste.
> 2. Die Richtung ist die instabilste Größe, die wir haben (8–12 % Dreher).
>    Genau sie dem LLM abzunehmen, spielt seine Schwäche aus.
> 3. „Nehmen oder nicht" ist eine binäre Frage mit einem klaren Erfolgsmaß
>    (Precision), und sie ist mit **viel weniger** Fällen messbar als
>    Zonenqualität.
>
> **Das ist die konkreteste Umbau-Option, die aus dieser Recherche folgt.** Sie
> ist keine Entscheidung dieses Nachtrags — sie gehört dem Nutzer vorgelegt.

### Was wir davon schon haben

| Baustein | Stand |
|---|---|
| Triple-Barrier-Methode | seit jeher, Ziel/Stop/Zeitlimit |
| Aalen-Johansen für konkurrierende Ereignisse | `kumulative_inzidenz()`, 03.08. |
| Block-Bootstrap über Symbole | `_block_bootstrap_ziel_anteil()`, 03.08. |
| Multiple-Testing-Bewusstsein | Methodik 2.5, seit 29.07. |
| Kein Vorausschauen im Backtest | `backtest_llm1_historisch._reihe_bis()`, 04.08. |
| **Wild Cluster Bootstrap** | **fehlt** — unsere Intervalle sind zu eng |
| **Versuchszähler / DSR** | **fehlt** — wir zählen unsere Versuche nicht |
| **E-Werte / anytime-valid** | **fehlt** — würde das Warten auf n-Schwellen ersetzen |
| **Meta-Labeling** | **fehlt** — die naheliegendste Architekturoption |

### Quellen

- [Bailey/López de Prado, The Deflated Sharpe Ratio (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2460551)
- [Cameron/Gelbach/Miller, Bootstrap-Based Improvements for Inference with Clustered Errors (REStat 2008)](https://direct.mit.edu/rest/article/90/3/414/57731/Bootstrap-Based-Improvements-for-Inference-with)
- [MacKinnon/Webb, The Wild Bootstrap for Few (Treated) Clusters](http://qed.econ.queensu.ca/pub/faculty/mackinnon/working-papers/qed_wp_1364.pdf)
- [Purged cross-validation (Übersicht)](https://en.wikipedia.org/wiki/Purged_cross-validation)
- [Combinatorial Purged Cross-Validation, QuantInsti](https://blog.quantinsti.com/cross-validation-embargo-purging-combinatorial/)
- [Ramdas et al., Game-Theoretic Statistics and Safe Anytime-Valid Inference](https://projecteuclid.org/journals/statistical-science/volume-38/issue-4/Game-Theoretic-Statistics-and-Safe-Anytime-Valid-Inference/10.1214/23-STS894.pdf)
- [Anytime Validity is Free: Inducing Sequential Tests (2025)](https://arxiv.org/pdf/2501.03982)
- [StockBench: Can LLM Agents Trade Stocks Profitably in Real-world Markets?](https://stockbench.github.io/)
- [When Agents Trade: Live Multi-Market Trading Arena for LLM Agents (WWW 2026)](https://dl.acm.org/doi/10.1145/3774904.3792821)
- [Meta-Labeling (Übersicht)](https://en.wikipedia.org/wiki/Meta-Labeling)
- [Hudson & Thames, Does Meta Labeling Add to Signal Efficacy?](https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/)
- [Why LLMs Are Not Deterministic Even at Temperature 0](https://www.qanswer.ai/blog/llm-non-determinism-temperature-zero)
- [A Practical Guide for Evaluating LLMs and LLM-Reliant Systems (arXiv 2506.13023)](https://arxiv.org/pdf/2506.13023)

---

## 3. Verwandte Dokumente

- [[Fakten_Entscheidungsmappe.md]] - Entscheidungsraster für Fakten/Prompt-Regeln
  selbst (was landet wie im LLM-Prompt), ergänzt diese Methodik (wie wird eine
  Änderung an diesen Fakten getestet und verifiziert).
- `Regelwerksmanual.md` - dokumentiert einzelne, bereits umgesetzte Regeln/Fixes
  inklusive ihres Verifikationsstands: ab jetzt mit der Stufen-Bezeichnung aus
  Abschnitt 0 statt einem unscharfen "erledigt".

---

# Nachtrag 2026-08-09: vier Lehren, die an einem Tag teuer waren

## 1. Der A/A′-Nullabgleich ist Pflicht, nicht Kür

Ein Vergleich A gegen B sagt **nichts**, solange nicht bekannt ist, wie stark A
gegen sich selbst streut. Der zweite Arm läuft mit **identischem** Aufbau, nur
noch einmal.

Real belegt: bei `nemotron-3-super-120b` produzierte der Nullabgleich **mehr**
Richtungsdreher (4 von 34) als der Formatvergleich (3 von 36). Die erste
Messung — ohne belastbaren Nullabgleich — hatte „das Schema dreht die
Handelsrichtung" ergeben. **Falsch, und ohne den A′-Arm wäre der Fehlschluss
stehengeblieben.**

Bei `temperature=0.0` ist der Nullabgleich **degeneriert** (A gegen A′ = 100 %).
Dann hat der Vergleich keinen Maßstab, und jede Abweichung sieht signifikant
aus. In diesem Fall zusätzlich bei Produktionstemperatur messen.

## 2. Der ERÖFFNEN-Wächter hat Vorrang vor jeder Abweichungsbilanz

Bricht die ERÖFFNEN-Quote ein, ist die Maßnahme **disqualifiziert** — unabhängig
davon, wie gut die Trefferbilanz aussieht.

Warum: Bei einer Grundmenge aus überwiegend Verlierern (35 zu 3) ist
Nichthandeln immer die punktbeste Strategie. Am 09.08. meldete die Auswertung
für Gemini „7 von 10 Abweichungen zugunsten des strikten Schemas" — sechs davon
waren „vermeidet Verlust" durch *Nichthandeln*, und dagegen stand ein verpasster
Gewinn von +2,45 R. Der Wächter fing es: **ERÖFFNEN-Quote 76 % → 61 %,
16 pp.** Ohne ihn wären 16 % der Signale vernichtet worden.

> Das Ziel sind MEHR Signale, nicht weniger. Eine Kennzahl, die sich durch
> weniger Handeln verbessern lässt, misst das Falsche.

## 3. Transportfehler und Formfehler strikt trennen

Ein 429, ein Timeout oder ein 5xx sagt **nichts** über die Eignung eines
Formats, Modells oder Anbieters. Wer ihn in den Nenner nimmt, bestraft die
geprüfte Sache für ein Ratenlimit.

Real: Geminis 429-Serie wurde zunächst als „ungültig" gezählt und hätte das
strikte Schema für ein Ratenlimit abgestraft. Ein Modell mit Transportfehlern
ist **ungemessen, nicht widerlegt.**

Folgeregel für Messläufe: Transportfehler dürfen bei der Wiederaufnahme **nicht
als erledigt** gelten, sonst zementiert der erste missglückte Lauf seine eigenen
Lücken.

## 4. Das teuerste Muster: den eigenen Aufbau messen statt der Sache

**Dreimal an einem Tag**, immer dieselbe Familie — die Kontrolle nicht geprüft,
bevor das Ergebnis gelesen wurde:

| Vorfall | Was gemessen wurde |
|---|---|
| Mini-Prompt ohne Feldliste | `json_object` konnte gar nicht bestehen — „Pflichtfeld fehlt" maß den Testaufbau |
| Fallauswahl „20 neueste" | **null** davon hatten einen bekannten Ausgang; die Besser/Schlechter-Frage war unbeantwortbar, bevor der erste Aufruf lief |
| Veraltete DB-Kopie | „0 % rechenbar" maß das Alter der Kopie (OHLC bis 19.07.), nicht die Datenlage |

Dazu drei **falsche Alarme** aus fehlerhaften Prüfskripten (AST sah nur den
Return-Namen; ein Regex hielt innere `"` für Stringanfänge und lieferte 54
Falschmeldungen; ein Vergleich auf literale Escapes war schlicht falsch).

> **Regel: jede Messung benennt ihre Kontrolle.** Wenn A und B nicht dieselbe
> Eingabe sehen, ist das Ergebnis keine Aussage über den Prüfgegenstand. Und
> bevor ein Befund berichtet wird: prüfen, ob das Prüfwerkzeug ihn überhaupt
> finden *könnte*.

## 5. Ein Test, der auf sauberem Code besteht, beweist nichts

Jeder neue Wächter wird gegen den **kaputten** Zustand gefahren, bevor er zählt.
Am 09.08. dreimal angewandt:

- Prompt-gegen-Schema: gegen den Zustand vor dem Fix meldet er `antizyklisch`
  als überzählig
- Remote-JS-Syntax: gegen die kaputte Zeile meldet er Spalte 37 (der Browser
  meldete 38)
- Breaker-Vorbelegung: offene Verbindung sperrt, geschlossene sperrt nicht

## 6. „Tendenz" braucht ein Mindest-n und muss beim Aufstocken halten

Ein Fakt darf auf Tendenz eingeführt werden, ohne vollen Nachweis — der Zustand
mit null Signalen ist nicht tragbar, und das Ausstiegsverfahren führt „fehlender
Wirkungsnachweis" ohnehin als **keinen** Rücknahmegrund.

> Eine Tendenz zählt aber nur, wenn sie beim Vergrößern der Stichprobe **hält
> oder wächst — nicht wenn sie schrumpft.**

Zweimal unabhängig belegt: Regel-Ablation +0,281/+0,182 bei 12 Ankern →
+0,014/−0,013 bei 28. Kosten-Fakt −0,734 bei 12 → −0,334 bei 24. Beide
schrumpften. Mindestens **5** bewertbare Fälle, bevor das Wort fällt.

## 7. Eine Wache gegen den leeren Lauf gehört in jeden Test

Ohne Kandidaten sind alle Zusicherungen wahr, ohne dass etwas geprüft wurde.
`teste_kette_reihenfolge.py` und `teste_allocator_prioritaet.py` prüfen deshalb
ausdrücklich, dass genug Fälle vorliegen — 6 bzw. 13.

## 2.18 Prüfsteine aus der eigenen Historie (Nachtrag 2026-08-11)

**Was ein Prüfstein ist und was nicht.** Ein Prüfstein ist ein echtes Signal aus
der Vergangenheit, dessen Ausgang in der Kursreihe steht — nicht verhandelbar,
nicht nachträglich gewählt. Er zeigt **grobe Fehlfunktion**, nicht Güte: vier
Fälle beweisen nichts über eine Trefferquote, aber sie beweisen, dass ein
Konzept einen bekannten Fehler nicht mehr macht.

**Die vier vom 10.08.**, aus `signals` mit bekanntem Verlauf:

```
BTC  KAUFEN     14.07.  →  −2,3 %
KAS  TAUSCHEN   14.07.  →  −8,9 %
KAS  NACHKAUFEN 15.07.  →  −8,6 %   (Position stand −14,6 %)
GRIFFAIN HALTEN 21.07.  →  +33,8 %  (verpasst)
```

**CAT ist als Prüfstein untauglich** (+44,5 %): seine FX-Ableitung war
nachweislich kaputt, der Anstieg kann ein Datenartefakt sein. Ein Prüfstein aus
einer defekten Reihe prüft die Reihe, nicht das Verfahren.

**Drei Zusicherungen, die jedes Prüfstein-Skript braucht:**

1. **Ausgang mit Stop rechnen**, nicht als Endrendite — siehe
   `Zielgroessen_und_Erfolgsmasse.md`, Nachtrag 11.08. Ein Trade mit +22,3 %
   Endrendite kann ausgestoppt worden sein.
2. **Die Begründungen mitspeichern.** Das Skript vom 11.08. speicherte nur
   Aktion und Betrag — die Ursache der sechs verpassten Fälle stand in den
   Begründungen und musste mit zwei zusätzlichen Aufrufen nachgeholt werden.
3. **Anker mit genug Zukunft wählen.** Für 20 Tage Horizont muss der Anker
   mindestens 20 Handelstage vor dem Reihenende liegen — sonst fällt er still
   heraus statt aufzufallen.

**Werkzeuge:**

| Skript | Frage |
|---|---|
| `pruefe_rollenkette.py` | läuft die Kette durch? drei Stufen: trocken / ein Fall / Prüfsteine |
| `messe_betragsdeckel.py` | gepaarte Messung zweier Prompt-Varianten auf denselben Ankern |

---

## 2.19 Externe Methodenlage zu vier Messfragen (recherchiert 2026-08-11)

**Anlass, Nutzervorgabe:** *„Recherche zuerst am Anfang vor der Messung, damit
die Basis stimmt und potentielle Fehler der Messung vermieden werden — seriöse
Quellen."* Vier Fragen, bei denen eine falsche Annahme die Messung entwertet.

### 2.19.1 Erstdurchgang — Konstruktion bestätigt, eine Annahme verletzt

Das Drei-Barrieren-Verfahren (López de Prado, *Advances in Financial Machine
Learning*) labelt nach der zuerst berührten Grenze — oben, unten, Zeit. **Unsere
Konstruktion in `messe_degradierung.py::erstdurchgang()` entspricht dem Standard.**

**Was wir übersehen haben: überlappende Labels verletzen die IID-Annahme.**
Benachbarte Anker teilen ihr Auswertungsfenster; der 24.06. und der 25.06.
schauen auf fast dieselbe Zukunft. Die Standardantwort ist **average uniqueness
weighting** — je Beobachtung messen, wie viel ihres Informationsgehalts
einzigartig ist, und danach gewichten.

> **Folge für die Messung vom 10.08. (Arbeitsstand 6.1/6.2):** Die 8.441 Fälle
> sind **keine 8.441 unabhängigen Beobachtungen**. Die effektive Stichprobe ist
> kleiner, die dort berichteten Konfidenzintervalle sind **zu eng**. Der Befund
> („kein Verfahren schlägt die Basisrate") kippt dadurch nicht — ein
> Nullergebnis wird durch weniger Power nicht stärker. Aber die Intervalle
> dürfen nicht mehr als eng zitiert werden, und jede künftige Messung dieser
> Bauart braucht die Gewichtung.

### 2.19.2 Anker — gegen die „Leitplanke", mit einer Einschränkung

Anchoring ist bei Sprachmodellen gemessen: GPT-4 erreicht einen Anchoring-Index
von **0,45** (Menschen 0,61 auf demselben Datensatz), 62 Fragen, drei Modelle,
je 30 Durchläufe (arXiv 2412.06593).

Zwei Details entscheiden unsere Bauformfrage:

| Beobachtung | Bedeutung für uns |
|---|---|
| **Experten-Anker wirken am stärksten** — alle 12 Fragen mit Experten-Anker zeigten die Verschiebung, p < 0,05 | ein aus ATR gerechneter Stop **ist** ein Experten-Anker |
| **Irrelevante Anker wirkten gar nicht** | die Stärke hängt an der wahrgenommenen Autorität, nicht an der Zahl |
| **Keine Standard-Gegenmaßnahme half** — weder Chain-of-Thought noch „ignoriere den Anker" noch Reflexion | wir könnten es nicht wegprompten |

**Entscheidung: Bauform B** — das Modell sieht die gerechneten Niveaus **nicht**.
Bauform C („Leitplanke") führt die stärkste bekannte Ankerklasse ein.

> **Einschränkung, ausdrücklich:** Gemessen wurde an *numerischen
> Schätzaufgaben*. Unsere Ausgabe ist kategorial (KAUFEN/NICHTS_TUN). Ein Befund
> von einer Aufgabe auf eine andere zu übertragen ist derselbe Fehler wie bei
> den Alt-System-Befunden. Starkes Argument, kein Beweis für unseren Fall.

**Nebenbefund (arXiv 2507.20957, sechs Modelle):** Konfirmationsneigung in der
Anlageanalyse — selbst bei maximaler Gegenevidenz lagen die Flip-Raten **unter
60 %**. Das dämpft die Erwartung, eine getrennte Entscheidungs-Rolle würde einen
einmal gefassten Befund noch umwerfen.

### 2.19.3 Bestand — die Literatur entscheidet es NICHT

**Widersprüchliche Lage, und das ist selbst das Ergebnis:**

- *Dafür:* LLM-Agenten zeigen Referenzpunkt-Verhalten (Kaufpreis, Allzeithoch
  verschieben die Risikobereitschaft); eine Arbeit misst eine Reduktion des
  Dispositionseffekts um **64,5 % / 72,7 %** nach Fine-Tuning — er war also
  vorher da. Bei GPT-4 trat die Reduktion nicht auf.
- *Dagegen:* Henning et al. (Caltech/Virginia Tech, sechs Modelle, arXiv
  2502.15800) finden *„textbook-rational"* Verhalten mit nur gedämpfter
  Blasenbildung — die menschlichen Verzerrungen tauchten dort **nicht** auf.

**Konsequenz: keine importierbare Annahme.** Die Frage, ob der Bestandsblock die
Entscheidung färbt, muss **bei uns** gepaart gemessen werden — dieselben Fakten
mit und ohne Block. Der n=3-Hinweis aus 7.12 bleibt ein Hinweis.

### 2.19.4 Textform — kein Standard, aber die Richtung ist gedeckt

Einen etablierten Standard „wie formuliert man Fakten für ein LLM" gibt es
**nicht**. Konvergente Einzelbefunde:

```
semantische gegen numerische Fragen, gleicher Wissensbereich:
   Claude 3   68,7 %  gegen  61,3 %
   GPT-4      68,4 %  gegen  56,7 %
notationsuebergreifender Zahlenvergleich:   50-70 %  (knapp ueber Zufall)
Matrixdaten in natuerliche Sprache umschreiben:  hebt die Leistung deutlich
```

**Grundsatz 10.1 der Faktenmappe („Aussagen statt Zahlenliste") ist gestützt.**
**R-T1 und R-T2 sind es nicht** — sie stehen auf unserer eigenen Messung aus
Arbeitsstand 7.11 und werden als eigene Regeln geführt, nicht als
Standardübernahme. Eine Quelle zu behaupten, wo keine ist, wäre derselbe Fehler
wie die drei quellenlosen Recherchen vom 29.07.

### Quellen

- López de Prado, *Advances in Financial Machine Learning* (Drei-Barrieren,
  average uniqueness)
- arXiv 2412.06593 — Anchoring Bias in Large Language Models: An Experimental Study
- arXiv 2507.20957 — Your AI, Not Your View: The Bias of LLMs in Investment Analysis
- arXiv 2510.12189 — Agent-Based Simulation of a Financial Market with LLMs
- arXiv 2502.15800 — Henning et al., LLM Trading: Agent Behavior in Experimental
  Asset Markets
- J. Comput. Soc. Sci. 10.1007/s42001-026-00465-4 — LLM agents and
  path-dependent market dynamics
- PMC12279315 — Numerical vs. Semantic Medical Knowledge Benchmark
- arXiv 2602.07812 — LLMs Know More About Numbers than They Can Say


---

## 2.20 Werkzeug: Abdeckungsprüfung vor jedem Lauf (Nachtrag 2026-08-11)

`pruefe_abdeckung.py` — kein Modellaufruf. Prüft je Assetklasse, welche
Watchlist-Assets die Rollen-Ebene beschreiben kann, und benennt bei jedem
Ausfall den **Grund** (keine Historie · zu wenige Kerzen · ETC-Reihe fehlt,
Futures-Referenz vorhanden · weder Historie noch Preis).

**Gehört vor jeden Mess- und Produktionslauf.** Stand 11.08.: 17 von 57 Assets
nicht beschreibbar, die Klasse `rohstoffe` vollständig ohne Abdeckung. Wer ohne
diese Prüfung misst, überspringt 30 % der Watchlist stumm — und ein stumm
übersprungenes Asset sieht in der Auswertung aus wie „kein Signal", nicht wie
„nicht geprüft".

**Die Schranke muss dieselbe sein wie in der Kette** (220 Kerzen). Eine Prüfung
auf „Symbol vorhanden" übersieht HYPE mit 167 Kerzen.

---

## 2.21 Fachstandard je Rolle — was die Literatur verlangt (recherchiert 2026-08-11)

**Nutzervorgabe:** *„was ist für mich ein guter Einstieg? sollte in der Literatur
und Standards stehen — was bewertet der Analyst? Was braucht der Trader als
Text? Braucht der Trader Fibonacci oder schadet die Angabe?"* Richtig gestellt:
das ist Fachwissen, keine Geschmacksfrage, und gehört recherchiert statt erfragt.

### 2.21.1 Was ein guter Einstieg ist

| Kriterium | Standard |
|---|---|
| **Zahl der Belege** | **drei bis vier UNABHÄNGIGE Faktoren**; ab fünf sinkt die Leistung |
| Ausrichtung | Setup zeigt in dieselbe Richtung wie die übergeordnete Struktur |
| Mehrere Zeitebenen | Einstieg, Auslöser und Zone deuten gleich |
| Chance/Risiko | mindestens 1:2 |

### 2.21.2 Was der Marktanalyst beurteilt — vier Dimensionen

**Trend · Volatilität · Breite · Liquidität/Makro.** Die Volatilität bestimmt
dabei laut Standard, wie wahrscheinlich ein Stop getroffen wird, und wie
Ausführungsqualität und Slippage ausfallen.

### 2.21.3 Was der Trader als Text braucht

- **Fünf oder mehr Indikatoren → schlechtere Ergebnisse als ein bis zwei klare
  Regeln.**
- Federal Reserve, Überlastungsindex bis 1885 zurück: mehr Information →
  **sinkende Entscheidungsgenauigkeit**, geringeres Handelsvolumen.
- Zwölf Indikatoren verlangsamen die Entscheidung messbar.

### 2.21.4 Fibonacci — schadet die Angabe?

**Nach dieser Lage überwiegt der Schaden.** Drei Gründe:

1. **Eigenständige Vorhersagekraft fraglich.** Die empirischen Arbeiten sind
   uneins; wo Effekte auftreten, verschwinden sie in jüngeren Teilperioden.
   Einfache Widerstandsniveaus schneiden in einer Untersuchung besser ab.
2. **Als Text an ein Modell ein Experten-Anker.** „61,8 % bei 2.184,32 EUR" ist
   genau die Ankerklasse mit der stärksten Wirkung, und keine Gegenmaßnahme half
   (2.19.2).
3. **Aus derselben Kursreihe wie alles andere** — es erhöht die *gefühlte* Zahl
   der Belege, ohne einen unabhängigen hinzuzufügen.

*Redlich dagegen:* eine Arbeit findet, dass Fibonacci **in Kombination mit einem
Vorhersagemodell** dessen Leistung verbessert. Als eigenständiger Beleg im Text
taugt es nach dieser Lage nicht.

### 2.21.5 Der Satz, der alles bindet

> *„If indicators are not independent — if they're all derived from the same
> underlying price data — their apparent agreement is an illusion. They're not
> four independent votes; they're the same price data filtered through four
> different lenses."*

**Redundante Indikatoren erzeugen die „Illusion der Bestätigung".** Das ist
genau der Mechanismus, gegen den `unabhaengige_faktoren` im Trader-Prompt steht
— und die Recherche liefert damit die Begründung, die dort bisher fehlte.

### Quellen

Confluence-Standard (colibritrader, usetct) · Fibonacci empirisch
(ScienceDirect S0957417421012495, arpgweb ijefr4(6)) · Marktregime
(wallstreetcourier) · Multikollinearität (Shukla, MQL5; Earn2Trade) ·
Informationsüberlastung (Federal Reserve IFDP; Pomegra)

---

# 2.20 Werkzeugkasten-Nachtrag (2026-08-12/13): die Prüfskripte des Umbaus

Ergänzt 2.13. Drei neue Skripte, und eine geänderte Arbeitsweise.

## Die Skripte

| Skript | Auslöser | was es beantwortet |
|---|---|---|
| `pruefe_pakete.py` | **nach jedem Paket, immer kumulativ** | Hält alles Gebaute noch? `--paket N` für eines, `--paket gesamt` für den Abgleich *zwischen* den Paketen, `--paket B1` für den Orchestrator, `--paket Export` für den Notebook-Export. Stand 13.08. abends: **404 Prüfungen** — ⚠️ **Stand 24.08. abends: 1.679**, und die Ausgabe geht zusätzlich nach Google Drive (siehe 2.72 unten) |
| `messe_sentiment_je_horizont.py` | einmalig, bei Fragen zur Stimmung | Wirkt Fear & Greed je Horizont verschieden? BTC, 3.087 Tage |
| `messe_top_fakten.py` | einmalig, bei Fragen „welcher Fakt trägt?" | 12 Merkmale gegen die Geometrie der App, 37 Symbole, 20.494 Anker |
| `pruefe_rollenkette.py` | vor jedem Live-Lauf | die Kette an echten Ankern, mit Wortlaut |

## Was diese Runde über das Prüfen selbst gelehrt hat

**1. EIN TEXTFUND IST KEINE AUSSAGE.** Zwei eigene Prüfungen sind daran
gescheitert, dass sie ein Wort suchten statt einer Eigenschaft:

| Prüfung | suchte | fand fälschlich |
|---|---|---|
| „im Text steht kein R mehr" | `" R"` | „ **R**EICHWEITE", „ **R**ücklauf" |
| „prüft keine Konfidenz" | `"confidence_pct"` | den Docstring, der erklärt, warum es die Größe *nicht mehr gibt* |

**Regel daraus:** wo eine Eigenschaft gemeint ist, muss ein Muster geprüft
werden (`Zahl gefolgt von R`, `Bezeichner gefolgt von Vergleichsoperator`) —
nicht das Vorkommen einer Zeichenkette.

**2. DIE GEDRUCKTE AUSGABE FINDET, WAS DER EINZELTEST NICHT FINDET.** Mehrere
Fehler waren im Modul unsichtbar und erschienen erst, als zwei Blöcke in
derselben Nachricht nebeneinander standen:

- „Stop auf 59.100 nachziehen" neben einem Kurs von 58.000 — die Position wäre
  längst ausgestoppt gewesen
- daneben ein Nachkauf-Vorschlag für dasselbe Asset
- die Liquidation zweimal mit **verschiedenen** Zahlen (35.638 gegen 30.238)
- „55,500.00 EUR" — englische Tausendertrennung
- dieselbe Position in zwei Gruppen der Ausstiegs-Mail

**Regel daraus:** jedes ausgabeerzeugende Modul wird **an seiner fertigen
Ausgabe** geprüft, nicht nur an seinen Rückgabewerten.

**3. EINE KOPIE WIRD GEPRÜFT, NICHT BEHAUPTET.** Wo eine Definition zweimal
stehen muss (Produktion darf nicht von einem Messskript abhängen), vergleicht
eine Prüfung **beide auf echten Daten** — `faktenblock.werte_aus_reihe()` gegen
`messe_top_fakten.merkmale()`, Abweichung < 1e-9. Ohne das wäre es genau die
Kopie, die still veraltet (so geschehen bei den Kostensätzen: Spread 0,0015
statt 0,0025).

**4. GEGEN EINE KOPIE IM SPEICHER, WENN DIE ECHTEN DATEN FEHLEN.** Die
Produktivdatenbank hat **keine offene Position und keinen einzigen MFE-Wert** —
dort hätte „geprüft 0" wie Erfolg ausgesehen. Die Ausstiegskette wird deshalb
gegen `sqlite3.connect(":memory:")` mit `backup()` geprüft; die Produktivdatei
wird nur gelesen.

**5. EINE ZAHL OHNE IHRE SCHICHTUNG IST KEINE DIAGNOSE.** „78 von 118 Signalen
haben leere Fakten" klang nach Defekt und war eine Verwechslung zweier
Grundgesamtheiten — alle 78 sind Abweisungen *vor* der Analyse. Nach
Gate-Zustand aufgeschlüsselt löste sich der Befund auf. Derselbe Fehlertyp wie
beim CRV-Gate am 02.08. (Survivorship).

**6. EINE PRÜFUNG UND EIN PUSH GEHÖREN NICHT IN DENSELBEN BEFEHL.** Am 12.08.
wurde ein Commit mit einer fehlgeschlagenen Prüfung gepusht, und die
Commit-Nachricht behauptete „alle bestanden" — weil `pruefe_pakete.py && git
push` in einer Zeile lief und das Ergebnis nicht gelesen wurde. Das macht eine
Gegenprüfung wertlos.

## Zwei Messfallen, neu belegt

**Multiples Testen braucht eine zweite Hürde.** Zwölf Merkmale sind zwölf
Tests; eines sieht zufällig gut aus. In `messe_top_fakten.py` muss ein Merkmal
**beides** haben: ein Bootstrap-Band ohne Null **und** eine monotone Ordnung
über die Fünftel. Ein Zickzack hat keinen Mechanismus, sondern Rauschen.

**Punktschätzer und geclusterte Schätzung können sich widersprechen** — und
dann gilt die geclusterte. „Tagesspanne": Spanne **+1,5 pp**, Bootstrap-Band
**vollständig negativ** (−8,1 … −1,9). Der gepoolte Wert entstand aus der
Zusammensetzung der Symbole. Wer nur die Spanne liest, übernimmt das Vorzeichen
verkehrt. **Ein solcher Widerspruch ist ein Ausschlusskriterium, kein Detail.**


---

## 2.21 Was die ersten echten Läufe über das Messen gelehrt haben (13.08.2026)

**Ein Lauf, den man nicht nachlesen kann, muss wiederholt werden.** Der erste
Stufe-C-Lauf schrieb in eine Kopie **im Speicher** — mit dem Prozessende war er
weg, und die zehn Signale ließen sich nicht ansehen. 46 Aufrufe für nichts.
Seither: Datei-Kopie, und die Mails als JSON daneben, weil sie nur im Speicher
entstehen.

**Einzelläufe sind keine Messung.** Zwei Läufe, dieselben Daten, dasselbe
Modell, zwei Minuten Abstand: erst 10 Einstiege mit einem Durchkommer, dann 9
ohne. Jede Aussage über die Kette braucht mehrere Läufe oder mehr Anker.

**Ein Trockenlauf muss in jedem Sinn trocken sein.** Der erste schrieb in die
Produktivdatenbank — nicht durch eigenes Zutun, sondern weil `baue_fall()` die
Finanzierungsrate übers Netz holt und jeder externe Aufruf seinen
Gesundheitsstand bucht. **Wer „kein Schreiben" sagt, muss auch „kein Netz"
sagen.**

**Eine Prüfung, die Fehler meldet, wo keine sind, wird weggelassen.** Die
Prüfung „schreibt nichts in die Produktivdatei" verglich die **Bytes** und
schlug an, obwohl keine Zeile geschrieben wurde: SQLite ordnet beim Öffnen
Seiten um. Jetzt vergleicht sie den **Inhalt aller Tabellen**.

**Der Drift-Wächter des Exports hat die Exportarbeit selbst erledigt.** Gegen
die Datenbank des Stufe-C-Laufs gehalten, nannte er exakt die zwei Tabellen und
acht Spalten, die fehlten — dieselbe Liste, die Kapitel 14 des Umbauplans von
Hand aufgestellt hatte. **Ein Wächter, der auf die eigenen Lücken zeigt, ist
mehr wert als eine Liste, die jemand pflegen muss.**

### Zwei Fallen beim Schreiben von Prüfskripten

**`open(ziel,"w").write(... open(quelle).read())` kürzt das Ziel, bevor das
Argument ausgewertet wird.** Wirft das Argument, ist die Datei leer. So gingen
am 13.08. 1.085 Zeilen Umbauplan verloren (aus dem letzten Commit
wiederhergestellt). **Erst lesen, dann prüfen, zuletzt schreiben** — und eine
Längenprüfung davor.

**`skript.py 2>&1 | tail -2 && git push` prüft die Pipe, nicht das Skript.**
`tail` liefert immer Exitcode 0. Dreimal am selben Tag passiert; zweimal wurde
mit roter Prüfung gepusht, einmal mit einer Prüfdatei, die nicht mehr parste.
**Der Exitcode gehört in eine eigene Variable, bevor irgendetwas committet
wird.**


# 2.21 Werkzeugkasten-Nachtrag (2026-08-15): die Suche nach freien Namen

Ergänzt 2.13 um ein Werkzeug, das aus einem Schaden entstanden ist.

| Skript | Frage | Auslöser |
|---|---|---|
| `finde_freie_namen.py` | **Greift eine Funktion auf einen Namen zu, den sie nicht kennt?** Liest den Syntaxbaum von `agent/`, `scheduler/`, `database/` und `ui/` und vergleicht je Funktion die benutzten gegen die gebundenen Namen. Kein Ausführen, keine Abhängigkeiten. | nach jedem Umbau, der eine Funktion aufteilt oder eine Variable verschiebt — und vor jedem Produktivgang |

**Warum es das gibt.** Dieselbe Falle schlug an zwei Tagen dreimal zu: jedes
Mal eine Variable aus `fuehre_lauf` oder `_ein_asset`, benutzt in einer
Funktion, die sie nicht sieht — und jedes Mal vom breiten Fehlerfang
geschluckt.

| | Name | Wirkung |
|---|---|---|
| 14.08. | `VK` | jedes Symbol lief in den Fehlerzweig |
| 15.08. | `_wl` | vor dem Betrieb gefunden |
| 15.08. | **`assetklasse`** | **zwei Vormittage ohne eine einzige Nein-Zeile** |

Der dritte war der teuerste, weil er nichts umbrachte, sondern schwieg. Der
Beweis steht in den Daten: **809 Nein-Zeilen bis 14.08. 17:55, danach keine.**
Damit fehlte genau der Arm der Messung, der sagen soll, ob das NEIN des
Modells besser ist als der Zufall — und im Log stand kein Wort davon, weil der
Fehler nur in `ergebnis["nein_fehler"]` landete und das niemand las.

**Bei der Einführung fand das Werkzeug zwei weitere schlafende Fehler:**

- `json` war in `scheduler/background.py` nirgends importiert. Nie aufgefallen,
  weil der Kanarienvogel einen Mistral-Client braucht und Mistral seit dem
  07.08. nicht mehr läuft — die Zeile davor kehrt vorher zurück.
- `ui/app.py` rief `ist_hedge_instrument()` ohne Import. Ein NameError beim
  Anlegen eines ETF-Assets.

Dazu fünf Zeilen toter Code in `agent/krypto/regime.py`, hinter einem `return`
und auf zwei nie definierte Namen gestützt — harmlos, aber er verdeckt die
echten Funde.

**Als Dauerprüfung** liegt dieselbe Logik in `pruefe_pakete.py` (Paket T4b) und
verlangt null Kandidaten. Sie brauchte selbst zwei Anläufe: die erste Fassung
benutzte `os` ohne Import — derselbe Fehler, den sie sucht.

> **Diese Klasse Fehler gehört nicht in einen Testlauf, sondern in eine
> statische Prüfung.** Ein Trockenlauf findet sie nur, wenn er genau den Zweig
> trifft, und der breite Fehlerfang macht sie dort unsichtbar. Das ist
> „Fail-soft ist fail-silent" in seiner teuersten Form: nicht ein Ausfall, den
> man sieht, sondern eine Messung, die stillschweigend nicht stattfindet.

# 2.22 Werkzeugkasten-Nachtrag (2026-08-15): der Anlassfilter, vor der Entscheidung gemessen

| Skript | Frage | Auslöser |
|---|---|---|
| `messe_anlass.py` | **Wie oft hätte der Anlassfilter gegriffen?** Liest `anlass_beobachtung` und zählt je Instrument, wie oft der Faktensatz wörtlich derselbe war wie beim letzten Urteil innerhalb von 24 Stunden — getrennt nach `voll` (mit Lagebild) und `asset` (ohne) — **und je Block**, damit sichtbar wird, WORAN eine Frage neu wurde. | ein paar Tage nach jedem Produktivgang, **bevor** über eine Sperre entschieden wird |

**Warum eine Messvariante und nicht gleich die Sperre.** Nutzervorgabe:
*„erstmal soviele Daten wie möglich zulassen und später selektiv
einschränken."* `agent/anlass.py` schreibt mit, wie oft es gegriffen **hätte** —
gesperrt wird nichts. Erst wenn die Zahl bekannt ist, lässt sich entscheiden,
und zwar mit bekannter Wirkung statt geschätzter.

> **Die Prüfung, dass sie nichts sperrt, muss statisch sein.** Mein erster
> Anlauf verglich zwei Trockenläufe — die Stufe läuft dort aber gar nicht, weil
> sie in die Datenbank schreibt. Der Vergleich zeigte, dass die
> *abgeschaltete* Stufe nichts tut. Belastbar ist nur: der Befund steht in
> `rollen_lauf.py` in keiner einzigen Bedingung (Paket T4c).

# 2.23 Werkzeugkasten-Nachtrag (2026-08-16): Phase I an ECHTEN Reihen prüfen

| Skript | Frage | Auslöser |
|---|---|---|
| `pruefe_phase1.py` | **Greifen die vier Ergänzungen bei UNSEREN Assets?** Rendert den Faktensatz für jedes Symbol der Watchlist und prüft vier Abgrenzungen: Liquidationsabstand nur bei Hebel · Finanzierung in keinem Spot-Satz · Lücken-Satz genau dort, wo die Reihe ihn hergibt · Sektorbezug nur bei Themen-ETF, nicht bei den Absicherungen. Ohne Netz, nur lesend. | nach jeder Änderung an `lagebeschreibung.py` oder an der Verdrahtung in `rollen_eingabe.py` |

**Warum es dieses Skript zusätzlich zu `pruefe_pakete.py` gibt.** Die
Paketprüfungen laufen auf konstruierten Kerzen — sie sagen, ob die Logik
stimmt, nicht ob sie greift. Genau dieser Unterschied hat am 16.08.
zugeschlagen: die Abgrenzung des Sektorbezugs stand auf `assetklasse == "etf"`,
der Aufrufer übergibt aber die **Gruppe** (`themen_etf`). Alle Unit-Prüfungen
grün, im Betrieb hätte sie nie gegriffen. **Im gerenderten Faktensatz fehlte
der Satz sofort sichtbar.**

> ⚠️ **Zwei Lehren über das Aufsetzen dieser Prüfung selbst — beide meine
> eigenen Fehler, beide an den Testdaten und nicht am Code:**
>
> **Ein Sollwert aus fremder Datenlage ist kein Sollwert.** Die erste Fassung
> prüfte gegen die feste Liste unvollständiger Assets aus der Bestandserhebung.
> Die ist an der Notebook-Datenbank erhoben; auf dem Entwicklungsrechner fehlen
> sechs dieser Reihen ganz. Die Prüfung meldete einen Fehler, den es nicht gab
> — und hätte drei echte Funde als „zuviel" verworfen. Geprüft wird jetzt gegen
> die **Reihe selbst**, unabhängig nachgerechnet.
>
> **Degenerierte Testdaten erzeugen echte Fehlalarme.** Der Gegenfall („ein
> vollständiges Asset bekommt keinen Lücken-Satz") lief auf einer streng
> steigenden Reihe. Die hat keine Wendepunkte, also findet `_niveaus()` keine
> Marke — und der Lücken-Block meldete das völlig zu Recht. Der Test brauchte
> eine schwingende Reihe.

**Neu gefunden, weil das Skript an echten Reihen läuft:** CAT (weniger als zwei
Marken — dieselbe kaputte Kursreihe wie am 06.08.), HYPE (167 Handelstage), MON
(232). Keines davon stand in der Bestandserhebung; alle drei sagen es jetzt
selbst im Faktensatz.

# 2.24 Werkzeugkasten-Nachtrag (2026-08-16): die Kette von Anfang bis Ende

| Skript | Frage | Ausloeser |
|---|---|---|
| `simuliere_kette.py` | **Laeuft die Abrufkette durch, und kommen die Saetze am Ende an?** Betriebsart `probe` gegen eine KOPIE der Datenbank, echte Reihen/Fakten/Rechnung/Schreiben/Mailaufbau, Attrappe nur fuer die drei Modellaufrufe. Spielt je Instrument JEDE Aktion des Vokabulars durch. | nach jeder Aenderung an der Rollen-Kette, **vor** jedem Produktivgang |

**Warum zusaetzlich zu den 855 Paketpruefungen.** Die sind statisch und pruefen
Teile. An einem einzigen Tag haben sie viermal etwas nicht gefunden, das beim
Durchlaufen sofort sichtbar war - zuletzt, dass **Rolle G nie gelaufen ist**:
`urteil.get("symbol")` war immer leer, die Funktion kehrte in der zweiten Zeile
zurueck, ohne Fehler und ohne Logzeile.

> **Eine Kette, die in jedem Einzelteil stimmt, kann als Ganzes reissen.**

**Was das Skript prueft, was ein Trockenlauf nicht kann.** `trocken`
ueberspringt genau die Stufen, um die es geht: es schreibt nicht, misst den
Anlass nicht und ruft Rolle G nicht. Deshalb `probe` - und deshalb gegen eine
Kopie, weil die Kette dann wirklich schreibt.

> ⚠️ **Die Abdeckungsliste ist wichtiger als die Fehlerzahl.** Der erste
> Durchgang meldete "0 Fehler" und hatte den Hebel nie beruehrt: seit dem 15.08.
> ist `hebel_pruefung_erlaubt` standardmaessig falsch, also fielen alle
> Hebel-Symbole an der Auftragsstufe heraus - **77 % der Produktionsaufrufe,
> ungeprueft, gemeldet als gruen**. Das Skript schaltet den Schalter jetzt in
> der Kopie ein und druckt aus, welche Koerbe es NICHT geprueft hat.

**Der Satz, der daraus folgt:** eine Stufe gilt erst als gebaut, wenn
`simuliere_kette.py` sie **in der fertigen Mail** nachweist.

**NACHTRAG 16.08. abends: gegen das NB-BACKUP laufen lassen, nicht gegen den Entwicklungsbestand.**

```bash
python simuliere_kette.py --db <entpacktes NB-Backup>
```

Im Entwicklungsbestand fehlen sechs Kursreihen - **Rohstoffe, 3QSS und X136**. Genau die Gruppen mit der duennsten Datenlage wurden deshalb uebersprungen, und der Lauf meldete trotzdem „0 Fehler“.

> ⚠️ **Die Simulation datiert die Signale in der KOPIE um 30 Tage zurueck.** Ohne das sperrt der echte Cooldown des Produktionsstands jedes Symbol - der Test bestaetigt dann, dass der Cooldown funktioniert, und sagt nichts ueber die Kette. Gemessen: hedge und themen_etf kamen mit **0 Modellaufrufen** durch.

Das Backup liegt bei jedem Export in `Claude_Austauschordner/DB_Backups/` und muss nicht angefordert werden.

## 2.25 Rechnet unser Prompt dem Modell etwas vor? (neu 2026-08-16)

**Auslöser:** neuer Parameter für eine Rolle, oder eine geänderte Formulierung
in `marktlage.py`, `lagebeschreibung.py`, `positionierung.py`.

```bash
python pruefe_zahlen_in_prompts.py --db <NB-Backup>
```

**Sucht drei Formen, die ein Blick in den Quelltext nicht sieht:**

| | | |
|---|---|---|
| **N1** | Rechenaufgabe | zwei Werte UND ihr Abstand im selben Satz (R-T10) |
| **N2** | ungedeckte Zahl | keine Bezugsgröße, kein Fenster (R-T1/R-T5) |
| **N3** | ohne Einordnung | Perzentil ohne Wort, ob das viel ist (R-T11) |

**Es rendert aus echten Daten** — Rolle A aus `lagebilder.fakten_json`, also dem
Produktionswortlaut selbst, BC und G aus den Bausteinen. Ein f-String im Code
sagt nichts darüber, was am Ende dasteht; genau daran ist der Sektor-Bezug am
16.08. vorbeigelaufen.

> **Der Selbsttest läuft immer mit** (`--selbsttest` allein, oder automatisch
> vor jedem Scan). Er enthält beide Fehlalarme des ersten Laufs als Gegenprobe:
> ein Tageszähler gegen ein Prozent, und die Ziffer in „3QSS". Schlägt er fehl,
> ist der Befund darunter nicht belastbar — und das Skript sagt es.

**Nicht verwechseln mit `pruefe_fakten_bezugsgroessen.py`** (2.x, vom 09.08.):
das prüft dieselbe Frage auf **JSON-Feldern** der alten Pipelines. Ein Satz ist
kein Feld — drei Zahlen mit je tadellosem Bezug können zusammen eine
Rechenaufgabe sein.

## 2.26 Externe Reihen: der Job schreibt, die Rolle liest (neu 2026-08-16)

**Auslöser:** eine neue Fremdquelle für Rolle G.

`zweite_meinung.rolle_g` öffnet die Datenbank mit `mode=ro` und **kann nicht
schreiben**. Jede Fremdquelle braucht deshalb zwei Teile:

| | |
|---|---|
| **schreiben** | `scheduler/background.py::externe_reihen_job`, täglich vor den Signalläufen |
| **lesen** | `positionierung.py::_gepflegte_reihe` — Datenbank, dann Prozessspeicher, dann Netz |

**Zu prüfen ist beides getrennt.** Eine Prüfung, die nur das Lesen abdeckt,
bleibt grün, während die Tabelle leer bleibt und jedes Urteil am Netz hängt.

```bash
python pruefe_pakete.py        # Reihenfolge, Revision, Netzentkopplung, fail-closed
```

> **Die Netzentkopplung ist die wichtigste der vier:** mit gefüllter Tabelle
> darf `lage()` **null** Abrufe machen. Sonst fällt der Fakt mit dem Anbieter
> aus — und ein Signal ohne Gegenprüfung sieht aus wie eines, das sie bestanden
> hat.

**Und die Testeingabe muss den Fall herstellen.** `COT_MINDESTREIHE = 60`: ein
Testbestand mit 48 Punkten lässt drei Prüfungen fehlschlagen, ohne dass am Code
etwas falsch wäre.

## 2.27 Eine gedrosselte Schnittstelle ist kein leeres Ergebnis (neu 2026-08-16)

**Auslöser:** eine neue Quelle, die MEHRERE Anfragen je Symbol braucht.

Am 16.08. hat ein Messlauf die SEC mit rund 30 Anfragen je Sekunde bedient —
Limit sind zehn. Die Antwort war ein `429`, über eine Viertelstunde lang, ohne
`Retry-After`.

> ⚠️ **Der Schaden wäre still gewesen.** Der Abruf fängt jeden Filing-Fehler
> einzeln ab; bei einer Sperre scheitern alle, und die Funktion gibt eine leere
> Liste zurück — ununterscheidbar von „dieses Unternehmen hat keine
> Insider-Aktivität". Der gesperrte Abruf hätte als Tatsache im Prompt
> gestanden.

**Drei Punkte, bei jeder mehrstufigen Quelle zu prüfen:**

| | |
|---|---|
| **Takt** | ein prozessweiter Begrenzer unter dem Anbieterlimit |
| **eigene Fehlerklasse** | eine Drosselung ist kein „keine Daten" — sonst kann kein Aufrufer den Unterschied sehen |
| **Schreibverhalten** | bei Sperre wird **nichts** geschrieben; der gestrige Stand ist ehrlicher als eine frisch datierte Null |

**Und der Modulkopf ist keine Zusage.** In `sec_edgar.py` stand fast einen Monat
*„bei unserem Nutzungsmuster nie annähernd erreicht, daher kein eigener
Rate-Limiter nötig"*. Das galt für fünf Filings. **Die Annahme galt für eine
Nutzung, nicht für die Schnittstelle.**

## 2.28 Neue Quellen gehören ins Remote-Monitoring (neu 2026-08-16)

**Nutzervorgabe:** *„vergiss auch nicht für alle Neuanbindungen … diese auch in
das Monitoring auf der Remoteseite zu berücksichtigen."*

| | |
|---|---|
| **API-Gesundheit** | `@track_api_health("…")` an jeder Abruffunktion — landet automatisch in `api_health_status` und im Export |
| **Aktualität** | `extract_notebook_diagnose._externe_reihen` — Abdeckung je Assetgruppe, Veraltungsliste, **Alter des ABRUFS** |

**Das Alter des Abrufs, nicht das des jüngsten Punktes.** Ein COT-Bericht ist
zwischen zwei Freitagen sieben Tage alt, ohne dass etwas fehlt.

> Der Export meldet unbekannte Tabellen selbst unter `nicht_erwaehnt` — wer eine
> neue Tabelle anlegt und den Abschnitt vergisst, sieht es beim nächsten Export.

## 2.29 Ein Schalter des Nutzers fällt ZU, nicht auf (neu 2026-08-16)

**Auslöser:** jede Stelle, die eine ausdrückliche Nutzerentscheidung liest.

```python
        try:
            if not db.get_hebel_pruefung_erlaubt(conn, sym):
                return False, "abgeschaltet"
        except Exception:
            logger.debug(...)      # ⚠️ und dann ging es WEITER
```

Ohne `conn.row_factory = sqlite3.Row` wirft der Leser, der Fang schluckt es auf
**debug**, und ein **abgeschaltetes** Asset wird trotzdem beurteilt.

| | zu prüfen |
|---|---|
| **Richtung** | ein Lesefehler darf nie „erlaubt" bedeuten |
| **Lautstärke** | `warning`, nicht `debug` — auf debug erscheint nichts in einem Log |
| **Testverbindung** | mit Zeilenfabrik, wie `db.get_connection()` sie setzt |

> Dieselbe Klasse wie die Regime-Dauer, und in der Wirkung schlimmer: dort
> fehlte ein Halbsatz, hier wird eine ausdrückliche Entscheidung übergangen.

## 2.30 Der Trockenlauf muss dieselben Stufen sehen (neu 2026-08-16, O-38)

Ein Trockenlauf, der Stufen überspringt, **überschätzt den Durchsatz** — und
zwar rückwirkend auch in jeder Messung, die mit ihm gemacht wurde.

| Stufe | Umgang |
|---|---|
| **reine Leser** (Nutzerschalter) | laufen immer — es gab nie einen Grund, sie auszunehmen |
| **schreibende Stufen** (Anlass) | laufen mit `schreiben=False` |

> **Ein Trockenlauf, der schreibt, verändert die Grundlage des nächsten
> scharfen Laufs.** Das Urteil braucht den Schreibvorgang nicht: Fingerabdruck
> rechnen, Vergleich lesen, Zeile weglassen.

**Grössenordnung:** die Anlass-Stufe stoppte am 16.08. **35 von 41**
Kryptosymbolen. Ein Trockenlauf ohne sie meldet eine Zahl, die es im Betrieb
nicht gibt.

## 2.31 Eine Prüfung darf nicht am Kalender hängen (neu 2026-08-17)

```python
    is_history_stale("2026-08-14", schwelle_tage=1)
    is not is_history_stale("2026-08-14")
```

Am 16.08. war der 14.08. **zwei** Tage zurück und der Unterschied zwischen den
Schwellen bestand. Einen Tag später sind es **drei**, beide schlagen an, und die
Prüfung scheiterte — **ohne dass sich am Code etwas geändert hätte.**

| | |
|---|---|
| **Falsch** | ein festes Datum, das zufällig heute den Fall herstellt |
| **Richtig** | relativ zu `date.today()` rechnen |
| **Und** | beide Seiten einzeln prüfen (`is True` / `is False`), nicht nur auf Ungleichheit |

> Eine Prüfung auf „die beiden Ergebnisse sind verschieden" ist auch dann grün,
> wenn beide aus dem falschen Grund verschieden sind — und rot, wenn beide aus
> dem richtigen Grund gleich sind.

## 2.32 Die Zuordnungsmatrix als ausführbarer Test (neu 2026-08-17)

**Auslöser:** ein neuer Parameter für eine Rolle, oder eine geänderte
Zuordnung je Assetklasse/Handelsform.

```bash
python pruefe_prompt_matrix.py --db <NB-Backup>
```

**Es ist das vierte Prüfwerkzeug und deckt als einziges die ZUORDNUNG ab:**

| Werkzeug | prüft |
|---|---|
| `pruefe_pakete.py` | Einzelteile |
| `simuliere_kette.py` | den Durchlauf |
| `pruefe_zahlen_in_prompts.py` | die **Form** der Sätze |
| **`pruefe_prompt_matrix.py`** | die **Zuordnung** — Rolle × Assetklasse × Handelsform |

**Kapitel 66 des Umbauplans steht dort als Code.** Ändert sich die Matrix, ist
dieses Skript mitzuziehen — sonst prüft es einen Stand, den es nicht mehr gibt.

> ⚠️ **`JOBABHAENGIG` unterscheidet fehlende Rohdaten von fehlender
> Verdrahtung.** Ein Backup, das älter ist als der Job, hat keine
> Fundamentaldaten — und dann fehlt der Satz **zu Recht**. Ohne diese
> Unterscheidung meldete der erste Lauf drei Lücken, die keine waren.
>
> **Ein Prüfer, der eine korrekte Auslassung als Fehler meldet, wird nach dem
> dritten Mal ignoriert.**

**Der Musterfall, den es abdeckt:** `krypto/hebel` zeigt in Rolle G **kein**
Funding — das ist die Vorschrift (R-R2 je Instrument), nicht ein Defekt. Ohne
dieses Werkzeug hält das jeder für einen Fehler.

## 2.33 Funktioniert es auch bei einem NEUEN Wert? (neu 2026-08-17)

**Nutzerfrage:** *„ist dies nur für den Bestand implementiert oder funktioniert
das auch bei neuen Werten? Sonst bekommen wir einen Schiefstand, wenn
gehandelt wird."*

**Zwei Klassen, und nur eine ist gefährlich:**

| | Klasse | woran erkennbar |
|---|---|---|
| ✓ | **von selbst** | leitet sich aus der Watchlist oder aus einer Tabelle ab, die je Symbol gefüllt wird |
| ⚠️ | **nur mit Eintrag** | eine von Hand gepflegte Zuordnung im Code entscheidet |

**Heute handgepflegt:** `SYMBOL_ZU_COT_ROHSTOFF` (COT + ETF-Bestand) und
`SYMBOL_ZU_HEBEL_FAKTOR` (Hebelfaktor, inzwischen aus `config.yaml` speisbar).

> ⚠️ **Fehlt der Eintrag, fällt der Parameter STILL aus** — kein Fehler, keine
> Logzeile, nur ein Satz weniger. Ein neuer Rohstoff wäre in Rolle G völlig
> blind, und niemand sähe es, weil dieselbe Rolle bei den bestehenden liefert.

```bash
python pruefe_prompt_matrix.py --db <NB-Backup>
```

Der Abschnitt **„NEUE WERTE"** vergleicht jede Handzuordnung mit der Watchlist
und meldet jedes Symbol, das fehlt. **Wer einen Wert aufnimmt, sieht es beim
nächsten Prüflauf** — statt es Wochen später an einer stillen Lücke zu merken.

**Beim Anlegen einer neuen Handzuordnung ist `HANDPFLEGE` mitzuziehen**, sonst
prüft der Abschnitt eine Liste, die nicht mehr vollständig ist.

## 2.34 Steht eine Reihe still? (neu 2026-08-17)

**Der teuerste Fehlertyp dieses Projekts hat heute seine reinste Form
gezeigt:** drei von vier Nicht-Kurs-Aussagen der Rolle A standen seit fünf
Tagen still, und **nichts fiel aus**. `marktlage.beschreibe_makro` nimmt den
jüngsten Wert ≤ Ankertag ohne Altersgrenze — der Satz entsteht weiter, nur mit
immer älteren Zahlen.

> **Ein fehlender Satz fällt auf. Ein alter sieht aus wie ein frischer.**

### Die zwei Alter

| | misst | hängt an | als Fehler gewertet |
|---|---|---|---|
| **Datenstand** | wie alt die Information ist | dem Anbieter | nein, nur berichtet |
| **Abrufstand** | wann wir zuletzt nachgesehen haben | **uns** | **ja, ab 2 Tagen** |

Ein Anbieter, der nichts Neues hat, ist normal. Ein Job, der nicht läuft, ist
es nie.

### Werkzeug

```bash
python pruefe_pakete.py --paket Frische
```

Registratur und Schwellen stehen in `agent/datenfrische.py` — **an einer
Stelle**, weil zwei Definitionen desselben Begriffs in diesem Projekt schon
einmal auseinandergelaufen sind (Umbauplan 70.4). Im Betrieb loggt der
`lagebild_reihen_job` jede veraltete Quelle täglich; im NB-Export steht der
Abschnitt `datenfrische`.

> ⚠️ **Neue Quelle = neue Zeile in der Registratur.** Fehlt sie, wird die
> Quelle **still nicht überwacht** — dieselbe Falle wie bei
> `SYMBOL_ZU_COT_ROHSTOFF`. `paket_frische` hält die Registratur deshalb gegen
> `mindestkriterien.QUELLEN_G`.

### 2.34b Eine Datenbankkopie ist nicht drei Dateien

`simuliere_kette.py` kopierte `.db`, `-wal` und `-shm` einzeln in ein immer
gleiches Ziel. Blieb dort ein WAL aus einem früheren Lauf liegen, passten
Hauptdatei und Beileger nicht mehr zusammen — `database disk image is
malformed`. **Das war der freundliche Ausgang: ein noch lesbares WAL hätte die
Kette gegen einen alten Stand laufen lassen, ohne Fehler.**

**Regel: eine Datenbank wird über `Connection.backup()` kopiert, nie über das
Dateisystem** — gefolgt von `PRAGMA integrity_check` auf der Kopie. Der
NB-Export (`_db_backup`) macht es seit jeher so; die Simulation seit heute.

## 2.35 Eine Schwelle beantwortet eine Frage - nicht zwei (neu 2026-08-17)

**Der Fall.** `NIVEAU_MIN_ABSTAND_ATR = 0,5` beantwortet: *„ab wann lohnt es,
eine Marke zu ERWAEHNEN?"* Ich habe dieselbe Schwelle benutzt fuer:
*„ab wann muss mein ZIEL davor enden?"*

**Ergebnis: 44 von 44 Symbolen gedeckelt, 98 % unter CRV 0,5, Median 0,21.**

> **Die Konstante war nicht falsch. Die zweite Frage war es.**

**Woran man es erkennt:** eine Konstante, die fuer einen neuen Zweck
uebernommen wird, ohne dass jemand die Verteilung fuer DIESEN Zweck misst.
Der Kommentar an der Konstante beschrieb ausdruecklich den alten Zweck
(„naeher als das ist keine eigene Marke") - er haette gereicht.

**Die Pruefung, die es gefunden haette** - und die vor jedem solchen Umbau
gehoert:

```
Wie oft greift die neue Regel ueber ALLE Symbole?
   greift sie bei 100 %, ist sie kein Filter, sondern eine Setzung.
   greift sie bei 2 %, ist sie kein Filter, sondern Dekoration.
```

Beides ist ein Befund, und beides sieht man erst nach der Zaehlung. Der
Nutzer hat sie eingefordert (*„bitte vorher pruefen, um hier nicht einen
Deckel ueber ein Asset zu legen bzw. der Fehler liegt an anderer Stelle"*) -
und der Fehler lag an anderer Stelle.

## 2.36 Ein Kriterium veraltet mit dem System (neu 2026-08-17)

**Drei Pruefungen haben an einem Tag denselben Fehler gezeigt:** sie
beschrieben einen Zustand, den es nicht mehr gibt.

| Pruefung | stand da | warum es fiel |
|---|---|---|
| `pruefe_prompt_matrix` | zaehlte alle Bloecke | `_marken_werte` kam dazu und ist kein Satzblock |
| `pruefe_pakete` (G5) | suchte den QUELLTEXT der Schranke | die Schranke wurde ersetzt |
| `simuliere_kette` | `gruppe != "krypto"` = keine Grundlage | Aktien haben seit dem 16.08. eine |

**Die Regel dahinter:** ein Kriterium, das eine Gruppe, einen Namen oder eine
Codezeile nennt, veraltet mit dem System. Eines, das die **Bedingung** fragt,
nicht.

```
schlecht   if gruppe != "krypto":            # eine Aufzaehlung
gut        if not _hat_eigene_grundlage(...) # die Bedingung selbst
```

> **Und: eine Einstellung ist keine Luecke.** Dass Rolle G bei zwei Symbolen
> auf BTC-weiter Grundlage urteilt, ist gemeldet und nicht gesperrt - eine
> Entscheidung des Nutzers. Sie als Fehler zu zaehlen faerbt jeden Lauf rot
> und traegt dem Auge bei, Befunde zu ueberlesen. Die Simulation fuehrt sie
> deshalb unter "BEKANNTE ZUSTAENDE".


## 2.37 Eine Prüfregel, die nie anschlägt, beweist nichts (neu 2026-08-17)

**Die Prüfung war selbst der Fehler.** Beim Vereinheitlichen der
Zahlenschreibweise sollte diese Regel englische Dezimalpunkte finden:

```python
re.findall(r"(?<!\d\.)\b\d+\.\d\b", text)     # erste Fassung
```

| Eingabe | gefunden |
|---|---|
| `2.5 x ATR` | ✓ |
| `3.81 bis 3,85` | **✗** — das `\b` scheitert an der zweiten Ziffer |

**Der erste Lauf über alle Mails meldete „0 Lücken".** Erst die gehärtete
Regel fand sieben — in jeder Gruppe.

> **Sie meldete sauber, wo es nicht sauber war.** Eine Prüfung, deren
> Negativfall nie erprobt wurde, ist kein Nachweis, sondern eine Behauptung
> mit grünem Häkchen.

### Die Pflicht daraus

**Jede neue Prüfregel wird in BEIDEN Richtungen erprobt**, und beide Proben
stehen als eigene Prüfungen daneben:

```python
pruefe(P, "der Tausenderpunkt gilt NICHT als englische Schreibweise",
       not _englische_zahlen("1.234,5 EUR und 1.234.567,8 EUR"))
pruefe(P, "und mehrstellige Nachkommastellen werden gefunden",
       _englische_zahlen("3.81 bis 3,85") == ["3.81"])
```

Dasselbe gilt für Wächter: `paket_ausfall` prüft nicht nur, **dass** drei
Fehler in Folge abbrechen, sondern auch, dass **zwei es nicht tun** und ein
Erfolg dazwischen zurücksetzt.

**Und die Regel lebt an EINER Stelle.** `pruefe_pakete.py` importiert
`_englische_zahlen` aus `simuliere_kette.py` — zwei Messungen, die verschieden
zählen, sind schlimmer als eine.

---

## 2.38 Am Produkt prüfen, nicht am Beispiel (neu 2026-08-17)

**Nutzervorgabe:** *„für alle eMail prüfen bitte"* — und genau darin lag der
Unterschied.

| | prüft | fand |
|---|---|---|
| `pruefe_pakete.py` | **eine** Beispielrechnung | nichts |
| `simuliere_kette.py` | die **echten** Mails aller Gruppen | sofort einen Fehler in **jeder** Gruppe |

Der Fund war eine rohe Python-Liste mitten in einer deutschen Mail:

```
Z-1: 2 Zahl(en) stehen nicht in der Eingabe: [42.0, 17.0]
```

Eckige Klammern, englische Punkte, und ein `.0`, das eine Genauigkeit
vortäuscht, die das Modell nie hatte.

> **Ein Beispiel beweist, dass etwas funktionieren KANN.** Ob es im Produkt
> funktioniert, beweist nur das Produkt. Wo eine Aussage über *alle* Mails
> gilt, gehört die Prüfung in `simuliere_kette.py`, nicht in eine
> Beispielrechnung.

### Was dort jetzt über jede Mail läuft

* keine Zahl in englischer Schreibweise
* die sechs Handelsparameter (Einstiegszone, Stop, Take-Profit/TP,
  Haltedauer, Betrag, Hebel) tragen den Fett-Schwarz-Griff — geprüft am
  **gerenderten HTML**, nicht an der Formatregel: dazwischen liegt die
  Reihenfolge der Regeln

**Nicht abgedeckt:** Rohstoffe und Absicherung — die Simulation überspringt
sie mangels Kursreihe im Bestand.

---

## 2.39 Fail-soft ist fail-silent — zum dritten Mal (neu 2026-08-17)

**Gefunden beim Nachweis gegen einen toten Anbieter**, nicht durch eine
Prüfung: `agent/zweite_meinung.py` setzte seit jeher ein Feld

```python
aus["uebersprungen"] = str(e)
```

**das nirgends gelesen wurde.** `zeilen()` lieferte nur bei gesetztem
`einwand` etwas — bei Andrang, Ausfall **und** Fehlschlag fehlte der Abschnitt
ersatzlos.

> **Eine ausgefallene Gegenprüfung sah aus wie eine, die es zu diesem Wert gar
> nicht gibt.** Ein Signal ohne Gegenprüfungszeilen war vom Leser nicht von
> einem zu unterscheiden, das die Prüfung bestanden hat.

### Die Prüffrage

Ein gesetztes Feld ist **kein** Nachweis. Zu jedem „wir merken uns das"
gehört die Gegenfrage: **wer liest es, und was passiert, wenn niemand es
tut?**

```bash
grep -rn 'get("feldname")' --include=*.py .    # gibt es einen Leser?
```

Fand sich keiner, ist das Feld entweder überflüssig oder ein stiller
Ausfall — beides ein Befund.

### Und die Darstellung trägt die Unterscheidung mit

Drei Lagen, drei Sätze: *zu viele Signale* · *nicht erreichbar* · *hat nicht
geantwortet*. Alle mit `●` (grau), nicht `▼` (rot):

> **Ein Ausfall unserer Technik ist kein Befund über den Handel.** Ihn rot zu
> setzen hieße, dem Leser eine Warnung über sein Geschäft zu geben, wo eine
> über unser Werkzeug gemeint ist.

## 2.40 Eine Pruefung, die den eigenen Leser nicht kennt (neu 2026-08-18)

`_quelltext()` entfernt Kommentarzeilen - richtig, weil dieses Projekt
Entferntes ausfuehrlich im Kommentar festhaelt und ein `grep` die geloeschte
Zeile sonst in ihrer eigenen Grabinschrift wiederfindet.

**Genau deshalb kann er einen Geltungsvermerk nicht sehen.** Die erste
Fassung von `paket_dimension` suchte den Vermerk
*"GILT NUR FUER DIE ALTEN PIPELINES"* in `config.yaml` ueber `_quelltext`
und schlug fehl - obwohl der Vermerk dastand.

> **Regel: wer Kommentare oder Dokumentation prueft, liest ROH.**
> `_quelltext` ist fuer aktiven Code da. Ein Vermerk ist kein Code.

---

## 2.41 `_quelltext` entfernt Kommentare - keine Docstrings (neu 2026-08-18)

Methodik 2.40 hielt fest: **wer Dokumentation prueft, liest roh.** Einen Tag
spaeter dieselbe Klasse in der Gegenrichtung.

Eine Pruefung sollte sicherstellen, dass die Kette `rechne(widerstand=...)`
NICHT fuellt - sonst waere der verworfene Widerstandsdeckel wieder scharf.
Sie suchte `"widerstand="` im Quelltext und schlug fehl. Gefunden hatte sie
**ihren eigenen Warnhinweis im Docstring** der Funktion, die den Weg
vermeidet.

> `_quelltext` entfernt Zeilen, die mit `#` beginnen. **Ein Docstring ist
> kein Kommentar.** In einem Projekt, das Verworfenes ausfuehrlich
> beschreibt, steht der gesuchte Text deshalb regelmaessig in seiner eigenen
> Grabinschrift - nur eine Etage tiefer als am 12.08.

### Die Regel

**Wer prueft, ob ein Aufruf ein Schluesselwort uebergibt, prueft am
Syntaxbaum, nicht am Text:**

```python
baum = ast.parse(io.open(pfad, encoding="utf-8").read())
treffer = [k for n in ast.walk(baum) if isinstance(n, ast.Call)
           for k in (n.keywords or []) if k.arg == "widerstand"]
```

Textsuche bleibt richtig fuer Konstanten und Vermerke. Fuer **Aufrufe** ist
sie zu grob - sie kann Beschreibung nicht von Ausfuehrung unterscheiden.

---

## 2.42 Ein Abbruch darf nie zu einem Messwert werden (neu 2026-08-19)

**Selbst gebaut, am selben Tag.** Ein Skript fragte 43 Symbole bei CoinGecko
nach Entwicklerdaten und wertete so aus:

```python
dev = d.get("developer_data") or {}      # bei HTTP 429 leer
s = dev.get("stars") or 0                # -> 0
(mit_repo if s else ohne_repo).append(…)  # -> 'kein Repository'
```

Ergebnis: **0 von 43 haben ein Repository** - waehrend BTC zwei Minuten
zuvor 73.168 Sterne gemeldet hatte. Der Lauf war ins Rate-Limit gelaufen,
und **jede Fehlerantwort wurde zu einem Nein**.

> Ein Abbruch sieht in einer Zaehlung genauso aus wie eine Verneinung -
> wenn man ihn laesst. Dieselbe Klasse wie *fail-soft ist fail-silent*, nur
> in einem Pruefskript statt im Produkt.

### Die Regel

**Jede Erhebung ueber eine fremde Quelle braucht DREI Zustaende, und sie
duerfen nie verschmelzen:**

| | |
|---|---|
| **ja** | die Quelle hat geantwortet und sagt ja |
| **nein** | die Quelle hat geantwortet und sagt nein |
| **nicht erfahren** | Netz, 429, unerwartete Form - **keine Auskunft** |

Und die Abdeckungszahl nennt **nur die ersten beiden** als beantwortet.
`messe_entwickleraktivitaet.py` weist die drei getrennt aus und liefert
Rueckgabewert 2, solange der dritte nicht leer ist.

⚠️ **Auch eine 200 ohne das erwartete Feld ist ein Fehler**, keine
Verneinung - es koennte ein Fehlerkoerper mit Status 200 sein.

---


## 2.43 Ein Vergleichsmassstab muss frischer sein als das Geprueffte (20.08.2026)

`lade_historie_nach.py` prueft nachgeladene Kursreihen gegen einen aktuellen
Preis - und nahm ihn zuerst aus `price_cache` der eigenen Datenbank. Vier
Symbole wurden abgelehnt, KAIA mit "30 % Abweichung, das ist ein anderes
Asset".

Der Preis stammte vom 19.07., ueber einen Monat alt: die Produktion laeuft
auf dem Notebook, der Entwicklungsrechner sieht ihre Daten nicht. Dreissig
Prozent in einem Monat sind bei einem Kleinwert normal. Mit einem frisch
geholten Preis betrug die Abweichung derselben Reihe 0,4 %.

REGEL: wer eine Fremdquelle gegen die eigene Datenbank prueft, prueft zwei
Dinge gleichzeitig - die Quelle UND das Alter der eigenen Daten. Der
Massstab muss aus einer Quelle kommen, die mindestens so frisch ist wie das
Geprueffte. Vgl. 2.36 (Datenstand gegen Abrufstand).

ZWEITER FUND IM SELBEN ATEMZUG: die Abfrage hatte kein ORDER BY und nahm
damit eine BELIEBIGE der 31 gespeicherten Zeilen. Eine Abfrage ohne
Sortierung auf einer Tabelle mit Historie ist immer ein Fehler, auch wenn
sie zufaellig oft richtig liegt.

## 2.44 Ein Fund in nachgeladenen Daten ist zuerst verdaechtig (20.08.2026)

Nach dem Nachladen von 28.838 Kerzen zeigte die Driftmessung erstmals einen
signifikanten positiven Wert (250 Tage Rueckblick, 5 Tage Horizont, t=3,20).

DIE PRUEFUNG, DIE DAZUGEHOERT: die nachgeladene Historie enthaelt nur Werte,
die es HEUTE noch gibt - und ein Wert steht auf der Watchlist, WEIL er
einmal gelaufen ist. Seine fruehe Historie enthaelt genau den Anstieg, der
ihn bekannt gemacht hat. Das erzeugt Momentum aus der Auswahl.

Deshalb wird jeder Fund auf zwei Zeitfenster aufgeteilt: die nachgeladene
Zeit (Auswahl wirkt rueckwirkend) und die schon vorhandene (Auswahl wirkt
nicht). Ein Fund, der nur im ersten steht, ist NICHT bestaetigt.

Gemessen: 250/5 lebt in der nachgeladenen Zeit (t=3,21 davor, t=1,57 danach)
- nicht bestaetigt. 250/60 zeigt in beiden dasselbe Vorzeichen und ist im
unbelasteten Teil signifikant.

## 2.45 Schwellen werden nicht nach dem Ergebnis angepasst (20.08.2026)

Der Placebo-Lauf misst die Schwelle, gegen die ein Fund bestehen muss. Auf
733 Terminen ergab er 3,05, auf 2.064 Terminen 2,40 - mit mehr Terminen
werden die Raender zahmer, das ist erwartbar.

Die 3,05 bleibt stehen. Eine Schwelle unmittelbar nach einem positiven Fund
zu SENKEN ist Rosinenpickerei, auch wenn die neue Zahl besser gemessen ist.
Wer sie senken will, muss es VOR dem naechsten Fund tun und begruenden.
Eine Paketpruefung haelt den Wert fest.


## 2.46 Varianten erhoehen die Schwelle, sie umgehen sie nicht (20.08.2026)

messe_drift.py rechnet drei Rangvarianten (roh, ohne_monat, vol_skaliert)
ueber drei Rueckblicke und drei Horizonte - 27 Felder statt 9. Die
Bonferroni-Schwelle steigt damit von 2,77 auf 3,11.

REGEL: jede zusaetzliche Variante ist ein zusaetzlicher Versuch. Wer sie
rechnet, ohne die Schwelle mitzuziehen, kauft sich Signifikanz. Und wer
nachtraeglich eine vierte ergaenzt, weil die dritte nicht passte, hat sich
ein Ergebnis gesucht - die Varianten stehen deshalb als Konstante im Code,
mit dem Vermerk, dass sie vor der ersten Rechnung festgelegt wurden.

## 2.47 Wenn die Gegenprobe nicht moeglich ist, wird sie benannt (20.08.2026)

Punkt 3 des Plans sah vor, einen Fund auf einer zweiten Anlageklasse zu
wiederholen. Das ging nicht: 2 Aktien und 4 ETF in der Watchlist, und unter
zehn Symbolen ist eine Rangliste keine.

FALSCH WAERE GEWESEN, es trotzdem zu rechnen und das Ergebnis zu melden.
Richtig ist: die Luecke benennen und den naechstbesten Ersatz nehmen - hier
die Halbierung der Symbolliste. Ein echter Zusammenhang steht in beiden
Haelften; einer, der an wenigen Werten haengt, nur in einer.

Der Punkt gilt damit als TEILWEISE erledigt, nicht als erledigt.


## 2.48 Ein deutsches Datum ist keine englische Zahl (20.08.2026)

Mit dem Terminkalender (93 D) stand erstmals ein Datum in der Mail:
"FOMC-Sitzung (15.09.-16.09.2026)". simuliere_kette.py meldete daraufhin acht
Luecken - "15.09" und "16.09" sahen fuer die Schreibweisenpruefung aus wie
englische Dezimalschreibweise.

DER FEHLER LAG IN DER PRUEFUNG, NICHT IN DER MAIL. Datumsangaben im Format
15.09. oder 16.09.2026 werden jetzt vorher herausgeschnitten; "1.5" bleibt
ein Fund.

REGEL: eine Pruefung, die zum ersten Mal auf eine neue Textart trifft, ist
zuerst selbst verdaechtig. Acht gleichartige Meldungen auf einmal sind ein
Hinweis auf die Pruefung, nicht auf acht neue Fehler.

## 2.49 Keine Zahl zweimal fuehren - auch nicht zwischen Code und Mailtext (20.08.2026)

agent/drift.py nennt in der Mail Messwerte: "ein Feld von 27 haelt die
Schwelle". Diese 27 steht auch in messe_drift.py, gerechnet aus Rueckblicken
mal Horizonten mal Varianten. Wer eine Variante ergaenzt und den Mailtext
vergisst, luegt die Mail an.

Drei Pruefungen binden die Zahlen aneinander: Feldzahl gegen das Werkzeug,
Schwelle gegen die Feldzahl, Ankerzahl gegen die Summe je Klasse. Dasselbe
Muster wie bei den vier Kopien der Stopzeile im August - nur diesmal ueber
Modulgrenzen hinweg.


## 2.50 Waehrung gehoert an den Wert, nicht in den Namen (20.08.2026)

ANLASS: eine Mail zeigte ETH bei 1.931,49 EUR und darunter "Stop auf
2.025,02 EUR nachziehen" - einen Stop UEBER dem Marktpreis. Die Rechnung war
richtig, die Waehrung nicht: der Wert war USD.

DIE WURZEL: die Waehrung steht im FELDNAMEN (`stop_eur`, `risiko_eur`), und
nichts prueft, ob der Inhalt dazu passt. `ausstiegsrechnung.bewerte()` ist
waehrungsblind und rechnet mit dem, was der Aufrufer uebergibt - fuer Krypto
ist das USD. Ihr Feld hiess trotzdem `risiko_eur`.

REGEL: wer einen Betrag MIT Waehrungsangabe ausgibt, schickt ihn vorher durch
eine Umrechnung ODER benutzt ein Feld, dessen Waehrung an der Quelle
feststeht. Fehlt der Umrechnungsfaktor, steht "-" statt einer Zahl - lieber
keine als eine in der falschen Waehrung.

WERKZEUG: `pruefe_waehrungen.py` geht ueber den SYNTAXBAUM (nicht per
Textsuche, siehe 2.41) und urteilt je Stelle UMGERECHNET / NATIV / ROH /
OHNE_BETRAG. Gemessen am 20.08.: 111 Stellen in 31 Dateien, 0 ROH. Der Lauf
ist in pruefe_pakete.py verankert.

⚠️ ZWEI EIGENE FEHLER BEIM BAUEN DES WERKZEUGS, und beide sind die eigentliche
Lehre: `_eur\b` fand `entry_eur_von` nicht (auf "eur" folgt ein Unterstrich,
und der ist ein Wortzeichen), und Zwischenvariablen wurden nicht aufgeloest.
Fuenf gemeldete Stellen waren sauber.

EIN PRUEFWERKZEUG MIT FEHLALARMEN WIRD NACH DEM DRITTEN NICHT MEHR AUFGERUFEN.
Wer eines baut, prueft jede gemeldete Stelle einzeln nach, BEVOR er das
Ergebnis meldet - sonst misst er sein eigenes Muster statt des Codes.

OFFEN UND NAMENTLICH FESTGEHALTEN: `umgeworfen_preis_eur` heisst EUR, wird an
einer Stelle aber umgerechnet. Zwei Lesarten, eine falsch; ohne Blick auf die
Quelle nicht entscheidbar. Die Pruefung laesst genau diese eine Stelle zu.


## 2.47 Ueberlappende Anker: der freie Placebo reicht nicht (20.08.2026)

**Der Fall.** Kapitel 103 mass +17,8 Punkte. Ein Placebo mit frei
gewuerfelten Ausgaengen setzte die Schwelle auf **+4,7** - der Fund haette
klar getragen. Eine Block-Permutation setzte sie auf **+20,5**. Derselbe
Messwert, dasselbe Datenmaterial, entgegengesetztes Urteil.

**Die Ursache.** Taegliche Anker mit einem Vorwaertsfenster von 120 Tagen
ueberlappen einander um mehr als 99 %. Freies Wuerfeln unterstellt
Unabhaengigkeit, die es nicht gibt, und macht die Zufallsverteilung **zu
schmal** - die Schwelle damit zu niedrig.

**Die Regel.** Wo Anker zeitlich ueberlappen, ist ein freier Placebo kein
gueltiger Massstab. Es gilt die **Block-Permutation**:

- Blocklaenge **groesser als das Vorwaertsfenster**, sonst zerschneidet sie
  genau die Abhaengigkeit, die sie erhalten soll
- Bloecke aus **aufeinanderfolgenden Ankern desselben Symbols**
- **Blockgrenzen wandern je Lauf** - feste Grenzen lassen immer dieselben
  Anker gemeinsam reisen und verschmaelern die Verteilung

## 2.48 Die Schwelle ist selbst eine Schaetzung (20.08.2026)

Dieselbe Probe lief dreimal: 20 Laeufe mit festen Grenzen ergaben +18,4
(traegt nicht), 20 Laeufe mit wandernden Grenzen +16,8 (**traegt**), 40 Laeufe
+20,5 (traegt nicht). **Haette man beim zweiten aufgehoert, stuende dort
'bestaetigt'.**

**Die Regel.** Liegt der Messwert im Bereich der Schwellen-Unsicherheit, wird
die **Zahl der Laeufe erhoeht**, bevor irgendetwas behauptet wird. Ein Urteil,
das bei mehr Ziehungen kippt, war nie eins.

## 2.49 Der Preis des Absuchens ist zu beziffern (20.08.2026)

Dieselben 40 Laeufe, aber nur **eine** Zelle statt 300 ausgewertet:

| | Schwelle |
|---|---:|
| Maximum aus 300 Zellen | +20,5 |
| eine vorab benannte Zelle | **+10,2** |

**Die Haelfte der Huerde entsteht aus dem Suchen, nicht aus der Datenlage.**
Wer viele Kombinationen durchprobiert, muss ein Vielfaches liefern. Deshalb
gehoert zu jeder Rastermessung die Angabe, **wie hoch die Huerde bei einer
vorab benannten Kombination laege** - sie zeigt, was eine begruendete
Hypothese wert waere.


## 2.50 Die Kontrolle muss dieselbe Grundgesamtheit benutzen wie die Regel (20.08.2026)

**Der Fall.** Kapitel 109 prueft die Regel *"H nur in Bulle und Seitwaerts"*.
Die Block-Permutation wuerfelte die Ausgaenge zunaechst ueber **alle** Lagen
der Pruefhaelfte - auch ueber den Baermarkt.

Die Regel beschraenkt sich aber auf zwei Lagen, und die hatten in dieser
Periode eine **niedrigere Grundquote** als der Durchschnitt: 28,4 % gegen
33,0 %. Der Zufallsarm bekam damit **4,6 Punkte geschenkt**, die nichts mit
der geprueften Groesse zu tun haben, sondern mit der Auswahl der Lagen. Die
Schwelle stand bei -1,8 statt bei -5,3.

**Die Regel.** Schraenkt eine Hypothese die Grundgesamtheit ein (Lage, Klasse,
Zeitfenster, Instrument), muss die Kontrolle **dieselbe** Einschraenkung
tragen. Sonst misst man nicht, ob die Hypothese etwas beitraegt, sondern ob
die Einschraenkung eine andere Basisrate hat.

**Zusammen mit 101.6 ergibt das ein Paar:**

| | |
|---|---|
| 101.6 | Die Kontrolle darf nicht ZERSTOEREN, was legitim verschieden ist |
| **2.50** | Die Kontrolle darf nicht BEKOMMEN, was die Regel nicht hat |

Beide Male sah das Ergebnis aus wie ein Befund und war ein Artefakt der
Kontrolle.


## 2.51 Ein Nullbefund gehoert als Zerlegung abgelegt, nicht als "erledigt" (20.08.2026)

**Nutzervorgabe.** *"'Erledigt' ist immer so endgueltig und es wird weggelegt
und als Erkenntnis abgehakt - hier sollten wir vorsichtiger vorgehen, sonst
fehlen uns die Optionen und wir haben am Ende wieder kein Ergebnis, sondern
wir haben uns selbst durch einen methodisch harten Regel-Filter den Weg
verbaut."*

**Der Fall.** Kapitel 111 sollte pruefen, ob die Strukturbedingung H nur ein
umstaendlicher Momentum-Indikator ist ("nahe am Hoch"). Als Ja/Nein-Frage
gebaut, haette ein knapper Fehlschlag zu "H ist Momentum, erledigt" gefuehrt.

Als ZERLEGUNG gebaut, kam heraus: der Hochabstand erklaert **44 %**, es
bleiben **+2,3 Punkte** ueber der Schwelle. Beides ist wahr, und die
Ja/Nein-Form haette die zweite Haelfte weggeraeumt.

**Die Regel.** Eine Kontrollfrage wird als Zerlegung gestellt:

    roher Effekt      die gemessene Groesse
    Resteffekt        nach Bereinigung um den Verdacht
    Anteil erklaert   was der Verdacht traegt

**Und die Kontrollgroesse wird SELBST als Kandidat ausgewiesen.** Faellt der
Resteffekt auf null, ist das kein Ende, sondern ein TAUSCH - eine einfachere
Groesse an derselben Stelle. Ein Weg schliesst sich erst, wenn beide Zahlen
null sind.

⚠️ Das ist kein Aufweichen der Strenge: die Schwelle bleibt, die
Block-Permutation bleibt, die Laufzahl wird bei Knappheit erhoeht. Was sich
aendert, ist nur, WAS am Ende in der Ablage steht - eine Zahl mit Restgroesse
statt eines Hakens.


## 2.52 Die Blockbildung muss zur Ankerdichte passen (20.08.2026)

**Der Fall.** Kapitel 112 meldete dreimal "traegt nicht" - mit einer Schwelle,
die EXAKT dem Messwert entsprach. Der Grund stand eine Zeile darueber:
`0 Reihen lang genug fuer mindestens zwei Bloecke`.

Die Block-Permutation schneidet Bloecke nach der **Anzahl aufeinanderfolgender
Anker**. Solange jeder Handelstag ein Anker ist, sind 250 Anker auch 250 Tage.
Innerhalb einer Teilmenge (hier: H) ist das nicht mehr so - dort war nur etwa
jeder fuenfzigste Tag ein Anker, rund 36 je Reihe. Die Bedingung "mindestens
500" traf auf KEINE Reihe zu, es wurde nichts gewuerfelt, und jede
Zufallsziehung war die Messung selbst.

**Die Regel.** Ein Block ist ein ZEITRAUM, keine Anzahl. Gebildet wird nach dem
Index der Anker (`idx - block_start >= blocklaenge`), nicht nach ihrer
Position in der Liste. Die Bloecke werden dadurch verschieden gross - das ist
kein Mangel, sondern die Zeitstruktur.

⚠️ **Und die Zahl der brauchbaren Reihen gehoert IMMER ausgegeben.** Ohne die
Zeile `0 Reihen lang genug` waere der Nullbefund nicht als Nullkontrolle
aufgefallen. Eine Kontrolle, die nichts kontrolliert, sieht von aussen aus wie
eine, die bestanden wurde.


## 2.53 "Traegt" ist ohne den Abstand zum Breakeven unvollstaendig (20.08.2026)

**Der Fall.** Kapitel 113 misst einen Drifteffekt von **+0,6 Punkten** gegen
eine Schwelle von **-0,1** - formal ein "traegt". Bei 442.000 Ankern und 308
Reihen ist die Zufallsverteilung so schmal, dass fast jeder von null
verschiedene Effekt signifikant wird.

**+0,6 Punkte sind statistisch echt und wirtschaftlich nichts.** Bis zum
Breakeven fehlen 5 bis 7 Punkte.

**Die Regel.** Jedes Urteil "traegt / traegt nicht" wird zusammen mit dem
ABSOLUTEN Abstand zum Breakeven berichtet. Die Schwelle beantwortet, ob ein
Effekt **echt** ist; sie beantwortet nicht, ob er **reicht**.

⚠️ Beide Fehler sind moeglich und beide sind teuer:

| | |
|---|---|
| kleine Stichprobe | echter Effekt faellt durch (103, 105) |
| grosse Stichprobe | belangloser Effekt besteht (113) |

Die Kette schuetzt vor dem ersten. Vor dem zweiten schuetzt nur, dass die
wirtschaftliche Groesse danebensteht.


## 2.54 Horizonte vergleichen nur, wer die Unentschiedenen gleich behandelt (20.08.2026)

**Der Fall.** Kapitel 117 verglich Haltedauern von 60, 120 und 250 Tagen. Die
kuerzeste sah mit **+11,0 Punkten** am besten aus.

Der Grund war eine Auswahl: bei 60 Tagen entschieden nur **70,2 %** der Faelle,
bei 250 Tagen **95,1 %**. Die uebrigen liefen ab und wurden NICHT gewertet.
Wer die Quote unter den Entschiedenen vergleicht, vergleicht bei jedem
Horizont eine ANDERE Grundgesamtheit.

Rechnet man einen Ablauf als Fehlschlag, wird aus **+11,0** ein **-6,4**.

**Die Regel.** Bei jedem Vergleich ueber Horizonte hinweg werden zwei Lesarten
ausgewiesen:

    mild          nur Entschiedene (die Auswahl bleibt drin)
    vorsichtig    ein Ablauf zaehlt als Fehlschlag

Das URTEIL haengt an der vorsichtigen; die Wahrheit liegt dazwischen, denn ein
Ablauf ist ein Ausstieg zum Marktpreis. ⚠️ Und der Placebo rechnet in
DERSELBEN Lesart wie das Urteil - ein milderer Massstab waere zu niedrig
(2.50).

⚠️ Die Entscheidungsquote gehoert IMMER ausgegeben. Ohne sie sieht ein
Auswahleffekt aus wie ein Befund.


## 2.55 Eine Permutation ist die falsche Kontrolle fuer eine deterministische Umrechnung (20.08.2026)

**Der Fall.** Kapitel 123 verglich zwei Ausstiegsregeln gegen die Basis. Die
Kontrolle war eine Block-Permutation - und sie lieferte eine Schwelle, die auf
drei Stellen genau dem Messwert entsprach. "Nicht besser" war keine Aussage,
sondern eine Tautologie.

**Zwei Gruende, und der zweite ist der wichtigere:**

  1. Eine Permutation vertauscht Werte. Sie aendert den MITTELWERT nicht -
     wer Mittelwerte vergleicht, misst also garantiert nichts.

  2. ⚠️ Es gab hier NICHTS ZU PERMUTIEREN. Die Varianten sind
     deterministische Umrechnungen DESSELBEN Pfades; es existiert keine
     zufaellige Zuordnung, die eine Permutation zerstoeren koennte.

**Die Regel.** Vor jeder Kontrolle ist zu benennen, WAS der Zufall zerstoeren
soll:

    zufaellige Zuordnung vorhanden   -> Permutation (2.47, 2.50, 2.52)
    deterministische Umrechnung      -> BLOCK-BOOTSTRAP auf den PAARWEISEN
                                        Differenzen; Zeitbloecke MIT
                                        Zuruecklegen ziehen, Vertrauens-
                                        intervall bilden

Die Frage lautet dann nicht "ist der Unterschied echt", sondern "wie genau ist
er geschaetzt" - und ein Intervall, das die Null nicht einschliesst, ist die
Antwort.

⚠️ Und die Warnung aus 2.52 gilt hier genauso: eine Kontrolle, die nichts
kontrolliert, sieht von aussen aus wie eine bestandene. Ein Ergebnis, bei dem
Schwelle und Messwert uebereinstimmen, ist IMMER ein Befund ueber die
Kontrolle - nie einer ueber die Sache.


### 2.56 Ein Vertrauensintervall allein ist kein Urteil — die Relevanzhürde kommt zuerst

**Anlass (21.08.2026, Kapitel 124):** `pruefe_strukturstop.py` verglich zwei
Stopvarianten über 631.755 Anker und meldete:

> ⚠️ EIN GEBAUTES UND VERDRAHTETES PRODUKTIONSMERKMAL SCHADET. Das gehoert
> sofort gemeldet.

Der gemessene Unterschied war **−0,0008 R je Trade**.

**Warum das passiert:** Bei sechsstelligen Fallzahlen wird das
Vertrauensintervall so eng, dass fast **jeder** Effekt von null verschieden
ist. „Statistisch nachweisbar" trennt dann nicht mehr wichtig von unwichtig —
es sagt nur noch, dass genug gemessen wurde.

**Die Regel:** Jedes Werkzeug, das ein Urteil ausspricht, prüft **zwei Hürden
in dieser Reihenfolge**:

| | |
|---|---|
| 1. **Relevanz** | Reicht der Punktschätzer überhaupt? Schwelle **vorab** im Kopf festlegen. |
| 2. **Vertrauensintervall** | Erst wenn ja: ist er von Zufall zu trennen? |

Fällt der Effekt unter die Relevanzhürde, lautet das Urteil **„kein
Unterschied von Belang"** — nicht „besser" und nicht „schlechter".

**Wie die Schwelle gewählt wird:** am größten bekannten Effekt des Projekts.
H bringt +0,15 R je Trade; eine Zehntelstelle davon (0,01 R) ist die Grenze,
unter der ein Unterschied die Entscheidung nicht mehr dreht.

⚠️ **Das ist die Umkehrung von 2.48.** Dort war die Schwelle zu hoch angesetzt
und hat einen echten Effekt begraben. Hier war sie gar nicht vorhanden und hat
ein Nichts zum Alarm gemacht. **Beide Fehler kommen daher, dass eine einzige
Zahl über ein Urteil entscheiden durfte.**

**Umgesetzt in:** `pruefe_strukturstop.py` (`RELEVANZ = 0.01`). Bei jedem
neuen Vergleichswerkzeug mitzubauen.


### 2.57 Ein Diagnosewerkzeug muss GESUNDHEIT melden, nicht WACHSTUM

**Anlass (22.08.2026):** Der NB-Export meldete zur Lebendigkeitsreihe „401
Zeilen, 3 Tage, 163 Symbole mit Wert". Alle drei Zahlen waren richtig. **Keine
beantwortete die Frage, die der Abschnitt beantworten sollte.**

Der Abschnitt war eigens gebaut worden, damit ein Ausbleiben *sofort*
auffällt. Er hätte einen halbierten Lauf, eine ganz fehlende Quelle und einen
falsch verstandenen Abdeckungsgrad **alle drei durchgehen lassen**.

**Drei Bauarten, an denen man das erkennt:**

| Muster | warum es blind macht | was stattdessen gehört |
|---|---|---|
| **Lebenszeitsumme** | sie wächst weiter, auch wenn ein Lauf die Hälfte schreibt | der **letzte Lauf** und eine Reihe je Tag |
| **Vermischte Grundgesamtheit** | „163 Symbole" las sich wie Abdeckung, enthielt aber den Vorrat | der Schnitt, auf den es ankommt, **getrennt** |
| **Takt ohne Fälligkeitstermin** | eine Wochenquelle fehlt am Anfang **zu Recht** und später **zu Unrecht** — gleiches Bild | das **Datum**, ab dem Fehlen ein Fehler ist |

⚠️ **Der dritte ist der gefährlichste**, weil er zeitverzögert zuschlägt. Am
22.08. fehlte die Entwicklerquelle richtigerweise (Sammlungsbeginn Donnerstag,
erster Montag 24.08.). Im November hätte dasselbe Bild einen Totalausfall
bedeutet — **und genauso ausgesehen**.

**Die Prüffrage vor jedem Diagnosefeld:**

> *Gibt es einen Defekt, bei dem dieses Feld unverändert aussieht?*

Lautet die Antwort ja, ist das Feld eine Beruhigung, keine Diagnose.

⚠️ **Und geprüft wird gegen DATEN, nicht gegen Quelltext.** Die neun
Dauerprüfungen dazu bauen eine SQLite-Datenbank im Speicher und rufen die
Exportfunktion auf. Eine Textprüfung hätte nichts gefunden: der Fehler lag
nicht in einem fehlenden Wort, sondern in **einer Zahl, die zu viel
enthielt**. Geprüft werden beide Urteile — „noch nicht fällig" **und**
„überfällig" — denn ein Werkzeug, das nur warnen kann, warnt bald immer.

**Umgesetzt in:** `extract_notebook_diagnose._kapitel93` (`eigene_symbole`,
`letzter_lauf.je_tag`, `entwickler_takt`), Prüfungen in `pruefe_pakete.py`.


### Die Messkette zu H — Kapitel 99 bis 124 (Nachtrag 22.08.2026)

⚠️ **Dieser Abschnitt schließt eine Lücke, die dem eigenen Anspruch
widerspricht.** 2.13 wurde gebaut, weil drei Mess-Funktionen ohne Aufrufer
dalagen. Beim Nachziehen am 22.08. gezählt: **116 Skripte im Projektstamm, 69
in diesem Werkzeugkasten.** Die Messkette der letzten drei Wochen war
vollständig **nicht** verzeichnet — dieselbe Falle in neuer Auflage.

**Die Grundlage — hier fängt jede Messung an:**

| Skript | Beantwortet | Auslöser |
|---|---|---|
| `lade_messreihen.py` | Baut `data/messdaten.db` (523 Reihen, 770.873 Kerzen, Binance-USDT). **Die Basis aller Kapitel ab 107.** | einmalig; erneut nur, wenn die Reihen altern |
| `messe_marken.py` | **Der Ankergenerator.** Erzeugt je Anker Hochabstand, Drift, Umsatz, Marken (frei/gedeckt/Berührungen/Alter/gefegt), Marktphase, Ausgang, Tage, Stopabstand. Acht Werkzeuge bauen darauf auf. | wenn ein neues Merkmal je Anker gebraucht wird |
| `simuliere_bremse.py` | Trägt die gemeinsame Infrastruktur: `gebuehr_je_seite()`, `SAETZE_ZUM_BERICHTEN`, `_reihen_roh()`, `_marktphase()` | nie direkt — wird importiert |

**Die Befunde, nach Frage sortiert:**

| Skript | Beantwortet |
|---|---|
| `messe_umschlag_kontext.py` | Heißt hoher Umschlag nach einem Anstieg etwas anderes als in der Ruhe? (98) |
| `messe_geometrie.py` | Welche Geometrie trägt sich — und hängt sie an der Lage? (101) |
| `messe_drift_absolut.py` | Trägt die **absolute** Drift das Barrierensystem? (102) |
| `messe_zeitteilung.py` | Wird aus dem Muster eine Regel? (109) — Zeitteilung |
| `messe_kollinearitaet.py` | Sind zwei Hebel dasselbe? (103) |
| `messe_struktur_bereinigt.py` | Trägt H über den Hochabstand hinaus? (108) |
| `messe_spiegel.py` | Ist H eine Richtungsbedingung? (110) — Spiegelbedingung |
| `messe_zerlegung.py` | Wie viel von H erklärt Momentum? (111) — **Zerlegung, nicht Ja/Nein** (2.51) |
| `messe_anreicherung.py` | Wissen Marken mehr (Berührungen, Alter, gefegt)? (112) |
| `messe_drift_zerlegt.py` | Ist der Drift der ATR-Kanal? (113) |
| `messe_phase_invers.py` | Wirkt die Marktphase invers? (114) |
| `messe_wann.py` | Hat H einen Anwendungszeitpunkt? (115) |
| `messe_liquiditaet.py` | Braucht H Liquidität? (116) |
| `messe_dosis.py` / `messe_dosis_sauber.py` | Braucht H eine eigene Geometrie? (117/118) |
| `bewerte_neu.py` | Rechnet alle Kapitel auf **zwei Gebührensätze** um (119) |
| `messe_klassen.py` | Trägt H je Kategorie und je Strategie? (120) |
| `messe_ueberleben.py` | Wie stark verzerrt die Überlebensauswahl? (121) |
| `pruefe_watchlist.py` | Wirkt H auf der **echten** Auswahl? (122) |
| `messe_ausstieg.py` | Tragen Teilverkauf und Einstandstop? (123) |
| `pruefe_strukturstop.py` | Schadet der Strukturboden im Stop? (124) — ruft die **Produktionsfunktion** |
| `pruefe_phasenindex.py` | Hält der Phasenindex, was er misst? (114, Gegenprobe) |

> ⚠️ **Alle bis auf eines tragen `⚠️ DIESER KOPF IST DIE VORABFESTLEGUNG`** —
> die Frage und ihre Abbruchregel stehen dort, **bevor** gerechnet wurde. Wer
> eines davon wiederverwendet, muss den Kopf neu schreiben, nicht nur die
> Parameter.
>
> **Die Ausnahme ist `pruefe_watchlist.py`, und sie bleibt eine.** Sie
> nachträglich zu schreiben wäre genau das, was die Regel verbietet: eine
> Frage „vorab" zu formulieren, nachdem die Antwort bekannt ist. Das Skript
> trägt seit dem 22.08. stattdessen den ehrlichen Vermerk, **warum** es keine
> braucht — es wendet die seit 108/119 feststehende Regel unverändert auf eine
> Teilmenge an, ohne einen einzigen gesuchten Parameter.


## 2.58 Das Messsystem — wie in diesem Projekt eine Messung gebaut wird

⚠️ **Warum dieser Abschnitt existiert (Nutzerhinweis 22.08.2026: „es sollte
auch ein Regelwerk oder Messsystem-Doku geben").** Die Bausteine standen
verstreut: Regeln in 2.47–2.57, Werkzeuge in 2.13, Ergebnisse in der
Befundkarte, Herleitungen in den Umbauplan-Kapiteln. **Wer eine neue Messung
aufsetzt, musste vier Dokumente zusammensuchen.** Hier steht das Gerüst an
einer Stelle. *Kein neues Dokument* — dieselbe Datei ist laut Landkarte für
„WIE getestet wird" zuständig.

### 2.58.1 Die sechs Teile, die jede Messung hat

| Teil | verbindlich | wo geregelt |
|---|---|---|
| **1 Vorabfestlegung** | Frage, Erwartung und **Abbruchregel** im Docstring, **bevor** gerechnet wird | 2.51 |
| **2 Grundgesamtheit** | dieselbe für Regel und Kontrolle — nie die Regel auf Teilmenge, die Kontrolle auf alles | **2.50** |
| **3 Kontrolle** | Block-Permutation bei überlappenden Ankern · **Block-Bootstrap** bei deterministischen Umrechnungen | 2.47 · **2.55** |
| **4 Schwelle** | ist selbst eine Schätzung; Läufe erhöhen, wenn der Messwert nahe liegt. **Preis des Absuchens** ausweisen | 2.48 · **2.49** |
| **5 Urteil** | **Relevanz vor Vertrauensintervall** · „trägt" nur mit Breakeven-Abstand · beide Lesarten bei Horizonten | **2.56** · 2.53 · 2.54 |
| **6 Ablage** | Nullbefund als **Zerlegung mit Rest**, Kontrollgröße selbst als Kandidat | 2.51 |

### 2.58.2 Die feststehenden Größen

| Größe | Wert | Herkunft |
|---|---|---|
| Messbasis | **523 Reihen**, 770.873 Kerzen, Binance-USDT | `lade_messreihen.py`; 347 handelnd + 176 eingestellt (121) |
| Referenzgebühr | **0,30 % je Seite** | Mischsatz üblicher Krypto-Broker — „ist das ein guter Trade" |
| Betriebsgebühr | **1,50 % je Seite** | Bitpanda-Brokerspread — „rechnet es sich für mich" |
| Kostenformel | `Kosten_R = 2 × Gebühr / Stopabstand` | 119 |
| Breakeven | `(1 + Kosten_R) / (1 + CRV)` | Basisrate ist `1/(1+CRV)` — die Hürde liegt bei Kosten > 0 **immer** darüber |
| Positivkontrolle | **Pflicht bei jedem Nullbefund** | 93 B — sonst heißt „nichts gefunden" nur „nicht hingesehen" |

> ⚠️ **Beide Gebührensätze werden IMMER nebeneinander berichtet.** Ein
> einzelner Satz beantwortet je nur eine der beiden Fragen, und achtzehn
> Kapitel lang beantwortete das Projekt unbemerkt die falsche.

### 2.58.3 Die drei Fehlerarten, die dieses Projekt wiederholt getroffen haben

| Art | Beispiel | Gegenmittel |
|---|---|---|
| **Blick in die Zukunft** | `_gefegt` las die ganze Restreihe → 79,0 % statt 67,3 % (112) | Reihe **am Anker abschneiden**, gegen die Produktion gegenrechnen |
| **Ungleiche Arme** | H in zwei Phasen gegen alle Anker in allen Phasen (109) — 4,6 Punkte Geschenk | 2.50 |
| **Entartete Kontrolle** | Schwelle gleich dem Messwert auf drei Stellen — es gab nichts zu permutieren (123) | 2.55; Zahl der brauchbaren Reihen **immer** ausdrucken (2.52) |

### 2.58.4 Und die Regel über allen anderen

> **Was gemessen wird, muss auch das sein, was analysiert wird** — und ein
> Werkzeug, das Fehlalarme gibt, wird nicht mehr aufgerufen.

Beides ist teuer bezahlt: eine Rollenanalyse („LLM wegen Sprache, NICHT wegen
Zahlen") und Minuten später eine Zahlen-Schätzung gemessen; und fünf
Fehlmeldungen aus einem Prüfwerkzeug, nach denen niemand es mehr startete.


### Der Restbestand — 52 Werkzeuge, die nie verzeichnet waren (22.08.2026)

⚠️ **Auf Nutzerhinweis geprüft** („offenbar nicht immer alle Punkte und
Umsetzungen dokumentiert"). Gezählt: **116 Skripte im Projektstamm, 64 in
diesem Werkzeugkasten** — auch nach dem Nachtrag zur H-Kette weiter oben.

**Und die erste Fassung dieses Nachtrags war selbst unvollständig**: sie ließ
die Kapitel 98, 101, 102 und 109 aus, obwohl sie zur beschriebenen Kette
gehören. Genau das Muster, das der Nutzer benannt hat.

⚠️ **Was hier folgt, ist ein INDEX, keine Bewertung.** Jede Zeile ist die
erste Zeile des jeweiligen Docstrings, maschinell übernommen. Ob ein Werkzeug
noch läuft, ob sein Befund noch gilt und ob es einen Aufrufer hat, steht damit
**nicht** fest — das ist bei jedem einzelnen an der Quelle zu prüfen. Ein
Index verhindert nur das eine: dass ein fertiges Werkzeug unsichtbar bleibt
und die Arbeit ein zweites Mal gemacht wird. **Genau dafür wurde 2.13
angelegt.**

#### LLM-Ebene, Prompts und Konfidenz (04.–10.08.)

| Skript | Erste Zeile des Docstrings |
|---|---|
| `messe_llm1_positionsbias.py` | Ist LLM1 positionsempfindlich wie LLM2? |
| `messe_prompt_verbesserungen.py` | Messen, BEVOR gebaut wird: zwei Prompt-Änderungen an LLM1 |
| `messe_regime_empfindlichkeit.py` | Reagiert das LLM überhaupt auf die Marktphase? |
| `messe_konfidenz_kalibrierung_neu.py` | Sagt Konfidenz etwas vorher — und müssen die Schwellen neu? |
| `messe_abstand_zum_zufall.py` | Schlägt die LLM-Ebene den Zufall? Größtmögliche Stichprobe |
| `messe_llm_gegen_regel.py` | Die Nullmessung: schlägt das LLM eine deterministische Regel? |
| `messe_einordnung_wirkung.py` | Wirkt das KLARTEXT-Urteil oder der Zahlenvergleich? |
| `messe_umbau_wirkung.py` | Wirkt der Umbau? Alt gegen neu, je Fakt, gepaart |
| `messe_abgleich_alt_neu.py` | Hebt der Umbau den Deadloop auf? Alt gegen neu, dieselben Fälle |
| `messe_zai_ohne_regime.py` | Leitet Z.ai LONG ab, wenn `regime` NICHT im Faktensatz steht? |
| `messe_regimeflag_sauber.py` | Der Regime-Flag, sauber: 2×2 aus Trigger-Richtung und Flag |
| `messe_namensanker.py` | Trägt der TICKERNAME das Urteil? |
| `messe_faktorzahl.py` | Steigt die Handlungsquote mit der Zahl unabhängiger Faktoren? |
| `messe_dritter_faktor.py` | Der kausale Test: hebt ein DRITTER Faktor die Handlungsquote? |
| `messe_szenario_stufe1.py` / `pruefe_szenario_stufe0.py` | Szenario-Schätzer, Stufe 0 und 1 |
| `pruefe_gemini_verhalten.py` | Was Gemini tatsächlich begrenzt — gemessen, nicht behauptet |
| `pruefe_gegenpruefung_trefferquote.py` | Erkennt der Konsistenzprüfer echte Widersprüche? |
| `pruefe_belege_gegen_fakten.py` | Nennt das Modell ein Perzentil, wo es keines gibt? |

#### Ausstieg, Halten und Positionsgröße (04.–06.08.)

| Skript | Erste Zeile des Docstrings |
|---|---|
| `messe_halte_kriterium.py` | Taugt das `halte_kriterium` etwas? 1.747 Zielpreise, nie ausgewertet |
| `messe_halten_ursache2.py` | Zweite Ablationsrunde: trägt einer der SIEBEN fehlenden Blöcke? |
| `messe_halten_ursache3.py` | Welcher Fakt trägt das HALTEN — **abbauend** statt aufbauend |
| `messe_zeitschranke.py` | Was passiert wirklich mit Trades, die die Zeitschranke erreichen? |
| `messe_planungshorizont.py` | Wann wird die Kante real? Der Planungshorizont, gemessen statt gesetzt |
| `bewerte_dynamisch.py` | Ergebnis unter der LIVE gefahrenen Ausstiegsregel statt starrer Barrieren |
| `pruefe_regel_je_marktphase.py` | Hält die Ausstiegsregel in ALLEN Marktphasen? |
| `pruefe_crv_positionsgroesse.py` | E2E-Prüfung der stufenlosen CRV-Abstufung, Spot |
| `messe_akkumulation.py` / `messe_akkumulation_az4.py` | Schlägt antizyklische Akkumulation (AZ-4) das stumpfe DCA? |
| `messe_allocator_gegen_zufall.py` | Ist die Budget-Allocator-Auswahl besser als Zufall? |
| `messe_short_und_einbruch.py` | SHORT als VERGLEICH messen — und was dabei auffiel |
| `messe_kostenhebel.py` | Gibt es diesen Aufbau überhaupt in einer tragfähigen Variante? |

#### Lagebild, Regime und Marktphase (06.–20.08.)

| Skript | Erste Zeile des Docstrings |
|---|---|
| `pruefe_marktlage.py` | Prüft das Lagebild (L2 Volatilität, L3 Trend, L4 Liquidität) an echten Daten |
| `pruefe_regime_glaettung.py` | Gegenprüfung der Regime-Glättung und des Divergenz-Fakts |
| `messe_marktphasen.py` | Verhält sich die Kette in verschiedenen Marktphasen unterschiedlich? |
| `messe_konstellationen.py` | Wo sitzt der Unterschied — Phase, Asset, oder in der Zahl selbst? |
| `messe_zellen_ausgang.py` | Unterscheiden sich die vier Struktur-Zellen im AUSGANG? |
| `messe_basislinie.py` / `messe_basislinie_aufloesung.py` | Die Basislinie vor dem glatten Schnitt |
| `messe_filterschaden.py` | **Schadet** der Anlassfilter? — gemessen, nicht geschätzt |
| `messe_trichter_treffer.py` | Hält der Trichter, was er sagt? (93 A, Fallstrick A2) |
| `messe_akkumulation_phasen.py` | Hängt die Rangfolge der Kaufregeln an der Marktrichtung? Zerlegt in nicht überlappende Zweijahresfenster und misst gegen den **quotengleichen** Zufall (23.08.) |
| `messe_tagewahl_je_symbol.py` | Trägt der Tagewahl-Vorsprung je Symbol — und **bleibt** er dort? (Beständigkeit, 23.08.) |
| `messe_tagewahl_je_eigenschaft.py` | Welche **Eigenschaft** eines Assets erklärt den Vorsprung? Liquidität, Volatilität, Größe, Alter, Beta, Marktzustand (23.08.) |
| `messe_querschnitt_umkehr.py` | Trennt die Umkehr-Bedingung die Assets **am selben Tag**? Querschnitt statt innerhalb eines Werts (23.08.) |
| `messe_auswahl.py` | Wie ist die **Auswahl** zu dimensionieren — k, Trendfilter, Marktzustand, Kosten der Drehung? (A1, 23.08.) |
| `messe_auswahl_historie.py` | Was hätte die Auswahl über die Historie ergeben? Signalzahl, Trefferquote, je Assetstufe und Marktlage (A1, 23.08.) |
| `messe_auswahl_kriterium.py` | **Quote oder Kriterium?** Wie viele kommen durch, wie oft keiner, und was das kostet (23.08.) |
| `pruefe_ausrollen.py` | **Nach jedem Ausrollen:** Schema, Leseprobe ueber den Modell-Lesepfad, Auswahl-Schatten, Trichter-Monotonie, Verkaufsseite, Rohstoff-Kerzen. Liest nur (24.08.) |
| `messe_strukturstop.py` | Trägt die Struktur den Stop? — Vorläufer von `pruefe_strukturstop.py` (124) |
| `messe_dimensionierung.py` | Was ändert sich, wenn der Hebel **anfällt** statt gewählt zu werden |

#### Datenbeschaffung und Betrieb

| Skript | Erste Zeile des Docstrings |
|---|---|
| `lade_fear_greed_nach.py` | Fear-&-Greed-Historie nachladen |
| `lade_makro_historie_nach.py` | Makro-Historie: Netto-Liquidität und Zinskurve |
| `pruefe_produktion_nb.py` | **Rauchtest für die Produktion auf dem Notebook** — nach dem Deployment |
| `pruefe_auswertbarkeit.py` | Kann die Messung ihre Frage überhaupt noch beantworten? |
| `pruefe_ausschuss_suche.py` | Prüfstand für die Ausschuss-Suche |

> ⚠️ **Zwei davon gehören in die Routine, nicht in ein Archiv:**
> `pruefe_produktion_nb.py` nach **jedem** Deployment auf das Notebook, und
> `pruefe_auswertbarkeit.py`, **bevor** eine Messung gestartet wird — sie
> beantwortet genau die Frage, an der die Läufe vom 10.08. gescheitert sind
> („Messung VOR dem Start prüfen, nicht das Ergebnis").


### 2.59 Eine Positivkontrolle misst die VERSCHIEBUNG, nicht den Wert danach

**Anlass (22.08.2026, Kapitel 125).** Die Kontrolle pflanzte 300 Treffer ein
und verglich das **Ergebnis** mit der Zufallsschwelle: **+0,4 gegen +2,5**.
Der naheliegende Schluss wäre gewesen: *das Werkzeug ist stumpf, ein
Nullbefund wäre wertlos* — und ein echter Befund von **−5,8 Punkten** wäre als
„nicht messbar" abgelegt worden.

**Der Fehler:** der eingepflanzte Effekt wirkte exakt richtig
(**Verschiebung +6,3, erwartet +6,3**). Nur lag der Ausgangswert so tief, dass
die Summe trotzdem unter der Schwelle blieb.

> **Die Frage lautet nicht „ist das Ergebnis groß genug", sondern „sehe ich
> die Änderung, die ich selbst verursacht habe".**

**Die Regel:** eine Positivkontrolle misst **immer** gegen denselben Lauf
ohne Einpflanzung. Sie druckt drei Zahlen: vorher, nachher, Verschiebung —
und daneben, was zu erwarten war. Weicht die Verschiebung um mehr als eine
kleine Toleranz ab, bricht der Lauf ab.

⚠️ **Der Fehler ist besonders tückisch, weil er nur bei einem starken echten
Effekt auftritt** — also genau dann, wenn etwas zu finden gewesen wäre.

**Umgesetzt in:** `messe_reihung_x_h.py`.

### 2.60 Wiederholte Bewertungen desselben Werts sind EINE Beobachtung

**Anlass (22.08.2026, Nutzerfrage):** *„wie wir diese korrekt zählen wenn
z. B. HYPE 5 mal am Tag eine Bewertung erhalten hat, ist das abgrenzbar?"*

**Gemessen an den 1.118 Z.ai-Gegenprüfungen: Faktor 5,82.**

| | |
|---|---:|
| Einträge | 1.118 |
| verschiedene Symbole | **22** |
| verschiedene (Symbol, Tag) | **192** |
| Höchstzahl an einem Tag | **48** |

**Die Folge:** Vertrauensintervalle werden um rund **Faktor 2,4** breiter.
In Kapitel 126 hat das **drei von vier Urteilen gekippt** — von „BESSER" bzw.
„SCHLECHTER" zu „nicht unterscheidbar".

**Die Regel:**

| | |
|---|---|
| **Zähleinheit** | der **Anlass**, nicht das Signal — `agent/anlass.py` definiert ihn (derselbe Fingerabdruck binnen 24 h) |
| **Näherung** | (Symbol, Tag), wenn der Fingerabdruck nicht vorliegt |
| **Rechnung** | Intervall auf `n / Häufungsfaktor`, die **Quote bleibt** |
| **Mindestzahl** | gilt für die **effektive** Stichprobe, nicht die rohe |

⚠️ **Das ist die Ergänzung zu 2.19.1**, die dort als Forderung stand
(*„jede künftige Messung dieser Bauart braucht die Gewichtung"*) und bis heute
in keinem Werkzeug umgesetzt war.

**Umgesetzt in:** `messe_signalbilanz.py` (`HAEUFUNG_GEMESSEN`).


### Nachtrag 22.08.2026 (abends) - zwei weitere Werkzeuge

| Skript | Beantwortet |
|---|---|
| `messe_reihung_x_h.py` | Traegt die Reihung **zusaetzlich zu H**? (125) - Antwort: sie traegt **negativ**, -5,8 Punkte |
| `messe_signalbilanz.py` | Was haben unsere **echten** Signale gebracht? (126) - Anbieter, Rolle G, Schatten, mit Haeufungskorrektur |

⚠️ Beide wurden von der Dauerpruefung "jedes Messwerkzeug steht im
Werkzeugkasten" gefangen, bevor sie hier fehlen konnten - die Pruefung vom
selben Morgen hat sich am selben Tag bezahlt gemacht.


### Nachtrag 22.08.2026 (spaet) - der Einstiegsnachweis

| Skript | Beantwortet |
|---|---|
| `pruefe_einstiegsnachweis.py` | Wurde der Einstieg je erreicht? (127) - **21,1 % nicht**, und der Rest ist Marktrichtung |


### Nachtrag 22.08.2026 - die Stopquelle

| Skript | Beantwortet |
|---|---|
| `messe_stopquelle.py` | Darf der Rauschboden das Modellurteil ueberstimmen? (130) - **ja**, -0,609 R fuer die These |


### Nachtrag 22.08.2026 - die Gegenpruefung ueber alle Rollen

| Skript | Beantwortet |
|---|---|
| `pruefe_s6a_rollen.py` | Haelt eine geaenderte FRAGE ueber ALLE Rollen? (133) - Prompt gegen Schema, Validator, Datenbank, Rolle G. **Drei Abhaengigkeiten waeren gebrochen** |

⚠️ **Bei jeder Aenderung an Prompt, Schema oder Aktionsvokabular aufrufen.**
Alle drei Funde kamen aus dieser Pruefung, keiner aus der Arbeit an der
geaenderten Stelle.


### `pruefe_aktionsvokabular.py` — kennt jede Stelle das volle Vokabular?

**Auslöser:** eine Aktion wird ergänzt, umbenannt oder entfernt.

**Was es prüft.** Über den Syntaxbaum aller Betriebsdateien: jede Liste und
jeder Vergleich, der eine verkaufsseitige Aktion nennt, muss die
verkaufsseitigen Aktionen der **neuen** Kette vollständig nennen.

**Warum es das gibt (22.08.2026, S6c).** `REDUZIEREN` fehlte an sechs Stellen
— darunter `_TRACKABLE_ACTIONS`, die entscheidet, ob ein Signal überhaupt
**aufgelöst** wird. 57 Signale lagen in der Datenbank, 55 auf
`nicht_anwendbar`; im Export standen sie im Band `mit_halten` und fehlten in
`ohne_halten`. Sie sahen aus wie NICHTS_TUN.

⚠️ **Der Fehler war nicht der Tippfehler, sondern die Bauart:** wer eine
Aktion ergänzt, muss von Hand jede Liste finden, die Aktionen aufzählt.

⚠️ **Jede Ausnahme trägt einen Grund, keinen Haken.** Die Suite prüft, dass
der Grund vorhanden und nicht leer ist — eine Ausnahme ohne Begründung ist
ein Schalter, keine Aussage.

**Läuft in der Suite mit.** Einzeln: `python pruefe_aktionsvokabular.py`.


### 2.61 Wer eine Spalte anlegt, muss eine Zeile daraus lesen (22.08.2026)

**Anlass:** Die App startete am Notebook nicht mehr. E1 hatte
`einstieg_erreicht` per Migration auf `signals` **und** `hebel_signals`
gelegt; `_row_to_hebel_signal()` gab die Zeile ungefiltert in den Konstruktor,
und eine unbekannte Spalte ist dort ein `TypeError`.

**Die Regel.** Eine Migration ist erst geprüft, wenn eine Zeile aus der
**migrierten** Tabelle durch den **Lesepfad** gegangen ist.

⚠️ **Ein Schreibtest genügt nicht.** Das Schreiben nennt seine Spalten
einzeln — eine neue fällt dort nicht auf. Das Lesen bekommt sie alle auf
einmal.

⚠️ **Und der blinde Fleck des Desktops.** Hier läuft `main.py` nie (stehende
Vorgabe: nie gegen die Produktiv-Datenbank). Also läuft die Migration nie,
also hat die Tabelle die Spalte nie, also ist **jede** Prüfung gegen diese
Datenbank strukturell blind für Migrationsfolgen. **Die Prüfung muss die
Migration selbst auslösen** — frische Datenbank, `init_db()`, Zeile schreiben,
Zeile lesen.

**Umgesetzt** in `pruefe_pakete.py` (Paket Dimension): für `signals` und
`hebel_signals` je eine Zeile mit allen Pflichtfeldern durch `_row_to_signal()`
bzw. `_row_to_hebel_signal()`. Positivkontrolle bestanden.


### 2.62 Ein erweiterter Filter öffnet keine abgelegte Zeile (22.08.2026)

**Anlass:** S6c erweiterte `_TRACKABLE_ACTIONS` um `REDUZIEREN`. Ich schrieb,
die betroffenen Zeilen bekämen ihr Ergebnis „beim nächsten Lauf
nachträglich". **Am Export desselben Abends standen 11 von 12 unverändert
da.**

**Die Regel.** Wer einen Auswahlfilter erweitert, ändert damit nur, was
**künftig** hineinläuft. Zeilen, die der alte Filter in einen **Endzustand**
geschrieben hat (`nicht_anwendbar`, `abgelaufen`, …), werden nie wieder
angefasst — die Auswertung holt sich typischerweise nur `NULL` oder `offen`.

**Was zu tun ist.** Zu jeder Filtererweiterung gehört die Frage: *gibt es
Zeilen, die der alte Filter endgültig abgelegt hat?* Wenn ja, braucht es eine
**eigene, einmalige Nachöffnung** —

1. **eng gefasst**: nur die Zeilen, die der alte Filter ausgeschlossen hat,
   nicht alle mit demselben Endzustand;
2. **mit Marke** (hier: `meta`-Schlüssel), sonst öffnet jeder Start erneut,
   was die Auswertung zu Recht wieder ablegt — eine Schleife ohne Ende;
3. **an einer Kopie der echten Datenbank geprüft**, nicht nur an einer leeren.

⚠️ **Und die Erwartung gehört gemessen, nicht angenommen.** Meine Aussage
stand vier Tage unwidersprochen in der Doku, weil niemand nachgesehen hat.


### `pruefe_instrument_verzweigungen.py` — jede Verzweigung am Instrument

**Auslöser:** ein Lauf wird entfernt, hinzugefügt oder umbenannt; oder eine
neue Bedingung `instrument == …` wird gebaut.

**Was es prüft.** Über den Syntaxbaum aller Module der neuen Kette: jede
Verzweigung am `instrument` muss ein **Urteil** tragen — `lebt` (bekommt das
Ergebnis-Etikett) oder `tot` (bekommt das Lauf-Etikett). Eine Stelle ohne
Urteil lässt die Prüfung durchfallen.

**Warum es das gibt (23.08.2026).** S6b hat den zweiten Lauf entfernt: Krypto
läuft nur noch mit `instrument="spot"`. Jede Bedingung `instrument == "hebel"`
ist damit **toter Code** — und **keine davon wird rot**, sie tut einfach nichts
mehr. Gefunden wurden sie einzeln und zu spät:

| | |
|---|---|
| Cooldown-Topf des Hebel-Laufs | Produktion drei Stunden stumm |
| Finanzierungsrate, Liquidationsabstand | fehlten im Lagebild |
| ⚠️ `rechne()` | rechnet den Hebel aus dem Lauf — seit S6b **immer 1,0** |
| ⚠️ `felder_aus_entscheidung()` | schreibt die `hebel`-Spalte nie — Topf und Cooldown tot |

**Stand:** 14 Stellen, 11 für Krypto tot. Einzeln:
`python pruefe_instrument_verzweigungen.py`.


### 2.63 `finde_freie_namen` gehört VOR den Funktionstest (23.08.2026)

**Anlass:** In `gesperrt_bis()` habe ich `g` benutzt — den Namen, den es nur
in `stunden()` gibt. Der breite Fehlerfang schluckte den `NameError`, und
**jede Gruppe galt als frei**: der Cooldown war komplett aus.

⚠️ **Das Werkzeug hätte es gefunden** — nachgestellt: mit eingebautem Fehler
meldet `finde_freie_namen.py` genau eine Fundstelle. **Ich habe es zu spät
laufen lassen.** Kein Werkzeuggap, ein Ablauffehler.

**Die Regel:** nach jeder Bearbeitung einer Betriebsdatei **zuerst**
`python finde_freie_namen.py`, **dann** der Funktionstest. Ein freier Name
verfälscht den Funktionstest, statt ihn scheitern zu lassen — der Test läuft,
er misst nur etwas anderes.

⚠️ **Die zweite Unterart sieht das Werkzeug weiterhin nicht:** ein Name, der
in derselben Funktion **später** gebunden wird (`_YAML2`, `_sq3`, `_AK`).
Dagegen hilft nur die Regel *„der Import gehört vor den ersten Gebrauch"* —
siebtes Vorkommen in drei Tagen.


### 2.64 Ein Testfall, der vom Kalender abhängt, meldet irgendwann einen Fehler, den es nicht gibt (24.08.2026)

**Gefunden beim Ausrollen.** Die Suite fiel um — an einer Prüfung, die mit dem
Umbau nichts zu tun hatte:

> `ein noch nicht faelliger Montag ist KEINE Warnung` — FEHL

**Die Prüfung hielt ein FESTES Datum gegen ein LAUFENDES „heute".** Sie baute
eine Datenbank mit Start am **20.08.** (Donnerstag), rechnete daraus den ersten
fälligen Montag — den **24.08.** — und erwartete, dass er **noch nicht** da ist.

⚠️ **Am 24.08. war er da. Das Produkt hat richtig gewarnt, die Prüfung war
gealtert.**

**Die Regel:**

> **Ein Testfall darf sein Szenario festlegen, aber nicht seinen Kalendertag.**
> Wo eine Prüfung „noch nicht fällig" oder „schon fällig" behauptet, muss das
> Datum **relativ zu heute** entstehen — sonst wandert der Testfall irgendwann
> in den anderen Zustand, und die Prüfung meldet einen Fehler, den es nicht
> gibt.

**Warum das teuer ist:** eine Prüfung mit Fehlalarmen wird nicht mehr
aufgerufen (2.x, Währungsprüfung). Und sie kam ausgerechnet an dem Tag, an dem
38 Commits ausgerollt wurden — die erste Frage war „habe ich etwas kaputt
gemacht", und die Antwort lag drei Ebenen entfernt.

**Behoben:** das Startdatum wird auf den **nächsten Donnerstag nach heute**
gelegt, der erste Montag daraus gerechnet. Beide Erwartungen — der Montag und
der Auswertungstermin zwölf Wochen später — folgen jetzt der Rechnung statt
einer Konstante. Dasselbe für die Tagesschlüssel in `je_tag`.

⚠️ **Und die Gegenprobe bleibt:** der zweite Fall („ein vergangener Montag OHNE
Zeile IST eine Warnung") war schon immer relativ gebaut und ist unverändert
grün. Beide Zustände werden weiterhin geprüft — nur hängt keiner mehr am
Wochentag.


### 2.65 Ein Prüfwerkzeug, das dreimal falsch lag — und was daran allgemein ist (24.08.2026)

`pruefe_ausrollen.py` sollte den Ausrollstand am Notebook bestätigen. Es hat in
drei aufeinanderfolgenden Läufen **drei verschiedene falsche Aussagen** über die
Kette gemacht — die Kette war jedes Mal in Ordnung.

| # | was es meldete | was wirklich war |
|---|---|---|
| **1** | „die Stufe `auswahl` fehlt noch — alter Codepfad" | Es las `bestanden_je_stufe`, also die Namen der **Python-Attribute**. `als_json()` schreibt `bestanden`. Ein leeres dict wurde zur Aussage |
| **2** | „2 hinein → auswahl 0/0 → 0 heraus" | stimmte, **beantwortete aber die Frage nicht**, die es aufwarf: wo blieben die zwei? Es zeigte nur *eine* Stufe |
| **3** | dieser Lauf sei grün | `Durchlauf` legt **alle** Stufen mit 0 an — `"auswahl" in best` ist deshalb **immer wahr** und sagt nichts darüber, ob die Stufe erreicht wurde |

**Drei Fehler, ein Muster:**

> ⚠️ **Das Werkzeug hat seine Quelle vermutet, statt sie zu lesen** — einmal die
> Schlüsselnamen, einmal den Umfang, einmal die Semantik eines Vorgabewerts.

**Und der Grund, warum es dreimal passieren konnte:** der Code stand **inline in
`main()`** und war damit **nicht prüfbar**. Jede Korrektur war ein neuer Blindflug.

**Die Regeln daraus:**

1. **Ein Prüfwerkzeug wird gegen das geprüft, was das Produkt WIRKLICH
   schreibt** — nicht gegen eine Annahme darüber. Konkret: die Dauerprüfung
   ruft jetzt `rollen_gate.schreibe()` auf und liest das Ergebnis mit derselben
   Funktion, die auch im Betrieb liest.
2. **Was ein Werkzeug behauptet, muss als Funktion vorliegen, nicht in `main()`.**
   Inline heißt unprüfbar, und unprüfbar heißt: der nächste Fehler fällt wieder
   erst dem Nutzer auf.
3. **Findet ein Werkzeug nicht, was es sucht, meldet es das als EIGENEN
   Fehler** — nicht als Befund über das Geprüfte. „erwartet `bestanden`,
   gefunden […] — das ist ein Fehler DIESER Prüfung, nicht der Kette."
4. ⚠️ **Ein Vorgabewert ist kein Fehlen.** Wer auf `"x" in d` prüft, wo `d` alle
   Schlüssel mit 0 vorbelegt, prüft nichts. Auf den **Wert** prüfen.

**Was es gekostet hätte:** die Zusammenfassung am Notebook las Punkt 4 als grün
(„Selection stage is now live"). Er war es nicht — und beim nächsten Mal hätte
niemand mehr hingesehen, denn *eine Prüfung mit Fehlalarmen wird nicht mehr
aufgerufen* (2.x).


**Nachtrag am selben Tag — der vierte Fehler war keiner im Lesen, sondern im
Sagen.** Das Werkzeug meldete korrekt *„größter Verlust bei `anlass`"* — und
eine Zusammenfassung machte daraus *„STALLED, der LLM-Generator hängt"*.
`anlass` ist ein **Hash des Faktentextes**, und ein Verlust dort ist der
**Zweck** der Stufe.

> ⚠️ **Fünfte Regel: eine Zahl ohne ihre Bedeutung ist eine Einladung zur
> schlimmsten Deutung.** Wo eine Prüfung einen Verlust meldet, muss dabeistehen,
> ob er eine **Bremse** (gewollt, spart einen Aufruf), eine **Lücke** (hier
> fehlt etwas) oder ein **Urteil** (gefragt und verworfen) ist. Das Projekt
> unterscheidet das seit dem 14.08. im Trichter — die Prüfausgabe tat es nicht.


**Und eine sechste Regel, am selben Tag aus derselben Quelle:** das Werkzeug
nannte nur die **größte** Verlustquelle. Am 24.08. waren das 3 Symbole an der
**Bremse** — und sie verdeckte 2 Symbole an einer **Datenlücke**.

> ⚠️ **Eine Lücke wiegt schwerer als eine Bremse, auch wenn sie kleiner ist.**
> „Am meisten" ist die falsche Rangfolge für eine Diagnose; „am schlimmsten"
> ist die richtige. Wer nach Häufigkeit sortiert, zeigt zuverlässig das, was
> gewollt ist, und verbirgt das, was fehlt.


### 2.66 Eine Prüfung, die vom Zustand der Produktion abhängt — und die ganze Suite mitreißt (24.08.2026)

**Der Absturz:**

```
File "pruefe_pakete.py", line 2994, in paket_b1
  lang = _marken(_lauf("hebel", "KAUFEN", "LONG")["mails"][0]["text"])
IndexError: list index out of range
```

⚠️ **Auf meinem Rechner grün, auf dem Notebook ein Absturz — bei identischem
Code.** Der Unterschied war die **Datenbank**: `_lauf` läuft gegen die echte
Produktions-DB, und **Cooldown** wie **Anlass-Fingerabdruck** lesen daraus, wann
ETH zuletzt beurteilt wurde. Wo die Produktion gerade läuft, ist ETH gesperrt →
keine Mail → `["mails"][0]` fliegt.

**Zwei getrennte Fehler, und der zweite ist der schlimmere:**

| | |
|---|---|
| **1** | Die Prüfung **hing am Zustand der Produktion**. Dieselbe Klasse wie 2.64 (Kalender), nur mit **Daten statt Datum** — und sie fällt erst auf, seit die Kette wirklich läuft |
| **2** | ⚠️ Sie **stürzte ab, statt rot zu werden**. Ein `IndexError` beendet die **ganze Suite** und nimmt **allen folgenden Paketen** ihr Ergebnis. Der Nutzer sah nie eine Schlusszeile — und damit auch nicht die 1.678 bestandenen Prüfungen davor |

**Die Regeln:**

> **Was eine Prüfung messen will, muss sie von dem trennen, was sie nicht
> messen will.** Diese hier prüft die **Geometrie der Richtung** — nicht, ob
> eine Bremse gerade greift. Also werden die Bremsen für sie **abgeschaltet**
> (`anlass.aktiv: False`, Cooldown 0), statt das Ergebnis dem Zufall des
> Zeitpunkts zu überlassen. Die Bremsen haben ihre eigenen Prüfungen.

> ⚠️ **Und keine Prüfung darf sterben.** `mails[0]` ohne vorherige
> Längenprüfung ist kein Test, sondern eine Wette. Wo ein Ergebnis fehlen
> **kann**, wird es als **roter Punkt** gemeldet — eine Prüfung, die stirbt,
> prüft nichts mehr, und sie nimmt alle anderen mit.

**Behoben:** `_OHNE_BREMSEN` gilt für **alle drei** Läufe des Pakets, und der
Mailzugriff geht über einen Helfer, der eine leere Liste als Befund meldet
statt als Ausnahme.

### 2.67 Eine Verbindung ohne `row_factory` ist derselbe Fehler an einer zweiten Stelle (24.08.2026)

**Der Fund:** `database.db.get_latest_prices()` wurde am selben Tag gehärtet,
weil sie `row["symbol"]` bei einer Verbindung ohne `row_factory = sqlite3.Row`
mit `TypeError: tuple indices must be integers or slices, not str` sterben
ließ. Wenige Stunden später, am Notebook: derselbe Fehler, andere Funktion —
`agent.krypto.backward_tracking.compute_ausstiegs_empfehlungen()` liest ihre
eigene SELECT-Abfrage genauso ungeschützt.

⚠️ **Am Desktop unsichtbar, weil die Testverbindung dort nie eine Position
erreicht, die diesen Zweig betritt.** Am Notebook, mit echtem Bestand, griff
der Zweig — und legte offen, dass `paket_15`s eigene Testverbindung
(`c = sqlite3.connect(":memory:"); q.backup(c)`) selbst kein `row_factory`
gesetzt hatte, anders als die Nachbarblöcke in derselben Datei.

**Die Regel:** *ein* gefundener `row_factory`-Fehler ist ein Hinweis, keine
Erledigung. Wer ihn an einer Funktion behebt, sollte **dieselbe Datei nach der
Geschwisterfunktion durchsuchen** — dieselbe Unachtsamkeit tritt selten genau
einmal auf. Behoben durch dasselbe Muster wie bei 2.61: die Funktion setzt
`row_factory` jetzt selbst (mit Save/Restore, damit die Einstellung des
Aufrufers hinterher unverändert gilt), statt sich auf den Aufrufer zu
verlassen.

### 2.68 Eine Zahl aus der lebenden Produktions-DB veraltet mit deren Wachstum (24.08.2026)

**Drei Prüfungen fielen am Notebook, obwohl der Code unverändert war:**

| Prüfung | erwartet | Notebook | Desktop |
|---|---:|---:|---:|
| „die leeren sind alle Abweisungen" | 78 | 416 | 78 |
| „die Migration legt die Tabelle an und ist idempotent" | `True / False` | `[] / []` | `True / False` |
| „12. Perzentil ins unterste Band, 74. ins dritte von vier" | Band 0/2 | Band 0/0 | Band 0/2 |

**Der gemeinsame Fehler:** alle drei lesen eine Zahl **aus der echten,
wachsenden Produktions-DB** und vergleichen sie gegen einen zum Schreibzeitpunkt
abgeschriebenen Wert — statt, wie die meisten Nachbarprüfungen im selben
Paket, eine **Kopie zu leeren und mit bekannten synthetischen Zeilen zu
füllen**. Auf einer Desktop-DB, die seit dem Schreiben der Prüfung nicht mehr
gewachsen ist, hält der Wert zufällig. Auf einer 24/7 laufenden
Produktions-DB nicht — die Abweisungen wachsen, die Migration ist längst
gelaufen, die Merkmalsverteilung verschiebt sich.

⚠️ **Das ist dieselbe Fehlerklasse wie 2.66, nur ohne Absturz.** Dort hing eine
Prüfung am *Zustand* der Produktion (gesperrt/nicht gesperrt), hier hängt sie
an einer *Zahl* der Produktion (Zeilenzahl, Bereits-migriert-Status,
Perzentilverteilung). Beides ist „was die Prüfung messen will" nicht sauber
von „was sie nicht messen will" getrennt.

**BEHOBEN (24.08.2026, selbes Datum):**

| Prüfung | Fix |
|---|---|
| „die leeren sind alle Abweisungen" | Vergleich gegen die **Gesamtmenge** leerer Zeilen statt gegen `78` — die Aussage „die leeren sind ALLE Abweisungen" ist umgebungsunabhängig prüfbar, ihre absolute Zahl nicht |
| „die Migration legt die Tabelle an" | `DROP TABLE IF EXISTS` auf der Kopie **vor** dem ersten Aufruf — stellt den Ausgangszustand her, den die Prüfung voraussetzt, statt ihn anzunehmen |
| „12. Perzentil ins unterste Band" | ⚠️ **Korrektur an der eigenen Diagnose**: die Bandbildung selbst ist rein deterministisch (`merkmale()`/`_prozent()`/`_band_grob()` hängen an KEINER Population) — nicht die Zahl war die Ursache, sondern `next(iter(bilanz))`, das den erstbesten Schlüssel aus tausenden echten Konstellationen nahm statt den erwarteten nachzuschlagen. Behoben: der erwartete Schlüssel wird vorausberechnet und gezielt in `bilanz` gesucht |

**Lehre aus der dritten Zeile:** eine plausible Diagnose („die Population hat
sich verschoben") kann falsch sein, obwohl das SYMPTOM zur Fehlerklasse
passt. Die Korrektur kam erst durch Lesen der tatsächlichen Bandfunktion,
nicht durch das Muster der ersten beiden Funde auf den dritten zu
übertragen.

### 2.69 Eine Prüfung veraltet auch, wenn nur das PROJEKT wächst — nicht nur seine DB (24.08.2026)

**„alle Reihen liegen in USD" fiel am Notebook** mit `{'USD', 'EUR'}` statt
`{'USD'}`. Anders als 2.68: hier wuchs keine Zeilenzahl — der PROJEKTUMFANG
wuchs. Die Prüfung stammt von vor dem Multi-Asset-Umbau, als jede Kursreihe
Krypto und damit USD war. Seither sind ETF/Aktien/Rohstoffe live, und
`lade_reihen_aus_db()`s eigener Docstring hält fest: ein reiner USD-Filter
„machte die ETF-Klasse unsichtbar" — **EUR bei einem Nicht-Krypto-Symbol ist
der erwartete Zustand, kein Defekt.**

**Behoben:** die Prüfung filtert jetzt auf die Krypto-Symbole der Watchlist
(`assetklasse == "krypto"`), bevor sie „alles USD" verlangt — genau der
Ausschnitt, den die nachfolgenden Prüfungen (USD→EUR-Umrechnung für `atr_eur`)
tatsächlich brauchen.

**Die Regel:** eine Prüfung, die „ALLE X haben Eigenschaft Y" behauptet, ist
nur so lange richtig, wie die Menge X nicht wächst. Ein Umbau, der eine neue
Anlageklasse einführt, kann eine Jahre alte, nie geänderte Prüfung stillschweigend
falsch machen — ohne dass an der Prüfung selbst etwas „kaputtgegangen" wäre.

### 2.70 Ein Text-Regex, der auf ein Schlüsselwort statt auf die Zeilenform prüft, findet die falsche Zeile (24.08.2026)

**Der Befund:** eine Prüfung verglich den geparsten SHORT-Stop gegen den
Kurs und schlug am Notebook wiederholt fehl. Die eigentliche Rechnung war
die ganze Zeit korrekt — bestätigt unabhängig über den NB-Export (73 von 73
echten SHORT-Einstiegssignalen haben Stop > Einstieg). Der Fehler lag im
**Test-Parser** `_marken()`: er suchte nach der ersten Zeile, die die
Zeichenkette `"Stop "` enthält. Bei einer Bestandsposition erzeugt die
Mail vor der eigentlichen Rechnung einen eigenen Absatz mit einer
Trailing-Stop-Empfehlung („Stop         auf 1.918 EUR nachziehen…") — die
enthält dasselbe Schlüsselwort und stand textlich zuerst.

**Die Regel:** ein Substring-Test auf ein Schlüsselwort ist nicht dasselbe
wie ein Test auf eine Zeilen-FORM. „Enthält das Wort" matcht jede Erwähnung;
„beginnt mit dem Wort, gefolgt von der Zahl" matcht nur die eine Zeile, die
gemeint war. Behoben: `_marken()` verlangt jetzt, dass die Zeile mit dem
Schlüsselwort beginnt UND das nächste Wort eine Zahl ist.

### 2.71 Wer eine Tabelle wipt, muss ALLE Tabellen wipen, die dieselbe Funktion liest (24.08.2026)

**Der Befund:** eine isolierte MFE-Prüfung (Kopie geleert, fünf synthetische
Zeilen eingefügt) fiel am Notebook mit „7 statt 5 Zeilen" und einem
verfälschten `mfe_r`-Wert. Ursache: die geprüfte Funktion
(`compute_ausstiegs_empfehlungen()`) liest zwei Tabellen, `signals` UND
`hebel_signals` — gewiped wurde nur die erste. Die Kopie war sonst die
volle Produktions-DB; am Notebook lag darin eine echte offene Position, die
sich unter demselben Symbol in das Ergebnis mischte.

**Die Regel:** „isolierte Testdaten" heißt: isoliert von JEDER Tabelle, die
der Code unter Test liest — nicht nur von der naheliegendsten. Bei einer
Funktion, die mehrere Tabellen zusammenführt, muss die Isolation ALLE
davon abdecken, sonst bleibt eine stille Hintertür zur echten Produktions-DB
offen, die erst auffällt, wenn dort zufällig ein passender echter Datensatz
liegt.

### 2.72 Ein „hat sich etwas geändert?"-Test misst jeden Schreiber, nicht nur den geprüften (24.08.2026)

**Der Befund:** eine Prüfung hashte die Produktionsdatei vor und nach einem
Trockenlauf, um zu belegen, dass er nichts schreibt. Sie war an einem Tag
**dreimal rot und zweimal grün — ohne jede Codeänderung.** Am Notebook
schreibt der 24/7 laufende Scheduler in dieselbe Datei; ob der Test anschlug,
hing davon ab, ob dessen 15-Minuten-Takt zufällig ins Messfenster fiel.

⚠️ **Der geprüfte Code konnte den Fehler gar nicht verursachen:** die
übergebene Verbindung war längst eine In-Memory-Kopie. Die Prüfung maß etwas,
das sie nie messen wollte.

**Die dritte Spielart der 2.66-Familie:**

| | was von der Produktion abhing |
|---|---|
| 2.66 | ihr **Zustand** (Symbol gesperrt oder frei) |
| 2.68 | eine **Zahl** (Zeilenzahl, Migrationsstatus) |
| **2.72** | die **Zeitgleichheit** eines fremden Schreibers auf derselben Datei |

**Die Regel:** ein Vorher/Nachher-Vergleich beweist nur dann etwas über den
geprüften Code, wenn **niemand sonst** das Verglichene anfassen kann. Wo ein
fremder Prozess dieselbe Datei beschreibt, ist die Frage nicht entscheidbar
— egal wie sorgfältig gehasht wird.

**Die Lösung ist Isolation, nicht Toleranz:** den geprüften Code auf eine
**eigene Kopie** zeigen lassen (hier über den ohnehin vorhandenen
`db=`-Parameter, der bis zu allen Fakten-Modulen durchgereicht wird — am Code
nachgesehen, nicht angenommen). Das macht den Test **stärker** als vorher:
eine Änderung dort kann nur vom Lauf kommen. Die Alternative — den Test bei
erkanntem Fremdschreiben „durchwinken" — hätte ihn zu einem Test gemacht, der
sich selbst abschaltet.

⚠️ **Und die Positivkontrolle gehört dazu:** ein grüner „nichts geändert"-Test
ist ein Nullbefund. Verifiziert wurde deshalb beides — der Hash bleibt bei
Nichtstun gleich UND schlägt nach einem einzigen `INSERT` an.

### 2.73 Wo die Prüfausgabe landet — und warum der Dateiname das Gerät trägt (24.08.2026)

`pruefe_pakete.py` schreibt seinen **vollständigen** Konsolentext zusätzlich
nach Google Drive:

```
Claude_Austauschordner\Pruefungen\pruefe_pakete_ausgabe_<GERAET>.txt
```

**Warum überhaupt:** die Ausgabe ist ~240 KB. Externe Zusammenfassungen davon
haben sie an einem Tag zweimal unbrauchbar gemacht — einmal bei 20.010 Zeichen
abgeschnitten (die Schlusszeile mit der Prüfzahl fehlte), einmal an einem
Zeitdeckel. Mehrfach wurden dabei **absichtliche Testfehler und normale
Betriebsmeldungen als kritische Systemfehler gedeutet**. Der Volltext an einem
festen Ort macht die Deutungsschicht überflüssig: **Rohzeilen zählen.**

**Warum mit Gerätenamen** (`platform.node()` — Desktop `9900K`, Notebook
`T440`): ohne ihn schreiben beide Geräte in dieselbe Datei, und wer zuletzt
schreibt, gewinnt — ohne jede Kennzeichnung. Genau das ist passiert: ein
eigener Desktop-Verifikationslauf überschrieb das frische Notebook-Ergebnis,
und um ein Haar wäre „0 FEHL" gemeldet worden, ohne den echten Befund je
gesehen zu haben. Eine Kopfzeile im Text nennt Gerät und Zeitstempel
zusätzlich.

**How to apply — beim Auswerten:**

| | |
|---|---|
| **1** | **Den DATEINAMEN prüfen, nicht nur den Zeitstempel.** Zwei Geräte können binnen Minuten schreiben |
| **2** | **Die Schlusszeile lesen** (`N Pruefungen, …`). Fehlt sie, ist der Lauf abgebrochen — der `finally`-Block schreibt trotzdem, die Datei ist dann nur unvollständig (erkennbar auch an der Größe: ~240 KB vollständig) |
| **3** | `grep -c "^  FEHL"` gegen die Schlusszeile gegenprüfen |

⚠️ **Best effort, nie blockierend:** fehlt das Laufwerk, scheitert nur der
Schreibversuch (eine Konsolenzeile), nicht die Suite. Der Laufwerksbuchstabe
kommt aus `extract_notebook_diagnose._google_drive_wurzel()` — **nie raten**,
er ist je Gerät verschieden.

⚠️ **Eigener Ordner, NICHT `Notebook_Analysedaten`:** Testergebnisse sind
**Code-Korrektheit**, der NB-Export ist **Produktionszustand**. Beides in
dieselbe Ablage zu legen wäre genau die Verwechslung, die schon einmal
Fehldeutungen erzeugt hat.


---

### 2.74 Eine Betriebskonstante, die in die Messgröße eingeht, ist eine Annahme DER MESSUNG (25.08.2026)

`messe_marken.py:43-46` schreibt über die Totzone `NIVEAU_MIN_ABSTAND_ATR = 0.5`:

> *„Das ist eine Eigenschaft des Betriebs, keine Annahme dieser Messung, und
> sie bleibt unangetastet.“*

Der Satz klingt sauber und ist falsch. Der Vorfilter H prüft **A** = kein
Widerstand in [+0,5 ATR, +4,0 ATR) und **B** = eine Unterstützung in
(−2,0 ATR, −0,5 ATR]. **Beide Bänder beginnen an der Totzone.** Die Zahl 0,5
ist damit keine Anzeigeeinstellung neben der Messung, sondern eine
**Bandgrenze in der Messgröße selbst**.

⚠️ **Dieselbe Denkfigur hat achtzehn Kapitel gekostet.** Der Betriebssatz
1,50 % stand ebenso da — als Gegebenheit des Betriebs, nicht als Annahme — und
war der falsche Maßstab für die Frage „ist das ein guter Trade" (Kap. 119).
Und die Herkunft macht es nicht besser, sondern schlechter: 0,5 ATR entstand
am 10.08. als Reparatur einer **Anzeigepanne** („Widerstand 0,0
Schwankungsbreiten höher" für jeden Prüffall).

**Die Regel:** Bevor eine Konstante als „Betrieb, bleibt unangetastet“ aus der
Prüfung genommen wird, ist eine Frage zu beantworten: **geht sie in die
Definition der gemessenen Größe ein?** Wenn ja, ist sie ein Parameter der
Messung und gehört in die Sensitivitätsprüfung — unabhängig davon, wo sie im
Code steht und warum sie einmal eingeführt wurde.

**Der Prüfsatz:** „Betrieb“ ist eine Aussage über den **Ort** einer Zahl, nie
über ihre **Rolle**. Nur die Rolle entscheidet, ob sie geprüft werden muss.

Angewandt in `Vorabfestlegung_S1_S4_H_Annahmen_25_08.md` (S1).

---

### 2.75 Eine Methodikregel gilt erst, wenn das NÄCHSTE Werkzeug sie auch befolgt (25.08.2026)

Regel **2.47** verlangt seit dem 20.08. wandernde Blockgrenzen:

> *„Blockgrenzen wandern je Lauf — feste Grenzen lassen immer dieselben Anker
> gemeinsam reisen und verschmälern die Verteilung.“*

An der Quelle geprüft, wer sie befolgt:

| Werkzeug | Blockgrenzen | Code |
|---|---|---|
| `messe_marken.py` | ✔ wandernd | `v = int(rngb.integers(0, a.blocklaenge))` (:413) |
| `messe_struktur_bereinigt.py` | ✔ wandernd | ebenso (:265) |
| `bewerte_neu.py` | ✘ **fest** | `if not gr or ii - gr[-1][0] >= 250:` (:205) |
| `messe_klassen.py` | ✘ **fest** | (:191) |
| `messe_ueberleben.py` | ✘ **fest** | (:194) |
| `messe_dosis.py` | ✘ **fest** | (:298) |

⚠️ **Die vier mit festen Grenzen sind genau die, die die heute gültigen
H-Urteile erzeugt haben** — Kap. 117 (Dosis), 119 (H trägt, +4,5 gegen +2,6),
120 (je Kategorie), 121 (Überlebensverzerrung, 523 Reihen). Die Regel wurde
geschrieben, nachdem die alten Werkzeuge sie befolgten, und die **neuen** haben
sie nie übernommen. Niemand hat es bemerkt, weil eine Methodikregel im Text
steht und nicht in einer Prüfung.

**Was daraus folgt — zwei Dinge, und das zweite ist das wichtigere:**

1. Die Wirkung ist zu messen (S3 der Vorabfestlegung). Die **Richtung ist nicht
   vorhersagbar**: 2.47 sagt „feste Grenzen verschmälern, also Schwelle zu
   niedrig“, 2.48 maß bei gleicher Läufezahl das Gegenteil (+18,4 fest gegen
   +16,8 wandernd) — dort dominierte die **Läufezahl**, nicht die Grenzenart.
2. **Eine Methodikregel ohne Prüfung ist eine Absichtserklärung.** Dies ist
   dieselbe Lehre wie „Naht statt Absichtserklärung“ und „eine Stufe gilt erst
   als gebaut, wenn das Werkzeug sie in der fertigen Ausgabe nachweist“ — nur
   eine Ebene höher: sie trifft die **Messmethodik selbst**.

**Maßnahme:** Dauerprüfung analog `finde_freie_namen.py` — ein Skript, das alle
`messe_*.py` / `bewerte_*.py` auf die Blockbildung absucht und meldet, wo
Grenzen fest gesetzt werden. Sonst wiederholt sich das beim nächsten Werkzeug.

---

### 2.75 Nachtrag — S3 gemessen: die Regel hatte recht (25.08.2026)

Die Wirkung ist gemessen (Vorabfestlegung S1–S4, Nachtrag 1). Ergebnis:

| | greedy+fest (Altzustand) | raster+fest | raster+wandernd |
|---|---:|---:|---:|
| Kap. 119 gesamt | **+3,11** | +4,00 | +3,36 |
| Kap. 121 Large | **+5,3** | +5,7 | +6,2 |

**Der Altzustand liefert in beiden Kapiteln die niedrigste von drei geprüften
Schwellen** — die Richtung, die 2.47 vorhersagt. Spanne je **0,9 Punkte** bei
2×Streufehler 0,17–0,19: kein Rauschen. **Ein Urteil kippt** (Large: „trägt
auch aus acht" → „ZU KNAPP"). Der Messwert selbst ist in allen Varianten
bitgleich — die Blockbildung berührt **nur** die Schwelle.

⚠️ **Und eine Lehre über den Vergleich selbst.** „Wandernde Grenzen" ändern
zwei Dinge zugleich: die **Lage** der Schnitte und das **Verfahren** (greedy
schneidet ab dem ersten Anker weiter, ein Raster auf festen Linien). Bei
dichten Ankern sollte das gleich sein; es war es nicht (477 gegen 484 Reihen
mit zwei Blöcken). Erst ein dritter Lauf, der das Verfahren allein umstellt,
machte die Zahlen interpretierbar. **Wer zwei Dinge zugleich umstellt, misst
ihre Summe** — auch dann, wenn beide „dasselbe" zu tun scheinen.

Offen: `messe_klassen` und `messe_dosis` sind noch nicht umgestellt; Kapitel
117 und 120 stehen unter demselben Vorbehalt.

---

### 2.76 Eine Teilung, deren Nummerierung aus einer MENGE stammt, teilt bei jedem Start anders (25.08.2026)

Zwei S3-Läufe desselben Werkzeugs meldeten für die **volle** Stichprobe exakt
dieselben Zahlen (13.768 H-Fälle) — für die **halbe** aber verschiedene
(7.474 gegen 7.069). Die Ankermenge war also identisch, ihre **Nummerierung**
nicht.

Nachgeprüft: `_reihen_roh` liefert die Symbole je Prozess in anderer
Reihenfolge. Zweimal aufgerufen:

```
Lauf 1:  BNB, BIO, NEAR, RENDER, ETH, XLM, SUI, XNO
Lauf 2:  ETH, XNO, RENDER, S, TAO, BIO, INJ, IMX
```

Die SQL ist sortiert (`order by symbol, currency, date`) — die Permutation
entsteht **danach**, über eine Menge, deren Iterationsreihenfolge am
String-Hash hängt (in Python je Prozess randomisiert). Da die Reihen-ID `r`
die **Position** in dieser Reihenfolge ist, wählt `(r % 2) == 1` bei jedem
Start eine andere Hälfte.

⚠️ **Folge für einen bestehenden Befund:** die Zeile *„halbe Stichprobe: +2,8
gegen Schwelle +3,3, nicht bestätigbar"* aus Kapitel 119 ist **eine Ziehung
unter vielen möglichen**, kein reproduzierbarer Befund. Sie darf als
„Auflösungsgrenze" nicht mehr zitiert werden, solange nicht über viele
Teilungen gemittelt wird.

**Die Regel:** Eine Teilung (Symbolhälften, Zeithälften, Faltungen) braucht
eine **inhaltliche, stabile** Kennung — das Symbol selbst, ein Datum, ein
Hash über den Namen mit festem Startwert. Eine **Position** in einer
Datenstruktur ist keine Kennung, solange nicht bewiesen ist, dass die
Reihenfolge über Prozessgrenzen hinweg gleich bleibt.

**Der Prüfsatz:** Wenn dasselbe Werkzeug zweimal gestartet dieselbe Teilung
liefern muss, dann prüfe genau das — einmal, mit zwei Aufrufen. Das kostet
weniger als der Befund, den es rettet.

---

### 2.77 Die Permutation muss die Grenze respektieren, die man befragt (25.08.2026)

Die Frage lautete: *„Fällt H's Vorsprung mit dem Ankeralter?"* Der erste
Aufbau bildete Permutationsblöcke **innerhalb** jedes Altersbands. Zwei
Fehler auf einmal:

**Zu grob.** Die Bänder sind 250 Handelstage breit, die Blocklänge ist es
auch — je Reihe und Band entstand etwa **ein** Block. Die Permutation konnte
nichts mischen, die Verteilung wurde künstlich breit: Schwelle **+16,3**
Punkte, wo der Messwert +5,2 beträgt. Das allein ist schon Methodik 2.52.

**Und die falsche Nullhypothese — das ist das Eigentliche.** Wer fragt, ob
das Alter einen Unterschied macht, muss zulassen, dass unter der
Nullhypothese ein Ausgang aus einem späten Band genauso gut in einem frühen
stehen könnte. Blöcke innerhalb des Bands verbieten genau diese Bewegung —
sie halten fest, was zur Disposition steht.

**Der korrigierte Aufbau permutiert über die ganze Reihe:** die
Bändergrenzen bleiben stehen, die Ausgänge wandern hindurch, die
Blockstruktur hält die zeitliche Abhängigkeit fest. Die Schwellen sanken auf
plausible +4,06 / +7,16 / +5,43, und die vorab benannte Differenz wurde
messbar (+4,30 gegen Schwelle +3,18).

**Die Regel:** Die Permutation muss genau die Struktur zerstören, deren
Wirkung geprüft wird — und alles andere erhalten. Wird nach einer
Gruppengrenze gefragt, muss das Gemischte **über** sie hinweg laufen.
Blöcke, die innerhalb der befragten Gruppe bleiben, beantworten eine andere
Frage.

**Der Prüfsatz:** Kann unter meiner Permutation ein Wert die Grenze
überschreiten, um die es geht? Wenn nein, misst der Placebo nicht die These.

⚠️ **Nebenbefund derselben Runde:** die Positivkontrolle lief zunächst gar
nicht — sie landete auf einer Zelle mit 203 Fällen, unter `MIN_FAELLE = 300`,
und lieferte `NaN`, was als „durchgefallen" ausgegeben wurde. **Ein `NaN` ist
kein Nullbefund, sondern eine nicht gelaufene Messung.** Zellfilter müssen an
die Mindestfallzahl des Werkzeugs gekoppelt sein, nicht an eine eigene Zahl.

---

### 2.78 Eine Zerlegung braucht den Nachweis, dass sie dieselbe Menge zerlegt (25.08.2026)

Kapitel 120/121 wurden nach Ankeralter zerlegt. Bevor irgendeine Zahl gelesen
wurde, war zu klären, ob das Werkzeug überhaupt dieselbe Grundmenge sieht wie
das Kapitel, das es zerlegt:

| Kategorie | Kap. 121 „ALLE" | Summe der drei Altersbänder |
|---|---:|---:|
| Large | 2.292 | 2.292 |
| Mid | 4.734 | 4.734 |
| Small | 6.540 | 6.540 |

Identisch — kein Anker geht verloren, keiner kommt hinzu. **Erst damit ist die
Zerlegung als Aussage über das Kapitel lesbar** und nicht bloß als eigene
Messung, die zufällig ähnliche Namen benutzt.

**Die Regel:** Wer eine bestehende Kennzahl aufteilt, weist die Summe der
Teile gegen das Ganze aus. Stimmt sie nicht, ist die Zerlegung eine andere
Messung — und darf nicht als Erklärung des Ursprungsbefunds auftreten.

⚠️ **Zweiter Punkt derselben Runde: eine stille Zuordnung, die genau die
geprüfte Gruppe trifft.** `messe_klassen._kategorie` rechnet
`u = f["umsatz"] or 0.0` — ein **fehlender** Umsatz wird zu 0 und landet damit
in der kleinsten Kategorie, „Small". Wer Small beurteilt, beurteilt also
teilweise die Datenlücke. Hier war der Anteil klein (1,0 % aller Anker, 1,4 %
von Small) und das Ergebnis unverändert; das war **vorher nicht bekannt**.

**Der Prüfsatz:** Wohin fallen die Fälle, für die das Merkmal FEHLT? Landen
sie in genau der Gruppe, über die geurteilt wird, ist das Urteil ohne diesen
Ausweis nicht lesbar.
