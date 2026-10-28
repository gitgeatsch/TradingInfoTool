# Voranalyse W-3: Die alte Spot-Kette stilllegen statt nur anhalten (27.10.2026)

> 🧭 **Laufender Plan:** [`Gesamtplan.md`](Gesamtplan.md) – Ziel, Betrieb, Vorhaben, offene Punkte und Dokumentenlandkarte.

Nutzer 27.10.: *„ja W-2 und W-3 Voranalyse starten, prüfen gegenprüfen und doku“*

**Grundlage:**
- eine Bestandsaufnahme im Code (nur gelesen);
- die tragenden Stellen selbst nachgelesen (✔ = von mir geprüft);
- der NB-Export vom 27.10. 07:51.

**Stehende Regeln:**
- *Stilllegung: wer SCHREIBT das noch?*
- *Umbau: prüfen, was FEHLT; Rücksprache vor dem Entfernen; keine Grundfunktion bricht.*

⚠️ **Nur Voranalyse.** Es wird nichts gebaut und nichts entfernt, bevor du entschieden hast.

## 1. Was die „alte Kette“ ist und was heute davon läuft

| Teil | Ort | läuft heute? |
|---|---|---|
| **Rollen-Kette** (`fuehre_umlauf` → `rollen_lauf.fuehre_lauf`: Rollen A/BC/G, Warteschlange, Auswahl, Vorfilter, Gate-Spur, Verkaufs-Sammelmail, Positions- und Hebelführung **in** der Kette) | `scheduler/background.py` Job `hebel_screening` (alle 15 min), Umlauf ab 5039; `scheduler/rollen_job.py`; `agent/rollen_lauf.py` | **nein**, angehalten seit 05.10. (✔ `background.py:5032-5038`) |
| **Älterer Weg** (Budget-Allocator, Multi-Asset-Batch 9/19 Uhr + Nachholen, `signal_batch`, alte Pipelines, Tranchen) | `background.py:5049-5136`, `5149ff`; `agent/krypto/*` | **nein**, gesperrt über `rollen_kette.aktiv_fuer` (alle 5 Gruppen) |
| GUI-Knöpfe der alten Pipelines („Signal berechnen“, „Fällige Signale“, Hebel „Jetzt analysieren“, Marktscan-Writeup) | `ui/signals_view.py`, `ui/hebel_view.py`, `ui/marktscan_view.py` | gesperrt über `alte_analyse_hinweis` (hängt ebenfalls an `aktiv_fuer`) |
| 07:15 `ausstiegs_job` (Stop nachziehen für alte Signale) | `background.py:849-966` | läuft, **mailt nichts**: NB 25.–27.10. *„keine Empfehlung offen“* (✔ NB-Log) |
| Ausstiegsverfolgung alter Signale | `ausstieg_verfolgung.py` (im 07:15-Job) | läuft aus: offen **85 → 68 → 50** (✔ NB-Log 25.–27.10.), fertig in ~3–4 T |
| Backward-Tracking 06:00 (Messung alter Signale) | `background.py:1205-1247` | läuft; misst bis 20 Handelstage nach dem letzten Signal |
| `lebendigkeit` 03:20 | Job `background.py:721` | läuft; nur die alte Kette liest es (kostet CoinGecko-Kontingent) |

**Was im selben Job `hebel_screening` heute zum NEUEN Betrieb gehört und bleiben MUSS:**
- Bitpanda-Hebel-Abgleich, Liquidationspreise, Wallet-Abgleich (P11), **Hebelführung H15** (`background.py:4901-4977`, vor dem Halt);
- ✔ **Wächter der Terminmarkt-Frische** `_pruefe_terminmarkt_frische` (`background.py:5018`). Er steht **im Zweig der alten Kette**, vor dem Halt; die REGEL0 braucht ihn (`open_interest_snapshot` für den LLM-Block).

## 2. Das Risiko HEUTE — warum Anhalten nicht reicht

| Ereignis | Was passiert (Code-Vorgaben, ✔ nachgelesen) |
|---|---|
| **`regel0_betrieb.yaml` unlesbar oder fehlerhaft** | `spot_kette_angehalten()` gibt im Zweifel **False** zurück (`regel0_groesse.py:137-143`) ⇒ die Rollen-Kette läuft **scharf** in allen 5 Gruppen wieder an: LLM-Aufrufe, NACHKAUFEN- und Sammelmails. **Zugleich** fällt A6 weg (`spot_mitnahme_aktiv` ⇒ False): Die 07:15-Mail führt wieder alte Spot-Zeilen, die B1-Mail ist aus. ⚠️ **Und H15 fällt aus**: `_hebelfuehrung_lauf` ruft `_G.lade()` ohne Rückfall auf (`background.py:4736`) |
| **Schlüssel `rollen_kette.aktiv_fuer` fehlt** in `config.yaml` | Vorgabe `()` (`rollen_job.py:45`, ✔) ⇒ der **ältere** Weg läuft wieder (Allocator, Multi-Asset-Batch), und die GUI-Knöpfe der alten Pipelines sind frei |

⇒ **Ein einziger Dateifehler** würde den als falsch gemessenen Weg wieder einschalten und gleichzeitig die echte Hebelführung abschalten. Das ist die eigentliche Lücke.

## 3. Wer liest, was die alte Kette schrieb (nach einer Stilllegung)

| Leser | wird | Bewertung |
|---|---|---|
| REGEL0, Messstand, Betriebslage | **unberührt**: lesen keine Tabelle der Kette | ✔ |
| `_regel0_spot_hinweis` (Satz in der REGEL0-Mail) | immer leer | harmlos |
| H15 `plan_zu` (liest Rollen-Signale) | Plan bleibt leer; REGEL0-Positionen brauchen ihn nicht (kein Stop/Ziel, die 24-h-Regel führt `haltedauer_text`) | ✔ kein Handlungsbedarf |
| Statusseite: Rollen-Topf, offene Signale, Sendezähler, Ausstieg | veraltet bzw. leer | Karte ausblenden oder „stillgelegt“ zeigen |
| GUI Signale-Tab, Watchlist-Tipp, Hebel-Tab Rollen-Signale | veraltet | Hinweis „stillgelegt“ |
| Diagnose `_rollen_kette` | veraltet | als Historie lassen |
| Module, die der neue Betrieb **mitbenutzt** | bleiben: `rollen_eingabe`, `gegenpruefer_rollen`, `positionsfuehrung.kurs_mit_stand`, `signal_mail`-Hilfen, `hebel_aggregat`, `ausstiegsrechnung`, `entscheidungsrechnung`, `assetklassen`, `kernwerte`, `toepfe`, `signal_abbildung`, `vorfilter`, `rollen_job` | **nicht löschen** |

## 4. Optionen (eine Entscheidung, mit Alternativen)

| | Umfang | Was wegfällt | Risiko |
|---|---|---|---|
| **S-1 harte Sperre (Vorschlag zuerst)** | (a) eine Code-Konstante `ALTE_KETTE_STILLGELEGT = True`: kein Umlauf, kein Allocator, kein Multi-Asset-Batch, GUI-Knöpfe zu, **unabhängig** von yaml und `aktiv_fuer` · (b) **H15 robust**: bei unlesbarer yaml mit den Code-Vorgaben weiter (Hebelführung an) · (c) der Wächter der Terminmarkt-Frische läuft **vor** jeder Verzweigung · (d) Statusseite und GUI zeigen „alte Kette stillgelegt (E-…)“ | **nichts, was heute läuft** (die Kette steht seit 05.10.). Code bleibt vorhanden, das ist umkehrbar | klein; Prüfstand am Seiteneffekt (Erweiterung von `pruefe_r4.py`): yaml kaputt ⇒ kein Umlauf, H15 läuft, Wächter läuft; `aktiv_fuer` weg ⇒ kein Allocator |
| S-2 Jobs abmelden (nach S-1) | Multi-Asset-Batch und Nachholen, `lebendigkeit` (nach Leser-Prüfung), danach 07:15-Job und Backward-Tracking, **sobald** die alten Signale fertig gemessen sind (~Anfang November) | Messung der Alt-Signale endet; CoinGecko-Kontingent wird frei | klein, aber jeder Job einzeln mit „wer liest das noch“ |
| S-3 Code entfernen | `rollen_lauf`, Rollen, Allocator, alte Pipelines | Code | ⚠️ groß: viele Module werden mitbenutzt; die Suite hat > 20 Pakete auf der alten Kette. **Nicht empfohlen**, solange S-1/S-2 den Zweck erfüllen |

**Suite bei S-1:**
- `Regel0Betrieb` (Reihenfolge Zweig < Halt < Umlauf < Allocator, `background.py`-Prüfungen um 32808) und `Abkapselung` / `GuiKette` (Sperre über `aktiv_fuer`) werden auf die neue Sperre nachgezogen.
- Die Pakete der Kette selbst (12c, 13, 15, Zellen …) prüfen Funktionen, die bleiben. Sie laufen weiter.

## 5. Offene Fachfragen (nicht Teil von S-1)

1. ~~H15-Plan für REGEL0-Positionen~~ **zurückgezogen (27.10., nachgelesen):** `plan_zu` sucht Stop und Ziel eines Signals der alten Kette, für *Schließen / Stop nachziehen / Hebel senken*. Die REGEL0 hat weder Stop noch Ziel, ihre Regel ist *24 h halten*. Die kennt H15 schon: `regel0_messstand.haltedauer_text` (E3, 18.10.) ordnet jeder Position ihr REGEL0-Signal zu (*„seit … h offen (Regel 24 h, überschritten) · REGEL0-Signal …“* bzw. *„eigene Entscheidung“*). Liquidation und Finanzierung laufen ohne Plan. **Für REGEL0-Positionen fehlt nichts.**
2. **Ende der Alt-Messung:** Backward-Tracking und Ausstiegsverfolgung sind nach den letzten 20 Handelstagen fertig. Danach können sie in S-2 abgemeldet werden.
3. `_melde_datenfrische` prüft auch Quellen, die nur die alte Kette brauchte. Bei S-2 dürfen keine Frische-Warnungen für abgemeldete Zulieferer kommen.

## 6. Gegenprüfung dieser Voranalyse

- ✔ selbst nachgelesen: Halt-Stelle und Wächter (`background.py:5005-5040`), `VORGABE_AKTIV_FUER = ()` (`rollen_job.py:45`), `bedient_neue_kette`, `_hebelfuehrung_lauf` mit `_G.lade()` (`background.py:4730-4740`), `spot_kette_angehalten` im Zweifel False (`regel0_groesse.py:137-143`).
- ✔ NB-Export 27.10.: 07:15 „keine Empfehlung offen“; Ausstiegsverfolgung offen 85 → 68 → 50; „Rollen-Kette ANGEHALTEN“ je Umlauf.
- Die Leserliste (§3) stammt aus der Bestandsaufnahme. Bei S-1 entfernt nichts einen Leser, deshalb reicht sie als Grundlage; bei S-2/S-3 wird sie je Job erneut nachgeprüft.

## 7. S-1 GEBAUT (27.10.2026; Nutzer: *„ja S-1 bauen - prüfen gegenprüfen und doku“*, E-164)

| Teil | Ort | Wirkung |
|---|---|---|
| **Feste Sperre** | `scheduler/rollen_job.py`: `ALTE_KETTE_STILLGELEGT = True`, `alte_kette_stillgelegt()`, `STILLGELEGT_TEXT` | gilt **unabhängig** von `regel0_betrieb.yaml` und `rollen_kette.aktiv_fuer`; zurück mit `False` (umkehrbar, der Code bleibt) |
| Umlauf und Allocator | `hebel_screening_job`: nach Abgleich, Wallet und H15 zuerst der **Terminmarkt-Wächter**, dann die Sperre (Log *„Alte Spot-Kette STILLGELEGT …“*) | kein `fuehre_umlauf`, kein `run_budget_allocator` |
| Multi-Asset-Batch | `multi_asset_batch_job` (damit auch das Nachholen beim Start) | übersprungen mit Logzeile |
| GUI-Knöpfe und Hinweis | `alte_analyse_hinweis`, `kette_angehalten_hinweis` | jeder Knopf der alten Pipelines gesperrt, auch ohne `aktiv_fuer`; der Hinweis *NICHT AKTUELL* nennt die Stilllegung |
| **H15 robust** | `_hebelfuehrung_lauf`: Ist die yaml unlesbar, gelten `regel0_groesse.VORGABE` (H15 an, Warnschwelle 15 %) | die Hebelführung echter Positionen fällt nicht mehr mit einem Dateifehler aus |
| Statusseite | `betriebslage.schalter()` erste Zeile `alte_kette_stillgelegt`; Schalter-Karte *„Alte Spot-Kette (W-3 S-1, im Code): stillgelegt“* | sichtbar |

**Prüfung am Seiteneffekt** (`Rechenkern_02_10/pruefe_w3_s1.py`, eigener Prozess, nur Modulwerte ersetzt) **8/8**:
- T1: yaml kaputt (Halt fällt auf False) ⇒ kein Umlauf.
- T2: `aktiv_fuer` leer ⇒ kein Allocator.
- T3: **umkehrbar**, mit der Konstante auf False läuft der Umlauf wie vor S-1, der Wächter genau einmal.
- T4: Konstante False und Halt an ⇒ wie R-4.
- T5: Batch übersprungen.
- T6: H15 läuft bei kaputter yaml mit den Vorgaben.
- T7: Knöpfe gesperrt ohne `aktiv_fuer`.
- T8: Statusseite zeigt es.

**Leser nachgezogen** (umgedeutete Regel: *keine feste Sperre* → *feste Sperre*):
- R-4 (`pruefe_r4.py`), die Sofortliste (S4/S5) und GuiKette (zwei Regelprüfungen) prüfen die Halt- bzw. Rückfall-Logik jetzt **bei aufgehobener Sperre**. Sie bleibt für den Fall der Umkehr gültig.
- Neu in GuiKette: *mit der festen Sperre ist jeder Knopf zu*.
- Neues Paket **W3Stilllegung**.

**Was wegfällt:** nichts, was heute läuft. Die Kette steht seit 05.10.

**NB:** K-W3-S1 im nächsten Pull.
