# Konzept — die Einstiegsbewertung: Vorfilter, Kette, nachgelagerter Filter

*Nutzerfrage 23.08.: „wie stellst du dir den Gesamtplan und die Funktionalität
der Einstiegsbewertung vor — bleiben wir bei einem reinen Vorfilter, oder ist
ein nachgelagerter Filter erforderlich, der die gesamte Entscheidungskette
bewerten kann? Nach Möglichkeit soll er die Vorarbeit fortsetzen und keine
neuen Baustellen aufmachen."*

> **Alles hier ist gemessen oder am Code gelesen.** Was ich vorschlage, steht
> als Vorschlag da; was gemessen ist, mit seiner Zahl.

---

## 0. Die kurze Antwort

| | |
|---|---|
| **Brauchen wir einen nachgelagerten Filter?** | **Ja** — und **er ist gebaut**: `wahrscheinlichkeit.py` |
| **Warum reicht ein Vorfilter nicht?** | Vor der Kette weiß niemand, was das Modell sagen wird. Ihre eigene Vorgabe — *„jede Entscheidung braucht eine Begründung"* — ist **nur nach der Kette** prüfbar |
| **Neue Baustelle?** | **Eine**, und das Konzept verlangt sie: **Z1s Urteil wird nirgends je Signal gespeichert** |
| **Was fehlt sonst?** | keine Bauteile — **Belege**. 46–66 aufgelöste Fälle sind die Obergrenze jeder Aussage |

---

## 1. Zuerst: NICHTS_TUN braucht Gründe, und die drei sind verschieden

**Ihre Beispiele, sortiert:**

| | Fall | woran erkennbar |
|---|---|---|
| **N1** | **Bestand vorhanden** → halten oder verkaufen ist die Frage, nicht kaufen | `holdings` / `hebel_positions` |
| **N2** | **Nichts hat sich geändert** — die vorige Empfehlung gilt weiter | ⚠️ **`anlass_beobachtung` — existiert, 45.479 Zeilen** |
| **N3** | **Unklare Indikatorenlage** → besser abwarten | offen, siehe 1.2 |

### 1.1 N2 ist bereits gebaut — und ist die belastbarste Zahl der Kette

`anlass.fingerabdruecke()` hasht **den fertigen Faktentext**, nicht die
Rohdaten:

> *„Wer den Kurs hashen würde, bekäme bei jedem Tick einen neuen Abdruck; der
> Text sagt ‚1.093 EUR wert' und ändert sich erst, wenn es der Leser merkt."*

**Gemessen: 45.479 Beobachtungen, davon 13.898 mit „hätte gesperrt" (31 %).**
Das ist genau Ihr N2 — *„es hat sich seit der letzten Empfehlung nichts
geändert"* —, und es ist die einzige Stufe der Kette mit Masse.

⚠️ **Schwäche, gemessen:** ein Hash ist alles oder nichts. Ändert sich
irgendeine Zahl in irgendeinem Block, gilt das Signal als neu. Deshalb nur
31 %. **`bloeckeabdruecke()` und `geaenderte_bloecke` liegen seit dem 16.08.
bereit** — die blockweise Auswertung ist vorbereitet und nicht benutzt.

### 1.2 ⚠️ N3 ist der gefährliche Fall — und das Projekt hat es schon einmal bezahlt

**Der Fachstandard** für „ich weiß es nicht" ist die **Abstention** (reject
option, Chow): ein Verfahren darf sich enthalten, wenn seine Sicherheit unter
einer Schwelle liegt.

⚠️ **Das Projekt hat genau das schon einmal versucht** (Fakten-Entscheidungs­-
mappe):

> *„Ein Mehrdeutigkeits-Label wäre strukturell eine ‚Unknown'-Option — die
> löst laut Literatur Abstention aus, und **genau dieser Mechanismus drückte
> hier die ERÖFFNEN-Quote von 93 % auf 3 %**."*

**Daraus folgt eine Bauregel, kein Verbot:**

> **Der Grund „unklare Lage" darf dem Modell nicht als Wahlmöglichkeit
> angeboten werden — er muss nach der Antwort deterministisch abgeleitet
> werden.**

Das ist genau die Aufgabe eines **nachgelagerten** Filters, und es ist das
erste Argument dafür, dass ein Vorfilter allein nicht reicht.

### 1.3 Was heute stattdessen passiert

| | |
|---|---|
| `facts_json` bei HALTEN / REDUZIEREN / VERKAUFEN | **17 Zeichen** — `{"asset": "IO"}` |
| Z.ai-Zweitmeinung auf der Verkaufsseite | **0 von 561** |
| Merkmalsfamilien bei REDUZIEREN | **10 von 75** |

**561 Nichthandlungen ohne nachvollziehbare Begründung.** Nach Ihrem
Grundsatz ist das der Kern des Problems, nicht ein Nebenschauplatz.

---

## 2. Vorfilter oder nachgelagerter Filter? — Beide, und beide existieren

### 2.1 Die drei Stellen, an denen bewertet werden kann

| Stelle | Modul | Zustand | was sie kann |
|---|---|---|---|
| **vor** der Kette | `vorfilter.py` (H) | ✔ gebaut, **Schatten** | Geometrie: Weg frei, Stop gedeckt |
| **in** der Kette | `rollen_gate` / `trichter` | ✔ läuft | Durchlässigkeit je Stufe |
| **nach** der Kette | **`wahrscheinlichkeit.py`** | ✔ **gebaut**, zeigt nur an | die Beiträge zusammenführen |

⚠️ **Der nachgelagerte Filter existiert also. Sein Modulkopf zitiert Ihren
Einwand von damals wörtlich** — *„das System kann diese Informationen nicht
SELBST in Zusammenhang bringen"*.

### 2.2 ⚠️ Aber er ist heute ein Vorfilter im Kostüm

**Seine fünf Beiträge, gemessen:**

| Beitrag | Zustand | Punkte | woher |
|---|---|---:|---|
| **Vorfilter H** | **trägt** | **+4,5** | vor der Kette |
| Rangplatz | null | 0,0 | vor der Kette |
| Trichter | enthalten | 0,0 | vor der Kette |
| Lebendigkeit | noch nicht | 0,0 | vor der Kette |
| Termine | nie | 0,0 | – |

> **Alle fünf stammen von *vor* der Kette.** Nichts, was das Modell, Z1 oder
> Z.ai beigetragen haben, geht ein.

**Damit beantwortet sich Ihre Frage:** ein reiner Vorfilter ist das, was wir
heute *haben* — und er kann Ihre Begründungspflicht nicht erfüllen, weil er
die Entscheidung nicht kennt, die er begründen soll.

### 2.3 Was ein nachgelagerter Filter bewerten könnte — gemessen

| Größe | gefüllt | **aufgelöst** | Zustand |
|---|---:|---:|---|
| `unabhaengige_faktoren` (Faktorzahl) | 1.656 | **66** | ⚠️ **Wiederholung der Entscheidung** — 3 = 82 % Einstieg, 2 = 0 % |
| `umgeworfen_preis_eur` (Widerlegungspreis) | 1.651 | **66** | die einzige Zahl, die dem Modell gehört — **nie ausgewertet** |
| `belege_json` | 1.611 | 54 | **nie gegen Ergebnisse ausgewertet** |
| `zai_gegenpruefung_urteil` | 836 | 46 | Anbieter nicht vom Zufall unterscheidbar (geclustert) |
| **Z1-Urteil** (Treue zur Eingabe) | **0** | **0** | ⚠️ **wird nirgends gespeichert** |

⚠️ **Z1 ist die einzige deterministische, kostenlose Prüfung der Kette** —
Zahlendeckung, Richtungstreue, Zuspitzung, Leerlauf. Sie läuft, geht in die
Mail und in die Zählung, und **landet nicht in der Signalzeile**. Sie kann
deshalb nie gegen Ergebnisse gemessen werden.

> **Das ist die eine Baustelle, die das Konzept verlangt** — und sie ist
> klein: ein Feld mehr in `felder_aus_entscheidung`.

---

## 3. ⚠️ Die harte Grenze: 66 Fälle

**Alles, was ein nachgelagerter Filter je belegen könnte, steht auf 66
aufgelösten Signalen** (42 Ziel, 24 Stop — Stand vor E1/E2; danach weniger).

| | |
|---|---:|
| Rollen-Signale gesamt | 1.656 |
| davon `nicht_anwendbar` | 1.428 |
| **aufgelöst** | **66** |

**Daraus folgt die Reihenfolge des Plans, nicht aus einer Vorliebe:**

> **Erst aufzeichnen, dann messen, dann entscheiden lassen.** Wer jetzt einen
> Beitrag in die Wahrscheinlichkeit einträgt, trägt eine Vermutung ein — und
> das Modul ist ausdrücklich dagegen gebaut („eine Zahl zu bauen hätte
> Sicherheit vorgetäuscht, wo keine war").

---

## 4. Der Plan

### Stufe 1 — Aufzeichnen, was heute verlorengeht *(die einzige Bauarbeit)*

| | was | Aufwand |
|---|---|---|
| **P1** | **Z1-Urteil je Signal speichern** — Zahlendeckung, Richtungstreue, Zuspitzung, Leerlauf | klein |
| **P2** | **Verkaufsseite: den Faktenstummel ersetzen** (B1/B2) — beide Schreibpfade, `familien` mit | klein |
| **P3** | **NICHTS_TUN bekommt seinen Grund** — N1/N2/N3 **deterministisch abgeleitet**, nicht vom Modell erfragt | mittel |

⚠️ **P3 ist der Punkt, an dem Ihre Begründungspflicht technisch wird.** Der
Grund wird *nach* der Antwort bestimmt: Bestand ja/nein (N1), Fingerabdruck
unverändert (N2), sonst N3. **Keine neue Frage an das Modell.**

### Stufe 2 — Messen, was trägt

| | was | wann möglich |
|---|---|---|
| **M1** | Widerlegungspreis gegen Ergebnis | jetzt (66 Fälle, zu wenig) |
| **M2** | Z1-Urteil gegen Ergebnis | **erst nach P1** |
| **M3** | Belege gegen Ergebnis | jetzt (54) |
| **M4** | Verkaufsseite überhaupt | **erst nach P2** |

⚠️ **Jede dieser Messungen braucht mehr Fälle, als heute existieren.** Das ist
kein Argument gegen sie, sondern der Grund, jetzt mit dem **Aufzeichnen** zu
beginnen: jeder Tag ohne P1/P2 ist ein Tag, der später fehlt.

### Stufe 3 — Entscheiden lassen

Erst wenn ein Beitrag seinen gemessenen Wert hat, kommt er in
`wahrscheinlichkeit.BEITRAEGE` — **mit Zustand `trägt`**, wie H heute.

**Und erst dann** bekommt die Wahrscheinlichkeit eine Schwelle und darf
auswählen — an der Stelle, an der heute die **Uhr** entscheidet.

---

## 5. Was das für Spot gegen Hebel heißt

**Ihr Eindruck, dass es „eher die Dimensionierung betrifft", trifft zu — und
die Arithmetik sagt, warum:**

```
hebel_noetig = verlustanteil / stop_rel        Kosten_R = 2 × Gebühr / stop_rel
```

**Der Stopabstand entscheidet beides** — Hebel *und* Kostenhürde, in
entgegengesetzte Richtung. Bei Referenz 0,30 %:

| | Stop | Hebel | Hürde über der Basisrate |
|---|---|---|---:|
| **SPOT — Bodenbildung oder Tod** | weit | 1,0 | **+0,8 Punkte** |
| **HEBEL — kurzfristige Chance** | eng | > 1 | **+8,0 Punkte** |

⚠️ **Und der Fachstandard sagt, dass die Antwort je Instrument gegenläufig
ist** (Entscheidungslog 03.08., gemessen):

| | Gate (ja/nein) | Größe |
|---|---|---|
| **Hebel** | **SQN +3,25** | +1,25 |
| **Spot** | +0,63 | **+1,36** |

> **Beim Hebel ist ein GATE überlegen, bei Spot die GRÖSSE.** Das ist genau
> Ihre Unterscheidung: eine kurzfristige Chance nimmt man oder nicht; eine
> Bodenbildung baut man in Größen auf.

**Damit hat der nachgelagerte Filter zwei verschiedene Aufgaben je
Instrument** — und das ist kein Sonderfall, sondern eine gemessene Eigenschaft:

| | Aufgabe des Filters |
|---|---|
| **Hebel** | **ja oder nein** — mit einer Schwelle |
| **Spot** | **wie groß** — über die CRV-Abstufung (geeicht, aber **aus**) |

---

## 6. Was ich NICHT vorschlage

| | warum |
|---|---|
| die Wahrscheinlichkeit jetzt entscheiden lassen | nur **ein** Beitrag trägt (H); die anderen wären Vermutungen |
| H scharf schalten | erst muss der Schatten zeigen, wie oft H auf der **Watchlist** zutrifft — Kapitel 124: auf 29 Symbolen **nicht bestätigbar** |
| die CRV-Abstufung einschalten | geeicht, aber das Einschalten ändert Positionsgrößen — Ihre Entscheidung |
| den Cooldown abschaffen | Ihre Vorgabe: er **steuert**, er entscheidet nur nicht |
| einen zweiten Filter bauen | ⚠️ **es gibt ihn** — er ist nur unterernährt |


---

## 7. ⚠️ Der Score in seiner heutigen Form — gemessen

**Nutzereinwand:** *„Die starre Geometrie wird mit H statisch aufgewertet —
ich zähle 1 und 1 zusammen, das ist keine Leistung."*

**Er hat recht, und die Messung ist eindeutig.** Über 1.323 auswertbare
Signale, Referenz 0,30 %:

| | trägt | trägt NICHT |
|---|---:|---:|
| **ohne H** | **0** | **1.323** |
| **mit H** | **948** | 375 |

> **H ist der einzige Schalter.** Der Rest ist Arithmetik aus zwei Zahlen,
> die das System sich selbst gesetzt hat:
>
> ```
> quote = 1/(1+CRV)  +  4,5 wenn H
> ```

⚠️ **Und es ist schwächer, als es aussieht: das CRV wählt das System selbst**
(Ziel = CRV × Stopabstand). Die „Basisrate aus der Geometrie" ist damit eine
Folge unserer eigenen Zielregel, keine Beobachtung am Markt. **Ein
ehrgeizigeres Ziel senkt die Quote rechnerisch** — nicht, weil der Trade
schlechter wäre.

**Der Score enthält über das einzelne Signal genau ein Bit: H ja oder nein.**

⚠️ **Das ist kein Darstellungsfehler, sondern eine Zustandsbeschreibung:** von
allen Größen der Kette ist H die einzige, die je gegen den Zufall gemessen
wurde. **Es gibt nichts Weiteres zum Zusammenzählen.**

**Was daraus folgt:**

| | |
|---|---|
| **nicht** mehr Beiträge einrechnen | ungemessene Beiträge machen den Score nicht besser, nur schwerer zu widerlegen |
| **wohl** die Zahl ehrlich zerlegen | *Ausgangslage der Gruppe* (Arithmetik) getrennt von *was dieses Signal daran ändert* (heute: nur H) |
| **und** die Kandidatenliste behalten | „nicht eingerechnet, und warum" ist die stärkste Stelle des Blocks |

---

## 8. Hart oder weich — die Einordnung

**Das Kriterium steht schon im Projekt:**

> *„ZÄHLEN, NICHT VERWERFEN — dieselbe Begründung wie beim Entscheider und
> beim Gate. **Ein Wächter, der selbst verwirft, macht seine eigene Wirkung
> unsichtbar.**"*

**Daraus die Linie:**

| | beantwortet | darf blockieren, weil |
|---|---|---|
| **HART** | **„kann / darf"** | die Alternative **unmöglich** oder **verboten** ist — Machbarkeit, Sicherheit, Kosten |
| **WEICH** | **„soll"** | Qualitätsaussagen müssen **messbar** bleiben, und messen heißt durchlassen |

### 8.1 Der Ist-Zustand, eingeordnet

| Stufe | heute | Einordnung | |
|---|---|---|---|
| `auftrag` (Instrument × Strategie) | hart | **hart** ✔ | Machbarkeit |
| `fakten` (Mindestgrundlage) | hart | **hart** ✔ | ohne Fakten kein Urteil |
| `lagebild` | hart | **hart** ✔ | dito |
| **`anlass`** (Fingerabdruck) | hart | **hart** ✔ | Kosten — dieselbe Frage zweimal zu stellen ist verschwendet |
| ⚠️ **`wiederholung`** (Cooldown) | **hart** | ⚠️ **beantwortet „soll"** | siehe 8.2 |
| `urteil` (Vertrag) | hart | **hart** ✔ | eine Antwort ohne Richtung ist keine Antwort |
| `aktion` (Bestand) | hart | **hart** ✔ | man kann nicht verkaufen, was man nicht hält |
| Mindestgröße, Töpfe, RM-11 | hart | **hart** ✔ | Kosten und Sicherheit |
| **Z1** (Treue zur Eingabe) | weich | **weich** ✔ | zählt, verwirft nicht |
| **Z.ai** (Zweitmeinung) | weich | **weich** ✔ | dito |
| **Vorfilter H** | Schatten | **weich** ✔ | wirkt noch nicht |
| **Wahrscheinlichkeit** | Anzeige | **weich** ✔ | dito |

### 8.2 ⚠️ Der Cooldown steht auf der falschen Seite

**Nutzervorgabe:** *„Ohne Uhr werden wir nicht auskommen, sie ist sinnvoll zur
**Steuerung** — aber nicht als **Entscheidung**."*

**Gemessen: er blockiert 30 von 30.** Damit ist er keine Schranke mehr,
sondern die Entscheidung.

> **Vorschlag für eine messbare Grenze:** eine harte Stufe, die dauerhaft
> nahezu alles blockiert, hat aufgehört, eine Schranke zu sein. **Wenn eine
> harte Stufe über einen vollen Umlauf mehr als 90 % verwirft, gehört sie
> geprüft** — entweder ist ihre Zahl falsch, oder sie beantwortet die falsche
> Frage.

---

## 9. ⚠️ Was ein guter Trade ist — auf dem Papier, vor der nächsten Messung

**Nutzervorgabe:** *„Wenn wir jetzt in der Planung und am Papier nicht wissen,
was ein guter Trade für ein Asset ist oder ein schlechter — bauen wir wieder
ein Luftschloss aus Messungen und Blockaden."*

**Der Einwand ist berechtigt.** Bisher misst das Projekt sein eigenes System.
Was fehlt, ist die Festlegung, **wonach** gesucht wird.

### 9.1 Es gibt vier Quellen eines Vorteils — und nur vier

**Etablierter Stand des Fachs.** Ein Trade hat nur dann einen
Erwartungswert über null, wenn mindestens eine davon zutrifft:

| | Quelle | die Aussage dahinter |
|---|---|---|
| **1** | **Drift / Trend** | der Wert steigt über den Haltezeitraum im Mittel — Momentum, Trendfolge |
| **2** | **Rückkehr zum Mittel** | der Preis ist von einem Niveau entfernt, zu dem er zurückkehrt — Bodenbildung, Unterstützung |
| **3** | **Information** | man weiß etwas, das im Preis noch nicht steht — Nachrichten, Flüsse, Fundamentaldaten |
| **4** | **Struktur / Prämie** | man wird für eine Leistung bezahlt — Spread, Finanzierung, Volatilitätsprämie |

⚠️ **Das Projekt hat drei davon selbst benannt** — *„Drift statt Timing ·
Nachrichten · Kosten"*. **Die Rückkehr zum Mittel fehlt in dieser Liste.**

### 9.2 ⚠️ Und genau sie ist die einzige, die bei uns misst

**H ist eine Rückkehr-zum-Mittel-Bedingung:** *kein mehrfach berührter
Widerstand unter dem Ziel* **und** *ein Träger über dem Stop*. Das ist eine
Aussage über **Struktur und Niveaus**, nicht über Richtung.

**Der Rangplatz ist eine Drift-Bedingung** — 250-Tage-Entwicklung im
Klassenvergleich.

**Und die Messung sagt, was passiert, wenn man beide mischt:**

| | |
|---|---:|
| H allein (523 Reihen, Referenz) | **+0,15 R je Trade** |
| Rangplatz **innerhalb** von H | **−5,8 Punkte** |

> ⚠️ **Zwei Vorteilsquellen, die einander aufheben.** Das ist kein
> Messartefakt — es ist der Normalfall: Momentum und Rückkehr zum Mittel sind
> **gegenläufige** Thesen. Wer beide gleichzeitig verlangt, sucht einen Wert,
> der zugleich gelaufen und zurückgeblieben ist.

**Und damit trifft die Formulierung des Nutzers den Kern exakt:**

| | Vorteilsquelle | Stop | Hebel | Horizont |
|---|---|---|---|---|
| **SPOT — „Bodenbildung oder Tod"** | **Rückkehr zum Mittel** | weit | 1,0 | lang |
| **HEBEL — „kurzfristige Chance"** | **Drift / Momentum** | eng | > 1 | kurz |

⚠️ **Das System stellt heute EINE Frage für beide.** Es fragt weder nach der
einen noch nach der anderen These — es fragt „kaufen oder nicht".

### 9.3 Was daraus als Festlegung folgt

**Ein guter Trade ist einer, dessen These benannt ist und dessen Bedingungen
zu dieser These passen.** Auf dem Papier:

| | **SPOT — Rückkehr zum Mittel** | **HEBEL — Drift** |
|---|---|---|
| **einschließend** | Träger über dem Stop (mehrfach berührt) · freier Weg zum Ziel · weiter Stop · Kostenhürde +0,8 Punkte | Rangplatz vorn in der Klasse · enger Stop, den die Struktur trägt · Liquidationsabstand ausreichend |
| **ausschließend** | ⚠️ **vorderer Rangplatz** (−5,8) · Widerstand unter dem Ziel · Stop ohne Träger | ⚠️ **weiter Stop** (Kostenhürde +8,0) · Finanzierung im oberen Perzentil · bekannter Termin im Fenster |
| **gemessen?** | **ja: +0,15 R** (523 Reihen) | ⚠️ **nein — nie gemessen** (S2) |

⚠️ **Die rechte Spalte ist Hypothese, die linke ist gemessen.** Das ist der
ehrliche Stand, und er sagt zugleich, wo die nächste Messung hingehört.

### 9.4 Die Nachricht — was man kann und was nicht

**Nutzervorgabe:** *„eine Nachricht kann den gesamten Markt bewegen, ABER dies
können wir nicht abfangen und auch nicht sauber mit einer Wahrscheinlichkeit
bewerten."*

**Richtig — und der Fachstandard verlangt das auch nicht.** Er unterscheidet:

| | | bei uns |
|---|---|---|
| **die Nachricht vorhersagen** | ✘ nicht möglich | – |
| **die Aussetzung messen** (Event-Risiko) | ✔ üblich | ⚠️ `anlass_kalender` **gebaut, nie gemessen** |
| **durch bekannte Termine nicht halten** | ✔ üblich | offen |
| **die Reaktion messen, nicht die Nachricht** | ✔ üblich | offen |

> **Man bewertet nicht die Nachricht, sondern die Aussetzung ihr gegenüber.**
> Ein Trade über einen bekannten Termin hinweg ist ein anderer Trade als
> derselbe daneben — unabhängig davon, was die Nachricht sagen wird.

⚠️ **`cycles.py` (FOMC-Kalender) ist gebaut und ausdrücklich „noch NICHT in
Facts/Pipeline verdrahtet".** Das ist keine neue Baustelle, sondern eine
angefangene.

### 9.5 Was das für die Marktphase heißt

⚠️ **Vorsicht ist hier geboten, und zwar aus eigener Erfahrung:** bis zum
22.08. lief jede Phasenmessung des Projekts auf einem einzigen Regime
(„Regime war IMMER bär"). Seit dem Drehen des Marktes (+15,8 % Median in neun
Tagen) gibt es **die erste zweite Phase**.

**Deshalb als Festlegung, nicht als Messung:**

| Phase | welche Vorteilsquelle trägt eher | Begründung |
|---|---|---|
| Aufwärts, breit | **Drift** | Trends halten länger, Rücksetzer sind flach |
| Abwärts, breit | **keine** — Kosten dominieren | die Basisrate ist driftfrei, die Hürde bleibt |
| Seitwärts / Boden | **Rückkehr zum Mittel** | Niveaus halten, Ausbrüche scheitern |

⚠️ **Das ist Lehrbuchwissen, nicht unsere Messung.** Es taugt als
**Hypothese, die man prüfen kann**, sobald es zwei Phasen in den Daten gibt —
und die gibt es seit neun Tagen.

---

## 10. Was ich als nächsten Schritt vorschlage

**Nicht mehr messen, sondern zuerst festlegen** — genau Ihr Einwand:

| | | |
|---|---|---|
| **1** | **Die These wird Teil des Signals.** Jedes Signal trägt, welche der vier Quellen es beansprucht | ohne sie ist „gut" nicht definierbar |
| **2** | **Die Rolle BC bekommt die These als Auftrag**, nicht als freie Wahl — so wie sie heute Instrument und Strategie bekommt | `handelsauftrag` ist die vorhandene Stelle |
| **3** | **Erst dann messen**, ob eine These trägt — je These getrennt | eine Messung über gemischte Thesen misst nichts |

⚠️ **Punkt 2 ist der Punkt, an dem die Strategien `swing` und `akkumulation`
aufhören, toter Code zu sein.** Sie sind bereits die Namen für „Drift kurz"
und „Rückkehr zum Mittel lang" — sie werden nur nie vergeben.

> **Das ist keine neue Baustelle. Es ist die angefangene, die nie zu Ende
> gebaut wurde.**
