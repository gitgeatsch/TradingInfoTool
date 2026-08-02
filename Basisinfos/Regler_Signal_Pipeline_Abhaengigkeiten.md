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

## Wie diese Matrix zu pflegen ist

- Vor jeder Regler-Änderung (Stage 1) prüfen: verändert sie die an Stage 2
  übergebene Kandidatenmenge? Falls ja, hier eine Zeile ergänzen und bei
  jeder Stage-3-Auswertung danach die Baseline-Verschiebung mitdenken.
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
