# Konzept: die Bewertungsstufe — und warum Schritt 1 nicht klein ist

**Angelegt 29.08.2026, zur Abstimmung. Nichts davon ist gebaut.**

**Nutzerauftrag:** *„mach Schritt 1 bis 3 … der 1. Schritt wird als klein
bezeichnet, ist aber vorher im Konzept zu bewerten und bevor wir bauen einen
abgestimmten Plan zur Zielerreichung."*

⚠️ **Der Auftrag war richtig, meine Einschätzung „klein" war es nicht.** Beim
Ausarbeiten sind zwei Grundsatzfragen aufgetaucht, die vor jedem Bau
entschieden sein müssen. Beide sind im Projekt bereits belegt — ich hatte sie
nicht verknüpft.

---

## 1. Die Frage, die alles davor entscheidet: **ist die Quote das richtige Maß?**

**Nein.** Und das steht seit dem 23.08. fest, Nutzervorgabe wörtlich:

> *„Wichtig für den ‚guten Trade' ist das POTENTIAL — also hohe
> Wahrscheinlichkeit, dass etwas unter bestimmten Bedingungen eintritt — und
> **nicht die reelle Zielerreichung**; diese ist immer außer Reichweite."*

**Die Begründung ist arithmetisch, nicht meinungsabhängig:**

```
Ziel        = CRV × Stopabstand
Basisrate   = 1/(1+CRV)          <- steht fest, BEVOR der Markt etwas tut
```

Ein Barrierensystem auf driftfreiem Pfad hat brutto Erwartungswert null — für
**jede** Geometrie (33,3 % theoretisch, 34,0 % gemessen über 19.891 Anker).

⚠️ **Wer „Ziel vor Stop" misst, misst die eigene Zielregel zurück.** Das
erklärt die Nullbefundserie: *„Nicht der Markt war leer — das Maß war blind."*

### Was das für unsere Bausteine heißt

| Baustein | betroffen? | warum |
|---|---|---|
| **Basisrate** `1/(1+CRV)` | ⚠️ **ist** die Blindheit | reine Konstruktion, keine Marktaussage |
| **Potential** `quote×CRV−(1−quote)` | ✔ **nicht blind** | es ist **null** bei reiner Basisrate und misst damit **ausschließlich die Beiträge** |
| **Vorfilter H, +4,5 Punkte** | ⚠️ **gemessen bei CRV 2,0** (`messe_marken.py:80`) | eine Aussage über „Ziel vor Stop", nicht über die Bewegung |

✔ **Wichtige Differenzierung:** H vergleicht zwei Arme mit **derselben**
Zielregel. Der Unterschied zwischen ihnen ist eine gültige Aussage — die
Blindheit betrifft die absolute Höhe, nicht den Vergleich.

⚠️ **Aber:** H sagt *„von hier aus wird das Ziel häufiger vor dem Stop
erreicht"* — nicht *„von hier aus bewegt sich der Kurs weiter"*. Für die
Zielvorgabe („wie viel ist hier zu holen") ist das die falsche Frage.

### Ist „Quote" überhaupt die richtige Bezeichnung?

**Nein — sie ist mehrdeutig und deshalb Teil des Problems.**

| heute | präzise | was gemeint ist |
|---|---|---|
| „Quote" | **Zielerreichungsquote** | Anteil der Fälle mit Ziel vor Stop |
| „Basisrate" | ✔ passt | was diese Quote per Geometrie ohnehin ist |
| „Potential" | ✔ passt | Erwartungswert in R, gebührenfrei |
| — fehlt — | **Bewegungserwartung** | wie weit sich der Kurs bewegt, barrierenfrei |

✔ **Das Werkzeug für die letzte Zeile existiert:** `agent/trichter.py`
(Kapitel 93, gebaut 19.08.) — „die übliche Kursbewegung auf 5/20/60
Handelstage, 80 % der Fälle, **Richtung offen**". Es steht bereits in jeder
Mail mit Einstiegszone.

⚠️ **In `wahrscheinlichkeit.py` ist der Trichter als Beitrag mit `0.0` Punkten
und dem Zustand „enthalten" geführt** — Begründung: *„er bestimmt die
Geometrie und damit die Basisrate."* Das ist richtig, **solange** die Basisrate
der Maßstab ist. Wird der Maßstab die Bewegung, ist der Trichter nicht mehr
„enthalten", sondern **die Grundlage**.

---

## 2. Die zweite Frage: **trägt die LLM-Kette überhaupt?**

**Ungemessen — und das Projekt hat sich selbst die Reihenfolge gegeben:**

> **„N-7 hat Vorrang vor N-6: ob ein Eingriff in die Kette sich lohnt, hängt
> davon ab, ob die Kette selbst trägt."**

**Was für die ALTE Kette gemessen wurde** (09.08.):

| | Richtungstreffer |
|---|---|
| LLM-Richtungswahl | **29,8 / 27,7 / 25,0 %** |
| „immer SHORT" | 74,0 / 80,9 / 87,5 % |
| EMA-200 | 61,8 / 61,7 / 63,5 % |

⚠️ *„Das LLM liegt hinter JEDER Regel."* Dazu Z.ai: **17× LONG in 2.469
Prüfungen**.

⚠️⚠️ **Seit dem Rollenumbau existiert KEINE vergleichbare Messung.** Der
Prompt ging von 34.611 auf 3.183 Zeichen, zwei Rollen statt einer, Z1 kam
dazu. Ob die heutige Kette den Zufall oder eine einfache Regel schlägt, ist
**unbeantwortet** — nicht „erfüllt".

**Was das für Schritt 1 bis 3 bedeutet:** Eine Bewertungsstufe, die entscheidet,
welche LLM-Urteile durchgehen, setzt voraus, dass die Urteile überhaupt Wert
haben. Ist das nicht so, filtert sie Rauschen nach Rauschen.

---

## 3. Was Stufe 11 (Entscheider) heute entscheidet — und was sie sollte

### Heute

```
basisrate = 1/(1+CRV)                              Geometrie
p         = geschrumpft(treffer, faelle, basisrate) Trefferbilanz
schwelle  = (1 + kosten_r)/(1 + CRV)                Gebühren
traegt    = p > schwelle                            -> wird nur gebucht
```

**Drei Befunde, alle gemessen:**

| | |
|---|---|
| ⚠️ **Die Trefferbilanz ist leer** | 2.313 Signale, davon 1.618 `nicht_anwendbar`, 335 `einstieg_nie_erreicht` — **nur 96 mit echtem Ergebnis**. Eine Zelle braucht **50**. `geschrumpft(0,0)` liefert exakt die Basisrate |
| ⚠️ **Der Maßstab sind die Gebühren** | bei 3 % Spot-Kosten verlangt sie 53,3 % statt 33,3 % — der am 25.08. verworfene Maßstab |
| ⚠️ **Sie wirkt nicht** | bucht „verloren", der Code läuft ohne `return` weiter |

✔ **In Summe: Sie vergleicht eine Zahl, die die Basisrate ist, mit einer
Schwelle, die die Gebühren sind — und tut nichts mit dem Ergebnis.**

### Was sie sollte

> **Stufe 11 beantwortet: „Ist die erwartete Bewegung groß genug, dass sich
> diese Handlung lohnt — unabhängig von Gebühren und Betrag?"**

| | heute | Ziel |
|---|---|---|
| **Eingang** | Trefferbilanz (leer) + Gebühren | **Bewegungserwartung** aus dem Trichter + gemessene Beiträge |
| **Maßstab** | Breakeven mit Gebühren | eine **Potentialschwelle**, gebührenfrei |
| **Wirkung** | zählt | **verwirft** — und der Grund steht in der Mail |

---

## 4. Wo Potential, Wahrscheinlichkeit und Wirtschaftlichkeit hingehören

**Die Trennung ist am Code gemessen** (CRV 2,0, Stop 5 %, Krypto, H erfüllt —
die Quote ist überall 0,3783, nur der Maßstab wechselt):

| Ebene | Satz | Breakeven | Abstand | Erwartungswert |
|---|---|---|---|---|
| **Potential** | **0,00 %** | 33,33 % | **+4,5 Punkte** | **+0,135 R** |
| **Messreferenz** | 0,30 % | 37,33 % | +0,5 Punkte | +0,015 R |
| **Wirtschaftlichkeit** | 1,50 % | 53,33 % | **−15,5 Punkte** | **−0,465 R** |

**Wo jede Ebene gilt:**

| Ebene | gilt für | gilt NICHT für |
|---|---|---|
| **Potential (0,00 %)** | Stufe 11 · Vorfilter H · Auswahl · jede Rangfolge | die Mail als alleinige Zahl |
| **Messreferenz (0,30 %)** | Vergleiche zwischen Signalen, Messläufe | Betrieb |
| **Wirtschaftlichkeit (1,50 %)** | ⚠️ **ausschließlich die Mail** — Ihre Auskunft | **jeden Filter, jede Rangfolge** |

⚠️ **Derselbe Trade ist gebührenfrei gut (+0,135 R) und mit Bitpanda-Satz
schlecht (−0,465 R).** Wer mit 1,50 % filtert, verwirft Trades, deren
Zeitpunkt richtig ist — er misst die Börse, nicht den Markt.

---

## 5. Punkt 4 im Gesamtkonzept: von „zählen" zu „filtern"

**Ihre Frage:** *„jetzt zählt er, soll er zukünftig aktiv schlechte Trades
filtern statt zählen, und wie machen wir das?"*

**Ja — aber in dieser Reihenfolge, und keine Stufe darf vorgezogen werden:**

| # | Schritt | Warum genau hier | Art |
|---|---|---|---|
| **V-0** | **N-7 messen:** trägt die heutige LLM-Kette? | Ohne diese Antwort filtert Stufe 11 Rauschen nach Rauschen. Das Projekt hat sich den Vorrang selbst gegeben | **Messung** |
| **V-1** | **Maß festlegen:** Bewegungserwartung statt Zielerreichung | Sonst baut Stufe 11 auf dem blinden Maß auf. Werkzeug (`trichter.py`) ist gebaut | ⚠️ **Ihre Entscheidung** |
| **V-2** | **Beiträge gegen das neue Maß neu messen** — beginnend mit H | H's +4,5 Punkte gelten für „Ziel vor Stop", nicht für „Bewegung" | **Messung** |
| **V-3** | **Schwelle festlegen:** ab welchem Potential wird gehandelt? | Keine Messfrage — eine Risikoentscheidung | ⚠️ **Ihre Entscheidung** |
| **V-4** | **Stufe 11 umstellen:** Potential statt Gebühren-Breakeven | erst jetzt sinnvoll | Bau, klein |
| **V-5** | **Stufe 11 scharf schalten:** verwerfen statt zählen | erst wenn V-1 bis V-4 stehen | Bau, klein |
| **V-6** | **Vorfilter H in Stufe 11 überführen** | er trägt schon +4,5 Punkte bei — es fehlt nur die Wirkung | Bau, klein |

⚠️ **V-4 bis V-6 sind zusammen etwa ein Tag. V-0 bis V-3 sind die Arbeit.**

⚠️ **Warum die Reihenfolge zwingend ist:** Jeder vorgezogene Bauschritt
verschärft einen bestehenden Fehler. Stufe 11 scharf zu schalten, solange ihr
Maßstab die Gebühren sind, würde nach genau der Definition filtern, die am
25.08. verworfen wurde.

---

## 6. Was ich zur Abstimmung brauche

| # | Frage | Vorschlag des Fachexperten |
|---|---|---|
| **A** | Wird **N-7** (trägt die LLM-Kette?) vor allem anderen gemessen? | ✔ **ja** — das Projekt hat sich den Vorrang selbst gegeben, und alles Weitere hängt daran |
| **B** | Wird das Maß von **Zielerreichung** auf **Bewegungserwartung** umgestellt? | ✔ **ja** — die Zielerreichung kann per Konstruktion nicht antworten |
| **C** | Bleibt **1,50 %** ausschließlich in der Mail? | ✔ **ja**, unverändert |
| **D** | Ab welchem Potential wird gehandelt? | ⚠️ **keine Empfehlung ohne V-2** — die Zahl hängt daran, was die neu gemessenen Beiträge tragen |

**Erst wenn A bis C entschieden sind, ist V-4 bis V-6 sinnvoll baubar.**

Verwandt: `Regelwerksmanual.md` R-A1 bis R-A18 und „Die sechs Stufen des
Ablaufs" · `feedback_potential_statt_zielerreichung` ·
`Zwischenstand_Gesamtprojekt_06_08.md` Nachtrag 25.08. (N-5 bis N-7) ·
`agent/trichter.py` (Kapitel 93)

---

## V-0 GEMESSEN — 29.08.2026 — ⚠️⚠️ NULLBEFUND

**Die Frage:** Trägt die heutige Rollen-Kette (Rolle A = Marktlage · Rolle BC =
Urteil · Trichter Stufe 1–11), oder filtert eine neue Bewertungsstufe nur
Rauschen nach Rauschen?

**Werkzeug:** `messe_n7_kette_korrigiert.py`
**Datenlage:** 1.516 Kaufempfehlungen · 29 von 54 Symbolen in `messdaten.db` ·
Überschneidung Signale × Kurse = **14.08.–21.08.2026, sieben Handelstage**
**Maß:** B(t,H) = Kurs(t+H)/Kurs(t) − 1, als Perzentilrang je Symbol
(gebührenfrei — Regel 2 des Zielbilds)

### Der Weg zum Befund — drei Korrekturen

| | Messung | Ergebnis | was daran falsch war |
|---|---|---|---|
| **1** | Kette gegen Zufall aus der **ganzen** Reihe | +0,1371 · t 7,71 | ⚠️ Der Signalzeitraum war **+0,704 Punkte** besser als der historische Schnitt (Median-Tagesbewegung +0,546 % gegen −0,158 %). **Rund 60 % des Vorsprungs war der Zeitraum, nicht die Kette** |
| **2** | Kette gegen Zufall aus **demselben Fenster** | +0,0539 · t 4,68 | ⚠️ Hält den Zeitraum fest, aber nicht den **Kalendertag**. Krypto läuft synchron — wenn die Kette an guten Tagen gemeinsam feuert, sieht jedes Symbol gut aus |
| **3** | **eigene gegen fremde Signaltage** (gepaart) | **+0,0013 · t 0,12** | ✔ Hält den Kalendertag exakt fest. **Das ist der Nachweis** |

### Das Ergebnis

```
HORIZONT 1 Tag  — 20 Symbole
  eigene Signaltage      +0,0538
  fremde Signaltage      +0,0525   Signaltage ANDERER Symbole, gleich gut
  ASSET-EIGENER Anteil   +0,0013   t = +0,12    7 von 20 positiv

HORIZONT 2 Tage — 17 Symbole
  ASSET-EIGENER Anteil   +0,0054   t = +0,29    5 von 17 positiv
```

⚠️⚠️ **Die Kette unterscheidet nicht zwischen Assets.** Die Signaltage eines
*fremden* Symbols sind an denselben Tagen genauso gut wie die eigenen. Der
gesamte scheinbare Vorsprung sitzt im Kalendertag, den alle Symbole teilen.

### Und der Kalendertag selbst? Auch kein Befund

| Tag | Bewegung | Signalquote |
|---|---|---|
| 14.08. | −0,53 % | **17 %** |
| 15.08. | −1,25 % | 55 % |
| 16.08. | +0,61 % | 55 % |
| 17.08. | −1,24 % | 72 % |
| 18.08. | **+7,96 %** | 69 % |
| 19.08. | +5,23 % | 76 % |
| 20.08. | +0,85 % | **79 %** |

Die Signalquote steigt **monoton von 17 % auf 83 %** — das ist das bekannte
Aufwärmen nach dem Neustart (Ausfallzeit 70,2 %, Stand 17.08.), nicht Timing.
Auf Tagesebene, der **ehrlichen** Einheit:

```
n = 7 Kalendertage
Zusammenhang Signalquote <-> Tagesbewegung:  r = +0,383
p (Permutation ueber die Tage)            =  0,387
nachweisbar waere bei n=7 erst             r > 0,73
```

### Kontrollen (Methodik 2.81 — laufen mit)

| Arm | Wert | Urteil |
|---|---|---|
| BESTTAG *(Lookahead, Positivkontrolle)* | +0,1460 · t 6,16 | ✔ das Maß **kann** trennen |
| ERSTE TAGE *(Negativkontrolle)* | −0,0752 · t −3,01 | ⚠️ **nicht neutral** — im Fenster lag ein Zeittrend, genau die Falle |
| FREMDE SIGNALTAGE *(Negativkontrolle)* | +0,0525 | ⚠️⚠️ **fast so gut wie die Kette** — der Alarm, der den Befund kippte |

### Was daraus folgt

Die vorab festgelegte Deutung greift:

> *„Kette schlägt den Zufall NICHT → eine Bewertungsstufe auf dieser Kette
> filtert Rauschen nach Rauschen. V-1 bis V-6 sind auszusetzen, bis die Kette
> selbst trägt."*

**Präzise gefasst — was gilt und was nicht:**

| | |
|---|---|
| ✔ **belegt** | Die Kette hat **keine Asset-Auswahl**. Gemessen, nicht vermutet: +0,0013 bei t 0,12, 7 von 20 Symbolen positiv. Das ist eine echte Null, kein Datenmangel — die 20 gepaarten Symbole reichen für diesen Test |
| ⚠️ **offen** | Ob die Kette **Kalendertage** trifft, ist mit sieben Tagen **nicht entscheidbar**. Weder belegt noch widerlegt |
| ✖ **nicht belegt** | Dass die Kette „nichts kann". Der Tagesteil ist ungemessen, nicht negativ |

**Der zweite Befund erklärt den ersten:** eine Kette, die an **63–75 % aller
Tage** meldet (BNB 100 %, BTC/ETH/ALGO/BEAMX/INJ je 88 %), kann keine
Asset-Auswahl haben — sie meldet fast alles.

⚠️ **Damit ist V-1 bis V-6 nicht widerlegt, sondern in der Reihenfolge
verschoben.** Eine Potentialschwelle auf einer Kette ohne Asset-Auswahl
schneidet an einer Stelle, an der es nichts zu unterscheiden gibt. Was zuerst
gebraucht wird, ist **Trennung überhaupt** — nicht ein besserer Maßstab für
eine Kette, die alle Assets gleich behandelt.

---

# TEIL 2 — DER GESAMTPLAN (29.08.2026)

**Nutzeraussage, die diesen Teil ausgelöst hat:** *„Es existieren nur
Fragmente, unfertig, weil uns der Gesamtplan und die erforderlichen
Bewertungsfaktoren fehlen — und ich weiß nicht mehr den Unterschied von
Potential und Wahrscheinlichkeit."*

**Beides ist berechtigt.** Der erste Punkt ist unten belegt, der zweite ist
mein Versäumnis: ich habe beide Wörter nebeneinander benutzt, ohne sie je
sauber zu trennen.

---

## 1. Wahrscheinlichkeit und Potential — der Unterschied in einem Satz

| | Frage | Einheit |
|---|---|---|
| **Wahrscheinlichkeit** | **Wie oft** geht es gut? | Prozent |
| **Potential** | **Was bleibt übrig**, wenn man es oft macht? | Vielfaches des Risikos (R) |

### Warum die Wahrscheinlichkeit allein nichts sagt

Beide Beispiele haben **dieselbe** Wahrscheinlichkeit von 38 %:

| Ziel gegenüber Stop | Rechnung | Potential |
|---|---|---|
| Ziel **dreimal** so weit | 0,38 × 3 − 0,62 | **+0,52 R** — gut |
| Ziel **gleich** weit | 0,38 × 1 − 0,62 | **−0,24 R** — schlecht |

Und umgekehrt: 25 % bei fünffachem Ziel ergibt +0,50 R — praktisch dasselbe
Potential bei **weit schlechterer** Trefferquote.

⚠️ **Eine Trefferquote ohne die Geometrie daneben ist keine Aussage.**

### Und was in unserem System dazukommt

Bei uns ist der Ausgangswert der Wahrscheinlichkeit fest an die Geometrie
gekoppelt — bei dreifachem Ziel sind es 25 %. Setzt man genau diesen Wert ein:

```
0,25 × 3 − 0,75 = 0
```

**Null.** Das ist kein Fehler, sondern der Kernbefund des Projekts.

| | |
|---|---|
| **Die Wahrscheinlichkeit** | enthält den Nullpunkt — den Teil, der ohnehin gilt, egal was der Markt tut |
| **Das Potential** | ist **der Abstand vom Nullpunkt** — und damit ausschließlich das, was wir über den Zufall hinaus wissen |

✔ **Merksatz:** *Die Wahrscheinlichkeit sagt, wie oft. Das Potential sagt, ob
es sich lohnt. Und in unserem System sagt das Potential zusätzlich: um wie viel
wir besser sind als raten.*

⚠️ **Daraus folgt unmittelbar:** Ein Potential von null bedeutet nicht „schlechter
Trade", sondern **„wir wissen nichts über diesen Trade"**. Genau das ist heute
der Regelfall.

---

## 2. Die Bewertungsfaktoren — vollständige Lage

**Ein Bewertungsfaktor ist eine gemessene Aussage, die das Potential über null
hebt.** Ohne solche Faktoren ist jede Bewertung exakt null — unabhängig davon,
wie gut die Kette, das Modell oder die Geometrie sind.

### Was geprüft wurde, und was dabei herauskam

| # | Faktor | Ergebnis | im Betrieb? |
|---|---|---|---|
| 1 | **Vorfilter H** (Weg frei, Stop gedeckt) | ✔ **trägt**, +4,5 Punkte | ✔ **ja** — der einzige |
| 2 | **Tagewahl** (unter dem Schnitt / nach Rückgang) | ✔ **trägt** — schlägt den quotengleichen Zufall in allen Klassen und beiden Marktphasen | ✖ **nein** — nur im Messwerkzeug |
| 3 | **Auswahl quer** (starke Werte, schwache Tage) | ✔ **trägt** — +1,01 %, t 3,20 | ⚠️ **halb** — wählt aus, zählt aber nicht als Beitrag |
| 4 | **Abstand von Bitcoin zum eigenen 200-Tage-Schnitt** | ✔ **einzig konsistent** über alle Prüfungen, **stetig** | ⚠️ **halb** — steht in der Lagebeschreibung, ist kein Beitrag |
| 5 | Rangplatz in der Anlageklasse | ⚠️ **trägt negativ** (−5,8 Punkte innerhalb H) | bewusst auf null |
| 6 | Lebendigkeit des Projekts | ⏳ sammelt, auswertbar **ab 18.09.2026** | registriert, null |
| 7 | Bekannte Termine | ✖ nie gegen den Zufall gemessen | registriert, null |
| 8 | Trichter (übliche Kursbewegung) | — steckt im Nullpunkt | enthalten |
| 9 | Liquidität, Schwankung, Größe, Alter, Beta | ✖ **flach** — keine Asset-Eigenschaft erklärt den Vorsprung | nein |
| 10 | Marktbreite | ✖ **invers** — breiter Markt war nie ein guter Einstieg | gestrichen |
| 11 | Drift | ✖ trug nicht — ⚠️ **im Bärmarkt gemessen**, Wiederholung offen | nein |
| 12 | Marktphase | ✖ stumm | nein |
| 13 | Struktur | ✖ trägt nicht | nein |
| 14 | Positionierung (Terminmarkt, Finanzierungsrate) | ⏳ **frühestens 22.10.2026** | sammelt seit 14.07. |
| 15 | **Modellurteil der Rollen-Kette** | ✖ **keine Asset-Auswahl** (V-0, 29.08.) | läuft, trägt nicht |

### Das Gesamtbild in Zahlen

| | |
|---|---|
| geprüfte Kandidaten | **15** |
| davon tragend | **4** (Nr. 1–4) |
| davon **als Bewertungsbeitrag im System** | **1** (Vorfilter H) |
| davon **abgestuft** statt Ja/Nein | **1** (Nr. 4, Bitcoin-Abstand) |

⚠️⚠️ **Das ist die Antwort auf „es existieren nur Fragmente":** Drei von vier
tragenden Faktoren sind gemessen, dokumentiert — und **werden in der Bewertung
nicht mitgezählt.** Nicht weil sie verworfen wurden, sondern weil sie nie
angeschlossen wurden.

⚠️ **Und der einzige angeschlossene ist ein Schalter.** Damit kann eine
Bewertung heute genau zwei Werte annehmen. Ein Vergleich dreier Empfehlungen
(Nutzerpunkt 2) ist damit unmöglich — nicht aus Konzeptmangel, sondern aus
Mangel an Abstufung.

---

## 3. Der Gesamtplan

**Die Reihenfolge folgt aus der Lage oben, nicht aus einer Vorliebe.**

| Stufe | Was | Warum genau hier | Art |
|---|---|---|---|
| **G-1** | **Begriffe festschreiben** — Wahrscheinlichkeit, Potential, Nullpunkt, Beitrag | Ohne das reden wir aneinander vorbei, wie am 29.08. geschehen | ✔ **mit diesem Abschnitt erledigt** |
| **G-2** | **Die drei tragenden, nicht angeschlossenen Faktoren anschließen** — Tagewahl · Auswahl quer · Bitcoin-Abstand | Sie sind **schon gemessen**. Kein Messaufwand, nur Anschluss. Das ist der größte Zugewinn je Aufwand im ganzen Projekt | Bau |
| **G-3** | **Abstufung herstellen** — jeden Beitrag als Wert von 0 bis 1 statt Ja/Nein, wo die Messung es hergibt | Ohne Abstufung kein Vergleich dreier Empfehlungen. Der Bitcoin-Abstand ist bereits stetig, die Tagewahl lässt sich stetig fassen | Bau + Messung |
| **G-4** | **Potential anschließen** — `potential.py` hat bis heute keinen einzigen Aufrufer | Erst jetzt hat es etwas zu rechnen | Bau, klein |
| **G-5** | **Schwelle festlegen** — ab welchem Potential wird gehandelt? | ⚠️ **Ihre Entscheidung.** Erst sinnvoll, wenn G-2/G-3 den Wertebereich kennen | Entscheidung |
| **G-6** | **Verwerfen statt zählen** | Erst wenn der Maßstab stimmt | Bau, klein |
| **G-7** | **Vergleich der Bewertungsqualität** (Nutzerpunkt 2) | Fällt automatisch ab, sobald G-3 abgestufte Werte liefert — es ist nur eine Sortierung fertiger Zahlen | Bau, klein |
| **G-8** | **Neue Faktoren suchen** — laufend | Vier tragende sind wenig. Die Suche endet nie | Messung |

⚠️ **G-2 ist der Bruch mit dem bisherigen Vorgehen.** Bisher wurde immer neu
gemessen. Der größte Hebel liegt aber darin, **das schon Gemessene endlich
anzuschließen**.

### Verhältnis zum bisherigen Plan V-0 bis V-6

| alt | neu | Änderung |
|---|---|---|
| V-0 (trägt die Kette?) | — | ✔ **erledigt, Nullbefund** |
| V-1 (Maß umstellen) | in G-3 aufgegangen | unverändert gültig |
| V-2 (Beiträge neu messen) | **G-2 vorgezogen** | ⚠️ **anschließen vor nachmessen** |
| V-3 (Schwelle) | G-5 | unverändert |
| V-4/V-5/V-6 | G-4/G-6 | unverändert |
| — | **G-7 neu** | Nutzerpunkt 2 vom 29.08. |

---

## G-8 erste Messung: Volumen und Größe als eigenständiger Beitrag — beide NULL

**Nutzerauftrag 29.08.:** *„ja prüfe Volumen und Größe als eigenständigen
Beitrag"*. Werkzeug: `messe_eigenschaft_beitrag.py`, 523 Reihen, Eigenschaft
aus den 252 Handelstagen **vor** dem Stichtag, Rangplatz **quer über alle
Assets desselben Kalendertags** (Marktlage konstant gehalten).

⚠️ **Das ist eine andere Frage als am 23.08.** Damals: verstärkt eine
Eigenschaft den Vorsprung einer **Regel**? Hier: bewegt sich ein Asset mit
hohem Volumen **von sich aus** stärker?

### Der Weg — die erste Zahl war irreführend

| Schritt | Volumen in R | was daran falsch war |
|---|---|---|
| alle Tage | −0,0163 · t **−5,73** | ⚠️ bei Horizont 5 überlappen aufeinanderfolgende Anker zu 80 % — der t-Wert ist überhöht |
| nur nicht überlappende Anker | −0,0153 · t **−2,49** | ⚠️ Zusammenhang bleibt, aber als **Rangmaß** — sagt nichts über den Ertrag |
| Effektgröße als **Mittelwert** in R | **+0,534 R** | ⚠️⚠️ **widerspricht dem Vorzeichen** — größter Einzelwert **+5.296 R**, das Mittel ist unbrauchbar |
| Effektgröße als **Median** | **−0,007 R · t −0,38** | ✔ robust — **null** |

### Das Ergebnis

| | Horizont 5 | Horizont 20 |
|---|---|---|
| **Volumen**, oberstes gegen unterstes Fünftel | **−0,007 R** · t −0,38 · 47 % der Tage | **+0,018 R** · t +0,20 · 46 % |
| **Größe** (Umsatz), dieselbe Messung | **−0,006 R** · t −0,26 | **−0,064 R** · t −0,71 |

✔ **Beide tragen nicht.** Vier Messungen, alle vier von null nicht zu trennen.

⚠️ **Die Lehre, die über diesen Befund hinausgeht:** Beim Volumen war ein
Zusammenhang statistisch nachweisbar (t −2,49) und **trotzdem null in Ertrag**.
Ein Rangzusammenhang ist kein Beitrag, solange er nicht in R beziffert ist.
**Neue Pflichtzeile in jeder Beitragsprüfung: die Effektgröße als Median in R,
nicht als Korrelation und nicht als Mittelwert.**

### Und damit ist das Muster über alle Messungen vollständig

| Art der Aussage | Beispiele | Ergebnis |
|---|---|---|
| **Eigenschaft des Assets** | Volumen · Größe · Volatilität · Liquidität · Alter · Beta · Kapitalisierung | ✖ **trägt keine einzige** |
| **Lage des Assets zum Bewertungszeitpunkt** | Vorfilter H · Tagewahl · Abstand von Bitcoin zum 200-Tage-Schnitt | ✔ **tragen, alle drei** |

⚠️⚠️ **Das ist keine Zufallsfolge, sondern eine Trennlinie** — und sie
bestätigt die Zielvorgabe des Nutzers unabhängig: *„Wir bewerten Zeitpunkte,
nicht Assets."* Sieben geprüfte Eigenschaften tragen nichts, drei geprüfte
Lagemerkmale tragen.

**Folge für G-8:** Weitere Asset-Eigenschaften zu prüfen hat die schlechteste
Aussicht aller offenen Wege. Die einzige Ausnahme mit eigenem Grund bleibt die
**Netzwerk-/Nutzungsaktivität** (ab 18.09.2026) — sie ist keine Marktgröße,
sondern eine Aussage über das Projekt dahinter.

---

## O-1 GEKLÄRT: die Geschwindigkeit ist KEINE Nutzerentscheidung

**Nutzerfrage 29.08.:** *„vorher bitte klären ob es meine Entscheidung sein
sollte oder ob du dies über unsere Dokumentation, bestehende Tradingstandards
und Recherche erheben kannst."*

✔ **Es ist ableitbar — aus zwei unabhängigen Quellen.**

### Quelle 1 — die eigene Doku führt es bereits als Fehler

`Fakten_Entscheidungsmappe.md`, Punkt **C1**, wörtlich:

> **Zieldauer / Haltedauer: Es gibt keine.** `halte_kriterium_bucket` ist eine
> Ablauffrist, `mindestziel_zeitraum_tage_geschaetzt` eine
> Volatilitätsrechnung — beide sind keine Strategieangabe und **widersprechen
> einander**. Gemessene Auflösung 2,6 Tage, Praxis 0,3 Tage.

Und an anderer Stelle: *„Krypto Hebel — Funding wiegt schwerer (Haltekosten je
Tag)."* **Die fehlende Zeitdimension ist im Projekt seit Längerem als
Konstruktionsfehler vermerkt, nicht als offene Geschmacksfrage.**

### Quelle 2 — der Fachstandard

Van Tharp, *Trade Your Way to Financial Freedom*: **Expectunity = Expectancy ×
Opportunity.** Sein eigenes Beispiel:

| System | Gelegenheiten/Jahr | Ertrag je Trade | Ergebnis |
|---|---:|---:|---:|
| 1 | 50 | **1,00 R** | 50 R |
| 2 | 500 | 0,20 R | **100 R** |

⚠️ **System 2 ist doppelt so gut, obwohl jeder einzelne Trade fünfmal
schlechter ist.** Genau das misst „Potential je Zeiteinheit".

**Die Bedingung, unter der das gilt** — und sie ist bei uns erfüllt: das
Kapital muss **knapp** sein. `agent/toepfe.py` begrenzt jeden Topf
ausdrücklich („Ein Topf begrenzt sich SELBST"). Wäre Kapital unbegrenzt, wäre
die Zeit gleichgültig.

✔ **Damit ist „c" keine Entscheidung, sondern die Auflösung eines bekannten
Konstruktionsfehlers nach Fachstandard.** Beide Zahlen werden gebraucht:

| Zahl | Einheit | wofür |
|---|---|---|
| **Potential** | R | ⚠️ die **Schwelle** — lohnt dieser Trade überhaupt? |
| **Potential je Tag** | R/Tag | ⚠️ die **Reihenfolge** — welcher von mehreren zuerst? (Nutzerpunkt 2) |

⚠️ **Eine Warnung, die dazugehört:** Wer nach Ertrag je Tag ordnet, bevorzugt
kurze Trades — und kurze Trades tragen die Gebühren häufiger. Das gehört in die
**Wirtschaftlichkeitsebene** (1,50 %), nie in die Bewertung. Sonst empfiehlt
das System Trades, die sich bewertet lohnen und abgerechnet nicht.

---

## G-2′ GEMESSEN: ein Kandidat, kein Beleg

**Werkzeug:** `messe_lage_beitrag.py`, 523 Reihen, beide Merkmale **stetig**,
Rangplatz quer je Kalendertag, Effektgröße als **Median** (Lehre aus dem
Volumen-Lauf), nur nicht überlappende Anker.

### Erstes Ergebnis

| Merkmal | H 5 | H 20 | H 60 |
|---|---|---|---|
| **Abstand zum 200-Tage-Schnitt** | **+0,0785 R** · t 2,93 | +0,1962 R · t 1,79 | +1,0305 R · t 2,12 |
| Rückgang vom Jahreshoch | +0,0135 · t 0,54 | +0,0693 · t 0,70 | +0,3000 · t 0,82 |
| Negativkontrollen | ✔ alle bei null | ✔ | ⚠️ bei H 60 **+0,3419** — höher als der Befund selbst |

✔ **Rückgang vom Jahreshoch trägt nicht** — in keinem Horizont.

### Die Gegenprüfung entscheidet — und sie fällt gegen den Befund aus

| | H 5 (510 Tage) | H 20 (127) | H 60 (41) |
|---|---|---|---|
| **Vorzeichentest** | p = **0,030** ✔ knapp | p = 0,214 ✖ | p = 0,755 ✖ |
| ohne stärkste 5 % je Seite | +0,058 R · t **3,31** ✔ **stabiler** | +0,144 · t 2,02 | +0,741 · t 2,01 |
| **erste Hälfte der Historie** | +0,1128 · t 2,58 | +0,2721 · t 1,71 | +2,1315 · t **2,47** |
| **zweite Hälfte** | +0,0442 · t **1,43** ⚠️ | +0,1214 · t 0,81 | **−0,0180** · t −0,05 ⚠️⚠️ |

⚠️ **Der Suchpreis ist nicht bezahlt:** 2 Merkmale × 3 Horizonte = **6 Zellen**.
Der einzige signifikante Vorzeichentest (p = 0,030) hält der Korrektur auf
sechs Zellen nicht stand (0,18).

⚠️⚠️ **Und die zeitliche Abschwächung ist der schwerste Einwand:** Über alle
drei Horizonte ist der Effekt in der **jüngeren** Hälfte schwächer, bei
Horizont 60 verschwindet er vollständig (+2,13 → −0,02).

### Urteil

| | |
|---|---|
| ✔ **dafür** | Vorzeichen über **alle drei** Horizonte gleich · Negativkontrollen sauber · **ohne Ausreißer stabiler**, nicht schwächer · Größenordnung plausibel (+0,058 R entspricht ~+2,0 Prozentpunkten, knapp die Hälfte von Vorfilter H) |
| ⚠️ **dagegen** | Vorzeichentest nur bei einem Horizont und dort knapp · **Suchpreis über 6 Zellen nicht bezahlt** · **zeitlich abnehmend**, bei H 60 erloschen |

**➔ Kandidat, kein Beleg.** Er wird **nicht** angeschlossen. Eine Wiederholung
auf unabhängigen Daten wäre der nächste Schritt — aber siehe unten.

---

## ⚠️⚠️ DAMIT GREIFT DER PUNKT DES NUTZERS: Grundlagenanalyse

**Nutzervorgabe 29.08.:** *„Sollten wir weiter keine tragenden Beiträge haben,
müssen wir wieder in eine Grundlagenanalyse einsteigen."*

**Der Stand nach zwei Messläufen an einem Tag:**

| | |
|---|---|
| tragende Beiträge im System | **1** (Vorfilter H) — und der ist binär, episodisch und trägt nur im Altersband 250–499 |
| tragende Beiträge neu belegt | **0** |
| widerlegt an diesem Tag | Volumen · Größe · Rückgang vom Jahreshoch |
| Kandidat ohne ausreichenden Beleg | Abstand zum 200-Tage-Schnitt |

**Die Bedingung ist eingetreten.**

---

# TEIL 3 — BESTANDSAUFNAHME UND DRIFT (29.08.2026)

**Drei Nutzeraufträge:** (1) welche Messungen haben wir, und sind sie u. U.
falsch? (2) welche tragenden Beiträge sind geprüft, ungeprüft, fehlen — und
**haben wir alle Kombinationen geprüft?** (3) Drift-Messung.

---

## A — Aufgabe 1: ⚠️ Zwei Drittel aller Messungen liefen auf der KLEINEN Basis

| Datenbasis | Werkzeuge | Reihen |
|---|---:|---|
| `tradinginfotool.db` — die Watchlist | **32** | ~26–54 |
| `messdaten.db` — die Messbasis | 22 | **523** (485 ≥ 500 Handelstage) |

**Darunter zentrale Messungen des Projekts:**
`messe_kollinearitaet` (die Kombinationsfrage) · `messe_drift` +
`messe_drift_absolut` (die Driftfrage) · `messe_tagewahl_je_eigenschaft` +
`messe_tagewahl_je_symbol` (die Eigenschaften) · `messe_konstellationen` ·
`messe_geometrie` · `messe_marktphasen`.

⚠️⚠️ **Das macht die Nullbefunde nicht falsch — es macht sie untermächtig.**
Kapitel 103.8 hat es selbst beziffert: die Positivkontrolle fand dort **nur
Effekte ab rund 20 Punkten**. Alle realistischen Beiträge liegen darunter —
Vorfilter H trägt **+4,5**. **Ein Nullbefund aus einem Werkzeug, das +4,5 gar
nicht sehen kann, ist keine Antwort.**

**Der Grund für die kleine Basis ist historisch:** BTC hatte bis zum 19.08. nur
ein Jahr Historie. Der Nachlauf hat die Lage verändert, die Werkzeuge sind
nicht nachgezogen worden.

### Was das für die einzelnen Befunde heißt

| Befund | Basis | neu zu bewerten? |
|---|---|---|
| Vorfilter H trägt (+4,5) | 523 Reihen | ✔ nein — auf der großen Basis gemessen |
| Kombination Phase × Band × Geometrie **fällt** | **26 Reihen** | ⚠️⚠️ **ja — untermächtig** |
| Drift trägt nicht (11.08.) | Watchlist | ⚠️ **ja** — hiermit wiederholt, siehe C |
| Eigenschaften tragen nicht (23.08.) | Watchlist (35 Symbole) | ⚠️ **teilweise** — durch den Lauf vom 29.08. auf 523 Reihen **bestätigt**, damit erledigt |
| Volumen/Größe tragen nicht (29.08.) | 523 Reihen | ✔ nein |
| Lage-Beitrag Kandidat (29.08.) | 523 Reihen | ✔ nein |

---

## B — Aufgabe 2: die Kombinationsfrage ist OFFEN, nicht beantwortet

**Ihre Frage, wörtlich:** *„Haben wir alle Kombinationen geprüft, so wie H
zustande kam — das war Glück. Ein Indikator trägt nicht, aber Indikator A und
Parameter B und Parameter C schon?"*

✔ **Sie haben in zwei Punkten recht, und beide sind belegbar.**

### B1 — H IST eine Kombination

`vorfilter.py`, wörtlich: **`H = A und B`**

| | Bedingung |
|---|---|
| **A** *(frei)* | keine Marke über dem Kurs mit ≥ 2 Berührungen unterhalb des **Ziels** |
| **B** *(gedeckt)* | eine Marke unter dem Kurs mit ≥ 2 Berührungen oberhalb des **Stops** |

**Der einzige tragende Beitrag des Systems ist eine Konjunktion.** Das ist kein
Zufall Ihrer Beobachtung, sondern der Sachstand.

### B2 — die Frage wurde schon einmal gestellt, und der Beleg war da

Kapitel 103 (20.08.) prüfte Phase × Driftband × Geometrie, **300 Zellen**:

| | Punkte zum Breakeven |
|---|---:|
| stärkster Einzelhebel | +1,6 |
| wenn sie sich addierten | +9,6 |
| **gemessen kombiniert** | **+17,8** |

**Überadditiv — 200 % dessen, was eine Addition verspräche.** Das Kapitel hielt
fest: *„Das Nutzermodell hat den ersten ernsthaften Beleg bekommen."*

### B3 — und warum er trotzdem fiel, und warum das nicht das letzte Wort ist

| Probe | Schwelle | gemessen | |
|---|---:|---:|---|
| frei gewürfelt | +4,7 | +17,8 | trägt |
| **Zeitblöcke, 40 Läufe** | **+20,5** | +17,8 | **trägt nicht** |

⚠️ **Aber die Positivkontrolle desselben Kapitels:** ein eingepflanzter Effekt
von **+22,1** wurde *gerade noch* gefunden. Wörtlich: *„Alles darunter kann
diese Datenmenge nicht von Zufall unterscheiden."* Und der Grund: **nur 26
Reihen waren lang genug für zwei Blöcke.**

**Heute sind es 485.**

### B4 — „Schritt 2" wurde nie gebaut

Kapitel 103.5 kündigte an: *„Damit hat **Schritt 2** (echte Konjunktion über
Kanäle hinweg: Volatilität × Struktur × Umschlag) eine Grundlage."*

⚠️ **Es existiert kein Werkzeug dafür.** Die systematische Kombinationssuche
über verschiedene Informationskanäle ist **nie durchgeführt worden**.

---

## C — Aufgabe 3: die Drift, wiederholt

**Werkzeug:** `messe_drift_wiederholung.py` — 523 Reihen, ~655.000 Anker,
Block-Bootstrap über 18 Halbjahres-Blöcke (die Marktepisoden).

⚠️ **Mein erster Aufbau war falsch und ich habe ihn selbst gekippt:** Er drehte
Block-Vorzeichen, was Symmetrie voraussetzt — die **Schiefe der Verteilung ist
2,68**. Er hätte „Drift trägt" behauptet, wo nichts steht. Korrigiert zum
Block-Bootstrap.

### Das Ergebnis

| Horizont | **Median** | 95 %-Bereich | **Mittel** | 95 %-Bereich |
|---|---|---|---|---|
| 5 Tage | **−0,077 R** | [−0,154 … −0,001] ✔ | +0,090 R | [−0,086 … +0,374] ⚠️ |
| 20 Tage | **−0,411 R** | [−0,640 … −0,149] ✔ | +0,744 R | [−0,191 … +2,541] ⚠️ |
| 60 Tage | **−1,038 R** | [−1,674 … −0,247] ✔ | +4,242 R | [−0,445 … +12,12] ⚠️ |

| | |
|---|---|
| ✔ **gesichert** | Der **typische** Trade verliert — Median negativ in allen drei Horizonten, mit Block-Bootstrap bestätigt |
| ⚠️ **nicht gesichert** | Der Mittelwert ist positiv, aber über 18 Marktepisoden **nicht von null zu trennen** |

**Anteil positiver Anker:** 46,5 % / 42,0 % / **38,8 %** — je länger gehalten,
desto seltener positiv. **88 % aller 523 Reihen enden tiefer, als sie
begannen.**

### ⚠️⚠️ Der strukturelle Befund, der daraus folgt

```
Median  −0,41 R      Mittel  +0,74 R      Schiefe  2,68
99-%-Quantil  +13,7 R
```

**Der gesamte positive Erwartungswert von Krypto steckt in wenigen extremen
Aufwärtsbewegungen.** Und genau die kappt ein Ziel bei CRV 2,0 — bei einem
Stop von 1 R wird bei +2 R verkauft, während die Quelle des Ertrags bei +13 R
liegt.

⚠️ **Das ist die ernsteste Strukturfrage, die dieser Tag aufgeworfen hat:**
Nicht ob wir den richtigen Zeitpunkt finden, sondern ob **die Zielregel selbst
den Ertrag abschneidet**. Sie ist mit keiner bisherigen Messung beantwortet.

**Für die Drift-Frage im engeren Sinn:** Sie trägt **nicht** — nicht als
Rückenwind für ein Long-Barrierensystem. Der Befund vom 11.08. ist damit auf
523 Reihen und mit korrekter Kontrolle **bestätigt**, nicht widerlegt.

---

## K-1 und K-2 gemessen — beide fallen, und ein Datenfehler kam ans Licht

### K-1: die Kombinationssuche

**Werkzeug:** `messe_konjunktion.py` · 627.180 Anker · 105 Zellen ·
**Suchpreis eingebaut** (Schwelle = Verteilung des Maximums, nicht Einzelzelle).

| | |
|---|---|
| beste Zelle | `trend/rueckgang` bei `unten/oben` → **−0,1955 R** |
| Schwelle (95 % des Maximums, 200 Läufe) | −0,3691 R |
| Urteil erster Ordnung | **trägt** — 0,17 R über dem größten Zufallswert, überadditiv |

**Die Gegenprüfungen kippen ihn:**

| | Befund |
|---|---|
| **2a Kollinearität** | Rohwert-Korrelation **+0,980** — Trend und Rückgang sind fast dieselbe Größe. ⚠️ Meine Ampel war auf die Rangkorrelation (+0,643) justiert und meldete fälschlich „verschiedene Information" |
| **2e Zeitstabilität** | erste Hälfte **+0,42** gegen Basis · zweite Hälfte **+0,003** — ⚠️⚠️ **in der jüngeren Hälfte erloschen** |
| **2d Lage** | Median besser (−0,196 gegen −0,416), **Mittel halbiert** (+0,175 gegen +0,766) |

⚠️ **Und die Positivkontrolle begrenzt, was der Lauf überhaupt aussagen kann:**
gefunden wird ein Effekt erst **ab +0,30 R**. **Vorfilter H trägt rund
+0,135 R.** Besser als Kapitel 103 (dort ~0,60 R), aber immer noch zu stumpf
für die Größenordnung, um die es geht.

➔ **Die Kombinationsthese ist weiterhin weder belegt noch widerlegt.**

### ⚠️⚠️ Der Datenfehler in `messdaten.db`

K-2 lieferte einen Einzelwert von **+80.584 R**. Das ist kein Marktereignis.
Die Prüfung (`pruefe_datenqualitaet.py`) zeigt **Token-Umstellungen, die als
Kurssprung in den Daten stehen**:

| Symbol | Faktor | Datum | was es war |
|---|---:|---|---|
| **LUNA** | **177.400** | 13.–31.05.2022 | Neuausgabe nach dem Kollaps |
| **COCOS** | 1.295 | 19.–23.01.2021 | Redenominierung 1:1000 |
| **DREP** | 108 | 29.03.–02.04.2021 | Token-Swap 1:100 |

**14 von 523 Reihen (2,7 %) haben einen Tagessprung über Faktor 5.**

⚠️ **Betroffen ist jede Messung, die auf MITTELWERTEN beruht.** Median-basierte
Messungen sind robust — glücklicherweise war fast alles heute Median. Die
einzige zu korrigierende Aussage: **das positive Drift-*Mittel* (+0,74 R) ist
mit Token-Umstellungen gerechnet.**

**Behoben** in `messe_zielregel.ergebnisse(bereinigt=True)`: Anker, deren
Vorwärtsfenster einen Sprung über Faktor 5 enthält, fallen weg — chirurgisch,
nicht reihenweise. **Das sind 656 von 634.893 Ankern (0,1 %) — und sie
verändern das Ergebnis um Faktor 6,5.**

### K-2: schneidet die Zielregel den Ertrag ab? — **Nein**

**Bereinigt, 634.237 Anker, gepaart auf demselben Pfad:**

| Variante | Mittel | Median | Treffer |
|---|---|---|---|
| ZIEL 1,0 | +0,0077 | **+1,0000** | 50,4 % |
| **ZIEL 2,0** *(heute)* | +0,0356 | −1,0000 | 34,6 % |
| ZIEL 5,0 | +0,1062 | −1,0000 | 19,9 % |
| OHNE ZIEL | +0,2624 | −1,0000 | 13,7 % |

**Erster Eindruck:** OHNE ZIEL minus ZIEL 2,0 = **+0,2268 R**, Intervall
schließt die Null nicht ein. **Die Gegenprüfung kippt auch das:**

```
Mittel                          +0,2268 R
getrimmt (oberste 1 % weg)      −0,1996 R      <- Vorzeichen dreht
Median                          +0,0000 R
Anteil positiv                   9,8 %
Anteil des obersten 1 % am Mittel: 187,1 %

je Reihe nach MEDIAN:     0 von 523 positiv
ohne die fuenf staerksten: −0,0015 R
Bootstrap ueber die 523 REIHEN: +0,0802 R [−0,0135 .. +0,1951]  NICHT trennbar
```

➔ **Die Zielregel schneidet den Ertrag nicht nachweisbar ab.** In 90,2 % der
Fälle bringt das Weglassen nichts oder schadet; der positive Mittelwert stammt
aus **1 % der Anker**.

⚠️ **Damit korrigiere ich meine eigene Deutung von heute Nachmittag.** Ich
hatte aus drei „konvergierenden" Befunden geschlossen, die Zielregel werfe den
Ertrag weg. **Gemessen trifft das nicht zu.** Was bleibt, ist der saubere
Trailing-Befund vom 26.08. — **das Trailing** schadet in der Aufwärtsphase
(−0,043 R, Intervall ohne Null), **das feste Ziel nicht.** Der Unterschied ist
plausibel: ein nachgezogener Stop schneidet früher ab als ein Ziel bei CRV 2,0.

---

# TEIL 4 — R-B: NEUE INFORMATIONSQUELLEN (30.08.2026)

**Nutzerentscheidung:** *„R-B — neue Informationsquellen außerhalb der
Kursreihe, Werte welche pot. die Anforderung erfüllen, zuletzt erst die
Nachrichten-Thematik, wenn klar ist welche verfügbar sind und wie diese
angewendet werden können."*

## Schritt 1: die Bestandsaufnahme

**Das System kennt bereits 20 externe Quellen** — DefiLlama, CoinGecko,
Binance/Bybit/OKX/Kraken Futures, Deribit, CFTC, SEC, FRED, Finnhub, EIA,
BoJ, GitHub. Entscheidend ist nicht die Anbindung, sondern **ob Daten mit
Historie vorliegen und ob sie je Asset unterscheiden.**

### ⚠️ Die Trennlinie, die alles entscheidet

| | |
|---|---|
| **marktweit** | eine Zahl für den ganzen Markt. Kann sagen *„heute ist ein guter Tag"* — **kann keine Assets unterscheiden**. Das ist Tagewahl, nicht Bewertung |
| **asset-spezifisch** | eine Zahl je Wert. **Nur das erfüllt die Anforderung** (Nutzerpunkt 1 vom 29.08.) |

### Der Bestand

| Quelle | je Asset? | Historie | sofort messbar? |
|---|---|---|---|
| **TVL (DefiLlama)** | ✔ **ja** | **6–8 Jahre je Protokoll** | ✔✔ **JA** |
| Entwickleraktivität | ✔ ja | abrufbar, ungeprüft | zu prüfen |
| Open Interest · Funding · Long-Anteil | ✔ ja | **227 Zeilen seit 14.07.2026** | ✖ zu kurz |
| Börsenzuflüsse · Deribit · CFTC | teilweise | ungeprüft | zu prüfen |
| Fear & Greed | ✖ marktweit | 3.111 Tage, 8,5 Jahre | nur für Tagewahl |
| Renditen 10J / kurz | ✖ marktweit | 2.414 Tage, 9,6 Jahre | nur für Tagewahl |
| Netto-Liquidität | ✖ marktweit | 501 Tage, lückenhaft | eingeschränkt |

⚠️⚠️ **Der zentrale Befund: asset-spezifische Nicht-Kurs-Daten werden praktisch
nicht gesammelt.** Die einzige laufende Sammlung (Open Interest) hat 227 Zeilen.
Alles mit langer Historie ist **marktweit** und kann deshalb genau das nicht,
was gebraucht wird.

## ⚠️⚠️ Die Memory-Aussage „TVL auswertbar ab 18.09.2026" ist falsch

**Gemessen am 30.08. durch Testabruf:**

```
uniswap:  2.858 Tagespunkte,  7,8 Jahre  (2018-11-03 .. 2026-08-29)
aave:     2.294 Tagespunkte,  6,3 Jahre
```

`agent/lebendigkeit.py` ruft `/protocols` ab — **eine Momentaufnahme**, und
sammelt daraus Tag für Tag eine eigene Reihe (`MINDESTREIHE = {"tvl": 30}`).
**DefiLlama liefert unter `/protocol/{name}` die komplette Historie mit.**

✔ **Die Wartezeit auf den 18.09. ist unnötig. TVL ist sofort messbar.**

### Abdeckung

```
DefiLlama kennt 8.149 Protokolle, davon 2.316 mit brauchbarem Kuerzel
Unsere 523 Messreihen:  188 mit TVL  (36 %)
```

Die stärksten: BNB (174 Mrd) · LDO (23,6) · AAVE (17,9) · SSV (12,3) ·
SPK (7,6) · ZRO (7,3) · EIGEN (6,5) · JST (6,3) · ETHFI (5,2) · ENA (4,6).
**Ohne TVL: 335** — Meme-Coins, reine Währungen, alte Werte.

⚠️ **188 Reihen sind kein Nachteil, sondern das Siebenfache dessen, worauf
Kapitel 103 lief** (26). Aber es ist eine **Auswahl** (nur DeFi) — die
Verzerrung gehört in jede Deutung.

## Warum TVL die Anforderung erfüllt

| Kriterium (aus dem Zielbild) | TVL |
|---|---|
| **asset-spezifisch** | ✔ je Protokoll |
| **nicht aus der Kursreihe** | ✔ hinterlegtes Kapital, keine Preisableitung |
| **abgestuft, kein Schalter** | ✔ stetige Größe |
| **Aussage über die LAGE, nicht die Eigenschaft** | ✔ Veränderung ist ein Zustand |
| **sofort messbar** | ✔ 6–8 Jahre |
| **kostenfrei** | ✔ kein Schlüssel, kein Kontingent |

---

## R-B Schritt 1b: die Optionsliste — an der Quelle geprüft (30.08.2026)

**Nutzerauftrag:** *„parallel weiterrecherchieren für weitere verfügbare Werte
und Parameter um Optionen zu haben."*

⚠️ **Alle Zeilen sind durch Testabruf belegt, nicht aus Dokumentation
übernommen.** Werkzeuge: `pruefe_quellen_optionen.py`, `pruefe_quellen2.py`,
`pruefe_coinmetrics_umfang.py`, `pruefe_funding_historie.py`.

### Asset-spezifisch, mit langer Historie, kostenfrei

| Größe | Quelle | unsere Symbole | Historie | Schlüssel |
|---|---|---:|---|---|
| **TVL** (hinterlegtes Kapital) | DefiLlama `/protocol/{slug}` | **188** | 6–8 Jahre | nein |
| **Gebühren / Umsatz** | DefiLlama `/summary/fees/{slug}` | ~188 | **7,8 Jahre** | nein |
| **Funding-Rate** | Binance `/fapi/v1/fundingRate` | ~30 gehandelte | **7,0 Jahre** (8-h-Takt) | nein |
| **Aktive Adressen** | Coin Metrics Community | **66** | bis **11 Jahre** (ETH: 4.049 Punkte) | nein |
| **Transaktionszahl** | Coin Metrics Community | **68** | lang | nein |
| Adressen mit Guthaben | Coin Metrics Community | 63 | lang | nein |
| Umlaufmenge · Emission | Coin Metrics Community | 66 / 63 | lang | nein |
| Hash-Rate | Coin Metrics Community | 10 | lang | nein |

**Coin Metrics Community:** `community-api.coinmetrics.io/v4`, **32 freie
Metriken**, kein Schlüssel, Limit 10 Anfragen / 6 s, Creative-Commons-Lizenz
für nicht-kommerzielle Nutzung.

### Asset-spezifisch, aber NICHT rückwirkend

| Größe | Warum | Folge |
|---|---|---|
| **Open Interest** | Binance liefert nur **30 Tage** (geprüft: 31 Punkte, 31.07.–30.08.) | eigene Sammlung bleibt nötig — die 227 Zeilen seit 14.07. sind der einzige Weg |

### Marktweit — nützlich, aber **nicht** für die Asset-Bewertung

Fear & Greed (8,5 J) · Renditen 10J/kurz (9,6 J) · Netto-Liquidität ·
Stablecoin-Umlauf (422 Coins) · Deribit · CFTC · SEC · FRED.

⚠️ **Sie können keine Assets unterscheiden.** Ihr Platz ist die Tagewahl, nicht
das Potential eines einzelnen Werts.

---

## ⚠️⚠️ ZWEI PROJEKTANNAHMEN SIND GEFALLEN — dieselbe Ursache

| Annahme im Projekt | geprüft am 30.08. |
|---|---|
| „TVL auswertbar **ab 18.09.2026**" | ✖ **falsch** — DefiLlama liefert 6–8 Jahre mit |
| „Positionierung: Wirkung erst **ab 22.10.2026**" | ⚠️ **halb falsch** — Open Interest ja, **Funding-Rate nein: 7,0 Jahre rückwirkend** |

**Die gemeinsame Ursache:** Beide Module (`lebendigkeit.py`,
`positionierung.py`) rufen den **Momentaufnahme-Endpunkt** ab und bauen daraus
Tag für Tag eine eigene Reihe. Dass dieselben Anbieter einen
**Historie-Endpunkt** haben, wurde nie geprüft.

⚠️ **Daraus folgt eine Regel, nicht nur eine Korrektur:**

> **Bevor eine Datenreihe „ab Datum X auswertbar" heißt, wird geprüft, ob die
> Quelle die Vergangenheit mitliefert.** Eine Wartezeit ist erst dann eine
> Tatsache, wenn der Historie-Endpunkt fehlt oder begrenzt ist — wie bei
> Binance Open Interest (30 Tage).

**Das kostet dem Projekt zwei Monate Wartezeit auf die zwei Größen, die als
aussichtsreichste Kandidaten geführt werden.**

---

## R-B Schritt 2 gemessen: TVL und aktive Adressen — beide NULL, aber diesmal belastbar

**Werkzeug:** `messe_fremdgroesse.py` · Abrufe: `hole_tvl_historie.py`,
`hole_fremdreihen.py` · Messdateien: `data/tvl_historie.db`,
`data/onchain_historie.db` — ⚠️ **die Produktions-DB wurde nicht berührt.**

### Die Datenlage, die jetzt vorliegt

| Reihe | Symbole | Tagespunkte | Zeitraum |
|---|---:|---:|---|
| **TVL** | 188 | **261.406** | 2018-02-14 .. 2026-08-30 |
| **Aktive Adressen** | 66 | **203.378** | 2013-01-01 .. 2026-08-29 |

**Das ist mehr Nicht-Kurs-Historie, als das Projekt in zwei Monaten Sammeln
bekommen hätte** — beschafft in zwölf Minuten.

### Der Aufbau, und warum zwei Varianten laufen

| | Frage | Kategorie |
|---|---|---|
| **absolut** | „hat viel TVL / viele Adressen" | **Eigenschaft** — siebenmal widerlegt |
| **Veränderung (30 Tage)** | „wächst gerade" | **Lage** ← der Kandidat |

⚠️ Die absolute Variante fällt in der Auswertung fast überall aus (nur 7–12
Reihen). **Das ist kein Fehler, sondern der Beleg:** ein großes Protokoll
bleibt groß, es wechselt das Terzil nie. Eine Eigenschaft kann innerhalb eines
Symbols gar nicht verglichen werden — genau deshalb ist die Veränderung der
richtige Kandidat.

### Das Ergebnis

| | Horizont 5 | Horizont 20 | Horizont 60 |
|---|---|---|---|
| **TVL**, Veränderung | −0,0136 ⚠️ | +0,0592 ⚠️ | +0,1557 ⚠️ |
| **Adressen**, Veränderung | −0,0237 ⚠️ | +0,0465 ⚠️ | +0,2716 ⚠️ |
| Negativkontrollen | ✔ bei null | ✔ | ✔ |

**Alle sechs Zellen: nicht von null zu trennen.** Positiv sind jeweils rund die
Hälfte der Reihen (82–96 von 175 bzw. 23–33 von 66).

⚠️ Zwei Einzelzellen meldeten „trägt" — TVL/H5 in der zweiten Hälfte (**negativ**)
und Adressen/H60 in der ersten Hälfte. **Bei 15 Zellen je Reihe ist das die
erwartete Zufallsausbeute**, und beide haben keine Entsprechung in der jeweils
anderen Hälfte.

### ⚠️⚠️ Die Positivkontrolle macht den Unterschied

| Reihe | findet einen Effekt ab |
|---|---|
| Aktive Adressen | **+0,10 R** |
| TVL | **+0,10 R** |

**Vorfilter H trägt rund +0,135 R — also ÜBER der Nachweisgrenze.**

✔ **Damit sind das die ersten belastbaren Nullbefunde dieser Serie.** Das
Werkzeug hätte einen Beitrag von der Größe des einzigen tragenden Merkmals
gefunden; es hat keinen gefunden.

**Zum Vergleich:** K-1 hatte eine Grenze von 0,30 R — dort wäre H unsichtbar
geblieben, und der Nullbefund war deshalb keine Antwort. **Hier ist er eine.**

➔ **TVL und Netzwerkaktivität tragen nicht.** Damit ist auch die vierte
Literaturfamilie (Liu/Tsyvinski: Netzwerkfaktoren sagen Renditen voraus)
geprüft — **sie bestätigt sich bei uns nicht**, wie schon die drei anderen.

---

## ⚠️⚠️ DURCHSICHT ALLER MESSUNGEN: haben wir die richtige FORM geprüft?

**Nutzerfrage 30.08., ausgelöst durch den TVL-Nullbefund:** *„verstehe nicht
ganz warum TVL und aktive Adressen keine Aussage liefern, werden diese nicht in
der Praxis angewendet?"* — und daraus: *„ich denke wir sollten alle bisherigen
Messungen prüfen ob wir diese korrekt einordnen und nicht nur am falschen Ende
nur messen."*

**Beide Fragen treffen.** Die Durchsicht ergibt:

| Messung | gemessene Form | Form in der Praxis | |
|---|---|---|---|
| Volumen (29.08.) | Mittel 252 T, Rang quer | Volumenspike (heute/Schnitt) · Turnover (Volumen/MC) | ⚠️ andere Form — als *Eigenschafts*test aber korrekt |
| Größe / Umsatz | Mittel 252 T, Rang quer | dient als Kontrollgröße, nicht als Signal | ✔ passt |
| Abstand 200-Tage-Schnitt | Kurs/Schnitt − 1 | genau so | ✔ passt |
| Rückgang vom Jahreshoch | Kurs/Hoch − 1 | genau so | ✔ passt |
| Umschlag (K-1) | heute / Schnitt 252 T | genau so | ✔ passt |
| Schwankung (K-1) | Spanne heute / Schnitt 252 T | genau so | ✔ passt |
| Drift · Zielregel · Trailing | Ertrag in R | genau so | ✔ passt |
| **TVL** | **Veränderung über 30 T** | **MC/TVL** — Marktkapitalisierung ÷ TVL | ⚠️⚠️ **falsche Form** |
| **Aktive Adressen** | **Veränderung über 30 T** | **NVM** — MC ÷ Adressen² (Metcalfe) | ⚠️⚠️ **falsche Form** |
| **Funding** *(läuft gerade)* | **Veränderung über 30 T** | **Niveau / Perzentil** — hohes Funding = Überhitzung | ⚠️⚠️ **falsche Form** |

### Die Ursache — eine Kategorie hat gefehlt

Ich habe konsequent das Schema angewandt, das sich an den Kursdaten bewährt
hatte:

| Kategorie | Frage | Ergebnis im Projekt |
|---|---|---|
| **Eigenschaft** | „was **ist** dieses Asset" | 7 geprüft, **keine trägt** |
| **Lage** | „wo **steht** es gerade" | 3 geprüft, alle zeigten etwas |
| **Bewertung** | „ist es **teuer oder billig**" | ⚠️⚠️ **nie geprüft** |

**Die dritte Kategorie ist die, auf der die klassische Fundamentalanalyse
ruht** — KGV, Kurs-Buchwert, Dividendenrendite. In Krypto sind ihre
Entsprechungen genau die Kennzahlen, die ich als Rohgröße gemessen habe:

```
MC/TVL   Marktkapitalisierung / hinterlegtes Kapital     unter 0,5 gilt als guenstig
NVT      Marktkapitalisierung / Transaktionswert          Preis gegen Nutzung
NVM      Marktkapitalisierung / (aktive Adressen)^2       Metcalfe
```

⚠️ **Der Unterschied ist nicht klein:** Ein Protokoll kann wachsendes TVL haben
**und trotzdem überteuert sein**. Dann sagt „TVL wächst" das Gegenteil von
„MC/TVL ist niedrig". **Meine Messung konnte den Praxis-Effekt nicht sehen,
weil sie eine andere Größe geprüft hat.**

**Literatur dazu:** *Finance Research Letters* — TVL/MCAP-Bänder als
Vorlaufindikator für Kursbewegungen; Kalichkin — Network Value to Metcalfe.
⚠️ Das ist Literatur, kein Beleg für **unsere** Daten — genau wie bei
Liu/Tsyvinski, die sich bei uns nicht bestätigte.

### Was das für die bisherigen Befunde heißt

| | |
|---|---|
| ✔ **bleibt gültig** | alle Kurs-Messungen — dort war die Form die übliche |
| ⚠️ **unvollständig, nicht falsch** | TVL und aktive Adressen: *„die Veränderung trägt nicht"* stimmt weiterhin. Aber es beantwortet nicht, ob die **Bewertungs**form trägt |
| ⚠️ **rechtzeitig erwischt** | **Funding** — die Messung wäre mit derselben falschen Form gelaufen |

### Was jetzt zu messen ist

Die Daten liegen bereits vollständig vor:

| Kennzahl | benötigt | Stand |
|---|---|---|
| **MC/TVL** | Kurs × Umlaufmenge ÷ TVL | ✔ alles da (Umlaufmenge 66 Symbole, 202.679 Punkte) |
| **NVM** | Kurs × Umlaufmenge ÷ Adressen² | ✔ alles da |
| **NVT** | Marktkapitalisierung ÷ Transaktionswert USD | ✖ **nicht frei verfügbar** — `TxTfrValAdjUSD` liefert 0 Symbole. Ersatz über `TxCnt` möglich, dann aber Anzahl statt Wert |
| **Funding-Niveau** | Perzentil in der eigenen Historie | ✔ sobald der Abruf durch ist |

---

## Die BEWERTUNGSform gemessen: MC/TVL trägt — schmal, aber es trägt

**Werkzeug:** `messe_bewertungskennzahl.py` · Gegenprüfung
`pruefe_mctvl_befund.py`

### ⚠️ Noch ein Formfehler, beim Bauen gefunden

Die erste Fassung maß **je Symbol über die Zeit** („ist Aave gerade günstig für
Aave-Verhältnisse"). Von 19 Symbolen blieben **4** — weil MC/TVL je Symbol
stabil ist und das Terzil fast nie wechselt.

**Die Praxis meint den QUERSCHNITT:** *„kaufe die günstigsten Protokolle"*.
Beide Sichten sind jetzt eingebaut; die ehrliche Einheit bleibt der
Kalendertag (Methodik 2.84).

### MC / TVL — Querschnitt

| Horizont | günstig minus teuer | Bootstrap | |
|---|---|---|---|
| **5** | **+0,0826 R** | [+0,041 .. +0,123] bei Block 250 | ✔ **trägt** |
| **20** | **+0,2714 R** | [+0,027 .. +0,493] bei Block 250 | ✔ **trägt** |
| 60 | +0,6725 R | [−0,169 .. +1,607] bei Block 180 | ⚠️ **fällt** |

**Gegenprüfungen:**

| | |
|---|---|
| **Blocklänge** | H5/H20 halten bei **allen** Längen bis 250 Tage ✔ · **H60 war ein Artefakt** — der 30-Tage-Block war kürzer als das Vorwärtsfenster, genau der Fehler aus Kapitel 103 |
| **Survivorship** | die 19 enden zu **95 %** tiefer, alle übrigen zu 87 % — ✔ **kein Überlebensvorteil**, eher das Gegenteil |
| **Negativkontrolle** | ✔ bei null in allen Horizonten |
| **Zeitstabilität** | ⚠️ **umgekehrtes Muster als sonst**: die **zweite** Hälfte trägt (+0,109 bei H5), die erste nicht. Der Effekt ist aktuell, nicht historisch |
| ⚠️ **Breite** | **nur 12 Symbole je Tag**, Terzile also **~4 Werte**. Das ist die Schwachstelle |

**Die 19 Symbole:** 1INCH · AAVE · ALPHA · BAL · COMP · CRV · FLOW · FUN · GAS ·
KNC · LDO · PAXG · PERP · REP · SNX · SRM · SUSHI · UNI · YFI — fast durchweg
DeFi-Token der 2020er Welle, dazu mit PAXG ein goldgedeckter Token, der dort
sachlich nicht hingehört.

### NVM (Marktkapitalisierung / Adressen²) — trägt nicht

| Horizont | Wert | |
|---|---|---|
| 5 | +0,0258 R | ⚠️ nicht trennbar |
| 20 | +0,1243 R | ⚠️ nicht trennbar (zweite Hälfte allein: +0,160 ✔) |

**Positivkontrolle: findet ab +0,10 R.** Auf **64 Symbolen** — also breiter als
MC/TVL und trotzdem ohne Befund. Metcalfe bestätigt sich bei uns nicht.

### Einordnung

| | |
|---|---|
| ✔ **Die dritte Kategorie ist nicht leer** | MC/TVL ist der erste Kandidat, der Blocklänge, Survivorship, Negativkontrolle **und** Zeitstabilität übersteht |
| ⚠️ **Aber er steht auf 12 Symbolen je Tag** | Terzile mit vier Werten sind zu schmal für eine Entscheidung |
| ➔ **Was fehlt, ist Breite** | Die Begrenzung ist die **Umlaufmenge** — Coin Metrics liefert sie für 66 Symbole, davon 19 mit TVL. CoinGecko `market_chart` liefert die Marktkapitalisierung historisch für alle, kostet aber Kontingent |

---

# ⚠️⚠️ DER FUNDING-BEFUND (30.08.2026) — der erste, der alles übersteht

**Werkzeuge:** `hole_fremdreihen.py` · `messe_funding_niveau.py` ·
`pruefe_funding_befund.py` · `pruefe_funding_monoton.py` ·
`pruefe_funding_survivorship.py`
**Datei:** `data/funding_historie.db` — ⚠️ Produktions-DB nicht berührt.

## Die richtige Form — die Lehre aus der Durchsicht

⚠️ Beinahe wäre auch Funding als **Veränderung** gemessen worden. Die
Praxislesart ist ein **Niveau**:

> Hohes positives Funding = viele Longs zahlen für ihre Position = überhitzte
> Positionierung = **Kontraindikator**.

## Die Datenlage

```
291 Symbole · 361.524 Tagespunkte · 2019-12-19 .. 2026-08-30  (6,7 Jahre)
Messung: 328.311 Anker, 290 Symbole, 2.296 Kalendertage
```

## Das Ergebnis — Querschnitt, niedriges minus hohes Funding

| Horizont | Wert | Bootstrap | erste Hälfte | zweite Hälfte |
|---|---|---|---|---|
| **5** | **+0,0420 R** | [+0,017 .. +0,070] | ✔ +0,067 | ✔ **+0,017** |
| **20** | **+0,1374 R** | [+0,065 .. +0,205] | ✔ +0,183 | ✔ **+0,091** |

⚠️⚠️ **Der erste Befund des Projekts, der in BEIDEN Hälften trägt.** Lage-Beitrag,
K-1 und R-A sind alle genau hier gestorben.

## Alle Gegenprüfungen

| # | Prüfung | Ergebnis |
|---|---|---|
| **V1** | **Mitläufer Momentum?** | Korrelation **+0,002**. Innerhalb der Momentum-Drittel: +0,126 / **+0,188** / +0,152 — überall dasselbe Vorzeichen und dieselbe Größe. ✔ **Funding ist nicht Momentum** |
| **V2** | Blocklänge | trägt bei **90 / 180 / 250 / 400** Tagen ✔ |
| **V3** | Survivorship | Funding-Symbole enden zu **90 %** tiefer, die übrigen zu 84 % — kein Überlebensvorteil. Auf den **ältesten 149** Symbolen: **+0,1330 R** [+0,083 .. +0,187] ✔ |
| **V4** | Monotoner Verlauf | ✔✔ **monoton über alle fünf Fünftel**: −0,095 / −0,093 / −0,129 / −0,175 / **−0,227** |
| | Negativkontrolle | ✔ bei null in allen Läufen |
| | Positivkontrolle | ✔ besteht ab +0,05 R |

⚠️ **Ein eigener Fehler unterwegs:** Die erste V4-Rechnung poolte alle Anker und
zeigte **keinen** Verlauf (alle Fünftel bei ~−0,53 R). Gepoolt mischen sich die
Marktphasen. Je Tag gerechnet — mit festgehaltener Marktlage — ist der Verlauf
sauber monoton. **Der Querschnittsvergleich braucht den Tag als Klammer.**

## Größenordnung

```
Funding (niedrigstes gegen hoechstes Fuenftel, H20):  +0,132 R
Vorfilter H (der bisher einzige Beitrag):             +0,135 R
```

**Etwa gleich groß — aber mit drei Unterschieden zugunsten von Funding:**

| | Vorfilter H | **Funding** |
|---|---|---|
| Form | **Schalter** (ja/nein) | **stetig**, monoton über fünf Stufen |
| Häufigkeit | trifft auf **3,3 %** der Ankertage zu | **jeden Tag für jedes Symbol** mit Perpetual-Kontrakt |
| Zeitstabilität | episodisch, trägt nur im Altersband 250–499 | **beide Hälften der Historie** |

## Was das für die Bewertungsstufe heißt

✔ **Der erste Beitrag, der die Anforderung des Nutzers vollständig erfüllt:**
asset-spezifisch · nicht aus der Kursreihe · **abgestuft statt Schalter** ·
Aussage über die Lage zum Bewertungszeitpunkt · sofort verfügbar.

⚠️ **Grenzen, die dazugehören:**

| | |
|---|---|
| Der Effekt ist ein **Querschnittsvergleich** — er sagt „dieses Asset gegen die anderen heute", nicht „dieses Asset gegen sich selbst" | die Je-Reihe-Sicht wurde nicht geprüft |
| Nur Symbole mit **Perpetual-Kontrakt** | 290 von 523; die gehandelten sind fast alle dabei |
| **Gemessen, nicht gebaut** | keine Zeile Produktionscode berührt |

---

## Funding je Reihe: ⚠️ die Je-Reihe-Sicht ist MARKT-TIMING

**Werkzeuge:** `pruefe_funding_je_reihe.py`, `pruefe_funding_marktphase.py`

**Die Frage:** Trägt Funding auch **innerhalb** eines Assets über die Zeit —
also ohne den Vergleich zu anderen?

| Variante | Wert | |
|---|---|---|
| **roh** (Marktlage nicht kontrolliert) | **+0,1685 R** [+0,091 .. +0,247] | ✔ trägt · 140/220 Symbole |
| **marktbereinigt** (Funding minus Tagesmedian) | **−0,0755 R** [−0,152 .. +0,002] | ✖ nicht trennbar · 97/261 |
| davon erste Hälfte | −0,3102 R | ⚠️ **umgekehrt** |

⚠️⚠️ **Der Effekt verschwindet, sobald der Markt kontrolliert ist.** Wenn das
Funding eines Symbols niedrig steht, ist meist der **ganze Markt** in einer
Phase mit niedrigem Funding — und danach läuft es besser. **Das ist eine
Aussage über den Markt, nicht über das Asset.**

### Ist dann auch der Querschnittsbefund Markt-Timing? — Nein

Der Querschnitt vergleicht Assets **an demselben Tag**, hält die Marktlage also
per Konstruktion fest. Belegt statt behauptet:

| Schnitt | Wert | |
|---|---|---|
| BTC-**Aufwärts**phase (1.390 Tage) | +0,1550 R [+0,046 .. +0,270] | ✔ trägt |
| BTC-**Abwärts**phase (981 Tage) | +0,0536 R [+0,036 .. +0,071] | ✔ trägt |
| Markt-Funding **niedrig** (1.939 T) | +0,0508 R [+0,010 .. +0,081] | ✔ trägt |
| Markt-Funding **hoch** (432 T) | **+0,3923 R** [+0,360 .. +0,437] | ✔✔ **siebenmal stärker** |
| ⚠️ letztes Jahr (337 T) | +0,0697 R [−0,003 .. +0,128] | ⚠️ knapp verfehlt |

✔ **Der Querschnittsbefund trägt in beiden Marktphasen** — er ist kein
Markt-Timing.

⚠️ **Und er ist am stärksten, wenn der ganze Markt überhitzt ist** (+0,39
gegen +0,05). Inhaltlich plausibel: Wenn überall viel für Long-Positionen
gezahlt wird, zahlt sich die Wahl der **am wenigsten** überhitzten Werte
besonders aus.

### ⚠️ Was das für die Nutzeranforderung bedeutet

**Nutzerpunkt 1 vom 29.08.:** *„Die Bewertung jedes potentiellen Trades eines
Assets soll NUR für das EINE Asset erfolgen."*

**Gemessen gilt:** Die Information steckt im **Vergleich**, nicht im Asset
allein. Ein isoliert betrachtetes Asset liefert keine tragfähige Aussage.

✔ **Die Anforderung bleibt trotzdem erfüllbar** — der Rangplatz *ist* eine
asset-eigene Zahl, sie braucht nur den Markt als Bezug:

> „Dieses Asset liegt heute im untersten Funding-Fünftel des Marktes."

Das ist dieselbe Konstruktion wie ein Kurs-Gewinn-Verhältnis gegen den
Branchenschnitt: eine Aussage über **ein** Unternehmen, gemessen an den
anderen. **Der Bezug ist Teil der Aussage, nicht ihr Ersatz.**

---

# TEIL 5 — DAS TRAGFÄHIGE KONSTRUKT (30.08.2026)

> ## ⚠️ DAS ZIEL, vom Nutzer am 30.08. erneut festgehalten
>
> **Empfehlungen werden nicht durch den Takt bestimmt, sondern durch begründete
> „Wahrscheinlichkeit" und „Potential".**

Alles Folgende dient ausschließlich diesem Satz. Jeder Schritt wird daran
gemessen, ob er dem Takt Auslösekraft nimmt und sie einer begründeten Zahl gibt.

## A — Die Datenquellen, Stand nach zwei Messtagen

| Größe | Quelle | Status | Beschaffung |
|---|---|---|---|
| **Funding-Rangplatz** | Binance `fapi/v1/fundingRate` | ✔✔ **trägt, voll geprüft** | 7 Jahre vorhanden; laufend: täglicher Querschnitt |
| **Vorfilter H** | eigene Marken-Rechnung | ✔ trägt, aber Schalter + episodisch | vorhanden |
| MC/TVL | DefiLlama + Coin Metrics | ⚠️ trägt, **nur 19 Symbole** | ✖ harte Grenze (siehe C3) |
| TVL-Veränderung · Adressen · NVM | DefiLlama / Coin Metrics | ✖ null, belastbar | Sammlung überflüssig (siehe C2) |
| Momentum 12-1 · 12-0 · 1M | eigene Kurse | ✖ null, ⚠️ **nur oberhalb 0,20 R** | — |

## B — Die korrekte Anwendung: Form vor Größe

**Die Lehre aus vier Formfehlern an einem Tag:**

| Größe | ✖ falsche Form | ✔ richtige Form |
|---|---|---|
| TVL | Veränderung | MC/TVL — Verhältnis |
| Aktive Adressen | Veränderung | NVM — MC/Adressen² |
| **Funding** | Veränderung · **eigenes Perzentil** | **Querschnittsrang je Tag** |
| Momentum | 20 Tage | 12 Monate ohne den letzten |

⚠️⚠️ **Für Funding ist das betriebsrelevant:** Das System berechnet heute schon
ein `funding_rate_perzentil` (1.909 Einträge, 35 Symbole) — als **Perzentil in
der eigenen Historie**. Genau diese Form wurde am 30.08. gemessen und trägt
**nicht** (marktbereinigt −0,0755 R). **Der Befund hängt am Querschnitt.**

## C — Drei Entscheidungen, die aus den Messungen folgen

### C1 — Funding wird angeschlossen, als abgestufter Beitrag

| Fünftel | Punkte roh | **geschrumpft** (In-Sample halbiert) |
|---|---|---|
| 0 (niedrigstes Funding) | +1,63 | **+0,81** |
| 1 | +1,69 | **+0,85** |
| 2 | +0,49 | **+0,25** |
| 3 | −1,04 | **−0,52** |
| 4 (höchstes) | −2,77 | **−1,39** |

⚠️ **Der Effekt sitzt im Negativen.** Funding ist ein **Warnsignal**, kein
Kaufsignal. Spanne roh +4,40 Punkte — praktisch identisch mit Vorfilter H
(+4,50), aber stetig statt Schalter und täglich statt 3,3 %.

### C2 — Die TVL-Sammlung wird eingestellt oder umgewidmet

Sie läuft seit 20.08. (10 Tage, 168 Symbole) und wäre am **19.09.** auswertbar.
⚠️ **Die Frage ist aber schon beantwortet**: die 6–8-Jahres-Historie zeigt,
dass die TVL-Veränderung nicht trägt — bei einer Nachweisgrenze von 0,10 R,
also unterhalb der Größe, um die es geht. **Drei Wochen Warten fügen nichts
hinzu.**

### C3 — MC/TVL wird NICHT angeschlossen

Es trägt (+0,083 / +0,271 R), aber auf **12 Symbolen je Tag**, Terzile mit
vier Werten. Verbreitern scheitert an der Marktkapitalisierung:
CoinGecko `market_chart?days=max` → **401**, Free Tier liefert nur 365 Tage.
**Keine Kontingentfrage, eine harte Grenze.** Bleibt als Anzeige, nicht als
Beitrag.

## D — Die Wirkungskette: wo greift was, und wann ist das ZIEL erreicht

| Stufe | was sie tut | wirkt heute? | nach G-2′ | Ziel erreicht? |
|---|---|---|---|---|
| **G-2′** Beitrag anschließen | die Zahl wird **richtig** | Mail | Mail | ✖ **nein** |
| **G-4** Potential anschließen | die Zahl wird **verrechnet** | — | — | ✖ nein |
| **G-5** Schwelle | die Zahl **entscheidet** | — | — | ⚠️ Ihre Entscheidung |
| **G-6** verwerfen statt zählen | **der Takt verliert die Auslösekraft** | — | — | ✔ **ja, hier** |

⚠️⚠️ **G-2′ allein ändert das Verhalten nicht.** `wahrscheinlichkeit.py` fließt
heute ausschließlich in die Mail. Wer nach G-2′ aufhört, hat eine richtigere
Zahl — und denselben Takt als Auslöser. **Das Ziel ist erst mit G-6 erreicht.**

## E — Folgeschritte für die anderen Assetklassen

**Erst wenn es für Krypto funktioniert.** Die Übertragung ist aber schon
absehbar, weil die **Kategorien** übertragbar sind:

| Kategorie | Krypto | **Aktien / ETF** |
|---|---|---|
| Eigenschaft | Größe, Volumen, Alter | Branche, Indexzugehörigkeit |
| Lage | Abstand zum Schnitt, H | dieselben — Kursdaten sind dieselben |
| **Bewertung** | **MC/TVL**, NVT, NVM | ⚠️ **KGV · Kurs-Buchwert · Dividendenrendite · EV/EBITDA** |
| Positionierung | **Funding** ✔ | Leerverkaufsquote · Put-Call-Verhältnis · CFTC-Positionierung |

**Was für Aktien dafür spricht:** Die Bewertungskategorie ist dort **besser
belegt als irgendwo sonst** — KGV und Kurs-Buchwert sind die
Standardfaktoren der Finanzliteratur (Fama/French). Und bei Krypto war es
genau diese Kategorie, die als einzige etwas lieferte.

**Datenlage:** `finnhub.io` und `sec.gov`/`data.sec.gov` sind bereits
angebunden — ⚠️ ob sie Fundamentaldaten mit Historie liefern, ist **ungeprüft**
und wäre der erste Schritt, wenn Krypto steht.

**Reihenfolge:** F-1 Krypto abschließen (G-2′ … G-6) → F-2 Datenlage Aktien
prüfen → F-3 dieselbe Messkette auf KGV/KBV → F-4 anschließen.

---

## ⚠️⚠️ WIRKSAMKEIT STATT MERKMALSMESSUNG — die Korrektur, die alles neu ordnet

**Nutzerkorrektur 30.08., wörtlich:** *„du sollst nicht alte messungen
wiederholen sondern diese auf **Wirksamkeit bei praktischer Anwendung** prüfen
— halte dich daran sonst misst du wieder nur unser System."*

**Sie trifft, und sie betrifft jeden Befund dieser Serie.** Alle Messungen
fragten *„trägt das Merkmal in MEINEM Aufbau?"* — Querschnitt, Terzile, Median
in R. Das ist der Messrahmen, nicht die Anwendung.

### Der Beleg an Funding — dieselbe Größe, zwei Zahlen

| | Wert |
|---|---|
| **Merkmal** — unterstes gegen oberstes Fünftel | **+0,1320 R** |
| **Regel** — „kein Einstieg ab Funding-Rangplatz 80 %" | **+0,0242 R** |

**Faktor 5,5.** Arithmetisch zwingend: Eine Regel, die 20,6 % sperrt, kann
höchstens diesen Anteil des Merkmalsunterschieds heben — und nur, wenn die
Gesperrten wirklich schlechter waren. **Sie waren es:** −0,235 R gegen
−0,158 R.

```
NETTO mit Regel minus ohne   +0,0242 R  [+0,0078 .. +0,0370]   traegt
  erste Haelfte              +0,0314 R  traegt
  zweite Haelfte             +0,0171 R  ⚠️ nicht trennbar
```

### Vorfilter H, nach derselben Regel gelesen — ohne neue Messung

Die Zahlen liegen vor, sie wurden nur nie so gelesen. **Betriebszahl aus dem
NB-Export vom 29.08.:**

```
vorfilter_schatten: 617 Zeilen -> h: 31 · nicht_h: 582 · nicht bestimmbar: 4
                                 H trifft in 5,0 % der Faelle zu
```

### Die Gegenüberstellung, die zählt

| | Einzelwirkung | Häufigkeit | **effektiv je Signal** |
|---|---|---|---|
| **Vorfilter H** | +4,5 Punkte | **5,0 %** | **≈ 0,23 Punkte** |
| **Funding-Regel (80 %)** | +0,8 Punkte | **100 %** | **≈ 0,80 Punkte** |

⚠️⚠️ **Der scheinbar viel kleinere Beitrag wirkt rund dreieinhalbmal so
stark** — nicht weil er größer ist, sondern weil er **immer** greift.

**Das sieht man in keiner Merkmalsmessung.** H stand zwei Wochen lang als „der
tragende Beitrag" da, weil +4,5 neben +0,8 größer aussieht.

⚠️ **Und H als Sperr-Regel wäre keine Verbesserung, sondern eine andere
Strategie:** „nur H-Einstiege" sperrt **95 %** aller Signale. Das steht so
schon in `vorfilter.py` — *„aus 24 Eröffnungen würde ungefähr eine"* — wurde
aber nie neben die Beitragszahl gestellt.

### Die Regel für alles Weitere

> **Kein Merkmalsbefund wird zur Empfehlung, bevor er als REGEL gerechnet ist.**
> Drei Zahlen, und nur die dritte ist die Wirkung:
> **wie viele Fälle · waren die wirklich schlechter · was bleibt netto.**
> Und: **die Häufigkeit gehört immer dazu** — „+4,5 Punkte" ohne „auf 5 % der
> Fälle" ist eine irreführende Zahl.

**Folge für die fünf offenen Kandidaten** (Turnover · Amihud · OI/MC ·
Volatilitäts-Risikoprämie · Momentum-Varianten): Die Liste bleibt, **die
Prüfform ändert sich** — nicht „trägt das Merkmal", sondern „was ändert die
Regel".

---

# TEIL 6 — DIE FÜNF KANDIDATEN ALS REGEL (30.08.2026)

**Werkzeuge:** `messe_regel_wirksamkeit.py` (gemeinsamer Maßstab) ·
`messe_kandidaten_als_regel.py` · `pruefe_regel_trennschaerfe.py` ·
`pruefe_turnover_befund.py`

⚠️ **Kein Merkmal wurde gemessen. Jede Zeile ist eine Regel:** *„kein Einstieg
im obersten/untersten 20 %"* — gepaart auf denselben Ankern, Bootstrap über
Blöcke von Kalendertagen.

## Die eingebaute Kontrolle

Funding ist bereits als Regel gerechnet (+0,0242 R). Der gemeinsame Maßstab
liefert **+0,0244 R** — ✔ das Werkzeug reproduziert.

## Das Ergebnis

| Kandidat | Symbole | gesperrt | **Netto-Wirkung** | Urteil |
|---|---:|---:|---|---|
| **Turnover** (Volumen/Umlaufmenge) | 66 | 21,2 % | **+0,0616 R** [+0,015 .. +0,114] | ⚠️ **trägt, aber Vorbehalt** |
| **Funding** *(Kontrolle)* | 290 | 20,6 % | **+0,0244 R** [+0,008 .. +0,037] | ✔ trägt |
| Amihud-Illiquidität | 523 | 20,4 % | −0,0016 R | ✖ null |
| Amihud, Gegenrichtung | 523 | 20,2 % | +0,0115 R | ✖ null |
| Momentum 12-1 | 523 | 20,2 % | −0,0008 R | ✖ null |
| OI / Marktkapitalisierung | — | — | — | ✖ **nicht messbar** (Binance: 30 Tage) |
| Volatilitäts-Risikoprämie | — | — | — | ✖ **nicht messbar** (nur BTC/ETH) |

## ⚠️⚠️ Die Positivkontrolle war zweimal falsch gebaut

| Anlauf | Konstruktion | warum sie nichts belegte |
|---|---|---|
| 1 | Effekt auf die **Behaltenen** pflanzen | die machen 80 % des Vergleichsmedians aus — der Effekt hob sich selbst auf |
| 2 | Effekt auf die **Gesperrten** pflanzen | der Median (50. Perzentil) reagiert kaum, wenn die äußeren 20 % weiter nach außen rutschen |
| **3** | **Merkmal bekannter Güte erzeugen** (`−Ziel + Rauschen·k`) | ✔ misst, welche Merkmalsgüte die Regel überhaupt findet |

**Ergebnis der richtigen Kontrolle:**

| Korrelation Merkmal ↔ Ausgang | Wirkung der Regel |
|---|---|
| −0,320 | +0,1162 R |
| −0,164 | +0,0599 R |
| **−0,082** | **+0,0343 R** ← noch klar gefunden |

```
echte Korrelationen:   Amihud +0,0076      Momentum 12-1 +0,0030
```

✔ **Die Messung findet Korrelationen bis 0,08 — Amihud und Momentum haben
zehnmal weniger. Beide Nullbefunde sind echt, nicht Blindheit.**

## Turnover: gegengeprüft, und der Vorbehalt bleibt

| | |
|---|---|
| **Blocklänge** | trägt bei 90 / 180 / 250 / 400 Tagen ✔ |
| **Mitläufer Funding?** | Korrelation −0,158; trägt **innerhalb** niedriger (+0,047) *und* hoher (+0,044) Funding-Schicht → ✔ **eigenständiger Beitrag** |
| **Zeitstabilität** | zweite Hälfte **+0,0529** ✔ · erste Hälfte nicht trennbar |
| ⚠️⚠️ **Survivorship** | **71 %** der 66 Turnover-Symbole enden tiefer — gegen **90 %** bei den übrigen 457 |

⚠️ **Der Auswahleffekt ist real und hat einen klaren Grund:** Coin Metrics
führt Umlaufmengen nur für etablierte Werte. Die 66 sind die Überlebenden.

**Was das entkräftet und was nicht:** Der Befund ist ein *Querschnitts*vergleich
**innerhalb** dieser 66 — der Bias ist allen gemeinsam und verzerrt den
Vergleich untereinander nicht zwangsläufig. **Aber die Übertragbarkeit auf die
übrigen 457 ist offen**, und genau die würden im Betrieb mitbewertet.

➔ **Turnover ist ein Kandidat mit ungeklärter Reichweite, kein gesicherter
Beitrag.** Funding bleibt der einzige, der auf breiter Basis ohne Vorbehalt
trägt.

---

# TEIL 7 — DAS KONZEPT (30.08.2026)

> **ZIEL:** Empfehlungen werden nicht durch den Takt bestimmt, sondern durch
> begründete **Wahrscheinlichkeit** und **Potential**.

## 1. Was aufgenommen wird — und warum

### Funding-Niveau ✔

Alle sechs Bedingungen aus **R-R8** erfüllt. Wirkung als Regel **+0,0244 R**
(≈ **+0,8 Punkte**) auf **100 %** der Signale, 290 Symbole, 6,3 Jahre.

### Turnover ✔ — der Vorbehalt ist ausgeräumt

**Nutzervorgabe:** *„aufnehmen wenn die Recherche und Messungen ausreichend
sind."* Die offene Frage war Survivorship (71 % gegen 90 %). **Geprüft:**

| | Wirkung |
|---|---|
| die **schwächeren** 33 der 66 Symbole | **+0,0471 R** [+0,031 .. +0,064] ✔ trägt |
| die stärkeren 33 | +0,0725 R [+0,021 .. +0,130] ✔ trägt |

**Die Regel wirkt auch dort, wo die Werte schlecht liefen.** Der Auswahleffekt
erklärt den Befund nicht.

### Und sie ersetzen einander nicht

Auf gemeinsamer Basis (71.022 Anker, 2.362 Tage):

| | Wirkung |
|---|---|
| nur Turnover | +0,0334 R |
| nur Funding | +0,0360 R |
| **beide** | **+0,0638 R** |

**92 % additiv — zwei eigenständige Beiträge.** ⚠️ Zusammen sperren sie
**37,3 %** der Einstiege statt je 20 %.

### Nicht aufgenommen

| | Grund |
|---|---|
| MC/TVL | 12 Symbole je Tag — zu schmal; CoinGecko `days=max` → 401 |
| Amihud · Momentum · TVL · Adressen · NVM · Drift · Zielregel | null, **belastbar** (Trennschärfe 0,08 Korrelation) |
| Vorfilter H | bleibt, ⚠️ aber **B3 offen** — nie als Regel gerechnet |

## 2. ⚠️ Die anderen Assetklassen — geprüft, und der Aufwand ist NICHT gering

**Nutzervorgabe:** *„mitbauen, wenn der Aufwand für Aktien, ETF und Rohstoffe
gering ist."* **Er ist es nicht — aus einem Grund, der sich nicht umgehen lässt.**

**Die Watchlist am Notebook (NB-Export 29.08.):**

| Klasse | Symbole | Messbasis | Nicht-Kurs-Daten |
|---|---:|---|---|
| **krypto** | **44** | ✔ 523 Reihen | ✔ Funding · Turnover |
| etf | **7** | ✖ | ✖ |
| rohstoffe | **4** | ✖ | ✖ |
| aktien | **2** | ✖ | ✖ |

⚠️⚠️ **Der Ansatz ist ein QUERSCHNITTSvergleich — bei 7 ETFs oder 2 Aktien gibt
es keinen Querschnitt.** Terzile aus zwei Werten sind keine Terzile. Das ist
keine Aufwandsfrage, sondern eine Grenze der Methode auf dieser Watchlist.

**Dazu fehlt beides, was man bräuchte:**
`messdaten.db` enthält **ausschließlich Krypto**; eine Fundamentaldaten-Tabelle
(KGV, Kurs-Buchwert) existiert nicht — Finnhub und SEC sind im Code angebunden,
speichern aber nichts.

### Was konzeptionell trotzdem mitgedacht ist — zum Aufwand null

`wahrscheinlichkeit.Beitrag` hat **bereits ein Feld `klassen`**. Funding und
Turnover werden mit `klassen=("krypto",)` registriert; für jede andere Klasse
meldet die Rechnung von sich aus *„auf X nie gemessen"*. **Die Struktur trägt
die Erweiterung schon — es fehlen nur die Daten.**

**Folgeschritte, wenn Krypto steht:**

| | Schritt | Bedingung |
|---|---|---|
| F-1 | Krypto abschließen (G-2′ … G-6) | — |
| F-2 | Messbasis für Aktien/ETF aufbauen | ⚠️ **braucht einen breiten Querschnitt**, nicht 9 Symbole — z. B. Index-Konstituenten |
| F-3 | Fundamentaldaten prüfen (Finnhub/SEC: liefern sie Historie?) | ungeprüft |
| F-4 | Dieselbe Messkette auf **KGV · Kurs-Buchwert** — die Bewertungskategorie ist dort **besser belegt als irgendwo** (Fama/French) | nach F-2/F-3 |

## 3. Der Bauplan

| # | Schritt | Datei | Wirkung |
|---|---|---|---|
| **1** | Funding- und Turnover-**Rangplatz je Tag** ermitteln | **neu** `agent/marktrang.py` | Datengrundlage |
| **2** | `Beitrag` um **Stufen** erweitern (heute nur ein Punktwert, H als Sonderfall) | `wahrscheinlichkeit.py` | Struktur |
| **3** | Beide Beiträge registrieren, `klassen=("krypto",)` | `wahrscheinlichkeit.BEITRAEGE` | die Zahl wird richtig |
| **4** | Parameter durchreichen | `rollen_lauf.py:1758` | additiv |
| **5** | Tägliche Beschaffung | Scheduler | ⚠️ Funding-Sammlung steht seit 19.07. |
| **6** | Prüfungen + Simulation | `Pruefungen/`, `simuliere_kette.py` | — |

⚠️ **Kalibriert wird mit den WIRKSAMKEITSzahlen** (+0,8 Punkte), nicht mit den
Merkmalszahlen (+4,4). Sonst behauptet das System eine Wirkung, die es nicht
hat — **R-R8 B3**.

⚠️⚠️ **Und das Ziel ist damit noch nicht erreicht.** Nach Schritt 6 ist die
Zahl richtig und steht in der Mail. **Der Takt löst weiterhin aus.** Erst
**G-6** (verwerfen statt zählen) nimmt ihm die Auslösekraft.

---

## G-2′ Schritt 1 GEBAUT: `agent/marktrang.py` (30.08.2026)

**Was es tut:** ermittelt je Symbol den **Querschnittsrang** von Funding und
Turnover — und **sperrt nichts**. Wie `vorfilter.py` für H: markieren, nicht
verhindern. Die Wirkung ist G-6 und eine eigene Entscheidung.

### Zwei Fehler, die vorher gefunden wurden

**(1) ⚠️ BTC und ETH fehlten im Funding-Abruf.** Große Werte haben neben dem
Perpetual auch Quartalskontrakte (`BTCUSDT_261225`) — **die haben keine
Funding-Rate**, und mein Filter nahm den letzten Treffer. Betroffen: genau
**BTC und ETH**, also die zwei wichtigsten.

✔ **Behoben** (`contractType == "PERPETUAL"`), nachgeholt, und der Befund
**hält: +0,0246 R** statt +0,0244. Die Prüfung war trotzdem nötig — ein
Befund ohne BTC und ETH wäre nicht vorzeigbar gewesen.

**(2) Die Umlaufmenge kommt im Betrieb aus einer anderen Quelle** als in der
Messung — CoinGecko `circulating_supply` gegen Coin Metrics `SplyCur`. Die
Definitionen unterscheiden sich (Burns; bei BNB **29 %**).

✔ **Geprüft:** Rangkorrelation **+0,967**, und die Sperrentscheidung wäre bei
**33 von 33** Symbolen identisch. Der Wechsel ist unkritisch.

### Die Bauform

| | |
|---|---|
| **Datenquellen** | Binance `premiumIndex` (885 Einträge) und CoinGecko `coins/markets` (250 Coins) — **je EIN Aufruf für alle Symbole** |
| **Kontingent** | 1 CoinGecko-Call je Lauf = **0,4 %** des Monatskontingents |
| **Querschnitt statt Historie** | der Rang wird über die heute bewerteten Symbole gebildet — die Je-Reihe-Sicht trägt nachweislich nicht (−0,0755 R marktbereinigt) |
| **Mindestquerschnitt 15** | darunter kein Fünftel: bei 10 Werten enthielte es zwei |
| **Fehlt eine Größe** | `None`, **nie 0** — dieselbe Regel wie `h = None` bei H |
| **Netzfehler** | wird geloggt, die Kette läuft weiter — eine Bewertung darf keinen Lauf abbrechen |

### Gegenprüfung an echten Daten

```
44 Watchlist-Symbole, 2 Aufrufe insgesamt
  Funding-Rang :  37   (mehr als die 27 der Historie-DB - premiumIndex ist live)
  Turnover-Rang:  29
```

**Prüfung:** `pruefe_marktrang.py` — **18 Prüfungen, 0 FEHL.** Darunter die
drei, die im Betrieb still bleiben würden: fehlender Wert sieht aus wie
geprüftes Nein · zu dünner Querschnitt liefert trotzdem Fünftel · die Mailzeile
wird zur Empfehlung statt zur Tatsache.

### Noch NICHT getan

| | |
|---|---|
| Schritt 2 | `Beitrag` um **Stufen** erweitern — heute kennt er nur einen Punktwert, H ist Sonderfall |
| Schritt 3 | beide Beiträge registrieren, `klassen=("krypto",)` |
| Schritt 4 | Parameter in `rollen_lauf.py:1758` durchreichen |
| Schritt 5 | tägliche Beschaffung im Scheduler |
| Schritt 6 | Simulation |

⚠️ **`marktrang.py` hat bis hierher keinen Aufrufer.** Es ist gebaut und
geprüft, aber nicht verdrahtet — genau wie es sein soll, bevor das Konzept
für Schritt 2 steht.

---

# TEIL 8 — KONZEPT SCHRITT 2: abgestufte Beiträge (30.08.2026)

**Nutzervorgabe:** *„ich denke ein Konzept reicht bei dieser kritischen
Thematik nicht, sondern sollte detailliert getestet und simuliert werden, um
weitere KERN-Umbauten oder Probleme zu verhindern. also Schritt für Schritt."*

## Warum der Eingriff kritisch ist

`wahrscheinlichkeit.rechne()` liefert eine Zahl, die **in jeder Mail steht**.
Drei Aufrufer hängen daran:

| Aufrufer | Aufruf |
|---|---|
| `rollen_lauf.py:1759` | `saetze(crv=, stop_relativ=, klasse=, h=)` |
| `potential.py:155` | `rechne(...)` |
| `pruefe_pakete.py:12465` | Prüfungen |

⚠️ **Und H ist heute über den NAMEN verdrahtet:**
`if b.zustand == "traegt" and b.name.startswith("Vorfilter H")`. Ein zweiter
Sonderfall daneben würde die Struktur zerfallen lassen.

## Die Zerlegung — sechs Teilschritte, jeder einzeln prüfbar

| # | Teilschritt | Prüfung | Risiko |
|---|---|---|---|
| **2a** | **Bitgleichheitstest bauen** — 432 Fälle einfrieren | ✔ **erledigt**, verifiziert | keins |
| **2b** | `Beitrag` um `merkmal` und `stufen` erweitern, **ohne** Verhalten zu ändern | 2a muss 0 FEHL bleiben | gering |
| **2c** | H vom **Namen** auf `merkmal="h"` umstellen | 2a bitgleich | ⚠️ mittel |
| **2d** | Parameter `merkmale: dict` einführen, `h=` bleibt als Rückfall | 2a bitgleich · alte Aufrufer unverändert | gering |
| **2e** | Funding und Turnover registrieren, `zustand="noch_nicht"` | 2a bitgleich — **noch trägt nichts** | keins |
| **2f** | Beiträge scharf: `zustand="traegt"` mit den Wirksamkeitszahlen | ⚠️ **2a ändert sich ABSICHTLICH** — neue Referenz mit Begründung | ⚠️ hoch |

⚠️ **Nur 2f verändert eine Zahl.** 2b bis 2e sind reine Struktur — der
Bitgleichheitstest muss dort **unverändert 0 FEHL** liefern. Das ist der
eigentliche Schutz: Wenn er bei 2c anschlägt, ist der Umbau falsch, und man
sieht es sofort statt in der nächsten Mail.

## Die Zielstruktur

```python
@dataclass(frozen=True)
class Beitrag:
    name: str
    zustand: str
    punkte: float = 0.0        # Schalter: ein Wert
    stufen: tuple = ()         # abgestuft: ein Wert je Fuenftel
    merkmal: str = ""          # Schluessel in `merkmale` - statt Namensabfrage
    quelle: str = ""
    warum: str = ""
    klassen: tuple = ()
```

**Und der Sonderfall wird zum Regelfall:**

```python
rechne(..., merkmale={"h": True, "funding_fuenftel": 4})
```

- `merkmal` leer → trägt aus dem Zustand heraus (wie heute)
- `merkmal` gesetzt, Wert `None` → **`zustand="nie"`**, nie 0 als Nein
- `stufen` gesetzt → Punkte je Fünftel statt eines Werts

## Die Kalibrierung von 2f — die Zahlen stehen fest

⚠️ **Mit den WIRKSAMKEITSzahlen, nicht den Merkmalszahlen** (R-R8 B3).

Die Regel-Wirkung ist **+0,0246 R** für Funding bei 20,6 % gesperrt. Umgerechnet
auf die Quote (Faktor 1/(1+CRV), bei CRV 2,0 also 1/3): **+0,8 Punkte** über
alle Signale. Auf Fünftel verteilt, geschrumpft und so, dass die Summe über
alle Fünftel diese 0,8 Punkte ergibt — **nicht die 4,4 der Merkmalsmessung.**

## Simulation vor 2f

**Zwei Stufen, wie vom Nutzer vorgegeben:**

| | |
|---|---|
| **klein** | `rechne()` mit allen Fünftel-Kombinationen: verschiebt sich die Quote wie erwartet, bleibt sie in [0,1], kippt kein Vorzeichen |
| **historisch** | `simuliere_kette.py` auf echten Signalen: wie viele Mails ändern sich, um wie viel, und **wie viele Empfehlungen kippen** |

⚠️ **Erst nach beiden Simulationen wird 2f gebaut.** Und selbst dann sperrt
noch nichts — das bleibt G-6.

---

## 2b GEBAUT: `Beitrag` kann abgestuft sein (30.08.2026)

**Rein additiv — kein Verhalten hat sich geändert.** Das war der Zweck.

### Was dazukam

```python
stufen: tuple = ()    # abgestuft: Punkte je Fuenftel 0..4
merkmal: str = ""     # Schluessel in `merkmale`; leer = kein Eingabewert
```

Dazu ein `__post_init__`, das **Widersprüche beim Import** auffallen lässt
statt im Betrieb:

| Fall | Meldung |
|---|---|
| `stufen` mit vier Werten | *„braucht genau 5 Werte (ein Fünftel je Rangplatz)"* |
| `punkte` **und** `stufen` | *„dann wäre unklar, welcher Wert gilt"* |
| `stufen` ohne `merkmal` | *„der Wert käme nie an"* |

### Prüfung

| | |
|---|---|
| **Bitgleichheit** | **432 Fälle, 0 FEHL** — nichts hat sich verschoben |
| neue Felder | 7 Prüfungen, alle grün |

### Gegenprüfung

| | |
|---|---|
| die drei echten Aufrufer | `potential.rechne()` ✔ · `wahrscheinlichkeit.saetze()` ✔ (13 Zeilen) · `rollen_lauf` importierbar ✔ |
| **Gesamtsuite** | **1.772 Prüfungen, ALLE BESTANDEN** (vorher 1.765) |

### Dauerhaft statt einmalig

Die sieben Prüfungen liegen als **Paket „Stufen"** in `pruefe_pakete.py` —
sie laufen ab jetzt bei jedem Suite-Durchlauf mit. Darunter die eine, die den
nächsten Schritt absichert:

> **„Vorfilter H trägt unverändert 4,5 Punkte"** — Schritt 2b darf H **nicht**
> umstellen. Das ist 2c, und dazwischen liegt der Bitgleichheitstest.

---

# ⚠️⚠️ TEIL 9 — WO SITZT WAS? Die Klärung vor 2c (30.08.2026)

**Nutzerfrage:** *„Vorher prüfe ob und wie dies konzeptionell zu sehen ist — wo
sitzt H und die weiteren Bewertungsstufen … wie soll das zusammenspielen mit
dem Nachfilter bzw. der Selektion, was letztendlich als Empfehlung per Mail bei
mir ankommt — sind diese Punkte geklärt?"*

**Antwort: Nein, sie waren es nicht.** Die Prüfung am Code fördert einen
Konstruktionsfehler zutage, der vor jedem weiteren Bauschritt auf den Tisch
gehört.

## Der tatsächliche Ablauf, mit Zeilennummern

| Zeile | Was | Wirkt es? |
|---|---|---|
| 409 | Trichter startet (`RG.Durchlauf`) | — |
| 498 | **Rolle A** — Marktlage, 1 Aufruf je Umlauf | — |
| 540 | **Auswahl** `auswahl.waehle()` — die besten `k` je Gruppe | ✔ **sperrt** |
| 1029–1035 | Auswahl-Gate im Trichter | ✔ **sperrt** |
| **1108** | **Rolle BC** — das Urteil, der teuerste Schritt | — |
| 1517 | `ER.rechne()` — Geometrie, Stop, Ziel, Betrag | ✔ sperrt bei Unrechenbarkeit |
| **1596** | **`TB.bewerte()` — Stufe 11, „der Entscheider"** | ⚠️ **zählt nur** (`NUR_ZAEHLEN`) |
| 1607 | *„--- Die Mail ---"* | — |
| **1741** | **`_VF.bewerte()` — Vorfilter H** | ⚠️ **nur Markierung** |
| **1759** | **`_WK.saetze()` — die Wahrscheinlichkeit** | ⚠️ **nur Mailtext** |
| 1795 | `SM.baue_mail()` | — |

## ⚠️⚠️ Der Befund: es gibt ZWEI Bewertungen, die nichts voneinander wissen

| | Stufe 11 (Zeile 1596) | Wahrscheinlichkeit (Zeile 1759) |
|---|---|---|
| **rechnet mit** | Trefferbilanz **(leer: 96 von 2.313)** + Gebühren-Breakeven | Basisrate + Beiträge (**H**) |
| **Maßstab** | `(1+Kosten)/(1+CRV)` — **1,50 % Gebühren** | gebührenfrei, Referenz 0,30 % |
| **Wirkung** | bucht „verloren", läuft weiter | Text in der Mail |
| **Zeitpunkt** | **vor** dem Mailbau | **nach** dem Mailbau |

⚠️ **Stufe 11 entscheidet, ohne H zu kennen** — H wird 145 Zeilen später
gerechnet. Käme Funding als Beitrag dazu, säße es an derselben Stelle: **nach**
der Entscheidungsstufe. Es könnte per Konstruktion nie etwas verwerfen.

⚠️ **Und die Maßstäbe widersprechen sich:** Stufe 11 misst mit
Bitpanda-Gebühren, die Wahrscheinlichkeit gebührenfrei — genau die Trennung,
die am 25.08. festgelegt wurde und die Stufe 11 verletzt.

## Die drei Filterebenen, sauber getrennt

| Ebene | wo | Frage | wirkt |
|---|---|---|---|
| **Selektion** | Zeile 540, **vor** dem Modell | *welche Assets beurteilen wir heute?* | ✔ ja — größter Filter |
| **Trichter** | Stufen 1–10 | *ist dieser Fall überhaupt bearbeitbar?* | ✔ ja |
| **„Nachfilter"** | Stufe 11 + H + Wahrscheinlichkeit | *ist es ein guter Trade?* | ✖ **nein — keine davon** |

**Der Name „Nachfilter" trifft es: Alles, was den Trade inhaltlich bewertet,
läuft nach der teuersten Stufe und filtert nichts.**

## Was daraus für 2c und alles Weitere folgt

**2c selbst ist davon unberührt** — es macht aus dem Namensvergleich
(`b.name.startswith("Vorfilter H")`) einen Merkmalsschlüssel. Das ist in jeder
Zielarchitektur richtig und ändert keine Position.

⚠️ **Aber die Zielarchitektur muss VOR 2f feststehen**, sonst wird an einer
Stelle gebaut, die danach umzieht. Drei Möglichkeiten:

| | Weg | Folge |
|---|---|---|
| **A** | Stufe 11 liest künftig `wahrscheinlichkeit` statt `trefferbilanz` | H, Funding und Turnover müssen **vor** Zeile 1596 gerechnet werden — Reihenfolge ändern |
| **B** | beide bleiben, die Mail zeigt zwei Zahlen | ⚠️ zwei Wahrheiten nebeneinander, für den Leser unentscheidbar |
| **C** | **die Trefferbilanz wird ein BEITRAG in `wahrscheinlichkeit`** | eine Zahl, alle Beiträge darin; Stufe 11 liest genau diese. Löst zugleich den Gebühren-Widerspruch |

**Empfehlung: C.** Sie beseitigt die Parallelität, statt sie zu verwalten — und
sie macht aus dem heutigen Sonderweg (Trefferbilanz mit eigenem Maßstab) einen
Beitrag wie jeden anderen, der sich derselben Prüfung stellen muss (R-R8).

⚠️ **Zu klären bleibt in jedem Fall die Reihenfolge:** Solange die Bewertung
nach dem Modellaufruf sitzt, kann sie nur markieren. **G-6 verlangt, dass sie
davor sitzt** — und das ist ein eigener Umbau, kein Nebeneffekt von 2c.

---

# TEIL 10 — DIE ZIELARCHITEKTUR (30.08.2026)

**Nutzervorgabe, die alles ordnet:**

> **1.** Die Bewertung erfolgt **ohne Wirtschaftlichkeit, Gebühren usw. — also
> neutral.**
> **2.** In der Mail **nur als Text** — **erst beim Hebel** (Strategie) braucht
> man die Standardrate 0,3 bzw. 1,5 % **rechnerisch**.

## Warum der Hebel die Ausnahme ist — und Spot nicht

| | Spot | **Hebel** |
|---|---|---|
| Gebühr fällt an | einmal beim Kauf, einmal beim Verkauf | **täglich**, solange die Position lebt |
| Sie verändert | die Abrechnung | ⚠️ **das Ergebnis desselben Kursverlaufs** |
| Also ist sie | eine Abrechnungsgröße | **Teil der Trade-Mechanik** |

**Bei Spot heißt „Gebühren in die Bewertung nehmen": die Börse messen statt den
Markt.** Beim Hebel wäre das Weglassen dagegen ein Fehler — dort entscheidet die
Haltedauer über das Ergebnis.

⚠️ **Und dieselbe Zahl hat beim Hebel zwei Rollen:** Die **Funding-Rate** ist
dort Kostenfaktor **und** der stärkste gemessene Positionierungsbeitrag
(+0,0246 R). **Wer sie verwechselt, zählt sie doppelt.**

## Bestandsaufnahme: jede Stelle, an der heute Gebühren vorkommen

| Stelle | Verwendung | heute | Urteil |
|---|---|---|---|
| `potential.rechne()` | **Bewertung** | ✔ ruft mit `gebuehr_je_seite=0.0`, nimmt nur `quote` | ✔ **richtig gebaut** |
| `wahrscheinlichkeit` → `quote` | **Bewertung** | ✔ `basis + zuschlag`, keine Gebühren | ✔ richtig |
| `wahrscheinlichkeit` → `abstand_punkte`, `erwartungswert_r` | Auskunft | 0,30 % und 1,50 % nebeneinander | ✔ richtig — Mailtext |
| `trefferbilanz.saetze()` | Auskunft | Text „Kauf und Verkauf kosten … %" | ✔ richtig |
| ⚠️ **`trefferbilanz.bewerte()` → Stufe 11** | **Bewertung** | **`(1+kosten_r)/(1+CRV)`** | ✖ **VERSTOSS** — entscheidet mit Gebühren |
| ⚠️ **Hebel-Finanzierung** | **Mechanik** | **existiert nicht** — kein Code rechnet sie | ✖ **LÜCKE** |

✔ **Die gute Nachricht: Die Bewertungsseite ist bereits neutral.** `potential`
und die `quote` rechnen ohne Gebühren. **Ein Verstoß und eine Lücke** — nicht
mehr.

## Die Zielarchitektur: wo wirkt was

```
   SELEKTION            vor dem Modellaufruf
   auswahl.waehle()     "welche Assets beurteilen wir heute?"
   -> sperrt                                      NEUTRAL

   TRICHTER 1-10        Stufen: Auftrag, Fakten, Lagebild, Anlass,
                        Auswahl, Wiederholung, Urteil, Aktion,
                        Geometrie, Risikoschicht
   -> sperrt            "ist dieser Fall ueberhaupt bearbeitbar?"
                                                  NEUTRAL

   BEWERTUNG            potential.rechne()
   -> Wahrscheinlichkeit aus Basisrate + Beitraegen
        Vorfilter H          Schalter, +4,5 Punkte auf 5 % der Faelle
        Funding-Rang         abgestuft, +0,8 Punkte auf 100 %
        Turnover-Rang        abgestuft
   -> daraus Potential = quote x CRV - (1 - quote)
                                        ⚠️⚠️ STRIKT NEUTRAL

   ENTSCHEIDUNG         Stufe 11
   -> Potential gegen SCHWELLE                    NEUTRAL
   -> heute: zaehlt nur          G-6: verwirft

   MECHANIK             nur Instrument `hebel`
   -> Finanzierung x Haltedauer vom Potential abziehen
                                        ⚠️ RECHNERISCH, nur hier

   MAIL                 signal_mail.baue_mail()
   -> Potential (neutral) + Wirtschaftlichkeit als TEXT
      "0,30 % Referenz: ...   1,50 % Bitpanda: ..."
                                        TEXT, nie Filter
```

## Die drei Umbauten, die daraus folgen

| # | Was | warum | Größe |
|---|---|---|---|
| **U-1** | **Stufe 11 liest `potential` statt `trefferbilanz.breakeven()`** | behebt den Verstoß: die Entscheidung wird neutral | mittel |
| **U-2** | **Reihenfolge**: Bewertung **vor** Zeile 1596 statt danach | solange sie nach dem Modell sitzt, kann sie nur markieren | ⚠️ groß |
| **U-3** | **Hebel-Finanzierung rechnen** — nur bei `instrument="hebel"` | schließt die Lücke; ⚠️ **getrennt** vom Funding-**Beitrag** halten | mittel |

⚠️ **U-2 ist der eigentliche Kern von G-6** und größer als alles bisher
Gebaute. Er verschiebt die Bewertung an eine Stelle, an der die Geometrie
(Zeile 1517) schon steht, das Modellurteil (1108) aber noch nicht gebraucht
wird — **das muss zuerst geprüft werden, nicht angenommen.**

## Was das für 2c bedeutet

**2c bleibt richtig und unberührt.** Es ersetzt den Namensvergleich durch einen
Merkmalsschlüssel — das ist in jeder der drei Umbauten Voraussetzung, nicht
Folge. ⚠️ **Aber 2f (scharf schalten) wartet auf die Entscheidung zu U-1/U-2.**

---

# TEIL 11 — WO GEHÖREN DIE BEWERTUNGSKNOTEN HIN? Fachliche Einordnung (30.08.2026)

**Nutzerauftrag:** *„prüfe als Fachexperte und auf Basis existierender
Tradingmodelle, was hier sinnvoll ist als Basis."* Dazu die Nutzerüberlegung:
nach der **finalen Gesamtbewertung** begründet verwerfen — und die fehlende
**LLM-Qualitätsmessung** konzeptionell mitdenken.

## 1. Die entscheidende Zahl steht im NB-Export

```
gemini heute:  130 Aufrufe          Tagesgrenze je Modell:  500
zai heute:      43                  Rollen-Kette:           119 Signale
                                                            -> 26 % Auslastung
```

⚠️⚠️ **Kostensparen ist damit KEIN Argument für frühes Filtern.** Genau das
war die einzige Begründung für **U-2** (Bewertung vor den Modellaufruf ziehen).
**Sie fällt weg.**

## 2. Was die etablierten Architekturen sagen

Das Standardmuster quantitativer Systeme (QuantConnect Algorithm Framework;
Alpha-/Risikomodell-Literatur) ist durchgehend:

```
   ALPHA-MODELL          erzeugt Insights fuer ALLE Kandidaten
        v
   PORTFOLIO-KONSTRUKTION  waehlt aus den Insights aus
        v
   RISIKOMODELL          begrenzt
        v
   AUSFUEHRUNG
```

⚠️ **Die Auswahl sitzt NACH der Signalerzeugung, nicht davor.** Und zwar aus
einem sachlichen Grund, nicht aus Bequemlichkeit:

> **Ein Querschnittsvergleich braucht alle Kandidaten.** Wer vorher filtert,
> kann hinterher nicht mehr sagen „TAO ist besser als BTC und LINK" — der
> Beste könnte schon aussortiert sein.

**Und genau Querschnittsgrößen sind unsere beiden Beiträge:** Funding-Rang und
Turnover-Rang werden über die heute bewerteten Symbole gebildet. Sie
**setzen die vollständige Liste voraus** — U-2 würde ihnen die Grundlage
entziehen.

## 3. Die Einordnung unseres Systems

| unsere Stufe | entspricht |
|---|---|
| Selektion (`auswahl.waehle`, k beste) | **Universum-Definition** — was überhaupt betrachtet wird |
| Trichter 1–10 | **Datenqualitäts-Gates** — ist der Fall bearbeitbar |
| Rolle A + Rolle BC | **Alpha-Modell** — erzeugt die Insights |
| Potential (H + Funding + Turnover) | **Signal-Bewertung** |
| Stufe 11 | ⚠️ **Portfolio-Konstruktion** — und genau hier gehört das Verwerfen hin |
| Töpfe, Budget | **Risikomodell** |

✔ **Die Struktur stimmt bereits. Was fehlt, ist die Wirkung an Stufe 11 —
nicht ihre Position.**

## 4. ➔ Fachliche Empfehlung: U-2 NICHT bauen

| | |
|---|---|
| ✖ **U-2 verwerfen** | Die einzige Begründung war Kostensparen — bei 26 % Auslastung gegenstandslos. Er widerspricht der Standardarchitektur **und** entzieht den Querschnittsbeiträgen die Grundlage |
| ✔ **U-1 bauen** | Stufe 11 liest `potential` statt `trefferbilanz.breakeven()` — behebt den Gebührenverstoß |
| ✔ **G-6 an Stufe 11** | dort verwerfen, **nach** der Gesamtbewertung — genau die Nutzerüberlegung |
| ✔ **U-3 später** | Hebel-Finanzierung, getrennt vom Funding-*Beitrag* |

**Die Nutzerüberlegung ist damit nicht nur möglich, sondern die fachlich
richtige Lösung.**

## 5. ⚠️ Der Bonus: die LLM-Qualitätsmessung fällt daraus ab

**Das ist der Punkt, der die Entscheidung zusätzlich trägt.** Wer **nach** dem
Modellaufruf verwirft, erzeugt genau die Daten, die für N-7 fehlen — ein
natürliches Experiment mit vier Feldern:

| | Bewertung **ja** | Bewertung **nein** |
|---|---|---|
| **LLM sagt kaufen** | Empfehlung geht raus | ⚠️ **verworfen — im Schatten weiterverfolgen** |
| **LLM sagt halten** | ⚠️ im Schatten | Ruhe |

**Daraus lassen sich beide Fragen getrennt beantworten:**

| Vergleich | beantwortet |
|---|---|
| verworfen gegen durchgelassen, **bei gleichem LLM-Urteil** | ⚠️ **trägt die BEWERTUNG?** |
| LLM-kaufen gegen LLM-halten, **bei gleicher Bewertung** | ⚠️ **trägt das MODELL?** (das offene N-7) |

⚠️⚠️ **Wer vor dem Modell filtert, bekommt diese Tabelle nie.** Die verworfenen
Fälle hätten kein LLM-Urteil — die zweite Zeile bliebe leer, und N-7 wäre
dauerhaft unbeantwortbar.

**Die Bauform dafür existiert schon:** `vorfilter_schatten` schreibt seit dem
22.08. genau so mit (617 Zeilen, 31 mit H). Dasselbe Muster, ein Feld mehr.

## 6. Was daraus als Reihenfolge folgt

| # | Schritt | Zustand |
|---|---|---|
| **2c–2e** | Struktur fertigbauen (Merkmal, Registrierung) | bereit |
| **U-1** | Stufe 11 auf `potential` umstellen — **neutral, ohne Gebühren** | Konzept steht |
| **S** | **Schattentabelle**: jede Bewertung mit LLM-Urteil und Ausgang mitschreiben | ⚠️ **vor** G-6 |
| **2f** | Beiträge scharf schalten | nach U-1 |
| **G-6** | verwerfen — **erst wenn der Schatten zeigt, dass die Verworfenen wirklich schlechter waren** | zuletzt |

⚠️ **Der Schatten kommt VOR dem Verwerfen, nicht danach.** Sonst schaltet man
eine Regel scharf, deren Wirkung auf den eigenen Signalen nie geprüft wurde —
derselbe Fehler wie bei H, das am 05.08. mit einem Mittelwert aus zwei
gegenläufigen Marktphasen scharfgeschaltet wurde.

---

## Die Abdeckung aller Varianten — Prüfung vor 2c (30.08.2026)

**`ERLAUBTE_PAARE` kennt fünf Kombinationen.** Für jede muss feststehen, ob ein
Beitrag gilt — und wenn nicht, **warum**.

| Instrument × Strategie | Richtung | **H** | **Funding** | **Turnover** | Begründung |
|---|---|---|---|---|---|
| spot × einstieg | long | ✔ | ✔ | ✔ | so gemessen |
| **spot × akkumulation** | long | ✖ ausgeschlossen | ✖ | ✖ | **kein einzelner Einstiegszeitpunkt** — ein Tagesrang bewertet einen Moment, die Staffelung hat keinen |
| hebel × einstieg | long | ✔ | ✔ | ✔ | gemessen |
| hebel × swing | long | ✔ | ✔ | ✔ | gemessen (Horizont 20 T deckt beides) |
| ⚠️ **alle × short** | **short** | `None` | ⚠️ **`None`** | ⚠️ **`None`** | **nicht gemessen** |
| absicherung × einstieg | — | ? | `None` | `None` | inverse ETFs, kein Perpetual → gar keine Daten |

### ⚠️⚠️ Warum Short zwingend `None` ist — nicht das gespiegelte Vorzeichen

Der Funding-Befund lautet: **hohes Funding = viele Longs zahlen = überhitzt =
schlechter für LONG.** Die naheliegende Spiegelung wäre *„dann ist es gut für
Short"*.

**Das wäre eine Vermutung, keine Messung.** Und im Projekt gibt es den
Präzedenzfall: **Kapitel 110** hat für H genau diese Spiegelung geprüft —
**H′ spiegelt NICHT.** Die Bedingung hilft im Bullenmarkt und schadet im
Bärmarkt, unabhängig von der Handelsrichtung.

➔ **Für Short gilt `None`, nicht `False` und nicht das Gegenteil.** Ein
Merkmal, das man nicht kennt, darf nie aussehen wie eines, das man geprüft hat.

### Die Konsequenz für 2c: zwei Filterfelder mehr

Heute kennt `Beitrag` nur `klassen`. Die Bedingung „nur Long" steht deshalb in
`vorfilter.py` — **beim Lieferanten des Werts, nicht beim Beitrag.** Das
funktioniert, verteilt aber das Wissen: Jeder neue Aufrufer müsste die Regel
kennen.

```python
klassen:    tuple = ()   # krypto | aktien | etf | rohstoffe
strategien: tuple = ()   # einstieg | swing | akkumulation
richtungen: tuple = ()   # long | short
```

**Damit deklariert jeder Beitrag selbst, wo er gilt** — und `rechne()` meldet
für alles andere `zustand="nie"` mit Begründung, wie heute schon bei fremden
Assetklassen.

### Die anderen Assetklassen — auf Planungsebene abgedeckt

Funding und Turnover werden mit `klassen=("krypto",)` registriert. Für Aktien,
ETF und Rohstoffe meldet die Rechnung dann **von selbst**:

> *„auf aktien nie gemessen — Binance Futures steht auf Krypto"*

✔ **Kein Sonderfall nötig, keine spätere Änderung an dieser Stelle.** Kommt für
Aktien eines Tages ein eigener Beitrag (KGV, Leerverkaufsquote), wird er mit
`klassen=("aktien",)` daneben registriert. **Die Struktur trägt das schon.**

---

## 2c GEBAUT: H hängt nicht mehr am Namen (30.08.2026)

**Vorher** stand im Code:

```python
if b.zustand == "traegt" and b.name.startswith("Vorfilter H"):
```

**Jetzt** deklariert jeder Beitrag sein Merkmal selbst — `merkmal="h"` — und
`rechne()` liest es aus `merkmale`. Der Sonderfall ist zum Regelfall geworden.

### Und drei Achsen statt einer

`_gilt()` prüfte bisher nur die **Assetklasse**. Die Bedingung „H nur bei Long"
stand deshalb in `vorfilter.py` — **beim Lieferanten des Werts, nicht beim
Beitrag**. Jetzt:

```python
klassen:    tuple = ()   # krypto | aktien | etf | rohstoffe
strategien: tuple = ()   # einstieg | swing | akkumulation
richtungen: tuple = ()   # long | short
```

Jede Ablehnung nennt **den Grund**:
*„für short nie gemessen — Vorfilter H ist auf long belegt"*.

⚠️ **Ein Detail, das die Bitgleichheit gerettet hat:** Der Klassen-Meldetext
lautet weiterhin wörtlich *„… steht auf Krypto"* — mit großem K, hartcodiert
wie vorher. Meine erste Fassung baute ihn aus `b.klassen` zusammen und schrieb
„krypto". Das hätte 300 Mailzeilen verändert.

### Prüfung

| | |
|---|---|
| **Bitgleichheit** | **432 Fälle, 0 FEHL** — H rechnet unverändert |
| Verhalten von H | `True` → 4,5 Punkte · `False` → Zustand **null** · `None` → Zustand **nie** ✔ |
| neuer Weg `merkmale={"h": …}` | liefert dasselbe wie `h=` ✔ |
| abgestufte Beiträge | Fünftel 0/2/4 → +2,0 / 0,0 / −2,0 ✔ · fehlender Wert → **nie**, nicht 0 |
| die drei Achsen | Long-Beitrag gilt bei short nicht, Akkumulation wird ausgeschlossen, **beide mit Begründung** ✔ |

### Gegenprüfung

| | |
|---|---|
| die drei Aufrufer | `potential.rechne()` ✔ · `saetze()` ✔ · `rollen_lauf` ✔ |
| **Gesamtsuite** | **1.784 Prüfungen, ALLE BESTANDEN** (vorher 1.772) |
| dauerhaft | **12 neue Prüfungen** im Paket „Stufen" — laufen ab jetzt immer mit |

### Was jetzt möglich ist, ohne weiteren Strukturumbau

```python
Beitrag(name="Finanzierung im Marktvergleich",
        zustand="traegt", punkte=0.0,
        stufen=(+0.81, +0.85, +0.25, -0.52, -1.39),
        merkmal="funding_fuenftel",
        klassen=("krypto",),
        strategien=("einstieg", "swing"),   # nicht akkumulation
        richtungen=("long",))               # short ist ungemessen
```

**Eine Zeile je Beitrag — genau wie im Modulkopf versprochen.** Das ist 2e;
davor liegt 2d (Parameter durchreichen) und die Entscheidung zu U-1.

---

# TEIL 12 — WAS SOLL STUFE 11 BEWIRKEN? Fachliche Vorlage (30.08.2026)

**Nutzerfrage:** *„was soll Stufe 11 bewirken, Funktionalität und Nutzen muss
festgelegt sein. Aktuell kann ich nichts dazu sagen. Ist es meine Entscheidung
oder ergibt sich das aus den Anforderungen?"*

## 1. ⚠️⚠️ Was Stufe 11 HEUTE tut — nachgerechnet

```
Quote (leere Bilanz)  =  basisrate_fuer(CRV)  =  0,340 bei CRV 2,0
Schwelle              =  (1 + kosten_r) / (1 + CRV)
```

**Und kosten_r im Betrieb, bei 1,5 % Gebühr je Seite:**

| Stopabstand | kosten_r | Schwelle bei CRV 2,0 | Quote | Urteil |
|---|---:|---:|---:|---|
| 3 % | **1,00** | 0,667 | 0,340 | trägt nicht |
| 5 % | **0,60** | 0,533 | 0,340 | trägt nicht |
| 8 % | 0,38 | 0,460 | 0,340 | trägt nicht |
| 20 % | 0,15 | 0,383 | 0,340 | trägt nicht |
| *(nur bei kosten_r = 0)* | 0,00 | 0,333 | 0,340 | *knapp ja* |

⚠️⚠️ **Stufe 11 sagt bei praktisch jedem Signal „trägt sich nicht".** Sie
verlangt eine Trefferquote von **53 %**, wo die Geometrie 33 % hergibt und der
beste gemessene Beitrag 4,5 Punkte beisteuert. **Nur weil sie ausschließlich
zählt, fällt es nicht auf.**

⚠️ **Und ein zweiter Widerspruch:** `trefferbilanz` rechnet mit der
**gemessenen** Basisrate 0,340, `wahrscheinlichkeit` mit der **arithmetischen**
1/(1+CRV) = 0,3333. **Zwei Basisraten im selben System.**

## 2. Was sich aus den ANFORDERUNGEN ergibt — nicht Ihre Entscheidung

| # | Vorgabe | Quelle | Folge für Stufe 11 |
|---|---|---|---|
| **A1** | *„Empfehlungen werden nicht durch den Takt bestimmt, sondern durch begründete Wahrscheinlichkeit und Potential"* | Zielvorgabe, 30.08. | **sie muss verwerfen** — Zählen erfüllt das nicht |
| **A2** | *„Die Bewertung erfolgt ohne Gebühren — neutral"* | Vorgabe 30.08. | **der Gebühren-Breakeven muss weg** |
| **A3** | *„JEDE Handlung muss begründet sein"* | Zielvorgabe | **jede Ablehnung nennt ihren Grund** |
| **A4** | Portfolio-Konstruktion folgt der Signalerzeugung | Standardarchitektur | **Position bleibt, wo sie ist** |
| **A5** | *„welcher der drei Trades ist der beste"* | Nutzerpunkt 2, 29.08. | **sie liefert eine Rangfolge, nicht nur ja/nein** |

✔ **Fünf von sechs Eigenschaften ergeben sich zwingend.** Da ist nichts zu
entscheiden.

## 3. Was Ihre Entscheidung ist — und nur das

> **Die SCHWELLE: ab welchem Potential wird gehandelt?**

Das ist keine Messfrage, sondern eine Risikoentscheidung. **Die
Entscheidungsgrundlage:**

| Lage | Potential |
|---|---|
| nur Geometrie, kein Beitrag trägt | **0,000 R** — „wir wissen nichts über diesen Trade" |
| Funding-Beitrag allein (+0,8 Punkte) | ≈ **0,024 R** |
| Vorfilter H allein (+4,5 Punkte) | ≈ **0,135 R** |
| H **und** Funding | ≈ **0,159 R** |

**Der ganze Wertebereich liegt heute zwischen 0 und rund 0,16 R.**

| Schwelle | Wirkung |
|---|---|
| **0,00** | jedes Signal geht durch, das nicht negativ ist — praktisch kein Filter |
| **> 0,00** | ⚠️ **mindestens ein Beitrag muss tragen** — „kein Signal ohne Begründung" |
| **0,10** | faktisch: **nur mit Vorfilter H** — das sind 5 % der Fälle |
| **0,15** | nur H **und** Funding zusammen — sehr selten |

⚠️ **Meine fachliche Empfehlung: knapp über 0,00.** Begründung: Die
Zielvorgabe lautet *„keine Empfehlung ohne begründetes Potential"* — nicht
*„nur die allerbesten"*. Eine Schwelle bei 0,10 würde die Signalzahl auf
etwa ein Zwanzigstel senken und hinge allein an H, dessen Wirkung episodisch
ist.

## 4. Der Nutzen von Stufe 11 — in einem Satz

> **Sie verwandelt eine Liste bewerteter Kandidaten in eine begründete
> Empfehlung — indem sie verwirft, was kein gemessenes Potential hat, und den
> Rest nach Potential ordnet.**

**Damit ist sie die Stelle, an der das Ziel eintritt.** Alles davor bereitet
vor; alles danach berichtet.

## 5. Was U-1 konkret ändert

| | heute | nach U-1 |
|---|---|---|
| Eingang | `trefferbilanz` (leer: 96 von 2.313) | `potential.rechne()` |
| Maßstab | `(1+kosten_r)/(1+CRV)` — **mit Gebühren** | **Schwelle in R, neutral** |
| Basisrate | 0,340 (gemessen) | 1/(1+CRV) — **eine einzige** |
| Ergebnis | `traegt` ja/nein | Potential **als Zahl** + ja/nein |
| Wirkung | zählt | **zählt weiter** — G-6 ist ein eigener Schritt |

⚠️ **U-1 schaltet nichts scharf.** Es macht die Zahl richtig und einheitlich.
Das Verwerfen ist G-6 und braucht vorher den Schatten.

---

## Die Schwellen-Kalibrierung — gemessen, mit einem eigenen Fehler unterwegs

**Nutzervorgabe:** *„Schwelle muss über 0,000 liegen, wie hoch ist noch zu
messen"* und *„ich würde gerne erst detailliert simulieren."*

⚠️ **Mein erster Anlauf war falsch konstruiert** — er verglich die Verbliebenen
mit der Gesamtmenge und mischte damit Auswahlleistung und Sperrquote. Die
Zufallsprobe kippte ihn (Methodik **2.93** neu). Korrigiert auf den
**quotengleichen** Vergleich:

| Schwelle | Durchlass | echt − quotengleicher Zufall | |
|---|---|---|---|
| 0,000 | 53,9 % | +0,1258 [+0,067 .. +0,199] | ✔ trägt |
| **0,010** | **38,9 %** | **+0,1701** [+0,092 .. +0,270] | ✔ trägt |
| 0,020 | 35,9 % | **+0,1818** [+0,102 .. +0,284] | ✔ trägt — Maximum |
| 0,030 | 19,5 % | +0,1654 [+0,050 .. +0,257] | ✔ trägt |
| 0,050 | 2,7 % | +0,2030 [−0,085 .. +0,286] | ⚠️ Stichprobe zu klein |

### Die Deutung — und was sie NICHT sagt

✔ **Eine Schwelle über 0,000 trägt.** Das ist der belastbare Teil, über einen
breiten Bereich (0,010 bis 0,030) gleichwertig.

⚠️ **Es gibt kein scharfes Optimum.** Die Werte 0,010 / 0,020 / 0,030 liegen
mit überlappenden Intervallen beieinander. Das Maximum bei 0,020 ist ein
**Suchergebnis über sieben Schwellen** — kein eigener Befund.

⚠️ **Die absolute Größe ist nicht mit der Funding-Regel vergleichbar**
(+0,18 gegen +0,024 R). Andere Maße: dort „mit Regel gegen ohne", hier „gegen
quotengleichen Zufall". **Die Zahlen dürfen nicht nebeneinander gestellt
werden.**

⚠️ **Und Vorfilter H fehlt in dieser Simulation** — die Marken liegen auf
diesen Ankern nicht vor. Das Potential ist damit unterschätzt, die Schwelle
fällt eher zu niedrig aus. Das ist die vorsichtige Richtung.

### ➔ Empfehlung: **0,010 als Startwert, kalibrierbar**

**Nicht das Maximum (0,020), sondern die untere Kante des tragenden Bereichs:**

| | |
|---|---|
| 0,010 statt 0,020 | das Maximum ist ein Suchergebnis; beide sind statistisch gleichwertig |
| **Durchlass 38,9 %** statt 35,9 % | mehr Signale bei gleicher Wirkung |
| über 0,000 | ⚠️ **die Nutzervorgabe: mindestens ein Beitrag muss tragen** |
| **in der Konfiguration** | nachjustierbar, ohne Codeänderung — genau das verlangt „kalibrierbar" |

**Konkret bedeutet 0,010:** Ein Signal braucht mindestens **+0,3 Punkte**
Zuschlag auf die Quote. Das erreicht jeder einzelne tragende Beitrag —
Funding-Fünftel 0 bis 2, Turnover-Fünftel 0 bis 2, oder Vorfilter H. **Wo
kein Beitrag trägt, gibt es keine Empfehlung.**
