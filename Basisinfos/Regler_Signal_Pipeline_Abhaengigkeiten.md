# Regler/Signal-Pipeline-Abhängigkeitsmatrix

**Zweck:** Dauerhaftes Referenzdokument (analog `Fakten_Entscheidungsmappe.md`
und `Test_und_Verifikationsmethodik.md`), kein einmaliger Audit. Die
Signal-Pipeline läuft in drei Stufen — Stage 1 (Deterministisch/Regler:
`risk_gate.py`/`hebel_risk_gate.py` + Vorfilter wie `budget_allocator.py`),
Stage 2 (LLM1/Analyst: `analyst.py`/`hebel_analyst.py` + die 4 weiteren
Spot-family-Analysten), Stage 3 (LLM2/Z.ai-Gegenprüfung). Eine Änderung in
einer Stufe wirkt oft unbemerkt in eine andere durch — dieses Dokument
sammelt bekannte Kopplungen, damit sie vor jeder künftigen Regler-/Prompt-
Änderung geprüft werden können, statt beim "Regler probieren" wieder von
vorne anzufangen.

**Entstehung:** 02.08.2026, im Rahmen der Dead-Loop-Synthese (Task #598,
siehe Memory `project_dead_loop_synthese_root_cause.md`). Erste Bündelung
bereits bekannter, aber bisher über Dutzende Einzel-Memories verstreuter
Kopplungen — kein vollständiger Neu-Audit aller Regler. Bei jeder künftigen
Änderung an einem hier gelisteten Element: Zeile aktualisieren oder neue
Zeile ergänzen.

---

## Bekannte Abhängigkeitsketten

| Element (Stufe) | Wirkung auf Stage 2 (LLM1) | Wirkung auf Stage 3 (LLM2/Z.ai) | Warum wichtig |
|---|---|---|---|
| `hebel_richtung_modus="nur_long"` (Stage 1, Vorfilter in `budget_allocator.py`, vor jedem LLM1-Call) | SHORT-Kandidaten erreichen Mistral nie — LLM1 sieht nur LONG-Kontext | Z.ai-SHORT-Urteile erscheinen strukturell fast immer als "Abweichung" von Mistral (das SHORT nie empfehlen kann) | Jede Interpretation der Z.ai-Richtungs-Übereinstimmungsquote MUSS das mitdenken — sonst wird ein Konfig-Artefakt für ein Kalibrierungsproblem gehalten. Bereits einmal genau so passiert (siehe `project_zai_gegenpruefungslogik.md`, "0b. ERLEDIGT") |
| CRV-Mindestschwelle `CRV_MINIMUM=2.0` (Stage 1, Regler in `risk_gate.py`/`hebel_risk_gate.py`) | bestimmt Anteil LLM1-Empfehlungen → HALTEN zurückgestuft (Veto-Schatten-Population) | Z.ai bekommt nur die Gate-überlebende Teilmenge zu Gesicht | Eine Schwellen-Änderung verschiebt die Z.ai-Vergleichspopulation unbemerkt mit — jede Vorher-Nachher-Z.ai-Auswertung nach so einer Änderung braucht eine neue Baseline, kein direkter alt-vs-neu-Vergleich |
| R-5.10-Konfidenzschwelle (Stage 1, Regime-Profil-Regler) | dieselbe Kopplung wie CRV oben | dieselbe Kopplung wie CRV oben | siehe oben |
| Preiszonen-Validierung `von>bis` (Stage 2, `_validate()` in allen 6 Analyst-Dateien, seit 02.08. Auto-Korrektur statt Ablehnung) | — | — | Die Zonenwerte fließen direkt in Stage 1s CRV-Formel (`risk_gate.py`/`hebel_risk_gate.py`, wählt `von`/`bis` rein numerisch nach Lage, nicht nach LLM-Reihenfolge). Ein unkorrigierter Tausch hätte dort eine FALSCHE CRV-Berechnung erzeugt, nicht nur einen Validierungsfehler — der Fix schützt also Stage 1 mit |
| `top_gruende.kategorie` (Stage 2, Schema, Rohstoff/Themen-ETF seit 02.08. mit "fundamental"-Alias) | — | — (Cross-Cutting/Meta-Stufe) | Wird von `compute_selbst_halten_performance_nach_grund()` als Gruppierungsschlüssel genutzt — eine inkonsistente Kategorievergabe in Stage 2 verzerrt später die Meta-Messung, ohne dass das in Stage 2 selbst sichtbar wird |
| Regel 27 "Action-Bias-Korrektur" (Stage 2, Prompt in `hebel_analyst.py`) | erhöht Anteil HALTEN ohne Gate-Veto (>95% aller Hebel-Signale) | reduziert Menge an ERÖFFNEN-Kandidaten, die Z.ai überhaupt bewertet | Genau die Population, die erst seit 31.07. (Selbst-Halten-Schatten-Tracking) überhaupt sichtbar ist — vor diesem Fix wäre eine Prompt-Änderung wie Regel 27 spurlos an jeder Messung vorbeigegangen. Direkt mitverantwortlich für RC2 (siehe Dead-Loop-Synthese) |
| `eigene_einschaetzung.folgen` (Stage 2, Signal-Fazit-Pflichtfeld) | — | — (Cross-Cutting) | Einzige Datenquelle für die Fazit-Selbsteinschätzung-Kalibrierung — kein Backup, wenn das Feld fehlt (7 der 27 Validierungsfehler aus Maßnahme 1 betrafen genau dieses Feld) |
| `_is_superseded()`-Logik (Cross-Cutting, `backward_tracking.py`/`hebel_backward_tracking.py`, Fix 19.07.) | — | — | Bestimmt, ob ein offenes Signal überhaupt bis TP/SL "überleben" kann, bevor es als "überholt" gilt. Betrifft ALLE Stage-2/3-Messungen gleichzeitig — der historische Bug (jedes neuere HALTEN überholte praktisch jedes offene Signal) erklärt rückwirkend einen Großteil der über Wochen kleinen Stichproben (RC1) |
| **RM-1b** Enge-Stop-Veto 2,5% + **RM-1c** ATR-relative Untergrenze 0,75x (Stage 1, `risk_gate.py`/`hebel_risk_gate.py`, beide 02.08.) | stufen ERÖFFNEN/KAUFEN vor dem CRV-Check zu HALTEN zurück - vergrößern also die Veto-Schatten-Population | Z.ai sieht diese Signale nicht mehr als Handelsempfehlung | **Dieselbe Kopplung wie CRV_MINIMUM oben, und sie kommt ZUSÄTZLICH** - der Z.ai-Nenner verschiebt sich seit 02.08. aus zwei neuen Gründen. Jede Z.ai-Auswertung, die Daten von vor und nach dem 02.08. mischt, vergleicht verschiedene Populationen. RM-1b greift laut Messung bei ~3,6% der Signale, RM-1c bei ~1,8% (Überschneidung fast vollständig) |
| **RM-1 exakt** + **RM-1d** Ziel-Positionszahl (Stage 1, `risk_gate.py::_rm1_exakt_und_positionszahl()`, 02.08.) | **keine** - verändern nur die Positionsgröße, nicht die Kandidatenmenge | **keine** | Bewusst hier vermerkt, damit die Abwesenheit einer Kopplung dokumentiert ist: beide wirken NACH der Aktionsentscheidung und ändern kein `action`. Wer sie später verschärft, muss diese Zeile prüfen - sobald daraus ein Veto würde (statt einer Größenkorrektur), entstünde dieselbe Nenner-Verschiebung wie bei RM-1b/1c. Reihenfolge beachten: beide korrigieren die BASIS, auf der die vier Anteils-Deckel (Konfidenz/Gegenszenario/technischer Konflikt/CRV-knapp) danach rechnen |
| **RM-11 exakt** (Stage 1, `hebel_risk_gate.py::_hebel_deckel_kandidaten()`, 02.08.) | **keine** - senkt nur den Hebel, kein `action`-Wechsel | **keine** | Weiterer Kandidat in der bestehenden `min()`-Kette neben Config-Maximum, RM-11 vorab, Regime-Konflikt und Gegenszenario. Wichtig beim Debuggen: der genannte "bindende Grund" kann seit 02.08. auch "RM-11 exakt" lauten - das ist kein Fehler, sondern der tatsächliche Stop, der die Vorab-Schätzung (2,0x ATR) unterbietet |
| Statistik-Prüfungen `win_rate_ci_95`/`crv_konzentration` (Cross-Cutting, `backward_tracking.py::_kennzahlen_mit_pruefung()`, 02.08.) | — | — | Verändern keine Pipeline, aber die **Interpretation** aller drei Aggregationen. `crv_konzentration.vorzeichen_kippt=True` heißt: der Mittelwert dieser Gruppe hängt an wenigen Ausreißern und trägt keine Regeländerung. Wer eine Regel auf `avg_realisiertes_crv` stützt, ohne dieses Feld zu prüfen, wiederholt den AIOZ-Fehler vom 02.08. |

| **RM-5 → RM-1** Volatilität steckt bereits in der Positionsgröße (Stage 1, `risk_gate.py:253-268`) | — | — | **Nachgetragen 04.08., hatte gefehlt.** RM-5 setzt den Stop auf `2 × ATR`, RM-1 rechnet `Positionsgröße = Risikobudget ÷ Stop-Abstand` — die Größe ist damit **proportional zu 1/ATR**, also lehrbuchmäßiges Volatility Targeting, seit Beginn eingebaut. Wer eine Volatilitäts-Komponente in die Positionsgröße einbaut, zählt sie ein **zweites** Mal. Genau das passierte am 04.08. bei der Positionsgrößen-Messung: die Variante "nur Volatilität" schnitt signifikant SCHLECHTER ab (−0,029 R je Signal, Intervall [−0,051 .. −0,008]) und wäre ohne diesen Kontrollfall als Literaturempfehlung eingebaut worden. Volatilität ist an drei Stellen im System: hier (Positionsgröße), RM-1c (Stop-Untergrenze 0,75× ATR) und Regel 6 (TP-Leitplanke ~1,5–2× ATR) |

## Regler-Klassifikation (Audit 04.08., Task #610/#611)

Von 202 Blatt-Schlüsseln in `config.yaml` werden 36 im Produktivcode nie
namentlich gelesen. Die Suche muss ohne Ausschlussfilter laufen — der erste
Durchgang schloss `analyse_*.py`, `backtest_*.py` und
`extract_notebook_diagnose.py` aus und hätte eine Verwendung als
Mess-/Analysegrundlage übersehen (Nutzer-Fund).

**Drei Kategorien, die auseinandergehalten werden müssen:**

| Kategorie | Kennzeichen | Behandlung |
|---|---|---|
| **Fehlalarm** | Name wird dynamisch zusammengebaut | Nicht anfassen. Beispiel: `gewicht_*` — `hebel_screening.py:200` baut `f"gewicht_{kategorie}"`. Textsuche findet das nicht |
| **Attrappe** | Verhalten existiert, ist aber hartkodiert; der Schlüssel steuert nichts | Entfernen **mit Begründung an Ort und Stelle**, nicht spurlos. Wenn der Config-Wert zusätzlich vom echten Verhalten abweicht, ist es kein harmloser Rest, sondern irreführend |
| **Nie umgesetzt** | Weder Schlüssel gelesen noch Verhalten vorhanden | Eigene Entscheidung je Fall — bauen, verwerfen oder als offen markieren |

**Entschieden und umgesetzt (04.08.):**

- `api_key_noetig`, `rate_limit_pro_minute` — entfernt. Letzterer war
  irreführend: 30 ohne, 100 **mit** API-Key. Kein Drossel-Regler als Ersatz,
  weil die wirksame Bremse bei der ANZAHL der Abfragen sitzt (Marktscan
  USD-only + `stufe_b_top_n_deckel`), nicht beim Takt — gegen ein
  Monatskontingent hilft langsamer nichts.
- `max_hebel_faellt_regime_krise_extrem_auf_null`, `aus_bei_krise_extrem` —
  Dublette, beide entfernt. **AZ-7 ist bewusst ein hartes Gate ohne Regler.**
  Notausstieg liegt beim `regime.manueller_override` (RG-8), weil die
  Regime-Einstufung träge ist und die Krise vorbei sein kann, während die
  Einstufung noch steht.
- `begruendung_pflicht` (Z-4), `liquidationspreis_ausweisen` (RM-11),
  `ema_perioden`, `rsi_periode`, `forecast_szenarien` — entfernt. Die
  Config-Werte beschrieben das Verhalten korrekt, steuerten es aber nicht.
  Genau diese Sorte verleitet dazu, in der Config nachzusehen statt im Code.
- `gestaffelt_kaufen` (AZ-4) — entfernt. **Lehre aus diesem Fall:** Erst hielt
  ich ihn für reine Aufräumarbeit, dann für eine Abweichung zwischen
  Spezifikation („nie all-in") und Umsetzung (Erlaubnis für drei Symbole).
  Beides falsch — die Spezifikation dokumentiert in Kap. 15 vollständig, was
  gebaut wurde, samt aller drei Einschränkungen (Regime baer/krise_extrem/
  seitwaerts, nur BTC/ETH/SOL, Toggle je Asset) und der strukturellen Grenze:
  Bitpanda hat keine Handels-API, das System kann Tranchen nur EMPFEHLEN.
  Der Fehler entstand, weil ich aus einer bei `→` abgeschnittenen Grep-Zeile
  geschlossen habe, statt den Absatz zu lesen. **Regel für alle weiteren
  AZ-Fälle: zuerst den Spezifikationsabsatz vollständig lesen, dann die
  Codesuche** — nicht umgekehrt.

**Als unerfüllt dokumentiert (04.08.):** `fundamental_gate` (AZ-5). Weder Gate
noch Prompt-Regel. Für Krypto fehlt die Datengrundlage („Substanz" hat keine
bilanzielle Entsprechung, Ersatzgrößen werden nicht abgerufen), für Aktien wäre
es machbar, aber bei 7 auswertbaren Signalen über Monate nicht überprüfbar.
Bewusst NICHT gebaut und in Spezifikation Kap. 15 mit Begründung und
Wiedervorlage-Bedingung vermerkt, statt stillschweigend offen zu bleiben.

**Strukturelle Lücke, die dabei sichtbar wurde:** AZ-8 beschreibt das
Schutzkonzept des antizyklischen Kapitels und nennt sechs
Schaltkreis-Unterbrecher — **zwei davon existierten nicht**, das Fundamental-Gate
(AZ-5) und die Drawdown-Notbremse (Z-3).

**Nachtrag 2026-08-04:** Z-3/RM-7 ist umgesetzt (Task #612) — Tabelle
`portfolio_wert_historie`, `agent/portfolio_historie.py`, tägliche Prüfung 6:30
durch `portfolio_wert_job()`. Damit fehlt von den sechs nur noch AZ-5, das
bewusst als unerfüllt dokumentiert ist. Wer sich auf AZ-8 beruft, muss also
noch eine Lücke mitdenken statt zwei.

**Wichtig für künftige Regler-Entscheidungen:** Z-3 rechnet auf einer
MENGENKONSTANTEN Wertreihe, nicht auf dem rohen Portfoliowert. Wer eine
weitere Regel auf Portfolio-Ebene baut, sollte dieselbe Unterscheidung treffen —
sonst reagiert sie auf eigene Handelsaktivität statt auf den Markt.

**Offen (#611):** `max_drawdown_prozent` (Z-3, in keinem Dokument außer der
Config, nie umgesetzt — und laut AZ-8 einer der tragenden Unterbrecher), der
Rest des `antizyklisch`-Blocks (nirgends gelesen — soweit vorhanden lebt das
Verhalten als Prompt-Text auf Stage 2, während die Config Stage 1 suggeriert),
sowie `auto_watchlist` (verspricht automatische Aufnahme, real ist es ein
manueller Button in `marktscan_view.py:568`).

**Nebenbefund:** Die Parameter-Übersicht der Remote-Seite
(`regelwerk_parameter.py::_PARAMETER`) umfasst 34 handverlesene Einträge von
rund 200 Schlüsseln. Z-3 steht nicht darin — ein definiertes Systemziel fehlt
in der Aufstellung der geltenden Parameter. Die Auswahlregel dieser Liste ist
selbst ungeklärt.

## Wie diese Matrix zu pflegen ist

- Vor jeder Regler-Änderung (Stage 1) prüfen: verändert sie die an Stage 2
  übergebene Kandidatenmenge? Falls ja, hier eine Zeile ergänzen und bei
  jeder Stage-3-Auswertung danach die Baseline-Verschiebung mitdenken.
- Auch das FEHLEN einer Kopplung eintragen (siehe RM-1 exakt/RM-1d/RM-11
  exakt): sonst prüft die nächste Änderung dieselbe Frage von vorne, und
  eine spätere Verschärfung - aus einer Größenkorrektur wird ein Veto -
  bleibt unbemerkt.
- Nachtrag 02.08.: an einem Tag kamen vier neue Gates dazu, ohne dass diese
  Matrix mitgezogen wurde. Sie stand danach mehrere Stunden unvollständig da
  und hätte die nächste Änderung in die Irre geführt. Die Matrix gehört in
  denselben Commit wie die Regel, nicht in einen Aufräumdurchgang danach.
- Vor jeder Prompt-/Schema-Änderung (Stage 2) prüfen: wird das betroffene
  Feld irgendwo als Berechnungsgrundlage (Stage 1, z.B. CRV-Formel) oder als
  Gruppierungs-/Filterschlüssel (Meta-Stufe) weiterverwendet?
- Neue Erkenntnisse aus Einzel-Untersuchungen (Memory-Dateien) hier als Zeile
  nachtragen, sobald eine Kopplung über eine einzelne Stufe hinaus entdeckt
  wird — nicht nur in der Einzel-Memory belassen.

Verwandte Dokumente: `Fakten_Entscheidungsmappe.md` (Frage-1-4-Raster für
einzelne Fakten, komplementär zu dieser stufenübergreifenden Sicht),
`Test_und_Verifikationsmethodik.md` (Statistik-Standards für jede Messung,
die von diesen Abhängigkeiten betroffen ist).
