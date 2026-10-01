# Voranalyse L — Liquidität zum Zeitpunkt (ENTWURF 01.10.2026, zur Abstimmung)

**Auftrag:** Nutzer 01.10. (E-39): *„Ja, Voranalyse L."* Nach dem Gespräch: *„Ja, finde den Ansatz gut. Setze die Messungen so auf,
dass wir daraus Erkenntnisse und ggf. Lösungsansätze für unsere Probleme erhalten."*
⚠️ **Das ist nur ein Entwurf.** Es wird nichts gemessen, bevor du Ja sagst.

> **Urteil in einer Zeile:** Wir messen, ob die **absolute Liquidität zum Einstieg** (USD-Volumen der letzten 24 h) die drei Probleme aus
> Teil 0 (2.703) trifft: zu wenig Vorteil je Handel für die Kosten, schwache Assets und die negative Stufe 2x. Gemessen wird erst auf 2024,
> mit **einer** Regel als Ergebnis, und erst nach deinem Ja einmal auf 2025–26.

---

## 0. Ziel, Stand, Test oder Betrieb

| | |
|---|---|
| **Ziel** | Mehr Vorteil je Handel durch **bessere Auswahl zum Zeitpunkt**, ohne Liste von Hand und ohne Asset-Vorurteil |
| **Stand** | 2.703 Teil 0: Ohne Kosten ist die REGEL0 in 4/4 Mengen positiv. Auf der breiten Menge liegt der Vorteil je Handel aber bei +0,33..+0,35 %, unter den Kosten. Auf deiner Liste liegt er bei +0,82 %. Später eingestellte Paare bringen weniger, die seltene Stufe 2x ist roh negativ. ➤ Die **Auswahl** entscheidet |
| **Test oder Betrieb** | Test. L1 liegt auf Ebene A (Bewertung 1, ob ein Einstieg zählt), L2 auf Ebene C (Bewertung 2, Hebelstufe), nur Auskunft. Die Bewertung bleibt **neutral**: Gewählt wird nach **Chance**, nicht nach Kosten (Regel 2). Das Konto ist nur Auskunft |

**Abgestimmte Grundsätze (Gespräch 01.10.):**
1. **Liquidität** = USD-Handelsvolumen der **letzten 24 Stunden bis zur Einstiegsstunde** (Volumen × Kurs aus den Stundenkursen). Das ist vorab bekannt, je Asset und Stunde verschieden, also ein echter Beitrag (Prüffrage erfüllt)
2. Die Wirkung wird **getrennt** gemessen: L1 *ob* (Bewertung 1) und L2 *wie viel Hebel* (Bewertung 2)
3. **Absolute Grenze in USD, kein Rang** (Regel 3: beim Hebel kein Asset-Rang). Sie funktioniert auch bei einem einzelnen Asset
4. **O9 (Größenklassen):** bleibt ein eigener Punkt. L zeigt als Auskunft, wie eng Liquidität und Marktkapitalisierung zusammenhängen (Abschnitt 4). Danach entscheiden wir, ob O9 in L aufgeht
5. Kein Spread, keine Orderbuchtiefe: Das wäre eine neue Datenquelle (D), derzeit ausgeschlossen

---

## 1. L0 — AUSKUNFT 2024: Dosis und Wirkung (kein Urteil)

Die REGEL0-Einstiege 2024 (bestand, alle 4 Mengen nur als Auskunft) nach **festen absoluten Stufen** der Liquidität:
**< 0,5 · 0,5–1 · 1–2 · 2–5 · 5–10 · 10–20 · ≥ 20 Mio USD** in 24 h.

| Je Stufe | wozu |
|---|---|
| Einstiege, Chance (Dq wie 2.688) | trägt die Liquidität etwas zur **Richtung** bei? |
| **Spiegel** (+5 % zuerst minus −5 % zuerst, binnen 24 h) | Pflicht nach E-29: Eine bessere Chance darf nicht nur aus **größerer Bewegung** kommen |
| Rohvorteil je Handel (Spot, ohne Kosten) | Wo liegt er **über** den Kosten von 0,48 %? |
| Liquidationen, Anteil Stufe 2x | Problem 3 |
| **ATR-frei?** (G-ATR wie 2.691): dieselbe Tabelle innerhalb der ATR-Drittel | Dünne Werte haben oft eine hohe ATR. Trägt die Liquidität **eigen** oder ist sie nur die ATR? |
| Anteil später eingestellter Paare (nur unverzerrt) | Ist die Liquidität zum Zeitpunkt ein **kausaler Stellvertreter** für *später eingestellt*? |

---

## 2. L1 — die REGEL (Bewertung 1), Wahl 2024, vorab festgelegt

| | |
|---|---|
| Form | Der REGEL0-Einstieg zählt nur, wenn die Liquidität ≥ **X** ist. Sonst bleibt alles wie in der REGEL0 (Schwelle +0,035, Ruhe 48 h, J, BTC) |
| Raster X | **0** (= REGEL0) · 0,5 · 1 · 2 · 5 · 10 · 20 Mio USD |
| Wahl auf 2024, bestand | größter Abstand *echt − P90 Nullwelt* (Maß wie 2.699, die Nullwelt mit **demselben** Filter). Bei Gleichstand (< 0,005) das **kleinere** X. Wird X = 0 gewählt, trägt L1 nicht |
| Spiegel an der gewählten Stufe | muss **besser** sein als bei X = 0. Sonst ist L1 nicht bestanden (die bessere Chance käme nur aus der Bewegung) |
| Bestätigung einmal 2025–26, 4 Mengen | Kern-Kriterien wie 2.688 (B1–B6), dazu in ≥ 3/4 Mengen Rohvorteil je Handel **höher** als die REGEL0 und Hebelkonto **mindestens so gut**. Vermerk *bestätigt, Vorwärtstest ausstehend* (B4) |

---

## 3. L2 — AUSKUNFT 2024: trägt die Liquidität Risiko über die ATR hinaus? (Bewertung 2)

Liquidationsrate je Liquiditätsstufe **innerhalb** jeder Hebelstufe und ATR-Zelle, auf allen Einstiegen 2024. Trägt die Liquidität dort
**eigene** Risikoinformation, wird sie ein **eigener**, vorab festgelegter Schritt für das ATR-Modell. Heute gibt es keine Regel daraus (Stufe 1, Vorprüfung).

---

## 4. Auskunft O9: Liquidität gegen Marktkapitalisierung

Wo eine Marktkapitalisierung zum Zeitpunkt vorliegt (`umlaufmenge_cg.db` × Kurs): Rangkorrelation zur Liquidität und der Anteil der
Einstiege, bei denen beide in verschiedene Klassen fallen. Das zeigt, ob L die Größenklassen (O9) schon abdeckt.

---

## 5. Prüfung und Gegenprüfung

| | |
|---|---|
| R-R11 | X = 0 trifft die REGEL0 zeilengleich (Einstiege, Abstand +0,0882 ohne BTC wie 2.699) |
| Gegenprüfung | Liquidität für 200 zufällige Einstiege **unabhängig** aus der Datenbank nachgerechnet |
| Vorgriff | Das Volumen endet in der Einstiegsstunde, deren Schluss der Einstiegskurs ist |
| Nullwelt | verschobene rsi-Modelle, Filter gleich |
| Zeitstabilität, Weglassprobe | je Jahr, ohne 10./11.10.2025 (in der Bestätigung) |
| je Asset | Anteil der Assets, die durch den Filter ganz herausfallen, und welche |

---

## 6. ⚠️ Was du vorher wissen solltest

| # | |
|---|---|
| **1** | **Weniger Handel.** Ein Filter nimmt Einstiege weg. Schon in der Wahl zeigen wir, **wie viele** und **welche Assets** wegfallen |
| **2** | **Bestätigungsjahre.** Wie bei B gilt: Besteht L1, dann mit dem Vermerk *Vorwärtstest ausstehend* |
| **3** | **Betrieb (E-35).** Das Volumen kommt mit den Stundenkursen mit (B1), es braucht **keine** neue Datenquelle |
| **4** | **Kein Asset-Vorurteil.** Ein Asset fällt nur **zu dem Zeitpunkt** heraus, an dem es dünn gehandelt wird. Wird es liquide, zählt es wieder |

---

## 7. Umfang

L0, L1-Wahl, L2 und O9-Auskunft auf 2024, etwa 1–1,5 h, dann **Stopp und Bericht**. Die Bestätigung nach deinem Ja dauert etwa 2 h.

## 8. Zur Abstimmung

| # | Vorschlag |
|---|---|
| **L-a** | L0 und L2 als Auskunft auf 2024, L1 als Regel mit Wahl 2024 wie oben |
| **L-b** | Raster 0 … 20 Mio USD, absolute Stufen, Gleichstand zum kleineren X |
| **L-c** | Spiegel als Pflicht an der gewählten Stufe |
| **L-d** | Stopp und Bericht nach der Wahl, Bestätigung erst nach deinem Ja |

---

## 9. ✔ ABGESTIMMT (Nutzer 01.10.2026) — mit zwei Ergänzungen; Vorab-Festlegung VOR dem Lauf

**Nutzer:** *„Ok. Anmerkung zum Handel: Zusätzliche Sperren oder Filter sehe ich kritisch, wenn diese nur Einstiege wegnehmen ohne Qualitätsgewinn.
Hier musst du mir die Auswirkungen konkret mitteilen. Aktuell wissen wir nicht, ob überhaupt und wie viele echte Signale je Asset ankommen
werden, z. B. BTC, ETH, LINK. Dies müssen wir ohnehin je Anpassung der REGEL0 durchführen."* — und: *„bitte für alle Assets, welche in der
Watchlist, im Portfolio bzw. Bestand sind."*

**Ergänzung 1, Qualitätsgewinn (Pflicht für L1):** An der gewählten Stufe X müssen die **weggenommenen** Einstiege **schlechter** sein als die
behaltenen, und zwar in der Chance (Dq) **und** in der Spot-Rendite 24 h ohne Kosten. Sonst ist L1 nicht bestanden, auch wenn der Abstand steigt.

**Ergänzung 2, Signalbilanz je Asset (stehend bei jeder REGELn):** `messe_signalbilanz_je_asset.py` zeigt die Signale vorher und nachher je Jahr für **alle** Assets
aus **Watchlist (Krypto), Bestand und Hebel-Liste**. Quelle ist der NB-Teilexport, der dafür um Watchlist und Bestand erweitert wurde (nur Symbole). Bis zum
nächsten NB-Lauf kommt der Bestand aus der Desktop-Kopie (Stand 19.07.), mit Vermerk.

**Festgelegt:**
- `messe_losfahren.py --kern --ruhe 48 --junge --mit-btc --liq` in 4 Mengen, Wahl nur auf **bestand**, die übrigen nur L0-Auskunft.
- Fällt ein Einstieg unter X, entfällt er **ersatzlos**. Eine spätere Stunde rückt nicht nach.
- Liquidität = Summe Volumen × Schluss über **24 lückenlose** Stunden bis zur Einstiegsstunde, sonst unbekannt (und bei X > 0 nicht zugelassen).
- L2: `messe_k6_hebelstufe.py --simulation 24,ohne,0.02 --spur-regel0 <csv> --spur-alle` (bestand), dann `messe_l2_liq_risiko.py` auf 2024.
- R-R11: Bei X = 0 sind die Einstiege die der REGEL0, die Simulation mit Spur ist zeilengleich zum REGEL0-Beleg.
- **Stopp und Bericht** nach L0, Wahl, L2 und Signalbilanz.

---

## 10. ERGEBNIS (Befund 2.704) — Stopp und Bericht

> **Urteil in einer Zeile:** **L1 ist nicht bestanden, und zwar aus einem lehrreichen Grund: Die Beziehung ist umgekehrt.** 2024 hatten die Einstiege
> bei **geringer** Liquidität die **bessere** Chance und mehr Vorteil, in allen vier Mengen gleich. Jeder Mindestfilter hätte die **besseren** Einstiege weggenommen.

### L0 — Dosis und Wirkung 2024 (Belege `L_01_10/liq__<m>.txt`)

| Liquidität 24 h | Chance bestand / unverzerrt:1–3 | Spiegel | Spot 24 h ohne Kosten |
|---|---|---|---|
| < 0,5 Mio (17–33 Einstiege) | +0,27..+0,52 | +0,07..+0,18 | +1,3..+1,6 % |
| 0,5–1 Mio | +0,20..+0,24 | +0,11..+0,14 | +0,8..+1,0 % |
| **1–2 Mio** | **+0,27..+0,36** | **+0,19..+0,28** | **+1,3..+2,0 %** |
| **2–5 Mio** | **+0,23..+0,26** | **+0,21..+0,26** | **+1,4..+2,0 %** |
| 5–10 Mio | +0,09..+0,14 | +0,08..+0,16 | +0,8..+0,9 % |
| 10–20 Mio | +0,09..+0,11 | +0,12..+0,15 | +0,6..+1,6 % |
| ≥ 20 Mio | +0,09..+0,10 | +0,10..+0,13 | +0,75..+1,1 % |

- **Richtung, nicht nur Bewegung:** Der Spiegel (+5 % zuerst minus −5 % zuerst) ist unten ebenfalls höher.
- **Überwiegend ATR-frei:** Innerhalb der ATR-Drittel bleibt das Muster meist erhalten (z. B. niedrige ATR, 1–5 Mio: +0,15..+0,30 gegen ≥ 20 Mio: +0,02..+0,09).
- **Gegenprüfung:** Die Liquidität ist für 200 Einstiege unabhängig aus der Datenbank nachgerechnet, 200/200 gleich. R-R11: X = 0 trifft die REGEL0 (bestand 2.222, Abstand +0,0882).

### L1 — die Regel (Wahl 2024)

Jedes X > 0 senkt den Abstand. Die weggenommenen Einstiege sind **besser** als die behaltenen (z. B. X = 5 Mio bestand: weggenommen Chance +0,24 / Spot +1,33 %,
behalten Spot +0,78 %). Die Regel wählt **X = 0 in 4 von 4 Mengen**. Der Qualitätsgewinn ist negativ. ➤ **L1 nicht bestanden**, es gibt keinen Filter.

### L2 — Risiko über die ATR hinaus (Beleg `L_01_10/l2__bestand.txt`)

Nicht messbar: 2024 gab es nur **8 Liquidationen** in 2.188 Handeln und **keine** Stufe 2x. Auch hier ist der Spot-Vorteil unten höher.

### Signalbilanz REGEL0 (Beleg `L_01_10/signalbilanz_regel0__bestand.txt`)

- Je Asset **25–45 Signale im Jahr**, sehr gleichmäßig. Beispiele 2024 / 2025 / 2026 (bis August): BTC 24 / 42 / 29 · ETH 28 / 39 / 24 · LINK 27 / 45 / 28 · SOL 27 / 37 / 26.
- Von **58** Assets aus Watchlist, Bestand und Hebel-Liste bekommen **28** Signale. **16 Krypto-Assets haben keine Stundenkurse**: Hebel-Liste HYPE, AKT, CAT, GRIFFAIN, XDC, dazu
  gehaltene bzw. beobachtete ASTER, CANTON, KAS, MON, SUPRA, VSN, BRETT, AIOZ, FLOKI, PLUME, XNO. Die übrigen 14 sind Aktien, ETFs oder Cash.
- ⚠️ Der Bestand stammt aus der Desktop-Kopie (19.07.). Der nächste NB-Teilexport liefert den aktuellen Stand.

### Was das heißt (Einordnung, zur Abstimmung)

| # | |
|---|---|
| 1 | **Kein Filter.** Dünn gehandelte Werte sind für den Kern **kein** Problem, 2024 waren sie sogar besser. Das passt zum Grundsatz *kein Asset-Vorurteil* (Regel 3) |
| 2 | **Ein neuer Hinweis**, noch keine Regel: Die Wirkung läuft in Gegenrichtung (geringe Liquidität hebt die Chance). Das wäre eine **eigene Hypothese**, vorab festzulegen und auf 2025–26 einmal zu bestätigen. 2025–26 ist für die Liquidität noch **unberührt** |
| 3 | ⚠️ **Was die Messung nicht sieht:** Bei dünnem Handel sind **Spread und Ausführung** teurer. Unser Kostenmodell rechnet pauschal 0,3 %. Der Vorteil unten kann im echten Handel teilweise verloren gehen, und das ist ohne Orderbuchdaten (D) nicht messbar |
| 4 | **Spannung zu Teil 0 (2.703):** 2025–26 brachten später eingestellte Paare weniger. Ob die mit geringer Liquidität dieselben sind, ist offen und wäre in der Bestätigung als Auskunft zu klären |
| 5 | **Die größte konkrete Lücke im Betrieb** sind die **16 Krypto-Assets ohne Stundenkurse**. Für sie kommt **kein** Signal an, auch für HYPE auf der Hebel-Liste nicht. Das ist O5 (Beschaffung derselben Datenart) |
