# Fakten-Entscheidungsmappe — Krypto-Spot- und Hebel-Pipeline

**Zweck:** Dauerhaftes Referenzdokument, kein einmaliger Audit-Schnappschuss. Jeder
Fakt, der künftig neu an ein LLM (Mistral-Kette oder Z.ai) übergeben wird, sollte vor
der Aufnahme gegen das Raster in Abschnitt 1 geprüft werden — so bleibt die Frage
"determinieren wir das, oder überlassen wir es dem LLM-Urteil, und mit welchem
Kontext?" ein bewusster Entscheidungspunkt statt eines Zufallsprodukts.

Stand der Bestandsaufnahme: 2026-07-28, Codebase-Audit aller Fakten in
`agent/krypto/pipeline.py::build_facts()` und `agent/krypto/hebel_pipeline.py::
build_hebel_facts()`, abgeglichen gegen `agent/krypto/analyst.py::SYSTEM_PROMPT`,
`agent/krypto/hebel_analyst.py::SYSTEM_PROMPT`, `agent/krypto/risk_gate.py` und
`agent/krypto/hebel_risk_gate.py`. Bei strukturellen Änderungen an diesen Dateien
sollte diese Mappe aktualisiert werden (Datum oben anpassen).

---

## 1. Das Entscheidungs-Raster

Für jeden Fakt vier Fragen, in dieser Reihenfolge:

**Frage 1 — Ist die "richtige" Reaktion unabhängig vom Kontext immer dieselbe?**
Wenn ja: gehört in den Risk-Gate (`risk_gate.py`/`hebel_risk_gate.py`), deterministisch,
nie dem LLM überlassen. Ein Limit, das diskutierbar ist, ist kein Limit. Beispiele, die
das bereits richtig machen: CRV-Minimum, Cash-Reserve-Pflicht, Konfidenz-Regime-
Schwelle, Bitpanda-Listing-Veto.

**Frage 2 — Braucht die Bewertung echtes, kontextabhängiges Abwägen mehrerer
Faktoren gleichzeitig?**
Wenn ja: gehört dem LLM — aber mit **Kontext**, nicht mit vorgegebener Schlussfolgerung.
Der Unterschied, der zählt: *Antwort vorgeben* ("FOMC < 14 Tage → das ist ein Risiko")
ist falsch, weil es die LLM-Urteilsarbeit durch Schein-Determinismus ersetzt, ohne
echten Durchgriff zu haben (nur Text in `key_risks`, keine Konsequenz). *Kontext liefern,
Urteil offenlassen* ("historisch überdurchschnittliche realisierte Volatilität im
24-48h-Fenster um FOMC, oft nach einer ruhigen Phase davor — bewerte selbst, ob das
hier relevant ist") ist richtig, weil es eine dokumentierte Marktbasis liefert, ohne die
Schlussfolgerung zu determinieren.

**Frage 3 — Bekommt das LLM aktuell überhaupt eine kalibrierende Einordnung, oder
nur den nackten Wert?**
Das ist die eigentliche Lücke, die in dieser Mappe gesucht wird. Nackte Werte ohne
Kontext (Kategorie (d) unten) führen zu unreproduzierbarem, im schlimmsten Fall
zufälligem Umgang durch das LLM.

**Frage 4 (neu, 2026-07-28) — Passt Gewichtung/Regel zum tatsächlichen
Zeithorizont dieser Pipeline?**
Hintergrund (Nutzer-Vorgabe): Hebel und Spot verfolgen bewusst unterschiedliche
Zeithorizonte. **Hebel = kurzfristige, taktische Positionen** (Nutzer hält historisch
im Schnitt ~1 Tag; Trigger-Screening alle 15 Minuten; Funding-Kosten pro Stunde
relevant). **Spot = langfristige Investitionsthese / Zyklus-Positionierung**, sinngemäß
ein "Bitcoin-Sparplan"-Ansatz: antizyklisch kaufen im Bärenmarkt (AZ-4: Boden-
Zielzonen, Cash-Reserve-Aufbau fürs Nachkaufen, Tranchen-Logik), tendenziell erst im
Bullenmarkt/bei Zyklus-Extremen wieder abbauen. Ein Fakt kann in der einen Pipeline
hochrelevant, in der anderen nachrangig sein — dieselbe schwache Behandlung ist
deshalb nicht in beiden Fällen gleich falsch. Ein akuter Kurzfrist-Fakt (z.B. FOMC-
Nähe, Funding-Rate) OHNE Kontext ist bei Hebel der dringlichere Fehler; ein
Langfrist-Fakt (Zyklusrisiko, Makro-Analogie) OHNE Kontext ist bei Spot der
dringlichere Fehler.

---

## 2. Kurzfassung der Zahlen (von 156 katalogisierten Fakt-Knoten, ca. 148 eigenständige Datenpunkte)

| Kategorie | Beschreibung | Anzahl (ca.) |
|---|---|---|
| (a) | Explizite Prompt-Regel **und** deterministische Gate-Nutzung | 30 |
| (b) | Nur Prompt-Regel, **kein** Gate | 34 |
| (c) | Nur Gate, **keine** Prompt-Regel (meist bewusst — reine Risk-Gate-Größen, dem LLM zu Recht nicht gezeigt) | 9 (+ 6 gate-interne Größen, die nie im Fakten-JSON stehen) |
| (d) | **Weder** Prompt-Regel **noch** Gate — komplett unkommentiert durchgereicht | 28 |

Kategorie (d) ist der eigentliche Handlungsraum dieser Mappe. Kategorie (b) enthält
einige Fälle, die näher am "Antwort vorgeben statt Kontext liefern"-Problem liegen als
am sauberen Zielzustand (siehe Abschnitt 3.2).

---

## 3. Prioritäre Befunde — brauchen eine Entscheidung

### 3.1 Zeithorizont-Fehlpassung (Frage 4) — neue, wichtigste Erkenntnis dieser Runde

| Fakt | Aktueller Zustand | Zeithorizont-Bewertung |
|---|---|---|
| `naechste_fomc_sitzungen` / `naechste_cpi_veroeffentlichung` | Spot: schwache 14-/5-Tage-Schwellenregel (Regel 13). **Hebel: gar keine Regel**, obwohl dieselben Fakten geliefert werden. | **Falsch herum priorisiert.** Für kurzfristige, gehebelte Positionen ist Event-Timing akut relevant — hier fehlt es komplett. Für Spots langfristige These ist es nachrangig — die schwache Regel dort ist eher proportional richtig. **Empfehlung: Hebel zuerst mit echtem Kontext (Frage 2) ausstatten, Spot ggf. unverändert lassen oder nur leicht verbessern.** |
| `regime.zyklus_risiko` + `.zyklus_risiko_begruendung` | Nur bei Spot vorhanden und mit Regel 11 versehen; bei Hebel wird der Fakt zwar mitgeliefert, aber **keine Regel** dazu. | **Passt zur Zeithorizont-Logik** — Zyklusrisiko ist ein Langfrist-Konzept, für Hebel folgerichtig nicht ausgearbeitet. Kein Handlungsbedarf, aber zur Klarheit hier vermerkt. |
| `historischer_makro_vergleich` (SPX/BTC-Forward-6m/12m-Analogien) | In beiden Pipelines identisch mit Regel 24/15 versehen (inkl. Vorsicht-Caveat). | Für Spot goldrichtig (Langfrist-These). Für Hebel (typische Haltedauer ~1 Tag) ist ein 6-12-Monats-Forward-Wert **strukturell fast irrelevant** — die Regel warnt zwar vor Übernutzung, aber die Frage ist, ob der Fakt überhaupt in den Hebel-Prompt gehört. **Kandidat für Entfernung aus dem Hebel-Fakten-JSON** (spart auch Token). |
| `optionsmarkt.dvol_prozent`/`.skew_prozentpunkte` (30-Tage-Sicht, Deribit) | Nur Hebel, mit Regel 21 (Cross-Check-Idee). | 30 Tage ist für Hebels ~1-Tage-Horizont bereits recht lang, aber als *marktweites* Sentiment-Signal (nicht coin-spezifisch) plausibel als Kontext-Fakt vertretbar. Kein akuter Handlungsbedarf. |

### 3.2 Echte Lücken (Kategorie (d)) mit hoher Priorität

- **`regime.fear_greed.wert` / `.einstufung`** — wird abgerufen, gespeichert, in JEDEM Signal mitgeschickt, aber in **keinem** der beiden Prompts erwähnt und in **keinem** Gate ausgewertet. Reiner Ballast (Tokenkosten ohne Nutzen) oder vergessene Anbindung. Entscheidung nötig: anbinden (mit Kontext) oder aus dem Fakten-JSON entfernen.
- **`regime_profil.gewicht_technik/_fundamental/_momentum/_kontext_makro`** (+ `gewinnabsicherung_verschaerft`) — vier Gewichtungszahlen ohne jede Anweisung, ohne jede Code-Auswertung. Entweder erklären, wie das LLM sie nutzen soll, oder entfernen.
- **`strategien_aktiv[]`** — Liste ohne jede Anweisung.
- **`markt_kontext.naechste_fomc_sitzungen`/`naechste_cpi_veroeffentlichung`/`praesidentschaftszyklus` im Hebel-Prompt** — siehe 3.1, höchste Priorität.
- **`antizyklisch.moeglicher_flush` bei Hebel** — bei Spot gibt es Regel 12 dafür ("möglicherweise", "Hinweis auf" — vorsichtige Formulierung verlangt), bei Hebel fehlt die Regel komplett, obwohl der Fakt geliefert wird.

### 3.3 Strukturelle Asymmetrien Spot ↔ Hebel (Konsistenz-Fragen, keine reinen Lücken)

1. **Retail-Konsens-Filter:** Hebel filtert `top_gruende` deterministisch per Regex
   (`filtere_retail_konsens_top_gruende()`), Spot verlässt sich allein auf die Prompt-
   Regel 15 (die dort sogar ausführlicher ist als bei Hebel). Spot hat denselben Schutz
   nicht, obwohl der frühere Retail-Konsens-Fund (siehe
   [[project_btc_hebel_review_antizyklisch_liquiditaetszonen_funding_fix]]) genau
   dieses Muster war.
2. **Retail-Konsens-Deckel:** Hebel deckelt den Hebel-Faktor bei extremem Konsens,
   Spot deckelt die Positionsgröße dafür **nicht** — nur Risikofaktor-Anzeige ohne
   Konsequenz.
3. **BTC-Matrix:** Spot hat nur die Prompt-Regel 8, keinen Gate-Faktor; Hebel hat
   Regel 16 **und** einen echten Risikofaktor ("Alt-Coin-Marktphase").
4. **Historische Erfolgsquote / BTC-Relativwert:** Prompt-Regel in beiden Pipelines
   identisch, aber die deterministische Gate-Absicherung existiert **nur bei Hebel**.
5. **Spot hat 29 Prompt-Regeln für ~127 Fakt-Knoten, Hebel nur 22 Regeln für ~105** —
   der Hebel-Prompt lässt `markt_kontext`, `moeglicher_flush`, `zyklus_risiko` und
   `disclaimers` komplett unkommentiert, obwohl die Fakten geliefert werden.
6. **ATR-relativ-Richtwert (NEU 2026-07-28):** Hebel bekam `atr.relativ_prozent` +
   einen 1,5×-Richtwert in Regel 6 (siehe 4.2, `.atr.relativ_prozent`). Spot hat
   dieselbe strukturelle Lücke (ATR nur absolut, keine SL-Distanz-Volatilitäts-
   Bindung in Regel 16), wurde aber nicht angefasst — Auslöser war ein Hebel-
   spezifischer Backtest, die Frage ob Spot dieselbe Nachbesserung braucht wurde
   mit dem Nutzer noch nicht besprochen. **Offen.**

---

## 4. Vollständiger Fakten-Katalog

*(Rohdaten aus dem Codebase-Audit vom 2026-07-28. Referenz für Detailfragen — bei
Unklarheiten über einen einzelnen Fakt hier nachschlagen, bevor eine Prompt-Änderung
vorgenommen wird.)*

### 4.1 Legende

- **Prompt-Regel**: wörtliches oder sehr nahes Zitat aus dem jeweiligen SYSTEM_PROMPT, mit Regelnummer.
- **Gate**: Fundstelle in `risk_gate.py`/`hebel_risk_gate.py` (Datei:Zeile), falls der Fakt dort deterministisch ausgewertet wird.

### 4.2 Spot-Pipeline (`build_facts()`)

**`asset.*`**
- `asset.symbol` — keine Regel; Gate: `pipeline.py:692-705` steuert `tranchen_erlaubt`/`cash_reserve_ziel`/`btc_relativwert`-Ausschluss über Symbolvergleich.
- `asset.name` — keine Regel, kein Gate.
- `asset.rolle` (core/taktisch) — **Regel 7/8**: core/Wiedereinstiegs-Kandidaten → zwei getrennte Bewertungsebenen (technisch + fundamentale These); sonst `regime.btc_matrix`-Skepsis. Gate: `risk_gate.py:304-308` (RM-2 Kern- vs. Asset-Limit), `:330-335` (Small-Cap-Veto-Vorbedingung).
- `asset.wird_aktuell_gehalten` — Regel 7 (Teil der Wiedereinstiegs-Bedingung); kein direktes Gate.
- `asset.beobachtungsstatus` — Regel 7/8; kein Gate.
- `asset.bitpanda_gelistet` — **Regel 2**: `false` ist typischster Veto-Grund, explizit benennen. Gate: `risk_gate.py:290-299`, hartes Veto (`kauf_erlaubt=False`); `None` löst bewusst kein Veto aus.

**`preis.*`**
- `preis.usd`/`preis.eur` — **Regel 4**: Zonen-Ableitung auf USD und EUR gleichermaßen. Gate: `risk_gate.py:209-216` (Stop-Loss-Distanz-Basis), `:354-357` (EUR-Positionsobergrenze); EUR-Werte seit 2026-07-27 deterministisch über `eur_aus_usd()` ersetzt.
- `preis.aktualisiert_vor_min` — keine Regel; äquivalentes Kriterium `is_price_stale()` läuft als eigenes Vor-LLM-Gate.

**`haltung.*`** (Spot-only)
- `haltung.menge`/`.wert_usd` — keine Regel, kein Gate.
- `haltung.einstandspreis_eur`/`.einstandspreis_quelle`/`.menge_ohne_bekannten_einstandspreis`/`.gewinn_verlust_pct` — **Regel 19**: niedrig gewichteter Kontext, KEIN Ersatz für Stop-Loss-/CRV-Pflicht; bei "unbekannt"-Quelle Unsicherheit erwähnen. Kein Gate.

**`vorherige_empfehlung`** (Spot-only) — **Regel 21**: nicht umgesetzte Verkaufs-/Tauschempfehlung explizit ansprechen, nicht unverändert wiederholen. Kein Gate (rein Prompt-seitig, Erzeugung selbst deterministisch).

**`historische_erfolgsquote.*`** (beide Pipelines) — **Regel 23 (Spot) / 14 (Hebel)**: schwaches Zusatzindiz für Konfidenz-Kalibrierung, ersetzt nicht die eigenständige Analyse; Stichprobengröße beachten. Gate: **nur Hebel** — `hebel_risk_gate.py:518-536` (Schwelle n≥15, Trefferquote-Schwellen 30/60).

**`historischer_makro_vergleich.*`** (beide) — **Regel 24 (Spot) / 15 (Hebel)**: Analog-Monate, `btc_forward_*`-Werte NIEMALS als belastbare Statistik. Kein Gate in beiden. Siehe 3.1 zur Zeithorizont-Frage bei Hebel.

**`liquiditaetszonen.*`** (beide) — **Regel 25 (Spot) / 17 (Hebel)**: Marketmaker-Konzept, rein informativ. `.in_naehe_ungefegter_zone` → Gate: `risk_gate.py:699-710`/`hebel_risk_gate.py:587-598`, aber **immer neutral bewertet**, kein Deckel. `.kursverlauf[]` (90 Punkte) ist reine Chart-Nutzlast im Prompt ohne Regel.

**`signal_stabilitaet.*`** (beide) — **Regel 26 (Spot) / 18 (Hebel)**: reine Transparenz, explizit KEIN Eingabewert für die eigene Konfidenz (sonst zirkulär). `.stabil`/`.einordnung` → Gate: `risk_gate.py:717-721`/`hebel_risk_gate.py:604-608`, echter Risikofaktor, aber kein Deckel. Übrige Unterschlüssel (`.verlauf[]` etc.) ohne Regel/Gate.

**`btc_relativwert.*`** (beide, `null` bei BTC) — **Regel 28 (Spot) / 20 (Hebel)**: Korrelation/Beta/Relativstärke, mehrmonatiger Hintergrund, NIEMALS Grundlage für kurzfristige Entscheidung. Gate: **nur Hebel** — `hebel_risk_gate.py:331-335`, mildert Regime-Konflikt-Text bei niedriger Korrelation/hoher Relativstärke ab (nur textuell).

**`technische_analyse.*`** (identisch in beiden)
- `.ema`/`.macd`/`.rsi_14`/`.bollinger` — indirekt über `.confluence`; MACD/RSI/Bollinger zusätzlich als hartes Verfügbarkeits-Gate vor jedem LLM-Call (`MIN_GATE_INDICATORS_AVAILABLE`).
- `.atr.wert` — **Regel 16 (Spot) / 6 (Hebel)**: Zonen-Ableitung aus echten Referenzpunkten. Gate: zentral — Stop-Loss-Distanz, RM-5-Veto bei Fehlen, RM-1-Obergrenze, Hebel: `max_safe_hebel()`.
- `.atr.relativ_prozent` (NEU 2026-07-28, **nur Hebel**) — ATR ÷ Kurs × 100, damit das LLM die Umrechnung nicht selbst vornehmen muss. Auslöser: Backtest von 61 aufgelösten Hebel-Trades zeigte SL-Abstand <5% mit 0-16,7% Win-Rate vs. 31,2% bei 5-10% (siehe [[project_enge_stop_loss_backtest_und_massnahmen]]). Frage 1 (Gate/deterministisch?) explizit verneint — Nutzer schloss einen harten Veto aus ("keine Signale unnötig wegschmeissen"); stattdessen Frage 2 (LLM-Urteil mit Kontext): Regel 6 um einen Richtwert erweitert (SL-Abstand i.d.R. ≥ 1,5× `atr.relativ_prozent`, mit Backtest-Zahlen als Begründung im Prompt, explizite Abweichungs-Erlaubnis bei Support/Widerstand/Fibonacci). **Kategorie (b)** — Prompt-Regel, kein Gate. Bei Spot fehlt dieses Feld bisher komplett (siehe 3.3, neuer Punkt 6) — nicht mit dem Nutzer abgestimmt, ob das nachgezogen werden soll.
- `.atr.perzentil` — **Regel 27 (Spot) / 19 (Hebel)**: reiner Risiko-/Positionsgrößen-Kontext, keine Richtungsaussage. Gate: negativ ab Schwelle, sonst neutral, nie positiv, kein Deckel.
- `.support_resistance`/`.fibonacci` — **Regel 9**: explizit relativ zum aktuellen Kurs einordnen, sonst würden diese Level "systematisch ignoriert". Kein Gate.
- `.confluence.gesamttendenz` — **Regel 22 (Spot) / 13 (Hebel)**: Pflicht-Prüfpunkt fürs Gegenargument bei "gemischt". Gate: doppelt — Positionsgrößen-/Hebel-Deckel bei "gemischt", plus Risikofaktor bullish/bearish gegen die gewählte Richtung.

**`regime.*`** (Spot hat mehr Felder als Hebel, siehe 4.3)
- `regime.wert` — Hebel **Regel 3**: `krise_extrem` → IMMER HALTEN. Gate: massiv — Small-Cap-Budget, Mindestkonfidenz-Veto, Positionsgrößen-Skalierung (Spot); Hebel-Totalveto bei `krise_extrem`, Hebel-Deckel, Risikofaktor (Hebel).
- `regime.fear_greed.wert`/`.einstufung` — ~~keine Regel in beiden Prompts~~ — **seit 2026-08-06 in Regel 37 (Spot) / 33 (Hebel) geregelt**, zusammen mit `btc_zu_ema50`. Weiterhin keine Gate-Nutzung.
- **`regime.btc_zu_ema50.abstand_prozent`/`.einordnung`** (NEU 2026-08-06, beide Krypto-Pipelines) — **Regel 37 (Spot) / 33 (Hebel)**. Schließt eine Lücke, die eine Nutzer-Beobachtung aufdeckte („BTC drei Tage gestiegen, keine Änderung in den Signalen" — nachgemessen +1,78 %). Unsichtbar war das, weil `btc_trend` eine **EMA-Ordnung** ist (ändert sich erst beim Kippen der Reihenfolge) und `regime.wert` aus einer **ODER-Bedingung** stammt, in der Fear & Greed allein „bär" erzwingt. **Kategorie (b)** — Kontext, kein Gate.
  - **Zwei Formen mit Absicht:** Prozentwert *und* kategoriale Einordnung. Extern belegt sind Modelle beim Schließen über stetige Größen schwach; kategoriale Labels tragen zuverlässiger. Dasselbe Muster wie CRV-Bänder (statt roher Kurve) und Kostentabelle (statt Formel).
  - **Kein Band heißt „unklar" oder „Übergang".** Ein Mehrdeutigkeits-Label wäre strukturell eine „Unknown"-Option — die löst laut Literatur Abstention aus, und genau dieser Mechanismus drückte hier die ERÖFFNEN-Quote von 93 % auf 3 %. Die Regel benennt die Divergenz **bejahend** („frühe Erholung") und sagt ausdrücklich, dass sie **kein Grund für pauschale Vorsicht** ist.
  - Nur Krypto-Spot und Hebel — Aktien/Rohstoffe/Themen-ETF haben einen anderen Regime-Block ohne BTC-Bezug, dort wäre der Fakt sinnlos.
- `regime.btc_matrix`/`.btc_matrix_hinweis` — **Regel 8 (Spot) / 16 (Hebel)**. Gate: **nur Hebel** — Risikofaktor "Alt-Coin-Marktphase".
- `regime.liquiditaets_regime`(_begruendung) — **Regel 10 (Spot)**, niedrig gewichteter Kontext, bei "unbekannt" nicht erwähnen. Kein Gate. Bei Hebel kein eigenes Feld.
- `regime.zyklus_risiko`(_begruendung) — **Regel 11 (Spot)**: BTC-weite Zyklus-Einordnung, relevant für alle Assets. Kein Gate. Bei Hebel geliefert, aber ohne Regel (siehe 3.1).
- `regime.boden_zielzone_btc/eth.*` — keine positive Regel; nur negativ über den Halluzinations-Check (`_pruefe_kreuzkontamination()`) — Erwähnung bei Nicht-BTC/ETH-Symbolen wird als Fehler behandelt.
- `regime.equities_baermarkt.*`/`regime.vix.*` — **Regel 10 (Spot)**: VIX als vorlaufendes Signal, vorsichtige Formulierung verlangt ("nicht immer", keine harte Kausalität). Kein Gate.
- `regime.cash_reserve_ziel.*` — keine Regel; Docstring explizit "rein informativ, kein neues Veto" — aber deterministisch aus den RM-1/RM-2/RM-4-Zwischenwerten berechnet.

**`regime_profil.*`** (beide)
- `.min_konfidenz_prozent` — indirekt über Regel 3 referenziert. Gate: hartes Veto (R-5.10) + Sockel der Positionsgrößen-Skalierung.
- `.small_cap_budget_prozent` — keine Regel; Gate: Small-Cap-Veto.
- `.gewicht_technik/_fundamental/_momentum/_kontext_makro`, `.gewinnabsicherung_verschaerft` — **keine Regel, kein Gate.** Siehe 3.2.

**`risiko_check.*`** (Spot-only)
- `.kauf_erlaubt`/`.veto_grund` — **Regel 2**: bei `false` niemals KAUFEN/NACHKAUFEN. Gate: zweites, redundantes Veto (Gürtel-und-Hosenträger).
- `.max_positionsgroesse_usd/_eur` — **Regel 3**: harte Obergrenze, kein Zielwert, serverseitig konfidenz-skaliert. Gate: vier Deckel-Kandidaten, Minimum wird gezogen.
- `.stop_loss_abstand_prozent`/`.cash_reserve_aktuell_prozent`/`.allokation_asset_aktuell_prozent`/`.small_cap_budget_prozent` — keine eigene Regel (Regel 3/16 decken die Konsequenz ab); alle mit hartem Gate (RM-5/RM-4/RM-2/R-5.10).
- `.drawdown_notbremse_geprueft` — hart `False`, dokumentierte, bewusste Lücke (RM-7/Z-3 nicht implementiert).

**`antizyklisch.*`** (Spot-Variante)
- `.funding_rate_aktuell` (roher Float) — indirekt über Regel 12; nicht im Spot-Gate, aber an Z.ai weitergereicht.
- `.moeglicher_flush` — **Regel 12**: vorsichtig formulieren ("möglicherweise", keine gesicherte Klassifikation). Kein Gate.
- `.long_konten_anteil_prozent`/`.retail_long_bias_extrem`/`.long_short_ratio_binance` — **Regel 15** (ausführlich): extremer/moderater Retail-Konsens ist Kontraindikator, gilt für den Inhalt, nicht nur das Label. Gate: dreistufiger Risikofaktor (Fakt zuerst).
- `.grund` — **Regel 12**: vorformulierter Text, in Begründung einbeziehen. Kein Gate.

**`markt_kontext.*`** (Spot-Variante) — **Regel 13** (gesamter Block): niedrig gewichteter Zusatzkontext.
- `.btc_exchange_flow_netto_btc`/`.hinweis`, `.stablecoin_supply_gesamt_usd` — Regel 13 (namentlich). Kein Gate.
- `.praesidentschaftszyklus.*` — Regel 13: rein deskriptiv, klarer Vorbehalt nötig. Kein Gate.
- `.naechste_fomc_sitzungen[]` — Regel 13: `<14 Tage` → als Volatilitätsfaktor in `key_risks` nennen. **Kein Gate — reine Prompt-Anweisung ohne Kontrolle.**
- `.naechste_cpi_veroeffentlichung` — Regel 13: `<5 Tage` → ebenfalls nennen, "historisch oft überdurchschnittliche Kursbewegungen". **Kein Gate.**

**Sonstige Spot-Fakten**
- `strategien_aktiv[]` — **keine Regel, kein Gate.**
- `tranchen_erlaubt` — **Regel 20**: nur bei `true` dürfen Tranchen gefüllt werden. Gate: Struktur-Validierung vorhanden (2-5 Einträge, Summe 100%), aber `tranchen_erlaubt=false` wird nicht hart erzwungen — nur ein Validierungsfehler bei strukturellen Mängeln, keine Ablehnung bei unerlaubter Befüllung.
- `disclaimers.*` — **Regel 5**: fehlende Makro-/Sentiment-Integration muss explizit benannt werden, keine erfundene Einschätzung. Kein Gate.

### 4.3 Hebel-Pipeline — Abweichungen von Spot

Übernommene, identische Blöcke: `asset.*` (reduziert: nur symbol/name/rolle),
`preis.*`, `technische_analyse.*` (exakt identisch), `historische_erfolgsquote.*`,
`historischer_makro_vergleich.*`, `liquiditaetszonen.*`, `signal_stabilitaet.*`,
`btc_relativwert.*`, `regime_profil` (aber `min_konfidenz_prozent` bei Hebel nicht
ausgewertet — Hebel nutzt stattdessen feste Schwellen 55/70 aus `risk_gate.py`).

**Hebel-spezifische Fakten:**

- `regime.richtungs_konflikt_mit_trigger`/`.richtungs_konflikt_hinweis` — **Regel 2**: explizit gewichten, gehebelte Gegen-Trend-Position ist strukturell riskanter. Gate: unabhängige Neuberechnung gegen die tatsächlich gewählte Richtung → Hebel-Deckel + Risikofaktor "Regime-Konflikt/-Ausrichtung".
- `antizyklisch.funding_rate_aktuell_prozent_pro_stunde`/`_pro_tag` — **Regel 9**: stündliche Rate NIEMALS zitieren (kaum einzuordnen für Menschen), stattdessen die Tagesrate MIT Einheit nennen. Gate: konkreter USD/EUR-pro-Tag-Betrag im Risikofaktor "Funding-Kosten".
- `trigger.trigger_zweig`/`.score_gesamt`/`.oi_change_pct_lookback`/`.kursaenderung_pct_lookback` — **Regel 7/8**: "einmal_trade" bei `kontra`, "swing_strategie" bei `trendfolge"`. Gate: `trigger_zweig=="kontra"` → AZ-7-Kontra-Bremse (Hebel-Deckel-Faktor).
- `position_aktuell.*` — **Regel 3** (zentral, lang): ERÖFFNEN/NACHKAUFEN/HALTEN-Logik abhängig davon, ob die eigene Richtung mit der bestehenden Position übereinstimmt. Bei Abweichung: System übersetzt das LLM-Urteil NACHTRÄGLICH deterministisch in TEILVERKAUF/SCHLIESSEN/HALTEN (Kontrathese-Übersetzung, Konfidenz-Schwellen 55/70, Bestätigungsfenster 2h).
  - `.tage_gehalten` — **Regel 7 (Warnung!)**: NICHT anhand einer angenommenen typischen Haltedauer bewerten — Nutzer hält historisch ~1 Tag, das war Marktreaktion, keine Strategie.
  - `.vorherige_hebel_empfehlung_nicht_umgesetzt` — Regel 3: nicht umgesetzte Hebel-Empfehlung explizit ansprechen. Kein Gate (rein Prompt-seitig).
- `optionsmarkt.*` (Deribit, immer BTC) — **Regel 21**: DVOL + Skew als Cross-Check gegen die eigene Konfidenz; Widerspruch im Gegenargument benennen. **Kein Gate** — der beschriebene Cross-Check bleibt komplett dem LLM überlassen.
- `hebel_kontext.max_hebel_config`/`.max_sicherer_hebel_geschaetzt` — **Regel 4**: realistischer Hebel-Vorschlag, wird nachträglich deterministisch geprüft. Gate: zwei der Deckel-Kandidaten für `hebel_final`.
- `markt_kontext.*` bei Hebel — `praesidentschaftszyklus`/`naechste_fomc_sitzungen`/`naechste_cpi_veroeffentlichung` werden geliefert, aber **keine Hebel-Regel dafür existiert** (Spot-Regel 13 gilt nur dort). Höchste Priorität, siehe 3.1.
- `disclaimers.hinweis` bei Hebel — nur ein Kurztext, keine `makro_einbezogen`/`sentiment_einbezogen`-Flags wie bei Spot, keine Regel.

**Neu am 2026-08-05 — die drei Fakten der LLM-Erweiterung** (Herleitung, Messung und
Verbleib-Entscheidung in Abschnitt 7):

- `kosten.*` — **Regel 30**. Tabelle „Kosten in R" über fünf Stop-Abstände × drei
  Haltedauern, dazu `lesehilfe`, `zwei_folgerungen` und die gemessene Haltedauer
  (Median 2,6 Tage). Bewusst eine **Tabelle statt einer Formel** — ein Modell, das
  rechnen soll, rechnet falsch; eines, das nachschlägt, schlägt richtig nach.
  Quelle: `backward_tracking.kosten_kontext_fuer_prompt()`, gespeist aus
  `kosten_in_r()`. **Kein Gate** — Frage 1 verneint: die richtige Reaktion auf
  Kosten hängt vom Setup ab (ein enger Stop an echtem Support kann trotz höherer
  Kostenlast richtig sein). Regel 30 sagt daher ausdrücklich **„KEIN Limit"**.
- `ausstiegsregel.*` — **Regel 31**. Trailing-Mechanik der seit 05.08. scharfen
  Regel (`ausloese_r`, `abstand_r`, Wirkungsweise, ausdrücklich `kein_breakeven_lock`
  mit der Begründung aus der 01.08.-Messung). Liefert `None`, wenn die Regel
  abgeschaltet ist (`ausloese_r = 0`) — der Fakt kann also nie behaupten, es gebe
  einen Trailing-Stop, den es nicht gibt. **Kein Gate.** Der Schlüsselsatz
  `was_das_fuer_deine_zonen_heisst` nennt **beide** Lesarten (weiteres Ziel wegen
  begrenztem Rückfallrisiko / näheres Ziel weil der Trailing ohnehin greift) und
  entscheidet bewusst nicht — Kontext liefern, Urteil offenlassen.
- `systemguete.*` — **Regel 31**. Die eigene, gemessene Bilanz: `anzahl_ausgewerteter_trades`,
  `erwartungswert_r`, `sqn` + `sqn_einordnung`, `profit_factor`. **Greift nur bei
  Hebel**: die Mindestschwelle liegt bei n ≥ 30 ausgewerteten Trades, und die
  erreicht Stand 05.08. allein `hebel` (n = 124). Krypto-Spot (19), Aktien, ETF und
  Rohstoffe liegen darunter — dort fällt der Fakt still weg, weil eine Systemgüte
  aus fünf Signalen irreführender wäre als gar keine. **Kein Gate.**

  **Der heikelste der drei.** Die Zahl ist unerfreulich (EW −0,114 R, SQN −0,77
  „kaum handelbar"). Die naheliegende Formulierung wäre „sei deshalb vorsichtiger"
  — und genau die wäre der Fehler: derselbe Mechanismus ließ beim
  Ausführbarkeits-Hinweis die ERÖFFNEN-Quote von 93 % auf 3 % einbrechen. Der Fakt
  trägt deshalb den ausdrücklichen Satz „Kalibrierungs-Kontext, KEINE
  Handlungsanweisung und kein Grund, grundsätzlich zurückhaltender zu werden".
  **Daraus folgt eine Pflicht:** die ERÖFFNEN-Quote ist Pflicht-Messgröße jedes
  Tests dieses Fakts — nicht nur die Zonenqualität. Senkt er sie im Betrieb,
  gehört er wieder entfernt.

### 4.4 Was zusätzlich/separat an Z.ai geht

Zwei getrennte, rein beobachtende Calls (Phase 1, kein Gate): Konsistenz-Check
(`baue_fakten()`) bekommt `symbol`, `action`, `confidence_pct`, `richtung` (nur Hebel),
`rsi`, `trend`, `regime`, `funding_rate_vorzeichen`, `technische_konfluenz`,
`optionsmarkt_skew` (nur Hebel) plus den zu prüfenden `short_reasoning`-Freitext.
Unabhängiger Richtungsabgleich (`baue_objektive_fakten()`) bekommt dieselbe Menge
OHNE `richtung`/`action`/`confidence_pct` (Anker-Vermeidung). Der Übereinstimmungs-
Vergleich läuft deterministisch in Python, nicht im Modell.

**Z.ai bekommt NICHT:** Fibonacci, Support/Resistance, ATR, Liquiditätszonen,
Signal-Stabilität, BTC-Relativwert, Makro-Analogie, historische Erfolgsquote,
Trigger, Position, Hebel-Kontext, Markt-Kontext, Risiko-Check, Haltung.

### 4.5 Größen, die nur im Gate leben (nie an das LLM gehen)

`richtungswende` (Risikofaktor, kein Prompt-Pendant — das LLM erfährt nichts davon),
`cash_veto`/`cash_veto_reason`, `crv` (Veto + gestufter Risikofaktor), `sl_abstand_relativ`
(nur Hebel), `positionsgroesse_usd` (Hebel-Zwischenrechnung), `regime_persistenz_tage`.
Sowie die LLM-**Ausgaben** `trade_thesis_typ`, `forecast.bear/bull.probability_pct`,
`confidence_pct`, `eigene_einschaetzung.folgen` (rein diagnostisch, ändert nie die
LLM-Werturteile — siehe [[feedback_llm_synthese_kein_deterministischer_override]]),
`top_gruende`-Text (Hebel-only-Filter gegen Retail-Konsens-Inhalte).

---

## 5. Nächste Schritte (Priorisierung bestätigt, 2026-07-28)

1. **Stufe 3 — Committet/gepusht (`7eac0ec`, 2026-07-28)** (Statusvokabular siehe
   [[reference_test_und_verifikationsmethodik]]): Hebel-Prompt um FOMC/CPI-Kontext
   ergänzt — neue Regel 22 in `agent/krypto/hebel_analyst.py::SYSTEM_PROMPT`
   (vorherige Regel 22 "eigene_einschaetzung" zu Regel 23 verschoben, inkl.
   Korrektur der bereits vorher veralteten "Regel 21"-Verweise an 3 Stellen im
   Code). Liefert dokumentierten Marktkontext (erhöhte realisierte Volatilität um
   FOMC/CPI, KEINE Richtungsaussage) statt einer vorgegebenen Schlussfolgerung —
   das LLM gewichtet selbst, ob und wie stark das bei der konkreten Stop-Loss-
   Distanz relevant ist. `praesidentschaftszyklus` wird explizit als für Hebel kaum
   aussagekräftiger Hintergrund-Fakt eingeordnet. Bewusst KEIN neues Gate/Deckel —
   passend zum Grundsatz "Kontext liefern, Urteil nicht vorwegnehmen" (Abschnitt 1,
   Frage 2). Verifiziert (Klasse 1, Änderungsklassen siehe Methodik-Dokument):
   Modul-Import, Compile-Check, durchgängige Regelnummerierung 1-23. Stufe 5
   (im Betrieb bestätigt) ist bei dieser reinen Kontext-Ergänzung ohne Gate
   voraussichtlich nicht sauber isolierbar messbar — siehe Methodik-Dokument
   Abschnitt 2.2.
2. **Stufe 3 — Committet/gepusht** (Statusvokabular siehe
   [[reference_test_und_verifikationsmethodik]]): Fear&Greed-Index war komplett
   toter Fakt (an `build_facts()` geliefert, aber ohne Prompt-Regel für Spot,
   ganz ohne Fakt-Übergabe für Hebel) — neue Regel 29 in
   `agent/krypto/analyst.py::SYSTEM_PROMPT` (vorherige Regel 29
   "eigene_einschaetzung" zu Regel 30 verschoben, 3 Kreuzverweise korrigiert:
   Schema-Kommentar, Modul-Docstring, Validierungsfunktion-Kommentar).
   Verifiziert (Klasse 1): Modul-Import, Compile-Check, durchgängige
   Regelnummerierung 1-30.

   **Nutzer-Nuance (2026-07-28), die die Regel komplexer macht als ein
   einfacher Kontraindikator:** im Bärenmarkt ist Fear&Greed nicht eindeutig
   verwertbar, da lange Angstphasen vorherrschen und Bodenbildung nur mit
   zusätzlichen Faktoren sinnvoll einzuordnen ist. Bei Hype-Phasen ist die
   Lage anders gelagert (kürzere Phasen, tendenziell brauchbareres
   Warnsignal). Regel 29 bildet das **asymmetrisch** ab: extreme Angst nur als
   unterstützenden Faktor werten (gekoppelt an niedriges `zyklus_risiko` +
   weitere Fakten), niemals als eigenständigen Kaufgrund; extreme Gier darf
   stärker gewichtet werden, besonders kombiniert mit hohem `zyklus_risiko`.
   Passt zum Grundsatz "Kontext liefern, Urteil nicht vorwegnehmen"
   (Abschnitt 1, Frage 2) und zur Spot-Zeithorizont-Einordnung (Frage 4) —
   die Regel liefert Marktkontext samt der dokumentierten Asymmetrie, nimmt
   dem LLM aber nicht die eigentliche Gewichtungsentscheidung ab.

   **Geltungsbereich: nur Spot (Variante a).** Für Hebel wäre eine analoge
   Regel eine **Variante B**, die geprüft und bewusst NICHT umgesetzt wurde
   (siehe [[feedback_document_rejected_options]]-Muster): Hebel-Positionen
   haben eine typische Haltedauer von Stunden bis wenigen Tagen — die für
   Fear&Greed relevante Unterscheidung "lange Bärenmarkt-Angstphase vs. kurze
   Hype-Phase" ist eine mehrwöchige bis mehrmonatige Marktstruktur-Frage
   (Zeithorizont-Fehlpassung, Frage 4 des Entscheidungsrasters, analog zum
   bereits identifizierten `historischer_makro_vergleich`-Fall bei Hebel,
   siehe Punkt 5 unten). Nutzer-Einschätzung dazu: "hier ist weniger mehr" —
   das Konzept nicht künstlich aufblähen. **Revisit-Bedingung:** falls sich
   künftig zeigt, dass kurzfristige Fear&Greed-Ausschläge (Tagesbasis statt
   Wochen/Monate) selbst einen brauchbaren Signalwert für Hebel-Timing haben
   (z.B. per Backtest gegen `hebel_signals`-Outcomes belegt), wäre das ein
   eigenständiger neuer Fakt/eigene Regel — keine einfache Kopie von Regel 29.

   **Token-Budget-Check (Standardprüfung ab jetzt für jede Regeländerung,
   siehe Abschnitt 1 Frage 5):** Regel-29-Text ca. 620 Zeichen / ~150 Token.
   Mistral ist der einzige reale Ablaufkette-Bestandteil neben Gemini (siehe
   [[reference_llm_provider_recherche_uebersicht]], 2026-07-28 korrigiert —
   Z.ai ist NICHT mehr Teil der Haupt-Fallback-Kette, läuft nur noch separat
   für die Gegenprüfung mit eigenem schlanken Fakten-Satz und sieht diesen
   SYSTEM_PROMPT nie). Mistral: 2.250.000 TPM / 300 RPM, realer Verbrauch
   geschätzt ~1.000-1.200 Token/Minute im Schnitt — ein einzelner
   ~150-Token-Regelzuwachs ist rechnerisch irrelevant für die Kapazität.
   Bleibt dennoch als Disziplin sinnvoll (Resilienz falls sich Mistrals
   Bedingungen ändern, Latenz, Prompt-Hygiene) — kein Anlass, eine bestehende
   Regel zum Ausgleich zu entfernen.
3. **Stufe 2 — Verifiziert (synthetisch), noch nicht committet:** `regime_profil.
   gewicht_technik`/`gewicht_fundamental`/`gewicht_momentum`/`gewicht_kontext_makro`
   war in BEIDEN Pipelines (Spot + Hebel) ein toter Fakt — das komplette
   `regime_profile`-Dict wird via `build_facts()`/`build_hebel_facts()` an die
   LLM geliefert, aber keine Prompt-Regel referenzierte es (im Unterschied zu
   `min_konfidenz_prozent`/`small_cap_budget_prozent` aus demselben Profil, die
   bereits deterministisch im Gate bzw. Scoring genutzt werden). Inhaltlich
   kein Nebensächlichkeits-Fakt, sondern ein durchdachtes, regimeabhängiges
   Gewichtungsschema aus `Basisinfos/config.yaml` (`regime.profile`) — z.B.
   `krise_extrem`: Technik 0.15/Fundamental 0.45/Momentum 0.15/Makro 0.25;
   `bulle`: Technik 0.43/Fundamental 0.25/Momentum 0.17/Makro 0.15.

   Neue Regel in `agent/krypto/analyst.py` (Regel 30, `eigene_einschaetzung`
   zu Regel 31 verschoben) UND `agent/krypto/hebel_analyst.py` (Regel 23,
   `eigene_einschaetzung` zu Regel 24 verschoben, je 3 Kreuzverweise korrigiert):
   nutzt das Gewichtungsschema als ORIENTIERUNG dafür, wie stark die KI
   technische/fundamentale/Momentum-/Makro-Aspekte in `long_reasoning`/
   `top_gruende` gewichtet — ausdrücklich KEINE starre Formel oder Pflichtquote,
   die eigene Einschätzung der konkreten Fakten bleibt maßgeblich. Passt zum
   Grundsatz "Kontext liefern, Urteil nicht vorwegnehmen" (Abschnitt 1, Frage 2).

   **Bewusst für BEIDE Pipelines** (anders als Fear&Greed, Punkt 2): die Frage
   "welche Analyse-Linse ist in diesem Regime verlässlicher" gilt nicht nur
   langfristig — die Regime-Klassifikation selbst wird bei Hebel bereits
   intensiv genutzt (Regime-Konflikt-Deckel, Regime-Persistenz), Frage 4 des
   Entscheidungsrasters spricht hier also nicht gegen eine gemeinsame Regel.

   Verifiziert (Klasse 1): Modul-Import + Compile-Check beider Dateien,
   durchgängige Regelnummerierung Spot 1-31 / Hebel 1-24 ohne Lücke.
   Token-Budget-Check: ca. 150 Token je Datei, vernachlässigbar (siehe
   Begründung bei Punkt 2).
4. **Stufe 2 — Verifiziert (synthetisch), noch nicht committet:** Spot-Retail-
   Konsens-Filter analog zu Hebel nachgezogen. Bei Hebel gibt es zwei getrennte
   Mechanismen, die beide "Retail-Konsens" heißen: `retail_konsens_risiko()`
   (richtungsabhängige Deckel-Formel für den erlaubten Hebel) und
   `filtere_retail_konsens_top_gruende()` (reiner Text-Filter, entfernt jeden
   `top_gruende`-Eintrag, der sich auf Retail-Konten-Positionierung beruft,
   unabhängig von der Richtung — Kategorie-Fehler: Positionierungsdaten sagen
   etwas über Squeeze-/Liquidationsrisiko aus, nicht darüber, ob der Kurs
   steigen sollte). Nur Letzteres ist für Spot relevant (kein Hebel-Konzept
   bei Spot); Spot hat aber bereits denselben zugrunde liegenden Fakt
   (`retail_long_bias_extrem`/`long_konten_anteil_prozent`) und dieselbe
   Prompt-Warnung (Regel 15), nur ohne deterministische Rückversicherung.

   **Bewusst dupliziert statt importiert** (Nutzer-Einschätzung: Spot/Hebel
   könnten hier eher auseinanderlaufen als gleich bleiben): `risk_gate.py`
   bekommt eine eigene Kopie von `_RETAIL_KONSENS_TOP_GRUND_MUSTER`/
   `filtere_retail_konsens_top_gruende()`, mit Kreuzverweis-Kommentar zum
   Hebel-Pendant in `hebel_risk_gate.py` — abweichend vom sonst üblichen
   "einzige Quelle der Wahrheit"-Muster (`CRV_MINIMUM`), weil Spot
   (langfristige These) und Hebel (kurzfristige Taktik) hier absichtlich als
   eigenständig behandelt werden.

   **Anwendungsort:** neuer Parameter `filter_retail_konsens_top_gruende`
   (Default `False`) in `risk_gate.py::post_check()` — nur
   `agent/krypto/pipeline.py` (Krypto-Spot) setzt `True`. NICHT generisch für
   alle 4 Spot-family-Pipelines aktiv: Aktien hat mit `short_interest_finra`
   ein ähnlich klingendes, aber fachlich anderes Konzept (institutionelle
   FINRA-Meldungen, kein Retail-Konsens) — per synthetischem Test (T4)
   empirisch bestätigt, dass der Regex bei FINRA-Short-Interest-Formulierungen
   ("Short-Interest laut FINRA...", "Short-Squeeze-Setup...") NICHT anschlägt,
   trotzdem bewusst nur am Krypto-Spot-Aufruf aktiviert statt generisch in
   `post_check()`, um kein unnötiges Risiko in einer gemeinsam genutzten
   Funktion einzugehen.

   Verifiziert (Klasse 2, 4 Testfälle): T1 Hebel-Regression (Verhalten
   unverändert), T2 Spot-Positivfall (identisches Verhalten zu Hebel bei
   demselben Text), T3 Grenzfälle (kein list, leere Liste, fehlendes
   `text`-Feld, `None`-Eintrag), T4 Kombinationsfall (Retail-/Long-Short-
   Ratio-Varianten werden gefiltert, FINRA-Short-Interest/Short-Squeeze-Text
   bleibt erhalten). Regressionscheck: Import aller 5 Spot-family-
   Pipeline-Module OK.
5. **Stufe 2 — Verifiziert (synthetisch), noch nicht committet:** `historischer_
   makro_vergleich` bei Hebel geprüft. Anders als Fear&Greed/`regime_profil`
   war das KEIN toter Fakt ohne Kontext — die Hebel-Regel 15 hatte bereits
   eine auffällig starke Warnung ("NIEMALS als belastbare Statistik...
   insbesondere für Hebel-Positionen"). Die eigentliche Frage: lohnt sich der
   Fakt trotz starker Warnung noch, angesichts der 6-/12-Monats-Vorwärts-
   renditen (`top_analoge`, `spx_forward_*`/`btc_forward_*`), die strukturell
   ein Mehrmonats-Konzept sind — ein Kategorie-Problem, das selbst starke
   Prompt-Warnungen nicht zuverlässig lösen (dasselbe Muster wie beim
   Retail-Konsens-Fund: reine Prompt-Warnungen reichen nicht immer aus).

   **Lösung (Nutzer-Vorschlag, verfeinert):** nicht komplett entfernen,
   sondern **destillieren** — die aktuelle Makro-Konstellation
   (`aktuelle_konstellation`: Dollarstärke/Zinsen/Renditen/Öl/Aktienbewertung)
   ist zeitlos gültig, kein Mehrmonats-Konzept, bleibt erhalten. Neue Funktion
   `agent/krypto/makro_analog.py::distill_makro_vergleich_fuer_hebel()`
   reduziert auf `aktuelle_konstellation` + `anzahl_analoge` +
   `spx_median_forward_6m_prozent` (12-Monats-Wert bewusst weggelassen — noch
   länger, noch unpassender; `top_analoge`-Liste entfällt komplett — größter
   Umfang UND größte Fehlinterpretationsgefahr; kein aggregiertes BTC-Feld,
   unverändert). Gleicher Fakt-Schlüsselname `historischer_makro_vergleich`
   für Spot UND Hebel beibehalten (nicht umbenannt) — der Fakt wird nirgends
   dauerhaft gespeichert, beide Fassungen werden nie gemeinsam vom selben
   Code gelesen, ein Kreuzverweis-Kommentar an der Hebel-Definitionsstelle
   reicht für menschliche Lesbarkeit.

   Hebel-Regel 15 komplett neu gefasst: die verbleibende Kennzahl wird
   ausdrücklich als **richtungsneutraler** Risikoappetit-Hintergrund für
   `key_risks`/`gegenargument` gerahmt — bewusst KEINE LONG/SHORT-Ableitung
   (SPX-Vorwärtsrendite auf Krypto zu übertragen wäre eine Scheingenauigkeit,
   die der Fakt selbst schon für `btc_forward_*` vermeidet) und KEINE
   Kategorie-Bucket-Übersetzung (bräuchte eine nicht vorhandene
   Vergleichsbasis, ebenfalls Scheingenauigkeit) — rohe Zahl mit klarer
   Einordnung, konsistent mit `zyklus_risiko`/`atr.perzentil`.

   Verifiziert (Klasse 2, 4 Testfälle): T1 `None`-Input, T2 Positivfall
   (Destillation entfernt `top_analoge`/`aktueller_monat`/12-Monats-Wert
   korrekt, behält die 3 Zielfelder), T3 Grenzfall (fehlende/`None`-Werte),
   T4 Kombinationsfall (Import-Konsistenz zwischen `hebel_pipeline.py` und
   `makro_analog.py`). Regressionscheck: Spot (`pipeline.py`/`analyst.py`)
   unverändert, Regelnummerierung Hebel 1-24 ohne Lücke.

Diese Liste wird schrittweise abgearbeitet, mit Vorher/Nachher-Beobachtung über die
in Abschnitt 6 (Prozess-Phase 4) genannten Metriken.

---

## 6. Über den Tellerrand — essentielle Signale, die komplett fehlen

Abschnitt 4 ist eine Bestandsaufnahme dessen, was existiert. Diese Frage ist anders:
was fehlt UNS GANZ, obwohl es in professioneller Krypto-Analyse Standard ist? Bewertet
nach (a) tatsächlicher Marktüblichkeit, nicht Exotik, (b) Umsetzbarkeit mit
kostenfreien Quellen (feste Projekt-Vorgabe, siehe
[[feedback_kostenfreie_llm_only]]), (c) Mehrwert für den jeweiligen Zeithorizont
(Abschnitt 1, Frage 4).

### 6.1 Sofort umsetzbar — Daten bereits vorhanden, nur nicht verdrahtet

| Kandidat | Warum marktüblich | Aufwand |
|---|---|---|
| **DXY-Trend (Dollar-Index) direkt in Krypto-Fakten** — **ERLEDIGT (2026-07-28)** | Dollar-Stärke korreliert historisch invers mit Krypto/Risk-Assets — Standard-Makro-Cross-Check bei jedem Krypto-Desk. `api/macro.py::get_dollar_index_trend()` existiert bereits (gebaut für `agent/kategorie_thesen.py`), wird aber **nie** an Krypto-Spot/Hebel übergeben — nur indirekt und stark verzögert über den monatlichen Makro-Analog-Cache. | Gering — reines Wiring, Funktion + Datenquelle bereits getestet im Einsatz. |
| **Open-Interest-Trend-vs-Kurs-Divergenz** (Squeeze-Erkennung) — **ERLEDIGT (2026-07-28)** | Klassische Technik: Kurs steigt bei FALLENDEM OI → oft fragile Short-Squeeze-Rally (wenig belastbar); Kurs steigt bei STEIGENDEM OI → frisches Kapital, robuster. Wird an praktisch jedem Krypto-Derivate-Desk verwendet. | Gering — wir haben Binance/Bybit/OKX-OI UND Kursänderung bereits (`antizyklisch.*`), nur die Verknüpfung als eigener Fakt fehlt. |
| **Funding-Rate-Perzentil** (Crowding-Indikator) — **ERLEDIGT (2026-07-28)** | Zeigt, ob die AKTUELLE Funding-Rate historisch extrem ist (Crowding-Signal), nicht nur den Rohwert. Genau dasselbe Prinzip wie das bereits gebaute `atr_percentile()` — nur auf Funding-Rate-Historie angewendet. | Gering — identisches Code-Muster wiederverwendbar. |

### 6.2 Recherchebedürftig — plausibel machbar, aber nicht sofort einschätzbar

| Kandidat | Warum interessant | Offene Frage |
|---|---|---|
| **Coin-spezifischer Exchange-Netto-Flow** (nicht nur BTC) | `markt_kontext.btc_exchange_flow_netto_btc` existiert NUR für BTC. Für Alts wäre dasselbe Prinzip (Zufluss=Verkaufsdruck-Hinweis) wertvoll, gerade für Hebel-Kandidaten abseits BTC/ETH. | CoinMetrics ist bereits als Datenquelle im Einsatz (`api_health`-Liste) — ob die kostenfreie Stufe genug Alt-Coins abdeckt, ist ungeprüft. |
| **Spot-Futures-Basis / Perpetual-Premium** | Zeigt, wie stark der Markt long/short positioniert ist (Basis-Spread), unabhängig von Funding-Rate. Ergänzt Funding-Rate um eine zweite, unabhängige Crowding-Perspektive. | Ob Kraken/Binance-Public-APIs Mark-Price/Index-Price sauber genug liefern, um eine belastbare Basis abzuleiten, ist ungeprüft. |

### 6.3 Bewusst zurückgestellt — Aufwand/Nutzen bzw. Kostenfrage

- **Orderbuch-Tiefe / Bid-Ask-Imbalance** — in professionellem Trading Standard, aber
  für die meisten Altcoins über kostenfreie APIs nicht robust und nicht ohne
  erheblichen Aufwand verfügbar. Bewusst nicht verfolgt, keine Deadline.
- **Makro-Korrelationsregime-Klassifikation** ("handelt Krypto gerade als Risk-on-
  Tech-Proxy oder als digitales-Gold-Hedge?") — würde viele der obigen Punkte
  (DXY, Equities-Korrelation) erst richtig einordnen können, ist aber methodisch
  aufwendig und eher ein Forschungsthema als ein kurzfristiger Fakt. Als Idee
  vorgemerkt, keine Umsetzung geplant.

Priorisierungsvorschlag: 6.1 zusammen mit den bereits entschiedenen Punkten aus
Abschnitt 5 angehen (DXY-Wiring ist im Aufwand vergleichbar mit den dortigen
Punkten), 6.2 erst nach einer kurzen Datenverfügbarkeits-Prüfung, 6.3 nicht ohne
neue Nutzer-Anfrage.

**OI-Squeeze-Divergenz + Funding-Rate-Perzentil — Umsetzung (2026-07-28):** vor
der Umsetzung Mengenanalyse gegen die echte Desktop-DB durchgeführt, da die
Doku-Behauptung "Daten bereits vorhanden" nur fuer Hebel-geprüfte Assets
zutraf, nicht pauschal für Spot. Fund: `asset_hebel_settings` (Hebel-Prüfung-
Toggle) ist ein reiner OPT-OUT (Default `True` für ALLE Krypto-Assets, siehe
`db.get_hebel_pruefung_erlaubt()`-Docstring) und die Tabelle war zum
Prüfzeitpunkt komplett leer (niemand hat je opt-out gemacht) — von 43 Krypto-
Watchlist-Assets hatten bereits 38 (88%) historische OI-/Funding-Daten in
`open_interest_snapshot`, die 5 fehlenden plausibel durch neuere Watchlist-
Ergänzungen oder fehlenden Derivate-Markt erklärt (bereits durch die
bestehende OI-Abdeckungs-Warnung sichtbar gemacht). Damit Entscheidung: beide
Fakten von Anfang an für Spot UND Hebel bauen, keine gestaffelte Ausweitung.

Neue reine Funktion `classify_squeeze_divergenz()` (`hebel_screening.py`)
vergleicht `compute_oi_change_pct()` (NEUES, eigenes 72h-Lookback-Fenster,
`config.yaml krypto_oi_fakten.squeeze_oi_lookback_stunden` — bewusst NICHT
Hebels 4h-Trendfolge-Fenster, da zeitlich nicht vergleichbar mit dem 3-Tage-
Kursfenster) mit dem bereits vorhandenen `antizyklisch.kursaenderung_letzte_
tage_prozent` (`anticyclic.py::DROP_LOOKBACK_DAYS=3`). 4 Label plus
"neutral" (Mindestbetrag `squeeze_schwelle_prozent`). Neue Funktion
`funding_rate_percentile()` (`indicators/calculations.py`) exakt nach dem
`atr_percentile()`-Muster (eigene `MIN_FUNDING_PERZENTIL_PUNKTE`-Konstante,
kein Anfassen des bestehenden ATR-Codes), gefüttert über einen DB-Fetch-
Wrapper (`hebel_screening.py::compute_funding_rate_percentile()`), der die
redundant in allen 3 Börsen-Zeilen gespeicherte Kraken-Funding-Rate ausliest.

Beide Fakten in `pipeline.py`/`hebel_pipeline.py` berechnet und in
`analyst.py`/`hebel_analyst.py` als `antizyklisch.squeeze_divergenz`/
`.funding_rate_perzentil` verdrahtet (neue Regeln 31/25). Verifiziert:
Klasse 2, 16 synthetische Testfälle (alle 4 Squeeze-Quadranten + neutral +
None-Propagierung + Perzentil-Grenzfälle + DB-Wrapper mit None-Filterung),
Regelnummerierung + Import-Regressionscheck über alle 6 betroffenen Module.

**DXY-Trend — Umsetzung (2026-07-28):** einheitlich für alle 6 Pipelines (Krypto
Spot/Hebel, Aktien, Rohstoffe, Themen-ETF, Hedge) verdrahtet, keine
Sonderbehandlung (Nutzer bestätigt: keine Gegenargumente gegen Gleichbehandlung
wie beim VIX-Vorbild). `RegimeResult.dollar_index_wert`/`dollar_index_trend`
(bereits vorklassifiziert: "steigend"/"fallend"/"gleichbleibend"/"unbekannt",
`DOLLAR_INDEX_TREND_THRESHOLD_PCT = 1.5`) fließt über `compute_current_regime()`
(gemeinsame Funktion aller 6 Pipelines) automatisch in `build_facts()`/
`build_hebel_facts()` als `regime.dollar_index.wert`/`.trend`. In 5 der 6
Analyst-Dateien als Ergänzung an die bestehende VIX-Regel angehängt (identisches
Makro-Kontext-Muster, minimaler Zusatz-Tokenaufwand); Hebel hat kein
VIX-Äquivalent, dort eigene kompakte Regel (Regel 24, vor dem abschließenden
`eigene_einschaetzung`-Rückblick). Verifiziert Klasse 1 (Import/Compile/
Regelnummerierung über alle 6 Dateien) — reines, risikoarmes Fakten-Wiring nach
demselben bereits produktiv laufenden VIX-Muster, keine neue Logik.

---

## LLM1 ist positionsempfindlich — live gemessen (2026-08-04)

**Der Ausgangsbefund lag seit dem 29.07. vor**, gemessen an der echten
Z.ai-API (`gegenpruefung.py::leite_eigene_richtung_positionsrobust`):
Gegenindikator früh → ignoriert (6/6), am Ende → stärker gewichtet (4/6),
in der Mitte → noch entschiedener (6/6). Das ist die U-förmige
Aufmerksamkeitskurve der *Lost-in-the-Middle*-Literatur. **LLM2 bekam
daraufhin Position Swapping. LLM1 hat davon nichts.**

**Die Reihenfolge im Hebel-Prompt ist fest** — 17 Blöcke, und sie endet so:

| Position | Block | |
|---|---|---|
| 7 von 17 | `trigger` | der Grund, warum das Signal existiert — **schwache Mitte** |
| **17 von 17** | `disclaimers` | ein Hinweistext — **stärkste Position** |

**Live-Messung am Desktop (Mistral, temperature=0.2 wie im Betrieb),
2 Faktensätze × 4 Arme × 5 Wiederholungen:**

| Arm | action | Konfidenz | gegen Rauschen |
|---|---|---|---|
| **Rauschboden** (A1 gegen A2, identischer Prompt) | 0,000 | 0,60 pp | — |
| umgekehrte Reihenfolge | 0,000 | 1,10 pp | 1,8× |
| **`trigger` ans Ende** | 0,000 | **3,20 pp** | **5,3×** |

**Die action blieb stabil, die Konfidenz nicht.** Sie fällt von 76,8 auf
73,2, wenn `trigger` ans Ende wandert — mehr als das Fünffache dessen, was
zwei identische Läufe auseinanderliegen.

**Warum das kein Längenproblem ist:** Mistral hat 2.250.000 TPM und 300 RPM
(am Dashboard verifiziert) — kein Kontextdruck. Anders als bei Z.ai, das ab
8K Token auf 1 % Concurrency gedrosselt wird und deshalb einen bewusst
schlanken Faktensatz bekommt. Bei LLM1 ist es ein reiner Aufmerksamkeitseffekt.

**Was daraus NICHT folgt:** dass eine „bessere" feste Reihenfolge die Lösung
ist. Genau das wurde am 29.07. verworfen — bei einem echten Signal ist
vorher nicht bekannt, welcher Fakt der Ausreißer ist, und *jede* feste
Reihenfolge bevorzugt strukturell den zuletzt genannten. Das etablierte
Gegenmittel ist Position Swapping.

**Offen:** Ob sich die Konfidenzverschiebung von 3,2 pp auf die
Handelsentscheidung auswirkt. Die action war in diesem Lauf stabil — bei
n=2 Faktensätzen ist das aber keine belastbare Aussage, sondern ein erster
Hinweis. Vor einer Prompt-Änderung gehört der Lauf verbreitert.

**Einschränkung des Laufs, ehrlich benannt:** Der erste Versuch mit 72
schnellen Aufrufen scheiterte überwiegend mit HTTPError. Ich habe das als
Ratenbegrenzung gedeutet und eine Drossel eingebaut — bei 300 RPM hätte die
Rate aber nicht greifen dürfen. Was tatsächlich half, war vermutlich die
Wiederholung, nicht die Wartezeit. **Die Ursache ist nicht belegt.**

---

## 7. Die LLM-Erweiterung vom 2026-08-05 — drei neue Fakten (Regeln 30/31)

*Katalog-Einträge in 4.3. Dieser Abschnitt hält fest, warum sie gebaut wurden,
was die Messung ergab und warum sie trotz Nullbefund drinbleiben.*

### 7.1 Warum überhaupt neue Fakten

Bis dahin waren **acht Selektionsmechanismen** gemessen worden — Screening-Score,
Konfidenz, Richtungswahl, Prompt-Regeln, CRV-Bänder, `halte_kriterium`,
Allocator-Auswahl — und keiner trug nachweisbar. Am *Sortieren* vorhandener
Information war nichts mehr zu holen. **Neue Information war die letzte unerprobte
Kategorie.** Nutzer-Vorgabe vom 05.08.: „merke dir vor allem die Punkte wo wir
Informationen derzeit NICHT dem LLM geben".

Aus sechs identifizierten Lücken wurden drei umgesetzt. Auswahlkriterium: beide
aussichtsreichsten (Kosten, Ausstiegsregel) waren **bereits deterministisch
berechnet** — es fehlte nur die Weitergabe. Und beide betreffen genau die Größen,
die das Modell selbst setzt: Stop und Ziel. Ein Modell, das seine Kosten nicht
kennt, kann kein kostendeckendes CRV wählen; eines, das den Trailing-Stop nicht
kennt, setzt Ziele gegen eine Regel, von der es nichts weiß.

### 7.2 Was bewusst NICHT gebaut wurde

| Lücke | Warum nicht |
|---|---|
| **Z-3 Portfolio-Drawdown** | Das 3+1-Raster ordnet ihn dem **Gate** zu: Frage 1 ist bejaht, „Drawdown über Schwelle → Risiko reduzieren" ist kontextunabhängig. Ein Fakt wäre hier die falsche Ebene. |
| **Ausführbarkeit / `nur_long`** | **Gemessen und verworfen.** Der ehrliche Hinweis ließ die ERÖFFNEN-Quote von 93 % auf 3 % einbrechen. Nicht anfassen. |
| **Zieldauer / Haltedauer** | Es gibt gar keine — die zwei vorhandenen Felder widersprechen einander. Das ist ein **Konstruktionsfehler**, keine Prompt-Ergänzung. |

### 7.3 Das Messergebnis

Drei-Arm-Design mit Rauschboden (A1/A2 identisch + B), **gepaart** — jeder Arm
sieht denselben Fall. 24 gepaarte Fälle, kombinierter Test aller drei Fakten.

| | |
|---|---|
| Wirkung auf den Stop-Abstand | **−0,334 pp** |
| nötiges n / vorhanden | **212** / 24 |
| ERÖFFNEN-Wächter (A1 / A2 / B) | 92,5 % · 92,1 % · 95,7 % — **kein Einbruch** |

**Kein Nachweis.** Der Effekt halbierte sich beim Verdoppeln der Stichprobe
(−0,734 → −0,334 pp), das nötige n stieg von 16 auf 212 — die klassische Signatur
eines Nullbefunds.

Bemerkenswert war die **Richtung**: erwartet wurden *weitere* Stops (wegen der
Kosten), das Modell wählte *engere*. Plausibel wegen der Ausstiegsregel — wer
weiß, dass ab +1R nachgezogen wird, kann einen engeren Anfangsstop verantworten.
Genau deshalb nennt Regel 30 beide Lesarten und schreibt keine vor.

**Methodisch wichtig:** der Kosten-Fakt **allein** hätte n = 618 gebraucht,
kombiniert waren es 16. Fakten einzeln zu testen ist bei dieser Effektgröße
aussichtslos — der gemeinsame Test war die richtige Entscheidung.

### 7.4 Warum sie trotzdem drinbleiben

1. **„Nicht nachweisbar" ist hier eine Aussage über die Messgrenze, nicht über die
   Wirkung.** 0,3 pp Effekt gegen 4,5 pp Rauschboden — mit unserem n ist alles
   unter ~4 pp unsichtbar. Herausnehmen hieße, auf eine Nicht-Messung hin zu handeln.
2. **Kein Schaden nachweisbar.** Der ERÖFFNEN-Wächter hält. Diese Messung war
   Pflicht, weil genau hier der Ausführbarkeits-Hinweis eingebrochen ist (7.2).
3. **Sie schließen namentlich dokumentierte Lücken** (Zielgrößen 6.7, Punkt 4).

**Der ehrliche Gegenpunkt:** beide A-Arme lagen konsistent ~3 pp unter B. Bei
n = 67/69 nicht von Rauschen zu trennen — aber es ist die Richtung, vor der der
Systemgüte-Fakt in seinem eigenen Docstring warnt.

### 7.4b Ausstiegsverfahren für einen Fakt — vierstufig, mit Begründungspflicht

**Warum kein einfacher Schwellwert.** Ein hartes „unter X fliegt raus" ist derselbe
Konstruktionsfehler wie ein hartes Gate: es entscheidet ohne Ursachenprüfung. Eine
gesunkene ERÖFFNEN-Quote kann vom Fakt kommen — oder vom Regime, von einem
Provider-Drift wie am 31.07., von einer anderen Änderung im selben Zeitraum. Wer
beim ersten Unterschreiten entfernt, hat gute Chancen, das Falsche zu entfernen und
den echten Grund nie zu finden. **Die Schwelle löst deshalb eine Prüfung aus, keine
Entfernung.**

Das Verfahren gilt für **jeden** Fakt, nicht nur für `systemguete`.

#### Stufe 0 — laufende Beobachtung

| | |
|---|---|
| **Messgröße** | ERÖFFNEN-Quote der Signale, deren `facts_json` den Block enthält |
| **Datenquelle** | `hebel_faktensaetze.bloecke_je_tag` im Notebook-Export (seit 06.08., zählt über alle Zeilen des Fensters) |
| **Vergleichsbasis** | 92,1 / 92,5 / 95,7 % aus dem Dreiarm-Test |
| **Rauschboden** | ~4,5 pp — alles darunter ist nicht interpretierbar |

#### Stufe 1 — Auslöser (löst Prüfpflicht aus, nicht Entfernung)

Die Quote liegt über **≥ 60 aufgelöste Signale** unter **85 %**.

*Warum 85 %:* gut zwei Rauschbreiten unter der Basis — ein Wert, den zufällige
Schwankung nicht erzeugt. Die eigentliche Gefahr ist ohnehin kein 3-pp-Abrieb,
sondern der Zusammenbruch, den der Ausführbarkeits-Hinweis gezeigt hat
(93 % → 3 %); den fängt diese Schwelle sicher.

*Warum 60:* darunter ist der Unterschied zum Rauschboden nicht auflösbar. Bei der
aktuellen Rate frühestens **Ende August 2026**.

#### Stufe 2 — Ursachenprüfung, drei Alternativen sind auszuschließen

**Bevor** über die Entfernung entschieden wird, ist zu belegen, dass es am Fakt
liegt und nicht an:

1. **Provider-Drift** — Replay eingefrorener Faktensätze gegen den aktuellen
   Endpunkt. Das Werkzeug existiert (`kanarienvogel.py`, gebaut und getestet). Der
   31.07. ist der Präzedenzfall: dort lag es am Anbieter, nicht am Code.
2. **Regime** — die Quote getrennt je Regime auswerten. Ein Regimewechsel
   verschiebt sie unabhängig vom Faktensatz.
3. **Andere Änderung im selben Fenster** — Deploy-Liste des Zeitraums gegen die
   Bruchstelle halten. Genau dieser Schritt hat am 05.08. die Datierung des
   Einbruchs vom 31.07. auf den 29.07. korrigiert.

**Erst wenn alle drei ausgeschlossen sind**, ist der Fakt der plausible Grund.

#### Stufe 3 — Entscheidung mit schriftlicher Begründung

Die Entfernung ist eine Regeländerung und wird wie eine behandelt: Eintrag im
`Regelwerk_Entscheidungslog.md` mit Zahl, ausgeschlossenen Alternativen und
**Revisit-Bedingung**. Eine Entfernung ohne Begründung ist so wenig zulässig wie
eine Einführung ohne Begründung.

Bei einem Teilbefund gilt die **kleinste wirksame Änderung**: `systemguete` ist der
Block mit der Warnung, `kosten` und `ausstiegsregel` tragen sie nicht. Es wird der
verdächtige Block entfernt, nicht die Gruppe.

#### Stufe 4 — Rücknahme nach dem Nur-Long-Muster

1. Block aus `build_hebel_facts()` entfernen, Regel 31 auf den Ausstiegsteil kürzen
2. **Nachtrag an der Codestelle** — „HIER STAND …, BEWUSST ENTFERNT" mit Grund und
   Messwert, wie beim Nur-Long-Veto. Verhindert versehentliche Wiederkehr.
3. Katalogeintrag in 4.3 auf *entfernt* mit Datum
4. Wirkung der Entfernung **messen** — sonst ist unbekannt, ob sie geholfen hat

#### Was ausdrücklich KEIN Ausstiegsgrund ist

- **Eine weiterhin negative Systemgüte.** Der Block soll die Zahl melden, nicht sie
  verbessern. Wer ihn daran misst, misst das System und nicht den Block.
- **Ein weiterhin fehlender Wirkungsnachweis.** „Nicht nachweisbar" bei 0,3 pp
  gegen 4,5 pp Rauschboden ist eine Aussage über die Messgrenze. Sonst wäre die
  Entfernung genauso unbegründet wie die Einführung es wäre.
- **Ein Abrieb innerhalb des Rauschbodens** (< 4,5 pp), egal wie konsistent die
  Richtung aussieht. Genau diese Konsistenz erzeugen kleine Stichproben zuverlässig
  — siehe 7.6.

### 7.5 Verifikationsstand (Stand 2026-08-06)

| Was | Stand |
|---|---|
| Bauen die drei Fakten korrekte Werte? | **verifiziert**, isoliert ausgeführt, Zahlen nachrechenbar, Quellen benannt |
| Greift `systemguete` in allen Tiers? | **Nein, nur Hebel** (n = 124). Krypto 19, Aktien/ETF/Rohstoffe ≈ 0 → Fakt fällt still weg. So gewollt. |
| Kommen sie im **Produktivlauf** an? | **NOCH OFFEN.** Der letzte Export (05.08. 19:54) ist älter als die Commits (20:33 / 21:34); 0 von 176 Faktensätzen enthalten die neuen Blöcke. **Prüfpunkt für den nächsten Export.** |

### 7.5b Was die Verifikation am 06.08. zusätzlich ergab

Die Ankunftsprüfung lief zunächst **ins Leere, und zwar aus einem Messfehler, nicht
aus einem Verdrahtungsfehler**: `_hebel_faktensaetze()` hatte das Fenster fest auf
`2026-07-26`..`2026-08-05` verdrahtet — das Fenster des Regel-28-Tests. Die drei
Blöcke kamen am Abend des 05.08.; der Export konnte sie strukturell nicht enthalten.
0 von 177 sah nach einem defekten Fakt aus und war ein totes Fenster.

**Behoben:** rollierendes Fenster (14 Tage) plus ein neuer Block
`bloecke_je_tag`, der je Tag zählt, welche Fakt-Blöcke tatsächlich im `facts_json`
standen — über **alle** Zeilen des Fensters, nicht nur über die geschichtete
Stichprobe. Damit ist die Ankunftsfrage für jede künftige Fakten-Änderung ohne
Umweg beantwortbar.

> **Lehre, die über diesen Fall hinausgeht:** ein Analyse-Export, der für EINE
> Fragestellung gebaut wurde, verfällt still. Wer ihn danach zur Verifikation
> benutzt, misst das Fenster statt der Sache.

### 7.6 Die übergreifende Lehre

Zweimal unabhängig belegt: **kleine Stichproben erzeugen zuverlässig Scheinbefunde
in der erwarteten Richtung.** Beim Regel-Ablationstest lagen die Einzeleffekte bei
12 Ankern bei +0,281 und +0,182, bei 28 Ankern bei +0,014 und −0,013. Hier:
−0,734 bei 12 Fällen, −0,334 bei 24. **Vielversprechende Zwischenstände immer
aufstocken, bevor berichtet wird.**

---

## 8. Gesamtaufnahme: was das LLM heute NICHT sieht (Stand 2026-08-06)

*Nutzer-Vorgabe 06.08.: „prüfe vorher ob dem LLM neben den genannten Fakten weitere
fehlen welche rein sollten aber noch nicht sind — also als Gesamtkapitel."*
Abschnitt 7 behandelt die drei am 05.08. gebauten Fakten. Dieses Kapitel ist die
vollständige Liste dessen, was darüber hinaus fehlt.

### 8.1 Wie die Liste entstanden ist

Nicht durch Nachdenken, sondern durch **Differenzbildung**: alles, was das System
deterministisch berechnet und für wissenswert hält (die 48 Blöcke des
Notebook-Exports plus die Rechenfunktionen in `backward_tracking.py`), gegen die
**20 Fakt-Blöcke**, die `build_hebel_facts()` tatsächlich liefert.

Der Hebel-Faktensatz enthält heute: `antizyklisch` · `asset` · `ausstiegsregel` ·
`btc_relativwert` · `disclaimers` · `hebel_kontext` · `historische_erfolgsquote` ·
`historischer_makro_vergleich` · `kosten` · `liquiditaetszonen` · `markt_kontext` ·
`optionsmarkt` · `position_aktuell` · `preis` · `regime` · `regime_profil` ·
`signal_stabilitaet` · `systemguete` · `technische_analyse` · `trigger`.

Jeder Kandidat wurde durch das **3+1-Fragen-Raster** aus Abschnitt 1 geschickt.

### 8.2 Kategorie A — berechnet, aber nicht weitergereicht

Das sind die billigsten Fälle: die Zahl existiert, es fehlt nur die Verdrahtung.

| # | Was fehlt | Datenlage | Raster-Urteil |
|---|---|---|---|
| **A1** | **CRV-Erfolgsbänder für Hebel** | gemessen und exportiert (`crv_breakeven_baender.hebel_h7/h14`), mit Basislinie, KI und `belastbar`-Flag | **Frage 2 — gehört ans LLM.** Präzedenzfall existiert: Spot hat das seit 03.08. als Regel 36 |
| **A2** | **Eigene HALTEN-Bilanz** | `selbst_gewaehltes_halten_performance`, Hebel n=12, Trefferquote 8,3 %, ⌀ −0,754 R | Frage 2, aber **Reihenfolge beachten** (8.5) |
| **A3** | **Konfidenz-Kalibrierungsversatz** | `konfidenz_kalibrierung`: vorhergesagt 77,5 % → tatsächlich 33,3 % (Δ 44,2 pp); niedrig 48,3 % → 19,4 % (Δ 28,9 pp) | Frage 2 mit Vorbehalt (8.5) |
| **A4** | **Veto-Schatten je Grund** | `crv_unter_minimum`: 274 aufgelöst, 43,8 % Trefferquote, +0,054 R | **Nicht empfohlen** (8.5) |
| **A5** | **Datenqualität des eigenen Faktensatzes** | `ohlc_aktualitaet_je_symbol`, `api_health` (27 Quellen), Staleness je Indikator | Frage 2, geringer erwarteter Effekt |

**A1 ist die klarste Lücke des ganzen Kapitels.** Der Hebel-Analyst *setzt* das CRV
und kennt dazu nur die Mindestgrenze aus Regel 5 — keine gemessene Einordnung. Der
Spot-Analyst, dessen Datenbasis mit n=19 ausgewerteten Trades weit dünner ist,
bekommt seit dem 03.08. die vollen Bänder als Regel 36. **Die Pipeline mit den
belastbaren Daten hat die schwächere Regel.**

Die gemessenen Hebel-Bänder (h7, n=136, nur ERÖFFNEN):

| CRV-Band | n | Ziel erreicht | Basislinie | **Abstand** | EW | belastbar |
|---|---|---|---|---|---|---|
| 2,0–2,5 | 79 | 24,0 % | 13,1 % | +10,9 pp | −0,092 R | nein |
| **2,5–3,0** | 34 | 43,1 % | 8,6 % | **+34,5 pp** | **+0,571 R** | **ja** |
| 3,0–4,0 | 33 | 20,5 % | 7,7 % | +12,7 pp | −0,009 R | nein |
| ≥ 4,0 | 26 | 5,1 % | 3,1 % | +2,1 pp | −0,081 R | nein |

> **WARNUNG — hier lauert ein bereits einmal widerrufener Befund.** Die absolute
> Quote im Band ≥ 4,0 bricht auf 5,1 % ein, **aber die Basislinie bricht
> mit** (3,1 %). Der Abstand bleibt positiv. Das ist Horizont-Trunkierung, kein
> Qualitätsverlust — genau der Artefakt, der am 03.08. als „CRV ≥ 4,0 ist das
> schlechteste Band" gemeldet und widerrufen wurde. **Nur
> `abstand_zur_basislinie_pp` darf in einen Fakt, absolute Quoten nie.**

#### 8.2b Der „Sprung bei CRV 4,0" — gegengeprüft und aufgelöst (06.08.)

**Nutzer-Einwand:** der Sprung sei ihm „sehr oft vorgekommen und war irgendwie
bewiesen". Berechtigt — und meine erste Erklärung war **falsch adressiert**.
Nachgerechnet in `pruefe_sprung_bei_crv4.py` an 871 Signalen (gegen 491 der
Originalmessung).

**Zuerst die Korrektur an mir selbst:** ich hatte den Sprung pauschal als
Trunkierungs-Artefakt bezeichnet. Das gilt nur für das Maß *„Ziel erreicht"*.
Regel 36 nutzte aber *„MFE ≥ 1R"*, und auf dieses Maß wirkt Trunkierung
**nicht** — die Schwelle 1R ist fest, unabhängig vom CRV.

**Was stattdessen dahintersteckt.** CRV = Zielabstand ÷ Stopabstand. Ein hohes
CRV entsteht auch durch einen **engen Stop** — und bei engem Stop ist 1R eine
winzige Kursbewegung, „MFE ≥ 1R" wird also mechanisch leicht.

| CRV-Band | MFE ≥ 1R | Median-Stop |
|---|---|---|
| 2,0–2,5 | 27,1 % | 6,25 % |
| 2,5–3,0 | 37,3 % | 5,62 % |
| 3,0–4,0 | 46,7 % | 4,22 % |
| ≥ 4,0 | 63,9 % | **2,56 %** |

**Es gibt gar keinen Sprung** — in der größeren Stichprobe steigt es glatt, und
der Stop-Abstand fällt spiegelbildlich. **Der Stop-Abstand allein trennt
schärfer als das CRV** (54,0 / 25,1 / 15,8 % über die Stop-Terzile, Intervalle
getrennt). Kontrolliert man ihn, schrumpft der CRV-Effekt von +36,8 auf
+13,4 pp, und alle Intervalle überlappen. **Das CRV war hier ein Stellvertreter
für die Stop-Enge.**

**Und dann kippt es — der eigentliche Punkt** (Nutzer-Formulierung: „es geht
nicht um den Wert, sondern wann dieser Wert alles zum Kippen bringt"):

| Stop-Abstand | n | MFE ≥ 1R | Ergebnis (EW) |
|---|---|---|---|
| **0–2 %** | 47 | **55,3 %** | **−1,043 R** |
| 2–3 % | 53 | 37,7 % | −0,479 R |
| **3–5 %** | 117 | 64,1 % | **+0,340 R** |
| 5–8 % | 136 | 36,0 % | −0,438 R |

Unter 2 % Stop-Abstand meldet die Kennzahl 55 % Erfolg, während der
Erwartungswert bei **−1,04 R** liegt: praktisch jeder Trade wird voll
ausgestoppt. Der Kurs tippt 1R an, weil 1R dort fast nichts ist, und nimmt
danach den Stop mit.

> **STEHENDE LEHRE:** „MFE ≥ 1R" taugt **nicht** als Erfolgsmaß für Fragen, bei
> denen der Stop-Abstand mitvariiert — es belohnt genau das, was das Ergebnis
> zerstört. Für solche Fragen „Ziel erreicht" gegen eine Basislinie mit
> **demselben Stop und demselben Horizont** verwenden; nur dann tragen beide
> Seiten denselben Effekt.

**Folge für die Praxis:** die Warnung in den neuen Regeln („zieh niemals den
Stop enger, um in ein besseres Band zu rutschen") ist damit nicht mehr nur
vorsichtig, sondern **an Zahlen belegt**.

#### 8.2c Der Widerspruch 3–5 % gegen 5–8 % — aufgelöst (06.08.)

**Er existiert nicht.** Beide Ausgangszahlen waren Survivorship-Artefakte, und
zwar aus demselben Grund: sie werteten nur **aufgelöste** Fälle aus. Ob ein
Signal auflöst, hängt aber vom **Stop-Abstand** ab — genau der Variablen, um die
es ging. Enge Stops lösen fast immer auf und landen mit −1 R in der Stichprobe;
weite bleiben offen und fallen heraus, auch die, die später gewonnen hätten.
**Die Stichprobenauswahl hing am Messgegenstand.**

Nachgemessen in `messe_stop_abstand_baender.py`: kein Auflösungs-Filter, jedes
Signal mit Zonen neu gegen die Preisreihe simuliert, Basislinie je Band mit
demselben Stop und CRV, Block-Bootstrap über Symbole.

| Stop-Band | n | EW | Bootstrap-KI | Abstand zur Basislinie |
|---|---|---|---|---|
| **0–2 %** | 26 | −0,770 | **[−1,124; −0,500]** | **−0,526** |
| 2–3 % | 37 | +0,182 | [−0,604; +1,801] | +0,421 |
| 3–5 % | 98 | +0,433 | [−0,185; +0,848] | +0,668 |
| 5–8 % | 147 | −0,036 | [−0,359; +0,364] | +0,142 |
| 8–12 % | 113 | −0,047 | [−0,319; +0,163] | +0,082 |
| > 12 % | 72 | +0,224 | [−0,285; +0,521] | +0,317 |

**Der einzige belastbare Befund: Stops unter 2 % sind zerstörerisch.** Als
einziges Band schließt das Intervall die Null aus und liegt klar unter der
Basislinie. Bei H14 bestätigt (−1,088, [−1,198; −1,000]), bei LONG allein
ebenfalls (−1,061). **Alles andere ist nicht trennbar** — jedes übrige Intervall
enthält die Null, 3–5 % überlappt 5–8 % vollständig.

Damit fallen beide Behauptungen: „unter 5 % schlecht" (01.08.) ist zu grob, weil
es das schlechteste Band mit den beiden besten Punktschätzern zusammenwirft;
„5–8 % negativ" (06.08.) hält survivorship-bereinigt nicht.

**Was daraus für Regeln folgt — und was nicht.** Die Daten stützen eine
**Untergrenze**, keinen Optimalwert. Ein Richtwert „Stop möglichst bei X %" wäre
durch nichts gedeckt; ein Hinweis „unter 2 % ist der Trade strukturell nicht
überlebensfähig" ist es. Das deckt sich mit dem Kostenfakt (enge Stops sind
doppelt teuer) und mit der Beobachtung aus 8.2b, dass genau dort MFE und
Ergebnis auseinanderlaufen.

**Einschränkung, die dazugehört:** 533 Signale fielen bei H7 aus, weil ihre
Preisreihe den Horizont nicht abdeckt. Das ist ein reiner Zeiteffekt (junge
Signale haben noch keine 7 Tage Zukunft) und damit **nicht** stop-abhängig — die
Bandvergleiche bleiben davon unberührt. SHORT ist je Band zu dünn (n = 2–17);
die Aussage trägt LONG.

Der belastbare Kern ist damit schmal, aber real: **2,5–3,0 ist das einzige Band mit
belastbarem Vorsprung.** Ein Fakt darf genau das sagen — und muss die drei anderen
Bänder als *nicht belastbar* kennzeichnen, statt eine Rangfolge zu suggerieren.

### 8.3 Kategorie B — strukturell nicht vom Modell herleitbar

Der stärkste Grund für einen Fakt: das Modell kann es **prinzipiell** nicht selbst
wissen, egal wie gut es analysiert.

| # | Was fehlt | Warum unherleitbar | Urteil |
|---|---|---|---|
| **B1** | **Relative Rangposition im Kandidatenfeld** | Das Modell sieht immer genau einen Kandidaten, nie das Feld. Ob dieser der beste von 40 oder der schlechteste ist, steht in keinem Fakt | **zurückgestellt** — der Rang käme aus dem Screening-Score, und der diskriminiert gemessen nicht (03.08.). Ein Rang aus einer nicht trennenden Größe ist Scheinpräzision |
| **B2** | **Klumpenrisiko im offenen Portfolio** | `position_aktuell` betrifft nur das eine Symbol. Vier offene Positionen in derselben Wette sind ein Risiko, das kein Einzelsignal zeigt | **offen — Achsenfrage, kein Blocker** (8.5) |
| **B3** | **Portfolio-Rückschlag Z-3** | Der Portfoliozustand steht in keinem Fakt (aktuell 16,84 % bei 15 % Schwelle, ausgelöst) | **bewusst NICHT** — Raster-Frage 1 bejaht, gehört ins Gate |

### 8.4 Kategorie C — fehlt als FELD, nicht als Weitergabe

| # | Was fehlt | Stand |
|---|---|---|
| **C1** | **Zieldauer / Haltedauer** | Es gibt keine. `halte_kriterium_bucket` ist eine Ablauffrist, `mindestziel_zeitraum_tage_geschaetzt` eine Volatilitätsrechnung — beide sind keine Strategieangabe und widersprechen einander. Gemessene Auflösung 2,6 T, Praxis 0,3 T |

**Das ist kein Prompt-Thema.** Solange kein Feld eine Zieldauer trägt, bleibt jede
Prompt-Ergänzung folgenlos — sie hätte nichts, worauf sie sich bezieht. Der
Konstruktionsfehler ist zuerst zu beheben; er ist seit dem 04.08. dokumentiert und
blockiert außerdem die Auswertung von `halte_kriterium` (05.08.).

### 8.5 Kategorie D — bewusst NICHT, mit Revisit-Bedingung

| Was | Warum nicht | Revisit, wenn |
|---|---|---|
| **Ausführbarkeit / `nur_long`** | **Gemessen:** ERÖFFNEN-Quote bricht von 93 % auf 3 % ein. Das Modell schlägt dann gar nichts mehr vor, statt LONG-Alternativen zu suchen | nie in dieser Form. Allenfalls als neutral formulierter Portfoliokontext, dann mit Dreiarm-Test |
| **Z-3 Portfolio-Drawdown** | Raster-Frage 1 bejaht: „Rückschlag über Schwelle → Risiko reduzieren" ist kontextunabhängig. Ein Fakt wäre die falsche Ebene | Z-3 je als graduelle statt binärer Größe gebraucht wird |
| **Veto-Schatten je Grund (A4)** | Nächster Verwandter des Ausführbarkeits-Hinweises: es teilt dem Modell mit, welche seiner Vorschläge verworfen werden. Zudem ist die Zahl fragil — beim CRV-Veto tragen 5 Fälle 221 % des Mittelwerts, `vorzeichen_kippt = true` | die Konzentration behoben ist UND eine neutrale Formulierung ohne Ausführbarkeits-Bezug vorliegt |
| **`score_gesamt`** | Liegt heute als **nackte Zahl ohne Regel** im Faktensatz — die schlechteste aller Varianten: kann ankern, ist nicht deutbar. Beschluss vom 03.08.: **entfernen**, nicht ergänzen | der Score nachweislich diskriminiert |
| **Eigene HALTEN-Bilanz (A2)** | Kein Einwand in der Sache — aber **dieselbe Familie wie `systemguete`**, das gerade unter Beobachtung steht (7.4b). Zwei Selbstbewertungs-Fakten gleichzeitig einzuführen macht einen negativen Befund unzuordenbar | das Ausstiegsverfahren zu `systemguete` abgeschlossen ist (frühestens Ende August) |
| **Konfidenz-Versatz (A3)** | Die Konfidenz **diskriminiert nicht** (05.08.). Ein Kalibrierungshinweis verschöbe nur das Niveau — und das Niveau ist genau das, worauf die Regime-Schwellen R-5.10 rechnen. Nebenwirkung auf das Gate, ohne Gewinn an Trennschärfe | die Konfidenz je Trennschärfe zeigt |
| **Klumpenrisiko (B2)** | **Offen, zur Klärung mit dem Nutzer** — nicht abgelehnt. Meine erste Einschätzung („`hauptgruppe` nur bei 13 von 57 befüllt, also blockiert") war zu eng gedacht: `assetklasse` und `rolle` sind **57 von 57** befüllt, und die Bewertung erfolgt ohnehin je Gruppe getrennt. Die offene Frage ist damit nicht *ob genug Daten da sind*, sondern **welche Gruppierungsachse** die richtige ist — Assetklasse, Rolle, Sektor oder eine korrelationsbasierte | Nutzer-Entscheidung zur Achse (Hinweis 06.08.: „die Kategorie-Thematik halte ich für nicht so problematisch — die Bewertung muss ohnehin je Gruppe gesondert erfolgen") |

### 8.6 Priorisierung

**Nur ein Kandidat ist heute umsetzungsreif: A1 (CRV-Erfolgsbänder für Hebel).**
Daten gemessen und exportiert, Präzedenzfall auf Spot vorhanden, betrifft eine
Größe, die das Modell selbst setzt, und schließt eine dokumentierte
Pipeline-Asymmetrie. Aufwand: Verdrahtung plus eine Prompt-Regel.

Alles andere ist **bewusst nachgelagert**, und zwar nicht aus Aufwandsgründen:

1. **A2 und A3 warten auf das Ausstiegsverfahren zu `systemguete`.** Solange
   offen ist, ob ein Selbstbewertungs-Fakt die ERÖFFNEN-Quote drückt, wäre ein
   zweiter davon methodisch fahrlässig — ein negativer Befund ließe sich keinem
   der beiden zuordnen.
2. **C1 (Zieldauer) ist Datenarbeit**, keine Prompt-Arbeit — solange kein Feld
   eine Zieldauer trägt, hat jede Prompt-Regel nichts, worauf sie sich bezieht.
   **B2 (Klumpenrisiko) ist eine offene Achsenfrage** und wartet auf eine
   Nutzer-Entscheidung, nicht auf Daten.
3. **A4 und B1 sind begründet abgelehnt**, nicht vergessen — beide mit
   Revisit-Bedingung oben.

> **Methodische Vorgabe für A1, aus 7.3 gelernt:** einzelne Fakten sind bei dieser
> Effektgröße nicht messbar (der Kosten-Fakt allein hätte n=618 gebraucht,
> kombiniert waren es 16). A1 wird deshalb **nicht einzeln** getestet, sondern
> gegen den heutigen Stand als Ganzes — Dreiarm-Design mit Rauschboden, gepaart,
> ERÖFFNEN-Quote als Pflicht-Wächter.


---

## 9. Nachweisverfahren für neue Fakten — der Plan vom 2026-08-09

**Anlass.** Nutzer-Vorgabe: *„wichtig wäre nur dass du als Fachexperte prüfst
wie wir die neuen Informationen sauber integrieren und einen ‚Nachweis'
erhalten ob es eine Verbesserung oder Verschlechterung ist — einfach nur
Einbauen hast du selbst eigentlich abgelehnt."*

### Der methodische Mangel, der diesen Plan nötig macht

Das bestehende Drei-Arm-Verfahren (Abschnitt 7) beweist, **dass** ein Fakt das
Verhalten ändert. Es kann nicht beweisen, **dass die Änderung eine Verbesserung
ist.** Gemessen wurde am 05./06.08. die *Wirkung auf den Stop-Abstand* — eine
Stellgröße, kein Ergebnis. Der Befund lautete „das Modell wählt engere Stops";
ob engere Stops hier besser sind, sagt die Messung nicht. Der vorhandene
Backtest (`backtest_llm1_historisch.py`) misst die Zonenqualität und ist auf der
ERÖFFNEN/HALTEN-Achse bei 94–100 % gesättigt.

**Es fehlt der Bewerter, der aus einer geänderten Entscheidung ein Ergebnis
macht.** Ohne ihn bleibt jede Fakt-Einführung „einbauen und hoffen".

Zweiter Engpass, der daran hängt: das nötige n von **212** (aus dem
Kosten-/Ausstiegs-Test) ist mit aufgelösten Signalen unerreichbar — 5,2 %
Auflösungsquote, ~1,2/Tag. Ein Bewerter, der auch unaufgelöste Signale gegen den
echten Kursverlauf auswertet, hebt die Stichprobe von 92 auf potenziell ~1.400.
Er ist damit nicht nur der Nachweis, sondern die einzige Möglichkeit, überhaupt
genug Fälle zu bekommen.

### Stufe 0 — Gegenprüfung der einen dokumentierten Widersprüchlichkeit

**ERLEDIGT (2026-08-09) — es gab keinen Widerspruch mehr.** Die Formulierung
oben beschrieb einen Stand, der seit dem 03.08. überholt war.

Der Docstring von `basislinie_erwartungswert()` löst ihn selbst auf, Abschnitt
„KORREKTUR DER KORREKTUR": die **−0,11 bis −0,26 R** stammen aus der Basislinie
von `analyse_crv_gate_survivorship.py`, die schon immer aus dem *Signalfenster*
zog; die **+0,081 R** waren der Wert aus der *vollen Historie*. Beide Zahlen
sind richtig, sie messen verschiedene Fenster. Seit
`_BASISLINIE_NUR_SIGNALFENSTER = True` sind beide Rechnungen deckungsgleich.

Gegengeprüft am Export vom 09.08.:

| Gruppe | Expectancy | Basislinie | Signalbeitrag |
|---|---|---|---|
| hebel/real | −0,149 R | **−0,094 R** (n=958) | **−0,055 R** |
| krypto/real | −0,159 R | −0,298 R (n=679) | +0,139 R |

Kein +0,081 R, und der Signalbeitrag liegt bei −0,055 R statt −0,379 R. **Die
Sperre auf dem Signalbeitrag ist damit gegenstandslos.**

Was echt offen bleibt, ist ein *anderer* Punkt, den derselbe Docstring
ausdrücklich als „unverändert offen" führt: die **Auflösungs-Asymmetrie**.
Auch sie ist inzwischen auf der Signalseite adressiert —
`_SYSTEMGUETE_MARK_TO_MARKET` bewertet unaufgelöste Signale zum Schlusskurs,
sodass beide Seiten des Vergleichs denselben Fall gleich behandeln.

> **Lehre:** dieser Plan hätte mit einer Auswertung begonnen, deren Ergebnis
> seit sechs Tagen im Code stand. Die stehende Vorgabe *„vor jedem Eingriff die
> interne Doku prüfen"* gilt auch für den eigenen Plan.

### Stufe 1 — Der Pfad-Bewerter, validiert

**ERLEDIGT (2026-08-09) — der Bewerter existierte bereits und ist jetzt
geprüft.**

`simuliere_signal()` (`agent/krypto/backward_tracking.py`) leistet genau das:
OHLC-Verlauf + Entry/Stop/Ziel → Ergebnis in R, mit identischer Abbruch- und
Fill-Logik wie das Backward-Tracking. Er war zudem **nicht nur ein
Analysewerkzeug, sondern lief bereits produktiv** — über
`_SYSTEMGUETE_MARK_TO_MARKET` speist er die ausgewiesene Systemgüte
(50 Fälle über beide Tabellen, davon 39 bei hebel/real). Geprüft war er nie.

> **Abnahmekriterium: er muss die bekannten Ausgänge reproduzieren.**
> Reproduziert er sie nicht, ist er für die anderen ~1.400 nicht
> vertrauenswürdig.

**Ergebnis: 97 von 100 auswertbaren Fällen (97,0 %) — auf dichten Kursreihen
82 von 82 (100,0 %).** Der gesamte Fehler liegt in der dünnen Population
(15 von 18). Negativkontrolle 47,1 %. Werkzeug, Kontrollen und die zwei Lehren
aus dem Lauf stehen in `Test_und_Verifikationsmethodik.md` 2.13
(`pruefe_pfad_bewerter.py`).

### Stufe 2 — Stichprobe verbreitern

Der validierte Bewerter über die unaufgelösten Signale. Erst danach ist n=212
erreichbar. **Offene Vorbedingung, gehört in jedes spätere Ergebnis:** 30,2 %
der Hebel-Signale haben weder Entry noch Stop hinterlegt. Die Lücke ist nicht
zufällig verteilt.

**Korrektur der zweiten Vorbedingung (2026-08-09, gemessen).** Hier stand
bisher, 19,2 % der Hebel-Signale trügen Symbole *„ohne jede Kursreihe"* —
CANTON, KAIA, KAITO, SUPRA, XNO. Das stimmt nicht mehr: diese Symbole **haben**
eine Kursreihe, sie ist nur **dünn** — je 23 Punkte im Abstand von rund vier
Tagen. Insgesamt neun Symbole (zusätzlich BRETT, EURCV, IO, VSN).

Der Unterschied ist nicht kosmetisch. „Keine Reihe" heißt *nicht bewertbar*;
„dünne Reihe" heißt *bewertbar, aber mit messbar schlechterer Reproduktion*
(83,3 % gegen 100,0 %). Die betroffenen Fälle bleiben in der Stichprobe und
tragen ihre Kennzeichnung mit — **Reichweite: 16,8 % der unaufgelösten
Hebel-Signale, 2,6 % bei Spot.**

**Folge für einen bestehenden Befund:** die KAIA-Diagnose (*„der Trigger feuert,
der Kurs reagiert nie"*, Median-MFE −0,01 R bei 11 Signalen) ruht auf einer
Vier-Tage-Balken-Reihe. Ein Median-MFE unterschätzt auf solchen Balken die
tatsächliche Bewegung systematisch. Der Befund kippt dadurch nicht, ist aber
schwächer belegt als bisher angenommen — bei der Wiedervorlage mitzuprüfen.

### Stufe 3 — Nachweisrahmen je Fakt

Bestehendes Drei-Arm-Design (A1/A2 identisch + B, gepaart auf denselben
Faktensätzen) **plus** Bewertung beider Arme durch den Bewerter aus Stufe 1.
Entscheidungsregel und nötiges n werden **vor** dem Lauf festgeschrieben.
Rauschboden ~4,5 pp ist die Messgrenze.

**Betriebsdefinition von „Tendenz" (Nutzer-Entscheidung 09.08.):** Ein Fakt darf
auf Tendenz eingeführt werden, ohne vollen Nachweis — der aktuelle Zustand mit
null Signalen ist nicht tragbar, und das Ausstiegsverfahren führt „fehlender
Wirkungsnachweis" ohnehin als **keinen** Rücknahmegrund.

> Eine Tendenz zählt aber nur, wenn sie beim **Vergrößern der Stichprobe hält
> oder wächst — nicht wenn sie schrumpft.**

Begründung aus eigenen Daten, zweimal unabhängig: Regel-Ablation +0,281/+0,182
bei 12 Ankern → +0,014/−0,013 bei 28. Kosten-Fakt −0,734 bei 12 → −0,334 bei 24.
Beide schrumpften. Die Rücknahmebedingung wird **vor** der Einführung
schriftlich festgelegt.

### Stufe 4 — Fakten, einer nach dem anderen

**Erster Kandidat: die Hebel-CRV-Bänder.** Begründung ist die in Abschnitt 8
gemessene Pipeline-Asymmetrie — der Hebel-Analyst *setzt* das CRV und kennt nur
die Mindestgrenze aus Regel 5, während Spot seit 03.08. die vollen Bänder hat,
bei n=19 gegen n=124 Datenbasis. Bestes Band 2,5–3,0 mit +34,5 pp über
Basislinie und EW +0,571 R.

**Falle beim Bauen:** nur `abstand_zur_basislinie_pp` darf in den Fakt — die
absolute Quote im Band ≥ 4,0 ist der am 03.08. widerrufene
Trunkierungs-Artefakt.

**Sequenzbedingung:** eigene HALTEN-Bilanz und Konfidenz-Versatz **nicht
parallel** — dieselbe Familie wie `systemguete`, das unter Beobachtung steht;
zwei Selbstbewertungs-Fakten gleichzeitig machen einen negativen Befund
unzuordenbar.

### Stufe 4 — der erste Lauf, vollständig festgelegt (Stand 2026-08-09)

**Der in Stufe 4 genannte Erstkandidat ist hinfällig.** Die Hebel-CRV-Bänder
sind **seit dem 06.08. live** (`hebel_pipeline.py:309`), der Fakt kommt an: vier
Bänder, Grundlage n=197, ein belastbares Band (CRV 2,5–3,0, +30,8 pp). Die
beschriebene Asymmetrie ist sogar **umgekehrt** — Spot bekommt heute *keinen*
Fakt, Hebel schon.

Messbar ist er trotzdem nicht, und der Grund gehört festgehalten:

| | |
|---|---|
| Faktensätze mit dem Fakt | 51 — alle ab dem Rollout-Tag 06.08. |
| Richtung | **51× SHORT, 0× LONG** |
| Folgetage im Kurs | Median 2, maximal 3 |
| bei Horizont ≥ 4 | **alle 51 zensiert** |

> Ein Fakt, der gerade erst ausgerollt wurde, kann per Konstruktion nur von den
> jüngsten Fällen getragen werden — und deren Ausgänge existieren noch nicht.
> Das ist dieselbe Falle wie „Fallauswahl schließt die Frage aus" (Methodik,
> Nachtrag 09.08., Punkt 4). **Wiedervorlage um den 20.08.**, dann haben die 51
> ihre 14 Tage.

#### Was stattdessen geprüft wird, und warum

**Erstkandidat: `liquiditaetszonen`.** Drei Gründe, in dieser Reihenfolge:

1. **Es gibt eine unabhängige Vorerwartung.** Stufe 2 dieses Fakts wurde am
   23.07. per Backtest verworfen (130 Ereignisse, p = 0,53). Meldet der Rahmen
   „im Rauschen", bestätigt das einen anders gewonnenen Befund — das ist die
   beste Kalibrierung, die ein Messverfahren bei seinem ersten Einsatz bekommen
   kann. Ein Verfahren zuerst dort einzusetzen, wo man die Antwort schon ahnt,
   prüft das Verfahren mit.
2. Sauber abgrenzbarer Block, in **100 %** der brauchbaren Fälle vorhanden.
3. Ein negativer Befund wäre handlungsrelevant: der Fakt steht in sechs Prompts.

**Zweitkandidat: `antizyklisch`** — der größte Block, und nach der
Schritt-7-Entscheidung („kein Rollout mangels Daten für die anderen Klassen")
ist offen, ob er wenigstens bei Krypto trägt.

#### Die Grundmenge, hart gefiltert

122 von 268 Faktensätzen decken bei **Horizont 7** die volle Beobachtungsdauer
ab; 104 LONG, 18 SHORT, 12 Symbole. Die übrigen 146 fallen wegen zu kurzer
Kurshistorie heraus — **vor** dem ersten Aufruf, nicht danach.

#### Die Entscheidungsregel steht vor dem Lauf fest

| Regel | Wert |
|---|---|
| ERÖFFNEN-Wächter (Vorrang vor allem) | Einbruch ≥ 10 pp ⇒ disqualifiziert |
| Mindestzahl gepaarter Fälle | 5 |
| Maßstab | CRV-Breakeven `1/(1+CRV)` |
| Nachweis | Bootstrap-Vertrauensbereich der gepaarten Differenz **ohne die Null** |
| „Tendenz" gilt nur | wenn sie beim Aufstocken hält oder wächst |

#### Hinweis: die Stichprobe überspannt zwei Vorschlagsregime (geprüft 09.08.)

    Zeitraum          ALLE Signale              nur ERÖFFNEN
    bis 30.07.        1011L/80S  ( 7 % SHORT)   119L/32S  (21 % SHORT)
    31.07.–04.08.      114L/294S (72 % SHORT)     7L/0S   ( 0 % SHORT)
    ab 05.08.           44L/362S (89 % SHORT)     2L/40S  (95 % SHORT)

Zwei getrennte Verschiebungen: am **31.07.** kippen die *Vorschläge* (SHORT von
7 % auf 72 %) — aber **293 von 294 fing das Nur-Long-Veto**, die Einstiege
blieben bei 0 % SHORT. Die *Einstiege* kippen erst am **05.08.**, und das ist
die dokumentierte Filterentfernung.

> **Für diesen Lauf heißt das:** der gepaarte Aufbau ist nicht betroffen — beide
> Arme sehen denselben Faktensatz, und die damalige `action` spielt keine Rolle.
> Die Faktensätze stammen aber aus zwei Vorschlagsregimen, und der 31.07. stellt
> 34,8 % davon.
>
> `werte_fakt_nachweis_neu_aus.py --ohne-tag 2026-07-31` beantwortet ohne einen
> einzigen neuen Aufruf, ob es darauf ankommt. **Das gehört vor jede
> Interpretation des Ergebnisses.**

Herleitung samt zweier eigener Messfehler auf dem Weg dorthin in der
Memory-Datei `project_richtungsbruch_31_07_unerklaert`.

#### Die Clusterung ist die härteste Einschränkung dieses Laufs

Methodik 2.5 ist hier bindend: *„Bei geclusterten Beobachtungen ist die EFFEKTIVE
Stichprobengröße die Anzahl distinkter Symbole, nicht die Roh-Zeilenzahl."*

| | |
|---|---|
| Roh-n | 122 Fälle |
| distinkte Symbole | **12** |
| größtes Symbol | LINK, 14,8 % — **unter** der 25-%-Grenze |
| Top-3 | 40,2 % |

Kriterium (b) ist erfüllt, Kriterium (a) — n ≥ 50 — auf Symbolebene **nicht**.

**Warum der Lauf trotzdem aussagekräftig ist, und wo seine Grenze liegt.** Der
Vergleich ist **gepaart**: beide Arme sehen denselben Faktensatz, dasselbe
Symbol, denselben Tag. Der Symbol-Effekt kürzt sich damit heraus — anders als
bei einem Querschnittsvergleich von Trefferquoten, für den 2.5 geschrieben
wurde. Was sich *nicht* herauskürzt, ist die Korrelation der Differenzen
innerhalb eines Symbols: achtzehn LINK-Fälle aus derselben Marktbewegung sind
keine achtzehn unabhängigen Beobachtungen.

Deshalb zieht das Vertrauensintervall **ganze Symbole statt einzelner Fälle**
(Cluster-Bootstrap, genau das „analog zu clustered standard errors", auf das
2.5 verweist). Das Intervall wird dadurch breiter — und das ist die ehrliche
Breite.

> **Was daraus folgt:** ein Befund aus diesem Lauf ist **hypothesengenerierend**,
> nicht operationalisierbar. Er darf keine Schwelle verschieben und kein Gate
> begründen. Für eine Einführung oder Rücknahme braucht es die Replikation auf
> einem anderen Zeitraum oder anderen Symbolen — 2.5 verlangt das ausdrücklich
> für informell nacheinander getestete Hypothesen.

#### Vier Gegenprüfungen, ohne die kein Ergebnis berichtet wird

1. **A/A′-Nullabgleich.** Zwei identische Arme liefern die Eigenstreuung. Ohne
   sie ist jede Zahl unbrauchbar.
2. **Gepaart je Fall, nicht über Mittelwerte.** Der erste Entwurf verglich zwei
   Einzelzahlen und produzierte im Trockenlauf einen **Fehlalarm**: das
   nachgebildete Modell hatte keine Fakt-Abhängigkeit, gemeldet wurde trotzdem
   „TENDENZ: verschlechtert" (−0,078 R gegen 0,067 R Rauschboden). Seit der
   Umstellung auf gepaarte Differenzen mit Bootstrap-Intervall lautet dasselbe
   Urteil korrekt **im Rauschen** (+0,014 R, [−0,088; +0,112], 48 Fälle).
3. **Trockenlauf mit nachgebildetem Modell vor jedem echten Lauf.** Er hat schon
   zwei eigene Fehler gefunden: den Fehlalarm oben und einen falschen Preis-
   schlüssel im Testmodell, der die bewertbare Menge von 97 auf 16 gedrückt und
   damit eine viel zu kleine Stichprobe vorgetäuscht hätte.
4. **Leerlauf-Wache.** Unter 30 brauchbaren Fällen wird **kein einziger Aufruf**
   abgesetzt.

#### Was gespeichert wird, damit nicht zweimal gemessen werden muss

* **Jede Rohantwort** landet im Protokoll. Eine Neuauswertung mit anderem
  Horizont, anderer Entscheidungsregel oder nach einem gefundenen
  Auswertungsfehler braucht **keinen neuen Aufruf**.
* **Die A-Arme sind fakt-unabhängig** und werden über mehrere geprüfte Fakten
  hinweg geteilt: k Fakten kosten `2 + k` Arme statt `3k`. Bei zwei Fakten sind
  das vier statt sechs Durchläufen.
* **Transportfehler** stehen in keinem Nenner und gelten bei der Wiederaufnahme
  nicht als erledigt — sonst zementiert der erste missglückte Lauf seine Lücken.

**Umfang des ersten Laufs:** 122 Fälle × 3 Arme = **366 Aufrufe**, bei Geminis
gemessenem Median von 5,5 s rund 35 Minuten seriell.

### Vorgeschaltet, weil billiger als alles andere

Bevor „null Signale" als Qualitätsproblem behandelt wird, muss die **mechanische
Ursache** ausgeschlossen sein: `llm_aufrufe_heute` im nächsten Export zeigt in
einer Zahl, ob überhaupt noch LLM-Aufrufe stattfinden. Finden keine statt, hilft
kein einziger neuer Fakt.

---

## 10. Der neue Faktensatz der Rollen-Ebene (Stand 2026-08-11)

*Kapitel 4 beschreibt, was die ALTE Pipeline liefert — rund 20 Blöcke aus 156
Knoten in einem Aufruf. Dieses Kapitel beschreibt, was die neue Rollen-Ebene
liefert. Beide existieren nebeneinander; die alte ist produktiv, die neue
geprüft, aber nicht verdrahtet.*

### 10.1 Der Grundsatz: Aussagen, keine Zahlenliste

Belegt (Recherche 10.08.): Tokenisierung zerlegt Zahlen in bedeutungslose
Fragmente; semantischer Inhalt ist der Leistungstreiber; Trader lesen
Marktstruktur, nicht nachlaufende Indikatoren. Statt

```
"abstand_in_atr": {"sma_200": -3.84}
```

liefert `agent/lagebeschreibung.py`

```
Der Kurs steht 3,8 Schwankungsbreiten unter dem 200-Tage-Schnitt.
```

### 10.2 Was Rolle BC sieht — sechs Blöcke, Bestand zuerst

| Block | Quelle | neu? |
|---|---|---|
| **Bestand** (investiert, Wert, G/V in EUR und %) | `holdings` + Preis | steht jetzt an **erster** Position |
| Marktstruktur (höhere/tiefere Hochs und Tiefs) | Williams-Fraktal, nur bestätigte Swings | **neu** |
| Bewegung 5/20/60 Tage | `closes` | **neu** |
| Niveaus: Widerstand/Unterstützung in ATR und EUR, mit Berührungszahl | geclusterte Swings, Mindestabstand 0,5 ATR | **neu** |
| **Umsatz** (relativ zum 20-Tage-Schnitt, Auf-/Abwärtsanteil, Stetigkeit) | `price_history_ohlc.volume` | **neu — lag ungenutzt** |
| Marktlage-Beurteilung von Rolle A | Rolle A | **neu** |

**Der Bestand zuerst ist kein Formatdetail.** Im KAS-Signal vom 15.07. stand
„−14,6 % auf der Position" in den *Risiken* und hat die Empfehlung nie erreicht;
das Modell kaufte in eine Verlustposition nach.

### 10.3 Was Rolle A sieht

Marktbreite (Anteil über 50-/200-Tage-Linie mit historischem Bezug). **Kein
einzelnes Asset** — damit kann sie nicht vom Einzelfall her rationalisieren.

### 10.4 Was bewusst NICHT übergeben wird

`historische_erfolgsquote` · `systemguete` · `signal_stabilitaet` ·
`konfidenz_kalibrierung` · `disclaimers` · `regime.boden_zielzone_*` ·
`strategien_aktiv` · `regime_profil.gewicht_*` · `kursverlauf[]` (90 Rohzahlen)

**Kein Block ist endgültig verworfen.** Die Begründungen stammen überwiegend aus
Messungen am ALTEN Aufbau; jeder ist **einzeln zuschaltbar**, und die Frage
gehört im neuen Aufbau neu gemessen. Details:
`Rollenkonzept_Entwurf_10_08.md` Abschnitt 4.

### 10.5 KEIN BETRAG für die Modelle

Weder Rolle A noch BC nennt eine Positionsgröße. Extern belegt: LLMs sind dort
am schwächsten, und das Praxismuster entkoppelt Richtungslogik von
quantitativer Größenbestimmung. Der Betrag folgt deterministisch aus der Zahl
**unabhängiger** Belege — 3+ → 500, 2 → 300, 1 → 100, 0 → keine Handlung. Eine
Setzung, als solche gekennzeichnet.

### 10.6 Der bekannte Defekt (11.08., noch nicht behoben)

`_struktur()` vergleicht die letzten **zwei** Swing-Punkte und nennt das
Ergebnis „ein intakter Abwärtstrend". Bei einer Korrektur innerhalb eines
Aufwärtstrends ist das falsch beschriftet — das Modell folgte der Beschriftung
und gewichtete einen +37-%-Aufwärtstrend als *gering*. Fix und Erfolgskontrolle:
`Arbeitsstand_Deadloop_09_08.md` 7.9.

**Zurückgestuft am 11.08. abends (7.10/7.11).** Hier stand „erklärt sechs von
sechs verpasste Gelegenheiten". Das beruhte auf **einer** gelesenen Begründung;
die Ergebnisdatei existiert nicht und speicherte Begründungen ohnehin nicht.
Die Zellenzählung über 44 Symbole ergibt: die Konstellation betrifft **2,71 %**
der Krypto-Tage (60T ≥ +30 %) — der Deadloop ist 97,5 %. **Der Defekt erklärt
ihn nicht.** Der **häufigere** Fehler ist das Gegenteil („Aufwärtstrend" bei
fallendem 60-Tage-Fenster, 11,39 %); das Aufwärtsurteil stimmt nur in 42 % der
Fälle mit der 60-Tage-Bewegung überein, das Abwärtsurteil in 74 %.

**Konsequenz für dieses Kapitel:** Der Defekt ist ein Sonderfall einer
allgemeineren Lücke — 10.1 regelt, dass Fakten *Aussagen* sein sollen, aber
nirgends steht, **wie** eine Aussage formuliert sein muss. Diese Formvorgabe
kommt als Kapitel 11 (Regeln R-T1…R-T9), und der Punktfix an `_struktur()` ist
dann ihr erster Anwendungsfall — **symmetrisch**, nicht in Richtung „mehr
kaufen".

---

## 11. Die Kette und die Form der Fakten (Stand 2026-08-11)

*Kapitel 4 beschreibt, WELCHE Fakten die alte Pipeline liefert. Kapitel 10,
welche die Rollen-Ebene liefert. Beide sagen nichts darüber, **wie** ein Fakt
formuliert sein muss — und genau dort saß der Defekt vom 11.08.
(`Arbeitsstand_Deadloop_09_08.md` 7.9/7.11). Dieses Kapitel schließt das.*

### 11.1 Die Kette in einem Bild

```
DETERMINISTISCH   Budget-Allocator waehlt Assets · Gate · Risiko · Positionsgroesse
                  Einstieg/Stop aus ATR (Regeln 4/16) · mechanische Notbremse
                        |   keine Betraege, keine Deckel an das Modell
LAGEBILD          1-2x taeglich, KEIN Einzelasset
                  raus: Lagebeschreibung, Tragfaehigkeit, Belege
                        |   Ergebnis, keine Rohdaten
BEFUND +          1x je Asset. Bestand zuerst.
ENTSCHEIDUNG      raus: Belege · unabhaengige Faktoren · Aktion ·
                        Begruendung · was_dagegen · umgeworfen_durch
                        |
VALIDATOR         korrigieren / degradieren / warnen - vier harte Gruende
                        |
BETRAG            deterministisch aus der Zahl unabhaengiger Faktoren
                        |
E-Mail je Asset + GUI
```

**Woran jede Stufe gemessen wird — getrennt, sonst schiebt man einer Stufe das
Versagen einer anderen zu:**

| Stufe | Maß | Warum getrennt |
|---|---|---|
| Gate | **Durchlässigkeit** — wie viele Handlungen wurden zu Nichthandeln? | sonst versteckt sich der Deadloop eine Ebene tiefer, wo er schwerer zu sehen ist. Der Regler-Audit fand 36 von 202 Schlüsseln wirkungslos |
| Lagebild | Zuspitzung ohne Deckung (`waechter_zuspitzung`) | seine Ausgabe ist die Eingabe der nächsten Rolle und wurde nie geprüft |
| Befund/Entscheidung | Handlungsquote **und** Erstdurchgang mit Stop | die Endrendite allein hat am 11.08. in die Irre geführt |
| Kette gesamt | Zielquote gegen **33 %** (Breakeven bei 3 / 1,5 ATR) | die Basisrate liegt bei 22,5 % — das ist die Hürde, nicht „Gewinn" |

### 11.2 Die Rollen — definiert über ihren exklusiven Eingang

**Die Namen sind unsere Bezeichnung, nicht das, was im Prompt steht.**

| Rolle | exklusiver Eingang | Frage | Ausgang |
|---|---|---|---|
| **Lagebild** | Marktdaten **ohne** Einzelwert | Wie ist das Umfeld? | Lage, Tragfähigkeit, Belege |
| **Befund** | Aufbau des Einzelwerts, Umsatz, Niveaus, Rang | Was zeigt *dieser* Wert? | Belege mit Gewicht |
| **Entscheidung** | **Bestand, Sperren, Kosten, vorherige Empfehlung** | Was tun wir, gegeben was wir halten? | Aktion, Begründung, Widerlegungskriterium |

**Der exklusive Eingang IST die Rollendefinition.** Damit wird der Grundsatz
„kein Block bei zwei Rollen" nicht nur eingehalten, sondern bedeutsam. Und
Lagebild sieht kein Asset — deshalb kann es nicht vom Einzelfall her
rationalisieren.

**Zur Persona im Prompt** („Du bist ein erfahrener Händler"): Nutzer am 11.08. —
*„nie im Prompt hängt vom Bedarf ab … wenn die Standards sagen wir brauchen die
Rollen, ist es kein Verbot."* Sie bleibt deshalb **eingeschaltet** und ist
einzeln schaltbar (`SYSTEM_PROMPT_TRADER_OHNE_PERSONA`). Eine offene, messbare
Frage, keine Setzung.

**Befund und Entscheidung sind heute EIN Aufruf.** Ob sie getrennt werden,
entscheidet die Betragsmessung (8c.3/M1). Das Argument für die Trennung ist
nicht Kontingent, sondern eine Eigenschaft: **Belege über den Markt dürfen nicht
davon abhängen, was wir zufällig halten.** Ein Gegenprüfer läuft nie im selben
Aufruf (R-A8).

### 11.3 Welche Fakten wohin — das Unterscheidungskriterium

> **Ein Marktfakt gehört in die BEURTEILUNG, wenn er zwischen Assets
> unterscheidet. Wirkt er auf alle gleich, ist er ein RISIKOPARAMETER — und
> Risiko ist deterministisch.**

| Fakt | unterscheidet? | gehört wohin |
|---|---|---|
| Marktbreite, Fear & Greed, FOMC-/CPI-Termine | nein — an einem Tag für alle gleich | Risikoschicht |
| freies Kapital, Depotwert, Deckel, Cash-Reserve, Drawdown-Grenze | nein | **nie an ein Modell** |
| BTC-Dominanz, DXY | ja | Beurteilung |
| **Lage des Assets zu SEINEM Benchmark** | ja, konstruktionsbedingt | Beurteilung — stärkster Kandidat |
| Korrelation des Assets zu seinem Markt | ja — sagt, wie viel der Gesamtmarkt hier bedeutet | Beurteilung |
| Bestand, G/V der Position | ja | **nur** Entscheidung |

**In einem Satz: Das Modell sieht, was wahr ist. Es sieht nie, was wir bereit
sind zu verlieren.**

### 11.4 Marktbezug je Assetklasse — Benchmark statt Breite

Die Marktbreite ist für dieses System **nicht baubar**, und das ist keine
Ermessensfrage (7.15):

| Klasse | Watchlist | mit Reihe | Breite möglich? | Benchmark |
|---|---|---|---|---|
| Krypto Spot | 44 | 34 | ja | BTC |
| Krypto Hebel | dito | dito | ja | BTC + Funding, OI |
| ETF | 7 | 6 | **nein** | je nach ETF, SPY als Näherung |
| Rohstoffe | 4 | 3 | **nein** | die Futures-Referenzen |
| Aktien | 2 | 2 | **nein** | **SPY — liegt seit 1993 in der DB** |

Für vier von fünf Klassen fehlen schlicht die Mitglieder. Der gemischte Korb,
der am VST-Anker Rohstoff-Futures und SPY als „Coins" zusammenrechnete, war der
Notbehelf daraus.

**Was für ein Einzelasset zählt, ist nicht der Zustand des Marktes, sondern die
Lage des Assets *in* seinem Markt.** `btc_relativwert` ist dieses Prinzip für
Krypto und existiert bereits.

### 11.5 R-T1 bis R-T9 — die Form eines Fakts

| # | Regel | Herkunft | Status |
|---|---|---|---|
| **R-T1** | **Jede Aussage nennt ihr Fenster.** Keine Behauptung ohne den Zeitraum, für den sie gilt | 7.9 | **tragend, eigene Messung** |
| **R-T2** | **Kein absolutes Etikett, wo ein relatives möglich ist.** Nicht „intakter Abwärtstrend", sondern „auf Sicht von 8 Handelstagen fallend, über 60 Tage +37 %" | 7.9/7.11 | **tragend, eigene Messung** |
| R-T3 | Keine Werturteile im Faktensatz | `einordnung`: 4,60 Konfidenzpunkte, 16 pp LONG | belegt, Wächter |
| R-T4 | Keine Selbstauskünfte (Trefferquote, Systemgüte, Kalibrierung) | −5,48 Konfidenzpunkte | Hypothese (Altsystem) |
| R-T5 | Relative Einheiten — ATR-Vielfache, % vom Schnitt | macht Fälle über Assets vergleichbar | belegt, praktiziert |
| R-T6 | Kein konstantes Feld | `regime` „baer" auf 1.022 Fällen | belegt, Wächter |
| R-T7 | Keine rohen Zahlenreihen | Tokenisierung, `kursverlauf[]` 90 Punkte | belegt |
| **R-T8** | **Blöcke dürfen einander nicht widersprechen — und keine Zwischenausgabe darf zuspitzen, was die Eingabe nicht hergibt** | 7.9/7.14 | **neu, Wächter gebaut** |
| R-T9 | Position ist Teil der Aussage — was zuerst steht, wiegt schwerer | B1, 3,2 pp bei 5,3× Rauschboden | belegt |

**Externe Deckung, ehrlich:** Einen Standard für die Textform von Fakten an ein
LLM gibt es **nicht** (Methodik 2.19.4). Gedeckt ist nur die Richtung —
semantisch schlägt numerisch (Claude 3: 68,7 % gegen 61,3 %), und
notationsübergreifende Zahlenvergleiche gelingen nur zu 50–70 %. **R-T1 und R-T2
stehen auf unserer eigenen Messung**, nicht auf Literatur.

### 11.6 Was das Modell NIE sieht — und warum

| | Begründung |
|---|---|
| **Positionsgröße, Beträge, Deckel** | R-A2. Extern belegt: LLMs sind dort am schwächsten. Und der Betrags-Umbau zeigte: die Frage verschiebt sich von „ist Handeln gerechtfertigt?" zu „sind 500 Euro gerechtfertigt?" |
| **Einstieg und Stop als Zahl** | Bauform B. Anchoring-Index 0,45 bei GPT-4, **Experten-Anker wirken am stärksten**, und keine Standard-Gegenmaßnahme half (Methodik 2.19.2). Ein aus ATR gerechneter Stop *ist* ein Experten-Anker |
| **Risikoparameter jeder Art** | sie ändern nichts daran, ob der Aufbau gut ist — nur ob wir dürfen. Das ist die Aufgabe des Gates |

**Was das Modell stattdessen zum Ausstieg liefert:** `umgeworfen_durch` — eine
überprüfbare Beobachtung, die die These widerlegen würde. Live geprüft am
11.08.: *„Ein Tagesschlusskurs über 2218,7467 EUR bei steigendem Volumen."*
Konkret, maschinell auswertbar, **und heute von niemandem ausgewertet**
(8c.2/K2). Das ist ein Urteil, keine Rechnung — deshalb gehört es zum Modell.

### 11.7 Offen in diesem Kapitel

- **Rang unter Kandidaten** — der Vergleich ist der Zuschnitt mit Evidenz, fehlt
- **Nachrichten** — nach allem Gemessenen die einzige Kategorie, die noch eine
  Kante enthalten kann. Sie gehören an **eine** Stelle: den Befund
- Ob Befund und Entscheidung getrennte Aufrufe werden (8c.3/M1)
- Ob die Persona bleibt (8c.3/M4)

---

## 12. Soll-Liste je Rolle — abgeleitet aus dem Fachstandard (2026-08-11)

*Schritt für Schritt: erst der verifizierte Ist-Zustand, dann die
Unabhängigkeitsrechnung, dann der Abgleich mit dem Standard (Methodik 2.21),
erst danach die Soll-Liste. Kein Schritt aus dem Gedächtnis — der Ist-Zustand
stammt aus `pruefe_rollenkette.py --trocken`.*

### 12.1 Schritt 1 — Was jede Rolle HEUTE bekommt, verifiziert

**LAGEBILD, vollständig — zwei Aussagen:**

```
Von 19 beobachteten Coins stehen 5 ueber ihrer 50-Tage-Linie (26 %).
   In den letzten 250 Handelstagen war dieser Anteil in 60 % der Faelle niedriger.
Von 19 beobachteten Coins stehen 1 ueber ihrer 200-Tage-Linie (5 %).
   In den letzten 250 Handelstagen war dieser Anteil in 38 % der Faelle niedriger.
```

Kein Regime, kein DXY, kein Fear & Greed, keine Volatilität, keine Liquidität.
**Nur Marktbreite** — und die ist für vier von fünf Assetklassen nicht
berechenbar (Kap. 11.4).

**BEFUND/ENTSCHEIDUNG, vollständig — neun Aussagen:**

```
1  Bestand
2  Marktstruktur (Swing-Vergleich) mit Fenster
3  Vergleich zur 60-Tage-Bewegung
4  Kursentwicklung 5 / 20 / 60 Tage
5  naechster Widerstand, in ATR und EUR, mit Beruehrungszahl
6  naechste Unterstuetzung, dito
7  Umsatz relativ zum 20-Tage-Schnitt
8  Umsatzverteilung auf Auf- und Abwaertstage
9  Umsatz-Stetigkeit ueber 10 Tage
+  Marktlage-Beurteilung aus dem Lagebild
```

### 12.2 Schritt 2 — Die Unabhängigkeitsrechnung

Der Standard zählt **unabhängige** Faktoren, nicht Aussagen. Nach Quelle
gruppiert:

| Quelle | Aussagen | unabhängige Faktoren |
|---|---|---|
| Schlusskurse | 2, 3, 4 | **1** |
| Swing-Hochs/-Tiefs (aus denselben Kerzen) | 2, 5, 6 | **1** — und teilt sich die Quelle mit der Struktur |
| Umsatzreihe | 7, 8, 9 | **1** |
| Depot | 1 | kein Marktfakt |

**Neun Aussagen, zwei unabhängige Marktfakten: Preis und Umsatz.** Genau die
„Illusion der Bestätigung" aus Methodik 2.21.5.

### 12.3 Schritt 3 — Der Abgleich, und was er erklärt

Der Standard verlangt **drei bis vier** unabhängige Faktoren. Verfügbar sind
**zwei**. Und das Modell zählt das selbst richtig — aus acht echten Durchläufen
(`degradierung.json`):

```
Faktoren = 3   ->  BTC 2026-03-27 REDUZIEREN · VST 2024-09-16 KAUFEN    beide gehandelt
Faktoren = 2   ->  5x NICHTS_TUN, 1x REDUZIEREN                          fast nie
```

**Der einzige KAUFEN im ganzen Satz kam aus dem einzigen Fall mit drei
Faktoren.**

> **DAMIT IST DER DEADLOOP ERKLÄRT, UND ZWAR ANDERS ALS SECHS WOCHEN LANG
> VERMUTET.** Er ist keine Fehlfunktion. Er ist das System, das den
> Fachstandard korrekt auf eine unzureichende Eingabe anwendet. Ein Trader, der
> bei zwei unabhängigen Faktoren nicht handelt, verhält sich diszipliniert.
>
> *n = 8 — ein starker Hinweis mit passendem Mechanismus, kein Beweis. Die
> Prüfung wäre: über viele Fälle zählen, ob die Handlungsquote mit der Zahl der
> Faktoren steigt.*

**Die Folge:** Mehr Handlungen entstehen **nicht** durch einen besseren Prompt,
sondern nur durch einen **dritten und vierten unabhängigen Faktor**. Und der
kann nicht aus der Kursreihe kommen — dort ist alles schon eine Übersetzung
desselben Fakts.

### 12.4 Schritt 4 — Die Soll-Liste

#### LAGEBILD

| | Fakt | Begründung |
|---|---|---|
| **RAUS** | Marktbreite | für 4 von 5 Klassen nicht berechenbar; der Korb ist gemischt und wechselt seine Zusammensetzung (Arbeitsstand 7.15) |
| **REIN** | **Volatilitätslage** je Klasse — heutige Schwankungsbreite gegen ihre eigene Historie | eine der vier Standarddimensionen, fehlt vollständig. Sie bestimmt laut Standard, wie wahrscheinlich ein Stop getroffen wird |
| **REIN** | **Trendlage des Klassen-Benchmarks** — BTC für Krypto, SPY für Aktien/ETF, Futures für Rohstoffe | zweite Standarddimension; ersetzt die Breite durch etwas, das je Klasse existiert |
| **REIN** | **Liquiditätslage** — Umsatzniveau des Benchmarks gegen seine Historie | dritte Dimension |
| BLEIBT | historischer Bezug („in X % der Fälle niedriger") | die einzige Kalibrierung, die das Modell vor Zuspitzung schützt — und sie wirkt nur, wenn sie mitgeliefert wird (`mit_bezug=True`) |

#### BEFUND

| | Fakt | Begründung |
|---|---|---|
| BLEIBT | Marktstruktur mit Fenster, Kursentwicklung, Niveaus | **zusammen EIN Faktor** — sie bleiben, aber sie zählen als einer |
| BLEIBT | Umsatz (drei Aussagen) | der zweite Faktor, seit 10.08. verfügbar |
| **REIN** | **Lage zum Klassen-Benchmark** (relative Stärke) | unterscheidet zwischen Assets — das Kriterium aus Kap. 11.3 |
| **REIN** | **Rang unter den Kandidaten des Durchgangs** | steht seit dem Rollenkonzept als Lücke; der Vergleich ist der Zuschnitt mit Evidenz |
| **NICHT REIN** | Fibonacci | eigenständige Vorhersagekraft fraglich, stärkster Ankertyp, und aus derselben Kursreihe — erhöht die *gefühlte* Zahl der Belege ohne einen echten (Methodik 2.21.4) |
| **NICHT REIN** | RSI, MACD, Stochastik nebeneinander | Multikollinearität; drei Werkzeuge derselben Kategorie sagen dasselbe |

#### ENTSCHEIDUNG

| | Fakt | Begründung |
|---|---|---|
| BLEIBT | Bestand zuerst | der KAS-Fall; offen bleibt, ob die Erststellung die Belege einfärbt (8c.3/M3) |
| BLEIBT | Sperren, Kosten, vorherige Empfehlung | Portfoliozustand, unterscheidet zwischen Assets |
| **REIN** | **`umgeworfen_durch` der VORHERIGEN Empfehlung, und ob es eingetreten ist** | der Ausstieg; heute wird das Feld erzeugt und nie gelesen (8c.2/K2) |
| NIE | Beträge, Deckel, Positionsgröße, Einstieg/Stop als Zahl | R-A2 und Bauform B (Kap. 11.6) |

### 12.5 Schritt 5 — Was fehlt und nicht aus dem Kurs kommen kann

Die Soll-Liste oben bringt das Lagebild auf drei der vier Standarddimensionen
und gibt dem Befund einen dritten unterscheidenden Fakt (relative Stärke). Sie
löst aber **nicht** das Grundproblem:

**Relative Stärke und Rang sind ebenfalls aus Kursreihen abgeleitet.** Sie
unterscheiden zwischen Assets — das ist mehr, als die heutigen Fakten leisten —
aber sie sind keine dritte Informationsquelle.

**Eine echte dritte Quelle wäre:** Nachrichten, Meldungen, Fundamentaldaten,
Positionierungsdaten. Erst damit sind drei bis vier *unabhängige* Faktoren
überhaupt möglich, und erst dann kann der Standard erfüllt werden.

**Das ist dieselbe Schlussfolgerung wie aus der Ökonomie-Rechnung (Arbeitsstand
7.25), auf einem völlig anderen Weg erreicht.** Zwei unabhängige Herleitungen,
dasselbe Ergebnis.

### 12.6 Reihenfolge der Umsetzung

| Rang | Schritt | Aufwand | warum hier |
|---|---|---|---|
| 1 | **Prüfen, ob die Handlungsquote mit der Faktorzahl steigt** — über viele Fälle statt über acht | gering, kein Modellaufruf nötig, wenn Faktorzahl mitgeschrieben wird | entscheidet, ob 12.3 trägt. **Vor allem anderen** |
| 2 | Volatilität + Benchmark-Trend + Liquidität ins Lagebild | mittel | drei der vier Standarddimensionen, heute fehlt alles außer Breite |
| 3 | Marktbreite raus | gering | sie ist nachweislich nicht berechenbar |
| 4 | Relative Stärke zum Klassen-Benchmark in den Befund | mittel | erster unterscheidender Fakt je Asset |
| 5 | `umgeworfen_durch` anschließen | mittel | der Ausstieg |
| 6 | Rang unter Kandidaten | mittel | steht seit dem Rollenkonzept offen |
| — | **Nachrichten** | groß | die einzige echte dritte Quelle. Ohne sie bleibt der Standard unerfüllbar |

---

## 12.7 Quellenabsicherung — was wir wirklich bekommen können (geprüft 2026-08-11)

**Nutzervorgabe:** *„davor noch alle Quellen sauber absichern — gehe in die
Detailrecherche zu Krypto und prüfe breit und intensiv."* Deshalb wurde nicht
gelesen, sondern **jeder Endpunkt einzeln aufgerufen**. Listicles zu freien APIs
sind Werbung; eine Quelle gilt hier erst als vorhanden, wenn sie geantwortet hat.

### Live getestet, alle mit Status 200

| Quelle | liefert | je Symbol? | Key? |
|---|---|---|---|
| **Binance Futures** | Open Interest · Long/Short · **Funding** | ja | nein |
| **Bybit** | Open Interest · **Funding** | ja | nein |
| CoinMetrics Community | BTC-On-Chain (aktive Adressen u. a.) | nur BTC | nein |
| DefiLlama | Stablecoin-Angebot | Marktebene | nein |
| blockchain.info | BTC-Marktpreisreihe | nur BTC | nein |
| Deribit | DVOL, Options-Skew | BTC/ETH | nein |
| Alternative.me | Fear & Greed | Marktebene | nein |
| CoinGecko keyless | **Entwickleraktivität je Coin** | ja | nein, **aber 429** |
| CoinPaprika | Ticker, Preise | ja | nein |

### Die Abdeckung, an unserer eigenen Watchlist gemessen

```
Binance USDT-Perpetuals gesamt   683      unsere Symbole dort   37 von 44
Bybit Linear-Perpetuals gesamt   699      unsere Symbole dort   35 von 44
mindestens eine der beiden                                      38 von 44  =  86 %

ohne Derivatedaten:  CANTON · EURCV · FLOKI · SUPRA · VSN · XNO
```

**86 % unserer Krypto-Symbole haben Positionierungsdaten — kostenlos, ohne
API-Key.** Das ist deutlich besser als zuvor angenommen; die Einschätzung
„Krypto hat die schwächste Zweitquellenlage" war falsch.

### DER FUND: Funding-Rate je Symbol ist frei verfügbar und wird nicht geholt

`api/derivatives.py` holt **Open Interest** und **Long/Short**, aber **keine
Funding-Rate**. Die kommt heute aus `api/kraken.py` — und Kraken deckt weniger
Symbole ab als Binance und Bybit zusammen. Beide liefern sie je Symbol,
kostenlos, keyless, live geprüft.

### Was NICHT brauchbar ist

| | Grund |
|---|---|
| CoinGecko `community_data` (Reddit) | **0 von 5** Coins mit belegten Werten; Telegram 2 von 5. Ein Feld, das überwiegend null ist, ist ein **konstantes Feld** (B10) und würde von `finde_konstanten()` zu Recht blockiert |
| CoinDesk Data (ehem. CryptoCompare) | kostenloser Zugang **zum 21.05.2026 eingestellt** |

### Betriebliche Warnung: CoinGecko keyless ist enger als beworben

**Nach fünf Aufrufen mit 2,5 Sekunden Pause kam HTTP 429.** Die verbreitete
Angabe „30 Aufrufe je Minute" hält in der Praxis nicht. Für 44 Coins bedeutet
das: sehr langsames Takten, der Demo-Key, oder ein Abruf nur für die Symbole,
die tatsächlich zur Entscheidung anstehen. **Das gehört in jede Aufwandsschätzung
— und in den Vorflug jedes Laufs, der CoinGecko benutzt.**

### Was das für die Entwicklerdaten heißt

`commit_count_4_weeks`, `pull_requests_merged`, `pull_request_contributors` und
`stars` sind **bei 4 von 5 geprüften Coins belegt** — und bei EURCV korrekt
null, weil ein Stablecoin kein Entwicklungsprojekt ist. Sie sind damit
**unabhängig vom Kurs und unterscheidend zwischen Assets** — beide Kriterien
aus Kapitel 11.3 erfüllt.

**Vorbehalt:** Entwicklungsaktivität ist ein **langsames** Merkmal. Sie ändert
sich über Monate, nicht über Tage. Für eine Entscheidung über einen Einstieg in
den nächsten Wochen ist sie eher ein Qualitäts- als ein Zeitpunktmerkmal. Das
gehört bei der Zuordnung berücksichtigt — sie taugt für „welches Asset", nicht
für „wann".

---

## 12.8 Zuordnung je Rolle und Assetklasse (2026-08-11)

*Angewandtes Kriterium (Kap. 11.3): **unterscheidet der Fakt zwischen Assets →
Beurteilung; wirkt er auf alle gleich → Lagebild oder Risikoschicht.** Alle
Quellen sind in 12.7 einzeln live geprüft.*

### LAGEBILD — je Klasse, die vier Standarddimensionen

| Dimension | Krypto | Aktien / ETF | Rohstoffe |
|---|---|---|---|
| **Trend** | BTC als Benchmark | SPY (in der DB seit 1993) | Futures-Referenz |
| **Volatilität** | **Deribit DVOL** | VIX (`yfinance_client`) | ATR-Perzentil der Referenz |
| **Liquidität** | Stablecoin-Angebot (DefiLlama), Börsenzuflüsse (CoinMetrics) | Zinsen, CPI, M2 (`macro`) | DXY |
| **Stimmung** | Fear & Greed (alternative.me), BTC-Dominanz | — | — |
| ~~Breite~~ | **entfällt** — für 4 von 5 Klassen nicht berechenbar (Kap. 11.4) | | |

**Heute im Lagebild: nur Marktbreite. Alle vier Zeilen oben fehlen vollständig.**

### BEFUND — je Asset, nur was zwischen Assets unterscheidet

| Klasse | dritter/vierter unabhängiger Faktor | Modul | Abdeckung |
|---|---|---|---|
| **Krypto Spot** | **Funding je Symbol** · Open Interest · Long/Short | `derivatives.py` (Funding **fehlt**, s. 12.7) | **38 von 44** |
| | relative Stärke zu BTC | vorhanden (`btc_relativwert`) | alle |
| | Entwickleraktivität | CoinGecko keyless | alle, aber **429-Grenze** |
| **Krypto Hebel** | wie Spot, Funding wiegt schwerer (Haltekosten je Tag) | dito | dito |
| **Aktien** | **Insidergeschäfte** (Form 4) | `sec_edgar.py` | je Aktie |
| | **Short Interest** | `finra.py` | je Aktie |
| | Analysten-Konsens-Verlauf | `finnhub.py` (Key) | je Aktie |
| | Fundamentaldaten | `asset_quality.py` | je Wertpapier |
| | relative Stärke zu SPY | zu bauen | alle |
| **Rohstoffe** | **COT-Positionierung** | `cftc_cot.py`, kein Key | je Rohstoff |
| | Lagerbestände | `eia.py` | nur Erdgas |
| | relative Stärke zur Futures-Referenz | zu bauen | alle |
| **ETF** | relative Stärke zu SPY | zu bauen | alle |
| | *sonst nichts* | — | — |

### ENTSCHEIDUNG — für alle Klassen gleich

Bestand · Sperren · Kosten · vorherige Empfehlung · **`umgeworfen_durch` der
vorherigen Empfehlung samt der Frage, ob es eingetreten ist**. Niemals Beträge,
Deckel oder Niveaus als Zahl (Kap. 11.6).

### Wie viele unabhängige Faktoren jede Klasse damit erreicht

```
Aktien       Preis · Umsatz · Insider/ShortInterest · Fundamentaldaten     4   erfuellt
Krypto       Preis · Umsatz · Positionierung/Funding · (Entwicklung)       3-4 erfuellt
Rohstoffe    Preis · Umsatz · COT-Positionierung · (Lagerbestaende)        3-4 erfuellt
ETF          Preis · Umsatz                                               2   NICHT erfuellt
```

> **ETF ist die einzige Klasse, die den Standard nicht erreichen kann** — es gibt
> keine dritte Quelle je ETF. Und es ist zugleich die Klasse mit der
> schlechtesten Kostenquote (0,52 R, Arbeitsstand 7.23), weil der ATR-Stop dort
> nur 1,9 % vom Kurs entfernt liegt.
>
> **Beide Befunde treffen dieselbe Klasse, unabhängig voneinander.** Das ist eine
> Entscheidungsgrundlage: ETFs sind für diesen Aufbau strukturell ungeeignet.
> Für ein Halten oder eine Akkumulation bleiben sie unberührt geeignet — das ist
> eine andere Frage (8d, Rang 1).

### Bekannte Lücken in dieser Zuordnung

1. **6 Krypto-Symbole ohne Derivatedaten** (CANTON, EURCV, FLOKI, SUPRA, VSN,
   XNO) bleiben bei zwei Faktoren. EURCV ist ein Stablecoin und braucht keine.
2. **Entwickleraktivität ist ein langsames Merkmal** — sie ändert sich über
   Monate. Sie taugt für *welches Asset*, nicht für *wann*.
3. **CoinGecko-Taktung**: 429 nach fünf Aufrufen. Der Abruf gehört auf die
   Symbole beschränkt, die tatsächlich zur Entscheidung anstehen.
4. **`finnhub.py` und `eia.py` brauchen einen Key** — kostenlos, aber
   einzurichten. Alle übrigen Quellen laufen keyless.
5. **Relative Stärke zum Klassen-Benchmark** ist für Aktien, ETF und Rohstoffe
   noch nicht gebaut; für Krypto existiert sie als `btc_relativwert`.

### Reihenfolge

| Rang | Schritt | warum |
|---|---|---|
| 1 | **Funding je Symbol in `derivatives.py`** | frei, keyless, 38 von 44, und der Baustein fehlt komplett |
| 2 | Lagebild auf die vier Dimensionen bringen | heute ist nur die untaugliche Breite drin |
| 3 | COT für Rohstoffe, Insider + Short Interest für Aktien | fertige Module, nie an die Rollen-Ebene angeschlossen |
| 4 | Relative Stärke je Klasse | erster unterscheidender Fakt für Nicht-Krypto |
| 5 | Entwickleraktivität | langsam, deshalb zuletzt |

---

## 12.9 Gebaut: Funding-Rate je Symbol (11.08.2026)

**Rang 1 aus 12.8 umgesetzt.** `api/derivatives.py` holte bisher Open Interest
und Long/Short, aber **keine Funding-Rate** — die kam ausschließlich aus
`api/kraken.py`, das weniger Perpetuals listet.

### Was neu ist

```
get_binance_funding_history(symbol, limit)   Binance zahlt alle 8 h, limit=100 ≈ 33 Tage
get_bybit_funding_history(symbol, limit)     absteigend geliefert, aufsteigend zurueckgegeben
get_funding_history(symbol, limit)           Binance zuerst, Bybit als Rueckfall
summarize_funding(readings)                  der historische Bezug
```

**Genau eine Quelle je Symbol, kein Mitteln.** Zwei Börsen zu mitteln wäre eine
Zahl, die es an keiner Börse gibt; das Feld `exchange` sagt, welche es war.

**Die rohe Zahl ist kein Fakt.** Eine Funding-Rate von 0,0001 sagt einem Modell
nichts — erst ihr Verhältnis zur eigenen Historie ist eine Aussage (R-T1: das
Fenster nennen, R-T5: relative Einheiten). `summarize_funding()` liefert
Perzentil, Anteil positiver Perioden und Mittel, **ohne Bewertung** (R-T3);
dasselbe Muster wie `finra.summarize_short_interest()`.

### Gemessene Abdeckung

```
39 von 44 Krypto-Symbolen  =  89 %      Binance 37 · Bybit 2
ohne:  CANTON · EURCV · FLOKI · SUPRA · VSN
```

**Besser als die 38 aus der Vorabschätzung in 12.7** — der Rückfall über beide
Börsen findet Symbole, die eine Prüfung gegen `exchangeInfo` übersieht (dort
weichen Basissymbole ab, etwa mit `1000`-Präfix). Die Abdeckung wurde deshalb
**nicht geschätzt, sondern durch Abruf aller 44 Symbole gemessen.**

### Konstanten-Prüfung bestanden

```
9 verschiedene aktuelle Werte bei 13 gepruefte Symbolen
Anteil positiver Funding-Perioden:  2 %  (CAT)  bis  100 %  (AKT)
Perzentil der aktuellen Rate:       0 %          bis   98 %
```

**CAT hatte in 98 von 100 Perioden negatives Funding, BTC in 99 positives.** Das
Feld unterscheidet stark zwischen Assets und ist damit ein Kandidat für den
**Befund** (Kriterium aus Kap. 11.3), nicht für die Risikoschicht.

### Was noch fehlt, bevor es wirkt

Die Funktion ist gebaut und geprüft — **sie ist noch nicht an die Rollen-Ebene
angeschlossen.** Dafür braucht es eine Aussage in `lagebeschreibung.py`, etwa:

> *„Der Terminmarkt zahlt seit 100 Perioden überwiegend Longs an Shorts
> (2 % positive Perioden); die aktuelle Rate liegt im untersten Zehntel ihrer
> eigenen Historie."*

Formuliert nach R-T1 (Fenster genannt), R-T2 (kein Etikett), R-T3 (keine
Bewertung), R-T5 (relativ). **Erst dieser Satz macht aus der Zahl einen Fakt —
und erst dann ist es der dritte unabhängige Faktor.**

---

# 13. Abgleich Code ↔ Doku über die ganze Ablaufkette (12.08.2026)

*Auf Nutzerverlangen: „gib mir je Abschnitt der Ablaufkette aus, was diese
macht, warum, was bekommt der nächste Abschnitt — sowie wo entsteht die
Detail-Information (eMail, GUI) für den Benutzer."*

**Jede Aussage hier ist an der QUELLE geprüft, nicht aus einem Aufrufer
abgeleitet.** Diese Regel entstand am selben Tag aus einem eigenen Fehler
(13.0).

## 13.0 Der Fehler, der die Regel erzwungen hat

Ich hatte berichtet, die neue Rollen-Kette laufe auf `gemini-3.5-flash-lite`.
Gelesen hatte ich das in **einem Prüfskript**.

| Fundstelle | Modell |
|---|---|
| `api/gemini.py:35` — `DEFAULT_MODEL` | **`gemini-3.1-flash-lite`** ← die Produktion |
| `pruefe_rollenkette.py:112` | `gemini-3.5-flash-lite` ← nur mein Skript |

`3.5` steht in sechs Messskripten und **nirgends sonst**. Der Nutzer hat es
bemerkt, nicht ich.

> **Folge, die bleibt: alle Messungen der neuen Kette liefen auf 3.5, die
> Produktion läuft auf 3.1.** Ein Befund überträgt sich nicht automatisch
> zwischen Modellen. Jede Zahl aus den Läufen vom 10.–12.08. braucht eine
> Wiederholung auf 3.1, bevor sie für die Produktion gilt.

**Nutzervorgabe daraus:** *„immer an der Quelle prüfen sonst haben wir ein
Problem."* Ein Skript ist eine **Verwendung**, keine Festlegung.

## 13.1 Es gibt ZWEI Ketten — und nur eine ist verdrahtet

| | Aufrufer in `scheduler/background.py`? |
|---|---|
| **ALT**: `szenario_fakten` + `krypto/analyst` + Pipelines | **ja** — das ist die Produktion |
| **NEU**: `rolle_analyst` + `rolle_trader` + `rollen_eingabe` | **nein** — null Aufrufer außerhalb von `messe_*.py` und `pruefe_*.py` |

Geprüft per Import-Suche über das ganze Repo. Alles, was in diesem Dokument
über die neue Kette steht, beschreibt damit einen **Bauzustand, keinen
Betrieb.**

## 13.2 Abschnitt für Abschnitt

### A — Datenbeschaffung
- **Was:** Kurse (Kraken, ersatzweise Binance/Bybit), Makro, Derivate, On-Chain
- **Warum:** ohne echte Tageskerzen rechnet jeder Fensterindikator falsch — der
  Vier-Tage-Kerzen-Fehler stand Wochen unbemerkt in der Datenbank
- **Weitergabe:** `price_history_ohlc`
- **Nutzer sieht:** nichts

### B — Faktenbildung: aus Zahlen werden Sätze
- **Was:** `agent/marktlage.py` (12 Aussagen, marktweit) und
  `agent/lagebeschreibung.py` (je Asset)
- **Warum:** die Rollenanalyse vom 10.08. — das LLM wird wegen **Sprache**
  gebraucht, nicht wegen Zahlen
- **Weitergabe:** `rollen_eingabe.baue_lagebild_eingabe()` /
  `baue_befund_eingabe()` — die einzigen Stellen, an denen Rolleneingaben
  entstehen
- **Nutzer sieht:** **nichts — und das ist eine Lücke.** Die Fakten, auf denen
  jede Empfehlung steht, tauchen in keiner Mail auf. Der Nutzer sieht das
  Urteil, nicht seine Grundlage

### C — Rolle 1 · Lagebild *(1 Aufruf je Durchgang, nicht je Asset)*
- **Was:** 12 Aussagen → 2–3 Sätze + 2–4 Belege
- **Warum:** kennt kein Asset und kann deshalb nicht vom Einzelfall her
  rationalisieren — der häufigste Weg, auf dem eine Marktbeurteilung zur
  Nachbegründung einer schon gefallenen Entscheidung wird
- **Weitergabe an Rolle 2:** `{"lage": <Prosa>, "gleichlauf": <gerechnet>}`
- **Nutzer sieht:** heute nichts

### D — Rolle 2+3 · Befund + Entscheidung *(1 Aufruf je Asset)*
- **Was:** sechs Schritte — Belege sammeln → unabhängige Faktoren zählen →
  handeln → begründen → Gegengrund → Falsifikator
- **Warum zusammengelegt:** getrennt wären es zwei Aufrufe je Asset. Bei 44
  Assets 88 statt 44
- **Weitergabe:** `aktion`, `belege`, `unabhaengige_faktoren`, `begruendung`,
  `was_dagegen`, `umgeworfen_durch`

**Aufrufrechnung:** 1 + 44 = **45 Aufrufe je Durchgang.** Prompt-Umfang alt
34.611 Zeichen, neu 705 + 1.871 = **2.576** (Faktor 13).

### E — Gate / Risikomanagement
- **Was:** RM-1…RM-7, Cash-Reserve, vier Positionsgrößen-Deckel, Vetos —
  deterministisch
- **Warum:** Risiko gehört nicht ins Modell (Kap. 11.3), extern belegt
- **Status:** **in keiner Messung der neuen Kette dabei** (G1 offen)

### F — Speichern
- **Was:** Tabelle `signals`, **112 Spalten**
- **Problem:** die Spalten gehören der **alten** Kette (13.3)

### G — E-Mail: hier entsteht die Nutzer-Information
Gebaut in `scheduler/background.py:2064` (`_notify_spot_signal`):

```
Aktion / Regime / Berechnet · Anbieter
--- 1. MATHEMATISCH BERECHNET ---
    Entry, Stop-Loss, Take-Profit, Mindestziel, Positionsgröße, Tranchen
--- 2. LLM-BEWERTUNG (Konfidenz X %) ---
    short_reasoning, Top-Gründe 1-5, Gegenargument, Key-Risks,
    Haltekriterium, Forecast bull/base/bear
--- 3. KONKLUSION (RISIKOFAKTOREN) ---
    Legende, Fazit
● Z.ai-Gegenprüfung der Begründung: <Urteil> - <Kurzbegründung>
● Z.ai eigene Richtungseinschätzung: <Richtung> (stimmt überein/weicht ab)
+ Liquiditätszonen-PNG
```

### H — GUI
`ui/app.py` Signale-Tab, Formatierer in `ui/formatting.py` — **eigene Kopien**,
getrennt von den E-Mail-Formatierern in `background.py`. Doppelpflege ist
gewollt (unterschiedlicher Textkontext), aber jede Änderung muss an **beiden**
Stellen passieren.

## 13.3 Die Naht, die beim Umschalten bricht

**Die E-Mail ist auf die Ausgabe der ALTEN Kette gebaut.** Drei Felder passen
nicht:

| E-Mail erwartet | neue Kette liefert |
|---|---|
| `Konfidenz X %` — **fest in der Abschnittsüberschrift** | **nichts.** Konfidenz wurde bewusst gestrichen: vorhergesagt 77,5 % gegen tatsächlich 33,3 % |
| `Regime` | nichts — über 1.022 Fälle konstant „baer" |
| Top-Gründe 1–5, Risikofaktoren, Forecast bull/base/bear | `belege`, `was_dagegen`, `umgeworfen_durch` |

Und umgekehrt: **`unabhaengige_faktoren` und `umgeworfen_durch` haben in den
112 Spalten kein Zuhause.** Ausgerechnet `umgeworfen_durch` ist der
Falsifikator, den V1 auswerten soll.

> **Für den glatten Schnitt heißt das:** B1 („Rollen-Ebene einhängen") ist nicht
> ein Aufruf, den man umlegt. Es sind drei Arbeiten: Feld-Abbildung neue Kette →
> `signals`, E-Mail-Text auf die neuen Felder, GUI auf die neuen Felder.

## 13.4 Z1 — der deterministische Prüfer, aufgeschlüsselt

Vier Regeln. Alle prüfen **Zusagen, die wörtlich im Prompt stehen**.

| Regel | prüft | fängt | Ebene |
|---|---|---|---|
| **Z-1 Zahlendeckung** | Jede Zahl der Ausgabe steht in der Eingabe (Toleranz 0,55 fürs Runden) | „Erfinde nichts hinzu" — der Beleg mit erfundenem Wert | je Fall |
| **Z-2 Richtungstreue** | Behauptete Gleich-/Gegenläufigkeit gegen den gerechneten `gleichlauf` | „die Märkte im Gleichschritt", während BTC −39 % und SPY +20 % steht | je Fall |
| **Z-3 Zuspitzung** | delegiert an `waechter_zuspitzung` | „extreme Schieflage" bei Perzentil 46 | je Fall |
| **Z-4 Leerlauf** | wie viele **verschiedene** Ausgaben über einen ganzen Lauf | ein Lagebild, das immer dasselbe sagt (R-T6) | je Lauf |

**Warum deterministisch und nicht als LLM:** ein prüfendes Modell hätte
dieselbe Schwäche wie das geprüfte und keinen Festpunkt außerhalb; die Güte
eines LLM ist bei uns vorab nicht messbar (Mistral −27,38 R über 38 Fälle ohne
Vorwarnung); und es kostet je Anker einen Aufruf aus der knappsten Ressource.

**Was Z1 NICHT kann, klar gesagt:** es prüft die **Treue zur Eingabe**, nicht
die **Güte des Urteils**. Ob „uneinheitliche Märkte" ein guter Grund ist, nichts
zu tun, sagt es nicht — das entscheidet eine Wirkungsmessung, kein Wächter.

## 13.5 Z.ai — was überlebt und was fällt

**Die vom Nutzer gewünschte Form ist bereits gebaut** — nicht als Idee, als
laufender Code: `agent/krypto/gegenpruefung.py`, aufgerufen in
`agent/krypto/pipeline.py:1080`, fünf DB-Spalten, E-Mail-Formatierer,
GUI-Formatierer.

### Die Architektur ist richtig und überlebt

1. **Sie prüft nicht die Entscheidung, sondern den Widerspruch.** Nicht „war
   KAUFEN richtig?" — das wäre eine zweite, primitivere Bewertung, die die
   Primäranalyse unterläuft — sondern: *widerspricht die Begründung den harten
   Zahlen?* Freitext gegen Zahlen ist die eine Sache, die ein LLM kann und eine
   Python-Regel nicht.
2. **Der Richtungs-Abgleich ist anti-anker gebaut.** `baue_objektive_fakten()`
   lässt `action`, `richtung` und `confidence_pct` bewusst weg. Die
   Übereinstimmung wird **in Python** verglichen, nicht vom Modell beurteilt.
3. **Wirkungsfrei by construction**, nicht per Konvention: der Aufruf läuft im
   `threading.Thread(daemon=True)` **nach** `insert_signal`. Er *kann* das
   Signal nicht ändern.

### Der Faktensatz fällt — Nutzereinwand, an der Quelle bestätigt

*„ich denke die alte ZAI prüfung ist auch auf den alten und falschen prompts
gelaufen."* Geprüft in `baue_objektive_fakten()`. Z.ai bekommt fünf Dinge:

| Fakt | Zustand nach unseren eigenen Messungen |
|---|---|
| `rsi` | in Ordnung |
| `funding_rate_vorzeichen` | in Ordnung |
| **`regime`** | **über 1.022 Fälle konstant „baer"** — ein Urteil gegen ein Feld, das nie variierte (R-T6) |
| **`trend`** | ein **absolutes Etikett** (`EMA-Ordnung.detail`) — der R-T2-Defekt, der den Deadloop gebaut hat |
| **`technische_konfluenz`** | „8 bullisch / 3 bärisch von 11" — Indikatorzählung **aus derselben Kursreihe**: *illusion of confirmation* |

In den Konsistenz-Check geht zusätzlich `confidence_pct` — 77,5 % vorhergesagt
gegen 33,3 % tatsächlich.

**Drei von fünf nutzbaren Fakten sind defekt.** Damit fällt auch die
Kalibrierung: der Befund „bei eindeutigen Fakten stabil, bei grenzwertigen
5/6 SHORT" beschreibt Z.ais Verhalten **auf genau diesem Faktensatz** und ist
nicht übertragbar.

> **Nicht messbar auf diesem Rechner:** in der Desktop-Datenbank stehen **0**
> Signale mit `zai_gegenpruefung_urteil`. Die Verteilung liegt auf dem Notebook.

### Bilanz

| überlebt | fällt |
|---|---|
| asynchron nach dem Insert · Anti-Anker · Vergleich in Python · zwei getrennte Aufrufe · E-Mail- und GUI-Weg · Prompt-Länge (1.340 Zeichen, richtige Größenordnung) | der Faktensatz (3 von 5 defekt) · der Prompt (fragt nach Ziel/Stop-Wahrscheinlichkeiten, die die neue Kette nicht produziert) · die Kalibrierungsmessung |

### Was zu bauen ist

- `pruefe_konsistenz()` gegen `begruendung` statt `short_reasoning`, und gegen
  die **neuen** Fakten (Prosa aus `marktlage.py` / `lagebeschreibung.py`)
- `leite_eigene_richtung()` auf die fünf Aktionen (KAUFEN, NACHKAUFEN,
  REDUZIEREN, VERKAUFEN, NICHTS_TUN) statt LONG/SHORT/NEUTRAL — weiter **ohne**
  `aktion` in der Eingabe
- Der gemessene Vorbehalt bleibt gültig und muss neu gemessen werden: bei
  grenzwertigen Fakten schwankt Z.ai. Solange die Prüfung **beobachtend**
  bleibt, ist das tragbar; bei Wirkung wäre es untragbar

**Z1 und Z.ai ersetzen einander nicht.** Z1 fängt **Erfindung** (kostenlos,
kann sich nicht irren), Z.ai fängt **Denkfehler** (ein Aufruf, kann sich irren).
Beide gehören in die Mail — Z1 als stille Fußzeile, Z.ai als die zwei Zeilen,
die der Nutzer heute schon kennt.


---

# 14. Die zweite Schiene: Fakten für den NUTZER (Nachtrag 2026-08-13)

Kapitel 11.6 sagt, was das **Modell** nie sieht. Dieses Kapitel sagt, was der
**Nutzer** sieht — und dass dafür andere Regeln gelten.

    Faktentext  -> das Modell  -> R-T1..R-T9: relativ vor absolut
    Faktenblock -> der Nutzer  -> ABSOLUT ZUERST, Etikett statt Perzentil

**Der Anlass war ein eigener Denkfehler:** die erste Fassung der neuen E-Mail
übernahm die Sätze für das *Modell*. Dort stand „3,9 Schwankungsbreiten höher,
bei 62.000 EUR" statt umgekehrt, und ein Perzentil, wo ein Etikett hingehört.
R-T1/R-T2 wurden für ein Modell hergeleitet, das absolute Zahlen nicht
einordnen kann — **der Nutzer kann das.**

## 14.1 Der Kern: drei Familien, nicht zehn

Gemessen an 37 Symbolen und 20.494 Ankern gegen die Geometrie, die die App
vorschlägt (`messe_top_fakten.py`). Basis 23,5 % Trefferquote.

| Familie | Richtung | gemessen |
|---|---|---|
| **Schwankung** | niedrig ist besser | 29,5 % gegen 17,8 % |
| **Kurzfrist-Momentum** | steigend ist besser | 28,0 % gegen 18,9 % |
| **Volumen** | hoch ist besser | 27,1 % gegen 22,5 % |

**Momentum erscheint genau EINMAL.** Rückgang seit 60-Tage-Hoch, Abstand zur
50-Tage-Linie, Trend 20 Tage und RSI 14 korrelieren mit **0,59 bis 0,89** — ein
Faktor, nicht vier. **Fear & Greed gehört in dieselbe Familie** (zur Hälfte aus
dem Kurs abgeleitet), nicht daneben.

## 14.2 Zusatzinfo — der Maßstab

Nutzervorgabe: *„kein Beiwerk ohne Sinn."* **Sinnvoll ist, was eine Dimension
aufmacht, die die drei Familien NICHT abdecken.** Ein weiteres kursabgeleitetes
Maß tut das nicht — es wäre der fünfte Momentum-Vertreter. Vier Kategorien
bestehen:

| Kategorie | Beispiele |
|---|---|
| **Kosten** | Funding EUR/Tag, Liquidationspreis |
| **Positionierung** | Retail-Konsens, Insider, Short-Interest, COT |
| **Fundamentaldaten** | KGV, Lagerbestände |
| **Vorausschauende Marktpreise** | Put-Skew — der einzige Fakt im System, der nicht aus der Vergangenheit stammt |

**Durchgefallen:** `regime_profil` (über 1.022 Fälle konstant „baer" — R-T6),
`signal_stabilitaet` (misst die gestrichene Konfidenz), `liquiditaetszonen`,
`trigger`/`systemguete`.

**Je Bereich verschieden, weil die Datenlage es ist:** von 40 Faktenschlüsseln
der sechs `build_facts()` kommen nur **fünf** in allen sechs vor (`preis`,
`regime`, `historische_erfolgsquote`, `historischer_makro_vergleich`,
`disclaimers`).

## 14.3 Jede Zeile sagt drei Dinge

    Schwankung   3,0 % je Tag                             GUENSTIG
      Wie stark der Kurs täglich schwingt, gemessen an seinem eigenen Jahr.
      Ruhig ist besser - über alle Einstiege gemessen: 29,5 % Treffer am
      guten Ende gegen 17,8 % am anderen, Schnitt 23,5 %.

Wert, Urteil, Bedeutung mit Richtung. Der Wert allein ist nicht benutzbar
(„Perzentil 74" war genau der Einwand), die Wirkung allein auch nicht.

**Der Wirkungssatz spricht über ALLE Einstiege, nicht über diesen.** Die erste
Fassung lautete „ruhige Einstiege erreichten ihr Ziel in 29,5 % der Fälle" —
das liest sich wie die Aussicht *dieses* Signals. Es ist die Verteilung, in die
es fällt.

## 14.4 Was fehlt, wird benannt

Ein Kernfakt ohne Wert erscheint als Lücke: *„Keine Angabe zu: Volumen. Ein
Punkt weniger steht damit hinter dieser Empfehlung."* Sonst sieht ein Signal
mit einem Fakt aus wie eines mit dreien.

**Zusatzinfo ist freiwillig** — ihr Fehlen wird nicht gemeldet.

**~~Am laufenden Tag entfällt das Volumen.~~ ÜBERHOLT 13.08.** — richtig war
die Absicht, falsch die Folge: weil *jedes* Live-Signal auf dem jüngsten Tag
rechnet, fehlte damit eine von **drei** gemessenen Familien in **jeder**
Nachricht. Der Faktenblock versprach drei Punkte und lieferte zwei (gefunden
in der Gegenprüfung zu Stufe C). **Jetzt kommt das Volumen vom letzten
vollständigen Tag** und trägt den Zusatz „(Vortag)“ — ein ganzer Tag statt
eines angefangenen. Die ursprüngliche Begründung bleibt gültig und steht
hier weiter:

Der Umsatz des laufenden Tages ist naturgemäß kleiner
als der eines ganzen Tages; an echten BTC-Daten stand er beim 0,2-fachen des
Mittels. Ohne diesen Schalter hätte **jede** Live-Mail „Volumen UNGÜNSTIG"
gemeldet — ein systematischer Fehler in jeder einzelnen Nachricht, und einer,
der wie ein Befund aussieht.

## Nachtrag (2026-08-16): Z.ai ist Rolle G - eine zweite QUELLE

**Der Richtungsabgleich ist stillgelegt.** Er bekam dieselben Marktfakten wie
Rolle BC und sollte daraus eine eigene Richtung ableiten - zwei Leser derselben
Seite. Vier unabhängige Gründe, jeder für sich ausreichend:

| | |
|---|---|
| keine eigene Quelle | *Homogeneous Debate* — teilen zwei Prüfer die Informationsgrenze, verliert die Prüfung ihren Wert |
| er unterschied nicht | über 2.469 Prüfungen: SHORT 1.246, NEUTRAL 1.206, **LONG 17** — bei LONG-Signalen zwei Zustimmungen in 377 Fällen (R-T6) |
| seine Zustimmung trennte nicht | 0 von 7 Treffern gegen 17,2 % bei Abweichung |
| seine gemessene Güte war die Marktrichtung | wer im Bärenregime immer SHORT sagt, hat oft recht |

Er kostete **drei von vier Aufrufen**; am 15.08. bekamen deshalb 35 von 39
Signalen gar keine zweite Meinung.

**An seiner Stelle steht Rolle G** mit eigener Grundlage: Veränderung der
offenen Kontrakte, Finanzierungsrate als Perzentil der eigenen Historie, Anteil
der Long-Konten, Marktregime mit Dauer. Ein Aufruf. Keine Frage ohne Grundlage —
bei Aktien, Rohstoffen und ETF wird nicht gefragt.

**Die Antwort steht immer in der Mail**, in einem eigenen Abschnitt, auch ohne
Einwand — mit den Zahlen, auf die sie sich stützt. Nutzervorgabe vom 16.08.

**Ungemessen wie alles andere:** eigene Spalte, gegen die Basisrate. Sagt sie in
95 % der Fälle „kein Einwand", ist sie dieselbe Konstante wie ihr Vorgänger.

---

## Nachtrag 16.08.2026 (abends) — Phase I: was der Trader jetzt zusätzlich sieht

`PROMPT_STAND` **2026-08-12 → 2026-08-16**. Jeder Messbefund gehört zu einem
Stand; die davor sind mit den neuen nicht vergleichbar.

| # | Fakt | wer bekommt ihn | Art |
|---|---|---|---|
| **F-160** | Abstand zur Zwangsauflösung bei 3-, 6- und 10-fachem Hebel — in Prozent **und** in Schwankungsbreiten | Rolle BC, **nur Hebel** | gerechnet, `1/Hebel` |
| **F-161** | Relative Stärke zum breiten Markt über 30 und 90 Handelstage | Rolle BC, **nur Themen-ETF** | gerechnet gegen SPY |
| **F-162** | Benennung fehlender Angaben: kein Umsatz · unter zwei Marken · Historie unter 250 Tagen | Rolle BC, alle | abgeleitet aus den Blöcken |
| **F-045** | Finanzierungsrate als Perzentil | Rolle BC **nur noch bei Hebel** — bei Spot jetzt allein Rolle G | unverändert |

### Die vier Fragen zu F-160

| | |
|---|---|
| **Ist er belegt?** | Ja — dieselbe Formel, mit der `entscheidungsrechnung` `liquidation_etwa_eur` rechnet. Keine zweite Definition |
| **Trägt er?** | Ungemessen. Die Praxisliteratur nennt ihn die zentrale Zahl einer gehebelten Entscheidung; unsere eigene Messung steht aus |
| **Ist er LLM-tauglich?** | Ja — Zahl mit Bezug. 33/17/10 % allein wären ein stehendes Feld (R-T6), erst die Schwankungsbreiten machen sie zu einer Aussage über *dieses* Asset |
| **Was kostet er?** | Nichts. Er wird ohnehin gerechnet, nur bisher **nach** dem Urteil |

### Der Wegfall bei Spot ist der ehrlichere Teil

Die Finanzierung wurde in **63 %** der Spot-Urteile als Beleg zitiert (O-34) —
für eine Zahlung, die ein Spot-Käufer weder leistet noch erhält. Sie war dort
zugleich der **dritte unabhängige Faktor**; ihr Wegfall kann `unabhaengige_faktoren`
von 3 auf 2 drücken und über `tranche_aus_faktoren()` den Betrag senken.

**Es kann also weniger und kleinere Spot-Signale geben.** Das ist kein
Einschränken: ein Faktor, der zur Sache nichts sagt, hat nie getragen. Und die
Information ist nicht weg — Rolle G liest dieselbe Rate, für Spot wie für Hebel.

### Zwei Altlasten, die dabei aufgefallen sind

**Die Klassen-Einstufung erreichte zwei von fünf Gruppen nicht.** `{"etf":
"aktien"}` war gegen die *Assetklasse* geschrieben, der Aufrufer übergibt die
*Gruppe* — bei `themen_etf` und `hedge` fand die Zuordnung seit dem 12.08. nie
einen Eintrag. Lautlos, weil ein fehlender Schlüssel kein Fehler ist.

**Die Mail zeigte andere Schwankungsbreiten als der Prompt.** Der Mail-Weg
rechnete die Blöcke ein zweites Mal und übergab den ATR in EUR, während der
Prompt-Weg die Quellwährung übergibt — bei USD-Assets um den Wechselkurs
daneben. Der zweite Aufruf ist gestrichen; Mail und Prompt benutzen jetzt
dasselbe Objekt.

### Was NICHT gebaut wurde

**Regime und Persistenz für Rolle A** — der fünfte grüne Schritt des Plans. Er
verletzt die Konstruktionsbedingung der zweiten Stufe: Rolle G hat beides seit
dem Morgen des 16.08., und ein Parameter gehört zu genau einem Modell.
Begründung und die offene Entscheidung stehen im Umbauplan, Kapitel 38.1.


## F-157 Momentum je Symbol: ein Feld von neun, nicht bestaetigt (20.08.2026)

FRAGE: Sagt die vergangene Entwicklung eines Kryptowerts relativ zu den
anderen etwas ueber seine kuenftige?

GEMESSEN: Rangliste quer ueber 40 Symbole am selben Tag, marktbereinigt,
3.290 Termine (2017-08-17 bis 2026-08-19), Newey-West-korrigiert, Schwelle
aus 40 Placebo-Laeufen.

BEFUND: 250 Tage Rueckblick / 5 Tage Horizont: +1,01 % Abstand zwischen
bestem und schlechtestem Fuenftel, t = 3,20 - erstmals ueber der Schwelle
3,05 und mit positivem Vorzeichen. 250/20 und 250/60 zeigen dieselbe
Richtung, ohne die Schwelle zu erreichen.

EINSCHRAENKUNG, DIE DEN BEFUND TRAEGT ODER STUERZT: das Signal liegt in der
nachgeladenen Historie (t=3,21 vor 2024-07-17, t=1,57 danach). Diese Zeit ist
auswahlverzerrt - die Reihen enthalten nur Werte, die es heute noch gibt, und
ein Wert steht auf der Liste, WEIL er einmal gelaufen ist. NICHT BESTAETIGT.

DER BELASTBARERE TEIL: 250 Tage Rueckblick / 60 Tage Horizont zeigt in
beiden Zeitraeumen dasselbe Vorzeichen und ist im unbelasteten Teil
signifikant (+10,70 %, t = 3,88, Nachweisgrenze 7,6 %). Auf 454
ueberlappenden Terminen in zwei Jahren.

FOLGE: kein Merkmal in der Mail. Weitermessen mit vorab festgelegten
Varianten (ausgelassener letzter Monat, volatilitaetsskalierte Rendite) und
auf einer anderen Anlageklasse.

WERKZEUG: messe_drift.py (--ab/--bis fuer die Zeitaufteilung, --placebo fuer
die Schwelle, --positivkontrolle fuer die Aussagekraft).


## F-158 Akkumulations-Signalmaß: es trägt — aber NICHT bei BTC/ETH/SOL (28.08.2026)

**Was gemessen wurde:** `V(t,H) = Mittel(Kurs[t+1..t+H]) / Kurs(t) − 1` —
die **Verbilligung**, das Erfolgsmaß, das `handelsauftrag.py` der Akkumulation
ausdrücklich gibt (*„Durchschnittskurs und Endvermögen statt Ziel vor Stop"*).
505 lückenlose Krypto-Reihen, 2017-08-17 .. 2026-08-21.

**Gemessen wird der Perzentilrang von V in der eigenen Reihe** — Basisrate
exakt 0,500 per Konstruktion, damit kann der Drift nicht als Signal durchgehen.

| Einordnung | |
|---|---|
| **Kategorie** | ✔ **gemessener Fakt** mit vollständigen Kontrollen |
| Vorteilsquelle (§9.1) | **Rückkehr zum Mittel** — nicht Drift, nicht Information |
| Gilt für | Krypto im Querschnitt (505 Reihen). Aktien/ETF **ungemessen** |
| ⚠️ **Gilt NICHT für** | **BTC, ETH, SOL** — die einzigen drei Werte, für die `spot × akkumulation` heute freigeschaltet ist |

⚠️⚠️ **DIE EINSCHRÄNKUNG IST DER KERN DES FAKTS.** Rang je Kernwert: BTC
**−0,0251** (p 0,723) · ETH **−0,0308** (p 0,810) · SOL **−0,0291** (p 0,855).

**Kein n=3-Rauschen:** Streuung je Symbol 0,0397, die Kernwerte liegen **2,39
Standardfehler** unter dem Mittel; nur **14,3 %** aller Symbole sind negativ —
alle drei Kernwerte darunter. **Nicht durch die Kursentwicklung erklärt:**
nach Gesamtentwicklung gefünftelt ist der Vorsprung konstant (+0,024 · +0,026
· +0,032 · +0,027 · +0,033, alle p < 0,005).

**Die Kennlinie ist monoton über alle neun Bänder, auf beiden Horizonten:**

| Abstand zum 200-Schnitt | Rang H=90 | Höhe H=90 | Rang H=365 | Höhe H=365 |
|---|---|---|---|---|
| **unter −40 %** | **+0,0960** | **+6,06 %** | **+0,0922** | **+5,39 %** |
| −7,5 .. 0 % | −0,0651 | −4,64 % | −0,0446 | −2,40 % |
| **über +30 %** | **−0,1508** | **−11,79 %** | **−0,1808** | **−15,77 %** |

**Sieben Gegenprüfungen bestanden:** Negativkontrolle (−0,0008 bei Null
±0,0007) · Positivkontrolle (+0,4242) · Rechenkontrolle (exakt 0) ·
Überlebende (bei **gefallenen** Reihen **stärker**) · Marktphase (beide
Hälften gleiches Vorzeichen) · Jensen/Log (identisch) · Saat (identisch).
⚠️ **Die achte — die Anwendungsfrage — nicht.**

⚠️ **Zwei eigene Konstruktionsfehler unterwegs, beide von den Kontrollen
gefangen:** ein Ausreißer-Mittelwert (eine Reihe mit +10.732 %) und ein
Verschub, der je Symbol ein anderer war. Nach der Korrektur wurde die
Nullverteilung **2,7-mal breiter** — und **RUECKGANG starb daran** (H=90,
p 0,000 → 0,060). Siehe Methodik **2.81**.

⚠️ **Was es nicht ist:** kein Alpha-Nachweis. Es sagt, **wann** innerhalb
einer Akkumulation gekauft wird — nicht, **ob** akkumuliert werden soll.

**Was für den Kern bleibt — Empfehlung B+C, keine Messfrage mehr:** fester
Takt **ohne** Verbilligungssatz in der Mail, plus die **Ausschlussseite**
(> +30 % über dem 200-Schnitt). Die Bremse ist unabhängig belegt und bei den
Kernwerten sogar am häufigsten gefordert (24,5 % ihrer Tage liegen in diesem
Band). ⚠️ **Die Kaufseite auf 502 kleine Werte auszuweiten, wäre der Fehler:**
Überlebensrisiko gegen Timing-Vorteil zu tauschen, bei Daten, in denen
delistete Währungen vollständig fehlen.

⚠️ **Es widerlegt den Buckel vom 27.08. in der Gegenrichtung** — dort war
*leicht* unter dem Schnitt am besten, hier ist *ganz tief* am besten. Kein
Widerspruch, sondern zwei Erfolgsmaße mit verschiedenen Kennlinien.

✔ **Bestätigt unabhängig die bestehende Ausschlussregel** (> +30 % über dem
Schnitt): mit −11,8 % bzw. −15,8 % das mit Abstand schlechteste Band.

**Vollständig:** `Befund_Akkumulationsmass_28_08.md` · Werkzeug
`messe_akkumulationsmass.py` · Dauerprüfung Paket **Akkumass**


## F-159 Der alte Weg ist stillgelegt, nicht gelöscht — und das ist der Stolperstein (28.08.2026)

**Nutzervorgabe:** *„ist wieder ein Stolperstein — prüfe wie kritisch es ist,
und wenn wir das so lassen, muss der Bereich sauber abgekapselt werden, damit
nichts mitläuft, wo wir später wieder ein Problem haben."*

### Der Stand, am Code geprüft (nicht vermutet)

| Weg | Gate | Status |
|---|---|---|
| **Rollen-Kette** `rollen_lauf.py` | — | ✔ **aktiv**, alle fünf Gruppen |
| Budget-Allocator → `krypto/pipeline` → `tranchen_erlaubt` | `background.py:3376` | ✖ übersprungen |
| Multi-Asset-Batch → `aktien/pipeline` u.a. → `tranchen_modul` | `background.py:3540` | ✖ übersprungen |

Ausgeführt: alle fünf Gruppen `bedient_neue_kette = True`, `_offen` leer.
✔ **Tranchen sind unerreichbar** — die Rollen-Kette importiert `agent/tranchen.py`
an keiner Stelle.

### ⚠️ Wie kritisch — die Messung des Schadens

`agent/multi_asset_batch.py` und `agent/krypto/budget_allocator.py` enthalten
das Wort `strategie` **null Mal**. Ein Rückfall braucht **keinen Fehler**: eine
Gruppe aus `rollen_kette.aktiv_fuer` zu nehmen genügt. Dann fehlen:

| | |
|---|---|
| **A** | `strategie` je Asset — alles wieder `einstieg`, **keine Akkumulation mehr** |
| **B** | Positionsführung — jedes Signal zählt wieder einzeln statt je Symbol |
| **C** | Akkumulation ohne Trailing — der Stop käme zurück |
| **L4/L5** | Cooldown je Strategie — wieder der Instrumentwert |
| **AZ-4** | Tranchen liefen wieder mit |

⚠️ **Und er wäre still gewesen:** beide Nahtstellen meldeten auf `info` — im Log
war ein Rückfall vom Normalbetrieb nicht zu unterscheiden. Der
Allocator-Zweig hatte **gar keine** Meldung.

### Die Abkapselung — vier Riegel

| | |
|---|---|
| **Gate** | beide Nahtstellen fragen `bedient_neue_kette` *(bestand schon)* |
| **Warnung** | `rollen_job.warne_alter_weg()` — **eine** Definition, zwei Aufrufer, auf `warning` statt `info`, mit `VERLUST_IM_RUECKFALL` als Folgenliste. Ohne Emoji: das Warnzeichen kam auf der Windows-Konsole als `⚠️` an |
| **Sichtbarkeit** | `agent/tranchen.py` weist sich im Docstring als **ABGEKAPSELT** aus — es steht *nicht* in der Toten-Liste der Modulkarte, weil es noch importiert wird, von Modulen, die selbst nie laufen |
| **Dauerprüfung** | Paket **Abkapselung** in `pruefe_pakete.py`, 11 Prüfungen |

⚠️ **Eine Grenze der Modulkarte, benannt:** sie findet Importe, **keine toten
Aufrufketten**. Ein Modul, das von einem nie laufenden Modul importiert wird,
sieht für sie lebendig aus.

### Nebenentscheidung: der Kern ist wieder der Kern

`_DCA_ERLAUBT_DEFAULT_SYMBOLS` von **16 auf 3** gekürzt (BTC, ETH, SOL). Die 13
Aktien/ETFs stammten aus der Tranchen-Zeit und stellten die GUI-Spalte auf
„An", **ohne auf die Strategie durchzuschlagen**. Die Spalte bleibt als
Anzeige der Standardkonfiguration — sie zeigt jetzt „Aus", was stimmt.

⚠️ **Nicht umbenannt:** `dca_erlaubt` / `asset_dca_settings` heißen weiter so,
obwohl DCA durch Akkumulation ersetzt ist. Nutzerentscheidung — eine
Umbenennung berührt Schema, GUI und sechs Module, ohne Verhalten zu ändern.
**Vorgemerkt, nicht offen.**


## F-160 B+C umgesetzt — die Akkumulation bekommt eine Lage-Zeile, keine Regel (28.08.2026)

**Nutzerauftrag:** *„B+C festlegen und umsetzen mit Prüfung und Gegenprüfung
wie immer."*

### ⚠️ C musste in der Gegenprüfung korrigiert werden, bevor es gebaut wurde

Die erste Fassung lautete *„für den Kern nur die Ausschlussseite nutzen"* —
begründet damit, dass die Bremse dort **am häufigsten greift** (24,5 % der
Tage). **Häufigkeit ist kein Beleg.** Nachgemessen zeigt das Band über +30 %
bei den Kernwerten teils die **Gegenrichtung**:

| | Rang H=90 | Rang H=365 |
|---|---|---|
| BTC | **+0,0112** | −0,0604 |
| ETH | **+0,0423** | +0,0284 |
| SOL | **+0,0605** | +0,0150 |

Eine Bremse darauf zu bauen wäre die *„Bremse ohne Potentialaussage"*, an der
dieses Projekt schon **79 %** seines Trichters verloren hat.

### ✔ Was die Gegenprüfung dafür geklärt hat — offene Frage 2 vom 27.08.

`Befund_Lage_27_08.md` hatte die Ausschlussregel **nur innerhalb tief
gefallener Assets** gemessen (Kurs ≤ 30 % des Hochs) und fragte, ob sie
darüber hinaus gilt. **Sie gilt:**

| Gruppe | Rang H=90 | Rang H=365 | Reihen |
|---|---|---|---|
| tief gefallen | −0,2063 | −0,0586 | 2 |
| **NICHT tief gefallen** | **−0,0924** | **−0,1450** | **363 / 329** |

Damit ist sie **breiter belegt als zuvor** — nur eben nicht für die drei
Werte, auf die sie heute träfe.

### Was gebaut wurde

`agent/akkumulationslage.py` — **sperrt nichts**, dieselbe Bauform wie
`agent/vorfilter.py`. Es schreibt zwei Zeilen in die Mail:

```
Lage         -40,8 % zum eigenen 200-Tage-Schnitt
             Erwartung +6,1 % guenstiger als ein beliebiger Tag dieser Reihe
             (Median ueber 90 Tage, 505 Reihen)
```

und für den Kern (**Entscheidung B**):

```
Lage         -40,8 % zum eigenen 200-Tage-Schnitt
             ACHTUNG: fuer BTC ist die Verbilligung NICHT belegt
             (Rang -0,03 bei p > 0,7) - dieser Wert wird gehalten, weil er
             ueberleben soll, nicht weil der Zeitpunkt guenstig ist
```

⚠️ **`belegt=False` ist nicht `belegt=None`** — für BTC/ETH/SOL ist gemessen,
dass es *nicht* trägt; das ist etwas anderes als „nie geprüft". Dieselbe
Unterscheidung wie `h = None` gegen `h = False` im Vorfilter.

**H=90 und nicht H=365**, obwohl der Vorsprung dort größer ist: der längere
Horizont hat bei 3.292 Tagen Achse nur rund neun unabhängige Fenster, H=90 hat
36. **Die vorsichtigere Zahl gehört in eine Mail.**

### ⚠️ Der Bau kostete einen selbst gebauten Fehler — Methodik 2.82

Der Import hieß `_AKL` — ein Name, der in `rollen_lauf.py` seit Zeile 50
belegt ist. Damit wurde er **lokal**, und zwei frühere Zugriffe warfen
`UnboundLocalError`, den der breite Fehlerfang schluckte: **keine Mail, kein
Signal, keine erkennbare Ursache.** Neue Dauerprüfung **T4c**;
`finde_freie_namen.py` findet diese Klasse **nicht**.

**Suite: 1.726 Prüfungen, alle bestanden** (Paket `Akkumulationslage` mit
Naht-Nachweis am **fertigen Mailtext**, Paket `T4c`).


## F-161 L2 war längst erledigt, L3a war es nicht (28.08.2026)

**Nutzerauftrag:** *„mach L2 und L3 — mit Prüfung und Gegenprüfung."* Die
Pflichtprüfung *„ein Planschritt gilt erst als offen, wenn der Code das
bestätigt"* hat einen der beiden erledigt, bevor er gebaut wurde.

### ✔ L2 — „Kern-Assets können keinen Hebel bekommen": **geschlossen durch A**

Am Code gemessen, nicht vermutet:

| Symbol | Instrument | Strategie | Hebel-Prüfung |
|---|---|---|---|
| BTC / ETH / SOL | spot | `akkumulation` | — |
| BTC / ETH / SOL | **hebel** | **`einstieg`** | **erlaubt (True)** |

`strategie_fuer()` prüft `if i != "spot": return vorgabe` — der Kern-Schalter
greift **nur** auf der Spot-Seite. `asset_schalter` sperrt den Kern nirgends
explizit. **Die Trennung, die L2 forderte, ist seit dem 27.08. da.**

### ⚠️ Der Nebenbefund, der schwerer wiegt als L2

```
INSTRUMENTE_JE_GRUPPE = { "krypto": ("spot",), ... }
```

**Die Rollen-Kette fährt Krypto überhaupt nicht als Hebel.** `laeufe()` liefert
für krypto genau einen Lauf: `spot`. Hebel entsteht ausschließlich über
`hebel_screening_job` und dessen eigenen Schalter
(`get_hebel_pruefung_erlaubt`) — nicht über den Umlauf.

> ⚠️ **KORRIGIERT AM 28.08. ABENDS.** Dieser Satz war zur Hälfte falsch. Der
> Hebel läuft **nicht** über das Screening, sondern fällt seit S6b (22.08.)
> aus der **Rechnung** an — `hebel = verlustanteil / stop_rel`, Kapitel 88:
> *„Hebel als Ergebnis statt als Kategorie"*.
>
> ⚠️ **Und `get_hebel_pruefung_erlaubt` wird gar nicht mehr gefragt:**
> `asset_schalter.py:89` prüft `if i == "hebel"`, und `instrument` ist seit
> S6b immer `"spot"`. **Der Schalter des Nutzers ist wirkungslos.**
> Vollständig: `Befund_Instrument_nach_S6b_28_08.md`.

⚠️ **Das gehört zur offenen Nutzerfrage** *„haben wir nun echte Hebelsignale
oder nur verkappte Spot?"* — und es ist **kein** Ergebnis von L2, sondern eine
Struktureigenschaft, die vorher nirgends festgehalten war.

### ✔ L3a — die Liquidation gehört an das Signal: **gebaut**

**Der Befund:** `entscheidungsrechnung` rechnet `liquidation_etwa_eur`
(Zeile 759), die Mail nennt sie (Zeile 944) — **gespeichert wurde sie nie.**
In `signals` fehlte die Spalte, und `felder_aus_entscheidung` ließ das Feld
deshalb **stillschweigend** fallen. Genau die Falle, die der eigene Docstring
dort für andere Felder beschreibt.

⚠️ **Rückwirkend nicht nachrüstbar.** Die Frage *„lagen unsere Hebel-Signale
näher an der Liquidation, wenn sie scheiterten?"* ist für alles Bisherige
dauerhaft unbeantwortbar. `hebel_positions` hat den Wert — aber das ist die
**Position**; ein Signal, das nie zur Position wurde, hinterlässt dort nichts.

**Vier Stellen, die zusammen wachsen mussten** — die Suite hat drei davon
erzwungen:

| Stelle | |
|---|---|
| `signal_abbildung.SPALTEN_SIGNAL` | die Spalte, additiv und idempotent |
| `felder_aus_entscheidung` | ⚠️ **nur bei Hebel** — für Spot wäre eine Null eine erfundene Zahl |
| `models.Signal` | ✖ **von der Suite gefangen**: `Signal` wird aus `SELECT *` gebaut, eine Spalte ohne Feld **kappt jeden Lesepfad** |
| `extract_notebook_diagnose` | ✖ **von der Suite gefangen**: sonst ist die Spalte am Notebook unsichtbar |

**Nachgewiesen, nicht behauptet:** Paket `L3` (6 Prüfungen) schreibt gegen das
**echte** Schema (`init_db`, nachdem eine Minimalattrappe an `gate_passed`
brach) und **liest den Wert aus der Tabelle zurück**. Die Simulation bestätigt,
dass die Migration im Betrieb greift.

### ⚠️ L3b — Finanzierungskosten: **nicht gebaut, und zwar bewusst**

Zwei Gründe, beide inhaltlich:

1. **Es gibt keinen hinterlegten Satz.** Weder `config.yaml` noch der Code
   kennen einen Finanzierungssatz für Hebelprodukte. Einen zu erfinden hieße,
   eine Zahl zu bauen, die aussieht wie eine gemessene.
2. **Die Nutzervorgabe spricht dagegen**, sie in die Bewertung zu nehmen:
   *„Spot und Hebel haben beides Kosten für die Wirtschaftlichkeit und je nach
   Haltedauer, aber diese können wir zum Zeitpunkt der Handelsentscheidung
   nicht voraussagen — aber das wollen wir auch nicht mehr."*

✔ **Was daraus folgt:** Finanzierungskosten gehören wie die 1,50 % in die
**Mail**, nicht ins Potential — und dafür braucht es den echten Satz vom
Nutzer oder von Bitpanda. **Offen, mit benanntem Grund.**

**Suite: 1.732 Prüfungen, alle bestanden.**
