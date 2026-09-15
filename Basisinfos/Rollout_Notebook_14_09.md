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

Nur lesend, startet keinen Job, ruft keine Börse auf. Der Volltext landet zusätzlich in `Claude_Austauschordner/Pruefungen/pruefe_rollout_14_09_<Gerätename>.txt` — der Laufwerksbuchstabe wird je Gerät gesucht (Notebook G:, Desktop K:).

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
- Der Fehlalarm zum Bestand (Job datenfrische, refresh_bitpanda_holdings) ist mit dem **Nachtrag** behoben (2.453-bestand-gebaut).
- Die Mail „WARNUNG – keine OI-Daten für X" kommt nicht mehr (ersetzt).

## 5 · Rückweg, falls nötig

Auf den vorherigen Commit wechseln und die App neu starten. Die neuen Spalten und die neue Quelle in `externe_reihe` stören den alten Code nicht (additiv).

## Nachtrag 14.09. abends — zweiter Pull

Gefunden nach dem Einspielen, alles in einem Commit:

| Was | Wirkung | Befund |
|---|---|---|
| Fehlalarm Bestand | die Datenfrische misst den Bitpanda-Abgleich statt der Mengenänderung; Jobname korrigiert | 2.453-bestand-gebaut |
| **Export brach ab** | `extract_notebook_diagnose.py` scheiterte seit dem Pull vom 13.09. an `veto_art` (auch die Übersichtsseite, Veto-Schatten) | 2.453-veto |
| Export prüft Schritt 54 | neuer Abschnitt `terminmarkt_und_umlaufmenge`, Auffälligkeiten in der Konsole | 2.453-export |

**Ablauf:** `git pull` → **App neu starten** (Laufzeitcode geändert) → nach 30 Minuten `python pruefe_rollout_14_09.py` → danach der Export:

```
python extract_notebook_diagnose.py
```

In der Konsole stehen dann die Zeilen **Terminmarkt**, **Umlaufmenge** und **Datenfrische**. Erwartet: Terminmarkt rund 39 Werte in 30 Minuten, Umlaufmenge 61 von 66, Datenfrische ohne `bestand`.


## Nachtrag 15.09. — die Pulls vom 14. spät bis 15.09.

| Commit | Was | Wirkung | Befund | am Notebook |
|---|---|---|---|---|
| `928b04d` | **Ampel** | Binance/Bybit/OKX werden nicht mehr rot, wenn ein Wert dort nur nicht gelistet ist | 2.454-ampel-gebaut | ✔ geprüft 15.09. |
| `04b69d3` | **Laufzeit-Kennzahl** | die Pause zwischen zwei 15-Minuten-Läufen zählt nicht mehr als Ausfall (26,8 statt 85,5 %) | 2.454-laufzeit-gebaut | ✔ geprüft 15.09. |
| `f5337da` | **Kursreihen** | S&P-Referenz im Tagesjob, Nachladen nach Handelstagen, Frische je Wert mit Mail | 2.453-kurs-gebaut | ✔ Export 15.09. 00:41: SPY 14.09., 62 Werte frisch |
| `8bedff5` | **Zugangsschlüssel** | FRED-Schlüssel nicht mehr im Klartext in Datenbank, Log und Export; beim Start wird der gespeicherte Eintrag bereinigt | 2.453-fredkey-gebaut | ⏳ Pull ausstehend |
| `0c22b77` | **Hebel-Abgleich** | Fällt der Abgleich der Hebelpositionen mit Bitpanda 1 Stunde lang aus, kommt eine Mail; die Hebelführungs-Mail nennt dann den Positionsstand | 2.455-hebelabgleich-gebaut | ⏳ Pull ausstehend |
| *(nächster Commit)* | **Kapitalkurse** | Kursreihen-Job täglich 05:30 statt 24 h ab Start; der Portfoliowert lädt einen fehlenden Handelstagskurs nach; fehlt er in Yahoos Tageshistorie, kommt der Schlusskurs aus dem letzten Handel des Platzes | 2.455-kapitalkurse-gebaut | ⏳ Pull ausstehend |

**Ablauf für `8bedff5`:** `git pull` → **App neu starten** (Laufzeitcode: `main.py`, `database/db.py`) → danach der Export:

```
python extract_notebook_diagnose.py
```

Erwartet in der Konsole des Exports zusätzlich (frühestens 15 Minuten nach dem Start): `Hebel-Abgleich: letzter Erfolg <heute> (vor 0,x h, Grenze 1 h), offen: keine`. Steht dort `noch kein erfolgreicher Lauf`, ist der Abgleich seit dem Start nicht gelungen. Erwartet: der Export enthält den Schlüssel nicht mehr (am Desktop gegengeprüft: 8 Treffer → 0). ⚠️ Die **alten Log-Dateien** am Notebook tragen ihn bis zur Rotation weiter; der Export maskiert sie. Die **bisherigen Exporte und DB-Sicherungen** im Austauschordner enthalten ihn noch — der Schlüssel ist kostenlos, ein neuer ist optional.

**Nach dem Pull von „Kapitalkurse" – woran man es am Notebook sieht (Log, ab dem nächsten Morgen):**

- 05:30 `Aktien-OHLC-Refresh …` und gegebenenfalls `Kursluecke CEBS: Tageskerze … fehlt in Yahoos Historie - Schlusskurs … aus dem letzten Handel (XETRA, …) eingesetzt`
- 06:30 `Tageswert <gestern>` an einem Werktag **ohne** fortgeschriebene Börsentitel; am Wochenende weiter mit (richtig)
- in den Tagen danach `Schlusskurs-Rueckfall … durch die echte Tageskerze ersetzt: alt -> neu (±x %)` – die Selbstprüfung. Eine WARNING (über 0,5 %) wäre ein Befund.
