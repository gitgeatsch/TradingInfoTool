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
