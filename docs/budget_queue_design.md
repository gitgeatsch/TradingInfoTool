# Gemeinsame Budget-Queue: Spot-Rotation + Marktscan + Hebel-Empfehlungen

Status: **Implementiert und gegen echte Daten verifiziert (2026-07-14,
Phase 5)** — siehe `agent/krypto/budget_allocator.py` und
`docs/hebel_positionsformel.md` Abschnitt "Phase 5" für Details/Fund-
Lektionen (u.a. Cerebras' echte Rate-Limits per API-Header bestätigt, Cerebras-
Overflow additiv statt nur "nicht vertagen", Cooldown ohne neue Tabelle über
bestehende Zeitstempel gelöst).

## Ausgangslage

Drei Verbraucher wollen sich dasselbe Groq-Tagesbudget (`llama-3.3-70b-versatile`,
~15-18 echte Calls/Tag) teilen:

1. **Spot-Rotation** (`signal_batch.py`, bestehend) — kein Trigger, reine
   Staleness-Rotation, ~7,7 Calls/Tag Grundbedarf (54 Assets / 7-Tage-Schwelle)
2. **Marktscan-Kaufkandidaten** (`marktscan.py`, bestehend) — Trigger-basiert
   (Score-Schwelle), automatischer Groq-Zweig aktuell bewusst deaktiviert
   (`groq_automatisch_kaufkandidaten: false`), weil er keine Budget-Bremse hat
3. **Hebel-Empfehlungen** (neu, noch nicht spezifiziert/gebaut) — Trigger-basiert
   (Screening alle 15 Min), volle Empfehlungskomplexität lt. Spezifikation
   (Long/Short, Zonen, Forecast) — braucht dieselbe Genauigkeit wie Spot-Signale

Ohne gemeinsame Logik entsteht ein Burst-Problem: mehrere gleichzeitig
getriggerte Kandidaten (Marktscan und/oder Hebel) können an einem Tag locker
das Budget sprengen, während die bestehende Spot-Rotation drumherum leer ausgeht.

## Design: 3 Prioritäts-Stufen + Budget-Reserve

Statt eines einzigen kontinuierlichen Scores (der über die drei sehr
unterschiedlichen Verbraucher hinweg schwer fair kalibrierbar wäre) drei
klare Stufen, jede mit ihrer eigenen internen Sortierung:

| Stufe | Verbraucher | Interne Sortierung | Begründung für die Stufe |
|---|---|---|---|
| **1 (höchste)** | Hebel-Trigger | Trigger-Schwere (0-100) | Marktereignis, zeitkritisch |
| **2** | Marktscan-Kaufkandidaten | `score_gesamt` (0-100) | Neue Chance, zeitsensibel aber weniger akut als ein aktives Marktereignis |
| **3 (niedrigste)** | Spot-Rotation | Tage seit letztem echten Signal | Routine-Auffrischung, hat eingebauten Puffer (7-Tage-Schwelle bei ~4-Tage-Ist-Rotation) |

### Verteilungsformel (pro Tag/Lauf)

```
B = Tagesbudget gesamt (config.yaml, aktuell 15)
F = Reserve fuer Spot-Rotation (Vorschlag: 5) - garantiert Grundrotation
    auch an sehr aktiven Tagen, damit sie nie komplett verhungert

verfuegbar_1_2 = B - F
tier1_verbraucht = min(anzahl_hebel_kandidaten, verfuegbar_1_2)
rest_fuer_2 = verfuegbar_1_2 - tier1_verbraucht
tier2_verbraucht = min(anzahl_marktscan_kandidaten, rest_fuer_2)
rest_fuer_3 = B - tier1_verbraucht - tier2_verbraucht   # >= F, ausser Tier 1 allein
                                                          # sprengt schon B - F
tier3_verbraucht = min(anzahl_faelliger_spot_assets, rest_fuer_3)
```

An einem ruhigen Tag (wenig Hebel/Marktscan-Aktivität) bekommt Spot-Rotation
den ganzen Rest, nicht nur die Reserve F. Nur an einem echten Ausnahmetag
(z.B. Markt-Crash triggert viele Hebel-Kandidaten gleichzeitig) darf Tier 1
auch unter die Reserve F drücken — das ist ein bewusster Kompromiss: ein
Markt-Crash-Tag rechtfertigt tatsächlich mehr Aufmerksamkeit für Hebel als
für Routine-Rotation.

### Cooldown pro Kandidat

Jeder Kandidat bekommt einen Cooldown-Schlüssel (`quelle:symbol`), **3-4
Stunden (Nutzer-Entscheidung 2026-07-13, unsicher/vorläufig wie andere
Schwellenwerte im Projekt)**. Verhindert, dass ein einzelnes, andauernd
auffälliges Asset (z.B. dauerhaft extreme Funding-Rate über mehrere
15-Min-Zyklen) das Budget allein aufbraucht. Nach Ablauf des Cooldowns darf
es erneut in die Queue.

### Kombinierte Calls bei Überschneidung

Bevor die drei Listen final abgearbeitet werden: Prüfen, ob ein Symbol
gleichzeitig in Tier 1 (Hebel) UND Tier 3 (Spot-Rotation, weil ohnehin heute
fällig) auftaucht. Falls ja: EIN Call mit erweitertem Schema (optionales
`hebel_empfehlung`-Feld zusätzlich zum normalen Signal-Schema) statt zwei
separater Calls — spart den doppelten System-Prompt-/Facts-Overhead. Gilt
nur für den Überschneidungsfall, kein genereller Fix.

## Cerebras-Overflow (Nutzer-Entscheidung 2026-07-13, hybrid)

Statt Cerebras nur als Notfall bei komplettem Groq-Ausfall zu behandeln:
**Groq zuerst (bis Tagesbudget B erschöpft), dann übernimmt Cerebras
(`gpt-oss-120b`) den Rest, bevor ein Kandidat auf den nächsten Zyklus
vertagt wird.** Gilt für **alle 3 Stufen** (Hebel, Marktscan, UND
Spot-Rotation — ursprünglich nur für Stufe 1+2 vorgeschlagen, nach
zusätzlicher Prüfung auf alle 3 ausgeweitet, siehe Testergebnisse unten).

**Qualitäts-Tracking statt einmaligem Freigabe-Gate:** jedes Signal bekommt
den tatsächlich genutzten Anbieter/Modell vermerkt (bestehende
`signals.groq_model`-Spalte wiederverwendbar, haelt z.B. auch
`"cerebras:gpt-oss-120b"`), damit sich Cerebras-Qualität über echte
Produktionsdaten laufend beobachten laesst statt nur einmalig zu testen.

**Fallback-Kette bei Doppel-Ausfall:** Falls auch Cerebras fehlschlägt
(eigenes Kontingent leer oder API-Fehler) - KEIN weiterer automatischer
Rueckfall auf eine unsicherere Stufe, sondern schlicht "heute überspringen,
nächster Zyklus erneut versuchen" (bestehendes Prinzip: nie blind auf einen
unsicheren Pfad ausweichen).

### Testergebnisse, die zur Entscheidung führten (2026-07-13)

Gegen `agent/krypto/analyst.py::SYSTEM_PROMPT` getestet (read-only DB-Zugriff
+ 2 gezielt konstruierte synthetische Szenarien, kein Produktionsschreiben):

- **5 echte Facts-Datensätze** (Produktions-DB, 5 verschiedene Symbole) →
  5/5 JSON/Schema gültig, 2 KAUFEN-Vorschläge beide mit korrekter CRV-Zonen-
  Mathematik (3.0 und 4.77)
- **Veto-Stresstest** (synthetisch, `kauf_erlaubt=false` erzwungen) → korrekt
  HALTEN, Veto-Grund explizit benannt - härteste Sicherheitsregel unter
  direktem Druck eingehalten
- **Bull-Stresstest** (synthetisch, eindeutig bullische Konfluenz) → KAUFEN,
  Zonen sauber aus echten Referenzpunkten (Support/Resistance/Fibonacci)
  abgeleitet statt erfunden, `halte_kriterium` vollständig, CRV 2.04 (über
  Pflichtgrenze, aber knapp - kein großer Puffer)

**Bekannte Grenze:** insgesamt 7 Testfälle, keine Tranchen-Faelle, keine
Core-Asset-Sonderregel (Rule 7) getestet, keine VERKAUFEN/TAUSCHEN-Faelle
(Produktions-DB hatte bisher 0 echte KAUFEN/VERKAUFEN-Signale zum Abgleich).
Deshalb laufendes Tracking statt "einmal getestet, für immer vertraut".

## Nicht verlorene Kandidaten bei Budget-Erschöpfung

Kandidaten, die an einem Tag nicht mehr drankommen, werden NICHT als
"fehlgeschlagen" markiert:
- **Hebel:** bleibt in der `hebel_triggers`-Tabelle offen, wird beim nächsten
  15-Min-Screening-Lauf neu bewertet (hält die Marktbedingung an, wird es
  automatisch wieder vorgeschlagen — kein Datenverlust, keine Sonderlogik)
- **Marktscan:** bleibt als `kaufkandidat` in `marktscan_candidates` stehen,
  wird beim nächsten Scan-Lauf (2x/Tag) neu bewertet (Score kann sich bis
  dahin ändern — das ist gewünscht, keine "eingefrorene" Warteschlange)
- **Spot-Rotation:** bleibt schlicht überfällig, rutscht beim nächsten Lauf
  automatisch nach oben (bestehendes Verhalten, unverändert)

## Nachtrag (2026-07-21): Revision - "keine eingefrorene Warteschlange" war ein Trugschluss

Die obige Design-Entscheidung (2026-07-13, vor jeder echten Produktionsdatenlage
getroffen) ging implizit davon aus, dass ein re-bewerteter Kandidat "einfach
wieder vorgeschlagen wird" und das reicht. Echte Produktionsdaten (2026-07-21,
Budget-Allocator-Neuplanung, siehe Plan-Datei swift-napping-muffin.md)
widerlegen das: reines `score_gesamt`-DESC-Ranking OHNE jede Wartezeit-
Erinnerung fuehrte zu bis zu 116h (Hebel) bzw. 5,7 Tagen Median (Marktscan)
Wartezeit, weil ein Kandidat von frischeren/hoeher gescorten Konkurrenten
zyklenlang verdraengt werden konnte - der bestehende 48h-Verfall-Backstop
(oben, "Cooldown pro Kandidat") griff dabei nachweislich NIE, weil er nur das
Alter der jeweils neuesten (bei fortlaufender Requalifizierung immer frischen)
Zeile pruefte.

**Fix (implementiert):** `agent/krypto/budget_allocator.py::
_priorisiere_nach_wartezeit()` teilt jede Kandidatenliste in "ueberfaellig"
(wahre Wartezeit seit Erstkandidatur >= `hebel_kandidat_sla_stunden`/
`marktscan_kandidat_sla_stunden`, konfigurierbar) und "normal" - Ueberfaellige
werden IMMER zuerst eingereiht (FIFO unter sich), unabhaengig vom Score. Der
bestehende `[:tier_n]`-Deckel aus `_verteile_budget()` bleibt unveraendert -
das aendert nur die Reihenfolge, nicht die Kapazitaet. Zusaetzlich per
Portfolio-Bonus (bereits gehalten/`rolle=='core'`) individuell verkuerzbar,
siehe `database/db.py::get_portfolio_prioritaets_bonus_je_symbol()`.

**Historischer Backtest** (`backtest_budget_allocator_sla.py`, gegen echte
Notebook-Historie): Hebel-Maximum 116,1h -> 52,5h (-55%), Marktscan-Median
137h -> 0,1h (Marktscan-Zahlen wegen duenner Historie - nur 8 Coins/12 Tage -
weniger belastbar als Hebel, Richtung aber konsistent). Median/Durchschnitt
bei Hebel leicht gestiegen (3,3h->6,7h) - der erwartete, akzeptierte
Kompromiss einer echten Fairness-Garantie gegenueber einem reinen Greedy-
Score-Ranking.

Diese Design-Entscheidung ("keine eingefrorene Warteschlange") gilt damit als
**revidiert**, nicht als fehlerhaft implementiert - der urspruengliche
2026-07-13-Gedanke war vernuenftig, bevor echte Mehrwochen-Produktionsdaten
zeigten, dass er ohne Wartezeit-Gedaechtnis zu unbegrenzter Verdraengung
fuehren kann.

## Architektur-Konsequenz für bestehenden Code

**Entschieden (2026-07-13): Option A — zentralisieren, UND der manuelle
Button bleibt zusätzlich erhalten.** Der automatische Groq-Zweig, der aktuell
INNERHALB von `marktscan.py::run_scan()` sitzt (und deaktiviert ist), wird
**herausgelöst** und in den neuen zentralen Allocator verschoben —
`run_scan()` liefert nur noch bewertete Kandidaten, OHNE selbst zu
entscheiden, ob/wann Groq gerufen wird.

**Der bestehende manuelle UI-Klick-Button bleibt vollständig erhalten** —
er ist strukturell schon ein getrennter Aufrufpfad
(`generate_candidate_writeup()` wird sowohl vom manuellen Klick als auch vom
Automatik-Zweig aufgerufen, siehe Docstring in `marktscan.py`). Der manuelle
Button ist damit weiterhin für "diesen einen Kandidaten will ich JETZT sofort"
nutzbar, unabhängig davon, ob die automatische Queue ihn heute sowieso
verarbeitet hätte.

**Wichtiger Fix dabei (Fund 2026-07-13):** Der manuelle Marktscan-Button
zählt AKTUELL NICHT gegen das gemeinsame Tagesbudget (schreibt in
`marktscan_candidates`, nicht in `signals` — nur Letzteres zählt
`count_real_signals_today()`). Das ist inkonsistent zum bestehenden
Spot-Signal-Einzel-Klick-Button, der schon korrekt mitzählt. Wird im Zuge
dieser Arbeit behoben: der manuelle Marktscan-Button prüft künftig ebenfalls
das verbleibende Tagesbudget und wird bei Erschöpfung blockiert/mit Warnung
versehen (Verhaltensänderung ggü. heute — bisher funktioniert der Klick immer
sofort). Ohne diesen Fix wäre "manuell" ein Schlupfloch am Budget vorbei.

## Neue/geänderte Dateien — ALLE erledigt (2026-07-14, Phase 5)

- **Neu:** `agent/krypto/budget_allocator.py` — Kandidaten aus allen Quellen
  gesammelt, Stufen-Logik angewendet, Cooldown geprüft (über bestehende
  Zeitstempel statt neuer Tabelle, siehe unten), Groq-dann-Cerebras-Ausführung
- **Neu:** `agent/krypto/llm_provider.py` — Provider-Erkennung für
  Qualitäts-Tracking (welcher Anbieter hat dieses Signal erzeugt), von
  `pipeline.py` und `hebel_pipeline.py` gemeinsam genutzt
- **Geändert:** `marktscan.py` — automatischer Groq-Zweig entfernt,
  `run_scan()` liefert nur noch Kandidaten; manueller Button bleibt, bekommt
  eine Budget-Warnung (kein hartes Blockieren) vor dem Call
- **Geändert:** `database/db.py` — KEINE generische Cooldown-Tabelle nötig
  (bestehende Zeitstempel in `hebel_signals`/`marktscan_candidates.
  groq_generiert_am` reichen), stattdessen 2 neue Abfrage-Funktionen
  (`get_pending_marktscan_kaufkandidaten()`, `count_real_marktscan_writeups_today()`)
  + `get_latest_marktscan_writeup_at()` für den Cooldown-Check
- **Geändert:** `scheduler/background.py` — Allocator-Aufruf huckepack auf dem
  bereits bestehenden 15-Min-`hebel_screening_job`; fixer
  05:00-`signal_batch_job`-Cron entfernt (Funktion + Registrierung), manueller
  Batch-Button bleibt (Nutzer-Entscheidung)
- **Geändert:** `api/cerebras.py` — Rate-Limiter nachgerüstet (siehe Fund oben)
- **Geändert:** `main.py` — `CerebrasClient`-Konstruktion (P-8, optional wie
  Groq/Bitpanda/FRED), an `build_scheduler()` durchgereicht

## Status der Design-Entscheidungen

1. ~~Reserve-Wert F~~ — **bestätigt: 5** (2026-07-13)
2. ~~Cooldown-Dauer~~ — **bestätigt: 3-4 Stunden** (2026-07-13, unsicher/vorläufig)
3. ~~Marktscan-Automatik-Zweig~~ — **bestätigt: Option A (zentralisieren) +
   manueller Button bleibt zusätzlich, mit Budget-Fix** (2026-07-13)

## Noch offen (separate Themen, nicht Teil dieser Queue selbst)

4. ~~Trigger-Schwellenwerte für Hebel-Screening~~ — **erledigt** (Phase 1,
   `agent/krypto/hebel_screening.py`, siehe `docs/hebel_positionsformel.md`)
5. ~~Hebel-Empfehlungsschema~~ — **erledigt** (Phase 4, `agent/krypto/
   hebel_analyst.py`, siehe `docs/hebel_positionsformel.md`)

Das Budget-Queue-Design selbst ist jetzt vollständig implementiert (siehe
oben) — nichts mehr offen aus diesem Dokument.
