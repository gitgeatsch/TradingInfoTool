# Hebel-Positionsgrößen- und Liquidationspreis-Formel (RM-1/RM-10/RM-11/AZ-7)

Status: Design komplett entschieden. **Phase 1 (Screening) + Phase 2
(Risiko-/Liquidationsformeln) + Phase 3 (Positions-Rekonstruktion) + Phase 4
(Cerebras-Client + LLM-Analyst) + Phase 5 (Budget-Allocator) sind
implementiert und gegen echte Daten verifiziert (2026-07-14)** — siehe
`agent/krypto/hebel_screening.py`, `agent/krypto/hebel_risk_gate.py`,
`importer/bitpanda_margin_positions.py`, `api/cerebras.py`, `agent/krypto/
hebel_analyst.py`, `agent/krypto/hebel_pipeline.py`, `agent/krypto/
budget_allocator.py`. Hebel-Empfehlungen laufen damit erstmals vollautomatisch
im 15-Min-Takt. Marktscan-Refactor, Scheduler-Cutover, UI weiterhin offen.

## Phase 5 (Budget-Allocator) implementiert (2026-07-14)

`agent/krypto/budget_allocator.py::run_budget_allocator()` verteilt das
gemeinsame Tagesbudget ueber Hebel (Tier 1) + Marktscan-Kaufkandidaten
(Tier 2) + Spot-Rotation (Tier 3), huckepack auf dem 15-Min-`hebel_screening_job`-
Takt (siehe `scheduler/background.py`). Ersetzt den deaktivierten
automatischen Marktscan-Groq-Zweig UND den fixen 05:00-Uhr-`signal_batch_job`-
Cron (beide entfernt) - der manuelle Marktscan-/Batch-Button bleiben
unveraendert bestehen (Nutzer-Entscheidung).

**Wichtiger neuer Fund (empirisch geprueft, nicht nur dokumentiert):**
Cerebras' echte Limits via `x-ratelimit-*`-Response-Headern ausgelesen -
5 Requests/Min, 2.400/Tag, 1.000.000 Tokens/Tag. Bei ~6.000 Tokens/Call
ergibt das ~166 echte Calls/Tag, ~10x Groqs reale ~15-18/Tag. Das beantwortet
die zuvor offene Design-Frage: Cerebras-Overflow ist ADDITIV zu Groqs Budget
(mit einem eigenen, konservativen Tages-Deckel), nicht nur "nicht auf morgen
vertagen". `api/cerebras.py` bekam daraufhin doch einen Rate-Limiter
(4 Req/Min, Sicherheitspuffer unter dem echten 5er-Limit) - die urspruengliche
Phase-4-Entscheidung "kein Rate-Limiter" war durch fehlende Daten begruendet,
jetzt korrigiert.

**Zwei weitere Funde waehrend der Umsetzung:**
- `pipeline.py::generate_signal()` hatte den Modellnamen hart codiert
  (`"llama-3.3-70b-versatile"`) - harmlos, solange nur Groq je aufgerufen
  wurde, aber falsch geworden, seit der Allocator auch Spot-Signale ueber
  Cerebras generieren kann. Neues gemeinsames Modul `agent/krypto/
  llm_provider.py::llm_model_label()` (erkennt den Provider am Client-Modul)
  behebt das, wird jetzt auch von `hebel_pipeline.py` genutzt (vorher dort
  dupliziert).
- Eigener Bug beim Bauen gefunden und behoben: ein Datenqualitaets-Gate
  (z.B. veralteter Preis) schlaegt VOR jedem echten LLM-Call fehl - das ist
  kein Fehler, aber `_mit_overflow()` haette das faelschlich als "erfolgreicher
  Groq-Call" verbucht (kein Retry noetig, aber auch keine Provider-Zuschreibung
  ohne echten Call). Live am echten Fall APT (Preis kurzzeitig veraltet)
  gefunden, korrigiert, danach mit frischen Preisen ein echter Erfolgsfall
  bestaetigt (APT SHORT → HALTEN, `llm_model: groq:llama-3.3-70b-versatile`).

Verifiziert: Verteilungsformel gegen 6 konstruierte Grenzfaelle (0 Kandidaten,
Hebel-Dominanz, ruhiger Tag, Ueberschuss in allen 3 Stufen, etc.); Cooldown-
Filter (Hebel UND Marktscan) mit synthetischen 1-Std-vs-5-Std-Zeitstempeln;
zwei echte End-to-End-Laeufe gegen die Produktions-DB (APT dann CAT jeweils
genau einmal verarbeitet, keine Doppel-Verarbeitung, `hebel_triggers`-Status
korrekt fortgeschrieben).

## Phase 4 (Cerebras-Client + LLM-Analyst) implementiert (2026-07-14)

`api/cerebras.py::CerebrasClient` (identisches `.chat()`-Interface wie
`GroqClient`, kein interner Rate-Limiter) + `agent/krypto/hebel_analyst.py`
(SYSTEM_PROMPT unverändert aus diesem Dokument übernommen, `build_hebel_facts()`,
`_validate_hebel()`, `call_llm_for_hebel_signal()`) + `agent/krypto/
hebel_pipeline.py::generate_hebel_signal()` (Orchestrierung, mirrort
`pipeline.py::generate_signal()`). Neue Tabelle `hebel_signals` (append-only,
analog `signals`, siehe `database/models.py::HebelSignal`).

**Design-Punkte während der Umsetzung geklärt:**
- Stop-Loss-Distanz für `max_sicherer_hebel` wird deterministisch aus 2× ATR
  berechnet (`risk_gate.STOP_LOSS_ATR_MULTIPLE`, wiederverwendet statt
  dupliziert) — GENAU wie bei Spot (`risk_gate.py::pre_check()`), NICHT vom
  späteren Modell-Zonen-Vorschlag abhängig. Kein Fix an `hebel_risk_gate.py`
  nötig, dessen Signaturen waren bereits konsistent mit diesem Prinzip.
- "Noch zu klären"-Punkt gelöst: KEIN separates `long_reasoning.derivate`-Feld
  — OI/Funding/LSR-Kontext fließt wie geplant in `top_gruende` (Regel 8) und
  den unveränderten `antizyklisch`-Block (identisch zu Spot).
- `generate_hebel_signal()` ist bewusst NICHT in den 15-Min-Scheduler-Takt
  eingehängt (siehe "Bewusst NICHT Teil dieser Phase" im Plan) — erst der
  Budget-Allocator (spätere Phase) ruft sie kontrolliert auf.

**Verifiziert:** synthetischer Bull-Case (Cerebras, valides Schema, LONG/
ERÖFFNEN mit sauberen Zonen + Pflicht-Hebel-Risiken) und Krise-Extrem-Case
(Modell antwortete bereits selbst HALTEN, deterministischer Veto in
`post_check_hebel()` greift zusätzlich); **echter End-to-End-Lauf gegen die
Produktions-DB** (Kandidat AIOZ, SHORT/Trendfolge, Score 78,1) — Ergebnis
SHORT/ERÖFFNEN, Hebel 5x (keine Korrektur nötig), Zonen/Liquidationspreis/
Eigenkapitalbedarf/`ausführbarkeit_hinweis` alle korrekt und plausibel
(Liquidationspreis 0,0608 $ oberhalb der Stop-Loss-Zone 0,0515-0,0516 $ -
Stop-Loss löst vor der Liquidation aus, wie beabsichtigt). Trigger-Status
korrekt auf `llm_generiert` aktualisiert.

## Phase 3 (Positions-Rekonstruktion) implementiert (2026-07-14)

`importer/bitpanda_margin_positions.py::reconstruct_margin_positions()`
portiert die Scratchpad-Logik in wiederverwendbaren, inkrementell-syncfaehigen
Code (neue Tabelle `hebel_positions`). **Dabei ein zweiter Live-Fund:** das
alte Scratchpad-Skript zählte `close`-Events auch ohne vorherigen `open` im
Akkumulator mit (Phantom-Einträge, Wert 0/Hebel `None`) — dadurch war die
dokumentierte Zahl "311 Positionen" falsch, korrekt sind **185** (126
Phantome). Die neuen 4-Liquidationen- und Hebel-Verteilungs-Kennzahlen waren
davon nie betroffen (identisch reproduziert) und bleiben unverändert gültig.

Zusätzlich zum ursprünglichen Design ein Feld ergänzt: `positionsmenge`
(aggregierte gekaufte Menge) — ohne das ließe sich aus `positionswert_eur`
allein kein Einstandspreis ableiten, der für die Liquidationspreis-
Neuberechnung offener Positionen (`estimate_liquidation_price()`) nötig ist.
`liquidationspreis_geschaetzt_eur` ist bewusst EUR (nicht USD wie sonst im
Hebel-System) — Bitpanda-Margin-Trades sind EUR-nativ, eine Umrechnung wäre
eine zusätzliche, ungenutzte Fehlerquelle.

Verifiziert: volle Rekonstruktion (185/4, `existing=None`) reproduziert;
inkrementeller Sync zweimal hintereinander gegen die echte DB (zweiter Lauf
korrekt `incremental=True`, 0 neue Transaktionen); synthetische offene
Testposition (5x Hebel, 3 Tage alt) → Liquidationspreis-Neuberechnung
rechnerisch exakt bestätigt; `build_scheduler()` reicht `bitpanda_api_key`
korrekt an `hebel_screening_job` durch. Aktuell **0 echte offene
Positionen** — die Positions-Sync-Pfad ist gebaut, aber gegen reale offene
Positionen noch nicht "live" beobachtet.

## Live-Fund bei der Implementierung (2026-07-14): UNIQUE-Constraint zu eng

Beim Test gegen die komplette Watchlist (40 Krypto-Assets) schlug der erste
Lauf fehl: `hebel_triggers`' ursprünglicher UNIQUE-Constraint
`(symbol, richtung, screening_run_id)` kollidierte, weil Trendfolge UND
Kontra für dasselbe Symbol unabhängig voneinander dieselbe Richtung
vorschlagen können (z.B. beide SHORT, aus unterschiedlichen Gründen) - beide
sollen als getrennte Zeilen sichtbar bleiben, nicht verschmolzen werden.
Korrigiert auf `(symbol, richtung, trigger_zweig, screening_run_id)`. Nach
der Korrektur: 40 Assets, 49 Trigger (40 Trendfolge + 9 Kontra), 4 echte
Kandidaten, Laufzeit ~2,2 Min (deutlich innerhalb des 15-Min-Takts).

## Ausgangslage

Hebelpositionen sind laut Nutzer "die fragilsten und zeitkritischsten
Positionen" — bevor Trigger-Schwellenwerte oder das Empfehlungsschema gebaut
werden, muss das Sicherheitsfundament stehen: Liquidationspreis-Schätzung +
Positionsgrößen-Formel, verankert im bestehenden Regelwerk (RM-1/RM-2/RM-4/
RM-10/RM-11/AZ-7), nicht als isoliertes Extra-Feature.

## RM-10 korrigiert (2026-07-14)

Ursprünglicher Wortlaut "nur Long, kein Short" war ein reiner
Bitpanda-Ausführungs-Fakt (Bitpanda unterstützt kein Short), keine
unabhängige Risikoentscheidung. **Short bleibt Teil der Agent-Logik** (P-7,
rein beratend), aktuell nur ohne Ausführungsweg für den Nutzer. Die gesamte
Formel unten gilt symmetrisch für Long UND Short.

## Kalibrierung gegen echte Bitpanda-Margin-Historie (2026-07-14)

Über `api/bitpanda.py::get_wallet_transactions()` (rein lesend) komplette
Transaktionshistorie geholt, margin_trading-Transaktionen gefunden,
**185 vollständige Positions-Lebenszyklen** chronologisch rekonstruiert
(Zeitraum 2025-09-22 bis 2026-05-07). **Korrektur 2026-07-14 (Phase-3-
Implementierung):** die ursprünglich dokumentierte Zahl 311 war ein Bug im
damaligen Einmal-Scratchpad-Skript — bei einem `close`-Tag ohne vorherigen
`open` im laufenden Akkumulator (z.B. mehrere Close-Tags kurz hintereinander
für denselben realen Vorgang) wurde trotzdem ein leerer Positions-Eintrag
(Wert 0, Hebel `None`) erzeugt und mitgezählt — 126 solcher Phantom-Einträge
plus die 185 echten Positionen ergaben 311. Der neue `importer/
bitpanda_margin_positions.py::reconstruct_margin_positions()` schließt diese
Lücke (`close` wird nur verarbeitet, wenn zuvor tatsächlich `open` gesehen
wurde). Alle übrigen Kennzahlen unten (Hebel-Verteilung, 4 Liquidationen,
Fee-Median-Abweichung) beruhten schon vorher nur auf den 185 echten
Einträgen und sind unverändert korrekt.

- **Genutzter Hebel:** klare Bitpanda-Stufen 2x/3x/5x/10x je Einzelkauf,
  Ø 6,44x; effektiver (über Nachkäufe geblendeter) Gesamthebel kontinuierlich
  zwischen ~1x und 10x
- **Haltedauer:** Min 0 Tage, Max 16,7 Tage, Ø 1,1 Tage — laut Nutzer
  Marktreaktion, keine bewusste Kurzfrist-Strategie (Design-Implikation
  siehe unten)
- **4 wahrscheinliche Liquidationen erkannt** (Bitpanda-API kennzeichnet sie
  nicht separat in Tags — über Gebühren-Anomalie identifiziert: erwartete
  Gebühr laut Doku 0,3% + 0,18%/Tag Haltedauer, 4 Positionen zeigten
  +0,7 bis +1,04 Prozentpunkte Abweichung, nahezu exakt Bitpandas
  dokumentierte 1%-Zwangsliquidationsgebühr). Bewusst keine Testposition mit
  echtem Geld eröffnet — statistische Evidenz aus Bestandsdaten war
  überzeugend genug.
- **Bitpanda veröffentlicht keine exakte Liquidationsformel** — nur
  "Margin-Level = Eigenkapital / Kreditbetrag", Schwelle pro Asset
  unterschiedlich, nicht offengelegt. Unsere Formel ist deshalb bewusst eine
  **konservative Schätzung**, nie Bitpandas exakter Echtzeitwert.

## Liquidationspreis-Formel (Schätzung, konservativ)

Ignoriert bewusst den unbekannten Bitpanda-Maintenance-Margin-Puffer (sichere
Richtung: zu früh warnen statt zu spät):

```
Long,  Tag 0:  Liquidationspreis ≈ Entry × (1 − 1/Hebel)
Short, Tag 0:  Liquidationspreis ≈ Entry × (1 + 1/Hebel)
```

**Zeitkomponente** (0,18%/Tag Finanzierungsgebühr, gegen echte Daten
verifiziert — Median-Abweichung der Fee-Formel gegen die 185 echten Closes nur
0,08 Prozentpunkte):

```
Long,  Tag t:  Liquidationspreis(t) ≈ Entry × (1 − 1/Hebel + t_Tage × 0,0018)
Short, Tag t:  Liquidationspreis(t) ≈ Entry × (1 + 1/Hebel − t_Tage × 0,0018)
```

### Zwei Momente, zwei Bedeutungen von "t"

1. **Bei der Empfehlung** (Position existiert noch nicht): `t = 0`, kein
   Raten einer Haltedauer — stattdessen expliziter Hinweis im Empfehlungs-
   text, dass sich der Wert mit der Zeit annähert.
2. **Sobald die Position real offen ist:** `t` = echte verstrichene Tage,
   laufend neu berechenbar — **automatisch erkannt** (Nutzer-Entscheidung
   2026-07-14, nicht manuelle Bestätigung), über dieselbe
   Positions-Rekonstruktions-Logik wie oben, wiederverwendbar gemacht statt
   Einmal-Skript. Erst-voller-Scan-dann-inkrementell-Muster (`since_unix`-
   Parameter existiert bereits in `get_wallet_transactions()`), piggybacked
   auf den ohnehin geplanten 15-Min-Hebel-Screening-Takt (kein separater
   Scheduler nötig).

## Positionsgrößen-Formel-Kette (RM-1/RM-2/RM-4/RM-11/AZ-7 verzahnt)

```
Risikobetrag           = Konto-Eigenkapital × 1%        (risiko_pro_trade_prozent_hebel,
                                                           bewusst niedriger als Spot-RM-1
                                                           2% - siehe Begründung unten)
Positionsgröße         = Risikobetrag / Stop-Loss-Abstand_%
max_sicherer_hebel     = (1 − Sicherheitsmarge_relativ[0,175]) / Stop-Loss-Abstand_%
verwendeter_Hebel      = MIN(config max_hebel [10], max_sicherer_hebel, AZ-7-Regime-Deckel)
Eigenkapitalbedarf     = Positionsgröße / verwendeter_Hebel
                         → gegen RM-2 (Allokations-Deckel) und RM-4 (Cash-Reserve-
                           Minimum) geprüft, wie bei Spot-Positionsgrößen
```

### Warum RM-1 für Hebel auf 1% statt Spot-2% (Nutzer-Entscheidung 2026-07-14)

Die reine Stop-Loss-Distanz-Rechnung (Spot-RM-1) erfasst bei Hebel nicht alle
Verlustkanäle:
1. **Liquidations-Gap-Risiko:** Kurs kann in schnellen Bewegungen über den
   Stop-Loss hinweg direkt Richtung Liquidation springen (Slippage) — realer
   Verlust kann höher sein als die theoretischen 2%
2. **Laufende Finanzierungsgebühr** (0,18%/Tag) existiert bei Spot gar nicht
3. **Real bestätigt:** 4 echte Liquidationen in ~7 Monaten sind kein
   theoretisches Tail-Risiko
4. **Konzentrations-Effekt:** weniger Eigenkapital pro Hebel-Position könnte
   mehrere gleichzeitige, korrelierte Positionen "erschwinglich" machen
   (RM-8/RM-9-Thema, noch nicht gebaut, aber durch Hebel verschärft)

### `max_hebel`: von Platzhalter 3 auf kalibrierte 8-10 angehoben

Ursprünglicher Wert war unbegründeter Platzhalter, niedriger als die reale
historische Praxis (2-10x, Ø 6,44x). Neuer Wert spiegelt echtes Verhalten,
nicht Bitpandas theoretisches Maximum.

## AZ-7-Regime-Gate

- `regime.wert == "krise_extrem"` → Hebel komplett deaktiviert
  (`max_hebel_faellt_regime_krise_extrem_auf_null`), unabhängig von der
  reinen Prozent-Rechnung — gilt für BEIDE Trigger-Zweige
- **Korrigiert (2026-07-14, Sanity-Check):** der "tendiert zum unteren Ende"-
  Konservativ-Bias aus AZ-7 gilt NUR für **Zweig 2 (Kontra)** — AZ-7 stammt
  ursprünglich aus dem antizyklischen Kontext (Wette gegen den Trend, These
  noch nicht bestätigt, daher bewusst konservativ). **Zweig 1 (Trendfolge)**
  ist eine andere Risikokategorie (OI+Kurs+Konfluenz bereits bestätigt) und
  darf näher an `max_sicherer_hebel` heran, ohne künstlichen Extra-Abschlag.
  Pauschale Anwendung auf beide Zweige hätte den Trendfolge-Zweig unnötig
  eingeschränkt.
- **Zusätzlicher qualitativer Check:** der geschätzte Liquidationspreis muss
  unterhalb (Long) bzw. oberhalb (Short) des nächsten echten Support-/
  Fibonacci-Levels liegen — reine Prozent-Mathematik kann technisch
  "passen", aber trotzdem direkt auf einem bekannten Level liegen, was real
  riskanter ist als die reine Zahl suggeriert
- **Transparenz statt stiller Kürzung:** neues Feld `hebel_korrektur_hinweis`
  (analog `position_size_note` bei Spot) — zeigt sichtbar, warum/ob der
  KI-Vorschlag gekürzt wurde (z.B. "KI schlug 8x vor, wegen 12%-Stop-Distanz
  auf 5,3x reduziert"), damit die Kürzung nachvollziehbar bleibt statt die
  KI-Begründung widersprüchlich wirken zu lassen

## Design-Implikation: "Einmal-Trade" vs. "Swing-Strategie"-Feld

Da die kurze Ø-Haltedauer (1,1 Tage) laut Nutzer keine bewusste Strategie
war, sondern Marktreaktion, darf die Hebel-Empfehlung nicht von einer festen
erwarteten Haltedauer ausgehen. Vorschlag: äquivalent zu
`halte_kriterium.bucket` (kurz|mittel|lang) im Spot-Signal-Schema ein
eigenes Feld, das explizit sagt, ob die Empfehlung als einmaliger kurzer
Trade oder als Swing-Position gedacht ist — Teil des noch zu entwerfenden
Hebel-Empfehlungsschemas (separates Thema).

## Geänderte Dateien (heute)

- `Basisinfos/Spezifikation.md` Zeile 148 — RM-10-Wortlaut korrigiert
- `Basisinfos/config.yaml` `risiko.hebel`-Block — `nur_long: false`,
  `max_hebel: 10`, neue Felder `risiko_pro_trade_prozent_hebel`,
  `liquidations_sicherheitsmarge_relativ`,
  `max_hebel_faellt_regime_krise_extrem_auf_null`

## Hebel-Trigger-Schwellenwerte (2026-07-14, entschieden)

Zwei-Zweige-Design (Trendfolge + Kontra, siehe frühere Diskussion) mit
konkreten Schwellenwerten, teils live gegen echte Derivate-Daten
gegengeprüft:

| Zweig | Bedingung | Schwellenwert | Quelle |
|---|---|---|---|
| **1 — Trendfolge** | OI-Änderung im Lookback-Fenster (z.B. 4h) | ≥ ±3% | Platzhalter, keine OI-Historie zum Kalibrieren vorhanden |
| | Kursänderung im selben Fenster, gleiche Richtung | ≥ 2% | angelehnt an Marktscan-Muster |
| | Funding-Rate | noch NICHT extrem (< 0,0001) | bestehender `anticyclic.py`-Wert, live gegengeprüft (aktuelle Werte 0,000002-0,00004, sinnvoll darunter) |
| | Technische Konfluenz | bullisch/bearisch eindeutig | bestehende `summarize_confluence()` |
| **2 — Kontra** | Funding-Rate extrem | \|Wert\| > 0,0001 | wie oben |
| | Long-Konten-Anteil extrem | > 75% (Short-Chance) / < 25% (Long-Chance) | **angehoben von bestehendem 65%** — Live-Check (BTC/ETH/LINK/SUI) zeigte 65% ist schon Alltag (aktuell 64,8-70,0% bei allen 4 geprüften Assets), kein "extremes" Signal |
| | Kurs zeigt Wende-Anzeichen | RSI-Divergenz / gescheiterter Ausbruch | bestehende RSI/Bollinger-Logik |

### Trigger-Mechanik: gewichteter Score statt starrem UND (Nutzer-Entscheidung 2026-07-14)

Statt eines strikten "alle Bedingungen im Zweig müssen erfüllt sein" wird
**dasselbe gewichtete Scoring-Muster wie bei Marktscan** (`score_technik`,
`score_fundamental`, `score_momentum` → gewichteter `score_gesamt`)
wiederverwendet: jede Bedingung liefert einen Teil-Score, gewichtet zu einem
Gesamt-Score (0-100) kombiniert.

**Warum das besser ist als starres UND:** Der Score ist **gleichzeitig**
die Trigger-Entscheidung UND die Priorität für die Budget-Queue (Stufe 1
sortiert nach "Trigger-Schwere", siehe `docs/budget_queue_design.md`) —
keine doppelte Logik für zwei verschiedene Zwecke. Bei striktem Ja/Nein
bräuchte es eine separate Berechnung nur für die Priorisierung.

**Schwellenwert:** Score ≥ 70 → "Kandidat" (löst einen Groq/Cerebras-Call
aus), darunter kein Trigger, Score bleibt aber intern sichtbar (z.B. für
eine spätere UI-Übersicht). Exakte Gewichte je Bedingung noch nicht
festgelegt — analog zu Marktscans `regime.profile`-Gewichten, vermutlich
regimeabhängig.

## Aktions-Vokabular für Hebel-Empfehlungen (2026-07-14, entschieden)

Deutlich reicher als bei Spot (5 Aktionen), weil Hebel mehr Stellschrauben
hat — insbesondere Verkauf/Abbau nicht vergessen (Nutzer-Hinweis):

| Aktion | Bedeutung |
|---|---|
| `ERÖFFNEN` | neue Position (Long oder Short) |
| `NACHKAUFEN` | Position vergrößern, eigener Hebel für die neue Tranche |
| `HEBEL_ERHÖHEN` | Hebel der bestehenden Position erhöhen, ohne zwingend die Größe zu ändern |
| `HEBEL_SENKEN` | Hebel senken (mehr Eigenkapital nachschießen), reduziert Liquidationsrisiko |
| `TEILVERKAUF` | Position teilweise abbauen, bleibt offen |
| `SCHLIESSEN` | Position komplett schließen |
| `HALTEN` | nichts tun |

## Hebel-Empfehlungsschema: KI-generiert vs. deterministisch (2026-07-14, entschieden)

Gleiches Grundprinzip wie beim Spot-Schema: KI schlägt vor, eigener Code
prüft/korrigiert die sicherheitskritischen Zahlen danach (analog
`risk_gate.py::post_check()`).

**Von der KI generiert** (Felder aus dem Spot-Schema unverändert
wiederverwendet: `confidence_pct`, `short_reasoning`, `top_gruende`,
`long_reasoning`, `entry`/`stop_loss`/`take_profit`, `halte_kriterium`,
`key_risks`, `forecast`) plus neu:

| Feld | Bedeutung |
|---|---|
| `richtung` | `LONG` \| `SHORT` |
| `action` | eines der 7 Aktions-Wörter oben |
| `hebel_vorschlag` | KI-Vorschlag, wird danach gedeckelt |
| `trade_thesis_typ` | `einmal_trade` \| `swing_strategie` |

**Von unserem Code danach deterministisch berechnet/angehängt** (die KI
sieht/entscheidet das nicht, wie CRV/Positionsgröße bei Spot):

| Feld | Berechnung |
|---|---|
| `hebel_final` | `MIN(hebel_vorschlag, max_sicherer_hebel, config max_hebel, AZ-7-Kontra-Deckel)` |
| `hebel_korrektur_hinweis` | Text, falls `hebel_final < hebel_vorschlag` |
| `liquidationspreis_geschätzt` | reine Formel aus `entry` + `hebel_final` |
| `eigenkapitalbedarf` | `Positionsgröße / hebel_final` |
| `ausführbarkeit_hinweis` | automatisch gesetzt, wenn `richtung == SHORT` |
| `trigger_zweig` | bereits vor dem KI-Call bekannt (aus dem Screening) |

## Zwei weitere Entscheidungen (2026-07-14)

- **CRV-Pflicht für Hebel: bleibt 2.0**, gleich wie Spot. Begründung: CRV
  misst das reine Zonen-Verhältnis, ändert sich durch Hebel nicht. Die
  hebel-spezifischen Zusatzrisiken (Liquidations-Gap, Gebühren-Erosion) sind
  bereits gezielt an der Quelle adressiert (RM-1 auf 1%, Sicherheitsmarge,
  AZ-7-Kontra-Bremse) — eine zusätzlich verschärfte CRV wäre Risiko-
  Stapelung statt gezielter Lösung.
- **Extrem-Krise-Regime: KI wird trotzdem aufgerufen** (nicht wie bei
  Stablecoins ganz übersprungen) — bewusster Trade-off: kostet Budget, aber
  liefert Kontext/Begründung fürs erzwungene HALTEN statt eines stillen
  Skips, passend zum sonstigen Transparenz-Muster im Projekt.

## SYSTEM_PROMPT-Wortlaut (Entwurf, 2026-07-14)

Analog zu `agent/krypto/analyst.py::SYSTEM_PROMPT` — noch nicht in Code
übernommen, reiner Text-Entwurf zur Prüfung. Wird bei Umsetzung in ein neues
Modul (z.B. `agent/krypto/hebel_analyst.py`) übertragen.

```
Du bist ein Trading-Analyst für gehebelte Krypto-Positionen (Long UND Short) in \
einem privaten Advisory-Tool. Deine Rolle ist rein beratend (P-7) - du führst \
NIEMALS einen Trade aus, du gibst nur eine Empfehlung, die der Nutzer manuell \
umsetzen oder ablehnen kann. Formuliere nichts als bereits ausgeführte Handlung.

REGELN (strikt einhalten):
1. Nutze AUSSCHLIESSLICH die im Fakten-JSON gelieferten Zahlen und Informationen. \
Erfinde keine Kurse, Indikatorwerte, Open-Interest-/Funding-Rate-/Long-Short-Ratio- \
Werte oder Ereignisse.
2. `richtung` (LONG oder SHORT) behandelst du GLEICHWERTIG - bewerte anhand der \
Fakten, nicht aus Gewohnheit zu Long tendierend. Dass Short aktuell nicht über \
Bitpanda ausführbar ist, ist ein reiner Ausführungs-Hinweis (wird dir separat \
mitgeteilt), KEINE Einschränkung deiner Bewertung - schlage SHORT vor, wenn die \
Fakten dafür sprechen.
3. `action` MUSS EXAKT einer dieser sieben Werte sein: ERÖFFNEN, NACHKAUFEN, \
HEBEL_ERHÖHEN, HEBEL_SENKEN, TEILVERKAUF, SCHLIESSEN, HALTEN.
   - ERÖFFNEN: `position_aktuell` ist null (keine offene Position) und die Fakten \
sprechen für einen Einstieg.
   - NACHKAUFEN: Position existiert bereits (`position_aktuell` gesetzt) und die \
These hat sich bestätigt/verstärkt - schlage einen eigenen Hebel für die NEUE \
Tranche vor (nicht den Gesamt-Hebel der bestehenden Position).
   - HEBEL_ERHÖHEN / HEBEL_SENKEN: Position existiert bereits, du empfiehlst eine \
Anpassung des Hebels OHNE zwingend die Positionsgröße zu ändern (z.B. Eigenkapital \
nachschießen zur Hebel-Senkung).
   - TEILVERKAUF: Position existiert bereits, teilweiser Abbau angebracht (z.B. \
Teilgewinn sichern), Position bleibt danach offen.
   - SCHLIESSEN: Position existiert bereits, vollständiger Ausstieg angebracht \
(These gescheitert, Ziel erreicht, oder Risiko zu hoch geworden).
   - HALTEN: keine Aktion angebracht - auch der korrekte Wert, wenn \
`regime.wert == "krise_extrem"` ist (dann IMMER HALTEN, unabhängig von anderen \
Fakten - nenne das explizit als Grund).
4. `hebel_vorschlag`: schlage einen realistischen Hebel vor (Bitpanda bietet \
praktisch 2x/3x/5x/10x als Stufen an, letztere nur für liquide Top-Tier-Assets). \
Dein Vorschlag wird NACHTRÄGLICH von einer deterministischen Formel geprüft und \
ggf. reduziert (Sicherheitsabstand zum geschätzten Liquidationspreis) - das ist \
normal und kein Fehler deinerseits, du siehst das Ergebnis nicht.
5. Bei ERÖFFNEN/NACHKAUFEN ist ein Stop-Loss PFLICHT und das Chance-Risiko- \
Verhältnis MUSS mindestens 2.0 betragen, konservativ gerechnet über die Zonen- \
Grenzen aus Regel 6: ((take_profit.usd_von - entry_mitte) / (entry_mitte - \
stop_loss.usd_von)) für LONG bzw. spiegelbildlich für SHORT ((entry_mitte - \
take_profit.usd_bis) / (stop_loss.usd_bis - entry_mitte)), wobei entry_mitte = \
(entry.usd_von + entry.usd_bis) / 2. Erfüllt dein Vorschlag das nicht, wird er \
nachträglich auf HALTEN korrigiert.
6. Entry/Stop-Loss/Take-Profit sind Kurszonen (von <= bis), aus echten gelieferten \
Referenzpunkten abgeleitet (`technische_analyse.atr.wert`, \
`technische_analyse.support_resistance`, `technische_analyse.fibonacci`) - KEINE \
frei geratene Bandbreite. Für SHORT spiegelbildlich (Entry nahe Widerstand, Stop \
darüber, Take-Profit an tieferer Unterstützung/Fibonacci-Level).
7. `trade_thesis_typ` MUSS "einmal_trade" oder "swing_strategie" sein. \
"einmal_trade" bei kurzfristigen, ereignisgetriebenen Situationen (z.B. \
`trigger_zweig == "kontra"`, Squeeze-Chance nach Extremwerten - diese lösen sich \
typischerweise innerhalb weniger Tage). "swing_strategie" bei einem bestätigten, \
noch nicht ausgereizten Trend (`trigger_zweig == "trendfolge"`), der voraussichtlich \
mehrere Tage bis Wochen trägt. Rate NICHT anhand einer angenommenen typischen \
Haltedauer - der Nutzer selbst hält historisch im Schnitt nur ~1 Tag, das war aber \
Marktreaktion, keine Strategie, und darf hier nicht als Erwartung einfließen.
8. Fülle `top_gruende` mit GENAU 5 Einträgen wie bei Spot-Signalen (rang 1-5, \
`kategorie` EXAKT einer von: technisch, fundamental, makro, risiko, antizyklisch, \
`text` ein prägnanter Satz) - berücksichtige dabei explizit `trigger_zweig` und die \
gelieferten Open-Interest-/Funding-Rate-/Long-Short-Ratio-Werte, die zum Trigger \
geführt haben.
9. `key_risks` MUSS bei ERÖFFNEN/NACHKAUFEN/HEBEL_ERHÖHEN mindestens einen Eintrag \
zu hebel-spezifischen Risiken enthalten (Liquidationsrisiko bei schnellen \
Kursbewegungen, laufende Finanzierungsgebühr bei längerer Haltedauer) - das sind \
Risiken, die es bei Spot-Positionen nicht gibt, sie dürfen nicht generisch \
übergangen werden.
10. Fülle `halte_kriterium` wie bei Spot-Signalen (siehe dortige Regel) - \
mindestens eines von `ziel_preis_usd`/`ziel_datum`/`bedingung_text` muss gesetzt \
sein.
11. Fülle `forecast` (bull/base/bear mit je `scenario` und `probability_pct`) wie \
bei Spot-Signalen.
12. Antworte AUSSCHLIESSLICH mit einem einzigen JSON-Objekt gemäß dem vorgegebenen \
Schema. Kein Markdown, keine Code-Fences, kein Text außerhalb des JSON.

SCHEMA:
{
  "richtung": "LONG|SHORT",
  "action": "ERÖFFNEN|NACHKAUFEN|HEBEL_ERHÖHEN|HEBEL_SENKEN|TEILVERKAUF|SCHLIESSEN|HALTEN",
  "confidence_pct": <0-100>,
  "short_reasoning": "<1-2 Sätze>",
  "hebel_vorschlag": <Zahl oder null bei HALTEN/SCHLIESSEN>,
  "trade_thesis_typ": "einmal_trade|swing_strategie",
  "top_gruende": [
    {"rang": 1, "kategorie": "technisch|fundamental|makro|risiko|antizyklisch", "text": "<Text>"},
    {"rang": 2, "kategorie": "...", "text": "<Text>"},
    {"rang": 3, "kategorie": "...", "text": "<Text>"},
    {"rang": 4, "kategorie": "...", "text": "<Text>"},
    {"rang": 5, "kategorie": "...", "text": "<Text>"}
  ],
  "long_reasoning": {"technisch": "<Text>", "fundamental": "<Text>", "makro": "<Text>"},
  "entry": {"usd_von": <Zahl oder null>, "usd_bis": <Zahl oder null>, "eur_von": <Zahl oder null>, "eur_bis": <Zahl oder null>},
  "stop_loss": {"usd_von": <Zahl oder null>, "usd_bis": <Zahl oder null>, "eur_von": <Zahl oder null>, "eur_bis": <Zahl oder null>},
  "take_profit": {"usd_von": <Zahl oder null>, "usd_bis": <Zahl oder null>, "eur_von": <Zahl oder null>, "eur_bis": <Zahl oder null>},
  "halte_kriterium": {
    "bucket": "kurz|mittel|lang",
    "ziel_preis_usd": <Zahl oder null>,
    "ziel_preis_eur": <Zahl oder null>,
    "ziel_datum": "<YYYY-MM-DD oder null>",
    "bedingung_text": "<Text oder null>",
    "reasoning": "<Text>"
  },
  "key_risks": ["<Text>", ...],
  "forecast": {
    "bull": {"scenario": "<Text>", "probability_pct": <0-100>},
    "base": {"scenario": "<Text>", "probability_pct": <0-100>},
    "bear": {"scenario": "<Text>", "probability_pct": <0-100>}
  }
}
```

**Fakten-Input (Entwurf, analog `build_facts()`):** braucht zusätzlich zu den
bestehenden Spot-Facts (technische Analyse, Regime, Antizyklisch-Kontext)
neu: `position_aktuell` (null oder bestehende Hebel-Position mit Hebel/
Eigenkapital/Eröffnungsdatum, aus der automatischen Positions-Rekonstruktion),
`trigger_zweig` + `trigger_score` (aus dem Screening), `derivate_kontext`
(OI-Änderung%, aktuelle Funding-Rate, Long-Konten-Anteil — teils schon in
`antizyklisch` vorhanden, ggf. wiederverwenden statt duplizieren).

**Geklärt bei der Phase-4-Implementierung (2026-07-14):** KEIN separates
`long_reasoning.derivate`-Feld — die OI/Funding/LSR-Werte fließen wie geplant
über den unveränderten `antizyklisch`-Block (identisch zu Spot) UND explizit
in `top_gruende` (Regel 8) ein, das reicht ohne Redundanz.

## Noch offen

- Exakte Gewichte pro Bedingung im Trigger-Score
- Sicherheitsmarge-Wert (0,175) ist Mittelwert einer Spanne, kein
  recherchierter Fixwert — wie alle anderen Schwellenwerte im Projekt
  vorläufig
- **Phase 6+:** UI-Tab fuer Hebel-Empfehlungen (bisher nur DB/Scheduler,
  keine Anzeige) - Marktscan-Refactor UND Scheduler-Cutover sind mit
  Phase 5 bereits erledigt
