# Die Landkarte der Kette — was rechnet, was urteilt, und wo

*Erstellt 12.09.2026 auf Nutzerfrage: „zeige mir den vollständigen Ablauf der
Kette — was wird wo deterministisch berechnet, wie und wo bewerten die
LLM1-Rollen, und wo ist die Gegenprüfung von LLM2 (Z.ai)?"*

⚠️ **Aus dem Code gelesen, nicht aus der Erinnerung.** Die Stufennamen stammen
aus `agent/rollen_gate.py::STUFEN`, die Aufrufstellen aus `agent/rollen_lauf.py`.

---

## Der Ablauf, Stufe für Stufe

Ein Umlauf läuft alle 15 Minuten über fünf Gruppen. Je Gruppe **einmal** Rolle A,
dann je Asset die zwölf Stufen.

| # | Stufe | Wer entscheidet | Kostet einen Modellaufruf? |
|---|---|---|---|
| — | **Rolle A — Marktlage** | **LLM1** | ja, **einmal je Umlauf** |
| 1 | `auftrag` — Instrument und Strategie erlaubt | Rechnung | nein |
| 2 | `fakten` — Faktenlage ausreichend | Rechnung | nein |
| 3 | `lagebild` — Lagebild geliefert | Rechnung (prüft Rolle A) | nein |
| 4 | `anlass` — Faktensatz hat sich geändert | Rechnung | nein |
| 5 | `auswahl` — gehört zu den besten k der Gruppe | Rechnung | nein |
| 6 | `terminmarkt` — OI-Aufbau nicht im obersten Fünftel | Rechnung | nein |
| 7 | `wiederholung` — nicht kürzlich schon gefragt | Rechnung | nein |
| 8 | `urteil` — **Urteil geliefert und vertragskonform** | **LLM1 (Rolle BC)** | **ja, je Asset** |
| 9 | `aktion` — Aktion ist ein Einstieg | Rechnung | nein |
| 10 | `geometrie` — Zonen rechenbar | Rechnung | nein |
| 11 | `risikoschicht` — Töpfe, Cash, Positionsgröße | Rechnung | nein |
| 12 | `entscheider` — Trefferquote schlägt den Breakeven | **Rechnung** | nein |
| — | **Rolle G — Gegenprüfung** | **LLM2 (Z.ai)** | ja, nebenläufig |

**Sieben Stufen liegen vor dem Modell, und das ist Absicht:** Jede von ihnen hat
eine eigene Stufe bekommen, weil sie **keinen Modellaufruf kostet** — `anlass`
(16.08.), `auswahl` (23.08.), `terminmarkt` (02.09.). Wer sie zusammenlegt, kann
hinterher nicht mehr sagen, ob eine Zeitregel, ein identischer Faktensatz oder
ein Rangplatz gebremst hat.

⚠️ **Namensfalle:** Wer im Projekt „Stufe 11" liest, meint den `entscheider` —
das ist seit dem Einschub von `terminmarkt` die zwölfte. Im Code wird deshalb
nur mit Namen gearbeitet, nie mit Nummern.

---

## ⚠️ Der „Entscheider" ist keine LLM-Rolle

Der ursprüngliche Entwurf trennte **Händler** (bewerten) und **Entscheider**
(handeln) als zwei Modellaufrufe. Das ergab rund 162 Aufrufe täglich. Nach dem
Nutzereinwand vom 10.08. wurden beide **in einen Aufruf gelegt** — das ist heute
Rolle BC.

Die Stufe, die heute `entscheider` heißt, ist **deterministisch**: Sie fragt, ob
die gerechnete Trefferquote die Bewertungsschwelle schlägt (`potential.traegt()`,
Schwelle 0,080 R). Kein Modell ist daran beteiligt.

| Begriff | Was heute dahintersteckt |
|---|---|
| Rolle **Markt** | LLM1, Rolle A — einmal je Umlauf, sieht kein einzelnes Asset |
| Rolle **Händler** | LLM1, Rolle BC — Belege, Aktion, Begründung, Gegenargument |
| Rolle **Entscheider** | **kein Modell mehr** — in Rolle BC aufgegangen; die gleichnamige *Stufe* ist gerechnet |
| Rolle **G** | LLM2 (Z.ai) — zweite Quelle, kein Veto |

---

## Was das Modell entscheidet — und was gerechnet wird

**Vom Modell (Rolle BC):** Aktion · Richtung · Begründung · Gegenargument ·
Belege mit Richtung und Gewicht · Zahl unabhängiger Faktoren · Widerlegung
(wodurch, welcher Preis, bis wann) · Einstieg und Stop als **Angabe**.

**Gerechnet, nie vom Modell:** Betrag (aus der Zahl unabhängiger Faktoren,
gedeckelt) · Hebel (`r(q)`, halbes Kelly) · Ziel (CRV 2,0 mechanisch) ·
Stopweite (Rauschboden und Marken) · Trefferquote (gemessene Beiträge) ·
Aggregat-Deckel · Cash und Töpfe · Liquidationsabstand.

**Bewusst nie eingebaut** — jeweils mit Grund:

- **keine Konfidenz in Prozent** — im eigenen System 77,5 % vorhergesagt gegen
  33,3 % eingetreten. Stattdessen die Zahl **unabhängiger Belege**.
- **keine Rechnung durch das Modell** — Tokenisierung zerlegt Zahlen.
- **keine Positionsgröße** — Rolle A durfte das bis 10.08.; Beträge setzt der
  Nutzer, das Risikomanagement ist deterministisch.
- **keine „unklar"-Option.**
- **zwei Z.ai-Aufrufe stillgelegt** — Richtungsabgleich (17× LONG in 2.469
  Prüfungen, dieselben Fakten wie Rolle BC) und Konsistenzprüfung (16.08. vom
  Nutzer abgelehnt).

⚠️ Deshalb stehen in der Oberfläche „Konfidenz –" und „Trigger (-)" leer: Das
sind Felder der alten Kette (Befund 2.390-gui).

---

## Die Gegenprüfung (LLM2, Z.ai)

Sie läuft **nebenläufig in einem eigenen Faden**, nach dem Urteil, mit
**eigenen Fakten**: der Positionierung am Terminmarkt — offene Kontrakte,
Finanzierungsrate als Perzentil, Anteil der Long-Konten, Marktregime mit Dauer.
Nichts davon steht im Faktentext von Rolle BC.

**Sie hat kein Veto.** Ihr Einwand erscheint in der Mail (Abschnitt 5,
„DIE GEGENPRÜFUNG") und im Kopf unter „Was dagegen spricht" — er verändert
weder Aktion noch Betrag noch Hebel. Fällt sie aus, läuft die Kette weiter
(P-8, fail-soft); im Log steht dann „Z.ai-Rolle G fehlgeschlagen".

**Sie wird nur gefragt, wo es eine eigene Grundlage gibt** (G5): Zu einem Wert
ohne symbolspezifische Terminmarktdaten wird nicht gefragt.

---

## Die vier Wächter um das Modell — alle deterministisch

| Wächter | Was er prüft |
|---|---|
| `empfehlung_vertrag` | Pflichtfelder, Richtungspflicht, Ablehnung sich selbst zurückziehender Begründungen, Rückstufung auf NICHTS_TUN ohne unabhängigen Faktor |
| **Z1** `gegenpruefer_rollen` | **Treue zur Eingabe**: Zahlendeckung, Richtungstreue, Zuspitzung, Leerlauf. Fragt *nicht*, ob das Urteil klug ist |
| `mindestkriterien` | ohne ausreichende Grundlage wird gar nicht erst gefragt (BC3, G5) |
| `anlass` + `wiederholung` | wie oft überhaupt gefragt wird |

⚠️ **Z1 und Z.ai werden leicht verwechselt** — deshalb heißt das Modul
`zweite_meinung`: Z1 ist deterministisch und prüft die Treue, Z.ai ist ein
zweites Modell und prüft die Sache.

---

## ⚠️⚠️ Die Lücke: der Beitrag der Modelle ist unbelegt

Die Trefferquote in der Mail stammt aus **gemessenen Beiträgen**, nicht aus dem
Modell. Das Modellurteil steht **daneben** und geht in keine Zahl ein.

**Ob das Urteil der Modelle den Zufall schlägt, ist für diese Kette nie gemessen
worden.** Für die *alte* Kette gibt es `messe_allocator_gegen_zufall.py`. Für die
neue gibt es die Durchlässigkeit des Trichters (wo verliert die Kette) — aber
keine Aussage darüber, ob ein KAUFEN des Modells besser ausgeht als ein Zufall
auf derselben Menge.

Das ist die stehende Nutzervorgabe *„das LLM muss den Zufall schlagen, und das
muss messbar sein"* — offen, und Gegenstand von **Schritt 42**.

---

## Gemessen: wo die Kette wirklich verliert (7 Tage, 12.09.2026)

3.345 Läufe, 39.471 Asset-Zellen hinein, 202 heraus. Aus
`gate_durchlaessigkeit` der Notebook-Sicherung:

| Stufe | bestanden | verloren | wer entscheidet |
|---|---|---|---|
| auftrag | 39.471 | 0 | Rechnung |
| fakten | 38.802 | 669 | Rechnung |
| lagebild | 38.802 | **0** | Rechnung (Rolle A blockiert nichts) |
| anlass | 26.797 | 12.005 | Rechnung |
| auswahl | 16.242 | 10.555 | Rechnung |
| terminmarkt | 16.242 | 0 | Rechnung |
| wiederholung | 2.055 | 14.187 | Rechnung |
| **urteil** | 2.046 | **9** | Vertrag verwirft die Antwort (8× ungültig, 1× Netz) |
| **aktion** | 1.799 | **247** | davon **56 vom Modell** („NICHTS_TUN"), 166 „Ausstieg steht auf SCHLIESSEN", 25 „vollständig gestakt" |
| geometrie | 1.366 | 346 | Rechnung (taktische Zelle ohne Hebel) |
| risikoschicht | 1.366 | 0 | Rechnung |
| **entscheider** | **115** | **1.251** | **Rechnung** — Potential unter der Schwelle |

**Der härteste Filter ist gerechnet, nicht geurteilt:** Die Entscheiderstufe
verwirft **92 %** dessen, was sie erreicht. Das Modell verwirft 56 Zellen in
sieben Tagen — **2,7 %** der 2.046, die es beurteilt hat.

---

## ⚠️⚠️ Vorgabe und Ist: „Entscheidungshilfe, nichts blockieren oder ändern"

*Nutzerhinweis 12.09.2026.* Gemessen am heutigen Code gilt das **für zwei der
drei Stellen**:

| | blockiert? | ändert Zahlen? |
|---|---|---|
| **Rolle A (Markt)** | nein — 0 Verluste an `lagebild` | nein |
| **Z.ai (Gegenprüfung)** | nein — kein Veto, nur Text in der Mail | nein |
| **Rolle BC (Händler)** | **ja** — 56 Zellen in 7 Tagen über „NICHTS_TUN" | **ja** — siehe unten |

**Wo Rolle BC die Zahlen verändert:** Ihr **Widerlegungspreis** geht in die
Stopweite ein (`rechne(umgeworfen_preis_eur=…)`), und über den Stop hängen
Betrag, Hebel und Ziel daran. Die Mail sagt es selbst: *„Zone und Stop teils aus
einer Modellangabe."* In der SOL-Mail stammt der Stop 80,26 EUR aus dieser
Angabe — daraus folgen 8,9 % Stopabstand, 3,9x Hebel und 174 EUR Risiko.

➔ **Damit steht eine Entscheidung an** (Befund 2.391-hilfe): Soll das Modell
weiterhin eine Empfehlung verhindern dürfen, und soll seine Preisangabe die
Geometrie bestimmen? Beides ist heute so gebaut, beides widerspricht der
Vorgabe „Entscheidungshilfe".
