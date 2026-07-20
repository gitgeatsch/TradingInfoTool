# Kategorie-Taxonomie — Basisinformationen für Release 2 (Schwerpunkte/Thesen-Verwaltung)

**Zweck dieses Dokuments:** Diskussionsgrundlage für den Aufbau der
Schwerpunkte/Thesen-Verwaltung (Release 2, Punkt #332-#334). Enthält die
vollständige Kategorie-Taxonomie aus `Basisinfos/kategorien.yaml`, eine
fachliche Einordnung pro Hauptgruppe (Thesen-Tauglichkeit, typische
Makro-Treiber), eine Übersicht, welche der im Projekt bereits angebundenen
Datenquellen für welche Hauptgruppe relevante Signale liefern, sowie einen
Vorschlag für das Datenmodell einer "These" als Ausgangspunkt für die
gemeinsame GUI-Konzeption.

**Wichtiger Hinweis zur Einordnung:** Die "fachliche Einordnung" unten ist
eine qualitative, allgemein anerkannte Makro-/Asset-Klassen-Logik (Lehrbuch-
Zusammenhänge: was tendenziell von welchem Umfeld profitiert) — **kein**
Backtesting-Ergebnis, keine Garantie, keine personalisierte Anlageberatung.
Sie soll nur als strukturierter Ausgangspunkt dienen, den du (ggf. mit
KI-Unterstützung über Punkt #333) im Betrieb selbst laufend hinterfragst und
anpasst.

---

## 1. Vollständige Taxonomie (10 Hauptgruppen, 72 Unterkategorien)

Quelle: `Basisinfos/kategorien.yaml`, systematisch aus Bitpandas realem
ETF/ETC/Edelmetall-Katalog hergeleitet (211 Produkte, Stand 2026-07-19).
Krypto ist bewusst nicht Teil dieser Taxonomie (eigene Anlageklasse, andere
Struktur in der Watchlist).

### 1.1 Edelmetalle
Gold · Silber · Platin & Palladium · Diversifiziert

### 1.2 Industriemetalle
Kupfer · Seltene Erden & strategische Metalle · Aluminium · Nickel · Zink ·
Blei · Zinn · Diversifiziert

### 1.3 Energie
Rohöl · Erdgas · Benzin & Heizöl · Diversifiziert (Energie-Rohstoffe) ·
Erneuerbare & Clean Energy · Uran / Kernenergie · Batterietechnologie ·
Energieversorger (Aktien) · Energie-Förderer (Aktien)

### 1.4 Agrarrohstoffe & Nahrungsmittel
Getreide · Ölsaaten · Genussmittel · Vieh · Diversifiziert · Forstwirtschaft ·
Wasser · Nahrungsmittel der Zukunft (Aktien)

### 1.5 Technologie & KI
Künstliche Intelligenz · Cybersicherheit · Halbleiter · Robotik &
Automatisierung · Internet der Dinge · Blockchain (Aktien) · Fintech ·
5G/Mobilfunk · Digitalwirtschaft · Metaverse · Gaming & eSports ·
Internet-Infrastruktur · Breite Technologie-Indizes · Smart Cities ·
Telemedizin · E-Commerce · Biotech · Zukunft der Mobilität

### 1.6 Absicherung / Hedge
Aktienmarkt-Short (breit) · Sektor-Short

### 1.7 Aktien — Regionen & Länder
Global/Entwickelte Welt · Emerging Markets (breit) · Europa (breit) ·
Nordamerika (breit) · USA (breit) · Asien-Pazifik (breit) · Einzelne
Länder/Märkte (42 Einzelmärkte, u. a. China, Indien, Japan, Brasilien,
Türkei, Vietnam)

### 1.8 Aktien — Sektoren
Finanzen · Gesundheit · Konsum (zyklisch) · Konsum (Basiskonsumgüter) ·
Industrie · Kommunikationsdienste · Grundstoffe · Immobilien

### 1.9 Anleihen & Geldmarkt
Staatsanleihen · Unternehmensanleihen · Hochzinsanleihen ·
Inflationsgeschützt · Geldmarkt · Sonstige (Green Bonds, MBS, Aggregate)

### 1.10 Sonstige
Faktor-/Strategie-ETFs (Dividende, Momentum, Value, Quality, Size) ·
Nischenthemen (Luxus, Tourismus, Private Equity, Carbon, Ageing Population)

---

## 2. Fachliche Einordnung pro Hauptgruppe

| Hauptgruppe | Thesen-Tauglichkeit | Typischer Makro-Treiber | Beispiel-These (analog deinen eigenen) |
|---|---|---|---|
| Edelmetalle | **Hoch** | Fallende Realzinsen, lockere Geldpolitik, Inflationsangst, geopolitische Unsicherheit | "Geld wird günstiger" → Gold/Silber übergewichten |
| Industriemetalle | **Hoch** | Infrastruktur-/Elektrifizierungs-Investitionszyklen (Rechenzentren, E-Mobilität, Netzausbau), China-Konjunktur | "Rechenzentren werden gebaut" → Kupfer übergewichten |
| Energie | **Hoch** | Angebotsverknappung, geopolitische Lieferrisiken, strukturell steigende Nachfrage (KI-Rechenzentren, E-Mobilität-Übergang) | "Alles wird teurer, besonders Energie" → Energie übergewichten |
| Technologie & KI | **Hoch**, aber granular | Zins-/Liquiditätsumfeld (Growth-Bewertung reagiert stark auf Zinsen), Innovationszyklen | Eher Unterkategorie- als Hauptgruppen-Ebene sinnvoll (z. B. gezielt "Halbleiter", nicht "ganz Technologie") |
| Aktien — Sektoren | **Hoch** | Klassische Sektor-Rotation über den Konjunkturzyklus (zyklisch vs. defensiv) | Deckt sich mit der bereits bestehenden Sektor-Rotations-Logik in `agent/themen_etf/analyst.py` |
| Agrarrohstoffe & Nahrungsmittel | Mittel | Wetterextreme, Inflations-Hedge, geopolitische Exportbeschränkungen | Eher episodisch/reaktiv als dauerhafte Schwerpunkt-These |
| Anleihen & Geldmarkt | Mittel | Leitzinserwartung, Rezessionsrisiko (Flucht in Staatsanleihen) | Eher Cash-Reserve-/Defensiv-Entscheidung als "Übergewichten"-These |
| Aktien — Regionen & Länder | Mittel | Relative Wachstumsdifferenzen, Währungseffekte, regionale Geldpolitik | Breiter/unschärfer als sektorale Thesen, aber sinnvoll für "diese Region meiden/übergewichten" |
| Absicherung / Hedge | Eigene Rolle | Reagiert auf bestehendes Portfolio-Exposure, nicht auf eine eigene Makro-These | Wird eher situativ (Bärenmarkt-Overlay, bereits im System) als thesenbasiert aktiviert |
| Sonstige | Niedrig | Sammelkategorie ohne einheitlichen Treiber | Für Thesen-Zuordnung eher ungeeignet, Unterkategorien ggf. einzeln betrachten |

---

## 3. Datenquellen-Mapping

Das Projekt hat aktuell 24 echte, live angebundene Datenquellen (siehe
`remote/server.py::API_HEALTH_GROUPS`). Relevanz pro Hauptgruppe:

| Hauptgruppe | Relevante bereits vorhandene Datenquellen | Was sie liefern |
|---|---|---|
| Edelmetalle | FRED, Fear & Greed, EZB/PBoC/BoJ-Zinsdaten | Realzins-Niveau, globale Geldpolitik, Risk-off-Stimmung |
| Industriemetalle | CFTC COT, China M2 | Managed-Money-Positionierung in Futures, chinesische Liquidität (China treibt Industriemetall-Nachfrage strukturell) |
| Energie | EIA, CFTC COT | US-Lagerbestände/Förderdaten (Erdgas bereits live integriert), Positionierung in Öl/Gas-Futures |
| Agrarrohstoffe | CFTC COT | Positionierung in Agrar-Futures |
| Technologie & KI | Finnhub, SEC EDGAR, yfinance-Fundamentaldaten | Analysten-Kursziele/-Trends, Insider-Trading als Sentiment-Signal, Bewertungskennzahlen |
| Aktien — Sektoren | Finnhub, SEC EDGAR, FINRA | Analysten-Sentiment, Insider-Aktivität, Short-Interest |
| Aktien — Regionen | FRED, EZB, PBoC, BoJ, China M2 | Jeweilige Zentralbankpolitik als Regionaltreiber |
| Anleihen & Geldmarkt | FRED (Leitzinsen), EZB, BoJ, PBoC | Zinsniveau/-erwartung |
| Absicherung | Fear & Greed, bereits bestehender Aktien-Bärenmarkt-/VIX-Indikator | Risikoregime-Einschätzung |
| Sonstige | Keine spezifische Zuordnung | — |

**Wichtig, ehrlich eingeordnet:** Diese Datenquellen liefern heute schon
FAKTEN für die Signal-Pipelines der einzelnen Assets (z. B. fließt CFTC COT
bereits in `agent/rohstoff/analyst.py` ein) — es gibt aber noch KEINE
Aggregation auf Hauptgruppen-Ebene ("wie steht die gesamte Kategorie
Energie gerade da"). Das wäre die eigentliche neue Arbeit für Punkt #333
(KI-Vorschläge-Job), nicht Teil der heutigen Konzeption zu #332.

---

## 4. Diskussionsvorschlag: Datenmodell einer "These" (für #332)

Aktualisierter Stand nach gemeinsamer Besprechung (siehe Abschnitt 5 für
die Entscheidungen):

| Feld | Beschreibung |
|---|---|
| `hauptgruppe` / `unterkategorie` | Bezug auf `kategorien.yaml`-IDs (Unterkategorie optional — eine These kann sich auf die ganze Hauptgruppe ODER gezielt auf eine Unterkategorie beziehen, z. B. nur "Halbleiter" statt "ganz Technologie"). Die GUI zeigt bei einer Hauptgruppen-These immer live an, welche Unterkategorien darunter konsolidiert werden. |
| `richtung` | Übergewichten / Neutral / Meiden — bei Hauptgruppe "Absicherung" stattdessen Aktiv/Inaktiv (siehe Abschnitt 8, eigene Logik) |
| `staerke` | z. B. 1-5 oder Prozent-Zielgewichtung — wirkt sich in Stufe 1 NUR auf Hervorhebung/Sortierung aus, nicht auf das Scoring (siehe Abschnitt 5, Entscheidung zu #334) |
| `begruendung` | Freitext (deine eigene Einschätzung, z. B. "Rechenzentren werden gebaut") |
| `pruef_mechanismus` | NEU (siehe Abschnitt 7): strukturierter Verweis, welcher objektive Datencheck für diese Hauptgruppe anwendbar ist (M2/Fed, Zinskurve, Dollar-Index, COT-Positionierung, oder "kein automatischer Check") — ersetzt das ursprünglich vorgeschlagene freie `unterstuetzender_fakt`-Feld, da der Check je Hauptgruppe unterschiedlich ist |
| `gesetzt_am` | Datum der Erstellung |
| `review_am` | Wiedervorlage-Datum — Thesen sollen nicht "für immer" gelten, sondern regelmäßig neu bewertet werden. Die GUI schlägt einen Wert vor, abgeleitet vom Zeithorizont des `pruef_mechanismus` (siehe Abschnitt 7, letzte Spalte) — inkl. Klartext-Begründung ("Vorschlag: 4 Wochen, weil COT-Daten wöchentlich aktualisiert werden"), keine stille Vorbelegung |
| `status` | Aktiv / Erledigt / Verworfen |
| `quelle` | Manuell (von dir gesetzt) / KI-Vorschlag (Punkt #333, nach deiner Bestätigung) |

Wo das technisch lebt: vermutlich eine neue DB-Tabelle (nicht
`config.yaml`), da es sich um sich ändernde, app-verwaltete Daten handelt,
keine statische Konfiguration — analog zu `asset_hebel_settings` oder
`makro_analog_ergebnis`.

---

## 5. Entscheidungen (Stand nach gemeinsamer Besprechung)

1. **Granularität:** beide Ebenen erlaubt (Hauptgruppe ODER Unterkategorie).
   GUI zeigt bei einer Hauptgruppen-These transparent, was darunter
   konsolidiert wird.
2. **Einfluss auf Marktscan/Screener (#334), zweistufig:**
   - **Stufe 1 (jetzt):** nur Hervorhebung/Sortierung, KEINE
     Scoring-Gewichtung — Risiko-/Qualitäts-Gates (Retail-Konsens-Deckel,
     Regime-Konflikt etc.) bleiben immer unabhängig von jeder These.
     Hintergrund: eine aggressive Gewichtung würde bei trendgetriebenen
     Themen (Beispiel Technologie & KI) prozyklisch verstärken statt
     vorlaufend zu warnen — direkter Widerspruch zur bestehenden
     antizyklischen Risikogate-Philosophie im Projekt.
   - **Zusatz, TEIL DER ERSTEN UMSETZUNGSRUNDE (nicht erst Stufe 2):** neuer
     objektiver Fakt `these_abgleich` je Signal — prüft die aktive These NICHT gegen
     sich selbst (Beliebtheit), sondern gegen unabhängige, bereits im
     Projekt vorhandene Daten (siehe Abschnitt 7), Text landet im
     Signal-Reasoning. Kann eine hypebasierte These sogar als "objektiv
     nicht gestützt" kennzeichnen.
   - **Stufe 2 (später, vorsichtig):** echte Scoring-Gewichtung NUR für
     strukturelle/langsame Kategorien (Edelmetalle, Industriemetalle,
     Energie, Anleihen), NIE für Technologie & KI oder andere
     sentimentgetriebene Kategorien.
3. **Richtgröße:** 3-6 gleichzeitig aktive Thesen, weich in der GUI
   angezeigt, kein Hard-Limit im Code.
4. **KI-Vorschläge-Job (#333):** täglich (Muster wie `makro_analog_job`,
   06:30 Uhr). Rhythmus-Optimierung als Punkt für später vorgemerkt.
5. **Haltedauer/Zeithorizont wird berücksichtigt:** die Prüf-Mechanismen
   aus Abschnitt 7 haben unterschiedliche natürliche Zeithorizonte
   (COT-Positionierung wöchentlich aktualisiert → kürzerer Horizont
   sinnvoll; M2-/Liquiditätsregime monatlich, Zinskurve/Dollar-Index
   brauchen mehrere Monate Verlauf, um aussagekräftig zu sein → längerer
   Horizont). Der `review_am`-Vorschlag in der GUI orientiert sich daran
   (siehe Abschnitt 7, neue Spalte). Zusätzlich prüft `these_abgleich`
   einen möglichen Mismatch zwischen dem Zeithorizont der These und der
   Haltedauer-Empfehlung des konkreten Signals (bestehendes Feld
   `holding_duration`/`halte_kriterium_bucket`).
6. **Gehaltene Assets erhalten Priorität in der Stufe-1-Hervorhebung:**
   innerhalb einer Kategorie mit aktiver These werden zuerst bereits
   gehaltene Assets (`wird_aktuell_gehalten`, live aus den Holdings
   abgeleitet) angezeigt, danach neue Watchlist-/Screener-Kandidaten,
   danach alles Übrige. Begründung: bei einem gehaltenen Asset steht eine
   echte Entscheidung an (nachkaufen/halten/reduzieren), bei einem neuen
   Kandidaten nur "einen Blick wert" — unterschiedliche Dringlichkeit.
7. **Transparenz-Prinzip (durchgängig, ausdrücklicher Nutzer-Wunsch):**
   jede automatische Wirkung einer These — Sortierung, Hervorhebung,
   Review-Datum-Vorschlag, `these_abgleich`-Text — muss ihre konkrete
   Begründung sichtbar mitliefern, mit minimalem Interpretationsaufwand
   für den Nutzer. Keine stille Umsortierung ohne erkennbaren Grund, kein
   Badge ohne Klartext-Erklärung dahinter. Gilt für alle offenen Punkte
   aus Abschnitt 9 (Diversifikations-Tabelle-Markierung,
   Screener-Hervorhebung) genauso wie für `these_abgleich` selbst.

---

## 6. Acht Kandidaten-Thesen mit Mechanik ("wann funktioniert das grundsätzlich")

Alle acht mit echten Live-Daten unterlegt (Abruf 2026-07-19 über die im
Projekt bereits eingebundenen Quellen). **Ausdrücklich keine
Kaufempfehlung** — Mechanik + aktuelle Datenlage, Richtung/Stärke
entscheidest du.

| # | Kategorie | Mechanik — wann funktioniert das grundsätzlich | Aktuelle Datenlage |
|---|---|---|---|
| 1 | Energie (Hauptgruppe) | Profitiert von Angebotsverknappung/geopolitischen Lieferrisiken/strukturell steigender Nachfrage | WTI 83,49 $ / Brent 90,20 $ (deutlich erhöht). Erdgas-Speicher baut saisonal weiter auf (3.024 Bcf, +41 letzte Woche), ABER Managed-Money bei Erdgas ist netto SHORT (-105.709 Kontrakte) — gemischtes Bild |
| 2 | Edelmetalle | Profitiert von fallenden Realzinsen, lockerer Geldpolitik, Inflationsangst | Gold 4.025 $ / Silber 57 $ — Liquiditätsumfeld stützt fundamental (US-M2 +3,1%/6 Monate, Fed Funds nur 3,63%), ABER Positionierung bei Gold schon sehr gedrängt (35,7% des Open Interest Managed-Money-Long) — Rücksetzer-Risiko |
| 3 | Industriemetalle/Kupfer | Profitiert von Infrastruktur-/Elektrifizierungs-Investitionszyklen (Rechenzentren, E-Mobilität, Netzausbau) | Kupfer 6,30 $, Managed-Money moderat netto long (29,8%) — noch Spielraum, nicht annähernd so gedrängt wie Gold |
| 4 | Erneuerbare & Clean Energy | Profitiert als Substitutionseffekt bei dauerhaft hohen fossilen Energiepreisen | Keine direkte Live-Kennzahl im Projekt abrufbar (siehe Lücken, Abschnitt 8) |
| 5 | Anleihen & Geldmarkt (Inflationsgeschützt/Staatsanleihen) | TIPS: profitieren, wenn Inflation stärker steigt als eingepreist. Nominale Staatsanleihen: profitieren, wenn Zinsen fallen sollen (Konjunkturabschwächung) | Fed Funds 3,63%, 10-Jahres-Rendite 4,54% — spürbarer positiver Realzins-Abstand, Fed erkennbar im lockeren Modus |
| 6 | Aktien-Sektoren/Finanzen | Profitiert von steiler Zinskurve (lange Zinsen deutlich über kurzen, bessere Zinsmarge für Banken) | 10J-Rendite 4,54% vs. 3-Monats-Zins 3,71% = +0,83 Prozentpunkte — Kurve aktuell NICHT invertiert, leicht positiv |
| 7 | Aktien-Regionen/Emerging Markets | Profitiert von schwachem US-Dollar (billigere Dollar-Schulden) und lockerer Fed | Dollar-Index (DXY) aktuell 100,69 — **Trend seit Jahresbeginn 2026 klar AUFWÄRTS** (von 96,99 im Januar auf Höchststand 101,19 im Juni, im Juli leicht abgeschwächt auf 100,69). Das ist ein Gegenwind für diese These, kein Rückenwind — trotz lockerer Fed hat der Dollar sich seit Jahresbeginn eher gefestigt |
| 8 | Absicherung/Hedge | Fundamental andere Logik: keine Richtungswette, sondern Portfolio-Versicherung — "funktioniert", wenn sie in einem Abschwung Kapital schützt, kostet in ruhigen Phasen bewusst etwas | Aktivierung sollte sich an Bewertungs-/Spätzyklus-Signalen orientieren (bestehender Aktien-Bärenmarkt-/VIX-Indikator im System), nicht an einer klassischen Makro-These |

---

## 7. Objektive Prüf-Mechanismen pro Hauptgruppe (Grundlage für `these_abgleich`)

Nicht jede Hauptgruppe hat denselben zugrundeliegenden Mechanismus — der
`these_abgleich`-Fakt muss deshalb wissen, WELCHEN Check er für welche
Hauptgruppe anwenden soll:

| Hauptgruppe | Anwendbarer Prüf-Mechanismus | Datenquelle (bereits im Projekt) | Typischer Zeithorizont / `review_am`-Vorschlag |
|---|---|---|---|
| Edelmetalle | M2-/Liquiditätsregime (Fed-Funds-Richtung + M2-Trend) | `agent/krypto/regime.py::_liquidity_regime()`, bereits fertig | Lang (M2 monatlich) — Vorschlag: 3 Monate |
| Industriemetalle | CFTC-COT-Positionierung (Managed-Money-Netto) | `api/cftc_cot.py`, bereits fertig für Kupfer | Kurz-mittel (COT wöchentlich) — Vorschlag: 4 Wochen |
| Energie | CFTC-COT-Positionierung (Erdgas) + EIA-Lagerbestände | `api/cftc_cot.py` (nur Erdgas!), `api/eia.py` — Rohöl-Positionierung fehlt (siehe Abschnitt 8) | Kurz-mittel (COT/EIA wöchentlich) — Vorschlag: 4 Wochen |
| Anleihen & Geldmarkt | Zinsniveau/-richtung (Fed Funds, ggf. Zinskurve) | FRED über `api/macro.py`, Zinskurve (10J vs. kurz) noch NICHT als eigene Funktion vorhanden | Lang (Zinsentscheide selten) — Vorschlag: 3 Monate |
| Aktien-Sektoren/Finanzen | Zinskurven-Steilheit (10J minus kurzfristig) | NEU zu bauen (siehe Abschnitt 8) | Mittel-lang (braucht mehrere Monate Verlauf) — Vorschlag: 2-3 Monate |
| Aktien-Regionen/Emerging Markets | Dollar-Index-Trend + Fed-Richtung | NEU zu bauen (siehe Abschnitt 8) | Mittel-lang (Trend erst über Monate aussagekräftig — siehe DXY-Fund Abschnitt 6) — Vorschlag: 2-3 Monate |
| Technologie & KI, Aktien-Sektoren (übrige), Agrarrohstoffe, Sonstige | Kein etablierter automatischer Check — bleibt bei reiner Hervorhebung ohne `these_abgleich`-Text, oder rein qualitativ (Finnhub-Analysten-Trend als Annäherung) | — | Kein Vorschlag ableitbar — manuell setzen |
| Absicherung | Kein Makro-Check — orientiert sich am bestehenden Aktien-Bärenmarkt-/VIX-Indikator | `agent/krypto/regime.py` (Bärenmarkt-Overlay) | Situativ, kein festes Intervall — Aktivierung/Deaktivierung statt Review |

---

## 8. Detailprüfung: gefundene Lücken (auf Nutzer-Wunsch geprüft)

1. **CFTC-COT deckt kein Rohöl ab** — `COT_MARKET_NAMES` in `api/cftc_cot.py`
   hat aktuell nur Gold/Silber/Kupfer/Erdgas. Für eine sauber gestützte
   Energie-These (Punkt 1) fehlt die Positionierungs-Perspektive für
   WTI/Brent. Kleiner, klar umrissener Nachrüst-Punkt.
2. **Dollar-Index (DXY) und Zinskurve (10J vs. kurzfristig) sind NICHT als
   eigene, health-überwachte Datenquellen im Projekt vorhanden** — die
   Werte oben wurden ad-hoc direkt über yfinance abgefragt, nicht über eine
   projekteigene, mit `@track_api_health` abgesicherte Funktion. Für einen
   verlässlichen `these_abgleich`-Fakt (Punkte 6 und 7) müssten dafür zwei
   kleine neue Funktionen gebaut werden (Muster wie bestehende
   yfinance-Anbindungen).
3. **Absicherung passt nicht sauber ins Standard-Datenmodell** — das Feld
   `richtung` (Übergewichten/Neutral/Meiden) ergibt bei einer
   Versicherungs-Logik wenig Sinn. Vorschlag: eigene, einfachere
   GUI-Darstellung für diese Hauptgruppe (Aktiv/Inaktiv statt
   Übergewichten/Meiden) — noch zu entscheiden.
4. **Krypto ist komplett außen vor** — `kategorien.yaml` deckt bewusst
   keine Kryptowerte ab (siehe Datei-Kopfkommentar), das gilt automatisch
   auch für die gesamte Thesen-Verwaltung. Der `these_abgleich`-Fakt
   erscheint deshalb NUR bei Aktien-/Rohstoff-/ETF-/Hedge-/Themen-ETF-
   Signalen, nie bei Krypto-Signalen. Sollte in der GUI/Doku klar so
   kommuniziert werden, damit es nicht wie ein Bug wirkt ("warum sehe ich
   bei BTC keinen These-Abgleich").
5. **Kein automatisches Verhalten bei Ablauf von `review_am`** — aktuell nur
   ein Datumsfeld ohne definierte Folge. Offene Frage: soll beim
   Überschreiten automatisch eine Erinnerung erscheinen (GUI-Badge,
   E-Mail), oder bleibt das rein manuell (du schaust selbst nach)?
6. **Keine Verbindung zur Diversifikations-Tabelle (Portfolio-Tab)
   vorgesehen** — aktuell zeigt die Tabelle nur Ist-Gewichtung nach
   Hauptgruppe. Eine visuelle Markierung "hier ist eine aktive These"
   direkt in dieser Übersicht wäre naheliegend, ist aber noch nicht
   Teil des Konzepts.
7. **Synergie mit dem Screener bisher ungenutzt** — `scan_etf_candidates()`
   taggt Kandidaten schon heute automatisch mit Hauptgruppe/Unterkategorie
   (Release 1). Wenn eine These aktiv ist, aber KEIN Watchlist-Asset in
   dieser Kategorie existiert, könnte der Screener das besonders
   hervorheben ("passt zu deiner These, ist aber noch nicht in der
   Watchlist") — eine Form von Stufe-1-Hervorhebung mit echtem Nutzen,
   noch nicht eingeplant.

---

## 9. Verbleibende offene Punkte (aus der Lücken-Prüfung, Abschnitt 8)

1. Zinskurve (10J vs. kurzfristig) und Dollar-Index als eigene,
   health-überwachte Datenquellen nachrüsten? (klein, analog bestehender
   yfinance-Anbindungen)
2. CFTC-COT um Rohöl (WTI/Brent) erweitern? (klein, `COT_MARKET_NAMES`
   ergänzen)
3. Wie soll die GUI die Absicherung-Hauptgruppe abweichend vom
   Standard-Richtung-Feld darstellen (Aktiv/Inaktiv statt
   Übergewichten/Meiden)?
4. Verhalten bei Ablauf von `review_am`: automatische Erinnerung
   (GUI-Badge/E-Mail) oder rein manuell?
5. Soll die Diversifikations-Tabelle (Portfolio-Tab) aktive Thesen visuell
   markieren? Falls ja: mit sichtbarem Klartext-Label ("aktive These:
   Übergewichten"), nicht nur einer Farbe/einem Icon ohne Erklärung
   (Transparenz-Prinzip, siehe Abschnitt 5, Punkt 7).
6. Soll der Screener Kandidaten aus Kategorien mit aktiver, aber in der
   Watchlist noch nicht vertretener These besonders hervorheben? Gleiche
   Anforderung: klarer Text-Hinweis, keine stille Sortierung.

Diese sechs Punkte sind kleinere Ausbau-Entscheidungen, keine
Blocker für den Start der Umsetzung von #332 — können auch während der
Umsetzung nach und nach entschieden werden. Punkt 7 aus Abschnitt 5
(Transparenz-Prinzip) gilt dabei durchgängig für alle sechs.

## 10. Umsetzungsstatus (2026-07-20)

Backend (These-Datenmodell, `these_abgleich`-Engine) + GUI-Tab
„Schwerpunkte" (#342) + Stufe-1-Hervorhebung (#343) sind implementiert und
verifiziert (Details: `Basisinfos/Regelwerksmanual.md`, Nachtrag Folge 7).
Bezug auf die obigen sechs Punkte:

1. **Erledigt.** Zinskurve/Dollar-Index als `@track_api_health("yfinance")`
   in `api/macro.py` (`get_zinskurve()`/`get_dollar_index_trend()`).
2. **Erledigt.** `COT_MARKET_NAMES` um `rohoel_wti`/`rohoel_brent` ergänzt.
3. **Erledigt.** `ui/thesen_view.py`: Richtung-Feld zeigt bei
   `hauptgruppe=absicherung` automatisch Aktiv/Inaktiv.
4. **Weiterhin offen.** Kein automatisches Verhalten bei Ablauf von
   `review_am` — rein manuell im Schwerpunkte-Tab einsehbar.
5. **Erledigt.** Diversifikations-Tabelle markiert Hauptgruppen mit aktiver
   These (▲/▼/●-Marker + Zeilen-Tooltip mit Klartext-Begründung), ohne die
   bestehende Wert-Sortierung zu verändern.
6. **Erledigt.** Screener sortiert Kandidaten mit aktiver These nach vorn
   (▲/▼/●-Marker + Zeilen-Tooltip), Scan-Reihenfolge sonst unverändert.

Zusätzlich, über die sechs Punkte hinaus: die Watchlist-Tab-Sortierung
(Nutzer-Entscheidung „gehaltene Assets sollten Priorität erhalten",
Abschnitt 5) ist ebenfalls Teil von #343 — gehaltene Assets mit aktiver
These stehen vor neuen Kandidaten mit aktiver These, beide vor dem Rest,
jeweils nur bei der initialen Einsortierung, nicht bei manueller
Spaltensortierung.

Bewusst nicht Teil dieser Runde: #333 (KI-Vorschläge-Job) und #334 Stufe 2
(echte Scoring-Gewichtung) — siehe Abschnitt 5, Punkt 2.
