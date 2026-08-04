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
- `regime.fear_greed.wert`/`.einstufung` — **keine Regel in beiden Prompts, keine Gate-Nutzung.** Siehe 3.2.
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

