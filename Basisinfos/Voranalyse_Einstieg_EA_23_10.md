# Voranalyse E-A — REGEL0 als Kaufzeitpunkt für ohnehin geplante Spot-Käufe auf Bitpanda (ab 23.10.2026)

**Wozu:** Nutzer 23.10.: *„ja E-A Messplan festlegen, prüfen, gegenprüfen und Doku, auf BP“*. Seine Hinweise:

1. Du hast REGEL0 schon bei Spot geprüft, und das wurde als Einstieg negativ bewertet? Also prüfen, was wir schon wissen.
2. Wir bleiben auf BP als Börse.
3. Welche Strategien und Zeiträume decken wir ab? Das muss zum Teil über mehrere Jahre erfolgen (auch recherchieren). Annahme: BTC 1 Jahr Bärenmarkt? 4-Jahres-Zyklus noch intakt?
4. Wie gehen wir mit Abweichungen und unterjährigen Regimewechseln um?

**Ausgangslage:** E-131. REGEL0 schlägt Zufallsstunden derselben Coins um +0,6 Pp (2025) bzw. +0,3 Pp (2026) je 24 h. Drift und Kosten zehren das beim Handeln auf.

## 1. Was wir schon wissen (Hinweis 1)

| Messung | Frage | Ergebnis | Unterschied zu E-A |
|---|---|---|---|
| **M-0c L3** (Spot §7.4, 05.10.) | Trägt der REGEL0-Einstieg **als eigener Handel** ohne Hebel, gehalten 72 / 120 / 480 h? Rang des **Ertrags** gegen Zufallsstunden desselben Coins im selben Monat | **nein**: 72 h und 120 h **unter** dem Zufall (Rang 0,488–0,498); 480 h 2025/26 knapp darüber (0,517 / 0,512), 2024 nicht (0,502) | M-0c misst einen **Handel** mit eigenem Ende. Bei E-A wird ein Kauf ohnehin getätigt und gehalten; gemessen wird nur der **Kaufpreis gegenüber dem geplanten Tag**. ⚠️ M-0c zeigt aber: Der 24-h-Vorsprung ist **schon nach 72 h weg**. Der Kurs gibt die Erholung wieder ab. Für einen dauerhaft gehaltenen Kauf zählt nur der Preis beim Kauf; der kann trotzdem besser sein, ist aber vermutlich klein |
| Spot §2 | Live-Signale der alten Kette (Juli–Okt. 2026) | Zeitpunkt ≈ Zufall | alte Kette, nicht REGEL0 |
| F1–F3 (Spot §8) | Klima-Kaufregeln gegen regelmäßiges Kaufen | regelmäßiges Kaufen nicht zu schlagen | Klima = langsame Phase; E-A = Kurzfrist-Zeitpunkt **innerhalb** weniger Tage |
| D1 (Spot §12) | Aufbau der Kernwerte | 70/20/10 BTC/ETH/SOL, Ausgleich über die Raten (E-69) | E-A setzt genau dort an: Wann im Monat wird gekauft? |

⇒ **Ehrliche Vorab-Erwartung:** klein. Es geht um Zehntelprozent je Kauf, und M-0c spricht gegen einen anhaltenden Vorsprung. Die Messung ist trotzdem sinnvoll und billig: Der Kauf findet ohnehin statt, also kostet das Timing nichts außer dem Warten.

## 2. Börse (Hinweis 2)

Bitpanda: Spot über den Broker oder Fusion, Limit-Kauf bei Spot fast überall möglich (Nutzer 23.10.). Die Kosten eines **ohnehin geplanten** Kaufs sind in beiden Fällen gleich (ein Kauf). Sie gehen deshalb nicht in den Vergleich ein (Regel 2).

## 3. Strategien und Zeiträume (Hinweis 3)

| Strategie | Horizont | E-A greift? |
|---|---|---|
| **Akkumulation Kernwerte** BTC/ETH/SOL (70/20/10, monatliche Rate, E-69) | mehrere Zyklen | **ja**: der Kaufzeitpunkt der Monatsrate |
| Altcoin-Spot L (Season-Option, Kauf in Tranchen auf Freigabe) | Monate bis 1–2 Jahre | **ja**: Zeitpunkt jeder Tranche |
| Hebel REGEL0 | 24 h | nein (eigener Strang) |

**Zeiträume:**
- REGEL0-Einstiege liegen für **2024-01 bis 2026-08** vor, also für einen Bullenmarkt (2024), das Hoch (Okt. 2025) und den Bärenmarkt seit Okt. 2025.
- Das ist **ein halber Zyklus**. Für mehrere Zyklen (2018, 2022) müssten die REGEL0-Signale für 2018–2023 neu erzeugt werden; dafür bräuchte es die BTC-Stundendaten vor 2023-09 (Download, Ja nötig). Das ist **Stufe B**, erst nach Stufe A und nur, wenn A einen Hinweis liefert.
- Zum 4-Jahres-Zyklus und zur Dauer der Bärenmärkte: Recherche (§6).

## 4. Abweichungen und Regimewechsel unterjährig (Hinweis 4)

- **E-A sagt kein Regime voraus**, und das ist Absicht (2.599: Der Marktzustand ist vorab nicht erkennbar).
- Die Regel verschiebt einen Kauf **höchstens N Tage**. Ein Regimewechsel kann sie also nur innerhalb dieses Fensters treffen.
- **Ausgewertet wird je Regime getrennt:** Phasen aus dem BTC-Kursverlauf (Zickzack −20 % / +25 %, aus den Kursen, nicht aus dem Ergebnis). Trägt E-A nur in einem Regime, ist das sichtbar.
- **Abweichungen vom Plan** werden begrenzt: Kommt im Fenster kein Signal, wird am Fensterende gekauft (Rückfall). Der Sparplan wird also nie ausgesetzt.

## 5. Messplan E-A Fassung 1 — VORAB festgelegt

| | festgelegt |
|---|---|
| geplante Käufe | am **1. jedes Monats**, 00:00 UTC, je Coin; Preis = Stundenschluss dieser Stunde (P_plan) |
| Coins | **Kern** BTC, ETH (SOL wo vorhanden) und **alle** Coins mit REGEL0-Einstiegen als Altcoin-Klasse; vier Mengen |
| Regel | Kauf zum Schluss der ersten REGEL0-**Einstiegsstunde** innerhalb von **N Tagen** nach dem geplanten Zeitpunkt; kommt keine, Kauf zum Schluss am Fensterende |
| Fenster N | 3, 7, 14 Tage |
| **Zielgröße** | Kaufvorteil = P_plan / P_Kauf − 1 (mehr Stück für denselben Betrag; bei gleichem Halteende ist das genau der Mehrwert) |
| **Nullwelt** | dieselbe Regel, aber die „Signale“ sind **Zufallsstunden** desselben Coins im selben Fenster, mit gleicher Zahl je Fenster; 200 Ziehungen; Rang = Anteil mit kleinerem Mittel |
| **Wahl auf 2024** | das N mit dem höchsten mittleren Kaufvorteil (Mittel der vier Mengen, alle Coins) |
| **Bestätigung** | 2025 und 2026 getrennt, für Kern und Altcoins |
| **trägt, wenn** | mittlerer Kaufvorteil > 0 **und** Rang ≥ 0,90 in **beiden** Jahren in **allen drei** unverzerrten Mengen (Altcoins); für den Kern (wenige Fälle) gemeinsam über die Mengen |
| Auskunft | je Regime-Phase (BTC-Zickzack −20 % / +25 %); Limit-Variante (Limit 0,5 % unter dem Signal-Schluss, 4 h gültig, sonst Kauf zum Schluss nach 4 h); Anteil mit Rückfall |
| **Selbsttest VOR dem ersten Blick** | (a) Zufallspfad mit zufälligen „Signalen“ → Kaufvorteil ≈ 0 und Rang gleichverteilt; (b) Positivkontrolle: „Signale“ an lokalen Tiefs → Kaufvorteil > 0, Rang ≥ 0,95. Fällt (a) oder (b) durch, wird nicht gemessen |
| Folgen | **trägt** → Voranalyse Betrieb (Sparplan-Mail *„Kaufsignal für die Monatsrate“* bzw. Limit-Order über Fusion) und Stufe B (mehrere Zyklen). **trägt nicht** → E-A ist erledigt; der Kauf am festen Tag bleibt |

### 5.1 Selbsttest sperrt Fassung 1 – Zielgröße verzerrt, Fassung 1b VORAB (23.10.2026)

- **Selbsttest Fassung 1:** Zufallssignale auf einem Zufallspfad ergeben einen Kaufvorteil von **+0,52 %** (Soll ≈ 0); die Ränge streuen 0,10–0,98; die Positivkontrolle ergibt +6,3 % (Rang 1,00). Nach Plan wurde **nicht gemessen**.
- **Ursache:** P_plan / P_Kauf − 1 ist wegen der **Konvexität** (Jensen) auch bei reinem Zufall im Mittel positiv. Wer später zu einem zufälligen Preis kauft, bekommt im Mittel mehr Stück; diese sind am Ende im Mittel aber **nicht mehr wert**.
- **Fassung 1b (einzige Änderung):**
  - Zielgröße ist der **Wertunterschied je eingesetztem Euro an einem gemeinsamen Endpunkt T** = Fensterende + 24 h: P_T / P_Kauf − P_T / P_plan.
  - Bei einem Zufallspfad ist sie im Mittel null, für jeden Kaufzeitpunkt.
  - Nach T halten beide Käufe gleich viel Wert im Verhältnis, das Ergebnis gilt also auch für ein längeres Halten.
- Alles andere bleibt wie §5. Kein echtes Ergebnis ist bisher angesehen.

## 6. Recherche 4-Jahres-Zyklus und Bärenmarktdauer

*(folgt, Recherche läuft)*

## 7. Ergebnis E-A Fassung 1b: TRÄGT NICHT – das Vorzeichen wechselt mit dem Jahr (23.10.2026; `p70_ea_kaufzeitpunkt.py`, `p70_gegenprobe.py` → `.txt`)

**Selbsttest:** bestanden. Zufallssignale auf einem Zufallspfad ergeben +0,05 % (Gegenprobe G3 mit anderem Startwert: −0,06 bis −0,09 %); die Positivkontrolle ergibt +5,9 %, Rang 1,00.

**Wahl auf 2024** (alle Coins): N = 3 / 7 / 14 Tage ergeben +2,02 / +3,14 / +2,66 %. **Gewählt: 7 Tage.**

**Bestätigung, Kaufvorteil je eingesetztem Euro** (Wertunterschied am gemeinsamen Endpunkt):

| | 2025 | 2026 |
|---|---|---|
| Altcoins unverzerrt 1 / 2 / 3: REGEL0 | +2,37 / +2,08 / +2,09 % | −0,69 / −0,15 / −0,71 % |
| Altcoins: Nullwelt (Zufallsstunden im Fenster) | +2,68 / +2,53 / +2,50 % | −1,53 / −1,03 / −1,41 % |
| **Altcoins: Rang REGEL0 gegen Nullwelt** | **0,01 / 0,00 / 0,00** | **1,00 / 1,00 / 1,00** |
| Kern BTC/ETH/SOL (vier Mengen gemeinsam): REGEL0 / Nullwelt / Rang | +0,42 / +0,83 / **0,05** | +1,66 / +0,30 / **1,00** |
| Limit-Variante (0,5 % unter dem Signal) | ≈ wie ohne Limit (+0,02 bis +0,07 Pp) | ≈ wie ohne Limit |

**Urteil nach §5: TRÄGT NICHT.**
- 2025 kauft REGEL0 innerhalb der Woche **schlechter** als ein zufälliger Zeitpunkt, 2026 **besser**.
- Kern und Altcoins zeigen dasselbe Bild.
- Der Kauf am festen Tag bleibt.

**Gegenprobe:**
- G1: eigene Schleife, gleich.
- G2 ✘ (Fairness): REGEL0 kauft im Fenster im Mittel **später** als die Nullwelt (2025 88,6 h gegen 76,4 h). 2025 war späteres Kaufen günstiger; der Unterschied hilft REGEL0 also und erklärt den schlechten Rang **nicht**.
- **G5, Nullwelt mit gleicher Wartezeit:** 2025 Rang **0,00**, 2026 Rang **1,00**. Das Urteil steht.
- G3: Selbsttest mit anderem Startwert ✔.
- Auskunft G4: Monate, in denen REGEL0 vorn liegt: 2025 50 %, 2026 75 %.

**Auskunft je Regime** (BTC-Zickzack −20 % / +25 %, unverzerrt 1, alle Coins, 7 Tage):

| Regime | Kaufvorteil REGEL0 | Nullwelt | Rang |
|---|---|---|---|
| steigend | −1,98 % | −1,79 % | **0,03** |
| fallend | +6,19 % | +5,93 % | **0,99** |

- Im **fallenden** Markt kauft REGEL0 besser als der Zufall, im **steigenden** schlechter.
- Das Regime ist vorab nicht erkennbar (2.599). Ein Schalter darauf wäre die schon gescheiterte Timing-Frage.
- Fast der ganze Kaufvorteil ist **Wartedrift**: Im fallenden Markt ist **jedes** Warten gut (+6 %), im steigenden schlecht (−2 %). Er ist kein Vorteil von REGEL0.

#### Zwischenfazit

| | |
|---|---|
| **Was das Ergebnis heißt** | REGEL0 trifft nach einem Rückgang einen Zeitpunkt, der **24 h** lang besser ist (E-131). Für einen **gehaltenen** Kauf hängt der Vorteil am Regime und kippt mit ihm. Das bestätigt M-0c: Der Vorsprung ist nach 72 h weg |
| **Was folgt** | E-A ist für die Kernwerte und Altcoin-Käufe **erledigt**; Stufe B (mehr Zyklen) entfällt, weil schon Stufe A keinen Hinweis liefert |
| **Für die Frage „ist REGEL0 ausgereizt?“** | Auf Bitpanda sind jetzt alle Wege geprüft: Kosten (Haltedauer, Limit), Auswahl, Timing geplanter Käufe. Trägt das Signal, dann nur als 24-h-Handel mit niedrigen Kosten (Kraken, E-130) |
