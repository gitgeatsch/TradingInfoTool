# Gesamtplan — TradingInfoTool

> **Der laufende Plan. Nur ZUSTAND: wie es heute ist und was als Nächstes kommt.**
> Angelegt 28.10.2026 (Nutzer: *„ja 1, neuer Gesamtplan – bau auf allen Ebenen einen Link-Verweis ein, damit wir die Pläne und Informationen immer finden und berücksichtigen können“*).
> **Fortschreiben heißt: den Zustand hier ändern, nicht unten anhängen** — eine Zeile wird ersetzt, nicht verlängert (≤ 1.500 Zeichen). Der Verlauf steht in `Arbeitsstand_Schritt59.md` (ein Stand-Block je Paket, auch jede Übergabe an eine neue Sitzung — keine eigene Übergabedatei), die Entscheidungen in `Entscheidungen_Hebelneubau.md` (E-n), die Befunde im Register.
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

### 1a. Wie es zu diesem Plan kam (abgestimmt 06.11.2026, E-169)

| | |
|---|---|
| **Auslöser** | *„Kein Einstiegssignal mit belegtem Vorsprung, weder für Hebel noch für Spot“* ([`Bilanz_Gesamt_25_10.md`](Bilanz_Gesamt_25_10.md)): Spot-Kaufzeitpunkte schlagen regelmäßiges Kaufen nicht, Altcoin-Korb ab 2024 −57 % gegen BTC, REGEL0 hängt an der Datenlänge (E-136), der LLM-Prüfblock trennt nicht (N5). Nutzer 27.10.: Mails *„allgemein gehalten ohne Essenz“*, Signale *„offensichtlich zufällig“*, der Trichter *„eine starre Konstruktion“* |
| **Weggabelung** 21.–27.10. | **Ende?** (21.10.: *„wenn sich das als Deadend herausstellt, brauchen wir das System so nicht weiterverfolgen“*) → **Grid** geprüft: endet (E-127, Rückkehr zur Mitte ≈ zehnmal zu klein für die Gebühr) · **weiter optimieren** (23.–25.10.: REGEL0 *„noch nicht ausgereizt“*, Spot-Einstieg; M-L, E-A, H-A, L-1/L-2) · **umbauen** (27.10. „Lagegerechte Handlung“, [`Konzept_Lagegerechte_Handlung_27_10.md`](Konzept_Lagegerechte_Handlung_27_10.md), E-165: H-1 trägt nicht) · **andere Lösung: Dashboard** (27.10.: *„mit Informationen zum Markt, einzelnen Assets und u. U. sogar mit logischer und fachlicher Bewertung z. B. über LLM“*) |
| **Entscheidung** 28.10. | *„Das Dashboard mit Fakten und LLM-Bewertungen brauchen wir ohnehin“* + *„Intelligenz in der Bewertung“* → Weg a: Ebenen 0–4, Sichten aus Schichten und Ereignissen (§4) |

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
| **Stillgelegt** | alte LLM-Kette (Rolle A, BC, Gate, Z1, Z.ai, Spot-Kette, Entscheider): E-164, [`Voranalyse_W3_Stilllegung_alte_Kette_27_10.md`](Voranalyse_W3_Stilllegung_alte_Kette_27_10.md) · alter Hebelweg: E-46 | `scheduler/rollen_job.ALTE_KETTE_STILLGELEGT` |

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

### 4.0 Drei Stufen, drei Stränge (abgestimmt 06.11.2026, E-169)

| Stufe | Inhalt | Stand |
|---|---|---|
| **I Dashboard** | Fakten, Ampeln, Einordnung je Markt und Asset | teils im Betrieb (Makro-Lage, Season-Ampel, Statusseite); Asset-Karte und Befund-Karte **vorgezogen** (G19) |
| **II Bewertung** | LLM-Gutachten je Sicht | läuft (G7 Stufe 1–2) |
| **III Signale** | trägt die Bewertung — deterministisch und/oder über das LLM — für **unsere Signale**? | REGEL0/Hebel: G7 Stufe 3 + **Gesamtkonzept G18** |
| **Ausweichregel** | was nicht trägt, bleibt **Information** in Dashboard und Mail — nie Auslöser, nie Gewicht | gilt für jede Stufe (Beispiele: G16 Wale, Makro K1–K9) |

| Strang | Umfang | Wann |
|---|---|---|
| **1 Krypto · REGEL0 · Hebel · alle Assets** | **im Detail planen**, inkl. Dashboard | **jetzt** (G18, G19) |
| **2 Krypto · Spot** | Eckpunkte für die Roadmap: Unterschiede zu Hebel, Daten, Zeitraum, Berechnung, Bewertung (G20) | **umgesetzt erst, wenn Hebel trägt** (Nutzer: Spot hat nichts direkt mit der Hebel-Aufgabe zu tun) |
| **3 Multiasset** | dieselben Eckpunkte (G21) | **offen, erst wenn der Krypto-Ansatz trägt** — im System gänzlich anders zu handhaben |

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
| [`Fuetterung_Satzform_31_10.md`](Fuetterung_Satzform_31_10.md) | **Fütterung Weg a**: Satzform der Zustände SF1–SF8 (an echtem Tag geprüft), Befunde P1–P5, Ereignisse nur über A1, Blöcke des finalen LLM, Takt der Sichten, Reihenfolge, **Frage Historie** |
| [`Voranalyse_S1_Ergaenzung_01_11.md`](Voranalyse_S1_Ergaenzung_01_11.md) | **S1 ergänzen** (Fütterung §6 Schritt 2): Trend, Breite, Season-Stufe, DVOL, Stablecoins, Funding, OI — Quelle, Tiefe, Maß, live am NB; Befunde V1–V6; Ausführung und Nachweis §5; Breite in der Betriebsmenge zum Zeitpunkt §6 |
| [`Voranalyse_Zustaende_Modul_01_11.md`](Voranalyse_Zustaende_Modul_01_11.md) | **Ebene-1-Modul `agent/zustaende.py`** (Fütterung §6 Schritt 3): Umfang (35 Sicht-Zustände + S8 Termine), Befunde Z1–Z9, Bauplan, Prüfpaket, Nachweis N1–N5; Ausführung §7 |
| [`Voranalyse_G7_Messplan_02_11.md`](Voranalyse_G7_Messplan_02_11.md) | **G7 Messplan**: Faktentreue F und Wert W getrennt, Befunde G7-1–G7-7, Stufen 0–5 und Budget; Stufe 0 §7, REGEL0-Einstiege aus der Betriebsrechnung §10, Stufe-3-Anlage und Menge b §11 |
| [`Voranalyse_G7_Stufe1_04_11.md`](Voranalyse_G7_Stufe1_04_11.md) | **G7 Stufe 1** Sicht-Gutachten im Rückspiel: Vorabfestlegung §4 (S7 §4.1), Bau und Proben §5, Beschleunigungspaket §5.5 (Reihenfolge, je Hauptsicht einmal messen, Frist 30.11.), Gegenprüfung §6 |
| [`Voranalyse_G7_S7_Anlage_05_11.md`](Voranalyse_G7_S7_Anlage_05_11.md) | **S7 Ereignisse**: Messanlage und Selbsttest, Form d + Wort-Arm S7w (§4a/§4b, §6), Gegenprüfung §7 (Vorgriff P-1, Überlebensauswahl P-2 behoben, Band P96,5) |
| [`Voranalyse_Laufzeit_02_11.md`](Voranalyse_Laufzeit_02_11.md) | **Laufzeit verkürzen**: Gemini-Töpfe und Modelle je Schlüssel, A1 auf gemini-3.5-flash-lite (§5–§6), GDELT-Probe am NB (§7), A1 fertig und zweiter Weg gpt-oss (§8) |
| [`Voranalyse_A1_Ereignisleser_01_11.md`](Voranalyse_A1_Ereignisleser_01_11.md) | **A1 Ereignis-Leser** (G9): Quellen, Befunde A1-1–A1-10, Typkatalog, Bauplan; gebaut §7 (Weg b), Prompt 3 §9 |
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

> **Jede Zeile nennt nur den heutigen Zustand, das Nächste und den Verweis.** Der Weg dorthin steht im [`Arbeitsstand_Schritt59.md`](Arbeitsstand_Schritt59.md) (ein Block je Paket; die alte Fassung dieser Tabelle im Block *Stand 29.10.–06.11.2026*), die Begründungen in der Voranalyse. Eine Zeile wird **ersetzt, nicht verlängert** — höchstens 1.500 Zeichen, geprüft vom Paket `Gesamtplan`.

### 5.1 Offen

| # | Punkt | Stand heute | Nächstes / Bedingung |
|---|---|---|---|
| **G18** | ⭐ **Gesamtkonzept Strang 1** (Krypto · REGEL0 · Hebel · alle Assets): was sollen die Signale **deterministisch und über das LLM** besser liefern als heute — und woran messen wir das? Zielbild (E-169): **mehrere Regeln je Lage** für Einstieg, Führung, Ausstieg | **der wichtigste offene Punkt** (E-169) | ✔ **Voranalyse 06.11.** ([`Voranalyse_G18_Gesamtkonzept_06_11.md`](Voranalyse_G18_Gesamtkonzept_06_11.md)): Plus von REGEL0 an marktweiten Tagen (E-138); neue Regeln nur aus neuer Information (E-156) → Tageszustand und Ereignisse je Asset wählen, langsame Marktlage informiert · ✔ **entschieden 07.11. (E-170)** · Nächstes: Erfolgsmessung, sobald die NB-Kopie `regel0_signale.db` vorliegt; Katalog nach den ersten vollen Sichten (G7) |
| **G19** | **Dashboard und spezifische Bewertung vorgezogen** (Stufe I, Asset-Karte + Befund-Karte aus B1–B6) | entschieden 06.11. (E-169): unabhängig von G7, ausgenommen von *Signale erst nach der ganzen Kette* (§6) | ✔ entschieden 07.11. (E-170): B1, B2 (ohne Wal), B4–B6 am Desktop, dann ein NB-Bündel; B3 getrennt · Nächstes: Voranalyse Bau G19 |
| **G20** | **Strang 2 Krypto · Spot** — Eckpunkte für die Roadmap | zurückgestellt bis Hebel trägt (E-169) | Eckpunkte in G18 §8 |
| **G21** | **Strang 3 Multiasset** — Eckpunkte | offen bis der Krypto-Ansatz trägt (E-169); im System gänzlich anders zu handhaben | Eckpunkte in G18 §8 |
| **G7** | **Messplan**: Faktentreue der Prüfer und Wert der Sichten im Rückspiel | Stufe 0 ✔ 02.11. · **Stufe 1 läuft** seit 05.11.: 2.464 Gutachten, Reihenfolge S1, S3, S8, S7, S7w, S2, S4; **alle Prompts eingefroren seit 06.11.** (Probe 2 bestanden); Lauf `data/_g7_stufe1_lauf9.txt` in eigener Prozessgruppe, Laufwache täglich 08:00, Frist 30.11. · Stand je Stufe: **§5.2** · Grundlagen: [`Voranalyse_G7_Messplan_02_11.md`](Voranalyse_G7_Messplan_02_11.md) (Stufen, Budget) · [`Voranalyse_G7_Stufe1_04_11.md`](Voranalyse_G7_Stufe1_04_11.md) (Vorabfestlegung §4, Paket §5.5) · [`Voranalyse_G7_S7_Anlage_05_11.md`](Voranalyse_G7_S7_Anlage_05_11.md) · [`Voranalyse_Laufzeit_02_11.md`](Voranalyse_Laufzeit_02_11.md) | je Hauptsicht **einmal** messen (Stufe 2), sobald sie vollständig ist; Tageskontingent über das Anfragebuch `data/_g7/anfragen.csv` |
| **G8** | **NB-Bündel** | ✔ Voranalyse 03.11., entschieden **b** (geteilt): **G8a** = S-2 (E-166) + G14 (E-167) + Z-1 lokal mit Fassungsmarke (E-168), Ablauf eines Pulls Voranalyse §5 · **G8b** = Bau B1–B6 + Ebenen 2/3 (Dashboard-Teil vorgezogen → G19), Mail mit beiden Blöcken ([`Bauplan_Dashboard_A3_A4_28_10.md`](Bauplan_Dashboard_A3_A4_28_10.md)); Prüfer v2 ersetzt Z-1; GDELT-Abruf am NB mit zwei Wochen Nachweis (Laufzeit §7, vorher klären: kurzes Fenster = Viertelstundenwerte?, §7.4; sonst c neu vorlegen, G7 §9.2); S7 live mit Beständen (G7 §9.1); Wal-Fünftel als Fakt (G16) · [`Voranalyse_G8_NB_Buendel_03_11.md`](Voranalyse_G8_NB_Buendel_03_11.md) | G8a: Kontrollen K-W3-S2, K-G14-1 am NB · G8b: nach G7 und G18, eigene Abstimmung |
| **G4** | **Lücken schließen** | ✔ Nachweis für S1–S4, S7, S8 (29.10., [`Voranalyse_Luecken_Prompt_Gesamtplan_28_10.md`](Voranalyse_Luecken_Prompt_Gesamtplan_28_10.md) A2) · ✔ ein Abrufer `api/sichten_quellen.py` für Historie und laufend (Einbinden A), Desktop-Nachweis 7/7 am 30.10. (`g4_nachweis_sichtenquellen.py`: kein Vorgriff, live = Rückspiel) · Quellgrenzen: HY (ICE) erst ab 10/2023; GDELT 38 Tage Quellausfall und Sperre für Vielnutzer → 10 Min. Abstand, ein Wiederholversuch, sonst Quellausfall des Tages | NB-Einbau mit G8b · für S5/S6 später: JGB 10J, Kimchi-Prämie, ECOS (G5) · bei häufiger GDELT-Sperre im Betrieb: GKG-Rohdateien |
| **G5** | **ECOS-Schlüssel** (Bank of Korea) | **zurückgestellt 29.10.: nur nice to have** — KOSPI/Won über yfinance, Kimchi-Prämie aus Upbit + Won; ECOS brächte nur Korea-Staatsanleihe täglich und amtliches M2 (S5). ⚠️ Anmeldung vermutlich nur mit koreanischer Handynummer (PASS, Drittquelle unbestätigt) | erst bei S5 neu bewerten |
| **G6** | Frankreich/Italien 10J **täglich** | kein freier Weg gefunden | Suche läuft weiter |
| **G10** | `soll_ist.py` (maschinelle Schrittliste, Paket Plan) | seit 21.09. **nicht fortgeschrieben**: 29 offene Schritte, die meisten der alten Kette | als Historie kennzeichnen oder bereinigen — Rücksprache vor dem Entfernen |
| **G11** | Verwässerung am NB | 90-T-Vergleich vermutlich ohne Wert bis ~Dez. (Reihe ab ~08.09.), ungeprüft | nächster NB-Export |
| **G12** | NB-Kontrollen | die offenen stehen **nur** in [`nb_kontrollen.yaml`](nb_kontrollen.yaml) und auf der Statusseite — hier keine Aufzählung, sie veraltet | nach jedem Pull / NB-Export |
| **G15** | Hebel-Phasen | [`Plan_Hebel_fuenf_Phasen_27_09.md`](Plan_Hebel_fuenf_Phasen_27_09.md) (wird maschinell gelesen) | – |

### 5.2 G7 — Stand je Stufe

| Stufe | Inhalt | Stand |
|---|---|---|
| 0 | Prüfer v2, Messanlage, Vergleichsarm 0c (Zustände ohne LLM), Wissensstand der Modelle, Daten | ✔ 02.11. — Zustände allein tragen (15 Befunde), GDELT Aktienmarkt trägt, Gemini sauber ab Nov. 2025 (Messplan §7–§11) |
| 1 | Sicht-Gutachten je Tag, Dez. 2025 – Okt. 2026 | **läuft** (Voranalyse Stufe 1) |
| 2 | Wert je Sicht gegen die Zielgröße und gegen den Vergleichsarm 0c | je Hauptsicht, sobald vollständig |
| 3 | finales LLM je REGEL0-Einstieg, Menge b (903 gemailt + 1.532 Stichprobe, festgeschrieben `g7_stufe3_menge_b.csv`) | Anlage ✔ 02.11. (Messplan §11), Lauf nach Stufe 2 |
| 4 | Beitrag je Sicht mit/ohne | nur bei Befund in Stufe 2 |
| 5 | zweiter Weg: Groq gpt-oss auf 2025 (G3) — für H = 7/10 (S2/S4) und als Bestätigung | nur für das, was in Stufe 2/3 trug |

### 5.3 Erledigt

| # | Punkt | Ergebnis | Rest offen |
|---|---|---|---|
| **G1–G3** | Plan · Sichten-Reihenfolge · Modellwahl | ✔ 28./29.10. (Nutzer: *„G2 und G3 wie empfohlen“*): S1–S4, S7, S8 zuerst, S5/S6 danach (§4.1); Gemini (Schlüssel 2) Dez. 2025 – Okt. 2026, danach Groq gpt-oss 2025 als zweiter Weg (§4.3, G7 Stufe 5) | – |
| **G9** | Binance-Ankündigungen und A1 Ereignis-Leser | ✔ geladen 28.10. (6.276 Meldungen ab 01/2023) · A1 gebaut 01.11. (`agent/ereignisse.py`, Weg b, Prompt 3), **fertig 04.11.** (1.009/1.009, 25.561 Ereignisse; zweiter Weg gpt-oss 78,9 % gleich, deckt Weg b nicht) · [`Voranalyse_A1_Ereignisleser_01_11.md`](Voranalyse_A1_Ereignisleser_01_11.md), Laufzeit §8 | Stufe 1 weist Weg b getrennt aus · Nutzer: Gegenprüfung der Handeinordnung (V4, drei Dateien) |
| **G13** | S-2 Jobs der alten Kette | ✔ gebaut 03.11. (E-166): Jobs überspringen sich, Thesen/Marktscan im Zweifel aus · [`Voranalyse_S2_Jobs_alte_Kette_03_11.md`](Voranalyse_S2_Jobs_alte_Kette_03_11.md) | NB: K-W3-S2 (G8a) |
| **G14** | Kern-Regel, „Kern immer zugelassen“ | ✔ gebaut 03.11. (E-167): Rückfrage beim Ausschalten, Warnzeile, Schalter-Lesefehler als Fehlermail, eine Kern-Liste; Aufbau = Sparplan (E-148, K-4 gebaut E-152) · [`Voranalyse_G14_Kern_Regel_03_11.md`](Voranalyse_G14_Kern_Regel_03_11.md) | NB: K-G14-1 (G8a) |
| **G16** | Wal-Verhalten | ✔ abgeschlossen 31.10.: Spot 1 Tag trug knapp auf 6 Altcoins, auf 138 neuen Altcoins **nicht trennbar** → vermutlich Glück; **trägt nicht als REGEL0-Gewicht**; keine weitere Wal-Messung ohne neue Begründung · [`Voranalyse_Wale_29_10.md`](Voranalyse_Wale_29_10.md) · [`Messplan_Wale_29_10.md`](Messplan_Wale_29_10.md) §10–§19 · [`Voranalyse_Wale_Stufe2_31_10.md`](Voranalyse_Wale_Stufe2_31_10.md) | in Weg a eingereiht: Fünftel als Fakt in der Asset-Karte (nur oben/unten), Eintrag in der Befund-Karte A3 als Bremse, Wert per Rückspiel mit/ohne; NB-Abruf 32 MB/Tag mit G8b |
| **G17** | R-R11-1 rot (10.735 statt 10.732) | ✔ gelöst 03.11.: ein gekipptes Bit im Arbeitsspeicher (Windows-Dateicache), nicht Code, nicht SSD; seitdem prüft das Paket `Kursdateien` die vier Kursdateien bitgenau gegen das Manifest · [`Voranalyse_G14_Kern_Regel_03_11.md`](Voranalyse_G14_Kern_Regel_03_11.md) §7 Nachtrag | Speichertest am Desktop (Nutzer) |

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
| **Signale erst nach der ganzen Kette** | eine Änderung an **Signalen** (z. B. REGEL0, Hebel, Spot) geht erst an den NB, wenn **alles** am Desktop gebaut und nachgewiesen ist (Nutzer 06.11., E-169; Nutzer 27.09.: *„die ganze Ablaufkette … inkl. LLMs und Rollen“*). **Ausgenommen: Dashboard und Bewertung** — Information ohne Auslösung, sie dürfen vorgezogen werden; für sie gilt nur *Desktop zuerst* |
| **Ausweichregel** | was nicht trägt, bleibt Information in Dashboard und Mail (§4.0) |
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
| **Historie — nicht fortschreiben** | [`Plan_Schritt59_Gesamtkette_17_09.md`](Plan_Schritt59_Gesamtkette_17_09.md) (bis Nachtrag 85) · [`Gesamtplan_Wo_wir_stehen_28_08.md`](Gesamtplan_Wo_wir_stehen_28_08.md) · [`Kette_Landkarte.md`](Kette_Landkarte.md) (alte Kette) · [`Uebergabe_Sitzung_04_11.md`](Uebergabe_Sitzung_04_11.md) (Übergabe 04.11.; seit 06.11. stehen Übergaben im Arbeitsstand) | Historie |
| Memory | `MEMORY.md` → Zeile *Gesamtplan* ganz oben | Zeiger |
