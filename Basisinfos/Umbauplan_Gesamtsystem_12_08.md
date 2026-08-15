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


---

## Kapitel 20 — Die erste Produktionsbewertung (14.08.2026)

Neun Kaufmails ab 09:05, dann gestoppt. **Die Kritik war in jedem Punkt
berechtigt**, und zwei Punkte waren schlimmer als die Beobachtung nahelegte.

### 20.1 Der Lesepfad war seit der Migration tot

`SPALTEN_SIGNAL` legte fünfzehn Spalten an `signals` an, `models.Signal` wuchs
nicht mit, `_row_to_signal()` baut die Klasse aus `SELECT *`.

**Es brach nicht beim ersten Rollen-Signal, sondern beim Anlegen der Spalten.**
`SELECT *` liefert alle Spalten, egal was in der Zeile steht — also war *jedes*
Signal unlesbar, auch jedes alte. Dreizehn Aufrufer von `get_latest_signal`.

*Erledigt.* Die Klasse ist nachgezogen; eine Prüfung vergleicht künftig
Tabellenspalten gegen Klassenfelder für `signals` **und** `hebel_signals`.

### 20.2 KAUFEN ohne Einstieg — der Formatierer

```
Einstiegszone   0 bis 0 EUR
Stop            0 EUR  (5,5 % - ...)
Take-Profit     0 bis 0 EUR
```

PLUME steht bei 0,0119 EUR. Die Rechnung war richtig, die Darstellung hat sie
vernichtet: `_eur()` hatte eine feste Stellenzahl. **In derselben Mail** stand
korrekt „Widerstand bei 0.0119 EUR" — die Zahlen des Modells laufen nicht durch
diesen Formatierer. Zwei Zahlenwege, einer davon kaputt.

*Erledigt.* `signal_mail.preis()` rechnet in signifikanten Stellen. Betroffen
war jeder Wert unter einem Euro, nicht nur Krypto.

### 20.3 Zwei Stop-Abstände für denselben Stop

| Block | Zahl | Bezugspunkt |
|---|---|---|
| 2. DIE RECHNUNG | 5,5 % | die Einstiegszone |
| 4. EINORDNUNG | 11,2 % | der aktuelle Kurs |

Beide für sich richtig — die Zone lag 6 % unter dem Kurs. Für den Leser ist es
der schlimmere Widerspruch: er schätzt sein Risiko doppelt so hoch ein und
sieht nicht, warum. *Erledigt* — die Einordnung rechnet gegen den geplanten
Einstieg.

### 20.4 Warum die Mail generisch wirkt — O-19 bis O-24

`baue_mail` kann sechzehn Eingaben darstellen. Die Rollen-Kette übergibt elf.
**Fünf Blöcke sind an nichts angeschlossen:**

| Nr. | Block | Was fehlt dadurch |
|---|---|---|
| **O-19** | `bestand` | „Habe ich das überhaupt?" — nach Nutzervorgabe 12.08. die **erste** Zeile |
| **O-20** | `marken` | Widerstand/Unterstützung **in Euro**, ebenfalls Vorgabe 12.08. |
| **O-21** | `lage_fakten` | das Lagebild, das Rolle A einmal je Lauf rechnet, erreicht die Mail nie |
| **O-22** | `ausstieg` | keine Ausstiegsführung für gehaltene Positionen |
| **O-23** | `coin_fakten` | Coin-Ebene |
| **O-24** | Charts | die alte Kette hängte zwei Inline-Grafiken an (Liquiditätszonen, Signal-Stabilität); `baue_versand()` reicht nur `(betreff, text)` durch |

Die Vorlage ist nicht generisch — sie wird nur zu einem Drittel gefüttert.

### 20.5 Was **kein** Defekt ist, aber so aussieht

- **„Trägt sich NICHT: 34 erreichen das Ziel, nötig wären 42"** und trotzdem
  KAUFEN. Das ist „zählen, nicht verwerfen" — der Entscheider ist ein
  Messinstrument, kein Türsteher. Es ist die bekannte Arithmetik, kein neuer
  Fehler. **Aber:** wenn neun von neun Mails das sagen, ist die Frage nicht
  mehr, ob die Anzeige stimmt, sondern ob sich das Filtern lohnt.
- **Z.ai meldet „widerspruch"** und die Mail geht raus — kein deterministischer
  Override des LLM-Werturteils, so entschieden.
- **160 EUR statt 800** — die CRV-Abstufung greift bei CRV 2,0 auf ein Fünftel.
  Gemessen und gewollt; die Nebenwirkung steht in derselben Mail („Die Gebühren
  fressen 27 % Ihres Risikos auf"). **O-26:** prüfen, ob Abstufung und
  Kostenklasse zusammen einen Betrag erzeugen, der sich nie tragen kann.

### 20.6 Groq an der Quelle — die bindende Grenze ist die zweite

`console.groq.com/docs/rate-limits`, „Free Plan Limits", abgerufen 14.08.2026:

    llama-3.3-70b-versatile    RPM 30 | RPD 1.000 | TPM 12K | TPD 100K

1.000 Anfragen klingen großzügig; bei ~1.200 Token je Aufruf sind die 100.000
TPD nach rund **83 Aufrufen** erschöpft — ein Zwölftel davon. Der Deckel von 80
stimmt also, aber aus einem anderen Grund als der Zahl, die man zuerst liest.

**O-25:** `_verbraucht` zählt Anfragen, nicht Token. Für Gemini und OpenRouter
ist das die richtige Einheit, für Groq nicht. Solange Groq der letzte Topf ist,
genügt die Näherung.


---

## Kapitel 21 — Verkaufsseite, Kaufmail und die Gegenprüfung (14.08.2026)

### 21.1 Die Verkaufsseite — drei Klassen statt zwei

Von 45 Urteilen des ersten Echtbetriebs waren **elf Verkaufsseite, und keines
erreichte den Nutzer**. `AKTIONEN_MIT_EINSTIEG` kennt drei Wörter; alles andere
fiel in `_schreibe_nein()` und wurde als „reines LLM-Halten" gebucht.
**Verkaufen lag mit Nichtstun in einem Topf.** Nachgerechnet: alle elf hatten
Bestand, zusammen über 1.400 EUR, darunter BTC mit 917 EUR.

| Klasse | Aktionen | Weg |
|---|---|---|
| Einstieg | KAUFEN, NACHKAUFEN, ERÖFFNEN | Einstiegsrechnung, Einzelmail |
| **Ausstieg** | REDUZIEREN, VERKAUFEN, SCHLIESSEN | `verkaufsrechnung`, **eine** Sammelmail |
| Nichts | HALTEN, NICHTS_TUN | Schattenbuchung, keine Mail |

**Warum nicht `ausstiegsrechnung.py`:** die rechnet in R und verlangt Einstieg
**und** Originalstop. Der Spot-Bestand hat keinen Stop — dort ist die
Positionsgröße die einzige Risikosteuerung. Ohne Stop kein R.

**Eine Mail, nicht elf** — die Regel stand seit 05.08. im `ausstiegs_job`:
*„bei 15 offenen Empfehlungen wären 15 Mails Rauschen, und Rauschen wird
ignoriert."* Sortiert nach **Dringlichkeit**, nicht nach Euro
(`backward_tracking` 4930).

### 21.2 Beide Ebenen in derselben Zeile

Für BTC liefen zwei Ausstiegswege parallel — der tägliche 7:15-Job (Trailing,
Ziel, Frist) und das Modellurteil aus dem 15-Minuten-Lauf. Getrennt verschickt
sehen sie aus wie zwei Meinungen; sie beantworten aber verschiedene Fragen.

```
BTC   REDUZIEREN  ein Drittel   917,45 EUR   Stand -20,4 %
      Führung: SCHLIESSEN · höchster Stand +2,40 R · Stop auf 52.100
```

### 21.3 Welches Signal meldet — und warum es überhaupt mehrere sind

Am 14.08. hatten **DBPK und OD7L je fünf offene Signale**, 3QSS vier, MON und
OD7C drei. Das ist gewollt: `_is_superseded()` räumt ältere ab, aber erst nach
der Mindestbeobachtung. Der Absatzkopf nannte nur Symbol, Art und Tagesdatum —
die Abfrage holte die `id` gar nicht.

```
DBPK   Spot, seit 01.08. - Einstieg 61.200 EUR, Spot-Signal #2986
    aus der Mail "TradingInfoTool: DBPK - KAUFEN" vom 01.08.
```

Der Rückverweis nennt den Betreff **wörtlich** — er ist damit eine Suchzeile
fürs Postfach, kein Klick ins System.

**Zeitablauf gegen Ablösung**, beides deterministisch:
`ueberholt_durch_neuere_analyse` wird **vor** `abgelaufen_unentschieden`
geprüft — sonst stünde jede Ablösung als Zeitablauf in der Bilanz.

**Gliederung:** Dringlichkeit als Block, die sechs Gruppen **innerhalb**.
Umgekehrt stünde ein fälliger Ausstieg in Rohstoffen unter zwanzig
Krypto-Zeilen. Untertitel erst ab vier Einträgen.

### 21.4 O-19 bis O-24 — die Kaufmail

Die fünf fehlenden Blöcke waren **keine fehlenden Daten**: die Sätze gehen
längst ans Modell. `lagebeschreibung.geteilt()` gibt dieselben Blöcke einzeln,
und `beschreibe_lage()` **ruft** sie — der Prompt bleibt zeichengleich, was er
muss, sonst wären alle bisherigen Messungen unvergleichbar.

**O-24:** der alte Chart bräuchte das gekürzte Faktum `liquiditaetszonen`.
`ui/trade_chart.py` zeichnet stattdessen den Trade — Zone, Stop, Ziel im
Kursverlauf. **Ohne Umrechnungsfaktor kein Bild:** USD-Reihe gegen EUR-Linien
wäre richtige Form und falsche Skala.

### 21.5 O-25, O-26, O-28

**O-28 — der Hebel-Durchgang fiel nie aus, er war gesperrt.**
`assetklassen.laeufe()` fährt krypto/spot **vor** krypto/hebel über dieselben
43 Symbole; die Sperre fragte nur nach `symbol` und `quelle_kette`. Kein Fehler
im Log — es sah aus wie ein ruhiger Tag.

> ⚠️ **FOLGE, offen:** 385 Aufrufe/Tag gegen 450 nutzbare, davon **295 Hebel
> (77 %)**. Die 3,5 h stammen aus einer Kette, in der ein *Trigger*
> vorsortierte. Nutzerentscheidung 14.08.: **vorerst keine Änderung** — Hebel
> sind kurzfristig und sollen bei offener Position häufiger bewertet werden.

**O-26 — die CRV-Abstufung galt außerhalb ihrer Messung.** Gemessen an 298
**Krypto**-Spot-Signalen, angewandt auf jedes `instrument == "spot"`. An der
Börse verdreifacht sie die Kostenquote (400 EUR → 1,00 %, 80 EUR → 3,00 %) und
macht den Trade teuer, wenn das Modell am wenigsten überzeugt ist.

**O-25 — Groq rechnet in Token.** RPD 1.000 gegen TPD 100.000; bei ~1.200 Token
je Aufruf bindet der zweite Wert nach 83. `GROQ_AUFRUFE_JE_TAG = int(100_000 /
1_200)` wächst mit dem Prompt mit. Dazu ein echter Zähler:
`llm_basis.zaehle_token()`, Schlüssel `:token`, gebucht **nach** dem Aufruf.

### 21.6 Was die Gegenprüfung gefunden hat — und was sie widerlegt

**Die Rechnung rundete jeden Kurs auf Cent.** `round(x, 2)` auf Einstieg, Stop
und Ziel:

```
KAS    Kurs 0,02428  ->  Zone 0,02 bis 0,02, Stop 0,02, Ziel 0,03
PLUME  Kurs 0,0119   ->  Zone 0,01 bis 0,01, Stop 0,01
```

> ⚠️ **KORREKTUR VON KAPITEL 20.2.** Dort steht, die Rechnung sei richtig
> gewesen und nur die Darstellung habe sie vernichtet. **Das ist falsch.** Der
> Formatierer machte den Schaden sichtbar; verursacht hat ihn `round(x, 2)` in
> der Rechnung. Gefunden, weil die Gegenprüfung eine **echte Mail gerendert**
> hat statt Funktionen zu prüfen.

**Die Ausstiegsführung wurde ohne Watchlist geholt** — die Funktion warnt
selbst davor. Ohne sie trägt jede Zeile `tier = "spot"`, und die
Gruppenüberschriften aus 21.3 wären gebaut und wirkungslos gewesen.

**Vier Kostenarten statt zwei.** `kosten_r_aus_stop` kannte Krypto und Börse;
`backward_tracking.kosten_in_r` führt seit 07.08. alle vier und wird jetzt
aufgerufen statt nachgebaut. Ein Hebel-Trade über 2 Tage kostet 0,088 R, über
30 Tage 0,760 R — pauschal angesetzt waren 0,600 R.

### 21.7 Offene Punkte

| Nr. | Punkt | Stand |
|---|---|---|
| **O-16** | Spot und Absicherung trennbar über `SYMBOL_ZU_HEBEL_FAKTOR` | **erledigt** |
| **O-17** | Einmalkauf 800 € — Kostenbasis dokumentiert, Entscheidung offen | **beim Nutzer** |
| **O-29** | **Ratenfrage:** 0 von 1.142 (alt) gegen 11 von 45 (neu) | vertagt bis Krypto stabil |
| — | Hebel-Cooldown 3,5 h für alle 43 Symbole | bewusst unverändert |


### 21.8 O-16 und O-17 (nachgetragen)

**O-16 war mehr als eine Bilanzfrage.** Spot und Absicherung haben beide
`hebel IS NULL` und lagen deshalb in denselben Zellen. Die Unterscheidung kommt
jetzt aus der **einen** Stelle, an der sie im Projekt steht —
`hedge/pipeline.SYMBOL_ZU_HEBEL_FAKTOR` (DBPK, 3QSS). Keine neue Spalte, keine
Watchlist nötig: die Liste ist statisch, und Hedge ist keine Assetklasse.

> ⚠️ **Der eigentliche Fund:** bis heute zählten offene Absicherungen gegen den
> **Spot-Topf**. Der hat einen Deckel, die Absicherung nicht — eine gehaltene
> Hedge-Position hat also stillschweigend Spot-Budget belegt. An einem Beispiel
> gemessen: Spot meldete 1.600 statt 800 EUR belegt.

Weil `sql_bedingung()` nur einmal existiert, trennt jetzt auch der **Cooldown**
die beiden — ohne dass dort eine Zeile geändert werden musste.

**O-17 — die Kostenbasis**, bei 5 % Stop und 1 € fix je Seite:

| Betrag | Fixkostenanteil | Gesamtkosten | in R |
|---|---|---|---|
| 250 € | 0,80 % | 1,30 % | 0,260 |
| 400 € | 0,50 % | 1,00 % | 0,200 |
| **800 €** | **0,25 %** | **0,75 %** | **0,150** |
| 1.000 € | 0,20 % | 0,70 % | 0,140 |
| 1.500 € | 0,13 % | 0,63 % | 0,127 |

Die Kurve wird ab etwa 800 € flach — der Sprung von 250 auf 800 halbiert die
Kosten in R, der von 800 auf 1.500 spart nur noch 0,023 R. **800 liegt am
Knick, und das ist ein Argument, keine Entscheidung:** wieviel Geld in eine
einzelne Aktie geht, ist eine Risikofrage. Überschreibbar unter
`risiko.rollen_kette.einsatz_eur_je_gruppe`.

### 21.9 Zwei Lehren aus der Gegenprüfung dieses Schritts

1. Ich hatte den Konfigurationspfad **verkürzt dokumentiert**
   (`rollen_kette.*` statt `risiko.rollen_kette.*`) — die Prüfung ist genau
   darüber gestolpert. An der Quelle steht `_cfg()`.
2. Meine erste Prüfung testete, ob ein **Kommentar** existiert. `_quelltext()`
   wirft Kommentarzeilen bewusst weg, und eine Prüfung, die Dokumentation statt
   Verhalten prüft, ist die Falle, die dieses Skript schon dreimal getreten hat.


### 21.10 O-29 — die Ratenfrage, so weit sie heute beantwortbar ist

Alte Kette: **0 von 1.142** Krypto-Spot-Signalen VERKAUFEN (98,2 % HALTEN).
Neue Kette: **11 von 45** in einem Lauf. Werkzeug: `messe_verkaufsseite.py`.

**Erstens: die Aktion hängt vollständig am Bestand.**

| Aktion | im Bestand | nicht |
|---|---|---|
| HALTEN | 8 | 16 |
| REDUZIEREN | 9 | 0 |
| KAUFEN | 0 | 8 |
| NACHKAUFEN | 2 | 0 |
| VERKAUFEN | 2 | 0 |

Perfekte Trennung — aber sie ist **erzwungen, nicht geurteilt**: man verkauft
nicht, was man nicht hält, und ein Zukauf heißt NACHKAUFEN. Kein Qualitätsbeleg.

**Zweitens: innerhalb des Bestands trennt kein gemessenes Merkmal.**

| Merkmal | Verkauf | Halten | AUC | p |
|---|---|---|---|---|
| Buchergebnis % | −25,98 | −44,01 | 0,636 | 0,647 |
| Schwankung | 0,04 | 0,02 | 0,500 | 0,963 |
| Momentum | 0,60 | 0,68 | 0,329 | 0,472 |
| Volumen | 0,34 | 0,34 | 0,567 | 1,000 |

**Die Aufteilung ist durch nichts erklärt, was wir dem Modell gegeben haben.**

Bemerkenswert ist die *Richtung* beim Buchergebnis: verkauft werden die
**besseren** Positionen (Median −26 %), gehalten die **schlechteren** (−44 %) —
MORPHO +3 %, XLM +4 %, X136 +14 % sollen raus, BRETT −92 %, BEAMX −89 %,
KAIA −84 % bleiben. Das ist die Form des Dispositionseffekts. **Es ist nicht
signifikant** (p = 0,647), also kein Befund — aber es ist die einzige sichtbare
Tendenz, und sie zeigt in die unerwünschte Richtung.

> ⚠️ **„Nicht unterscheidbar" heißt hier NICHT „zufällig bewiesen".** Bei 11
> gegen 8 hat jeder Test wenig Trennschärfe. Der Unterschied ist der zwischen
> einem Befund und einer offenen Frage — und das Skript druckt ihn mit aus.

**Was offen bleibt:** ob die Verkäufe sich *tragen*. Dafür braucht es
aufgelöste Ausgänge, also Wochen. `rollen_kette.verkauf_mailt` entscheidet, ob
sie in der Zwischenzeit im Postfach landen oder nur in der Datenbank —
**gebucht wird in beiden Fällen.**


---

## Kapitel 22 — Der erste Betriebstag, nach dem Neustart (14.08.2026)

### 22.1 O-29 als Werkzeug, nicht als Auswertung

`messe_verkaufsseite.py` — Kreuztabelle Aktion × Bestand, dann AUC und
Permutationstest über die gemessenen Merkmale. Kein Modellaufruf, feste Saat.
`messe_begruendungen.py` — ordnet jeden Beleg dem Faktenblock zu, aus dem er
stammt, und hält die Ausgänge dagegen.

**Beide stehen NEBEN dem Export, nicht darin** (Methodik 2.13). 2.1a stellt die
**Rohdaten** bereit — dafür kam `belege_json` in den Export. Der Export ist ein
Basis-Werkzeug, das andere importieren; würde er selbst Analyseskripte
importieren, hinge die Datenbeschaffung an ihren Fehlern. Beide sind in 2.13
mit Auslöser registriert.

### 22.2 Die Belege gehen jetzt in die Datenbank

Bis heute ging nur ihre **Anzahl** hinein. Die Mail zeigte „Belege (5, davon 3
unabhängige Faktoren)" — gespeichert wurden die 5 und die 3. *Welche* Fakten
das Urteil trugen, war damit nachträglich nicht beantwortbar, und für
bestehende Zeilen bleibt es das: eine Zeile ohne Belege lässt sich nicht
nachrüsten.

### 22.3 Die Remote-Karte zeigte 0, während die Kette lief

```
LLM-Budget heute (Krypto)   0 / 180        Z.ai-Gegenprüfung heute   10
```

Zwei Zahlen auf derselben Karte, die einander widersprechen.
`count_real_signals_today()` filtert auf `groq_raw_response IS NOT NULL` — eine
Spalte, die **nur die alte Kette** schrieb. Und die 180 sind
`budget_allocator.taegliches_budget_gesamt`, während das Log selbst meldet:
*„Budget-Allocator übersprungen"*.

Die Karte zeigt jetzt die **Anbieter-Kontingente** — die einzige harte Grenze,
die die Kette anhalten kann. Gerechnet mit derselben Funktion, die auch
auswählt.

### 22.4 Zwei Aufräumsachen aus dem Log

**Abruftakt 2 s → 5 s.** Zwanzig Warnungen in drei Minuten, Aufbau 1,24–2,71 s.
Nachgemessen: am Desktop kalt 0,42 s, warm 0,03 s — der Cache wirkt. Die
Spitzen fielen genau in das Fenster, in dem die Rollen-Kette lief. Es ist
**Konkurrenz um die Maschine**, kein Defekt. Gegen Konkurrenz hilft kein Cache.

**Mistral raus** aus der Kategorie-Synthese — 402 seit dem 07.08., der Rückfall
auf Gemini funktionierte jedes Mal. Ein Fehler, der bei jedem Lauf auftritt und
nichts bedeutet, trainiert das Auge, Fehlerzeilen zu überlesen.

### 22.5 CANTON heißt an der Börse CC

Binance 400, Bybit 0 Kerzen, OKX 51001 — drei Börsen, dreimal nichts. Statt
eine vierte zu probieren: CoinGecko fragen, **wo** gehandelt wird. Antwort für
`canton-network`: Kraken, OKX, Bybit, MEXC — unter dem Ticker **CC**.

**Preis-Gegenprobe auf Nutzerfrage** („prüfe ob cc und canton ident sind"):

| | Kraken | CoinGecko | Abweichung |
|---|---|---|---|
| CANTON | CCUSD 0,096770 | canton-network 0,096751 | **0,02 %** |
| VSN | VSNUSD 0,035410 | vision-3 0,035603 | **0,54 %** |

Dieselbe Probe hat am 11.08. den yfinance-Rückfall zu Fall gebracht — dort
gehörten drei von acht geratenen Tickern einem anderen, toten Asset.

Abgerufen: CANTON 278 Tageskerzen, VSN 395, Abstände genau 1 Tag. **EURCV ist
kein Loch** (Cash-Äquivalent, korrekt ausgeschlossen), **ASTER** hat 313/328
Kerzen — seine Lücke war die veraltete Desktop-Datenbank.

### 22.6 „database is locked"

`sqlite3.connect()` lief ohne Timeout (Vorgabe 5 s) und im
Vorgabe-Journalmodus, in dem ein Schreibvorgang die **ganze Datei** sperrt.
Jetzt `busy_timeout` 30 s und **WAL**. Vorher geprüft, dass der Export
`conn.backup()` benutzt — die Online-Backup-API, die WAL kennt.

### 22.7 Ein Rechenfehler von mir, und ein falscher Alarm

> ⚠️ **O-30 — meine Budgetrechnung zählte Urteile, das Kontingent zählt
> HTTP-Versuche.** `zaehle_aufruf` steht in `api/gemini.py` **innerhalb** der
> Wiederholschleife; jeder 429- und 503-Versuch bucht mit. Bei 385 Urteilen
> und im Schnitt 1,5 Versuchen sind das 578 Aufrufe — der erste Topf (450)
> wäre leer. Meine Aussage „385 von 450, es passt" hat diesen Faktor nicht
> berücksichtigt. **Muss am ersten vollen Betriebstag gemessen werden.**

**Und ein Alarm, der keiner war:** OpenRouter tauchte auf Signalen auf, was
nach erschöpften Gemini-Töpfen aussah. Der Nutzer hat es aufgelöst — es waren
**keine Krypto-Signale**. Aktien, Rohstoffe, Themen-ETF und Hedge laufen weiter
über die alte Kette (`multi_asset_batch_job`, Mo–Fr 9 und 19 Uhr), und die
benutzt OpenRouter. Erwartetes Verhalten, solange `aktiv_fuer` nur `krypto`
kennt.


---

## Kapitel 23 — Der Trockenlauf über beide Instrumente (15.08.2026)

### 23.1 Die Ursache des Hebel-Stillstands war der Deckel — nicht die Schatten

Am 14.08. abends hatte ich sie in den Schattenbuchungen vermutet und
`belegt_eur` umgebaut. **An den Daten widerlegt:**

```
Topf ohne Aktionsfilter (vor dem Fix):  0 EUR
Topf mit  Aktionsfilter (nach dem Fix): 0 EUR
```

Schattenzeilen tragen gar keinen `position_size_eur` — sie konnten den Topf nie
füllen. Der Fix bleibt richtig (ein Schatten ist keine Position), aber er hat
die Ursache nicht berührt, und genau das hatte ich behauptet.

**Der Beweis aus dem Export vom 15.08. 04:16:**

```
12:23  LINK  NACHKAUFEN  hebel 10.0  position_size_eur 500.0
Hebel-Topf belegt: 500 EUR   Deckel laut config.yaml: 500 EUR
```

> ⚠️ **Die Nutzerentscheidung vom 13.08. lautete 3.000 EUR.** Sie stand nur in
> `toepfe.VORGABE_DECKEL_EUR`; die `config.yaml` führte weiter 500 — und die
> **Konfiguration gewinnt gegen den Code.** Ein einziges Signal füllte damit
> den Topf, und ab 12:23 bekam jedes weitere Hebel-Symbol Betrag 0, blockiert
> an der Stufe `geometrie` — also **nach** dem Modellaufruf. Ohne Zeile kein
> Cooldown, alle 15 Minuten von vorn.

**Bilanz des Betriebstags: 802 Gemini-Aufrufe, 47 Urteile — davon 1 nach 12:23.**

Eine Prüfung verlangt jetzt, dass Code-Vorgabe und Konfiguration denselben Wert
tragen. Eine Vorgabe, die von der Konfiguration überstimmt wird, ist kein
Standard, sondern eine zweite Wahrheit.

### 23.2 Die Verkaufsseite war seit ihrem Bau tot

Der Trockenlauf zeigte es in der ersten Zeile:

```
'str' object has no attribute 'get_all_holdings'
```

`_ein_asset` bekommt `db: str = "data/tradinginfotool.db"` — den **Dateinamen**.
Mein Verkaufszweig rief darauf Modulfunktionen auf; der Fehler landete im
breiten Fang als „Bestand nicht lesbar", und **jedes** Verkaufsurteil wurde als
„ohne Bestand" zum Schatten.

> Und am 14.08. habe ich auf genau dieses Symptom einen Fix gesetzt: im Gate
> stand „5x SCHLIESSEN ohne Bestand", ich schloss auf die falsche **Tabelle**
> und stellte auf `hebel_positions` um. Das war richtig — und heilte nichts,
> weil der Aufruf davor schon scheiterte. **Ein Symptom kann zwei Ursachen
> haben, und die erste gefundene ist nicht automatisch die einzige.**

Nach der Korrektur: Spot-Ausstiege 7 statt 0.

### 23.3 Was der Trockenlauf sonst zeigt

| Instrument | hinein | heraus | Ausstiege | Hauptverlust |
|---|---|---|---|---|
| Spot | 35 | 21 | 7 | 7× „ohne Bestand", 7× Vertragsverstoß (Testdaten) |
| Hebel | 35 | 10 | 0 | 25× Aktion (HALTEN, SCHLIESSEN/HEBEL_SENKEN ohne Bestand, HEBEL_ERHÖHEN) |

**O-31: `HEBEL_ERHÖHEN` fällt durch alle Raster.** Es steht weder in
`AKTIONEN_MIT_EINSTIEG` noch in `AKTIONEN_MIT_AUSSTIEG` und wird als „nichts"
gebucht — obwohl es Kapital bindet. 5 von 35 im Trockenlauf.

**O-32: Hebelfaktor 10,0** beim LINK-Signal. Der Nutzer nannte am 13.08. „eine
Hebelposition vorerst 1000" für den *Betrag*; ob 10× die gewollte Hebelhöhe
ist, wurde nie entschieden.

### 23.4 Der Export bestätigt zwei weitere Fehldeutungen

„gemini gesamt 802 über 500er Limit" — **kein Limitbruch.** Die Grenze gilt je
Modell: 3.1 bei 451, 3.5 bei 351, beide unter 500. Der Sammelzähler „gemini"
ist der alte UTC-Zähler.

„5 Job-Fehler durch Multi-Modell-Switching" — **keiner aus der Rollen-Kette:**
3× FRED-Makroabruf, 2× die alte Kette bei OD7x.

---

## Kapitel 24 — Der Vollumstieg (15.08.2026)

### 24.1 Die Trennlinie, auf der alles Weitere steht

> **Das System bemisst den einzelnen Trade. Die Aufteilung des Portfolios
> bemisst der Nutzer.**

Stop, Positionsgröße aus Risiko und Hebel aus Liquidationsabstand folgen aus dem
Trade allein. Topf und Cash-Reserve brauchen Wissen, das dieses System **nicht
hat**: ob der Nutzer die Empfehlungen von gestern ausgeführt hat. Es kennt
seinen Bestand (Bitpanda-Sync), nicht seine Absicht.

| Begrenzung | misst | Verhalten |
|---|---|---|
| Cash (RM-4) | echtes Geld | meldet |
| Topf | echte Positionen | meldet |
| CRV-Abstufung | — | **stillgelegt** |
| Mindestgröße je Kostenklasse | Trade-Eigenschaft | **einzige harte Grenze** |

Die CRV-Abstufung ist **still, nicht neu kalibriert**: gemessen an 298 Signalen
der *alten* Kette, als das Ziel mechanisch bei CRV 2,0 lag. Seit dem
Struktur-Ziel fällt das CRV aus dem Chart, und der Regelfall traf den Sockel —
160 von 800 EUR. Eine neue Spreizung wäre wieder eine Zahl ohne Messung.

Die Mindestgröße ist **gemessen, nicht gesetzt**: Krypto 25 €, Börse 100 €.
Krypto ist betragsunabhängig (1,5 % je Seite kürzen sich heraus) — eine
Mindestgröße aus Gebührengründen hat dort keine Grundlage.

### 24.2 Paket 14 — die Absicherung fragt nach dem Portfolio

Der letzte nicht gebaute Baustein. Bis dahin lief sie durch den Spot-Prompt:
Marktstruktur, Widerstand, Momentum **des Instruments**. Bei 3QSS und DBPK ist
das die falsche Frage — ihr Chart *ist* das Spiegelbild des Nasdaq bzw. S&P.

```
Abzusicherndes Exposure: 8.804 EUR (alles außer Absicherungen und Cash).
Davon bereits abgesichert: 1.337 EUR - das sind 15 %.
Dieses Instrument hebelt 3-fach auf den Nasdaq-100; 1 EUR deckt 3 EUR.
Für volle Deckung der offenen 7.467 EUR wären 2.489 EUR nötig.
Laufende Gebühr etwa 0,8 % pro Jahr.
```

> ⚠️ **Halber Fehler im Trockenlauf gefunden:** die Mail zeigte weiter die
> gemessenen Trefferquoten — *„Ruhig ist besser — über alle Einstiege gemessen:
> 29,5 % Treffer"*. Diese sind an **Einstiegen** gemessen; eine Absicherung
> wird nicht gekauft, um zu steigen. Eine Zahl mit falscher Herkunft liest sich
> wie ein Befund. Der Faktenblock lässt sie für `hedge` jetzt weg **und sagt,
> dass er es tut.**

### 24.3 Inhaltliche Stichprobe — je Gruppe unabhängig nachgerechnet

| Gruppe | Symbol | Kurs Mail / nachgerechnet | Stop Mail / 2,5×ATR | Kosten in R |
|---|---|---|---|---|
| aktien | PLTR | 150,77 / 150,77 | 132,82 / 132,82 | 0,063 |
| hedge | 3QSS | 1,35 / 1,349 | 1,20 / 1,2016 | 0,082 |
| krypto spot | AIOZ | 0,04176 / 0,041755 | 0,03464 / 0,034639 | 0,176 |
| krypto hebel | AIOZ | 0,04176 / 0,041755 | 0,03464 / 0,034639 | 0,012 |
| rohstoffe | OD7C | 30,09 / 30,0899 | 29,05 / 29,0523 | 0,218 |
| themen_etf | CEBS | 9,64 / 9,643 | 8,96 / 8,9638 | 0,106 |

**Keine Abweichung.** Nachgerechnet zu Fuß aus Kerze und Bestand, nicht über die
Kette — eine Prüfung, die dieselbe Funktion aufruft, prüft nur, dass die
Funktion sich selbst gleicht.

### 24.4 Der Schnitt griff nur halb — zwei Funde

> ⚠️ **`bedient_neue_kette` stand an genau EINER Stelle**, in
> `hebel_screening_job`, und dort **fest auf „krypto"**. Der Multi-Asset-Batch —
> der Aktien, Rohstoffe, Themen-ETF und die Absicherung bedient — kannte den
> Schnitt **gar nicht**.
>
> `aktiv_fuer` auf alle sechs zu setzen hätte damit nicht umgestellt, sondern
> **verdoppelt**: Rollen-Kette im 15-Minuten-Takt und Batch um 9 und 19 Uhr,
> dieselben Symbole, beide mit Modellaufrufen und Mail. Genau der
> Parallelbetrieb, den der Nutzer am 13.08. ausgeschlossen hat.

Zweitens lautet die Startfrage jetzt *„ist irgendeine Gruppe umgestellt"* statt
*„ist krypto umgestellt"*. Wäre Krypto eines Tages abgeschaltet und Aktien
nicht, liefe der Umlauf sonst lautlos gar nicht.

### 24.5 Budget mit allen sechs Gruppen

| Gruppe | Instrument | Symbole | Cooldown | Aufrufe/Tag |
|---|---|---|---|---|
| aktien | spot | 2 | 24 h | 2 |
| hedge | absicherung | 2 | 24 h | 2 |
| krypto | spot | 43 | 15 h | 69 |
| krypto | hebel | 43 | 3,5 h | **295** |
| rohstoffe | spot | 4 | 24 h | 4 |
| themen_etf | spot | 5 | 24 h | 5 |
| Lagebild | (3 h) | | | 8 |
| **Summe** | | | | **385** |

**Bindend ist der erste Topf: 450 nutzbar.** Der Hebel trägt 77 % — der
Vollumstieg kostet nur **16 zusätzliche Aufrufe**.

> ⚠️ **Korrektur vom 15.08. abends.** Hier stand *„alle vier zusammen 1.874"*,
> und dieselbe Summe stand als „Aufrufe frei" auf der Remote-Karte.
> Arithmetisch richtig (450 + 450 + 900 + 74), als Aussage falsch: **die Töpfe
> sind eine Rückfallkette, kein Vorrat.** OpenRouter und Groq kommen erst dran,
> wenn Gemini erschöpft ist — und dahinter steht ein **anderes Modell**. Dieses
> Projekt hat gemessen, dass das zählt: nemotron dreht bei bitgleicher Eingabe
> in ~12 % der Fälle die Richtung, Mistral lag über 38 Fälle bei −27,38 R. Ein
> Durchfallen in Topf 2 heißt, dass ein anderes Modell antwortet und die
> Messreihe bricht.
>
> Und bei Groq ist die bindende Grenze nicht die Anfragenzahl, sondern
> **100.000 Token am Tag** — bei ~1.200 je Aufruf sind das 83, ein Zwölftel der
> 1.000 RPD.
>
> **Mit rund 405 Aufrufen Bedarf gegen 450 nutzbar liegt der Betrieb bei 90 %
> des ersten Topfes.** Die Remote-Karte zeigt seitdem den ersten Topf mit Rest
> vorn und die Kettensumme daneben.

> ⚠️ **Dritter Fund, aus dieser Rechnung:** die Gruppen-Cooldowns waren **toter
> Code**. `budget_allocator.spot_cooldown_stunden` (15) stand in der
> config.yaml und wurde **vor** der Gruppen-Vorgabe (24) gefragt — die 24
> Stunden vom 14.08. kamen nie zum Zug. Im Krypto-Betrieb unsichtbar, weil
> Krypto ohnehin 15 h hat. **Eine Gruppe ist spezifischer als ein Instrument;**
> innerhalb derselben Spezifität gewinnt weiterhin die Konfiguration.

**O-30 bleibt offen:** das Kontingent zählt HTTP-**Versuche**, nicht Urteile.
Bei 1,5 Versuchen je Urteil wären es 578 statt 385.

### 24.6 Offene Punkte nach dem Vollumstieg

| Nr. | Punkt |
|---|---|
| **O-17** | Einmalkauf 800 € für Börsenwerte — übernommen, nicht entschieden |
| **O-29** | Ratenfrage der Verkaufsseite — 0 von 1.142 (alt) gegen 11 von 45 (neu) |
| **O-30** | Kontingent zählt Versuche, Budgetrechnung zählt Urteile |
| **O-32** | Hebelfaktor stand bei 10,0 — nie entschieden |
| — | CRV-Abstufung: messbar, sobald aufgelöste Signale vorliegen |

---

## Kapitel 25 — Geplant nach dem ersten sauberen Produktionslauf (15.08.2026)

Beide Punkte kommen vom Nutzer, in dieser Reihenfolge — der zweite **vor** dem
ersten.

### 25.1 Zuerst: die Fakten und Entscheidungen der LLM aufschlüsseln (O-34)

> *„Zuvor müssen wir — wie bereits angekündigt — die Fakten und Entscheidungen
> der LLM aufschlüsseln und bewerten, falls notwendig auch anpassen."*

Das Werkzeug steht: **`messe_begruendungen.py`** ordnet jeden Beleg dem
Faktenblock zu, aus dem er stammt, und hält die Ausgänge dagegen. Seit dem
14.08. wird `belege_json` geschrieben — ohne diese Spalte wäre die Frage
nachträglich nicht beantwortbar, und eine Zeile ohne Belege bleibt ohne Belege.

**Was die Auswertung liefern wird:**

| Block | Kauf | Verkauf | trägt sich |
|---|---|---|---|
| struktur · bewegung · marken · volumen · finanzierung · lagebild · bestand | | | |

**Und was daraus folgen kann.** Trägt ein Block nichts bei, gehört er aus dem
Faktentext — jede Zeile darin kostet Prompt und Aufmerksamkeit. Trägt einer
auffällig viel, ist er der Kandidat für mehr Tiefe. Das ist die erste Änderung
am Prompt, die auf einer **Messung** stehen würde statt auf einer Annahme.

**Voraussetzung:** aufgelöste Signale *mit* Belegen. Das braucht Wochen; das
Skript trennt Verteilung von Erfolg und sagt selbst, wenn es nur die erste hat.

### 25.2 Danach: Hedge-Instrumente ohne Codeeingriff ergänzen (O-33)

> *„berücksichtige im Plan einen nachgelagerten Punkt, um Börsenwerte (Hedge
> über Nasdaq etc.) zu den Hedge-Positionen hinzufügen zu können, ohne dass wir
> in den Code eingreifen müssen."*

**Heute geht das nicht.** `hedge/pipeline.SYMBOL_ZU_HEBEL_FAKTOR` ist ein fest
verdrahtetes Wörterbuch mit zwei Einträgen (DBPK 2×, 3QSS 3×), dazu
`SYMBOL_ZU_REFERENZ_INDEX`. **Elf Module lesen es:**

```
absicherung_fakten · assetklassen · hedge/pipeline · krypto/backward_tracking
multi_asset_batch · themen_etf/pipeline · toepfe · scheduler/background
teste_hedge_wirksamkeit · ui/app · ui/signals_view
```

**Das ist die gute Nachricht.** Weil alle elf über *dieselbe* Stelle gehen,
genügt es, **diese eine** aus der Konfiguration zu speisen — mit der
Code-Liste als Rückfall. Kein Aufrufer muss angefasst werden.

```yaml
hedge:
  instrumente:
    3QSS: {hebel: 3, referenz: "Nasdaq-100"}
    DBPK: {hebel: 2, referenz: "S&P 500"}
```

**Drei Dinge, die dabei nicht vergessen werden dürfen:**

1. **Hedge ist keine Assetklasse.** Ein neues Instrument steht in der Watchlist
   als `etf` und wird *nur* über diese Zuordnung zur Absicherung. Genau daran
   ist der OHLC-Refresh am 06.08. gescheitert.
2. **Der Hebelfaktor ist die Größenlogik**, nicht Schmuck: `benötigter Einsatz
   = abzusicherndes Exposure / Hebelfaktor`. Ein falscher Faktor
   über- oder unterhedgt still.
3. **Ein neues Instrument braucht eine Kursreihe.** 3QSS und DBPK stehen in
   EUR, nicht USD — und werden zur Laufzeit rekonstruiert. Wer eines ergänzt,
   ohne das zu prüfen, bekommt eine Gruppe ohne Daten (Kapitel 19.2).

**Warum nachgelagert:** solange die Absicherung aus zwei Instrumenten besteht,
ist der Codeeingriff einmal im Jahr fällig. Die Konfigurierbarkeit lohnt, wenn
mehr dazukommen — und sie sollte nicht zwischen Produktivgang und erster
Messung geschoben werden.

### 25.3 Die Reihenfolge, und warum sie so herum ist

Beide Punkte sind **nach** dem ersten Produktionslauf ohne massive Fehler
angesetzt — geprüft über NB-Export und Log. Der Grund ist derselbe wie am
14.08.: jede Änderung während eines Laufs vermischt sich mit dem, was der Lauf
zeigen soll.

Und O-34 kommt vor O-33, weil es die teurere Frage ist. Ob wir Hedge-Instrumente
bequem ergänzen können, ändert nichts an der Qualität der Empfehlungen. Ob die
Fakten tragen, ändert alles.

### 25.4 Drei Werte, die der Nutzer bewusst stehen lässt (15.08.2026)

Vor dem Produktivgang zur Abstimmung gestellt, alle drei beantwortet mit
**„vorerst so belassen"**. Das ist ausdrücklich **keine Bestätigung des
Wertes** — es ist die Entscheidung, ihn nicht ohne Messgrundlage zu ändern.

| Nr. | Wert | Stand |
|---|---|---|
| — | Hebel-Cooldown 3,5 h | bleibt; trägt 295 von 385 Aufrufen (77 %) |
| **O-32** | Hebelfaktor 10,0 | *„in der Theorie möglich — ob ok, kann man noch nicht sagen"* |
| **O-17** | Einmalkauf 800 € Börsenwerte | bleibt, übernommen aus Krypto |

**Der Nutzer hat das 10,0×-Signal nie erhalten** — es entstand im Trockenlauf
am Desktop. Ob 10-fach in der Produktion überhaupt auftritt, ist damit selbst
noch eine offene Beobachtung, keine Feststellung.

**Alle drei bleiben offen und werden entschieden, wenn es Zahlen gibt** — der
Cooldown, sobald das Kontingent unter dem Vollumstieg gemessen ist; O-32,
sobald ein echtes Hebel-Signal mit hohem Faktor aufgelöst ist; O-17, sobald
Börsenwerte-Signale in der Produktion angekommen sind. Sie stehen damit in
derselben Reihe wie die CRV-Abstufung: **stillgestellt, nicht kalibriert.**

---

## Kapitel 26 — Fünf Funde aus dem ersten Produktionslauf (15.08.2026)

Der Nutzer nach Sichtung des Posteingangs:

> *„dieses Bild im Maileingang ist fast so erschreckend wie wenn keine Mails
> gekommen wären"*

**26 Einstiegsempfehlungen über 10.400 EUR in 105 Minuten, bei 10.388 EUR
Depotwert** — davon 5.200 EUR Doppelnennungen. Dreizehn Hebel-Eröffnungen
fielen in 96 Sekunden.

Die Mengenfrage ist damit gestellt, aber **nicht** hier beantwortet (26.6).
Zuerst die Frage des Nutzers: *„Zuerst sollten wir wissen warum jetzt das
Ganze Portfolio gehandelt wird."*

### 26.1 Warum die Menge entstand — gemessen, nicht vermutet

**Zwei Änderungen, beide gewollt, nie miteinander multipliziert.**

| | alt | neu |
|---|---|---|
| Anteil der Assets, die vor das Modell kommen | 3,3 % | 60 % |
| Handlungsquote des Modells | 1,8 % | 15 % |

Die alte Kette bewertete jedes Asset zuerst deterministisch: 51.019
Screenings → 7.588 Kandidaten (14,9 %) → 1.699 erreichten das Modell.
`assetklassen.laeufe()` gibt **alle** Symbole der Gruppe zurück, ohne
Bedingung; nur der Cooldown nimmt etwas weg (109 von 270 = 40 %).

**Der Anlass ist die Uhr.** `hebel_trigger` kommt in keinem Modul der
Rollen-Kette vor — und das Screening läuft weiter, schreibt seine Kandidaten
in die Datenbank, und niemand liest sie.

Im eingeschwungenen Zustand: 385 Urteile am Tag × 6,6 % ≈ **25
Kaufempfehlungen täglich**.

### 26.2 Der Faktensatz sagte im Hebel-Lauf „ohne Hebel"

> ⚠️ **Der schwerste Fund.** `rollen_eingabe.baue_fall()` nahm `instrument`
> gar nicht entgegen. `baue_befund_eingabe()` fiel damit auf seine
> Vorgabewerte zurück, und im AUFTRAG-Block **jedes** Laufs stand:
>
> ```
> Gehandelt wird der Wert selbst, ohne Hebel und ohne laufende Kosten.
> ```
>
> Auch im Hebel-Lauf. Auch im Absicherungslauf.

Die Rolle bekam ihre Anweisung getrennt und richtig
(`rolle_trader.prompt_fuer(instrument, …)`) — die **Fakten widersprachen ihr**,
und `handelsauftrag.beschreibe()` nennt sich selbst die *Bedingung, unter der
alles Weitere zu lesen ist*. Sie steht bewusst zuerst, weil was zuerst steht
schwerer wiegt (R-T9).

**13 Hebel-Eröffnungen entstanden auf Fakten, die dem Modell sagten, es gebe
keinen Hebel und keine laufenden Kosten.**

### 26.3 Der Bestand kam immer aus der Spot-Tabelle

`rollen_eingabe.bestand()` las `holdings` — auch im Hebel-Lauf. Im Prompt
stand dann für LINK:

```
LINK ist bereits im Bestand: 1700 EUR investiert, aktuell 1093 EUR wert
```

Das Modell tat, was jeder täte, der das liest: **SCHLIESSEN**. Danach sah der
Code korrekt in `hebel_positions` nach, fand nichts und verwarf.

**22× SCHLIESSEN und 3× TEILVERKAUF „ohne Bestand" — 9 % aller Modellaufrufe.**

Der Kommentar im Verwerfzweig sagte, das sei kein Fehler des Modells, es kenne
den Bestand nicht. Das stimmte nicht: **es kannte einen Bestand, nur den
falschen.**

**Und die Gegenrichtung ist der LINK-Fall des Nutzers:**

> *„problem ist dass die trades unabhängig sind und ich bin in einem hebel bei
> LINK — also eine Empfehlung und dann kommt ein spot verkauf rein."*

Ein Urteil je Asset wäre die vollständige Lösung; der Nutzer hat sie als zu
komplex zurückgestellt, solange die Fakten nicht stimmen. Die kleine Lösung
steht jetzt: **die andere Seite wird benannt statt verschwiegen.**

```
In LINK besteht keine offene Hebelposition.
Unabhaengig davon liegen 141,8961 Stueck LINK im Spot-Bestand.
Das ist KEINE Hebelposition und wird getrennt beurteilt.
```

### 26.4 Ein Hebel von 1,0 riskierte mehr als erlaubt

`max(1.0, min(hebel_noetig, …))` war als Untergrenze gedacht und war eine
stillschweigende Umdeutung. Fällt der nötige Faktor unter 1, heißt das: **die
ungehebelte Position riskiert bereits mehr als das Budget hergibt.** Die
Untergrenze hat den Überschuss nicht beseitigt, sondern verschwiegen.

Gemessen am KAITO-Fall: 300 EUR bei 9,9 % Stop riskieren **29,70 EUR gegen ein
Budget von 20**.

Dazu kam eine zweite Ebene: `signal_abbildung` schrieb die Hebelspalte nur bei
`hebel > 1.0`. KAITO und CAT landeten damit als **Spot** in der Datenbank —
außerhalb von Hebel-Cooldown (`hebel IS NOT NULL`) und Hebel-Topf, mit dem
Mailbetreff *ERÖFFNEN (Hebel)*.

> ⚠️ **Meine erste Fassung sagte solche Fälle ab — und die eigene Prüfung 10
> hat sie gestoppt:** dort liegt der nötige Faktor bei 0,99. Ein Prozent
> Überschuss ist ein Rundungsrand, keine Pathologie. **Der Betrag folgt jetzt
> dem Risikobudget** (300 → 202 EUR), der Faktor ist danach genau 1,0, und die
> Spalte entscheidet sich am **Instrument** statt am Wert.

### 26.5 Zwei kleinere, beide mit Folgen

**Die Frist des Modells lag fast immer in der Vergangenheit.** Von 37 Werten
für `umgeworfen_bis` lagen **36 vor dem Tag des Signals**, allein 29-mal der
Füllwert `2024-12-31`. Gerechnet wurde nichts falsch — `_tage_bis()` fängt es
ab. Aber `ausstiegsrechnung` führt die Frist als drittes Kriterium und setzt
„· FRIST ABGELAUFEN" in die Überschrift. Am 15.08. traf das erst 1 von 40
Positionen, **nur weil die alten Signale das Feld nicht hatten.**

**ASTER stürzte bei jedem Lauf ab**, 16× seit dem 14.08. Der Wächter in
`faktenblock.werte_aus_reihe()` prüfte `RUECKBLICK + ATR_FENSTER` = 264, die
Momentum-Fenster brauchen aber `RUECKBLICK + MOMENTUM_FENSTER` = 310. **In der
Lücke von 46 Kerzen wurde die Auswahl leer**, und `.max()` warf. ASTER stand
bei 299, MON bei 264 — jedes Symbol durchläuft dieses Fenster, während seine
Historie wächst.

### 26.6 Was ausdrücklich NICHT entschieden ist

Der Nutzer hat meinen ersten Vorschlag — einen Deckel je Umlauf — als
**Pseudogate** zurückgewiesen, mit der Frage, auf die es keine Antwort gibt:
*welche Trades sind wirklich GUT, und wie willst du das messen?* Ein
Qualitätsrang wäre eine Behauptung gegen den eigenen Grundbefund (8.441 Fälle,
kein Verfahren schlägt die Basisrate).

> **Nutzervorgabe:** *„damit wir nicht wieder Einschränken damit es weniger
> wird, sondern wir haben das System aufgemacht um besser zu werden."*

Offen und zu schärfen, **nicht zu bauen**: die Gliederung der beiden
Vorschläge — ein Urteil je Asset (zurückgestellt, optional) und der Anlass
statt der Uhr (B1 vorhandenes Screening · B2 neu für alle Gruppen · B3 „es hat
sich etwas geändert").

### 26.7 Gegenprüfung

| Prüfung | Ergebnis |
|---|---|
| Jeder Fix am auslösenden Fall | 27 von 27 |
| Bestehende Paketprüfungen | **784, alle bestanden** (779 + 5 neue) |
| Spot-Prompt gegen den Stand davor | **55 Symbole bitgleich** |
| Hebel-Prompt | verändert, genau dort wo er falsch war |
| Symbole, die noch abstürzen | 0 |

Der bitgleiche Spot-Prompt ist die wichtigste Zeile dieser Tabelle: alle
bisherigen Messungen bleiben vergleichbar.

### 26.8 Der sechste Fund — zwei Geometrien für dasselbe Signal

Der Nutzer, nachdem der Fund benannt war:

> *„ein ähnliches Problem hast du gestern bereits gefixed — offenbar ist der
> Fehler verstreut."*

Er hat recht, und das ist die eigentliche Lehre. Es gab **drei** Stellen:

| Weg | las die Geometrie aus | Stand |
|---|---|---|
| Mail (`rollen_lauf`) | der **Rechnung** | 14.08. repariert |
| Schattenbuchung (`_schreibe_nein`) | der Rechnung, **nachgeflickt** | Flicken |
| **Hauptpfad (`signal_abbildung`)** | **dem Modell** | unbemerkt |

Zwei Reparaturen an zwei Symptomen, und die Ursache stand unberührt dazwischen.
Dasselbe Signal trug damit zwei Geometrien: eine, die der Nutzer liest, und
eine, die in der Datenbank steht.

**Gemessen an den 23 Einstiegen des Vormittags:**

| | |
|---|---|
| Zeilen mit **engerem** Stop als die Mail | **19 von 23** |
| Median-Faktor | 1,5× |
| Äußerster Fall | ETH, 0,94 % gegen 2,50 % (2,7×) |
| Zeilen unter RM-1b (2,5 %) | **7** |

> ⚠️ **Korrektur meiner eigenen Zahl:** zuerst nannte ich Faktor 3 bis 7. Diese
> Rechnung ließ `umgeworfen_preis_eur` weg — den Falsifikationspreis des
> Modells, der in den Stop eingeht. Mit ihm sind es 1,5 im Median. Die
> Richtung bleibt, die Größenordnung war zu hoch.

**Warum es mehr als Unsauberkeit ist:** `stop_loss_*` wird von **17 Modulen**
gelesen, darunter `backward_tracking` — die Erfolgsmessung. Sie hätte jedes
Rollen-Signal an einem Stop gemessen, der nie empfohlen wurde, und die
Trefferbilanz wäre systematisch zu schlecht ausgefallen. Die sieben Zeilen
unter RM-1b gehören zu der Klasse, für die dieses Projekt **0,0 %
Trefferquote über 9 Trades** gemessen hat.

**Der Fix:** die Abbildung nimmt die Geometrie aus der Rechnung, für **beide**
Wege; der Flicken im Schattenpfad fällt weg. Der Stop steht in `von` und `bis`
gleichermaßen — eine Marke, an der geschlossen wird, hat keine zwei Kanten.
Das Modell bleibt Rückfall für Zeilen ohne Rechnung, und seine Zahl ist nicht
verloren: `umgeworfen_preis_eur` geht als **Eingabe** in genau diesen Stop.

**Nebenbefund für O-34:** `stop_zu_eng` wird von **niemandem** gelesen —
außerhalb von `rolle_trader.py` null Fundstellen. Nach diesem Fix ist das
keine Lücke mehr, sondern eine Messgröße: wie oft schlägt das Modell einen
Stop vor, der unter dem Grundrauschen liegt.

> **Eine Prüfung hielt den ORT des Flickens fest statt die Tatsache** und
> schlug deshalb an, obwohl die Sache besser gelöst ist. Sie prüft jetzt das
> Verhalten. Eine Prüfung, die eine Stelle festschreibt, verbietet ihre
> Verbesserung.

### 26.9 Welche Krypto-Assets in den Hebel-Lauf gehen

Nutzerfrage: *„nur jene welche in der GUI mit Hebel gekennzeichnet sind?"*

**Ja** — Kette und Oberfläche fragen dieselbe Funktion
(`asset_schalter.darf_analysiert_werden` und `ui/app.py`), es gibt keinen
zweiten Weg. Die 19 abgeschalteten greifen nachweislich: 34 Gate-Verluste mit
genau dieser Begründung, kein Signal von einem abgeschalteten Asset.

| | Anzahl |
|---|---|
| Krypto in der Watchlist | 44 |
| Schalter ausdrücklich **aus** | 19 |
| Schalter ausdrücklich **an** | 17 |
| **ohne jede Zeile** | **8** |
| → gehen in den Hebel-Lauf | **25** |

**Der Schalter ist ein Opt-out, kein Opt-in.** Ohne Zeile gilt „an"
(`db.py:1653`, ausdrücklich so entworfen). Die GUI zeigt sie deshalb als „An" —
ehrlich, aber vom Nutzer nie entschieden: BNB, BTC, ETH, HYPE, KAIA, SUI, TAO
und **EURCV**.

**Vier der zwölf Hebel-Signale des Vormittags stammen daraus** (BNB, ETH,
HYPE, TAO). Und EURCV ist ein Euro-Stablecoin — er fällt nur deshalb nicht ins
Modell, weil seine Reihe keine Tageskerzen hat. Dass ihn ein Datenmangel
aufhält und keine Regel, ist Zufall.

**Offen, gehört dem Nutzer:** ob die acht ohne Zeile bewusst mitlaufen sollen.

### 26.10 Der Hebel-Schalter wird gerade gezogen — Opt-out wird Opt-in

Nutzer, nach dem Blick in die eigene Oberfläche:

> *„der Schalter ist ein OPT IN … wir haben ohne Schalter angefangen und der
> ungleiche Stand kam damit zustande. ja kann man machen, default ist auf aus
> und der aktuelle Bestand — bei Hebel muss gerade gezogen werden."*

**Die Herkunft des ungleichen Stands.** Der Schalter kam am 18.07. dazu, als
schon 44 Krypto-Assets in der Watchlist standen. Wer nie angefasst wurde, hatte
keine Zeile — und „keine Zeile" galt als **an**, ausdrücklich so entworfen, um
das Verhalten bestehender Nutzer nicht zu ändern.

Damit war er technisch ein **Opt-out**, sah in der Oberfläche aber aus wie eine
Liste getroffener Entscheidungen. Sieben Symbole standen auf „An", ohne dass
sie je jemand eingeschaltet hätte: **BNB, BTC, ETH, HYPE, KAIA, SUI, TAO**.
Vier der zwölf Hebel-Signale des Vormittags kamen aus dieser Gruppe.

**Zwei Änderungen, die nur zusammen richtig sind:**

| | |
|---|---|
| `_migrate_hebel_schalter_geradeziehen()` | schreibt für jedes Krypto-Asset ohne Zeile den bisher **geltenden** Wert — „an" |
| `get_hebel_pruefung_erlaubt()` | gibt ohne Zeile jetzt **False** |

> ⚠️ **Wer die Vorgabe umdreht ohne die Migration, schaltet sieben laufende
> Assets still ab.** Deshalb läuft die Geradeziehung in `init_db()` — beim
> App-Start, also vor dem Scheduler.

**Am Verhalten ändert sich heute nichts.** Gegengeprüft an der NB-Kopie:

```
AUSGANGSLAGE: 43 Krypto-Assets, 7 ohne Zeile
Migration hat 7 Zeilen ergaenzt: BNB, BTC, ETH, HYPE, KAIA, SUI, TAO

OK  KEIN Symbol hat sich veraendert          ({})
OK  kein bestehendes AUS wurde zu AN         (19 bleiben aus)
OK  jedes Krypto-Asset hat jetzt eine Zeile  (kein unentschiedener Fall mehr)
OK  EURCV (Cash) bekam KEINE Zeile
OK  ein NEUES Asset ohne Zeile ist jetzt AUS
OK  ein zweiter Lauf aendert nichts
```

**Was sich ab jetzt ändert:** ein Asset, das neu in die Watchlist kommt, wird
**nicht mehr stillschweigend gehebelt**. Der Nutzer schaltet es ein, wenn er
will — und in der Oberfläche ist ab sofort jedes „An" eine festgehaltene
Entscheidung, keine Vorgabe.

**Cash-Äquivalente bleiben außen vor.** Für EURCV gibt es keine Hebelfrage,
also auch keine Antwort, die man festhalten müsste — dieselbe Bedingung wie in
`ui/app.py` und seit 26.9 auch in der Kette.

> **Nebenbefund, nicht behoben:** der Schalter wird im **Trockenlauf
> übersprungen** (`if betriebsart != TROCKEN`). Kein Produktionsfehler — im
> Gate stehen 34 Verluste mit genau dieser Begründung —, aber jeder
> Trockenlauf überschätzt damit den Durchsatz, auch die, mit denen der
> Vollumstieg geprüft wurde.

### 26.11 Der Richtungsschalter — und warum mein erster Vorschlag falsch war

Nutzerfrage: *„prüfe zusätzlich, ob der Schalter für short only in der GUI sauber integriert ist."*

**Befund: er war in der Rollen-Kette gar nicht integriert.** `hebel_richtung_modus`
stand in keinem ihrer Module. Gleichzeitig bietet der Trader-Prompt SHORT
ausdrücklich an (`"richtung": "LONG|SHORT"`) — ein SHORT-Hebelsignal der neuen
Kette wäre trotz `nur_long` verschickt worden.

> ⚠️ **Mein erster Vorschlag war, SHORT im Prompt nicht anzubieten. Der Nutzer
> hat gestoppt und auf die Doku verwiesen — zu Recht.** Genau dieser Zustand
> bestand bis zum 05.08. und wurde in fünf Schritten entfernt, weil er
> **313 SHORT-Vorschläge als „HALTEN" in die Datenbank gelegt** hatte. Beim
> 31.07.-Bruch hat das einen ganzen Tag gekostet.

**Die verbindliche Fassung** (Entscheidungslog, 05.08., Nutzervorgabe wörtlich):

> der Schalter soll „NULL Einfluss auf die Funktionsweise im Hintergrund"
> haben — SHORTs sollen lediglich nicht per E-Mail kommen und nicht in der GUI
> erscheinen.

Es blieben **genau zwei Lesestellen**, beide an der Präsentationsgrenze. Die
Rollen-Kette brauchte die dritte — an derselben Grenze, nicht davor.

**Gebaut:** `_ist_email_relevante_richtung()` ist nach
`agent/asset_schalter.py` gezogen (`mail_richtung_erlaubt`), zu den übrigen
Nutzerschaltern; `background.py` delegiert dorthin und behält seinen Namen,
weil ein Dutzend Kommentare darauf verweisen. **Eine Definition, zwei Ketten.**

In der Kette sitzt die Frage **nach** dem Schreiben des Signals: das Modell
wurde gefragt, die Zeile steht mit echter `richtung` und echter `action`, das
Gate zählt sie als durchgekommen, der Ausgang wird verfolgt. Nur die Mail
unterbleibt — mit Logzeile und Vermerk in `mails_unterdrueckt`.

**Beide Versandstellen** sind abgesichert (mit und ohne Z.ai) — eine allein
hätte die Mail durchgelassen, sobald die zweite Meinung antwortet.

### 26.12 Alle offenen Punkte, Stand 15.08.2026 abends

**Zur Entscheidung beim Nutzer:**

| Nr. | Punkt | Stand |
|---|---|---|
| **O-17** | Einmalkauf 800 € für Börsenwerte | vorerst so belassen |
| **O-32** | Hebelfaktor 10,0 nie entschieden | vorerst so belassen |
| — | Hebel-Cooldown 3,5 h (295 von 385 Aufrufen) | vorerst so belassen |

Alle drei ausdrücklich **stillgestellt, nicht bestätigt** — sie werden
entschieden, wenn es Zahlen gibt (Kapitel 25.4).

**Gebaut, wartet auf Messung:**

| Nr. | Punkt |
|---|---|
| **O-29** | Verkaufsrate — kein gemessenes Merkmal trennt Verkaufen von Halten |
| **O-30** | Kontingent zählt HTTP-Versuche, die Budgetrechnung zählt Urteile (gemessen: 195 gegen 102, Faktor 1,9) |
| — | CRV-Abstufung stillgelegt — messbar, sobald aufgelöste Signale vorliegen |
| — | `stop_zu_eng` wird von **niemandem** gelesen. Nach 26.8 keine Lücke mehr, sondern eine Messgröße für O-34: **7 von 23** Modellvorschlägen lagen unter dem Grundrauschen |

**Geplant, in dieser Reihenfolge:**

| Nr. | Punkt |
|---|---|
| **O-34** | Die Fakten und Entscheidungen der LLM aufschlüsseln (`messe_begruendungen.py`) — **zuerst** |
| **O-36** | **Anlass statt Uhr.** Fingerabdruck des Faktentextes; ist er zeichengleich, ist es dieselbe Frage. Dazu eine 24-Stunden-Decke, damit nie dauerhaft blockiert wird. **Zuerst nur messen, nicht sperren** — dann kennen wir die Wirkung, bevor wir sie einschalten |
| **O-33** | Hedge-Instrumente ohne Codeeingriff |
| **O-35** | **Der Hebel-Tab liest `hebel_signals` — die alte Tabelle.** Die neue Kette schreibt nach `signals`; auf der Hebelseite ist die Oberfläche seit dem Umstieg leer. Das ist zugleich die Anzeige-Hälfte des Richtungsschalters |
| **O-37** | **Der Ausstieg läuft über zwei Schienen.** Der deterministische Ausstieg hatte TURBO bereits mit SCHLIESSEN; die LLM-Kette urteilte darüber noch einmal. Nutzervorgabe vom 14.08.: *„wenn ein Kurs den gewünschten Wert erreicht hat, brauche ich keine LLMs"* |
| **O-38** | **Der Trockenlauf überspringt die Nutzerschalter** (`if betriebsart != TROCKEN`). Kein Produktionsfehler, aber jeder Trockenlauf überschätzt den Durchsatz — auch die, mit denen der Vollumstieg geprüft wurde |

**Zu prüfen im nächsten Export:**

| Punkt |
|---|
| **TURBO trug eine offene Hebelposition, obwohl der Nutzer keine hält.** `hebel_positions` wird ausschließlich vom Bitpanda-Margin-Sync geschrieben, und eine Verkaufsmail braucht zwingend Menge > 0 — um 06:19 gab es keine einzige offene Position. Verdacht: eine hängengebliebene Zeile (dafür existiert `fix_stuck_hebel_positions.py`). Nachzusehen: Status, `eroeffnet_am`, `letzte_transaktion_unix_timestamp`, `quelle_tags_json` und die Sync-Zeilen im Log |
| Kommen noch „SCHLIESSEN ohne Bestand"? Das waren 9 % der Aufrufe |
| Verschieben sich die Ausstiegsempfehlungen? Der Stop in der Zeile ist seit 26.8 weiter, und `ausstiegsrechnung` rechnet darauf |
| Läuft ASTER ohne Absturz durch |

---

## Kapitel 27 — Der Lauf nach den sieben Fixes (15.08.2026, NB-Export 13:04)

### 27.1 Was die Fixes gebracht haben

| | vor den Fixes | nach dem Pull |
|---|---|---|
| „SCHLIESSEN ohne Bestand" | 4 (**15 %** der Urteile) | **0** |
| Signale heraus | 0 | 20 |
| ASTER-Abstürze | 16 seit 14.08., zuletzt 08:45 | **keiner** |

Alle drei greifen.

### 27.2 TURBO war kein Phantom — der Betreff log

```
10:04:15 UTC   Signalzeile:  TURBO  ERÖFFNEN  hebel=3,8  500 EUR
12:06:56 lokal Mailbetreff:  TURBO - SCHLIESSEN (Hebel)
```

Dieselbe Empfehlung, 2:41 Minuten auseinander — die Wartezeit auf Z.ai. Der
Margin-Sync meldete um 12:00 ausdrücklich **0 Positionen**.

Die Ursache stand in `signal_mail.py`: der Betreff übernahm die
**deterministische Ausstiegsempfehlung**, sobald sie mit SCHLIESSEN beginnt —
ohne Rücksicht darauf, ob die Mail überhaupt von einem Ausstieg handelt.

> ⚠️ Der Nutzer liest „TURBO schließen" und findet im Text einen Plan, 500 €
> gehebelt zu eröffnen. **Zweimal an einem Vormittag.**

### 27.3 Drei Stimmen, zwei Meinungen

Der Mailtext hatte längst recht — er schreibt in genau diesem Fall *„Kein
zusätzlicher Einstieg: der Ausstieg steht auf SCHLIESSEN"* und zeigt Zone,
Stop und Ziel gar nicht erst.

**Die Signalzeile wurde trotzdem als ERÖFFNEN über 500 EUR geschrieben.**

    Der Text sagte nein, die Datenbank sagte ja.

Und gemessen wird die Datenbank: die Trefferbilanz hätte diese Zeilen als
Einstiege gezählt, die nie empfohlen wurden.

**Und es war kein Grenzfall.** Von den sieben Symbolen, deren
Ausstiegsrechnung SCHLIESSEN sagte, bekamen **sieben** eine
Eröffnungsempfehlung: ALGO, ETH, INJ, SUI, TAO, TURBO, VIRTUAL.

### 27.4 Was gebaut wurde

**Der Betreff nennt die Aktion dieser Mail.** Die Dringlichkeit bleibt, wo sie
etwas aussagt: bei HALTEN und NICHTS_TUN beschreibt die Ausstiegsempfehlung
tatsächlich, was zu tun ist. Bei einem Einstieg beschreibt sie das Gegenteil —
dort steht sie weiter im Text, im Abschnitt „2. DIE POSITION" **vor** dem
Urteil des Modells.

**Kein Einstieg, wo der Ausstieg fällig ist.** Die Kette bucht das Urteil als
Nein-Fall mit gerechneten Zonen — der Messwert bleibt, die widersprüchliche
Mail entfällt.

> Das ist **kein Qualitätsfilter** und braucht keine Prognose. Er behauptet
> nicht, dass der Einstieg schlecht wäre — er stellt fest, dass die Nachricht
> ihn ohnehin verweigert. Eine Empfehlung, die im eigenen Text zurückgenommen
> wird, trägt keine Information.

**Nur bei einem echten Bestand.** `ist_bestand` unterscheidet die offene
Position von der alten Signalzeile: von den neun SCHLIESSEN-Zeilen bezogen
sich **nur drei** auf einen tatsächlichen Bestand. Eine abgelaufene Empfehlung
von vorletzter Woche darf keinen neuen Einstieg verhindern.

**Und die Führung wird je Symbol UND Instrument nachgeschlagen.** Die Liste
enthält eine Zeile je *Signal*, nicht je Position — TURBO stand zweimal darin
(Spot und Hebel), VIRTUAL ebenfalls. Die alte Schleife schrieb beide in
denselben Schlüssel; es gewann, was zufällig zuletzt kam. Drei Aufrufer, jetzt
eine Nachschlagestelle.

### 27.5 Was der Lauf sonst zeigte

> ⚠️ **Elf SHORT-Signale, und die Mails sind hinausgegangen** — ONDO, NEAR,
> RENDER, SOL, KAITO, ALGO, INJ, SUI. Im Betreff stand nichts davon.
> **Bitpanda kann gehebelte Shorts nicht ausführen.** Der Fix lag zu diesem
> Zeitpunkt fertig im Repo, der Nutzer hatte davor gepullt — deshalb null
> Unterdrückungszeilen im Log.

**Die Leerlaufwache schlug 11-mal an** („8 Aufrufe in Folge ohne Ergebnis").
Sie tut, was sie soll — aber die meisten Umläufe enden vorzeitig. Das ist
Cooldown plus NICHTS_TUN, und genau das Bild, auf das O-36 zielt.

**Drei Symbole doppelt** im Mailfenster (HYPE, BEAMX, SOL) · **O-30 erneut**:
Gemini 320 gesamt gegen 227 über die Einzelmodelle, Faktor 1,41 · **40 ×**
`remote.status`: Statusaufbau über der eigenen Schwelle · **ein Job
übersprungen** (12:13, `hebel_screening_job` lief noch).

### 27.6 Gegenprüfung

| | |
|---|---|
| Betreff und Text am echten TURBO-Fall | 11 von 11 |
| Paketprüfungen | **813, alle bestanden** |
| Bestehende Prüfung umgeschrieben | 1 — sie hielt das alte Betreffverhalten fest |

Die umgeschriebene Prüfung verlangte *„ein fälliger Ausstieg steht im
BETREFF"* — auch auf einer Kaufmail. Die Sorge dahinter war richtig, die
Umsetzung nicht. Sie prüft jetzt beides: dass der Betreff die Aktion dieser
Mail nennt **und** dass der fällige Ausstieg vor dem Urteil im Text steht.


---

## Kapitel 28 — O-35, und ein Schweigen von zwei Vormittagen (15.08.2026)

### 28.1 Der Fund, der O-35 unterbrach

Beim Bauen der Hebel-Tab-Abfrage kam die Frage auf, ob Schattenzeilen aus dem
Hebel-Lauf die Hebelspalte tragen. Die Antwort war schlimmer als erwartet:

```
Zeilen heute gesamt: 69   ·   gate_passed: alle 1
ist_reines_llm_halten: keine einzige
```

Bei **67 Nein-Urteilen** im Gate. Und in der Historie:

> **809 Nein-Zeilen bis 14.08. 17:55 — danach keine einzige.**

Reproduziert:

```
SOL: name 'assetklasse' is not defined
```

`_schreibe_nein()` ist eine eigene Funktion und rief `_kostenklasse(assetklasse)`
auf — einen Namen, den nur `_ein_asset` kennt. Der breite Fehlerfang legte das
in `ergebnis["nein_fehler"]`, **und das liest niemand.**

### 28.2 Zum dritten Mal dieselbe Falle

| | Name | Wirkung |
|---|---|---|
| 14.08. | `VK` | jedes Symbol lief in den Fehlerzweig |
| 15.08. | `_wl` | vor dem Betrieb gefunden |
| 15.08. | **`assetklasse`** | **zwei Vormittage ohne eine einzige Nein-Zeile** |

Der dritte war der teuerste, weil er nichts umbrachte, sondern schwieg. Damit
fehlte genau der Arm, der die Frage des Nutzers beantworten sollte — *„sind die
Signale Würfel mit Bonusinfo?"* — denn ob das **NEIN** des Modells besser ist
als der Zufall, misst man nur an den Nein-Fällen.

**Drei Konsequenzen:**

1. `assetklasse` ist jetzt Parameter, an beiden Aufrufstellen übergeben.
2. Der Fehler wird **geloggt**, nicht nur gesammelt. *„Fail-soft ist
   fail-silent"* steht seit dem 02.08. als stehende Vorgabe — diese Stelle war
   der Beweis.
3. Und die Schattenzeile bekommt das **Instrument**: seit die Hebelspalte am
   Instrument hängt statt am Wert, hätte eine Nein-Zeile aus dem Hebel-Lauf als
   Spot gegolten — der Hebel-Cooldown hätte sie nie gefunden.

### 28.3 Ein Werkzeug statt einer weiteren Reparatur

`finde_freie_namen.py` liest den Syntaxbaum und vergleicht je Funktion die
benutzten gegen die gebundenen Namen. Kein Ausführen, keine Abhängigkeiten
(Methodik 2.21, als Dauerprüfung in Paket T4b).

**Es fand zwei weitere schlafende Fehler:**

- `json` war in `scheduler/background.py` **nirgends importiert**. Nie
  aufgefallen, weil der Kanarienvogel einen Mistral-Client braucht und Mistral
  seit dem 07.08. nicht mehr läuft.
- `ui/app.py` rief `ist_hedge_instrument()` **ohne Import** — ein NameError
  beim Anlegen eines ETF-Assets.

Dazu fünf Zeilen toter Code in `regime.py`, hinter einem `return`.

> Die Prüfung brauchte selbst zwei Anläufe: die erste Fassung benutzte `os`
> ohne Import — genau der Fehler, den sie sucht.

### 28.4 O-35 — der Hebel-Tab sieht beide Ketten

Er las ausschließlich `hebel_signals`, die Tabelle der **alten** Kette. Die
Rollen-Kette schreibt nach `signals` mit gesetzter `hebel`-Spalte. Seit dem
Vollumstieg war der Tab auf der Hebelseite **leer**, während im Hintergrund
weiter Hebel-Signale entstanden.

`get_latest_rollen_hebel_signal_per_symbol_and_richtung()` liest sie, mit
**demselben Diskriminator** wie die Töpfe (`toepfe.sql_bedingung("hebel")`) —
eine eigene `hebel IS NOT NULL`-Kopie wäre die vierte Wahrheit über dieselbe
Sache gewesen.

**Was fehlt, wird nicht erfunden.** Von den 107 Feldern eines `HebelSignal`
füllt die neue Kette 88; die übrigen 19 sind Größen der alten Pipeline
(`trigger_score`, `eigenkapitalbedarf_eur`, `liquidationspreis_*`,
`kontrathese_*`). Sie bleiben leer statt eine Zahl zu zeigen, die niemand
gerechnet hat. Zwei werden umbenannt, weil dieselbe Sache anders heißt:
`hebel` → `hebel_final`, `modell` → `llm_model`.

**Die jüngere Zeile gewinnt** je (Symbol, Richtung) — ein fester Vorrang einer
Tabelle wäre eine Behauptung über die Zeit.

### 28.5 Und die WAL-Dateien, nochmal

`*.db` in der `.gitignore` trifft `*.db-wal` **nicht** — „.db-wal" endet nicht
auf „.db". Am 14.08. sind die Dateien deshalb mit einem `git add -A` ins Repo
gelangt; ich hatte damals notiert, sie seien in die `.gitignore` aufgenommen.
**Das stimmte nicht.** Jetzt stehen sie darin, mit Begründung.

### 28.6 Gegenprüfung

| | |
|---|---|
| Suche nach freien Namen | **0 Kandidaten** (vorher 7) |
| Nein-Zeile Spot / Hebel | geschrieben, `hebel=None` / `hebel=2,1` |
| Hebel-Tab, beide Quellen | zusammengeführt, jüngere gewinnt |
| Paketprüfungen | **818, alle bestanden** |

Die Nein-Zeile ist an beiden Instrumenten belegt: `ist_reines_llm_halten=1`,
`gate_passed=0`, und im Hebel-Lauf mit gesetzter Hebelspalte.


---

## Kapitel 29 — O-34: welcher Faktenblock trägt? (15.08.2026)

### 29.1 Zuerst die Zuordnung reparieren, dann messen

Der erste Lauf meldete **19 % nicht zuordenbar** — und das Werkzeug sagt selbst,
was das heißt: *steigt dieser Anteil, ist die Zuordnung veraltet und nicht etwa
die Datenlage schlecht.* Die sechzig unzugeordneten Belege waren drei klar
erkennbare Gruppen:

| Gruppe | Beispiel aus dem Lauf | gehört zu |
|---|---|---|
| Lagebild-Prosa | *„der Krypto-Sektor befindet sich in einer Schwächephase"* | `lagebild` |
| eigene Wortwahl des Modells | *„HYPE 60-Tage-Entwicklung bei −17,0"* | `bewegung` |
| Absicherungssätze | *„Gesamtexposure von 8.915 EUR"* | **fehlte ganz** |

Der dritte Fall ist der interessanteste: **Paket 14 ist vom 15.08., die
Zuordnung vom 14.08.** Der Absicherungsblock existierte im Werkzeug nicht.

Nach der Korrektur: **3 % nicht zuordenbar.** Erst damit ist die Rangfolge
belastbar.

### 29.2 Die Verteilung — 70 Signale, 319 Belege

| Block | Kauf | Verkauf | Summe |
|---|---|---|---|
| struktur | 58 | 22 | **80** |
| finanzierung | 44 | 12 | 56 |
| bewegung | 38 | 12 | 50 |
| marken | 33 | 13 | 46 |
| volumen | 27 | 5 | 32 |
| lagebild | 16 | 7 | 23 |
| bestand | 4 | 16 | 20 |
| unbekannt | 7 | 3 | 10 |
| absicherung | 2 | 0 | 2 |

### 29.3 Und die eigentliche Frage: WO wird zitiert?

Die Gesamtliste sagt, wie oft — nicht wo. Deshalb schlüsselt das Werkzeug jetzt
nach Instrument auf, **Belege je Zeile** (absolut gewinnt sonst die größere
Gruppe):

| Block | hebel | spot |
|---|---|---|
| struktur | 1,22 | 1,08 |
| **finanzierung** | **1,00** | **0,63** |
| bewegung | 0,66 | 0,76 |
| marken | 0,75 | 0,58 |
| volumen | 0,50 | 0,42 |
| lagebild | 0,16 | **0,47** |
| bestand | 0,03 | **0,50** |

**Drei Befunde:**

**Die Finanzierungsrate wird in 63 % der Spot-Entscheidungen zitiert.** Sie ist
eine Größe des Terminmarkts — bei einem Spot-Kauf zahlt und bekommt man sie
nicht. `baue_fall()` liefert den Block unabhängig vom Instrument, und das
Modell nutzt ihn. Als Stimmungsmaß ist das vertretbar, als *Kostenargument*
nicht. **Das ist der erste Kandidat für eine Prompt-Entscheidung** — und die
erste, die auf einer Messung stünde statt auf einer Annahme.

**Der Bestandsblock arbeitet genau richtig herum:** 0,50 je Spot-Zeile gegen
0,03 im Hebel-Lauf. Nach dem Fix vom 15.08. sieht der Hebel-Lauf korrekt „keine
offene Hebelposition" — es gibt dort schlicht nichts zu zitieren.

**Das Lagebild wird im Spot dreimal häufiger zitiert als im Hebel** (0,47 gegen
0,16). Es kostet acht Modellaufrufe am Tag. Ob sich das trägt, ist noch nicht
entschieden — es speist auch den `gleichlauf`, nicht nur die Belege.

### 29.4 Was noch nicht messbar ist

**Ein einziges aufgelöstes Signal.** Die Erfolgsspalte steht im Bericht, aber
sie sagt nichts: *„100 % Trefferquote"* über n = 1 ist keine Aussage. Die
Verteilung ist da, der Erfolg braucht Wochen — genau die Trennung, die das
Werkzeug von Anfang an ausweist.

### 29.5 Gegenprüfung der beiden vorigen Umsetzungen — an echten Daten

Nicht meine eigenen Tests wiederholt, sondern der Produktionslauf vom 15.08.
durchgerechnet: **hätten die Änderungen dort genau das getan, was sie sollen?**

**O-37, die Einstiegssperre:**

```
50 Einstiege am 15.08.
  gesperrt worden waeren:              2  (ETH/spot, TURBO/hebel)
  unveraendert durchgegangen:         48
  OHNE die Bestandspruefung:          13
```

> ⚠️ **Korrektur einer eigenen Zahl.** Ich hatte gemeldet: *„von sieben
> Symbolen mit SCHLIESSEN bekamen sieben eine Eröffnungsempfehlung"*. Das war
> auf **Symbolebene** und schloss Ausstiegsempfehlungen zu **alten
> Signalzeilen ohne Position** ein. Auf der Ebene, auf der die Sperre wirklich
> arbeitet — (Symbol, Instrument) und echter Bestand —, sind es **2 von 50**.
> Die Richtung des Befundes bleibt, die Größenordnung war zu hoch.

Damit ist die Präzisierung nachträglich belegt: ohne `ist_bestand` hätte die
Sperre **13 statt 2** Einstiege getroffen — der Rest wären alte Zeilen ohne
Gegenstand gewesen.

**O-35, der Hebel-Tab:**

```
115 Rollen-Zeilen, davon 32 mit Hebel und Richtung
  erwartete Paare (Symbol, Richtung):  22
  von der Abfrage geliefert:           22
```

Keine Spot-Zeile dabei, je Paar die jüngste, `hebel` → `hebel_final`, `modell`
→ `llm_model`, und `trigger_score`/`eigenkapitalbedarf_eur` bleiben leer statt
erfunden.

**12 von 12 bestanden**, dazu 818 Paketprüfungen.


---

## Kapitel 30 — O-36: der Anlass, als Messung ohne Sperre (15.08.2026)

### 30.1 Der Grundansatz kommt vom Nutzer

> *„warum eine neue Bewertung und Signal, wenn sich nichts geändert hat … nach
> einer 1. Bewertung kommt erst eine 2., wenn sich an den Grundlagen und
> Kriterien etwas geändert hat … damit nichts blockiert wird, die Prüfung nur
> eine bestimmte Zeit, z. B. 24 Stunden."*

**Das ist kein Qualitätsfilter und braucht keine Prognose.** Er behauptet
nicht, ein Trade werde gut — er stellt fest, dass dieselbe Frage auf denselben
Daten keine neue ist. Der Unterschied ist entscheidend, weil dieses Projekt an
8.441 Fällen gemessen hat, dass **kein Verfahren die Basisrate schlägt**. Ein
Rang nach erwarteter Güte wäre eine Behauptung gegen den eigenen Grundbefund;
*„das haben wir schon gefragt"* ist keine.

Die Messgrundlage steht ebenfalls im Projekt: **ein Modell dreht bei
bitgleicher Eingabe in etwa 12 % der Fälle die Richtung.**

### 30.2 Der Fingerabdruck ist der Prompt selbst

Keine Schwelle auf dem Kurs — die wäre wieder eine gesetzte Zahl. Der
Faktentext rundet ohnehin (*„1.093 EUR wert", „−35,7 %"*), bildet also genau
die Auflösung ab, die das Modell sieht. **Ist der Text zeichengleich, ist es
wörtlich dieselbe Frage.**

**Zwei Abdrücke, weil die richtige Definition noch nicht feststeht:**

| | umfasst |
|---|---|
| `voll` | alles, was das Modell liest — samt Lagebild-Prosa |
| `asset` | nur die Fakten dieses Assets, ohne Lagebild |

Der Unterschied ist keine Feinheit: das Lagebild ist Modellprosa und wechselt
alle drei Stunden. Nähme man es mit, wäre fast jede Frage „neu" und der Filter
wirkungslos. **Welche der beiden die richtige ist, soll die Messung sagen und
nicht ich.**

### 30.3 Was gebaut wurde

`agent/anlass.py` schreibt bei jedem Urteil eine Beobachtung: beide Abdrücke,
ob sie mit der letzten innerhalb von 24 Stunden übereinstimmen, und den
zeitlichen Abstand. Die Stufe sitzt **direkt vor dem Modellaufruf** — dort, wo
später auch die Sperre säße. Wer die Wirkung woanders misst als da, wo er sie
einbauen würde, misst etwas anderes.

`messe_anlass.py` liest die Tabelle und beantwortet die Frage, die vor der
Entscheidung fehlt:

    Greift der Filter in 5 % der Fälle, lohnt er nicht.
    Greift er in 60 %, stellt die Kette dieselbe Frage sechsmal.

### 30.4 Sie sperrt nichts — und das ist statisch bewiesen

> ⚠️ **Meine erste Gegenprüfung hat das Falsche geprüft.** Sie verglich zwei
> Trockenläufe und stellte fest, dass sie gleich ausgehen. Nur läuft die Stufe
> im Trockenlauf **gar nicht** (`if betriebsart != TROCKEN`, weil sie in die
> Datenbank schreibt). Der Vergleich zeigte also, dass die *abgeschaltete*
> Stufe nichts tut.

Der belastbare Beweis ist statisch: **der Befund steht in `rollen_lauf.py` in
keiner einzigen Bedingung.** Was in keiner Bedingung steht, kann nichts
sperren — unabhängig von der Betriebsart. Sechs Erwähnungen von `anlass` in der
Kette, alle Sammeln oder Fehlerbehandlung, keine Verzweigung.

### 30.5 Gegenprüfung

| | |
|---|---|
| gleiche Fakten → gleiche Abdrücke | OK |
| neues Lagebild ändert `voll`, **nicht** `asset` | OK |
| geänderte Assetfakten ändern **beide** | OK |
| Reihenfolge der Schlüssel zählt nicht | OK |
| erste Frage ist nie eine Wiederholung | OK |
| dieselbe Frage 15 min später wäre gesperrt | OK |
| **nach 24 h wieder eine neue Frage** | OK |
| Spot und Hebel werden **getrennt** geführt | OK |
| jede Frage wird mitgeschrieben, auch die gesperrten | OK |
| **der Befund wird nirgends gelesen** | OK |

**15 von 15**, dazu **823 Paketprüfungen** und null freie Namen.

### 30.6 Was jetzt zu tun ist: nichts

Die Stufe läuft mit, sobald die Produktion wieder anläuft. Nach ein paar Tagen
sagt `messe_anlass.py`, wie oft der Filter gegriffen hätte — getrennt nach
Instrument, mit den Symbolen, die sich am häufigsten wiederholen, und mit dem
Abstand zur vorigen Frage.

**Erst dann steht die Entscheidung auf einer Messung statt auf einer
Schätzung.** Das ist der ganze Zweck der Messvariante.


---

## Kapitel 31 — O-30: es gab keinen Mehrverbrauch (15.08.2026)

### 31.1 Die Behauptung

O-30 stand seit dem 14.08. so im Plan:

> *„meine Budgetrechnung zählte URTEILE, das Kontingent zählt HTTP-VERSUCHE.
> Die Buchung `zaehle_aufruf` steht INNERHALB der Wiederholschleife von
> `api/gemini.py` — jeder 429- und 503-Versuch bucht mit."*

Belegt hatte ich das mit zwei Zahlenpaaren: **195 gegen 102** (Faktor 1,9) und
später **320 gegen 227** (Faktor 1,41).

### 31.2 Beides war dieselbe Verschiebung

| Tag | `gemini` (UTC) | Summe `gemini:*` (Pazifik) | Differenz |
|---|---|---|---|
| 14.08. | 802 | 895 | **−93** |
| 15.08. | 320 | 227 | **+93** |

**Exakt spiegelbildlich.** Die beiden Zähler buchen dieselben Ereignisse —
beide stehen in derselben Wiederholschleife — und unterscheiden sich **nur in
der Tagesgrenze**: `gemini` auf UTC, `gemini:<modell>` auf Googles Pazifik-Tag.
Zwischen 00:00 und 09:00 CEST liegen die Aufrufe im UTC-Tag von heute und im
Pazifik-Tag von gestern. Das sind die 93.

> ⚠️ **Und die Erklärung stand die ganze Zeit im Export**, ein Feld weiter:
> *„source `gemini:<modell>` zählt auf Googles Pazifik-Tag …; source `gemini`
> zählt auf UTC-Tag."* Ich habe sie zweimal nicht gelesen und aus dem
> Zahlenvergleich einen Befund gemacht.

### 31.3 Was tatsächlich stimmt

| | |
|---|---|
| Trader-Urteile im Pazifik-Tag 15.08. | 216 |
| Gemini-Versuche im selben Fenster | 227 |
| **Versuche je Urteil** | **1,051** |
| Wiederholungen im Log | **0** |

Die elf zusätzlichen Aufrufe sind die **Lagebild-Aufrufe**, nicht Retries. Es
gab an diesem Tag keine einzige Wiederholung.

**Die Budgetrechnung war im Kern richtig.** Der Aufschlag beträgt 5 %, nicht
90 %.

Und beide Wächter lesen bereits den richtigen Zähler — `api/gemini.py` und
`scheduler/rollen_job.py` fragen `gemini:<modell>` auf dem Pazifik-Tag, also
genau den, der Googles Grenze abbildet.

### 31.4 Was trotzdem gebaut wurde

Nicht am Zähler — der stimmt. Sondern an der Stelle, die mich zweimal in die
Irre geführt hat: **der Export rechnet den Versatz jetzt selbst aus**
(`tagesgrenzen_versatz`, je Tag) und die Lesehilfe sagt ausdrücklich, dass die
beiden Zahlen **nicht vergleichbar** sind und eine Differenz **kein
Mehrverbrauch** ist.

> **Eine Erklärung, die daneben steht, wird überlesen.** Wer die Zahlen
> vergleicht, findet die Antwort jetzt an derselben Stelle wie die Frage.

### 31.5 Gegenprobe

| | |
|---|---|
| Differenzen heben sich exakt auf | −93 / +93 |
| beide Buchungen stehen in derselben Schleife | an der Quelle geprüft |
| beide Wächter lesen den Pazifik-Zähler | geprüft |
| Versuche je Urteil | 1,051 |
| Wiederholungen im Betrieb | 0 |
| Export rechnet und warnt | geprüft |

**9 von 9**, dazu 823 Paketprüfungen.

**O-30 ist damit geschlossen — nicht behoben, sondern widerlegt.**
