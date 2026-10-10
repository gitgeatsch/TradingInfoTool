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

