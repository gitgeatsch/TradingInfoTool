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

---

## 11. #333-Konzeption: Fortschritt und Status (laufende Diskussion, Stand 2026-07-24)

**Zweck dieses Abschnitts:** #333 wird in mehreren Gesprächsrunden Punkt für
Punkt konzipiert, bevor eine Zeile Code geschrieben wird (gleiche Methodik
wie bei #332). Damit kein Zwischenstand fälschlich als "fertig" gilt oder
übersehen wird, führt jeder entschiedene ODER noch offene Punkt hier einen
klaren Status. Nichts in diesem Abschnitt ist implementiert — das passiert
erst nach vollständigem Konzept, dann wandert es (wie bei #332) ins
`Regelwerksmanual.md`/`.docx` als Umsetzungsstand.

**Status-Legende:**
- **[ENTSCHIEDEN — NICHT GEBAUT]**: Design/Wert steht fest, aber noch keine
  Code-Zeile geschrieben.
- **[BAUSTEIN VORHANDEN, NICHT VERDRAHTET]**: die zugrunde liegende
  Funktion/Datenquelle existiert bereits im Code (für einen anderen Zweck),
  muss aber noch an die #333-Logik angeschlossen werden.
- **[GEBAUT]**: implementiert UND synthetisch verifiziert (nicht nur
  geschrieben) — Code lebt bereits in den Produktivdateien, aber noch nicht
  auf dem Notebook deployed/committed.
- **[OFFEN]**: noch keine Entscheidung getroffen, nächster
  Diskussionspunkt oder zurückgestellt.

| # | Punkt | Status | Detail |
|---|---|---|---|
| 1 | Grundsatz-Reihenfolge: #333 vor #334 Stufe 2 | [ENTSCHIEDEN — NICHT GEBAUT] | #334 Stufe 2 fehlt die Screener-Scoring-Infrastruktur (`agent/aktien/screener.py` sortiert nur nach Marktkapitalisierung) — eigenes, größeres Vorprojekt, zurückgestellt |
| 2 | Zweischichtiges Design (Schicht 1 deterministisch pro Kategorie, Schicht 2 EIN täglicher LLM-Synthese-Call über alle Kategorien) | Schicht 1 (Mehrfach-Mechanismus-Kombination) [GEBAUT], Schicht 2 (LLM-Synthese-Call) [ENTSCHIEDEN — NICHT GEBAUT] | `config.get_pruef_mechanismus()` liefert jetzt Listen, `agent/kategorie_thesen.py::_kombiniere_abgleiche()` kombiniert per Einigkeitsregel (alle verfügbaren Mechanismen müssen übereinstimmen, sonst neutral) — 8 synthetische Tests + 2 End-to-End-Tests bestanden. Schicht 2 (Prompt/Job) weiterhin offen |
| 3 | Fall A (keine aktive These → neuer `These`-Vorschlag, `quelle='ki_vorschlag'`) | [GEBAUT] | `agent/kategorie_vorschlaege.py::run_kategorie_vorschlaege_job()` — Sonde-These ermittelt Rohsignal, bei Persistenz automatische `These`-Anlage. Echter Lauf gegen alle 8 Kategorien: Edelmetalle/Industriemetalle/Anleihen/Finanzen/Aktien-Regionen → uebergewichten, Absicherung → inaktiv, Energie/Emerging-Markets korrekt neutral (widersprüchliche Signale) |
| 4 | Fall B (aktive These wird widersprochen → separate Änderungsaufforderung statt stiller Überschreibung) | [GEBAUT] | Gleiche Funktion, zweiter Zweig — bestehende These bleibt bis zum Nutzer-Klick unverändert, Tracker wird auf 'offen' gehoben. 3 synthetische Tests (Persistenz erreicht/Abbruch bei Signalwechsel/Cooldown nach Ablehnung) bestanden |
| 5 | Persistenz-Anforderung vor Fall B (analog Kontrathese-Zeitfenster) + Cooldown nach Ablehnung — konkrete Werte je Mechanismus-Typ | [ENTSCHIEDEN — NICHT GEBAUT] | Siehe Abschnitt 15 für die vollständige Tabelle je Mechanismus-Typ + Cooldown-Regel |
| 6 | Materialitätsschwelle COT-Positionierung: Dreizonen-Modell (<10% Rauschen / 10–25% Signal / >25% Signal+Rücksetzer-Hinweis) | [GEBAUT] | `_abgleich_cot_positionierung()` nutzt jetzt Netto-Position als % des kombinierten Open Interest statt roher Kontrakt-Summe — 3 synthetische Szenarien (Rauschen/moderat/gedrängt) bestanden |
| 7 | Materialitätsschwelle Zinskurve: Totzone ±0,25 Prozentpunkte | [GEBAUT] | `_abgleich_zinskurve()` erweitert — 3 synthetische Szenarien (normal/Totzone/invertiert) bestanden |
| 8 | Materialitätsschwelle VIX | [GEBAUT] | Korrigiert beim Bauen: nicht die ursprünglich vorgeschlagene neue <15/15–25/>25-Schwelle, sondern die bereits bestehende `agent/krypto/regime.py::VIX_BANDS` (20/"ruhig", 30/"erhöht", 40/"gestresst", "krise") wiederverwendet — "ruhig" = Risk-on, "gestresst"/"krise" = Risk-off (exakt dieselbe Schwelle wie der etablierte Boden-Zielzone-Trigger, Task #245), "erhöht" bewusst neutral |
| 9 | Materialitätsschwelle EIA-Erdgas-Lagerbestand: 5-Jahres-Saisonvergleich, ±5%-Schwelle | [ENTSCHIEDEN — NICHT GEBAUT] | Doch machbar (Korrektur einer zu vorschnellen früheren Einschätzung) — siehe Abschnitt 14 für Details + Kombinationsregel mit COT-Erdgas |
| 10 | Grundsatz-Korrektur: keine Kategorie wird strukturell ausgeschlossen (auch Technologie & KI, Sonstige) | [ENTSCHIEDEN — NICHT GEBAUT] | Ersetzt die frühere, zu pauschale Annahme "nur 6 Kategorien qualifizieren" |
| 11 | Sentiment-Mechanismus für Technologie & KI + übrige Aktien-Sektoren (Finnhub-Analystentrend + SEC-EDGAR-Insider + FINRA-Short-Interest) | [ENTSCHIEDEN — NICHT GEBAUT] | Manuell kuratierte Bellwether-Ticker pro Unterkategorie (kein automatisches Ableiten möglich, siehe Abschnitt 12 für die vollständige Tabelle + Aggregationsregel + Abgrenzung zu ähnlich klingenden Kategorien wie Grundstoffe/Industriemetalle) |
| 12 | Gold/Silber-COT-Zuordnung zu Edelmetalle | [GEBAUT] | `_COT_ROHSTOFF_FUER_KATEGORIE["edelmetalle"] = ["gold", "silber"]` + spezifische Unterkategorie-Overrides; kombiniert mit M2 über die neue Mehrfach-Mechanismus-Logik (Punkt 2) |
| 13 | Absicherung-Mechanismus (VIX + Aktien-Bärenmarkt) | [GEBAUT] | `_abgleich_baerenmarkt_overlay()` implementiert (ODER-Verknüpfung, VIX-Schwelle korrigiert auf die bereits bestehenden `VIX_BANDS`/"gestresst"+"krise" statt einer neu erfundenen Schwelle, siehe Punkt 8) — 6 synthetische Szenarien bestanden |
| 14 | Gleicher VIX/Bärenmarkt-Mechanismus für alle Aktien-Regionen (nicht nur Emerging Markets) | [GEBAUT] | Neuer Hauptgruppen-Eintrag `"aktien_regionen"` (Fallback für Global/Europa/Nordamerika/USA/Asien-Pazifik/Einzelländer), Emerging Markets kombiniert jetzt Dollar-Index + Bärenmarkt-Overlay. `_abgleich_baerenmarkt_overlay()` hat jetzt zwei Richtungs-Zweige (Absicherung-Sonderfall unverändert, normale Kategorien mit umgekehrter Polarität — Risk-off ist Gegenwind statt Auslöser). 5 synthetische Tests + 2 End-to-End-Tests bestanden, Absicherung-Regression bestätigt unverändert |
| 15 | `review_am`-Ablauf-Verhalten | [GEBAUT] | `ui/thesen_view.py::refresh()` markiert überfällige `review_am`-Daten mit ⚠-Präfix in der Spalte + erweitertem Tooltip "Wiedervorlage fällig seit TT.MM.JJJJ" — kein Änderungsvorschlag, keine E-Mail, reiner Kalender-Hinweis. Löst gleichzeitig den ursprünglich offenen Punkt 4 aus Abschnitt 10 |
| 16 | Job-Struktur (täglich 06:30, Muster `makro_analog_job`) | [GEBAUT] | `scheduler/background.py::kategorie_vorschlaege_job()` registriert (cron 06:30 + sofortiger Erststart, `misfire_grace_time` wie bei `makro_analog`) — noch NICHT auf dem Notebook deployed |
| 17 | Transparenz-Anforderung: jede #333-Wirkung (KI-Vorschlag, Änderungsaufforderung, Bellwether-/Mechanismus-Begründung) braucht Mouseover/Tooltip in GUI + Klartext in E-Mail | [GEBAUT] | Fall-B-GUI in `ui/thesen_view.py` fertig: neuer Bereich "Offene Änderungsaufforderungen" im Schwerpunkte-Tab (`vorschlag_tree` + `_render_vorschlaege()`), Zeilen-Tooltip zeigt Begründung+Datenstand, Buttons "Übernehmen"/"Ablehnen" mit erklärendem Tooltip. `_on_vorschlag_uebernehmen()` aktualisiert die verlinkte These direkt (`dataclasses.replace()`+`db.update_these()`) und schließt den Tracker als 'uebernommen', `_on_vorschlag_ablehnen()` lässt die These unverändert und löst die 30-Tage-Cooldown-Regel aus. Synthetischer Test (temp-DB, kompletter Übernehmen+Ablehnen-Flow inkl. Sichtbarkeits-Check über `get_offene_aenderungsvorschlaege()`) bestanden. Fall-A-Anzeige braucht keine eigene GUI (neue These landet automatisch in der bestehenden ThesenView). E-Mail-Anbindung (#333-Job selbst versendet noch keine Mail, nur GUI) bewusst zurückgestellt — Job ist rein deterministisch und läuft still im Hintergrund, erst eine Änderungsaufforderung im Status 'offen' braucht Nutzer-Aufmerksamkeit, die die GUI jetzt abdeckt |
| 18 | M2-Mechanismus-Nachbesserung: Net-Liquidity-Proxy (WALCL−TGA−RRP, wöchentlich) als primäres Tempo-Signal, M2-Liquiditätsregime als sekundäre Bestätigung | [GEBAUT] | FRED-Serien-IDs live verifiziert (WALCL 6.747 Mrd, WTREGEN 830 Mrd, RRPONTSYD 0,9 Mrd — plausibel). `agent/kategorie_thesen.py::_net_liquidity_trend()` neu, unabhängig von der Krypto-Regime-Pipeline (bewusst NICHT in `agent/krypto/regime.py` verdrahtet, siehe Docstring). Live-Test: Net Liquidity aktuell ~5.917 Mrd. USD, Trend "steigend" (26 abgeglichene Wochenwerte). Fallback auf reines M2 bei fehlendem `FRED_API_KEY`/Abruf-Fehler getestet. ECB-M3-Ergänzung nicht umgesetzt (optional, zurückgestellt) |
| 19 | Japan-M2 fehlt im Trend-Mehrheitsentscheid (nur aktueller Wert, keine Historie über `get_japan_m2()`) | **[OFFEN, vorgemerkt]** | Eigenständiges, kleineres Thema — bräuchte eine neue historische Japan-M2-Quelle, nicht Teil dieser #333-Runde |

**Konzeptphase abgeschlossen (2026-07-24):** alle 19 Punkte sind entweder
entschieden (16), bereits vorhandener Baustein (2, nur Verdrahtung offen)
oder bewusst vorgemerkt/kein Blocker (1, Punkt 19 Japan-Lücke). Umsetzung
beginnt jetzt — Fortschritt wird ab hier direkt an den einzelnen Punkten in
der Tabelle oben nachgeführt (Status wechselt auf `[GEBAUT]`/`[VERDRAHTET]`
sobald der jeweilige Code steht), bevor der Gesamtstand ins
`Regelwerksmanual.md`/`.docx` übertragen wird.

---

## 12. Bellwether-Ticker + Kategorie-Abgrenzung (Detail zu Punkt 11)

**Wichtige Einschränkung (ehrlich, P-10):** Bitpandas eigene Themenkorb-Symbole
(z. B. `SEMICON`, `ARTINT`, `CYBERSEC` — gleiche Produktkategorie wie
`COPPERMINE`) sind **Produktnamen, keine Börsenticker**
(`agent/aktien/screener.py:137-142`) — es gibt keinen yfinance-Ticker, über
den sich echte ETF-Top-Holdings automatisch ableiten ließen (das hätte
`api/asset_quality.py::get_asset_quality()` sonst geleistet). Die
Bellwether-Zuordnung ist deshalb eine **manuell kuratierte, statische
Tabelle** (gleiche Art Datenstruktur wie `kategorien.yaml` oder
`COT_MARKET_NAMES` selbst), kein automatisch abgeleiteter Mechanismus.

Nicht alle 18 Technologie-&-KI-Unterkategorien werden vorbereitet (bei
3-6 gleichzeitig aktiven Thesen insgesamt unnötig) — Start mit den
wahrscheinlichsten Kandidaten, Rest bei Bedarf später ergänzbar
(config-getrieben, kein Rewrite nötig).

| Kategorie | Scope/Definition | Abgrenzung zu ähnlich klingenden Kategorien | Bellwether |
|---|---|---|---|
| Halbleiter (Technologie & KI) | Chip-Designer/-Hersteller als Unternehmen | Nicht Seltene Erden/strategische Metalle (Industriemetalle — Rohstoff-Vorstufe) | NVDA, AMD (TSM bewusst nicht: Foreign Private Issuer, keine Section-16-Insider-Meldepflicht) |
| Künstliche Intelligenz (Technologie & KI) | Unternehmen mit KI als Kerngeschäft/-Strategie | Bewusst ohne NVDA (läuft unter Halbleiter) — kein Titel in zwei Körben | MSFT, PLTR |
| Cybersicherheit (Technologie & KI) | Reine Security-Software-Unternehmen | Abgegrenzt von allgemeiner Software/Tech | CRWD, PANW |
| Biotech (liegt unter Technologie & KI, NICHT unter Gesundheit!) | Forschungsgetriebene, oft kleinere/spekulativere Firmen, klinische Studien/Zulassungen als Treiber | Bewusst getrennt von "Gesundheit" — Innovationszyklus statt Konjunktur-Rotation | AMGN, VRTX (bewusst diversifiziert, keine Einzelwirkstoff-Biotechs — Klumpenrisiko einer einzelnen Zulassung) |
| Gesundheit (Aktien-Sektoren) | Breiter, defensiverer Sektor: Krankenversicherer, Pharma-Großkonzerne, Medizintechnik | Siehe Biotech-Abgrenzung oben | UNH, JNJ |
| Konsum (zyklisch) (Aktien-Sektoren) | Einzelhandel, Reisen, Automobile | Nicht Agrarrohstoffe (das sind die Rohwaren, nicht die verkaufenden Unternehmen) | AMZN, HD |
| Konsum (Basiskonsumgüter) (Aktien-Sektoren) | Lebensmittel-/Hygieneartikel-Hersteller | Gleiche Abgrenzung — Hersteller, keine Agrar-Rohstoff-Wette | PG, KO |
| Industrie (Aktien-Sektoren) | Maschinenbau, Luft-/Raumfahrt, Verteidigung, Transport, Baugewerbe | Nicht Industriemetalle (eigene Hauptgruppe, Kupfer/Aluminium als Rohstoff) — trotz ähnlichem Namen komplett andere Kategorie | HON, CAT |
| Kommunikationsdienste (Aktien-Sektoren) | Meta, Alphabet, Telekom-/Medienkonzerne | Überschneidet sich inhaltlich mit Technologie & KI (Big Tech) — bewusst offen benannt, kein verstecktes Doppelsignal | GOOGL, META |
| Grundstoffe (Aktien-Sektoren) | GICS-"Materials": Chemiekonzerne, Bergbau-/Minenunternehmen, Verpackung, Forst-/Papier — die **Unternehmen** | Nicht Industriemetalle (Rohstoff-Future/ETC, die reine Ware) und nicht Agrarrohstoffe (Getreide/Genussmittel als Ware) — Grundstoffe = die Firmen, die Rohstoffe verarbeiten/fördern | LIN, DOW |

**Kernregel gegen Verwechslung:** überall wo eine Hauptgruppe eine reine
Rohstoff-/Warenkategorie ist (Industriemetalle, Energie, Agrarrohstoffe,
Edelmetalle), geht es um die physische Ware/das Future. Überall wo es eine
Aktien-Sektoren- oder Technologie-&-KI-Unterkategorie ist, geht es um die
Unternehmen, die damit handeln/es herstellen/davon profitieren.

**Aggregationsregel (2 Bellwether-Titel × 3 Signaltypen):**
- Analystentrend (Finnhub): Durchschnitt Buy+StrongBuy-Anteil über den Korb,
  aktuell vs. Vormonat, Richtung nur bei Verschiebung > 5 Prozentpunkte
  gewertet.
- Insider-Aktivität (SEC EDGAR): **Anzahl** Käufer vs. Verkäufer im Korb
  (bewusst nicht Dollar-Volumen — ein einzelner Großverkauf würde sonst
  alles dominieren).
- Short-Interest-Trend (FINRA): Days-to-Cover-Richtung letzte vs. vorletzte
  Meldeperiode, gemittelt über den Korb.
- Kombinationsregel: mindestens 2 von 3 Signalen müssen in dieselbe Richtung
  zeigen, sonst "gemischt/neutral" — verhindert, dass ein einzelnes
  verrauschtes Signal (z. B. ein steuerlich bedingter Insider-Verkauf)
  allein die Kategorie-Einschätzung kippt.

---

## 13. Transparenz-Anforderung für #333 (Detail zu Punkt 17)

Jede automatische Wirkung von #333 — neuer KI-Vorschlag, Änderungsaufforderung
gegen eine bestehende These, Bellwether-/Mechanismus-Begründung — muss ihre
konkrete Grundlage sichtbar mitliefern, exakt nach dem bereits etablierten
Transparenz-Prinzip (Abschnitt 5, Punkt 7). Kein Badge/keine Umsortierung
ohne erkennbaren Grund.

Wiederverwendung bestehender, bereits bewährter Bausteine statt Neubau:
- **GUI (Schwerpunkte-Tab/`ui/thesen_view.py`):** Mouseover-Tooltip mit den
  konkreten Rohwerten (z. B. "COT Kupfer: Managed-Money netto long 29,8% des
  Open Interest, Bericht vom TT.MM.JJJJ") — gleicher Baustein wie
  `ui/widget_tooltip.py`/`ui/row_tooltip.py`, bereits an mehreren Stellen im
  Projekt im Einsatz (Diversifikations-Tabelle, Screener-Marker).
- **Signal-Detail-Panels (`ui/signals_view.py`/`ui/hebel_view.py`):** der
  `these_abgleich`-Text erscheint dort bereits heute (Fakt im Prompt) — bei
  einer Bellwether-basierten Kategorie zusätzlich die konkreten Bellwether-
  Ticker + deren Einzelwerte in der Begründung nennen, nicht nur das
  Aggregat-Urteil.
- **E-Mail:** gleiches 3-Abschnitte-Template (`scheduler/background.py`) wie
  bei Risikofaktoren/Kontrathese — Klartext statt Badge, da E-Mail kein
  Mouseover kennt.

---

## 14. EIA-Erdgas-Materialitätsschwelle (Detail zu Punkt 9)

**Korrektur einer zu vorschnellen früheren Einschätzung:** ursprünglich als
"nicht datentechnisch möglich" eingestuft, weil `get_natural_gas_storage_
history()` bisher nur mit `n_weeks=8` genutzt wurde. Bei genauerem Hinsehen
unterstützt die Funktion bereits einen beliebigen `n_weeks`-Parameter (reine
API-`length`-Angabe) — ein Aufruf mit `n_weeks=260` (5 Jahre) liefert
dieselben Daten, nur mehr davon. Die EIA-Wochenreihe existiert durchgängig
seit den 1990ern, 5 Jahre Historie sind real verfügbar. Kein neuer
Datenzugriff nötig, nur ein größerer Parameterwert + eine neue
Aggregationsfunktion.

**Berechnung:** aus den 260 Wochenwerten für die aktuelle Kalenderwoche
(± wenige Tage Toleranz wegen Schaltjahren) den Durchschnitt der letzten 5
Jahre bilden, dann `(aktueller_wert - 5j_durchschnitt) / 5j_durchschnitt`
berechnen. Kalenderwochen-Zuordnung über Datum ± Toleranz, nicht über einen
starren Wochenindex (sonst Drift durch Schaltjahre).

**Materialitätsschwelle: ±5%** vom 5-Jahres-Durchschnitt — Abweichungen
darunter gelten als "im saisonalen Rahmen", darüber als auffällig (gängige
Einordnung in der Energie-Berichterstattung, gleiche Größenordnungs-Logik
wie die anderen Schwellen in diesem Abschnitt).

**Richtungslogik:** Lagerbestand über dem 5-Jahres-Schnitt = reichliches
Angebot = bearish für Erdgaspreis (gegen "Energie übergewichten"). Unter dem
Schnitt = knapperer Markt = bullish.

**Kombination mit COT-Erdgas (Energie hat damit 2 Indikatoren):** beide
müssen übereinstimmen für eine gewertete Richtung, sonst "gemischt/neutral"
— kodifiziert die bereits im Konzeptdokument (Abschnitt 6, Beispiel 1)
korrekt, aber nur verbal getroffene Einordnung ("Speicher baut saisonal
weiter auf, ABER Managed-Money ist netto SHORT — gemischtes Bild") als feste
Regel, dieselbe 2-von-2-Logik wie beim Bellwether-Modell (Abschnitt 12), nur
mit 2 statt 3 Signalen.

---

## 15. Persistenz-Anforderung, Cooldown + M2-Mechanismus-Nachbesserung (Detail zu Punkt 5 + 18)

### Persistenz-Anforderung vor einer Änderungsaufforderung (Fall B)

Nicht ein einheitlicher Wert — an die `review_am`-Buckets aus Abschnitt 7
angelehnt, je nach natürlichem Datentakt des Mechanismus. Grund: ein zu
kurzes Fenster bei wöchentlichen Daten würde nur denselben Bericht mehrfach
zählen, keine echte unabhängige Bestätigung (gleiches Prinzip wie die
Mindestbeobachtung im Backward-Tracking).

| Mechanismus-Typ | Natürlicher Datentakt | Persistenz-Anforderung | Warum |
|---|---|---|---|
| COT-Positionierung (Kupfer/Erdgas/Rohöl, künftig Gold/Silber) | wöchentlich | 14 Tage (≥2 Berichtszyklen) | Ein einzelner Bericht darf nicht reichen |
| EIA-Erdgas-Saisonvergleich | wöchentlich | 14 Tage | Gleiche Begründung |
| Bellwether-Sentiment (Finnhub/SEC-EDGAR/FINRA) | gemischt, FINRA bindend (2×/Monat) | 14 Tage | Am langsamsten Baustein orientiert |
| **Liquiditätsregime — Net-Liquidity-Anteil** (neu, siehe unten) | wöchentlich | 14 Tage | Jetzt gleiche schnelle Schiene wie COT/EIA statt 60 Tage |
| Liquiditätsregime — Global-M2-Anteil (Kontext, nicht mehr alleiniger Gate) | monatlich | (keine eigene Gate-Funktion mehr, nur Begründungstext) | Bleibt als langsamere Bestätigung sichtbar, blockiert aber nichts mehr allein |
| Zinskurve, Dollar-Index | bereits mehrmonatiger Trend | 30 Tage zusätzlich | Trendlogik glättet schon selbst |
| VIX/Bärenmarkt (Absicherung) | ereignisgetrieben, Versicherungslogik | 7 Tage | Portfolio-Schutz soll schneller reagieren können |

**Cooldown nach Ablehnung:** einheitlich 30 Tage ODER bis das Signal
zwischenzeitlich wieder zur bestehenden These zurückgedreht UND erneut
dagegen gelaufen ist (je nachdem was zuerst eintritt) — verhindert sowohl
sofortiges Nerven direkt nach dem Ablehnen als auch endloses Ignorieren
eines sich tatsächlich verfestigenden Trends.

**Technische Konsequenz:** COT/EIA/etc. speichern keine eigene Historie
(reine Momentaufnahmen) — der #333-Job muss deshalb selbst kleinen Zustand
mitführen ("seit wann läuft die aktuelle Widerspruchs-Serie für diese
These"), z. B. als `beobachtung`-Zwischenstatus auf dem
`these_aenderungsvorschlaege`-Eintrag, der erst nach Ablauf der
Persistenzfrist auf `offen` (für den Nutzer sichtbar) hochgestuft wird.
Bricht die Widerspruchs-Serie vorzeitig ab, wird der Entwurf verworfen
(Reset) — gleiches Prinzip wie bei der Kontrathese-Zeitfenster-Bestätigung.

### M2-Mechanismus-Nachbesserung (Punkt 18)

**Ausgangsproblem:** M2 wird von der Fed nur noch monatlich veröffentlicht
(die frühere wöchentliche Reihe wurde eingestellt) — eine echte
Datengrenze, keine Implementierungsschwäche. Eine 60-Tage-Persistenz allein
auf M2-Basis wäre für die einzigen beiden darauf angewiesenen Kategorien
(Edelmetalle, Anleihen & Geldmarkt) zu träge.

**Bereits vorhandene Basis (Prüfung ergab: mehr als zunächst angenommen):**
`agent/krypto/regime.py::_m2_global_trend()` ist bereits ein
**Mehrheitsentscheid über USA (FRED) + Eurozone (EZB) + China
(Eastmoney)**, kein reiner US-Wert. Reale Lücke: Japan fließt nur mit dem
aktuellen Wert ein, nicht in den Trend (keine historische Quelle über
`get_japan_m2()` — HTML-Scraping-Fallback liefert nur eine Momentaufnahme).
Bewusst als eigenständiges, kleineres Thema zurückgestellt (Punkt 19), nicht
Teil dieser #333-Runde.

**Neue Komponente — Net Liquidity** (wöchentlich, löst das Tempo-Problem):
`Netto-Liquidität = Fed-Bilanzsumme (WALCL) − Treasury General Account
(WTREGEN) − Reverse-Repo-Nutzung (RRPONTSYD)`, alle drei Serien über
denselben FRED-Zugang wie die bereits vorhandenen `FRED_SERIES`-Einträge
(`api/macro.py`) beziehbar — keine neue API-Anbindungsart nötig, nur neue
Serien-IDs. **Wichtig:** Serien-IDs stammen aus Fachwissen, nicht live
verifiziert — vor Umsetzung genauso zu prüfen wie seinerzeit
`ism_ersatz_philly_fed`.

**Neue Aufteilung:** Net-Liquidity wird das **primäre, persistenz-gatende
Signal** (14-Tage-Bucket, wie COT/EIA). Der bestehende
Global-M2-Mehrheitsentscheid (ggf. um ECB-M3 ergänzt — einzige Region, die
M3 tatsächlich noch als Referenzgröße veröffentlicht; USA hat M3 2006
eingestellt, China hat kein vergleichbares Aggregat) bleibt als
**sekundäre, langsamere Bestätigung** im Begründungstext sichtbar, ist aber
nicht mehr alleiniger Blocker. Betroffen: Edelmetalle, Anleihen & Geldmarkt
(die einzigen beiden Kategorien, die aktuell nur auf `m2_liquiditaet`
sitzen).

**Nächster offener Diskussionspunkt:** #11 (Bellwether-Ticker-Auswahl für
Technologie & KI + übrige Aktien-Sektoren) oder #9 (EIA-Materialität) —
beide noch unentschieden.
