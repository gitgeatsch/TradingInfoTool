# Die letzte Stundenkerze bleibt für immer offen

**25.09.2026** · gefunden beim Gegenprüfen der neu geladenen BTC-Reihe ·
Prüfung `pruefe_leitwert_und_regimeform.py` (P1 und P5)

**Nutzerhaltung:** *„wenn es um eine Korrektur gehen sollte bin ich sogar der
Meinung, dass sowohl der Betrieb und in den Messdaten korrigiert wird"*

---

# § 1 Der Befund in einem Satz

> ⚠️⚠️ **Die jeweils letzte Stundenkerze jedes Symbols war beim Laden noch
> OFFEN und bleibt es dauerhaft** — kein Lauf korrigiert sie je. Median der
> Volumenquote **0,736**, bei 43 von 116 Symbolen unter 60 %.

⭐ **Entscheidend ist das Wort „dauerhaft".** Eine gerade laufende Kerze wäre
harmlos — sie würde beim nächsten Lauf abgeschlossen. Hier bleibt sie stehen:
**43 Symbole tragen eine unvollständige Kerze vom 24.09.**, und es ist
2026-09-25 17:34.

---

# § 2 Wie es gefunden wurde — durch eine Prüfung, die fast grün gelaufen wäre

Der Fund war ein **Nebenprodukt**. Geprüft werden sollte, ob die für den
Leitwert frisch geholte BTC-Reihe dieselbe ist wie die in der Messbasis
(P1, Bitgleichheit). Ergebnis: **1 von 26.872 Stunden abweichend**, und zwar
um 110 %.

**Der Einzelfall, BTC, Stunde 2026-09-24 15:00:**

| | open | high | low | close | Volumen |
|---|---|---|---|---|---|
| **Messbasis** (damals geladen) | 83673,77 | 84100,01 | 83508,00 | 84080,01 | **481,36** |
| **Binance** (heute geholt) | 83673,77 | **84468,01** | 83508,00 | **84418,00** | **1011,04** |

⭐ **`open` und `low` stimmen exakt** — es ist dieselbe Kerze. Nur `high`,
`close` und Volumen fehlten, weil die Stunde noch lief. Genau die Größen, die
sich innerhalb einer Stunde noch ändern können.

⚠️ **Hätte ich die abweichende Stunde als „Rundungsfehler" abgetan, wäre der
Befund verloren gewesen.** Die Prüfung weist deshalb nicht nur die *Zahl* der
Abweichungen aus, sondern ihre **Größe** — 110 % ist keine Rundung.

---

# § 3 Die Ursache — zwei Zeilen, die zusammen wirken

In `hole_stundenkurse.py`, Funktion `main()`:

```python
vorh  = c.execute("SELECT MAX(stunde) ... WHERE symbol=?").fetchone()[0]
start = _ms(vorh) + 3_600_000 if vorh else _ms(von)   # (1) ab MAX + 1 Stunde
...
"INSERT OR IGNORE INTO stundenkurse VALUES (?,?,?,?,?,?,?)"   # (2) IGNORE
```

| | |
|---|---|
| **(1)** | Der Start liegt **hinter** der letzten gespeicherten Stunde — sie wird nie wieder abgerufen |
| **(2)** | Und selbst bei einem erneuten Abruf würde `IGNORE` sie nicht überschreiben |

➤ **Jede der beiden allein wäre harmlos.** Zusammen machen sie den Fehler
dauerhaft. Das ist der Grund, warum er über Monate unentdeckt blieb.

---

# § 4 ⚠️ Die Abgrenzung — und warum sie nötig war

**Nutzerhinweis während der Prüfung:** *„vorsicht es gibt auch komprimierte
oder verkürzte daten"* — und *„u.U. meine ich andere daten die du von GB auf
ein paar kB zusammengefasst hast"*.

Der Hinweis war berechtigt: meine erste Messung verglich vier Tabellen
miteinander, die nicht vergleichbar sind.

| Tabelle | Median-Quote | letzte Zeitpunkte | Diagnose |
|---|---|---|---|
| **`stundenkurse.db`** | **0,720** | 2026-09-24 15:00 (43 Sym.), 09-16 (33) | ⚠️ **offene Kerzen** |
| **`btc_leitwert.db`** | **0,086** | 2026-09-25 **17:00** | ⚠️ **derselbe Fehler, von mir gebaut** |
| `messdaten.db` | 0,502 | 2026-09-03 (690 Sym.), 09-20 (348) | ✔ **kein** offene-Kerze-Fall |
| `tradinginfotool.db` | **4,084** | 2026-08-19 | ✔ **kein** offene-Kerze-Fall |

⭐ **Die entscheidende Prüffrage war: ist die letzte Zeile überhaupt die
laufende Periode?** Nur dann kann sie offen sein. Bei den Tagesdaten ist sie
Wochen alt — dort hat der niedrige Median eine **andere** Ursache (gemischte
Assetklassen, Wochenenden, Feiertage). Und ein Median von **4,084** kann per
Definition keine unvollständige Kerze sein.

➤ **Ohne diese Trennung hätte der Befund drei Datenbanken beschuldigt, von
denen zwei unschuldig sind.**

⚠️ **Und der Geräteaspekt:** am Desktop sind alle Dateien voll (nur
`stundenkurse.db` trägt `_nur_messbasis`). Die verkürzten Fassungen
(`_nur_symbolliste` 12–16 KB, `_nur_betrieb` 368 KB) liegen am **Notebook** —
und dort läuft `hole_stundenkurse.py` nicht. Die Korrektur betrifft also nur
den Desktop.

---

# § 5 ✔ Was bereits korrigiert ist

**Beide Lader**, und der zweite ist der unangenehmere Teil:

| Datei | Änderung |
|---|---|
| `hole_stundenkurse.py` | Start bei **`MAX(stunde)`** statt `+1 Stunde` · `INSERT OR **REPLACE**` |
| `hole_btc_leitwert.py` | ⚠️ **dasselbe** — ich hatte den Fehler beim Bauen des Leitwert-Laders **nachgebaut** |

⚠️⚠️ **Der zweite Punkt gehört ausdrücklich hingeschrieben:** ich habe am
25.09. einen Lader gebaut, der einen Fehler wiederholt, den dasselbe Werkzeug
wenige Minuten später aufdeckte. Kopierte Struktur bringt kopierte Fehler mit
— und die eigene, frische Datei war mit Quote **0,086** die am schlechtesten
betroffene von allen.

Kosten der Korrektur: **ein Abruf mehr je Symbol und Lauf.**

---

# § 6 ⏳ Was noch offen ist

| # | |
|---|---|
| **1** | **Die vorhandenen 116 Kerzen korrigieren.** Wartet, bis der laufende Regime-Lauf `stundenkurse.db` freigibt — ein Schreibzugriff während seines Lesens riskiert eine Sperre |
| **2** | ⭐ **R-R11 danach:** die Korrektur berührt **2.784 von 3.244.186 Ankern = 0,0858 %** (Anker `n−25` schaut mit H=24 bis zur letzten Kerze). Klein, aber nicht null → **2.597 ist nachzumessen und gegen die alten Zahlen zu halten** |
| **3** | Prüfen, ob `hole_terminmarkt_historie.py` und die übrigen `hole_*.py` dasselbe Muster haben. **Vorbefund:** nur diese zwei nutzen `INSERT OR IGNORE`, die anderen vier nutzen `REPLACE` — und ihre Zeitspalten sind Momentanwerte (Open Interest, Funding), keine Aggregate über die Stunde, können also nicht „offen" sein |

---

# § 7 Die Lehre, allgemein

> **Eine Wiederaufnahme, die nur vorwärts kennt, friert den Rand ein.**

Dasselbe Muster hatte schon die BTC-Lücke verursacht: `hole_stundenkurse.py`
setzt bei `MAX(stunde)` an, also wird ein Symbol, dessen Quellspanne sich nach
**hinten** erweitert, nie nachgeholt. Zweimal derselbe Konstruktionsfehler,
einmal am linken und einmal am rechten Rand der Reihe.

➤ **Beim Bau eines inkrementellen Laders sind es immer zwei Fragen:** *Was
fehlt am Ende?* **und** *was fehlt am Anfang — und ist der zuletzt
geschriebene Wert überhaupt endgültig?*

---

# § 8 ✔✔ ERLEDIGT — Korrektur und R-R11 (Nachtrag 25.09., 20:0x)

## 8.1 Die Korrektur

`korrigiere_letzte_kerze.py` — ein **gezieltes** Werkzeug, nicht der Lader.

⚠️ **Warum nicht einfach `hole_stundenkurse.py`?** Der ist korrigiert und
hätte die Kerzen mitabgeschlossen, aber er holt ab `MAX(stunde)` **bis zum
Ende der Terminmarkt-Spanne** — womöglich tausende neue Kerzen je Symbol.
Dann wäre die Ankermenge von 2.597/2.598 verschoben und **R-R11 nicht mehr
führbar**: man könnte nicht unterscheiden, ob eine Abweichung von der
Kerzenkorrektur oder von neuen Daten kommt.

| | |
|---|---|
| **geändert** | **43** von 116 |
| schon richtig | 73 (deren letzte Kerze war beim Laden bereits abgeschlossen) |
| Fehler | **0** |
| Sicherung | `data/kerzen_vor_korrektur_2026_09_25.db` (20 KB, 116 Zeilen) |
| Dauer | 77 Sekunden |
| **Median-Volumenquote** | **0,736 → 1,060** |

⭐ **Die 43 sind exakt die Zahl, die vorher als „unter 60 % Volumenquote"
gemessen wurde.** Zwei unabhängige Wege, dieselbe Menge — das bestätigt den
Befund nachträglich.

## 8.2 ⭐ Die Riegel, am Seiteneffekt nachgewiesen

Ein Schutz, den niemand ausführt, ist keiner. Beide wurden gegen
**Wegwerfdateien** geprüft, bevor die echte Korrektur lief:

| Fall | Ergebnis |
|---|---|
| Datei mit Marke `_nur_symbolliste` | ✔ **ABBRUCH** vor jedem Schreibzugriff |
| unmarkierte Datei mit nur 24 Zeilen | ✔ **ABBRUCH** („zu wenig für die volle Messbasis") |

⚠️ Das ist der Notebook-Schutz: dort liegen die verkürzten Fassungen, und
eine Korrektur darf da keinen Seiteneffekt haben.

## 8.3 ✔✔ R-R11 — die Toleranz war VORAB hergeleitet

`pruefe_rr11_stundenkerze.py`, Toleranz aus der Geometrie gerechnet statt
gesetzt:

```
Anker i liest Kerze n-1  <=>  i >= n-1-H       und  gueltig nur bis n-25
    H = 6   ->  i >= n-7   -> alle gesperrt     ->  0 Anker
    H = 12  ->  i >= n-13  -> alle gesperrt     ->  0 Anker
    H = 24  ->  i >= n-25  -> genau EINER       ->  1 Anker je Symbol
|dE[R]|  <=  116 / 3.237.922 * (CRV+1)
```

| Probe | Vorhersage | Gemessen |
|---|---|---|
| **H6 / H12** | **bitgleich** | ✔ **40 Zellen, 0 Abweichungen** |
| **H24** | ≤ 0,000090 | ✔ **0,000010** — **11,2 %** der Grenze |
| Aussagen von 2.597 | Stopneutralität k≤1,0 · NETTO-Rang Fünftel 4 | ✔ 0 Verletzungen |

⭐ **Die Bitgleichheit bei H6/H12 ist der schärfste Teil:** dort hätte *jede*
Abweichung einen Fehler in der Korrektur bedeutet, nicht ein Rauschen.

## 8.4 ⚠️ Und die Positivkontrolle des Prüfwerkzeugs

Eine Selbstprobe (Datei gegen sich selbst) zeigt nur, dass Gleiches als
gleich erkannt wird — **nicht, dass Unterschiede gefunden werden.** Deshalb
zwei gepflanzte Abweichungen:

| | |
|---|---|
| 0,00001 in einer H6-Zelle | ✔ **gefunden** (Bitgleichheit bricht) |
| 0,001 in einer H24-Zelle | ✔ **gefunden** („ausgeschöpft 1116,5 %") |

⚠️ **Und ein Logikfehler, den erst die Selbstprobe zeigte:** bei Differenz
null überall blieb die interne Variable auf `None`, und die Prüfung meldete
*„keine H24-Zelle"* — obwohl 20 vorlagen. **Eine Prüfung, die bei perfektem
Ergebnis meldet, sie habe nichts gefunden, ist wertlos:** Erfolg und Ausfall
wären nicht unterscheidbar.

➤ **Alle drei offenen Punkte aus § 6 sind damit erledigt.** Punkt 3 bleibt
als Vorbefund: nur diese zwei Lader nutzten `INSERT OR IGNORE`, die übrigen
vier nutzen `REPLACE` und führen Momentanwerte (Open Interest, Funding), die
per Definition nicht „offen" sein können.
