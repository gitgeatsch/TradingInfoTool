# Vorabfestlegung — hat der Funding-Beitrag die richtige FORM?

*Geschrieben am 23.09.2026, **vor** der Messung. Nutzervorgabe: „wir
benötigen vorab die richtige Fragestellung und Hypothese".*

---

## 1 Der Anlass

Die Live-Stufentabelle von `funding` ist **nicht monoton**:

```
Fünftel      0        1        2        3        4
Wirkung   -0,0639  -0,0262  -0,0962  -0,1476  -0,2127     (R, H20)
Stufen     +0,82    +1,30    +0,12    -0,54    -1,70      (Punkte)
```

Das Maximum liegt bei **Fünftel 1**, nicht bei 0. `rechne_funding_beitrag.py`
legt jedoch vorab fest: *„nutzbar: die Stufen sind MONOTON über die
Fünftel — nicht nutzbar: sonst."*

**Gemessen ist bereits** (23.09., `funding_buckel.py`):

| | |
|---|---|
| Buckel in der **ersten** Hälfte | +0,0291 R |
| Buckel in der **zweiten** Hälfte | +0,0465 R |
| Blockbootstrap auf die Differenz | +0,0337 R, Band **[−0,0234 .. +0,0910]** |

➤ **Richtung stabil, statistisch nicht von null zu trennen.**

## 2 ⚠️⚠️ Die Fragestellung — und was sie NICHT ist

> **Ist die Wirkung von `funding` im Querschnittsrang monoton, oder hat
> sie ein Maximum innerhalb der Verteilung?**

Das ist eine **Formfrage**, keine Beitragsfrage.

| | |
|---|---|
| **Nicht gefragt** | ob `funding` trägt — das ist gemessen (2.549: auf der vollen Menge, beide Fenster) |
| **Nicht gefragt** | ob die Stufen „besser" werden — das wäre eine Optimierung ohne Kriterium |
| **Gefragt** | wo das Maximum der Wirkung liegt, und ob die Gruppenbildung es erzeugt |

## 3 Die Hypothesen — vor der Messung benannt

### H0 — die heutige Vorabfestlegung

> Die Wirkung ist **monoton fallend** im Funding-Rang. Das Maximum liegt
> am unteren Ende (Fünftel 0 = niedrigstes Funding).

Begründung: wer am wenigsten Finanzierung zahlt, hat die günstigste Lage.
Diese Erwartung steht hinter der Monotonie-Bedingung im Werkzeug.

### H1 — aus der Praxisliteratur abgeleitet

> Die Wirkung ist **nicht monoton**. Das Maximum liegt bei **moderat
> niedrigem**, nicht bei extrem niedrigem Funding.

Begründung (Recherche 23.09.): *„Extreme readings in **either direction**
have historically preceded mean reversions … because extreme rates mark a
**crowded, leveraged position**."* Extrem negatives Funding ist
Short-Crowding bzw. Kapitulation — also selbst ein Risikozustand, keine
günstige Lage.

⚠️ **Das Gewicht dieser Quellen ist begrenzt und das gehört hier
hingeschrieben:** es sind Broker- und Marktkommentare (Kraken, Phemex,
MetaMask, Yellow, BitMEX). Die akademische Literatur zur Cross-Section von
Kryptorenditen führt **Size, Momentum, Trend und Value** — Funding ist
dort **kein etablierter Faktor**. Die einzige gefundene Funding-Arbeit
stützt sich auf **acht Tage** Daten.

➔ **H1 ist eine Hypothese aus der Praxis, kein Befund.** Sie wird hier
geprüft, nicht vorausgesetzt.

### H2 — die Artefakt-Hypothese

> Der Buckel entsteht durch die **Gruppenbildung**. Die Funding-Verteilung
> ist stark schief; ein Rangschnitt in fünf gleich große Gruppen legt die
> unterste Grenze mitten in eine dichte Region, und Fünftel 0 und 1
> enthalten sachlich dasselbe.

## 4 ⚠️⚠️⚠️ Die Entscheidungsregel — VORAB, nicht nach den Zahlen

Zwei **unabhängige** Wege, dieselbe Frage:

| | Weg | Was ihn unabhängig macht |
|---|---|---|
| **A** | dieselbe Messung in **Dezilen** statt Fünfteln | andere Gruppengrenzen; ein Schnittartefakt verschiebt sich, ein echtes Maximum bleibt |
| **B** | Wirkung gegen das **absolute Funding-Niveau** statt gegen den Rang | kommt ohne Gruppenbildung aus |

**Vorab festgelegt, was welches Ergebnis bedeutet:**

| A zeigt Maximum im Inneren | B zeigt Maximum im Inneren | → Schluss |
|---|---|---|
| ja | ja | **H1 gestützt** — die Form ist nicht monoton. Die Stufen bleiben, die **Vorabfestlegung** im Werkzeug wird korrigiert |
| nein | nein | **H0 gestützt** — der Buckel ist ein Fünftel-Artefakt. Fünftel 0+1 werden zusammengefasst, Stufen monoton |
| ja | nein *(oder umgekehrt)* | **nichts entschieden** — die Wege widersprechen sich. Dann bleibt alles unverändert und der Punkt wird als offen geführt |

⚠️ **„Maximum im Inneren" heißt:** die Gruppe mit der höchsten Wirkung ist
**nicht** die unterste, **und** ihr Abstand zur untersten übersteigt die
Trennschärfe der Messung. Ein Abstand darunter zählt als „am Rand".

## 5 Der Messstandard — er gilt hier vollständig

```
Messstandard ab 2026-09-09: Bezug = nullpunkt | Nullwelten = 90. Perzentil
über 40 Ziehungen | Trennschärfe gegen denselben Bezug | gepflanzte
Stärken bis 0,40 R | Positivkontrolle 5 Ziehungen
```

| | |
|---|---|
| Nullpunkt | Mittelwert der Nullwelten, **nicht** null |
| Band | Blockbootstrap, Blocklänge `messnorm._block(H20)` = **60** |
| Trennschärfe | gegen den Nullpunkt, Positivkontrolle über ein künstliches Merkmal |
| **Beide Historienhälften** | R-R8 **B6** — beide Wege werden je Hälfte ausgewiesen |
| Häufigkeit | R-R8 **B4** — je Gruppe die Zahl der Symbol-Tage |

⚠️ **Die Zielgröße ist `bewegung_r` auf H20** — dieselbe wie in der
Registrierung. Ein Wechsel würde die Frage verändern.

## 6 Was aus dem Ergebnis NICHT folgt

- **Keine** Aussage über den Beitrag selbst — er trägt (2.549)
- **Keine** Neukalibrierung der Schwelle, solange die Stufen unverändert
  bleiben. Ändern sie sich, greift **R-R9** zwingend
- **Keine** Übertragung auf `turnover` — dessen Stufen sind monoton

## 7 Reihenfolge

1. Weg **A** (Dezile), beide Hälften
2. Weg **B** (absolutes Niveau), beide Hälften
3. Entscheidung nach der Tabelle in § 4 — **ohne Nachverhandlung**
4. Erst danach: Bau, R-R9, Gegenprüfung, Betrieb

---

*Diese Festlegung wird nicht mehr geändert. Weicht die Messung ab, wird
die Abweichung benannt — nicht die Festlegung angepasst.*

---

# ERGEBNIS — 23.09.2026, nach der Messung

## Die Entscheidung nach § 4: **NICHTS ENTSCHIEDEN**

| Weg | Ergebnis |
|---|---|
| **A** Dezile auf dem Rang | Maximum bei Dezil **1**, Abstand +0,1278 R **[+0,0660 .. +0,1879]** → Null ausgeschlossen, **belegt** |
| **B** Gruppen nach absolutem Niveau | ⛔ **unbrauchbar** — zwei Dezile leer, eines mit dem Vierfachen |

➔ Die Regel in § 4 sagt für diesen Fall: **alles bleibt unverändert, der
Punkt wird als offen geführt, keine Nachverhandlung.** So wird verfahren.

## ⛔⛔ Der eigentliche Ertrag: die Rangbildung ist bei Bindungen willkürlich

**35,4 % aller Funding-Werte sind exakt +0,0003** — die Standardrate der
Börse. Je Kalendertag macht der häufigste Wert im **Median 32,5 %** aus,
an Spitzentagen **93,3 %**.

`argsort(argsort(w))` vergibt bei gleichen Werten Ränge nach
**Array-Position**. Nachgewiesen: sechs identische Werte landen in **drei
verschiedenen Fünfteln**. Assets mit exakt derselben Funding-Rate bekommen
verschiedene Bewertungspunkte.

## Zwei Alternativen geprüft — beide schlechter

| | Ergebnis |
|---|---|
| **Durchschnittsrang** (korrekte Bindungsbehandlung) | wird **unruhiger**: −0,0619 / −0,0578 / **+0,0111** / −0,1733 / −0,0727; Fünftel 4 besser als 3, Gruppen 68k–84k statt gleich groß |
| **Dreiteilung** unter/auf/über Standardrate | Richtung **umgekehrt** (über Standard am besten), **alle** Bänder schließen die Null ein, Hälften widersprechen sich |

## ⚠️ Was das unbequem macht

**Die einzige Form mit belegtem Ergebnis ist genau die, die Bindungen
willkürlich aufteilt.** Keine Alternative ist belegt besser.

➔ **Die heutige Stufentabelle bleibt** — nicht weil sie gut ist, sondern
weil keine Änderung belegt ist. Der **Bindungsbefund** bleibt als Risiko
stehen; er betrifft die Live-Bewertung, nicht nur diese Frage.

⚠️ **Nicht geprüft:** ob `turnover` ebenfalls betroffen ist. Seine Werte
sind stetig — aber das ist eine Vermutung, keine Messung.

Befund **2.550-funding-form-nicht-entscheidbar**.

---

# NACHTRAG — VORABFESTLEGUNG 2: die Bindungs-Hypothese

*Geschrieben am 23.09.2026 **nach** dem Bindungsfund, aber **vor** der
Prüfung an `turnover`. Der Commit belegt die Reihenfolge.*

## ⚠️⚠️ Warum die erste Festlegung geändert werden darf

**Nutzerhinweis:** *„eine Hypothese auf falschen Annahmen muss geändert
werden, so wie der Beitrag anders angewendet werden muss."*

Die Monotonie-Bedingung in `rechne_funding_beitrag.py` setzt voraus, dass
die **Rangbildung sauber trennt**. Bei **32,5 % Bindungen im Median** tut
sie das nicht. Die Festlegung stand damit auf einer falschen Annahme —
das ist kein Nachverhandeln, sondern Korrektur der Voraussetzung.

## Der offene Mangel, den diese Festlegung heilt

Die Differenz ordinal → Durchschnittsrang wurde **gemessen, bevor** eine
Hypothese stand: +0,0046 R auf der gemeinsamen Menge, Band
[+0,0006 .. +0,0070]. Sauber gerechnet, aber **Datenfischen** — zwei
Varianten gerechnet, die bessere begründet.

➔ Das macht sie zur **Beobachtung**, nicht zum Befund.

## Die Hypothese — quantitativ, damit sie scheitern kann

> **H-Bindung:** Der Unterschied zwischen ordinaler und
> Durchschnittsrang-Behandlung entsteht **durch die Bindungsdichte**.
> Er skaliert mit ihr.

**Daraus die Vorhersage für `turnover`** (3,2 % Bindungen gegen 32,5 %):

```
erwartete Differenz  =  0,0046 R  ×  3,2 / 32,5  =  +0,00045 R
```

## ⚠️⚠️⚠️ Die Entscheidungsregel — vor der Messung

| Differenz bei `turnover` | → Schluss |
|---|---|
| **< +0,0010 R** *(nahe der Vorhersage)* | **H-Bindung gestützt.** Der Effekt kommt von den Bindungen. Die Behandlung wird korrigiert — für `funding` mit Wirkung, für `turnover` folgenlos |
| **> +0,0030 R** *(wie bei funding)* | **H-Bindung widerlegt.** Der Unterschied kommt woanders her; die Korrektur wäre nicht begründet und unterbleibt |
| **dazwischen** | **nichts entschieden** — die Vorhersage trifft nicht, aber sie scheitert auch nicht. Der Punkt bleibt offen |

⚠️ **Gemessen wird gepaart auf der GEMEINSAMEN Tagesmenge** — der Fehler
aus dem ersten Anlauf (2.399 gegen 2.115 Tage) wird nicht wiederholt.
Band über Blockbootstrap, Blocklänge 60.

⚠️ **Und die Lückentage werden ausgewiesen**: fallen bei `turnover` Tage
weg, wird ihre Wirkung genannt — bei `funding` waren sie **schlechter**
(+0,0126 gegen +0,0257) und haben den ersten Vergleich geschönt.

## Was auch bei „gestützt" NICHT folgt

- **Keine** Aussage, dass `funding` besser wird — die +0,0046 R bleiben
  eine Beobachtung an derselben Datenlage
- **Keine** Änderung ohne **R-R9** (Neukalibrierung) und ohne neue
  Stufentabelle

---

# VORABFESTLEGUNG 3 — die ANWENDUNG, nicht die Form

*23.09.2026, vor der Messung. Nutzerfrage, die alles davor einordnet:
„haben wir schon die korrekte Anwendung festgelegt — Regler, Schalter,
wann positiv oder negativ? Sonst haben wir einen Beitrag zu was?"*

## ⛔⛔ Der Befund, der alle heutigen Fundstellen erklärt

`funding` wird an **drei Stellen verschieden** angewandt, und keine davon
wurde je gemeinsam festgelegt:

| Wo | Als was | Wirkung |
|---|---|---|
| **Betrieb** (`wahrscheinlichkeit`) | **Regler** | 5 Stufen auf die Quote: +0,82 … −1,70 |
| **Messung** (`phase3_kette`, `n67`) | **Schalter** | oberstes Fünftel wird gesperrt |
| **Mail** (`marktrang`) | **Text** | „Hohe Finanzierungskosten zeigen viele Long-Positionen an" |

➔ **Die Messung modelliert einen Schalter, der Betrieb fährt einen
Regler.** Alle vier heutigen Fundstellen — Buckel, Monotonie, Bindungen,
Messung≠Betrieb — sind Symptome derselben Ursache: **der Beitrag hat nie
eine festgelegte Anwendung.**

⚠️ Auch mein eigener Satz *„geprüft wird die Sperre — so wirkt der Beitrag
im Betrieb"* war deshalb falsch.

## Die Festlegung: drei ökonomische Zustände

**Nutzervorgabe:** *„der Schalter sollte u. U. in drei Positionen gemessen
werden — hoch, neutral, niedrig."* Dem folge ich, mit ökonomisch
begründeten Grenzen statt Rangschnitten:

| Zustand | Grenze | Anteil | Bedeutung |
|---|---|---|---|
| **negativ** | Funding < 0 | 22,6 % | Shorts zahlen Longs — Short-Crowding, Kapitulation |
| **normal** | 0 ≤ Funding ≤ Standardrate | 30,2 % | kein Ungleichgewicht |
| **hoch** | Funding > Standardrate | 47,3 % | Longs zahlen Prämie — Long-Crowding |

⚠️⚠️ **Die Grenzen kommen aus der SACHE, nicht aus der Verteilung.** Damit
entfallen Bindungsproblem, Monotoniefrage und die Abhängigkeit von der
Tagesbesetzung auf einen Schlag — alle drei waren Folgen der Rangbildung.

⛔ **Meine frühere Dreiteilung schnitt AN der Standardrate** und isolierte
damit den Massepunkt statt eines ökonomischen Zustands. Ihr Negativergebnis
(„über Standard am besten") zählt **nicht** — es beantwortete die falsche
Frage.

## Die Hypothese — sie muss scheitern können

```
negativ         schlechter als normal     ← Stress, Kapitulation
normal          bestes
hoch            schlechter als normal     ← Long-Crowding
```

➔ Eine **U-Form**, klar verschieden von der heutigen monotonen
Stufentabelle.

⚠️ **Was die Lehrmeinung leistet und wo sie aufhört:** sie sagt, was die
Zustände **bedeuten** (Positionierung, Crowding, Stress). Sie sagt
**nicht**, ob sie in unserer Messmenge **tragen**. Das entscheidet die
Messung.

## ⚠️⚠️⚠️ Die Entscheidungsregel — vor den Zahlen

| Ergebnis | → Schluss |
|---|---|
| **normal** ist bestes **und** beide Ränder liegen unter ihm, Abstände über der Trennschärfe | **U-Form belegt** — die Anwendung wird auf drei Zustände umgestellt, R-R9 greift |
| **hoch** ist am schlechtesten, **negativ** aber nicht (monoton fallend) | **Lehrmeinung nur halb** — dann einseitiger Schalter am oberen Ende, unteres Ende ohne Bonus |
| kein Abstand übersteigt die Trennschärfe | **nichts entschieden** — die heutige Anwendung bleibt, Punkt bleibt offen |
| **hoch** ist das beste | **Hypothese widerlegt** — dann ist die Lehrmeinung für unsere Menge falsch, und das wird so festgehalten |

**Gemessen wird** nach Messstandard: gepaart auf derselben Tagesmenge,
Band über Blockbootstrap (Blocklänge 60), **beide Historienhälften**
(R-R8 B6), Häufigkeit je Zustand (B4), Zielgröße `bewegung_r` auf H20.

## Was auch bei „belegt" NICHT folgt

- **Keine** Umstellung ohne **R-R9** (Neukalibrierung) und neue Punktetabelle
- **Keine** Übertragung auf `turnover` — dessen Werte sind stetig, die
  Rangform dort unauffällig (3,2 % Bindungen)
- **Keine** Aussage über die Mail-Formulierung — sie ist Text, kein Beitrag
