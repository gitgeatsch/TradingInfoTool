# Konstruktionsfrage: die drei Zeitskalen (06.08.2026)

**Auslöser:** Nutzer-Beobachtung — „BTC ist drei Tage leicht gestiegen, aber
keine Änderung in den Signalen." Nachgemessen: **+1,78 %** über drei Tage
(63.462 → 64.593), Signale am 06.08. weiterhin 19 SHORT gegen 3 LONG.

**Nutzer-Klarstellung, die den Rahmen setzt:** die 0–5 Tage waren **kein
Wunsch, sondern ein Kompromiss**, damit überhaupt gemessen und Parameter
festgelegt werden können. Gesucht ist ein stabileres Konzept — **ohne dass
etwas bricht.**

---

## 1. Das System verhält sich korrekt — und genau das ist das Problem

```
regime:           baer
btc_trend_label:  abwärts (EMA20 < EMA50 < EMA200)
regime_reason:    BTC unter EMA50 und/oder Fear&Greed im Angst-Bereich
```

Ein Anstieg von 1,78 % in drei Tagen dreht diesen EMA-Stapel nicht — dafür
bräuchte es Wochen. **Kein Bug.** Aber es legt offen, dass drei verschiedene
Zeitskalen im System vermischt sind:

| | Skala | Wirkt über | Wird gesetzt durch |
|---|---|---|---|
| **A** | **Regime** | Wochen bis Monate | EMA20 / EMA50 / **EMA200** |
| **B** | **Handelshorizont** | 0–5 Tage | Vorgabe (Messkompromiss) |
| **C** | **Messhorizont** | 7 und 14 Tage | Auswertungsparameter |

**Skala A gatet Entscheidungen auf Skala B.** Über die Lebensdauer eines
einzelnen Trades ist das Regime praktisch konstant.

### Warum das mehr ist als eine Schönheitsfrage

Das Regime-Label steuert vier harte Mechanismen:

- **R-5.10** Mindestkonfidenz (krise_extrem 85 / bär 75 / seitwärts 65 / bulle 60)
- Positionsgrößen-Skalierung
- Hebel-Deckel
- **AZ-7** (krise_extrem → Hebel komplett aus)

Ist das Regime über die Trade-Dauer konstant, **filtern diese Mechanismen nicht
zwischen Trades — sie verschieben nur das Gesamtniveau.** Ein Filter, der
innerhalb seines Wirkungszeitraums nie umschaltet, ist kein Filter, sondern eine
Konstante mit Verfallsdatum.

> Das ist dieselbe Fehlerfamilie wie die **Zeithorizont-Fehlpassung**, die in
> `Fakten_Entscheidungsmappe.md` 3.1 als „wichtigste Erkenntnis dieser Runde"
> steht — dort für Makro-Fakten (6–12-Monats-Forward-Werte im Hebel-Prompt mit
> ~1 Tag Haltedauer). Die Nutzer-Beobachtung zeigt dieselbe Fehlpassung **am
> Regime-Label selbst**, und das wiegt schwerer, weil daran Gates hängen.

---

## 2. Vier Vorschläge — keiner bricht etwas

Bewusst in dieser Reihenfolge: erst benennen, dann messen, dann entscheiden.
**Kein Vorschlag ändert einen laufenden Gate-Parameter.**

### V1 — Die drei Zeitskalen explizit trennen und benennen

**Was:** A, B und C bekommen Namen und je einen dokumentierten Zweck.
Handelshorizont und Messhorizont sind heute dieselbe Zahl, obwohl sie
verschiedene Fragen beantworten.

**Warum zuerst:** ohne diese Trennung ist jede Parameterdiskussion unentscheidbar
— „5 Tage" heißt heute je nach Kontext „so lange halte ich", „so weit schaue ich
zurück" oder „so lange messe ich nach".

**Risiko:** null. Reine Dokumentation.

### V2 — Messen, ob das Regime überhaupt trennt (der billigste echte Erkenntnisgewinn)

**Was:** Trefferquote und Erwartungswert je Regime-Label, gegen eine Basislinie
je Regime. Die Frage: **unterscheiden sich Signale im Bärenregime messbar von
denen im Seitwärtsregime?**

**Warum das der erste Schritt sein muss:** wir haben nie geprüft, ob das Label
diskriminiert. Falls nein, sind alle vier daran hängenden Mechanismen
Niveauverschiebungen — und dann ist die Frage nicht „welche Zeitskala", sondern
„wozu überhaupt".

**Datenlage:** vorhanden. `regime` steht an jedem Signal, Outcomes ebenso.
Methodik wie gehabt — Basislinie je Bucket, Block-Bootstrap über Symbole.

**Risiko:** null. Reine Auswertung.

### V3 — Den Handelshorizont aus den Daten ableiten statt ihn zu setzen

**Was:** messen, **wann** die Bewegung tatsächlich stattfindet — an welchem Tag
nach Signalstellung der maximale Buchgewinn (MFE) typischerweise erreicht wird.

**Warum:** die 0–5 Tage sind gesetzt, nicht gemessen. Bekannt ist bereits:
Auflösung Median 2,6 Tage, gehandelte Praxis 0,3 Tage, Stop trägt rechnerisch
3,3 Tage — **drei Werte, die nicht zusammenpassen**. Der MFE-Zeitpunkt ist die
fehlende vierte Zahl und die einzige, die sagt, wann die Kante real wird.

**Datenlage:** `outcome_max_realisiertes_crv` existiert; der zugehörige
Zeitpunkt muss aus der Simulation kommen (`simuliere_signal` liefert `tag`
bereits).

**Risiko:** null bis zur Entscheidung. Danach wäre eine Horizont-Änderung ein
bewusster Schritt mit Messgrundlage statt einer Setzung.

### V2 — GEMESSEN am 06.08.: das Regime hat sich NIE geändert

Die Frage war „trennt das Regime überhaupt?". Sie ist **nicht beantwortbar —
und genau das ist die Antwort.**

**Ausnahmslos jedes Signal in der gesamten Datenbank trägt `regime = "baer"`:**
1.391 Hebel-Signale, 2.223 Spot-Signale. Kein einziges anderes Label, über die
ganze Historie.

Die Eingangsgrößen erklären, warum — sie haben sich bewegt, aber nie genug:

| Größe | Beobachtet (31 Tage) |
|---|---|
| `btc_trend_label` | **21 von 21** „abwärts (EMA20 < EMA50 < EMA200)" |
| `fear_greed_label` | Fear (20) / Extreme Fear (11) — **nie darüber** |
| `regime_reason` | **21 von 21** „BTC unter EMA50 und/oder Fear&Greed im Angst-Bereich" |
| `fear_greed_value` | 20 bis 33 (Spanne 13) |
| VIX | 15,81 bis 20,66 |

**Eine Variable mit genau einem Wert kann nicht diskriminieren.** Die
regime-abhängigen Mechanismen haben über die gesamte Projektlaufzeit **jeweils
nur einen einzigen Zweig ausgeführt**.

#### Was das bedeutet — und es ist mehr als eine Formalie

**1. Die Regime-Gates sind keine Filter, sondern Konstanten.** Alles, was wir je
über dieses System gemessen haben, wurde unter genau einer Regime-Einstellung
gemessen. Das ist kein Codefehler — es ist eine Grenze dessen, was wir behaupten
dürfen.

**2. Die eigentliche Gefahr sind die nie ausgeführten Zweige.** Ein
Regimewechsel schaltet gleichzeitig drei Dinge um, die noch nie mit echten Daten
gelaufen sind:

| | bär (immer aktiv) | seitwärts | bulle |
|---|---|---|---|
| `min_konfidenz_prozent` | **75** | **65** | **60** |
| `small_cap_budget_prozent` | 4 | 8 | 12 |
| vier Gewichts-Fakten | eine Belegung | andere | andere |

**Der Konfidenz-Sprung ist der kritische.** Nach der Messung vom 05.08. liegt
die Masse der Konfidenzverteilung seit dem Mistral-Drift **exakt auf 70**. Die
Schwelle 75 filtert dort 5 % durch; eine Schwelle von 65 ließe **61 %** durch.

> **Ein Regimewechsel nach „seitwärts" würde das Gate schlagartig um den Faktor
> zwölf öffnen — über einen Codepfad, der noch nie mit echten Daten gelaufen
> ist.** Das ist die größte Stabilitätsgefahr im System, und sie hat nichts mit
> Zeitskalen zu tun.

**3. Die Gewichts-Fakten haben keine Regel.** `gewicht_technik`,
`gewicht_fundamental`, `gewicht_momentum`, `gewicht_kontext_makro` gehen an das
Modell, ohne dass eine Prompt-Regel erklärt, was sie bedeuten (Katalog 4.2:
„keine Regel, kein Gate"). Bei einem Regimewechsel ändern sich also stillschweigend
vier Zahlen im Faktensatz, deren Wirkung nie gemessen wurde.

#### Vorschlag V2b — den Regimewechsel trockenlaufen lassen, bevor er echt passiert

**Was:** die historischen Faktensätze erneut durch die Kette schicken, einmal mit
erzwungenem `seitwaerts`, einmal mit `bulle` — und messen, was die Gates tun.
Wie viele Signale kämen durch, wie ändern sich Positionsgrößen und Hebel-Deckel?

**Warum das jetzt geht:** die Werkzeuge existieren vollständig — echte
Faktensätze im Export, `backtest_llm1_historisch.py` als Basis, das
Dreiarm-Verfahren für die Prompt-Seite.

**Risiko:** null. Reine Simulation, kein Produktionspfad wird berührt.

**Warum es dringend ist:** dieser Zweig wird irgendwann von selbst aktiv — und
zwar ohne Vorwarnung, an einem beliebigen Morgen um 06:00. Ihn dann zum ersten
Mal live zu erleben, ist das Gegenteil von „stabil und sauber".

### V3 — GEMESSEN am 06.08.: das Ergebnis kippt die Frage

`messe_planungshorizont.py`, 300–488 Hebel-Signale je Variante, Anteil des am
Horizont-Ende erreichten MFE, der bereits an Tag N stand.

| Variante | n | Median-Tag für 99 % | **Bestwert erst NACH Tag 5** |
|---|---|---|---|
| H7, mit Barrieren | 487 | 1,0 | 14,4 % |
| H7, ohne Barrieren | 488 | 3,0 | 26,4 % |
| H14, mit Barrieren | 300 | 2,0 | 26,3 % |
| **H14, ohne Barrieren** | 300 | 5,0 | **45,0 %** |
| H14, nur LONG | 269 | 2,0 | 25,7 % |
| H14, nur SHORT | 31 | 4,0 | 32,3 % |

**Im Median ist bei Tag 5 alles da** — in jeder Variante 100 %. Der typische
Trade ist nach **1–2 Tagen** entschieden. Für den Medianfall sind 5 Tage also
nicht knapp, sondern großzügig.

**Aber der Median verdeckt den Schwanz.** Bei **26 %** der Signale kommt der
Bestwert erst nach Tag 5 — und ohne Barrieren, also wenn kein Stop dazwischen
geht, bei **45 %**.

**Die Lücke zwischen 26,3 % und 45,0 % ist die eigentliche Aussage.** Sie sagt:
bei fast einem Fünftel der Signale beendet eine Barriere den Trade, *bevor* die
Bewegung fertig ist. Das ist derselbe Befund wie beim Ausstieg (50 % standen
einmal bei +1R, nur 17,6 % kamen an) — hier von der Zeitachse her gesehen.

> **DARAUS FOLGT NICHT „HORIZONT VERLÄNGERN".** Ein fester Horizont ist für
> diese Verteilung das falsche Instrument: er müsste für den Median viel zu
> lang sein, um dem Viertel gerecht zu werden. Was man braucht, ist ein
> Mechanismus, der **nicht im Voraus wissen muss, wie lange es dauert** — und
> der ist seit dem 05.08. live: die **Ausstiegsregel** (Trailing ab +1R). Sie
> lässt laufen, was läuft, und sichert, was erreicht wurde.

**Die Konsequenz für den Prompt ist damit kleiner als gedacht:** die 5 Tage sind
als *Planungsrahmen* vertretbar. Irreführend ist nur, sie als *harte Grenze*
darzustellen, wo ein Viertel der Fälle darüber hinausläuft — und der
Trailing-Stop diesen Fällen ohnehin gerecht wird.

**Vorbehalte, die dazugehören:**

- **Über 14 Tage hinaus ist nichts messbar.** Volle 21-Tage-Vorläufe gibt es
  für 38 Signale, 30-Tage-Vorläufe für null. Ob die Bewegung darüber
  weiterläuft, bleibt offen.
- **Tag 0 trägt schon 60–80 % des End-MFE.** Das ist teils die Tagesspanne des
  Signaltags selbst — der Einstieg liegt nahe am Kurs, und das Tageshoch zählt
  bereits. Kein Fehler, aber es überzeichnet, wie schnell „die Kante da ist".
- **SHORT nur n=31.** Die Richtungs-Aufteilung ist ein Hinweis, keine Aussage.

### V4 — Ein kurzfristiges Regime als SCHATTEN-Fakt

**Was:** ein zweites Regime-Maß auf Skala B (z. B. 3–5-Tage-Trend oder EMA5/EMA20)
wird berechnet, gespeichert und ausgewertet — **aber an kein Gate angeschlossen**.

**Warum dieser Weg:** genau so wurden Veto-Schatten-Tracking und
selbst-gewähltes-HALTEN-Tracking eingeführt. Erst messen, was ein Mechanismus
getan hätte, dann entscheiden. Das ist die einzige Methode in diesem Projekt,
die bisher zuverlässig funktioniert hat.

**Risiko:** null, solange nichts verdrahtet wird. Danach nur nach Nachweis.

---

## 2b. Die SHORT-Absicherungen (Nasdaq / S&P 500) — eigene Kategorie, eigener Maßstab

**Nutzer-Hinweis 06.08.: „die Short-Absicherungspositionen sind ebenfalls anders
zu behandeln — also Nasdaq und S&P 500."** Richtig, und die Prüfung fördert
einen blockierenden Fund zutage.

### Was es ist

| Symbol | Instrument | Referenz | Hebel |
|---|---|---|---|
| **DBPK** | inverse ETP | S&P 500 | 2× short |
| **3QSS** | inverse ETP | Nasdaq-100 | 3× short |

Zweck laut Config: **Kompromiss-Hedge**, weil Bitpanda keine echten
Krypto-Short-Positionen anbietet. Gesteuert über `hedge.max_abdeckung_anteil`
(Obergrenze, kein Zielwert) und eine Bull-Wahrscheinlichkeits-Schwelle.

### DER BLOCKIERENDE FUND

**Beide Positionen sind gehalten — 3QSS mit 218,25 Einheiten, DBPK mit 1.739,16
— und beide haben NULL Kurspunkte und keinen Einstandspreis.**

Daraus folgt eine Kette:

1. Sie stehen im Mengenkorb der Portfolio-Wertreihe (beide, in allen Ständen).
2. Sie haben keinen Kurs → sie zählen als „Symbol ohne Kurs" und fallen aus der
   Bewertung.
3. **Z-3 misst damit den Portfolio-Rückschlag OHNE die Absicherung, die ihn
   dämpfen soll.**

Das ist ein logischer Kurzschluss: die Notbremse für Drawdown ist blind für das
einzige Instrument, das gegen Drawdown gekauft wurde. Am letzten Stand fehlen
**19 von 33 Symbolen** mangels Kurs — die beiden Hedges darunter.

Zusätzlich: **32 Hedge-Signale, null mit Ergebnis.** Ohne Kursreihe ist weder
technische Analyse noch Erfolgsmessung möglich.

### Warum der Maßstab ohnehin ein anderer sein muss

Selbst mit Kursdaten wäre die übliche Messung falsch — aus demselben Grund wie
bei AZ-4:

- **Eine Absicherung soll nicht gewinnen, sie soll dämpfen.** Nach Trefferquote
  oder R-Multiple bewertet, sieht jede funktionierende Versicherung schlecht
  aus: in ruhigen Phasen kostet sie, und genau dann ist sie richtig.
- **Gehebelte inverse ETPs haben Volatilitäts-Drag.** Ein 3×-Short verliert in
  Seitwärtsphasen strukturell, unabhängig von der Richtung — die Config benennt
  das selbst („die Position decayt täglich ohne Absicherungsnutzen"). Das ist
  dieselbe Kostenfamilie wie Funding beim Hebel, nur schwerer sichtbar.

**Der richtige Maßstab ist ein Portfolio-Maß, kein Positions-Maß:**

> Sinkt der maximale Portfolio-Rückschlag mit der Absicherung gegenüber
> demselben Portfolio ohne sie — und was hat diese Dämpfung gekostet?

Das ist rechenbar, sobald Kurse vorliegen: die Portfolio-Wertreihe existiert
seit dem 04.08. (90 Tage, mengenkonstanter Index). Es wäre dieselbe Rechnung
zweimal — einmal mit, einmal ohne die Hedge-Mengen.

### Vorschlag V5 — in dieser Reihenfolge

1. **Kursdaten für 3QSS und DBPK beschaffen.** Ohne sie ist alles Weitere
   unmöglich, und Z-3 bleibt strukturell falsch. Das ist der dringlichste
   ASAP-Fix des ganzen Projekts — er blockiert eine bereits ausgelöste
   Notbremse.
2. **Hedge aus der normalen Erfolgsmessung herausnehmen** und als eigene
   Kategorie führen. Solange sie mitläuft, verzerrt sie die ETF-Zahlen und wird
   selbst falsch bewertet.
3. **Portfolio-Rückschlag mit und ohne Hedge** rechnen — die eigentliche Frage.
4. **Decay separat ausweisen.** Bei 2× und 3× inversen Produkten gehört die
   Haltedauer-Kostenrechnung dazu, analog zum Hebel-Kostenmodell.

**Risiko:** Punkt 1 ist reine Datenbeschaffung. Punkt 2 ändert nur die
Zuordnung in Auswertungen, keinen Handelspfad. Punkte 3 und 4 sind Messungen.
**Kein Vorschlag greift in eine laufende Regel ein.**

---

## 3. Was zur Stabilität gehört, aber keine Zeitskalen-Frage ist

Der Wunsch war „stabil und sauber". Der einzige Vorfall, der das System bisher
wirklich gebrochen hat, war **kein Parameter**, sondern ein
**Anbieter-Verhaltenswechsel**: Mistral hat am 31.07. sein Verhalten geändert
(Replay-Nachweis: 55,4 % → 68,0 % Konfidenz bei bitgleichem Prompt). Das hat
Tage gekostet, bis es gefunden war.

**Der Kanarienvogel dafür ist gebaut und getestet, aber nicht aktiviert** —
Aktivieren wäre eine Zeile. Die damalige Begründung (kein zweiter Vorfall) steht
noch; sie sollte aber gegen den Aufwand einer erneuten Suche abgewogen werden.

---

## 4. Empfohlene Reihenfolge

0. **V5 Punkt 1 VOR allem anderen** — Kursdaten für 3QSS und DBPK. Es ist der
   einzige Punkt, der eine **bereits ausgelöste** Notbremse untergräbt: Z-3
   meldet 16,84 % Rückschlag auf einem Portfolio, aus dem die Absicherung
   herausfällt.
1. ~~**V3**~~ — **am 06.08. gemessen, siehe oben.** Ergebnis: die 5 Tage sind
   für den Median großzügig, aber ein Viertel läuft darüber hinaus. Ein fester
   Horizont ist das falsche Instrument; die Ausstiegsregel ist das richtige und
   ist bereits live. **Keine Horizont-Änderung empfohlen.**
2. ~~**V2**~~ — **am 06.08. gemessen.** Das Regime war IMMER „baer", über alle
   3.614 Signale. Nicht messbar, weil konstant — und damit ist die
   Zeitskalen-Frage **nicht die dringendste**. Die dringendste ist der nie
   ausgeführte Regimewechsel-Zweig.
3. **V2b NEU und vorgezogen** — den Regimewechsel trockenlaufen lassen. Ein
   Wechsel nach „seitwärts" öffnet das Konfidenz-Gate von 5 % auf 61 %, über
   einen Codepfad der nie mit echten Daten lief. Reine Simulation, kein Risiko.
4. **V1** — Benennung nachziehen.
5. **V4** (kurzfristiges Regime als Schatten-Fakt) — erst sinnvoll, wenn es
   überhaupt Regime-Variation gibt, an der man es messen könnte.

## 5. Was die beiden Messungen zusammen ergeben

V3 sagt: **der Handelshorizont ist nicht das Problem** — der Median-Trade ist
nach 1–2 Tagen entschieden, und für den Schwanz ist die bereits laufende
Ausstiegsregel das richtige Instrument.

V2 sagt: **das Regime ist nicht einmal eine Variable** — es war immer derselbe
Wert, und die daran hängenden Gates haben nie einen zweiten Zweig ausgeführt.

**Die Zeitskalen-Fehlpassung, mit der dieses Dokument begann, ist damit real,
aber nachrangig.** Ein langsames Regime, das ein schnelles Geschäft gatet, ist
konstruktiv unschön — aber es hat bisher schlicht nichts getan. Das echte Risiko
liegt nicht darin, dass das Regime zu langsam reagiert, sondern darin, **was
passiert, wenn es zum ersten Mal reagiert.**

**Ausdrücklich NICHT empfohlen:** jetzt am EMA-Fenster, an R-5.10 oder am
Handelshorizont zu drehen. Alle drei sind gekoppelt, und wir haben für keinen
davon einen Wirkungsnachweis. Eine Änderung ohne Messung wäre genau der Fehler,
den das Projekt in den letzten Tagen mehrfach vermieden hat.
