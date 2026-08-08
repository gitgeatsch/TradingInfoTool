# Messungen zur LLM-Anbieterfrage (08.–09.08.2026)

Rohdaten und Werkzeuge der Anbieter-Untersuchung. Die **Befunde** stehen im
`Regelwerk_Entscheidungslog.md` (vier Nachträge vom 08./09.08.) — hier liegen
die Skripte und Protokolle, damit sich nichts neu bauen muss, wer eine Zahl
nachrechnen oder eine Messung wiederholen will. Ein voller Durchlauf kostet
rund 45 Minuten echte API-Aufrufe.

## Werkzeuge

| Skript | Zweck |
|---|---|
| `haertetest.py` | N echte Faktensätze durch ein Modell, geprüft gegen die echte `_validate_hebel()`. `python -u haertetest.py 20 <modell-id>` |
| `screening.py` | Breitenmessung über alle erreichbaren `:free`-Modelle, 3 Fälle je Modell. Trennt **Format-** von **Transport**-Fehlern |
| `rueckspiel.py` | Historischer Rücktest: 38 Mistral-Entscheidungen mit bekanntem Ausgang, neu gespielt durch die Kandidaten |
| `rueckspiel_auswertung.py` | Auswertung auf der **gemeinsamen** Fallmenge — Rohzahlen des Laufs sind nicht vergleichbar, weil die Modelle unterschiedlich viele Fälle beantworteten |
| `schema_test.py` + `hebel_schema.py` | `json_object` gegen striktes `json_schema`, nur dieser Parameter verstellt |
| `parallel_voll.py` / `parallel_test.py` | Gleichzeitigkeit bei Volllast bzw. bei Kurzfragen |
| `reasoning_test.py` | Der 86-%-Befund: wie viel Wartezeit unangefordertes Reasoning kostet |
| `or_katalog.py`, `or_probe.py`, `or_endpoints_frei.py` | OpenRouter-Katalog, Erreichbarkeit, Endpunkt-Ebene |
| `hol_fakten.py`, `scan_export.py` | Ziehen einzelne Blöcke aus dem 125-MB-Notebook-Export, ohne ihn ganz zu laden |
| `nachtlauf.sh` | Die Kette, die über Nacht lief |

## Zwei Fallstricke, die hier eingebaut sind

**`hol_fakten.py` streamt** bis zum gesuchten Top-Level-Schlüssel und dekodiert
nur dessen Wert — der Export hat 125 MB, ihn ganz zu laden ist unnötig.

**Die Faktensätze liegen NICHT hier.** `fakten_*.json` wurden bewusst nicht
mitkopiert: sie sind groß und enthalten in 13 % der Fälle echte Positionsgrößen
in Euro. Wer sie braucht, zieht sie mit `hol_fakten.py` aus dem aktuellen Export
im Notebook-Analyseordner.

## Was beim Wiederholen zu beachten ist

* **`db.DB_PATH` vor dem ersten Import auf eine Kopie umbiegen** — `@track_api_health`
  öffnet bei JEDEM Client-Call eine Verbindung. „Kein DB-Test" heißt nicht
  „kein DB-Schreibzugriff".
* **Ausgabe nie durch `| tail` in einen Hintergrundlauf pipen** — die Pipe
  puffert bis zum Ende; ein 35-Minuten-Lauf war dadurch blind und beim Abbruch
  komplett verloren. Immer `python -u … > datei.log`.
* **Nicht zwei Messungen gleichzeitig** gegen denselben Anbieter — Rate-Limit-
  Konkurrenz verfälscht genau das, was gemessen werden soll.

## Die wichtigsten Protokolle

`screening.log` (13 Modelle) · `nem120_20.log` (20er-Härtetest des Siegers) ·
`laguna20.log` · `schema.log` (der Schema-Vergleich) · `parallel_voll.log` ·
`rueckspiel.log` (der historische Rücktest) · `nachtlauf.log` (Zeitstempel der Kette)
