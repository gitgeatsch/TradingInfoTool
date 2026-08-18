# Umbauplan Gesamtsystem — von der Rollen-Ebene zur Empfehlung (12.08.2026)

*Der Masterplan für den Umbau: WAS jede Rolle bekommt, was sie liefert, und
wie daraus eine Empfehlung für den Nutzer wird.*

> ⚠️ **Korrigiert am 16.08.2026.** Hier stand, dieser Plan löse
> `Rollenkonzept_Entwurf_10_08.md` *„nicht ab, sondern setze darauf auf: das
> Rollenkonzept sagt, WER urteilt"*. Das galt am 12.08. und gilt nicht mehr —
> jenes Dokument ordnet Funding, OI-Squeeze und Long/Short der **Rolle B** zu
> und kennt keine zweite Stufe. Genau diese Zuordnung wurde am 16.08.
> rückgängig gemacht.
>
> **WER urteilt, steht seit dem 17.08. verbindlich im `Regelwerksmanual.md`,
> Abschnitt R-R1 bis R-R5.** Das Rollenkonzept trägt einen Standvermerk und
> bleibt als Begründungsquelle stehen.

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



### 30.7 Nachtrag: ein Abdruck je Block — und warum es keinen Modellaufruf braucht

Nutzerfrage: *„warum brauchen wir einen LLM-Aufruf, das verstehe ich nicht — der
Hash kann ja deterministisch gebildet werden, oder?"*

**Richtig, und im Sperrbetrieb gibt es keinen.** Fingerabdruck rechnen, mit dem
letzten vergleichen, bei Gleichheit zurückkehren — der Aufruf findet nie statt.
Das ist die ganze Ersparnis; ein SHA-256 über ein paar Kilobyte kostet
Mikrosekunden.

**Dass heute trotzdem gerufen wird, liegt nicht an der Messung.** Die braucht
den Aufruf nicht, sie braucht nur den Hash. Gerufen wird, weil die Signale
weiter kommen sollen — *„erstmal so viele Daten wie möglich zulassen"*. Die
Stufe ist fertig gebaut und nur an einer Stelle nicht verdrahtet: scharf
schalten heißt, ein `if` mit `durchlauf.verloren(...)` und `return` zu
ergänzen.

**Die Anschlussfrage war die interessantere:** wenn eine Frage als „neu" gilt,
woran lag es?

Deshalb jetzt ein Abdruck **je Block** — bestand · struktur · bewegung · marken
· volumen · finanzierung (und absicherung, wo es sie gibt). Die Beobachtung
notiert, welche Blöcke sich geändert haben; `messe_anlass.py` zählt sie aus.

> **Der Verdacht, den das prüfen soll:** der Finanzierungsblock ändert sich bei
> Krypto **alle acht Stunden von selbst** — eine neue Funding-Periode
> verschiebt die Perzentile, ohne dass am Chart etwas geschehen ist. Er könnte
> den Filter ausgerechnet dort stumpf machen, wo er am meisten brächte. Und es
> ist derselbe Block, der laut O-34 in **63 % der Spot-Urteile** zitiert wird,
> obwohl er dort gar nicht anfällt.
>
> Ohne diese Aufschlüsselung wäre die Messung eine Zahl ohne Ursache. Der
> Bericht warnt selbst, wenn die Finanzierung mehr als die Hälfte der Fragen
> neu macht.

**Zwei Dinge waren dabei zu beachten:**

**Der Prompt darf sich nicht verändern.** Die Blöcke gehen als **Ausgang**
(`bloecke_ziel`) an der Messung vorbei — nicht als zusätzlicher Schlüssel in
den Faktensatz. Ein Feld mehr dort hätte alle bisherigen Messungen
unvergleichbar gemacht. Geprüft: der Faktensatz ist mit und ohne Abgriff
identisch.

**Und die Lage wird nur einmal gerechnet.** `beschreibe_lage()` rief `geteilt()`
bisher **innerhalb** der Schleife auf — sechsmal dieselbe Rechnung über
dieselbe Reihe. Jetzt einmal, und das Ergebnis geht weiter. Die Blöcke neu zu
rechnen wäre ohnehin ausgeschieden: die Finanzierung müsste dafür erneut an die
Börse.

### 30.8 Gegenprüfung, erweitert

| | |
|---|---|
| je Block ein eigener Abdruck | OK |
| nur der geänderte Block unterscheidet sich | OK |
| die Messung nennt den schuldigen Block | `['finanzierung']` |
| ein **weggefallener** Block zählt mit | `['marken']` |
| beides steht in der Zeile | OK |
| **Faktensatz mit und ohne Abgriff identisch** | OK |
| die Blöcke kamen trotzdem an | 6 Blöcke |
| der Befund wird nirgends gelesen | OK |

**23 von 23**, dazu **829 Paketprüfungen** und null freie Namen.
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


---

## Kapitel 32 — LLM-Optimierung, Fortsetzung: was die Rollen wissen und was ihnen fehlt (16.08.2026)

**Auftrag des Nutzers:** erheben, welche Werte und Parameter wir je Asset und
Handelsstrategie in die Prompts „übersetzen"; extern recherchieren, ob
Marktanalyst, Trader und Bewerter haben, was man in der Praxis braucht; und
dasselbe für die zweite Stufe (Z.ai) mit **anderen, selektierten** Werten.

### 32.1 Der erste Befund: Rolle C gibt es nicht

> ⚠️ **UMBENANNT 16.08.2026.** Was dieses Kapitel „Rolle C" nennt, heisst seit dem 17.08. **Rolle G — Gegenprüfer**. Der Buchstabe C war doppelt vergeben: das C in **„Rolle BC"** ist der Entscheider in LLM1 und hat mit Z.ai nichts zu tun. Der Kapiteltext bleibt im Wortlaut von damals stehen.

Der Nutzer: *„Es sollten drei sein — Marktanalyst 1. Stufe, 2. Stufe Trader und
Bewerter — A, B und C."*

**Der Code kennt nur A und BC.** In `llm_schema.py`, `entscheidungsrechnung.py`
und `gegenpruefer_rollen.py` heißt die zweite Rolle durchgehend „Rolle BC".
Beurteilen und Handeln wurden in **einen** Aufruf gelegt.

Was heute „Bewerter" heißt, ist **keine LLM-Rolle**, sondern Arithmetik:
`trefferbilanz.bewerte()` schlägt in der eigenen Trefferbilanz nach und rechnet
Basisrate gegen Breakeven. Das ist wertvoll — aber es ist kein Urteil, sondern
eine Division.

> **Damit fehlt die Instanz, die B widerspricht.** In der Literatur ist genau
> das der Punkt, an dem Mehragenten-Systeme ihren Nutzen ziehen: nicht durch
> mehr Meinung, sondern durch eine Rolle, die *gegen* die vorliegende
> Entscheidung argumentiert.

### 32.2 Bestandsaufnahme: was heute in welchen Prompt geht

**Rolle A — Marktanalyst (Lagebild), 1× je 3 Stunden, klassenübergreifend**

| Eingabe | Quelle |
|---|---|
| je Leitmarkt: Trend 250/60 Handelstage, Abstand zu Hoch/Tief, tägliche Schwankung + Perzentil, Umsatz-je-Bewegung + Perzentil | `marktlage.py` aus Kursreihen |
| Anlegerstimmung (Fear & Greed) — **nur Bitcoin** | `macro_snapshot` |
| Netto-Liquidität, Zinskurven-Spread | `lade_makro()` |

Ausgabe: Prosa · Einstufung je Klasse (günstig/gemischt/ungünstig) · 2–4 Belege.

**Rolle BC — Trader, 1× je Asset und Umlauf**

| Block | Inhalt | gilt für |
|---|---|---|
| `auftrag` | Instrument (spot/hebel/absicherung) + Strategie | alle |
| `bestand` | Menge, Einstand, G/V — **je Instrument** seit 15.08. | alle |
| `struktur` | Swing-Hochs/-Tiefs, Fenster benannt | alle |
| `bewegung` | 5 / 20 / 60 Handelstage | alle |
| `marken` | nächster Widerstand/Unterstützung in ATR, Berührungen | alle |
| `volumen` | Tagesumsatz gegen 20-Tage-Mittel, Aufwärtstage-Anteil | alle |
| `finanzierung` | Funding-Perzentil am Terminmarkt | **alle** — auch Spot |
| `absicherungslage` | Exposure, Deckung, Hebelfaktor | nur `absicherung` |
| Lagebild | Prosa + Einstufung **der eigenen Klasse** | alle |

> ⚠️ **Erster Befund aus O-34:** der Finanzierungsblock geht in **jeden**
> Prompt und wird in **63 % der Spot-Urteile** zitiert — obwohl er bei einem
> Spot-Kauf weder anfällt noch zahlbar ist.

**Was NICHT je Assetklasse oder Strategie unterschieden wird:** außer
`auftrag`, `bestand` und `absicherungslage` **nichts.** Eine Aktie bekommt
dieselben sechs Blöcke wie ein Memecoin — dieselben Fenster, dieselben
Perzentile, dieselbe Sprache.

### 32.3 Was das System rechnet und keiner Rolle gibt

| Fakt | Bestand | im Prompt? |
|---|---|---|
| Optionsmarkt (Deribit) | 1.163 Fakten, **1.149 mit Gegenargument** | nein |
| OI-Squeeze-Divergenz | 1.526 Fälle, fünf Zustände | nein |
| Funding-Perzentil | 1.909 | ja (überall) |
| Makro: DXY, Fed Funds, 10J-Rendite, CPI, Öl, S&P-Abweichung | laufend | nur A |
| Regime + Persistenz | *bär*, seit 27 Tagen | nein |
| BTC-Dominanz, Krypto-Relativwert | gebaut | nein |
| Bitpanda-Handelbarkeit, Spread | gebaut | nein |

**Der Umbau hat den Prompt von 34.611 auf 3.183 Zeichen gekürzt** — richtig
gegen den Deadloop, aber die weggefallenen Fakten sind nie wieder bewertet
worden.

### 32.4 Externe Recherche — was Praxis und Literatur vorsehen

**TradingAgents** (arXiv 2412.20138) bildet ein Handelshaus nach und trennt
**vier Analysten**, die *verschiedene Quellen* lesen:

| Rolle | bekommt |
|---|---|
| Fundamentalanalyst | Abschlüsse, Gewinne, Insider-Transaktionen |
| Stimmungsanalyst | Social Media, Sentiment-Scores, Insider-Stimmung |
| Nachrichtenanalyst | Nachrichten, **Makroindikatoren**, Ereignisse |
| Technischer Analyst | OHLCV + ~60 Indikatoren |

Darüber **Bull- und Bear-Forscher, die in Runden gegeneinander
argumentieren**, ein Trader, und ein **Risiko-Team aus drei Haltungen**
(risikofreudig, neutral, konservativ), das die Entscheidung des Traders prüft,
bevor sie gilt.

**FinMem** (arXiv 2311.13743) ergänzt eine geschichtete **Erinnerung** — der
Agent hält vergangene Fälle mit unterschiedlicher Verfallszeit vor und zieht
sie zur Entscheidung heran.

**Und zur zweiten Stufe die deutlichste Fundstelle:** ein Modell, das seine
eigene oder eine gleichartig erzeugte Ausgabe prüft, **rationalisiert
nachträglich, statt unabhängig zu prüfen**. Der Begriff dafür ist *Homogeneous
Debate*: teilen die Prüfer Modell, Trainingsverteilung oder **Informations­grenze**,
sinkt die epistemische Vielfalt und die Prüfung verliert ihren Wert. Verlangt
wird ein Prüfer mit **frischem Kontext und eigener Informationsquelle**.

### 32.5 Was uns fehlt — und was davon wir haben könnten

| Was die Praxis trennt | bei uns | Bewertung |
|---|---|---|
| Fundamentaldaten | fehlen ganz | bei Krypto kaum verfügbar, bei Aktien/ETF schon |
| Nachrichten | **fehlen ganz** | Memory: „Nachrichten" ist einer von drei Wegen, die das Vorzeichen drehen können |
| Stimmung | nur Fear & Greed, nur BTC, nur Rolle A | vorhanden, nicht verteilt |
| Technik | **vollständig** | unsere Stärke |
| Makro | nur Rolle A | gerechnet, beim Trader nicht |
| Positionierung (OI, Funding, Optionen) | gerechnet, **ungenutzt** | die größte ungehobene Menge |
| Bull/Bear-Streit | **fehlt** | wäre Rolle C |
| Risikoprüfung als eigene Instanz | deterministisch | Arithmetik statt Urteil |
| Erinnerung an frühere Fälle | Trefferbilanz als Zahl | keine Fallerinnerung |

### 32.6 Mein Vorschlag als Fachexperte — in dieser Reihenfolge

**Erst aufräumen, dann erweitern.** Jede neue Zeile im Prompt macht die
bisherigen Messungen unvergleichbar; deshalb zuerst das, was nachweislich
falsch ist.

**Schritt 1 — Finanzierung nur dort, wo sie anfällt.** Gemessen, begründet,
kostet nichts. Der Block gehört in den Hebel-Prompt, nicht in den Spot-Prompt.

**Schritt 2 — Rolle C bauen, als Gegenrede.** Nicht als zweiter Trader,
sondern als die Instanz, die der vorliegenden Entscheidung **widerspricht**:
sie bekommt den Befund von B **und** die Fakten, die B nicht hatte, und nennt
den stärksten Einwand. Das ist die Rolle, die der Nutzer immer gemeint hat —
und die Literatur sagt, dass sie nur trägt, wenn sie eine **eigene
Informationsgrundlage** hat.

**Schritt 3 — die zweite Stufe (Z.ai) wird diese Rolle C.** Damit ist die
Frage „was macht Z.ai" beantwortet: nicht dieselbe Frage noch einmal, sondern
die Fakten, die sonst niemand liest.

| Z.ai bekommt | Z.ai bekommt NICHT |
|---|---|
| Optionsmarkt-Gegenargument (Deribit) | die Kursstruktur, die B schon hatte |
| OI-Squeeze-Zustand | die Begründung von B |
| Funding-Extremwerte | das Lagebild |
| Regime + Persistenz | |
| geplante Aktion, Richtung, Hebel | |

Eine Frage: **„Spricht in diesen Daten etwas gegen diesen Trade?"** Ein
Aufruf statt vier.

**Schritt 4 — Nachrichten.** Die einzige echte Informationsquelle, die uns
ganz fehlt, und laut eigenem Grundbefund einer von drei Wegen, die das
Vorzeichen drehen können. Aufwendig, deshalb zuletzt — aber nicht vergessen.

### 32.7 Drei Bedingungen für jeden dieser Schritte

**Es muss unterscheiden.** Der Richtungsabgleich sagte in 2.469 Prüfungen
1.246× SHORT, 1.206× NEUTRAL und **17× LONG**. Ein Merkmal, das fast immer
denselben Wert hat, kann nichts trennen — Regel R-T6. Jede neue Rolle wird ab
Tag eins auf ihre Verteilung gemessen.

**Es darf nicht überstimmen.** Ein Einwand steht in der Mail und in der Zeile;
er kippt die Empfehlung nicht. Nutzervorgabe vom 29.07., unverändert gültig.

**Es muss auflösbar sein.** Eigene Spalte, Ausgang verfolgt, Trefferquote gegen
die Basisrate — wie jede andere Behauptung in diesem System.

### 32.8 Was zuerst zu erheben ist, bevor gebaut wird

Diese Aufstellung ist aus dem Code gezogen, nicht aus der Erinnerung. Was
fehlt, ist die **Wirkungsmessung je Block**: O-34 misst, welcher Block zitiert
wird, aber noch nicht, welcher etwas **ändert**. Dafür braucht es aufgelöste
Signale mit Belegen — die laufen seit dem 14.08. auf.

**Vor Schritt 2 und 3 steht deshalb die O-34-Auswertung mit Ausgängen.** Erst
sie sagt, ob die vorhandenen Blöcke tragen — und eine Rolle C auf einer
Faktenbasis zu bauen, von der wir nicht wissen, ob sie trägt, wäre derselbe
Fehler noch einmal.


---

## Kapitel 33 — Reicht das, was unsere Rollen sehen? Ja/Nein je Rolle (16.08.2026)

**Nutzervorgabe, wörtlich:** *„die Information sollte tragen, weil es in der
Praxis so angewendet wird und ggf. auch in LLM-Lösungen … was sehen unsere
Rollen aktuell an Info — reicht das heute z. B. einem Trader = ja/nein und
entsprechend anpassen — der Auftrag muss analog für Z.ai durchgeführt werden."*

Der Maßstab ist damit ausdrücklich **nicht** unsere eigene Ausgangsmessung,
sondern die Praxis. Das ist ein zulässiger und hier der schnellere Weg: was
Händler durchgängig verwenden, ist eine Vorannahme, die man nicht erst selbst
beweisen muss.

### 33.1 Der Maßstab aus der Praxis: CSTI

Die Praxisliteratur beschreibt die Entscheidung als vier Fragen in fester
Reihenfolge — *Condition · Setup · Trigger · Invalidation*:

| | Frage | was gemeint ist |
|---|---|---|
| **C** | Bedingung | Ist das Umfeld überhaupt geeignet? Trend, Spanne, Volatilität, Nachrichtenlage |
| **S** | Aufbau | Liegt die erwartete Kursstruktur vor? Rücklauf an eine Marke, Konsolidierung, Bruch |
| **T** | **Auslöser** | Der genaue Anlass JETZT: Kerzenschluss, Bruch, Umsatzsprung |
| **I** | Widerlegung | Welcher Kurs beweist, dass die Lesart falsch war? |

Dazu als Auswahlkriterien durchgängig genannt: **Liquidität und Spread**,
**Umsatzbestätigung**, **Katalysator** (Ereignis, Zahlen, Makrotermin),
**Trendausrichtung über mehrere Zeitebenen**, und eine kleinere Position bei
riskanterem Aufbau.

**Und in den LLM-Lösungen:** der Trader in TradingAgents bekommt **Berichte,
keine Rohindikatoren** — von vier Analysten mit *verschiedenen Quellen* — plus
das Ergebnis eines Bull/Bear-Streits. Ein Risiko-Team prüft seine Entscheidung
danach aus drei Haltungen.

### 33.2 Rolle B/C — der Trader. Reicht es? **NEIN**

| Praxis verlangt | bei uns | Urteil |
|---|---|---|
| **C** Bedingung | Lagebild, Einstufung der eigenen Klasse | **ja** |
| **S** Aufbau | `struktur` + `marken`, mit benanntem Fenster | **ja** |
| **T** **Auslöser** | — | **FEHLT** |
| **I** Widerlegung | `umgeworfen_durch` + `umgeworfen_preis_eur`, Pflichtfeld | **ja, stark** |
| Liquidität/Spread | — (`volumen` ist Relativumsatz, nicht Handelbarkeit) | **FEHLT** |
| Umsatzbestätigung | `volumen`: Tagesumsatz gegen 20-Tage-Mittel, Aufwärtstage | ja |
| **Katalysator** | — | **FEHLT** |
| Trend über Zeitebenen | `bewegung` 5/20/60 Tage — als Zahlen, ohne Ausrichtungsaussage | teilweise |
| Positionsgröße | **bewusst nicht beim Modell** — System rechnet aus Risiko | besser als Praxis |

**Drei Lücken, und die erste ist die schwerste.**

> ⚠️ **Der Auslöser fehlt vollständig — und das ist derselbe Befund wie O-36.**
> Die Praxis trennt „der Aufbau liegt vor" von „jetzt ist der Moment". Unsere
> Kette kennt nur den Aufbau; **den Moment gibt die Uhr vor.** Deshalb wird
> dasselbe Asset alle 15 Minuten gefragt, und deshalb hat der Nutzer die
> Anlassfrage überhaupt gestellt.
>
> Der alte Weg hatte den Auslöser: `hebel_screening` mit Trendfolge- und
> Kontra-Zweig, Schwelle 70, gemessen 9,6 % Kandidaten. Er läuft weiter — und
> **niemand liest ihn.**

**Liquidität und Spread** entscheiden in der Praxis, ob ein Aufbau überhaupt
handelbar ist. Wir rechnen die Handelbarkeit (Bitpanda-Listung, Override) und
geben sie dem Modell nicht. Bei einem Titel wie SUPRA oder BEAMX ist das keine
Nebensache.

**Katalysator** ist die einzige Kategorie, die uns ganz fehlt — kein
Ereignis, keine Zahlen, kein Makrotermin. Das deckt sich mit dem eigenen
Grundbefund: *Nachrichten* sind einer von drei Wegen, die das Vorzeichen
drehen können, und der einzige davon, den wir nie versucht haben.

### 33.3 Rolle A — der Marktanalyst. Reicht es? **FAST**

| Praxis verlangt | bei uns | Urteil |
|---|---|---|
| Trend je Leitmarkt | 250/60 Handelstage, Abstand Hoch/Tief | ja |
| Volatilitätsregime | tägliche Schwankung + Perzentil | ja |
| Handelbarkeit | Umsatz je Bewegung + Perzentil | ja |
| Stimmung | Fear & Greed — **nur Bitcoin** | teilweise |
| Makro | Netto-Liquidität, Zinskurve | ja |
| **Terminkalender** | — | **FEHLT** |
| Regime + Persistenz | gerechnet (*bär*, 27 Tage), **nicht im Prompt** | FEHLT |

Zwei kleine Lücken, beide billig: die Stimmung liegt für mehr als BTC vor, und
Regime samt Persistenz ist gerechnet und wird nicht gereicht. Ein
**Terminkalender** (FOMC, CPI) wäre neu — aber genau das, was die Praxis unter
„post-news condition" versteht.

### 33.4 Z.ai — Rolle C. Reicht es? **NEIN, und zwar grundsätzlich**

Heute bekommt Z.ai **dieselben Marktfakten wie der Trader** und beantwortet
dieselbe Frage. Das ist nach der Literatur der Fehlerfall — *Homogeneous
Debate*: gleiche Informationsgrenze, keine epistemische Vielfalt, und ein
Modell, das eine gleichartig erzeugte Ausgabe prüft, **rationalisiert
nachträglich statt unabhängig zu prüfen**.

Die Messung bestätigt es: **17× LONG in 2.469 Prüfungen.**

**Was Z.ai stattdessen bekommen sollte — die Auswahl:**

| Z.ai bekommt | warum |
|---|---|
| **Optionsmarkt-Gegenargument** (Deribit) | 1.149 von 1.163 Fakten tragen bereits ein Gegenargument — und B sieht keines davon |
| **OI-Squeeze-Zustand** | fünf Zustände, 1.526 Fälle; sagt etwas über Positionierung, das keine Kerze hergibt |
| **Funding-Extremwerte** | dieselbe Familie, aber als Extremwert statt als Perzentiltext |
| **Regime + Persistenz** | 27 Tage bär — der Kontext, in dem jedes Urteil steht |
| **Handelbarkeit/Spread** | ob der Trade überhaupt ausführbar ist |
| die geplante Aktion, Richtung, Hebel | damit der Einwand konkret wird |

| Z.ai bekommt NICHT | warum |
|---|---|
| Kursstruktur, Marken, Bewegung | hatte B schon — das wäre wieder dieselbe Grenze |
| die Begründung von B | sonst prüft es den Text statt der Sache |
| das Lagebild | Modellprosa, kein Fakt |

**Eine Frage:** *„Spricht in diesen Daten etwas gegen diesen Trade?"* — ein
Aufruf statt vier.

### 33.5 Was daraus folgt, in dieser Reihenfolge

| | Schritt | Aufwand |
|---|---|---|
| **1** | **Finanzierung nur im Hebel-Prompt** — gemessen, falsch platziert | klein |
| **2** | **Handelbarkeit und Spread in den Trader-Prompt** — gerechnet, ungenutzt | klein |
| **3** | **Regime + Persistenz in Rolle A**, Stimmung über BTC hinaus | klein |
| **4** | **Auslöser zurückholen** — das vorhandene Screening als Anlass lesen, zusammen mit O-36 | mittel |
| **5** | **Z.ai auf Rolle C umbauen** — Positionierung statt Kursdaten | mittel |
| **6** | **Katalysator/Nachrichten** — die einzige ganz fehlende Quelle | groß |

**Die Schritte 1 bis 3 ändern den Prompt** und machen damit frühere Messungen
unvergleichbar. Das ist unvermeidlich und muss im `PROMPT_STAND` vermerkt
werden — jeder Messbefund gehört zu einem Stand, sonst ist er nicht
zuordenbar.

### 33.6 Was ich als Fachexperte dazu sage

**Die drei Lücken beim Trader sind keine Feinheiten.** Ein Händler, der Aufbau
und Widerlegung kennt, aber weder Auslöser noch Handelbarkeit noch Anlass,
trifft eine gut begründete Entscheidung **zum falschen Zeitpunkt an einem
möglicherweise nicht handelbaren Titel**. Genau das beschreibt der
Produktionslauf vom 15.08.: 26 Empfehlungen über 10.400 EUR in 105 Minuten,
ausgelöst von der Uhr.

**Und die Positionsgröße ist der eine Punkt, an dem wir besser sind als die
Praxis.** In TradingAgents entscheidet der Trader über die Größe; bei uns folgt
sie aus Risiko und Stopabstand. Das ist richtig so und sollte nicht angetastet
werden — es ist Arithmetik, keine Meinung.

**Quellen:** [TradingAgents](https://arxiv.org/html/2412.20138v1) ·
[FinMem](https://arxiv.org/abs/2311.13743) ·
[CSTI-Rahmen und Auswahlkriterien](https://www.smbtraining.com/blog/the-ultimate-swing-trading-guide-for-beginners-developing-traders) ·
[Verification Paradox](https://yaihq.com/research/verification-paradox-agents-cannot-validate-themselves)

### 33.7 Meine Meinung: das meiste gehört NICHT in den Prompt

Nutzerfrage: *„sollten unsere Rollen diese aus der Praxis haben oder nicht —
weil LLMs dies nicht können?"*

**Meine Antwort: die Rollen sollen die Praxis abbilden — aber die wenigsten
dieser Punkte gehören ins Modell.** Der Trennstrich ist nicht „wichtig oder
nicht", sondern:

> **Ist es eine berechenbare Bedingung — oder ein Urteil über Sprache und
> Zusammenhang?**

Das Erste gehört auf die deterministische Spur. Nur das Zweite ins Modell.

**Und dafür hat dieses Projekt die härteste Beweislage, die es hat.** Jedes Mal,
wenn das Modell eine ZAHL liefern sollte, war sie schlecht:

| Zahl vom Modell | gemessen |
|---|---|
| Konfidenz | 77,5 % vorhergesagt gegen 33,3 % eingetreten — sagt nichts vorher |
| Frist (`umgeworfen_bis`) | **36 von 37** lagen in der Vergangenheit |
| Einstieg/Stop als Zonen | bei **19 von 23** enger als die Rechnung, 7 unter RM-1b |
| Richtung (Z.ai) | **17× LONG** in 2.469 Prüfungen |
| Hebelfaktor | wird gar nicht erst gefragt — und das war richtig |

Jedes Mal, wenn es SPRACHE liefern sollte — Begründung, Gegengrund,
Widerlegungsbedingung —, war es brauchbar.

**Daraus folgt Punkt für Punkt:**

| Lücke | gehört wohin | warum |
|---|---|---|
| **Auslöser** | **deterministisch, vor dem Aufruf** | „Kurs schließt über X bei Umsatz Y" ist eine Bedingung, keine Einschätzung. Der alte Weg hatte das richtig: Screening rechnet, nur Kandidaten kommen zum Modell |
| **Handelbarkeit/Spread** | **deterministisch, als Filter** | ob ein Titel handelbar ist, ist eine Tatsache. Ein Modell zu fragen, ob 3 % Spread zuviel sind, wäre eine Meinung über eine Rechnung, die wir schon haben |
| Trend über Zeitebenen | deterministisch, als Satz | rechenbar; als Satz in den Faktentext, nicht als Frage |
| Regime + Persistenz | deterministisch, als Satz | dito — billig, aber wenig zu erwarten: es ist aus denselben Kursdaten abgeleitet |
| **Katalysator/Nachrichten** | **ins Modell** | **hier und nur hier ist das LLM überlegen** — Text lesen und einordnen kann kein Regelwerk |

**Und das ändert meinen Z.ai-Vorschlag.** Ich hatte Optionsmarkt, OI-Squeeze
und Funding-Extreme für Rolle C vorgeschlagen. Ehrlich betrachtet ist der
größte Teil davon **eine Regel, keine Frage**:

    Funding im 95. Perzentil UND geplante Richtung LONG  ->  Einwand
    Long-Squeeze-Verdacht UND geplante Richtung LONG     ->  Einwand

Das ist deterministisch, kostenlos, sofort messbar und immer verfügbar. Ein
Modell dafür zu bezahlen wäre derselbe Fehler wie beim Richtungsabgleich —
nur mit anderen Zahlen.

> ⚠️ **STANDVERMERK 16.08.2026 abends: diese Gabelung wurde NICHT
> genommen.** Die Voraussetzung war, dass die Positionierungsfakten zu
> deterministischen Regeln werden. Gebaut wurde das Gegenteil — Rolle G
> ist die **Positionierungsrolle mit eigenen Quellen** (Kapitel 55–60).
> Damit entfaellt die Begruendung, ihr die Nachrichten zu geben; sie
> gehoeren zu **BC**, siehe Kapitel 63 und R-R6.
>
> **Die ehrliche Konsequenz: Rolle C sollte die Nachrichten- und
> Katalysator-Rolle sein, nicht die Zahlen-Rolle.** Die Positionierungsfakten
> werden deterministische Einwände im Faktentext — sichtbar für B, ohne
> zusätzlichen Aufruf.

**Was das für die Reihenfolge heißt:** die Schritte 1 bis 4 bleiben, werden
aber überwiegend **Rechnung statt Prompt**. Schritt 5 (Z.ai-Umbau) wird kleiner
— die Zahlen wandern in die Regel — und Schritt 6 (Nachrichten) rückt von
„zuletzt, weil aufwendig" auf **„der eigentliche Grund, überhaupt ein zweites
Modell zu betreiben"**.

**Ein Vorbehalt, den ich nenne, weil er zählt:** dass ein Modell mit den
richtigen Fakten besser urteilt, ist bei uns **nicht gemessen** — dieses
Projekt hat an 8.441 Fällen gezeigt, dass kein Verfahren die Basisrate
schlägt, und alle bisherigen Prompt-Erweiterungen haben daran nichts geändert.
Die Praxisbegründung trägt die Entscheidung, sie ersetzt aber nicht den
Nachweis. Deshalb bekommt jede dieser Ergänzungen eine eigene Spalte und wird
gegen die Basisrate gemessen — sonst wiederholen wir die Geschichte der
Konfidenz.

---

## Kapitel 34 — Schritt 1: Bestandserhebung je Rolle und Assetklasse (16.08.2026)

**Nutzervorgabe zur Reihenfolge:** *„1. Zuerst Bestandserhebung. 2. Recherche
und Analyse. 3. Schritt für Schritt Integration oder Anpassung von LLM1 und
LLM2."* — und ausdrücklich: *„wir suchen nicht einfach, was wir dem LLM neu
hinzufügen, weil wir es haben."*

Kapitel 32 und 33 sind damit **vorgezogen** worden: sie enthalten Recherche und
Bewertung, bevor der Bestand sauber erhoben war. Sie bleiben gültig, stehen
aber sachlich **nach** diesem Kapitel.

**Erhoben wird gerendert, nicht gelesen** (`erhebe_prompts.py`). Ein
Code-Studium sagt, was gebaut ist; nur der gerenderte Satz sagt, was ankommt.

### 34.1 Was ankommt — je Gruppe und Instrument

| Gruppe / Instrument | bestand | struktur | bewegung | marken | volumen |
|---|---|---|---|---|---|
| aktien / spot | 1 | 2 | 1 | 2 | 2 |
| **hedge / absicherung** | 1 | 2 | 1 | **1** | **0** |
| krypto / spot | 1 | 2 | 1 | 2 | 2 |
| krypto / hebel | 1 | 2 | 1 | 2 | 2 |
| **rohstoffe / spot** | 1 | 2 | 1 | 2 | **0** |
| themen_etf / spot | 1 | 2 | 1 | 2 | 2 |

**Befund 1: es gibt keine Unterscheidung je Assetklasse — nur je Instrument.**

Unterschiedlich ist ausschließlich der `auftrag`:

```
spot         "Gehandelt wird der Wert selbst, ohne Hebel und ohne laufende Kosten."
hebel        "Gehandelt wird eine gehebelte Position. Die Finanzierung faellt an
              JEDEM Tag an ... Zwangsaufloesung."
absicherung  "Gehandelt wird ein Absicherungsinstrument. Es soll das uebrige
              Portfolio abfedern, nicht selbst Gewinn erzielen."
```

Und der `bestand`, seit dem 15.08. je Instrument. **Sonst bekommt eine Aktie
denselben Satzbau wie ein Memecoin** — dieselben Fenster (5/20/60), dieselben
Wendepunkt-Regeln, dieselbe Markenlogik.

> ⚠️ **Befund 2: bei `rohstoffe` und `hedge` fehlt der Volumenblock ganz** —
> und niemand sagt es. Diese beiden Gruppen entscheiden mit **einem Block
> weniger** als die übrigen, ohne dass der Faktensatz das erwähnt. Der Grund
> ist die Datenlage (Zertifikate und ETP führen in unserer Reihe kein
> Volumen), aber im Prompt sieht es aus wie „kein Befund" statt „nicht
> vorhanden". Bei `hedge` fehlt zusätzlich eine der beiden Marken.

### 34.2 LLM-Tauglichkeit: der Teil, der gelungen ist

| Block | Sätze ohne Zahl | Zahl **mit** Bezug | Zahl **ohne** Bezug |
|---|---|---|---|
| bestand | 2 | 4 | **0** |
| struktur | 0 | 12 | **0** |
| bewegung | 0 | 6 | **0** |
| marken | 0 | 11 | **0** |
| volumen | 0 | 8 | **0** |

**Keine einzige nackte Zahl.** Jede Zahl steht neben ihrem Maßstab:

```
"Der naechste Widerstand liegt 1.1 Schwankungsbreiten hoeher, bei 158.7 EUR
 (3-mal beruehrt)."
```

Der Kurs allein wäre eine nackte Zahl — *„1,1 Schwankungsbreiten"* macht ihn
lesbar, *„3-mal berührt"* gibt ihm Gewicht. Genau das, wofür
`lagebeschreibung.py` gebaut wurde, und es hält.

**Das ist der Maßstab für alles Weitere:** eine Ergänzung, die eine Zahl ohne
Bezug bringt, verschlechtert den Prompt, auch wenn ihr Inhalt richtig ist.

### 34.3 Rolle A — Marktanalyst

Bekommt je Leitmarkt (krypto/aktien/rohstoffe): Trend über 250 und 60
Handelstage, Abstand zu Hoch und Tief, tägliche Schwankung mit Perzentil,
Umsatz je Bewegung mit Perzentil. Für Bitcoin zusätzlich die Anlegerstimmung.
Dazu Netto-Liquidität und Zinskurven-Spread.

**Keine Unterscheidung je Assetklasse ist hier richtig** — die Rolle beurteilt
gerade die Unterschiede zwischen den Märkten.

### 34.4 Rolle C — gibt es nicht

Der Code kennt `Rolle A` und `Rolle BC`. Beurteilen und Handeln liegen in einem
Aufruf; der „Bewerter" ist `trefferbilanz.bewerte()` — Arithmetik über die
eigene Trefferbilanz, kein Urteil. **Z.ai** ist heute kein C, sondern ein
zweiter B mit derselben Informationsgrenze.

### 34.5 Was Schritt 2 damit zu tun hat

Die Recherche in Kapitel 33 hat den Praxismaßstab (CSTI, Liquidität,
Katalysator) — **aber sie wurde gegen einen angenommenen Bestand geführt.**
Mit dem erhobenen Bestand sind zwei Punkte neu und gehören vor jede Ergänzung:

1. **Die fehlende Klassendifferenzierung ist die größere Frage als jede
   fehlende Kennzahl.** Ob ein Memecoin und eine Aktie dieselben Fenster
   brauchen, ist eine Praxisfrage, die noch niemand gestellt hat.
2. **Zwei Gruppen laufen mit weniger Blöcken** — und der Prompt sagt es nicht.
   Das ist kein Ergänzungswunsch, das ist eine stillschweigende Lücke.

**Erst danach** kommt die Frage nach Auslöser, Handelbarkeit und Katalysator.

### 34.6 Die Erhebung je Asset: acht von 56 urteilen unvollständig

Nutzerfrage: *„haben alle Assets und Gruppen ausreichende Bewertungsgrundlagen
und Parameter für alle Rollen?"* — **Nein.**

| Gruppe | Assets | vollständig | unvollständig |
|---|---|---|---|
| aktien | 2 | 2 | – |
| krypto | 43 | 41 | **2** |
| themen_etf | 5 | 4 | **1** |
| hedge | 2 | 1 | **1** |
| **rohstoffe** | **4** | **0** | **4** |

```
hedge      3QSS      527 Kerzen   volumen fehlt, nur EINE Marke
rohstoffe  OD7C      520          volumen fehlt
rohstoffe  OD7H      520          volumen fehlt
rohstoffe  OD7L      137          volumen fehlt, unter 250 Handelstagen
rohstoffe  OD7N      520          volumen fehlt
themen_etf X136      162          volumen fehlt, unter 250 Handelstagen
krypto     CANTON      0          KEINE REIHE
krypto     VSN         0          KEINE REIHE
```

**Drei verschiedene Arten von Lücke:**

**Datenlage** — Zertifikate und ETP führen in unserer Reihe kein Volumen. Kein
Fehler, aber der Faktensatz sagt es nicht: das Modell sieht keinen Volumensatz
und liest das als *unauffällig* statt als *nicht vorhanden*.

**Gar keine Grundlage** — CANTON und VSN stehen in der Watchlist, laufen durch
die Kette und fallen an der Faktenstufe heraus.

**Zu kurze Historie** — OD7L (137) und X136 (162) liegen unter den 250
Handelstagen, die die Perzentile brauchen. Dieselbe Grenze, die ASTER betraf.

> ⚠️ **Die erste Korrektur steht damit fest, noch vor jeder Erweiterung:**
> eine fehlende Angabe gehört in den Faktentext. *„Für dieses Instrument liegt
> kein Umsatz vor"* — sonst liest das Modell Abwesenheit als Unauffälligkeit.
> Das ist der KAS-Fall in anderer Gestalt: dort fehlte der Bestand im Prompt,
> und das Modell kaufte in eine Verlustposition nach.

### 34.7 Die fünf Körbe für Schritt 2 (Nutzervorgabe)

*„Wir müssen jedenfalls unterteilen in Krypto Spot und Hebel — Aktien,
Rohstoffe und ETF."*

| Korb | Assets | Auftrag | Besonderheit der Datenlage |
|---|---|---|---|
| **Krypto Spot** | 43 (41 vollständig) | ohne Hebel, ohne laufende Kosten | einzige Gruppe mit Funding **und** Volumen |
| **Krypto Hebel** | dieselben 43, 25 nach Schalter | gehebelt, Finanzierung täglich, Zwangsauflösung | identische Fakten wie Spot — **nur der Auftrag trennt sie** |
| **Aktien** | 2 | ohne Hebel | vollständig; Funding gibt es am Terminmarkt nicht |
| **Rohstoffe** | 4 | ohne Hebel | **kein einziges vollständiges Asset** — Volumen fehlt durchgehend |
| **ETF** | 5 + 2 Absicherung | ETF: ohne Hebel · Absicherung: eigener Auftrag + Exposure-Block | X136 und 3QSS ohne Volumen |

**Der auffälligste Befund dieser Aufteilung:** Krypto Spot und Krypto Hebel
bekommen **denselben Faktensatz**. Zwei Entscheidungen mit völlig
verschiedener Geometrie — Liquidationsabstand, tägliche Finanzierung,
Haltedauer — stehen auf identischen Fakten; unterschieden werden sie nur durch
zwei Sätze im `auftrag`.

Das ist die erste Frage für Schritt 2: **welche Parameter braucht ein
Hebel-Urteil, die ein Spot-Urteil nicht braucht — und umgekehrt.**

---

## Kapitel 35 — Schritt 2: Korb für Korb gegen die Praxis (16.08.2026)

Je Korb drei Fragen: **was liefern wir · was verlangt die Praxis für genau
dieses Instrument · ist die Lücke LLM-tauglich zu schließen** (Satz mit Bezug,
keine nackte Zahl).

### 35.1 Krypto Hebel — die größte Lücke, und sie ist nicht klein

**Was wir liefern:** denselben Faktensatz wie Spot — bestand, struktur,
bewegung, marken, volumen, finanzierung. Unterschied: zwei Sätze im `auftrag`.

**Was die Praxis verlangt** (Perpetual-Futures-Literatur, durchgängig):

| | Praxis | bei uns |
|---|---|---|
| **Liquidationsabstand** | bei 10-fach genügt eine Gegenbewegung von rund 10 %, bei 25-fach vier — die zentrale Zahl der Entscheidung | **wird NACH dem Urteil gerechnet** |
| **Finanzierung als Kostenbetrag** | bei 5-fach und 0,01 % je acht Stunden etwa 4,5 % der Margin im Monat; bei 0,05 % rund das Fünffache | nur als **Perzentiltext**, ohne Betrag |
| **Finanzierung als Warnsignal** | extremes Funding geht scharfen Umkehrungen oft voraus | Perzentil vorhanden, **nicht als Signal benannt** |
| **Open Interest, Kaskadenrisiko** | Liquidationsketten erklären, warum OI plötzlich verschwindet | **gerechnet, ungenutzt** (1.526 Fälle) |
| **Haltedauer** | Perps erzwingen Entscheidungen — kein unbegrenztes Aussitzen | wird gerechnet, **Modell sieht sie nicht** |

> ⚠️ **Der Kern:** das Modell wählt ERÖFFNEN, ohne den Liquidationsabstand und
> ohne die tägliche Kostenhöhe zu kennen. Es liest einen **qualitativen
> Warnsatz ohne jede Größe** — beides wird zwei Schritte später gerechnet und
> steht dann in der Mail.
>
> Am AKT-Signal: Hebel 3,1×, Zwangsauflösung bei 0,3200 EUR, Stop bei 0,4475 —
> ein komfortabler Abstand. **Aus Sicht des Modells war das Zufall**, es hat
> ihn nicht beurteilt.

**LLM-tauglich?** Ja, und sauber: *„Bei diesem Hebel läge die Zwangsauflösung
16,7 % unter dem Einstieg, der Stop bei 4,8 %."* Zwei Zahlen, beide mit Bezug
zueinander — genau die Form, die `lagebeschreibung` überall sonst hat.

**Das Henne-Ei-Problem:** der Hebel folgt aus dem Stop, den das Modell nennt.
Niemand kennt den Faktor, bevor das Modell geantwortet hat. **Ohne Umbau
lösbar:** der Abstand bei den *Grenzhebeln* lässt sich vorher sagen — bei
3-fach 33 %, bei 6-fach 17 %, bei 10-fach 10 %. Eine Tabelle statt eines
Kreisbezugs.

### 35.2 Krypto Spot — nah dran, mit einem Fremdkörper

Die Praxis verlangt bei Spot: Struktur, Marken, Umsatzbestätigung, Trend über
Ebenen, Liquidität, Katalysator. Kein Funding, keine Liquidation, keine
Haltefrist.

| | |
|---|---|
| **liefern wir** | Struktur, Marken, Bewegung, Volumen, Bestand — **vollständig** |
| **Fremdkörper** | **Finanzierung.** Fällt bei Spot nicht an, wird aber in **63 %** der Spot-Urteile zitiert (O-34) |
| **fehlt** | Handelbarkeit und Spread · Auslöser · Katalysator |

Der Funding-Block ist hier nicht nur überflüssig, sondern **irreführend**: er
beschreibt eine Zahlung zwischen Long- und Short-Positionen, die ein
Spot-Käufer weder leistet noch erhält. Als *Stimmungsmaß* wäre er brauchbar —
dann müsste er aber so formuliert sein und nicht als Kostenmechanik.

### 35.3 Aktien — Daten vollständig, Termine fehlen

Beide Assets haben alle Blöcke. Was die Praxis bei Einzelaktien zusätzlich
verlangt und wir **nicht** liefern:

| Praxis | bei uns |
|---|---|
| **Termine** — Quartalszahlen, Dividende | fehlt ganz |
| Sektor- und Indexbezug | fehlt |
| **Handelszeiten und -tage** | fehlt |
| Fundamentaldaten | fehlt |

**Bei Aktien ist der Katalysator kein Zusatz, sondern der Regelfall.** Ein
Einstieg zwei Tage vor Quartalszahlen ist eine andere Entscheidung als
derselbe Chart drei Wochen davor — das Modell kann den Unterschied nicht
sehen.

Die Handelszeiten sind der praktische Punkt: **die Kette läuft im
15-Minuten-Takt, die Börse nicht.** Ein Aktiensignal um 23 Uhr ist bis zum
nächsten Morgen kalt.

### 35.4 Rohstoffe — kein einziges vollständiges Asset

Alle vier ohne Volumenblock, OD7L zusätzlich unter 250 Handelstagen.

**Und ein Punkt, den erst die Bestandserhebung sichtbar macht:** es sind
**Zertifikate**, keine Rohstoffe. Der Faktensatz behandelt sie wie einen
Kurswert — ein Zertifikat trägt aber einen Emittenten, einen Basiswert, ein
Bezugsverhältnis und je nach Bauart einen Hebel oder eine Barriere.

| Praxis bei Zertifikaten | bei uns |
|---|---|
| Basiswert und Bezugsverhältnis | fehlt |
| Emittentenrisiko | fehlt |
| Spread, Handelbarkeit außerhalb der Referenzzeit | fehlt |
| Rollverluste bei Terminkontrakt-Basis | fehlt |

**Die Gruppe mit der schwächsten Grundlage** — und die, bei der ich am
wenigsten sagen kann, ohne die Papiere einzeln anzusehen. Sie gehört als
eigener Rechercheschritt aufgesetzt.

### 35.5 ETF und Absicherung — zwei verschiedene Dinge in einem Korb

**Themen-ETF** (5 Stück): der Sektorbezug ist die tragende Information — ein
Kupfer-ETF folgt dem Kupferpreis, nicht seinem eigenen Chart. Wir liefern nur
den eigenen Chart.

**Absicherung** (2 Stück) hat als einzige Gruppe einen **eigenen Faktenblock**:
Exposure, Deckung, Hebelfaktor, laufende Gebühr — der Paket-14-Block vom
15.08. **Die am besten zugeschnittene Gruppe im ganzen System.**

| | fehlt |
|---|---|
| ETF | Referenzindex, Sektorbezug, TER, Spread |
| Absicherung | Volumen (3QSS), zweite Marke |
| beide | Handelszeiten |

### 35.6 Was das in Summe ergibt

| Korb | Zustand | größte Lücke |
|---|---|---|
| **Krypto Hebel** | **schlechteste Passung** | Liquidationsabstand und Kostenhöhe fehlen im Urteil |
| Krypto Spot | gut, ein Fremdkörper | Funding gehört nicht hinein |
| Aktien | Daten vollständig | Termine — bei Aktien der Regelfall |
| **Rohstoffe** | **schwächste Grundlage** | Volumen durchgehend, Zertifikatsnatur ignoriert |
| ETF / Absicherung | gemischt | Referenzindex · Absicherung am besten zugeschnitten |

**Die Reihenfolge folgt aus der Lücke, nicht aus dem Aufwand:**

1. **Krypto Hebel** — 77 % der Aufrufe und die größte Lücke. Liquidations­abstand
   und Finanzierungshöhe in den Faktensatz.
2. **Krypto Spot** — den Funding-Block herausnehmen oder umformulieren.
3. **Fehlende Angaben benennen** — gruppenübergreifend, betrifft 8 Assets.
4. **Aktien: Termine** — erste echte neue Datenquelle, klein abgegrenzt.
5. **Rohstoffe** — eigener Rechercheschritt, Zertifikate statt Kurswerte.
6. **ETF: Referenzindex** — für die Absicherung liegt er bereits vor.

**Quellen:**
[Perpetual Futures — Funding, Hebel, Liquidation](https://crypto.news/what-are-perpetual-futures-perps-funding-rates-and-liquidations-explained/) ·
[Liquidationsmechanik](https://metamask.io/news/perpetual-futures-liquidation-mechanics) ·
[Funding als Kosten und als Signal](https://metamask.io/news/perpetual-futures-funding-frequency-strategies) ·
[Perps gegen Spot](https://metamask.io/news/crypto-spot-trading-vs-perpetual-futures)

---

## Kapitel 36 — Gegenprüfung der Reihenfolge, Rollenzuordnung und die Aufteilung LLM1/LLM2 (16.08.2026)

Drei Lücken in Kapitel 35, alle drei vom Nutzer benannt: die Reihenfolge ist
nicht auf Risiko geprüft, die Lücken sind keiner Rolle zugeordnet, und die
Aufteilung zwischen LLM1 und LLM2 fehlt ganz.

### 36.1 Die Gegenprüfung — und sie dreht meine Reihenfolge um

**Der Maßstab ist ein gemessener Vorfall dieses Projekts:**

> **Ausführbarkeit / Kostenhinweis: gemessen und verworfen.** Der ehrliche
> Hinweis ließ die ERÖFFNEN-Quote von **93 % auf 3 %** einbrechen. Das Modell
> schlug dann gar nichts mehr vor, statt Alternativen zu suchen.

Daraus die Risikoklassen:

| | Art der Ergänzung | Risiko |
|---|---|---|
| **grün** | beschreibt die Lage, ohne sie zu bewerten | gering |
| **gelb** | nennt Kosten, Ausführbarkeit oder ein Risiko | **gemessen gefährlich** |
| **rot** | fordert das Modell zur Abwägung gegen einen Nachteil auf | belegt schädlich |

**Und damit fällt meine Nummer 1 auseinander:**

| Ergänzung | Klasse | warum |
|---|---|---|
| Liquidationsabstand als **Geometrie** | **grün** | *„bei 6-fach läge die Zwangsauflösung 17 % unter dem Einstieg"* — eine Lagebeschreibung wie der Widerstand |
| Finanzierung als **Kostenbetrag** | **gelb/rot** | *„kostet 4,5 % der Margin im Monat"* ist wörtlich der Hinweis, der die Quote von 93 auf 3 % gedrückt hat |

**Der Liquidationsabstand ist harmlos, die Kostenhöhe ist es nicht** — und ich
hatte beide in einen Punkt geworfen.

**Die geprüfte Reihenfolge:**

| | Ergänzung | Klasse | Rolle |
|---|---|---|---|
| **1** | Liquidationsabstand bei den Grenzhebeln | grün | **BC** |
| **2** | Funding aus dem Spot-Prompt entfernen | grün (Wegnahme) | **BC** |
| **3** | Fehlende Angaben benennen (8 Assets) | grün | **BC** |
| **4** | Referenzindex bei ETF und Absicherung | grün | **BC** |
| **5** | Regime und Persistenz | grün | **A** |
| **6** | Aktientermine, Handelszeiten | **gelb** | **BC** |
| **7** | Zertifikatsnatur bei Rohstoffen | **gelb** | **BC** |
| **8** | Finanzierung als Betrag beim Hebel | **rot** | **BC** |

**Fünf grüne Schritte vor dem ersten gelben.** Das war in Kapitel 35 nicht so,
und die Umstellung folgt nicht aus dem Aufwand, sondern aus einem Messwert.

**Für gelb und rot gilt zusätzlich:** nicht in den Betrieb ohne gepaarten
Vergleich auf denselben Ankern — ein Arm mit, einer ohne. Genau die Methode,
mit der 93 → 3 % überhaupt gefunden wurde.

### 36.2 Welche Lücke gehört zu welcher Rolle

| Lücke | Rolle A (Marktanalyst) | Rolle BC (Trader) | Rolle C (Z.ai) | keine Rolle |
|---|---|---|---|---|
| Liquidationsabstand | | **X** | | |
| Finanzierung als Betrag | | **X** (rot) | | |
| Funding als Fremdkörper im Spot | | **X** (Wegnahme) | | |
| Fehlende Angaben benennen | | **X** | | |
| Referenzindex, Sektorbezug | | **X** | | |
| Zertifikatsnatur | | **X** | | |
| Aktientermine | | **X** | | |
| Makro-Terminkalender | **X** | | | |
| Regime und Persistenz | **X** | | | |
| Stimmung über BTC hinaus | **X** | | | |
| **Open Interest, Squeeze** | | | **X** | |
| **Optionsmarkt** | | | **X** | |
| **Nachrichten, Katalysator** | | | **X** | |
| **Auslöser** | | | | **deterministisch, vor dem Aufruf** |
| **Handelbarkeit, Spread** | | | | **deterministisch, als Filter** |

**Zwei Lücken gehören keiner Rolle** — sie sind Bedingungen, keine
Einschätzungen, und gehören auf die Rechenspur vor dem Modellaufruf.

### 36.3 Die Aufteilung LLM1 / LLM2 — und die Regel, die sie trägt

Das fehlte in Kapitel 35 vollständig, und es ist der Punkt, an dem die
Gegenprüfung überhaupt erst funktioniert.

> **Ein Parameter gehört zu GENAU EINEM Modell.** Geht er an beide, teilen sie
> die Informationsgrenze — und die Prüfung ist wieder das, was sie heute ist:
> *Homogeneous Debate*, zwei Leser derselben Seite.

Das ist keine Sparregel, sondern die **Konstruktionsbedingung** der zweiten
Stufe. Sie ist heute verletzt: Z.ai bekommt denselben Faktentext wie BC.

| Korb | LLM1 — Rolle BC bekommt | LLM2 — Rolle C bekommt |
|---|---|---|
| **Krypto Hebel** | Struktur · Marken · Bewegung · Volumen · Bestand · Auftrag · **Liquidationsabstand** · Funding-**Perzentil** | **Open Interest / Squeeze-Zustand** · **Funding-Extremwert als Signal** · **Optionsmarkt** · Regime-Persistenz · geplante Aktion und Richtung |
| **Krypto Spot** | dieselben, **ohne Funding** | **Funding als Stimmungsmaß** · Optionsmarkt · **Nachrichten** |
| **Aktien** | Struktur · Marken · Bewegung · Volumen · Bestand · **Sektorbezug** | **Termine** (Quartalszahlen) · **Nachrichten** · Makrolage |
| **Rohstoffe** | Struktur · Marken · Bewegung · Bestand · **Hinweis auf fehlendes Volumen** · **Basiswert** | **Emittent und Bauart** · Rollsituation · **Nachrichten zum Basiswert** |
| **ETF / Absicherung** | Struktur · Marken · Bewegung · Bestand · **Referenzindex** · Exposure-Block | **Lage des Referenzindex** · **Nachrichten zum Sektor** |

**Das Muster ist in allen fünf Körben dasselbe:** LLM1 bekommt, was aus der
**Kursreihe und dem Depot** folgt. LLM2 bekommt, was **außerhalb** davon liegt
— Positionierung, Termine, Nachrichten.

Damit beantwortet sich auch die Frage nach zusätzlichen Parametern für Z.ai:
**es sind nicht dieselben in anderer Form, sondern andere.** Und drei davon
existieren bereits — Open Interest, Optionsmarkt, Regime —, zwei nicht:
Termine und Nachrichten.

### 36.4 Was das für die Reihenfolge bedeutet

Die fünf grünen Schritte betreffen **ausschließlich LLM1**. Der Umbau von LLM2
setzt voraus, dass die Trennung steht — sonst verschiebt man nur, was beide
sehen.

| Phase | betrifft | Inhalt |
|---|---|---|
| **I** | LLM1 | die fünf grünen Schritte, einer nach dem anderen |
| **II** | LLM2 | Richtungsabgleich stilllegen, Positionierungsfakten aufbauen |
| **III** | beide | gelb und rot, jeweils mit gepaartem Vergleich |
| **IV** | LLM2 | Nachrichten — neue Quelle, eigenes Vorhaben |

**Und eine Bedingung für Phase I:** jeder der fünf Schritte ändert den
`PROMPT_STAND`. Fünf Änderungen an fünf Tagen erzeugen fünf Stände, zwischen
denen niemand mehr vergleichen kann. **Deshalb Phase I als EIN Stand**, nicht
als fünf — sie sind alle grün, alle beschreibend, und ihre Einzelwirkung wäre
bei dieser Signalzahl ohnehin nicht trennbar.

---

## Kapitel 37 — Rolle C in Betrieb: Anhaltspunkte, Bestätigung, eigener Abschnitt (16.08.2026)

### 37.1 Hat Rolle C genug Anhaltspunkte?

| | |
|---|---|
| Krypto-Assets | 44 |
| **volle Positionierung** (3 von 3 Angaben) | **35** |
| teilweise | 2 |
| **gar keine — Rolle C fragt NICHT** | **7** |

**Vier Anhaltspunkte je Frage:** Veränderung der offenen Kontrakte ·
Finanzierungsrate als Perzentil der eigenen Historie · Anteil der Long-Konten ·
**Marktregime mit Dauer** (heute ergänzt).

Aktien, Rohstoffe und ETF haben keine Terminmarktdaten — dort wird **gar nicht
gefragt**. Das ist gewollt: ein Modell, das über nichts urteilt, urteilt
trotzdem, und das wäre die nächste Konstante.

> ⚠️ **Beim Regime lag ich zweimal daneben.** Erst fragte ich eine Tabelle
> `regime_status` ab — die es nicht gibt; das Regime steht auf der jüngsten
> Signalzeile, die Dauer rechnet `regime.regime_persistenz_tage()`. Der
> Fail-soft hat es gefangen, aber als dauerhaftes *„keine Angabe"*. Und in der
> Korrektur fing ich Regime und Dauer gemeinsam — dadurch standen *„Regime
> baer"* und *„keine Angabe zum Marktregime"* **nebeneinander in derselben
> Ausgabe.** Jetzt getrennt gefangen.

**Ehrlich zur Menge:** vier Anhaltspunkte sind dünn. Aus dem Plan fehlen noch
Optionsmarkt (Deribit, 1.149 Fakten mit Gegenargument) und Nachrichten. Beide
sind eigene Vorhaben.

### 37.2 Auch ohne Einwand steht eine Aussage da

Nutzervorgabe: *„wenn sie keinen Einwand hat, soll sie etwas anzeigen — und
natürlich soll es auch eine Art Bestätigung sein."*

Meine erste Fassung ließ „kein Einwand" weg, aus Sorge vor einem konstanten
Feld (R-T6). **Der Einwand des Nutzers trifft:** eine Gegenprüfung, die nur bei
Widerspruch sichtbar ist, lässt offen, ob sie überhaupt gelaufen ist.

**Die Sorge bleibt trotzdem berechtigt und ist anders gelöst:** die Bestätigung
**nennt die Zahlen, auf die sie sich stützt**. Damit bewegt sich der Text mit
den Daten und ist kein konstantes Feld.

```
--- 5. GEGENPRUEFUNG (zweites Modell) ---
kein Einwand - die Positionierung stuetzt den Handel: Funding im gewohnten Bereich
  Die Finanzierungsrate steht im 72. Perzentil der letzten 400 Messungen - im gewohnten Bereich.
  65 % der Konten stehen long; das ist das 90. Perzentil der eigenen Historie.
Dieses Modell kennt NUR die Positionierung am Terminmarkt, nicht die Kurslage.
```

Drei Zustände, alle mit Begründung und Grundlage:

| Antwort | Kopfzeile |
|---|---|
| ja | **EINWAND** — die Positionierung spricht dagegen |
| nein | kein Einwand — die Positionierung stützt den Handel |
| unklar | nicht eindeutig — die Positionierung lässt beides zu |

### 37.3 Eigener Abschnitt statt Nachsatz

Die Zeilen der zweiten Stufe standen bisher **hinten in „4. EINORDNUNG"** — dort
sahen sie aus wie ein Nachsatz unserer eigenen Rechnung. Sie sind aber die
Aussage einer **anderen Quelle** und stehen jetzt in **„5. GEGENPRÜFUNG
(zweites Modell)"**.

### 37.4 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **831, alle bestanden** |
| freie Namen | 0 |
| frühere Gegenprüfungen (37 · 23 · 12 · 10) | alle grün |

Eine bestehende Prüfung hielt fest, dass „kein Einwand" **keine** Zeile
erzeugt — sie war eine Stunde alt und von mir. Sie prüft jetzt das Gegenteil,
**und zusätzlich, dass die Bestätigung ihre Zahlen nennt.**

### 37.5 Was offen bleibt

**Ob Rolle C etwas trägt, ist ungemessen** — wie alles andere auch. Sie bekommt
eine eigene Spalte und wird gegen die Basisrate gemessen. Der Unterschied zum
Vorgänger ist nicht, dass sie besser ist, sondern dass sie **überhaupt eine
eigene Information hat**, über die sie urteilen kann.

Und die Verteilung wird ab dem ersten Tag beobachtet: sagt sie in 95 % der
Fälle „kein Einwand", ist sie dieselbe Konstante wie der Richtungsabgleich —
nur mit anderen Worten.

---

## Kapitel 38 — Phase I: vier grüne Ergänzungen in EINEM Prompt-Stand (16.08.2026)

`PROMPT_STAND` springt von **2026-08-12 auf 2026-08-16**. Alle Messbefunde
davor gehören zum alten Stand und sind mit den neuen nicht vergleichbar — das
ist der Preis und er war in 36.4 eingeplant.

### 38.1 Der fünfte Schritt ist NICHT gebaut — und das ist der Plan, nicht die Umsetzung

Kapitel 36 führt fünf grüne Schritte. Gebaut sind **vier**. Der fünfte —
*Regime und Persistenz für Rolle A* — verletzt die Konstruktionsbedingung, die
zwei Kapitel weiter oben im selben Dokument steht:

> **Ein Parameter gehört zu GENAU EINEM Modell.** Geht er an beide, teilen sie
> die Informationsgrenze — und die Prüfung ist wieder *Homogeneous Debate*.

**Der Plan widerspricht sich hier selbst.** 36.2 ordnet „Regime und Persistenz"
der **Rolle A** zu; die Tabelle in 36.3 führt „Regime-Persistenz" in derselben
Zeile unter **LLM2**. Und Kapitel 37 hat es am Morgen des 16.08. in **Rolle C**
gebaut, als vierten Anhaltspunkt.

**Warum es bei Rolle C bleibt — und das ist kein Ausweichen:**

| | |
|---|---|
| **Rolle A hat beide Zutaten schon** | Das Regime rechnet `regime_score()` aus BTC-Kurs gegen EMA50/200 **und** Fear & Greed. Rolle A bekommt den BTC-Trend über 250 und 60 Handelstage und die Anlegerstimmung — sie liest die Bestandteile bereits. Das Etikett obendrauf ist eine **vorverdaute Wertung**, keine neue Angabe |
| **Und ein Etikett verstößt gegen R-T3** | *„Regime bär"* ist genau die Art Wort, die `lagebeschreibung` überall sonst vermeidet |
| **Rolle C hat sonst nichts davon** | Sie sieht ausschließlich die Positionierung am Terminmarkt. Das Regime ist ihr einziger Kontext — und der einzige Weg, auf dem er sie erreicht |

**Was ich dabei einräume:** das Regime ist aus **unserer** Kursreihe gerechnet.
Streng genommen gehört es damit auf die LLM1-Seite, und die Zuweisung an Rolle C
ist ein Kompromiss zugunsten einer Stufe, die sonst auf drei Anhaltspunkten
steht. Sauber wird es erst, wenn Rolle C den Optionsmarkt und die Nachrichten
hat — dann kann das Regime dorthin zurück, wo es hingehört.

**Die Entscheidung gehört dem Nutzer.** Baue ich es zusätzlich in Rolle A, ist
die Trennung der zweiten Stufe aufgehoben — das war der ganze Grund für Phase II
vom selben Tag.

### 38.2 Die vier gebauten Schritte

| | Ergänzung | Rolle | wo |
|---|---|---|---|
| **1** | Liquidationsabstand je Grenzhebel | BC | `lagebeschreibung._hebelgeometrie` |
| **2** | Finanzierung raus aus dem Spot-Prompt | BC | `lagebeschreibung._finanzierung` |
| **3** | Fehlende Angaben benennen | BC | `lagebeschreibung._luecken` |
| **4** | Sektorbezug für Themen-ETF | BC | `lagebeschreibung._referenz` |

**Schritt 1 — der Liquidationsabstand.** Das Henne-Ei-Problem aus 35.1 ist
umgangen, nicht gelöst: der Faktor folgt aus dem Stop, den das Modell erst
nennen wird, aber der **Abstand je Faktor** steht vorher fest. Drei
Stützstellen, dieselbe Formel `1/Hebel`, mit der `entscheidungsrechnung` später
`liquidation_etwa_eur` rechnet:

```
Der Abstand zur Zwangsaufloesung haengt allein am Hebelfaktor: bei 3-fach
33 %, also 5.6 Schwankungsbreiten; bei 6-fach 17 %, also 2.8; bei 10-fach
10 %, also 1.7.
Welcher Faktor es wird, folgt aus dem Risikobudget und dem Stopabstand, den
du nennst - gerechnet wird er nach deiner Antwort.
```

**33/17/10 % sind über alle Assets gleich** — allein wären sie ein stehendes
Feld (R-T6). Erst die Schwankungsbreiten daneben machen daraus eine Aussage
über *dieses* Asset: bei einem ruhigen Wert sind 10 % viele ATR, bei einem
unruhigen wenige.

**Grün, nicht gelb:** kein Betrag, keine Warnung, kein „das ist riskant". Die
Finanzierungshöhe bleibt Phase III — sie ist der Hinweis, der die
ERÖFFNEN-Quote von 93 % auf 3 % gedrückt hat.

**Schritt 2 — Funding verlässt den Spot-Prompt.**

| | |
|---|---|
| bisher | in **jedem** Krypto-Prompt, auch Spot |
| gemessen (O-34) | in **63 %** der Spot-Urteile als Beleg zitiert |
| die Sache | eine Zahlung zwischen Long- und Short-Positionen, die ein Spot-Käufer weder leistet noch erhält |

> ⚠️ **Was das kostet, offen gesagt.** Funding war bei Spot der einzige Fakt,
> der nicht aus der eigenen Kursreihe stammte — der *dritte unabhängige Faktor*,
> um den es am 11.08. überhaupt ging. Fällt er weg, sinkt bei manchem
> Spot-Urteil `unabhaengige_faktoren` von 3 auf 2, und daran hängt über
> `tranche_aus_faktoren()` der Betrag. **Es kann also weniger und kleinere
> Spot-Signale geben.**
>
> Das ist trotzdem kein Einschränken: ein Faktor, der zur Sache nichts sagt,
> hat nie getragen — er wurde nur mitgezählt. Und die Information ist nicht
> weg, sie wechselt die Stufe: **Rolle C liest dieselbe Rate als Perzentil,
> für Spot genauso wie für Hebel.** Damit gehört sie bei Spot ab jetzt zu
> genau einem Modell.

Nebenbei entfallen die Börsenabfragen: pro Spot-Durchgang 43, dazu elf für
Aktien, Rohstoffe und ETF, die dort gar kein Symbol haben. Jede davon buchte
ihren Gesundheitsstand in `api_health_status`.

**Schritt 3 — was fehlt, wird benannt.**

```
Fuer dieses Instrument wird KEIN Umsatz ausgewiesen. Das ist eine fehlende
Angabe, kein unauffaelliger Umsatz - ueber die Beteiligung am Markt sagt
diese Beschreibung nichts.
```

Drei Fälle: kein Umsatz · weniger als zwei Marken · Historie unter 250
Handelstagen. **Die Spannung zu R-T6 ist echt** — für alle vier
Rohstoff-Zertifikate steht derselbe Satz, innerhalb der Gruppe also ein
konstantes Feld. Er unterscheidet aber die **Gruppen**, und genau das ist seine
Aufgabe: er sagt einem Urteil über OD7C, dass es auf einem Block weniger steht
als eines über SOL. R-T6 verbietet stehende Felder, weil sie nichts trennen;
dieses trennt.

> **Wortlaut geändert nach einem Fund an ISOC.** Erst stand dort *„liegen keine
> Umsatzdaten vor"*. ISOC hat aber Daten — **2.517 gemeldete Nullen**. Der Satz
> hätte über sich selbst die Unwahrheit gesagt, und das ist schlimmer als kein
> Satz.

**Schritt 4 — der Sektorbezug.**

```
Ueber die letzten 30 Handelstage lief dieser Wert 8.9 Prozentpunkte
schlechter als der breite Markt (S&P-500-ETF).
```

Nichts davon ist neu geholt: `themen_etf/pipeline._compute_sektor_rotation()`
rechnet dieselbe Größe gegen dieselbe SPY-Reihe, seit es Themen-ETF gibt. Sie
hing an der **alten** Pipeline und hat die Rollen-Kette nie erreicht — der
häufigste Befund dieses Projekts, hier noch einmal.

Die Rechnung steht trotzdem neu in `rollen_eingabe`, und zwar aus einem Grund:
die alte Fassung nimmt `[-1]` aus der Datenbank. In der Rollen-Kette gibt es
einen **Ankertag**, und wer die letzte Kerze der Datenbank benutzt, liest im
Backtest die Zukunft. Die Formel ist dieselbe, die Kausalität ist es nicht.

**Für die Absicherung nichts zu tun:** DBPK und 3QSS nennen ihren Referenzindex
bereits (*„hebelt 3-fach auf den Nasdaq-100"*). Die **Lage** dieses Index
gehört nach 36.3 zur zweiten Stufe.

### 38.3 Drei Funde beim Verdrahten — alle drei gefunden durch RENDERN, nicht durch Lesen

> ⚠️ **1. Die Abgrenzung des Sektorbezugs hätte NIE gegriffen.** Meine erste
> Fassung prüfte `assetklasse == "etf"`. Der Aufrufer übergibt aber die
> **Gruppe** — `themen_etf` bzw. `hedge`. `agent/assetklassen.py` hält die drei
> Begriffe in seinem Kopf ausdrücklich auseinander, weil sie sich ähnlich sehen
> und es nicht sind. Kein Test hätte angeschlagen; im gerenderten Faktensatz
> fehlte der Satz sofort sichtbar.

> ⚠️ **2. Derselbe Fehler steckte seit dem 12.08. in der Klassen-Einstufung.**
> `klasse = {"etf": "aktien"}.get(assetklasse, assetklasse)` war ebenfalls gegen
> die Assetklasse geschrieben. **Für `themen_etf` und `hedge` fand die Schleife
> deshalb nie einen Eintrag** — die Einstufung des Leitmarkts fehlte in ihrem
> Prompt, lautlos, weil ein fehlender Schlüssel kein Fehler ist. Drei von fünf
> Gruppen bekamen sie, zwei nicht.

> ⚠️ **3. Die Mail rechnete die Blöcke ein zweites Mal — mit dem falschen ATR.**
> Der Mail-Weg rief `LB.geteilt()` erneut auf und übergab `atr_e` (**EUR**),
> während der Prompt-Weg die Quellwährung übergibt. `_niveaus()` rechnet gegen
> die Quellreihe — **die Mail zeigte dem Leser andere Schwankungsbreiten als
> dem Modell**, bei USD-Assets um den Wechselkurs daneben. Derselbe Fehler wie
> am 12.08. in `leite_zonen_ab()`, nur auf der Anzeigeseite.
>
> Behoben durch Streichen: seit dem 15.08. legt `baue_fall(bloecke_ziel=...)`
> dieselben Blöcke für den Anlassfilter ohnehin daneben. **Die Mail benutzt
> jetzt dasselbe Objekt wie der Prompt** — eine Quelle, eine Rechnung.

### 38.4 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **845, alle bestanden** (14 neue) |
| freie Namen | 0 |
| `pruefe_phase1.py` an echten Reihen | **alle bestanden** |

**Zwei Prüfungen mussten umgeschrieben werden**, weil sie den *alten*
Mechanismus festhielten („es gibt einen zweiten `LB.geteilt()`-Aufruf"). Sie
prüfen jetzt die stärkere Form derselben Absicht: **es gibt nur einen Weg.**

> ⚠️ **Und meine eigene neue Prüfung war zweimal falsch aufgesetzt** — beide
> Male an den Testdaten, nicht am Code:
> * `pruefe_phase1` prüfte gegen die feste Liste aus 34.6. Die ist an einer
>   **anderen Datenbank** erhoben: auf dem Entwicklungsrechner fehlen den vier
>   Rohstoff-Zertifikaten, 3QSS und X136 die Reihen ganz. Die Prüfung meldete
>   einen Fehler, den es nicht gab — und hätte drei echte Funde (CAT, HYPE,
>   MON) als „zuviel" verworfen. **Ein Sollwert aus fremder Datenlage ist kein
>   Sollwert.**
> * In `pruefe_pakete` lief der Gegenfall auf einer streng steigenden Reihe —
>   die hat keine Wendepunkte, also findet `_niveaus()` keine Marke, und der
>   Lücken-Block meldete das völlig zu Recht.

**Neu gefunden an echten Reihen:** CAT (weniger als zwei Marken — dieselbe
kaputte Reihe wie am 06.08.), HYPE (167 Handelstage), MON (232). Alle drei
sagen es jetzt selbst.

### 38.5 Was ab morgen zu beobachten ist

**Der Sektorbezug tickt von selbst** — die relative Stärke ändert sich täglich.
Für die fünf Themen-ETF wird der Anlassfilter damit fast immer „geändert"
melden, genau wie es die Finanzierung bei Krypto tat. `messe_anlass.py`
schlüsselt das je Block auf und wird es zeigen.

**Und die Gegenrichtung:** bei Spot fällt der Finanzierungsblock weg, der sich
alle acht Stunden von selbst bewegte. Dort sollte der Filter **schärfer**
werden. Beides in derselben Messung, beides ab dem ersten Lauf sichtbar.

| offen | |
|---|---|
| Phase III | Aktientermine · Zertifikatsnatur · Finanzierungshöhe — **nur mit gepaartem Vergleich** |
| Phase IV | Nachrichten und Katalysator |
| Rohstoffe | eigener Rechercheschritt (35.4) |
| Rolle A | Terminkalender, Stimmung über BTC hinaus |

---

## Kapitel 39 — Die Regime-Dauer kam im Betrieb nie an (16.08.2026, abends)

Gefunden beim Rendern der Parameterübersicht, nicht durch Lesen.

```
vorher:  Der Gesamtmarkt steht im Regime 'baer'.
jetzt:   Der Gesamtmarkt steht im Regime 'baer', seit 2 Tagen ununterbrochen.
```

**Die Ursache.** `regime_persistenz_tage()` liest über
`get_hebel_regime_tageshistorie()`, und die greift mit `row["tag"]` auf die
Spalten zu — das setzt `conn.row_factory = sqlite3.Row` voraus. `rolle_c`
öffnet aber eine gewöhnliche Verbindung. Der `TypeError` verschwand im breiten
`except Exception: pass`, und in **jeder** Ausgabe stand nur das Regime.

> ⚠️ **Das war genau der Schaden, gegen den die Dauer eingebaut wurde.** Das
> Regime allein ist über alle Signale eines Tages identisch — ein konstantes
> Feld (R-T6). Erst *„seit 27 Tagen"* macht daraus eine Aussage, die sich
> bewegt. Und es ist zugleich das Argument, mit dem in 38.1 begründet wurde,
> warum das Regime bei Rolle C richtig aufgehoben ist. **Es galt zu diesem
> Zeitpunkt nicht.**

**Fail-soft ist fail-silent, hier in seiner teuersten Form:** kein Ausfall, den
man sieht, sondern ein Halbsatz, der fehlt.

**Behoben** durch Leihe statt Übernahme — die Zeilenfabrik wird für den einen
Aufruf gesetzt und danach zurückgestellt, weil `conn` dem Aufrufer gehören
kann. Der Fehlerfang **zählt** jetzt statt zu schlucken.

**Drei neue Prüfungen, funktional statt am Quelltext:** an einer
In-Memory-Datenbank ohne `row_factory` muss `lage()` eine Dauer liefern, der
Satz muss sie tragen, und die Verbindung des Aufrufers muss hinterher
unverändert sein. **848 Prüfungen, alle bestanden.**

---

## Kapitel 40 — Der weitere Plan für LLM1 und LLM2 (16.08.2026, abends)

**Nutzerbefund, der das auslöst:** *„Z.ai ist nur Krypto only — also
unzureichend."* Er trifft. Rolle C fragt heute bei 44 von 56 Assets; die
übrigen zwölf bekommen **keine** Gegenprüfung, und zwar nicht, weil dort keine
zweite Quelle existiert.

### 40.1 Der Befund, der den ganzen Plan trägt

**Die Positionierungsdaten für Aktien, Rohstoffe und Optionen sind gebaut, live
verifiziert — und hängen an den ALTEN Pipelines.**

| Gruppe | zweite Quelle außerhalb der Kursreihe | wo sie liegt | in Rolle C? |
|---|---|---|:--:|
| Krypto | Open Interest · Funding · Long-Konten (Binance) | `positionierung.py` | **ja** |
| Krypto | **Deribit DVOL + Options-Skew** | `krypto/optionsmarkt.py` | nein |
| **Aktien** | **FINRA Short Interest** (VST/PLTR live geprüft, 205 bzw. 138 Punkte) | `api/finra.py` → `aktien/pipeline.py` | nein |
| **Aktien** | **SEC Form 4 Insider-Käufe** | `api/sec_edgar.py` → dieselbe | nein |
| **Aktien** | **Finnhub Analysten-Trend** (Richtung des Konsens) | `api/finnhub.py` → dieselbe | nein |
| **Rohstoffe** | **CFTC COT „Managed Money"** — alle vier Symbole gemappt | `api/cftc_cot.py` → `rohstoff/pipeline.py` | nein |
| **Rohstoffe** | **EIA-Lagerbestände** (Erdgas) | `api/eia.py` → dieselbe | nein |
| ETF / Absicherung | COT auf E-mini S&P 500 / Nasdaq-100 | **nicht gemappt** — die API kann es, wir fragen nicht | nein |

> **Das ist derselbe Befund wie beim Sektorbezug heute Mittag und wie beim
> Auslöser aus `hebel_screening`:** nicht fehlende Daten, sondern fehlende
> Verdrahtung. Es ist der häufigste Fund dieses Projekts.

**Und alle sieben passen zur Konstruktionsbedingung**: sie beschreiben, wie
*andere* aufgestellt sind — nicht, was der Chart sagt. Genau das, was Rolle BC
strukturell nicht sieht.

### 40.2 Was je Rolle offen ist — nach Klasse sortiert

> ⚠️ **KORRIGIERT 17.08.2026 — beide Zeilen unten stimmen nicht mehr.**
>
> **A-1 ist NICHT umsetzbar.** Dort steht *„liegt vor, wird nur für BTC
> gerendert"*. Nachgezählt: die einzige Stimmungsquelle mit Historie ist
> **Fear & Greed** (3.116 Werte, Krypto), `vix_wert` hat **25 Werte** — für
> ein Perzentil zu dünn. Eine Stimmung über BTC hinaus **existiert nicht**.
>
> **Und der „Schatz" `macro_snapshot` ist keiner.** Von 42 Spalten haben
> **sechs** eine brauchbare Historie — und alle vier inhaltlichen davon
> (`fear_greed_value`, `netto_liquiditaet_mrd`, `rendite_10j_pct`,
> `rendite_kurz_pct`) stehen **bereits in Rolle A**. Die übrigen 36 tragen
> zwischen 1 und 100 Werte. Sie sind nicht ungenutzt, sie sind **leer**.

**Rolle A (Marktanalyst) — zwei kleine Lücken, beide grün**

| | Lücke | Datenlage |
|---|---|---|
| A-1 | Stimmung über BTC hinaus | liegt vor, wird nur für BTC gerendert |
| A-2 | Makro-Terminkalender (FOMC, CPI) | **keine Quelle** |

**Rolle BC (Trader) — drei Lücken, alle im Betrieb spürbar**

| | Lücke | Klasse | Datenlage |
|---|---|---|---|
| B-1 | **Auslöser** — der Anlass ist die Uhr | grün | `hebel_screening` rechnet ihn, **niemand liest ihn** |
| B-2 | Handelbarkeit und Spread | **gelb** | gerechnet (Bitpanda-Listung, Override) |
| B-3 | Aktientermine · Zertifikatsnatur · Finanzierungshöhe | **gelb/rot** | teils vorhanden |

**Rolle C (Z.ai) — die große Lücke ist die Abdeckung**

| | Lücke | Datenlage |
|---|---|---|
| C-1 | **44 von 56 Assets, Rest ohne Gegenprüfung** | sieben Quellen gebaut, keine verdrahtet |
| C-2 | Optionsmarkt bei Krypto | gebaut |
| C-3 | Nachrichten / Katalysator | **keine Quelle** |

### 40.3 Der Plan — vier Phasen, Reihenfolge nach Risiko

> **Die Reihenfolge folgt nicht dem Aufwand.** Maßstab bleibt der gemessene
> Vorfall: der Kosten-/Ausführbarkeitshinweis ließ die ERÖFFNEN-Quote von 93 %
> auf 3 % einbrechen. Grün vor gelb, gelb nur mit gepaartem Vergleich.

#### Phase V — Rolle C bekommt alle Assetklassen *(als nächstes)*

Rein additiv: **kein Prompt von LLM1 wird angefasst**, `PROMPT_STAND` bleibt.
Damit ist es der einzige Schritt, der die laufende Messung nicht zerschneidet.

| Schritt | Gruppe | Quelle | Aufwand |
|---|---|---|---|
| **V-1** | **Rohstoffe** | CFTC COT — alle vier Symbole bereits gemappt | klein |
| **V-2** | **Aktien** | FINRA Short Interest + SEC Form 4 | mittel |
| **V-3** | **Krypto** | Deribit DVOL + Skew als fünfter Anhaltspunkt | klein |
| **V-4** | **ETF / Absicherung** | COT auf den Referenzindex — Marktnamen erst verifizieren | mittel |

**Eine Regel für alle vier:** was Rolle C bekommt, darf **nicht** in den
Faktentext von BC. Sonst ist die zweite Stufe wieder, was sie bis gestern war.

> ⚠️ **V-2 hat einen Haken, der vorher zu klären ist.** Finnhub und EIA
> brauchen einen API-Key. Ein Schlüssel gehört ins Gerät, nicht ins Repo —
> und Schlüssel werden zwischen den Geräten **nicht** übertragen.

#### Phase VI — der Auslöser (B-1)

**Die größte Lücke bei BC, und die Daten liegen bereit.** `hebel_screening`
führt Trendfolge- und Kontra-Zweig mit Schwelle 70, gemessen **9,6 %
Kandidaten** — er läuft weiter, und niemand liest ihn.

Der Anlass gehört **vor** den Modellaufruf, nicht in den Prompt: er ist eine
Bedingung, keine Einschätzung (36.2). Zusammen mit O-36 auszuwerten — die
Anlassmessung sagt bis dahin, wie oft dieselbe Frage wiederholt wird.

#### Phase VII — gelb und rot, nur gepaart

| | | Arm A | Arm B |
|---|---|---|---|
| VII-1 | Handelbarkeit/Spread (B-2) | ohne | mit |
| VII-2 | Aktientermine | ohne | mit |
| VII-3 | Zertifikatsnatur bei Rohstoffen | ohne | mit |
| VII-4 | **Finanzierungshöhe als Betrag** (rot) | ohne | mit |

Gleiche Anker, gleicher Anbieter, gleicher Stand — die Methode, mit der 93 → 3 %
überhaupt gefunden wurde.

#### Phase VIII — Nachrichten (C-3)

Die einzige Kategorie, für die **gar keine Quelle** existiert, und laut eigenem
Grundbefund einer von drei Wegen, die das Vorzeichen drehen können. Eigenes
Vorhaben, eigene Recherche.

### 40.4 Was den Plan blockieren kann

| | |
|---|---|
| **Kontingent** | jede neue Quelle ist ein Aufruf je Signal. Vor jedem Schritt: Limits, Kontingent, Dauer |
| **API-Schlüssel** | Finnhub und EIA brauchen einen — pro Gerät, nie übertragen |
| **Messbarkeit** | Phase V ändert LLM1 nicht und ist damit messfreundlich. Ab Phase VI wird jede Änderung zu einem neuen Stand |
| **Rolle C ist selbst ungemessen** | ob sie überhaupt trägt, weiß niemand. **Nach ein paar Betriebstagen zuerst ihre Verteilung ansehen** — sagt sie in 95 % „kein Einwand", ist die Ausweitung auf vier Assetklassen die Ausweitung einer Konstante |

> **Der letzte Punkt ist der wichtigste.** Vier Gruppen anzuschließen, bevor
> bekannt ist, ob die eine funktioniert, wäre Bauen statt Messen. **V-1 ist
> klein genug, um beides zu tun:** Rohstoffe anschließen, dann eine Woche
> Verteilung, dann entscheiden.

---

## Kapitel 41 — Das Aufnahmekriterium für Parameter, verbindlich (16.08.2026, abends)

**Nutzervorgabe, wörtlich:** *„Ein Parameter soll zu einer Rolle aufgenommen
werden, wenn er die erforderlichen Kriterien erfüllt UND für die Aufgabe, also
unser Ziel, tatsächlich geeignet bzw. erforderlich ist — nicht weil ihn eine
Quelle liefert."*

Bis heute gab es dieses Kriterium nicht. Jede Ergänzung wurde einzeln
begründet, und die Begründung lautete meistens *„es ist gerechnet und liegt
ungenutzt herum"*. **Das ist eine Verfügbarkeitsbegründung, keine
Eignungsbegründung** — genau der Einwand des Nutzers.

### 41.1 Die sieben Prüfungen, in dieser Reihenfolge

Die Reihenfolge ist nicht kosmetisch: **der billigste Ausschlussgrund steht
vorn.** Wer zuerst die LLM-Tauglichkeit prüft, formuliert einen Satz sorgfältig
aus, der schon an Prüfung 1 scheitert.

| | Prüfung | Frage | fällt durch, wenn |
|---|---|---|---|
| **P1** | **Auftrag** | Braucht die AUFGABE dieser Rolle den Parameter? | er gehört zur Aufgabe einer anderen Rolle oder zu keiner |
| **P2** | **Eignung** | Ist der Zusammenhang **gemessen** oder **in der Praxis etabliert**? | er ist nur plausibel |
| **P3** | **Nicht-Redundanz** | Sagt er etwas, das die vorhandenen Parameter dieser Rolle nicht schon sagen? | er ist eine weitere Übersetzung desselben Fakts |
| **P4** | **Informationsgrenze** | Hat ihn die andere Stufe schon? | ja — dann verlieren beide Stufen ihre Unabhängigkeit |
| **P5** | **LLM-Tauglichkeit** | Satz mit Maßstab, keine nackte Zahl, kein Etikett? | Rohwert oder Wertung (R-T1/T3/T5) |
| **P6** | **Unterscheidungskraft** | Bewegt er sich über Assets **oder** über die Zeit? | er ist über beides konstant (R-T6) |
| **P7** | **Risikoklasse** | grün, gelb oder rot? | gelb/rot **ohne** gepaarten Vergleich |

**P2 hat drei Stufen, und sie sind nicht gleichwertig:**

| Rang | Beleg | zulässig |
|---|---|---|
| 1 | in unseren Daten **gemessen** | ja |
| 2 | in der **Praxis** durchgängig angewendet | ja — Nutzervorgabe vom 16.08.: *„die Information sollte tragen, weil es in der Praxis so angewendet wird"* |
| 3 | plausibel, aber unbelegt | **nein** |

> **Warum Rang 2 zulässig ist, obwohl er kein Beweis ist.** Rang 1 ist uns
> derzeit weitgehend verschlossen: **kein Verfahren schlägt in unseren Daten die
> Basisrate** (8.441 Fälle, zwei Verfahren, beide Merkmalsfamilien). Bestünde
> man auf Rang 1, dürfte gar nichts aufgenommen werden. Rang 2 ist die
> nächstbeste Vorannahme — und sie ist **falsifizierbar**, weil jeder aufgenommene
> Parameter danach gegen die Basisrate gemessen wird.

### 41.2 Die Obergrenze — Aufnehmen ist nicht kostenlos

**Das ist die zweite Hälfte des Nutzerauftrags und wurde bisher völlig
übersehen.** Ein Parameter mehr ist nicht neutral, sondern verdrängt
Aufmerksamkeit:

| Befund | Quelle |
|---|---|
| **Fünf oder mehr Indikatoren → schlechtere Ergebnisse** als ein bis zwei klare Regeln | eigene Methodik 2.21.3 |
| Ab **12 Indikatoren** verlangsamt sich die Entscheidung messbar (3–8 s je Trade) | Praxisliteratur |
| Eine Standardabweichung mehr Informationskomplexität → **18 % langsamere** Verarbeitung, **23 % längere** Fehlbewertung | Fed-Studie, Überlastungsindex bis 1885 |
| Mehrere Indikatoren erzeugen in der Regel **Redundanz und widersprüchliche Signale**, keine bessere Trefferquote | Praxisliteratur |

> **Daraus folgt eine harte Regel:** ab der Obergrenze ist eine Aufnahme ein
> **Tausch**, keine Ergänzung. Wer etwas aufnimmt, benennt, was dafür geht.

**Vorgeschlagene Budgets** (Aussagen, nicht Datenpunkte):

| Rolle | Budget | heute | Kopfraum |
|---|---|---|---|
| Rolle A | **16** | 15 | 1 |
| Rolle BC | **14** | ~12 (Krypto Spot) | 2 |
| Rolle G | **8** | 4 | 4 |

Rolle BC hat das kleinste Budget bei der größten Lückenliste — **das ist der
eigentliche Engpass des Systems**, und er lässt sich nur durch Streichen von
Redundanz auflösen, nicht durch Hinzufügen.

### 41.3 Was die Recherche bestätigt — und was sie korrigiert

**BESTÄTIGT, und schärfer als erwartet: die Konstruktionsbedingung ist ein
mathematischer Satz, keine Faustregel.**

> Erhalten zwei Prüfer **identische** Eingaben, bildet die Debatte ein
> **Martingal**: die erwartete Korrektheit verbessert sich über Runden **nicht**.
> Sie kommen unabhängig zu denselben Schlüssen, und der Austausch verstärkt nur
> den geteilten Prior. Hinzu kommt: **LLM-Fehler korrelieren zu über 60 %**,
> ein naives Ensemble hat also einen Fehlerboden ungleich null.
>
> **Was hilft, ist gezielte Informationsasymmetrie.** Sie verwandelt das
> Martingal in echte Meinungsrevision. Die Debatte verbessert die Genauigkeit
> des Urteilenden **dann, wenn der Prüfer Information hat, die dem Urteilenden
> fehlt.** Mit komplementärem privatem Wissen fiel der Brier-Score in einem
> Versuch von 0,45 auf 0,004.

Damit ist der Umbau vom 16.08. früh nicht mehr nur begründet, sondern **die
einzige Konstruktion, die überhaupt funktionieren kann**. Und die Messung des
alten Richtungsabgleichs — 17× LONG in 2.469 Prüfungen — ist genau das
vorhergesagte Martingal.

**KORRIGIERT: unsere größte Lücke ist nicht die Positionierung, sondern die
Nachrichten.**

> In einer Ablationsstudie über LLM-Handelsagenten sind **Nachrichten und
> Fundamentaldaten die beiden tragenden Quellen** — sie liefern komplementäre
> Signale (Stimmung bzw. Verankerung). Werden sie nacheinander entfernt,
> **sinkt die kumulierte Rendite**; ohne beide bricht die Leistung deutlich ein.

Das deckt sich mit unserem eigenen Grundbefund (*Nachrichten* als einer von drei
Wegen, die das Vorzeichen drehen können) — **und es stellt die bisherige
Reihenfolge in Frage.** Phase VIII war das Letzte; nach dieser Studie ist es
das Wirksamste.

**PRÄZISIERT: COT trägt nur am Extremwert.**

> Die Positionierung des „Managed Money" ist **dann** aussagekräftig, wenn sie
> **historische Extremwerte** erreicht: Rekord-Netto-Long geht Korrekturen oft
> voraus, extreme Shorts markieren häufig Böden.

**Konsequenz für den Satzbau:** COT gehört als **Perzentil der eigenen
Historie** in den Prompt, nicht als Netto-Position — genau die Form, die die
Finanzierungsrate schon hat. Ein Rohwert würde P5 verletzen und wäre nach
dieser Quelle zusätzlich inhaltlich schwach.

### 41.4 Die Rollen, verbindlich definiert

**Bis heute steht nirgends verbindlich, was die zweite Stufe tut.** Im
`Regelwerksmanual.md` finden sich zwei Halbsätze; alles Übrige lebt in
Code-Kommentaren. Eine Rolle ohne festgeschriebenen Auftrag lässt sich weder
prüfen noch widerlegen.

| | **Rolle A** | **Rolle BC** | **Rolle G** *(Name offen)* |
|---|---|---|---|
| **Stufe** | LLM1, Aufruf 1 | LLM1, Aufruf 2 | LLM2, Aufruf 3 |
| **Aufgabe** | Wie steht der MARKT? | Was tun wir mit DIESEM Wert? | Spricht etwas AUSSERHALB unserer Kursdaten dagegen? |
| **Grundlage** | Leitmärkte, Makro, Stimmung | Kursreihe + Depot + Auftrag + Lagebild | ausschließlich Fremdquellen |
| **darf NICHT** | einzelne Assets beurteilen | Positionsgröße oder Hebel wählen | die Empfehlung kippen |
| **Ausgabe** | Lage + Einstufung je Klasse | Belege, Aktion, Begründung, Falsifikator | Einwand ja/nein/unklar + Grund |
| **Mindestgrundlage** | drei Leitmärkte | Struktur + Bestand + Auftrag | **offen — siehe 41.5** |
| **Messkriterium** | Zuspitzungswächter | gegen die Basisrate | gegen die Basisrate, **plus Verteilung** |

> ⚠️ **Die Benennung ist zu entscheiden.** „Rolle C" ist doppelt vergeben: das
> **C in „BC"** ist der Entscheider in LLM1 (seit dem 10.08. mit B in einem
> Aufruf). Z.ai am 16.08. ebenfalls „C" zu nennen war mein Fehler — und zwar in
> derselben Ecke, in der der Nutzer am 12.08. bereits reklamiert hatte.
> Vorschlag: **Rolle G — Gegenprüfer.** „Z" ist im Projekt für Regeln vergeben
> (Z-2, Z-3).

### 41.5 Bestandsabgleich — alle Parameter gegen die sieben Prüfungen

#### Rolle A — 15 Aussagen

| Parameter | P1 | P2 | P3 | P5 | P6 | Urteil |
|---|:--:|:--:|:--:|:--:|:--:|---|
| Netto-Liquidität (26-Wochen-Bezug) | ✓ | Praxis | ✓ | ✓ | ✓ | bleibt |
| Zinskurven-Spread + Perzentil | ✓ | Praxis | ✓ | ✓ | ✓ | bleibt |
| Trend 250/60 je Leitmarkt (3×) | ✓ | Praxis | ✓ | ✓ | ✓ | bleibt |
| **Spanne Hoch/Tief je Leitmarkt (3×)** | ✓ | Praxis | **⚠** | ✓ | ✓ | **prüfen** |
| Volatilität + Perzentil (3×) | ✓ | Praxis | ✓ | ✓ | ✓ | bleibt |
| Liquidität (Amihud) + Perzentil (3×) | ✓ | Praxis | ✓ | ✓ | ✓ | bleibt |
| Stimmung, nur BTC | ✓ | Praxis | ✓ | ✓ | ✓ | **ausweiten** |

> ⚠️ **P3-Fund, am gerenderten Satz sichtbar:**
> ```
> Bitcoin steht 37.6 % unter seinem Schlusskurs von vor 250 Handelstagen ...
> Bitcoin liegt 37.6 % unter dem Schlusskurs-Hoch dieser 250 Handelstage ...
> ```
> **Dieselbe Zahl in zwei Sätzen.** Liegt das Hoch am Anfang des Fensters — in
> einem Abwärtstrend der Regelfall —, fallen Trend und Spanne zusammen. Der
> zweite Satz sieht dann wie ein zweiter Fakt aus und ist keiner. Bei Aktien
> und Rohstoffen trennen sich die Zahlen; die Redundanz ist also **bedingt**,
> nicht strukturell. **Zu klären, nicht sofort zu streichen.**

#### Rolle BC — Krypto Spot, rund 12 Aussagen

| Parameter | P1 | P2 | P3 | P5 | P6 | Urteil |
|---|:--:|:--:|:--:|:--:|:--:|---|
| Auftrag (2 Sätze) | ✓ | Praxis | ✓ | ✓ | je Gruppe | bleibt |
| Bestand + Gegenseite | ✓ | **gemessen** (KAS-Fall) | ✓ | ✓ | ✓ | bleibt |
| **Struktur (2)** | ✓ | Praxis | **⚠** | ✓ | ✓ | **Familie** |
| **Bewegung (1)** | ✓ | Praxis | **⚠** | ✓ | ✓ | **Familie** |
| **Marken (2)** | ✓ | Praxis | **⚠** | ✓ | ✓ | **Familie** |
| Volumen (2) | ✓ | Praxis | ✓ | ✓ | ✓ | bleibt |
| Lücken (0–3) | ✓ | **gemessen** (KAS-Fall) | ✓ | ✓ | je Gruppe | bleibt |
| Lagebild + Klasseneinstufung | ✓ | Praxis | ✓ | ✓ | ✓ | bleibt |
| Liquidationsabstand (nur Hebel) | ✓ | Praxis | ✓ | ✓ | ✓ | bleibt |
| Sektorbezug (nur ETF) | ✓ | Praxis | ✓ | ✓ | ✓ | bleibt |
| Finanzierung (nur Hebel) | ✓ | Praxis | ✓ | ✓ | ✓ | bleibt |

> ⚠️ **Der größte P3-Befund des ganzen Systems, und er steht seit dem 11.08. im
> eigenen Quelltext:** *„Struktur, Bewegung und Niveaus sind derselbe Fakt in
> drei Übersetzungen."* Das sind **fünf von zwölf Aussagen aus einer Familie.**
>
> Nach mRMR ist genau das der Fall, den man vermeidet: hohe Relevanz, aber hohe
> Redundanz untereinander. Und es erklärt eine eigene Messung, für die es bisher
> keine Erklärung gab — **das Modell zählte in 72 % der Fälle nur ein bis zwei
> unabhängige Faktoren.** Es hat die Redundanz korrekt erkannt.
>
> **Das ist der Grund, warum BC keinen Kopfraum hat.** Der Auslöser, die
> Handelbarkeit und der Katalysator passen erst hinein, wenn die Familie
> zusammengefasst ist.

#### Rolle G — 4 Aussagen

| Parameter | P1 | P2 | P3 | **P4** | P6 | Urteil |
|---|:--:|:--:|:--:|:--:|:--:|---|
| Offene Kontrakte, Änderung | ✓ | Praxis | ✓ | ✓ | ✓ | bleibt |
| Finanzierungsrate, Perzentil | ✓ | Praxis | **⚠ dieselbe Tabelle** | ✓ | ✓ | bleibt |
| Anteil Long-Konten, Perzentil | ✓ | Praxis | **⚠ dieselbe Tabelle** | ✓ | ✓ | bleibt |
| **Marktregime + Dauer** | ✓ | Praxis | ✓ | **✗** | global | **Konflikt** |

> ⚠️ **Zwei Befunde, und beide sind ernst.**
>
> **P3:** die drei Terminmarktzahlen stammen aus **einer** Tabelle
> (`open_interest_snapshot`) und beschreiben dieselbe Menge Menschen auf
> derselben Börse. Drei Zahlen, aber **eine** Quelle.
>
> **P4:** das Regime wird aus **unserer** Kursreihe gerechnet (BTC gegen
> EMA50/200) plus Fear & Greed — beides sieht Rolle A bereits. Streng nach der
> Konstruktionsbedingung gehört es damit auf die LLM1-Seite. Es steht heute bei
> G, weil G sonst nur **eine** Quelle hätte.
>
> **Ehrlich zusammengefasst: Rolle G hat heute eine symbolspezifische
> Fremdquelle.** Nach dem Martingal-Satz ist das der Grenzfall, in dem eine
> Gegenprüfung gerade eben etwas beitragen kann — und keine Reserve hat.

#### Rolle BC — die übrigen fünf Körbe

Die Tabelle oben zeigt Krypto Spot. Die anderen Körbe teilen **dieselben fünf
Grundblöcke** und unterscheiden sich in dem, was dazukommt oder fehlt:

| Korb | Aussagen | zusätzlich | fehlt | P3-Lage |
|---|:--:|---|---|---|
| Krypto Spot | ~12 | — | Auslöser, Handelbarkeit, Katalysator | **Familie 5/12** |
| Krypto Hebel | ~15 | Liquidationsabstand (2), Finanzierung (1) | Kostenhöhe (rot), Haltedauer | Familie 5/15 |
| Aktien | ~12 | — | **Termine, Fundamentaldaten**, Handelszeiten | Familie 5/12 |
| Rohstoffe | ~10 | Lücken-Satz (Umsatz) | Volumen, **Zertifikatsnatur**, Basiswert, Emittent | Familie 5/10 — **am schwersten** |
| Themen-ETF | ~14 | Sektorbezug (2) | TER, Spread, Handelszeiten | Familie 5/14 |
| Absicherung | ~15 | **Absicherungslage (5)** — Exposure, Deckung, Hebelfaktor, nötiger Einsatz, laufende Gebühr | Volumen, zweite Marke | Familie 5/15, **am günstigsten** |

> **Zwei Dinge fallen dabei auf.**
>
> **Die Absicherung ist die am besten zugeschnittene Gruppe** — als einzige hat
> sie einen eigenen, auftragsspezifischen Block, und der besteht aus fünf
> Aussagen, die zu keiner anderen redundant sind.
>
> **Rohstoffe sind der schlechteste Fall:** die wenigsten Aussagen, davon der
> größte Anteil aus der redundanten Familie, und die einzige Gruppe, bei der
> die Natur des Instruments (Zertifikat, Emittent, Bezugsverhältnis) im Prompt
> gar nicht vorkommt.

#### Was dieser Abgleich NICHT abdeckt

**Er ist vollständig für die Parameter, die heute im Prompt stehen — und für
nichts darüber hinaus.** Ausdrücklich offen:

| offen | warum |
|---|---|
| **P2 auf Rang 1** (gemessen) für fast alle Zeilen | steht auf „Praxis", weil kein Verfahren die Basisrate schlägt. Das ist kein Versäumnis dieses Abgleichs, sondern der Stand des Projekts |
| **P7 (Risikoklasse)** je Zeile | nur für die Neuzugänge vergeben; die Altbestände sind nie eingestuft worden |
| **Rolle G für Aktien, Rohstoffe, ETF** | es gibt sie nicht — nichts abzugleichen |
| **Die alte Kette** (`krypto/`, `aktien/`, `rohstoff/`, `hedge/`, `themen_etf/`) | läuft parallel mit eigenen, viel größeren Faktenblöcken. Dieser Abgleich betrifft **nur** die Rollen-Kette |
| **Ausgabeseite** | was die Rollen ZURÜCKgeben, ist hier nicht geprüft — eigener Schritt |

### 41.6 Was daraus für die Reihenfolge folgt

**Die Recherche dreht meine eigene Priorität an zwei Stellen:**

| | bisher | jetzt | Grund |
|---|---|---|---|
| Nachrichten | Phase VIII, zuletzt | **hoch** | Ablationsstudie: Nachrichten und Fundamentaldaten tragen; ohne sie sinkt die Rendite |
| Deribit für Krypto | Phase V-3 | **zurück** | DVOL/Skew stehen für **BTC als marktweites Barometer** — innerhalb Krypto bekäme jeder Coin denselben Satz. Global wie das Regime, keine symbolspezifische Quelle |
| Redundanz bei BC | gar nicht im Plan | **neu, vorn** | fünf von zwölf Aussagen sind eine Familie; ohne Zusammenfassen kein Kopfraum |
| CFTC / FINRA | Phase V-1 / V-2 | **bleibt vorn** | die einzigen symbolspezifischen Fremdquellen, die wir schon haben |

**Und eine Regel, die ab jetzt für jeden Schritt gilt:** vor der Umsetzung wird
der Parameter durch P1–P7 geschickt und das Ergebnis im Plan vermerkt. Fällt er
durch, steht **warum** dort — nicht nur, dass er nicht kam.

**Quellen:**
[Diverse Evidence, Better Forecasts — Deliberation unter Informationsasymmetrie](https://arxiv.org/html/2607.01661v1) ·
[StockBench — Ablation über Datenquellen](https://arxiv.org/html/2510.02209v1) ·
[Fed: Effects of Information Overload on Financial Markets](https://www.federalreserve.gov/econres/ifdp/effects-of-information-overload-on-financial-markets-how-much-is-too-much.htm) ·
[mRMR — Relevanz und Redundanz](https://en.wikipedia.org/wiki/Minimum_redundancy_feature_selection) ·
[CFTC Commitments of Traders](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm) ·
[Are more indicators better for trading decisions?](https://www.swissquote.com/en-ch/private/inspire/blog/technical-analysis/are-more-indicators-better-trading-decisions)

---

## Kapitel 42 — Basis-Sets je Rolle, und der Klasse-1-Umbau (16.08.2026)

### 42.1 „LLM-Integration prüfen" sind ZWEI Prüfungen

**Nutzervorgabe, wörtlich:** *„Wenn ich sage die LLM-Integration zu PRÜFEN — sind
das zwei Sachen. 1. Benötigen wir diesen Parameter im LLM oder ist dieser
schädlich, Bias, Zahlen etc. für unsere Bewertung. 2. Wenn erforderlich, dann
korrekt für das LLM übersetzen, damit wir keine Nebeneffekte, sondern das
gewünschte Ziel erreichen."*

P5 aus Kapitel 41 zerfällt damit in zwei, und die erste ist die härtere:

| | Frage | fällt durch, wenn |
|---|---|---|
| **P5a** | **Gehört der Parameter überhaupt ins Modell?** | er verzerrt, etikettiert oder verdrängt mehr, als er trägt |
| **P5b** | **Ist er korrekt übersetzt?** | Rohwert, fehlender Maßstab, Wertung im Satz |

**P5a hat in diesem Projekt eine gemessene Grundlage** — es ist kein
theoretischer Punkt:

| Parameter | Wirkung | Urteil |
|---|---|---|
| Kosten- und Ausführbarkeitshinweis | ERÖFFNEN **93 % → 3 %** | P5a **durchgefallen** |
| Etikett *„intakter Abwärtstrend"* | Modell gewichtete das Wort hoch, die Zahl daneben gering | P5a **durchgefallen** |
| Konfidenz in Prozent | 77,5 % vorhergesagt gegen 33,3 % tatsächlich | P5a **durchgefallen** |
| Marktbreite | Richtung gemessen **invers** | P5a **durchgefallen** |
| nackte Zahlen (`"rsi_14": 55.0`) | Tokenisierung zerlegt sie | P5b **durchgefallen** |
| **doppelt genannte Zahl** | Wiederholung wirkt wie Position (R-T9) | **P5b, neu — siehe 42.3** |

**Vier von sechs Fällen sind P5a.** Die Frage „schadet er?" hat in unserer
eigenen Geschichte mehr Parameter aussortiert als die Frage „ist er richtig
formuliert?".

### 42.2 Die Basis-Sets — was jede Rolle mindestens braucht

Bisher gab es eine **Liste des Vorhandenen**, kein Soll. Ein Basis-Set leitet
sich aus der **Aufgabe** ab, nicht aus der Datenlage.

#### Rolle A — Marktanalyst · Basis-Set 4+2

| # | Praxis verlangt | haben wir | P5a | P5b | Status |
|---|---|---|:--:|:--:|---|
| A1 | Trend je Leitmarkt | 250/60 Tage, 3 Leitmärkte | ✓ | ✓ | **erfüllt** |
| A2 | Volatilität | täglich + Perzentil | ✓ | ✓ | **erfüllt** |
| A3 | Breite | **ersatzlos gestrichen** — Richtung invers | **✗** | — | **begründet weg** |
| A4 | Liquidität/Makro | Amihud + Netto-Liquidität + Zinskurve | ✓ | ✓ | **erfüllt** |
| A5 | Stimmung | **nur BTC** | ✓ | ✓ | Lücke, billig |
| A6 | Terminkalender | ✗ | ✓ | offen | **Lücke** |

**3 von 4 Kerndimensionen, die vierte an P5a gescheitert.**

#### Rolle BC — Händler · Basis-Set CSTI + 4

| # | Praxis verlangt | haben wir | P5a | P5b | Status |
|---|---|---|:--:|:--:|---|
| **C** | Bedingung | Lagebild + Klasseneinstufung | ✓ | ✓ | **erfüllt** |
| **S** | Aufbau | Struktur + Marken | ✓ | ✓ | **erfüllt** |
| **T** | **Auslöser** | ✗ — `hebel_screening` läuft, niemand liest es | ✓ | offen | **LÜCKE** |
| **I** | Widerlegung | Pflichtfeld + Preis + Datum | ✓ | ✓ | **erfüllt, stark** |
| Z1 | Umsatzbestätigung | ✓, Fehlen benannt | ✓ | ✓ | **erfüllt** |
| Z2 | mehrere Zeitebenen | 5/20/60, ohne Ausrichtungsaussage | ✓ | teilw. | teilweise |
| Z3 | Liquidität/Spread | ✗ | **fraglich** | — | **LÜCKE, gelb** |
| Z4 | Katalysator | ✗ | ✓ | offen | **LÜCKE** |
| — | Positionsgröße | **nicht beim Modell** | — | — | besser als Praxis |

> **Z3 ist der Fall, an dem P5a wirklich beißt.** Handelbarkeit und Spread
> stehen in jeder Praxisliste — und ihr nächster Verwandter, der
> Ausführbarkeitshinweis, hat die ERÖFFNEN-Quote von 93 auf 3 % gedrückt.
> **Praxisbedarf und LLM-Verträglichkeit widersprechen sich hier.** Nur mit
> gepaartem Vergleich, sonst gar nicht.

**Je Korb obendrauf:** Krypto Hebel 1/3 · Aktien **0/3** · Rohstoffe **0/4** ·
Themen-ETF 1/3 · Absicherung **4/4**.

> ⚠️ **Fund ohne bisherige Zuordnung:** die Ablationsstudie nennt Nachrichten
> **und Fundamentaldaten** als die beiden tragenden Quellen. Die
> Fundamentaldaten **haben wir** — KGV, Forward-KGV, Gewinnwachstum,
> Dividendenrendite, Analystenkonsens, **nächster Quartalstermin** — in
> `api/yfinance_client.py`, benutzt von der **alten** Aktien-Pipeline. In der
> Rollen-Kette gehören sie **keiner Rolle**. Nach P1 gehören sie zu **BC**: sie
> beschreiben die Qualität *dieses* Wertes, nicht die Aufstellung anderer.

#### Rolle G — Gegenprüfer · Basis-Set nach EIGENSCHAFT

**Für „zweites Modell prüft erstes" gibt es keinen Praxismaßstab.** Die
Debattenliteratur liefert stattdessen eine Bedingung — und damit ein Basis-Set,
das nicht aus einer Liste besteht:

| # | Bedingung | heute |
|---|---|:--:|
| G1 | mindestens **zwei unabhängige Quellen** | ✗ — **eine** |
| G2 | davon mindestens eine **symbolspezifisch** | ✓ |
| G3 | **keine** davon im Faktentext von BC | ✓ |
| G4 | jede Aussage als Perzentil/Extremwert | ✓ |
| G5 | für **jede** Assetklasse erfüllbar | ✗ — nur Krypto |

| Klasse | Quelle 1 | Quelle 2 | Status |
|---|---|---|---|
| Krypto | Binance OI/Funding/Long ✓ | **fehlt** | **1 von 2** |
| Aktien | FINRA Short Interest | SEC Form 4 | **2 von 2, unverdrahtet** |
| Rohstoffe | CFTC COT (4 Symbole gemappt) | EIA | **2 von 2, unverdrahtet** |
| ETF / Absicherung | COT auf Index-Futures | Nachrichten | **0 von 2** |

> **Der Befund kehrt sich um: Aktien und Rohstoffe hätten das vollständige
> Basis-Set — Krypto, die einzige Klasse, für die Rolle G heute läuft, erreicht
> es nicht.**

### 42.3 Klasse 1 — gebaut, in einem Zug

**Rolle BC: eine wörtliche Doppelung.**

```
_struktur:  b60 = 100.0 * (c[i] / c[i - 60] - 1.0)
_bewegung:  100.0 * (c[i] / c[i - tage] - 1.0)     # tage = 60
```

| | |
|---|---|
| identische Zahl in beiden Blöcken | **42 von 42 Reihen** |
| abweichend | **0** |

**Zwei Schäden, nicht nur Redundanz:**

**Gewicht** — eine Zahl, die zweimal dasteht, wiegt schwerer. Dieselbe Mechanik
wie R-T9, nur über Wiederholung statt Position, und **nicht beabsichtigt**.

**Messung** — `messe_begruendungen.py` ordnet Belege ihrem Block zu. Die Anker
*„zum vergleich"* und *„60 handelstage"* standen unter `bewegung`, der Satz aber
in `struktur`. **Die Blockmessung lief durch genau den Fehler, den sie messen
sollte.**

**Gelöst durch Zusammenlegen, nicht durch Löschen:**

```
[verlauf] Auf Sicht der letzten 17 Handelstage zeigt die Marktstruktur hoehere
          Hochs und hoehere Tiefs; der letzte Wendepunkt liegt 9 Handelstage
          zurueck.
[verlauf] Kursentwicklung im selben Rahmen: 5 Tage -2.5 %, 20 Tage -10.3 %,
          60 Tage -32.0 %.
```

Die 60-Tage-Zahl wurde am 11.08. **absichtlich** neben die Strukturaussage
gesetzt (ETH-Fall: Etikett hoch gewichtet, Zahl daneben gering). Das
Zusammenlegen **erhält die Nachbarschaft** und entfernt nur die zweite Nennung.
Eine reine Löschung hätte den Fix von damals rückgängig gemacht.

**Rolle A: dieselbe Doppelung, bedingt — und aufgewertet statt gestrichen.**

```
vorher:  Bitcoin liegt 37.6 % unter dem Schlusskurs-Hoch und 9.9 % ueber dem
         Schlusskurs-Tief dieser 250 Handelstage.
jetzt:   ... dieser 250 Handelstage; das Hoch liegt 250 Handelstage zurueck,
         das Tief 19.
```

Der Abstand allein fällt mit dem Satz davor zusammen, sobald das Hoch am
Fensteranfang liegt. **Die Lage der Extrema in der Zeit steht sonst nirgends** —
ein Hoch von vor 240 Tagen beschreibt eine andere Lage als eines von vor 12, bei
identischem Abstand. Und im BTC-Fall erklärt der Satz jetzt selbst, **warum**
die Zahl sich wiederholt.

**Z.ai heißt ab jetzt Rolle G.** „Rolle C" war doppelt vergeben — das C in „BC"
ist der Entscheider in LLM1. `Rolle BC` bleibt unangetastet.

### 42.4 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **853, alle bestanden** (8 neue) |
| freie Namen | 0 |
| `pruefe_phase1.py` an echten Reihen | bestanden |
| Reihen mit wiederholter Prozentzahl im `verlauf`-Block | **0 von 42** |
| Belegzuordnung | Struktur- **und** Bewegungssätze → `verlauf` |

> ⚠️ **Drei eigene Fehler in dieser Runde, alle beim Prüfen, nicht beim Bauen:**
>
> **Der Blockname mit Leerzeichen.** Um zwei Wörterbuch-Einträge für denselben
> Block zu führen, hatte ich den Schlüssel `"verlauf "` benutzt. Das hätte
> funktioniert und in **jeder Auswertung lautlos einen zweiten, fast
> gleichnamigen Block** erzeugt. Jetzt zwei getrennte Tabellen, und eine
> Prüfung verbietet Leerraum in Blocknamen.
>
> **Die streng steigende Testreihe, zum zweiten Mal.** Sie hat keine
> Wendepunkte, also liefert `_struktur()` gar keinen Satz — der Test maß eine
> Reihe statt der Zusammenlegung. Derselbe Stolperstein wie beim
> Lücken-Gegenfall am Vortag.
>
> **Der Suchtext über einen f-String-Umbruch.** `"das Hoch liegt {wo_hoch}
> Handelstage zurueck"` steht im Quelltext auf zwei Zeilen verteilt und war als
> ein Stück nicht zu finden.

### 42.5 Was als Nächstes ansteht

| | Schritt | Klasse |
|---|---|---|
| 1 | **Auslöser (T)** aus `hebel_screening` — vor den Aufruf, nicht in den Prompt | grün |
| 2 | **Rolle G: Rohstoffe (CFTC) und Aktien (FINRA)** — dort ist das Basis-Set vollständig erfüllbar | additiv |
| 3 | **Fundamentaldaten und Termine zu BC** — als **Tausch**, nicht als Ergänzung | grün/gelb |
| 4 | Klasse 2 (`struktur` ↔ `marken`) | **erst nach der Blockmessung** |

---

## Kapitel 43 — Die Abrufkette von Anfang bis Ende, simuliert (16.08.2026)

**Nutzervorgabe:** *„die Abrufkette prüfen und simulieren bzw. testen — von
Anfang bis zum Ende."* Ergebnis: `simuliere_kette.py`, und der erste Lauf hat
gefunden, dass **Rolle G nie gelaufen ist.**

### 43.1 Warum eine Simulation, wo es 855 Prüfungen gibt

Die Paketprüfungen sind **statisch**. Sie lesen Quelltext und rufen einzelne
Funktionen — und haben an einem einzigen Tag viermal etwas nicht gefunden, das
beim Durchlaufen sofort sichtbar wurde:

| | gefunden durch |
|---|---|
| Sektorbezug greift nie (`etf` statt `themen_etf`) | Rendern |
| Klassen-Einstufung erreicht 2 von 5 Gruppen nie | Rendern |
| Mail rechnet Blöcke neu, mit ATR in EUR | Lesen |
| **Rolle G läuft nie** | **Simulation** |

> **Eine Kette, die in jedem Einzelteil stimmt, kann als Ganzes reissen.**

**Aufbau:** Betriebsart `probe` gegen eine **Kopie** der Datenbank, echte
Kursreihen, echte Fakten, echte Rechnung, echtes Schreiben, echter Mailaufbau —
**Attrappe nur für die drei Modellaufrufe**. Die Attrappe spielt je Instrument
**jede** Aktion des Vokabulars durch, `NICHTS_TUN` wie `ERÖFFNEN`.

### 43.2 Der Fund: Rolle G hat nie stattgefunden

```python
sym = str(urteil.get("symbol") or urteil.get("asset") or "").strip().upper()
if not sym:
    return None
```

`urteil` ist die validierte Antwort von Rolle BC. Nachgezählt trägt sie **20
Schlüssel — `symbol` ist keiner davon**, `asset` auch nicht.

> **`sym` war immer leer. Die Funktion kehrte in der zweiten Zeile zurück.**
> Kein Fehler, kein Logeintrag, keine Zeile in der Mail. Die zweite Stufe war
> seit ihrem Bau am 16.08. ein Aufruf, der nie stattfand.

Und gestern habe ich sie für fertig erklärt: Anhaltspunkte gemessen (44
Assets), Bestätigungszweig gebaut, Mailabschnitt geprüft, 831 Prüfungen grün.
**Alles davon war richtig — und alles davon prüfte Teile.**

**Behoben:** das Symbol kommt vom Aufrufer. Der Rückfall auf das Urteil bleibt
stehen, der Betriebspfad verlässt sich nicht mehr darauf.

### 43.3 Drei weitere Funde derselben Runde

> ⚠️ **Die Konsistenzprüfung lief noch — obwohl sie am 16.08. abgelehnt wurde.**
> Nutzer, wörtlich: *„das brauche ich nicht — war nie meine Anforderung."* Ich
> habe darauf Rolle G gebaut und die alte Prüfung **weiterlaufen lassen**: ein
> Z.ai-Aufruf je Signal und in jeder Mail die Zeile *„Ein zweites Modell nennt
> die Begründung …"*.
>
> Sie verletzt zudem R-R2 in Reinform — voller Faktentext von Rolle BC **plus**
> deren Begründung, also identische Informationsgrenze. Entfernt; Prompt bleibt
> lesbar stehen.

> ⚠️ **Der Andrangdeckel hing an genau dieser Prüfung.** `MAX_GLEICHZEITIG = 2`
> wirkte nur über `_mit_platz(G.pruefe_konsistenz, …)`. Weder der
> Richtungsabgleich noch Rolle G liefen je hindurch. Mit dem Entfernen wäre er
> **ersatzlos verschwunden** — und `rollen_lauf` startet einen Faden je Signal.
> Zehn Signale, zehn gleichzeitige Aufrufe: der Zustand vom 14.08.
>
> **Gefangen von der eigenen Paketprüfung**, die auf *„die Bremse sitzt am
> Anbieter, nicht am Lauf"* bestand.

> ⚠️ **Der Modulkopf beschrieb zwei Tage lang eine Konstruktion, die es nicht
> mehr gab** — „Eigene Richtung", „`mehrheit()`", „4 sequenzielle Aufrufe je
> Einstieg". Wer dort las, las den Stand vom 13.08.

**Und die Umbenennung war unvollständig:** „Rolle C" stand noch fünfmal in der
Fakten-Entscheidungsmappe und in Umbauplan Kapitel 32 — beides von mir selbst,
am Tag zuvor geschrieben.

### 43.4 Was die Simulation NICHT geprüft hat

**Diese Zeilen sind wichtiger als die Fehlerzahl.** Ein Lauf, der die Hälfte
der Körbe überspringt und „0 Fehler" meldet, ist die gefährlichste Sorte grün —
und genau das war der erste Durchgang.

| | |
|---|---|
| gelaufen | aktien/spot · krypto/spot · **krypto/hebel** · themen_etf/spot |
| **übersprungen** | **hedge/absicherung** und **rohstoffe/spot** — im Entwicklungsbestand fehlen die Kursreihen |

> **Der Hebel lief im ersten Durchgang auch nicht.** Seit dem 15.08. ist
> `hebel_pruefung_erlaubt` standardmässig **falsch**, also fielen alle
> Hebel-Symbole an der Auftragsstufe heraus — und der Lauf meldete „0 Fehler",
> ohne 77 % der Produktionsaufrufe berührt zu haben. Die Simulation schaltet
> den Schalter jetzt **in der Kopie** ein.

### 43.5 Was am Ende ankommt

```
4 Gruppen, 8 Signale, 9 Mails, 0 Fehler, 0 Luecken
signals: KAUFEN 3 · NACHKAUFEN 4 · REDUZIEREN 1 · HEBEL_ERHÖHEN 1 · ERÖFFNEN 1
anlass_beobachtung: 10 Zeilen
```

Geprüft wird nicht nur, **dass** nichts abstürzt, sondern **dass die Sätze
ankommen**: der `verlauf`-Block in jeder Mail, der Liquidationsabstand in jeder
Hebel-Mail, Rolle G bei **Krypto** — und bei Aktien und ETF ausdrücklich
**NICHT**, weil dort keine Positionierungsdaten vorliegen (R-R3/G5).

### 43.6 Reihenfolge, neu begründet

| | | warum jetzt |
|---|---|---|
| **1** | ~~Rolle G ans Laufen bringen~~ | **erledigt** — sie war der Blocker für alles Weitere |
| **2** | **Rohstoffe und Absicherung in die Simulation** | zwei von sechs Körben sind ungeprüft; das ist die grössere Lücke als jede neue Quelle |
| **3** | D-1 `.docx`-Pendants, D-2 Abhängigkeitsmatrix | Dokumentation, blockiert nichts |
| **4** | Rolle G für Rohstoffe (CFTC) | braucht eine Persistenzschicht — COT wird nicht gespeichert |

**Und ein Satz, der ab jetzt gilt:** eine Stufe gilt erst als gebaut, wenn
`simuliere_kette.py` sie **in der fertigen Mail** nachweist. Rolle G war drei
Tage lang „fertig".

---

## Kapitel 44 — Produktionsanalyse am NB-Export vom 16.08. (16.08.2026)

**Nutzervorgabe:** *„wichtig immer sauber gegenprüfen, damit wir nichts
verschlimmbessern auf Basis einer Annahme oder eines fehlenden Logeintrags."*

### 44.1 Der Kursstillstand — zwei Tage alte Charts für 77 % der Aufrufe

**In der Signalmail sichtbar:** *„BNB · Kurs 523,48 EUR · **2026-08-14**"* — in
einer Mail vom Sonntag, 16.08. 09:15.

**Im Export bestätigt:** **alle 61 Kursreihen enden am Freitag, 14.08.** Auch
BTC, ETH, SOL — Werte, die rund um die Uhr handeln.

```
2026-08-14 20:57  Kraken-OHLC-Refresh: 37/57 Assets aktualisiert
2026-08-16 00:14  Aktien-OHLC-Refresh: 2/2      (kein Kraken-Lauf)
2026-08-16 06:40  Aktien-OHLC-Refresh: 2/2      (kein Kraken-Lauf)
2026-08-16 07:55  Aktien-OHLC-Refresh: 2/2      (kein Kraken-Lauf)
```

**Drei Dinge mussten zusammenkommen** — jedes für sich harmlos:

| | |
|---|---|
| **Takt** | 24 Stunden, und er beginnt bei **jedem Neustart neu**. Am 16.08. wurde dreimal neu gestartet — der reguläre Lauf kam nie dran |
| **Sofortlauf** | greift erst bei **mehr als zwei** Tagen Rückstand. Freitag → Sonntag sind **genau zwei** |
| **Watchdog** | benutzt **dieselbe** Schwelle und griff deshalb ebenfalls nicht |

Der letzte Kraken-Lauf am 14.08. 20:57 kam nur zustande, weil ein Neustart ihn
auslöste — die Reihen waren damals *mehr* als zwei Tage alt.

> **Die Rollen-Kette urteilte am Sonntag auf Charts vom Freitag.** Struktur,
> Marken, Bewegung, Volumen — alles zwei Tage alt. Für Krypto, also **77 % aller
> Aufrufe**.

**Korrigiert, und zwar schmal.** `HISTORY_STALE_THRESHOLD_DAYS = 2` bleibt
unangetastet — an ihr hängen die Anzeige und das Datenqualitäts-Gate **R-5.0**
der alten Kette. Stattdessen bekommt der Kraken-Check eine **eigene, engere**
Schwelle:

```python
KRYPTO_OHLC_STALE_THRESHOLD_DAYS = 1
```

`_ohlc_data_is_stale()` sieht **ausschliesslich Kraken-gelistete Assets** an,
also Krypto — und dort ist ein Rückstand von zwei Tagen kein Wochenende,
sondern ein Ausfall.

**Nachgerechnet am echten Fall:**

| Kerze | heute | Rückstand | alt (> 2) | neu (> 1) |
|---|---|---|---|---|
| 14.08. | 16.08. | 2 Tage | **schweigt** | **schlägt an** |
| 15.08. | 16.08. | 1 Tag | schweigt | schweigt |

**Warum nicht 0:** die Kerze des laufenden Tages entsteht erst mit seinem Ende.
„Älter als heute" wäre dauerhaft wahr und liesse den Nachholer im
Watchdog-Takt feuern statt alle 24 Stunden — eine Verschlimmbesserung.

### 44.2 Die Doppelung, in der echten Mail

```
Zum Vergleich: ueber 60 Handelstage steht der Kurs -1.9 %.
Kursentwicklung: 5 Tage +0.6 %, 20 Tage +6.5 %, 60 Tage -1.9 %.
```

**Der Klasse-1-Befund, im Produktionstext.** Behoben am 17.08. (Kapitel 42.3);
dieselbe Mail zeigt zugleich den neuen Liquidationsabstand aus Phase I.

### 44.3 Die Gegenprüfung, Tag für Tag

| Tag | Rollen-Signale | Konsistenz | Richtungsabgleich |
|---|---|---|---|
| 14.08. | 46 | 11 | 2 |
| 15.08. | 180 | 57 | 30 |
| **16.08.** | **59** | **25** | **0** |

**Alles drei bestätigt sich an echten Daten:**

* **Der Richtungsabgleich ist sauber aus** — 0 am 16.08., letzter Eintrag
  15.08. 20:14. Die Stilllegung hat gewirkt.
* **Die Konsistenzprüfung lief weiter** — 25 von 34 Einstiegen an einem halben
  Tag. Genau die, die der Nutzer am 16.08. abgelehnt hatte. Am 17.08. entfernt.
* **Rolle G hat null Einträge** — sie hat nie stattgefunden (Kapitel 43.2).

> Die 28 Z.ai-Aufrufe des Diagnosebildschirms waren also **nicht** die
> Gegenprüfung, die gewünscht war, sondern die, die abgelehnt war.

**Nebenbefund:** 9 von 34 Einstiegen bekamen gar keine Prüfung — Andrang oder
Zeitüberschreitung. Mit einem Aufruf statt vier sollte das verschwinden.

### 44.4 Was NICHT defekt ist — geprüft statt vermutet

| Vermutung | Befund |
|---|---|
| Marktscan kaputt | **nein.** Er läuft (cron 4 und 16 Uhr): *„34 Kandidaten bewertet (0 Treffer, Regime baer)"*. Die Mail feuert nur bei `kaufkandidat`; die Schwelle liegt bei Score 70, und im Bärenregime erreicht keiner der 34 auch nur 50. Letzter Kaufkandidat: Juli |
| Altbestand läuft mit | **nein.** Alle 59 Signale des 16.08. tragen `quelle_kette: rollen`. Budget-Allocator und Multi-Asset-Batch überspringen sich selbst |
| 11.970 Tracebacks | **behoben.** 11.953 davon sind **ein** Fehler, alle am 14.08. zwischen 09:35 und 10:11 — 36 Minuten, bevor der NB den Fix `4cd8d68` zog. Seither keiner mehr |
| Doppelte Ausstiegsmails | **nein.** Der Ausstiegs-Job lief in 72 Stunden **kein einziges Mal** (offener Punkt A2b) |

> ⚠️ **Zwei eigene Fehlgriffe in dieser Analyse, beide gefangen:** ich habe die
> Z.ai-Belegung zuerst über die Spalte `zai_urteil` gezählt — sie heisst
> `zai_gegenpruefung_urteil` — und daraufhin „0 von 285" gemeldet. Und einmal
> `zai_stimmen` statt des Urteils. **Beide Male wäre der Schluss gewesen, die
> Gegenprüfung erreiche die Datenbank nicht.** Sie tut es.

### 44.5 Was offen bleibt

| | |
|---|---|
| **A2b** | der Ausstiegs-Job ist in 72 Stunden nicht gelaufen |
| **Signalzahl** | 30 ERÖFFNEN am 16.08., in zwei Wellen zu je ~15 in drei Minuten |
| **Fehlalarm-Muster** | `pruefe_export_standard.py` meldet „11970 Tracebacks im Log-Fenster" **ohne Zeitbezug**. Eine grosse Zahl aus 36 Minuten von vor zwei Tagen liest sich wie ein akuter Ausfall |

---

## Kapitel 45 — A2b geklärt, und die Basislinie vor dem glatten Schnitt (16.08.2026)

### 45.1 A2b: der Ausstiegs-Job ist NICHT defekt — er hatte keine Gelegenheit

| | |
|---|---|
| Zeitplan | **Cron, täglich 07:15 lokal** |
| Schalter | **aktiv** (`risiko.ausstieg_trailing_ausloese_r = 1,0`) |
| Ausführungen im 48-h-Fenster | **0** |
| Misfire-Meldung | **keine** |

**Der Grund steht in den Loglücken:**

```
2026-08-14 21:58 bis 2026-08-15 07:57    599 min   ← 07:15 liegt darin
2026-08-16 06:46 bis 2026-08-16 07:55     69 min   ← 07:15 liegt darin
```

**An beiden Tagen lief die App zur Cron-Zeit nicht.**

> ⚠️ **Und das ist der eigentliche Befund, größer als A2b:**
>
> **Die App war 24,6 von 48 Stunden aus — 51 %.** 16 Fenster über zehn
> Minuten, elf Neustarts.

**Damit erklären sich alle „Jobs, die nie laufen" auf einen Schlag:**

| Job | Ausführungen | Takt |
|---|---|---|
| `refresh_prices_job` | 107× | 15 min |
| `hebel_screening_job` | 106× | 15 min |
| `refresh_ohlc_job` | **1×** | **24 h** |
| `backward_tracking_job` | **1×** | lang |
| `portfolio_wert_job` | **1×** | lang |
| `ausstiegs_job` | **0×** | **Cron 07:15** |

**Kurze Takte treffen, lange nicht.** Ein 24-Stunden-Job kann nicht laufen,
wenn die längste ununterbrochene Laufzeit darunter liegt — und der Takt bei
jedem Neustart neu beginnt. Ein fester Cron trifft nur, wenn die App zufällig
gerade oben ist.

**Das ist die gemeinsame Wurzel des Kursstillstands (44.1) und von A2b.** Der
Frischefix von heute macht den Start robust und ist richtig; er behebt aber
nicht, dass das Notebook — laut Projektbeschreibung ein **24/7-Server** — zur
Hälfte nicht läuft.

**Was NICHT zu tun ist:** den Cron auf ein kurzes Intervall stellen. Der Job
schickt eine Mail; ein 15-Minuten-Takt wäre Mailflut. Die saubere Lösung
braucht einen **Zeitstempel des letzten Laufs**, damit beim Start nachgeholt
werden kann, was heute noch nicht lief. Das berührt das Schema und ist deshalb
eine Entscheidung, keine Nebenbei-Korrektur.

### 45.2 Die Basislinie — `messe_basislinie.py`

**Nutzervorgabe:** *„halte den alten Stand fest … um einen Vergleich bzw.
Anhaltspunkte für nach dem LLM-Umbau zu haben."*

Festgehalten in `Basisinfos/basislinie_vor_schnitt.json`, Stand **NB-Export
16.08. 09:41**.

**Durchsatz und Gegenprüfung:**

| Tag | Signale | Einstiege | Konsistenz | Richtungsabgleich |
|---|---|---|---|---|
| 14.08. | 46 | 11 | 11 | 2 |
| 15.08. | **180** | **92** | 57 | 30 |
| 16.08. | 59 | 34 | 25 | **0** |

**Aktionen:**

```
14.08.  HALTEN 24 · REDUZIEREN 9 · KAUFEN 8 · NACHKAUFEN 3 · VERKAUFEN 2
15.08.  ERÖFFNEN 67 · HALTEN 62 · REDUZIEREN 24 · KAUFEN 14 · NACHKAUFEN 11
16.08.  ERÖFFNEN 30 · HALTEN 21 · NACHKAUFEN 4 · REDUZIEREN 4
```

> **67 ERÖFFNEN an einem Tag.** Das ist die Zahl, über die zu reden ist — und
> sie steht jetzt fest, samt Datum und Herkunft.

**Datenlage, unter Vorbehalt lesen:** 61 von 63 Reihen endeten am **14.08.**
Jede Aussage über Signalqualität aus diesem Fenster steht darauf, dass die
Charts bis zu zwei Tage alt waren.

**Was die Basislinie festhält:** Betrieb (Laufzeit, Ausfallfenster),
Jobausführungen, Signale und Aktionen je Tag, Abdeckung der Gegenprüfung,
Alter der Kursreihen, Durchlässigkeit je Stufe, Systemgüte,
Richtungsverteilung, LLM-Aufrufe, Gate-Vetos.

**Was sie NICHT tut: bewerten.** Sie schreibt Zahlen mit Datum und Herkunft.

### 45.3 Warum es diese Basislinie geben muss

In vier Tagen hat die Kette den Prompt-Stand **zweimal** gewechselt, den
Richtungsabgleich stillgelegt, die Konsistenzprüfung entfernt und Rolle G
überhaupt erst zum Laufen gebracht. **Wer danach misst, misst gegen nichts** —
jede Zahl sähe anders aus, und niemand könnte sagen, ob besser oder nur anders.

**Drei Vergleiche, die erst dadurch möglich werden:**

| Frage | Vorher-Wert |
|---|---|
| Sinkt die Signalzahl, oder steigt nur der HALTEN-Anteil? | 67 ERÖFFNEN gegen 62 HALTEN am 15.08. |
| Erreicht Rolle G mehr Einstiege als die alte Prüfung? | Konsistenz 25 von 34 (74 %), Rolle G **0** |
| Läuft die Kette überhaupt öfter? | 51 % Ausfallzeit, `refresh_ohlc` 1× in 48 h |

---

## Kapitel 46 — Sind die Signale der letzten Tage brauchbar? (16.08.2026)

**Nutzerfrage:** *„Kann man sagen, alle Signale und Bewertungen der letzten
Tage sind unvollständig bzw. fehlerhaft — d. h. auch eine Gegenüberstellung
Kauf/Verkauf/Halten bzw. Hebel Einstiege/Ausstiege ist unbrauchbar, oder kann
man daraus etwas lesen?"*

**Antwort: teils, und die Trennlinie lässt sich exakt ziehen.** Die Signale
tragen ihren `prompt_stand` — die Zuordnung ist keine Schätzung.

### 46.1 Die Aufteilung, gemessen

| Prompt-Stand | 14.08. | 15.08. | 16.08. | Σ | Einstiege |
|---|---:|---:|---:|---:|---|
| **2026-08-12** | 46 | 154 | 26 | **226** | 117 (52 %) |
| **2026-08-16** (Phase I) | – | – | 29 | **29** | 20 (69 %) |
| **ohne Stand** | – | 26 | 4 | **30** | 0 |

Die 30 ohne Stand sind **ausschliesslich** Verkaufsseite (28 REDUZIEREN,
2 VERKAUFEN) — der Ausstiegspfad setzt das Feld nicht.

### 46.2 Welcher Defekt wirkte auf welche Signale

| Defekt | betroffen | Wirkung |
|---|---|---|
| **60-Tage-Doppelung** | **alle 285** | eine Zahl zweimal im Prompt — Gewichtung verzerrt, aber **gleichmässig** |
| Klassen-Einstufung fehlt bei `themen_etf`/`hedge` | diese Gruppen, seit 12.08. | Lagebild-Einstufung fehlte |
| Sektorbezug greift nie | Themen-ETF | fehlender Block |
| **fehlende Kerze** | **nur 16.08., 59 Signale** | am 15.08. war die 14.08.-Kerze die **normale Vortageskerze** |
| **Rolle G tot** | alle | es gab **keine** zweite Stimme — die Empfehlung selbst ist unberührt |
| Konsistenzprüfung | 93 Einstiege | eine Zeile in der Mail; sie **kippt nichts** (Nutzervorgabe 29.07.) |
| **51 % Ausfallzeit** | alle | verzerrt, **welche** Assets wann drankamen |

> ⚠️ **Korrektur an meiner eigenen früheren Aussage.** Ich hatte geschrieben,
> die Kette habe „auf zwei Tage alten Charts" geurteilt. Das gilt **nur für den
> 16.08.** — am 15.08. war die jüngste Kerze vom 14.08., also die normale
> Vortageskerze. Betroffen sind **59 von 285**, nicht alle.

### 46.3 Was sich daraus NICHT lesen lässt

**Kein Erfolgsvergleich.** Von 285 Signalen haben **8** einen aufgelösten
Ausgang:

```
nicht_anwendbar 214 · ohne Status 58 · take_profit 6 · offen 5 · stop_loss 2
```

> **Eine Gegenüberstellung Kauf/Verkauf/Halten kann derzeit gar keine
> Erfolgsmessung sein** — es gibt fast nichts Aufgelöstes. Wer aus 6 Treffern
> und 2 Stopps etwas ableitet, misst Rauschen.

**Kein Vergleich über Stände hinweg.** 226 gegen 29 Signale, und die 29 stehen
zusätzlich auf der fehlenden Kerze. Der Unterschied 52 % → 69 % Einstiege sieht
nach Phase I aus, ist aber bei n=29 an einem Tag mit fehlender Kerze **nicht
belastbar**.

**Keine Rate je Asset.** Bei 51 % Ausfallzeit ist „x % der Assets" eine Aussage
über die Laufzeit, nicht über den Markt.

### 46.4 Was sich sehr wohl lesen lässt

**Die Verteilung innerhalb eines Stands** — 226 Signale, ein Prompt, ein
Modell, dieselbe Doppelung für alle:

```
HALTEN 98 · ERÖFFNEN 81 · KAUFEN 22 · NACHKAUFEN 14 · REDUZIEREN 9 · VERKAUFEN 2
```

**52 % Einstiege.** Das ist keine Datenfrage, sondern das Verhalten des Modells
unter bekannten Bedingungen. Die Doppelung verzerrt es, aber **für alle gleich**
— ein systematischer Versatz, kein Rauschen.

**Und die Verkaufsseite ist auffällig dünn:** 11 von 226 sind VERKAUFEN oder
REDUZIEREN (5 %), gegen 117 Einstiege. Das deckt sich mit O-29.

### 46.5 Der Anlassfilter hat geantwortet — und deutlich

Die Messung aus O-36 lief im Betrieb mit. **2.665 Beobachtungen**, 15.08. 16:30
bis 16.08. 07:29:

| Instrument | Urteile | wörtliche Wiederholung |
|---|---:|---:|
| spot | 1.759 | **80 %** |
| hebel | 864 | **81 %** |
| absicherung | 42 | **93 %** |
| **gesamt** | **2.665** | **81 %** |

**Vier von fünf Modellaufrufen stellen dieselbe Frage noch einmal.**
Median-Abstand zur vorigen Frage: **0,2 Stunden** — das ist der Takt, nicht der
Markt. Einzelne Symbole: 66 von 70 Urteilen identisch.

> **Eine Vermutung ist damit widerlegt — meine eigene.** Ich hatte erwartet,
> das Lagebild mache die Fragen künstlich „neu", weil es Modellprosa ist und
> alle drei Stunden wechselt. Der Unterschied zwischen *mit* und *ohne*
> Lagebild beträgt **2 Prozentpunkte** (79 % gegen 81 %). Es macht fast nichts
> aus.

**Was eine Frage wirklich neu macht:**

| Block | Anteil |
|---|---:|
| **marken** | **15 %** |
| bestand | 4 % |
| finanzierung · hebelgeometrie · lücken · referenz | je 3 % |
| bewegung · struktur · volumen | je 2 % |

**Die Marken allein tragen die Hälfte aller echten Änderungen.** Sie sind
kursnah und bewegen sich, sobald ein Tick über eine Clustergrenze läuft.

### 46.6 Was das für die Signalzahl bedeutet

**Die 67 ERÖFFNEN an einem Tag entstehen nicht, weil das Modell 67-mal etwas
Neues sieht** — sondern weil es 2.665-mal gefragt wird und in 81 % der Fälle
dieselbe Frage bekommt.

**Damit steht die Bremse auf einer Messung statt auf einer Schätzung.** Und sie
ist keine Einschränkung im Sinne von *„weniger, damit es weniger ist"*: sie
entfernt Wiederholungen, keine Urteile.

**Offen bleibt die Nebenwirkung.** Greift der Filter, sinkt die Zahl der
Aufrufe um rund 80 % — und damit auch die Zahl der Gelegenheiten, bei denen ein
Asset zufällig im richtigen Moment gefragt wird. Ob das schadet, sagt keine
dieser Zahlen.

### 46.7 Zwei eigene Fehler dieser Runde

> ⚠️ **Das Datum.** Ich habe die gesamte Dokumentation dieser Sitzung auf den
> **17.08.** datiert — es ist der **16.08.**, ein Sonntag. 42 Stellen in 16
> Dateien, korrigiert. Der Fehler zerstört genau die Zuordnung, um die es in
> diesem Kapitel geht.

> ⚠️ **Der Prompt-Stand wäre kollidiert.** Die Datumskorrektur hätte den
> Klasse-1-Stand auf `2026-08-16` gesetzt — denselben Schlüssel, den Phase I in
> der Produktion bereits trägt (29 Signale). Genau die Signale, deren
> Unterschied gemessen werden soll, wären nicht mehr trennbar gewesen. Jetzt
> **`2026-08-16b`**, nach der Buchstabenkonvention der Datei.

---

## Kapitel 47 — Schadet der Anlassfilter? Ja. Und er wird trotzdem nicht gebaut (16.08.2026)

**Nutzerfrage:** *„mach die Messung, ob der Filter schadet"* — und die
Nachfrage, die das Vorhaben beendet hat: *„bringt uns das weiter? Die
LLM-Aufrufe werden trotzdem durchgeführt … was ist das Ziel — das Rauschen zu
messen?"*

### 47.1 Zwei eigene Zahlen, die ich korrigieren muss

> ⚠️ **„Vier von fünf Modellaufrufen stellen dieselbe Frage noch einmal" war
> falsch.** Die Anlassstufe sitzt **vor** dem Cooldown — sie sieht jedes Symbol,
> auch die, die der Cooldown unmittelbar danach entfernt.
>
> | | |
> |---|---|
> | Anlass-Beobachtungen | **2.665** |
> | davon mit zugeordnetem Signal | **258 (9,7 %)** |
>
> Die 81 % sind **81 % der Beobachtungen, nicht der Modellaufrufe.** Der
> Cooldown leistet die Arbeit bereits.

> ⚠️ **Die 42,3 % Antwortwechsel stehen auf n=26.** 2.127 von 2.153 Paaren sind
> nicht zuordenbar, weil gar kein zweiter Modellaufruf stattfand. Die Richtung
> ist belastbar, die Prozentzahl nicht.

### 47.2 Der Filter schadet — und zwar nicht geringfügig

| | |
|---|---|
| Symbole mit **erstmaligem** Einstieg | 17 |
| Symbole mit **Wiederholungs**-Einstieg | 21 |
| davon **nur** über eine Wiederholung | **10** |

```
3QSS 1x · BEAMX 2x · CAT 5x · CEBS 1x · PLTR 1x
PLUME 1x · SOL 4x · SUI 5x · TURBO 4x · VIRTUAL 2x
```

**Zehn von 21 Symbolen hätten ohne die Wiederholung nie einen Einstieg
bekommen** — darunter SOL, SUI und TURBO. Von 121 zuordenbaren Einstiegen
stammen **82 aus Wiederholungen**, nur 39 aus Erstfragen.

> **Die Wiederholung ist nicht „dasselbe Signal noch einmal".** Es ist
> *dieselbe Frage mit anderer Antwort* — die erste Frage erzeugte kein Signal,
> die zweite schon. Genau die Varianz aus 47.1.

**Der Einwand des Nutzers trifft also, und stärker als er ihn formuliert hat:**
es ist nicht geringfügig, es sind zwei Drittel der Einstiege.

### 47.3 Und trotzdem wird der Filter nicht gebaut

**Die Nachfrage des Nutzers beendet das Vorhaben, und sie hat recht.**

Ein Filter, der Wiederholungen unterdrückt, würde die Signalzahl senken.
**Er würde die Qualität nicht ändern** — und das ist keine Vermutung, sondern
der Grundbefund dieses Projekts:

> **Kein Verfahren schlägt die Basisrate** (8.441 Fälle, zwei Verfahren, beide
> Merkmalsfamilien). Ein Barrierensystem auf einem driftfreien Pfad hat brutto
> den Erwartungswert null.

Daraus folgt hart: ein Einstieg, der aus einem Zufall entstand, ist **genauso
viel wert** wie einer aus der Erstfrage — nämlich brutto null und nach Kosten
negativ. **Wer ihn entfernt, entfernt nichts Wertvolles. Wer ihn behält, behält
nichts Wertvolles.**

> **„Ist das Ziel, das Rauschen zu messen?" — Nein.** Und mein Vorschlag, den
> Filter auf den Mailversand zu beschränken, war halbherzig: er hätte das
> Symptom versteckt und die Aufrufe weiterlaufen lassen. Der Nutzer hat den
> Grund benannt, bevor ich ihn selbst gesehen habe.

### 47.4 Was daraus wirklich folgt

**Die Signalzahl ist nicht das Problem — sie ist sein Symptom.** Sie ist hoch,
weil wir gute von schlechten Einstiegen nicht unterscheiden können. Jede
Bremse, die nicht an dieser Unterscheidung ansetzt, verschiebt eine Zahl.

**Drei Dinge bleiben, in dieser Reihenfolge:**

| | | warum |
|---|---|---|
| **1** | **Bündelung des Versands** — eine Mail je Lauf statt eine je Signal | löst genau das, was stört (das Postfach), ohne die Kette, die Urteile oder die Messung anzufassen. **Keine Bewertung, nur Zustellung** |
| **2** | **Neustarts reduzieren** | elf in 48 Stunden, jeder löst einen Sofortlauf aus. Das ist die konkreteste Ursache für Signalspitzen — und sie liegt im Betrieb, nicht im Modell |
| **3** | **S2 — Drift statt Timing** | von den drei bekannten Wegen (Drift · Nachrichten · Kosten) der einzige, der das Vorzeichen drehen kann, und der einzige, der **nie gemessen** wurde |

**Was NICHT weiterverfolgt wird:** der Anlassfilter als Sperre oder als
Mailfilter. Die Messung bleibt laufen — sie kostet nichts und beantwortet
später, ob sich das Bild ändert.

### 47.5 Der Wert dieser Runde

Es wurde nichts gebaut, und das ist das Ergebnis. **Ein Vorhaben, das seit dem
15.08. im Plan stand (O-36), ist an seiner eigenen Messung gescheitert** — und
zwar an der richtigen Stelle: bevor es gebaut wurde.

**Werkzeuge, die bleiben:** `messe_anlass.py` (wie oft wäre gesperrt worden),
`messe_filterschaden.py` (was hätte es gekostet).

---

## Kapitel 48 — Die Anlass-Sperre, gebaut (16.08.2026)

**Kapitel 47 kam zum Schluss, sie nicht zu bauen. Der Nutzer hat den
Fehlschluss darin benannt, und er hatte recht.**

> Ich hatte gemessen, der Filter „koste" 82 von 121 Einstiegen — und im selben
> Absatz geschrieben, dass diese Einstiege nichts wert sind. **„Kosten" setzt
> einen Wert voraus.** Aus „Erwartungswert null" folgt nicht „also egal",
> sondern: dann entscheidet alles andere.

**Das tragende Argument ist ein Korrektheitsargument:**

> **Eine Empfehlung, die auf identischen Daten beruht wie eine vorherige
> NICHT-Empfehlung, ist keine Empfehlung — sie ist die Streuung des Modells.**

Es hängt nicht davon ab, ob das System je Geld verdient. Und der Nutzer hat den
zweiten Halbsatz gleich mitgeliefert: *„kein Rauschen messen"* — es geht nicht
darum, die Streuung zu vermessen, sondern sie nicht zu versenden.

### 48.1 Was vor dem Bauen gemessen war

| | |
|---|---|
| Wiederholungen bei **intakter** Datenlage (15.08.) | **74 %** |
| mit stehenden Kursen (16.08.) | 83 % |
| Einstiege auf einem Faktensatz, den es schon gab | **82 von 121** |
| Wiederholungen, die die **Aktion kippten** | **11 von 26** |

Der Kursstillstand hebt die Quote um neun Punkte — **er erzeugt sie nicht.**

### 48.2 Wo die Sperre sitzt

**Vor dem Modellaufruf**, in einer **eigenen Gate-Stufe**.

```
auftrag → fakten → lagebild → ANLASS → wiederholung → urteil → ...
```

**Eigene Stufe, aus demselben Grund wie der Cooldown am 14.08.:** sie kostet
keinen Modellaufruf. Wer sie mit `wiederholung` zusammenlegt, kann hinterher
nicht mehr sagen, ob eine **Zeitregel** oder ein **identischer Faktensatz**
gebremst hat.

**Vor dem Aufruf, nicht danach:** wer die Antwort erst holt und dann wegwirft,
hat das Kontingent ausgegeben und das Rauschen bereits erzeugt — er versteckt
es nur. Genau das war mein verworfener Mailvorschlag.

**Die Beobachtung wird trotzdem geschrieben**, auch wenn gesperrt wird. Sonst
verschwände mit der Sperre die Zahl, an der man sie später beurteilen könnte —
und man sähe nur noch, dass weniger kommt, nicht warum.

### 48.3 Feinjustierung ohne Codeänderung

```yaml
anlass:
  aktiv: true
  abdruck: asset          # ohne Lagebild - macht gemessen 2 Punkte aus
  hoechstalter_stunden: 24.0
  ignoriere_bloecke: []   # z.B. [marken]
  mindest_bloecke: 1
```

**Beide Regler können nur MEHR sperren, nie weniger** — ein identischer Abdruck
ist immer eine Wiederholung.

> **`ignoriere_bloecke: [marken]` ist der vorbereitete Fall.** Die Marken tragen
> **15 %** aller echten Änderungen, sind kursnah und springen, sobald ein Tick
> über eine Clustergrenze läuft. Ob das eine neue Lage ist oder Rauschen, ist
> **offen** — deshalb ein Regler und keine Setzung.

**Die Vorgabe im Code ist AUS.** Eingeschaltet wird in `config.yaml` — dieselbe
Regel wie bei `rollen_kette.aktiv_fuer`: ein Modul, das beim blossen Einspielen
die Produktion umstellt, nimmt dem Nutzer die Entscheidung ab.

### 48.4 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **869, alle bestanden** (10 neue) |
| freie Namen | 0 |

**Die Prüfungen decken auch die Gegenrichtung ab:** eine echte Änderung geht
durch, eine erste Frage wird nie gesperrt, und ein defektes Urteil sperrt
**nicht** — eine Sperre, die bei einer Lücke zuschlägt, entfernt Signale aus
einem Grund, den niemand sieht.

### 48.5 Der Ende-zu-Ende-Beweis

`simuliere_kette.py` fährt jede Gruppe jetzt **zweimal**: einmal frisch, einmal
mit identischen Kursreihen und aktiver Sperre.

| Gruppe | erster Lauf | zweiter Lauf, mit Sperre |
|---|---|---|
| aktien/spot | 2 Signale, 3 Aufrufe | **0 / 0** |
| krypto/spot | 2 Signale, 2 Aufrufe | **0 / 0** |
| krypto/hebel | 2 Signale, 3 Aufrufe | **0 / 0** |
| themen_etf/spot | 2 Signale, 3 Aufrufe | **0 / 0** |

**Null Modellaufrufe im Wiederholungslauf** — die Sperre greift vor dem Aufruf.
Und der erste Lauf liefert weiterhin Signale, sonst prüfte der Test gegen
nichts.

Die Attrappe wird für den zweiten Lauf **neu gebaut**: sonst zählte sie im
Aktionsvokabular weiter, und der Test würde die Attrappe messen statt die
Sperre.

### 48.6 Was der LLM-Umbau daran ändern wird

**Nutzerhinweis, und er trifft:** *„nach dieser Änderung werden wir die LLMs
durchführen, und diese kann einen Einfluss auf diesen Punkt haben — u. U. nur im
Positiven, da wir mehr unabhängige Parameter bekommen."*

**Richtig, und die Richtung ist vorhersagbar:** je mehr Blöcke der Faktensatz
trägt, desto wahrscheinlicher bewegt sich einer — die Sperre greift **seltener**.
Das ist kein Fehler, sondern der gewünschte Zustand: sie soll nur dort greifen,
wo wirklich nichts Neues vorliegt.

**Aber es hat eine Kehrseite, und dafür sind die Regler da.** Ein Block, der
sich häufig aus sich selbst bewegt — wie die Marken —, macht jede Frage „neu",
ohne dass die Lage eine andere wäre. Kommen weitere solche Blöcke dazu, sinkt
die Wirkung der Sperre, ohne dass sich etwas verbessert hätte.

**Deshalb gehört nach jedem Umbauschritt `messe_anlass.py` erneut gelaufen** —
die Blockaufschlüsselung sagt, welcher neue Parameter tickt und welcher trägt.

### 48.7 Was offen bleibt

**Die Sperre ist grob, nicht scharf.** Sie entfernt das Offensichtliche —
identische Fakten —, nicht das Feine. Ein Signal hängt danach daran, dass sich
*irgendein* Block bewegt hat, und in 15 % der Fälle sind das die kursnahen
Marken.

**Und sie löst Problem 2 nicht:** gute von schlechten Einstiegen zu
unterscheiden. Sie war nie dafür gedacht — dass ich beides vermischt habe, war
der Fehler in Kapitel 47.

---

## Kapitel 49 — Die Restpunkte aus der NB-Analyse (16.08.2026)

**Nutzerfrage vor Punkt 2:** *„haben wir noch offene Punkte und Fixes aus der
NB-Analyse?"* — **Ja, drei kleine. Alle drei betreffen die Diagnose selbst.**

### 49.1 Der Export trug die Anlassmessung nicht

**Und das war seit heute Mittag dringend:** die Sperre ist scharf, der Export
kannte den Block nicht. Um zu sehen, ob sie greift, hätte jedes Mal das
DB-Backup ausgepackt werden müssen.

**Exportiert wird die Auswertung, nicht die Rohzeilen** — über 2.600 in
15 Stunden, und die JSON ist ohnehin 155 MB. Je Instrument, je Block,
Median-Abstand, dazu der Satz, der die Fehldeutung verhindert:

> *„Die Stufe sitzt VOR dem Cooldown — sie sieht jedes Symbol, auch die, die
> der Cooldown danach entfernt. Die Quote ist deshalb NICHT der Anteil
> vermeidbarer Modellaufrufe."*

Genau diesen Satz hätte ich heute früh selbst gebraucht — ich hatte die 81 %
als Modellaufrufe gelesen.

### 49.2 Zwei Fehlalarme, die echte Funde überdecken

> ⚠️ **13 „Auffälligkeiten", die keine sind.** Der Export prüft
> `gate_passed = 0` **und** Aktion ≠ HALTEN → Widerspruch. Das ist die
> Semantik der **alten** Kette.
>
> In der Rollen-Kette bedeutet `gate_passed = 0` etwas anderes:
> `_schreibe_nein()` bucht damit die **Nein-Messung** — eine Zeile, die
> festhält, was das Modell gesagt *hätte*, obwohl keine Empfehlung herauskam.
> Aktion und Flag stehen dort **absichtlich** nebeneinander.
>
> Betroffen: 11 Verkaufsseite vom 14.08. und zweimal TURBO ERÖFFNEN. **Keiner
> davon ist ein Defekt.**

> ⚠️ **„11970 Tracebacks im Log-Fenster"** — ohne Zeitbezug. 11.953 davon waren
> **ein** Fehler aus 36 Minuten am 14.08., behoben durch einen Pull.
>
> Die Meldung nennt jetzt **Zeitraum und häufigste Ursache**:
> ```
> 11970 Tracebacks, alle zwischen 2026-08-14 09:35 und 2026-08-15 22:50
>   - haeufigste Ursache 11953x TypeError: RemoteStatus.__init__() ...
> ```

**Warum das zählt:** eine große Zahl ohne Einordnung liest sich wie ein akuter
Ausfall und **überdeckt die echten Funde daneben**. Von vier gemeldeten
Auffälligkeiten waren zwei Fehlalarme — und der Kursstillstand, der wirklich
zwei Tage lang wirkte, stand in **keiner**.

### 49.3 Was aus der NB-Analyse offen BLEIBT

| | Punkt | Art |
|---|---|---|
| **A2b** | Ausstiegs-Job lief 0× — **kein Defekt**, die App lief zur Cron-Zeit nicht | **Betrieb** |
| **Laufzeit** | **51 % Ausfallzeit**, elf Neustarts in 48 h. Erklärt A2b, den Kursstillstand und `refresh_ohlc` 1× | **Betrieb** |
| Nachhollogik | Jobs mit langem Takt bräuchten einen Zeitstempel des letzten Laufs — **berührt das Schema**, deshalb eine Entscheidung | offen |
| Marktscan | läuft, findet im Bärenregime 0 von 34. **Kein Defekt** — die Frage ist, ob Sie das so wollen | Entscheidung |
| **D-1** | `.docx`-Pendants stehen seit 02.08. still | Doku |
| **D-2** | `Regler_Signal_Pipeline_Abhaengigkeiten.md` kennt die Rollen-Kette nicht | Doku |
| prompt_stand | 30 Signale ohne — der Verkaufspfad setzt das Feld nicht | Messlücke |

**Keiner dieser Punkte blockiert Punkt 2.** Die beiden Betriebspunkte sind die
gewichtigsten, und sie lassen sich nicht im Code lösen: ein 24-Stunden-Job kann
nicht laufen, wenn die längste ununterbrochene Laufzeit darunter liegt.

### 49.4 Was heute behoben wurde

| | |
|---|---|
| Kursstillstand | eigene Frischeschwelle für Krypto (24/7-Markt) |
| **Rolle G lief nie** | Symbol kommt vom Aufrufer |
| Konsistenzprüfung | entfernt — vom Nutzer am 16.08. abgelehnt |
| Andrangdeckel | lag auf der entfernten Prüfung, jetzt auf Rolle G |
| Klasse-1-Doppelung | `struktur` + `bewegung` → `verlauf` |
| **Anlass-Sperre** | gebaut, Ende zu Ende bewiesen |
| Export | Anlassblock ergänzt, zwei Fehlalarme entschärft |

---

## Kapitel 50 — Die Betriebspunkte abgearbeitet (16.08.2026)

**Nutzereinwand:** *„warum können wir die offenen Punkte nicht noch vor Punkt 2
erledigen? sonst vergessen wir wieder."*

**Er hat recht, und die Projektgeschichte gibt ihm recht** — diese Sitzung hat
mehrfach Dinge gefunden, die „gebaut, aber nie verdrahtet" oder „behoben, aber
nicht ausgerollt" waren. „Blockiert nicht" heisst hier erfahrungsgemäss „wird
vergessen".

### 50.1 Der Nachholer — A2b an der Wurzel

**Der Befund war:** fünf tägliche Cron-Jobs zwischen 06:00 und 07:15 liefen in
48 Stunden zusammen **viermal**, der Ausstiegs-Job **gar nicht**.

```
ausstiegs_job       0x   cron 07:15
backward_tracking   1x   cron 06:00
portfolio_wert      1x   cron 06:30
refresh_ohlc        1x   24-h-Takt
```

**Kein Defekt in den Jobs.** Die App war 24,6 von 48 Stunden aus, und **ein
Cron trifft nur, wenn sie zur Uhrzeit läuft.** APScheduler holt nichts nach —
der Jobstore liegt im Speicher und ist nach einem Neustart leer.

**Gebaut: ein Zeitstempel je Job.**

```
db.merke_joblauf(conn, "ausstiegs_empfehlungen")
db.letzter_joblauf(conn, "ausstiegs_empfehlungen")
```

Beim Aufbau des Schedulers fragt `_nachholen(job_id, versatz)`: **lief er heute
schon?** Wenn nein → `next_run_time = jetzt + Versatz`.

> **Warum nicht einfach „beim Start immer laufen".** Genau davor warnt der
> Kommentar an `refresh_ohlc` seit dem 12.07.: ein teurer Job wäre dann bei
> **jedem** Neustart fällig, auch nach einem Absturz vor fünf Minuten. Bei elf
> Neustarts am Tag wären das elf Läufe — und beim Ausstiegs-Job elf Mails.

**Der Versatz erhält die Reihenfolge**, und die ist nicht kosmetisch — der
Kommentar am Ausstiegs-Job sagt es selbst: die Regel rechnet auf Werten, die
das Backward-Tracking vorher fortschreibt.

| Job | Versatz |
|---|---|
| `backward_tracking` | +30 s |
| `portfolio_wert` | +120 s |
| `ausstiegs_empfehlungen` | +240 s |

**Vermerkt wird bei JEDEM Ausgang**, auch wenn der Job nichts zu melden fand.
Sonst holte der Nachholer bei jedem Neustart erneut nach.

**Im Zweifel wird NICHT nachgeholt:** fällt die Abfrage aus, läuft der Job wie
bisher zur Uhrzeit. Ein Nachholer, der bei einer Lücke feuert, macht aus einem
Lesefehler einen Modellaufruf.

### 50.2 Funktional getestet, nicht nur am Quelltext

| Fall | Ergebnis |
|---|---|
| Job nie gelaufen | **NACHHOLEN** |
| Job läuft jetzt | ruhig |
| **Neustart am selben Tag** | **ruhig** — kein Doppelfeuer |
| Lauf war gestern | **NACHHOLEN** |

Der dritte Fall ist der wichtige: er ist genau das Szenario mit elf Neustarts.

### 50.3 D-2 erledigt

`Regler_Signal_Pipeline_Abhaengigkeiten.md` kennt die Rollen-Kette jetzt: die
**sechs Dateien, die einen Prompt verändern** (samt der Pflicht, den
`PROMPT_STAND` mitzuziehen), die Regler in `config.yaml` — und ausdrücklich das,
was die Kette **nicht** steuert:

> **Die Frische der Kursreihen** und **die Laufzeit der App.** Beides hat am
> 16.08. Signale erzeugt bzw. verhindert, ohne dass die Kette es merkte.

Der Standvermerk bleibt stehen — er erklärt den Zustand, in dem die Regel
*„vor jeder Prompt-Änderung prüfen"* ins Leere lief.

### 50.4 Was jetzt noch offen ist

| | | warum nicht jetzt |
|---|---|---|
| **51 % Ausfallzeit** | die App läuft nicht durch | **Betrieb, nicht Code.** Der Nachholer mildert die Folge, nicht die Ursache |
| **D-1** `.docx` | seit 02.08. still | kein Werkzeug zum Erzeugen vorhanden |
| **Marktscan-Schwelle** | 0 von 34 im Bärenregime | **Ihre Entscheidung**, kein Defekt |
| **prompt_stand** | 30 Signale ohne | der Verkaufspfad setzt das Feld nicht — Messlücke, kein Fehlverhalten |

> ⚠️ **Ein eigener Fehler beim Prüfen, zum dritten Mal derselbe Typ.** Mein
> Reihenfolgetest verglich, **wo die Aufrufe im Quelltext stehen** — dort steht
> der Ausstiegs-Job zuerst. Die Reihenfolge steckt aber in den
> **Versatzsekunden**. Der Test hing am falschen Gegenstand, wie schon bei der
> streng steigenden Testreihe und beim Blocknamen mit Leerzeichen.

---

## Kapitel 51 — Die letzten drei Punkte (16.08.2026)

**Nutzervorgabe:** *„vorher noch die offenen Punkte hier."*

### 51.1 D-1: das Werkzeug gab es seit dem 02.08.

Ich hatte geschrieben *„kein Werkzeug zum Erzeugen vorhanden"*. **Falsch, und
zum dritten Mal derselbe Fehler an einem Tag** — eine Behauptung statt
nachzusehen. Es gibt `build_docx.py` seit dem 02.08., und `python-docx` ist
installiert.

```
python build_docx.py --pruefen   ->  5 von 6 veraltet
python build_docx.py             ->  alle neu erzeugt
```

Fünf Lesekopien waren zwei Wochen zurück, jetzt alle **AKTUELL**. Die
`.md`-Dateien bleiben die Quelle der Wahrheit; die `.docx` sind reproduzierbar.

### 51.2 Die Messlücke geschlossen

`_sende_ausstieg()` übergab `prompt_stand=None` — deshalb trugen **30 von 285**
Signalen keinen Stand, und es waren **ausschliesslich Verkaufszeilen** (28
REDUZIEREN, 2 VERKAUFEN).

> **Warum das zählt:** die Verkaufsseite fiel damit aus jedem
> Vorher-Nachher-Vergleich heraus — ausgerechnet der Teil, über den am
> wenigsten bekannt ist. O-29 hat gemessen, dass **kein** Merkmal Verkaufen von
> Halten trennt.

Es ist **derselbe** Stand wie beim Einstieg: `befund` ist die Antwort von Rolle
BC und entsteht aus demselben Prompt.

### 51.3 Marktscan — was ich falsch dargestellt hatte

> ⚠️ **Zwei meiner Aussagen waren falsch.** Ich hatte geschrieben, keiner der
> 34 Kandidaten erreiche auch nur 50, und der letzte Kaufkandidat sei aus dem
> Juli. Beides stützte sich auf die **Desktop-Dev-Datenbank** (Daten bis 10.07.)
> und auf **eine einzelne Logzeile**.

**An den NB-Daten:**

| | |
|---|---|
| bewertet, letzte 30 Tage | 164 |
| davon **Score ≥ 70** | **45 (27 %)** |
| Kaufkandidaten im August | **3** — M (83,8), COTI (71,1), **H (74,8) am 14.08.** |
| Mail dazu | **verschickt**, 14.08. 16:02 |

**Der Marktscan funktioniert vollständig, inklusive Versand.** „Ewig keine"
heisst: **selten** — drei im August.

**Und der eigentliche Befund liegt woanders:**

> **24 von 64 Kandidaten mit Score ≥ 70 wurden herabgestuft** — 37 %. Grund:
> nicht bei Bitpanda gelistet, oder Small-Cap-Budget im Regime *bär*
> ausgeschöpft (4 % statt 12 % im Bullenmarkt).
>
> **Der Nutzer erfährt davon nie.** Sie verschwinden lautlos nach
> `watchlist_wuerdig`.

**Was zur Entscheidung steht — und was NICHT:**

| Option | Wirkung |
|---|---|
| **A** alles lassen | ~3 Mails/Monat, nur Handelbares |
| **B** Herabgestufte **in derselben Mail** nennen | keine zusätzliche Mail, schliesst die Informationslücke |
| **C** Schwelle 70 → 60 | **120 statt 45** Kandidaten → ~4 Mails **pro Tag** |

**Die Schwelle ist nicht das Problem** — sie liefert drei Mails im Monat. Die
Lücke ist die stille Herabstufung.

### 51.4 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **881, alle bestanden** |
| freie Namen | 0 |
| Ende-zu-Ende-Simulation | 0 Fehler, 0 Lücken |
| `pruefe_phase1.py` | bestanden |
| `.docx` | 6 von 6 aktuell |

---

## Kapitel 52 — Punkt 2: alle sechs Körbe laufen durch die Simulation (16.08.2026)

**Der Anlass:** `simuliere_kette.py` übersprang **Rohstoffe** und
**Absicherung** — im Entwicklungsbestand fehlen ihre Kursreihen — und meldete
trotzdem „0 Fehler". Zwei von sechs Körben liefen scharf und waren in keinem
Testlauf. **Dieselbe Konstellation, die Rolle G drei Tage lang „fertig"
aussehen liess.**

**Gelöst mit den Reihen aus dem NB-Backup** (`DB_Backups/` neben dem Export,
entsteht bei jedem NB-Export automatisch).

```
python simuliere_kette.py --db <entpacktes NB-Backup>
6 Gruppen durchlaufen, 12 Signale, 14 Mails, 0 Fehler, 0 Luecken
```

### 52.1 Der erste Lauf prüfte einen Produktionsstand, nicht die Kette

| Gruppe | Modellaufrufe |
|---|---|
| hedge/absicherung | **0** |
| themen_etf/spot | **0** |
| aktien/spot | 1 |

**Der echte Cooldown sperrte.** Im NB-Backup stehen Produktionssignale von
heute — jedes Symbol war bis zum 17.08. gesperrt:

```
nicht kuerzlich schon gefragt   0   (2 verloren)
      1x Cooldown bis 2026-08-17T04:43
      1x Cooldown bis 2026-08-17T06:15
```

**Die Simulation datiert die Signale in der KOPIE jetzt um 30 Tage zurück** —
zurückdatiert, nicht gelöscht: die Zeilen werden für Bestand, Trefferbilanz und
Ausstiegsführung gebraucht. Danach laufen alle sechs Gruppen vollständig.

> **Ohne diesen Schritt hätte der Test bestätigt, dass der Cooldown
> funktioniert — und nichts über die Kette gesagt.**

### 52.2 Ein Trichterloch, das dabei auffiel

```
Faktensatz hat sich geaendert    0   (0 verloren)
```

Zwei Symbole hatten die Anlass-Stufe passiert, und sie stand mit **null zu
null** da. Meine Änderung von heute Mittag buchte beide Stufen gemeinsam am
Ende — griff der Cooldown, kehrte die Funktion vorher zurück, und die
Anlass-Stufe wurde nie gebucht.

**Genau das, was die eigene Stufe verhindern sollte:** eine Zahl, deren Summe
nicht mehr aufgeht. Jetzt wird `anlass` **vor** dem Cooldown gebucht.

> ⚠️ **Und ein Kommentar von mir war falsch.** Ich hatte geschrieben, ein
> doppelter Aufruf zähle nicht doppelt, weil `Durchlauf` Mengen führe.
> Nachgesehen: `bestanden_je_stufe[stufe] += 1` ist ein **Zähler**. Der Guard
> für den Trockenlauf ist damit zwingend, nicht kosmetisch.

### 52.3 Was in den beiden neuen Körben ankommt

**Absicherung (DBPK):**

```
--- 1. DIE ABSICHERUNG ---
Auf Sicht der letzten 17 Handelstage zeigt die Marktstruktur tiefere Hochs ...
Kursentwicklung im selben Rahmen: 5 Tage -0.7 %, 20 Tage -8.6 %, 60 Tage -6.1 %.
Es liess sich weniger als eine Marke oberhalb UND eine unterhalb bestimmen ...
  Abzusicherndes Exposure: 8.898 EUR (alles im Depot ausser Absicherungen und Cash).
  Davon bereits abgesichert: 1.341 EUR - das sind 15 %.
  Dieses Instrument hebelt 2-fach auf den S&P 500; 1 EUR darin deckt 2 EUR Exposure.
  Laufende Gebuehr etwa 0,8 % pro Jahr - eine Absicherung kostet auch dann, wenn nichts passiert.
```

**Rohstoffe (OD7H):**

```
--- 1. DER WERT ---
Kursentwicklung im selben Rahmen: 5 Tage +1.1 %, 20 Tage +9.4 %, 60 Tage -2.6 %.
Fuer dieses Instrument wird KEIN Umsatz ausgewiesen. Das ist eine fehlende
Angabe, kein unauffaelliger Umsatz ...
```

**Beide Lücken-Sätze aus Phase I stehen zum ersten Mal in einer echten Mail** —
die fehlende Marke bei der Absicherung, der fehlende Umsatz beim Zertifikat.
Bis heute war nur bewiesen, dass die Funktion sie erzeugt.

### 52.4 „DER COIN" stand über einem WisdomTree-Zertifikat

> ⚠️ Die Mailüberschrift war fest `1. DER COIN` — aus der Zeit, als die Kette
> nur Krypto bediente. Seit dem Vollumstieg stand sie über **OD7H** (Zertifikat
> auf Gold) und **DBPK** (inverser S&P-ETF).

Kein Defekt der Kette — aber ein Etikett, das dem Leser etwas anderes sagt, als
vor ihm liegt. Dieselbe Regel wie bei den Faktensätzen.

| Instrument | Überschrift |
|---|---|
| spot, hebel | **1. DER WERT** |
| absicherung | **1. DIE ABSICHERUNG** |

Die Absicherung bekommt einen eigenen Namen, weil sie ausdrücklich **kein**
Trade ist — der Prompt sagt es dem Modell, die Mail sagt es jetzt dem Leser.

### 52.5 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **886, alle bestanden** (8 neue) |
| freie Namen | 0 |
| Simulation gegen NB-Backup | **6 Gruppen**, 12 Signale, 14 Mails, 0 Fehler, 0 Lücken |
| Simulation gegen Entwicklungsstand | 4 Gruppen, 0 Fehler |
| `pruefe_phase1.py` | bestanden |

**Eine bestehende Prüfung hat die Änderung gefangen** — Paket 11 verlangte
`1. DER COIN` in der gerenderten Mail. Sie prüft jetzt dieselbe Absicht
(Reihenfolge und Vollständigkeit) am neuen Namen, plus die eigene Überschrift
der Absicherung.

> ⚠️ **Zwei eigene Fehler in dieser einen neuen Prüfung**, beide an der
> Testeingabe: ein selbstgebautes `rechnung`-dict ohne `einstieg_von_eur`, und
> **keine Fakten übergeben** — dann bleibt Abschnitt 1 leer, und `_abschnitt()`
> lässt ihn zu Recht ganz weg. Der Test suchte eine Überschrift, die es ohne
> Inhalt gar nicht geben darf.
>
> Derselbe Typ wie die streng steigende Testreihe und der Blockname mit
> Leerzeichen: **die Eingabe stellt den Fall nicht her, den sie prüfen will.**

### 52.6 Was das für die Arbeitsweise heisst

**Die Simulation läuft ab jetzt gegen das NB-Backup**, nicht gegen den
Entwicklungsbestand. Dort fehlen sechs Reihen (Rohstoffe, 3QSS, X136), und
genau die Gruppen mit den dünnsten Daten wären ungeprüft geblieben.

Das Backup liegt bei jedem Export daneben und muss nicht angefordert werden.

---

## Kapitel 53 — Gegenprüfung der grünen Punkte: ein Ausfall und ein Schatz (16.08.2026)

**Nutzerfrage vor Phase III:** *„haben wir alle grünen Punkte und Parameter
erledigt oder haben wir hier noch Schätze — sind für alle drei Rollen
ausreichend Mindestkriterien je Assetgruppe vorhanden, und haben wir die
Information, ob unsere Quellen noch Daten für uns haben?"*

**Antwort: nein, und in beide Richtungen.** Ein Punkt, der als erledigt galt,
ist es in der Produktion nicht — und eine Tabelle mit 99 Jahren Historie sieht
keine Rolle.

### 53.1 Der Ausfall: Rolle A bekommt in der Produktion 12 statt 15 Aussagen

**Gemessen am NB-Backup, am echten Lagebild der Produktion:**

```
Rolle A bekam 12 Aussagen.
FEHLT: Netto-Liquiditaet, Zinskurve, Anlegerstimmung
```

**Es fehlen genau die drei, die NICHT aus der Kursreihe stammen** — also die
gesamte Dimension A4 (Liquidität/Makro) und A5 (Stimmung). In Kapitel 42 stand
A4 als **„erfüllt"**. Das galt für den Desktop.

**Die Ursache liegt nicht im Code:**

| | NB (Produktion) | Desktop |
|---|---:|---:|
| `macro_snapshot` Zeilen | **36** | 3.384 |
| Fear & Greed | **36** | 3.111 |
| `netto_liquiditaet_mrd` | **Spalte fehlt** | 501 |
| `rendite_10j_pct` | **Spalte fehlt** | 2.414 |

**Die Nachladeläufe vom 12.08. sind nie auf dem Notebook gelaufen.** Die
Skripte liegen im Repo (`lade_makro_historie_nach.py`,
`lade_fear_greed_nach.py`) — sie wurden dort nur nie ausgeführt.

> **36 Zeilen reichen nicht für ein 250er-Perzentil.** Deshalb entfällt auch
> der Stimmungssatz, obwohl `fear_greed_value` befüllt ist.

**„Fail-soft ist fail-silent", zum wievielten Mal.** `lade_makro()` und
`lade_stimmung()` geben bei einem Fehler ein leeres dict zurück, und der Satz
entfällt lautlos. Für den Einzelausfall richtig — dass die halbe
Makro-Dimension seit Tagen fehlt, darf niemandem entgehen.

**Behoben, soweit im Code möglich:** das Lagebild meldet jetzt, **welche**
Dimension fehlt.

```
WARNING Lagebild ohne Netto-Liquiditaet, Zinskurve, Anlegerstimmung -
        12 Aussagen statt der erwarteten 15. Pruefen, ob
        `lade_makro_historie_nach.py` und `lade_fear_greed_nach.py`
        auf DIESEM Geraet gelaufen sind.
```

> ⚠️ **Der Rest liegt beim Nutzer:** die beiden Skripte müssen **auf dem
> Notebook** laufen. Ohne sie urteilt Rolle A weiter ohne Makro und ohne
> Stimmung — und jede frühere Aussage über die Qualität des Lagebilds steht auf
> zwölf statt fünfzehn Aussagen.

### 53.2 Der Schatz: 99 Jahre Makro-Historie, die keine Rolle sieht

`makro_historie_monat` — **1.185 Monate, ab 1927, aktuell bis 2026-08**:

| Kennzahl | Monate | ab |
|---|---:|---|
| `spx_close`, `spx_trend_deviation_std` | **1.185** | **1927-12** |
| `oel_wti` | 967 | 1946 |
| `cpi_yoy_prozent` | 942 | 1948 |
| `fed_funds_rate` | 865 | 1954 |
| **`rendite_10y`** | **776** | **1962** |
| `dxy_proxy` | 248 | 2006 |

**Sie wird von `makro_analog_job` gefüllt** (12 Läufe im Fenster) und von
**keinem Prompt gelesen**.

**Zwei Dinge sind daran bemerkenswert:**

**Erstens:** `rendite_10y` ist genau die Größe, die Rolle A heute fehlt — nur
in einer anderen Tabelle und in monatlicher Auflösung. Makro **ist** monatlich
(CPI, Fed), also ist das kein Nachteil.

**Zweitens:** `spx_trend_deviation_std` ist die Abweichung des breiten Marktes
vom eigenen Langfristtrend **in Standardabweichungen, über 99 Jahre**. Das ist
bereits die Form, die R-T5 verlangt — relativ zur eigenen Historie, nicht
absolut.

**Durch die sieben Aufnahmeprüfungen (R-R4):**

| | | |
|---|---|---|
| P1 | Auftrag | Marktlage → **Rolle A** ✓ |
| P2 | Eignung | Praxis: Makro ist eine der vier Dimensionen ✓ |
| P3 | Nicht-Redundanz | stammt aus **keiner** unserer Kursreihen ✓ |
| P4 | Informationsgrenze | LLM1, kein Konflikt mit Rolle G ✓ |
| P5a | gehört es ins Modell? | beschreibend, kein Etikett ✓ |
| P5b | übersetzt? | *„1,6 Standardabweichungen über dem Langfristtrend"* ✓ |
| P6 | Unterscheidungskraft | bewegt sich monatlich ✓ |
| P7 | Risikoklasse | **grün** ✓ |

**Ein Kandidat, der alle sieben besteht — und er kostet keinen einzigen neuen
Abruf.**

### 53.3 Der Stand der Mindestkriterien, korrigiert

| Rolle | Soll | Produktion |
|---|---|---|
| **A** | 4 Dimensionen + Stimmung | **2 von 4** — Trend ✓, Volatilität ✓, Breite gestrichen, **Makro ✗**, **Stimmung ✗** |
| **BC** | CSTI + 4 | 3 von 4 CSTI, **Auslöser fehlt** · 1,5 von 4 Auswahlkriterien |
| **G** | 2 unabhängige Quellen | **1** — und nur bei Krypto |

> **Rolle A galt als die am besten aufgestellte Rolle.** Nach dieser Messung
> ist sie es nicht: von vier Praxisdimensionen liefert die Produktion zwei.

### 53.4 Was NICHT gefunden wurde

Alle 38 Spalten in `macro_snapshot` sind befüllt und aktuell — VIX, Dollar-Index,
M2 für vier Währungsräume, CPI, fünf Leitzinsen, BTC-Dominanz, Zyklusrisiko.
**Sie erreichen keine Rolle**, sind aber auch nicht als grüne Punkte geführt;
sie durch P1–P7 zu schicken ist eigene Arbeit, keine Nachlese.

`hebel_triggers` mit **52.770** Zeilen bleibt der bekannte Fall: gerechnet,
niemand liest ihn — und als Prompt-Parameter durch P4 gesperrt (Kapitel 43).

### 53.5 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **886, alle bestanden** |
| freie Namen | 0 |
| Simulation gegen NB-Backup | 6 Gruppen, 0 Fehler, 0 Lücken |
| `pruefe_phase1.py` | bestanden |
| Warnung funktional geprüft | schlägt gegen das NB-Backup an, schweigt bei vollständigen Daten |

---

## Kapitel 54 — Die Mindestkriterien als Code (16.08.2026, abends)

**Nutzerfrage:** *„sind die neuen Mindestkriterien bereits implementiert und
geprüft?"* — **Nein, sie standen als Text.** Und genau diese Lücke hat am
selben Tag zugeschlagen: Rolle A urteilte in der Produktion mit **12 statt 15**
Aussagen, weil zwei Makro-Spalten auf dem Notebook fehlten. `lade_makro()` ist
fail-soft, der Satz entfiel lautlos.

> **Eine Rolle, deren Mindestgrundlage niemand prüft, urteilt auch dann weiter,
> wenn ihr ein Drittel fehlt — und die Ausgabe sieht genauso aus.**

`agent/mindestkriterien.py` prüft jetzt alle drei Rollen an **einer** Stelle.

### 54.1 Was je Rolle verlangt wird

| Rolle | Kriterium | heute |
|---|---|---|
| **A** | Trend · Volatilität · Liquidität · **Makro** · **Stimmung** | **erfüllt**, seit die Nachladeläufe auf dem NB liefen (3.115 / 502 / 2.417) |
| **BC** | Auftrag · Lage · Block `bestand` · Block `verlauf` | erfüllt |
| **G** | **zwei unabhängige QUELLEN** (R-R3/G1) | **nicht erfüllt — eine** |

**Drei Dinge sind bewusst NICHT Kriterium:**

**Die Breite** bei Rolle A — sie ist am 12.08. ersatzlos gestrichen worden. Sie
zu verlangen hiesse, etwas zu fordern, das wir entfernt haben.

**Der Auslöser** bei Rolle BC — er fehlt strukturell und hat eine eigene Phase.
Eine Warnung bei **jedem** Urteil liest niemand.

**Das Regime** als Quelle bei Rolle G — es wird aus BTC-Kurs und Fear & Greed
gerechnet, und beides sieht Rolle A bereits. Es steht bei G, weil sie sonst
gar nichts hätte, aber es ist **keine fremde** Quelle.

### 54.2 Rolle G zählt QUELLEN, nicht Zahlen

```
Quellen heute -> ['terminmarkt']
fehlt         -> ['G1: 1 von 2 unabhaengigen Quellen (terminmarkt)']
mit COT       -> ['terminmarkt', 'cot'] | fehlt: nichts
```

Open Interest, Finanzierungsrate und Long-Konten stammen aus **einer** Tabelle
und beschreiben dieselbe Menge Menschen auf derselben Börse. **Drei Zahlen,
eine Quelle.**

Vorher stand dort `len(fehlt) >= 3` — eine grobe Regel, die zufällig
funktionierte, weil die drei Zahlen alle da oder alle weg sind. Sie bleibt als
unterste Grenze erhalten (G5: ohne jede Grundlage wird nicht gefragt).

### 54.3 Melden ist die Vorgabe, Sperren die Ausnahme

```yaml
mindestkriterien:
  melden: true
  sperren: []      # A, BC, G - leer = nichts sperrt
```

**Ein Modul, das beim blossen Einspielen eine Rolle stilllegt, nimmt dem Nutzer
die Entscheidung ab** — dieselbe Regel wie bei `rollen_kette.aktiv_fuer` und
`anlass.aktiv`. Hier wäre sie besonders teuer: **Rolle G erfüllt ihre eigene
Mindestgrundlage heute nicht** und wäre sofort stillgelegt.

**Je Rolle schaltbar**, nicht als ein Schalter für alle — die drei haben sehr
verschiedene Lücken.

### 54.4 Der Gegentest, und was er gefunden hat

| Konfiguration | Signale | Rolle-G-Aufrufe |
|---|---:|---:|
| ohne sperren | 1 | 1 |
| **`sperren=[G]`** | **1** | **0** |
| `sperren=[BC]` | 1 | 1 |

Das Signal bleibt, wenn G gesperrt wird — **richtig, denn Rolle G kippt
nichts.** Und `sperren=[BC]` ändert nichts, weil BC seine Grundlage erfüllt.

> ⚠️ **Der erste Gegentest war falsch aufgesetzt.** Beide Läufe gingen auf
> dieselben Symbole, und der **Cooldown des ersten** erklärte die Null des
> zweiten. Erst mit Zurückdatieren vor jedem Lauf wurde der Vergleich gültig.

> ⚠️ **Und dann fand er einen echten Fehler:** `sperren=[G]` änderte nichts.
> `rolle_g` hatte den Parameter, aber `hole()` reichte ihn nicht durch — **die
> Konfiguration erreichte die Rolle nie.** Zum zweiten Mal an einem Tag
> dasselbe Muster wie beim Symbol, das Rolle G tagelang totlegte. Eine eigene
> Prüfung hält den Weg jetzt offen.

### 54.5 Was die Prüfungen im Betrieb zeigen

Aus dem Ende-zu-Ende-Lauf gegen das NB-Backup:

```
Rolle G (PLTR):  G1: 0 von 2 Quellen (keine); G2: keine symbolspezifische Quelle
Rolle G (ASTER): G1: 1 von 2 Quellen (terminmarkt)
Rolle G (OD7H):  G1: 0 von 2 Quellen (keine); G2: keine symbolspezifische Quelle
```

**Damit steht schwarz auf weiss, was bisher nur im Plan stand:** Aktien,
Rohstoffe und ETF haben für die Gegenprüfung **gar keine** Grundlage, Krypto
hat die Hälfte.

### 54.6 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **898, alle bestanden** (12 neue) |
| freie Namen | 0 |
| Simulation NB-Backup | 6 Gruppen, 0 Fehler, 0 Lücken |
| Simulation Entwicklungsstand | 4 Gruppen, 0 Fehler |
| `pruefe_phase1.py` | bestanden |
| Sperr-Gegentest | je Rolle nachgewiesen |

---

## Kapitel 55 — Recherche vor Phase III: wie die Lücken je Assetgruppe zu schliessen sind (16.08.2026)

**Nutzervorgabe:** *„es wäre wünschenswert, wenn wir jedenfalls die Lücken
schliessen können und eine brauchbare Rolle G haben — alle Rollen haben die
erforderlichen Mindestkriterien, LLM-fähig, und diese je Assetgruppe bzw.
Handelsstrategie; erst danach können wir über eine Erweiterung nachdenken."*

**Damit ist die Reihenfolge gesetzt: Mindestkriterien zuerst, Optimierung
später.** Diese Recherche fragt deshalb nur eines — **womit** die Lücken zu
schliessen sind, und **ob es das kostenlos gibt.**

### 55.1 Der grösste Fund liegt in der eigenen Datenbank

> ⚠️ **TEILWEISE WIDERRUFEN durch Kapitel 56 (16.08., später am Tag).**
> Von den drei Feldern ist nur das **Open Interest** wirklich je Börse
> erhoben. `funding_rate` (Kraken) und `long_account_pct` (Binance)
> werden je einmal geholt und unter alle drei Börsenetiketten
> geschrieben — 0 von 41.547 bzw. 0 von 40.033 gemeinsamen
> Zeitpunkten weichen ab. Die Zeilenzahlen unten stimmen, ihre
> Deutung als *zweite Quelle* gilt nur für das Open Interest.

`positionierung.py` liest `WHERE exchange = 'binance'`. In derselben Tabelle
stehen:

| Börse | Zeilen | Symbole | aktuellster Stand |
|---|---:|---:|---|
| binance | 43.310 | 37 | 16.08. 07:40 |
| **bybit** | **40.177** | **35** | 16.08. 07:40 |
| **okx** | **36.681** | **31** | 16.08. 07:40 |

**Alle drei Felder je Börse befüllt** — offene Kontrakte, Finanzierungsrate,
Long-Konten. **22 Symbole tragen mindestens zwei Börsen**, vierzehn davon alle
drei. Kostenlos, ohne Schlüssel, seit Monaten laufend — und `api/derivatives.py`
holt sie bereits.

> **Damit ist G1 für Krypto formal erfüllbar, ohne eine einzige neue Quelle.**

**Aber ehrlich zur Qualität — und das entscheidet, ob es ein Lückenschluss oder
ein Scheinlückenschluss ist:**

Bybit und OKX sind eine **andere Stichprobe derselben Grundgesamtheit**, nicht
eine andere Informationsart. Sie messen dasselbe Phänomen an anderen
Teilnehmern. Nach der Debattenliteratur zählt aber die **Informationsgrenze**,
nicht die Zahl der Endpunkte.

**Was WIRKLICH neu ist, ist die Divergenz.** Die Praxisliteratur führt die
Funding-Spanne zwischen Börsen als eigene Grösse — allerdings primär als
**Arbitrage**-Gelegenheit, nicht als Richtungssignal. Für uns heisst das:

```
"Auf Binance stehen 65 % der Konten long, auf OKX 52 % -
 die Positionierung ist zwischen den Boersen uneinig."
```

Das ist eine Aussage über **Uneinigkeit**, die weder BC noch die heutige Rolle G
hat. Sie ist LLM-tauglich (zwei Zahlen mit Bezug zueinander) und grün.

> **Meine Einordnung:** die zweite Börse erfüllt G1 dem Buchstaben nach und
> **halb** dem Sinn nach. Der Gewinn liegt in der Divergenz, nicht in der
> Verdopplung. Als **echte** zweite Informationsart bleibt der Optionsmarkt.

### 55.2 Was je Assetgruppe fehlt — und was es kostenlos gibt

| Gruppe | Rolle G braucht | vorhanden? | Kosten |
|---|---|---|---|
| **Krypto** | 2. Quelle | **Bybit + OKX in der DB** · Deribit gebaut | **frei** |
| **Aktien** | 2 Quellen | **FINRA Short Interest** + **SEC Form 4** gebaut, live geprüft | **frei** |
| **Rohstoffe** | 2 Quellen | **CFTC COT** (4 Symbole gemappt) + **EIA** | frei, **EIA braucht Schlüssel** |
| **ETF / Absicherung** | 2 Quellen | ⚠️ **nichts** | — |

> ⚠️ **Für ETF gibt es keine kostenlose Quelle.** Fondsflüsse, NAV-Prämie und
> Positionierung liegen bei Massive/ETF Global (ab 99 $/Monat), Intrinio, EPFR,
> Cbonds — durchgängig kostenpflichtig. Die Nutzervorgabe *„nur kostenfreie
> Quellen"* schliesst sie aus.
>
> **Der einzige freie Weg wäre indirekt:** CFTC COT auf die **Index-Futures**
> (E-mini S&P 500, E-mini Nasdaq-100). Das trifft nicht den ETF, sondern seinen
> Referenzindex — für DBPK (S&P) und 3QSS (Nasdaq) ist das nah genug, für einen
> Kupfer- oder Rüstungs-ETF nicht. **Die Marktnamen sind unverifiziert.**

**Konsequenz, die ich klar sagen muss:** *„alle Rollen haben die
Mindestkriterien je Assetgruppe"* ist für **Themen-ETF nicht erreichbar**,
solange nur kostenlose Quellen zulässig sind. Erreichbar sind vier von fünf
Gruppen plus die Absicherung über den Referenzindex.

### 55.3 Die BC-Lücken — zwei liegen ebenfalls schon da

| Lücke | Quelle | Stand |
|---|---|---|
| **Aktientermine** (Quartalszahlen) | `yfinance_client.naechstes_earnings_datum` | **gebaut**, in der alten Pipeline |
| **Fundamentaldaten** | KGV, Forward-KGV, Gewinnwachstum, Dividende, Analystenkonsens | **gebaut**, dieselbe Stelle |
| Handelbarkeit / Spread | Bitpanda-Listung + Override | gerechnet, **gelb** |
| Auslöser | `hebel_screening` | **gesperrt durch P4** (Kapitel 43) |
| Katalysator / Nachrichten | — | **keine Quelle** |
| Zertifikatsnatur | — | eigener Rechercheschritt |

**Die Ablationsstudie nennt Nachrichten und Fundamentaldaten als die beiden
tragenden Quellen.** Die Fundamentaldaten haben wir — sie erreichen nur keine
Rolle.

### 55.4 Was das für Phase III bedeutet

**Phase III ist gelb und rot** — Kostenhöhe, Aktientermine, Zertifikatsnatur,
Handelbarkeit. Sie darf erst laufen, wenn die Mindestkriterien stehen, denn
sonst misst der gepaarte Vergleich die Lücke statt die Änderung.

**Die Reihenfolge, die aus dieser Recherche folgt:**

| | Schritt | Gruppe | Aufwand | Klasse |
|---|---|---|---|---|
| **1** | **Bybit/OKX in Rolle G** — Divergenz als eigene Aussage | Krypto | **klein**, Daten liegen | grün |
| **2** | **CFTC COT** in Rolle G — als Perzentil, nicht als Netto-Position | Rohstoffe | mittel, **braucht Persistenz** | grün |
| **3** | **FINRA + SEC Form 4** in Rolle G | Aktien | mittel | grün |
| **4** | **Fundamentaldaten + Termine** zu BC | Aktien | mittel, als **Tausch** | grün/gelb |
| **5** | COT auf Index-Futures | Absicherung | **Marktnamen prüfen** | grün |
| — | Themen-ETF | — | **nicht kostenlos lösbar** | — |
| **dann** | **Phase III** | alle | gepaarter Vergleich | gelb/rot |

**Schritt 1 ist der einzige, der heute ohne neue Anbindung geht** — und er
schliesst die Lücke, die als einzige beziffert vor uns liegt.

### 55.5 Was die Recherche NICHT hergegeben hat

**Keine kostenlose ETF-Flussquelle.** Alle geprüften Anbieter sind
kostenpflichtig; ETF.com, VettaFi und ICI aggregieren, geben aber keine freie
API.

**Kein Beleg, dass die Funding-Divergenz die RICHTUNG vorhersagt.** Die
Literatur führt sie als Arbitrage-Grösse. Als Fakt über die Positionierung ist
sie zulässig; als Richtungssignal wäre sie unbelegt — und damit P2 Rang 3, also
nicht aufnahmefähig.

**Quellen:**
[CoinGlass — Derivatedaten je Börse](https://www.coinglass.com/CryptoApi) ·
[CoinAPI — historische Funding-Raten](https://www.coinapi.io/blog/historical-crypto-funding-rates-api-coinapi) ·
[Funding-Rate-Arbitrage Binance/Bybit/OKX](https://yieldo.me/blog/funding/funding-rate-arbitrage-guide) ·
[Funding-Raten lesen](https://zipmex.com/blog/how-to-analyze-funding-rates-in-crypto/) ·
[Massive/ETF Global — Fund Flows, ab 99 $](https://massive.com/docs/rest/partners/etf-global/fundflows) ·
[Intrinio — ETF NAV Flows](https://docs.intrinio.com/documentation/web_api/get_etf_nav_flows_v2) ·
[CFTC Commitments of Traders](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm)

---

## Kapitel 56 — Schritt 1 gebaut, und Kapitel 55 zur Hälfte widerrufen (16.08.2026)

### 56.1 Die Korrektur zuerst: zwei von drei Feldern sind Kopien

**Kapitel 55 hat gemeldet, Bybit und OKX seien eine zweite Quelle für Rolle G.
Das stimmt nur für ein Feld von dreien.** Nachgezählt am Produktionsbestand:

| Feld | gemeinsame Zeitpunkte | davon verschieden |
|---|---:|---:|
| `long_account_pct` | 41.547 | **0** |
| `funding_rate` | 40.033 | **0** |
| `open_interest` | 41.551 | **41.551** |

**Die Ursache steht in `hebel_screening._hole_und_speichere`** (Zeilen 75–124):
die Finanzierungsrate wird **einmal bei Kraken** geholt, der Long-Anteil
**einmal bei Binance** — und beide dann in **alle drei** Börsenzeilen
geschrieben. Nur das Open Interest wird je Börse wirklich abgerufen.

> ⚠️ **Die Spalte `exchange` behauptet für zwei von drei Feldern etwas, das die
> Daten nicht hergeben.** Wer `WHERE exchange = 'bybit'` schreibt und eine
> Finanzierungsrate liest, bekommt Kraken-Daten unter falschem Etikett.

**Gefunden nicht durch Lesen, sondern durch Rechnen.** Der Plan sah plausibel
aus, die Zeilenzahlen sahen plausibel aus. Erst die Frage *„weichen die Werte
überhaupt voneinander ab?"* hat es aufgedeckt — dieselbe Lehre wie am 12.08.
und am 13.08.: **ein Plan ist eine Absicht, eine Tabelle ist keine Messung.**

### 56.2 Was von Schritt 1 übrig bleibt — und es trägt

**Open Interest je Börse ist echt.** Gemessen über **8.087 gepaarte
Zeitpunkte** und 22 Symbole, 8-Stunden-Fenster:

| | Spanne der OI-Änderung zwischen den Börsen |
|---|---|
| Median | **3,00 pp** |
| 90. Perzentil | 10,93 pp |
| Maximum | 70,88 pp |
| Anteil > 1 pp | **85,3 %** |

**Das ist kein konstantes Feld** (R-T6) — die Perzentile der ausgelieferten
Sätze streuen über 0 bis 96.

**Nur Änderungen, nie Niveaus.** Binance führt ein Vielfaches der Kontrakte von
OKX; absolute Stände zu vergleichen hieße, Börsengrößen zu messen statt
Verhalten.

**Abdeckung: 35 von 39 Symbolen.** Gegenprobe mit nur einer Börse in der
Tabelle: keine Divergenz, die übrigen Sätze bleiben vollständig.

### 56.3 Der Nutzerhinweis, der den Satzbau umgeworfen hat

> *„wurde der Parameter ausreichend gegengeprüft, ob es positiv für unsere
> LLM-Config ist bzw. nicht schädlich — da LLMs nicht mit Zahlen umgehen bzw.
> auch nicht rechnen sollen."*

**Mein Entwurf verstieß dagegen.** Er lieferte:

```
"... an den Boersen ungleich: OKX +0.0 %, Bybit -1.3 %."
"Die Spanne zwischen den 3 Boersen betraegt 1.3 Prozentpunkte; ..."
```

**Drei Zahlen, und die dritte ist die Differenz der ersten beiden.** Ein Modell,
dem man Summand, Summand und Summe hinlegt, prüft nach statt zu urteilen.

**Die Fassung, die ausgeliefert wird:**

```
Die offenen Kontrakte am Terminmarkt sind auf Binance in den letzten
  8 Stunden um 0.1 % gefallen.
Die Boersen entwickeln sich dabei uneinheitlich: auf Bybit nehmen sie
  staerker ab als auf OKX.                                    <- keine Zahl
Wie weit sie auseinanderliegen, steht im 26. Perzentil der letzten
  368 Messungen dieses Werts - im gewohnten Bereich.
```

**Der Richtungssatz trägt null Zahlen**, das Perzentil trägt seinen Maßstab und
seine Einordnung. Daraus sind **R-T10** und **R-T11** geworden.

> **Bewusst ohne Deutung.** Beim Funding steht ein Hinweis, was ein Extremwert
> bedeutet — er ist durch die Praxisliteratur gedeckt. Für die Börsendivergenz
> ist er das **nicht**: die Literatur führt die Spanne als Arbitrage-Größe, nicht
> als Richtungssignal. Eine Deutung wäre meine Vermutung, Rang 3 der
> Eignungsleiter (P2), und damit nicht aufnahmefähig.

### 56.4 Rückwirkende Prüfung: 445 Sätze, ein echter Fund

**Nutzervorgabe:** *„prüfe rückwirkend, ob wir weitere solche Fehler bereits im
System haben — bei den zukünftigen Punkten bitte prüfen."*

Dafür `pruefe_zahlen_in_prompts.py`, gerendert aus **echten** Daten:

| Rolle | Quelle der Sätze |
|---|---|
| A | `lagebilder.fakten_json` — der Produktionswortlaut selbst |
| BC | `lagebeschreibung.geteilt()` über 30 echte Reihen |
| G | `positionierung.saetze()` über 40 Symbole |

**Der eine Fund — und er ist älter als der Umbau:**

```
vorher:  66 % der Konten stehen long; das ist das 92. Perzentil der
         eigenen Historie.
nachher: 67 % der Konten stehen long; das ist das 82. Perzentil der
         letzten 400 Messungen - im gewohnten Bereich.
```

**Zwei Mängel in einem Satz, in 37 von 37 Fällen:** keine Einordnung (R-T11)
und kein genanntes Fenster (R-T1). Der Nachbarsatz über die Finanzierungsrate
macht beides seit jeher richtig.

> ⚠️ **Der erste Lauf meldete 33 Fälle, von denen 31 Fehlalarme waren** — mein
> Prüfer rechnete einen Tageszähler gegen ein Prozent (*„5 Tage −3,4 %"* gegen
> *„20 Tage −8,4 %"*) und hielt die Ziffer in **3QSS** für eine nackte Zahl.
> Behoben durch Einheitenbindung und eine Wortgrenze — **und durch einen
> Selbsttest mit sieben Fällen**, darunter mein eigener Entwurf als
> Positivprobe und beide Fehlalarme als Gegenprobe.
>
> **Ein Prüfer ohne Prüfung ist eine Meinung.**

### 56.5 Kein zweites Werkzeug für dieselbe Frage

**Nutzerhinweis:** *„prüfe, ob du nicht bereits ein geeignetes Werkzeug gebaut
hast für LLM-Prüfung — damit du es nicht mehrfach baust."*

**Es gab eines** — `pruefe_fakten_bezugsgroessen.py` vom 09.08. Die Grenze steht
jetzt **in beiden Dateien**:

| | `pruefe_fakten_bezugsgroessen.py` | `pruefe_zahlen_in_prompts.py` |
|---|---|---|
| Gegenstand | JSON-Faktendicts der alten Pipelines | gerenderte **Sätze** der Rollen A/BC/G |
| entstanden | 09.08. | 16.08. (die Rollen kamen 10.–16.08.) |
| N2 nackte Zahl | ✓ je Feld | ✓ je Satz |
| N1 Rechenaufgabe | — | ✓ |
| N3 Perzentil ohne Einordnung | — | ✓ |

**Ein Satz ist kein Feld:** *„OKX +0,0 %, Bybit −1,3 %, Spanne 1,3 Punkte"* hat
je Zahl einen tadellosen Bezug und ist trotzdem eine Rechenaufgabe.

### 56.6 Was Schritt 1 für die Mindestkriterien NICHT tut

**Rolle G erfüllt G1 weiterhin nicht.** `mindestkriterien.QUELLEN_G` gruppiert
nach **Informationsart**, nicht nach Endpunkt — drei Börsen bleiben *eine*
Terminmarktquelle. Das ist Absicht: G1 zu erfüllen, indem man dieselbe Größe
dreimal zählt, wäre eine Selbsttäuschung im Code.

> **Schritt 1 macht Rolle G inhaltlich besser, nicht formal vollständig.** Die
> zweite Informationsart bleibt offen — Optionsmarkt, COT, Short Interest.

### 56.7 Gegenprüfung

| | |
|---|---|
| `pruefe_zahlen_in_prompts.py` | Selbsttest **7/7**, 445 Sätze, **kein Befund** |
| Paketprüfungen | **898, alle bestanden** |
| freie Namen | 0 |
| `pruefe_phase1.py` | bestanden |
| Simulation gegen NB-Backup | **6 Gruppen**, 12 Signale, 14 Mails, **0 Fehler, 0 Lücken** |
| Gegenprobe Divergenz | eine Börse allein → keine Divergenz, übrige Sätze vollständig |

### 56.8 Offen aus diesem Kapitel

| | Punkt | Warum nicht jetzt |
|---|---|---|
| **1** | **`funding_rate`/`long_account_pct` unter fremdem Börsenetikett** | `compute_funding_rate_percentile` liest sie aus den Binance-Zeilen — ein Eingriff trifft das Hebel-Screening in der Produktion |
| **2** | echte Funding-Divergenz | `get_bybit_funding_history` existiert und ist live geprüft; kostet einen zusätzlichen Abruf je Symbol und Lauf |
| 3 | Long-Anteil je Börse | Bybit/OKX haben Endpunkte, gebaut ist keiner |

---

## Kapitel 57 — Die breite Suche: die unerwartete Quelle war der eigene Ordner (16.08.2026)

**Nutzeridee:** *„zu den Themen-ETF können wir hier selbst Daten erhalten durch
die BP-API … versuche die Recherche etwas breiter für die bestehenden Lücken,
u.U. werden die Daten über einen kostenlosen Anbieter verfügbar gemacht, mit dem
man nicht rechnet, da die Quelle primär andere Daten bereitstellt."*

**Der Gedanke trägt — und er hat zweimal getroffen.**

### 57.1 Bitpanda: nein, und zwar aus einem strukturellen Grund

`api/bitpanda.py` gibt es seit dem 09.07. `GET /v3/assets` ist öffentlich,
ohne Schlüssel, 3.238 Einträge über alle Anlageklassen. **Aber es ist ein
Verzeichnis**, kein Marktdatendienst: Symbol, Name, Gruppe, Handelbarkeit. Der
authentifizierte Teil (`/v1/wallets`, `/v1/trades`) liefert **unser eigenes**
Depot, nicht die Positionierung anderer.

> Eine Brokerschnittstelle kennt den Markt nicht — sie kennt ihren Kunden.
> Für die Handelbarkeit ist sie die richtige Quelle, und dafür ist sie im
> Einsatz. Für Rolle G ist sie strukturell blind.

### 57.2 Der eigentliche Fund: sechs fertige Clients für genau diese Lücken

**Es musste gar nichts recherchiert werden — es liegt im Ordner `api/`:**

| Client | seit | liefert | kostenlos, Schlüssel |
|---|---|---|---|
| **`onchain.py`** | 08.07. | **CoinMetrics**: MVRV, NUPL, Realized Price, **Börsen-Zuflüsse**, Stablecoin-Angebot | ja, **keiner** |
| `deribit.py` | 26.07. | DVOL, Options-Skew (BTC) | ja, keiner |
| `cftc_cot.py` | 18.07. | COT „Managed Money", Rohstoffe | ja, keiner |
| `finra.py` | 19.07. | Short Interest, Aktien | ja, keiner |
| `sec_edgar.py` | 19.07. | Form 4 Insider, Aktien | ja, keiner |
| `finnhub.py` | 19.07. | Analysten-Trend, Aktien | ja, Schlüssel |

> **`onchain.py` ist die Antwort auf die Krypto-Lücke, nach der Kapitel 55
> gesucht hat.** Börsen-Zuflüsse und MVRV sind eine **andere Informationsart**
> als Terminmarkt-Positionierung — nicht bloß eine zweite Stichprobe. Genau das,
> was G1 dem SINN nach verlangt und was drei Börsen nicht leisten.

**Die Lückenschließung ist damit überwiegend kein Beschaffungs-, sondern ein
Verdrahtungsproblem.**

### 57.3 Der zweite Treffer für die ETF-Lücke — mit harter Grenze

**yfinance ist primär eine Kursquelle und trägt trotzdem Fondsdaten:**

| Symbol | Fondsvolumen | NAV |
|---|---:|---:|
| VVMX | 1.063.055.872 | — |
| EXH3 | 328.757.344 | 65,52 |
| CEBS | 486.353.088 | 11,161 |
| DBPK | 47.249.068 | 0,1504 |
| 3QSS · X136 · ISOC | — | — |
| OD7C/H/L/N | — | — |

**Das Fondsvolumen über die Zeit IST der Fondsfluss** — die Größe, die bei
Massive/ETF Global ab 99 $/Monat kostet (Kapitel 55.2).

**Aber drei Einschränkungen, und die dritte ist die wichtigste:**

**Erstens: 4 von 13.** Drei ETFs tragen nichts (ISIN- bzw. München/Mailand-
Notierungen), die vier Rohstoff-Zertifikate strukturell nicht — ein Zertifikat
ist kein Fonds und hat kein Fondsvolumen. **Eine Teillösung, kein Lückenschluss.**

**Zweitens: keine Historie.** yfinance liefert den Momentanwert. Die Reihe muss
ab dem ersten Tag selbst aufgebaut werden — dasselbe Persistenzproblem wie beim
COT.

**Drittens — und hier wäre es beinahe schiefgegangen:**

> ⚠️ **Der NAV steht in gemischten Währungen.** Gegen unsere Kursreihe gerechnet:
>
> | | Kurs | NAV | Verhältnis |
> |---|---:|---:|---:|
> | EXH3 | 65,56 EUR | 65,52 | 1,00 |
> | DBPK | 0,1304 EUR | 0,1504 | **1,153** |
> | CEBS | 9,643 EUR | 11,161 | **1,157** |
>
> **Zwei „Abschläge von 13 %" — und EUR/USD steht bei rund 1,16.** Das ist kein
> Abschlag, das ist der Wechselkurs. Ein naiv gebauter Prämien-Fakt hätte dem
> Modell reine Währungsumrechnung als Marktsignal geliefert.

**Dieselbe Klasse wie der Scheinwert von 51.000 EUR bei OD7H und wie die
kaputte CAT-Reihe:** ein Feld ist da, sieht plausibel aus, und trägt eine
andere Größe als sein Name behauptet. **Deshalb hier nichts gebaut.**

### 57.4 Was die breite Suche NICHT gefunden hat

**Keine kostenlose Positionierungsquelle für europäische Themen-ETF.** FINRA
Short Interest deckt **US-Listings** ab — unsere ETFs notieren in Frankfurt,
München und Mailand. Die Idee, FINRA als unerwartete ETF-Quelle zu nutzen,
scheitert an der Börse, nicht am Preis.

### 57.5 Die Reihenfolge, neu sortiert

**Kapitel 55.4 hat die Reihenfolge nach Aufwand sortiert. Nach diesem Kapitel
sortiert sie sich nach Informationsart:**

| | Schritt | schliesst | Aufwand |
|---|---|---|---|
| ~~1~~ | ~~Börsendivergenz~~ | **erledigt** (Kap. 56) | — |
| **2** | **`onchain.py` an Rolle G** | **G1 für Krypto, dem SINN nach** | klein — Client fertig |
| 3 | `cftc_cot.py` an Rolle G | Rohstoffe | mittel — braucht Persistenz |
| 4 | `finra.py` + `sec_edgar.py` an Rolle G | Aktien | mittel |
| 5 | Fondsvolumen-Reihe aufbauen | ETF, **teilweise** | klein, wirkt erst in Wochen |
| — | NAV-Prämie | — | **gesperrt**, bis die Währung je Fonds feststeht |

**Schritt 2 ist jetzt der erste** — nicht weil er der billigste ist, sondern
weil er als einziger eine zweite **Informationsart** bringt.

---

## Kapitel 58 — Schritt 2: Rolle G bekommt eine zweite Informationsart (16.08.2026)

**Bis heute hatte Rolle G EINE Quellenart.** Schritt 1 hat drei Börsen daraus
gemacht — das verbessert den Fakt, vermehrt aber die Art nicht: offene
Kontrakte bleiben offene Kontrakte. **R-R3 verlangt zwei unabhängige Quellen,
und unabhängig heißt: andere Erhebung, andere Frage.**

### 58.1 Die Messung hat den Kandidaten ausgewählt, nicht die Plausibilität

`api/onchain.py` bietet MVRV, NUPL, Realized Price, **Börsenzu- und -abflüsse**
und Stablecoin-Angebot. Bevor irgendetwas gebaut wurde, die Frage aus R-T6:
**bewegt sich das überhaupt?** Gemessen über das letzte Jahr, Perzentil im
730-Tage-Fenster:

| | Median | Streuung | verschiedene Werte | Extremtage |
|---|---:|---|---:|---:|
| **Netto-Börsenfluss** | **47** | 0–99 | **97** von 365 | 17 % |
| MVRV | **5** | 0–74 | 55 von 365 | **68 %** |

> **MVRV liegt seit einem Jahr fast durchgehend im untersten Dezil.** Der Satz
> hieße fast immer „außergewöhnlich niedrig" — ein konstantes Feld (R-T6), und
> zwar **gemessen statt vermutet.**

**Dazu kommt P3 (Nicht-Redundanz), und die Quelle dafür ist unser eigener Code.**
`agent/krypto/regime.py` hält seit dem 08.07. fest, dass MVRV, das
Log-Regressions-Risiko und Fear & Greed **dieselbe Frage** beantworten — und
Fear & Greed sieht Rolle A bereits.

**Stablecoin-Angebot fällt aus einem dritten Grund weg:** `get_stablecoin_supply`
liefert nur den Momentanwert, ohne Historie gibt es kein Perzentil und damit
keinen R-T5-konformen Satz.

**Der Netto-Börsenfluss bleibt — und er ist genau das, was fehlte:** gezählte
Münzbewegungen auf der Kette, keine Positionsstände an einem Terminmarkt.

### 58.2 Die Gratis-Stufe gibt weit mehr her, als die Kopfzeile sagt

**Live geprüft am 16.08.:**

| Metrik | Tage | ab | Lücken |
|---|---:|---|---:|
| `FlowInExNtv` / `FlowOutExNtv` | **5.593** | 2011-04-24 | **0** |
| `CapMVRVCur` u. a. | 6.434 | 2009-01-03 | 561 (die frühen Jahre) |

Die Modul-Kopfzeile spricht von einem „~30-Tage-Fenster" — **das galt für die
Preishistorie über einen anderen Weg, nicht für diese Metrik.** Wieder ein Fall
für *„immer an der Quelle prüfen"*: eine Kopfzeile ist eine Beschreibung, keine
Festlegung.

Abgerufen werden trotzdem nur **800 Tage** — genug für ein 730-Tage-Perzentil
mit Puffer, und schonend an einer Schnittstelle mit 10 Anfragen je 6 Sekunden.

### 58.3 Der Satz, nach R-T10 und R-T11

```
Am 2026-08-15 flossen mehr Bitcoin auf die Boersen als von ihnen herunter.
Gemessen an den letzten 730 Tagen steht diese Bewegung im 72. Perzentil
  - im gewohnten Bereich.
```

**Richtung ohne Zahl, Perzentil mit Fenster und Einordnung.** Der Zahlenprüfer
findet nichts.

> **Bewusst ohne Deutung.** Dass Zuflüsse Verkaufsdruck *ankündigen*, ist eine
> gängige Lesart — und in unseren Daten nie gemessen, also P2 Rang 3.
> `onchain.py` nennt sie im Feldkommentar „potenziell Verkaufsdruck"; genau
> dieses *potenziell* gehört nicht in einen Faktensatz.

### 58.4 Zwei Absicherungen, die das Ganze erst tragfähig machen

**Erstens: nur für Krypto, fail-closed.** Ein Satz über Bitcoin-Bewegungen in
der Beurteilung einer Aktie wäre kein fehlender Fakt, sondern ein falscher (P1).
Die Assetklasse wird deshalb **explizit durchgereicht** —
`rollen_lauf` → `ZM.hole` → `rolle_g` → `PO.lage` —, nicht erraten. Fehlt sie,
bleibt der Fakt weg.

**Zweitens: G2 ist damit NICHT erfüllt.** Der Fluss ist BTC-weit; über SEI sagt
er nichts. `mindestkriterien` führt deshalb jetzt `SYMBOLSPEZIFISCH_G` getrennt,
und `pruefe_g` leitet G2 nicht mehr aus G1 ab.

```
vorher:  if not q:                    -> irgendeine Quelle reicht
nachher: if not [n for n in q if n in SYMBOLSPEZIFISCH_G]:
```

> **Ohne diese Änderung hätte ein Symbol ohne Terminmarktdaten G2 durch eine
> Marktgröße erfüllt, die über dieses Symbol nichts aussagt.**

### 58.5 Ein Regressionsfehler in der eigenen Änderung — gefunden beim Nachlesen

`zweite_meinung.rolle_g` bricht ab, wenn `len(fehlt) >= 3` (G5: über nichts
wird nicht gefragt). Meine erste Fassung hängte den ausgefallenen Fluss an
`fehlt` an.

> ⚠️ **Damit hätte eine ZUSÄTZLICHE Quelle die Rolle STILLGELEGT, sobald sie
> ausfällt.** Genau verkehrt herum — und die Simulation lief grün.

Behoben mit einem eigenen Schlüssel `fehlt_rahmen`. **Der Wortlaut wäre
ohnehin falsch gewesen:** `fehlt` erzeugt *„Zu diesem Wert liegt keine Angabe
vor"*, der Fluss beschreibt aber den Rahmen — jetzt *„Zum Gesamtmarkt liegt
keine Angabe vor"*. Verschwiegen wird nichts.

**Gefunden nicht von einem Test, sondern beim Lesen der Aufrufstelle.** Jetzt
steht es als Paketprüfung.

### 58.6 Der Stand der Mindestkriterien

| Gruppe | Quellenarten | G1 | G2 |
|---|---|---|---|
| **Krypto** | **Terminmarkt + On-Chain** | **erfüllt** | **erfüllt** |
| Aktien | — | fehlt | fehlt |
| Rohstoffe | — | fehlt | fehlt |
| Themen-ETF | — | fehlt | fehlt |
| Absicherung | — | fehlt | fehlt |

**Eine von fünf Gruppen steht.** `sperren` bleibt leer — eine scharfe Schranke
legte vier Gruppen still.

### 58.7 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **904, alle bestanden** (6 neue) |
| freie Namen | 0 |
| `pruefe_zahlen_in_prompts.py` | Selbsttest 7/7, 445 Sätze, **kein Befund** |
| `pruefe_phase1.py` | bestanden |
| Simulation | 6 Gruppen, 12 Signale, 14 Mails, **0 Fehler, 0 Lücken** |
| **Ende-zu-Ende-Nachweis** | **12 Rolle-G-Aufrufe mitgeschnitten — 4 Krypto tragen den Fluss, 8 Nicht-Krypto nicht** |
| Gegenprobe Ausfall | `fehlt` bleibt leer, G5 greift nicht, Satz erscheint trotzdem |
| Tagescache | erster Abruf 1,9 s, zweiter 0,04 s |

**Der Ende-zu-Ende-Nachweis war nötig, nicht schmückend.** „0 Fehler" hat Rolle
G drei Tage lang als fertig ausgewiesen, während sie nie lief.

### 58.8 Offen

| | Punkt | Warum nicht jetzt |
|---|---|---|
| 1 | **Persistenz des Flusses** | heute Prozess-Cache; eine neue Tabelle wäre ein Schemaeingriff mitten in der Messkampagne |
| 2 | `cftc_cot.py` an Rolle G (Rohstoffe) | Schritt 3 |
| 3 | `finra.py` + `sec_edgar.py` (Aktien) | Schritt 4 |
| 4 | `funding_rate`/`long_account_pct` unter fremdem Börsenetikett | Kapitel 56.8 |

---

## Kapitel 59 — Schritt 3: COT für Rohstoffe, und eine Tabelle für alle Fremdquellen (16.08.2026)

### 59.1 Die Entscheidung, die der Nutzer delegiert hat

> *„mit Persistenz — ok und entscheide du wegen Cache und Datenbank"*

**Eine generische Tabelle statt drei Einzellösungen.**

```sql
CREATE TABLE externe_reihe (
    quelle, schluessel, datum, wert, geholt_am,
    PRIMARY KEY (quelle, schluessel, datum)
);
```

**Begründung:** COT (wöchentlich), Börsenflüsse (täglich), später Short
Interest (halbmonatlich) und Insiderkäufe haben dieselbe Form — eine Größe je
Datum, von außen geholt, gebraucht wird ihr **Perzentil in der eigenen
Geschichte**. Drei eigene Tabellen wären drei Migrationen, drei Lesefunktionen
und drei Stellen, an denen dasselbe Perzentil anders gerechnet wird.

**UPSERT statt INSERT** — die CFTC revidiert Berichte nachträglich. Ein
`INSERT OR IGNORE` würde die Korrektur verwerfen und dauerhaft den ersten,
falschen Wert führen. Steht als Dauerprüfung.

### 59.2 Das Konstruktionsproblem, das die Architektur bestimmt hat

> ⚠️ **`zweite_meinung.rolle_g` öffnet die Datenbank mit `mode=ro`.**

Persistenz kann dort **nicht** stattfinden. Damit war die Frage nicht *ob*,
sondern *wo* — und die Antwort steht schon im Projekt: `hebel_screening`
schreibt `open_interest_snapshot`, `positionierung` liest nur.

**Also ein Job:** `scheduler/background.py::externe_reihen_job`, täglich 06:35,
also **vor** den Signalläufen. `next_run_time` bootstrapt sofort nach dem
Einspielen, sonst stünde die Tabelle bis zum nächsten Morgen leer.

**Gelesen wird in drei Stufen** — Datenbank, Prozessspeicher, Netz:

| Stufe | wofür |
|---|---|
| **Datenbank** | der Normalfall im Betrieb |
| Prozessspeicher | Läufe ohne Job: Simulation, Messskripte, erster Start |
| Netz | höchstens einmal je Prozess und Kalendertag |

**Gemessen:** Job schreibt 2.072 Punkte in 4,6 s. Danach liest Rolle G in
**0,06 s mit null Netzabrufen.**

> **Ohne Stufe 1 hinge jedes Urteil unmittelbar am Netz** — und ein Signal ohne
> Gegenprüfung sieht aus wie eines, das sie bestanden hat.

### 59.3 Die Messung hat wieder die Größe gewählt

Anteil der Wochen mit Extremwert (Perzentil ≥90 oder ≤10), 156-Wochen-Fenster:

| | Gold | Silber | Kupfer | Erdgas |
|---|---:|---:|---:|---:|
| **Long-Anteil am OI** | **50 %** | **15 %** | **4 %** | **35 %** |
| Netto Managed Money | 63 % | 39 % | 41 % | 21 % |

**Der Anteil gewinnt** — er ist bereits normiert, während die Nettoposition an
der absoluten Marktgröße hängt und mit ihr wandert. Dieselbe Überlegung, aus
der `positionierung.py` nur OI-**Änderungen** vergleicht und keine Niveaus.

**Fenster 156 Wochen (drei Jahre).** Die Länge ändert die Extremhäufigkeit
kaum — 104/156/208 Wochen ergeben Gold 35/50/44 %, Silber 20/15/13 %, Kupfer
7/4/6 %, Erdgas 33/35/38 %. Entschieden hat deshalb nicht die Extremrate,
sondern dass drei Jahre einen Rohstoffzyklus decken und alle vier Märkte sie
tragen (Kupfer und Erdgas haben 236 Berichte).

> **Golds Häufung ist eine Markteigenschaft, kein Mangel der Größe.** Der
> aktuelle Wert steht beim 58. Perzentil; die Verteilung nutzt den vollen
> Bereich. Anders als MVRV in Kapitel 58, das an einem Ende klebte.

### 59.4 Ein Fehler, der tadellos aussah

**Die erste Fassung meldete für Gold und Silber den Bericht vom 2014-02-04** —
mit einem einwandfreien 46. Perzentil.

```
$order: ASC + $limit: 400   ->  die AELTESTEN 400 Berichte
```

Gold und Silber tragen mehr als 400 Zeilen; Kupfer und Erdgas haben nur 236 und
waren deshalb **zufällig richtig** — was den Fehler beinahe verdeckt hätte.

> **Die Messung, die das Fenster festgelegt hat, benutzte `DESC`.** Dieselbe
> Abfrage, andere Daten. *„Immer an der Quelle prüfen"* gilt auch für die eigene
> Messung von vor zehn Minuten.

Golds Perzentil springt nach der Korrektur von 46 auf **58**.

### 59.5 Der Satz

```
Die US-Aufsicht meldet woechentlich, wie stark die grossen spekulativen Fonds
  auf der Kaufseite stehen - im Terminmarkt des Basiswerts, nicht in diesem
  Zertifikat.
Im Bericht vom 2026-08-11 steht dieser Anteil im 58. Perzentil der letzten
  156 Wochenberichte - im gewohnten Bereich.
```

**Der Basiswert wird ausdrücklich genannt.** Wir halten WisdomTree-Zertifikate,
die Behörde misst den Future an der COMEX — nah genug, um etwas zu sagen, aber
nicht dasselbe Instrument. Wer das verschweigt, lässt das Modell glauben, es
lese eine Aussage über unser Papier.

**Erste Fassung des Einleitungssatzes endete auf *„einen Teil der offenen
Kontrakte auf der Kaufseite"*** — grammatisch tadellos und ohne Information.
Ersetzt.

### 59.6 Der Stand — ehrlich

| Gruppe | Quellenarten | G1 (zwei Arten) | G2 (symbolspezifisch) |
|---|---|---|---|
| **Krypto** | Terminmarkt + On-Chain | **erfüllt** | **erfüllt** |
| **Rohstoffe** | **COT** | **fehlt** (1 von 2) | **erfüllt** |
| Aktien | — | fehlt | fehlt |
| Themen-ETF | — | fehlt | fehlt |
| Absicherung | — | fehlt | fehlt |

> **Schritt 3 hat Rohstoffe von null auf eine Quelle gebracht, nicht auf zwei.**
> COT ist eine Informationsart; G1 verlangt zwei. Das ist kein Versäumnis des
> Schritts, sondern der Umfang, den eine Quelle hat.

**Die zweite Art für Rohstoffe wäre `api/eia.py`** — Erdgas-Lagerbestände, also
physische Bestände statt Positionierung. Sie deckt aber **nur Erdgas**; für
Gold, Silber und Kupfer ist keine kostenlose zweite Art bekannt. Und EIA
braucht als einzige unserer Quellen einen Schlüssel.

### 59.7 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **910, alle bestanden** (6 neue) |
| freie Namen | 0 |
| `pruefe_zahlen_in_prompts.py` | Selbsttest 7/7, 445 Sätze, kein Befund |
| `pruefe_phase1.py` | bestanden |
| Simulation | 6 Gruppen, 12 Signale, 14 Mails, **0 Fehler, 0 Lücken** |
| **Ende-zu-Ende** | **12 Rolle-G-Aufrufe — OD7H und OD7C tragen COT, 4 Krypto den Fluss, 6 andere nichts** |
| Persistenz | Migration auf Bestands-DB, 2.072 Punkte, Revision schlägt durch |
| Netzentkopplung | mit gefüllter Tabelle **null** Abrufe |

> ⚠️ **Zwei eigene Fehler in den neuen Prüfungen.** Die Schritt-2-Prüfung hing
> am Namen `_fluss_reihe`, den Schritt 3 umbenannt hat — sie prüft jetzt den
> **Netzabruf** selbst, also die Stelle, an der der Sachverhalt heute entsteht.
> Und mein Testbestand hatte 48 Punkte bei `COT_MINDESTREIHE = 60`: **die
> Eingabe stellte den Fall nicht her, den sie prüfen wollte** — zum fünften Mal
> diese Woche.

### 59.8 Offen

| | Punkt | |
|---|---|---|
| 1 | zweite Art für Rohstoffe | EIA deckt nur Erdgas, braucht einen Schlüssel |
| 2 | `finra.py` + `sec_edgar.py` an Rolle G | Schritt 4, Aktien |
| 3 | Themen-ETF und Absicherung | **keine kostenlose Quelle bekannt** (Kap. 57) |
| 4 | `funding_rate`/`long_account_pct` unter fremdem Börsenetikett | Kap. 56.8 |

---

## Kapitel 60 — Schritt 4: Aktien, und eine Sperre, die wir selbst ausgelöst haben (16.08.2026)

### 60.1 Zwei Quellen, zwei sehr verschiedene Qualitäten — gemessen

**Eindeckungsdauer (FINRA): stark.**

| | Meldeperioden | ab | `days_to_cover` fehlt |
|---|---:|---|---:|
| PLTR | 140 | 2020-10-15 | **0** |
| VST | 207 | 2017-12-29 | **0** |

Der Wert ist **bereits normiert** — Leerverkaufsposition geteilt durch
Tagesumsatz. Genau die Form, die R-T5 verlangt, und dieselbe Überlegung, aus
der COT den Long-*Anteil* nimmt und nicht die Nettoposition. **Ein Abruf je
Symbol.**

**Insidergeschäfte (SEC Form 4): schwach als Perzentil, brauchbar als Zählung.**

Gemessen über 730 Tage: **PLTR 572 Transaktionen, davon 3 Käufe. VST 9
Transaktionen, davon 0 Käufe.**

> Ein Satz über Insider*käufe* hieße fast immer „keine" — ein konstantes Feld
> (R-T6), dieselbe Absage wie an MVRV in Kapitel 58.

**Was bleibt, ist die Zählung** beider Seiten. Sie schwankt und steht in keiner
Kursreihe.

**Kein Volumen-Perzentil**, obwohl es die bessere Größe wäre: PLTRs monatliches
Verkaufsvolumen schwankt um das **13,2-fache**. Aber es gibt nur 18
Monatspunkte, und dafür müssten je Symbol rund 120 Filings einzeln geholt
werden. Vermerkt als offener Punkt.

### 60.2 Die Sperre — und was sie über das Fehlerverhalten verriet

Beim Messen dieses Volumens machte ein Lauf **rund 120 Abrufe in vier
Sekunden**, etwa 30 je Sekunde bei einem SEC-Limit von zehn.

```
429 Too Many Requests   (Server: AkamaiGHost, kein Retry-After)
```

**Die Sperre hielt über eine Viertelstunde** und traf jeden weiteren Abruf,
auch die Tickerliste.

> ⚠️ **Der Schaden wäre still gewesen.** `get_recent_insider_transactions`
> fängt jeden Filing-Fehler EINZELN ab, damit ein kaputtes Filing die anderen
> nicht blockiert — richtig gedacht. Bei einer Sperre scheitern aber **alle**,
> und die Funktion gibt eine leere Liste zurück: ununterscheidbar von „dieser
> Wert hat keine Insider-Aktivität". **Ein gesperrter Abruf hätte als Tatsache
> im Prompt gestanden.**

**Der Modulkopf hatte es sogar begründet:** *„bei unserem Nutzungsmuster nie
annähernd erreicht, daher kein eigener Rate-Limiter nötig."* Das stimmte für
`max_filings=5`. **Die Annahme galt für eine Nutzung, nicht für die
Schnittstelle** — und sie stand fast einen Monat unwidersprochen im Code.

**Drei Änderungen:**

| | |
|---|---|
| `_im_takt()` | prozessweiter Begrenzer, **8 statt 10** je Sekunde, vor allen drei Abrufstellen |
| `SecGesperrtError` | eigene Klasse — eine Drosselung ist **kein** „keine Daten" |
| Job meldet laut | bei Sperre wird **nichts** geschrieben; der gestrige Stand ist ehrlicher als eine frisch datierte Null |

**Live nachgewiesen, beide Richtungen:** während der Sperre meldete der Job
*„SEC gesperrt, Insiderzahlen für PLTR NICHT aufgefrischt"* und schrieb nichts;
nach dem Ablauf lief er **live in 14 Sekunden** durch, ohne erneute Sperre.

### 60.3 Der Fakt liest, holt aber nie

**`_insider()` macht keinen einzigen Netzabruf** — anders als alle übrigen
Quellen. Grund ist genau die Drosselung: ein Form-4-Abruf sind mehrere Anfragen
je Symbol, und bei einer Sperre gäbe es keine leere, sondern eine **falsche**
Antwort. Geschrieben wird ausschließlich im Job.

> Sichtbar in der Simulation: dort steht bei PLTR und VST nur
> `short_interest`, weil der Job gegen die Simulationskopie nie lief. **Das ist
> das gewünschte Verhalten**, nicht ein Ausfall.

### 60.4 Zwei Fehler im Satz, beide inhaltlich

**Erstens verschwieg er die Kaufseite**, wenn sie null war:

```
vorher:  Bei den Insidern haben in den letzten 90 Tagen 55 verkauft.
nachher: Insider meldeten in den letzten 90 Tagen keinen Kauf und
         55 Verkaeufe am offenen Markt - Zuteilungen und
         Optionsausuebungen zaehlen nicht mit.
```

**Genau die Null ist die Aussage.** „55 Verkäufe" allein liest sich wie eine
Hälfte, deren andere jemand vergessen hat.

**Zweitens zählte er Geschäfte und nannte sie Personen.**
`summarize_insider_activity` zählt Transaktionen; mein Schlüssel hieß
`insider_verkaeufer`. Bei PLTR waren es **55 Geschäfte von acht Personen**.
Schlüssel und Satz sagen jetzt beide *Geschäfte*.

*(Dazu zwei Grammatikfehler aus einer selbstgebauten Mehrzahl — „kein Kauf"
statt „keinen Kauf", „Verkaufe" statt „Verkaeufe". Ein Faktensatz, der
holpert, liest sich wie ein Fehler.)*

**Und keine Deutung.** Dass Insiderverkäufe ein schlechtes Zeichen seien, ist
die gängige Lesart und falsch verkürzt: Führungskräfte bekommen Aktien als
Vergütung und verkaufen sie planmäßig. `sec_edgar.py` sagt das im Modulkopf
selbst. **Gezählt wird, gedeutet nicht** — steht als Prüfung.

### 60.5 Das Monitoring auf der Remoteseite

> **Nutzervorgabe:** *„vergiss auch nicht für alle Neuanbindungen die du heute
> gemacht hast, API etc., diese auch in das Monitoring auf der Remoteseite zu
> berücksichtigen."*

**Die API-Gesundheit war bereits abgedeckt** — `@track_api_health` steht an
allen vier Quellen, und `api_health_status` führt `coinmetrics`, `cftc_cot`,
`finra` und `sec_edgar` seit Juli. Die neue Nutzung läuft durch dieselben
Dekoratoren.

**Was fehlte, ist die Frage, die im Betrieb zählt: sind die Reihen aktuell?**
Dafür der neue Exportabschnitt `_externe_reihen`:

```
abdeckung : krypto=onchain · rohstoffe=cot · aktien=finra+sec_edgar
            themen_etf/absicherung = keine kostenlose Quelle bekannt
veraltet  : (Liste, Schwelle 48 h)
reihen    : je Quelle/Schluessel Punkte, Zeitraum, ABRUF-Alter
```

**Gemeldet wird das Alter des ABRUFS, nicht des jüngsten Punktes.** Ein
COT-Bericht ist zwischen zwei Freitagen bis zu sieben Tage alt, ohne dass etwas
fehlt; die Frage ist, wann wir zuletzt **nachgesehen** haben.

> Der Export prüft sich selbst: Tabellen, die er nicht kennt, meldet er unter
> `nicht_erwaehnt`. `externe_reihe` wäre dort aufgetaucht — die Selbstprüfung
> hat funktioniert.

### 60.6 Der Stand

| Gruppe | Quellenarten | G1 | G2 |
|---|---|---|---|
| **Krypto** | Terminmarkt + On-Chain | **erfüllt** | **erfüllt** |
| **Aktien** | **Leerverkäufer + Insider** | **erfüllt** | **erfüllt** |
| Rohstoffe | COT | fehlt (1 von 2) | **erfüllt** |
| Themen-ETF | — | fehlt | fehlt |
| Absicherung | — | fehlt | fehlt |

**Aktien sind die einzige Gruppe, deren beide Quellen symbolspezifisch sind** —
G1 und G2 aus einer Hand. Bei Krypto trägt G2 allein der Terminmarkt.

**Zwei von fünf Gruppen stehen vollständig.** `sperren` bleibt leer.

### 60.7 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **917, alle bestanden** (7 neue) |
| freie Namen | 0 |
| `pruefe_zahlen_in_prompts.py` | Selbsttest 7/7, 445 Sätze, kein Befund |
| `pruefe_phase1.py` | bestanden |
| Simulation | 6 Gruppen, 12 Signale, 14 Mails, **0 Fehler** |
| **Job live** | **14 s inkl. SEC, keine Sperre**, PLTR und VST auf G1+G2 |
| Sperrfall live | Job meldet laut, schreibt nichts, Fakt sagt „keine Angabe" |
| Exportabschnitt | Abdeckung, Veraltung, Abruf-Alter — gegen echte Daten gerendert |

### 60.8 Offen

| | Punkt | |
|---|---|---|
| 1 | Volumen-Perzentil für Insider | 18 Monatspunkte, ~120 Filings je Symbol |
| 2 | zweite Art für Rohstoffe | EIA deckt nur Erdgas, braucht einen Schlüssel |
| 3 | Themen-ETF und Absicherung | **keine kostenlose Quelle bekannt** (Kap. 57) |
| 4 | `funding_rate`/`long_account_pct` unter fremdem Börsenetikett | Kap. 56.8 |

---

## Kapitel 61 — Das Regime raus, der Anker je Gruppe, und warum kein Wächter angeschlagen hat (16.08.2026 abends)

### 61.1 Der Fund kam aus einer Mail, nicht aus einer Messung

**Nutzerfrage:** *„warum haben wir das Regime hier angeführt — haben wir damit
nicht bereits eine LLM-Bewertung auf nur eine Seite gezwungen?"*

**Die Antwort stand in seiner eigenen Signalmail vom 17:39:**

```
EINWAND - die Positionierung spricht dagegen: Der Gesamtmarkt steht
im Regime 'baer', seit 27 Tagen ununterbrochen.
```

**Das Modell griff aus sechs Faktensätzen genau den EINEN heraus, der ein
Urteil enthält, und gab ihn als Begründung zurück** — während jeder echte
Positionierungsfakt daneben *„im gewohnten Bereich"* sagte. Die Gegenprüfung
stand damit nicht auf der Positionierung, sondern auf einem Etikett, das wir
selbst gerechnet und selbst hineingelegt hatten.

**Nachgezählt am Produktionsbestand:**

| Tabelle | Zeilen mit Regime | verschiedene Werte |
|---|---:|---:|
| `signals` | 2.549 | **1** (`baer`) |
| `hebel_signals` | 1.819 | **1** (`baer`) |

**Vier eigene Regeln auf einmal verletzt:**

| | |
|---|---|
| **R-T2** | ein Etikett statt eines beschriebenen Sachverhalts |
| **R-T3** | ein Werturteil, dem Prüfer fertig hingelegt |
| **R-T6** | ein konstantes Feld |
| **P3** | aus BTC-Kurs und Fear & Greed gerechnet — beides sieht Rolle A bereits; **unsere** Ableitung, keine fremde Information |

**Und die ursprüngliche Begründung war längst entfallen.** Sie stand wörtlich
im Modulkopf: das Regime sei nötig, *„weil sie sonst nur eine Quelle hätte"*.
Seit heute hat Krypto Terminmarkt **und** On-Chain, Aktien Leerverkäufer
**und** Insider. **Der Grund war weg, das Feld war geblieben.**

### 61.2 Der Fehler ist aktenkundig — seit Wochen

`szenario_fakten.finde_konstanten` trägt ihn im Docstring:

> `regime` war auf allen 1.022 Fällen „baer" — der Gegenprüfer las eine
> Konstante mit Richtungsaussage und kam deshalb **1 von 1.022 Mal** auf LONG.

**Derselbe Feldname, dieselbe Wirkung, dieselbe Rolle.** Ich habe ihn am
16.08. wieder eingebaut.

**Warum kein Wächter angeschlagen hat:** `enthaelt_werturteile` und
`finde_konstanten` prüfen **Feldnamen in einem dict**. Rolle G bekommt
**Sätze**. Der Wächter konnte es strukturell nicht sehen.

> **Dieselbe Lücke wie heute Vormittag zwischen
> `pruefe_fakten_bezugsgroessen` (Felder) und `pruefe_zahlen_in_prompts`
> (Sätze) — zum zweiten Mal an einem Tag, und beim zweiten Mal hat sie
> gekostet.**

### 61.3 Der Prüfauftrag, nachgeschärft

`pruefe_zahlen_in_prompts.py` prüft jetzt fünf Formen statt drei:

| | | |
|---|---|---|
| N1 | Rechenaufgabe | zwei Werte UND ihr Abstand (R-T10) |
| N2 | ungedeckte Zahl | kein Fenster, kein Bezug (R-T1/R-T5) |
| N3 | ohne Einordnung | Perzentil ohne Wort dazu (R-T11) |
| **N4** | **Etikett** | **ein fertiges Urteil (R-T2/R-T3)** |
| **N5** | **Konstante** | **bei fast jedem Symbol wortgleich (R-T6)** |

**Der Selbsttest trägt den echten Mailsatz als Positivprobe** — und einen
beschriebenen Sachverhalt derselben Art als Gegenprobe, damit N4 nicht jede
Richtungsangabe meldet. **9 von 9.**

> ⚠️ **Und der Prüfer hatte selbst eine Lücke:** er rief `lage()` **ohne
> Assetklasse** auf und sah damit nur den Terminmarkt — ausgerechnet die
> Sätze, die heute dazugekommen sind, waren unsichtbar. Behoben; er rendert
> jetzt je Gruppe.

### 61.4 Was N5 sofort gefunden hat — und was es bedeutet

```
12/12  [G/krypto] Am 2026-08-15 flossen mehr Bitcoin auf die Boersen
                  als von ihnen herunter.
```

**Der Börsenfluss aus Schritt 2 ist über alle Kryptosymbole wortgleich** — er
ist BTC-weit. Damit teilt er eine Eigenschaft mit dem Regime, das gerade
entfernt wurde.

**Der Unterschied, und er ist real, aber schmaler als mir lieb ist:**

| | Regime | Börsenfluss |
|---|---|---|
| Herkunft | **unsere** Ableitung | fremde Messung (CoinMetrics) |
| Form | **Etikett** (`'baer'`) | beschriebener Vorgang |
| Deutung im Satz | Richtung eingebaut | **keine** |
| über Symbole | konstant | konstant |

**Offen zur Entscheidung, nicht eigenmächtig geändert.** Die gängige Lesart
„Zuflüsse = Verkaufsdruck" steht nicht im Satz, kann aber im Modell entstehen —
und dann schiebt sie jedes Kryptourteil in dieselbe Richtung.

### 61.5 Die drei Formulierungen aus der Mail

| vorher | nachher |
|---|---|
| `um 0.0 % gefallen` | `praktisch unveraendert geblieben` |
| `67 % der Konten stehen long; das ist das 0. Perzentil - aussergewoehnlich wenige` | `Der Anteil der Konten auf der Kaufseite steht im 82. Perzentil … - im gewohnten Bereich` |
| `uneinheitlich` bei Spanne im **7. Perzentil** | `weitgehend gleichlaeufig`, sobald das Perzentil unten liegt |

**Alle drei sagten mehr, als der Messwert hergab** — eine Richtung bei null,
eine rohe Zahl neben ihrer eigenen Widerlegung, ein Wort gegen sein Perzentil.

### 61.6 Der Ankertag — vier von sechs Gruppen standen still

**Aus dem NB-Export vom 16.08., nach dem Neustart um 17:15:**

| Gruppe | Ankertag | fakten (bestanden, verloren) | Signale |
|---|---|---|---:|
| krypto/hebel | 2026-08-16 | 41, 0 | **16** |
| krypto/spot | 2026-08-16 | 13, 0 | 1 |
| aktien/spot | 2026-08-16 | **0, 2** | 0 |
| hedge | 2026-08-16 | **0, 2** | 0 |
| rohstoffe | 2026-08-16 | **0, 4** | 0 |
| themen_etf | 2026-08-16 | **0, 5** | 0 |

**Der 16.08. war ein Samstag.** Krypto handelt durchgehend, die Börsen nicht.

**Die Ursache:** `rollen_job` übergibt **alle** Kursreihen — Lagebild und
Gleichlauf brauchen sie, denn sie beschreiben den gesamten Markt. `symbole`
ist dagegen auf die Gruppe gefiltert. **Der Ankertag wurde über alle sechzig
gerechnet:** 41 Kryptoreihen mit Samstagskerze sind 68 % und reißen die
60-%-Schranke — also ankerte auch der Aktienlauf auf einem Tag, an dem keine
seiner Reihen einen Kurs hat.

> **Der Docstring von `_ankertag` beschreibt genau diesen Fehler, eine Ebene
> tiefer:** *„EIN einziges Symbol setzt den Anker für alle."* Dass er auch
> zwischen **Assetklassen** auftritt, ist niemandem aufgefallen, weil `reihen`
> ungefiltert durchgereicht wird.

**Behoben chirurgisch:** nur `_ankertag` rechnet über die Reihen der Gruppe;
Lagebild und Gleichlauf bekommen weiterhin alle.

**Nachgestellt und belegt** — die Zahlen decken sich Zeile für Zeile mit dem
Produktionslog:

| Gruppe | Anker alt | Anker neu | ALT hätte verloren | Log |
|---|---|---|---|---|
| aktien | 16.08. | **14.08.** | 2 von 2 | `(0, 2)` ✓ |
| hedge | 16.08. | **14.08.** | 2 von 2 | `(0, 2)` ✓ |
| rohstoffe | 16.08. | **14.08.** | 4 von 4 | `(0, 4)` ✓ |
| themen_etf | 16.08. | **14.08.** | 5 von 5 | `(0, 5)` ✓ |
| krypto | 16.08. | 16.08. | — | 16 Signale ✓ |

> ⚠️ **Und der erste Versuch, es zu belegen, ging daneben:** das NB-Backup
> endet überall am 14.08. und enthält die Samstagskerzen nicht. **Die Eingabe
> stellte den Fall nicht her** — zum sechsten Mal diese Woche. Erst
> nachgestellte Samstagskerzen für die 41 Kryptoreihen zeigten ihn.

### 61.7 Was der Export sonst noch sagte

| | |
|---|---|
| Neue Reihen | **alle zehn da**, `veraltet: []`, Abruf 0,0 h alt |
| Abdeckung | krypto=onchain · rohstoffe=cot · **aktien=finra+sec_edgar** |
| API-Gesundheit | alle vier Quellen mit Erfolg um 15:33–15:34 UTC |
| Jobläufe | **zwei App-Starts** (17:15:55 und 17:33:06); der erste schrieb 2.072 Punkte ohne Aktiendaten, der zweite 2.423 mit |
| SEC | keine Sperre am Notebook |
| Selbstprüfung | `nicht_erwaehnt: ["job_laeufe"]` — kleiner offener Punkt aus früherer Arbeit |

### 61.8 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **916, alle bestanden** — zwei Regime-Zusicherungen sind zur **Gegenwache** geworden |
| freie Namen | 0 |
| `pruefe_zahlen_in_prompts.py` | **Selbsttest 9/9**, 344 Sätze je Assetklasse, kein Befund |
| `pruefe_phase1.py` | bestanden |
| Simulation | 6 Gruppen, 12 Signale, 14 Mails, **0 Fehler** |

**Aus einer gelöschten Prüfung wird nichts gelernt.** Die beiden Zusicherungen,
die das Regime verlangten, prüfen jetzt das Gegenteil: dass es nicht
zurückkommt.

---

## Kapitel 62 — Warum ein Fakt nicht in zwei Rollen stehen kann, und wo der Börsenfluss hingehört (16.08.2026 abends)

**Nutzerfrage:** *„warum kann dieser Fakt nicht in A und G sein — welche Regel
spricht dagegen? … gibt es einen fachlich sachlichen Grund, diesen Parameter in
Rolle A umzuhängen oder doch eher bei G lassen — bewerte, wie wertvoll er vom
Inhalt ist. Ist er hoch, dann umhängen zu A; wenn nicht, dann zur Gegenprüfung."*

**Beides beantwortet, und die zweite Antwort korrigiert meine eigene Empfehlung
vom selben Abend.**

### 62.1 Warum nicht beides — der Mechanismus, nicht die Vorschrift

**Alles, was in Rolle A steht, erreicht Rolle BC.** Nachgesehen im Code, nicht
angenommen:

```python
# agent/rollen_lauf.py:799
bc_ein["marktlage_beurteilung"] = {"lage": lagebild["lage"], ...}
```

Das Lagebild ist die **Antwort** der Rolle A und wird als Beurteilung in die
Eingabe der Rolle BC gelegt (`rollen_eingabe.baue_befund_eingabe`, Zeile 220 ff.).

**Daraus folgt zwingend:**

| Fakt steht in | BC weiß ihn | G hat etwas, das BC fehlt |
|---|---|---|
| nur A | **ja** | nein |
| nur G | nein | **ja** |
| **A und G** | **ja** | **nein** |

> **Steht ein Fakt in beiden, ist die zweite Stufe an dieser Stelle keine
> Gegenprüfung mehr, sondern eine zweite Lesung derselben Information.**

**Und genau das war der Zustand, den der Umbau beseitigt hat.** Rolle G bekam
früher denselben Faktentext wie BC — Ergebnis: **17 × LONG in 2.469 Prüfungen.**
Ein Prüfer ohne eigene Grundlage bestätigt.

**Die Literatur sagt dasselbe, und sie ist der Grund für R-R2:**

- teilen zwei Prüfer Modell **und** Informationsgrenze, bildet die Debatte ein
  **Martingal** — sie fügt im Erwartungswert nichts hinzu
- LLM-Fehler korrelieren zu **über 60 %**
- was hilft, ist ausschließlich **konstruierte Informationsasymmetrie**

**R-R2 ist damit keine Ordnungsvorschrift, sondern die Umsetzung dieses
Mechanismus.** „Ein Parameter gehört zu genau einem Modell" heißt: die
Asymmetrie wird gebaut, nicht gehofft.

> **Die Nutzerformulierung trifft es exakt:** *„unabhängige Quelle, 2× dieselbe
> Information."* Zwei Quellen sind es nur, solange sie nicht beide dasselbe
> Modell erreichen.

### 62.2 Der Wert des Börsenflusses — auf unserer eigenen Leiter

**P2, Eignungsleiter:**

| Rang | | Börsenfluss |
|---|---|---|
| 1 | **bei uns gemessen** | **nein** |
| 2 | in der Praxis angewendet | **ja** — Börsenzuflüsse sind Standardwerkzeug der Kryptoanalyse |
| 3 | Vermutung | besser als das |

**Rang 2, bei uns unbelegt.**

**Gemessen ist nur seine Streuung** (Kapitel 61.4), nicht seine Wirkung:

| | |
|---|---|
| verschiedene Aussagen über 365 Tage | **4** |
| häufigste Einzelaussage | 48 % |
| Richtungsverteilung | Abfluss 57 % / Zufluss 43 % |
| Extremtage | 18 % |

**Er unterscheidet zwischen Tagen — ob er dabei etwas Richtiges unterscheidet,
weiß niemand.**

### 62.3 Die Nutzerregel, angewandt

> *„ist er hoch, dann umhängen zu A; wenn nicht, dann zur Gegenprüfung G"*

**Die Regel ist gut, und sie hat einen Grund, den sie nicht ausspricht:**

**Rolle G ist einseitig gebaut.** Sie kann nur einwenden, nie befürworten —
*„sie entscheidet nichts; der Einwand steht in der Mail und in der Zeile, er
kippt die Empfehlung nicht"* (Nutzervorgabe 29.07., unverändert).

**Rolle A dagegen wirkt in beide Richtungen**, weil ihr Lagebild in BCs
Entscheidung eingeht.

> **Daraus folgt die Regel von selbst:** ein Fakt mit **belegtem** Wert gehört
> dorthin, wo er in beide Richtungen wirken darf. Ein Fakt mit **unbelegtem**
> Wert gehört in den Kanal, der nur eine Fahne setzt, die ein Mensch liest.

**Rang 2 ist nicht Rang 1. Also G.**

### 62.4 Zwei Sachargumente, die ich zu schwach gewichtet hatte

**Erstens: Börsenflüsse SIND Positionierung.** Münzen, die auf eine Börse
wandern, liegen dort, wo man sie verkaufen kann. Das ist keine Marktstimmung,
sondern die aggregierte Aufstellung der Halter — Rolle Gs erklärter Auftrag.

**Mein Argument „marktweit ⇒ gehört zu A" war zu grob.** Auch die
Terminmarktdaten sind Marktaggregate; sie sind nur je Symbol erhoben. Die
Trennlinie verläuft nicht zwischen *einzeln* und *marktweit*, sondern zwischen
**Positionierung** (G) und **Marktlage** (A).

> **Das Regime war kategorial etwas anderes:** ein Bewertungs**etikett**, keine
> Messung. Es fiel nicht wegen seiner Marktweite heraus, sondern weil es ein
> fertiges Urteil war — und über 2.549 von 2.549 Fällen dasselbe.

**Zweitens: in Rolle A wäre er eine SECHSTE Dimension** neben Trend,
Volatilität, Liquidität, Makro und Stimmung. Das ist eine eigene
Aufnahmeentscheidung durch P1–P7, kein Umhängen.

### 62.5 Entscheidung

**Der Börsenfluss bleibt in Rolle G.** Nichts zu ändern.

> ⚠️ **Das korrigiert meine Empfehlung von wenige Minuten zuvor** („umhängen
> nach Rolle A"). Sie stand auf dem Argument „marktweit gehört zum Rahmen" —
> und das ist genau die Begründung, mit der ich am selben Tag das **Regime** in
> Rolle G gerechtfertigt hatte. Ein Argument, das zwei entgegengesetzte
> Platzierungen stützt, trägt keine von beiden.

### 62.6 Was offen bleibt — und wie es entschieden wird

| | |
|---|---|
| **Konstanz im Lauf** | er ist über alle Kryptosymbole wortgleich, kann also nur alle gemeinsam schieben. Bei einem Positionierungsaggregat vertretbar — sichtbar über **N5** |
| **G2 hängt allein am Terminmarkt** | der Fluss deckt G1, nie G2. So im Code kodiert (`SYMBOLSPEZIFISCH_G`) |
| **die eigentliche Frage** | **Einwandrate gegen Fluss-Perzentil**, sobald Rolle G genug Läufe hat |

**Und die Messung entscheidet in beide Richtungen:**

- trägt er (**Rang 1**) → er gehört in den Hauptpfad, also nach A
- unterscheidet er nichts → er fliegt ganz raus, nicht nur um

> **Damit ist die Platzierung kein Dauerurteil, sondern der Stand bis zur
> ersten Messung.**

### 62.7 Die Regel, die daraus folgt

**R-R6** (neu): *Ein Fakt steht in genau einer Rolle — und welche, entscheidet
sein Belegstand, nicht seine Nützlichkeit.*

| Belegstand | Kanal | Begründung |
|---|---|---|
| **Rang 1** (gemessen) | **A / BC** | darf in beide Richtungen wirken |
| **Rang 2** (Praxis) | **G** | setzt nur eine Fahne, die ein Mensch liest |
| **Rang 3** (Vermutung) | **gar nicht** | nicht aufnahmefähig (P2) |

**Nie in beiden.** A erreicht BC — ein Fakt in A und G ist ein Fakt, den der
Prüfer und der Geprüfte teilen, und dann prüft niemand mehr.

---

## Kapitel 63 — Wohin die Nachrichten gehören: eine Gabelung, die niemand geschlossen hat (16.08.2026 abends)

**Nutzerhinweis:** *„was ist mit der Nachrichtenschiene für die LLMs — hätte
diese eher im primären LLM gesehen, aber aktuell nicht bewertbar."*

**Der Hinweis hat einen Widerspruch aufgedeckt, der tiefer liegt als eine
Formulierung.**

### 63.1 Drei Aussagen, zwei Antworten

| Stelle | sagt | Datum |
|---|---|---|
| `positionierung.py` Modulkopf | Nachrichten gehören **zu Rolle G** | 16.08. früh |
| Umbauplan ~Kap. 39 | *„Rolle C sollte die **Nachrichten- und Katalysator-Rolle** sein, nicht die Zahlen-Rolle"* | 15.08. |
| Kapitel 55.3 | „Katalysator / Nachrichten" steht unter den **BC-Lücken** | 16.08. |

**Zwei gegen eine — und die Mehrheit lag falsch.**

### 63.2 Es war keine Unachtsamkeit, sondern eine nicht geschlossene Gabelung

**Die Planstelle hatte eine Voraussetzung**, die im selben Absatz steht:

> *„Die Positionierungsfakten werden **deterministische Einwände** im
> Faktentext — sichtbar für B, ohne zusätzlichen Aufruf."*

**Der Gedanke war schlüssig:** wenn die Zahlen ohnehin als Regel gerechnet
werden können, soll das zweite Modell das tun, was nur ein Modell kann —
Sprache lesen. Dann wäre G die Nachrichtenrolle.

> ⚠️ **Diese Gabelung wurde nicht genommen.** Gebaut wurde am 16.08. das
> Gegenteil: Rolle G ist die **Positionierungsrolle mit eigenen Quellen** —
> Terminmarkt, On-Chain, COT, Leerverkäufer, Insider (Kapitel 55–60).

**Mit der Voraussetzung entfällt die Folgerung.** Der Satz blieb trotzdem
stehen, und ein zweiter, davon abgeleiteter Satz wanderte in einen Modulkopf —
also genau dorthin, wo jemand ihn liest, **bevor** er baut.

### 63.3 Wohin sie gehören: zu BC

**Der entscheidende Grund ist die Einseitigkeit, die R-R6 festhält.**

**Rolle G kann nur einwenden, nie befürworten** — *„sie entscheidet nichts; der
Einwand kippt die Empfehlung nicht"* (Nutzervorgabe 29.07., unverändert).

> **Ein Katalysator, der ausschließlich vetieren kann, ist keiner.** Eine gute
> Quartalszahl könnte in Rolle G nichts bewirken, eine schlechte alles. Die
> Hälfte der Information ginge verloren, und zwar systematisch dieselbe.

**Dazu die Systematik selbst:** in der CSTI-Gliederung ist die Nachricht der
**Trigger** — der Grund, warum ein Setup *jetzt* handelbar wird. Das ist Teil
des Einstiegs, nicht seiner Prüfung.

### 63.4 Wo R-R6 nicht greift — und was daraus folgt

**Nach Belegstand wäre die Antwort G.** Die Ablationsstudie ist externe
Literatur, also P2 **Rang 2**, und R-R6 schickt Rang 2 in den einseitigen Kanal.

**Hier greift die Regel nicht, und der Grund ist kategorial:**

| | beschreibt | Beispiel |
|---|---|---|
| alles bisher Platzierte | einen **Zustand** | „der Anteil steht im 82. Perzentil" |
| eine Nachricht | ein **Ereignis** | „die Quartalszahlen liegen vor" |

**Ein Zustand kann geprüft werden. Ein Ereignis ändert die Fakten, statt eine
zu sein.** R-R6 ordnet Zustandsbeschreibungen; für Ereignisse entscheidet die
Wirkrichtung, und die verlangt einen zweiseitigen Kanal.

**R-R6 trägt diesen Zusatz jetzt.**

### 63.5 Warum sie trotzdem nicht bewertbar ist — der Nutzer hat recht

**Erstens: es gibt keine Quelle.** Kein einziger Nachrichten-Client im Projekt.
Und für unser gemischtes Universum — 43 Kryptowerte, 2 US-Aktien, europäische
ETFs, WisdomTree-Zertifikate — ist keine kostenlose Quelle offensichtlich.

**Zweitens: ohne Verdrahtung kein gepaarter Vergleich**, also keine Messung.

**Drittens, und das ist der harte Teil:**

> ⚠️ **Eine Schlagzeile ist von Natur aus ein Etikett.** *„Unternehmen
> übertrifft Erwartungen"* **ist** ein fertiges Urteil — genau das, was am
> selben Abend als Regime aus Rolle G geflogen ist (R-T2, R-T3, R-T12).

Sie in eine beschreibende Form zu übersetzen ist selbst eine Modellleistung.
**Wir würden einen ungemessenen LLM-Schritt VOR das LLM setzen** — und damit
die Fehlerquelle einbauen, gegen die die ganze Faktenschicht geschrieben ist.

**Was sie bewertbar machen würde**, in dieser Reihenfolge:

| | |
|---|---|
| **1** | die **Übersetzung** festlegen: Ereignisart, zeitlicher Abstand, Betroffenheit — **ohne Wertung** |
| **2** | eine kostenlose Quelle für die tatsächliche Watchlist finden |
| **3** | gepaart messen, wie jede andere Änderung |

**Dieselbe Reihenfolge wie heute bei allem anderen: erst die Form, dann die
Quelle, dann die Wirkung.** Wer bei der Quelle anfängt, baut ein Etikett ein.

### 63.6 Was geändert wurde

| Stelle | |
|---|---|
| `positionierung.py` Modulkopf | Nachrichten ausdrücklich **nicht** in Rolle G, mit Begründung und Verweis |
| Umbauplan Kap. 39 | **Standvermerk**: die Gabelung wurde nicht genommen — die Stelle bleibt lesbar, sie war eine ernsthafte Überlegung |
| Regelwerksmanual R-R6 | Zusatz **Zustand gegen Ereignis** |

**Kein Code, nur Zuordnung.** Gebaut wird nichts — die Schiene bleibt hinten.
Aber sie steht jetzt an der richtigen Stelle, bevor jemand sie nach dem alten
Modulkopf in die falsche Rolle baut.

---

## Kapitel 64 — Ehrliche Börsenetiketten, ein sehender Trockenlauf, und ein Schalter, der nach der falschen Seite fiel (16.08.2026 nachts)

### 64.1 Punkt 2: jede Zeile sagt jetzt, woher ihre Daten stammen

**Der Zustand bis heute:** alle drei Börsenzeilen trugen dieselbe
Finanzierungsrate (von **Kraken**) und denselben Long-Anteil (von **Binance**).

| Feld | gemeinsame Zeitpunkte | davon verschieden |
|---|---:|---:|
| `long_account_pct` | 41.547 | **0** |
| `funding_rate` | 40.033 | **0** |
| `open_interest` | 41.551 | **41.551** |

> **Es war eine bewusste Abkürzung, kein Versehen.** Der Docstring von
> `compute_funding_rate_percentile` hält sie ausdrücklich fest: *„derselbe
> Kraken-Wert liegt redundant in allen 3 Börsen-Zeilen, daher reicht EINE
> Börse als Quelle."*

**Zerbrochen ist sie mit Rolle G.** `positionierung.py` liest seit heute früh
je Börse und nimmt die Spalte wörtlich — wer dort `exchange='bybit'` filtert,
bekam Kraken- und Binance-Daten unter falschem Etikett, **in einem Faktensatz
für ein Sprachmodell**.

**Was jetzt gilt:**

| Zeile | trägt |
|---|---|
| `kraken` | Finanzierungsrate — **neue, eigene Zeile**, weil Kraken keine der drei Börsen ist |
| `binance` | Open Interest **und** Long-Anteil (beides echt von dort) |
| `bybit`, `okx` | **nur** Open Interest |

**Ein Leser für alle:** `db.lies_funding_reihe()`. Vorher las jeder Aufrufer
selbst `WHERE exchange = 'binance'`; drei Leser hätten drei Übergänge bedeutet,
und einer davon wäre vergessen worden.

**Der Übergang ist eingebaut und befristet.** Rund 40.000 Altzeilen tragen den
Wert noch unter den Börsenetiketten; ist die `kraken`-Reihe zu kurz, wird dort
nachgesehen. Bei einem 15-Minuten-Takt greift der Rückfall nach gut acht
Stunden nicht mehr.

**Nachgewiesen an echten Daten, alle drei Fälle:**

| | |
|---|---|
| Altbestand allein | 400 Werte gelesen, Rolle-G-Perzentil **28 — unverändert** |
| 48 `kraken`-Zeilen | 48 Werte, alle aus der neuen Quelle → **Vorrang** |
| 10 `kraken`-Zeilen | 400 Werte → **Rückfall greift** |

### 64.2 Punkt 3 (O-38): der Trockenlauf sieht jetzt beide Nutzerstufen

**Zwei Stellen standen unter `if betriebsart != TROCKEN`, und die Gründe waren
verschieden:**

| Stufe | warum übersprungen | Korrektur |
|---|---|---|
| **Nutzerschalter** (DCA, Hebel-Prüfung, Bitpanda-Override) | **gar kein Grund** — `asset_schalter` ist ein reiner Leser | läuft jetzt immer |
| **Anlass-Sperre** | sie **schreibt** eine Beobachtung | läuft mit `schreiben=False` |

> **Das Urteil braucht den Schreibvorgang nicht:** der Fingerabdruck wird
> gerechnet, der Vergleich gelesen, nur die neue Zeile entfällt. **Ein
> Trockenlauf, der schreibt, verändert die Grundlage des nächsten scharfen
> Laufs** — genau das soll `probe` vermeiden.

**Wie groß der Unterschied ist, zeigt derselbe Tag:** die Anlass-Stufe hat am
16.08. **35 von 41** Kryptosymbolen gestoppt. Ein Trockenlauf, der sie nicht
kennt, meldet einen Durchsatz, den der scharfe Betrieb nie erreicht — **auch
die Läufe, mit denen der Vollumstieg geprüft wurde.**

### 64.3 Der Fund, den erst diese Korrektur sichtbar gemacht hat

**Der Schalter des Nutzers fiel nach OFFEN.**

```python
        try:
            if not db.get_hebel_pruefung_erlaubt(conn, sym):
                return False, "Hebel-Pruefung ... abgeschaltet"
        except Exception:
            logger.debug("hebel_pruefung_erlaubt nicht lesbar fuer %s", sym)
        # ... und dann ging es WEITER
```

**Nachgestellt:** ohne `conn.row_factory = sqlite3.Row` wirft der Leser einen
`TypeError`, der Fang schluckt ihn auf **debug**-Ebene — und ein ausdrücklich
**abgeschaltetes** Asset wurde trotzdem beurteilt.

| Zeilenfabrik | Schalter | Ergebnis |
|---|---|---|
| `sqlite3.Row` | AUS | wird nicht beurteilt ✓ |
| `None` | AUS | **wird beurteilt** ✗ |

> ⚠️ **Dieselbe Klasse wie die Regime-Dauer** (`row["tag"]` ohne Zeilenfabrik,
> vom breiten `except` verschluckt) — und in der Wirkung schlimmer: dort fehlte
> ein Halbsatz, hier wird eine **ausdrückliche Entscheidung des Nutzers**
> übergangen. *„Überall möglich, aber nur dort Signale erzeugen, wo ich das
> selektiv möchte."*

**Die Produktion ist nicht betroffen** — `db.get_connection()` setzt die
Zeilenfabrik. Es war eine Falle für jeden Aufrufer, der eine einfache
Verbindung öffnet; `simuliere_kette.py` und die Paketprüfungen taten genau das.

**Behoben: beide Schalter fallen jetzt ZU**, und die Meldung geht auf
**Warnung** statt debug. Wer nicht lesen kann, was gewollt ist, darf es nicht
annehmen.

### 64.4 Drei Prüfungen mussten mit — und zwei davon aus demselben Grund

> ⚠️ **Zum siebten Mal diese Woche: die Eingabe stellte den Fall nicht her.**

| Prüfung | was fehlte |
|---|---|
| „ein Hebel-Lauf erzeugt eine Mail" | **kein Schalter gesetzt.** `get_hebel_pruefung_erlaubt` ist seit dem 15.08. **Opt-in** — keine Zeile heißt AUS. Der Trockenlauf hatte das verdeckt |
| „ein normales Asset bleibt unberührt" | rief mit `conn=None` — mit fail-closed korrekterweise ein Nein. Die Prüfung meint die **Cash**-Regel und braucht einen Bestand, in dem der Schalter beantwortbar ist |
| Testverbindung | **ohne Zeilenfabrik**, anders als jede Produktionsverbindung |

**Nicht die Zusicherung gelockert, sondern den Fall hergestellt.** Und die
neuen Prüfungen halten beides fest: dass ein abgeschaltetes Asset auch trocken
keine Mail erzeugt, dass der Trockenlauf dabei **nichts schreibt**, und dass
ohne lesbare Schalter gar nicht beurteilt wird.

### 64.5 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **919, alle bestanden** (3 neue) |
| freie Namen | 0 |
| `pruefe_zahlen_in_prompts.py` | Selbsttest 9/9, 344 Sätze, kein Befund |
| `pruefe_phase1.py` | bestanden |
| Simulation | 6 Gruppen, 12 Signale, 14 Mails, **0 Fehler** |
| Funding-Übergang | drei Fälle einzeln belegt (siehe 64.1) |
| Schalter fail-closed | mit und ohne Zeilenfabrik gegengeprüft |

### 64.6 Was von der Liste bleibt

| | Punkt | Stand |
|---|---|---|
| 1 | **51 % Ausfallzeit** | Betrieb, nicht Code — bleibt oben |
| 4 | TURBO-Phantomposition | im nächsten Export nachsehen |
| 5 | **O-33** Hedge-Instrumente ohne Codeeingriff | offen |
| 6 | `job_laeufe` in den Export | offen |

---

## Kapitel 65 — Die Restpunkte: zwei geklärt, zwei gebaut (17.08.2026)

### 65.1 TURBO war nie eine hängengebliebene Zeile

**Offener Punkt seit dem 15.08.:** *„TURBO trug eine offene Hebelposition,
obwohl der Nutzer keine hält."*

**Nachgesehen im Export:** `hebel_positions` hat **188 Zeilen und keine einzige
für TURBO.**

> Der Phantombestand war der Mailbetreff-Fehler, der am 15.08. bereits behoben
> wurde: `signal_mail.py` übernahm die deterministische Ausstiegsempfehlung in
> den Betreff, sobald sie mit SCHLIESSEN begann. **Der Punkt war seit zwei
> Tagen erledigt und stand nur noch auf der Liste.**

**Ein Nebenbefund bleibt:** vier Positionen aus **Oktober 2025** stehen auf
`wahrscheinlich_liquidiert` (LINK, TAO ×2, SUI) und wurden nie aufgelöst.
`fix_stuck_hebel_positions.py` gibt es dafür — kein Betriebsproblem, aber
Altbestand, den niemand angesehen hat.

### 65.2 Die Ausfallzeit — beziffert statt geschätzt

**Die Zahl in der Liste war zu niedrig.** Gemessen über das Logfenster:

| | |
|---|---|
| Beobachtungsfenster | **57,6 h** |
| Stille (Lücken > 8 min) | **41,0 h** |
| **Ausfall** | **71 %** — nicht 51 % |

**Die vier längsten Lücken:**

| Lücke | Dauer |
|---|---|
| 14.08. 21:58 → 15.08. 07:57 | **10,0 h** |
| 15.08. 13:39 → 18:27 | 4,8 h |
| 14.08. 10:11 → 14:18 | 4,1 h |
| 16.08. 13:43 → 17:15 | 3,5 h |

> **Das ist kein Absturzmuster.** Zehn Stunden am Stück in der Nacht sind eine
> Maschine, die nicht läuft — bei einem Gerät, das ein 24/7-Server sein soll.

**Nicht die Zahl der Neustarts.** Die ist irreführend: an Entwicklungstagen
startet die App zehnmal, und das ist kein Ausfall. Gezählt wird die **Stille
zwischen zwei Logzeilen**.

**Im Code nicht behebbar — aber messbar.** Der Export trägt jetzt einen
Abschnitt `laufzeit`, damit die Zahl nicht bei jedem Mal von Hand
ausgerechnet wird und dann drei Tage veraltet in einer Liste steht:

```
fenster_stunden · fehlende_stunden · ausfall_prozent
luecken_gesamt  · laengste (10)    · schwelle_minuten
```

> **Warum das die wichtigste Betriebszahl ist:** ein System, das zwei von drei
> Stunden nicht läuft, verpasst Gelegenheiten **unsystematisch** — und jede
> Messung darauf hat eine Lücke, die im Ergebnis niemand sieht. Die
> Trichterzahlen sagen, *wo* die Kette verliert; diese sagt, ob sie überhaupt
> gelaufen ist.

### 65.3 `job_laeufe` im Export

Die Selbstprüfung meldete die Tabelle seit dem 16.08. unter `nicht_erwaehnt` —
**genau dafür gibt es sie.** Jetzt sichtbar: je Job der letzte Lauf, sein Alter
und eine Liste `ueberfaellig` (älter als 26 Stunden = ein Tageslauf ist
ausgefallen **und** der Nachholer hat ihn nicht geholt).

**Zusammen beantworten die beiden Abschnitte die Betriebsfrage:** `laufzeit`
sagt, ob die App lief — `joblaeufe` sagt, ob die Arbeit trotzdem getan wurde.

> ⚠️ **Spaltenname geraten statt nachgesehen.** Ich schrieb `gelaufen_am`, sie
> heißt `zuletzt_am`. Der erste Testaufruf hat es sofort gefangen — aber es ist
> genau der Fehler, gegen den *„immer an der Quelle prüfen"* geschrieben wurde.

### 65.4 O-33: Absicherungsinstrumente ohne Codeeingriff

> *„berücksichtige im Plan einen nachgelagerten Punkt, um Börsenwerte (Hedge
> über Nasdaq etc.) zu den Hedge-Positionen hinzufügen zu können, ohne dass wir
> in den Code eingreifen müssen."*

**Elf Module lesen `SYMBOL_ZU_HEBEL_FAKTOR` — und das war die gute Nachricht.**
Weil alle über *dieselbe* Stelle gehen, genügte es, diese eine aus der
Konfiguration zu speisen. **Kein Aufrufer musste angefasst werden.**

```yaml
hedge:
  instrumente:
    DBPK: {hebel: 2, referenz: "S&P 500"}
    3QSS: {hebel: 3, referenz: "Nasdaq-100"}
```

**Fünf Fälle einzeln belegt:**

| Fall | Ergebnis |
|---|---|
| neues Instrument dazu | `DBPK 2, 3QSS 3, XSPS 5` |
| Hebel geändert | `DBPK 4` |
| Eintrag **ohne** `hebel` | verworfen, mit Warnung |
| Abschnitt leer | **Vorgaben** |
| Konfiguration wirft | **Vorgaben** |

**Ohne `hebel` keine Aufnahme.** Der Faktor ist die Größenlogik — *benötigter
Einsatz = abzusicherndes Exposure / Hebelfaktor*. Ein geratener Wert über- oder
unterhedgt **still**.

**Die Code-Liste bleibt als Rückfall.** Eine Konfiguration, die bei einem
Tippfehler die Absicherung abschaltet, wäre der schlechtere Tausch.

**Die drei Fallstricke aus Kapitel 25.2 stehen jetzt in der `config.yaml`
selbst** — dort, wo jemand liest, der ein Instrument ergänzt: Hedge ist keine
Assetklasse (Watchlist-Eintrag als `etf` nötig), der Hebel ist die
Größenlogik, und ein neues Instrument braucht eine Kursreihe. Letzteres meldet
`rollen_job` bereits von selbst (*„n Symbole ohne Kursreihe"*).

### 65.5 Eine Prüfung, die mit der Zeit ablief

> ⚠️ **Zum achten Mal diese Woche stellte eine Eingabe den Fall nicht her — und
> diesmal, weil sie aufgehört hat, ihn herzustellen.**

```python
    ST5.is_history_stale("2026-08-14", schwelle_tage=1)
    is not ST5.is_history_stale("2026-08-14")
```

Am 16.08. war der 14.08. **zwei** Tage zurück: die Krypto-Schwelle (1 Tag)
schlug an, die geteilte (2 Tage) schwieg — der Unterschied war da. Einen Tag
später sind es **drei** Tage, beide schlagen an, und die Prüfung scheiterte.

**Sie maß den Kalender statt den Code.** Jetzt rechnet sie relativ zu heute und
prüft beide Seiten einzeln, statt nur auf Ungleichheit.

### 65.6 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **922, alle bestanden** (3 neue für O-33) |
| freie Namen | 0 |
| `pruefe_zahlen_in_prompts.py` | Selbsttest 9/9, 344 Sätze, kein Befund |
| `pruefe_phase1.py` | bestanden |
| Simulation | 6 Gruppen, 12 Signale, 14 Mails, **0 Fehler** |
| `config.yaml` | 2.034 CRLF, **0 reine LF** |
| Exportabschnitte | gegen echte Daten gerendert, fail-soft geprüft |

### 65.7 Was jetzt noch offen ist

| | Punkt | Art |
|---|---|---|
| **1** | **71 % Ausfallzeit** | **Betrieb** — im Code nicht lösbar, ab jetzt in jedem Export sichtbar |
| 2 | vier Positionen auf `wahrscheinlich_liquidiert` seit Oktober 2025 | Altbestand |
| 3 | zweite Quellenart für Rohstoffe (EIA, nur Erdgas, braucht Schlüssel) | **Entscheidung** |
| 4 | Themen-ETF und Absicherung: keine kostenlose Quelle | **Grenze** |
| 5 | Einwandrate gegen Fluss-Perzentil (R-R6) | wartet auf Daten |

**Damit ist die Liste vom 15./16.08. abgearbeitet.** Was bleibt, ist entweder
Betrieb, eine Entscheidung oder eine Messung, die Läufe braucht.

---

## Kapitel 66 — Die Zuordnungsmatrix: welcher Parameter in welche Rolle, je Assetklasse und Handelsform — und warum (17.08.2026)

**Nutzervorgabe:** *„die unterschiedlichen Zuordnungen der Parameter je Asset
und Handelsform bitte sauber zur Nachvollziehbarkeit dokumentieren — sonst
vermutet man Fehler, wo keine sind, bzw. wissen wir, warum Spot und Hebel
unterschiedlich sind."*

**Das ist der wichtigste Abschnitt dieses Kapitels.** Drei der letzten fünf
Funde waren keine Fehler, sondern Zuordnungen, deren Grund nirgends stand.

### 66.1 Die Matrix

| Parameter | Rolle | Krypto Spot | Krypto Hebel | Aktien | Rohstoffe | ETF · Absicherung |
|---|---|:-:|:-:|:-:|:-:|:-:|
| Bestand · Verlauf · Marken · Volumen | **BC** | ✓ | ✓ | ✓ | ✓ | ✓ |
| Hebelgeometrie (Liquidationsabstand) | **BC** | — | ✓ | — | — | — |
| **Finanzierungsrate** (Anteil positiver Perioden) | **BC** | **—** | **✓** | — | — | — |
| Referenzindex | **BC** | — | — | — | — | ✓ |
| **Gewinn-/Umsatzwachstum** | **BC** | — | — | **✓** | — | — |
| **Umschlag** (Umsatz / Umlaufbestand) | **BC** | **✓** | **✓** | — | — | — |
| Lange Sicht + Tagesmakro + Stimmung | **A** | ✓ | ✓ | ✓ | ✓ | ✓ |
| Offene Kontrakte · Börsendivergenz · Long-Anteil | **G** | ✓ | ✓ | — | — | — |
| **Finanzierungsrate** (Perzentil) | **G** | **✓** | **—** | — | — | — |
| Börsenzu-/-abflüsse (BTC-weit) | **G** | ✓ | ✓ | — | — | — |
| COT „Managed Money" | **G** | — | — | — | ✓ | — |
| Leerverkäufer · Insider | **G** | — | — | ✓ | — | — |

### 66.2 Warum Spot und Hebel sich unterscheiden — die drei Fälle

**Fall 1: Hebelgeometrie nur beim Hebel.** Ein Spot-Käufer wird nicht
zwangsliquidiert. Der Satz hätte dort keinen Gegenstand.

**Fall 2: Finanzierungsrate — und zwar über Kreuz.**

| | Rolle BC | Rolle G |
|---|:-:|:-:|
| **Spot** | — | ✓ |
| **Hebel** | ✓ | — |

**Warum überhaupt getrennt:** R-R2 verlangt, dass ein Parameter zu genau
**einem** Modell gehört. Steht er in beiden, hat der Prüfer nichts, was dem
Geprüften fehlt — und die zweite Stufe ist wieder das, was sie vor dem Umbau
war (17× LONG in 2.469 Prüfungen).

**Warum bei Spot in G:** gemessen (O-34) wurde die Finanzierungsrate in **63 %
der Spot-Urteile** als Beleg zitiert — obwohl ein Spot-Käufer weder Funding
zahlt noch erhält. Ein Fakt ohne Gegenstand trug dort ein Sechstel der
Begründungen. Er wurde deshalb im August aus dem Spot-Prompt entfernt.

**Warum beim Hebel in BC:** dort ist er ein *echter Kostenfaktor* — und
zugleich der **einzige** Fakt der entscheidenden Rolle, der nicht aus der
Kerzenreihe stammt. Nähme man ihn weg, stünde BC beim Hebel bei **100 % Chart**
— und genau diese Unterernährung ist der gemessene Grundbefund (von allen
Merkmalen trennt nur das Momentum Einstieg von Halten, p = 0,000).

> ⚠️ **Bis zum 17.08. stand er in BEIDEN.** Das war keine Entscheidung: der
> Plan (Kap. 36.1, Schritt 2) sagt *„Funding aus dem **Spot**-Prompt
> entfernen"* und schweigt zum Hebel. Der Modulkopf hält fest, bei Spot gehöre
> es *„jetzt zu genau einem Modell"* — über den Hebel steht dort nichts.
> **Ein Nebenprodukt, das niemand geprüft hat.**

**Fall 3: Börsenzu-/-abflüsse in beiden Instrumenten, aber nur in G.** Sie sind
BTC-weit und damit über alle Kryptosymbole eines Laufs identisch. Sie decken
**G1** (zweite Informationsart) und **nie G2** (symbolspezifisch) — das ist in
`mindestkriterien.SYMBOLSPEZIFISCH_G` kodiert und nicht Auslegung.

### 66.3 Warum manche Gruppen weniger haben — und das kein Defekt ist

| Gruppe | Rolle G hat | Grund |
|---|---|---|
| Krypto | 4–5 Größen | Terminmarkt existiert, kostenlos, symbolweise |
| Rohstoffe | COT | eine Informationsart; EIA deckt **nur Erdgas** und braucht einen Schlüssel |
| Aktien | Leerverkäufer + Insider | beide symbolspezifisch — als **einzige** Gruppe G1 und G2 aus einer Hand |
| **ETF · Absicherung** | **nichts** | **keine kostenlose Quelle bekannt** (Kap. 57) — eine Grenze, keine Lücke |

**Und in Rolle BC:**

| Gruppe | nicht-kursabgeleiteter Fakt | Anteil Kerzenreihe |
|---|---|---|
| Krypto Hebel | Finanzierungsrate | ~88 % |
| **Aktien** | **Gewinn-/Umsatzwachstum** | **60 %** |
| **Krypto Spot** | **Umschlag** (seit 17.08. abends) | **75 %** |
| Rohstoffe · ETF · Absicherung | **keiner** | **~90 %** |

> **Nachtrag 17.08. abends:** Krypto Spot hat seitdem den **Umschlag** —
> den Anteil des Umlaufbestands, der täglich den Besitzer wechselt. Der
> Preis kürzt sich heraus: (Stück × Preis)/(Umlauf × Preis). Gemessen über
> **102.316 Werte und 44 Symbole**: Median 4,77 %, p10 0,92, p90 16,12 —
> und er bewegt sich auch innerhalb eines Symbols (BRETT 3,06 → 48,49).
>
> ⚠️ **Er steht in BC, obwohl R-R6 für Rang 2 den einseitigen Kanal
> vorsieht.** Begründung: er hat **keine eingebaute Richtung** — „viel
> Umschlag" ist weder Kauf noch Verkauf, anders als der Börsenfluss, dessen
> Lesart „Zufluss = Verkaufsdruck" das Modell mitbringt, auch wenn wir sie
> nicht schreiben. Ein richtungsloser Kontextfakt kann in einem
> zweiseitigen Kanal nicht systematisch schieben. **Das ist eine Auslegung,
> keine Ableitung** — und sie gehört vor der nächsten Messung geprüft.
>
> **Offen bleiben Rohstoffe, ETF und Absicherung** — zusammen 5 % der
> Urteile, und für sie ist keine kostenlose nicht-kursabgeleitete Quelle
> bekannt.

### 66.3b Das Prinzip — die Matrix ist ableitbar, nicht auswendig zu lernen

**Nutzerfrage 17.08.:** *„prüfe noch einmal, ob die Spot- und Hebelzuordnung
korrekt ist — Funding wird grundsätzlich nur bei Hebel eingesetzt, sonst bauen
wir hier einen Fehler ein."*

**Die Frage führt weiter, als sie gestellt war.** Gilt sie für Funding, gilt
sie auch für offene Kontrakte, Long-Anteil und Börsendivergenz — es sind
**alles** Terminmarktgrößen, und ein Spot-Käufer hält keinen Terminkontrakt.

**Extern geprüft:** die Praxisliteratur ist eindeutig — Funding-Raten werden
**auch von Spot-Händlern** als Stimmungsmaß gelesen, und Extremwerte gehen
Umkehrungen voraus. Die Größe ist für Spot zulässig, **aber nicht als Kosten**.

> **Rolle BC bekommt, was MEINEN Trade ausmacht** — seinen Gegenstand, seine
> Kosten, seine Ausführbarkeit.
> **Rolle G bekommt, wie DIE ANDEREN aufgestellt sind.**

**Angewandt löst das jeden Einzelfall:**

| Parameter | Rolle | weil |
|---|---|---|
| Funding **Hebel** | **BC** | eine Zahlung, die mein Trade leistet — *„dann zahlen die Long-Positionen an die Short-Positionen"* |
| Funding **Spot** | **G** | ich zahle sie nicht; sie sagt nur, wie die anderen stehen |
| Hebelgeometrie | BC | Eigenschaft **meiner** Position |
| Umschlag | BC | **Ausführbarkeit** meines Trades |
| Gewinn-/Umsatzwachstum | BC | **was ich kaufe** |
| OI · Long-Anteil · Divergenz · Fluss · COT · Short · Insider | **G** | wie die anderen stehen — unabhängig davon, ob ich selbst am Terminmarkt bin |

**Und die Formulierung folgt dem Prinzip, nicht nur die Platzierung.** Der
BC-Satz beim Hebel nennt die **Zahlung**, der G-Satz beim Spot den
**Extremwert** — dieselbe Zahl, zwei Aussagen.

> **Nachgeprüft und abgesichert:** kein Satz der Rolle G trägt einen
> Selbstbezug („du", „dein", „zahlst") oder ein Kostenwort — **0 Treffer über
> alle Gruppen und Instrumente**. `pruefe_prompt_matrix.py` hält das fest.

**Quellen zur Spot-Nutzung der Funding-Rate:**
[Zipmex](https://zipmex.com/blog/how-to-analyze-funding-rates-in-crypto/) ·
[CryptoQuant](https://userguide.cryptoquant.com/cryptoquant-metrics/market/funding-rates) ·
[Altrady](https://www.altrady.com/blog/crypto-trading-strategies/crypto-funding-rates-explained)

### 66.4 Die Regel, nach der zugeordnet wird

| Frage | Antwort | Regel |
|---|---|---|
| Beschreibt es **den Markt** oder **diesen Wert**? | Markt → **A**, Wert → **BC/G** | P1 |
| Hat es **belegten** Wert (bei uns gemessen)? | ja → **A/BC**, nein → **G** | **R-R6** |
| Steht es schon in einer anderen Rolle? | dann **nirgends sonst** | **R-R2** |
| Ist es ein **Ereignis** statt eines Zustands? | dann **A/BC**, nie G | R-R6-Zusatz |
| Hat der Wert diesen Gegenstand überhaupt? | nein → **kein Satz** | P1, fail-closed |

**Rolle A geht über das Lagebild in Rolle BC ein** (`rollen_lauf.py:799`).
Deshalb kann ein Fakt nicht in A **und** G stehen — BC wüsste ihn dann, und G
hätte nichts mehr, was BC fehlt.

### 66.5 Was in diesem Durchgang gebaut wurde

**Punkt 1 — die Funding-Doppelung aufgelöst.** Rolle G verzichtet beim Hebel,
Rolle BC beim Spot. Betrifft **56 %** aller Urteile.

**Punkt 2 — `makro_historie_monat` erreicht Rolle A.** 1.185 Monate ab 1927,
täglich gepflegt, **von keinem Prompt gelesen**. Zwei Aussagen:

```
Der breite US-Aktienmarkt steht 1.5 Standardabweichungen ueber seinem
  langfristigen Trend, gemessen an 1184 Monaten Historie; das liegt im
  100. Perzentil der letzten 240 Monate - aussergewoehnlich weit oben.
Die US-Verbraucherpreise liegen 3.5 % ueber dem Vorjahr; das liegt im
  78. Perzentil der letzten 240 Monate - im gewohnten Bereich.
```

> **Nur zwei, nicht sechs.** Die Tabelle trägt auch Öl, Dollarindex und die
> Kursstände selbst. Alle aufzunehmen hieße, 15 auf 21 Aussagen zu bringen —
> und die Literatur, auf der dieses Projekt steht, ist eindeutig: **ab fünf
> Indikatoren verschlechtern sich Ergebnisse, ab zwölf verlangsamt sich die
> Aufnahme messbar.** Mehr Fakten sind nicht mehr Information.
>
> Ausgeschlossen nach **P3**: `rendite_10y` steckt schon in der Zinskurve,
> `spx_close`/`btc_close` beschreibt Rolle A bereits, `oel_wti` und
> `dxy_proxy` wären weitere **Kursreihen** — das Gegenteil dessen, was
> gebraucht wird.

**Punkt 4 — das Stablecoin-Angebot läuft ab heute mit.** Es erzeugt **keinen
Satz**: DefiLlama liefert nur den Momentanwert, ohne Historie kein Perzentil.
Aber die Reihe muss anfangen zu wachsen — in drei Monaten trägt sie ein
90-Tage-Perzentil, und dann ist sie eine **dritte** Informationsart für Krypto
(weder Kursreihe noch Terminmarkt).

### 66.6 Zwei Funde aus der Gegenprüfung

**R-T11 galt nur für Rolle G.** Von Rolle As fünfzehn Aussagen trugen **acht**
ein Perzentil ohne ein Wort dazu, ob das viel ist — und Rolle A speist **100 %
der Urteile**. Die Regel entstand gestern bei Rolle G und wurde dort angewandt,
wo sie gefunden wurde. Jetzt überall, mit **einer** Definition
(`marktlage._einordnung`, dieselben Grenzen 90/10 wie in `positionierung`).

**Nach der Korrektur: 0 Befunde statt 8.**

> ⚠️ **Und derselbe Vorzeichenfehler zum zweiten Mal an einem Tag.** Der erste
> Entwurf schrieb *„Die US-Verbraucherpreise liegen **−0,1 % über** dem
> Vorjahr"* — bei Deflation ist „über" schlicht falsch. Zwei Stunden zuvor
> stand derselbe Fehler im Fundamentalsatz („der Umsatz wächst schneller",
> obwohl beide schrumpften). **Ein Muster, kein Zufall: ich formuliere den
> Regelfall und prüfe die Vorzeichen nicht.**

### 66.7 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **928, alle bestanden** |
| freie Namen | 0 |
| `pruefe_zahlen_in_prompts.py` | Selbsttest 9/9, kein Befund |
| Rolle A | 17 Aussagen, **0 Befunde** (vorher 8) |
| Rolle G Spot/Hebel | Funding genau einmal, G1/G2 in beiden erfüllt |
| Kausalität | Anker 2020-03 liefert −0,2 SD (25. Perzentil) gegen heute +1,6 SD (100.) |
| Simulation | 6 Gruppen, 12 Signale, 14 Mails, **0 Fehler** |

---

## Kapitel 67 — Ende-zu-Ende-Test aller neuen Parameter: die Matrix wird ausführbar (17.08.2026)

**Nutzervorgabe:** *„mache für alle zuletzt neu hinzugefügten LLM-Parameter der
Rollen einen sauberen Ende-zu-Ende-Test und eine detaillierte Fehler- und
Promptanalyse."*

### 67.1 Warum ein viertes Prüfwerkzeug — und kein drittes zu viel

| Werkzeug | prüft |
|---|---|
| `pruefe_pakete.py` | **Einzelteile** — jede Funktion für sich |
| `simuliere_kette.py` | den **Durchlauf** — kommt eine Mail heraus |
| `pruefe_zahlen_in_prompts.py` | die **Form** der Sätze — Zahlen, Etiketten, Konstanten |
| **`pruefe_prompt_matrix.py`** | die **Zuordnung** — steht der Parameter bei der richtigen Rolle, Assetklasse **und Handelsform** |

**Die Matrix aus Kapitel 66 steht jetzt als Code.** Weicht der Betrieb ab,
meldet das Skript es — und niemand muss raten, ob eine fehlende Zeile ein
Fehler oder eine begründete Auslassung ist.

> **Drei der letzten fünf Funde waren keine Fehler, sondern Zuordnungen, deren
> Grund nirgends stand.** Genau dagegen ist es gebaut.

### 67.2 Das Ergebnis — Rolle BC

| Gruppe / Instrument | Sätze | aus der Kerzenreihe | Blöcke |
|---|---:|---:|---|
| krypto/spot | 8 | **75 %** | bestand, verlauf, marken, volumen, **umschlag** |
| krypto/hebel | 10 | **80 %** | + hebelgeometrie, (finanzierung) |
| **aktien/spot** | 10 | **60 %** | + **fundamental** |
| rohstoffe/spot | 6 | 67 % | bestand, verlauf, marken, lücken |
| **themen_etf/spot** | 7 | **86 %** | bestand, verlauf, marken, volumen |
| hedge/absicherung | 6 | 50 % | bestand, verlauf, marken, lücken |

### 67.3 Das Ergebnis — Rolle G

| Gruppe / Instrument | Sätze | Merkmale |
|---|---:|---|
| krypto/spot | 8 | terminmarkt · divergenz · **funding** · long_anteil · börsenfluss |
| **krypto/hebel** | 6 | terminmarkt · divergenz · long_anteil · börsenfluss — **kein funding** |
| rohstoffe/spot | 5 | cot |
| aktien/spot | 6 | short · insider |
| themen_etf · hedge | 3 | — |

> **Die Zeile `krypto/hebel` ist der eigentliche Nachweis.** Dort fehlt das
> Funding — und das ist die Vorschrift, nicht ein Defekt (R-R2 je Instrument).
> Ohne dieses Werkzeug hätte das jeder für einen Fehler gehalten.

### 67.4 Fehleranalyse — der Test hat zuerst sich selbst gefunden

**Fünf Abweichungen im ersten Lauf, davon zwei aus meinem eigenen Prüfmuster:**

| | Meldung | Urteil |
|---|---|---|
| 1 | `boersenfluss` fehlt bei krypto/spot | ⚠️ **mein Fehler** — der Satz hat **zwei Formen** („auf die Börsen" / „von den Börsen herunter"), mein Muster kannte eine |
| 2 | dito bei krypto/hebel | dito |
| 3 | `fundamental` fehlt bei PLTR | **kein Fehler** — das Test-Backup ist älter als der Job, der die Daten schreibt |
| 4 | aktien 86 % Kerzenreihe | Folge von 3 — **mit** Jobdaten sind es **60 %** |
| 5 | themen_etf 86 % Kerzenreihe | **echt und bekannt** — keine kostenlose Quelle (Kap. 57) |

**Daraus zwei Verbesserungen am Werkzeug selbst:**

- **Zwei Satzformen** statt einer im Muster
- **`JOBABHAENGIG`** — fehlen die Rohdaten, meldet das Skript *„ohne Rohdaten,
  Job lief gegen diese Datei nicht"* statt einer Lücke. **Ein Prüfer, der eine
  korrekte Auslassung als Fehler meldet, wird nach dem dritten Mal ignoriert.**

**Nach der Korrektur, mit vollständigen Jobdaten: eine einzige Abweichung** —
Themen-ETF bei 86 %.

### 67.5 Promptanalyse — was sich heute bewegt hat

| Gruppe | Kerzenreihe vorher | nachher | wodurch |
|---|---:|---:|---|
| **aktien/spot** | 85 % | **60 %** | Gewinn-/Umsatzwachstum |
| **krypto/spot** | ~90 % | **75 %** | Umschlag |
| krypto/hebel | ~88 % | 80 % | Umschlag (Funding war schon da) |
| themen_etf · rohstoffe | ~86 % | unverändert | **keine Quelle** |

**Und Rolle A**, die über das Lagebild in **jede** Gruppe eingeht:

| | vorher | nachher |
|---|---:|---:|
| Aussagen | 15 | **17** |
| davon kursabgeleitet | 12 (80 %) | 12 (**71 %**) |
| Perzentile **ohne** Einordnung | **8** | **0** |

### 67.6 Was der Test NICHT beantwortet

**Er prüft Zuordnung und Form, nicht Wirkung.** Ob die neuen Sätze die Urteile
verbessern, weiß niemand — dafür braucht es den gepaarten Vergleich, und der
braucht Läufe unter dem neuen Stand (`2026-08-17b`).

**Drei Auslegungen stehen weiterhin zur Prüfung und nicht zur Ableitung:**

| | Auslegung | Prüfbar durch |
|---|---|---|
| 1 | Der **Umschlag** steht in BC, obwohl R-R6 für Rang 2 den einseitigen Kanal vorsieht — Begründung: keine eingebaute Richtung | Vergleich der Einstiegsquote mit/ohne |
| 2 | Der **Börsenfluss** bleibt in G, obwohl er über alle Symbole wortgleich ist | Einwandrate gegen Fluss-Perzentil |
| 3 | **Zwei** Makroaussagen statt sechs — wegen der Überlastungsgrenze | Vergleich mit einem Arm, der mehr trägt |

### 67.7 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **932, alle bestanden** |
| freie Namen | 0 |
| `pruefe_zahlen_in_prompts.py` | Selbsttest 9/9, kein Befund |
| **`pruefe_prompt_matrix.py`** | **1 Abweichung** — themen_etf, bekannt und dokumentiert |
| `pruefe_phase1.py` | bestanden |
| Simulation | 6 Gruppen, 12 Signale, 14 Mails, **0 Fehler, 0 Lücken** |
| Form über alle Rollen | **kein Satz rechnet dem Modell etwas vor** |

---

## Kapitel 68 — Zwei Parameter, die sich selbst einschalten (17.08.2026)

**Nutzerfrage:** *„damit diese zukünftigen Parameter auch nicht vergessen
werden — sind diese alle dokumentiert und im Plan, bzw. hast du diese bereits
fertig umgesetzt und wir warten nur?"*

> ⚠️ **Beim Stablecoin-Angebot lautete die Antwort: NEIN.** Ich hatte nur das
> **Sammeln** gebaut. In drei Monaten hätte sich jemand erinnern müssen, dass
> da eine Reihe wächst, für die noch kein Satz existiert — **und genau so
> gehen Dinge verloren.**

### 68.1 Was jetzt gilt

**Beide Wege stehen vollständig.** Der Satz entsteht, sobald die Reihe lang
genug ist; bis dahin entsteht keiner. **Es gibt nichts zu merken und nichts
nachzubauen — die Zeit allein schaltet sie ein.**

| Parameter | Rolle | ab | Takt | brauchbar in |
|---|---|---:|---|---|
| **Stablecoin-Angebot** | G, Krypto | 90 Punkten | täglich | ~3 Monaten |
| **DVOL** (implizite Schwankung) | G, **nur BTC/ETH** | 60 Punkten | täglich | ~2 Monaten |
| **Skew** (Schieflage der Absicherungskosten) | G, **nur BTC/ETH** | 60 Punkten | täglich | ~2 Monaten |

**Nachgewiesen, nicht behauptet** — mit nachgestellter Historie erscheinen alle
drei Sätze, ohne sie keiner:

```
Das insgesamt im Kryptomarkt liegende Stablecoin-Kapital steht im
  99. Perzentil der letzten 120 Messungen - aussergewoehnlich viel.
Am Optionsmarkt preisen die Haendler die Schwankung der naechsten Wochen
  im 78. Perzentil der letzten 90 Messungen ein - im gewohnten Bereich.
Dabei ist Absicherung nach unten die teurere Seite; wie deutlich, steht
  im 84. Perzentil der letzten 90 Messungen - im gewohnten Bereich.
```

**Gegenprobe SOL:** kein Optionsmarkt (Deribit führt ihn nicht), aber das
marktweite Stablecoin-Kapital sehr wohl.

### 68.2 Warum zu Rolle G

**Nach dem Prinzip aus 66.3b:** beide beschreiben, **wie die anderen
aufgestellt sind** — das verfügbare, noch nicht investierte Kapital und das,
was der Optionsmarkt für die nächsten Wochen einpreist. Keine davon ist eine
Eigenschaft *meines* Trades.

**DVOL ist dabei die einzige vorausschauende Größe im ganzen System.** Alles
andere — Kurs, Umsatz, Positionierung, Flüsse — beschreibt, was **war**.

### 68.3 Und die Matrix weiß davon

`pruefe_prompt_matrix.py` führt beide, aber **nur unter `darf_nicht`** für die
fremden Gruppen — nicht unter `muss`. Sonst meldete sie drei Monate lang eine
Lücke, die keine ist.

> **Ein Prüfer, der eine korrekte Auslassung als Fehler meldet, wird nach dem
> dritten Mal ignoriert.** Das ist inzwischen der dritte Ort, an dem dieselbe
> Überlegung steht.

### 68.4 Ein freier Name, gefangen bevor er lief

> ⚠️ Mein erster Entwurf benutzte `heute` im Deribit-Block des Jobs — **dort
> ist es nicht definiert**, es gehört zu `_aktien_reihen`. Ein `NameError`, den
> der breite Fang als *„Optionsmarkt nicht auffrischbar"* verschluckt hätte:
> die Reihe wäre nie gewachsen, und in drei Monaten hätte jemand gerätselt,
> warum kein Satz kommt.
>
> **`finde_freie_namen.py` hat ihn gefangen** — zum vierten Mal in zwei Tagen,
> und dieses Mal vor dem ersten Lauf.

### 68.5 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **932, alle bestanden** |
| freie Namen | **0** (einer gefunden und behoben) |
| `pruefe_zahlen_in_prompts.py` | Selbsttest 9/9, **356 Sätze**, kein Befund |
| `pruefe_prompt_matrix.py` | 2 bekannte Abweichungen (Testbestand ohne Jobdaten) |
| Job live | 5 neue Reihen geschrieben, **0 Fehler** |
| Selbsteinschaltung | mit Historie 3 Sätze, ohne Historie 0 |
| Simulation | 6 Gruppen, 12 Signale, **0 Fehler, 0 Lücken** |

---

## Kapitel 69 — Die Mindestabdeckung, gezählt statt eingeschätzt (17.08.2026)

**Nutzervorgabe:** *„es fehlen noch einige für den geplanten glatten Schnitt zur
alten Kette und dem angestrebten Ziel — also hier müssen wir dranbleiben und
eine brauchbare Ausgangslage schaffen, sonst messen wir aber wieder nur einen
Ausschnitt."*

**Damit die Aussage prüfbar wird und nicht Einschätzung bleibt, ist sie jetzt
ein Kriterium im Code: BC3.**

### 69.1 BC3 — mindestens ein Fakt außerhalb der Kursreihe

> **Ein Urteil auf einer einzigen Datenquelle ist kein Urteil, sondern eine
> Umformulierung dieser Quelle.**

**Der Grund ist gemessen:** von allen gespeicherten Merkmalen trennt einzig das
Momentum-Perzentil Einstieg von Halten (0,760 gegen 0,624 über 340 Urteile,
p = 0,000) — nicht weil das Modell fixiert wäre, sondern weil an einer echten
Signalmail nachgezählt **sieben von neun** Sätzen aus derselben Kerzenreihe
stammen. Und es trifft den Grundbefund: *die Information ist nicht in den
Kursdaten* (8.441 Fälle).

**Gemeldet, nicht gesperrt** — drei von sechs Gruppen erfüllen es heute nicht.

### 69.2 Die Ausgangslage, je Symbol gezählt

| Gruppe / Instrument | Symbole | **BC3** | **G1** | **G2** | Kursanteil |
|---|---:|---:|---:|---:|---:|
| krypto/spot | 43 | **43/43** | 37/43 | 37/43 | 75 % |
| krypto/hebel | 43 | **43/43** | 37/43 | 37/43 | 73 % |
| **aktien/spot** | 2 | **2/2** | **2/2** | **2/2** | **63 %** |
| rohstoffe/spot | 4 | **0/4** | 0/4 | 4/4 | 67 % |
| **themen_etf/spot** | 5 | **0/5** | **0/5** | **0/5** | **86 %** |
| hedge/absicherung | 2 | **0/2** | 0/2 | 0/2 | 61 % |

> **Aktien ist die einzige Gruppe, die alle drei Kriterien vollständig
> erfüllt** — und sie stellt **1 %** der Urteile.

### 69.3 Was zur brauchbaren Ausgangslage fehlt

| | Lücke | Umfang | Aussicht |
|---|---|---|---|
| **1** | **6 von 43 Kryptowerten ohne Terminmarktdaten** → G1 und G2 fallen | ~14 % der Kryptosymbole | Datenlage der Börsen, **nicht behebbar** |
| **2** | **Rohstoffe: kein Nicht-Chart-Fakt für BC** | 4 Symbole, 3 % der Urteile | **offen** — COT liegt bei G, für BC fehlt etwas Eigenes |
| **3** | **Rohstoffe: G1 bei einer Quelle** | dito | EIA, **nur Erdgas**, braucht Schlüssel |
| **4** | **Themen-ETF: alles** | 5 Symbole | **keine kostenlose Quelle** |
| **5** | **Absicherung: alles** | 2 Symbole | **keine kostenlose Quelle** |

**Nach Urteilen gewichtet** sind das 5 % — nach Gruppen die Hälfte. **Für einen
glatten Schnitt zählt die zweite Zahl:** eine Gruppe, die strukturell weniger
sieht, ist im Vorher-Nachher-Vergleich nicht vergleichbar, egal wie selten sie
auftritt.

### 69.4 Was in den kommenden Wochen von selbst dazukommt

| Parameter | Rolle | brauchbar in | Wirkung auf |
|---|---|---|---|
| Stablecoin-Angebot | G | ~3 Monaten | Krypto, **alle 43** |
| DVOL · Skew | G | ~2 Monaten | **nur BTC/ETH** |

**Keiner davon schließt eine der fünf Lücken oben.** Sie vertiefen, wo es schon
Abdeckung gibt.

### 69.5 Die ehrliche Folgerung

**Der glatte Schnitt ist heute nicht messbar.** Ein gepaarter Vergleich über
alle Gruppen würde bei Rohstoffen, Themen-ETF und Absicherung eine
Faktengrundlage vergleichen, die es in der alten Kette so nie gab — und bei
Krypto sechs Symbole ohne zweite Stufe.

**Was heute geht:** ein Vergleich **innerhalb** von Krypto und Aktien, also
über **94 %** der Urteile. Das ist kein Ausschnitt im Sinne der Warnung,
sondern die Menge, für die die Ausgangslage steht — und sie wäre als solche zu
benennen.

### 69.6 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **932, alle bestanden** |
| freie Namen | 0 |
| `pruefe_zahlen_in_prompts.py` | Selbsttest 9/9, **356 Sätze**, kein Befund |
| `pruefe_prompt_matrix.py` | 2 bekannte Abweichungen |
| `pruefe_phase1.py` | bestanden |
| Simulation | 6 Gruppen, 12 Signale, 14 Mails, **0 Fehler, 0 Lücken** |
| Abdeckung | je Symbol gezählt, nicht je Gruppe geschätzt |

---

## Kapitel 70 — Krypto steht, Rohstoffe haben einen Weg, Themen-ETF nicht (17.08.2026)

### 70.1 Krypto — die Basisabdeckung steht

| | |
|---|---|
| **BC3** (Nicht-Chart-Fakt) | **43/43 = 100 %** — der Umschlag |
| **G1 + G2** | 37/43 Symbole = **96 % der Urteile** |

**Die sechs Ausfälle kosten 15 von 428 Urteilen = 4 %** — und zwei davon
(CANTON, VSN) erzeugen ohnehin keine, weil ihnen die Kursreihe fehlt.

| Symbol | Urteile | OI-Zeilen |
|---|---:|---:|
| AIOZ · SUPRA · XNO | je 4 | 217 · 0 · 0 |
| FLOKI | 3 | 557 |
| CANTON · VSN | **0** | 0 |

**Nicht behebbar:** die Börsen führen für diese Werte keine Terminkontrakte.
Das ist eine Datenlage, keine Verdrahtung.

### 70.2 Rohstoffe — ein Weg, und er deckt drei von vier

**Nutzerhinweis:** *„Erdgas alleine ist den Aufwand u. U. nicht wert."*
**Richtig — und die Recherche hat etwas Besseres ergeben.**

Freie Schnittstellen ohne Schlüssel für Lagerbestände, ETF-Bestände oder
Zentralbankkäufe gibt es nicht: [Heavy Metal
Stats](https://heavymetalstats.com/) und
[MetalCharts](https://metalcharts.org/comex) sind Oberflächen, keine APIs;
[Metals-API](https://metals-api.com/) und
[Commodities-API](https://commodities-api.com/) liefern **Preise** — genau das,
wovon wir zu viel haben.

**Aber derselbe Trick wie beim Krypto-Umschlag trägt:** die **Stückzahl** eines
physisch hinterlegten ETF ist eine Mengenangabe, kein Preis. Sie ändert sich
nur, wenn Metall tatsächlich ein- oder ausgelagert wird — eine echte
Nachfragegröße.

| Rohstoff | ETF | `sharesOutstanding` | frei |
|---|---|---:|---|
| **Gold** | GLD | 260.300.000 | ✓ yfinance |
| **Silber** | SLV | 341.449.984 | ✓ |
| **Erdgas** | UNG | 12.084.600 | ✓ |
| Kupfer | CPER | **nicht verfügbar** | ✗ |

> **Drei von vier statt Erdgas allein** — und ohne Schlüssel, anders als EIA.

**Einschränkungen, offen gesagt:** yfinance liefert nur den Momentanwert, also
**dieselbe Wartezeit wie beim Stablecoin** (~3 Monate bis zum Perzentil). Und
die Größe gehört nach dem Prinzip 66.3b zu **Rolle G** — sie beschreibt, wie
die anderen aufgestellt sind. **Sie schließt G1, nicht BC3.**

**Für BC3 bliebe bei Rohstoffen die Haltekostenquote.** Sie ist heute nirgends
hinterlegt — nur die Absicherung hat eine, und die ist ausdrücklich
*„geschätzt, nicht belegt"*. Sie müsste je Instrument recherchiert werden und
ist **gelb**: der Kostenhinweis hat die ERÖFFNEN-Quote schon einmal von 93 %
auf 3 % gerissen.

### 70.3 Themen-ETF — die Abgrenzung ist wirklich unklar

**Nutzerhinweis:** *„bei den Themen-ETF bin ich mir schon bei der Abgrenzung
unsicher."* **Zu Recht, und das lässt sich zeigen:**

| Symbol | Thema |
|---|---|
| VVMX | seltene Erden |
| X136 | erneuerbare Energie |
| EXH3 | Basiskonsum |
| **CEBS** | **Kupfer** |
| ISOC | Agrar, diversifiziert |

> **CEBS ist ein Kupfer-ETF in der Gruppe `themen_etf`, während OD7C ein
> Kupfer-Zertifikat unter `rohstoffe` steht.** Dieselbe Sache, zwei Gruppen.
> Fünf Symbole, fünf verschiedene Themen — eine Gruppe ist das nur der Form
> nach.

**Was sie schon haben, und es funktioniert:** den **Sektorbezug** — relative
Stärke zum breiten Markt, gebaut in Kapitel 35.5 genau für diesen Fall. Er
streut kräftig (VVMX −15,3 %/−30,0 % gegen X136 +5,7 %/−1,1 %).

> ⚠️ **Mein Matrixtest hat ihn übersehen** — ich übergab `referenz` nicht und
> meldete daraufhin, die Gruppe habe keinen. Behoben. Zum wiederholten Mal
> derselbe Typ: die Eingabe stellte den Fall nicht her, den sie prüfen wollte.

**Aber er löst BC3 nicht:** die relative Stärke vergleicht **zwei Kursreihen**
und ist damit selbst eine. Mit ihm steht die Gruppe bei **89 % Kursanteil** —
dem schlechtesten Wert überhaupt.

**Was helfen würde, gibt es nicht als eine Quelle:** jedes der fünf Themen
bräuchte seine eigene — seltene Erden, Erneuerbare, Basiskonsum, Kupfer, Agrar.
**Fünf Quellen für fünf Symbole und 3 % der Urteile.**

> **Empfehlung, dem Nutzervorschlag folgend: zurückstellen.** Nicht weil es
> unwichtig wäre, sondern weil der Aufwand je Urteil um Größenordnungen über
> allem liegt, was wir sonst tun könnten — und weil die Gruppe vorher eine
> **Abgrenzung** braucht, keine Parameter.

### 70.4 Ein eigener Fund am Rande

**Zwei Definitionen desselben Begriffs.** `mindestkriterien.KURSREIHENBLOECKE`
führte `referenz` als Kursreihe, `pruefe_prompt_matrix` nicht — und sie liefen
sofort auseinander: **67 % gegen 89 %** für dieselbe Gruppe. Jetzt importiert
die Matrix die eine Definition.

### 70.5 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **932, alle bestanden** |
| freie Namen | 0 |
| `pruefe_prompt_matrix.py` | Sektorbezug ergänzt, **eine** Definition für „Kursreihe" |
| Krypto-Abdeckung | je Symbol gezählt, Ausfälle beziffert |
| Rohstoff-Recherche | vier Anbieter geprüft, drei von vier Metallen abgedeckt |

---

## Kapitel 71 — ETF-Bestände für Rohstoffe, und was bei einem neuen Wert passiert (17.08.2026)

### 71.1 Die hinterlegte Menge — Rohstoffe bekommen ihre zweite Quellenart

**Gebaut nach demselben Muster wie Stablecoin und Deribit: vollständig, mit
Selbsteinschaltung.** Der Job sammelt ab heute, der Satz entsteht ab 90
Punkten — **rund drei Monate**.

| Rohstoff | ETF | Stückzahl | Stand 17.08. |
|---|---|---|---:|
| **Gold** | GLD | `sharesOutstanding` | 260.300.000 |
| **Silber** | SLV | dito | 341.449.984 |
| **Erdgas** | UNG | dito | 12.084.600 |
| Kupfer | CPER | **nicht ausgewiesen** | — |

> **Warum die Stückzahl und nicht das Fondsvolumen:** das Volumen ist
> *Stück × Preis* und damit eine Kursgröße. Die Stückzahl eines physisch
> hinterlegten ETF ändert sich **nur, wenn Metall tatsächlich ein- oder
> ausgelagert wird** — eine echte Nachfragegröße. Derselbe Gedanke wie beim
> Krypto-Umschlag.

**⚠️ Die Veränderung ist die Aussage, nicht der Stand.** Ein Perzentil auf den
Stand wäre wertlos: die Reihe wächst oder fällt langsam, und der jüngste Wert
läge fast immer im 0. oder 100. Perzentil — **ein konstantes Feld in
Zeitlupe** (R-T6). Gemessen wird die Veränderung über 20 Tage und ihr
Perzentil gegen die eigene Geschichte.

**Nachgewiesen mit nachgestellter Historie:**

```
Die in boersengehandelten Fonds physisch hinterlegte Menge dieses
  Rohstoffs wurde in den letzten 20 Tagen abgebaut.
Wie stark, steht im 20. Perzentil der letzten 120 Messungen -
  im gewohnten Bereich.
```

| Symbol | Quellen | G1 | G2 |
|---|---|---|---|
| **OD7H** (Gold) | cot · **etf_bestand** | **erfüllt** | **erfüllt** |
| OD7C (Kupfer) | cot | fehlt | erfüllt |

**Damit schließt sich Lücke 3 aus Kapitel 69 für drei von vier Rohstoffen** —
ohne Schlüssel, anders als EIA.

### 71.2 Die Frage, die den Schiefstand verhindert

**Nutzerfrage:** *„ist dies nur für den Bestand implementiert oder funktioniert
das auch bei neuen Werten? Sonst bekommen wir einen Schiefstand, wenn
gehandelt wird."*

**Die Parameter zerfallen in zwei Klassen, und nur eine ist gefährlich:**

| | Klasse | Parameter |
|---|---|---|
| ✓ | **von selbst** — leiten sich aus der Watchlist oder aus Tabellen ab, die je Symbol gefüllt werden | Umschlag · Fundamentaldaten · Leerverkäufer · Insider · Terminmarkt · Börsendivergenz · Sektorbezug · Bestand · Verlauf · Marken · Volumen |
| ⚠️ | **nur mit Eintrag** — eine von Hand gepflegte Zuordnung entscheidet, ob der Parameter überhaupt entsteht | **COT + ETF-Bestand** (`SYMBOL_ZU_COT_ROHSTOFF`) · **Hebelfaktor** (`SYMBOL_ZU_HEBEL_FAKTOR`) |

> **Fehlt der Eintrag, fällt der Parameter STILL aus:** kein Fehler, keine
> Logzeile, nur ein Satz weniger. Ein neuer Rohstoff wäre in Rolle G **völlig
> blind** — und niemand sähe es, weil dieselbe Rolle bei den vier bestehenden
> liefert.

**Stand heute: beide Zuordnungen vollständig.**

```
COT + ETF-Bestand (Rohstoffe)    4 Eintraege,  4 Symbole   vollstaendig
Hebelfaktor (Absicherung)        2 Eintraege,  2 Symbole   vollstaendig
```

**Und die Prüfung schlägt an, sobald das nicht mehr gilt** — gegengeprüft mit
zwei erfundenen Neuzugängen:

```
⚠️ rohstoffe/OD7X: fehlt in SYMBOL_ZU_COT_ROHSTOFF - faellt STILL aus
⚠️ hedge/XSPS:     fehlt in SYMBOL_ZU_HEBEL_FAKTOR - faellt STILL aus
```

**`pruefe_prompt_matrix.py` führt das ab jetzt bei jedem Lauf.** Wer einen
Wert aufnimmt, sieht beim nächsten Prüflauf, was ihm fehlt — statt es
Wochen später an einer stillen Lücke zu merken.

### 71.3 Der Stand der Mindestabdeckung

| Gruppe | BC3 | G1 | G2 | Änderung heute |
|---|---|---|---|---|
| krypto/spot · hebel | ✓ 100 % | 96 % | 96 % | — |
| aktien/spot | ✓ | ✓ | ✓ | — |
| **rohstoffe** | ✗ | **3 von 4 ab ~3 Monaten** | ✓ | **ETF-Bestand** |
| themen_etf · hedge | ✗ | ✗ | ✗ | zurückgestellt |

**Offen bleibt bei Rohstoffen BC3** — dafür käme nur die Haltekostenquote in
Frage, und die ist gelb.

### 71.4 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **932, alle bestanden** |
| freie Namen | 0 |
| `pruefe_zahlen_in_prompts.py` | Selbsttest 9/9, **360 Sätze**, kein Befund |
| `pruefe_prompt_matrix.py` | 2 bekannte Abweichungen, Neuzugangsprüfung **vollständig** |
| Job live | 3 ETF-Bestände geschrieben, 0 Fehler |
| Selbsteinschaltung | mit Historie 2 Sätze, ohne Historie 0 |
| Gegenprobe Neuzugang | 2 erfundene Symbole, **2 Lücken gemeldet** |
| Simulation | 6 Gruppen, 12 Signale, **0 Fehler, 0 Lücken** |

---

## Kapitel 72 — Was beim Umbau liegengeblieben ist, und die Reihen, die stillstanden (17.08.2026)

**Nutzerfrage:** *„diverse Parameter sind weggefallen beim Umbau — M2 Money
Supply, ISM, Consumer Index. Wurden diese einfach verworfen oder haben wir sie
aktiv entfernt? Prüfe ob wir sie nutzen, nicht nutzen und warum — LLM-Tauglichkeit?"*

### 72.1 Die Antwort ist unangenehmer als beide Möglichkeiten

**Weder verworfen noch entfernt — es wurde nie entschieden.** Die Felder
schreibt `agent/krypto/pipeline.py::_update_macro_snapshot`, also die **alte**
Pipeline. Die läuft heute nur noch, wenn jemand in der Oberfläche von Hand ein
Signal auslöst. Als die Rollenkette sie ersetzte, hörte der Schreiber auf zu
laufen; die Spalten stehen alle noch da, mit 7 bis 9 Zeilen.

| Parameter | in der DB | erreicht eine Rolle |
|---|---|---|
| M2 USA (`M2SL`) | 7 Zeilen, bis 15.07. | ✗ |
| M2 Eurozone / China / Japan | je 9, bis 19.07. | ✗ |
| ISM-Ersatz (Philly Fed) | 7 Zeilen, bis 15.07. | ✗ |
| CPI headline / core | 7 Zeilen, bis 15.07. | ✓ als `cpi_yoy_prozent` |
| **Consumer Confidence** | — | **nie gebaut** |

> **Den echten ISM hatten wir nie.** FRED verlor die Lizenz 2016 — `NAPM`
> antwortet heute *„series does not exist"* (live geprüft). Was gespeichert
> ist, ist der Philadelphia-Fed-Index als Stellvertreter: eine **regionale**
> Umfrage für eine nationale, zwischen zwei Monatswerten 10,3 → 41,4.

### 72.2 LLM-Tauglichkeit — und warum nichts davon zurückkommt

| | Parameter | Urteil |
|---|---|---|
| 🔴 | **M2** | **Redundant gegen etwas Besseres, das schon drin ist.** Die Netto-Liquidität (WALCL − TGA − RRP) misst dieselbe Frage — wie viel Geld im System ist — **wöchentlich statt monatlich** und näher am Mechanismus. M2 ging nicht verloren, es wurde ersetzt. **P3.** |
| 🔴 | **ISM / Philly Fed** | Stellvertreter eines Stellvertreters (Rang 2–3), und er trägt ein **Etikett**: über/unter 50 heißt „Expansion/Kontraktion" — dasselbe fertige Urteil, das beim Regime herausgeflogen ist. **R-T12.** |
| 🟡 | **Consumer Confidence** | Fachlich sauber, keine Kursgröße, über `UMCSENT` frei (live geprüft: Juni 2026 = 49,5). Aber **monatlich mit ~2 Monaten Verzug** — M2 steht Mitte August auf dem Juni-Wert. |
| 🟢 | **CPI** | **Ist seit 16.08. drin** und war von den dreien die richtige Wahl: 942 Monate, keine Kursgröße, als Perzentil mit Einordnung. |

Dazu die Überlastungsgrenze: Rolle A trägt **17 Aussagen**. Alle drei
nachzuziehen hieße 20 — und die zwei stärksten davon sind rot.

### 72.3 Der eigentliche Fund: drei Reihen standen still

**Bei der Prüfung fiel etwas Schlimmeres auf als eine fehlende Zahl.** Die
zwei Makro-Fakten der Rolle A und die Stimmung stammten aus **Skripten, die
ein Mensch von Hand startet** — `lade_makro_historie_nach.py` und
`lade_fear_greed_nach.py`. Kein `add_job()`, nirgends.

```
netto_liquiditaet_mrd   letzter Wert 2026-08-05   (12 Tage)
rendite_10j_pct         letzter Wert 2026-08-11   ( 6 Tage)
fear_greed_value        letzter Wert 2026-08-12   ( 5 Tage)
                        alle 3.111 Zeilen mit demselben fetched_at
```

> **⚠️ Warum das niemand sah.** `marktlage.beschreibe_makro` nimmt den
> jüngsten Wert **≤ Ankertag — ohne Altersgrenze**. Der Satz verschwindet
> also nicht, wenn die Reihe stehenbleibt. Er wird weiter erzeugt, weiter an
> das Modell gegeben, weiter geglaubt — nur immer älter.
>
> **Ein fehlender Satz fällt auf. Ein alter sieht aus wie ein frischer.**

**Das ist „fail-soft ist fail-silent" in seiner unangenehmsten Form: hier
fällt nicht einmal etwas aus. Es steht nur still.**

### 72.4 Was gebaut wurde

**`lagebild_reihen_job`, täglich 06:40, mit Sofortstart.** Holt beide
Makrogrößen und Fear & Greed über ein 120-Tage-Fenster; benutzt die Abrufe der
Nachladeskripte statt sie zu kopieren — zwei Kopien wären zwei Stellen, an
denen die Einheitenumrechnung (Mio. gegen Mrd.) auseinanderlaufen kann.

| | Nachladen | Tagesjob |
|---|---|---|
| Fenster | 2017 bis heute | 120 Tage |
| Konflikt | `COALESCE(bestand, neu)` | **`COALESCE(neu, bestand)`** |
| Grund | Historie darf einen Live-Wert nicht überschreiben | die Fed **revidiert** WALCL — der frische Wert ist die Korrektur |

> **Der Abrufstempel wandert immer mit**, auch wenn kein Wert neu ist. Er
> beantwortet *„wann haben wir zuletzt nachgesehen"*, nicht *„wann hat sich
> etwas geändert"*. Ohne diese Zeile meldete eine wöchentliche Reihe an sechs
> von sieben Tagen einen Jobausfall — und nach dem dritten Fehlalarm sieht
> niemand mehr hin.

**Nachgewiesen an einer Kopie, nie an der Quelle:**

```
Liquiditaet  2026-08-05 -> 2026-08-12      Zins  2026-08-11 -> 2026-08-14
Fear & Greed 2026-08-12 -> 2026-08-17      203 Punkte, 0 Fehler
```

Werte plausibel und anschlussfähig (5.839,6 → 5.795,3 Mrd.; Spread 0,95 →
1,00; F&G 29–34) — **keine Einheitenverschiebung.**

### 72.5 `agent/datenfrische.py` — damit es das nächste Mal auffällt

**Eine Registratur aller fünfzehn Quellen, die ein Prompt tatsächlich liest**,
über alle drei Rollen. Der Kern ist die Unterscheidung zweier Alter:

| | misst | hängt an | Folge |
|---|---|---|---|
| **Datenstand** | wie alt die Information ist | dem **Anbieter** | ein hohes Alter kann völlig richtig sein — die CFTC veröffentlicht freitags |
| **Abrufstand** | wann wir zuletzt erfolgreich nachgesehen haben | **uns** | älter als 2 Tage = **es läuft kein Job** |

> **Ein Anbieter, der nichts Neues hat, ist normal. Ein Job, der nicht läuft,
> ist es nie.** Deshalb wird nur das Abrufalter als Fehler gewertet.

**Vier Urteile, nach Dringlichkeit:** `fehlt` · `abruf` · `daten` · `frisch`.

**Mitgenommen wurden auch die drei größten Quellen, die nicht in
`externe_reihe` stehen** — Terminmarkt (93 % aller Urteile), Kursreihe (jeder
Satz jeder Rolle), Bestand. Sie wegzulassen hieße, ausgerechnet die
wichtigsten herauszuhalten, weil sie in einer anderen Tabelle liegen.

**Drei Abnehmer:** der Tagesjob loggt jede veraltete Quelle als Warnung · der
NB-Export trägt den Abschnitt `datenfrische` · `pruefe_pakete.py --paket
Frische` prüft die Prüfung.

### 72.6 Ein zweiter Fund: die Simulation las eine kaputte Kopie

**`simuliere_kette.py` kopierte drei Dateien einzeln** (`.db`, `-wal`, `-shm`)
in ein **immer gleiches Ziel**. Lag dort noch ein WAL von 08:19 (102 MB) und
die Quelle hatte inzwischen eingecheckt (0 Byte), passten Hauptdatei und
Beileger nicht mehr zusammen:

```
sqlite3.DatabaseError: database disk image is malformed
```

> **Das ist der freundliche Ausgang.** Ein WAL, das zufällig noch lesbar ist,
> wirft keinen Fehler — es lässt die Kette gegen einen **alten Stand** laufen,
> und niemand sieht es.

**Ersetzt durch `Connection.backup()`** — liest über SQLite (das WAL ist
automatisch drin), schreibt **eine** in sich stimmige Datei, braucht keine
Beileger. Danach `PRAGMA integrity_check`, derselbe Maßstab wie beim NB-Export
(der es längst richtig macht).

> ⚠️ **Korrektur an meiner eigenen Meldung von heute Vormittag.** Der Wert
> *„6 Gruppen, 12 Signale"* stammte aus einem Lauf gegen eine Kopie mit
> ebendiesem 102-MB-WAL. Mit sauberer Kopie sind es **4 Gruppen, 8 Signale** —
> Rohstoffe und Absicherung haben in der Entwicklungsdatei keine Kursreihe.
> *0 Fehler, 0 Lücken* gilt in beiden Läufen.

### 72.7 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **940**, alle bestanden (8 neu) |
| Frischeprüfung, **beide Richtungen** | frische Datei **0 von 15** auffällig · stillstehende **15 von 15** |
| leere Datei | meldet `fehlt`, **nicht** `frisch` |
| Vollständigkeit | jedes Merkmal der Rolle G hat einen Anbieter, jeder Anbieter eine Frischeprüfung |
| Gegenprobe | erfundenes Merkmal `wetterdienst` → **gemeldet** |
| Joblauf live | 203 Punkte, 0 Fehler, drei Reihen aufgeholt |
| Scheduler | 19 Jobs, `lagebild_reihen` cron 06:40, Sofortstart |
| freie Namen | 0 |
| Simulation | 4 Gruppen, 8 Signale, 9 Mails, **0 Fehler, 0 Lücken** |

---

## Kapitel 73 — Warum nach jedem Start viele Signale kommen (17.08.2026)

**Nutzerfrage:** *„Gibt es einen Fehler oder Grund, warum weiterhin nach einem
App-Start wieder viele Signale kommen? Funktioniert der Fingerabdruck? Ist es
ein neuer Lauf oder ein Fehler in der Bremse?"*

### 73.1 Die Bremse funktioniert — nachweislich

**Sie ist scharf** (`Basisinfos/config.yaml`, `anlass.aktiv: true`) und
arbeitet. Drei Läufe um 02:58, aus dem Export von 05:07:

| Lauf | hinein | von der Bremse gestoppt | Grund |
|---|---:|---:|---|
| 1 | 5 | **5** | „Faktensatz unveraendert seit 0.2 h (asset)" |
| 2 | 4 | **4** | dito |
| 3 | 41 | **18** von 24 | dito |

Über 7.308 Beobachtungen: **75,8 %** der Spot- und **74,5 %** der
Hebel-Fragen sind Wiederholungen und werden **vor** dem Modellaufruf
verworfen. Der Trichter aus Lauf 3 im Ruhebetrieb:

```
41 Symbole -> 17 Hebel abgeschaltet -> 24 zur Bremse
  -> 18 gestoppt, 6 durch -> Cooldown 4 weg, 2 durch -> 1 Signal
```

**Ein Signal aus 41 Symbolen. Das ist kein Defekt.**

### 73.2 Es ist ein neuer Lauf, kein Fehler in der Prüfung

**Zwei Mechanismen, die sich addieren:**

**Die Bremse stoppt nur, was *identisch* ist.** Nach einer Betriebspause sind
die Kurse gelaufen, der Faktensatz ist echt anders — die Frage ist tatsächlich
neu. Sie greift gegen die 15-Minuten-Wiederholungen *innerhalb* einer
Laufphase (Medianabstand **0,25 h**). Der Fall „gar kein Vorgänger" ist selten:
**78 von 7.308 = 1 %**.

**Beim Start feuert alles auf einmal.** Jeder Job trägt `next_run_time` =
sofort. Das Hebel-Screening läuft sonst alle 15 Minuten und verteilt sich —
beim Start geht eine volle Runde in einem Zug los. Genau das zeigt der
Screenshot: **12 Mails zwischen 08:48 und 08:52**.

> **Der Treiber ist die Betriebszeit, nicht die Logik.**
> Fenster 67,4 h · fehlend 47,3 h · **Ausfall 70,2 %** · längste Lücke 9,99 h.
> Bei 70 % Ausfall verbringt das System die meiste Zeit in dem Zustand, in dem
> jede Frage berechtigt neu ist. **Durchlaufen zu lassen wäre wirksamer als
> jede Verschärfung der Bremse.**

### 73.3 Wo der Hebel läge — und eine Zahl, die falsch im Code stand

| Block | Änderungen | Anteil |
|---|---:|---:|
| **marken** | **1.579** | **59,3 %** |
| bestand | 314 | 11,8 % |
| acht weitere | je 77–117 | zusammen 28,9 % |

> ⚠️ **`agent/anlass.py` und `config.yaml` behaupteten beide 15 %.** Gemessen
> sind es **59,3 %** (1.579 von 2.663). Das war eine Schätzung an der Stelle,
> an der der Nutzer entscheidet — beide Stellen sind korrigiert.

Mit `mindest_bloecke: 1` reicht **dieser eine** kursnahe Block, damit eine
Frage als neu gilt. Er ist damit der größte einzelne Grund, warum die Bremse
durchlässt. Beide Regler stehen in `config.yaml`, **kein Codeeingriff** — ob
ein verschobener Marken-Block eine neue Lage ist oder Rauschen, entscheidet
nur eine Messung mit umgestelltem Regler.

### 73.4 Die Einstellung steht jetzt im Export

**Der Abschnitt zeigte die *Wirkung* der Bremse, nicht ihre *Einstellung*.**
Dass sie scharf ist, ließ sich nur daraus schließen, dass sie gestoppt hat —
stünde sie auf aus, sähe der Abschnitt aus wie „es gab nichts zu sperren".
**Zwei sehr verschiedene Lagen, ein Bild.**

Neu unter `rollen_kette.anlass.einstellungen`: `geltend` (was gilt), `quelle`
(aus der Datei oder Vorgabe im Code) und das Höchstalter aus dem Code.

> **Die Datei allein reicht nicht**, obwohl sie im Git liegt. Sie sagt, was
> eingespielt *wurde* — nicht, was das laufende Notebook geladen hat. Zwischen
> Pull und Neustart liegt bei 70 % Ausfallzeit regelmäßig ein halber Tag.

**Außerhalb des Tabellenzweigs**, damit die Einstellung auch dann erscheint,
wenn es keine Beobachtungen gibt — „keine Zeilen" bei eingeschalteter Sperre
heißt etwas anderes als bei ausgeschalteter.

### 73.5 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | 940, alle bestanden |
| freie Namen | 0 |
| Einstellung ohne Beobachtungstabelle | **erscheint trotzdem** |
| `config.yaml` | Zeilenenden geprüft, einheitlich CRLF, lädt unverändert |
| Quelle je Schlüssel | fünf von fünf aus `config.yaml`, nicht aus der Vorgabe |

---

## Kapitel 74 — Der Zähler, der seit dem Kettenschnitt null meldet (17.08.2026)

### 74.1 Der Widerspruch stand im selben Export

```
signal_volumen_heute : {"spot": 0, "hebel": 0}
llm_aufrufe_heute    : {"gemini": 86, "zai": 41}
spot_signals         : 76 Rohzeilen von heute
```

**Null Signale bei 86 Modellaufrufen** — und die Urteile lagen als Rohzeilen
in derselben Datei. Die Zahlen widersprachen einander, und niemandem fiel es
auf: **eine Null ist kein Fehler, sie sieht aus wie ein ruhiger Tag.**

**Ursache**, dieselbe wie am 14.08. auf der Fernsteuerkarte, nur eine Stelle
weiter: `count_real_signals_today()` und `count_real_hebel_signals_today()`
filtern auf `groq_raw_response IS NOT NULL` — eine Spalte, die
**ausschließlich die alte Kette** geschrieben hat. Die neue schreibt
`quelle_kette = 'rollen'` mit `modell = gemini-3.1-flash-lite`.

> **Die Bedingung kann strukturell nie mehr wahr werden.**

### 74.2 Die alten Zähler bleiben — unverändert

**Sie sind nicht falsch.** Sie zählen die alte Kette, und die ist tot (0/180).
Sie umzubauen hieße, den Budgetpfad in `signal_batch.py` mitzuverbiegen, der
auf ihrer heutigen Bedeutung steht.

> **Ein toter Zähler wird ersetzt, nicht umdefiniert.**

Im Export heißen sie jetzt so, wie sie zählen: `alte_kette_spot`,
`alte_kette_hebel`, `alte_kette_marktscan_writeups` — daneben `rollen_kette`.

### 74.3 Eine Zählung, zwei Abnehmer

`db.zaehle_rollen_urteile_heute()` — **die eine Definition.** Die Zählung
stand bis heute **inline in `remote/status.py`**; der Export hätte sie
kopieren müssen. Zwei Kopien einer Zählung sind zwei Stellen zum
Auseinanderlaufen — wie `KURSREIHENBLOECKE` gegen den Matrixtest (67 % gegen
89 % für dieselbe Gruppe, Kap. 70.4).

**Gegen die echten Produktionszeilen geprüft — exakte Übereinstimmung:**

| | gezählt | erwartet | Hauptfenster |
|---|---:|---:|---:|
| Urteile | **76** | 76 | 76 |
| davon Hebel | **43** | 43 | 43 |
| davon Spot | 33 | 33 | — |
| mit Handlung | **48** | 48 | 48 |

**Neu mitgezählt: die Aufteilung nach Aktion.** Sie war bisher nur zu
bekommen, indem 3.467 Rohzeilen aus dem Export nachgezählt wurden.

| Aktion | | |
|---|---:|---:|
| **ERÖFFNEN + KAUFEN + NACHKAUFEN** | **45** | **59 %** |
| HALTEN | 28 | 37 % |
| REDUZIEREN | 3 | 4 % |

### 74.4 Und die Prüfung, die den Widerspruch gefunden hätte

`pruefe_export_standard.py` meldet ab jetzt: **Modellaufrufe ohne Urteile.**
Ein Aufruf ohne Ergebnis ist entweder ein toter Zähler oder eine ausgefallene
Kette — beides gehört gemeldet.

**Vier Fälle gegengeprüft:**

| Fall | Ausgabe |
|---|---|
| der Fall von heute früh | ⚠️ *„127 Modellaufrufe, aber NULL Urteile"* |
| Zähler lebt | „76 Urteile (43 Hebel / 33 Spot), 48 mit Handlung (63 %)" |
| alte Datei, Spalte fehlt | ⚠️ *„nicht zaehlbar: Spalte quelle_kette fehlt"* |
| **ruhiger Tag** | **kein Befund** |

> ⚠️ **Mein erster Gegentest war wertlos** und meldete in allen vier Fällen
> dasselbe: er rief `main()` im selben Prozess auf, das seinen Pfad aus
> `sys.argv` nimmt — gelesen wurde also jedes Mal der echte Export. Zum
> wiederholten Mal derselbe Typ: **die Eingabe stellte den Fall nicht her.**

### 74.5 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | 940, alle bestanden |
| gegen echte Produktionszeilen | 76 / 43 / 33 / 48 **exakt** |
| leere Datei | meldet `nicht_verfuegbar`, **nicht** 0 |
| Exportprüfer | 4 Fälle, 3 Befunde, ruhiger Tag stumm |
| Fernsteuerkarte | rechnet mit derselben Funktion |
| freie Namen | 0 |
| Simulation | 4 Gruppen, 8 Signale, **0 Fehler, 0 Lücken** |

---

## Kapitel 75 — Gestaktes galt als nicht vorhanden (17.08.2026)

**Nutzerfund an einer echten SOL-Mail:** *„SOL wird schon lange gehalten"* —
die Mail sagte oben **„SOL ist nicht im Bestand"** und zwanzig Zeilen tiefer
**„Bestehende Position: HALTEN, +0.43 R"**.

### 75.1 Beide Sätze stimmten — und beide kamen aus derselben Lücke

Der Beweis steht im eigenen Sync-Code, live gegen den Account verifiziert
(`importer/bitpanda_avg_cost.compute_staked_quantities`):

> *„gestakte Bestände sind über die normalen Wallet-Endpunkte **strukturell
> nicht sichtbar** — Bitpanda bucht einen stake-Transfer als **ABGANG** aus
> der normalen Wallet."*

**`quantity` ist also der FREIE Bestand, `staked_quantity` kommt ADDITIV dazu.
Ein vollständig gestakter Wert steht mit Menge 0 in der Tabelle.**

> **Im Export haben 23 von 56 Zeilen die Menge 0.**

**Die alte Kette hat es an sieben Stellen richtig gemacht** —
`(h.quantity or 0) + (h.staked_quantity or 0) > 0` in `krypto/analyst`,
`multi_asset_batch`, `signal_batch`, `risk_gate`, `db`, `aktien/analyst`,
`rohstoff/analyst`. **Beim Umbau ist genau diese Addition verlorengegangen.**

### 75.2 Drei Stellen, eine Wurzel

| | Stelle | Wirkung |
|---|---|---|
| 1 | `rollen_eingabe.bestand()` las nur `quantity` | das Modell hörte **„nicht im Bestand"** und entschied über einen Neukauf |
| 2 | `rollen_lauf` übergab `menge=quantity` an `verkaufsrechnung.rechne`, die das Gestakte **selbst noch einmal abzieht** | `frei = 0 − gestakt` → **kein Verkaufsauftrag**, obwohl gehalten |
| 3 | `backward_tracking`: `SELECT ... WHERE quantity > 0` | `ist_bestand = False` → die Führung galt als **bloße Signalverfolgung** |

> ⚠️ **Derselbe Fehlertyp wie am 15.08., nur eine Spalte weiter:** der
> Ausführungspfad kannte das Staking, die **Fakten, auf die das Modell
> antwortet**, kannten es nicht.

**Nachgewiesen am gemeldeten Fall:**

```
vorher   SOL ist nicht im Bestand.
nachher  SOL ist bereits im Bestand: 839 EUR investiert,
         aktuell 811 EUR wert - 28 EUR im Minus (-3.4 %).
```

Und die Verkaufsrechnung, die vorher gar nichts ergab:

| | vorher | nachher |
|---|---|---|
| voll gestakt | kein Auftrag | kein Auftrag — **richtig**, gestaktes ist nicht frei |
| **halb gestakt** | **kein Auftrag** | **10 Stück, 649 EUR** |
| frei | 20 Stück | 20 Stück |

Und das Protokoll nennt jetzt den Unterschied: *„VERKAUFEN vollständig
gestakt, nicht frei verkäuflich"* statt *„VERKAUFEN ohne Bestand"* — zwei sehr
verschiedene Gründe hatten ein Wort.

### 75.3 Wie weit es reicht

**39 von 76 Urteilen des 17.08. liefen auf Symbolen mit Menge 0** — davon
**27 Einstiege** (20 ERÖFFNEN, 7 KAUFEN). Das sind **60 % aller Einstiege des
Tages**.

> **Noch nicht beziffert, wie viele der 23 Nullzeilen gestakt und wie viele
> wirklich verkauft sind** — der Export trug `staked_quantity` bis heute
> nicht. Er trägt sie ab jetzt. SOL ist durch den Nutzer bestätigt.

**Das ist eine ernstzunehmende Spur zur Einstiegsquote**, an der wir seit
Tagen sitzen: das Modell empfahl zu kaufen, was der Nutzer bereits hält.

### 75.4 Gehalten oder nur verfolgt — jetzt steht es dran

**Nutzervorgabe:** *„es sollte unterscheidbar sein, was tatsächlich gehalten
wird und was nur als Signal getrackt wird — das brauchen wir beim Kauf, Halten
und Verkauf, sonst verwirrt der Inhalt."*

```
mit Bestand   Bestehende Position:
ohne          Verfolgter Einstiegsvorschlag (NICHT im Bestand):
```

**Die Unterscheidung gab es seit dem 13.08.** — `ist_bestand`, entstanden aus
dem Nutzersatz *„diese Aktionen sind teilweise fiktiv"* (von 45
Signal-Symbolen lagen 28 gar nicht im Bestand). **Sie stand nur nirgends in
der Mail.**

### 75.5 R übersetzt — die Rechnung war seit dem 12.08. da

`bewerte()` rechnet `stand_prozent` und `mfe_prozent` aus, mit genau dieser
Begründung im Kommentar: *„R ist eine interne Einheit; Prozent versteht jeder."*
Die **Sammelmail** hat den Umstieg damals vollzogen, die **Einzelmail nicht**.

```
vorher   Stand   +0.43 R, hoechster Buchgewinn +0.41 R
nachher  Stand   +1.4 % (+0.43 R) - Hoechststand noch nicht nachgefuehrt
```

> **Der höchste Buchgewinn kann nicht kleiner sein als der aktuelle Stand.**
> Kein Rechenfehler: `mfe_r` kommt aus dem Backward-Tracking (letzter Lauf
> 04:00), `stand_r` aus dem aktuellen Kurs. Aber es liest sich als
> Unmöglichkeit — und dann glaubt der Leser der ganzen Zeile nicht mehr. Also
> wird die Alterung **benannt statt gedruckt**.

Und der Trailing-Stop sagt jetzt, was er meint: *„löst erst aus, wenn der
Gewinn so groß ist wie das Risiko (+1.0 R)"*.

### 75.6 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **942**, alle bestanden (2 neu) |
| ⚠️ zwei bestehende Prüfungen **schlugen zuerst fehl** | sie führten kein `ist_bestand` — der Test prüfte ab der Änderung einen anderen Fall als den, den er beschreibt. Behoben, nicht umgangen |
| gemeldeter Fall | „nicht im Bestand" → **„bereits im Bestand: 839 EUR"** |
| Gegenprobe | ein Symbol mit Menge 0 **und** ohne Staking bleibt „nicht im Bestand" |
| Verkaufsrechnung | drei Fälle, halb gestakt von **0 auf 10 Stück** |
| beide Überschriften | im Test belegt, in beide Richtungen |
| freie Namen | 0 · Zahlenprüfer 9/9 |
| Simulation | 4 Gruppen, 8 Signale, **0 Fehler, 0 Lücken** |

---

## Kapitel 76 — Vier Widersprüche aus einer Mail (17.08.2026)

Alle vier stammen aus **einer** SOL-Mail, die der Nutzer Zeile für Zeile
durchgegangen ist. Drei davon waren keine Anzeigefehler.

### 76.1 A2 — das Ziel lag hinter der Mauer, die dieselbe Mail nannte

```
Der naechste Widerstand liegt ... bei 66.55 EUR (5-mal beruehrt).
+ Widerstand bei 66.55 EUR bietet klares Ziel              [Beleg]
Take-Profit  67,67 bis 68,53 EUR  (CRV 2,0 - kein Widerstand in Reichweite)
```

**`entscheidungsrechnung._ziel()` kann das Ziel kurz VOR den nächsten
Widerstand legen** — der Praxisstandard, eigener Regelzweig, eigene
CRV-Ausweisung, ausführlich begründet.

> ⚠️ **Der Parameter dafür heißt `widerstand` — und kein einziger Aufrufer hat
> ihn je gefüllt.** Also lief immer der Zweig *„kein Widerstand in
> Reichweite"*. Die Logik war gebaut und tot.

**An 39 echten Kursreihen gemessen: 39 von 39 Symbolen haben einen Widerstand
in Reichweite.** Der Zweig war also nicht selten falsch, sondern **immer**.

**Was sich für SOL ändert:**

| | Ziel | CRV | Regel |
|---|---|---:|---|
| vorher | 71,03–71,69 EUR | 2,00 | kein Widerstand in Reichweite |
| **nachher** | **65,90–66,55 EUR** | **0,42** | vor dem Widerstand bei 67 EUR (5-mal berührt) |

> **Eine unbequeme Zahl, und sie gehört so hingeschrieben.** Der Trade trug nie
> CRV 2,0 — er trug 0,42, und die Mail versprach das Doppelte.
> **Gesperrt wird deswegen nichts:** `crv_erreicht=False` erzeugt eine
> sichtbare Warnzeile, die Entscheidung bleibt beim Nutzer.

**Eine Ermittlung, zwei Abnehmer.** `lagebeschreibung.niveaus_werte()` liefert
die Marken als Zahlen; `_niveaus()` schreibt seinen Satz aus **demselben**
Ergebnis. Eine zweite Ermittlung wäre die nächste Stelle zum Auseinanderlaufen
(Kap. 70.4).

> ⚠️ **Die Zahlen dürfen nicht als Faktenblock mitzählen.** Anlassfilter und
> Mindestkriterien zählen **Blöcke von Sätzen**; ein Eintrag mit Zahlen darin
> hätte beide Messungen verschoben. Deshalb `_marken_werte` mit Unterstrich
> und `nur_saetze()` davor.

### 76.2 A3 — 34 gegen 36, vier Zeilen auseinander

```
Von hundert solchen Einstiegen erreichen erfahrungsgemaess 34 das Ziel ...
--> Traegt sich NICHT: 36 erreichen das Ziel, noetig waeren 73.
```

Beide Zahlen sind richtig und meinen Verschiedenes: **34 ist die
Erfahrungsrate, 36 die um die eigenen Fälle angepasste Schätzung**
(`geschrumpft()` zieht sie bei wenigen Fällen zur Erfahrungsrate hin). Die
Entscheidung steht auf der angepassten — **richtig so, das ist die bessere
Schätzung.**

> **Falsch war die Beschriftung:** *„Gemessen an der Erfahrungsrate"* stand
> unter einer Zahl, die eben nicht die Erfahrungsrate ist. Wer beides liest,
> hält eine der zwei Zeilen für einen Fehler — und weiß nicht, welche.

```
nachher   Die 36 sind die Erfahrungsrate von 34, angepasst um 3 eigene
          Faelle - fuer eine eigene Zahl sind es zu wenige.
```

### 76.3 A4 — zwei Zahlen unter einem Wort

„Die Unterstützung" stand dreimal in der Mail: **zweimal bei 63,44 EUR**
(unsere Markenrechnung) und **einmal bei 63,64 EUR** (der Widerlegungspreis
des Modells).

**Beide bleiben stehen.** Die Zahl des Modells ist seine Bedingung — sie zu
überschreiben hieße, sein Werturteil zu verändern. Was fehlte, war die
Einordnung:

```
Unsere Markenrechnung sieht die Unterstuetzung bei 63,44 EUR
(4-mal beruehrt) - das Modell nennt 63,64 EUR. Zwei Zahlen, zwei Quellen.
```

> ⚠️ **Meine erste Schwelle war 0,5 % — und schwieg ausgerechnet im gemeldeten
> Fall:** 63,44 gegen 63,64 sind 0,32 %. Auf einen Stop, der 2,5 % entfernt
> liegt, ist das ein Achtel des Risikos, keine Rundung. Jetzt ein Promille.

### 76.4 A5 und B1 — die Alterung wird benannt

```
vorher   Stand   +0.43 R, hoechster Buchgewinn +0.41 R
nachher  Stand   +1.4 % (+0.43 R) - Hoechststand noch nicht nachgefuehrt
```

Der höchste Buchgewinn kann nicht kleiner sein als der aktuelle Stand. Kein
Rechenfehler: `mfe_r` kommt aus dem Backward-Tracking (04:00), `stand_r` aus
dem aktuellen Kurs. **Aber es liest sich als Unmöglichkeit — und dann glaubt
der Leser der ganzen Zeile nicht mehr.**

### 76.5 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **957**, alle bestanden — **15 neu unter `--paket Mail`** |
| A2 | ohne Marke · mit Marke · CRV ausgewiesen · LONG · SHORT · ohne Marken None · Satz und Zahl aus einer Ermittlung |
| A3 | Erklärung da · Entscheidung unverändert |
| A4 | beide Zahlen mit Quelle · **bei gleicher Zahl stumm** |
| A5 / B1 | Alterung benannt · echter Höchststand bleibt · Prozent vor R |
| Abgrenzung | Markenwerte zählen **nicht** als Faktenblock |
| an echten Reihen | **39 von 39** Symbolen haben einen Widerstand in Reichweite |
| freie Namen | 0 · Zahlenprüfer 9/9 |
| Simulation | 4 Gruppen, 8 Signale, **0 Fehler, 0 Lücken** |

---

## Kapitel 77 — A6: das Modell hat sich die Zahl selbst ausgedacht (17.08.2026)

**Der Verdacht aus der Mailprüfung ist bestätigt — und er ist systematisch.**

### 77.1 Der Befund

In der SOL-Mail stand im **Belegblock**:

```
- Umsatzvolumen im 35. Perzentil deutet auf fehlendes Momentum hin  [gering]
```

Im **Faktenblock derselben Mail** stand *„Volumen das 0,4-fache des Mittels
(Vortag)"* — kein Perzentil. Und `faktenblock.kern()` sagt es ausdrücklich:

> *„Das Perzentil erscheint **NICHT** im Text — es bestimmt nur das
> Urteilswort."*

**Gemessen über alle gespeicherten Belege der Rollen-Kette:**

```
484 Signale, 1.834 Belege
14 Befunde in 14 verschiedenen Symbolen  (0,76 %)
```

| Symbol | Beleg |
|---|---|
| MORPHO | *„Handelsvolumen im 100. Perzentil **der letzten 400 Tage**"* |
| KAITO | *„Umsatzvolumen im 92. Perzentil deutet auf Kapitulationsphase hin"* |
| MON | *„Umsatzvolumen 6.0 % (84. Perzentil) deutet auf Liquidität hin"* |
| VIRTUAL | *„Umsatzvolumen im 3. Perzentil (außergewöhnlich ruhig)"* |

> ⚠️ **„der letzten 400 Tage" kommt in keinem unserer Sätze vor.** Das Modell
> hat nicht nur eine Zahl erfunden, sondern auch ein Messfenster dazu.

### 77.2 Was hier passiert ist

**Es ist die Umkehrung von R-T12.** Wir geben ein **Etikett**
(GUENSTIG/UNGUENSTIG) und halten die Zahl zurück — weil der Nutzer rohe
Perzentile abgelehnt hatte (*„Perzentil 74 war genau der Einwand"*). Das
Modell rechnet aus dem Etikett eine plausible Zahl **zurück** und schreibt sie
als Messung hin.

**Warum das mehr ist als ein Schönheitsfehler:** die Belege sind der Block,
den die Mail als **Beweis** präsentiert — mit Gewicht und gezählt als
„unabhängige Faktoren". Eine erfundene Messung darin ist eine **Behauptung mit
Siegel**, und sie ist nicht als solche erkennbar: *„im 92. Perzentil der
letzten 400 Tage"* liest sich exakt wie unsere echten Sätze.

### 77.3 Der Eingriff — ein Satz, an der Stelle, wo es passiert

```
Erfinde nichts. Zu Schwankung, Kursentwicklung und Volumen bekommst du
KEIN Perzentil, sondern ein Urteilswort - nenne dort auch keines.
```

> **„Erfinde nichts" stand schon da** — seit jeher, im selben Absatz. Es hat
> nicht getragen. **Eine allgemeine Ermahnung schlägt keine konkrete Lücke;**
> die Stelle muss benannt werden.

`PROMPT_STAND` → **`2026-08-17c`**. Ohne den Sprung wären Urteile vor und nach
der Änderung nicht trennbar.

**Nicht gemacht — und warum:**

| Weg | verworfen, weil |
|---|---|
| dem Modell das Perzentil geben | widerspricht der Entscheidung, die der Nutzer selbst getroffen hat |
| den Beleg löschen | ein deterministischer Eingriff in das Werturteil des Modells |
| nur beobachten | die Zahl steht in der Mail und liest sich wie eine Messung |

### 77.4 `pruefe_belege_gegen_fakten.py`

**Es prüft nicht jede Zahl gegen die Fakten des Laufs** — die werden je Signal
nicht gespeichert und ließen sich ohne Ankertagsverletzung nicht
rekonstruieren. Es prüft die Fälle, in denen wir **ohne den Lauf zu kennen**
wissen, dass es die Zahl nicht gegeben haben kann.

> **Keine Fehlalarme, dafür unvollständig — in dieser Reihenfolge.**

**`auch_woanders` ist der ganze Trick.** Die Schwankung *hat* ein Perzentil —
im Lagebild, für den Markt (*„Bitcoin-Volatilität im 0. Perzentil"*). Ein
Beleg, der das zitiert, ist korrekt, und ihn zu melden wäre ein Fehlalarm.
**Von 33 Funden der ersten Promptprüfung waren 31 genau solche.**

Die Liste steht in **`faktenblock.PERZENTIL_NUR_INTERN`** — neben dem Code,
der die Perzentile zurückhält, nicht im Werkzeug.

### 77.5 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **968**, alle bestanden — **11 neu unter `--paket Belege`** |
| Selbsttest des Werkzeugs | **9/9**, beide Richtungen |
| erkannt | der gemeldete Satz · die erfundene Fensterlänge · die Zählung über viele Zeilen |
| **nicht** erkannt (richtig so) | Finanzierungsrate · Marktvolatilität · unser eigener Volumensatz · leer/None |
| Herkunft der Liste | aus `faktenblock`, nicht kopiert |
| Promptstand | mitgezogen, und die bestehende Prüfung darauf nachgeführt |
| Export | neuer Abschnitt `belege_gegen_fakten` |
| freie Namen · Zahlenprüfer · `pruefe_phase1` | 0 · 9/9 · bestanden |
| Simulation | 4 Gruppen, 8 Signale, **0 Fehler, 0 Lücken** |

**Ob die Promptzeile trägt, sagt der nächste Export** — die Quote steht
jetzt in jedem drin, mit dem Promptstand daneben.

---

## Kapitel 78 — Der Nutzertext trennt sich vom Modelltext (17.08.2026)

### 78.1 „Was soll mir ‚im gewohnten Bereich' sagen?"

**Die Nutzerfrage war berechtigt, und zwar strukturell.** `_einordnung()`
kennt drei Wörter mit Schwellen bei 90 und 10:

```
>= 90   "aussergewoehnlich hoch"
<= 10   "aussergewoehnlich niedrig"
sonst   "im gewohnten Bereich"
```

> **79 von 101 möglichen Perzentilwerten landen auf „im gewohnten Bereich".**
> Der Satz ist per Konstruktion in vier von fünf Fällen derselbe — ein
> **konstantes Feld (R-T6)**, genau das, was beim Regime entfernt wurde
> (2.549 von 2.549 identisch). In der gemeldeten SOL-Mail standen **vier**
> Perzentilzeilen, **alle vier** „im gewohnten Bereich".

**⚠️ Die Einordnung war nie für den Nutzer gebaut.** R-T11 („kein Perzentil
ohne Einordnung") entstand für das **Modell**: ein Sprachmodell kann mit einer
nackten Zahl nicht umgehen. Sie ist in die Mail durchgerutscht, weil Nutzer-
und Modelltext aus denselben Sätzen gebaut werden.

**Die Antwort ist deshalb nicht besser übersetzen, sondern weglassen.**

```
vorher   Wie weit sie auseinanderliegen, steht im 71. Perzentil ... - im gewohnten Bereich.
         Die Finanzierungsrate steht im 77. Perzentil ... - im gewohnten Bereich.
         Der Anteil der Konten steht im 72. Perzentil ... - im gewohnten Bereich.
         Gemessen an 730 Tagen steht diese Bewegung im 44. Perzentil - im gewohnten Bereich.

nachher  Alle 4 Angaben zur Positionierung liegen im gewohnten Bereich.
```

**Was auffällt, bleibt wortgleich stehen** — mit Zahl, weil sie dann etwas
bedeutet. Dann heißt der Sammelsatz *„3 weitere …"* statt *„Alle 3 …"*, sonst
wüsste der Leser nicht, ob er etwas übersehen hat.

> ⚠️ **Das Modell behält alles.** Der Filter sitzt in `signal_mail`, nicht in
> `lagebeschreibung`, `marktlage` oder `positionierung` — geprüft. Dem Modell
> die Einordnung wegzunehmen wäre eine Änderung seiner Grundlage, keine
> Darstellungsfrage.

### 78.2 Die Herkunft je Abschnitt

**Nutzervorschlag:** *„je eMail-Bereich die tatsächliche Quelle angeben —
eigene Berechnung deterministisch, oder nur Daten einer Datenquelle, LLM1 und
LLM2."*

**Umgesetzt auf der Achse „wie wissen wir das", nicht „wer hat geredet":**

```
--- 1. DER WERT ---
    [GEMESSEN - Kurse und Fremdquellen]
--- 2. DIE POSITION ---
    [GERECHNET aus Ihren Zahlen, Zone und Stop teils aus einer Modellangabe]
--- 3. DAS URTEIL DES MODELLS ---
    [BEHAUPTET - Rolle Haendler]
--- 4. EINORDNUNG ---
    [GERECHNET aus der gemessenen Erfahrungsrate]
--- 5. GEGENPRUEFUNG (zweites Modell) ---
    [BEHAUPTET - andere Quelle: Terminmarkt und Kette]
```

**Warum nicht „LLM1 / LLM2":** der Modellname sagt, *wer* geredet hat — nicht,
*wie viel es wert ist*. Und die beiden Modelle sind nicht dieselbe Art
Aussage: Rolle BC fällt ein **Urteil**, Rolle G erhebt einen **Einwand aus
einer anderen Quelle**. Sie zu Geschwistern zu machen wäre das Gegenteil des
Rollenumbaus.

> **GEMISCHT ist der ehrliche Fall.** Der Stop ist arithmetisch exakt **und**
> ruht auf einem Prozentsatz, den eine Regel aus einer Modellaussage abgeleitet
> hat. Ihn „eigene Berechnung" zu nennen wäre falsche Sicherheit — genau das,
> was die Angabe verhindern soll.

### 78.3 Ein Fund am Rande, der A6 korrigiert

**Der Export nach Promptstand aufgeschlüsselt:**

| Promptstand | Belege | erfundene Perzentile |
|---|---:|---:|
| 2026-08-12 · 16 · 16b | 1.484 | **0** |
| **2026-08-17b** | 272 | **19 (6,99 %)** |
| 2026-08-17c (nach dem Neustart) | 46 | 2 (4,35 %) |

**Das Verhalten beginnt exakt mit 17b** — dem Stand, der Krypto-Spot den
**Umschlag** gegeben hat. Und dessen Satz trägt ein Perzentil:

```
Vom gesamten Umlaufbestand dieses Werts wechselten in den letzten
24 Stunden 6,0 % den Besitzer; das liegt im 84. Perzentil ...
```

Der Beleg des Modells dazu lautete:

```
MON: Umsatzvolumen 6.0 % (84. Perzentil) deutet auf Liquiditaet hin
```

> ⚠️ **Beide Zahlen sind UNSERE.** Das Modell hat sie nicht erfunden — es hat
> sie **umbenannt**: aus „Umlaufbestand, der den Besitzer wechselt" wurde
> „Umsatzvolumen". Und das kollidiert mit dem Volumenblock, der direkt daneben
> steht und bewusst **kein** Perzentil hat.

**Meine Schlussfolgerung von Kapitel 77 war damit zur Hälfte falsch:** es ist
überwiegend eine **Namensverwechslung**, keine freie Erfindung. Frei erfunden
bleiben die Fensterlängen („der letzten 400 Tage" — die gibt es nirgends).

**Folge für den Eingriff:** die Promptzeile aus 17c behandelt ein Symptom. Der
Ursachenweg wäre, den Umschlagsatz so zu benennen, dass er nicht mit dem
Volumenblock verwechselt werden kann. **Zur Entscheidung vorgelegt, nicht
gebaut** — er ändert den Prompt ein drittes Mal an einem Tag.

### 78.4 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **981**, alle bestanden — **13 neu unter `--paket Lesbar`** |
| das Argument selbst | 79 von 101 Werten heißen „im gewohnten Bereich" — nachgezählt, nicht behauptet |
| vier Sprachfälle | alle · weitere · Singular · nichts |
| **das Modell behält alles** | `ohne_gewohntes` kommt in keiner Faktendatei vor — geprüft |
| Herkunft | sechs Abschnitte · kein Modellname · gemischter Fall benannt |
| freie Namen · Zahlenprüfer · Belegprüfer · Phase 1 | 0 · 9/9 · 9/9 · bestanden |
| Simulation | 4 Gruppen, 8 Signale, **0 Fehler, 0 Lücken** |

---

## Kapitel 79 — Der Umschlag bekommt ein Hauptwort (17.08.2026)

### 79.1 Die Ursache statt des Symptoms

**Kapitel 77 nannte es eine Erfindung. Es war eine Umbenennung.**

```
unser Satz:  Vom gesamten Umlaufbestand ... wechselten in den letzten
             24 Stunden 6,0 % den Besitzer; das liegt im 84. Perzentil ...
das Modell:  MON: Umsatzvolumen 6.0 % (84. Perzentil) deutet auf
             Liquiditaet hin
```

**Beide Zahlen sind unsere.** Und „Umsatzvolumen" ist der Name des Blocks
direkt daneben — der bewusst **kein** Perzentil hat.

| Promptstand | Belege | Perzentile zu einer Größe ohne Perzentil |
|---|---:|---:|
| 12.08. · 16. · 16b | 1.484 | **0** |
| **17b** (Umschlag kam dazu) | 272 | **19 (6,99 %)** |

**Der Zusammenhang ist nicht zu übersehen.**

### 79.2 Warum der alte Satz einlud, ihn umzubenennen

**Er hatte kein eigenes Hauptwort.** Er begann mit *„Vom gesamten
Umlaufbestand"*, und das Perzentil hing an einem **„das"** auf einen
Nebensatz. Wer daraus zitiert, muss sich selbst einen Namen dafür suchen — und
der naheliegende stand zwei Zeilen weiter oben.

**Die Abhilfe ist ein Hauptwort:**

```
vorher   Vom gesamten Umlaufbestand dieses Werts wechselten in den letzten
         24 Stunden 6,0 % den Besitzer; das liegt im 84. Perzentil der
         letzten 120 Messungen - im gewohnten Bereich.

nachher  Der Umschlag dieses Werts betraegt 6,0 %: so viel vom
         Umlaufbestand hat binnen 24 Stunden den Besitzer gewechselt.
         Dieser Umschlag liegt im 84. Perzentil der letzten 120
         Messungen - im gewohnten Bereich.
```

Drei Änderungen, jede mit einem Zweck:

| | |
|---|---|
| **„Der Umschlag"** als Subjekt | ein benanntes Ding, kein Vorgang |
| **„Dieser Umschlag liegt im …"** | das Perzentil hängt an DIESEM Wort, nicht an einem „das" |
| **„vom Umlaufbestand"** | der Bezug steht dabei — der Volumenblock misst gegen den eigenen Durchschnitt, der Umschlag gegen den Umlaufbestand |

**Und das Wort „Umsatz" kommt darin nicht mehr vor** — es gehört dem Block
nebenan.

**Die beiden nebeneinander, wie das Modell sie liest:**

```
Der Umschlag dieses Werts betraegt 6,0 % ... Dieser Umschlag liegt im
84. Perzentil der letzten 120 Messungen - im gewohnten Bereich.

Volumen      das 0,4-fache des Mittels                MITTEL
  Wie viel heute gehandelt wird, verglichen mit den letzten 20 Tagen.
```

`PROMPT_STAND` → **`2026-08-17d`**. Die Zeile aus 17c bleibt — sie schadet
nicht und deckt den Rest.

### 79.3 Der Prüfer heißt jetzt richtig

**Meine erste Deutung war zur Hälfte falsch, und das steht jetzt im Werkzeug**
— nicht nur im Umbauplan:

> „Perzentile zu Größen, die keines haben" statt „erfundene Perzentile".

**Der Befund bleibt trotzdem ein Befund:** zu dieser Größe gibt es kein
Perzentil, und der Leser kann die beiden nicht auseinanderhalten. **Frei
erfunden bleiben die Fensterlängen** („der letzten 400 Tage" — die gibt es
nirgends).

### 79.4 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **988**, alle bestanden — **7 neu (A6b)** |
| der neue Satz | Hauptwort · Perzentil hängt daran · Bezug genannt · **„Umsatz" kommt nicht vor** |
| der Block daneben | hat weiterhin **kein** Perzentil — sonst hätte die Umbenennung eine zweite Quelle |
| Prüfer, beide Richtungen | „Umschlag im 84. Perzentil" **erlaubt** · „Umsatzvolumen (84. Perzentil)" **gemeldet** |
| Promptstand | mitgezogen, bestehende Prüfungen nachgeführt |
| freie Namen · Zahlenprüfer · Belegprüfer · Phase 1 | 0 · 9/9 · 9/9 · bestanden |
| Simulation | 4 Gruppen, 8 Signale, **0 Fehler, 0 Lücken** |

> **Offen und nicht angefasst:** die Mail mischt zwei Zahlenschreibweisen —
> „2,3 %" aus dem Faktenblock neben „−1.2 %" aus der Lagebeschreibung. Das
> betrifft viele Sätze auf einmal und damit den Prompt; getrennt zu
> entscheiden.

---

## Kapitel 80 — Eine Zahlenschreibweise (17.08.2026)

### 80.1 Was daran gefährlich war — die Prüfung vorab

**Nutzervorgabe:** *„prüfe aber vorher, ob es Nebenwirkungen gibt."* Zu Recht:
die Fakten gehen in denselben Text, den drei Wächter und vier Prüfwerkzeuge
lesen.

| Leser | Muster | Urteil |
|---|---|---|
| `pruefe_zahlen_in_prompts.ZAHL` | `-?\d+(?:[.,]\d+)?` | ✓ kennt **beide** |
| `gegenpruefer_rollen._ZAHL` | `[.,]` + `float(roh.replace(",", "."))` | ✓ normalisiert selbst |
| `waechter_zuspitzung._BEZUG` | `im (\d+)\. perzentil` | ✓ **Ordnungszahl**, nicht betroffen |
| `pruefe_belege_gegen_fakten` | `(\d{1,3})\.\s*Perzentil` | ✓ dito |
| Paketprüfungen | prüfen **Wörter**, nicht Zahlenformate | ✓ |
| **`pruefe_pakete` „übergenau"** | `\d{4,}\.\d{3,}` | ⚠️ **wäre still blind geworden** |

> **⚠️ DER ORDNUNGSPUNKT IST DIE FALLE.** „im 84. Perzentil" ist kein
> Dezimalpunkt. Ein Ersetzen über dem Satz macht daraus „im 84, Perzentil" und
> zerstört nebenbei zwei Wächtermuster. Deshalb formatiert `schreibweise.de()`
> die **Zahl** und bekommt nie einen Satz zu sehen.

### 80.2 Eine bestehende Falle, gefunden beim Hinsehen

```python
f"Die Netto-Liquiditaet ... betraegt {jetzt:,.0f} Mrd. USD und liegt
  damit {betrag:.1f} % {richtung} ihrem Stand ..."
  .replace(",", ".")        # <- ueber dem GANZEN Satz
```

**Das tat nur das Richtige, solange der Satz kein zweites Komma enthielt** —
genau die Falle, an der die Betragsformatierung am 14.08. schon einmal
gescheitert ist. Behoben.

### 80.3 Vier Kopien derselben Zeile

```
faktenblock._de          Vorgabe 0 Stellen
ausstiegsrechnung._de    Vorgabe 2 Stellen
trefferbilanz._de        Vorgabe 1 Stelle
signal_mail.eur          Vorgabe 0 Stellen
```

**Vier Definitionen desselben Begriffs** — und drei Module, die gar keine
hatten und deshalb englisch schrieben. Jetzt `agent/schreibweise.py`, einmal;
die Vorgabe für die Stellenzahl bleibt am Verwendungsort, die Rechnung nicht.

**35 Formate umgestellt** — 22 in `lagebeschreibung`, 10 in `marktlage`,
3 in `positionierung`.

```
vorher   Kursentwicklung im selben Rahmen: 5 Tage -1.2 %, 20 Tage +1.6 %
nachher  Kursentwicklung im selben Rahmen: 5 Tage -1,2 %, 20 Tage +1,6 %

         Die Netto-Liquiditaet betraegt 5.840 Mrd. USD und liegt damit
         2,5 % ueber ihrem Stand von vor 26 Wochen.
         ... betraegt +0,95 Prozentpunkte; das liegt im 95. Perzentil ...
```

### 80.4 Eine Prüfung, die den Quelltext las statt das Ergebnis

**Zwei Prüfungen sind fehlgeschlagen — beide zu Recht, eine davon aufschlussreich:**

```python
"maketrans" in _quelltext(datei)        # <- suchte ein WORT im Code
```

Sie fiel, weil die vier Kopien durch eine gemeinsame Funktion ersetzt wurden:
**das Verhalten war richtig, die Prüfung sah nur das falsche Wort.**

> Eine Prüfung, die den Quelltext liest statt das Ergebnis, fällt bei jeder
> Aufräumarbeit an — und wird dann *angepasst* statt ernstgenommen.
> **„Katalog ist keine Messung."**

Ersetzt durch fünf Messungen: jede Formatierung muss `1234.5` als **„1.234,50"**
liefern, und alle vier Module müssen dieselbe Funktion importieren.

### 80.5 Was der Nutzer erwarten muss

**`PROMPT_STAND` → `2026-08-17e`.** Der Faktentext ändert sich, also auch das,
was das Modell liest.

> ⚠️ **Die Anlassbremse ist für eine Runde offen.** Der Fingerabdruck ist der
> Prompttext selbst; ändert sich seine Schreibweise, ist jede Frage einmal
> „neu". Nach dem Neustart läuft also ein voller Durchgang ohne Bremse —
> erwartet, einmalig, und in den Zahlen des nächsten Exports sichtbar.

### 80.6 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **990**, alle bestanden — **6 neu**, 2 nachgezogen |
| Ordnungszahlen | „95. Perzentil" unversehrt, 0 Dezimalpunkte im Makrotext |
| Tausenderpunkt | „1.936 EUR investiert" — deutsch, nicht englisch |
| übergenau-Prüfung | liest jetzt **beide** Schreibweisen |
| Schreibweise | fünf Module gemessen, nicht im Quelltext gesucht |
| freie Namen · Zahlenprüfer · Belegprüfer · Phase 1 | 0 · 9/9 · 9/9 · bestanden |
| Simulation | 4 Gruppen, 8 Signale, **0 Fehler, 0 Lücken** |

**Nicht angefasst:** reine Zählungen bleiben ohne Tausenderpunkt („1184
Monaten", „366 Messungen"). Sie sind Anzahlen, keine Messwerte — ein Punkt
darin läse sich wie eine Genauigkeit, die es nicht gibt.

---

## Kapitel 81 — Sechs Funde aus einer BTC-Hebelmail (17.08.2026)

Vier vom Nutzer, zwei von mir — darunter eine Tautologie, die ich am selben
Tag selbst eingebaut hatte.

### 81.1 P2 — „Bestehende Position" bei einer Position, die es nicht gibt

```
Abschnitt 1:  In BTC besteht keine offene Hebelposition.
Abschnitt 2:  Bestehende Position: Empfehlung HALTEN, Stand -3,8 %
```

**Beide Mengen standen in einem `gehalten`:**

```python
gehalten  = {symbol FROM holdings ...}
gehalten |= {symbol FROM hebel_positions WHERE status='offen'}
ist_bestand = row["symbol"] in gehalten
```

BTC liegt im **Spot**-Bestand — damit galt `ist_bestand` auch im
**Hebel**-Lauf. **Es ist derselbe Fehler wie am 15.08. beim Bestandsblock**
(*„meinte den SPOT-Bestand"*), nur an der Kennzeichnung statt an den Fakten.

**Drei Zustände statt zweier**, und die andere Seite wird benannt statt
verschwiegen — dieselbe Entscheidung wie bei `gegenbestand_satz`:

| Lage | Überschrift |
|---|---|
| dieses Instrument | `Bestehende Position:` |
| **die andere Seite** | `Verfolgter Einstiegsvorschlag - Sie halten diesen Wert im Spot, aber keine Hebelposition darauf:` |
| nur verfolgt | `Verfolgter Einstiegsvorschlag (NICHT im Bestand):` |

> ⚠️ **`finde_freie_namen.py` hat einen Rest gefunden, bevor er lief.** Nach
> dem Aufteilen der Menge blieb in der Take-Profit-Nachlese ein `gehalten`
> stehen — ein Spot-Bestand hätte dort einen Verkaufshinweis für eine
> Hebelposition erzeugt, die es nicht gibt. Ohne das Werkzeug ein NameError
> hinter einem breiten Fang.

> ⚠️ **Und mein erster Entwurf schrieb „eine Spot-Bestand".** Deutsche Artikel
> lassen sich nicht zusammenstecken; jetzt zwei feste Sätze je Instrument.

### 81.2 P5 — das Urteil der Gegenprüfung verschwand lautlos

| `einwand` | Ausgabe **vorher** |
|---|---|
| `nein` | Urteil + Fakten + Schlusssatz |
| fehlt | gar nichts |
| **unbekanntes Wort** | **Fakten + Schlusssatz, aber kein Urteil** |

**Der dritte Fall ist die gemeldete Mail** — deterministisch nachgestellt. Wo
der unbekannte Wert herkommt, ist **noch offen**: `rolle_g` lässt nur
ja/nein/unklar durch. Die Zeile macht den Fall jetzt sichtbar, statt auf die
Ursache zu warten:

```
Die Gegenpruefung lief, ihr Urteil ist aber nicht lesbar ('keine') -
bitte nur die Angaben darunter werten.
```

Dazu eine Warnung im Log. **Im Export ist es keine Randerscheinung: 69 von 119
Urteilen tragen gar keine Gegenprüfung.**

### 81.3 B — meine eigene Tautologie

> „Die 83 sind die Erfahrungsrate von 83, angepasst um 1 eigene Fall"

Bei **CRV 0,2** liegt die Erfahrungsrate bei 83 %, und ein einzelner eigener
Fall verschiebt sie nicht sichtbar — beide Zahlen runden auf denselben Wert.
Mein Fix von heute Vormittag hätte das erkennen müssen.

```
nachher   Das ist die Erfahrungsrate - 1 eigener Fall verschiebt sie
          noch nicht.
```

Die Unterscheidung hängt an der **gerundeten** Zahl: was der Leser sieht,
entscheidet, ob eine Erklärung nötig ist.

### 81.4 C — ein Satz sprach das Modell an, nicht den Leser

```
vorher   ... und dem Stopabstand, den DU nennst - gerechnet wird er nach
         DEINER Antwort.
nachher  ... und dem gewaehlten Stopabstand - er wird erst nach der
         Entscheidung gerechnet.
```

Die Aussage bleibt vollständig — sie hält das Modell davon ab, selbst einen
Faktor zu wählen (Kapitel 11.6). **Faktentexte gehen an beide Leser; wer einen
davon anspricht, schreibt für den anderen falsch.**

### 81.5 P3 und D — Bezug und Grammatik

```
vorher   Was dagegen spricht: Die negative Kursentwicklung ...
         Widerlegt waere DAS durch: Schlusskurs unter 53.274 EUR
nachher  Die Entscheidung EROEFFNEN waere widerlegt durch: ...
```

**Ein Fürwort, dessen Bezug man erraten muss, ist in einer Handelsempfehlung
eines zu viel.** Dazu: „etwa 1 Handelstag" statt „1 Handelstage".

### 81.6 P1 — die Zeitachse

Hier stand `ax.set_xticks([])`. **Ob ein Verlauf zwei Wochen oder ein halbes
Jahr zeigt, ändert alles an seiner Bedeutung.**

```
21.04.      13.05.      04.06.      26.06.      18.07.
        90 Handelstage bis 2026-07-19
```

Vier bis fünf Marken, nicht alle — bei 120 Kerzen wären 120 Datumsangaben eine
schwarze Leiste. Das Datum kommt aus **derselben Kerze** wie der Kurs.

### 81.7 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **1.008**, alle bestanden — **18 neu unter `--paket BTC`** |
| P2 | vier Lagen · kein zusammengesteckter Artikel |
| P5 | bekannt · **unbekannt benannt** · gar keines bleibt leer |
| B | Tautologie weg · Erklärung bleibt, wo sie trägt · Singular |
| C | kein „du" · Aussage vollständig |
| D · P3 · P1 | Singular und Plural · Bezug ausgeschrieben · Achse gezeichnet |
| freie Namen | 0 — **nach einem Fund**, der ohne das Werkzeug still gewesen wäre |
| Zahlenprüfer · Belegprüfer · Phase 1 | 9/9 · 9/9 · bestanden |
| Simulation | 4 Gruppen, 8 Signale, **0 Fehler, 0 Lücken** |

**Offen und zur Entscheidung:** ob CRV < 1 den Einstieg sperren soll (die
BTC-Mail bot 150 EUR Risiko für 35 EUR Chance), und ob die Belege Pfeile
bekommen oder die Mail auf HTML umgestellt wird.

---

## Kapitel 82 — Der Deckel fällt, die Marken bleiben (17.08.2026)

### 82.1 Die Bestandsaufnahme, die den Vormittag widerlegt hat

**Heute früh habe ich die Zielrechnung an den nächsten Widerstand
gekoppelt** (Kapitel 76, A2). Der Nutzer bat, vor einer Verschärfung zu
prüfen — *„um hier nicht einen Deckel über ein Asset zu legen bzw. der Fehler
an anderer Stelle liegt."* **Er hatte recht:**

| | |
|---|---:|
| Symbole mit Widerstand | 44 von 44 |
| davon **gedeckelt** | **44** |
| CRV danach unter 0,5 | **43 (98 %)** — Median **0,21** |
| deckelnder Widerstand, Median | **0,79 ATR** |
| **maximaler** Abstand überhaupt | **1,94 ATR** |

**Und der Grund ist strukturell:**

```
Marken ZWISCHEN Kurs und mechanischem Ziel (Median 1,50 ATR):
   1 Marke :  3 Symbole      3 Marken: 18   <- der Normalfall
   2 Marken: 13              4 Marken:  9
                             7 Marken:  1
   -> bei 44 von 44 mindestens eine
```

FLOKI hat 143 Marken oberhalb, APT 154, W 166. **Auf Tagesfraktalen liegt
immer eine Marke im Weg.** Eine Schwelle kann das nicht reparieren: bei
1,5 ATR wären noch **1 von 44** gedeckelt — der Deckel wäre faktisch aus.

> **Ein Deckel auf die nächste Marke heißt: „es gibt nie ein 2R-Ziel."**
> Der Deckel ist damit abgeschaltet. `_marke_im_weg` und der Zweig in
> `_ziel` bleiben stehen, mit dem Grund im Kommentar.

**Und die Klammer sagt jetzt, was sie ist:** aus *„kein Widerstand in
Reichweite"* wird *„mechanisch, 2x Risiko"*. Der alte Text hätte über einer
Liste von vier Marken behauptet, es gebe keine.

### 82.2 Was der Nutzer gefragt hat — und was daraus wurde

> *„Die Punkte sind immer eine Trendwende — Kurs geht wieder nach unten — und
> nicht: hat Kurs erreicht und ist durchgegangen. Ist das korrekt?"*

**Ja — und nein.** Jeder Punkt ist ein bestätigtes Williams-Fraktal, also eine
echte Umkehr. Aber `_cluster` warf Hochs und Tiefs in einen Topf. Am echten
BTC-Niveau bei 65.652:

```
3x Swing-Hoch  -> der Kurs stieg dorthin und drehte NACH UNTEN
4x Swing-Tief  -> der Kurs fiel dorthin und drehte NACH OBEN
```

**„7-mal berührt" verschwieg, wohin.** Jetzt steht es dabei.

### 82.3 Zwei Begriffe aus der alten Kette geholt

**Dieselbe Sache hatte zwei Namen.** `agent/krypto/liquidity_zones.py`
(gebaut 23.07., Stufe 2 per Backtest verworfen, p = 0,53) rechnet dieselben
Swing-Cluster — **und kann zwei Dinge mehr:**

| | neue Kette (vorher) | alt `liquidity_pools` |
|---|---|---|
| Richtung | gemischt | **getrennt** |
| „bereits gefegt" | nein | **ja** |

**Beide sind jetzt übernommen.** Die neue Kette entsprach bis heute
`support_resistance_levels` — der *schwächeren* der beiden alten Funktionen.
Sie „Liquiditätszonen" zu nennen wäre eine Falschetikettierung gewesen.

> ⚠️ **Der Name gilt nur für Krypto Spot und Hebel.** Die Deutung dahinter
> (Stop-Hunt, Marketmaker) wurde am 23.07. ausdrücklich auf den
> 24/7-Markt mit hohem Retail- und Hebelanteil begrenzt. **Die Marken selbst
> gibt es überall** — nur der Name ist begrenzt.

Beide Module tragen jetzt einen Querverweis aufeinander.

### 82.4 Wie es in der Mail aussieht

```
Take-Profit     72.880,75 bis 73.781,25 EUR  (CRV 2,0 - mechanisch, 2x Risiko)
  Auf dem Weg dorthin liegen 4 Marken (Liquiditaetszonen), die 3 naechsten:
    65.652,00 EUR  +0,7 Schwankungsbreiten - 7 Umkehrpunkte
      (3x nach unten gedreht, 4x gehalten), zuletzt 2026-07-15
    66.671,00 EUR  +1,3 Schwankungsbreiten - 7 Umkehrpunkte
      (3x nach unten gedreht, 4x gehalten), zuletzt 2024-11-04 - seither durchbrochen
    67.284,00 EUR  +1,6 Schwankungsbreiten - 4 Umkehrpunkte
      (3x nach unten gedreht, 1x gehalten), zuletzt 2026-06-15
  Was das heisst: an diesen Preisen hat der Kurs frueher gedreht - dort liegen Auftraege.
  Je mehr Umkehrpunkte, desto eher passiert es wieder; 'durchbrochen' heisst, die
  Marke hat zuletzt nicht gehalten. Das Ziel ist GERECHNET, nicht vorhergesagt: es
  sagt, wie weit der Kurs laufen muesste, damit sich der Trade traegt.
```

**Das Datum ist die Antwort auf die Zeitfensterfrage.** Statt einer gesetzten
Grenze steht da, wann zuletzt gedreht wurde — die zweite Marke oben stammt aus
dem **November 2024** und ist längst gebrochen. Ohne Datum wirkt sie aktuell.

**Im Chart** dieselben Marken als beschriftete Linien (Preis + Umkehrzahl),
drei je Seite. Dort stand bisher `marken=None` — der Chart konnte es immer und
bekam nie etwas.

### 82.5 Nutzerentscheidungen, festgehalten

| | |
|---|---|
| Gruppen | Marken **überall**, Name nur Krypto |
| Anzahl in der Mail | **drei** (es sind bis zu sieben) |
| Marken mit einer Umkehr | **zeigen** — sie sind ein Drittel |
| Zeitfenster | **keins**, dafür das Datum der letzten Berührung |

### 82.6 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **1.030**, alle bestanden — **22 neu unter `--paket Marken`** |
| Richtung | 3 Wenden nach unten / 2 nach oben an einer gebauten Reihe nachgewiesen |
| „durchbrochen" | erkannt **und** nicht erkannt, je nach Kursverlauf |
| kein Deckel | Ziel bleibt mechanisch · die Kette füttert ihn nicht mehr |
| Mailtext | Richtung, Datum, Bruchstatus, Erläuterung, Singular/Plural, „keine Marke im Weg" |
| Name | Krypto **ja**, rohstoffe/aktien/etf/hedge **nein** — einzeln geprüft |
| Chart | beschriftet **und** verträgt weiterhin eine reine Preisliste |
| freie Namen · Zahlenprüfer · Belegprüfer · Phase 1 | 0 · 9/9 · 9/9 · bestanden |
| Simulation | 4 Gruppen, 8 Signale, **0 Fehler, 0 Lücken** |

---

## Kapitel 83 — Der eine Mistral-Aufruf (17.08.2026)

**Nutzerfrage an der Budgetanzeige:** *„spannend — wie kann es sein, dass
Mistral einen Aufruf hatte?"*

```
LLM Budget (2026-08-17)
   Gemini:   164/500 (33%)
   Z.ai:     80 calls
   Mistral:  1 call
```

### 83.1 Die Quelle

`marktscan_backward_tracking_job` (Tagesjob, 07:00):

```python
llm_client = mistral_client or gemini_client      # Mistral ZUERST
```

Der Job misst den Erfolg von Marktscan-Kandidaten und holt bei einem Erfolg
eine kurze Begründung. **Ein Erfolg heute → ein Aufruf.**

### 83.2 Warum es ein Rest ist

**Dieselbe Zeile wurde am 14.08. an der Kategorie-Synthese bereinigt**, mit
einer Begründung, die auch hier gilt:

> Mistrals Free-Plan wurde am 07.08. kostenpflichtig; seither beantwortet er
> jeden Aufruf mit **„402 Payment Required"**. Der Rückfall auf Gemini
> funktionierte jedes Mal — der Mistral-Ruf war reine Verzögerung plus eine
> Fehlerzeile je Durchlauf.
>
> *„Ein Fehler, der bei JEDEM Lauf auftritt und nichts bedeutet, ist schlimmer
> als keiner: er trainiert das Auge, Fehlerzeilen zu überlesen."*

**Zwei Stellen, eine Behandlung — die zweite blieb stehen.**

| | |
|---|---|
| Kosten | **keine** — der Aufruf schlägt fehl, es fließt kein Geld |
| Wirkung | Rückfall auf Gemini, der Job läuft durch |
| Schaden | eine bedeutungslose Fehlerzeile — **und eine „1" in der Anzeige, die eine Nutzung behauptet, die es nicht gab** |

Der Parameter bleibt in der Signatur: der Scheduler übergibt ihn, und ihn dort
zu entfernen wäre eine Änderung an mehreren Aufrufstellen für nichts.

### 83.3 Ein zweiter Fund am selben Provider

**Der Kanarienvogel** (`kanarienvogel_job`, tägliche LLM-Drift-Messung, 10
Aufrufe) hängt ebenfalls an Mistral. Er ist **bewusst nicht registriert** —
aber sein Docstring beschreibt nur, wie man ihn aktiviert, nicht dass er heute
ins Leere liefe.

> ⚠️ **Und hier gibt es KEINEN Rückfall.** Der Kanarienvogel misst ein
> bestimmtes Modell; ein Ersatzprovider wäre eine andere Messung. Wer ihn
> einschaltet, bekommt zehn Fehlschläge täglich und eine Drift-Messung, die
> nichts misst.

Die Warnung steht jetzt im Docstring. **Sie ersetzt die Entscheidung nicht** —
registriert ist er weiterhin nicht.

### 83.4 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **1.035**, alle bestanden — **5 neu unter `--paket Provider`** |
| kein lebender Pfad zieht Mistral vor | geprüft über den ganzen Scheduler |
| Parameter bleibt | Signatur unverändert, Scheduler-Aufruf unberührt |
| Kanarienvogel | Warnung im Docstring · **weiterhin nicht registriert** |
| Scheduler | baut 19 Jobs, `marktscan_backward_tracking` dabei |
| freie Namen | 0 |

**Prompt und Kette sind nicht berührt** — der ruhige Messtag bleibt intakt.

---

## Kapitel 84 — Bestandsaufnahme der Basisabdeckung, und eine Lücke, die keine war (17.08.2026)

**Gemessen an der Produktionsdatenbank von 18:28**, nicht an der
Entwicklungsdatei.

### 84.1 Wo der glatte Schnitt heute steht

**Rolle BC — BC3: mindestens ein Fakt außerhalb der Kerzenreihe**

| Gruppe | erfüllt | woher |
|---|---:|---|
| krypto/spot · hebel | **41/41** | Umschlag |
| aktien/spot | **2/2** | Fundamentaldaten |
| **rohstoffe/spot** | **0/4** | — |
| etf (5 Themen + 2 Hedge) | 0/7 | zurückgestellt |

**Rolle G — G1: zwei Quellen · G2: eine symbolspezifisch**

| Gruppe | erfüllt | Quellen |
|---|---:|---|
| krypto/spot · hebel | **37/44** | onchain 44 · terminmarkt 37 |
| aktien/spot | **2/2** | short_interest · insider |
| **rohstoffe/spot** | 0/4 | nur cot → **G1 fehlt** |
| etf | 0/7 | nichts |

**G1 fehlt 25×, G2 fehlt 21×.** Davon lösen sich zwei von selbst: der
ETF-Bestand schließt G1 für drei von vier Rohstoffen in rund drei Monaten;
die sieben Kryptowerte ohne Terminmarkt sind **nicht behebbar** (die Börsen
führen dort keine Kontrakte).

### 84.2 Der Fund: Lücken, die es nicht gab

```
aktien/PLTR:  Zu diesem Wert liegt keine Angabe vor: Finanzierungsrate.
              Zu diesem Wert liegt keine Angabe vor: Open Interest.
              Zu diesem Wert liegt keine Angabe vor: Anteil der Long-Konten.
```

**Eine Aktie hat keine Finanzierungsrate.** Das war **die Hälfte** der
G-Sätze bei Aktien und Rohstoffen und **alles** bei Themen-ETF.

> ⚠️ **Die richtige Behandlung stand schon im selben Code**, zwei Zeilen
> weiter, nur je *Instrument* statt je *Assetklasse*:
>
> *„NUR MELDEN, WENN SIE HIER HINGEHÖRT. Beim Hebel ist ihre Abwesenheit
> Absicht, kein Mangel — ‚keine Angabe' wäre gelogen."*

**Ergebnis:**

| | vorher | nachher |
|---|---:|---:|
| aktien/PLTR | 6 Sätze | **3**, alle mit Inhalt |
| rohstoffe/OD7H | 6 | **3** |
| themen_etf/CEBS | 3 | **0** |
| krypto/BTC | 8 | **8** — unverändert |

### 84.3 Und die Nebenwirkung, die es fast gegeben hätte

**Die Filterung entschärfte den Wächter, der leere Aufrufe verhindert.** G5
zählte die *gemeldeten Lücken*:

```python
if len(lage.get("fehlt") or []) >= 3:    # <- funktionierte nur, solange
    return None                          #    jede Klasse dieselben drei meldete
```

Bei einem Themen-ETF steht seit der Filterung `fehlt = []` **und**
`saetze = []` — die alte Schranke hätte durchgelassen und **Rolle G mit einer
leeren Positionierung gefragt.** Genau der Fall, den sie verhindern soll.

> **Der richtige Wächter stand schon eine Zeile höher** (`if not saetze`) —
> meine erste Fassung stellte einen zweiten daneben. Jetzt gibt es genau
> einen, und er misst, **was das Modell zu sehen bekommt**, statt was wir
> vermissen.

### 84.4 Drei Prüfungen, die veraltet waren

| | stand da | jetzt |
|---|---|---|
| `pruefe_prompt_matrix` | zählte `_marken_werte` als Faktenblock → **50 %** statt 75 % Kursreihenanteil | nur Satzblöcke |
| `pruefe_pakete` G5 | suchte den **Quelltext** der alten Schranke | prüft das **Verhalten** |
| `simuliere_kette` | `gruppe != "krypto"` ⇒ Rolle G ohne Grundlage | fragt die **Mindestkriterien** |

Die dritte meldete beide Aktien als „urteilt OHNE Grundlage" — **obwohl beide
seit dem 16.08. G1 und G2 erfüllen.** Das Kriterium beschrieb einen Zustand,
den es nicht mehr gibt.

**Und die Simulation trennt jetzt Lücke von Einstellung:** dass Rolle G bei
AIOZ und ASTER allein auf dem BTC-weiten Fluss urteilt, ist gemeldet und
**nicht gesperrt** — eine Entscheidung, keine Lücke. Sie steht unter
*„BEKANNTE ZUSTÄNDE"*, nicht unter den Fehlern.

### 84.5 Regelkonformität und Parameterqualität

| | |
|---|---|
| N1–N5 | **kein Befund** — kein Satz rechnet vor, keine Konstante trägt Richtung |
| Belege gegen Fakten unter `17e` | **0 von 183** (17b: 19 von 272 = 6,99 %) |

**Der Umschlag-Umbau ist damit belastbar bestätigt:** zur alten Rate wären
13 Befunde zu erwarten gewesen; null zu sehen hat eine Wahrscheinlichkeit von
rund **zwei zu einer Million**.

**Extern geprüft:** Funding-Rate und Open Interest haben dokumentierte
Vorhersagekraft — **nur an den Extremen** (Granger-Tests über 35,7 Mio.
Minutenbeobachtungen). Unsere Sätze sagen in vier von fünf Fällen „im
gewohnten Bereich", also genau dort, wo die Literatur nichts findet. Die
Parameter sind richtig gewählt; sie sagen nur meistens nichts.

**Rohstoff-Lagerbestände, dritte Recherche:** COMEX und LME sind frei
**einsehbar**, aber nicht frei **abrufbar** — Oberflächen ohne API,
Fastmarkets nur nach Registrierung mit einem Tag Verzug. **Kein
schlüsselloser Weg.**

### 84.6 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **1.046**, alle bestanden — **11 neu unter `--paket Luecken`** |
| Filterung | krypto meldet weiter · aktien/rohstoffe/etf/hedge nicht mehr · andere Lücken unberührt |
| ohne Klasse | meldet weiter · **neue Klasse** meldet nicht |
| ⚠️ Kommentar gegen Umsetzung | die Prüfung fand meinen Widerspruch: „fail-open" geschrieben, fail-closed gebaut — Kommentar korrigiert |
| G5 | genau **ein** Wächter, am Verhalten geprüft |
| freie Namen · Zahlenprüfer · Belegprüfer · Phase 1 | 0 · 9/9 · 9/9 · bestanden |
| Simulation | 4 Gruppen, 8 Signale, **0 Fehler, 0 Lücken**, 4 bekannte Zustände |

### 84.7 Was offen bleibt

| | Stand |
|---|---|
| **Rohstoffe BC3** | nur die Haltekostenquote käme in Frage — **gelb**, je Zertifikat von Hand zu recherchieren |
| **Themen-ETF** | zurückgestellt, wie entschieden |
| Krypto G2, 7 Symbole | nicht behebbar — keine Kontrakte an den Börsen |

---

## Kapitel 85 — Warum Rolle G so oft ausfällt, und die sechs fetten Zeilen (17.08.2026)

### 85.1 Der Ausfall von Rolle G — gemessen, nicht vermutet

**85 von 159 Urteilen bekamen keine Gegenprüfung.** Zwei unabhängige
Ursachen, beide belegt:

**(a) Der Durchsatz.**

| Regler | Wert | Folge |
|---|---:|---|
| `MAX_GLEICHZEITIG` | **2** | zwei Anfragen zugleich |
| `WARTE_AUF_PLATZ_SEKUNDEN` | **180** | wer länger wartet, fällt aus |
| `REQUEST_TIMEOUT_SECONDS` | **150** | — |

Zwei Plätze × 180 s reichen bei gemessenen ~25 s je Aufruf für rund **13
Signale je Umlauf**. Ein Umlauf hat 20–40.

**(b) Die Zeitgrenze passt zu einem anderen Prompt.**

> Die 150 s stammen aus einer Messung von 109 s — **an einem Prompt mit
> 34.611 Zeichen.** Rolle G schickt heute **1.495**.

**Live nachgemessen:** HTTP 200 nach **22,4 · 29,7 · 33,1 s**, ein Ausreißer
bei 65,5 s, dazwischen vereinzelt vorübergehende HTTP-Fehler.

**Ein Aufruf, der nach 150 s noch läuft, kommt nicht mehr** — er hält nur
einen der zwei Plätze besetzt. Die Zeitgrenze schützt hier nichts, sie
blockiert.

⚠️ **Nicht umgesetzt.** Der Vorschlag (Zeitgrenze herunter, Gleichzeitigkeit
herauf) ist eine Änderung an einem fremden Anbieterlimit und liegt beim
Nutzer.

### 85.2 Sechs Zeilen fett und schwarz

**Nutzervorgabe:** *„Einstiegszone, Stop, TP, Haltedauer, Betrag und Hebel"* —
die Größen, nach denen tatsächlich gehandelt wird.

**Am ERSTEN WORT erkannt, nicht am Vorkommen:**

```python
if stripped.split(" ", 1)[0].rstrip(":") in HANDELSPARAMETER:
```

> „Stop" steht auch mitten in Sätzen — *„der Trailing-Stop löst erst aus"*.
> Würde jedes Vorkommen fett, hieße fett bald nichts mehr.

### 85.3 „Für alle eMail prüfen" — und was das gefunden hat

Die Paketprüfung baut **eine** Beispielrechnung. Die Nutzervorgabe verlangt
**jede** Mail, also läuft die Prüfung jetzt in `simuliere_kette.py` über die
echten Mails aller Gruppen.

**Sofort ein Fund, in JEDER Gruppe:**

```
Z-1: 2 Zahl(en) stehen nicht in der Eingabe: [42.0, 17.0]
```

Eine rohe Python-Liste in einer sonst deutschen Mail — englische Punkte,
eckige Klammern, und ein `.0`, das eine Genauigkeit vortäuscht, die das
Modell nie hatte. **Jetzt:** *„2 Zahl(en) stehen nicht in der Eingabe: 42 und
17."*

### 85.4 Die Prüfregel war selbst der zweite Fehler

| | |
|---|---|
| erste Fassung | `\b\d+\.\d\b` |
| fand | `2.5` |
| fand **nicht** | `3.81` — das `\b` scheitert an der zweiten Ziffer |

**Sie meldete sauber, wo es nicht sauber war.** Der erste Simulationslauf gab
„0 Lücken" aus; erst die gehärtete Regel fand die sieben.

```python
_ENG_ZAHL = re.compile(r"(?<![\d.])\d+\.(\d+)")   # 3 Ziffern = Tausendergruppe
```

Beide Werkzeuge benutzen jetzt **dieselbe** Funktion — zwei Messungen, die
verschieden zählen, sind schlimmer als eine.

### 85.5 Die letzten englischen Zahlen

| Stelle | stand da | jetzt |
|---|---|---|
| `ausstiegsregel.trailing_begruendung` | `1.90 R` — direkt unter `+1,70 R` | `1,90 R` |
| `entscheidungsrechnung._ziel()` | `2.5 x ATR` (aus `:g`) | `2,5 x ATR` |
| `gegenpruefer_rollen` Z-1 | `[42.0, 17.0]` | `42 und 17` |

### 85.6 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **1.068**, alle bestanden — **22 neu unter `--paket Fett`** |
| fett | sechs Größen am gerenderten **HTML** geprüft, nicht an der Regel |
| nicht fett | drei Fließtextzeilen, die mit einem Parameternamen beginnen |
| Zahlregel | beide Richtungen — Tausenderpunkt bleibt, `3.81` wird gefunden |
| alle Mails | **9 Mails, 4 Gruppen, 0 Lücken** — Spot wie Hebel, Einstieg wie Bestand |
| freie Namen · Zahlenprüfer · Belegprüfer · Darstellung | 0 · 9/9 · 9/9 · bestanden |

**Eine bestehende Prüfung schlug fehl und hatte recht:** sie erwartete
`62.0` im Z-1-Satz. Erwartung nachgezogen, nicht die Änderung.

### 85.7 Offen

| | |
|---|---|
| **Rolle G, Regler** | Vorschlag liegt vor — **Entscheidung beim Nutzer** |
| Rohstoffe/Hedge in der Simulation | übersprungen, keine Kursreihe im Bestand — die Mailprüfung sah sie nicht |

---

## Kapitel 86 — Die 85 fehlenden Gegenprüfungen: es war unsere Geduld (17.08.2026)

### 86.1 Was nicht ging

**Die 2 sind hart.** `api/zai.py:66` zitiert Z.ais eigene Doku: *„Concurrency
limit: 2"* für glm-4.5-flash. Alles darüber wird serverseitig mit 429
abgewiesen — genau der Zustand vom 28.07. (210 Logzeilen, praktisch alle
429). **Mein erster Vorschlag „Gleichzeitigkeit herauf" war an dieser Stelle
falsch.**

**Und die Zeitgrenze ist geteilt.** Die 150 s gelten auch für die alten
Pipelines (aktien, hedge, hebel), die über
`fuehre_beide_calls_im_hintergrund` weiter den großen Prompt schicken.

### 86.2 Die eigentliche Ursache

Ein Befund macht die Rechnung erst klar: **es ist heute EIN Z.ai-Aufruf je
Signal**, nicht zwei — `mehrheit()` (drei Stimmen) ist seit dem 16.08.
abgeschaltet.

```
Kapazität   2 Plätze × 3.600 s / 30 s  =  ~240 Aufrufe je Stunde
gebraucht   20–40 je Umlauf
```

**Die Kapazität war die ganze Zeit da.** Wir sind nur nach 180 Sekunden aus
der Warteschlange gegangen: 2 × 180/30 = **12 Signale** kamen dran, der Rest
bekam `Andrang`.

> **Das Limit begrenzt, wie viele GLEICHZEITIG laufen — nicht, wie viele
> insgesamt drankommen.** Die 180 s waren unsere Geduld, nicht die Grenze des
> Anbieters.

### 86.3 Der Fund nebenbei: heute schon widersprüchlich

| | |
|---|---:|
| ein Faden durfte warten | 180 s + 150 s = **330 s** |
| `rollen_lauf.py:582` gab auf nach | 240 + 60 = **300 s** |

**Der Hauptfaden stieg aus, bevor die Warteschlange es tat.** Der Faden lief
als Daemon weiter, **seine Mail ging MIT dem Einwand raus**, und `ZM.schreibe`
fiel aus. Die Mail zeigte dann einen Befund, den die Datenbank nicht kennt.

**Die Regel daraus:** die Warteschlange muss **vor** dem Hauptfaden aufgeben.

### 86.4 Was gebaut wurde

| Regler | vorher | jetzt | |
|---|---:|---:|---|
| `WARTE_AUF_PLATZ_SEKUNDEN` | 180 | **480** | 12 → 32 Signale |
| `WARTE_MAX_SEKUNDEN` | 240 | **540** | Aufgabegrenze 600 s > 555 s |
| Zeitgrenze Rolle G | 150 (global) | **75 (nur hier)** | eigener Parameter |
| `MAX_GLEICHZEITIG` | 2 | **2** | Anbieterlimit, unberührt |
| `REQUEST_TIMEOUT_SECONDS` | 150 | **150** | alte Pipelines unberührt |

Die Zeitgrenze als **Parameter an `chat()` mit Vorgabe
`REQUEST_TIMEOUT_SECONDS`** — wer nichts angibt, bekommt was er immer bekam.

**Warum 75:** live gemessen 22,4 / 29,7 / 33,1 s, ein Ausreißer bei 65,5 s —
auf einem Prompt von **1.495** Zeichen, nicht den 34.611, an denen die 150 s
gemessen wurden. Bei zwei Plätzen kostet ein hängender Aufruf die halbe
Kapazität, und zwar so lange wie **fünf** normale Aufrufe.

### 86.5 Der Nachweis am Andrang selbst

Maßstab 1:100 (ein Aufruf 0,30 s statt 30 s), 40 Signale:

| | mit Gegenprüfung | `Andrang` | Umlauf |
|---|---:|---:|---:|
| vorher 180 s | **14** von 40 | 26 | 210 s |
| jetzt 480 s | **32** von 40 | 8 | 481 s |

Vorhergesagt hatte ich 12 → 32. **Die acht offenen sind der Andrangfall nach
einem Neustart, nicht der Normalbetrieb** — und sie sind als `Andrang`
sichtbar, nicht als stille Zustimmung.

### 86.6 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **1.080**, alle bestanden — **12 neu unter `--paket Andrang`** |
| Zeitgrenze am Draht | gemessen an `requests`: 150 / **75** / 150 |
| Deckel | 20 Fäden, gemessene Spitze **2** |
| `Andrang` | wird geworfen, nicht stillschweigend übersprungen |
| Reihenfolge | 555 s < 600 s, und die 600 stehen am Code, nicht in der Rechnung |
| Takt | 600 s < 900 s (`HEBEL_SCREENING_INTERVAL_MINUTES = 15`) |
| freie Namen · Zahlenprüfer · Belegprüfer · Darstellung | 0 · 9/9 · 9/9 · bestanden |
| Simulation | 4 Gruppen, 9 Mails, **0 Fehler, 0 Lücken** |

### 86.7 Was das kostet, und was offen bleibt

**Mails eines Umlaufs treffen über ~8 Minuten verteilt ein statt über ~3.**
Bei Haltedauern um 25 Handelstage folgenlos.

⚠️ **Der eine echte Nachteil:** ist Z.ai ausgefallen, wartet jetzt jeder Faden
8 statt 3 Minuten aufs Nichts. Sauber lösen würde das ein Abbruch nach *n*
Transportfehlern im selben Umlauf — **nicht gebaut**, das ist eigene Mechanik
und war nicht beauftragt.

---

## Kapitel 87 — Der Gegenspieler zur langen Wartezeit (17.08.2026)

**Der Preis von Kapitel 86.** Mit 180 s wartete ein Faden bei einem
Anbieterausfall drei Minuten aufs Nichts; mit 480 s wären es acht — **mal
vierzig Fäden**. Die Wartezeit hilft gegen Andrang und schadet bei Ausfall,
also braucht sie einen Gegenspieler, der die beiden Lagen unterscheidet.

### 87.1 Die Mechanik

**`AUSFALL_SCHWELLE = 3` Transportfehler IN FOLGE brechen den Umlauf ab.**

| Entscheidung | warum |
|---|---|
| **in Folge**, nicht insgesamt | ein Anbieter, der weg ist, lässt ALLES scheitern; ein wackliger lässt Erfolge dazwischen zu. Eine Gesamtzahl behandelte beide Lagen gleich |
| **drei**, nicht eins | einzelne HTTP-Fehler kamen am 17.08. vereinzelt vor, ohne dass der Anbieter weg war |
| nur **Transport** | eine unbrauchbare Antwort ist ein Inhaltsproblem — der Anbieter lebt. Sie zu zählen hieße, wegen schlechter Antworten das Fragen einzustellen |
| je **Umlauf**, nicht für immer | beim nächsten Takt kostet ein fortdauernder Ausfall drei Aufrufe statt vierzig |

**`Ausfall` erbt von `Andrang`** — die Folge ist dieselbe (der Aufruf hat
nicht stattgefunden), also behandelt jeder bestehende `except Andrang` ihn
richtig, ohne dass eine Stelle nachgezogen werden muss. Unterscheidbar bleibt
er am Typ und am Text.

### 87.2 Zweimal gefragt, nicht einmal

```python
grund = _abgebrochen()          # VOR dem Warten
if grund: raise Ausfall(grund)
if not _PLATZ.acquire(...): raise Andrang(...)
try:
    grund = _abgebrochen()      # UND NOCH EINMAL danach
```

> **Wer beim Eintritt in die Schlange stand, hat den Abbruch nicht gesehen** —
> bei 480 s Wartezeit sind das im Andrangfall fast alle. Ohne die zweite Frage
> brennt jeder wartende Faden nach dem Abbruch noch seine eigene Zeitgrenze
> ab, und der Abbruch spart nichts.

### 87.3 Der Nachweis am Ausfall selbst

Maßstab 1:100, 40 Signale, toter Anbieter:

| | Aufrufe ins Leere | Umlauf | Buchung |
|---|---:|---:|---|
| ohne Abbruch | **14** | 525 s | 14 Fehler + 26 Andrang |
| mit Abbruch | **4** | 150 s | 4 Fehler + 36 Ausfall |

Vier statt drei, weil zwei Aufrufe gleichzeitig laufen: **wer schon unterwegs
ist, wird nicht zurückgerufen.**

### 87.4 Und dabei die eigentliche Blindheit gefunden

Der Lauf gegen den toten Anbieter zeigte etwas, das nicht am Abbruch lag:

```
1.  art=None   Mailzeilen=0
2.  art=None   Mailzeilen=0
3.  art=None   Mailzeilen=0
4.  art='ausfall'  Mailzeilen=1
```

⚠️ **`aus["uebersprungen"]` wurde gesetzt und NIRGENDS gelesen.** `zeilen()`
lieferte nur bei gesetztem `einwand` etwas — bei Andrang, Ausfall und
Fehlschlag fehlte der Abschnitt **ersatzlos**. Eine ausgefallene Gegenprüfung
sah aus wie eine, die es zu diesem Wert gar nicht gibt.

**Jetzt sagt die Mail es, in drei unterscheidbaren Sätzen:**

```
● Gegenpruefung nicht gelaufen - zu viele Signale in diesem Umlauf.
  Dieses Signal ist NICHT gegengeprueft.
● Gegenpruefung nicht gelaufen - die Gegenquelle war in diesem Umlauf
  nicht erreichbar. Dieses Signal ist NICHT gegengeprueft.
● Gegenpruefung nicht gelaufen - die Gegenquelle hat nicht geantwortet.
  Dieses Signal ist NICHT gegengeprueft.
```

**● und nicht ▼:** grau, nicht rot. Ein Ausfall unserer Technik ist kein
Befund über den Handel — ihn rot zu setzen hieße, dem Leser eine Warnung über
sein Geschäft zu geben, wo eine über unser Werkzeug gemeint ist.

**Keine Anbieternamen, keine Fehlertypen im Satz.** Mit „ConnectTimeout nach
3 Versuchen" kann der Leser nichts anfangen; was er wissen muss, ist, dass
dieses Signal **ohne** Gegenprüfung zu ihm kommt.

### 87.5 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **1.099**, alle bestanden — **19 neu unter `--paket Ausfall`** |
| zwei Fehler | brechen NICHT ab · ein Erfolg dazwischen setzt zurück |
| drei in Folge | brechen ab · weitere Aufrufe werfen `Ausfall` in **0,000 s** |
| Inhaltsfehler | fünf kaputte Antworten brechen nicht ab |
| Rücksetzung | `beginne_umlauf()` in `fuehre_umlauf`, am Code geprüft |
| Mail | drei Lagen, drei Sätze, alle grau, ein echter Befund verdrängt sie |
| echter Weg | `ZM.hole()` mit totem Client: keine Ausnahme nach oben, Mail geht raus |
| freie Namen · Zahlenprüfer · Belegprüfer · Darstellung | 0 · 9/9 · 9/9 · bestanden |
| Simulation | 4 Gruppen, 9 Mails, **0 Fehler, 0 Lücken** |

### 87.6 Was bleibt

Die drei Aufrufe vor dem Auslösen laufen weiterhin ins Leere — **das ist der
Preis dafür, einen Ausfall von einem Aussetzer zu unterscheiden.** Ihre Mails
tragen jetzt den Hinweis.


---

## Kapitel 88 — PLAN Fassung 2: Hebel als Ergebnis statt als Kategorie (18.08.2026)

**Ersetzt die Erstfassung desselben Tages.** Die Erstfassung behauptete, es
gebe genau EINEN freien Parameter (k). Das war falsch — siehe 88.2. Sie steht
in der Git-Historie; zwei nebeneinander stehende Pläne wären genau der
Schaden, den die Doku-Regel benennt.

**Status: Plan, nichts gebaut.**

### 88.1 Der Befund

| | |
|---|---|
| `laeufe()` gibt Krypto **dieselbe Symbolliste an beide Instrumente** | 43 Assets → 86 Urteile |
| Stop, Zone, Ziel, Haltedauer | **in beiden Läufen identisch** (`_stop_abstand` kennt kein Instrument) |
| `asset_hebel_settings` | **0 Zeilen** — alle auf Vorgabe „erlaubt" |
| Hebel-Eignungskriterium | **existiert nicht** — `pre_check_hebel` wird von der neuen Kette nicht aufgerufen, `krise_extrem` kommt dort nicht vor |
| Stopquelle | in **10 von 12** echten Fällen die Klemme RM-1b/1c, nicht das Urteil |
| Rauschtreffer bei 0,75 ATR | **56,7 %** binnen 5 Handelstagen (63.884 Anker) |

### 88.2 ⚠️ DIE KORREKTUR: zwei Achsen, nicht eine

```
Hebel = Verlustanteil / Stopabstand      →   Hebel > 1  ⟺  Stop < Verlustanteil
```

**Die Spot/Hebel-Grenze IST der Verlustanteil.** Er steht heute bei **15 %**
für **beide** Instrumente (`betraege.VORGABE_VERLUSTANTEIL`) — vermutlich nie
so entschieden, sondern nie unterschieden.

Bei ATR-Median 3,41 % liegt ein 1,5-ATR-Stop bei rund 5 %. **Also ist bei
15 % Verlustanteil praktisch alles ein Hebelgeschäft — unabhängig von k.**
Das ist die eigentliche Ursache von „derzeit fast immer Hebel".

Gemessen mit den echten Budgets (Einsatz 1.000 €, Risiko 150 €), 59 Symbole:

| k | Hebel nötig (Median) |
|---:|---:|
| 0,75 (heute) | **5,9x** |
| 1,5 | 2,9x |
| 2,5 | 1,8x |

**Literaturwerte als Ausgangspunkt (Nutzervorgabe 18.08.):** Risiko je Trade
**1–2 %** des Kapitals, Hebeldeckel **2**. Heute: 150 € gegen einen Hebeltopf
von 3.000 € = **5 %** je Trade. `config.yaml` führt
`risiko_pro_trade_prozent_hebel: 1` — **die neue Kette liest den Schlüssel
nicht.** Konfiguration und Verhalten widersprechen sich um den Faktor fünf.

### 88.3 Die Regel

```
stop = min( 25 % x Kurs,                        Deckel, unverändert
            max( k x ATR,                       Rauschboden
                 Marke ± 0,25 ATR,              Struktur
                 Widerlegungspreis ) )          These (Modell)
Betrag  = Risikobudget / stop_relativ
Hebel   = Verlustanteil / stop_relativ
Etikett = "hebel" wenn Hebel > 1,0
```

Das ist **Volatility Targeting**: Hebel proportional zu 1/Volatilität,
stetig, ohne Schwelle. Die Literatur nennt genau das als Vorteil — *„scales
continuously with forecast risk, never fully exiting."*

**Zwei harte Zusatzbedingungen, beide Tatsachen statt Prognosen:**

1. **SHORT ⇒ Hebel.** Spot kann bei Bitpanda nicht short. Die Richtung ist
   damit selbst ein Hebelkriterium, und zwar ein zwingendes.
2. **Hebel nur bei Krypto.** `INSTRUMENTE_JE_GRUPPE` — für Aktien, Rohstoffe
   und ETF rechnet die Formel zwar einen Hebel aus, handelbar ist er nicht.
   Dort wirkt das Ergebnis als Betragsbegrenzung, nicht als Etikett.

### 88.4 Was das Modell sieht — und was nur gerechnet wird

**Die Trennlinie verläuft nicht bei „Zahl / keine Zahl", sondern bei der
Frage:** *„wo setzt du den Stop"* ist ein Risikoparameter (kann es nicht),
*„wo stirbt deine Begründung"* ist ein Urteil über den eigenen Text (kann es).

| | Modell | Rechnung |
|---|---|---|
| Lage, Belege, Richtung, Aktion | ✓ | |
| `umgeworfen_durch` + `umgeworfen_preis_eur` | ✓ | |
| Stop, Zone, Ziel, Haltedauer, Betrag, Hebel, Etikett | | ✓ |

**⚠️ BEFUND: `einstieg_eur` und `stop_eur` werden verlangt, verworfen — und
sind trotzdem tödlich.** `rechne()` liest sie nie; `empfehlung_vertrag.py:206`
nimmt aber die Aktion auf **NICHTS_TUN** zurück, wenn sie fehlen oder wenn
`stop >= einstieg`. Zwei Zahlen, die das Modell nicht schätzen kann, können
den Trade beenden.

**Zwei Folgefehler an derselben Stelle, beide heute schon wirksam:**

| | |
|---|---|
| Die Prüfung greift nur bei `KAUFEN`/`NACHKAUFEN` | **`ERÖFFNEN` — die Haupt-Hebelaktion — ist ungeprüft.** Die riskanteste Aktion ist die einzige ohne Kontrolle |
| Die Prüfung kennt **keine Richtung** | bei SHORT liegt der Stop korrekt ÜBER dem Einstieg → ein SHORT-`NACHKAUFEN` wird still zu NICHTS_TUN. Dieselbe Klasse wie die 313 SHORTs, die als HALTEN in der Datenbank lagen |

**Änderungen am Prompt (Stufe 3, nicht jetzt):**

1. `einstieg_eur` und `stop_eur` **streichen**.
2. Das Instrument verlässt den Prompt **nur beim Einstieg**. Beim **Bestand**
   bleibt es: eine bestehende Position *ist* gehebelt — Tatsache, keine
   Prognose. Nur dort ergeben `HEBEL_ERHÖHEN`/`HEBEL_SENKEN` Sinn.
3. **Ein Faktensatz statt zwei** — Funding, Put-Skew und Retail-Long gehen an
   jedes Krypto-Urteil.

### 88.5 ⚠️ DIE FALLSTRICKE — vollständig, aus der Gegenprüfung

| # | Fallstrick | Umgang |
|---|---|---|
| **F1** | **Das JSON-Schema hängt am Instrument.** `llm_schema.py:515` wählt das Aktions-Enum je Instrument — *„ein Schema mit dem falschen Enum lässt das Modell gar nicht erst antworten."* Spot kennt 5 Aktionen, Hebel 7 | Einstieg braucht ein gemeinsames Vokabular. `KAUFEN` entspricht `ERÖFFNEN` — vorerst **spots Wort behalten**, das Etikett kommt danach. Umbenennen berührt 24 Codestellen und DB-Werte |
| **F2** | **`richtung` gibt es nur bei Hebel.** Ohne Instrument im Prompt könnte das Modell SHORT sagen — was Spot nicht kann | genau deshalb **SHORT ⇒ Hebel** (88.3). Kein Widerspruch, sondern die Auflösung |
| **F3** | **Zirkelbezug Budget ↔ Instrument.** `risiko_eur(instrument,…)` und `einsatz_eur(instrument,…)` brauchen das Instrument, das erst am Ende entsteht | Konvention: **das Etikett entscheidet sich am Spot-Budget**, danach gilt das Hebel-Budget. Ein Durchlauf, kein Iterieren |
| **F4** | **Töpfe ebenso.** `topf_frei_eur` wird vor `rechne()` aus dem Topf des Instruments geholt | dieselbe Konvention wie F3 |
| **F5** | **24 Codestellen** in 8 Modulen hängen an `instrument == "hebel"` | Stufe 3 ist der große Teil des Umbaus, nicht Stufe 0 |
| **F6** | **Die Marken erreichen `rechne()` nicht** — `widerstand` wird von keinem Aufrufer gefüllt | Durchreichung neu bauen; die Werte liegen in `_marken_werte` bereit |
| **F7** | **Der Vertrag verliert seine Plausibilitätsprüfung**, wenn die beiden Preisfelder gehen | Prüfung wandert auf `umgeworfen_preis_eur` — und **muss richtungsbewusst** sein, sonst wird F2 nachgebaut |
| **F8** | **Anlass: zwei Fingerabdrücke werden zu einem.** Gemessen an 37 Paaren: 59,5 % ändern sich gemeinsam, 8,1 % nur Spot, 0 % nur Hebel → **rund 53 % der Urteile bleiben** | die Stichprobe ist klein (die Läufe fallen selten auf dieselbe Minute). **Vor Stufe 3 auf voller Historie nachmessen** |
| **F9** | **Messreihenbruch**: bisherige Signale tragen ein Etikett aus dem Lauf, künftige eines aus der Rechnung | Stichtag setzen, Vergleiche nur innerhalb einer Seite |
| **F10** | **Längerer Prompt** durch den gemeinsamen Faktensatz | gegen R-T1…R-T12 prüfen. **Geprüft: N1–N5 hängen am Prompttext, nicht an den Antwortfeldern** — das Streichen ist dort folgenlos |

### 88.6 Deadloop-Sicherheit

> **Kein Kriterium darf ein Urteil verhindern. Es darf nur bestimmen, welcher
> Art das Urteil ist.**

| | Gate | Klassifikation |
|---|---|---|
| tut | **entfernt** Urteile | **ordnet** sie zu |
| Deadloop möglich | ja | nein |
| messbar | nein — was weg ist, hinterlässt keine Spur | ja |

**Kanarienvogel:** je Umlauf **Zahl der Urteile** und **Verteilung
spot/hebel** nebeneinander. Zahl konstant und Verteilung verschiebt sich =
Klassifikation. Zahl sinkt = irgendwo filtert etwas.

⚠️ **Achtung, die Zahl sinkt durch F8 gewollt um rund die Hälfte.** Der
Kanarienvogel muss deshalb **je Symbol** zählen, nicht je Lauf — sonst meldet
er den geplanten Umbau als Defekt.

**Zwei Stellen, an denen es doch eine stille Bremse würde:**

1. `RechnungBlockiert` unter der Mindestgröße — gemessen 0 von 59 bei 25 €
   Risiko, **muss trotzdem gezählt und gemeldet werden**.
2. Funding im 99. Perzentil (2.129 %/Jahr) — **kein Veto**: der Trade wird
   dann Spot.

### 88.7 Der Bau (technisch)

**Eine reine Funktion, zwei Aufrufer** — das Muster, dessen Fehlen am 70.4
schon einmal Werte auseinanderlaufen ließ.

```
agent/entscheidungsrechnung.py
    dimensioniere(kurs, atr, k, verlustanteil, einsatz_eur,
                  marke=None, umgeworfen_preis_eur=None,
                  ist_short=False, hebel_handelbar=True) -> dict
        # rein: ohne DB, ohne Uhr, ohne Netz
        # liefert stop_rel, stop_regel, betrag, hebel, etikett,
        #         gebunden_durch, tage_schaetzung
```

| Aufrufer | Zweck |
|---|---|
| `messe_hebelentscheidung.py` | Stufe 0 — über die volle OHLC-Historie |
| `rechne()` | Produktion — **erst in Stufe 3** |

**Datenquelle:** `DB_Backups/tradinginfotool_*.db.gz` im Austauschordner
(täglich vom Notebook), auspacken in den Scratchpad, `PRAGMA
integrity_check`. **Nicht die Desktop-Datenbank** — sie endet am 19.07.
(`data/gui_heartbeat.txt`).

**Prüfungen `--paket Dimension`, vor der ersten Messung:**

| | |
|---|---|
| Rein | zweimal derselbe Aufruf = dasselbe Ergebnis |
| Böden | jeder greift einzeln, der weiteste gewinnt, Deckel bindet |
| Grenzfall | Hebel exakt 1,0 → `spot`, Betrag folgt dem Risiko |
| Spiegelung | LONG/SHORT symmetrisch; SHORT ⇒ Etikett `hebel` |
| Handelbarkeit | Nicht-Krypto bekommt nie das Etikett `hebel` |
| Kein Filter | **nie `None`** — für jede Eingabe ein Ergebnis oder eine benannte Ausnahme |
| Mindestgröße | Unterschreitung wird gemeldet, nicht verschluckt |

### 88.8 Stufe 0 — was gemessen wird, heute

**OHLC reicht von 1985-10-01 bis 2026-08-18** (63 Symbole, 116.535 Zeilen).
Die Sprungfrage ist historisch beantwortbar; Beobachten wäre die schlechtere
Messung.

**Zwei Achsen, ein Feld statt einer Zeile:**
k aus {0,75 · 1,0 · 1,5 · 2,0 · 2,5} **mal** Verlustanteil aus
{1 % · 2 % · 5 % · 10 % · 15 %}

| Frage | Messung |
|---|---|
| Anteil Hebel/Spot | je Feld |
| **Sprungrate** je Asset | wie oft wechselt das Etikett — entscheidet über Hysterese |
| Rauschtreffer | je k, Horizont 5 und 20 Tage, auf frischen Daten |
| Betragsverteilung | Unterschreitungen der Mindestgröße |
| nötiger Vorsprung vor dem Zufall | je Feld |
| Streuung des Hebels von Tag zu Tag | die eigentliche Hysterese-Zahl |

⚠️ **Nicht messbar in Stufe 0:** Funding hat nur **einen Monat** Historie
(ab 2026-07-14, 39 Symbole). Diese eine Größe wächst tatsächlich erst an.

### 88.9 Was NICHT passiert

kein Eingriff in `rechne()` · kein k festgelegt · kein Verlustanteil geändert ·
keine Hysterese gebaut · keine Zusammenlegung der Läufe · keine Prompt-Änderung

### 88.10 Offene Entscheidungen des Nutzers

| | Stand |
|---|---|
| **Verlustanteil je Instrument** | heute 15 % für beide. Literatur 1–2 %. **Die eigentliche Spot/Hebel-Grenze** |
| **k** | offen — folgt aus der Rauschmessung |
| `hebel_max` | bindet nachweislich nie (0 von 59); RM-11 kann bei Verlustanteil unter 91 % **mathematisch nie** binden. Vorerst unangetastet |
| Aktionsvokabular beim Einstieg | `KAUFEN` behalten oder umbenennen (F1) |
| Laufende Positionen bei Volatilitätsanstieg | Stop nachziehen · verkleinern · unverändert — heute nirgends geregelt |

### 88.11 Reihenfolge

| Stufe | Inhalt | ändert Verhalten |
|---|---|---|
| **0** | reine Funktion + `--paket Dimension` + Messung über die Historie | **nein** |
| 1 | Verlustanteil und k festlegen | nein |
| 2 | Hysterese festlegen, aus der Sprungrate | nein |
| 3 | Prompt, Schema, Vertrag, `rechne()`, Läufe zusammenlegen, Kanarienvogel je Symbol | **ja** |

---

## Kapitel 89 — Stufe 0 gemessen: was besser wird und was schlechter (18.08.2026)

**Nichts geändert.** `rechne()` ist unberührt, die Produktion kennt die neue
Funktion nicht. Werkzeug: `messe_dimensionierung.py`, Daten aus dem
Notebook-Backup vom 18.08. (58 Symbole).

### 89.1 Das Feld — Anteil Hebel je (k, Verlustanteil)

| k \ VA | 1 % | 2 % | 5 % | 10 % | 15 % |
|---:|---:|---:|---:|---:|---:|
| **0,75** *(heute)* | 9 % | 33 % | 91 % | 97 % | **98 %** |
| 1,00 | 0 % | 21 % | 78 % | 93 % | 98 % |
| 1,50 | 0 % | 9 % | 48 % | 91 % | 93 % |
| 2,00 | 0 % | 0 % | 29 % | 78 % | 91 % |
| 2,50 | 0 % | 0 % | 21 % | 64 % | 90 % |

**Der Ist-Zustand steht in der Ecke mit 98 % Hebel.** Und die Tabelle zeigt,
welche Achse was tut: **der Verlustanteil entscheidet über das Etikett**
(waagerecht die großen Sprünge), **k über die Kosten** (senkrecht).

### 89.2 Die Sprungrate — Hysterese ist kaum nötig

Wechsel des Etiketts je 100 Handelstage, Median über alle Symbole:

| | maximal |
|---|---:|
| über das ganze Feld | **4,3** |

> **Ein Asset wechselt im Median höchstens alle 23 Handelstage die Schublade.**
> Das ist die Zahl, die über Hysterese entscheiden sollte — und sie sagt:
> **eine Hysterese wird nicht gebraucht.** Der Deadband-Aufwand aus der
> Literatur adressiert ein Problem, das wir messbar nicht haben.

### 89.3 Rauschtreffer — auf frischen Daten bestätigt

26.910 Anker, Horizont 5 Handelstage:

| Stop | wird getroffen |
|---:|---:|
| **0,75 ATR** *(heute)* | **57,3 %** |
| 1,00 ATR | 45,5 % |
| 1,50 ATR | 27,5 % |
| 2,50 ATR | 9,4 % |

Die alte Messung auf der Juli-Datenbank sagte 56,7 % — **auf frischen Daten
57,3 %.** Der Befund ist stabil.

### 89.4 Was besser wird — und was das NICHT heißt

| | Stop | Tage | Hebel | Betrag | zu klein | **nötiger Vorsprung** |
|---|---:|---:|---:|---:|---:|---:|
| **heute** (k 0,75 · VA 15 %) | 2,6 % | 2 | **5,82** | 1.000 € | 0 | **38,8 pp** |
| bestes Feld (k 2,5 · VA 1 %) | 8,6 % | 25 | **1,00** | 116 € | 0 | **11,6 pp** |

**Der nötige Vorsprung vor dem Zufall sinkt um den Faktor 3,3.**
10 von 25 Feldern liegen unter der Hälfte des heutigen Werts.

> ⚠️ **Was diese Spalte NICHT sagt:** dass die Trades besser laufen. Sie sagt,
> wie viel Treffsicherheit **über dem Zufall** nötig wäre, damit sie sich
> tragen. Kleiner ist *leichter*, nicht *gut*. Die Basisrate bleibt 33,3 %,
> und 11,6 pp Vorsprung sind immer noch mehr, als dieses Projekt je gemessen
> hat.

**Was schlechter wird**, ehrlich benannt:

| | |
|---|---|
| **Betrag** | 1.000 € → 116 €. Wer 1.000 € einsetzen will, kann das bei 1 % Verlustanteil nicht mehr |
| **Haltedauer** | 2 → 25 Handelstage. Aus Zwei-Tage-Geschäften werden Fünf-Wochen-Geschäfte |
| **Hebel verschwindet** | 5,82 → 1,00. Wer Hebelgeschäfte will, bekommt bei 1 % keine mehr |
| Mindestgröße | **0 Unterschreitungen** in allen 25 Feldern — der einzige befürchtete Nebeneffekt tritt nicht ein |

### 89.5 Der Config-Schlüssel, über den niemand mehr stolpern soll

`risiko_pro_trade_prozent_hebel: 1` ist **nicht obsolet** — `hebel_risk_gate.py`
und `risk_gate.py` lesen ihn, beide gehören zu den **alten** Pipelines. Die
Rollen-Kette liest ihn nicht; sie dimensioniert über
`betraege.VORGABE_VERLUSTANTEIL` (15 %).

**Behandlung statt Löschung:**

| | |
|---|---|
| `config.yaml` | Geltungsvermerk *„GILT NUR FUER DIE ALTEN PIPELINES"* mit Verweis auf `betraege.py` |
| `betraege.py` | Gegenverweis im Docstring von `verlustanteil()` — *„nicht zu verwechseln … wer das eine liest und das andere meint, irrt um den Faktor fünf"* |
| Prüfung | `--paket Dimension` hält **beide** Vermerke fest |

> Ein Schlüssel, der für die eine Kette gilt und für die andere nicht, ist
> gefährlicher als ein toter — deshalb steht der Geltungsbereich jetzt an
> beiden Enden.

⚠️ **Und die Prüfung selbst hatte den Fehler:** sie las über `_quelltext`,
das Kommentarzeilen entfernt — ein Geltungsvermerk *ist* ein Kommentar. Sie
schlug fehl, obwohl der Vermerk dastand. Jetzt liest sie roh.

### 89.6 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **1.116**, alle bestanden — **17 neu unter `--paket Dimension`** |
| Reinheit | zweimal derselbe Aufruf, zweimal dasselbe Ergebnis |
| drei Böden | jeder greift einzeln, der weiteste gewinnt, Obergrenze bindet |
| Grenzfall | Stop = Verlustanteil → **spot**, nicht hebel |
| SHORT | erzwingt das Etikett `hebel` |
| Handelbarkeit | ohne Hebel-Angebot entsteht keiner |
| Spiegelung | LONG/SHORT identischer Stopabstand |
| **nie still nichts** | 3 unbrauchbare Eingaben + 4 falsche Verlustanteile werfen **benannt** |
| freie Namen · Zahlen · Belege · Darstellung | 0 · 9/9 · 9/9 · bestanden |
| Simulation | 4 Gruppen, 9 Mails, 0 Fehler, 0 Lücken — **Produktion unverändert** |

### 89.7 Was jetzt entschieden werden kann

| | Messgrundlage |
|---|---|
| **Verlustanteil** | 1 % → 9 % Hebel · 2 % → 33 % · 15 % → 98 % (bei k 0,75) |
| **k** | Rauschtreffer 57,3 % (0,75) · 27,5 % (1,5) · 9,4 % (2,5) |
| **Hysterese** | **nicht nötig** — Sprungrate maximal 4,3 je 100 Tage |
| `hebel_max` | bindet weiterhin nie |

**Offen bleibt** die Funding-Achse — ein Monat Historie reicht nicht.

---

## Kapitel 90 — UMSETZUNGSPLAN Stufe 3: k = 2,0 und Verlustanteil 6 % (18.08.2026)

**Status: Plan, nichts gebaut.** Baut auf Kapitel 88 (Fassung 2) und den
Messergebnissen aus Kapitel 89.

### 90.1 Was gesetzt wird — und warum genau diese zwei Werte

| | Wert | Begründung |
|---|---:|---|
| **k** (ATR-Faktor des Rauschbodens) | **2,0** | Rauschtreffer **15,9 %** statt 57,3 % — in 5 von 6 Fällen entscheidet die These, nicht das Zappeln. Liegt zwischen Elder (2 ATR) und Chandelier (3 ATR) |
| **Verlustanteil** | **6 %** | = **2 % des Hebeltopfes** je Trade, der obere Literaturwert. Ergibt 45 % Hebel statt 98 % |

**Warum 6 % und nicht 3 %:** beide sind Literaturwerte (1 % bzw. 2 % des
Kapitals). 6 % ist der **halb so große Eingriff** — 53 Prozentpunkte
Verschiebung statt 88. Alles, was an F5 hängt (Töpfe, Cooldowns, Mailbetreff,
DB-Werte), wird entsprechend weniger durchgeschüttelt. **3 % bleibt der
nächste Schritt, nicht der erste.**

### 90.2 ⚠️ DIE REGLER-FRAGE — ist VA 3 später eine Zeile oder wieder Arbeit?

**Geprüft, mit unterschiedlichem Ergebnis je Größe:**

| | Zustand heute | |
|---|---|---|
| **Verlustanteil** | **ist bereits ein Regler.** `betraege._cfg(config, "verlustanteil")` liest ihn; nachgewiesen funktionieren **beide** Pfade: `rollen_kette.verlustanteil.hebel` und `risiko.rollen_kette.verlustanteil.hebel` | ✅ |
| **k** | `GRENZEN["stop_min_atr"] = 0,75` ist ein **fester Modulwert**. Der Kommentar daneben nennt zwar `risiko.sl_abstand_min_atr_faktor`, aber der Schlüssel steuert die **alten** Pipelines, nicht diese Zeile | ❌ |

**Daraus die Antwort auf die Frage:**

> **VA 3 %, 4 %, 8 % sind nach diesem Umbau eine Konfigurationszeile — kein
> Code, keine Detailarbeit.** Der Regler existiert bereits; in `config.yaml`
> steht heute nur kein Eintrag, also gilt die Codevorgabe 15 %.
>
> **k muss in diesem Umbau erst ein Regler werden** (Schritt S1). Danach gilt
> dasselbe für ihn.

**Der Preis, der bleibt** — und der ist nicht technisch: **jede Änderung an
VA verschiebt die Population zwischen den Schubladen und bricht damit die
Messreihe (F9).** Der Code kostet nichts, die Vergleichbarkeit schon. VA ist
deshalb ein Regler, den man *selten* dreht, nicht ein Schalter zum Probieren.

### 90.3 Die Schritte — jeder einzeln prüfbar und einzeln rückholbar

**S1 bis S4 ändern kein beobachtbares Verhalten.** Der Wechsel passiert in
einem einzigen Schritt (S5), und der ist eine Konfigurationszeile.

| Schritt | Inhalt | Fallstricke | ändert Verhalten |
|---|---|---|---|
| **S1** | **k wird ein Regler.** `GRENZEN["stop_min_atr"]` aus `config` lesbar, **Vorgabe bleibt 0,75** | — | **nein** |
| **S2** | **Marken durchreichen.** `_marken_werte` erreicht `rechne()`; noch ohne Wirkung, weil `_stop_abstand` sie nicht benutzt | **F6** | **nein** |
| **S3** | **Vertrag umbauen.** Richtungsbewusste Prüfung auf `umgeworfen_preis_eur`; danach `einstieg_eur`/`stop_eur` aus Prompt und Schema streichen | **F7**, Teil von **F1** | **nein** (die Prüfung ersetzt eine gleichwertige) |
| **S4** | **Prompt und Schema vereinheitlichen.** Gemeinsames Aktionsvokabular beim Einstieg, Instrument nur noch beim Bestand, **ein** Faktensatz | **F1 · F2 · F10** | **nein** |
| **S5** | **`rechne()` auf `dimensioniere()` umstellen**, dann `k = 2,0` und `verlustanteil = 0,06` in `config.yaml` | **F3 · F4 entfallen** (s. u.) | **JA** |
| **S6** | **Läufe zusammenlegen** + Kanarienvogel **je Symbol** | **F5 · F8 · F9** | **JA** |

**F3 und F4 entfallen ersatzlos**, weil der Verlustanteil für Spot und Hebel
derselbe ist:

```
Hebel = Verlustanteil / Stopabstand      ← kein Einsatz, kein Topf
```

Das Etikett ist damit **wohldefiniert, ohne das Instrument zu kennen.** Der
Zirkelbezug entsteht erst, wenn die beiden Instrumente verschiedene
Verlustanteile bekommen — was hier ausdrücklich **nicht** geschieht.

### 90.4 Was je Schritt geprüft wird

| Schritt | Prüfung |
|---|---|
| **S1** | ohne Konfigurationseintrag ist jedes Ergebnis **bitgleich** zu heute; mit Eintrag greift der Wert |
| **S2** | die Marke kommt an und ist dieselbe wie in der Mail — **eine Quelle, nicht zwei** (Umbauplan 70.4) |
| **S3** | SHORT mit Stop über dem Einstieg wird **nicht** mehr degradiert; ein widersprüchlicher Widerlegungspreis schon. `ERÖFFNEN` ist nicht mehr ungeprüft |
| **S4** | jedes Instrument bekommt ein gültiges Schema; kein Modell antwortet mit einem unbekannten Enum; R-T1…R-T12 und N1–N5 laufen durch |
| **S5** | `rechne()` und `dimensioniere()` liefern für dieselbe Eingabe **dasselbe** — die reine Funktion ist die einzige Quelle |
| **S6** | **Zahl der Urteile je Symbol konstant**, nur die Verteilung verschiebt sich |

### 90.5 Der Kanarienvogel und die Rückfahrkarte

**Je Umlauf zu zählen und nebeneinander zu berichten:**

| Größe | erwartet |
|---|---|
| Urteile **je Symbol** | **konstant** (nicht je Lauf — der halbiert sich gewollt, F8) |
| Verteilung spot/hebel | verschiebt sich von 98/2 auf rund **55/45** |
| `RechnungBlockiert` unter Mindestgröße | gemessen 0, **muss trotzdem gezählt werden** |
| `Andrang`/`Ausfall` bei Rolle G | unverändert |

**Rückfahrkarte:** S5 ist eine Konfigurationszeile. Fällt etwas auf, wird
`verlustanteil` auf 0,15 und `stop_min_atr` auf 0,75 zurückgesetzt — **ohne
Codeänderung.** S6 ist die einzige Stufe, die einen echten Rückbau bräuchte;
sie kommt deshalb zuletzt und getrennt.

### 90.5b Cluster-Grenze — OPTIONAL, und sie löst kein Problem

**Nutzerentscheidung 18.08.: aufnehmen, aber als Option, und erst wenn das
System läuft.**

| | |
|---|---|
| Messgrundlage | 40 Kryptowerte, mittlere paarweise Korrelation **0,50**, effektiv **1,9 unabhängige Wetten** |
| Literatur | korrelierte Positionen als **eine** Risikoeinheit, Gruppe bei 3 % gedeckelt |
| eigener Befund | Verlustquelle ist die Wiederholung — 5 Symbole = 102 % des Minus |
| heute | Hebel gedeckelt bei 3.000 EUR, **Spot überhaupt nicht** (`toepfe_deckel_eur.spot` leer) |

**Kein Qualitäts-Gate.** Sie sagt nicht „dieser Trade ist schlecht", sondern
„du bist in dieser Wette bereits voll" — dieselbe Bauform wie der bestehende
Hebeltopf. Der Deadloop kam von Filtern, die dem Modell WIDERSPRACHEN; ein
Kapazitätsdeckel widerspricht ihm nicht.

**Sie gehört zu S5**, weil Heat die Summe der Risiken ist und das Risiko je
Trade der Verlustanteil — getrennt zu bauen hieße, dieselbe Größe zweimal
festzulegen.

> ⚠️ **Was sie NICHT tut, ausdrücklich:** sie löst das Auswahlproblem nicht.
> „Jeden Tag ein guter Tag zum Traden" bleibt im URTEIL bestehen — 52 % aller
> Urteile sind Einstiege, am 17.08. waren es 142 an einem Tag. Die
> Cluster-Grenze begrenzt, wie viele davon GLEICHZEITIG gehandelt werden
> dürfen. Mehr nicht.

### 90.6 Was NICHT in diesem Umbau ist

- **keine Hysterese** — gemessen nicht nötig (max. 4,3 Wechsel je 100 Tage)
- **kein Eingriff an `hebel_max`** — bindet nachweislich nie
- **keine Cluster-/Heat-Grenze** — fachlich begründet (Korrelation 0,50,
  effektiv 1,9 unabhängige Wetten), aber ein **eigenes** Vorhaben
- **keine Funding-Bedingung** — ein Monat Historie reicht nicht
- **kein VA 3 %** — der nächste Schritt, nicht dieser

### 90.7 Restrisiko, offen benannt

| | |
|---|---|
| **Der Charakter der Geschäfte ändert sich** | Haltedauer 2 → 16 Handelstage, Betrag 1.000 → 874 €, Hebel 5,8 → 1,2 im Median. Das ist gewollt, aber spürbar |
| **F8 ist auf 37 Paaren gemessen** | vor S6 auf voller Historie nachzumessen |
| **Der nötige Vorsprung bleibt bei 14,6 pp** | über der Basisrate von 33,3 %. **Kein Trade trägt sich dadurch** — die Lücke schrumpft von 38,8 auf 14,6, sie schließt sich nicht |
| **S4 berührt den Prompt** | und damit die einzige Ebene, deren Verhalten wir nicht deterministisch vorhersagen können. Deshalb steht S4 **vor** S5: erst der Prompt stabil, dann die Zahlen |

---

## Kapitel 91 — PLAN: die Extreme sichtbar machen (18.08.2026)

**Status: Plan, nichts gebaut.** Nutzerfreigabe für **Punkt 1** liegt vor:
*„kein Filter — saubere und FETTE Kennzeichnung."*

### 91.1 Die Frage, aus der dieses Kapitel entstand

Nutzerfrage 18.08., und sie ist besser gestellt als alles, was der Umbauplan
bisher beantwortet:

> *„Wie finde ich unter den Kryptos Trades mit Potential? Ein Smallcap ist seit
> 150 Tagen im Abwärtstrend — ist der Coin tot oder nur Bodenbildung für einen
> Spot-Kauf? Und selbst wenn er tot ist: mit Hebel und kurzfristigem Einstieg
> kann ich eine Chance nutzen — ich muss sie erkennen können."*

**Das sind zwei verschiedene Fragen mit zwei verschiedenen Indikatorfamilien:**

| | Frage | Horizont | Indikatoren laut Literatur |
|---|---|---|---|
| **Spot** | tot oder Boden? | Monate | On-chain-Aktivität bei fallendem Kurs · **Entwickleraktivität** · Börsenbestände |
| **Hebel** | Bewegung in Sicht? | 2–5 Sitzungen | **Funding extrem negativ** · hohes OI bei negativem Funding · niedriger Long-Anteil |

### 91.2 ⚠️ DER BEFUND: wir sammeln sie bereits

```
mindestkriterien.QUELLEN_G = {
  'terminmarkt': ('oi_aenderung_pct', 'funding_perzentil',
                  'long_anteil_pct', 'divergenz'),   <- die Squeeze-Indikatoren
  'onchain':     ('boersenfluss',),                  <- der Akkumulations-Indikator
  'optionsmarkt': ('dvol', 'skew'), ...
}
```

**Genau die Größen, die die Literatur nennt** — 120.641 Funding-Messwerte
liegen in der Datenbank.

**Der Fehler ist nicht, dass sie fehlen, sondern wie wir sie benutzen.** Aus
dem eigenen Befund vom 17.08.:

> *„Funding-Rate und Open Interest haben dokumentierte Vorhersagekraft — **nur
> an den Extremen** (Granger-Tests über 35,7 Mio. Minutenbeobachtungen). Unsere
> Sätze sagen in vier von fünf Fällen ‚im gewohnten Bereich', also genau dort,
> wo die Literatur nichts findet."*

**Wir schreiben den Indikator in 80 % der Fälle hin, wo er nichts sagt — und
ziehen in den 20 %, wo er etwas sagt, keine Konsequenz.** Dasselbe Muster wie
bei den Marken, bei `uebersprungen`, bei `funding_eur_tag`: eingesammelt,
nicht angeschlossen.

### 91.3 Punkt 1 — was gebaut wird

**Die Schwelle muss nicht erfunden werden: sie existiert schon.**
`marktlage._einordnung` teilt Perzentile in *gewohnt* und *auffällig*;
gemessen sind **79 von 101** Werten „gewohnt", also **rund ein Fünftel
auffällig** — genau die Größenordnung, die die Literatur als „Extreme" meint.

Drei Änderungen, alle additiv:

| | |
|---|---|
| **1. Merkmal am Signal** | jedes auffällige Terminmarkt- oder On-chain-Merkmal wird als **Flag am Signal gespeichert** (Name, Wert, Perzentil, Richtung) |
| **2. Kennzeichnung in der Mail** | die betreffende Zeile wird **fett** gesetzt — und behält ihre Richtungsfarbe (▲ grün / ▼ rot), damit sie von den schwarz-fetten **Handelsparametern** unterscheidbar bleibt |
| **3. Zeile im Export** | Anzahl und Art der Auffälligkeiten je Umlauf |

**Ohne Flag ändert sich nichts** — die Zeile bleibt, wie sie ist. Und die
gewohnten Werte werden weiterhin über `ohne_gewohntes()` zusammengefasst; die
Kennzeichnung ist genau deren Gegenstück.

### 91.4 Was ausdrücklich NICHT passiert

> **Kein Filter. Keine Bevorzugung. Kein Gate.**

- Ein Signal mit auffälligem Funding wird **nicht** eher versendet
- Ein Signal ohne Auffälligkeit wird **nicht** unterdrückt
- Die Reihenfolge, die Töpfe, die Cooldowns bleiben unberührt
- Das Modell erfährt nichts Neues — die Fakten stehen schon im Prompt

**Es ist eine Kennzeichnung, keine Entscheidung.** Damit gilt die stehende
Regel: *kein Kriterium darf ein Urteil verhindern, es darf nur bestimmen,
welcher Art das Urteil ist.* Hier bestimmt es nicht einmal das — es macht nur
sichtbar, was ohnehin dasteht.

### 91.5 Wozu das gut ist: es macht die Literaturfrage messbar

Sobald das Flag am Signal steht, lässt sich **zum ersten Mal** fragen:

> **Verhalten sich Signale mit auffälligem Funding/OI anders als die übrigen?**

| | |
|---|---|
| historisch | Funding reicht nur bis **2026-07-14** — ein Monat, 39 Symbole. Für einen ersten Blick, nicht für ein Urteil |
| laufend | jedes neue Signal trägt das Flag; die Auswertung wächst mit |
| Maßstab | dieselbe wie immer: **schlägt es die Basisrate?** |

**Erst wenn diese Frage mit Ja beantwortet ist, darf aus der Kennzeichnung
eine Unterscheidung werden.** Das ist die Reihenfolge, deren Umkehrung den
Deadloop erzeugt hat.

### 91.6 Punkt 2 — die zwei fehlenden Quellen (danach)

Beide gehören zur **Spot**-Frage, also genau zu der aus dem Nutzerbeispiel:

| Größe | Quelle | Kosten | Stand |
|---|---|---|---|
| **Entwickleraktivität** (Commits, aktive Entwickler) | GitHub-API, öffentliche Repos | **frei** | fehlt vollständig |
| **Netzwerkaktivität** (aktive Adressen) | CoinMetrics Community — **wir rufen CoinMetrics bereits täglich auf** | **frei** | fehlt vollständig |

**Der beste „ist der Coin tot"-Indikator der Literatur — Entwickleraktivität —
fehlt uns komplett**, und er kostet nichts.

⚠️ **Neue Quelle = neue Zeile in `datenfrische`**, sonst wird sie still nicht
überwacht (dieselbe Falle wie bei `SYMBOL_ZU_COT_ROHSTOFF`).

### 91.7 Punkt 3 — erst danach eine Unterscheidung

Ob aus den Merkmalen je Strategie verschiedene Fragen werden, ist **nach**
Punkt 1 und 2 zu entscheiden, nicht vorher. Ohne Messung wäre es geraten.

### 91.8 Fallstricke

| # | | Umgang |
|---|---|---|
| **G1** | **Zwei Sorten Fett in derselben Mail.** Schwarz-fett sind heute die Handelsparameter (Einstiegszone, Stop, TP …) | die Auffälligkeit bleibt **farbig** fett (▲/▼), nicht schwarz — sonst wird „fett" bedeutungslos |
| **G2** | **R-T6, kein konstantes Feld.** Erschiene die Kennzeichnung fast immer, wäre sie wertlos | rund ein Fünftel erwartet; **die Rate ist zu messen und zu berichten**, nicht anzunehmen |
| **G3** | **Ohne Speicherung ist nichts messbar.** Eine Kennzeichnung nur in der Mail wäre in einer Woche verloren | Flag gehört an das Signal in der Datenbank, nicht nur in den Text |
| **G4** | **Ein Monat Funding-Historie** | für einen ersten Blick, ausdrücklich nicht für ein Urteil |
| **G5** | **Die Versuchung, sofort zu filtern** | genau das ist der Deadloop. Punkt 1 ist absichtlich folgenlos |

### 91.9 Reihenfolge

| | Inhalt | ändert Verhalten |
|---|---|---|
| **P1a** | Flag am Signal speichern | **nein** |
| **P1b** | Kennzeichnung in Mail und Export | **nein** (nur Darstellung) |
| **P1c** | Messung: trägt das Extrem? | **nein** |
| P2 | GitHub- und CoinMetrics-Anbindung | nein |
| P3 | Unterscheidung je Strategie — **nur bei positivem Befund** | ja |

---

## Kapitel 92 — S1 gebaut: der Rauschboden ist ein Regler (18.08.2026)

**Verhalten unverändert.** Ohne Eintrag in der Konfiguration rechnet die Kette
bitgleich wie zuvor — nachgewiesen im Ende-zu-Ende-Lauf.

### 92.1 Was gebaut wurde

| | |
|---|---|
| `betraege.stop_min_atr(config)` | liest den Faktor aus **beiden** Konfigurationspfaden, gibt **`None`**, wenn nichts gesetzt ist |
| `entscheidungsrechnung._stop_abstand(..., min_atr=None)` | benutzt ihn statt der festen `GRENZEN["stop_min_atr"]` |
| `rechne(..., stop_min_atr=None)` | reicht ihn durch |
| `rollen_lauf` | `stop_min_atr=BE.stop_min_atr(config)` |

**`None` statt eines wiederholten Vorgabewerts.** Die Vorgabe 0,75 steht an
genau **einer** Stelle; sie in `betraege` zu wiederholen hieße, dieselbe Zahl
an zwei Orten zu pflegen — der Fehler aus Umbauplan 70.4.

### 92.2 ⚠️ Wo der Regler wirkt — und wo nicht

```
Modell liefert einen Preis  →  Klemme RM-1b/1c   ← HIER wirkt k
Modell liefert nichts       →  _stop_aus_atr     ← hier NICHT (2,5 ATR)
```

**Das ist kein Mangel, sondern der Produktionsfall:** gemessen liefert das
Modell **12 von 12** Mal einen Preis, und **10 davon** liegen im Rauschen und
werden auf die Klemme gehoben. Der Regler greift also genau dort, wo die
Produktion landet.

Der ATR-Rückfall benutzt weiterhin `stop_ziel_atr = 2,5` — zufällig der Wert,
den die Messung als sinnvoll ausweist. **Dass beide Zweige denselben Faktor
benutzen sollten, gehört zu S5**, nicht hierher.

Nachgerechnet auf dem Produktionspfad (Kurs 100, ATR 4, Widerlegungspreis 99):

| k | Stop | Hebel |
|---:|---:|---:|
| 0,75 *(heute)* | 3,00 % | 5,0 |
| 1,5 | 6,00 % | 2,5 |
| **2,0** | **8,00 %** | **1,9** |

### 92.3 Der Wert wird geprüft, nicht geglaubt

`stop_min_atr` außerhalb von (0, 10] wird abgewiesen. **25 statt 2,5 wäre
sonst ein stiller Faktor zehn** — dieselbe Klasse wie „15 statt 0,15" beim
Verlustanteil.

### 92.4 Gegenprüfung

| | |
|---|---|
| Paketprüfungen | **1.123**, alle bestanden — **7 neu unter `--paket Dimension`** |
| **bitgleich ohne Eintrag** | `rechne(**e) == rechne(**e, stop_min_atr=None)` |
| beide Konfigurationspfade | `rollen_kette.*` und `risiko.rollen_kette.*` |
| unsinnige Werte | 0, −1, 11 werden **benannt** abgewiesen |
| Wirkung auf dem Produktionspfad | 3,00 % → 8,00 %, Hebel 5,0 → 1,9 |
| Durchreichung | am Quelltext von `rollen_lauf` geprüft |
| freie Namen · Zahlen · Belege · Darstellung | 0 · 9/9 · 9/9 · bestanden |
| **Ende zu Ende** | Simulation: 12 Aufrufe an `rechne()`, **alle mit `None`** — 4 Signale, 4 Mails, 0 Fehler, 0 Lücken |

**Der Ende-zu-Ende-Nachweis ist der wichtigste:** er zeigt, dass der Regler
die Aufrufstelle erreicht **und** dass ohne Konfigurationseintrag nichts
passiert. Ein Regler, der die Aufrufstelle nicht erreicht, wäre Dekoration;
einer, der ungewollt greift, wäre ein Verhaltenswechsel durch die Hintertür.

### 92.5 Nächster Schritt

**S2 — die Marken durchreichen** (F6 aus 88.5). Ebenfalls verhaltensneutral:
`_marken_werte` erreicht `rechne()`, ohne dass `_stop_abstand` sie schon
benutzt.

### 92.6 S2 gebaut: die Marke auf der Stopseite (18.08.2026)

**Reine Verkabelung, Nutzerentscheidung A** — der Stop bewegt sich nicht.

| | |
|---|---|
| `rollen_lauf._marke_am_stop(bloecke, ist_short)` | LONG → Unterstuetzung, SHORT → Widerstand |
| `rechne(..., marke_stop_eur=None)` | nimmt sie entgegen, traegt sie im Ergebnis |
| angeschlossen | **erst in S5** |

⚠️ **DIE FALLE, DIE DABEI UMGANGEN WURDE.** `rechne()` hat bereits einen
Parameter `widerstand` — ihn zu fuellen waere der naheliegende Weg und waere
falsch: er geht an `_ziel()` und wuerde den **Widerstandsdeckel** wieder
scharf schalten, der am 17.08. gemessen verworfen wurde (44 von 44 Symbolen
gedeckelt, 98 % unter CRV 0,5, Median 0,21). Die Stopmarke nimmt deshalb
einen **eigenen** Weg.

**Sichtbarkeit vorher geprueft, nicht angenommen:** `_bloecke_anlass` wird in
Zeile 651 gesetzt, `rechne()` in Zeile 1126 gerufen — beide in `_ein_asset`
(ab 596), **kein `def` dazwischen**. Genau die Falle der freien Namen, die in
diesem Projekt dreimal zugeschlagen hat.

⚠️ **Und ein Fehler in der eigenen Pruefung:** sie suchte `"widerstand="` im
Quelltext und fand **ihren eigenen Warnhinweis im Docstring**. `_quelltext`
entfernt Kommentarzeilen, aber **keine Docstrings**. Jetzt prueft sie am
**Syntaxbaum**: kein `ast.Call` uebergibt das Schluesselwort. Dieselbe Klasse
wie Methodik 2.40, nur eine Etage tiefer.

**Gegenprueft:** 1.129 Pruefungen (6 neu) · Marke aendert Stop und Hebel
nicht · steht im Ergebnis · LONG/SHORT nehmen die richtige Seite · leere
Bloecke geben `None` · freie Namen 0 · drei Selbsttests · **Ende zu Ende:
12 Aufrufe, 4 davon mit Stopmarke, Stop unveraendert**, 9 Mails aus 4
Gruppen ohne Fehler und ohne Luecke.

### 92.7 S3 gebaut: der Vertrag prüft die richtige Zahl (18.08.2026)

**Der erste Schritt, der den Prompt berührt.**

| vorher | nachher |
|---|---|
| `einstieg_eur` und `stop_eur` **verlangt**, von `rechne()` **nie gelesen**, und trotzdem tödlich | **entfernt** aus Prompt und Schema |
| Prüfung nur bei `KAUFEN`/`NACHKAUFEN` — **`ERÖFFNEN` ungeprüft** | alle drei Einstiegsaktionen |
| **keine Richtung** — SHORT mit korrektem Stop wurde still zu NICHTS_TUN | **richtungsbewusst** |
| geprüft wurde eine Zahl, die das Modell nicht schätzen kann | geprüft wird der **Widerlegungspreis** — die eine Zahl, die ihm gehört |

**Fehlen bleibt erlaubt.** Das Schema lässt `null` ausdrücklich zu — nicht
jede Beobachtung hat einen Kurs, und eine erzwungene Zahl wäre erfunden. Nur
ein **Widerspruch** wird beanstandet.

#### Doku-Gegenprüfung (Nutzerauftrag)

| Stelle | Wirkung | erledigt |
|---|---|---|
| `Rollenkonzept_Entwurf_10_08.md` | nennt beide Felder als Antwortfelder — **wird durch S3 zusätzlich falsch** | Nachtrag im Standvermerk |
| `Umbauplan` 88.4 · `Entscheidungslog` | beschreiben den **Plan**, sie zu entfernen | bleibt richtig |
| `gegenpruefer_rollen._VERBOTEN_FUER_RICHTUNG` | verbietet Felder, die es nicht mehr gibt | gekennzeichnet, **nicht gestrichen** |
| `signal_abbildung` · `ui/trade_chart` · `rollen_lauf:1207` | lesen `rechnung.get("stop_eur")` — die **gerechneten** Felder | **unberührt** |

> ⚠️ **Gleicher Name, zwei Herkünfte.** `einstieg_eur`/`stop_eur` gibt es
> als Antwortfeld des Modells **und** als Ergebnisfeld von `rechne()`. Nur
> die ersten sind weg. Eine Prüfung hält beides auseinander.

**Gegenprüft:** 1.139 Prüfungen (10 neu) · sechs Vertragsfälle einzeln
(LONG/SHORT × richtig/falsch/fehlend, plus ohne Kurs) · Schema und Prompt
nachgewiesen bereinigt · gerechnete Felder weiterhin vorhanden · freie Namen
0 · drei Selbsttests · **Prompt-Matrix** sauber · Simulation 9 Mails aus 4
Gruppen, 0 Fehler, 0 Lücken.

### 92.8 S4 gebaut: ein Faktensatz statt zwei (18.08.2026)

**⚠️ Korrektur am eigenen Plan.** Kapitel 90 hatte F1 (gemeinsames
Aktionsvokabular) und F2 (`richtung`) in S4 gelegt. Beide gehören dorthin
**nicht**:

> Ein gemeinsames Vokabular ist erst nötig, wenn die beiden Läufe
> **zusammengelegt** werden. Bis dahin kennt jeder Lauf sein Instrument, und
> das Enum darf davon abhängen. **44 Codestellen** hängen an `ERÖFFNEN` —
> sie jetzt anzufassen wäre Risiko ohne Anlass.

**F1 und F2 sind nach S6 verschoben**, wo die Zusammenlegung sie erzwingt.
S4 ist damit F10: ein Faktensatz.

#### Was geändert wurde

| Bereich | vorher | nachher |
|---|---:|---:|
| `krypto_spot` | **1** Zusatzfakt | **4** |
| `krypto_hebel` | 4 | 4 |
| aktien · rohstoffe · themen_etf · hedge | unverändert | unverändert |

**Die Begründung war das Instrument, und sie trägt nicht.**
Finanzierungsrate, Put-Skew und der Anteil der Long-Konten sagen etwas über
die **Positionierung im Markt** — und die ist dieselbe, ob man sie gehebelt
handelt oder nicht. Es sind zudem genau die Indikatoren, die die Literatur
für die kurzfristige Chance nennt (hohes Open Interest bei negativem Funding
= überfüllte Shortseite).

#### ⚠️ Das ist KEINE neutrale Änderung

Kapitel 90 hatte behauptet, S1 bis S4 seien verhaltensneutral. **Für S4
stimmt das nicht:** ein größerer Faktensatz heißt ein anderer
Fingerabdruck — und damit eine andere Auslöserate bei Spot. Die Richtung ist
absehbar (mehr bewegliche Fakten → häufigeres Auslösen), die Größe nicht.
**Zu beobachten, nicht zu schätzen.**

Promptlänge nach der Änderung: Spot **2.110**, Hebel **2.414** Zeichen —
beide weit unter den 34.611 der alten Kette.

**Gegenprüft:** 1.143 Prüfungen (4 neu) · Faktensätze identisch · andere
Klassen unberührt · **Vokabular hängt weiterhin am Instrument** (als Prüfung
festgehalten, damit die Verschiebung nach S6 nicht vergessen wird) · freie
Namen 0 · drei Selbsttests · Prompt-Matrix unverändert · Simulation 9 Mails
aus 4 Gruppen, 0 Fehler, 0 Lücken.

### 92.9 S5 gebaut: der Wechsel (18.08.2026)

**Der Schritt, der die Zahlen dreht.** Zwei Konfigurationszeilen — und eine
Codeänderung, die sie erst wirksam macht.

#### Die Stopregel steht jetzt an EINER Stelle

`_boeden(kurs, atr, k, marke, widerlegung, ist_short)` liefert die benannten
Untergrenzen; **`_stop_abstand` und `dimensioniere` benutzen beide diese
Funktion.** Vorher stand die Rechnung zweimal da — der Fehler aus 70.4,
diesmal vermieden statt nachgebaut.

| Boden | woher |
|---|---|
| **Rauschen** | `max(2,5 % Kurs, k × ATR)` |
| **Struktur** | Marke ± 0,25 ATR — **seit S5 angeschlossen** |
| **These** | Widerlegungspreis des Modells |

⚠️ **Der ATR-Rückfall bleibt Untergrenze**, wenn das Modell nichts sagt. Ohne
ihn bekäme ein Signal ohne Widerlegungspreis bei k < 2,5 plötzlich einen
**engeren** Stop als vorher — eine Verschlechterung durch die Hintertür, und
zwar dort, wo ohnehin am wenigsten bekannt ist.

#### Die zwei Zeilen

```yaml
rollen_kette:
  stop_min_atr: 2.0
  verlustanteil: {spot: 0.06, hebel: 0.06, absicherung: 0.06}
```

**Für beide Instrumente derselbe Verlustanteil** — und das ist kein Zufall:
wären sie verschieden, hinge das Etikett davon ab, welches Budget man vorher
gewählt hat. **F3 und F4 aus 88.5 entfallen damit ersatzlos.**

#### Gemessen an der echten Kette

| | vorher | nachher |
|---|---:|---:|
| Stopabstand | ~3 % | **4–6 %** |
| Hebel (Median) | 5,0 | **1,00** |
| Anteil mit Hebel | 98 % | **7 von 16 = 44 %** |
| Risiko je Trade | 150 € | **60 €** (= 2 % des Topfes) |

**Alle drei Böden entscheiden in der Praxis** — „jenseits der nächsten Marke",
„Widerlegungspreis des Modells" und „Rauschboden RM-1b/1c" stehen
nebeneinander in denselben neun Mails.

#### Zwei Prüfungen mussten nachgezogen werden

| | |
|---|---|
| „ein 1,26-%-Stop kommt nicht durch" | erwartete das Wort **„Rauschen"**, die Regel heißt jetzt **„Rauschboden"** — Wortlaut, kein Verhalten |
| „die Marke ändert den Stop noch NICHT" | war für **S2** richtig und ist mit S5 überholt. **Erwartung nachgezogen, nicht die Änderung zurückgedreht** |

**Gegenprüft:** 1.143 Prüfungen · sieben Stopfälle einzeln (ohne alles · These
im Rauschen · These weit · Marke gewinnt · These schlägt Marke · Obergrenze ·
k = 2,0 mit Marke) · freie Namen 0 · drei Selbsttests · Simulation 9 Mails aus
4 Gruppen, 0 Fehler, 0 Lücken.

#### Rückfahrkarte

Die beiden Konfigurationszeilen löschen — **ohne Codeänderung** ist der alte
Zustand wieder da.
