# Voranalyse G19 — Dashboard und spezifische Bewertung vorziehen: Bau B1, B2, B4–B6 (07.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

**Auftrag:** Nutzer 07.11.: *„ok 1. prüfen gegenprüfen und Doku“* — Voranalyse für den Bau von G19 nach **E-170 F-D 1**: B1, B2 (ohne Wal-Fünftel), B4, B5, B6 am Desktop bauen und nachweisen, dann **ein** NB-Bündel; B3 (LLM-Rolle) getrennt danach.
**Grundlagen:** [`Bauplan_Dashboard_A3_A4_28_10.md`](Bauplan_Dashboard_A3_A4_28_10.md) (B1–B6, §6 Prüfungen, §8 Mail) · [`Datenbasis_Schichten_Sichten_28_10.md`](Datenbasis_Schichten_Sichten_28_10.md) (Ebenen, Ü1–Ü9) · [`Fuetterung_Satzform_31_10.md`](Fuetterung_Satzform_31_10.md) (SF1–SF9) · [`Voranalyse_G18_Gesamtkonzept_06_11.md`](Voranalyse_G18_Gesamtkonzept_06_11.md) §6.
**Erhoben:** aus dem Code am Desktop, nur lesend (Fundstellen Datei:Zeile in §3–§5). **Fassung 2** nach der unabhängigen Gegenprüfung (§10: 20 Befunde, 2 schwer, alle eingearbeitet). **Nichts gebaut, nichts am Betrieb geändert.**

---

> ⛔ **Entschieden 07.11.2026 (E-171), Nutzer *„OK dann Möglichkeit1“*: G19 wird nur als UNTERBAU gebaut.**
> Jetzt **B2** (Fakt-Sammler, §4) und **B4** (Job mit Protokoll `data/asset_lage.db`, §5.1), dazu ihre Prüfungen aus §6 und ein Diagnose-Abschnitt für K-AL-1.
> **Zurückgestellt bis B3** (nach G7 Stufe 2): **B1** Befund-Karte (§3), **B5** Statusseite (§5.2) und der Befundblock in der Mail (§5.3).
> ✔ **Gebaut und geprüft 07.11. → §11** (Prüfstand 26/26 auf NB-Kopien, Code-Gegenprüfung 16 Befunde eingearbeitet). NB: K-AL-1, K-AL-2.
> Grund: Fakten und Befund-Verweise ohne Bewertung helfen dem Nutzer nicht (*Information ohne Handlungsableitung ist nur Arbeit*); die spezifische Bewertung kommt erst aus Ebene 3/4 (G7, A1, finales LLM) — und nur, wenn sie trägt. Die Abschnitte zu B1/B5 bleiben als Vorlage für B3 stehen.

## 0. In sechs Sätzen

1. Gebaut wird eine **Asset-Karte** je Bestand, je REGEL0-Signal des Tages und je offener Hebelposition: **Fakten** (Code, nur lesend) und **Befunde im Geltungsbereich** (Befund-Karte, vom Code zugeordnet) — **ohne LLM**.
2. Fast jeder Fakt hat schon eine Lesefunktion; neu sind ein Upbit-Leser je Asset, eine Termin-Ablage, die Vereinigung der Asset-Menge und **übergebbare Pfade** für alle Leser (sonst ist kein Prüfstand gegen Kopien möglich).
3. Die Befund-Karte nimmt nur **registrierte** Befunde mit ihrer **registrierten** Zahl (brutto; netto nur gekennzeichnet nachgelagert) — keine Diagnosezahlen ohne Band, kein Vorzeichen, das sich zu einem Gewicht zählen ließe.
4. Der Job schreibt nur in die **eigene Datei** `data/asset_lage.db`; die Signalkarten werden **nicht über die Uhrzeit**, sondern über den Schlüssel `(symbol, signalstunde)` nachgezogen — der Signalweg bleibt unberührt.
5. **Nachweis am Desktop gegen NB-Kopien**, die schon im Austauschordner liegen (`regel0_signale.db` 04.11., `spot_betrieb.db` 01.11., DB-Sicherung 06.11.); eine Prüfung verlangt **je Quelle einen echten Fakt** — leere Karten lassen sie rot.
6. Die Mail folgt dem Entscheid vom **28.10. (Weg 2, beide Blöcke)**: die REGEL0-Signalmail bekommt den Befundblock als neuen Mailteil (§5.3) — keine neue Frage.

---

## 1. Berichtigung zu G18 — und was daraus für B1 folgt

**Berichtigung (gefunden beim Erheben für B1):** In der Voranalyse G18 (§0, §1.2) und in meiner Nachricht vom 06.11. stand, das Plus von REGEL0 liege „zu **99 %** an Tagen mit mehr als 20 Signalen“. **Die 99 % sind der Anteil an der *Differenz zweier Fassungen*** (61 % + 38 %), nicht am Plus (E-138; [`Voranalyse_REGEL0_Robustheit_24_10.md`](Voranalyse_REGEL0_Robustheit_24_10.md) §3.4). Die Tabelle dort (**Diagnose p82, nur Mechanismus, ohne Band, netto nach 0,48 %**):

| Signale am Tag | Tage | Referenz | lang |
|---|---|---|---|
| 1–5 | 282 | −1,97 % | −1,60 % |
| 6–20 | 241 | −0,50 % | −0,57 % |
| 21–60 | 172 | +0,31 % | −0,31 % |
| > 60 | 46 | +0,76 % | +0,08 % |

**Was bleibt:** „Plus nur an marktweiten Tagen, **aber nicht robust**“ (Bilanz B.7) — nur in der Referenzfassung, und das Plus der Referenz kommt laut E-139 allein aus der Reife-Regel (Band [−0,23; +0,59]). G18 ist am 07.11. berichtigt; E-170 ist davon nicht berührt.

**Folgen für B1:**
- **Keine Diagnosezahl auf die Karte.** Die Zahlen oben haben kein Band, gelten nur für eine Fassung und sind netto. Auf die Karte kommt nur die **registrierte** Zahl eines Befunds (hier `E-139`).
- **Vorgriff-Sperre:** Die Zahl der Signale **am Tag** steht erst am Tagesende fest; zur Signalstunde ist sie unbekannt (*TAGESwert an STUNDENanker ist Vorgriff*). Ein Befund dazu wird **nie** maschinell zugeordnet, sondern nur mit seiner Grenze gezeigt. Die Spur „REGEL0 an marktweiten Tagen“ (E-138) ist nach E-170 F-C nur auf Daten ab 25.10. prüfbar *(nicht zu verwechseln mit Kandidat K-b der Bilanz B.6, einem Marktsignal auf BTC/ETH mit Test auf 2020–23 — in G18 §3.2 vermengt, dort ebenfalls berichtigt)*.

---

## 2. Abgrenzung — was G19 baut und was nicht

| | in G19 | nicht in G19 (wohin) |
|---|---|---|
| Fakten je Asset | ✔ B2 | Wal-Fünftel (E-170: ohne; Abruf 32 MB/Tag mit G8b) |
| Befund-Karte und Code-Zuordnung | ✔ B1 | LLM-Auswahl A3, Gegenanwalt A4 → **B3**, getrennt, zwei Modelle (Ü7), K-AL-0 |
| Sicht-Zustände `agent/zustaende.py` | am Desktop, wenn `sichten.db` da ist, **einmal oben** (marktweit) | NB: Abrufer `api/sichten_quellen.py` erst mit **G8b** |
| Statusseite „Asset-Lage“, Befundblock in der Signalmail | ✔ B5 | – |
| REGEL0-Signal, Trader-Prüfblock, H15 | **unverändert** | Signaländerungen erst nach der ganzen Kette (E-169) |
| Asset-Zustände mit Rang (Kurs-Abstand 200 T u. ä., Fütterung §4 Block 2) | – | mit B3: erst dann gibt es einen Leser dafür |

⚠️ **Ausweichregel (E-169):** Alles auf der Karte ist **Information** — nie Auslöser, nie Gewicht. Die Karte sagt nicht „kaufen“ oder „nicht kaufen“ (Bauplan §1, Ü9).

---

## 3. B1 — die Befund-Karte

### 3.1 Datenmodell (in `bestand.py`, wie die anderen Register)

| Feld | Inhalt | Beispiel |
|---|---|---|
| `kennung` | eine Kennung aus `bestand.BEFUNDE` — **nur registrierte**; eine E-Nummer ohne eigenen Befundeintrag (z. B. E-138) geht nur über den Befund, der sie aufnimmt (hier E-139) | `E-139`, `G16-wale-s2` |
| `strang` | `regel0` · `hebel` · `spot_einstieg` · `spot_fuehrung` | `regel0` |
| `zahl` | die Zahl, die genannt werden darf — **wörtlich im registrierten Befundtext**, brutto; netto nur mit Kennzeichen „nach Kosten, nachgelagert“ (Regel 2) | aus dem Text von E-139 |
| `gilt_wenn` | maschinenlesbar aus den Schlüsseln in §3.3, oder leer | `kern == ja` |
| `grenze` | Text: was der Befund **nicht** sagt | „nicht robust (0/6)“, „nur Kern“, „Tageszahl erst am Tagesende bekannt“ |

⚠️ **Kein Feld für die Richtung** (für/gegen). Ein Vorzeichen je Zeile ließe sich zählen und würde zum Gewicht (Ausweichregel). Das Paket prüft, dass keine Karte und keine Mail Befundzeilen **zählt oder verrechnet**.

**Erzeugt:** `REGISTER_Befundkarte.md` über `schreibe()` in `bestand.py:12152`. Nie von Hand ändern.

### 3.2 Die Auswahlregel

Ein Befund kommt auf die Karte, wenn **alle drei** gelten:
1. `stand == "gilt"` in `bestand.BEFUNDE` (heute 1.103 geltende, 100 abgelöste, 91 offene);
2. er betrifft eine **Handlung im Betrieb** (REGEL0-Einstieg, Hebel-Führung, Spot-Einstieg, Spot-Führung), nicht ein Messwerkzeug;
3. er nennt eine **Zahl**, ein **klares Nein** („trägt nicht“, „nicht trennbar“) **oder „nicht entscheidbar / nicht belegt“** (z. B. E-133) — gerade diese schützen vor Überdeutung.

Erwartet: 30–60 Einträge. Die Liste wird im Bau aus dem Register erhoben, von einer **zweiten Instanz** gegengeprüft und dir **vor dem NB-Bündel** als Anlage vorgelegt (sie ist Inhalt, kein Code).

### 3.3 Zuordnung durch den Code — „im Geltungsbereich“, nicht „gilt hier“

| Art | Anzeige |
|---|---|
| `gilt_wenn` gesetzt und erfüllt | **„im Geltungsbereich von {Kennung} (Bedingung: …)“** · Zahl · Grenze |
| `gilt_wenn` leer | **„für den Strang {strang}, Geltungsbereich nicht maschinell prüfbar“** · Zahl · Grenze |

Befunde sind Mittelwerte über Mengen; „gilt hier“ würde behaupten, sie träfen auf **diesen** Handel zu (Bauplan §1: *„liegt die Lage in ihrem Geltungsbereich“*).

**Erlaubte Schlüssel für `gilt_wenn`** — je Schlüssel mit Bezugszeitpunkt und genauem Wert:

| Schlüssel | Wert | Bezugszeitpunkt |
|---|---|---|
| `kern` | ja/nein (`agent/kernwerte.py:22`) | fest |
| `strang` | aus dem Anlass der Karte | fest |
| `hebel_offen` | Position in `hebelfuehrung.lade` (ohne „laut Bitpanda geschlossen“) | Kartenzeit |
| `bestand_vorhanden` | frei + gestakt > 0 | Kartenzeit |
| `ankuendigung_art` | `aktive(c, symbol, ende)` | **Signalkarte: Ende der Signalstunde** · Bestandskarte: Kartenzeit |
| `upbit_fall` | Fall in `upbit_fall` | wie oben |

**Nicht erlaubt** (Gegenprüfung §10 Nr. 13): `verw_fuenftel` (heutiger Wert an Grenzen des letzten Monatsstichtags, gemessen aber auf Stichtag-Rängen — Messgeometrie ≠ Betrieb), `season_stufe` (wird täglich neu geschrieben, Revisionen), alles mit Tages- oder Zukunftsbezug. Diese bleiben **Fakten auf der Karte**, aber keine Zuordnungsbedingung. Die Liste prüft das Paket im Helfer (CLAUDE.md, Prüfungen Regel 3).

---

## 4. B2 — der Fakt-Sammler `agent/asset_lage.py`

### 4.1 Welche Assets eine Karte bekommen

**Bestände ∪ REGEL0-Signale des Tages ∪ offene Hebelpositionen**:
- Bestände: `holdings` mit `quantity + staked_quantity > 0` (Muster `remote/status.py:410-418`);
- Signale: `regel0_signale.db`, Tabelle `signal`, Tag der `signalstunde` — **alle**, nicht nur `hebel_schalter = 1` (Filter in `betriebslage.regel0_heute`, `agent/betriebslage.py:251`);
- Hebel: **dieselbe Menge wie `hebelfuehrung.lade`** (`agent/hebelfuehrung.py:494`, ohne die laut Bitpanda geschlossenen, `:507-509`, P11c) — nicht `db.get_open_hebel_positions`, sonst gäbe es Karten für Positionen, die H15 nicht mehr führt.

**Kartenschlüssel = Bitpanda-Symbol** (Kurse liegen so in `price_cache`); ein Signal ohne Bitpanda-Gegenstück bekommt das Binance-Symbol mit Vermerk. Zuordnung über **eine** Funktion (`betriebslage.zuordnung_bitpanda`, `:338`); die beiden anderen (`spot_abbau._zuordnung`, `spot_upbit.zuordnung`) haben andere Bedeutungen und werden nicht gemischt (*vier Symbolwelten ohne Brücke*).

**Menge:** ~40 Bestände + **alle** Signale (Betrieb 03.10.–01.11.: 1.642, ≈ 55 je Tag; an Tagen mit > 60 Signalen mehr) → **100–200 Karten je Tag**, nicht 40–60. Die Statusseite zeigt deshalb **Bestände, Hebelpositionen und Signale mit `hebel_schalter = 1`** einzeln, die übrigen Signale gesammelt (Anzahl, aufklappbare Liste).

### 4.2 Fakt → Quelle → Lesefunktion

| Fakt | Lesefunktion | Lücke / Regel |
|---|---|---|
| Kurs mit Stand | `positionsfuehrung.kurs_mit_stand` (`agent/positionsfuehrung.py:140`) | – |
| Bestand, Einstand, Ergebnis | `bitpanda_avg_cost.compute_cost_basis_view(..., menge=frei+gestakt)` (`importer/bitpanda_avg_cost.py:262`) | ⚠️ ohne `menge` nur frei. Ergebnis heißt **„zum Schlusskurs“**, nie „realisiert“ |
| REGEL0-Signal | eigenes SELECT über `betriebslage.ro` (`:24`) | ⚠️ **nicht** `regel0_ablage.oeffne` (`:38`). `stufe_vorlaeufig` → `stufe` ändert sich nachträglich → Karte zeigt den Stand mit Zeitpunkt |
| Hebel | aus `hebelfuehrung.lade`: **nur** Liquidation, Abstand, `nahe_stufe`, Haltedauer | ⚠️ `stop_eur` und `empfehlung` hängen an `plan_zu` bzw. der **angehaltenen Rollen-Kette** (`:341-352`, `:380-404`) → **nicht anzeigen** |
| Binance-Ankündigungen | `binance_ankuendigungen.aktive(c, symbol, ende)` (`:185`) mit `ro`-Verbindung | ⚠️ **nicht** `oeffne`/`mailteile_aus_ablage` (`:131`, `:237`) |
| Upbit | **neu je Asset**: SELECT auf `upbit_fall`/`upbit_meldung` (`data/spot_betrieb.db`, `agent/spot_upbit.py:67-76`) über `spot_mitnahme._ro` (`:61`) | nur L-Bestände (ohne Kern, Stablecoins) — die Karte sagt das |
| Verwässerung | `verwaesserung.fakt(ordner, symbol)` (`agent/verwaesserung.py:180`) | NB: 90-T-Vergleich ggf. leer bis ~Dez. (G11) → „kein Wert (Reihe zu kurz)“ |
| Season-Ampel | `season_ampel.uebersicht(ordner)` (`:422`) | marktweit → einmal oben |
| Makro K1–K9, Lagebild L1–L7 | `makro_lage.stand`, `stand_gesamtmarkt` (`:256`, `:526`) | marktweit → einmal oben |
| Termin (O52) | `termin_fakt` (`:113/132`), fragt FRED **live** (`:56`) | der **Job** holt die Termine einmal und legt sie ab; der Sammler geht nie ins Netz |
| Sicht-Zustände | `zustaende.zustaende(T, Ablage())` (`agent/zustaende.py:295`) | marktweit → einmal oben; nur wenn `sichten.db` da ist (lädt 161 MB in den Speicher → nur einmal je Lauf) |

### 4.3 Form jeder Angabe — drei Zustände je Quelle

Je Fakt ein Datensatz `{schluessel, wert, satz, quelle, stand, alter, zustand, kennzeichen="Fakt"}`, `satz` in Satzform SF1/SF5. **`zustand` ∈ {`ok`, `leer`, `nicht abgefragt`}**: „keine Meldung“ darf nie wie „nicht abgefragt“ aussehen (`termin_fakt.py:15-16` kennt diesen dritten Zustand schon). Eine fehlende Quelle bricht die Karte nicht ab, ist aber **sichtbar** und wird gezählt.

**Ü8 in dieser Stufe:** *gleiche Form, nur vorwärts protokolliert* — ein Rückspiel mit damaligem Stand ist für Season und Makro nicht möglich (beide werden überschrieben).

### 4.4 Übergebbare Pfade

Mehrere Leser haben **feste Pfade**: `makro_lage.ABLAGE` (`:34`), `zustaende.ABLAGE` (`:28`), `hebelfuehrung.lade` liest die Haltedauer aus `_NL.DATEN_VORGABE` (`:536`), `season_ampel.uebersicht(None)` greift auf die Vorgabe zurück (`:425`). Der Sammler bekommt **einen** Datenordner und reicht ihn an jeden Leser weiter; wo ein Leser das nicht kann, bekommt er ein Pfad-Argument mit der heutigen Vorgabe als Standard (Betrieb unverändert). Ohne das läse ein Prüfstand „gegen Kopien“ teils die echten Dateien.

**Produktions-DB:** nur `mode=ro` mit `row_factory = sqlite3.Row` (wegen `hebelfuehrung.lade`) — **nie** über `db_conn_factory`/`db.get_connection()` (schreibend, WAL-Pragma, `database/db.py:633-639`).

---

## 5. B4 Job, B5 Statusseite und Mail

### 5.1 Job `asset_lage`

| | |
|---|---|
| Ablage | **eigene Datei** `data/asset_lage.db`: `lauf`, `karte` (Asset, Zeitpunkt, Anlass, Fakten-Stand), `fakt`, `befund_zuordnung`, `termin`, `marke` — Protokoll (P6, Ü6) |
| Tageskarten | täglich **07:45 Ortszeit** wie die anderen Tagesjobs (`scheduler/background.py:184`), Nachholen mit Versatz **≥ 600 s** (season_ampel nutzt 330 s) |
| Signalkarten | stündlich **:35 UTC**: alle `(symbol, signalstunde)`, die in `asset_lage.db` noch keine Karte haben. **Nicht über die Uhrzeit.** Ein Lesefehler (`locked`, Timeout) lässt die Marke stehen → nächster Lauf holt nach, kein Signal geht verloren |
| ehrlicher Verzug | die Signale schreibt die **Rechnung** nach dem Nachlader (normal ~7 Min., Monatstraining ~25, Grenze 50; `background.py:1781`) → Signalkarte **bis ~1 h** nach dem Signal. Die Signal**mail** betrifft das nicht (§5.3) |
| Nachgeholte Karten | Karte für ein Signal, das älter als 2 h ist, trägt „Fakten Stand X, Signal Y“ und das Kennzeichen `nachgeholt` → **nicht** in eine spätere Wertmessung (sonst Vorgriff) |
| Doppelläufe | `coalesce=True`, `max_instances=1` (Muster `:6010`); beide Jobs schreiben über **eine** Sperre |
| Schalter | `asset_lage_aktiv` in `regel0_betrieb.yaml`, Vorgabe **aus**; zusätzlich **Gerätebedingung im Helfer** (Muster `regel0_nachlader.betrieb_erlaubt`, `agent/regel0_nachlader.py:115`): sonst schaltet ein Pull ihn am Desktop mit ein |
| Fehler | `_notify_job_failure` (`:2783`); Lesefehler einer Quelle = Zustand der Angabe, kein Jobfehler |
| Abweichung vom Bauplan B4 | „nach jedem REGEL0-Lauf mit Signal“ wird zu „stündlich :35 UTC über den Schlüssel“ — Grund: kein Eingriff in `_regel0_rechnung_starten` (`:1786`, gibt `erg` nicht zurück) |

### 5.2 Statusseite

Neue Karte **„Asset-Lage“** nach dem vorhandenen Muster: Getter mit `@_gecacht_frist` (`remote/status.py:141`; der Cache-Wächter `teste_status_cache.py:176-190` findet jeden `_get_*` selbst), Feld in `RemoteStatus` (`:261`), `_safe` in `_build_status_roh`, `div.card` + JS in `remote/server.py`. Oben einmal **Markt** (Season, Makro, Lagebild, Termine, am Desktop Sicht-Zustände), darunter die Karten nach §4.1. Der Getter liest nur `asset_lage.db`.

### 5.3 Mail — Entscheid vom 28.10. (Weg 2)

Bauplan §8: *„Entschieden 28.10. spät: Weg 2, vorerst beide Blöcke“* (*„um eine stufenweise Ablöse und den visuellen Effekt zu sehen“*). Der Befundblock ist die **code-geprüfte Vorstufe von A3**; er kommt deshalb in die **REGEL0-Signalmail**, neben dem Trader-Block:
- höchstens **drei** Zeilen „im Geltungsbereich“ (nur Code-zugeordnet); „für den Strang“ nur auf der Statusseite;
- **neuer Mailteil** in `_regel0_mails` nach dem Muster der übrigen (`befunde=lambda r: …`, `background.py:1759-1767`), eine reine Funktion mit **derselben** Zuordnung wie die Karte, gerechnet zur Mailzeit (die Karte um :35 käme zu spät);
- das ist ein Eingriff in den **Mail**pfad, nicht in das Signal; geprüft mit den Paketen `Mail` und `Regel0Betrieb` und am Desktop mit echter Konfiguration.

Bestände ohne Handlung bekommen **keine** Mail (*jede Mail eine Handlung*).

---

## 6. B6 — Prüfen und Gegenprüfen

**Prüfstand = NB-Kopien im Wegwerfpfad** (`wegwerf.py`). Am Desktop fehlen `data/regel0_signale.db`, `data/spot_betrieb.db`, `data/makro_lage.json`; im Austauschordner liegen aber: `regel0_signale.db` (04.11.), `spot_betrieb.db` (01.11.), `umlaufmenge_cg.db`, die tägliche Sicherung `DB_Backups/tradinginfotool_2026-11-06_0632.db.gz`. Makro: ein Desktop-Lauf von `makro_lage.lauf` **in den Wegwerfpfad** (§4.4).

| Prüfung | Soll | Wie / Gegenprobe |
|---|---|---|
| **Paket `Befundkarte`** | jede Kennung existiert in `bestand.BEFUNDE` und **gilt** — eine **unbekannte Kennung ist rot** (nicht wie `pruefe_pakete.py:34834` still überspringen); `zahl` wörtlich im Befundtext; `gilt_wenn` nur mit Schlüsseln aus §3.3; kein Richtungsfeld, keine Zählung | Gegenproben: (a) Kennung abgelöst, (b) Kennung unbekannt, (c) `gilt_wenn` mit `signale_tag` oder `verw_fuenftel`, (d) Zahl um eine Stelle geändert → je rot |
| **Echte Fakten** | **je Quelle mindestens ein Fakt im Zustand `ok`** auf den NB-Kopien | Gegenprobe: eine Quelle entfernen → rot |
| **Seiteneffekt — Schreiben** | Eingangsdateien byte-gleich (SHA-256) | Gegenprobe: echter Schreibzugriff → rot |
| **Seiteneffekt — Öffnen** | jede `sqlite3.connect` ohne `mode=ro` wird gezählt (Ausnahme **genau** `asset_lage.db`, im Helfer nach Pfad) | Gegenprobe: `regel0_ablage.oeffne` auf vollständiger Datei — SHA bleibt gleich, der **Zähler** muss rot werden |
| **Seiteneffekt — neue Dateien** | Verzeichnisinhalt vorher = nachher (auch `-wal`, `-journal`, leere neue DB) | Gegenprobe: Leser auf fehlende Datei → neue Datei → rot |
| **Kein Zugriff außerhalb** | 0 Öffnungen außerhalb des Wegwerfordners | Gegenprobe: ein Leser mit festem Pfad → rot |
| **Kein Netz im Sammler** | 0 Netzaufrufe | Netz gesperrt; Gegenprobe: `termin_fakt` direkt → rot |
| **Drei Zustände** | `nicht abgefragt` ≠ `leer` je Quelle | je Quelle ein Fall |
| **Bestand = frei + gestakt** | Ergebnis gleich der Portfolio-Ansicht | ein gestakter Bestand |
| **Signalkarten** | jedes `(symbol, signalstunde)` genau eine Karte; Lesefehler → Marke bleibt | Gegenprobe: Sperre während des Laufs |
| **Zustände des anderen Geräts** | Karte entsteht ohne `sichten.db`, mit leerer Verwässerung, ohne Bitpanda-Schlüssel, und **am Desktop ohne Betriebsquellen** (alle Angaben `nicht abgefragt`, **sichtbar**) | je Zustand ein Prüffall (CLAUDE.md, Prüfungen Regel 1) |
| **Zuordnung Code gegen Hand** | gleich, Abweichungen einzeln | 20 Karten, **Handzuordnung durch eine zweite Instanz** |
| **Mail** | Befundblock ≤ 3 Zeilen, Pakete `Mail`/`Regel0Betrieb` grün | echte Konfiguration, Wegwerfpfad |
| **Standard-DB** | Paket `StandardDB` grün | wie immer |
| **NB-Kontrolle K-AL-1** | Job läuft, Tageskarte für alle Bestände < 26 h, **Signalkarte ≤ 90 Min. nach Signal**, Schalter wie gesetzt | neu in `nb_kontrollen.yaml`, Diagnose-Abschnitt `asset_lage` |

⚠️ **Was diese Prüfungen nicht zeigen:** dass die Karte bessere Entscheidungen bringt. Das wäre eine Wertmessung (Bauplan §6, eigener Messplan nach B3).

---

## 7. Der Weg zum NB

- **Ein** Bündel: B1, B2, B4, B5, B6, K-AL-1, Schalter aus → nach dem Pull einschalten → Diagnose.
- **G8a** (S-2, G14, Z-1) wartet laut Plan auf denselben Pull; ob der NB schon gezogen hat, ist hier **nicht geprüft**. Ist er es nicht, gehen G8a und G19 **gemeinsam**, mit einer Diagnose für K-W3-S2, K-G14-1, K-Z1-1 und K-AL-1.
- Dashboard und Bewertung sind von *Signale erst nach der ganzen Kette* ausgenommen, **nicht** von *Desktop zuerst* (E-169).
- **Nebenbei für E-170 F-A:** die Kopie `regel0_signale.db` vom 04.11. liegt schon im Austauschordner — die Erfolgsmessung kann damit bis 04.11. beginnen, eine frischere Kopie später.

---

## 8. Aufwand und Reihenfolge

| Schritt | Aufwand |
|---|---|
| B1 Datenmodell, Paket, **Auswahl aus dem Register** | ~1 Tag |
| B2 Sammler, Upbit-Leser, Vereinigung, **Pfade übergebbar** | ~1–1½ Tage |
| B4 Job + Ablage, B5 Statusseite + Mailteil | ~1 Tag |
| B6 Prüfstand auf NB-Kopien, Gegenproben, Gegenprüfung, Befundliste zur Vorlage | ~1 Tag |

---

## 9. Offene Frage

~~**Keine.** Die Mailfrage ist am 28.10. entschieden (Weg 2, §5.3); alles Übrige ist fachlich beantwortet. Vor dem NB-Bündel bekommst du die **Befundliste** (§3.2) zur Abnahme.~~

**Nachfrage des Nutzers 07.11.** (*„was hilft mir ‚im Geltungsbereich von E-139‘ oder ‚FOMC in 5 Tagen‘ …“*) → drei Möglichkeiten vorgelegt (1 Unterbau B2/B4 · 2 wie geplant · 3 zurückstellen), **entschieden 1** (E-171, Kasten oben). Die Befundliste und der Mailblock kommen mit B3.

---

## 10. Gegenprüfung (07.11.2026, unabhängig, nur lesend)

Fundstellen geprüft, bis auf einen Aufruf alle richtig; Registerzahlen und die Berichtigung „99 % = Anteil an der Differenz“ bestätigt. 20 Befunde, alle eingearbeitet:

| # | Schwere | Befund | eingearbeitet |
|---|---|---|---|
| 1 | **schwer** | Am Desktop fehlen fast alle Betriebsquellen; mit „scheitert nie“ wären alle Prüfungen an leeren Karten grün | §6 Prüfstand auf NB-Kopien, Prüfung „je Quelle ein echter Fakt“ mit Gegenprobe; §4.3 drei Zustände sichtbar |
| 2 | **schwer** | §1/§3.1 brachten Diagnosezahlen (netto, ohne Band, nur Referenz) als „Zahl“ auf die Karte; „nicht robust“ fehlte | §1 Spalte „lang“ und „nicht robust“; §3.1 nur registrierte Zahl, brutto |
| 3 | mittel | E-138 ist kein registrierter Befund; das zitierte Paketmuster überspringt unbekannte Kennungen still | §3.1 nur `bestand.BEFUNDE`; §6 unbekannt = rot |
| 4 | mittel | Befundblock in der Mail braucht einen Eingriff in den Mailpfad — widersprach „Signalweg unberührt“ | §5.3 offen benannt: neuer Mailteil, Pakete Mail/Regel0Betrieb |
| 5 | mittel | F-1 fragte die am 28.10. entschiedene Mailfrage neu | §5.3, §9: Weg 2 gilt, keine Frage |
| 6 | mittel | „Stopp“ angezeigt, aber `stop_eur` kommt aus der angehaltenen Kette | §4.2 nur Liquidation, Abstand, Stufe, Haltedauer |
| 7 | mittel | zwei Quellen für offene Hebelpositionen | §4.1 dieselbe Menge wie `hebelfuehrung.lade` |
| 8 | mittel | Kartenzahl unterschätzt (≈ 55 Signale/Tag) | §4.1 100–200, Statusseite gestaffelt |
| 9 | mittel | Takt über die Uhrzeit: Verzug, Sperre, Vorgriff bei Nachholen, Doppelläufe, Zeitzone | §5.1 Schlüssel, Marke bleibt bei Fehler, `nachgeholt`, coalesce, Versatz, Zeitzone |
| 10 | mittel | feste Pfade in mehreren Lesern — Prüfstand läse echte Dateien | §4.4, §6 „kein Zugriff außerhalb“ |
| 11 | mittel | Seiteneffekt-Nachweis: SHA allein erkennt `CREATE IF NOT EXISTS` und neue Dateien nicht; Öffner der Prod-DB offen | §6 drei Arme mit je eigener Gegenprobe; §4.4 nur `mode=ro` |
| 12 | mittel | „gilt hier“ zu stark; Feld `richtung` = Vorzeichen → Gewicht | §3.3 „im Geltungsbereich“; §3.1 kein Richtungsfeld |
| 13 | mittel | Schlüssel ohne Bezugszeitpunkt; `verw_fuenftel`/`season_stufe` problematisch; Ü8 nicht erfüllbar | §3.3 Tabelle mit Bezugszeitpunkt, beide gestrichen; §4.3 Ü8 zurückgenommen |
| 14 | leicht | Spur K-b mit E-138-Spur verwechselt (auch G18 §3.2) | §1, G18 berichtigt |
| 15 | leicht | falscher Aufruf `zustaende`; Sicht-Zustände sind marktweit | §4.2 |
| 16 | leicht | Cache-Wächter braucht keinen Eintrag; Paket heißt `StandardDB` | §5.2, §6 |
| 17 | leicht | drei Bitpanda↔Binance-Zuordnungen | §4.1 ein Kartenschlüssel, eine Zuordnung |
| 18 | leicht | Schalter in der yaml schaltet nach Pull auch den Desktop ein | §5.1 Gerätebedingung im Helfer |
| 19 | leicht | Auswahlregel schloss „nicht entscheidbar“ aus; K-AL-1 ohne Signalweg; Handprobe nicht unabhängig | §3.2, §6 |
| 20 | leicht | dritter Zustand „nicht abgefragt“ bei Termin/Ankündigung | §4.3, §6 |

---

## 11. Bau B2/B4 (07.11.2026, E-171) — was gebaut ist

| Teil | Datei | Kern |
|---|---|---|
| **B2 Fakt-Sammler** | `agent/asset_lage.py` (`sammle`) | Bestände ∪ Signale ∪ Hebel; je Asset Kurs (EUR aus `price_cache`, sonst je Signal der USDT-Kurs zur Signalstunde, getrennt gezählt), Bestand frei + gestakt mit Stand des Bitpanda-Abgleichs, Signal, Hebel (Liquidation, Abstand, Warnstufe, Haltedauer), Binance-Ankündigungen je Signalende, Upbit (nur L-Bestände), Verwässerung (mit P22b-Vermerk); Markt einmal: Season, Makro, Gesamtmarkt, Termine, am Desktop Sicht-Zustände. **Nur Zustandsteile** — die gemessenen Sätze der Mailzeilen bleiben weg (Befunde kommen mit B3) |
| **B4 Job** | `agent/asset_lage.py` (`lauf`, `stand`), `scheduler/background.py` (`asset_lage_job`, Jobs `asset_lage` 07:45, `asset_lage_signal` :35 UTC) | eigene Ablage `data/asset_lage.db`; jeder Lauf protokolliert (auch 0 Karten, Grund, Fehler); Signalkarten über `(symbol, signalstunde)`, **eindeutig** (Index) — der Tageslauf legt für ein Signal mit Karte keine zweite an; Angaben mit `bezug` nur auf der Karte ihres Signals; `nachgeholt` > 2 h |
| Schalter | `agent/regel0_groesse.py`, `regel0_betrieb.yaml` | `asset_lage_aktiv: false`; dazu Gerätebedingung `betrieb_erlaubt` |
| Pfade | `agent/hebelfuehrung.py` `lade(daten=…)`, `agent/verwaesserung.py` `fakt(zusatz=…)` | Vorgabe unverändert (Betrieb gleich) |
| Diagnose | `extract_notebook_diagnose.py` `_asset_lage` | Stand je Lauf, `fehler_24h`, Verzug, Schalter, Gerät |
| NB-Kontrollen | `nb_kontrollen.yaml` K-AL-1 (nach Pull, Schalter aus), K-AL-2 (nach Einschalten) | – |
| Prüfstand | `pruefstand_asset_lage.py`, Paket `AssetLage` | **26 Prüfpunkte** auf der Prüfgrundlage `Pruefgrundlagen/asset_lage_2026-11-04` (NB-Kopien 04./06.11., verkleinert auf 8,6 MB) |

**Nebenwirkungen im Betrieb, vollständig:** `data/asset_lage.db` (eigene Ablage) · `job_laeufe` und ggf. Misfire-Mail (wie jeder Job) · `api_health_status` beim FRED-Abruf der Termine (wie jeder FRED-Abruf). Der Tagesspeicher von `termin_fakt` behält einen Fehlschlag des Jobs **nicht**. Keine Mail, keine Anzeige.

**Offen, nicht blockierend:** keine Aufbewahrungsgrenze der Ablage (≈ 1,5 KB je Karte, ≈ 100 MB im Jahr) — vor B3 festlegen.

### 11.1 Code-Gegenprüfung (07.11., unabhängig) — 16 Befunde, alle eingearbeitet

| # | Schwere | Befund | eingearbeitet |
|---|---|---|---|
| 1 | **schwer** | Signalkarten doppelt: der Tageslauf (06:45 UTC) legte Karten für Signale an, die die Stundenläufe 00:35–06:35 schon hatten; der Prüfstand fuhr den Tageslauf zuerst und war blind | `schreibe` überspringt vorhandene Schlüssel, eindeutiger Index; Prüfstand in **Betriebsreihenfolge** |
| 2 | mittel | Lesefehler im Tageslauf brachen den ganzen Lauf ab | je Quelle `nicht abgefragt`; Lauf mit `fehler` protokolliert, Fehlermail |
| 3 | mittel | leere/gesperrte Stundenläufe ohne Protokollzeile → K-AL-2 fälschlich rot | jeder Lauf protokolliert; `fehler_24h`; K-AL-2 angepasst |
| 4 | mittel | „leer“, obwohl nicht im Prüfkreis (Nicht-Krypto, Upbit außerhalb L-Bestand, Termine teilweise, Verwässerung-Ausnahme) | alle `nicht abgefragt` mit Grund; Prüfpunkte |
| 5 | mittel | falscher Stand (Season „2“, Bestand `updated_at`, Ankündigung/Upbit Bezug statt Abruf) | Season-Datum, `bitpanda_holdings_synced_at`, letzter `*_lauf` |
| 6 | mittel | P22b-Vermerk ging verloren | `verwaesserung.fakt(zusatz=…)` |
| 7 | mittel | gemessene Sätze unter „Fakt“ (Makro, Season, Rhythmus) | nur Zustandsteile; Prüfpunkt |
| 8 | mittel | Signalkarten im Stundenlauf ohne Bestand/Hebel | gleiche Asset-Fakten in beiden Läufen |
| 9 | mittel | FRED-Fehlschlag des Jobs blieb im Tagesspeicher → REGEL0-Mail „nicht abgefragt“ | Fehlschläge aus dem Speicher entfernt; Prüfpunkt |
| 10 | mittel | USDT-Kurs verdeckte einen kaputten EUR-Weg; Entfernen-Gegenprobe fehlte; Sichten-Zweig ungeprüft | Kurswege getrennt verlangt; Gegenprobe je Quelle; Sichten-Fall |
| 11 | mittel | WAL-Produktion ungeprüft | Prüfpunkt mit offenem Schreiber im zweiten Prozess |
| 12 | leicht | Schalter-Arm hing an der echten yaml | im Prüfstand ausdrücklich gesetzt |
| 13 | leicht | Angaben mehrerer Signale auf jeder Signalkarte; negatives Alter unbemerkt | `bezug` je Signal; Auskunftszeile |
| 14 | leicht | Warnstufe aus Code statt yaml, Format, „jenseits der Liquidation“ fehlte | `nahe_grenze` aus yaml, % , Satz |
| 15 | leicht | „schreibt NUR asset_lage.db“ ungenau; FRED unter der Sperre | Docstrings vollständig; Abruf vor der Sperre |
| 16 | leicht | „Ergebnis zum Schlusskurs“ mit Live-Kurs; Fehlerzweig ohne Gesamtmarkt; Datei nicht geschlossen | „zum Kurs (Stand …)“; Gesamtmarkt im Fehlerzweig; `with open` |
