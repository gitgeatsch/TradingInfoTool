# Gesamtplan — TradingInfoTool

> **Der laufende Plan. Nur ZUSTAND: wie es heute ist und was als Nächstes kommt.**
> Angelegt 28.10.2026 (Nutzer: *„ja 1, neuer Gesamtplan – bau auf allen Ebenen einen Link-Verweis ein, damit wir die Pläne und Informationen immer finden und berücksichtigen können“*).
> **Fortschreiben heißt: den Zustand hier ändern, nicht unten anhängen.** Die Chronik steht in `Arbeitsstand_Schritt59.md`, die Entscheidungen in `Entscheidungen_Hebelneubau.md`, die Befunde im Register.
> Geprüft von `python pruefe_pakete.py --paket Gesamtplan`: Verweise vorhanden, Rückverweise gesetzt, Befunde gültig.

---

## 1. Ziel und die vier Regeln

> **Je Asset und Handlung eine neutrale, begründete Aussage über das POTENTIAL — wie viel ist hier zu holen, verglichen mit allem anderen.**

| # | Regel |
|---|---|
| 1 | Der Takt ist nie Signalgeber |
| 2 | Gebühren gehören nicht in die Bewertung (neutral, brutto; Kosten nachgelagert) |
| 3 | Kein Asset-Vorurteil, beim Hebel kein Asset-Rang; in der Mail ist der Stand des Assets erwünscht |
| 4 | Ein Fakt ist keine Begründung |

Prüffrage vor jedem Vorschlag: **Bewertung oder Fakt?** Im Wortlaut steht das in [`CLAUDE.md`](../CLAUDE.md), Abschnitt *Das übergeordnete Ziel*.

**Nutzerwort 28.10.2026, das den heutigen Plan bestimmt:** *„Auf Basis der Durchführung sicher nicht falsch. Aber mir fehlt die Intelligenz in der Bewertung – mit statischen mathematischen Berechnungen kommen wir nicht weiter.“*

---

## 2. Was heute im Betrieb läuft (Notebook)

| Teil | Stand | Schalter / Quelle |
|---|---|---|
| **REGEL0** (Hebel-Einstieg, stündlich, 24 h) | läuft seit 03.10., Mails seit Testwoche-Freigabe 10.10. ⚠️ **Vorwärtsprotokoll mit Vorbehalt**: die Festschreibung E-36 hält der Prüfung nicht stand, das Ergebnis hängt an der Datenlänge (E-136, `Bilanz_Gesamt_25_10.md`) | `regel0_betrieb.yaml` |
| **LLM-Prüfblock** in der REGEL0-Mail | Trader, gemini-3.5-flash-lite, 5 Stimmen, gemessen **„trennt nicht“** (N5) — bleibt vorerst in der Mail (Nutzer 28.10.: beide Blöcke, stufenweise Ablösung) | `regel0_llm.yaml` |
| **Hebelführung H15** + 24-h-/72-h-Erinnerung | läuft | `hebelfuehrung_aktiv` |
| **Spot B1** Mitnahme ×3 · **B3** Upbit-Listing · **B4** Abbau-Fünftel (Monatsstichtag) | laufen seit 12.–14.10. | `spot_*_aktiv` |
| **Season-Ampel** B1–B3 | läuft seit 18.10. | `season_ampel_aktiv` |
| **Binance-Ankündigungen** (Delisting, Monitoring) als Fakt | läuft seit 10.10. | `ankuendigung_aktiv` |
| **Makro-Lage** K1–K9, Lagebild L1–L7, DVOL, Termine, Verwässerung | als **Fakt** in Statusseite und Mails | `agent/makro_lage.py`, `termin_fakt.py`, `verwaesserung.py` |
| **Statusseite** | `remote/server.py` (Flask, Tailscale) | – |
| **Stillgelegt** | alte LLM-Kette (Rolle A, BC, Gate, Z1, Z.ai, Spot-Kette, Entscheider): E-164 · alter Hebelweg: E-46 | `scheduler/rollen_job.ALTE_KETTE_STILLGELEGT` |

Offene **Kontrollen am NB** stehen nur in [`nb_kontrollen.yaml`](nb_kontrollen.yaml) und auf der Statusseite.

---

## 3. Was gemessen gilt

**Nicht hier, sondern im Register.** Es wird aus `bestand.py` erzeugt und nie von Hand geändert.

| Frage | Blatt |
|---|---|
| Was gilt, was ist abgelöst? | [`REGISTER_Befunde.md`](REGISTER_Befunde.md) |
| Was ist auf welcher Basis registriert? | [`REGISTER_Kandidaten.md`](REGISTER_Kandidaten.md) |
| Welche Fakten (F-Nummern) gibt es, vor jeder Messung | [`REGISTER_Fakten.md`](REGISTER_Fakten.md) |
| Methodik nach Thema | [`REGISTER_Methodik_Themen.md`](REGISTER_Methodik_Themen.md) |
| Werkzeuge alt/neu | [`REGISTER_Werkzeuge.md`](REGISTER_Werkzeuge.md) |
| Gesamtbilanz aller Ansätze und Prüfbericht | [`Bilanz_Gesamt_25_10.md`](Bilanz_Gesamt_25_10.md) |
| Bilanz der LLM-Komponente (elf Wege) | [`Bilanz_LLM_Komponente_21_10.md`](Bilanz_LLM_Komponente_21_10.md) |

**Die Lage in drei Sätzen:**
1. Aus Kurs-, Terminmarkt- und Makrozahlen allein ist kein Vorsprung belegt, der die Prüfung übersteht. Zuletzt trug auch H-1 nicht (E-165-h1b/-h1c).
2. LLM-Urteile über **dieselben** Zahlen trennen nicht.
3. Die Information ist der Engpass, nicht die Rechnung.

---

## 4. Das Vorhaben: Intelligenz in der Bewertung — Ebenen, Sichten, Fragen

**Leitsatz:** *Das LLM erzeugt Information, die Messung bestimmt ihren Wert.*

### 4.1 Aufbau

| Ebene | Was | Wer |
|---|---|---|
| 0 Rohdaten | abgerufen | Datenquellen |
| 1 Zustände | berechnet, mit Einordnung (Perzentil, Abstand zum Normalen) | Code, **Fakt** |
| 2 Sichten S1–S8 | Zustände + Ereignisse je Bereich | Code + Ereignis-Leser A1 |
| 3 Gutachten je Sicht | einheitliches Schema: Zustand, Wirkung auf Krypto, Horizont, neu seit, eingepreist, Treiber mit Beleg, kippt wenn, Gegenargument | LLM, **ungeprüft** |
| 4 Finales LLM je Handlung | Bedenken-Stufe 0/1/2 + zwei Gründe + was umstimmt; dazu A3 Befund-Gedächtnis und A4 Gegenanwalt | LLM, geprüft vom Code; **entscheidet nicht**, Gewicht erst nach Messung |

**Sichten:** S1 Krypto gesamt · S2 Liquidität/Zinsen USA · S3 Risikoappetit · S4 Dollar/Rohstoffe · S5 Asien · S6 Staatsschulden · S7 Ereignisse · S8 Termine. **Entschieden 29.10.: S1–S4, S7 und S8 zuerst** (G2).

### 4.2 Die Dokumente des Vorhabens

| Dokument | Inhalt |
|---|---|
| [`Voranalyse_Dashboard_LLM_28_10.md`](Voranalyse_Dashboard_LLM_28_10.md) | Bestandsaufnahme, Expertenkonzept A1–A6, Prinzipien P1–P9, **Anbieter gemessen §1.5a** |
| [`Datenbasis_Schichten_Sichten_28_10.md`](Datenbasis_Schichten_Sichten_28_10.md) | Ebenen, Übergaberegeln Ü1–Ü9, Inventar abgerufen/berechnet/LLM-Bedarf, Sichten, **§3a Fragestellung je Sicht und finales LLM** |
| [`Voranalyse_Luecken_Prompt_Gesamtplan_28_10.md`](Voranalyse_Luecken_Prompt_Gesamtplan_28_10.md) | Lücken je Sicht mit Quellen (A), **Prompt-Umfang gemessen** (B), Entscheid zu diesem Plan (C/D) |
| [`Bauplan_Dashboard_A3_A4_28_10.md`](Bauplan_Dashboard_A3_A4_28_10.md) | Bauschritte B1–B6 (Befund-Karte, Fakt-Sammler, LLM-Rolle, Job, Statusseite, Prüfungen), Mail mit beiden Blöcken |
| [`Konzept_Lagegerechte_Handlung_27_10.md`](Konzept_Lagegerechte_Handlung_27_10.md) | REGEL0 bleibt Auslöser, die Schichten wählen das Wie |

### 4.3 Feste Randbedingungen (gemessen)

| | |
|---|---|
| Notebook | i5-4300U, 8 GB → **kein lokales LLM**; alles über freie Dienste |
| Betrieb | Gemini **Schlüssel 1** (NB), 500 Aufrufe/Tag **je Modell**; Prüfblock nutzt 3.5-flash-lite, das Vorhaben einen **eigenen** Modelltopf (3.1, Nachweis vor dem Einschalten) |
| Tests/Messungen | Desktop: Gemini **Schlüssel 2** (eigenes Projekt), Groq gpt-oss-120b und gpt-oss-20b (**je Modell** 1.000 Anfragen, 8.000 Token/min, 200.000 Token/Tag) |
| Prompt | Stufung ist Pflicht (Rohmeldungen direkt in eine Sicht ≈ 11.500 Token, über A1 1.100–2.000); finales LLM ≈ 3.000 Token; bei Groq **jede Anfrage ≤ 8.000 Token** |
| Kontamination | alle verfügbaren Gemini-Modelle kennen 2025 (3.5 bis ~Okt. 2025; die Modelle 2.5 sind für neue Konten gesperrt, geprüft 28.10.) → Rückspiel 2025 nur mit gpt-oss; ab Dez. 2025 Gemini möglich, **Wissensstand je Modell vorher prüfen** |

---

## 5. Offene Punkte und Reihenfolge — die eine Liste

| # | Punkt | Stand | Wer / Bedingung |
|---|---|---|---|
| **G1** | Dieser Plan, Verweise auf allen Ebenen | ✔ 28.10. | – |
| **G2** | **Sichten-Reihenfolge** | ✔ **entschieden 29.10.** (Nutzer: *„G2 und G3 wie empfohlen“*): **S1–S4, S7, S8 zuerst**; S5 Asien und S6 Staatsschulden danach | – |
| **G3** | **Modellwahl für das Rückspiel** | ✔ **entschieden 29.10.**: zuerst **Gemini (Schlüssel 2) Dez. 2025 – Okt. 2026** (~1 Woche), danach **Groq gpt-oss 2025** als zweiter Zeitraum und zweite Modellfamilie (~3–4 Wochen); vorher Wissensstand je Modell prüfen | – |
| **G4** | **Lücken schließen** (Nachweis je ein Abruf, dann einbinden): Nachrichten live am NB · KOSPI/Nikkei/DXY/MOVE (✔ nachgewiesen) · Bundesbank 10J (✔) · JGB 10J · Kimchi-Prämie · Coinbase-Prämie · Basis Quartalsfutures · ALFRED | **Nachweis für S1–S4, S7, S8 ✔ 29.10.** (`Voranalyse_Luecken…` **A2**): Coinbase-Prämie, Basis Quartal, ALFRED, HY ab 10/2023, 9 Feeds live, GDELT-Ton — keine blockierende Lücke mehr. Offen: **Einbinden** (Abstimmung) · für S5/S6 später: JGB 10J, Kimchi-Prämie, ECOS | Abstimmung Einbinden |
| **G5** | **ECOS-Schlüssel** (Bank of Korea) — Eintrag in `.env` leer | **zurückgestellt 29.10.: nur nice to have** — KOSPI/Won kommen über yfinance (✔N), die Kimchi-Prämie aus Upbit + Won; ECOS brächte nur Korea-Staatsanleihe täglich und amtliches M2 (S5, nicht in der ersten Reihe). ⚠️ Anmeldung verlangt laut BoK-Datenschutzblatt Name, Telefon, E-Mail; eine Drittquelle (Anbieter, unbestätigt) nennt **PASS-Prüfung mit koreanischer Handynummer** → für uns vermutlich nicht machbar | erst bei S5 neu bewerten |
| **G6** | Frankreich/Italien 10J **täglich** — kein freier Weg gefunden | Suche läuft weiter | – |
| **G7** | **Messplan** Faktentreue (Selbsttest der Prüfer, 1.000 Fälle) und Wert der Sichten (Rückspiel) | nach G2–G4 | Voranalyse → Abstimmung |
| **G8** | **Bau** B1–B6 + Ebenen 2/3, Mail mit beiden Blöcken | nach G7 | Abstimmung |
| **G9** | V1 Binance-Ankündigungen 2023–26 laden | ✔ geladen 28.10.: 6.276 Meldungen ab 01/2023, 4.097 mit Text (2 Texte nicht abrufbar), Katalog 93 nur Titel · `data/_a1/binance_ankuendigungen_alle.db` (`Rechenkern_02_10/a1_lade_binance.py`) · nächster Schritt: Voranalyse A1 (Regeln zuerst, LLM für den Rest, Stichprobe ~200) | – |
| **G10** | `soll_ist.py` (maschinelle Schrittliste, Paket Plan) ist seit 21.09. **nicht fortgeschrieben**: 29 offene Schritte, die meisten der alten Kette | als Historie kennzeichnen oder bereinigen | Rücksprache vor dem Entfernen |
| **G11** | Verwässerung am NB: 90-T-Vergleich vermutlich ohne Wert bis ~Dez. (Reihe ab ~08.09.) | ungeprüft | nächster NB-Export |
| **G12** | NB-Kontrollen ausstehend: K-W1-MAIL, K-W2-PUNKT (nächste Mail) · K-SP-3c, K-B4-D1 (nach 02.11.) · K-WC-1b (nächste H15-Mail) · **K-DA-1** (Datenausfall-Mail erst nach Nachprüfung, 29.10.; nach Pull + Neustart) | offen | `nb_kontrollen.yaml` |
| **G13** | S-2 Anfang November | nur nach Voranalyse und Ja | – |
| **G14** | Kern-Regel E-69 (BTC/ETH/SOL immer zugelassen) beschlossen, **nicht gebaut** | offen | Abstimmung |
| **G15** | Hebel-Phasen | [`Plan_Hebel_fuenf_Phasen_27_09.md`](Plan_Hebel_fuenf_Phasen_27_09.md) (wird maschinell gelesen) | – |

---

## 6. Feste Regeln der Arbeit

| Regel | Kurz |
|---|---|
| Ablauf | Voranalyse → Abstimmung (eine Entscheidung je Frage, mit Alternativen und Empfehlung) → Bau → prüfen, gegenprüfen, Doku |
| D vor L | erst die Daten und Fakten, dann die LLM-Rolle |
| Messstandard | `messnorm.standardzeile()`; Selbsttest ≥ 1.000 Ziehungen vor dem ersten Blick; Nullwelt tagestreu |
| R-R11 | erst reproduzieren, dann widerlegen |
| Grundgesamtheit | in Betrieb und Messung gleich |
| NB = Produktion | `data/tradinginfotool.db` am NB nie beschreiben, die Suite läuft nicht am NB, Prüfungen gegen eine Kopie |
| **Desktop zuerst** | eine Änderung geht erst an den NB, wenn ihre **Funktion am Desktop nachgewiesen** ist (Nutzer 09.08.: *„vor der PROD … Prüfung am Desktop“*; nachgetragen 29.10., fehlte in diesem Plan) |
| Labor allein ist FAIL | fertig ist erst, was am NB mit den dortigen Daten läuft — die **zweite** Hälfte derselben Reihenfolge: Desktop-Nachweis → NB-Betriebsprüfung |
| kostenfrei | nur freie Quellen und Dienste |
| Mail | jede Mail eine Handlung; Information nie nur in der GUI |
| LLM | Prüfung, nicht Entscheider; Fakt / gemessen / ungeprüft gekennzeichnet |
| Zwei-Jahres-Lösung | ist keine Option |

---

## 7. Wo alles steht — Dokumentenlandkarte

| Ebene | Dokument | Art |
|---|---|---|
| Einstieg | [`CLAUDE.md`](../CLAUDE.md) → **dieser Plan** | Regeln |
| Plan | **`Gesamtplan.md`** (dieses Blatt) | ZUSTAND |
| Übergabe / Chronik | [`Arbeitsstand_Schritt59.md`](Arbeitsstand_Schritt59.md) | Chronik, neuester Block unten |
| Entscheidungen | [`Entscheidungen_Hebelneubau.md`](Entscheidungen_Hebelneubau.md) (E-n) | Historie |
| Hebel | [`Plan_Hebel_fuenf_Phasen_27_09.md`](Plan_Hebel_fuenf_Phasen_27_09.md) · [`Regelwerk_Hebel_Bewertung_27_09.md`](Regelwerk_Hebel_Bewertung_27_09.md) | Zustand Hebel |
| Betrieb im Detail | [`Voranalyse_Schritt7_Betrieb_02_10.md`](Voranalyse_Schritt7_Betrieb_02_10.md) (§23.x) · [`Regelwerksmanual.md`](Regelwerksmanual.md) · [`Spezifikation.md`](Spezifikation.md) | Referenz |
| Spot | [`Voranalyse_Spot_Neubau_04_10.md`](Voranalyse_Spot_Neubau_04_10.md) · [`Plan_Asset_Lebenszyklus_14_09.md`](Plan_Asset_Lebenszyklus_14_09.md) | Referenz |
| Geräte | [`MEMORY_SYNC_STRATEGY.md`](MEMORY_SYNC_STRATEGY.md) | Zustand |
| Betriebsschalter | [`regel0_betrieb.yaml`](regel0_betrieb.yaml) · [`regel0_llm.yaml`](regel0_llm.yaml) · [`nb_kontrollen.yaml`](nb_kontrollen.yaml) | Zustand |
| **Alle Dokumente** | [`REGISTER_Dokumente.md`](REGISTER_Dokumente.md): **jedes** Dokument unter `Basisinfos/`, nach Art geordnet (Pläne, Messpläne/Vorabfestlegungen, Regelwerke, Entscheidungen, Konzepte, Voranalysen, Befunde), mit Einstufung laufend / Historie / vor Messstandard / Arbeitsblatt | **erzeugt** von `python dokumente.py` |
| Messpläne | [`Messplan_H1_Lagegerechte_Handlung_28_10.md`](Messplan_H1_Lagegerechte_Handlung_28_10.md) · [`Messplan_Indikator_Atlas_23_10.md`](Messplan_Indikator_Atlas_23_10.md) · die 33 Vorabfestlegungen im Register · viele Messpläne stehen als Abschnitt in [`Voranalyse_Schritt7_Betrieb_02_10.md`](Voranalyse_Schritt7_Betrieb_02_10.md) (§23.x) | Historie je Messung |
| Messstandard und Methodik | `messnorm.py` (`messnorm.standardzeile()`) · [`Test_und_Verifikationsmethodik.md`](Test_und_Verifikationsmethodik.md) · [`Regelwerk_Entscheidungslog.md`](Regelwerk_Entscheidungslog.md) | Zustand im Code |
| Fakten und Befunde | [`Fakten_Entscheidungsmappe.md`](Fakten_Entscheidungsmappe.md) · [`Befundkarte.md`](Befundkarte.md) · die fünf `REGISTER_*.md` (§3) | erzeugt bzw. Historie |
| Messwerkzeuge und Ergebnisse | `Basisinfos/Rechenkern_02_10/` (Skripte und `.txt`-Ausgaben) → [`REGISTER_Werkzeuge.md`](REGISTER_Werkzeuge.md) | – |
| **Historie — nicht fortschreiben** | [`Plan_Schritt59_Gesamtkette_17_09.md`](Plan_Schritt59_Gesamtkette_17_09.md) (bis Nachtrag 85) · [`Gesamtplan_Wo_wir_stehen_28_08.md`](Gesamtplan_Wo_wir_stehen_28_08.md) · [`Kette_Landkarte.md`](Kette_Landkarte.md) (alte Kette) | Historie |
| Memory | `MEMORY.md` → Zeile *Gesamtplan* ganz oben | Zeiger |
