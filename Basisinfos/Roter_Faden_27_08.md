# Der rote Faden — wo wir stehen und was zusammenhängt

**Angelegt 27.08.2026.** Nutzerauftrag: *„Nach der Teilumsetzung bringe die
Punkte und Pläne in Zusammenhang, damit wir einen roten Faden haben."*

---

## 0. Das Ziel in einem Satz

> **Ein System, das bei hohem Potential ein begründetes Handelssignal erzeugt —
> statt 190 Signale am Tag nach der Uhr.**

**Die drei Vorgaben, die das schärfen** (Nutzer, 25.–27.08.):

| | |
|---|---|
| ⚠️ **Der Takt darf nie Signalgeber sein** | er begrenzt, er erzeugt nicht |
| **Ein guter Trade ist Potential, nicht Gebührendeckung** | zwei Ebenen, die sich nie überschneiden |
| **Wir bewerten nicht Assets, sondern Zeitpunkte** | auch ein Shitcoin hat Potential |

---

## 1. Wo der Weg herkommt — der Ausgangszustand

| | gemessen |
|---|---|
| Signale je Tag | **190** über 44 Symbole = **4,3 je Symbol** |
| davon ERÖFFNEN | **0** (Stand 24.08.) |
| Trichterverluste an Bremsen ohne Qualitätsaussage | **79 %** (`anlass` 1.252 · `wiederholung` 445) |
| offene Signale je Position | bis zu **21** (BIO), 17 (BTC) |
| Durchsatz gegen Cooldown-Obergrenze | 63 % |

**Die Diagnose:** Der Scheduler ist der Auslöser, der Cooldown die Bremse.
Beide sagen nichts über Qualität.

---

## 2. Was heute gebaut wurde — und wie es zusammenhängt

```
   ZIEL: Signal bei hohem Potential

   ┌─────────────────────────────────────────────────────────┐
   │  1  POSITION statt Signal        agent/positionsfuehrung │  ✔ gebaut
   │     44 statt 266 Führungen, Break-Even sichtbar          │  ✘ kein Aufrufer
   ├─────────────────────────────────────────────────────────┤
   │  2  STRATEGIE je Position        agent/handelsauftrag    │  ✔ existiert
   │     einstieg / swing / akkumulation + Paar-Matrix        │  ⚠️ nie gesetzt
   ├─────────────────────────────────────────────────────────┤
   │  3  AUSLÖSER statt Takt          Ausloeser_und_Begr…     │  ⚠️ 11/20 Zellen
   │     K1 Lage · K2 Vorfilter · V1 These · V3 Greed · V4    │  ✘ nicht gebaut
   ├─────────────────────────────────────────────────────────┤
   │  4  POTENTIAL als Auswahl        agent/potential         │  ✔ gebaut
   │     quote × CRV − (1 − quote), gebührenfrei              │  ⚠️ 1 Beitrag
   └─────────────────────────────────────────────────────────┘
```

**Die vier greifen ineinander:** Ohne (1) erzeugt jeder Auslöser 21 Meldungen
statt einer. Ohne (2) greifen weder Paar-Matrix noch die GUI-Schalter des
Nutzers. Ohne (3) bleibt die Uhr der Auslöser. Ohne (4) kann das System zwei
Handlungen nicht gegeneinander abwägen.

---

## 3. Was fertig ist — belastbar

| | Baustein | Beleg |
|---|---|---|
| ✔ | **Positionsführung** | 44 statt 266, Break-Even, −6.544 € Gesamtstand; Staking abgezogen |
| ✔ | **Potentialmaß** | 6 Tests bestanden, Zwei-Ebenen-Trennung nachgewiesen (+0,135 R gegen −0,365 R) |
| ✔ | **Kern-Auswahl** | BTC/ETH/SOL — der GUI-Schalter nennt sie seit Wochen |
| ✔ | **Takt fachlich egal** | 2–14 Tage unter 0,2 % Unterschied; nur Mindestgebühr zählt |
| ✔ | **V1-Datenlage** | 262 von 266 Signalen tragen den Widerlegungspreis, Spanne je Position **Faktor 1,00–1,02** |
| ✔ | **Ein Ausschluss** | weit über dem 200-Schnitt kaufen: −11,2 Punkte, 3/3 Jahre |
| ✔ | **Modulkarte** | `zeige_modulkarte.py` — 160 Module, gegen dreifaches Neuerfinden |
| ✔ | **Methodik 2.80** | Prüfliste zwischen Ergebnis und Deutung |

---

## 4. ⚠️ Was heute gestorben ist — und was das bedeutet

| | Befund | Todesursache |
|---|---|---|
| 1 | Lage-Staffelung trägt | falsche Kontrolle — verliert **−8,3 %** gegen konstante Quote |
| 2 | Tief Gefallene fallen weiter | keine Basisrate |
| 3 | Umsatz trennt tot von lebendig | widerlegt |
| 4 | Buckel bei leicht unter dem Schnitt | Marktphase |

⚠️ **Damit gibt es für den Kern KEINE belegte positive Kaufregel.** Die
Kandidaten sind erschöpft: Fear ist ausgeschlossen (151 Tage am Stück),
„nie teurer als zuletzt" verstummt, die Lage-Staffelung ist gescheitert,
„Boden gehalten" wurde nie gebaut.

**Was bleibt, sind Ausschlüsse** — nicht kaufen, wenn teuer. Das passt zum
Gesamtbefund des Projekts und ist keine Niederlage, aber es heißt: **Der Kern
wird vorerst nach Zeittakt akkumuliert, nicht nach Auslöser.**

---

## 5. ⚠️ Drei Schiefstände, die heute aufgedeckt wurden

**Alle drei sind vom selben Typ: beim Umbau verlorene Funktionalität, die in
der Doku als fertig steht.**

| | was in der Doku steht | tatsächlich |
|---|---|---|
| **Spot-Verkaufs-Roadmap** | *„vollständig abgeschlossen"* (01.08.) | alle vier Schritte hängen an der alten Kette · `halte_kriterium`: **1 von 266** |
| **Strategien** | `handelsauftrag.py` seit 12.08. vollständig | `strategie` in **0 von 7.294** gesetzt |
| **Tranchen** | AZ-4 gebaut, GUI-Schalter da | Rollen-Kette kennt sie **nicht** |

**Gegenmittel gebaut:** `zeige_modulkarte.py` + Methodik 2.80 Punkt 6.

---

## 6. Die Reihenfolge — was worauf wartet

```
JETZT MÖGLICH, ohne Vorbedingung
  A  strategie setzen (Kern → akkumulation)      → schaltet GUI-Schalter scharf,
                                                    beendet Trailing auf Spot
  B  Positionsführung anschließen                 → 83 % weniger Prüfungen
  C  V1 als Ausstieg                              → Datenlage vollständig

WARTET AUF EINE ENTSCHEIDUNG DES NUTZERS
  D  Zielallokation je Stufe                      → ohne sie rechnet V4 nicht
  E  Hebel: Krücke (beides melden) oder warten?   → braucht D nicht
  F  Cooldown/Job-Takt                            → 190/Tag ist die Ausgangslage

WARTET AUF MESSUNG
  G  H über ein CRV-Raster                        → erst dann Spot gegen Hebel
  H  V3 (Greed-Teilverkauf) Wirkung               → Daten da, ungemessen
  I  Auswertung Vorfilter-Schatten                → ~19.09.2026
  J  Lebendigkeit / TVL                           → ab 18.09.2026
  K  Terminmarkt-Wirkung (OI, Funding)            → ab 22.10.2026 / 11.03.2027
```

⚠️ **A, B und C sind unabhängig voneinander und von allem anderen.** Sie
bringen das System in einen Zustand mit weniger und begründeten Meldungen,
ohne dass die Potentialfrage geklärt sein muss.

---

## 7. Der ehrlichste Satz zum Stand

**Das System kann nach diesem Tag besser sagen, was es NICHT weiß.** Es hat
eine Positionssicht, ein Potentialmaß mit ausgewiesenen Grenzen, eine
Auslöser-Matrix mit sichtbaren Lücken und eine Prüfliste, die vier falsche
Befunde an einem Tag gefunden hat.

⚠️ **Was es nicht hat, ist ein zweiter tragender Beitrag.** Das Potentialmaß
rechnet heute im Wesentlichen „trifft H zu?" — und H läuft bis 19.09. im
Schatten. **Jede weitere Verfeinerung der Auswahl scheitert daran, nicht an
der Mechanik.**

Verwandt: `Ausloeser_und_Begruendungen_27_08.md` ·
`Befund_Lage_27_08.md` · `Entscheidung_Kern_Staffelung_27_08.md` (widerrufen) ·
`Bestandsaufnahme_Positionsfuehrung_26_08.md` ·
`Test_und_Verifikationsmethodik.md` 2.80


---

# FORTSCHREIBUNG 31.08.2026 — Bestandsaufnahme aller Pläne mit Status

**Nutzerauftrag 31.08., wörtlich:** *„Du schaffst es nicht, nach einem halben
Tag Arbeit die neuen Planungspunkte mit den alten wieder zu einem Ganzen
zusammenzuführen — somit arbeiten wir immer nur an einem Bereich, und wenn
dieser fertig ist, wird nur die Hälfte umgesetzt und wichtige Punkte
vergessen. Also ZUERST mach eine Bestandsaufnahme der Pläne und deren Status
und dann, was davon konkret umgesetzt oder teilweise umgesetzt ist — z. B.
fehlt die Verdrahtung."*

⚠️ **Jede Zeile unten ist am CODE geprüft, nicht aus einem Dokument
übernommen.** Wo Doku und Code sich widersprechen, gilt der Code — und der
Widerspruch steht dabei.

## ⚠️ Ein Befund vorweg: die Verdrahtungsprüfung selbst war falsch

Die Prüfung in `pruefe_pakete.py` suchte Modulnamen **im Quelltext**. Sie
meldete `positionsfuehrung` als verdrahtet — der einzige Treffer war ein
**Docstring** in `handelsauftrag.py:74`. Eine Erwähnung ist kein Aufruf.
Seit 31.08. rechnet sie über echte `import`-Kanten (AST), mit einer
Gegenprobe auf die bekannte Lücke.

**Erreichbarkeit von `main.py` / `scheduler/` / `ui/` aus, über echte Importe:**

    ✘ positionsfuehrung      gebaut, kein Aufrufer  (unveraendert seit 27.08.)
    ✘ marktbreite            gebaut, kein Aufrufer  (Reparaturliste D2)
    ✔ alle 24 anderen geprueften Module

---

## 1. Die vier Bausteine des Roten Fadens — Stand heute

| # | Baustein | 27.08. | **31.08.** | was konkret fehlt |
|---|---|---|---|---|
| **1** | **Positionsführung** (`agent/positionsfuehrung.py`) — eine Position je Symbol statt je Signal | ✔ gebaut, ✘ kein Aufrufer | **unverändert** | **die Verdrahtung.** Kein `import` aus `scheduler/`, `ui/` oder `main.py`. Es gibt auch **keine Tabelle `positionen`** — das Modul rechnet nur zur Laufzeit aus `holdings` |
| **2** | **Strategie je Position** (`agent/handelsauftrag.py`) — `einstieg`/`swing`/`akkumulation` + Paar-Matrix | ✔ existiert, ⚠️ nie gesetzt | **teilweise** | `einstieg` wird gesetzt (**924** von 5.772 Signalen). `akkumulation` und `swing`: **weiterhin 0** |
| **3** | **Auslöser statt Takt** (`Ausloeser_und_Begruendungen_27_08.md`) | ⚠️ 11/20 Zellen, ✘ nicht gebaut | **unverändert** | nicht angefasst seit 27.08. |
| **4** | **Potential als Auswahl** (`agent/potential.py`) | ✔ gebaut, ⚠️ 1 Beitrag | ✔ **3 Beiträge, scharf** | gilt für **eine** Zelle: `krypto × spot × einstieg` |

---

## 2. Die Punkte A–K aus Abschnitt 6 — was ist daraus geworden

| | Punkt | 27.08. | **31.08.** |
|---|---|---|---|
| **A** | `strategie` setzen (Kern → `akkumulation`) | jetzt möglich | ⚠️ **halb** — `einstieg` gesetzt, `akkumulation` nie. Damit läuft **jeder Nachkauf als Einstieg** |
| **B** | Positionsführung anschließen | jetzt möglich | ✘ **offen, unverändert** |
| **C** | V1 (These/Widerlegungspreis) als Ausstieg | jetzt möglich | ⚠️ `vorfilter` ist im Ausstieg referenziert, als Ausstiegsregel nicht nachgewiesen |
| **D** | Zielallokation je Stufe | wartet auf Nutzer | ✘ **offen — Ihre Entscheidung** |
| **E** | Hebel: Krücke oder warten? | wartet auf Nutzer | ✘ **offen.** ⚠️ Verschärft: `INSTRUMENTE_JE_GRUPPE` gibt Krypto nur `spot` — **Hebel läuft in keiner Gruppe** |
| **F** | Cooldown / Job-Takt | wartet auf Nutzer | ✘ offen |
| **G** | H über ein CRV-Raster | wartete auf Messung | ⛔ **hinfällig** — H ist am 31.08. als Beitrag gefallen (R1) |
| **H** | V3 (Greed-Teilverkauf) Wirkung | Daten da, ungemessen | ✘ **weiterhin ungemessen** |
| **I** | Auswertung Vorfilter-Schatten (~19.09.) | wartete | ⛔ **hinfällig** — H gefallen |
| **J** | Lebendigkeit / TVL (ab 18.09.) | wartete | ⛔ **Termin hinfällig** — DefiLlama liefert 6–8 Jahre, 188 Reihen geladen. **Sofort messbar** |
| **K** | Terminmarkt (OI, Funding; ab 22.10. / 11.03.27) | wartete | ⛔ **Termin hinfällig** — Binance liefert 7,0 Jahre. Funding ist seit 31.08. tragender Beitrag |

⚠️ **Vier der sieben Wartepunkte waren gar keine.** G und I sind durch R1
erledigt, J und K standen auf einer falschen Annahme über den
Historie-Endpunkt.

---

## 3. Reparaturliste 23.08. — die offenen Zeilen

| | was | Stand 31.08. |
|---|---|---|
| A1–A5 | Hebel-Rechnung, `hebel`-Spalte, Topf, Cooldown, CRV-Faktor | ✔ repariert 23.08. |
| **A6** | Mail-Betreff und -Abschnitt hängen am Lauf | ⚠️ **offen** — im Code nicht mehr nachweisbar, aber auch nicht belegt repariert |
| B1–B3 | Verkaufsseite: Faktensatz, Merkmale, Zweitmeinung | ✔ repariert 23./24.08. |
| **C1** | Einsatz 800 € statt 1.000 € | ⚠️ **Entscheidung offen** |
| **C2** | Risiko je Trade schwankt um Faktor 9 | ⚠️ **Entscheidung offen — schwer** |
| **C3** | `crv_spreizung`: config gegen Code | ⚠️ **offen**, Eichung vermessen |
| **D1** | `swing`/`akkumulation` nie benutzt | ✘ **offen** — bestätigt, 0 Signale |
| **D2** | Module ohne Aufrufer | ⚠️ **teilweise** — `marktbreite` ✘, `szenario_*` existieren nicht mehr |
| **D3** | 27 config-Schlüssel liest niemand | ⚠️ **offen** — kein Auditwerkzeug im Stamm |
| E1–E5 | Cooldown, Lagebild, Richtungspflicht, REDUZIEREN, E2 | ✔ repariert 22./23.08. |

---

## 4. N-12 Positionsführung (26.08.) — die sieben Lücken

| | Lücke | betrifft | Stand 31.08. |
|---|---|---|---|
| **L1** | Keine Position mit These — Stop/Ziel/MFE/Einstand fehlen | alle | ✘ **offen** — Tabelle `positionen` existiert nicht |
| **L2** | Akkumulation nicht angeschlossen — Nachkauf = neues Signal | alle | ✘ **offen** — 0 von 5.772 |
| **L3** | Trailing phasenabhängig, greift trotzdem immer | Spot + Hebel | ✘ offen |
| **L4** | Keine Spot-Zeitskala — Handelshorizont 0–5 Tage | Spot, Core | ✘ offen, strukturell |
| **L5** | Einstand nur teilweise bekannt (`tracked_qty` < Bestand) | alle | ✘ offen — 9 Assets nur gestakt |
| **L6** | Rolle `taktisch`/`core` ohne erkennbare Wirkung | alle | ✘ ungeprüft |
| **L7** | Absicherung: 97,2 % Anlass-Sperrquote | Hedge | ✘ offen — faktisch aus |

---

## 5. Was am 30./31.08. dazugekommen ist

| | was | Stand |
|---|---|---|
| **2e** | Funding + Turnover als Beiträge registriert **und** verdrahtet | ✔ fertig |
| **R1** | H (Vorfilter „Weg frei") auf `null` gesetzt | ✔ fertig — H war Komposition, nicht Leistung |
| **R2** | Mailzeile zu den Kursmarken lesbar, ohne Rohzahlen | ✔ fertig |
| **P1/P2** | Schnittabstand zum eigenen 200-Tage-Schnitt als dritter Beitrag | ✔ fertig — Abdeckung **43/43**, der einzige aus der eigenen Kursreihe |
| **P3** | Rang über die **Messbasis** statt über den Markt | ✔ fertig |
| **G-6** | Stufe 11 (Entscheider) scharf: `NUR_ZAEHLEN = ()` | ✔ fertig — mit drei Zuständen (`vermessen`/`bewertbar`/`trägt`) |
| **B1** | „Kette hat keinen Betriebsaufrufer" | ⛔ **war falsch** — `rollen_job.py:444` ruft `fuehre_lauf`; 119–235 Signale/Tag seit 14.08. |
| **P6** | Messbasis für die anderen Klassen | ⚠️ **angefangen** — krypto 523, rohstoffe 35, **aktien 20 (Lauf abgestürzt)**, themen_etf 0 |
| — | Strategie-Geltung der Beiträge auf `einstieg` beschränkt | ✔ gesetzt, ⚠️ **Suite noch nicht grün** |

---

## 6. ⚠️ Der Zusammenhang, der bisher nicht ausgesprochen war

**Drei Baustellen sind in Wahrheit eine Kette:**

```
   keine POSITION (L1, Punkt B)
        |  weil es keine Position gibt,
        v
   keine AKKUMULATION (L2, D1, Punkt A)
        |  weil es keine Akkumulation gibt,
        v
   jeder NACHKAUF ist ein EINSTIEG
        |  und bekommt deshalb
        v
   die EINSTIEGSBEWERTUNG (Stufe 11, G-6)
```

In der Notebook-Produktion sind das **630 NACHKAUFEN mit
`strategie=einstieg`**. Sie werden mit einer Einstiegsbewertung entschieden,
obwohl sie fachlich Akkumulation sind. Das ist heute nicht falsch gerechnet —
es ist gar nicht als eigene Frage gestellt.

⚠️ **Deshalb ist Punkt B (Positionsführung verdrahten) kein Nebenpunkt.**
Er ist die Vorbedingung dafür, dass „je Asset **und je Strategie**" überhaupt
mehr als eine Zelle haben kann.

---

## 7. Was daraus folgt — die Reihenfolge, korrigiert

    ZUERST, weil alles andere daran haengt
      B   Positionsfuehrung verdrahten + Tabelle `positionen`   (L1)
      A   akkumulation setzen, sobald B steht                   (L2, D1)

    PARALLEL MOEGLICH, unabhaengig
      P6  Messbasis aktien/ETF fertigladen                      (Aktienlauf reparieren)
      P7  Schnittabstand je Klasse messen                       -> hebt die Notiz auf
      --  Suite wieder gruen (zwei eingefrorene Pruefungen)

    IHRE ENTSCHEIDUNG, blockiert sonst nichts
      D   Zielallokation je Stufe
      E   Hebel: Kruecke oder warten - ⚠️ er laeuft in KEINER Gruppe
      F   Cooldown / Job-Takt
      C1/C2/C3  Einsatzhoehe, Risikoschwankung, CRV-Spreizung

    SOFORT MESSBAR (die Termine waren falsch)
      J   Lebendigkeit / TVL - 188 Reihen liegen da
      H   V3 Greed-Teilverkauf - Daten da, nie gemessen

---

# FORTSCHREIBUNG 02.09.2026 — Standortbestimmung vor dem Pull

**Nutzerauftrag:** *„Wenn wir jetzt pullen, werden wir wieder lange
fehlersuchen. Bin eher dafür, einen stabilen und möglichst fehlerfreien
Codestand zu pullen. Prüfe und vergleiche, wo wir im Gesamtplan stehen —
Bereiche und Details wie Remoteseite usw. sind noch offen."*

⚠️ **Jede Zeile am Code geprüft**, mit echten Importkanten (AST) und gegen
die Notebook-Produktion. Wo Doku und Code sich widersprechen, gilt der Code.

## 0. ⚠️ Die Zahl, die alles andere einordnet

`origin/main` steht auf dem **29.08.** Am Notebook zählt die Entscheider-
stufe nur; lokal verwirft sie. Der echte Trichter (F-175) sagt:

| | Signale in 4 Tagen |
|---|---|
| heute am Notebook | **113** (+147 Mails) |
| nach einem Pull | **2** |

> **Der Pull ist keine Übertragung, sondern eine Umschaltung des
> Betriebszustands.** Die Sorge vor langer Fehlersuche ist berechtigt —
> aber der Grund wäre nicht ein Fehler, sondern die Menge.

## 1. Die vier Bausteine — Stand heute gegen den 31.08.

| # | Baustein | 31.08. | **02.09.** |
|---|---|---|---|
| **1** | **Positionsführung** | ✘ kein Aufrufer | ✔ **verdrahtet** (Schritt 7). ⚠️ Tabelle `positionen` fehlt weiterhin |
| **2** | **Strategie je Position** | ⚠️ nur `einstieg` (924/5.772) | ⚠️ **Zellenmodell setzt beide** — aber F-169: die zweite Zelle stirbt an `anlass` |
| **3** | **Auslöser statt Takt** | ✘ nicht gebaut | ✘ **unverändert seit 27.08.** |
| **4** | **Potential als Auswahl** | ✔ 3 Beiträge | ⚠️ **2 Beiträge** — der Schnittabstand ist am 31.08. gefallen |

## 2. Der Umbauplan 28.08. — abgeschlossen

Schritte **1–8** gebaut und in einem Lauf nachgewiesen. **N-13** gemessen,
**N-14** gebaut (12. Trichterstufe), **N-13-1′** gemessen, nicht gebaut.

⚠️ **Und der Trichter sagt, dass beide an der falschen Stelle liegen:**
`anlass` + `auswahl` + `wiederholung` nehmen zusammen 97 %. Die neuen
Sperren sitzen genau vor der schärfsten Stufe.

## 3. ⚠️ Die Remoteseite — nicht begonnen

| | Stand |
|---|---|
| `Tailscale-Setup-Anleitung.md` | ✔ Anleitung da — *„Tailscale selbst macht noch nichts an der App"* |
| Steuer-Seite | ✘ **nicht gebaut.** Kein Modul mit `remote`/`steuer` in `agent/` oder `ui/` |
| `Option_Claude_Agent_Anbindung_23_08.md` | ✔ Konzept da (Stufe 0 beschrieben), ✘ nichts umgesetzt |

**Die Remoteseite ist ein eigener, unangetasteter Bereich.** Sie blockiert
nichts und wird von nichts blockiert — aber sie steht in keinem der
laufenden Pläne, und deshalb fiel sie bisher aus jeder Statuszeile heraus.

## 4. Was seit dem 31.08. NICHT weitergekommen ist

| | | warum es hier steht |
|---|---|---|
| **L1** Tabelle `positionen` | ✘ offen | Vorbedingung für „je Strategie" |
| **L2–L7** N-12 | ✘ offen | unverändert seit 26.08. |
| **Baustein 3** Auslöser statt Takt | ✘ offen | seit 27.08. nicht angefasst |
| **D2** `marktbreite` ohne Aufrufer | ✘ offen | am Code bestätigt |
| **A6, C1, C2, C3, D1, D3** | ⚠️ offen | Reparaturliste 23.08. |
| **P6** Messbasis andere Klassen | ⚠️ krypto 523 · rohstoffe 35 · aktien 20 · ETF 0 | der Aktienlauf stürzte ab |
| **H** V3 Greed-Teilverkauf | ✘ nie gemessen | Daten liegen seit Wochen |
| **J** Lebendigkeit/TVL | ✘ nie gemessen | 188 Reihen liegen da |

## 5. ⚠️ Was ein Pull HEUTE mitbrächte — und was daran wackelt

**Stabil und geprüft:**
Zellenmodell · Positionsführung · Gebührentrennung · Stop-Untergrenze ·
I-2 (Paarprüfung) · die Messwerkzeuge · Suite **1928 bei 0 FEHL**

**Wackelig:**

| | Risiko |
|---|---|
| **G-6 scharf** | 113 → 2 Signale. **Die größte Einzeländerung des Jahres** |
| **Schwelle 0,080** | in der Simulation 56,3 Mails/Tag, im echten Trichter 0,5 Signale/Tag — **Faktor 100 daneben** |
| **N-14** | liegt vor der schärfsten Stufe; Wirkung im Betrieb ungemessen |
| **F-169** | die zweite Zelle stirbt an `anlass` — Schritt 3+4 läuft weitgehend leer |

## 6. Die Reihenfolge, die ich vorschlage

    ZUERST — Stabilitaet herstellen, ohne die Menge zu aendern
      1  G-6 und die Schwelle vom Pull ausnehmen (ein Schalter, kein Umbau)
      2  F-169 klaeren: warum stirbt die zweite Zelle an `anlass`
      3  Tabelle `positionen` (L1) - Vorbedingung fuer alles bei "je Strategie"

    DANN — den Betriebszustand bewusst umschalten
      4  G-6 scharf, mit einer vorher entschiedenen Zielmenge
      5  N-14 an die richtige Stelle (nach `wiederholung`, nicht davor)

    UNABHAENGIG, blockiert nichts
      6  Remoteseite Stufe 0
      7  P6 Messbasis aktien/ETF
      8  J (TVL) und H (Greed) messen - Daten liegen seit Wochen

## 7. Der ehrlichste Satz zum Stand

**Die Mechanik ist so weit wie nie — und die Bewertung entscheidet über
0,5 Signale am Tag.** Wir haben drei Tage an Sperren gearbeitet, während
der Trichter sagt, dass 97 % längst vorher wegfallen.

> **Ein stabiler Pull ist nicht der, bei dem alles gebaut ist, sondern
> der, bei dem wir die Menge vorher kennen.** Die kennen wir seit heute.
