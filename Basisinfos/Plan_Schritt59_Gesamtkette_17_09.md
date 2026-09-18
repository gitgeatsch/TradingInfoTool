# Schritt 59 – Gesamtkette messen und bewerten

**Stand:** 17.09.2026 · **Status:** ABGESTIMMT – Nutzer 17.09.: *„ja N1 bis N10 wie empfohlen, committen und mit Phase 0 starten“*. Dazu: *„schritt für schritt vorgehen wie immer mit Abstimmung, Details im Plan können sich u.U. noch ändern. Berücksichtige auch erforderlichen Stillstand der Produktion für Messungen und Simulationen im LLM-Bereich“* (→ § 6a) und *„prüfe den Plan, ob wir zuerst die Krypto-Kette und Themen vollständig abschließen und erst danach die noch offene Multiasset-Schiene machen sollten … damit haben wir einen funktionierenden Teilbereich und keine unvollständige Gesamtlösung“* (→ § 1a). **Jede Phase und jedes Paket bekommt vor dem Bau eine eigene Voranalyse mit Abstimmung.**

**Grundlage:** drei unabhängige Recherchen am Code (LLM-Rollen · Stufen und Datenlage · Plan, Register, Methodik), jede Kernaussage von Charlie am Code bzw. an einer Kopie der NB-Sicherung 2026-09-17 04:41 UTC nachgeprüft (§ 10).

---

## 0 Auftrag und Rahmen

**Nutzervorgabe 15.09.2026 (Wortlaut):** *„Zu den Hebelsignalen und Krypto insgesamt muss die gesamte Ablaufkette und LLMs in einem umfangreichen Planpunkt gemessen und bewertet werden – erinnere dich, Ziel: Hebel nur dann, wenn ein optimales Chancen-Risiko-Verhältnis vorhanden ist. Die Bewertung sollte aber für alle Strategien erfolgen (Spot und Akkumulation) sowie Unterscheidung Einstieg, Führung und Ausstieg bzw. Reduktion.“*

**Nutzerhinweis 16.09.2026:** *„…dieser [LLM-Teil] ist extrem heikel und wir sind auf die Doku und Recherche angewiesen, dass alles korrekt umgesetzt wird – weil die LLM-Rollen nicht alle Informationen und in einem speziellen Format übergeben bekommen.“*

**Nutzerhinweis 17.09.2026:** *„…sind alle Bewertungen für alle Strategien (Indikatoren) vorhanden und geprüft? Sonst ist der LLM-Umbau u.U. später anzusetzen.“* und *„…das Thema ist schwierig und heikel, somit brauchen wir einen Plan, der detailliert und umfangreich diesen Bereich abdeckt.“*

**Geltende Regeln, die dieser Plan einhält:**

| Regel | Folge für Schritt 59 |
|---|---|
| **D vor L** (Blockordnung 12.09.) | Schritt 59 ist D-BEWERTUNG. Er **misst** die LLM-Rollen, er **ändert** sie nicht. Umbau = Schritt 33 (wartet auf 59). |
| **LLM ist Prüfung, nicht Entscheider** | Das Messdesign fragt je Rolle: trägt sie etwas bei – nicht: soll sie entscheiden. |
| **Messstandard vor der Messung** (`messnorm.standardzeile()`, ab 09.09.) | Jede Zelle hat vorab Frageart, Menge, Zielgröße, Nullbezug, Band, Positivkontrolle. Ohne Band nur „HINWEIS“. |
| **R-R11 Reproduktionspflicht** | Registrierte Befunde (z. B. `funding`, `turnover`, `oi_aenderung`) werden zuerst reproduziert, bevor ein Widerspruch zählt. |
| **Regeln 1–4** | Takt ist kein Signalgeber (betrifft die Wiederholungssperre als stärksten Filter), keine Gebühren in der Bewertung, kein Asset-Rang für den Hebel, ein Fakt ist keine Begründung. |
| **Zeitfenster ab 2023** | Jede Tabelle nennt ihr Zeitfenster. |
| **Keine Teillösung / Voranalyse vor jedem Schritt** | Jede Phase bekommt vor dem Bau ihre eigene Voranalyse und Abstimmung. |
| **NB = Produktion** | Messungen nur auf Kopien bzw. `mode=ro`. |

---

## 1 Antwort auf die Zwischenfrage: Ist die Bewertung für alle Strategien vorhanden und geprüft?

**Nein.** Belegt nur für **Krypto × Spot × Einstieg**. Alles andere ist ungemessen, gesperrt oder nicht gespeichert.

| Strategie × Phase | Bewertung heute | Geprüft? | Beleg |
|---|---|---|---|
| **Krypto · Spot · Einstieg** | Entscheiderstufe: Potential aus `funding` (Regler), `turnover` (Regler), `oi_aenderung` (Schalter) gegen die Schwelle je Datenlage | ✔ drei Beiträge tragen nach Messstandard (11.09.); `schnitt`, `schnitt50`, `vola` offen; Kette als Ganzes **nicht** gemessen | REGISTER_Kandidaten; `agent/wahrscheinlichkeit.BEITRAEGE` (alle `klassen=("krypto",)`) |
| **Krypto · Hebel · Einstieg** | nutzt die Spot-Bewertung (Vorgabe HEBEL-AUS-SPOT); Hebelhöhe aus r(q) | ✖ eigene Güte **blockiert durch A1** (Zielgröße `barriere` ungeeicht); Kalibrierung 2–5x gemessen (2.432), oberes Ende offen | Schritte 35, 37; `messnorm.ZIELGROESSE_JE_LAGE` |
| **Krypto · Hebel · Führung** | Hebelführung H-4 (Regeln: Liquidation, Schließen, Hebel senken, Stop nachziehen) | ✖ ungemessen; **Empfehlungen werden nicht gespeichert** | `agent/hebelfuehrung.py`; nur Meldeschlüssel in `job_laeufe` |
| **Krypto · Spot · Führung** (Nachkaufen auf Bestand, Stop nachziehen) | läuft als „Einstieg“ durch dieselbe Kette; Stop-Nachzieh-Mail aus `backward_tracking` | ✖ ungemessen; Phase in den Daten nicht getrennt | 2.455-hebelsignale; `ausstiegs_job` nur Mail |
| **Krypto · Ausstieg/Reduktion** | Rolle BC entscheidet; Menge deterministisch (`verkaufsrechnung`); **kein Gütemaß** | ✖ „Verkaufsbewertung nicht gelöst“; nur Hinweis 2.403 (VERKAUFEN schlägt Zufall, REDUZIEREN nicht – nicht normgerecht) | Schritt 43; 2.392, 2.401 |
| **Krypto · Akkumulation** | **gesperrt** bis zur Registrierung (Paket 2) | ✖ Akkumulationsmaß (`schnitt`, H90) offen, Blatt vor dem Messstandard | Schritt 25; `potential.lage_gesperrt` |
| **Aktien, Themen-ETF, Rohstoffe · Spot · Einstieg/Nachkauf** | ⚠️⚠️ **KEINE** – Klasse „nicht vermessen“: die Entscheiderstufe **zählt nur und lässt durch** | ✖ – die Kaufempfehlung beruht **allein auf Rolle BC** (z. B. BW, G2X, X136, ISOC NACHKAUFEN am 17.09. 05:34–05:36) | `rollen_lauf.py:2481-2488`; `mindestkriterien` BC3 „kein Fakt außerhalb der Kursreihe“ |
| **Absicherung (DBPK, 3QSS)** | keine Bewertung; Rolle BC liefert NACHKAUFEN ohne Richtung → verworfen | ✖ seit 22.08. praktisch kein Urteil | 2.389-richtung, 2.451-absicherung (offen), Rollenfrage R2 in 33 |

**Folgerung:**

1. **Ja – der LLM-Umbau (Schritt 33) gehört später.** Das steht schon so im Plan (33 wartet auf 59), wird durch diesen Befund aber ausdrücklich bestätigt: solange nur eine von acht Zellen eine gemessene Bewertung hat, würde ein Umbau der Rollen das Falsche optimieren.
2. **Schritt 59 kann die LLM-Ebene heute nur als Basislinie zählen**, nicht bewerten (§ 5, § 6 Phase 7).
3. **Die Lücken in der Bewertung selbst sind die eigentliche Vorarbeit** – sie liegen in den D-Schritten 43 (Ausstieg), 25 (Akkumulation), 35 (Hebel/A1), N-8 (Nicht-Krypto, bisher ohne eigenen Schritt) und in der fehlenden Protokollierung (§ 6 Phase 1).
4. ⚠️ **Neu sichtbar und entscheidungsbedürftig:** Für Aktien, ETF und Rohstoffe erzeugt heute allein das Sprachmodell Kaufempfehlungen, ohne gemessene Grundlage – derselbe Zustand, den der Nutzer am 11.09. für die Akkumulation per Sperre beendet hat (Entscheidung N1).

---

## 1a Krypto zuerst vollständig, Multiasset danach? – fachliche Prüfung (17.09.)

**Ergebnis: Ja – Krypto-Kette und Krypto-Themen vollständig abschließen, dann die Multiasset-Schiene.** Das deckt sich mit den bestehenden Nutzervorgaben, die im Plan stehen, aber in der Umsetzung nicht durchgehalten wurden.

**Die Vorgaben im Plan (`soll_ist.VORGABEN`):**

| Vorgabe | Wortlaut (gekürzt) | Stand im Plan | tatsächlich |
|---|---|---|---|
| **KRYPTO-ZUERST** (10.09.) | „Multiasset (Aktien, ETF, Rohstoffe, Hedge) ist NACHGELAGERT – erst nach dem Krypto-Produktivgang.“ | „erfüllt“ | ⚠️ irreführend: die Multiasset-Ketten laufen seit dem Vollumstieg 15.08. **scharf** mit (`rollen_kette.aktiv_fuer: [krypto, aktien, rohstoffe, themen_etf, hedge]`) und erzeugen Kaufmails ohne gemessene Bewertung (§ 1) |
| **VERKAUF-VOR-MULTIASSET** (12.09.) | Verkaufsempfehlungen angehen und **abschließen**, bevor Multiasset beginnt | offen | offen (Schritt 43) |
| **KRYPTO-STABIL-UND-KORREKT** (15.09.) | Krypto-Teil stabil und funktional korrekt, bevor weitergearbeitet wird (Schritt 60 nach 59) | offen | offen |

**Fachliche Gründe für „Krypto zuerst“:**

1. **Die gesamte gemessene Bewertung ist Krypto:** alle Beiträge (`BEITRAEGE`, `klassen=("krypto",)`), alle Messbasen (`messdaten`, `funding_historie`, `terminmarkt_historie`, `onchain_historie`), der Messstandard und sein Selbsttest. Für Nicht-Krypto gibt es **keine Messbasis** (N-19 zurückgestellt).
2. **Ein funktionierender Teilbereich ist prüfbar, eine halbe Gesamtlösung nicht:** Eine Kette, deren Einstieg, Führung, Ausstieg, Hebel und Akkumulation gemessen sind, lässt sich im Betrieb gegen Zufall halten. Mehrere halb bewertete Klassen verwischen jede Aussage – die Güte der Gesamtmails ist dann ein Durchschnitt aus Gemessenem und Ungemessenem.
3. **Die offenen Krypto-Themen sind groß und hängen aneinander:** Verkaufsseite (43), Akkumulation (25–27), Hebel/A1 (35), Stopregel (52), Führung (Protokoll), Fehlerkorrektur und Mails (60), LLM-Rollen (33). Parallelarbeit an Multiasset würde genau diese Kette zerschneiden.
4. **LLM-Kontingent und Betrieb:** Die Multiasset-Gruppen verbrauchen Modellaufrufe und erzeugen Mails, deren Güte unbekannt ist; bei den Absicherungen fällt jeden Morgen „2 Fehler“ an (2.389-richtung).
5. **Die Multiasset-Fragen sind grundsätzlich andere:** Handelstage statt 24/7, keine Terminmarktdaten, Fundamentaldaten bei Aktien, Absicherung als Portfoliofrage – ein eigener Entwurf ist sauberer als Anhängsel der Krypto-Matrix.

**Folgen für diesen Plan (eingearbeitet):**

- **Schritt 59 misst die KRYPTO-Kette vollständig** (Spot, Hebel, Akkumulation × Einstieg, Führung, Ausstieg; deterministisch und LLM).
- **Nicht-Krypto und Absicherung** werden in 59 **nur gezählt** (Hinweis, N1-Kennzeichnung) – die Bewertung wandert in eine **eigene Multiasset-Schiene im Block SPÄTER** (bisherige Phase 7 und N4 angepasst).
- **Schritt 33 (LLM-Rollen)** wird zuerst für Krypto entworfen; die Multiasset-Rollenfragen (R2 Absicherung, Fundamentaldaten) gehen in die Multiasset-Schiene.
- **Reihenfolge Krypto:** 59 → 60 → 43 → 25–27 → 33 (Krypto) → Krypto abgeschlossen → Multiasset-Schiene.
- **Doku:** Vorgabe KRYPTO-ZUERST von „erfüllt“ auf „offen“ mit Klarstellung (Phase 0.5).
- ⚠️ **Offene Betriebsfrage N11:** Was passiert **bis dahin** mit den scharf laufenden Multiasset-Ketten? (§ 8) – vorher Voranalyse, weil das Entfernen einer Gruppe aus `aktiv_fuer` laut Code die Gruppe nicht einfach abschaltet (`bedient_neue_kette`, möglicher Rückfall auf die alten Pipelines – zu prüfen, Phase 0.8).

---

## 2 Ist-Stand der Kette (deterministisch)

Reihenfolge `agent/rollen_gate.py:67-126` (`STUFEN`), Art des Verlusts `ART_JE_STUFE`.

| # | Stufe | prüft | wer | verwirft | gespeichert |
|---|---|---|---|---|---|
| – | Rolle A | Marktlage je Gruppe, höchstens alle 3 h neu | LLM | nein – aber **fällt sie aus, fällt die Gruppe aus** | `lagebilder` |
| 1 | auftrag | Nutzerschalter, erlaubtes Paar | Rechnung | ja | nur Summe |
| 2 | fakten | Kursreihe/Grundlage | Rechnung | ja | nur Summe |
| 3 | lagebild | Rolle A geliefert | Rechnung | praktisch nie | nur Summe |
| 4 | anlass | Faktensatz geändert | Rechnung | ja | Summe; `anlass_beobachtung` |
| 5 | auswahl | beste k der Gruppe (Bestand ausgenommen) | Rechnung | ja | Summe; `auswahl_schatten` |
| 6 | terminmarkt | OI-Aufbau nicht im obersten Fünftel | Rechnung | ja | nur Summe |
| 7 | wiederholung | Sperre je Symbol/Instrument/Gruppe/Strategie (tatsächlich **3,5 h**, F-214) | Rechnung | ja – **stärkster Filter (94,1 %)** | nur Summe |
| 8 | urteil | Rolle BC + Vertrag + Z1 | LLM, dann Rechnung | nur der Vertrag | Summe |
| 9 | aktion | Einstieg oder Verkauf/Bestand | gemischt | NICHTS_TUN, SCHLIESSEN, gestakt | `signals` (Nein-Zeile) |
| 10 | geometrie | Zonen, Stop, Hebel rechenbar (Stop nutzt **Widerlegungspreis aus BC**) | Rechnung | ja | nur Summe |
| 11 | risikoschicht | Töpfe, Cash, Größe | Rechnung | bucht nur | Summe |
| 12 | entscheider | Potential gegen Schwelle; Akkumulation gesperrt; **nicht vermessene Klassen: durchlassen** | Rechnung | ja (92 %, 2.391) | `signals` (`veto_art='entscheider'`) |
| – | Rolle G | Einwand aus Terminmarkt-Positionierung | LLM | **kein Veto** | `zai_gegenpruefung_*` |

**Speicherlücken (belegt):**

- `gate_durchlaessigkeit` (15.496 Zeilen am NB): **eine Zeile je Lauf, nur Summen**, ohne Symbol und Strategie.
- `auswahl_schatten` (127.153 Zeilen): `letzte_stufe` je Symbol – nur die letzte **bestandene** Stufe, Schlüssel `(lauf, gruppe, symbol)` → zwei Zellen desselben Symbols überschreiben sich; **kein Verlustgrund**.
- Verluste an Stufe 1–7, am Vertrag und an der Geometrie erzeugen **keine** `signals`-Zeile.
- Gesperrte Akkumulation erzeugt **keine** Zeile.
- Hebelführung, Positionsführung Spot, Ausstiegsführung: **Empfehlungen werden nicht gespeichert** (nur Mail bzw. Meldeschlüssel).

---

## 3 Ist-Stand der LLM-Rollen – was sie TATSÄCHLICH bekommen

(Vollständig mit Datei:Zeile in den Recherchen; hier die für das Messdesign tragenden Punkte.)

### Rolle A – Marktanalyst (`agent/rolle_analyst.py`, Prompt-Stand 2026-08-12b)

- **Eingabe:** nur `{"marktlage": [Sätze]}` aus `marktlage.beschreibe_marktlage` – lange Sicht, Makro (Netto-Liquidität, Zinskurve), je Leitmarkt (BTC, SPY, OD7C) Trend/Volatilität/Liquidität, Fear & Greed; Zahlen als Sätze mit Perzentil und Fenster. Kein Asset, kein Bestand, keine Bewertung.
- **Ausgabe:** `lage`, `klassen[{klasse, einstufung, warum}]`, `belege`.
- **Wirkung:** nur `lage` und ein gerechneter `gleichlauf` gehen an BC. **Die Einstufung je Klasse erreicht BC nicht** (`rollen_lauf.py:1505` überschreibt).

### Rolle BC – Händler (`agent/rolle_trader.py`, Prompt-Stand 2026-09-11a)

- **Eingabe (JSON, in dieser Reihenfolge):** `asset`, `auftrag` (Instrument/Strategie in 2 Sätzen), `stand` (bestand · fundamental nur Aktien · verlauf 5/20/60 T · marken · hebelgeometrie 3/6/10x · referenz nur Themen-ETF · volumen · umschlag nur Krypto · finanzierung **praktisch nie**, weil Krypto-Instrument immer „spot“ · luecken), `marktlage_beurteilung` `{lage, gleichlauf}`, `terminmarkt` (nur Krypto, `nur_eigen=True`), `absicherungslage` (nur Absicherung). Keine Kürzung; deutsche Zahlen.
- **Kennt NICHT:** Potential, `bewegung_r`, Schwelle, Trefferquote, r(q), Hebel, Betrag, Topf, Cash, Stop, Ziel, CRV, Phase/Führungsstand, Einstand einer Hebelposition, die Einstufung von Rolle A (bestätigt 2.398).
- **Ausgabe:** Belege mit Gewicht, unabhängige Faktoren, Aktion (KAUFEN/NACHKAUFEN/REDUZIEREN/VERKAUFEN/NICHTS_TUN), Richtung LONG/SHORT, Begründung, Gegenargument, Widerlegung (`umgeworfen_durch/_preis_eur/_bis`).
- **Wirkung:** NICHTS_TUN beendet den Fall (Stufe 9). **Der Widerlegungspreis geht als Boden in den Stop ein** → Stop, r(q)-Hebel, Betrag, Ziel hängen daran; `umgeworfen_bis` → Haltedauer; SHORT erzwingt „hebel“. Bei **nicht vermessenen Klassen** ist BC die einzige Entscheidung.

### Rolle G – Gegenprüfer (`agent/zweite_meinung.py`, Z.ai `glm-4.5-flash`)

- **Aufruf:** nur für Einstiege, die alle 12 Stufen bestanden haben, und für Ausstiege; im eigenen Faden nach dem Schreiben.
- **Eingabe:** `{"geplant": {aktion, richtung}, "positionierung": [Sätze]}` – Terminmarkt **mit** Rahmen (feine OI-%, BTC-Börsenfluss, fehlende Angaben). Keine Begründung, kein Stop, keine Kurslage.
- **Wirkung:** **kein Veto**; `einwand ja/nein/unklar` + Grund in DB und Mail.

### Widersprüche und Lücken (alle belegt – Klärung in Phase 0)

| # | Widerspruch / Lücke | Fundstelle |
|---|---|---|
| W1 | **BC bekommt seit 01.09. („Schritt 5“) Terminmarkt-Sätze** (OI, Long-Anteil, Divergenz, laut Code-Lesung auch den Funding-Extremsatz) – der G-Prompt sagt wörtlich „Diese Angaben standen dem Entscheider NICHT zur Verfügung“. **Quelle gefunden:** die Nutzerentscheidung betraf nur *„`hebel_triggers` als Anlass einspeisen“* (Anforderungen_Umbau_28_08 Z. 443, erledigt Z. 601); die Einspeisung in BC ist eine **technische Folge** (Anlass-Fingerabdruck wird über den BC-Faktensatz gebildet, `rollen_lauf.py:1532-1537`) – **nie eigens entschieden** und **gegen den Beschluss vom 17.08.**: *„Verworfen: den Auslöser in den BC-Prompt zu geben … Rolle G könnte nicht mehr unabhängig widersprechen“* (Regelwerk_Entscheidungslog Z. 16584-16590). Verletzt R-R2, R-R3 G3, R-R7/Kap. 66.3b. Dasselbe Dokument sagt am selben Tag noch „G sieht als einzige Rolle den Terminmarkt“ (Z. 697). | `rollen_lauf.py:1553-1565`, `zweite_meinung.py:451`, `positionierung.py:916` |
| W2 | Einstufung von Rolle A erreicht BC nicht (Mechanismus „Urteil zur eigenen Klasse“ läuft ins Leere) | `rollen_lauf.py:1505`, `rollen_eingabe.py:338-363` |
| W3 | Mail-Abschnitt „Umfeld“ tot (liest nie gesetztes `fakten_roh`, falscher Feldname `beurteilung`) | `rollen_lauf.py:2626` |
| W4 | BC-Prompt verlangt Einstiegs-/Ausstiegskurs, Schema verbietet die Felder seit 18.08. | `rolle_trader.py:219-222` |
| W5 | BC-Prompt: „kein Perzentil zu Schwankung/Kursentwicklung“ stimmt nicht; Schritt 1 fragt „was für einen **Einstieg** spricht“ auch bei Bestandsfragen | `rolle_trader.py` |
| W6 | Finanzierungsblock für Krypto tot (Instrument immer „spot“) | `assetklassen.py:61-67`, `rollen_eingabe.py:765` |
| W7 | Akkumulation hat keine eigene LLM-Frage (übernimmt Einstiegsurteil) | `rollen_lauf.py:1606-1612` |
| W8 | Rolle A: Ausfall kostet die ganze Gruppe; Landkarte sagt anderes | `rollen_lauf.py:500-502` |
| W9 | Landkarte G5 „ohne symbolspezifische Daten nicht gefragt“ – Code fragt auch nur mit BTC-Börsenfluss | `zweite_meinung.py:549` |
| W10 | Der Widerlegungspreis von BC steuert Stop → Hebel/Betrag; Fakten-Mappe 11.6 sah `umgeworfen_durch` als **Ausstiegsbeobachtung**, nicht als Größenhebel; Landkarte-Vorgabe „Entscheidungshilfe, nichts blockieren oder ändern“ (12.09.) durch BC verletzt (2.391-hilfe offen) | `entscheidungsrechnung.py:457-517`; Fakten-Mappe Z. 1559-1571 |
| W11 | ⚠️ **17.09. richtiggestellt (2.457-w11 fällt weg, gehört zu 2.455-regelwerk):** der Log endet **nicht** am 19.08. – Einträge laufen bis **24.08.**, und am **03.09.** steht dort bereits ein Schlussvermerk samt Übergangsregel (bis 24.08. Chronologie im Log, danach F-Nummern, Methodik, Anforderungen_Umbau). Richtig bleibt: Schritt 5, Stufe `terminmarkt` und Prompt-Stand `2026-09-11a` sind dort nicht verzeichnet – sie stehen in 2.452-anlass, 2.391, 2.379-liq. Weiterbehandlung: Schritt 58 (Regelblatt aus dem Code, Weg A) | Log Z. 22689; Befund 2.455-regelwerk |

---

## 3a Basisdokumente zur LLM-Funktion – Soll gegen Ist

(Nutzerhinweis 17.09.: *„vergiss nicht relevante Basisdokumente, welche auch Information zur aktuellen LLM-Funktion geben sollten“*. 18 Dokumente mit LLM-Bezug geprüft, Kernaussagen am Code und an den Fundstellen nachgeprüft.)

### Welches Dokument was festlegt – und wie aktuell es ist

| Dokument | legt fest | Stand gegen Code |
|---|---|---|
| **Regelwerksmanual.md** | R-R1 Rollen und Namen · R-R2 ein Parameter je Modell · R-R3 G1–G5 · R-R4 P1–P7 (Aufnehmen ist ein Tausch; Budgets A 16, BC 14, G 8 Aussagen) · R-R6 Belegstand · R-R7/Kap. 66 Zuordnungsmatrix · R-T1–R-T12 Format · R-A1–R-A8 Ausgabe · R-R11 | ⚠️ kein Rollen-Nachtrag nach 29.08.; R-A1 „1–2×/Tag“ (Code 3 h), R-A2 Betragsstaffel veraltet (r(q)), R-R6 „was in A steht, weiß BC“ (W2), G „nach der Mail/Regime/49,8 %“ veraltet, R-R11 doppelt vergeben |
| **Kette_Landkarte.md** (12.09.) | 12 Stufen, was jede Rolle bekommt und bewirkt, Vorgabe „Entscheidungshilfe“ | ⚠️ „nichts davon im BC-Faktentext“ (W1), Regime bei G, Einstieg/Stop als BC-Angabe, „Rolle A blockiert nichts“ (W8), G „nach dem Urteil“ statt nach 12 Stufen |
| **Umbauplan_Gesamtsystem_12_08.md** | Kap. 32–37 Rollenaufbau, 36.1/36.2 Auslöser als Bedingung vor dem Aufruf, 41/42 Einstufung als Baustein für BC, 66 Zuordnungsmatrix | ⚠️ 32.2 (Funding bei allen) und 37.1 (Regime in G) überholt; 36.2/66.3b durch Schritt 5 verletzt; 33.7 widerspricht 66.3b |
| **Regelwerk_Entscheidungslog.md** | Nutzerentscheidungen bis 19.08., u. a. Beschluss 17.08. (Auslöser nicht in BC) | ⚠️ endet 19.08. (W11); Namen „Lagebild/Befund/Entscheidung“ durch R-R1 überholt |
| **Rollenkonzept_Entwurf_10_08.md** | Herkunft der Rollen | als überholt markiert; sein Standvermerk nennt Terminmarkt in BC „falsch und heute schädlich“ – genau das ist seit 01.09. wieder der Fall |
| **Anforderungen_Umbau_28_08.md** | §8.3: LLM-Nein ist Prognose, G keine Trichterstufe, LLM muss Zufall schlagen, bevor es wirkt; L1–L4 Grenzen der Messung; Schritt 5 | ⚠️ Z. 697 widerspricht Z. 601 (beide 01.09.); „LLM muss Zufall schlagen, bevor es wirkt“ gegen Ist: BC wirkt ungemessen |
| **Fakten_Entscheidungsmappe.md** | 11.2 exklusiver Eingang der Entscheidung · 11.6 was das Modell nie sieht · F-197 G-c · F-174/F-214 Sperre | ✔ 11.6 stimmt (kein Betrag/Stop/Risiko); ⚠️ 11.2 (Kosten, Sperren an BC) nicht nachgezogen; 13.5 Konsistenzcheck abgelöst |
| **Messkonzept_LLM_Standard_25_08.md** | N-7: F1 Kette gegen gleich großen Zufall, F2 gegen EMA-200, F3 Urteil vs. Vorauswahl; Zerlegung C1 in sechs Teile; Ablation ≥ 200 Paare je Arm | ⚠️ **vor dem Messstandard** (|t| ≥ 3,05, keine Tagesklammer, Entscheider als „zählt nur“) – Konzept verwendbar, Norm neu |
| **Konzept_Bewertungsstufe_29_08.md** | V-0-Messung (Z. 230–321); **Vier-Felder-Schema** Teil 11 §5 (Z. 2159–2197): verworfen vs. durchgelassen bei gleichem LLM-Urteil → trägt die Bewertung; LLM-kaufen vs. LLM-halten bei gleicher Bewertung → trägt das Modell | ⚠️ Stufennummer (11 → heute 12), Entscheider „NUR_ZAEHLEN“ überholt; **Vier-Felder-Schema passt am besten zu Schritt 59** |
| **Zielgroessen_und_Erfolgsmasse.md** | §3b nur Vorwärtsmessung (Vorwissen des Modells), §7b Anbieterdrift, §8 CoT-Rauschen | ✔ als Methodenregeln gültig; Pipelinebezüge (LLM1/LLM2, Mistral) veraltet |
| **Test_und_Verifikationsmethodik.md** | 2.93 gleich großer Zufall, 2.109 Poolen nur begründet, 2.110 Norm, 2.15 CC1–CC4 und Rauschboden mit drei Armen (Z. 988–992), 2.188, 2.201, 2.204, §F Literatur, §G Meta-Labeling | ✔ verbindlich |
| **Gesamtplan_Wo_wir_stehen_28_08.md** | K-1 bis K-7 Kettenprüfung (LLM-Rollen „nicht enthalten … nicht messbar“, Z. 2147), A1/A8/A9, 2.391-hilfe | ⚠️ A9 doppelt belegt; K-7 „nicht entscheidbar bei n=139“ |
| **Regler_Signal_Pipeline_Abhaengigkeiten.md** | jede Prompt-Änderung = neuer Prompt-Stand, Messungen nur innerhalb eines Stands vergleichbar (Z. 202–204) | ✔ Regel gültig; Stage-2/3-Teil beschreibt die alte Pipeline |
| Zwischenstand_06_08, Bestandsaufnahme_02_08, Arbeitsstand_Deadloop_09_08, Konzept_Nachrichten_24_08 | Messungen der **alten** Kette (Richtungstreffer, Konfidenz), Look-ahead-Argument | historisch – nicht übertragbar, aber als Methodenwarnung gültig |

### Verbindliche Regeln für Messung (59) und späteren Umbau (33)

1. **LLM ist Prüfung, nicht Entscheider** (Nutzer 13.09.) · **Entscheidungshilfe, nichts blockieren oder ändern** (Landkarte, Nutzer 12.09.) · **LLM muss den gleich großen Zufall messbar schlagen, bevor es wirkt** (Anforderungen §8.3) · **G keine Trichterstufe, kein Veto** (Nutzer 31.08.).
2. **Informationsgrenzen:** R-R2 (ein Parameter je Modell), R-R3 G1–G5 (keine G-Quelle im BC-Faktentext), R-R7/Kap. 66 Zuordnungsmatrix, **Beschluss 17.08.: Auslöser nicht in den BC-Prompt**, R-R4 P1–P7 (Verfügbarkeit ist kein Aufnahmegrund; Aussagenbudget), Fakten-Mappe 11.6 (Modell sieht nie Betrag, Risiko, Stop als Zahl).
3. **Format:** R-T1–R-T12 (Fenster nennen, keine Etiketten, relativ statt roh, Perzentil mit Einordnung 90/10, kein Etikett in die Gegenprüfung, der Prompt rechnet nicht vor).
4. **Ausgabe:** keine Konfidenz (R-A3), kein Betrag (R-A2), keine Vorsichtssprache (R-A4), keine „unklar“-Kategorie für BC, Formfehler korrigieren/Sinnfehler ablehnen (R-A5), Aktion nicht raten (R-A6), Kauf ohne Ausstieg → NICHTS_TUN (R-A7), Gegenprüfer nie im selben Aufruf (R-A8).
5. **Messmethodik LLM:** nur **Vorwärtsmessung** (Vorwissen des Modells); **Rauschboden mit drei Armen** (8–12 % Richtungsdreher bei identischer Eingabe); **Schichtung nach `prompt_stand` und `modell`**; Anbieterdrift mitschreiben; gleich großer Zufall als Nullmodell; Tagesklammer (Poolen nur begründet, 2.109).
6. **Namen** nur nach R-R1; „Entscheider“ ist die Rechenstufe, nicht BC (der G-Prompt verwendet das Wort falsch).

### Registrierte LLM-Ergebnisse (R-R11 – zuerst reproduzieren)

| Ergebnis | Aussage | Stand |
|---|---|---|
| **V-0** (29.08., Konzept_Bewertungsstufe Z. 230–321) | Rollen-Kette hat **keine Asset-Auswahl** (+0,0013, t 0,12); Tagestreffer „nicht entscheidbar“ (7 Handelstage) | vor Messstandard |
| **G-c / F-197** (03.09.) | Einwand von G: 45,8 % vs. 54,8 % TP-Quote, Band [−0,246 .. +0,233] → **nicht nachweisbar** (n=55, 9 Tage) | vor Messstandard, gepoolt |
| **Nichtdeterminismus** (Methodik 2.15) | 8–12 % Richtungsdreher bei identischer Eingabe | gilt |
| **CoT-Rauschen** (Zielgrößen §8) | Prompt-Änderung wirkt 0,01× des Eigenrauschens; 0,10 R brauchen 695 Paare | gilt als Größenordnung |
| **Anbieterdrift** (Zielgrößen §7b) | Mistral 31.07. anderes Verhalten bei bitgleichem Prompt | gilt als Warnung |
| alte Kette (06.08.) | Richtungstreffer LLM 25–30 % gegen EMA-200 ~62 % | historisch, nicht übertragbar |

**Nicht gefunden:** eine Messung „Rolle A gegen Zufall“, eine Messung der Rollen-Kette nach Messstandard, ein Befund zu Schritt 42 Stufe 2.

---

## 4 Datenlage (NB-Sicherung 2026-09-17 04:41 UTC, Kopie, `mode=ro`)

| Größe | Wert |
|---|---|
| Zeilen der Rollen-Kette in `signals` (mit `strategie`) | **2.344** · 23.08.–17.09. |
| davon `strategie` | **100 % `einstieg`** |
| Spot NACHKAUFEN / REDUZIEREN / HALTEN / VERKAUFEN / KAUFEN | 1.523 / 364 / 307 / 117 / 21 |
| Hebel (alle NACHKAUFEN) | **10** · 12.–16.09. |
| Absicherung | 2 (HALTEN) |
| Akkumulation | **0** (gesperrt, keine Zeile) |
| `gate_passed` 1 / 0 | 1.174 / 1.170 |
| `veto_art='entscheider'` | 8 |
| `potential_r` gesetzt | **67** – nur bei `gate_passed=0`, erst seit 14.09.; **0 bei durchgelassenen und 0 beim Hebel** |
| `kurs_bei_empfehlung_eur` | 44 (nur Ausstiegsweg) |
| `outcome_status` | einstieg_nie_erreicht 908 · nicht_anwendbar 691 · offen 278 · stop_loss 320 · take_profit 147 (altes CRV-Maß, nicht `bewegung_r`) |
| `umgesetzt` | 1 |
| je Woche (Zeilen / durchgelassen) | KW33 24/19 · KW34 1.088/642 · KW35 621/252 · KW36 420/176 · KW37 191/85 |
| `gate_durchlaessigkeit` / `auswahl_schatten` | 15.496 / 127.153 |
| **BC-Prompt-Stand** (Modell durchgehend `gemini-3.1-flash-lite`) | `2026-08-17e`: **2.078** Zeilen (23.08.–12.09.) · `2026-09-11a`: **266** Zeilen (12.–17.09.) → **jede LLM-Aussage getrennt je Stand**; der heutige Stand hat erst 5 Tage |
| Rolle-G-Urteile | ja 394 · nein 440 · unklar 33 · ohne 1.477 (867 Urteile – 16× so viele wie bei G-c) |

**Historische Messbasis:** `data/messdaten.db` Tageskurse bis 08.09. (5,13 Mio. Zeilen) · `funding_historie.db` 2019–31.08. · `terminmarkt_historie.db` 12/2021–31.08. · `onchain_historie.db` bis 12.09.

**Was daraus folgt (belegt):**

- `bewegung_r` ist **keine Spalte**, sondern eine Zielgröße der Messnorm, die aus Kursreihen gerechnet wird.
- Die Norm verlangt **≥ 20 Blöcke**; bei H20 sind das rund 1.200 Handelstage. **Die Live-Daten (Rollen-Kette seit 14.08., heutige Fassung seit 12.09.) reichen für kein Normurteil** – live ist nur Frageart `zaehlung` zulässig, Güte-Aussagen sind höchstens HINWEIS.
- Normgerechte Güte gibt es nur **historisch**, und dort nur für **deterministische** Stufen (auswahl, terminmarkt, entscheider; fakten vermutlich; geometrie nur ohne Widerlegungspreis). **Die LLM-Rollen sind historisch nicht nachrechenbar** (keine Aufzeichnung vor 14.08.; `backtest_llm1_historisch.py` kostet Kontingent und hat ein ungeklärtes Vorwissen-Problem).

---

## 5 Die Matrix – Messdesign je Zelle

Legende Urteilsmöglichkeit: **U** = Normurteil möglich · **H** = nur HINWEIS · **Z** = nur Zählung · **✖** = heute unmöglich · **(B)** = Blocker.

### 5.1 Deterministische Ebene

| Zelle | Frageart / Menge | Zielgröße | Nullbezug | Datenbasis, Fenster | heute | Blocker / Voraussetzung |
|---|---|---|---|---|---|---|
| Krypto·Spot·Einstieg – **Kette gesamt** | `beitrag`, selektierte Menge der Kette | `bewegung_r` | Nullwelten (gemischte Ränge), Tagesklammer | historisch ab 2023, nachgebaute Stufen 5, 6, 12 | **U** | A8 (k=2 je Tag → 0 Tage) → **N3** |
| – je Stufe (auswahl, terminmarkt, entscheider) | `beitrag` „Kette mit gegen ohne Stufe“ (Muster N-67) | `bewegung_r` | dito | dito | **U** | R-R11: registrierte Beiträge zuerst reproduzieren |
| – anlass, wiederholung | `beitrag` | `bewegung_r` | dito | nur teilweise nachbaubar | **H** | Regel 1: Wiederholungssperre ist eine **Uhr** → Nutzerfrage (F-214) |
| – geometrie (Stop) | `geometrie` | `bewegung_r` bzw. Stop-Treffer | Schritt 52 | historisch, **ohne** Widerlegungspreis | **H** | Schritt 52 |
| Krypto·Spot·Einstieg – live | `zaehlung` | – | – | `gate_durchlaessigkeit`, `signals` | **Z** | Phase 1 für Zellen-Auflösung |
| Krypto·**Hebel**·Einstieg | `beitrag` | **`barriere`** (Norm) | Nullwelten | historisch | **✖ (B)** | **A1** (Schritt 35) – vorher nur H auf `bewegung_r` („Spot gegen Hebel“) |
| – trägt r(q) den Hebel? | Simulation `simuliert=True` | `barriere` / `bewegung_r` | – | historische Einstiegsmenge | **H** | A1; Kapitalbasis 12.–14.09. war ~1.720 € zu hoch |
| Krypto·Hebel·**Führung** | `beitrag` je Regel (Stop nachziehen, Hebel senken …) | Folge-`bewegung_r` ab Empfehlung | „halten ohne Regel“ | **fehlt** | **✖** | Phase 1 (Speicherung) · Schritt 52 |
| Krypto·Spot·**Führung** (Nachkauf auf Bestand) | wie Einstieg, Menge „mit Bestand“ | `bewegung_r` | dito | historisch trennbar über Bestand? | **H** | Phase-Feld fehlt; 2.455-hebel-nachkaufen |
| Krypto·**Ausstieg/Reduktion** | eigenes Gütemaß (43 (1)) | Verlauf nach Verkauf gegen „halten“ | Nullmodell „halten“ | Live 2.403; historisch neu zu bauen | **H → U** | Schritt 43 (1); Outcome-Kategorie Ausstieg (2.401) |
| Krypto·**Akkumulation** | `beitrag` | **`verbilligung`** (Rang, Basisrate 0,5) | Nullwelten | historisch H90 | **U** | Schritt 25 (Reproduktion 2.286/2.287, Zeitstabilität) |
| **Aktien / Themen-ETF / Rohstoffe** | `beitrag` / `markt` | `bewegung_r` | Nullwelten | **eigene Messbasis nötig** (N-8, kein Schritt) | **✖** | Messbasis Nicht-Krypto → **N4** |
| **Absicherung** | eigene Frage (Wirksamkeit gegen Portfolio) | `bewegung_r` laut Norm – fachlich zweifelhaft | – | `hedge_wirksamkeit` | **✖** | Rollenfrage R2 (Schritt 33) |

### 5.2 LLM-Ebene (so gemessen, wie die Rollen gefüttert werden – § 3)

| Rolle | Frage | Menge | Zielgröße / Nullmodell | heute | Grenze |
|---|---|---|---|---|---|
| **BC** – Aktion | Tragen NACHKAUFEN/KAUFEN mehr als NICHTS_TUN (Selbst-Halten-Schatten)? | live, Krypto und Nicht-Krypto getrennt | `bewegung_r` ab Empfehlungstag; Zufall bei gleicher Trefferzahl | **H** | Live-Länge; Tagesklammer |
| **BC** – Widerlegungspreis | Ist der Modellstop besser als der Regelstop? | 81,5 % der Stops (2.438) | Stop-Treffer gegen ATR-Regel | **H** | Schritt 52 |
| **BC** – Ausstieg | VERKAUFEN/REDUZIEREN gegen halten | live | Nullmodell halten | **H** | 43 (1) |
| **BC** – Nicht-Krypto | einzige Entscheidung – trägt sie? | live Aktien/ETF/Rohstoffe | `bewegung_r` gegen Zufall | **H** | Menge klein; wichtigste LLM-Frage (§ 1) |
| **A** – Einstufung | Stimmt „günstig/ungünstig“ je Klasse mit der Folgebewegung der Klasse? | `lagebilder` seit 14.08. | Klassenbewegung | **H** | wenige Zeitpunkte (3-h-Takt); wird heute **nicht verwendet** (W2) |
| **G** – Einwand | Haben Signale mit Einwand schlechtere Folge als ohne? | live Einstiege mit G-Urteil | `bewegung_r` gegen ohne Einwand | **H** | kein Veto → reine Beobachtung; W1 (BC sah dieselben Daten) |
| alle | LLM gegen Zufall (Schritt 42 Stufe 2) | live | Zufall bei gleicher Trefferzahl | **H** | historisch ✖ |
| **Kette** – Vier-Felder-Schema (Konzept_Bewertungsstufe Teil 11 §5) | (1) verworfen vs. durchgelassen bei gleichem LLM-Urteil → trägt die **Bewertung**? (2) LLM-kaufen vs. LLM-halten bei gleicher Bewertung → trägt das **Modell**? | live, ab Phase 1 vollständig (heute `potential_r` nur Nein-Seite, erst seit 14.09.) | `bewegung_r` ab Empfehlungstag | **H** | braucht Phase 1.2; A8 |
| **Reproduktion V-0 und G-c** | vor jeder neuen LLM-Aussage (R-R11) | V-0: eigene vs. fremde Signaltage; G-c: Einwand vs. kein Einwand, jetzt n=867 | wie registriert, dann nach Norm | **H** | Poolen (2.109) begründen |

**Pflichten für jede Zeile in 5.2:** getrennt je `prompt_stand` (2.078 / 266) · Rauschboden mit drei Armen, wo wiederholt gefragt wird · nur Vorwärtsdaten · Messkopf mit Datenlänge und Blockzahl · Ergebnis heißt HINWEIS, solange die Norm (≥ 20 Blöcke) nicht erfüllt ist.

---

## 6 Vorgehen in Phasen

Jede Phase: **eigene Voranalyse → Abstimmung → Bau/Messung → prüfen → gegenprüfen → Doku (Befund, Plan, Memory) → Abnahme.** Keine Phase beginnt, bevor die vorige abgenommen ist, außer wo „parallel“ steht.

### Phase 0 – Grundlage klären (keine Messung, keine LLM-Änderung)

**Ziel:** Die Widersprüche aus § 3 und die Messanlage bereinigen, damit nichts auf falschen Annahmen gemessen wird.

| Paket | Inhalt | Art |
|---|---|---|
| 0.1 | **W1 entscheiden** (Quelle gefunden, § 3): Einspeisung der Terminmarkt-Sätze in BC gegen Beschluss 17.08. – Nutzerentscheidung **N5**. Wichtig für die Messung: seit 01.09. sind BC und G **nicht mehr unabhängig** → jede G-Messung ab 01.09. getrennt ausweisen. **Kein Prompt- oder Eingabe-Edit ohne Entscheidung.** | N5 |
| 0.2 | W2–W11 als Befunde registrieren und je Punkt zuordnen: D-ABBILDUNG (Doku/Mail, jetzt) oder Schritt 33 (Prompt/Rollen, später) · ✔ **ERLEDIGT 17.09.:** W1–W9 als Befunde 2.457-w1 … 2.457-w9 registriert, dazu die neuen Funde 2.457-n2 (Rahmen-Sätze erreichen BC, sprechen ab ca. Mitte Oktober) und 2.457-n3 (2.397 rechnet mit 0,75 ATR, Kette läuft mit 2,0). W10 und W11 als Nachtrag an 2.391-hilfe bzw. 2.455-regelwerk (kein neuer Befund). Zuordnung: W3/N1 → Paket 0.12 (Mail), alles Übrige → Schritt 33, Doku-Teile hier | erledigt |
| 0.2b | **Basisdokumente nachziehen (nur Doku, kein Code):** Kette_Landkarte (W1, W8, G-Zeitpunkt, Regime), Regelwerksmanual (Rollen-Nachtrag „Stand 17.09.“ zu R-A1, R-A2, R-R6, G-Abschnitt; R-R11-Doppelvergabe), Anforderungen_Umbau Z. 697, Regelwerk_Entscheidungslog fortführen oder ausdrücklich als „geschlossen 19.08., Fortsetzung in REGISTER_Befunde/soll_ist“ kennzeichnen, Messkonzept_LLM_Standard und Konzept_Bewertungsstufe mit Standvermerk (Stufe 12, Messstandard) · ✔ **ERLEDIGT 17.09.:** Landkarte an fünf Stellen korrigiert (Standkorrektur am Kopf plus Markierung je Stelle); Regelwerksmanual **nur Standvermerk** – kein Nachtrag von Hand, weil Schritt 58 (Weg A, Nutzerentscheidung 15.09.) das Regelblatt aus dem Code erzeugt; Anforderungen Z. 697 richtiggestellt; Entscheidungslog braucht nichts (Schlussvermerk vom 03.09. besteht); Messkonzept und Konzept_Bewertungsstufe mit Standvermerk (trägt / ersetzt / überholt) | erledigt |
| 0.3 | Messanlage: `messnorm.py:818` protokolliert `null_ziehungen=5` statt 40 → korrigieren (reiner Protokollfehler); Kopfkommentar „Selbsttest fehlt“ veraltet; CLAUDE.md-Tabelle zum Nullbezug (Mittel, nicht 90. Perzentil) richtigstellen · ✔ **GEBAUT 17.09.** (2.457-protokoll): `null_ziehungen=NULL_ZIEHUNGEN`, Kopfkommentar mit Nachtrag 2.204, CLAUDE.md-Zeile (Mittelwert der Nullwelten, p90 nur obere Grenze); Paket Messstandard +1 Prüfung am Lauf (29/29), Mutation rot | erledigt |
| 0.4 | `messe_ausstiegsguete.py` öffnet die Produktions-DB **ohne `mode=ro`** → auf `mode=ro` umstellen, bevor es wieder läuft · ✔ **GEBAUT 17.09.** (E1, 2.457-nurlesend): **alle acht** gefundenen Skripte (nicht nur dieses) öffnen `mode=ro`; Paket NurLesend 18/18, 5 Mutationen rot, echte Läufe gegen NB-Kopie bytegleich · offen als eigener kleiner Punkt: `backtest_llm1_historisch.py`, `pruefe_rollenkette.py` – ⚠️ 18.09. präzisiert: `backtest_llm1_historisch` ist **Produktionscode** (`rollen_eingabe` importiert `waehrung_je_symbol`), die Umstellung braucht daher die volle Prüfung · ✔ **Restpunkt erledigt 18.09.**: beide Skripte auf `mode=ro`, Prüfung auf mehrere Öffnungen je Skript erweitert | erledigt |
| 0.5 | Planbereinigung: A9 hat zwei Bedeutungen (Längsachse vs. Auflösung) → trennen; Schritt 42 „fertig“ nur durch Aufgehen in 59 kennzeichnen; 37 Status an 2.432 angleichen; 43/25 Rückverweis auf 59; R-R11 im Regelwerk doppelt vergeben; 2.414 unter „gilt“ als Hinweis kennzeichnen · ✔ **ERLEDIGT 17.09.:** A9 bleibt die Längsachse, die Hebel-Auflösung heißt so und trägt keine Nummer; Schritt 37 auf fertig (2.432 beantwortet ihn); Schritt 42 im Titel als „in 59 aufgegangen“; 43 und 25 mit Rückverweis auf 59; Band-Regel im Manual ist jetzt **R-R12** (R-R11 bleibt die Reproduktionspflicht), Fakten-Mappe nachgezogen; 2.414 als Hinweis gekennzeichnet; Vorgabe KRYPTO-ZUERST auf **offen** | erledigt |
| 0.6 | Am NB nachsehen: geltende Wiederholungssperre – Desktop-`config.yaml`: Krypto **12 h** (seit 28.08.), **gehebelt 3,5 h** (`cooldown_stunden_wenn_gehebelt`), Akkumulation 48 h; F-214 (05.09.) nennt 3,5 h → Begriffe angleichen; NB-Werte und `gegenpruefung.openrouter_aktiv` aus dem Export bestätigen · ✔ **ERLEDIGT 17.09. (aus Betriebsdaten der NB-Kopie 2026-09-17 04:41 abgeleitet, weil `config.yaml` nicht im Export steht):** Krypto ab Rollout 14.09. 17 UTC: 133 Folgeurteile ≥ 11,9 h, nur 5 kurze (3,5–4,0 h) – jedes nach einem Signal mit Hebel ≥ 2x → **Krypto 12 h, gehebelt 3,5 h ab `hebel_ab`** wirksam (`agent/wiederholung.py:120-127`); 371 kurze Abstände davor = alter Fehler O1 (Hebel ≥ 1,0, behoben 11.09., am NB ab 14.09.); Aktien/ETF/Rohstoffe **≥ 24 h**; Gegenprüfer **Z.ai** (Kontingent 16.09.: zai 27, openrouter 0). F-214 („3,5 h“) beschreibt den Stand vor 28.08./O1 | erledigt |
| 0.7 | ✔ **GEBAUT 17.09. zusammen mit 0.10** – **N1 umsetzen:** Kaufmails nicht vermessener Klassen kennzeichnen („nicht vermessen – Empfehlung beruht allein auf dem Modellurteil“) – Mailtext, Betreff-Prüfung, Prüfpaket | Bau klein, D-BETRIEB |
| 0.8 | **Stillstand und Abgrenzung** (N11 entschieden: (a)) – (1) Schalter, der NUR die LLM-Aufrufe anhält; (2) Bestandsaufnahme, was Multiasset im Code, in den Daten und in den Mails von Krypto abgrenzt, damit der spätere Umbau ohne Probleme erfolgen kann. Ursprüngliche Frage: Was bewirken `rollen_kette.aktiv_fuer` (Gruppe entfernen → `bedient_neue_kette` → alter Pfad?) und `betriebsart: probe` (Mail gebaut, nicht versandt – Modellaufrufe laufen weiter)? Welcher Schalter hält **nur die LLM-Aufrufe** an, ohne Bestand, Preise, Kursreihen, Datenfrische zu stoppen? Ergebnis: Stillstands-Verfahren für § 6a · ✔ **RECHERCHE ERLEDIGT 17.09.** (Befunde 2.456-llm-pause, 2.456-etf-knopf, 2.456-abgrenzung): **kein** Schalter hält nur die Modellaufrufe an (`probe` stoppt nur den Versand; `trocken`, Schlüssel entfernen, Kontingent erschöpfen legen die deterministische Hebelführung still; `aktiv_fuer` schaltet den alten Weg ein); Konfiguration wirkt erst nach Neustart; Kategorie-Synthese und Marktscan-Erfolgsmessung rufen ebenfalls Modelle; ⚠️ GUI-Lücke: Analyseknöpfe für Themen-ETF und Absicherung starten die alte Pipeline mit echtem Aufruf; `signals` ohne Assetklasse, Mails ohne Klassenkennzeichen | erledigt |
| 0.9 | **ETF-Knopf-Lücke schließen** (2.456-etf-knopf): Sperre über `assetklassen.gruppe(asset)` statt Watchlist-Feld · ✔ **GEBAUT 17.09.:** Regel `rollen_job.alte_analyse_hinweis` behandelt die Watchlist-Klasse `etf` fail-closed (gesperrt, sobald `themen_etf` oder `hedge` aktiv), Oberfläche übergibt `assetklassen.gruppe(asset)`; Paket GuiKette +4 Prüfungen (26/26), 3 Mutationen je rot, Verhaltensprobe an der echten Watchlist (DBPK/3QSS hedge, G2X/X136 themen_etf gesperrt); am Notebook K13 | gebaut, K13 offen |
| 0.10 | **Abgrenzung Multiasset** (2.456-abgrenzung, N11): Gruppe beim Schreiben in `signals` festhalten; zusammen mit 0.7 die Kennzeichnung in `signal_mail.baue_mail` (Betreff und Kopf, Merker `vermessen`) und in der Verkaufs-Sammelmail · ✔ **GEBAUT 17.09. (mit 0.7):** Spalte `signals.gruppe` in allen drei Schreibwegen (Altzeilen leer, D3); Einzelmail nicht vermessener Gruppen mit Betreff-Zusatz `· Themen-ETF, nicht vermessen` und erster Zeile `⚠️ NICHT VERMESSEN – …` (D1), Merker aus der Entscheiderstufe, ohne Merker fail-closed nach Gruppe; Krypto unverändert (D2); Verkaufs-Sammelmail mit Bereich in Betreff und Kopf (D4); Export mit `gruppe`. Paket Abgrenzung 11/11, 10 Mutationen je rot; Prüfstand `simuliere_kette.py` mit Modell-Attrappe auf NB-Kopie: Mails G2X, X136 (Themen-ETF), VST (Aktien), DBPK (Absicherung) gekennzeichnet, Zeile `gruppe=hedge` geschrieben; am Notebook K14 | gebaut, K14 offen |
| 0.11 | **Pausenschalter nur für Modellaufrufe** (2.456-llm-pause): Schlüssel `rollen_kette.modellaufrufe: pausiert` nach Vorschlag im Befund – eigene Voranalyse; gebraucht erst vor Phase 8 (Messfenster), deshalb nach 0.9/0.10/0.7 | Bau mittel |
| 0.12 | **Tote Mail-Abschnitte reparieren** (2.457-w3, Nutzerentscheidung V7 vom 17.09.): „Umfeld“ und „Zusatzinfo“ lesen `bc_ein["fakten_roh"]`, das niemand setzt, und das falsche Feld `beurteilung`. Lagebild direkt lesen, Feld `einstufung`. **Nur Mail, keine LLM-Eingabe** – ändert keine Messung. Kleiner Bau nach den Doku-Paketen, vor Phase 1 · ✔ **GEBAUT 17.09.** (X1–X4): Umfeld zeigt Lage, Gleichlauf (nur Krypto) und die Einstufung der eigenen Klasse mit Begründung; Zusatzinfo aus dem laufenden Terminmarkt-Abruf, Fehlendes wird protokolliert. **`bc_ein` in allen 41 Fällen bitgleich** – kein neuer Prompt-Stand, kein anderer Fingerabdruck. Paket Mailabschnitte 18/18, 6 Mutationen rot. Offen (Schritt 33): Finanzierungsrate (Einheit unbelegt, 2.457-w6), `btc_relativwert_pct`, Zusatzwerte für Aktien/Rohstoffe/Absicherung | erledigt, K16 offen |
| 0.13 | **Datenarchäologie** (Nutzerentscheidungen Y1–Y4): Was liegt für Phase 1 schon vor, was lässt sich rekonstruieren, was muss protokolliert werden – und trägt der Bestand eine LLM-Messung? · ✔ **ERLEDIGT 18.09.** (2.458-archaeologie, 2.458-fallzahl): Trichter seit 14.08. vorhanden (15.496 Läufe **mit Gründen**), Anlass-Stufe je Symbol (177.885 Zeilen); **Rekonstruktionsprobe negativ** – `potential_r` ist nicht nachrechenbar (Ziel nirgends gespeichert, `marktrang.raenge` ohne Stichtag); der laufende Prompt-Stand trägt nur **24 entschiedene Fälle** | erledigt |

### Phase 1 – Protokollierung schaffen (Bau, eigene Voranalyse) — *parallel zu Phase 2–3 möglich*

**Ziel:** Die Messgrößen, die live fehlen, ab sofort mitschreiben – **jeder Tag ohne sie ist für die Messung verloren.**

| Paket | Inhalt |
|---|---|
| 1.1 | Stufe **und Grund** je Zelle (Lauf × Gruppe × Symbol × Strategie) statt nur Summen · ⚠️ 0.13: je **Lauf** liegt beides seit 14.08. vor (`gate_durchlaessigkeit`, 15.496 Läufe), je **Symbol** nur für die Stufe `anlass` – zu bauen ist die **Zuordnung je Zelle**, nicht die Erfassung von vorn · ✔ **GEBAUT 18.09.** (2.458-protokoll-2): neue Tabelle `zellen_lauf` mit Stufe, Ergebnis, Grund, Art, Kontext und Verweis auf die Signalzeile; Filter nach A5 (ab `urteil` plus `auswahl`) – rund 193 statt 4.965 Zeilen je Tag |
| 1.2 | `potential_r`, Schwelle, Quote, Beitragslage **auch bei durchgelassenen** Einstiegen und beim Hebel · ⚠️ 0.13: **nicht rekonstruierbar** (Ziel fehlt, Ränge ohne Stichtag) – ohne Protokoll ist diese Größe für die Vergangenheit dauerhaft verloren. **Höchste Priorität in Phase 1** · ✔ **GEBAUT 18.09.** (2.458-protokoll-1): eine Funktion `_potential_dazu` an **beiden** Zeilenarten |
| 1.3 | Phase als eigenes Feld: Einstieg · Führung (Nachkauf auf Bestand / Hebel auf Spot-Bestand) · Ausstieg · Akkumulation · ✔ **GEBAUT 18.09.**: neue Spalte `signals.phase`, abgeleitet aus Aktion, Strategie und Bestand – `strategie` bleibt unberührt |
| 1.4 | Speicherort für Empfehlungen aus **Hebelführung, Positionsführung, Ausstiegsführung/Stop-Nachziehen** mit Kurs zum Zeitpunkt · ✔ **GEBAUT 18.09.** (2.458-protokoll-3): Tabelle `fuehrung_lauf`, Empfehlungen **und** geprüfte Positionen ohne Empfehlung |
| 1.5 | Ausgangskategorie für Ausstiege in `outcome_*` (2.401) bzw. eigene Folgebewegung · ✔ **GEBAUT 18.09.** (2.458-protokoll-4, schließt 2.401): eigene Ausstiegsfelder, zwei Horizonte (5/20 Handelstage), richtungsbereinigt in Prozent, gemailte **und** stumme Ausstiege, **rückwirkend nachgezogen** – 224 von 611 sofort gemessen |
| 1.6 | Zeile auch bei gesperrter Akkumulation und bei nicht vermessener Klasse (Kennzeichen) · ✔ **GEBAUT 18.09.**: gesperrte Akkumulation als Zeile in `zellen_lauf` (höchstens eine je Tag und Zelle); nicht vermessene Klassen deckt bereits 1.1 ab |
| 1.7 | `kurs_bei_empfehlung_eur` für **alle** Zeilen · 0.13: näherungsweise aus der Tagesreihe rekonstruierbar (Tagesschluss statt Live-Kurs) – trotzdem mitschreiben, der Unterschied ist genau die Intraday-Bewegung · ✔ **GEBAUT 18.09.**: an allen drei Schreibwegen |

Prüfung: Prüfpaket mit Mutationen, Standard-DB-Wächter, Trockenlauf gegen NB-Kopie, NB-Kontrolle nach Pull.

### Phase 2 – Live-Zählung (Frageart `zaehlung`, nur HINWEIS)

✔ **WERKZEUG GEBAUT 18.09.** (2.459-zaehlung): `zaehle_kette.py`, sechs Sichten, nur lesend; Schichtung nach Prompt-Stand und an der Linie 01.09. ist im Werkzeug erzwungen, Krypto und Nicht-Krypto getrennt, keine Quote unter zehn Fällen. Paket Zaehlung 11/11, 7 Mutationen rot. **Vollständig laufen lassen, sobald K19/K20 am Notebook bestätigt sind** – Führung und Ausstiege tragen erst dann bei.

Trichter je Stufe und Art über die Läufe; Entscheider-Vierfeld (durchgelassen vs. verworfen, Ausgang); BC NICHTS_TUN vs. Kauf; G-Einwand vs. Folge; Nicht-Krypto getrennt. Ausgabe als Tabelle mit Zeitfenster und Hinweis-Kennzeichen. **Keine Güte-Urteile.**

### Phase 3 – Historische Messung der deterministischen Kette (Normurteile)

Werkzeug aus Schritt 29/30 (Basis `simuliere_kette.py`/N-67-Muster), Zielgröße `bewegung_r`, ab 2023.

1. **R-R11:** `funding`, `turnover`, `oi_aenderung` in der Kette reproduzieren.
2. Kette gesamt gegen Nullwelten.
3. Beitrag je Stufe (auswahl, terminmarkt, entscheider) als „mit gegen ohne“.
4. Wiederholungssperre als Hinweis + Nutzerfrage Regel 1.
5. ⚠️ **NEU 18.09. (2.459-ungemessen): die vier ungemessenen Größen der Modelleingabe messen** – `referenz_spy` (relative Stärke gegen den S&P-500-ETF, **läuft live mit**), `fundamental_wachstum` (Gewinn-/Umsatzwachstum bei Aktien, **läuft live mit**), `stablecoin_kapital` und `optionsmarkt_dvol_skew` (stumm, seit 18.09. aus dem BC-Prompt gefiltert). ⚠️ Für `referenz_spy` **vor** der Messung klären, gegen welchen Maßstab gemessen wird – der S&P-500-ETF ist für Krypto ein fremder. ⚠️ Für `fundamental_wachstum` gibt es keine Messbasis (Aktien) – gehört in die Multiasset-Schiene.

Gegenprüfung: `selbsttest_messanlage.py` (Anlage), Positivkontrolle je Lauf, Nullwelten-Fehlalarm, Messkopf mit `messmenge.zeile()`.
**Voraussetzung:** Entscheidung **N3** (A8).

### Phase 4 – Hebel (Einstieg und Führung)

1. **A1 lösen** (Schritt 35): Fehlalarmquote der Barrieren-Anlage auf Nullwelten, Eichung `barriere`.
2. Danach: Hebel-Einstieg auf `barriere`; r(q)-Simulation; „derselbe Trade als Spot“.
3. Führung: nach Phase 1 (1.4) Regeln der Hebelführung gegen „halten“; Stopregel mit Schritt 52.
4. Vorher zulässig: nur HINWEIS „Spot gegen Hebel auf `bewegung_r`“ (Entscheidung **N6**).

### Phase 5 – Ausstieg und Reduktion (Schritt 43 (1))

Gütemaß „war der Verkauf richtig?“ gegen Nullmodell „halten“, historisch neu bauen; Live-Hinweis 2.403 reproduzieren (R-R11); REDUZIEREN und VERKAUFEN getrennt; Hebel-Ausstieg getrennt (7c).

### Phase 6 – Akkumulation (Schritt 25)

2.286/2.287 reproduzieren; Zeitstabilität H90 (Permutationstest); Überschneidung schnitt/funding/oi; Zielgröße `verbilligung`. Erst bei tragendem Beitrag: Sperre aufheben (eigene Nutzerentscheidung).

### Phase 7 – Nicht-Krypto: nur Zählung in 59 — *Bewertung in die Multiasset-Schiene (§ 1a)*

In Schritt 59 nur: Trichter und Anzahl der Nicht-Krypto- und Absicherungsempfehlungen zählen, N1-Kennzeichnung prüfen. **Die eigentliche Bewertung** (Messbasis Aktien/Themen-ETF/Rohstoffe, Kandidaten aus Kursreihe und Fundamentaldaten, Absicherung als Portfoliofrage, Rollenfrage R2) wird ein **eigener Schritt im Block SPÄTER**, begonnen erst nach Abschluss der Krypto-Kette.

⚠️ **Für Schritt 33 vorgemerkt (18.09., 2.459-ungemessen):** `referenz_spy` und `fundamental_wachstum` laufen heute **ungemessen** in der BC-Eingabe mit. Sie bleiben **unangetastet**, bis die Basislinie steht – eine Eingabeänderung mitten in der Messung würde sie teilen. Danach: aufnehmen, wenn sie tragen, sonst entfernen. Zusammen mit **W1** zu entscheiden.

### Phase 8 – LLM-Ebene als Basislinie (misst, ändert nichts)

Die Fragen aus § 5.2 auf den Live-Daten plus Phase-1-Protokoll, alle als HINWEIS mit ausgewiesener Datenlänge; BC bei Nicht-Krypto zuerst (einzige Entscheidung). Optional LLM historisch (`backtest_llm1_historisch.py`) nur nach Entscheidung **N7** (Kontingent, Vorwissen-Problem).

### Phase 9 – Zusammenführung und Entscheidungsvorlage

Matrix ausgefüllt (Zahl · Güte · Beitrag je Zelle, mit Urteilsart); daraus Vorlagen für **Schritt 33** (Rollen: was bekommen sie künftig – z. B. Potential/Schwelle, R1 Blockierrecht, R2 Absicherung), **43**, **25/26**, **60**, Hebel-Freigabe. Befund, Plan, Memory, Register.

---

## 6a Stillstand der Produktion – wann nötig, wie gering zu halten

(Nutzerhinweis 17.09.: *„Berücksichtige auch erforderlichen Stillstand der Produktion für Messungen und Simulationen im LLM-Bereich.“*)

**Warum überhaupt Stillstand:** Messungen und Simulationen mit **echten Modellaufrufen** teilen sich Schlüssel und Tageskontingente mit dem Notebook (Gemini 500 je Modell/Tag, Z.ai, OpenRouter 1.000/Tag; heute ~80–130 Gemini- und ~25–45 Z.ai-Aufrufe im Betrieb). Außerdem verändert ein Lauf, der während der Messung Signale schreibt oder Cooldowns setzt, die Messmenge. Deterministische Messungen laufen dagegen am Desktop auf Kopien und Messbasen – **ohne** Stillstand.

| Phase / Tätigkeit | Stillstand nötig? | Art |
|---|---|---|
| 0 Grundlage, Doku, kleine Fixes | nein | nur Pull + ggf. kurzer Neustart |
| 1 Protokollierung bauen | nein | Pull + Neustart (Minuten), NB-Kontrolle |
| 2 Live-Zählung | nein | Kopie der NB-Sicherung |
| 3–6 historische deterministische Messung (Krypto) | **nein** | Desktop, Messbasen, `mode=ro` |
| 8 LLM-Basislinie auf **gespeicherten** Live-Daten | **nein** | Kopie |
| 8 LLM mit **wiederholten Aufrufen** (Rauschboden drei Arme, Prüfstand mit echter config.yaml, Rolle A/BC/G gegen gleiche Eingaben) | **ja – LLM-Teil der Kette pausieren** | Messfenster, Kontingent reservieren |
| 8 LLM historisch (N7 – vorerst nein) | ja | entfällt vorerst |
| 9/33 Prompt- oder Eingabevarianten (A/B) | **ja** | Messfenster je Variante; alternativ getrennte Schlüssel |
| Protokoll- oder Kettenumbau mit Migration | kurz | Neustart, Sicherung vorher |

**Verfahren (Ausarbeitung in Phase 0.8, dann Abstimmung):**

1. **Messfenster** vorher mit dem Nutzer festlegen (Dauer, Zeitpunkt); in dieser Zeit entstehen **keine Empfehlungen** – bei Krypto (24/7) ist das ein echter Verzicht und wird so benannt.
2. **Nur den LLM-Teil anhalten**, nicht Bestand, Preise, Kursreihen, Datenfrische, Sicherung – welcher Schalter das sauber leistet, klärt 0.8 (`aktiv_fuer`, `betriebsart`, App-Stopp sind jeweils zu grob oder mit Nebenwirkung).
3. **Vorher/nachher:** Sicherung, Export, Zeitpunkt im Messkopf; nach dem Fenster Kontrolle, dass die Kette wieder scharf läuft (wie K-Kontrollen).
4. **Kontingent-Budget je Messung** vorab rechnen (Aufrufe × Arme × Wiederholungen) und gegen die Tagesgrenzen prüfen – lieber mehrere kurze Fenster als eines, das das Kontingent erschöpft.

---

## 7 Reihenfolge und Abhängigkeiten

```
Phase 0 ──► Phase 1 (Bau Protokoll) ──────────────► (sammelt Daten)
   │                                                     │
   ├──► Phase 2 (Zählung live) ◄─────────────────────────┤
   ├──► Phase 3 (historisch, deterministisch) ── N3
   │        └──► Phase 4 (Hebel) ── A1/Schritt 35, Schritt 52
   │        └──► Phase 5 (Ausstieg, 43(1))
   │        └──► Phase 6 (Akkumulation, 25)
   ├──► Phase 7 (Nicht-Krypto nur zählen) ── N1
   └──► Phase 8 (LLM-Basislinie Krypto) ◄── Phase 1 + 2 · Messfenster § 6a
            └──► Phase 9 ──► 60 → 43 → 25–27 → 33 (Krypto)
                                   └──► KRYPTO ABGESCHLOSSEN
                                            └──► Multiasset-Schiene (SPÄTER): Bewertung Nicht-Krypto, Absicherung, Rollen R2
```

- **Warten auf 59:** Schritt 33 (LLM), Schritt 60 (Krypto stabil).
- **Geht in 59 auf / liefert zu:** 42, 29, 30, 43 (1), 25, 35, 37, 52.
- **Laufen parallel weiter:** Schritt 61 Stufe 1.5/1.6, 55, 56, 62.

---

## 8 Entscheidungen für den Nutzer

**Nutzerentscheidung 17.09.: N1 bis N10 wie empfohlen.** Nachträglich angepasst durch § 1a: **N4** – Nicht-Krypto nicht als eigener D-Schritt, sondern als Multiasset-Schiene im Block SPÄTER nach Abschluss Krypto (folgt dem Nutzervorschlag 17.09.; bei Abstimmung bestätigen). **N11 neu offen.**

| # | Frage | Optionen | Empfehlung |
|---|---|---|---|
| **N11** | Die Multiasset-Ketten laufen scharf ohne gemessene Bewertung. Was bis zum Beginn der Multiasset-Schiene? | (a) weiterlaufen mit N1-Kennzeichnung · (b) Mailversand aus, Kette zählt weiter · (c) Gruppen ganz aus | ✔ **ENTSCHIEDEN 17.09.: (a)** – Nutzer: *„diese läuft bereits seit Wochen falsch, so belassen bis zum Plan und Umsetzung – nur sauber abgrenzen und kennzeichnen, damit der Umbau danach ohne Probleme erfolgen kann, wenn Krypto fertig ist“*. ⚠️ Nicht über `aktiv_fuer` abschalten (Rückfall auf die alte Pipeline). |
| **N1** | Nicht-Krypto-Kaufempfehlungen beruhen allein auf dem LLM (§ 1). Wie bis zur Messung? | (a) so lassen, in der Mail kennzeichnen „nicht vermessen – nur Modellurteil“ · (b) sperren wie die Akkumulation am 11.09. · (c) nur Ausstiege/Reduktionen zulassen | **(a) sofort kennzeichnen**, (b) als Nutzerentscheidung offen – Regel 4 verbietet eine Sperre nach Datenlage nicht, weil hier die Messung der ganzen Lage fehlt (gleiche Begründung wie 11.09.) |
| **N2** | Phase 1 (Protokollierung) vorziehen und parallel bauen? | ja / nach Phase 0 | **ja, direkt nach Phase 0** – jeder Tag ohne Protokoll fehlt später |
| **N3** | A8: auf welcher Menge gilt die Bewertung? | (a) Kette entscheidet auf breiterer Menge · (b) Bewertung gilt ausdrücklich nur auf Stellvertretermenge validiert | **(b)** für Phase 3, mit Kennzeichnung; (a) als spätere Umbaufrage |
| **N4** | Nicht-Krypto (N-8) als eigene Phase in 59 oder als eigener Schritt (SPÄTER)? | in 59 / eigener Schritt | **eigener Schritt im Block D-BEWERTUNG**, in 59 nur Zählung und LLM-Hinweis |
| **N5** | W1: Terminmarkt-Sätze bei BC – nie eigens entschieden, gegen Beschluss 17.08. (G soll unabhängig widersprechen können). Wie weiter? | (a) bis zur Messung **unverändert lassen**, aber dokumentieren und G-Messung ab 01.09. getrennt · (b) Anlass-Fingerabdruck auf die Terminmarkt-Werte stützen, **ohne** sie in den BC-Prompt zu geben (stellt 17.08. wieder her; Code-Änderung an der Kette) · (c) Einspeisung als neue Regel bestätigen und R-R2/G3/R-R7 ändern | **(a) jetzt**, (b) als Teil von Schritt 33 vorbereiten – eine Eingabeänderung mitten in der Basislinienmessung würde die Messung teilen |
| **N10** | Meta-Labeling (Methodik §G, offen seit August): misst 59 BC als **Richtungsgeber** oder nur als **„nehmen / nicht nehmen“** einer gerechneten Empfehlung? | Richtungsgeber (heutige Rolle) / Filter (Meta-Label) / beides | **beides als getrennte Fragen** – heutige Rolle messen (Basislinie), Filterfrage als Vorlage für 33 |
| **N6** | Hebel vor A1: HINWEIS „Spot gegen Hebel auf `bewegung_r`“ zulassen? | ja, gekennzeichnet / nein, erst nach A1 | **ja, als HINWEIS** – Normurteil erst nach A1 |
| **N7** | LLM historisch mit echten Aufrufen testen? | ja (Kontingent, Vorwissen prüfen) / nein | **nein vorerst** – erst Live-Basislinie (Phase 8) |
| **N8** | Wiederholungssperre (Uhr, 94 % Filter) gegen Regel 1 | in 59 messen und dann entscheiden / sofort diskutieren | **in Phase 3 als Hinweis messen**, Entscheidung danach |
| **N9** | Reihenfolge der Bewertungsphasen 4–6 | Hebel → Ausstieg → Akkumulation (Priorität 11.09./15.09.) | **so**, mit Phase 3 als gemeinsamer Grundlage |
| ~~**N12**~~ **ENTFÄLLT als Entscheidung** (18.09.) | Die Frage war falsch gestellt: nicht *einfrieren oder laufen lassen*, sondern **gemessen oder nicht** – und die Antwort folgt aus der stehenden Regel **R-R4/P1** (*Verfügbarkeit ist kein Aufnahmegrund; Aufnehmen ist ein Tausch*). Beide Sätze sind **nie gemessen** worden. | **Ersetzt durch vier Schritte** (2.459-ungemessen): (1) alle vier ungemessenen Größen als **Kandidaten registriert**; (2) die zwei **stummen** (Stablecoin, Optionsmarkt) aus dem BC-Prompt **gefiltert** – Fehlerkorrektur, heute folgenlos, weil kein Satz entsteht; (3) in **Phase 3 messen**; (4) in **Schritt 33** bewusst entscheiden | ✔ erledigt 18.09. |

---

## 9 Risiken und Fallen

1. **Gedachte statt tatsächliche Eingabe messen** (Nutzerhinweis 16.09.) → § 3 ist die verbindliche Grundlage; vor jeder LLM-Messung gegen den Code am Messtag neu abgleichen.
2. **Normurteil auf zu kurzer Live-Zeit** → live nur Zählung/Hinweis, Blockzahl in jedem Kopf.
3. **Falsche Zielgröße** (Hebel auf `bewegung_r` statt `barriere`) → Norm-Tabelle `ZIELGROESSE_JE_LAGE` als Pflichtfeld.
4. **Selektierte Menge vs. frei** verwechselt (06.09.) → `messmenge.zeile()` im Kopf, Frageart vorab.
5. **Registrierte Beiträge „widerlegt“ ohne Reproduktion** → R-R11 als erster Arbeitsschritt jeder Phase.
6. **Produktions-DB beschrieben** (api_health, `messe_ausstiegsguete.py`) → nur Kopien, `mode=ro`, Wächter.
7. **Kapitalbasis 16.07.–16.09. zu hoch** (Staking doppelt) → Hebel-/Betragszahlen aus diesem Zeitraum nicht als Maßstab.
8. **Namen** → Rollen nur nach R-R1 (Marktanalyst, Händler, Gegenprüfer); `entscheider` ist eine Rechenstufe.
9. **Veraltete Memory-Schnappschüsse** (Cooldown-Eintrag war bis 17.09. veraltet) → Register vor Memory.
10. **Absicherung mit Spot-Zielgröße** fachlich falsch gemessen → eigene Frage, nicht in die Spot-Matrix mischen.
11. **Prompt-Stände vermischt** (2.078 alte gegen 266 neue BC-Zeilen) → Schichtung Pflicht, sonst misst man einen Durchschnitt zweier Rollen.
12. **Nichtdeterminismus** (8–12 % Dreher) als Befund missverstanden → Rauschboden mit drei Armen.
13. **Vorwissen des Modells** bei historischen Ankern → nur Vorwärtsmessung.
14. **BC und G seit 01.09. nicht unabhängig** (W1) → G-Aussagen vor/nach 01.09. getrennt.
15. **Basisdokumente beschreiben Soll, nicht Ist** (§ 3a) → vor jeder Messung am Code bestätigen, nie aus Landkarte/Regelwerk allein ableiten.

---

## 10 Gegenprüfung dieses Plans (17.09.2026)

| Aussage | geprüft wie | Ergebnis |
|---|---|---|
| Zielgröße je Lage (Hebel = `barriere`) | `messnorm.py:191-197` | ✔ |
| 33 und 60 warten auf 59 | `soll_ist.py:1205`, `:1440` | ✔ |
| Cooldown F-174 durch F-214 geschlossen | REGISTER_Fakten | ✔ (Memory korrigiert) |
| BC bekommt Terminmarkt | `rollen_lauf.py:1553-1565` | ✔ |
| G-Prompt behauptet das Gegenteil | `zweite_meinung.py:451` | ✔ |
| A-Einstufung überschrieben | `rollen_lauf.py:1505` | ✔ |
| `potential_r` nur bei `gate_passed=0`, seit 14.09. | NB-Kopie: 67/1.170 vs. 0/1.174 | ✔ |
| Protokollfehler `null_ziehungen` | `messnorm.py:818` | ✔ |
| `messe_ausstiegsguete.py` ohne `mode=ro` | Z. 109/115 | ✔ |
| Nicht vermessene Klassen werden durchgelassen | `rollen_lauf.py:2481-2488`; `BEITRAEGE` nur `klassen=("krypto",)` | ✔ |
| Datenzahlen § 4 | Abfragen auf Kopie `tradinginfotool_2026-09-17_0441` | ✔ |
| Quelle „Schritt 5, 01.09.“ (W1) | Anforderungen_Umbau_28_08 Z. 443/601/697; Regelwerk_Entscheidungslog Z. 16584-16590; letzter Log-Eintrag Z. 17497 (19.08.) | ✔ gefunden: Anlass-Entscheidung, BC-Einspeisung technische Folge, gegen Beschluss 17.08. |
| Zwei BC-Prompt-Stände, ein Modell | NB-Kopie: `2026-08-17e` 2.078 · `2026-09-11a` 266 | ✔ |
| 867 G-Urteile | NB-Kopie | ✔ |
| `nur_eigen` entfernt nur den Rahmen (Börsenfluss), nicht OI/Funding | `positionierung.py:913-960`, `:1057-1077` | ✔ (Funding-Satz laut Code-Lesung enthalten) |

**Quellen:** `soll_ist.py` (Schritte 25, 29, 30, 33, 35, 37, 42, 43, 52, 59, 60, 61), `messnorm.py`, `agent/rollen_lauf.py`, `agent/rollen_gate.py`, `agent/rollen_eingabe.py`, `agent/rolle_analyst.py`, `agent/rolle_trader.py`, `agent/zweite_meinung.py`, `agent/positionierung.py`, `agent/potential.py`, `agent/wahrscheinlichkeit.py`, `agent/hebelfuehrung.py`, `agent/krypto/backward_tracking.py`, `Basisinfos/REGISTER_Befunde.md`, `REGISTER_Kandidaten.md`, `REGISTER_Fakten.md`, `Regelwerksmanual.md` (R-R1, R-R7, R-R11), `Kette_Landkarte.md`, `Gesamtplan_Wo_wir_stehen_28_08.md`; Befunde 2.391, 2.398, 2.389-richtung, 2.401, 2.403, 2.432, 2.438, 2.451-absicherung, 2.455-hebelsignale, 2.455-hebel-nachkaufen; Fakten F-174, F-214.
