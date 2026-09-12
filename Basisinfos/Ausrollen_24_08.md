<!-- STAND: 2026-09-02 · VOR dem Messstandard vom 2026-09-09 · keine Messwerte, deshalb ohne sichtbaren Kopf -->
# Ausrollen — was auf dem Notebook zu tun ist, und was danach zu beobachten

*Stand: 24.08.2026, alles gepusht bis `3970b7b`. **38 Commits** seit dem
letzten Notebook-Stand (`cc06fe1`).*

> ⚠️ **Ausrollen heißt hier NICHT scharfschalten.** Die Produktion ist bereits
> `scharf` und bedient alle fünf Gruppen. Sie zieht den neuen Code und startet
> neu — **es wird nichts eingeschaltet, sondern etwas verengt.**

---

## 1. Die Schritte, in dieser Reihenfolge

```bash
git fetch && git status
```
⚠️ **Zuerst `fetch`, nicht `pull`** — das Notebook hatte schon einmal eigene
Commits.

```bash
git pull --ff-only
```

Dann den Scheduler **stoppen, ziehen, starten**. ⚠️ **Nicht gestoppt lassen:**
der Schatten füllt sich ausschließlich aus echten Läufen.

```bash
python pruefe_pakete.py
```
Muss **1.679 bestanden** melden (Stand 24.08. abends; war 1.659 vor der
Fehlerrunde dieses Tages). Bricht sie ab, nicht starten.

⚠️ **Die Ausgabe landet zusätzlich auf Google Drive**, seit externe
Zusammenfassungen sie wiederholt gekürzt oder falsch gedeutet haben:

```
Claude_Austauschordner\Pruefungen\pruefe_pakete_ausgabe_<GERAET>.txt
```

**Der Dateiname trägt das Gerät** (`platform.node()` — Desktop `9900K`,
Notebook `T440`), weil sonst ein Desktop-Testlauf das Notebook-Ergebnis
kommentarlos überschreibt. Genau das ist am 24.08. passiert. **Beim Prüfen
den DATEINAMEN ansehen, nicht nur den Zeitstempel** — und die Schlusszeile
lesen: fehlt sie, ist der Lauf abgebrochen (der `finally`-Block schreibt
trotzdem).

```bash
python finde_freie_namen.py
```
Muss **0 Kandidaten** melden.

---

## 2. ⚠️ Was beim ersten Lauf von selbst passiert

| | was | woran erkennbar |
|---|---|---|
| **neue Spalte** | `signals.strategie` wird angelegt | `signal_abbildung.migriere()` beim ersten Schreiben |
| **neue Tabelle** | `auswahl_schatten` | wird beim ersten Lauf angelegt |
| **neue Trichterstufe** | `auswahl` erscheint zwischen `anlass` und `wiederholung` | in der Gate-Zeile der Mail |

**Nichts davon braucht einen Handgriff** — aber jedes davon ist eine Stelle, an
der schon einmal etwas schiefging (22.08.: eine neue Spalte hielt die App an).
**Deshalb Punkt 3.**

---

## 3. Die Leseprobe nach dem ersten Lauf — Pflicht, nicht Kür

```bash
python -c "import sqlite3,database.db as db; c=sqlite3.connect('data/tradinginfotool.db'); c.row_factory=sqlite3.Row; s=db.get_latest_signal(c,'BTC'); print(s.symbol, s.action, repr(s.strategie))"
```

⚠️ **Wer eine Spalte anlegt, muss eine Zeile daraus lesen.** Ein Schreibtest
genügt nicht: das Schreiben nennt Spalten einzeln, das Lesen bekommt sie alle.

```bash
python -c "import sqlite3; from agent import auswahl as A; c=sqlite3.connect('data/tradinginfotool.db'); print(A.stand(c))"
```
Erwartet: `zeilen` > 0, `laeufe` ≥ 1, `gewaehlt` ≥ 1.

---

## 4. Was sich im Betrieb ändert — die Zahlen

| | vorher | nachher |
|---|---|---|
| Beurteilungen je Tag (Krypto) | 85–150 | ⚠️ **~21 je Umlauf**, davon der Großteil **Bestand** |
| Einstiegs-Kandidaten je Umlauf | alle 41 | **2** (plus Gleichstand) |
| Begründung je Signal | „Cooldown abgelaufen" | **„Rang 2 von 41"** |
| Verkaufsseite `facts_json` | 17 Zeichen | **~1.420 Zeichen** |
| Gegenprüfung auf Ausstiegen | 0 von 561 | **jede** |

**Erwartete Signale:** rund **zwei Krypto-Einstiege je Tag** bei 15 % Handlungs­-
quote, plus die Verkaufsseite. ⚠️ **Nicht null** — aber deutlich weniger
Wiederholungen desselben Werts.

---

## 5. ⚠️ Worauf in den ersten Läufen zu achten ist

| # | was | warum |
|---|---|---|
| **1** | **Die ersten Signale LESEN, nicht zählen** | Lehre vom 10.08. Die Auswahl-Begründung steht im Block über dem Rangplatz |
| **2** | **Die Gate-Zeile**: passiert `auswahl` plausibel viele? | ⚠️ Erwartet: Bestand + 2. Sind es 0, greift etwas, das nicht greifen soll |
| **3** | ⚠️ **Der Trichter muss monoton bleiben** | `hinein` ≥ jede Stufe. Am 23.08. buchte der Trockenlauf `anlass` doppelt — behoben, aber es ist die Stelle |
| **4** | **Die Warnung „Einstiegsseite … Läufe in Folge ohne Einstieg"** | der laufübergreifende Zähler. Erscheint sie, liefert die Auswahl Kandidaten und die Kette nimmt keinen |
| **5** | **Rohstoffe** | ⚠️ in der Desktop-Kopie haben OD7C/H/N/L **null eigene Kerzen**. Am Notebook prüfen — dort fehlt sonst die halbe Faktenbasis |
| **6** | **Kontingent** | Gemini 500/Tag **je Modell**, Reset 09:00 MESZ. Ein Desktop-Lauf nimmt der Produktion Kontingent weg |

---

## 6. Was NICHT ausgerollt wird

| | |
|---|---|
| `crv_spreizung` | steht weiter auf **1,0** — die CRV-Abstufung ist **aus**. Geeicht (`voll_ab` 3,0), nicht eingeschaltet |
| A1c (Takt 20 Handelstage) | **nicht gebaut** — die Auswahl gilt je Umlauf, den Mindestabstand macht der Cooldown |
| K4 (b) — die Bedingung „taugt überhaupt" | **nicht gebaut**, weil keine gemessene Größe dafür existiert |
| Gegenprüfung auf Nein-Zeilen | **nicht gebaut** — ~21 je Umlauf gegen 2 gleichzeitige Z.ai-Aufrufe wäre der halbe Takt |

---

## 7. Wenn etwas schiefgeht

**Zurückrollen ist ein Commit:**

```bash
git log --oneline -1 && git revert --no-commit HEAD~38..HEAD
```

⚠️ **Aber die Daten bleiben:** `signals.strategie` und `auswahl_schatten` sind
**additiv** — sie stören eine ältere Codeversion nicht. Ein Rückschritt kostet
also keine Zeilen, nur die neuen Felder bleiben leer.

---

# AUSROLLEN 02.09.2026 — das Scharfschalten, und der Knoten, der fast übersehen wurde

**Nutzerentscheidung:** *„Ich würde gerne umschalten und das scharf, danach
messen. Du musst vorher prüfen, ob wir alle wichtigen Punkte und Knoten
haben — z. B. was ist mit der neuen Datenbank, wie kommt die auf das NB?"*

## ⚠️⚠️ Der Knoten: vier Datenbanken, die `git pull` NICHT mitbringt

`*.db` steht in `.gitignore`. Der Produktionscode liest seit dem 31.08.
vier Dateien, die es auf dem Notebook nicht gibt:

    data/funding_historie.db       22 MB   -> messbasis("funding")
    data/onchain_historie.db       22 MB   -> messbasis("turnover")
    data/terminmarkt_historie.db  132 MB   -> messbasis("oi"), N-14
    data/messdaten.db             166 MB   -> schnitte(), messbasis("schnitt")

**Fehlen sie, bricht nichts ab — und genau das ist die Gefahr.**
`messbasis()` liefert eine leere Menge, `raenge()` überspringt die Größe mit
einem `logger.error`. Beide **tragenden** Beiträge (Funding, Turnover)
hätten dann keinen Rang, das Potential läge bei **0,000**, und die scharf
geschaltete Stufe 11 sperrte **alles**.

> **Ein Pull ohne diese Dateien schaltet die Kette stumm — lautlos.**
> Genau der Deadloop, aus dem das System gerade kommt.

## Die Lösung: es sind gar nicht die Daten, die gebraucht werden

Drei der vier werden **nur nach der Symbolliste** gefragt. Aus 176 MB
werden **40 KB**:

    python baue_messbasis_paket.py --ziel "K:/My Drive/Claude_Austauschordner/Messbasis"

    funding_historie.db       302 Symbole  ->  12,0 KB
    onchain_historie.db        66 Symbole  ->  12,0 KB
    terminmarkt_historie.db   132 Symbole  ->  16,0 KB

**Gegengeprüft:** `marktrang.messbasis()` liest aus dem Paket exakt
dieselben Mengen wie aus den Originalen (302 / 66 / 122 — identisch).

⚠️ **Jede Paketdatei kennzeichnet sich selbst** (Tabelle
`_nur_symbolliste`): eine verkleinerte Datenbank, die aussieht wie eine
echte, wäre sonst eine Falle für jede spätere Messung.

⚠️ **`messdaten.db` ist NICHT im Paket** — sie wird wirklich ausgelesen.
Ohne sie fällt der Schnittabstand weg; er ist am 31.08. als Beitrag
gefallen und nur noch **Anzeige**. Wer ihn will: `lade_messreihen.py` am
Notebook.

## Die übrigen Knoten — alle geprüft

| | Stand |
|---|---|
| **Schema** `signals.instrument` | ✔ `_migrate_signal_instrument` läuft in `init_db` automatisch |
| **`config.yaml`** | ✔ liegt in `Basisinfos/` und **ist im Repo** — kommt mit dem Pull. Eine Änderung: Stop-Untergrenze 2,5 → 5,0 % |
| **Neue Python-Pakete** | ✔ keine (`requirements.txt` unverändert) |
| **Schwelle 0,080** | ✔ steht im **Code** (`agent/potential.py`), nicht in der config |
| **Config-Schlüssel ohne Vorgabe** | ✔ keine |
| **`.env`** | ✔ unverändert — wird ohnehin nie übertragen |

## Die Reihenfolge

```bash
python baue_messbasis_paket.py --ziel "K:/My Drive/Claude_Austauschordner/Messbasis"
```
*(am Desktop, vor dem Push)*

Dann am Notebook:

```bash
git fetch && git status
```
⚠️ **Zuerst `fetch`, nicht `pull`** — das Notebook hatte schon einmal eigene Commits.

```bash
git pull --ff-only
```

**Dann die drei Dateien aus `Claude_Austauschordner/Messbasis` nach `data/`
kopieren** — vor dem Neustart, sonst läuft der erste Lauf blind.

```bash
python pruefe_pakete.py
```
Muss **1.928 bestanden** melden. Bricht sie ab: nicht starten.

Dann Scheduler stoppen, starten.

## ⚠️ Was danach zu erwarten ist — und zwar sofort

| | vorher | nachher |
|---|---|---|
| Signale | ~28/Tag | **~0,5/Tag** |
| Mails | ~37/Tag | entsprechend wenige |

**Das ist kein Fehler, sondern die Umschaltung.** Wer am nächsten Morgen
eine leere Mailbox sieht, hat den erwarteten Zustand.

## Wie danach gemessen wird

Die Zeile steht schon im Log, seit dem 14.08.:

    grep "Durchlaessigkeit" data/tradinginfotool.log

⚠️ **Das Log rotiert bei 5 MB mit drei Sicherungen.** Bei 9,3 Läufen am Tag
deckt das Fenster nur wenige Tage ab — **nach zwei Tagen holen**, nicht
nach zwei Wochen.

**Die Frage, die der Trichter danach beantwortet:** greift Stufe 11 auf
denselben Zellen wie vorher, oder verschiebt sich der Verlust? Und: was
macht die neue Stufe `terminmarkt` (N-14)?

---

# 🚀 11.09.2026 — DER PRODUKTIVGANG NACH DEM BEWERTUNGSUMBAU

> *„der Umbau des Systems für das NB läuft nun schon seit Tagen bzw.
> Wochen, da die bestehende Lösung nicht funktioniert — also auch kein
> Pull am NB seit Tagen. Wenn du Vorarbeiten und die S1 etc. benötigst,
> dann mach die Planung und Umsetzung so, dass wir sauber vom Desktop auf
> das NB produktiv gehen können."*
> — Nutzervorgabe 11.09.2026

## Die Lage — gemessen, nicht geschätzt

| | |
|---|---|
| **Commits seit dem letzten dokumentierten Ausrollstand (24.08.)** | **292** |
| Commits seit dem 02.09. | 181 |
| geänderte **Betriebs**dateien seit 02.09. | 10 — `agent/auswahl.py`, `marktrang.py`, `potential.py`, `rollen_gate.py`, `rollen_lauf.py`, `signal_mail.py`, `wahrscheinlichkeit.py`, `zweite_meinung.py`, `database/models.py`, `scheduler/rollen_job.py` |

⚠️ **Das ist kein Nachziehen, das ist ein Gesamtpaket.** Die stehende
Regel gilt: *am Notebook immer eine custom zusammengestellte
Gesamtpaket-Installation, nicht einzelne Schritte nacheinander* — der
inkrementelle Weg hat dort schon einmal eine Lücke hinterlassen.

---

## ⓿ Die Vorarbeiten — **am Desktop, vor dem Rollout**

**Warum vorher:** der Code wird ohnehin ersetzt. Diese drei nachträglich
einzubauen kostet einen **zweiten** Rollout.

### S-1 · Die drei Messquellen als Scheduler-Jobs

**Heute:** `funding_historie.db`, `terminmarkt_historie.db` und
`onchain_historie.db` werden von `hole_fremdreihen.py` und
`hole_terminmarkt_historie.py` **von Hand** geschrieben. Von 21 geplanten
Jobs schreibt **keiner** sie. Kein Misfire-Schutz, kein
Staleness-Watchdog, kein Backoff, keine Fehlermail.

**Tragweite — kleiner als sie aussieht:** die laufenden **Werte** kommen
aus Live-API-Abrufen; die DBs liefern nur die **Messbasis**. Für den
Betrieb also kaum kritisch, für **Messungen und Kalibrierung** voll.

➔ Als Jobs aufsetzen, mit `api.boersen_klines.fuelle_luecken` als
Vorbild — sie füllt bereits Lücken statt nur die Spitze zu prüfen.

### S-2 · ⚠️⚠️ Der stille Ausfall

`agent/marktrang.py:718`:

```python
f = eintrag.get("funding_fuenftel")
if f is not None:
    zeilen.append("Finanzierung: ...")
```

> Fällt die API kurz aus, wird der Wert `None` — und die Zeile wird
> **weggelassen**. Die Mail sieht normal aus, nur kürzer. Die Bewertung
> ist an dem Tag **stumm um einen Beitrag ärmer**.

Bei Totalausfall aller vier nennt die Mail sogar die **falsche Ursache**
(„gehört nicht zur Messbasis" — es lag am **Netz**).

➔ Sichtbare Zeile *„heute nicht verfügbar"* mit der **richtigen**
Ursache. Verletzt sonst zwei stehende Vorgaben: *fail-soft ist
fail-silent* und *Änderungen dürfen die Bewertung nicht blockieren, schon
gar nicht still*.

### S-3 · Alle Jobs protokollieren

**Heute** hinterlassen nur **6 von 21** Jobs eine Spur in `job_laeufe`.
Für `refresh_prices`, `refresh_history`, `marktscan`, `hebel_screening`
und elf weitere ist **nicht feststellbar, wann sie zuletzt liefen** —
nach einem Ausfall also nicht, was gefehlt hat.

➔ `_log_job_event` für alle 21, nicht für sechs.

---

## ❶ Der Rollout selbst

Die Schritte aus Abschnitt 1 oben gelten unverändert (`fetch` vor `pull`,
Scheduler stoppen/ziehen/starten, `pruefe_pakete.py`,
`finde_freie_namen.py`).

⚠️ **Zwei Zahlen sind neu:** die Prüfsuite meldet heute **2048** (nicht
1.679), und die drei bekannten Roten sind CANTON/ASTER/MON ohne
Messreihe, CANTON ohne Beitrag, sieben Klassenkollisionen — dazu die
Datenalterung der Nicht-Krypto-Messbasen.

---

## ❷ Die Abnahme **am Notebook** — was danach wahr sein muss

| | |
|---|---|
| **L1** | ⚠️ **die Oberfläche einmal am NB öffnen** und im Watchlist-Reiter *„Akkumulation umschalten (Krypto)"* für **ETH und SOL** setzen. Der Schalter **existiert** — er wirkt aber auf die DB des Geräts, auf dem die GUI läuft. Am Desktop geschaltet landet er in der Desktop-DB, die nie produktiv ist |
| **Datenstand** | `funding_historie` / `terminmarkt_historie` / `onchain_historie` nachziehen (Rückstand 11–13 Tage) |
| **`portfolio_wert_historie`** | muss wieder **täglich** schreiben. Steht sie erneut, ist die 80-%-Abdeckungsschranke der Grund — dann sind die 6 von 32 Symbolen ohne Kurs die eigentliche Aufgabe |
| **`hebel_signals`** | steht seit dem 10.08. — nach dem Rollout prüfen, ob das ein Ausfall oder die begründete Folge der blockierten Hebellage ist |

---

## ⚠️ Was dieser Rollout NICHT löst

| | |
|---|---|
| **Die Hebellage** | bleibt blockiert (A1, A9, P-1) — der Rollout ändert daran nichts |
| **Der Takt** | Mailaufkommen und Wiederholungsanteil sind **nach** dem Rollout zu messen, nicht vorher — vorher misst man den alten Stand |
| **Die Akkumulationsbewertung** | `schnitt` ist gemessen, aber **nicht registriert**. Bis die FORM entschieden ist, hat die Akkumulationslage **null** Beiträge — auch nach dem Rollout |

---

# 🚀 PAKET B — der Rollout am Notebook (Schritt 24, vorbereitet 11.09.2026)

> Nutzerentscheidung 11.09.: *„1 Hebel, 2 Spot, 3 Akkumulation — zumindest
> Hebel und Spot müssen sauber funktionieren."* Paket B bringt beides; die
> Akkumulation bleibt gesperrt (Paket 2).

## Was dieser Rollout ändert

| | vorher | nachher |
|---|---|---|
| **Hebel** | aus der Stopgeometrie (1,0–1,5x auf Spot-Signalen) | aus der **Wahrscheinlichkeit** r(q), 2–5x, sonst Spot mit **unverändertem Betrag** |
| **Aggregat-Deckel** | keiner | alle Hebelrisiken zusammen ≤ **3 % des Kapitals** (bei 18.213 EUR: 546 EUR) |
| **Hebelführung** | Positionen wurden nirgends gelesen | eigene Mail bei LIQUIDATION / SCHLIESSEN / HEBEL SENKEN / KURS FEHLT / STOP NACHZIEHEN |
| **Mail** | ein Block | *Auf einen Blick* · *Was dagegen spricht* · 6 Abschnitte · Anhang |
| **Cooldown Krypto** | 3,5 h für jeden Hebel > 1,0 | 3,5 h erst ab 2x, sonst **12 h** |
| **Kapital** | 9.942 EUR (ohne Gestaktes, 01.09.) | **18.213 EUR** (mit Gestaktem, nachgerechnet) |

## ⚠️ Die Schalter — Stand beim Push

| Schalter | Wirkung | Stand |
|---|---|---|
| `rollen_kette.hebel_aus_quote.aktiv` | ohne ihn entsteht **kein** Hebelgeschäft | ✔ **AN** (Nutzer 12.09.) |
| `marktscan.aktiv` | alter Marktscan, eigene Mails (2.369) | **AN** — die einzige Entdeckung außerhalb der Watchlist (2.385); der Ersatz wird erst gemessen (Schritt 39) |
| `hebel_screening.aktiv` | altes Hebel-Screening; `false` legt **nur** das Screening still, Positionsabgleich und Hebelführung laufen weiter | ✔ **AUS** (Nutzer 12.09.) |
| Hebel-Schalter **je Asset** (GUI) | nur dort entsteht ein Hebelgeschäft | am NB **24 von 44** Kryptowerten an |

## Die Schritte, in dieser Reihenfolge

**1. App und Watchdog beenden** (Tray-Symbol).

**2. Zuerst `fetch`, nicht `pull`:**

```bash
git fetch && git status
```

⚠️ **Meldet `git status` eine geänderte `Basisinfos/config.yaml`** — die App
schreibt sie selbst (Watchlist, Schalter): `git diff Basisinfos/config.yaml`
ansehen. Betrifft es andere Abschnitte als der Push, nur diese Datei
committen, dann weiter. Überlappt es: **anhalten**, nicht verwerfen.

```bash
git pull --ff-only
```

**3. Die Vollständigkeitsprüfung — erst lesen, dann nachrechnen:**

```bash
python ausrollen_paket_b.py
```

Erwartet: **C1 ✔ K1 ✔**; offen dürfen nur **P2** (Kapital alt) und **D1**
(Quelle `kapital`) sein — genau das rechnet der nächste Schritt nach.

```bash
python ausrollen_paket_b.py --nachrechnen
```

Erwartet: **0 nicht erfüllt**, *„Kapital … FRISCH"*, Deckel rund **546 EUR**
(am Desktop gegen die Sicherung vom 11.09. gerechnet: 9 Tage, 18.213 EUR). Die
neue Spalte `verlust_am_stop_eur` wird dabei angelegt und gelesen.

**4. Die Suite:**

```bash
python pruefe_pakete.py
```

⚠️ **Am Notebook sind es 2.180 Prüfungen, 4 übersprungene Blöcke und 0 Rote**
— `data/messdaten.db` liegt dort planmäßig nicht (Befund 2.386).

> ⚠️⚠️ **Null Rote heißt am Notebook NICHT „alles in Ordnung".** Alle vier
> bekannten Roten liegen im Paket *Neuaufnahme*, und das ist dort nicht
> beantwortbar — es wird als Ganzes übersprungen. Die Lücken gelten weiter.

Am Desktop sind es **2.193 Prüfungen** mit diesen **4 bekannten Roten**: Messreihe
für gehaltene Werte (ASTER, CANTON, MON), Messbasis Nicht-Krypto veraltet,
Kernwert CANTON ohne Beitrag, sieben Klassenkollisionen. Die Ausgabe steht in
`Pruefungen\pruefe_pakete_ausgabe_T440.txt` — **Dateinamen prüfen**.

**5. Der Durchlauf mit einem Hebelgeschäft** (arbeitet auf zwei Kopien im
Temp-Verzeichnis, rund 1 GB, einige Minuten):

```bash
python simuliere_kette.py --nachweis-paket-b
```

Erwartet: **17 Fälle, 17 gezeigt**, dazu zwei ○-Befunde zur Akkumulation
(Schritt 26). ⚠️ Er ruft keine Modelle — die Antworten kommen aus einer
Attrappe, das Kontingent bleibt unberührt.

```bash
python finde_freie_namen.py
```

Muss **0 Kandidaten** melden.

**6. Watchdog starten.**

## Was danach zu erwarten ist

| | |
|---|---|
| **Hebelmails** | nur für Werte mit Hebel-Schalter **und** Beiträgen, die r(q) über 2x heben — **selten** (Simulation: rund die Hälfte der Kandidaten, davon ein Drittel durch den Deckel Spot) |
| **Hebelführung** | eine Mail nur bei Handlungsbedarf, einmal je Zustand und Tag |
| **Spot** | Beträge wie bisher; der Betreff verliert das Schein-„(Hebel)" |
| **Akkumulation** | **keine** Signale — im Trichter steht `anlass`, nicht die Sperre (2.382-akku-anlass) |

## Nach dem ersten Lauf

```bash
python ausrollen_paket_b.py
```

Alles ✔ außer Hinweisen. ⚠️ **Die erste Hebelmail LESEN, nicht zählen:**
Kopf *„Betrag … – Hebel …x"*, darunter die Hebelrechnung mit dem Satz zum
Aggregat-Deckel.

## Was dieser Rollout NICHT bringt

| | |
|---|---|
| Akkumulation | Paket 2 (Schritte 25–27) — und dort Anlass und Cooldown je Zelle |
| Topfregel | begrenzt praktisch nie — neu fassen nach dem Rollout (Schritt 28) |
| Feinschliff Mail | Kursmarken und Rangangaben zusammenlegen, Rundung des Hebels, Wortlaut Anhang C |

## Wenn etwas schiefgeht

Zurück ist ein `git revert` über die Paket-B-Commits. **Die Daten bleiben
additiv:** die Spalte `verlust_am_stop_eur` und die nachgerechneten Tage in
`portfolio_wert_historie` stören einen älteren Code nicht.
