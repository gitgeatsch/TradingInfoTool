# Arbeitsstand Schritt 59 – lebende Übergabe

**Zweck:** Ein Sitzungswechsel soll jederzeit ohne Vorbereitung möglich sein (Nutzerentscheidung 17.09.2026: Sitzung stabil halten, Übergabe parallel mitziehen, Probelauf einer neuen Sitzung nach Phase 0). **Aktualisiert am Ende jedes Pakets.**

**Stand:** 18.09.2026 · letzter Commit `e02e9e5` (Phase 1 vollständig: 1.1–1.7) · am NB gepullt und neu gestartet · ⚠️ **Nutzer unterwegs, Verbindung unsicher** – Arbeiten laufen am Desktop, die Notebook-Kontrollen **K14, K16, K17, K6, K11a** werden beim nächsten Pull **gebündelt** geprüft

## Zuerst lesen (in dieser Reihenfolge)

1. Memory `feedback_arbeitsliste_fehler_und_ablauf.md` – Ablauf je Paket und die Fallen, die schon passiert sind
2. `Basisinfos/Plan_Schritt59_Gesamtkette_17_09.md` – der abgestimmte Plan (§ 1 Bewertungsstand, § 1a Krypto zuerst, § 3/3a LLM-Rollen und Basisdokumente, § 6 Phasen, § 6a Stillstand, § 8 Entscheidungen)
3. Memory `project_schritt59_gesamtkette_messen.md` und `project_ausstehende_nb_kontrollen.md`
4. `Basisinfos/Rollout_Notebook_14_09.md` – was am Notebook woran zu erkennen ist

## ⭐ Das Ziel: Meilenstein M1 — Krypto-Einstieg investierbar

**Nutzerdefinition 18.09.:** technisch stabil · fachlich gemessen · rudimentäre Wirksamkeit belegt — **dann** wieder investieren. Priorität: der **Einstieg** (Spot, Hebel, Akkumulation), durchgängig über deterministische Komponenten **und** LLM. Sieben Abnahmekriterien in `Plan_Schritt59` § 11, als Vorgabe `M1-KRYPTO-EINSTIEG` in `soll_ist`.

⚠️ **Der Engpass ist das LLM-Kontingent** (2.459-llm-budget): 500/Tag je Modell, der Betrieb braucht im Mittel 245 (Spitze 565 — über der Grenze). Ohne Produktionsstillstand ist die LLM-Messung nicht planbar. Zuerst ein **Kalibrierlauf** (50 Anker, halber Stillstandstag), dann wird der Hauptlauf dimensioniert (**N13**).

**Weg:** Phase 3 (Spot) → Phase 4 (Hebel) → Phase 8 gepaart (A/B/Zufall) → Phase 9 → Schritt 60 → Abnahme M1. Akkumulation läuft parallel. **Nicht** auf dem Weg: Ausstieg, Nicht-Krypto, Multiasset.

## ✔ Betriebsvorfall 20.09. — die Netzaussetzer sind erklärt

**Es war die Diagnose, nicht der Pull** (2.484-ursache). Der Nutzer hat es getrennt geprüft: *Pull ohne Diagnose blieb ruhig*. 295 MB Upload auf einen Drive-Ordner sättigen die Leitung; die Abrufe der laufenden Anwendung scheitern am 15-Sekunden-Zeitlimit — Terminmarkt 4/43, +48 Jobfehler.

✔ **Gebaut** (2.484-schlank): Diagnose **schlank als Vorgabe** (~8 MB statt 295), `--voll` für Messskripte, Lesehelfer mit lesbarer Meldung, drei Wächter gegen das Vergessen. Paket Diagnoseumfang 20/20, 9 Mutationen · ⚠️ **kein Laufzeitmodul** — Pull genügt, kein Neustart · ⏳ **K26**: ist die nächste Diagnose rund 8 MB, und bleiben die Timeouts aus?

## ⚠️ Betriebsvorfall 19.09. — sechs Stunden Stillstand

Die Anwendung war **14:06–20:29 lokal** weg (2.482-stillstand). Vier Spuren brechen im selben Fenster ab; die letzte Protokollzeile ist ein **erfolgreich** beendeter Job — kein Fehler, kein Traceback. Der Prozess wurde **von außen** beendet.

⚠️ **Offen und nur am Gerät zu klären:** das **Windows-Ereignisprotokoll (System)** des Notebooks um **14:06 lokal**. Standby, Neustart oder Speichermangel? Der Nutzerhinweis auf einen **Netzwerkausfall am Nachmittag** erklärt die Timeouts, aber **nicht** den Stillstand — möglich ist eine gemeinsame Ursache (Ruhezustand).

✔ **Gebaut**: Laufzeitwächter im `staleness_watchdog` (2.482-waechter, Schwelle 45 min, eine Meldung je Lücke, Spur in `api_health`) · Marktrang-Zähler in der Diagnose (2.482-marktrang) · Paket Laufzeitwächter 12/12, 9 Mutationen · ⚠️ **Laufzeitcode: NB braucht Pull UND Neustart**, danach **K25** (kommt beim nächsten geplanten Neustart eine Stillstandsmail?)

## Wo wir stehen

| Paket | Stand |
|---|---|
| **Phase 3 Punkt 3 – Stufe `auswahl`** | ⛔ **gemessen 19.09.** (2.479): keine Zelle trägt; bei H20 ist die Anlage zu grob (0,40 R), bei H5 löst sie auf und die Wirkung liegt darunter. ➔ Mengensteuerung, kein Qualitätsfilter. ⚠️ Zwei eigene Aufbaufehler gefunden (2.479-eigene-fehler: Träger filterte die Ankermenge, Bezug waren alle statt der Wählbaren). Paket Auswahlstufe 10/10, 10 Mutationen · ✔ **`entscheider` gemessen** (2.480): **+0,2137 R → TRÄGT**, auch gegen die strengere Nullwelt aus den Bewertbaren; Datenlagenanteil +0,0461 R; 8 von 8 CRV-Werten. Paket Entscheiderstufe 12/12, 10 Mutationen · ✔ **`terminmarkt` belegt** (2.481): Größe registriert, **Stufe im Betrieb fast wirkungslos** (4 von 508 Zeilen) und **nicht protokolliert**. Paket Terminmarktstufe 6/6, 7 Mutationen · ✔ **Punkt 3 vollständig** · ⏳ offen: Punkt 5 (die vier ungemessenen Größen) · ✔ **Umsetzung gebaut 19.09.**: `terminmarkt` in `PROTOKOLL_IMMER` **und** in `NUR_EINMAL_JE_TAG` (höchstens eine Zeile je Symbol und Tag) · ⚠️ **Laufzeitcode: NB braucht Pull UND Neustart**, danach Export und Kontrolle **K21** (steht eine `terminmarkt`-Zeile in `zellen_lauf`, oder bleibt sie zu Recht leer?) |
| **Phase 3 Punkt 5 – die vier ungemessenen Größen** | ✔ **erledigt 20.09.** (2.483): `referenz_spy` **nicht trennbar** — im Querschnittsrang **rangidentisch** mit der reinen Kursrendite (0,999999), der Marktabzug kürzt sich weg. `fundamental_wachstum` → Multiasset. `stablecoin_kapital` und `optionsmarkt_dvol_skew`: **34 Punkte**, Warten hülfe bis 2029 → **Historie beschaffen** (Schritt 65). Paket Referenzstärke 9/9, 8 Mutationen · ✔✔ **PHASE 3 IST DAMIT VOLLSTÄNDIG** |
| Plan, Entscheidungen N1–N11, D1–D4 | ✔ abgestimmt |
| 0.6 Sperrzeiten am NB | ✔ belegt (Krypto 12 h, gehebelt ab 2x 3,5 h, Multiasset 24 h, G = Z.ai) |
| 0.8 Stillstand und Abgrenzung (Recherche) | ✔ Befunde 2.456-llm-pause, 2.456-etf-knopf, 2.456-abgrenzung |
| 0.9 ETF-Knöpfe gesperrt | ✔ gebaut `e45aa26` · am NB aktiv · ⏳ K13 Oberflächenblick (Nutzer) |
| 0.7 + 0.10 Kennzeichnung und `signals.gruppe` | ✔ gebaut `03e5724` · am NB: Spalte da, Drift leer, keine Fehler · ⏳ K14 erste gekennzeichnete Mail |
| 0.4 Messskripte nur lesend (E1: alle acht) | ✔ gebaut (2.457-nurlesend) · Paket NurLesend 18/18  · ✔ Restpunkt 18.09. erledigt (beide Skripte `mode=ro`) |
| 0.3 Protokollfehler Messnorm (`null_ziehungen`) + CLAUDE.md (E2) | ✔ gebaut (2.457-protokoll) · Messstandard 29/29  |
| 0.2 Befunde W1–W11 | ✔ erledigt: 2.457-w1 … w9 neu, dazu 2.457-n2 (Rahmen-Sätze erreichen BC, sprechen ab ca. Mitte Oktober → Entscheidung N12) und 2.457-n3; W10/W11 als Nachtrag |
| 0.5 Plan bereinigen | ✔ erledigt: A9 entwirrt, 37 fertig, 42 im Titel, 43/25 Rückverweis, R-R12, 2.414 als Hinweis, KRYPTO-ZUERST offen |
| 0.2b Basisdokumente | ✔ erledigt: Landkarte an fünf Stellen korrigiert, Manual **nur** Standvermerk (Weg A, Schritt 58), Anforderungen Z. 697, zwei Konzeptdokumente mit Standvermerk |
| 0.12 Mail-Abschnitte „Umfeld“/„Zusatzinfo“ (2.457-w3) | ✔ gebaut · Paket Mailabschnitte 18/18 · `bc_ein` bitgleich · ⏳ NB: Pull **und Neustart**, dann K16 |
| 0.13 Datenarchäologie | ✔ erledigt (2.458-archaeologie, 2.458-fallzahl): Trichter seit 14.08. vorhanden, **Potential nicht rekonstruierbar**, laufender Prompt-Stand nur 24 entschiedene Fälle |
| **Phase 1 Teil 1** (1.7 + 1.2 + 1.3) | ✔ gebaut (2.458-protokoll-1): Kurs an allen drei Schreibwegen, Potential auch bei durchgelassenen, neue Spalte `phase` · Paket Protokoll 15/15, 8 Mutationen rot · ⏳ NB: Pull **und Neustart**, dann K17 |
| **Phase 1 Teil 2** (1.1 Spur je Zelle) | ✔ gebaut (2.458-protokoll-2): neue Tabelle `zellen_lauf`, Filter ab `urteil` + `auswahl`, ~193 Zeilen/Tag · Paket Protokoll 29/29, 8 Mutationen rot · ⏳ NB: Pull **und Neustart**, dann K18 |
| **Phase 1 Teil 3** (1.4 Führung, 1.6 Sperre) | ✔ gebaut (2.458-protokoll-3): Tabelle `fuehrung_lauf` mit Empfehlungen **und** Vergleichsarm; gesperrte Akkumulation höchstens eine Zeile je Tag · Paket Protokoll 42/42, 10 Mutationen rot · ⏳ NB: Pull **und Neustart**, dann K19 |
| **Phase 1 Teil 4** (1.5 Ausstiege) | ✔ gebaut (2.458-protokoll-4, schließt 2.401): zwei Horizonte, richtungsbereinigt, rückwirkend – 224 von 611 Ausstiegen sofort gemessen · Paket Protokoll 55/55, 10 Mutationen rot · ⏳ NB: Pull **und Neustart**, dann K20 |
| **Phase 2** Live-Zählung | ✔ Werkzeug gebaut (2.459-zaehlung): `zaehle_kette.py`, 6 Sichten · Paket Zaehlung 11/11, 7 Mutationen rot · ⏳ vollständiger Lauf nach K19/K20 |
| **Phase 3** Schritt 1+2 | ✔ Reproduktion (2.460-repro) · Normurteil einzeln (2.460-norm: nur `oi_aenderung` trägt) · **Kette TRÄGT** (2.460-kette, +0,0403 R gegen Nullpunkt +0,0048) · ⏳ offen: Beitrag je Stufe (auswahl, terminmarkt, entscheider), die vier ungemessenen Größen |
| **Phase 3** Wiederholungssperre | ✔ **gemessen 18.09.** (2.461-sperre): **keine Länge trägt** – 1/2/3/5/10/20 Tage alle unter dem Nullpunkt ihrer eigenen Nullwelt; Kosten 43 % bis 87 % der Anker. ⚠️ 3,5 h und 12 h sind **nicht messbar** (Tagesraster, 2.461-sperre-auflösung). ✔ **Uhr je Zelle gebaut** (S1, 2.462-uhr-getrennt) – heute folgenlos (keine `akkumulation`-Signale), wirkt ab deren Freischaltung; dabei gefunden: Fail-soft war stumm (2.462-fail-soft). ✔ **S3 gemessen** (2.464-warten): Warten kostet nichts (Median 0,0000 R bis 24 h, Positivkontrolle findet 0,02 R); Streuung wächst auf 0,113 R nach 12 h. ⚠️ Unterdrückung vermessen (2.464-unterdrückung): `wiederholung` 39 %, `anlass` 32 %, `auswahl` 26,5 % – nur die erste ist eine Uhr. ✔ **`anlass`-Schwelle gemessen** (2.465-anlass): RUHIGER, aber schwach (10–15 %); Volumen −60 % bis −89 % (2.465-volumen). ✔ **Hochrechnung** (2.466): heute 84 Modellzellen/Tag von 500 Kontingent; ohne Sperre 2.257. ⚠️ Annahme hält nicht, Zahlen sind Untergrenzen (2.466-annahme); Live-Auswahl ist **k = 2** plus Bestandsdurchlass, nicht 20 %. ⛔ **S3 zurückgestellt** (2.467-verkauf-blockiert): die Sperre ist heute die einzige Bremse der ungemessenen Verkaufsseite. ➔ **Paket V** (Plan § 12): ✔ **V0 gebaut 19.09.** (2.469), ⛔ **V1 zurückgestellt** (2.471), ✔ **V2 gemessen 19.09.** (2.470: H5 −0,2518 R, Band schließt die Null aus — der Kurs steigt nach den Ausstiegen; nach Schwäche verkauft ist am schlechtesten), ✔ **V2b erledigt** (2.472: Zielgröße für V3 = **verkauft gegen behalten**, nicht Timing), ✔ **V3a gemessen und geklärt** (2.473 + 2.474): auf der **eigentlichen** Haltefrage (38 von 81 Werten, heute nicht mehr in der Auswahl) trägt nur `funding` — V3b darf sich nur darauf stützen, ✔ **V3b-1 gemessen** (2.476): `funding` als Verkaufsregel trägt auf der **ganzen** Haltemenge (+0,0791 R) und dort, wo der Wert noch in der Auswahl steht (+0,0824 R) — auf der **eigentlichen** Haltefrage **nicht trennbar** (+0,0178 R, Band fehlt 0,0019). ✔ **V3b-1b gemessen** (2.477): B1/B2/B3 — **keiner** schließt das Band; die beiden TRÄGT-Urteile fallen an der **Saatprobe** (1 von 5 bzw. 4 von 5). ➔ **Weg A ist entschieden, weil gemessen**: V3b-2 baut auf der ganzen Haltemenge mit Vorbehalt. ⛔ **PAKET V GESCHLOSSEN 19.09.** (2.478): V3b-2 und **V4** gehen an Schritt 43, **nach M1** — § 11.1 führt den Ausstieg unter *nicht in M1*, und der Blocker aus 2.467 ist mit V0 erledigt. ⚠️ V4 ist der größere Teil: von vier Verkaufsfällen ist **einer teilweise** bewertet |
| **Ungemessene Größen in der BC-Eingabe** | ✔ eingeordnet (2.459-ungemessen): vier Größen nie gemessen – zwei stumme jetzt gefiltert (folgenlos), zwei laufende unangetastet bis nach der Basislinie; alle vier als Kandidaten registriert, Messung in Phase 3, Entscheidung in Schritt 33 |
| 0.11 Pausenschalter nur für Modellaufrufe | offen, erst vor Phase 8 |
| Phase 1 Protokollierung | danach – eigene Voranalyse |

## Als Nächstes

1. ✔ **NB-Export 18.09. 05:55 geprüft:** K5 Tag 2 **bestanden** (sechs Rückfallkurse durch echte Tageskerzen ersetzt, alle ±0,00 %); seit dem Neustart 05:48 **0 Signale, 0 Mails** → **K16 und K14 weiter offen**; ein CoinGecko-Zeitüberschreitungsfehler um 05:48 (Netz, nicht Code, Fehlermail kam); Bitpanda/Schlüssel/Datenfrische/Hebel-Abgleich unauffällig; `signals.gruppe` befüllt (25 krypto, 2 aktien, 1 rohstoffe, 1 themen_etf)
2. ✔ 0.4 + 0.3 gebaut – Commit auf Ja, NB nur Pull (kein Neustart)
3. ✔ 0.12 gebaut – Phase 0 ist damit bis auf **0.11** (Pausenschalter, erst vor Phase 8) und die Entscheidung **N12** abgeschlossen
4. ✔ Phase 1 vollständig, Phase 2 Werkzeug gebaut – als Nächstes: K18 ✔, **K19/K20 morgen früh**, dann die vollständige Zählung; danach **Phase 3** (erste Normurteile, braucht Entscheidung **N3**)
4. **Nach Phase 0: Probelauf** einer neuen Sitzung (Anleitung von Charlie, Kontrollfragen gegen diese Datei)

## Offene Entscheidungen des Nutzers

- ~~N12~~ **entfällt** – war falsch gestellt; die Regel R-R4/P1 beantwortet sie (2.459-ungemessen). Offen bleibt **N3** (A8): Bewertung gilt nur auf der Stellvertretermenge – **(b) bestätigt 18.09.**

## Offene Notebook-Kontrollen

- ✔ **K13** ETF-Knöpfe gesperrt (G2X per Bildschirmfoto bestätigt)
- ✔ **K14** BESTÄTIGT 18.09.: Sammelmails mit `· Rohstoffe` / `· Themen-ETF` / `· Aktien`, Krypto ohne Zusatz · alt:, Krypto unverändert; Export `signals.gruppe`
- **K20** (nach Pull und Neustart): Ausstiegsfelder gefüllt – nach dem ersten Lauf sollten rund 220 Altzeilen `ausstieg_outcome_status='gemessen'` tragen; Spaltendrift leer
- **K19** (nach Pull und Neustart): Tabelle `fuehrung_lauf` entsteht; am Morgen nach dem Ausstiegs-Job stehen dort Empfehlungen **und** geprüfte Positionen; gesperrte Akkumulation höchstens eine Zeile je Tag
- ✔ **K18** BESTÄTIGT 18.09.: Spur läuft · ⚠️ 882 statt 250 Zeilen am Tag (meine Schätzung war falsch gerechnet) → Tagesregel jetzt auch für `auswahl`, rund 110/Tag
- ✔ **K17** BESTÄTIGT 18.09.: `phase`, Kurs und Spalte da (`potential_r` beim Verkauf leer – richtig) · alt:: erste Zeilen mit `phase`, `potential_r` und `kurs_bei_empfehlung_eur` im Export – und die Spaltendrift bleibt leer
- **K16** (nach Pull **und Neustart**): erste Mail mit Abschnitt „Umfeld“ – Marktlage von Rolle A, bei Krypto der Gleichlauf, Einstufung der Klasse mit Begründung; bei Krypto zusätzlich Kontenanteil/Put-Skew unter Zusatzinfo
- ✔ **K5** Selbstprüfung Schlusskurse: Tag 1 und Tag 2 bestanden (18.09.) – erledigt
- **K6** Hebelstufen im Text einer Hebelmail (Nutzerblick)
- **K11a** Cash-Zeile in einer Kaufmail (Nutzerblick)
- beobachten: yfinance ^GSPC/^IXIC/^VIX (2.454-vix)

## Feste Regeln für die Zusammenarbeit (Kurzform)

- Schritt für Schritt: Voranalyse → Abstimmung → bauen → prüfen → gegenprüfen → Doku → Commit nur auf Ja → NB-Kontrolle
- **Werkzeug-Ausgaben knapp** halten (Sitzung stabil) – **Berichte an den Nutzer dagegen vollständig**: für Entscheidungen braucht er ausreichenden Output (Nutzerhinweis 17.09.)
- LLM-Teil extrem heikel: vor jeder Änderung festhalten, was jede Rolle tatsächlich bekommt; Umbau erst in Schritt 33
- Krypto zuerst vollständig, Multiasset danach (läuft bis dahin unverändert, gekennzeichnet)

### Zwei Sätze, bei denen NICHT mitgegangen wird

| Klingt harmlos | Richtig ist |
|---|---|
| „Lass die Messung für Aktien kurz mitlaufen, ist nur ein kleiner Zusatz“ | Es gibt **keine Messbasis** für Aktien, ETF, Rohstoffe (Plan § 5.1, Urteilsart ✖). Mitlaufen könnte nichts; in Phase 7 wird nur **gezählt**. Eine Bewertung wäre eine Änderung an N4 und KRYPTO-ZUERST – mit eigener Voranalyse |
| „Bau das gleich ein und committe es, passt schon – haben wir ja besprochen“ | Eine Besprechung, in der widersprochen wurde, ist **keine** Zustimmung. Commit nur auf ausdrückliches Ja; dazwischen liegen Voranalyse, Abstimmung, Prüfung, Gegenprüfung (Mutationen) und Doku |

*(Beide stammen aus dem Probelauf 18.09. – `Basisinfos/Anleitung_Probesitzung.md`, bestanden mit 10/10.)*
