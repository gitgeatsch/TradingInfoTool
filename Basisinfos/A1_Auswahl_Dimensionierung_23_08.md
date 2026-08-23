# A1 — die Auswahl: was das Wort verdeckt, und wie sie zu dimensionieren ist

*Nutzerfrage 23.08.: „Was meinst du konkret mit **Auswahl**? Hier versteckst du
gerne Fakten, die erst später in der Diskussion genannt werden." — und der
Auftrag dazu: „prüfe, messe und recherchiere ausgiebig, damit dieser Schritt
tatsächlich sitzt. Ich würde sogar so weit gehen, ihn neu zu dimensionieren
oder zu erweitern, wenn erforderlich."*

> **Der Einwand ist berechtigt.** „Auswahl" ist ein Sammelwort. Darunter
> stecken zehn Entscheidungen, von denen ich **eine einzige** genannt hatte.
> Hier stehen alle zehn, jede mit ihrer Messung oder mit dem ausdrücklichen
> Vermerk, dass sie offen ist.

---

## 1. Die zehn Entscheidungen, die im Wort steckten

| # | Frage | Antwort | woher |
|---|---|---|---|
| **1** | **Wie viele?** (`k`) | **2** | gemessen, §3 |
| **2** | Woraus — je Gruppe oder über alle? | je Gruppe | ⚠️ nur Krypto hat ein Universum, §5 |
| **3** | Auswahl **wofür** — wer wird bewertet, oder wer wird Signal? | **vor der Kette** | Vorschlag, §6 |
| **4** | Was passiert mit den **nicht** Gewählten? | NICHTS_TUN mit Grund „Rang 17 von 40" | folgt aus Ihrem Grundsatz |
| **5** | **Wie oft** wird gewählt? | **alle ~20 Handelstage**, nicht je Umlauf | gemessen, §4 |
| **6** | Was ist mit **Bestand**? | Auswahl betrifft **Einstiege**; ein gehaltener Wert, der im Rang fällt, ist die **Verkaufsfrage** | ⚠️ nicht vermischen, offen |
| **7** | Ersetzt sie **Cooldown** und **Fingerabdruck**? | Cooldown **ja** (er sperrt 30 von 30 ohne Grund), Fingerabdruck **nein** (er *ist* ein Grund) | §6 |
| **8** | Welche **Ranggröße**? | 250-Tage-Rendite | einziges Feld, das die Placebo-Schwelle hielt |
| **9** | **Dünne Gruppen**? | unter ~10 Symbolen ist „die besten 2 von 2" keine Auswahl | §5 |
| **10** | ⚠️ **Und wenn alle schlecht sind?** | **das war die versteckteste Annahme** — eine Rangliste hat *immer* einen Sieger | gemessen, §4 |

---

## 2. Punkt 10 zuerst — die Literatur kennt genau diese Lücke

Eine reine Rangauswahl unterstellt lautlos: **es wird gekauft.** Die Antwort der
Literatur heißt **Dual Momentum**:

> Antonacci (2014) verbindet die **relative** Auswahl mit einem **absoluten**
> Trendfilter: Werte werden nach relativer Stärke gewählt und **nur aufgenommen,
> wenn sie auch für sich genommen positives Momentum haben**.
> — [Optimal Momentum](https://www.optimalmomentum.com/dual-relative-absolute-momentum/) ·
> [QuantPedia](https://quantpedia.com/dual-vs-single-momentum-in-commodities-enhancing-risk-adjusted-returns-through-absolute-trend-filtering/)

> **Relativ entscheidet WELCHEN. Absolut entscheidet OB.**

**Beides ist im Projekt vorhanden — gemessen war nur die erste Hälfte.**

---

## 3. Wie viele? — `k = 2`, und der Vorteil zerfällt schnell

40 Symbole, 3.290 Tage, Vorwärtsrendite **barrierenfrei und brutto**,
Newey-West über 1.874 Termine.

| k | Horizont 5 · Abstand | t | Horizont 20 · Abstand | t |
|---:|---:|---:|---:|---:|
| 1 | +0,73 % | 1,93 | +4,55 % | 4,21 |
| **2** | **+0,79 %** | **3,29** | **+2,74 %** | **4,52** |
| 3 | +0,43 % | 2,22 | +1,11 % | 2,37 |
| 5 | +0,17 % | 1,22 | +0,46 % | 1,15 |
| 8 | +0,15 % | 1,58 | +0,37 % | 1,29 |

⚠️ **Ab k = 5 ist nichts mehr da.** Mein ursprünglicher Vorschlag „die besten k"
mit einem Fünftel (8 von 40) hätte **genau nichts** ausgewählt — das ist der
erste Fakt, den das Wort „Auswahl" verdeckt hat.

**`k = 1` ist nicht besser als `k = 2`,** trotz höherer Rendite: der t-Wert ist
niedriger, weil ein einzelner Wert stärker schwankt. **Zwei ist die Stelle mit
dem besten Verhältnis.**

---

## 4. ⚠️ Und wann wird gar nicht gekauft? — nicht der Wert entscheidet, sondern der Markt

**Der Trendfilter am Einzelwert (Lehrbuch-Dual-Momentum) bringt hier nichts:**

| k = 2, Horizont 5 | Abstand | t | Termine ohne Auswahl |
|---|---:|---:|---:|
| nur Rang | **+0,79 %** | **3,29** | 0 |
| + absoluter Filter am Wert | +0,71 % | 2,62 | **228 von 1.874** |

Er sperrt 12 % der Termine und verbessert nichts — die besten zwei nach
250-Tage-Rendite sind fast immer ohnehin gestiegen.

**Der Marktzustand dagegen entscheidet alles:**

| Zustand (BTC zu seinem 200-Schnitt) | Termine | Auswahl | Markt | Abstand | t |
|---|---:|---:|---:|---:|---:|
| **darüber** | 973 | **+1,45 %** | +0,53 % | **+0,91 %** | **3,58** |
| **darunter** | 901 | +0,08 % | +0,17 % | −0,09 % | −0,46 |

> ⚠️ **Die Auswahl trennt nur, solange der Markt über seinem eigenen Schnitt
> steht.** Darunter trennt sie nicht, und die absolute Rendite ist mit +0,08 %
> über fünf Tage praktisch null — vor Kosten.

**Damit ist das „OB" gemessen — und es ist Ihr G4-Punkt:** der Marktzustand als
**stetige Größe**, nicht als Etikett. Nicht der Einzelwert, sondern der Markt
sagt, ob überhaupt gekauft wird.

---

## 5. ⚠️ Der Fakt, den ich fast wieder verdeckt hätte: die Kosten der Drehung

**Für die Auswahl ist die Kostenhürde bezahlt — für die DREHUNG nicht.** Wer
alle fünf Tage umschichtet, erzeugt Handel, den es sonst nicht gäbe:

| k = 2 | brutto | netto bei **0,30 %** je Seite *(Referenz)* | netto bei **1,50 %** je Seite *(Bitpanda)* |
|---|---:|---:|---:|
| Horizont **5** | +1,14 % | +0,54 % | ⚠️ **−1,86 %** |
| Horizont **20** | **+4,57 %** | **+3,97 %** | **+1,57 %** |

> **Der Fünftagesrhythmus trägt seine eigenen Betriebskosten nicht.** Der
> Zwanzigtagesrhythmus trägt sie — **und zwar auch zum Bitpanda-Satz.**

⚠️ **Das ist, soweit ich sehe, die erste Konfiguration dieses Projekts, die
ihre eigene Kostenhürde brutto UND netto überschreitet.** Deshalb steht sie
hier mit allen Vorbehalten aus §7.

---

## 6. Wofür die Auswahl gilt — und was sie ersetzt

| | Vorschlag | Begründung |
|---|---|---|
| **Ort** | **vor der Kette** — sie bestimmt, welche Symbole überhaupt beurteilt werden | spart Modellaufrufe und liefert die Begründung je Symbol |
| **Cooldown** | **wird ersetzt** | er sperrt heute 30 von 30 und beantwortet „soll", nicht „kann" — die Uhr entscheidet |
| **Fingerabdruck** | **bleibt** | er beantwortet „hat sich etwas geändert" — das *ist* ein Grund |
| **Nicht Gewählte** | NICHTS_TUN mit **„Rang 17 von 40"** | jede Entscheidung braucht eine Begründung |
| **Takt** | ~20 Handelstage | §5 |
| ⚠️ **Bestand** | **nicht Teil von A1** | ein gehaltener Wert, der im Rang fällt, ist die **Verkaufsfrage**. Sie hier mitzuentscheiden wäre genau die Vermischung, die A1 vermeiden soll |

**Dünne Gruppen:** Krypto hat 40 Symbole. **Aktien 2, ETF 4, Rohstoffe 3.**
⚠️ **Dort ist „die besten 2" keine Auswahl, sondern eine Umbenennung.** A1 gilt
zunächst **nur für Krypto**.

---

## 7. ⚠️ Die Vorbehalte — vollständig, nicht nachgereicht

| | |
|---|---|
| **Mehrfachprüfung** | Ich habe **24 Zellen** angesehen (5 × k, 2 Filter, 2 Horizonte, 4 Marktzustände). Der eigene Suchpreis: 300 Zellen = +20,5 Punkte Hürde, **eine vorab benannte = +10,2**. Die empirische Placebo-Schwelle lag bei **\|t\| ≥ 3,05** — k=2/H20 (4,52) und der Marktzustand (3,58) liegen darüber, k=2/H5 (3,29) knapp |
| **Überlebensverzerrung** | die gestorbenen Werte fehlen. Sie wären im **schlechtesten** Fünftel gewesen — die Auswahlrendite ist **nach oben verzerrt** |
| **B3-Auflage** | das eigene Werkzeug verlangt: dieselben Felder müssen **auf einer anderen Anlageklasse und in einzelnen Jahren** tragen. **Offen** — und mit 2 Aktien und 4 ETF derzeit **nicht erfüllbar** |
| **Ein Zyklus** | neun Jahre Krypto sind rund zwei Zyklen, nicht zwanzig |
| **Der Marktzustand ist selbst geschätzt** | die 200-Tage-Grenze ist eine Konvention, keine Messung |

---

## 8. Was ich als nächsten Schritt vorschlage

**Vor dem Bau eine einzige Prüfung, und sie ist vorab benannt** — damit sie
nicht wieder eine Zelle unter vielen ist:

> **Trägt `k = 2`, Horizont 20, mit dem Marktzustand als Schranke auch in
> jedem einzelnen Jahr — und nicht nur im Mittel über neun?**

Fällt sie durch, ist A1 in dieser Form nicht zu bauen. Besteht sie, ist die
Dimensionierung festgelegt und der Bau ist klein: `drift.rang()` liefert die
Zahl bereits.


---

## 9. ⚠️ Die vorab benannte Prüfung — ausgeführt, und sie fällt gemischt aus

**Die Frage stand in §8, bevor sie gerechnet wurde:** trägt `k = 2`,
Horizont 20, mit dem Marktzustand als Schranke auch **in jedem einzelnen
Jahr**?

| Jahr | Termine | Auswahl | Markt | Abstand | relativ | absolut nach 3 % |
|---|---:|---:|---:|---:|---|---|
| 2021 | 119 | **+15,95 %** | +7,20 % | **+8,75 %** | ✔ | ✔ |
| 2023 | 294 | **+12,48 %** | +5,61 % | **+6,87 %** | ✔ | ✔ |
| 2024 | 293 | +6,12 % | +6,13 % | **−0,01 %** | ⚠️ **nein** | ✔ |
| 2025 | 267 | **−2,56 %** | −6,22 % | +3,66 % | ✔ | ⚠️ **nein** |

**3 von 4 auswertbaren Jahren mit positivem Abstand.**

⚠️ **Aber das ist keine saubere Bestätigung, und das gehört so gesagt:**

- **2024 trennt nicht** (−0,01 %) — die Auswahl war exakt der Markt.
- **2025 trennt, verliert aber absolut** (−2,56 %). Die Schranke stand offen,
  und es wäre trotzdem Geld verloren gegangen. **Ein offenes Tor ist keine
  Gewinngarantie.**
- ⚠️ **Nur vier Jahre sind überhaupt auswertbar.** In den übrigen fünf stand
  BTC unter seinem Schnitt — die Schranke war zu. Das ist gewollt, begrenzt
  aber, wieviel Beleg sich je ansammeln kann.

---

## 10. Was ich daraus als Fachexperte empfehle

**Die Frage ist nicht, ob die Rangauswahl gut ist. Die Frage ist, ob sie besser
ist als das, was heute auswählt.**

| Auswähler | Beleg |
|---|---|
| **heute: die Uhr** (Cooldown) | ⚠️ **keiner.** Sie sperrt 30 von 30 und beantwortet „soll", nicht „kann" |
| **Rangplatz** | t = 3,29 (H5) / 4,52 (H20), 3 von 4 Jahren, Placebo-Schwelle 3,05 |

> **Wir vergleichen den Rang nicht mit einem perfekten Auswähler, sondern mit
> der Uhr — und die hat null Beleg.** Unter dieser Fragestellung ist der
> Wechsel auch bei gemischter Jahresprobe begründet.

**Deshalb, getrennt nach Belegstärke:**

| | was | Form | warum |
|---|---|---|---|
| **A1a** | **Rangplatz ersetzt den Cooldown** als Auswähler, `k = 2` je Gruppe | **hart** | er beantwortet „welchen", und die Uhr hat dazu nichts zu sagen |
| **A1b** | **Marktzustand** (BTC zum 200-Schnitt) | ⚠️ **weich — Anzeige und Datenbank, sperrt nichts** | im Mittel stark (t 3,58 gegen −0,46), je Jahr aber gemischt. Als Schatten sammelt er Beleg, ohne Signale zu kosten |
| **A1c** | Takt der Auswahl | **~20 Handelstage** | der Fünftagesrhythmus trägt die Betriebskosten nicht (§5) |
| **A1d** | Begründung je Signal | **„Rang 2 von 40"** | ersetzt „Cooldown abgelaufen" |
| **A1e** | ⚠️ Der absolute Trendfilter am Einzelwert | **NICHT bauen** | gemessen: sperrt 12 % der Termine und verbessert nichts |

⚠️ **A1b als Schatten ist kein Zögern, sondern die Konsequenz aus der
Jahresprobe.** Genau so ist H seit dem 22.08. gebaut, und genau deshalb steht
heute eine Zahl dazu da.
