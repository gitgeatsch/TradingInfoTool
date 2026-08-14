# Umbauplan Gesamtsystem — von der Rollen-Ebene zur Empfehlung (12.08.2026)

*Der Masterplan für den Umbau. Er löst `Rollenkonzept_Entwurf_10_08.md` nicht
ab, sondern setzt darauf auf: das Rollenkonzept sagt, WER urteilt; dieser Plan
sagt, WAS jede Rolle bekommt, was sie liefert, und wie daraus eine Empfehlung
für den Nutzer wird.*

---

## 0. Der Auftrag, in den Worten des Nutzers

> **Wir bauen für alle Assets und für alle sinnvollen Handelsstrategien inkl.
> Hebel — je nachdem was benötigt wird.**
> 1. Das wird auf die Rollen aufgeteilt.
> 2. Je nach Asset oder Assetklasse sind die richtigen Informationen zu
>    übergeben.
> 3. Die LLMs werden auf ihren Zweck und ihre Funktion umgebaut.
> 4. **Für die E-Mail und den User soll am Ende klar sein, ob es ein guter
>    Einstieg ist oder nicht — „der Entscheider".** Nicht durch einen Text wie
>    „gute Marktlage für BTC-Einstieg", sondern de facto: auf Basis der im Text
>    übergebenen Fakten und der LLM-Bewertung — ist bzw. könnte dies ein guter
>    Trade sein.

Und der Rahmen dazu:

> *„Es soll ein glatter Schnitt werden."* — altes und falsches raus.
> *„Strategie war noch nie korrekt implementiert, soll aber mit dem neuen System
> funktionieren."*
> *„Immer an der Quelle prüfen, sonst haben wir ein Problem."*

---

## 1. Das Raster — vier Entscheidungen je Datum

**Nutzervorgabe 12.08., und sie ist das Rückgrat dieses Plans:**

> *„Du musst immer unterscheiden, wenn wir Daten weglassen, ob wir das
> spezifisch je Rolle, Asset oder Funktionalität machen oder generell streichen
> — sehe ich in meiner Empfehlung kein Take-Profit mehr, oder messen wir es nur
> nicht mehr, oder geben es nicht an die LLMs?"*

Jedes Datum hat deshalb **vier unabhängige Entscheidungen**:

| | Frage |
|---|---|
| **1 Eingabe** | Sieht das Modell es? |
| **2 Ausgabe** | Produziert das Modell es? |
| **3 Messung** | Wertet das Backward-Tracking es aus? |
| **4 Anzeige** | Sieht der Nutzer es in Mail und GUI? |

**Ein „nein" in Spalte 1 ist kein „nein" in Spalte 4.** Genau diese Vermengung
hat bisher zu Fehlschlüssen geführt — auch bei mir.

---

## 2. Die Felder-Matrix — verbindlich

| Feld | 1 Eingabe | 2 Ausgabe | 3 Messung | 4 Anzeige | Begründung |
|---|---|---|---|---|---|
| **Take-Profit** | — | **abgeleitet** | **ja** | **ja** | Geometrie muss fest bleiben, sonst ist keine Trefferquote vergleichbar (§6) |
| **Einstieg** | — | ja, **als Spanne** | ja | ja | heute ein Punkt, der Nutzer braucht „bei ca." |
| **Stop** | — | ja, als Spanne | ja | ja | |
| **Konfidenz** | nein | **nein** | als Trefferbilanz | **ja — als gemessene Quote** | 77,5 % vorhergesagt gegen 33,3 % eingetreten |
| **Regime-Etikett** | **nein** | nein | nein | nein | über 1.022 Fälle konstant „baer" |
| **Regime-Score** | **ja** | nein | ja | ja | variiert 0,250–0,750, trennt die Phasen |
| **Marktbreite** | nein | nein | nein | nein | Korb zu 25 % keine Coins, Bezug wandert, Richtung invers |
| **Richtung / Hebelfaktor** | Instrument ja | **ja** bei Hebel | ja | ja | ohne sie kein „Long 3x" |
| **Betrag** | nein | **nein** | ja | ja | abgeleitet aus unabhängigen Faktoren (R-A2) |
| **Haltekriterium / Ausstieg** | — | **ja, strukturiert** | ja | ja | heute Freitext `umgeworfen_durch`, nicht ausgewertet |
| **Thesen-Abgleich** (M2, COT, DXY, Zinskurve, EIA, Insider) | **ja** | nein | ja | ja | **gebaut, läuft, von der neuen Kette ungenutzt** (§5.3) |
| **Trefferquote / Filter** | **nein** | nein | **ja — er *ist* die Messung** | **ja** | Anker (Index 0,45) und Zirkularität; Nachfilter statt Vorfilter (§6.5) |

---

## 3. Assets × Strategien

**Sinnvoll heißt: die Assetklasse trägt sie, und wir können sie messen.**

| Strategie | krypto | aktien | etf | rohstoffe | was sie eigen macht |
|---|---|---|---|---|---|
| **Spot-Einstieg** (einmal) | ✓ | ✓ | ✓ | ✓ | Ziel + Stop, ein Zeitpunkt |
| **Spot-Swing** | ✓ | ✓ | ✓ | ✓ | Haltekriterium, Trailing-Stop, Horizont |
| **Akkumulation / DCA** | ✓ | ✓ | ✓ | ✓ | Umschalter **je Asset** (Watchlist-Tab) — der Nutzer entscheidet, wo. **Außer Absicherung.** Kein Stop, kein Zeitpunkt: anderes Erfolgsmaß. Siehe E1a |
| **Hebel LONG** | ✓ | — | — | ✓ | Finanzierung **je Tag**, Liquidationsabstand |
| **Hebel SHORT** | ✓ | — | — | ✓ | dito |
| **Hedge / Absicherung** | ✓ | ✓ | ✓ | ✓ | bezieht sich auf **das Portfolio**, nicht auf ein Asset |

**Die Strategie ist eine VORGABE an die Rolle, keine Frage an sie** — dieselbe
Linie wie beim Betrag. Der Aufrufer weiß immer, worum es geht: `krypto/pipeline`
und `krypto/hebel_pipeline` sind getrennt. Er übergibt es heute nur nicht —
`strategie`, `hebel`, `spot`, `instrument` kommen in der neuen Kette **null Mal**
vor.

**Warum das die Rollen betrifft:** die Strategie bestimmt, welche Fakten
überhaupt relevant sind. Bei Hebel sind Finanzierungsrate und
Liquidationsabstand tragend; bei DCA sind Stop und Einstiegszeitpunkt
**bedeutungslos**. Ein Prompt für alles wäre wieder der 34.611-Zeichen-Monolith.

---

## 4. Die Rollen — drei Rollen, zwei Abfragen

| Rolle | Aufrufe | kennt | liefert | Stand |
|---|---|---|---|---|
| **1 Lagebild** | 1 je Durchgang | kein Asset | Lage in Worten, Belege, **Urteil je Assetklasse**, `gleichlauf` (gerechnet) | Fakten fertig, Urteil fehlt |
| **2 Befund** | ⎫ 1 je Asset | Asset, Lagebild, **Instrument + Strategie** | Belege mit Richtung/Gewicht, Zahl unabhängiger Faktoren | Eingabe unvollständig |
| **3 Entscheidung** | ⎭ | + Bestand | Aktion, Richtung/Hebel, Einstieg, Stop, Haltekriterium, Begründung, Gegengrund, Falsifikator | Felder unvollständig |
| **Entscheider** | **0 — deterministisch** | alles oben + Trefferbilanz | **die Zahl und der Satz für die Mail** | fehlt |

**Der Entscheider ist keine vierte Rolle und kein LLM-Aufruf.** Er ist die
Darstellung von Rolle 2/3 plus die gemessene Trefferbilanz. Damit kostet er
nichts, kann nicht halluzinieren, und seine Güte ist per Konstruktion messbar.

### 4.1 Rolle 1 urteilt je Assetklasse — und warum das kein Rückfall ist

Am 12.08. wurde das Kategoriefeld `traegt` **entfernt**; jetzt kommt ein Urteil
je Klasse hinzu. Der Unterschied trägt:

- `traegt` fragte nach **Marktbreite** — und in den Fakten stand keine. Das
  Modell hätte erfinden müssen.
- „Ist diese Klasse gerade tragfähig?" fragt nach **genau den Fakten, die es
  hat**: Trend, Volatilität, Liquidität je Leitmarkt.

**Ein Urteil über Vorhandenes ist erlaubt; ein Urteil über Fehlendes ist
Erfindung.**

---

## 5. Fakten je Rolle, Klasse und Strategie

### 5.1 Was die Rollen heute bekommen

| Rolle | Quelle | Stand |
|---|---|---|
| Lagebild | `agent/marktlage.py` — 12 Aussagen, 3 Leitmärkte × Trend/Volatilität/Liquidität | fertig (L1–L6) |
| Befund/Entscheidung | `agent/lagebeschreibung.py` — Struktur, ATR, Kurs, Bestand, Finanzierung | Einzeldefekte behoben, nie systematisch |

### 5.2 Was je Strategie dazukommt

| Fakt | Spot | Swing | DCA | Hebel |
|---|---|---|---|---|
| Trend / Volatilität / Liquidität | ✓ | ✓ | ✓ | ✓ |
| Kurs, ATR, Struktur, Bestand | ✓ | ✓ | ✓ | ✓ |
| **Finanzierungsrate** | — | — | — | **tragend** (gebaut 11.08.) |
| **Liquidationsabstand** | — | — | — | **tragend, fehlt** |
| Haltekriterium / Horizont | — | ✓ | — | ✓ |
| Kostenquote in R | ✓ | ✓ | — | ✓ (höher) |

### 5.3 Der größte ungenutzte Bestand — der Thesen-Abgleich

`agent/kategorie_thesen.py::build_these_abgleich_fact()` läuft in **4 von 6
Pipelines** (aktien, hedge, rohstoff, themen_etf) und speist sich aus Quellen,
die **nichts mit der Kursreihe zu tun haben**:

```
M2 / Netto-Liquidität (FRED) · COT-Positionierung (CFTC) · Zinskurve ·
Dollar-Index · Bärenmarkt-Overlay · EIA-Erdgas ·
Bellwether: Analystentrend, Insider-Käufe, Short-Interest (Finnhub)
```

**Das ist der dritte unabhängige Faktor, den das Projekt seit Wochen sucht** —
und er ist gebaut, getestet und im Betrieb. Krypto nutzt ihn **nicht**, die neue
Rollen-Kette nutzt ihn **überhaupt nicht**.

Der Standard verlangt 3–4 **unabhängige** Faktoren; Indikatoren aus derselben
Kursreihe sind „illusion of confirmation". Dies ist die einzige bereits
vorhandene Faktenfamilie, die diese Bedingung erfüllt.

---

## 6. Der Entscheider

**Das Modell wird nie nach einer Zahl gefragt. Wir schauen nach, wie oft es
recht hatte.**

```
Das LLM urteilt.       -> Text + Aktion. Nie eine Prozentzahl.
Das System zählt mit.  -> "Wenn dieses System KAUFEN sagte bei 4 unabhängigen
                          Faktoren, traf es in X % der Fälle (n = Y)."
```

### 6.1 Die fünf Schritte

1. **Einstufung durch das LLM** — keine Prozentzahl, sondern prüfbare Merkmale:
   Zahl unabhängiger Faktoren, Belege mit Richtung und Gewicht, Falsifikator.
2. **Merkmale des Falls, deterministisch** — Volatilitäts-Perzentil, Lage in der
   Jahresspanne, Gleichlauf, Regime-Score, Kostenquote.
3. **Nachschlagen in der Trefferbilanz** — wie oft traf diese Kombination in
   unserer Historie? Mit Fallzahl und Konfidenzintervall, **Cluster-Bootstrap
   über Symbole**, nicht über Anker (überlappende Fenster).
4. **Gegen den Breakeven halten** — bei CRV 2:1 sind 33,3 % nötig, mit Kosten
   mehr.
5. **Der Satz für den Nutzer** — drei Zahlen und ein Urteil.

### 6.2 Wie es in der Mail aussieht

```
Grundwahrscheinlichkeit dieser Geometrie:        34 %
Diese Konstellation (3 unabh. Faktoren, ruhige
Volatilität, Kurs nahe Jahrestief) traf in
unserer Historie:                                41 %   (n = 312)
Für Kosten zu schlagen sind:                     38 %
--> Erwartungswert positiv, knapp.
```

**Und wenn nichts gemessen ist, sagt die Mail das auch:** *„Für diese
Konstellation liegen erst 14 Fälle vor — keine belastbare Abweichung von 34 %."*
Ein ehrliches „wir wissen es nicht" ist brauchbar; eine erfundene 77,5 % nicht.

### 6.3 Warum der Take-Profit abgeleitet wird

Die gesamte Erfolgsmessung läuft auf der Geometrie **3 ATR Ziel / 1,5 ATR
Stop**. Nennt das Modell den TP frei, weicht die Geometrie je Signal ab und die
Trefferquoten sind nicht mehr vergleichbar — **dann lässt sich die
Trefferbilanz aus 6.1/3 gar nicht bauen**.

```
Ziel = Einstieg + CRV × (Einstieg − Stop)
```

Das Modell entscheidet weiterhin **Richtung, Einstieg und Risikoabstand** — also
das Wesentliche. Dieselbe Linie wie beim Betrag: **das Modell urteilt, die Zahl
leitet sich ab.**

### 6.4 Die Kalibrierung: mit dem Mittelwert anfangen, je Signal nachziehen

**Nutzervorschlag 12.08.:** *„ich schlage vor, dass wir hier mit einem Mittelwert
anfangen und dann pro Signal uns anpassen."* Das ist exakt das Verfahren, das der
Standard dafür vorsieht — **Schrumpfung zum Mittelwert** (empirisches Bayes):

```
              k + m · p₀
       p̂  =  ────────────
               n + m

  p₀ = Basisrate 34 %   (der Mittelwert, mit dem wir starten)
  k  = Treffer dieser Konstellation
  n  = Fälle dieser Konstellation
  m  = Gewicht des Mittelwerts, Startwert 50
```

| n | Ergebnis |
|---|---|
| 0 Fälle | **34 %** — der Mittelwert, unverändert |
| 20 Fälle, 12 Treffer | 34 % → **38 %** — vorsichtig angepasst |
| 300 Fälle, 123 Treffer | **40 %** — die Messung trägt jetzt selbst |

**Es gibt keine Schwelle, die jemand setzt, und keinen Schalter, den jemand
umlegt.** Die Kalibrierung läuft mit jedem neuen Ausgang automatisch mit und ist
von Anfang an ehrlich: bei wenigen Fällen sagt sie schlicht die Basisrate.

**Der Filter ist damit keine Zahl, sondern ein Vergleich:** `p̂` gegen den
Kosten-Breakeven. Liegt die Konstellation darunter, trägt sich der Trade
rechnerisch nicht.

### 6.5 Wo der Filter sitzt — und warum das LLM ihn NICHT sieht

```
Fakten -> [ LLM urteilt: Aktion, Belege, Begründung ] -> Filter -> Signal -> E-Mail
                        ^                                  ^                   ^
                 sieht den Filter nicht          deterministisch        der Nutzer sieht ihn
```

**Drei Gründe, alle belegt:**

1. **Ankereffekt.** Sagt man dem Modell „diese Konstellation traf historisch in
   41 %", richtet es sein Urteil daran aus, statt die Fakten zu lesen. Gemessener
   Ankerindex 0,45, **Experten-Anker wirken am stärksten** — eine Zahl aus dem
   eigenen System ist der stärkste denkbare Anker. Keine Gegenmaßnahme aus der
   Literatur hat funktioniert.
2. **Zirkularität.** Die Tabelle entsteht **aus den Urteilen des Modells**. Sie
   ihm zurückzugeben macht aus einer Messung eine Rückkopplung.
3. **Nachfilter statt Vorfilter.** Ein Vorfilter ist **unsichtbar** — was er
   wegschneidet, sieht niemand. Ein Nachfilter ist **messbar**: jedes abgelehnte
   Signal bleibt sichtbar und rückwirkend prüfbar. Genau der Fehler des alten
   Nur-Long-Vorfilters, behoben am 05.08.

| | Filter / Trefferquote |
|---|---|
| 1 LLM-Eingabe | **nein** — Anker und Zirkularität |
| 2 LLM-Ausgabe | nein — deterministisch |
| 3 Messung | **ja** — er *ist* die Messung |
| 4 Anzeige | **ja** — die Zahl und ihre Wirkung stehen in der Mail |

---

## 6a. Getrennte Töpfe — Absicherung braucht eine Sonderstellung

**Nutzervorgabe 12.08.:** *„Absicherung soll nicht ausgeschlossen werden, sondern
es benötigt eine Sonderstellung, ohne dass die anderen Handlungen beeinflusst
werden — gilt für alle Bereiche, wo mit Beträgen gerechnet wird. Beispiel: es
kommen keine Kaufpositionen rein, weil Hedge gering ist. Oder kein Hebel, weil
mein aktueller Cash-Anteil zu gering ist."*

**Ist-Zustand, geprüft — die Sorge ist heute noch nicht eingetreten:**

> `agent/empfehlung_vertrag.py:47`: *„das Cash-Veto hat in **118 Signalen kein
> einziges Mal** gegriffen."* Und die Entwurfsentscheidung: *„Cash bleibt eine
> **INFORMATION**, kein Veto."*

Und für die LLM-Aufrufe existiert das gewünschte Muster bereits:
`budget_allocator._verteile_budget()` verteilt gestaffelt (Hebel → Marktscan →
Spot) mit einer **`spot_reserve`**, die verhindert, dass Hebel den Spot
aushungert — Sonderstellung ohne Beeinflussung, nur für Aufrufe statt für Geld.

### Die Vorgabe

> **Getrennte Töpfe je Zweck — Spot · Hebel · Absicherung. Keine Verrechnung
> untereinander, in keiner Richtung.**
>
> - Ein niedriger Absicherungsgrad **erzeugt** einen Hedge-Vorschlag; er
>   **unterdrückt keinen Kauf**.
> - Ein knapper Cash-Anteil **begrenzt die Größe** einer Position; er
>   **verhindert keine Aktion** in einem anderen Topf.
> - Wo eine Größe *doch* über Töpfe hinweg wirken soll, ist das eine
>   **ausdrückliche Regel mit Namen** — nie ein Nebeneffekt einer Budgetformel.

Das gilt für **jede** Stelle, an der mit Beträgen gerechnet wird: Positionsgröße,
Cash-Reserve, Tranchen, Budget-Allocator, Hebel-Deckel.

---

## 7. Was bricht — die vollständige Nahtliste

### 7.1 Zwingend, sonst funktioniert das System nicht

| Naht | Befund |
|---|---|
| **Backward-Tracking ↔ Take-Profit** | `backward_tracking.py:397` liest `take_profit_usd_von/bis`. Ohne TP kein `take_profit_erreicht`, kein realisiertes CRV — **und damit keine Zahl für §6** |
| **Feldabbildung neue Kette → `signals`** | `unabhaengige_faktoren` und `umgeworfen_durch` haben in den 112 Spalten kein Zuhause |
| **E-Mail** | `Konfidenz X %` steht **fest in der Abschnittsüberschrift**; Regime-Zeile; Top-Gründe 1–5; Risikofaktoren; Forecast bull/base/bear |
| **Hebel-Tab** | braucht `richtung`, `hebel_faktor`, 7 Aktionen — die neue Kette hat 5 Spot-Aktionen |
| **Konfidenz-Schwelle in allen 6 Pipelines** | `min_konfidenz_prozent` aus dem Regime-Profil steuert das Risk-Gate. Die neue Kette liefert keine Konfidenz — **es gibt heute keinen Ersatz** |

### 7.2 Strukturell, nicht durch Umbenennen lösbar

**Hedge passt nicht in die Rollen-Kette.** `agent/hedge/analyst.py` macht laut
eigenem Modulkopf **bewusst keine Einzeltitel-Technikanalyse** — 3QSS
(Nasdaq-100 3x Short) hat keine Kurshistorie, und ein gehebeltes inverses
Produkt bräuchte eine tägliche Rebalancing-Simulation. Er urteilt über
**Portfolio-Exposure**.

Die Rolle „Befund" ist aber genau auf Einzeltitel-Technik gebaut. **Hedge
braucht einen eigenen Faktensatz**: Exposure, Korrelation, Absicherungsgrad.

### 7.3 Überlebt — geprüft, entgegen erster Annahme

| | |
|---|---|
| **Ausstiegs-Empfehlung** | `stopempfehlung_aus_mfe(entry, stop, mfe_r)` braucht nur Einstieg und Stop — beides vorhanden |
| **Nur-Long-Filter** | am 05.08. bereits richtig umgebaut: SHORT läuft voll durch die Kette, gefiltert wird **nur** an der Präsentationsgrenze (`_ist_email_relevante_richtung()`, `ui/hebel_view.py`). Die Ausstiegs-Mail nimmt SHORT bewusst aus dem Filter |

### 7.4 Kleinigkeiten

- `ui/letzte_bewertung.py` — **eine Zeile** mit `confidence_pct`
- `scheduler/background.py:258` — Kommentar beschreibt den CoinGecko-Rückfall
  noch als aktiv, obwohl er abgeschaltet ist (**eigene Datenleiche vom 12.08.**)

---

## 8. Was NICHT betroffen ist — geprüft, nicht vermutet

| Bereich | Befund |
|---|---|
| **Screener** (`agent/aktien/screener.py`) | **kein LLM**, kein Regime, keine Konfidenz. ETF-Findung enumeriert **Bitpandas eigenen Katalog** — bewusst kein yfinance-Screen, weil eine UCITS-Discovery am kaufbaren Sortiment vorbeiginge. Themen-Gewichtung `_kategorie_score_bonus()` ist **objektiv gegatet** (hängt an `gestuetzt`/`widerspricht`, nicht an der bloßen Existenz einer These) |
| **Marktscan** | nutzt `liquiditaets_regime`, `zyklus_risiko`, `btc_matrix_state` — die **gesunden** Regime-Teile, nicht das tote Etikett. CoinGecko-**Client** (Marktentdeckung) unberührt vom OHLC-Schnitt |
| **`agent/tranchen.py`** | nutzt `equities_baermarkt_aktiv`, `vix_label` — ebenfalls gesunde Teile |
| **`kategorie_vorschlaege`** | rein deterministisch, kein LLM-Aufruf |
| Portfolio, Watchlist, `detail_panel`, `signal_stabilitaet_chart` | keine Altfelder |
| `portfolio_wert`, `bitpanda_holdings`, `marktscan_backward_tracking`, `makro_analog` | unberührt |

**Offen zur Durchsicht:** `agent/kategorie_synthese.py` (eigener Prompt,
Etikett-Muster) — erzeugt keine Handelssignale, deshalb **eigene Stufe nach der
Signalkette**.

---

## 8a. Die Gegenprüfung läuft KUMULATIV — `pruefe_pakete.py`

**Nutzervorgabe 12.08.:** *„mache rückwirkend über alle Pakete pro neuem Paket
eine Gegenprüfung, sonst verlieren wir den Faden."*

Der Punkt ist die **Rückwirkung**. Jedes Paket einmal zu prüfen und danach nie
wieder heißt, dass Paket 5 Paket 1 still zerbricht — und genau das ist am
12.08. **zweimal** passiert:

| | |
|---|---|
| Der Marktbreite-Schnitt entfernte `TRAGFAEHIGKEIT` — daran erkannte der Schema-Verteiler die Rolle Lagebild. Jeder strikte Aufruf wäre mit `AttributeError` gestorben | gefunden **einen Umbau später** |
| Zwei neue Felder vergrößerten einen Strikt-Vertrag-Verstoß, den es vorher schon gab. Die volle Fläche zeigte **28–31 Verstöße je Signal-Analyst** | vorher nie geprüft |

**Beides hätte ein Lauf dieser Datei gefangen.**

```bash
python pruefe_pakete.py            # alle Pakete
python pruefe_pakete.py --paket 1  # nur eines
```

Stand: **404 Prüfungen** über Paket 0–14, 12b/12c/12d, die Gesamtprüfung, B1, den Export und die Analysestandards, alle bestanden.

**Nummern-Korrektur 12.08. abends:** die Diskussion hat die Reihenfolge verschoben. Die Prüfpakete 10–12 tragen jetzt den Inhalt, der wirklich gebaut wurde; „Gate" und „Z1 + Z.ai" stehen als **12c/12d** weiter offen und sind **übersprungen, nicht erledigt**. Kein LLM-Aufruf, kein
Netzwerk, keine Schreibzugriffe — sie darf jederzeit laufen.

> **Regel für neue Pakete:** wer ein Paket baut, hängt seine Prüfungen dort an
> **und lässt die alten mitlaufen.** Eine Prüfung, die nur am Tag ihrer
> Entstehung lief, ist eine Notiz, kein Netz.

Ein Detail, das die Datei schon bewiesen hat: sie liest **nur aktiven Code**,
Kommentarzeilen fliegen raus. Dieses Projekt hält Entferntes ausführlich im
Kommentar fest — ein `grep` fände die gelöschte Zeile in ihrer eigenen
Grabinschrift wieder. Genau dieser Fehler ist am 12.08. passiert, als der
Nur-Long-Vorfilter als aktiv galt, weil ein Kommentar seine Entfernung
beschrieb.

Und beim ersten Lauf hat sie einen Fehler **in einer meiner eigenen Prüfungen**
gefunden: `"Hebel"` galt dort als ungültig, obwohl `pruefe()` die Schreibweise
absichtlich normalisiert. In der Einzelprüfung war das verdeckt, weil der
Testfall mit `akkumulation` gepaart war — dort warf schon die Kombination.

---

## 9. Reihenfolge — Arbeitspakete

Die Reihenfolge folgt einer Zwangskette:

```
Take-Profit -> Backward-Tracking misst -> Trefferbilanz -> die Zahl in der Mail
```

**Ohne den ersten Schritt gibt es den letzten nie.**

| # | Paket | Inhalt |
|---|---|---|
| **0** | **Bereinigungen** | **ERLEDIGT 12.08.** — Symbolliste `("BTC","ETH","SOL")` raus (sie überstimmte den Schalter) · Hedge ohne Tranchen (Regel stand mit umgekehrtem Vorzeichen) · Kommentarleiche `background.py:258` |
| **1** | **Ausgabefelder** | **ERLEDIGT 12.08.** — `leite_zonen_ab()`: Zielkurs aus CRV 2,0, Spannen aus 0,25 ATR um Einstieg/Stop/Ziel; Falsifikator maschinenlesbar (`umgeworfen_preis_eur`, `umgeworfen_bis`). In `validiere()` verdrahtet, alle **sieben** Aufrufer reichen den ATR durch. **Richtung + Hebelfaktor gehören zu Paket 13**, nicht hierher |
| **2** | **Instrument + Strategie** | **ERLEDIGT 12.08.** — `agent/handelsauftrag.py`: drei Instrumente × drei Strategien, **drei Paare bewusst ausgeschlossen** (hebel×akkumulation, absicherung×swing/akkumulation). Der Auftrag steht **zuerst** im Faktensatz (R-T9), Schritt 3 des Prompts hängt an der Strategie, und `validiere()` entfernt Kurse, wo die Strategie keine hat. Prompt und Faktensatz lesen **dieselbe** Definition |
| **3** | **Rolle 1 urteilt je Assetklasse** | **ERLEDIGT 12.08.** — Feld `klassen` (günstig/gemischt/ungünstig je Leitmarkt, mit Begründung), an den Trader weitergereicht **nur für seine eigene Klasse**. **Statt des Regime-Scores die Anlegerstimmung**: der Score ist zur Hälfte Kursabstand und dopplte L3 — die Stimmung ist die neue Hälfte. Historie nachgeladen: **3.111 Tage ab 2018** (`lade_fear_greed_nach.py`), vorher 10 |
| **4** | **Makro in die Rollen-Kette** | **ERLEDIGT 12.08.** — **Befund: der Thesen-Abgleich liefert heute NICHTS** (13 von 57 Assets mit Hauptgruppe, `thesen`-Tabelle **0 Zeilen**). Thesenunabhängig sind aber die Daten darunter: **Netto-Liquidität** (FRED WALCL−WTREGEN−RRPONTSYD) und **Zinskurve** (^TNX/^IRX). Historie nachgeladen (`lade_makro_historie_nach.py`): 501 Wochenwerte ab 2017 + 2.414 Zinstage. Die These des Nutzers bleibt **draußen** — sie wäre ein Anker |
| **5** | **Getrennte Töpfe** (§6a) | **ERLEDIGT 12.08.** — `agent/toepfe.py`. Deckel **absolut in Euro, nicht in Prozent**: ein Prozentdeckel schrumpft mit dem Verlust (bei −70 % nur noch 30 %, während die Erholung +233 % braucht) und bremst damit am stärksten, wenn Handeln am nötigsten ist. **Nur der Hebel hat einen Deckel** (500 EUR) — Spot und Absicherung keinen. Keine Funktion kennt den Portfoliowert, also kann eine fehlende Bewertung nichts sperren |
| **6** | **Feldabbildung → `signals`** | **ERLEDIGT 12.08.** — `agent/signal_abbildung.py`. **`NICHTS_TUN` wird auf `HALTEN` abgebildet** — korrigiert nach Nutzereinwand: auf Asset-Ebene ist beides dieselbe Aktion (kein Trade, Stand bleibt), und der Unterschied „halte ich es überhaupt" steht im Bestand, nicht im Aktionsnamen. Zwei Etiketten für dasselbe Ergebnis würden jede Auswertung zwingen, beide zu kennen. **`REDUZIEREN` bleibt eigenständig** (Teilverkauf ≠ Vollverkauf). Sieben neue Spalten + Tabelle `lagebilder` (eine Zeile je Durchgang statt 44-facher Redundanz). **`facts_json` ist Pflicht** — es war bei 78 von 118 Altsignalen leer |
| **7** | **Backward-Tracking** | **ERLEDIGT 12.08.** — der Bruch war eine **Währung**: das Tracking lädt USD-Kerzen und vergleicht `entry_usd`/`stop_loss_usd`/`take_profit_usd`, die neue Kette schrieb nur EUR → `_zonen_mittel` gab `(None, None, None)`, jedes Signal wäre für immer unaufgelöst geblieben. Jetzt **USD-Spiegelung mit eingefrorenem Kurs** (misst die Asset-Bewegung, nicht die des Wechselkurses). Nebenbei gefunden: die Spanne war **14,4 % zu breit**, weil der ATR aus der USD-Reihe auf EUR-Kurse angewandt wurde |
| **8** | **Trefferbilanz / Schrumpfung** (§6.4) | **ERLEDIGT 12.08.** — `agent/trefferbilanz.py`. Die Formel **reproduziert** den bekannten Befund, statt ihn zu behaupten: ohne Kosten exakt 33,3 %, mit Krypto-Kosten 41,0 % gegen eine Basisrate von 34,0 % → trägt nicht. **Abgelaufene Fälle werden ausgewiesen, nicht verrechnet** (7.23 — „keines = 0 R" ist eine Setzung, betrifft 15–21 %). Die Bilanz **verwirft nichts**: sie rechnet und beschreibt |
| **9** | **Live-Lauf auf `gemini-3.1-flash-lite`** | Wortlaut zeigen. **Nicht 3.5** — alle bisherigen Messungen liefen auf 3.5 |
| **10** | **Berechnung der Entscheidung** | **ERLEDIGT 12.08.** — `entscheidungsrechnung.py`: Zone, Stop, Ziel, Haltedauer, Betrag, Hebel; jede Zahl mit Formel, Quelle und ZWEI Grenzen. Stop aus `umgeworfen_preis_eur` des Modells, geklemmt durch RM-1b/1c und die neue Obergrenze |
| **11** | **Take-Profit + Mail** | **ERLEDIGT 12.08.** — Ziel am nächsten Widerstand statt mechanisch 2 R, zu kleine CRV wird ausgewiesen; `signal_mail.py` mit vier Abschnitten |
| **12** | **Faktenblock + Chart** | **ERLEDIGT 12.08.** — `faktenblock.py` (drei gemessene Familien + Zusatzinfo je Bereich), an echte Kursreihen angeschlossen; `ui/signal_chart.py` ersetzt beide alten Charts |
| **12b** | **GUI** | **ERLEDIGT 13.08.** — Regime-Tab zeigt den Score samt Stützstellen, der Override setzt ihn. *Die E4-Zeile „Score als Fakt an Rolle 1" ist begründet abgelehnt: der Score besteht aus 0,5 × EMA50-Abstand + 0,5 × Fear & Greed und liegt damit vollständig in der Momentum-Familie (Kap. 12.8)* |
| **12c** | **Gate** | **ERLEDIGT 13.08.** — `rollen_gate.py`: Konfidenz-Schwelle entfällt, Durchlässigkeit je Stufe (acht Stufen, die letzte zählt nur), Faktorzahl nur mitgeschrieben |
| **12d** | **Z1 + Z.ai** | **ERLEDIGT 13.08.** — Z1 verdrahtet (zählen, nicht verwerfen); Z.ai kennt alle fünf Aktionen — REDUZIEREN fiel bis dahin still durch — und bekommt die Faktensätze der neuen Kette |
| **13** | **Hebel** (E2) | **ERLEDIGT 13.08.** — sieben Aktionen, Richtung vom Modell, Hebelfaktor gerechnet; Stop, Ziel und Liquidation drehen bei SHORT. Finanzierung und Liquidationsabstand standen bereits in Faktenblock und Rechnung |
| **14** | **Hedge** (E1b) | eigene Rolle, Portfolio-Fakten statt Einzeltitel-Technik |
| **15** | **Rollout** | ein Paket, Notebook, Checkliste 8e.3 |
| **16** | **Kategorie-Synthese** | eigene Stufe, kein Signalweg |

---

## 10. E1 bis E4 — entschieden am 12.08.

### E1a — DCA: rein, aber als Bereinigung

**Der Ist-Zustand ist bereits fast das Zielbild.** DCA ist kein toter Schalter,
sondern ein **Umschalter je Asset im Watchlist-Tab** (`ui/app.py:876`), verdrahtet
in **allen fünf** Pipelines.

> **Nutzermodell:** *„ich möchte selbst entscheiden, bei welchen Assets die
> Strategie angewendet wird — überall möglich außer Absicherungspositionen, aber
> nur dort Signale erzeugen, wo ich das selektiv möchte."*

Zwei Abweichungen sind zu bereinigen:

1. **Die fest verdrahtete Liste `("BTC","ETH","SOL")`** in `krypto/pipeline.py:724`
   widerspricht dem Modell — sie schneidet Assets weg, die der Nutzer
   eingeschaltet hat. Begründet ist sie mit „Tranchen sind für die größten,
   liquidesten Positionen gedacht": eine Annahme, kein Messergebnis, und sie
   **doppelt den Schalter**. → **raus**, der Schalter ist die Entscheidung.
2. **Hedge bekommt heute Tranchen** (`hedge/pipeline.py:756`). Der Code hält das
   selbst für fragwürdig: *„Für Hedge ist sie sogar potenziell invers — DBPK/3QSS
   sind Short-Produkte, für die ein Bärenmarkt das GUTE Umfeld ist."*
   → **Hedge ausdrücklich ohne Tranchen** (Nutzer bestätigt).

**Damit ist DCA kein Neubau, sondern ein kleines Bereinigungspaket.**

### E1b — Hedge: rein, als eigene Rolle, terminiert nach Spot und Hebel

*Nutzer: „kann man als eigene Rolle sehen — ja, aber Nebenthema, soll das
Primärziel nicht beeinträchtigen. Entscheide du — als glatter Schnitt müssen wir
es umbauen."*

**Entscheidung:** rein. Der glatte Schnitt verlangt es, und Absicherung ist der
Teil, der im Bärenmarkt zählt. Aber **nicht** in „Befund" gepresst — für 3QSS gibt
es keinen Einzeltitel-Chart. Eigene Rolle mit Portfolio-Fakten (Exposure,
Korrelation, Absicherungsgrad), eingeplant **hinter** Spot und Hebel, damit sie
das Primärziel nicht blockiert. Die Tranchen-Bereinigung aus E1a wird
**vorgezogen** — sie kostet nichts.

### E2 — Hebel: ja, als Paket 2 nach Spot

*Nutzerentscheidung.* Hebel braucht zwei Fakten, die Spot nicht braucht
(Finanzierung je Tag, Liquidationsabstand) und trägt die höhere Kostenquote —
also genau dort, wo die Netto-Rechnung am ehesten kippt. Erst wenn Spot
durchgemessen ist, wissen wir, ob die Kette überhaupt trägt.

### E3 — Konfidenz-Schwelle: ersatzlos. Der Entscheider IST der Filter

**Sie fällt nicht durch Wahl, sondern als Folge:** sie prüft `confidence_pct`, und
die neue Kette produziert keine Konfidenz (77,5 % vorhergesagt gegen 33,3 %
eingetreten).

**Sie hat auch nie gewirkt, und das ist belegt:**

> `Regelwerk_Entscheidungslog.md:15526` —
> **Korrelation Konfidenz × realisiertes CRV: r = +0,073 (n = 92)**

Dazu: das Regime war über 1.022 Fälle konstant „baer" → die Schwelle stand
faktisch immer bei **75**, für jedes Asset, in jeder Marktlage. **Eine konstante
Schwelle auf einer nutzlosen Größe.**

**Einen Ersatz brauchen wir trotzdem** — aus unserer eigenen Rechnung: brutto
+0,028 R, netto krypto −0,230 R. Die Kosten kippen das Vorzeichen, also wirkt
jeder vermiedene schwache Trade direkt auf die Größe, an der wir scheitern.

**Der Fachstandard nennt die Lösung Meta-Labeling** (López de Prado 2018):
Richtung und Größe werden entkoppelt; ein Sekundärmodell urteilt nicht über den
Markt, sondern über das Primärmodell — *hat es diesmal wahrscheinlich recht?* Es
filtert Fehlsignale und damit unnötige Transaktionskosten.

> **Die Auflösung: der Ersatz ist keine neue Schwelle, sondern der Entscheider
> selbst.** Die kalibrierte Trefferquote gegen den Kosten-Breakeven **ist** der
> Filter (§6.4/6.5). Eine Mechanik statt zwei — und die einzige, die gemessen
> statt gesetzt ist.

**Bis die Tabelle trägt:** kein LLM-seitiger Qualitätsfilter. Die Faktorzahl wird
nur **mitgeschrieben** (Veto-Schatten), nicht scharf geschaltet. Drei Gründe: ein
unbelegter Filter ist schlechter als keiner (die Faktorzahl zeigte in der Messung
**keinen Effekt**, 7.26); ein Filter verkleinert die Stichprobe, die wir zum
Kalibrieren brauchen; und das System hat monatelang nicht gekauft — ein
zusätzlicher unbegründeter Filter ist genau das Risiko, das gerade beseitigt
wurde.

**Die RM-Schicht bleibt unangetastet** (RM-1…RM-7, Cash-Reserve,
Positionsgrößen-Deckel, Vetos). Sie ist nicht defekt und ist ausdrücklich die
Schicht, in die Risiko gehört.

### E4 — Regime-Tab: Score statt Etikett, der Override bleibt

Der Tab ist **kein Anzeigefeld, sondern ein Bedienelement** — manueller Override
(RG-8).

| | heute | künftig |
|---|---|---|
| Anzeige | Etikett „baer" (konstant) | **Regime-Score 0,00–1,00** + die vier Stützstellen als Lesehilfe |
| Wirkung | `min_konfidenz` + Konflikt-Veto | **Score geht NICHT als Fakt an Rolle 1 — Begründung unten.** Konflikt-Veto kehrt zurück, sobald es wieder eine Richtung gibt (Hebel, Paket 13) |
| **Override** | setzt das Etikett | **setzt den Score** — derselbe Hebel, feinere Auflösung |

Der Score ist gebaut, variiert 0,250–0,750 und trennt die Marktphasen. Der
Override wird dadurch **mächtiger**, nicht schwächer: statt vier Schubladen ein
Regler.

**Korrektur 13.08. beim Umsetzen von 12b: die Zeile „Score als Fakt an Rolle 1"
wird NICHT umgesetzt — und der Grund ist eine eigene Messung.** Der Score
besteht laut `regime.regime_score()` aus:

    0,5 × Preis (Abstand zu EMA50, EMA200 mit halbem Gewicht)
  + 0,5 × Fear & Greed

**Beides liegt vollständig in der Momentum-Familie** (Kap. 12.8): der Abstand
zur 50-Tage-Linie ist einer der vier Momentum-Vertreter (Rangkorrelation 0,59
bis 0,89 untereinander), und Fear & Greed gehört ebenfalls dorthin, weil er zur
Hälfte aus dem Kurs abgeleitet ist.

Ihn als eigenen Fakt an Rolle 1 zu geben, hieße einen **fünften
Momentum-Vertreter** danebenzustellen — und würde einen Aufbau besser belegt
aussehen lassen, als er ist. Genau das verhindert die Regel „Momentum erscheint
genau einmal".

**Die anderen beiden Zeilen sind umgesetzt:** die Anzeige zeigt den Score samt
Stützstellen, und der Override setzt ihn.


---

## 11. Was dieser Plan über sich selbst weiß

Er entstand aus einer Gegenprüfung, die **zwei eigene Fehler** aufgedeckt hat:

1. **`gemini-3.5-flash-lite` als Produktionsmodell berichtet** — gelesen in einem
   Prüfskript, während `api/gemini.py:35` **3.1** sagt.
2. **Den Nur-Long-Vorfilter als aktiv gemeldet** — gelesen war ein Kommentar
   über etwas, das am 05.08. **entfernt** wurde.

Beide Male war die Ursache dieselbe: eine Zeile gegrept statt den Block gelesen.
**Nutzervorgabe daraus: immer an der Quelle prüfen.** Jede Aussage in diesem Plan
nennt ihre Fundstelle, damit sie nachprüfbar ist statt geglaubt werden zu müssen.

Und ein dritter, den der Nutzer korrigiert hat: ich hatte „das Modell soll eine
Wahrscheinlichkeit nennen" mit „das Modell soll urteilen" vermengt und deshalb
eine Tabelle als **Ersatz** für ein Urteil vorgeschlagen, das gar nicht ersetzt
werden muss. **Die Kalibrierung misst das Urteil — sie ersetzt es nicht.**

---

# 12. Die deterministische Schiene in der E-Mail (12.08.2026, abends)

## 12.1 Warum es diesen Abschnitt gibt

Die erste Fassung der neuen Mail war dem Nutzer zu dünn: *„Modell Urteil — Info
ist mehr als schlank … Als erster Wurf ok, aber hier müssen wir nachschärfen."*

Mein erster Vorschlag war falsch: **die Faktenlage für das LLM verbreitern**
(MACD, RSI, Funding, Optionsmarkt zurück in den Prompt), damit die Belege Zahlen
tragen. Der Nutzer hat das korrigiert:

> *„ganz wichtig — nein, es sollen keine Zahlen in die Ablaufkette bzw. LLM —
> aber als Info bzw. wo als Fakt vorhanden und sinnvoll ergänzen
> (deterministische Schiene kombiniert)."*

Das ist die bessere Lösung, und sie lässt **Kapitel 11.6 der
Fakten-Entscheidungsmappe unangetastet**. Es gibt ab hier **zwei Schienen**:

| | wer liest es | welche Regeln gelten |
|---|---|---|
| **Faktentext** | das Sprachmodell | R-T1…R-T9: relativ vor absolut, benanntes Fenster, keine rohen Zahlenreihen |
| **Faktenblock** | der Nutzer | Lesbarkeit: **absolut zuerst**, Etikett statt Perzentil, eine Währung |

**Das war der eigentliche Denkfehler der ersten Mail:** ich hatte die Sätze für
das *Modell* in die Mail übernommen. Daher stand dort „3,9 Schwankungsbreiten
höher, bei 62.000 EUR" statt „62.000 EUR, das sind 3,9 Schwankungsbreiten" — und
daher stand dort ein Perzentil, wo ein Etikett hingehört. R-T1 und R-T2 wurden
für ein Modell hergeleitet, das absolute Zahlen nicht einordnen kann. **Der
Nutzer kann das.**

## 12.2 Bestandsaufnahme — was vorliegt

Erhoben aus den sechs `build_facts()` der bestehenden Pipelines. **40 Schlüssel,
sehr ungleich verteilt:**

| | Spot | Hebel | Aktien | Rohst. | ETF | Hedge |
|---|---|---|---|---|---|---|
| Schlüssel gesamt | 21 | 21 | 17 | 16 | 14 | 11 |

**In allen sechs vorhanden — nur fünf:** `preis`, `regime`,
`historische_erfolgsquote`, `historischer_makro_vergleich`, `disclaimers`.

**Je Bereich eigen** — und das ist der Grund, warum der Block nicht einheitlich
sein kann (Nutzer: *„sollte u.U. je Assetklasse bzw. Bereich unterschiedlich
sein"*):

| Bereich | was es NUR dort gibt |
|---|---|
| **Krypto Hebel** | `optionsmarkt` (Put-Skew), `kosten` (Funding), `hebel_kontext`, `ausstiegsregel`, `systemguete`, `trigger`, `position_aktuell` |
| **Krypto (beide)** | `btc_relativwert`, `liquiditaetszonen`, `markt_kontext`, `antizyklisch`, `regime_profil`, `signal_stabilitaet` |
| **Aktien** | `fundamentaldaten`, `analysten_trend_finnhub`, `insider_trading`, `short_interest_finra` |
| **Rohstoffe** | `lagerbestaende`, `positionierung`, `makro_ueberlagerung` |
| **Themen-ETF** | `sektor_rotation` |
| **Hedge** | `portfolio_exposure`, `hedge_instrument` |

## 12.3 Was fehlt

**Die neue Rollen-Kette kennt elf Faktenfamilien** (Makro, Trend, Volatilität,
Liquidität, Stimmung, Gleichlauf · Bestand, Struktur, Bewegung, Niveaus,
Volumen). Die alte Kette trug 40 Schlüssel. **Der Unterschied ist kein Verlust,
solange er auf der deterministischen Schiene wieder ankommt** — er darf nur
nicht im Prompt landen.

Offen und zu klären:

1. **`retail_konsens` — gefunden, und der Fund bestätigt die Zwei-Schienen-
   Trennung.** Er steckt in `antizyklisch`, gespeist aus
   `api/derivatives.py::get_binance_long_short_ratio()` → `long_account_pct`.
   Und in `agent/krypto/hebel_analyst.py:156` steht wörtlich, er *„gehört
   NIEMALS in `top_gruende`"*. Es gibt also bereits eine Regel, die ihn aus der
   Begründung des Modells heraushält — **genau der Fakt, der auf die
   deterministische Schiene gehört und nirgends sonst hin.**

   Grenzen, die mitgeschrieben gehören: **nur Binance**, **nur Krypto**, und es
   ist der *Konten*-Anteil, nicht der positionsgewichtete. Für Aktien,
   Rohstoffe und ETF gibt es kein Gegenstück — der Block kann also auch aus
   diesem Grund nicht einheitlich sein.
2. **Währungseinheit.** Die alte Hebel-Mail mischt EUR und USD ohne Kennzeichen
   (siehe 12.5). Der Faktenblock braucht **eine** Währung.
3. **Welche der 40 tragen überhaupt etwas?** Der Regler-Audit vom 04.08. fand
   36 von 202 Schlüsseln wirkungslos. Ein Fakt in der Mail, den niemand nutzt,
   ist Füllstoff — genau der Vorwurf, der die Risikofaktoren-Legende gekostet
   hat.

## 12.4 Die Meinung des Marktanalysten — ja, aber nur mit Zahl

Nutzerfrage: *„u.U. kann man auch die Meinung des Marktanalysten hinzugeben,
wenn diese sinnvolle Daten enthält."*

Rolle A liefert dreierlei: **Lage in Prosa**, **Urteil je Assetklasse**, und je
Urteil einen **Beleg mit Zahl**. Aufgenommen wird das Urteil **samt Beleg** —
das ist eine begründete Einordnung. Die freie Prosa daneben nicht: sie stünde
als zweite Meinung neben dem Urteil aus Abschnitt 3 und könnte ihm
widersprechen. **R-T8 gilt auch für die Mail:** zwei Blöcke derselben Nachricht
dürfen einander nicht widersprechen.

## 12.5 Prüfbefund zur alten Mail — zwei Währungen, nicht gekennzeichnet

Der Nutzer hat einen Screen der alten Hebel-Mail (05.08., HYPE LONG) zur
Prüfung gegeben. Sie enthält einen Fehler, der jeden Zahlenvergleich darin
entwertet:

| steht dort | Einheit | in EUR |
|---|---|---|
| Abschnitt 1: `Entry: 49,74-49,91 EUR` | EUR | 49,8 |
| LLM-Text: *„Fibonacci-Level 0.382 bei 57.28"* | **USD** | 49,9 |
| LLM-Text: *„Buyside-Zone bei 65.61"* | **USD** | 57,2 |
| Grafik: *„Buy-Side-Zone: 57.05 EUR"* | EUR | 57,05 |
| Fazit: *„Entry 57.3, Stop 54.6, TP 65.6"* | **USD** | 49,9 / 47,6 / 57,2 |

Dieselbe Zone heißt im Text **65,61** und in der Grafik **57,05 EUR**; das Fazit
nennt einen Entry, den Abschnitt 1 nicht kennt. Der Faktor ist durchgehend
1,147. Dazu zwei kleinere Widersprüche: **CRV 2,89** gegen **3,0** im Fazit, und
**Stop-Abstand 4,7 %** gegen **4,9 %**.

Derselbe Fehlertyp wie in `leite_zonen_ab` (ATR aus USD auf EUR-Niveaus, am
12.08. gefunden). **Für die neue Mail ist das eine Pflichtprüfung.**

## 12.6 Die Charts

| | Urteil |
|---|---|
| **Signal-Stabilität** (Konfidenzverlauf) | **raus.** Er plottet genau die Größe, die wegen 77,5 % vorhergesagt gegen 33,3 % gemessen gestrichen wird. Das Verlaufsbild einer unkalibrierten Zahl ist doppelt irreführend |
| **Liquiditätszonen** | **raus in dieser Form.** Er zeigt die Buy-Side-Zone, aber **nicht Einstieg, Stop und Ziel** — also gerade nicht das, was zu tun wäre. Dazu überlappende Beschriftungen und der Währungsfehler aus 12.5 |
| **NEU: ein Chart** | 90 Tage Kurs mit **Einstiegszone, Stop, Ziel** als Bänder, plus Widerstand und Unterstützung. Damit wird Abschnitt 2 auf einen Blick prüfbar: liegt der Stop unter einer echten Marke, steht das Ziel vor der Mauer? |

## 12.7 Sentiment — gemessen, und die Vermutung hält nicht

Nutzerthese, ausdrücklich als unbewiesen gekennzeichnet: *„sehr schlechtes
Sentiment ist oft für DCA oder Spot (längerfristig) gut, eher schlecht bei
Hebel."* Gemessen an BTC über **3.087 Tage mit Kurs UND Stimmung** (2018-02 bis
2026-07), `messe_sentiment_je_horizont.py`:

**Kurz, 10 Tage** — Basis 26,0 % Trefferquote:

| Stimmung | n | Treffer | ggü. Basis |
|---|---|---|---|
| extreme Angst | 673 | 19,7 % | **−6,3 pp** |
| Angst | 869 | 23,1 % | −2,9 pp |
| neutral | 451 | 21,9 % | −4,1 pp |
| Gier | 740 | 29,7 % | +3,7 pp |
| extreme Gier | 330 | **38,3 %** | **+12,3 pp** |

Monoton — und **in die Gegenrichtung der These**. Auf 90 Tagen läuft es gleich
herum, dort trägt die Messung aber wenig: in 3.087 Tagen stecken nur rund **33
unabhängige** 90-Tage-Fenster, die Bänder sind entsprechend breit.

**Warum es so herauskommt, und warum es kein Widerspruch zur Literatur ist:**
Fear & Greed ist zur Hälfte aus dem Kurs abgeleitet (Volatilität 25 %,
Marktdynamik/Volumen 25 %), dazu BTC-Dominanz 10 %. Er misst weniger eine
Stimmung als einen **Trend**. Der Befund ist damit Time Series Momentum
(Moskowitz/Ooi/Pedersen 2012), nicht Sentiment-Contrarian (Baker/Wurgler) — und
die Contrarian-Literatur arbeitet mit **Umfragen** und mit **Aktien**, beides
trifft hier nicht zu.

**Folgen für die Mail:** „Angst" darf nicht als Gelegenheit dargestellt werden.
Und der Index gehört als das benannt, was er ist — **Bitcoin**, nicht der
Kryptomarkt. Im Faktenblock steht der Absolutwert mit Etikett
(*„Fear & Greed für Bitcoin: 27 von 100 — Angst"*), nicht das Perzentil.

## 12.8 Welche Fakten tragen — gemessen statt behauptet

Nutzerauftrag: *„damit es keine Überhand nimmt — u.U. kannst du die 10 Top
Fakten (laut modernen Methoden) mit relevanten Zusatzinfos heranziehen, damit
ich etwas anfangen kann."*

„Laut modernen Methoden" hätte ich aus der Literatur abschreiben können —
Momentum, 52-Wochen-Hoch, Amihud, alles belegt. Das wäre aber eine Aussage über
**andere** Märkte und andere Zeiträume. Gemessen wurde deshalb an unseren
eigenen Reihen; die Literatur deutet das Ergebnis, sie ersetzt es nicht.
`messe_top_fakten.py`, **37 Symbole, 63.389 Zeilen, 20.494 auswertbare Anker.**

**Maßstab ist die Geometrie, die die App vorschlägt** — Stop 2,5 × ATR, Ziel
CRV 2,0, Fenster 10 Handelstage. Ein Merkmal trägt, wenn das oberste Fünftel
eine andere Trefferquote hat als das unterste. Basis über alle Anker: **23,5 %.**

**Zwei Hürden, beide nötig:** ein Bootstrap-Band ohne Null (Cluster über
**Symbole**, nicht über Anker) **und** eine monotone Ordnung. Zwölf Merkmale
sind zwölf Tests — bei zwölf Versuchen sieht eines zufällig gut aus, aber ein
Zickzack über die Fünftel hat keinen Mechanismus, sondern Rauschen.

### Das Ergebnis

| Merkmal | unterstes | oberstes | Spanne | monoton | Band |
|---|---|---|---|---|---|
| **Schwankungsbreite (Perzentil)** | 29,5 % | 17,8 % | **−11,7 pp** | 3/4 | −15,8 … −8,6 |
| **Rückgang seit 60-Tage-Hoch** | 18,9 % | 28,0 % | **+9,1 pp** | **4/4** | +0,9 … +15,0 |
| **Abstand zur 50-Tage-Linie** | 19,6 % | 27,7 % | +8,1 pp | 3/4 | +0,0 … +14,9 |
| Stand im Jahresbereich | 20,3 % | 27,8 % | +7,4 pp | 3/4 | −4,3 … +14,6 ✗ |
| **Trend 20 Tage** | 18,9 % | 25,6 % | +6,6 pp | 3/4 | +0,8 … +12,2 |
| **RSI 14** | 20,2 % | 26,4 % | +6,2 pp | **4/4** | +0,2 … +10,7 |
| Trend 60 Tage | 21,9 % | 26,9 % | +5,0 pp | 3/4 | −2,3 … +10,1 ✗ |
| **Volumen zum Mittel** | 22,5 % | 27,1 % | +4,5 pp | 3/4 | +1,4 … +7,4 |
| Illiquidität (Amihud) | 23,9 % | 20,6 % | −3,3 pp | 2/4 ✗ | −6,6 … −0,1 |
| Tagesspanne (Perzentil) | 20,9 % | 22,4 % | +1,5 pp | 2/4 ✗ | −8,1 … −1,9 ⚠ |
| Abstand zum Allzeithoch | 26,7 % | 27,7 % | +1,0 pp | 1/4 ✗ | −9,7 … +8,3 ✗ |
| Trend 250 Tage | 22,4 % | 23,1 % | +0,7 pp | 1/4 ✗ | −7,3 … +5,3 ✗ |

**Es sind nicht zehn, es sind sechs.** Zehn zu nennen hieße, vier
Rauschmerkmale mitzuschleppen — genau die Überhand, die vermieden werden soll.

### Und die sechs sind drei — mit Beleg

Rangkorrelation zwischen den sechs, Median über 37 Symbole:

| | Schwank. | Rückgang | 50-Tage | Trend 20 | RSI | Volumen |
|---|---|---|---|---|---|---|
| **Schwankungsbreite** | — | −0,23 | −0,22 | −0,21 | −0,19 | −0,01 |
| **Rückgang 60T-Hoch** | −0,23 | — | **0,89** | **0,71** | **0,59** | 0,10 |
| **Abstand 50-Tage-Linie** | −0,22 | 0,89 | — | **0,83** | **0,72** | 0,10 |
| **Trend 20 Tage** | −0,21 | 0,71 | 0,83 | — | **0,78** | 0,13 |
| **RSI 14** | −0,19 | 0,59 | 0,72 | 0,78 | — | 0,10 |
| **Volumen zum Mittel** | −0,01 | 0,10 | 0,10 | 0,13 | 0,10 | — |

Die vier Momentum-Maße hängen zu **0,59 bis 0,89** zusammen — **ein** Faktor,
nicht vier. Volumen ist mit 0,01 bis 0,13 praktisch unabhängig von allem.

| Familie | Richtung | stärkster Vertreter |
|---|---|---|
| **Schwankung** | niedrig ist besser | Schwankungsbreite im Perzentil, −11,7 pp |
| **Kurzfrist-Momentum** | steigend ist besser | Rückgang seit 60-Tage-Hoch, +9,1 pp (4/4) |
| **Volumen** | hoch ist besser | Volumen zum Mittel, +4,5 pp |

**Das ist genau die Unterscheidung, nach der der Prompt fragt** — „wie viele
deiner Belege sagen wirklich VERSCHIEDENE Dinge?". Vier Momentum-Belege sind
**ein** Faktor. Wer sie einzeln in den Faktenblock schreibt, lässt einen Aufbau
viermal so gut belegt aussehen, wie er ist.

### Zur Schwankungsbreite — Nutzereinwand, und er trägt

Nutzer: *„ein hoher Parameter ist ein Warnsignal, normal — dann wäre das
interessant."* Genau so ist es, und die Korrelationsmatrix belegt es:

Ich hatte zwei Zweifel notiert. **Beide sind ausgeräumt:**

1. *Ist es mechanisch?* Nein. Beide Barrieren stehen in ATR-Vielfachen, der
   ATR-Pegel kürzt sich heraus. Gemessen wird der ATR **relativ zur eigenen
   Vergangenheit** — also Ausdehnung gegen Beruhigung.
2. *Ist es Momentum von hinten?* Der Zusammenhang „Volatilität steigt, wenn
   Kurse fallen" (Leverage-Effekt, Black 1976) ist da — aber mit **−0,2**
   schwach. Der weitaus größte Teil des Signals ist eigenständig.

**Damit ist die Schwankungsbreite das stärkste EINZELNE Merkmal, das wir haben,
und zugleich das konventionellste.** Hohe Schwankung ist ein Warnsignal — die
Messung sagt, wie teuer es ist: 17,8 gegen 29,5 %.

### Was das mit der Sentiment-Messung zu tun hat

**Es ist dieselbe Messung.** Fear & Greed ist zur Hälfte aus dem Kurs abgeleitet;
„Gier" heißt „der Kurs ist zuletzt gestiegen". Der Sentiment-Befund aus 12.7
(+12,3 pp für extreme Gier) und der Momentum-Befund hier sind **ein** Befund.
Fear & Greed gehört damit in die **Momentum-Familie**, nicht daneben.

### Zwei Dinge, die auffallen

**1. Langfrist-Momentum trägt NICHT.** „Trend 250 Tage" landet mit +0,7 pp und
1/4 auf dem letzten Platz — und genau dieser Horizont ist es, für den Time
Series Momentum (Moskowitz/Ooi/Pedersen 2012) belegt ist. Der Unterschied liegt
im Maßstab: TSMOM misst **Renditen über Monate**, hier wird eine
**Barrierenauflösung über 10 Tage** gemessen. Das ist nicht dieselbe Frage; das
Ergebnis widerlegt die Literatur nicht, es sagt nur, dass ihr Befund für unsere
Geometrie nichts hergibt.

**2. „Tagesspanne" ist ein Methoden-Warnsignal, kein Fakt.** Ihre Spanne ist
**+1,5 pp, das Bootstrap-Band liegt aber vollständig im Negativen** (−8,1 …
−1,9). Punktschätzer und geclusterte Schätzung widersprechen sich — der
gepoolte Wert entsteht durch die **Zusammensetzung** der Symbole, nicht durch
das Merkmal. Wer nur die Spanne gelesen hätte, hätte das Vorzeichen verkehrt
übernommen. Raus.

## 12.9 Zusatzinfo — der Maßstab, und was ihn besteht

Nutzerpräzisierung: *„du hast recht mit Füllstoff — aber das wäre die Aufgabe:
welche Faktoren sind als Zusatzinfo sinnvoll, und ich kann diese nutzen, wenn
ich möchte — also kein Beiwerk ohne Sinn natürlich."*

**Der Maßstab folgt aus 12.8: eine Zusatzinfo ist sinnvoll, wenn sie eine
Dimension aufmacht, die die drei Familien NICHT abdecken.** Ein weiteres aus
dem Kurs abgeleitetes Maß tut das nicht — es wäre der fünfte Momentum-Vertreter
und würde einen Aufbau besser belegt aussehen lassen, als er ist. Vier
Kategorien bestehen den Maßstab:

| Kategorie | warum sie etwas Neues sagt |
|---|---|
| **Kosten** | ändert die Rechnung selbst, nicht die Einschätzung — und wird tatsächlich bezahlt |
| **Positionierung** | wer steht wie im Markt. Aus dem Kurs nicht ableitbar |
| **Fundamentaldaten** | Substanz statt Kursverlauf. Vollständig unabhängig |
| **vorausschauende Marktpreise** | was ANDERE für die Zukunft zahlen — die einzige Kategorie mit Blick nach vorn |

### Je Bereich, mit Begründung

| Bereich | Zusatzinfo | Kategorie | warum sie nutzt |
|---|---|---|---|
| **Krypto Hebel** | Funding in EUR/Tag | Kosten | bei 25 Tagen Haltedauer entscheidet sie über Gewinn oder Verlust (12.x) |
| | Liquidationspreis | Kosten/Risiko | sicherheitskritisch: greift die Zwangsliquidation vor dem eigenen Stop? |
| | Put-Skew (Optionsmarkt) | vorausschauend | der einzige Fakt im ganzen System, der nicht aus der Vergangenheit stammt |
| | Retail-Konsens (Binance) | Positionierung | steht die Mehrheit schon dort, wo wir hinwollen? Nur Krypto, nur Binance, Konten-Anteil |
| **Krypto beide** | BTC-Relativwert | Positionierung | trennt „der Coin steigt" von „der Markt steigt". **Achtung: teils Momentum** |
| | Fear & Greed (Bitcoin) | — | **gehört in die Momentum-Familie**, nicht daneben (12.8) |
| **Aktien** | Fundamentaldaten | Fundamental | unabhängig vom Kurs, klassisch belegt |
| | Insider-Trading | Positionierung | wer es am besten wissen kann, handelt sichtbar |
| | Short-Interest (FINRA) | Positionierung | Gegenposition, aus dem Kurs nicht ableitbar |
| | Analysten-Trend | Positionierung | schwächster der vier — als Info brauchbar, als Faktor nicht |
| **Rohstoffe** | Lagerbestände | Fundamental | Angebot und Nachfrage direkt |
| | Positionierung (COT) | Positionierung | wer hält welche Seite |
| **Themen-ETF** | Sektor-Rotation | — | **relative Stärke = Momentum**, kein eigener Faktor |
| **Hedge** | Portfolio-Exposure | — | keine Meinung, sondern die Rechengrundlage |

### Was den Maßstab NICHT besteht

| | warum raus |
|---|---|
| `regime_profil` | das Regime stand über 1.022 Fälle durchgehend auf „baer" — ein konstantes Feld trägt keine Information (R-T6) |
| `signal_stabilitaet` | misst den Verlauf der Konfidenz, und die ist gestrichen |
| `liquiditaetszonen` | Stufe 2 wurde bereits verworfen; die Zonen-Grafik zeigt nicht Einstieg/Stop/Ziel (12.6) |
| `trigger`, `systemguete` | interne Zustände. `systemguete` gehört inhaltlich in Abschnitt 4 (Einordnung), nicht in den Faktenblock |
| `disclaimers` | Rechtstext, kein Fakt |

---

# 13. Der „leere Fakten"-Befund — untersucht, und er war keiner (12.08.2026)

## 13.1 Was ich gemeldet hatte, und warum es falsch war

Beim Anschluss der Zusatzinfo fiel auf: **78 von 118 gespeicherten Spot-Signalen
tragen `facts_json = {}`.** Ich habe das als Defekt gemeldet — *„die Fakten, auf
denen die Empfehlung steht, fehlten bei zwei Dritteln"* — und dieselbe Aussage
stand seit dem Vormittag auch in `agent/signal_abbildung.py`, Punkt 4.

**Beides war falsch.** Nachgezählt nach Gate-Zustand:

| Aktion | Gate | Grund | leer |
|---|---|---|---|
| HALTEN | 0 | Preis veraltet oder nicht vorhanden | **72 / 72** |
| HALTEN | 0 | Stablecoin, keine Historie | 6 / 6 |
| HALTEN | **1** | — | **0 / 37** |
| KAUFEN, NACHKAUFEN, TAUSCHEN | 1 | — | **0 / 3** |

**Jedes Signal, das das Gate passiert hat, trägt seine Fakten — ausnahmslos.**
Die leeren sind Abweisungen *vor* der Analyse: dort gab es nie Fakten, weil die
Pipeline vorher anhält. `_fixed_signal(facts=None)` ist genau dafür gebaut.

**Die Lehre ist eine Zahl ohne ihre Schichtung.** „78 von 118" klingt nach
Befund und war eine Verwechslung von zwei Grundgesamtheiten. Der Fehler ist
derselbe wie beim CRV-Gate am 02.08. (Survivorship) — nur diesmal von mir und
nicht in einer Messung, sondern in einem Nebensatz. Als Prüfung gesichert:
`gate_passed=1` ⟹ `facts_json` nicht leer.

## 13.2 Was die Zahl WIRKLICH zeigt

72 Abweisungen wegen „Preis veraltet" verteilen sich auf **43 Symbole, darunter
BTC dreizehnmal**. Das trifft nicht Exoten, sondern alles. Der Grund ist eine
zeitliche Lücke, nicht ein Datenproblem einzelner Werte:

| | |
|---|---|
| Schwelle `PRICE_STALE_THRESHOLD_MINUTES` | **30 Minuten** (zwei Scheduler-Takte) |
| Letzter Preis im Cache | **2026-07-19 12:50** |
| Letzte „Preis veraltet"-Abweisung | **2026-07-21 16:04** |

Signale je Tag, nach Gate:

| Tag | durch | abgewiesen |
|---|---|---|
| 07.–15.07. | 40 | 36 |
| **21.07.** | **0** | **42** |

**Am 21.07. wurde jedes einzelne Asset abgewiesen**, weil der Preis-Cache seit
zwei Tagen nicht mehr geschrieben wurde. Das Gate hat dabei exakt richtig
gehandelt: es hat sich geweigert, auf veralteten Preisen zu analysieren, statt
ein Ergebnis zu liefern, das gut aussieht. Das ist *fail-loud* und der
erwünschte Zustand.

## 13.3 Die echte Lücke — und sie ist ein alter Bekannter

**Der Staleness-Watchdog deckt den Preis-Cache nicht ab.**
`scheduler/background.py` prüft im laufenden Betrieb zwei Dinge und stößt bei
beiden einen Nachhol-Lauf an:

| geprüft | Nachhol-Lauf | Meldung an den Nutzer |
|---|---|---|
| Kurs-**Historie** | ja, `refresh_history` | nein, nur `logger.info` |
| Kraken-**OHLC** | ja, `refresh_ohlc` | nein, nur `logger.info` |
| **Preis-Cache** | **nein** | **nein** |

Ausgefallen ist genau das, was nicht überwacht wird. Und weil ein Lauf ohne
Signale von einem Lauf ohne Gelegenheiten nicht zu unterscheiden ist, war der
21.07. für den Nutzer **unsichtbar**: keine Mail, kein Hinweis, nur Stille.

Das ist wörtlich das Muster aus `feedback_fail_soft_ist_fail_silent` — nur
eine Ebene höher: nicht ein Wert fällt still aus, sondern der ganze Lauf.

## 13.4 Vorschlag, nicht umgesetzt

Drei Punkte, in dieser Reihenfolge — **bewusst nicht mitgebaut**, weil sie das
Betriebsverhalten ändern und die Produktion für den Umbau steht:

1. **Preis-Cache in den Watchdog.** Dieselbe Mechanik wie für Historie und
   OHLC, dieselbe Schwelle. Der billigste der drei Punkte.
2. **Ein Lauf, der ALLES abweist, ist eine Meldung wert.** Nicht je Asset —
   einmal je Lauf, mit dem häufigsten Grund. Ein Signal-loser Lauf und ein
   ausgefallener Lauf sehen heute gleich aus.
3. **Abweisungen gehören nicht in die Signaltabelle.** 72 von 118 Zeilen sind
   keine Empfehlungen, sondern Datenausfälle. Solange sie dort stehen, ist
   jede Auszählung über `signals` erklärungsbedürftig — und genau daran bin
   ich heute selbst hängengeblieben. Der teuerste der drei Punkte, weil er
   Schema und Auswertungen berührt; deshalb zuletzt.

---

# 14. Abschluss-Checkliste: was NACH dem letzten Paket noch fehlt

**Nutzervorgabe 13.08.:** *„vergiss nicht am Ende der Umsetzung die
Dokumentationen und Zentraldokumente nachzutragen und ggf. auch die
Analysestandards nachzuziehen mit dem NB-Export-Skript."*

Steht hier und nicht im Gedächtnis, weil genau das am 12./13.08. schon einmal
liegengeblieben ist: vier laufend fortzuschreibende Dokumente standen seit dem
11.08. still, und es fiel erst auf, als der Nutzer danach fragte.

## 14.1 Zentraldokumente — wer ist wofür zuständig

Die Landkarte steht in `feedback_doku_struktur_zuordnung`. **Diese vier sind
bei JEDER Änderung mitzuziehen:**

| Datei | was hinein muss |
|---|---|
| `Regelwerk_Entscheidungslog.md` | Nachtrag je Fix und Messung, **Index-Zähler und Themenzeile mit** |
| `Regelwerksmanual.md` | der IST-Zustand, sobald sich eine Regel ändert |
| `Test_und_Verifikationsmethodik.md` | jedes neue Prüfskript in 2.13 |
| `Fakten_Entscheidungsmappe.md` | jeder neue oder entfernte Fakt |
| `Zielgroessen_und_Erfolgsmasse.md` | Änderungen an Messung oder Zielgrößen |

## 14.2 ~~Der Notebook-Export kennt den Umbau nicht~~ — ERLEDIGT 13.08. abends

**Der Bestandsaufnahme unten ist abgeholfen:** `_rollen_kette(conn)` exportiert
beide Tabellen, die acht `signals`-Spalten sind ergänzt, die Stufen der
Durchlässigkeit stehen **entfaltet** statt als JSON-Klumpen. Der Drift-Wächter
des Exports meldet gegen die Datenbank des Stufe-C-Laufs **keine offene Tabelle
und keine offene Spalte** mehr — und er war es auch, der die Liste unten
bestätigt hat, Punkt für Punkt. **Ein Wächter, der auf die eigenen Lücken zeigt,
ist mehr wert als eine Liste, die jemand pflegen muss.**

Die ursprüngliche Zählung bleibt als Beleg stehen:

`extract_notebook_diagnose.py` exportierte 18 Tabellen. **Vom gesamten
Umbau war keine einzige dabei:**

| | im Export |
|---|---|
| Tabelle `lagebilder` (Paket 6) | **nein** |
| Tabelle `gate_durchlaessigkeit` (12c) | **nein** |
| Spalte `quelle_kette` | **nein** |
| Spalte `rolle_begruendung` | **nein** |
| Spalte `umgeworfen_preis_eur` / `_bis` | **nein** |
| Spalte `unabhaengige_faktoren` | **nein** |

**Ohne diese Felder ist der Umbau von außen unsichtbar.** Jede spätere
Auswertung liefe auf den Altdaten und käme zu den Schlüssen der alten Kette —
genau die Falle, die `pruefe_export_vollcheck.py` unter Frage D beschreibt
(*„fehlen relevante Informationen, die eine spätere Auswertung kippen
würden?"*).

## 14.3 Die Analysestandards, die mitzuziehen sind

| Skript | was zu ergänzen ist |
|---|---|
| ~~`extract_notebook_diagnose.py`~~ | **ERLEDIGT 13.08.** — beide Tabellen, acht Spalten, Stufen entfaltet |
| ~~`pruefe_export_standard.py`~~ | **ERLEDIGT 13.08.** — **Punkt 16**: Durchlässigkeit je Stufe, plus drei Meldungen (Deadloop zurück · Einstiege tragen sich nicht · Faktorzahl nimmt nur zwei Werte an). Punkt 4 als *nur Altdaten* gekennzeichnet |
| ~~`pruefe_export_vollcheck.py`~~ | **ERLEDIGT 13.08.** — C6 (eine Zeile je Lauf: hinein → Urteil → Einstieg → gerechnet → trägt sich) und D6–D8 (kommen die sieben Felder mit, ist der Block da, hat jedes Kettensignal sein Lagebild) |

## 14.4 ~~Was in den Dokumenten noch fehlt~~ — NACHGEZOGEN 13.08. abends

Die Liste unten ist abgearbeitet. Was jetzt wo steht:

| | wo |
|---|---|
| 12b/12c/12d, 13, B1, die zwei Läufe | `Regelwerk_Entscheidungslog.md`, Nachtrag 13.08. abends + zwei Indexzeilen |
| IST-Zustand Betrieb, Gate, Hebel, Z1 | `Regelwerksmanual.md`, Nachtrag 13.08. abends |
| Was die Läufe über das **Messen** lehrten | `Test_und_Verifikationsmethodik.md` **2.21** |
| `--paket gesamt` / `B1` / `Export` | Methodik 2.13, Werkzeugkasten-Zeile |
| Die neun Einstiege mit ihrem Breakeven | `Zielgroessen_und_Erfolgsmasse.md`, Nachtrag 13.08. abends |
| Volumen vom Vortag statt Ausfall | `Fakten_Entscheidungsmappe.md` Kap. 14, als überholt markiert |

**Drei eigene Aussagen sind dabei als überholt gekennzeichnet worden**, nicht
gelöscht — wer eine Aussage streicht, nimmt der nächsten Lesung die Möglichkeit
zu sehen, dass sie einmal galt und warum sie fiel:

1. „Das Modell wählt **immer** den engsten erlaubten Stop" — aus n=2
   verallgemeinert, hält über n=10 nicht (Median 5,3 %)
2. „Am laufenden Tag entfällt das Volumen" — Absicht richtig, Folge falsch:
   eine von drei Familien fehlte damit in **jeder** Nachricht
3. „78 von 118 Signalen haben leere Fakten" — Zahl richtig, Deutung falsch
   (Kap. 13 dieses Plans)

**Auch die Analysestandards sind nachgezogen** (14.3) — und der Probelauf
gegen die Datenbank des Stufe-C-Laufs meldete sofort beides, was er melden
sollte: *„9 Einstiege, keiner trägt sich nach Kosten“* und *„Faktorzahl nimmt
über 20 Urteile nur [2, 3] an“*. **Eine Prüfung, die an echten Daten nichts
findet, ist keine bestandene Prüfung, sondern eine unerprobte.**

Die ursprüngliche Lückenliste, als Beleg:

- **12b/12c/12d und 13** standen nur im Umbauplan und in den Commit-Nachrichten
- **Die Gesamtprüfung** und ihre drei Funde waren nirgends in der Methodik
- **Die neuen Prüfskript-Pakete** fehlten im Werkzeugkasten
- **Der Ausstieg** war im Manual beschrieben, aber die Take-Profit-Nachlese und
  die Näherungswarnung kamen danach

## 14.5 Reihenfolge am Ende

1. **Erst der Betrieb** (B1) — solange nichts läuft, beschreibt jede Doku eine
   Vermutung
2. **Dann der Export**, sonst ist der erste Betriebslauf nicht auswertbar
3. **Dann die Zentraldokumente**, mit den echten Zahlen aus 1 und 2 statt mit
   den erwarteten
4. **Zuletzt die Analysestandards** — sie prüfen, was in 2 und 3 entstanden ist

**Diese Reihenfolge ist nicht beliebig.** Wer die Doku vor dem ersten Lauf
schreibt, dokumentiert eine Absicht und muss sie danach zweimal korrigieren.

**Stand 13.08. abends: alle vier erledigt.** Und die
Reihenfolge hat sich bezahlt gemacht — die Doku trägt jetzt die neun echten
Stopabstände, die zwei auseinandergehenden Läufe und den Befund zur Faktorzahl.
Vor dem Lauf hätte an all diesen Stellen eine Erwartung gestanden.

---

# 15. Vor dem Produktivgang zu behandeln (Stand 13.08.2026 abends)

Was hier steht, ist **nicht** die Rollout-Checkliste (die ist Kapitel 14),
sondern die Liste der offenen **inhaltlichen** Punkte. Sie stammt aus den
Stufen B und C — dem ersten und zweiten echten Lauf der neuen Kette.

## 15.1 Die Faktorzahl ist die Entscheidung noch einmal

Gemessen an 20 echten Urteilen:

| | |
|---|---|
| Werte insgesamt | nur **2 und 3** — nie 1, nie 4, nie 5 |
| Faktorzahl 3 | 11× → **9 davon Einstiege (82 %)** |
| Faktorzahl 2 | 9× → **0 Einstiege** |

Sie ist der Ersatz für die gestrichene Konfidenz (E3) — und hat **dasselbe
Problem in anderer Gestalt**: Wer die Zahl kennt, kennt die Entscheidung. Ein
Filter darauf wäre ein Filter auf die Entscheidung selbst.

**Aussichtsreichster Weg: sie deterministisch bilden.** Die Belege tragen
`richtung` und `gewicht`; Unabhängigkeit ließe sich über die drei gemessenen
Familien rechnen (Schwankung / Momentum / Volumen, Kap. 12.8) statt sie zu
erfragen. Dann wäre sie per Konstruktion unabhängig von der Aktion — und die
Sprachaufgabe bliebe, wo sie hingehört: bei der **Zuordnung** eines Belegs zu
einer Familie, nicht bei der Zählung.

## 15.2 Neun von zehn Einstiegen tragen sich nicht

Das ist kein Fehler, sondern das Ergebnis. Über beide Läufe:

| Stopabstand | erforderliche Trefferquote |
|---|---|
| 2,5 % | 73 % |
| 4,1 % | 57 % |
| 5,5 % | 52 % |
| 9,3 % | 52 % |
| **Basisrate** | **34 %** |

Selbst der beste Einstieg braucht 45 %. **Die Kette ist technisch fertig und
wirtschaftlich nicht.** Der Umbau hat den Deadloop beseitigt und damit
sichtbar gemacht, dass darunter ein Rechenproblem liegt — kein Modellproblem.

Die drei bekannten Auswege bleiben unverändert: **Drift statt Timing (S2, nie
gemessen) · Nachrichten · Kosten.**

## 15.3 Zwei Läufe, zwei Ergebnisse

Dieselben Daten, dasselbe Modell, zwei Minuten Abstand:

| | Einstiege | durch den Entscheider |
|---|---|---|
| Lauf 1 | 10 | 1 |
| Lauf 2 | 9 | 0 |

**Einzelläufe sind keine Messung.** Wer aus einem Lauf eine Zahl ableitet,
misst das Rauschen mit. Für jede Aussage über die Kette braucht es mehrere
Läufe oder mehr Anker — das gilt auch für alles in diesem Kapitel.

## 15.4 `signal_mail` hat keine Wartemechanik für Z.ai

Solange nur `probe` läuft, folgenlos. **Vor `scharf` muss sie gebaut sein** —
sonst kehrt der Fund vom 28.07. zurück (Krypto-Spot hatte gar keinen
Wartemechanismus, und die Mail ging ohne die Gegenprüfungszeilen raus, obwohl
das Urteil zum Versandzeitpunkt vorlag). Der Weg steht fest:
`_sende_signal_email_mit_zai_wartezeit()`.

## 15.5 Kleinere offene Punkte

- **Sechs von neun Begründungen enthalten keine Zahl.** Die Belege tragen
  Werte, der tragende Satz nicht. Ob das ein Mangel ist, ist offen.
- **Der Ankertag ist das jüngste Datum irgendeines Symbols.** Im Testlauf
  fielen 25 von 45 daran aus. Im Betrieb harmlos — aber wenn eine Quelle
  ausfällt, verschiebt sie den Anker für alle.
- **Der Hebel-Weg ist nie live gelaufen.** Paket 13 ist geprüft und im
  Trockenlauf gefahren, aber nie mit echtem Modell.


---

# 16. Betraege, Toepfe und die Pruefung der alten Kette (13.08.2026, abends)

**Nutzervorgabe, die das ausgeloest hat:** *„vergiss nicht ... ziehe jedenfalls
alle Punkte inkl. der offenen in der Doku und Zentraldokumenten nach damit
nichts verloren geht"* — nachdem beim Durchgehen auffiel, wie viel im System
**dokumentiert und nicht gebaut** ist.

## 16.1 Die Frage, die alles ausgelöst hat

Vor dem Produktivgang stand ein Nebenbefund: `risiko_eur=75.0` und
`betrag_wunsch_eur=500.0` sind in `rollen_lauf` fest verdrahtet. Die
Rückfrage des Nutzers — *„was ist das Problem genau mit meinem Betrag"* — hat
drei Ebenen freigelegt, die vorher niemand getrennt hatte.

### Die drei Deckel, die es wirklich gibt

| Deckel | begrenzt | Wert vorher | Ebene |
|---|---|---|---|
| `betrag_max_eur` | **eine einzelne Empfehlung** | 1.000 € | pro Trade |
| `betrag_min_eur` | Mindestgröße | 100 € | pro Trade |
| Topf **spot** | alle Spot-Positionen zusammen | **keiner** | pro Instrument |
| Topf **hebel** | alle Hebel-Positionen zusammen | 500 € | pro Instrument |
| — | **pro Asset** | **existiert nicht** | — |

**Einen Deckel je Asset hat das System nie gehabt.** Mein erster Vorschlag
(„1.000 € je Asset") hat eine Ebene erfunden — und hätte BTC mit über 2.500 €
Bestand jeden weiteren Kauf verboten. Der Nutzereinwand war berechtigt.

### Was der Nutzer wirklich meint, wenn er „2 bis 8 Prozent" sagt

*„glaube aber Kursverlust und nicht Kapitalverlust und nicht als Teil des
Gesamtportfolios"* — und damit ist die richtige Größe benannt:

| gemeint | im System | Stand |
|---|---|---|
| 2–8 % **Kursverlust** | der **Stopabstand** | wird längst gerechnet: Median 5,3 %, Spanne 2,5–9,3 % |
| 15–20 % **Verlust vom Einsatz** | der Kapitalverlust | stand als fixe 75 € da |

Die gemessenen Stopabstände decken sich mit seiner Einschätzung — das ist eine
unabhängige Bestätigung der Mechanik, kein Zufall.

Und die 15 % waren bereits implizit da: `500 € · 3× Hebel · 5 % Kursverlust =
75 € = 15 % vom Einsatz`.

## 16.2 Die Umparametrisierung: Anteil statt Betrag

```
Risiko in Euro  =  Einsatz × Verlustanteil
Hebel           =  Verlustanteil ÷ Kursverlust bis Stop
```

**Der Hebel hängt am ANTEIL, nicht am Einsatz.** Von 500 auf 1.000 € zu gehen
ändert ihn nicht (bei 5 % Stop bleibt es 3,0×) — es verdoppelt nur den
Euro-Verlust von 75 auf 150 €. Diese Entkopplung ist der eigentliche Gewinn:
Einsatz und Hebel sind getrennt einstellbar.

**Kein Depotwert, keine Prozente vom Gesamtportfolio** — dieselbe Linie wie bei
den Töpfen, und aus demselben Grund: bei Positionen, die 60 % im Minus stehen,
schrumpft ein Prozentsatz genau dann, wenn wieder gehandelt werden müsste.

## 16.3 Entschieden am 13.08.

| | Größe | Wert |
|---|---|---|
| Spot `akkumulation` | Tranche je Signal | **250 €** |
| Spot `einstieg` | Einmalkauf | **800 €** |
| Spot | Topf-Deckel | **keiner** (unverändert) |
| Hebel | Einsatz je Signal | **1.000 €** |
| Hebel | Topf gesamt | **3.000 €** (drei Positionen) |
| Hebel | Verlustanteil vom Einsatz | **15 %** |
| beide | **Cooldown** | aus der Konfiguration |

**Der Betrag hängt an der STRATEGIE, nicht am Instrument.** Die Kette
unterscheidet `einstieg` · `swing` · `akkumulation` seit Paket 2 — ein
Einmalkauf schiebt keine zweite Tranche nach und darf deshalb größer sein.

**Bewusst NICHT eingeführt:** ein Deckel je Asset und die Kern/Satellit-Rolle.
Der Nutzer will das vorerst nicht. Vorgemerkt für später ist **seine** Variante,
und sie ist besser als die von mir vorgeschlagene:

| Stufe | Deckel je Asset |
|---|---|
| BTC, ETH | keiner |
| Highcap | 2.500 € |
| Midcap | 1.500 € |
| Lowcap | 800 € |
| Smallcap | 500 € |

**Warum seine besser ist:** Kern/Satellit hätte eine Entscheidung je Asset
verlangt, 57-mal von Hand und bei jedem neuen wieder. Die
Marktkapitalisierungs-Staffel leitet sich aus einer Zahl ab, die schon da ist
(`price_cache.market_cap_usd`, 1.279 Zeilen, BTC 1.298 Mrd bis SUPRA 7 Mio).
**Null Pflege.**

## 16.4 Die Prüfung der alten Kette — was ihr fehlt und was doppelt ist

Auf Nutzerwunsch vollständig durchgegangen: **253 Konfigurationsschlüssel, 195
liest die alte Kette und die neue nicht.** Der Großteil sind eigene Teilsysteme
(Marktscan, Budget-Allocator, Screening). Was bleibt:

### A — sechs Werte werden an ZWEI Stellen gepflegt

| Konfiguration | Kopie in der neuen Kette | Wert |
|---|---|---|
| `sl_abstand_min_atr_faktor` | `GRENZEN["stop_min_atr"]` | 0,75 |
| `sl_abstand_eng_schwelle_relativ` | `GRENZEN["stop_min_relativ"]` | 0,025 |
| `hebel.max_hebel` | `GRENZEN["hebel_max"]` | 10 |
| `hebel.liquidations_sicherheitsmarge_relativ` | `GRENZEN["liquidations_marge"]` | 0,09 |
| `hebel.eigenkapital_richtwert_eur` | `toepfe.VORGABE_DECKEL_EUR` | 500 |
| `ausstieg_trailing_ausloese_r` | `ausstiegsregel.AUSLOESE_R` | 1,0 |

Alle sechs stimmen **heute** überein. Ändert jemand die Konfiguration, folgt die
neue Kette nicht — dieselbe Fehlerart wie die Kostensätze (12.08.), `gemini-3.5`
(12.08.) und `rolle_begruendung` (13.08.).

### B — acht Schutzfunktionen fehlen ganz

| | fehlt | Einstellungen |
|---|---|---|
| 1 | **Cooldown** | 8 Schlüssel: Hebel 3,5 h · Spot 15 h · Kern 8 h · ausgemustert 120 h · Re-Evaluierung 1 h · Position 3 h · Multi-Asset 8/72 h |
| 2 | **Cash-Reserve (RM-4)** | `cash_reserve_min_prozent: 10`, `cash_reserve_min_fixed_eur: 2000` |
| 3 | **Allokation je Asset (RM-2)** | 25 % · Kern 35 % · Small Cap 12 % |
| 4 | **Drawdown-Notbremse (Z-3)** | `ziele.max_drawdown_prozent: 15` |
| 5 | **Positionsgrößen-Dämpfer** | Gegenszenario → 50 % · technischer Konflikt → 60 % · CRV knapp → 60 % |
| 6 | **Hebel-Dämpfer** | Regime-Konflikt → 3× · Retail-Konsens → 3× · kontra-konservativ 0,6 · Funding-Rate |
| 7 | **Gleichzeitige Positionen** | `ziel_gleichzeitige_positionen: 5` |
| 8 | **Signal-Stabilität** | 4 Schlüssel |

**Punkt 3 ist die Asset-Deckel-Frage in anderer Gestalt:** die alte Kette HAT
einen Deckel je Asset, als Prozentsatz vom Portfolio. Die vom Nutzer
vorgemerkte Marktkapitalisierungs-Staffel ist derselbe Gedanke in absoluten
Euro — und passt damit besser zur Linie der neuen Kette.

### Die Klammer um 2, 3, 4 und 7

**Alle vier brauchen den Portfoliowert — und den kennt die neue Kette
absichtlich nicht.** `toepfe.py` sagt es selbst: *„Keine Funktion kennt den
Portfoliowert, also kann eine fehlende Bewertung nichts sperren."*

Dieselbe Datei führt `UEBERGREIFEND = ("cash_reserve",)` als **die eine** Regel,
die über Töpfe hinweg wirken soll. **Sie ist dokumentiert und nirgends gebaut.**
Genau das ist die Sorte Lücke, die der Nutzer meint.

**Der Ausweg ist der, den die Töpfe schon gehen:** dieselben Regeln in absoluten
Euro. „Mindestens 2.000 € Cash" statt „10 % des Portfolios" — die Kette bleibt
portfolioblind, der Schutz wirkt trotzdem.

## 16.5 Die Dämpfer — gemessen, nicht vermutet

Nutzerfrage: *„ich würde u.U. sogar andenken die vorhandenen Dämpfer vorerst
sauber stillzulegen"*.

**Was die Daten sagen**, über 118 Spot- und 5 Hebel-Signale:

```
signals       118 Zeilen,  4 mit risk_veto_reason -> 4x Konfidenz-Schwelle (R-5.10)
hebel_signals   5 Zeilen,  1 mit risk_veto_reason -> 1x CRV unter Minimum
```

**Alle vier Vetos stammen von der Regel, die längst gestrichen ist** (E3,
Konfidenz). Von den Dämpfern taucht keiner auf — **aber das beweist nichts**:
Dämpfer *verwerfen* nicht, sie *verkleinern*. Und:

> **Ihre Wirkung wird nirgends aufgezeichnet.** Es gibt keine Spalte, die
> festhält, dass eine Position halbiert wurde. Hätten sie gegriffen, könnten
> wir es nicht sehen.

Das ist derselbe Einwand, den dieses Projekt gegen jeden unsichtbaren Filter
erhebt — nur diesmal gegen die eigene alte Kette.

### KORREKTUR am selben Abend, beim Umsetzen

**Zwei Aussagen von mir waren falsch, und die zweite dreht die Empfehlung.**

**1. „Die Wirkung wird nirgends aufgezeichnet" — ungenau.** Die Spalten gibt es:
`hebel_signals.eigenkapital_deckel_hinweis` und `hebel_korrektur_hinweis`. Sie
sind nur **in allen Zeilen leer**. (`signals.position_size_note` ist zu 40 von
118 gefüllt, enthält aber Fließtext des Modells, nicht den Vermerk des
Dämpfers.) Der Platz ist also da und wird nicht benutzt — die Reparatur ist
Füllen, nicht Anlegen.

**2. „Nicht blind stilllegen, sondern mit Zähler" — zu pauschal.** Im Code steht
eine Messung, die ich vorher nicht gelesen hatte. Zur stufenlosen CRV-Abstufung
bei Spot, an **298 Spot-Signalen**:

| | vorher | nachher |
|---|---|---|
| SQN | +0,63 | **+1,36** |
| Summe | +9,8 R | **+23,1 R** |
| Rückschlag | 36,3 R | **27,1 R** |

**Besseres Ergebnis bei kleinerem Risiko.** Dieser Dämpfer ist gemessen und er
wirkt. Ihn stillzulegen hieße, eine belegte Verbesserung wegzuwerfen.

### Die Empfehlung, die daraus folgt

**Nur stilllegen, was auf einer Größe beruht, die wir als wertlos GEMESSEN
haben** — alles andere behalten und mit einem Zähler versehen:

| Dämpfer | beruht auf | gemessen | Empfehlung |
|---|---|---|---|
| Konfidenz-Skalierung | Konfidenz | r = +0,073, faktisch konstant | **stilllegen** |
| Regime-Konflikt → 3× | Regime | über 1.022 Fälle konstant „baer" | **stilllegen** |
| CRV-Spreizung / CRV knapp | CRV | SQN +0,63 → +1,36 | **behalten** |
| Gegenszenario → 50 % | Gegenszenario-Wahrscheinlichkeit | ungemessen | behalten **+ Zähler** |
| technischer Konflikt → 60 % | Konfluenz | ungemessen | behalten **+ Zähler** |
| Retail-Konsens → 3× | Retail-Positionierung | ungemessen | behalten **+ Zähler** |
| kontra-konservativ 0,6 | AZ-7-Kontra | ungemessen | behalten **+ Zähler** |

Der Zähler schreibt in die **vorhandenen leeren Spalten**. Nach einigen Wochen
ist für jeden ungemessenen Dämpfer entschieden, ob er etwas taugt — statt es
heute in die eine oder andere Richtung zu behaupten.

**Wichtig dabei:** die alte Kette bedient weiterhin **Aktien, Rohstoffe,
Themen-ETF und Hedge**. Ein Abschalten ist dort eine echte Verhaltensänderung
an einem laufenden System, nicht eine Aufräumarbeit.

## 16.6 Was offen bleibt — das Register

Damit nichts verlorengeht, ausdrücklich auf Nutzerwunsch:

| | offener Punkt | woher |
|---|---|---|
| O-1 | **Cash-Reserve absolut** bauen (RM-4) | 16.4 B-2, entschieden als eigener Schritt |
| O-2 | **Dämpfer stilllegen mit Zähler** | 16.5, Empfehlung liegt vor |
| O-3 | **Marktkapitalisierungs-Staffel** je Asset | 16.3, vom Nutzer vorgemerkt |
| O-4 | **Portfoliowert: ja oder nein?** — davon hängen RM-2, Z-3 und `ziel_gleichzeitige_positionen` ab | 16.4, Klammer |
| O-5 | **Spot-Mail nennt einen „Stop", den es nicht gibt** — bei Spot ohne Stop-Order ist der Widerlegungspreis eine Beobachtungsmarke | 16.1 |
| O-6 | **`belegt_eur=0.0`** fest verdrahtet — der Topf meldet sich immer als leer | 16.1 |
| O-7 | **Faktorzahl-Frage anders stellen** („welcher Beleg würde allein genügen") | Kap. 15.1 |
| O-8 | **Konsistenzprüfung von Z.ai auf Rauschen messen** — nur die Richtung ist gemessen (30 %) | Kap. 15 |
| O-9 | **Signal-Stabilität** (4 Konfigurationsschlüssel) — nach dem 30-%-Rauschbefund interessant | 16.4 B-8 |
| O-10 | **Paket 14 Hedge, 15 Rollout, 16 Kategorie-Synthese** | Paketliste |

**O-4 ist die Weiche.** Solange sie offen ist, bleiben vier Schutzregeln
unbaubar — und zwar nicht aus Nachlässigkeit, sondern weil die Entscheidung
noch aussteht.


---

# 17. Die Multi-Asset-Schiene — geplant, bevor gebaut wird (13.08.2026)

**Nutzerfrage:** *„sind die weiteren Assets — Aktien, ETF, Rohstoffe, etc. im
Plan bzw. bereits zum Teil im Umbau berücksichtigt?"* — und der Auftrag,
**vorher die gesamte Kette durchzuprüfen**, ob etwas vergessen wurde.

## 17.1 Der Befund: mehr ist fertig als erwartet

Stufe für Stufe am Code geprüft, nicht am Plan:

| Stufe | Stand | Beleg |
|---|---|---|
| Auftrag | **klassenfrei** | Instrumente und Strategien kennen keine Assetklasse |
| Lagebild (Rolle A) | **fertig** | `KLASSEN = ("krypto", "aktien", "rohstoffe")` |
| Faktenblock, Zusatz | **fertig** | sechs Bereiche: aktien · hedge · krypto_hebel · krypto_spot · rohstoffe · themen_etf |
| Faktenblock, Kern | **klassenfrei** | Schwankung/Momentum/Volumen aus der reinen Kursreihe |
| Quellen-Abbildung | **fertig** | 10 Pfade inkl. KGV, COT-Netto, Insider-Saldo, Analysten-Trend |
| Kostenmodell | **fertig** | `krypto` · `boerse_fix_eur` · `boerse_spread` |
| Töpfe | **klassenfrei** | nach **Zweck** getrennt, nicht nach Klasse — das trägt jede Klasse |
| Beträge | nur spot/hebel/absicherung | je Instrument, nicht je Klasse |
| Cooldown | nur spot/hebel/absicherung | dito |

**Die Kette ist von Anfang an klassenfähig gebaut worden.** Was fehlt, ist die
Verdrahtung, nicht das Material.

## 17.2 Was konkret fehlt — drei Zeilen und zwei Entscheidungen

**Fest verdrahtet auf Krypto sind genau zwei Stellen:**

```
rollen_lauf.py:425   bereich=f"krypto_{instrument}"
rollen_lauf.py:428   block = FB.baue(f"krypto_{instrument}", ...)
```

**Nicht übergeben wird, obwohl das Ziel es kann:**

| Größe | Ziel | Folge heute |
|---|---|---|
| `assetklasse` | `rollen_eingabe.baue_befund_eingabe` | der Faktentext nennt die Klasse nicht |
| `klasse` | `trefferbilanz.kosten_r_aus_stop` | **siehe 17.3** |

**Die Kursreihen sind kein Problem:** `rollen_lauf` bekommt `reihen` vom
Aufrufer und ist selbst quellenfrei. Eine andere Klasse heißt: ein anderer
Lader, kein anderer Lauf.

## 17.3 Ein latenter Defekt, gefunden bei dieser Prüfung

`kosten_r_aus_stop()` hat die Vorgabe `klasse="krypto"` — und `rollen_lauf`
übergibt nichts. **Solange nur Krypto läuft, stimmt das zufällig.** Sobald eine
Aktie durch dieselbe Kette geht, rechnet der Entscheider mit
**Krypto-Gebühren** (1,5 % je Seite) statt mit Börsengebühren (1 € fix +
0,25 % Spread) — und der Breakeven wäre grob falsch, ohne dass irgendetwas
meldet.

**Das ist kein Fehler von heute, sondern eine Zeitbombe für den Tag der
Erweiterung.** Sie gehört vor die erste fremde Assetklasse, nicht danach.

## 17.4 Reihenfolge

1. **`klasse` und `assetklasse` durchreichen** — behebt 17.3, bevor es zum
   Fehler werden kann. Klein und sofort.
2. **`bereich` aus der Assetklasse bilden** statt aus `"krypto_"` — dann greift
   die Zusatzinfo je Bereich, die es schon gibt.
3. **Beträge und Cooldown je Klasse**, falls gewünscht — heute hängen beide am
   Instrument. Für Aktien wären andere Werte plausibel; das ist eine
   Nutzerentscheidung, keine Verdrahtung.
4. **Je Klasse ein Lader für die Kursreihen** — der einzige echte Neubau, und
   er liegt außerhalb der Kette.

**Nicht enthalten und bewusst offen:** ob die alte Kette für Aktien, Rohstoffe,
Themen-ETF und Hedge **parallel weiterläuft** oder abgelöst wird. Solange sie
läuft, gilt jede Änderung an ihren Dämpfern (Kap. 16.5) auch für diese vier.


---

# 18. Die Kostensteuerung — und was drei Prüfungen dabei fanden (14.08.2026)

**Der Anlass war eine Zahl.** Nach dem Schnitt auf `scharf` fiel auf, dass die
Kette im 15-Minuten-Takt einen vollen Durchgang über alle Symbole macht:

```
96 Läufe × (1 Lagebild + 41 Trader) × 2 Instrumente + Z.ai  ≈  11.900 Aufrufe/Tag
Gemini-Grenze                                                      500 Aufrufe/Tag
```

Nach knapp zwei Stunden wäre der Tag tot gewesen. **Meine erste Schätzung lautete
5.000 — sie war falsch, weil ich Z.ai vergessen hatte** (6.912 davon).

## 18.1 Der architektonische Unterschied, der das erklärt

> **Die alte Kette filtert VOR dem LLM-Aufruf. Die neue filtert DANACH.**

| | alt | neu |
|---|---|---|
| Was einen Aufruf auslöst | eine erkannte Konstellation | die Fälligkeit im Cooldown |
| Wer sagt „hier ist etwas" | deterministisches Screening | das Modell |
| Belegt durch Zahlen | 46 Kandidaten → **3** LLM-Aufrufe | 25 Aufrufe → 9 Einstiege |

**Und das war Absicht, nicht Nachlässigkeit.** Genau die Vorfilter der alten
Kette haben den Deadloop erzeugt (98,2 % HALTEN). Der Aufbau war für
**Messläufe** richtig — für einen 15-Minuten-Takt ist er zu teuer.

**Nutzerfrage dazu, die den Kern traf:** *„ich dachte das GATE ist bereits der
Filter, der als erstes entscheidet, ob ein Trade bis zur Bewertung kommt."*

Nachgesehen: von acht Gate-Stufen liegen drei vor dem Aufruf, und die filtern
kaum. Die Stufe, an der 16 von 25 ausscheiden — `aktion` — liegt **danach**.
**Das Gate ist ein Messinstrument, kein Türsteher.** Es wurde nie verschoben; ein
erstes Gate hat diese Kette nie gehabt.

## 18.2 Die drei Arten von „nicht jetzt" — die Unterscheidung, die gefehlt hat

| | Frage | Beispiel | Deadloop-Risiko |
|---|---|---|---|
| **Kostenfilter** | *wann* schaue ich hin? | Cooldown, Budget, Reihenfolge | **keins** |
| **Nutzerentscheidung** | *will ich* das handeln? | DCA-/Hebel-Schalter je Asset | **keins** |
| **Qualitätsfilter** | *ob* es ein Signal ist | die alten Vorgates | **das war der Deadloop** |

Nur der dritte ist gefährlich. Die ersten beiden verschieben oder setzen um —
**kein Asset fällt dauerhaft heraus.**

## 18.3 Was gebaut wurde

| | | Wirkung |
|---|---|---|
| **1** | Cooldown **vor** den Trader-Aufruf | 4.800 → 66 Spot-Aufrufe/Tag |
| **2** | Lagebild 3 h wiederverwendet | 192 → 48 |
| **3** | Warteschlange, **fünf** Stufen | Reihenfolge, kein Ausschluss |
| **4** | Tagesbudget + Rückfallkette 3.1 → 3.5 → OpenRouter | harte Grenze, 10 % Reserve |
| **5** | Modell auf der Signalzeile | Voraussetzung für 4 |
| **6** | NICHTS_TUN messbar mitgeschrieben | zweiter Messarm, **null Zusatzkosten** |

**Ergebnis: 319 Aufrufe am Tag über alle fünf Assetklassen — 64 % des ersten
Topfes, 16 % aller drei.**

### Zur Reihenfolge, in zwei Nutzereinwänden geschärft

*„in der Praxis ist eine bestehende Position bzw. bestimmte Assets wichtiger"* —
und danach *„Bei Hebel soll der hebel bestand ganz oben sein."*

Der zweite ist die scharfe Fassung: es genügt nicht, beide Bestände zu kennen.
Die Regel heißt **„das eigene Instrument zuerst"** — eine offene Hebelposition
hat einen Liquidationspreis, sie kann verschwinden; dasselbe Symbol im Spot
steht einfach weiter da.

### Zur Rückfallkette: der Grund ist Messbarkeit, nicht Durchsatz

Ein Anbieterwechsel mischt **zwei Urteilsverteilungen in dieselbe
Trefferbilanz**. Der Mistral-Verhaltensbruch vom 31.07. zeigte 55,4 gegen
68,0 % bei **bitgleichem** Prompt. Deshalb das Geschwistermodell derselben
Familie zuerst und der Fremdanbieter zuletzt — und deshalb ist Punkt 5 die
Voraussetzung.

## 18.4 Was die Gesamtprüfung der Kette ergab

| Prüfung | Ergebnis |
|---|---|
| Hat jedes der **22** neuen Module einen Betriebsaufrufer? | **ja, ausnahmslos** |
| Ruft der Scheduler die Kette — beide Instrumente, Betriebsart aus der Konfiguration, alle Töpfe? | **ja** |
| Liest jemand die neuen Einstellungen? | **ja** |
| Ehrt die Kette die **Asset-Schalter der GUI**? | **NEIN — drei Lücken** |

## 18.5 Die Querprüfung GUI / Einstellungen / Assets — drei überstimmte Entscheidungen

```
asset_dca_settings.dca_erlaubt                    alte Kette: ja   neue: NEIN
asset_hebel_settings.hebel_pruefung_erlaubt       alte Kette: ja   neue: NEIN
asset_bitpanda_override.bitpanda_gelistet_override alte Kette: ja  neue: NEIN
```

**Die Kette erzeugte Signale, wo der Nutzer ausdrücklich keine wollte.** Seine
Vorgabe steht wörtlich im alten Code (12.08.):

> *„ich möchte selbst entscheiden, bei welchen Assets die Strategie angewendet
> wird — überall möglich, aber nur dort Signale erzeugen, wo ich das selektiv
> möchte."*

Das ist schlimmer als ein fehlendes Merkmal — es ist eine **überstimmte
Entscheidung**. Behoben in `agent/asset_schalter.py`, geprüft **vor** dem
Modellaufruf, **fail-open**: ein Lesefehler darf nicht dazu führen, dass die
Kette stumm nichts mehr tut.

## 18.6 Die Remote-Seite — geprüft, noch nicht umgestellt

`remote/server.py` (1.048 Zeilen) und `remote/status.py` (1.092):

| kennt | |
|---|---|
| `quelle_kette` · `lagebild` · `gate_durchlaessigkeit` · `unabhaengige_faktoren` · `zai_stimmen` | **nein** |
| `confidence_pct` | **im Code ja — aber die Karte wird nirgends gerendert** |

**Korrektur 14.08. nach dem ersten Startlog:** ich hatte hier geschrieben, die
Remote-Ansicht *zeige* eine leere Konfidenzspalte. **Sie zeigt sie nicht.**
`_get_konfidenz_kalibrierung` ist definiert und wird **nirgends aufgerufen**,
`KONFIDENZ_BUCKET_ORDER` in `server.py` ebenso — die ganze Karte ist toter
Code. R-1 bleibt als Kennzeichnung im Quelltext stehen, damit sie jemand
vorfindet, der sie eines Tages verdrahtet; dringend war sie nicht.

**Dafür war etwas anderes dringend, und es stand nicht in meinem Plan:**

**Die Remote-Ansicht würde die neuen Signale anzeigen, aber ohne alles, was sie
ausmacht — und mit einer Konfidenzspalte, die strukturell leer bleibt.** Dazu
eine Kalibrierungskarte, die eine Frage beantwortet, die es nicht mehr gibt
(*„hält confidence_pct, was es verspricht?"*).

> **`/api/status` starb bei JEDEM Abruf.**
> `TypeError: RemoteStatus.__init__() got an unexpected keyword argument
> 'selbst_gewaehltes_halten_performance_nach_grund'` — der Konstruktoraufruf
> übergab das Feld, die Klasse kannte es nicht, seit Commit `598753c`. Die
> Fernsteuerung war **vollständig tot**, und zwar unbemerkt.

**Warum es durch alle Netze fiel:** `_safe()` fängt Fehler der einzelnen
*Karten* ab, nicht den Aufbau des Ergebnisobjekts. Die Laufzeitwache misst die
*Dauer*, nicht das Gelingen. Und es gab keinen Testlauf, der den Status einmal
wirklich **baut** — genau den gibt es jetzt.

### Plan für die Remote-Umstellung

| | Schritt |
|---|---|
| **R-1** | Die Konfidenz-Karte als **nur für die alte Kette** kennzeichnen — sie ist nicht falsch, nur nicht mehr zuständig |
| **R-2** | Signalliste um `quelle_kette`, `modell`, `unabhaengige_faktoren` ergänzen |
| **R-3** | Eine Karte **Durchlässigkeit** — wo verliert die Kette? Der aussagekräftigste neue Wert |
| **R-4** | Z.ai-Stimmen anzeigen: „(2 von 3, uneinheitlich)" statt eines nackten Urteils |
| **R-5** | Trefferbilanz-Stand sichtbar machen: wie viele Zellen sind belastbar? |

**R-1 ist der einzige dringende Punkt** — eine leere Spalte, die früher etwas
bedeutete, liest sich wie ein Defekt. Der Rest ist Komfort und kann nach dem
Produktivgang kommen.

## 18.7 Was offen bleibt

| | | |
|---|---|---|
| **O-11** | Remote-Umstellung R-1 bis R-5 | R-1 vor dem Produktivgang |
| **O-12** | Der Kontra-Verdacht im Hebel-Screening | alle drei LLM-Aufrufe gingen an `trendfolge`; der beste Kontra-Kandidat lag bei 69,1, der schwächste trendfolge bei 72,1. Bei n=46 ein Verdacht, kein Befund |
| **O-13** | Der Screening-Score ist **nie gegen Ergebnisse gemessen** | er entscheidet heute nur die Reihenfolge — ein kalibrierter Vorfilter wäre erst möglich, wenn die Kette aufgelöste Signale liefert |
| **O-14** | Stufe „vorgemerkt" der Warteschlange ist leer | es gibt keinen Ort in der Datenbank, an dem eine Vormerkung stünde |


---

## Kapitel 19 — Der Multi-Asset-Umlauf und die drei Entscheidungen (14.08.2026)

### 19.1 Der Umlauf ersetzt die feste Liste

Bis heute stand im Job `for instrument in ("spot", "hebel")`. Aktien,
Rohstoffe, Themen-ETF und die Absicherung waren damit von der neuen Kette **gar
nicht erreichbar** — der glatte Schnitt hätte sie stillgelegt, ohne sie zu
ersetzen. Was ein Umlauf ist, steht jetzt an **einer** Stelle,
`assetklassen.laeufe()`:

| Gruppe | Instrument | Symbole | Tranche | Cooldown |
|---|---|---|---|---|
| aktien | spot | 2 | 400 € | 24 h |
| hedge | absicherung | 2 | 500 € | 24 h |
| krypto | spot | 43 | 250 € | 15 h |
| krypto | hebel | 43 | 1.000 € | 3,5 h |
| rohstoffe | spot | 4 | 400 € | 24 h |
| themen_etf | spot | 5 | 400 € | 24 h |

**Warum börsengehandelte Werte andere Zahlen bekommen:** an der Börse kostet
1 € fix je Seite — bei 250 € sind das 0,8 % allein an Fixkosten, während sich
der Betrag bei Krypto herauskürzt. Und Krypto handelt rund um die Uhr, eine
Aktie nicht: ein 15-Stunden-Takt fragt dort mehrfach am selben Handelstag
dasselbe.

**24 h ist kein gemessener Wert**, sondern Handelstagslogik. Der Einmalkauf
bleibt bei 800 €, weil der Nutzer Beträge für Krypto genannt hat und nicht für
Aktien — eine erfundene Zahl wäre schlimmer als die übernommene.

### 19.2 Trockenlauf über alle sechs Gruppen — und der Nagel darin

Ohne einen einzigen Modellaufruf, und er findet, was ein echter Lauf teuer
fände: `hedge` 0 von 2 Symbolen mit Kursreihe, `rohstoffe` 0 von 4, `krypto`
32 von 43, `themen_etf` 4 von 5.

**Der Grund ist wichtiger als der Befund.** Hedge- und Rohstoff-Reihen werden
zur **Laufzeit rekonstruiert**, und die Funktion dafür liegt in den *alten*
Pipelines. Auf dem Desktop fehlen sie, weil die Produktion hier am 21.07.
stehenblieb — vor der Rekonstruktion. Auf dem Notebook existieren sie (Startlog
14.08.: „Hedge-Reihe für 3QSS rekonstruiert: 520 Punkte").

> ⚠️ **NAGEL FÜR DEN SCHNITT:** der OHLC-Refresh ruft
> `_ensure_ohlc_backfilled` **direkt aus den Pipeline-Modulen**, unabhängig von
> deren Signalerzeugung. Der Schnitt darf die **Signalerzeugung** stilllegen —
> **diese Funktion nicht.** Wer die Pipelines eines Tages löscht, nimmt den
> börsengehandelten Werten ihre Kursreihen mit, und zwar lautlos.

### 19.3 Z.ai — die Annahme war falsch herum

Die Sorge war „drei Stimmen nacheinander kosten Zeit". Der Engpass war das
Gegenteil: `rollen_lauf` startet einen Faden **je Signal**, jeder ruft Z.ai auf.
Bei zehn Signalen liefen zehn gleichzeitige Aufrufe gegen ein Limit von zwei —
die Parallelität war längst da, nur unbegrenzt.

`zweite_meinung.MAX_GLEICHZEITIG = 2`, als Semaphore **am Anbieter**, nicht am
Lauf: dort gilt sie auch für jeden künftigen Aufrufer, der von der Grenze
nichts weiß. Gemessen: 12 Fäden, Spitze 2. Wer binnen 180 s keinen Platz
bekommt, wird als *übersprungen* gebucht — ein Ausfall darf nicht aussehen wie
eine bestandene Prüfung.

### 19.4 Trefferbilanz: nach Instrument getrennt, nach Modell nicht

Spot und Hebel lagen in denselben Zellen. Das ist ein Fehler, keine
Ungenauigkeit: ein Hebel-Trade hat einen Stop und löst binnen Stunden auf, eine
Spot-Tranche hat keinen und läuft über Wochen. **Der Beleg liegt im Projekt** —
die CRV-Abstufung hilft bei Spot (SQN +0,63 → +1,36) und schadet beim Hebel
(+3,25 → +1,25). Eine gemeinsame Bilanz hätte das nie zeigen können.

*Bekannte Grenze:* Spot und Absicherung sind über `hebel IS NULL` **nicht**
trennbar. Eine Instrumentspalte wäre eine zweite Wahrheit neben einer, die
schon eindeutig ist.

**Nach Modell wird nicht gespalten**, und der Einwand des Nutzers ist der
Grund: *„angenommen 3.5 weicht ab, dann haben wir diese Abweichung in ALLEN
Hebeln"*. Genau deshalb hilft Spalten nicht — es würde die Zellen vierteln, und
schlimmer: fällt der erste Topf aus, landet das Urteil in einer frischen,
leeren Zelle. Der Entscheider stünde ohne Bilanz da, genau wenn etwas
schiefgeht. Stattdessen `modell_mischung()` — die Spalte steht ohnehin auf jeder
Zeile, jetzt ist sie ablesbar.

### 19.5 Groq zurück in der Kette — als vierter Topf

`gemini-3.1-flash-lite` → `gemini-3.5-flash-lite` → OpenRouter → **Groq**.

Der Ausschlussgrund vom 26.07. ist entfallen: „413 Payload Too Large" bei einem
Prompt von 34.611 Zeichen. Der Rollen-Umbau hat ihn auf 3.183 gekürzt
(750–900 Token je Aufruf). **Nicht Groq hat sich geändert, sondern wir.** Die
Abkündigung vom 14.08. betrifft `llama-3.1-8b-instant`; wir fahren
`llama-3.3-70b-versatile`.

> ⚠️ **80 ist eine Annahme, keine abgelesene Zahl.** Die bindende
> Free-Tier-Grenze ist vermutlich nicht die Anfragenzahl, sondern die **Token
> je Tag** — bei ~1.200 Token je Aufruf wären 100.000 TPD rund 83 Aufrufe. Vor
> ernsthafter Nutzung an der Quelle nachlesen.

### 19.6 Offene Punkte aus diesem Kapitel

| Nr. | Punkt |
|---|---|
| **O-15** | Groq-Tageslimit an der Quelle prüfen (Anfragen *oder* Token) |
| **O-16** | Spot und Absicherung in der Trefferbilanz nicht trennbar — erst relevant, wenn Hedge-Signale auflösen |
| **O-17** | Einmalkauf-Betrag für börsengehandelte Werte ist übernommen (800 €), nicht entschieden |
| **O-18** | `_ensure_ohlc_backfilled` darf beim Aufräumen der alten Pipelines nicht mitgelöscht werden |
