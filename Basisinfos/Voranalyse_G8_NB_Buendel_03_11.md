# Voranalyse G8: was jetzt ans Notebook kann (03.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) G8 · Kontrollen: [`nb_kontrollen.yaml`](nb_kontrollen.yaml) · Bündel-Inhalt laut [`Voranalyse_G7_Messplan_02_11.md`](Voranalyse_G7_Messplan_02_11.md) §6.2, §9.1, §9.4

Nutzer 03.11.: *„ja G8 prüfen und gegenprüfen und doku“*

⚠️ **Nur Voranalyse.** Nichts wird gebaut und nichts geht ans NB, bevor du entschieden hast.

## 1. Was G8 laut Plan ist

G8 ist **zweierlei**, und das war bisher in einer Zeile vermengt:

| Teil | Inhalt | Stand | Hängt an |
|---|---|---|---|
| **Bau** | B1–B6 + Ebenen 2/3, Mail mit beiden Blöcken ([`Bauplan_Dashboard_A3_A4_28_10.md`](Bauplan_Dashboard_A3_A4_28_10.md)) | **nicht gebaut** | G7 (Wert der Sichten gemessen), *Betriebsumstellung erst nach der ganzen Kette* |
| | GDELT-Abruf am NB | nicht gebaut | Urteil der GDELT-Probe (K-GD-1, ab 16.11.) |
| | S7 live mit Beständen (G7 §9.1) | nicht gebaut | Teil des Baus |
| | Z-1-Zahlenerkennung (G7 §6.2) | nicht gebaut | siehe §3, **kein sichtbarer Ausgang im Betrieb** |
| **Bündel** (fertig, wartet nur auf den Pull) | **W-3 S-2** (E-166, K-W3-S2) | ✔ gebaut 03.11., Suite grün | – |
| | **G14** (E-167, K-G14-1) | ✔ gebaut 03.11., Suite grün | – |
| | Kursdateien-Abgleich (G17) | ✔ gebaut 03.11. | wirkt nur am Desktop, am NB übersprungen |

**Folge:** Das ganze G8 kann frühestens nach G7 und dem GDELT-Urteil ans NB, also **nicht vor etwa dem 20.11.** Bis dahin lägen S-2 und G14 fertig und ungenutzt auf dem Desktop.

## 2. Was ein Pull HEUTE am NB ändert — geprüft

**NB-Stand:** `fe1bf509` (01.11. 10:59, GOOGL in die Watchlist). Laut Diagnose vom 01.11. 11:36 ist das Arbeitsverzeichnis sauber: nichts geändert, kein Stash. Seitdem gibt es **29 Commits**. `fe1bf509` ist ein Vorfahre von HEAD, der Pull ist also ein reiner Fast-Forward.

| Wirkt im Betrieb | Commits | Was |
|---|---|---|
| ✔ **ja** | 8561053e (E-166) | `background.py`, `rollen_job.py`, `regel0_groesse.py`, Statusseite, Diagnose: die alten Jobs überspringen sich. Dazu **Frage 2**: `thesen_pausiert` und `marktscan.aktiv` fallen im Zweifel auf AUS. Heute ohne Wirkung, weil beide ohnehin aus sind |
| ✔ **ja** | fac05067 (E-167) | `kernwerte.py`, `regel0_stundenlauf.py`, `betriebslage.py`, GUI (Watchlist/Hebel/Bestand), Statusseite, Diagnose, Teilexport |
| ✔ ja, nur Anzeige | mehrere | `nb_kontrollen.yaml`: die Statusseite zeigt den Stand 03.11. mit den neuen offenen Kontrollen |
| ✔ ja, ohne Folge | 06347e61 | `agent/cycles.py` wird vom Betrieb gelesen (Termine). Neu ist nur eine **zusätzliche** Liste vergangener FOMC-Tage; `FOMC_MEETING_DATES` und `fomc_liste_reicht_bis` bleiben unverändert |
| ✔ ja, nur von Hand | b921534d | `pruefe_uebertragung.py`: `--abgleich` entfällt am NB, `--pruefen` verhält sich bei Gleichheit wie bisher |
| ✘ **nein, liegt nur da** | übrige | neue Module `agent/zustaende.py`, `agent/ereignisse.py`, `agent/gutachten_pruefer.py`, `api/sichten_quellen.py`, `g7_messanlage`. **Der Betrieb lädt sie nicht**, geprüft per Importanalyse ab `main.py`, `background.py`, `remote/server.py` und dem Unterprozess `regel0_stundenlauf`. Sonst Dokumente und Messskripte |

- **Konfiguration:** `regel0_betrieb.yaml`, `regel0_llm.yaml`, `config.yaml` und `kategorien.yaml` sind unverändert. Keine neue Bibliothek, `requirements.txt` unverändert.
- **GDELT-Probe:** läuft aus dem Austauschordner in eigener Konsole, nur mit der Standardbibliothek, und liegt nicht im Repo. Pull und **App-Neustart** berühren sie nicht. ⚠️ Das NB darf **nicht neu gestartet** werden, und die Probe-Konsole darf nicht geschlossen werden.

## 3. Z-1: gehört nicht in dieses Bündel

Der Fehler ist echt. `_ZAHL = [-+]?\d{1,3}(?:[.,]\d+)?|\d{4,}` greift immer zuerst mit der kurzen Alternative, darum zerlegt die Erkennung große Zahlen: `71211.95 → 712 | 11.95`, `2026 → 202 | 6`.

**Die Gegenprüfung hat aber gezeigt: im Betrieb hat Z-1 keinen sichtbaren Ausgang.**
- Das Ergebnis landet nur in der Spalte `ungedeckt` der Tabelle in `regel0_signale.db`.
- **Niemand liest diese Spalte**: keine Mail, keine Statusseite, keine Diagnose, kein Teilexport. Selbst nachgesehen mit `grep ungedeckt`.
- Die Angabe in G7 §6.2a, die Zahl stehe in *„Protokoll und Mail“*, stimmt für die Mail **nicht**.

**Ein Fix hätte dazu Nebenwirkungen:**
- `_ZAHL` ist gemeinsam. Er verschiebt die Messskripte `g7_stufe0.py` und `g7_voranalyse.py` und damit die dokumentierte Reproduktion *„Z-1 erkennt ~40 %“* (R-R11).
- Jahreszahlen würden plötzlich als eine Zahl gezählt. Die Spalte wäre vor und nach dem Fix ohne Fassungsmarke nicht vergleichbar.

→ Z-1 zu flicken bringt dem Betrieb heute nichts. Sinnvoll ist G7 §6.2 **c**: Z-1 wird durch den **Prüfer v2** (`agent/gutachten_pruefer.py`, Selbsttest 8/8) ersetzt, wenn G8b gebaut wird. Bis dahin bleibt Z-1 unverändert.

## 4. Die Entscheidung

| | Weg | Folge |
|---|---|---|
| **a** | **G8 teilen. G8a jetzt: nur Pull** (S-2 + G14, alles fertig und grün). **G8b später:** B1–B6, GDELT live, S7 live und Prüfer v2 statt Z-1, nach G7 und dem GDELT-Urteil | Zwei Schutzbauten laufen ab sofort. Kein Bau vorher nötig. Ein Pull mehr als geplant, dafür klein und leicht zu diagnostizieren |
| b | wie a, dazu Z-1 lokal in `regel0_llm` beheben, mit Fassungsmarke | Verzögert den Pull um Bau und Gegenprüfung, ohne sichtbaren Nutzen im Betrieb (§3) |
| c | alles in einem Pull nach G7 (~20.11.) | Hält die Regel *bündeln* am strengsten ein. S-2 und G14 liegen ~3 Wochen ungenutzt, das Bündel wird groß |

**Empfehlung a.** Die Regel *NB-Änderungen bündeln* soll viele kleine Pulls vermeiden. Hier liegen aber drei Wochen dazwischen, und G8a ist selbst schon ein Bündel aus zwei Bauten.

## 5. Ablauf am NB bei a (für dich)

1. **Zeitpunkt:** zwischen etwa **:20 und :55** einer Stunde. Um :05 startet die stündliche REGEL0-Rechnung (meist ~7 min, mit Monatstraining bis ~25 min). Sicheres Zeichen: die Zeile `REGEL0-ERGEBNIS` der laufenden Stunde steht im Log.
2. **App beenden.** Danach im Task-Manager prüfen, dass **kein** `python`-Prozess der App mehr läuft. Die GDELT-Konsole bleibt offen; das ist ein eigener Prozess, an der eigenen Konsole erkennbar.
3. Im Projektordner:
   ```bash
   git status
   ```
   Es soll nichts geändert sein. Steht dort etwas, nicht weitermachen und mir melden.
4. Dann:
   ```bash
   git pull --ff-only
   ```
5. **App starten.** Beim Start laufen wie immer sofort der Nachlader, die REGEL0-Rechnung und die Nachholer (Spot, Season-Ampel, Messstand). Dabei sind Mails möglich, das ist normal.
6. **Am nächsten Morgen:** Diagnose oder Teilexport. Ich prüfe dann K-W3-S2 und K-G14-1 sowie die übrigen fälligen Kontrollen.

## 6. Gegenprüfung (03.11., unabhängig, nur lesend)

**Kernaussage bestätigt:** Im Betrieb wirken nur E-166 und E-167. Der Pull ist ein Fast-Forward, es gibt keinen Importweg zu den neuen Modulen und keine neue Abhängigkeit. Ohne schweren Befund. Eingearbeitet:

| Befund | Schwere | Eingearbeitet in |
|---|---|---|
| Neustart während der REGEL0-Rechnung: Mischung aus altem und neuem Code, zwei Rechnungen parallel (keine Sperre zwischen Prozessen) | mittel | §5 Punkte 1, 2, 4 (Zeitfenster, Prozessprüfung, `--ff-only`) |
| Z-1 hat keinen sichtbaren Ausgang; die Begründung, Z-1 mitzunehmen, war zu stark | mittel | §3, §4 — **Empfehlung von „a mit Z-1“ auf „a ohne Z-1“ geändert** |
| `_ZAHL` ist gemeinsam: verschiebt Messskripte und die Reproduktion; Alternativen „lokal“ und „Prüfer v2“ fehlten | mittel | §3, §4 b |
| `cycles.py` und `nb_kontrollen.yaml` werden im Betrieb gelesen | leicht | §2 (folgenlos bzw. nur Anzeige) |
| Frage 2 von E-166 fehlte | leicht | §2 |
| `git status` vor dem Pull; was beim Neustart läuft | leicht | §5 Punkte 3 und 5 |

## 7. Entscheid und Bau (03.11.)

Nutzer: *„Ok b“*. **G8a = S-2 + G14 + Z-1 lokal in `regel0_llm` mit Fassungsmarke**, gebaut als **E-168**.
- Die Erkennung ist die alte Regel mit der langen Ziffernfolge zuerst. Ohne vierstellige Zahl liest sie gleich wie vorher (Zufallsprobe 17.156).
- Die gemeinsame `_ZAHL` ist unverändert.
- Paket Zahlendeckung prüft den echten Weg bis in die Ablage. Kontrolle K-Z1-1.

⚠️ Am 03.11. hat der Nutzer schon **vor** dem Push gezogen. Angekommen ist nur der GitHub-Stand vom 02.11. 13:42 (`62d7d556`): neue Module, die nicht geladen werden, die FOMC-Liste und `nb_kontrollen.yaml`. Folgenlos laut §2. S-2, G14 und Z-1 kommen mit dem nächsten Pull nach dem Push (Ablauf §5).
