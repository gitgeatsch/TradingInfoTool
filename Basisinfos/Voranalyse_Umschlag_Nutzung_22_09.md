# Voranalyse — `umschlag_naeherung` im Betrieb nutzen (22.09.2026)

> **Nutzerauftrag 21.09.:** *„führe eine Fachliche prüfung durch ob das
> Ergebnis und die Simulation ein besseres Ergebnis ist **und eine
> Voranalyse da wir auch die Qualität prüfen müssen wenn wir den Beitrag
> nutzen wollen**"*

⚠️ Diese Voranalyse **entscheidet nichts**. Sie legt den Ist-Stand am
Code, die Leser und Schreiber, die offenen Punkte und die Risiken hin —
so, wie es `voranalyse-vor-jedem-schritt` verlangt. Gebaut wird erst
nach der Abstimmung.

**Vorgelagert:** `Loesungskonzept_Umschlag_21_09.md` (was gemessen ist).

---

## 0. Die fachliche Prüfung zuerst — ist das Ergebnis besser?

**Nein — und das ist belegt, nicht vermutet** (Befund 2.518).

| | |
|---|---|
| Differenz NEU − ALT, gleicher Auswahlanteil | **+0,0453 R**, Band **[−0,0122 .. +0,1067]** — nicht trennbar |
| Positivkontrolle auf die Differenz (Methodik 2.105) | die Anlage **findet ab +0,02 R** |
| Nullkontrolle (gemischte Ränge) | +0,0112 — ein Teil der 0,0453 ist Maßverzerrung |

➤ **Die Anlage könnte einen Unterschied sehen. Sie sieht keinen.**
Damit ist der Nullbefund belegt und nicht nur behauptet.

⛔ **Mein erster Lauf meldete „NEU ist besser" (+0,1351 R) und war ein
Artefakt**: die neue Tabelle wählte nur 9,0 % je Tag aus gegen 23,6 % bei
der alten. Eine strengere Regel hat bessere Mediane **auch ohne bessere
Information**. Behoben durch Bisektion auf gleichen Auswahlanteil.

### ⚠️⚠️ Was das für die Entscheidung heißt

> **Der Gewinn der Näherung liegt in der ABDECKUNG, nicht in der
> BEWERTUNG. Wer sie einsetzt, kauft Vollständigkeit — nicht
> Treffsicherheit.**

Und das widerspricht **nicht** 2.515: dort ist gemessen, dass
`umschlag_naeherung` **trägt** (+0,0172 R gegen den Nullpunkt). Hier ist
gemessen, dass sie **nicht besser trägt** als die registrierte Tabelle.
Beides gilt nebeneinander — gut genug zum Aufnehmen, nicht gut genug zum
Verdrängen.

---

## 1. Ist-Stand am Code — wer liest, wer schreibt

### 1.1 Der Nenner (die Umlaufmenge)

| Datei | Definition | Schreiber | Takt | Symbole | im Betrieb gelesen? |
|---|---|---|---|---|---|
| `externe_reihen` / `coinmetrics_splycur` (Betriebs-DB) | **Gesamtausgabe** auf dem Ledger | `scheduler/background.py` (Block „Umlaufmenge für Turnover") | **täglich, automatisch** | ⚠️ genau `marktrang.messbasis("turnover")` | **ja** — `umlaufmengen()` |
| `data/onchain_historie.db` / `splycur` | dieselbe | `hole_fremdreihen.py splycur` | **von Hand, Desktop** | 66 | ja, als zweiter Ort |
| `data/umlaufmenge_cg.db` | **freier Umlauf** = Marktkap. / Preis | `hole_umlaufmenge_cg.py` (Vollabruf) | ⛔ **von Hand, kein Job** | 375 | ⛔ **nein** — `betriebsweg: None` |

### 1.2 Der Weg vom Nenner zum Signal

```
umlaufmengen()          Menge je Symbol   (nur SplyCur)
      │
turnover_werte()        Binance-24h-Stückvolumen / Menge
      │
raenge()                Querschnittsrang über den Markt  ->  turnover_fuenftel 0..4
      │
potential.bewerte()     Stufentabelle  ->  Punkte
      │
potential.schwelle      Vorgabe × (erreichbar_max / erreichbar_voll)
      │
Signal
```

### 1.3 ⚠️⚠️ Der Engpass sitzt **nicht** dort, wo ich ihn zuerst vermutet habe

Der Auffrischjob im Scheduler fragt

```python
_symbole = sorted(_MR.messbasis("turnover"))
```

— also **genau die Symbole, die die Messbasis führt**. Die Menge im
Betrieb ist damit nicht durch die Quelle begrenzt, sondern durch **diese
Zeile**. Wer nur den Leser erweitert und den Schreiber stehen lässt,
bekommt keine einzige zusätzliche Menge.

---

## 2. Was der Wechsel technisch verlangt — sechs Punkte

| # | Punkt | Warum | Aufwand |
|---|---|---|---|
| **1** | `umlaufmenge_cg.db` an den Betrieb anschließen (`betriebsweg` in `UMSCHLAG_GROESSEN` füllen) | die Näherungsmenge wird im Betrieb heute **gar nicht gelesen** | klein |
| **2** | Den Scheduler-Abruf auf die **breitere** Symbolmenge stellen | sonst bleibt es bei 66 (§ 1.3) | klein, aber Netzlast prüfen |
| **3** | ⚠️⚠️ **Die Driftsperre in den Betrieb ziehen** | das Messwerkzeug wirft Symbole mit Mengendrift über Faktor **6,53** und Tagessprung über **5** heraus; `turnover_werte()` hat **keine** solche Prüfung. Tokenumstellungen wandern sonst mit der Lösung ein | mittel — **vor** dem Nennerwechsel, nicht danach |
| **4** | ⚠️ **R-R9: die Schwelle neu kalibrieren** | `potential.py` trägt die Vorgabe auf der registrierten Tabelle (`3.15/0.83/0.22/-1.79/-2.40`). Wechselt die Tabelle, ist die Vorgabe eine andere Größe | mittel |
| **5** | Einen **Takt** für den CG-Abruf festlegen und in `datenfrische.py` eine Frist eintragen | heute Vollabruf von Hand, keine Frischegrenze — ein stiller Ausfall wäre unsichtbar | klein |
| **6** | `turnover_verfuegbar()` auf die neue Quelle ausweiten | er kennt heute nur `MESSBASIS["turnover"]`; sonst meldet jedes Messwerkzeug wieder eine falsche Abdeckung (der Fehler von 2.510) | klein |

✔ **Gut daran:** die Näherung braucht je Symbol **einen einzigen Wert**
(die jüngste Menge, rückwärts konstant) — nicht die 365-Tage-Historie.
Der laufende Job ist also deutlich kleiner als der Vollabruf.

---

## 3. Die Qualitätsprüfung — was steht, was fehlt

### ✔ Erfüllt und nachgewiesen

| Kriterium | Stand | Beleg |
|---|---|---|
| **R-R8/B1** Form | Regler gerechtfertigt — die Ordnung trägt bei wachsender Sperrbreite durchgehend | 2.516 |
| **R-R8/B2** Ebene | Querschnittsrang über den Markt, wie der registrierte Beitrag | 2.515 |
| **R-R8/B3** als Regel gerechnet | sechs von sechs Zeilen eigenhändig nachgerechnet, vier Nachkommastellen | 2.515-b3 |
| **R-R8/B4** Häufigkeit | ⚠️ als **Sperre gefallen** (0,8 % der Signale); als **Regler** erfüllt — 59,0 % der Signale bekommen einen Wert | 2.515-b4, 2.517 |
| **R-R8/B5** Trennschärfe | gegen den Nullpunkt gemessen, Nullwert abgezogen | 2.516 |
| **R-R8/B6** beide Hälften | +0,0179 / +0,0164, beide tragen, je 45 Blöcke | 2.515-b6 |
| **Saatprobe** | 5/5 Bootstrap **und** 4/4 Nullwelt, beide Zufallsquellen getrennt gedreht | 2.515-saatprobe |
| **Besetzung je Fünftel** | 58,3 bis 58,9 Anker — gleichmäßig, keine Median-Verzerrung | 2.517 |
| **Stufentabelle auf dem Messfenster** | H20 ab 2023 monoton, Spanne 5,38 | 2.517 |
| **Betriebsfolge simuliert** | 424 → 1.504 Werte; Durchlass 532 → 399; Hebel-Median 1,00 → 3,49 | 2.517 |
| **Qualität gegen die registrierte Tabelle** | kein Unterschied — **Nullbefund belegt** | 2.518 |

### ⛔ Offen — und jeder Punkt ist eine eigene Arbeit

| # | Offen | Warum es zählt |
|---|---|---|
| **O1** | ⚠️⚠️ **Die Nennerfrage (Schritt 67) wird durch die Näherung ENTSCHIEDEN, nicht umgangen** | Der Näherungsnenner ist `Marktkap. / Preis` — also **freier Umlauf**, nicht Gesamtausgabe. Wer die Näherung einsetzt, wechselt den Nenner. Ein Wechsel verschob früher **76,7 % aller Fünftel**, fast nur nach unten. ➤ Entschärft, aber nicht erledigt, durch 2.518: bei gleichem Auswahlanteil ist **kein Ergebnisunterschied** messbar. Die Entscheidung gehört trotzdem **benannt**, nicht eingeschmuggelt |
| **O2** | **Blockdeckung auf dem Messfenster** | über die ganze Historie **90 Blöcke** — komfortabel. Auf dem Fenster ab 2023 sind es **22** bei einer Grenze von 20. Das ist die alte Fragilität von Schritt 68 in kleiner Form |
| **O3** | **Der Näherungsfehler ist nur dort prüfbar, wo eine echte Menge existiert** | gemessen −0,0008 R auf 44 Symbolen. Für die übrigen 322 ist er **nicht messbar**, nur plausibel (die Menge ist träge) |
| **O4** | **Die funding-Lücke in der Simulation** | bei 1.407 von 2.550 Signalen (55,2 %) fehlt der funding-Rang; überall steht der Rückfall `funding = 2`. Die **Hebelzahlen** hängen damit an einer Annahme für den zweiten Beitrag. ⚠️ Der **Vergleich** alt gegen neu nicht — beide Seiten benutzen denselben Wert |
| **O5** | **R-R9 gerechnet, nicht nur benannt** | siehe § 2 Punkt 4 |
| **O6** | **Die Tabelle: welche gilt?** | 2.518 sagt: es macht für die Qualität keinen Unterschied. Dann ist es eine Frage der **Konsistenz**, nicht der Leistung — und die spricht für die Tabelle, die auf derselben Basis gerechnet ist wie die Anwendung |

---

## 4. Risiken

| Risiko | Wirkung | Gegenmittel |
|---|---|---|
| ⚠️⚠️ **Tokenumstellungen wandern mit der Lösung ein** | ein Faktor-1000-Fehler im Nenner erzeugt täglich einen falschen Spitzenrang — genau der Fall der Nennersperre | § 2 Punkt 3 **vor** dem Wechsel, und der Nachweis am **Seiteneffekt**, nicht an einer Textsuche |
| **Mehr Daten → weniger Signale** | der Durchlass sinkt von 532 auf 399 (20,9 → 15,6 %), weil mehr Werte die **volle** statt der gesenkten Schwelle erfüllen müssen | das ist **gewollt** (2.511-schwelle-belohnt-luecke), gehört aber dem Nutzer vorher gesagt |
| **Der Hebel springt** | Median 1,00 → 3,49; SOL, BTC, BNB an die Deckelgrenze 5,00 | erst nach Phase 4 / M1-Kriterium 2 freischalten, nicht mit diesem Paket |
| **Kein Qualitätsgewinn** | der Einsatz rechtfertigt sich allein über die Abdeckung | ausdrücklich so entscheiden — oder lassen |
| **Stille Quellenverwechslung** | drei Dateien, zwei Definitionen | `umschlag_name()` ist **abgeleitet** und liefert für eine vierte Quelle `unbekannt` — der Riegel steht schon |

---

## 5. Was der Nutzer entscheiden muss

| # | Frage | Meine Empfehlung |
|---|---|---|
| **E1** | Wird der Beitrag **allein wegen der Abdeckung** umgestellt, obwohl kein Qualitätsgewinn nachweisbar ist? | **ja** — 59 % statt 17 % Abdeckung beendet die Schwellensenkung bei der Hälfte der Fälle, und die Schwellensenkung ist ein **Nachteil ohne Gegenleistung** (2.511) |
| **E2** | Wird damit der **Nenner** von Gesamtausgabe auf freien Umlauf gewechselt (O1)? | **ja, und ausdrücklich** — 2.518 zeigt, dass es das Ergebnis nicht verschlechtert, und `umschlag_frei` ist definitorisch die richtige Größe (2.500) |
| **E3** | Welche **Stufentabelle** gilt? | die auf der Näherung **ab 2023** gerechnete (H20: +2,32 / +0,50 / +0,34 / −0,11 / −3,06) — gleiche Basis wie die Anwendung |
| **E4** | Geht der **Hebel** mit, oder nur Spot? | **erst Spot.** Der Hebel gehört an Phase 4 / M1-Kriterium 2, nicht an dieses Paket |
| **E5** | Reihenfolge | **erst die Driftsperre** (§ 2.3), dann der Nennerwechsel. Nicht umgekehrt |

---

## 6. Vorschlag für die Reihenfolge

```
1.  Driftsperre in `marktrang` und `messe_kandidaten_als_regel`   (§ 2.3)
       │  Nachweis am Seiteneffekt, nicht an einer Textsuche
2.  Mengenquelle anschliessen + Scheduler-Abruf erweitern         (§ 2.1, 2.2)
       │  danach: Abdeckung messen, nicht annehmen
3.  Frist in `datenfrische.py` + `turnover_verfuegbar` ausweiten   (§ 2.5, 2.6)
4.  Stufentabelle setzen (E3) und Schwelle neu kalibrieren (R-R9)  (§ 2.4)
5.  Betrieb pruefen: Pull + Neustart + Export nach ~30 Min
6.  ERST DANN der Hebel — als eigenes Paket in Phase 4
```

⚠️ **Nichts davon ist gebaut.** Die Reihenfolge ist ein Vorschlag zur
Abstimmung, kein begonnener Umbau.

---

## Belege

Befunde **2.515-\***, **2.516-ordnung-traegt**, **2.517-tabelle-fenster**,
**2.517-betriebssimulation**, **2.518-qualitaet-gleichwertig** ·
2.500 · 2.505-\* · 2.510-\* · 2.511-\* · 2.453-turnover · Methodik 2.105 ·
R-R8, R-R9, R-R11 · F-170, F-212, F-218

Werkzeuge: `phase4_c_ist_das_ergebnis_besser.py` ·
`phase4_c_betriebssimulation_naeherung.py` ·
`phase4_c_regler_oder_schalter.py` ·
`phase4_c_naeherung_konstante_menge.py` ·
`rechne_turnover_beitrag.py --umschlag naeherung --ab 2023-01-01`
