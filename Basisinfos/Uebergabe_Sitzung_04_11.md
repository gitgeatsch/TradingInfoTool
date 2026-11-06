# Übergabe an die nächste Sitzung (04.11.2026)

> ⛔ **HISTORIE – nicht fortschreiben**, abgelöst am 06.11.2026: der Zustand steht im [`Gesamtplan.md`](Gesamtplan.md), Verlauf und Übergaben stehen im [`Arbeitsstand_Schritt59.md`](Arbeitsstand_Schritt59.md).

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md). Diese Datei ergänzt ihn um den Stand **zwischen** den Plänen: was gerade läuft, was als Nächstes kommt, was eine neue Sitzung sonst nicht wüsste.

**Warum gewechselt wird:** Das Protokoll der Sitzung `db18e928` ist 340 MB groß. Am 02.11. und am 04.11. kam deshalb je eine Antwort nicht mehr an, und die App hat die Sitzung abgebrochen (Memory `reference_sitzungsabbruch_unvollstaendige_antwort.md`). Nutzerregel 02.11.: beim zweiten Abbruch wird gewechselt.

## 1. Zuerst lesen

1. `CLAUDE.md` (Projekt) und `MEMORY.md`, Abschnitt **„HIER ANFANGEN“**
2. [`Gesamtplan.md`](Gesamtplan.md) §5, Zeilen **G7, G8, G14, G17**
3. [`Voranalyse_G8_NB_Buendel_03_11.md`](Voranalyse_G8_NB_Buendel_03_11.md) **§5** (Ablauf eines NB-Pulls) und **§7** (Entscheid b, früher Pull)
4. [`nb_kontrollen.yaml`](nb_kontrollen.yaml): die offenen Kontrollen

⚠️ `Anleitung_Probesitzung_04_11.md` ist für den **Nutzer** und wird von der neuen Sitzung **nicht** geöffnet.

## 2. Stand Code

| | |
|---|---|
| `origin/main` | **`e776ada0`** (E-168), gepusht 03.11. |
| Commits vom 03.11. | `8561053e` E-166 (W-3 S-2) · `fac05067` E-167 (G14) · `e53c95ce` G17 gelöst · `b921534d` Kursdateien-Abgleich · `b1dedb69` Voranalyse G8 · `e776ada0` E-168 (G8a: Z-1 lokal in `regel0_llm`, Fassung 2) |
| Suite Desktop | letzter Volllauf 03.11.: 3.514 Prüfungen, 1 rot nur durch Mischung alt/neu während des Laufs; alle geänderten Pakete auf dem Endstand grün |
| Nicht committen | `Basisinfos/config.yaml.bak`, alles unter `data/` |

## 3. Stand Notebook

| | |
|---|---|
| Zuletzt **ausgewertete** Diagnose | 01.11. 11:36, Kopf `fe1bf509` |
| Pull 03.11. vor dem Push | brachte nur `62d7d556` (Module, die der Betrieb nicht lädt; FOMC-Liste; `nb_kontrollen.yaml`), folgenlos |
| Pull von `e776ada0` | ✔ **bestätigt**: Der Export vom 04.11. 07:38 zeigt den Kopf `e776ada066a3…`. Damit laufen S-2, G14 und Z-1 am NB. Nicht geprüft ist, **seit wann** die App mit diesem Stand läuft (Neustart nach dem Pull); das zuerst ablesen |
| **NB-Export 04.11.** | `Notebook_Analysedaten/notebook_diagnose.json` im Austauschordner. Der Stand von 05:56 wurde **nicht ausgewertet**. Der Nutzer hat am 04.11. vormittags einen **neuen** Export gestartet → **die neueste Datei auswerten** (Dateizeit prüfen) |
| GDELT-Probe | läuft am NB in eigener Konsole bis ~16.11. (`GDELT_Probe/gdelt_probe_T440.jsonl`). Konsole offen lassen, NB **nicht** neu starten |

## 4. Die Aufgaben, in dieser Reihenfolge

1. **NB-Export 04.11. auswerten.**
   - Der Git-Kopf ist ✔ `e776ada0` (Export 07:38). Der Pull wäre nur nötig, wenn er wider Erwarten nicht dort steht. Ablauf nach Voranalyse G8 §5:
     1. zwischen :20 und :55 die App beenden und prüfen, dass kein `python` der App mehr läuft (die GDELT-Konsole bleibt offen);
     2. `git status`;
     3. `git pull --ff-only`;
     4. App starten;
     5. am nächsten Morgen die Diagnose.
   - Ist der Pull da, prüfen: **K-W3-S2** und **K-G14-1**, dazu die fälligen **K-SP-3c** (bis 04.11.) und **K-B4-D1** (bis 08.11.) und die übrigen offenen aus der YAML.
   - **K-Z1-1** braucht eine **Kopie** von `regel0_signale.db` vom NB. Nur Zeilen mit `ergebnis IS NOT NULL` zählen; die Spalte `ungedeckt` trägt `{"fassung":2,...}`.
2. **A1-Volllauf (G9) ist stehen geblieben, nicht fertig.**
   - Log `data/_a1/a1_volllauf_gemini_lite.txt`: letzter Eintrag Nachrichten-Stapel **898/1009**, 03.11. ~11:09 Ortszeit. Fehlerdatei leer, am 04.11. läuft kein `python`-Prozess.
   - Vor dem Neustart die Ursache klären: Kontingent gemini-3.5-flash-lite, Desktop-Neustart, Abbruch mit der Sitzung. Der Lauf ist wiederaufnehmbar; der Startbefehl steht in `Voranalyse_Laufzeit_02_11.md` §6.
   - Danach `--schreibe` und der Vergleich mit Groq gpt-oss (2.133 Antworten als zweiter Weg).
3. **G7 Stufe 1** ([`Voranalyse_G7_Messplan_02_11.md`](Voranalyse_G7_Messplan_02_11.md)), danach die Gleichheitsprobe für Stufe 3 (gebündelt je Tag erst nach der Probe).
4. **Später:**
   - GDELT-Urteil nach dem 16.11. (K-GD-1, bis 20.11.).
   - Danach **G8b**: B1–B6, GDELT live, S7 live mit Beständen, Prüfer v2 ersetzt Z-1.
   - Beim Nutzer offen: V4, die Gegenprüfung der Handeinordnung (drei Dateien).

## 5. Was eine neue Sitzung sonst nicht wüsste

- **Antworten kurz.** Nutzer 03.11.: *„einiges zu viel Info“*.
- **G17 Bitkipper:** Kippt ein deterministisches Ergebnis (R-R11-1 ≠ 10.732), zuerst `python pruefe_uebertragung.py --abgleich` laufen lassen. Der Nutzer hält den Speicherfehler für ein **ungeklärtes Einmalproblem**; den Speichertest **nicht** wieder anmahnen, nur bei einer Wiederholung.
- **`gegenpruefer_rollen._ZAHL` nie ändern.** `g7_stufe0.py` und `g7_voranalyse.py` hängen daran (R-R11). Die Korrektur steckt **nur** in `agent/regel0_llm.py` (`ZAHLENDECKUNG_FASSUNG = 2`).
- **Suite-Ausgabedatei:** Einzelne Pakete über `main()` laufen zu lassen überschreibt `Pruefungen/pruefe_pakete_ausgabe_9900K.txt`. Deshalb die Paketfunktion direkt mit `python -c` aufrufen.
- **Konsole:** `PYTHONIOENCODING=utf-8` setzen, sonst bricht cp1252 ab. Die Diagnose-Konsole bleibt ASCII.
- **GDELT:** keine Anfragen vom Desktop bis 16.11.
- **Gemini:** am Desktop nur Schlüssel 2, nie den NB-Schlüssel.
- **Arbeitsablauf:**
  1. Voranalyse
  2. Abstimmung (eine Entscheidung mit Alternativen)
  3. bauen
  4. prüfen am Seiteneffekt
  5. gegenprüfen
  6. Doku (Gesamtplan, Entscheidungen, Register: `python dokumente.py`)
  7. Commit nur auf ausdrückliches Ja, per `git commit -F` mit `Co-Authored-By`-Zeile
  8. Push
  9. NB-Pull nach §4.1
  10. Diagnose
- **Protokollgröße:** Ab ~300 MB Sitzungsprotokoll brechen Antworten ab. Dann diese Datei fortschreiben und wechseln.
