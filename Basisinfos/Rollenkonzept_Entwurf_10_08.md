# Rollenkonzept — Ein- und Ausgang je Rolle (ENTWURF, 2026-08-10)

> ## ⚠️ STANDVERMERK 16.08.2026 — dieses Dokument ist ÜBERHOLT
>
> **Der Text unten bleibt vollständig stehen.** Seine Begründungen sind der
> wertvollere Teil, und mehrere davon gelten unverändert — allen voran die
> Grundregel *„kein Block erscheint bei zwei Rollen"*, die inzwischen als
> **Konstruktionsbedingung** im Regelwerksmanual steht (R-R2).
>
> **Er beschreibt aber nicht mehr, WER urteilt.** Der Umbauplan sagt in seiner
> Einleitung, er löse dieses Dokument *„nicht ab, sondern setze darauf auf"* —
> das galt am 12.08. und gilt für die Rollenzuordnung **nicht mehr.**
>
> **VERBINDLICH IST SEIT 17.08.: `Regelwerksmanual.md`, Abschnitt R-R1 bis R-R5.**
>
> | unten steht | gilt heute | seit |
> |---|---|---|
> | Rolle A gibt `max_tranche_eur` aus und deckelt den Entscheider | **abgeschafft** — Rolle A nennt keinen Betrag; er folgt aus der Zahl unabhängiger Faktoren | 10.08. |
> | **Marktbreite** fehlt und muss gebaut werden (Bauliste Nr. 1) | **ersatzlos gestrichen** — Subjekt falsch, Bezugskorb wandert, Richtung gemessen **invers** | 12.08. |
> | Rolle B bekommt `antizyklisch.*` — Funding, OI-Squeeze, Long/Short | **falsch und heute schädlich.** Genau diese Fakten sind seit dem 16.08. **exklusiv Rolle G**. In Rolle BC wären sie die Verletzung der Konstruktionsbedingung — zwei Prüfer mit derselben Informationsgrenze bilden ein Martingal | 16.08. |
> | „Rolle B" als eigene Rolle neben „Rolle BC" | es gibt **A** und **BC**; B und C liegen seit dem 10.08. in einem Aufruf | 10.08. |
> | LLM2 kommt nicht vor | es gibt **Rolle G — Gegenprüfer**, mit eigener Informationsgrundlage und eigener Mindestgrundlage (R-R3) | 16./17.08. |
> | Ausgabe `neigung`, `lage_text` | heute `lage`, `klassen`, `belege` | 12.08. |
>
> **Wer aus diesem Dokument baut, ohne den Standvermerk zu lesen, baut den
> Homogeneous-Debate-Fehler nach** — es ist genau die Zuordnung, die am 16.08.
> rückgängig gemacht wurde.
>
> Aktueller Stand: `Regelwerksmanual.md` R-R1…R-R5 (Regeln) ·
> `Umbauplan_Gesamtsystem_12_08.md` Kapitel 41–42 (Basis-Sets und
> Aufnahmekriterium) · `Fakten_Entscheidungsmappe.md` (welcher Fakt zu wem).

---


**Status: Entwurf zur Abstimmung.** Nichts davon ist gebaut. Wird erst nach
Freigabe umgesetzt und dann in `Fakten_Entscheidungsmappe.md` überführt.

---

## 1. Der Befund, aus dem alles folgt

Wir haben **nicht zu wenig Fakten, sondern zu viele in einem Aufruf.**

```
Spot-System-Prompt          34.611 Zeichen, 37 Regeln
Faktensatz                  ~20 Blöcke aus 156 katalogisierten Knoten
Praxis-Empfehlung           3–4 unabhängige Faktoren; ab 5 „Analyse-Lähmung"
Ergebnis in der Datenbank   115 von 118 Signalen HALTEN
```

Ein Aufruf macht heute alles gleichzeitig: Marktlage beurteilen, Kandidat
bewerten, Zonen setzen, Risiko prüfen, Menge festlegen, begründen. Die Literatur
trennt genau das, und die Messung dazu ist eindeutig: eine einzelne Abfrage mit
mehreren Rollen verliert Leistung durch Kontextkonflikte beim Rollenwechsel.

---

## 2. Die Bias-Effekte, gegen die gebaut wird

> **VORSICHT — Nutzerhinweis 10.08.: „diese Befunde beruhen zum Teil auf dem
> ALTEN System."** Das ist richtig und ändert ihren Status. Ein Effekt, der in
> einem Prompt mit 37 Regeln und 156 Fakten gemessen wurde, ist kein Naturgesetz
> für einen Aufbau mit 4–6 Blöcken je Rolle. Die Spalte **Übertragbarkeit**
> trennt deshalb:
>
> - **generisch** — Literatur oder Modelleigenschaft, gilt unabhängig von unserem
>   Aufbau. Danach darf gebaut werden.
> - **systemabhängig** — an *unserem alten* Faktensatz gemessen. Gilt als
>   **Hypothese**, nicht als Befund. Konsequenz: der Block kommt zunächst nicht
>   in den Prompt, bleibt aber **einzeln zuschaltbar**, damit die Frage im neuen
>   Aufbau neu beantwortet werden kann.
>
> Nichts wird auf Basis einer systemabhängigen Messung endgültig verworfen.

| # | Effekt | Beleg | Übertragbarkeit | Gegenmittel |
|---|---|---|---|---|
| B1 | **Lost-in-the-Middle** | live gemessen 04.08.: `trigger` ans Ende → 3,2 pp, **5,3× Rauschboden** | **generisch** — U-förmige Aufmerksamkeit ist Literaturstand; die Stärke bei uns ist systemabhängig | Position Swapping je Rolle |
| B2 | **Werturteile im Faktensatz** | `einordnung`: 4,60 Konfidenzpunkte, **16 pp LONG-Anteil**, p 0,031 | **systemabhängig in der Höhe, generisch im Mechanismus** — ein Urteil im Faktensatz ist eine Anweisung, kein Datum | Wächter blockiert den Start |
| B3 | **Abstention durch Unsicherheitssignale** | Mehrdeutigkeits-Label drückte ERÖFFNEN **93 % → 3 %** | **systemabhängig** — extreme Größe, im alten Kontext gemessen. Mechanismus (Unknown-Option → Abstention) ist Literatur | keine „unklar"-Kategorien |
| B4 | **Überladung** → Lähmung | 156 Knoten gegen 3–4 empfohlene Faktoren | **generisch** — Praxisliteratur, unabhängig von uns | 4–6 Blöcke je Rolle |
| B5 | **Verbalisierte Konfidenz nicht kalibriert** | 77,5 % vorhergesagt → 33,3 % tatsächlich | **generisch** — mehrfach extern belegt (systematische Überkonfidenz) | keine Rolle nennt eine Konfidenz |
| B6 | **Richtungsinstabilität** bei identischer Eingabe | nemotron dreht in ~12 % der Fälle | **generisch** — Sampling-Eigenschaft; am NEUEN Szenario-Prompt gemessen | Selbstkonsistenz: 3 Abfragen |
| B7 | **Echo-Effekt** — Prüfer wiederholt die Vorlage | Konstruktionsgrund der alten Gegenprüfung, **nie gemessen** | **unbelegt** — Annahme, keine Messung | Prüfer liefert keine eigene Richtung |
| B8 | **Zahlen-Tokenisierung** | GPT-3 zerlegt 42235630 in [422, 35, 630]; GPT-4o auf 15 % | **generisch** — Modelleigenschaft, extern belegt | keine Rolle rechnet |
| B9 | **Negative Rahmung** → Risikoaversion | Literatur; deckt sich mit `systemguete`-Befund | **generisch im Mechanismus**, systemabhängig in der Höhe | Gegengründe in ein **eigenes** Feld |
| B10 | **Konstante Felder** täuschen Information vor | vier tote Felder an einem Tag; `regime` auf 1.022 Fällen „baer" | **generisch** — ein konstantes Feld kann per Definition nicht unterscheiden | Wächter blockiert den Start |

---

## 3. Zuordnung der vorhandenen Blöcke auf die Rollen

**Grundregel: kein Block erscheint bei zwei Rollen.** Sonst entsteht ein Echo
statt einer zweiten Meinung.

### Rolle A — Analyst (Marktlage)

Läuft **einmal je Durchgang**, nicht je Asset. Sieht **kein** einzelnes Asset.

| Block | woher | warum hier |
|---|---|---|
| `regime.*` (Fear&Greed, BTC-zu-EMA50, Matrix, Liquidität, Zyklus, VIX) | vorhanden | die Marktlage selbst |
| `regime_profil.min_konfidenz_prozent`, `small_cap_budget_prozent` | vorhanden | wie viel Risiko das Regelwerk erlaubt |
| DXY-Trend | vorhanden seit 28.07. | Makro-Cross-Check |
| `markt_kontext.*` (FOMC, CPI, Exchange-Flow, Stablecoin-Supply) | vorhanden | Termine und Liquidität |
| **Marktbreite** | **fehlt — muss gebaut werden** | „12 von 40 Coins über der 200-Tage-Linie" trennt breite von schmaler Bewegung |

**Ausgabe:**
```
lage_text        2–3 Sätze, was den Markt gerade kennzeichnet
neigung          guenstig_fuer_neueinstiege | neutral | unguenstig
max_tranche_eur  100 | 300 | 500      ← deckelt, was der Entscheider darf
begruendung      welche 2–3 Fakten die Neigung tragen
```

### Rolle B — Trader (Aufbau und Vergleich)

Je Asset. Sieht die Marktlage **als Ergebnis**, nicht deren Rohdaten.

| Block | woher | warum hier |
|---|---|---|
| `technische_analyse.*` (Struktur, ATR, Support/Resistance, Fibonacci, Confluence) | vorhanden | der Aufbau |
| **Volumen** | **seit 10.08. verfügbar, nie geliefert** | Umsatzbestätigung — laut Praxis das, was echte Aktivität von Rauschen trennt |
| `btc_relativwert.*` | vorhanden | relative Stärke |
| `liquiditaetszonen.*` | vorhanden | wo Liquidität sitzt |
| `antizyklisch.*` (Funding, OI-Squeeze, Long/Short) | vorhanden | Positionierung |
| **Rang unter Kandidaten** | **fehlt — muss gebaut werden** | der Vergleich ist der Zuschnitt mit Evidenz |
| Ergebnis von Rolle A | — | Kontext, nicht Rohdaten |

**Ausgabe:**
```
belege                 2–8 Stück: {fakt, richtung, gewicht}
unabhaengige_faktoren  Zahl — zählt NICHT dieselbe Sache dreimal
einstieg_eur           aus ATR und Referenzpunkten (Regeln 4/16, existieren)
stop_eur               dito
rang                   Platz unter den vergleichbaren Kandidaten
umgeworfen_durch       eine überprüfbare Beobachtung
```

### Rolle BC — Trader und Entscheider in EINEM Aufruf

**Warum zusammengelegt (Nutzerentscheidung 10.08.: 5-faches Kontingent ist nicht
tragbar).** Die Recherche nennt drei Einwände gegen mehrere Perspektiven in einem
Aufruf. Geprüft, welche hier greifen:

| Einwand | trifft zu? |
|---|---|
| Schema-Konfusion bei mehreren JSON-Objekten | **nein** — wir erzeugen genau eines |
| Anchoring — das Zweite haftet am Ersten | **nein, gewollt** — die Entscheidung SOLL auf den Belegen aufbauen |
| Selbstvalidierung des eigenen Textes | **nein** — es wird nichts kritisiert, es wird gefolgert |
| **Hedging — abwägende Beidseitigkeit** | **JA, der ernste Einwand** |

Die Befunde betreffen Rollen, die einander **widersprechen** sollen. B und C
widersprechen nicht, sie sind zwei Schritte derselben Aufgabe.

**Gegen das Hedging-Risiko wirken zwei bereits gebaute Dinge:** der Vertrag trennt
`begruendung` von `was_dagegen` (der Gegengrund hat einen eigenen Platz), und der
Validator lehnt Relativierer ab — er hat den echten KAS-Text abgewiesen
(*"die Begründung zieht sich selbst zurück (['aber weiterhin'])"*).

Damit ist Hedging kein Risiko, sondern ein **messbarer Zustand**: häufen sich
Validator-Ablehnungen wegen Relativierern, ist die Zusammenlegung widerlegt und C
wird abgespalten.

**EIN GEGENPRÜFER DARF NIEMALS IN DENSELBEN AUFRUF.** Dort greift die
Selbstvalidierung voll. Falls er gebaut wird, zwingend als eigener Aufruf.

| Block | woher | warum hier |
|---|---|---|
| **`haltung.*`** (Menge, Einstand EUR, G/V %) | vorhanden | **im KAS-Fall der entscheidende, ungenutzte Block — steht an ERSTER Position gegen B1** |
| `technische_analyse.*` (Struktur, ATR, Support/Resistance, Confluence) | vorhanden | der Aufbau |
| **Volumen** | seit 10.08. verfügbar, nie geliefert | Umsatzbestätigung |
| `btc_relativwert.*` | vorhanden | relative Stärke |
| `liquiditaetszonen.*`, `antizyklisch.*` | vorhanden | Liquidität und Positionierung |
| `vorherige_empfehlung`, `risiko_check.*`, `kosten.*` | vorhanden | Sperren, Kosten, Wiederholungsschutz |
| **Rang unter Kandidaten** | fehlt — muss gebaut werden | der Vergleich ist der Zuschnitt mit Evidenz |
| Ergebnis von Rolle A | — | Kontext, nicht Rohdaten |

**Ausgabe = der Vertrag** aus `agent/empfehlung_vertrag.py`, plus die Belege:
```
belege                 2–8 Stück: {fakt, richtung, gewicht}
unabhaengige_faktoren  zählt NICHT dieselbe Sache dreimal
aktion · tranche_eur · einstieg_eur · stop_eur
begruendung · was_dagegen · umgeworfen_durch
```

## 4. Was zunächst NICHT übergeben wird — jeder Block einzeln zuschaltbar

> **Kein Block wird endgültig verworfen.** Die Begründungen unten stammen
> überwiegend aus Messungen am ALTEN Aufbau (37 Regeln, 156 Fakten). Ob ein Fakt
> dort Vorsicht erzeugte, sagt wenig darüber, wie er neben fünf anderen wirkt.
> Deshalb gilt: Startkonfiguration ohne diese Blöcke, jeder **einzeln
> zuschaltbar**, und die Frage wird im neuen Aufbau neu gemessen — gepaart, ein
> Block je Lauf. Das ist dieselbe Methodik wie beim `einordnung`-Nachweis.
>
> Die Spalte **Status** trennt: *belegt* heißt im neuen Aufbau nachprüfbar
> begründet; *Hypothese* heißt aus dem alten System übernommen.

| Block | Grund | Status |
|---|---|---|
| `historische_erfolgsquote.*`, `systemguete` | Trefferquote −5,48 Konfidenzpunkte, CI [−9,41, −2,17] | **Hypothese** — am alten Aufbau gemessen |
| `signal_stabilitaet.*` | Selbstauskunft, keine Marktaussage | **Hypothese** — nie einzeln gemessen |
| `konfidenz_kalibrierung` | Selbstauskunft über eigene Fehlerquote | **Hypothese** — nie gemessen |
| `disclaimers.*` | steht an **Position 17 von 17**, der stärksten Stelle (B1) | **belegt** — Positionseffekt ist generisch; der Platz ist unstrittig falsch |
| `regime.boden_zielzone_btc/eth` | keine positive Regel, nur Halluzinations-Check | **belegt** — hat nie eine Entscheidung getragen |
| `strategien_aktiv[]`, `regime_profil.gewicht_*` | im Regler-Audit als wirkungslos festgestellt | **belegt** — 36 von 202 Schlüsseln ohne Wirkung |
| `.kursverlauf[]` (90 Punkte) | 90 rohe Zahlen, siehe B8 | **belegt** — Tokenisierung ist Modelleigenschaft |

**Diese Blöcke werden nicht gelöscht.** Sie bleiben in Datenbank und Anzeige und
sind je einzeln wieder zuschaltbar. Sie gehen nur in der Startkonfiguration nicht
in den Prompt.

---

## 5. Die Kette von Anfang bis Ende

```
Budget-Allocator wählt Assets                          (unverändert)
        ↓
ROLLE A — 1-2× am Tag, NICHT je Asset
  rein:  Marktlage-Blöcke + Marktbreite (neu) - kein einzelnes Asset
  raus:  neigung, max_tranche_eur, Begründung
        ↓  (Ergebnis, keine Rohdaten)
ROLLE BC — 1× je Asset
  rein:  Bestand ZUERST, dann Aufbau, Volumen, Rang, A-Ergebnis
  raus:  Belege + DER VERTRAG
        ↓
Validator lehnt ab, was den Vertrag nicht erfüllt      (gebaut, 10.08.)
        ↓
E-Mail je Asset + GUI                                  (unverändert)
```

**Kontingent, an echten Zahlen** (Spitzentag 21.07.: 42 Signale, 45 Symbole):

| Aufbau | Aufrufe je Tag | gegen heute |
|---|---|---|
| heute | ~40 | — |
| **Variante 2 (A + BC)** | **~42** | **+5 %** |
| Variante 1 (A + B + C) | ~82 | doppelt |
| ursprünglicher Entwurf (A + 3×B + C) | ~162 | **4-fach — verworfen** |

**Selbstkonsistenz gestrichen.** Sie stand im Referenzstandard, aber der Beleg
dafür (nemotron dreht in ~12 % der Fälle) stammt von der RICHTUNGSWAHL - einer
Aufgabe, die Rolle BC gar nicht mehr hat. Ein Befund von einer Aufgabe auf eine
andere zu übertragen ist derselbe Fehler wie bei den Alt-System-Befunden.
Verdreifacht die teuerste Stufe für eine Vermutung. Wird gemessen, wenn Rolle BC
erkennbar schwankt - an wenigen Fällen, nicht im Dauerbetrieb.

## 6. Was noch gebaut werden muss

| # | Fehlt | Aufwand |
|---|---|---|
| 1 | **Marktbreite** — Anteil der Assets über 50-/200-Tage-Linie | gering, Daten vorhanden |
| 2 | **Volumen-Aussagen** in die Produktionspipeline | gebaut (`lagebeschreibung.py`), muss angeschlossen werden |
| 3 | **Rang unter Kandidaten** | mittel — Vergleich über alle Kandidaten eines Durchgangs |
| 4 | **Zwei Prompts** statt einem (A und BC) | mittel |
| 5 | **Position Swapping** für A und BC | gering, Muster existiert bei LLM2 |
| 6 | ~~Selbstkonsistenz~~ | **gestrichen** — nicht belegt, vervierfacht das Kontingent |

---

## 7. Verifikation — vor dem ersten Modellaufruf

1. **Wächter** `enthaelt_werturteile()` und `finde_konstanten()` über alle
   Rollen-Eingaben, alle sechs Assetklassen. Grün oder Abbruch.
2. **Kausalitätsprobe** — Eingabe aus voller Reihe gegen abgeschnittene, bitgleich.
3. **Überschneidungsprobe** — kein Block bei zwei Rollen. Automatisch prüfbar.
4. **Der KAS-Prüfstein** — der Fall vom 15.07. muss durch das neue Konzept zu
   „nicht nachkaufen" führen. Rolle C sieht −10,3 % im Bestand, Rolle A deckelt
   bei bärischem Regime. Kommt trotzdem NACHKAUFEN heraus, ist das Konzept
   widerlegt.
5. **Ein echter Durchlauf** — ein Asset, alle Rollen, Antworten vollständig
   ausgedruckt, zum Lesen. Kosten: 2 Aufrufe.

Erst danach wird über eine Messung gesprochen.
