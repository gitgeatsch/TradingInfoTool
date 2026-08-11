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

### Nachweis: `regime` unterdrückt die Richtung (gemessen 10.08., 20 Anker gepaart)

Derselbe Faktensatz, ein Feld Unterschied, `messe_zai_ohne_regime.py`:

| Richtung | MIT `regime` | OHNE `regime` |
|---|---|---|
| LONG | **0** | **2** |
| SHORT | 11 | 7 |
| NEUTRAL | 9 | 11 |

**Sechs von zwanzig Ankern ändern ihr Urteil — alle sechs in dieselbe Richtung,
keiner gegenläufig.** Vorzeichentest **p = 0,031**.
`SHORT→NEUTRAL` 4×, `NEUTRAL→LONG` 2×.

Z.ai nennt die Ursache in der eigenen Begründung:

```
GRIFFAIN   mit regime : NEUTRAL — "Gemischte Signale: baerisches Regime,
                                   aber bullischer RSI"
           ohne regime: LONG    — "Bullische Indikatoren ueberwiegen leicht"
```

**Grenzen:** n=20, zwei LONG-Fälle absolut — belastbar ist die RICHTUNG des
Effekts, nicht seine Größe. Und Arm A hatte fünf Felder statt der sieben der
Produktion (`trend`, `funding_rate_vorzeichen` in `facts_json` nicht an den
erwarteten Pfaden). Ist `trend` ebenfalls durchgehend bärisch, ist der
gemessene Effekt eine **Untergrenze**.

### Der zweite konstante Fakt: `optionsmarkt_skew`

Über dieselben 1.022 Fälle: **1.022 × negativ, 0 × positiv.** Die
unterschiedlichen Zahlenwerte je Tag (−12,29/−12,28/−12,27) sind Tagesdrift
desselben Marktwertes, keine Symbolunterschiede. Negativer Skew = Puts teurer
= bärisch. Und der Wert stammt vom **BTC**-Optionsmarkt, nicht vom bewerteten
Symbol — dieselbe Bezugsgrößen-Lücke, die für den Primär-Prompt notiert ist.

**Damit trugen von Z.ais sechs Fakten ZWEI eine konstante Richtungsaussage.**
`symbol` trägt keine. Übrig bleiben `rsi`, `technische_konfluenz` und `trend`
als tatsächlich symbolabhängige Information.

### Antwort auf „sollen MUSS-Faktoren wie beim Primär-LLM dazu?"

**Nein — nicht mehr Fakten, sondern informative.** Bekäme Z.ai denselben
Faktensatz wie LLM1, wäre es ein zweiter Durchlauf derselben Analyse: seine
Zustimmung würde nichts mehr bedeuten, weil beide dieselben Fehler machten.
Der Wert einer Gegenprüfung liegt in der Unabhängigkeit ihrer Eingaben. Dazu
kommt Z.ais eigene Grenze (kleine Prompts, begrenzte Frequenz).

Die Prüffrage vor jedem Feld lautet deshalb nicht „ist es wichtig?", sondern:
**trägt es symbolabhängige Information — oder ist es über alle Fälle
konstant?** Ein konstanter Fakt in einem Sechs-Felder-Satz ist kein Kontext,
er ist ein Daumen auf der Waage.

---

## 11. Der Messtag 10.08. — drei Befunde, ein Mechanismus

### Lauf A: die Wirkungsmessung auf dem Produktionsmodell

50 Anker × 5 Arme auf `gemini-3.1-flash-lite`, **250 Zellen, null Fehler**,
Phasen 17/17/16, deterministische Ankerauswahl.

| | LONG-Konfidenz | 95%-Intervall (Cluster) | Wild-p | Richtungswahl |
|---|---|---|---|---|
| **Trefferquote** | −19,29 → −18,41 | [−2,86; +3,16] | **1,0** | 46 % → 48 % |
| **Systemgüte** | −3,85 → **−8,86** | **[−9,41; −2,17]** | **0,02** | 56 % → **44 %** |

Trefferquote-Umbau: **kein Effekt**. Systemgüte-Umbau: **nachweislich schädlich**
— das Intervall schließt die Null aus, und ohne das stärkste Symbol wird der
Effekt größer (−6,58 statt −5,48), also trägt ihn kein Einzelfall.

**Damit ist die gestrige Zahl (+5,45 auf dem Ausweichmodell) widerlegt.**

### Die Ursache: eine einzige Textzeile

`messe_einordnung_wirkung.py`, 25 Anker, ein Feld Unterschied:

```
mit  einordnung:  6 von 25 LONG = 24,0 %
ohne einordnung: 10 von 25 LONG = 40,0 %

SHORT -> LONG   4        LONG -> SHORT   0
Konfidenz -4,60 Punkte, 95%-Intervall [-7,39; -1,54], Wild-p 0,0305
```

**`einordnung: "unter der Basislinie"` kostet 4,6 Konfidenzpunkte und 16 pp
LONG-Anteil.** Die Zahlen, aus denen dieses Urteil abgeleitet ist, stehen in
BEIDEN Armen unverändert — und richten diesen Schaden nicht an.

Durch Subtraktion: von den −5,48 des Gesamtumbaus entfallen etwa −4,6 auf die
Textzeile, der Rest liegt im Rauschen. **Die Zahlen bewirken nichts, der Text
bewirkt alles.**

### Der Literaturvergleich bestätigt es wörtlich

> „adversarial false audits can push them toward **unjustified conservatism**,
> representing an alignment tax where **textual compliance is purchased at the
> cost of distorted decision geometry**"

Wir haben dem Modell mitgeteilt, sein Beitrag liege unter der Basislinie — ein
Audit — und es wurde konservativer. Nicht weil die Daten es nahelegen, sondern
weil ein Werturteil im Faktensatz stand.

Ebenso belegt: **„prompt-level interventions leave these biases largely
intact"** — was unsere Wochen der Darstellungsarbeit erklärt.

### Die Nullmessung: hat die Richtungswahl überhaupt eine Kante?

`messe_llm_gegen_regel.py`, nur ERÖFFNEN-Signale, Wahrheit ist die tatsächliche
Kursbewegung in ATR-Vielfachen — ohne Bezug auf irgendeine Empfehlung.

| Verfahren | 3 Kerzen | 7 Kerzen | 14 Kerzen |
|---|---|---|---|
| **LLM** | **29,8 %** | **27,7 %** | **25,0 %** |
| Konfluenz-Mehrheit | 52,0 % | 40,7 % | 40,2 % |
| Kurs vs EMA-200 | 61,8 % | 61,7 % | 63,5 % |
| **immer SHORT** | 74,0 % | 80,9 % | 87,5 % |
| n | 131 | 94 | 96 |

**Das LLM liegt hinter JEDER Regel, über alle Horizonte.** 27,7 % ist dabei
keine Zufallsquote (die wäre 50 %) — die Ausgabe ist systematisch, nur mit
falschem Vorzeichen. Das Modell wendet eine Gegenbewegungs-Logik in einem
Markt an, der weiter fiel. Passt zum Literaturbefund, dass LLMs
**contrarian strategies** bevorzugen.

**Zwei Messfehler auf dem Weg dorthin, beide meine:** erst die „tatsächliche
Richtung" aus MFE und Primärrichtung abgeleitet (Zirkelschluss, ergab 98,6 %),
dann die Richtungswahl an 1.668 HALTEN-Signalen gemessen, wo das Modell gar
keine Entscheidung traf. Beide gefunden, weil das Ergebnis unmöglich aussah.

### Was daraus folgt

**Zahlen informieren, Text weist an.** Eine Zahl ist Datenmaterial, das das
Modell abwägen kann. Ein Klartext-Urteil ist näher an einer Anweisung — es
sagt dem Modell, was es schließen soll. Genau davor warnt unsere eigene Regel
[[feedback_llm_synthese_kein_deterministischer_override]], nur in der anderen
Richtung: wir haben ein Werturteil in den Faktensatz geschmuggelt.

**Betroffen sind alle Felder desselben Bautyps:** `einordnung` (Trefferquote und
Systemgüte), `sqn_einordnung` („kaum handelbar"), `hebel_korrektur_hinweis`,
`eigenkapital_deckel_hinweis`, `ausfuehrbarkeit_hinweis`.

---

## 6. Der Grundbefund vom 10.08. — die Information ist nicht da

Bis hierher hat dieses Dokument nach einem Fehler im System gesucht: falsche
Fakten, falsche Rollen, falsche Aufbereitung. Der 10.08. verschiebt die Frage
eine Ebene tiefer.

### 6.1 Was gemessen wurde

Zwei voneinander unabhängige Verfahren auf denselben Daten, beide ohne
Sprachmodell und ohne Kontingent:

| Verfahren | was es findet |
|---|---|
| Nächste Nachbarn (k = 10 … 200) | lokale Ähnlichkeit: „ging es bei ähnlicher Lage ähnlich aus?" |
| Multinomiale Regression mit Quadrattermen | Schwellen und Zusammenspiel mehrerer Merkmale |

Zwei Merkmalsfamilien: die bisherigen (RSI, Abstand zum 200-Tage-Schnitt,
Schwankungsbreite, Renditen 20/60) und die aus der Price-Action-Praxis
(Marktstruktur höhere/tiefere Hochs und Tiefs, Abstand zu Widerstand und
Unterstützung in ATR, Position im letzten Schwung, Reife der Bewegung).

Beides zeitlich vorwärts geprüft, Bootstrap über Symbole, 8.441 Fälle.

### 6.2 Das Ergebnis

```
LONG                    Brier    Basis    Differenz               Urteil
  alte Merkmale         0,6351   0,6178   +0,0173 [+0,000..+0,035]  schlechter
  Trader-Merkmale       0,6188   0,6178   +0,0009 [-0,007..+0,009]  kein Befund
  beide                 0,6468   0,6178   +0,0290 [+0,011..+0,046]  schlechter

SHORT
  alte Merkmale         0,6217   0,6167   +0,0049 [-0,013..+0,023]  kein Befund
  Trader-Merkmale       0,6308   0,6167   +0,0140 [+0,006..+0,022]  schlechter
  beide                 0,6355   0,6167   +0,0188 [-0,001..+0,039]  kein Befund
```

**Kein einziges Verfahren schlägt die Basisrate.** Die Trader-Merkmale landen bei
LONG auf +0,0009 — das Modell reproduziert die Basisrate und sonst nichts.

Die Analogie über vergangene ähnliche Fälle, die als stärkster neuer Baustein
geplant war, ist **gesichert schlechter** als die Basisrate (k = 10: +0,1211,
95 % [+0,094 .. +0,152]) und nähert sich ihr mit wachsendem k von unten an — sie
wird also genau in dem Maß besser, in dem sie aufhört, Nachbarschaft zu benutzen.

### 6.3 Der Befund, der schwerer wiegt als die Vorhersagbarkeit

LONG erreicht das Ziel in **22,5 %** der Fälle. Bei Ziel 3 ATR gegen Stop 1,5 ATR:

```
0,225 × (+2R) + 0,565 × (−1R) + 0,21 × 0R = −0,115 R je Trade
```

**Der Aufbau verliert strukturell, bevor ein Modell etwas dazu sagt.** Breakeven
läge bei 33 % Trefferquote. Ein Verfahren müsste also nicht „besser als Zufall"
sein, sondern gezielt die Fälle über 33 % herausfischen. Genau das gelingt
keinem der geprüften.

### 6.4 Was die externe Literatur dazu sagt (recherchiert 10.08.)

1. **Technische Handelsregeln allgemein:** Park/Irwin prüften über 9.000 Regeln
   aus 12 Systemen — nach Kosten und Data-Snooping-Korrektur nicht profitabel
   (1985–2004). In US-Terminmärkten gab es substanzielle Gewinne 1978–1984, ab
   1985 nicht mehr. **Unser Messergebnis ist der Normalfall, kein Systemdefekt.**
2. **Krypto konkret:** Momentum wirkt auf 2–4 Wochen, Umkehr jenseits eines
   Monats. Der letzte Tagesertrag ist ein starkes Signal — bei illiquiden Coins
   als Umkehr, bei den größten als Momentum; die Liquidität dreht das Vorzeichen.
   Unser 20-Tage-Horizont liegt im Momentum-Fenster.
3. **Aber diese Evidenz ist durchweg QUERSCHNITTLICH.** Sie sagt: „Coins mit
   Eigenschaft X schlagen Coins mit Eigenschaft Y" — ein Rangvergleich zur
   selben Zeit. Wir fragen etwas anderes: „Erreicht dieser eine Coin sein
   absolutes Ziel vor dem Stop?" Für diese Einzeltitel-Barrierefrage gibt es
   kaum Evidenz.
4. **ATR-Ausstiege wirken bedingt.** Schnellere Take-Profit-Signale sind nicht
   besser als eine einfache Basisstrategie; am besten schneiden **gleitende und
   variable** ATR-Fenster ab. Wir haben feste 1,5 und 3,0.

### 6.5 Was daraus folgt

Wir haben eine Fragestellung gewählt, für die kaum Evidenz existiert
(Einzeltitel-Barriere), mit einer Geometrie, die dem Stand widerspricht (fest
statt variabel), und dann gemessen, dass sie nicht funktioniert. Alle drei
Punkte standen vorher in der Literatur.

Damit sind die bisherigen Einzelbefunde erklärt, ohne dass es weiterer bedarf:
dass das Sprachmodell die Basisrate nicht schlägt, dass die stumpfe Regel
gleichauf liegt, dass die Konfidenz nicht ordnet, dass die Kalibrierung nur die
halbe Strecke bringt. **Es war nie ein Modellproblem.**

Es deckt sich mit dem Befund vom 04.08.: 50 % der Signale standen einmal bei
+1R, angekommen sind 17,6 %. Der Einstieg war schon damals nicht das Problem.

### 6.6 Die offene Entscheidung

Drei Richtungen, keine davon technisch, alle drei eine Produktentscheidung:

1. **Zonengeometrie statt Vorhersage.** Anderer Horizont, anderes Verhältnis,
   variable statt feste ATR-Fenster — die Literatur weist hier eher Wirkung aus
   als bei besseren Merkmalen.
2. **Ausstieg statt Einstieg.** 50 % gegen 17,6 % sagen, dass der Wert im Halten
   und Herausgehen liegt, nicht im Auswählen.
3. **Ranking statt Einzelfall.** Coins gegeneinander ranken, mit Liquidität als
   unterscheidendem Merkmal — der Zuschnitt, für den die Krypto-Evidenz gilt.

**Nicht weitergebaut wird bis zur Entscheidung.** Die geplante Lagebeschreibung
würde Merkmale in Sprache übersetzen, von denen wir jetzt wissen, dass sie
nichts tragen — schöner verpackte Leere.

### 6.7 Werkzeuge (ohne Kontingentbedarf, wiederholbar)

| Skript | Frage |
|---|---|
| `pruefe_analogie.py` | Analogie gegen die Basisrate auf den Messlauf-Ankern |
| `pruefe_analogie_gross.py` | dasselbe auf Tausenden Fällen, vektorisiert, mit Bootstrap |
| `pruefe_trader_merkmale.py` | Trader-Merkmale gegen alte, Regression, walk-forward |

**Drei Konstruktionsfehler auf dem Weg, alle vor dem Ergebnis gefunden:**
Merkmalstabelle begann grundlos bei Index 250 statt 200 (48 von 80 Ankern
fielen heraus, systematisch die frühen); Nachbarn nach Beginndatum statt nach
Auflösungsdatum gefiltert (Leckage); Urteilszeile prüfte nur eine Richtung und
hätte ein gesichert schlechteres Ergebnis als „kein Befund" ausgegeben.

---

## 7. Der Rollen-Umbau — gebaut und am echten Fall geprüft (10.08. abends)

> ## ⚠ VERSIONSZUORDNUNG — vor 7.2 bis 7.9 lesen (nachgetragen 11.08. abends)
>
> **Alle Messbefunde in 7.2 bis 7.9 wurden mit Prompt-Stand `2026-08-10b`
> erhoben — also MIT der Betragsfrage in beiden Rollen.** Der Umbau vom 10.08.
> entfernte das Betragsfeld aus Schema und Pflichtfeldern, ließ die Frage im
> Prompt aber stehen. Das wurde erst am 11.08. abends bemerkt (7.10, Nachtrag
> 205). Wer einen dieser Befunde weiterverwendet, muss ihn auf einem aktuellen
> Prompt-Stand **wiederholen**, bevor er ihn als geltend behandelt.
>
> | Abschnitt | Befund | Status nach dem 11.08. |
> |---|---|---|
> | 7.2 / 7.5 | vier Prüfsteine, „4 von 5 richtig" | Stand `10b`, Erfolgsmaß **ohne Stop** gerechnet (7.9) — **beides zu wiederholen** |
> | 7.3 | Gegentest Marktbreite 20 % / 100 % | Stand `10b`, Mechanik-Nachweis — bleibt aussagekräftig |
> | 7.4 | Marktbreite wirkt invers | **kein LLM beteiligt** — unberührt |
> | 7.7 | „Betragsdeckel wirkt nicht" | Stand `10b`; **beide** Arme enthielten die Betragsfrage. Verglichen wurde „darf sie melden" gegen „darf nicht", nicht „mit" gegen „ohne" |
> | 7.8 | „das System kauft fast nie" | Stand `10b`, Anker nach Ausgang gewählt — Handlungsquote gilt, Trefferquote nicht |
> | 7.9 | Ursache Struktur-Etikett | **zurückgestuft**, siehe 7.10 und 7.11 |
>
> **Die Namen in diesem Abschnitt sind veraltet.** „Rolle A" heißt jetzt
> **Lagebild**, „Rolle B/BC" heißt **Befund** bzw. **Entscheidung**. Nur unsere
> Bezeichnungen, nie im Prompt.

### 7.1 Was gebaut wurde

Nach dem Grundbefund aus Abschnitt 6 wurde die LLM-Ebene neu aufgesetzt. Der
Nutzer benannte den Defekt präzise: **„Gate haben wir, LLM produziert auch
Ergebnisse — der Defekt ist das LLM, Eingang und Ausgang."**

| Baustein | Datei | Kern |
|---|---|---|
| Ausgang | `agent/empfehlung_vertrag.py` | keine Empfehlung ohne Betrag, Kurse, tragende Begründung |
| Eingang Asset | `agent/lagebeschreibung.py` | Aussagen statt Zahlen, **Bestand an erster Stelle** |
| Eingang Markt | `agent/marktbreite.py` | Anteil über 50-/200-Tage-Linie mit historischem Bezug |
| Rolle A | `agent/rolle_analyst.py` | Marktlage → Höchstbetrag. 1.147 Zeichen |
| Rolle BC | `agent/rolle_trader.py` | Aufbau + Bestand → Handlung. 2.036 Zeichen |
| Milde | `agent/antwort_normalisierung.py` | Formfehler korrigieren, Sinnfehler ablehnen |
| Durchlauf | `pruefe_rollenkette.py` | drei Stufen: trocken / ein Fall / Prüfsteine |

**Prompt: 3.183 Zeichen gegen 34.611 im Altsystem.** Rund 42 Aufrufe täglich
statt 40 — Variante 2 (Trader und Entscheider in einem Aufruf), nachdem der
erste Entwurf mit Selbstkonsistenz auf 162 kam.

### 7.2 Die vier Prüfsteine — echte Signale mit bekanntem Ausgang

```
BTC  KAUFEN     14.07.  → NICHTS_TUN   hätte −2,3 % vermieden
KAS  TAUSCHEN   14.07.  → NICHTS_TUN   hätte −8,9 % vermieden
KAS  NACHKAUFEN 15.07.  → NICHTS_TUN   hätte −8,6 % vermieden
GRIFFAIN HALTEN 21.07.  → NICHTS_TUN   +33,8 % wieder verpasst
```

**Der Kerndefekt ist behoben.** In allen drei Fällen erscheint der Bestand als
hochgewichteter Gegenbeleg — *„Bestand mit −16,8 % im Minus bei 3453 EUR
Einsatz"*. Im Altsystem stand dieselbe Information in den Risiken und hat die
Empfehlung nie erreicht; genau deshalb kaufte KAS am 15.07. in eine
Verlustposition nach.

Kein einziger `_warnung`-Marker: Das Hedging, das die Zusammenlegung von Rolle B
und C riskierte, trat nicht auf.

### 7.3 Das System reagiert — Gegentest bei maximaler Marktbreite

Der Einwand gegen 7.2 lautet: vier Mal NICHTS_TUN könnte auch ein blindes
System sein. Der Gegentest am breitesten Zeitpunkt der Historie widerlegt das:

```
Marktbreite  20 %  → Rolle A: höchstens 100 EUR → NICHTS_TUN
Marktbreite 100 %  → Rolle A: höchstens 500 EUR → NACHKAUFEN 500 EUR
```

Die Kette überträgt also: Rolle A deckelt, Rolle BC folgt.

### 7.4 Und der Befund, der schwerer wiegt als der Test

**In der gesamten Historie gibt es keinen Zeitpunkt mit breitem Markt, an dem
ein Einstieg 20 Tage später im Plus gewesen wäre.**

| Marktbreite über 50-Tage-Linie | Zeitpunkte | Median-Rendite 20 Tage danach |
|---|---|---|
| über 45 % | 15 | **−0,6 % bis −20,4 %** |
| 100 % (13.05., 23.05., 22.07.2025) | 3 | −14,0 %, −10,9 %, −12,2 % |

**Je breiter der Markt, desto schlechter der Einstieg.** Das ist keine Anomalie,
sondern deckt sich mit der externen Recherche: Krypto zeigt Momentum auf 2–4
Wochen und **Umkehr jenseits eines Monats**.

Zwei Konsequenzen:

1. **Der Test „erkennt das System Chancen?" ist mit diesen Daten nicht
   durchführbar** — es gab in 16 Monaten keine. Das erklärt auch, warum alle
   vier Prüfsteine zu NICHTS_TUN führen: es war fast immer richtig.
2. **Die Marktbreite als Eingangsgröße für Rolle A ist zu hinterfragen.** Sie
   wirkt in unseren Daten invers. Die Rolle folgt ihr aktuell im Wortsinn — bei
   100 % Breite erlaubt sie den größten Betrag, und genau dort war die
   Folgerendite am schlechtesten.

**Nicht weitergebaut wird an diesem Punkt.** Ob die Marktbreite umgedreht,
ersetzt oder mit dem Momentum-Fenster kombiniert gehört, ist eine
Konzeptentscheidung — keine Reparatur.

### 7.5 Prüfsteine NACH dem Betrags-Umbau (10.08. spät)

*Abschnitt 7.2 bleibt stehen — er hält den Stand VOR dem Umbau fest, als Rolle A
noch einen Höchstbetrag wählte. Dieser Abschnitt trägt den geprüften Stand.*

**Der Umbau:** Weder Rolle A noch Rolle BC nennt noch einen Betrag. Er wird
deterministisch aus der Zahl unabhängiger Faktoren abgeleitet (3+ → 500,
2 → 300, 1 → 100, 0 → keine Handlung). Extern belegt: *„Statt LLMs die
Positionsgröße eigenständig bestimmen zu lassen, sind sie am wirksamsten in
hybriden Systemen mit traditionellen quantitativen Risikoregeln."* Das
Designmuster entkoppelt Richtungslogik von quantitativer Größenbestimmung.

| Fall | Altsystem | **nach Umbau** | war richtig? |
|---|---|---|---|
| BTC 14.07. → −2,3 % | KAUFEN | NICHTS_TUN | **ja** |
| KAS 14.07. → −8,9 % | TAUSCHEN | **REDUZIEREN 300 EUR** | **ja** |
| KAS 15.07. → −8,6 % | NACHKAUFEN | NICHTS_TUN | **ja** |
| GRIFFAIN 21.07. → +33,8 % | HALTEN | NICHTS_TUN | nein, verpasst |
| BTC 22.07.2025 → −12,2 % (Median) | — | NICHTS_TUN | **ja** |

**Der Fortschritt gegenüber 7.2: eine aktive Handlung statt keiner.** Vor dem
Umbau lieferten alle vier Prüfsteine NICHTS_TUN; jetzt greift das System bei
KAS am 14.07. mit REDUZIEREN ein — und lag damit richtig. Die Begründung nennt
konkrete Werte: *„Angesichts der schwachen Marktbreite und der ungebrochenen
Abwärtsdynamik begrenze ich das Risiko durch Teilverkauf."*

### 7.6 Was diese Ergebnisse NICHT zeigen

**Nutzereinwand 10.08.: „oberes Ziel beachten — wenn du damit mehr Qualität und
mehr Signale meinst, dann ok."** Die ehrliche Bilanz an diesem Maßstab:

| Ziel | Stand |
|---|---|
| **mehr Qualität** | belegt — 4 von 5 richtig, die Handlung war richtig, Begründungen nennen Werte statt Allgemeinplätze |
| **mehr Signale** | **offen** — auf der Verkaufsseite ja, auf der Kaufseite unentschieden |

**Die eine Handlung ist ein Verkaufssignal.** Der Deadloop betraf handelbare
**LONG**-Signale. Alle Prüfsteine liegen in fallenden Phasen — es gab dort keine
Kaufgelegenheit, und deshalb ist die Frage *„produziert das System jetzt
Kaufsignale?"* mit diesen Fällen **nicht beantwortbar**.

Der Grund steht in 7.4: In 16 Monaten Historie gibt es keinen Zeitpunkt, an dem
ein Einstieg 20 Tage später im Plus gewesen wäre. **Wir können mit diesen Daten
nicht prüfen, ob das System Chancen erkennt — es gab keine.**

**Ein Einzelbefund, der gemessen gehört statt geglaubt:** Am selben Fall
(BTC, 22.07.2025) sagte das Modell vor dem Umbau NACHKAUFEN mit 500 EUR, danach
NICHTS_TUN. Vermutung: ein vorgegebener Höchstbetrag liest sich als
Handlungsaufforderung — passend zum Befund, dass Modelle Anweisungen auch dann
folgen, wenn es zu Verlusten führt. **Ein Fall ist kein Beleg**; das ist eine
Hypothese für eine gepaarte Messung, kein Ergebnis.

### 7.7 Gepaarte Messung zum Betragsdeckel — Hypothese widerlegt (11.08.)

**13 Anker, zwei Arme, bitgleich dieselben Fakten.** Vier Assetklassen-Phasen,
Krypto und Aktien, Aufwärts- wie Abwärtslagen.

**In jedem einzelnen Fall identische Aktion mit und ohne Deckel.** Die
Einzelfall-Beobachtung vom 10.08. (BTC 22.07.2025: mit Deckel NACHKAUFEN, ohne
NICHTS_TUN) war Sampling-Zufall. Der Betragsdeckel wirkt **nicht** als
Handlungsaufforderung.

Der Umbau bleibt trotzdem richtig — aus dem belegten Grund, nicht aus diesem:
LLMs sind bei der Positionsgröße am schwächsten, und das Designmuster der Praxis
entkoppelt Richtungslogik von quantitativer Größenbestimmung.

### 7.8 Der eigentliche Befund der Messung: das System kauft fast nie

```
BTC  2025-06-24  +13,0 %  →  REDUZIEREN   FALSCH
BTC  2025-12-25  +11,2 %  →  NICHTS_TUN   verpasst
BTC  2026-03-27  +13,3 %  →  NICHTS_TUN   verpasst
ETH  2025-06-24  +23,1 %  →  NICHTS_TUN   verpasst
ETH  2026-03-27  +17,9 %  →  NICHTS_TUN   verpasst
VST  2024-09-16  +48,3 %  →  NICHTS_TUN   verpasst
PLTR 2022-09-06  +16,2 %  →  NICHTS_TUN   verpasst
PLTR 2024-07-24  +22,3 %  →  KAUFEN       RICHTIG
```

**Sieben von dreizehn Ankern brachten zweistellige Gewinne. Das System handelte
bei einem davon — und lag richtig.**

Zwei Konsequenzen:

1. **Das Problem ist nicht die Qualität der Entscheidungen, sondern ihre Zahl.**
   Trefferquote bei Käufen: 1 von 1. Handlungsquote: 2 von 13.
2. **Die Erklärung aus 7.6 ist widerlegt.** Dort stand, es habe „keine
   Kaufgelegenheiten gegeben". Die gab es — bei BTC, ETH, VST und PLTR, mit
   +11 bis +48 %. Das System hat sie gesehen und nichts getan. Der Befund aus
   7.4 (kein breiter Markt war je ein guter Einstieg) galt für die
   **Marktbreite**, nicht für Einzelwerte.

**Das ist der Deadloop, erstmals über Assetklassen hinweg gemessen** — nicht auf
Altcoins beschränkt, nicht auf einen Zeitraum, nicht durch fehlende Gelegenheiten
erklärbar.

**Nächster Schritt, nicht mehr in dieser Sitzung:** Herausfinden, WARUM das
Modell bei +23 % Aufwärtsbewegung NICHTS_TUN sagt. Die Belege der abgelehnten
Fälle liegen in `betragsdeckel*.json` und sind lesbar — dort steht die
Begründung im Klartext.

### 7.9 DIE URSACHE gefunden: eine falsch beschriftete Marktstruktur (11.08.)

**Nutzerfrage: „wenn wir immer auf 20 Tage breiten Marktanstieg gehen, wird es
u.U. nicht funktionieren?"** Die Prüfung gab ihm doppelt recht.

**Erstens war mein Erfolgsmaß falsch.** Ich hatte „richtig" an der
20-Tage-Endrendite gemessen. Mit Stop sieht es anders aus:

```
Anker                20T-Rendite   zwischenzeitl. Tief   mit 1,5-ATR-Stop
BTC  2025-06-24          +13,0 %              −0,9 %      ZIEL
BTC  2025-12-25          +11,2 %              −0,7 %      ZIEL
BTC  2026-03-27          +13,3 %              −2,1 %      ZIEL
ETH  2025-06-24          +23,1 %              −3,1 %      ZIEL
ETH  2026-03-27          +17,9 %              −2,8 %      ZIEL
VST  2024-09-16          +48,3 %              −0,6 %      ZIEL
PLTR 2022-09-06          +16,2 %              −2,1 %      keines
PLTR 2024-07-24          +22,3 %             −10,7 %      STOP
```

Die sechs verpassten Fälle waren **saubere Gelegenheiten** — Ziel erreicht, Stop
nie in Gefahr. Und der einzige Fall, in dem das System kaufte, wäre
**ausgestoppt** worden. Korrigierte Bilanz: nicht 1 von 1 richtig, sondern
**0 von 1**.

**Zweitens, und das ist die Ursache:** Der Faktensatz für ETH am 24.06.2025
enthielt zwei Sätze, die sich widersprechen —

```
Die Marktstruktur zeigt tiefere Hochs und tiefere Tiefs
  — ein intakter ABWÄRTSTREND.
Kursentwicklung: 5 Tage −2,9 %, 20 Tage −6,1 %, 60 Tage +37,0 %
```

Das Modell folgte dem ersten und gewichtete den zweiten als **gering**:

```
dagegen  hoch    Intakter Abwaertstrend mit tieferen Hochs und Tiefs
dagegen  hoch    Gesamtmarkt in Schwaechephase
dafuer   mittel  Naechste Unterstuetzung
dafuer   GERING  60-Tage-Entwicklung mit +37,0 % noch im groesseren Aufwaertstrend
```

**Der Fehler liegt in `agent/lagebeschreibung.py::_struktur()`.** Sie vergleicht
die letzten **zwei** Swing-Punkte — wenige Tage — und belegt das Ergebnis mit
einem absoluten Wort: *„ein intakter Abwärtstrend"*. Bei einer Korrektur
innerhalb eines starken Aufwärtstrends ist das schlicht falsch beschriftet. Eine
Rückwärtsbewegung von 6 % nach einem Anstieg von 37 % ist eine Kaufgelegenheit,
kein Abwärtstrend.

**Das erklärt sechs von sechs verpassten Gelegenheiten** — und zwar besser als
jede Modellkritik. Nicht das Modell hat versagt; es hat einer irreführenden
Beschriftung geglaubt, die ich geschrieben habe.

**Der Fix (nicht mehr in dieser Sitzung gebaut):** Die Struktur relativ zur
übergeordneten Bewegung formulieren, ohne absolutes Etikett. Etwa: *„Auf Sicht
von zwei Wochen tiefere Hochs und Tiefs, innerhalb eines 60-Tage-Anstiegs von
+37 % — eine Korrektur im Aufwärtstrend."* Derselbe Fakt, ohne das Wort, das
mehr Gewicht bekommt als die Zahl daneben.

> **NACHTRAG 11.08. abends — die Behauptung „erklärt sechs von sechs" ist
> zurückgestuft.** Sie beruht auf EINER gelesenen Begründung, nicht auf sechs
> (siehe 7.10), und die Zellenzählung in 7.11 zeigt, dass dieser Defekt den
> Deadloop **nicht** erklären kann. Der Fix bleibt richtig, seine erwartete
> Wirkung ist aber klein und muss **symmetrisch** sein — der häufigere Fehler
> ist das Gegenteil.

---

## 7.10 Die Belege existieren nicht — Rückstufung von „sechs von sechs" (11.08. abends)

**Auftrag:** vor jedem weiteren Schritt prüfen, ob die Ursachenbehauptung aus 7.9
trägt. Sie stützt sich darauf, dass die Begründungen der sechs verpassten Fälle
gelesen wurden. Das Ergebnis der Prüfung:

| Prüfung | Ergebnis |
|---|---|
| `betragsdeckel*.json` auf der Platte | **nicht vorhanden**, projektweite Suche |
| je committet | **nein** (`git log --diff-filter=A` leer) |
| in `.gitignore` ausgespart | **nein** — also nicht bewusst, sondern verloren |
| Begründungen im Ergebnisformat | **nein** — `messe_betragsdeckel.py` speichert `aktion`, `betrag`, `deckel`, `faktoren`, `richtig` |
| Lauf rekonstruierbar | **nein** — ein Commit, dort 6 Anker (VST ×3, PLTR ×3), kein BTC/ETH |

**Die 13 Anker aus 7.7 und die 8 aus 7.8 stammen aus mehreren Läufen mit
überschriebener ANKER-Liste.** Der Repo-Stand bildet keinen davon ab.

**Damit gilt:** „erklärt sechs von sechs" steht auf **einer** gelesenen
Begründung (ETH 24.06.2025, aus zwei nachgeholten Aufrufen). Der Satz in 7.8,
die Belege lägen lesbar in `betragsdeckel*.json`, ist in **beiden** Teilen
falsch. Zusicherung 2 aus Methodik 2.18 wurde geschrieben, aber nie umgesetzt.

### Was die Prüfung dafür ohne Modellaufruf geklärt hat

Die Bestandslage der acht Anker, direkt aus `holdings`:

```
BTC  2025-06-24  → REDUZIEREN   Bestand VORHANDEN (0,0506 @ 68.275 EUR)
BTC  2025-12-25  → NICHTS_TUN   Bestand VORHANDEN
BTC  2026-03-27  → NICHTS_TUN   Bestand VORHANDEN
ETH  2025-06-24  → NICHTS_TUN   "nicht im Bestand" (Menge 0)
ETH  2026-03-27  → NICHTS_TUN   "nicht im Bestand"
VST  2024-09-16  → NICHTS_TUN   "nicht im Bestand" (kein Einstand)
PLTR 2022-09-06  → NICHTS_TUN   "nicht im Bestand"
PLTR 2024-07-24  → KAUFEN       "nicht im Bestand"
```

**Vier der sechs verpassten Gelegenheiten hatten keinen Bestand.** Die
Hypothese, der hochgewichtete Bestandsblock unterdrücke die Handlung, scheidet
für die historischen Anker damit aus — für den **Produktivbetrieb** (wo
tatsächlich gehalten wird) bleibt sie offen. Zwei Populationen, keine Rivalen.

### Zwei Funde, die über die Messung hinausgehen

**FUND 1 — die Produktion meldet die Hälfte des Depots als „nicht im Bestand".**

```
28 Positionen tatsächlich gehalten
14 davon meldete die Rollen-Ebene als "nicht im Bestand":
   3QSS CEBS DBPK EXH3 ISOC OD7C OD7H OD7L OD7N PLTR VSN VST VVMX X136
```

`agent/lagebeschreibung.py::_bestand()` behandelte „Einstand fehlt" identisch mit
„nicht investiert" und gab aus: *„VST ist nicht im Bestand."* Das ist **falsch,
nicht unvollständig**. Das Modell entscheidet über einen Neukauf in der Annahme,
wir hielten nichts — bei der Hälfte des Depots. Dieselbe Fehlerklasse wie der
KAS-Fall vom 15.07., nur breiter.

> **KORREKTUR am selben Abend — die Ursache ist eine andere und eindeutigere.**
> Hier stand zuerst „14 Positionen **ohne Einstandspreis**". Das ist falsch:
> **jede gehaltene Position hat einen Einstand, keine einzige ohne.** Die 14
> führen ihn in `avg_buy_price_manual_eur` statt in `avg_buy_price_eur`.
>
> Der Fehler ist ein **Lesefehler**: `pruefe_rollenkette::_bestand()` fragte nur
> die berechnete Spalte ab und umging damit die seit jeher etablierte
> Vorrangregel `database/models.py::effective_avg_buy_price_eur` (manueller Wert
> geht vor). Die Daten waren da, der Code hat nicht hingesehen.
>
> **Behoben 11.08.** — beide Spalten werden gelesen, manuell hat Vorrang. Als
> Netz unterscheidet `lagebeschreibung::_bestand()` jetzt zusätzlich drei
> Zustände statt zwei: nicht im Bestand · im Bestand ohne bekannten Einstand ·
> im Bestand mit G/V. VST liefert danach: *„VST ist bereits im Bestand: 248 EUR
> investiert, aktuell 148 EUR wert — 100 EUR im Minus (−40,3 %)."*

**FUND 2 — `_kurs_eur()` liest immer die älteste Zeile.**
`price_cache` hat **1.526 Zeilen für 55 Symbole** — eine Historie, kein Cache.
`pruefe_rollenkette.py::_kurs_eur()` fragt ohne `ORDER BY` mit `fetchone()` ab
und bekommt damit die älteste. Für VST/PLTR hat gerade die älteste Zeile keinen
EUR-Kurs, während neuere ihn führen (139,20 / 111,10) → unnötiger Rückfall auf
die Quellwährung. Bei Krypto wird ein veralteter Umrechnungskurs verwendet.
Einzeiler-Fix.

### Drei Konstruktionsfehler, die vor einem Neulauf zu beheben sind

| | Fehler | Stelle |
|---|---|---|
| K1 | Erfolgsmaß ist die 20-Tage-**Endrendite** — das in 7.9 widerlegte Maß | `wahrheit()`, `war_richtig()` |
| K2 | Begründungen werden nicht gespeichert | Ergebniszeile |
| K3 | ANKER-Liste wird überschrieben statt versioniert | Modulkonstante |

---

## 7.11 Zellenzählung: der Struktur-Defekt erklärt den Deadloop NICHT (11.08. abends)

**Frage:** Wie häufig ist die Konstellation aus 7.9 überhaupt — Etikett
„Abwärtstrend" bei stark positiver 60-Tage-Bewegung? Ohne Modellaufruf, über
44 Symbole und die ganze Historie (CAT ausgeschlossen, kaputte FX-Reihe).

**Absicherung:** Die Fraktale werden einmal je Symbol vorberechnet (sonst
quadratische Laufzeit). Gegenprobe gegen das Original `_struktur()`:
**291 Stichproben, 0 Abweichungen.**

**Zelle A — Etikett ABWÄRTS bei positiver 60-Tage-Bewegung:**

| 60-Tage-Schwelle | Krypto | Aktien/Rohstoff |
|---|---|---|
| ≥ +10 % | 6,21 % | 3,32 % |
| ≥ +20 % | 4,19 % | 1,12 % |
| **≥ +30 %** (ETH-Fall lag bei +37 %) | **2,71 %** | 0,44 % |
| ≥ +40 % | 1,73 % | 0,29 % |

**Der Deadloop ist 115 von 118 Signalen — 97,5 %. Ein Defekt auf 3 % der Tage
kann das nicht erklären.** Selbst bei der lockersten Schwelle sind es 6 %.

**Der Widerspruch zu 7.9 löst sich auf:** Die acht Anker waren nach großen
Gewinnen ausgewählt. Unter *solchen* Tagen ist eine Korrektur im Aufwärtstrend
weit häufiger als unter allen Tagen. `_struktur()` kann diese sechs Fälle also
erklären und für den Deadloop trotzdem fast bedeutungslos sein.

### Die Spiegelzelle ist größer als die Defektzelle

```
Krypto   Zelle A (abwaerts-Etikett bei 60T ≥ +10 %)    6,21 %
         Zelle C (aufwaerts-Etikett bei 60T ≤ −10 %)  11,39 %   ← fast doppelt
```

Das Etikett „intakter **Aufwärts**trend" während eines 60-Tage-Rückgangs ist der
häufigere Fehler. **Ein Punktfix nur in Richtung „mehr kaufen" würde die
kleinere Hälfte beheben und die größere verschärfen** — er schöbe in fallende
Märkte hinein. Die Beschriftung muss symmetrisch korrigiert werden.

### Das Aufwärts-Etikett ist unzuverlässig, nicht das Abwärts-Etikett

```
Krypto   abwaerts 35,3 %  aufwaerts 25,2 %  verengt 23,6 %  weitet 15,8 %
Aktien   aufwaerts 35,6 % abwaerts  29,2 %  weitet  18,1 %  verengt 17,2 %

Übereinstimmung des Etiketts mit der 60-Tage-Bewegung (Krypto):
   "abwaerts"   26,2 / 35,3 = 74 %
   "aufwaerts"  10,7 / 25,2 = 42 %   ← kaum besser als ein Münzwurf
```

**Korrektur einer Fehldeutung im Verlauf:** Zuerst hatte ich das häufige
Abwärts-Etikett mit „zwei Jahre Bärenmarkt" erklärt. Das ist falsch —
`Test_und_Verifikationsmethodik.md` hält fest, dass die **Kursreihen** alle drei
Phasen enthalten (bulle 35,1 %, bär 36,0 %, gemischt 28,8 %). Ausnahmslos
„baer" tragen die **Signale**, nicht die Reihen. Der Detektor ist also nicht zu
bärisch — sein **Aufwärtsurteil** trägt nicht.

### Was das am Plan ändert

| | vorher | jetzt |
|---|---|---|
| `_struktur()`-Fix | Priorität 1, „erklärt den Deadloop" | echter Defekt, **begrenzte Wirkung**, symmetrisch zu fixen |
| Ursache des Deadloops | gefunden | **wieder offen** — Kandidaten: Bestandsmechanismus (Produktion, FUND 1), Geometrie (6.3), Regime |
| Textform-Regeln R-T1/R-T2 | Nebenprodukt | **das tragende Ergebnis** — ein Punktfix wirkt nachweislich in die falsche Richtung |

**Werkzeug:** `zaehle_zellen.py` (Scratchpad, ohne Kontingentbedarf,
wiederholbar; gehört bei Übernahme nach Methodik 2.13).

---

## 7.12 Degradierung widerlegt — und ein erster Hinweis auf die Betragsfrage (11.08. spät)

**Frage:** `empfehlung_vertrag.validiere()` nimmt eine Kaufempfehlung ohne
gültigen Ausstieg auf NICHTS_TUN zurück (R-A7). Alle bisherigen Skripte
speicherten nur `aktion` — ein degradierter Kauf war von einem abgewogenen
NICHTS_TUN nicht unterscheidbar. Damit konnte 7.8 („das System kauft fast nie")
beides bedeuten.

**Werkzeug:** `messe_degradierung.py`, Prompt-Stand `2026-08-11`, 16 Aufrufe.
Behebt K1 (Erstdurchgang statt Endrendite), K2 (speichert Begründung, Belege,
`_degradiert`, `_korrekturen`, Bestandslage, Prompt-Stand) und K3 (`ANKER_7_8`
benannt und versioniert).

### Ergebnis: null degradierte Käufe

```
ROH (was das Modell sagte):  REDUZIEREN 2, NICHTS_TUN 5, KAUFEN 1
FINAL (nach dem Vertrag):    REDUZIEREN 2, NICHTS_TUN 5, KAUFEN 1
DEGRADIERT: 0 von 8
```

**Die Hypothese ist für diese acht Anker widerlegt.** Jedes NICHTS_TUN stand
schon in der Rohantwort. Der mechanische Pfad existiert im Code, aber er hat
hier nicht gefeuert. Pfad geschlossen.

### Der eigentliche Hinweis: drei Aktionen haben sich geändert

| Anker | Bestand | Stand `10b` | Stand `2026-08-11` | Ausgang |
|---|---|---|---|---|
| BTC 2025-06-24 | ja | REDUZIEREN | REDUZIEREN | ZIEL |
| BTC 2025-12-25 | ja | NICHTS_TUN | NICHTS_TUN | ZIEL |
| BTC 2026-03-27 | ja | NICHTS_TUN | **REDUZIEREN** | ZIEL |
| ETH 2025-06-24 | nein | NICHTS_TUN | NICHTS_TUN | ZIEL |
| ETH 2026-03-27 | nein | NICHTS_TUN | NICHTS_TUN | ZIEL |
| VST 2024-09-16 | nein | NICHTS_TUN | **KAUFEN** | ZIEL |
| PLTR 2022-09-06 | nein | NICHTS_TUN | NICHTS_TUN | ZIEL |
| PLTR 2024-07-24 | nein | KAUFEN | **NICHTS_TUN** | **STOP** |

**Auf den beiden entscheidenden Fällen ging es in die richtige Richtung:** VST
wird gekauft und erreicht das Ziel an Tag 4; PLTR 2024-07-24 wird nicht mehr
gekauft und wäre an Tag 7 ausgestoppt worden. BTC 2026-03-27 ging in die
falsche Richtung (REDUZIEREN vor einem Anstieg).

> **DAS IST KEIN BELEG.** Der Lauf ist **nicht gepaart**, n = 8, die Anker sind
> nach ihrem Ausgang ausgewählt, und B6 sagt, dass das Modell bei identischer
> Eingabe in ~12 % der Fälle anders antwortet. Drei Änderungen bei acht Ankern
> liegen im Bereich reiner Stichprobenstreuung. Es ist ein **Hinweis**, der die
> gepaarte Messung rechtfertigt — nicht ihr Ergebnis.

**Die ETH-Fälle bleiben NICHTS_TUN.** Das Entfernen der Betragsfrage hat sie
nicht bewegt — konsistent mit 7.11: der Struktur-Defekt ist ein eigener,
kleinerer Mangel.

### Nebenbeobachtung zum Bestand (n = 3, Hinweis)

```
mit Bestand  (3):  REDUZIEREN, NICHTS_TUN, REDUZIEREN     — kein einziger Kauf
ohne Bestand (5):  NICHTS_TUN x4, KAUFEN                  — der einzige Kauf
```

Beide REDUZIEREN traten ausschließlich dort auf, wo ein Bestand vorlag; der
einzige Kauf dort, wo keiner vorlag. Bei n = 3 ist das nichts als ein Hinweis —
aber es ist derselbe Mechanismus, der in 7.10 für die historischen Anker
ausgeschlossen wurde und für den Produktivbetrieb offen blieb. Gepaart prüfbar:
dieselben Fakten mit und ohne Bestandsblock.

### Erstdurchgang: was der Horizont wirklich kostet

```
bis  5 Tage:  offen 7, ZIEL 1
bis 10 Tage:  offen 6, ZIEL 1, STOP 1
bis 20 Tage:  ZIEL 6, offen 1, STOP 1
bis 40 Tage:  ZIEL 7, STOP 1
```

**Bei 3 ATR Zieldistanz lösen sich die Fälle bei 16 bis 19 Tagen auf.** Ein
Horizont von 5 oder 10 Tagen erklärt das meiste zu „offen" — nicht zu
„gescheitert". Die Zeitschranke gehört an die **Zieldistanz** gekoppelt, nicht
frei gewählt. Der Einwand des Nutzers, 20 Tage seien womöglich zu lang, trifft
für diese Zieldistanz nicht zu; er würde bei einem engeren Ziel zutreffen.

---

## 7.13 Ebene 1 umgesetzt — und ein Werturteil, das das System selbst erzeugt (11.08. spät)

### Behoben

| Fix | Datei | war |
|---|---|---|
| Einstand liest **beide** Spalten, manuell hat Vorrang | `pruefe_rollenkette::_bestand()` | nur `avg_buy_price_eur` → 14 Positionen als „nicht im Bestand" |
| Drei Zustände statt zwei (Netz) | `lagebeschreibung::_bestand()` | „Einstand fehlt" = „nicht investiert" |
| `order by fetched_at desc limit 1` | `pruefe_rollenkette::_kurs_eur()` | las die **älteste** `price_cache`-Zeile |
| Struktur **ohne Etikett**, mit Fenster und Maßstab (R-T1/R-T2) | `lagebeschreibung::_struktur()` | „ein intakter Abwärtstrend" |
| `umgeworfen_durch` wird mitgespeichert | `messe_degradierung.py` | fehlte — K2 galt auch für mich |

### 0d Kausalitätsprobe — bestanden, nachdem sie richtig konstruiert war

**24 Anker × 4 Zukunftslängen, 0 Abweichungen.** Kein Lookahead.

Die **erste** Fassung der Probe schlug bei 18 von 18 an — und war selbst falsch
gebaut: sie verglich die volle Reihe gegen `reihe[:i+1]` und stellte damit einen
*abgeschlossenen* Tag einem *laufenden* gegenüber. `tag_vollstaendig = index <
len(reihe) - 1` nimmt den laufenden Tag korrekt aus dem Umsatzfenster. Die
richtige Probe hält den Tag abgeschlossen und variiert nur die Zukunft dahinter.

> **Bemerkenswert bleibt die Folge:** Im Backtest sieht das Modell eine
> Umsatzzeile mehr als in der Produktion am laufenden Tag. Beides ist für sich
> richtig — aber **jede Messung auf historischen Ankern ist dadurch leicht
> optimistisch** gegenüber dem Produktivverhalten. Bei Vergleichen mitdenken.

### Der Struktur-Fix wirkt im Text, nicht in der Gewichtung

ETH 2025-06-24, ein Durchlauf nach dem Fix. Eingabe jetzt ohne Etikett:

```
Auf Sicht der letzten 8 Handelstage zeigt die Marktstruktur tiefere Hochs und
tiefere Tiefs; der letzte Wendepunkt liegt 2 Handelstage zurueck.
Zum Vergleich: ueber 60 Handelstage steht der Kurs +37.0 %.
```

Ergebnis: weiterhin **NICHTS_TUN**. Und das Modell erfindet das Etikett selbst —
*„die intakte Abwärtsstruktur verbietet einen Neueinstieg"*. Der 8-Tage-Beleg
trägt Gewicht **hoch**, die +37 % landen in `was_dagegen`, also als Einwand
gegen die eigene Entscheidung statt als Argument darin.

**Das bestätigt 7.11 am Einzelfall:** der Etikettdefekt war nicht die Ursache.
Der Fix bleibt richtig (die Beschriftung war falsch), aber er bewegt die
Entscheidung nicht. *n = 1, B6-Drift ~12 % — als Beobachtung zu lesen, nicht als
Messung.*

### DER FUND: das Werturteil entsteht jetzt IM SYSTEM

Eingabe an das Lagebild:

```
Von 13 beobachteten Coins stehen 1 ueber ihrer 50-Tage-Linie (8 %).
In den letzten 250 Handelstagen war dieser Anteil in 46 % der Faelle NIEDRIGER.
```

Also ein **knapp durchschnittlicher** Wert — der Kalibrierungssatz sagt es
ausdrücklich. Ausgabe:

```
"Der Gesamtmarkt befindet sich in einer EXTREMEN SCHIEFLAGE mit starkem
 Abwaertsdruck."
```

Und dieser Satz erreicht die Entscheidung als Beleg mit Gewicht **hoch**:
*„Gesamtmarkt in extremer Schieflage mit starkem Abwärtsdruck"*.

**Die Architekturlücke:** `enthaelt_werturteile()` prüft **Eingaben**. Die
Ausgabe des Lagebilds wird zur Eingabe der Entscheidung — und wird **nicht**
geprüft. B2 (Werturteile im Faktensatz) ist damit nicht behoben, sondern nur
verschoben: das Urteil wird jetzt vom System selbst erzeugt.

**Warum das ein besserer Deadloop-Kandidat ist als alles bisher Untersuchte:**

| Kandidat | Anteil der Aufrufe |
|---|---|
| Struktur-Etikett (7.9) | 2,71 % der Krypto-Tage |
| Degradierung (7.12) | 0 von 8 |
| Betragsfrage (Nachtrag 205) | 100 % — offen |
| **Werturteil aus dem Lagebild** | **100 %, und es trägt Gewicht *hoch*** |

**Nächster Schritt:** den Wächter auf die **Zwischenausgabe** anwenden — Lagebild
→ Entscheidung. Kein Modellaufruf nötig, um zu zählen, wie oft die Ausgabe
Wertwörter enthält, die die Eingabe nicht hergibt.

---

## 7.14 Wächter auf die Zwischenausgabe — und der Kandidat, der übrig bleibt (11.08. spät)

**Neues Werkzeug:** `agent/waechter_zuspitzung.py`. Kein Nachbau von
`enthaelt_werturteile()` — der prüft **Feldnamen in einem Dict**, dieser prüft
**Freitext einer Zwischenausgabe**. Zwei Stufen (harte Gradwörter / weiche,
kontextabhängige) und eine Deckungsprüfung gegen den historischen Bezug der
Eingabe. Ohne Modellaufruf.

### Ist-Zustand: 1 von 8 — meine Behauptung war falsch

```
BTC 2026-03-27   hart=['drastisch']   VERSTOSS   (Perzentil waere [24, 0] gewesen)
uebrige 7        hart=[]              kein Verstoss
```

**Ich hatte aus dem einen ETH-Durchlauf auf „100 % der Aufrufe, mit Gewicht
hoch" geschlossen. Das ist zurückgenommen** — die Rate liegt bei 1 von 8, nicht
bei 8 von 8. Dritter Fall desselben Fehlers an einem Tag (n = 1
verallgemeinert). Der Wächter hat ihn sofort sichtbar gemacht; genau dafür ist
er da, und er bleibt als stehende Naht in der Kette.

**Nachtrag zum ETH-Fall:** Der Durchlauf mit *„extremer Schieflage"* lief über
`pruefe_rollenkette` mit `mit_bezug=True` und Perzentilen [40, 28] — mitten im
unauffälligen Band. Das war also ein **echter** unbelegter Verstoß, und der
Wächter erkennt ihn. Nur ist er selten, nicht die Regel.

### Dritter Backtest/Live-Unterschied, gefunden dabei

```
pruefe_rollenkette / Produktion   mit_bezug=True    → Kalibrierungssatz vorhanden
messe_betragsdeckel.py            mit_bezug=False   → fehlt
messe_degradierung.py             mit_bezug=False   → aus dem ersten kopiert
```

**Alle Ankermessungen liefen ohne den Satz, der die Zuspitzung eindämmen soll.**
Zusammen mit `tag_vollstaendig` (7.13) sind das drei Stellen, an denen Messung
und Produktion dem Modell Unterschiedliches zeigen. Vor jedem Vergleich prüfen.

### DER KANDIDAT, DER ÜBRIG BLEIBT: das Breite-Urteil

| Anker | Perzentile | Lagebild | Aktion |
|---|---|---|---|
| BTC 2025-06-24 | [40, 28] | schmal_getragen | REDUZIEREN |
| BTC 2026-03-27 | [24, 0] | schmal_getragen | REDUZIEREN |
| ETH 2025-06-24 | [40, 28] | schmal_getragen | NICHTS_TUN |
| ETH 2026-03-27 | [24, 0] | schmal_getragen | NICHTS_TUN |
| BTC 2025-12-25 | [2, 2] | breit_getragen | NICHTS_TUN |
| VST 2024-09-16 | [84, 8] | breit_getragen | **KAUFEN** |

> **Einschränkung zuerst:** Die acht Anker sind **nach großen Gewinnen
> ausgewählt**. Dass alle vier „schmal"-Fälle das Ziel erreichten, ist deshalb
> **kein Beleg** — bei dieser Auswahl erreicht fast alles das Ziel. Die
> Ausgangsspalte ist per Konstruktion nahezu konstant.

**Was nicht an der Auswahl hängt:** vier „schmal_getragen" → kein einziger Kauf,
zwei REDUZIEREN. Der einzige Kauf fällt auf einen „breit_getragen"-Anker. Die
Kette **überträgt** das Breite-Urteil in die Handlungsrichtung — wie schon der
Gegentest in 7.3 (20 % Breite → NICHTS_TUN, 100 % → NACHKAUFEN), hier an echten
Ankern bestätigt.

**Und die Richtung ist die gemessen falsche.** 7.4, unabhängig über die ganze
Historie: kein Zeitpunkt mit breitem Markt war je ein guter Einstieg — 15
Zeitpunkte über 45 % Breite, Median −0,6 % bis −20,4 %.

| Kandidat | Anteil der Aufrufe | Status |
|---|---|---|
| Struktur-Etikett | 2,71 % | behoben, war nicht die Ursache (7.11/7.13) |
| Degradierung | 0 von 8 | widerlegt (7.12) |
| Zuspitzung | 1 von 8 | real, selten; Wächter steht |
| Betragsfrage | 100 % | offen, gepaart zu messen |
| **Breite-Urteil** | **100 %** | **überträgt (7.3) UND zeigt in die gemessen falsche Richtung (7.4)** |

**Das ist der einzige Kandidat, dessen Existenz nicht mehr belegt werden muss.**
7.3 zeigt die Übertragung, 7.4 die Richtung. Offen ist nur die **Größe** — und
die gehört in denselben gepaarten Lauf wie die Betragsfrage.

---

## 7.15 Marktbreite ist für dieses System nicht baubar — und 16 Assets sind unsichtbar (11.08. spät)

**Nutzervorgabe:** *„Alle ist — Krypto Spot, Hebel, Aktien, ETF und Rohstoffe
(Bitpanda)."* Und: *„die Marktbreite sehe ich für das Einzelasset nicht so
relevant."* Beides geprüft, beides bestätigt.

### Der Defekt am konkreten Fall

Am VST-Anker (Aktie, 16.09.2024) liefert das Lagebild:

```
"Von 10 beobachteten COINS stehen 6 ueber ihrer 200-Tage-Linie (60 %)."

Die 10 sind:  CEBS · EXH3 · ISOC · PLTR · VST · VVMX
              3 Rohstoff-Futures · SPY        —  kein einziger Coin
```

Krypto hat an diesem Datum keine 200 Tage Historie. Drei Fehler in einem Satz:

1. **Gemischter Korb** — Krypto, Aktien, Rohstoff-Futures und ein S&P-ETF in
   einer Zahl. Das ist die Breite von „was wir tracken und wovon Daten da sind".
2. **Falsche Beschriftung** — „Coins" für einen Korb ohne Coins. Und das
   beurteilte Asset steckt selbst im Korb.
3. **Die Korbgröße wechselt** — 30 Symbole beim 50-Tage-Fenster, 10 beim
   200-Tage-Fenster. Der Kalibrierungssatz („in 84 % der Fälle war dieser Anteil
   niedriger") vergleicht deshalb gegen eine Historie mit **anderer
   Zusammensetzung**. Das Perzentil ist bedeutungslos — und es ist genau der
   Satz, der die Zuspitzung eindämmen sollte (7.14).

Im selben Block stehen zwei gegenläufige Signale: 50-Tage-Breite im 84.
Perzentil, 200-Tage-Breite im 8. — aus zwei verschieden großen Körben.

### Warum eine Breite JE KLASSE ebenfalls nicht geht: es fehlen die Mitglieder

| Klasse | Watchlist | mit Kursreihe | Breite möglich? |
|---|---|---|---|
| Krypto | 44 | 35 | ja |
| ETF | 7 | 4 | **nein** |
| Rohstoffe | 4 | **0** | **nein** |
| Aktien | 2 | 2 | **nein** |

**Für vier von fünf Klassen ist eine Marktbreite arithmetisch unmöglich.** Das
ist keine Ermessensfrage, das ist eine Abzählung. Der gemischte Korb war der
Notbehelf, der genau daraus entstanden ist.

### Und der härtere Fund: 16 von 57 Assets sind für die Rollen-Ebene unsichtbar

```
Rohstoffe   OD7C OD7H OD7L OD7N   Reihen liegen unter _ROHSTOFF_FUTURES_OD7C/H/N
                                  -> Schluessel passt nicht, OD7L fehlt ganz
ETF         3QSS DBPK X136        keine Reihe
Krypto      BRETT CANTON EURCV IO KAIA KAITO SUPRA VSN XNO   keine Reihe
```

`lade_reihen_aus_db()` liefert für diese Symbole `None` — **`beschreibe_lage()`
kann sie nicht beschreiben, die Kette hat für sie keine Eingabe.** Für die
gesamte Assetklasse Rohstoffe gilt das ausnahmslos, obwohl die Futures-Reihen
in der Datenbank liegen. Direkte Bestätigung des Nutzerhinweises
*„alle müssen funktionieren"*.

### Was an die Stelle tritt: Benchmark je Klasse statt Breite

Das Kriterium: **ein Marktfakt gehört in die Beurteilung, wenn er zwischen
Assets unterscheidet. Wirkt er auf alle gleich, ist er ein Risikoparameter — und
Risiko ist deterministisch.**

| Fakt | unterscheidet? | gehört wohin |
|---|---|---|
| Marktbreite, Fear & Greed, FOMC-Termine | nein | Risikoschicht |
| BTC-Dominanz, DXY | ja | Beurteilung |
| **Lage des Assets zu SEINEM Benchmark** | ja, konstruktionsbedingt | **Beurteilung** |
| Korrelation des Assets zu seinem Markt | ja — sagt, wie viel der Gesamtmarkt hier überhaupt bedeutet | Beurteilung |

| Klasse | Benchmark | vorhanden? |
|---|---|---|
| Krypto Spot / Hebel | BTC (Hebel zusätzlich Funding, OI) | ja |
| Aktien | SPY | **ja — `_THEMEN_ETF_BENCHMARK_SPY`, seit 1993** |
| ETF | je nach ETF; SPY als Näherung | teilweise |
| Rohstoffe | die Futures-Reihen selbst | ja, nach Schlüsselkorrektur |

**Der Benchmark-Gedanke ist nicht neu** — SPY liegt bereits unter einem
Benchmark-Namen in der Datenbank, und `btc_relativwert` ist dasselbe Prinzip für
Krypto. Es ist ein Anschluss, keine Neuentwicklung.

**Ehrlich dazu:** Das erzeugt keine Kante. Es entfernt eine falsche Eingabe und
ersetzt sie durch eine unterscheidende. Der Grundbefund aus Abschnitt 6 bleibt.

---

## 7.16 Abdeckung geprüft: 17 von 57 Assets sind für die Kette unsichtbar (11.08. spät)

**Neues Werkzeug:** `pruefe_abdeckung.py` — Vorflugkontrolle, kein Modellaufruf.
Prüft je Assetklasse, welche Watchlist-Assets die Rollen-Ebene beschreiben kann,
und **benennt den Grund**, wo sie es nicht kann.

```
aktien         2 von  2   (100 %)
etf            4 von  7   ( 57 %)
krypto        34 von 44   ( 77 %)
rohstoffe      0 von  4   (  0 %)   ← die Kette läuft für diese Klasse nicht an
--------------------------------
beschreibbar  40 · nicht beschreibbar 17  (30 % der Watchlist)
```

**Es sind 17, nicht die zuerst gezählten 16:** HYPE hat 167 Kerzen und fällt
unter die 220er-Schranke der Ankerprüfung. Eine Prüfung auf `symbol in reihen`
hätte es übersehen — die Schranke gehört in die Prüfung, sonst misst sie etwas
anderes als die Kette später liest.

### Vier verschiedene Ursachen, nur eine davon ein Defekt

| Gruppe | Zahl | Ursache | Handlung |
|---|---|---|---|
| **Rohstoffe** | 4 | ETC-Reihe wird von `agent/rohstoff/pipeline.py` aus der Futures-Referenz **rekonstruiert**; die Produktion steht seit 10.08. OD7L hat zusätzlich keine Futures-Referenz | Pipeline einmal laufen lassen — **Produktionsentscheidung des Nutzers** |
| **Krypto** | 9 | nicht in `KRAKEN_PAIR_MAP` (35 Einträge). Kraken ist die OHLC-Quelle; Bitpanda listet sie, Kraken nicht. Die 9 stimmen **exakt** überein | zweite Quelle, oder bewusst ohne technische Analyse führen |
| **ETF** | 3 | 3QSS, DBPK, X136 ohne OHLC-Historie | Quelle klären |
| **HYPE** | 1 | erst 167 Kerzen — zu jung | löst sich von selbst |

`KAITO` und `XNO` haben nicht einmal einen Preis im Cache — dort ist zu prüfen,
ob sie noch in die Watchlist gehören.

### Was ausdrücklich NICHT gemacht wurde

Die Rohstoff-Lücke wurde **nicht** durch die Futures-Reihe gefüllt, obwohl sie
mit 6.498 Kerzen direkt danebenliegt. Das wäre der Fehler vom 06.08. zurück:
bis dahin lag die Futures-Historie unter dem ETC-Symbol, alles Nachgelagerte
hielt sie für den ETC, und ein OD7C-Signal trug Kurse, die es an der Börse nie
gab. `database/db.py` hält den richtigen Zustand fest: *„gilt als ohne Kurs —
sichtbar statt falsch."*

**Der eigentliche Defekt war nie die Lücke, sondern die Stille.** Die Kette
übersprang diese Assets ohne Eintrag; in jeder Auswertung sieht ein stumm
übersprungenes Asset aus wie „kein Signal", nicht wie „nicht geprüft". Genau die
U-Boot-Wirkung, die der Nutzer benannt hat. Das Werkzeug macht sie sichtbar.

### Regeln, die beim Bau galten

- Ein Ersatzwert, der wie ein Kurs aussieht, ist schlimmer als eine Lücke — er
  ist nicht als falsch erkennbar.
- Der Hinweis „keine Historie" **unterscheidet zwischen Assets** und ist damit
  kein konstantes Feld im Sinne von `finde_konstanten()`. Wäre er für alle
  gleich, gehörte er nicht in den Faktensatz.
- Für die Übergabe an ein Modell gilt die bestehende Konvention
  `nicht_verfuegbar` — kein neues Vokabular.


### KORREKTUR zu 7.16 (11.08., wenige Minuten später) — die Zahlen gelten für eine VERALTETE DB

**Die Abdeckungszahlen oben sind auf dem Desktop erhoben, und dessen Daten enden
am 19.07.2026.** Das steht so in der Übergabe und wurde beim Messen übersehen.

```
price_history_ohlc   jüngster Eintrag  2026-07-19
price_cache          jüngster Eintrag  2026-07-19
holdings             jüngster Eintrag  2026-07-19
```

**Was danach gebaut wurde und hier deshalb nie lief:**

| Datum | Baustein | deckt ab |
|---|---|---|
| 03.08. | `api/coingecko_ohlc_fallback.py` | genau die 9 Krypto ohne Kraken-Listing — KAIA, KAITO, CANTON, SUPRA, IO, XNO, BRETT werden dort **namentlich** genannt |
| — | `api/yfinance_history.py` | die Wertpapiere (3QSS, DBPK, VSN) |
| 06.08. | Rohstoff-Migration + `_rekonstruiere_etc_reihe()` | die ETC-Reihen |

Der Fallback ist **gebaut und angeschlossen** (`scheduler/background.py`, läuft
nach Kraken). Die Lücke ist also mit hoher Wahrscheinlichkeit **kein
Produktionszustand**, sondern der Datenstand vom 19.07.

**Konsequenzen:**

1. **Die 9 Krypto NICHT auf `nicht_verfuegbar` setzen.** Sie sind vermutlich seit
   dem 03.08. gefüllt — nur nicht hier.
2. **Die Rohstoff-Pipeline NICHT auf dem Desktop laufen lassen.** Sie würde ein
   Symptom des veralteten Standes beheben, nicht eine echte Lücke — und sie
   verstieße gegen die stehende Regel (drei dokumentierte Vorfälle).
3. **`pruefe_abdeckung.py` gehört auf das Notebook** oder gegen einen frischen
   Notebook-Export. Dort erst zeigt es die echte Abdeckung.

**Was bestehen bleibt:** das Werkzeug selbst, die Schranke von 220 Kerzen (HYPE
wäre sonst durchgerutscht), und der Grundsatz — eine Kette, die Assets stumm
überspringt, macht „nicht geprüft" ununterscheidbar von „kein Signal". Nur die
konkrete Liste gilt für den 19.07., nicht für heute.

**Vierte Selbstkorrektur des Tages.** Alle vier wurden gefunden, bevor sie
Schaden anrichteten — aber alle vier hatten dieselbe Wurzel: eine Zahl
erhoben, ohne vorher zu prüfen, worauf sie erhoben wird.

---

## 7.17 Abdeckung auf ECHTEN Daten — zwei stille Defekte (11.08. spät)

**Datenquelle:** `DB_Backups/tradinginfotool_2026-08-10_0554.db.gz` aus dem
Austauschordner — der Snapshot vom Tag des Produktionsstopps, 190 MB entpackt,
`integrity_check: ok`. Das Backup entsteht bei **jedem** Notebook-Export
(`_db_backup()`, gebaut 06.08.), es musste also nichts angefordert werden.

```
                    Desktop (19.07.)   Notebook (10.08.)
price_history_ohlc        85.280           110.835
signals                      118             2.957
```

### Zuerst: der Deadloop-Befund hält der 25-fachen Stichprobe stand

```
Desktop     115 / 118  = 97,5 % HALTEN   (2 Wochen)
Notebook   2888 / 2957 = 97,7 % HALTEN   (5 Wochen)

Handlungen gesamt 69:  KAUFEN 24 · TAUSCHEN 22 · NACHKAUFEN 15 · VERKAUFEN 8
```

Die Kennzahl, auf der die ganze Erzählung steht, überlebt fast auf die
Nachkommastelle. **Der Deadloop ist real und jetzt solide belegt.**

### Rohstoffe: in der Produktion längst gelöst

3 von 4 beschreibbar (OD7C/OD7H/OD7N, je 520 Kerzen). Die Pipeline hat die
ETC-Reihen rekonstruiert. Nur OD7L fehlt — dort gibt es keine Futures-Referenz.
**Der Auftrag „Pipeline einmal laufen lassen" war in der Produktion bereits
erfüllt; nur der Desktop-Datenstand war alt.**

### DEFEKT 1: Die gesamte Assetklasse ETF ist wegen eines Währungsfilters unsichtbar

```
3QSS  EUR   522 Kerzen              DBPK  EUR  4160  (ab 2010)
CEBS  EUR   793                     EXH3  EUR  4722  (ab 2008)
ISOC  EUR  3647                     VVMX  EUR  1236
X136  EUR   157
```

**Die Daten sind da, reichlich und tief.** `lade_reihen_aus_db()` filtert
`currency='USD'` — und die ETFs liegen ausschließlich in EUR. Damit sieht die
Rollen-Ebene **keine einzige Zeile** davon. Kein fehlender Datensatz, ein
Filter-Blindfleck.

Das erklärt auch den Unterschied zum Desktop, wo 4 ETFs USD-Zeilen hatten: die
Erfassung hat zwischenzeitlich auf EUR gewechselt.

### DEFEKT 2: Der CoinGecko-Rückfall speichert 4-Tage-Kerzen, als wären es Tageskerzen

```
KAIA  24 Kerzen  2026-05-07 .. 2026-08-07  =  92 Tage
Abstände zwischen allen Kerzen:  4 Tage, ausnahmslos (23 von 23)
```

Betroffen: KAIA, KAITO, CANTON, SUPRA, IO, XNO, BRETT. CoinGecko liefert auf dem
freien Zugang für `days=90` **Vier-Tage-Kerzen**; sie landen in derselben
Tabelle wie Krakens Tageskerzen, und `price_history_ohlc` führt **keine
Granularitätsspalte**.

**Folge:** Für diese sieben Symbole rechnet jeder „20-Tage"-Indikator in
Wahrheit über **80 Kalendertage**. ATR, gleitende Durchschnitte, der
Swing-Detektor, die 60-Tage-Bewegung — alles bezieht sich auf eine andere
Zeitskala, ohne dass es irgendwo sichtbar wird. Genau die U-Boot-Wirkung: nichts
stürzt ab, alles ist verschoben.

Die 220-Kerzen-Schranke hat sie hier zufällig aufgefangen (24 < 220). **Ohne die
Schranke wären sie in jede Messung eingegangen.**

### Stand der Abdeckung auf echten Daten

```
aktien      2 von  2   (100 %)
rohstoffe   3 von  4   ( 75 %)   OD7L ohne Futures-Referenz
krypto     34 von 44   ( 77 %)   10 mit 4-Tage-Kerzen bzw. zu kurz
etf         0 von  7   (  0 %)   Waehrungsfilter — Daten vorhanden
------------------------------------------------
beschreibbar 39 · nicht beschreibbar 18 (32 %)
```

**Korrektur an 7.16:** Die dort gemeldeten Ursachen galten für den Desktop-Stand
vom 19.07. Auf echten Daten sind es andere — und zwei davon sind echte Defekte
statt fehlender Backfills.

---

## 7.18 ETF-Filter behoben — und Entscheidungsvorlage zur Granularität (11.08. spät)

### Behoben: der Währungsfilter

`lade_reihen_aus_db()` filterte `currency='USD'`. Neu: **eine Währung je Symbol,
USD bevorzugt, EUR als Rückfall.** Der Filter wird nicht einfach entfernt —
Krypto liegt in **beiden** Währungen (44 USD, 35 EUR), ohne Auswahl käme dort
jeder Tag doppelt heraus.

```
vorher   45 Symbole, ETF-Klasse unsichtbar
nachher  63 Symbole (56 USD, 7 EUR)

EXH3 4722 Kerzen ab 2008 · DBPK 4160 ab 2010 · ISOC 3647 ab 2011
VVMX 1236 · CEBS 793 · 3QSS 522 · X136 157
```

**Zweite Stelle, die mitmusste:** `_kurs_eur()` rechnet Kurse nach EUR um. Bei
einer Reihe, die bereits in EUR liegt, wäre das eine stille Doppelumrechnung —
der Kurs sähe plausibel aus und läge um den Wechselkurs daneben. Die
Vorrangregel steht deshalb an **einer** Stelle: `waehrung_je_symbol()`.

Abdeckung danach: **45 von 57** statt 39. Keine Klasse mehr ohne Abdeckung.

---

### ENTSCHEIDUNGSVORLAGE: 4-Tage-Kerzen im Tageskerzen-Bestand

**Der Befund (7.17).** Der CoinGecko-Rückfall liefert für sieben Symbole
Kerzen im **Vier-Tage-Abstand** — KAIA, KAITO, CANTON, SUPRA, IO, XNO, BRETT.
24 Kerzen über 92 Tage, Abstand ausnahmslos 4 Tage. Sie liegen in derselben
Tabelle wie Krakens Tageskerzen, und `price_history_ohlc` führt **keine
Granularitätsspalte**. Jeder „20-Tage"-Indikator rechnet dort über 80
Kalendertage — ATR, gleitende Durchschnitte, Swing-Erkennung, 60-Tage-Bewegung.

**Warum es heute nicht auffällt:** Die 220-Kerzen-Schranke fängt sie ab (24 <
220). Das ist ein **Zufall**, kein Schutz — die Schranke prüft Länge, nicht
Granularität. Wer sie senkt, holt sie zurück.

| # | Option | dafür | dagegen |
|---|---|---|---|
| **A** | **Granularitätsspalte** in `price_history_ohlc` | ehrlich, dauerhaft, kein Datenverlust; jede Auswertung kann filtern | Schemaänderung; **jeder** Leser muss sie beachten — wer sie vergisst, rechnet weiter falsch. Ein Feld, das man beachten *muss*, ist selbst eine Falle |
| **B** | Rückfall auf **echte Tageskerzen** umstellen | eine Zeitskala für alles | `/ohlc` liefert auf dem freien Zugang bei 90 Tagen 4-Tage-Kerzen; Tageswerte gäbe es nur über `/market_chart` — **ohne High/Low**, und genau die brauchen ATR und Swing-Erkennung |
| **C** | Betroffene Symbole **ausschließen** | sofort, kein Risiko, ehrlich | sieben Assets ohne technische Analyse — darunter KAIA, laut Fallback-Modul **17,2 % aller Screening-Kandidaten** |
| **D** | Status quo (Schranke fängt sie ab) | nichts zu tun | wirkt durch Zufall; kein Vermerk, keine Warnung. Genau der stille Zustand, den wir gerade abschaffen |

**Empfehlung: eine Variante von A, aber ohne Schemaänderung.**

Die Granularität steht **in den Daten selbst** — der Median-Abstand zwischen
zwei Kerzen. Der Lader kann sie messen und eine Reihe, die nicht täglich ist,
zurückweisen oder kennzeichnen. Vorteile gegenüber einer Spalte:

- **keine Migration**, kein Feld, das jemand vergessen kann
- **selbstprüfend** — die Regel gilt für jede Reihe, auch für künftige Quellen
- die Erkennung ist eindeutig: Tageskerzen haben Median-Abstand 1 (auch bei
  Aktien, wo das Wochenende einzelne 3-Tage-Lücken erzeugt), die
  CoinGecko-Reihen haben 4

Wirkung wäre dieselbe wie C — die sieben fallen heraus —, aber **begründet und
sichtbar** statt zufällig, und die Regel greift automatisch, wenn eine Quelle
später eine andere Granularität liefert.

**Offen und zu prüfen:** Ob die 8.441-Fälle-Messung vom 10.08. (Abschnitt 6)
diese Symbole enthielt. Lief sie über `lade_reihen()` auf der Exportdatei, sind
4-Tage-Kerzen möglicherweise als Tageskerzen eingegangen. Das wäre ein Befund
zu Abschnitt 6, nicht nur zur Rollen-Ebene.

---

## 7.19 Gegenprüfung der Entscheidungsvorlage — zwei eigene Fehler, ein besserer Weg (11.08. spät)

**Nutzervorgabe:** *„mach noch eine Gegenprüfung zu deinen Befunden, vor allem A
— u.U. gibt es eine Möglichkeit ohne mit den Kompromissen zu leben."* Die
Prüfung hat zwei Aussagen von mir widerlegt und einen dritten Weg gefunden.

### Fehler 1: „CoinGecko liefert keine Tageskerzen" — unbelegt behauptet

Ich hatte das aus allgemeinem Wissen gesagt, nicht aus dem Code geprüft. Im
Modul steht:

```
api/coingecko_ohlc_fallback.py:79
  "CoinGecko liefert bei `days` <= 90 Tageskerzen; darueber werden es
   Vier-Tage-Kerzen"
api/coingecko_ohlc_fallback.py:83
  ABRUF_TAGE = 90
```

**Der Code erwartet Tageskerzen und bekommt 4-Tage-Kerzen.** Ob die Grenze bei
CoinGecko anders liegt als angenommen oder sich geändert hat — die Wirkung ist
dieselbe: die Annahme steht als Kommentar da und stimmt nicht. Die
Umwandlungsfunktion heißt `_rohdaten_zu_tageskerzen()` und behauptet es im
Namen.

### Fehler 2: es sind neun Symbole, nicht sieben

Der Granularitätsprüfer über alle 63 Reihen:

```
Median-Abstand 1 Tag   54 Reihen   (inkl. Aktien mit Wochenendlücken, SPY)
Median-Abstand 4 Tage   9 Reihen   BRETT CANTON EURCV IO KAIA KAITO SUPRA VSN XNO
```

**EURCV und VSN kommen dazu — und beide sollten laut dem Modulkopf gar nicht
dort sein:** *„Wertpapiere (3QSS, DBPK, VSN) laufen über yfinance, Stablecoins
(EURCV) brauchen keine Kerzen."* `braucht_fallback()` prüft aber nur
Assetklasse, Kraken-Paar und CoinGecko-ID. VSN ist in der Watchlist als
`krypto` geführt, also greift die Ausnahme nie; eine Stablecoin-Regel gibt es im
Code überhaupt nicht. **Dritter Fall an einem Tag von „dokumentiert, nicht
gebaut"** — nach R-A2 und Methodik-Zusicherung 2.

### Der Weg ohne Kompromiss: yfinance, mit Preis-Gegenprobe

`api/yfinance_history.py::get_full_ohlc_history()` ist laut eigenem Docstring
**assetklassen-neutral**; `ETH-USD` steht als genutzter Ticker im Modulkopf. Nur
der Aufrufer `backfill_all_aktien_ohlc()` filtert auf `assetklasse == "aktien"`.
Dieselbe Lage wie beim CoinGecko-Rückfall: die Fähigkeit ist da, nur nicht
angeschlossen.

**Live geprüft, gegen unseren eigenen Preis aus `price_cache`:**

| Symbol | unser Preis | yfinance | Abw. | Urteil | Tageskerzen |
|---|---|---|---|---|---|
| KAIA | 0,026990 | 0,027390 | 1,5 % | **passt** | 652 ab 2024-10-29 |
| KAITO | 0,677982 | 0,656000 | 3,2 % | **passt** | 498 ab 2025-04-01 |
| SUPRA | 0,000192 | 0,000189 | 1,8 % | **passt** | 612 ab 2024-12-08 |
| XNO | 0,410082 | 0,381893 | 6,9 % | **passt** | 3198 ab 2017-11-09 |
| IO | 0,12866 | — | — | kein aktueller Kurs | „Historie" endet 2022 |
| BRETT | 0,00424 | — | — | kein aktueller Kurs | „Historie" endet 2023 |
| HYPE | 54,21 | — | — | kein aktueller Kurs | „Historie" endet 08/2024 |

**Vier von neun bekämen echte Tageskerzen, alle über der 220er-Schranke** — sie
wären damit vollständig beschreibbar statt ausgeschlossen.

**Und die Gegenprobe ist selbst der Schutz:** IO, BRETT und HYPE liefern bei
Yahoo eine lange, plausibel aussehende Historie, die einem **anderen, toten
Asset** gehört (unser IO ist io.net von 2024, Yahoos IO-USD endet 04/2022;
HYPE ist Hyperliquid ab 11/2024, Yahoos HYPE-USD endet 08/2024). Ohne den
Preisabgleich wäre das die schlimmste Sorte Fehler — eine falsche Kursreihe, die
nicht als falsch erkennbar ist. Dasselbe Problem, das der CoinGecko-Client für
`/search` bereits dokumentiert: *„das könnte still die falsche Coin-Historie
laden."*

### Gebaut: `granularitaet_je_symbol()`

Median-Abstand zwischen zwei Kerzen, aus den Daten selbst — keine Spalte, keine
Migration, nichts zu vergessen, gilt automatisch für jede künftige Quelle. Der
Median statt des Mittelwerts, weil Aktien über das Wochenende 3-Tage-Lücken
haben und trotzdem täglich sind. Verifiziert: 54 Reihen Median 1 (inkl. VST,
PLTR, EXH3, SPY, BTC), 9 Reihen Median 4.

### Die 8.441-Fälle-Messung ist NICHT betroffen

`pruefe_trader_merkmale.py` und `pruefe_analogie.py` haben beide dieselbe
Schranke:

```
if len(c) < 250: return []
```

Bei 24 Kerzen tragen die betroffenen Symbole **null Zeilen** bei. Der
Grundbefund aus Abschnitt 6 steht unverändert.

> **Aber aus demselben Zufall wie überall sonst:** Es schützt eine **Längen**-
> schranke, keine Granularitätsprüfung. Lieferte eine Quelle je 300
> Vier-Tage-Kerzen, gingen sie ungehindert ein. Deshalb gehört
> `granularitaet_je_symbol()` in beide Messskripte, nicht nur in den Lader.

### Korrigierte Empfehlung

1. **yfinance für die vier bestätigten Symbole anschließen** — echte
   Tageskerzen, lange Historie, kein Kompromiss. Mit **verpflichtender**
   Preis-Gegenprobe, die falsche Ticker aussortiert.
2. **Granularitätsprüfung als Wächter** — greift für den Rest und für alles
   Künftige.
3. Für CANTON, IO, BRETT, EURCV, VSN bleibt der ehrliche Zustand: keine
   verwertbare Tageshistorie. EURCV ist ein Stablecoin und braucht keine.

---

## 7.20 Umgesetzt: yfinance-Rückfall mit Pflicht-Gegenprobe, Granularitätswächter in beiden Ladepfaden (11.08. spät)

### Neu: `api/yfinance_krypto_fallback.py`

Dritte OHLC-Quelle für Krypto ohne Kraken-Listing, mit fester Rangfolge:

```
1. Kraken      Boersenkurs, taeglich          KRAKEN_PAIR_MAP
2. yfinance    taeglich, Ticker VERIFIZIERT   dieses Modul
3. CoinGecko   Vier-Tage-Kerzen               nur wo 1 und 2 nichts liefern
```

**Die Tickerprüfung ist Pflicht, nicht Kür.** Zwei Prüfungen, beide müssen
bestehen — und „keine Gegenprobe möglich" zählt als **nicht** bestanden:

| Prüfung | wogegen |
|---|---|
| **Preis** — letzter yfinance-Schluss gegen unseren aus `price_cache`, Toleranz 15 % | ein anderes Asset fällt nicht knapp durch, sondern deutlich |
| **Aktualität** — Reihe muss bis in die letzten 7 Tage reichen | ein totes Asset hat einen plausiblen Preis, nur eben von damals |

**Trockenlauf gegen den Notebook-Snapshot:**

```
KAIA    0,026990 vs 0,027598   2,3 %    652 Kerzen   UEBERNEHMEN
KAITO   0,677982 vs 0,657600   3,0 %    498          UEBERNEHMEN
SUPRA   0,000192 vs 0,000189   2,0 %    612          UEBERNEHMEN
XNO     0,410082 vs 0,382708   6,7 %   3198          UEBERNEHMEN

BRETT   Reihe endet 2023-06-08 (1160 Tage alt)       abgelehnt
CANTON  keine Daten bei Yahoo                        abgelehnt
IO      268,9 % Abweichung, endet 2022-04-11         abgelehnt
VSN      99,0 % Abweichung, endet 2023-03-29         abgelehnt
```

**VSN ist der Beleg dafür, dass die Prüfung Pflicht sein muss: 972 Kerzen — es
hätte jede reine Längenprüfung bestanden.** Nur der Preisabgleich zeigt, dass es
ein vollständig anderes Asset ist. Eine falsche Kursreihe ist die schlimmste
Fehlerklasse dieses Projekts, weil sie nicht als falsch erkennbar ist.

**EURCV** steht in `OHNE_KERZEN` — ein Stablecoin hat eine per Konstruktion
flache Reihe, und die ist für jeden Indikator ein konstantes Feld (B10). Das
stand als Absicht schon im CoinGecko-Modul und war dort nie implementiert.

**Vorgabe ist `--trocken`.** Ein Schreibzugriff auf die Kursdaten ist eine
Produktionshandlung und muss mit `--schreiben` ausdrücklich verlangt werden.
Der Backfill selbst gehört auf das Notebook, nicht auf den Desktop.

### Wächter in BEIDEN Ladepfaden

`nur_tageskerzen()` — verwirft Reihen mit Median-Abstand > 1 und **nennt jede
einzelne**:

```
DB: 9 Reihe(n) sind KEINE Tageskerzen und werden nicht geladen:
    BRETT (4d), CANTON (4d), EURCV (4d), IO (4d), KAIA (4d), KAITO (4d),
    SUPRA (4d), VSN (4d), XNO (4d)
```

Verifiziert: 63 → 54 Reihen, alle verbleibenden mit Median 1. Angeschlossen an
`lade_reihen_aus_db()` **und** `lade_reihen()` — die Messskripte lesen über den
zweiten, und dort schützte bisher nur die Längenschranke, und die nur zufällig.

**Still verwerfen wäre derselbe Fehler wie das stumme Überspringen fehlender
Assets** — deshalb die Warnung mit Namen und Granularität.

### Was bewusst NICHT geändert wurde

Der Währungsfilter in `lade_reihen()` (Exportpfad) bleibt auf USD. In der
Datenbank war er ein Defekt — er machte die ETF-Klasse unsichtbar. Im Exportpfad
wäre seine Änderung etwas anderes: sie veränderte die **Grundgesamtheit** der
8.441-Fälle-Messung und machte deren Ergebnis unvergleichbar. Der Grund steht im
Docstring, damit die nächste Person nicht „aufräumt".

### Offen für den Betrieb

Der yfinance-Rückfall ist gebaut und geprüft, aber **nicht in
`scheduler/background.py` verdrahtet** — dort läuft heute nur der
CoinGecko-Rückfall nach Kraken. Das Einhängen ist eine Produktionsänderung und
gehört auf das Notebook, zusammen mit einem `--schreiben`-Lauf für die vier
bestätigten Symbole.

---

## 7.21 Die geschichtete Ankerpopulation — Grundlage aller offenen Messungen (11.08. spät)

**Werkzeug:** `baue_ankerpopulation.py`, ohne Modellaufruf, reproduzierbar
(fester Seed). Ausgabe: `ankerpopulation.json`.

**Wozu.** Jede bisherige Messung lief auf Ankern, die **nach ihrem Ausgang**
ausgewählt waren — die acht aus 7.8, weil sie zweistellige Gewinne brachten.
Damit lässt sich zeigen, dass ein Fix etwas verbessert, aber **nie**, dass er
nichts kaputt macht. Die vier Zellen aus 7.11 werden hier ausschließlich nach
**Eingangsmerkmalen** geschichtet; der Ausgang wird erst **nach** der Auswahl
gerechnet und mitgeschrieben.

### Vier Schranken, jede aus einem bezahlten Fehler

| Schranke | Wert | Herkunft |
|---|---|---|
| Vorlauf | 220 Kerzen | dieselbe wie in der Kette — sonst misst die Auswahl etwas anderes als der Betrieb liest |
| Zukunft | 40 Handelstage | Methodik 2.18 Zusicherung 3 — sonst fällt ein Anker still heraus statt aufzufallen |
| **Abstand** | 40 Tage zwischen Ankern **desselben** Symbols | Methodik 2.19.1: überlappende Auswertungsfenster verletzen die Unabhängigkeit. Ohne sie sind 32 Anker keine 32 Beobachtungen |
| Symboldeckel | 2 je Zelle | fünf Symbole stellten einmal 102 % des Minus — eine Stichprobe, die an wenigen Symbolen hängt, misst diese Symbole |

### Korrektur beim ersten Lauf: Referenzreihen waren drin

Der erste Durchlauf zog `_ROHSTOFF_FUTURES_OD7C/H/L/N`,
`_THEMEN_ETF_BENCHMARK_SPY` und `_HEDGE_INDEX_3QSS` — in Zelle A **vier von
sechs Symbolen**. Das sind **Referenzreihen, keine handelbaren Assets**: wir
handeln den ETC, nicht den Future, und SPY ist ein Maßstab. Sie sind zudem die
längsten Reihen (bis 1993) und wären deshalb überproportional vertreten gewesen.

Die Population ist jetzt auf **Watchlist-Symbole** beschränkt: 48 handelbare
Reihen, 6 Referenzreihen ausgeschlossen.

### Ergebnis

```
Kandidaten vor der Ziehung:  A 1447 · B 4585 · C 2020 · D 2674   (40-42 Symbole je Zelle)

Gezogen, je 8:
  A  Etikett abwaerts, 60T >= +10 %    ZIEL 1  STOP 7
  B  Etikett abwaerts, 60T <= -10 %    ZIEL 1  STOP 5  offen 2
  C  Etikett aufwaerts, 60T <= -10 %   ZIEL 0  STOP 7  offen 1
  D  Etikett aufwaerts, 60T >= +10 %   ZIEL 1  STOP 7
```

**Die vier Zellen unterscheiden sich im Ausgang praktisch nicht.** Das
Struktur-Etikett trägt in keiner Richtung Information über den weiteren Verlauf.

> **n = 8 je Zelle — das ist kein Beleg.** Es zeigt in dieselbe Richtung wie
> Abschnitt 6 (kein Verfahren schlägt die Basisrate) und wie 7.11, aber die
> Stichprobe trägt keine eigene Aussage. Für einen Befund über die Zellen
> müsste man alle 10.726 Kandidaten auswerten — was ohne Modellaufruf möglich
> und der nächste billige Schritt wäre.

**Die Gesamt-Zielquote von 3 von 32 (9,4 %)** liegt unter der Basisrate von
22,5 % aus Abschnitt 6. Bei n = 32 ist das rund 1,8 Standardabweichungen —
auffällig, aber nicht auszuschließen. Möglicher Grund: die Zellen verlangen
|60-Tage| ≥ 10 %, wählen also **trendende** Lagen, und die verhalten sich
anders als alle Tage. Das ist prüfbar, sobald die Vollauswertung läuft.

### Wofür sie da ist

`ankerpopulation.json` ist ab jetzt die Grundgesamtheit für **M1 bis M4**
(Betragsfrage, Breite-Urteil, Bestandsblock, Persona — siehe
`Zwischenstand_Gesamtprojekt_06_08.md` 8c.3). **Die acht Anker aus 7.8 werden
für Wirkungsmessungen nicht mehr verwendet** — sie bleiben als Prüfsteine für
grobe Fehlfunktion, mehr nicht.

---

## 7.22 Vollauswertung der Zellen — und ein Befund zum Horizont in 6.3 (11.08. spät)

**Werkzeug:** `messe_zellen_ausgang.py`, kein Modellaufruf. 19.891 Anker über
44 handelbare Symbole, Cluster-Bootstrap **über Symbole** (nicht über Anker —
benachbarte Anker teilen ihr Auswertungsfenster, zehntausend Anker sind keine
zehntausend Beobachtungen, Methodik 2.19.1).

### Ergebnis 1: Die vier Zellen unterscheiden sich NICHT

| Schwelle | A (Etikett falsch) | B (zu Recht) | C (Etikett falsch) | D (zu Recht) |
|---|---|---|---|---|
| ±5 % | 35,0 [28,5..39,7] | 34,5 [31,3..39,0] | 33,8 [29,5..38,8] | 36,1 [30,9..39,8] |
| ±10 % | 34,0 [26,1..40,6] | 34,5 [31,6..38,4] | 32,4 [28,3..37,0] | 35,0 [29,3..39,2] |
| ±20 % | 34,2 [23,1..44,0] | 33,8 [29,9..37,8] | 30,8 [25,9..35,7] | 31,1 [23,4..36,2] |
| ±30 % | 30,0 [17,5..41,9] | 32,5 [27,8..37,5] | 24,3 [19,0..30,5] | 27,8 [18,7..34,8] |

**Bei jeder Schwelle überlappen alle vier Intervalle deutlich.** Das
Struktur-Etikett trägt in **keiner** Richtung Information über den weiteren
Verlauf. Der Defekt aus 7.9 war echt — eine falsch beschriftete Tatsache —, aber
**ohne Folgen für das Ergebnis**. Damit ist die Frage abgeschlossen; sie braucht
keine weitere Messung.

### Ergebnis 2: Der Erwartungswert hängt am Horizont, und der wurde nie abgeleitet

Dieselbe Geometrie (Ziel 3,0 ATR, Stop 1,5 ATR), nur die Zeitschranke variiert:

```
Horizont   ZIEL %   STOP %   keines %   Ziel/entschieden   EW in R (keines = 0)
      10     18,5     45,0       36,4             29,1 %                -0,080
      20     27,9     57,2       14,8             32,8 %                -0,014   <- 6.3
      30     31,0     60,7        8,3             33,8 %                +0,013
      40     32,2     62,2        5,6             34,1 %                +0,021
      60     33,3     63,4        3,2             34,5 %                +0,033
```

**Der Vorzeichenwechsel liegt zwischen 20 und 30 Tagen.** `HORIZONT_KERZEN = 20`
(`agent/szenario_fakten.py:52`) ist eine Konstante, die **nie aus der
Zieldistanz abgeleitet wurde**. Und 7.12 zeigt: bei 3 ATR lösen sich die Fälle
erst bei **16 bis 19 Tagen** auf — die Schranke schneidet genau am
Auflösungspunkt ab. Bei 10 Tagen bleiben 36 % unentschieden.

### Was daraus NICHT folgt

> **Abschnitt 6.3 ist damit nicht widerlegt.** Bei seinem Horizont von 20 Tagen
> ist auch diese Messung **negativ** (−0,014 R) — die Richtung reproduziert
> sich. Die Höhe nicht (22,5 % gegen 27,9 % Zielquote), und dafür gibt es einen
> Grund, der nichts mit dem Horizont zu tun hat: **die Grundgesamtheit ist eine
> andere.** Hier 48 handelbare Symbole samt Aktien, ETF und Rohstoffen; dort
> 20 überwiegend krypto-lastige aus der Exportdatei.
>
> **Und diese Rechnung ist BRUTTO.** Das Kostenmodell vom 04.08. ergab netto
> **−0,233 R**. Ein Brutto-Erwartungswert von +0,02 R bleibt danach deutlich
> negativ. Die Schlussfolgerung „der Aufbau verliert" überlebt also
> voraussichtlich — **nur nicht aus dem Grund, der in 6.3 steht.**

### Zwei offene Fäden daraus

1. **Die Zeitschranke gehört an die Zieldistanz gekoppelt**, nicht frei gesetzt.
   Ein Ziel von 3 ATR braucht mehr Zeit als eines von 1 ATR. Heute ist beides
   unabhängig konfiguriert.
2. **„keines = 0 R" ist eine Annahme, keine Messung.** Ein Trade, der die
   Zeitschranke erreicht, wird irgendwo geschlossen — nicht bei null. Bei
   Horizont 20 betrifft das 15 bis 21 % aller Fälle und trägt den Unterschied
   zwischen −0,014 und −0,115 R mit. Das gehört ausgerechnet, nicht gesetzt.

---

## 7.23 „keines = 0 R" war eine Setzung — und die Kosten sind der eigentliche Grund (11.08. spät)

**Werkzeug:** `messe_zeitschranke.py`, kein Modellaufruf.

### Befund 1: Offene Fälle sind kein neutraler Rest, sondern Überlebende

Abschnitt 6.3 rechnet `0,225 × 2R + 0,565 × (−1R) = −0,115 R`. Die dritte
Gruppe — weder Ziel noch Stop — taucht darin nicht auf und wird damit implizit
mit **0 R** bewertet. Bei Horizont 20 sind das 15 bis 21 % aller Fälle.

Gemessen, statt gesetzt:

```
Horizont 20: offene Faelle  Mittel +0,281 R · Median +0,146 R · 57,3 % im Plus
   5. Perzentil -0,634    25. -0,158    50. +0,146    75. +0,723    95. +1,432
```

**Und das ist strukturell, nicht zufällig.** Ein Fall, der 20 Tage überlebt hat,
ohne einen Stop bei 1,5 ATR zu berühren, ist ein **ausgewählter Überlebender** —
der Stop liegt viel näher als das Ziel bei 3 ATR. Die Gruppe *muss* positiv
verzerrt sein. Sie mit null zu bewerten unterschätzt den Erwartungswert
systematisch in eine Richtung.

### Befund 2: Damit verschwindet die Horizontabhängigkeit — und 7.22 korrigiert sich

```
Horizont    EW mit "keines = 0"    EW mit tatsaechlichem Kurs
      10               -0,080                        +0,028
      20               -0,014                        +0,028
      30               +0,013                        +0,030
      40               +0,021                        +0,031
      60               +0,033                        +0,038
```

**Richtig bewertet ist der Erwartungswert über alle Horizonte flach bei rund
+0,03 R.** Der Vorzeichenwechsel zwischen 20 und 30 Tagen, den 7.22 als Befund
meldete, war **ein Artefakt der Null-Annahme**, keine Eigenschaft des Marktes.
Die Zeitschranke ist damit weit weniger kritisch als dort behauptet.

### Befund 3: Die Kosten sind der Grund — und zwar um ein Vielfaches

Die bisher zitierten **−0,233 R sind eine HEBEL-Zahl**: sie enthalten eine
Tagesgebühr (Funding) und hängen an 2,6 Tagen Haltedauer. Bei Spot gibt es kein
Funding. Die Sätze je Klasse stehen seit 07.08. in
`agent/krypto/backward_tracking.py`.

**Kosten in R = Roundtrip in % / Stopabstand in %** — der Stopabstand ist
1,5 ATR und damit je Asset verschieden, deshalb je Anker gerechnet:

| Klasse | Anker | Stop, Median | Kosten in R | Brutto-EW | **Netto-EW** |
|---|---|---|---|---|---|
| krypto | 12.795 | 11,7 % | 0,257 | +0,028 | **−0,230** |
| aktien | 3.383 | 5,9 % | 0,170 | +0,028 | **−0,143** |
| etf | 13.400 | 1,9 % | 0,521 | +0,028 | **−0,493** |
| rohstoffe | 720 | 3,0 % | 0,335 | +0,028 | **−0,307** |

**Die Kosten sind das Sechs- bis Achtzehnfache des Brutto-Erwartungswerts.**

**ETF ist am schlechtesten, und der Grund ist lehrreich:** der Stopabstand
beträgt dort nur 1,9 % des Kurses. Geringe Schwankung heißt enger ATR-Stop, und
ein enger Stop heißt, dass jede Gebühr einen großen Teil des Risikobudgets
frisst. Nicht die Kosten sind hoch, der Stop ist eng.

### Was daraus folgt — und was nicht

**Der Aufbau trägt sich nicht.** Das bestätigt die Schlussfolgerung aus
Abschnitt 6 — **aber die Begründung dort ist die falsche.** Die Geometrie
verliert brutto nicht (+0,03 R); es sind die Kosten.

**Und die Geometrie lässt sich nicht daraus herausdrehen.** Damit die Kosten
unter den Bruttovorteil fallen, müsste gelten
`Stop % > Roundtrip % / 0,03` — bei Krypto also ein Stop von **100 % des
Kurses**. Ein weiterer Stop senkt die Kosten in R, verschiebt aber die
Trefferquote mit. **Es gibt keine Stop-Einstellung, die diesen Aufbau bei diesen
Gebühren tragfähig macht.**

Damit ist der Hebel **nicht** „bessere Einstiege wählen" — brutto ist der Aufbau
ohnehin nahe null, und Abschnitt 6 hat gemessen, dass kein Verfahren die
Basisrate schlägt. Der Hebel liegt bei **Kosten je R**: weniger und größere
Bewegungen, längere Haltedauern, oder eine andere Gebührenstruktur.

### Grenzen dieser Messung

- Der **Brutto-EW ist der Gesamtwert**, für alle Klassen derselbe. Ein
  klassenweiser Bruttowert wäre genauer und würde die Tabelle verschieben.
- **400 EUR Referenzposition.** Bei Börsenwerten sinkt der Fixanteil mit der
  Größe: bei 1.000 EUR fielen die ETF-Kosten von 0,52 auf rund 0,37 R — besser,
  aber weiterhin ein Vielfaches von 0,03.
- Steuern und Slippage sind nicht enthalten.

---

## 7.24 Der Kostenhebel — für Krypto und ETF beantwortet, für den Rest nicht messbar (11.08. spät)

**Werkzeug:** `messe_kostenhebel.py`, kein Modellaufruf. Frage: Gibt es diesen
Aufbau in einer tragfähigen Variante? Kosten in R = Roundtrip % / Stopabstand %,
also senkt **ausschließlich** ein größeres Stopvielfaches die Quote — bei Spot
fällt keine Tagesgebühr an, die Haltedauer wirkt dort nicht.

### Die Grundgesamtheit, die ich VOR dem Lauf hätte prüfen müssen

```
krypto     29 Symbole,  6.805 Anker      belastbar
etf         6 Symbole, 12.260 Anker      belastbar
aktien      2 Symbole,  3.003 Anker      UNBRAUCHBAR
rohstoffe   3 Symbole,    150 Anker      UNBRAUCHBAR
```

**Aktien sind PLTR (+1.711 % über die Reihe) und VST (+1.140 %).** Eine
Long-only-Barrierenstrategie auf zwei der besten Aktien des Jahrzehnts — sie
stehen in der Watchlist, *weil* sie gelaufen sind. Der gemessene Wert von
+0,86 R ist reine Survivorship und wird hier **nicht** berichtet.

**Rohstoffe** sind 150 stark überlappende Anker aus drei **rekonstruierten**
ETC-Reihen à 520 Kerzen — bei 220 Vorlauf und 250 Horizont bleiben je Symbol
rund 50 Anker, effektiv wenige unabhängige Beobachtungen.

*Zweiter Fall an einem Tag, in dem ich eine Messung gebaut und gefahren habe,
ohne vorher zu prüfen, ob die Grundgesamtheit die Frage trägt.*

### Das Ergebnis, wo es trägt

| Klasse | Stop | Stop % | Treffer | offen | Brutto | Kosten | **Netto** |
|---|---|---|---|---|---|---|---|
| krypto | 1,5 | 12,3 % | 26,3 % | 0,0 % | −0,211 | 0,244 | **−0,455** |
| krypto | 3,0 | 24,5 % | 24,1 % | 0,9 % | −0,273 | 0,122 | **−0,395** |
| krypto | 6,0 | 49,1 % | 11,1 % | 24,4 % | −0,531 | 0,061 | **−0,592** |
| krypto | 15,0 | 122,7 % | 0,2 % | 95,9 % | −0,399 | 0,024 | **−0,424** |
| etf | 1,5 | 1,8 % | 32,3 % | 3,7 % | +0,005 | 0,558 | **−0,553** |
| etf | 6,0 | 7,2 % | 27,5 % | 12,8 % | −0,015 | 0,140 | **−0,155** |
| etf | 15,0 | 17,9 % | 10,9 % | 61,7 % | +0,020 | 0,056 | **−0,036** |

**Die Kosten fallen proportional — um den Faktor zehn von s=1,5 auf s=15. Der
Bruttovorteil fällt schneller.** Bei s=6 bricht die Krypto-Trefferquote auf
11 % ein, bei s=15 auf 0,2 %, und 96 % laufen in die Zeitschranke.

**Es gibt keine Stop-Einstellung, bei der Krypto oder ETF positiv wird.**
Positionsgröße hilft nur den Börsenklassen und nur begrenzt: ETF bei s=1,5 von
−0,553 (400 EUR) auf −0,296 (5.000 EUR) — weiterhin negativ.

### KORREKTUR an 7.23: „flach über alle Horizonte" war zu weit gefasst

7.23 schloss aus den Horizonten 10 bis 60, der Erwartungswert sei flach bei rund
+0,03 R. **Bei 250 Tagen ist er −0,211.**

Der Grund ist einleuchtend: Bei kurzem Horizont stehen die offenen Fälle bei
durchschnittlich +0,28 R — aber das sind **unrealisierte** Buchgewinne. Über 250
Tage lösen sie sich auf, überwiegend als Stop. **Ein kurzer Horizont verbucht
Gewinne, die später ausgestoppt worden wären.**

> **Einschränkung:** Die Grundgesamtheit unterscheidet sich mit — der
> 250-Tage-Lauf verlangt längere Reihen und nutzt damit frühere Anker. Horizont
> und Population wirken zusammen und lassen sich hier nicht trennen. Was
> bleibt: „flach" war eine Verallgemeinerung aus einem schmalen Bereich und ist
> zurückgenommen.

### Was jetzt gilt

**Der Aufbau trägt sich in keiner gemessenen Variante** — nicht bei anderem
Stop, nicht bei anderer Größe, nicht bei anderem Horizont. Für Aktien und
Rohstoffe ist die Frage mit den vorhandenen Daten **nicht beantwortbar**; dafür
bräuchte es mehr Symbole, die nicht nach ihrem Erfolg in der Watchlist stehen.

Das ist eine Entscheidungsgrundlage, keine Niederlage: Die verbleibenden Hebel
liegen außerhalb der Geometrie — eine andere Gebührenstruktur, eine andere
Assetauswahl, oder tatsächliche Vorhersagekraft aus Information, die nicht im
Kurs steht.

---

## 7.25 Gegenprüfung aller Befunde des 11.08. — und was sie zusammen bedeuten

**Nutzervorgabe:** *„mach für alle Prüfungen eine Gegenprüfung und eine
Zusammenfassung, was das im Detail und für die Lösung insgesamt bedeutet."*
Nach fünf Selbstkorrekturen an einem Tag ist das die richtige Reihenfolge.

### Teil 1: Was hält der Gegenprüfung stand

| # | Befund | Was ihn kippen könnte | Ergebnis |
|---|---|---|---|
| 1 | **97,7 % HALTEN** auf 2.957 Signalen | HALTEN könnte Nicht-Entscheidungen enthalten — bei Assets ohne Position ist „halten" kein Urteil | **hält.** Getrennt: im Bestand 51 Handlungen auf 1.736 (2,9 %), ohne Bestand 18 auf 1.221 (1,5 %). Beide Teilmengen zeigen dasselbe. `outcome_status='nicht_anwendbar'` bestätigt, dass HALTEN nie als Trade geführt wird. *Einschränkung: `holdings` ist der heutige Stand, nicht der zum Signalzeitpunkt* |
| 2 | **Struktur-Etikett trägt keine Information** | Cluster-Bootstrap über 44 Symbole; Krypto-Symbole sind untereinander stark korreliert, die Intervalle könnten zu eng sein | **hält, und zwar erst recht.** Breitere Intervalle machen „kein Unterschied" wahrscheinlicher, nicht unwahrscheinlicher. Die schnelle Etikett-Fassung war gegen `_struktur()` geprüft: 291 Stichproben, 0 Abweichungen |
| 3 | **ETF-Klasse war unsichtbar** | — | **hält.** Verifiziert durch Laden: 45 statt 39 beschreibbare Assets |
| 4 | **4-Tage-Kerzen als Tageskerzen** | — | **hält.** 23 von 23 Abständen exakt 4 Tage |
| 5 | **yfinance: 4 von 8 bestehen** | 15 % Toleranz ist gesetzt; ein richtiger Ticker mit 20 % Abweichung fiele durch | **hält.** Die Ablehnungen waren nicht knapp (99 %, 269 %, oder Reihe seit Jahren tot). Konservativ in die sichere Richtung |
| 6 | **Kosten dominieren** | In 7.23 wurde EIN Brutto-Wert (+0,028) auf ALLE Klassen angewandt | **teilweise überholt.** 7.24 liefert die klassenweisen Bruttowerte; die Tabelle in 7.23 ist dadurch ersetzt. Die Richtung ändert sich nicht, die Höhe schon |
| 7 | **Keine Stop-Einstellung hilft** | Nur das Verhältnis 2:1 getestet — ein anderes Verhältnis könnte helfen | **hält, siehe Teil 2 — es kann kein Verhältnis helfen** |
| 8 | **„keines = 0 R" war gesetzt** | — | **hält** als Rechnung; die Größe der Korrektur hängt am Horizont (7.24) |

### Teil 2: Die Erklärung, die alles zusammenbindet

Für einen **driftfreien** Pfad mit Zielbarriere `+a` und Stopbarriere `−b` gilt:

```
P(Ziel zuerst) = b / (a + b)

EW = a · b/(a+b)  −  b · a/(a+b)  =  0      EXAKT null, fuer JEDE Geometrie

   Ziel 3 / Stop 1,5  →  33,3 %      Ziel 1 / Stop 1  →  50,0 %
   Ziel 6 / Stop 3    →  33,3 %      Ziel 1 / Stop 2  →  66,7 %
   ... alle mit Erwartungswert exakt 0
```

**Und gemessen, über 19.891 Anker, entschiedene Fälle: 34,0 % gegen theoretisch
33,3 %.** Der Markt verhält sich auf dieser Granularität wie ein Martingal, auf
0,7 Prozentpunkte genau.

**Damit ist jeder Einzelbefund dieses Projekts ein Spezialfall derselben
Tatsache:**

| Befund | folgt daraus |
|---|---|
| Kein Verfahren schlägt die Basisrate (6.1/6.2) | die Basisrate **ist** der Martingalwert — es gibt nichts zu schlagen |
| Die vier Zellen unterscheiden sich nicht (7.22) | kein Merkmal trägt Information, also auch nicht das Etikett |
| Keine Stop-Einstellung hilft (7.24) | der Erwartungswert ist für **jede** Geometrie null |
| Die Konfidenz ordnet nicht, die Kalibrierung bringt die halbe Strecke | es gibt keine Ordnung, die man treffen könnte |
| Die Kosten entscheiden (7.23) | null minus Kosten ist negativ, zwangsläufig |

**Das ist keine Messung mehr, das ist Arithmetik.** Ein Barrierensystem auf einem
näherungsweise driftfreien Pfad hat brutto den Erwartungswert null — unabhängig
von Zieldistanz, Stopweite, Verhältnis und Horizont. Nach Kosten ist es strikt
negativ. Kein Prompt, kein Modell und keine Parametrierung ändert das.

### Teil 3: Was das im Detail bedeutet

1. **Die Geometriefrage ist geschlossen** — nicht durch Messrauschen, sondern
   durch Mathematik. Weitere Stop-, Ziel- oder Horizontvarianten sind
   verschwendete Zeit.
2. **Die LLM-Ebene kann diese Lücke nicht schließen.** Sie müsste Information
   liefern, die den Pfad *nicht driftfrei* macht. Genau das hat Abschnitt 6 für
   alle kursbasierten Merkmale ausgeschlossen.
3. **Die heute behobenen Defekte bleiben richtig** — falsche Beschriftungen,
   unsichtbare Assets, falsche Kerzen und ein nie gebautes R-A2 gehören
   beseitigt, unabhängig von der Ökonomie. Aber **keiner von ihnen war je der
   Grund**, und das ist jetzt belegt statt vermutet.
4. **Die Kostenquote ist der einzige Parameter mit Wirkung** — und sie ist bei
   1,5 % je Seite (Bitpanda Krypto) so hoch, dass sie den Bruttovorteil um das
   Sechs- bis Achtzehnfache übersteigt.

### Teil 4: Was das für die Lösung insgesamt bedeutet

**Es bleiben genau drei Wege, und nur drei:**

| Weg | Was er verlangt | Stand |
|---|---|---|
| **A — Drift statt Timing** | Keine Vorhersage. Wer den Aufwärtsdrift eines Marktes einsammelt, braucht keine Barriere zu treffen. Akkumulation, DCA, Halten | **steht seit dem 07.08. als Punkt S2 auf der eigenen Liste** („Akkumulations-Messung für Spot, AZ-4 gegen DCA") und ist dort als *günstigster Punkt der ganzen Liste* markiert |
| **B — Echte neue Information** | Etwas, das nicht im Kurs steht: Nachrichten, Meldungen, Positionierung. Nur so wird der Pfad nicht driftfrei | ungeprüft. Die einzige unerprobte Kategorie |
| **C — Kosten senken** | Andere Gebührenstruktur oder andere Assets. Wirkt, reicht aber allein nicht: 0 minus weniger Kosten ist immer noch nicht positiv | begrenzt, nicht hinreichend |

**Weg A ist der einzige, der ohne Vorhersagekraft auskommt** — und genau deshalb
der einzige, der nach allem heute Gemessenen tragen kann. Er steht seit vier
Tagen auf der eigenen Liste und wurde nie gemessen.

**Weg B ist die einzige Chance, das Timing doch noch zu retten** — und die
Rollen-Ebene, die heute gebaut und repariert wurde, ist genau die Stelle, an der
Nachrichten hineinkämen. Die Arbeit war also nicht umsonst; sie war nur nie das
Ergebnis, sondern die Vorbereitung.

**Was ausdrücklich NICHT folgt:** dass das Projekt gescheitert ist. Es hat in
sechs Wochen eine belastbare Antwort auf die Frage „funktioniert Timing mit
Kursdaten" erarbeitet — die Antwort ist nein, und sie ist jetzt begründet statt
vermutet. Das ist ein Ergebnis.

---

## 7.26 Der kausale Test zum dritten Faktor — NEGATIV, und er widerlegt meine eigene Konstruktion (11.08. spät)

**Werkzeug:** `messe_dritter_faktor.py`. Gepaart, 20 Krypto-Anker aus der
geschichteten Population, bitgleich bis auf **einen Satz** — die
Finanzierungsrate am Terminmarkt, kausal am Ankertag abgeschnitten. Ein Lagebild
je Anker für beide Arme, damit der Lauf genau **einen** Unterschied misst.

### Das Ergebnis

```
ARM OHNE   Faktoren im Schnitt 2,30   {2: 14, 3: 6}   Handlungen 8/20   Kaeufe 6
ARM MIT    Faktoren im Schnitt 2,45   {2: 11, 3:  9}   Handlungen 7/20   Kaeufe 6

Aktion geaendert: 1 von 20   —   SEI 2025-03-16  REDUZIEREN -> NICHTS_TUN
```

**Die Faktorzahl stieg, die Handlungsquote nicht.** Drei Anker gingen von zwei
auf drei Faktoren; bei keinem wurde daraus ein Kauf. Die einzige Änderung ging
in Richtung *weniger* Handlung.

### Der naheliegende Einwand, geprüft und ebenfalls negativ

Vielleicht war der neue Fakt zu **neutral** — ein Perzentil von 39 argumentiert
für nichts. Also nachgesehen, wo er stark in eine Richtung zeigt:

```
9 von 20 Ankern mit extremer Finanzierung (Perzentil <= 15 oder >= 85)
   ALGO 7 % · GRIFFAIN 99 % · APT 2 % · SEI 10 % · APT 14 % · KAS 15 %
   SEI 14 % · W 5 % · NEAR 6 %
Auch dort: genau eine Aenderung, und die in die Gegenrichtung.
```

**Auch ein Fakt, der klar in eine Richtung zeigt, ändert die Entscheidung nicht.**

### Was damit widerlegt ist — meine eigene Konstruktion von heute Nachmittag

Faktenmappe 12.3 schloss aus der Korrelation (bei drei Faktoren 78 %
Handlungsquote, bei zwei 18 %, p = 0,0035): *„Der Deadloop ist keine
Fehlfunktion, sondern das System, das den Fachstandard korrekt auf eine
unzureichende Eingabe anwendet."*

**Diese Erklärung ist widerlegt.** Wird ein echter dritter unabhängiger Faktor
hinzugefügt, steigt die Handlungsquote **nicht**. Die Korrelation war das
Modell, das in sich stimmig antwortet: Es entscheidet auf dem Kursbild und
berichtet eine Faktorzahl, die dazu passt. **Die Zahl beschreibt die
Entscheidung, sie treibt sie nicht.**

Ich hatte das als Einschränkung notiert („Faktorzahl und Aktion stammen aus
demselben Aufruf") und trotzdem eine Erklärung darauf gebaut. Der Test war
richtig angesetzt — die Schlussfolgerung davor war zu früh.

### Was daraus folgt

Damit ist **jede** geprüfte Einzelerklärung für den Deadloop gefallen:

| Erklärung | Prüfung | Ergebnis |
|---|---|---|
| Struktur-Etikett | 19.891 Anker, Zellenvergleich | 2,71 % der Tage, Zellen unterscheiden sich nicht |
| Degradierung durch ungültigen Stop | 8 Anker, roh gegen final | 0 von 8 |
| Betragsfrage | noch offen | — |
| Zu wenige unabhängige Faktoren | **gepaart, 20 Anker** | **kein Effekt** |

**Was bleibt, ist die Erklärung aus 7.25:** Im Kursverlauf ist auf dieser
Granularität nichts zu finden — 34,0 % gemessen gegen 33,3 % theoretisch bei
einem reinen Zufallspfad. Ein Modell, das darin selten einen Handlungsgrund
findet, verhält sich **richtig**. Die niedrige Handlungsquote ist kein Defekt
und auch nicht die Folge eines fehlenden Faktors, sondern die zutreffende
Antwort auf eine Eingabe ohne verwertbaren Inhalt.

### Was der neue Baustein trotzdem wert ist

Die Finanzierungsrate bleibt im Code. Sie ist der **erste Fakt in dieser Kette,
der nicht aus unserer Kursreihe stammt**, sie ist korrekt nach R-T1/T2/T3/T5
formuliert, kausal abgeschnitten und deckt 89 % der Krypto-Symbole ab. Sie
rettet den Timing-Ansatz nicht — aber sie ist der erste Schritt auf dem einzigen
Weg, der nach 7.25 noch offen ist: **Information, die nicht im Kurs steht.**

Ein einzelner solcher Fakt reicht dafür nicht. Das war die Lehre dieses Laufs.
