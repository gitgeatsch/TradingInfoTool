# Voranalyse — REGEL0 auf der HEBEL-ASSETLISTE des Nutzers (30.09.2026)

**Auftrag (Nutzer 30.09.):** *„Ja, Messung auf meiner Hebel-Assetliste vorbereiten, prüfen und gegenprüfen. Bei 3. zu den
Mindestbedingungen reden wir noch einmal, wenn wir zu diesem Schritt kommen. Ich denke, wir können und müssen die bestehende Hebel-
und Spot-Achse (laut Plan) ersetzen, ein Parallelbetrieb wird schwierig. Nach der Assetliste gehen wir nach deinem korrigierten
Plan und REGEL0 (auf REGEL1 etc.) vor."*

> **Urteil in einer Zeile:** Wir spielen die **REGEL0 unverändert** nur auf den Assets deiner Hebel-Liste durch. Das ist die
> Betriebswirklichkeit, denn du handelst diese Liste. Keine Wahl, keine neue Zahl, nur Auskunft.

---

## 1. Die Liste und ihre Datenlage — geprüft

| | |
|---|---|
| Quelle | `asset_hebel_settings` in `data/tradinginfotool.db`, **nur lesend**. ⚠️ Das ist die **Desktop-Kopie vom 24.09.**, die Produktion liegt am Notebook. Ist die Liste noch aktuell? |
| Umfang | **43** Assets mit Hebelprüfung erlaubt |
| **mit Stundendaten** | **28** |
| ⛔ **ohne Stundendaten (15)** | KAS, FLOKI, AKT, AIOZ, BRETT, PLUME, SUPRA, CAT, GRIFFAIN, MON, CANTON, ASTER, HYPE, VSN, XNO. Das ist die bekannte Lücke *vier Symbolwelten* (2.612) und wird hier **nicht** behoben (D ist derzeit keine Option) |
| ⚠️ **BTC** | hat Stundendaten, wird im Lader aber **bewusst ausgeschlossen**, weil es der Leitwert des Marktes ist (`messe_e2_beitraege.py`). BTC ist damit **nie als handelbares Asset** gemessen worden |
| ⚠️ MORPHO | Daten erst ab 2025-10, zu kurz für das 12-Monats-Normal, daher keine Kern-Einstiege |
| **messbar** | **26 Assets** mit Kern-Einstiegen (bestand): 1.679 von 7.814 Einstiegen 2024–26 |

---

## 2. Der Aufbau — REGEL0 unverändert

| | |
|---|---|
| Einstiege | aus der **bestand**-Messung. Modell und Normal kommen aus **allen** 116 Symbolen, gehandelt werden nur deine 26 (E-31: Die Skala hängt an der Grundgesamtheit, und der Betrieb rechnet ebenfalls auf der ganzen Menge) |
| Hebel, Kosten, Geometrie | REGEL0: ATR, Grenze 2 %, Markpreis, 24 h ohne Ziel, Bitpanda-Kosten |
| Zeitraum | 2025-01..2026-08 (dazu 2024 als Auskunft) |
| Menge | nur **bestand**. Die unverzerrten Mengen sind Stichproben und enthalten nur 10–26 deiner Assets. Die eingestellten Paare betreffen deine heutige Liste nicht |

**Ausgaben (alle Auskunft):**
1. Hebelkonto, Spotkonto, Rohvorteil je Handel, je Jahr, Juli–Dezember 2025, mit/ohne 10./11.10., Nullwelt
2. **je Asset**: Einstiege, Rohvorteil, Liquidationen. Das ist Information für **deine** Auswahl (Mail-Auskunft erlaubt, Regel 3), keine Bewertung von Assets
3. **Liste gegen Rest** von bestand: Ist deine Liste besser oder schlechter als die übrigen 88 Assets?
4. **Gegenprüfung Zufall**: 40 zufällige Listen aus 26 bestand-Assets. Liegt deine Liste über ihnen? Das zeigt, ob die Auswahl selbst etwas bringt

---

## 3. ⚠️ Was die Zahl NICHT bedeutet — gegengeprüft

1. **Überlebensverzerrung:** Deine Liste ist die **heutige**. Die Assets gibt es noch, und du hast sie in Kenntnis ihrer Entwicklung gewählt. Die Vergangenheit
   sieht deshalb **zu gut** aus. Die Zahl zeigt die Betriebswirklichkeit **ab jetzt**, nicht, was du 2025 verdient hättest.
2. **Kleine Menge:** 26 Assets mit etwa 1.700 Einstiegen sind etwa ein Fünftel von bestand. Die Streuung ist größer.
3. 2025–26 ist gesehen, und das Urteil gilt weiter nur in der Form *besser als heute, ehrlich belegt* (E-34).
4. 15 Assets der Liste fehlen, dazu BTC. Die Messung sagt über sie **nichts**.

---

## 4. Umfang

1. die Einstiegsdatei auf deine 26 Assets filtern (`kern48_einstiege_liste.csv`), dazu die Wucht-Datei
2. `messe_k6_hebelstufe.py --kurs mark --einstiege kern48_einstiege_liste.csv --simulation 24,ohne,0.02` auf bestand, dazu `--je-asset` (neu: die Tabelle je Asset)
3. derselbe Lauf auf **allen** bestand-Einstiegen mit `--je-asset` für *Liste gegen Rest* und die Zufallslisten. Die Auswertung danach ist rein rechnerisch.

Zwei Läufe zu je etwa 12 Minuten. **R-R11:** Der Lauf auf allen Einstiegen muss N4 bestand bitgleich treffen (+0,2038).

---

## 5. Zur Abstimmung (H1–H3)

| # | Vorschlag |
|---|---|
| **H1** | Liste = Desktop-Kopie vom 24.09. (43), **falls noch aktuell**, gemessen werden die 26 Assets mit Daten |
| **H2** | REGEL0 unverändert, nur bestand, Ausgaben 1–4 als Auskunft |
| **H3** | BTC bleibt wie im Lader ausgeschlossen, die fehlenden 15 werden nur ausgewiesen. Eine BTC-Messung als Asset wäre eine eigene Frage |

**Notiert (Nutzer):** Die Mindestbedingungen für den Betrieb besprechen wir, wenn der Schritt kommt. Die bestehende Hebel- und Spot-Achse wird
laut Plan **ersetzt**, ein Parallelbetrieb ist schwierig.
