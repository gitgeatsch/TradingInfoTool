# Status und Messplan — der Hebel, nach Standards und Regeln

**25.09.2026.** Nutzerauftrag: *„status und weitere messungen nach standards
und regeln"*

---

# TEIL A — DER STATUS

## § A1 ✔ Was reproduziert und damit GESICHERT ist

| | Werkzeug | Ergebnis |
|---|---|---|
| **R-R11** | `n78_terminmarkt_kanaele.py` (Original, normgerecht) | Basis exakt: 122 Symbole, 1.415–1.734 Tage, Mengenzahl je Kandidat |
| `long_bias` auf `bewegung_r` | dito | **0 von 3** — reproduziert |
| `top_bias` | dito | **0 von 2** — reproduziert |
| **Referenz** `oi_aenderung` | dito | **3 von 3** (+0,047 / +0,021 / +0,013) — der Aufbau stimmt |
| **Kontrolle** `zufall` | dito | 0 von 4 |
| **N-17b** | `messe_kandidaten_redundanz.py` (Original) | `long_bias × top_bias` **+0,954** gegen +0,955 |

⭐ **Die Referenz ist der Grund, warum diesen Läufen zu trauen ist.** Ohne
sie wäre ein Nullbefund nicht von einem kaputten Aufbau zu unterscheiden.

## § A2 ⚠️ Was NEU erkannt wurde — und es dreht das Bild

**`long_bias` ist mit FÜNF Größen redundant, nicht mit einer** (Schwelle
|ρ| ≥ 0,2, Median je Kalendertag):

| gegen | ρ |
|---|---|
| `top_bias` | **+0,954** |
| `schnitt50` | −0,375 |
| `vola` | −0,341 |
| `rsi` | −0,291 |
| `spanne_aus` | −0,226 |

➤ **Selbst wenn er auf `barriere` trägt, wäre er kein eigener Beitrag** —
er zählte einen Effekt doppelt, den `vola` und `schnitt50` bereits tragen.

**Und der Umkehrschluss:** `taker_bias × rsi` = **+0,004** — der **einzige
unbelastete** der vier. Das Register nennt ihn *„DER AUSSICHTSREICHSTE"*,
und in R-R11 war er der einzige mit einer tragenden Zelle (50 %: +0,0177,
nicht robust).

⚠️⚠️ **Damit ist meine Kandidatenauswahl vom 25.09. umgekehrt:** Ich hatte
`long_bias` als Fund gemeldet — er ist der am schwersten belastete.
`taker_bias`, den ich verworfen hatte, ist der einzige saubere.

## § A3 ⚠️ Was unter Vorbehalt steht

| Befund | Vorbehalt |
|---|---|
| **2.583** Gleichstand unschuldig | ✔ hält (Zählung, zwei Gegenprüfungen) |
| **2.587** Querschnitt 18 statt 116 | ✔ hält (Zählung) |
| **2.586** K5 gefallen | ⚠️ Altbestandswerkzeug · **aber** die Fehler gingen alle Richtung *zu optimistisch*, ein Nullbefund wird davon nicht falsch |
| **2.585** Basisrate nicht vorhersagbar | ⛔ **95. statt 90. Perzentil · keine Trennschärfe** — hier *ist* der Nullbefund die Aussage, und ohne Trennschärfe heißt er auch „zu wenig gesehen" |

## § A4 Die offenen Punkte, sortiert

| | | |
|---|---|---|
| **O-1** | ⭐ **Die `barriere`-Spur** — die Hebel-Frage, laut Register **NIE gemessen** | bereit |
| **O-2** | **P-1**: Rangfenster für 6–72 h | Vorabfestlegung 11 liegt |
| **O-3** | **Der Querschnitt**: 18 Symbole → Terzile statt Fünftel? | ungemessen |
| **O-4** | **Vier Werkzeuge an `messnorm` binden** | Handwerk |
| **O-5** | **2.585 nachziehen** (90. Perzentil, Trennschärfe) | vor Verwendung |
| **O-6** | **`messe_zusammenspiel_beitraege`**: Urteil ohne Nullpunkt | zurücknehmen oder nachrüsten |
| **O-7** | `taker_bias` 1/3 statt 0/3 — Ursache ungeklärt | benannt |

---

# TEIL B — DER MESSPLAN

## § B1 ⭐ Die nächste Messung: O-1, die `barriere`-Spur

**Nutzervorschlag 25.09., und er ist methodisch stärker als er klingt:**

> *„zuerst die bekannten und tragenden Beiträge und dann die offenen
> Beiträge"*

➤ **Das ist die POSITIVKONTROLLE auf der neuen Zielgröße** — genau das, was
allen meinen Messungen gefehlt hat.

| Ausgang | Bedeutung |
|---|---|
| Die tragenden tragen auch auf `barriere` | ✔ die Zielgröße funktioniert → die offenen sind sinnvoll messbar |
| Sie tragen **nicht** | ⛔ **die `barriere`-Spur ist tot** — ein Nullbefund bei den offenen wäre dann wertlos, weil er nichts über die Kandidaten sagt |

⚠️ **Ohne diesen Schritt ist ein „trägt nicht" auf `barriere` nicht
interpretierbar.**

## § B2 Der Aufbau — Standard für Standard

| Regel | Umsetzung |
|---|---|
| **Werkzeug** | `n78_terminmarkt_kanaele.py`, nur `lage` umgestellt — **kein Neubau** |
| **Lage** | `Lage(instrument="hebel", strategie="einstieg")` |
| **Zielgröße** | **`barriere`** — von `messnorm.ZIELGROESSE_JE_LAGE` erzwungen, nicht gewählt |
| **Horizont** | **3** — von `messnorm.HORIZONT_JE_LAGE` erzwungen |
| **Frageart** | `beitrag` → **selektierte Menge**, über `zulaessige_mengen()` je Kandidat |
| **Nullpunkt** | 90. Perzentil über 40 Ziehungen (Vorgabe aus `messnorm`) |
| **Trennschärfe** | gegen denselben Bezug, Stärken bis 0,40 R |
| **Positivkontrolle** | ⭐ die **tragenden** Beiträge (§ B1) **und** die eingebaute Referenz `oi_aenderung` |
| **Negativkontrolle** | `zufall` |
| **B5/B6** | in `pruefe_auswahl` enthalten |
| **R-R11** | ✔ **erfüllt** — § A1 |
| **Register** | ✔ **gelesen** — § A2 |

## § B3 Die Kandidaten, mit Erwartung

| Gruppe | Kandidaten | Erwartung |
|---|---|---|
| **Positivkontrolle** | `funding` · `turnover` · `oi_aenderung` | **müssen tragen** — sie sind live registriert |
| **offen** | `taker_bias` ⭐ · `oi_je_umsatz` | der einzige unbelastete zuerst |
| **belastet** | `long_bias` · `top_bias` | laufen mit, aber ein Treffer wäre wegen § A2 **kein eigener Beitrag** |
| **Kontrolle** | `zufall` | muss null |

## § B4 ⭐ Die Entscheidungsregel — VOR dem Lauf

| Ergebnis | Entscheidung |
|---|---|
| ⛔ **Die tragenden tragen NICHT auf `barriere`** | **Abbruch.** Die Spur ist tot, und das ist der Befund — nicht die Kandidaten |
| ✔ **Tragende tragen, `taker_bias` auch, robust über alle zulässigen Mengen** | ⭐ **Erster Hebel-Beitrag.** Danach: Redundanz gegen die Live-Beiträge, dann Stufen |
| ⚠️ **`taker_bias` trägt auf nur EINER Menge** | **kein Befund** — N-73: nicht robust |
| ⚠️ **Nur `long_bias`/`top_bias` tragen** | **kein eigener Beitrag** (§ A2, fünffach redundant) |
| ⛔ **Kontrolle trägt** | Lauf ungültig |

⚠️⚠️ **Wird nicht nachverhandelt.**

## § B5 Die Vorhersage, vor dem Lauf

**Erwartung: die tragenden tragen auch auf `barriere`, keiner der offenen.**

**Begründung:** `funding` und `turnover` sind auf `bewegung_r` belegt; eine
Zielgröße, auf der sie ganz verschwänden, wäre selbst verdächtig. Die
offenen sind auf `bewegung_r` mit 0,00 bis 0,04 R gefallen, während die
Referenz +0,047 trägt — dass dieselben Größen auf `barriere` plötzlich
deutlich tragen, wäre überraschend.

⚠️ **Ein Nullbefund bei den offenen ist damit das wahrscheinliche Ergebnis
— aber diesmal ein interpretierbarer**, weil die Positivkontrolle
mitläuft.

## § B6 Was danach kommt — in dieser Reihenfolge

```
1. O-1   die barriere-Spur mit Positivkontrolle      ← jetzt
2. O-5   2.585 nachziehen (90. Perzentil, Trennschärfe)
3. O-4   die vier Werkzeuge an messnorm binden
4. O-3   der Querschnitt: Terzile statt Fünftel?
5. O-2   P-1, das Rangfenster
```

⚠️ **O-6** (`messe_zusammenspiel_beitraege`) wird **nicht** nachgerüstet,
sondern das Urteil zurückgenommen — die Aussage „Faktor 2 zu groß" stammt
aus einer Messung ohne Nullpunkt und wird durch 2.580 ohnehin schon
getragen.
