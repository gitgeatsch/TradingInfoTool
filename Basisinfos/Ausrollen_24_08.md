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
