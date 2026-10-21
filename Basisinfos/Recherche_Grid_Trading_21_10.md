# Recherche Grid-Trading (Stand 21.10.2026)

**Wozu:** Nutzer 21.10.: *„Danach gehe in Recherche und prüfe, wie automatisiertes GRID-Trading funktioniert und ob wir so eine Lösung mit oder ohne LLM bauen können – Start: nur BTC und ein Altcoin meiner Wahl, kann wechseln.“* Anlass ist die Bilanz der LLM-Komponente (E-125, `Bilanz_LLM_Komponente_21_10.md`).

Grundlage sind zwei Recherchen vom 21.10.: A zu Funktionsweise, Belegen und Risiken, B zu Börsen, APIs und Werkzeugen für einen Kunden in Österreich. Abgeglichen ist das mit unserer Datenlage und unseren Befunden. **Keine Anlageempfehlung, keine steuerliche Einordnung.**

## 1. Wie ein Gitter funktioniert

- **Aufbau:** Man legt eine untere Grenze, eine obere Grenze und N Stufen fest.
  - *Arithmetisch* heißt gleicher Preisabstand.
  - *Geometrisch* heißt gleiches Verhältnis q = (P_o/P_u)^(1/N), also gleicher Prozentgewinn je Stufe. Bei breiten Bändern ist das die sinnvollere Form.
- **Start:** Über dem Kurs liegen Verkaufsorders, darunter Kauforders. Für die Verkaufsorders braucht man ein **Startinventar**, das beim Start zum Marktkurs gekauft wird (Binance-FAQ). Startet man in der Bandmitte, ist man sofort zu etwa der Hälfte investiert.
- **Je Durchlauf:** Ein Kauf füllt sich, dann wird eine Stufe höher ein Verkauf gesetzt. Ein Verkauf füllt sich, dann wird eine Stufe tiefer ein Kauf gesetzt.
  - Netto je Paar ≈ Stufenabstand − 2 × Gebühr.
- **Ausbruch:**
  - *nach oben:* Alles ist verkauft. Der Gewinn ist gedeckelt und der weitere Anstieg fehlt.
  - *nach unten:* Man ist voll investiert und hat auf dem Weg nach unten nachgekauft. Der Verlust entspricht etwa dem Halten, gemildert nur um die Gittergewinne.
- **Varianten:**
  - unendliches Gitter: hält den Positionswert konstant, also ein Rebalancing;
  - Trailing: das Band wandert mit;
  - Futures-Gitter mit Hebel: dazu kommen Liquidation und Funding;
  - dynamisches Gitter: wird nach einem Ausbruch neu gesetzt.

## 2. Woran es verdient – der Kern

> **Bei einem reinen Zufallspfad ist der Erwartungswert eines Gitters ohne Gebühren NULL.**
> Chen/Chen/Jang, arXiv 2506.11921, 2025: Die Gittergewinne gleichen genau den Inventarverlust aus.

- Ein Vorteil entsteht **nur**, wenn der Kurs auf der Skala des Stufenabstands **stärker zur Mitte zurückkehrt als ein Zufallspfad**, und zwar so stark, dass es mehr als die Gebühren einbringt.
- Das Profil entspricht einer **Short-Volatility-Position** (Quantpedia 2022): Seitwärtsphasen bringen Gewinn, Trendphasen Verlust.
- **„Gitter-Gewinn“ ist nicht das Ergebnis.** Die Anbieter zeigen den realisierten Gittergewinn, oft auf das Jahr hochgerechnet. Das Gesamtergebnis ist Gittergewinn plus Inventargewinn oder -verlust.
  - Beispiel (Einzelfall, OKX-Nutzerbeitrag 26.09.2026): *+1.139 % annualisiert* angezeigt, **−11,73 % gesamt**.
- **Gegen Halten:** Im Aufwärtstrend liegt das Gitter strukturell zurück, weil es früh verkauft. Seitwärts kann es vorne liegen. Im Abwärtstrend verliert es ähnlich wie Halten, nur etwas gemildert.

## 3. Belege – dünn

| Quelle | Befund | Schwäche |
|---|---|---|
| Chen/Chen/Jang 2025 (1-min Binance, BTC/ETH 2021-01 bis 2024-07, Gebühr 0,08 %) | dynamisches Gitter IRR „bis 60–70 %“, nach den Autoren vor allem durch steigende Kurse; ETH: IRR kaum höher, Drawdown kleiner | Band im Nachhinein gewählt, ein Zeitraum (überwiegend Bullenmarkt), keine Reproduktion |
| Stevens Institute FE 800 (2024) | ML-Parameter (Random Forest, LSTM) schlagen die einfache Wahl **nicht** | keine Zahlen veröffentlicht |
| Börsen (Binance, Pionex, Bitget, KuCoin) | **keine** aggregierte Statistik über die Erfolge der Nutzer | nur Formeln und Backtest-APYs als Schätzung |
| Ratgeber und Binance Square | „+23,4 %“, „+31 %“, Einzel-Backtests | keine Primärquelle, Werbung |

**Fazit:** Theoretisch ist das Gitter ohne Rückkehr zur Mitte null. Empirisch gibt es nur Backtests mit Vorgriff- und Bullenmarkt-Verzerrung.

## 4. Mit oder ohne LLM?

**Ohne LLM baubar. Ein LLM hat keinen belegten Ansatzpunkt.**

- **Denkbar wären drei Aufgaben:** Band und Stufen wählen, bei Nachrichten pausieren, auf Dauer fallende Coins ausschließen.
- **Gefunden wurde keine Studie mit Nachweis.** Nahe Befunde sprechen dagegen: Bei Stevens schlug ML die einfache Wahl nicht, FINSABER (2025) fand, dass LLM-Timing über die Zeit keinen Vorsprung hält, und Zhu/Cai (2026) fanden keinen dauerhaften Nettovorteil.
- **Unsere eigene Messung passt dazu.** Der gefährliche Fall für ein Gitter ist der **Absturz**, also das Nachkaufen ins fallende Messer. Genau dafür hat L-C2 (Schritt7 §23.75) gezeigt, dass ein sauberes LLM die 16 Absturztage 2025–26 aus den Schlagzeilen des Vortags **nicht** erkennt. Vor dem 10.10.2025 urteilte es *niedrig*.
- **Was die Ertragsfrage entscheidet, ist messbar und regelbasiert:**
  - Rückkehr zur Mitte auf Stufenskala (Varianz-Ratio, Autokorrelation, Zahl der Durchläufe gegen Zufallspfade);
  - Band aus der Volatilität (ATR- oder Quantil-Vielfache);
  - Mindestabstand größer als 2 × Gebühr;
  - Pause außerhalb des Bandes, Stopp unter der Untergrenze, Neusetzen nach Ausbruch.
- ⚠️ **Ein Trendfilter ist kein Selbstläufer:** Bei uns gilt *„Der Marktzustand ist nicht vorab erkennbar“*, und das Regime wiegt zwölfmal mehr als die Lage. Ein Filter „nur seitwärts laufen lassen“ wäre deshalb erst zu messen.

## 5. Verbindung zu unseren Befunden (Einordnung, meine – keine Messung)

- **REGEL0 ist bereits eine Wette auf Rückkehr:** Kauf nach einem Rückgang, Gegenbewegung binnen 24 h. Die *Lage ist ordenbar* (Reverse Momentum, Lift ~1,9). Der KERN verliert aber **an den Kosten, nicht am Signal**: ~0,48 % je Runde über Bitpanda.
- **Ein Gitter tauscht beides:** Es arbeitet mit Limitorders, also Maker-Gebühren von 0,10 % bis −0,005 % je Seite statt Broker-Spanne, und **je Asset über die Zeit** statt im Querschnitt nach einem Rückgang.
- ⚠️ **Ob unsere Querschnitts-Rückkehr auch als Zeitreihen-Rückkehr eines einzelnen Assets auf Stufenskala besteht, ist NICHT belegt.** Das wäre eine andere Messung („Unbedingte Messung nicht auf eine Teilmenge übertragen“). Genau sie wäre die erste Prüfung.

## 6. Wo es laufen könnte (Österreich, Stand der Recherche B)

| Börse | MiCA | Gebühren Maker / Taker | Eigener Grid-Bot | API / Werkzeug |
|---|---|---|---|---|
| **Bitpanda Broker** (heute im Einsatz) | ✔ | 0,99 % BTC / 1,49 % Alts je Seite (Spanne) | – | **für ein Gitter zu teuer** |
| Bitpanda Fusion | ✔ | 0,25 % → 0,02 % (Staffel) | – | REST mit Handelsrecht, Limitorders; WebSocket erst angekündigt; kein ccxt |
| One Trading | ✔ (AFM) | API −0,005 % / 0,015 % | – | REST, ccxt `onetrading`; Zugang für Privatkunden unklar |
| Bybit EU | ✔ (FMA Wien) | 0,10 / 0,10 % | Spot-Grid seit 09/2025 | ccxt, Freqtrade |
| OKX (MyOKX) | ✔ (Malta) | 0,08 / 0,10 % | Spot-Grid | ccxt |
| Kraken | ✔ | 0,25 / 0,40 % | Smart-Grid seit 09/2026 | ccxt |
| Binance | ✘ für AT seit 01.07.2026 nicht rechtssicher | – | – | **nur als Datenquelle** (frei) |
| Bitget, Pionex | ✘ | – | – | nicht rechtssicher |

- **Werkzeuge (frei):**
  - ccxt (MIT);
  - Hummingbot (Apache, Grid-Executor);
  - Freqtrade (kein fertiges Gitter);
  - Jesse: Live-Handel kostenpflichtig, scheidet aus.
- ⚠️ **Ein eigenes Konto bei einer weiteren Börse legt der Nutzer selbst an.** Ein Gitter erzeugt viele Einzelgeschäfte, und seit 2026 gilt die DAC8-Meldepflicht. Beides gehört vor jeden Live-Betrieb, ist aber **keine** Frage des Rückspiels.

## 7. Wie ein seriöses Rückspiel aussähe

- **Auflösung:**
  - Stundenkerzen genügen für ein enges Gitter nicht, weil die Reihenfolge von Hoch und Tief innerhalb der Kerze unbekannt ist.
  - **1-Minuten-Kerzen** sind das Mindeste. Sie liegen frei auf data.binance.vision, als Monatsdateien zu je ~2 MB je Paar.
  - Lokal haben wir Stundenkurse (BTC, SOL, AVAX ab 2023-09; ETH, LINK, ADA ab 2021-12; XRP, DOGE ab 2023-01; SUI ab 2023-05).
- **Konservative Füllung:** Eine Order gilt erst als gefüllt, wenn der Kurs die Stufe um einen Tick **durchschreitet**. Ist die Reihenfolge unklar, zählt höchstens ein Durchlauf je Stufe und Kerze.
- **Kein Vorgriff:** Die Bandregel wird **vorab** festgelegt (Walk-Forward), nie aus dem Testzeitraum. Das ist genau der Fehler bei Chen u. a.
- **Nullpunkt:** Dasselbe Gitter läuft auf Nullwelten, etwa mit Zufallspfaden aus der eigenen Schwankung. Ihr Ertrag ist theoretisch null, und genau das macht den Nullpunkt herleitbar (Messstandard).
- **Getrennt ausweisen (Regel 2):**
  - die **Bewertung** (Rückkehr über die Nullwelt, ohne Gebühren);
  - die **Anwendung** netto bei mehreren Gebührenstufen: 0,02 / 0,10 / 0,25 % je Seite.
- **Vergleich:**
  - Halten derselben Startmenge;
  - 50/50-Rebalancing;
  - reiner Stablecoin.
- **Ausweisen:** das **Gesamtergebnis**, nicht den Gittergewinn, dazu Drawdown und Kapitalnutzung. Mehrere Marktphasen einschließen; Messfokus ab 2023/24.

## 8. Stand und offene Frage

- **Baubar ja, ohne LLM.** Ob es etwas einbringt, entscheidet **eine messbare Frage**: Kehrt der Kurs von BTC und des gewählten Altcoins auf der Skala von ~0,5–3 % stärker zur Mitte zurück als ein Zufallspfad, und zwar über die Gebühr?
- **Nichts gemessen, nichts gebaut, nichts heruntergeladen.**
- **Zur Abstimmung:** der nächste Schritt (Stufe-1-Vorprüfung auf den vorhandenen Stundenkursen, gleich 1-min-Rückspiel oder nicht weiterverfolgen) und die Wahl des Altcoins.

## 9. Messplan Stufe 1 (W-A) — Rückkehr zur Mitte auf Stufenskala, VORAB festgelegt (22.10.2026)

Nutzer 22.10.: *„ok, können eine kurze Prüfung machen für W-A, dann müssen wir u. U. zurück zu Alternativen oder Bestehendes noch einmal analysieren.“*

**Die eine Frage:** Kehrt der Kurs von BTC und ETH auf der Skala von 1–3 % so viel stärker zur Mitte zurück als in einer zufälligen Reihenfolge derselben Bewegungen, dass ein Gitter **mehr als die Fusion-Gebühr** (0,25 % je Ausführung) verdient?

**Daten:**
- `data/stundenkurse.db` (Messbasis, nur lesend), Binance-Spot, Stundenschlüsse.
- BTC und ETH, gemeinsames Fenster **2023-09-01 bis 2026-08-31** (36 volle Monate, Messfokus).
- Fehlende Stunden erhalten den Vorstundenkurs; ihre Zahl wird ausgewiesen.

**Das Gitter (Bewertungsform):**
- geometrisch, Stufe **g = 1 %, 2 %, 3 %** (Auskunft 0,5 %);
- **jeden Monat neu**: Bezug ist der erste Stundenschluss, Bestand 0; am letzten Stundenschluss wird glattgestellt;
- jede Ausführung hat denselben Nennwert (1 Einheit Geld);
- Leiter mit *zuletzt gehandelter Stufe*: verkauft wird eine Stufe höher, gekauft eine tiefer. Gefüllt wird zum **Stufenpreis**, sobald ein Stundenschluss die Stufe erreicht; mehrere Stufen in einer Stunde ergeben mehrere Füllungen;
- ⚠️ Der Bestand darf negativ werden. Das ist eine Bewertung der Rückkehr, **nicht** der Betrieb; am Spot wäre die obere Seite durch das Inventar begrenzt.

**Größen:**
- Ergebnis je Monat und Summe (in Einheiten Nennwert);
- Zahl der Ausführungen (Füllungen plus Glattstellung);
- Ergebnis je Ausführung.

**Nullwelt (herleitbar):**
- 200 Ziehungen; **je Monat** werden die stündlichen Log-Renditen zufällig umgeordnet.
- Anfang und Ende jedes Monats und die Schwankung bleiben gleich; zerstört wird nur die **Reihenfolge**.
- Bei Zufallsreihenfolge ist ein Gitter im Mittel ein Nullsummenspiel.
- **Rang** = Anteil der Nullwelten mit kleinerem Ergebnis.

**Überschuss je Ausführung** = (echt − Mittel der Nullwelten) ÷ Ausführungen echt, in % des Nennwerts. Maßstab: **0,25 %** (Fusion, Grundstufe).

**Trägt (je Zelle Asset × Stufe, vorab, zweiseitig):**

| | |
|---|---|
| trägt | Rang ≥ 0,95 **und** Überschuss je Ausführung ≥ 0,25 % **und** Überschuss > 0 in **beiden Hälften** (2023-09 bis 2025-02 / 2025-03 bis 2026-08) |
| umgekehrt | Rang ≤ 0,05: Auf dieser Skala herrscht **Trend**, und ein Gitter schadet |

**Folgen, vorab:**

| Ergebnis | Folge |
|---|---|
| mindestens eine Zelle trägt | **Stufe 2**: Rückspiel eines echten Spot-Gitters (Band, Inventar, Fusion-Kosten) auf 1-Minuten-Kerzen. Der Download braucht ein **Nutzer-Ja** |
| keine Zelle trägt | **W-A endet.** Zurück zu den Alternativen bzw. eine neue Analyse des Bestehenden (Nutzer 22.10.) |

**Auskunft:**
- g = 0,5 %;
- Netto-Ergebnis bei 0,25 % je Ausführung;
- SOL und LINK im selben Fenster.

⚠️ **Ehrlich vorab:**
- Stundenschlüsse sehen nichts **innerhalb** der Stunde. Ein echtes Gitter füllt öfter; eine Rückkehr innerhalb der Stunde bleibt hier ungemessen (das wäre Stufe 2).
- Sechs Zellen ergeben Mehrfachtesten. Die Gebührenschwelle und die Bedingung „beide Hälften“ begrenzen das.

### 9.1 Fassung 1 gelaufen — das INSTRUMENT ist falsch herum, das Ergebnis ist ungültig (22.10.2026; `grid_stufe1.py`, `grid_stufe1_gegenprobe.py` → `.txt`)

- **Ergebnis von Fassung 1 (nur festgehalten, nicht bewertet):** alle 6 Zellen Rang 0,000 bis 0,040, also *„umgekehrt (Trend)“*. SOL und LINK ebenso.
- **Gegenprobe:**
  - G1 eigene Gitterschleife (gleich) ✔
  - G2 Nullwelt behält das Monatsende ✔
  - **G3 Selbsttest mit bekannter Wahrheit ✘:** Eine künstliche Welt mit *Rückkehr zur Mitte* (Stundenrenditen φ = −0,10) erhielt Rang **0,000**, eine *Trend*-Welt (φ = +0,10) Rang **1,000**. Das Instrument zeigt die Richtung also **verkehrt** an.
  - **G4 zweiter Weg ✘:** Die Varianz-Ratio zeigt keinen Trend, sondern eine leichte Rückkehr: VR(24) BTC 0,952 (z −1,0), ETH 1,030 (+0,6), SOL 0,918 (−1,6), LINK 0,940 (−1,2); SOL VR(6) 0,930 (z −2,8).
- **Ursache (aus der Sache, nicht nachgestellt):**
  - Die Nullwelt hat die Stundenrenditen je Monat **umgeordnet**. Damit bleiben Anfang **und Ende** jedes Monats fest.
  - Bei festem Monatsende ist der Restbestand des Gitters vorgegeben, und das Ergebnis hängt nur noch an der **Zahl der Stufendurchgänge**.
  - Eine Rückkehr zur Mitte *verringert* die Schwankung auf längerer Skala, also auch die Durchgänge. Sie erscheint deshalb als Nachteil.
  - Ihr eigentlicher Vorteil für das Gitter, ein **Monatsende nahe am Start und damit ein kleiner Restbestand**, war durch die Nullwelt ausgeschaltet.
- ⇒ Fassung 1 misst die **falsche Frage**. Ihr Ergebnis ist **kein Befund**, auch nicht *„Trend“*.

### 9.2 Messplan Fassung 2 — VORAB, Selbsttest ZUERST (22.10.2026)

**Was sich ändert**, und nur das:
- **Nullwelt = Zufallspfad.** Je Monat 200 Ziehungen der Stundenrenditen **mit Zurücklegen** aus demselben Monat.
  - Gleich bleiben die Schwankung und die erwartete Drift des Monats; das **Monatsende ist frei**.
  - Für einen Zufallspfad ist das Gitter in der Theorie ein Nullsummenspiel (bis auf Mechanik, die echt und Nullwelt gleich trifft).

**Selbsttest VOR der Messung:** Pflicht, sonst wird nicht gemessen.
- Künstliche Monate mit der BTC-Stundenschwankung:
  - Rückkehr φ = −0,10 → Rang ≥ 0,95;
  - Trend φ = +0,10 → Rang ≤ 0,05;
  - unabhängig φ = 0 → Rang dazwischen.

**Unverändert aus §9:** Daten, Fenster, Stufen, monatliches Neusetzen, Glattstellung, Nennwert, Schwelle 0,25 % je Ausführung, beide Hälften, zweiseitig, Folgen, Auskunft.

⚠️ **Ehrlich:** Fassung 1 und G4 sind angesehen. G4 zeigt eine leichte Rückkehr auf Stunden bis Tage. Das Urteil hängt aber an der **Größe über der Gebühr**, nicht an der Richtung, und diese Größe ist ungesehen.
