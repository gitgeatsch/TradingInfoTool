# Schritt 53 — GUI und Anwendungsfälle: der Lebenszyklus eines Assets

**Stand 14.09.2026 · Befund 2.450 · Nutzervorgabe 07.09. (Gesamtplan 28.08., E1)**

> *„Die umfangreiche Planung mit GUI, Funktionalitäten und Anwendungsfällen —
> neue Assets, Assets fallen weg oder ändern sich."*

Dieses Dokument ist die **Ist-Aufnahme am Code** (jede Aussage mit Fundstelle,
die tragenden gegengeprüft) und ein **Vorschlag mit Entscheidungen**. Es baut
nichts. Umgesetzt wird erst, was entschieden ist.

⚠️ **Vorarbeit, die hier nicht wiederholt wird:** N-13 (01.09., neuer Wert nicht
bewertbar), `pruefe_neuaufnahme.py` (08.09., meldet die drei Fälle), Schritt 49
(Turnover-Basis), Schritt 51 / Befund 2.442 (Stummmeldung gehaltener Werte),
Schritt 32 / 2.448 (GUI an die laufende Kette angeglichen).

---

## Zwei Tatsachen, die jeden Fall prägen

| | |
|---|---|
| **Wo was steht** | Die **Watchlist** steht nur in `Basisinfos/config.yaml` (git-synchronisiert). **Bestände** und die drei **Schalter je Asset** (DCA, Hebel-Prüfung, Bitpanda-Override) stehen in der **Datenbank** — geräteeigen, nicht synchronisiert. |
| **Der Zwischenspeicher** | `config.load_config()` liest die Datei **einmal** und hält sie (`config.py:86`). Nur Schreibvorgänge **desselben Prozesses** leeren ihn. ⚠️ Der Kommentar in `scheduler/background.py:170` („liest config.yaml ohne Caching") ist **falsch**. Folge: eine per `git pull` geänderte Watchlist wirkt am Notebook erst nach einem **Neustart**. |

---

### ⚠️ Welche Schalter einen Neustart brauchen (Nutzerfrage 14.09.)

| Schalter | Ort | Neustart? |
|---|---|---|
| je Asset: Hebel-Prüfung, DCA/Akkumulation, Bitpanda-Override | **Datenbank des Geräts** | **nein** — je Lauf frisch gelesen (`agent/asset_schalter.py:112/122`, `agent/rollen_lauf.py:2144`) |
| global im Menü: Long/Short, E-Mail nur Bitpanda, Suchfilter | `config.yaml` | am Notebook umgestellt: **nein** (die GUI leert den Speicher, `config.py:768`); per Pull gekommen: **ja** |

⚠️ **Die Asset-Schalter werden nicht synchronisiert.** Ein am Desktop gesetztes
Häkchen ändert am Notebook nichts — auch nicht nach Pull und Neustart. Wirksam
sind nur die Schalter in der GUI **am Notebook**.

---

## Fall 1 — Ein neues Asset kommt dazu

**Wege hinein**

| Weg | Schreibt | Fundstelle |
|---|---|---|
| GUI „Asset hinzufügen…" | config.yaml (mit Sicherung), sucht die CoinGecko-ID, prüft CoinGecko und Bitpanda — Warnungen blockieren nicht | `ui/app.py:1649-1777`, `config.py:346-426` |
| Marktscan „In Watchlist übernehmen" | config.yaml, immer `taktisch/beobachtung` | `ui/marktscan_view.py:571-623` |
| ⚠️ **automatisch**: offene Hebel-Position auf unbekanntem Symbol | config.yaml, `name = symbol`, ohne Kategorie — **alle 15 Minuten, auch bei abgeschaltetem Screening** | `scheduler/background.py:3405-3425`, `importer/bitpanda_margin_positions.py:353-423` |
| Bitpanda-Sync, Excel-Import | **nicht** in die Watchlist — unbekannte Symbole werden nur gesammelt | `importer/bitpanda_sync.py:256-260` |

**Was danach von selbst lädt — und was nicht**

| Daten | automatisch? | Voraussetzung |
|---|---|---|
| Preise | ✔ Takt | `coingecko_id` (Wertpapiere: `yfinance_symbol`) |
| Tageskerzen | ✔ alle 24 h | Kraken-Liste oder Binance/Bybit `SYMBOLUSDT`; „nirgends gelistet" steht nur als INFO im Log |
| Marktränge | ✔ je Lauf | **nur für Symbole in der Messbasis** |
| Funding-, Umlaufmengen-, Terminmarkt-Historie | ✖ **von Hand** | `hole_fremdreihen.py`, `hole_umlaufmenge.py`, `hole_terminmarkt_historie.py` — laut `agent/datenfrische.py` schreibt keiner der 21 Jobs sie |
| Messreihen (`messdaten.db`) | ✖ **von Hand, nur Desktop** | `lade_messreihen.py --schreiben` |

**Wann die Kette es beurteilt**

1. Gruppe aus der Watchlist, Cash-Äquivalente raus (`agent/assetklassen.py:108`).
2. Ohne Kursreihe fällt es still heraus, nur INFO (`scheduler/rollen_job.py:440`).
3. Auswahl braucht **mehr als 250 Kerzen**, der Faktenblock **310** (`agent/auswahl.py:140`, `agent/faktenblock.py:270`).
4. Hebel ist **opt-in** — ohne Schalterzeile aus (`database/db.py:1980`).
5. ⚠️ **Ohne Rang in einer Messbasis: „keine Datengrundlage"**, die Kette bricht ab (`agent/rollen_lauf.py:2461`).

**Gemessen am 14.09.** (Messbasis-Dateien am Desktop, Watchlist-Krypto ohne Cash):

| Messbasis | Watchlist-Werte darin |
|---|---|
| Funding | 36 von 43 |
| Turnover | 7 von 43 |
| Terminmarkt | 32 von 43 |
| Schnittabstand | 39 von 43 |
| **in keiner der beiden tragenden (Funding, Turnover)** | **7: FLOKI, AIOZ, SUPRA, CAT, CANTON, VSN, XNO** |

⚠️ **Die Messbasis zu erweitern ist KEINE Datenfrage allein.** Sie ist die Menge,
über die der Beitrag gemessen wurde; ein Rang über eine andere Menge sähe aus
wie ein richtiger (`agent/marktrang.py`, N-13-1). Wer sie erweitert, braucht die
Reproduktion (R-R11).

---

## Fall 2 — Ein Asset fällt weg

| | Heute | Fundstelle |
|---|---|---|
| Entfernen aus der Watchlist | ✖ **gibt es nicht** — weder GUI noch Konfigurations-Funktion noch Übersichtsseite; nur Handarbeit in config.yaml. Nächster Ersatz: `beobachtungsstatus = ausgemustert` | `config.py` (nur add/update) |
| Bestand danach | bleibt **eingefroren** stehen: der Bitpanda-Sync überspringt Werte außerhalb der Watchlist | `importer/bitpanda_sync.py:256-265` |
| Preise, Kerzen | enden — alle Jobs laufen über die Watchlist | |
| ⚠️ **Ausstiegs- und Hebelführung** | **keine** — beide filtern auf die Symbole des Laufs; ein gehaltener, entfernter Wert bekommt keine Ausstiegs- und keine Liquidationsmail | `agent/rollen_lauf.py:939, 966`, `agent/hebelfuehrung.py:389` |
| offene Hebel-Position | das Symbol kommt nach 15 Minuten **automatisch zurück** (Fall 1) | |
| ganz verkauft | Bitpanda-Abnahme wird übernommen | `importer/bitpanda_sync.py:333` |
| Messreihen | bleiben — gewollt, die Messbasis ist breiter als das Portfolio | `pruefe_neuaufnahme.py:228` |

---

## Fall 3 — Ein Asset ändert sich

| Änderung | Heute |
|---|---|
| **Token-Umstellung, Redenominierung** | ✖ **kein Schutz im Betrieb** — der Sprungfilter steht nur in Messskripten (`messe_zielregel.py:72`); `pruefe_neuaufnahme` prüft die Frische je Klasse, nicht Brüche in einer Reihe |
| Umbenennung, anderes Kürzel | nur feste Tabellen (`api/bitpanda.py:54` CANTON→CC, `KRAKEN_PAIR_MAP`); der Bearbeiten-Dialog kann Symbol, Name, Klasse, `yfinance_symbol` und Cash-Kennzeichen **nicht** ändern (`ui/app.py:1780`) |
| CoinGecko-ID | per GUI änderbar — die alte Preishistorie hängt an der alten ID und verwaist (`database/db.py:71`) |
| gleiches Symbol in zwei Klassen | die Produktions-Kerzentabelle hat keinen Klassenschlüssel (`database/db.py:98`, D3) |
| Bitpanda-Delisting | nur ✗ in der GUI; eine fehlgeschlagene Abfrage gilt als handelbar (`agent/asset_schalter.py:178`) |
| Stablecoin / Cash-Äquivalent | nur von Hand in YAML |

---

## Fall 4 — Gehalten, aber nicht in der Watchlist

**Heute nicht eingetreten** (Sicherung 12.09.: 29 Bestände, alle in der
Watchlist). Wenn es eintritt: keine Preise, kein Lauf, keine Ausstiegsführung,
der Bitpanda-Job meldet es nicht (`scheduler/background.py:1693`), die
Stummmeldung überspringt es (`agent/verkaufsrechnung.py:381`),
`pruefe_neuaufnahme` auch (`:155`).

---

## Zur Oberfläche (aus Befund 2.448-rest)

- Übersichtsseite: „Offene Signale" und „Ausstiegsempfehlungen" lesen beide Ketten ohne Trennung.
- Ein Verlauf der Rollen-Hebelzeilen fehlt (der Hebel-Verlauf liest nur `hebel_signals`).
- Die Detailansicht nennt ihre Lücken (Trefferquote, Gebühren, Marktvergleich, Termine) — schließbar nur über den gespeicherten Mailtext, am 14.09. dagegen entschieden.
- Die alten GUI-Wege sind stillgelegt, nicht gelöscht.

---

## Vorschlag — nach Wirkung geordnet

### A · Betrieb: was heute still falsch laufen kann (klein)

| # | Vorschlag | Warum zuerst |
|---|---|---|
| A1 | ✔ **ENTSCHIEDEN 14.09.: Doku berichtigen + Hinweis „Neustart ausstehend"** (Übersichtsseite/Sammelmail), **kein** automatisches Neueinlesen. Nutzer: *„grundsätzlich starte ich nach jedem Pull die App neu, ein stabiler Betrieb ist im Vordergrund."* Der dokumentierte Ablauf ist ohnehin „Pull + Neustart"; das Neueinlesen hätte Einstellungen mitten im Lauf gewechselt | falsche Kommentare (`background.py:170`, `config.yaml:1176`) versprechen Wirkung ohne Neustart |
| A2 | **Gehalten außerhalb der Watchlist melden** — Stummmeldung und Bitpanda-Job nennen solche Bestände | sonst ein Bestand ohne jede Führung, still |
| A3 | **Neuaufnahme sichtbar machen**: Sammelmail/Übersichtsseite nennt Watchlist-Werte, die die Kette nicht beurteilen kann, samt Grund (Kerzen < 250/310, keine Messbasis) | heute 7 Werte, und es steht nur im Log |

### B · Oberfläche: die Anwendungsfälle bedienbar machen (mittel)

| # | Vorschlag |
|---|---|
| B1 | Spalte **„Bewertbar"** in der Watchlist: Kerzen, Funding-/Turnover-/OI-Messbasis — ✔/✖ mit Grund |
| B2 | **Entfernen** als Funktion — mit Sperre, solange ein Bestand oder eine offene Hebel-Position besteht (sonst holt die Automatik das Symbol zurück, Fall 2) |
| B3 | Nach „Asset hinzufügen": **was fehlt noch** und welches Skript es lädt |
| B4 | Übersichtsseite: Kettentrennung in „Offene Signale" und „Ausstiegsempfehlungen"; Verlauf der Rollen-Hebelzeilen |

### C · Daten und Messung: gehört in den Bewertungsblock (groß)

| # | Vorschlag |
|---|---|
| C1 | **Messbasis-Aufnahme** neuer Werte als geregelter Ablauf (Historie laden + Reproduktion) — Messfrage, R-R11 |
| C2 | **Bruchschutz im Betrieb** gegen Token-Umstellungen (der Sprungfilter aus der Messung als Warnung auf der Kursreihe) |
| C3 | Klassenschlüssel in der Produktions-Kerzentabelle (D3) |

### ✔ ENTSCHIEDEN 14.09. — der Neuaufnahme-Ablauf (Nutzerabstimmung)

Grundsatz: **ein gehaltener Wert darf dem System nie unbekannt bleiben; ein
nur vorgeschlagener kommt mit Zustimmung.**

| Weiche | Entscheidung |
|---|---|
| **1 Wer nimmt auf** | Gehaltene Werte (Bitpanda-Bestand, Hebel-Position, GUI-Eingabe) **automatisch**; Marktscan-Kandidaten **nur mit Bestätigung**. ⚠️ Nutzervorgabe dazu, wörtlich: *„sobald ein neuer Bestand vorhanden ist, muss auch die laufende Indikator-Bewertung und gesamte Ablaufkette für das neue Asset gestartet werden."* |
| **2 Wo festgehalten** | `config.yaml` wie heute, plus Hinweis „am Notebook geändert – vor dem nächsten Pull committen" |
| **3 Daten** | automatisch in einem Neuaufnahme-Lauf (Historie, Funding, Umlaufmenge, Terminmarkt), wiederholt bis vollständig oder „gibt es nicht" |
| **4 Signale ohne Messbasis** | **nein** — geführt (Preis, Ausstiegsführung) ohne Einstiegssignal, bis die Messbasis-Aufnahme (C1) entschieden ist |

⚠️ **Vor dem Bau verlangt (Nutzerauftrag 14.09.):** *„Prüfe im Detail alle
Anwendungsfälle, dass das System mit neuen, geänderten, verkauften Positionen
korrekt umgehen kann (Spot und Hebel)."* → Abschnitt „Positionsfälle" (folgt).

### Bewusst NICHT vorgeschlagen

- **Schalter je Asset geräteübergreifend synchronisieren** — das Notebook ist die Produktion; ein Sync vom Desktop hätte dieselbe Klasse Fehler wie der config.yaml-Konflikt. Stattdessen: die Schalter dort bedienen, wo sie wirken.
- **Die Automatik für Hebel-Positionen abschalten** — ein gehaltenes Hebelgeschäft muss bepreist und geführt werden; das Problem ist das fehlende Entfernen (B2), nicht das Nachtragen.

---

## Positionsfälle — Spot und Hebel, im Detail geprüft (14.09.)

**Wie geprüft:** Aufnahme aller Code-Pfade (Such-Agent), die tragenden Aussagen
einzeln am Code gegengelesen (✔ = gegengeprüft), Wirkungen an der
Produktionssicherung 2026-09-12_0646 gemessen (📏). Nicht einzeln
gegengeprüfte Aussagen sind mit ○ markiert.

### Die Takte

| Was | Takt | Fundstelle |
|---|---|---|
| Bitpanda-Bestandsabgleich (Spot) | alle 30 min | `scheduler/background.py:71` |
| Hebel-Positionsabgleich **und** Rollen-Kette | alle 15 min, in dieser Reihenfolge | `background.py:3399–3505` |
| Wiederholsperre (Cooldown) | Krypto 12 h · Akkumulation 48 h · nach Hebel ≥ 2: 3,5 h · übrige Klassen 24 h | `agent/wiederholung.py` |
| Portfoliowert = Kapital für den Hebel | täglich 06:30 | `background.py:4259` ✔ |
| Ausstiegsmail (Stop nachziehen) | täglich 07:15 | `background.py:562` ✔ |

⚠️ **Nichts startet einen Lauf sofort.** Ein neuer Bestand wartet auf den
nächsten Takt.

### Spot

| # | Fall | Heute | |
|---|---|---|---|
| S1 | Erstkauf, Wert in der Watchlist | Abgleich schreibt den Bestand; der Wert überspringt die Auswahl; **Anlassprüfung und Cooldown gelten weiter**. Die Anlassbeobachtung wird VOR dem Cooldown geschrieben — die Änderung „Bestand" ist beim nächsten Takt schon verbraucht. 📏 Gehaltene Kryptowerte wurden 09.–12.09. alle **12 bis 20 h** beurteilt; 27 % der Beobachtungen „unverändert" | ✔ `rollen_lauf.py:1294–1456` |
| S2 | Kauf eines Werts außerhalb der Watchlist | **still übersprungen** — kein Bestand, kein Lauf, kein Kapital, keine Meldung | ✔ `bitpanda_sync.py:256` |
| S3 | Nachkauf | Menge wird übernommen; **Einstand nur per Knopf** neu gerechnet; Margin-Buchungen fließen in den Spot-Einstand ein ○; eine Hand-Überschreibung bleibt auch nach Komplettverkauf ○ | `bitpanda_avg_cost.py` |
| S4 | Teilverkauf | nur mit gelungener Staking-Prüfung übernommen, sonst Mail „bestätigen". ⚠️ **Jeder Rückgang bestätigt ein offenes VERKAUFEN/REDUZIEREN automatisch als umgesetzt** — auch ein Staking-Transfer | ✔ `bitpanda_sync.py:312–340` |
| S5 | Komplettverkauf | Zeile bleibt mit Menge 0. Offene Signale bleiben offen; ⚠️ **die Ausstiegsmail empfiehlt weiter „Stop nachziehen"** — sie listet offene *Signale*, nicht Bestände. ⚠️ Fehlt ein Wallet in der API, bleibt die **alte Menge stehen** (Phantom) | ✔ `backward_tracking.py:5386`, `background.py:604`, `bitpanda_sync.py:344` |
| S6 | Staking | gestakte Menge zählt für Kette und Kapital; teils nur `quantity > 0` gelesen (Warteschlange, Stummmeldung) ○ | |
| — | Topf „belegt" | zählt nur Signale **ohne** Ergebnisstatus. 📏 **1 Signal (500 EUR) statt 239 offener (115.100 EUR)** — „Im Topf frei" zeigt fast immer den vollen Topf; reine Anzeige, begrenzt nichts | ✔ `toepfe.py:321`, `backward_tracking.py:1308` |
| — | Kapital | Vortageswert ohne Cash und ohne Hebel-Eigenkapital; ein neuer Bestand zählt frühestens am Folgetag — der Hebel fällt dann eher **kleiner** aus | ✔ `portfolio_historie.py:1142` |

### Hebel

| # | Fall | Heute | |
|---|---|---|---|
| H1 | Eröffnung | aus Margin-Buchungen rekonstruiert, **Richtung immer LONG** — Bitpanda führt keine Hebel-Shorts aus (`config.yaml` RM-10), also gewollt. Hebelführung im selben Takt; Plan-Zuordnung nur zu einem Rollen-Signal der letzten 24 h. ⚠️ Eine reine Hebel-Position zählt für die Kette **nicht als Bestand** (Auswahl, Terminmarkt, Cooldown gelten) ○ | ✔ `bitpanda_margin_positions.py:268`; `rollen_lauf.py:1375` ○ |
| H2 | Aufstocken | Wert, Kredit, Menge addiert; Eröffnungsdatum bleibt ○ | |
| H3 | Teilschließung | eine große Teilschließung kann als **Vollschließung** gelten ○ | `bitpanda_margin_positions.py:233` |
| H4 | Schließung | Status `geschlossen`, raus aus Deckel, Führung, Warteschlange ○ | |
| H5 | Liquidation | erst **nachträglich** über eine Gebührenauffälligkeit erkannt; vorher warnt die Hebelführung am geschätzten Preis ○ | |
| H6 | Position auf unbekanntem Symbol | automatisch in die Watchlist ✔; **Hebelführung erst, wenn Kerzen da sind** (bis 24 h), der Aggregat-Deckel zählt sie sofort ○ | `background.py:3405`, `rollen_lauf.py:966` ✔ |
| H7 | SHORT-Signal bei „Nur Long" | Mail unterdrückt ✔ (2.447-schalter); das Signal belegt 24 h den Aggregat-Deckel ○ | |
| — | Spot **und** Hebel auf demselben Wert | der Verkaufszweig nimmt die **Hebel-Position**, der Spot-Bestand wird für diesen Verkauf übergangen | ✔ `rollen_lauf.py:1697` |
| — | Hebel-Abgleich fällt aus | nur Logzeile, keine Mail ○ | `background.py:3447` |

### Eine gehaltene Absicherung ohne Urteil

📏 **DBPK** (gehalten, 1.739 Stück): letztes Urteil **22.08.** Seither passierte
es die Anlassstufe neunmal — ein Urteil entstand nie. Das ist die Folge von R2
(Schritt 33): die Absicherung liefert keine Richtung, und KAUFEN/NACHKAUFEN
verlangen eine. **Eine gehaltene Position ist seit drei Wochen ungeführt.**
3QSS wird beurteilt (letztes Urteil 09.09.).

---

## Entscheidungen zu den Positionsfällen (einzeln mit dem Nutzer, 14.09.)

| Punkt | Befund | Entscheidung |
|---|---|---|
| 1 | 2.451-absicherung — DBPK seit 22.08. ohne Urteil. **Ursache im Notebook-Log belegt**: *„DBPK: NACHKAUFEN ohne Richtung – erlaubt (LONG, SHORT), bekommen None"* (31.08.), 3QSS ebenso; die verworfene Empfehlung schreibt keine Zeile, nur eine Warnung. Nebenbei: yfinance meldete am 02.09. `DBPK.DE: possibly delisted` | ✔ **Wächter jetzt**: die Sammelmail meldet jede gehaltene Position ohne Urteil seit N Tagen, samt Grund aus dem Lauf. **R2 bleibt in Schritt 33** (LLM-Schiene, nach der Messung) |
| 2 | 2.451-sofort — neuer Bestand erst nach 12–20 h beurteilt (Cooldown, Anlass vor Cooldown verbraucht) | ✔ **Bestandsänderung hebt Cooldown und Anlass einmal auf**: Menge seit dem letzten Urteil geändert (`holdings.updated_at`, Hebel eröffnet/geschlossen) → Urteil im nächsten Takt, spätestens ~45 min. Routinebremsen bleiben |
| 3 | 2.451-verkauf — **präzisiert**: die tägliche Ausstiegsmail (07:15) führt SIGNALE statt Positionen. 📏 127 Zeilen für 23 Werte (18× QNT, 17× AVAX, 15× ETH), 125 aus der Rollen-Kette, 13 Zeilen für nicht gehaltene Werte, 0 als umgesetzt markiert. Spot hat laut `positionsfuehrung.py` keinen Stop und kein R. ⚠️ Eigene Korrektur: SEI, BNB, VSN sind nicht verkauft, sondern vollständig gestakt (Menge 0, gestakt > 0) | ✔ **Mail auf Positionen umstellen**: eine Zeile je gehaltener Position aus `positionsfuehrung` (Einstand, Ergebnis EUR/%), Hebel mit Stop-Empfehlung, Spot ohne R; nicht gehaltene Signale nur noch in der Messung |
| 4 | 2.451-bestaetigung — ein Rückgang der **Stückzahl** eines Assets (Bitpanda: Wallet-Balance, nicht Cash) bestätigt ein offenes VERKAUFEN/REDUZIEREN automatisch als umgesetzt, auch bei Staking; gespeichert wird die Rest- statt der verkauften Menge. 📏 bisher 1 Fall (XNO 24.08.) | ✔ **automatisch bleibt, präzisiert**: nur bestätigen, wenn der Rückgang nicht durch mehr gestakte Stück erklärt ist; als Menge die **verkaufte Stückzahl** speichern. Nutzer: *immer Menge der Assets* |
| 5 | 2.451-phantom — liefert Bitpanda ein Asset nicht mehr, bleibt die alte Stückzahl still stehen (bewusst: unbekannt ist nicht verkauft, P-10); nur der manuelle Dialog zeigt es | ✔ **melden**: Sammelmail und Übersichtsseite nennen es mit Datum, nur bei Änderung, gleicher Meldeweg wie die Neuaufnahme; P-10 bleibt |
| 6 | 2.451-topf — belegt zählt nur Signale ohne Ergebnisstatus (📏 1 statt 239 offene); die offenen mitzuzählen ergäbe 115.100 EUR aus meist nie ausgeführten Empfehlungen; richtig wäre: aus Empfehlungen gekauft und noch gehalten — dafür fehlt die Verknüpfung Kauf ↔ Empfehlung | ✔ **jetzt kennzeichnen** (Füllstand nicht bestimmbar), **später richtig zählen**: der Abgleich verknüpft eine Mengenzunahme mit der offenen KAUFEN/NACHKAUFEN-Empfehlung (Gegenstück zu Punkt 4), der Topf zählt umgesetzte, noch gehaltene |

### Punkt 7 — die kleineren Hebel-Fälle, gegengeprüft (14.09.)

| Fall | Ergebnis der Prüfung | Einstufung |
|---|---|---|
| 7a Teilschließung als Vollschließung | **kein Fehler.** Die Regel „Erlös deckt den Kredit" stammt aus echten Bitpanda-Rohdaten. Am echten Fall HYPE (26.07.): 7,70 Stück zur Tilgung verkauft (400 EUR), die **restlichen 3,79 Stück im selben Moment ebenfalls verkauft** (197,63 EUR) — eine Vollschließung in zwei Verkaufsbuchungen. Produktionstabelle: 188 Positionen, 184 geschlossen, 4 wahrscheinlich liquidiert, **keine offen** (letzte eröffnet 22.07.). ⚠️ Das Nachspielen mit dem Export vom 03.08. war **nicht deckungsgleich** (4 statt 184 Schließungen) — der Export bildet die Margin-Buchungen nicht vollständig ab; daraus kein Befund | erledigt |
| 7b Liquidation erst nachträglich | **bewusst.** Die API meldet keine Liquidation; erkannt an der 1-%-Zwangsgebühr, laut `docs/hebel_positionsformel.md` an 4 Fällen bestätigt. Davor warnt die Hebelführung am geschätzten Preis „eher zu früh als zu spät" (`hebelfuehrung.py:272`) | erledigt; die Treffsicherheit der Schätzung ist nicht nachgemessen |
| 7c Spot **und** Hebel auf demselben Wert | **bewusst** (S6b, Kommentar `rollen_lauf.py:1676`): die Hebel-Position hat Vorrang, weil sie ein Ausfallrisiko trägt. Folge: eine Verkaufsempfehlung bezieht sich dann **nur** auf die Hebel-Position, der Spot-Bestand bleibt unberücksichtigt. Heute theoretisch, seit Paket B wieder möglich | vorzulegen |
| 7d Hebel-Abgleich fällt aus | **bestätigt, bewusst** (Vorfall 18.08.: ein Ausfall kostete den ganzen Umlauf) — seither nur Logwarnung. Kehrseite: ein **länger anhaltender** Ausfall bleibt unbemerkt, die Hebelführung arbeitet auf veraltetem Stand | vorzulegen |

**Entscheidungen zu Punkt 7 (14.09.):**

- **7d** ✔ Mail bei **anhaltendem** Ausfall des Hebel-Abgleichs (vorhandener Fehler-Mailweg, erst nach mehreren Fehlschlägen in Folge, mit Spamsperre) — Nutzervorgabe: *mit aussagekräftigem Betreff und Inhalt*. Die Kette läuft weiter wie seit dem 18.08.
- **7c** ✔ **Ein Asset, zwei Positionen — sauberer, fachlich korrekter Umbau** (Nutzer: *es ist ein Asset mit zwei Positionen*). Die Gestaltung wird vor dem Bau im Detail abgestimmt (folgt).

---

## Ausstieg und Positionsführung — Diskussion mit dem Nutzer (14.09.)

Die Themen werden **einzeln** behandelt (Nutzervorgabe: *„du bist schon wieder
zu schnell"*).

| Thema | Stand |
|---|---|
| **A Verkaufen/Reduzieren** | ✔ Einig: beide gehören **gemessen und sauber ins Konzept übernommen**, sonst ergeben sie keinen Sinn. Befund-Grundlage: die Ausstiegsseite läuft an der ganzen Bewertung vorbei (2.392); VERKAUFEN des Modells schlägt den Zufall als Hinweis (2.403, H10 78,8 % gegen 50 %, n = 80), REDUZIEREN nicht. **Offen:** die erforderlichen Bewertungen und Urteile — mit dem Nutzer zu **dimensionieren**, wie beim Einstieg |
| **B Hebel** | in Diskussion — Takt (3,5 h stammt aus der alten Kette, Nutzer möchte 1 h, realistisch) und Führung nach Marktsituation |
| **C Kern / Akkumulation** | ✔ **vorerst keine Verkaufsaktionen.** Nachgelagert in den Plan: *„bei längerem Greed u. U. sinnvoll — Fear macht keinen Sinn"*. Expertenmeinung und Prüfung der Vorgaben folgen als eigenes Thema |


---

## Fortsetzung 10.10.2026 — Voranalyse GUI-Bereinigung im 3. Umbau (Hebel REGEL0 / Spot-Neubau)

**Auftrag (Nutzer 10.10.):** *„Ich würde gerne die GUI bereinigen und optimieren – u. U. sind auch ganze TABs zusammenzuführen, da einige Schalter und Funktionen u. U. nicht mehr relevant sind.“*

- **Nutzung:** *„GUI nur für Wartungen und manuelle Aufgaben, nur wenn erforderlich – primär Signalmails und die Übersichtsseite“*.
  - Die Übersichtsseite ist *„über VPN eine Statusseite mit den wichtigsten Systeminformationen“* (`remote/status.py` + `remote/server.py`).
- **Gerät:** *„Am Desktop läuft die Anwendung nicht, ich greife nur remote auf das NB zu.“*
- **Ziel:** *„Die GUI ist historisch gewachsen … Die neue HEBEL- und SPOT-Funktionalität soll integriert und wenn möglich fachlich und technisch sauber gruppiert werden.“*
- ⚠️ **Vorgabe:** *„wir sind im 3. großen Umbau – es dürfen keine Grundfunktionen brechen“*.
  - Dazu: *„alte Funktionen können durch neue ersetzt werden oder nicht mehr benötigt sein – z. B. die automatische Asset-Aufnahme bei Spot und Hebel gegenüber der manuellen“*.

**Grundlage:**
- Zwei Inventare aus dem Code (Watchlist/Portfolio/Signale/Marktscan/Menüs; Screener/Hebel/Regime/Schwerpunkte/Statusseite).
- Die schweren Aussagen sind **am Code nachgeprüft**: `portfolio.py:286`, `bitpanda_avg_cost.py:212-227`, `rollen_job.py:104-108`, `excel_import.py:118-123`, H15/REGEL0 nicht in `ui/`/`remote/`, Marge 0,09 doppelt.
- ⚠️ Die lokale `data/tradinginfotool.db` am Desktop steht im Juli. Die Datenfrische am NB ist aus Code und Schaltern abgeleitet, nicht gemessen.

### G-A Grundfunktionen — bleiben erhalten (jede mit Nachweis vorher/nachher)

| # | Grundfunktion | heute |
|---|---|---|
| GF1 | **Statusseite** über VPN: Betrieb, Kontingente, Knöpfe Preise / Marktscan / Not-Reset / Neustart, letzte Fehler | `remote/` |
| GF2 | **Hebel-Schalter je Asset** (REGEL0 mailt nur mit Schalter) | Watchlist *Hebel-Prüfung umschalten* → `asset_hebel_settings` |
| GF3 | **Bitpanda-Abgleich von Hand** | Datei › Von Bitpanda abgleichen |
| GF4 | **Einstand von Hand** (Doppelklick Portfolio) | `AvgBuyPriceDialog` |
| GF5 | **Asset hinzufügen / bearbeiten** (auch Aktien, ETF, Rohstoffe) | Watchlist |
| GF6 | **Bitpanda-Override** (gelistet ja/nein) | Watchlist |
| GF7 | **Bestand ansehen** (Menge frei/gestakt, Wert, G/V) | Portfolio |
| GF8 | **Offene Hebelpositionen** mit Liquidationspreis | Hebel |
| GF9 | **REGEL0-Signale** mit Mailtext und Prüfblock | Hebel |
| GF10 | Charts (Doppelklick), Dark Mode, Thesen/Schwerpunkte pflegen | Watchlist, Ansicht, Schwerpunkte |
| GF11 | **Alles, was Jobs und Mails aus `ui/` nutzen** (z. B. `ui/trade_chart.py` in `rollen_lauf`, `ui/liquidity_chart.py`) | vor jedem Entfernen Leser suchen |

### G-B Befund je Tab (A = aktuell · W = Wartung · X = alt, Schreiber steht)

| Tab | A | W | X (alt) | Fehler / irreführend |
|---|---|---|---|---|
| **Watchlist** | Preise, Status *Gehalten* (frei + gestakt), Chart, **Hebel-Prüfung** (REGEL0) | Hinzufügen/Bearbeiten, Bitpanda-Override, Schwerpunkt, Zusammensetzung | Akkumulation (Leser steht), Zeilen-Tooltip *Letztes Signal* (Stand ≤ 05.10., REGEL0 fehlt), Rollen *core/taktisch* (≠ E-90) | Der Tooltip *Hebel-Prüfung* spricht von der Rollen-Kette; die Meldung nach *Hinzufügen* verspricht Signale *„beim nächsten Takt“* |
| **Portfolio** | Bestand, Gesamtwert, Diversifikation | Einstand-Dialog | *Letzte Bewertung anzeigen* (alte Kette) | ⛔ **Wert = 0 bei voll gestakt** (`portfolio.py:286`, O37); G/V „-“ bei q = 0; Fiat-Feld *„manuell“*, wird aber vom Cash-Abgleich überschrieben; der Zusatz *„im Regelwerk nicht berücksichtigt“* meint die alte Kette |
| **Signale** | — | Rückmeldung (alt) | **ganzer Tab**: nur `signals` der Rollen-Kette, Stand ≤ 05.10., ohne Veraltet-Hinweis, *neuestes zuerst*; Knöpfe gesperrt | ⛔ wirkt aktuell, ist es nicht. Der Sperrtext *„läuft über die Rollen-Kette (automatisch im Takt)“* ist falsch (Kette angehalten). Die Rückmeldung schreibt nur `quantity` |
| **Marktscan** | Kandidatenliste, *Jetzt scannen*, Erfolg | Übernehmen, Verwerfen | P-5-Texte, P-5-Knopf (Allocator aus) | Tooltip *„wartet auf Budget-Allocator“*; *Übernehmen* sagt *„Neustart nötig“*, *Hinzufügen* sagt das Gegenteil |
| **Screener** | — | Scan (yfinance), Übernehmen | — | verspricht Bewertung *„über die normale Signal-Pipeline“*; für Aktien/ETF läuft keine |
| **Hebel** | **REGEL0-Zeilen + Detail**, **offene Positionen + Liq.-Preis**, Spalte REGEL0 | Filter, Schalter | alte `hebel_signals`, Rollen-Hebelsignale, Kandidaten (`hebel_triggers`), *Jetzt analysieren*, *Signal-Historie* (nur alte Kette) | **kein Abstand in %, keine H15-Empfehlung, kein aktueller Kurs**; nur das jüngste REGEL0-Signal je Asset, keine REGEL0-Historie; Tooltip *„Führung kommt später (O13)“* veraltet; Text *„nächster Budget-Allocator-Lauf“*; Liq.-Marge 0,09 an zwei Stellen gepflegt (`config.yaml:506` und `entscheidungsrechnung.GRENZEN`) |
| **Regime** | — | Override (wirkungslos) | **ganzer Tab** (liest `signals.regime`, Parameter alter Regelwerke) | *„Wirkt ab dem nächsten Pipeline-Lauf“* — es läuft keine |
| **Schwerpunkte** | — | Thesen pflegen, Vorschläge übernehmen | Tages-Synthese (läuft weiter, **verbraucht Gemini**) | REGEL0 liest keine Thesen; Wirkung nur auf die Markierungen in Screener/Watchlist |
| **Menüs** | Datei › Von Bitpanda abgleichen | Dark Mode | Benachrichtigungen › *nur Bitpanda-gelistet* (nur alte Mails), Hebel › *Long+Short/Nur Long* (nur alter Mailfilter), Marktsuche › *nur handelbar* (nur Screener) | ⛔ **Datei › Einstandspreise berechnen überschreibt `staked_quantity` mit der alten Rekonstruktion** (das Verfahren, das früher verdoppelte; der Job korrigiert in 30 min); Datei › Export/Import nur `quantity` (voll gestakt = 0); die Schalter-Meldungen *„Commit + Push (Desktop) und Pull“* passen nicht zum NB-Betrieb |

### G-C Statusseite (Hauptwerkzeug neben den Mails)

| | |
|---|---|
| aktuell | Portfolio (frei + gestakt + Fiat), veraltete Preise, letzter Marktscan, CoinGecko-/Gemini-Kontingent, API-Status, Knöpfe, letzte Fehler |
| alt / irreführend | *LLM-Kontingent Rollen-Kette*: Urteile heute dauerhaft 0, ohne Hinweis · der REGEL0-Prüfblock (`gemini-3.5-flash-lite`) erscheint vermutlich als *„Gemini 3.5 (Rückfall)“* der Kette · Abschnitt A *„Ausgeführte Empfehlungen“* enthält nur die Marktscan-Quote · Abschnitt B *„Z.ai“* ist leer · Abschnitt C *„Veto-Schatten“* enthält *Stop nachziehen* · Regime, Parameter, Themenfelder alt · Rollennamen *Kette 1/2/3* |
| berechnet, nicht gezeigt | `offene_signale`, `provider_sendezaehler`, `cash_reserve_synced_at`, `staked_value_eur` |
| **fehlt ganz** | **REGEL0** (letzter Stundenlauf, Signale heute, Mailstand, Prüfblock) · **Hebelpositionen mit Abstand und H15-Empfehlung**, letzter H15-Lauf · Frische Hebel-Abgleich (`hebel_abgleich.frische` vorhanden) · Zeitpunkt Bitpanda-Bestandsabgleich · **Schalterstand** (`testwoche_freigegeben`, `spot_kette_angehalten`, `alter_hebelweg_aus`, `ankuendigung_aktiv`) · letzter Stop-Nachzieh-Lauf · offene NB-Kontrollen · Hebel-Eigenkapital im Wert |

### G-D Asset-Aufnahme — automatisch gegen manuell

| Weg heute | Art | Bewertung |
|---|---|---|
| REGEL0-Datenbasis (täglich, alle Binance-Assets) | automatisch | bleibt; Lücke O38 (tokenisierte Aktien) per Regel schließen |
| Hebelposition auf unbekanntem Symbol → Watchlist (`bitpanda_margin_positions.py:413`) | automatisch | bleibt (sonst keine Führung) |
| **REGEL0-Mail nur mit Hebel-Schalter** je Watchlist-Asset | **manuell (Opt-in)** | **bewusst manuell lassen**: Das ist deine Freigabe, auf welchem Wert Hebel überhaupt in Frage kommt. Der Schalter gehört aber in den **Hebel-Bereich**, nicht in die Watchlist |
| Neuer Spot-Bestand bei Bitpanda → nur Mail | manuell | → **automatisch (O26)** über die Asset-ID mit Preisabgleich und Sperren (`symbol_zuordnung.csv`); E-90 macht jeden neuen Krypto-Bestand automatisch L |
| Krypto-Watchlist *beobachtung* (FLOKI, GRIFFAIN, IMX …) | manuell | Der Spot-Neubau rechnet auf dem **ganzen Binance-Universum**. Für die Krypto-Beobachtung wird eine Hand-Watchlist **dafür nicht mehr gebraucht** (offen: Nutzt sie noch etwas außer Hebel-Schalter und Anzeige?) |
| Aktien, ETF, Rohstoffe (OD7L, EXH3, PLTR …) | manuell | **bleibt manuell** (keine automatische Quelle; der Spot-Neubau ist Krypto) |
| Screener / Marktscan *Übernehmen* | manuell | nur sinnvoll, wenn die Entdeckung weiter gewünscht ist (Abstimmung) |

### G-E Sofortliste — Fehler, die unabhängig vom Umbau zu beheben sind (klein)

| # | Fehler | Wirkung |
|---|---|---|
| S-1 | Portfolio-Wert und G/V nur aus `quantity` | Wert 0 bei 10 voll gestakten Werten (O37) |
| S-2 | **Einstandspreise berechnen überschreibt `staked_quantity`** | bis zum nächsten Job (30 min) falscher Staking-Bestand |
| S-3 | Export/Import Excel nur `quantity` | Gestakte fehlen im Export; der Import kollidiert mit dem Abgleich |
| S-4 | Signale-Tab ohne Veraltet-Hinweis | wirkt wie aktuelle Empfehlungen |
| S-5 | falsche Hinweistexte (Sperrtext, Tooltip Hebel-Prüfung, Regime-Override, Allocator, O13, Fiat *manuell*) | Fehlbedienung |

### G-F Zielbild (Vorschlag zur Abstimmung)

**Statusseite = Lagebild** (zuerst, weil Hauptwerkzeug):
1. **Betrieb:** Jobs mit letztem Lauf, Frische, Kontingente, Fehler.
2. **Hebel:** REGEL0 heute; offene Positionen mit Kurs, Liquidation, **Abstand %** und **H15-Empfehlung**; Schalterstand.
3. **Spot:** Bestand frei + gestakt; später Ampel und offene Handlungen.
4. **Kontrollen und Warnungen.**

Alte Karten entfallen.

**GUI = Wartung**, von 8 auf 5 Tabs:

| neu | Inhalt | aus heute |
|---|---|---|
| **Bestand** | Spot (frei + gestakt richtig bewertet, Einstand, Cash) und Hebelpositionen **getrennt** | Portfolio + untere Hebel-Tabelle |
| **Hebel** | REGEL0-Liste **mit Historie**, Detail, Positionen mit Abstand/H15, **Hebel-Schalter je Asset** | Hebel (ohne Altlisten) + Schalter aus der Watchlist |
| **Spot** | vorerst Watchlist-Fünftel und Bestandsrollen (Kern/L) als Anzeige; Ampel und Handlungen mit dem Spot-Bau (Stufe 1) | neu |
| **Assets** | Stammdaten: hinzufügen, bearbeiten, Bitpanda-Override, Zuordnung/Sperren, Chart; Aktien/ETF/Rohstoffe | Watchlist (ohne Akkumulation) |
| **Archiv (nur lesen)** oder entfernen | alte Signale, Regime, Marktscan/Screener, Schwerpunkte — je nach Abstimmung | Signale, Regime, Marktscan, Screener, Schwerpunkte |

### G-G Vorgehen, damit keine Grundfunktion bricht

1. **Stufe 0 (Sofortliste S-1 bis S-5):** klein, eigener Push, Prüfstand je View gegen eine Kopie (nie `main.py` am Desktop).
2. **Stufe 1 Statusseite:** neue Karten Hebel/REGEL0/H15/Schalter, alte Karten raus.
3. **Stufe 2 GUI-Tabs** in der Reihenfolge Hebel → Bestand → Assets → Spot.
4. **Archivieren oder Entfernen** erst nach der Leser/Schreiber-Prüfung je Funktion (Lehre H15: *Wer liest/schreibt das noch?*).
5. **Je Stufe:**
   - Liste GF1–GF11 vorher/nachher;
   - Paket `GuiKette` erweitert, ganze Suite;
   - eine NB-Änderung, Pull + Neustart, Kontrolle.

### G-H Fragen zur Abstimmung (Punkt für Punkt)

| # | Frage |
|---|---|
| G1 | Sofortliste S-1 bis S-5 zuerst (unabhängig vom Umbau)? |
| G2 | Zielbild: Statusseite = Lagebild, GUI = Wartung mit 5 Tabs — so? |
| G3 | Alte Tabs (Signale, Regime): **Archiv (nur lesen)** oder **entfernen**? |
| G4 | Marktscan, Screener, Schwerpunkte: Werden die Entdeckung neuer Werte und die Thesenpflege noch gebraucht? (Die Tages-Synthese verbraucht weiter Gemini.) |
| G5 | Asset-Aufnahme: Spot-Bestand automatisch (O26), Hebel-Schalter bewusst manuell im Hebel-Tab, Krypto-Hand-Watchlist entfällt, Aktien/ETF/Rohstoffe bleiben manuell — so? |
| G6 | Akkumulation (DCA-Schalter): entfällt sie, oder kommt sie mit dem Akkumulations-Strang neu? |

### G-I Stufe 0 gebaut — Sofortliste S-1 bis S-5 (10.10.2026, Nutzer: *„G1 ja, Sofortliste zuerst bauen, prüfen und gegenprüfen“*)

| # | Bau | Datei |
|---|---|---|
| S-1 | Zeile *Wert* = (frei + gestakt) × Preis; G/V über frei + gestakt. `compute_cost_basis_view` bekommt ein **optionales** `menge`; nur das Portfolio übergibt es, die fünf Analysten rechnen unverändert. Summen unten unverändert (sie waren schon richtig). Einstand-Dialog *„nur x von y bepreist“* auf frei + gestakt | `importer/bitpanda_avg_cost.py`, `ui/portfolio.py` |
| S-2 | *Einstandspreise berechnen* schreibt `staked_quantity` nur noch im **alten** Abgleich (`bitpanda.bestand_quelle: alt`); beim neuen gehört das Gestakte allein den Wallet-Salden | `importer/bitpanda_avg_cost.py` |
| S-3 | Export: Spalten **Gestakt** und **Gesamt** (*Anzahl Coins* bleibt frei → Rundweg ohne Doppelzählung). Import: ein vom Bitpanda-Abgleich geführter Bestand wird **nicht** überschrieben, sondern gemeldet | `importer/excel_import.py` |
| S-4 | Signale-Tab: Hinweis **„⚠ NICHT AKTUELL … Rollen-Kette seit 05.10.2026 angehalten …“**, solange `spot_kette_angehalten`; ebenso im Watchlist-Zeilentipp *Letztes Signal* | `ui/signals_view.py`, `ui/app.py`, `scheduler/rollen_job.kette_angehalten_hinweis` |
| S-5 | Texte: Sperrtext nennt den Halt; Tooltip *Hebel-Prüfung* = REGEL0-Opt-in + H15; Meldung nach *Hinzufügen*; zwei Menü-Schaltertexte (*wirkt nur auf alte Mails*); Regime-Override (*derzeit ohne Wirkung*); Hebel-Tipp O13 → H15; Kandidat *„nächster Budget-Allocator-Lauf“*; Screener; Fiat *„vom Bitpanda-Abgleich“*; Zusatz *„im Regelwerk nicht berücksichtigt“* entfernt. Der Allocator-Satz im Marktscan stand nur im **Kommentar**, nicht in der Anzeige — unverändert | `ui/*.py`, `scheduler/rollen_job.py` |

**Nachweis:**
- Prüfstand `sofortliste_pruefstand.py` **9/9**: Views einzeln gegen eine Wegwerf-DB, Standard-DB per Prüfsumme unverändert.
  - ⚠️ Ein eigener Prüffehler wurde behoben: Der S2-Lauf im alten Weg setzt gestakte Mengen zurück (wie vorgesehen); S3 lief zuerst auf diesem Stand.
- Gegenprobe `sofortliste_gegenprobe.py` **5/5**:
  - 4.000 Einstandsrechnungen gegen eine eigene Formel;
  - Aufrufer aus dem Quelltext abgeleitet (nur das Portfolio übergibt `menge`);
  - 25 Zufallszeilen und Gesamtwert;
  - echte config mit `bestand_quelle = neu` (am NB belegt durch das Log *„Bitpanda-Bestand (neu)“*);
  - Excel-Rundweg exakt, Abgleich-Bestand geschützt.
- Paket `GuiKette` **27/27** (Prüfstand als Wache eingehängt) · **ganze Suite 3.233, nur die 5 bekannten roten**.
- Grundfunktionen GF1–GF11: keine entfernt. Die Sperrlogik der alten Knöpfe ist unverändert, nur ihr Text.

### G-J Watchlist und Spot-Bereich — Abstimmung 10.10.2026

Nutzer 10.10.:
- *„wir sind noch nicht bei Multiassets wie Rohstoffen, aber diese sollten wenn möglich wie bei Krypto automatisch in den Bestand übernommen werden – aber dort sind wir noch nicht im Plan“*
- *„Beobachtungen der gewünschten Assets mache ich manuell“*
- *„1. ja Meine Assets – wäre der gesamte Bestand“*
- *„2. reden wir nur von Krypto? Spot und Hebel oder getrennt? Das wäre eine Kombination aus Screener-Einstieg und Bestand? Eine Bevorzugung des Bestandes benötigen wir nur – nach alter Kette – wenn der Cooldown und Prüftakt es erfordern; wenn nicht, dann können diese gleichwertig behandelt werden“*
- *„3. JA, alles was noch nicht fertig ist oder noch gebaut werden muss, entsprechend in den Plan einordnen und Schritt für Schritt umsetzen“*

**Festgehalten:**

| | |
|---|---|
| **Meine Assets** | = der **gesamte Bestand** (automatisch) + **deine Beobachtung** (manuell), aus allen Bereichen. Ersetzt die Rolle der Watchlist als Interessenliste; die Stammdaten (Preisquelle, IDs, Klasse, Schwerpunkt) bleiben daran |
| **Multi-Asset-Bestand** (Rohstoffe, ETF, Aktien) | automatische Übernahme wie bei Krypto — **noch nicht im Plan**, jetzt eingeordnet als Plan **O39** (nach dem Krypto-Spot-Bau) |
| **Spot und Hebel** | **getrennt** (zwei Stränge, T-1..T-6). Spot-Bereich = **Einstieg (Kandidaten aus dem ganzen Binance-Universum, Rolle L) + Bestand führen**, also die Kombination aus *Screener-Einstieg* und *Bestand*, die du beschreibst. Hebel-Bereich = **REGEL0 (Einstieg) + Hebelpositionen (Führung, H15)** |
| **Gleichwertigkeit** | Der Bestand wird **nicht bevorzugt**. In der alten Kette war das nur wegen Cooldown, Prüftakt und LLM-Budget nötig. Der neue Spot rechnet täglich bzw. monatlich ohne LLM über das ganze Universum, also alle **gleichwertig** |
| **Diamanten (K)** | erst, wenn K-1/K-2 einen tragenden Einstieg liefern |

**Was daraus in den Plan kommt** (Plan Hebel O39–O41; Reihenfolge Schritt für Schritt):

| # | Punkt | wann |
|---|---|---|
| O40 | **Meine Assets**: Watchlist → Stammdaten + Kennzeichen *Bestand / Hebel freigegeben / beobachtet*; Bestand automatisch (Krypto: O26); **Speicherort** der Stammdaten in die Datenbank statt `config.yaml` (eine GUI-Änderung am NB kollidiert sonst mit dem nächsten Pull) | mit GUI Stufe 2 (Tab *Assets*) |
| O41 | **Spot-Bereich** (GUI-Tab + Mail nach E-91): Bestand führen (Kern/L, Mitnahme ×3, Verkaufsanlässe, Abbau-Reihenfolge) und Einstiegs-Kandidaten (oberes Fünftel, nur bei Ampel Vorlauf/Season-Klima); Diamanten-Teil erst nach K-1/K-2 | mit dem Spot-Bau Stufe 1 (§39, Reihenfolge 1–5) |
| O39 | **Multi-Asset-Bestand** automatisch übernehmen (Rohstoffe, ETF, Aktien) | nach dem Krypto-Spot-Bau |


### G-K Abstimmung 10.10.2026 (2) — Regime, G2 im Detail, G3/G4, G6 Akkumulation

Nutzer 10.10.:
- *„was machen wir mit dem Regime-TAB – war dieser nur für Krypto? – denke einen solchen Bereich sollten wir sauber für Krypto umbauen (brauchen wir für unsere Krypto-Strategien und Regeln, Markt) und dann später für Multiassets“*
- *„G2 – ja, ist mir aber zu wenig detailliert für eine Entscheidung“*
- *„G3 – Archiv ja als vorläufiger Bereich, bis alles läuft“*
- *„G4 – ja Krypto zusammenfassen – die Aktien-, ETF- und Rohstoff-Bereiche inkl. der Thesen brauchen wir später wieder beim Multiasset-Umbau“*
- *„G6 – prüfe und gib mir konkrete Info, da ich nicht mehr unterscheiden kann, wie Akkumulation jetzt im System funktioniert (NEU) – wir haben Core-Assets BTC, ETH und SOL, taktische Assets – wie grenzen sich diese von einer noch nicht gebauten Akkumulation ab?“*

**Entschieden:**
- **G3:** Archiv (nur lesen) als vorläufiger Bereich, bis alles läuft.
- **G4:** Krypto zusammenfassen; Aktien/ETF/Rohstoffe und Thesen bleiben für den Multi-Asset-Umbau erhalten.

#### Regime-Tab — Befund am Code

- **Nur Krypto:** `agent/krypto/regime.py` rechnet einen Score aus **BTC gegen EMA50/EMA200 und Fear & Greed**, dazu Dominanz und M2-Liquidität aus `macro_snapshot`.
- **Leser:** nur die **alte** Rollen-Kette bzw. Pipeline. Die REGEL0 liest kein Regime; der Override wirkt heute auf nichts.
- **Gemessen seit dem Neubau:**
  - *Der Marktzustand ist nicht vorab erkennbar* (`btc_trend` 1,09 gegen eine Zufallsreihe 1,04; 2.599).
  - Dafür **trägt die Season-Ampel** (B1 BTC 91 T, B2 M2, B3 Stablecoins; Spot §36) für den Spot-Einstieg L.
  - Die **Dominanz-Spitze** ist ein Fakt mit Lift 1,65 (§33).
  - Das **BTC-Klima** (Überhitzung) ist für den Teilverkauf der Akkumulation offen (§10).
- ⇒ **Vorschlag:** Aus *Regime* wird **„Markt (Krypto)“**. Er zeigt die gemessenen Marktfakten, die die Krypto-Strategien wirklich nutzen, und keinen Score, der nichts steuert. Für Multi-Asset folgt später ein eigener Markt-Teil (O39).

#### G6 — wie Akkumulation heute funktioniert (am Code und in der Doku geprüft)

| | Stand |
|---|---|
| **Rollen *core/taktisch*** | Feld `rolle` in der Watchlist; gelesen **nur von den Analysten der alten Kette** (`agent/krypto/analyst.py:99`, Aktien analog) als Textregel im Prompt. Seit dem Halt (05.10.) wirkt es auf **nichts** |
| **„Akkumulation umschalten“** | Schalter `asset_dca_settings.dca_erlaubt` → `handelsauftrag.strategie_fuer` gibt der **alten Kette** die Strategie *akkumulation* (Tranchen zu 250 €). Läuft seit 05.10. **nicht**. Schon vorher: Die Akkumulationszelle fiel **immer** an `lage_gesperrt`, **null Kaufsignale** (Spot §10.2, 2.540) |
| **`agent/akkumulationslage.py`** | rechnet nur eine Lage (Abstand zum 200-Schnitt), sperrt nichts. ⚠️ Gemessen **trägt der Befund für BTC/ETH/SOL nicht** (Rang −0,025/−0,031/−0,029) |
| **Spot-Neubau E-90** | **Kern = BTC, ETH, SOL fest**: keine Mitnahme ×3, keine Abbau-Reihenfolge. Das ist nur eine **Ausnahme vom Spot**, noch keine Akkumulation |
| **gemessen für eine künftige Akkumulation** | Kaufseite: **regelmäßiges Kaufen** schlägt jede Klima-Regel nicht (F2/F3, §8.9/§8.11) → die Grundlage. **Verkaufsseite (Teilverkauf über Zyklen): ungemessen**. Gewichtung der Kernwerte, eigener Topf, deine Rolle: offen (D1–D6, §10.5) |

⇒ **Klarstellung:**
- Eine Akkumulation **gibt es im neuen System heute nicht**.
- *core/taktisch* sind **Altlast** der Rollen-Kette.
- Die Kernwerte BTC/ETH/SOL sind im Spot nur **ausgenommen**.
- Die Akkumulation ist ein eigener, **noch nicht gebauter** Strang (Richtungsentscheid: 1. Hebel, 2. Akkumulation, 3. Spot). Er startet mit den offenen Punkten D1–D6.

#### G2 im Detail — das Zielbild je Bereich

**Statusseite (über VPN, Hauptwerkzeug neben den Mails)**

| Karte | Inhalt | Quelle | heute |
|---|---|---|---|
| Betrieb | jeder Job mit letztem Lauf und Ergebnis (REGEL0-Stundenlauf, Nachlader, Bitpanda-Bestand, Hebel-Abgleich, H15, Stop-Nachzieh, Preise, Marktscan, Ankündigungen); Watchdog; letzte Fehler | `job_laeufe`, `regel0_signale.db/lauf`, Log | nur 3 Jobs |
| Hebel | offene Positionen: Kurs, Liquidation, **Abstand %**, **H15-Empfehlung**, Eigenkapital, seit; REGEL0 heute: Signale, gemailt, Prüfblock | `hebel_positions`, `hebelfuehrung.lade`, Ablage | fehlt |
| Schalter | `testwoche_freigegeben`, `spot_kette_angehalten`, `alter_hebelweg_aus`, `ankuendigung_aktiv`, `hebelfuehrung_aktiv` | `regel0_betrieb.yaml` | fehlt |
| Bestand | Gesamtwert (frei + gestakt + Fiat + Hebel-Eigenkapital), Zeitpunkt des letzten Abgleichs, Abweichungsmeldungen | holdings, meta | Teil vorhanden |
| Kontingente | CoinGecko, Gemini **je Nutzer** (REGEL0-Prüfblock, N5, Thesen-Synthese) | Zähler | falsch benannt |
| Kontrollen | offene NB-Kontrollen (K-…) als Liste | neu (Datei/Tabelle) | fehlt |
| entfällt | Rollen-Kette-Kontingent, Z.ai, *Veto-Schatten*, Regime-Karte, Parameter, Themenfelder | — | — |

**GUI (Wartung), 6 Tabs + Archiv**

| Tab | Zweck | Inhalt (Spalten / Abschnitte) | Knöpfe (Grundfunktion) | kommt aus | Bau |
|---|---|---|---|---|---|
| **1 Bestand** | was du hältst, richtig bewertet | **Spot**: Symbol, Klasse, frei, gestakt, Preis, Wert, Einstand, G/V, Rolle (Kern/L). **Hebel**: getrennte Tabelle der offenen Positionen (Verweis auf Tab 2). Summenzeile, Diversifikation, Fiat | Einstand (GF4), Bitpanda-Abgleich (GF3), Fiat-Ausnahme | Portfolio | Stufe 2 |
| **2 Hebel** | REGEL0 und Führung | **Signale**: alle REGEL0-Signale mit Filter (heute / 7 T / alle), Stufe, gemailt, Prüfblock, Ausstieg; Detail mit Mailtext. **Positionen**: Kurs, Liquidation, Abstand %, H15-Empfehlung, Finanzierung. **Freigabe je Asset**: Liste aller Krypto-Assets mit Hebel-Schalter | Hebel-Schalter (GF2, aus der Watchlist hierher), Detail | Hebel (ohne die 3 Altlisten) | Stufe 2, zuerst |
| **3 Spot** | Krypto-Spot nach E-89–E-91 | **Bestand führen**: je Coin Abstand zu ×3, Fünftel (Abbau-Reihenfolge), offene Verkaufsanlässe. **Einstiegs-Kandidaten** L: oberes Fünftel je Klasse, Bitpanda-handelbar, aktiv nur bei Ampel. **Diamanten** (K): Platzhalter bis K-1/K-2 | (keine Pflicht-Knöpfe; Handlungen kommen per Mail) | neu (ersetzt Krypto-Marktscan) | mit dem Spot-Bau Stufe 1 |
| **4 Markt (Krypto)** | Marktfakten für die Krypto-Strategien | Season-Ampel B1–B3 mit Wert, Schwelle, Stufe, Verlauf 12 Monate; Breite; Dominanz-Spitze; BTC-Klima; Fear & Greed; Liquidität und Stablecoins (alles als **Fakt**, kein Override) | — | Regime (umgebaut) | mit Spot C1 + D1 (Nachlader) |
| **5 Meine Assets** | Stammdaten und Beobachtung | alle Assets aus allen Klassen mit Kennzeichen *Bestand* (auto), *Hebel freigegeben*, *beobachtet* (manuell); Preisquelle, Bitpanda-Name, Klasse, Schwerpunkt; Chart | Hinzufügen/Bearbeiten (GF5), Bitpanda-Override (GF6), Chart (GF10) | Watchlist (ohne Akkumulation, ohne core/taktisch) | Stufe 2 (O40) |
| **6 Multi-Asset (ruht)** | für den späteren Umbau erhalten | Screener Aktien/ETF/Rohstoffe, Thesen/Schwerpunkte (Pflege bleibt) | Screener-Scan, Thesen pflegen (GF10) | Screener, Schwerpunkte | nur umgehängt |
| **Archiv** (vorläufig, nur lesen) | Nachschlagen bis alles läuft | alte Signale (Rollen-Kette), alter Regime-Stand, Krypto-Marktscan, alte Hebel-Listen | keine Analyse-Knöpfe | Signale, Regime-Alt, Marktscan, Hebel-Altlisten | Stufe 2 |

**Offene Einzelfragen zu G2:**
- (a) Soll die **Thesen-Synthese** (täglich 06:15, Gemini) bis zum Multi-Asset-Umbau **pausieren**? Sie verbraucht Kontingent, und REGEL0 und Spot lesen sie nicht.
- (b) Soll der **Marktscan-Job** (04/16 Uhr, CoinGecko) weiterlaufen, bis der Spot-Tab steht, und dann entfallen?


### G-L Abstimmung 10.10.2026 (3) — Überwachung je Bereich, zentrale Parameter, Entscheidungen

Nutzer 10.10.:
- *„Bei G2 – haben wir alles, was gemonitored werden soll je Bereich? Was ist mit zentralen Parametern und Kalibrierungseinstellungen, hatten wir besprochen?“*
- *„GUI JA – wichtig: wenn wir umbauen, prüfen, ob etwas fehlt, und Rücksprache mit mir“*
- *„2. Regime ja, vorerst Krypto – werden wir aber auch später für den Aktienmarkt benötigen“*
- *„3. ja, können wir pausieren, aber nicht vergessen und einplanen“*
- *„4. JA – ebenfalls nicht vergessen“*

**Entschieden:**
- **G2 GUI ja**, mit der stehenden Regel: Bei jedem Umbauschritt wird geprüft, **ob etwas fehlt**, mit **Rücksprache vor dem Entfernen**.
- **Markt (Krypto)** statt Regime, später auch für den **Aktienmarkt** (zu O39).
- **Thesen-Synthese pausieren** (Plan O42) und **Marktscan bis zum Spot-Tab** (Plan O43), beide eingeplant.

**Parameter — bisher besprochen?** Nur für die **alte** Kette: Parameter-Übersicht 17.07. (`agent/krypto/regelwerk_parameter.py`, Kap.-15-Kalibrierung, Regime-Tab und Remote-Karte). Für das **neue** System (REGEL0, H15, Prüfblock, Spot) **nicht** — das ist eine Lücke im Zielbild.

#### Überwachung je Bereich — Soll-Liste (was die Statusseite zeigen muss)

| Bereich | überwachen | Quelle heute | auf der Statusseite heute |
|---|---|---|---|
| **Hebel / REGEL0** | Stundenlauf (letzter, Laufzeit, frisch/veraltet, nicht im Handel), Signale heute (gemailt, gesperrt, verpasst, Korrektur), Erinnerungen fällig/entfallen | `regel0_signale.db` (lauf, signal) | ✘ |
| | Nachlader je Datei (Stand, Rückstand, Fehler), Neuaufnahme (neu, Fehler) | `_nachlader`, `_neuaufnahme` | ✘ |
| | LLM-Prüfblock: Aufrufe/Tag gegen das Limit 150, Fehler, **Zeitgrenze überschritten** (H14), Urteilsverteilung | `pruefung`, Log | ✘ |
| | Hebelpositionen + H15: Abstand %, Empfehlung, letzte Meldung; Hebel-Abgleich-Frische | `hebel_positions`, `job_laeufe hebelfuehrung:`, `hebel_abgleich.frische` | ✘ |
| | Ankündigungen O29: letzter Lauf, neue Meldungen | `ankuendigung_lauf` | ✘ |
| **Bestand** | letzter Bitpanda-Abgleich, Abweichungsmeldungen, Wallet-Salden-Fassung, Cash-Abgleich | meta, Log | teils |
| **Spot** (mit dem Bau) | Ampel-Stand und -Wechsel, Datenfrische D1 (Stablecoins, M2, BTCDOM), Umlauf, Betriebsreihen, monatlicher Rang-Lauf, ausgelöste Handlungen | neu | — |
| **Daten** | Frische je Quelle (Preise, Kerzen, Makro, Umlauf, Terminmarkt) | `agent/datenfrische.pruefe` (vorhanden) | teils |
| **Kontingente** | CoinGecko, Gemini **je Verbraucher** (Prüfblock, N5, Synthese) | Zähler | falsch benannt |
| **System** | Watchdog, letzte Fehler, Speicher, **Neustart ausstehend** (A1 aus Schritt 53) | vorhanden / A1 | teils |
| **Kontrollen** | offene NB-Kontrollen (K-…) | Memory/Doku → neu als Datei | ✘ |

⚠️ **Technischer Hinweis:** Fast alle Zahlen rechnet der **Teilexport** (`nb_teilexport_betriebsdaten.py`) heute schon. Die Statusseite soll **dieselben Funktionen** nutzen, nicht nachbauen (eine Quelle, sonst laufen beide auseinander).

#### Zentrale Parameter und Kalibrierung — Vorschlag

| Gruppe | Parameter | steht in | Art |
|---|---|---|---|
| REGEL0 Modell | Modellmonat, Prüfsumme, Trainingszeitpunkt, nächstes Training | `data/regel0_modelle/` | gemessen (Training) |
| REGEL0 Regel | Schwelle 0,035, Ruhe 48 h, Halten 72 h, Erstes Ereignis ±5 %, Regelversion REGEL0.1 | `agent/regel0_rechnung.py` (Code-Konstanten) | **gemessen**: nur per Messung ändern (Regel *Schwelle ist Messung*) |
| REGEL0 Größe | Positionswert 1.500 €, Einsatz 300–800 €, Richtwert 4 gleichzeitig, Sperre ab Richtwert | `regel0_betrieb.yaml` | **deine Wahl** |
| Schalter | alter Hebelweg aus, Testwoche, Kette angehalten, Ankündigungen, Hebelführung | `regel0_betrieb.yaml` | **deine Wahl** |
| H15 | Warnschwelle 15 %, Stufen 15/10/5, Liquidationsmarge 0,09 (⚠️ an **zwei** Stellen gepflegt) | yaml / Code / `config.yaml` | Wahl / Schätzung |
| LLM-Prüfblock | Fassung 0.2, Modell, 5 Stimmen, Zeitgrenze 120 s, Tageslimit 150, Rollen an/aus | `regel0_llm.yaml` | Wahl, gemessen in N4/N5 |
| Spot (mit dem Bau) | Kosten je Klasse, Ampel-Schwellen B1–B3, Mitnahme ×3, Fenster 365 T, Fünftel | künftig eine Datei | gemessen (§31, §36) |
| Messstandard | Nullpunkt, Trennschärfe, Leiter | `messnorm.standardzeile()` | gemessen (08.09.) |

**Vorschlag:**
- Eine **Parameter-Karte** auf der Statusseite und ein **Teil im GUI-Tab „Betrieb/Parameter“**, beide **nur lesend**.
- Je Parameter: Wert, Datei, **Art** (*deine Wahl* / *gemessen* / *Schätzung*), *gemessen am*, Befund.
- **Geändert wird nur über die Datei** (Commit + Pull): *deine Wahl* jederzeit, *gemessen* nur nach einer neuen Messung.
- Ein Änderungsknopf in der GUI würde gemessene Werte zur Stellschraube machen. Dazu kommt die Pull-Kollision am NB.
- ⚠️ **Nebenbefund:** Die Liquidationsmarge 0,09 steht doppelt (`config.yaml:506` und `entscheidungsrechnung.GRENZEN`). Sie wird auf **eine** Quelle zusammengeführt (Plan O44).

### G-M Entschieden 10.10.2026 (4) und Einordnung in den Gesamtplan

Nutzer 10.10.: *„1. ja 2. passt 3. ja, mit Statusseite starten – prüfe vorher, ob der Bau in unserem Gesamtplan passt …“*

- **Parameter-Karte nur lesend**; geändert wird nur über die Datei, gemessene Werte nur nach einer Messung (G-L).
- **Überwachungsliste G-L passt.**
- **Reihenfolge:** GUI-1 Statusseite → GUI-2 Hebel-Tab → GUI-3 Bestand → GUI-4 Meine Assets → GUI-5 Archiv/Multi-Asset. Verschränkt mit Hebel und Spot im **Paketplan ab 10.10.** (Plan_Hebel_fuenf_Phasen_27_09.md, P8–P20): O29 zuerst, dann die Statusseite.


### G-N Voranalyse P9 — GUI-1 Statusseite (10.10.2026)

**Ist am Code:**
- `remote/status.py` (1.220 Z.) baut `RemoteStatus` aus rund 40 Gettern, zwischengespeichert 900 s (`_gecacht`). Warnung, wenn der Aufbau > 1,0 s dauert.
- `remote/server.py` (1.114 Z.): Flask, eine HTML-Seite mit JS, Abruf `/api/status` alle **5 s**, Knöpfe über `/api/*` mit Zugangs-Token.
- Der Teilexport `nb_teilexport_betriebsdaten.py` rechnet alles **inline** in `_inhalt()` (≈ 330 Zeilen mit `print`). Es gibt **keine** Funktionen zum Mitnutzen.
- `hebelfuehrung.lade(conn)` ist rein lesend (Positionen + `price_cache`) und für die Seite geeignet.
- Liquidationsmarge: `entscheidungsrechnung.GRENZEN["liquidations_marge"]` = 0,09 (H15, Rollen-Kette) **und** `config.yaml risiko.hebel.liquidations_sicherheitsmarge_relativ` = 0,09 (`hebel_risk_gate`, Liq.-Preis-Tabelle). Heute gleich, aber doppelt gepflegt.

**Bauweise (Vorschlag):**

| Teil | Inhalt | Schutz |
|---|---|---|
| neu `agent/betriebslage.py` | **eine** Quelle für die Lage: `regel0()`, `hebel()`, `schalter()`, `jobs()`, `bestand()`, `kontrollen()`, `parameter()`, `daten()` (ruft `datenfrische.pruefe`); andere Dateien nur `mode=ro` | nur lesend; Prüfstand auf einer Kopie der Prod-Sicherung |
| `remote/status.py` | neue Felder je Karte, Getter mit `_gecacht` (Laufzeit < 1 s bleibt) | Wache `build_status` vorhanden |
| `remote/server.py` | neue Karten: Betrieb, Hebel, Schalter, Bestand, Kontingente je Verbraucher, Kontrollen, Parameter | Flask-Testclient |
| Teilexport | ruft `betriebslage` statt inline | **Ausgabe vorher/nachher zeilengleich** auf derselben Kopie (der Teilexport ist dein Instrument und darf sich nicht still ändern) |
| O44 | `GRENZEN["liquidations_marge"]` liest den Wert aus `config.yaml` (eine Quelle) | Wert bleibt 0,09; H15-Prüfstand und Gegenprobe unverändert grün |
| Kontrollen | neue Datei `Basisinfos/nb_kontrollen.yaml` (offene K-…, Stand, Nachweis), gepflegt von mir mit jedem Befund; die Seite liest sie | heute stehen sie nur im Memory/Doku |

**Karten, die entfallen oder umziehen** (⚠️ **Rücksprache vor dem Entfernen**):

| heute | Vorschlag |
|---|---|
| LLM-Kontingent *Rollen-Kette* (Urteile heute = 0) | **ersetzen** durch *Kontingente je Verbraucher* |
| *Alte Kette* (Budget heute) | entfällt (Kette angehalten) |
| A *„Ausgeführte Empfehlungen“* (nur Marktscan-Quote) | Marktscan-Quote in *Betrieb*; Überschrift entfällt |
| B *„Z.ai“* (leer) | entfällt |
| C *„Veto-Schatten“* (enthält *Stop nachziehen*) | *Stop nachziehen* in *Betrieb* (letzter Lauf, Anzahl); Überschrift entfällt |
| Regime-Karte, Parameter (alt) | entfällt; ersetzt durch *Parameter* (neu) bzw. später *Markt (Krypto)* |
| Themenfelder, wartende Themen, Absicherung | in einen eingeklappten Abschnitt *Multi-Asset (ruht)* |
| Z-3 | **unklar**, wer es heute schreibt → vor dem Bau prüfen, dann Rücksprache |
| Portfolio, Preise, CoinGecko, Gemini, API-Status, Knöpfe, Fehler | **bleiben** (GF1) |

**Nachweis (vorab):**
- Prüfstand auf einer Kopie der neuesten Prod-Sicherung: jede Karte gefüllt, Werte gegen eigenes SQL (Gegenprobe), Aufbau < 1 s, Standard-DB per Prüfsumme unberührt.
- Teilexport zeilengleich vorher/nachher.
- Paket `GuiKette` erweitert, ganze Suite.
- Am NB: Pull + Neustart, **K-ST-1** = du siehst alle Karten über VPN, nichts fehlt.


### G-O Kontrollen-Datei, die nie veraltet (10.10.2026; Teil von P9)

Nutzer 10.10.: *„3. ja – so aufsetzen, dass es nie veraltet“*.

**Befund heute:**
- Die NB-Kontrollen stehen im Memory `project_ausstehende_nb_kontrollen.md`, einer Liste, die **nur nach unten wächst**: rund 20 Kennungen seit 15.09. (K1–K8, K-ALARM-2, K-S7-3/4/5, K-SN-2, K-LLM-1, K-MISFIRE-2, K-PRUEF-1, K-BP-1/2/3, K-ANK-1 …).
- Welche noch offen ist, steht nirgends an **einer** Stelle. Der Index nennt *„OFFEN K-S7-3, K-S7-4, K-ALARM-2“*, die Einträge darunter sind teils neuer.
- ⇒ Das ist genau die Art, wie eine Liste veraltet.

**Aufbau `Basisinfos/nb_kontrollen.yaml`** (eine Zeile je Kontrolle):

| Feld | Inhalt |
|---|---|
| `id`, `titel` | z. B. `K-ANK-1`, *„O29: Abrufe laufen, Mailzeile bei Meldung“* |
| `seit`, `paket`, `commit` | woher sie kommt (P8, `3a133e8` …) |
| `art` | **automatisch** (das System prüft selbst) oder **manuell** (Nachweis im Export) |
| `pruefung` | bei *automatisch*: Name einer Prüffunktion in `agent/betriebslage.KONTROLLEN` |
| `nachweis` | bei *manuell*: was im Export zu sehen sein muss |
| `faellig_bis` | Datum, bis wann sie erledigt sein muss |
| `status`, `erfuellt_am`, `beleg` | *offen* / *erfüllt* / *entfallen*, mit Fundstelle |

**Vier Sicherungen gegen das Veralten:**
1. **Automatische Kontrollen prüfen sich selbst:** Am NB wertet `betriebslage.kontrollen()` sie live aus. Beispiele:
   - K-ANK-1 = `ankuendigung_lauf` mit Läufen ohne Fehler;
   - K-BP-3 = Marke *Wallet-Salden Fassung 2* gesetzt und seither keine Mismatch-Meldung.
   - Die Statusseite zeigt *„erfüllt (automatisch, Zeitpunkt)“*, ohne dass jemand die Datei anfasst.
2. **Fälligkeit:** Eine manuelle Kontrolle über `faellig_bis` steht **rot** auf der Statusseite **und** macht die Suite rot. Sie zwingt mich zur Pflege.
3. **Kein Betriebs-Push ohne Kontrolle:** Eine Suite-Prüfung verlangt, dass der jüngste Commit, der Betriebscode ändert (`agent/`, `scheduler/`, `importer/`, `remote/`, `ui/`, `database/`, `Basisinfos/regel0_*.yaml`), in einer Kontrolle steht.
4. **Eine Quelle:**
   - Das Memory verweist nur noch auf die Datei, statt die Liste zu führen.
   - Teilexport und Statusseite zeigen denselben Abschnitt.
   - Erledigte bleiben als Historie (*erfüllt*) und werden nicht gelöscht.

**Übernahme des Altbestands:**
- Jede Kennung aus dem Memory bekommt einen Status mit Beleg.
- Was sich nicht mehr belegen lässt, kommt als Liste zur **Rücksprache**; nichts wird still abgehakt.


### G-P P9 gebaut — Statusseite mit der Betriebslage (10.10.2026)

Nutzer 10.10.: *„Pull am NB erledigt – P9 Statusseite starten“*. Umgesetzt nach G-N/G-O; Abweichungen vom Vorschlag stehen unten und sind begründet.

**Was gebaut ist:**

| Teil | Inhalt |
|---|---|
| `agent/betriebslage.py` | **eine** Quelle für Statusseite und Teilexport, nur lesend (`mode=ro`). Neu dazu `nachlader_kurz()` (nur der letzte Lauf je Datei, ohne `GROUP BY symbol` über die Kursreihe) |
| `remote/status.py` | acht neue Felder (`betrieb`, `hebel_lage`, `regel0_lage`, `schalter`, `bestand_lage`, `kontingente`, `kontrollen`, `parameter_neu`); Dekorator `_gecacht_frist(s)` mit **eigener Frist an der Funktion**: 60 s Jobs/Hebel/Schalter/Kontingente, 120 s REGEL0/Bestand, 300 s Kontrollen, 900 s Parameter und Neuaufnahme |
| `remote/server.py` | neue Karten: Offene NB-Kontrollen · Hebel (H15 je Position: Kurs, Liq., Abstand, Empfehlung, Warnstufe, Grund; zuletzt gemeldet) · REGEL0 heute (Signale, Mails, letzter Lauf, Prüfblock, Ankündigungen) · Betrieb (auffällige Jobs offen, alle eingeklappt; Nachlader je Datei; Neuaufnahme; Marktscan-Quote; Stop nachziehen) · Schalter + Bestand · Kontingente je Verbraucher · Parameter (neu) |
| Teilexport | ruft `betriebslage` (zeilengleich nachgewiesen), neu der Abschnitt **NB-KONTROLLEN** |
| O44 | `GRENZEN["liquidations_marge"]` liest `config.yaml risiko.hebel.liquidations_sicherheitsmarge_relativ`; fehlt der Eintrag: 0,09 **mit Warnung** im Log |
| Kontrollen | `Basisinfos/nb_kontrollen.yaml` + Suite-Paket **Kontrollen** (Frist, Datei nicht älter als der jüngste Betriebs-Commit, Felder, Commits, eine Quelle) |

**Entfallen / umgehängt** (wie abgestimmt): Karte *ALTE KETTE* · Überschriften A/B/C · Regime-Karte · Parameter (alte Kette). Marktscan-Quote und Stop nachziehen → *Betrieb*. Themenfelder, wartende Themen, Absicherung → eingeklappter Abschnitt **Multi-Asset (ruht)**. Die Getter bleiben im Code; `budget_heute`, `regime_status`, `parameter_overview` werden nicht mehr gerechnet (Felder bleiben deklariert, `None`).

**Z-3 geprüft, bleibt:** geschrieben vom Job `portfolio_wert` täglich 04:30 (zuletzt 10.10.), mailt bei Rückschlag ≥ `ziele.max_drawdown_prozent`, unabhängig von jeder Kette ⇒ Grundfunktion, **keine** Entfernung, daher keine Rücksprache nötig. Neu direkt unter dem Portfolio-Wert (dieselbe Gegenprobe Kursreihe ↔ Snapshot).

**Abweichungen vom Vorschlag (begründet):**
- *Rollen-Kontingent ersetzen:* die Rollen-Kette bleibt als **ein Verbraucher** in *Kontingente je Verbraucher* (nächster Topf, Urteile heute) — sie ist angehalten, aber ihr Topf ist dieselbe Gemini-Grenze. Die vier Topf-Zeilen sind entfallen (stehen je Modell in der Gemini-Karte).
- *Z.ai-Gegenprüfung heute* entfällt mit der Alte-Kette-Karte (kam aus `budget_heute`).
- *Stop nachziehen in Betrieb (letzter Lauf, Anzahl):* Kopfzeile *„N von M · Lauf vor X“*, die 50-Zeilen-Liste eingeklappt.
- *Jobs:* am Handy 26 Zeilen → nur die über 26 h offen, die ganze Liste eingeklappt. Klappabschnitte stehen **fest im HTML** — im erzeugten Teil klappten sie bei jedem Abruf (5 s) wieder zu.
- *Schalter:* rechts der **Zustand** (*„alter Hebelweg: aus“*), nicht der Rohwert — *„alter_hebelweg_aus: an“* las sich als das Gegenteil.

**Befunde beim Bau:**
- `job_laeufe` gibt es nur, wo die App läuft (NB ja, Desktop nein). Die Karte meldet das jetzt, statt auszufallen (gefunden von der neuen Suite-Prüfung).
- SQLite legt beim **Lesen** einer WAL-Datenbank ein leeres `-wal` (0 Byte) und `-shm` an. Kein Schreibzugriff; die Suite prüft jetzt *Hauptdatei gleich, Journal ohne neue Daten*.
- `h15_gegenprobe.py` G6 fror den **Ort** der SQL-Zeile ein (Teilexport) — prüft jetzt die Regel (Abschnitt ruft die Quelle, beide lesen nur).
- Kalter Aufbau 1,9 s am Desktop = Erst-Importe (`regel0_rechnung` 0,73 s; am NB lädt sie der stündliche REGEL0-Job ohnehin, neu nur `messnorm` ≈ 0,1 s). Warm **0,27 s**.

**Nachweis (auf der NB-Kopie vom 10.10. 05:14, nie an der Produktion):**
- `p9_pruefstand.py` **6/6** (alle 8 Karten gefüllt, warm 0,28 s, Flask 200/200/401/401, Entfallenes weg, Prüfsumme Kopie **und** Desktop-DB gleich, Grundfunktionen da).
- `p9_gegenprobe.py` **10/10** (jede Zahl mit eigenem SQL).
- Automatische Kontrollen an einer Wegwerfkopie: beide Bedingungen hergestellt → *erfüllt (automatisch)*; ein Fehlerlauf → K-ANK-1 wieder offen.
- Teilexport zeilengleich (NB-Kopie 253 → +10 Zeilen NB-KONTROLLEN, Desktop 356 → +10).
- Handyansicht 375 px ohne Querlauf (Bildschirmfotos). Paket GuiKette 36/36, Kontrollen 12/12, H15 11/11 + 7/7, Sofortliste 9/9 + 5/5, `teste_status_cache.py` grün.

**Am NB offen:** **K-ST-1** — du siehst die Seite über VPN, alle Karten gefüllt, nichts fehlt; Teilexport mit NB-KONTROLLEN.


### G-Q P9b — Laufzeit der Statusseite (10.10.2026)

Nutzer 10.10.: *„Alle Karten gefüllt, nichts fehlt – Folgeschritt Laufzeit vorlegen“*, dann *„Ja, P9b bauen, prüfen und gegenprüfen“*. **K-ST-1 erfüllt.**

**Anlass:** Seit dem Neustart mit P9 (16:36) meldete das NB 192-mal *„Statusaufbau dauerte > 1 s“* (Median 1,12 s). Gemessen an der Prod-Kopie (713 MB): die warme Zeit lag zu fast 100 % in drei **alten** Live-Abfragen, nicht in den neuen Karten.

| Abfrage | vorher | Ursache | jetzt |
|---|---|---|---|
| `db.get_latest_prices` (Grundfunktion, 17 Aufrufer) | 0,084 s | `GROUP BY symbol` über alle 428.505 Zeilen von `price_cache` | Sprung über den Primärschlüssel (rekursiv, je Symbol das jüngste): **0,0003 s**, **bitgleich** |
| Marktscan-Karte `_get_marktscan_last` | 0,118 s | lud 500 Kandidaten als Objekte | zwei gezielte Abfragen auf den jüngsten Lauf: 0,015 s; bleibt live |
| Rollen-Kontingent `_get_rollen_budget` | 0,07 s | `signals` zweimal ohne passenden Index | Frist **60 s** statt live (Kette seit 05.10. angehalten) |

**Warmer Aufbau am Desktop: 0,29 → 0,02 s** (am NB erwartet ≈ 0,1 s). Kein Index, keine Frist auf die Preise (bleiben live, auch nach *„Preise aktualisieren“*).

**Nachweis:** `p9b_gegenprobe.py` **7/7** (Preise alt = neu auf der Kopie und an Randfällen; Marktscan alt = neu, ein Lauf > 500 Kandidaten wird jetzt vollständig gezählt statt abgeschnitten; Laufzeit; Frist; Prüfsumme der Kopie gleich). ⚠️ B6 (Rollen-Kontingent) prüft nur 0 = 0 — die Kette urteilt heute nicht. Dauerhafte Wache in Paket GuiKette (Preise **bitgleich** zur alten Abfrage auf der Desktop-DB). p9_pruefstand 6/6, p9_gegenprobe 10/10, H15 11/11 + 7/7, Sofortliste 9/9 + 5/5, `teste_status_cache.py` grün.

**Am NB:** Pull + Neustart → **K-ST-2** (Diagnose: höchstens die erste Warnung nach dem Start, danach keine; Hebelführung-Logzeile wie vorher).


### G-R P9c — Fristen nach der Datenänderung (11.10.2026)

Nutzer 11.10.: *„Ja, P9c bauen, prüfen und gegenprüfen“*.

**Befund K-ST-2** (Diagnose 11.10. 06:06, Neustart 05:32 mit P9b): **9 Warnungen in 34 min** statt 194 in 3 h bzw. 398 in 10 h vorher. Sie fallen in drei Gruppen:
- 1 beim Start;
- 5 an Job-Zeitpunkten (Preis-Refresh :47/:02, Nachlader :04; 3,8–5,9 s, CPU-Konkurrenz wie am 14.08.);
- **3 im Minutentakt** (05:33–05:36, 1,2–1,4 s), verursacht durch **meine** 60-s-Fristen.

Betrieb ohne ERROR, H15 unverändert. K-ST-2 ist abgelöst durch K-ST-3.

**Änderung:** Die Frist richtet sich nach der Änderung der Daten.

| Karte | vorher | jetzt | Begründung |
|---|---|---|---|
| Hebel (H15 je Position) | 60 s | **300 s** | Kurs und H15 ändern sich nur alle 15 min (Preis-Refresh, Hebel-Screening) |
| Kontingente je Verbraucher | 60 s | **300 s** | Prüfblock-Aufrufe nur mit einem Signal; der Live-Zähler je Gemini-Modell bleibt in seiner Karte |
| Rollen-Kontingent | 60 s | **300 s** | Kette angehalten |
| Betrieb (Jobs), Schalter | 60 s | 60 s | billig (0,005 s) |

**Preis:** Die Hebelkarte liegt höchstens 5 min hinter dem neuesten Kurs. Die Aufzinsung der Liquidation in 5 min beträgt ETH 0,02 €, BTC 0,54 €. Die H15-Mail kommt unverändert sofort.

**Nachweis** (`p9c_gegenprobe.py` **4/4**):
- Fristen wie festgelegt;
- Werte aus dem Speicher = frisch gerechnet. ⚠️ Die Hebelkarte ist zeitabhängig (Aufzinsung, 9. Nachkommastelle), deshalb ist sie gleich bis auf diese Aufzinsung, und die ist beziffert;
- Neuberechnung je Minute 0,143 → **0,005 s** (Desktop);
- nach 301 s wird wieder neu gerechnet.

Dazu: p9_pruefstand 6/6, p9_gegenprobe 10/10, p9b_gegenprobe 7/7, GuiKette 39/39, Kontrollen 12/12, Hebelführung 35/35, `teste_status_cache.py` grün.

**Am NB:** Pull + Neustart → **K-ST-3**. Warnungen nur noch beim Start und zu den Job-Zeitpunkten.


### G-S P10 — Thesen pausiert (O42, 11.10.2026)

Nutzer 11.10.: *„Ja, P10 mit beiden Jobs bauen, prüfen und gegenprüfen – wichtig beim Umbau der jeweiligen Bereiche dies berücksichtigen“*.

**Ist (Code und NB-Daten):**
- `kategorie_synthese` (Gemini 3.1, 1 Aufruf je Lauf) und `kategorie_vorschlaege` (ohne Sprachmodell; legt nach 7/14/30 Tagen selbst Thesen an) laufen um 06:15 und 06:30 **und bei jedem Start**. Am 10.10. waren das 6 Läufe zu je 3–4 min.
- Jeder Lauf holt Daten aus FRED, CFTC, yfinance, EIA, Finnhub, SEC und FINRA.
- REGEL0, H15 und die Spot-/Rollen-Kette lesen davon **nichts**.
- Bisher 6 Thesen automatisch angelegt (zuletzt 23.08.), 5 Kandidaten in Beobachtung.
- ⚠️ **Korrektur zum Plan:** Die Synthese zieht **nicht** am Topf des Prüfblocks (Gemini 3.5); gemeinsam sind nur Schlüssel und Minutendrossel.

**Gebaut:**
- Schalter `thesen_pausiert: true` in `Basisinfos/regel0_betrieb.yaml`, je Lauf gelesen. Vorgabe im Code: läuft wie bisher.
- **Beide** Jobs prüfen ihn vor jeder Verbindung und jedem Client und enden mit der Logzeile *„Thesen pausiert (O42 …)“*.
- Statusseite: Schalterkarte *„Thesen (Multi-Asset, O42): pausiert“*, Abschnitt *Multi-Asset (ruht)* mit *„Stand eingefroren“*.
- Thesen, Vorschläge und Ergebnisse bleiben stehen; der Tab Schwerpunkte zeigt den letzten Stand; die manuelle Pflege bleibt.

**⚠️ Für O39 – beim Umbau JEDES Multi-Asset-Bereichs** (Nutzervorgabe 11.10.):
- Den Schalter mitbedenken.
- **Vor dem Wiedereinschalten die Kandidaten prüfen.** Die Beobachtungstage sind Datumsdifferenzen und laufen in der Pause weiter. Der erste Lauf danach könnte sofort Thesen anlegen (Fall A) oder Vorschläge auf *offen* heben (Fall B).
- Die Karte *Themen in Beobachtung* zählt die Tage auch während der Pause herunter.

**Nachweis:**
- `p10_pruefstand.py` **6/6**, ohne Netz, LLM und Datenbank:
  - Schalter an → 0 Verbindungen, 0 Abgleiche, 0 LLM;
  - aus und fehlend → wie vor P10;
  - falscher Typ → läuft weiter, `lade()` bricht laut ab;
  - echte Datei: alle Leser laufen;
  - Wache auf die Gemini-Zeile unverändert.
- Weiter: p9-Prüfstand und -Gegenprobe, H15, Pakete Regel0Betrieb, GuiKette, Kontrollen und Hebelführung, die ganze Suite.

**Am NB:** nur Pull (je Lauf gelesen). **K-TH-1.**


### G-T Voranalyse P11 (Hebel Schritt B, O36) und O45 (Wochen-MACD/RSI), 11.10.2026

Nutzer 11.10.: *„Ja, beide Voranalysen parallel vorbereiten und vorlegen“*. Je ein Code-Bericht, dazu von mir an den Daten gegengeprüft.

**P11 – Ist:**
- Kein Code vergleicht heute die Bitpanda-Hebel-Wallets mit `hebel_positions`.
- Die Daten liegen aber vor, offline:
  - `bitpanda_wallet_saldo` (`margin-trading` je Asset, `margin-trading-credit` auf EURCV) aus dem Bestands-Job, alle 30 min;
  - `hebel_positions.positionsmenge` und `kreditbetrag_eur` aus dem Hebel-Sync, alle 15 min, alte API;
  - `bitpanda_katalog` (ID → Symbol).
- **Gegengeprüft an der Prod-Kopie 10.10.:** BTC 0,02038541 = 0,02038541 · ETH 0,89636371 = 0,89636371 · Kredit −2.600 = 1.000 + 1.600. Heute stimmig, weil keine Teilschließung.
- Der Importer-Fehler (2.679) sitzt in `importer/bitpanda_margin_positions.py:226–253`:
  - Vollschluss-Bedingungen, darunter `sell_value >= 99,5 % Kredit`;
  - Teilschluss kürzt Wert und Kredit anteilig, die Menge nur um `sell_qty`;
  - nach einem falschen Vollschluss gehen Restmenge und Restkredit verloren.
  - Er **schreibt** in die Produktion (`upsert_hebel_position`).
- Richtiges Buch je Symbol: `messe_k7_abgleich.abschnitte()`.

**P11 – Vorschlag (nur lesend, bündelbar):**
- Wache `agent/hebel_wallet_abgleich.py` im Hebel-Screening-Job nach dem Sync:
  - je Symbol Wallet-Menge gegen die Summe der offenen `positionsmenge`;
  - Kredit-Wallet gegen die Summe `kreditbetrag_eur`;
  - erfasst auch *Wallet > 0 ohne Position* und *Position ohne Wallet*.
- **Zeitversatz:** Gemeldet wird erst, wenn die Abweichung **zwei Läufe hintereinander** besteht (≥ 30 min).
- **Ausgabe:**
  - Logzeile je Lauf;
  - Mail *„Hebelposition passt nicht zu Bitpanda: …“* mit 6 h Sperrfrist (Muster der Spot-Meldung);
  - Zeile in der Hebelkarte der Statusseite und im Teilexport.
- **Der Importer-Fix** ist ein Schreiber in die Produktion → eigenes Paket **P11b**, allein, erst wenn die Wache einen echten Fall zeigt oder du teilweise schließt.

**O45 – Ist:**
- Heute geht nur **eine** Signalmail raus: REGEL0 (`agent/regel0_mail.py`).
- Dazu die H15-Führungsmail. Spot-Mails der Rollen-Kette sind angehalten.
- `indicators/calculations.py` hat `macd` (mind. 35 Werte) und `rsi` (mind. 15); eine Wochenaggregation fehlt noch.
- Einhängen wie O29: als Zutat `f(r)` in `versende(...)`, scheitert ohne die Mail aufzuhalten (P-8).
- **Gegengeprüft (Desktop-Daten 01.10.):**
  - Alle **26** Assets mit Hebel-Schalter an haben ≥ 48 volle Wochen in `stundenkurse(_alle).db` (Median ≈ 150).
  - MACD und RSI sind für alle rechenbar, 0,03 s je Asset.
  - 93 der 537 Assets im Zusatzuniversum haben < 15 Wochen (meist tokenisierte Aktien „…B“, O38) → *„zu kurz“*.

**O45 – Vorschlag:**
- Woche Mo 00:00 bis So 24:00 UTC (wie Binance), **nur abgeschlossene Wochen**.
- Anzeige als **Zustand statt Rohzahl**: *„Wochenchart: MACD über Signal seit 2 Wochen, Abstand wächst · RSI 58,7 (neutral)“*.
  - Die MACD-Rohwerte hängen an der Preisskala, z. B. 1000CAT mit Faktor 1000; der Zustand ist skalenfrei.
- **Ort:** Abschnitt 3 *Einschätzung*, eine Zeile; die Zahlen dazu in Abschnitt 5 *Technik*.
- **Mails:**
  - jetzt die REGEL0-Signalmail und die H15-Führungsmail (Bitpanda-Symbol über `symbol_zuordnung.csv` zurückübersetzt);
  - Spot-Mails mit ihrem Bau (P14 ff.);
  - Korrektur und Erinnerung nicht (sie verweisen auf die Signalmail).
- **Kein Auslöser** (Regel 4, E-91): Die Zeile ändert weder Signal noch Stufe noch Versand.
- Suite: Regel0Betrieb (Mailtext, Tab-Detail = Mailanfang), `pruefe_o25.py`; Mail-Prüfstand mit echter `config.yaml`, LONG/Text/HTML.

**Bündel (E-97):**
- P11 ist nur lesend, mit eigener Logzeile und Mail → bündelbar.
- ⚠️ O45 verändert den Inhalt der Signalmail und ist nach E-97 ein **Grenzfall**. Additiv und fehlertolerant, eigene Kennzeile → Bündel vorgeschlagen, **Entscheidung beim Nutzer**.

### G-U Bündel P11 + O45 gebaut (11.10.2026)

Nutzer 11.10.: *„ja Bündelung ist ok – nur Hinweis zu RSI und MACD – das sollen schon Charts sein und nicht nur … Durchschnittswerte“*, Auswahl **Woche + Tag**; *„ja wie immer prüfen und gegenprüfen“*.

**P11 – Hebel-Wallet-Abgleich (O36 Schritt B), nur lesend:**
- `agent/hebel_wallet_abgleich.py` (`pruefe`, `zeile`, `bestaetigt`, `mail`).
  - Je Symbol wird `margin-trading` mit der Summe der offenen `positionsmenge` verglichen, der Kredit `margin-trading-credit` mit der Summe `kreditbetrag_eur`.
  - Fälle: *Menge weicht ab*, *Wallet ohne Position*, *Position ohne Wallet*, *positionsmenge fehlt*.
- `_hebel_wallet_lauf` im Hebel-Job, nach `_pruefe_hebel_abgleich` und vor H15.
  - Je Lauf eine Logzeile.
  - Mail erst nach **zwei Läufen in Folge**, Sperre 6 h je Abweichung (meta `hebel_wallet:*`), nur am Betriebsgerät.
- Statusseite und Teilexport lesen über `betriebslage.hebel_wallet_abgleich`:
  - Hebelkarte: *„Abgleich mit Bitpanda: stimmt / WEICHT AB“*;
  - Teilexport: Zeile *HEBEL-WALLET-ABGLEICH (P11)*.
- Der Importer-Fix bleibt **P11b** (Schreiber, allein).

**O45 – Wochen- und Tageschart mit RSI 14 und MACD 12/26/9:**
- `agent/indikator_chart.py` baut Kerzen aus den REGEL0-Stundenkursen.
  - **Nur abgeschlossene Kerzen**, nach der Uhr und mit mindestens 90 % der Stunden.
  - Die Woche beginnt Mo 00:00 UTC (`W-MON`, closed=left).
  - Gezeigt werden 104 Wochen bzw. 180 Tage; gerechnet wird über die ganze Reihe.
- Umrechnung in EUR:
  - REGEL0 über `eur_je_usd`, H15 über H15-Kurs ÷ Binance-Schluss. Damit ist der Faktor bei 1000CAT erfasst.
  - Ist die Reihe zu kurz, steht im Bild *„zu kurz“*.
- **REGEL0-Signalmail:** zwei weitere Bilder unter *2 · Chart* (`versende(zusatzbilder=…)`).
  - Der Text bleibt unverändert.
  - Ein Fehler lässt die Mail mit dem Signalbild durch (P-8).
- **H15-Mail:** zwei Bilder je gemeldeter Position, Logzeile *Charts n*. Die Prüfstände mit `(betreff, text)` bleiben gültig.
- Die Charts sind Kontext, **kein Auslöser** (Regel 4, E-91).
- **Gefunden in der Gegenprobe:** Das pauschale Weglassen der letzten Kerze verlor bei vorzeitig endender Reihe eine volle Woche. Jetzt entscheidet die Uhr.

**Nachweis:**
- `p11_o45_pruefstand.py` **10/10**:
  - Kopie stimmt;
  - fünf gestellte Abweichungen;
  - Zeitversatz;
  - Job-Lauf mit Sperre;
  - Mailtext;
  - Signalmail mit 3 Bildern, Text gleich;
  - P-8;
  - H15-Mail mit Bildern an einer Wegwerfkopie;
  - alte Signatur;
  - Prüfsumme.
- `p11_o45_gegenprobe.py` **4/4**:
  - eigenes SQL;
  - Kerzen von Hand über ISO-Woche bzw. UTC-Datum: 249 Wochen und 1.750 Tage gleich;
  - RSI und MACD in reinem Python.
- Suite Regel0Betrieb 85/85 mit neuen Wachen. Alle Prüfstände P9, P10, H15, O29 und Sofortliste grün.

**Am NB:** Pull + Neustart → **K-HW-1** (Diagnose), **K-WC-1** (nächste Signal- bzw. H15-Mail).


### G-V Voranalyse P12 — GUI-2 Hebel-Tab (11.10.2026)

Nutzer 11.10.: *„Pull und Neustart am NB erledigt, Export kommt später“* → Voranalyse P12 laut Paketplan. Code-Bericht, von mir am Code und an der Prod-Kopie gegengeprüft.

**Ist `ui/hebel_view.py` (1.197 Zeilen):**
- **Ein** Treeview mischt vier Quellen:
  - A `hebel_signals` (alte Kette, letztes 10.08.);
  - B Hebel-Urteile der Rollen-Kette (letztes 27.09., seit E-46 aus);
  - C Kandidaten `hebel_triggers` (Screening aus);
  - REGEL0 (`agent/regel0_ansicht.py`), **nur das jüngste Signal je Asset**, Filter nur *2 Tage / alle*.
- Darunter die offenen Positionen: Hebel, Eigenkapital, Eröffnung, geschätzte Liquidation, REGEL0-Vermerk.
  - **Ohne** Kurs, Abstand, H15-Empfehlung, Finanzierung und Wallet-Abgleich.
- Die Knöpfe *Jetzt analysieren* (alte Pipeline, gesperrt) und *Signal-Historie* (`hebel_signals`) gehören zur alten Kette.
- Der Tab wird **alle 3 s** neu gelesen (`app._poll_prices`).
- Der **Hebel-Schalter** liegt in der Watchlist (`ui/app.py:405`, `_toggle_hebel_pruefung_erlaubt` :960 → `db.set_hebel_pruefung_erlaubt`).
  - REGEL0 schreibt ihn je Signal in die Ablage (`regel0_stundenlauf._hebel_schalter`).
  - Gemailt wird nur mit `hebel_schalter=1`.
  - Stand: 26 von 44 an.
- **Kein Job und kein Mailweg importiert `ui/hebel_view.py`** (GF11). Einziger fremder Nutzer ist `pruefe_h17.py`.
- Sieben Suite-Prüfungen lesen Textstellen in `hebel_view.py` (Pakete 15, Dimension, Altbestand, GuiKette, Regel0Betrieb).

**Vorschlag: neuer Tab `ui/hebel_tab.py`; `hebel_view.py` bleibt unverändert** (Suite-Textprüfungen und `pruefe_h17` bleiben gültig).

| Bereich | Inhalt | Quelle |
|---|---|---|
| **Signale (REGEL0)** | **alle** Signale; Filter *heute / 7 Tage / alle* und *nur Schalter an / alle*. Spalten: Asset, Signalstunde (Ortszeit), Stufe (vorläufig/endgültig), Status, gemailt, Trader-Urteil, Ausstieg. Detail = Mailtext + Prüfblock + Mailstand (`regel0_ansicht.detail`, eine Quelle mit der Mail). Signalchart wie heute, dazu Knöpfe *Wochenchart* / *Tageschart* (O45-Bilder) | `regel0_signale.db` (nur lesend) |
| **Positionen (H15)** | Asset, Richtung, Hebel, Eigenkapital, Kurs, Liquidation, **Abstand %**, **H15-Empfehlung**, **Finanzierung bisher / je Tag**, Ergebnis netto, REGEL0-Vermerk; Zeile **Abgleich mit Bitpanda: stimmt / WEICHT AB** (P11) | `hebelfuehrung.lade`, `betriebslage.hebel_wallet_abgleich` |
| **Freigabe je Asset** | alle Krypto-Assets der Watchlist (ohne Cash) mit Hebel-Schalter An/Aus, *REGEL0-Daten vorhanden*, letztes Signal; Knopf *Schalter umschalten* (dieselbe `db.set_hebel_pruefung_erlaubt`, GF2) | `asset_hebel_settings`, `betriebslage.neuaufnahme_und_abgleich` |

**Weitere Punkte:**
- **Laufzeit:** Die Signale lesen die kleine Ablage (≈ 1 MB). Positionen und Abgleich (H15 rechnet ≈ 0,1 s am Desktop, am NB etwa 0,4 s) werden nur gelesen, **wenn der Tab sichtbar ist**, höchstens alle 60 s; dazu ein Knopf *Aktualisieren*. Der 3-s-Takt blockiert sonst die GUI.
- **Entfällt im Hebel-Tab:** die Altlisten A/B/C, *Jetzt analysieren*, *Signal-Historie*. Der Code bleibt (`hebel_view.py`).

⚠️ **Zur Rücksprache (Regel *Umbau: prüfen, was fehlt*):**
1. **Hebel-Schalter in der Watchlist:** jetzt entfernen, oder bis GUI-4 (*Meine Assets*) doppelt lassen?
2. **Alter Hebel-Tab:** bis GUI-5 (Archiv) als letzter Tab *„Hebel (alt)“* erreichbar lassen, oder jetzt ganz aus der GUI nehmen (Code bleibt)?

**Nachweis vorab:**
- **Prüfstand:** die View einzeln gegen eine Kopie der NB-Sicherung (Tk unsichtbar, Muster `sofortliste_pruefstand`/`pruefe_h17`).
  - Jede Spalte gefüllt.
  - Filterzahlen gegen eigenes SQL.
  - Detail beginnt mit dem Signalmail-Text.
  - Positionen gleich `hebelfuehrung.lade`.
  - Schalter umschalten **an einer Wegwerf-DB**: genau eine Zeile in `asset_hebel_settings`, und die Watchlist sieht dieselbe.
  - Lesen ohne Schreibzugriff (Prüfsumme).
  - Laufzeit des Lesens.
- **Gegenprobe:** eigene Zählung der Signale je Filter, eigene Abstandsrechnung.
- **Suite:** GuiKette erweitert, ganze Suite. Am NB: Pull + Neustart → **K-GUI-2**.
- **Bündel (E-97):** reine GUI, kein Job, keine Mail → bündelbar (z. B. mit P13 H14 nach N5).

### G-W P12 gebaut — neuer Hebel-Tab (11.10.2026)

Nutzer 11.10.: *„1. bis GUI-4 doppelt lassen 2. aus der GUI entfernen“*.

**Gebaut:** `ui/hebel_tab.py` (`HebelTab`), in `ui/app.py` als Tab *Hebel*. `ui/hebel_view.py` ist aus der GUI genommen, der Code bleibt; die sieben Suite-Textprüfungen darauf und `pruefe_h17` bleiben gültig. Drei Unterreiter:
- **Signale (REGEL0):**
  - alle Signale; Filter *heute / 7 Tage / alle* und *nur Hebel-Schalter an* (Spalte `hebel_schalter` der Ablage, derselbe Wert, der das Mailen erlaubt);
  - Spalten: Asset, Signal, Stufe, Status, gemailt, Trader-Urteil, Ausstieg;
  - Detail = `regel0_ansicht.detail` (Mailtext + Prüfblock + Mailstand), Signalchart, Knöpfe *Wochenchart* / *Tageschart* (O45).
- **Positionen (H15):**
  - Kurs, Liquidation, Abstand %, H15-Empfehlung mit Warnstufe, Finanzierung bisher/je Tag, Ergebnis netto, REGEL0-Vermerk;
  - Zeile *Abgleich mit Bitpanda (Wallets): stimmt / WEICHT AB* (P11);
  - Detail = `hebelfuehrung.zeilen`.
- **Freigabe je Asset:**
  - alle Krypto-Assets der Watchlist (ohne Stablecoins) und jedes Asset mit Schalterzeile; Schalter AN/aus, REGEL0-Daten da/FEHLEN, letztes Signal;
  - Knopf *Schalter umschalten* (dieselbe `db.set_hebel_pruefung_erlaubt` wie die Watchlist, GF2). Der Watchlist-Knopf bleibt bis GUI-4.

**Laufzeit:** Der 3-s-Takt der App liest nur die Ablage. Unveränderte Daten zeichnen nichts neu, Sortierung und Auswahl bleiben stehen, das Detail wird nicht neu gezeichnet. H15 und der Abgleich laufen nur bei sichtbarem Unterreiter, höchstens alle 60 s (Knopf *Aktualisieren*).

**Gefunden beim Bau:**
- **Steuerzeichen:** Drei Prüfmuster in `pruefe_pakete.py` enthielten ein Backspace statt `\b` – zwei aus meinen Patches (P11 *nur lesend*, P12) und eines älter (Paket 14, `R\b`). Die Prüfungen waren damit **wirkungslos**. Jetzt sind sie bereinigt, mit Gegentests (erkennen INSERT, `db.set_`, *0,12 R*), und Paket 14, Regel0Betrieb und GuiKette sind grün. In `simuliere_kette.py` steht ein Backspace nur in einem Kommentar.
- **Signalchart im Prüfstand:** Es braucht Stunden im Signalfenster. Die Kopie hat nur Stellvertreter, also wurde der GUI-Weg mit einem echten Ersatzbild geprüft; die Erzeugung prüft Regel0Betrieb.

**Nachweis:**
- `p12_pruefstand.py` **8/8** (View einzeln, unsichtbar, gegen eine Wegwerfkopie der NB-Sicherung):
  - 424 Signale, 2 Positionen mit H15, Abgleich *stimmt*, 44 Freigaben (26 an);
  - Detail beginnt mit der Mail;
  - Filter monoton;
  - 3-s-Takt ohne Neuzeichnen;
  - H15 nur sichtbar bzw. erzwungen;
  - GF2 an der Wegwerfkopie, die Watchlist sieht denselben Wert;
  - Lesen schreibt nichts (Prüfsumme);
  - Einbindung.
- `p12_gegenprobe.py` **4/4**: eigenes SQL je Filter (424/17/353/15), gemailt 17, Abstand selbst gerechnet, AN 26.
- GuiKette 44/44 mit P12-Wachen.

**Am NB:** Pull + Neustart → **K-GUI-2** (Nutzer öffnet die GUI).

**Nachtrag G-W, 11.10.2026 abends — Bildprüfung durch den Nutzer:**
- Am NB ist der Tab da. Das Bild des Reiters *Freigabe je Asset* zeigte einen **Fehler von mir**: Bei ausgeschalteten Assets stand in *REGEL0-Daten* „-“, sofern es noch kein Signal gab – die Datenlage war für sie **nie geprüft**.
  - Betroffen waren 12 Assets mit Kursdaten, darunter APT, ASTER, BRETT, CANTON (über CC-Futures), IMX, QNT, S.
  - Gerade vor dem **Einschalten** ist das die entscheidende Frage.
- **Korrektur:** `betriebslage.mit_regel0_daten(namen)` prüft die Datenlage für **alle** Assets: *da*, *keine*, bei Schalter an ohne Kurse *FEHLEN*.
  - Datenbestand und Zuordnung stehen in einer Stelle (`regel0_datensymbole`, `zuordnung_bitpanda`); `neuaufnahme_und_abgleich` nutzt dieselben Helfer.
  - Der Teilexport ist für die Zeilen REGEL0-NEUAUFNAHME und *ohne REGEL0-Daten* unverändert.
- Gegenprobe G5 (eigene Lesung der Kursdateien und der Zuordnung, 40/40) – jetzt **5/5**. Prüfstand 8/8, p9-Gegenprobe 10/10, GuiKette 44/44, Regel0Betrieb 85/85.

### G-X P14 Spot B1 gebaut (11.10.2026)

- Spot B1 Mitnahme ×3: eigener Job 07:10, Schalter `spot_mitnahme_aktiv` (aus), Ablage `data/spot_betrieb.db`, A6 mit dem Schalter. Ausführlich: Spot §41.8, E-100.
- **Sichtbar:**
  - Statusseite: Karte *Betrieb* mit Zeile *Spot-Mitnahme ×3 (B1)*; Schalterkarte *Spot-Mitnahme ×3 (B1) – Mail*;
  - Teilexport *SPOT-MITNAHME (B1)*.
- Der App-Tab *Spot-Bestand* kommt mit GUI-3 (P15).


### G-Y Voranalyse P15 — GUI-3 Bestand-Tab (12.10.2026, im Bündel mit P16)

Nutzer 12.10.: *„Ja, Voranalyse P15 + P16 vorbereiten, prüfen und gegenprüfen“*.

**Zielbild:** abgestimmt in G-K, Tab *1 Bestand*: *„was du hältst, richtig bewertet“*. Fakten erhoben mit `p15p16_voranalyse.py` an der NB-Sicherung 11.10. 11:49, Gegenprobe `p15p16_gegenprobe.py` **4/4**.

**Ist `ui/portfolio.py` (533 Zeilen, Tab *Portfolio*):**
- **eine** Tabelle für alle **47** Bestände mit frei + gestakt > 0:
  - Kern 3, L 27, EURCV, Aktien 3, ETF 8, Rohstoffe 4;
  - **XDC ist gehalten, steht aber nicht in der Watchlist** des Desktops. Am NB zählt B1 28 L-Bestände; die Watchlist am NB weicht also ab.
- Spalten: Symbol, Name, Assetklasse, Bestand (*frei (+ gestakt)*), Preis, Wert (frei + gestakt), Einstand, G/V %.
- Darunter die Diversifikation nach Schwerpunkt (mit Thesen-Markern), der Knopf **„Letzte Bewertung anzeigen“** (letzte KI-Analyse der **angehaltenen** Rollen-Kette), der Gesamtwert (frei + gestakt + Fiat, **ohne Hebel-Eigenkapital**) und das Fiat-Feld (Ausnahme).
- **Fehlt:** Rolle (Kern/L), B1-Stand, Hebelpositionen. Eine Marktwert-Klasse H/M/S rechnet der Betrieb am NB heute **nicht** (sie braucht das NB-Universum aus P18, Spot §42.1).
- Neu aufgebaut wird der Tab **alle 3 s** (`app._poll_prices`). Doppelklick = Einstand (`AvgBuyPriceDialog`, GF4).
- Bitpanda-Abgleich: Menü *Datei* und Job alle 30 min.
- **Nur `ui/app.py` importiert `PortfolioView`**; keine Suite-Prüfung liest Textstellen aus `portfolio.py`.

**Vorschlag: neuer Tab `ui/bestand_tab.py` an der Stelle von *Portfolio*; `portfolio.py` bleibt** (der Dialog wird wiederverwendet), wie bei P12.

| Bereich | Inhalt | Quelle |
|---|---|---|
| **Spot** (alle Klassen) | Symbol, Name, Assetklasse, **frei**, **gestakt** (eigene Spalten), Preis (⚠ veraltet), Wert, Einstand, G/V %, **Rolle** (*Kern* BTC/ETH/SOL · *L* übrige Krypto · *Cash* · *—* andere Klassen · *nicht in Watchlist*), **B1: × Startkurs**, **Fenster bis**, **B1-Status** (offen / fällig / zu prüfen / verpasst / kein Kurs), **Upbit KRW** (ja/nein, aus P16) | holdings, `price_cache`, `spot_mitnahme.kreis` + `spot_betrieb.db` (nur lesend) |
| **Hebel** (kurz) | Asset, Richtung, Hebel, Eigenkapital, Abstand %, H15-Empfehlung, Abgleich Bitpanda; Hinweis *„Details im Hebel-Tab“* | `hebelfuehrung.lade`, `betriebslage.hebel_wallet_abgleich` — dieselbe Quelle wie Tab 2 |
| **Summen** | Spot frei · gestakt · Fiat · **Hebel-Eigenkapital** · **Gesamt** (Definition G-K) · letzter Bitpanda-Abgleich | wie heute + `hebel_positions` |
| Diversifikation | unverändert | wie heute |
| Knöpfe | Doppelklick Einstand (GF4), Fiat-Ausnahme (bleibt) | wie heute |

**Weitere Punkte:**
- **Laufzeit:** Der Spot-Teil bleibt im 3-s-Takt. B1 und Hebel werden nur gelesen, wenn der Tab **sichtbar** ist, und höchstens alle **60 s** (Muster P12). Unveränderte Daten zeichnen nichts neu.
- **Marktwert-Klasse H/M/S:** Spalte erst mit **P18**, weil der NB sie heute nicht rechnet. Eine CoinGecko-Rangnäherung wäre eine **andere Grundgesamtheit** als die Messung (Regel *Grundgesamtheit ist keine Stellschraube*).
- ⚠️ **Der Gesamtwert ändert sich**, weil das Hebel-Eigenkapital hinzukommt. Die Zeile nennt die Teile einzeln, damit der Sprung nachvollziehbar bleibt.

⚠️ **Zur Rücksprache (Regel *Umbau: prüfen, was fehlt*):**
1. **„Letzte Bewertung anzeigen“** gehört zur angehaltenen Rollen-Kette (letzte Analysen bis 05.10.). Jetzt **entfernen** (Code bleibt), oder bis GUI-5 (Archiv) im Tab lassen?
2. Der Tab heißt künftig **„Bestand“** statt *Portfolio*. Inhaltlich fehlt nichts: Alles Bisherige bleibt, es kommt nur dazu.

**Nachweis vorab:**
- **Prüfstand** gegen eine Kopie der NB-Sicherung (Tk unsichtbar, Muster `p12_pruefstand`):
  - jede Spalte gefüllt;
  - Summen gegen eigenes SQL;
  - Rolle gleich `spot_mitnahme.kreis`;
  - B1 gegen eine Wegwerf-Ablage aus `spot_mitnahme.lauf`;
  - Hebel gleich `hebelfuehrung.lade`;
  - kein Schreibzugriff (Prüfsumme);
  - Laufzeit des Lesens.
- **Gegenprobe:** eigene Wertsumme, eigene ×-Rechnung aus Dollar-Schlüssen.
- **Suite:** GuiKette erweitert. Am NB: **K-GUI-3**.

### G-Z P15 gebaut — Bestand-Tab (12.10.2026, im Bündel mit P16)

Nutzer 12.10.: *„Ja, den Ausbau eindeutig kennzeichnen, damit man nicht über den alten Code stolpert“* (Rücksprache G-Y).

**Entscheidungen:**
1. Der Knopf *Letzte Bewertung* **entfällt**.
2. Der Tab heißt **Bestand**.

**Gebaut:**
- `ui/bestand_tab.py` (`BestandTab`) ersetzt den Tab *Portfolio*.
  - Er erbt von `PortfolioView`: Einstand per Doppelklick (GF4), Fiat-Feld, Diversifikation, Tooltip.
  - Er ruft deren Konstruktor **bewusst nicht** (dort entsteht der alte Knopf).
- Inhalt wie G-Y:
  - Spot für alle 47 Bestände, mit Rolle, frei/gestakt getrennt, B1 (× Start, Fenster bis, Status) und Upbit KRW;
  - Hebel kurz;
  - Summe mit Hebel-Eigenkapital.
- B1, B3 und Hebel werden nur bei sichtbarem Tab gelesen, höchstens alle 60 s; unveränderte Daten zeichnen nichts neu.

**Ausbau gekennzeichnet:**
- `ui/portfolio.py`: Kopf *„⛔⛔ ABGELOEST am 12.10.2026 … NICHT MEHR IN DER GUI EINGEHAENGT“*, dazu ein Vermerk am alten Knopf.
- `ui/letzte_bewertung.py`: Vermerk *einziger GUI-Aufrufer war der abgelöste Tab*.
- `ui/app.py`: Kommentar am Import und an der Einhängung.
- Inventurblatt: Zeile `ui/portfolio.py` als ABGELÖST, neue Zeile `ui/bestand_tab.py`.
- Suite *GuiKette* wacht über alle Kennzeichnungen.

**Nachweis:**
- `p15_pruefstand.py` **11/11**, Tk unsichtbar, gegen die Kopie der NB-Sicherung:
  - 47 Zeilen, Rollen Kern 3 · L 27 · Cash 1 · andere 15 · nicht in Watchlist 1;
  - B1 für alle 27 L-Fenster, Upbit *nein* bei 11;
  - Hebel ETH/BTC;
  - Summe mit Hebel-Eigenkapital 900 €;
  - kein Knopf *Bewertung*;
  - kein Neuzeichnen ohne Änderung;
  - Produktion und Ablage unverändert;
  - schneller Teil 0,004 s, langsamer Teil 0,07 s.
- `p15_gegenprobe.py` **3/3**:
  - Summen per eigenem SQL (Abweichung 0,0000 €);
  - Rolle mit eigener Regel;
  - × Start für 27 Fenster aus eigenem SQL, mit gestellten neuen Kursen.
- Suite GuiKette **51/51**, Paket BitpandaInventur **6/6**.

Am NB: **K-GUI-3** (dein Bild der GUI).

### G-Z1 P15b — Mouseover für jede Spalte, nach dem ersten Bild (12.10.2026)

Nutzer 12.10. (Bild des Tabs am NB): *„bitte überall ein Mouseover mit der genauen Bedeutung der Spalten, wenn noch nicht eingebaut“*.

**Bestandsaufnahme:**
- Die Watchlist war vollständig erklärt.
- Im **Bestand-Tab** fehlten 6 Spot-Spalten und die ganze Hebel-Tabelle. ⚠️ Außerdem war die Erklärung der Diversifikation (*Schwerpunkt* ▲/▼/●), die der alte Portfolio-Tab hatte, **beim Neubau verloren gegangen**; sie ist wiederhergestellt.
- Im **Hebel-Tab** fehlten 10 Spalten.

**Gebaut:**
- Jede Spalte jeder Tabelle in Bestand- und Hebel-Tab hat einen Text. Die Aussagen sind am Code geprüft: Hebel, Liquidationspreis, REGEL0-Vermerk, Signal-Asset, Kursquelle.
- Nach dem Bild außerdem: Mengen ab einer Million ausgeschrieben (CAT stand als *2.6188e+07*); die Spalten *Einstand* und *Upbit KRW* sind breiter.

**Nachweis:**
- Suite GuiKette **52/52**, neue Wache *jede Spalte erklärt*. Sie ist aus den Spaltenlisten abgeleitet; gegengetestet wird sie, indem ein Text entfernt wird → rot.
- `p15_pruefstand` 11/11, `p12_pruefstand` 8/8.

Am NB: **K-GUI-3b**. K-GUI-3 ist mit dem Bild erfüllt.

**Hinweis:** Die alten Tabs (Signale, Marktscan, Screener, Regime, Schwerpunkte) sind nicht angefasst. Regime und Schwerpunkte haben gar keine Spaltenerklärung; sie gehen mit GUI-5 ins Archiv bzw. in *Multi-Asset (ruht)*.

### G-Z2 P15c — Nachbesserung nach dem zweiten Bild (12.10.2026)

Nutzer 12.10. (Bild nach Pull und GUI-Neustart): *„eine Spalte fehlt in der Anzeige, Mouseover ist da, aber kann rechts in der Tabelle nicht gelesen werden, da es rechts von der Maus gerendert wird“*.

| Fehler | Ursache | behoben |
|---|---|---|
| Spalte *Upbit KRW* abgeschnitten | meine breitere Einstand-Spalte (P15b) – die Summe der Breiten passte bei 150 % Anzeige nicht mehr ins Fenster, und eine waagrechte Laufleiste fehlte | Breiten neu (Summe 1.210, ×1,5 = 1.815 ≤ 1.900), **waagrechte Laufleiste** |
| Mouseover am rechten Rand nicht lesbar | das Fenster stand immer rechts unten vom Zeiger (Spaltenkopf **und** Zeile) | `heading_tooltip.platziere` / `lage`: reicht der Bildschirm nicht, **links bzw. oberhalb** vom Zeiger. Gilt für alle Tabs (gemeinsame Funktion) |
| Einstand lang, *2.6188e+07* in der Einstand-Spalte bei CAT | Zusatz *(⚠ n unbepreist)* | kompakt **„⚠“** bzw. **„(m)“**; die Menge steht im Zeilen-Mouseover |

**Nachweis:**
- `p15_pruefstand` **14/14** (neu P12 Breite und Laufleiste, P13 Einstand kompakt, P14 Randregel);
- `p12_pruefstand` 8/8;
- `lage()` an fünf Randfällen;
- GuiKette **54/54** (zwei neue Wachen).

Am NB: **K-GUI-3b** (neues Bild).

### G-Z3 P15d — Summen sichtbar (13.10.2026)

- **Bild 13.10. 05:03:** Upbit-Spalte, Laufleiste, kompakter Einstand und CAT-Menge passen. Nutzer: *„Summe für Hebel ist nicht sichtbar“*.
- **Ursache:** Die Summenzeile stand ganz unten und lag bei 150 % Anzeige außerhalb des Fensters.
- **Behoben:**
  - Der **Gesamtwert** mit allen Teilen steht **oben** unter der Kopfzeile.
  - Die Hebel-Überschrift nennt *„offene Positionen: n · Eigenkapital zusammen … EUR“*.
  - Die Spot-Tabelle hat 13 statt 16 Zeilen (Laufleiste).
- **Nachweis:** `p15_pruefstand` **15/15** (neu P15), GuiKette mit Wache P15d.

### G-Z4 P15e — Aufteilung nach Rolle statt Schwerpunkt, senkrechte Laufleiste (13.10.2026)

Nutzer 13.10. (Bild 06:38): *„unten ist entweder ein alter Bereich bzw. Multi-Asset-Schwerpunkte – diese brauchen wir später noch einmal, oder?“* → Vorschlag 1–3 → *„Ja, 1 bis 3 so umsetzen, prüfen und gegenprüfen“*.

1. Im Bestand-Tab steht die **Aufteilung nach Rolle**: Kern · L · Cash · Fiat · andere Klassen · nicht in Watchlist · Hebel, jeweils mit Wert und Anteil am Gesamtwert (zusammen 100 %). Jede Spalte hat einen Mouseover-Text.
2. Die **Diversifikation nach Schwerpunkt** (Multi-Asset, Thesen ▲/▼/●) ist **aus dem Bestand-Tab genommen, nicht gelöscht**: Der Code `PortfolioView._refresh_diversifikation` ist als *AUFBEWAHRT für GUI-5* gekennzeichnet. Er zieht mit GUI-5 in *Multi-Asset (ruht)* (Plan P20, für O39).
3. Die Spot-Tabelle hat eine **senkrechte und eine waagrechte Laufleiste**.

**Nachweis:**
- `p15_pruefstand` **17/17**: P16 Aufteilung mit 7 Gruppen, Hebel 900 €, Anteile 100 %; P17 beide Laufleisten; P7 ohne Schwerpunkt-Tabelle.
- `p15_gegenprobe` **4/4**: G4 Aufteilung per eigenem SQL, Abweichung 0,0000 €.
- GuiKette **58/58** (Wachen: Aufteilung an gestellten Zeilen; Schwerpunkt aus und aufbewahrt; Laufleisten).

### G-Z5 P15f — die Aufteilung passt ins Fenster (13.10.2026)

- **Bild 13.10. 07:12:** Nutzer: *„der Bereich unten mit Aufteilung nach Rolle ist leer … ist das korrekt so?“* — Nein.
- **Ursache:** Die Tabelle war nicht leer, sondern lag bei 150 % Anzeige **unter dem Fensterrand** (13 + 3 + 7 = 23 Tabellenzeilen).
- **Behoben:**
  - Die Aufteilung ist **waagrecht**: eine Spalte je Gruppe, zwei Zeilen *Wert (EUR)* und *Anteil %*, mit Mouseover je Gruppe.
  - Die Hebel-Tabelle ist so hoch wie die Zahl der Positionen (1–5).
  - Spot 12 Zeilen mit Laufleiste — zusammen **16** Zeilen.
- **Nachweis:** `p15_pruefstand` **18/18** (neu P18 Höhe), `p15_gegenprobe` 4/4, GuiKette 58/58.

### G-Z6 P15g — die drei Bereiche in der Höhe verschiebbar (13.10.2026)

- Nutzer 13.10.: *„du kannst zusätzlich die drei Bereiche auch in der Höhe anpassbar machen zum Verschieben, wenn notwendig, oder?“*
- **Gebaut:** Spot, Hebel und Aufteilung liegen in **einem senkrechten PanedWindow**; die Trennleisten lassen sich mit der Maus ziehen.
  - Kopfzeile und Gesamtwert stehen fest oben.
  - Das Fiat-Feld hängt fest unten und rutscht beim Ziehen nicht aus dem Fenster.
- **Nachweis:** `p15_pruefstand` **19/19** (neu P19: drei Bereiche, Trennleiste programmgesteuert verschoben 479 → 359, Fiat-Feld außerhalb), GuiKette mit Wache P15g.

### G-Z7 P15h — Hebel-Zeilen und Aufteilung vollständig (13.10.2026)

**Bild 13.10. 07:41:**
- Aufteilung und Trennleisten sind da.
- Die Hebel-Überschrift sagt *2 Positionen · 900 €*, in der Tabelle steht aber nur BTC. Laut Diagnose 07:40 ist ETH **offen** (12,4 %, LIQUIDATION NAHE); die Tabelle war um eine Zeile gescrollt.
- *Anteil %* ist halb abgeschnitten.

**Behoben:**
- Hebel- und Aufteilungstabelle springen nach jedem Neuladen an den Anfang.
- Beim ersten Anzeigen setzt der Tab die Trennleisten so, dass Hebel und Aufteilung ihre **volle Höhe** haben. Die Dicke der Trennleiste wird nachgemessen: Der Prüfstand fand 91 statt 96 px, das ist korrigiert. Danach verschiebt der Nutzer frei.

**Nachweis:** `p15_pruefstand` **20/20** (neu P20: 96/96 px, Hebel nach Neuladen oben), GuiKette mit Wache P15h.

**K-SP-2 erfüllt** (Diagnose 13.10. 07:44): A6 nimmt die 50 alten Spot-Zeilen heraus, keine Stop-Mail mehr. Die erste Mitnahme-Mail → **K-SP-2b** (Ereignis).

### G-Z8 P18b — Watchlist: Grundliste im Repo + Ergänzung am NB (Voranalyse 14.10.2026)

Nutzer 14.10.: *„P18b Voranalyse vorbereiten“* (Variante B nach Spot §48.5).

**Ziel:**
- Kein Schreibweg am NB ändert mehr die versionierte `config.yaml`, damit kein Pull mehr an einer lokalen Änderung scheitert (Anlass: XDC und CT, K-WL-1).
- Der Desktop behält seine Quelle für Tests und Messungen, und die Grundliste behält Git-Verlauf und Hand-Bearbeitung.

**Ist-Stand am Code (geprüft):**

| | Befund |
|---|---|
| Laden | `config.load_config()` hält die ganze `config.yaml` im Speicher (`_config_cache`); `get_watchlist()` baut daraus die 62 `WatchlistAsset` |
| ⚠️ Kommentar falsch | `scheduler/background.py` (`refresh_prices_job`) und `main.py` sagen *„get_watchlist() liest config.yaml ohne Caching“*. Tatsächlich wird zwischengespeichert. Richtig ist trotzdem die Wirkung: GUI, Scheduler und Statusseite laufen am NB in **einem** Prozess (`main.py`), und jeder Schreibweg leert den Zwischenspeicher. Eine Änderung von außen (Pull) wirkt erst nach dem Neustart |
| Leser | 63 Dateien rufen `get_watchlist()`, 19 davon im Betrieb. Direkt an der Datei lesen nur `git_stand.py` (Repo, gewollt), `messe_signalbilanz_je_asset.py` (Messung am Desktop) und ⚠️ `nb_teilexport_betriebsdaten.py:226` (die Zeile *WATCHLIST krypto* am NB, würde die Ergänzung übersehen) |
| Schreiber | fünf Wege, alle über vier Funktionen in `config.py`: `add_watchlist_entry` (GUI *Asset hinzufügen*, Marktscan, Screener, **Hebel-Importer automatisch**) und `_update_watchlist_field` / `update_watchlist_kategorie` (GUI *Bearbeiten*: Rolle, Status, CoinGecko-ID, Kategorie). Die Aufrufer übergeben nur Werte |
| Datenbank | `database/db.py` importiert `config` nur **innerhalb** einer Funktion (Migration der Hebel-Schalter in `init_db`), also gibt es keinen Ring. `db.DB_PATH` ist in Prüfskripten umbiegbar |

**Prototyp (Wegwerf-DB, 14.10.):**
- Mit leerer Ergänzung ergibt sich genau die heutige Liste (**62 Einträge, bitgleich**).
- Neuaufnahme, Überschreiben eines Feldes (XLM Rolle) und Ausblenden (QNT) wirken richtig.
- Lesen 0,7 ms.

**Bau (Vorschlag):**

| # | Inhalt |
|---|---|
| W-1 | Tabelle `watchlist_ergaenzung` in der Produktion (`symbol` PK, `eintrag` JSON nur mit den geänderten Feldern, `entfernt`, `herkunft` = gui / gui_bearbeiten / marktscan / screener / hebel_import / o26, `angelegt_am`, `geaendert_am`). Angelegt in `init_db` (App-Start am NB), **nie** beim Lesen |
| W-2 | `get_watchlist()` = Grundliste aus `config.yaml` **plus** Ergänzung. Ein Eintrag ergänzt (neues Symbol, hinten angehängt) oder überschreibt Felder (Symbol der Grundliste); *entfernt* blendet aus. Gelesen nur mit `mode=ro`; fehlt die Datei oder die Tabelle (Desktop, Prüfskripte), ist die Ergänzung leer. Zwischengespeichert wie heute; jeder Schreibweg leert den Speicher |
| W-3 | Die vier Schreibfunktionen schreiben in die Ergänzung statt in die Datei, mit denselben Prüfungen wie heute (Symbol schon vorhanden, Kategorie gültig, Wert ändert sich). Die Aufrufer bleiben **unverändert**; `herkunft` kommt als optionaler Parameter, ohne ihn gilt *gui* |
| W-4 | Diagnose: `watchlist_stammdaten` je Symbol mit `quelle` (grundliste / ergaenzung / grundliste+ergaenzung) und `herkunft`. Punkt 17: Einträge aus der Ergänzung sind **Hinweise** (*„nur am NB – ins Repo übernehmen?“*), keine Auffälligkeit. Eine Abweichung **ohne** Ergänzung bleibt eine Auffälligkeit; die lokal geänderte `config.yaml` ebenso |
| W-5 | Teilexport: die Zeile *WATCHLIST* über `get_watchlist()` und dazu die Ergänzung je Eintrag (Herkunft, Datum) |
| W-6 | Übernahme ins Repo: Ich trage den Eintrag per Commit in die Grundliste ein. Danach ist die Ergänzung **deckungsgleich**, und Punkt 17 meldet *„überflüssig“*. Gelöscht wird die Zeile **nicht** automatisch (*nichts löschen ohne Ja*), sondern mit deinem Ja |
| W-7 | Die falschen Kommentare *„ohne Caching“* in `background.py` und `main.py` richtigstellen |
| W-8 | Prüfstand am Seiteneffekt (Wegwerf-Produktion): Teil 0 bitgleich mit leerer Ergänzung; jede der vier Schreibfunktionen schreibt in die Ergänzung und **nicht** in `config.yaml` (Prüfsumme); der Hebel-Importer legt einen neuen Coin in der Ergänzung an; Zwischenspeicher nach dem Schreiben frisch; *entfernt* blendet aus; Punkt 17 mit Ergänzung = Hinweis, ohne = Auffälligkeit; Standard-DB unberührt. Dazu ein Suite-Paket |

**Risiken:**
- Ein Fehler im Zusammenführen träfe alle 63 Leser. Dagegen stehen Teil 0 bitgleich und der Prototyp.
- Zwei Orte: Wer nur die Datei liest, sieht die Ergänzung nicht. Das betrifft die drei direkten Leser oben. Der Teilexport wird umgestellt; `git_stand` und die Messung am Desktop sollen die Grundliste lesen.
- Der Desktop sieht Einträge, die es nur am NB gibt, erst über die Diagnose. So ist es gewollt; Punkt 17 nennt sie.

**Nicht in P18b:**
- O40 *Meine Assets* (Ansicht, Kennzeichen Bestand / Hebel / beobachtet; der Bestand wird zur Laufzeit aus `holdings` abgeleitet).
- O26 (automatische Aufnahme neuer Bitpanda-Bestände; sie schreibt dann in genau diese Ergänzung).

**Am NB:** Pull und Neustart (`init_db` legt die Tabelle an). Kontrolle **K-WL-2**:
- Die Diagnose zeigt `quelle` je Symbol, Punkt 17 ist still (Ergänzung leer).
- Der nächste Eintrag über die GUI erscheint als Hinweis, und `git status` bleibt leer.

Aufwand etwa ein halber Tag einschließlich Prüfstand.

### G-Z9 P18b gebaut (14.10.2026, Nutzer: *„Ja, P18b bauen, prüfen und gegenprüfen“*)

| Teil | Stand |
|---|---|
| `database/db.py` | Tabelle `watchlist_ergaenzung` im Schema (`init_db`, App-Start) |
| `config.py` | `watchlist_ergaenzung()` (nur lesend, legt nie etwas an), `watchlist_eintraege()` (Zusammenführen), `watchlist_herkunft()`, `get_watchlist()` liest Grundliste + Ergänzung. Die vier Schreibfunktionen schreiben in die Ergänzung (`_ergaenzung_schreiben`), gleiche Prüfungen wie vorher, Rückweg bei Fehlschlag. Der tote Text-Helfer `_upsert_field_at_block_end` ist ausgebaut |
| Aufrufer | unverändert bis auf die Herkunft: `hebel_import`, `marktscan`, `screener`; GUI-Aufnahme `gui`, GUI-Bearbeiten `gui_bearbeiten` |
| Diagnose / Punkt 17 | `watchlist_stammdaten` mit `quelle` und `herkunft`, Abschnitt `watchlist_ergaenzung`. Ergänzung = **Hinweis** (übernehmen? / überschreibt / ausgeblendet / deckungsgleich-überflüssig); Abweichung ohne Ergänzung = Auffälligkeit |
| Teilexport | Watchlist über `get_watchlist()`, dazu die Ergänzung je Eintrag |
| Kommentare | *„ohne Caching“* in `background.py` und `main.py` richtiggestellt |
| **Prüfstand** `p18b_pruefstand.py` (Kopie der Produktion 14.10. 03:29) | **6/6**:<br>• `init_db` legt nur die neue Tabelle an, die 39 anderen behalten ihre Zeilenzahl.<br>• Die Liste ist bitgleich mit `config.yaml`.<br>• Der Hebel-Importer legt einen neuen Coin **in der Ergänzung** an, `config.yaml` bleibt bitgleich.<br>• Der Bestandsabgleich ordnet den Coin ohne Neustart zu.<br>• Punkt 17 meldet einen Hinweis, keine Auffälligkeit.<br>• Die Original-Sicherung bleibt unberührt |
| Suite-Paket **WatchlistErgaenzung** | **10/10** mit Wegwerf-DB:<br>• Teil 0 bitgleich; Lesen legt nichts an.<br>• Aufnahme, doppelte Aufnahme, Bearbeiten (Rolle), CoinGecko-ID und Kategorie (ungültig bricht vor dem Schreiben ab), Ausblenden.<br>• Punkt 17: Hinweis statt Auffälligkeit; dieselbe Lage ohne Kennzeichen wird gemeldet.<br>• `config.yaml` bleibt bitgleich.<br>• Mutationen *Ergänzung schreibt nicht* und *entfernt wirkungslos* werden gefunden |

**Fund (nicht im Umfang, zur Entscheidung):**
- Fünf **Einstellungs-Schalter** der GUI schreiben weiterhin in die versionierte `config.yaml`: Hebel-Richtungsmodus, Marktsuche und E-Mail *nur Bitpanda-gelistet*, Regime-Override, Regime-Score-Override.
- Sie gehören zum alten System und sind seit 28.07. **bewusst** über Git synchronisiert (*„auf beiden Geräten garantiert derselbe Wert“*).
- Ein Klick am NB erzeugt trotzdem dieselbe lokale Änderung. P21 meldet sie.
- Vorschlag: so lassen, sie werden selten benutzt. Falls doch nötig: dieselbe Lösung wie hier, als eigene Tabelle.

### G-Z10 „Asset hinzufügen“ einfacher? (Prüfung 14.10.2026, Nutzerfrage)

Nutzer 14.10.: *„prüfe, ob die aktuelle Funktionalität zu Asset hinzufügen einfacher umsetzbar ist als jetzt bei der manuellen Methode“*.

**Heute (am Code geprüft):**
- Man öffnet den Dialog und **tippt Symbol und Name**, wählt Assetklasse, Rolle und Status.
- Die CoinGecko-ID versucht der Dialog über den Bitpanda-Namen (genau ein Treffer); sonst öffnet er die Suche. Danach folgen die Warnungen der Prüfung.
- ⚠️ Eine gehaltene Position ohne Watchlist-Eintrag ist in der App **nicht sichtbar**: Der Bestandsabgleich übernimmt sie nicht in `holdings`, der Bestand-Tab zeigt sie nicht, und sie fehlt im Gesamtwert (HBAR 13.10.: rund 102 EUR).
- Sichtbar ist sie nur als Logzeile und in der täglichen Mail *„Position ohne Watchlist-Eintrag“*.

**Was das System schon weiß:**
- Bitpanda-Asset-ID, Kürzel, Name und **Art aus dem Katalog**: coin/token → krypto, stock/equity_stock → aktien, etf/equity_etf → etf, metal → rohstoffe. Nur ETC ist nicht eindeutig (3QSS steht als etf in der Watchlist).
- Dazu Menge und Wert.

**Vorschlag P18c (klein, GUI):**

| # | |
|---|---|
| 1 | Bestand-Tab: Bitpanda-Positionen **ohne** Watchlist-Eintrag als eigene Zeilen (Rolle *nicht in Watchlist*, Wert, Menge), aus `bitpanda_wallet_saldo` + `bitpanda_katalog`, nur lesend; sie zählen in Gesamtwert und Aufteilung |
| 2 | **Doppelklick** auf eine solche Zeile öffnet *Asset hinzufügen* **vorausgefüllt**: Symbol, Name, Assetklasse aus dem Katalog, Rolle taktisch, CoinGecko-ID automatisch. **Neu** ist ein Preisabgleich der gefundenen ID gegen den Bitpanda-Kurs, damit keine falsche ID durchrutscht (Muster D5). Du drückst nur **Hinzufügen** |
| 3 | Die Mail *„Position ohne Watchlist-Eintrag“* nennt diesen Weg |

- **Nicht** automatisch, sondern weiter mit deiner Bestätigung (Airdrops wie CT nur auf Rückfrage). Das vollautomatische O26 bleibt später.
- Aufwand etwa 2–3 Stunden; GUI-Neustart; schreibt über P18b in die Ergänzung.
