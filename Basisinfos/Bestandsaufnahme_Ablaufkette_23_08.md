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
| **Was der Vorfilter H leistet** | in 51 Beobachtungen **null** H-Urteile — als Filter würde er alles blockieren |
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
| **`vorfilter_schatten` (V1/H)** | 51 | ⚠️ **49× „nicht_h", 2× unbestimmbar, 0× „h"** |
| `veto_schatten_performance` | 719 (Hebel, alte Kette) | Vetos nach Grund |
| `selbst_gewaehltes_halten` | 42 | HALTEN-Entscheidungen |
| `zai_richtung_performance_schatten` | 127 | Rolle G, alte Kette |
| `kapitel93.rangplatz` | 27 Felder | t = 3,2 bei Schwelle 3,11 — **knapp** |

> ⚠️ **Der Vorfilter H hat in einem vollen Tag kein einziges Mal gegriffen.**
> Als Filter eingeschaltet würde er **alles** blockieren. Das ist kein Fehler
> im Code — H ist schlicht fast nie erfüllt.

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

| Stop | Hebel nötig | Kosten in R (0,30 %) | Breakeven | Hürde über Basisrate |
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

⚠️ **Bei Bitpanda-Gebühr (1,50 %) ist der enge Stop nicht handelbar:**
Kosten_R = 120 %.

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

⚠️ **Was ich NICHT vorschlage:** die Wahrscheinlichkeit jetzt an die Auswahl
hängen, oder den Vorfilter H scharf schalten. **H hat in 51 Beobachtungen
null Treffer** — er würde die Kette schließen, nicht schärfen.
