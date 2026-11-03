# Voranalyse G13 / W-3 S-2: Die Jobs der alten Kette (03.11.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) G13 · Vorlauf: [`Voranalyse_W3_Stilllegung_alte_Kette_27_10.md`](Voranalyse_W3_Stilllegung_alte_Kette_27_10.md) §4 (S-2) und §7 (S-1 gebaut)

Nutzer 03.11.: *„Ok, S-2-Voranalyse angehen"*

⚠️ **Nur Voranalyse.** Nichts wird gebaut oder abgemeldet, bevor du entschieden hast.

**Grundlage:**
- Registrierungen in `scheduler/background.py` (5743–6253), selbst gelesen;
- je Job die Leser im Code (Suche über `agent`, `api`, `database`, `remote`, `scheduler`, `ui`);
- NB-Diagnose vom **01.11.** (Log 29.10.–01.11., `joblaeufe`, `ausstiegs_empfehlungen`), Stand `fe1bf509`, also mit S-1.

**Stehende Regeln:** *Stilllegung: wer SCHREIBT das noch?* · *Umbau: prüfen, was FEHLT; Rücksprache vor dem Entfernen.*

## 1. Was die vier S-2-Jobs heute am NB tun (Log 30.10.–01.11.)

| Job | Takt | tut heute | schreibt | liest das noch jemand? |
|---|---|---|---|---|
| `multi_asset_batch` + Nachholer beim Start | Mo–Fr 9/19 Uhr | **nichts**: *„übersprungen – alte Kette STILLGELEGT"* (S-1). Der Nachholer meldet bei **jedem Neustart** *„fälliger Termin … hole sofort nach"* (zuletzt erledigt 14.08.) und überspringt dann | nichts | – |
| `lebendigkeit` | 03:20 | sammelt TVL für 45 Symbole (DefiLlama, 2 Abrufe/Tag); montags Entwicklerdaten (CoinGecko, **1 Abruf je Symbol ≈ 45/Woche**) | `lebendigkeit_beobachtung` | **nur `rollen_lauf`** (alte Kette, Mailsatz). Kein Leser im Betrieb; schon festgestellt in `Datenbasis_Schichten_Sichten_28_10.md` §5.7. Der Spot-Neubau (04.10., W3t) wollte für F9 ohnehin den **vollen DefiLlama-Verlauf je Protokoll**, nicht diese Tageswerte |
| `backward_tracking` + Nachholer | 06:00 | misst die **21 noch offenen Alt-Signale** (Spot); Hebel: **0** offen | `signals.outcome_*` | `ausstiegs_job` (s. u.), Statusseite-Karte, Diagnose. **Kein** REGEL0-Leser: die REGEL0 führt eine eigene Ablage (`regel0_ablage`: `lauf`/`signal`/`pruefung`) |
| `ausstiegs_empfehlungen` | 07:15 | rechnet Stop-Nachzieh-Empfehlungen für die 21; **mailt nichts** (A6 filtert alle 21 Spot-Zeilen, Hebel-Zeilen gibt es keine); schreibt `fuehrung_lauf` (21 Zeilen/Tag); Ausstiegsverfolgung: **10 offen, 0 gemessen** am 01.11. | `fuehrung_lauf`, `signals.ausstieg_*` | Statusseite-Karte „Ausstieg" (zeigt *„0 von 21"*). `fuehrung_lauf` hat **keinen** Leser im Code |

**Die 21 offenen Alt-Signale** (NB 01.11.): HYPE 15 · ASTER 5 · VSN 1, alle KAUFEN/NACHKAUFEN vom **26.08.–15.09.**

⚠️ **Korrektur zu W-3 §5.2:** Dort stand, die Alt-Messung sei *„nach den letzten 20 Handelstagen fertig"*. Für die **Ausstiegsverfolgung** stimmt das (Horizont H20). Für das **Backward-Tracking** nicht: ein Signal bleibt offen bis Ziel, Stop oder Ablauf, und der Ablauf ist **14/45/120 Tage** je Halte-Bucket, **90** ohne Bucket (`config.yaml` `backward_tracking`). Die 21 sind seit über 45 Tagen offen, also Bucket „lang" oder ohne Bucket. Nach dieser Regel enden sie **frühestens ~24.11., spätestens ~13.01.2027**. „Anfang November" war zu früh angesetzt.

## 2. Wer bricht, wenn sie wegfallen?

| Frage | Befund |
|---|---|
| REGEL0, Messstand, H15, Spot B1–B4, Season-Ampel | ✔ **unberührt**: REGEL0, Messstand, B1–B4 und C1 lesen weder `signals`/`hebel_signals`-Ausgänge noch `lebendigkeit_beobachtung`. ⚠️ **Berichtigt nach der Gegenprüfung (§7):** H15 liest sie doch. `hebelfuehrung.plan_zu` nimmt `signals.outcome_status`/`outcome_max_realisiertes_crv` eines **gekoppelten Alt-Signals mit `instrument='hebel'`** für *Stop nachziehen* bzw. *Schließen*. Folgenlos ist das, weil am NB **kein** solches Signal offen ist: Alle 21 offenen sind Spot (`tier krypto`, NB 01.11.: Backward-Tracking *„Spot: 21 geprüft"*, Hebel 0). Gekoppelt wird nur an Signale der letzten 24 h, und die alte Kette steht seit 05.10. REGEL0-Positionen führt H15 über `haltedauer_text` (W-3 §5.1) |
| Frische-Warnungen (W-3 §5.3) | ✔ **keine Fehlalarme**: `agent/datenfrische.py` REGISTRATUR hängt nur an `lagebild_reihen`, `makro_analog`, `externe_reihen` und den Kursreihen, an **keinem** der vier |
| **Statusseite, Job-Liste** | ⚠️ **ja**: sie färbt jeden Job „stale", dessen letzter Lauf älter als **26 h** ist (`remote/server.py:839-844`). Wird ein Job **abgemeldet**, steht er dort **für immer rot**. Ein Dauer-Rot erzieht zum Wegsehen |
| Statusseite, Karte „Ausstieg" | zeigt dann einen alten Stand; braucht „stillgelegt" |
| Mails | keine fällt weg: 07:15 mailt seit A6 nichts mehr |
| Kontingente | frei werden ≈ **195 CoinGecko-Abrufe/Monat** (montags 45) und 2 DefiLlama-Abrufe/Tag. Klein, aber ohne Gegenwert |

**Ausdrücklich NICHT abmelden** (geprüft, weil sie nach alter Kette klingen):

| Job | Grund |
|---|---|
| `makro_analog` 06:30 | schreibt `makro_historie_monat`, und die liest der **REGEL0-LLM-Block** (`regel0_llm.markt_eingabe` → `marktlage.beschreibe_lange_sicht`) |
| `lagebild_reihen` 06:40 | Netto-Liquidität, Zinskurve, F&G in `macro_snapshot`, ebenfalls REGEL0-LLM-Block + Frischeprüfung |
| `externe_reihen` 06:35 | u. a. Umlaufmenge (`umlaufmenge_cg.db`) und Coin-Metrics-Umlauf für `turnover` |
| `hebel_screening` | Abgleich, Wallet, H15, Terminmarkt-Wächter (W-3 §1) |

## 3. Was eine Messung bis zum Ende noch brächte

Die 21 offenen Alt-Signale stammen aus **zwei Assets in drei Wochen**: HYPE 15, ASTER 5, VSN 1. Nach dem Messregelwerk (Block max(15 T, 3×H), **< 20 Blöcke ⇒ KEIN BEFUND**) tragen sie **keinen Befund**, weder allein noch als Zuwachs zu einem bestehenden. Die alte Kette ist als **falsch** gemessen und seit 27.10. fest stillgelegt (E-164). Bis Januar weiterzumessen kostet nichts Spürbares, bringt aber auch nichts.

Für die **10 offenen Ausstiegsverfolgungen** gilt dasselbe. ⚠️ **Nicht geprüft:** warum am 01.11. keine davon fertig wurde. Bei Krypto wäre H20 seit spätestens 25.10. erreicht, falls die letzte Ausstiegshandlung um den 05.10. lag. Möglich ist, dass Börsentitel darunter sind (Werktage). Das klärt der nächste NB-Export, es entscheidet aber nichts.

## 4. Optionen (eine Entscheidung, mit Alternativen)

| | Umfang | Folgen | Risiko |
|---|---|---|---|
| **a) Im Job überspringen (Vorschlag)** | Wie bei S-1 der Multi-Asset-Batch: **eine Zeile am Jobanfang** `if rollen_job.alte_kette_stillgelegt(): log …; return`, und zwar in `lebendigkeit_job`, `backward_tracking_job`, `ausstiegs_job` und **in beiden Nachholern**. Die Nachholer prüfen **vor** ihrer Meldung „hole sofort nach". Karte „Ausstieg" auf der Statusseite: *„stillgelegt (S-2)"* | Registrierung bleibt ⇒ `job_laeufe` bleibt frisch, **kein Dauer-Rot**. Umkehrbar mit **derselben** Konstante wie S-1, ein Schalter für die ganze alte Kette. Die 21 Signale bleiben `offen` stehen (nichts wird umgeschrieben) | klein. Prüfung am Seiteneffekt als Erweiterung von `pruefe_w3_s1.py`: Konstante an ⇒ kein Schreibzugriff auf `signals`/`fuehrung_lauf`/`lebendigkeit_beobachtung`, keine CoinGecko-/DefiLlama-Abfrage; Konstante aus ⇒ alles wie heute |
| b) Abmelden (Registrierung entfernen) | `add_job` der vier und die zwei Nachholer streichen; Statusseite filtert die vier IDs aus der Job-Liste | gleiche Wirkung, dazu weniger Zeilen im Scheduler | mehr Änderungen (Scheduler **und** Statusseite), Umkehr nur per Code. Der Filter ist eine **Aufzählung**, die still veraltet (stehende Prüfregel 4) |
| c) Warten bis zum natürlichen Ende | nichts tun; die 21 laufen bis spätestens ~13.01.2027 aus, danach a) oder b) | Messung vollständig, aber ohne Befundwert (§3) | keins. Kostet zwei Monate Kontingent und Rechenzeit für nichts |

**Empfehlung: a).** Sie folgt dem Muster von S-1, ist mit derselben Konstante umkehrbar, erzeugt keinen Dauer-Alarm, und die verlorene Messung hat nach dem Regelwerk keinen Befundwert.

**NB:** Nicht dringend, denn S-1 sperrt das Gefährliche schon. Deshalb **ins nächste NB-Bündel (G8)**, nicht einzeln (*NB-Änderungen bündeln*). Bauen und prüfen kann ich am Desktop sofort.

## 5. Daneben gefunden: dieselbe Lücke wie W-3 §2, bei zwei ruhenden Funktionen

Sie gehören **nicht** zur alten Kette und deshalb nicht zu S-2. Sie haben aber dasselbe Muster: *„aus" hängt an einer Datei, im Zweifel „an"*.

| Funktion | aus über | im Zweifel | Folge bei Dateifehler |
|---|---|---|---|
| Kategorie-Synthese/-Vorschläge (#333, Thesen) | `regel0_betrieb.yaml` `thesen_pausiert` (O42) | **an** (`regel0_groesse.thesen_pausiert`: unlesbar ⇒ False) | täglich ein Gemini-Aufruf, Thesen-Abgleich, mögliche Mail *„schneller Wechsel"* |
| Marktscan + Erfolgsmessung | `config.yaml` `marktscan.aktiv: false` | **an** (`.get("aktiv", True)`) | CoinGecko-Scan 04:00/16:00, Mails *Kaufkandidat* / *Watchlist heiß* |

**Frage 2 (nur, wenn du willst):** Sollen diese beiden im Zweifel auf **aus** fallen? Das wären zwei Zeilen, umkehrbar. Ob die Thesen später wiederkommen, ist eine **fachliche** Frage (O42 sagt „pausiert", nicht „stillgelegt"). Deshalb schlage ich nur die **Vorgabe** vor, keine Sperre.

## 6. Gegenprüfung dieser Voranalyse

- ✔ Selbst gelesen:
  - Registrierungen und Nachholer: `background.py` 5879–5898, 6018–6035, 6243–6253.
  - Jobkörper: 721–753, 849–966, 1205–1247.
  - `_is_expired` mit den Vorgaben 14/45/120/90.
  - `thesen_pausiert` im Zweifel False.
  - Statusseite `JOB_ALT_MIN = 26 h`.
  - `datenfrische.REGISTRATUR`.
  - `regel0_llm.markt_eingabe` liest `makro_historie_monat`.
- ✔ Leser:
  - `lebendigkeit_beobachtung`: nur `agent/lebendigkeit.py` selbst und `rollen_lauf`.
  - `fuehrung_lauf`: nur der Schreiber.
  - REGEL0-Signale stehen nicht in `signals`/`hebel_signals`. Schreiber dorthin sind nur `db.insert_signal`, `db.insert_hebel_signal` (aus `hebel_pipeline`, gesperrt) und `signal_abbildung`.
- ✔ NB-Log 30.10.–01.11.: alle vier Jobzeilen wie in §1. 07:15 *„22/21 Spot-Zeilen nicht gemailt (A6)"*, *„keine Empfehlung offen"*.
- ⚠️ **Offen:**
  - Die NB-Daten sind vom **01.11.**, neuer gibt es keine.
  - Die 10 offenen Ausstiegsverfolgungen sind nicht erklärt (§3).
  - Messskripte am Desktop, die `signals.outcome_*` vom NB lesen, laufen auf **Kopien**. Sie verlieren nichts, solange keine neue Kopie gezogen wird.

## 7. GEBAUT (03.11.2026; Nutzer: *„Ok a und Frage 2 ja – bauen, prüfen, gegenprüfen und doku"*, E-166)

| Teil | Ort | Wirkung |
|---|---|---|
| **Jobs überspringen sich** | `scheduler/background.py`: `lebendigkeit_job`, `backward_tracking_job`, `ausstiegs_job` fragen am Anfang `rollen_job.alte_kette_stillgelegt()` (dieselbe Konstante wie S-1). Logzeile *„… übersprungen – alte Kette stillgelegt (W-3 S-2, E-166)"* | kein Abruf (DefiLlama/CoinGecko), keine Messung der Alt-Signale, keine Führung/Ausstiegsverfolgung, keine Mail. Die Jobs bleiben **registriert**: `job_laeufe` bleibt frisch, kein Dauer-Rot |
| 07:15 | `merke_joblauf` bleibt **vor** der Sperre (Nachholer); `load_config()` erst **nach** ihr (Gegenprüfung Befund 7) | eine kaputte `config.yaml` stört den stillgelegten Job nicht |
| **Nachholer beim Start** | `backward_tracking_catchup_if_missed`, `multi_asset_batch_catchup_if_missed`: Sperre **vor** DB-Zugriff und Meldung | Schluss mit *„hole sofort nach"* bei jedem Neustart (zuletzt erledigt 14.08.) |
| Statusseite | `remote/status.py::_get_ausstiegs_empfehlungen` rechnet nicht mehr; `remote/server.py` Karte und Kopf *„stillgelegt"* | keine Stop-Empfehlungen für Alt-Signale mehr (vorher 21 Zeilen HYPE/ASTER/VSN) |
| Diagnose | `extract_notebook_diagnose.py`: `lebendigkeit.stillgelegt`, `ausstiegs_empfehlungen.stillgelegt` (nur Auskunft), `marktscan_aktiv` mit Vorgabe AUS | der Export sagt, warum die Reihe endet |
| **Frage 2 Thesen** | `regel0_groesse.thesen_pausiert()` im Zweifel **True**; `VORGABE["thesen_pausiert"] = True` (wie die Datei) | yaml kaputt, fehlt oder ohne Schlüssel ⇒ Synthese/Vorschläge ruhen (kein Gemini-Aufruf, keine Mail) |
| **Frage 2 Marktscan** | `marktscan_job`, `marktscan_backward_tracking_job`: `(config.get("marktscan") or {}).get("aktiv", False)` | Abschnitt/Schlüssel fehlt ⇒ AUS; vorher AN bzw. KeyError mit Fehlermail |

**Prüfung am Seiteneffekt** `Rechenkern_02_10/pruefe_w3_s2.py` **14/14** (`pruefe_w3_s2.txt`):
- eigener Prozess, Wegwerf-DB auf D:, `db.DB_PATH` umgebogen;
- T1–T8: jeder Job und Nachholer mit der Konstante an ⇒ Zählwerk 0, `job_laeufe` vermerkt, keine Zeile *„hole sofort nach"*; mit der Konstante aus ⇒ alles wie vorher (**umkehrbar**). T5 sogar bei kaputter `config.yaml`;
- T9: Statusseite;
- T10/T11: Marktscan bei fehlendem, leerem, `None`- und `false`-Abschnitt aus, bei `true` an, Sperre frei;
- T12/T13: Thesen bei kaputter, fehlender und schlüsselloser yaml pausiert, mit `false` wieder an;
- T14: Standard-DB per sha256 über `.db` und `-wal` unverändert.

S-1 weiter **8/8**. Ins Suite-Paket **W3Stilllegung** aufgenommen (14/14 plus „Jobs bleiben registriert").

**Gegenprüfung** (unabhängiger Leser des Diffs, ohne meine Schlüsse): sieben Befunde, alle bearbeitet.

| # | Befund | erledigt |
|---|---|---|
| 1 hoch | `p14_pruefstand.py` S9 ruft den 07:15-Job und wäre jetzt rot (Suite-Paket SpotMitnahme) | S9 hebt die Sperre für den A6-Test auf (A6 gilt für den Fall der Umkehr); **10/10**. In der Suite vor der Korrektur tatsächlich rot gewesen |
| 2 mittel | T14 nur über Größe/Zeit der Hauptdatei, WAL übersehen; kein Wegwerfpfad | sha256 `.db` + `-wal`, `db.DB_PATH` umgebogen |
| 3 niedrig | §2 sagte, kein Leser im neuen Betrieb lese `signals.outcome_*`. H15 tut es für gekoppelte Hebel-Alt-Signale | §2 berichtigt: am NB keines offen (21 Spot, Hebel 0), Kopplung nur 24 h |
| 4 niedrig | Diagnose `marktscan_aktiv` mit Vorgabe True | auf False |
| 5 niedrig | `p10_pruefstand.py` T3/T4 erwarteten die alte Vorgabe (nicht in der Suite) | nachgezogen, **6/6** |
| 6 niedrig | Diagnose rechnet die Ausstiegs-Empfehlungen weiter | als Auskunft markiert (`stillgelegt`) |
| 7 niedrig | `load_config()` stand vor der Sperre | hinter die Sperre |

**Daneben in der Suite gefunden (nicht S-2):** `o54_pruefstand.py` M6 fiel, weil die Textmail heute *„Aktien-Angst (VIX)"* am Bindestrich umbricht. Der Vergleich machte daraus *„Aktien- Angst"*. Der Inhalt war gleich, nur der Vergleich nicht. Er ist jetzt unempfindlich gegen Bindestrich-Umbrüche, **8/8**.

**Was wegfällt:** die Messung der 21 offenen Alt-Signale (ohne Befundwert, §3), 10 offene Ausstiegsverfolgungen, die TVL-/Entwickler-Reihe (≈ 195 CoinGecko-Abrufe/Monat). Keine Mail, die heute ankommt.

**NB:** mit dem Bündel G8, Kontrolle **K-W3-S2**.
