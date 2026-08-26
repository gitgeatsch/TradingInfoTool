# Befundkarte — was steht, was fiel, was fehlt

**Lebende Datei.** Jedes neue Kapitel wird hier eingetragen, bevor es als
erledigt gilt. Wer nur den Umbauplan liest, sieht Puzzleteile; hier steht,
wie sie zusammenhängen und worauf sie zulaufen.

Stand: 20.08.2026, Kapitel 123. Einzelheiten je Kapitel:
`Umbauplan_Gesamtsystem_12_08.md`. Methodikregeln:
`Test_und_Verifikationsmethodik.md` 2.47–2.53.

---

## 1. Das Zielbild — woran alles gemessen wird

**Der Grundbefund des Projekts:** ein Barrierensystem auf einem **driftfreien
Pfad** hat brutto den Erwartungswert **null** — für jede Geometrie.
Theoretisch 33,3 % bei CRV 2,0, gemessen 34,4 %. **Das ist Arithmetik, keine
Messfrage.**

Daraus folgt die einzige Frage, die zählt:

> **Gibt es eine Bedingung, unter der die Trefferquote den Breakeven
> `(1 + Kosten_R) / (1 + CRV)` übersteigt — und ist sie außerhalb der Daten
> nachweisbar, in denen sie gefunden wurde?**

Alles darunter — Trichter, Marken, Drift, Marktphase — sind **Kandidaten für
diese eine Bedingung**. Kein Kandidat ist ein Ergebnis, bevor er die Kette
unten durchlaufen hat.

**Drei Wege waren von Anfang an benannt:** Drift · Nachrichten · Kosten.
Bearbeitet ist bisher fast ausschließlich der erste, dazu die Struktur als
vierter, ursprünglich nicht vorgesehener Kanal.

---

## 2. Die Kette — was jeder Kandidat durchlaufen muss

Sie ist der eigentliche Ertrag der Kapitel 99–113. Ein neuer Kandidat kostet
ab jetzt nur noch Rechenzeit.

| # | Stufe | verhindert | Regel |
|---|---|---|---|
| 1 | **Vorabfestlegung** im Modulkopf | dass die Frage sich ans Ergebnis anpasst | — |
| 2 | **Reifeprobe** (erste 250 Tage je Reihe weg) | dass ein *Datenzustand* als Marktzustand gilt | 104.3 |
| 3 | **Block-Permutation** statt freiem Placebo | dass überlappende Anker als Beleg zählen | **2.47** |
| 4 | Blöcke in **Kalenderzeit** | eine Kontrolle, die nichts kontrolliert | **2.52** |
| 5 | **Läufe erhöhen** bei Knappheit | dass ein Urteil am Schätzfehler hängt | **2.48** |
| 6 | **Gleiche Grundgesamtheit** für Regel und Kontrolle | dass der Zufallsarm eine fremde Basisrate geschenkt bekommt | **2.50** |
| 7 | **Hürdenrechnung** einzeln vs. Maximum | dass Absuchen als Fund verkauft wird | **2.49** |
| 8 | **Positivkontrolle** | dass „nichts gefunden" nur „nicht hingesehen" heißt | 93 B |
| 9 | **Phasenprobe** | dass eine Marktwette als Struktur auftritt | 101.4 |
| 10 | **Zeitteilung** | dass ein Muster als Regel gilt | 109 |
| 11 | **Zerlegung statt Fallbeil** | dass ein Nullbefund Optionen mit wegräumt | **2.51** |
| 12 | **Abstand zum Breakeven** neben jedem Urteil | dass ein belangloser Effekt als Fund gilt | **2.53** |
| 13 | **Zwei Lesarten** für Unentschiedene | dass ein Auswahleffekt wie ein Befund aussieht | **2.54** |
| 14 | **Bootstrap statt Permutation** bei deterministischen Umrechnungen | eine Kontrolle, die den Mittelwert gar nicht ändern kann | **2.55** |

**Regel 2.51 wirkt rückwärts:** Befunde, die vor ihrer Einführung als
„erledigt" abgelegt wurden, beantworten meist die *Handelsfrage* („erreicht es
den Breakeven?") statt der *Informationsfrage* („trägt es Signal?"). Das ist
der Grund, warum Kapitel 113 den Drift wieder aufmacht.

---

## 3. Der Befundstand

### 3.1 Was steht

⚠️ **Kapitel 119 hat die Beurteilungsgrundlage korrigiert.** Alle Urteile der
Kapitel 99–118 liefen über den Abstand zum Breakeven — und der enthielt
Bitpandas Brokerspread von 1,5 %. Seit 119 gilt: **Referenzsatz 0,30 % je
Seite für die Frage „ist das ein guter Trade", Betriebssatz 1,50 % für „rechnet
es sich für mich", beide immer nebeneinander.**

| **H trägt — gebührenfrei** | **119** | ⚠️ **heute +3,78 gegen +3,36** (S3, 25.08.) — früher +4,5 gegen +2,6 | **13.768 Fälle, 523 Reihen** |
| H über dem Breakeven bei Referenzgebühr | 119 | **+3,1** (Betrieb: −1,0) | +0,086 R je Trade |
| **H je Kategorie — ZERLEGT** | **120/121** | ⚠️ **kein Kategorienbefund trägt altersunabhängig** (25.08.). Small nur im Band 250–499 (+7,77 gegen +6,54); **ab 750 nur +0,44 gegen +3,87**. Large trägt in **keinem** Band | Mid nie · 1 von 12 Zellen trägt |
| Spot gegen Hebel | 120 | Unterschied 0,017 R — **dreht kein Vorzeichen** | Finanzierung 0,03 %/Tag |
| **Strukturboden im Stop schadet nicht** | **124** | −0,0008 R über 631.755 Anker, greift bei 1,1 % | gemessen mit der Produktionsfunktion |

| Befund | Kapitel | Zahl | worauf es ruht |
|---|---|---|---|
| **H trägt Information** | 108 | −0,3 gegen Schwelle −2,1, schlägt alle 40 Ziehungen | 262 Reihen, 9.221 Fälle |
| **kostenunabhängig** | 108 | +4,8 gegen +2,0; alle fünf Stopbänder positiv | direkte Standardisierung |
| **kein Momentum-Ersatz** | 111 | +2,3 gegen +1,8 bei gleichem Hochabstand | 120 Läufe, stabil ab 40 |
| **keine Liquiditätsfolge** | 116 | +5,3 gegen +2,4 bei gleichem Umsatz | Bereinigung vergrößert ihn |
| **Geometrie ist reine Kostenarithmetik** | 101 | −6,0 → +0,1 über 20 Felder, monoton | vollständig erklärt |

> ⚠⚠ **S3 GEMESSEN AM 25.08.2026 — zwei Korrekturen an diesem Abschnitt.**
>
> **(1) Die Basis ist gewachsen, der Vorsprung geschrumpft.** Kapitel 119 lief
> auf 312 Reihen und 446.509 Ankern; Kapitel 121 hat 176 eingestellte Paare
> nachgeladen. Mit **identischem Code** auf der heutigen Basis (523 Reihen,
> 631.117 Anker) ergibt sich **+3,78 statt +4,5**, bei einer Schwelle von
> **+3,11 statt +2,6**. Der Abstand fällt von **1,9 auf 0,67** Punkte — und
> mit 2.47-konformen Blockgrenzen auf **0,42**. Kein Fehler, sondern
> Methodik 2.68: eine Zahl aus wachsender Datenlage veraltet.
>
> **(2) Large trägt nicht mehr.** Die Schwelle „aus acht“ hängt vom
> Blockbildungsverfahren ab: **+5,3** (Altzustand) · +5,7 · **+6,2**
> (2.47-konform). Der Messwert **+5,9** liegt darunter, sobald korrekt
> gerechnet wird → **ZU KNAPP (2.48)**, also gilt nichts. **Small hält in
> allen drei Varianten** (+7,9 gegen max. +6,2).
>
> ⚠️ **Der Altzustand liefert in BEIDEN Kapiteln die niedrigste von drei
> geprüften Schwellen.** Spanne je 0,9 Punkte bei 2×Streufehler 0,17–0,19 —
> kein Rauschen. Kapitel 117 und 120 (`messe_dosis`, `messe_klassen`) sind
> **noch nicht umgestellt** und stehen unter demselben Vorbehalt.
>
> Vollständig: `Vorabfestlegung_S1_S4_H_Annahmen_25_08.md`, Nachtrag (1).

### 3.2 Was fiel — und woran

| Behauptung | Kapitel | woran sie fiel |
|---|---|---|
| **H hält außerhalb seiner eigenen Daten** | **118** | Zeit −7,8 gegen −1,6 · Symbol +1,2 gegen +4,5 |
| **H braucht eine eigene Dosis** | **117** | Optimum liegt in derselben Ecke wie das der Basis |
| **H braucht Liquidität** | **116** | +2,7 gegen Schwelle +6,3; im liquidesten Band ist H am schlechtesten |
| **H hat einen Anwendungszeitpunkt** | **115** | Beharrung +3,9 gegen Schwelle +7,9; über Breakeven in **2 von 20** Fenstern |
| Die Marktphase wirkt **invers** | **114** | 6 von 6 Punktschätzern dagegen, beide Indizes |
| Die U-Form der Driftbänder | **113** | +7,0 auf 39 Reihen → **+0,6** auf 347 |
| Der Drift ist derselbe ATR-Kanal | **113** | Bereinigung **vergrößert** ihn (+0,6 → +1,5) |
| Kombination dreier Hebel trägt | 103 | Block-Permutation: +17,8 gegen Schwelle +20,5 |
| H überträgt sich über einen Regimewechsel | 109 | +2,7 außerhalb, Schwelle −5,3 → nein |
| H ist eine **Richtungs**bedingung | 110 | Spiegelbedingung dreht **nicht** mit |
| Der Phaseneffekt ist kurzfristig | 111.1 | 250-Tage-Fenster trennt am schärfsten |
| Die Marke weiß mehr (Stärke/Alter/gefegt) | 112 | keines der drei über der Schwelle |
| Aktien/ETF verbreitern die Basis | 106 | 2 + 4 Reihen gegen 39 |

⚠️ **Vier Erklärungen sind gefallen, der Befund aus 108 steht.** Wir wissen
*dass* H trägt und nicht mehr, *warum*.

### 3.3 Was nicht entscheidbar war

| Frage | Kapitel | Grund |
|---|---|---|
| Konjunktion mehrerer Trichterwerte | 103 | Effekt +17,8 unter Schwelle +20,5 bei 26 Reihen |
| H bei gleichen Kosten (schmale Basis) | 105 | +7,1 gegen +10,0 bei 24 Reihen |
| **Lebendigkeit für ~18 der 44 Kryptowerte** | **93 C** | über TVL nur `keine_quelle` — DefiLlama kennt sie, hat aber kein hinterlegtes Kapital. **Dauerhaft**, nicht datenbedingt |

**Beide wurden durch Kapitel 107 aufgelöst** — 347 statt 39 Reihen. *Nicht
entscheidbar* ist ein Datenproblem, kein Erkenntnisstand.

---

## 4. Die Abhängigkeitskarte

```
Grundbefund: driftfreier Pfad = Erwartungswert null
   |
   +-- Kosten senken ----> 101 Geometrie ......... erklärt, keine Information
   |                       102 Drift ............. 113 prüft nach
   |                       103 Kollinearität ..... nicht entscheidbar -> 107
   |
   +-- Information finden -> 104 Struktur H
   |        |                 105 kostenbereinigt (schmal) -> nicht entscheidbar
   |        |                       |
   |        |                 107 BREITE BASIS (347 Reihen)  <-- löst 103 UND 105
   |        |                       |
   |        |                 108 H trägt .......... STEHT
   |        |                       |
   |        +-- warum? --> 109 Zeitteilung ........ Regel fällt
   |        |              110 Spiegelbedingung ... Erklärung fällt
   |        |              111 Phasenhorizont ..... Erklärung fällt
   |        |              111 Hochabstand ........ 44 % erklärt, 56 % bleibt
   |        |              112 Anreicherung ....... nichts mehr zu holen
   |        |
   |        +-- AUSSERHALB? -------> 118 zwei Teilungen .. BEIDE NEIN
   |        |                              und die gewaehlte Geometrie ist
   |        |                              nicht einmal stabil (CRV 1,5/3,0)
   |        |
   |        +-- WELCHE DOSIS? -----> 117 Geometrie .. dieselbe wie Basis
   |        |                              +4,5 gegen Schwelle +4,7
   |        |                              (eine vorab benannte Zelle: +3,7)
   |        |
   |        +-- WANN anwenden? -----> 115 Beharrung .. KEINE
   |        |                              -> H ist real und nicht handelbar
   |        |                                 ZWEIG GESCHLOSSEN (104-115)
   |        |
   |        +-- womit kombinieren? --> 113 Drift ... NICHT kombinierbar
   |                                       (H liegt zu 92 % im Driftextrem,
   |                                        die Zelle fehlt)
   |
   +-- Nachrichten -------> NIE BEARBEITET

Quer dazu: 114 prueft den BEGRIFF Marktphase selbst
   -> nicht invers, aber auch nicht vorhersagend (13 Zeitbloecke)
   -> die Phasenprobe bleibt gueltig, heisst aber "gilt in allen drei
      ZEITABSCHNITTEN", nicht "gilt in allen Marktzustaenden"
```

**Was das zeigt:** die Kapitel 109–112 hängen alle an **einem** Befund (108)
und versuchen ihn zu *erklären*. Alle vier sind gescheitert. Der Befund ist
davon unberührt — aber ohne Erklärung ist er nicht verallgemeinerbar, und
genau deshalb überträgt er sich in 109 nicht.

⚠️ **Der dritte Weg — Nachrichten — ist seit dem Grundbefund benannt und
wurde nie angefasst.** Er ist der einzige Kanal, der weder über den ATR noch
über die Kursreihe läuft.

---

## 5. Die offenen Fragen — und was jede ändern würde

| Frage | Kapitel | was sie ändern würde |
|---|---|---|
| Warum schneiden Shorts im trailing-Bär am schlechtesten ab? | offen (114.4) | Kandidat: Volatilität — die Quote selbst, nicht der Abstand |
| Ist die Marktbreite als *inverses* Signal brauchbar? | offen | ein verlässlich inverser Zusammenhang ist so gut wie ein positiver |
| Trägt der **Umschlag**? | offen | einziger unberührter Kanal in den Kursdaten |
| Trägt „gefegt" **umgekehrt**? | offen (112.4) | Beobachtung −4,2, Richtung ungeprüft |
| **Warum treffen sterbende Coins häufiger ihr Ziel?** | offen (121.4) | 39,3 % gegen 35,2 %; drei Erklärungsversuche widerlegt, **keine Erklärung** |
| **Handelbarkeit in Small** | ⚠️ **mit Kursdaten unprüfbar** (121.5) | Spread, Markttiefe und ob es beim Ausstieg einen Käufer gibt, stehen in keiner OHLC-Reihe — und sind kein Gebührenproblem |
| **BTC ist nicht messbar** | 120.4 | 202 H-Fälle; eine Reihe, 2,1 % der Tage. Für das wichtigste Einzelasset gibt es keine Aussage |
| **Ausstieg** | **erledigt (123)** | Teilverkauf −0,069 R, Einstandstop −0,119 R — beide Intervalle unter null. Die einfachste Variante ist die beste |
| **Nachrichten** | **nie bearbeitet** | einziger Kanal außerhalb der Kursreihe — und damit der einzige mögliche Partner für H, der nicht per Konstruktion mit ihm korreliert |

---

## 5b. ⚠️ Die Antwort auf die Kernfrage (Stand 118)

Alle Kandidaten der Kapitel 99–118 stammen aus **der Kursreihe**. Sie sind
untereinander verwandt — der ATR-Kanal trat **fünfmal** unter neuem Namen auf,
H und Drift überlappen zu 92 %. **Keiner hat einen Außer-Stichproben-Test
bestanden.**

> **Aus der Kursreihe allein lässt sich für dieses Barrierensystem keine Regel
> gewinnen, die außerhalb ihrer eigenen Daten trägt.**

Das ist ein Ergebnis, kein Scheitern — und es ist mehr wert als ein Filter,
der auf einem Stichprobenartefakt in den Betrieb gegangen wäre. Was bleibt:
die **Prüfkette** (vierzehn Stufen, 2.47–2.54) und die **Datenbasis** (347
Reihen). Beide erledigen den nächsten Kandidaten in Stunden statt Wochen.

---

## 5c. Die praktische Bilanz auf der ECHTEN Auswahl (122)

29 Watchlist-Symbole, 37.623 Anker. H-Vorsprung **+4,8 Punkte** — stimmig mit
+4,5 auf allen 523 Reihen.

| Nettoerwartungswert je Trade | ohne Filter | **mit H** | Gewinn |
|---|---:|---:|---:|
| Referenz 0,30 % | −0,031 R | **+0,114 R** | +0,145 |
| **Betrieb 1,50 %** | −0,182 R | **−0,036 R** | +0,146 |

> **H verbessert um rund 0,15 R je Trade — an beiden Sätzen gleich. Zum
> Betriebssatz reicht das nicht bis über null.**

⚠️ **KORRIGIERT 25.08. — siehe 6.0.** Der folgende Satz gilt als
**Geldrechnung**, nicht als Qualitätsurteil: für „ist das ein guter Trade"
zählt der **Referenzsatz**, und dort trägt H (+0,114 R).

⚠️ **Die bindende Größe ist nicht der Filter, sondern die Handelsgebühr.** H
schließt vier Fünftel der Lücke; das letzte Fünftel schließt nur der
Handelsplatz.

⚠️ Und auf 29 Symbolen ist der Effekt **nicht bestätigbar** (27 Reihen mit zwei
Blöcken, Schwelle +9,2) — dieselbe Wand wie Kapitel 105. Der Nachweis steht
auf 523 Reihen; die Watchlist kann ihn weder bestätigen noch widerlegen.

---

## 5d. ⚠️ H steht auf VIER ungeprüften Annahmen (25.08.2026)

H ist der einzige tragende Befund des Projekts. Umso wichtiger ist, worauf er
steht. Vier Zahlen gehen in **jedes** H-Urteil ein und sind **nie** geprüft
worden — alle vier an der Quelle verifiziert, nicht aus Plänen abgeschrieben:

| | Annahme | Quelle | was kippt, wenn sie fällt |
|---|---|---|---|
| **K1** | Totzone **0,5 ATR** — nähere Marken zählen nicht | `lagebeschreibung.py:215-220` | **H selbst** — sie ist die untere Kante *beider* Bänder |
| **K2** | Phasenindex = Mittel aus `c[j]/c[0]` je Reihe | `simuliere_bremse.py:230-233` | die **Phasenabhängigkeit** (+7,6/+6,0/−6,5) |
| **K3** | Blockgrenzen liegen **fest** statt zu wandern | `bewerte_neu.py:205` u. a. | die **Schwellen aller H-Urteile seit Kap. 119** |
| **K4** | Reifeschnitt **250 Handelstage** | `messe_struktur_bereinigt.py` | die Trennung **Phase gegen Reihenalter** |

**K1 ist der Gebührenfehler in neuer Form.** `messe_marken.py:43-46` schreibt
wörtlich, die Totzone sei *„eine Eigenschaft des Betriebs, keine Annahme dieser
Messung, und sie bleibt unangetastet“*. Genau so stand achtzehn Kapitel lang
der Betriebssatz 1,50 % da: als gegeben, nicht als Annahme — und war der
falsche Maßstab.

**K3 ist die schwerste.** Die eigene Methodikregel 2.47 verlangt wandernde
Blockgrenzen (*„feste Grenzen lassen immer dieselben Anker gemeinsam reisen"*).
Die vier Werkzeuge, die die heute gültigen H-Urteile erzeugt haben —
`bewerte_neu`, `messe_klassen`, `messe_ueberleben`, `messe_dosis` — setzen
sie **fest**. Die älteren (`messe_marken`, `messe_struktur_bereinigt`) ließen
sie wandern. Die Richtung des Fehlers ist **nicht vorhersagbar**: Regel 2.47
sagt „Schwelle zu niedrig“, die Messung in 2.48 zeigte das Gegenteil — dort
dominierte die Läufezahl.

**✔ S1 gemessen (25.08.): K1 trägt NICHT.** Totzone 0,25 / 0,5 / 1,0 ergeben
+3,92 / +3,78 / +3,82 — **Spanne 0,14 Punkte**, alle drei über ihrer Schwelle.
Die Trefferzahl ändert sich dabei um **+36 %** (12.367 → 16.826), die Quote
bleibt bei 38,1 %. **H lebt nicht von einer bestimmten Markenauswahl.**
Positivkontrolle punktgenau bestanden (erwartet +2,18, gemessen +2,18).

⚠⚠ **S4 gemessen (25.08.): K4 wirkt am stärksten — H trägt nur in einem
schmalen Altersfenster.** Mindestalter 250 / 500 / 750 ergibt +3,78 / +2,0 /
+1,0 bei Schwellen +3,4 / +3,7 / +4,9 — **nur der Bestandswert 250 trägt.**
Die Quote selbst fällt monoton (38,1 → 35,7 → 33,8 %), es ist also nicht die
dünnere Basis. Positivkontrolle bei 750 punktgenau bestanden.

**Die Gegenprüfung trennt Artefakt von Auswahl** (`messe_reifeband.py`):
bei **identischer Reihenmenge** fällt der Vorsprung von **+5,24** (Ankeralter
250–499) auf **+0,94** (ab 750) — Unterschied **+4,30 gegen Schwelle +3,18,
trägt**. Es ist das **Reifeartefakt**, nicht die Reihenauswahl.

⚠️ **Nur EINE von fünf Zellen trägt überhaupt:** LANG 250–499 (+5,24 gegen
+4,06), und sie deckt **36,9 %** der H-Fälle ab. **63 % der Fälle liegen in
Zellen, die nicht tragen.** Bei kurzen Reihen ist H sogar negativ (−4,48) —
die Vermutung „die jungen, kleinen Werte tragen H" ist widerlegt, wenn auch
nur beschreibend (die Trennung LANG/KURZ nutzt Zukunftsinformation).

**Was gilt:** H trägt in den Handelstagen 250–499 einer weiterlaufenden Reihe.
**Was nicht gilt:** „H ist widerlegt" — die tragende Zelle ist real. Sie ist
nur **viel kleiner als der bisher berichtete Befund**.

⚠️ **Folge für den Betrieb:** `vorfilter.py` prüft H **ohne**
Alterskriterium. Und **Kap. 120/121 stehen unter Vorbehalt** — die
Kategorienurteile wurden nie nach Ankeralter zerlegt; Small ist die Kategorie
mit den jüngsten Reihen.

**Kapitel 120/121 nach Ankeralter zerlegt (25.08.)** — die offene Rechnung aus
S4. Verhaltenskontrolle: die Bändersummen sind **identisch** mit Kap. 121
(2.292 / 4.734 / 6.540), die Zerlegung ist verlustfrei. Positivkontrolle
punktgenau bestanden.

| | 250–499 | 500–749 | ab 750 |
|---|---:|---:|---:|
| Large | +8,80 (S +10,52) | +8,18 (S +13,12) | +5,40 (S +9,25) |
| Mid | −0,25 | +2,19 | +4,21 |
| **Small** | **+7,77 (S +6,54) TRÄGT** | +6,07 (S +7,33) | **+0,44 (S +3,87)** |

**V1 (vorab benannt): Small ab 750 trägt nicht.** Small hat damit **keinen
nachweisbaren altersunabhängigen Kern**.
⚠️ **V2 (Differenz 250–499 gegen ab 750) verfehlt seine Schwelle**
(+7,33 gegen +9,04). Nach der Vorabfestlegung heißt das: **nicht entscheidbar,
als Zerlegung ablegen — NICHT „Small ist widerlegt".** Der Verlauf
+7,77 → +6,07 → +0,44 zeigt in diese Richtung, ist aber kein Nachweis.

**Large trägt in keinem Band** — konsistent mit S3, wo es bei korrekten
Blockgrenzen kippte. Zwei unabhängige Zerlegungen, derselbe Schluss.

⚠⚠ **KORREKTUR 25.08. abends — die Altersdeutung fällt.** Ein Nutzereinwand
(*„nicht das Alter der Assets, sondern u. U. der Reifegrad des Marktes"*) hat
einen Confounder aufgedeckt: **innerhalb derselben Reihe liegt das Band
250–499 immer früher in der Kalenderzeit** als das Band ab 750 (Median-Jahr
2022 gegen 2024). Beide Achsen gekreuzt gemessen:

| Ankeralter | bis 2022 | 2023–2024 | ab 2025 |
|---|---:|---:|---:|
| 250–499 | **+5,36 TRÄGT** | −3,98 | −3,48 |
| 500–749 | +4,05 | −14,66 | −9,79 |
| ab 750 | −3,90 | −5,15 | **+11,22 TRÄGT** |

**Alterseffekt +9,26 gegen Schwelle +9,25 → ZU KNAPP.
Zeiteffekt +8,84 gegen +9,10 → ZU KNAPP.** Zwei etwa gleich große Effekte,
keiner vom Zufall zu trennen. Positivkontrolle bestanden.

⚠️ **Die tragenden Zellen liegen DIAGONAL** — jung/früh und alt/spät. Wäre
das Alter die Ursache, dürfte die zweite nicht existieren. **S4s Satz „ab 750
trägt nicht" hält der Zerlegung nicht stand:** die +0,94 waren ein Mittelwert;
„ab 750, ab 2025" ist mit **+11,22 die stärkste Zelle der Messung**.

**Was bleibt:** die S4-Messung (H trägt bei 250, nicht bei 500/750).
**Was fällt:** ihre Deutung als Asset-Alter — und damit auch die Empfehlung
„die Watchlist ist zu alt für H".

**Was stattdessen gilt, und es ist nicht neu (Kap. 115):** *H trägt selten
viel, nicht durchgehend* — positiv in 7 von 20 Fenstern, über Breakeven in 2
von 20, ohne Beharrung. **H ist episodisch, und keine der vier geprüften
Achsen (Alter, Kategorie, Marktphase, Kalenderzeit) sagt vorher, wann.**

⚠️ **Bis S2 gelaufen ist, gilt jede H-Zahl dieser Karte unter Vorbehalt.**
Vorabfestlegung mit Messplan, Schwellen und vorab benannter Lesart:
`Vorabfestlegung_S1_S4_H_Annahmen_25_08.md`.

---

## 6. Was für den Betrieb gilt

⚠️ **Dieser Abschnitt stand bis Kapitel 124 auf dem Stand von 118** („nichts
ist umsetzungsreif, H liegt bei −0,3 unter seinem Breakeven"). Das war die
Lesart **mit der Bitpanda-Gebühr im Maßstab** und auf 347 Reihen. Seit 119
(zwei Sätze), 121 (523 Reihen) und 122 (echte Auswahl) gilt:

| | ohne Filter | mit H |
|---|---:|---:|
| Referenz 0,30 % | −0,031 R | **+0,114 R** |
| Betrieb 1,50 % | −0,182 R | **−0,036 R** |

**H ist gemessen wirksam (+0,15 R je Trade an beiden Sätzen) und zum
Betriebssatz trotzdem nicht profitabel.** Die bindende Größe ist der
Handelsplatz, nicht der Filter.

**Was das für einen Eingriff heißt:**

| | |
|---|---|
| H als **Vorfilter** (Signalzahl, LLM-Budget) | zulässig — er nimmt nachweislich die schlechteren weg |
| H als **Freigabe zum Handeln** | ⚠️ **nein — aber NICHT wegen der Gebühr**, siehe Korrektur 25.08. unten |
| Nachweis auf 29 Watchlist-Symbolen | Punktschätzer **+4,8**, stimmig, **nicht unabhängig bestätigbar** (122.3) |
| Handelbarkeit im dünnsten Band | ⚠️ **mit Kursdaten unprüfbar** (121.5) — 18 von 29 liegen dort |

**Die Überlebensverzerrung** ist seit 121 **korrigiert**: 523 Reihen inklusive
der 176 eingestellten Paare. H trägt dort **stärker**, nicht schwächer.

### ⚠️ 6.0 KORREKTUR 25.08.2026 — dieser Abschnitt fiel hinter Kapitel 119 zurück

**Nutzerhinweis 25.08.:** *„H sehe ich etwas anders bei der Freigabe — wieder
der Hinweis: **nicht der Handelsplatz oder die Gebühr entscheidet.** Wenn,
dann sollte der Standardsatz zur Anwendung kommen."*

**Er hat recht, und es ist kein Sonderfall, sondern ein Rückfall.** Kapitel 119
hat genau diesen Fehler bereits behoben:

> ⚠️ **„Der Fehler, der achtzehn Kapitel durchzogen hat."** Jedes Urteil der
> Kapitel 99–118 lief über den Abstand zum Breakeven — gerechnet wurde mit
> **1,5 %, also Bitpandas Brokerspread**.
>
> **Nutzer, 20.08.:** *„Die Kalkulation SOLL und MUSS börsenunabhängig
> passieren. Ich rede die ganze Zeit von einem GUTEN TRADE = Kurs &
> Wahrscheinlichkeit — das Gebührenthema ist NICHT das Thema eines NEUTRALEN
> Trades."*

**Die beiden Sätze oben blieben stehen und tun genau das wieder:**

| Satz | warum er so nicht gilt |
|---|---|
| *„zum Betriebssatz trotzdem nicht profitabel"* | richtig als **Geldrechnung**, falsch als **Qualitätsurteil** |
| *„Die bindende Größe ist der Handelsplatz, nicht der Filter"* | ⚠️ macht **Bitpandas Spread zum Maßstab für einen guten Trade** — genau das, was 119 verworfen hat |

**Was stattdessen gilt:**

> **H's Vorsprung ist gebührenfrei +4,5 Punkte** (Block-Permutation: Schwelle
> +2,6 → **TRÄGT**). Am **Referenzsatz 0,30 %**: +3,1 Punkte, **+0,114 R** je
> Trade. **Diese Zahl hängt an keinem Gebührensatz** — sie ist die Antwort auf
> *Kurs & Wahrscheinlichkeit*.

⚠️ **Damit ist H als Freigabe NICHT durch die Gebühr ausgeschlossen.** Nach
`Vollumstieg 15.08.` gilt ohnehin: *„System bemisst den Trade, Nutzer das
Portfolio."* Der Betriebssatz gehört in die **Geldrechnung der Mail**, nicht
in die Freigabeentscheidung.

### ⚠️ 6.0b Der ECHTE Grund, warum H noch nicht freigibt

Er steht in `agent/vorfilter.py` und hat mit Gebühren nichts zu tun:

> **„Der Befund steht auf fremden Reihen, nicht auf unseren."** Gemessen auf
> **523 Binance-USDT-Reihen**. Auf der echten Watchlist stimmt der
> Punktschätzer (**+4,8**) — aber **27 Reihen tragen die nötige Schwelle
> (+9,2) NICHT.**
>
> „Ein Schnitt dieser Größe wird nicht auf einen Befund von fremden Reihen
> gebaut. Deshalb erst der Schatten: vier Wochen mitschreiben, dann prüfen, ob
> die von H aussortierten Signale WIRKLICH die schlechteren waren — auf
> unseren eigenen."

**Dazu zwei Eigenschaften von H, die jede Freigabeentscheidung mitbestimmen:**

| | |
|---|---|
| **Seltenheit** | H trifft auf **3,3 % der Ankertage** zu — „aus 24 Eröffnungen würde ungefähr eine" |
| ⚠️ **nur LONG** | Kapitel 110: die Spiegelbedingung H' **spiegelt nicht**. Für SHORT ist H **unbelegt** → `h = None`, nicht `h = False` |

**Die Freigabeentscheidung hängt also an V2** (~20.09., vier Wochen Schatten),
**nicht am Gebührensatz.**

### 6.1 Was in der Produktion nachgeprüft wurde

| Merkmal | Kapitel | Urteil |
|---|---|---|
| **Strukturboden im Stop** (Unterstützung trägt den Stop) | **124** | **gebaut, verdrahtet, schadet nicht** — −0,0008 R, unter der Relevanzhürde |
| Teilverkauf bei +1R / Einstandstop | 123 | beide **schlechter** als durchhalten — **nicht** eingebaut |

⚠️ **124 hat auch ein Werkzeugproblem freigelegt:** bei 631.755 Ankern ist
fast jeder Effekt statistisch von null verschieden. Ein Urteil braucht
**Relevanz vor Vertrauensintervall** (Methodik 2.56).


---

# 7. Die Selektionsebene — was es gibt, was davon gemessen ist

**Angelegt am 22.08.2026 auf Nutzerfrage:** *„habe jetzt keinen Überblick mehr
zu dem Trichter Thema und welche Parameter im Bereich der Qualität und
Selektion vorhanden sind … mir fehlt der gesamte Plan bzw. das Bild dazu."*

⚠️ **Alles hier ist an der Quelle nachgesehen, nicht aus Plänen abgeschrieben.**
Zwei Einträge dieser Woche standen elf bzw. drei Tage zu Unrecht als offen.

## 7.1 Was heute wirklich sperrt — und es sind wenige

| Stufe | prüft | sperrt? | je gegen Zufall gemessen? |
|---|---|---|---|
| `anlass.sperrt()` | **ist das dieselbe Frage?** Fingerabdruck des Prompttexts, 24 h | **ja**, `anlass.aktiv: true` | ⚠️ **braucht keine Prognose** — „das haben wir schon gefragt" ist keine Qualitätsaussage |
| `asset_schalter.ist_handelbar()` | Bitpanda-Listing | **ja** | entfällt — Rahmenbedingung |
| `mail_richtung_erlaubt()` | `nur_long` | **nur den Versand** (seit 05.08.) | entfällt |
| `mindestkriterien.melde()` | hat die Rolle genug Grundlage? | **nein** — `sperren: []` | nein |
| CRV-Abstufung, Mindestgröße, Cooldowns | Geometrie und Takt | teils | **nein** |

> ⚠️ **Kein einziger dieser Regler ist je gegen den Zufall gemessen worden.**
> Der einzige gemessene Kandidat ist **H** — und der läuft seit dem 22.08. als
> Schatten, der nichts sperrt.

**Das ist kein Versäumnis, sondern die Vorgabe:** *„AUFGEMACHT um besser zu
werden — nicht einschränken, damit es weniger wird."* `anlass` ist bewusst so
gebaut, dass es **keine Prognose** braucht.

## 7.2 Was beschreibt, aber nichts sperrt — die vier Merkmale plus H

| # | Merkmal | Aussage | Stand |
|---|---|---|---|
| 93 A | **Trichter** | wie weit kann sich der Kurs bewegen | läuft |
| 93 B | **Rangplatz** | wo steht der Wert im Feld | läuft, **nur Krypto** |
| 93 C | **Lebendigkeit** | wächst die Nutzung des Projekts | sammelt, ab **18.09.** |
| 93 D | **Termine** | was steht an | läuft |
| 93 E | **Gesamtbild** | zählt die vier — *„1 dafür, 1 dagegen, 2 nicht bewertbar"* | läuft |
| V1 | **Vorfilter H** | Weg frei und Stop gedeckt | **Schatten seit 22.08.** |

⚠️ **„Noch nicht bewertbar" ist die häufigste Antwort, und das ist ehrlich.**
Wer daraus eine Note baute, bekäme eine Zahl, die Sicherheit vortäuscht.

## 7.3 Der Trichter — genau

**Eine Formel, keine Prognose:**

    Weite = Faktor × ATR × √Horizont

| Klasse | Faktor (80 %) | Grundlage |
|---|---:|---|
| **krypto** | **0,79** | 34 Reihen, 23.343 Anker |
| aktien | 0,91 | ⚠️ **2 Reihen**, 3.875 Anker |
| etf | 1,18 | ⚠️ 4 Reihen, 8.877 Anker |
| *Rückfall* | 0,90 | 40 Reihen, 36.095 Anker |

**Beispiel Krypto, Kurs 100 EUR, ATR 4:**

| Horizont | Spanne (80 %) | |
|---:|---|---:|
| 5 Tage | 92,9 – 107,1 EUR | ±7,1 % |
| 20 Tage | 85,9 – 114,1 EUR | ±14,1 % |
| 60 Tage | 75,5 – 124,5 EUR | ±24,5 % |

**Wozu er dient — die halbe Entscheidung:**
liegt der **Stop** innerhalb der üblichen Bewegung (dann wird er vom bloßen
Rauschen getroffen)? Ist das **Ziel** im gewählten Zeitraum überhaupt
erreichbar?

⚠️ **Er sagt die GRÖSSE, nie die RICHTUNG.** Volatilität clustert und ist
autokorreliert, Renditen sind es nicht — einer der robustesten Befunde der
Finanzökonometrie. Deshalb ein Trichter und keine Kurve.

⚠️ **Und die Faktoren sind gemessen, nicht aus dem Lehrbuch.** „1 ATR = 68 %"
gilt hier **nicht**: ATR misst die Tagesspanne, der Trichter die Änderung von
Schluss zu Schluss. Es gibt auch **keinen Faktor für alle Klassen** — die
erste Fassung hatte einen (0,98), und er passte auf keine einzige.

⚠️ **Er wirft, statt zu raten.** Ohne Kurs oder ATR gibt es keine Spanne —
eine erfundene Spanne wäre schlimmer als keine, weil Stop und Größe daran
hängen.

## 7.4 Die Reihung — und was du anders in Erinnerung hast

**Du hast recht, dass es sie gibt, und recht, dass sie Assets untereinander
vergleicht.** Sie rangiert **innerhalb derselben Anlageklasse** über 250
Handelstage:

> *Platz 7 von 41 Kryptowerten, im besten Fünftel (+34,2 % in diesem
> Zeitraum).*

⚠️ **Aber sie sagt NICHT, wer das beste Potenzial hat — und das ist gemessen,
nicht vermutet:**

| Rückblick / Horizont | Abstand bestes zu schlechtestem Fünftel | t | Schwelle |
|---|---:|---:|---:|
| 250 / **5 Tage** | **+1,01 %** | **3,20** | 3,11 |
| 250 / 20 Tage | +3,85 % | 2,54 | — |
| 250 / 60 Tage | +10,10 % | 1,58 | — |

**Genau ein Feld von 27 hält die Schwelle** — ausgerechnet das kürzeste. Und
+1,01 % Abstand heißt rund **+0,5 % für das beste Fünftel gegenüber dem
Markt**, bei **3 % Handelskosten**.

> **Der Vorteil ist gemessen und gleichzeitig zu klein, um ihn zu bezahlen.**
> Deshalb steht in der Mail ein Rangplatz und keine Empfehlung — mit genau
> diesem Satz daneben.

**Drei Einschränkungen gehören dazu:** ohne den letzten Monat im Rückblick
fällt t von 3,20 auf 1,68 · der Effekt lebt in der **auswahlverzerrten**
nachgeladenen Zeit · beide Hälften der Symbolliste zeigen dasselbe Vorzeichen,
keine ist für sich signifikant.

⚠️ **Und er läuft nur für Krypto.** `drift.saetze()` gibt für alle anderen
Klassen eine leere Liste zurück.

## 7.5 Marktphasen — wir schalten bewusst NICHTS um

**Nachgesehen: kein einziger Parameter wird nach Marktphase umgeschaltet.**
Weder in `rollen_lauf`, noch in `entscheidungsrechnung`, `mindestkriterien`
oder `betraege`.

**Das ist Absicht, und der Grund ist teuer bezahlt.** Ein binäres Etikett
(„Bär"/„Bulle", „über/unter der 200-Tage-Linie") verleitet zur Binärlesung —
und genau ein solches Etikett hat den Deadloop gebaut. `_struktur()` nannte
eine Lage „intakter Abwärtstrend", während die Jahreszahl daneben stieg.

**Stattdessen beschreibt das Lagebild die Phase in ZAHLEN:**

| | Quelle |
|---|---|
| eigene Rendite über 12 Monate **und** über 60 Handelstage | Moskowitz/Ooi/Pedersen, *Time Series Momentum*, JFE 2012 |
| Lage zwischen Jahrestief und Jahreshoch, **beide Ränder** | George/Hwang, *The 52-Week High*, JF 2004 |

Laufen die beiden Trendzahlen auseinander, ist das eine Korrektur — der Leser
sieht das, statt ein Etikett zu bekommen.

**Und die Messseite sagt dasselbe:**

| Befund | Kapitel |
|---|---|
| **H überträgt sich NICHT über einen Regimewechsel** | 109 |
| Die Marktphase wirkt **nicht invers** — 6 von 6 Punktschätzern dagegen | 114 |
| Die Spiegelbedingung H' **spiegelt nicht** — hilft im Bullen, schadet im Bär, wie H | 110 |
| ⚠️ **Das Regime war im gesamten Messzeitraum „bär"** | Memory |

> ⚠️ **Daraus folgt eine Regel, keine Lücke:** „Modell oder Markt?" ist mit
> unseren Daten **unbeantwortbar**, weil es nie eine zweite Phase gab. Die
> Marktphase taugt höchstens als **Schichtung** einer Messung, nie als
> Schalter für einen Parameter.

## 7.6 Die Anlageklassen — der ehrliche Stand

| | Trichter | Rangplatz | Lebendigkeit | Rolle G | **H gemessen** |
|---|---|---|---|---|---|
| **krypto** | eigener Faktor (34 Reihen) | ✔ | ✔ | **2 Quellen** | **✔ 523 Reihen** |
| aktien | eigener Faktor ⚠️ **2 Reihen** | ✘ | ✘ | **2 Quellen** | ✘ **nie** |
| etf | eigener Faktor ⚠️ 4 Reihen | ✘ | ✘ | **0 Quellen** | ✘ **nie** |
| rohstoffe | *Rückfall* | ✘ | ✘ | **2 Quellen** | ✘ **nie** |
| hedge | *Rückfall* | ✘ | ✘ | **0 Quellen** | ✘ **nie** |

> ⚠️ **KORREKTUR 25.08.2026.** Diese Spalte stand bis heute mit
> „0 Quellen“ für **vier** Klassen. An der Quelle geprüft ist das für
> **zwei** falsch: `positionierung.py:709` führt seit dem 17.08. den
> Aktien-Zweig (Eindeckungsdauer FINRA + Insidergesäfte SEC),
> `:728` den Rohstoff-Zweig (COT-Perzentil + physische ETF-Metallmenge);
> `mindestkriterien.QUELLEN_G:114-128` führt beide Paare, `MINDEST_QUELLEN_G`
> ist 2. **Richtig bleibt es für ETF und Hedge** — für die gibt es in
> `positionierung.lage` überhaupt keinen Zweig. Der Befund darunter
> „vier Klassen nicht verdrahtet“ war also zur Hälfte veraltet.

**Zwei verschiedene Ursachen, und nur eine ist lösbar:**

**(1) Das Universum ist zu klein** — 2 Aktien, 4 Rohstoffe, 5 Themen-ETF,
2 Hedge. Externer Standard sind 30 aufgelöste Fälle als Untergrenze, 100+ für
Belastbarkeit. **Bei dieser Größe entsteht in keiner Nicht-Krypto-Klasse je
eine auswertbare Stichprobe** — unabhängig davon, wie gut der Code wird. Das
steht als **C1** im Zwischenstand: *Nutzerentscheidung, Code kann das nicht
lösen.*

**(2) Rolle G ist für ZWEI Klassen nicht verdrahtet** (Stand 25.08.) — und
das **ist** lösbar. Für Aktien und Rohstoffe wurde es am 17.08. nachgeholt
(`finra`, `sec_edgar`, `cftc_cot`, ETF-Metallbestand). Offen sind **Themen-ETF
und Hedge**: dort gibt es in `positionierung.lage` keinen Zweig, `saetze()`
bleibt leer, `zweite_meinung.py:549-550` bricht ab. Deshalb steht dort 0 von 2
Quellen, und deshalb bleibt `sperren: []` leer — ein scharfes Kriterium hätte
Rolle G für diese beiden Klassen sofort stillgelegt.

⚠️ **Der Vorfilter-Schatten läuft ab dem 22.08. über ALLE Klassen** — mit dem
Vermerk „auf dieser Klasse nie gemessen". Sonst hätten wir in vier Wochen
wieder nur Krypto-Daten.

## 7.7 Das Bild in einem Satz

> **Es gibt genau eine gemessene Selektionsgröße (H, nur Krypto), vier
> beschreibende Merkmale ohne Sperrwirkung, und keinen einzigen betrieblichen
> Regler, der je gegen den Zufall geprüft wurde. Die Marktphase schaltet
> nichts, weil sie es nach allem Gemessenen nicht darf.**

## 7.8 Was daraus als Reihenfolge folgt

| | Schritt | Voraussetzung | frühestens |
|---|---|---|---|
| **1** | **V1 läuft** — H im Schatten, alle Klassen | — | **läuft** |
| **2** | **V2**: waren die von H aussortierten Signale die schlechteren? | ~4 Wochen aufgelöste Signale | **~20.09.** |
| **3** | **93 C auswerten** (TVL) | 30 Messungen | **18.09.** |
| 4 | **Rolle G für Aktien/Rohstoffe/ETF verdrahten** | die drei Clients anschließen | jederzeit |
| 5 | Strukturboden auch für **SHORT** messen | Erweiterung von `pruefe_strukturstop.py` | jederzeit |
| 6 | **93 C** (Entwickler) | 12 Wochenmessungen | **09.11.** |
| 7 | **Nachrichten** (C3) — die einzige nie erprobte Informationskategorie | Konzept | offen |

⚠️ **Schritt 4 ändert die Datenlage, nicht das Universum.** Er macht Rolle G
für die anderen Klassen überhaupt erst urteilsfähig — die Stichprobengröße
(C1) bleibt davon unberührt.
