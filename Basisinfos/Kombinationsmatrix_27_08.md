# Welche Merkmalskombinationen wurden geprüft — und welche nie

**Angelegt 27.08.2026.** Nutzerauftrag: *„mach das systematisch — welche
Kombinationen wurden nie geprüft?"*

⚠️ **Meine erste Einschätzung war falsch.** Ich hatte vermutet, das Projekt
habe *„überwiegend Einzelmerkmale getestet"*. Die Durchsicht der **75
Messwerkzeuge** zeigt das Gegenteil: **Kombinationen sind der Regelfall.**
Was fehlt, ist etwas anderes — siehe Abschnitt 4.

---

## 1. Die Merkmale, die das Projekt kennt

| # | Merkmal | Quelle | trägt? |
|---|---|---|---|
| **M1** | **Weg frei + Stop gedeckt** (H) | `vorfilter.py` | ✔ **+4,5 Punkte** — der einzige |
| M2 | Rangplatz / Reihung | `auswahl.py` | ⚠️ **negativ** (−5,8 innerhalb H) |
| M3 | Drift (250-T-Rendite) | `drift.py` | ✘ |
| M4 | Liquidität / Amihud | `marktlage` | ✘ |
| M5 | Umsatzkategorie (Large/Mid/Small) | `messe_klassen` | ⚠️ kippt bei sauberen Grenzen |
| M6 | Ankeralter / Reife | `messe_reifeband` | ⚠️ episodisch |
| M7 | Marktphase / Regime | `regime.py` | ⚠️ Confounder, kein Merkmal |
| M8 | Sentiment (Fear & Greed) | `macro_snapshot` | ⚠️ ungemessen als Auslöser |
| M9 | Umschlag | `lagebeschreibung` | ✘ (t 0,85 gegen 1,65) |
| M10 | Marken / Struktur | `lagebeschreibung` | ✔ = Bestandteil von M1 |
| M11 | Geometrie (CRV, Stopabstand) | `entscheidungsrechnung` | ⚠️ **EW null für jede** |
| M12 | Horizont | Messparameter | — |
| M13 | **Terminmarkt** (OI, Funding, Divergenz) | `positionierung.py` | ⚠️ **eigener Kanal**, Wirkung ab 22.10.2026 |
| M14 | Entwickleraktivität | `messe_entwickleraktivitaet` | ⚠️ Daten ab 09.11.2026 |
| M15 | Lage zum 200-Schnitt | `auswahl.py` | ⚠️ nur als Ausschluss (−11,2 Punkte) |
| M16 | Konfidenz des Modells | `signals` | ✘ (r = +0,073) |
| M17 | Marktbreite | `marktbreite.py` | ⚠️ **invers** — gestrichen 12.08. |

---

## 2. Geprüfte Kombinationen — 14 an der Zahl

| Kombination | Werkzeug | Ergebnis |
|---|---|---|
| **M1 selbst** (frei **und** gedeckt) | `messe_marken` | ✔ trägt — H ist bereits eine Konstellation |
| M1 × M2 (Reihung) | `messe_reihung_x_h` | ⚠️ **negativ** — innerhalb H schneidet das beste Fünftel 5,8 Punkte schlechter ab |
| M1 × M4 (Liquidität) | `messe_liquiditaet` | Vorbedingung, kein Zugewinn |
| M1 × M5 (Klasse) | `messe_klassen` | Large +5,9 · Mid +2,5 · Small +7,9 — ⚠️ S3: Large kippt |
| M1 × M6 (Alter) | `messe_reifeband` | trägt nur 250–499 (+5,24) |
| M5 × M6 | `messe_kat_alter` | ⚠️ diagonal, keine Achse allein erklärt es |
| M6 × M7 (Alter/Zeit) | `messe_alter_vs_zeit` | ⚠️ **nicht trennbar** (2.79) |
| M1 × M11 × M12 (Dosis) | `messe_dosis`, `_sauber` | Geometrie und Dauer gemeinsam |
| M11 × M15 (Geometrie/Lage) | `messe_geometrie` | — |
| Tagewahl × 8 Eigenschaften | `messe_tagewahl_je_eigenschaft` | ⚠️ **alle flach**, größter Betrag 0,16 |
| M9 × Kontext | `messe_umschlag_kontext` | ✘ |
| M8 × M12 (Sentiment/Horizont) | `messe_sentiment_je_horizont` | — |
| Regimeflag × Triggerrichtung (2×2) | `messe_regimeflag_sauber` | — |
| Kettennaht (2×2 faktoriell) | `messe_kettennaht_eingriffe` | — |
| **Kollinearität** (sind es drei Hebel oder einer?) | `messe_kollinearitaet` | — |
| **Faktorzahl** (steigt die Quote mit der Anzahl?) | `messe_faktorzahl` | nur Werte 2 und 3 |
| **Dritter Faktor** (kausaler Test) | `messe_dritter_faktor` | — |

---

## 3. ⚠️ Nie geprüfte Kombinationen

**Alle mit M1, weil M1 der einzige tragende Baustein ist:**

| Kombination | warum nie | Vorbedingung |
|---|---|---|
| **M1 × M13** (H × Terminmarkt) | ⚠️ **die interessanteste** — M13 ist der einzige *eigene Kanal* (ρ 0,034/0,195/0,250 zu ATR/Umsatz/Rendite) | Daten ab **22.10.2026** (H20) |
| **M1 × M8** (H × Sentiment) | F&G liegt mit 3.125 Tagen vor, nie gegen H geschnitten | ✔ **sofort möglich** |
| **M1 × M15** (H × Lage) | Lage ist als Ausschluss belegt (−11,2), nie mit H gekreuzt | ✔ **sofort möglich** |
| M1 × M14 (H × Entwickler) | Daten fehlen | ab 09.11.2026 |
| M13 × M8 (Terminmarkt × Sentiment) | beide ungemessen | ab 22.10.2026 |
| **Drei-Wege** (M1 × X × Y) | ⚠️ **keine einzige** — alle Prüfungen sind 2×2 oder Schnitte | Fallzahl |

⚠️ **Und die strukturelle Grenze:** H trifft **3,3 %** der Ankertage. Jede
Kombination *innerhalb* H halbiert die Menge weiter. Bei 19.891 Ankern sind
das 656 H-Fälle; ein Zwei-Wege-Schnitt darin lässt ~300 je Zelle — knapp über
`MIN_FAELLE`. **Ein Drei-Wege-Schnitt ist mit dieser Basis nicht messbar.**

---

## 4. Was wirklich fehlt — und es ist nicht die Kombination

**Die Durchsicht zeigt: Das Projekt hat systematisch kombiniert.** Was es nicht
hat, ist etwas anderes:

| | |
|---|---|
| ⚠️ **Ein zweiter tragender Baustein** | von 17 Merkmalen trägt **eines**. Jede Kombination aus einem tragenden und einem nicht tragenden Merkmal kann bestenfalls das erste bestätigen |
| ⚠️ **Merkmale außerhalb der Kursreihe** | M2–M12 und M15–M17 sind alle aus Kurs, Volumen oder Modellantwort abgeleitet. **M13 und M14 sind die einzigen echten Fremdquellen** — und beide noch nicht auswertbar |
| ⚠️ **Ein Erfolgsmaß, das nicht auf die Basisrate fällt** | N-10: „Ziel vor Stop" fällt per Konstruktion auf `1/(1+CRV)`. Alle Nullbefunde hängen daran |

**Der Grundbefund vom 10.08. bleibt damit unangetastet:** *„Die Information
steckt nicht in den Kursdaten."* Wer nur Kursreihen kombiniert, kombiniert
Ableitungen derselben Quelle.

---

## 5. Was daraus folgt — zwei sofort mögliche Messungen

| | Frage | Aufwand | warum lohnend |
|---|---|---|---|
| **K-A** | **Trägt H zusätzlich bei extremem Sentiment?** | F&G liegt vor, H ist gerechnet | erste Kombination aus Kurs**struktur** und **Stimmung** — zwei verschiedene Quellen |
| **K-B** | **Trägt H zusätzlich, wenn die Lage nicht extrem ist?** | beides vorhanden | die Lage ist als **Ausschluss** belegt; als Filter *vor* H könnte sie die 3,3 % verbessern |

⚠️ **Beide sind Zwei-Wege-Schnitte innerhalb H** — die Fallzahl reicht knapp,
und der Suchpreis für zwei vorab benannte Zellen ist zu zahlen (+10,2 Punkte
je Zelle statt +20,5 bei freier Suche).

**Und die ehrliche Erwartung:** Beide messen weiterhin nur Ableitungen der
Kursreihe (M8 ist ein Stimmungsindex, aber er folgt dem Kurs). Der einzige
Kandidat auf **neue Information** bleibt M13 — ab dem 22.10.2026.

Verwandt: `Roter_Faden_27_08.md` · `Konzept_Einstiegsbewertung_23_08.md` §9.1 ·
`Test_und_Verifikationsmethodik.md` 2.49 (Suchpreis), 2.79, 2.80
