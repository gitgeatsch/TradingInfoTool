# Rollout am Notebook — Gesamtpaket vom 14.09.2026

> **Ein Durchgang, in dieser Reihenfolge.** Das Notebook läuft bis dahin auf dem
> Stand vom 13.09. früh (Commit `2f0c73f`). Dieses Paket bringt die Arbeit von
> zwei Tagen — nicht nur eine Reparatur.

## Was im Paket steckt

| Schritt | Was sich im Betrieb ändert | Befund |
|---|---|---|
| 54 | **Terminmarkt-Daten:** eigener Job `terminmarkt` (alle 15 min, alle Kryptowerte). `positionierung` liest nach der Uhr: älter als 2 h → „keine aktuelle Angabe" statt alter Zahl. Mail bei 6 h Gesamtausfall oder 24 h je Wert. | 2.452-gebaut |
| 56 (1) | **Umlaufmenge für turnover:** `externe_reihen` holt SplyCur täglich von Coin Metrics in die Betriebsdatenbank. Ohne das wäre turnover am Notebook ausgefallen. | 2.453-turnover-gebaut |
| 49B | turnover = Binance-Stückvolumen / SplyCur — dieselbe Größe wie die Messung, 60 statt 33 Werte | 2.419 |
| 48 | Ausstiege gestakter Werte bekommen einen Mailabschnitt; der Kurs zur Ausstiegsempfehlung wird gespeichert (neue Spalte) | 2.402, 2.428 |
| 31 / 41 | Mail gestrafft, drei SHORT-Falschaussagen korrigiert, Richtung im Betreff | 2.446, 2.447 |
| 32 | Oberfläche: alte Analyse-Knöpfe stillgelegt mit Hinweis, Detailansicht der Rollen-Kette | 2.448-umsetzung |
| 51 | Stummmeldung für gehaltene Werte ohne Messreihe | 2.442 |
| 50B | Datenfrische nennt „X von Y Symbolen" | 2.425 |

⚠️ **Nicht im Paket:** die Verkaufsbewertung (Schritt 43, Detailplanung folgt), die Punkte aus Schritt 55 und 56 (2)–(8).

## 1 · Vorher am Notebook

```
git status
git log -1 --format="%h %s"
```

- Erwartet: Commit `2f0c73f`. Lokale Änderungen höchstens in `Basisinfos/config.yaml` (Watchlist, Schalter) — **dieses Paket ändert `config.yaml` nicht**, ein Pull kollidiert damit nicht.
- Andere lokale Änderungen: **nicht verwerfen**, erst ansehen (`git diff`).
- Die tägliche Sicherung der Datenbank liegt im Austauschordner (`DB_Backups`). Die Migration ist additiv (vier neue Spalten in `signals`), ein Rückweg bleibt möglich.

## 2 · Pull und Neustart

```
git pull
```

Danach **die App neu starten** — ein Pull lädt den Code nicht in den laufenden Prozess.

## 3 · Kontrolle — frühestens 30 Minuten nach dem Neustart

```
python pruefe_rollout_14_09.py
```

Nur lesend, startet keinen Job, ruft keine Börse auf.

| Zeile | Erwartet |
|---|---|
| neue Module importierbar | OK |
| Terminmarkt: Werte in 30 Minuten | OK bei ≥ 35 (rund 39 Werte haben Terminmarkt-Daten) |
| BTC bekommt frische Terminmarkt-Zahlen | OK — „OI-Änderung erst nach 8 Stunden" ist erwartet |
| Umlaufmenge / `umlaufmengen` | OK bei ≥ 55 (rund 61) |
| `signals.kurs_bei_empfehlung_eur` | OK oder WARTEN (entsteht beim ersten Umlauf) |
| Datenfrische terminmarkt / coinmetrics_splycur | frisch |

Bei **WARTEN**: in 15 Minuten wiederholen. Bei **FEHLER**: der Grund steht in der Zeile; im Log nach `Terminmarkt-Sammlung` bzw. `Umlaufmenge` suchen.

Optional, ebenfalls nur lesend:

```
python pruefe_pakete.py --paket TerminmarktDaten
```

```
python pruefe_pakete.py --paket Umlaufmenge
```

## 4 · Die ersten 24 Stunden — was normal ist

- **In den ersten 8 Stunden** fehlt die OI-Änderung in den Terminmarkt-Sätzen; bei den 13 Juli-Werten fehlt rund 7,5 Stunden die Einordnung von Finanzierungsrate und Kontenanteil. Der Satz sagt das.
- **Mailbetreffs** der Signale nennen jetzt die Richtung, z. B. „(Hebel, LONG)".
- **Neue Hinweismails** möglich: „Terminmarkt-Daten seit … nicht aktualisiert" (nur bei echtem Ausfall).
- **Bekannt, nicht neu:** eine Datenfrische-Meldung zum Bestand kann ein Fehlalarm sein (2.453-bestand, Schritt 56).
- Die Mail „WARNUNG – keine OI-Daten für X" kommt nicht mehr (ersetzt).

## 5 · Rückweg, falls nötig

Auf den vorherigen Commit wechseln und die App neu starten. Die neuen Spalten und die neue Quelle in `externe_reihe` stören den alten Code nicht (additiv).
