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
1. **V2** — trennt das Regime überhaupt? Das entscheidet, ob die
   Zeitskalen-Frage die richtige Frage ist. Kostet eine Auswertung.
2. **V3 parallel** — wann wird die Kante real? Liefert den empirischen
   Handelshorizont.
3. **V1** — Benennung nachziehen, sobald die beiden Zahlen vorliegen.
4. **V4** nur, falls V2 zeigt, dass das langsame Regime nicht trennt.

**Ausdrücklich NICHT empfohlen:** jetzt am EMA-Fenster, an R-5.10 oder am
Handelshorizont zu drehen. Alle drei sind gekoppelt, und wir haben für keinen
davon einen Wirkungsnachweis. Eine Änderung ohne Messung wäre genau der Fehler,
den das Projekt in den letzten Tagen mehrfach vermieden hat.
