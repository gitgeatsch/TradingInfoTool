# Der Hebel in fünf Phasen — Planung und Stand

**27.09.2026** · Nutzervorgabe wörtlich, danach der Abgleich

> Dieses Blatt löst `Bauplan_Hebel_27_09.md` als oberste Liste ab. Der
> Bauplan bleibt gültig für die **technischen** Schritte (Dateien,
> Reihenfolge, Fallen), ist aber der Phase 1 untergeordnet.

### ⭐⭐⭐ Das REGELWERK zur Bewertung

`Basisinfos/Regelwerk_Hebel_Bewertung_27_09.md` — wie aus einer Messung
eine Regel wird. **Einstieg misst gegen die CHANCE, Hebel gegen das RISIKO.**

⛔ Entstanden aus der Nutzerkritik vom 27.09.: *„Was ist mit turnover und
funding, diese waren bereits gesetzt oder?“* — an einem Tag zehn
Kursmerkmale gemessen und die **drei registrierten Träger** nie geladen.

---

### ⭐⭐⭐ PLAN UND VORGEHEN AB 30.09.2026 — von der REGEL0 bis zum Betrieb

**Nutzer 30.09.2026:** *„Bitte Plan und Vorgehensweise dokumentieren und auch offene Punkte und Schwächen. Wenn wir eine Lösung haben,
die nur am Desktop im Labor funktioniert, ist es ein FAIL."*

> ⛔⛔ **LEITSATZ (E-35):** Eine Regel ist erst dann fertig, wenn sie **am Notebook im Betrieb** mit den **dort verfügbaren Daten**,
> derselben **Grundgesamtheit** und **ohne Handgriff am Desktop** dieselben Signale erzeugt wie in der Messung. Was nur im Labor läuft,
> ist ein **FAIL**, egal wie gut die Messung ist.

Zugehörige Dokumente: `REGEL0_Hebel_Entwurf_30_09.md` (Parameter und Referenzzahlen) · `Lagebewertung_30_09.md` · `Voranalyse_J_Mindesthistorie_30_09.md` ·
`Voranalyse_REGEL0_Hebelliste_30_09.md` · Stand im Code `python hebel_neubau.py`.

---

#### 1. Der Plan — in dieser Reihenfolge

| # | Schritt | Inhalt | Stand |
|---|---|---|---|
| 1 | ✔ **J Showstopper Mindesthistorie — BESTANDEN (2.698)** | Das eigene Normal gilt ab 240 h statt 12 Monate, über die bestehende Schrumpfung, reife Assets bitgleich | Voranalyse zur Abstimmung (J-a bis J-d) |
| 2 | ✔ **Schwellenwahl prüfen — bestätigt s = +0,035 (2.699)** | Wählt die Regel auf der **vollständigen** 2024-Menge (nach J) wieder s = +0,035? (49 von 116 Symbolen fehlten 2024 großenteils) | nach J |
| 3 | ✔ **REGEL0 festschreiben — FESTGESCHRIEBEN 01.10.2026 (E-36)** | Parameter und Referenzzahlen (mit J), im Dokument **und im Code** (eine Konstante, von der Wache geprüft) | nach 1–2, Nutzer-Ja |
| 4 | **Betriebsprüfung REGEL0** (Abschnitt 3) | Welche Daten und Rechenwege hat das Notebook, was fehlt? Das ist eine **Befundaufnahme** und noch kein Bau | nach 3 |
| 5 | ✔ **Messung auf der Hebel-Liste — nach Kosten positiv (2.700)**: ×1,23, Rohvorteil +0,87 %, Rückgang 0,08; die Auswahl trägt (Zufallslisten +0,59 %). ⚠️ Rückschau-Vorbehalt | REGEL0 auf deinen 43 Assets (28 mit Daten, dazu die jungen durch J) | nach 3 |
| 6 | **REGEL1 … n** — ausreizen | je ein Schritt gegen die Vorstufe: **A** Positionsführung (⛔ **2.702 nicht bestätigt, 0/4**: auf 2024 gewählt 72 h · Stop 1,5 ATR · Verzug 1 h, 2025–26 Konto −1,62..−2,01 gegen REGEL0; die Einstiege tragen weiter, die Ausstiegsform nicht; REGEL0 bleibt — `Voranalyse_A_Positionsfuehrung_01_10.md` Abschnitt 7) · **B** Kern stabilisieren (⛔◐ **2.703 nicht bestanden**: weniger Springen kostet Chance; ⭐ Teil 0: ohne Kosten ist die REGEL0 in 4/4 positiv, die Kosten sind der größte Posten, dann Gegenwind und später eingestellte Paare — `Voranalyse_B_Kern_stabilisieren_01_10.md` Abschnitt 8) · **R** Regime-Kontext aus der Überfüllung · **L** Liquidität (⛔⭐ **2.704**: L1 Mindestfilter nicht bestanden, die Beziehung ist **umgekehrt**: geringe Liquidität hatte 2024 die bessere Chance, 4/4; L2 nicht messbar; Signalbilanz: 16 Krypto-Assets der Listen ohne Stundenkurse — `Voranalyse_L_Liquiditaet_01_10.md` Abschnitt 10) · Käuferanteil auf dem Kern | Reihenfolge je Stufe abstimmen |
| 7 | **Betriebsvorbereitung** | Mindestbedingungen abstimmen (Nutzer: *„reden wir, wenn wir zu diesem Schritt kommen“*). Die bestehende Hebel- und Spot-Achse wird **ersetzt**, kein Parallelbetrieb | später |
| 8 | **Umstellung** | nach der ganzen Kette samt LLM-Rollen und Mail | später |

⏸ **Derzeit nicht Teil des Umbaus (Nutzer, E-33):** C Vorwärtstest · D neue Datenquellen · E Börse/Kosten.

---

#### 2. Die Vorgehensweise je Schritt — Pflichtablauf

| # | Pflicht | Quelle |
|---|---|---|
| 1 | **Voranalyse** mit Ziel, Stand, *Test oder Betrieb*, Zwischenfazit zum Ziel, dann Abstimmung (Nutzer-Ja) | stehend |
| 2 | **Vorab-Festlegung** der Kriterien, Werkzeug **vor** dem Lauf committet, Funktionstest | stehend |
| 3 | **R-R11**: die Vorstufe (REGELn) zuerst **bitgleich** reproduzieren | R-R11 |
| 4 | Zahlen per **Regel** messen, nie zur Wahl vorlegen. Wahl auf **2024**, **einmal** bestätigt auf 2025–26 | E-24, E-21 |
| 5 | Nullwelt, Zeitstabilität, Weglassprobe, Mehrfachtesten, je Asset, Tagesblock | die sechs Prüfungen |
| 6 | **Spiegelprobe** bei jedem Potential- oder Bewegungsmaß | E-29 |
| 7 | 4 Mengen, Urteil auf **unverzerrt**, wenn es auseinanderläuft | E-30 |
| 8 | ⭐ **Betriebsprüfung** (neu, E-35): Gibt es jede verwendete Größe **am Notebook**? Mit welchem Stand, welcher Historie, welcher Grundgesamtheit? Rechnet es dort **ohne** Desktop? | Abschnitt 3 |
| 9 | Befund, Doku (Zentraldokumente, Regelwerk, Plan, Memory), Wache grün, Commit und Push, **Zwischenfazit zum Ziel** | stehend |

---

#### 3. ⛔ Betriebsprüfung — was die REGEL0 am Notebook braucht und was dort ist

Stand laut Doku (`project_messbasen_geraeteaufteilung`, CLAUDE.md). ⚠️ **Das muss am Notebook bestätigt werden** (sparsamer Export, Schritt 4).

| # | braucht die REGEL0 | am Desktop (Labor) | am Notebook (Betrieb), laut Doku | Bewertung |
|---|---|---|---|---|
| **B1** | **Stundenkurse** je Asset (rsi, Ruhe, ATR, Ereignis) | `stundenkurse.db` 346 MB, 116 Symbole ab 2021/2023 | ⚠️ nicht als Datei dokumentiert. Die Betriebskopie `messdaten.db` hat 30 MB, 500 Tage, **ohne eingestellte**. Auflösung zu prüfen | ⛔ **Showstopper-Kandidat** |
| **B2** | **Modelltraining** rsi (monatlich, alle Assets gepoolt, Historie ab 2023) | läuft im Messskript | ⛔ keine Trainingshistorie dokumentiert | ⛔ **Showstopper-Kandidat**. Ein Training am Desktop mit Übergabe von Hand wäre ein **FAIL** (E-35) |
| **B3** | **ATR-Modell** der Hebelstufe (rollierend geschätzt) | im Messskript | wie B2 | ⛔ wie B2 |
| **B4** | **Markpreis** (Liquidation) | `markpreis_historie.db` 722 MB | ⚠️ nicht dokumentiert. Live beziehbar (Binance) | zu prüfen |
| **B5** | **Grundgesamtheit** gleich (die v̂-Skala hängt an der Menge, E-31) | 116 bestand, dazu die eingestellten | Betriebskopie **398 statt 517** im Rang (CLAUDE.md) | ⛔ **muss gleich werden**, sonst andere Signale |
| **B6** | **Symbolzuordnung** Bitpanda ↔ Binance | Namensgleichheit | keine Zuordnung (2.612, vier Symbolwelten) | ⛔ Voraussetzung |
| **B7** | 15 Assets deiner Liste **ohne Stundendaten**, dazu BTC als Leitwert ausgeschlossen | – | – | für diese Assets **kein Signal** möglich. Ist das Beschaffung derselben Datenart (kein D)? Zur Klärung |
| **B8** | das **Normal** (12 Monate beziehungsweise nach J ab 240 h) | aus der Historie | braucht B1 | hängt an B1 |
| **B9** | **Mail, LLM-Rollen, Importer** | – | kennen die neue Bewertung nicht; der Importer teilt Teilschließungen falsch ein (2.679) | Betriebsvorbereitung (Schritt 7) |

**✔ NB-BEFUND 01.10.2026 07:10** (`nb_teilexport_betriebsdaten.py` am T440, nur lesend; Beleg `Basisinfos/NB_01_10/nb_betriebsdaten_T440.txt`):

| | am Notebook vorgefunden | Folge |
|---|---|---|
| B1 Stundenkurse | ⛔ **keine** stündliche OHLC-Reihe. `stundenkurse.db` fehlt; `messdaten.db` (Betriebskopie, 42 MB) und `tradinginfotool.db` haben nur **Tageskerzen**, `price_cache` hat Schnappschüsse ohne Hoch und Tief | Bauaufgabe S2: Historie übertragen (346 MB) und laufend stündlich nachladen |
| B2/B3 Training | ⛔ **`scipy` FEHLT** (numpy 2.5.1 statt 2.4.6 am Desktop, pandas gleich, Python 3.13.14 gleich). Das rsi-Modell (`minimize`, `sparse`) und die Hebelstufe (`expit`) brauchen scipy | ✔ **scipy installiert (Nutzer 01.10.)**. Offen: R-R11 am NB gegen die REGEL0-Belege (bitgleich trotz anderer numpy-Version?), sobald die Daten dort liegen |
| B4 Markpreis | ⛔ `markpreis_historie.db` fehlt. Die Binance-Anbindung besteht aber (`open_interest_snapshot`, 40 Symbole) | Historie übertragen (722 MB) und laufend nachladen |
| B5 Grundgesamtheit | ⛔ Die Betriebskopie trägt 529 Symbole als **Tageskerzen**, die REGEL0 rechnet auf **116 Symbolen stündlich** | mit B1 dieselbe Menge herstellen |
| Speicher | ✔ 60 GB frei | reicht |
| B7 Hebel-Liste | ⚠️ **25 erlaubt** (am Desktop-Stand 24.09. waren es 43): 19 weggefallen (AIOZ, APT, ASTER, AVAX, BIO, BRETT, CANTON, FLOKI, IMX, IO, KAS, MON, PLUME, QNT, S, SUPRA, VSN, W, XNO), **XDC** neu. Ohne Messung bleiben AKT, CAT, GRIFFAIN, HYPE, XDC (keine Stundendaten) und KAIA (kein gültiger Markpreis) | 2.700 auf der heutigen Liste aus den Werten je Asset nachgerechnet (Summe der alten Liste bitgleich ×1,229): **18 Assets, 1.112 Handel, Konto ×1,144, Rohvorteil +0,815 %**, 2 Liquidationen. Weiter positiv nach Kosten. Beleg `Basisinfos/NB_01_10/liste_nb_aus_2700.txt` |

➤ **Urteil Schritt 4:** Am Notebook kann die REGEL0 **heute nicht** laufen: Es fehlen Stundenkurse, Markpreise und scipy. Das sind **Bauaufgaben** (S2, Nutzer 30.09.), kein Showstopper. Die Daten gibt es am Desktop. Laufend nachladen lassen sie sich über die Binance-Anbindung, die am Notebook schon besteht.

➤ **Folge für den Plan:** Jede **REGELn** wird nur dann festgeschrieben, wenn ihre zusätzlichen Größen die Prüfung B1–B9 bestehen
oder ein **Weg am Notebook** feststeht. R (Überfüllung marktweit) und L (Umsatz in USD, Marktkapitalisierung) nutzen Terminmarkt- und
Umsatzdaten, die am Notebook **live** kommen. Das ist dort also eher leichter als die Historie.

---

#### 4. Offene Punkte

| # | offen | wann |
|---|---|---|
| O1 | Abstimmung J (J-a bis J-d) | **jetzt** |
| O2 | Schwellenwahl auf der vollständigen 2024-Menge | nach J |
| O3 | Datenlage am Notebook **bestätigen** (B1–B5), mit einem sparsamen Export und nur den nötigen Tabellen. ✔ **Vorbereitet (01.10.):** `nb_teilexport_betriebsdaten.py`, nur lesend, ohne Netz, Ausgabe nur auf stdout. Aufruf am Notebook: `python nb_teilexport_betriebsdaten.py > nb_betriebsdaten.txt`, dann die Datei in den Austauschordner. Es zeigt Datenbanken, Tabellen, Zeiträume, Symbole, die Hebel-Liste und die Pakete. Am Desktop getestet (44 s, Produktion unverändert). ✔ **Gelaufen 01.10. 07:10 am T440** (Ergebnis direkt im Austauschordner): Es fehlen Stundenkurse, Markpreise und scipy, die Hebel-Liste ist 25 statt 43 (siehe NB-BEFUND oben) | erledigt, Bauaufgaben in Schritt 7 |
| O4 | Wo und wie das Modell im Betrieb trainiert wird (B2/B3), **ohne Desktop** | Schritt 4, Voranalyse |
| O5 | Die 15 Assets ohne Stundendaten: Beschaffung oder Ausschluss? Deine Entscheidung. ✔ **BTC** (Nutzer 01.10.: *„BTC soll dann am NB auch Hebel nutzen können“*): Heute schließt der Lader BTC als Leitwert aus. Nötig ist ein **eigener Schritt analog zu J**: Modell und Marktmitte bleiben ohne BTC (REGEL0 bitgleich), BTC wird zusätzlich ausgewertet und gemessen, ob es trägt. ◐ **Gemessen (2.701):** technisch sauber (die übrigen bitgleich), statistisch nicht nachweisbar (nur ~30 Signale je Jahr), wirtschaftlich unschädlich (Konto um null, keine Liquidation). ✔ **Nutzer 01.10.: aufgenommen (E-37)**, Vermerk *nicht nachgewiesen, unschädlich*; REGEL0-Referenz jetzt mit BTC | erledigt |
| O6 | Reihenfolge von A, B, R, L und Käuferanteil. ✔ **Entwurf A** (01.10.): `Voranalyse_A_Positionsfuehrung_01_10.md`, ein nachgezogener Stop in ATR (k × H), Einstieg REGEL0 unverändert, nur Erfolgsmessung. Zur Abstimmung, dazu die Nutzerfrage A-B1: Kann Bitpanda einen nachgezogenen Stop? | nach Schritt 5 |
| O7 | Mindestbedingungen Betrieb, Ersatz der Achse | Schritt 7 (Nutzer) |
| O8 | Spot-Zugänge PLUME, XDC, INJ | Spot-Arm, später |
| O11 | ⭐ **Datenbasis: ALLE abrufbaren Krypto-Assets stündlich halten** (Nutzer 01.10.: *wir nehmen alles, was es gibt, vor allem, wenn es im Bestand ist*). Binance 503 Spot + 165 nur als Futures; Zuordnungstabelle mit täglicher Preisprüfung; ✔ Futures-Kurse gleichwertig (Frage 3, Korrelation 0,993, rsi P95 2,4, ATR +3 %). Offen: Frage 4 (trainieren oder nur bewerten), dann Bau und Erstbefüllung. XDC, AIOZ, VSN, SUPRA nicht bei Binance, die Lücke wird in Kauf genommen — `Voranalyse_Datenbasis_alle_Assets_01_10.md` | zur Abstimmung |
| O9 | ⏳ **Idee des Nutzers (01.10., nicht jetzt):** eine **verteilte, ausgewählte Messmenge** nach Größenklassen, z. B. Kernwerte (BTC, ETH, SOL), dann größere und mittlere Werte, kleinere, wenige Ultra-Smallcaps. ⚠️ Die Einteilung der Symbole wird **gesondert besprochen** (Nutzer 01.10.: *meine Angabe ist ungenau und teilweise falsch, LINK ist eher ein Highcap*). Die Klassengrenzen sollen aus einer Messgröße kommen (z. B. Marktkapitalisierung zum jeweiligen Zeitpunkt), nicht aus einer Aufzählung. Nutzer 01.10. zum **Klassenwechsel**: *Assets aus den alten Bullruns in den Top 100 sind teilweise nicht mehr dort, im schlimmsten Fall jetzt ein Smallcap oder der Kurs ist tot* – das ist eine Ursache unseres Datenlage-Problems. ➤ Die Klasse muss deshalb **zum Zeitpunkt** gelten (was damals wusste man), nie nach heutigem Stand. Sonst ist die Menge überlebensverzerrt (wie bestand gegen unverzerrt, 2.668/2.669) und enthält einen Vorgriff. Die Datenquelle für die Marktkapitalisierung je Zeitpunkt ist zu prüfen (CoinGecko-Historie, `umlaufmenge_cg.db`). ✔ Die **25 am Notebook** sind *relativ aktuell*. Die Hebel-Liste wird sich ändern, ihre Verkleinerung hängt auch damit zusammen, dass das System *aktuell nicht so funktioniert wie geplant*. ➤ Deshalb wird die Regel nicht an die Liste gebunden: Die Liste ist nur Auskunft, das Urteil fällt auf den Mengen. Vor einer Umsetzung ist zu klären, wie sich die Grundgesamtheit dabei verhält (E-31, CLAUDE.md *Grundgesamtheit ist keine Stellschraube*) | später |
| O10 | **Marktphasen und Verlusthandel im Gegenwind** (Nutzer 01.10.: *eigenes Thema, nicht vollends durch eine einfache mathematische Rechnung zu lösen*). Gehört zu **R**. B Teil 0 liefert dazu nur die Aufteilung der Verluste (Auskunft) | mit R |

---

#### 5. Schwächen — ehrlich

| # | Schwäche | Einstufung | Weg |
|---|---|---|---|
| S1 | **Mindesthistorie 12 Monate** | ⛔ **Showstopper** (Nutzer) | J |
| S2 | **Betriebsdaten und Training am Notebook** (B1–B3, B5) | ✔ **Bauaufgabe Betrieb, kein Showstopper** (Nutzer 30.09.: *„Wenn es erforderlich ist, Daten vom Desktop auf das NB zu übertragen, dann werden wir dies natürlich machen, das ist gelebte Praxis — aber für den laufenden Betrieb brauchen wir ohnehin eine Datenanbindung.“*): einmal die Historie übertragen, dann die laufende Datenanbindung, dazu das Monatstraining als Job am Notebook. Bedingung bleibt **dieselbe Grundgesamtheit** | Schritt 7 |
| S3 | Vorteil je Handel (+0,29..+0,31 %) unter den Kosten (0,48 %) in der Messgeometrie | Schwäche | A (Positionsführung), R, L |
| S4 | Das Signalangebot springt (grobes Dämpfungsraster) | Schwäche, Betrieb: unberechenbar | B |
| S5 | Im Gegenwind stumpf (Modell flach) | Schwäche | R, dazu der Informationsgewinn als Auskunft |
| S6 | 2025–26 durch viele Ebenen verbraucht | methodisch | jede Stufe ehrlich als *besser als heute* (E-34) |
| S7 | Die Schwelle ist auf einer zu kleinen 2024-Menge gewählt | methodisch | O2 |
| S8 | 15 Assets der Liste ohne Daten, BTC nie als Asset gemessen | Abdeckung | O5 |
| S9 | Messanlage: bestand überlebensverzerrt, unverzerrt Stichproben | methodisch | E-30, Messung auf der Hebel-Liste |

---

### ⭐⭐⭐ STAND 30.09.2026 nachmittags — Kern heben (L2 bis Richtung)

| | Stand 30.09.2026 nachmittags (Befunde 2.691–2.695) |
|---|---|
| ✔ **Bewertung 1** | **Kern** (rsi-Ersteintritt, s = +0,035) **+ Ruhe 48 h** davor. Die Ruhe trägt eigene Information (2.691/2.692) und **verdoppelt** den Rohvorteil je Handel (2.694) |
| ✔ **Bewertung 2** | die **ATR** bleibt das Risikomodell. vola_kausal ist die ATR selbst (G-ATR, 2.691) |
| ⛔ **Stärke** | Die Stärke in der Übertrittsstunde ordnet nicht, der Kern ist ein **Schalter**. Das folgt zum Teil aus der Einstiegsform, weil 80 % der Einstiege zwischen +0,035 und +0,044 liegen (2.691; H-Schalter im Plan) |
| ⛔ **Wucht** (ema_abstand, volumenschub) | Sie trägt eigene Information für das **Potential** (2.692), wählt aber **größere Bewegungen in beide Richtungen**, keine bessere Richtung: Der Spiegel fällt 4/4 (2.693). **Rolle B** gehört in Positionsführung und Hebelstufe. E-28 greift nicht |
| ⛔ **Richtung weiter** (Tempo, Tiefe davor, Ruhe 72 h, top_konten_verh) | kein neuer Beitrag (2.695). Ruhe 72 h zeigt ein **gleiches Regimemuster** (2025 +, 2026 −) |
| ◐ **Erfolgsmessung** | Hebel mit Kern + Ruhe 48 h verliert weiter in 3/4 (unverzerrt ×0,63..×0,68). Rohvorteil **+0,29..+0,31 %** gegen **0,48 %** Kosten, die Lücke beträgt etwa **0,18 Prozentpunkte** (2.694) |
| ⭐ **Engpass** | das **Regime**: Verluste und Kippeffekte liegen im Gegenwind (zweites Halbjahr 2025) |
| ⚠️ **neue Pflichten** | **Spiegelprobe** bei jedem Potential- und Bewegungsmaß (E-29) · **Urteil auf unverzerrt**, bestand ist überlebensverzerrt (E-30) · **untere v̂-Grenzen** gelten nur in ihrer Menge (E-31) |
| ⭐⭐⭐ **PLAN UND VORGEHEN AB 30.09.** | Abschnitt *PLAN UND VORGEHEN AB 30.09.2026* oben in diesem Plan: 1 J → 2 Schwellenwahl auf der vollständigen Menge → 3 REGEL0 festschreiben → 4 **Betriebsprüfung am Notebook** → 5 Hebel-Liste → 6 REGEL1..n (A, B, R, L, Käuferanteil) → 7 Betriebsvorbereitung → 8 Umstellung. ⛔ **E-35: Labor-only ist FAIL** |
| ✔ **SHOWSTOPPER J BEHOBEN (2.698)** — vorher: *ZUERST: SHOWSTOPPER J* (Nutzer 30.09. spät) | `Voranalyse_J_Mindesthistorie_30_09.md` (J-a bis J-d zur Abstimmung): das eigene Normal ab 240 h statt 12 Monate über die bestehende Schrumpfung, reife Assets bitgleich. ⚠️ Gegenprüfung: **49 von 116** Symbolen haben Daten erst ab 2023-09 oder später (SOL, AVAX, BNB …), in der Wahl 2024 fehlten sie großenteils. Danach wird die Schwellenwahl auf der vollständigen Menge geprüft |
| ➤ **NÄCHSTER SCHRITT (Nutzer 30.09. spät)** | **REGEL0 auf der Hebel-Assetliste** (`Voranalyse_REGEL0_Hebelliste_30_09.md`, H1–H3 zur Abstimmung): 26 von 43 Assets messbar, 15 ohne Stundendaten, **BTC** im Lader als Leitwert ausgeschlossen. Danach wie im korrigierten Plan: REGEL0 → REGEL1 … (A, B, R, L). ⚠️ Nutzer: Die **Mindestbedingungen** für den Betrieb besprechen wir, wenn der Schritt kommt. Die bestehende Hebel- und Spot-Achse wird **ersetzt**, ein Parallelbetrieb ist schwierig |
| ⭐⭐ **OPTIONEN R und L** (Nutzer 30.09. abends, E-34) | **R** Regime-Kontext aus der **Überfüllung**: konten_verh und funding **marktweit**, dazu premium. Das sind die als Beitrag gefallenen Marktanteile, auf den Kern-Einstiegen 2024 der stärkste Effekt (Chance −0,243 gegen Zufall 0,155, L2-Wahl), zusammen mit dem Informationsgewinn (2.697) · **L** **Liquidität in Bewertung 2**: Umsatz in USD (`richtung_historie.fluss.quote_volumen`, Zahl der Trades), Marktkapitalisierung aus `umlaufmenge_cg`, oi_wert. Schwache Assets tragen die Verluste im Gegenwind (2.697). Dazu offen: **Käuferanteil** auf dem Kern (letzter Richtungskandidat). ⛔ **J = SHOWSTOPPER** (Nutzer 30.09.: *keine Schwäche*): **junge Assets**. Das eigene Normal verlangt 12 Monate, junge Assets (12 von 28 der Hebel-Liste) bekommen im ersten Jahr kein Signal. Lösung: Marktnormal, das mit wachsender Historie überblendet wird. Reihenfolge mit A/B zur Abstimmung |
| ⭐⭐ **ENTSCHEIDUNG 30.09. (E-33)** | **REGEL0** festschreiben (Entwurf `REGEL0_Hebel_Entwurf_30_09.md`, zur Prüfung), dann **A** W4 Positionsführung und **B** M1-3 Kern stabilisieren, jeweils gegen REGEL0. **C/D/E derzeit nicht** Teil des Umbaus |
| ⭐ **LAGEBEWERTUNG 30.09.** | `Lagebewertung_30_09.md` zur Abstimmung: Phase 1 steht weitgehend (Kern + Ruhe 48 h, ATR). Die Lücke (~0,18 Pp je Handel) sitzt in **Positionsführung, Regime, Kosten**. Empfehlung **A** W4 Positionsführung → **B** M1-3 Kern stabilisieren, **C** Vorwärtstest monatlich ab Oktober |
| ➤ **nächster Schritt** | **Kern-Short** (W3, E-32: nicht der Betriebs-SHORT, nicht die Absicherung), Schritt 1 abgestimmt, **Wahl 2024: kein Signal über der Nullwelt in keiner Menge** (Stufen streuen 0,015–0,050, bestand 28 Einstiege), K1 Symmetrie s = 0,035 bestätigt: ⛔ **Schritt 1 nicht bestanden (2.696)** (Tagesblock 0/4), aber echte Richtung (Nullwelt und Spiegel 4/4). ⭐ **Ursache der Lücken:** Das rsi-Modell ist in 8 von 20 Monaten fast flach, genau im Gegenwind. M1 Schritt 0 und M1-1 gemessen (Abschnitte 10–11): Die Flachheit ist **teils Schätzer-Kippen** (grobes Dämpfungsraster), **teils echt** (Oktober bis Dezember 2025). ⭐ Der **stetige Informationsgewinn** des rsi-Modells fällt genau im Gegenwind und eignet sich als Regime-Messgerät (Kontext). ◐ **M1-2 Auskunft (2.697)**: In Monaten mit weniger Information verliert der Kern in unverzerrt 3/3 seinen Vorteil (Rohvorteil −0,08..−1,16 % gegen +0,38..+0,59 %), statistisch aber schwach. ⏳ **Teil B Wiedervorlage:** Urteil auf den Monaten ab 2026-09, Regel K_IG < 1 eingefroren; **M1-3** Kern stabilisieren vorgemerkt; nach M1 **Abstimmung und Bewertung der Lage** (Nutzer), danach **W4** Positionsführung (Erfolgsmessung) |

Einzelheiten in den Voranalysen `Voranalyse_L2_Kern_anheben_30_09.md`, `…_L2_N3_Ueberschneidung_…`, `…_L4_Summe_…`,
`…_N4_Simulation_Ruhe48_…` und `…_Richtung_Kern_…` sowie in `python hebel_neubau.py`.

---

### ⭐⭐ STAND 28.09.2026 — wo Phase 1 steht

| | |
|---|---|
| ✔ **Anwendungsebene abgestimmt** | K1–K7 (27.09.), Regelwerk *Stand 28.09.* · Voranalyse `Voranalyse_Kombination_Anwendungsebene_27_09.md` |
| ✔ **Messbasis vervollständigt** | 137 eingestellte Paare plus Terminmarkt nachgeladen (2.668/2.669), `--menge unverzerrt` |
| ✔ **K3 gemessen** | Kontextfläche ohne Feld, Dominanz-Sperren fallen (2.670/2.672) |
| ✔ **K1 Schritt 1 gemessen** | Wirkungskurven je Beitrag (2.671, 2.673, 2.674) und das vorab festgelegte **Randkriterium** mit **Regeltest** (2.675) |
| ✔ **Altersachse gemessen** | gültig, keine Umkehr; der **24 h alte** Wert trägt in Suche, Prüfzeit und 2022; die Tagesperiode ist kein Uhrzeit-Artefakt (2.676, löst 2.675 ab — dessen Altersachsen-Satz war ein Lesefehler). **Kein Blocker**: Alter und A4 werden Gewichte |
| ⛔ **K1 Schritt 2 gemessen** (2.677) | die Kombination als **Kurvenmodell** trägt nicht (T1–T3 in keiner Menge) — die Regel ist sauber (Zufall schweigt), aber die **Auflösung** reicht nicht (+0,16 statt der gesuchten +0,03…+0,06); der Marktmedian steht für die Zeit. Die Wirkung ist da: wo *oben gestreckt*, liegt q ungesehen +0,07…+0,10 über der Schätzung |
| ⛔⭐ **K1 Schritt 2b gemessen** (2.678) | trägt nach dem Vorabkriterium nicht — die Kombination ist schlechter als rsi allein. **Ursache**: wer nach Normal + Beitrag auswählt, wählt das **Phase-Normal**, und das kehrt zur Mitte zurück. Nach dem **Beitrag** allein ausgewählt: q +0,05 über dem Normal in allen vier Mengen, auch rollierend — etwa so viel wie der rsi-Rand allein |
| ✔ **K5 entschieden** (28.09., vorläufig) | Schwelle auf dem **Beitrag** (Vorsprung gegen das eigene Normal) — *trägt auch das nicht, wird neu abgestimmt* |
| ✔ **K7 gemessen** (2.679, 28.09.) | am **echten Bitpanda-Buch** (37 Abschnitte, 7 Liquidationen aus der Gebührensignatur): der **Markpreis** wird Hauptmaß; m = 0,09 liquidiert zu früh, nie zu spät; alle Fehlalarme in Büchern **über 5x**. ⚠️ Der Importer teilt die Positionen falsch ein (Teilschließungen) — eigene Voranalyse, spätestens Phase 2 |
| ⛔◐ **K1 Schritt 2c gemessen** (2.680, 29.09.) | die Auswahl nach dem **Beitrag** ist robust (T6: in jedem Drittel des Normals positiv; jedes Jahr, 80–86 % der Assets) — aber **nicht mehr als rsi allein** (T2) und **nicht kalibriert** (T3, Steigung 0,42–0,55). Nach der Vorabfestlegung: **K5 wird neu vorgelegt** |
| ◐ **K6 gemessen** (2.681, 29.09.) | Spot-Tief **und** Markpreis, je vier Mengen: die **ATR allein** sagt die Liquidationsgefahr voraus, die Risikokurven bringen **nichts** dazu; **5x** vorwärts kalibriert, **3x** nur geordnet, **2x** zu selten. Tabelle liegt vor (Grenze 1 %/72 h: 3x 20–25 %, 2x 75–78 % der Anker, eingetreten unter der Grenze). ⚠️ **H0** (auf der Einstiegsauswahl) und **J10** (10./11.10.) offen |
| ⛔ **K5 neu gemessen** (2.682, 29.09.) | **Tor nicht bestanden — kein Urteil.** In der Kombination bestimmt rsi die Auswahl, eine Wirkung der Lage wird verdeckt (gepflanzte +0,04 kommen als +0,004 an). Die Lage muss **zuerst für sich** gemessen werden |
| ◐ **K5-Folge gemessen** (2.683, 29.09.) | **rsi allein zeitstabil** (jedes Jahr, auch 2022) und **roh fast kalibriert**; das Phase-Normal ist größtenteils Rauschen, die **Schrumpfung** behebt die Rückkehr zur Mitte; die Lage hat einzeln klare Kurven, in der Kombination kommt nichts an (Tor ⛔) |
| ◐ **Gegenprüfung** (2.684, 29.09.) | rsi hält gegen das **geschrumpfte** Normal (Verzerrungsanteil ~0), 2024 schwach; rsi misst die **laufende** Bewegung (RSI der letzten 14 h) — Fortsetzung, kein OPTIMUM |
| ✔ **Rollen geprüft und im Standblatt** (29.09.) | das Schema vom 25.09. hält: **A** Richtung entscheidet **OB** (vorher = OPTIMUM, nur Kandidaten; während = Fortsetzung mit rsi, eigener Einstiegstyp) · **B** Bewegungserwartung **WIE WEIT** (robust, 2.655/2.662) · **C** Risikosperre mit der ATR **WIE VIEL HEBEL** — keine Summe, kein Blocker (`Einordnung_Beitraege_29_09.md`) |
| ◐ **Losfahren aus dem Stand gemessen** (2.685, 29.09.) | **kein Sweet Spot beim Anfahren** nachweisbar: die rsi-Auswahl trägt in **jeder** Phase (jedes Jahr, 77–86 % der Assets), absolut am meisten in der Fahrt; ein Anfahr-Vorteil ≥ +0,08 ausgeschlossen, kleinere nicht auflösbar (Leiter: Auflösung +0,08). Die Tachonadel ist selbst Fortsetzung → **kein Gewicht**; ob in die Mail: **offen** (Nutzer: *abstrakte Zahl, schon zu viel Information*). funding auf stehenden Ankern über dem Band, aber unter der Auflösung und vor allem Markt → Kontext |
| ◐ **K6 S Stufe 1** (29.09.) | die Signalstärke erreicht die Weiter-Schwelle nur auf der Kante (+0,0408), nur 2025, nicht monoton — keine Vollmessung; R2 (Lage-Extreme) zurückgestellt |
| ⛔◐ **Wetter gemessen** (2.686, 29.09.) | Begriffe **Beitrag · Kontext · Gewicht · Sperre** abgestimmt (Regelwerk). Das Wetter (BTC 30 Tage) als Gewicht auf rsi ist ab 2024 **nicht nachweisbar** (+0,029 in der Betriebsform, Nullwelt P90 +0,112, wenige Wetterlagen) — nach der Abbruchregel die letzte Wettermessung. ✔ rsi trägt in **jedem** Wetter und Jahr |
| ◐⭐ **K5 Wahl 2024** (2.687, 29.09.) | der **Zustand** (rsi oben) ist als Zahl **nicht kalibriert** und ordnet 2024 nicht — keine Schwelle darauf. Der **Ersteintritt** (erstes Überschreiten, Einstieg 1 h später) trägt **+0,076..+0,093**, weit jenseits der Nullwelt (Nutzereinwand *nicht aufs fahrende Auto aufspringen*) — **Kandidat**, nur 2024 |
| ⛔ **Korrektur (29.09., Nutzer)** | die **Schwelle** gehört ans **Ende von Bewertung 1** — auf die **Summe** der Chance-Beiträge (Regelwerk § 1/§ 4, E-4), nicht auf rsi allein. K5 ist **zurückgestellt**, bis die Summe steht. Aus 2.687 bleibt ein **Messform**-Befund für den rsi-Beitrag (Zustand nicht kalibriert, Ersteintritt trägt). Prüftakt und Cooldown sind **Phase 2** |
| ✔⚠ **KERN Schritt 1 bestanden** (2.688, 29.09.) | der Ersteintritt (s = +0,035, per Regel auf 2024 gewählt) trägt **einmal bestätigt 2025–26 in 4 von 4 Mengen** (+0,059..+0,076, B1–B6). ⚠️ Nicht besser als der Zustand; stark **regimeabhängig** (2025 klein, Juli–Dezember 2025 negativ) |
| ✔⚠ **KERN Schritt 2 H0** (2.689, 29.09.) | die ATR-Tabelle unterschätzt das Risiko der Einstiege **nirgends** (5x: 12 h 0,40–0,45, 24 h 0,48–0,59, 72 h 0,76–0,81 beobachtet/geschätzt) — **vorsichtig, kein Aufschlag**; 2x nur Black Swan. ⚠️ Der Kern ist ein **Tageshandel**: +5 % im Median nach 19–20 h |
| ⛔✔ **KERN Schritt 3 Simulation** (2.690, 29.09.) | Wahl 2024: 24 h, ohne Ziel, Grenze 2 % (Konto ×1,24). **Bestätigung 2025–26: das Hebelkonto verliert in 4 von 4 Mengen** (×0,26–×0,62), Spot um null — das **Signal schlägt den Zufall** klar, aber der **Rohvorteil je Handel (+0,12..+0,33 %) liegt unter den Bitpanda-Kosten eines Tageshandels (0,48 %)**; Kostenbasis am echten Buch geprüft |
| ⭐ **LÖSUNGSWEG zum Ziel** (30.09., Vorschlag zur Abstimmung) | W1 **L2** den Kern anheben (jetzt) · W2 **Potential** als zweite Zielgröße · W3 **Short-Kern** gegen das Regime · W4 **Positionsführung** mit nachgezogenem Stop (Phase 5) · W5 **Datenquellen** für *A vorher* · W6 L3/L1 später — Einzelheiten `Voranalyse_L2_Kern_anheben_30_09.md` Abschnitt 10 |
| ⭐ **OPTIMIERUNGSLOOP** (Nutzer 30.09.) | ⚠️ Hinweis 30.09. (kein Auftrag): Die Hebungen gehen in Richtung der **Lage kurz vorher**. Früher verworfene Beiträge und Gewichte werden in Lösungsansätzen und Messungen **nicht ausgeschlossen**, auf dem Kern sind sie neu messbar (Regelwerk-Zeile *Lage kurz vorher*). *das Optimierungsthema werden wir über mehrere Ebenen ausreizen* — je Ebene (Regelparameter · Beiträge auf dem Kern · Summe · Positionsführung) dasselbe Verfahren: **Wahl auf 2024**, **einmalige** Bestätigung 2025–26, später die neuen Monate ab 2026-09. Erste Ebene: **N2 Ruhe davor** (L2 Abschnitt 13). ✔ L2 bestätigt (2.691): Stärke ordnet nicht (Schalter); **48 h Ruhe** davor 3/4; **ema_abstand_atr** und **volumenschub** oben heben das **Potential** ATR-frei (4/4, 3/4); vola_kausal ist die ATR (G-ATR). ➤ N3 Überschneidung, dann Summe L4, N4 Simulation |
| ➤ **nächster Schritt (30.09. vormittags)** | ✔ L2 bestätigt (2.691, Voranalyse L2 Abschnitt 15) — ✔ **N3 abgestimmt** (P1–P5, `Voranalyse_L2_N3_Ueberschneidung_30_09.md` Abschnitt 8), ✔ **N3 bestätigt (2.692)**: die Form per Regel **ema_abstand_atr + Ruhe 48 h** trägt (3/4, 4/4); volumenschub 2025–26 in 4/4 eigen → **Vergleichsarm**; *beide oben* Potential +0,22 ATR (Kern +0,06), **nicht** die Chance. ✔ **L4 abgestimmt** (Q1–Q5, E-28; dazu L4-5 **Spiegel** als Urteil vor der Rechnung), ⛔ **L4 bestätigt NICHT (2.693)**: der **Spiegel fällt** 4/4 — die Wucht wählt größere Bewegungen in beide Richtungen (2025 nach unten, 2026 nach oben), keine bessere Richtung; Rolle B gehört in Positionsführung/Hebelstufe; E-28 greift nicht. Es trägt **Kern + Ruhe 48 h**. ⛔◐ **N4 (2.694)**: Der Hebel verliert weiter in 3/4 (unverzerrt ×0,63..×0,68, vorher ×0,26..×0,34). Der **Rohvorteil je Handel verdoppelt sich** (+0,29..+0,31 %), die Lücke zu 0,48 % halbiert sich. Die Wucht bringt mehr Hoch, aber weniger Rohvorteil (W4). ✔ **Voranalyse RICHTUNG abgestimmt** (`Voranalyse_Richtung_Kern_30_09.md`, P1–P4: rsi-Tempo, Tiefe davor, Ruhe 72 h, top_konten_verh unten; Chance mit Pflicht-Spiegel; ⛔◐ **bestätigt NICHT (2.695)**: kein neuer Richtungsbeitrag; **Ruhe 72 h** mit gleichem **Regimemuster** (2025 +0,05..+0,07, 2026 negativ), Tiefe davor in unverzerrt wegen der v̂-Skala nicht auswertbar; ➤ zur Abstimmung **Kern-Short**), danach **Kern-Short** (W3, **nicht** der Betriebs-SHORT und **nicht** die Absicherung), daneben W4 — Überschneidung ema_abstand/volumenschub/Ruhe 48 h, dann **Summe (L4)**, **N4** Simulation als Erfolgsmessung |
| ⭐ **ZWISCHENFAZIT 30.09. mittags** (Nutzer: *wo stehen wir, ist der Weg der richtige?*) | **Stand:** Der Kern trägt ungesehen, ist aber klein und verliert an den Kosten (2.688/2.690). L2/N3 haben das **Potential je Einstieg** gehoben: Ruhe 48 h, ema und volumenschub; *beide oben* etwa das Vierfache (2.691/2.692). Das Risiko bleibt bei der ATR, ein Artefakt wurde erkannt und aussortiert (vola_kausal). **Nicht erreicht:** die **Chance** steigt nicht, die **Wirtschaftlichkeit** ist ungeprüft (N4), *A vorher* (früher Einstieg) fehlt. **Urteil des Experten:** Der Weg ist richtig, mit drei Korrekturen: (1) das **Potential** als Zielgröße der Summe ausdrücklich machen (L4 Q1), (2) ein **Vorwärtstest** auf den Monaten ab 2026-09 als fester Teil des Optimierungsloops, weil 2025–26 mit jeder Ebene weiter *verbraucht* wird, (3) W4 (Gewinner laufen lassen) und W5 (Quellen für *vorher*) nicht aus dem Blick verlieren, denn größere Bewegungen belohnen eine gute Positionsführung |
| ⭐ **H-SCHALTER** (Nutzer 30.09., **nach Kern heben / nach L4**) | ✔ Nutzer 30.09.: *„dein Hinweis zur Stärke ist wichtig — als **optionale Prüfung**, wie weit die **Richtung** noch optimiert werden kann“*, also Rolle A (rsi) weiter ausreizen. *der Kern ist ein Schalter* (2.691 A1) war **nicht Absicht** — noch einmal als **Hypothesenfrage** gegenprüfen und Vor-/Nachteile bewerten. Gemessen ist nur die Stärke **in der Übertrittsstunde** (80 % der Einstiege zwischen +0,035 und +0,044, kaum Streuung → zum Teil Folge der Einstiegsform). Hypothese: die **Summe** liefert die Abstufung; Gegenhypothese: eine andere rsi-Stärkeform ordnet (Anstieg des Vorsprungs, Abstand nach 1–3 h, Zustandsdauer). Einzelheiten `Voranalyse_L2_N3_Ueberschneidung_30_09.md` Abschnitt 7 |
| (vorher 30.09. früh) | **L2 zuerst** (Nutzer): stärkere Signale **neutral** messen — höheres Potential je Handel, **ohne** Kosten in der Auswahl; die Wirtschaftlichkeit zeigt danach die Simulation (Erfolgsmessung). Dann L4 (Summe), L3 (Haltedauer ohne Hebel); **L1 (Börse) erst Phase 4/5** — die Bewertung bleibt neutral |
| ⏸ *nach dem Kern* | Bewertung 1 als **Summe aller Beiträge** fertig machen: die Lage-Beiträge (funding, konten_verh, oi_aenderung, ema_abstand selbstbezogen) **mit einer Messform, die sie auflöst**, neben rsi in die Summe — dann erst die Schwelle auf der Summe · Bewertung 2 als Summe der Risiko-Beiträge (ATR + Lage-Extreme) |
| ⏸ *überholt* | **K5 neu abstimmen** (Nutzer) — mit der einfacheren Regel *rsi allein* zur Bestätigung und der OPTIMUM-Frage (rsi misst die Bewegung) · **K6** mit dem Markpreis auswerten (danach H0: auf der Einstiegsauswahl) · dann **Simulation Ebene 3** |

Die Reihenfolge im Einzelnen steht unter *Was Phase 1 noch verlangt*, Zeile 2.

---

### ⚠️⚠️ Der Faktenteil kommt aus Code — hier steht die Planung

```bash
python hebel_neubau.py
```

**Nutzerkritik 27.09.:** *„wir haben einen Hauptplan — wenn du wieder
etwas Neues parallel machst, bringt das nichts."*

| | |
|---|---|
| **Dieses Blatt** | die **Phasen**, die Reihenfolge, die Entscheidungen — die oberste Liste |
| `hebel_neubau.stand()` | der **Faktenteil**: welche Rolle steht wo, auf welcher Geometrie, mit welchem Befund |

⚠️ Und damit sie nicht auseinanderlaufen, **liest** `stand()` die Phasen
aus *diesem* Blatt, statt sie zu kopieren. Ändert sich hier das Format,
bricht es ab — es gibt keinen stillen Rückfall auf eine zweite Liste.

⛔ **Wozu das gebaut wurde:** Auf die Frage *„zeige mir den aktuellen
Hebel-Einstieg"* habe ich `agent/betraege.py` vorgelegt — Kelly,
Basisrate, `funding_fuenftel`. Also den **alten Spot-Ablauf** als
Ist-Stand des Hebels. Der Riegel dagegen (`pruefe_quellen`) stand seit
dem Vortag da und griff nicht: er bewacht **Messskripte**, ein Bericht ist
keines. Jetzt kommt der Bericht aus Code, der den Spot-Arm nicht kennt —
nachgewiesen am **Seiteneffekt** (`python hebel_neubau.py --nachweis`).

---

# Die fünf Phasen

| # | Phase | Nutzervorgabe |
|---|---|---|
| **1** | **Grundlage** | *„Messen und die Bewertungen und die fachliche und technische Grundlage zu schaffen — muss sauber über **alle Beiträge** funktionieren (hier sind wir noch immer, Binance, CoinGecko, oder andere Quelle?). Kalibrieren der Hebel, etc."* |
| **2** | **Prüfung an Echtdaten** | *„Prüfung der Messungen anhand von Echtdaten (alle) und **aktuellen Hebelpositionen (Portfolio)** und funktioniert das System am Papier mit historischen Daten (nur Desktop) auf Herz und Nieren — oder müssen wir nachjustieren, da zu wenig oder zu viele Signale entstehen (jetzt kommt **Prüftakt und Cooldown** ins Spiel)"* |
| **3** | **Ablaufkette** | *„Wenn die Basis und das System funktioniert: Hebel über die **gesamte Ablaufkette** prüfen und die **LLM-Bewertung** anpassen, wo erforderlich"* |
| **4** | **Produktion** | *„finaler Umbau und in Produktion für **Einstieg und Hebelbewertung**"* |
| **5** | **Ausbau** | *„nachgelagerte Punkte — Krypto und Hebel final ausbauen mit **Hebelpositionsführung** (Trailing?) und **Ausstieg**"* |

**Wir sind in Phase 1.**

---

# ⛔ Die Trennung, an der ich gescheitert bin

> **Nutzervorgabe 27.09.:** *„DIE BEWERTUNG MUSS NEUTRAL OHNE ERTRAG
> erfolgen — der Ertrag oder Positionsgröße ist NACH der Bewertung
> relevant. Zum Zeitpunkt der Beitragsprüfung ist DAS RISIKO und somit der
> HEBEL zu bewerten. Halte deine Messungen zur Erfolgsmessung mit den
> Betriebsbedingungen auseinander."*

| Ebene | Frage | darf verwenden | darf **nicht** |
|---|---|---|---|
| **A · Bewertung** | Ist diese Lage gut? Welcher Hebel ist bei diesem **Risiko** vertretbar? | Kurs, EMA, ATR, Stopabstand, Zielabstand, RM-11 — alles zum **Entscheidungszeitpunkt** bekannt | ⛔ Ertrag, `q`, CRV aus Ergebnissen, Kelly, Positionsgröße, Kapazität |
| **B · Erfolgsmessung** | Trägt diese Regel? | Erträge, Nullwelt, Weglassprobe, Zeitstabilität | ⛔ zurückfließen in A |
| **C · Betriebsbedingungen** | Was kommt von den Signalen an? | Kapazität, Symbolsperre, Prüftakt, Cooldown, Kontingent, Datenlage | ⛔ als Qualitätsurteil gelesen werden |

⚠️ **Mein Fehler:** Ich habe die **Schwelle** — eine A-Größe — als
**Kelly-Nullstelle** bestimmt. Kelly kommt aus `q` und CRV, also aus
**Erträgen**. Und dann habe ich C (Kapazität, Positionsgröße) in dieselbe
Tabelle gelegt und daraus über A geurteilt.

---

# Der Stand — Befund für Befund, nach Ebenen sortiert

## ✔ Gültig — Ebene B (Erfolgsmessung)

| Befund | |
|---|---|
| **2.606** | EMA-Länge **48 Stunden** ist gemessen; der klassische 50-Tage-EMA ist wertlos (MFE/MAE 1,00) |
| **2.625/2.626** | Die Achse ist **invers** und trägt — 12 von 12 out-of-sample, 115 von 115 Symbolen |
| **2.628** | Geometrie **H24 / Stop 1,00 ATR / Trailing 1,5 / 0,5** |
| **2.629** | Die Kalibriergrenze ergibt sich aus den Kosten; Stop 1,00 ist auch netto optimal |
| **2.633** | Die **Auswahl** trägt 5 von 5 Jahren und in jeder Weglassprobe. ⛔ Die **Stufung** 5/4/3/2 trägt nicht — sie hing an 2025 |
| **2.635** | Auf **Tagesbasis** trägt die Achse **nicht** — keine der sechs EMA-Längen, keine Teillösung |
| **2.636** | Stundendaten machbar: **7-Tage-Fenster** reicht (100 % gleiche Auswahl), Binance am NB erreichbar, Verzögerung bis **6 Stunden** trägt noch |
| **2.637** | **Skalenfaktor 2,0832** für Quellen ohne High/Low — je Symbol (2,6 % Streuung) und über 5 Jahre stabil |

## ✔ Gültig — Ebene C (Betriebsbedingungen)

| Befund | |
|---|---|
| **2.634** | ⛔ **Der Hebel kann heute gar nicht entstehen**: kein Beitrag gilt für `instrument="hebel"`, Kelly im Code ist exakt **0,0**. Das ist der Ist-Zustand, kein Urteil |
| **2.638** | Der Betrieb kauft nur **Streckenanfänge** (29,1 % der Anker). Die **Trennschärfe bleibt** (+2,78 gegen +2,83), der absolute Ertrag fällt |
| **2.623** | **Z-2** (`crv_minimum` 2,0) ist tautologisch und gehört entfernt |
| **2.621** | Längste **Verlustserie 198–199** über alle Stopweiten — nicht wegkalibrierbar |
| *aus 2.640* | ⚠️ Ohne High/Low zerfällt die Reihe in **mehr, kürzere Strecken** (2,32 gegen 2,92 Anker) und feuert **2,29×** so oft. Mengenfrage, keine Ordnungsfrage |

## ⛔ Zurückzuziehen — Ebene A aus Ertrag abgeleitet

| Befund | warum |
|---|---|
| **2.630** | Hebelkurve und Hebelhöhe aus **Kelly** — war schon durch 2.632/2.633 korrigiert, ich habe den Fehler dann wiederholt |
| **2.632** | Schwelle **−1,2881** als Kelly-Nullstelle |
| **2.640** | Schwellen **−1,65 / −2,20** ebenso. ⚠️ Der **Quellenvergleich** darin bleibt gültig (Ebene C) |
| **2.639** | ⛔ **Doppelt falsch**: Positionsgröße 20–50 % statt der echten 1,2–7,8 % (`r_min` 0,5 %, `r_max` 1,25 %), **und** die Frage gehört gar nicht in die Bewertung |

---

# ⛔⛔⛔ Die Korrektur vom 27.09. abends — ich war im falschen Arm

> **Nutzervorgabe:** *„WIR sind bei einem NEUBAU des Hebels, die alten
> Beiträge sind nicht relevant. NUR HEBEL UMBAU … trenne ALT von NEU,
> sonst killt uns der Umbau."*

## Die drei Rollen — aus dem Neubauplan vom 25.09.

| Rolle | Frage | Testform | Kandidaten | Stand |
|---|---|---|---|---|
| **A Richtung** | geht es aufwärts? Trendumkehr? | monotone Ordnung **plus Spiegelprobe** | `trendstruktur` (mehrere Zeitebenen), `ema_lage`, `ema_steigung`, **`rsi_aenderung`** (tief *und steigend*) | ⛔ **nicht gebaut** |
| **B Bewegungserwartung** | kommt überhaupt etwas? | gegen die **Auflösungsrate**, nicht gegen `q` — B ist richtungslos | `bandenge` (Squeeze) | ⛔ **nicht gebaut** |
| **C Risikosperre** | überdehnt, überhitzt? | **Ausschlusstest** — verbessert das Weglassen des Extrems den Rest? | **`ema_abstand_atr`** | ✔ gemessen (2.642) |

**Anordnung: `A ∧ B ∧ ¬C`** — keine Summe, kein gemeinsames Fünftel.

⚠️⚠️ **Überholt als Anordnung (Stand 28.09.):** E-4 (*„der Hebel ist ein
Beitragssystem und KEIN Blocksystem“*) und K1 (Wirkungskurven, Summe der
Kurven) ersetzen `A ∧ B ∧ ¬C`. Gültig bleibt die **Rollenfrage** je
Merkmal (Richtung, Bewegung, Sperre) — sie steht jetzt in der Rolle
jedes Rands (Einstieg / Sperre, 2.675). ⚠️ Die Tabellen `ROLLEN` und
`KANDIDATEN` in `hebel_neubau.py` führen noch die alte Anordnung und
sind von einer Wache festgehalten — nachzuziehen ist das in einem eigenen
Schritt mit Vorlage, nicht nebenbei.

⭐⭐ **`ema_abstand_atr` ist Rolle C.** Ich habe sie zwei Tage lang als
Einstiegssignal vermessen. 2.642 („Risiko-Filter, kein Ertragsfilter")
ist damit **kein Rückschlag, sondern die Bestätigung ihrer Rolle**.

## ⛔ Dreimal in den Spot-Arm zurückgerutscht

| | |
|---|---|
| **1** | `funding_fuenftel` / `turnover_fuenftel` als „unsere Beiträge" behandelt — beide `instrumente=("spot",)`, auf H20 und `bewegung_r` gemessen |
| **2** | die **Kelly-Nullstelle** als Bewertungsschwelle benutzt — dieselbe Formel, mit der der Spot-Arm seine Quote rechnet |
| **3** | die **Risikosperre** als Einstiegssignal vermessen |

✔ **Der Riegel steht jetzt im Code** (`hebel_neubau.pruefe_quellen`) und
wird vom Suite-Paket **`Hebelneubau`** bewacht (10 Prüfungen).
⛔ **Der produktive Spot-Arm wurde NICHT stillgelegt** — er führt offene
Positionen; das braucht einen eigenen Auftrag.

## Die Abdeckung für den Hebel — gemessen 27.09.

| | Symbole | Anteil |
|---|---|---|
| `asset_hebel_settings` freigegeben | 43 | 100 % |
| mit Stundenkursen (≥ 300 h) | 28 | **65,1 %** |
| ⚠️ **davon liquide** (≥ 100.000 USD/h) | **15** | **34,9 %** |

APT · AVAX · BNB · BTC · ETH · INJ · **KAITO** · LINK · NEAR · ONDO ·
SOL · SUI · TAO · VIRTUAL · XLM — ⚠️ gegenüber 2.611 **KAITO statt
RENDER**, die Grenze ist beweglich. Mit dem Laderfix → 86 %.

⛔ **Korrigiert 27.09. abends (E-8):** hier stand *„`funding` und
`turnover` … Spot-Quellen, hier irrelevant"*. Das war falsch und genau
der Fehler, den 2.651 benennt. Die Spot-**Quellen** sind nicht
irrelevant — sie wurden für H20 optimiert und vermessen; nur ihre
**Anwendung** wird auf den Hebel dimensioniert (kurzer, intensiver
Handel). Tot für den Hebel ist Spot in seiner **heutigen Form** (Code und
Produktion). Beim Betrieb zählt, ob die **Quelle live beschaffbar** ist,
nicht was der heutige Sammler holt — Nutzer: *„der aktuelle Betriebscode
ist veraltet."*

# Was Phase 1 noch verlangt

| # | offen | |
|---|---|---|
| **0** | ✔✔ **1a ERLEDIGT (2.642)** — der Horizont ist kein Eingang, sondern ein **Messfenster**. Gemessen regelfrei in ATR: die Achse ist ein **Risiko-Filter** (d 0,521 auf MAE) und kein Ertragsfilter (d 0,267 auf MFE), stabil in 5 von 5 Jahren. ⛔ *Kurz* trifft nicht zu — die Auswahl braucht 10,5 % **laenger** bis zum Hoechstpunkt. ⭐ Die Bruecke zum Hebel steht damit **ohne Ertrag**: 0,75 statt 1,08 ATR Rueckgang heisst niedrigere Stopwahrscheinlichkeit, also mehr Hebel | *erledigt* |
| **1** | ⭐ **Die Bewertungsebene neu aufsetzen — sie ist NEUTRAL.** Nutzer 27.09.: *„die BEWERTUNG soll, wenn möglich, OHNE auskommen — eine Zeitpunktbewertung, die Lage und das Risiko (Beiträge bestimmen) — ohne Geometrie, ohne Ertrag, das kommt danach. Zum MESSEN und PRÜFEN als Vergleich und Erfolgsrechnung — ja, da sollen Kurs und ggf. Stop, erreichtes Ziel etc. Verwendung finden, nicht in der Bewertung, die ist NEUTRAL."* ⛔ Hier stand bis 27.09. abends *„Chance-Risiko-Verhältnis aus Stop- und Zielabstand"* — das ist Geometrie in der Bewertung und widersprach dem Regelwerk. ➤ Bewertung 1 (Lage) und Bewertung 2 (Risiko) kommen aus den **Beiträgen**; Stop, Ziel und Kurs gehören in Ebene B/C (2.641) | *nächster Schritt* |
| **2** | ⚠️ **„muss sauber über ALLE Beiträge funktionieren"** — ◐ **Teil erledigt:** die registrierten Träger und die Terminmarkt-Merkmale sind auf **Bewertung 1** gemessen — `funding` (mit dem **Vortageswert**, 2.663: die Hälfte des alten Lifts war Vorgriff), `oi_aenderung`, `konten_verh` tragen bei k = 0, **keiner mit Vorlauf**; `turnover` und die übrigen fallen. Die **Höhe** hält den Pflichtablauf (2.662); die Datenfehler aus 2.658 verschieben kein Urteil (2.664). Stand je Merkmal: `python hebel_neubau.py`. ✔ **E2 mit den Richtungsdaten ist gelaufen (2.665):** 4 von 88 halten den Pflichtablauf, 0 von 80 Zufallsauswahlen; nur **funding** ist Lage vorher — und klein; der Käuferanteil begleitet die Bewegung. **Offen, in dieser Reihenfolge (Nutzer 27.09.: *sauber und langsam, bis wir die Grundlagen haben*):** ✔ **Such-/Prüf-Trennung für funding gelaufen (2.666):** funding **hält auf 2022** in derselben Größe (die erste Fassung *dreht* war ein Mitternachtseffekt) und markiert zusätzlich die **Phase** des Assets. ✔ **Höhe in ATR (2.667):** die Prozent-Höhe ist größtenteils die ATR selbst; für die Liquidation ist die ATR zum Einstieg das Risikomaß. ⛔ Den Käuferanteil 2021/22 nachzuladen lohnt nicht: er **begleitet** die Bewegung (2.665), mehr Daten ändern daran nichts. (a) ⭐ **Die ANWENDUNGSEBENE** — bisher ist jeder Beitrag **einzeln** gemessen; die **Kombination** je Asset und Zeitpunkt (Nutzer: *ein Beitrag ist selbst schwach, in Kombination stärker*) ist ungemessen. Voranalyse und Abstimmung vor dem Bau; (b) **Höhe in Prozent und in ATR nebeneinander** — danach die Nutzerentscheidung, welche Einheit Bewertung 2 misst; (c) **Vorlauf** bei H72/H120; (d) **Bewertung 2** für dieselben Träger. ⭐ **STAND 28.09.:** ✔ (a) **abgestimmt** als K1–K7 (27.09.); ✔ (b) entschieden durch **K6**: Bewertung 2 misst die **Liquidationsgefahr in Prozent am Markpreis**, die ATR zum Einstieg ist das Risikomaß (2.667); ✔ die Prüfung von K1–K7 fand die **Überlebensverzerrung** (2.668) → **137 Eingestellte nachgeladen**, Messbasis `--menge unverzerrt` (2.669); ✔ **K3** ohne Feld (2.670), Dominanz-Sperren fallen (2.672); ✔ **K1 Schritt 1**: ema_abstand selbstbezogen trägt als Kurve (2.671), funding/Premium geteilt, Asset-Anteil trägt nicht (2.673), **Randkriterium mit Regeltest** (2.675): rsi/momentum oberer Rand trägt je Asset, funding_markt unten nur in der Suche, *viele Longs je Asset* hält nicht. **Offen, in dieser Reihenfolge:** ✔ (e) die **Altersachse** — gemessen (2.676): gültig, der 24 h alte Wert trägt in jedem Zeitraum, kein Blocker; (f) **K1 Schritt 2** — die Kurven **gemeinsam** schätzen (rsi/momentum/ema_abstand korrelieren, eine Information), Log-Odds, je mit dem aktuellen **und** dem 24 h alten Wert, A4 als abnehmendes Gewicht — ⛔ als Kurvenmodell gemessen und verworfen (2.677: Auflösung zu grob, Markt steht für die Zeit); **neu vorzulegen**: Asset-Beiträge als Ränder, längeres Fenster, Auflösung vorab nachgewiesen; (g) **K6** Hebelstufe aus der Liquidationsgefahr (R, dann R+S); (h) **K7** Markpreis und Abgleich an den echten Positionen (NB-Kopie); (i) **Simulation Ebene 3** — die Regel muss auf ungesehenen Monaten wirken; (j) **Stammsatz** je Asset (S1–S6, vier Symbolwelten ohne Brücke, 2.612) vor jeder Neuaufnahme; (c) Vorlauf bleibt offen. ⭐ **STAND 29.09.:** ✔ (h) **K7** gemessen (2.679, Markpreis Hauptmaß); ⛔◐ (f) der dritte Anlauf **2c** (2.680) löst die Rückkehr zur Mitte, bringt aber nicht mehr als rsi allein und ist nicht kalibriert — **K5 wird neu vorgelegt**; ◐ (g) **K6** mit dem Spot-Tief gelaufen, mit dem Markpreis in Rechnung. ⭐ **STAND 29.09. ABENDS:** ✔ (g) K6 mit dem Markpreis (2.681); Losfahren (2.685), Wetter (2.686) ohne neue Regel; K5 **zurückgestellt** — die Schwelle gehört auf die Summe (E-23); stattdessen der **KERN** Ende zu Ende: ✔ Schritt 1 (2.688, Ersteintritt trägt ungesehen in 4 von 4 Mengen), ✔ Schritt 2 H0 (2.689, ATR-Tabelle vorsichtig, Kern ist ein Tageshandel), ➤ Schritt 3 **Simulation** | teilweise ⭐ **STAND 30.09.:** Auf dem **Kern** sind 14 Kandidaten gemessen (L2 Teil B, N3, L4, Richtung). Es trägt die **Ruhe 48 h** (Regel am Kern). Die Wucht ist Rolle B, keine Richtung (2.693), und die Kurs-Vorgeschichte ist ausgereizt (2.695). Früher verworfene Beiträge bleiben **nicht ausgeschlossen** (Nutzerhinweis 30.09.). Offen: Kern-Short, W4, *A vorher* mit neuer Quelle |
| **3** | **Die Quellenfrage**: Binance (28), CoinGecko (16) — oder eine dritte Quelle? | Nutzerentscheidung |
| **4** | **Den Hebel kalibrieren** — aus dem Risiko, nicht aus der Statistik (2.627) | offen |
| **5** | ✔✔ **ERLEDIGT (2.646)** — der Horizont widersprach sich dreifach, weil `HORIZONT_JE_LAGE` **keine Einheit** führte. Jetzt 24 **Stunden** für den Hebel, 20 **Handelstage** für Spot, Einheit in eigener Tabelle, Wächter in der Suite | *erledigt* |
| **6** | **Stundendaten in den Betrieb** — technische Grundlage, ohne sie trägt nichts (2.635) | geplant, nicht gebaut |

## ⛔ Die Grundlage aus 2.647 — ÜBERHOLT durch 2.656

⛔⛔ **Der Ertrag unten (84×) kam aus der Trailing-Regel, nicht aus der
Lage** (2.656: 2.626/2.631 bitgleich reproduziert, ohne Trailing ist das
untere Ende der Achse kein Einstieg). Gültig bleibt die **Methodik** —
gegen das eigene Symbol messen, 99,1 % blieben übrig, also kein
Asset-Rang — und die **Risikorolle** von `ema_abstand_atr` aus 2.642.
Der Rest dieses Abschnitts ist der Stand vom Vormittag.

**Nutzereinwand:** *„wenn du falsch beginnst, sind die Messungen danach
auch wertlos."* Berechtigt — 2.626 hatte nur **tagestreu** gemessen.

| | |
|---|---|
| **absolut** | W ≤ −1,2881 → **+1,2568 %** gegen Markt +0,0150 % (**84×**), monoton über fünf Schwellen |
| ⭐ **je Asset** | gepoolter Lift +1,2418 Pp, **symbolintern +1,2301 Pp** — **99,1 % bleiben übrig**; 84,7 % der Symbole positiv, Konzentration 17,5 % (gleichverteilt wären 9 %) |

⛔ **Damit ist ausgeschlossen, dass die Achse Symbole statt Lagen
sortiert** — der Verstoß gegen Regel 3, den der gepoolte Vergleich nicht
gezeigt hätte.

⚠️ **Die Prüfliste ist deshalb auf SECHS erweitert** (Nutzervorgabe
27.09.: *„nicht den Markt alleine messen, sondern die Bewertung muss auf
das Asset gehen"*). Werkzeug: `messe_grundlage_je_asset.py`, Wächter:
`pruefe_pakete.py --paket Hebelneubau`.

## Was NICHT in Phase 1 gehört

Positionsgröße · Kapazität · Prüftakt und Cooldown *(Phase 2)* ·
LLM-Bewertung *(Phase 3)* · Positionsführung und Ausstieg *(Phase 5)*

⚠️ Genau diese Punkte habe ich in Phase 1 hineingezogen. Sie stehen hier,
damit das nicht noch einmal passiert.
