# Bau-Voranalyse Kern-Regel (E-68/E-69) — 25.10.2026

Nutzer 25.10.: *„ja L1-a, L2-a und Kern-Regel Voranalyse starten“* · vorher: *„es sind kernwerte und wenn dann fallen diese aus der normalen spot regel raus nur diese ist bisher noch nicht zustande gekommen, prüfe welche Regel für kern zählt“*.

⚠️ **Nur Voranalyse.** Kein Betriebscode, bis du den Bauumfang (§6) abgestimmt hast. Gemessen ist die Regel schon (Spot §12.6–§12.10), beschlossen mit E-69. Es fehlt nur der Bau.

## 1. Die Regel (wie beschlossen, Spot §12.11 / E-69)

| Teil | Inhalt | Art |
|---|---|---|
| **Aufbau** | BTC/ETH/SOL **70/20/10**, monatlich gleicher Betrag; **Ausgleich über die Raten** (R1): die Rate geht zuerst in den untergewichteten Wert, **ohne Verkauf** (steuerneutral) | **Handlung**: Rate kaufen, mit Aufteilung |
| **Klima-Ampel** | Stufe in Worten (*Kapitulation · Bodenbildung · Wende bestätigt · Aufwärtstrend · überhitzt*) mit q und den drei Zutaten | Fakt |
| **K1-Hinweis Verkauf** | q war in diesem Zyklus über **0,90** und fällt unter 0,85 / 0,75 / 0,65 → *„Starke Überhitzung kippt – Teilverkauf erwägen (je ein Zehntel)“*, mit gemessener Wirkung (bis +16 % Stück 2017/2021, sonst wie Halten) und Vorbehalt *im Wesentlichen ein Ereignis (2021)* | Hinweis, du entscheidest |
| **Hinweis Rückkauf** | nach einem K1-Verkauf: in der Zone q ≤ 0,20 / 0,10 / 0,05 je ein Drittel des wartenden Geldes; nach 12 Monaten *„Rest kaufen“* | Hinweis, du entscheidest |

Kein Auslöser, keine automatische Handlung.

**Das Klima q** (`Spot_Voranalyse_04_10/k3_gewichten.klima`, aus **BTC** für alle drei Werte):
- Mittel aus drei Perzentilen im **wachsenden Fenster seit 2013**: MVRV · 1 − (Abstand zum Hoch ÷ Jahresschwankung) · Preis ÷ 200-Wochen-Schnitt (1.400 T).
- Bekannt am Tagesschluss t.

**Heute (Fakt, letzter Desktop-Stand 04.10.2026):** q = **0,38**. Im Jahr 2026 lag q zwischen 0,07 und 0,49; 2024 höchstens 0,86, 2025 höchstens 0,84. ⇒ **K1 ist seit 2021 nicht scharf** (q nie über 0,90). Ein Rückkauf-Hinweis entfällt, weil nichts verkauft wurde. Im Betrieb wäre heute nur der **Aufbau** wirksam.

## 2. Was schon da ist (bestehendes Schema zuerst)

| Bedarf | Vorhanden | Lücke |
|---|---|---|
| BTC-Kurs ab 2013 | `api/onchain.get_btc_full_price_history` (CoinMetrics, frei) | — |
| BTC-MVRV ab 2013 | `api/onchain` holt `CapMVRVCur` (bisher nur den **letzten** Wert, `page_size=10`) | Historie ab 2013 holen: **eine** Abfrage, ~5.050 Zeilen (am 25.10. geprüft: Status 200, 2013-01-01 bis 2026-10-24) |
| Speichern | `DB.schreibe_externe_reihe` (Job `externe_reihen`, schreibt schon CoinMetrics-Reihen) | neue Reihe `coinmetrics/btc_mvrv` |
| q rechnen | `k3_gewichten.klima` (Messcode) | als Betriebsfunktion übernehmen, **derselbe Code**; Nachbau-Prüfung Tag für Tag gegen die Messreihe |
| Kern-Bestand | Bitpanda-Bestand in der Betriebs-DB, **frei + gestakt** | je Wert in EUR zusammenführen (ETH/SOL sind teilweise gestakt) |
| ETH/SOL-Kurs EUR | Bitpanda/Binance-Kurse im Betrieb | — |
| Season-Ampel | `agent/season_ampel.py` (eigene Ampel, Altcoin-Phase) | getrennt halten: **andere Frage** (Season vs. Klima des Kerns) |
| Mail, Statusseite, Diagnose | bestehende Wege (`regel0_mail`, `remote/server.py`, `extract_notebook_diagnose.py`) | neuer Abschnitt *Kern* |

⚠️ **Datenquelle am NB:** CoinMetrics läuft dort schon (`btc_netto_boersenfluss`). Die neue Reihe ist dieselbe Quelle, nur eine weitere Kennzahl. Kein Download, kein Schlüssel, kostenfrei.

## 3. Wie der Bau aussehen würde (Vorschlag)

| Teil | Ort | Inhalt |
|---|---|---|
| Daten | Job `externe_reihen` (täglich 06:35) | BTC-Preis und MVRV ab 2013, **ganze Reihe je Lauf** (CoinMetrics revidiert selten, aber möglich; wie §49.5 der Season-Ampel) |
| Rechnung | neues Modul `agent/kern_regel.py` | `klima(p, mvrv)` (gleicher Code wie die Messung), `stufe(q)`, `k1_zustand(q)` (scharf / Stufe 1–3 ausgelöst / Zone), `rate(bestand_eur, betrag)` für die Aufteilung nach R1 |
| Mail **Kern-Rate** | einmal im Monat am Rate-Tag | **Handlung:** *„Kern-Rate X €: BTC a € · ETH b € · SOL c €“*, dazu als Zusatz die Ampel, die Abweichung vom Zielverhältnis und ggf. K1/Rückkauf |
| Mail **K1/Rückkauf** | nur bei Eintritt | *„Teilverkauf erwägen“* bzw. *„Rückkauf erwägen“*; eine Handlung, du entscheidest |
| Statusseite + Reiter Markt | laufend | Klima q, Stufe, drei Zutaten, K1-Zustand, Kern-Verhältnis Ist gegen 70/20/10 |
| Diagnose | NB-Export | Abschnitt `kern_regel`: q, Stand der Reihe, letzte Rate, K1-Zustand |
| Schalter | `config` | `kern_regel_aktiv` (Vorgabe **aus** bis zur NB-Kontrolle) |
| Prüfung | Suite-Paket `Kern-Regel` | Nachbau q gegen `k3_gewichten` (alle Tage gleich), R1-Aufteilung gegen `d_kern_teilverkauf.d1`, K1-Zustand an 2017/2021 nachgespielt |
| NB-Kontrolle | `nb_kontrollen.yaml` K-KR-1 | Reihe gefüllt ab 2013, q am NB = q am Desktop (±0,01), keine Mail bei Schalter aus |

⚠️ **Wechselwirkung mit REGEL0 und Hebel:** keine. Die Kern-Regel betrifft nur den **Spot-Bestand** von BTC/ETH/SOL. REGEL0 und Hebel auf dem Kern bleiben unverändert zugelassen (Nutzer 25.10., §8.0).

⚠️ **Die alte Spot-Kette** (NACHKAUFEN, Akkumulation) behandelt BTC/ETH/SOL heute noch als normale Spot-Werte. Mit dem Bau müssen sie dort **heraus**, sonst kämen zwei Kaufvorschläge für denselben Wert. Das ist ein Umbau: vorher prüfen, was dann fehlt, und mit dir abstimmen (Regel *Umbau: prüfen was fehlt*).

## 4. Offene Entscheidungen (deine)

| # | Frage | Warum sie deine ist | Mein Vorschlag |
|---|---|---|---|
| **K-1** | **Monatsrate in EUR** | Geldfrage, nicht messbar | — (du nennst den Betrag; die Regel braucht nur „gleich jeden Monat“) |
| **K-2** | **Rate-Tag** | Gemessen wurde der Monatserste. Ein anderer Tag ändert die Regel nicht messbar | Monatserster, Mail am Morgen |
| **K-3** | **Ausgleich auch für den Altbestand?** Liegt das Ist heute weit von 70/20/10, dauert der Ausgleich über die Raten lange | Steuer- und Geldfrage | nur über die Raten (wie beschlossen, ohne Verkauf); die Abweichung steht in jeder Mail |
| **K-4** | **Kern aus der alten Spot-Kette nehmen** (§3) | Umbau einer laufenden Funktion | ja, im selben Bündel; vorher die Liste, was dann fehlt |

## 5. Was die Regel NICHT kann (ehrlich)

- Sie ist gegen **100 % BTC** (M0, gleiche Raten) gemessen und liegt im Median gleichauf (Spot §12.6: 1,00 × M0, größter Rückgang um 3 Pp **größer** als BTC allein). Sie **schlägt den Markt nicht**, sie nimmt ETH und SOL mit geringem Zusatzrisiko dazu.
- K1 hängt im Wesentlichen an **einem** Ereignis (2021). Im ETF-Markt kam q nie über 0,90, K1 hätte nie gehandelt.
- Das Klima beschreibt, keine Kaufregel aus q schlug DCA (Spot §8.11, F1–F3). Deshalb ist q **Fakt**, kein Auslöser.

## 6. Bauumfang zur Abstimmung

| Stufe | Umfang |
|---|---|
| **B-1 (Vorschlag)** | Daten + q + Ampel auf Statusseite/Reiter/Diagnose, **ohne Mail**; Schalter aus. Nachweis am NB (K-KR-1) |
| **B-2** | Kern-Rate-Mail (Handlung) und K1/Rückkauf-Hinweis, nach K-1 bis K-3 |
| **B-3** | Kern aus der alten Spot-Kette nehmen (K-4), nach der Liste *was fehlt* |

Der Bau läuft getrennt vom Hebel (T-1 bis T-6) und wird mit dem nächsten NB-Pull gebündelt.

## 7. K-4 Bestandsaufnahme: Was die Spot-Seite heute für BTC/ETH/SOL tut (26.10.2026, nur gelesen)

Nutzer 26.10. (E-148): *„(b) nur K-4“*.

| Pfad | erzeugt für den Kern | heute schon ohne Kern? | läuft heute? |
|---|---|---|---|
| **Alte Rollen-Kette** (NACHKAUFEN/Akkumulation, Zelle `spot × akkumulation`; `rollen_lauf.py`, `assetklassen.py:262`) | Kauf-/Nachkaufsignale und Mails | **nein** | **angehalten** seit 05.10. (`regel0_betrieb.yaml:40 spot_kette_angehalten: true`, `background.py:5035`) |
| Rollen-Kette: Verkaufs-Sammelmail, Positionsführung je Symbol | Verkaufsurteile, Positionszeile (Einstand, G/V) | nein | angehalten (mit der Kette) |
| 07:15 Stop-Nachzieh-Mail (alte Spot-Signale) | Stop-Zeilen für offene alte Signale | über A6: mit `spot_mitnahme_aktiv` fallen **alle** Spot-Zeilen weg | Spot-Zeilen aus |
| B1 Mitnahme, B3 Upbit, B4 Abbau | nichts | **ja** (`spot_mitnahme.KERN`, `spot_abbau.SONDER`) | ja |
| C1 Season-Ampel | keine Handlung; BTC ist **Eingangsgröße** | Handlung ja | ja |
| alter Budget-Allocator, Tranchen, signal_batch | Kauf/Tranchen | nein | tot gelegt |

**Was NICHT berührt werden darf:**
- `asset_hebel_settings.hebel_pruefung_erlaubt`: REGEL0, Hebel-Mail und Hebel-Tab hängen daran.
- Watchlist-Einträge BTC/ETH/SOL: Kurse, Terminmarktdaten für REGEL0, H15, BTC-Vergleich in B1.
- `dca_erlaubt` ist **kein** Ausschalter. Abgeschaltet macht er aus dem Kern normale Spot-Einstiege **mit Stop**; das ist eine Falle.

**Befund:**
- Heute erzeugt die Spot-Seite **keine** Kaufvorschläge für den Kern: Die alte Kette steht, und B1/B3/B4 nehmen ihn schon aus.
- K-4 ist deshalb eine **Absicherung**. Sie wirkt nur, wenn die Kette wieder läuft.
- ⚠️ Das kann **ungewollt** passieren: `spot_kette_angehalten` gilt im Zweifel als *false* (`regel0_groesse.py:137-143`). Ist `regel0_betrieb.yaml` unlesbar, läuft die Kette wieder **und** A6 fällt aus. Dann kämen NACHKAUFEN-Mails für den Kern zurück.
- Eine zentrale Kern-Konstante gibt es nicht. Es gibt sieben verstreute Stellen, darunter `rolle: core` mit zehn weiteren Werten (anderer Begriff).

**Vorschlag K-4 (zur Abstimmung):**
- Eine zentrale Konstante `KERN = BTC, ETH, SOL`, auf die `spot_mitnahme.KERN` verweist.
- Ein Ausschluss **nur** in den Spot-Zellen der Rollen-Kette (`assetklassen`/`rollen_lauf`), weder über `dca_erlaubt` noch über die Hebelschalter.
- Positionszeilen des Kerns (Bestand, G/V) bleiben als Information.
- Suite-Prüfung: Kern erzeugt keine Spot-Zelle, Hebelzelle und REGEL0 unverändert.
