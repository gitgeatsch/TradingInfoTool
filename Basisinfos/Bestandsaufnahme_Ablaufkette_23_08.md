# Bestandsaufnahme der Ablaufkette — 23.08.2026

*Nutzervorgabe: „vollständige Bestandsaufnahme, sonst bauen wir wieder einen
Fleckerlteppich."*

> **Alles hier ist gemessen oder am Code gelesen.** Wo ich schätze, steht es
> daneben. Wo eine frühere Aussage von mir falsch war, steht sie mit ⚠️ und
> Korrektur.

---

## 0. Die kürzeste Fassung

| | |
|---|---|
| **Was filtert heute wirklich** | eine **Uhr** (Cooldown), nicht eine Aussage |
| **Was der Vorfilter H leistet** | ⚠️ **gemessen +0,15 R je Trade** über 523 Reihen (Kapitel 119–124). Der Schatten zeigt an einem Tag 0 von 51 — das ist ein Tag, keine Widerlegung |
| **Was den Hebel entscheidet** | seit S6b **nichts** — er ist immer 1,0 |
| **Was das System an Auswahl kann** | Trefferquote **27,8 %** gegen Basisrate **33,3 %** |
| **Fleckerlteppich, gemessen** | **5 Module** laufen nirgends, **8** nur außerhalb der Kette, **27 config-Schlüssel** liest niemand |

---

## 1. Der Umlauf — was passiert, wenn ein Krypto-Asset dran ist

**Gemessen an der `Durchlaessigkeit`-Zeile des Produktionslogs** (22.08.,
krypto/spot, 41 Symbole):

| Stufe | durch | verloren | was sie prüft |
|---|---:|---:|---|
| `auftrag` | 41 | 0 | Instrument × Strategie zulässig |
| `fakten` | 41 | 0 | Mindestgrundlage vorhanden |
| `lagebild` | 41 | 0 | Rolle A gelaufen |
| **`anlass`** | **30** | **11** | ⚠️ **Fingerabdruck** — hat sich der Faktentext geändert? |
| **`wiederholung`** | **0** | **30** | ⚠️ **Cooldown** — eine Uhr |
| `urteil` | 0 | 0 | Rolle BC |

> ⚠️ **Der einzige wirksame Filter ist die Uhr.** Der Fingerabdruck blockiert
> 27 %, der Cooldown den ganzen Rest. Alles, was danach kommt — Rolle BC,
> Gegenprüfung, Vertrag, Rechnung — bekam an diesem Tag **kein einziges
> Symbol** zu sehen.

**Seit der Reparatur vom 23.08.** (Cooldown Krypto 15 h → 3,5 h) läuft die
Uhr viermal schneller. **Das ändert nichts an der Bauart:** es filtert
weiterhin die Zeit, nicht die Eignung.

---

## 2. Die deterministische Komponente

### 2.1 Was das Modell an Fakten bekommt

`lagebeschreibung.geteilt()` liefert **11 Blöcke**. Gemessen an einem
Krypto-Fall:

| Block | Sätze | Zustand |
|---|---:|---|
| `verlauf` | 2 | ✔ |
| `volumen` | 2 | ✔ |
| `marken` | 1 | ✔ |
| `luecken` | 1 | ✔ |
| `bestand` | 1 | ✔ |
| **`hebelgeometrie`** | 2 | ✔ **seit 23.08. wieder** (Kapitel 143) |
| **`finanzierung`** | 1 | ✔ **seit 23.08. wieder**, bedingt formuliert |
| `fundamental` | 0 | leer — Krypto hat keine |
| `referenz` | 0 | leer im Testfall |
| `umschlag` | 0 | leer im Testfall |

**Dazu aus `positionierung`** (Rolle G): Open Interest, Finanzierungsrate,
Retail-Anteil, Börsenflüsse, COT, Short Interest, Insider, Skew, Stablecoin.

### 2.2 Die Rechnung — und ⚠️ der schwerste offene Defekt

**Es gibt zwei Rechnungen nebeneinander.** Der Docstring der einen sagt selbst,
dass das ein Fehler ist (*„Zwei Rechnungen an zwei Orten sind der Fehler, an
dem in diesem Projekt schon einmal Werte auseinandergelaufen sind"*).

| | `rechne()` — **die Produktion** | `dimensioniere()` — **die Messung** |
|---|---|---|
| Felder | 32 | 14 |
| Hebel woher | **`instrument`** (der Lauf) | **`hebel_handelbar`** (die Gruppe) |
| hält fest | den **Betrag** | das **Risiko** |

⚠️ **Seit S6b ist `instrument` immer `"spot"`. Folge: Hebel immer 1,0.**

| 22.08. | Signale | mit Hebelspalte |
|---|---:|---:|
| bis 11:30 (zwei Läufe) | 97 | 55 |
| ab 11:30 (ein Lauf) | 16 | **0** |

**Und der tiefere Unterschied** (Produktionswerte: Verlustanteil 6 %, Einsatz
800 €, Budget 48 €):

| Stop | `rechne()` Betrag | **Verlust am Stop** | `dimensioniere()` Betrag |
|---:|---:|---:|---:|
| 2,5 % | 800 € | **20 €** | 800 € (Risiko 48 €) |
| 6,0 % | 800 € | **48 €** | 800 € (Risiko 48 €) |
| 22 % | 800 € | **176 €** | 545 € (Risiko 48 €) |

> **Das Risiko je Trade schwankt heute um den Faktor 9.** Der Umschlagpunkt
> liegt bei `stop_rel = 48/800 = 6 %`. Bei engem Stop wird **42 % des
> Risikobudgets** eingesetzt, bei weitem **367 %**.

### 2.3 Die Regler — 245 Schlüssel, gemessen

| | | |
|---|---:|---|
| von der **Rollen-Kette** gelesen | **133** | 54 % |
| nur **außerhalb** gelesen (alte Kette, Screening) | **85** | 35 % |
| ⚠️ **nirgends im Code gefunden** | **27** | 11 % |

**Die 27 toten Schlüssel** sind überwiegend Absichtserklärungen ohne Code:
`risiko.stop_loss_pflicht`, `indikatoren.confluence_pflicht`,
`antizyklisch.*` (6 Stück), `hebel_screening.gewichte.*` (8 Stück),
`regime.bestimmung`.

---

## 3. Die LLM-Ebene

| Rolle | Modul | Zustand |
|---|---|---|
| **A — Lagebild** | `rolle_analyst.py` | ✔ läuft, L1–L6, zwölf Aussagen |
| **BC — Trader** | `rolle_trader.py` | ✔ läuft, ein Vokabular für beide Instrumente (S6a) |
| **G — Gegenprüfung** | `gegenpruefer_rollen.py` | ✔ läuft (Z.ai) |

**Der Vertrag** (`empfehlung_vertrag.py`) prüft: Aktion aus fünf zulässigen,
**Richtung Pflicht bei KAUFEN/NACHKAUFEN** (seit 23.08. instrumentunabhängig),
Betrag aus der Tranchenliste, Widerlegungspreis auf Widerspruchsfreiheit.

⚠️ **Was das Modell NICHT liefern darf:** Hebelfaktor, Positionsgröße,
Wahrscheinlichkeiten. Das ist gebaut und geprüft.

**Die Regeln für den Faktentext** sind R-T1…R-T11 (Regelwerksmanual). ⚠️ Die
oft zitierte Vorgabe *„keine Zahlen ins LLM"* meint **rohe** Zahlen — R-T5
verlangt relative Zahlen ausdrücklich (Kapitel 144).

---

## 4. Messung — was gemessen wird und was es sagt

### 4.1 Die Auflösung (Backward-Tracking)

| | |
|---|---|
| Zustände | `take_profit_erreicht`, `stop_loss_erreicht`, `einstieg_nie_erreicht`, `ueberholt_durch_neuere_analyse`, `abgelaufen_unentschieden`, `nicht_anwendbar`, `offen` |
| **E1** (18.08.) | die Auflösung verlangt den **Einstieg** — 21,1 % hatten ihre Zone nie erreicht |
| **E2** (22.08.) | am Erstellungstag zählt **nur der Schlusskurs** — 34,6 % aller Signale änderten ihr Ergebnis |
| **Trefferquote danach** | **27,8 %** gegen Basisrate **33,3 %** |
| ⚠️ Fallzahl | **18** aufgelöste Signale — trägt keine Aussage über Güte |

### 4.2 Die Schattenmessungen

| Schatten | Zeilen | was er sagt |
|---|---:|---|
| **`vorfilter_schatten` (V1/H)** | 51 | 49× „nicht_h", 2× unbestimmbar, 0× „h" — ⚠️ **ein Tag, und der Grund fehlte im Export** |
| `veto_schatten_performance` | 719 (Hebel, alte Kette) | Vetos nach Grund |
| `selbst_gewaehltes_halten` | 42 | HALTEN-Entscheidungen |
| `zai_richtung_performance_schatten` | 127 | Rolle G, alte Kette |
| `kapitel93.rangplatz` | 27 Felder | t = 3,2 bei Schwelle 3,11 — **knapp** |

> ⚠️ **KORREKTUR (Nutzereinwand, 23.08.).** Ich hatte daraus geschlossen, H
> würde „die Kette schließen". **Das war falsch, und zwar dreifach:**
>
> 1. **`h = True` ist erreichbar** — auf echten Markenstrukturen nachgeprüft
>    (frei ✔, gedeckt ✔). Mein Gegentest war falsch aufgebaut: er benutzte
>    `widerstand`/`unterstuetzung`, `bewerte()` liest `oben`/`unten`.
> 2. **H ist gemessen WIRKSAM:** +0,15 R je Trade über **523 Reihen /
>    19.891 Anker**. Bei Referenz 0,30 %: ohne Filter −0,031 R, **mit H
>    +0,114 R** (Kapitel 119–124).
> 3. **51 Zeilen aus EINEM Tag** — und ausgerechnet dem, an dem der Cooldown
>    fast alles blockiert hat. Gegen 523 Reihen ist das kein Gegenbeweis.
>
> **Der echte Mangel war der Export:** `stand()` meldete nur *wieviele*, nicht
> *warum*. Seit 23.08. meldet er `je_haelfte` (fehlte A oder B?), `je_grund`
> und `je_instrument`. **Eine Zahl ohne ihr Warum ist kein Befund.**

### 4.3 Was nicht gemessen wird

| | |
|---|---|
| ob die **Faktenblöcke** ein Urteil verbessern | nie geprüft |
| ob die **Reihenfolge** (R-T9) wirkt | offen (8c.3/M3) |
| ob das Modell die **Bedingung** im Finanzierungssatz befolgt | ab jetzt in `belege_gegen_fakten` nachsehbar |
| **Trefferquote nach Stopklasse** | ⚠️ **nie gemessen — und arithmetisch die aussichtsreichste Frage** (Teil 6) |

---

## 5. ⚠️ Der Fleckerlteppich, gemessen

### 5.1 Module, die nirgends laufen

**Von `main.py` aus nicht erreichbar (5):**

| Modul | Grund |
|---|---|
| `marktbreite.py` | am 12.08. ersatzlos gestrichen (L1–L6) — **toter Code** |
| `szenario_analyst.py` | ⚠️ **eine ganze Familie ohne Aufrufer** |
| `szenario_entscheidung.py` | dito |
| `szenario_fakten.py` | dito |
| `szenario_gegenpruefer.py` | dito |

> ⚠️ **KORREKTUR meiner eigenen Aussage in Kapitel 143.** Dort steht, der
> technische Konfliktdeckel habe keine Eingabe, weil `szenario_fakten` „die
> Zählung statt der Gesamttendenz" schreibe. **Das Modul läuft überhaupt
> nicht.** Die Folgerung (keine Eingabe) stimmt, die Begründung war falsch.

**Nur außerhalb der Rollen-Kette (8):** `datenfrische`, `provider_sperre`,
`portfolio_historie`, `themenfeld_erfolg`, `schwerpunkt_prioritaet`,
`kategorie_synthese`, `kategorie_vorschlaege`, `multi_asset_batch`.

### 5.2 Gebaut, verdrahtet, aber ohne Wirkung

| | Zustand |
|---|---|
| **`vorfilter.py` (V1/H)** | schreibt mit, **entscheidet nichts** — und würde alles blockieren |
| **`wahrscheinlichkeit.py`** | zeigt an, **entscheidet nichts** |
| **Strategien** `swing` / `akkumulation` | in `handelsauftrag` definiert — `rollen_job.py` fährt **durchgehend `einstieg`** |
| **fünf Konfliktdeckel** | am 23.08. **gestrichen** (Kapitel 137) — 3 von 4 hatten nie gegriffen |
| **`hebel_triggers`** | `hebel_screening_job` schreibt alle 15 min — die Rollen-Kette **liest die Tabelle nicht** |

### 5.3 Die Instrument-Verzweigungen

`pruefe_instrument_verzweigungen.py` (neu, 23.08.): **14 Stellen, 11 für
Krypto tot.** Neun harmlos, **zwei schwer** (`rechne`, `felder_aus_entscheidung`).

---

## 6. Wann Hebel, wann Spot — die Arithmetik entscheidet

```
hebel_noetig = verlustanteil / stop_rel          Kosten_R = 2 × Gebühr / stop_rel
```

**Der Stopabstand entscheidet beides zugleich — in entgegengesetzte Richtung:**

> ⚠️ **DIE GEBÜHR DES HANDELSPLATZES GEHÖRT NICHT IN DIE BEWERTUNG**
> (Nutzervorgabe 22.08.). Ein Trade wird **neutral** beurteilt — mit der
> **Referenz 0,30 %**. Der Bitpanda-Satz von 1,50 % gehört ausschließlich in
> die **Geldrechnung der Mail**, wo der Nutzer sieht, was ihn ein Trade
> tatsächlich kostet.
>
> **Warum die Trennung trägt:** *„Es gibt den besseren Trade. Ob er sich
> rechnet, entscheidet allein der Handelsplatz."* (Kapitel 119.3). Wer den
> Betriebssatz in die Bewertung mischt, verwirft gute Trades wegen einer
> Eigenschaft, die nichts mit ihnen zu tun hat — und macht den Handelsplatz
> unsichtbar, statt ihn zur Entscheidung zu machen.

**Alle Zahlen hier zur Referenz 0,30 %:**

| Stop | Hebel nötig | Kosten in R | Breakeven | Hürde über Basisrate |
|---:|---:|---:|---:|---:|
| 2,5 % | 2,40 | 24,0 % | 41,3 % | **+8,0 Punkte** |
| 6,0 % | 1,00 | 10,0 % | 36,7 % | +3,4 Punkte |
| 12,0 % | 0,50 | 5,0 % | 35,0 % | +1,7 Punkte |
| 25,0 % | 0,24 | 2,4 % | 34,1 % | **+0,8 Punkte** |

> **Der Hebel ist keine Wahl, sondern die Folge eines engen Stops. Und ein
> enger Stop kostet in R am meisten.**

**Damit trifft die Formulierung des Nutzers den Mechanismus genau:**

| | Stop | Hebel | Kostenhürde |
|---|---|---|---|
| **SPOT — „Bodenbildung oder Tod"** | weit | 1,0 | **+0,8 Punkte** |
| **HEBEL — „kurzfristige Chance"** | eng | > 1 | **+8,0 Punkte** |

⚠️ **Das ist eine Aussage über den TRADE, nicht über den Handelsplatz.** Was
ein enger Stop beim Betriebssatz kostet, gehört in die Mail — nicht in die
Frage, ob der Trade gut ist.

**Die daraus folgende, nie gestellte Messfrage:** ist die Trefferquote über
die Stopklassen **gleich**? Wenn ja, sind weite Stops arithmetisch überlegen,
**ohne dass irgendein Modell besser werden muss.**

---

## 7. Die offenen Entscheidungen — beim Nutzer

| | Frage | Folge |
|---|---|---|
| **E-1** | `rechne()` auf `hebel_handelbar` umstellen? | der Hebel entsteht wieder; Bruch in der Hebel-Reihe |
| **E-2** | Risiko je Trade **fest** (Betrag folgt) oder Betrag fest (Risiko schwankt)? | heute schwankt es um Faktor 9 |
| **E-3** | Einsatz bei **800 €** belassen? | vorläufig dokumentiert (Kapitel 144) |
| **E-4** | Strategien `swing`/`akkumulation` verdrahten? | die Naht für SPOT-lang gegen HEBEL-kurz |
| **E-5** | die fünf toten Module löschen oder anschließen? | `szenario_*`, `marktbreite` |
| **E-6** | die 27 toten config-Schlüssel entfernen? | sie lesen sich wie lebende Einstellungen |

---

## 8. Was ich als Reihenfolge vorschlage

| | | warum |
|---|---|---|
| **1** | **E-1** (Hebel entsteht wieder) | ohne ihn misst die Kette ein Instrument, das sie nicht schreibt |
| **2** | **Vorfilter blockweise** (V-1) statt Alles-oder-nichts-Hash | ersetzt einen Teil der Uhr durch eine Aussage; rein mechanisch |
| **3** | **welche Blöcke wirken** (V-3) — aus `anlass_beobachtung`, die seit 16.08. `geaenderte_bloecke` führt | aus vorhandenen Daten, kein Umbau |
| **4** | **Stopklassen-Messung** | die aussichtsreichste offene Frage — braucht Fälle |
| **5** | **E-2** (Risikofrage) | Geldfrage |

⚠️ **KORRIGIERTE EMPFEHLUNG (Nutzereinwand 23.08.).**

Hier stand: *„den Vorfilter H nicht scharf schalten, er hat null Treffer."*
**Das war falsch** — und es hätte die einzige Größe stillgelegt, die im
ganzen Projekt den Zufall messbar schlägt:

| über 523 Reihen / 19.891 Anker, Referenz 0,30 % | |
|---|---:|
| ohne Filter | −0,031 R |
| **mit H** | **+0,114 R** |
| Vorsprung | **+0,15 R je Trade** |

**H gehört damit auf die Liste — an welcher Stelle, ist die offene Frage.**
Der Schatten muss erst zeigen, wie oft H auf der *Watchlist* zutrifft; die
Messung lief auf 523 Reihen, die Watchlist hat 57 Symbole, und Kapitel 124
hält ausdrücklich fest, dass der Nachweis auf 29 Symbolen **nicht
bestätigbar** ist.

⚠️ **Was ich weiterhin NICHT vorschlage:** die Wahrscheinlichkeit an die
Auswahl zu hängen. Sie fasst mehrere Beiträge zusammen, von denen bisher nur
einer trägt — sie würde H verwässern, nicht verstärken.


---

## 9. Nachtrag — die drei Messungen an der Produktionsdatenbank (23.08.)

*Grundlage: `tradinginfotool_2026-08-22_2209.db.gz` (265 MB entpackt), letzte
Signalzeile 22.08. 19:10. ⚠️ **Vor** den Nachöffnungen von E2 und S6c — die
liefen erst beim Neustart um 22:55.*

### 9.1 ⚠️ Welche Fakten das Modell wirklich bekam — und was gespeichert wurde

**Nicht aus dem Code gelesen, sondern aus `facts_json` der echten Signale.**

| Aktion | Zeilen | mittlere Länge `facts_json` | Merkmalsfamilien |
|---|---:|---:|---:|
| ERÖFFNEN | 881 | **2.187 Zeichen** | 849 |
| KAUFEN | 83 | 1.511 | 80 |
| NACHKAUFEN | 131 | 1.423 | 115 |
| **HALTEN** | 475 | **17 Zeichen** | 460 |
| **REDUZIEREN** | 75 | **17 Zeichen** | **10** |
| **VERKAUFEN** | 11 | **18 Zeichen** | **2** |

> ⚠️ **Die gesamte Verkaufsseite wird mit einem Stummel gespeichert:**
> `facts_json = {"asset": "IO"}`.

**An der Quelle bestätigt — es sind zwei Schreibpfade, und beide verdrahten
den Stummel fest:**

| Stelle | was sie übergibt |
|---|---|
| `_ein_asset` (Hauptpfad, Einstieg) | `fakten=bc_ein` — der **echte** Faktensatz |
| `_schreibe_nein` (die Nein-Zeile) | `fakten={"asset": symbol}` |
| `_sende_ausstieg` (**die Verkaufsseite**) | `fakten={"asset": symbol}`, dazu `familien=None` |

⚠️ **Die naheliegende Erklärung ist widerlegt.** „Kein Bestand" erklärt es
nicht: **72 von 75 REDUZIEREN haben Bestand**, und alle 75 sind Stummel.
Staking auch nicht — 1 von 34 Beständen ist voll gestakt.

> **Das erklärt O-29.** Der Befund lautete: *„die Verkaufsseite ist durch
> nichts erklärt — kein gemessenes Merkmal trennt Verkaufen von Halten (alle
> p > 0,47)."* ⚠️ **Es gab keine Merkmale zu messen.** Bei REDUZIEREN sind
> 10 von 75 gefüllt, bei VERKAUFEN 2 von 11.

**Was das Modell beim Einstieg sah** (1.067 Faktensätze, vor S6b):

| | |
|---|---:|
| Sätze je Faktensatz | 8–12, Schwerpunkt bei **11** |
| Marktstruktur / Umsatz / Marken | je **100 %** |
| Bestand | 90 % |
| Finanzierung | 85 % |
| Liquidation / Hebel | 81 % |

⚠️ Die letzten beiden sind die **Hebel-Lauf**-Signale. Seit S6b und bis zur
Reparatur von heute waren sie bei **0 %** (Kapitel 143).

### 9.2 Rolle G — ⚠️ es sind zwei Prüfer, nicht einer

**Korrektur meiner eigenen Angabe in Abschnitt 3.** Dort stand
*„G — Gegenprüfung — `gegenpruefer_rollen.py` — läuft (Z.ai)"*. **Das
verwechselt zwei Dinge**, und der Modulkopf sagt ausdrücklich, dass genau
diese Verwechslung schon einmal passiert ist:

| | Modul | was es prüft | Kosten |
|---|---|---|---|
| **Z1** | `gegenpruefer_rollen.py` | **Treue zur Eingabe**: Zahlendeckung, Richtungstreue, Zuspitzung, Leerlauf. Fragt **nicht**, ob das Urteil klug ist | **deterministisch, kostenlos** |
| **Z.ai** | `zweite_meinung.py` | **ein zweites Modell** — fragt genau das | ein Aufruf je Signal |

**Beide laufen.** Z.ai erreicht 668 von 881 ERÖFFNEN-Zeilen (76 %).
⚠️ **Bei HALTEN, REDUZIEREN und VERKAUFEN: 0 von 561.**

**Und was ein Verstoß auslöst, ist entschieden:** *zählen, nicht verwerfen* —
dieselbe Begründung wie beim Gate. Ein Wächter, der selbst verwirft, macht
seine eigene Wirkung unsichtbar.

### 9.3 Welcher Schatten ist überhaupt auswertbar?

| Schatten | Zeilen | davon aufgelöst |
|---|---:|---:|
| **`anlass_beobachtung`** (Fingerabdruck) | **45.479** | ⚠️ **13.898 hätten gesperrt** (31 %) |
| `gate_durchlaessigkeit` (Trichter) | 3.799 | – |
| Selbst-HALTEN | 506 | **8** |
| **`vorfilter_schatten` (H)** | 51 | **0** |
| Veto-Schatten (Rollen-Kette) | **0** | 0 |

**Die Grundgesamtheit jeder Auswertung** (Rollen-Kette, Stand vor E2):

| | |
|---|---:|
| `nicht_anwendbar` | 1.428 |
| `einstieg_nie_erreicht` | 145 |
| **`take_profit_erreicht`** | **42** |
| **`stop_loss_erreicht`** | **24** |
| `offen` | 17 |

> ⚠️ **66 aufgelöste Signale tragen alles.** Und 1.428 stehen auf
> `nicht_anwendbar` — der weitaus größte Teil davon HALTEN, die per
> Definition keine Zonen haben.

**Was daraus folgt, vorsichtig formuliert:**

1. **Der Anlass-Schatten ist der einzige mit Masse** — 45.479 Beobachtungen,
   und er sagt, dass **31 %** der Läufe redundant waren. Das ist die
   belastbarste Zahl der ganzen Kette.
2. **Der Vorfilter-Schatten ist noch nicht auswertbar** — 0 aufgelöste
   Signale. Er sagt heute nur, *wie oft* H zutrifft, nicht *ob es hilft*.
3. **Der Veto-Schatten der Rollen-Kette existiert nicht** (0 Zeilen). Die
   719 Zeilen im Export stammen aus der **alten** Kette.

### 9.4 ⚠️ Und der Vorbehalt, den der Nutzer benannt hat

*„Durch unseren Umbau kann es sehr leicht sein, dass deine Messungen bzw.
Vorhersagen durch die Fehler in der Umsetzung auseinanderlaufen."*

**Das ist in dieser Messung dreimal eingetreten:**

| | |
|---|---|
| Die Hebel-Fakten (81 %) | gelten nur **vor** S6b — danach 0 % |
| Die 66 aufgelösten Signale | Stand **vor** E1/E2 — nach der Nachöffnung sind es andere |
| Meine „drei Tabellen nie angefasst" | **Fehlalarm**, verworfen |

**Jede Zahl hier trägt deshalb ihren Zeitraum.** Wo sie ihn nicht trägt, ist
sie nicht belastbar.
