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


---

## 11. Der Simulationslauf über die Historie — und die Antwort auf „Vorfilter, Auslöser oder Info?"

*Nutzerfrage: „Wie soll die Auswahl in der Praxis konkret angewendet werden und
den erwarteten Nutzen bringen? 1. als Vorfilter 2. als Begründung für den
Handel, also Auslöser 3. nur Info?" — und dazu: „wie oft gibt es Signale, sind
diese meist gute Trades, je nach Spot oder Hebel, nach Assets, in
unterschiedlichen Marktlagen."*

`messe_auswahl_historie.py`, 40 Symbole, 2017-08-17 bis 2026-08-19, Auswahl
alle 20 Handelstage, `k = 2`. Maß ist die Bewegung über den Takt —
**barrierenfrei und brutto**, Kosten daneben.

### 11.1 Wie oft

> **184 Empfehlungen über sechs Jahre = 30,7 je Jahr**, also rund alle zwölf
> Tage eine. Heute könnten es 41 **je Umlauf** sein.

### 11.2 ⚠️ Sind es meist gute Trades? — Nein.

| | Signale | Mittel | **Median** | Markt | >0 Ref | **>0 Betrieb** |
|---|---:|---:|---:|---:|---:|---:|
| **alle Empfehlungen** | 184 | +5,01 % | **−0,63 %** | +1,95 % | 48 % | **44 %** |
| davon **Rang 1** | 92 | **+7,03 %** | **+2,83 %** | +1,95 % | 53 % | **48 %** |
| davon Rang 2 | 92 | +3,00 % | −2,01 % | +1,95 % | 43 % | 40 % |

> ⚠️ **Der Mittelwert ist positiv, der Median negativ.** Die Auswahl lebt von
> wenigen großen Gewinnern — **die Mehrzahl der Empfehlungen verliert.** Nach
> Betriebskosten sind **44 %** positiv.

**Und ein neuer Befund, der k betrifft:** Rang 1 ist deutlich besser als
Rang 2 — in Mittel, Median und Trefferquote. ⚠️ **Nach diesem Maß wäre `k = 1`
besser als `k = 2`**, obwohl der t-Wert das Gegenteil nahelegte. Der
Unterschied ist echt und erklärbar: der t-Wert misst den *Abstand zum Markt*
bei geringerer Streuung, dieses Maß den **Trade selbst**.

### 11.3 Je Assetstufe

| Stufe | Signale | Mittel | Median | >0 Betrieb |
|---|---:|---:|---:|---:|
| **klein** (< 1 Mrd) | 50 | **+9,87 %** | +4,08 % | **54 %** |
| **gross** (≥ 10 Mrd) | 61 | +7,33 % | +2,50 % | 48 % |
| btc | 9 | +6,08 % | +1,43 % | 44 % |
| mittel (1–10 Mrd) | 56 | −0,05 % | −6,63 % | 34 % |
| **eth** | 8 | ⚠️ **−8,74 %** | −9,71 % | **25 %** |

⚠️ **`klein` ist genau die Stufe, die die Überlebensverzerrung am härtesten
trifft** — die gestorbenen Kleinen fehlen. Die +9,87 % sind eine **Obergrenze**.
**ETH** wurde nur achtmal gewählt und war fast immer falsch.

### 11.4 Je Marktlage

| | Signale | Mittel | >0 Betrieb |
|---|---:|---:|---:|
| BTC über dem 200-Schnitt | 98 | **+7,73 %** | 45 % |
| BTC unter dem 200-Schnitt | 86 | +1,92 % | 43 % |

> ⚠️ **Der Marktzustand hebt den Mittelwert, nicht die Trefferquote.** Er macht
> die Gewinner größer, nicht die Verlierer seltener. Das stützt A1b als
> **Schatten** und spricht gegen eine harte Schranke.

### 11.5 Je Jahr — drei gute, drei schlechte

| 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---:|---:|---:|---:|---:|---:|
| **+18,82 %** | −4,35 % | **+14,04 %** | **+9,53 %** | −1,21 % | −4,17 % |
| 67 % | 39 % | 56 % | 63 % | 33 % | 35 % |

⚠️ **Die beiden jüngsten Jahre sind negativ.**

### 11.6 ⚠️ Hebel — eine Umrechnung, keine Messung

| | Mittel | positiv | schlechtester Fall |
|---|---:|---:|---:|
| 2x | +3,43 % | 44 % | ⚠️ **−121 %** |
| 3x | +4,84 % | 44 % | ⚠️ **−182 %** |

Der Hebel ändert die **Trefferquote nicht** — er multipliziert beide Seiten.
Rechnerisch übersteigt der schlechteste Fall den Einsatz; in der Praxis wird
vorher liquidiert. **Das ist das Argument gegen Hebel auf dieser Auswahl:** bei
44 % Trefferquote und einem Schwanz dieser Größe ist die Ruinwahrscheinlichkeit
das bindende Problem, nicht der Erwartungswert.

---

## 12. Die Antwort auf die drei Möglichkeiten

| | | Urteil |
|---|---|---|
| **1. Vorfilter** | bestimmt, **welche Werte überhaupt beurteilt werden** | ✔ **Ja — so ist es gebaut, und das ist die richtige Rolle** |
| **2. Auslöser** | die Auswahl **ist** die Kaufentscheidung | ⚠️ **Nein.** 44 % Trefferquote, Median −0,63 % — das ist keine Entscheidung, das ist eine Vorauswahl |
| **3. Nur Info** | eine Zahl in der Mail | ⚠️ **Zu wenig.** Genau das war der Zustand: der Rangplatz stand seit dem 20.08. in der Mail und hat nie etwas verändert |

**Der erwartete Nutzen, ehrlich benannt — er liegt nicht in der Rendite:**

| | |
|---|---|
| **Die Flut endet** | 41 Beurteilungen je Umlauf werden 2 |
| **Jede Entscheidung hat einen Grund** | „Rang 2 von 41" statt „Cooldown abgelaufen" |
| **Die Grundmenge ist besser als der Markt** | +5,01 % gegen +1,95 % über 20 Tage |
| ⚠️ **Was sie NICHT leistet** | sie macht aus 44 % keine 60 %. **Das ist die Aufgabe der Kette danach** — und ob die Kette das schafft, ist bisher unbelegt |

> **Daraus folgt der nächste Messschritt, und er ist billig:** je Umlauf
> mitschreiben, was die mechanische Auswahl empfohlen hätte und was die Kette
> daraus gemacht hat. **Erst dieser Vergleich sagt, ob die LLM-Ebene ihren
> Platz verdient** — gegen eine Basislinie, die es vorher nicht gab.


---

# RECHERCHE 31.08.2026 — warum A1 im Betrieb nicht bremst

**Nutzerauftrag:** *„Kläre zuerst, warum A1 nicht greift. Vorher recherchieren,
ob es einen Grund gibt und u. U. kein Fehler vorliegt — der Grund für den
Lauftakt sollte dokumentiert sein und wie es funktionieren soll."*

**Beobachtung, die den Auftrag ausgelöst hat:** `K_GROSS = 2`, aber in der
Notebook-Produktion bekommen **28–32 von 43 Assets täglich** ein Signal,
4,2–5,6 Signale je Asset und Tag.

Drei Ursachen, geprüft. **Zwei davon sind kein Fehler.**

---

## 1. Der Lauftakt — begründet, dokumentiert, KEIN Fehler

    HEBEL_SCREENING_INTERVAL_MINUTES = 15   ->  96 Läufe pro Tag
    A1 wählt k=2 je Lauf                    ->  192 gewählte Assets pro Tag

**Der Grund steht in `docs/budget_queue_design.md`** (14.07.2026, Phase 5):

> *„Ohne gemeinsame Logik entsteht ein Burst-Problem: mehrere gleichzeitig
> getriggerte Kandidaten können an einem Tag locker [das Tagesbudget
> verbrauchen]."*

Der 15-Minuten-Takt ist die **Granularität einer Budgetverteilung** — er
verteilt ein knappes LLM-Kontingent gleichmäßig über den Tag. Er war nie als
Signalfrequenz gedacht. Drei Verbraucher teilten sich dasselbe Budget:
Spot-Rotation, Marktscan-Kaufkandidaten, Hebel-Empfehlungen.

**Beim Schnitt am 14.08.** (`background.py:3373`) trat `fuehre_umlauf` an die
Stelle des Budget-Allocators — im selben Takt. ✔ **Die Budgetbremse kam mit:**

    KETTE = gemini 500 + gemini 500 + openrouter 1000 + groq 83 = 2.083/Tag
    RESERVE_ANTEIL = 0,1                              -> ~1.875 nutzbar

⚠️ **Aber sie bremst bei 174 Signalen/Tag nicht** — sie ist zehnmal so groß.
Und sie ist eine **technische** Grenze (LLM-Kontingent), keine fachliche.

### Die Lücke, die daraus folgt

> **Es gibt im ganzen System keine Stelle, die sagt: „so viele Empfehlungen
> sind fachlich sinnvoll."**

Der Takt folgt dem Kontingent, nicht dem Bedarf. Nutzervorgabe 31.08.:
*„Der Takt darf nur mit dem Bedarf nach der Frequenz folgen."* Diese Vorgabe
ist nirgends umgesetzt — nicht weil sie verletzt wurde, sondern weil die
Größe „Bedarf" nie definiert wurde.

**Das ist die eigentliche offene Entscheidung**, und sie ist keine Messfrage.

---

## 2. Die Bestandsausnahme — Absicht und Umsetzung weichen ab

`rollen_lauf.py:1115`:

```python
if (auswahl or {}).get("aktiv") and not _hat_bestand:
    if symbol not in auswahl["gewaehlt"]:
        durchlauf.verloren(symbol, "auswahl", ...)
        return
```

**Wer Bestand hat, wird von A1 nicht gefiltert.** Die Begründung im Code ist
richtig und gemessen:

> *„Die Auswahl beantwortet die Frage ‚welchen soll ich KAUFEN'. Bei einem
> gehaltenen Wert lautet die Frage aber ‚halten oder verkaufen' — und die
> stellt sich unabhängig davon, ob er heute unter den besten zwei ist. Ohne
> diese Ausnahme fällt die gesamte Verkaufsseite aus der Kette."*
>
> Gemessen: von 24 Bestandspositionen wären **21 nicht mehr beurteilt worden**.

Und dieselbe Absicht steht in diesem Dokument, Abschnitt oben:

> **Bestand** — **nicht Teil von A1**: ein gehaltener Wert, der im Rang fällt,
> ist die **Verkaufsfrage**.

### ⚠️ Die Umsetzung ist breiter als die Absicht

Die Ausnahme lässt das Asset **für JEDE Aktion** durch, nicht nur für die
Verkaufsseite. Gemessen an 1.854 einstiegsfähigen Signalen der
NB-Produktion:

| Aktion | mit Bestand (A1 umgangen) | ohne Bestand | Anteil umgangen |
|---|---:|---:|---:|
| NACHKAUFEN | **595** | 232 | **72 %** |
| ERÖFFNEN | 332 | 549 | 38 % |
| KAUFEN | 7 | 139 | 5 % |
| **gesamt** | **934** | 920 | **50 %** |

**Die Hälfte aller Einstiegssignale umgeht die Auswahl über den Bestand.**
Ein Nachkauf ist aber keine Verkaufsfrage — er kostet Geld und braucht eine
Begründung wie jeder andere Einstieg.

⚠️ **Das ist ein echter Befund, aber es ist eine ENTSCHEIDUNG, kein Bug.**
Zwei vertretbare Lesarten:

| | Lesart | Argument |
|---|---|---|
| **A** | Bestand umgeht A1 nur für **Ausstiegsaktionen** | ein Nachkauf ist ein Einstieg; A1 wurde genau dafür gebaut |
| **B** | Bestand umgeht A1 wie heute, für alles | wer investiert ist, kennt den Wert; die Positionsfrage steht über der Auswahlfrage |

Für A spricht der Wortlaut der eigenen Festlegung (*„das ist die
Verkaufsfrage"*), für B die Sorge, eine bestehende Position nicht mehr
aufstocken zu können, wenn sie im 250-Tage-Rang zurückfällt.

---

## 3. Der Umlaut in `auswahl.EINSTIEGSAKTIONEN` — unkritisch, aber real

    agent/auswahl.py:388      EINSTIEGSAKTIONEN     = (..., "EROEFFNEN")   ohne Umlaut
    agent/signal_mail.py:91   AKTIONEN_MIT_EINSTIEG = (..., "ERÖFFNEN")    mit Umlaut

Die Produktion schreibt **`ERÖFFNEN`** (881 Signale). `auswahl.py:414` prüft
`aktion in EINSTIEGSAKTIONEN` — das trifft nie zu.

**Wirkung, geprüft:** Die Stelle sitzt in `stumme_laeufe()`, und die ist
**ausdrücklich eine Meldung, kein Abbruch** (`rollen_lauf.py:736`: *„als
MELDUNG statt Abbruch — ein laufübergreifender Abbruch wäre eine Falle"*).

    ✔ kein Abbruch, kein verändertes Signal
    ⚠️ aber eine FALSCHE Warnung: der Zähler meldet „8 Läufe ohne Einstieg
       bei einem gewählten Wert", während 881 Eröffnungen entstanden sind

⚠️ **Und die Prüfung, die genau das fangen soll, deckt `auswahl.py` nicht ab.**
`pruefe_pakete.py:2803` (*„das Vokabular wird importiert, nicht
abgeschrieben"*) prüft nur `signal_abbildung.py`.

---

## Zusammenfassung

| # | Befund | Urteil |
|---|---|---|
| **1** | 15-Min-Takt × k=2 = 192 gewählte Assets/Tag | ✔ **kein Fehler** — Budgetgranularität, dokumentiert. ⚠️ Aber die Bremse ist ein LLM-Kontingent (2.083/Tag), keine fachliche Frequenz |
| **2** | 50 % der Einstiege umgehen A1 über den Bestand | ⚠️ **Entscheidung offen** — die Absicht war die Verkaufsseite, die Umsetzung deckt alles ab |
| **3** | Umlaut in `EINSTIEGSAKTIONEN` | ⚠️ **echter Fehler, folgenlos** — falsche Warnung, kein verändertes Verhalten. Prüfungslücke |
