# Bauplan — den Hebel gekapselt neu einpflanzen

**24.09.2026.** Nutzerauftrag: *„plane die zukünftige Architektur so, dass
wir flexibel arbeiten können und mit dem aktuellen Code den HEBEL neu
einpflanzen können, gekapselt sauber vom SPOT neu dimensioniert — wenn das
steht, in die Messung und Prüfung, ob wir mit den bestehenden Daten
fachlich und technisch korrekte Hebel erzeugen können."*

> ⛔ **Dieser Plan macht keine Nebenschauplätze auf.** LLM-Wirksamkeit,
> Führung, Akkumulation und Spot stehen im Gesamtplan und bleiben dort.

---

# § 0 Der Kern

**Reihenfolge, Nutzerentscheidung 24.09.: Kapselung → GEOMETRIE → Quote.**

| | |
|---|---|
| **Heute** | der Hebel erbt die Spot-Bewertung, weil `instrumente=()` bei jedem Beitrag „gilt überall" heißt |
| **Kapselung** | die drei Live-Beiträge bekommen `instrumente=("spot",)` → der Hebel hat **keine** Beiträge mehr |
| **Folge** | die Hebelquote ist die **nackte Basisrate**. Ehrlich, messbar, und **kein Betriebsverlust** — es gibt null Hebelsignale |
| **Dann GEOMETRIE** | ⭐ weil die Quote die Lücke **größenordnungsmäßig nicht schließen kann** (§ 0.1) |
| **Quote zuletzt** | nur wenn die Geometrie einen Raum öffnet |

## § 0.1 ⚠️⚠️⚠️ Die Rechnung, die die Reihenfolge erzwingt

Kelly wird null bei `q₀ = 1/(1+CRV)` = **0,3333** (CRV 2).

| | |
|---|---|
| **Gemessen auf H5** (2.570, je vola-Lage) | q = **0,284 … 0,323** |
| **Fehlende Strecke** | **1,03 … 4,93 Prozentpunkte** |
| **Was Beiträge auf H3 liefern** (B0, 2.576) | beste einzeln **+0,21 Pp** · alle positiven **+0,24 Pp** |
| **Verhältnis** | ⛔ **Faktor 4 bis 21 zu wenig** |

> ⛔ **Die Quote kann den Hebel nicht retten — es ist keine Frage der
> Messgenauigkeit, sondern der Größenordnung.**

Selbst ein Beitrag, der **doppelt so stark** ist wie alles je Gemessene,
schließt die Lücke nicht.

➤ **Die Geometrie bewegt den Nullpunkt selbst. Sie ist die einzige
Stellschraube mit der passenden Größenordnung.**

⚠️ **Und der Vorbehalt gehört dazu:** das Barrierensystem hat brutto
Erwartungswert null — wer CRV ändert, verschiebt `q₀` **und** `q`. Der
Ansatzpunkt ist allein die **Abweichung** davon bei begrenztem Horizont:
dort gewinnt die nähere Barriere, und wie stark, hängt an vola und
Haltedauer. Ob dieser Raum trägt, ist **offen**.

---

# § 1 Was „gekapselt" konkret heißt — am Code

## 1.1 Die Kapselung ist halb gebaut und deshalb wirkungslos

`Beitrag` hat vier Achsen, `_gilt()` prüft sie (`wahrscheinlichkeit.py:660`).
**Aber `instrumente` ist bei jedem Beitrag leer — und leer heißt „gilt
überall".**

> ⚠️ **Der Hebel erbt damit automatisch jeden Spot-Beitrag.** Nicht durch
> eine Entscheidung, sondern durch einen Vorgabewert.

## 1.2 Drei Eingriffe, und die Kapselung steht

| | Eingriff | Datei | Wirkung |
|---|---|---|---|
| **K1** | `_hq_quote` mit `instrument="hebel"` rufen | `rollen_lauf.py:2165` | ohne das greift **keine** Instrumentregel (Blocker B aus 2.574) |
| **K2** | `funding`, `turnover`, `schnitt` auf `instrumente=("spot",)` | `wahrscheinlichkeit.py` | der Hebel erbt nichts mehr |
| **K3** | Gleichheitswächter lagerichtig | `rollen_lauf.py:2591` | er vergleicht ab jetzt **zwei Lagen** — heute ein Fehler je Signal |

⚠️ **Die Reihenfolge ist zwingend: K1 vor K2.** Ohne K1 ist `instrument`
dort `spot`, und K2 bliebe wirkungslos — man würde die Kapselung bauen und
sie träfe nie zu.

## 1.3 Was danach im Betrieb passiert — vorher gerechnet, nicht gehofft

| | |
|---|---|
| Hebelquote | = Basisrate `1/(1+CRV)` = 0,3333 |
| Kelly daraus | **exakt null** (2.558: Basisrate ist die Kelly-Nullstelle) |
| Hebelsignale | **null** |
| **Verlust gegenüber heute** | ⭐ **keiner** — es gibt heute schon null (2.485) |

> ✔ **Deshalb ist dieser Schritt ungefährlich: er macht sichtbar, was ohnehin
> der Fall ist.** Der Hebel entsteht heute aus geerbten Spot-Beiträgen —
> also aus einer Bewertung, die für ihn nie gemessen wurde.

⚠️ **Die Spot-Seite bleibt bitgleich.** K2 setzt genau die Lage, auf der
die drei Beiträge gemessen wurden. Nachweis: der Bitgleichheitstest mit
Lagenachse (2.575) — die Spot-Fälle müssen **0 FEHL** zeigen, die
Hebel-Fälle **müssen** sich ändern. Beides wird geprüft.

---

# § 2 Die Architektur — flexibel für alle Lagen, nicht nur den Hebel

Die Kapselung über `instrumente`/`strategien` trägt **jede** Lage. Für
Akkumulation und Spot ist später nichts Neues zu bauen — nur zu füllen:

```
Beitrag(name=..., instrumente=("spot",),  strategien=("einstieg",))
Beitrag(name=..., instrumente=("hebel",), strategien=("einstieg",))
Beitrag(name=..., instrumente=("spot",),  strategien=("akkumulation",))
```

| Was je Lage eigen ist | Stand |
|---|---|
| Zielgröße | ✔ `ZIELGROESSE_JE_LAGE` |
| Horizont | ✔ `HORIZONT_JE_LAGE` (24.09.) |
| Beiträge | ✔ Feld da, **wird mit K2 zum ersten Mal benutzt** |
| Schwelle | ⚠️ heute eine gemeinsame — **je Lage nötig, sobald etwas trägt** |
| Geometrie, Führung | ✔ beim Hebel vorhanden |

➤ **Kein Architekturumbau. Eine vorhandene, nie benutzte Achse wird
eingeschaltet.**

---

# § 3 Die Datenfrage

## 3.0 ⭐⭐ NUTZERAUFLAGE: **Der Hebel darf nicht an fehlenden Stundendaten sterben**

**Und das tut er auch nicht.** Der ganze Plan läuft auf **Tagesdaten**:

| Phase | braucht | vorhanden |
|---|---|---|
| **1 Kapselung** | nichts | ✔ |
| **2 Geometrie** (Horizontachse 2–20) | Tages-OHLC, 534 Symbole, 32.040 Anker | ✔ **vollständig** |
| **3 Quote** | Tages-Merkmale ✔ · stündlicher Terminmarkt ✔ (3,36 Mio) | ✔ |
| **4 Einpflanzen** | nichts | ✔ |

➤ **Es fehlt allein die stündliche ZIELGRÖSSE (Kurse).** Sie ist an genau
**einer** Stelle relevant: ob Ziel und Stop am selben Tag fielen und in
welcher Reihenfolge — und das betrifft **kurze** Horizonte stärker als lange.

⚠️ **Und dieser Vorbehalt wird nicht behauptet, sondern GEZÄHLT** (§ 2.3,
Punkt 4) — **über die ganze Horizontachse**. Damit sagt die Messung selbst,
**ab welchem Horizont Tagesdaten nicht mehr tragen**. Das ist die
belastbare Antwort auf *„brauchen wir Stundenkurse?"* statt einer Schätzung.

⛔ **Solange stirbt hier nichts.** Stündliche Kurse sind eine mögliche
**Verbesserung**, kein Tor. Beschaffbar wären sie von derselben Quelle, die
`betriebsreihen_job` schon täglich nutzt (Binance) — das bleibt eine eigene
Entscheidung und blockiert keine Phase.

## 3.1 Was auf Tagesdaten gemessen ist, und warum es nicht reicht

Auf **Tages**daten ist der Kandidatenraum erschöpft (2.566): drei tragen auf
H20, sieben nicht, vier können nicht je Asset differenzieren. Und **B0**
zeigt: auf H3 und der Menge, die die Kette wirklich sieht, trägt **keiner**.

> ⚠️ **Das gilt für Tagesdaten. Nur dafür.**

## 3.2 ⭐ Was ungenutzt daliegt

`data/terminmarkt_historie.db`, **516 MB**:

| Tabelle | Auflösung | Zeilen | Symbole | Zeitraum |
|---|---|---|---|---|
| **`terminmarkt`** | ⭐ **stündlich** | **3.355.712** | **122** | 2021-12-01 … 2026-09-02 |
| `terminmarkt_tag` | täglich | 119.935 | 100 | dieselbe Spanne |

**Die Bewertung nutzt ausschließlich die untere Zeile.** Faktor **28** an
Auflösung und **22 Symbole** liegen brach.

Je Stunde stehen **sieben** Größen: `oi`, `oi_wert`, `top_konten_verh`,
`top_summe_verh`, `konten_verh`, `taker_verh`, `punkte`.

## 3.3 Warum das für den Hebel und nur für ihn zählt

Ein Hebeltrade hält im Median **0,30 Tage** (2.493). Eine Tageszahl ist für
ihn ein Mittelwert über **mehr als drei Haltedauern**. Für Spot (H20) ist
dieselbe Zahl fein genug.

> **Wir haben den Hebel bisher mit der Auflösung des Spot-Geschäfts
> gemessen.** Das ist derselbe Fehlertyp wie beim Horizont (2.571), nur eine
> Ebene tiefer: nicht das Fenster war falsch, sondern die Körnung.

## 3.4 ⚠️ Die Grenze, die bleibt — und sie ist hart

**Die Zielgröße bleibt täglich.** `price_history_ohlc` hat `date`;
Intraday-Kurse gibt es nirgends (jede Tabelle mit Kursspalte geprüft).

| | |
|---|---|
| **Merkmale** | stündlich ✔ |
| **Zielgröße** | täglich ⛔ |

➤ **Messbar wird die Achse 2 bis 20 Tage, nicht 0,30 Tage** — und H3 ist der Horizont, mit dem
der Betrieb ohnehin rechnet (2.513: Signal entschieden nach Median 4
Kalendertagen, Ziel nach 2, geplanter Zielzeitraum 3,4 Tage). **H3 ist
also nicht der Notbehelf, sondern die Betriebswirklichkeit.** Und bei H3 trägt die Tages-OHLC
eine Annahme: fallen Ziel und Stop am selben Tag, zählt
`barriere_je_reihe` den **Stop** — konservativ, aber ungemessen. Bei H20
fällt das kaum ins Gewicht, bei H3 deutlich mehr. **Das wird ausgewiesen,
nicht behoben.**

⚠️ Stündliche Kurse wären von derselben Quelle beschaffbar, die der
`betriebsreihen_job` schon nutzt (Binance). **Das ist eine eigene
Entscheidung und steht nicht in diesem Plan.**

---

# § 4 Der Ablauf — vier Phasen mit Abbruchbedingung

## ✔✔ Phase 1 — Kapselung **GEBAUT 24.09.** (Befund 2.579)

**Aus drei Eingriffen wurden sieben** — die Kapselung hat einen
Konstruktionsfehler an **fünf** Stationen freigelegt:

| | Stelle | wie gefunden |
|---|---|---|
| **K1** | `_hq_quote` rechnete mit `spot` | Voranalyse |
| **K1b** | `potential.rechne` → `WK.rechne` | Seiteneffekt-Test |
| **K1c** | `Potential.vermessen` | **Suite** |
| **K1d** | `erreichbar_voll` → `_gilt()` | **Suite** |
| **K1e** | `saetze()` hatte **keinen** `instrument`-Parameter (Mail) | **Suite** |
| **K1f** | der **zweite** `rechne`-Aufruf in `saetze()` | **Prüfung T7** |
| **K2/K3** | Beiträge auf `("spot",)` · Wächter lagerichtig | — |

✔ **Abgenommen:** `spot` 0,3452 (5 Mailzeilen, vermessen, 2 Beiträge) ·
`hebel` 0,3333 (nicht vermessen, 0 Beiträge). Bitgleichheitstest **0 von
488 FEHL**, Suite **3.086 Prüfungen, 3 rot** (die drei bekannten).

⚠️⚠️ **Die Lehre:** `merkmale` (31.08.) → `strategie` (02.09.) →
`instrument` (24.09.) ist derselbe Bruch zum dritten Mal. Der Merksatz
dagegen stand im Code und verwies auf ein Prüfpaket, **das es nicht gab**.
Jetzt gebaut — und aus `_gilt()` **abgeleitet**, nicht aufgezählt. Die
vierte Achse (`richtung`) wurde gleich mitgeschlossen.

### Der ursprüngliche Plan lautete:


K1, K2, K3 aus § 1.2, in dieser Reihenfolge.

| Abnahme | |
|---|---|
| Bitgleichheitstest | **Spot 0 FEHL**, Hebel-Fälle verändert |
| Suite | grün bis auf die drei bekannten |
| Betrieb | Hebelsignale weiter null — nachgewiesen, nicht angenommen |

⛔ **Abbruch, wenn sich ein Spot-Fall bewegt.** Dann trifft K2 mehr als
gedacht.

## ⭐ Phase 2 — DIE GEOMETRIE *(Messung — jetzt die eigentliche Frage)*

**Die Frage:** *Gibt es überhaupt eine Geometrie, in der `q` über der
Nullstelle liegt?* Wenn nein, ist gleichgültig, was die Bewertung findet.

### 2.0 ⚠️⚠️⚠️ DER HORIZONT IST EINE ACHSE, KEINE VORGABE

**Nutzerhinweis 24.09.:** *„H3 war nur mein Beispiel — die Messung muss die
optimalen Grenzen ergeben, H3, 5, 10, 20 etc."*

> ⚠️ **Er trifft einen Fehler von mir.** Ich habe H20 kritisiert, *weil es
> gesetzt war* — und dann H3 gesetzt. Beides sind Setzungen.

`HORIZONT_JE_LAGE[("hebel","einstieg")] = 3` ist aus der **beobachteten
Haltedauer** abgeleitet (Median 0,30 Tage, Betrieb rechnet 3,4 Tage). Das
beschreibt den **Ist-Zustand**, nicht das Optimum.

> **Die Frage „bei welcher Haltedauer ist die Geometrie am günstigsten?"
> ist nie gestellt worden.**

➤ **Gemessen wird über die Horizontachse: 2, 3, 5, 10, 20.** Das Ergebnis
kann `HORIZONT_JE_LAGE` ändern — es ist dessen Begründung, nicht dessen
Voraussetzung.

⚠️ **Drei Achsen, und damit ein Suchpreis:** Horizont × Stopweite × CRV.
Die Vorabfestlegung muss die Zahl der Kombinationen nennen und den
Mehrfachtest korrigieren (Poisson gegen die Erwartung, Methodik 2.477),
sonst findet man Rauschen.

⚠️ **Und die Norm darf hier nicht dazwischenfunken:** `warne_horizont`
meldet jede Abweichung von der Lagenvorgabe. Für eine **Geometrie**frage,
die den Horizont *sucht*, ist das Rauschen — `FRAGEARTEN` trennt
`beitrag` von `geometrie` bereits, die Warnung muss dieser Trennung
folgen.

### 2.1 ✔ Was schon gemessen ist — und auf welchem Horizont

| Befund | gemessen auf | fehlt |
|---|---|---|
| **2.435** „Stopweite: Gipfel bei 7–9 %", 534 Symbole, 32.040 Anker, **sechs Weiten gepaart** | **H5, H10, H20** | ⛔ nein |
| **2.435-richtung** „bei SHORT ist die Stopweite egal" | dieselben | ⛔ nein |
| **2.564** „ein globales CRV — die Merkmalslage ändert die Geometrie nicht" | **H20** | ⛔ nein — und *„Lage"* hieß dort **Merkmals**lage, nicht **Halte**dauer |
| **2.544** Kennlinie, steuerndes Fenster 0,0095–0,0150 Quotenpunkte | H20 | ⛔ nein |
| **2.570** Kelly je vola-Lage negativ | **H5** | ⚠️ am nächsten dran |

➤ **Die Geometrie ist gründlich vermessen — aber nie über die
Horizontachse als Frage.** H5/H10/H20 lagen je einzeln vor; **H2 und H3
fehlen ganz**, und niemand hat die Werte gegeneinander gestellt.

⚠️ Das ist keine Doppelarbeit, sondern **R-R11**: dieselbe Frage, diesmal
mit dem Horizont als **gemessener** statt gesetzter Größe.

### 2.2 ✔✔ Die Werkzeuge stehen bereits

| | |
|---|---|
| `messe_stopweite_historisch.py` | ⭐ **kennt `--horizont` schon** (`HORIZONTE = (5, 10, 20)`, überschreibbar). **Keine Änderung nötig.** Sechs Weiten, gepaart je Anker |
| `phase4_crv_je_lage.py` | `horizont=20` fest → **eine Zeile** |
| `phase4_vola_als_geometrie.py` | vorhanden |

⚠️ **Die Menge ist aus der Norm abgeleitet, nicht gewählt:**
`messnorm.FRAGEARTEN` führt für `geometrie` das **Messuniversum** —
*„die Geometrie gilt für jeden Anker, nicht nur für die ausgewählten"*
(2.564). Damit entfällt hier der F-212-Zielkonflikt.

### 2.3 Was gemessen wird

1. **Stopweite über die Horizontachse** (2/3/5/10/20), sechs Weiten
   gepaart, LONG und SHORT getrennt — **wandert der Gipfel mit dem
   Horizont?** Bei H5–H20 lag er bei 7–9 % (2.435); für H2/H3 ist er
   ungemessen.
2. **CRV über die Horizontachse** — 2.564 fand *ein globales* CRV, aber
   auf H20 und über **Merkmals**lagen. Ob es über **Halte**dauern hält,
   ist offen.
3. **Beides je vola-Lage** — N-52 sagt, ruhige Assets lösen *öfter* auf.
   Der Verdacht: die Regel `max(5 % Kurs, 0,75 × ATR)` erzeugt **zwei
   Regime** — bei ruhigen bindet die 5 %-Grenze, bei volatilen der ATR.
   **Auf H3 nie geprüft.**
4. ⚠️ **Der Pfad-Vorbehalt als ZAHL, nicht als Satz:** wie oft fallen Ziel
   und Stop am **selben Tag**? `barriere_je_reihe` zählt dann den Stop
   (konservativ). ⭐ **Über die Horizontachse gemessen sagt diese Zahl
   zugleich, ab welchem Horizont Tagesdaten nicht mehr tragen** — also wo
   die Grenze der vorhandenen Auflösung wirklich liegt, statt sie zu
   schätzen.

### 2.4 Die Entscheidungsregel — vor der Messung

| Ergebnis | |
|---|---|
| **Es gibt eine Geometrie mit `q > q₀`**, Kontrolle sauber | ✔ **Phase 3** — und erst dort ist die Quotenfrage sinnvoll. ⭐ Der gefundene Horizont wird **Vorgabe** in `HORIZONT_JE_LAGE`, mit dieser Messung als Begründung |
| **Kein Raum über die GANZE Achse**, Trennschärfe reicht | ⛔ **Mit Tagesdaten ist auf keinem Horizont von 2 bis 20 ein Hebel möglich.** Das ist dann ein belastbares Ergebnis — und die Frage geht an die **Auflösung** (Stundenkurse) oder an die **Instrumentwahl**, nicht an die Bewertung |
| **Trennschärfe reicht nicht** | ⚠️ Datendecke, nichts entschieden |

## Phase 3 — die Quote *(nur wenn Phase 2 einen Raum findet)*

Dann erst die Kandidaten — und **dann** ist auch der stündliche
Terminmarkt an der Reihe (3,36 Mio Zeilen, 122 Symbole, sieben Größen,
nie in einer Bewertung). `k1c_hebel_barriere.py`, H3, `barriere`, ohne
Fünftel 4, Kontrolle, Saatprobe, R-R11.

⚠️ **Vor dem Bau: Vorabfestlegung**, sonst entsteht ein Suchpreis über
sieben Größen mal Fensterlängen.

## Phase 4 — einpflanzen *(nur bei positivem Phase 3)*

Beitrag mit `instrumente=("hebel",)` · Schwelle je Lage (R-R9) ·
`KALIBRIERT_FUER` · Mail-Prüfstand · Betriebsprüfung am Notebook.

---

# § 5 Was dieser Plan ausdrücklich **nicht** anfasst

| | |
|---|---|
| **Spot** | bleibt bitgleich. Eigener offener Punkt |
| **Akkumulation** | erbt die Architektur später, ohne neuen Bau |
| **LLM** | kein Eingriff. Der Hebel-Prompt bleibt wie er ist, bis Phase 3 etwas ergibt — **ein Prompt für eine Lage ohne Signale wäre Arbeit an einem toten Pfad** |
| **Führung / Ausstieg** | eigenes Thema, eigener Befund (2.392) |
| **Stufe 6 / F-168** | wird in Phase 3 **umgangen**, nicht geändert. Eine Änderung träfe Spot |

---

# § 6 Die ehrliche Erwartung, vor dem Lauf

**Phase 3 kann negativ ausgehen.** Auf Tagesdaten ist der Kandidatenraum
erschöpft, und die stündliche Dynamik ist eine **Hypothese**, kein Befund.

➤ **Was der Plan garantiert, ist nicht ein Hebel, sondern eine belastbare
Antwort auf die Frage, die seit Tagen offen ist:** ob mit den vorhandenen
Daten ein fachlich und technisch korrekter Hebel erzeugbar ist.

⚠️ **Und er macht den Unterschied zu allen bisherigen Versuchen:** diesmal
wird nicht ein Kandidat gegen eine Spot-Infrastruktur gemessen, sondern
eine **gekapselte Hebelbewertung** gegen Daten in der Auflösung, die zu
ihrem Horizont passt.

---

# § 7 ⭐ DIE PHASEN BIS M1 — Hebel End2End

**Nutzerfrage 24.09.:** *„Ziel ist eine funktionierende Strategie ‚Hebel'
über die gesamte Ablaufkette und LLM (anpassen, messen und prüfen),
End2End — ist das noch so?"*

> ✔ **Das Ziel steht unverändert. Aber dieser Plan deckte nur H1–H4 ab.
> H5 bis H9 fehlten — sie stehen jetzt hier.**

## 7.1 Die Kette

| | Phase | Art | hängt ab von |
|---|---|---|---|
| **H1** | **Kapselung** K1 → K2 → K3 | Bau | — |
| **H2** | ⭐ **Geometrie über die Horizontachse** 2/3/5/10/20 × Stopweite × CRV × vola | **Messung — GABELUNG** | H1 |
| *H2a* | *(nur falls H2 leer)* **Auflösung**: stündliche Kurse beschaffen, H2 wiederholen | Daten + Bau | H2 negativ |
| **H3** | **Quote** — Beiträge auf der gefundenen Geometrie, inkl. der 3,36 Mio stündlichen Terminmarktzeilen | Messung | H2 positiv |
| **H4** | **Einpflanzen** — Beitrag `instrumente=("hebel",)`, Schwelle je Lage (R-R9), `KALIBRIERT_FUER` | Bau | H3 positiv |
| **H5** | ⚠️ **Trichter lagerichtig** — Stufe 6 (F-168 auf H20/`bewegung_r`), dazu `anlass` und `auswahl` prüfen | Messung + Bau | H4 |
| **H6** | **Mail** — Hebelsignal erklären, LONG **und** SHORT am Prüfstand | Bau | H4 |
| **H7** | **Betriebsprüfung** — entstehen am Notebook tatsächlich Hebelsignale? | Betrieb | H4+H5+H6 |
| **H8** | **LLM lagerichtig** — eigener Hebel-Prompt, **gepaart gemessen** gegen den heutigen | Messung + Bau | **H7** |
| **H9** | **Wirksamkeit End2End** — M1-Kriterium 7 | Messung | H7+H8 |

## 7.2 ⚠️ Die drei Lücken, die im Plan fehlten — offen benannt

| | |
|---|---|
| **H5 Trichter** | Der Plan sagte *„Stufe 6 wird in Phase 2 umgangen, nicht geändert"*. Das ist für die **Messung** richtig und für den **Betrieb** falsch: F-168 ist auf **H20 und `bewegung_r`** gemessen (Spot-Lage) und greift ohne Instrumentbedingung. Solange sie steht, sperrt sie dem Hebel genau das Fünftel weg, in dem B0 die Trennkraft fand (2.576) |
| **H8 LLM** | Der Plan schloss es aus — richtig **bis H7**, denn ein Prompt für eine Lage ohne Signale wäre Arbeit an einem toten Pfad. **Danach ist er Pflicht**: heute ist `_HANDELN["spot"] is _HANDELN["hebel"]`, das Modell weiß nicht, worüber es urteilt, und sein eigener Docstring warnt davor |
| **H9 Wirksamkeit** | fehlte ganz. ⚠️ **Und sie hat ein eigenes Problem:** es gibt **null historische Hebelsignale**. Wirksamkeit ist damit nur **simuliert** oder am **Papier** messbar — wie das zählt, ist eine Frage an M1, keine Messfrage |

## 7.3 Was an Infrastruktur **schon** steht — und deshalb keine Phase braucht

| | |
|---|---|
| Hebeltopf, Aggregat-Deckel | ✔ `TO.frei_eur(_topf_instrument)`, `hebel_aggregat` |
| Cooldown je Instrument | ✔ `WH.gesperrt_bis(..., instrument, ...)` |
| Handelbarkeit je Klasse | ✔ `_AKL.hebel_handelbar` |
| Geometrie, Liquidation (RM-11) | ✔ `entscheidungsrechnung` |
| Positionsführung, Börsenabgleich | ✔ `hebelfuehrung`, `hebel_abgleich` |

➤ **Die Ausführung ist vollständig. Es fehlt ausschließlich die
Entstehung.**

## 7.4 ⚠️ Das Betriebsrisiko, das erst ab H7 entsteht

Heute gibt es **null** Hebelsignale — deshalb ist bis H6 nichts zu
verlieren. **Ab H7 ändert sich das:** entstehen Signale, wird der
Hebeltopf belegt, und der Nutzer bekommt Empfehlungen, die er ausführen
soll.

⚠️ Dazu gehört 2.489: *„nicht alle Hebel sind für alle Assets verfügbar"*
— die Stufenliste (2/3/5/10) ist eine **Annahme**, welche Stufe ein Asset
wirklich zulässt, weiß die Rechnung nicht. **Vor H7 zu klären, nicht
danach.**

## 7.5 Die Gabelung, ehrlich

> **H2 entscheidet alles.** Findet die Geometrie über die ganze
> Horizontachse keinen Raum mit `q > q₀`, dann sind H3 bis H9 gegenstandslos
> — und die Frage geht an **H2a (Auflösung)** oder an M1 selbst.

⚠️ **Das ist kein Grund, H2 zu verschieben, sondern es vorzuziehen.** Es
ist die billigste Phase (Werkzeuge stehen, Betrieb unberührt) und die mit
dem größten Informationsgewinn.
