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
| `9d5d82f` | **Kapitalkurse** | Kursreihen-Job täglich 05:30 statt 24 h ab Start; der Portfoliowert lädt einen fehlenden Handelstagskurs nach; fehlt er in Yahoos Tageshistorie, kommt der Schlusskurs aus dem letzten Handel des Platzes | 2.455-kapitalkurse-gebaut | ⏳ Pull ausstehend |
| `ea816c3` | **Hebelstufen** | Hebelmails zeigen den gerechneten Hebel und die einstellbaren Stufen (untere hervorgehoben, obere mit Überschuss oder „NICHT SICHER“); alle Zahlen rechnen mit demselben Hebel | 2.455-hebelstufen-gebaut | ⏳ Pull ausstehend |
| `ed8f10d` | **OD7-Kurse und Kursangabe** | OD7H und OD7C bekommen wieder echte Kurse (ISIN in Stuttgart statt eingefrorenem Kürzel von 2022) – Kapital rund +420 EUR, ohne Indexsprung; eine tägliche Wache meldet jede tote Kursangabe; G2X, BW, ROL in der Watchlist | 2.455-kurs-od7-gebaut | ✔ Pull + Export 15.09. fehlerfrei; ⏳ 05:30-Teil (K8) |
| `beddca4` | **Krypto-Preisabruf** | Ein unsinnig großer CoinGecko-Wert (ETH-Volumen über 2^63) legte seit 07:49 den ganzen Krypto-Preisabruf lahm; jetzt als Kommazahl, unplausibles Volumen verworfen, jeder Coin einzeln gespeichert | 2.455-preis-ueberlauf | ✔ geprüft 15.09. 21:36: 3 Läufe 44/60, keine Fehler |
| `f5e9990` | **Bestand über die neue Bitpanda-Schnittstelle** | Frei und gestakt je Wallet aus den Buchungen; die doppelt gezählten gestakten Mengen werden korrigiert (Kapital rund −2.440 €, ohne Indexsprung); offene Verkaufssignale gelten nur bei echtem Verkauf als umgesetzt; Mails mit Name, Wert, Status und Aktion | 2.455-bestand-neu-gebaut | ✔ Export 16.09. 19:35: 10 Änderungen wie im Trockenlauf; ⏳ Tageswert am Morgen (K10) |
| `cbc9482` | **Cash und Mailversand** | Cash gesamt, verfügbar und in offenen Orders gebunden (mit Anzahl und ältester Order); die Kaufmail sagt, ob eine Position nur mit aufgelösten Orders passt; eine gescheiterte Mail wird nach 1 Minute wiederholt und am Signal vermerkt; das Protokoll nennt jede Bestandsänderung | 2.455-cash-gebaut | ✔ Export 16.09. 22:09: Cash mit Orderdetails, Mailzählung und Vermerk wirken; ⏳ Cash-Zeile in der Kaufmail, Tageswert am Morgen (K11) |
| `95341c9` | **Papierkorb-Warnung im Export** | Der Export zählt, was er in den Google-Drive-Papierkorb schiebt (alte Sicherungen, alte Exportfassungen), und warnt ab 2 GB; nach dem Leeren einmal `--papierkorb-geleert` | 2.455-drive-papierkorb | ✔ Pull 16.09.; Papierkorb geleert; ⏳ `--papierkorb-geleert` und erste Zeile im nächsten Export |
| *(nächster Commit)* | **Schlüsselüberwachung** | Lehnt Bitpanda einen Schlüssel ab, kommt eine eigene Mail mit Handlung (sofort, dann täglich, Entwarnung wenn es wieder geht); fehlt ein Schlüssel beim Start, eine Mail; Erinnerung 30, 7 und 1 Tag vor dem Ablauf des Fusion-Schlüssels (15.09.2027). Mails nennen nur die Namen der Schlüssel, nie Werte | 2.455-schluessel-gebaut | ⏳ Pull ausstehend (K12) |

**Ablauf für `8bedff5`:** `git pull` → **App neu starten** (Laufzeitcode: `main.py`, `database/db.py`) → danach der Export:

```
python extract_notebook_diagnose.py
```

Erwartet in der Konsole des Exports zusätzlich (frühestens 15 Minuten nach dem Start): `Hebel-Abgleich: letzter Erfolg <heute> (vor 0,x h, Grenze 1 h), offen: keine`. Steht dort `noch kein erfolgreicher Lauf`, ist der Abgleich seit dem Start nicht gelungen. Erwartet: der Export enthält den Schlüssel nicht mehr (am Desktop gegengeprüft: 8 Treffer → 0). ⚠️ Die **alten Log-Dateien** am Notebook tragen ihn bis zur Rotation weiter; der Export maskiert sie. Die **bisherigen Exporte und DB-Sicherungen** im Austauschordner enthalten ihn noch — der Schlüssel ist kostenlos, ein neuer ist optional.

**Nach dem Pull von „Kapitalkurse" – woran man es am Notebook sieht (Log, ab dem nächsten Morgen):**

- 05:30 `Aktien-OHLC-Refresh …` und gegebenenfalls `Kursluecke CEBS: Tageskerze … fehlt in Yahoos Historie - Schlusskurs … aus dem letzten Handel (XETRA, …) eingesetzt`
- 06:30 `Tageswert <gestern>` an einem Werktag **ohne** fortgeschriebene Börsentitel; am Wochenende weiter mit (richtig)
- in den Tagen danach `Schlusskurs-Rueckfall … durch die echte Tageskerze ersetzt: alt -> neu (±x %)` – die Selbstprüfung. Eine WARNING (über 0,5 %) wäre ein Befund.


**Nach dem Pull von „OD7-Kurse und Kursangabe“ – ⚠️ `config.yaml` ist betroffen.** Am Notebook hat `Basisinfos/config.yaml` lokale Änderungen (Watchlist, Schalter). Ein einfacher `git pull` bricht dann ab. Sicherer Weg – die lokalen Änderungen bleiben erhalten:

```
git diff --stat
git stash
git pull
git stash pop
```

- Meldet `git stash pop` einen **Konflikt** in `config.yaml`: **nichts verwerfen**, die Datei bleibt im Stash – Bildschirmfoto von `git status` und `git diff` schicken, dann lösen wir es gemeinsam.
- Danach **App neu starten**.

**Woran man es sieht (K8):**

- innerhalb von 15 Minuten nach dem Start: OD7H um 36 EUR, OD7C um 47 EUR in der Portfolio-Ansicht
- 05:30 `ETC-Reihe fuer OD7H rekonstruiert: … Anker ≈42 USD` (vorher ≈21) und `Kursangaben geprueft: 16 Werte, 0 tot, 0 ohne Angabe`
- 06:30 `Tageswert <gestern>` rund 420 EUR höher, der Index ohne Sprung
- der Bitpanda-Abgleich meldet G2X, BW und ROL als neue Bestände
- ⚠️ eine Zeile `Kursangabe tot: …` wäre ein Befund


**Nach dem Pull von „Krypto-Preisabruf“ (K9):** normaler `git pull` (keine `config.yaml`-Änderung) → **App neu starten**. Erwartet innerhalb von 15 Minuten: `Preis-Refresh: 4x/5x Assets aktualisiert`, keine Zeile `Preis-Refresh fehlgeschlagen`; liefert CoinGecko den ETH-Wert noch, zusätzlich `CoinGecko-Volumen fuer ETH verworfen …` (richtig). Der Backoff des alten Prozesses ist mit dem Neustart weg.


**Nach dem Pull von „Bestand über die neue Bitpanda-Schnittstelle“ (K10):** normaler `git pull` → **App neu starten** → nach **30 Minuten** Export.

Erwartet im Log:

- innerhalb von 30 Minuten der erste Lauf, **rund 90 Sekunden** (Katalog und volle Buchungshistorie werden einmal geholt): `Bitpanda-Bestandsabgleich: N aktualisiert …`
- die Staking-Korrekturen wie im Trockenlauf: ETH gestakt 0,943 → 0,486, SUI 1.554 → 822, TAO 5,82 → 2,99, SOL 5,93 → 3,01, NEAR 267 → 194, AVAX 40,4 → 25,5, HYPE 3,02 → 1,52, BNB 0,159 → 0,124
- **keine** Zeile `nicht uebernommen`; eine Zeile `NICHT als umgesetzt markiert` für BNB ist **richtig** (Schutz vor falscher Signal-Bestätigung)
- der zweite Lauf braucht nur wenige Sekunden
- am nächsten Morgen: Tageswert rund 2.440 € niedriger, **ohne Indexsprung**

**Rückweg, falls etwas nicht stimmt:** in `Basisinfos/config.yaml` einen Abschnitt `bitpanda:` mit `bestand_quelle: alt` eintragen und die App neu starten – dann läuft der alte Abgleich, ohne Code-Änderung. Bitte vorher Bescheid geben.


**Nach dem Pull von „Cash und Mailversand“ (K11):** normaler `git pull` → **App neu starten** → nach **30 Minuten** Export. ⚠️ In der `.env` am Notebook muss `FUSION_API_KEY` stehen (sonst fehlen nur die Orderdetails, der Betrag stimmt trotzdem).

Erwartet im Log:

- nach dem ersten Abgleich `Bitpanda-Bestandsabgleich (neu): N Aenderung(en) …` – die alte Zeile mit „Zuwaechse“ kommt nicht mehr
- `Bitpanda-Cash (neu): verfuegbar 560,00 EUR, gesamt 3.467,27 EUR, gebunden 2.907,27 EUR in 10 Orders (…)`; steht dort `(ohne Orderdetails)`, fehlt der Fusion-Schlüssel
- Kettenzeilen `… N Mails (x zugestellt, y NICHT zugestellt) …`
- in Kaufmails: `Cash frei 0 EUR !! reicht nur, wenn Sie offene Orders aufloesen (10 Orders, 2.907 EUR gebunden, aelteste vom 04.06.)` – **richtig**, solange die Orders liegen: das verfügbare Cash plus Stablecoins liegt 81 € unter der Reserve von 2.000 €
- am nächsten Morgen: Spalte Cash im Tageswert rund 3.467 € statt 560 €, Portfoliowert und Index **unverändert**
- ⚠️ eine Zeile `Empfehlungsmail NICHT zugestellt` wäre ein Befund (dann steht sie auch im Export unter `bitpanda_bestand.auffaellig`)


**Nach dem Pull von „Papierkorb-Warnung im Export“:** normaler `git pull` – **kein Neustart nötig** (nur das Exportskript). Beim nächsten Export steht am Ende einmalig `Buchfuehrung beginnt heute …`. Dann:

1. drive.google.com → Papierkorb → **Papierkorb leeren**; bei `notebook_diagnose.json` → Versionen verwalten → alte Versionen löschen
2. am Notebook einmal `python extract_notebook_diagnose.py --papierkorb-geleert`

Ab dann zeigt jeder Export `Google-Drive-Papierkorb: rund X GB …`; ab 2 GB steht dort `BITTE LEEREN` mit denselben zwei Schritten.


**Nach dem Pull von „Schlüsselüberwachung“ (K12):** normaler `git pull` → **App neu starten** (`main.py` prüft beim Start) → nach **30 Minuten** Export.

Erwartet – im Normalfall passiert **nichts Sichtbares**:

- **keine** Mail „beim Start fehlt …“ (beide Schlüssel stehen in der `.env`); käme sie doch, fehlt der genannte Schlüssel wirklich
- **keine** Zeile `abgelehnt (BITPANDA_API_KEY)` oder `abgelehnt (FUSION_API_KEY)` im Log
- der Bestandsabgleich läuft weiter wie bei K11 (`Bitpanda-Cash (neu): … in 10 Orders …`)
- ⚠️ eine Mail „… abgelehnt – Handlung nötig“ wäre ein echter Befund: dann den Schritten in der Mail folgen
