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


---

## 6. Rückmeldung des Nutzers (30.09.) — Liste und MORPHO

**Nutzer:** *„Nein, es haben sich einige Assets geändert, aber der Großteil ist noch ok. MORPHO verstehe ich nicht. Das System braucht
keine Historie, um bei der Prüfung den Einstieg zu bewerten, oder?“*

- **Liste:** Die Desktop-Kopie ist **nicht aktuell**. Die aktuelle Liste kommt vom Nutzer (Änderungen nennen oder eine Mini-Abfrage am Notebook, nur lesend, nur diese Tabelle).
- **MORPHO, geprüft am Code:** Das Signal braucht wenige Tage (rsi 14 h und 10 Tage für den Monatsabstand, Ruhe 48 h, ATR etwa 14 Tage). Nur das
  **eigene Normal** verlangt **volle 12 Monate** (`normal()`: `st - st[0] >= JAHR_H` mit 8.760 h). MORPHO (ab 2025-10) hätte erst ab 2026-10 Signale.
  Das betrifft **12 von 28** Assets der Liste in ihrem ersten Jahr. ➤ Eingetragen als **Schwäche 4** der REGEL0 und Kandidat **J** (Marktnormal für junge Assets).


**Rückmeldung 2 (Nutzer 30.09.):** *„1. An den Hebelassets (Hebelschalter) hat sich nichts geändert. 2. An Spot-Assets hinzugekommen: PLUME,
XDC Network, Injective. Anmerkung: Die erforderliche Mindesthistorie ist eigentlich ein Showstopper und keine Schwäche."*
- ✔ **H1 erfüllt:** Die Hebel-Liste (43) vom 24.09. gilt unverändert.
- Die Spot-Zugänge PLUME, XDC und INJ betreffen den **Spot-Arm**, nicht diese Messung. Notiert.
- ⛔ Die Mindesthistorie ist als **Showstopper** eingestuft (`REGEL0_Hebel_Entwurf_30_09.md` Abschnitt 8). Vorschlag: **zuerst beheben**, dann diese
  Messung. Sonst fehlen die 12 jungen Assets der Liste gerade in ihrer Anfangszeit.

---

## 7. ✔ START (Nutzer 01.10.2026) — Umsetzung mit der FESTGESCHRIEBENEN REGEL0 (mit J)

**Nutzer:** *„Ja, mit 5 Hebel-Liste weiter, prüfen und gegenprüfen."* Einen Export vom Notebook braucht es dafür nicht, die Hebel-Liste ist unverändert.

- **Einstiege:** `kern48j_einstiege_bestand.csv` (REGEL0 mit J), gefiltert auf die Liste → `kern48j_einstiege_liste.csv`. **27 Assets** (mit J jetzt auch MORPHO)
  und **2.247 Einstiege**, davon 570 neu durch J. Ohne Einstiege: BTC (Leitwert) und die 15 Assets ohne Stundendaten.
- **Lauf 1:** alle bestand-Einstiege mit `--je-asset` (neu: je Asset Handel, Rohvorteil, Log-Beitrag zum Konto, Liquidationen). **R-R11:** muss die REGEL0-Referenz
  bestand treffen (9.905 · +0,2634 · +0,583 %), und die Summe der Log-Beiträge je Asset muss das Konto ergeben.
- **Lauf 2:** nur die Liste mit `--je-asset --gruppe`: S1–S5 mit eigener Nullwelt, dazu neu gegen reif.
- **Danach, rein rechnerisch aus Lauf 1:** die Liste gegen den Rest und gegen **40 zufällige Listen** aus 27 bestand-Assets (Rohvorteil je Handel und Konto).


---

## 8. ERGEBNIS — Befund 2.700

Belege `Basisinfos/Hebelliste_01_10/` (`alle__bestand.txt`, `liste__bestand.txt`).

| | deine Liste | alle bestand-Assets (REGEL0-Referenz) |
|---|---|---|
| Assets mit Handel 2025–26 | **25** (von 43) | 112 |
| Handel | 1.598 | 7.322 |
| **Hebelkonto** (log) | **+0,2063 (×1,23)** | +0,2634 (×1,30) |
| S1 2025 / 2026 | ✔ +0,127 / +0,080 | ✔ +0,253 / +0,010 |
| S2 Nullwelt P90 | ✔ −0,269 | ✔ |
| S4 Hebel gegen Spot | ✔ +0,206 gegen +0,091 | ✔ |
| ohne 10./11.10.2025 | +0,227 | |
| **Rohvorteil je Handel** | **+0,87 %** gegen 0,48 % Kosten | +0,58 % |
| größter Rückgang (log) | **0,083** | 0,637 |
| Juli–Dezember 2025 (Gegenwind) | **+0,006** | |
| Assets mit positivem Rohvorteil | **96 %** | 84 % |
| junge Assets (J) | +1,19 % Rohvorteil (268 Handel) | |

**Gegenprüfung — trägt die Auswahl selbst?**

| | Rohvorteil je Handel |
|---|---|
| deine Liste (25) | **+0,87 %** |
| der Rest von bestand (87) | +0,50 % |
| 1.000 zufällige Listen zu 25 Assets | Mittel +0,59 %, P90 +0,73 %. **Nur 0,4 %** erreichen deine Liste |

✔ **R-R11:** Der Lauf über alle ist bitgleich zur REGEL0-Referenz. Die Summe der Beiträge je Asset ergibt das Konto, und die Liste ist in beiden Läufen gleich (+0,2063).

**Je Asset** (Rohvorteil je Handel, Auskunft für deine Auswahl, keine Bewertung von Assets): TAO +2,51 · VIRTUAL +2,32 · KAITO +1,81 · RENDER +1,54 ·
NEAR +1,47 · W +1,26 · QNT +1,22 · IMX +1,21 · IO +1,10 · AVAX +0,92 · BEAMX +0,81 · BIO +0,76 · ALGO +0,73 · BNB +0,72 · SOL +0,66 · SUI +0,64 ·
ETH +0,57 · MORPHO +0,52 · APT +0,51 · ONDO +0,44 · LINK +0,43 · INJ +0,39 · SEI +0,23 · TURBO +0,00 · XLM −0,48 (Prozent).

**Ohne Handel:** KAIA und S. Ihre Markpreis-Monate sind **gesperrt**, weil unter dem Ticker früher ein anderes Instrument lief (K7). Dazu BTC (Leitwert, eigener Schritt
analog J) und 15 Assets ohne Stundendaten.

⚠️ **Der Vorbehalt, ehrlich:** Deine Liste ist die **heutige**, gewählt in Kenntnis der Entwicklung. Assets, die schlecht liefen, sind vermutlich nicht
mehr darin. Die Vergangenheit sieht dadurch zu gut aus, und der Abstand zu den Zufallslisten ist zum Teil **Rückschau**. Der echte Beleg kommt aus dem
**Betrieb** mit deiner Liste ab jetzt, wie du es gesagt hast.

**Zwischenfazit zum Ziel:** Zum ersten Mal ist die REGEL0 auf der **praktisch gehandelten** Grundgesamtheit **nach Kosten mit Hebel positiv**, in beiden
Jahren, mit kleinem Rückgang und ohne Verlust im Gegenwind. Die Kostenlücke der REGEL0 (S3) sitzt vor allem in den Assets, die du **nicht**
handelst.
