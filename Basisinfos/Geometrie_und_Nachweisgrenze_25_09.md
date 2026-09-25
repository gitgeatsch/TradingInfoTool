# Die Geometrie, der Horizont und die Nachweisgrenze — 25.09.2026

**Befunde 2.591-messgeometrie-ist-nicht-betrieb · 2.591-kelly-sitzt-auf-der-null ·
2.592-tagesstreuung-erklaert-die-grenze**

Ausgelöst durch zwei Nutzervorgaben desselben Tages:

> *„das ist bereits der 3. Hebelumbau und viele Messungen, vorsicht auch bei
> alten Informationen und Messungen."*
>
> *„Wenn du dir unsicher bist führe eine Messung mehr aus als eine zuwenig."*

---

# § 1 Was gemessen wurde — und was aus Altbeständen stammt

⚠️ **Strikt getrennt, weil der Hinweis genau darauf zielte.**

| | Quelle | Status |
|---|---|---|
| Stopweiten der vier Geometrien | **heute gemessen**, 781.164 Anker | ✔ Fakt |
| ATR-Definitionen im Vergleich | **heute gemessen**, 781.700 Werte | ✔ Fakt |
| Auflösungsanteil je Horizont | **heute gemessen** | ✔ Fakt |
| Konvergenz der bedingten Quote | **heute gemessen**, H bis 120 | ✔ Fakt |
| Hebelwirkung der Basisrate | **heute gerechnet** mit `betraege.hebelrechnung` | ✔ Fakt |
| Auswahleffekt der Mindestbesetzung | **heute gemessen**, 1.478 Tage | ✔ Fakt |
| *3 Tage bei 0,75 ATR, 23 bei 2,5 ATR* | Befund 2.445 | ✔ **heute unabhängig reproduziert** |
| *81,5 % der Stops aus dem Widerlegungspreis* | Befund 2.397/2.438 | ⚠️ **laut Register nicht reproduzierbar** — Werkzeug fehlt |
| *Median-Stop 13 % im Betrieb* | Befund 2.397 | ⚠️ ebenso — nur als Orientierung verwendet |

---

# § 2 ⛔ Die Messgeometrie ist nicht die Betriebsgeometrie

`k1c_hebel_barriere.barriere_je_reihe` behauptet im Docstring *„genau die
Geometrie, die `entscheidungsrechnung` baut"*. Sie rechnet aber nur die
**Untergrenze**:

```python
MESSUNG     min(25%K, max(5%K, 0,75 × ATR))            ← der Zielwert fehlt
PRODUKTION  clamp(2,5 × ATR, max(5%K, 0,75 × ATR), 25%K)
```

| | |
|---|---|
| Stopweite Median | Messung **6,18 %** · Rückfall **20,59 %** |
| identisch | **3,31 %** der Anker · Verhältnis Median **3,333** |

## 2.1 ✔ Zwei Verdachtsmomente wurden dabei entkräftet

| Verdacht | Prüfung | Ergebnis |
|---|---|---|
| die ATR-Definitionen unterscheiden sich (`B.spanne` gegen `atr_wilder`) | 781.700 Werte | ⛔ **nein** — 8,236 % gegen 8,679 %, Verhältnis 1,0538. Es ist der **Multiplikator** |
| `config.yaml` = 2,0 gegen `GRENZEN` = 0,75 verzerrt den Rückfall | beide Varianten gerechnet | ⛔ **nein** — 2,5 × ATR überschreitet den Boden 2,0 immer, **bitgleich** |
| mein Nachbau der Produktionsformel ist falsch | gegen `_stop_aus_atr` | ✔ **bitgleich 16/16** |

⚠️ **Und ein Memory-Fehler kam dabei heraus:** dort stand *„2,5 × ATR trifft
bei Krypto rund 7,5–8 %"*. Falsch — **1 × ATR** sind 8,24 %, **2,5 × ATR**
sind **20,59 %**. Der zugrundeliegende Befund 2.445-wirkung sagt es selbst
richtig; das Memory hatte ihn verkürzt. Korrigiert.

---

# § 3 ⭐ Und deshalb passt der Horizont nicht

Anteil **aufgelöster** Anker bei **H3**:

| Geometrie | H3 gelöst | Auflösungsmedian |
|---|---|---|
| Messung (6,18 %) | **51,7 %** | **H3** |
| Betrieb 13 % | **20,3 %** | H10 |
| ATR-Rückfall (20,59 %) | **8,0 %** | H16 |

✔✔ **Das reproduziert 2.445 aus einer völlig anderen Rechnung** — R-R11 erfüllt.

➤ **`messnorm.HORIZONT_JE_LAGE[(hebel, einstieg)] = 3` ist der
Auflösungsmedian der MESSgeometrie.** Bei H3 werden die Beiträge an 8–20 %
der Fälle gemessen und auf alle angewandt.

---

# § 4 ⛔⛔⛔ Der Hebel entsteht nur auf der Kelly-Null

Durchgerechnet mit `betraege.hebelrechnung`, 17.987 EUR Kapital, CRV 2,0:

| Lage | q | kelly | Hebel |
|---|---|---|---|
| **angenommene** Basisrate · Stop 13 % | 0,3333 | −0,0000 | **keiner** |
| + ein Beitrag +1,0 Pp | 0,3433 | +0,0150 | **2,07x** |
| + drei Beiträge +3,0 Pp | 0,3633 | +0,0450 | **3,46x** |
| **gemessen** H3 Messgeometrie | 0,2798 | −0,0830 | keiner |
| … + drei Beiträge +3,0 Pp | 0,3098 | −0,0380 | **keiner** |
| **gemessen** H23 Rückfall (Stop 20,6 %) | 0,3444 | +0,0181 | **keiner** |
| **gemessen** H23 Betrieb-13 % | 0,3460 | +0,0130 | **keiner** |

➤ **Nur die Zeile mit der ANGENOMMENEN Basisrate erzeugt Hebel.** Sie ist
`1/(1+CRV)` und damit **exakt die Kelly-Nullstelle** — die Formel sitzt per
Konstruktion im Kipppunkt, deshalb kippt dort jeder Beitragspunkt sofort in
Hebel.

## 4.1 ✔✔ Aber die Annahme 0,3333 ist für sich RICHTIG

Die **bedingte** Quote konvergiert bei H120 auf **0,3405** (Messung),
**0,3658** (Rückfall), **0,3602** (Betrieb) — und `tage_max` = 120 erlaubt
dieses Halten. `BASISRATE_GEMESSEN` = 0,340 trifft die Messgeometrie exakt.

⚠️⚠️ **Es ist kein Fehler, sondern eine Unvereinbarkeit:** die Basisrate gilt
für einen **bis zur Auflösung gehaltenen** Trade, die Beiträge werden bei
**H3** gemessen. Zwei Regime, eine Formel.

⚠️ Und die Nullstelle ist die Ruinwahrscheinlichkeit **ohne Zeitgrenze** — sie
ist damit die **bedingte** Quote. Die unbedingte (0,025 bis 0,145 bei H3)
dagegen zu stellen wäre ein Einheitenfehler. Das hatte ich zunächst vor und
habe es beim Nachrechnen verworfen.

---

# § 5 Die Symbolzahl, die Tagesklammer und die Nachweisgrenze

**Nutzerfrage:** *„prüfe warum nur 18 Symbole — ist das Messstandard oder nur
fehlende Daten"*

## 5.1 ✔✔ Die Antwort: **weder**

| Trichterstufe | funding täglich | Terminmarkt stündlich |
|---|---|---|
| Quelle je Termin (Median) | **116** | **82** |
| + Kursreihe vorhanden | 116 | 82 |
| + Mindestlänge je Symbol | 116 | — |
| + Vorlauf/Horizont | 105 | — |
| + Mindestbesetzung ≥ 12 | **121** | 82 |
| **verloren** | **6,0 %** der Tage | **0,0 %** der Stunden |

Und die Terminmarkt-Abdeckung **wächst**: Jahresmedian **35** (2021) → 40 → 50
→ 86 → **122** (2025) → **122** (2026).

⚠️⚠️ **Die „18 Symbole" aus 2.587 gelten nicht allgemein** — sie stammen aus
dem Schnitt mit der **Stundenbasis** (116 Symbole, kurze Historie), nicht aus
der Terminmarktabdeckung.

⚠️ **Onchain nebenbei geprüft** (Nutzerfrage): 66 Symbole gelten nominell, je
Tag sind es **49** im Median; `txtfrvaladjusd` ist **leer**; `adractcnt` endet
am **29.08.2026** und hat **keinen** Eintrag in `abruf_symbol`, wird also nicht
überwacht.

## 5.2 ⛔ Mein eigener Befund 2.592 war auf zu wenigen Reihen gemessen

Dieselbe Falle, vor der oben gewarnt wird — nur bei einer **brandneuen**
Messung. Nachgemessen:

| geladen | Symbole/Tag | Streuung | **Nachweisgrenze (2,5 × SE)** |
|---|---|---|---|
| 40 | 16 | 0,2020 | 0,0254 |
| 120 | 24 | 0,2261 | 0,0153 |
| **alle 536** | **67** | 0,1898 | **0,0102** |

➤ Der erwartete Beitrag (0,002–0,012) liegt damit **an** der Grenze, nicht
hoffnungslos darunter. **2.592 ist abgelöst** durch 2.593.

## 5.3 ⭐⭐⭐ Und dabei kam der eigentliche Fund heraus

Dieselben **190.612** Anker, zwei Gewichtungen:

| | `q` | Kelly | Hebel |
|---|---|---|---|
| Mittel der **Tagesmittel** | **0,3447** | +0,0171 | **2,36x** |
| **gepoolt** über Anker | **0,2472** | −0,0803 | **keiner** |

⚠️ Ich hatte zwischenzeitlich **2,36x** gemeldet. Das war ein **Artefakt der
Tagesklammer**: sie gewichtet einen Tag mit 15 Ankern wie einen mit 300 — und
dünne Tage haben die **höchste** Quote (0,5526 gegen 0,0757, monoton über fünf
Fünftel).

➤ **Für `q` ist die GEPOOLTE Zahl richtig** — ein Trade entsteht je **Anker**,
nicht je Tag. Für die **Beitrags**messung bleibt die Tagesklammer richtig, weil
es dort um den Querschnitt *innerhalb* eines Tages geht. **Zwei Fragen, zwei
Gewichtungen**, und jede Messung muss sagen, welche sie nimmt.

## 5.4 ✔✔ Gegengeprüft je Jahr und je Block

| 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|
| 0,2401 | 0,3000 | 0,2096 | 0,2766 | 0,2487 | 0,2173 | 0,2694 |

**Alle sieben unter 0,3333.** In 60-Tage-Blöcken: **6 von 36** darüber (16,7 %),
Spanne 0,0999–0,4102, Streuung 0,0780.

➤ **Damit ist § 4 bestätigt:** bei H3 liegt die bedingte Quote **strukturell**
unter der Kelly-Nullstelle. Kein Widerspruch zur Theorie — `1/(1+CRV)` gilt
**ohne** Zeitgrenze, und ein kurzes Fenster benachteiligt das **Ziel**, weil es
doppelt so weit entfernt liegt wie der Stop.

⭐ **Ab welchem Horizont sie trägt, ist gemessen:** H10 **0,3342** · H16 0,3419
· H23 0,3433.

## 5.5 Die Mindestbesetzung wählt Stop-Tage aus — das bleibt

Quote je Fünftel des **Auflösungsanteils** des Tages:

| Auflösungsanteil | 0,137 | 0,307 | 0,522 | 0,794 | 0,971 |
|---|---|---|---|---|---|
| **Quote** | **0,5526** | 0,5306 | 0,3751 | 0,1972 | **0,0757** |

Der Mechanismus ist zwingend: der Stop liegt **eine** Einheit entfernt, das
Ziel **zwei**. Dieser Teil von 2.592 hängt **nicht** an der Reihenzahl und
bleibt — er ist die Erklärung für die 10-Punkte-Verschiebung in § 5.3.

⛔ **`funding` trennt trotzdem in keiner Auflösungsgruppe** (−0,0097 / −0,0027
/ +0,0025). Die Auswahl ist ein **Niveau**fehler, kein Trennungsfehler.

# § 6 Was daraus **nicht** folgt

- **Nicht**, dass `barriere_je_reihe` zu ändern ist. Sechs Messwerkzeuge
  hängen daran, und der Betriebsstop liegt laut 2.438 im Median bei 8 %
  (Widerlegungspreis) — **näher an der Messgeometrie als am Rückfall**.
  ⚠️ Diese Zahl ist nicht reproduzierbar.
- **Nicht**, welcher Horizont richtig ist. Entwurfsentscheidung.
- **Nicht**, dass `MIND_JE_TAG` zu senken ist: eine kleinere Besetzung
  **erhöht** die Tagesstreuung und damit den Fehler. Zielkonflikt, zu
  messen.
- **Nicht**, dass `funding` widerlegt ist. **Untermächtig ist nicht anders.**
- **Nicht**, dass die Beiträge das Problem sind. Sie sind es nicht.
- **Nicht**, dass `H` auf 10 zu setzen ist. Das ist eine Entwurfsentscheidung
  mit Folgen für Haltedauer und Finanzierung.
- ⚠️ **Nicht entschieden ist die Geometriefrage selbst.** Der Docstring ist
  richtiggestellt; ob die Geometrie zu wechseln ist, hängt am **echten
  Betriebsstop**, und der ist nicht reproduzierbar gemessen.

---

# § 7 Die Werkzeuge

| Datei | Was sie beantwortet |
|---|---|
| `pruefe_barrierengeometrie.py` | die vier Geometrien, Einheitenprobe, Auflösung je Horizont · Selbstprobe gegen `_stop_aus_atr` |
| `pruefe_symbole_je_termin.py` | Trichter der Symbolverfügbarkeit je Termin, Stufe für Stufe · Abdeckung je Jahr |
| `messe_funding_je_geometrie.py` | trägt `funding` bei gewechselter Geometrie? · **Bitgleichheitsnachweis** gegen `barriere_je_reihe` (15.495/15.495) · Zusicherung, dass `in_r` nur 0,0/1,0 enthält |

⚠️ **Beide nur lesend.** Die Suite bestätigt: kein Paket schreibt in
`data/tradinginfotool.db`.
