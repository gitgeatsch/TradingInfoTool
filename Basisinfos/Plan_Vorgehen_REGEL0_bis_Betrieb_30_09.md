# Plan und Vorgehensweise — von der REGEL0 bis zum Betrieb (30.09.2026)

**Nutzer 30.09.2026:** *„Bitte Plan und Vorgehensweise dokumentieren und auch offene Punkte und Schwächen. Wenn wir eine Lösung haben,
die nur am Desktop im Labor funktioniert, ist es ein FAIL."*

> ⛔⛔ **LEITSATZ (E-35):** Eine Regel ist erst dann fertig, wenn sie **am Notebook im Betrieb** mit den **dort verfügbaren Daten**,
> derselben **Grundgesamtheit** und **ohne Handgriff am Desktop** dieselben Signale erzeugt wie in der Messung. Was nur im Labor läuft,
> ist ein **FAIL**, egal wie gut die Messung ist.

Zugehörige Dokumente: `REGEL0_Hebel_Entwurf_30_09.md` (Parameter und Referenzzahlen) · `Lagebewertung_30_09.md` · `Voranalyse_J_Mindesthistorie_30_09.md` ·
`Voranalyse_REGEL0_Hebelliste_30_09.md` · Stand im Code `python hebel_neubau.py`.

---

## 1. Der Plan — in dieser Reihenfolge

| # | Schritt | Inhalt | Stand |
|---|---|---|---|
| **1** | ⛔ **J Showstopper Mindesthistorie** | Das eigene Normal gilt ab 240 h statt 12 Monate, über die bestehende Schrumpfung, reife Assets bitgleich | Voranalyse zur Abstimmung (J-a bis J-d) |
| **2** | **Schwellenwahl prüfen** | Wählt die Regel auf der **vollständigen** 2024-Menge (nach J) wieder s = +0,035? (49 von 116 Symbolen fehlten 2024 großenteils) | nach J |
| **3** | ⭐ **REGEL0 festschreiben** | Parameter und Referenzzahlen (mit J), im Dokument **und im Code** (eine Konstante, von der Wache geprüft) | nach 1–2, Nutzer-Ja |
| **4** | **Betriebsprüfung REGEL0** (Abschnitt 3) | Welche Daten und Rechenwege hat das Notebook, was fehlt? Das ist eine **Befundaufnahme** und noch kein Bau | nach 3 |
| **5** | **Messung auf der Hebel-Liste** | REGEL0 auf deinen 43 Assets (28 mit Daten, dazu die jungen durch J) | nach 3 |
| **6** | **REGEL1 … n** — ausreizen | je ein Schritt gegen die Vorstufe: **A** Positionsführung · **B** Kern stabilisieren (Dämpfung) · **R** Regime-Kontext aus der Überfüllung · **L** Liquidität in Bewertung 2 · Käuferanteil auf dem Kern | Reihenfolge je Stufe abstimmen |
| **7** | **Betriebsvorbereitung** | Mindestbedingungen abstimmen (Nutzer: *„reden wir, wenn wir zu diesem Schritt kommen“*). Die bestehende Hebel- und Spot-Achse wird **ersetzt**, kein Parallelbetrieb | später |
| **8** | **Umstellung** | nach der ganzen Kette samt LLM-Rollen und Mail | später |

⏸ **Derzeit nicht Teil des Umbaus (Nutzer, E-33):** C Vorwärtstest · D neue Datenquellen · E Börse/Kosten.

---

## 2. Die Vorgehensweise je Schritt — Pflichtablauf

| # | Pflicht | Quelle |
|---|---|---|
| 1 | **Voranalyse** mit Ziel, Stand, *Test oder Betrieb*, Zwischenfazit zum Ziel, dann Abstimmung (Nutzer-Ja) | stehend |
| 2 | **Vorab-Festlegung** der Kriterien, Werkzeug **vor** dem Lauf committet, Funktionstest | stehend |
| 3 | **R-R11**: die Vorstufe (REGELn) zuerst **bitgleich** reproduzieren | R-R11 |
| 4 | Zahlen per **Regel** messen, nie zur Wahl vorlegen. Wahl auf **2024**, **einmal** bestätigt auf 2025–26 | E-24, E-21 |
| 5 | Nullwelt, Zeitstabilität, Weglassprobe, Mehrfachtesten, je Asset, Tagesblock | die sechs Prüfungen |
| 6 | **Spiegelprobe** bei jedem Potential- oder Bewegungsmaß | E-29 |
| 7 | 4 Mengen, Urteil auf **unverzerrt**, wenn es auseinanderläuft | E-30 |
| 8 | ⭐ **Betriebsprüfung** (neu, E-35): Gibt es jede verwendete Größe **am Notebook**? Mit welchem Stand, welcher Historie, welcher Grundgesamtheit? Rechnet es dort **ohne** Desktop? | Abschnitt 3 |
| 9 | Befund, Doku (Zentraldokumente, Regelwerk, Plan, Memory), Wache grün, Commit und Push, **Zwischenfazit zum Ziel** | stehend |

---

## 3. ⛔ Betriebsprüfung — was die REGEL0 am Notebook braucht und was dort ist

Stand laut Doku (`project_messbasen_geraeteaufteilung`, CLAUDE.md). ⚠️ **Das muss am Notebook bestätigt werden** (sparsamer Export, Schritt 4).

| # | braucht die REGEL0 | am Desktop (Labor) | am Notebook (Betrieb), laut Doku | Bewertung |
|---|---|---|---|---|
| **B1** | **Stundenkurse** je Asset (rsi, Ruhe, ATR, Ereignis) | `stundenkurse.db` 346 MB, 116 Symbole ab 2021/2023 | ⚠️ nicht als Datei dokumentiert. Die Betriebskopie `messdaten.db` hat 30 MB, 500 Tage, **ohne eingestellte**. Auflösung zu prüfen | ⛔ **Showstopper-Kandidat** |
| **B2** | **Modelltraining** rsi (monatlich, alle Assets gepoolt, Historie ab 2023) | läuft im Messskript | ⛔ keine Trainingshistorie dokumentiert | ⛔ **Showstopper-Kandidat**. Ein Training am Desktop mit Übergabe von Hand wäre ein **FAIL** (E-35) |
| **B3** | **ATR-Modell** der Hebelstufe (rollierend geschätzt) | im Messskript | wie B2 | ⛔ wie B2 |
| **B4** | **Markpreis** (Liquidation) | `markpreis_historie.db` 722 MB | ⚠️ nicht dokumentiert. Live beziehbar (Binance) | zu prüfen |
| **B5** | **Grundgesamtheit** gleich (die v̂-Skala hängt an der Menge, E-31) | 116 bestand, dazu die eingestellten | Betriebskopie **398 statt 517** im Rang (CLAUDE.md) | ⛔ **muss gleich werden**, sonst andere Signale |
| **B6** | **Symbolzuordnung** Bitpanda ↔ Binance | Namensgleichheit | keine Zuordnung (2.612, vier Symbolwelten) | ⛔ Voraussetzung |
| **B7** | 15 Assets deiner Liste **ohne Stundendaten**, dazu BTC als Leitwert ausgeschlossen | – | – | für diese Assets **kein Signal** möglich. Ist das Beschaffung derselben Datenart (kein D)? Zur Klärung |
| **B8** | das **Normal** (12 Monate beziehungsweise nach J ab 240 h) | aus der Historie | braucht B1 | hängt an B1 |
| **B9** | **Mail, LLM-Rollen, Importer** | – | kennen die neue Bewertung nicht; der Importer teilt Teilschließungen falsch ein (2.679) | Betriebsvorbereitung (Schritt 7) |

➤ **Folge für den Plan:** Jede **REGELn** wird nur dann festgeschrieben, wenn ihre zusätzlichen Größen die Prüfung B1–B9 bestehen
oder ein **Weg am Notebook** feststeht. R (Überfüllung marktweit) und L (Umsatz in USD, Marktkapitalisierung) nutzen Terminmarkt- und
Umsatzdaten, die am Notebook **live** kommen. Das ist dort also eher leichter als die Historie.

---

## 4. Offene Punkte

| # | offen | wann |
|---|---|---|
| O1 | Abstimmung J (J-a bis J-d) | **jetzt** |
| O2 | Schwellenwahl auf der vollständigen 2024-Menge | nach J |
| O3 | Datenlage am Notebook **bestätigen** (B1–B5), mit einem sparsamen Export und nur den nötigen Tabellen | Schritt 4 |
| O4 | Wo und wie das Modell im Betrieb trainiert wird (B2/B3), **ohne Desktop** | Schritt 4, Voranalyse |
| O5 | Die 15 Assets ohne Stundendaten und BTC als Asset: Beschaffung oder Ausschluss? Deine Entscheidung | Schritt 4 |
| O6 | Reihenfolge von A, B, R, L und Käuferanteil | nach Schritt 5 |
| O7 | Mindestbedingungen Betrieb, Ersatz der Achse | Schritt 7 (Nutzer) |
| O8 | Spot-Zugänge PLUME, XDC, INJ | Spot-Arm, später |

---

## 5. Schwächen — ehrlich

| # | Schwäche | Einstufung | Weg |
|---|---|---|---|
| S1 | **Mindesthistorie 12 Monate** | ⛔ **Showstopper** (Nutzer) | J |
| S2 | **Betriebsdaten und Training am Notebook** (B1–B3, B5) | ⛔ **Showstopper-Kandidat** (E-35) | Schritt 4 |
| S3 | Vorteil je Handel (+0,29..+0,31 %) unter den Kosten (0,48 %) in der Messgeometrie | Schwäche | A (Positionsführung), R, L |
| S4 | Das Signalangebot springt (grobes Dämpfungsraster) | Schwäche, Betrieb: unberechenbar | B |
| S5 | Im Gegenwind stumpf (Modell flach) | Schwäche | R, dazu der Informationsgewinn als Auskunft |
| S6 | 2025–26 durch viele Ebenen verbraucht | methodisch | jede Stufe ehrlich als *besser als heute* (E-34) |
| S7 | Die Schwelle ist auf einer zu kleinen 2024-Menge gewählt | methodisch | O2 |
| S8 | 15 Assets der Liste ohne Daten, BTC nie als Asset gemessen | Abdeckung | O5 |
| S9 | Messanlage: bestand überlebensverzerrt, unverzerrt Stichproben | methodisch | E-30, Messung auf der Hebel-Liste |
