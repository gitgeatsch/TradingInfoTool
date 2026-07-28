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

Diese acht Punkte werden IMMER kurz durchgegangen, auch wenn der Anlass für den
Export etwas anderes war - Auffälligkeiten ausserhalb der eigentlichen Fragestellung
nicht ignorieren (siehe z.B. den ISOC/X136-Ticker-Fund, der nebenbei beim
Durchgehen von Punkt 6 auffiel).

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

---

## 3. Verwandte Dokumente

- [[Fakten_Entscheidungsmappe.md]] - Entscheidungsraster für Fakten/Prompt-Regeln
  selbst (was landet wie im LLM-Prompt), ergänzt diese Methodik (wie wird eine
  Änderung an diesen Fakten getestet und verifiziert).
- `Regelwerksmanual.md` - dokumentiert einzelne, bereits umgesetzte Regeln/Fixes
  inklusive ihres Verifikationsstands: ab jetzt mit der Stufen-Bezeichnung aus
  Abschnitt 0 statt einem unscharfen "erledigt".
