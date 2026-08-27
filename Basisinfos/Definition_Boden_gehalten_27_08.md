> ⚠⚠ **TEILWEISE ÜBERHOLT am 27.08.2026 — für den KERN nicht mehr nötig.**
>
> Der Nutzer hat entschieden, den Kern zu **staffeln** statt zu timen (*„Staffelung wie in akkumulation beschrieben, das passt zur Praxis“*). Damit entfällt die Ja/Nein-Frage „ist jetzt ein Boden?“, auf die G die Antwort war — die Staffelung fragt **wie viel**, nicht **ob**. Siehe `Entscheidung_Kern_Staffelung_27_08.md`.
>
> **Was bestehen bleibt:** (1) der gemessene Fear-Befund in Abschnitt 0 — Fear ist ein Dauerzustand (längste Phase **151 Tage**), Extreme Greed ein Ereignis (Median **1 Tag**); (2) die fachliche Herleitung aus Dow, Wyckoff und Charttechnik; (3) G als möglicher Baustein für die **taktische** Stufe, wo ein einzelner Einstiegszeitpunkt gesucht wird.

# „Boden gehalten" — Definition, Abgrenzung zu H, Wirkung auf die Ablaufkette

**Angelegt 27.08.2026.** Auftrag des Nutzers:

> *„Definition Boden gehalten und Abgrenzung zu H. Vorher noch prüfen, was wir
> hier bauen: Grundlage sollen die **Literatur und funktionierende
> Handelsgrundlagen** sein, als Fachexperte. Zusätzlich hat die Entscheidung
> Einfluss auf unsere zentrale Funktionalität in der Ablaufkette. Wichtig: wir
> haben erst den Scheduler umgebaut — **Hebel und Spot waren getrennt und sind
> nun ein Lauf**; das muss berücksichtigt werden, da es für ein Asset de facto
> **virtuell zwei Positionen** gibt: Spot mit/ohne Bestand und Hebel mit/ohne
> Bestand."*

Und der Einwand, der das ausgelöst hat:

> *„Fehler ist, Kern-Assets über den Fear zu kaufen — der Markt ist über Monate
> im Fear. Es muss eine **strukturelle Bodenbildung** sein."*

⚠️ **Der Einwand ist gemessen und belegt** (3.125 Tage Fear-&-Greed-Historie,
2018-02-01 bis 2026-08-26):

| | Phasen | Median | **längste** | über 30 Tage |
|---|---:|---:|---:|---:|
| **Fear (<45)** | 100 | 3 T | ⚠️ **151 Tage** | **15** |
| Extreme Fear (<25) | 109 | 2 T | 74 T | 4 |
| Greed (>55) | 95 | 3 T | 94 T | 12 |
| **Extreme Greed (>75)** | 64 | **1 T** | 76 T | **1** |

**Fear ist ein Dauerzustand, Extreme Greed ein Ereignis.** Wer bei Fear
nachkauft, kauft im Extremfall 151 Tage am Stück in einen fallenden Markt.
Als *Verkaufs*auslöser bleibt Extreme Greed brauchbar — 64 Phasen in 8,5
Jahren, Median ein Tag.

---

## 1. Was die Handelsliteratur sagt — die fachliche Grundlage

Drei etablierte Lehrgebäude beschreiben Bodenbildung. Sie widersprechen sich
nicht; sie beschreiben dieselbe Sache verschieden genau.

### 1.1 Dow-Theorie — das höhere Tief

Die älteste und parameterärmste Aussage: Ein Abwärtstrend endet nicht mit dem
tiefsten Kurs, sondern mit dem **ersten Tief, das über dem vorherigen liegt**.
Ein einzelnes Tief ist kein Boden — erst das zweite, höhere Tief macht daraus
eine Struktur.

**Was daraus folgt:** Man braucht **zwei** Tiefpunkte und ihre Reihenfolge.
Ein Niveau allein sagt nichts.

### 1.2 Wyckoff — der Secondary Test und der Spring

Das Akkumulationsschema beschreibt, wie ein Boden entsteht: auf den
Verkaufshöhepunkt folgt eine automatische Erholung, dann der **Secondary
Test** — der Kurs kehrt zum Tief zurück und prüft, ob noch Angebot da ist.
Hält er, ist das Angebot erschöpft. Der **Spring** ist der Sonderfall: Der
Kurs bricht kurz *unter* das Tief und kehrt sofort zurück — die Verkäufer
laufen in die Falle.

**Was daraus folgt:** Entscheidend ist nicht, dass ein Niveau existiert,
sondern **wie sich der Kurs verhält, wenn er es erreicht**. Und: Ein kurzer
Unterschnitt ist kein Bruch, solange die Rückkehr schnell erfolgt.

### 1.3 Klassische Charttechnik — der Retest

Ein Niveau wird durch wiederholte Berührungen zur Unterstützung. Nach einem
Bruch nach oben tauscht es die Rolle (aus Widerstand wird Unterstützung), und
der **Retest von oben** ist der verlässlichste Einstiegspunkt — weil er die
neue Rolle bestätigt.

### 1.4 Was alle drei gemeinsam haben — und warum es hier zählt

> **Nicht die Existenz eines Niveaus trägt die Aussage, sondern das
> Verhalten des Kurses an diesem Niveau.**

⚠️ **Genau diese Unterscheidung fehlt unserem heutigen H.**

---

## 2. Was H heute ist — und was es nicht sagt

`agent/vorfilter.py`, wörtlich die Definition der Messung
(`messe_marken.laufe`):

    A  frei      keine Marke UEBER dem Kurs mit >= 2 Beruehrungen
                 unterhalb des Ziels
    B  gedeckt   eine Marke UNTER dem Kurs mit >= 2 Beruehrungen
                 im Band (-2,0 ATR, -0,5 ATR]

**Beide Bedingungen sind rein räumlich.** Sie fragen: *Wo liegt Struktur
relativ zum heutigen Kurs?* Sie fragen nicht: *Was ist dort zuletzt
passiert?*

**Ein Beispiel, das den Unterschied zeigt:**

| | Kurs | Marke | H-B? | Boden gehalten? |
|---|---|---|---|---|
| **Fall 1** | 62.000 | 60.000, zuletzt vor 8 Monaten berührt | ✔ **ja** | ✘ nein — nichts ist passiert |
| **Fall 2** | 62.000 | 60.000, vor 5 Tagen auf 59.400 gefallen, zurück über 60.000 | ✔ ja | ✔ **ja** — getestet und gehalten |

**H sieht beide Fälle gleich.** Das ist kein Fehler von H — es wurde als
Geometrie-Filter gebaut und als solcher gemessen (+4,5 Punkte gegen
Zufallsschwelle +2,6). Aber es beantwortet die Frage des Nutzers nicht.

⚠️ **Und der Stand, der dazugehört:** H läuft seit dem 22.08. **als Schatten**
— es markiert, es sperrt nicht. Vier Wochen mitschreiben, Auswertung um den
**19.09.2026**. Bis dahin ist H kein Filter, sondern eine Beobachtung.

---

## 3. Definition: G — „Boden gehalten"

> **G gilt für ein Asset an einem Tag, wenn eine Marke unter dem Kurs
> innerhalb der letzten `N` Handelstage BERÜHRT oder kurz UNTERSCHRITTEN
> wurde und der Kurs seither wieder darüber steht.**

### 3.1 Die Bestandteile, einzeln begründet

| | Bedingung | Herkunft | Vorschlag |
|---|---|---|---|
| **G1** | Eine Marke `M` unter dem Kurs mit **≥ 2 Berührungen** | wie H-B — dieselbe Markenrechnung, keine zweite Quelle | unverändert |
| **G2** | Das **Tief** der letzten `N` Tage lag **bei oder unter** `M` | Wyckoff Secondary Test: das Niveau muss *geprüft* worden sein | **N = 20** Handelstage |
| **G3** | Der Unterschnitt war **flach**: Tief ≥ `M − t·ATR` | Wyckoff Spring: ein kurzer Unterschnitt ist kein Bruch | **t = 0,5 ATR** |
| **G4** | Der **Schlusskurs steht heute über** `M` | Rückeroberung — sonst ist es ein laufender Bruch | unverändert |
| **G5** | *(optional)* Das jüngste Tief liegt **über** dem vorherigen | Dow: höheres Tief | **erst nach Messung** |

### 3.2 Warum diese Parameter — und was an ihnen unsicher ist

**N = 20 Handelstage (rund ein Monat).** Kürzer, und man verpasst
Bodenbildungen, die sich über Wochen ziehen; länger, und ein Test von vor
zwei Monaten gilt noch als frisch, obwohl inzwischen alles anders ist.

⚠️ **N ist eine gesetzte Zahl, keine gemessene** — dieselbe Klasse von
Annahme wie die vier aus `Vorabfestlegung_S1_S4`. Sie **muss** in der Messung
variiert werden (10 / 20 / 40), sonst wiederholen wir K3.

**t = 0,5 ATR.** Der Wert ist **nicht frei gewählt**: Es ist dieselbe Totzone
`NIVEAU_MIN_ABSTAND_ATR`, die schon die untere Kante beider H-Bänder bildet.
S1 hat gemessen, dass ihre Variation nichts trägt — das spricht dafür, sie
hier ebenfalls zu nehmen, statt eine zweite Konstante einzuführen.

**G5 bewusst zunächst weglassen.** Das höhere Tief ist fachlich die stärkste
Aussage, verlangt aber eine zweite Swing-Erkennung und halbiert vermutlich die
Trefferzahl. Erst messen, ob G ohne G5 trägt; G5 ist die **Verschärfung**, die
danach geprüft wird.

---

## 4. Die Abgrenzung in einem Satz

> **H fragt WO der Kurs steht. G fragt, WAS DORT PASSIERT IST.**

| | **H** (heute) | **G** (neu) |
|---|---|---|
| Art | räumlich, statisch | zeitlich, ereignisbezogen |
| Braucht | Kurs, Marken, ATR | zusätzlich **20 Tage Kursverlauf** |
| Frage | „Ist Platz nach oben und Halt nach unten?" | „Wurde der Halt geprüft und hat er gehalten?" |
| Trefferrate | 3,3 % der Ankertage | **unbekannt — zu messen** |
| Richtung | nur LONG (H' spiegelt nicht) | vermutlich ebenso, ⚠️ zu prüfen |
| Status | Schatten bis ~19.09. | nicht gebaut |

**Sie schließen einander nicht aus.** G ⊂ H-B ist konstruktionsbedingt
wahrscheinlich (beide setzen dieselbe Marke voraus), aber **nicht garantiert**
— G4 verlangt nur „über der Marke", H-B verlangt zusätzlich das Band
(−2,0 ATR, −0,5 ATR]. Ein Asset, das nach dem Test weit weggelaufen ist,
erfüllt G, aber nicht H-B.

⚠️ **Das ist ein Befund, kein Nebensatz:** Die beiden messen verschiedene
Mengen, und welche davon trägt, ist offen.

---

## 5. Wirkung auf die Ablaufkette — die zwei Läufe je Asset

### 5.1 Was der Scheduler-Umbau geändert hat

`assetklassen.laeufe()` liefert **(Gruppe, Instrument, Symbole)**. Für Krypto
sind das zwei Einträge:

    (krypto, spot,  44 Symbole)
    (krypto, hebel, 44 Symbole)

**Ein Asset wird also zweimal pro Umlauf beurteilt** — und das ist genau die
Beobachtung des Nutzers: *„für ein Asset gibt es de facto virtuell zwei
Positionen — Spot mit/ohne Bestand und Hebel mit/ohne Bestand."*

Vier Zustände je Asset:

| | Spot | Hebel |
|---|---|---|
| **mit Bestand/Position** | `holdings` — Verkaufsseite (`verkaufsrechnung`) | `hebel_positions` — echter Stop, Liquidation |
| **ohne** | Einstiegsseite (`entscheidungsrechnung`) | Einstiegsseite |

### 5.2 Wo G eingreift — und wo NICHT

⚠️ **G ist ein Merkmal, kein Auslöser.** Es sagt „hier hat ein Boden
gehalten"; was daraus folgt, hängt vom Lauf ab:

| Lauf | Zustand | Was G bedeutet |
|---|---|---|
| **Spot, Kern** | mit Bestand | **Nachkauf-Anlass** — der Auslöser, der Fear ersetzt |
| **Spot, Kern** | ohne Bestand | Ersteinstieg (bei BTC/ETH/SOL faktisch nie) |
| **Spot, Zyklisch** | mit Bestand | Nachkauf an starkem Level |
| **Spot, Taktisch** | ohne Bestand | Einstieg — dort, wo H heute markiert |
| **Hebel** | ohne Position | **Long-Einstieg mit Stop unter `M`** — die Marke liefert den Stop |
| **Hebel** | mit Position | kein Einfluss — dort entscheidet der reale Stop |

**Der elegante Teil:** Dieselbe Struktur trägt beide Instrumente, aber
verschieden. Beim Spot ist `M` ein **Anlass**, beim Hebel ein **Stop-Ort**.
Das ist kein Zufall, sondern der Grund, warum die Marke überhaupt eine Marke
ist — sie ist der Ort, an dem die These falsch wird.

### 5.3 ⚠️ Was das für die Doppelzählung bedeutet

Heute erzeugt jedes NACHKAUFEN-Signal eine eigene Trailing-Führung (Frage D:
**77 % Doppelungen**, LINK 6×, MON 5×). Wenn G zum Nachkauf-Anlass wird,
**verschärft sich das**, solange Positionen nicht zusammengefasst sind:
Jeder gehaltene Boden erzeugt ein weiteres Signal auf denselben Bestand.

**Reihenfolge daraus:** Die Positionsführung (eine Position je Symbol, ein
Durchschnittseinstand — Nutzerfestlegung 26.08.) muss **vor** G scharfgeschaltet
werden, nicht danach.

---

## 6. Vorabfestlegung der Messung

⚠️ **Nichts wird gebaut, bevor das gerechnet ist** (N-6). Die Messung läuft an
denselben Ankern wie H — `messe_marken.laufe`, 19.891 Anker, dieselbe
Produktionsrechnung.

### 6.1 Was gemessen wird

| | Frage | Vergleich |
|---|---|---|
| **M1** | Trägt G überhaupt? | G gegen den Rest, Blockpermutation |
| **M2** | Trägt G **zusätzlich zu H**? | G∧H gegen H allein — die entscheidende Frage |
| **M3** | Wie empfindlich ist N? | N ∈ {10, 20, 40} |
| **M4** | Wie groß ist die Schnittmenge? | Anteil G∩H an G und an H |
| **M5** | Trefferrate von G | wie viele Ankertage — 3,3 % ist H's Wert |

### 6.2 Vorab festgelegt, was welches Ergebnis bedeutet

| Ergebnis | Lesart |
|---|---|
| **M2 trägt** | ⚠️ G ist ein **eigener** Baustein — der erste, der das Verhalten misst statt der Geometrie. Dann ist er der Nachkauf-Anlass für den Kern |
| M2 trägt nicht, M1 trägt | G ist eine **Umformulierung** von H, kein Zugewinn. Dann bleibt H, und der Kern-Anlass wird aus H-B gebaut |
| **weder M1 noch M2** | G trägt nicht. ⚠️ Dann ist die Frage „was löst den Kern-Nachkauf aus" **offen** — und Fear ist als Antwort ausgeschlossen (Abschnitt 0) |
| M3: N-abhängig | ⚠️ die Schwelle ist selbst eine Schätzung (2.48) — dann ist der Suchpreis zu zahlen |

⚠️ **Positivkontrolle ist Pflicht** (93 B). Und: **zwei vorab benannte Größen**
(M1, M2), alles übrige ist Beschreibung — der Suchpreis für zwölf Zellen wäre
sonst +20,5 Punkte statt +10,2.

### 6.3 Was NICHT gemessen wird

Ob G ein *guter Zeitpunkt zum Kaufen* ist im Sinne des Nutzers („Potential").
Gemessen wird gegen das bestehende Erfolgsmaß. ⚠️ **Und das ist die bekannte
Schwäche** (N-10): „Ziel vor Stop" fällt per Konstruktion auf die Basisrate.
G wird damit an derselben Größe gemessen wie alle Nullbefunde davor.

---

## 7. Offene Entscheidungen

| # | Frage | Vorschlag |
|---|---|---|
| **1** | N = 20 Handelstage als Ausgangswert? | ja, mit Variation 10/40 |
| **2** | G5 (höheres Tief) zunächst weglassen? | ja — erst die einfache Form messen |
| **3** | Reihenfolge Positionsführung vor G? | ⚠️ **ja, zwingend** (5.3) |
| **4** | Gilt G auch für SHORT? | nein — H' spiegelt nicht, für G unbelegt |

Verwandt: `Vorabfestlegung_S1_S4_H_Annahmen_25_08.md` · `Bestandsaufnahme_Positionsfuehrung_26_08.md` ·
`Regelwerksmanual.md` Kap. 4 (AZ-1…AZ-8), Kap. 10 (S-1…S-6) ·
`Test_und_Verifikationsmethodik.md` 2.47/2.48/2.51/2.74
