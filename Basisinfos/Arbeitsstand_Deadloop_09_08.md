# Arbeitsstand Deadloop — lebende Datei, Stand 2026-08-09

**Zweck:** Diese Datei ist der Anker gegen Informationsverlust zwischen Sessions.
Sie enthält den Stand der Deadloop-Untersuchung, die getroffenen Entscheidungen
und die offenen Fäden. **Wer hier weiterarbeitet, liest zuerst diese Datei** —
und trägt jede Erkenntnis hier nach, bevor er sie im Chat berichtet.

---

## 1. Der Deadloop, mechanisch geschlossen

Drei Ebenen wirken zusammen. Nur eine davon ist behebbar.

| Ebene | Wirkung | Herkunft | behebbar? |
|---|---|---|---|
| **Broker** | nur LONG ausführbar | Bitpanda kann kein Krypto-Short — **RM-10 im Regelwerksmanual**, ausdrücklich *keine* Risiko-Entscheidung, sondern ein Broker-Fakt | **nein** (Kompromiss: inverse ETPs DBPK/3QSS — die haben null Kursdaten) |
| **Markt** | Bärenregime → Modell wählt korrekt SHORT | 82,7 % SHORT in der Produktion; im simulierten BÄR-Arm 83,3 % | **nein** |
| **Unsere Fakten** | drücken **LONG-Konfidenz in jedem Regime**, SHORT nie | Regel 14 (Trefferquote), Regel 31 (Systemgüte) | **ja — als einzige** |

> **Die einzige handelbare Richtung ist die, die wir systematisch entmutigen.**

---

## 2. Gemessen am 09.08. (Gemini, 36 Anker, 7 Arme, 251 gültige Aufrufe)

Rauschboden bei bitgleicher Eingabe: **0,83 Konfidenzpunkte** (A1 gegen A2, n=36).

### Konfidenzeffekt je Regime und Richtung, gepaart gegen die Grundlinie

| Arm | BULLE LONG | SEITW. LONG | BÄR LONG | SHORT (alle Regimes) |
|---|---|---|---|---|
| + Systemgüte | −4,89 | −14,55 | −30,00 *(n=2)* | **±0,00** |
| + Trefferquote roh | −16,90 | −26,11 | −33,33 *(n=3)* | ±0,00 / −5,00 |
| + Trefferquote **mit Bezug** | −8,90 | −20,50 | −30,00 *(n=3)* | **±0,00** |
| + Regime-Flag | +0,00 *(n=1)* | −11,67 | −23,33 | **−1,73 im BULLE** |

**Lesart:**

- **Der Regime-Flag ist legitim.** Er bestraft die gegen den Trend laufende Seite
  — im Bullen SHORT, im Bären LONG. Das ist seine Konstruktion.
- **Systemgüte und Trefferquote sind es nicht.** Sie treffen LONG in **jedem**
  Regime, auch im Bullenmarkt, und SHORT in keinem.
- **Kein R-Effekt schließt die Null aus.** Dass ein Abstellen mehr Ertrag bringt,
  ist NICHT gezeigt. Die Begründung für eine Änderung ist die sachlich
  unbegründete Einseitigkeit, nicht ein bewiesener Ertragsgewinn.

**Vorbehalte:** BÄR-LONG-Zellen haben n=2–3. Ein Anbieter. E2 ist konstruktiv
beschädigt (Flag ohne Trigger-Richtung eingespeist → das Modell rekonstruierte
die Richtung daraus, 10 von 12 BULLE-Fällen kippten von LONG auf SHORT).

### Gegenprüfungen, die Alternativerklärungen ausschließen

| Hypothese | Ergebnis |
|---|---|
| LONGs kommen aus einem schwächeren Trigger-Zweig | **widerlegt** — `kontra` 8,9 % bei LONG, 10,1 % bei SHORT |
| LONGs waren tatsächlich schlechter | **widerlegt** — LONG 16,2 % Trefferquote / −0,368 R gegen SHORT 15,0 % / −0,321 R |
| Der Unterschied liegt am Anbieter | **bestätigt als Störfaktor** — `ja`-Quote mistral 0,1 % gegen gemini 5,6 %. Deshalb laufen alle Arme auf DEMSELBEN Anbieter, gepaart |

---

## 3. Der entschiedene Grundsatz — und wo er verletzt wird

`crv_baender_kontext_fuer_prompt()` (seit 06.08., alle sechs Pipelines) hält im
eigenen Docstring fest:

> **„NUR DER ABSTAND ZUR BASISLINIE GEHT IN DEN FAKT, NIE DIE ABSOLUTE QUOTE."**

Begründung dort: die absolute Zielquote fällt mit steigendem CRV zwangsläufig.
Bei CRV 4,0 und H=7 erreicht selbst ein Zufallseinstieg nur 3,1 %. Wer absolute
Quoten nebeneinanderstellt, liest daraus „hohes CRV ist schlecht" — der
Trunkierungs-Artefakt, der am 03.08. gemeldet und am selben Tag widerrufen wurde.

**Zwei Stellen verletzen diesen Grundsatz bis heute:**

| Stelle | was sie tut | Soll |
|---|---|---|
| `compute_win_rate_fact()` → **Regel 14** | liefert `trefferquote_pct` **absolut** (heute 16,0 %, 15 von 94) | Abstand zur Basislinie `1/(1+CRV)` statt der nackten Quote |
| `hebel_risk_gate.py:546` | `quote < 30` → Risikofaktor **„negativ"**, feste Schwelle ohne CRV-Bezug | Schwelle CRV-relativ: bei CRV 2,0 liegt der Breakeven bei **33,3 %** |

**Beides gehört zusammen geändert.** Nur eine Seite anzufassen erzeugt zwei
widersprüchliche Rahmungen derselben Zahl im selben System — Prompt sagt „16 %
gegen 33,3 % Breakeven", Gate sagt „negativ, Punkt".

**Drei Ebenen prüfen, nicht eine:** jeder Fakt wirkt potenziell im **Prompt**
(Regel), im **Gate** (deterministische Schwelle) und in der **Anzeige**
(`risikofaktoren_json` → Panel und Mail). Das LLM sieht die Risikofaktoren
**nicht** — sie entstehen nach dem Aufruf (`hebel_pipeline.py:375`).

---

## 4. Zusätzlicher Befund: was die Trefferquote zählt

`_RESOLVED_OUTCOMES` = `take_profit_erreicht`, `stop_loss_erreicht`,
`liquidation_wahrscheinlich`. Treffer ist ausschließlich `take_profit_erreicht`.

**Die 43 „überholt durch neuere Analyse" fallen ganz heraus** — 30,3 % aller
abgeschlossenen Hebel-Signale. Sie fallen heraus, *weil* eine Neubewertung kam,
was mit Marktbewegung korreliert. Zeit bis Überholung: **Median 0,7 Tage**,
P75 2,9, max 18,6 (n=43).

---

## 4b. Externe Methodenlage (recherchiert 09.08.) — was belastbar ist

**Wir müssen das nicht selbst erfinden. Drei Punkte sind Lehrbuchstand:**

1. **Die Trefferquote allein ist die irreführende Zahl.** Maßgeblich ist der
   Erwartungswert: `Trefferquote × Ø-Gewinn > Verlustquote × Ø-Verlust`. Eine
   45-%-Quote bei 2:1 ist ausgezeichnet, eine 75-%-Quote bei 0,5:1 eine Falle.
   **Wir speisen genau die irreführende Zahl ein** (Regel 14) — und den
   Erwartungswert daneben, ohne die beiden zu verknüpfen.
2. **Niedrige Trefferquoten sind psychologisch unangenehm, auch wenn die
   Strategie profitabel ist.** Sprachmodelle erben diese Reaktion aus dem
   Trainingstext. Das ist der plausibelste Mechanismus hinter unserem Befund.
3. **Stichprobengrößen:** 20 Trades sagen nahezu nichts, 50–100 **je Setup**
   sind nötig. Unsere 94 gelten für den *gesamten* Track-Record über alle
   Symbole — der Fakt sagt das im `hinweis` immerhin dazu.

**Aus der LLM-Literatur, direkt einschlägig:**

- **Verbalisierte Konfidenz taugt nicht als Steuersignal.** Modelle
  verbalisieren Unsicherheit zuverlässig, übersetzen sie aber nicht in
  Entscheidungen. Deckt sich mit unserem Befund, dass die Konfidenz innerhalb
  SHORT `ja` von `mit_vorbehalt` überhaupt nicht trennt (68 gegen 68).
- **Negative Rahmung treibt Modelle in übermäßige Risikoaversion.** Genau das
  tun `systemguete` und die rohe Trefferquote.
- **Bemerkenswerter Gegensatz:** die Literatur berichtet für LLM-Handelsagenten
  einen **LONG-Bias** (bis 90,4 % Long-Signale). Wir haben das Gegenteil — weil
  wir gegensteuernde Fakten einspeisen. Unser Problem ist hausgemacht, nicht
  modellinhärent.

**Was daraus für den Umbau folgt** — und es deckt sich mit dem bereits
entschiedenen Grundsatz aus Abschnitt 3:

> Die Trefferquote gehört **nie allein** und **nie absolut** in den Faktensatz.
> Entweder mit ihrem CRV-Breakeven als Bezug, oder ersetzt durch den Abstand
> zur Basislinie — so wie `crv_baender` es seit dem 06.08. bereits macht.

Gemessen ist der Teileffekt: der Bezugsrahmen holt **rund 5 Konfidenzpunkte**
zurück (−16,09 statt −21,26 auf LONG) und erhält als einziger Eingriffsarm noch
Selbstzustimmung (4,3 % gegen 0,0 %).

**Quellen:** [Fin-Bias](https://arxiv.org/pdf/2605.09106) ·
[Agentic Trading](https://arxiv.org/html/2605.19337v1) ·
[Are LLM Decisions Faithful to Verbal Confidence?](https://arxiv.org/pdf/2601.07767) ·
[Reported Confidence Tracks Commitment More Than Correctness](https://arxiv.org/pdf/2606.29490) ·
[I-CALM](https://arxiv.org/pdf/2604.03904) ·
[Win Rate vs Risk-Reward](https://journalplus.co/learn/guides/win-rate-vs-risk-reward/) ·
[Base Rates and Reference Classes](https://www.lesswrong.com/posts/ahWnHGZCWqzTnXs4i/base-rates-and-reference-classes)

---

## 5. Offene Fäden

| # | Faden | Stand |
|---|---|---|
| 1 | **E2 sauber wiederholen** — Regime-Flag MIT Trigger-Richtung, beide Richtungen | offen, ~72 Aufrufe |
| 2 | **Dreiebenen-Konsistenzprüfung** über Erfolgsquote, Systemgüte, Regime-Flag (Prompt / Gate / Anzeige) | offen |
| 3 | **Relative Schwelle umsetzen** an beiden Stellen aus Abschnitt 3 | offen — Grundsatz und Referenzimplementierung existieren |
| 4 | **Ertragsfrage** — kein R-Effekt schließt die Null aus; Stichprobe reicht nicht | offen, braucht ein Vielfaches an Ankern |
| 5 | **Marktphasenlauf auf Gemini** — „wie wären Signale und Parameter außerhalb des Bärenregimes?" | offen, Werkzeug steht (`messe_regimephasen_llm.py`) |
| 6 | Ausstiegsverfahren `systemguete` nach Mappe 7.4b — Stufe 1 frühestens **Ende August** (≥60 aufgelöste Signale) | wartend |
| 7 | **Gemini-Limits ungeklärt** — 200/200/429 in drei Sekunden, hartes Tageskontingent widerlegt. Kein Retry auf 429 (kostete 19 Messpunkte), Statuscode wird nicht protokolliert, Grenzen nie gemessen | **offen, blockiert weitere Gemini-Läufe in ihrer Verlässlichkeit** |

**Ausdrücklich KEIN Ausstiegsgrund** (Mappe 7.4b): eine weiterhin negative
Systemgüte, ein weiterhin fehlender Wirkungsnachweis, ein Abrieb im Rauschboden.
Der hier gemessene Befund ist eine **andere Kategorie** — eine gerichtete
Asymmetrie ohne sachliche Grundlage — und fällt nicht unter diese Ausschlüsse.

---

## 5a. ERGEBNIS des sauberen Regime-Flag-Laufs (09.08., Gemini, 2×2)

`messe_regimeflag_sauber.py`, 36 Anker, Trigger-Richtung in ALLEN Armen, nur
der Flag variiert. Rauschboden 0,83 (übernommen aus dem Kettennaht-Lauf).

| Regime | LONG-Trigger (T2−T1) | SHORT-Trigger (T4−T3) |
|---|---|---|
| BULLE | −2,42 (n=12), Intervall enthält Null | **−5,45** [−7,22; −3,93] |
| SEITWÄRTS | −8,33 [−14,44; −1,25] | −2,00 [−3,12; −0,91] |
| **BÄR** | **+1,11** [+0,00; +3,75] | −0,56 [−2,14; +0,00] |
| GESAMT | −3,13 [−5,52; −0,23] | −2,83 [−3,68; −1,73] |

**Beide vorab festgelegten Vorhersagen sind gescheitert.** Trend-Konflikt hätte
im Bären eine starke LONG-Strafe verlangt — es gibt **keine**. Richtungsfilter
hätte in jedem Regime eine LONG-Strafe verlangt — im Bären ist sie **positiv**.

> **Im einzigen Regime, das in der Produktion je existiert hat, tut der Flag
> praktisch nichts.** Und das, obwohl die Prompt-Regeln 2 und 26 ihn zu einem
> von nur ZWEI privilegierten Dämpfungsfällen erheben, mit Erlaubnis, die
> 75-%-Konfidenzuntergrenze zu unterschreiten.

**Erklärt zugleich den Widerspruch zum ersten, beschädigten E2-Lauf** (dort
LONG −23,33 im Bären): ohne genannte Trigger-Richtung musste sich das Modell
den Konflikt selbst zusammenreimen. Mit genannter Richtung kann es ihn aus
Regime und Trigger ohnehin ableiten — der explizite Flag fügt dann nichts
hinzu. Hypothese, keine Messung, aber sie passt auf beide Läufe.

**Folge für den Plan: der Regime-Flag kommt NICHT in Phase 2.** Die Ursache der
LONG-Unterdrückung liegt damit durch **Ausschluss bestätigt** bei `systemguete`
und `historische_erfolgsquote`.

**Einschränkungen, die dazugehören:** 19 HTTP-Fehler sitzen alle in den letzten
6 Ankern (Gemini-Tageskontingent) — die spätesten Anker fehlen systematisch,
nicht zufällig. Zellen mit n=9–12 bei 5–7 Symbolen liegen **unter** der selbst
gesetzten Clustergrenze von 12.

---

## 5c. ZWISCHENSTAND nach dem Wirkungslauf (09.08. spät)

`messe_umbau_wirkung.py`, 36 Anker, 5 Arme, **OpenRouter** (Gemini-Tagesbudget
verbraucht), 180 Aufrufe, 0 Fehler.

### Was gemessen wurde

| Arm | ERÖFFNEN | LONG-Anteil | selbst-ja | dyn R | Zielquote-Vorsprung |
|---|---|---|---|---|---|
| **A1** | 97,2 % | 13,9 % | 66,7 % | +0,253 | +3,6 pp |
| Q_alt | 94,4 % | **8,3 %** | 63,9 % | −0,036 | **−11,3 pp** |
| Q_neu | 94,4 % | 11,1 % | 44,4 % | +0,222 | **+19,9 pp** |
| G_alt | **91,7 %** | 13,9 % | 63,9 % | −0,078 | **−16,4 pp** |
| **G_neu** | **97,2 %** | **16,7 %** | **66,7 %** | +0,285 | +5,0 pp |

**Sechs Vergleiche, alle in dieselbe Richtung:** auf jeder Gesamtgröße liegt die
alte Form schlechter als die neue. `G_neu` stellt die Grundlinie vollständig
wieder her.

### Was die GEGENPRÜFUNG davon übriglässt

**Drei Einwände, alle bestätigt, alle gegen den eigenen Befund:**

1. **Konzentration.** Kein einziger R-Effekt überlebt das Entfernen seines
   größten Beitragssymbols. `G_alt` hing zu 30,2 % an BTC (ohne BTC p=0,105
   statt 0,053), `Q_alt` zu 41,3 % an PLUME (p=0,384). Die Methodik verlangt
   diese Prüfung — sie fehlte im Auswerter und ist jetzt eingebaut.
2. **Nicht drei unabhängige Achsen, sondern zwei.** `dyn_r` und die Zielquote
   stammen aus **denselben Zonen und Kursen**. Es sind zwei Ansichten einer
   Sache, nicht zwei Belege.
3. **Mehrfachvergleich.** Vier Arme gegen A1: unter reinem Zufall trifft in
   rund 19 % der Fälle mindestens einer die 5-%-Schwelle. `G_alt`s p=0,053
   liegt genau dort.

Dazu eine Einschränkung des Aufbaus: **der Anbieterwechsel zerstörte die
LONG-Stichprobe.** `nemotron` wählt LONG nur in ~8 % der Fälle (Gemini: ~58 %),
die LONG-Zellen haben n=3–4. Die Richtungsaufspaltung trägt hier nichts.

### Der Stand, präzise

| Aussage | Status |
|---|---|
| Die alte Form wirkt **gerichtet auf LONG**, ohne sachliche Grundlage | **belegt** — Gemini-Lauf, n=36, Intervalle ohne Null, Rauschboden 0,83 |
| Die alte Form **kostet Ertrag** | **nicht belegt** — hängt an Einzelsymbolen |
| Der Umbau **verbessert den Ertrag** | **nicht belegt** — dito |
| Der Umbau **stellt das Verhalten wieder her** | **Hinweis** — sechs gleichgerichtete Vergleiche, abhängige Größen |

### Warum wir trotzdem umbauen

Die Begründung war nie ein Ertragsversprechen. Sie ruht auf drei Säulen, von
denen keine von diesem Lauf abhängt:

1. **Ein belegter Defekt:** eine gerichtete Wirkung auf LONG, die durch nichts
   gedeckt ist — LONG liegt mit 16,2 % Trefferquote sogar leicht über SHORT
   mit 15,0 %.
2. **Ein bereits entschiedener Grundsatz:** *„NUR DER ABSTAND ZUR BASISLINIE
   GEHT IN DEN FAKT, NIE DIE ABSOLUTE QUOTE"* — seit 06.08. in allen sechs
   Pipelines umgesetzt, nur an diesen zwei Stellen nicht.
3. **Der Umbau nimmt nichts weg.** Rohzahlen bleiben unverändert; es kommt
   Einordnung dazu. Das Risiko einer Änderung, die nur Kontext ergänzt, ist
   strukturell klein.

> **Ein unbewiesener Zusatznutzen ist kein Gegenargument gegen die Behebung
> eines belegten Defekts.** (Nutzer, 09.08.)

---

## 5b. DER PLAN — von hier bis in die Produktion

**Grundsatz:** wir ändern nichts, was wir nicht vorher und nachher gemessen
haben. Und wir entfernen nichts, wo Umrahmen reicht — das ist die von Mappe
7.4b geforderte *kleinste wirksame Änderung*.

### Phase 0 — Nachweis abschließen *(läuft)*

| | Was | Werkzeug | Kosten |
|---|---|---|---|
| 0.1 | Regime-Flag sauber, 2×2 mit Trigger-Richtung | `messe_regimeflag_sauber.py` | 144 Aufrufe, **läuft** |
| 0.2 | Ergebnis aufbereiten und entscheiden: Richtungsfilter oder Trend-Konflikt | dito | — |

**Entscheidungstor:** Zeigt der Flag Trend-Konflikt-Verhalten (im Bären LONG,
im Bullen SHORT bestraft), bleibt er **unangetastet** — er tut dann, was er
soll. Zeigt er in jedem Regime nur LONG-Strafe, kommt er in Phase 2 dazu.

### Phase 1 — Das Ausstiegs-/Umbauverfahren nach Mappe 7.4b

Das Verfahren verlangt in **Stufe 2**, drei Alternativerklärungen
auszuschließen. Für einen *kontrollierten Versuch* sind zwei davon
gegenstandslos, und das ist ein Vorteil, kein Mangel:

| Alternative aus 7.4b | Stand |
|---|---|
| Provider-Drift | **entfällt** — alle Arme laufen gepaart im selben Lauf, auf demselben Anbieter, in derselben Minute |
| Regime | **geprüft, es IST die Aufschlüsselung** — der Effekt tritt in jedem Regime auf, auch im Bullen |
| Andere Änderung im Fenster | **entfällt** — es gibt kein Fenster, nur Arme |

> **Der kontrollierte Versuch ersetzt die Beobachtungsprozedur und ist
> stärker als sie.** Beobachtend kann man Ursachen nur ausschließen;
> experimentell kann man sie herstellen.

**Stufe 3 verlangt eine schriftliche Begründung mit Revisit-Bedingung.** Die
steht in Abschnitt 3 dieser Datei und wird bei Umsetzung in
`Regelwerk_Entscheidungslog.md` eingetragen.

**Was unser Befund NICHT ist:** „kein Wirkungsnachweis" — das wäre laut 7.4b
ausdrücklich **kein** Ausstiegsgrund. Unser Befund ist eine **gerichtete
Asymmetrie ohne sachliche Grundlage**, belegt durch zwei Gegenprüfungen
(Trigger-Zweig gleich verteilt, LONG-Ergebnis nicht schlechter). Das ist eine
andere Kategorie.

### Phase 2 — Umbau, zwei Stellen, eine Logik

Beide Änderungen setzen den **bereits entschiedenen Grundsatz** aus Abschnitt 3
an den zwei Stellen um, die ihn noch verletzen. Kein neues Konzept.

| | Änderung | Datei | Stand |
|---|---|---|---|
| 2.1 | `historische_erfolgsquote`: Median-CRV, Breakeven, Abstand, Überholungs-Ausweis — **und je Richtung mit Schrumpfung** | `backward_tracking.py::compute_win_rate_fact()` | **GEBAUT + GETESTET** |
| 2.2 | Gate-Schwelle **CRV-relativ** statt fest 30/60, mit Rückfallpfad | `hebel_risk_gate.py` | **GEBAUT + GETESTET** |
| 2.3 | `systemguete`: **Basislinie, Signalbeitrag und Vertrauensbereich durchreichen** | `backward_tracking.py::systemguete_kontext_fuer_prompt()` | **GEBAUT + GETESTET** |

### Was tatsächlich gebaut wurde (09.08.)

**`schrumpfe_zu_neutral()`** — Nutzer-Vorschlag: *„eine neutrale
Ausgangsposition, die sich ohnehin selbst durch den Betrieb kalibriert".*
Formel `n/(n+k) × gemessen + k/(n+k) × neutral`, mit `PSEUDO_STICHPROBE = 50`
(unteres Ende der Literaturempfehlung 50–100 je Setup). Roh, gewichtet und
Gewicht stehen **immer alle drei** im Fakt — sonst wäre es Beschönigung statt
Kalibrierung. 19 Prüfungen, darunter die harte Grenze: **ein negativer
Erwartungswert kann nie positiv werden.**

**Trefferquote je Richtung** — und die Richtungen haben *verschiedene*
Breakevens, weil ihre Median-CRVs verschieden sind:

| | n | roh | Median-CRV | eigener Breakeven | Gewicht | geschrumpft |
|---|---|---|---|---|---|---|
| LONG | 74 | 16,2 % | 2,54 | 28,2 % | 0,597 | 21,04 |
| SHORT | 20 | 15,0 % | 3,02 | 24,9 % | 0,286 | 22,07 |

Nach Schrumpfung liegen beide fast gleichauf — das ist die Wahrheit (−12,0 pp
gegen −9,9 pp zur jeweiligen Latte). Dem Modell fehlt damit die Grundlage, ein
globales Minus einer Richtung zuzuschlagen.

**Systemgüte — der überraschendste Fund:** `compute_systemguete()` rechnet die
Basislinie **längst mit**, und `systemguete_kontext_fuer_prompt()` warf sie weg.

| Feld | Wert | erreichte das LLM bisher? |
|---|---|---|
| `expectancy_r` | −0,149 | ja |
| `basislinie_erwartungswert_r` | **−0,094** | **nein** |
| `signalbeitrag_r` | **−0,055** | **nein** |
| `erwartungswert_ci` | **[−0,407; +0,147]** | **nein** |

Das Modell las „−0,149 R, das System verliert" — während ein **mechanischer
Einstieg im selben Zeitraum −0,094 R verloren hätte** und **das
Vertrauensintervall die Null enthält**. Die Zahl ist statistisch nicht von
„kein Effekt" zu unterscheiden, und wurde als Tatsache eingespeist.

Deshalb hier **keine Schrumpfung**: das Vertrauensintervall ist die *echte*
Unsicherheit, nicht eine Prior-Näherung. Durchreichen schlägt Rechnen.

**Tests:** `teste_schrumpfung.py` (19) und `teste_trefferquote_bezug.py` (21),
jede Zusicherung mit Gegenkontrolle. Darunter: dieselbe Trefferquote von 25 %
wird bei CRV 2,0 als *negativ* und bei CRV 4,0 als *neutral* bewertet — das
konnte die feste 30er-Schwelle nicht.

**2.1 ist gemessen wirksam** — der Bezugsrahmen holt rund 5 Konfidenzpunkte
zurück (−16,09 gegen −21,26) und erhält als einziger Arm noch
Selbstzustimmung. **2.2 und 2.3 sind ungemessen** und brauchen Phase 3.

**Rollout-Pflicht:** `pruefe_fakten_rollout.py` nach jeder Fakten-Änderung —
die Entscheidung gilt über **alle sechs Pipelines**, nicht nur Hebel.

### Phase 3 — Wirkung messen, BEVOR es in die Produktion geht

Derselbe Aufbau wie Phase 0, mit den umgebauten Fakten als Armen:

| Arm | Inhalt |
|---|---|
| A1 / A2 | Grundlinie und Rauschboden |
| **U1** | Erfolgsquote **umgebaut** (2.1) |
| **U2** | Systemgüte **umgebaut** (2.3) |
| **U12** | beide — der neue Produktionszustand |

**Drei Tore, alle drei müssen offen sein** (`werte_kettennaht_aus.py` prüft sie):

1. Verhaltensänderung **über dem Rauschboden**
2. R-Effekt **schließt die Null aus** — oder mindestens: er ist nicht negativ
3. **ERÖFFNEN-Wächter meldet nichts** — kein Gewinn aus Nichthandeln

**Stichprobe:** die bisherige (36 Anker) reicht für das Verhalten, **nicht**
für den Ertrag. Für Tor 2 braucht es ein Vielfaches — grob 120–150 Anker.
Das ist der ehrliche Kostenpunkt dieses Plans.

### Phase 4 — Produktion und Nachmessung

1. Umbau deployen, **Nachtrag an der Codestelle** („HIER STAND …, BEWUSST
   GEÄNDERT" mit Grund und Messwert) nach dem Nur-Long-Muster
2. Eintrag in `Regelwerk_Entscheidungslog.md` mit Revisit-Bedingung
3. **Nachmessen im Betrieb:** ERÖFFNEN-Quote, LONG-Anteil und
   Selbstzustimmung je Regime, gegen die heutigen Werte
   (LONG-`ja` 0,0 %, ERÖFFNEN 8,3 %, LONG-Anteil 17,3 %)
4. **Revisit-Bedingung:** kehrt die LONG-`ja`-Quote nach 60 aufgelösten
   Signalen nicht über 0 %, war die Diagnose unvollständig — dann ist der
   nächste Verdächtige die Prompt-Regel 26 selbst, nicht mehr der Faktensatz

### Was dieser Plan NICHT verspricht

**Keinen Ertragsgewinn.** Begründet ist die Beseitigung einer sachlich
unbegründeten Einseitigkeit — nicht ein bewiesenes Plus. Wer mehr behauptet,
überschreitet die Datenlage. Die Ertragsfrage bleibt Faden 4 in Abschnitt 5.

---

## 6. Werkzeuge, die dabei entstanden sind

| Datei | Zweck |
|---|---|
| `messe_kettennaht_eingriffe.py` | faktorielle Arme mit A1/A2-Rauschboden, additiv statt subtraktiv |
| `werte_kettennaht_aus.py` | Verhalten + Ertrag + Zufallsvergleich, mit ERÖFFNEN-Wächter |
| `bewerte_dynamisch.py` + `teste_bewerte_dynamisch.py` | Ergebnis unter der live gefahrenen Ausstiegsregel (19 Prüfungen) |
| `messe_regimephasen_llm.py` + `teste_regimephasen.py` | Marktphasen-Simulation (26 Prüfungen) |
| `pruefe_regimephasen_vorflug.py` | Vorflugkontrolle für neu gebaute Clients |
| `pruefe_llm_stabilitaet.py` | Rauschboden je Anbieter vor jedem großen Lauf |
| `pruefe_gemini_verhalten.py` + `teste_gemini_tagesbudget.py` | Geminis echte Grenzen aus dem Fehlerkörper lesen (27 Prüfungen) |

---

## 7. Nachtrag 09.08. abends — warum die Produktion einen Tag stand

**Gemessen, nicht recherchiert** (`pruefe_gemini_verhalten.py`, ein Aufruf):

```
quotaId    GenerateRequestsPerDayPerProjectPerModel-FreeTier
Grenzwert  500
```

Drei Eigenschaften, die wir alle drei falsch hatten:

| | bisherige Annahme | gemessen |
|---|---|---|
| **PerDay** | „nur ein Burst-Limit, Warten hilft" | Tageslimit — Warten hilft bis morgen früh nicht |
| **PerProject** | Kontingent hängt am Gerät | hängt am **Schlüssel**: Desktop-Messläufe nehmen der Produktion direkt Budget weg |
| **PerModel** | ein Topf für Gemini | **je Modell ein eigener Topf**; `gemini-3.5-flash-lite` war unberührt |

### Warum wir es zwei Tage nicht gesehen haben

Ich hatte behauptet, der OpenAI-Kompatibilitäts-Endpunkt verschlucke diese
Angabe. **Das war falsch.** Er liefert dieselbe `QuotaFailure`, nur als
JSON-**Liste** statt als Objekt. Unser Client hat den Fehlerkörper schlicht nie
gelesen — `raise_for_status()` und fertig. Die Antwort stand in jedem einzelnen
429 des Tages. Das war unsere Blindheit, nicht Googles Auskunftsverweigerung.

### Warum das bestehende Tagesbudget nicht gegriffen hat

`gemini_taegliches_budget` (Vorgabe 200) existiert seit dem 14.07. in
`budget_allocator.py:446`. Vier Gründe, warum es die 500 nicht verhindert hat:

1. Es sitzt im **Allocator** — Messskripte bauen sich einen `GeminiClient`
   direkt und gehen vollständig daran vorbei. **Genau so sind die 500 gefallen.**
2. Es zählt auf **UTC-Tag**, Google setzt auf **Pazifik-Mitternacht** zurück —
   sieben Stunden Versatz, in denen der Zähler fälschlich auf 0 steht.
3. Es zählt je **Anbieter**, begrenzt wird je **Modell**.
4. Sein Zähler liest `api_call_kontingent_taeglich` — **die Tabelle fehlte in
   der Desktop-DB**, der Aufruf scheiterte still (P-10) und fiel auf den
   Datensatz-Zähler zurück, der Fehlschläge nicht mitzählt.

### Was jetzt gebaut ist

| Ort | Änderung |
|---|---|
| `api/gemini.py` | Fehlerkörper wird geparst; `PerDay` wirft sofort `TageskontingentErschoepft` statt dreimal zu wiederholen; Tageswächter **im Client**, je Modell, auf Pazifik-Tag; `budget_status()` für Vorflugkontrollen |
| `api/llm_basis.py` | `verbrauch_heute()`; `zaehle_aufruf()` nimmt einen Tagesschlüssel |
| `database/db.py` | `increment_api_call_counter()` nimmt einen Tagesschlüssel — bestehende Aufrufer unverändert auf UTC |
| Desktop-DB | die drei fehlenden `api_call_kontingent*`-Tabellen angelegt |
| `remote/status.py` + `server.py` | Karte „Gemini-Tageskontingent je Modell", ungecacht |
| `fahre_wirkungsmessung.py` | Stufe 1 **wählt** das Modell nach Budget; Produktionsmodell steht hinten, damit die Messung ausweicht und nicht die Produktion |
| `messe_umbau_wirkung.py` | `--modell`; rechnet den Bedarf **vor** dem Lauf gegen das Budget |

**Geprüft:** 27 + 16 Prüfungen mit Gegenkontrollen, dazu die Kette gegen die
echte API (erschöpftes Modell → typisierter Abbruch ohne Wiederholung; freies
Modell → Antwort) und ein echter Prompt auf `gemini-3.5-flash-lite`: 5 Arme,
0 Fehler, alle Messfelder befüllt, Antwortformat `json_object`.

### Was offen bleibt

- **Warum vereinzelte Einzelaufrufe durchkamen**, während acht Aufrufe mit
  10 s Abstand komplett scheiterten, erklärt ein hartes Tageslimit nicht.
  Keine vierte Vermutung ohne Messung.
- **Die Tagesgrenze von `gemini-3.5-flash-lite` ist unbelegt.** Google nennt
  den Grenzwert nur im *Fehler*körper; ein erfolgreicher Aufruf sagt nichts.
  Vermutlich ebenfalls 500 — belegen ließe es sich nur durch Aufbrauchen.
- **Der Zähler beginnt bei null.** Er kennt die heute bereits verbrauchten
  Aufrufe nicht und weiß nichts von einem zweiten Gerät am selben Schlüssel.
  Deshalb hat Stufe 1 **zwei** Ebenen: Zähler *und* echter Probeaufruf.

---

## 8. Wirkungsmessung gefahren (09.08., 23:24–23:37) — halbes Ergebnis

Auf `gemini-3.5-flash-lite` (eigener 500er-Topf, Produktionsbudget unberührt),
25 Anker × 5 Arme, **125 Aufrufe, 0 Fehler**. Rauschboden 0,83.

| Fakt | alt | neu | Besserung | Urteil |
|---|---|---|---|---|
| **Trefferquote (Q)** | −15,14 | −9,68 | **+5,45** | über dem Rauschboden — **wirksam** |
| **Systemgüte (G)** | −2,83 | −3,88 | −1,05 | darunter — **kein Nachweis** |

Der Trefferquote-Umbau drückt die LONG-Konfidenz um 5,45 Punkte weniger, das
Sechsfache des Rauschbodens. Der Systemgüte-Umbau bewirkt nichts — die alte
Form drückte dort ohnehin nur −2,83.

**Warum die Zwischenzahlen kein Ergebnis waren:** nach 5 Ankern stand die
Systemgüte bei **+15,50 „WIRKSAM"**. Bei 25 Ankern bleibt −1,05. Genau davor
war gewarnt worden, bevor die Zahl bekannt war.

### Drei Defekte, die dieser Lauf aufgedeckt hat

**1. Der Auswertbarkeits-Wächter tötete auf Nullbeobachtungen.** `0 × 60/5 = 0`
→ „unerreichbar". Null Treffer in fünf Versuchen schließen aber nichts aus;
nach der Dreierregel wären bis zu 36 Fälle möglich gewesen. Repariert ist der
**Schätzer**, nicht die Regel (`_hoechstens_noch()`): bei n=0 die Dreierregel,
bei n>0 unverändert der Punktschätzer. **Korrektur einer früheren Aussage:**
„der Wächter hätte den nemotron-Lauf nach fünf Ankern gestoppt" war zu stark —
mit dem korrigierten Schätzer greift er beim zehnten.

**2. Die Ankerliste war nach Datum sortiert — also nach Phase.** Die Bärenphase
ist die jüngste, ihre Anker standen am Ende. Der Abbruch bei 25 lieferte
`BULLE 17, SEITWAERTS 8, BAER 0` — ausgerechnet die Phase fehlte, in der die
Produktion läuft. Jetzt reihum verschränkt (`verschraenke_phasen()`): jeder
Anfang der Liste ist phasenausgewogen. Dieselbe Fehlerklasse wie der
Stichproben-Alias aus D1g, eine Ebene höher.

**3. Folgefehler aus 2:** ohne Bärenanker wählte der Grundlinienarm 25 von 25
mal LONG → keine gepaarte SHORT-Zelle → die **Kontrollbedingung der Messregel
war nicht prüfbar**. Der Bewerter behauptete trotzdem „SHORT bleibt". Korrigiert:
er meldet jetzt „Regel zur HÄLFTE erfüllt — ob der Umbau die Asymmetrie auflöst
oder nur verschiebt, ist offen".

### Damit gilt

Der Befund **+5,45 auf die Trefferquote** steht — aber **für Bullen- und
Seitwärtsphasen**, gemessen auf `gemini-3.5-flash-lite`. Nicht für die
Bärenphase, in der die Produktion tatsächlich läuft, und nicht für das
Produktionsmodell. Die Wiederholung mit phasenausgewogener Stichprobe steht aus.

**Geprüft:** 22 (Auswertbarkeit) + 14 (Phasenverschränkung) Prüfungen mit
Gegenkontrollen; die Gegenkontrolle reproduziert den echten Ausfall exakt
(alte Fassung bei 25 Ankern: `BULLE 20, SEITWAERTS 5, BAER 0`).

---

## 9. Offene Fäden nach dem Produktionsstart 10.08.

### Z.ai — der nächste blinde Fleck (Nutzer-Entscheidung: nach dem Messlauf)

| Beleg | Wert |
|---|---|
| Aufrufe am 08.08. | **490** — mehr als Gemini (190) und Mistral (9) zusammen |
| Aufrufe am 10.08. bis 07:00 | 22 |
| `api_health_status` 05:00:46 | **429 Too Many Requests** |
| Tagesdeckel im Allocator | **keiner** — die Statusseite schreibt es sogar hin: „kein Tagesdeckel" |

Z.ai ist die Gegenprüfung, nicht Teil der Signal-Kette. Genau deshalb schaut
niemand darauf: sie hat kein Budget, keinen Wächter, keine Sichtbarkeit — und
läuft bereits in 429er. **Das ist dieselbe Ausgangslage wie bei Gemini vor dem
09.08.**, nur eine Ebene weiter außen. Der Unterschied: bei Gemini kostete das
Nichtwissen einen Produktionstag.

Zu klären, in dieser Reihenfolge:
1. Wie hoch ist Z.ais tatsächliches Limit? **Aus dem Fehlerkörper lesen**,
   nicht recherchieren — dieselbe Methode, die bei Gemini die zwei Tage
   Spekulation in einem Aufruf beendet hat (`pruefe_gemini_verhalten.py`).
2. Zählt `zaehle_aufruf("zai")` vollständig? Der Zähler existiert, ein
   Deckel nicht.
3. Braucht die Gegenprüfung überhaupt 490 Aufrufe/Tag — oder läuft sie
   mehrfach über dieselben Fälle?

### Kleinere Fäden aus demselben Lauf

- **ATR-Perzentil fällt aus** (`benötigt mind. 30 gültige ATR-Werte, nur 10`),
  betroffenes Symbol im Logausschnitt nicht sichtbar. Degradiert sauber, kein
  Absturz.
- **`refresh_prices`: 44 von 57 Assets** aktualisiert — 13 ohne Aktualisierung,
  Ursache offen.
- **`OD7L` mit 131 Punkten** rekonstruiert, während OD7N/OD7H/OD7C je 520
  bekamen.
- **Open-Interest-Abrufe scheitern** für BEAMX, AKT, TURBO, CAT, GRIFFAIN —
  Kleinstwerte, auf OKX/Bybit nicht gelistet. Erwartbar, kein Handlungsbedarf.

### Nachtrag zur Versionierung

Die Messungsumbauten (Cluster-Intervall, Konzentrationsprüfung,
Richtungswahl-Auswertung, reparierter Trockenlauf-Mock, Stufe 2b) sind über
`git add -A` in `33a2b11` mitgekommen — also unter einer Commit-Botschaft, die
sie nicht beschreibt. Inhaltlich sind sie geprüft und in Abschnitt 8
dokumentiert; die Nachvollziehbarkeit hängt hier an dieser Datei, nicht am
Commit-Titel.

---

## 10. LLM2: die Richtungs-Gegenprüfung urteilt über eine Konstante

**Nutzer-Entscheidung 10.08.: `regime` aus `baue_objektive_fakten()` entfernen —
NACH dem Messlauf.**

### Der Befund

Z.ais unabhängige Richtungsableitung über 1.022 Hebel-Signale:

| Z.ais eigene Richtung | | Primärmodell auf denselben Fällen |
|---|---|---|
| NEUTRAL | 545 (53,3 %) | SHORT 665 (65,1 %) |
| SHORT | 476 (46,6 %) | LONG 357 (34,9 %) |
| **LONG** | **1 (0,1 %)** | |

Von 357 LONG-Signalen des Primärmodells bestätigt Z.ai **eines**. Juli: 1 von
463. August: **0 von 559**.

### Die Ursache — nicht das Modell, der Faktensatz

`leite_eigene_richtung()` bekommt genau sechs Fakten (`baue_objektive_fakten()`,
`gegenpruefung.py:215`): `symbol`, `rsi`, `trend`, **`regime`**,
`funding_rate_vorzeichen`, `technische_konfluenz`, `optionsmarkt_skew`.

**`regime` war auf ALLEN 1.022 Fällen `baer` — 100,0 %.**

Der Systemprompt verlangt „leite ALLEIN aus diesen Fakten deine eigene
Markteinschätzung ab". Ein Modell, dem bei jedem Aufruf „Bärenmarkt" als Fakt
mitgegeben wird, kommt praktisch nie auf LONG. Das Ergebnis ist die erwartbare
Antwort auf die gestellte Frage — kein Bias im üblichen Sinn, sondern ein
**Konstruktionsfehler des Faktensatzes**.

Folge: die Richtungs-Gegenprüfung ist **für LONG-Signale wertlos**. Sie kann
nur bestätigen, was das Regime ohnehin sagt. Passt zu
[[project_regime_immer_baer_kein_vergleich]].

### Zwei widerlegte Zwischenthesen (beide meine)

**„Der Positions-Fallback vom 29.07. erzeugt die NEUTRALs."** Teilweise: 204
der 545 NEUTRALs tragen den Vermerk „Positions-uneinheitlich". Aber **LONG war
schon vor dem Fix null** (0 von 159 Fällen vor dem 29.07. 18:45). Der Fix ist
nicht die Ursache.

**„0,0 % Übereinstimmung."** Abfragefehler meinerseits —
`zai_uebereinstimmung` ist Text (`ja`/`nein`), nicht 0/1. Echte Quote **33,6 %**
(343 von 1.022), davon 342 aus SHORT-gegen-SHORT.

### Was der Fix vom 29.07. wirklich tat

Positions-Bias, nicht Richtungs-Bias: die Reihenfolge der JSON-Schlüssel
beeinflusste das Urteil messbar („Lost in the Middle", live belegt mit zwei
spiegelbildlichen Szenarien). Gegenmittel Position Swapping — zwei Aufrufe mit
umgekehrter Faktenreihenfolge, bei Uneinigkeit NEUTRAL. Läuft nachweislich und
ist sauber gebaut; es adressierte nur nie die Frage, die wir jetzt stellen.

### Nebenbefund: die Widerspruchsquote misst LLM1, nicht LLM2

Konsistenzprüfung (Kurzbegründung gegen harte Fakten), je Primäranbieter:

| Anbieter | n | Widerspruch |
|---|---|---|
| `mistral:mistral-small-2506` | 727 | **41,3 %** |
| `gemini:gemini-3.1-flash-lite` | 288 | **13,5 %** |

Mistrals Begründung widerspricht den eigenen Eingabefakten **dreimal so oft**.
Das ist eine Aussage über LLM1. Passend dazu, dass Mistral seit dem 07.08.
ohnehin nur noch dritte Stufe der Kette ist.

**Wichtig beim Weiterarbeiten:** `pruefe_gegenpruefung_trefferquote.py` warnt im
Docstring ausdrücklich davor, aus dem Konsistenzurteil auf den Handelsausgang
zu schließen — „das wäre eine Kategorienverwechslung, LLM2 ist ein
Konsistenzprüfer und kein Prognosemodell".
