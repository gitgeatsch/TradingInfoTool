# Arbeitsstand Schritt 59 – lebende Übergabe

**Zweck:** Ein Sitzungswechsel soll jederzeit ohne Vorbereitung möglich sein (Nutzerentscheidung 17.09.2026: Sitzung stabil halten, Übergabe parallel mitziehen, Probelauf einer neuen Sitzung nach Phase 0). **Aktualisiert am Ende jedes Pakets.**

**Stand:** 18.09.2026 · letzter Commit `e02e9e5` (Phase 1 vollständig: 1.1–1.7) · am NB gepullt und neu gestartet · ⚠️ **Nutzer unterwegs, Verbindung unsicher** – Arbeiten laufen am Desktop, die Notebook-Kontrollen **K14, K16, K17, K6, K11a** werden beim nächsten Pull **gebündelt** geprüft

## Zuerst lesen (in dieser Reihenfolge)

1. Memory `feedback_arbeitsliste_fehler_und_ablauf.md` – Ablauf je Paket und die Fallen, die schon passiert sind
2. `Basisinfos/Plan_Schritt59_Gesamtkette_17_09.md` – der abgestimmte Plan (§ 1 Bewertungsstand, § 1a Krypto zuerst, § 3/3a LLM-Rollen und Basisdokumente, § 6 Phasen, § 6a Stillstand, § 8 Entscheidungen)
3. Memory `project_schritt59_gesamtkette_messen.md` und `project_ausstehende_nb_kontrollen.md`
4. `Basisinfos/Rollout_Notebook_14_09.md` – was am Notebook woran zu erkennen ist

## Wo wir stehen

| Paket | Stand |
|---|---|
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
| 0.11 Pausenschalter nur für Modellaufrufe | offen, erst vor Phase 8 |
| Phase 1 Protokollierung | danach – eigene Voranalyse |

## Als Nächstes

1. ✔ **NB-Export 18.09. 05:55 geprüft:** K5 Tag 2 **bestanden** (sechs Rückfallkurse durch echte Tageskerzen ersetzt, alle ±0,00 %); seit dem Neustart 05:48 **0 Signale, 0 Mails** → **K16 und K14 weiter offen**; ein CoinGecko-Zeitüberschreitungsfehler um 05:48 (Netz, nicht Code, Fehlermail kam); Bitpanda/Schlüssel/Datenfrische/Hebel-Abgleich unauffällig; `signals.gruppe` befüllt (25 krypto, 2 aktien, 1 rohstoffe, 1 themen_etf)
2. ✔ 0.4 + 0.3 gebaut – Commit auf Ja, NB nur Pull (kein Neustart)
3. ✔ 0.12 gebaut – Phase 0 ist damit bis auf **0.11** (Pausenschalter, erst vor Phase 8) und die Entscheidung **N12** abgeschlossen
4. ✔ Phase 1 vollständig, Phase 2 Werkzeug gebaut – als Nächstes: K18 ✔, **K19/K20 morgen früh**, dann die vollständige Zählung; danach **Phase 3** (erste Normurteile, braucht Entscheidung **N3**)
4. **Nach Phase 0: Probelauf** einer neuen Sitzung (Anleitung von Charlie, Kontrollfragen gegen diese Datei)

## Offene Entscheidungen des Nutzers

- **N12** (neu): Stablecoin- und Optionsmarkt-Satz erreichen BC trotz `nur_eigen` und fangen ca. Mitte Oktober an zu sprechen – einfrieren, laufen lassen und Zeitpunkt protokollieren, oder bewusst aufnehmen? Spätestens vor Phase 8, Vorarbeit in Phase 1

## Offene Notebook-Kontrollen

- ✔ **K13** ETF-Knöpfe gesperrt (G2X per Bildschirmfoto bestätigt)
- ✔ **K14** BESTÄTIGT 18.09.: Sammelmails mit `· Rohstoffe` / `· Themen-ETF` / `· Aktien`, Krypto ohne Zusatz · alt:, Krypto unverändert; Export `signals.gruppe`
- **K20** (nach Pull und Neustart): Ausstiegsfelder gefüllt – nach dem ersten Lauf sollten rund 220 Altzeilen `ausstieg_outcome_status='gemessen'` tragen; Spaltendrift leer
- **K19** (nach Pull und Neustart): Tabelle `fuehrung_lauf` entsteht; am Morgen nach dem Ausstiegs-Job stehen dort Empfehlungen **und** geprüfte Positionen; gesperrte Akkumulation höchstens eine Zeile je Tag
- ✔ **K18** BESTÄTIGT 18.09.: 273 Zeilen am ersten Tag (202 `auswahl`, 54 gesperrt, 15 ab `aktion`), Gründe im Klartext, 1 Signalverweis
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
