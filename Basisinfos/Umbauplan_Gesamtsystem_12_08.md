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

Stand: **46 Prüfungen** über Paket 0–3, alle bestanden. Kein LLM-Aufruf, kein
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
| **4** | **Thesen-Abgleich in die Rollen-Kette** | der dritte unabhängige Faktor (§5.3) |
| **5** | **Getrennte Töpfe** (§6a) | Spot · Hebel · Absicherung, keine Verrechnung untereinander |
| **6** | **Feldabbildung → `signals`** | neue Spalten für `unabhaengige_faktoren`, `umgeworfen_durch` |
| **7** | **Backward-Tracking auf die neuen Felder** | *jetzt* misst es wieder |
| **8** | **Trefferbilanz / Schrumpfung** (§6.4) | *jetzt* erst möglich — der Entscheider und damit der Filter |
| **9** | **Live-Lauf auf `gemini-3.1-flash-lite`** | Wortlaut zeigen. **Nicht 3.5** — alle bisherigen Messungen liefen auf 3.5 |
| **10** | **Gate** | Konfidenz-Schwelle entfällt (E3); Durchlässigkeit je Stufe zählen; Faktorzahl im Veto-Schatten |
| **11** | **Z1 + Z.ai** | Z1 verdrahten; Z.ai auf die neuen Fakten und die 5 Aktionen |
| **12** | **E-Mail + GUI** | Entscheider-Block, Fakten sichtbar machen, Hebel-Tab, **Regime-Tab auf den Score + Override** (E4) |
| **13** | **Hebel** (E2) | Richtung, Hebelfaktor, 7 Aktionen, Finanzierung, Liquidationsabstand |
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
| Wirkung | `min_konfidenz` + Konflikt-Veto | Score als **Fakt** an Rolle 1; Konflikt-Veto kehrt zurück, sobald es wieder eine Richtung gibt (Hebel, Paket 2) |
| **Override** | setzt das Etikett | **setzt den Score** — derselbe Hebel, feinere Auflösung |

Der Score ist gebaut, variiert 0,250–0,750 und trennt die Marktphasen. Der
Override wird dadurch **mächtiger**, nicht schwächer: statt vier Schubladen ein
Regler.

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
