# Voranalyse: XDC in die Messbasis (30.10.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

*Auftrag des Nutzers vom 30.10.: „XDC: Aufnahme in die Messbasis als eigener Schritt mit Voranalyse?“ – „Ja unbedingt“. Alles hier ist nur lesend gelaufen bzw. auf einer Wegwerfkopie. Messbasis und Produktion sind unberührt.*

## 1. Lage

| | |
|---|---|
| Bestand | **14.999,69 XDC** (NB-Sicherung 29.10.) |
| Warum keine Messreihe | Die Messbasis lädt nur **Binance**, und dort ist XDC nicht gelistet |
| Was es gibt | Die Produktion am NB führt **1.029 Tageskerzen** (04.01.2024 bis 28.10.2026, Quelle `gemessen` = echter Kursabruf), dazu 395 Tage CoinGecko |
| Weg dafür | `uebernehme_messreihen.py` (D-1 vom 08.09.). Damit kamen schon AIOZ, HYPE, KAS u. a. herein; jede Zeile trägt die eigene Quelle `uebernommen_gemessen` |
| Aufnahmebedingungen | ✔ alle erfüllt: ≥ 400 Kerzen, Tagesabstand 1, Preise plausibel, je Tag eine Zeile |

⚠️ **Gefunden:** Das Werkzeug war seit dem 13.09. defekt. Der Messreihen-Status hat seitdem eine Spalte für die Assetklasse, und das Werkzeug brach beim Schreiben ab. Das ist **behoben** (eine Zeile). Am Prüfstand ist nachgewiesen, dass es jetzt sauber schreibt.

## 2. Wirkung auf die Grundgesamtheit (gemessen, nicht geschätzt)

Gemessen wurde über die ganze Historie: Rang nach Schnittabstand 200 T, gerechnet wie `marktrang`, je Tag mit und ohne XDC.

| | |
|---|---|
| Tage mit XDC im Rang | 792 (ab 21.07.2024) |
| Werte je Tag im Rang | Median 361 |
| **Fünftel-Wechsel der übrigen Werte** | **0,44 %** der Wert-Tage, höchstens **4 je Tag** |
| Zum Vergleich | Die Grundgesamtheitsfrage vom 20.09. galt mit 0,8 % als gelöst; damals lag der Ausgangswert bei 52,6 % |
| XDC selbst | meist oben (Fünftel 3: 389 Tage, 4: 286 Tage) |

**Beide Seiten (Regel 3 der Grundgesamtheit):** Der **Betrieb am NB rangt XDC schon heute.** `marktrang` ergänzt jeden Wert, der nicht auf Binance läuft, aus der Produktions-DB, sofern er mindestens 200 Tage hat und frisch ist. Nur der **Messung** fehlt XDC. Eine Aufnahme **gleicht die beiden Seiten an**. Am NB ändert sich dadurch nichts.

## 3. Eine Falle, die gemessen wurde

Die Messbasis ist seit dem **20.09. eingefroren**. Der Frischewächter in `marktrang` prüft nur die **jüngste Zeile der ganzen Datei**. Eine XDC-Reihe bis 28.10. würde ihn **blind** machen: Die 40 Tage alte Basis sähe auf einen Schlag frisch aus. Das ist am Prüfstand nachgewiesen (vorher „kein Rang“, nachher 518 Werte).
→ Deshalb wird XDC **zum 20.09. gekappt**, so wie die übrige Basis.

## 4. Deine Entscheidung

| | Weg | Folge |
|---|---|---|
| **a (Empfehlung)** | XDC übernehmen, **bis 20.09. gekappt**, Quelle `uebernommen_gemessen` | danach Urteilsvergleich vorher/nachher (`pruefe_messbasis_wechsel.py`, R-R11) und volle Suite; die Prüfung „gehaltene Position ohne Messreihe“ wird für XDC grün. **Am NB nichts** |
| b | Übernehmen bis heute | ⛔ macht den Frischewächter blind, nicht empfohlen |
| c | Nicht aufnehmen | Die Prüfung bleibt für XDC rot oder bekommt eine Ausnahme. Gilt nur, falls du XDC bald verkaufst |

⚠️ **Erinnerung:** Am 07.10. hast du gesagt *„ich schalte später XDC ab, mach bitte eine Erinnerung“*. Willst du XDC weiter halten, ist **a** richtig. Verkaufst du bald, genügt **c**.

**Antwort genügt so:** „XDC a“ (oder c).

---

## 5. UMGESETZT (Nutzer 30.10.: „xdc wird auch längerfristig gehalten“ → a)

| | |
|---|---|
| Geschrieben | `data/messdaten.db` (Desktop): XDC **991 Tage**, 04.01.2024 bis **20.09.2026**, Quelle `uebernommen_gemessen`, Status `uebernommen`. Quelle war die NB-Sicherung vom 29.10. (nur gelesen) |
| Frischewächter | jüngster Tag der Datei weiterhin **2026-09-20** ✔ |
| Anker vorher/nachher (`pruefe_messbasis_wechsel.py`) | **alle 7 bitgleich**, Symbole 536 → 536 |
| Suite Neuaufnahme | XDC **grün**; CANTON als Kernposition mit Grund ausgenommen (Nutzer 30.10.). Rot bleiben nur **ASTER (388), MON (339), CANTON (109)**: zu kurz, also eine Datenlage-Grenze |

⚠️ **Korrektur zu §2:** Die Messungen rangen nicht über die ganze Datei, sondern über die **eingefrorene Messmenge `messmenge.V1`** (R-R11). XDC ist nicht in V1. Darum ist der Ankervergleich **bitgleich**, und die gemessenen 0,44 % wirken heute **nicht**. Sie würden erst wirken, wenn eine neue Messmenge V2 zusammengestellt wird. Das wäre ein eigener Schritt, und dann gilt die Zahl aus §2. Gewonnen ist jetzt: XDC **hat** eine Messreihe und ist damit für jede Messung verfügbar, die sie anfordert.

Rückgängig machen: `DELETE FROM price_history_ohlc WHERE symbol='XDC' AND quelle='uebernommen_gemessen'` sowie die Zeilen XDC in `messreihen` und `messreihen_status`.
